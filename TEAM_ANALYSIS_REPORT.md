# MyLumi 全部参赛队伍（Public Teams）全景统计与分析报告

> **数据来源**: MyLumi Public Team API (`https://mylumi.playingatlearning.org/api/team/public/list/`)

> **队伍总数**: **530 支** | **覆盖城市**: **72 个** | **归属组织/学校**: **108 个**


---

## 1. 核心关键结论 (Executive Summary)

1. **队伍就绪度（Readiness）不高，仅约 1/3 队伍完全就绪**：

   - 达到完全就绪 (`status = good`) 的队伍共 **203 支 (38.3%)**。

   - 其余 **327 支队伍 (61.7%)** 仍卡在审核流或邀请中。

2. **最大审核阻碍：花名册人数不足、加州指纹审查与队员/教练邀请**：

   - **53.18% 的队伍花名册未达最低要求**（不满 2 人或尚未录入），成为最普遍的未就绪原因。

   - **48.17% 的队伍卡在加州指纹背景调查（Fingerprinting）**（LiveScan/MRT）。

   - **33.91% 的队伍处于 `waiting_invites`**（等待教练/监护人接受系统邀请）。

3. **项目组别以 FLL Challenge 为主，探索组与创新版稳步发展**：

   - **FLL Challenge (9-14岁)**: 占绝大多数 **67.24% (349 支队伍)**。

   - **FLL Explore (6-10岁)**: 占 **22.54% (117 支队伍)**。

   - **Future Edition (各学段创新试点)**: 累计 **10.22% (53 支队伍)**。

4. **组织结构呈现「家庭社区为主、超级大社团引领」的二元格局**：

   - **家庭/社区独立队伍 (Family/Community)**: 占 **38.92% (202 队)**，是第一大主力。

   - **Piedmont Makers (皮埃蒙特创客)**: 拥有多达 **140 队 (26.97%)**，是全加州规模最大的单一机器人社团。

   - **公立/私立学校**: 占 **23.51% (122 队)**。

5. **地域高度集中在东湾与南湾/硅谷**：

   - 东湾 (Oakland, Piedmont, Fremont 等) 占 **49.71% (258 队)**。

   - 南湾/硅谷 (San Jose, Santa Clara, Mountain View, Sunnyvale 等) 占 **33.33% (173 队)**。


---

## 2. 赛事项目组别分布 (Program Breakdown)

| 比赛项目 (Program) | 队伍数 (Count) | 占比 (Percentage) | 状态 |
| :--- | :---: | :---: | :--- |
| **FIRST LEGO League: Challenge** | 354 | 66.79% | 主力组别 |
| **FIRST LEGO League: Explore** | 120 | 22.64% | 主力组别 |
| **FIRST LEGO League: Future Edition 3-5** | 28 | 5.28% | 创新/探索 |
| **FIRST LEGO League: Future Edition 6-8** | 25 | 4.72% | 创新/探索 |
| **FIRST LEGO League: Future Edition K-2** | 3 | 0.57% | 创新/探索 |


## 3. 队伍合规与就绪度诊断 (Compliance & Readiness)

### 3.1 总体就绪状态 (Status v2 分布)

| 状态代码 (Status) | 解释说明 | 队伍数 | 占比 |
| :--- | :--- | :---: | :---: |
| `good` | ✅ 完全合规就绪 (可参加正式赛事/抽签) | 203 | 38.3% |
| `waiting_invites` | ⏳ 等待邀请接受 (队员/教练已发出邀请但未确认) | 175 | 33.02% |
| `pending_fingerprinting` | ⚠️ 卡在加州指纹背景审查 (LiveScan / MRT 缺失) | 84 | 15.85% |
| `waiting_members` | 👥 队伍人数不足 (未达 2 名正式学生队员最低门槛) | 30 | 5.66% |
| `pending_national_screening` | 🔍 卡在 FIRST 全美背景调查 (Screening 待处理) | 21 | 3.96% |
| `waiting_jotform` | 📝 线上免责表单/Jotform 待签署 | 11 | 2.08% |
| `roster_overload` | 🚫 花名册超员 (超出官方人数上限) | 6 | 1.13% |


### 3.2 五大关键合规环节通过率

