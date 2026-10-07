# MyLumi Event Data Crawler & Dataset

爬取自 [MyLumi (Playing at Learning)](https://mylumi.playingatlearning.org/) 的全量比赛（Events）及相关数据（包含过去所有归档比赛与当前新赛季比赛）。

---

## 📊 数据总览

已成功爬取并解析 **141 场比赛**，覆盖 2023 ~ 2026 四个赛季（包括 Challenge 与 Explore 两大组别）：

| 数据表 | 记录数 | 说明 |
| :--- | :--- | :--- |
| **`events`** | **141** | 过去及现在的所有赛事（ID、名称、赛季、状态、时间、地点、容量等） |
| **`scores`** | **1,185** | 各赛事机器得分（排名、单轮得分 Round 1~4、最高分 Highest、裁判评价等） |
| **`awards`** | **542** | 获奖信息（冠军奖、核心奖项、组别、获奖队伍/个人、机构、城市） |
| **`event_teams`** | **1,825** | 各赛事参赛队伍名单、队伍编号、名称、晋级情况（Advancement） |
| **`schedules`** | **6,261** | 比赛及裁判面试日程（时间、场地/房间、时长、练习赛标识等） |
| **`seasons`** | **6** | 赛季元数据（年度、赛季名称、赛事总数、Logo路径等） |

### 赛季分布
- **`2023 - MASTERPIECE (Challenge)`**: 28 场
- **`2023 - MASTERPIECE (Explore)`**: 11 场
- **`2024 - SUBMERGED (Challenge)`**: 31 场
- **`2024 - SUBMERGED (Explore)`**: 17 场
- **`2025 - UNEARTHED (Challenge)`**: 31 场
- **`2025 - UNEARTHED (Explore)`**: 9 场
- **`2026 - BIOGLOW (Challenge)`** (当前赛季): 14 场

---

## 📁 本地数据存储结构

数据均保存在本地 `data/` 目录下，提供三种格式：

```text
mylumi_crawler/
├── crawler.py           # 核心爬虫与数据转换 ETL 脚本
├── query.py             # 快速数据查询与分析 CLI 工具
├── data/
│   ├── mylumi.db        # 完整 SQLite 数据库（已建索引，适合高频分析与 SQL 查询）
│   ├── csv/             # 导出的 CSV 数据表（适合 Pandas、Excel、Numbers 打开）
│   │   ├── events.csv
│   │   ├── scores.csv
│   │   ├── awards.csv
│   │   ├── teams.csv
│   │   └── schedules.csv
│   └── raw/             # 原始 JSON 数据归档（1:1 保存 API 完整原始字段）
│       ├── seasons.json
│       ├── events_active.json
│       ├── events_archive.json
│       └── events/
│           ├── 1/
│           │   ├── details.json
│           │   ├── scores.json
│           │   ├── awards.json
│           │   ├── teams.json
│           │   └── schedules.json
│           ├── ...
│           └── 314/
```

---

## 🚀 使用指南

### 1. 重新爬取或增量更新
脚本自带缓存机制，默认跳过已下载事件；如需增量爬取新赛事或强制更新：
```bash
# 默认增量更新（自动探测新事件，已存在的自动复用）
python3 crawler.py

# 调整并发线程数（默认 5）
python3 crawler.py --workers 8

# 强制重新下载所有数据
python3 crawler.py --force

# 仅从本地 raw JSON 重新生成 SQLite 数据库与 CSV
python3 crawler.py --export-only
```

### 2. 快速查询 CLI (`query.py`)
提供了便捷的查询命令：
```bash
# 1. 查看整体统计信息
python3 query.py summary

# 2. 列出各赛季
python3 query.py seasons

# 3. 按赛季过滤比赛（如 2025 或 BIOGLOW）
python3 query.py events --season 2025
python3 query.py events --season BIOGLOW

# 4. 查队伍历史成绩与获奖记录（支持队伍号或队名模糊匹配）
python3 query.py team 64638
python3 query.py team "Brain Bot"

# 5. 查看机器人得分排行榜（支持按赛季）
python3 query.py leaderboard -n 10
python3 query.py leaderboard --season 2024 -n 10

# 6. 直接执行自定义 SQL
python3 query.py sql "SELECT name, venue_city, start_time FROM events WHERE season LIKE '%BIOGLOW%'"
```

---

## 🐍 编写后续分析脚本示例 (Python)

你可以直接使用 Python 内置的 `sqlite3` 或 `pandas` 进行分析：

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/mylumi.db")

# 示例 1: 查询各赛季各队平均最高得分前 10
df_scores = pd.read_sql_query("""
    SELECT s.team_number, s.team_name, e.season, AVG(s.highest_score) as avg_high_score
    FROM scores s
    JOIN events e ON s.event_id = e.id
    GROUP BY s.team_number, e.season
    ORDER BY avg_high_score DESC
    LIMIT 10;
""", conn)
print(df_scores)

# 示例 2: 查询获 Champions Award 最多的队伍
df_champions = pd.read_sql_query("""
    SELECT team_number, team_name, count(*) as champions_count
    FROM awards
    WHERE award_name LIKE "%Champion%"
    GROUP BY team_number
    ORDER BY champions_count DESC;
""", conn)
print(df_champions)
```
