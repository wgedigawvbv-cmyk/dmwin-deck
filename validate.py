"""窓の働きを1つずつ確かめる（エンジンが窓理論どおりに動いているか）"""
from engine import play_match
from seeds import SEEDS, PASSIVE

N = 1500


def pct(x):
    return f"{x * 100:5.1f}%"


def with_cards(base, add, remove_from=("filler",)):
    c = dict(base[0])
    for k, n in add.items():
        c[k] = c.get(k, 0) + n
        left = n
        for r in remove_from:
            take = min(left, c.get(r, 0))
            c[r] = c.get(r, 0) - take
            left -= take
    c = {k: v for k, v in c.items() if v}
    assert sum(c.values()) == 40
    return (c, base[1])


print("■ 1. 何もしない相手に対して、各デッキはどの経路で、何ターン目に勝つか")
for name, deck in SEEDS.items():
    wr, paths, rounds = play_match(deck, PASSIVE, N, seed=1)
    tot = sum(paths.values()) or 1
    ps = "・".join(f"{k} {v / tot * 100:.0f}%" for k, v in sorted(paths.items(), key=lambda x: -x[1]))
    print(f"  {name:12s} 勝率 {pct(wr)}｜平均 {rounds:4.1f}ターン目まで｜勝ち筋 {ps}")

print("\n■ 2. 封殺は狙った経路だけを止めるか（相手＝何もしない＋メタクリーチャー8枚、攻撃はしない）")
metas = [("なし", {}), ("トリガー封じ", {"m_trig": 8}), ("踏み倒し封じ", {"m_free": 8}), ("呪文制限", {"m_spell": 8}),
         ("出たターン攻撃不可", {"m_attack": 8}), ("展開制限", {"m_summon": 8})]
for name in ("入れ替え", "連鎖の特殊勝利", "呪文ループ", "速さ（攻撃で割る）"):
    row = []
    for mname, add in metas:
        opp = with_cards(PASSIVE, add)
        wr, paths, rounds = play_match(SEEDS[name], opp, N, seed=2)
        main = {"入れ替え": "SWAP", "連鎖の特殊勝利": "CHAIN", "呪文ループ": "LOOP", "速さ（攻撃で割る）": "ATTACK"}[name]
        share = paths.get(main, 0) / max(1, sum(paths.values()))
        row.append(f"{mname} {rounds:4.1f}T/{share * 100:3.0f}%")
    print(f"  {name}：" + "｜".join(row))
print("  （数字は「平均の決着ターン／本来の経路で勝った割合」）")

print("\n■ 3. トリガー封じは、受け型のトリガーと0コスト受けを止めるか（速さ vs 受け）")
base = SEEDS["速さ（攻撃で割る）"]
with_trig = ({**{k: v for k, v in base[0].items()}, "m_trig": 4, "m_free": 4, "b1": 4, "sa2": 4}, 1)
assert sum(with_trig[0].values()) == 40
for label, deck in [("封殺なし", base), ("トリガー封じ4＋踏み倒し封じ4（代わりに小型とSAを減らす）", with_trig)]:
    wr, _, _ = play_match(deck, SEEDS["受け（トリガー）"], N, seed=3)
    print(f"  速さ（{label}）vs 受け：{pct(wr)}")

print("\n■ 4. 除去は封殺を壊し、保護はそれを防ぐか（連鎖デッキに除去4枚 vs 踏み倒し封じ8枚）")
chain_rm = ({**SEEDS["連鎖の特殊勝利"][0], "draw": 4, "removal": 4}, 0)
assert sum(chain_rm[0].values()) == 40
for label, add in [("踏み倒し封じ（保護なし）", {"m_free": 4}), ("踏み倒し封じ（保護つき）", {"m_free_p": 4})]:
    opp = with_cards(PASSIVE, add)
    for dl, deck in [("除去なし", SEEDS["連鎖の特殊勝利"]), ("除去4枚", chain_rm)]:
        wr, paths, rounds = play_match(deck, opp, N, seed=4)
        share = paths.get("CHAIN", 0) / max(1, sum(paths.values()))
        print(f"  相手 {label}｜連鎖デッキ {dl}：平均 {rounds:4.1f}T・連鎖で勝った割合 {share * 100:3.0f}%")
