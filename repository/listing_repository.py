from data import select_all, execute_query
from classes import SelectListing, InsertListing, SelectPriceHistory
from typing import List, Optional

from repository.price_history_repository import PriceHistoryRepository

class ListingRepository:
    def __init__(self):
        self.listings = []

    async def get_listing_count(self, id: str) -> int:
        return await execute_query("SELECT COUNT(*) FROM listings WHERE id = ?", (id,))

    async def get_all_listings(self) -> List[SelectListing]:
        """Get all listings with their price history"""
        listings = await select_all("""
            SELECT l.*, ph.price, ph.date, ph.currency 
            FROM listings l
            LEFT JOIN price_history ph ON l.id = ph.listing_id
            ORDER BY l.created_at DESC
        """, as_dict=True)

        listing_map = {}
        for row in listings:
            if row['id'] not in listing_map:
                listing_map[row['id']] = SelectListing(
                    id=row['id'],
                    title=row['title'], 
                    url=row['url'],
                    stock=row['stock'],
                    price_history=[]
                )
            if row['price'] is not None:
                listing_map[row['id']].price_history.append(
                    SelectPriceHistory(
                        price=row['price'],
                        date=row['date'],
                        currency=row['currency']
                    )
                )
        
        return list(listing_map.values())

    async def get_listing_by_id(self, listing_id: str) -> Optional[SelectListing]:
        """Get single listing by ID with price history"""
        rows = await select_all("""
            SELECT l.*, ph.price, ph.date, ph.currency
            FROM listings l 
            LEFT JOIN price_history ph ON l.id = ph.listing_id
            WHERE l.id = ?
            ORDER BY ph.date DESC
        """, (listing_id,), as_dict=True)

        if not rows:
            return None

        listing = SelectListing(
            id=rows[0]['id'],
            title=rows[0]['title'],
            url=rows[0]['url'], 
            stock=rows[0]['stock'],
            price_history=[]
        )

        for row in rows:
            if row['price'] is not None:
                listing.price_history.append(
                    SelectPriceHistory(
                        price=row['price'],
                        date=row['date'],
                        currency=row['currency']
                    )
                )

        return listing

    async def get_listing_by_url(self, url: str) -> Optional[SelectListing]:
        """Get single listing by URL with price history"""
        rows = await select_all("""
            SELECT l.*, ph.price, ph.date, ph.currency
            FROM listings l
            LEFT JOIN price_history ph ON l.id = ph.listing_id 
            WHERE l.url = ?
            ORDER BY ph.date DESC
        """, (url,), as_dict=True)

        if not rows:
            return None

        listing = SelectListing(
            id=rows[0]['id'],
            title=rows[0]['title'],
            url=rows[0]['url'],
            stock=rows[0]['stock'],
            price_history=[]
        )

        for row in rows:
            if row['price'] is not None:
                listing.price_history.append(
                    SelectPriceHistory(
                        price=row['price'],
                        date=row['date'],
                        currency=row['currency']
                    )
                )

        return listing

    async def upsert_listing(self, listing: InsertListing) -> str:
        """Insert or update listing in database"""
        await execute_query("""
            INSERT INTO listings (id, title, url, stock) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                stock = excluded.stock
        """, (listing.id, listing.title, listing.url, listing.stock))
        return listing.id

    async def delete_listing(self, listing_id: str) -> bool:
        """Delete listing and associated price history from database"""
        await PriceHistoryRepository().delete_price_history(listing_id)
        result = await execute_query("DELETE FROM listings WHERE id = ?", (listing_id,))
        return result > 0