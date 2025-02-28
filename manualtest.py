from ebay import Ebay
from checker import Checker
checker = Checker()
listings = checker.get_all_listings()
for listing in listings:
    print(listing)
