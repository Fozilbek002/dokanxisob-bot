import aiosqlite

DB_NAME = "shop.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Mahsulotlar (ombor) - har bir mahsulotning joriy qoldig'i va tannarxi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                purchase_price REAL NOT NULL,
                sale_price REAL,
                quantity REAL NOT NULL DEFAULT 0,
                UNIQUE(owner_id, name)
            )
        """)
        # Sotuvlar tarixi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                sale_price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                revenue REAL NOT NULL,
                cost REAL NOT NULL,
                profit REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # Qo'shimcha chiqimlar (ijara, transport va h.k.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        await db.commit()


# ==== MAHSULOTLAR (KIRIM) ====

async def add_or_update_product(owner_id: int, name: str, purchase_price: float, quantity: float):
    """Mahsulot kiritish: mavjud bo'lsa qoldiqni oshiradi va tannarxni yangilaydi, yo'q bo'lsa yaratadi."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, quantity FROM products WHERE owner_id = ? AND name = ?",
            (owner_id, name),
        )
        row = await cursor.fetchone()
        if row:
            product_id, current_qty = row
            new_qty = current_qty + quantity
            await db.execute(
                "UPDATE products SET purchase_price = ?, quantity = ? WHERE id = ?",
                (purchase_price, new_qty, product_id),
            )
        else:
            await db.execute(
                """INSERT INTO products (owner_id, name, purchase_price, quantity)
                   VALUES (?, ?, ?, ?)""",
                (owner_id, name, purchase_price, quantity),
            )
        await db.commit()


async def get_products(owner_id: int, only_in_stock: bool = False):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM products WHERE owner_id = ?"
        if only_in_stock:
            query += " AND quantity > 0"
        query += " ORDER BY name"
        cursor = await db.execute(query, (owner_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_sale_price(product_id: int, sale_price: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE products SET sale_price = ? WHERE id = ?", (sale_price, product_id)
        )
        await db.commit()


async def decrease_stock(product_id: int, quantity: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id = ?",
            (quantity, product_id),
        )
        await db.commit()


# ==== SOTUVLAR ====

async def record_sale(owner_id: int, product_name: str, quantity: float,
                       sale_price: float, purchase_price: float):
    revenue = sale_price * quantity
    cost = purchase_price * quantity
    profit = revenue - cost
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO sales
               (owner_id, product_name, quantity, sale_price, purchase_price, revenue, cost, profit)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (owner_id, product_name, quantity, sale_price, purchase_price, revenue, cost, profit),
        )
        await db.commit()
    return revenue, cost, profit


async def get_sales(owner_id: int, limit: int = 15):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sales WHERE owner_id = ? ORDER BY id DESC LIMIT ?",
            (owner_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ==== CHIQIMLAR ====

async def add_expense(owner_id: int, name: str, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO expenses (owner_id, name, amount) VALUES (?, ?, ?)",
            (owner_id, name, amount),
        )
        await db.commit()


async def get_expenses(owner_id: int, limit: int = 15):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM expenses WHERE owner_id = ? ORDER BY id DESC LIMIT ?",
            (owner_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ==== STATISTIKA ====

async def get_stats(owner_id: int, date_from: str = None, date_to: str = None):
    """date_from / date_to: 'YYYY-MM-DD' formatida, ikkalasi ham qamrab olinadi (inclusive).
    Agar ikkalasi ham None bo'lsa, butun vaqt hisoblanadi."""
    async with aiosqlite.connect(DB_NAME) as db:
        if date_from and date_to:
            date_filter = "AND date(created_at) BETWEEN ? AND ?"
            params = (owner_id, date_from, date_to)
        else:
            date_filter = ""
            params = (owner_id,)

        cursor = await db.execute(
            f"""SELECT COUNT(*), COALESCE(SUM(revenue),0), COALESCE(SUM(cost),0), COALESCE(SUM(profit),0)
               FROM sales WHERE owner_id = ? {date_filter}""",
            params,
        )
        sale_count, total_revenue, total_cost, total_sales_profit = await cursor.fetchone()

        cursor = await db.execute(
            f"SELECT COALESCE(SUM(amount),0) FROM expenses WHERE owner_id = ? {date_filter}",
            params,
        )
        (total_expenses,) = await cursor.fetchone()

        net_profit = total_sales_profit - total_expenses

        return {
            "sale_count": sale_count,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_sales_profit": total_sales_profit,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
        }
