#!/usr/bin/env python3
# backend/scripts/generate_mock_history.py
"""
Generate synthetic historical snapshots and daily summaries for SteamVault.

- Finds latest snapshot date in DB and uses that as anchor (current day).
- For each game with an anchor snapshot, generates earlier snapshots (non-decreasing cumulative
  playtime) across ~90 days before the anchor (some days missing).
- Inserts DailySummary rows computed from inserted snapshots (skips days with zero new playtime).
"""

import random
from datetime import datetime, timedelta, time, timezone, date
from collections import defaultdict
import os
import sys


# ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.db.database import SessionLocal, engine, Base
from backend.app.db.models import Game, Snapshot, DailySummary

# ----------------------------------------------------------
# Config - tweak these to change "amount" of history or behavior
# ----------------------------------------------------------
MAX_DAYS_BACK = 95           # maximum days in past to simulate (approx 3 months)
MIN_PLAYED_DAYS = 8          # min number of days with play increments for an active game
MAX_PLAYED_DAYS = 60         # max number of days with play increments
PROB_CREATE_SNAPSHOT = 0.65  # per-day probability to create a snapshot for casual games (used indirectly)
RANDOM_SEED = 42             # reproducible runs
# ----------------------------------------------------------

random.seed(RANDOM_SEED)

def get_anchor_day(db):
    # find most recent snapshot date in DB and use its date (UTC)
    latest = db.query(Snapshot).order_by(Snapshot.date.desc()).first()
    if not latest:
        raise RuntimeError("No snapshots found in DB. Please ensure you have at least one snapshot for today.")
    # convert to date (assume stored in tz-aware UTC or naive but consistent)
    anchored_date = latest.date.astimezone(timezone.utc).date() if latest.date.tzinfo else latest.date.date()
    return anchored_date

def load_anchor_playtimes(db, anchor_date):
    """
    Return dict appid -> (playtime_forever on anchor_date, snapshot_id)
    """
    anchor_start = datetime.combine(anchor_date, time.min).replace(tzinfo=timezone.utc)
    anchor_end = datetime.combine(anchor_date + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)

    rows = (
        db.query(Snapshot)
        .filter(Snapshot.date >= anchor_start, Snapshot.date < anchor_end)
        .order_by(Snapshot.appid, Snapshot.date.desc())
        .all()
    )
    out = {}
    for s in rows:
        if s.appid not in out:
            out[s.appid] = {"playtime": s.playtime_forever, "snapshot": s}
    return out

def distribute_deltas(total_delta, k):
    """Return list of k non-negative integers that sum to total_delta (random partition)."""
    if k <= 0:
        return []
    if total_delta <= 0:
        return [0] * k
    # generate k random positive-ish parts
    cuts = sorted(random.sample(range(1, total_delta + k), k - 1)) if k > 1 else []
    parts = []
    prev = 0
    for c in cuts:
        parts.append(c - prev)
        prev = c
    parts.append(total_delta + k - prev)
    # make them more varied (subtract 1 because we used the +k trick), then scale
    parts = [max(0, p - 1) for p in parts]
    # shuffle to avoid early bias
    random.shuffle(parts)
    return parts

