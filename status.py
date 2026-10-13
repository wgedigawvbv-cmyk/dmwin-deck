#!/usr/bin/env python3
"""実装したカードの一覧と、実装の正確さを書き出す

  python status.py            画面に出す
  python status.py cards.md   ファイルに書き出す
"""
import sys

import engine3                        # noqa: F401  （新カードを登録する）
import envreg
from cards3 import BY_KEY, DECKS, POOL

CIV = {"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}
KIND = {"C": "クリーチャー", "S": "呪文", "T": "タマシード", "G": "G城", "X": "クロスギア", "K": "禁断の鼓動"}


def civja(c):
    return "・".join(CIV[x] for x in c.civ) if c.civ else "無色"


def lines():
    out = []
    base = [c for c in POOL if c.key not in envreg.STATUS]
    out.append("# 実装したカードの一覧\n")
    out.append(f"合計 {len(POOL)} 枚（もとの札束 {len(base)} 枚＋ネットで調べて足した {len(envreg.STATUS)} 枚）\n")
    out.append("`full`＝カードに書かれている効果を全部実装／`partial`＝省いた部分がある（理由を書いた）／"
               "`approx`＝部品の並びでの近似登録。\n")
    out.append("どのカードも「どれを選ぶか」「任意効果を使うか」は、このシミュレーター共通の決まりで機械的に決める"
               "（これは省略ではなく、全デッキに同じやり方を使うための決まり）。\n")
    st = {}
    for k, v in envreg.STATUS.items():
        st[v[0]] = st.get(v[0], 0) + 1
    out.append("実装の正確さ：" + "、".join(f"{a} {b}枚" for a, b in sorted(st.items())) + "\n")

    out.append("\n## ネットで調べて足したカード\n")
    out.append("| カード | コスト | 文明 | 種類 | 実装 | 省いた点 | 出典 |")
    out.append("|---|---|---|---|---|---|---|")
    for k in sorted(envreg.STATUS, key=lambda k: (BY_KEY[k].cost, k)):
        c = BY_KEY[k]
        stt, note, src, _text, _nm = envreg.STATUS[k]
        out.append(f"| {c.name} | {c.cost} | {civja(c)} | {KIND.get(c.kind, c.kind)} | {stt} | {note or '—'} | {src} |")

    out.append("\n## カードの効果（自分の言葉で書いたもの）\n")
    for k in sorted(envreg.STATUS, key=lambda k: (BY_KEY[k].cost, k)):
        c = BY_KEY[k]
        stt, note, src, text, _nm = envreg.STATUS[k]
        out.append(f"### {c.name}（コスト{c.cost}／{civja(c)}／{KIND.get(c.kind, c.kind)}"
                   + (f"／パワー{c.power}" if c.kind == 'C' else "") + ")")
        out.append(text or "（効果なし）")
        if note:
            out.append(f"**省いた点**：{note}")
        out.append(f"出典：{src}\n")

    out.append("\n## もとからあった札束（cards3.py）\n")
    out.append("| カード | コスト | 文明 | 種類 | note（実装した内容） |")
    out.append("|---|---|---|---|---|")
    for c in sorted(base, key=lambda c: (c.cost, c.key)):
        out.append(f"| {c.name} | {c.cost} | {civja(c)} | {KIND.get(c.kind, c.kind)} | {c.note or '—'} |")

    out.append("\n## 公式カバレージの入賞デッキ（decks8.py が読み込めたもの）\n")
    try:
        import decks8
        ok, bad = decks8.load()
        out.append(f"読み込めたデッキ：{len(ok)}／読み込めなかったデッキ：{len(bad)}\n")
        for n, a in ok.items():
            d = a["deck"]
            out.append(f"- **{n}**（{sum(d.values())}枚／出典 {a['source']}）：" + "、".join(
                f"{BY_KEY[k].name}×{v}" for k, v in sorted(d.items(), key=lambda kv: BY_KEY[kv[0]].cost)))
        for n, why, src in bad:
            out.append(f"- （使えない）{n}：{why}")
    except Exception as e:
        out.append(f"（読み込めませんでした：{e}）")
    out.append("\n## デッキ（手で写した7つと、デッキタイプ5つ）\n")
    import archetypes
    for n, d in DECKS.items():
        out.append(f"- **{n}**（実在／40枚）：" + "、".join(f"{BY_KEY[k].name}×{v}"
                                                      for k, v in sorted(d.items(), key=lambda kv: BY_KEY[kv[0]].cost)))
    for n, a in archetypes.ARCHETYPES.items():
        d = a["deck"]
        out.append(f"- **{n}**（ネットで調べたタイプ／40枚）：" + "、".join(
            f"{BY_KEY[k].name}×{v}" for k, v in sorted(d.items(), key=lambda kv: BY_KEY[kv[0]].cost)))
        out.append(f"  - 出典：{a['source']}／入れ替えた点：{a['subs']}")
    return out


if __name__ == "__main__":
    txt = "\n".join(lines())
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(txt + "\n")
        print(f"書き出しました：{sys.argv[1]}（{len(txt)}文字）")
    else:
        print(txt)
