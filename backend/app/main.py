from fastapi import FastAPI
from app.auth import steam_login

app = FastAPI()

@app.get("/")
def root():
    return {"message": "SteamVault backend running"}

# routes
app.include_router(steam_login.router, prefix="/auth", tags=["auth"])
