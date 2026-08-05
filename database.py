import aiosqlite

DB_NAME = "shop.db"


async def init_db():
    """Ma'lumotlar bazasi va jadvallarni yaratish"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Mahsulotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        # Buyurtmalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                total REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # Buyurtma tarkibidagi mahsulotlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        """)
        await db.commit()


async def add_product(owner_id: int, name: str, price: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO products (owner_id, name, price) VALUES (?, ?, ?)",
            (owner_id, name, price),
        )
        await db.commit()


async def get_products(owner_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE owner_id = ? ORDER BY name", (owner_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def create_order(owner_id: int, items: list, total: float):
    """items: [{"name":..., "price":..., "quantity":..., "subtotal":...}, ...]"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO orders (owner_id, total) VALUES (?, ?)",
            (owner_id, total),
        )
        order_id = cursor.lastrowid
        for item in items:
            await db.execute(
                """INSERT INTO order_items
                   (order_id, product_name, price, quantity, subtotal)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, item["name"], item["price"], item["quantity"], item["subtotal"]),
            )
        await db.commit()
        return order_id


async def get_orders(owner_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE owner_id = ? ORDER BY id DESC LIMIT ?",
            (owner_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_order_items(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_stats(owner_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE owner_id = ?",
            (owner_id,),
        )
        count, total_sum = await cursor.fetchone()
        return {"count": count, "total_sum": total_sum}
