from classes import Settings
from data import execute_query, select_one

async def get_settings():
    settings = await select_one("SELECT * FROM settings")
    return Settings(interval=settings[1])

async def update_settings(interval: int):
    await execute_query("UPDATE settings SET interval = ?", (interval,))


