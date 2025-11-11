# /backend/app/db/database.py
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./steamvault.db")

# required for sqlite when using with multiple threads
if DATABASE_URL.startswith("sqlite"):
    connection_args = {"check_same_thread": False} # for sqlite only

# setup db connection 
engine = create_engine(DATABASE_URL, connect_args=connection_args, echo=False)

# short db transaction env
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create tables for dev if missing
def init_database():
    Base.metadata.create_all(bind=engine)