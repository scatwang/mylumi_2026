#!/usr/bin/env python3
"""
Crawl all public teams from MyLumi API:
https://mylumi.playingatlearning.org/api/team/public/list/?page_size=75

Saves:
- data/raw/public_teams.json
- data/csv/public_teams.csv
- data/mylumi.db (table: public_teams)
"""

import csv
import json
import logging
from pathlib import Path
import sqlite3
import time
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("public_teams_crawler")

BASE_API = "https://mylumi.playingatlearning.org/api/team/public/list/"
PAGE_SIZE = 75
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_page(page: int, max_retries: int = 5, delay: float = 1.0):
    url = f"{BASE_API}?page={page}&page_size={PAGE_SIZE}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.warning("HTTP error %d fetching page %d (attempt %d): %s", e.code, page, attempt, e.reason)
            if e.code == 404:
                return None
        except Exception as e:
            logger.warning("Error fetching page %d (attempt %d): %s", page, attempt, e)

        time.sleep(delay * (2 ** (attempt - 1)))
    return None


def crawl_all_teams():
    logger.info("Starting public teams crawl...")
    all_teams = []
    page = 1
    total_count = None

    while True:
        logger.info("Fetching page %d...", page)
        data = fetch_page(page)
        if not data:
            logger.error("Failed to fetch page %d, aborting.", page)
            break

        total_count = data.get("count", total_count)
        results = data.get("results", [])
        if not results:
            logger.info("No results returned for page %d, ending crawl.", page)
            break

        all_teams.extend(results)
        logger.info("Fetched page %d: %d teams (Total accumulated: %d / %s)",
                    page, len(results), len(all_teams), total_count)

        if not data.get("next") or (total_count and len(all_teams) >= total_count):
            break

        page += 1
        time.sleep(0.3)  # Polite throttle

    logger.info("Successfully fetched %d teams in total.", len(all_teams))
    return all_teams


def flatten_team(t: dict) -> dict:
    sq = t.get("status_quickview") or {}
    screening = sq.get("screening") or {}
    fingerprinting = sq.get("fingerprinting") or {}
    coaches = sq.get("coaches") or {}
    roster = sq.get("roster_status") or {}
    agreements = sq.get("agreements") or {}
    advancement = t.get("advancement") or {}

    registered_events = t.get("registered_events") or []

    return {
        "id": t.get("id"),
        "number": t.get("number"),
        "name": t.get("name"),
        "city": t.get("city"),
        "org_name": t.get("org_name"),
        "program_id": t.get("program_id"),
        "program_label": t.get("program_label"),
        "status_v2": t.get("status_v2"),
        "coaches_count": t.get("coaches_count"),
        # Screening
        "screening_good": screening.get("good"),
        "screening_details": screening.get("details"),
        "screening_count": screening.get("count"),
        "screening_threshold": screening.get("threshold"),
        # Fingerprinting
        "fingerprinting_good": fingerprinting.get("good"),
        "fingerprinting_details": fingerprinting.get("details"),
        "fingerprinting_count": fingerprinting.get("count"),
        "fingerprinting_threshold": fingerprinting.get("threshold"),
        "livescan_count": fingerprinting.get("livescan_count"),
        "mrt_count": fingerprinting.get("mrt_count"),
        "bcia_count": fingerprinting.get("bcia_count"),
        "bcia_status": fingerprinting.get("bcia"),
        # Coaches Quickview
        "coaches_good": coaches.get("good"),
        "coaches_required": coaches.get("required_count"),
        "coaches_invited": coaches.get("invited"),
        # Roster
        "roster_good": roster.get("good"),
        "roster_details": roster.get("details"),
        "roster_count": roster.get("count"),
        "roster_threshold": roster.get("threshold"),
        # Agreements
        "agreements_good": agreements.get("good"),
        "agreements_details": agreements.get("details"),
        "jotform_required": agreements.get("jotform_required"),
        "jotform_complete": agreements.get("jotform_complete"),
        # Advancement
        "advancement_state": advancement.get("state"),
        # Registered events
        "registered_events_count": len(registered_events),
        "registered_events_json": json.dumps(registered_events, ensure_ascii=False),
        # Logos
        "program_logo_path": t.get("program_logo_path"),
        "season_logo_path": t.get("season_logo_path"),
    }


