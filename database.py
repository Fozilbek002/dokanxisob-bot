"""
database.py — SQLite ma'lumotlar bazasi bilan ishlash

Jadvallar:
    items      — ombordagi mahsulotlar (nomi, kelish narxi, miqdori)
    sales      — sotuvlar tarixi (qaysi mahsulot, necha dona, qancha narxda sotilgan)
    expenses   — chiqimlar (masalan: ijara, transport, ish haqi va h.k.)
    cash       — kassa ochish/yopish tarixi
"""

import sqlite3
from datetime import datetime

DB_PATH = "hisobot_bot.db"


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
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            sale_price REAL NOT NULL,
            purchase_price REAL NOT NULL,
            total REAL NOT NULL,
            profit REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            opening_balance REAL,
            closing_balance REAL,
            opened_at TEXT,
            closed_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- OMBOR (ITEMS) ----------------

def add_item(name, purchase_price, quantity, unit="dona"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO items (name, purchase_price, quantity, unit, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, purchase_price, quantity, unit, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_items():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM items ORDER BY name").fetchall()
    conn.close()
    return rows


def get_item(item_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return row


def update_stock(item_id, new_quantity):
    conn = get_conn()
    conn.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
    conn.commit()
    conn.close()


# ---------------- SOTISH (SALES) ----------------

def add_sale(item_id, item_name, quantity, sale_price, purchase_price):
    total = quantity * sale_price
    profit = total - (quantity * purchase_price)
    conn = get_conn()
    conn.execute(
        """INSERT INTO sales
           (item_id, item_name, quantity, sale_price, purchase_price, total, profit, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (item_id, item_name, quantity, sale_price, purchase_price, total, profit, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_sales(start_iso, end_iso):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sales WHERE created_at BETWEEN ? AND ? ORDER BY created_at",
        (start_iso, end_iso),
    ).fetchall()
    conn.close()
    return rows


# ---------------- CHIQIM (EXPENSES) ----------------

def add_expense(description, amount):
    conn = get_conn()
    conn.execute(
        "INSERT INTO expenses (description, amount, created_at) VALUES (?, ?, ?)",
        (description, amount, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_expenses(start_iso, end_iso):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE created_at BETWEEN ? AND ? ORDER BY created_at",
        (start_iso, end_iso),
    ).fetchall()
    conn.close()
    return rows


# ---------------- KASSA ----------------

def open_cash(opening_balance):
    conn = get_conn()
    conn.execute(
        "INSERT INTO cash (status, opening_balance, opened_at) VALUES ('ochiq', ?, ?)",
        (opening_balance, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def close_cash(closing_balance):
    conn = get_conn()
    conn.execute(
        """UPDATE cash SET status = 'yopiq', closing_balance = ?, closed_at = ?
           WHERE status = 'ochiq'""",
        (closing_balance, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_cash_status():
    conn = get_conn()
    row = conn.execute("SELECT * FROM cash WHERE status = 'ochiq' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row


# ---------------- HISOBOT (REPORT) ----------------

def get_report(start_iso, end_iso):
    """Berilgan davr uchun kirim, chiqim, foyda/zarar hisoblaydi."""
    sales = get_sales(start_iso, end_iso)
    expenses = get_expenses(start_iso, end_iso)

    total_income = sum(s["total"] for s in sales)          # jami sotuv summasi (kirim)
    total_gross_profit = sum(s["profit"] for s in sales)    # sotuvdan sof foyda (tannarxsiz)
    total_expenses = sum(e["amount"] for e in expenses)     # jami chiqimlar
    net_profit = total_gross_profit - total_expenses        # sof foyda/zarar

    return {
        "sales": sales,
        "expenses": expenses,
        "total_income": total_income,
        "total_gross_profit": total_gross_profit,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
    }
