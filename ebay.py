import requests
from classes import SelectListing
from parser import ListingParser

class Ebay:
    def __init__(self):
        self.parser = ListingParser()

    def get_response(self, url: str) -> requests.Response:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_listing(self, url: str) -> SelectListing:
        response = self.get_response(url)
        return self.parser.parse_listing(response)
