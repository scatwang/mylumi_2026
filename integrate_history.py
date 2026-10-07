#!/usr/bin/env python3
"""
Integrate historical event performances, scores, awards, and advancements
from events/ and mylumi.db into public teams.

Updates:
- data/raw/public_teams.json (adds `history` object to each team)
- data/csv/public_teams.csv (adds flattened history columns)
- data/mylumi.db (adds columns to public_teams table)
- web/teams_data.js (refreshes frontend data)
"""

import csv
import json
import logging
from pathlib import Path
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("integrate_history")

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "mylumi.db"
RAW_TEAMS_JSON = DATA_DIR / "raw" / "public_teams.json"
CSV_PATH = DATA_DIR / "csv" / "public_teams.csv"
WEB_DIR = ROOT_DIR / "web"


def to_int(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def to_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def extract_history_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Map events
    cur.execute("SELECT id, name, season, start_time, venue_city, venue_name FROM events")
    events_map = {row["id"]: dict(row) for row in cur.fetchall()}

    # 2. Map scores by team_number
    cur.execute("SELECT event_id, ranking, highest_score, round_1, round_2, round_3, round_4, team_number FROM scores")
    scores_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in scores_by_team:
            scores_by_team[num] = []
        scores_by_team[num].append(dict(r))

    # 3. Map awards by team_number
    cur.execute("SELECT event_id, award_name, display_name, category, place_number, team_number FROM awards")
    awards_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in awards_by_team:
            awards_by_team[num] = []
        awards_by_team[num].append(dict(r))

    # 4. Map event_teams by team_number
    cur.execute("SELECT event_id, team_id, team_number, team_name, advancing_to_next_level, advancing_wait_list FROM event_teams")
    event_teams_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in event_teams_by_team:
            event_teams_by_team[num] = []
        event_teams_by_team[num].append(dict(r))

    # 5. Map historical names across event_teams, scores, awards, and schedules
    historical_names_by_team = {}
    for tbl in ["event_teams", "scores", "awards", "schedules"]:
        cur.execute(f"SELECT event_id, team_number, team_name FROM {tbl} WHERE team_number IS NOT NULL AND team_name IS NOT NULL")
        for r in cur.fetchall():
            num = r["team_number"]
            raw_name = (r["team_name"] or "").strip()
            if not raw_name:
                continue
            eid = r["event_id"]
            season = events_map.get(eid, {}).get("season", "")
            if num not in historical_names_by_team:
                historical_names_by_team[num] = {}
            if raw_name not in historical_names_by_team[num]:
                historical_names_by_team[num][raw_name] = set()
            if season:
                historical_names_by_team[num][raw_name].add(season)

    conn.close()
    return events_map, scores_by_team, awards_by_team, event_teams_by_team, historical_names_by_team


def build_team_history(team_num, current_name, events_map, scores_by_team, awards_by_team, event_teams_by_team, historical_names_by_team):
    sc_list = scores_by_team.get(team_num, [])
    aw_list = awards_by_team.get(team_num, [])
    et_list = event_teams_by_team.get(team_num, [])

    # Past names extraction
    curr_clean = (current_name or "").strip()
    team_history_names = historical_names_by_team.get(team_num, {})
    past_names_details = []
    past_names_list = []

    def get_latest_season(seasons_set):
        if not seasons_set:
            return ""
        return sorted(list(seasons_set), reverse=True)[0]

    for hname, seasons in sorted(team_history_names.items(), key=lambda item: get_latest_season(item[1]), reverse=True):
        if hname.lower() != curr_clean.lower():
            past_names_list.append(hname)
            past_names_details.append({
                "name": hname,
                "seasons": sorted(list(seasons), reverse=True)
            })

    has_history = bool(sc_list or aw_list or et_list)

    # Scores
    score_vals = [to_float(s["highest_score"]) for s in sc_list if to_float(s["highest_score"]) is not None]
    max_score = max(score_vals) if score_vals else None
    avg_score = round(sum(score_vals) / len(score_vals), 1) if score_vals else None

    ranks = [to_int(s["ranking"]) for s in sc_list if to_int(s["ranking"]) is not None and to_int(s["ranking"]) > 0]
    best_rank = min(ranks) if ranks else None

    # Events & Seasons
    event_ids = set([x["event_id"] for x in (sc_list + aw_list + et_list)])
    seasons = sorted(list(set([events_map[eid]["season"] for eid in event_ids if eid in events_map and events_map[eid]["season"]])))

    adv_count = sum(1 for x in et_list if x.get("advancing_to_next_level") == 1)
    has_champ = any("championship" in (events_map.get(eid, {}).get("name") or "").lower() for eid in event_ids)

    # Clean detailed awards list
    awards_details = []
    for a in aw_list:
        eid = a["event_id"]
        ev = events_map.get(eid, {})
        awards_details.append({
            "name": a["award_name"] or a["display_name"],
            "category": a["category"],
            "season": ev.get("season", ""),
            "event_name": ev.get("name", ""),
            "place": a.get("place_number")
        })

    # Event details summary
    event_history_details = []
    for eid in sorted(list(event_ids)):
        ev = events_map.get(eid, {})
        # Find score for this event
        ev_score = next((s["highest_score"] for s in sc_list if s["event_id"] == eid), None)
        ev_rank = next((s["ranking"] for s in sc_list if s["event_id"] == eid), None)
        ev_adv = any(x.get("advancing_to_next_level") == 1 for x in et_list if x["event_id"] == eid)
        ev_awards = [a["award_name"] for a in aw_list if a["event_id"] == eid]
        event_history_details.append({
            "event_id": eid,
            "event_name": ev.get("name", ""),
            "season": ev.get("season", ""),
            "date": (ev.get("start_time") or "")[:10],
            "highest_score": to_float(ev_score),
            "ranking": to_int(ev_rank),
            "advanced": ev_adv,
            "awards": ev_awards
        })
    # Sort events by date desc
    event_history_details.sort(key=lambda x: x["date"], reverse=True)

    # Classifications
    if not has_history:
        exp_tier = "Rookie (新队伍)"
        score_tier = "暂无历史成绩"
    elif len(seasons) >= 2 or has_champ or adv_count >= 2:
        exp_tier = "Veteran (老牌强队)"
    elif len(seasons) == 1 or len(event_ids) >= 1:
        exp_tier = "Experienced (有参赛经验)"
    else:
        exp_tier = "Rookie (新队伍)"

    if max_score is None:
        score_tier = "暂无得分记录"
    elif max_score >= 500:
        score_tier = "500+ (争冠顶尖)"
    elif max_score >= 400:
        score_tier = "400-499 (一档强队)"
    elif max_score >= 300:
        score_tier = "300-399 (中坚晋级)"
    else:
        score_tier = "<300 (入门发展)"

    # Build by_season breakdown for 2025, 2024, 2023
    seasons_order = [
        ("2025", "2025-26", "UNEARTHED"),
        ("2024", "2024-25", "SUBMERGED"),
        ("2023", "2023-24", "MASTERPIECE")
    ]
    by_season = {}
    for yr_prefix, yr_short, yr_theme in seasons_order:
        s_events = [ev for ev in event_history_details if ev.get("season", "").startswith(yr_prefix)]
        qt_ev = next((ev for ev in s_events if "champ" not in ev.get("event_name", "").lower()), None)
        champ_ev = next((ev for ev in s_events if "champ" in ev.get("event_name", "").lower()), None)
        by_season[yr_prefix] = {
            "season_key": yr_prefix,
            "season_label": yr_short,
            "theme": yr_theme,
            "has_participated": bool(s_events),
            "qt": qt_ev,
            "champ": champ_ev
        }

    return {
        "has_history": has_history,
        "past_names": past_names_list,
        "past_names_details": past_names_details,
        "events_count": len(event_ids),
        "seasons_count": len(seasons),
        "seasons": seasons,
        "max_score": max_score,
        "avg_score": avg_score,
        "best_ranking": best_rank,
        "score_records_count": len(sc_list),
        "awards_count": len(aw_list),
        "awards": awards_details,
        "advancements_count": adv_count,
        "has_championship": has_champ,
        "experience_tier": exp_tier,
        "score_tier": score_tier,
        "events": event_history_details,
        "recent_event": event_history_details[0] if event_history_details else None,
        "by_season": by_season
    }


def update_database_and_files():
    logger.info("Extracting historical data from SQLite...")
    events_map, scores_by_team, awards_by_team, event_teams_by_team, historical_names_by_team = extract_history_data()

    logger.info("Loading public teams from %s...", RAW_TEAMS_JSON)
    with open(RAW_TEAMS_JSON, "r", encoding="utf-8") as f:
        teams = json.load(f)

    # Attach history to each team
    matched_teams_count = 0
    scored_teams_count = 0
    awarded_teams_count = 0
    past_names_teams_count = 0

    for t in teams:
        num = t.get("number")
        name = t.get("name")
        hist = build_team_history(num, name, events_map, scores_by_team, awards_by_team, event_teams_by_team, historical_names_by_team)
        t["history"] = hist
        t["past_names"] = hist["past_names"]
        if hist["has_history"]:
            matched_teams_count += 1
        if hist["max_score"] is not None:
            scored_teams_count += 1
        if hist["awards_count"] > 0:
            awarded_teams_count += 1
        if hist["past_names"]:
            past_names_teams_count += 1

    logger.info("Matched %d/%d teams with historical records (%d scored, %d awarded, %d with past names).",
                matched_teams_count, len(teams), scored_teams_count, awarded_teams_count, past_names_teams_count)

    # 1. Save updated JSON
    with open(RAW_TEAMS_JSON, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
    logger.info("Updated %s with history objects.", RAW_TEAMS_JSON)

    # 2. Update SQLite table public_teams
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add columns if not exist
    cols_to_add = [
        ("has_history", "INTEGER DEFAULT 0"),
        ("history_past_names", "TEXT"),
        ("history_events_count", "INTEGER DEFAULT 0"),
        ("history_seasons_count", "INTEGER DEFAULT 0"),
        ("history_max_score", "REAL"),
        ("history_avg_score", "REAL"),
        ("history_best_ranking", "INTEGER"),
        ("history_awards_count", "INTEGER DEFAULT 0"),
        ("history_advancements_count", "INTEGER DEFAULT 0"),
        ("history_has_championship", "INTEGER DEFAULT 0"),
        ("history_experience_tier", "TEXT"),
        ("history_score_tier", "TEXT"),
        ("history_json", "TEXT"),
    ]

    cur.execute("PRAGMA table_info(public_teams)")
    existing_cols = set(col[1] for col in cur.fetchall())

    for col_name, col_type in cols_to_add:
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE public_teams ADD COLUMN {col_name} {col_type}")

    # Update rows in public_teams
    for t in teams:
        h = t["history"]
        cur.execute("""
            UPDATE public_teams SET
                has_history = ?,
                history_past_names = ?,
                history_events_count = ?,
                history_seasons_count = ?,
                history_max_score = ?,
                history_avg_score = ?,
                history_best_ranking = ?,
                history_awards_count = ?,
                history_advancements_count = ?,
                history_has_championship = ?,
                history_experience_tier = ?,
                history_score_tier = ?,
                history_json = ?
            WHERE number = ?
        """, (
            1 if h["has_history"] else 0,
            json.dumps(h["past_names"], ensure_ascii=False) if h["past_names"] else None,
            h["events_count"],
            h["seasons_count"],
            h["max_score"],
            h["avg_score"],
            h["best_ranking"],
            h["awards_count"],
            h["advancements_count"],
            1 if h["has_championship"] else 0,
            h["experience_tier"],
            h["score_tier"],
            json.dumps(h, ensure_ascii=False),
            t["number"]
        ))
    conn.commit()
    conn.close()
    logger.info("Updated SQLite table 'public_teams' with historical performance columns.")

    # 3. Update CSV
    update_csv(teams)

    return teams


def update_csv(teams):
    if not CSV_PATH.exists():
        return

    # Read existing CSV rows
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Build map of history by number
    hist_map = {t["number"]: t["history"] for t in teams}

    # Extend rows with history
    for r in rows:
        num = to_int(r.get("number"))
        h = hist_map.get(num, {})
        r["has_history"] = h.get("has_history", False)
        r["history_past_names"] = " / ".join(h.get("past_names", []))
        r["history_events_count"] = h.get("events_count", 0)
        r["history_seasons_count"] = h.get("seasons_count", 0)
        r["history_max_score"] = h.get("max_score", "")
        r["history_avg_score"] = h.get("avg_score", "")
        r["history_best_ranking"] = h.get("best_ranking", "")
        r["history_awards_count"] = h.get("awards_count", 0)
        r["history_advancements_count"] = h.get("advancements_count", 0)
        r["history_has_championship"] = h.get("has_championship", False)
        r["history_experience_tier"] = h.get("experience_tier", "")
        r["history_score_tier"] = h.get("score_tier", "")

    new_fieldnames = list(rows[0].keys())
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Updated CSV %s with historical performance columns (%d rows).", CSV_PATH, len(rows))


def main():
    update_database_and_files()
    logger.info("Historical data integration completed successfully!")


if __name__ == "__main__":
    main()
