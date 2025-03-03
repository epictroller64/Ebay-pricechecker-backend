from typing import List
from classes import InsertPriceHistory, SelectPriceHistory
from data import execute_query_many, select_all, execute_query


class PriceHistoryRepository:
    def __init__(self):
        self.price_history = []

    async def get_price_history(self, listing_id: str):
        results = await select_all("SELECT * FROM price_history WHERE listing_id = ?", (listing_id,), as_dict=True)
        return [SelectPriceHistory(price=result["price"], date=result["date"], currency=result["currency"]) for result in results]

    async def add_price_history(self, listing_id: str, price_history: InsertPriceHistory):
        return await execute_query("INSERT INTO price_history (listing_id, price, date, currency) VALUES (?, ?, ?, ?)", (listing_id, price_history.price, price_history.date, price_history.currency))

    async def delete_price_history(self, listing_id: str):
        return await execute_query("DELETE FROM price_history WHERE listing_id = ?", (listing_id,))
    
    async def add_many_price_histories(self, listing_id: str, price_histories: List[InsertPriceHistory]):
        values = [(listing_id, ph.price, ph.date, ph.currency) 
                 for ph in price_histories]
        
        query = """
            INSERT INTO price_history (listing_id, price, date, currency)
            VALUES (?, ?, ?, ?)
        """
        return await execute_query_many(query, values)
