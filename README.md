# SteamVault
personal steam tracker

![Python 3.12.7](https://img.shields.io/badge/Python-3.12.7-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-009688.svg?logo=fastapi)

## High-level planned architecture
**Frontend**
- calls api via https -> (Fly.io or Render hosted app) 

**Backend**
- handles steam API calls
- stores data in db
- exposes endpoints
- automated via Render cron-jobs or github actions
  - hit `/fetch/daily/` every X hours

**Database**
- data snapshots
- computed analytics
- hosted with backend (any lightweight db)


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

### daily_analytics
- update this

## API Endpoints
| Endpoint                      | Method | Description                                             |
| ----------------------------- | ------ | ------------------------------------------------------  |
| `/fetch/`                     | GET    | Fetch owned games & update snapshots (`.env` protected) |
| `/analytics/summary/generate` | POST   | Compute daily summary (admin-protected)                 |
| `/analytics/summary/latest`   | GET    | Get most recent daily summary                           |
| `/`                           | GET    | Default route                                           |

## Installation

**Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Install Requirements**
```bash
pip install -r requirements.txt
```

**Setup Environment**
Create `.env` file:
```
STEAM_API_KEY=your_key
STEAM_ID=your_id
ADMIN_TOKEN=your_secret
```
**Run app**
```bash
uvicorn backend.app.main:app --reload
```