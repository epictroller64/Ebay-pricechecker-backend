import time
from data import select_all, execute_query, select_one
from classes import DisplayListing, SelectListing, InsertListing, SelectPriceHistory
from typing import List, Optional

from repository.listing_relations_repository import ListingRelationsRepository
from repository.price_history_repository import PriceHistoryRepository

class ListingRepository:
    def __init__(self):
        self.listings = []
        self.listing_relation_repo = ListingRelationsRepository()

    async def get_listing_count(self, id: str) -> int:
        return await execute_query("SELECT COUNT(*) FROM listings WHERE id = ?", (id,))

    async def get_all_listings_display(self) -> List[DisplayListing]:
        """Get all listings suitable for frontend display. More efficent processing."""
        start_time = time.time()
        listings = await select_all("""
            SELECT l.*, ph.price, ph.date, ph.currency 
            FROM listings l
            LEFT JOIN price_history ph ON l.id = ph.listing_id
            ORDER BY ph.date ASC
        """, as_dict=True)

        listing_map = {}
        for row in listings:
            existing_listing = listing_map.get(row['id'], None) 
            price_change = 0
            if existing_listing and existing_listing.price != row['price']:
                #found price change
                price_change = row['price'] - existing_listing.price
            if price_change != 0 or existing_listing is None:
                listing_map[row['id']] = DisplayListing(
                    id=row['id'],
                    title=row['title'], 
                    url=row['url'],
                    stock=row['stock'],
                    price=row['price'],
                    last_price_change=price_change
                )
        end_time = time.time()
        finish_time = end_time - start_time
        print(f"Time taken: {finish_time:.2f} seconds")
        return list(listing_map.values())

    async def get_all_listings_base(self) -> List[SelectListing]:
        """Get all listings without price history attatched, only last one attatched"""
        listings = await select_all("""
                                    SELECT l.*, ph.price, ph.date, ph.currency
                FROM listings l
                LEFT JOIN (
                    SELECT *, ROW_NUMBER() OVER (PARTITION BY listing_id ORDER BY date DESC) AS rn
                    FROM price_history
                ) ph ON l.id = ph.listing_id AND ph.rn = 1
                ORDER BY l.created_at DESC;
""", as_dict=True)
        final_listings = [
            SelectListing(
                id=row['id'],
                title=row['title'],
                url=row['url'],
                stock=row['stock'],
                price_history=[SelectPriceHistory(
                        price=row['price'],
                        date=row['date'],
                        currency=row['currency'])]
            ) for row in listings
        ]
        return final_listings


    
    async def get_all_listings_by_user_id(self, user_id: str) -> List[SelectListing]:
        listing_relations = await self.listing_relation_repo.get_listing_relations_by_user_id(user_id)

        listings = []
        for lr in listing_relations:
            listing = await select_one("""
            SELECT l.*, ph.price, ph.date, ph.currency 
            FROM listings l
            LEFT JOIN price_history ph ON l.id = ph.listing_id
            WHERE l.id = ? 
        """, (lr['listing_id'], ), as_dict=True)
            listings.append(listing)
        listing_map = {}
        for row in listings:
            existing_listing = listing_map.get(row['id'], None) 
            price_change = 0
            if existing_listing and existing_listing.price != row['price']:
                #found price change
                price_change = row['price'] - existing_listing.price
            if price_change != 0 or existing_listing is None:
                listing_map[row['id']] = DisplayListing(
                    id=row['id'],
                    title=row['title'], 
                    url=row['url'],
                    stock=row['stock'],
                    price=row['price'],
                    last_price_change=price_change
                )
        return list(listing_map.values())

    async def get_all_listings(self) -> List[SelectListing]:
        """Get all listings with their price history"""
        start_time = time.time()
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
        end_time = time.time()
        finish_time = end_time - start_time
        print(f"Time taken: {finish_time:.2f} seconds")
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

    async def upsert_listing(self, listing: InsertListing, user_id: Optional[str]) -> str:
        """Insert or update listing in database"""
        await execute_query("""
            INSERT INTO listings (id, title, url, stock) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                stock = excluded.stock
        """, (listing.id, listing.title, listing.url, listing.stock))
        if user_id:
            ## Also insert listing relation
            await self.listing_relation_repo.insert_listing_relation(user_id, listing.id)
        return listing.id


    async def delete_listing(self, listing_id: str, user_id: str) -> bool:
        await self.listing_relation_repo.delete_listing_relation(listing_id, user_id)
        ## Check if no more users have this listing linked, delete it entirely
        listing_relations = await self.listing_relation_repo.get_listing_relations_by_listing_id(listing_id)
        if len(listing_relations) == 0:
            await PriceHistoryRepository().delete_price_history(listing_id)
            result = await execute_query("DELETE FROM listings WHERE id = ?", (listing_id,))
            return result > 0
