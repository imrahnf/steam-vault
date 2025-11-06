# /backend/app/main.py
from dotenv import load_dotenv
from fastapi import FastAPI
from backend.app.routes import fetch, analytics, admin
from backend.app.db.database import init_database

load_dotenv()

app = FastAPI(title="SteamVault")

# Initialize db
init_database()

# Setup routers
app.include_router(fetch.router, prefix="/fetch", tags=["fetch"])
#app.include_router(analytics.router, prefix="/api", tags=["analytics"])
#app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
async def main():
    return {"message" : "SteamVault API running."}