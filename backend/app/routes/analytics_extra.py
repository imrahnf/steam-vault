from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.db.database import SessionLocal
from backend.app.db.models import DailySummary, Game, Snapshot
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func

router = APIRouter()

# ------------------------
# 1. Daily summaries history
# ------------------------
@router.get("/summary/history")
def summary_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 90
):
    db = SessionLocal()
    try:
        query = db.query(DailySummary).order_by(DailySummary.date.desc())
        if start_date:
            query = query.filter(DailySummary.date >= start_date)
        if end_date:
            query = query.filter(DailySummary.date <= end_date)
        summaries = query.limit(limit).all()
        return [s.__dict__ for s in reversed(summaries)]
    finally:
        db.close()

# ------------------------
# 2. Streaks
# ------------------------
@router.get("/streaks")
def get_streaks(appid: Optional[int] = None):
    db = SessionLocal()
    try:
        # Get all daily summaries ordered by date
        summaries = db.query(DailySummary).order_by(DailySummary.date).all()
        longest_streak = 0
        current_streak = 0
        temp_streak = 0

        for s in summaries:
            # if appid is provided, check playtime delta for that game
            played = True
            if appid:
                # find snapshot for that day
                snap = (
                    db.query(Snapshot)
                    .filter(Snapshot.appid == appid)
                    .filter(Snapshot.date >= datetime.combine(s.date, datetime.min.time(), tzinfo=timezone.utc))
                    .filter(Snapshot.date < datetime.combine(s.date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
                    .order_by(Snapshot.date.desc())
                    .first()
                )
                played = snap.playtime_forever > 0 if snap else False
            else:
                # overall streak, any game played today?
                played = s.total_playtime_minutes > 0

            if played:
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
            else:
                temp_streak = 0

        current_streak = temp_streak
        return {"longest_streak": longest_streak, "current_streak": current_streak}
    finally:
        db.close()

# ------------------------
# 3. Activity heatmap
# ------------------------
@router.get("/activity/heatmap")
def activity_heatmap(limit_days: int = 90):
    db = SessionLocal()
    today = date.today()
    start_date = today - timedelta(days=limit_days)
    try:
        # get summaries
        summaries = (
            db.query(DailySummary)
            .filter(DailySummary.date >= start_date)
            .order_by(DailySummary.date)
            .all()
        )
        heatmap = [
            {
                "date": s.date.isoformat(),
                "total_playtime": s.total_playtime_minutes,
                "games_played": s.total_games_tracked
            }
            for s in summaries
        ]
        return heatmap
    finally:
        db.close()

# ------------------------
# 4. Compare multiple games (date-aligned)
# ------------------------
@router.get("/games/compare")
def compare_games(
    appids: List[int] = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    db = SessionLocal()
    try:
        # Determine full date range
        if not start_date:
            # default to 90 days ago
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        all_dates = [
            start_date + timedelta(days=i)
            for i in range((end_date - start_date).days + 1)
        ]

        result = {}
        for appid in appids:
            # fetch snapshots for this game within the range
            snaps = (
                db.query(Snapshot)
                .filter(Snapshot.appid == appid)
                .filter(Snapshot.date >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc))
                .filter(Snapshot.date < datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
                .order_by(Snapshot.date)
                .all()
            )

            # map date -> playtime
            snap_map = {}
            for snap in snaps:
                snap_map[snap.date.date()] = snap.playtime_forever

            daily_data = []
            last_playtime = 0
            for d in all_dates:
                current_playtime = snap_map.get(d, last_playtime)
                delta = max(current_playtime - last_playtime, 0)
                daily_data.append({
                    "date": d.isoformat(),
                    "playtime_forever": current_playtime,
                    "daily_delta": delta
                })
                last_playtime = current_playtime

            result[appid] = daily_data

        return result
    finally:
        db.close()
