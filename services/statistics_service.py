
from datetime import datetime, timedelta
from typing import Dict, Optional
from classes import CustomDate
from repository.listing_repository import ListingRepository

#TODO: FINISH LATER
class StatisticsService:
    def __init__(self) -> None:
        self.listing_repository = ListingRepository()

    async def get_price_data_between_dates(
        self, listing_ebay_id: str, start_date: CustomDate, end_date: CustomDate
    ) -> Dict[str, Optional[float]]:
        listing = await self.listing_repository.get_listing_by_id(listing_ebay_id)
        if not listing or not listing.price_history:
            return {}
        date_map = {}
        start_datetime = start_date.to_datetime()
        end_datetime = end_date.to_datetime()
        current_datetime = start_datetime
        while current_datetime <= end_datetime:
            #get daily precision
            key = current_datetime.strftime("%d %m %Y")
            if len(listing.price_history) == 0:
                date_map[key] = 0
                continue
            existing_time = listing.price_history.pop()
            existing_datetime = datetime.strptime(existing_time.date, '%Y-%m-%dT%H:%M:%S.%f')
            if existing_datetime == current_datetime:
                date_map[key] = existing_time.price
            else:
                date_map[key] = 0
            current_datetime = current_datetime + timedelta(days=1)
        return date_map
        
    async def get_price_data_between_dates2(
        self, listing_ebay_id: str, start_date: CustomDate, end_date: CustomDate
    ) -> Dict[str, Optional[float]]:
        listing = await self.listing_repository.get_listing_by_id(listing_ebay_id)
        if not listing or not listing.price_history:
            return {}

        start_dt = datetime(start_date.year, start_date.month, start_date.day)
        end_dt = datetime(end_date.year, end_date.month, end_date.day)

        date_map = {
            (start_dt + timedelta(days=i)).strftime('%Y-%m-%d'): None
            for i in range((end_dt - start_dt).days + 1)
        }

        for price_entry in listing.price_history:
            price_date = price_entry.date  
            price_value = price_entry.price  

            if isinstance(price_date, str):
                price_date = datetime.strptime(price_date, '%Y-%m-%dT%H:%M:%S.%f')

            if start_dt <= price_date <= end_dt:
                date_key = price_date.strftime('%Y-%m-%d')
                date_map[date_key] = price_value

        return date_map