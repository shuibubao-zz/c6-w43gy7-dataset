#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site_data.py  ——  把 submissions.json 转成 dashboard/data.js（内嵌，离线可用）

网站不依赖任何 CDN / 后端：数据以 data.js 内嵌，浏览器直接打开即可。
本脚本是"数据 → 前端"的桥，保证口径单一来源（都来自 submissions.json）。

用法：python build_site_data.py
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_IN = os.path.join(HERE, "..", "卢怡然_C6A_data", "submissions.json")
OUT = os.path.join(HERE, "data.js")


def main():
    with open(JSON_IN, encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"]
    students = data["students"]
    challenges = list(data["challenges"].keys())
    ch_titles = data["challenges"]

    # 全局统计
    subs = [r for r in records if r["status"] != "missing"]
    status_cnt = defaultdict(int)
    for r in subs:
        status_cnt[r["status"]] += 1
    ailog_missing = sum(1 for r in subs if any("AI日志" in m for m in r["missing"]))

    # 每挑战统计
    ch_stats = {}
    for ch in challenges:
        cr = [r for r in subs if r["challenge"] == ch]
        n = len(cr)
        complete = sum(1 for r in cr if r["status"] == "complete")
        avg = (sum(r["completeness"] for r in cr) / n) if n else 0
        ch_stats[ch] = {"n": n, "complete": complete, "complete_rate": complete / n if n else 0,
                        "avg_completeness": avg}

    # 每学生统计
    stu_stats = {}
    by_stu = defaultdict(list)
    for r in subs:
        by_stu[r["student"]].append(r)
    for s in students:
        rs = by_stu.get(s, [])
        n = len(rs)
        complete = sum(1 for r in rs if r["status"] == "complete")
        avg = (sum(r["completeness"] for r in rs) / n) if n else 0
        stu_stats[s] = {"n": n, "complete": complete, "complete_rate": complete / n if n else 0,
                        "avg_completeness": avg, "real": s == "卢怡然"}

    # 时间线（最近 12 条）
    timeline = sorted([r for r in subs if r["submitted_at"]], key=lambda x: x["submitted_at"], reverse=True)[:12]

    payload = {
        "generated_at": data["generated_at"],
        "students": students,
        "challenges": challenges,
        "ch_titles": ch_titles,
        "records": records,
        "stats": {
            "student_count": len(students),
            "challenge_count": len(challenges),
            "submission_count": len(subs),
            "record_count": len(records),
            "status_cnt": dict(status_cnt),
            "avg_completeness": (sum(r["completeness"] for r in subs) / len(subs)) if subs else 0,
            "ailog_missing": ailog_missing,
            "ailog_missing_rate": (ailog_missing / len(subs)) if subs else 0,
            "ch_stats": ch_stats,
            "stu_stats": stu_stats,
            "timeline": timeline,
        },
        "caliber": data["caliber"],
    }

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// 自动生成，请勿手改。来源：卢怡然_C6A_data/submissions.json\n")
        f.write("window.DASHBOARD_DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write(";\n")
    print(f"✅ 已生成 {os.path.basename(OUT)}（内嵌 {len(records)} 条记录，离线可用）")


if __name__ == "__main__":
    main()