| 审核环节 (Compliance Step) | 通过队伍数 | 通过率 (Pass Rate) | 未完成/失败数 | 未完成比例 |
| :--- | :---: | :---: | :---: | :---: |
| 👨‍🏫 教练人数要求 (至少2位教练) | 423 | **79.81%** | 107 | 20.19% |
| 🛡️ FIRST 全美背景审查 (Screening) | 333 | **62.83%** | 197 | 37.17% |
| 🖐️ 加州司法部指纹背景调查 (Fingerprinting) | 286 | **53.96%** | 244 | 46.04% |
| 📑 家长/教练免责协议 (Jotform / Agreements) | 348 | **65.66%** | 182 | 34.34% |
| 📋 学生队员花名册要求 (至少2人，未超员) | 260 | **49.06%** | 270 | 50.94% |


## 4. 地域与区域分布 (Regional & Geographic Distribution)

### 4.1 全量队伍按大区域队伍数量分布 (All 519 Teams)

| 大区域 (Region) | 队伍数量 | 占比 (All Teams) | 包含的核心代表城市 |
| :--- | :---: | :---: | :--- |
| **东湾 (East Bay)** | 263 队 | **49.62%** | Oakland, Piedmont, Fremont, Dublin, Pleasanton, San Ramon, Berkeley, Castro Valley, Hayward... |
| **南湾 / 硅谷 (South Bay)** | 179 队 | **33.77%** | San Jose, Santa Clara, Sunnyvale, Mountain View, Saratoga, Cupertino, Los Altos, Milpitas, Palo Alto... |
| **半岛与旧金山 (Peninsula & SF)** | 47 队 | **8.87%** | San Francisco, Burlingame, Hillsborough, San Carlos, San Mateo, Menlo Park, Belmont... |
| **首府圈与中谷 (Sacramento & Valley)** | 39 队 | **7.36%** | Folsom, Mountain House, Sacramento, El Dorado Hills, Tracy, Lathrop, Modesto, Roseville... |
| **北湾 (North Bay)** | 1 队 | **0.19%** | Kentfield (Marin County) 等 |
| **其他 / 外围区域 (Other)** | 1 队 | **0.19%** | 其他边缘城市及未标明区域 |


### 4.2 FLL-Challenge 核心主力组按区域队伍数量分布 (Challenge 349 Teams)

| 大区域 (Region) | Challenge 队伍数 | 占 Challenge 比例 | 区域主力特征 |
| :--- | :---: | :---: | :--- |
| **南湾 / 硅谷 (South Bay)** | 144 队 | **40.68%** | 🏆 跃升为 Challenge 第一主力！硅谷科技学区与独立创客汇聚 |
| **东湾 (East Bay)** | 140 队 | **39.55%** | 🥈 Challenge 第二主力，拥有老牌社区队与创客俱乐部 |
| **半岛与旧金山 (Peninsula & SF)** | 39 队 | **11.02%** | 🥉 集中在旧金山私校与半岛学区 |
| **首府圈与中谷 (Sacramento & Valley)** | 30 队 | **8.47%** | 第四主力，Folsom / Mountain House 增长迅速 |
| **北湾 (North Bay)** | 1 队 | **0.28%** | Marin County 等低密度区域 |


### 4.2 队伍最多的 Top 15 城市

| 排名 | 城市 (City) | 队伍数 | 占总队伍比例 |
| :---: | :--- | :---: | :---: |
| 1 | **Oakland** | 84 | 15.85% |
| 2 | **Piedmont** | 70 | 13.21% |
| 3 | **San Jose** | 54 | 10.19% |
| 4 | **Fremont** | 44 | 8.3% |
| 5 | **Santa Clara** | 27 | 5.09% |
| 6 | **San Francisco** | 23 | 4.34% |
| 7 | **Mountain View** | 22 | 4.15% |
| 8 | **Dublin** | 17 | 3.21% |
| 9 | **Sunnyvale** | 16 | 3.02% |
| 10 | **Saratoga** | 16 | 3.02% |
| 11 | **Cupertino** | 14 | 2.64% |
| 12 | **Folsom** | 11 | 2.08% |
| 13 | **Pleasanton** | 10 | 1.89% |
| 14 | **Los Altos** | 7 | 1.32% |
| 15 | **San Ramon** | 7 | 1.32% |


## 5. 组织机构与队伍性质结构 (Organization Breakdown)

### 5.1 组织性质大类分类

