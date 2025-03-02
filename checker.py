from classes import InsertListing, SelectListing, InsertPriceHistory, SelectPriceHistory
from data import select_all, execute_query
from ebay import Ebay
import time
import asyncio

class Checker:
    def __init__(self, update_interval: int = 20):
        self.ebay = Ebay()
        self.update_interval = update_interval
        self.next_update = int(time.time() + update_interval)

    async def get_next_update(self):
        return self.next_update
    
    def set_next_update(self):
        self.next_update = int(time.time() + self.update_interval)

    async def update_loop(self):
        while True:
            sleep_time = self.next_update - time.time()
            print(f"sleep_time: {sleep_time}")
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            await self.update_listings()
            self.set_next_update()
    
    async def delete_listing(self, id: str):
        await execute_query("DELETE FROM listings WHERE id = ?", (id,))
        await execute_query("DELETE FROM price_history WHERE listing_id = ?", (id,))

    async def update_listings(self):
        listings = await self.get_all_listings()
        for listing in listings:
            upsert_result = await self.add_or_update_listing(listing.url)
            if upsert_result:
                print(f"Upserted listing {listing.url} with id {upsert_result['id']}")
    
    async def add_or_update_listing(self, url: str):
        parsed_listing = self.ebay.get_listing(url)
        if parsed_listing:
            result = await execute_query("""
                INSERT INTO listings (id, title, url, stock) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url, 
                    stock = excluded.stock;
            """, (parsed_listing.id, parsed_listing.title, parsed_listing.url, parsed_listing.stock))
            
            listing_id = parsed_listing.id
            was_inserted = await execute_query("SELECT COUNT(*) FROM listings WHERE id = ?", (listing_id,)) == 0
            
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
        insert_id = await execute_query("INSERT INTO price_history (listing_id, price, date, currency) VALUES (?, ?, ?, ?)", (listing_id, pricehistory.price, pricehistory.date, pricehistory.currency))
        return insert_id

    def check_listings(self):
        pass


    async def get_all_listings(self):
        listings = await select_all("SELECT * FROM listings", as_dict=True)
        selectlistings = [SelectListing(id=listing["id"], title=listing["title"], url=listing["url"], stock=listing["stock"], price_history=[]) for listing in listings]
        for listing in selectlistings:
            price_history = await select_all("SELECT * FROM price_history WHERE listing_id = ? ORDER BY date DESC", (listing.id,), as_dict=True)
            listing.price_history = [SelectPriceHistory(price=price_history["price"], date=price_history["date"], currency=price_history["currency"]) for price_history in price_history]
        return selectlistings

