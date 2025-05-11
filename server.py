import asyncio
import os
import time
from fastapi import Depends, FastAPI, HTTPException, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Query
from fastapi.responses import FileResponse
from checker import Checker
from pydantic import BaseModel
import logging
from errors import InvalidUrlError, ListingNotFoundError
from repository.listing_repository import ListingRepository
from repository.zip_repository import ZipRepository
from services.ws_service import ws_service
from services.auth_service import AuthService
from services.listing_service import ListingService
from services.reminder_service import ReminderService
from classes import CustomDate, LoginUser, RegisterUser, SelectUser, Settings, Token
from data import init_db
from services.scraper_service import ScraperService
from services.settings_service import SettingsService
from services.statistics_service import StatisticsService
from telegram_bot import telegram_app
from dotenv import load_dotenv


API_VERSION = 1.30

load_dotenv(override=True)

allowed_origins = [
    "https://ebay-price-checker-front-end.vercel.app",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://app.ohh.ee",
    "https://ebay.ohh.ee"
]

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
checker = Checker()

class ListingRequest(BaseModel):
    url: str

class ListingDeleteRequest(BaseModel):
    id: str

class ReminderRequest(BaseModel):
    method: str
    target_product_id: str
    type: str

async def validate_user(request: Request):
    auth_service = AuthService()
    session_token = request.cookies.get("session_token", None)
    if not session_token:
        raise HTTPException(status_code=401, detail="Token not sent")
    validation_result = await auth_service.validate_user(session_token)
    if not validation_result.get('success'):
        raise HTTPException(status_code=401, detail=validation_result['error'])
    if validation_result.get('body').get('user'):
        return validation_result.get('body').get('user')
    else:
        raise HTTPException(status_code=401, detail="No user found")

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
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"], 
)


@app.get('/api/api-version')
def get_apiversion_handler():
    return {"version": API_VERSION}

@app.get('/api/reminders')
async def get_reminders_handler(user: SelectUser = Depends(validate_user)):
    return {"success": "OK", "body": await ReminderService().reminder_repository.get_and_update_reminders()}

@app.post('/api/reminders')
async def add_reminder_handler(reminder: ReminderRequest, user: SelectUser = Depends(validate_user)):
    try:
        await ReminderService().reminder_repository.add_reminder(reminder)
        return {"success": "Ok"}
    except Exception as e:
        print(str(e))
        return {"error": "Failed"}

@app.get('/api/settings')
async def get_settings_handler(user: SelectUser = Depends(validate_user)):
    return {"success": "OK", "body": await SettingsService().settings_repository.get_settings_by_user_id(user.id)}


@app.post('/api/settings')
async def update_settings_handler(settings: Settings, user: SelectUser = Depends(validate_user)):
    await SettingsService().settings_repository.update_settings(settings)
    return {"success": "OK"}

@app.get("/api/listings")
async def get_listings_handler(user: SelectUser = Depends(validate_user)):
    start = time.time()
    listings = await ListingService().listing_repository.get_all_listings_by_user_id(user.id)
    # Convert listings to a list of dictionaries
    end = time.time()
    elapsed = end - start
    print(f"Listings handler: {elapsed:.2f}")
    return {"success": "OK", "body": listings}

@app.post("/api/listings")
async def add_listing_handler(listing: ListingRequest, user: SelectUser = Depends(validate_user)):
    try:
        existing_listing = await ListingRepository().get_listing_by_url(listing.url)
        insert_result = await checker.add_or_update_listing(listing.url, existing_listing, user.id)
        if insert_result:
            return {"success": "OK", "body": {"id": insert_result}}
        else:
            raise HTTPException(status_code=500, detail="Failed to add listing")
    except InvalidUrlError as e:
        print(str(e))
        return { "error": "Invalid URL"}
    except ListingNotFoundError as e:
        print(str(e))
        return {"error": "Listing not found"}

@app.delete("/api/listings")
async def delete_listing_handler(id: str = Query(..., description="Listing id"), user: SelectUser = Depends(validate_user)):
    try:
        delete_result = await ListingService().listing_repository.delete_listing(id)
        if delete_result:
            return {"success": "Ok"}
    except Exception as e:
        print(str(e))
        return  {"error": "Failed"}

