#!/usr/bin/env python3
"""
Statistical Analyzer for NorCal FLL Event Participating Teams.
Enriches event teams with full compliance, past performance, past names,
and generates deep tournament competitor intelligence.

Outputs:
- data/event_teams_analysis.json
- web/event_teams_data.js
- EVENT_TEAMS_ANALYSIS_REPORT.md
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("analyze_event_teams")

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "mylumi.db"
PUBLIC_TEAMS_JSON = RAW_DIR / "public_teams.json"
EVENT_TEAMS_JSON = RAW_DIR / "event_teams_all.json"
WEB_DIR = ROOT_DIR / "web"


def get_team_region(city):
    if not city:
        return "未知 (Unknown)"
    c = city.strip().lower()
    east_bay = {"oakland", "berkeley", "fremont", "alameda", "newark", "union city", "hayward", "san leandro", "dublin", "pleasanton", "livermore", "san ramon", "danville", "castro valley", "albany", "piedmont", "walnut creek", "concord"}
    south_bay = {"san jose", "sunnyvale", "santa clara", "cupertino", "milpitas", "campbell", "saratoga", "los gatos", "morgan hill", "gilroy"}
    peninsula = {"san mateo", "palo alto", "mountain view", "redwood city", "menlo park", "foster city", "san carlos", "belmont", "burlingame", "hillsborough", "millbrae", "san bruno", "south san francisco", "daly city", "los altos", "los altos hills", "east palo alto", "pacifica", "half moon bay"}
    sf = {"san francisco", "sf"}
    north_bay = {"san rafael", "novato", "mill valley", "tiburon", "sausalito", "santa rosa", "petaluma", "napa", "vallejo", "fairfield", "vacaville", "benicia"}
    central_valley = {"sacramento", "elk grove", "folsom", "rancho cordova", "davis", "woodland", "roseville", "rocklin", "modesto", "stockton", "tracy", "manteca", "lodi", "turlock", "mountain house"}
    santa_cruz = {"santa cruz", "scotts valley", "watsonville", "aptos", "monterey", "salinas", "seaside", "marina", "carmel"}

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


def load_data():
    # 1. Load public teams map
    with open(PUBLIC_TEAMS_JSON, "r", encoding="utf-8") as f:
        teams_list = json.load(f)
    teams_map = {t["number"]: t for t in teams_list if t.get("number")}

    # Fallback to historical leaderboard if available
    hist_json = ROOT_DIR / "data" / "historical_leaderboard.json"
    if hist_json.exists():
        try:
            with open(hist_json, "r", encoding="utf-8") as f:
                hist_data = json.load(f)
            for ht in hist_data.get("leaderboard", []):
                num = ht.get("team_number")
                if num and num in teams_map:
                    if not teams_map[num].get("power_score"):
                        teams_map[num]["power_score"] = ht.get("power_score", 0.0)
                    if not teams_map[num].get("tier"):
                        teams_map[num]["tier"] = ht.get("tier", "Rookie (新队伍/待赛)")
        except Exception:
            pass

    # 2. Load events metadata from DB or raw json
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, season, program, venue_city, venue_name, capacity, total_registered, start_time, end_time, status_v2, website_uri
        FROM events
        WHERE season LIKE '%2026%' OR id >= 300
        ORDER BY id
    """)
    events_meta = {r["id"]: dict(r) for r in cur.fetchall()}
    conn.close()

    # 3. Load crawled event teams
    with open(EVENT_TEAMS_JSON, "r", encoding="utf-8") as f:
        event_teams_raw = json.load(f)

    return teams_map, events_meta, event_teams_raw


