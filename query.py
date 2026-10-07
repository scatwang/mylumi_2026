#!/usr/bin/env python3
"""
MyLumi Data Query & Analysis Helper
-----------------------------------
A quick CLI tool to inspect and query the crawled MyLumi dataset.

Examples:
  python3 query.py summary
  python3 query.py seasons
  python3 query.py events --season 2025
  python3 query.py team 55496
  python3 query.py leaderboard --season 2024
  python3 query.py awards --team 64638
  python3 query.py sql "SELECT name, city, capacity FROM events WHERE event_status = 'open'"
"""

import argparse
from pathlib import Path
import sqlite3
import sys

DB_PATH = Path(__file__).parent / "data" / "mylumi.db"


def get_conn():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}. Run 'python3 crawler.py' first.")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def show_summary():
    conn = get_conn()
    c = conn.cursor()
    print("=" * 60)
    print("           MyLumi Dataset Summary")
    print("=" * 60)

    tables = ["seasons", "events", "scores", "awards", "event_teams", "schedules"]
    for t in tables:
        c.execute(f"SELECT count(*) FROM {t}")
        cnt = c.fetchone()[0]
        print(f"  {t:15s}: {cnt:6d} records")

    print("\nEvents by Season:")
    c.execute("""
        SELECT COALESCE(season, 'Unknown'), count(*),
               SUM(CASE WHEN event_status = 'open' THEN 1 ELSE 0 END) as open_cnt,
               SUM(CASE WHEN event_status = 'closed' THEN 1 ELSE 0 END) as closed_cnt,
               SUM(CASE WHEN event_status = 'canceled' THEN 1 ELSE 0 END) as canceled_cnt
        FROM events
        GROUP BY season
        ORDER BY season
    """)
    for row in c.fetchall():
        s_name, total, open_c, closed_c, canc_c = row
        print(f"  - {s_name:32s}: {total:2d} events ({open_c} open, {closed_c} closed, {canc_c} canceled)")
    print("=" * 60)


def show_seasons():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, year, name, program_abbreviation, event_count FROM seasons ORDER BY year DESC")
    print(f"{'ID':<4} {'Year':<6} {'Name':<25} {'Program':<15} {'Events':<6}")
    print("-" * 60)
    for r in c.fetchall():
        print(f"{r[0]:<4} {r[1]:<6} {r[2]:<25} {r[3]:<15} {r[4]:<6}")


def show_events(season_filter=None, status_filter=None):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT id, name, season, event_status, start_time, total_registered, capacity FROM events WHERE 1=1"
    params = []
    if season_filter:
        query += " AND season LIKE ?"
        params.append(f"%{season_filter}%")
    if status_filter:
        query += " AND event_status = ?"
        params.append(status_filter)
    query += " ORDER BY id DESC"

    c.execute(query, params)
    rows = c.fetchall()
    print(f"Found {len(rows)} events:")
    print(f"{'ID':<5} {'Status':<10} {'Start Date':<12} {'Reg/Cap':<10} {'Name'}")
    print("-" * 75)
    for r in rows:
        date_str = (r[4] or "")[:10]
        reg_cap = f"{r[5] or 0}/{r[6] or 0}"
        print(f"{r[0]:<5} {r[3]:<10} {date_str:<12} {reg_cap:<10} {r[1]}")


