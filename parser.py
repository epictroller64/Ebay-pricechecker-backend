from classes import ScrapedListing, SelectListing, SelectPriceHistory
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
    
    def parse_listing_details(self, response: requests.Response, download_images: bool):
        basic_details = self.parse_listing(response)
        bs = BeautifulSoup(response.text, "html.parser")
        dl_elements = bs.find_all('dl', class_='ux-labels-values')
        features = {}
        for dl in dl_elements:
            key = dl.find('dt', class_='ux-labels-values__labels').get_text(strip=True)
            value = dl.find('dd', class_='ux-labels-values__values').get_text(strip=True)
            features[key] = value

        seller_url = ""
        seller_elem = bs.find("div", class_="x-sellercard-atf__info__about-seller")
        if seller_elem:
            seller_link = seller_elem.find("a")
            if seller_link: 
                seller_url = seller_link.attrs.get("href")
        image_urls = []
        if download_images:
            image_cotainer = bs.find('div', class_="ux-image-grid no-scrollbar")
            img_elements = image_cotainer.find_all('img')

            image_urls = [str(img['src']).replace("l140", "l1600") for img in img_elements if 'src' in img.attrs]

        return ScrapedListing(
                              id=basic_details.id, 
                              title=basic_details.title, 
                              url=response.url, 
                              stock=basic_details.stock,
                              price=basic_details.price_history[-1].price,
                              features=features,
                              images=image_urls,
                              scraped_at=datetime.now(),
                              seller_url=seller_url)

    def parse_listing(self, response: requests.Response) -> SelectListing:
        bs = BeautifulSoup(response.text, "html.parser")
        price_element = bs.select_one(".x-bin-price__content .x-price-primary .ux-textspans")
        price_history = []
        if price_element:
            price_text = price_element.text.strip()
            currency = price_text.split()[0]
            price = float(price_text.split()[-1].replace('$', '').replace('/ea', '').replace(",", ".")) 
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

