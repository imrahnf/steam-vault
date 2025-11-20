# backend/app/routes/demo/demo_routes.py
from fastapi import APIRouter, HTTPException, Query
from backend.app.db.demo_database import SessionLocal
from backend.app.services import analytics, games
from typing import Optional, List
from datetime import date

'''
This module is simply for showcasing demo data.
This can be deleted.
This uses the steamvault_demo.db file.
'''

demo_router = APIRouter(prefix="/demo")

# create a single demo session (could also create one per request)
demo_session = SessionLocal()

# Demo reference date - the "current date" for demo purposes
DEMO_REFERENCE_DATE = date(2025, 11, 15)

@demo_router.get("/analytics/summary/latest")
async def demo_get_latest_summary():
    summary = analytics.get_latest_summary(session=demo_session)
    if not summary:
        raise HTTPException(status_code=404, detail="No summaries yet.")
    return summary

@demo_router.get("/analytics/top_games")
async def get_top_games(
    period: str = Query("lifetime", enum=["week", "month", "lifetime"]),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
    ):
    result = analytics.get_top_games(period, page, limit, demo_session, reference_date=DEMO_REFERENCE_DATE)
    if not result:
        raise HTTPException(status_code=404, detail="No data for that period.")
    return result

@demo_router.get("/analytics/summary/history")
async def demo_summary_history( start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 90 ):
    summary = analytics.summary_history(start_date, end_date, limit, session=demo_session)
    if not summary:
        raise HTTPException(status_code=404, detail="No data available to compute today's summary.")
    return summary

@demo_router.get("/analytics/trends")
async def get_trends():
    result = analytics.get_trends(demo_session, reference_date=DEMO_REFERENCE_DATE)
    if not result:
        raise HTTPException(status_code=404, detail="Not enough data to show trends")
    return result

@demo_router.get("/analytics/streaks")
async def streaks(appid: Optional[int] = None):
    streak = analytics.get_streaks(appid, demo_session)
    if not streak:
        raise HTTPException(status_code=404, detail="No data available to fetch streak.")
    return streak

@demo_router.get("/analytics/activity/heatmap")
async def activity_heatmap(limit_days: int = 90):
    activity = analytics.activity_heatmap(limit_days, demo_session, reference_date=DEMO_REFERENCE_DATE)
    if not activity:
        raise HTTPException(status_code=404, detail="Not enough data available to see activity.")
    return activity

@demo_router.get("/analytics/games/compare")
async def compare_games( appids: List[int] = Query(...), start_date: Optional[date] = None, end_date: Optional[date] = None):
    comparison = analytics.compare_games(appids, start_date, end_date, demo_session, reference_date=DEMO_REFERENCE_DATE)
    if not comparison:
        raise HTTPException(status_code=404, detail="Could not compare games.")
    return comparison

@demo_router.get("/games/search")
async def search(q: str = Query(..., min_length=1)):
    return games.search_games(q, demo_session)

@demo_router.get("/games/{appid}")
async def game_details(appid: int, days: int = 30):
    details = games.game_details(appid, days, demo_session)
    if "error" in details:
        raise HTTPException(status_code=404, detail="Game not found")
    return details