import aiosqlite
from typing import List, Optional, Any
from contextlib import asynccontextmanager

DATABASE_NAME = "listings.db"

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

async def select_one(query: str, params: tuple = ()) -> Optional[tuple]:
    """Execute a query and return a single row"""
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params)
        return await cursor.fetchone()

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
    
    await execute_query(create_listings_table)
    await execute_query(create_price_history_table)

# Initialize the database when the module is imported
import asyncio
asyncio.run(init_db())
