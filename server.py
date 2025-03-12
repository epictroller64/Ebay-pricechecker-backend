import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Query
from checker import Checker
import uvicorn
from pydantic import BaseModel
import logging
from errors import InvalidUrlError, ListingNotFoundError
from services.listing_service import ListingService
from services.reminder_service import ReminderService
from classes import CustomDate, Settings
from data import init_db
from services.settings_service import SettingsService
from services.statistics_service import StatisticsService
from telegram_bot import telegram_app
from dotenv import load_dotenv

API_VERSION = 1.01

load_dotenv(override=True)

checker = Checker()

class ListingRequest(BaseModel):
    url: str

class ListingDeleteRequest(BaseModel):
    id: str

class ReminderRequest(BaseModel):
    method: str
    target_product_id: str
    type: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the update loop task
    await init_db()
    run_tg = os.getenv("RUN_TG") or "TRUE"
    if run_tg == "FALSE":
        run_tg = False
    else:
        run_tg = True
    asyncio.create_task(checker.update_loop())
    if run_tg:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()

    yield
    if run_tg:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()


app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/api/api-version')
def get_apiversion_handler():
    return {"version": API_VERSION}

@app.get('/api/reminders')
async def get_reminders_handler():
    return await ReminderService().reminder_repository.get_reminders()

@app.post('/api/reminders')
async def add_reminder_handler(reminder: ReminderRequest):
    try:
        await ReminderService().reminder_repository.add_reminder(reminder)
        return {"success": True}
    except Exception as e:
        print(str(e))
        return {"success": False}

@app.get('/api/settings')
async def get_settings_handler():
    return await SettingsService().settings_repository.get_settings()

@app.post('/api/settings')
async def update_settings_handler(settings: Settings):
    await SettingsService().settings_repository.update_settings(settings.interval)

@app.get("/api/listings")
async def get_listings_handler():
    listings = await ListingService().listing_repository.get_all_listings()
    # Convert listings to a list of dictionaries
    listings_json = [listing.to_dict() for listing in listings]
    return listings_json

@app.post("/api/listings")
async def add_listing_handler(listing: ListingRequest):
    try:
        insert_result = await checker.add_or_update_listing(listing.url)
        if insert_result:
            return {"success": True, "id": insert_result}
        else:
            raise HTTPException(status_code=500, detail="Failed to add listing")
    except InvalidUrlError as e:
        print(str(e))
        return {"success": False, "error": "Invalid URL"}
    except ListingNotFoundError as e:
        print(str(e))
        return {"success": False, "error": "Listing not found"}

@app.delete("/api/listings")
async def delete_listing_handler(id: str = Query(..., description="Listing id")):
    try:
        delete_result = await ListingService().listing_repository.delete_listing(id)
        if delete_result:
            return {"success": True}
    except Exception as e:
        print(str(e))
        return 

@app.delete("/api/reminders")
async def delete_listing_handler(id: str = Query(..., description="Reminder id")):
    try:
        delete_result = await ReminderService().reminder_repository.delete_reminder(id)
        if delete_result:
            return {"success": True}
        return {"success": False}
    except Exception as e:
        print(str(e))
        return {"success": False, "error": "Failed to delete reminders"}

@app.get("/api/next-update")
async def get_next_update_handler():
    next_update, interval = await checker.get_next_update()
    return {"nextUpdate": next_update, "interval": interval}


@app.get("/api/test-statistics")
async def test_stats_handler():
    start_date = CustomDate(day=9, month=3, year=2025)
    end_date = CustomDate(day=10, month=3, year=2025)
    stats = await StatisticsService().get_price_data_between_dates(listing_ebay_id="256430205325", start_date=start_date, end_date=end_date)
    return {"success": True, "data": stats}
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
