# backend/app/services/analytics.py
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot, DailySummary
from datetime import date, timedelta, datetime

def compute_daily_summary():
    db = SessionLocal()

    try:
        today = date.today()

        # first check if there's a record for today and return it if it exists
        existing_summary = db.query(DailySummary).filter_by(date=today).first()
        if existing_summary:
            print("There is already a summary for today")
            return existing_summary
        

        # get all the snapshots for today
        todays_snapshots = db.query(Snapshot).filter(
            Snapshot.date >= datetime.combine(today, datetime.min.time())).all()
        
        if not todays_snapshots:
            print("No snapshots to return")
            return None

        # compute total time & num of games for today
        total_playtime = sum(s.playtime_forever for s in todays_snapshots)
        total_games = len({s.appid for s in todays_snapshots})

        # most played game
        playtime_by_game = {}
        for s in todays_snapshots:
            playtime_by_game[s.appid] = playtime_by_game.get(s.appid, 0) + s.playtime_forever

        most_played_appid = max(playtime_by_game, key=playtime_by_game.get)
        most_played_mins = playtime_by_game[most_played_appid]
        most_played_game = db.query(Game).filter_by(appid=most_played_appid).first()

        # make comparison from yesretedya
        yesterday = today - timedelta(days=1)
        prev_summary = db.query(DailySummary).filter_by(date=yesterday).first()
        prev_playtime = prev_summary.total_playtime_minutes if prev_summary else 0

        summary = DailySummary(
            date=today,
            total_playtime_minutes=total_playtime,
            total_games_tracked=total_games,
            most_played_appid=most_played_appid,
            most_played_name=most_played_game.name if most_played_game else None,
            most_played_minutes=most_played_mins,
            average_playtime_per_game=round(total_playtime / total_games, 2) if total_games else 0,
            total_playtime_change=total_playtime-prev_playtime
        )

        db.add(summary)
        db.commit()
        db.refresh(summary)

    except Exception as e:
        db.rollback()
        print(f"excepting: {e}")
    finally:
        db.close()