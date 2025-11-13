# /backend/app/db/database.py
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Fetch database variables
if all([USER, PASSWORD, HOST, PORT, DBNAME]):
    print("Using Supabase Postgres")
    # Construct the SQLAlchemy connection string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
else:
    print("Using local SQLite database")
    DATABASE_URL = "sqlite:///./steamvault.db"

# Uncomment for data showcasing or testing:
# DATABASE_URL = "sqlite:///./steamvault.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create tables for dev if missing
def init_database():
    Base.metadata.create_all(bind=engine)
