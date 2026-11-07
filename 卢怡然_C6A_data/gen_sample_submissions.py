#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_sample_submissions.py  ——  C6A 样本提交数据生成器（确定性、真实落盘）

权威口径说明（详见 challenge_schema.json 的 _meta.caliber_notes）：
  题包未提供真实 20 人「群文件」。本脚本生成一个"代表性合成样本"，
  用于在真实扫描管线上演示。其中：
    - 卢怡然 的记录基于本会话真实完成的工作（C2A/C2G/C3/C4A/C4B/C5/C5A/C6/C6A 已完成；C4C/C4D 无证据→未提交）
    - 其余 19 名为确定性合成样本（random.seed(42)），仅用于演示完整管线

生成器只"决定每个文件是否落地"；扫描器 scan_submissions.py 完全独立地从磁盘重新
推导一切（学生/挑战/状态/完成度/缺失），二者不共享任何中间变量 —— 这证明了管线的
自动化是真实的，而非脚本自己喂给自己。

用法：python gen_sample_submissions.py
"""
import json
import os
import random
import shutil
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "challenge_schema.json")
OUT_DIR = os.path.join(HERE, "submissions")
SEED = 42

# ---------- 学生名册（20 人）----------
# 卢怡然 为真实记录；其余为合成样本
STUDENTS = [
    {"name": "卢怡然", "pinyin": "luyiran", "major": "大数据应用开发", "github": "shuibubao--zz", "real": True},
    {"name": "张伟", "pinyin": "zhangwei", "major": "计算机科学", "github": "zw-sias", "real": False},
    {"name": "李娜", "pinyin": "lina", "major": "软件工程", "github": "ln-sias", "real": False},
    {"name": "王强", "pinyin": "wangqiang", "major": "人工智能", "github": "wq-sias", "real": False},
    {"name": "刘洋", "pinyin": "liuyang", "major": "数据科学", "github": "ly-sias", "real": False},
    {"name": "陈静", "pinyin": "chenjing", "major": "网络空间安全", "github": "cj-sias", "real": False},
    {"name": "杨帆", "pinyin": "yangfan", "major": "物联网", "github": "yf-sias", "real": False},
    {"name": "赵磊", "pinyin": "zhaolei", "major": "软件工程", "github": "zl-sias", "real": False},
    {"name": "黄敏", "pinyin": "huangmin", "major": "计算机科学", "github": "hm-sias", "real": False},
    {"name": "周涛", "pinyin": "zhoutao", "major": "人工智能", "github": "zt-sias", "real": False},
    {"name": "吴婷", "pinyin": "wuting", "major": "数字媒体", "github": "wt-sias", "real": False},
    {"name": "徐杰", "pinyin": "xujie", "major": "数据科学", "github": "xj-sias", "real": False},
    {"name": "孙丽", "pinyin": "sunli", "major": "软件工程", "github": "sl-sias", "real": False},
    {"name": "马超", "pinyin": "machao", "major": "网络空间安全", "github": "mc-sias", "real": False},
    {"name": "朱琳", "pinyin": "zhulin", "major": "物联网", "github": "zl2-sias", "real": False},
    {"name": "胡军", "pinyin": "hujun", "major": "人工智能", "github": "hj-sias", "real": False},
    {"name": "郭薇", "pinyin": "guowei", "major": "计算机科学", "github": "gw-sias", "real": False},
    {"name": "林峰", "pinyin": "linfeng", "major": "数据科学", "github": "lf-sias", "real": False},
    {"name": "何雪", "pinyin": "hexue", "major": "数字媒体", "github": "hx-sias", "real": False},
    {"name": "高翔", "pinyin": "gaoxiang", "major": "软件工程", "github": "gx-sias", "real": False},
]

# 卢怡然真实进度覆盖（基于本会话实际产出）
LUYIRAN_REAL = {
    "C2A": "complete", "C2G": "complete", "C3": "complete", "C4A": "complete",
    "C4B": "complete", "C5": "complete", "C5A": "complete", "C6": "complete",
    "C6A": "complete", "C4C": "missing", "C4D": "missing",
}

# 各挑战被"尝试"的基础概率（硬核工程挑战 C4C/C4D 尝试率低）
ATTEMPT_BASE = {
    "C2A": 0.95, "C2G": 0.85, "C3": 0.9, "C4A": 0.8, "C4B": 0.8,
    "C4C": 0.5, "C4D": 0.45, "C5": 0.85, "C5A": 0.8, "C6": 0.75, "C6A": 0.7,
}


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def write_file(path, content, mtime):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    os.utime(path, (mtime, mtime))


def write_dir(path, mtime):
    os.makedirs(path, exist_ok=True)
    keep = os.path.join(path, ".keep")
    with open(keep, "w", encoding="utf-8") as f:
        f.write("# 目录型交付物占位标记\n")
    os.utime(keep, (mtime, mtime))


def placeholder_content(student, ch, label):
    return (
        f"# {student['name']} · {ch} · {label}\n\n"
        f"> 本文件为 C6A 样本数据生成器产出的占位文件，仅用于演示扫描/校验管线。\n"
        f"> 真实提交应由对应同学按 Elite20 命名规范交付。\n"
    )


def main():
    random.seed(SEED)
    schema = load_schema()
    challenges = schema["challenges"]

    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    epoch0 = datetime(2026, 3, 1).timestamp()

    for st in STUDENTS:
        st_dir = os.path.join(OUT_DIR, st["name"])
        os.makedirs(st_dir, exist_ok=True)
        # 每个学生一个基线"勤奋度"，决定文件齐备率
        diligence = random.uniform(0.45, 0.96)
        for ch, cdef in challenges.items():
            if st["real"]:
                state = LUYIRAN_REAL.get(ch, "missing")
                attempted = state != "missing"
            else:
                attempted = random.random() < ATTEMPT_BASE.get(ch, 0.7)
                state = None

            if not attempted:
                continue

            # 模拟提交时间：越早的挑战提交越早
            ch_idx = list(challenges.keys()).index(ch)
            days = ch_idx * 12 + random.randint(0, 40)
            mtime = epoch0 + days * 86400 + random.randint(0, 86400)

            for rf in cdef["required_files"]:
                if rf.get("kind") == "dir":
                    # 目录型交付物：目录名 = 学生 + pattern 去掉前导 * 后的部分
                    present = (st["real"]) or (random.random() < diligence + 0.05)
                    if present:
                        dir_name = st["name"] + rf["pattern"][1:]  # *_C5A_screenshots -> 卢怡然_C5A_screenshots
                        write_dir(os.path.join(st_dir, dir_name), mtime)
                    continue
                # 文件型
                if st["real"]:
                    present = True
                else:
                    base = diligence
                    if rf.get("is_ai_log"):
                        base -= 0.18  # AI日志 是最常被漏交的必填项
                    if rf.get("core"):
                        base += 0.08
                    present = random.random() < base
                if present:
                    fname = rf["pattern"].replace("*", st["name"])
                    # 去掉 glob 残留（pattern 形如 *_C2A_方案设计.md）
                    if fname.endswith(".*"):
                        fname = fname[:-2] + ".skill"
                    write_file(os.path.join(st_dir, fname),
                               placeholder_content(st, ch, rf["label"]), mtime)

    # 汇总
    total_files = sum(len(files) for _, _, files in os.walk(OUT_DIR))
    print(f"✅ 已生成样本提交目录：{OUT_DIR}")
    print(f"   学生数：{len(STUDENTS)}（含 1 名真实：卢怡然）")
    print(f"   挑战数：{len(challenges)}")
    print(f"   落地文件/目录标记总数：{total_files}")
    print(f"   确定性种子：{SEED}（可复现：删除 submissions/ 后重跑结果一致）")


if __name__ == "__main__":
    main()
