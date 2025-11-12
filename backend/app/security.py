# /backend/app/security.py
from dotenv import load_dotenv
import os
from fastapi import Header, HTTPException

load_dotenv()

CRON_SECRET = os.getenv("CRON_SECRET")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# simple logic to verify authorized users calling internal endpoints
async def verify_admin_token(x_token: str = Header(None)):
    if x_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access - invalid admin token")
    

async def verify_cron_token(x_token: str = Header(None)):
    if x_token != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized access - invalid cron token")
