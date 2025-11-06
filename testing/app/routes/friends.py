from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
import os

load_dotenv

router = APIRouter()

# /app/friends
@router.get("/")
async def get_friends(request: Request):
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")  

    # verify the user is logged in
    steam_id = request.session.get("steam_id")
    if not steam_id:
        return RedirectResponse("/")

    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"

    # fetch the data
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200:
            return JSONResponse({"error": "could not fetch friends data"}, status_code=500)

    data = r.json()
    return JSONResponse(data)