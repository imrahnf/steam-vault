  # SteamVault
  personal steam tracker

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

  ## Backend planned design
  ```
  backend/
  │
  ├── app/
  │   ├── main.py
  │   ├── routes/
  │   │   ├── fetch.py        # fetch data via Steam API
  │   │   ├── analytics.py    # give frontend summaries
  │   │   └── admin.py        # manual fetch and info
  │   ├── models/ # 
  │   │   ├── game.py         # tentative 
  │   │   ├── snapshot.py     # tentative 
  │   │   ├── analytics.py    # tentative 
  │   │   └── base.py         # tentative 
  │   ├── services/
  │   │   ├── steam_api.py    # fetch data from Steam API
  │   │   ├── compute.py      # calculate statistics
  │   │   └── cron.py         # automation
  │   └── database.py         # database handling
  ```

  ## Database schema
  ### games
  | Column         | Type     | Description                           |
  | -------------- | -------- | ------------------------------------- |
  | `id`           | int (PK) | Auto ID                               |
  | `appid`        | int      | Steam App ID                          |
  | `name`         | text     | Game name                             |
  | `img_icon_url` | text     | Game image URL (for frontend display) |

  ### snapshots
  | Column                  | Type              | Description              |
  | ----------------------- | ----------------- | ------------------------ |
  | `id`                    | int (PK)          | Auto ID                  |
  | `date`                  | datetime          | When data was fetched    |
  | `appid`                 | int (FK -> games) | Which game               |
  | `playtime_forever`      | int               | Total playtime (hours)   |
  | `last_played`           | datetime          | last_played              |

  ### daily_analytics
  | Column                      | Type     | Description                           |
  | --------------------------- | -------- | ------------------------------------- |
  | `date`                      | datetime | Date of snapshot                      |
  | `total_playtime_today`      | int      | Total playtime added                  |
  | `games_played_today`        | int      | Count of games with playtime increase |
  | `top_game_today`            | text     | Game with most new playtime           |

  ### cached_summary
  | Column       | Type     | Description                         |
  | ------------ | -------- | ----------------------------------- |
  | `id`         | int (PK) | Auto ID                             |
  | `updated_at` | datetime | When last computed                  |
  | `data`       | JSON     | Cached data blob for `/api/summary` |

  ## API Endpoints

  `/fetch/daily`
  - `POST` method automated by cron
  - fetch games, playtime, achievements, etc..
  - saves data into `snapshots` and computes daily anayltics

  `/api/daily_summary`
  - return most recent analytics summary

  `/api/top_games`
  - return top games by lifetime

  `/api/trends`
  - return the histortical playtime trend data

  `/admin/fetch`
  - manually trigger fetch protected by the `.env` toekn

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

  **Activate venv**
  ```bash
  source .venv/bin/activate
  ```

  ## Running app
  **Start Server**
  ```bash
  uvicorn main:app --reload --app-dir backend
  ```