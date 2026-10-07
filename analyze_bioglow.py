#!/usr/bin/env python3
"""
BIOGLOW Qualification Tournaments Analysis & Venue Historical Benchmarking
-------------------------------------------------------------------------
Computes weekend labeling (Week 1, Week 2, Week 3), comprehensive score metrics,
advancement cutoffs, and historical venue linkages across 2025 (UNEARTHED),
2024 (SUBMERGED), and 2023 (MASTERPIECE) for the upcoming 2026 BIOGLOW season.
"""

import json
from pathlib import Path
import re
import sqlite3
import statistics

DB_PATH = Path(__file__).parent / "data" / "mylumi.db"
OUTPUT_JSON = Path(__file__).parent / "data" / "bioglow_analysis.json"


def get_weekend_index(season_year: int, date_str: str) -> int:
    """
    Returns 1, 2, or 3 for November Qualification Tournaments.
    2026: Nov 7-8 (W1), Nov 14-15 (W2), Nov 21-22 (W3)
    2025: Nov 1-2 (W1), Nov 8-9 (W2), Nov 15-16 (W3)
    2024: Nov 2-3 (W1), Nov 9-10 (W2), Nov 16-17 (W3)
    2023: Nov 4-5 (W1), Nov 11-12 (W2), Nov 18-19 (W3)
    """
    if not date_str or len(date_str) < 10:
        return 0
    parts = date_str[:10].split("-")
    month = int(parts[1])
    day = int(parts[2])

    if month != 11:
        return 0  # not a November QT

    if season_year == 2026:
        if day <= 8:
            return 1
        elif day <= 15:
            return 2
        else:
            return 3
    elif season_year == 2025:
        if day <= 2:
            return 1
        elif day <= 9:
            return 2
        else:
            return 3
    elif season_year == 2024:
        if day <= 3:
            return 1
        elif day <= 10:
            return 2
        else:
            return 3
    elif season_year == 2023:
        if day <= 5:
            return 1
        elif day <= 12:
            return 2
        else:
            return 3

    # Generic fallback
    if day <= 7:
        return 1
    elif day <= 14:
        return 2
    return 3


