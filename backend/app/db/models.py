# /backend/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone, date

Base = declarative_base()

# game table holding essential game info
class Game(Base):
    __tablename__ = "games"
    
    # attributes
    id = Column(Integer, primary_key=True, index=True)
    appid = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    img_icon_url = Column(String, nullable=True)

    # allow Game.snapshot to return list of snapshots for the game
    snapshots = relationship("Snapshot", back_populates="game", cascade="all, delete-orphan")

# a single snapshot showcasing current steam data at any given moment
class Snapshot(Base):
    __tablename__ = "snapshots"

    # attributes
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    appid = Column(Integer, ForeignKey("games.appid"), nullable=False, index=True)
    playtime_forever = Column(Integer, nullable=False) # minutes
    last_played = Column(DateTime, nullable=True)

    # allow snapshot.game to return to Game obj
    game = relationship("Game", back_populates="snapshots")

# computed daily summaries stored to preserve historical data
class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=date.today, nullable=False, unique=True, index=True)

    # basic data
    total_playtime_minutes = Column(Integer, default=0)
    new_games_count = Column(Integer, default=0)
    total_games_tracked = Column(Integer, default=0)

    average_playtime_per_game = Column(Float, default=0.0)
    total_playtime_change = Column(Integer, default=0)  # diff vs yesterday

    # top game
    most_played_appid = Column(Integer, ForeignKey("games.appid"), nullable=True)
    most_played_name = Column(String, nullable=True)
    most_played_minutes = Column(Integer, default=0)

    # just to easily reference the highest played game
    most_played_game = relationship("Game")