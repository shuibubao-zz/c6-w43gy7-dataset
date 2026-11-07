# 卢怡然 · C6A 提交数据仪表盘 · 方案设计

> 把散落在群文件、聊天记录、各文件夹里的 20 人×11 挑战提交，变成一个**可浏览、可筛选、可追踪**的课程管理系统原型。
> 一句话架构：`真实磁盘文件 → C4A 式扫描校验 → 结构化 JSON/CSV → 离线纯前端仪表盘 + 离线 Excel`。

---

## 1. 总体架构

```
群文件 / 提交文件夹（真实磁盘）
        │
        │ ① gen_sample_submissions.py  —— 仅"无真实群文件"时的代表性样本生成器
        │    （卢怡然=真实进度；其余 19 名为确定性合成样本，种子固定可复现）
        ▼
submissions/  ← 命名规范  <姓名>_<挑战>_<后缀>  的真实文件落地
        │
        │ ② scan_submissions.py  —— 独立递归扫描，不信任任何"记忆"里的数字
        │    · 按命名规范解析 学生/挑战
        │    · 对照 challenge_schema.json 的 required_files 算 状态/齐备率/缺失/评级
        │    · 内嵌 C4A 初筛规则（缺核心产出即不通过）
        │    · 校验命名规范违规
        ▼
submissions.json / submissions.csv   ← 单一口径来源（Level 1）
        │
        ├─▶ build_report.py → 卢怡然_C6A_report.xlsx（6 Sheet，条件格式，Level 2）
        │
        └─▶ build_site_data.py → data.js（内嵌 220 条）
                 │
                 ▼
            dashboard/（纯静态 HTML+CSS+JS，零 CDN，离线可用，Level 3）
                 │
                 ├─ gen_summary.py → 周报.md（通知系统，Level 4）
                 └─ GitHub repo（git 多次提交，Level 4）

全程无数据库、无后端、无联网依赖：换一台装了 Python + 浏览器 的机器，
把 submissions/ 换成真实群文件，三步即可重建整个系统。
```

---

## 2. 技术选型与理由

| 层 | 选型 | 为什么 |
|----|------|--------|
| 数据管线 | **Python 标准库**（fnmatch/datetime/collections/json/csv）+ openpyxl | 零重型依赖；扫描与校验纯标准库，任何人 `python x.py` 即可跑 |
| 结构化存储 | JSON（主）+ CSV（辅） | JSON 保留嵌套 `files[]`；CSV 供评审快速看 |
| Excel | openpyxl（唯一第三方 Python 库） | 挑战推荐库；可程序化写条件格式与图表，不手动填表 |
| 前端 | **纯静态 HTML + 自写 CSS + 原生 JS**，零 CDN、零框架 | 离线双击即开；无外部资源失败风险；评审环境断网也能看 |
| 图表 | canvas 手绘（甜甜圈/条形/热力矩阵） | 不引 Chart.js CDN，保证"零 CDN"承诺真实成立 |
| 校验/评审 | 内嵌 C4A 初筛规则（Python 实现） | 把"评审技能"落到可执行代码，而非口头描述 |
| 截图/录屏 | Edge 无头模式 + ffmpeg-static | 真实运行截图，非设计稿；demo.mp4 由真实截图合成 |
| AI 协作 | 本会话 WorkBuddy | 见 `卢怡然_C6A_AI日志.md` |

**关键决策：纯前端而非 React/Streamlit。**
原因：挑战要求"本地网站 + 离线查看"，纯静态满足度最高、部署最简单（拖到 Netlify 或开 GitHub Pages 即上线），且不引入框架学习成本与 CDN 依赖。代价是交互逻辑需手写，但本场景交互不复杂，手写可控性更好。

---

## 3. 数据模型设计（单一口径来源）

**两处 schema，互不重复：**

1. **`challenge_schema.json`** —— 11 个挑战的"必填文件清单 + 分级定义"。这是**唯一权威口径**。改一个挑战的必填项，只改这里，扫描器/Excel/仪表盘全部跟着变。
2. **`submissions.json` 的 record** —— 每条提交记录。字段**完全对齐**挑战"数据模型参考"：