| 组织类别 (Category) | 队伍数 | 占比 | 特征说明 |
| :--- | :---: | :---: | :--- |
| **Family/Community** | 215 | 40.57% | 家长自发组建或社区邻里团队，灵活性高但指纹审查容易掉队 |
| **Piedmont Makers** | 146 | 27.55% | Piedmont 区域极具影响力的创客公益联盟，建制化规模极大 |
| **School / Academic Institution** | 143 | 26.98% | 公立学区或私立学校校队，合规受学区流程制约 |
| **Other / Private Org** | 26 | 4.91% | 课外科技机构、俱乐部或独立培训中心 |


### 5.2 队伍最多的 Top 10 具体机构/学校

| 排名 | 机构/学校名称 (Org Name) | 队伍数 | 占总队伍比例 |
| :---: | :--- | :---: | :---: |
| 1 | **Family/Community** | 207 | 39.06% |
| 2 | **Piedmont Makers** | 136 | 25.66% |
| 3 | **Cabrillo Middle School** | 12 | 2.26% |
| 4 | **Town School for Boys** | 8 | 1.51% |
| 5 | **Argonaut Elementary** | 8 | 1.51% |
| 6 | **Home School** | 7 | 1.32% |
| 7 | **Tom Matsumoto Elementary** | 7 | 1.32% |
| 8 | **San Francisco Day School** | 5 | 0.94% |
| 9 | **Foothill Elementary** | 5 | 0.94% |
| 10 | **Nueva School** | 4 | 0.75% |


## 6. 队伍编号与资历分析 (Team Number & Vintage)

- **最低队伍编号**: `#445` (Matsuyama RoboPines，极早期老牌老队)
- **最高队伍编号**: `#600743` (今年全新注册队伍)
- **编号中位数**: `#67947` | **编号平均数**: `#93919.9`

| 编号区间 (Team Number Range) | 代表建队年代 / 阶段 | 队伍数量 | 占比 |
| :--- | :--- | :---: | :---: |
| `< 10,000 (Veteran/Early Teams)` | 历史资历 | 17 | 3.21% |
| `10,000 - 29,999 (Established Teams)` | 历史资历 | 60 | 11.32% |
| `30,000 - 49,999 (Mid-Era Teams)` | 历史资历 | 100 | 18.87% |
| `50,000 - 64,999 (Recent Teams 2021-2023)` | 历史资历 | 48 | 9.06% |
| `65,000 - 74,999 (New Teams 2024-2025)` | 历史资历 | 140 | 26.42% |
| `>= 75,000 (Brand New Teams 2025-2026)` | 历史资历 | 165 | 31.13% |


## 7. 教练配置分析 (Coaches Configuration)

| 教练人数 (Coaches Count) | 队伍数 | 占比 | 官方标准评估 |
| :---: | :---: | :---: | :--- |
| **0 人** | 19 | 3.58% | ⚠️ 警告：不足2人，不符青年保护政策 |
| **1 人** | 70 | 13.21% | ⚠️ 警告：不足2人，不符青年保护政策 |
| **2 人** | 426 | 80.38% | ✅ 标配（2名成人教练） |
| **3 人** | 15 | 2.83% | ➕ 增配副教练/助理 |


## 8. 队伍历史战绩与历届成绩综合分析 (Historical Performance & Veteran Analysis)

> **数据整合来源**: 关联以往官方赛事库 (`data/mylumi.db` 中 `events`, `scores`, `awards`, `event_teams` 表)

- **历史参赛战队覆盖率**: **282 支 / 519 支 (53.21%)** 拥有官方参赛记录。

- **机器人比赛得分记录**: **205 支 (38.68%)** 记录有真实对战最高分。

- **斩获官方奖项队伍**: **86 支 (16.23%)** 斩获过冠亚季军、核心价值或机器人设计等奖项。

- **成功晋级更高级别队伍**: **70 支** 在往届资格赛中成功晋级。

- **进军州锦标赛 (Championship) 队伍**: **73 支** 拥有锦标赛终极决战经历。


### 8.1 参赛队伍资历梯度分布 (Experience Tier)

