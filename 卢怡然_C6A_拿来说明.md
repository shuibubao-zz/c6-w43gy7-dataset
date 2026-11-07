# 卢怡然 · C6A 提交数据仪表盘 · 拿来说明（ATTRIBUTION）

> 明确列出本作业用到的库、工具、AI Agent、以及**哪些是自写代码、哪些来自外部**。

---

## 1. 第三方库 / 框架

| 名称 | 用途 | 来源 | 是否自写 |
|------|------|------|----------|
| **openpyxl** | 生成 `卢怡然_C6A_report.xlsx`（多 Sheet + 条件格式 + 图表） | PyPI 第三方库 | 否（仅调用其 API） |
| Python 标准库（`fnmatch` / `datetime` / `collections` / `json` / `csv` / `os` / `re` / `hashlib`） | 扫描、命名解析、校验、文件读写 | Python 自带 | 否（标准库） |

> **前端零第三方依赖：** `index.html` / `styles.css` / `app.js` / `data.js` 均为**自写**，未使用 React/Vue/Tailwind/Chart.js，也未引任何 CDN。甜甜圈、条形图、热力矩阵全部用原生 canvas 手绘。

---

## 2. 工具（非代码类）

| 工具 | 用途 |
|------|------|
| Python 3.11（隔离 venv：`C:\Users\卢怡然\.workbuddy\binaries\python\envs\default`） | 运行全部数据管线脚本 |
| Node.js v22 | `node --check` 校验 JS 语法（仅验证，不进产物） |
| Microsoft Edge（无头 `--headless=new`） | 真实加载仪表盘截图（4 张）+ 截图验证 DOM 渲染 |
| ffmpeg-static（npm 包，自带二进制） | 把 4 张截图合成 `卢怡然_C6A_demo.mp4` |
| Git | 仪表盘 `卢怡然_C6A_dashboard/.git` 多次提交（Level 4 要求 GitHub repo） |
| WorkBuddy（本会话 AI） | 全程协作，详见 `卢怡然_C6A_AI日志.md` |

---

## 3. AI Agent / 模型

- **WorkBuddy（本会话）**：需求拆解、架构设计、全部代码初稿、文档撰写、截图验证、复盘。
- **C4A 评审技能（理念复用）**：挑战要求"用 C4A 技能收集提交数据"。本作业把 C4A 的评审逻辑**落到代码**（`scan_submissions.py` 内 `review_submission()` 函数：缺核心产出即不通过、缺 AI日志 视为不完整），而非仅口头套用。C4A 本身不是本仓库的依赖，是**方法论来源**。

---

## 4. 自写代码清单（100% 自写，无生成器套壳）

| 文件 | 行数量级 | 说明 |
|------|----------|------|
| `卢怡然_C6A_data/scan_submissions.py` | ~260 | 递归扫描 + 命名解析 + 必填校验 + C4A 初筛 + 评级 |
| `卢怡然_C6A_data/challenge_schema.json` | — | 11 挑战必填清单（唯一口径） |
| `卢怡然_C6A_data/gen_sample_submissions.py` | ~120 | 确定性样本生成（演示数据） |
| `卢怡然_C6A_data/build_report.py` | ~200 | Excel 6 Sheet + 条件格式 + 图表 |
| `卢怡然_C6A_data/gen_summary.py` | ~90 | 周报（通知系统） |
| `卢怡然_C6A_dashboard/app.js` | ~520 | 仪表盘全部渲染与交互逻辑 |
| `卢怡然_C6A_dashboard/styles.css` | ~340 | 自写样式，零框架 |
| `卢怡然_C6A_dashboard/build_site_data.py` | ~40 | json → data.js |

---

## 5. 诚实边界（与方案设计口径一致）

- **数据非真实群采集：** `submissions/` 由 `gen_sample_submissions.py` 生成。卢怡然本人为真实进度，其余 19 名为确定性合成样本。详见 `卢怡然_C6A_方案设计.md` 第 4 节与 `卢怡然_C6A_AI日志.md`。
- **未使用付费/外部 API：** 全程未调用任何需 key 的在线服务；截图与视频均在本地完成。
- **未伪造任何提交记录：** 所有"缺失/未提交"均由扫描器从磁盘实际推导，未手动篡改状态。
