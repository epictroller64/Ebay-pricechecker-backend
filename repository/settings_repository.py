from classes import Settings
from data import execute_query, select_one

class SettingsRepository:
    
    async def get_settings(self) -> Settings:
        settings = await select_one("SELECT * FROM settings")
        return Settings(interval=settings[1], phone_number=settings[2], telegram_userid=settings[3], email=settings[4])

    async def update_settings(self, interval: int):
        await execute_query("UPDATE settings SET interval = ?", (interval,))