| 资历梯队 (Tier) | 队伍数量 | 占比 | 梯队特征描述 |
| :--- | :---: | :---: | :--- |
| **Rookie (新队伍)** | 248 队 | **46.79%** | 今年新注册或首次加入 MyLumi 系统的初生战队 |
| **Veteran (老牌强队)** | 178 队 | **33.58%** | 跨多赛季参赛、晋级过 Championship 或斩获多项大奖的老牌王者 |
| **Experienced (有参赛经验)** | 104 队 | **19.62%** | 参加过往届赛事，具备完整正赛与机器人调试经验 |


### 8.2 历史战绩得分实力梯队 (Score Tier)

| 历史最高分梯队 | 队伍数量 | 占总队伍比 | 战力梯队特征 |
| :--- | :---: | :---: | :--- |
| **暂无得分记录** | 325 队 | **61.32%** | - |
| **<300 (入门发展)** | 130 队 | **24.53%** | 🌱 基础任务得分梯队，仍在成长与打磨中 |
| **300-399 (中坚晋级)** | 56 队 | **10.57%** | 💪 地区晋级核心主力，具备稳健的机械与编程能力 |
| **400-499 (一档强队)** | 15 队 | **2.83%** | ⚡ 具备稳进 Championship 实力的一档种子队 |
| **500+ (争冠顶尖)** | 4 队 | **0.75%** | 🔥 绝对争冠梯队，场地任务全清或近乎满分 |


### 8.3 机器人对战生涯最高分排行榜 Top 15 (Top Career High Scores)

| 排名 | 队号 | 队伍名称 | 城市 (大区域) | 生涯最高分 | 历史平均分 | 历史最佳排名 | 累计奖项 | 晋级次数 | 参赛赛季 |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `#64638` | **Brain Bots** | San Jose (南湾) | **540.0** | 480.0 | 第 1 名 | 🏆 11 | 🚀 2 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 2 | `#60085` | **Lego Artisans** | Cupertino (南湾) | **515.0** | 420.0 | 第 1 名 | 🏆 6 | 🚀 2 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 3 | `#60868` | **iBots** | San Jose (南湾) | **515.0** | 379.0 | 第 1 名 | 🏆 14 | 🚀 3 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 4 | `#17494` | **17494** | Santa Clara (南湾) | **505.0** | 395.0 | 第 1 名 | 🏆 1 | 🚀 0 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 5 | `#65258` | **CrypticButterflies** | San Jose (南湾) | **485.0** | 417.5 | 第 1 名 | 🏆 2 | 🚀 1 | 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 6 | `#71606` | **Lego Legends** | Fremont (东湾) | **480.0** | 450.0 | 第 2 名 | 🏆 0 | 🚀 1 | 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 7 | `#72905` | **Argo Cosmos** | Saratoga (南湾) | **470.0** | 435.0 | 第 3 名 | 🏆 1 | 🚀 1 | 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 8 | `#52561` | **Brilliant Beavers** | San Carlos (半岛与旧金山) | **465.0** | 295.0 | 第 1 名 | 🏆 1 | 🚀 1 | 2023 - MASTERPIECE (Challenge), 2025 - UNEARTHED (Challenge) |
| 9 | `#68040` | **MH Quantum** | Mountain House (首府圈与中谷) | **465.0** | 232.5 | 第 1 名 | 🏆 1 | 🚀 0 | 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 10 | `#48793` | **Mountain House** | Mountain House (首府圈与中谷) | **455.0** | 319.0 | 第 2 名 | 🏆 4 | 🚀 3 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 11 | `#52363` | **TerraBytes** | San Jose (南湾) | **450.0** | 306.2 | 第 4 名 | 🏆 2 | 🚀 1 | 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 12 | `#71232` | **Aura100%** | San Jose (南湾) | **440.0** | 410.0 | 第 1 名 | 🏆 1 | 🚀 1 | 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 13 | `#71804` | **Astrobot** | Mountain House (首府圈与中谷) | **440.0** | 440.0 | 第 1 名 | 🏆 0 | 🚀 0 | 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 14 | `#57382` | **RoboRise** | Foster City (半岛与旧金山) | **435.0** | 365.0 | 第 5 名 | 🏆 3 | 🚀 2 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge), 2025 - UNEARTHED (Challenge), 2026 - BIOGLOW (Challenge) |
| 15 | `#44532` | **FLL-C 44532** | Piedmont (东湾) | **430.0** | 305.0 | 第 4 名 | 🏆 4 | 🚀 1 | 2023 - MASTERPIECE (Challenge), 2024 - SUBMERGED (Challenge) |


