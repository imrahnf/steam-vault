# /backend/app/services/db_sync.py
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot, DailySummary
from backend.app.services import cache
from datetime import datetime, date, timezone
from sqlalchemy import func

def save_game_to_db(game_list: list):
    '''
    Insert or update game rows and add snapshots
    Only one snapshot per game per day
    '''
    db = SessionLocal()
    try:
        today = date.today()

        for g in game_list:
            appid = g["appid"]

            # check if game exists
            game = db.query(Game).filter_by(appid=appid).first()

            if not game:
                game = Game(
                    appid=appid,
                    name=g.get("name") or "Unknown",
                    img_icon_url=g.get("img_icon_url")
                )
                db.add(game)
                db.flush()
            else:
                updated = False
                if g.get("name") and game.name != g.get("name"):
                    game.name = g.get("name")
                    updated = True
                if g.get("icon_url") and game.img_icon_url != g.get("icon_url"):
                    game.img_icon_url = g.get("icon_url")
                    updated = True
                if updated:
                    db.add(game)

            # parse last_played
            last_played_dt = None
            if g.get("last_played"):
                try:
                    last_played_dt = datetime.fromisoformat(g.get("last_played"))
                except Exception:
                    last_played_dt = None

            # check if a snapshot for today exists
            existing_snapshot = db.query(Snapshot).filter(
                Snapshot.appid == appid,
                func.date(Snapshot.date) == today
            ).first()
            now_utc = datetime.now(timezone.utc)
            playtime_now = int(g.get("playtime_minutes", 0))

            if existing_snapshot:
                # Only update if playtime changed
                if existing_snapshot.playtime_forever != playtime_now:
                    existing_snapshot.playtime_forever = playtime_now
                    existing_snapshot.last_played = last_played_dt
                    existing_snapshot.date = now_utc
                    db.add(existing_snapshot)
            else:
                snapshot = Snapshot(
                    appid=appid,
                    playtime_forever=playtime_now,
                    last_played=last_played_dt,
                    date=now_utc
                )
                db.add(snapshot)


        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        cache.delete_cache("daily-summary-latest")
        cache.delete_cache("top_games_week")
        cache.delete_cache("top_games_month")
        cache.delete_cache("top_games_lifetime")
        cache.delete_cache("playtime_trends")

        db.close()
