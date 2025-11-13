# /backend/app/routes/games.py
from fastapi import APIRouter, Query, HTTPException
from typing import List
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot
from backend.app.services import games
from datetime import datetime, timedelta, timezone

router = APIRouter()

# ------------------------
# 1. Search games by name
# ------------------------
@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    return games.search_games(q)

# ------------------------
# 2. Game details + history preview
# ------------------------
@router.get("/{appid}")
async def game_details(appid: int, days: int = 30):
    details = games.game_details(appid, days)
    if "error" in details:
        raise HTTPException(status_code=404, detail="Game not found")
    return details