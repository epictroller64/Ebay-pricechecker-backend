from repository.reminder_repository import ReminderRepository
from classes import SelectListing, SelectReminder
from telegram_bot import telegram_app, RECIPENT_ID

class ReminderService:
    def __init__(self):
        self.reminder_repository = ReminderRepository()

    async def get_reminders(self):
        await self.reminder_repository.get_reminders()

    async def remind_stock_status(self, new_listing: SelectListing, prev_listing: SelectListing):
        reminders = await self.reminder_repository.get_reminders_by_target_product_id(new_listing.id)
        if new_listing.stock == 0 and prev_listing.stock > 0:
            for reminder in reminders:
                if reminder.type == "out_of_stock" and reminder.target_product_id == new_listing.id:
                    await self.send_reminder(reminder, new_listing)
        elif new_listing.stock > 0 and prev_listing.stock == 0:
            for reminder in reminders:
                if reminder.type == "back_in_stock" and reminder.target_product_id == new_listing.id:
                    await self.send_reminder(reminder, new_listing)
    
    async def remind_price_status(self, new_listing: SelectListing, prev_listing: SelectListing):
        reminders = await self.reminder_repository.get_reminders_by_target_product_id(new_listing.id)
        if new_listing.price_history[0].price < prev_listing.price_history[0].price:
            for reminder in reminders:
                if reminder.type == "price_drop" and reminder.target_product_id == new_listing.id:
                    await self.send_reminder(reminder, new_listing)
        elif new_listing.price_history[0].price > prev_listing.price_history[0].price:
            for reminder in reminders:
                if reminder.type == "price_increase" and reminder.target_product_id == new_listing.id:
                    await self.send_reminder(reminder, new_listing)

    async def send_reminder(self, reminder: SelectReminder, listing: SelectListing):
        match reminder.method:
            case "telegram":
                await self.send_telegram_reminder(reminder, listing)
            case "sms":
                await self.send_sms_reminder(reminder, listing)
            case "email":
                await self.send_email_reminder(reminder, listing)
    
    async def send_telegram_reminder(self, reminder: SelectReminder, listing: SelectListing):
        print(f"Sending telegram reminder for {listing.id}")
        reminder_message = ""
        match reminder.type:
            case "out_of_stock":
                reminder_message = f"❌ {listing.title} is now out of stock\n\nView listing: {listing.url}"
            case "back_in_stock":
                reminder_message = f"✅ {listing.title} is back in stock!\n\nQuantity available: {listing.stock}\nPrice: {listing.price_history[0].currency} {listing.price_history[0].price}\n\nView listing: {listing.url}"
            case "price_drop":
                old_price = listing.price_history[1].price if len(listing.price_history) > 1 else None
                new_price = listing.price_history[0].price
                diff = old_price - new_price if old_price else None
                reminder_message = f"📉 Price dropped for {listing.title}!\n\nNew price: {listing.price_history[0].currency} {new_price}"
                if diff:
                    reminder_message += f"\nPrice difference: {listing.price_history[0].currency} {diff:.2f}"
                reminder_message += f"\n\nView listing: {listing.url}"
            case "price_increase":
                old_price = listing.price_history[1].price if len(listing.price_history) > 1 else None
                new_price = listing.price_history[0].price
                diff = new_price - old_price if old_price else None
                reminder_message = f"📈 Price increased for {listing.title}!\n\nNew price: {listing.price_history[0].currency} {new_price}"
                if diff:
                    reminder_message += f"\nPrice difference: {listing.price_history[0].currency} {diff:.2f}"
                reminder_message += f"\n\nView listing: {listing.url}"
        await telegram_app.bot.send_message(chat_id=RECIPENT_ID, text=reminder_message)

    async def send_sms_reminder(self, reminder: SelectReminder, listing: SelectListing):
        print(f"Sending sms reminder for {listing.id}")

    async def send_email_reminder(self, reminder: SelectReminder, listing: SelectListing):
        print(f"Sending email reminder for {listing.id}")

