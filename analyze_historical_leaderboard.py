#!/usr/bin/env python3
"""
Comprehensive Historical Leaderboard & 2026 Registration Tracker for NorCal FLL.
================================================================================
Aggregates all historical performance across seasons (2023-2026), builds power
rankings, computes career statistics, awards, advancements, past aliases,
and tracks 2026 BIOGLOW registration status with a sharp focus on unregistered
powerhouse teams.

Outputs:
- data/historical_leaderboard.json
- web/leaderboard_data.js
- HISTORICAL_LEADERBOARD_REPORT.md
"""

import csv
import json
import logging
from pathlib import Path
import sqlite3
import statistics

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("historical_leaderboard")

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "mylumi.db"
WEB_DIR = ROOT_DIR / "web"
OUTPUT_JSON = DATA_DIR / "historical_leaderboard.json"
OUTPUT_JS = WEB_DIR / "leaderboard_data.js"
OUTPUT_MD = ROOT_DIR / "HISTORICAL_LEADERBOARD_REPORT.md"


def get_region(city: str) -> str:
    if not city:
        return "未知 (Unknown)"
    c = city.strip().lower()
    east_bay = {
        "oakland", "berkeley", "fremont", "alameda", "newark", "union city",
        "hayward", "san leandro", "dublin", "pleasanton", "livermore",
        "san ramon", "danville", "castro valley", "albany", "piedmont",
        "walnut creek", "concord"
    }
    south_bay = {
        "san jose", "sunnyvale", "santa clara", "cupertino", "milpitas",
        "campbell", "saratoga", "los gatos", "morgan hill", "gilroy"
    }
    peninsula = {
        "san mateo", "palo alto", "mountain view", "redwood city", "menlo park",
        "foster city", "san carlos", "belmont", "burlingame", "hillsborough",
        "millbrae", "san bruno", "south san francisco", "daly city", "los altos",
        "los altos hills", "east palo alto", "pacifica", "half moon bay"
    }
    sf = {"san francisco", "sf"}
    north_bay = {
        "san rafael", "novato", "mill valley", "tiburon", "sausalito",
        "santa rosa", "petaluma", "napa", "vallejo", "fairfield", "vacaville", "benicia"
    }
    central_valley = {
        "sacramento", "elk grove", "folsom", "rancho cordova", "davis",
        "woodland", "roseville", "rocklin", "modesto", "stockton", "tracy",
        "manteca", "lodi", "turlock", "mountain house"
    }
    santa_cruz = {
        "santa cruz", "scotts valley", "watsonville", "aptos", "monterey",
        "salinas", "seaside", "marina", "carmel"
    }

    if c in east_bay:
        return "东湾 (East Bay)"
    if c in south_bay:
        return "南湾 (South Bay)"
    if c in peninsula:
        return "半岛 (Peninsula)"
    if c in sf:
        return "旧金山 (San Francisco)"
    if c in central_valley:
        return "中央谷/萨克拉门托 (Central Valley)"
    if c in north_bay:
        return "北湾 (North Bay)"
    if c in santa_cruz:
        return "圣克鲁兹/蒙特雷 (Santa Cruz)"
    return "其他地区 (Other)"


def to_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def to_int(val):
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def calculate_power_score(career_max_score, career_avg_score, champions_count,
                          core_awards_count, other_awards_count,
                          advancements_count, has_championship, seasons_count, events_count):
    """
    Computes a comprehensive power score (0 to 100) reflecting a team's
    historical competitive pedigree in NorCal FLL.
    """
    # 1. Peak robot performance (Max Score up to 35 pts)
    # Benchmark: 540 is historic max
    score_component = 0.0
    if career_max_score:
        score_component = min(35.0, (career_max_score / 540.0) * 35.0)

    # 2. Consistency (Avg Score up to 15 pts)
    avg_component = 0.0
    if career_avg_score:
        avg_component = min(15.0, (career_avg_score / 450.0) * 15.0)

    # 3. Champions Award honors (up to 25 pts, each championship is 12.5 pts)
    champ_component = min(25.0, champions_count * 12.5)

    # 4. Core Awards & other awards (up to 12 pts)
    award_component = min(12.0, (core_awards_count * 3.5) + (other_awards_count * 1.0))

    # 5. Advancements & Championship presence (up to 10 pts)
    adv_component = min(8.0, advancements_count * 3.0)
    if has_championship:
        adv_component = min(10.0, adv_component + 2.0)

    # 6. Experience & longevity (up to 3 pts)
    exp_component = min(3.0, (seasons_count * 0.8) + (events_count * 0.3))

    total = round(score_component + avg_component + champ_component + award_component + adv_component + exp_component, 1)
    return min(100.0, total)


