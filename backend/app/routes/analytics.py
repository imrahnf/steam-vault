# /backend/app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from backend.app.services.analytics import compute_daily_summary
from backend.app.db.database import SessionLocal
from backend.app.db.models import DailySummary
from backend.app.security import verify_admin_token

router = APIRouter()

@router.post("/summary/generate", dependencies=[Depends(verify_admin_token)])
async def generate_summary():
    summary = compute_daily_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No data for today or not enough data to compute.")
    return {"message": "Created summary", "summary":summary.__dict__}

@router.get("/summary/latest")
async def get_latest_summary():
    db = SessionLocal()
    try:
        summary = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
        if not summary:
            raise HTTPException(status_code=404, detail="No summaries yet.")
        return summary.__dict__
    finally:
        db.close()