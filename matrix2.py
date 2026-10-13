#!/usr/bin/env python3
"""第2版：デッキ12種類の総当たり

  python matrix2.py        （1分ほど）
"""
import random
from collections import Counter

import engine2
from engine2 import Game
from seeds2 import SEEDS

N = 300
SHORT = {"連鎖速攻（der'Bande型）": "連鎖速攻", "小型速攻（赤単型）": "小型速攻", "ドラゴンビート（ドギラゴン王道型）": "ドラゴン",
         "全ブレイク（墓地ソース型）": "全ブレイク", "一手封殺（ウィリデ・ドギラゴン逆型）": "一手封殺", "呪文ループ（創世竜ループ型）": "呪文ループ",
         "クリーチャーループ（ドッコイ型）": "生物ループ", "連鎖の特殊勝利（ゴルギーオージャー型）": "連鎖特殊", "手札破壊コントロール（邪眼帝型）": "手札破壊",
         "カウンター（バイケン型）": "カウンター", "メタビート": "メタビート", "受け（トリガー）": "受け"}


def main():
    engine2.TEMPO = 1
    rng = random.Random(7)
    names = list(SEEDS)
    win = {a: {} for a in names}
    turns, by4, clean, trig, hand, meta3, lock4, total = 0, 0, 0, 0, 0, 0.0, 0, 0
    endturn = Counter()
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if j < i:
                continue
            w = n = 0
            for g in range(N):
                gm = Game(SEEDS[a], SEEDS[b], rng, first=g % 2)
                r = gm.play()
                if r is None:
                    continue
                n += 1
                w += r == "A"
                total += 1
                turns += gm.round
                endturn[min(gm.round, 8)] += 1
                by4 += gm.round <= 4
                clean += gm.stats["clean"]
                trig += gm.stats["trig"] > 0
                hand += gm.stats["hand"] > 0
                meta3 += gm.stats["meta3"]
                lock4 += gm.stats["lock"].get(r, 99) <= 4
            win[a][b] = w / max(1, n)
            win[b][a] = 1 - w / max(1, n)
    print("【総当たり】テンポ1・各組300戦。行のデッキが列のデッキに勝つ割合（%）")
    print("　｜" + "｜".join(SHORT[n] for n in names) + "｜平均")
    for a in names:
        row = [f"{win[a][b] * 100:.0f}" if a != b else "—" for b in names]
        avg = sum(win[a][b] for b in names if b != a) / (len(names) - 1)
        print(f"{SHORT[a]}｜" + "｜".join(row) + f"｜{avg * 100:.0f}")
    print(f"\n【流れ】{total}戦の平均")
    print(f"  勝ったターンの平均 {turns / total:.1f}／4ターン目までに決着 {by4 / total * 100:.0f}%"
          f"／盾5枚からの1ターンキル {clean / total * 100:.0f}%")
    print("  決着ターンの内訳：" + "、".join(f"{t}{'以降' if t == 8 else ''}ターン目 {endturn[t] / total * 100:.0f}%" for t in sorted(endturn)))
    print(f"  盾からの受け（トリガー・G・ストライク）が効いた対戦 {trig / total * 100:.0f}%／手札からの受けが効いた対戦 {hand / total * 100:.0f}%")
    print(f"  3ターン目の終わりに場にある封殺 1人あたり{meta3 / total:.1f}枚／4ターン目までに勝者が封殺を完了 {lock4 / total * 100:.0f}%")
    engine2.TEMPO = 0


if __name__ == "__main__":
    main()