### 8.4 历史荣誉斩获最多战队 Top 10 (Most Awarded Teams)

| 排名 | 队号 | 队伍名称 | 城市 | 奖项总数 | 生涯最高分 | 晋级次数 | 代表奖项 |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `#60868` | **iBots** | San Jose | **🏆 14 个** | 515.0 分 | 🚀 3 次 | Core Values Award、Breakthrough Award、CT Kids Choice Award:  Favorite Team Costume |
| 2 | `#64638` | **Brain Bots** | San Jose | **🏆 11 个** | 540.0 分 | 🚀 2 次 | Robot Performance Award、Innovation Project Award、Coach/Mentor Award |
| 3 | `#54977` | **Menlo Park Narleaotters** | Menlo Park | **🏆 6 个** | 425.0 分 | 🚀 3 次 | Champion's Award、Champion's Award、Champion's Award |
| 4 | `#60085` | **Lego Artisans** | Cupertino | **🏆 6 个** | 515.0 分 | 🚀 2 次 | Robot Design Award、Robot Performance Award、Robot Performance Award |
| 5 | `#4979` | **4979** | Santa Clara | **🏆 4 个** | 380.0 分 | 🚀 3 次 | Core Values Award、Robot Design Award、Champion's Award |
| 6 | `#44532` | **FLL-C 44532** | Piedmont | **🏆 4 个** | 430.0 分 | 🚀 1 次 | Champion's Award、Robot Performance Award、CT Kids Choice Award:  Favorite Robot and/or attachment |
| 7 | `#48793` | **Mountain House** | Mountain House | **🏆 4 个** | 455.0 分 | 🚀 3 次 | Champion's Award、CT Kids Choice Award:  Best team giveaway、Champion's Award |
| 8 | `#66292` | **CookieBots** | Danville | **🏆 4 个** | 350.0 分 | 🚀 2 次 | Robot Design Award、Coach/Mentor Award、Core Values Award |
| 9 | `#68202` | **Curious Earthlings** | Fremont | **🏆 4 个** | 375.0 分 | 🚀 2 次 | Robot Design Award、CT Kids Choice Award:  Favorite team chant、Champion's Award |
| 10 | `#445` | **Matsuyama RoboPines** | Sacramento | **🏆 3 个** | 160.0 分 | 🚀 1 次 | Core Values Award、Core Values Award、Coach/Mentor Award |


### 8.5 资历与当前合规就绪率的交叉分析 (Cross-Analysis: Experience vs Readiness)

| 队伍资历梯队 | 队伍总数 | 全部就绪队伍 (Good) | 完全就绪率 (Readiness) | 深度洞察 |
| :--- | :---: | :---: | :---: | :--- |
| **Veteran (老牌强队)** | 178 | 121 | **67.98%** | 老牌队伍流程轻车熟路，教练指纹背景常驻有效，就绪率显著高于平均 |
| **Experienced (有经验)** | 104 | 66 | **63.46%** | 中坚队伍就绪度平稳 |
| **Rookie (新队伍)** | 248 | 16 | **6.45%** | 新手队伍大幅拖累整体就绪率，主要卡在加州指纹预约与队员邀请 |


## 9. 给参赛队伍与组委会的行动建议 (Actionable Insights)

1. **老牌队伍示范带头与结对帮扶 (Buddy System)**：

   - 84 支 Veteran 战队的合规就绪率显著领先，建议组委会引导老牌队伍在社区分享 LiveScan 加州指纹和 Roster 快速达标经验，帮带 292 支 Rookie 新战队。

2. **重点关注 `waiting_invites` 的 176 支队伍**：

   - 这是最容易转为 `good` 的队伍群体。绝大多数只需教练或家长登录 FIRST/MyLumi 邮箱确认接受邀请，即可变为可用状态。

3. **关注单教练（69 队）与无教练（20 队）的合规风险**：

   - 共有 89 队不足 2 名教练，违反了 FIRST YPP（Youth Protection Policy）底线要求，需尽快增设第二教练。

4. **高分战队提早规划选拔赛赛站**：

   - 历史 400+ 顶尖队（如 64638, 60868, 60085 等）实力强劲，建议关注各 Qualifier 赛站容量，及早完成全部审核锁定参赛名额。
