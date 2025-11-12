# /backend/app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.services import analytics
from backend.app.services.analytics import compute_daily_summary, get_top_games, get_trends, get_latest_summary
from backend.app.db.database import SessionLocal
from backend.app.db.models import DailySummary
from backend.app.security import verify_admin_token
from backend.app.services import cache

router = APIRouter()

@router.post("/summary/generate", dependencies=[Depends(verify_admin_token)])
async def generate_summary():
    summary = compute_daily_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No data for today or not enough data to compute.")
    return {"message": "Created summary", "summary":summary.__dict__}

@router.get("/summary/latest")
async def get_latest_summary():
    summary = analytics.get_latest_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No summaries yet.")
    return summary


@router.get("/top_games")
async def get_top_games(
    period: str = Query("lifetime", enum=["week", "month", "lifetime"]),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
    ):
    result = analytics.get_top_games(period, page, limit)
    if not result:
        raise HTTPException(status_code=404, detail="No data for that period.")
    return result

@router.get("/trends")
async def get_trends():
    result = analytics.get_trends()
    if not result:
        raise HTTPException(status_code=404, detail="Not enough data to show trends")
    return result