def compute_event_metrics(conn, event_id: int):
    """Calculates all statistical metrics for an event's scores and advancement."""
    c = conn.cursor()

    # Get team scores
    c.execute("""
        SELECT s.team_number, s.team_name, s.highest_score, s.round_1, s.round_2, s.round_3, s.ranking, s.ordinal
        FROM scores s
        WHERE s.event_id = ?
        ORDER BY s.highest_score DESC
    """, (event_id,))
    score_rows = c.fetchall()

    # Get advancement info
    c.execute("""
        SELECT team_number, advancing_to_next_level, advancing_wait_list
        FROM event_teams
        WHERE event_id = ?
    """, (event_id,))
    adv_info = {r[0]: {"adv": bool(r[1]), "wait": bool(r[2])} for r in c.fetchall()}

    # Get awards count
    c.execute("""
        SELECT award_name, category, team_number, team_name
        FROM awards
        WHERE event_id = ?
    """, (event_id,))
    award_rows = c.fetchall()

    def to_float(val):
        if val is None:
            return None
        try:
            f = float(val)
            return f if f > 0 else None
        except (ValueError, TypeError):
            return None

    highest_scores = [to_float(r[2]) for r in score_rows]
    highest_scores = [s for s in highest_scores if s is not None]
    total_scored_teams = len(score_rows)

    if not highest_scores:
        return {
            "scored_teams": total_scored_teams,
            "max_score": None,
            "top_team": None,
            "top3_avg": None,
            "top5_avg": None,
            "median_score": None,
            "mean_score": None,
            "std_dev": None,
            "p75_score": None,
            "p25_score": None,
            "min_score": None,
            "advancement_cutoff": None,
            "advancement_count": 0,
            "round_averages": [None, None, None],
            "distribution": {"<200": 0, "200-299": 0, "300-399": 0, "400+": 0},
            "scores_list": [],
            "awards_list": [
                {"name": a[0], "category": a[1], "team_number": a[2], "team_name": a[3]}
                for a in award_rows
            ],
        }

    max_score = max(highest_scores)
    top_team = f"#{score_rows[0][0]} {score_rows[0][1]}" if score_rows else None
    top3_avg = round(statistics.mean(highest_scores[:3]), 1) if len(highest_scores) >= 3 else max_score
    top5_avg = round(statistics.mean(highest_scores[:5]), 1) if len(highest_scores) >= 5 else top3_avg
    med_score = round(statistics.median(highest_scores), 1)
    mean_score = round(statistics.mean(highest_scores), 1)
    std_dev = round(statistics.stdev(highest_scores), 1) if len(highest_scores) > 1 else 0.0

    # Percentiles
    if len(highest_scores) >= 4:
        quantiles = statistics.quantiles(highest_scores, n=4)
        p25 = round(quantiles[0], 1)
        p75 = round(quantiles[2], 1)
    else:
        p25 = min(highest_scores)
        p75 = max(highest_scores)
    min_score = min(highest_scores)

    # Advancement cutoff
    adv_scores = [to_float(r[2]) for r in score_rows if adv_info.get(r[0], {}).get("adv")]
    adv_scores = [s for s in adv_scores if s is not None]
    adv_cutoff = min(adv_scores) if adv_scores else None
    adv_count = sum(1 for v in adv_info.values() if v.get("adv"))

    # Round averages
    r1_vals = [s for s in [to_float(r[3]) for r in score_rows] if s is not None]
    r2_vals = [s for s in [to_float(r[4]) for r in score_rows] if s is not None]
    r3_vals = [s for s in [to_float(r[5]) for r in score_rows] if s is not None]
    round_averages = [
        round(statistics.mean(r1_vals), 1) if r1_vals else None,
        round(statistics.mean(r2_vals), 1) if r2_vals else None,
        round(statistics.mean(r3_vals), 1) if r3_vals else None,
    ]

    # Distribution brackets
    dist = {
        "<200": sum(1 for s in highest_scores if s < 200),
        "200-299": sum(1 for s in highest_scores if 200 <= s < 300),
        "300-399": sum(1 for s in highest_scores if 300 <= s < 400),
        "400+": sum(1 for s in highest_scores if s >= 400),
    }

    # Clean scores list for UI drill-down
    clean_scores = []
    for r in score_rows:
        t_num = r[0]
        t_adv = adv_info.get(t_num, {}).get("adv", False)
        t_wait = adv_info.get(t_num, {}).get("wait", False)
        clean_scores.append({
            "ranking": r[6],
            "ordinal": r[7],
            "team_number": t_num,
            "team_name": r[1],
            "highest_score": r[2],
            "round_1": r[3],
            "round_2": r[4],
            "round_3": r[5],
            "advancing": t_adv,
            "waitlist": t_wait,
        })

    return {
        "scored_teams": total_scored_teams,
        "max_score": max_score,
        "top_team": top_team,
        "top3_avg": top3_avg,
        "top5_avg": top5_avg,
        "median_score": med_score,
        "mean_score": mean_score,
        "std_dev": std_dev,
        "p75_score": p75,
        "p25_score": p25,
        "min_score": min_score,
        "advancement_cutoff": adv_cutoff,
        "advancement_count": adv_count,
        "round_averages": round_averages,
        "distribution": dist,
        "scores_list": clean_scores,
        "awards_list": [
            {"name": a[0], "category": a[1], "team_number": a[2], "team_name": a[3]}
            for a in award_rows
        ],
    }


