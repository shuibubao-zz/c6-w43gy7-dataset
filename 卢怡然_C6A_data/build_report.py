#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_report.py  ——  C6A Excel 报表生成器（Level 2）

读取 submissions.json + challenge_schema.json，生成 卢怡然_C6A_report.xlsx：
  Sheet1 总览    ：学生×挑战 矩阵（✅/⚠️/❌ + 齐备率%）+ 每挑战完成率 + 每学生完成率 + 柱状图
  Sheet2 按学生  ：每个学生的全部提交明细
  Sheet3 按挑战  ：每个挑战的全部学生提交
  Sheet4 时间线  ：按提交时间倒序的全部提交
  Sheet5 缺失项  ：所有缺必填项 / 评审未过的条目（缺失单元格标红）
  Sheet6 口径说明：数据口径与权威源（诚实标注合成样本）

用法：python build_report.py
依赖：openpyxl（已装于隔离 venv）
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_IN = os.path.join(HERE, "submissions.json")
SCHEMA_IN = os.path.join(HERE, "challenge_schema.json")
OUT = os.path.join(HERE, "..", "卢怡然_C6A_report.xlsx")

TZ = timezone(timedelta(hours=8))
GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
RED = PatternFill("solid", fgColor="FFC7CE")
HEADER = PatternFill("solid", fgColor="2F5496")
REALFILL = PatternFill("solid", fgColor="DDEBF7")
WHITE = Font(color="FFFFFF", bold=True)
BOLD = Font(bold=True)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

STATUS_SYM = {"complete": "✅", "partial": "⚠️", "missing": "❌"}


def load():
    with open(JSON_IN, encoding="utf-8") as f:
        data = json.load(f)
    with open(SCHEMA_IN, encoding="utf-8") as f:
        schema = json.load(f)
    return data, schema


def fmt_dt(s):
    if not s:
        return ""
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return s


def status_fill(status):
    return {"complete": GREEN, "partial": YELLOW, "missing": RED}.get(status)


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER
        cell.font = WHITE
        cell.alignment = CENTER
        cell.border = BORDER


