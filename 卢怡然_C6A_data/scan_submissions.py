#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_submissions.py  ——  C6A 提交数据扫描器 / 校验引擎（Level 1 + Level 4 自动化核心）

完全独立地从磁盘重新推导一切（不读取任何"中间答案"）：
  1. 递归扫描 submissions/ 下所有文件与目录型交付物
  2. 按命名规范 <学生>_<挑战>_<后缀> 解析归属（正则提取，非硬编码名单）
  3. 对照 challenge_schema.json 的必填清单，逐条匹配，计算：
       status / completeness / missing / level_achieved / submitted_at
  4. 命名规范校验：文件名不符合规范 → 标记命名违规
  5. C4A 评审集成（文件名级初筛）：命名合规 + AI日志在场 + 核心产出在场 → 通过

输出：
  submissions.json  结构化全量记录（含每条明细 + 命名校验 + C4A 初筛）
  submissions.csv   扁平表，供 Excel / 其他工具直接消费

用法：python scan_submissions.py
"""
import csv
import fnmatch
import json
import os
import re
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "challenge_schema.json")
SUBMISSIONS_DIR = os.path.join(HERE, "submissions")
JSON_OUT = os.path.join(HERE, "submissions.json")
CSV_OUT = os.path.join(HERE, "submissions.csv")

TZ = timezone(timedelta(hours=8))
NAME_RE = re.compile(r"^(?P<name>.+?)_(?P<ch>C\d+[A-Z]?)_(?P<rest>.+)$")


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def collect(submissions_dir):
    """返回 (files_by_rel, dirs_by_basename)。files: relpath->mtime; dirs: basename->mtime"""
    files = {}
    dirs = {}
    for root, dirnames, filenames in os.walk(submissions_dir):
        for fn in filenames:
            if fn == ".keep":
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, submissions_dir)
            files[rel] = os.path.getmtime(full)
        for dn in dirnames:
            full = os.path.join(root, dn)
            dirs[dn] = os.path.getmtime(full)
    return files, dirs


def level_from(completeness, full):
    if completeness >= 1.0:
        return 4
    if completeness >= 0.75:
        return 3
    if completeness >= 0.5:
        return 2
    if completeness > 0:
        return 1
    return 0


def review_submission(cdef, matched_labels, naming_ok, files_for_sub):
    """C4A 评审集成（文件名级初筛，非完整人工评审）。返回 (passed:bool, note:str)"""
    missing_required = [rf["label"] for rf in cdef["required_files"]
                        if rf["required"] and rf["label"] not in matched_labels]
    needs = []
    if not naming_ok:
        needs.append("命名不规范")
    ai_log = [rf for rf in cdef["required_files"] if rf.get("is_ai_log")]
    if ai_log and ai_log[0]["label"] not in matched_labels:
        needs.append("缺AI日志")
    core = [rf for rf in cdef["required_files"] if rf.get("core")]
    missing_core = [rf["label"] for rf in core if rf["label"] not in matched_labels]
    if missing_core:
        needs.append("缺核心产出(" + "/".join(missing_core) + ")")
    if not missing_required and not needs:
        return True, "通过（初筛）"
    if not needs:
        return True, "通过（初筛）"
    return False, "需补：" + "、".join(needs)


def scan():
    schema = load_schema()
    challenges = schema["challenges"]
    files, dirs = collect(SUBMISSIONS_DIR)

    # 按 (student, ch) 聚合
    # agg[(name,ch)] = {"files":[(basename, mtime)], "dirs":[(basename,mtime)], "name_ok":bool}
    agg = {}
    students_meta = {}
    for rel, mtime in files.items():
        bn = os.path.basename(rel)
        m = NAME_RE.match(bn)
        if not m:
            continue  # 不符合命名规范的文件不参与（但会被命名校验单独列出）
        name, ch, rest = m.group("name"), m.group("ch"), m.group("rest")
        if ch not in challenges:
            continue
        key = (name, ch)
        agg.setdefault(key, {"files": [], "dirs": [], "name_ok": True})
        agg[key]["files"].append((bn, mtime))
    for dbn, mtime in dirs.items():
        m = NAME_RE.match(dbn)
        if not m:
            continue
        name, ch = m.group("name"), m.group("ch")
        if ch not in challenges:
            continue
        key = (name, ch)
        agg.setdefault(key, {"files": [], "dirs": [], "name_ok": True})
        agg[key]["dirs"].append((dbn, mtime))

    records = []
    for ch, cdef in challenges.items():
        for (name, ch2), bucket in agg.items():
            if ch2 != ch:
                continue
            matched_labels = set()
            present_files = []
            files_list = []  # 对齐挑战"数据模型参考"的 files[] 字段
            for rf in cdef["required_files"]:
                if rf.get("kind") == "dir":
                    hit = any(fnmatch.fnmatch(dbn, rf["pattern"]) for dbn, _ in bucket["dirs"])
                else:
                    hit = any(fnmatch.fnmatch(bn, rf["pattern"]) for bn, _ in bucket["files"])
                if hit:
                    matched_labels.add(rf["label"])
                    if rf.get("kind") != "dir":
                        present_files.extend([bn for bn, _ in bucket["files"]
                                              if fnmatch.fnmatch(bn, rf["pattern"])])
                files_list.append({
                    "filename": (rf["pattern"].replace("*_", name + "_").split("/")[-1]
                                 if not hit else
                                 sorted([bn for bn, _ in bucket["files"]
                                         if fnmatch.fnmatch(bn, rf["pattern"])])[0] if rf.get("kind") != "dir"
                                 else sorted([dbn for dbn, _ in bucket["dirs"]
                                              if fnmatch.fnmatch(dbn, rf["pattern"])])[0]),
                    "category": rf["label"],
                    "required": bool(rf.get("required", False)),
                    "present": bool(hit),
                })
            required = [rf for rf in cdef["required_files"] if rf["required"]]
            req_total = len(required)
            req_present = sum(1 for rf in required if rf["label"] in matched_labels)
            missing = [rf["label"] for rf in required if rf["label"] not in matched_labels]
            completeness = (req_present / req_total) if req_total else 0.0
            if req_present == 0:
                status = "missing"
            elif req_present == req_total:
                status = "complete"
            else:
                status = "partial"
            all_mtimes = [mt for _, mt in bucket["files"]] + [mt for _, mt in bucket["dirs"]]
            submitted_at = datetime.fromtimestamp(max(all_mtimes), TZ).isoformat() if all_mtimes else None
            naming_ok = bucket["name_ok"]
            passed, note = review_submission(cdef, matched_labels, naming_ok, bucket["files"])
            records.append({
                "student": name,
                "challenge": ch,
                "title": cdef["title"],
                "status": status,
                "completeness": round(completeness, 3),
                "required_total": req_total,
                "required_present": req_present,
                "missing": missing,
                "level_achieved": level_from(completeness, status == "complete"),
                "submitted_at": submitted_at,
                "naming_ok": naming_ok,
                "review_passed": passed,
                "review_note": note,
                "present_files": sorted(set(present_files)),
                "missing_required": missing,
                "files": files_list,
            })

    # 补齐"完全未提交"的 student×challenge 组合（矩阵需要）
    all_students = sorted({k[0] for k in agg})
    present_keys = {(r["student"], r["challenge"]) for r in records}
    for name in all_students:
        for ch, cdef in challenges.items():
            if (name, ch) in present_keys:
                continue
            required = [rf for rf in cdef["required_files"] if rf["required"]]
            records.append({
                "student": name, "challenge": ch, "title": cdef["title"],
                "status": "missing", "completeness": 0.0,
                "required_total": len(required), "required_present": 0,
                "missing": [rf["label"] for rf in required], "level_achieved": 0,
                "submitted_at": None, "naming_ok": True, "review_passed": False,
                "review_note": "需补：未提交",
                "present_files": [], "missing_required": [rf["label"] for rf in required],
                "files": [{"filename": rf["pattern"].replace("*_", name + "_").split("/")[-1],
                           "category": rf["label"], "required": bool(rf.get("required", False)),
                           "present": False} for rf in required],
            })

    # 命名规范违规清单（不符合 <学生>_<挑战>_<后缀> 或挑战未知的文件）
    naming_violations = []
    for rel, mtime in files.items():
        bn = os.path.basename(rel)
        m = NAME_RE.match(bn)
        if not m:
            naming_violations.append({"file": rel, "reason": "不符合 <学生>_<挑战>_<后缀> 命名规范"})
        elif m.group("ch") not in challenges:
            naming_violations.append({"file": rel, "reason": f"挑战编号 {m.group('ch')} 不在已知清单"})

    records.sort(key=lambda r: (r["student"], r["challenge"]))
    out = {
        "generated_at": datetime.now(TZ).isoformat(),
        "caliber": schema["_meta"]["caliber_notes"],
        "students": all_students,
        "challenges": {ch: cdef["title"] for ch, cdef in challenges.items()},
        "records": records,
        "naming_violations": naming_violations,
        "summary": {
            "student_count": len(all_students),
            "challenge_count": len(challenges),
            "submission_count": len([r for r in records if r["status"] != "missing"]),
            "record_count": len(records),
        },
    }
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # CSV
    with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["student", "challenge", "title", "status", "completeness",
                    "required_total", "required_present", "missing", "level_achieved",
                    "submitted_at", "naming_ok", "review_passed", "review_note",
                    "present_files"])
        for r in records:
            w.writerow([r["student"], r["challenge"], r["title"], r["status"],
                        f'{r["completeness"]:.3f}', r["required_total"], r["required_present"],
                        "|".join(r["missing"]), r["level_achieved"],
                        r["submitted_at"] or "", "Y" if r["naming_ok"] else "N",
                        "Y" if r["review_passed"] else "N", r["review_note"],
                        "|".join(r["present_files"])])

    print(f"✅ 扫描完成：{len(records)} 条记录（含未提交组合）")
    print(f"   学生 {len(all_students)} 人 × 挑战 {len(challenges)} 个")
    print(f"   实际有提交：{out['summary']['submission_count']} 条")
    print(f"   命名违规：{len(naming_violations)} 条")
    print(f"   输出：{os.path.basename(JSON_OUT)} / {os.path.basename(CSV_OUT)}")


if __name__ == "__main__":
    scan()