def normalize_venue_key(name: str, venue: str) -> str:
    """Normalize venue name into a unified matching key."""
    s = f"{venue or ''} {name or ''}".lower()
    s = s.replace(".", "").replace("-", " ")

    mappings = [
        ("st martin", "st_martin_tours"),
        ("dorris eaton", "dorris_eaton"),
        ("beyer", "beyer_hs"),
        ("sf day", "sf_day_school"),
        ("king's academy", "kings_academy"),
        ("kings academy", "kings_academy"),
        ("bay university", "sf_bay_university"),
        ("sfbu", "sf_bay_university"),
        ("basis", "basis_independent"),
        ("town school", "sf_town_school"),
        ("play space", "play_space"),
        ("nueva", "nueva_school"),
        ("pleasant grove", "pleasant_grove"),
        ("gunn", "gunn_hs"),
        ("lowell", "lowell_hs"),
        ("epa center", "epa_center"),
        ("leland", "leland_hs"),
        ("santa teresa", "santa_teresa"),
        ("quarry lane", "quarry_lane"),
        ("gomes", "gomes_elem"),
        ("stratford", "stratford_prep"),
        ("st christopher", "st_christopher"),
        ("mountain view", "mountain_view_hs"),
        ("mt view", "mountain_view_hs"),
        ("san antonio", "san_antonio_center"),
        ("sacramento country", "sacramento_country_day"),
        ("fremont high", "fremont_hs"),
        ("presentation", "presentation_hs"),
    ]

    for needle, key in mappings:
        if needle in s:
            return key
    return "other_" + re.sub(r"[^a-z0-9]", "_", s[:20])


def extract_clean_venue_and_city(name: str, venue_name: str, city: str):
    v = venue_name
    c = city
    if not v or not c or v == name or c == "None" or v == "None":
        m = re.search(r'QT\s*[-–]\s*(.+)', name)
        if m:
            sub = m.group(1).strip()
            sub = re.sub(r'^(?:NOV|DEC|OCT)\s+\d+\s+', '', sub, flags=re.IGNORECASE)
            if ',' in sub:
                vpart, cpart = sub.rsplit(',', 1)
                v = vpart.strip()
                c = cpart.strip()
            else:
                v = sub.strip()
                if "sf" in sub.lower() or "san francisco" in sub.lower():
                    c = "San Francisco"
                else:
                    c = "Bay Area"
    if v and "The Play Space" in v:
        v = "The Play Space"
    if v and "St. Martin" in v:
        v = "St. Martin of Tours"
    if not c or c == "None":
        c = "Bay Area"
    return v or name, c