def analyze_single_event(eid, ev_info, teams_raw, teams_map):
    capacity = ev_info.get("capacity") or 18
    reg_items = teams_raw.get("teams", [])
    total_reg = len(reg_items)
    fill_rate = round((total_reg / capacity) * 100, 1) if capacity > 0 else 0
    spots_remaining = max(0, capacity - total_reg)

    enriched_teams = []
    ready_count = 0
    veteran_count = 0
    experienced_count = 0
    rookie_count = 0

    career_scores = []
    teams_with_awards = 0
    total_career_awards = 0
    teams_with_advancement = 0

    status_counts = {}
    city_counts = {}
    region_counts = {}
    org_counts = {}
    score_tier_counts = {
        "500+ (争冠顶尖)": 0,
        "400-499 (一档强队)": 0,
        "300-399 (中坚晋级)": 0,
        "<300 (入门发展)": 0,
        "暂无得分记录": 0
    }

    power_scores = []
    tier_s_count = 0
    tier_a_count = 0
    tier_b_count = 0
    tier_c_count = 0
    tier_rookie_count = 0

    for item in reg_items:
        raw_t = item.get("team") or {}
        num = raw_t.get("number")
        full_t = teams_map.get(num, {})

        # Inherit full profile if exists, else fallback to raw
        name = full_t.get("name") or raw_t.get("name") or f"Team #{num}"
        city = full_t.get("city") or raw_t.get("city") or "Unknown"
        org_name = full_t.get("org_name") or raw_t.get("org_name") or "Family/Community"
        status_v2 = full_t.get("status_v2") or "unknown"
        status_quickview = full_t.get("status_quickview") or {}
        history = full_t.get("history") or {}
        past_names = full_t.get("past_names") or history.get("past_names") or []
        past_names_details = history.get("past_names_details") or []

        p_score = full_t.get("power_score") or history.get("power_score") or 0.0
        t_tier = full_t.get("tier") or history.get("tier") or "Rookie (新队伍/待赛)"
        power_scores.append(p_score)
        if "Tier S" in t_tier:
            tier_s_count += 1
        elif "Tier A" in t_tier:
            tier_a_count += 1
        elif "Tier B" in t_tier:
            tier_b_count += 1
        elif "Tier C" in t_tier:
            tier_c_count += 1
        else:
            tier_rookie_count += 1

        is_ready = status_v2 == "good"
        if is_ready:
            ready_count += 1
        status_counts[status_v2] = status_counts.get(status_v2, 0) + 1

        reg_name = get_team_region(city)
        region_counts[reg_name] = region_counts.get(reg_name, 0) + 1
        city_counts[city] = city_counts.get(city, 0) + 1
        org_counts[org_name] = org_counts.get(org_name, 0) + 1

        # History metrics
        exp_tier = history.get("experience_tier", "Rookie (新队伍)")
        if "Veteran" in exp_tier:
            veteran_count += 1
        elif "Experienced" in exp_tier:
            experienced_count += 1
        else:
            rookie_count += 1

        max_sc = history.get("max_score")
        if max_sc is not None:
            career_scores.append(max_sc)
            if max_sc >= 500:
                score_tier_counts["500+ (争冠顶尖)"] += 1
            elif max_sc >= 400:
                score_tier_counts["400-499 (一档强队)"] += 1
            elif max_sc >= 300:
                score_tier_counts["300-399 (中坚晋级)"] += 1
            else:
                score_tier_counts["<300 (入门发展)"] += 1
        else:
            score_tier_counts["暂无得分记录"] += 1

        aw_cnt = history.get("awards_count", 0)
        if aw_cnt > 0:
            teams_with_awards += 1
            total_career_awards += aw_cnt

        if history.get("advancements_count", 0) > 0 or history.get("has_championship"):
            teams_with_advancement += 1

        enriched_team = {
            "number": num,
            "name": name,
            "city": city,
            "region": reg_name,
            "org_name": org_name,
            "status_v2": status_v2,
            "status_quickview": status_quickview,
            "past_names": past_names,
            "past_names_details": past_names_details,
            "history": history,
            "power_score": p_score,
            "tier": t_tier,
            "advancing_to_next_level": item.get("advancing_to_next_level", False),
            "advancing_wait_list": item.get("advancing_wait_list", False),
        }
        enriched_teams.append(enriched_team)

    # Sort registered teams by power_score desc, career max score desc, then by number
    enriched_teams.sort(key=lambda t: (
        t.get("power_score") or 0.0,
        t["history"].get("max_score") or -1,
        t["history"].get("awards_count") or 0,
        -t["number"]
    ), reverse=True)

    top_career_score = max(career_scores) if career_scores else None
    top_scoring_team = next((t for t in enriched_teams if t["history"].get("max_score") == top_career_score), None) if top_career_score is not None else None
    avg_career_score = round(sum(career_scores) / len(career_scores), 1) if career_scores else None
    avg_power_score = round(sum(power_scores) / len(power_scores), 1) if power_scores else 0.0

    # Format distributions
    cities_dist = sorted([{"city": c, "count": cnt, "pct": round(cnt / total_reg * 100, 1)} for c, cnt in city_counts.items()], key=lambda x: x["count"], reverse=True)
    regions_dist = sorted([{"region": r, "count": cnt, "pct": round(cnt / total_reg * 100, 1)} for r, cnt in region_counts.items()], key=lambda x: x["count"], reverse=True)
    orgs_dist = sorted([{"org": o, "count": cnt, "pct": round(cnt / total_reg * 100, 1)} for o, cnt in org_counts.items()], key=lambda x: x["count"], reverse=True)

    return {
        "event_id": eid,
        "name": ev_info.get("name", f"Event #{eid}"),
        "season": ev_info.get("season", "2026 - BIOGLOW (Challenge)"),
        "program": ev_info.get("program", "FIRST LEGO League: Challenge"),
        "venue_city": ev_info.get("venue_city") or "TBD",
        "venue_name": ev_info.get("venue_name") or "TBD",
        "start_time": (ev_info.get("start_time") or "")[:10],
        "capacity": capacity,
        "total_registered": total_reg,
        "fill_rate": fill_rate,
        "spots_remaining": spots_remaining,
        "ready_count": ready_count,
        "ready_pct": round(ready_count / total_reg * 100, 1) if total_reg > 0 else 0,
        "pending_count": total_reg - ready_count,
        "status_counts": status_counts,
        "experience": {
            "veteran_count": veteran_count,
            "veteran_pct": round(veteran_count / total_reg * 100, 1) if total_reg > 0 else 0,
            "experienced_count": experienced_count,
            "experienced_pct": round(experienced_count / total_reg * 100, 1) if total_reg > 0 else 0,
            "rookie_count": rookie_count,
            "rookie_pct": round(rookie_count / total_reg * 100, 1) if total_reg > 0 else 0,
        },
        "strength": {
            "top_career_score": top_career_score,
            "top_team_number": top_scoring_team["number"] if top_scoring_team else None,
            "top_team_name": top_scoring_team["name"] if top_scoring_team else None,
            "avg_career_score": avg_career_score,
            "avg_power_score": avg_power_score,
            "tier_s_count": tier_s_count,
            "tier_a_count": tier_a_count,
            "tier_b_count": tier_b_count,
            "tier_c_count": tier_c_count,
            "tier_rookie_count": tier_rookie_count,
            "teams_with_awards": teams_with_awards,
            "total_career_awards": total_career_awards,
            "teams_with_advancement": teams_with_advancement,
            "score_tier_counts": score_tier_counts
        },
        "cities_dist": cities_dist,
        "regions_dist": regions_dist,
        "top_orgs": orgs_dist[:8],
        "teams": enriched_teams
    }