def ensure_no_snapshot_on_date(db, appid, dt_date):
    """Return True if a snapshot already exists for appid on dt_date (any time within that date)."""
    start = datetime.combine(dt_date, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(dt_date + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
    existing = db.query(Snapshot).filter(Snapshot.appid == appid, Snapshot.date >= start, Snapshot.date < end).first()
    return existing is not None

def insert_snapshot(db, appid, playtime_forever, dt_date, last_played=None):
    """Insert snapshot for given appid at a random time during dt_date (UTC)."""
    # pick a time-of-day
    hour = random.randint(12, 23)  # later in day makes sense for 'last played today'
    minute = random.randint(0, 59)
    sec = random.randint(0, 59)
    snap_dt = datetime(dt_date.year, dt_date.month, dt_date.day, hour, minute, sec, tzinfo=timezone.utc)
    s = Snapshot(appid=appid, playtime_forever=int(playtime_forever), date=snap_dt, last_played=last_played or snap_dt)
    db.add(s)
    return s

def compute_and_insert_daily_summary_for_date(db, target_date):
    """
    Compute daily summary for target_date using the same logic your compute_daily_summary uses:
    - For each appid, find latest snapshot during target_date (if any).
    - Find previous snapshot strictly before target_date.
    - Delta = latest.playtime_forever - prev.playtime_forever (or 0).
    - If any positive deltas, insert DailySummary for date.
    """
    day_start = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(target_date + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)

    # get latest snapshot per appid for this day
    todays_snaps = (
        db.query(Snapshot)
        .filter(Snapshot.date >= day_start, Snapshot.date < day_end)
        .order_by(Snapshot.appid, Snapshot.date.desc())
        .all()
    )
    latest_today = {}
    for s in todays_snaps:
        if s.appid not in latest_today:
            latest_today[s.appid] = s

    if not latest_today:
        return None

    total_today = 0
    playtime_by_game = {}

    for appid, snap in latest_today.items():
        prev_snap = (
            db.query(Snapshot)
            .filter(Snapshot.appid == appid, Snapshot.date < day_start)
            .order_by(Snapshot.date.desc())
            .first()
        )
        prev_playtime = prev_snap.playtime_forever if prev_snap else 0
        delta = snap.playtime_forever - prev_playtime
        if delta > 0:
            playtime_by_game[appid] = delta
            total_today += delta

    if not playtime_by_game:
        return None

    most_played_appid = max(playtime_by_game, key=playtime_by_game.get)
    most_played_minutes = playtime_by_game[most_played_appid]
    most_played_game = db.query(Game).filter_by(appid=most_played_appid).first()

    # previous summary (previous calendar day)
    prev_summary = db.query(DailySummary).filter(DailySummary.date < target_date).order_by(DailySummary.date.desc()).first()
    prev_total = prev_summary.total_playtime_minutes if prev_summary else 0
    total_change = total_today - prev_total

    summary = DailySummary(
        date=target_date,
        total_playtime_minutes=total_today,
        total_games_tracked=len(latest_today),
        most_played_appid=most_played_appid,
        most_played_name=most_played_game.name if most_played_game else None,
        most_played_minutes=most_played_minutes,
        average_playtime_per_game=round(total_today / len(latest_today), 2) if latest_today else 0,
        total_playtime_change=total_change,
        new_games_count=0  # we won't attempt to detect exact "new games" for this script
    )
    db.add(summary)
    return summary

def main():
    print("[+] Ensuring tables exist...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        anchor_date = get_anchor_day(db)
        print(f"[+] Anchor (latest) snapshot date detected: {anchor_date.isoformat()}")

        # Gather anchor playtimes
        anchor_playtimes = load_anchor_playtimes(db, anchor_date)
        if not anchor_playtimes:
            print("[-] No snapshots found for anchor date. Nothing to do.")
            return

        # list of games from DB
        games = db.query(Game).all()
        games_by_appid = {g.appid: g for g in games}
        print(f"[+] Loaded {len(games)} games from DB")

        start_date = anchor_date - timedelta(days=MAX_DAYS_BACK - 1)
        all_dates = [start_date + timedelta(days=i) for i in range((anchor_date - start_date).days + 1)]
        print(f"[+] Simulating history from {start_date.isoformat()} to {anchor_date.isoformat()} ({len(all_dates)} days)")

        # For each game, generate earlier snapshots that end at anchor_playtimes[appid]
        inserted_snapshots = 0
        for appid, anchor in anchor_playtimes.items():
            playtime_today = anchor["playtime"]
            if playtime_today <= 0:
                # nothing to simulate; maybe user never played this game
                continue

            # choose initial_playtime (cumulative) some small percent of final to simulate growth
            # ensure it's <= playtime_today
            # pick a lower bound so game isn't zero for whole range, unless small final value
            lower_bound = max(0, int(playtime_today * 0.02))  # start at 2% of final
            initial_playtime = random.randint(lower_bound, max(0, playtime_today - 1)) if playtime_today > 1 else 0

            total_delta = playtime_today - initial_playtime
            # decide how many days we'll distribute the deltas across (played days)
            # bias higher for popular games
            popularity_factor = min(1.0, playtime_today / 500.0)  # games with lots of minutes get more days
            min_days = max(MIN_PLAYED_DAYS, int(MIN_PLAYED_DAYS * (0.5 + popularity_factor)))
            max_days = min(MAX_PLAYED_DAYS, int(MAX_PLAYED_DAYS * (0.5 + popularity_factor)))
            k = random.randint(min_days, max_days) if total_delta > 0 else 0
            # limit k to available historic days (exclude anchor)
            candidate_days = [d for d in all_dates if d < anchor_date]
            if not candidate_days or k == 0:
                continue
            k = min(k, len(candidate_days))

            # choose k distinct days from candidate_days to receive increments
            played_days = sorted(random.sample(candidate_days, k))

            # distribute total_delta across k parts
            parts = distribute_deltas(total_delta, k)

            # Now insert snapshots for each played day, building cumulative value starting from initial_playtime
            cumulative = initial_playtime
            for day, inc in zip(played_days, parts):
                cumulative += inc
                # Avoid creating a snapshot if one already exists for this appid on that date
                if ensure_no_snapshot_on_date(db, appid, day):
                    continue
                insert_snapshot(db, appid, cumulative, day)
                inserted_snapshots += 1

        db.commit()
        print(f"[+] Inserted {inserted_snapshots} historical snapshots")

        # Now compute DailySummaries across the range (start_date .. anchor_date), skipping days where summary exists
        inserted_summaries = 0
        for d in all_dates:
            # skip if summary already exists for that date
            existing = db.query(DailySummary).filter(DailySummary.date == d).first()
            if existing:
                # print(f"  - summary exists for {d}")
                continue
            s = compute_and_insert_daily_summary_for_date(db, d)
            if s:
                inserted_summaries += 1
                # commit every so often to avoid huge transactions
                if inserted_summaries % 20 == 0:
                    db.commit()
        db.commit()
        print(f"[+] Inserted {inserted_summaries} daily summaries")

        print("[+] Done. You can now call /analytics endpoints to view generated data.")
        print("Tip: run GET /analytics/summary/latest and GET /analytics/trends and GET /analytics/top_games?period=month")

    except Exception as e:
        db.rollback()
        print("ERROR:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # ensure project root is on path
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    main()