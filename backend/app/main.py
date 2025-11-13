# /backend/app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from backend.app.routes import fetch, analytics
from backend.app.db.database import init_database

from backend.app.security import verify_cron_token

load_dotenv()

app = FastAPI(title="SteamVault", docs_url=None, redoc_url=None, openapi_url=None)

# Initialize db
init_database()

# Setup routers
app.include_router(fetch.router, prefix="/fetch", tags=["fetch"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

@app.get("/")
async def main():
    return {"message" : "SteamVault API running."}

# keep Render app alive
@app.post("/cron/ping", dependencies=[Depends(verify_cron_token)])
async def cron_ping():    
    print("pinged the /cron/ping endpoint [POST]")
    return {"status": "ok", "ran": "cron/ping"}

@app.on_event("startup")
async def run_fetch():
    from backend.app.routes.fetch import get_steam_games
    await get_steam_games()