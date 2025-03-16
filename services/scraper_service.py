

import csv
from datetime import datetime
import os
import zipfile
import requests
from classes import ScrapedListing
from ebay import Ebay
from repository.zip_repository import ZipRepository


class ScraperService:
    def __init__(self) -> None:
        self.ebay = Ebay()
        self.zip_repository = ZipRepository()

    async def scrape_listing_details(self, url: str, download_images: bool):
        listing_details = self.ebay.get_listing_details(url, download_images)
        downloaded_images = self.download_images(listing_details.images)
        created_sheet = self.create_sheet(listing_details)
        downloaded_images.append(created_sheet)
        zipped_file = self.zip_files(downloaded_images)
        zip_hash_id = await self.zip_repository.insert_zip(zipped_file)
        return zip_hash_id, listing_details

    def zip_files(self, paths):
        try:
            zip_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + 'listing' + '.zip'
            with zipfile.ZipFile(zip_filename, "w") as zip: 
                for path in paths:
                    zip.write(path, os.path.basename(path))
            return zip_filename
        except Exception as e:
            print("Failed to ZIP files")
            print(str(e))

    def create_sheet(self, listing: ScrapedListing):
        try:
            output_file = os.path.abspath(f"{listing.id}_sheet.csv")
            with open(output_file, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=listing.model_dump().keys())
                writer.writeheader()
                writer.writerow(listing.model_dump())
            return output_file
        except Exception as e:
            print("Failed to create sheet")
            print(str(e))
    
    def download_images(self, images):
        PATH = "IMAGES"
        downloaded_files = []
        try:
            for url in images:
                resp = requests.get(url, stream=True)
                splitted_parts = url.split("images/g/")
                name = splitted_parts[-1].replace("/", "-")
                if resp.status_code == 200:
                    file_path = os.path.abspath(f"{PATH}/{name}")
                    with open(file_path, "wb") as file:
                        for chunk in resp.iter_content(chunk_size=8192):
                            file.write(chunk)
                        downloaded_files.append(file_path)
            return downloaded_files
        except Exception as e:
            print(str(e))