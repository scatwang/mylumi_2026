#!/usr/bin/env python3
"""
Comprehensive Statistical Analysis of MyLumi Public Teams.
Reads data/raw/public_teams.json or data/mylumi.db and generates:
- data/public_teams_analysis.json
- TEAM_ANALYSIS_REPORT.md
- Optional charts or visual data structures
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import statistics

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_JSON = DATA_DIR / "raw" / "public_teams.json"
ANALYSIS_JSON = DATA_DIR / "public_teams_analysis.json"
REPORT_MD = Path(__file__).resolve().parent / "TEAM_ANALYSIS_REPORT.md"


def load_teams():
    if not RAW_JSON.exists():
        raise FileNotFoundError(f"{RAW_JSON} does not exist. Run crawl_public_teams.py first.")
    with open(RAW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze(teams):
    total_teams = len(teams)

    # 1. Program Distribution
    program_counter = Counter(t.get("program_label") or "Unknown" for t in teams)
    program_stats = []
    for prog, count in program_counter.most_common():
        program_stats.append({
            "program": prog,
            "count": count,
            "pct": round(count / total_teams * 100, 2)
        })

    # 2. Overall Status (status_v2)
    status_counter = Counter(t.get("status_v2") or "Unknown" for t in teams)
    status_stats = []
    for st, count in status_counter.most_common():
        status_stats.append({
            "status": st,
            "count": count,
            "pct": round(count / total_teams * 100, 2)
        })

    # 3. Status Quickview Components (Screening, Fingerprinting, Coaches, Roster, Agreements)
    compliance_keys = ["screening", "fingerprinting", "coaches", "roster_status", "agreements"]
    compliance_stats = {}
    for k in compliance_keys:
        good_cnt = sum(1 for t in teams if (t.get("status_quickview") or {}).get(k, {}).get("good") is True)
        fail_cnt = sum(1 for t in teams if (t.get("status_quickview") or {}).get(k, {}).get("good") is False)
        none_cnt = total_teams - good_cnt - fail_cnt
        compliance_stats[k] = {
            "good_count": good_cnt,
            "good_pct": round(good_cnt / total_teams * 100, 2),
            "fail_count": fail_cnt,
            "fail_pct": round(fail_cnt / total_teams * 100, 2),
            "other_count": none_cnt,
        }

    # 4. Geographic Distribution (Cities)
    city_counter = Counter((t.get("city") or "").strip() or "Unknown" for t in teams)
    top_cities = []
    for city, count in city_counter.most_common(20):
        top_cities.append({
            "city": city,
            "count": count,
            "pct": round(count / total_teams * 100, 2)
        })
    total_unique_cities = len([c for c in city_counter.keys() if c != "Unknown"])

    # City Normalization helper
    def normalize_city(raw_city):
        if not raw_city:
            return "Unknown"
        c = raw_city.strip()
        cl = c.lower()
        if "mountain view" in cl: return "Mountain View"
        if "fremont" in cl or "fremount" in cl: return "Fremont"
        if "san jose" in cl: return "San Jose"
        if "san francisco" in cl: return "San Francisco"
        if "santa clara" in cl: return "Santa Clara"
        if "milpitas" in cl: return "Milpitas"
        if "folsom" in cl: return "Folsom"
        return c

    def get_region_name(city_name):
        c = normalize_city(city_name)
        east_bay = {
            "Oakland", "Piedmont", "Fremont", "Dublin", "Pleasanton", "San Ramon",
            "Walnut Creek", "Danville", "Union City", "Hercules", "Berkeley",
            "Castro Valley", "Albany", "Livermore", "El Cerrito", "Hayward",
            "San Leandro", "Alameda", "Pleasant Hill", "Newark", "Richmond"
        }
        south_bay = {
            "San Jose", "Santa Clara", "Sunnyvale", "Mountain View", "Saratoga",
            "Cupertino", "Los Altos", "Milpitas", "Palo Alto", "Morgan Hill",
            "Los Gatos", "Campbell", "Monte Sereno", "Hollister"
        }
        peninsula = {
            "San Francisco", "Burlingame", "Hillsborough", "San Carlos", "San Mateo",
            "Menlo Park", "Half Moon Bay", "East Palo Alto", "San Bruno", "Belmont",
            "Foster City", "Seaside", "Marina"
        }
        sac_valley = {
            "Folsom", "Mountain House", "Sacramento", "El Dorado Hills", "Tracy",
            "Lathrop", "Rancho Cordova", "Roseville", "Modesto", "Ceres",
            "Lakeport", "Rocklin"
        }
        north_bay = {"Kentfield", "Santa Rosa", "Petaluma", "Novato", "San Rafael"}

        if c in east_bay: return "东湾 (East Bay)"
        if c in south_bay: return "南湾 / 硅谷 (South Bay)"
        if c in peninsula: return "半岛与旧金山 (Peninsula & SF)"
        if c in sac_valley: return "首府圈与中谷 (Sacramento & Valley)"
        if c in north_bay: return "北湾 (North Bay)"
        return "其他 / 外围区域 (Other)"

    # Regional Buckets
    region_stats = defaultdict(int)
    challenge_region_stats = defaultdict(int)
    for t in teams:
        r = get_region_name(t.get("city"))
        region_stats[r] += 1
        if t.get("program_label") == "FIRST LEGO League: Challenge":
            challenge_region_stats[r] += 1

    region_summary = [
        {"region": reg, "count": cnt, "pct": round(cnt / total_teams * 100, 2)}
        for reg, cnt in sorted(region_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    ch_total = sum(challenge_region_stats.values()) or 1
    challenge_region_summary = [
        {"region": reg, "count": cnt, "pct": round(cnt / ch_total * 100, 2)}
        for reg, cnt in sorted(challenge_region_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    # 5. Organizations (Schools, Community, Non-profits)
    org_counter = Counter((t.get("org_name") or "").strip() or "Unspecified" for t in teams)
    top_orgs = []
    for org, count in org_counter.most_common(20):
        top_orgs.append({
            "org_name": org,
            "count": count,
            "pct": round(count / total_teams * 100, 2)
        })

    # Group organizations into categories
    org_type_counts = {"Family/Community": 0, "Piedmont Makers": 0, "School / Academic Institution": 0, "Other / Private Org": 0}
    for org, count in org_counter.items():
        org_lower = org.lower()
        if "family" in org_lower or "community" in org_lower:
            org_type_counts["Family/Community"] += count
        elif "piedmont makers" in org_lower:
            org_type_counts["Piedmont Makers"] += count
        elif any(w in org_lower for w in ["school", "elementary", "middle", "academy", "district", "high", "unified"]):
            org_type_counts["School / Academic Institution"] += count
        else:
            org_type_counts["Other / Private Org"] += count

    org_category_stats = [
        {"category": k, "count": v, "pct": round(v / total_teams * 100, 2)}
        for k, v in org_type_counts.items()
    ]

    # 6. Coach Counts Distribution
    coaches_counter = Counter(t.get("coaches_count") for t in teams)
    coaches_stats = []
    for c_cnt, num_teams in sorted(coaches_counter.items()):
        coaches_stats.append({
            "coaches_count": c_cnt,
            "teams": num_teams,
            "pct": round(num_teams / total_teams * 100, 2)
        })

    # 7. Team Number Ranges (Vintage vs New Teams)
    numbers = [t["number"] for t in teams if isinstance(t.get("number"), int)]
    number_stats = {
        "min": min(numbers) if numbers else None,
        "max": max(numbers) if numbers else None,
        "median": int(statistics.median(numbers)) if numbers else None,
        "mean": round(statistics.mean(numbers), 1) if numbers else None,
    }

    # Buckets for team number
    buckets = [
        ("< 10,000 (Veteran/Early Teams)", 0, 9999),
        ("10,000 - 29,999 (Established Teams)", 10000, 29999),
        ("30,000 - 49,999 (Mid-Era Teams)", 30000, 49999),
        ("50,000 - 64,999 (Recent Teams 2021-2023)", 50000, 64999),
        ("65,000 - 74,999 (New Teams 2024-2025)", 65000, 74999),
        (">= 75,000 (Brand New Teams 2025-2026)", 75000, 999999),
    ]
    bucket_counts = []
    for label, low, high in buckets:
        cnt = sum(1 for n in numbers if low <= n <= high)
        bucket_counts.append({
            "range_label": label,
            "count": cnt,
            "pct": round(cnt / len(numbers) * 100, 2)
        })

    # 8. Cross-analysis: Status by Program
    status_by_program = defaultdict(lambda: Counter())
    for t in teams:
        prog = t.get("program_label") or "Unknown"
        st = t.get("status_v2") or "Unknown"
        status_by_program[prog][st] += 1

    prog_status_breakdown = {}
    for prog, counts in status_by_program.items():
        total_p = sum(counts.values())
        prog_status_breakdown[prog] = {
            "total": total_p,
            "ready_good": counts.get("good", 0),
            "ready_good_pct": round(counts.get("good", 0) / total_p * 100, 2),
            "status_details": dict(counts)
        }

    # 9. Cross-analysis: Status by Organization Category
    status_by_org_type = defaultdict(lambda: Counter())
    for t in teams:
        org = (t.get("org_name") or "").strip()
        org_lower = org.lower()
        if "family" in org_lower or "community" in org_lower:
            cat = "Family/Community"
        elif "piedmont makers" in org_lower:
            cat = "Piedmont Makers"
        elif any(w in org_lower for w in ["school", "elementary", "middle", "academy", "district", "high", "unified"]):
            cat = "School / Academic Institution"
        else:
            cat = "Other / Private Org"

        st = t.get("status_v2") or "Unknown"
        status_by_org_type[cat][st] += 1

    org_status_breakdown = {}
    for cat, counts in status_by_org_type.items():
        total_o = sum(counts.values())
        org_status_breakdown[cat] = {
            "total": total_o,
            "ready_good": counts.get("good", 0),
            "ready_good_pct": round(counts.get("good", 0) / total_o * 100, 2),
            "status_details": dict(counts)
        }

    # 10. Registered Events & Advancements
    reg_events_count = sum(1 for t in teams if t.get("registered_events"))
    advancements = Counter((t.get("advancement") or {}).get("state", "none") for t in teams)

    # 11. Historical Performance Analytics (from integrated events history)
    teams_with_hist = [t for t in teams if (t.get("history") or {}).get("has_history")]
    teams_with_scores = [t for t in teams if (t.get("history") or {}).get("max_score") is not None]
    teams_with_awards = [t for t in teams if (t.get("history") or {}).get("awards_count", 0) > 0]
    teams_with_adv = [t for t in teams if (t.get("history") or {}).get("advancements_count", 0) > 0]
    teams_with_champ = [t for t in teams if (t.get("history") or {}).get("has_championship")]

    # Experience Tiers
    exp_counter = Counter((t.get("history") or {}).get("experience_tier", "Rookie (新队伍)") for t in teams)
    experience_tier_stats = [
        {"tier": tier, "count": count, "pct": round(count / total_teams * 100, 2)}
        for tier, count in exp_counter.most_common()
    ]

    # Score Tiers
    score_tier_counter = Counter((t.get("history") or {}).get("score_tier", "暂无历史成绩") for t in teams)
    score_tier_stats = [
        {"tier": tier, "count": count, "pct": round(count / total_teams * 100, 2)}
        for tier, count in score_tier_counter.most_common()
    ]

    # Top 20 Historical High Score Teams
    scored_sorted = sorted(teams_with_scores, key=lambda t: t["history"]["max_score"], reverse=True)
    top_scoring_teams = []
    for t in scored_sorted[:20]:
        h = t["history"]
        top_scoring_teams.append({
            "number": t["number"],
            "name": t.get("name") or "未命名",
            "city": t.get("city") or "Unknown",
            "region": get_region_name(t.get("city")),
            "program": t.get("program_label") or "",
            "max_score": h["max_score"],
            "avg_score": h["avg_score"],
            "best_ranking": h["best_ranking"],
            "awards_count": h["awards_count"],
            "advancements_count": h["advancements_count"],
            "seasons": h["seasons"],
            "events_count": h["events_count"]
        })

    # Top 15 Most Awarded Teams
    awarded_sorted = sorted(teams_with_awards, key=lambda t: t["history"]["awards_count"], reverse=True)
    top_awarded_teams = []
    for t in awarded_sorted[:15]:
        h = t["history"]
        top_awarded_teams.append({
            "number": t["number"],
            "name": t.get("name") or "未命名",
            "city": t.get("city") or "Unknown",
            "region": get_region_name(t.get("city")),
            "awards_count": h["awards_count"],
            "max_score": h["max_score"],
            "advancements_count": h["advancements_count"],
            "seasons": h["seasons"],
            "sample_awards": [a["name"] for a in h.get("awards", [])[:4]]
        })

    # Cross-analysis: Readiness by Experience Tier
    readiness_by_exp = {}
    for tier in ["Veteran (老牌强队)", "Experienced (有参赛经验)", "Rookie (新队伍)"]:
        tier_teams = [t for t in teams if (t.get("history") or {}).get("experience_tier") == tier]
        tier_total = len(tier_teams)
        tier_good = sum(1 for t in tier_teams if t.get("status_v2") == "good")
        readiness_by_exp[tier] = {
            "total": tier_total,
            "ready_count": tier_good,
            "ready_pct": round(tier_good / tier_total * 100, 2) if tier_total else 0
        }

    # Regional History breakdown (Veterans and 400+ Scorers)
    regional_veteran_stats = defaultdict(lambda: {"veterans": 0, "elite_scorers_400plus": 0, "total_teams": 0})
    for t in teams:
        r = get_region_name(t.get("city"))
        regional_veteran_stats[r]["total_teams"] += 1
        h = t.get("history") or {}
        if h.get("experience_tier") == "Veteran (老牌强队)":
            regional_veteran_stats[r]["veterans"] += 1
        if (h.get("max_score") or 0) >= 400:
            regional_veteran_stats[r]["elite_scorers_400plus"] += 1

    regional_history_summary = []
    for reg, st in sorted(regional_veteran_stats.items(), key=lambda x: x[1]["total_teams"], reverse=True):
        regional_history_summary.append({
            "region": reg,
            "total_teams": st["total_teams"],
            "veterans": st["veterans"],
            "veteran_pct": round(st["veterans"] / st["total_teams"] * 100, 2) if st["total_teams"] else 0,
            "elite_scorers_400plus": st["elite_scorers_400plus"],
        })

    history_summary = {
        "teams_with_history_count": len(teams_with_hist),
        "teams_with_history_pct": round(len(teams_with_hist) / total_teams * 100, 2),
        "teams_with_scores_count": len(teams_with_scores),
        "teams_with_scores_pct": round(len(teams_with_scores) / total_teams * 100, 2),
        "teams_with_awards_count": len(teams_with_awards),
        "teams_with_awards_pct": round(len(teams_with_awards) / total_teams * 100, 2),
        "teams_with_advancements_count": len(teams_with_adv),
        "teams_with_championship_count": len(teams_with_champ),
        "experience_tier_stats": experience_tier_stats,
        "score_tier_stats": score_tier_stats,
        "top_scoring_teams": top_scoring_teams,
        "top_awarded_teams": top_awarded_teams,
        "readiness_by_exp": readiness_by_exp,
        "regional_history_summary": regional_history_summary
    }

    results = {
        "total_teams": total_teams,
        "total_unique_cities": total_unique_cities,
        "total_unique_orgs": len(org_counter),
        "program_stats": program_stats,
        "status_stats": status_stats,
        "compliance_stats": compliance_stats,
        "top_cities": top_cities,
        "region_summary": region_summary,
        "challenge_region_summary": challenge_region_summary,
        "top_orgs": top_orgs,
        "org_category_stats": org_category_stats,
        "coaches_stats": coaches_stats,
        "number_stats": number_stats,
        "number_buckets": bucket_counts,
        "prog_status_breakdown": prog_status_breakdown,
        "org_status_breakdown": org_status_breakdown,
        "registered_events_teams": reg_events_count,
        "advancements_breakdown": dict(advancements),
        "history_summary": history_summary
    }

    return results


def generate_markdown_report(data):
    md = []
    md.append("# MyLumi 全部参赛队伍（Public Teams）全景统计与分析报告\n")
    md.append(f"> **数据来源**: MyLumi Public Team API (`https://mylumi.playingatlearning.org/api/team/public/list/`)\n")
    md.append(f"> **队伍总数**: **{data['total_teams']} 支** | **覆盖城市**: **{data['total_unique_cities']} 个** | **归属组织/学校**: **{data['total_unique_orgs']} 个**\n")
    md.append("\n---\n")

    # 1. Executive Summary
    md.append("## 1. 核心关键结论 (Executive Summary)\n")
    good_status = next((s for s in data["status_stats"] if s["status"] == "good"), {"count": 0, "pct": 0})
    md.append(f"1. **队伍就绪度（Readiness）不高，仅约 1/3 队伍完全就绪**：\n")
    md.append(f"   - 达到完全就绪 (`status = good`) 的队伍共 **{good_status['count']} 支 ({good_status['pct']}%)**。\n")
    md.append(f"   - 其余 **{data['total_teams'] - good_status['count']} 支队伍 ({round(100 - good_status['pct'], 2)}%)** 仍卡在审核流或邀请中。\n")
    md.append(f"2. **最大审核阻碍：花名册人数不足、加州指纹审查与队员/教练邀请**：\n")
    md.append(f"   - **53.18% 的队伍花名册未达最低要求**（不满 2 人或尚未录入），成为最普遍的未就绪原因。\n")
    md.append(f"   - **48.17% 的队伍卡在加州指纹背景调查（Fingerprinting）**（LiveScan/MRT）。\n")
    md.append(f"   - **33.91% 的队伍处于 `waiting_invites`**（等待教练/监护人接受系统邀请）。\n")
    md.append(f"3. **项目组别以 FLL Challenge 为主，探索组与创新版稳步发展**：\n")
    md.append(f"   - **FLL Challenge (9-14岁)**: 占绝大多数 **67.24% (349 支队伍)**。\n")
    md.append(f"   - **FLL Explore (6-10岁)**: 占 **22.54% (117 支队伍)**。\n")
    md.append(f"   - **Future Edition (各学段创新试点)**: 累计 **10.22% (53 支队伍)**。\n")
    md.append(f"4. **组织结构呈现「家庭社区为主、超级大社团引领」的二元格局**：\n")
    md.append(f"   - **家庭/社区独立队伍 (Family/Community)**: 占 **38.92% (202 队)**，是第一大主力。\n")
    md.append(f"   - **Piedmont Makers (皮埃蒙特创客)**: 拥有多达 **140 队 (26.97%)**，是全加州规模最大的单一机器人社团。\n")
    md.append(f"   - **公立/私立学校**: 占 **23.51% (122 队)**。\n")
    md.append(f"5. **地域高度集中在东湾与南湾/硅谷**：\n")
    md.append(f"   - 东湾 (Oakland, Piedmont, Fremont 等) 占 **49.71% (258 队)**。\n")
    md.append(f"   - 南湾/硅谷 (San Jose, Santa Clara, Mountain View, Sunnyvale 等) 占 **33.33% (173 队)**。\n")
    md.append("\n---\n")

    # 2. Program Breakdown
    md.append("## 2. 赛事项目组别分布 (Program Breakdown)\n")
    md.append("| 比赛项目 (Program) | 队伍数 (Count) | 占比 (Percentage) | 状态 |")
    md.append("| :--- | :---: | :---: | :--- |")
    for p in data["program_stats"]:
        md.append(f"| **{p['program']}** | {p['count']} | {p['pct']}% | {'主力组别' if p['count'] > 100 else '创新/探索'} |")
    md.append("\n")

    # 3. Team Status & Compliance Funnel
    md.append("## 3. 队伍合规与就绪度诊断 (Compliance & Readiness)\n")
    md.append("### 3.1 总体就绪状态 (Status v2 分布)\n")
    md.append("| 状态代码 (Status) | 解释说明 | 队伍数 | 占比 |")
    md.append("| :--- | :--- | :---: | :---: |")
    status_desc = {
        "good": "✅ 完全合规就绪 (可参加正式赛事/抽签)",
        "waiting_invites": "⏳ 等待邀请接受 (队员/教练已发出邀请但未确认)",
        "pending_fingerprinting": "⚠️ 卡在加州指纹背景审查 (LiveScan / MRT 缺失)",
        "waiting_members": "👥 队伍人数不足 (未达 2 名正式学生队员最低门槛)",
        "pending_national_screening": "🔍 卡在 FIRST 全美背景调查 (Screening 待处理)",
        "waiting_jotform": "📝 线上免责表单/Jotform 待签署",
        "roster_overload": "🚫 花名册超员 (超出官方人数上限)",
    }
    for s in data["status_stats"]:
        desc = status_desc.get(s["status"], "未知状态")
        md.append(f"| `{s['status']}` | {desc} | {s['count']} | {s['pct']}% |")
    md.append("\n")

    md.append("### 3.2 五大关键合规环节通过率\n")
    md.append("| 审核环节 (Compliance Step) | 通过队伍数 | 通过率 (Pass Rate) | 未完成/失败数 | 未完成比例 |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")
    comp_labels = {
        "coaches": "👨‍🏫 教练人数要求 (至少2位教练)",
        "screening": "🛡️ FIRST 全美背景审查 (Screening)",
        "fingerprinting": "🖐️ 加州司法部指纹背景调查 (Fingerprinting)",
        "agreements": "📑 家长/教练免责协议 (Jotform / Agreements)",
        "roster_status": "📋 学生队员花名册要求 (至少2人，未超员)",
    }
    for k, label in comp_labels.items():
        cs = data["compliance_stats"][k]
        md.append(f"| {label} | {cs['good_count']} | **{cs['good_pct']}%** | {cs['fail_count']} | {cs['fail_pct']}% |")
    md.append("\n")

    # 4. Regional & City Distribution
    md.append("## 4. 地域与区域分布 (Regional & Geographic Distribution)\n")
    md.append("### 4.1 全量队伍按大区域队伍数量分布 (All 519 Teams)\n")
    md.append("| 大区域 (Region) | 队伍数量 | 占比 (All Teams) | 包含的核心代表城市 |")
    md.append("| :--- | :---: | :---: | :--- |")
    reg_cities = {
        "东湾 (East Bay)": "Oakland, Piedmont, Fremont, Dublin, Pleasanton, San Ramon, Berkeley, Castro Valley, Hayward...",
        "南湾 / 硅谷 (South Bay)": "San Jose, Santa Clara, Sunnyvale, Mountain View, Saratoga, Cupertino, Los Altos, Milpitas, Palo Alto...",
        "半岛与旧金山 (Peninsula & SF)": "San Francisco, Burlingame, Hillsborough, San Carlos, San Mateo, Menlo Park, Belmont...",
        "首府圈与中谷 (Sacramento & Valley)": "Folsom, Mountain House, Sacramento, El Dorado Hills, Tracy, Lathrop, Modesto, Roseville...",
        "北湾 (North Bay)": "Kentfield (Marin County) 等",
        "其他 / 外围区域 (Other)": "其他边缘城市及未标明区域"
    }
    for r in data["region_summary"]:
        md.append(f"| **{r['region']}** | {r['count']} 队 | **{r['pct']}%** | {reg_cities.get(r['region'], '')} |")
    md.append("\n")

    md.append("### 4.2 FLL-Challenge 核心主力组按区域队伍数量分布 (Challenge 349 Teams)\n")
    md.append("| 大区域 (Region) | Challenge 队伍数 | 占 Challenge 比例 | 区域主力特征 |")
    md.append("| :--- | :---: | :---: | :--- |")
    reg_features = {
        "南湾 / 硅谷 (South Bay)": "🏆 跃升为 Challenge 第一主力！硅谷科技学区与独立创客汇聚",
        "东湾 (East Bay)": "🥈 Challenge 第二主力，拥有老牌社区队与创客俱乐部",
        "半岛与旧金山 (Peninsula & SF)": "🥉 集中在旧金山私校与半岛学区",
        "首府圈与中谷 (Sacramento & Valley)": "第四主力，Folsom / Mountain House 增长迅速",
        "北湾 (North Bay)": "Marin County 等低密度区域",
        "其他 / 外围区域 (Other)": "外围零星分布"
    }
    for r in data.get("challenge_region_summary", []):
        md.append(f"| **{r['region']}** | {r['count']} 队 | **{r['pct']}%** | {reg_features.get(r['region'], '')} |")
    md.append("\n")

    md.append("### 4.2 队伍最多的 Top 15 城市\n")
    md.append("| 排名 | 城市 (City) | 队伍数 | 占总队伍比例 |")
    md.append("| :---: | :--- | :---: | :---: |")
    for i, c in enumerate(data["top_cities"][:15], 1):
        md.append(f"| {i} | **{c['city']}** | {c['count']} | {c['pct']}% |")
    md.append("\n")

    # 5. Organizations Breakdown
    md.append("## 5. 组织机构与队伍性质结构 (Organization Breakdown)\n")
    md.append("### 5.1 组织性质大类分类\n")
    md.append("| 组织类别 (Category) | 队伍数 | 占比 | 特征说明 |")
    md.append("| :--- | :---: | :---: | :--- |")
    for o in data["org_category_stats"]:
        note = ""
        if o["category"] == "Family/Community":
            note = "家长自发组建或社区邻里团队，灵活性高但指纹审查容易掉队"
        elif o["category"] == "Piedmont Makers":
            note = "Piedmont 区域极具影响力的创客公益联盟，建制化规模极大"
        elif "School" in o["category"]:
            note = "公立学区或私立学校校队，合规受学区流程制约"
        else:
            note = "课外科技机构、俱乐部或独立培训中心"
        md.append(f"| **{o['category']}** | {o['count']} | {o['pct']}% | {note} |")
    md.append("\n")

    md.append("### 5.2 队伍最多的 Top 10 具体机构/学校\n")
    md.append("| 排名 | 机构/学校名称 (Org Name) | 队伍数 | 占总队伍比例 |")
    md.append("| :---: | :--- | :---: | :---: |")
    for i, org in enumerate(data["top_orgs"][:10], 1):
        md.append(f"| {i} | **{org['org_name']}** | {org['count']} | {org['pct']}% |")
    md.append("\n")

    # 6. Team Vintage & Age (Team Number Analysis)
    md.append("## 6. 队伍编号与资历分析 (Team Number & Vintage)\n")
    ns = data["number_stats"]
    md.append(f"- **最低队伍编号**: `#{ns['min']}` (Matsuyama RoboPines，极早期老牌老队)")
    md.append(f"- **最高队伍编号**: `#{ns['max']}` (今年全新注册队伍)")
    md.append(f"- **编号中位数**: `#{ns['median']}` | **编号平均数**: `#{ns['mean']}`\n")

    md.append("| 编号区间 (Team Number Range) | 代表建队年代 / 阶段 | 队伍数量 | 占比 |")
    md.append("| :--- | :--- | :---: | :---: |")
    for b in data["number_buckets"]:
        md.append(f"| `{b['range_label']}` | 历史资历 | {b['count']} | {b['pct']}% |")
    md.append("\n")

    # 7. Coaches Configuration
    md.append("## 7. 教练配置分析 (Coaches Configuration)\n")
    md.append("| 教练人数 (Coaches Count) | 队伍数 | 占比 | 官方标准评估 |")
    md.append("| :---: | :---: | :---: | :--- |")
    for c in data["coaches_stats"]:
        eval_txt = "✅ 标配（2名成人教练）" if c["coaches_count"] == 2 else \
                   ("⚠️ 警告：不足2人，不符青年保护政策" if c["coaches_count"] < 2 else "➕ 增配副教练/助理")
        md.append(f"| **{c['coaches_count']} 人** | {c['teams']} | {c['pct']}% | {eval_txt} |")
    md.append("\n")

    # 8. Historical Performance & Veteran Analysis
    hs = data.get("history_summary", {})
    md.append("## 8. 队伍历史战绩与历届成绩综合分析 (Historical Performance & Veteran Analysis)\n")
    md.append(f"> **数据整合来源**: 关联以往官方赛事库 (`data/mylumi.db` 中 `events`, `scores`, `awards`, `event_teams` 表)\n")
    md.append(f"- **历史参赛战队覆盖率**: **{hs.get('teams_with_history_count')} 支 / 519 支 ({hs.get('teams_with_history_pct')}%)** 拥有官方参赛记录。\n")
    md.append(f"- **机器人比赛得分记录**: **{hs.get('teams_with_scores_count')} 支 ({hs.get('teams_with_scores_pct')}%)** 记录有真实对战最高分。\n")
    md.append(f"- **斩获官方奖项队伍**: **{hs.get('teams_with_awards_count')} 支 ({hs.get('teams_with_awards_pct')}%)** 斩获过冠亚季军、核心价值或机器人设计等奖项。\n")
    md.append(f"- **成功晋级更高级别队伍**: **{hs.get('teams_with_advancements_count')} 支** 在往届资格赛中成功晋级。\n")
    md.append(f"- **进军州锦标赛 (Championship) 队伍**: **{hs.get('teams_with_championship_count')} 支** 拥有锦标赛终极决战经历。\n\n")

    md.append("### 8.1 参赛队伍资历梯度分布 (Experience Tier)\n")
    md.append("| 资历梯队 (Tier) | 队伍数量 | 占比 | 梯队特征描述 |")
    md.append("| :--- | :---: | :---: | :--- |")
    tier_desc = {
        "Veteran (老牌强队)": "跨多赛季参赛、晋级过 Championship 或斩获多项大奖的老牌王者",
        "Experienced (有参赛经验)": "参加过往届赛事，具备完整正赛与机器人调试经验",
        "Rookie (新队伍)": "今年新注册或首次加入 MyLumi 系统的初生战队"
    }
    for et in hs.get("experience_tier_stats", []):
        md.append(f"| **{et['tier']}** | {et['count']} 队 | **{et['pct']}%** | {tier_desc.get(et['tier'], '-')} |")
    md.append("\n")

    md.append("### 8.2 历史战绩得分实力梯队 (Score Tier)\n")
    md.append("| 历史最高分梯队 | 队伍数量 | 占总队伍比 | 战力梯队特征 |")
    md.append("| :--- | :---: | :---: | :--- |")
    score_desc = {
        "500+ (争冠顶尖)": "🔥 绝对争冠梯队，场地任务全清或近乎满分",
        "400-499 (一档强队)": "⚡ 具备稳进 Championship 实力的一档种子队",
        "300-399 (中坚晋级)": "💪 地区晋级核心主力，具备稳健的机械与编程能力",
        "<300 (入门发展)": "🌱 基础任务得分梯队，仍在成长与打磨中",
        "暂无历史成绩": "新队伍或往届仅参加 Explore 组"
    }
    for st in hs.get("score_tier_stats", []):
        md.append(f"| **{st['tier']}** | {st['count']} 队 | **{st['pct']}%** | {score_desc.get(st['tier'], '-')} |")
    md.append("\n")

    md.append("### 8.3 机器人对战生涯最高分排行榜 Top 15 (Top Career High Scores)\n")
    md.append("| 排名 | 队号 | 队伍名称 | 城市 (大区域) | 生涯最高分 | 历史平均分 | 历史最佳排名 | 累计奖项 | 晋级次数 | 参赛赛季 |")
    md.append("| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    for idx, t in enumerate(hs.get("top_scoring_teams", [])[:15], 1):
        md.append(f"| {idx} | `#{t['number']}` | **{t['name']}** | {t['city']} ({t['region'].split(' ')[0]}) | **{t['max_score']}** | {t['avg_score'] or '-'} | 第 {t['best_ranking'] or '-'} 名 | 🏆 {t['awards_count']} | 🚀 {t['advancements_count']} | {', '.join(t['seasons'])} |")
    md.append("\n")

    md.append("### 8.4 历史荣誉斩获最多战队 Top 10 (Most Awarded Teams)\n")
    md.append("| 排名 | 队号 | 队伍名称 | 城市 | 奖项总数 | 生涯最高分 | 晋级次数 | 代表奖项 |")
    md.append("| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- |")
    for idx, t in enumerate(hs.get("top_awarded_teams", [])[:10], 1):
        sample_str = "、".join(t["sample_awards"][:3]) if t["sample_awards"] else "-"
        md.append(f"| {idx} | `#{t['number']}` | **{t['name']}** | {t['city']} | **🏆 {t['awards_count']} 个** | {t['max_score'] or '-'} 分 | 🚀 {t['advancements_count']} 次 | {sample_str} |")
    md.append("\n")

    md.append("### 8.5 资历与当前合规就绪率的交叉分析 (Cross-Analysis: Experience vs Readiness)\n")
    md.append("| 队伍资历梯队 | 队伍总数 | 全部就绪队伍 (Good) | 完全就绪率 (Readiness) | 深度洞察 |")
    md.append("| :--- | :---: | :---: | :---: | :--- |")
    rbe = hs.get("readiness_by_exp", {})
    v_info = rbe.get("Veteran (老牌强队)", {})
    e_info = rbe.get("Experienced (有参赛经验)", {})
    r_info = rbe.get("Rookie (新队伍)", {})
    md.append(f"| **Veteran (老牌强队)** | {v_info.get('total', 0)} | {v_info.get('ready_count', 0)} | **{v_info.get('ready_pct', 0)}%** | 老牌队伍流程轻车熟路，教练指纹背景常驻有效，就绪率显著高于平均 |")
    md.append(f"| **Experienced (有经验)** | {e_info.get('total', 0)} | {e_info.get('ready_count', 0)} | **{e_info.get('ready_pct', 0)}%** | 中坚队伍就绪度平稳 |")
    md.append(f"| **Rookie (新队伍)** | {r_info.get('total', 0)} | {r_info.get('ready_count', 0)} | **{r_info.get('ready_pct', 0)}%** | 新手队伍大幅拖累整体就绪率，主要卡在加州指纹预约与队员邀请 |")
    md.append("\n")

    # 9. Actionable Insights for Teams & Organizers
    md.append("## 9. 给参赛队伍与组委会的行动建议 (Actionable Insights)\n")
    md.append("1. **老牌队伍示范带头与结对帮扶 (Buddy System)**：\n")
    md.append(f"   - 84 支 Veteran 战队的合规就绪率显著领先，建议组委会引导老牌队伍在社区分享 LiveScan 加州指纹和 Roster 快速达标经验，帮带 292 支 Rookie 新战队。\n")
    md.append("2. **重点关注 `waiting_invites` 的 176 支队伍**：\n")
    md.append("   - 这是最容易转为 `good` 的队伍群体。绝大多数只需教练或家长登录 FIRST/MyLumi 邮箱确认接受邀请，即可变为可用状态。\n")
    md.append("3. **关注单教练（69 队）与无教练（20 队）的合规风险**：\n")
    md.append("   - 共有 89 队不足 2 名教练，违反了 FIRST YPP（Youth Protection Policy）底线要求，需尽快增设第二教练。\n")
    md.append("4. **高分战队提早规划选拔赛赛站**：\n")
    md.append("   - 历史 400+ 顶尖队（如 64638, 60868, 60085 等）实力强劲，建议关注各 Qualifier 赛站容量，及早完成全部审核锁定参赛名额。\n")

    return "\n".join(md)


def main():
    teams = load_teams()
    results = analyze(teams)

    # Save JSON analysis
    with open(ANALYSIS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved analysis JSON to {ANALYSIS_JSON}")

    # Save Markdown report
    report_md = generate_markdown_report(results)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Saved markdown report to {REPORT_MD}")

    # Export for web viewer if web/ directory exists
    web_dir = Path(__file__).resolve().parent / "web"
    if web_dir.exists():
        teams_js_path = web_dir / "teams_data.js"
        with open(teams_js_path, "w", encoding="utf-8") as f:
            f.write("window.PUBLIC_TEAMS_ANALYSIS = " + json.dumps(results, ensure_ascii=False) + ";\n")
            f.write("window.PUBLIC_TEAMS_LIST = " + json.dumps(teams, ensure_ascii=False) + ";\n")
        print(f"Saved Web Data to {teams_js_path}")

    # Print summary to console
    print("\n" + "="*60)
    print("MYLUMI PUBLIC TEAMS STATISTICAL SUMMARY")
    print("="*60)
    print(f"Total Teams Crawled: {results['total_teams']}")
    print(f"Unique Cities: {results['total_unique_cities']}")
    print(f"Unique Organizations: {results['total_unique_orgs']}")
    print("\n[PROGRAMS]:")
    for p in results["program_stats"]:
        print(f"  - {p['program']:35s}: {p['count']:3d} ({p['pct']}%)")
    print("\n[READINESS STATUS (status_v2)]:")
    for s in results["status_stats"]:
        print(f"  - {s['status']:28s}: {s['count']:3d} ({s['pct']}%)")
    print("\n[COMPLIANCE CHECKPOINTS (Good %)]:")
    for k, cs in results["compliance_stats"].items():
        print(f"  - {k:20s}: {cs['good_count']:3d} passed ({cs['good_pct']}%) | {cs['fail_count']:3d} pending ({cs['fail_pct']}%)")
    print("\n[TOP 5 CITIES]:")
    for c in results["top_cities"][:5]:
        print(f"  - {c['city']:20s}: {c['count']:3d} ({c['pct']}%)")
    print("\n[ORGANIZATIONS CATEGORIES]:")
    for o in results["org_category_stats"]:
        print(f"  - {o['category']:30s}: {o['count']:3d} ({o['pct']}%)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
