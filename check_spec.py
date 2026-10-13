#!/usr/bin/env python3
"""実装したカードの数値が、調べた内容（cardspecN.json）と合っているかを突き合わせる

  コスト・文明・種類・パワー・ブレイク数・キーワード（ブロッカー、スピードアタッカー、マッハファイター、
  S・トリガー、G・ストライク、ジャストダイバー、進化）を比べ、食い違いを並べる。

  python check_spec.py
"""
import glob
import json
import unicodedata

import engine3                      # noqa: F401
import envreg
from cards3 import BY_KEY

KW = {"blocker": "blocker", "sa": "sa", "mach": "mach", "trig": "trig", "gs": "gs", "jd": "jd",
      "noatk": "noatk", "noatkp": "noatkp"}


def norm(s):
    s = unicodedata.normalize("NFKC", str(s))
    for a, b in (("＆", "&"), ("：", ":"), ("ー", "-"), ("／", "/"), ("Ⅻ", "XII"), ("～", "~")):
        s = s.replace(a, b)
    return "".join(s.split()).lower()


def main():
    idx = {}
    for c in BY_KEY.values():                      # まずカード名そのもの（単体のカードを優先する）
        idx.setdefault(norm(c.name), c)
    for c in BY_KEY.values():                      # 次にツインパクトの片面の名前
        for part in str(c.name).split("/"):
            idx.setdefault(norm(part), c)
    bad = []
    n = 0
    for f in sorted(glob.glob("cardspec*.json")):
        for d in json.load(open(f, encoding="utf-8"))["cards"]:
            c = idx.get(norm(d["name"]))
            if c is None:
                for h, cc in idx.items():
                    q = norm(d["name"])
                    if len(q) >= 5 and len(h) >= 5 and (q in h or h in q):
                        c = cc
                        break
            if c is None:
                bad.append((d["name"], "実装が見つからない"))
                continue
            n += 1
            diff = []
            if d.get("cost") is not None and c.cost != d["cost"]:
                diff.append(f"コスト {c.cost}≠{d['cost']}")
            if d.get("civ") and set(c.civ) != set(d["civ"]) and not c.twin:
                diff.append(f"文明 {c.civ}≠{d['civ']}")
            if d.get("kind") and c.kind != d["kind"] and not (c.twin and d["kind"] in ("C", "S")):
                diff.append(f"種類 {c.kind}≠{d['kind']}")
            if d.get("power") is not None and c.kind == "C" and c.power != d["power"]:
                diff.append(f"パワー {c.power}≠{d['power']}")
            if d.get("brk") and d["brk"] > 0 and c.brk != d["brk"]:
                diff.append(f"ブレイク数 {c.brk}≠{d['brk']}")
            kws = set(d.get("keywords") or [])
            for want, attr in KW.items():
                if want in kws and not getattr(c, attr):
                    diff.append(f"{want} が付いていない")
            if d.get("evolution") and not c.evo:
                diff.append("進化の指定がない")
            if diff:
                bad.append((d["name"], "／".join(diff)))
    print(f"突き合わせた枚数：{n}")
    print(f"食い違い：{len(bad)}件")
    for nm, why in bad:
        st = envreg.STATUS.get(idx.get(norm(nm)).key) if idx.get(norm(nm)) else None
        print(f"  {nm}：{why}" + (f"（{st[0]}）" if st else ""))


if __name__ == "__main__":
    main()
