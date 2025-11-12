# /backend/app/routes/fetch.py
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends

import asyncio

from backend.app.services import steam_api, db_sync
from backend.app.security import verify_admin_token
from backend.app.services import cache

load_dotenv()

router = APIRouter()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

"""
Fetch user's owned games and data
Returns JSON list of games with appid, name, and playtime.
"""
@router.get("/", dependencies=[Depends(verify_admin_token)])
async def get_steam_games():
    # fetch raw data response
    raw_data = await steam_api.get_owned_games()

    # process
    processed_data = await steam_api.process_owned_games(raw_data)

    # save to db
    try:
        # sqlalchemy blocks the thread
        await asyncio.to_thread(db_sync.save_game_to_db, processed_data["games"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to save snapshot: {e}")

    print(processed_data["games"][0])

    return processed_data

@router.get("/profile", dependencies=[Depends(verify_admin_token)])
async def get_proflie():
    # fetch cached data
    cached = cache.get_cache("steam-profile")
    
    if cached:
        return {"cached": True, "profile":cached}
    
    try:
        profile_data = await steam_api.get_player_summary(STEAM_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile {e}")

    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    cache.set_cache("steam-profile", profile_data, 7200) # 2 hr cache

    return {"cached": False, "profile":profile_data}