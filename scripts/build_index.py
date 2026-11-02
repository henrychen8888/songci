#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成索引模块（modules/02_index.md）：词人索引 + 词牌索引。

用法：
    python build_index.py --corpus modules/01_songci-quanji.md --out modules/02_index.md
"""
import argparse
import json
import re
from collections import Counter

HEAD_A = re.compile(r"^## (.+?)（(\d+) 首）$")
HEAD_C = re.compile(r"^### (.+?)·")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-ci", type=int, default=120)
    args = ap.parse_args()

    authors, cipai = [], Counter()
    with open(args.corpus, encoding="utf-8") as fh:
        for line in fh:
            m = HEAD_A.match(line.rstrip("\n"))
            if m:
                authors.append((m.group(1), int(m.group(2))))
                continue
            m2 = HEAD_C.match(line.rstrip("\n"))
            if m2:
                cipai[m2.group(1)] += 1

    total = sum(n for _, n in authors)
    out = []
    out.append("# 索引 · 词人与词牌")
    out.append("")
    out.append("> 本文件由 `scripts/build_index.py` 从正典自动生成，供快速定位。**不含正文**，查原文请回正典。")
    out.append("> 总计：**{} 首 / {} 位词人 / {} 个词牌**。".format(total, len(authors), len(cipai)))
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 一、词人索引（按首数降序）")
    out.append("")
    out.append("> 查某人：在本表中找名字，再在正典中 `grep \"^## 名字（\"` 定位该词人分组。")
    out.append("> ⚠️ **首数 ≠ 成就**：存佚悬殊极大（存词 ≤ 2 首者占 64.4%）。")
    out.append("")
    out.append("| 序 | 词人 | 首数 | 序 | 词人 | 首数 | 序 | 词人 | 首数 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    ordered = sorted(authors, key=lambda x: (-x[1], x[0]))
    per = (len(ordered) + 2) // 3
    cols = [ordered[0:per], ordered[per:2 * per], ordered[2 * per:]]
    for i in range(per):
        cells = []
        for c in cols:
            if i < len(c):
                cells += [str(i + 1 + (cols.index(c) * per)), c[i][0], str(c[i][1])]
            else:
                cells += ["", "", ""]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 二、词牌索引（前 {} 个）".format(args.top_ci))
    out.append("")
    out.append("> 查某调：在本表找词牌，再在正典中 `grep \"^### 词牌·\"` 列出该调全部篇目。")
    out.append("> 注意：数据集中部分词牌为合称（如「木兰花・玉楼春」），检索时两个名字都要试。")
    out.append("")
    out.append("| 序 | 词牌 | 首数 | 序 | 词牌 | 首数 | 序 | 词牌 | 首数 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    top = cipai.most_common(args.top_ci)
    per = (len(top) + 2) // 3
    cols = [top[0:per], top[per:2 * per], top[2 * per:]]
    for i in range(per):
        cells = []
        for k, c in enumerate(cols):
            if i < len(c):
                cells += [str(i + 1 + k * per), c[i][0], str(c[i][1])]
            else:
                cells += ["", "", ""]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    rest = len(cipai) - len(top)
    if rest > 0:
        out.append("> 其余 **{}** 个词牌（多为仅一二首的冷调）未列出，可用 `grep -o \"^### [^·]*\"` 自行统计。".format(rest))
    out.append("")
    out.append("---")
    out.append("")
    out.append("*（自动生成，勿手改。重跑：`python scripts/build_index.py --corpus modules/01_songci-quanji.md --out modules/02_index.md`）*")

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print(json.dumps({"词人": len(authors), "词牌": len(cipai), "行数": len(out),
                      "字节": sum(len(x.encode()) for x in out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
