#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建《宋词正典》模块（modules/01_songci-quanji.md）。

数据源：chinese-poetry 开源数据集「宋词」（ci.song.*.json，共 22 个分卷）。
流程：繁→简（zhconv）→ 空白/标点归一 → 去重 → 剔残句 → 按词人分组排序 → 输出 Markdown。

用法：
    python build_corpus.py --src <原始 json 目录> --out <模块路径> [--report <统计 json>]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, OrderedDict

# 词史序（用于词人分组排序；未列者按 Unicode 序排在其后）
CI_ORDER = [
    # 唐五代（正典不收，仅用于排序兜底）
    "温庭筠", "韦庄", "冯延巳", "李煜",
    # 北宋前期
    "和岘", "王禹偁", "寇准", "潘阆", "林逋", "柳永", "范仲淹", "张先",
    "晏殊", "欧阳修", "宋祁", "梅尧臣", "王安石", "王琪", "杜安世",
    # 北宋中后期
    "晏几道", "苏轼", "黄庭坚", "秦观", "贺铸", "晁补之", "周邦彦", "李之仪", "毛滂",
    # 南渡
    "李清照", "朱敦儒", "张元干", "叶梦得", "陈与义", "岳飞", "李纲",
    # 南宋中
    "陆游", "范成大", "杨万里", "张孝祥", "辛弃疾", "陈亮", "刘过", "姜夔",
    "史达祖", "刘克庄", "吴潜", "吴文英", "高观国",
    # 宋末元初
    "周密", "王沂孙", "蒋捷", "张炎", "刘辰翁", "文天祥", "汪元量", "陈允平",
]

WS = re.compile(r"[ \t\u3000]+")


def load(src_dir):
    recs = []
    names = sorted(
        [f for f in os.listdir(src_dir) if f.startswith("ci.song.") and f.endswith(".json")],
        key=lambda x: int(re.findall(r"\d+", x)[0]),
    )
    for n in names:
        with open(os.path.join(src_dir, n), encoding="utf-8") as fh:
            recs.extend(json.load(fh))
    return recs, names


def clean_text(s, conv):
    s = conv(s)
    s = WS.sub("", s)
    s = s.replace("\u200b", "").replace("\ufeff", "")
    return s.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--zhconv-path", default=None, help="zhconv 包所在目录（可选）")
    args = ap.parse_args()

    if args.zhconv_path:
        sys.path.insert(0, args.zhconv_path)
    try:
        import zhconv
        conv = lambda s: zhconv.convert(s, "zh-cn")
        conv_mode = "zhconv 1.4.1 (zh-cn)"
    except Exception:  # 无依赖时降级为恒等映射，并在报告中标明
        conv = lambda s: s
        conv_mode = "未启用（恒等映射）"

    raw, names = load(args.src)
    stat = OrderedDict()
    stat["分卷文件"] = len(names)
    stat["原始条目"] = len(raw)
    stat["繁简转换"] = conv_mode

    # 1) 清洗 + 结构校验
    recs, bad_struct = [], 0
    for r in raw:
        a = clean_text(r.get("author") or "", conv) or "无名氏"
        rh = clean_text(r.get("rhythmic") or "", conv) or "（失调名）"
        ps = [clean_text(p, conv) for p in (r.get("paragraphs") or [])]
        ps = [p for p in ps if p]
        if not ps:
            bad_struct += 1
            continue
        recs.append({"author": a, "rhythmic": rh, "paragraphs": ps})
    stat["结构异常（无正文）"] = bad_struct

    # 2) 去重：同作者 + 同词牌 + 同正文
    seen, dedup, dup_cnt = set(), [], 0
    for r in recs:
        key = (r["author"], r["rhythmic"], "".join(r["paragraphs"]))
        if key in seen:
            dup_cnt += 1
            continue
        seen.add(key)
        dedup.append(r)
    stat["重复剔除"] = dup_cnt

    # 3) 剔残句（正文总字数 < 8，且未含完整句读）
    keep, frag = [], 0
    for r in dedup:
        body = "".join(r["paragraphs"])
        if len(re.sub(r"[^\u4e00-\u9fff]", "", body)) < 8:
            frag += 1
            continue
        keep.append(r)
    stat["残句剔除"] = frag
    stat["正典收录"] = len(keep)

    # 4) 分组排序
    order_idx = {n: i for i, n in enumerate(CI_ORDER)}
    by_author = {}
    for r in keep:
        by_author.setdefault(r["author"], []).append(r)
    authors = sorted(
        by_author.keys(),
        key=lambda a: (order_idx.get(a, 10 ** 6), -len(by_author[a]), a),
    )
    stat["词人数"] = len(authors)
    stat["词牌数"] = len({r["rhythmic"] for r in keep})

    # 5) 输出
    out = []
    out.append("# 宋词正典 · 两宋词辑存")
    out.append("")
    out.append("> **正典性质**：本模块为两宋词**辑存本**（非校勘本、非全集），共 **{} 首 / {} 位词人 / {} 个词牌**，"
               "简体（zhconv zh-cn 转换）。数据源见 `modules/03_corpus-notes.md`。".format(
                   len(keep), len(authors), stat["词牌数"]))
    out.append("> **检索约定**：词人手 `## 作者（N 首）`，单篇手 `### 词牌·首句`，正文按**韵段**逐行缩进。"
               "跨韵段引文须分段检索，不可整段匹配。")
    out.append("> **边界铁律**：本辑未收 **≠** 该词人无此作（见 `modules/03_corpus-notes.md` §四）。")
    out.append("")
    out.append("---")
    out.append("")

    # 词人总览表
    out.append("## 词人总览（按词史序）")
    out.append("")
    out.append("| 序 | 词人 | 首数 | 序 | 词人 | 首数 | 序 | 词人 | 首数 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    rows = [(i + 1, a, len(by_author[a])) for i, a in enumerate(authors)]
    per_col = (len(rows) + 2) // 3
    cols = [rows[0:per_col], rows[per_col:2 * per_col], rows[2 * per_col:]]
    for i in range(per_col):
        cells = []
        for c in cols:
            if i < len(c):
                cells += ["{}".format(c[i][0]), c[i][1], str(c[i][2])]
            else:
                cells += ["", "", ""]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("---")
    out.append("")

    for a in authors:
        out.append("## {}（{} 首）".format(a, len(by_author[a])))
        out.append("")
        items = sorted(by_author[a], key=lambda r: (r["rhythmic"], r["paragraphs"][0]))
        for r in items:
            head = r["rhythmic"]
            first = re.sub(r"[，。、？！；：,.?!;:]", "", r["paragraphs"][0])[:9]
            out.append("### {}·{}".format(head, first))
            for p in r["paragraphs"]:
                out.append("　　" + p)
            out.append("")
        out.append("")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))

    stat["输出行数"] = len(out)
    stat["输出字节"] = os.path.getsize(args.out)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(stat, fh, ensure_ascii=False, indent=2)
    print(json.dumps(stat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
