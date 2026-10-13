#!/usr/bin/env python3
"""公式カバレージの入賞デッキリストを、シミュレーターのデッキに変換する

  env_lists.json ／ env_lists_b.json ／ env_lists_c.json … 公式サイトのテキストカバレージ・デッキリストから書き取った採用リスト
  （カード名と枚数。出典URLつき）。カード名を実装したカードのキーに対応させ、40枚そろっているものを使う。
  40枚でないもの、未実装のカードを含むものは使わない。
  殿堂入りの枚数を超えて見えるリストは、こちらの殿堂の判定（カードの説明文からの自動判定）が誤っている可能性があるため、
  リストのとおりに読み込み、over に記録して知らせるだけにする。

  python decks8.py          変換できたデッキと、変換できなかった理由を一覧する
"""
import json
import unicodedata

import archetypes
import engine3                       # noqa: F401  （カードを登録してから使う）
import playable3
from cards3 import BY_KEY

FILES = ("env_lists.json", "env_lists_b.json", "env_lists_c.json", "deck_jokers.json")
ALIAS = {           # 書き取りのゆれ（同じカードの別表記）
    "改竜の炎 ボルメテウス・ハック": "改竄の炎 ボルメテウス・ハック",
}


def norm(s):
    """カード名を突き合わせるための正規化（全角半角・記号・空白の違いを吸収する）"""
    s = unicodedata.normalize("NFKC", str(s))
    for a, b in (("＆", "&"), ("：", ":"), ("ー", "-"), ("－", "-"), ("―", "-"), ("〜", "~"), ("～", "~"),
                 ("／", "/"), ("Ⅻ", "XII"), ("Ⅹ", "X"), ("“", '"'), ("”", '"'), ("＜", "<"), ("＞", ">")):
        s = s.replace(a, b)
    return "".join(s.split()).lower()


def _index():
    idx = {}
    for c in BY_KEY.values():                    # まず名前そのもの（単体のカードを優先して引けるように）
        idx.setdefault(norm(c.name), c.key)
    for c in BY_KEY.values():
        for part in str(c.name).split("/"):      # ツインパクトは、まだ無い名前だけ片面の名前でも引けるように
            idx.setdefault(norm(part), c.key)
    return idx


def find(name, idx):
    q = norm(ALIAS.get(str(name).strip(), name))
    if q in idx:
        return idx[q]
    for h, k in idx.items():                     # 片方がもう片方を含む（「改竜の炎」と「改竄の炎」のような差は拾えない）
        if len(q) >= 5 and len(h) >= 5 and (q in h or h in q):
            return k
    return None


def load(verbose=False):
    """{デッキ名: {カードのキー: 枚数}} と、使えなかったデッキの理由を返す"""
    idx = _index()
    out, skipped = {}, []
    for f in FILES:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except FileNotFoundError:
            continue
        for d in data.get("decks", []):
            deck, miss = {}, []
            for nm, v in d["cards"].items():
                k = find(nm, idx)
                if k is None:
                    miss.append(nm)
                else:
                    deck[k] = deck.get(k, 0) + v
            n = sum(deck.values())
            why = None
            over = [f"{BY_KEY[k].name}×{v}（上限{archetypes.LIMIT.get(k, 4)}枚）"
                    for k, v in deck.items() if v > archetypes.LIMIT.get(k, 4)]
            if miss:
                why = "未実装のカード：" + "、".join(miss)
            elif n != 40:
                why = f"{n}枚（40枚でない）"
            elif over and any(archetypes.LIMIT.get(k, 4) == 0 for k in deck):
                why = "使えないカードを含む：" + "、".join(over)
            if why:
                skipped.append((d["name"], why, d.get("source", "")))
                continue
            out[d["name"]] = {"deck": deck, "source": d.get("source", ""), "over": over}
    return out, skipped


DECKS8 = {n: a["deck"] for n, a in load()[0].items()}
SOURCES = {n: a["source"] for n, a in load()[0].items()}


# ------------------------------------------------------------------ 公開用：使用者名を外す
_RANKS = ("準優勝", "優勝", "1位", "2位", "3位", "4位", "5位", "6位", "7位", "8位")  # 「準優勝」を先に見る