def build():
    data, schema = load()
    records = data["records"]
    students = data["students"]
    challenges = list(data["challenges"].keys())
    ch_titles = data["challenges"]

    wb = Workbook()

    # ---------------- Sheet1 总览 ----------------
    ws = wb.active
    ws.title = "总览"
    ws.append(["Elite20 提交数据仪表盘 · 总览（学生 × 挑战）"])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(challenges) + 3)
    ws.cell(1, 1).font = Font(bold=True, size=14, color="2F5496")
    ws.append(["图例：✅完整 ⚠️部分 ❌缺失/未提交 ｜ 单元格数字=必填齐备率% ｜ 蓝色行=真实记录（卢怡然）"])
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(challenges) + 3)

    hdr = 4
    ws.cell(hdr, 1, "学生")
    for j, ch in enumerate(challenges, start=2):
        ws.cell(hdr, j, ch)
    ws.cell(hdr, len(challenges) + 2, "提交数")
    ws.cell(hdr, len(challenges) + 3, "完整率")
    style_header(ws, hdr, len(challenges) + 3)

    # 索引
    by_stu = defaultdict(list)
    for r in records:
        if r["status"] != "missing":
            by_stu[r["student"]].append(r)

    row = hdr + 1
    for s in students:
        is_real = (s == "卢怡然")
        ws.cell(row, 1, s).font = BOLD
        if is_real:
            ws.cell(row, 1).fill = REALFILL
        comp_sum = 0.0
        n_sub = 0
        for j, ch in enumerate(challenges, start=2):
            rec = next((r for r in records if r["student"] == s and r["challenge"] == ch), None)
            if rec is None:
                ws.cell(row, j, "")
                continue
            sym = STATUS_SYM[rec["status"]]
            pct = int(round(rec["completeness"] * 100))
            cell = ws.cell(row, j, f"{sym}{pct}%")
            cell.fill = status_fill(rec["status"])
            cell.alignment = CENTER
            cell.border = BORDER
            if rec["status"] != "missing":
                comp_sum += rec["completeness"]
                n_sub += 1
        if is_real:
            for j in range(2, len(challenges) + 2):
                if ws.cell(row, j).fill.fgColor.rgb in (None, "00000000"):
                    pass
        ws.cell(row, len(challenges) + 2, n_sub).alignment = CENTER
        full_rate = (sum(1 for r in by_stu[s] if r["status"] == "complete") / len(by_stu[s])) if by_stu[s] else 0
        ws.cell(row, len(challenges) + 3, f"{int(round(full_rate*100))}%").alignment = CENTER
        for c in range(1, len(challenges) + 4):
            ws.cell(row, c).border = BORDER
        row += 1

    # 每挑战完成率（底部统计行）
    ws.cell(row, 1, "挑战完成率↓").font = BOLD
    for j, ch in enumerate(challenges, start=2):
        cr = [r for r in records if r["challenge"] == ch and r["status"] != "missing"]
        rate = (sum(1 for r in cr if r["status"] == "complete") / len(cr)) if cr else 0
        ws.cell(row, j, f"{int(round(rate*100))}%").alignment = CENTER
        ws.cell(row, j).font = BOLD
    ws.cell(row, 1).fill = HEADER
    ws.cell(row, 1).font = WHITE

    ws.column_dimensions["A"].width = 12
    for j in range(2, len(challenges) + 2):
        ws.column_dimensions[get_column_letter(j)].width = 8
    ws.column_dimensions[get_column_letter(len(challenges) + 2)].width = 9
    ws.column_dimensions[get_column_letter(len(challenges) + 3)].width = 9
    ws.freeze_panes = "B5"

    # 柱状图：每挑战完整率
    chart = BarChart()
    chart.title = "各挑战完整率（%）"
    chart.type = "col"
    chart.y_axis.title = "完整率%"
    chart.x_axis.title = "挑战"
    data_ref = Reference(ws, min_col=2, max_col=len(challenges) + 1, min_row=row, max_row=row)
    cats = Reference(ws, min_col=2, max_col=len(challenges) + 1, min_row=hdr, max_row=hdr)
    chart.add_data(data_ref, from_rows=True, titles_from_data=False)
    chart.set_categories(cats)
    chart.height = 8
    chart.width = 20
    ws.add_chart(chart, f"A{row + 3}")

    # ---------------- Sheet2 按学生 ----------------
    ws2 = wb.create_sheet("按学生")
    cols = ["学生", "挑战", "标题", "状态", "齐备率", "必填总数", "已交", "缺失项", "提交时间", "评审", "评审备注"]
    ws2.append(cols)
    style_header(ws2, 1, len(cols))
    r = 2
    for rec in sorted(records, key=lambda x: (x["student"], x["challenge"])):
        if rec["status"] == "missing":
            continue
        ws2.append([rec["student"], rec["challenge"], rec["title"], STATUS_SYM[rec["status"]],
                    f'{int(round(rec["completeness"]*100))}%', rec["required_total"], rec["required_present"],
                    "、".join(rec["missing"]) or "—", fmt_dt(rec["submitted_at"]),
                    "通过" if rec["review_passed"] else "需补", rec["review_note"]])
        ws2.cell(r, 4).fill = status_fill(rec["status"])
        if rec["missing"]:
            ws2.cell(r, 8).fill = RED
        if not rec["review_passed"]:
            ws2.cell(r, 10).fill = YELLOW
        r += 1
    for c, w in zip(range(1, len(cols) + 1), [10, 8, 22, 8, 8, 9, 7, 18, 16, 8, 26]):
        ws2.column_dimensions[get_column_letter(c)].width = w
    ws2.freeze_panes = "A2"

    # ---------------- Sheet3 按挑战 ----------------
    ws3 = wb.create_sheet("按挑战")
    ws3.append(cols)
    style_header(ws3, 1, len(cols))
    r = 2
    for rec in sorted(records, key=lambda x: (x["challenge"], x["student"])):
        if rec["status"] == "missing":
            continue
        ws3.append([rec["student"], rec["challenge"], rec["title"], STATUS_SYM[rec["status"]],
                    f'{int(round(rec["completeness"]*100))}%', rec["required_total"], rec["required_present"],
                    "、".join(rec["missing"]) or "—", fmt_dt(rec["submitted_at"]),
                    "通过" if rec["review_passed"] else "需补", rec["review_note"]])
        ws3.cell(r, 4).fill = status_fill(rec["status"])
        if rec["missing"]:
            ws3.cell(r, 8).fill = RED
        if not rec["review_passed"]:
            ws3.cell(r, 10).fill = YELLOW
        r += 1
    for c, w in zip(range(1, len(cols) + 1), [10, 8, 22, 8, 8, 9, 7, 18, 16, 8, 26]):
        ws3.column_dimensions[get_column_letter(c)].width = w
    ws3.freeze_panes = "A2"

    # ---------------- Sheet4 时间线 ----------------
    ws4 = wb.create_sheet("时间线")
    tcols = ["提交时间", "学生", "挑战", "标题", "状态", "齐备率", "缺失项", "评审"]
    ws4.append(tcols)
    style_header(ws4, 1, len(tcols))
    r = 2
    timeline = sorted([x for x in records if x["submitted_at"]], key=lambda x: x["submitted_at"], reverse=True)
    for rec in timeline:
        ws4.append([fmt_dt(rec["submitted_at"]), rec["student"], rec["challenge"], rec["title"],
                    STATUS_SYM[rec["status"]], f'{int(round(rec["completeness"]*100))}%',
                    "、".join(rec["missing"]) or "—", "通过" if rec["review_passed"] else "需补"])
        ws4.cell(r, 5).fill = status_fill(rec["status"])
        if rec["missing"]:
            ws4.cell(r, 7).fill = RED
        if not rec["review_passed"]:
            ws4.cell(r, 8).fill = YELLOW
        r += 1
    for c, w in zip(range(1, len(tcols) + 1), [18, 10, 8, 22, 8, 8, 18, 8]):
        ws4.column_dimensions[get_column_letter(c)].width = w
    ws4.freeze_panes = "A2"

    # ---------------- Sheet5 缺失项 ----------------
    ws5 = wb.create_sheet("缺失项")
    mcols = ["学生", "挑战", "状态", "缺失必填项", "评审", "评审备注", "提交时间"]
    ws5.append(mcols)
    style_header(ws5, 1, len(mcols))
    r = 2
    for rec in sorted(records, key=lambda x: (x["student"], x["challenge"])):
        if not rec["missing"] and rec["review_passed"]:
            continue
        ws5.append([rec["student"], rec["challenge"], STATUS_SYM[rec["status"]],
                    "、".join(rec["missing"]) or "—", "通过" if rec["review_passed"] else "需补",
                    rec["review_note"], fmt_dt(rec["submitted_at"])])
        if rec["missing"]:
            ws5.cell(r, 4).fill = RED
        if not rec["review_passed"]:
            ws5.cell(r, 5).fill = YELLOW
        r += 1
    for c, w in zip(range(1, len(mcols) + 1), [10, 8, 8, 22, 8, 28, 16]):
        ws5.column_dimensions[get_column_letter(c)].width = w
    ws5.freeze_panes = "A2"

    # ---------------- Sheet6 口径说明 ----------------
    ws6 = wb.create_sheet("口径说明")
    ws6.append(["数据口径与权威源说明（C6A 诚实披露）"])
    ws6.cell(1, 1).font = Font(bold=True, size=13, color="2F5496")
    notes = [
        "",
        "1. 权威数据源：题包未附带真实 20 人「群文件」。本报表数据来自对 submissions/ 目录的",
        "   真实磁盘扫描（scan_submissions.py），扫描规则为唯一权威识别口径：文件名需匹配",
        "   <学生>_<挑战>_<后缀> 且挑战编号在 challenge_schema.json 已知清单内。",
        "",
        "2. 真实 vs 合成：卢怡然（蓝色行）的记录基于本会话真实完成的工作（C2A/C2G/C3/C4A/",
        "   C4B/C5/C5A/C6/C6A 已完成；C4C/C4D 无证据→未提交）。其余 19 名为确定性合成样本",
        "   （random.seed(42)），仅用于演示完整扫描/校验/可视化管线。合成数据不代表真实同学。",
        "",
        "3. 完成度 completeness = 必填文件已交数 / 必填文件总数（不含选填）。",
        "4. 状态 status：complete=全部必填在场；partial=部分必填在场；missing=0 必填在场（含未提交）。",
        "5. level_achieved 为文件齐备度近似（complete→4；≥0.75→3；≥0.5→2；>0→1；0→0），",
        "   不等同真实质量评级。",
        "6. 评审列 = C4A 评审集成（文件名级初筛）：命名合规 + AI日志在场 + 核心产出在场 → 通过；",
        "   否则标'需补'。这是初筛，非 C4A 完整人工评审。",
        "7. 复现：删除 submissions/ 与 submissions.json 后，依次运行 gen_sample_submissions.py",
        "   → scan_submissions.py → build_report.py，结果一致。",
    ]
    for i, line in enumerate(notes, start=2):
        ws6.cell(i, 1, line)
    ws6.column_dimensions["A"].width = 90

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"✅ 已生成 Excel：{os.path.normpath(OUT)}")
    print(f"   Sheet：总览 / 按学生 / 按挑战 / 时间线 / 缺失项 / 口径说明")


if __name__ == "__main__":
    build()
