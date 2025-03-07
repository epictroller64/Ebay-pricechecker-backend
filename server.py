import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from checker import Checker
import uvicorn
from pydantic import BaseModel
import logging
from errors import InvalidUrlError, ListingNotFoundError
from services.listing_service import ListingService
from services.reminder_service import ReminderService
from classes import Settings
from data import init_db
from services.settings_service import SettingsService
from telegram_bot import telegram_app
from dotenv import load_dotenv

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

@app.get('/api/reminders')
async def get_reminders_handler():
    return await ReminderService().reminder_repository.get_reminders()

@app.post('/api/reminders')
async def add_reminder_handler(reminder: ReminderRequest):
    return await ReminderService().reminder_repository.add_reminder(reminder)

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
        return {"success": False, "error": "Invalid URL"}
    except ListingNotFoundError as e:
        return {"success": False, "error": "Listing not found"}

@app.delete("/api/listings")
async def delete_listing_handler(listing: ListingDeleteRequest):
    delete_result = await ListingService().listing_repository.delete_listing(listing.id)
    if delete_result:
        return {"success": True}

@app.get("/api/next-update")
async def get_next_update_handler():
    next_update, interval = await checker.get_next_update()
    return {"nextUpdate": next_update, "interval": interval}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
