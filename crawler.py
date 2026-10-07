#!/usr/bin/env python3
"""
MyLumi Event Data Crawler
-------------------------
Crawls all past and current FIRST LEGO League / Robotics events from
https://mylumi.playingatlearning.org/

Data saved:
- Raw JSON responses under `data/raw/`
- SQLite database `data/mylumi.db`
- Clean CSV tables under `data/csv/`
"""

import argparse
import concurrent.futures
import csv
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "https://mylumi.playingatlearning.org"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mylumi_crawler")


def fetch_url(url: str, max_retries: int = 4, delay_between_retries: float = 1.0):
    """Fetch URL with retries, exponential backoff, and user-agent header."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8")
                    return json.loads(content)
                else:
                    logger.warning("HTTP %d for %s (attempt %d)", resp.status, url, attempt)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # resource not found, don't retry
            logger.warning("HTTP error %d for %s (attempt %d): %s", e.code, url, attempt, e.reason)
        except Exception as e:
            logger.warning("Error fetching %s (attempt %d): %s", url, attempt, e)

        if attempt < max_retries:
            time.sleep(delay_between_retries * (2 ** (attempt - 1)))

    return None


class MyLumiCrawler:
    def __init__(self, data_dir: Path, workers: int = 5, force: bool = False, delay: float = 0.05):
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw"
        self.events_raw_dir = self.raw_dir / "events"
        self.csv_dir = data_dir / "csv"
        self.db_path = data_dir / "mylumi.db"
        self.workers = workers
        self.force = force
        self.delay = delay

        # Ensure directory structure
        self.events_raw_dir.mkdir(parents=True, exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    def _save_json(self, path: Path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def crawl_metadata(self):
        """Fetch seasons, active events list, archive events list."""
        logger.info("Fetching seasons metadata...")
        seasons_path = self.raw_dir / "seasons.json"
        if self.force or not seasons_path.exists():
            seasons = fetch_url(f"{BASE_URL}/api/event/archive/seasons/")
            if seasons:
                self._save_json(seasons_path, seasons)
                logger.info("Saved %d seasons to %s", len(seasons), seasons_path)
        else:
            with open(seasons_path, "r", encoding="utf-8") as f:
                seasons = json.load(f)

        logger.info("Fetching active events list...")
        active_path = self.raw_dir / "events_active.json"
        if self.force or not active_path.exists():
            active_events = fetch_url(f"{BASE_URL}/api/event/")
            if active_events:
                self._save_json(active_path, active_events)
                logger.info("Saved %d active events to %s", len(active_events), active_path)
        else:
            with open(active_path, "r", encoding="utf-8") as f:
                active_events = json.load(f)

        logger.info("Fetching archived events list...")
        archive_path = self.raw_dir / "events_archive.json"
        if self.force or not archive_path.exists():
            archive_events = fetch_url(f"{BASE_URL}/api/event/archive/")
            if archive_events:
                self._save_json(archive_path, archive_events)
                logger.info("Saved %d archived events to %s", len(archive_events), archive_path)
        else:
            with open(archive_path, "r", encoding="utf-8") as f:
                archive_events = json.load(f)

        return seasons or [], active_events or [], archive_events or []

    def discover_all_event_ids(self, active_events, archive_events):
        """
        Combine IDs from active and archive lists, and probe IDs in range
        to catch canceled or unlisted events (e.g. IDs 1..314+).
        """
        known_ids = set()
        for e in active_events:
            if "id" in e:
                known_ids.add(e["id"])
        for e in archive_events:
            if "id" in e:
                known_ids.add(e["id"])

        logger.info("Found %d known events from index APIs (active + archive)", len(known_ids))

        # Check existing cached events on disk
        for item in self.events_raw_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                known_ids.add(int(item.name))

        max_id = max(known_ids) if known_ids else 314
        # Probe up to max_id + 10 to ensure we don't miss recent additions
        probe_target = max_id + 10
        candidates = [i for i in range(1, probe_target + 1) if i not in known_ids]

        if candidates:
            logger.info("Probing %d unlisted candidate IDs (1 to %d) to discover canceled/unlisted events...", len(candidates), probe_target)
            discovered = []

            def probe(cid):
                url = f"{BASE_URL}/api/event/{cid}/"
                res = fetch_url(url, max_retries=1)
                return cid, res is not None

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                for cid, exists in executor.map(probe, candidates):
                    if exists:
                        discovered.append(cid)

            if discovered:
                logger.info("Discovered %d extra unlisted events: %s", len(discovered), sorted(discovered))
                known_ids.update(discovered)

        all_ids = sorted(known_ids)
        logger.info("Total events to crawl: %d (ID range: %d to %d)", len(all_ids), min(all_ids), max(all_ids))
        return all_ids

    def crawl_event(self, event_id: int):
        """
        Crawl all sub-endpoints for a single event:
        - details (/api/event/{id}/)
        - scores (/api/event/{id}/scores/)
        - awards (/api/event/{id}/awards/)
        - schedules (/api/event/{id}/schedules/)
        - teams (/api/event/{id}/teams/) [with pagination]
        """
        event_dir = self.events_raw_dir / str(event_id)
        event_dir.mkdir(parents=True, exist_ok=True)

        endpoints = [
            ("details.json", f"{BASE_URL}/api/event/{event_id}/"),
            ("scores.json", f"{BASE_URL}/api/event/{event_id}/scores/"),
            ("awards.json", f"{BASE_URL}/api/event/{event_id}/awards/"),
            ("schedules.json", f"{BASE_URL}/api/event/{event_id}/schedules/"),
        ]

        # 1. Fetch fixed endpoints
        for fname, url in endpoints:
            fpath = event_dir / fname
            if not self.force and fpath.exists():
                continue
            data = fetch_url(url)
            if data is not None:
                self._save_json(fpath, data)
            if self.delay:
                time.sleep(self.delay)

        # 2. Fetch teams (handling pagination)
        teams_path = event_dir / "teams.json"
        if self.force or not teams_path.exists():
            all_teams_results = []
            next_url = f"{BASE_URL}/api/event/{event_id}/teams/"
            total_count = 0

            while next_url:
                teams_data = fetch_url(next_url)
                if not teams_data or not isinstance(teams_data, dict):
                    break
                total_count = teams_data.get("count", total_count)
                results = teams_data.get("results", [])
                all_teams_results.extend(results)
                next_url = teams_data.get("next")
                if next_url and not next_url.startswith("http"):
                    next_url = f"{BASE_URL}{next_url}"
                if self.delay:
                    time.sleep(self.delay)

            consolidated_teams = {
                "count": total_count or len(all_teams_results),
                "results": all_teams_results,
            }
            self._save_json(teams_path, consolidated_teams)

    def crawl_all(self):
        """Run full crawl of all events."""
        t0 = time.time()
        logger.info("Starting MyLumi crawler...")
        seasons, active_events, archive_events = self.crawl_metadata()
        all_ids = self.discover_all_event_ids(active_events, archive_events)

        logger.info("Downloading data for %d events using %d worker threads...", len(all_ids), self.workers)

        completed = 0
        total = len(all_ids)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_id = {executor.submit(self.crawl_event, eid): eid for eid in all_ids}
            for future in concurrent.futures.as_completed(future_to_id):
                eid = future_to_id[future]
                try:
                    future.result()
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        logger.info("Progress: %d/%d events completed (%.1f%%)", completed, total, (completed / total) * 100)
                except Exception as e:
                    logger.error("Error crawling event %d: %s", eid, e)

        elapsed = time.time() - t0
        logger.info("Finished crawling %d events in %.2f seconds!", len(all_ids), elapsed)


class MyLumiDBBuilder:
    """
    ETL component: parses raw JSON files into SQLite tables and CSV files
    for easy analytical queries.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw"
        self.events_raw_dir = self.raw_dir / "events"
        self.csv_dir = data_dir / "csv"
        self.db_path = data_dir / "mylumi.db"
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    def build_all(self):
        logger.info("Building SQLite database at %s...", self.db_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create schema
        cursor.executescript("""
        DROP TABLE IF EXISTS seasons;
        CREATE TABLE seasons (
            id INTEGER PRIMARY KEY,
            year INTEGER,
            name TEXT,
            program_abbreviation TEXT,
            season_logo_path TEXT,
            program_logo_path TEXT,
            event_count INTEGER
        );

        DROP TABLE IF EXISTS events;
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            name TEXT,
            season TEXT,
            program TEXT,
            program_abbreviation TEXT,
            event_status TEXT,
            event_status_display TEXT,
            status_v2 TEXT,
            capacity INTEGER,
            total_registered INTEGER,
            start_time TEXT,
            end_time TEXT,
            timezone TEXT,
            is_complete BOOLEAN,
            venue_id INTEGER,
            venue_city TEXT,
            venue_name TEXT,
            venue_address TEXT,
            description TEXT,
            website_uri TEXT
        );

        DROP TABLE IF EXISTS scores;
        CREATE TABLE scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            ranking INTEGER,
            ordinal TEXT,
            team_number INTEGER,
            team_name TEXT,
            judging_lane_name TEXT,
            highest_score REAL,
            round_1 REAL,
            round_2 REAL,
            round_3 REAL,
            round_4 REAL,
            gp_note_1 TEXT,
            gp_note_2 TEXT,
            gp_note_3 TEXT,
            gp_note_4 TEXT,
            FOREIGN KEY (event_id) REFERENCES events (id)
        );

        DROP TABLE IF EXISTS awards;
        CREATE TABLE awards (
            id INTEGER PRIMARY KEY,
            event_id INTEGER,
            award_type_id INTEGER,
            award_name TEXT,
            display_name TEXT,
            category TEXT,
            place_number INTEGER,
            team_number INTEGER,
            team_name TEXT,
            team_org TEXT,
            recipient_name TEXT,
            city TEXT,
            state TEXT,
            FOREIGN KEY (event_id) REFERENCES events (id)
        );

        DROP TABLE IF EXISTS event_teams;
        CREATE TABLE event_teams (
            id INTEGER PRIMARY KEY,
            event_id INTEGER,
            team_id INTEGER,
            team_number INTEGER,
            team_name TEXT,
            city TEXT,
            org_name TEXT,
            advancing_to_next_level BOOLEAN,
            advancing_wait_list BOOLEAN,
            FOREIGN KEY (event_id) REFERENCES events (id)
        );

        DROP TABLE IF EXISTS schedules;
        CREATE TABLE schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            team_number INTEGER,
            team_name TEXT,
            item_type TEXT, -- 'match' or 'judging'
            session_number INTEGER,
            start_time TEXT,
            location_name TEXT, -- table name or room
            duration_minutes INTEGER,
            is_practice BOOLEAN,
            FOREIGN KEY (event_id) REFERENCES events (id)
        );
        """)

        # 1. Populate seasons
        seasons_path = self.raw_dir / "seasons.json"
        if seasons_path.exists():
            with open(seasons_path, "r", encoding="utf-8") as f:
                seasons = json.load(f)
            for s in seasons:
                cursor.execute("""
                    INSERT OR REPLACE INTO seasons VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    s.get("id"),
                    s.get("year"),
                    s.get("name"),
                    s.get("program_abbreviation"),
                    s.get("season_logo_path"),
                    s.get("program_logo_path"),
                    s.get("event_count"),
                ))

        # Collect data for CSV export as well
        events_rows = []
        scores_rows = []
        awards_rows = []
        teams_rows = []
        schedules_rows = []

        # 2. Iterate each event directory
        event_dirs = sorted([d for d in self.events_raw_dir.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda x: int(x.name))
        logger.info("Processing %d event raw data directories into database...", len(event_dirs))

        for edir in event_dirs:
            eid = int(edir.name)

            # Details
            details_path = edir / "details.json"
            if details_path.exists():
                with open(details_path, "r", encoding="utf-8") as f:
                    det = json.load(f)
                if isinstance(det, dict):
                    venue = det.get("venue")
                    if not isinstance(venue, dict):
                        venue = {}
                    row = (
                        det.get("id", eid),
                        det.get("name"),
                        det.get("season"),
                        det.get("program"),
                        det.get("program_abbreviation"),
                        det.get("event_status"),
                        det.get("event_status_display"),
                        det.get("status_v2"),
                        det.get("capacity"),
                        det.get("total_registered"),
                        det.get("start_time"),
                        det.get("end_time"),
                        det.get("timezone"),
                        det.get("is_complete"),
                        venue.get("id"),
                        venue.get("city"),
                        venue.get("name"),
                        venue.get("address"),
                        det.get("description"),
                        det.get("website_uri"),
                    )
                    cursor.execute("""
                        INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, row)
                    events_rows.append(row)

            # Scores
            scores_path = edir / "scores.json"
            if scores_path.exists():
                with open(scores_path, "r", encoding="utf-8") as f:
                    sc_data = json.load(f)
                scores = (sc_data.get("scores") or []) if isinstance(sc_data, dict) else []
                for sc in scores:
                    if not isinstance(sc, dict):
                        continue
                    rounds = sc.get("rounds") or []
                    gp_notes = sc.get("gp_notes") or []
                    r1 = rounds[0] if len(rounds) > 0 else None
                    r2 = rounds[1] if len(rounds) > 1 else None
                    r3 = rounds[2] if len(rounds) > 2 else None
                    r4 = rounds[3] if len(rounds) > 3 else None
                    gp1 = gp_notes[0] if len(gp_notes) > 0 else None
                    gp2 = gp_notes[1] if len(gp_notes) > 1 else None
                    gp3 = gp_notes[2] if len(gp_notes) > 2 else None
                    gp4 = gp_notes[3] if len(gp_notes) > 3 else None

                    row = (
                        eid,
                        sc.get("ranking"),
                        sc.get("ordinal"),
                        sc.get("number"),
                        sc.get("name"),
                        sc.get("judging_lane_name"),
                        sc.get("highest"),
                        r1, r2, r3, r4,
                        gp1, gp2, gp3, gp4,
                    )
                    cursor.execute("""
                        INSERT INTO scores (
                            event_id, ranking, ordinal, team_number, team_name, judging_lane_name,
                            highest_score, round_1, round_2, round_3, round_4,
                            gp_note_1, gp_note_2, gp_note_3, gp_note_4
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, row)
                    scores_rows.append((None, *row))

            # Awards
            awards_path = edir / "awards.json"
            if awards_path.exists():
                with open(awards_path, "r", encoding="utf-8") as f:
                    aw_data = json.load(f)
                awards_dict = (aw_data.get("awards") or {}) if isinstance(aw_data, dict) else {}
                if isinstance(awards_dict, dict):
                    for category, items in awards_dict.items():
                        if not isinstance(items, list):
                            continue
                        for aw in items:
                            if not isinstance(aw, dict):
                                continue
                            aw_type = aw.get("award_type") or {}
                            team = aw.get("team") or {}
                            team_org = team.get("org_name") or (team.get("org", {}).get("name") if isinstance(team.get("org"), dict) else None)
                            row = (
                                aw.get("id"),
                                eid,
                                aw_type.get("id"),
                                aw_type.get("name"),
                                aw_type.get("display_name"),
                                category,
                                aw.get("number"),
                                team.get("number"),
                                team.get("name"),
                                team_org,
                                aw.get("recipient_name"),
                                team.get("city") or aw.get("city"),
                                team.get("state") or aw.get("state"),
                            )
                            cursor.execute("""
                                INSERT OR REPLACE INTO awards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, row)
                            awards_rows.append(row)

            # Teams
            teams_path = edir / "teams.json"
            if teams_path.exists():
                with open(teams_path, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                results = (t_data.get("results") or []) if isinstance(t_data, dict) else []
                for t_item in results:
                    if not isinstance(t_item, dict):
                        continue
                    team_info = t_item.get("team") or {}
                    row = (
                        t_item.get("id"),
                        eid,
                        team_info.get("id"),
                        team_info.get("number"),
                        team_info.get("name"),
                        team_info.get("city"),
                        team_info.get("org_name"),
                        t_item.get("advancing_to_next_level"),
                        t_item.get("advancing_wait_list"),
                    )
                    cursor.execute("""
                        INSERT OR REPLACE INTO event_teams VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, row)
                    teams_rows.append(row)

            # Schedules
            schedules_path = edir / "schedules.json"
            if schedules_path.exists():
                with open(schedules_path, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                sched_obj = (s_data.get("schedules") or {}) if isinstance(s_data, dict) else {}
                if isinstance(sched_obj, dict):
                    teams_list = sched_obj.get("teams") or []
                    if isinstance(teams_list, list):
                        for t_entry in teams_list:
                            if not isinstance(t_entry, dict):
                                continue
                            t_num = t_entry.get("number")
                            t_name = t_entry.get("name")

                            # matches
                            for m in (t_entry.get("matches") or []):
                                if not isinstance(m, dict):
                                    continue
                                row = (
                                    eid,
                                    t_num,
                                    t_name,
                                    "match",
                                    m.get("number"),
                                    m.get("start_time_display"),
                                    m.get("table_name"),
                                    m.get("length"),
                                    m.get("practice"),
                                )
                                cursor.execute("""
                                    INSERT INTO schedules (
                                        event_id, team_number, team_name, item_type, session_number,
                                        start_time, location_name, duration_minutes, is_practice
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, row)
                                schedules_rows.append((None, *row))

                            # judging
                            for j in (t_entry.get("judging") or []):
                                if not isinstance(j, dict):
                                    continue
                                row = (
                                    eid,
                                    t_num,
                                    t_name,
                                    "judging",
                                    j.get("number"),
                                    j.get("start_time_display"),
                                    j.get("room"),
                                    j.get("length"),
                                    False,
                                )
                                cursor.execute("""
                                    INSERT INTO schedules (
                                        event_id, team_number, team_name, item_type, session_number,
                                        start_time, location_name, duration_minutes, is_practice
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, row)
                                schedules_rows.append((None, *row))

        conn.commit()

        # Build indexes for lightning fast analytical queries
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_events_season ON events(season);
            CREATE INDEX IF NOT EXISTS idx_scores_event ON scores(event_id);
            CREATE INDEX IF NOT EXISTS idx_scores_team ON scores(team_number);
            CREATE INDEX IF NOT EXISTS idx_awards_event ON awards(event_id);
            CREATE INDEX IF NOT EXISTS idx_awards_team ON awards(team_number);
            CREATE INDEX IF NOT EXISTS idx_teams_event ON event_teams(event_id);
            CREATE INDEX IF NOT EXISTS idx_teams_number ON event_teams(team_number);
            CREATE INDEX IF NOT EXISTS idx_schedules_event ON schedules(event_id);
            CREATE INDEX IF NOT EXISTS idx_schedules_team ON schedules(team_number);
        """)
        conn.commit()

        # Report summary counts
        cursor.execute("SELECT count(*) FROM events")
        c_events = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM scores")
        c_scores = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM awards")
        c_awards = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM event_teams")
        c_teams = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM schedules")
        c_schedules = cursor.fetchone()[0]

        logger.info(
            "SQLite database built successfully: %d events, %d scores, %d awards, %d event_teams, %d schedules",
            c_events, c_scores, c_awards, c_teams, c_schedules
        )
        conn.close()

        # Export to CSV
        logger.info("Exporting tables to CSV under %s...", self.csv_dir)
        self._export_csv(
            self.csv_dir / "events.csv",
            ["id", "name", "season", "program", "program_abbreviation", "event_status", "event_status_display", "status_v2", "capacity", "total_registered", "start_time", "end_time", "timezone", "is_complete", "venue_id", "venue_city", "venue_name", "venue_address", "description", "website_uri"],
            events_rows,
        )
        self._export_csv(
            self.csv_dir / "scores.csv",
            ["event_id", "ranking", "ordinal", "team_number", "team_name", "judging_lane_name", "highest_score", "round_1", "round_2", "round_3", "round_4", "gp_note_1", "gp_note_2", "gp_note_3", "gp_note_4"],
            [r[1:] for r in scores_rows],
        )
        self._export_csv(
            self.csv_dir / "awards.csv",
            ["id", "event_id", "award_type_id", "award_name", "display_name", "category", "place_number", "team_number", "team_name", "team_org", "recipient_name", "city", "state"],
            awards_rows,
        )
        self._export_csv(
            self.csv_dir / "teams.csv",
            ["id", "event_id", "team_id", "team_number", "team_name", "city", "org_name", "advancing_to_next_level", "advancing_wait_list"],
            teams_rows,
        )
        self._export_csv(
            self.csv_dir / "schedules.csv",
            ["event_id", "team_number", "team_name", "item_type", "session_number", "start_time", "location_name", "duration_minutes", "is_practice"],
            [r[1:] for r in schedules_rows],
        )
        logger.info("CSV files export complete!")

    def _export_csv(self, path: Path, headers, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="MyLumi Event Data Crawler")
    parser.add_argument("--data-dir", default="data", help="Output directory for crawled data (default: data)")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent download threads (default: 5)")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay in seconds between requests (default: 0.05)")
    parser.add_argument("--force", action="store_true", help="Force re-download of already downloaded files")
    parser.add_argument("--export-only", action="store_true", help="Skip download and only build SQLite/CSV from cached data")

    args = parser.parse_args()
    data_dir = Path(args.data_dir).resolve()

    crawler = MyLumiCrawler(
        data_dir=data_dir,
        workers=args.workers,
        force=args.force,
        delay=args.delay,
    )

    if not args.export_only:
        crawler.crawl_all()

    # Always build/refresh SQLite & CSV after crawl
    builder = MyLumiDBBuilder(data_dir=data_dir)
    builder.build_all()


if __name__ == "__main__":
    main()
