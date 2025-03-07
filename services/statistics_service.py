
from datetime import datetime
from classes import CustomDate
from repository.listing_repository import ListingRepository

#TODO: FINISH LATER
class StatisticsService:
    def __init__(self) -> None:
        self.listing_repository = ListingRepository()

    async def get_price_data_between_dates(self, listing_ebay_id: str, start_date: CustomDate, end_date: CustomDate ):
        listing = await self.listing_repository.get_listing_by_id(listing_ebay_id)
        #dont need too precise price movements, group them by day
        date_map = {}
        #create map with days between start and end
        current_date = datetime(start_date.year, start_date.month, start_date.day)
        while current_date <= datetime(end_date.year, end_date.month, end_date.day):
            find_result = listing.price_history.pop()

            date_map[current_date.strftime('%Y-%m-%d')] = None
