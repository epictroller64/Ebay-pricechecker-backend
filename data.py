import aiosqlite
from typing import List, Optional, Any
from contextlib import asynccontextmanager

DATABASE_NAME = "listings.db"

async def enable_wal_mode(db):
    """Enable WAL mode for the SQLite database."""
    await db.execute("PRAGMA journal_mode=WAL;")
    print("WAL mode enabled.")

@asynccontextmanager
async def get_db_connection():
    async with aiosqlite.connect(DATABASE_NAME) as conn:
        yield conn

async def execute_query(query: str, params: tuple = ()) -> int | None:
    """Execute a query without returning results"""
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params)
        lastrowid = cursor.lastrowid
        await cursor.close()  # Close the cursor before committing
        await conn.commit()
        return lastrowid

async def execute_query_many(query: str, params: tuple = ()) -> int | None:
    """Execute a query without returning results"""
    async with get_db_connection() as conn:
        cursor = await conn.executemany(query, params)
        lastrowid = cursor.lastrowid
        await cursor.close()
        await conn.commit()
        return lastrowid

async def select_one(query: str, params: tuple = (), as_dict: bool = False) -> Optional[tuple] | dict:
    """Execute a query and return a single row"""
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params)
        fetched = await  cursor.fetchone()
        if fetched and as_dict:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, fetched))
        return fetched 

async def select_all(query: str, params: tuple = (), as_dict: bool = False) -> List[tuple] | List[dict]:
    """Execute a query and return all rows"""
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params)
        if as_dict:
            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        else:
            return await cursor.fetchall()

def dict_factory(cursor: aiosqlite.Cursor, row: tuple) -> dict:
    """Convert a row to a dictionary using column names as keys"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

async def select_one_dict(query: str, params: tuple = ()) -> Optional[dict]:
    """Execute a query and return a single row as dictionary"""
    async with get_db_connection() as conn:
        conn.row_factory = dict_factory
        cursor = await conn.execute(query, params)
        return await cursor.fetchone()

async def select_all_dict(query: str, params: tuple = ()) -> List[dict]:
    """Execute a query and return all rows as dictionaries"""
    async with get_db_connection() as conn:
        conn.row_factory = dict_factory
        cursor = await conn.execute(query, params)
        return await cursor.fetchall()

# Initialize database and create tables
async def init_db():
    create_listings_table = """
    CREATE TABLE IF NOT EXISTS listings (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        stock INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    create_listing_relations_table = """
    CREATE TABLE IF NOT EXISTS listing_relations (
        id TEXT PRIMARY KEY,
        listing_id TEXT NOT NULL,
        user_id TEXT NOT NULL
    )        
"""
    
    create_price_history_table = """
    CREATE TABLE IF NOT EXISTS price_history (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
        listing_id TEXT NOT NULL,
        price REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        currency TEXT NOT NULL,
        FOREIGN KEY (listing_id) REFERENCES listings (id)
    )
    """
    create_settings_table = """
    CREATE TABLE IF NOT EXISTS settings (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
        interval INTEGER NOT NULL,
        phone_number TEXT,
        telegram_userid TEXT,
        email TEXT,
        user_id TEXT NOT NULL
    )
    """
    create_reminders_table = """
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
        method TEXT NOT NULL CHECK (method IN ('telegram', 'sms', 'email')),
        target_product_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('out_of_stock', 'back_in_stock', 'price_drop', 'price_increase')),
        FOREIGN KEY (target_product_id) REFERENCES listings (id)
    )
    """
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    create_zip_table = """
    CREATE TABLE IF NOT EXISTS zip_files (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
        filename TEXT   
    )
"""
    
    await execute_query(create_listings_table)
    await execute_query(create_price_history_table)
    await execute_query(create_settings_table)
    await execute_query(create_reminders_table)
    await execute_query(create_zip_table)
    await execute_query(create_users_table)
    await execute_query(create_listing_relations_table)
