# 卢怡然 · C6A 提交数据仪表盘 · 教学说明

> 给"下一期课程助教 / 下一届学员"看的操作手册：**怎么装、怎么跑、怎么换真实数据、怎么部署**。
> 全程命令行，复制粘贴即可。所有命令在 Windows + 隔离 Python venv 实测通过。

---

## 0. 环境要求

| 依赖 | 用途 | 安装 |
|------|------|------|
| Python 3.11+ | 扫描/校验/Excel/周报 | 已自带（本机 `C:\Users\卢怡然\.workbuddy\binaries\python\envs\default`） |
| openpyxl | 生成 Excel | `python -m pip install openpyxl`（已装） |
| 浏览器（Edge/Chrome） | 看仪表盘 + 截图 | 已装 |
| ffmpeg-static（可选） | 合成 demo.mp4 | `npm i ffmpeg-static` |

> 仪表盘本身是**纯静态前端**，打开不需要 Python；只有"重新生成数据"才需要 Python。

---

## 1. 目录结构（一眼看懂）

```
卢怡然_C6A/
├── 卢怡然_C6A_data/            ← 数据管线（Level 1+4）
│   ├── challenge_schema.json   ← 【唯一口径】11 挑战的必填文件 + 分级
│   ├── gen_sample_submissions.py  ← 样本生成器（无真实群文件时用）
│   ├── scan_submissions.py     ← 扫描+校验+评级引擎
│   ├── build_report.py         ← 生成 Excel
│   ├── gen_summary.py          ← 生成周报（通知系统）
│   ├── submissions/            ← 真实磁盘文件（被扫描的对象）
│   ├── submissions.json/.csv   ← 扫描产物（单一口径来源）
│   └── 卢怡然_C6A_report.xlsx  ← 由 build_report.py 生成
├── 卢怡然_C6A_dashboard/       ← 网站（Level 3）
│   ├── index.html / styles.css / app.js
│   ├── data.js                 ← 由 build_site_data.py 从 json 生成
│   ├── build_site_data.py
│   ├── deploy.sh / README.md
│   └── .git/                   ← Level 4：git 多次提交
├── 卢怡然_C6A_screenshots/     ← 4 张真实运行截图
├── 卢怡然_C6A_demo.mp4         ← 4 张截图合成（25 秒）
└── 卢怡然_C6A_*.md             ← 全部提交文档
```

---

## 2. 三步跑通（演示数据）

```bash
# 第 1 步：生成代表性样本（仅"无真实群文件"时需要；有真实数据可跳过）
cd 卢怡然_C6A_data
python gen_sample_submissions.py
# → submissions/ 下生成 20 学生 × 11 挑战的真实磁盘文件

# 第 2 步：扫描 + 校验 + 评级
python scan_submissions.py
# 预期输出：
#   ✅ 扫描完成：220 条记录（含未提交组合）
#   学生 20 人 × 挑战 11 个
#   实际有提交：152 条
#   命名违规：0 条
#   → 生成 submissions.json / submissions.csv

# 第 3 步：生成 Excel 与仪表盘数据
python build_report.py
#   ✅ 已生成 Excel：卢怡然_C6A_report.xlsx（6 个 Sheet）
cd ../卢怡然_C6A_dashboard
python build_site_data.py
#   ✅ 已生成 data.js（内嵌 220 条记录，离线可用）
```

---

## 3. 复跑关键数字（评审可验证）

把下面整段贴进 `卢怡然_C6A_data/` 目录下的 Python，能复现方案设计里的全部数字：

```python
import json
d=json.load(open('submissions.json',encoding='utf-8'))
recs=d['records']
subs=[r for r in recs if r['status']!='missing']
print("全量记录:",len(recs))                       # 220
print("实际提交:",len(subs))                        # 152
from collections import Counter
print("全量状态:",dict(Counter(r['status'] for r in recs)))  # complete52/partial100/missing68
print("平均齐备率: %.1f%%"%(sum(r['completeness'] for r in subs)/len(subs)*100))  # 71.0%
ailog=sum(1 for r in subs if any('AI日志' in m for m in r['missing']))
print("缺AI日志: %d/%d = %.1f%%"%(ailog,len(subs),ailog/len(subs)*100))  # 65/152=42.8%
```

---

## 4. 换成真实数据（核心卖点：零代码改动）

```bash
# 1) 清空演示样本
rm -rf 卢怡然_C6A_data/submissions/*

# 2) 把真实群文件按命名规范丢进去
#    命名规范：<学生姓名>_<挑战编号>_<后缀>.<ext>
#    例：张三_C4B_article.html、李四_C2A_AI日志.md
#    目录型交付物：<学生>_<挑战>_<标签>/  （如 王五_C5_repo/）

# 3) 若某挑战的必填文件清单与 challenge_schema.json 不同，改这一个文件即可
#    （其余代码全自动跟随）

# 4) 重跑第 2、3 步 → 仪表盘与 Excel 立即反映真实数据
```

**命名规范校验：** 任何不符合 `<姓名>_<挑战>_<后缀>` 或挑战编号不在 schema 里的文件，会被 `scan_submissions.py` 计入 `naming_violations` 并在仪表盘"数据健康"处标红——这是 Level 4 校验引擎的一部分。

---

## 5. 看仪表盘

**方式 A（最稳，离线）：** 直接用浏览器打开 `卢怡然_C6A_dashboard/index.html`。
> 注意：因 `data.js` 用 `file://` 加载可能被浏览器 CORS 拦。若空白，用方式 B。

**方式 B（推荐）：** 起本地静态服务
```bash
cd 卢怡然_C6A_dashboard
python -m http.server 8000
# 浏览器打开 http://127.0.0.1:8000/
```

**方式 C（公开分享）：** 部署到 GitHub Pages / Netlify / Vercel
```bash
# GitHub Pages：
bash deploy.sh 你的GitHub用户名          # 提交 + 推送
# 然后仓库 Settings → Pages → Source=main/root → Save
# 约 2 分钟后访问 https://<用户名>.github.io/<仓库>/
# 或把整个 dashboard/ 文件夹拖到 Netlify 拖拽区
```

---

## 6. 仪表盘功能速查

| 功能 | 在哪 | 说明 |
|------|------|------|
| 总览 | 首页 | 5 张统计卡 + 状态甜甜圈 + 各挑战完整率条形 + 20×11 热力矩阵 |
| 学生详情 | 点学生名 / `#stu=姓名` | 该生全部提交卡片：状态徽章、齐备率条、缺失项、文件链接、评审备注 |
| 挑战详情 | 点挑战编号 / `#ch=C4B` | 该挑战全部学生完成情况，按完整率排序 |
| 筛选/排序 | 顶部控件 | 按状态/挑战/姓名过滤，按齐备率/时间排序 |
| 缺失高亮 | 矩阵红格 / 卡片红条 | 缺必填项（尤其 AI日志）自动标红 |
| 文件链接 | 学生详情卡片 | 点击打开对应提交文件（本地路径） |

---

## 7. 常见翻车点

| 现象 | 原因 | 解决 |
|------|------|------|
| 浏览器直接打开 index.html 空白 | `data.js` 被 file:// CORS 拦 | 用方式 B 起本地服务 |
| 改了 schema 但仪表盘没变 | 没重跑 `build_site_data.py` | 重跑第 3 步 |
| 真实数据没被识别 | 文件名不符合 `<姓名>_<挑战>_<后缀>` | 看 `naming_violations`，按规范改名 |
| Excel 打开是乱码 | 不是 UTF-8？ | openpyxl 默认正确编码；用 Excel 打开，非记事本 |
