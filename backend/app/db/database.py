# /backend/app/db/database.py
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fetch database variables
if not DATABASE_URL:
    print("Using Supabase URL")
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
else:
    print("Using SQLite database")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create tables for dev if missing
def init_database():
    Base.metadata.create_all(bind=engine)
