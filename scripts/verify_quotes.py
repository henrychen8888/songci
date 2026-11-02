#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用核验：把 Markdown 中「」内的引文逐一在正典/补遗中检索。

规则：
1. 只核验「词句」类引文——含书名号、省略号、×、冒号、括号、ASCII 的引号视为术语或示例，跳过。
2. 匹配时先整串比对，失败则按标点切句、取最长分句比对；比对前剥离空白与标点（只留汉字），
   因此「、，。」的位置差异不影响命中。
3. `references/_quote-whitelist.txt` 中列出的是**确属词话、序跋、笔记等文献引文**，
   不作词句核验（每行一条，允许 # 注释）。凡新增此类引文，须加入白名单并注出处。

退出码：0 = 全部命中；1 = 存在未命中。

用法：
    python verify_quotes.py --corpus modules/01_songci-quanji.md \\
        --buyi modules/02_buyi.md --whitelist references/_quote-whitelist.txt \\
        --docs SKILL.md "references/*.md" "cases/*.md"
"""
import argparse
import glob
import os
import re
import sys

QUOTE = re.compile(r"「([^「」]{2,80})」")
SPLIT = re.compile(r"[，。、；：？！,;:!?\s·]")
CJK = re.compile(r"[\u4e00-\u9fff]")
# 非词句特征：书名号、省略号、乘号、冒号、括号、ASCII
NON_VERSE = re.compile(r"[《》『』×…：:()（）A-Za-z0-9]")


def norm(s):
    """只保留汉字。"""
    s = s.replace("**", "").replace("*", "")
    return "".join(CJK.findall(s))


def load_text(paths):
    buf = []
    for p in paths:
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                buf.append(fh.read())
    return norm("\n".join(buf))


def load_whitelist(paths):
    wl = set()
    for p in paths:
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        wl.add(norm(line))
    return wl


def match(raw, pool):
    """整串 → 分句（按原始标点切）取最长，任一命中即算命中。"""
    if not pool:
        return False
    nq = norm(raw)
    if nq and nq in pool:
        return True
    parts = sorted({norm(p) for p in SPLIT.split(raw)}, key=len, reverse=True)
    for p in parts:
        if len(p) >= 4 and p in pool:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--buyi", default=None)
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--whitelist", nargs="*", default=[])
    args = ap.parse_args()

    corpus = load_text([args.corpus])
    buyi = load_text([args.buyi])
    wl = load_whitelist(args.whitelist)

    files = []
    for d in args.docs:
        files.extend(sorted(glob.glob(d)))
    files = [f for f in dict.fromkeys(files) if os.path.isfile(f)]

    total = hit_c = hit_b = 0
    skipped = whitelisted = 0
    miss = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                for m in QUOTE.finditer(line):
                    q = m.group(1)
                    # 仅核验「像词句」的引文：含句读，或长度 >= 10 字；其余视为术语/示例
                    looks_verse = bool(re.search(r"[，、；]", q)) or len(norm(q)) >= 10
                    if NON_VERSE.search(q) or not looks_verse:
                        skipped += 1
                        continue
                    if norm(q) in wl:
                        whitelisted += 1
                        continue
                    total += 1
                    if match(q, corpus):
                        hit_c += 1
                    elif match(q, buyi):
                        hit_b += 1
                    else:
                        miss.append((f, ln, q))

    print("扫描文件：%d" % len(files))
    print("核验引文：%d（正典 %d / 补遗 %d / 未命中 %d）" % (total, hit_c, hit_b, len(miss)))
    print("跳过：术语与示例 %d 条；文献白名单 %d 条" % (skipped, whitelisted))
    for f, ln, q in miss:
        print("MISS  %s:%d  「%s」" % (f, ln, q))
    sys.exit(0 if not miss else 1)


if __name__ == "__main__":
    main()
