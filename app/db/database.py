import aiosqlite
from datetime import datetime
from app.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance REAL DEFAULT 0.0,
                    total_deposited REAL DEFAULT 0.0,
                    total_orders REAL DEFAULT 0.0,
                    referrer_id INTEGER,
                    registration_date TEXT,
                    registration_time TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    method TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    completed_at TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_name TEXT,
                    quantity INTEGER,
                    price_per_item REAL,
                    total_price REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS promo_codes (
                    code TEXT PRIMARY KEY,
                    amount REAL,
                    is_used INTEGER DEFAULT 0,
                    used_by INTEGER,
                    created_at TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    referrer_id INTEGER,
                    referred_id INTEGER PRIMARY KEY,
                    bonus_paid REAL DEFAULT 0.0,
                    created_at TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT DEFAULT '',
                    stock INTEGER DEFAULT 0,
                    deliver_data TEXT DEFAULT ''
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS product_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    item_data TEXT NOT NULL,
                    is_sold INTEGER DEFAULT 0,
                    sold_to INTEGER,
                    sold_at TEXT,
                    created_at TEXT
                )
            """)
            # default settings
            await conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('referral_percent', '10')"
            )
            # default product
            cur = await conn.execute("SELECT COUNT(*) FROM products")
            count = (await cur.fetchone())[0]
            if count == 0:
                await conn.execute(
                    "INSERT INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)",
                    ("Milanuncios Selfreg", 2.50, "Selfreg аккаунт Milanuncios🇪🇸", 0),
                )
            await conn.commit()

    # ── Users ──

    async def add_user(self, user_id: int, username: str, first_name: str, referrer_id: int = None):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now()
            await conn.execute(
                "INSERT OR IGNORE INTO users "
                "(user_id, username, first_name, referrer_id, registration_date, registration_time) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, first_name, referrer_id,
                 now.strftime("%d.%m.%Y"), now.strftime("%H:%M:%S")),
            )
            await conn.commit()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cur.fetchone()

    async def ensure_user(self, user_id: int, username: str = "", first_name: str = ""):
        user = await self.get_user(user_id)
        if not user:
            await self.add_user(user_id, username, first_name)
            user = await self.get_user(user_id)
        return user

    async def update_balance(self, user_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE users SET balance = balance + ?, total_deposited = total_deposited + ? "
                "WHERE user_id = ?",
                (amount, amount, user_id),
            )
            await conn.commit()

    async def deduct_balance(self, user_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id),
            )
            await conn.commit()

    async def get_all_user_ids(self):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT user_id FROM users")
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    async def get_user_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT COUNT(*) FROM users")
            row = await cur.fetchone()
            return row[0]

    # ── Payments ──

    async def add_payment(self, user_id: int, amount: float, method: str):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            cur = await conn.execute(
                "INSERT INTO payments (user_id, amount, method, created_at) VALUES (?, ?, ?, ?)",
                (user_id, amount, method, now),
            )
            await conn.commit()
            return cur.lastrowid

    async def complete_payment(self, payment_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            await conn.execute(
                "UPDATE payments SET status = 'completed', completed_at = ? WHERE id = ?",
                (now, payment_id),
            )
            await conn.commit()

    async def get_payment_history(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            return await cur.fetchall()

    # ── Orders ──

    async def add_order(self, user_id: int, product_name: str, quantity: int,
                        price_per_item: float, total_price: float):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            cur = await conn.execute(
                "INSERT INTO orders (user_id, product_name, quantity, price_per_item, total_price, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, product_name, quantity, price_per_item, total_price, now),
            )
            await conn.commit()
            return cur.lastrowid

    async def get_order_history(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            return await cur.fetchall()

    # ── Promo codes ──

    async def add_promo_code(self, code: str, amount: float):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            await conn.execute(
                "INSERT OR REPLACE INTO promo_codes (code, amount, created_at) VALUES (?, ?, ?)",
                (code, amount, now),
            )
            await conn.commit()

    async def get_promo_code(self, code: str):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
            return await cur.fetchone()

    async def use_promo_code(self, code: str, user_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE promo_codes SET is_used = 1, used_by = ? WHERE code = ?",
                (user_id, code),
            )
            await conn.commit()

    # ── Referrals ──

    async def add_referral(self, referrer_id: int, referred_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            await conn.execute(
                "INSERT OR IGNORE INTO referrals (referrer_id, referred_id, created_at) "
                "VALUES (?, ?, ?)",
                (referrer_id, referred_id, now),
            )
            await conn.commit()

    async def get_referrals(self, referrer_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM referrals WHERE referrer_id = ?", (referrer_id,),
            )
            return await cur.fetchall()

    async def get_referral_count(self, referrer_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (referrer_id,),
            )
            row = await cur.fetchone()
            return row[0] if row else 0

    async def get_referral_earnings(self, referrer_id: int) -> float:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute(
                "SELECT COALESCE(SUM(bonus_paid), 0) FROM referrals WHERE referrer_id = ?",
                (referrer_id,),
            )
            row = await cur.fetchone()
            return row[0] if row else 0.0

    async def add_referral_bonus(self, referrer_id: int, referred_id: int, bonus: float):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE referrals SET bonus_paid = bonus_paid + ? "
                "WHERE referrer_id = ? AND referred_id = ?",
                (bonus, referrer_id, referred_id),
            )
            await conn.commit()

    # ── Products ──

    async def add_product(self, name: str, price: float, description: str, stock: int):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute(
                "INSERT INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)",
                (name, price, description, stock),
            )
            await conn.commit()
            return cur.lastrowid

    async def get_product(self, product_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            return await cur.fetchone()

    async def get_all_products(self):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM products ORDER BY id")
            return await cur.fetchall()

    async def update_product(self, product_id: int, name: str, price: float, description: str, stock: int):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE products SET name=?, price=?, description=?, stock=? WHERE id=?",
                (name, price, description, stock, product_id),
            )
            await conn.commit()

    async def delete_product(self, product_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            await conn.commit()

    async def decrement_stock(self, product_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0",
                (product_id,),
            )
            await conn.commit()

    # ── Product Items (товары для выдачи) ──

    async def add_product_item(self, product_id: int, item_data: str):
        """Добавить товар (аккаунт/данные) к продукту."""
        async with aiosqlite.connect(self.db_path) as conn:
            from datetime import datetime
            now = datetime.now().isoformat()
            await conn.execute(
                "INSERT INTO product_items (product_id, item_data, created_at) VALUES (?, ?, ?)",
                (product_id, item_data, now),
            )
            # Увеличиваем сток продукта
            await conn.execute(
                "UPDATE products SET stock = stock + 1 WHERE id = ?",
                (product_id,),
            )
            await conn.commit()

    async def add_product_items_bulk(self, product_id: int, items: list):
        """Добавить несколько товаров сразу."""
        async with aiosqlite.connect(self.db_path) as conn:
            from datetime import datetime
            now = datetime.now().isoformat()
            for item_data in items:
                await conn.execute(
                    "INSERT INTO product_items (product_id, item_data, created_at) VALUES (?, ?, ?)",
                    (product_id, item_data.strip(), now),
                )
            # Увеличиваем сток продукта
            await conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (len(items), product_id),
            )
            await conn.commit()

    async def get_available_item(self, product_id: int):
        """Получить первый доступный товар для продукта."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM product_items WHERE product_id = ? AND is_sold = 0 LIMIT 1",
                (product_id,),
            )
            return await cur.fetchone()

    async def mark_item_sold(self, item_id: int, user_id: int):
        """Отметить товар как проданный."""
        async with aiosqlite.connect(self.db_path) as conn:
            from datetime import datetime
            now = datetime.now().isoformat()
            await conn.execute(
                "UPDATE product_items SET is_sold = 1, sold_to = ?, sold_at = ? WHERE id = ?",
                (user_id, now, item_id),
            )
            await conn.commit()

    async def get_items_count(self, product_id: int) -> int:
        """Получить количество доступных товаров для продукта."""
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute(
                "SELECT COUNT(*) FROM product_items WHERE product_id = ? AND is_sold = 0",
                (product_id,),
            )
            row = await cur.fetchone()
            return row[0] if row else 0

    async def get_all_items(self, product_id: int, include_sold: bool = False):
        """Получить все товары для продукта."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            if include_sold:
                cur = await conn.execute(
                    "SELECT * FROM product_items WHERE product_id = ? ORDER BY id",
                    (product_id,),
                )
            else:
                cur = await conn.execute(
                    "SELECT * FROM product_items WHERE product_id = ? AND is_sold = 0 ORDER BY id",
                    (product_id,),
                )
            return await cur.fetchall()

    async def sync_product_stock(self, product_id: int):
        """Синхронизировать stock продукта с реальным количеством товаров."""
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute(
                "SELECT COUNT(*) FROM product_items WHERE product_id = ? AND is_sold = 0",
                (product_id,),
            )
            row = await cur.fetchone()
            count = row[0] if row else 0
            await conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (count, product_id),
            )
            await conn.commit()

    async def sync_all_stocks(self):
        """Синхронизировать stock для всех продуктов."""
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT id FROM products")
            products = await cur.fetchall()
            for (pid,) in products:
                cur2 = await conn.execute(
                    "SELECT COUNT(*) FROM product_items WHERE product_id = ? AND is_sold = 0",
                    (pid,),
                )
                row = await cur2.fetchone()
                count = row[0] if row else 0
                await conn.execute(
                    "UPDATE products SET stock = ? WHERE id = ?",
                    (count, pid),
                )
            await conn.commit()

    # ── Settings ──

    async def get_setting(self, key: str, default: str = "") -> str:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cur.fetchone()
            return row[0] if row else default

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            await conn.commit()

    async def get_referral_percent(self) -> float:
        val = await self.get_setting("referral_percent", "10")
        return float(val)


db = Database(DATABASE_PATH)
