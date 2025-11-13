# SteamVault
![Python 3.12.7](https://img.shields.io/badge/Python-3.12.7-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg?logo=fastapi)![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render)

> **SteamVault** is a modular **backend analytics engine** and **REST API** that automatically tracks your Steam gaming activity.  
It fetches daily playtime, stores historical snapshots, and generates rich analytics such as:
- Daily summaries  
- Weekly/monthly top games  
- 14-day playtime trends  
- Streak detection  
- Activity heatmaps  
- Per-game history previews  
- Multi-game comparisons  

SteamVault is **backend only by design**.  
You can interact with it through HTTP clients (Postman, curl) or connect any frontend/dashboard you prefer.

This provides an extensible and production ready analytics service that anyone can build on.

---

# Table of Contents
- [SteamVault](#steamvault)
- [Table of Contents](#table-of-contents)
    - [⭐ Why SteamVault?](#-why-steamvault)
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
  - [Installation \& Deployment](#installation--deployment)
    - [Environment Variables](#environment-variables)
      - [Required Variables](#required-variables)
      - [Notes](#notes)
    - [Local Development Setup](#local-development-setup)
      - [1. Clone \& Install](#1-clone--install)
      - [2. Start the API](#2-start-the-api)
    - [Mock Data (optional, for testing)](#mock-data-optional-for-testing)
    - [Deployment on Render](#deployment-on-render)
      - [Database Requirements](#database-requirements)
    - [Cron Jobs / Scheduled Tasks](#cron-jobs--scheduled-tasks)
  - [Extending SteamVault](#extending-steamvault)


---

### ⭐ Why SteamVault?
Steam shows lifetime playtime, but offers no **historical records** or analytics. SteamVault fills this gap by generating daily snapshots and summaries, enabling:
- Daily snapshots
- Daily summaries
- Trends and top games
- Streaks and activity heatmaps
- Game comparisons over time

---

### Key Features
- Fetch Steam library + playtime automatically
- Generate daily summaries and analytics
- Weekly/monthly/lifetime top games
- Trends across the last 14 days
- Per-game history previews and comparisons
- Activity heatmap (day-by-day)

> The project is designed to be modular: while the recommended free setup uses **Supabase PostgreSQL (IPv4 session pooler)** and **Render** for hosting, it can be easily adapted to other Postgres databases or deployment platforms. This is just a general reference setup and the app can be configured to work with any PostgreSQL-compatible database or hosting platform.

---

## Tech Stack
- **Backend:** FastAPI, Python 3.12.7, Gunicorn + Uvicorn
- **Database:** Supabase PostgreSQL (IPv4 Session Pooler, SSL enforced)
- **Cloud & CI/CD:** Render (auto-deploy from GitHub main branch)
- **Scheduler:** Google Cloud Scheduler (cron jobs)
- **Frontend:** Not yet implemented (API only, fully decoupled)
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
│   │   ├── generate_mock_history.py # Explained later
├── requirements.txt
└── README.md
└── steamvault.db                    # (Optional) Explained later
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

## Installation & Deployment
Before running SteamVault, create an `.env` file in the root of the project.
### Environment Variables
#### Required Variables
```bash
# Steam API
STEAM_API_KEY=YOUR_STEAM_API_KEY
STEAM_ID=YOUR_STEAM_64_ID

# Security tokens
ADMIN_TOKEN=GENERATE_A_RANDOM_SECRET
CRON_SECRET=GENERATE_A_DIFFERENT_SECRET

# Database (pick one)
DATABASE_URL=   # Full PostgresSQL URL
# or, for SQLite development:
DATABASE_URL=sqlite:///./steamvault.db
```
#### Notes
**How do I get these keys and security tokens?**
- **STEAM_API_KEY** — https://steamcommunity.com/dev/apikey
- **STEAM_ID** — https://steamid.io/
- **ADMIN_TOKEN** / **CRON_SECRET**
  - Use any random string. For ex:
    - Open terminal and type `openssl rand -hex 32`
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
- Enable **IPv4 session pooler**
- Enable **SSL required**

---

### Cron Jobs / Scheduled Tasks
| Job Name             | Frequency        | Target Endpoint               | Purpose                           |
| -------------------- | ---------------- | ----------------------------- | --------------------------------- |
| `steamvault-fetch`   | Every 15 minutes | `/fetch/`                     | Fetch latest Steam data           |
| `steamvault-ping`    | Every 5 minutes  | `/cron/ping`                  | Keep Render app alive             |
| `steamvault-summary` | Daily at 1:00 AM | `/analytics/summary/generate` | Generate daily playtime summaries |

> Google Cloud Scheduler, GitHub Actions, or any external cron service works.

---

## Extending SteamVault
- Swap PostgreSQL for any other compatible database
- Deploy on other cloud platforms with minimal changes
- Frontend is fully decoupled; add frontend anytime

---

**Author:** Omrahn Faqiri  
**License:** MIT  
© 2025 SteamVault