def generate_full_analysis():
    logger.info("Loading public teams, events and crawled event teams...")
    teams_map, events_meta, event_teams_raw = load_data()

    event_analyses = []
    total_capacity = 0
    total_registered = 0
    all_ready_count = 0
    all_veteran_count = 0
    highest_overall_score = -1
    highest_scoring_team = None

    for eid_str, raw_data in sorted(event_teams_raw.items(), key=lambda x: int(x[0])):
        eid = int(eid_str)
        ev_info = events_meta.get(eid, {})
        ev_analysis = analyze_single_event(eid, ev_info, raw_data, teams_map)
        event_analyses.append(ev_analysis)

        total_capacity += ev_analysis["capacity"]
        total_registered += ev_analysis["total_registered"]
        all_ready_count += ev_analysis["ready_count"]
        all_veteran_count += ev_analysis["experience"]["veteran_count"]

        top_s = ev_analysis["strength"]["top_career_score"]
        if top_s is not None and top_s > highest_overall_score:
            highest_overall_score = top_s
            highest_scoring_team = {
                "event_id": eid,
                "event_name": ev_analysis["name"],
                "team_number": ev_analysis["strength"]["top_team_number"],
                "team_name": ev_analysis["strength"]["top_team_name"],
                "score": top_s
            }

    overall_summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "total_events": len(event_analyses),
        "total_capacity": total_capacity,
        "total_registered": total_registered,
        "overall_fill_rate": round(total_registered / total_capacity * 100, 1) if total_capacity else 0,
        "total_spots_remaining": max(0, total_capacity - total_registered),
        "overall_ready_count": all_ready_count,
        "overall_ready_pct": round(all_ready_count / total_registered * 100, 1) if total_registered else 0,
        "overall_veteran_count": all_veteran_count,
        "overall_veteran_pct": round(all_veteran_count / total_registered * 100, 1) if total_registered else 0,
        "highest_overall_score": highest_overall_score if highest_overall_score >= 0 else None,
        "highest_scoring_team": highest_scoring_team,
        "events": event_analyses
    }

    # Save data/event_teams_analysis.json
    analysis_json_path = DATA_DIR / "event_teams_analysis.json"
    with open(analysis_json_path, "w", encoding="utf-8") as f:
        json.dump(overall_summary, f, ensure_ascii=False, indent=2)
    logger.info("Saved analysis JSON to %s.", analysis_json_path)

    # Save web/event_teams_data.js
    web_js_path = WEB_DIR / "event_teams_data.js"
    with open(web_js_path, "w", encoding="utf-8") as f:
        f.write("/* Auto-generated NorCal FLL Event Participating Teams Dataset */\n")
        f.write("window.EVENT_TEAMS_DATA = ")
        json.dump(overall_summary, f, ensure_ascii=False)
        f.write(";\n")
    logger.info("Saved web JS data to %s.", web_js_path)

    # Generate Markdown Report
    generate_markdown_report(overall_summary)

    return overall_summary


