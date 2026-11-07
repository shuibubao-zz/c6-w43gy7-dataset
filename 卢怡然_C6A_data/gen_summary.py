#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_summary.py  ——  C6A 通知系统（Level 4 自动化）

读取 submissions.json，生成一份"每周提交状态摘要"Markdown，可直接发群。
每次新增提交后重跑即可刷新，无需改代码。

用法：python gen_summary.py [--markdown 输出路径]
默认输出：卢怡然_C6A_周报.md（落在 C6A 根目录）
"""
import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_IN = os.path.join(HERE, "submissions.json")
DEFAULT_OUT = os.path.join(HERE, "..", "卢怡然_C6A_周报.md")
TZ = timezone(timedelta(hours=8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", default=DEFAULT_OUT)
    args = ap.parse_args()

    with open(JSON_IN, encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"]
    students = data["students"]
    challenges = list(data["challenges"].keys())
    subs = [r for r in records if r["status"] != "missing"]

    total = len(records)
    complete = sum(1 for r in records if r["status"] == "complete")
    partial = sum(1 for r in records if r["status"] == "partial")
    missing = sum(1 for r in records if r["status"] == "missing")
    avg = sum(r["completeness"] for r in subs) / len(subs) if subs else 0
    ailog_missing = [r for r in subs if any("AI日志" in m for m in r["missing"])]

    # 每挑战
    ch_lines = []
    for ch in challenges:
        cr = [r for r in subs if r["challenge"] == ch]
        n = len(cr)
        crate = (sum(1 for r in cr if r["status"] == "complete") / n) if n else 0
        ch_lines.append(f"| {ch} | {data['challenges'][ch]} | {n} | {int(round(crate*100))}% |")

    # 缺 AI日志 名单
    ailog_stu = defaultdict(list)
    for r in ailog_missing:
        ailog_stu[r["student"]].append(r["challenge"])

    # 学生排行
    by_stu = defaultdict(list)
    for r in subs:
        by_stu[r["student"]].append(r)
    rank = []
    for s in students:
        rs = by_stu.get(s, [])
        cr = sum(1 for r in rs if r["status"] == "complete") / len(rs) if rs else 0
        rank.append((s, cr, len(rs)))
    rank.sort(key=lambda x: -x[1])
    top = rank[:3]
    low = [x for x in rank if x[2] > 0 and x[1] < 0.5][:5]

    out = []
    out.append(f"# Elite20 提交状态周报（自动生成）")
    out.append("")
    out.append(f"> 生成时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} ｜ 数据源：submissions.json（scan_submissions.py 实时扫描）")
    out.append("")
    out.append("## 一、总览")
    out.append("")
    out.append(f"- 全量矩阵记录：**{total}** 条（{len(students)} 学生 × {len(challenges)} 挑战）")
    out.append(f"- 状态分布：✅完整 **{complete}** ｜ ⚠️部分 **{partial}** ｜ ❌缺失/未提交 **{missing}**")
    out.append(f"- 实际提交平均必填齐备率：**{int(round(avg*100))}%**")
    out.append(f"- ⚠️ 缺 AI日志 的提交：**{len(ailog_missing)}** 条（占实际提交 {int(round(len(ailog_missing)/len(subs)*100))}%）")
    out.append("")
    out.append("## 二、各挑战完成情况")
    out.append("")
    out.append("| 挑战 | 标题 | 提交数 | 完整率 |")
    out.append("|------|------|--------|--------|")
    out.extend(ch_lines)
    out.append("")
    out.append("## 三、重点提醒：缺 AI日志（必填项）")
    out.append("")
    if ailog_stu:
        for s, chs in sorted(ailog_stu.items(), key=lambda x: -len(x[1])):
            out.append(f"- **{s}**：{', '.join(chs)}")
    else:
        out.append("- 无")
    out.append("")
    out.append("## 四、学生排行（完整率）")
    out.append("")
    out.append("**领先：** " + "、".join(f"{s}({int(round(c*100))}%, {n}提交)" for s, c, n in top))
    if low:
        out.append("**待跟进（有提交但完整率<50%）：** " + "、".join(f"{s}({int(round(c*100))}%)" for s, c, n in low))
    out.append("")
    out.append("## 五、建议动作")
    out.append("")
    out.append("1. 对缺失 AI日志 的同学定向提醒（必填项，无此项无法评审）。")
    out.append("2. 对完整率<50% 的同学排查卡点。")
    out.append("3. 完整率最低的硬核挑战（C4C/C4D/C6A/C4B）可考虑补充示例或答疑。")
    out.append("")
    out.append("---")
    out.append("> 本摘要由 C6A 仪表盘 `gen_summary.py` 自动生成；数据口径见 `卢怡然_C6A_data/challenge_schema.json` 与 `口径说明` Sheet。卢怡然为真实记录，其余为合成样本。")

    with open(args.markdown, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"✅ 周报已生成：{os.path.normpath(args.markdown)}")
    print(f"   摘要：{total} 记录 / 完整 {complete} / 部分 {partial} / 缺失 {missing} / 缺AI日志 {len(ailog_missing)} 条")


if __name__ == "__main__":
    main()
