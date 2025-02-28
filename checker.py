from classes import InsertListing, SelectListing, InsertPriceHistory, SelectPriceHistory
from data import select_all, execute_query
from ebay import Ebay

class Checker:
    def __init__(self):
        self.ebay = Ebay()
    
    async def add_listing(self, url: str):
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

    def check_listing(self, listing: SelectListing):
        pass

    async def get_all_listings(self):
        listings = await select_all("SELECT * FROM listings", as_dict=True)
        selectlistings = [SelectListing(id=listing["id"], title=listing["title"], url=listing["url"], stock=listing["stock"], price_history=[]) for listing in listings]
        for listing in selectlistings:
            price_history = await select_all("SELECT * FROM price_history WHERE listing_id = ?", (listing.id,), as_dict=True)
            listing.price_history = [SelectPriceHistory(price=price_history["price"], date=price_history["date"], currency=price_history["currency"]) for price_history in price_history]
        return selectlistings

