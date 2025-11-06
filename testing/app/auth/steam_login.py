from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import urllib.parse

router = APIRouter()

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
FRONTEND_URL = "http://localhost:8000" # backend serves frontend work

@router.get("/login")
def login():
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"{FRONTEND_URL}/auth/verify", # after verification, send to /verify
        "openid.realm": FRONTEND_URL,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    # build OpenID query and redirect user to steam login page for authentication
    query = urllib.parse.urlencode(params)
    redirect_url = f"{STEAM_OPENID_URL}?{query}"
    return RedirectResponse(redirect_url)

@router.get("/verify")
async def verify(request: Request):
    params = dict(request.query_params)
    
    # the claimed id is in the "openid.claimed_id" param returned
    # "openid.claimed_id":"https://steamcommunity.com/openid/id/[ID]"
    claimed_id = params.get("openid.claimed_id")
    if not claimed_id:
        return RedirectResponse("/?error=steam_id_not_found")
    
    # split the string and extract the [ID]
    steam_id = claimed_id.split('/')[-1]
    
    # store id in session
    request.session["steam_id"] = steam_id

    return RedirectResponse(f"/dashboard")
    