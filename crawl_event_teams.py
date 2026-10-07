#!/usr/bin/env python3
"""
Crawler for NorCal FLL Event Participating Teams.
Fetches participating teams for each event from:
https://mylumi.playingatlearning.org/api/event/{event_id}/teams/

Updates:
- data/raw/event_teams_{event_id}.json
- data/raw/event_teams_all.json
- SQLite `data/mylumi.db` (`event_teams` and `events` tables)
"""

import json
import logging
from pathlib import Path
import sqlite3
import time
import urllib.error
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawl_event_teams")

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "mylumi.db"
BASE_URL = "https://mylumi.playingatlearning.org/api/event/{event_id}/teams/"


def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://mylumi.playingatlearning.org/",
    }


def fetch_event_teams(event_id):
    """Fetch all teams registered for a specific event."""
    url = f"{BASE_URL.format(event_id=event_id)}?page_size=100"
    headers = get_headers()
    all_teams = []

    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning("Event %d: 404 Not Found", event_id)
                return []
            logger.error("Event %d HTTP error %s: %s", event_id, e.code, e.reason)
            return []
        except Exception as e:
            logger.error("Event %d request failed: %s", event_id, e)
            return []

        results = data.get("results", [])
        all_teams.extend(results)
        url = data.get("next")

    return all_teams


def get_target_events():
    """Retrieve all 2026 season events and active events from DB or JSON."""
    events = []
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, season, program, venue_city, venue_name, capacity, start_time
            FROM events
            WHERE season LIKE '%2026%' OR id >= 300
            ORDER BY id
        """)
        rows = cur.fetchall()
        events = [dict(r) for r in rows]
        conn.close()

    if not events:
        active_json = RAW_DIR / "events_active.json"
        if active_json.exists():
            with open(active_json, "r", encoding="utf-8") as f:
                events = json.load(f)

    # Fallback to standard 301..314 range if needed
    if not events:
        events = [{"id": i, "name": f"Event {i}"} for i in range(301, 315)]

    return events


def crawl_all_event_teams():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    events = get_target_events()
    logger.info("Found %d target events to crawl.", len(events))

    all_event_teams_data = {}
    total_registrations = 0
    unique_team_numbers = set()

    conn = sqlite3.connect(DB_PATH) if DB_PATH.exists() else None
    cur = conn.cursor() if conn else None

    for ev in events:
        eid = ev["id"]
        ev_name = ev.get("name", f"Event {eid}")
        logger.info("Crawling Event #%d: %s...", eid, ev_name)

        teams_raw = fetch_event_teams(eid)
        count = len(teams_raw)
        total_registrations += count
        logger.info("  -> Fetched %d registered teams.", count)

        # Save individual raw event file
        event_raw_path = RAW_DIR / f"event_teams_{eid}.json"
        with open(event_raw_path, "w", encoding="utf-8") as f:
            json.dump({
                "event_id": eid,
                "event_name": ev_name,
                "count": count,
                "teams": teams_raw
            }, f, ensure_ascii=False, indent=2)

        all_event_teams_data[eid] = {
            "event_id": eid,
            "event_name": ev_name,
            "count": count,
            "teams": teams_raw
        }

        # Update SQLite if available
        if cur:
            # Update events table total_registered
            cur.execute("UPDATE events SET total_registered = ? WHERE id = ?", (count, eid))

            # Replace event_teams records for this event
            cur.execute("DELETE FROM event_teams WHERE event_id = ?", (eid,))
            for item in teams_raw:
                t = item.get("team") or {}
                tnum = t.get("number")
                if tnum:
                    unique_team_numbers.add(tnum)
                cur.execute("""
                    INSERT INTO event_teams (
                        event_id, team_id, team_number, team_name, city, org_name,
                        advancing_to_next_level, advancing_wait_list
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    eid,
                    t.get("id"),
                    tnum,
                    t.get("name"),
                    t.get("city"),
                    t.get("org_name"),
                    1 if item.get("advancing_to_next_level") else 0,
                    1 if item.get("advancing_wait_list") else 0
                ))

        time.sleep(0.15)

    if conn:
        conn.commit()
        conn.close()
        logger.info("Database updated with latest event teams and registered counts.")

    # Save merged all event teams JSON
    merged_path = RAW_DIR / "event_teams_all.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(all_event_teams_data, f, ensure_ascii=False, indent=2)
    logger.info("Saved all event teams data to %s.", merged_path)

    logger.info("=" * 60)
    logger.info("CRAWL COMPLETED SUMMARY:")
    logger.info("  Total Events Crawled: %d", len(events))
    logger.info("  Total Registrations: %d", total_registrations)
    logger.info("  Unique Teams Registered: %d", len(unique_team_numbers))
    logger.info("=" * 60)

    return all_event_teams_data


if __name__ == "__main__":
    crawl_all_event_teams()
