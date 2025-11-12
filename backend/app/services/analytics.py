# backend/app/services/analytics.py
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot, DailySummary
from backend.app.services import cache
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import aliased

def compute_daily_summary():
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        today_utc = now_utc.date()
        tomorrow_utc = today_utc + timedelta(days=1)

        # Return existing summary if already exists
        existing_summary = db.query(DailySummary).filter_by(date=today_utc).first()
        if existing_summary:
            return existing_summary

        # Get latest snapshot per game for today
        todays_snapshots = (
            db.query(Snapshot)
            .filter(
                Snapshot.date >= datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc),
                Snapshot.date < datetime.combine(tomorrow_utc, datetime.min.time(), tzinfo=timezone.utc)
            )
            .order_by(Snapshot.appid, Snapshot.date.desc())
            .all()
        )

        if not todays_snapshots:
            return None

        # Pick only latest snapshot per game for today
        latest_today = {}
        for s in todays_snapshots:
            if s.appid not in latest_today:
                latest_today[s.appid] = s

        total_today = 0
        playtime_by_game = {}

        for appid, snap in latest_today.items():
            # latest snapshot **before today** for this game
            prev_snap = (
                db.query(Snapshot)
                .filter(Snapshot.appid == appid, Snapshot.date < datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc))
                .order_by(Snapshot.date.desc())
                .first()
            )
            prev_playtime = prev_snap.playtime_forever if prev_snap else 0
            delta = snap.playtime_forever - prev_playtime
            if delta > 0:
                playtime_by_game[appid] = delta
                total_today += delta

        if not playtime_by_game:
            return None  # nothing new played today

        # Most played game today
        most_played_appid = max(playtime_by_game, key=playtime_by_game.get)
        most_played_minutes = playtime_by_game[most_played_appid]
        most_played_game = db.query(Game).filter_by(appid=most_played_appid).first()

        # Compare with yesterday summary if exists
        yesterday = today_utc - timedelta(days=1)
        prev_summary = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
        prev_total = prev_summary.total_playtime_minutes if prev_summary else 0
        total_change = total_today - prev_total

        summary = DailySummary(
            date=today_utc,
            total_playtime_minutes=total_today,
            total_games_tracked=len(latest_today),
            most_played_appid=most_played_appid,
            most_played_name=most_played_game.name if most_played_game else None,
            most_played_minutes=most_played_minutes,
            average_playtime_per_game=round(total_today / len(latest_today), 2) if latest_today else 0,
            total_playtime_change=total_change
        )

        db.add(summary)
        db.commit()
        db.refresh(summary)

        cache.set_cache("daily-summary-latest", summary, ttl=900)
        return summary

    except Exception as e:
        db.rollback()
        print(f"Error computing daily summary: {e}")
    finally:
        db.close()

def get_latest_summary():
    cache_key = "daily-summary-latest"
    cached = cache.get_cache(cache_key)
    if cached:
        return {"cached": True, "summary": cached}

    db = SessionLocal()
    try:
        return db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    finally:
        db.close()

def get_top_games(period: str, page: int = 1, limit: int = 10):
    cache_key = f"top_games_{period}_{page}_{limit}"
    cached = cache.get_cache(cache_key)
    if cached:
        return {"cached": True, **cached}

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        skip = (page - 1) * limit

        # define period range
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None  # lifetime

        if period in ["week", "month"]:
            S1 = aliased(Snapshot)
            S2 = aliased(Snapshot)

            subq = (
                db.query(
                    S1.appid.label("appid"),
                    (func.max(S2.playtime_forever) - func.min(S1.playtime_forever)).label("delta_playtime")
                )
                .join(S2, S1.appid == S2.appid)
                .filter(S1.date >= start_date)
                .filter(S2.date >= start_date)
                .group_by(S1.appid)
                .subquery()
            )

            total = db.query(subq).count()
            results = (
                db.query(Game.name, subq.c.delta_playtime)
                .join(subq, subq.c.appid == Game.appid)
                .order_by(subq.c.delta_playtime.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

        else:  # lifetime
            subq = (
                db.query(
                    Snapshot.appid,
                    func.max(Snapshot.playtime_forever).label("total_playtime")
                )
                .group_by(Snapshot.appid)
                .subquery()
            )

            total = db.query(subq).count()
            results = (
                db.query(Game.name, subq.c.total_playtime)
                .join(subq, subq.c.appid == Game.appid)
                .order_by(subq.c.total_playtime.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

        top_games = [
            {"name": r[0], "total_playtime": int(r[1] or 0)}
            for r in results if r[1] is not None
        ]

        response = {
            "cached": False,
            "period": period,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "top_games": top_games
        }

        # Cache results for speed
        ttl = 300 if period in ["week", "month"] else 3600
        cache.set_cache(cache_key, response, ttl=ttl)

        return response

    finally:
        db.close()

def get_trends():
    cache_key = "playtime_trends"
    cached = cache.get_cache(cache_key)
    if cached:
        return {"cached": True, "trends": cached}

    db = SessionLocal()
    try:
        now = date.today()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        def total_since(start):
            q = (
                db.query(func.sum(DailySummary.total_playtime_minutes))
                .filter(DailySummary.date >= start)
            )
            return q.scalar() or 0

        this_week = total_since(week_ago)
        last_week = total_since(two_weeks_ago)
        change = 0 if last_week == 0 else ((this_week - last_week) / last_week) * 100

        trends = {
            "this_week": {"total_playtime": this_week},
            "last_week": {"total_playtime": last_week},
            "change_vs_last_week": f"{change:+.1f}%"
        }

        cache.set_cache(cache_key, trends, ttl=1800) # 30 mins cache
        return {"cached": False, "trends": trends}
    finally:
        db.close()
