from classes import Settings
from data import execute_query, select_one

class SettingsRepository:
    

    async def get_settings_by_user_id(self, user_id: str) -> Settings:
        settings = await select_one("SELECT * FROM settings WHERE user_id = ?", (user_id, ))
        if settings:
            return Settings(interval=settings[1], phone_number=settings[2], telegram_userid=settings[3], email=settings[4], user_id=settings[5])
        return Settings(interval=40, phone_number="", telegram_userid="", email="", user_id="")

    async def get_settings(self) -> Settings:
        settings = await select_one("SELECT * FROM settings")
        if settings:
            return Settings(interval=settings[1], phone_number=settings[2], telegram_userid=settings[3], email=settings[4], user_id="")
        return Settings(interval=40, phone_number="", telegram_userid="", email="", user_id="")
    
    async def insert_settings(self, settings: Settings):
        await execute_query("INSERT INTO settings (interval, phone_number, telegram_userid, email, user_id) VALUES (? , ?, ?, ?, ?)", (settings.interval, settings.phone_number, settings.telegram_userid, settings.email, settings.user_id))

    async def update_settings(self, settings: Settings):
        await execute_query("UPDATE settings SET interval = ?, phone_number = ?, telegram_userid = ?, email = ? WHERE user_id = ?", (settings.interval, settings.phone_number, settings.telegram_userid, settings.email, settings.user_id))

