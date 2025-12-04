# SteamVault
![Python 3.12.7](https://img.shields.io/badge/Python-3.12.7-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg?logo=fastapi) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg) ![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render) ![Live Demo](https://img.shields.io/badge/Live_Demo-SteamVault-0A84FF?logo=google-chrome&logoColor=white)

> **SteamVault** is a modular **backend analytics engine** and **REST API** that automatically tracks your Steam gaming activity.  
It fetches daily playtime, stores historical snapshots, and generates rich analytics such as:
- Daily summaries.
- Weekly/monthly top games.
- 14-day playtime trends.  
- Streak detection.  
- Activity heatmaps.  
- Per-game history previews.  
- Multi-game comparisons.  

> SteamVault is **backend-only by design**. There is **no official frontend** yet, but any dashboard can be plugged in.

This provides an extensible and production ready analytics service that anyone can build on.

---

# Live Demo (Frontend Dashboard)
**A lightweight frontend dashboard is available here:**
👉 **https://steamvault.omrahnfaqiri.com**

This demo is powered by the public `/demo/*` analytics API is fully readonly. No Steam account required.

# Quick Start (Demo Mode)
```bash
git clone https://github.com/imrahnf/steam-vault
cd steam-vault
python -m venv .venv

source .venv/bin/activate # MacOS/Linux
# or 
.venv\Scripts\activate # Windows

pip install -r requirements.txt
cp .env.example .env
uvicorn backend.app.main:app --reload
# Visit http://127.0.0.1:8000/docs
```
---

# Table of Contents
- [SteamVault](#steamvault)
- [Quick Start (Demo Mode)](#quick-start-demo-mode)
  - [🚀 Live Demo (Frontend Dashboard)](#-live-demo-frontend-dashboard)
- [Table of Contents](#table-of-contents)
    - [Why SteamVault?](#-why-steamvault)
    - [Key Features](#key-features)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Database schema](#database-schema)
    - [games](#games)
    - [snapshots](#snapshots)
    - [daily\_summaries](#daily_summaries)
  - [API Endpoints](#api-endpoints)
    - [Fetch](#fetch)
    - [Analytics](#analytics)
    - [Games](#games-1)
    - [System/Cron Job](#systemcron-job)
  - [API Usage](#api-usage)
    - [Admin Protected Routes](#admin-protected-routes)
    - [Cron Protected Routes](#cron-protected-routes)
    - [Public Endpoints](#public-endpoints)
  - [Demo Mode (Optional)](#demo-mode-optional)
    - [What Demo Mode Does](#what-demo-mode-does)
    - [Demo Database](#demo-database)
    - [Demo Routes (`/demo/*`)](#demo-routes-demo)
  - [Installation \& Deployment](#installation--deployment)
    - [Environment Variables](#environment-variables)
      - [Required Variables](#required-variables)
      - [Notes](#notes)
    - [Local Development Setup](#local-development-setup)
      - [1. Clone \& Install](#1-clone--install)
      - [2. Start the API](#2-start-the-api)
      - [API Docs (Swagger/ReDoc/OpenAPI)](#api-docs-swaggerredocopenapi)
      - [To **show docs**, replace this in `main.py`:](#to-show-docs-replace-this-in-mainpy)
    - [Mock Data (optional, for testing)](#mock-data-optional-for-testing)
    - [Deployment on Render](#deployment-on-render)
      - [Database Requirements](#database-requirements)
    - [Cron Jobs / Scheduled Tasks](#cron-jobs--scheduled-tasks)
  - [Extending SteamVault](#extending-steamvault)


---

### Why SteamVault?
Steam shows lifetime playtime, but offers no **historical records** or analytics. SteamVault fills this gap by generating daily snapshots and summaries, enabling:
- Daily snapshots.
- Daily summaries.
- Trends and top games.
- Streaks and activity heatmaps.
- Game comparisons over time.

---

### Key Features
- Fetch Steam library + playtime automatically.
- Generate daily summaries and analytics.
- Weekly/monthly/lifetime top games.
- Trends across the last 14 days.
- Per-game history previews and comparisons.
- Activity heatmap (day-by-day).

> The project is designed to be modular: while the recommended free setup uses **Supabase PostgreSQL (IPv4 session pooler)** and **Render** for hosting, it can be easily adapted to other Postgres databases or deployment platforms. This is just a general reference setup and the app can be configured to work with any PostgreSQL-compatible database or hosting platform.

---

## Tech Stack
- **Backend:** FastAPI, Python 3.12.7, Gunicorn + Uvicorn.
- **Database:** Supabase PostgreSQL (IPv4 Session Pooler, SSL enforced).
- **Cloud & CI/CD:** Render (auto-deploy from GitHub main branch).
- **Scheduler:** Google Cloud Scheduler (cron jobs).
- **Frontend:** Not yet implemented (API only, fully decoupled).
> A small in-memory caching layer reduces redundant Steam API calls. See [backend/app/services/cache.py](backend/app/services/cache.py) for more info.

---
## Project Structure
```
steam-vault/
├── backend/
│   ├── app/
│   │   ├── routes/                  # API endpoints
│   │   ├── db/                      # Database setup
│   │   ├── services/                # Logic (Steam fetch, analytics, cache)
│   │   └── main.py                  # FastAPI entrypoint
│   │   └── security.py              # Authorize internal endpoint calls
│   ├── scripts/
│   │   └── generate_mock_history.py # Explained later
├── requirements.txt
└── steamvault.db                    # (Optional) Explained later
└── steamvault_demo.db               # (Optional) Explained later
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
### Fetch
| Endpoint         | Method | Description                                                    |
| ---------------- | ------ | -------------------------------------------------------------- |
| `/fetch/`        | GET    | Fetch owned games + create snapshot (**admin token required**) |
| `/fetch/profile` | GET    | Fetch Steam profile info (cached)                              |

### Analytics
| Endpoint                      | Method | Description                                       |
| ----------------------------- | ------ | ------------------------------------------------- |
| `/analytics/summary/generate` | POST   | Generate daily summary (**admin token required**) |
| `/analytics/summary/latest`   | GET    | Most recent summary                               |
| `/analytics/summary/history`  | GET    | Daily summaries (range or limited)                |
| `/analytics/top_games`        | GET    | Top games for week / month / lifetime             |
| `/analytics/trends`           | GET    | 14-day trend data                                 |
| `/analytics/streaks`          | GET    | Play streaks (per game)                |
| `/analytics/activity/heatmap` | GET    | Daily activity heatmap                            |
| `/analytics/games/compare`    | GET    | Compare multiple games side by side               |

### Games
| Endpoint         | Method | Description                           |
| ---------------- | ------ | ------------------------------------- |
| `/games/search`  | GET    | Search games by name                  |
| `/games/{appid}` | GET    | Game details + n-day history preview |

### System/Cron Job
| Endpoint     | Method | Description                                 |
| ------------ | ------ | ------------------------------------------- |
| `/`          | GET    | API status                                  |
| `/cron/ping` | POST   | Keep Render alive (**cron token required**) |


## API Usage
### Admin Protected Routes
These endpoints require `x-token` in the request header with the value of `ADMIN_TOKEN` from `.env`:
- `/fetch/`
- `/analytics/summary/generate/`

### Cron Protected Routes
Requires `x-token` header with `CRON_SECRET` from `.env`:
- `/cron/ping/`

### Public Endpoints
Accessible without any tokens- fully public:
- `/fetch/profile`
- `/analytics/summary/latest`
- `/analytics/trends`
- `/analytics/top_games`
- `/analytics/summary/history`
- `/analytics/streaks`
- `/analytics/activity/heatmap`
- `/analytics/games/compare`
- `/games/*`

---

## Demo Mode (Optional)
SteamVault includes a **fully isolated demo environment** that exposes read only analytics using a separate SQLite database, controlled with the `.env` variable:
```ini
DEMO_MODE=1
```

### What Demo Mode Does
When `DEMO_MODE=1`:
- The API **does NOT hit the real Steam API**
- The API **does NOT run fetch or write operations**
- The API uses `steamvault_demo.db`, which ships with the repository
  - No database initialization required
- Only demo endpoints (`/demo/*`) are enabled
- API documentation (Swagger/ReDoc/OpenAPI) is automatically **enabled**

> In `DEMO_MODE=1`, the API switches to demo-only mode using `steamvault_demo.db`, and only `/demo/*` routes are registered. Regular production routes (`/fetch`, `/analytics/*`, `/games/*`) are disabled.
> 
> **Note**: API documentation is enabled automatically in `DEMO_MODE`, but can also be enabled separately using `SHOW_DEMO_DOCS=1`.



### Demo Database
The repo includes:
```
steamvault_demo.db
```
This database contains pre generated example game histories, allowing users to explore analytics **without connecting their Steam account**.

### Demo Routes (`/demo/*`)
| Endpoint                           | Method | Description                            |
| ---------------------------------- | ------ | -------------------------------------- |
| `/demo/analytics/summary/latest`   | GET    | Latest daily summary (demo DB)         |
| `/demo/analytics/summary/history`  | GET    | Historical summaries                   |
| `/demo/analytics/top_games`        | GET    | Top games (week/month/lifetime)        |
| `/demo/analytics/trends`           | GET    | 14-day trends                          |
| `/demo/analytics/streaks`          | GET    | Play streaks (all games or per-game)   |
| `/demo/analytics/activity/heatmap` | GET    | 90-day activity heatmap                |
| `/demo/analytics/games/compare`    | GET    | Compare multiple games by `appid` list |
| `/demo/games/search`               | GET    | Search games in demo DB                |
| `/demo/games/{appid}`              | GET    | Game details + playtime preview        |


---

## Installation & Deployment
Before running SteamVault, create an `.env` file in the root of the project.
### Environment Variables
#### Required Variables
```bash
# Demo + Docs
DEMO_MODE=0          # 1 = use demo database + enable /demo routes
SHOW_DEMO_DOCS=0      # 1 = expose demo Swagger/ReDoc even if DEMO_MODE=0

# Steam API (ignored in DEMO_MODE=1)
STEAM_API_KEY=YOUR_STEAM_API_KEY
STEAM_ID=YOUR_STEAM_64_ID

# Internal security tokens
ADMIN_TOKEN=GENERATE_A_RANDOM_SECRET
CRON_SECRET=GENERATE_A_DIFFERENT_SECRET

# Database
# Only used when DEMO_MODE=0
DATABASE_URL=sqlite:///./steamvault.db  
```
#### Notes
**How do I get these keys and security tokens?**
- **STEAM_API_KEY** — https://steamcommunity.com/dev/apikey.
- **STEAM_ID** — https://steamid.io/.
- **ADMIN_TOKEN** / **CRON_SECRET**
  - Use any random string
    - e.g: Open terminal and type `openssl rand -hex 32`
> **ADMIN_TOKEN** & **CRON_SECRET** are **not provided by the project**. You **must generate your own** secrets.

**DATABASE_URL rules**
- **Development: SQLite (recommended early on):**
    ```
    DATABASE_URL=sqlite:///./steamvault.db
    ```
- **Production: Supabase PostgreSQL:**
  Use Supabase IPv4 Session Pooler with SSL enforced (required by Render).
    ```
    postgresql://<user>:<password>@<host>:<port>/<dbname>
    ```
    If you prefer environment variable components instead, SteamVault automatically builds a PostgreSQL URL from:

    ```
    user=
    password=
    host=
    port=
    dbname=
    ```

### Local Development Setup
#### 1. Clone & Install
```bash
git clone https://github.com/imrahnf/steam-vault.git
cd steam-vault

python -m venv .venv
source .venv/bin/activate # MacOS/Linux
# or 
.venv\Scripts\activate # Windows

pip install -r requirements.txt
```

#### 2. Start the API
```bash
uvicorn backend.app.main:app --reload
```

The API will be running on:
```
http://127.0.0.1:8000
```

#### API Docs (Swagger/ReDoc/OpenAPI)
SteamVault controls documentation visibility and routing separately:
- Documentation visibility is controlled by `DEMO_MODE`, `SHOW_DEMO_DOCS`, and [/backend/app/main.py](/backend/app/main.py)
**Production deploys should always keep both disabled.**

| Variable           | Effect                                                 |
| ------------------ | ------------------------------------------------------ |
| `DEMO_MODE=1`      | Enables demo DB AND automatically **enables API docs** |
| `SHOW_DEMO_DOCS=1` | **Allows demo API docs** even when `DEMO_MODE=0`                |


**Production deploys should always keep both disabled.**

#### To **show docs**, replace this in [`main.py`](/backend/app/main.py):
```python
app = FastAPI(title="SteamVault",docs_url=None,redoc_url=None,openapi_url=None)
```
with:
```python
app = FastAPI(title="SteamVault")
```

---

### Mock Data (optional, for testing)
1. Edit: [`backend/app/db/database.py`](backend/app/db/database.py):
    ```
    # DATABASE_URL = "sqlite:///./steamvault.db"
    ```
2. Run the mock generator:
    ```
    python backend/scripts/generate_mock_history.py
    ```
    SQLite database (`steamvault.db`) will be generated.

---

### Deployment on Render
> **Recommended free setup**: Render free tier for hosting + Supabase free tier (IPv4 session pooler) for database. This combination provides a fully functional backend without cost.
1. Push your repo to GitHub.
2. Create a new **Web Service** on Render.
3. Connect it to your repository.
4. Set the same `.env` keys inside Render's environment variables section
5. **Build Command**:
    ```
    pip install -r requirements.txt
    ```
6. **Start Command**:
    ```
    gunicorn -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8000
    ```

#### Database Requirements
If using Supabase:
- Enable **IPv4 session pooler**.
- Enable **SSL required**.

---

### Cron Jobs / Scheduled Tasks
| Job Name             | Frequency            | Target Endpoint               | Purpose                           |
| -------------------- | -------------------- | ----------------------------- | --------------------------------- |
| `steamvault-fetch`   | Every 15 minutes     | `/fetch/`                     | Fetch latest Steam data           |
| `steamvault-ping`    | Every 5 minutes      | `/cron/ping`                  | Keep Render app alive             |
| `steamvault-summary` | Daily at 1:00 AM EST | `/analytics/summary/generate` | Generate daily playtime summaries |

> Google Cloud Scheduler, GitHub Actions, or any external cron service works.

---

## Extending SteamVault
- Swap PostgreSQL for any other compatible database.
- Deploy on other cloud platforms with minimal changes.
- Frontend is fully decoupled; add frontend anytime.

---

**Author:** Omrahn Faqiri  
**License:** MIT  
© 2025 SteamVault
