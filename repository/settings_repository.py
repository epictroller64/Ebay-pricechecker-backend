from classes import Settings
from data import execute_query, select_one

class SettingsRepository:
    
    async def get_settings(self) -> Settings:
        settings = await select_one("SELECT * FROM settings")
        if settings:
            return Settings(interval=settings[1], phone_number=settings[2], telegram_userid=settings[3], email=settings[4])
        return Settings(interval=40, phone_number="", telegram_userid="", email="")

    async def update_settings(self, settings: Settings):
        await execute_query("UPDATE settings SET interval = ?, phone_number = ?, telegram_userid = ?, email = ?", (settings.interval, settings.phone_number, settings.telegram_userid, settings.email))