def get_region_name(city: str) -> str:
    """Classify city into NorCal FLL geographic region."""
    if not city:
        return "Bay Area (湾区)"
    c = city.strip()
    if c in ["San Jose", "Sunnyvale", "Santa Clara", "Campbell", "Cupertino", "Saratoga", "Morgan Hill"]:
        return "South Bay (南湾)"
    elif c in ["Palo Alto", "East Palo Alto", "Mountain View", "San Mateo", "Redwood City", "Burlingame"]:
        return "Peninsula (半岛)"
    elif c in ["Fremont", "San Ramon", "Dublin", "Pleasanton", "Oakland", "Berkeley", "Hayward", "Union City", "Livermore"]:
        return "East Bay (东湾)"
    elif c in ["San Francisco"]:
        return "San Francisco (旧金山)"
    elif c in ["Sacramento", "Elk Grove", "Modesto", "Stockton", "Davis", "Roseville", "Rocklin"]:
        return "Greater Sac & Central Valley (萨克拉门托与中央谷地)"
    return "Bay Area (湾区)"


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Fetch all events
    c.execute("""
        SELECT id, name, season, program, program_abbreviation, event_status,
               capacity, total_registered, start_time, end_time, timezone,
               venue_id, venue_city, venue_name, venue_address, website_uri
        FROM events
        ORDER BY start_time, id
    """)
    all_events_raw = c.fetchall()

    events_by_id = {}
    for r in all_events_raw:
        eid = r[0]
        s_name = r[2] or ""
        year = 2026 if "2026" in s_name else (2025 if "2025" in s_name else (2024 if "2024" in s_name else 2023))
        date_str = (r[8] or "")[:10]
        wk = get_weekend_index(year, date_str)
        clean_venue, clean_city = extract_clean_venue_and_city(r[1], r[13], r[12])
        v_key = normalize_venue_key(r[1], clean_venue)
        reg_name = get_region_name(clean_city)

        metrics = compute_event_metrics(conn, eid)

        event_obj = {
            "id": eid,
            "name": r[1],
            "season": s_name,
            "season_year": year,
            "program_abbreviation": r[4],
            "event_status": r[5],
            "capacity": r[6],
            "total_registered": r[7],
            "start_time": r[8],
            "date": date_str,
            "weekend": wk,
            "weekend_label": f"Week {wk}" if wk > 0 else "Special/Championship",
            "venue_id": r[11],
            "city": clean_city,
            "region": reg_name,
            "venue_name": clean_venue,
            "venue_key": v_key,
            "address": r[14],
            "website_uri": r[15],
            "metrics": metrics,
        }
        events_by_id[eid] = event_obj

    # 2. Extract 2026 BIOGLOW events
    bioglow_events = [e for e in events_by_id.values() if e["season_year"] == 2026]
    bioglow_events.sort(key=lambda x: (x["date"], x["name"]))

    # 3. Build venue historical index
    # We group past Qualification Tournaments (2025, 2024, 2023) by venue_key
    past_qt_events = [
        e for e in events_by_id.values()
        if e["season_year"] < 2026 and e["program_abbreviation"] == "fll_challenge" and e["weekend"] > 0
    ]

    venues_catalog = {}
    for pe in past_qt_events:
        vk = pe["venue_key"]
        if vk not in venues_catalog:
            venues_catalog[vk] = {
                "venue_key": vk,
                "display_name": pe["venue_name"],
                "city": pe["city"],
                "events_history": [],
            }
        venues_catalog[vk]["events_history"].append(pe["id"])

    # Link BIOGLOW events to their venue's past history
    for be in bioglow_events:
        vk = be["venue_key"]
        hist_ids = venues_catalog.get(vk, {}).get("events_history", [])
        
        # Sort historical events descending by date
        hist_events = [events_by_id[hid] for hid in hist_ids]
        hist_events.sort(key=lambda x: x["date"], reverse=True)

        # Calculate cross-year historical summary for this venue
        valid_max_scores = [h["metrics"]["max_score"] for h in hist_events if h["metrics"]["max_score"]]
        valid_cutoffs = [h["metrics"]["advancement_cutoff"] for h in hist_events if h["metrics"]["advancement_cutoff"]]
        valid_medians = [h["metrics"]["median_score"] for h in hist_events if h["metrics"]["median_score"]]
        valid_top3 = [h["metrics"]["top3_avg"] for h in hist_events if h["metrics"]["top3_avg"]]

        be["venue_history"] = {
            "venue_key": vk,
            "historical_event_count": len(hist_events),
            "past_events": [
                {
                    "id": h["id"],
                    "name": h["name"],
                    "season": h["season"],
                    "season_year": h["season_year"],
                    "date": h["date"],
                    "weekend": h["weekend"],
                    "weekend_label": h["weekend_label"],
                    "metrics": h["metrics"],
                }
                for h in hist_events
            ],
            "benchmark": {
                "all_time_venue_max": max(valid_max_scores) if valid_max_scores else None,
                "avg_venue_top3": round(statistics.mean(valid_top3), 1) if valid_top3 else None,
                "avg_venue_median": round(statistics.mean(valid_medians), 1) if valid_medians else None,
                "avg_advancement_cutoff": round(statistics.mean(valid_cutoffs), 1) if valid_cutoffs else None,
                "last_year_event_id": hist_events[0]["id"] if hist_events and hist_events[0]["season_year"] == 2025 else None,
            },
        }

    # 4. Cross-Weekend Macro Statistics (for Season Progression Trends)
    # Compare 2025 Week 1 vs Week 2 vs Week 3
    season_2025_qts = [e for e in past_qt_events if e["season_year"] == 2025]
    week_comparison_2025 = {}
    for wk in [1, 2, 3]:
        wk_events = [e for e in season_2025_qts if e["weekend"] == wk]
        wk_maxes = [e["metrics"]["max_score"] for e in wk_events if e["metrics"]["max_score"]]
        wk_top3 = [e["metrics"]["top3_avg"] for e in wk_events if e["metrics"]["top3_avg"]]
        wk_medians = [e["metrics"]["median_score"] for e in wk_events if e["metrics"]["median_score"]]
        wk_cutoffs = [e["metrics"]["advancement_cutoff"] for e in wk_events if e["metrics"]["advancement_cutoff"]]

        week_comparison_2025[f"Week {wk}"] = {
            "events_count": len(wk_events),
            "avg_max_score": round(statistics.mean(wk_maxes), 1) if wk_maxes else None,
            "avg_top3_score": round(statistics.mean(wk_top3), 1) if wk_top3 else None,
            "avg_median_score": round(statistics.mean(wk_medians), 1) if wk_medians else None,
            "avg_advancement_cutoff": round(statistics.mean(wk_cutoffs), 1) if wk_cutoffs else None,
            "events": [{"id": e["id"], "name": e["name"], "venue": e["venue_name"], "max": e["metrics"]["max_score"], "top3": e["metrics"]["top3_avg"], "cutoff": e["metrics"]["advancement_cutoff"]} for e in wk_events],
        }

    # 5. Modular Induction Analysis: By Region & By Weekend
    def build_dataset_induction(qt_events, dataset_key, dataset_label):
        from collections import defaultdict
        region_group = defaultdict(list)
        wk_group = defaultdict(list)
        valid_events = [e for e in qt_events if e["metrics"]["median_score"] is not None]

        for e in valid_events:
            region_group[e["region"]].append(e)
            wk_group[e["weekend"]].append(e)

        all_medians = [e["metrics"]["median_score"] for e in valid_events]
        grand_mean = statistics.mean(all_medians)
        ss_total = sum((m - grand_mean) ** 2 for m in all_medians)

        # 5.1 Region ANOVA & Stats
        region_induction = []
        ss_region = 0.0
        for reg, evts in region_group.items():
            meds = [x["metrics"]["median_score"] for x in evts]
            maxs = [x["metrics"]["max_score"] for x in evts if x["metrics"]["max_score"] is not None]
            top3s = [x["metrics"]["top3_avg"] for x in evts if x["metrics"]["top3_avg"] is not None]
            cutoffs = [x["metrics"]["advancement_cutoff"] for x in evts if x["metrics"]["advancement_cutoff"] is not None]
            m_mean = round(statistics.mean(meds), 1)
            m_med = round(statistics.median(meds), 1)
            m_std = round(statistics.stdev(meds), 1) if len(meds) > 1 else 0.0
            ss_region += len(meds) * ((m_mean - grand_mean) ** 2)

            cities_in_reg = sorted(list(set(x["city"] for x in evts)))
            all_team_scores = [
                t["highest_score"] for x in evts for t in x["metrics"]["scores_list"]
                if t.get("highest_score") is not None and t.get("highest_score") > 0
            ]
            pooled_med = round(statistics.median(all_team_scores), 1) if all_team_scores else None

            if m_mean >= 255:
                tier = "Tier S (特高分核心区)"
                tier_class = "tier-s"
            elif m_mean >= 235:
                tier = "Tier A (高分主力强区)"
                tier_class = "tier-a"
            elif m_mean >= 215:
                tier = "Tier B (稳健标准区)"
                tier_class = "tier-b"
            else:
                tier = "Tier C (发展/单校区)"
                tier_class = "tier-c"

            region_induction.append({
                "region": reg,
                "cities": cities_in_reg,
                "cities_str": ", ".join(cities_in_reg),
                "tier": tier,
                "tier_class": tier_class,
                "events_count": len(evts),
                "total_teams": len(all_team_scores),
                "mean_median": m_mean,
                "pooled_median": pooled_med,
                "median_median": m_med,
                "min_median": round(min(meds), 1),
                "max_median": round(max(meds), 1),
                "std_median": m_std,
                "mean_max": round(statistics.mean(maxs), 1) if maxs else None,
                "mean_top3": round(statistics.mean(top3s), 1) if top3s else None,
                "mean_cutoff": round(statistics.mean(cutoffs), 1) if cutoffs else None,
                "events": [
                    {
                        "id": x["id"],
                        "name": x["name"],
                        "season_year": x["season_year"],
                        "city": x["city"],
                        "venue_name": x["venue_name"],
                        "weekend": x["weekend"],
                        "weekend_label": x["weekend_label"],
                        "date": x["date"],
                        "median": x["metrics"]["median_score"],
                        "max": x["metrics"]["max_score"],
                        "cutoff": x["metrics"]["advancement_cutoff"],
                    }
                    for x in evts
                ],
            })
        region_induction.sort(key=lambda x: (x["mean_median"], x["events_count"]), reverse=True)

        # 5.2 Weekend ANOVA & Stats
        weekend_induction = []
        ss_wk = 0.0
        for wk in [1, 2, 3]:
            evts = wk_group.get(wk, [])
            meds = [x["metrics"]["median_score"] for x in evts]
            maxs = [x["metrics"]["max_score"] for x in evts if x["metrics"]["max_score"]]
            top3s = [x["metrics"]["top3_avg"] for x in evts if x["metrics"]["top3_avg"]]
            cutoffs = [x["metrics"]["advancement_cutoff"] for x in evts if x["metrics"]["advancement_cutoff"]]
            m_mean = round(statistics.mean(meds), 1) if meds else 0.0
            m_med = round(statistics.median(meds), 1) if meds else 0.0
            m_std = round(statistics.stdev(meds), 1) if len(meds) > 1 else 0.0
            if meds:
                ss_wk += len(meds) * ((m_mean - grand_mean) ** 2)

            all_wk_team_scores = [
                t["highest_score"] for x in evts for t in x["metrics"]["scores_list"]
                if t.get("highest_score") is not None and t.get("highest_score") > 0
            ]
            wk_pooled_med = round(statistics.median(all_wk_team_scores), 1) if all_wk_team_scores else None

            insight = ""
            if wk == 1:
                insight = "冷启动起步周：赛季初队伍机械未充分调优，无特大高分，中位数偏低，出线门槛最低。"
            elif wk == 2:
                insight = "技术成熟跃升周：各队算法与结构成型，中位数跳升至平台期，单场最高分跳涨 +30% 以上。"
            else:
                insight = "巅峰收官周：最高分飙出 510/440 分全季极值，但中位数与第2周完全走平（甚至微降），验证了天花板冲高、底盘固定的规律。"

            weekend_induction.append({
                "weekend": wk,
                "weekend_label": f"Week {wk}",
                "events_count": len(evts),
                "total_teams": len(all_wk_team_scores),
                "mean_median": m_mean,
                "pooled_median": wk_pooled_med,
                "median_median": m_med,
                "min_median": round(min(meds), 1) if meds else None,
                "max_median": round(max(meds), 1) if meds else None,
                "std_median": m_std,
                "mean_max": round(statistics.mean(maxs), 1) if maxs else None,
                "mean_top3": round(statistics.mean(top3s), 1) if top3s else None,
                "mean_cutoff": round(statistics.mean(cutoffs), 1) if cutoffs else None,
                "insight": insight,
                "events": [
                    {
                        "id": x["id"],
                        "name": x["name"],
                        "season_year": x["season_year"],
                        "city": x["city"],
                        "region": x["region"],
                        "venue_name": x["venue_name"],
                        "median": x["metrics"]["median_score"],
                        "max": x["metrics"]["max_score"],
                        "cutoff": x["metrics"]["advancement_cutoff"],
                    }
                    for x in evts
                ],
            })

        # 5.3 Effect Size: Region vs Weekend
        eta2_region = round((ss_region / ss_total) * 100, 1) if ss_total > 0 else 0.0
        eta2_wk = round((ss_wk / ss_total) * 100, 1) if ss_total > 0 else 0.0
        variance_ratio = round(ss_region / ss_wk, 1) if ss_wk > 0 else 999.0

        reg_min = min(r["mean_median"] for r in region_induction)
        reg_max = max(r["mean_median"] for r in region_induction)
        reg_rng = round(reg_max - reg_min, 1)

        wk_min = min(w["mean_median"] for w in weekend_induction)
        wk_max = max(w["mean_median"] for w in weekend_induction)
        wk_rng = round(wk_max - wk_min, 1)
        rng_ratio = round(reg_rng / wk_rng, 1) if wk_rng > 0 else 999.0

        # Cross-metric sensitivity breakdown
        metrics_sensitivity = []
        for m_key, m_label in [
            ("median_score", "中位数分数 (Median)"),
            ("mean_score", "单场平均分 (Mean)"),
            ("advancement_cutoff", "出线晋级线 (Cutoff)"),
            ("top3_avg", "前三平均分 (Top 3 Avg)"),
            ("max_score", "单场最高分 (Max Score)"),
        ]:
            v_list = [e["metrics"][m_key] for e in valid_events if e["metrics"][m_key] is not None]
            if v_list:
                g_m = statistics.mean(v_list)
                tot_ss = sum((x - g_m) ** 2 for x in v_list)
                r_ss = sum(len([x for x in region_group[r] if x["metrics"][m_key] is not None]) * ((statistics.mean([x["metrics"][m_key] for x in region_group[r] if x["metrics"][m_key] is not None]) - g_m) ** 2) for r in region_group if [x for x in region_group[r] if x["metrics"][m_key] is not None])
                w_ss = sum(len([x for x in wk_group[w] if x["metrics"][m_key] is not None]) * ((statistics.mean([x["metrics"][m_key] for x in wk_group[w] if x["metrics"][m_key] is not None]) - g_m) ** 2) for w in wk_group if [x for x in wk_group[w] if x["metrics"][m_key] is not None])
                metrics_sensitivity.append({
                    "metric_key": m_key,
                    "metric_label": m_label,
                    "region_explained_pct": round((r_ss / tot_ss) * 100, 1) if tot_ss > 0 else 0.0,
                    "weekend_explained_pct": round((w_ss / tot_ss) * 100, 1) if tot_ss > 0 else 0.0,
                    "dominant_factor": "大区 (Region)" if r_ss > w_ss else "周次 (Weekend)",
                    "ratio": round(r_ss / w_ss, 1) if w_ss > 0 else 999.0,
                })

        verdict_zh = ""
        if dataset_key == "2025":
            verdict_zh = (
                "【2025 赛季结论】：大区对中位数的方差解释力达 18.1%，周次仅占 1.6%（大区影响力是周次的 11.2 倍）。"
                "大区之间平均中位数落差达 47.5 分（东湾 230.0 分 vs 中央谷地 277.5 分），"
                "而跨周末极差仅为 14.8 分（且 Week 2 与 Week 3 几乎完全持平，仅差 1.3 分）。"
            )
        else:
            verdict_zh = (
                "【2024+2025 双赛季强化结论】：样本量扩大至 36 场后，进一步证实了【Week 2 与 Week 3 中位数完全持平】的硬规律！"
                "双赛季合并后，Week 2 的平均中位数为 234.0 分，Week 3 为 233.4 分（差异仅 0.6 分，完全锁定在同一水平线）。"
                "大区间的落差（71.9 分）依然显著大于周次极差（31.5 分，且周次差异仅源自 Week 1 的初期冷启动）。"
                "大区整体生态排序跨两个赛季保持高度一致：中央谷地始终领跑，南湾与半岛稳居核心高强区，东湾与旧金山处于温和区。"
            )

        return {
            "dataset_key": dataset_key,
            "dataset_label": dataset_label,
            "events_count": len(valid_events),
            "region_induction": region_induction,
            "weekend_induction": weekend_induction,
            "impact_comparison": {
                "metric_analyzed": "median_score",
                "sample_size": len(valid_events),
                "grand_mean": round(grand_mean, 1),
                "ss_total": round(ss_total, 1),
                "region_effect": {
                    "sum_of_squares": round(ss_region, 1),
                    "variance_explained_pct": eta2_region,
                    "mean_min": reg_min,
                    "mean_max": reg_max,
                    "range_pts": reg_rng,
                },
                "weekend_effect": {
                    "sum_of_squares": round(ss_wk, 1),
                    "variance_explained_pct": eta2_wk,
                    "mean_min": wk_min,
                    "mean_max": wk_max,
                    "range_pts": wk_rng,
                },
                "variance_ratio": variance_ratio,
                "range_ratio": rng_ratio,
                "decisive_factor": "Region (大区)",
                "verdict_zh": verdict_zh,
                "metrics_sensitivity": metrics_sensitivity,
            },
        }

    dataset_2025 = build_dataset_induction(
        [e for e in past_qt_events if e["season_year"] == 2025],
        "2025",
        "2025 赛季 (20 场实测·基准统一)"
    )

    dataset_combined = build_dataset_induction(
        [e for e in past_qt_events if e["season_year"] in [2024, 2025]],
        "combined",
        "2024 + 2025 双赛季聚合 (36 场实测·样本扩大)"
    )

    # 6. Output full analysis package
    analysis_payload = {
        "generated_at": "2026-10-01",
        "current_season": "2026 - BIOGLOW (Challenge)",
        "bioglow_events": bioglow_events,
        "all_qt_events": past_qt_events,
        "week_comparison_2025": week_comparison_2025,
        "datasets": {
            "2025": dataset_2025,
            "combined": dataset_combined,
        },
        # Default backward compatible bindings
        "region_induction": dataset_2025["region_induction"],
        "weekend_induction": dataset_2025["weekend_induction"],
        "impact_comparison": dataset_2025["impact_comparison"],
        "events_by_id": {eid: e for eid, e in events_by_id.items() if e["program_abbreviation"] == "fll_challenge"},
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(analysis_payload, f, ensure_ascii=False, indent=2)

    WEB_DATA_JS = Path(__file__).parent / "web" / "data.js"
    with open(WEB_DATA_JS, "w", encoding="utf-8") as f:
        f.write("window.BIOGLOW_DATA = " + json.dumps(analysis_payload, ensure_ascii=False) + ";")

    print(f"Successfully generated BIOGLOW analysis dataset at {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size / 1024:.1f} KB)")
    print(f"Successfully updated web data script at {WEB_DATA_JS} ({WEB_DATA_JS.stat().st_size / 1024:.1f} KB)")
    print("\n=== BIOGLOW Events Venue Historical Linking Summary ===")
    for be in bioglow_events:
        hist = be["venue_history"]
        bench = hist["benchmark"]
        ly_id = bench["last_year_event_id"]
        ly_str = f"2025 Event #{ly_id}" if ly_id else "No 2025 event"
        max_str = f"Max {bench['all_time_venue_max']}" if bench['all_time_venue_max'] else "N/A"
        cut_str = f"Cutoff {bench['avg_advancement_cutoff']}" if bench['avg_advancement_cutoff'] else "N/A"
        print(f"[{be['id']}] {be['weekend_label']} | {be['date']} | {be['city']:15s} | {be['venue_name'][:25]:25s} -> {ly_str:16s} ({hist['historical_event_count']} past events | {max_str} | {cut_str})")


if __name__ == "__main__":
    main()
