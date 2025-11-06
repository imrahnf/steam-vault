# /backend/app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Game(Base):
    __tablename__ = "games"
    
    # attributes
    id = Column(Integer, primary_key=True, index=True)
    appid = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    img_icon_url = Column(String, nullable=True)

    # allow Game.snapshot to return list of snapshots for the game
    snapshots = relationship("Snapshot", back_populates="game", cascade="all, delete-orphan")

class Snapshot(Base):
    __tablename__ = "snapshots"

    # attributes
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    appid = Column(Integer, ForeignKey("games.appid"), nullable=False, index=True)
    playtime_forever = Column(Integer, nullable=False) # minutes
    last_played = Column(DateTime, nullable=True)

    # allow snapshot.game to return to Game obj
    game = relationship("Game", back_populates="snapshots")

