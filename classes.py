
from pydantic import BaseModel
from typing import List

class InsertPriceHistory(BaseModel):
    price: float
    date: str
    currency: str

class SelectPriceHistory(BaseModel):
    price: float
    date: str
    currency: str

    def to_dict(self):
        return {
            "price": self.price,
            "date": self.date,
            "currency": self.currency
        }

class InsertListing(BaseModel):
    id: str
    title: str
    url: str
    stock: int

class SelectListing(BaseModel):
    id: str
    title: str
    url: str
    stock: int
    price_history: List[SelectPriceHistory]

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "stock": self.stock,
            "price_history": [price_history.to_dict() for price_history in self.price_history]
        }



