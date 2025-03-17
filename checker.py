from classes import InsertPriceHistory, Settings
from ebay import Ebay
import time
import asyncio
import logging
from typing import List

from services.price_history_service import PriceHistoryService
from services.reminder_service import ReminderService
from services.listing_service import ListingService
from services.settings_service import SettingsService

class Checker:
    def __init__(self):
        self.ebay = Ebay()
        self.settings = Settings(interval=20, phone_number="", telegram_userid="", email="")
        self.next_update = int(time.time() + self.settings.interval)
        self.logger = logging.getLogger(__name__)
        self.reminder_service = ReminderService()
        self.listing_service = ListingService()
        self.settings_service = SettingsService()
        self.price_history_service = PriceHistoryService()

    async def refresh_settings(self):
        self.settings = await self.settings_service.settings_repository.get_settings()

    async def get_next_update(self):
        await self.refresh_settings()
        return self.next_update, self.settings.interval
    
    async def set_next_update(self):
        await self.refresh_settings()
        self.next_update = int(time.time() + self.settings.interval)

    async def update_loop(self):
        while True:
            try:
                await self.refresh_settings()
                sleep_time = max(0, self.next_update - time.time())
                self.logger.info(f"Sleeping for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
                await self.set_next_update()
                await self.update_listings()
            except Exception as e:
                self.logger.error(f"Error in update loop: {str(e)}")
                await asyncio.sleep(10)  # Prevent tight loop on error
    
    async def delete_listing(self, id: str):
        await self.listing_service.listing_repository.delete_listing(id)

    async def update_listings(self):
        listings = await self.listing_service.listing_repository.get_all_listings()
        promises = []
        for listing in listings:
            promises.append(self.add_or_update_listing(listing.url))
        results = await asyncio.gather(*promises, return_exceptions=True)
        for result in results:
            if result:
                if result == BaseException:
                    print(str(result))
                print(f"Upserted listing {listing.url} with id {result['id']}")
    
    async def add_or_update_listing(self, url: str):
        if not self.validate_url(url):
            self.logger.error(f"Invalid eBay URL: {url}")
            return None
        existing_listing = await self.listing_service.listing_repository.get_listing_by_url(url)
        parsed_listing = self.ebay.get_listing(url)
        if existing_listing:
            await self.reminder_service.reminder_repository.get_reminders_by_target_product_id(existing_listing.id)
            await self.reminder_service.remind_stock_status(existing_listing, parsed_listing)
            
        if parsed_listing:
            await self.listing_service.listing_repository.upsert_listing(parsed_listing)
            
            listing_id = parsed_listing.id
            was_inserted = await self.listing_service.listing_repository.get_listing_count(listing_id) == 0
            
            if parsed_listing.price_history:
                for price_history in parsed_listing.price_history:
                    insert_id = await self.add_price_history(parsed_listing.id, price_history)
                    print(f"Inserted price history with id: {insert_id}")
            
            return {
                "id": listing_id,
                "action": "inserted" if was_inserted else "updated"
            }
        else:
            return None
    

    async def add_price_history(self, listing_id: str, pricehistory: InsertPriceHistory):
        insert_id = await self.price_history_service.price_history_repository.add_price_history(listing_id, pricehistory)
        return insert_id

    async def add_price_histories(self, listing_id: str, 
                                price_histories: List[InsertPriceHistory]) -> List[int]:
        return await self.price_history_service.price_history_repository.add_many_price_histories(listing_id, price_histories)


    async def get_all_listings(self):
        return await self.listing_service.get_all_listings()


    def validate_url(self, url: str) -> bool:
        """Validate eBay URL format"""
        cleaned_url = ''.join(char for char in url if not char.isspace())
        return cleaned_url.startswith('https://www.ebay.') and '/itm/' in cleaned_url

