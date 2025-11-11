# /backend/app/services/db_sync.py
from backend.app.db.database import SessionLocal
from backend.app.db.models import Game, Snapshot, DailySummary
from datetime import datetime

def save_game_to_db(game_list: list):
    '''
    Insert or update game rows and add snapshots
    '''

    db = SessionLocal()
    try:
        # loop through list
        for g in game_list:
            appid = g["appid"]

            # check if row exists
            game = db.query(Game).filter_by(appid=appid).first() 

            # handle game not found
            if not game:
                # insert into the table
                game = Game(appid=appid, name=g.get("name") or "Unknown", img_icon_url=g.get("img_icon_url"))
                db.add(game)
                db.flush()
            else:
                # update the fields since it exists
                updated = False # add if there were changes made

                # update game name
                if g.get("name") and (game.name != g.get("name")):
                    game.name = g.get("name")
                    updated = True
                # update icon
                if g.get("icon_url") and (game.img_icon_url != g.get("icon_url")):
                    game.img_icon_url = g.get("icon_url")
                if updated:
                    db.add(game)
                
            
            # create a snapshot
            last_played_dt = None
            if g.get("last_played"):
                try:
                    last_played_dt = datetime.fromisoformat(g.get("last_played"))
                except Exception:
                    last_played_dt = None

            snapshot = Snapshot(
                appid=appid,
                playtime_forever=int(g.get("playtime_minutes", 0)),
                last_played=last_played_dt
            )

            db.add(snapshot)
        
        db.commit() # commit changes

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()