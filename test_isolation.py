#!/usr/bin/env python3
"""カードが「自分が入っていない対戦」に影響していないかを調べる

  envcards/*.py のカードは、全体に効く差し込み口（ATKEND・ATKWATCH・BREAKREP など）に
  関数を登録する。この種の関数は**どの対戦でも呼ばれる**ので、
  「自分のカードがバトルゾーンにいるか／自分のカードの攻撃か」を必ず確かめないといけない。
  確かめ忘れると、そのカードが1枚も入っていないデッキの対戦まで動きが変わる。

  実際にこれが起きた：《百族の団長 プチョヘンザ斧》と《勝利宣言 鬼丸「V」》が ATKEND で
  自分のカードかを確かめておらず、**あらゆるクリーチャーの攻撃の終わりに**能力が働いていた
  （test3 が5件失敗して気づいた）。

  この試験は、モジュールごとに全体フックを外して、
  もとからある7デッキ（新カードを1枚も含まない）の対戦の手数が変わらないことを確かめる。
  変わったら、そのモジュールのどれかが「自分がいなくても働く」フックを持っている。

  python test_isolation.py            全モジュールを調べる
  python test_isolation.py env25      1つだけ調べる
"""
import random
import sys

import engine3 as E
from cards3 import DECKS

LISTS = [n for n in dir(E) if n.isupper() and isinstance(getattr(E, n), list)]
GAMES = 120
SEED = 5
# env0 は全モジュールが使う共通の仕組み（封印・スレイヤー・EXライフ・スター進化）で、
# もとからあるカードにも効くので、外して比べる対象にしない
# env1・env6 は「もとからある7デッキのカードの抜けを直す」モジュールなので、
# もとからある対戦の動きが変わるのが正しい（env1＝7デッキの1枚差しと公式リストの復元、
# env6＝cards3 の実装漏れの直し）。だから比べる対象から外す。
SHARED = {"envcards.env0", "envcards.env1", "envcards.env6"}


def run(games=GAMES, seed=SEED):
    """もとからある7デッキだけで対戦し、総手数を返す（新カードは1枚も入らない）"""
    rng = random.Random(seed)
    names = list(DECKS)
    n = 0
    for t in range(games):
        a, b = rng.choice(names), rng.choice(names)
        g = E.Game(DECKS[a], DECKS[b], rng, first=t % 2)
        while not g.over:
            g.apply(rng.choice(g.legal()))
            n += 1
    return n


def modules():
    out = set()
    for ln in LISTS:
        for f in getattr(E, ln):
            m = getattr(f, "__module__", "") or ""
            if m.startswith("envcards.") and m not in SHARED:
                out.add(m)
    return sorted(out)


def pull(mod):
    """mod が登録した全体フックを外す。返り値：元に戻すための情報"""
    saved = []
    for ln in LISTS:
        lst = getattr(E, ln)
        keep = [f for f in lst if (getattr(f, "__module__", "") or "") != mod]
        if len(keep) != len(lst):
            saved.append((ln, list(lst)))
            lst[:] = keep
    return saved


def restore(saved):
    for ln, old in saved:
        getattr(E, ln)[:] = old


def determinism():
    """同じ種なら、プロセスをまたいでも同じ結果になるか（文字列の集合を回すと順序が変わる）"""
    import subprocess
    outs = []
    for h in ("0", "1", "2"):
        r = subprocess.run([sys.executable, "-c", "import engine3; print(engine3.selftest(120, 7))"],
                           cwd=__import__("os").path.dirname(__import__("os").path.abspath(__file__)),
                           env={**__import__("os").environ, "PYTHONHASHSEED": h},
                           capture_output=True, text=True)
        outs.append(r.stdout.strip())
    ok = len(set(outs)) == 1
    print(("○ " if ok else "× ") + f"再現性：PYTHONHASHSEED を変えても同じ結果 {outs}")
    if not ok:
        print("  直し方：`for x in set(...)` を `for x in sorted(set(...))` にする"
              "（文字列の集合はプロセスごとに順序が変わる）")
    return ok


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    base = run()
    mods = [m for m in modules() if only is None or m.endswith("." + only)]
    if not mods:
        print(f"全体フックを登録しているモジュールが見つかりません（{only}）")
        return 0
    print(f"もとからある7デッキで {GAMES}戦：{base}手（この数が変わらないことを確かめる）\n")
    bad = []
    for m in mods:
        saved = pull(m)
        try:
            n = run()
        finally:
            restore(saved)
        ok = (n == base)
        print(("○ " if ok else "× ") + f"{m.split('.')[-1]:8s} 外すと {n}手"
              + ("" if ok else f"　← {n - base:+d}手ずれる。自分のカードがいない対戦に影響している"))
        if not ok:
            bad.append(m)
    total = len(mods)
    if only is None:
        print()
        total += 1
        if not determinism():
            bad.append("（再現性）")
    print(f"\n{total - len(bad)}/{total} 通過"
          + ("" if not bad else "　影響しているモジュール：" + "、".join(x.split('.')[-1] for x in bad)))
    if bad:
        print("  直し方：そのモジュールの全体フックの先頭で、"
              "`if u.k != \"自分のキー\": return` か `if not s.has(i, \"自分のキー\"): return` を書く")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