def show_team(team_query):
    conn = get_conn()
    c = conn.cursor()
    # Find matching teams
    c.execute("""
        SELECT DISTINCT team_number, team_name, city, org_name
        FROM event_teams
        WHERE team_number = ? OR team_name LIKE ?
    """, (team_query if team_query.isdigit() else -1, f"%{team_query}%"))
    teams = c.fetchall()

    if not teams:
        print(f"No team found matching '{team_query}'.")
        return

    for t_num, t_name, city, org in teams:
        print("=" * 65)
        print(f"Team #{t_num}: {t_name}")
        print(f"Location: {city or 'N/A'} | Organization: {org or 'N/A'}")
        print("-" * 65)

        # Events participated
        print("Participated Events:")
        c.execute("""
            SELECT e.id, e.season, e.name, et.advancing_to_next_level
            FROM event_teams et
            JOIN events e ON et.event_id = e.id
            WHERE et.team_number = ?
            ORDER BY e.start_time
        """, (t_num,))
        for eid, season, ename, adv in c.fetchall():
            adv_str = " (ADVANCED)" if adv else ""
            print(f"  - [{eid}] {season}: {ename}{adv_str}")

        # Scores
        print("\nScores:")
        c.execute("""
            SELECT e.name, s.ranking, s.ordinal, s.highest_score, s.round_1, s.round_2, s.round_3
            FROM scores s
            JOIN events e ON s.event_id = e.id
            WHERE s.team_number = ?
            ORDER BY e.start_time
        """, (t_num,))
        scores = c.fetchall()
        if scores:
            for ename, rank, ord_, highest, r1, r2, r3 in scores:
                print(f"  - {ename[:35]:35s} | Rank: {ord_ or rank} | High: {highest} | Rounds: [{r1}, {r2}, {r3}]")
        else:
            print("  No score records found.")

        # Awards
        print("\nAwards:")
        c.execute("""
            SELECT e.name, a.award_name, a.category, a.place_number
            FROM awards a
            JOIN events e ON a.event_id = e.id
            WHERE a.team_number = ?
            ORDER BY e.start_time
        """, (t_num,))
        awards = c.fetchall()
        if awards:
            for ename, aw_name, cat, place in awards:
                place_str = f" #{place}" if place else ""
                print(f"  - {aw_name}{place_str} ({cat}) @ {ename}")
        else:
            print("  No awards found.")
        print("=" * 65 + "\n")


def show_leaderboard(season=None, top_n=20):
    conn = get_conn()
    c = conn.cursor()
    query = """
        SELECT s.team_number, s.team_name, MAX(s.highest_score) as max_score,
               e.season, e.name as event_name
        FROM scores s
        JOIN events e ON s.event_id = e.id
        WHERE 1=1
    """
    params = []
    if season:
        query += " AND e.season LIKE ?"
        params.append(f"%{season}%")
    query += """
        GROUP BY s.team_number
        ORDER BY max_score DESC
        LIMIT ?
    """
    params.append(top_n)

    c.execute(query, params)
    rows = c.fetchall()
    season_title = f" (Season: {season})" if season else " (All Time)"
    print(f"\nTop {len(rows)} Highest Robot Scores{season_title}:")
    print(f"{'Rank':<5} {'Team #':<8} {'Score':<8} {'Team Name':<28} {'Event / Season'}")
    print("-" * 80)
    for idx, (t_num, t_name, score, s_name, e_name) in enumerate(rows, 1):
        print(f"{idx:<5} {t_num:<8} {score:<8} {t_name[:26]:<28} {s_name} - {e_name[:25]}")


def run_sql(query):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query)
    columns = [desc[0] for desc in c.description] if c.description else []
    rows = c.fetchall()
    if columns:
        print(" | ".join(f"{col:<15}" for col in columns))
        print("-" * (len(columns) * 18))
    for r in rows:
        print(" | ".join(f"{str(v):<15}" for v in r))
    print(f"\n({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="MyLumi Dataset Inspector")
    subparsers = parser.add_subparsers(dest="command")

    # summary
    subparsers.add_parser("summary", help="Show overview of dataset")

    # seasons
    subparsers.add_parser("seasons", help="List all seasons")

    # events
    p_events = subparsers.add_parser("events", help="List events")
    p_events.add_argument("--season", help="Filter by season (e.g. 2024, 2025, BIOGLOW)")
    p_events.add_argument("--status", choices=["open", "closed", "canceled"], help="Filter by status")

    # team
    p_team = subparsers.add_parser("team", help="Inspect a specific team's history")
    p_team.add_argument("query", help="Team number or name")

    # leaderboard
    p_lb = subparsers.add_parser("leaderboard", help="Top robot scores")
    p_lb.add_argument("--season", help="Filter by season (e.g. 2024, 2025)")
    p_lb.add_argument("-n", type=int, default=20, help="Number of teams to show (default: 20)")

    # sql
    p_sql = subparsers.add_parser("sql", help="Run arbitrary SQL query")
    p_sql.add_argument("query", help="SQL string")

    args = parser.parse_args()

    if args.command == "summary" or args.command is None:
        show_summary()
    elif args.command == "seasons":
        show_seasons()
    elif args.command == "events":
        show_events(season_filter=args.season, status_filter=args.status)
    elif args.command == "team":
        show_team(args.query)
    elif args.command == "leaderboard":
        show_leaderboard(season=args.season, top_n=args.n)
    elif args.command == "sql":
        run_sql(args.query)


if __name__ == "__main__":
    main()
