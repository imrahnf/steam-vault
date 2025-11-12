# SteamVault
Personal Steam playtime tracker

![Python 3.12.7](https://img.shields.io/badge/Python-3.12.7-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg?logo=fastapi)

## High-level planned architecture
**Frontend**
- not yet implemented

**Backend**
- Handles Steam API calls.
- Stores snapshots and analytics in the database
- Exposes endpoints for fetching data and viewing analytics

**Database**
- SQLite (tentative)
- Stores snapshots, game info, and computed daily summaries.


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


## API Endpoints
| Endpoint                      | Method | Description                                                          |
| ----------------------------- | ------ | -------------------------------------------------------------------- |
| `/fetch/`                     | GET    | Fetch owned games from Steam and update snapshots (`.env` protected) |
| `/fetch/profile`              | GET    | Get Steam profile info (cached)                                      |
| `/analytics/summary/generate` | POST   | Compute daily summary (`.env` protected)                             |
| `/analytics/summary/latest`   | GET    | Get the most recent daily summary                                    |
| `/analytics/top_games`        | GET    | Get top games over week, month, or lifetime                          |
| `/analytics/trends`           | GET    | Get playtime trends over the last two weeks                          |
| `/`                           | GET    | Default route to check API status                                    |

## Installation
**Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Install Dependencies**
```bash
pip install -r requirements.txt
```

**Setup Environment**
Create `.env` file in root:
```
STEAM_API_KEY=your_key
STEAM_ID=your_id
ADMIN_TOKEN=your_secret
DATABASE_URL=database_url
CRON_SECRET=secret_code
```
**Run app**
```bash
uvicorn backend.app.main:app --reload
```