def anon_one(n):
    """デッキ名から使用者の名前・ハンドルを外す（大会・順位・デッキの型は残す）。

    入賞リストの出典は公式カバレージなので情報自体は公開されているが、
    **個人のサイトで「この人はこのデッキを使った」という形にして載せ直すのは別の話**。
    デッキを組む側が要るのは「どの大会の何位の、どういう型か」なので、
    名前を外しても失うものはない。手元のファイルは出典をたどれるように名前を残し、
    **配る版（web／公開リポジトリ）だけ**この関数を通す。

    デッキ名は2つの形がある。
      ・「大会 順位 使用者 - デッキの型」…… 使用者だけを抜く。
        「- 」の後ろの丸かっこは型の説明（(ボンメェ2枚型) など）なので触らない。
      ・「デッキの型(使用者)」…………………… 末尾の丸かっこを落とす。
        中に順位が書いてあれば順位だけ残す（(ハンドル名・優勝) → (優勝)）。"""
    import re
    if " - " in n or "－" in n:
        return re.sub(r"(準優勝|優勝|\d+位)\s+[^-－]+?\s+[-－]\s+", r"\1 - ", n).strip()
    m = re.search(r"\(([^()]*)\)\s*$", n)
    if m:
        inner = m.group(1)
        keep = next((r for r in _RANKS if r in inner), "")
        n = n[:m.start()].rstrip()
        if keep:
            n += f"({keep})"
    return n.strip(" 　-－")


def anon_map(names):
    """{もとの名前: 配る版の名前}。名前を外すとぶつかるものには①②…を付けて見分ける"""
    out, used = {}, {}
    for n in sorted(names):
        a = anon_one(n)
        used[a] = used.get(a, 0) + 1
        if used[a] > 1 or sum(1 for x in names if anon_one(x) == a) > 1:
            a = f"{a} {'①②③④⑤⑥⑦⑧⑨⑩⑪⑫'[min(used[a] - 1, 11)]}"
        out[n] = a
    return out


def short(n):
    """表に出すための短い名前（大会・順位・デッキ名）。

    **必ず anon_one を通す**＝表に出す名前に使用者の名前・ハンドルは入らない。
    手元のファイルと配る版で名前が食い違うと、goals.json の当たり先がずれるので、
    どちらでも同じ名前になるようにここで揃える。
    もとの名前（使用者つき）は DECKS8 のキーと env_lists*.json に残してあるので、出典はたどれる。"""
    n = anon_one(n)
    ev = ""
    for a, b in (("超CSⅨ新潟", "CS9"), ("DMGP2026-1st Day2", "GP"), ("超CSⅧ大阪", "CS8阪"),
                 ("超CSⅧ北海道", "CS8道"), ("DMGP2025-2nd Day2", "GP25"), ("全国2025 関東A", "全国関A")):
        if a in n:
            ev = b
            break
    if ev in ("GP25", "全国関A"):
        # 公式カバレージに順位表記がない大会。もとのファイルは使用者名で区別しているが、
        # 配る版は名前を外して①②…に替えてある（anon_one）。どちらでも見分けられるようにする。
        tail = n.rstrip()[-1:]
        if tail in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫":
            return (ev + " " + tail)[:15]
        return (ev + " " + n.split("(")[-1].rstrip(")"))[:15]
    rest = n.split(")", 1)[1] if ")" in n and ev else n
    rank = ""
    for r in ("優勝", "準優勝", "2位", "3位", "4位", "5位", "6位", "7位", "8位"):
        if r in rest:
            rank = r.replace("位", "")
            break
    name = rest.split(" - ", 1)[1] if " - " in rest else rest
    name = name.split("(")[0].strip(" -　")
    if "事前メタ" in n:
        ev, rank, name = "GP", "紹介", "メタ紹介"
    out = (ev + rank + " " + name).strip()
    return out[:15] or n[:15]


if __name__ == "__main__":
    ok, bad = load()
    print(f"使えるデッキ：{len(ok)}／使えないデッキ：{len(bad)}\n")
    for n, a in ok.items():
        d = a["deck"]
        if a.get("over"):
            print(f"  （注）{short(n)}：{'、'.join(a['over'])}")
        dead = playable3.dead(d)
        print(f"○ {short(n):16s} {sum(d.values())}枚  {('出せない札: ' + str({BY_KEY[k].name: v for k, (v, _r) in dead.items()})) if dead else ''}")
    print()
    for n, why, _src in bad:
        print(f"× {n[:40]}：{why}")
