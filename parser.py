from classes import SelectListing, SelectPriceHistory
from bs4 import BeautifulSoup
import requests
from datetime import datetime

class ListingParser:

    def parse_id_from_url(self, url: str) -> str:
        splitted = url.split("/")
        if len(splitted) > 3:
            return splitted[-1]
        else:
            #seems invalid url
            return None
        
    def parse_title(self, bs: BeautifulSoup) -> str:
        return bs.select_one(".x-item-title__mainTitle").text.strip()

    def parse_listing(self, response: requests.Response) -> SelectListing:
        bs = BeautifulSoup(response.text, "html.parser")
        price_element = bs.select_one(".x-bin-price__content .x-price-primary .ux-textspans")
        price_history = []
        if price_element:
            price_text = price_element.text.strip()
            currency = price_text.split()[0]
            price = float(price_text.split()[-1].replace('$', '').replace('/ea', '')) 
            price_history.append(SelectPriceHistory(price=price, date=datetime.now().isoformat(), currency=currency))
        else:
            currency = None
            price = None

        stock_element = bs.select_one(".x-quantity__availability")
        stock = 0
        found = False
        if stock_element:
            quantity_elements = stock_element.select("span")
            for qe in quantity_elements:
                if qe.text == "Out of Stock":
                    found = True
                    stock = 0
                    break
            if found == False:
                quantity_element = stock_element.select_one(".ux-textspans.ux-textspans--SECONDARY") 
                try:
                    text = quantity_element.text.strip()
                    if text.startswith("More than"):
                        stock = int(text.split()[2])  # Get number after "More than"
                    else:
                        stock = int(text.split()[0])
                except (ValueError, IndexError):
                    stock = 0

        return SelectListing(
            id=self.parse_id_from_url(response.url),
            title=self.parse_title(bs),
            url=response.url,
            stock=stock,
            price_history=price_history
        )

