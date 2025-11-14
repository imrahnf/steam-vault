# backend/app/db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

load_dotenv()
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

if DEMO_MODE:
    print("Using demo SQLite database")
    DATABASE_URL = "sqlite:///./steamvault_demo.db"
else:
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    if all([USER, PASSWORD, HOST, PORT, DBNAME]):
        print("Using Supabase Postgres")
        DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
    else:
        print("Using local SQLite database")
        DATABASE_URL = "sqlite:///./steamvault.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize production DB if not demo
def init_database():
    if not DEMO_MODE:
        Base.metadata.create_all(bind=engine)
