#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正典统计：词人/词牌/字频/意象/领字/句式模板。

所有数字均从 modules/01_songci-quanji.md 实时统计产出，可复现。
用法：
    python stats.py --corpus modules/01_songci-quanji.md --out references/_stats.json [--top-ci 50]
"""
import argparse
import json
import re
from collections import Counter, defaultdict

CJK = re.compile(r"[\u4e00-\u9fff]")
PUNCT = "，。、？！；：,.?!;:·"

# 意象分组（用于 references/10）
MOTIF = {
    "天象时令": ["雨", "风", "云", "月", "雪", "霜", "露", "烟", "雾", "斜阳", "夕阳", "落日", "残阳",
                 "春", "秋", "寒", "晓", "暮", "黄昏", "清明", "重阳", "元宵", "七夕"],
    "草木花卉": ["花", "落花", "残红", "梅", "柳", "杨花", "荷", "莲", "菊", "桂", "海棠", "牡丹",
                 "桃", "杏", "梧桐", "芭蕉", "芳草", "绿", "红"],
    "禽鸟虫鱼": ["雁", "燕", "莺", "鹃", "鹧鸪", "鸦", "蝶", "鹤", "蝉", "鱼"],
    "建筑空间": ["楼", "阑干", "栏杆", "帘", "幕", "屏", "窗", "庭", "院", "阁", "亭", "台", "桥", "门", "墙", "深院"],
    "器物服饰": ["酒", "尊", "杯", "盏", "灯", "烛", "香", "篆", "琴", "箫", "笛", "笙", "筝", "舟", "船", "扇", "钗", "簪", "罗衣", "翠袖"],
    "身体情态": ["泪", "鬓", "眉", "眼", "手", "腰", "魂", "梦", "醉", "病", "瘦", "老"],
    "情绪心境": ["愁", "恨", "怨", "思", "忆", "寂寞", "相思", "离", "别", "闲", "空", "无奈", "断肠"],
    "时空人事": ["年", "夜", "时", "旧", "今", "昔", "故人", "何处", "天涯", "江南", "长安", "归"],
}

LINGZI = ["正", "渐", "又", "奈", "看", "念", "叹", "问", "恨", "怕", "算", "料", "想", "记", "忘",
          "但", "任", "便", "纵", "更", "莫", "休", "须", "且", "况", "甚", "怎", "何", "几", "才",
          "早", "已", "独", "自", "共", "与", "最", "甚", "漫", "尽", "顿", "方", "恰", "算", "待"]


def parse(path):
    """把正典 md 解析为 [(author, rhythmic, title_first, [paragraphs])]。"""
    out, author, cur = [], None, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("## ") and "（" in line:
                author = line[3:].split("（")[0].strip()
            elif line.startswith("### "):
                head = line[4:]
                rh, _, first = head.partition("·")
                cur = {"author": author, "rhythmic": rh, "first": first, "paragraphs": []}
                out.append(cur)
            elif line.startswith("　　") and cur is not None:
                cur["paragraphs"].append(line[2:])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-ci", type=int, default=50)
    args = ap.parse_args()

    recs = parse(args.corpus)
    rep = {"正典篇数": len(recs)}

    # 词人
    ac = Counter(r["author"] for r in recs)
    rep["词人数"] = len(ac)
    rep["词人TOP60"] = ac.most_common(60)

    # 词牌
    rc = Counter(r["rhythmic"] for r in recs)
    rep["词牌数"] = len(rc)
    rep["词牌TOP60"] = rc.most_common(60)

    # 字频（仅汉字）
    chars = Counter()
    for r in recs:
        for p in r["paragraphs"]:
            for ch in p:
                if CJK.match(ch):
                    chars[ch] += 1
    rep["单字TOP100"] = chars.most_common(100)
    rep["总字数"] = sum(chars.values())

    # 意象词频（短语级：在正文中统计出现次数）
    full = [p for r in recs for p in r["paragraphs"]]
    joined = "\n".join(full)
    motifs = {}
    for grp, words in MOTIF.items():
        motifs[grp] = sorted(
            [(w, joined.count(w)) for w in words], key=lambda x: -x[1]
        )
    rep["意象词频"] = motifs

    # 领字（句首单字频次，仅统计韵段首字）
    lead = Counter()
    for p in full:
        if p and CJK.match(p[0]):
            lead[p[0]] += 1
    rep["句首单字TOP60"] = lead.most_common(60)
    rep["领字候选频次"] = sorted(
        [(w, lead.get(w[0], 0)) for w in dict.fromkeys(LINGZI)], key=lambda x: -x[1]
    )

    # 句式模板：按词牌统计字数/句数/最常见句长序列
    per = defaultdict(list)
    for r in recs:
        lens = [len(CJK.findall(p)) for p in r["paragraphs"]]
        lens = [x for x in lens if x]
        if lens:
            per[r["rhythmic"]].append(lens)
    tpl = {}
    for rh, _ in rc.most_common(args.top_ci):
        seqs = per[rh]
        total = [sum(s) for s in seqs]
        seg = [len(s) for s in seqs]
        cseq = Counter(tuple(s) for s in seqs).most_common(3)
        tpl[rh] = {
            "篇数": len(seqs),
            "字数中位数": sorted(total)[len(total) // 2],
            "字数区间": [min(total), max(total)],
            "韵段数众数": Counter(seg).most_common(1)[0][0],
            "常见句长模板": [{"模板": list(k), "篇数": v} for k, v in cseq],
        }
    rep["词牌句式模板"] = tpl
    rep["句长区间分布"] = Counter(
        len(CJK.findall(p)) for p in full
    ).most_common(25)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: (v if not isinstance(v, list) else ("<%d 项>" % len(v)))
                      for k, v in rep.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
