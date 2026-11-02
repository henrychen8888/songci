#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建《词源补遗》模块（modules/02_buyi.md）。

收录五代词源两部：花间集（447 首，晚唐五代 18 家）+ 南唐二主词（李璟、李煜 45 首）。
数据源：chinese-poetry 仓库 五代诗词/huajianji/*.json 与 五代诗词/nantang/poetrys.json。
用途：宋词之源。**不入正典**（正典仅收宋词），引用时须标「补遗」。

用法：
    python build_buyi.py --src <目录> --out <模块路径> [--zhconv-path <目录>]
"""
import argparse
import json
import os
import re
import sys

WS = re.compile(r"[ \t\u3000]+")


def clean(s, conv):
    return WS.sub("", conv(s or "")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--zhconv-path", default=None)
    args = ap.parse_args()

    if args.zhconv_path:
        sys.path.insert(0, args.zhconv_path)
    try:
        import zhconv
        conv = lambda s: zhconv.convert(s, "zh-cn")
    except Exception:
        conv = lambda s: s

    items = []
    # 花间集
    names = sorted(
        [f for f in os.listdir(args.src) if f.startswith("huajianji-") and f.endswith(".json")],
        key=lambda x: int(re.findall(r"\d+", x)[0]),
    )
    for n in names:
        try:
            with open(os.path.join(args.src, n), encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue  # 个别分卷可能不存在
        for r in data:
            rh = clean(r.get("rhythmic") or (r.get("title") or "").split(" ")[0], conv)
            items.append({
                "book": "花间集",
                "author": clean(r.get("author"), conv) or "无名氏",
                "rhythmic": rh or "（失调名）",
                "title": clean(r.get("title"), conv),
                "paragraphs": [clean(p, conv) for p in (r.get("paragraphs") or []) if clean(p, conv)],
            })
    # 南唐二主词
    nt = os.path.join(args.src, "nantang.json")
    if os.path.exists(nt):
        with open(nt, encoding="utf-8") as fh:
            for r in json.load(fh):
                items.append({
                    "book": "南唐二主词",
                    "author": clean(r.get("author"), conv),
                    "rhythmic": clean(r.get("rhythmic"), conv) or "（失调名）",
                    "title": clean(r.get("title"), conv),
                    "paragraphs": [clean(p, conv) for p in (r.get("paragraphs") or []) if clean(p, conv)],
                })

    items = [i for i in items if i["paragraphs"]]
    out = []
    out.append("# 词源补遗 · 花间集与南唐二主词")
    out.append("")
    out.append("> **性质**：本模块收**五代词源**，非宋词，**不入正典**。凡引此处词句，须标「补遗」而非「正典」。")
    out.append("> **数据源**：chinese-poetry 仓库「五代诗词」（花间集、南唐二主词），经繁→简与空白归一。")
    out.append("> **收录范围**：花间集 **9 卷 447 首**（数据源第 10 卷文件缺失，故不足 500 首之数，非原书残阙）；南唐二主词 **45 首**（李煜 41、李璟 4）。")
    out.append("> **质量警示**：花间集部分篇目存在**讹字**（数据源 OCR 遗留），**仅可作词源示例与风格参照，不可作校勘依据**；引用前须与通行本对校。南唐二主词质量较可靠。")
    out.append("> **未收**：冯延巳《阳春集》、温庭筠别集、敦煌曲子词均未收；不可据此断为「无此作」。")
    out.append("")
    out.append("---")
    out.append("")

    for book in ["花间集", "南唐二主词"]:
        sel = [i for i in items if i["book"] == book]
        if not sel:
            continue
        authors = sorted({i["author"] for i in sel})
        out.append("## {}（{} 首 / {} 家）".format(book, len(sel), len(authors)))
        out.append("")
        for a in authors:
            sub = [i for i in sel if i["author"] == a]
            out.append("### {}".format(a))
            out.append("")
            for r in sub:
                out.append("- **《{}》**".format(r["rhythmic"]))
                for p in r["paragraphs"]:
                    out.append("  　　" + p)
            out.append("")
        out.append("---")
        out.append("")

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print(json.dumps({"收录": len(items), "行数": len(out),
                      "字节": os.path.getsize(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
