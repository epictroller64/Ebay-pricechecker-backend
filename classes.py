
from datetime import datetime
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



class Settings(BaseModel):
    interval: int
    phone_number: str
    telegram_userid: str
    email: str


class SelectReminder(BaseModel):
    id: str
    method: str
    target_product_id: str
    type: str

    def to_dict(self):
        return {
            "id": self.id,
            "method": self.method,
            "target_product_id": self.target_product_id,
            "type": self.type
        }

class InsertReminder(BaseModel):
    method: str
    target_product_id: str
    type: str

    def to_dict(self):
        return {
            "method": self.method,
            "target_product_id": self.target_product_id,
            "type": self.type
        }


class CustomDate(BaseModel):
    day: int
    month: int
    year: int

    def __str__(self) -> str:
        return super().__str__(f"{self.day} {self.month} {self.year}")

    def to_datetime(self) -> datetime:
        return datetime(day=self.day, month=self.month, year=self.year)



class SelectUser(BaseModel):
    id: str
    password: str
    email: str
    created_at: datetime

class InsertUser(BaseModel):
    password: str
    email: str
    created_at: datetime

class Token:
    email: str
    id: str

class LoginUser(BaseModel):
    email: str
    password: str

class RegisterUser(BaseModel):
    email: str
    password: str
    repeat_password: str