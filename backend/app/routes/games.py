from fastapi import APIRouter, Query
from typing import List
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot
from datetime import datetime, timedelta, timezone

router = APIRouter()

# ------------------------
# 1. Search games by name
# ------------------------
@router.get("/search")
def search_games(q: str):
    db = SessionLocal()
    try:
        games = db.query(Game).filter(Game.name.ilike(f"%{q}%")).all()
        return [{"appid": g.appid, "name": g.name, "img_icon_url": g.img_icon_url} for g in games]
    finally:
        db.close()

# ------------------------
# 2. Game details + history preview
# ------------------------
@router.get("/{appid}")
def game_details(appid: int, days: int = 30):
    db = SessionLocal()
    try:
        game = db.query(Game).filter_by(appid=appid).first()
        if not game:
            return {"error": "Game not found"}

        # last `days` snapshots
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        snapshots = (
            db.query(Snapshot)
            .filter(Snapshot.appid == appid, Snapshot.date >= cutoff)
            .order_by(Snapshot.date)
            .all()
        )
        return {
            "appid": game.appid,
            "name": game.name,
            "img_icon_url": game.img_icon_url,
            "history": [{"date": s.date.isoformat(), "playtime_forever": s.playtime_forever} for s in snapshots]
        }
    finally:
        db.close()