def assign_tier(power_score, career_max_score, champions_count, advancements_count, seasons_count):
    """
    Assigns tier based on both multi-dimensional power score and distinctive accolades.
    """
    if power_score >= 65 or champions_count >= 2 or (champions_count >= 1 and (career_max_score or 0) >= 420) or ((career_max_score or 0) >= 500 and advancements_count >= 2):
        return "Tier S (霸主/夺冠热门)"
    if power_score >= 45 or champions_count >= 1 or (career_max_score or 0) >= 380 or advancements_count >= 2 or ((career_max_score or 0) >= 320 and seasons_count >= 2):
        return "Tier A (种子强队/劲旅)"
    if power_score >= 25 or (career_max_score or 0) >= 240 or seasons_count >= 2 or advancements_count >= 1:
        return "Tier B (中坚力量/资深)"
    if power_score > 0 or career_max_score is not None:
        return "Tier C (成长中队伍/新锐)"
    return "Rookie (新队伍/待赛)"


def main():
    logger.info("Connecting to database: %s", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Load all events metadata
    cur.execute("""
        SELECT id, name, season, program, venue_city, venue_name, capacity, total_registered, start_time, end_time, status_v2, website_uri
        FROM events
    """)
    events_map = {r["id"]: dict(r) for r in cur.fetchall()}
    logger.info("Loaded %d events metadata.", len(events_map))

    # 2. Identify 2026 BIOGLOW events and registrations
    cur.execute("""
        SELECT et.event_id, et.team_number, et.team_name, e.name as event_name, e.venue_city, e.start_time, e.venue_name
        FROM event_teams et
        JOIN events e ON et.event_id = e.id
        WHERE e.season LIKE '%2026%' OR e.id >= 300
    """)
    reg_2026_rows = cur.fetchall()
    reg_2026_by_team = {}
    for r in reg_2026_rows:
        num = r["team_number"]
        if num not in reg_2026_by_team:
            reg_2026_by_team[num] = []
        reg_2026_by_team[num].append({
            "event_id": r["event_id"],
            "event_name": r["event_name"],
            "city": r["venue_city"],
            "venue_name": r["venue_name"],
            "date": r["start_time"][:10] if r["start_time"] else ""
        })
    logger.info("Found %d unique teams registered in 2026 BIOGLOW season.", len(reg_2026_by_team))

    # 3. Load public teams catalog
    cur.execute("""
        SELECT number, name, city, org_name, status_v2, coaches_count, screening_good,
               fingerprinting_good, coaches_good, roster_good, roster_count, agreements_good, program_label
        FROM public_teams
    """)
    public_teams_map = {r["number"]: dict(r) for r in cur.fetchall()}
    logger.info("Loaded %d public teams from database.", len(public_teams_map))

    # 4. Load all scores by team
    cur.execute("""
        SELECT s.event_id, s.team_number, s.team_name, s.highest_score, s.round_1, s.round_2, s.round_3, s.round_4, s.ranking,
               e.season, e.name as event_name, e.start_time
        FROM scores s
        JOIN events e ON s.event_id = e.id
        WHERE s.team_number IS NOT NULL
        ORDER BY e.start_time ASC
    """)
    scores_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in scores_by_team:
            scores_by_team[num] = []
        scores_by_team[num].append(dict(r))

    # 5. Load all awards by team
    cur.execute("""
        SELECT a.event_id, a.team_number, a.team_name, a.award_name, a.display_name, a.category, a.place_number,
               a.city, a.team_org, e.season, e.name as event_name, e.start_time
        FROM awards a
        JOIN events e ON a.event_id = e.id
        WHERE a.team_number IS NOT NULL
        ORDER BY e.start_time ASC
    """)
    awards_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in awards_by_team:
            awards_by_team[num] = []
        awards_by_team[num].append(dict(r))

    # 6. Load all event_teams (to detect participation, advancement, city, org)
    cur.execute("""
        SELECT et.event_id, et.team_number, et.team_name, et.city, et.org_name,
               et.advancing_to_next_level, et.advancing_wait_list,
               e.season, e.name as event_name, e.start_time
        FROM event_teams et
        JOIN events e ON et.event_id = e.id
        WHERE et.team_number IS NOT NULL
        ORDER BY e.start_time ASC
    """)
    event_teams_by_team = {}
    for r in cur.fetchall():
        num = r["team_number"]
        if num not in event_teams_by_team:
            event_teams_by_team[num] = []
        event_teams_by_team[num].append(dict(r))

    # 7. Collect all unique team numbers across ALL sources
    all_team_numbers = set()
    all_team_numbers.update(scores_by_team.keys())
    all_team_numbers.update(awards_by_team.keys())
    all_team_numbers.update(event_teams_by_team.keys())
    all_team_numbers.update(public_teams_map.keys())
    all_team_numbers.update(reg_2026_by_team.keys())
    all_team_numbers = sorted(list(all_team_numbers))
    logger.info("Total unique teams aggregated across entire history: %d", len(all_team_numbers))

    # 8. Build detailed record for each team
    teams_leaderboard = []

    for num in all_team_numbers:
        pub_info = public_teams_map.get(num, {})
        sc_list = scores_by_team.get(num, [])
        aw_list = awards_by_team.get(num, [])
        et_list = event_teams_by_team.get(num, [])
        reg_2026 = reg_2026_by_team.get(num, [])

        # Determine best representative team name
        # 1. From public_teams (latest official 2026 name)
        # 2. From latest score or event_team
        current_name = pub_info.get("name")
        if not current_name:
            # find latest from scores or event_teams
            all_records = sc_list + et_list + aw_list
            if all_records:
                # sorted by event start_time
                valid_named = [r for r in all_records if r.get("team_name") and r["team_name"].strip()]
                if valid_named:
                    current_name = valid_named[-1]["team_name"].strip()
        if not current_name:
            current_name = f"Team {num}"

        # Collect past names and history aliases
        names_seasons = {}
        for r in (sc_list + et_list + aw_list):
            rname = (r.get("team_name") or "").strip()
            sname = r.get("season") or ""
            if rname:
                if rname not in names_seasons:
                    names_seasons[rname] = set()
                if sname:
                    names_seasons[rname].add(sname[:4])

        past_names = []
        for name_str, seasons_set in names_seasons.items():
            if name_str.lower() != current_name.lower():
                past_names.append({
                    "name": name_str,
                    "seasons": sorted(list(seasons_set))
                })

        # City & Org resolution cascade
        city = pub_info.get("city")
        if not city:
            # check latest valid city in event_teams
            for et in reversed(et_list):
                if et.get("city") and et["city"].strip():
                    city = et["city"].strip()
                    break
        if not city:
            # check awards
            for aw in reversed(aw_list):
                if aw.get("city") and aw["city"].strip():
                    city = aw["city"].strip()
                    break
        if not city:
            city = "未知"
        region = get_region(city)

        org_name = pub_info.get("org_name")
        if not org_name:
            for et in reversed(et_list):
                if et.get("org_name") and et["org_name"].strip():
                    org_name = et["org_name"].strip()
                    break
        if not org_name:
            for aw in reversed(aw_list):
                if aw.get("team_org") and aw["team_org"].strip():
                    org_name = aw["team_org"].strip()
                    break
        if not org_name:
            org_name = "Family/Community / School"

        # Calculate scores
        highest_score_vals = [to_float(s["highest_score"]) for s in sc_list if to_float(s["highest_score"]) is not None]
        career_max_score = max(highest_score_vals) if highest_score_vals else None
        career_avg_score = round(statistics.mean(highest_score_vals), 1) if highest_score_vals else None

        # Best rank
        ranks = [to_int(s["ranking"]) for s in sc_list if to_int(s["ranking"]) is not None and to_int(s["ranking"]) > 0]
        best_ranking = min(ranks) if ranks else None

        # Seasons played
        event_ids = set([x["event_id"] for x in (sc_list + aw_list + et_list)])
        seasons_set = set()
        season_max_scores = {}
        for eid in event_ids:
            ev = events_map.get(eid)
            if ev and ev.get("season"):
                year_match = ev["season"][:4]
                seasons_set.add(ev["season"])

        for s in sc_list:
            ev = events_map.get(s["event_id"])
            if ev and ev.get("season"):
                syear = ev["season"][:4]
                val = to_float(s["highest_score"])
                if val:
                    season_max_scores[syear] = max(season_max_scores.get(syear, 0), val)

        seasons_played = sorted(list(seasons_set))
        seasons_count = len(seasons_played)
        events_count = len(event_ids)

        # Awards breakdown
        awards_count = len(aw_list)
        champions_awards = []
        core_awards = []
        other_awards = []

        for a in aw_list:
            aname = a.get("award_name") or ""
            ev_title = a.get("event_name") or ""
            sea = a.get("season") or ""
            aw_dict = {
                "award_name": aname,
                "display_name": a.get("display_name"),
                "category": a.get("category"),
                "place_number": a.get("place_number"),
                "season": sea,
                "event_name": ev_title,
                "date": a.get("start_time")[:10] if a.get("start_time") else ""
            }
            if "champion" in aname.lower():
                champions_awards.append(aw_dict)
            elif a.get("category") == "core":
                core_awards.append(aw_dict)
            else:
                other_awards.append(aw_dict)

        champions_count = len(champions_awards)
        core_awards_count = len(core_awards)
        other_awards_count = len(other_awards)

        # Advancements
        adv_records = [x for x in et_list if x.get("advancing_to_next_level") == 1]
        advancements_count = len(adv_records)
        has_championship = any("championship" in (events_map.get(eid, {}).get("name") or "").lower() for eid in event_ids)

        # 2026 Registration status
        is_registered_2026 = len(reg_2026) > 0
        in_public_teams = bool(pub_info)

        if is_registered_2026:
            status_code = "registered"
            status_label = "🟢 已报名 2026"
            reg_locs = [(r.get("city") or "TBD") + " (" + (r.get("date") or "TBD") + ")" for r in reg_2026]
            status_desc = f"已报名: {', '.join(reg_locs)}"
        elif in_public_teams:
            status_code = "unregistered_active"
            status_label = "🟡 在册未报名 (Active Unregistered)"
            status_desc = "在 2026 Public Teams 库中，但尚未锁定任何预选赛席位"
        else:
            status_code = "unregistered_historical"
            status_label = "🔴 往届未激活 (Historical Inactive)"
            status_desc = "往年参赛队伍，尚未在 2026 赛季名册中激活或报名"

        # Compliance summary if in public teams
        compliance_status = pub_info.get("status_v2") or "unknown"
        screening_good = bool(pub_info.get("screening_good"))
        fingerprinting_good = bool(pub_info.get("fingerprinting_good"))
        coaches_good = bool(pub_info.get("coaches_good"))
        roster_good = bool(pub_info.get("roster_good"))
        agreements_good = bool(pub_info.get("agreements_good"))

        # Power score & Tier
        power_score = calculate_power_score(
            career_max_score=career_max_score,
            career_avg_score=career_avg_score,
            champions_count=champions_count,
            core_awards_count=core_awards_count,
            other_awards_count=other_awards_count,
            advancements_count=advancements_count,
            has_championship=has_championship,
            seasons_count=seasons_count,
            events_count=events_count,
        )

        tier = assign_tier(
            power_score=power_score,
            career_max_score=career_max_score,
            champions_count=champions_count,
            advancements_count=advancements_count,
            seasons_count=seasons_count,
        )

        # Tags
        tags = []
        if champions_count > 0:
            tags.append(f"🏆 冠军奖得主 x{champions_count}")
        if (career_max_score or 0) >= 500:
            tags.append("⚡ 500+ 神级巅峰")
        elif (career_max_score or 0) >= 400:
            tags.append("⚡ 400+ 顶尖得分")
        if advancements_count > 0:
            tags.append(f"🚀 晋级总决赛 x{advancements_count}")
        if has_championship:
            tags.append("👑 曾战锦标赛")
        if seasons_count >= 3:
            tags.append("🛡️ 三朝元老队伍")

        team_obj = {
            "team_number": num,
            "team_name": current_name,
            "past_names": past_names,
            "city": city,
            "region": region,
            "org_name": org_name,
            "power_score": power_score,
            "tier": tier,
            "tags": tags,
            # Registration
            "is_registered_2026": is_registered_2026,
            "registered_events_2026": reg_2026,
            "in_public_teams": in_public_teams,
            "status_code": status_code,
            "status_label": status_label,
            "status_desc": status_desc,
            "compliance_status": compliance_status,
            "compliance_checks": {
                "screening": screening_good,
                "fingerprinting": fingerprinting_good,
                "coaches": coaches_good,
                "roster": roster_good,
                "agreements": agreements_good
            },
            "roster_count": to_int(pub_info.get("roster_count")),
            # Career Stats
            "career_max_score": career_max_score,
            "career_avg_score": career_avg_score,
            "season_max_scores": season_max_scores,
            "best_ranking": best_ranking,
            "seasons_count": seasons_count,
            "seasons_played": seasons_played,
            "events_count": events_count,
            "awards_count": awards_count,
            "champions_count": champions_count,
            "core_awards_count": core_awards_count,
            "advancements_count": advancements_count,
            "has_championship": has_championship,
            # Detailed history items
            "champions_awards": champions_awards,
            "awards_list": aw_list,
            "scores_list": [{
                "event_id": s["event_id"],
                "event_name": s["event_name"],
                "season": s["season"],
                "date": s["start_time"][:10] if s.get("start_time") else "",
                "highest_score": to_float(s["highest_score"]),
                "round_1": to_float(s["round_1"]),
                "round_2": to_float(s["round_2"]),
                "round_3": to_float(s["round_3"]),
                "round_4": to_float(s["round_4"]),
                "ranking": to_int(s["ranking"]),
            } for s in sc_list],
        }
        teams_leaderboard.append(team_obj)

    # 9. Sort by power_score DESC, career_max_score DESC, awards_count DESC
    teams_leaderboard.sort(key=lambda t: (
        t["power_score"],
        t["career_max_score"] or 0,
        t["champions_count"],
        t["awards_count"],
        t["advancements_count"]
    ), reverse=True)

    # Assign rank
    for idx, t in enumerate(teams_leaderboard, start=1):
        t["overall_rank"] = idx

    logger.info("Processed %d total teams in leaderboard.", len(teams_leaderboard))

    # 10. Compute Summary Statistics for Unregistered Powerhouses
    unregistered_teams = [t for t in teams_leaderboard if not t["is_registered_2026"]]
    registered_teams = [t for t in teams_leaderboard if t["is_registered_2026"]]

    unregistered_tier_s = [t for t in unregistered_teams if "Tier S" in t["tier"]]
    unregistered_tier_a = [t for t in unregistered_teams if "Tier A" in t["tier"]]
    unregistered_powerhouses = unregistered_tier_s + unregistered_tier_a

    unregistered_champions = [t for t in unregistered_teams if t["champions_count"] > 0]
    unregistered_500_plus = [t for t in unregistered_teams if (t["career_max_score"] or 0) >= 500]
    unregistered_400_plus = [t for t in unregistered_teams if (t["career_max_score"] or 0) >= 400]

    logger.info("Summary KPI Highlights:")
    logger.info("  Total Teams: %d", len(teams_leaderboard))
    logger.info("  2026 Registered: %d (%.1f%%)", len(registered_teams), len(registered_teams) / len(teams_leaderboard) * 100)
    logger.info("  2026 Unregistered: %d (%.1f%%)", len(unregistered_teams), len(unregistered_teams) / len(teams_leaderboard) * 100)
    logger.info("  Unregistered Tier S: %d teams", len(unregistered_tier_s))
    logger.info("  Unregistered Tier A: %d teams", len(unregistered_tier_a))
    logger.info("  Unregistered Powerhouses (S+A): %d teams", len(unregistered_powerhouses))
    logger.info("  Unregistered Champions Award Winners: %d teams", len(unregistered_champions))
    logger.info("  Unregistered 500+ Score Legends: %d teams", len(unregistered_500_plus))
    logger.info("  Unregistered 400+ Score High Performers: %d teams", len(unregistered_400_plus))

    # Regional analysis of unregistered powerhouses
    region_powerhouse_counts = {}
    for t in unregistered_powerhouses:
        reg = t["region"]
        region_powerhouse_counts[reg] = region_powerhouse_counts.get(reg, 0) + 1

    summary_data = {
        "generated_at": "2026-10-08",
        "total_teams": len(teams_leaderboard),
        "registered_2026_count": len(registered_teams),
        "unregistered_2026_count": len(unregistered_teams),
        "unregistered_tier_s_count": len(unregistered_tier_s),
        "unregistered_tier_a_count": len(unregistered_tier_a),
        "unregistered_powerhouses_count": len(unregistered_powerhouses),
        "unregistered_champions_count": len(unregistered_champions),
        "unregistered_500_plus_count": len(unregistered_500_plus),
        "unregistered_400_plus_count": len(unregistered_400_plus),
        "total_champions_teams": len([t for t in teams_leaderboard if t["champions_count"] > 0]),
        "total_tier_s_teams": len([t for t in teams_leaderboard if "Tier S" in t["tier"]]),
        "total_tier_a_teams": len([t for t in teams_leaderboard if "Tier A" in t["tier"]]),
        "region_powerhouse_distribution": region_powerhouse_counts,
    }

    # 11. Save historical_leaderboard.json
    export_payload = {
        "summary": summary_data,
        "teams": teams_leaderboard
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, ensure_ascii=False, indent=2)
    logger.info("Saved complete JSON dataset to %s", OUTPUT_JSON)

    # 12. Save web/leaderboard_data.js
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("/* Auto-generated historical leaderboard and registration tracking dataset */\n")
        f.write("window.LEADERBOARD_DATA = ")
        json.dump(export_payload, f, ensure_ascii=False)
        f.write(";\n")
    logger.info("Saved frontend JS dataset to %s", OUTPUT_JS)

    # 13. Generate comprehensive Markdown report
    generate_markdown_report(summary_data, unregistered_powerhouses, registered_teams, teams_leaderboard)
    conn.close()


def generate_markdown_report(summary, unregistered_powerhouses, registered_teams, all_teams):
    logger.info("Generating Markdown report: %s", OUTPUT_MD)

    lines = []
    lines.append("# NorCal FLL 历史全部队伍战力排行榜与 2026 赛季未报名强队洞察报告")
    lines.append("")
    lines.append(f"> **生成时间**: {summary['generated_at']} | **历史全量队伍**: {summary['total_teams']} 支 | **已报名**: {summary['registered_2026_count']} 支 | **未报名**: {summary['unregistered_2026_count']} 支")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 一、 核心战况速览：未报名强队雷达预警")
    lines.append("")
    lines.append(f"- 🚨 **未报名顶尖强队总数**: **{summary['unregistered_powerhouses_count']} 支** (Tier S 霸主 **{summary['unregistered_tier_s_count']}** 支 + Tier A 劲旅 **{summary['unregistered_tier_a_count']}** 支)")
    lines.append(f"- 🏆 **未报名冠军大奖 (Champion's Award) 得主**: **{summary['unregistered_champions_count']} 支** (占历史所有冠军队伍的 **{round(summary['unregistered_champions_count'] / summary['total_champions_teams'] * 100, 1)}%**！)")
    lines.append(f"- ⚡ **未报名 500+ 神级巅峰高分队伍**: **{summary['unregistered_500_plus_count']} 支**")
    lines.append(f"- ⚡ **未报名 400+ 顶尖得分队伍**: **{summary['unregistered_400_plus_count']} 支**")
    lines.append(f"- 📈 **2026 赛季席位现状**: 14 场分站赛共 240 个席位，目前已报名 119 席，剩余约 121 个席位；**大量传统豪门尚未出手，预选赛名额极具潜在竞争风暴！**")
    lines.append("")
    lines.append("### 区域未报名强队分布")
    lines.append("")
    lines.append("| 区域 | 未报名 Tier S/A 强队数 | 说明 |")
    lines.append("|---|---|---|")
    for reg, cnt in sorted(summary["region_powerhouse_distribution"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| **{reg}** | **{cnt} 队** | 传统机器人俱乐部与名校聚集地 |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 二、 重点未报名顶级强队 (Tier S 霸主与夺冠热门)")
    lines.append("")
    lines.append("以下是生涯战绩卓越、曾斩获冠军大奖或创下 500+ 神级高分、但**截至目前尚未在 2026 BIOGLOW 赛季报名**的顶尖豪门：")
    lines.append("")
    lines.append("| 战力排名 | 队号 | 队名 | 曾用名 | 城市 | 生涯最高分 | 冠军奖 | 核心大奖 | 晋级总决赛 | 参赛赛季 | 战力指数 | 2026名册状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")

    tier_s_unreg = [t for t in unregistered_powerhouses if "Tier S" in t["tier"]]
    for t in tier_s_unreg:
        past_str = ", ".join([p["name"] for p in t["past_names"]]) if t["past_names"] else "-"
        status_disp = "已在2026名册(待选站)" if t["in_public_teams"] else "往届老牌未激活"
        score_disp = f"{t['career_max_score']}分" if t['career_max_score'] else "-"
        lines.append(
            f"| #{t['overall_rank']} | **#{t['team_number']}** | {t['team_name']} | {past_str} | {t['city']} | "
            f"**{score_disp}** | 🏆 x{t['champions_count']} | 🎖️ x{t['core_awards_count']} | 🚀 x{t['advancements_count']} | "
            f"{t['seasons_count']}届 | **{t['power_score']}** | {status_disp} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 三、 重点未报名种子战队 (Tier A 劲旅)")
    lines.append("")
    lines.append("以下是多次晋级总决赛、获得过技术大奖且高分在 350+ 分以上、但尚未报名的种子队伍（精选前 25 支）：")
    lines.append("")
    lines.append("| 战力排名 | 队号 | 队名 | 曾用名 | 城市 | 生涯最高分 | 核心大奖 | 晋级总决赛 | 参赛赛季 | 战力指数 | 2026名册状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

    tier_a_unreg = [t for t in unregistered_powerhouses if "Tier A" in t["tier"]][:25]
    for t in tier_a_unreg:
        past_str = ", ".join([p["name"] for p in t["past_names"]]) if t["past_names"] else "-"
        status_disp = "已在2026名册(待选站)" if t["in_public_teams"] else "往届老牌未激活"
        score_disp = f"{t['career_max_score']}分" if t['career_max_score'] else "-"
        lines.append(
            f"| #{t['overall_rank']} | **#{t['team_number']}** | {t['team_name']} | {past_str} | {t['city']} | "
            f"**{score_disp}** | 🎖️ x{t['core_awards_count']} | 🚀 x{t['advancements_count']} | "
            f"{t['seasons_count']}届 | **{t['power_score']}** | {status_disp} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 四、 历史最高得分 500+ 分俱乐部与未报名情况")
    lines.append("")
    lines.append("| 队号 | 队名 | 生涯最高分 | 创造赛季 | 冠军奖数 | 2026 报名状态 |")
    lines.append("|---|---|---|---|---|---|")
    club_500 = sorted([t for t in all_teams if (t["career_max_score"] or 0) >= 500], key=lambda x: x["career_max_score"], reverse=True)
    for t in club_500:
        reg_str = f"🟢 已报 #{t['registered_events_2026'][0]['event_id']}" if t["is_registered_2026"] else "🔴 **尚未报名**"
        lines.append(f"| **#{t['team_number']}** | {t['team_name']} | **{t['career_max_score']} 分** | {', '.join(t['seasons_played'])} | 🏆 x{t['champions_count']} | {reg_str} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 五、 2026 赛季已报名的顶尖战队代表 (对决风向标)")
    lines.append("")
    lines.append("| 战力排名 | 队号 | 队名 | 城市 | 生涯最高分 | 梯队 | 2026 已报场次 |")
    lines.append("|---|---|---|---|---|---|---|")
    top_registered = sorted(registered_teams, key=lambda x: x["power_score"], reverse=True)[:15]
    for t in top_registered:
        ev_str = ", ".join([f"#{r['event_id']} {r['city']}" for r in t["registered_events_2026"]])
        lines.append(f"| #{t['overall_rank']} | **#{t['team_number']}** | {t['team_name']} | {t['city']} | **{t['career_max_score']}分** | {t['tier']} | {ev_str} |")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Markdown report successfully generated!")


if __name__ == "__main__":
    main()