def generate_markdown_report(data):
    md_path = ROOT_DIR / "EVENT_TEAMS_ANALYSIS_REPORT.md"
    events = data["events"]

    lines = [
        "# NorCal FLL BIOGLOW 2026 · 每场比赛参赛队伍竞技与合规全景分析报告",
        "",
        f"> **生成时间**: {data.get('generated_at', datetime.now().strftime('%Y-%m-%d'))} | **涵盖分站赛**: {data['total_events']} 站 | **总报名队伍**: {data['total_registered']} / {data['total_capacity']} 席位 ({data['overall_fill_rate']}%)",
        "",
        "---",
        "",
        "## 一、 全部分站赛注册与竞技强度横向对比",
        "",
        "| ID | 比赛名称 | 日期 | 城市 | 席位 | 报名数 | 饱和度 | 老牌强队 | 生涯最高纪录 | 合规就绪率 |",
        "|---|---|---|---|---|---|---|---|---|---|"
    ]

    for ev in events:
        top_s_txt = f"{ev['strength']['top_career_score']} 分 (#{ev['strength']['top_team_number']})" if ev['strength']['top_career_score'] else "暂无得分"
        lines.append(
            f"| **#{ev['event_id']}** | {ev['name'][:35]}... | {ev['start_time']} | {ev['venue_city']} | {ev['capacity']} | **{ev['total_registered']}** | {ev['fill_rate']}% | {ev['experience']['veteran_count']}队 ({ev['experience']['veteran_pct']}%) | {top_s_txt} | {ev['ready_pct']}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 二、 各分站赛深度阵容分析",
        ""
    ])

    for ev in events:
        lines.append(f"### ⚔️ #{ev['event_id']}: {ev['name']}")
        lines.append(f"- **基本信息**: 📅 日期: {ev['start_time']} | 📍 场馆: {ev['venue_name']} ({ev['venue_city']})")
        lines.append(f"- **容量饱和**: 已报 **{ev['total_registered']} / {ev['capacity']}** 队 ({ev['fill_rate']}%) | 剩余席位: {ev['spots_remaining']}")
        lines.append(f"- **合规就绪**: ✅ 合规就绪 **{ev['ready_count']}** 队 ({ev['ready_pct']}%) | ⚠️ 审查中 **{ev['pending_count']}** 队")
        lines.append(f"- **梯队构成**: 🛡️ 老牌强队: {ev['experience']['veteran_count']} 队 | 🎖️ 有经验: {ev['experience']['experienced_count']} 队 | 🌱 新队伍: {ev['experience']['rookie_count']} 队")
        if ev['strength']['top_career_score']:
            lines.append(f"- **最强纪录**: ⚡ 历史最高分 **{ev['strength']['top_career_score']} 分** (由 #{ev['strength']['top_team_number']} {ev['strength']['top_team_name']} 保持) | 场均历史分: {ev['strength']['avg_career_score']} 分")
        lines.append(f"- **荣誉底蕴**: 🏆 曾获奖队伍 {ev['strength']['teams_with_awards']} 支 (累计斩获 {ev['strength']['total_career_awards']} 座大奖) | 🚀 曾晋级总决赛队伍: {ev['strength']['teams_with_advancement']} 支")
        
        # Team list preview
        lines.append("")
        lines.append("| 编号 | 队伍名称 | 曾用名 | 城市 | 梯队 | 生涯最高分 | 就绪状态 | 组织/学校 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for t in ev["teams"]:
            past_txt = ", ".join(t["past_names"]) if t["past_names"] else "-"
            sc_txt = f"{t['history'].get('max_score')}分" if t['history'].get('max_score') is not None else "-"
            lines.append(f"| #{t['number']} | {t['name']} | {past_txt} | {t['city']} | {t['history'].get('experience_tier', '-')} | {sc_txt} | {t['status_v2']} | {t['org_name']} |")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Saved markdown report to %s.", md_path)


if __name__ == "__main__":
    generate_full_analysis()
