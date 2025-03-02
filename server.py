from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from checker import Checker
import asyncio
import uvicorn
from pydantic import BaseModel

from classes import Settings
from data import init_db
from settings import get_settings, update_settings


checker = Checker()

class ListingRequest(BaseModel):
    url: str

class ListingDeleteRequest(BaseModel):
    id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the update loop task
    await init_db()
    asyncio.create_task(checker.update_loop())
    yield
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/api/settings')
async def get_settings_handler():
    return await get_settings()

@app.post('/api/settings')
async def update_settings_handler(settings: Settings):
    await update_settings(settings.interval)

@app.get("/api/listings")
async def get_listings_handler():
    listings = await checker.get_all_listings()
    # Convert listings to a list of dictionaries
    listings_json = [listing.to_dict() for listing in listings]
    return listings_json

@app.post("/api/listings")
async def add_listing_handler(listing: ListingRequest):
    insert_result = await checker.add_or_update_listing(listing.url)
    if insert_result:
        return {"success": True, "id": insert_result}
    else:
        raise HTTPException(status_code=500, detail="Failed to add listing")

@app.delete("/api/listings")
async def delete_listing_handler(listing: ListingDeleteRequest):
    delete_result = await checker.delete_listing(listing.id)
    if delete_result:
        return {"success": True}

@app.get("/api/next-update")
async def get_next_update_handler():
    next_update = await checker.get_next_update()
    return {"nextUpdate": next_update, "interval": 20}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)