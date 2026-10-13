#!/usr/bin/env python3
r"""勝利条件（ゴール）をデッキごと・使う人ごとに決める

  ■ なぜ必要か
  一人回し（solo.py）は既定で「相手の盾を5枚割り切ってダイレクトアタックするまでのターン数」を測る。
  これはビートダウンには正しい指標だが、**デッキの目的がそれではない**デッキでは意味を持たない。
    ・《究極銀河ユニバース》のデッキ → 目的はメテオバーンの特殊勝利。盾を割り切る必要はない。
    ・ループデッキ               → 目的は無限ループの成立。盤面の形が揃った瞬間に勝ちは決まっている。
    ・コントロール               → 目的は「相手の盤面を0にして、こちらが8マナ並べる」ような状態。
  実測で ユニバース退化 の「殴り切り平均」は 9.95ターンと出たが、これは**測る対象を間違えている**
  からそう見えるだけだった。

  ■ ゴールは「部品（parts）」に分けて書ける
  「届いたか／届かなかったか」だけでは、**何が足りなくて崩れたのか**が分からない。
  そこでゴールを順番のある部品に分けて書く。部品ごとに「何割の対戦で・何ターン目に」そろったかが出るので、
  どこが関門なのかが分かる。

    {
      "name":  "ユニバース特殊勝利",
      "decks": ["ユニバース"],
      "parts": [
        {"name": "フェニックスを出す",   "when": {"in_play_any": ["ボルシャック・栄光・ルピア"]}},
        {"name": "ユニバース着地",       "when": {"in_play": "究極銀河ユニバース"}},
        {"name": "メテオバーンで勝つ",   "when": {"special_win": "究極銀河ユニバース"}}
      ]
    }

  ■ ゴール地点は使う人が決める（--goal-at）
  上のゴールは3つの部品でできているが、**どこをゴール地点と呼ぶかは測る人が決めてよい**。
    ・「着地すれば勝ったも同然」と考えるなら、ゴール地点は2番目の部品。
    ・「本当に勝ち切るまで」を見たいなら、3番目。
  `--goal-at ユニバース着地` のように指定すると、その部品をゴールとして測る。
  **部品の条件はそれぞれ「その時点の盤面」を丸ごと書く**（前の部品を満たしている前提にしない）。
  そうしておくと、どの部品をゴール地点に選んでも、その条件だけで正しく判定できる。
  ゴール表に `"goal_at": "部品の名前"` と書いておけば、既定のゴール地点になる。
  部品に分けず `"when"` だけを書いてもよい（これまでどおり）。

  ■ 自分のゴール表（mygoals.json）
  goals.json は同梱の見本。**自分のゴールは mygoals.json に書く**（同じ場所に置くだけでよい。
  同じ名前のゴールは mygoals.json のほうが優先され、こちらに書いた新しいゴールが先に当たる）。
  デッキを組む画面（deckui.py）の「ゴール」欄で作って、そのまま貼り付けて保存できる。

  ■ 書ける条件
  python goals.py --conds で一覧が出る。まとめ役は {"all":[…]} {"any":[…]} {"not":…} {"ever":…}。

  盤面を見るだけでは**一瞬の出来事を取りこぼす**。たとえば踏み倒しで出したカードが、
  その瞬間に進化元として下に入ると、どの瞬間を見ても「場に立っている」ことが一度も無い。
  そのために次の3つがある。
    {"entered": "カード名"}          この試合で一度でも場のクリーチャーになった
                                   （出た直後に下に入っても、退化・侵略・革命チェンジで表に出た場合も数える）
    {"played":  "カード名"}          この試合で自分の手で使った（召喚した・唱えた）
    {"in_play_or_under": "カード名"} いま場にいる（進化元として下に入っているものも数える）
  また {"ever": 条件} は「一度でも満たしたら、その後ずっと満たしたことにする」まとめ役。
  「3体並んだ」のように次の瞬間に崩れる条件を拾うときに使う。

  ■ 部品は順番に通ったかも見る
  部品ごとに「そろった割合」と「順に通った割合」の両方を出す。
  前の部品を飛ばして成立しているなら、**部品の書き方が実際の道筋と合っていない**。
  順番を見ないでよいゴールは "ordered": false と書く。

  ■ いつ判定するか
  自分のターン中は**1手ごと**に見る。コンボは「ターンの途中で揃って、その場で使い切る」ことが
  多く、ターンの終わりだけを見ると見逃すため。決着した瞬間にも見る。
  記録するのは**最初に満たしたターン**（＝ゴール到達ターン）。これが殴り切りターンの一般化になる。

  ■ 使い方（PowerShell）
    python goals.py --list                                ゴールの一覧（mygoals.json を重ねたもの）
    python goals.py --conds                               書ける条件の一覧
    python goals.py --check ユニバース退化                  どのデッキにどのゴールが当たるか
    python goals.py --validate                            書いた条件が組み立てられるか確かめる
    python goals.py --init                                mygoals.json のひな形を作る
    python solo.py --deck ユニバース --games 2000           自動で当たったゴールも一緒に測る
    python solo.py --deck ユニバース --goal-at ユニバース着地  ゴール地点を部品で指定する
    python solo.py --deck 赤零 --goal ワンショット            ゴールを名前で指定する
    python solo.py --deck 赤零 --goal-file mygoals.json      ゴール表を指定する
    python solo.py --deck 赤零 --goal-stop                   ゴールに届いたらそこで打ち切る（速い）
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "goals.json")
MINE = os.path.join(HERE, "mygoals.json")          # 使う人が自分で書くゴール表（あれば重ねる）
NORMAL_WIN = ("ダイレクトアタック", "山札切れ", "時間切れ")
# special_win に名前で書ける「決まり方」（engine と envcards の s.win(...) に出てくるもの）
HOWS = ("ループ", "シャコガイル", "究極銀河ユニバース", "轟䡛合体 ゴルギーオージャー",
        "お目覚めメイ様", "サイバー・J・イレブン")


# ================================================================ 書ける条件の一覧
# arg＝値の種類：num 数／card カード名／cards カード名の並び／bool はい・いいえ／how 決まり方の名前
# cnt＝「count」で枚数・体数を足せる条件
COND = {
    "in_play":              ("場：自分の場にこのカードがいる", "card", True),
    "in_play_all":          ("場：自分の場にこれが全部そろっている", "cards", False),
    "in_play_any":          ("場：自分の場にこのどれかがいる", "cards", False),
    "opp_in_play":          ("場：相手の場にこのカードがいる", "card", True),
    "in_play_or_under":     ("場：自分の場にいる（進化元として下に入っているものも数える）", "card", True),
    "entered":              ("出来事：この試合でこのカードが場に出た（一瞬でも）", "card", True),
    "played":               ("出来事：この試合でこのカードを使った（召喚・唱えた）", "card", True),
    "in_grave":             ("墓地：自分の墓地にこのカードがある", "card", True),
    "creatures_at_least":   ("場：自分のクリーチャーがN体以上", "num", False),
    "opp_creatures_at_most": ("場：相手のクリーチャーがN体以下", "num", False),
    "total_power_at_least": ("場：自分のパワー合計がN以上", "num", False),
    "untapped_at_least":    ("場：すぐ殴れる自分のクリーチャーがN体以上", "num", False),
    "breaks_at_least":      ("打点：いま割れる盾の合計がN枚以上", "num", False),
    "opp_shields_at_most":  ("盾：相手の盾がN枚以下", "num", False),
    "opp_shields_at_least": ("盾：相手の盾がN枚以上", "num", False),
    "my_shields_at_least":  ("盾：自分の盾がN枚以上", "num", False),
    "my_shields_at_most":   ("盾：自分の盾がN枚以下", "num", False),
    "mana_at_least":        ("マナ：自分のマナがN枚以上", "num", False),
    "hand_at_least":        ("手札：自分の手札がN枚以上", "num", False),
    "opp_deck_at_most":     ("山札：相手の山札がN枚以下", "num", False),
    "my_deck_at_most":      ("山札：自分の山札がN枚以下", "num", False),
    "win":                  ("決着：どんな形でも勝った", "bool", False),
    "special_win":          ("決着：特殊勝利で勝った（名前を書けばその勝ち方だけ）", "how", False),
    "direct_attack":        ("決着：ダイレクトアタックで勝った", "bool", False),
    "turn_at_most":         ("ターン：自分のNターン目まで", "num", False),
}


# ------------------------------------------------------------------ カード名 → キー
_IDX = None
_KEYCACHE = {}


def _key(name):
    """カード名（日本語のまま）をカードのキーに直す。見つからなければ分かる形で止める"""
    global _IDX
    if name in _KEYCACHE:
        return _KEYCACHE[name]
    import decks8
    if _IDX is None:
        _IDX = decks8._index()
    k = decks8.find(name, _IDX)
    if k is None:
        raise SystemExit(f"ゴールの条件に書かれた『{name}』というカードが見つかりません。"
                         "\n  python cardfetch.py --missing で実装状況を確認してください")
    _KEYCACHE[name] = k
    return k


# ------------------------------------------------------------------ 条件を1つの関数にまとめる
def _one(spec):
    """条件1つを f(g, i) -> bool に直す。i は測る側のプレイヤー番号"""
    if not isinstance(spec, dict) or not spec:
        raise SystemExit(f"ゴールの条件の書き方が違います：{spec!r}")
    if "all" in spec:
        fs = [_one(x) for x in spec["all"]]
        return lambda g, i: all(f(g, i) for f in fs)
    if "any" in spec:
        fs = [_one(x) for x in spec["any"]]
        return lambda g, i: any(f(g, i) for f in fs)
    if "not" in spec:
        f = _one(spec["not"])
        return lambda g, i: not f(g, i)
    if "ever" in spec:
        # 一度でも満たしたら、その後ずっと満たしたことにする。
        # 盤面は動くので「3体並んだ」のような条件は次の瞬間に崩れる。それを拾うためのまとめ役。
        f = _one(spec["ever"])
        seen = [False]

        def f_ever(g, i):
            if seen[0]:
                return True
            seen[0] = bool(f(g, i))
            return seen[0]
        return f_ever

    kinds = set(spec) - {"count"}
    if len(kinds) != 1:
        raise SystemExit(f"ゴールの条件は1つの辞書に1つだけ書いてください：{spec!r}")
    t = kinds.pop()
    if t not in COND:
        raise SystemExit(f"『{t}』という条件は知りません（python goals.py --conds で一覧）")
    v = spec[t]
    n = int(spec.get("count", 1))

    if t == "in_play":
        k = _key(v)
        return lambda g, i: sum(1 for u in g.P[i].board if u.k == k) >= n
    if t == "in_play_all":
        ks = [_key(x) for x in v]
        return lambda g, i: all(any(u.k == k for u in g.P[i].board) for k in ks)
    if t == "in_play_any":
        ks = [_key(x) for x in v]
        return lambda g, i: any(any(u.k == k for u in g.P[i].board) for k in ks)
    if t == "opp_in_play":
        k = _key(v)
        return lambda g, i: sum(1 for u in g.P[1 - i].board if u.k == k) >= n
    if t == "in_play_or_under":
        k = _key(v)

        def f_pu(g, i):
            c = 0
            for u in g.P[i].board:
                if u.k == k:
                    c += 1
                c += sum(1 for x in u.under if x == k)
            return c >= n
        return f_pu
    if t == "entered":
        # enter＝ふつうに出た／surface＝退化・侵略・革命チェンジなどで下のカードが表に出た。
        # どちらも「このカードが場のクリーチャーになった」瞬間なので、まとめて数える。
        k = _key(v)
        return lambda g, i: (g.hist is not None
                             and sum(1 for w, pi, x in g.hist
                                     if w in ("enter", "surface") and pi == i and x == k) >= n)
    if t == "played":
        # 自分の手で使った（召喚した・唱えた）。退化や侵略で表に出ただけのものは数えない。
        k = _key(v)
        return lambda g, i: (g.hist is not None
                             and sum(1 for w, pi, x in g.hist
                                     if w in ("enter", "cast") and pi == i and x == k) >= n)
    if t == "in_grave":
        k = _key(v)
        return lambda g, i: sum(1 for x in g.P[i].grave if x == k) >= n
    if t == "creatures_at_least":
        return lambda g, i: g.ncre(i) >= v
    if t == "opp_creatures_at_most":
        return lambda g, i: g.ncre(1 - i) <= v
    if t == "total_power_at_least":
        return lambda g, i: sum(g.power(i, u) for u in g.P[i].board if u.c.kind == "C") >= v
    if t == "untapped_at_least":
        return lambda g, i: sum(1 for u in g.P[i].board
                                if u.c.kind == "C" and not u.tap and not u.sick) >= v
    if t == "breaks_at_least":
        def f_brk(g, i):
            tot = 0
            for u in g.P[i].board:
                if u.c.kind != "C" or u.tap:
                    continue
                if u.sick and not (u.c.sa or u.sa):
                    continue
                tot += g.brk(i, u)
            return tot >= v
        return f_brk
    if t == "opp_shields_at_most":
        return lambda g, i: len(g.P[1 - i].sh) <= v
    if t == "opp_shields_at_least":
        return lambda g, i: len(g.P[1 - i].sh) >= v
    if t == "my_shields_at_least":
        return lambda g, i: len(g.P[i].sh) >= v
    if t == "my_shields_at_most":
        return lambda g, i: len(g.P[i].sh) <= v
    if t == "mana_at_least":
        return lambda g, i: len(g.P[i].mana) >= v
    if t == "hand_at_least":
        return lambda g, i: len(g.P[i].hand) >= v
    if t == "opp_deck_at_most":
        return lambda g, i: len(g.P[1 - i].deck) <= v
    if t == "my_deck_at_most":
        return lambda g, i: len(g.P[i].deck) <= v
    if t == "win":
        return (lambda g, i: g.over and g.winner == i) if v else (lambda g, i: not (g.over and g.winner == i))
    if t == "direct_attack":
        return lambda g, i: g.over and g.winner == i and g.how == "ダイレクトアタック"
    if t == "special_win":
        if v is True:
            return lambda g, i: g.over and g.winner == i and g.how not in NORMAL_WIN
        return lambda g, i: g.over and g.winner == i and g.how == v
    if t == "turn_at_most":
        return lambda g, i: g.myturn(i) <= v
    raise SystemExit(f"『{t}』の組み立て方が書かれていません（goals.py の不具合）")


# ------------------------------------------------------------------ ゴールの形をそろえる
def parts_of(spec):
    """ゴールの部品の一覧 [(名前, 条件), …] を返す。部品に分けていないゴールは1つだけ返す"""
    if not spec:
        return []
    ps = spec.get("parts")
    if ps:
        return [(p.get("name", f"部品{n + 1}"), p["when"]) for n, p in enumerate(ps)]
    return [(spec.get("name", "ゴール"), spec["when"])]


def goal_when(spec, at=None):
    """ゴール地点の条件を返す。at に部品の名前を渡すと、そこをゴール地点にする。

    部品に分けたゴールで at を指定しないときは、
      ・"goal_at" が書いてあればそれ
      ・無ければ最後の部品
    をゴール地点にする。"""
    ps = parts_of(spec)
    if not ps:
        return None, ""
    want = at or spec.get("goal_at")
    if want:
        hit = [p for p in ps if want == p[0]] or [p for p in ps if want in p[0]]
        if not hit:
            raise SystemExit(f"『{want}』という部品がゴール「{spec.get('name', '')}」にありません"
                             f"（部品：{'、'.join(n for n, _w in ps)}）")
        return hit[0][1], hit[0][0]
    if spec.get("when") is not None and not spec.get("parts"):
        return spec["when"], spec.get("name", "")
    return ps[-1][1], ps[-1][0]


# ------------------------------------------------------------------ ゴール表
def load(path=None, mine=True):
    """ゴールの一覧を読む。

    path を省くと goals.json（同梱の見本）。そのうえで mygoals.json があれば重ねる
    （同じ名前のゴールは mygoals.json のほうが勝ち、新しいゴールは先頭に積まれて先に当たる）。"""
    def _read(p):
        if not p or not os.path.exists(p):
            return []
        d = json.load(open(p, encoding="utf-8"))
        gs = d.get("goals", d) if isinstance(d, dict) else d
        return [g for g in gs if isinstance(g, dict) and ("when" in g or "parts" in g)]

    base = _read(path or DEFAULT)
    if not mine or path:
        return base
    my = _read(MINE)
    if not my:
        return base
    names = {g.get("name") for g in my}
    return my + [g for g in base if g.get("name") not in names]


def pick(deck_name, name=None, path=None):
    """デッキ名（またはゴール名の指定）から、使うゴールを1つ選ぶ。無ければ None"""
    gs = load(path)
    if name:
        hit = [g for g in gs if name in g.get("name", "") or name in g.get("label", "")]
        if not hit:
            raise SystemExit(f"『{name}』というゴールがありません（python goals.py --list で一覧）")
        return hit[0]
    for g in gs:
        for d in g.get("decks", []):
            if d and d in deck_name:
                return g
    return None


class Tracker:
    """1戦のあいだ、ゴールと、その部品それぞれに届いたターンを見張る

    部品は2通りに数える。
      そろった（raw）     ：その部品の条件を満たした最初のターン。前の部品は関係ない。
      順に通った（ordered）：前の部品を**すでに全部通したうえで**満たした最初のターン。
    ゴールの道筋としては ordered のほうが正しいが、raw と見比べると
    「順番を飛ばして成立している＝部品の書き方が道筋と合っていない」ことに気づける。"""

    __slots__ = ("spec", "f", "turn", "label", "name", "at", "pf", "pnames", "pturn", "oturn", "ordered")

    def __init__(s, spec, at=None):
        s.spec = spec
        s.name = (spec or {}).get("name", "")
        s.label = (spec or {}).get("label", s.name)
        s.turn = None
        s.at = ""
        s.pnames, s.pf, s.pturn, s.oturn = [], [], [], []
        s.ordered = bool((spec or {}).get("ordered", True))
        if not spec:
            s.f = None
            return
        when, at_name = goal_when(spec, at)
        s.at = at_name
        s.f = _one(when)
        for nm, w in parts_of(spec):
            s.pnames.append(nm)
            s.pf.append(_one(w))
            s.pturn.append(None)
            s.oturn.append(None)

    def check(s, g, i):
        """ゴールに届いていれば True。最初に届いたターンだけを覚える"""
        if s.f is None:
            return False
        t = None
        prev_ok = True
        for n, f in enumerate(s.pf):
            hit = s.pturn[n] is not None
            if not hit:
                try:
                    hit = bool(f(g, i))
                except Exception:                    # noqa: BLE001
                    hit = False
                if hit:
                    if t is None:
                        t = max(1, g.myturn(i))
                    s.pturn[n] = t
            if s.oturn[n] is None and prev_ok and hit:
                if t is None:
                    t = max(1, g.myturn(i))
                s.oturn[n] = t
            prev_ok = prev_ok and s.oturn[n] is not None
        if s.turn is not None:
            return True
        try:
            ok = s.f(g, i)
        except Exception:                            # noqa: BLE001  条件が今の盤面で評価できない時は未達扱い
            return False
        if ok:
            s.turn = max(1, g.myturn(i))
        return ok

    def parts(s):
        """[(部品の名前, そろったターン or None, 順に通ったターン or None), …]"""
        return list(zip(s.pnames, s.pturn, s.oturn))


# ------------------------------------------------------------------ 入口
def _init_mine():
    if os.path.exists(MINE):
        print(f"すでにあります：{MINE}（上書きしません）")
        return
    sample = {
        "_doc": "自分のゴール表。goals.json より優先されます。python goals.py --validate で確かめられます。"
                "deckui.py が作る画面の「ゴール」欄で作って、ここに貼り付けるのが簡単です。",
        "goals": [{
            "name": "自分のゴール（例）",
            "label": "書き換えて使ってください",
            "decks": [],
            "goal_at": "殴れる形ができる",
            "parts": [
                {"name": "3ターン目までに動く", "when": {"all": [{"creatures_at_least": 1}, {"turn_at_most": 3}]}},
                {"name": "殴れる形ができる", "when": {"breaks_at_least": 6}},
                {"name": "勝つ", "when": {"win": True}},
            ],
        }],
    }
    json.dump(sample, open(MINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"作りました：{MINE}")
    print("  decks に自分のデッキ名の一部を書くと、自動で当たるようになります。")
    print("  python goals.py --validate で書き方を確かめられます。")


def _show(g):
    print(f"  {g['name']}" + (f"（自分のゴール表）" if g.get("_mine") else ""))
    if g.get("label"):
        print(f"    目指す状態 {g['label']}")
    if g.get("decks"):
        print("    当たるデッキ名 " + "、".join(g["decks"]))
    ps = parts_of(g)
    _w, at = goal_when(g)
    if len(ps) > 1:
        print(f"    部品（ゴール地点は「{at}」）")
        for n, (nm, w) in enumerate(ps, 1):
            mark = "←ゴール" if nm == at else ""
            print(f"      {n}. {nm}{mark}　{json.dumps(w, ensure_ascii=False)}")
    else:
        print("    条件 " + json.dumps(ps[0][1], ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="デッキごと・使う人ごとの勝利条件（ゴール）")
    ap.add_argument("--list", action="store_true", help="ゴールの一覧")
    ap.add_argument("--conds", action="store_true", help="書ける条件の一覧")
    ap.add_argument("--check", help="このデッキ名にどのゴールが当たるか")
    ap.add_argument("--at", help="--check と一緒に使う。ゴール地点にする部品の名前")
    ap.add_argument("--file", help="ゴール表のJSON（既定 goals.json ＋ mygoals.json）")
    ap.add_argument("--validate", action="store_true", help="全部のゴールの条件が組み立てられるか確かめる")
    ap.add_argument("--from-text", metavar="文章",
                    help="文章からゴールを作る（例： --from-text \"ユニバースが表に出る / 特殊勝利する\"）")
    ap.add_argument("--text-file", help="文章の書かれたファイルからゴールを作る")
    ap.add_argument("--to-text", metavar="ゴール名", help="あるゴールを文章にして見せる")
    ap.add_argument("--init", action="store_true", help="自分のゴール表 mygoals.json のひな形を作る")
    a = ap.parse_args()

    if a.init:
        _init_mine()
        return
    if a.from_text or a.text_file:
        import goaltext
        txt = open(a.text_file, encoding="utf-8").read() if a.text_file else a.from_text
        goal, notes = goaltext.parse(txt)
        print("【こう読みました】")
        print(goaltext.report(notes))
        bad = [n for n in notes if not n["ok"]]
        print()
        if not goal["parts"]:
            raise SystemExit("読める行がありませんでした。python goals.py --conds で書ける条件が見られます")
        for _nm, w in parts_of(goal):
            _one(w)                                   # 実際に組み立てられるか確かめる
        print("【mygoals.json に貼り付けるもの】")
        print(json.dumps({"goals": [goal]}, ensure_ascii=False, indent=1))
        if bad:
            print(f"\n（{len(bad)}行は読めませんでした。上の×の行を書き直してください）")
        return
    if a.to_text:
        import goaltext
        tab = load(a.file)
        g = next((x for x in tab if x.get("name") == a.to_text), None) or \
            next((x for x in tab if a.to_text in x.get("name", "")), None)
        if g is None:
            raise SystemExit(f"『{a.to_text}』というゴールがありません（python goals.py --list）")
        print(f"【{g['name']}】")
        print(goaltext.explain(g))
        return
    if a.conds:
        print(f"書ける条件 {len(COND)}種類（1つの辞書に1つ。まとめ役は all／any／not）\n")
        arg = {"num": "数", "card": "カード名", "cards": "カード名の並び", "bool": "はい／いいえ", "how": "はい／決まり方の名前"}
        for k, (ja, kind, cnt) in COND.items():
            print(f"  {k:24} {ja}")
            print(f"  {'':24}   値＝{arg[kind]}" + ("　count で枚数・体数を足せる" if cnt else ""))
        print("\n  例 {\"all\": [{\"opp_creatures_at_most\": 0}, {\"mana_at_least\": 8}]}")
        return
    gs = load(a.file)
    if a.check:
        g = pick(a.check, None, a.file)
        if g:
            print(f"『{a.check}』→")
            _show(g)
            if a.at:
                _w, at = goal_when(g, a.at)
                print(f"    （--goal-at で「{at}」をゴール地点にします）")
        else:
            print(f"『{a.check}』に当たるゴールはありません（殴り切りターンだけを測ります）")
        return
    if a.validate:
        bad = 0
        for g in gs:
            try:
                for _nm, w in parts_of(g):
                    _one(w)
                goal_when(g)
                print(f"  OK   {g['name']}")
            except SystemExit as e:
                bad += 1
                print(f"  NG   {g['name']}：{e}")
        print(f"\n{len(gs)}件中 {len(gs) - bad}件が組み立てられました")
        if os.path.exists(MINE):
            print(f"（{MINE} を重ねて読んでいます）")
        return
    src = a.file or (DEFAULT + ("　＋　" + MINE if os.path.exists(MINE) else ""))
    print(f"{len(gs)}件のゴール（{src}）\n")
    for g in gs:
        _show(g)
        print()
    if not a.list:
        print("（--list で一覧、--conds で書ける条件、--check デッキ名 でどれが当たるか、"
              "--init で自分のゴール表を作る）")


if __name__ == "__main__":
    main()
