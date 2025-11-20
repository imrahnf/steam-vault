# backend/app/services/analytics.py
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot, DailySummary
from backend.app.services import cache
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import aliased
from typing import List, Optional

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

def get_latest_summary(session=None):
    db = session or SessionLocal() # fallback to main db
    close_after = False
    if session is None:
        close_after = True # only close if we created it ourselves
    
    # check cache, use different cache key for demo
    prefix = "demo-" if session else ""
    cache_key = f"{prefix}daily-summary-latest"

    cached = cache.get_cache(cache_key)
    if cached:
        return {"cached": True, "summary": cached}

    try:
        return db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    finally:
        if close_after:
            db.close()

def get_top_games(period: str, page: int = 1, limit: int = 10, session=None, reference_date=None):
    db = session or SessionLocal()
    close_after = False
    if session is None:
        close_after = True

    prefix = "demo-" if session else ""
    cache_key = f"{prefix}top_games_{period}_{page}_{limit}"
    
    cached = cache.get_cache(cache_key)
    print(f"Cache hit for {cache_key}: {bool(cached)}")
    if cached:
        return {"cached": True, **cached}

    try:
        # Use reference_date for demo mode, otherwise current time
        if reference_date:
            now = datetime.combine(reference_date, datetime.min.time(), tzinfo=timezone.utc)
        else:
            now = datetime.now(timezone.utc)
        skip = (page - 1) * limit

        # Determine start date based on period
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # lifetime
            start_date = None

        if start_date:
            # Get delta playtime in the period
            subq = (
                db.query(
                    Snapshot.appid,
                    (func.max(Snapshot.playtime_forever) - func.min(Snapshot.playtime_forever)).label("delta_playtime")
                )
                .filter(Snapshot.date >= start_date)
                .group_by(Snapshot.appid)
                .subquery()
            )

            total = db.query(subq).count()
            results = (
                db.query(Game.appid, Game.name, Game.img_icon_url, subq.c.delta_playtime)
                .join(subq, subq.c.appid == Game.appid)
                .order_by(subq.c.delta_playtime.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            # Lifetime: total playtime for each game
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
                db.query(Game.appid, Game.name, Game.img_icon_url, subq.c.total_playtime)
                .join(subq, subq.c.appid == Game.appid)
                .order_by(subq.c.total_playtime.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

        # Format results - filter out games with zero playtime
        top_games = [
            {"appid": r[0], "name": r[1], "img_icon_url": r[2], "total_playtime": int(r[3] or 0)}
            for r in results
            if r[3] and int(r[3]) > 0
        ]

        response = {
            "period": period,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "top_games": top_games
        }

        # Cache results
        ttl = 10 if period in ["week", "month"] else 3600
        cache.set_cache(cache_key, response, ttl=ttl)

        return {"cached": False, **response}
    finally:
        if close_after:
            db.close()

def get_trends(session=None, reference_date=None):
    db = session or SessionLocal()
    close_after = False
    if session is None:
        close_after = True

    prefix = "demo-" if session else ""
    cache_key = f"{prefix}playtime_trends"

    cached = cache.get_cache(cache_key)
    if cached:
        return {"cached": True, "trends": cached}

    try:
        # Use reference_date for demo mode
        now = reference_date if reference_date else date.today()
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
        if close_after:
            db.close()

def summary_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 90,
    session=None
    ):
    db = session or SessionLocal() # fallback to main db
    close_after = False
    if session is None:
        close_after = True # only close if we created it ourselves
    
    try:
        query = db.query(DailySummary).order_by(DailySummary.date.desc())
        if start_date:
            query = query.filter(DailySummary.date >= start_date)
        if end_date:
            query = query.filter(DailySummary.date <= end_date)
        summaries = query.limit(limit).all()

        # Convert summaries to dictionaries
        return [{
            'id': s.id,  # Add id
            'new_games_count': s.new_games_count,  # Add new_games_count
            'average_playtime_per_game': s.average_playtime_per_game,
            'most_played_appid': s.most_played_appid,
            'most_played_minutes': s.most_played_minutes,
            'date': s.date.isoformat(),  # Ensure date is formatted as a string
            'total_playtime_minutes': s.total_playtime_minutes,
            'total_games_tracked': s.total_games_tracked,
            'total_playtime_change': s.total_playtime_change,
            'most_played_name': s.most_played_name
        } for s in reversed(summaries)]
    finally:
        if close_after:
            db.close()

def get_streaks(appid: Optional[int] = None, session=None):
    db = session or SessionLocal()
    close_after = False
    if session is None:
        close_after = True

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
        if close_after:
            db.close()

def compare_games(appids: List[int], start_date: Optional[date] = None, end_date: Optional[date] = None, session=None, reference_date=None):
    db = session or SessionLocal()
    close_after = False
    if session is None:
        close_after = True

    try:
        # Use reference_date for demo mode
        today = reference_date if reference_date else date.today()
        
        # Determine full date range
        if not start_date:
            # default to 90 days ago
            start_date = today - timedelta(days=90)
        if not end_date:
            end_date = today

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
        if close_after:
            db.close()

def activity_heatmap(limit_days: int = 90, session=None, reference_date=None):
    db = session or SessionLocal()
    close_after = False
    if session is None:
        close_after = True
    
    # Use reference_date for demo mode
    today = reference_date if reference_date else date.today()
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
        if close_after:
            db.close()