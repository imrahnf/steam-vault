# SteamVault
![Python 3.12.7](https://img.shields.io/badge/Python-3.12.7-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg?logo=fastapi)![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render)
> **SteamVault** is a personal playtime tracker for Steam. It **automatically** collects your game data, **tracks** daily playtime, and **generates analytics** so you can see your gaming habits, trends, and favorite games over time.

### Motivation
Steam keeps track of playtime for each game, but it doesn’t make **historical data** easily accessible or provide meaningful analytics over time. I created SteamVault to **visualize gaming habits**, track **long-term trends**, and answer questions like *"which game do I spend most time on?"* or *"how did playtime change from last week?"*. It also helps identify underplayed games, see growth in gaming sessions, and spot patterns over months or even years.

---

### Key Features
- Fetch your Steam library and daily playtime automatically.
- Generate daily summaries and trends for all your games.
- See top games, average playtime, and changes in your gaming patterns.
- Lightweight and modular, works with Supabase/PostgreSQL, and deployable anywhere.

> The project is designed to be modular: while the recommended free setup uses **Supabase PostgreSQL (IPv4 session pooler)** and **Render** for hosting, it can be easily adapted to other Postgres databases or deployment platforms. This is just a general reference setup and the app can be configured to work with any PostgreSQL-compatible database or hosting platform.

---

## Tech Stack
- **Backend:** FastAPI, Python 3.12.7, Gunicorn + Uvicorn
- **Database:** Supabase PostgreSQL (IPv4 Session Pooler, SSL enforced)
- **Cloud & CI/CD:** Render (auto-deploy from GitHub main branch)
- **Scheduler:** Google Cloud Scheduler (cron jobs)
- **Frontend:** Not yet implemented, fully decoupled from backend

> This app also includes a lightweight in-memory caching layer to reduce redundant API calls and improve response speed. See [cache.py](backend/app/services/cache.py) for more info.

---
## Project Structure
```
steam-vault/
├── backend/
│   ├── app/
│   │   ├── routes/              # API endpoints
│   │   ├── db/                  # Database setup
│   │   ├── services/            # Logic (Steam fetch, analytics, cache)
│   │   └── main.py              # FastAPI entrypoint
│   │   └── security.py          # Authorize internal endpoint calls
├── requirements.txt
└── README.md
└── steamvault.db                # OPTIONAL
```

---

## Database schema
### games
| Column       | Type     | Description    |
| ------------ | -------- | -------------- |
| id           | int (PK) | Auto ID        |
| appid        | int      | Steam App ID   |
| name         | text     | Game name      |
| img_icon_url | text     | Game image URL |

### snapshots
| Column           | Type     | Description              |
| ---------------- | -------- | ------------------------ |
| id               | int (PK) | Auto ID                  |
| date             | datetime | When snapshot was taken  |
| appid            | int (FK) | Linked to `games.appid`  |
| playtime_forever | int      | Total playtime (minutes) |
| last_played      | datetime | Last played timestamp    |

### daily_summaries
| Column                    | Type     | Description                     |
| ------------------------- | -------- | ------------------------------- |
| id                        | int (PK) | Auto ID                         |
| date                      | date     | Summary date                    |
| total_playtime_minutes    | int      | Total playtime across all games |
| new_games_count           | int      | Number of newly tracked games   |
| total_games_tracked       | int      | Total games being tracked       |
| average_playtime_per_game | float    | Average playtime per game       |
| total_playtime_change     | int      | Difference vs previous day      |
| most_played_appid         | int      | App ID of the most played game  |
| most_played_name          | text     | Name of the most played game    |
| most_played_minutes       | int      | Minutes played of the top game  |

---

## API Endpoints
| Endpoint                      | Method | Description                                                          |
| ----------------------------- | ------ | -------------------------------------------------------------------- |
| `/fetch/`                     | GET    | Fetch owned games from Steam and update snapshots (`.env` protected) |
| `/fetch/profile/`             | GET    | Get Steam profile info (cached)                                      |
| `/analytics/summary/generate/`| POST   | Compute daily summary (`.env` protected)                             |
| `/analytics/summary/latest/`  | GET    | Get the most recent daily summary                                    |
| `/analytics/top_games/`       | GET    | Get top games over week, month, or lifetime                          |
| `/analytics/trends/`          | GET    | Get playtime trends over the last two weeks                          |
| `/`                           | GET    | Default route to check API status                                    |
| `/cron/ping/`                 | POST   | Keep Render app alive (used by cron)                                 |

## API Usage
### Admin Protected Routes
These endpoints require `x-token` in the request header with the value of `ADMIN_TOKEN` from `.env`:
- `/fetch/` – fetch your Steam library and snapshots
- `/analytics/summary/generate/` – compute daily summary
**Example:**
```
curl -X POST "https://<app-url>.com/analytics/summary/generate" -H "x-token: <YOUR_ADMIN_TOKEN>"
```

### Cron Protected Routes
Used for scheduled tasks like keeping the Render app alive:
- `/cron/ping/` – keep Render app alive

**Example:**
```
curl -X POST "https://<app-url>.com/cron/ping" -H "x-token: YOUR_CRON_SECRET"
```
### Public Endpoints
No authentication needed:
- `/fetch/profile/` – get cached Steam profile info
- `/analytics/summary/latest/` – get the latest summary
- `/analytics/top_games/` – top games over week/month/lifetime
- `/analytics/trends/` – playtime trends

**Example:**
```
curl "https://<app-url>.com/analytics/summary/latest"
```
##### Example API Response:`/analytics/summary/latest/`
```json
{
  "new_games_count": 0,
  "id": 1,
  "average_playtime_per_game": 824.28,
  "most_played_appid": 359550,
  "most_played_minutes": 12177,
  "total_playtime_minutes": 100562,
  "date": "2025-11-13",
  "total_games_tracked": 122,
  "total_playtime_change": 100562,
  "most_played_name": "Tom Clancy's Rainbow Six® Siege X"
}
```

---

## Installation & Deployment
### Local Development
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app locally (with hot reload)
uvicorn backend.app.main:app --reload
```

### Environment Variables
Set these in `.env` for **local testing** or in Render's dashboard for **production**:
```
STEAM_API_KEY=XXXXXXXXXX       # Steam developer API key
STEAM_ID=XXXXXXXXXX            # Your Steam user ID
ADMIN_TOKEN=XXXXXXXXXX         # Admin token (custom/random) for protected routes

# Supabase IPv4 Session Pooler database variables (these will be provided in Supabase)
user=XXXXXXXXXX
password=XXXXXXXXXX
host=XXXXXXXXXX
port=XXXX
dbname=postgres
# Make sure SSL is enabled in Supabase settings: Database → Settings → SSL Configuration → Enforce SSL on incoming connections
```

If preferred, you can define a full database url with:
```
# Example:
DATABASE_URL=postgresql://postgres:password@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```
[database.py](backend/app/db/database.py) will **automatically** use this if explicitly defined.

### Deployment on Render
> **Recommended free setup**: Render free tier for hosting + Supabase free tier (IPv4 session pooler) for database. This combination provides a fully functional backend without cost.
1. Push your repo to GitHub.
2. Create a new **Web Service** on Render.
3. Connect it to your repository.
4. Set the environment variables in the dashboard.
5. Set **Build Command** to:
```
pip install -r requirements.txt
```
6. Set the **Start Command** to:
```
gunicorn -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8000
```
If you want Render to assign the port **automatically**, set `8000` to `$PORT`

7. Deploy and monitor logs. The app should start and hit the `/` endpoint with:
```json
{"message": "SteamVault API running."}
```

---

### Cron Jobs / Scheduled Tasks
| Job Name             | Frequency        | Target Endpoint               | Purpose                           |
| -------------------- | ---------------- | ----------------------------- | --------------------------------- |
| `steamvault-fetch`   | Every 15 minutes | `/fetch/`                     | Fetch latest Steam data           |
| `steamvault-ping`    | Every 5 minutes  | `/cron/ping`                  | Keep Render app alive             |
| `steamvault-summary` | Daily at 1:00 AM | `/analytics/summary/generate` | Generate daily playtime summaries |

> Cron jobs can be set up via **Google Cloud Scheduler** for free (or any cron service) pointing to the app’s endpoints.

---

## Extending SteamVault
- Switch to any PostgreSQL compatible database by updating `DATABASE_URL`
- Deploy on other cloud platforms (Heroku, Vercel, AWS) with minimal changes.
- Frontend is fully decoupled

---

**Author:** Omrahn Faqiri  
**License:** MIT  
© 2025 SteamVault