# /backend/app/services/steam_api.py
from dotenv import load_dotenv
import httpx, os
from datetime import datetime
from fastapi import HTTPException

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")

async def get_owned_games():
    if not STEAM_API_KEY or not STEAM_ID:
        raise ValueError("Missing STEAM_API_KEY or STEAM_ID")

    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": STEAM_ID,
        "include_appinfo": "true",
        "include_played_free_games": "true",
        "format": "json"
    }

    try:
        # get data from Steam API
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"SteamAPI Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"SteamAPI Error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected problem occured: {e}")

    # TODO: validate the structure matches what was expected

    return data

async def process_owned_games(raw_response: dict):
    # extract correct data
    games = raw_response.get("response", {}).get("games", [])
    processed = []

    for game in games:
        processed.append({
            "appid": game["appid"],
            "name": game.get("name"), # may not always be present
            "playtime_minutes": game.get("playtime_forever", 0), # minutes
            "icon_url": (
                f"https://media.steampowered.com/steamcommunity/public/images/apps/{game["appid"]}/{game.get("img_icon_url", "")}.jpg"
                if game.get("img_icon_url") else None
            ),
            "last_played": ( # orginally posix
                datetime.fromtimestamp(game["rtime_last_played"]).isoformat()
                if game.get("rtime_last_played") else None
            )
        })

    return {"game_count": len(processed), "games": processed}