def save_to_json(teams, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
    logger.info("Saved raw JSON to %s (%d teams)", output_path, len(teams))


def save_to_csv(flat_teams, output_path: Path):
    if not flat_teams:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(flat_teams[0].keys())
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_teams)
    logger.info("Saved CSV to %s (%d rows)", output_path, len(flat_teams))


def save_to_sqlite(flat_teams, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS public_teams")
    cur.execute("""
    CREATE TABLE public_teams (
        id INTEGER PRIMARY KEY,
        number INTEGER,
        name TEXT,
        city TEXT,
        org_name TEXT,
        program_id INTEGER,
        program_label TEXT,
        status_v2 TEXT,
        coaches_count INTEGER,
        screening_good INTEGER,
        screening_details TEXT,
        screening_count INTEGER,
        screening_threshold INTEGER,
        fingerprinting_good INTEGER,
        fingerprinting_details TEXT,
        fingerprinting_count INTEGER,
        fingerprinting_threshold INTEGER,
        livescan_count INTEGER,
        mrt_count INTEGER,
        bcia_count INTEGER,
        bcia_status TEXT,
        coaches_good INTEGER,
        coaches_required INTEGER,
        coaches_invited INTEGER,
        roster_good INTEGER,
        roster_details TEXT,
        roster_count INTEGER,
        roster_threshold INTEGER,
        agreements_good INTEGER,
        agreements_details TEXT,
        jotform_required INTEGER,
        jotform_complete INTEGER,
        advancement_state TEXT,
        registered_events_count INTEGER,
        registered_events_json TEXT,
        program_logo_path TEXT,
        season_logo_path TEXT
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_public_teams_number ON public_teams(number)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_public_teams_city ON public_teams(city)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_public_teams_status ON public_teams(status_v2)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_public_teams_program ON public_teams(program_label)")

    sql = """
    INSERT INTO public_teams (
        id, number, name, city, org_name, program_id, program_label, status_v2, coaches_count,
        screening_good, screening_details, screening_count, screening_threshold,
        fingerprinting_good, fingerprinting_details, fingerprinting_count, fingerprinting_threshold,
        livescan_count, mrt_count, bcia_count, bcia_status,
        coaches_good, coaches_required, coaches_invited,
        roster_good, roster_details, roster_count, roster_threshold,
        agreements_good, agreements_details, jotform_required, jotform_complete,
        advancement_state, registered_events_count, registered_events_json,
        program_logo_path, season_logo_path
    ) VALUES (
        :id, :number, :name, :city, :org_name, :program_id, :program_label, :status_v2, :coaches_count,
        :screening_good, :screening_details, :screening_count, :screening_threshold,
        :fingerprinting_good, :fingerprinting_details, :fingerprinting_count, :fingerprinting_threshold,
        :livescan_count, :mrt_count, :bcia_count, :bcia_status,
        :coaches_good, :coaches_required, :coaches_invited,
        :roster_good, :roster_details, :roster_count, :roster_threshold,
        :agreements_good, :agreements_details, :jotform_required, :jotform_complete,
        :advancement_state, :registered_events_count, :registered_events_json,
        :program_logo_path, :season_logo_path
    )
    """

    # SQLite boolean convert
    converted_rows = []
    for row in flat_teams:
        c_row = dict(row)
        for bool_key in ["screening_good", "fingerprinting_good", "coaches_good", "roster_good",
                         "agreements_good", "jotform_required", "jotform_complete"]:
            val = c_row.get(bool_key)
            c_row[bool_key] = 1 if val is True else (0 if val is False else None)
        converted_rows.append(c_row)

    cur.executemany(sql, converted_rows)
    conn.commit()
    conn.close()
    logger.info("Saved %d records into SQLite table 'public_teams' at %s", len(flat_teams), db_path)


def main():
    root_dir = Path(__file__).resolve().parent
    data_dir = root_dir / "data"

    teams = crawl_all_teams()
    if not teams:
        logger.error("No teams crawled!")
        return

    flat_teams = [flatten_team(t) for t in teams]

    # Save JSON
    save_to_json(teams, data_dir / "raw" / "public_teams.json")

    # Save CSV
    save_to_csv(flat_teams, data_dir / "csv" / "public_teams.csv")

    # Save SQLite
    save_to_sqlite(flat_teams, data_dir / "mylumi.db")

    logger.info("Public teams crawling and storage complete!")


if __name__ == "__main__":
    main()
