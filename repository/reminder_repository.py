
from classes import SelectReminder, InsertReminder
from data import select_all, execute_query


class ReminderRepository:
    def __init__(self):
        self.reminders = []

    async def get_and_update_reminders(self):
        reminders = await select_all("SELECT * FROM reminders", as_dict=True)
        self.reminders = [SelectReminder(id=reminder['id'], method=reminder['method'], target_product_id=reminder['target_product_id'], type=reminder['type']) for reminder in reminders]
        return self.reminders

    async def add_reminder(self, reminder: InsertReminder):
        #check if already exists
        await self.get_and_update_reminders()
        if [x for x in self.reminders if x.method == reminder.method and x.target_product_id == reminder.target_product_id]:
            return
        await execute_query("INSERT INTO reminders (method, target_product_id, type) VALUES (?, ?, ?)", (reminder.method, reminder.target_product_id, reminder.type))

    async def delete_reminder(self, reminder_id: str):
        await execute_query("DELETE FROM reminders WHERE id = ?", (reminder_id,))

    async def get_reminders_by_target_product_id(self, target_product_id: str, use_cache: bool = False):
        if use_cache:
            result = [x for x in self.reminders if x.target_product_id == target_product_id]
            return result
        reminders = await select_all("SELECT * FROM reminders WHERE target_product_id = ?", (target_product_id,), as_dict=True)
        return [SelectReminder(id=reminder['id'], method=reminder['method'], target_product_id=reminder['target_product_id'], type=reminder['type']) for reminder in reminders]

    async def get_reminders_by_method(self, method: str, use_cache: bool = False):
        if use_cache:
            result = [x for x in self.reminders if x.method == method]
            return result
        reminders = await select_all("SELECT * FROM reminders WHERE method = ?", (method,), as_dict=True)
        return [SelectReminder(id=reminder['id'], method=reminder['method'], target_product_id=reminder['target_product_id'], type=reminder['type']) for reminder in reminders]