@app.delete("/api/reminders")
async def delete_listing_handler(id: str = Query(..., description="Reminder id"), user: SelectUser = Depends(validate_user)):
    try:
        delete_result = await ReminderService().reminder_repository.delete_reminder(id)
        if delete_result:
            return {"success": "Deleted successfully"}
        return {"error": "Failed"}
    except Exception as e:
        print(str(e))
        return {"error": "Failed to delete reminders"}

@app.get("/api/next-update")
async def get_next_update_handler(user: SelectUser = Depends(validate_user)):
    start = time.time()
    next_update, interval = await checker.get_next_update()
    end = time.time()
    elapsed = end - start
    print(f"Nextupdate handler: {elapsed:.2f}")
    return {"success": "OK", "body": {"nextUpdate": next_update, "interval": interval}}


@app.get("/api/test-statistics")
async def test_stats_handler():
    start_date = CustomDate(day=9, month=3, year=2025)
    end_date = CustomDate(day=10, month=3, year=2025)
    stats = await StatisticsService().get_price_data_between_dates(listing_ebay_id="256430205325", start_date=start_date, end_date=end_date)
    return {"success": "OK", "body": stats}


@app.post("/api/register")
async def register_handler(user: RegisterUser, response: Response):
    auth_service = AuthService()
    register_response = await auth_service.register(user)
    if register_response.get('success'):
        session_token = register_response["body"]["token"]
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            domain=".ohh.ee",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=True,  
            samesite="none",
        )

        return {"success": "Registration successful", "body": {"session_token": session_token, "user_id": register_response['body']['user_id']}}
    return register_response

@app.post("/api/login")
async def login_handler(user: LoginUser, response: Response):
    auth_service = AuthService()
    login_resp = await auth_service.login(user)
    if login_resp.get("success"):
        session_token = login_resp["body"]["token"]
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            domain=".ohh.ee",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=True,  
            samesite="none",
        )
        return {"success": "User logged in", "body": {"session_token": session_token, "user_id": login_resp['body']['user_id']}}
    return login_resp

@app.get("/api/logout")
def logout_handler(response: Response):
    response.set_cookie(
        key="session_token",
        value='',
        httponly=True,
        max_age=-1,
        secure=False,
        domain=".ohh.ee",
        samesite="Lax"
    )
    return {"success": "User logged out"}

@app.get("/api/auth-validate")
async def auth_handler(user: SelectUser = Depends(validate_user)):
    print("Authed user: ", user.id)
    return {"success": "User validated"}

@app.get("/api/listing-details")
async def listing_details_handler(
    url: str = Query(..., description="Ebay URL"),
     download_images: bool = Query(..., description="Whether to scrape and download images or not")                       
     ):
    scraping_service = ScraperService()
    zip_id, scraped_listing = await scraping_service.scrape_listing_details(url, download_images)
    return {"success": "Listing retrieved", "body": {"data": scraped_listing, "zip_id": zip_id}}

@app.get("/api/zip")
async def zip_dl_handler(zip_id: str = Query(..., description="ZIP File ID")):
    zip_repo = ZipRepository()
    zip_data = await zip_repo.get_zip(zip_id)
    path = zip_data['filename']
    abspath = os.path.abspath(path)
    if not os.path.exists(abspath):
        return {"error": "File doesnt exist"} 
    return FileResponse(abspath, filename=path)

@app.get("/api/ws-auth")
async def ws_auth_handler(user: SelectUser = Depends(validate_user)):
    ws_token = ws_service.generate_session_token(user.email, user.id)
    return {"success": "OK", "body": ws_token}

@app.websocket('/ws/{session_token}')
async def websocket_handler(websocket: WebSocket, session_token: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "connect":
                connect_resp = await ws_service.connect(session_token, websocket)
                if connect_resp.get('success'):
                    await websocket.send_json({"type": "connection", "body": {"success":"Connected"}})
                else:
                    await websocket.send_json( {"type": "connection", "body": {"error":"Failed"}})
                print(connect_resp)
            print(message)
    except WebSocketDisconnect:
        ws_service.disconnect(session_token) 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
