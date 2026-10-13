#!/usr/bin/env python3
"""創作者まわりの検査：カードの登録、役割の数え方、デッキがいつも40枚か、デッキタイプが組めるか"""
import random

import archetypes
import creator
import envreg
import netcards
import playable3
import roles3
from cards3 import BY_KEY, POOL

n = 0


def check(name, ok):
    global n
    n += 1
    print(("○ " if ok else "× ") + name)
    if not ok:
        raise SystemExit(1)


st = {}
for _k, _v in envreg.STATUS.items():
    st[_v[0]] = st.get(_v[0], 0) + 1
check(f"ネットで調べたカードが登録されている（{len(envreg.STATUS)}枚：{st}）", len(envreg.STATUS) >= 80)
check("効果の近似（approx）が残っていない", st.get("approx", 0) == 0)
check("すべてのカードに出典がある", all(v[2].startswith("https://") for k, v in envreg.STATUS.items()))
check("すべてのカードに効果の説明がある", all(v[3] for k, v in envreg.STATUS.items()))
check("省いた点があるカードには理由が書いてある",
      all(v[1] for v in envreg.STATUS.values() if v[0] == "partial"))
check("カードのキーが POOL と一致している", len({c.key for c in POOL}) == len(POOL))

check("検査：知らない部品は拒否（近似登録の道具）",
      netcards.validate({"key": "n_x", "name": "x", "cost": 1, "civ": "N", "kind": "S",
                         "source": "https://x", "text": "t", "fx": [["foo"]]}) is not None)

check("役割：ルード・ザーナは引く・除去・ブロッカー", {"draw", "rem", "blk"} <= roles3.roles("n_rudezana"))
check("役割：ゴールデンデン・トラップは除去と加速とトリガー", {"rem", "acc", "trg"} <= roles3.roles("n_goldenden"))
check("役割：モウジャキンガは多くの役割をこなす", len(roles3.roles("n_mouja")) >= 5)
check("役割：ゾンビポンの助はどの役割も担わない", not roles3.roles("pon"))
th = roles3.thinness({"pon": 1, "n_rudezana": 4})
check("薄さ：役割のない札のほうが低い", th["pon"] < th["n_rudezana"])

check("デッキタイプ：枚数と上限に問題がない", not archetypes.check())
keys = sorted(set(creator.BASEKEYS) | set(creator.NETKEYS))
rng = random.Random(3)
for a in creator.load_types():
    d = creator.build_type(a, rng, keys)
    check(f"タイプ「{a['name']}」が40枚で出せる形に組める",
          d is not None and sum(d.values()) == 40 and not playable3.dead(d))

check("もとの札束とネットのカードが分かれている",
      len(creator.BASEKEYS) == 78 and not (set(creator.BASEKEYS) & set(creator.NETKEYS)))
d = creator.concept(rng, creator.BASEKEYS)
check("創作した最初のデッキが40枚", sum(d.values()) == 40)
for i in range(30):
    e = creator.mutate(d, rng, keys) if i % 3 else creator.prune_refill(d, rng, keys)
    if e:
        if sum(e.values()) != 40 or playable3.dead(e):
            check("入れ替え後も40枚で出せる", False)
        d = e
check("入れ替えを30回しても40枚で出せる", sum(d.values()) == 40 and not playable3.dead(d))
for k, v in archetypes.LIMIT.items():
    if creator.cap(k) != v:
        check(f"枚数の上限が守られている（{BY_KEY[k].name}）", False)
check("殿堂入り・ドリーム・禁断の上限が創作者にも効いている", True)

print(f"\n{n}/{n} 通過")
