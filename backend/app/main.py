# /backend/app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import fetch, analytics, games
from backend.app.db.database import init_database
from backend.app.security import verify_cron_token

# DELETE THIS, demo purposes only
from backend.app.routes.demo.demo_routes import demo_router 

load_dotenv()
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
SHOW_DEMO_DOCS = os.getenv("SHOW_DEMO_DOCS", "0") == "1"

# Docs visibility logic
if DEMO_MODE or SHOW_DEMO_DOCS:
    # Enable docs
    app = FastAPI(title="SteamVault")
else:
    # Disable all docs
    app = FastAPI(title="SteamVault",docs_url=None,redoc_url=None,openapi_url=None)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://imrahnf.github.io",
        "https://www.omrahnfaqiri.com",
        "https://steamvault.omrahnfaqiri.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize db
init_database()

@app.get("/")
async def main():
    return {"message" : "SteamVault API running."}

# keep Render app alive
@app.post("/cron/ping", dependencies=[Depends(verify_cron_token)])
async def cron_ping():    
    print("pinged the /cron/ping endpoint [POST]")
    return {"status": "ok", "ran": "cron/ping"}

# Startup event
@app.on_event("startup")
async def run_fetch():
    # Include demo routes if demo mode OR demo docs is active
    if DEMO_MODE or SHOW_DEMO_DOCS:
        app.include_router(demo_router, tags=["demo"])
        print("[DEMO ROUTES ENABLED]")

    # Production (real) routes only when not demo mode
    if not DEMO_MODE:
        app.include_router(fetch.router, prefix="/fetch", tags=["fetch"], include_in_schema=False)
        app.include_router(analytics.router, prefix="/analytics", tags=["analytics"], include_in_schema=False)
        app.include_router(games.router, prefix="/games", tags=["games"], include_in_schema=False)
        from backend.app.routes.fetch import get_steam_games
        await get_steam_games()