```json
{
  "student": "卢怡然",
  "challenge": "C4B",
  "title": "公众号文章生成技能",
  "status": "complete",            // complete / partial / missing
  "completeness": 1.0,             // 必填齐备率 0~1
  "required_total": 7,
  "required_present": 7,
  "missing": [],
  "level_achieved": 4,
  "submitted_at": "2026-04-12T...", // ISO8601，矩阵时间线用
  "naming_ok": true,               // 命名规范校验
  "review_passed": true,           // C4A 初筛
  "review_note": "全部必填齐备",
  "present_files": ["卢怡然_C4B_..."],
  "missing_required": [],
  "files": [                       // 对齐参考 schema 的 files[]
    {"filename":"卢怡然_C4B_AI日志.md","category":"AI日志","required":true,"present":true},
    ...
  ]
}
```

**评级逻辑（`level_from`）：** 按必填齐备率 + 是否完整提交映射到 Level 1–4：
- 齐备率 ≥ 0.9 且 status=complete → 结合文件类型推断最高可达级别（含方案/产出/AI日志/复盘/拿来说明 视为达到高阶）
- 未提交 → Level 0

---

## 4. ⚠️ 口径声明（权威数据源 + 诚实边界）

> 这是本作业最容易翻车的点，单独强调。

- **题包里没有真实的 20 人 × 11 挑战群文件。** 挑战 objective 要求"明确口径与权威数据源"，所以我**明确声明数据源**，而不是假装有一份真实群文件。
- **口径：** `submissions/` 由 `gen_sample_submissions.py` 生成——**卢怡然本人（本会话真实完成的工作）为真实进度**，其余 19 名为**确定性合成样本**（随机种子固定，任何人重跑得到同一份数据）。
- **为什么诚实标注：** C6A 评分项含"数据洞察 25%"，洞察数字的**可信度取决于数据源是否声明清楚**。把合成数据伪装成真实采集，一旦被问"这 20 人真实吗"就崩。反过来，明确标了口径，评审能看到"系统的能力是真的（扫描/校验/可视化都跑通），只是演示数据用代表性样本"——这才是可复用的系统。
- **权威源排序（本作业语境）：** ① 真实磁盘文件（最高，scan 直接从文件推导）② challenge_schema.json（必填口径，唯一来源）③ 合成样本生成器（演示数据，明确标注）。
- **切换到真实数据零成本：** 删掉 `submissions/` 里的合成文件，把真实群文件按 `<姓名>_<挑战>_<后缀>` 命名丢进去，重跑 `scan_submissions.py` 即可——系统代码一行不改。

---

## 5. 分级映射（Level 1→4 如何对应交付）

| Level | 要求 | 本作业对应交付 |
|-------|------|----------------|
| 1 Bronze | 收集+结构化 JSON/CSV | `scan_submissions.py` + `submissions.json/csv` + 本文件第 3–4 节 |
| 2 Silver | Excel 5 Sheet | `build_report.py` → `卢怡然_C6A_report.xlsx`（总览/按学生/按挑战/时间线/缺失项/口径说明） |
| 3 Gold | 交互网站 | `卢怡然_C6A_dashboard/`（总览/学生详情/挑战详情/筛选排序/文件链接/缺失高亮） |
| 4 Platinum | 自动化+实时 | ① 自动扫描 ② 校验引擎（命名+必填）③ 评审集成（C4A 初筛）④ 通知系统（周报.md）⑤ 多课程扩展（schema 驱动）⑥ GitHub repo |

---

## 6. 关键数字（均可在本机复跑，见教学说明/AI日志）

| 指标 | 数值 |
|------|------|
| 学生 × 挑战 组合 | 20 × 11 = **220** 条记录（含未提交） |
| 实际有提交 | **152** 条 |
| 全量状态 | complete **52** / partial **100** / missing **68** |
| 班级整体完整率 | 52 / 220 = **23.6%** |
| 提交内平均必填齐备率 | **71.0%** |
| 缺 AI日志 的提交 | **65 / 152 = 42.8%** |
| 最简单挑战 | **C3 = 100%** 完整率 |
| 最难关卡 | **C4B = 7%** / C4C 14% / C6A 19% 完整率 |
| 卢怡然排名 | **第 1**（9 提交 / 9 完整） |

> 每个数字背后都有 `scan_submissions.py` 的独立推导，未做任何人工"估算填充"。复跑命令见 `卢怡然_C6A_教学说明.md` 第 3 节。
