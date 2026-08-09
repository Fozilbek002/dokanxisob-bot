"""
database.py — SQLite ma'lumotlar bazasi bilan ishlash

Har bir foydalanuvchi (owner_id — Telegram user_id) uchun alohida:
    items            — ombordagi mahsulotlar
    sales            — sotuvlar tarixi
    expenses         — chiqimlar
    cash_ledger      — kassa harakatlari (kirim/chiqim), balans shulardan hisoblanadi
    recurring_costs  — doimiy oylik xarajatlar (ijara, yuk tashish), kunlik ulushga bo'linadi
"""

import os
import sqlite3
from datetime import datetime, date

DB_PATH = os.environ.get("DB_PATH", "hisobot_bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT DEFAULT 'dona',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            sale_price REAL NOT NULL,
            purchase_price REAL NOT NULL,
            total REAL NOT NULL,
            profit REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cash_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS recurring_costs (
            owner_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_amount REAL NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (owner_id, category)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- OMBOR (ITEMS) ----------------

def add_item(owner_id, name, purchase_price, quantity, unit="dona"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO items (owner_id, name, purchase_price, quantity, unit, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (owner_id, name, purchase_price, quantity, unit, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_items(owner_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM items WHERE owner_id = ? ORDER BY name", (owner_id,)
    ).fetchall()
    conn.close()
    return rows


def get_item(owner_id, item_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM items WHERE id = ? AND owner_id = ?", (item_id, owner_id)
    ).fetchone()
    conn.close()
    return row


def update_stock(owner_id, item_id, new_quantity):
    conn = get_conn()
    conn.execute(
        "UPDATE items SET quantity = ? WHERE id = ? AND owner_id = ?",
        (new_quantity, item_id, owner_id),
    )
    conn.commit()
    conn.close()


def delete_item(owner_id, item_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM items WHERE id = ? AND owner_id = ?", (item_id, owner_id)
    )
    conn.commit()
    conn.close()


# ---------------- SOTISH (SALES) ----------------

def add_sale(owner_id, item_id, item_name, quantity, sale_price, purchase_price, sale_date=None):
    """sale_date: 'YYYY-MM-DD' (ixtiyoriy). Berilmasa, hozirgi vaqt ishlatiladi."""
    total = quantity * sale_price
    profit = total - (quantity * purchase_price)
    created_at = f"{sale_date}T12:00:00" if sale_date else datetime.now().isoformat()

    conn = get_conn()
    conn.execute(
        """INSERT INTO sales
           (owner_id, item_id, item_name, quantity, sale_price, purchase_price, total, profit, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (owner_id, item_id, item_name, quantity, sale_price, purchase_price, total, profit, created_at),
    )
    conn.commit()
    conn.close()
    return total, profit


def get_sales(owner_id, start_iso, end_iso):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sales WHERE owner_id = ? AND created_at BETWEEN ? AND ? ORDER BY created_at",
        (owner_id, start_iso, end_iso),
    ).fetchall()
    conn.close()
    return rows


# ---------------- CHIQIM (EXPENSES) ----------------

def add_expense(owner_id, description, amount):
    conn = get_conn()
    conn.execute(
        "INSERT INTO expenses (owner_id, description, amount, created_at) VALUES (?, ?, ?, ?)",
        (owner_id, description, amount, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_expenses(owner_id, start_iso, end_iso):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE owner_id = ? AND created_at BETWEEN ? AND ? ORDER BY created_at",
        (owner_id, start_iso, end_iso),
    ).fetchall()
    conn.close()
    return rows


# ---------------- KASSA (CASH LEDGER) ----------------

def cash_add(owner_id, amount, note=""):
    """Kassaga kirim (+) yoki chiqim (-) yozadi."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO cash_ledger (owner_id, amount, note, created_at) VALUES (?, ?, ?, ?)",
        (owner_id, amount, note, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_cash_balance(owner_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS balance FROM cash_ledger WHERE owner_id = ?",
        (owner_id,),
    ).fetchone()
    conn.close()
    return row["balance"]


def get_cash_ledger(owner_id, limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM cash_ledger WHERE owner_id = ? ORDER BY id DESC LIMIT ?",
        (owner_id, limit),
    ).fetchall()
    conn.close()
    return rows


# ---------------- DOIMIY XARAJATLAR (IJARA / YUK) ----------------

def set_recurring_cost(owner_id, category, monthly_amount):
    conn = get_conn()
    conn.execute(
        """INSERT INTO recurring_costs (owner_id, category, monthly_amount, updated_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(owner_id, category) DO UPDATE SET
               monthly_amount = excluded.monthly_amount,
               updated_at = excluded.updated_at""",
        (owner_id, category, monthly_amount, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recurring_costs(owner_id):
    """{'ijara': 3600000, 'yuk': 500000} kabi lug'at qaytaradi."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, monthly_amount FROM recurring_costs WHERE owner_id = ?", (owner_id,)
    ).fetchall()
    conn.close()
    return {r["category"]: r["monthly_amount"] for r in rows}


# ---------------- HISOBOT (REPORT) ----------------

def get_report(owner_id, start_iso, end_iso):
    """Berilgan davr uchun kirim, chiqim, doimiy xarajat ulushi va sof foyda/zararni hisoblaydi."""
    sales = get_sales(owner_id, start_iso, end_iso)
    expenses = get_expenses(owner_id, start_iso, end_iso)

    total_income = sum(s["total"] for s in sales)
    total_gross_profit = sum(s["profit"] for s in sales)
    total_expenses = sum(e["amount"] for e in expenses)

    # Davrdagi kunlar sonini hisoblash (ikkala chekka ham kiradi)
    try:
        d1 = datetime.fromisoformat(start_iso).date()
        d2 = datetime.fromisoformat(end_iso).date()
        num_days = (d2 - d1).days + 1
        if num_days < 1:
            num_days = 1
    except ValueError:
        num_days = 1

    recurring = get_recurring_costs(owner_id)
    monthly_total = sum(recurring.values())
    daily_recurring = monthly_total / 30
    recurring_for_period = daily_recurring * num_days

    total_expenses_all = total_expenses + recurring_for_period
    net_profit = total_gross_profit - total_expenses_all

    return {
        "sales": sales,
        "expenses": expenses,
        "total_income": total_income,
        "total_gross_profit": total_gross_profit,
        "total_expenses": total_expenses,
        "recurring_for_period": recurring_for_period,
        "recurring_breakdown": recurring,
        "num_days": num_days,
        "total_expenses_all": total_expenses_all,
        "net_profit": net_profit,
    }
