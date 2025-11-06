from dotenv import load_dotenv
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware # session middleware

from app.auth import steam_login
from app.routes import friends

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

app = FastAPI()

# add SessionMiddleware (random_string)
app.add_middleware(
    SessionMiddleware,
    secret_key="1234567890",  # TODO: GENERATE RANDOM STRING
    session_cookie="steamvault_session",
    max_age= 3 * 60 * 60 * 24  # cookie lifespan in seconds (3 days)
)

# static/templates folder
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

# routing for the login & authentication endpoints
app.include_router(steam_login.router, prefix="/auth", tags=["auth"])
app.include_router(friends.router, prefix="/app/friends", tags=["friends"])

# home endpoint
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    steam_id = request.session.get("steam_id")

    # could not retrieve key from log in, redirect user
    if steam_id:
        return RedirectResponse("/dashboard")
    else:
        return templates.TemplateResponse("index.html", {"request": request})

# hande errors with its own endpoint
@app.get("/error", response_class=HTMLResponse)
async def error_page(request: Request, message: str | None = "Something went wrong, please try again."):
    return templates.TemplateResponse("error.html", {"request": request, "message": message})

# logged in user's dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    steam_id = request.session.get("steam_id")

    # could not retrieve key from log in, redirect user
    if not steam_id:
        return RedirectResponse("/")

    return templates.TemplateResponse("dashboard.html", {"request": request, "steam_id": steam_id})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")