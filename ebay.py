import requests
from classes import SelectListing
from errors import InvalidUrlError, ListingNotFoundError
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
            if e.response.status_code == 404:
                raise ListingNotFoundError(f"Listing not found: {url}")
            elif e.response.status_code == 400:
                raise InvalidUrlError(f"Invalid URL: {url}")
            else:
                raise e

    def get_listing(self, url: str) -> SelectListing:
        response = self.get_response(url)
        return self.parser.parse_listing(response)
