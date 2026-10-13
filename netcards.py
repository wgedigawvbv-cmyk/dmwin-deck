#!/usr/bin/env python3
"""ネットから持ってきた実在カードを「部品の並び」で近似登録する（間に合わせの道具）

  ※ このしくみは効果を近似する。ちゃんと実装したカードは envcards/*.py にあり、そちらは
     カードに書かれている効果をそのまま書いている（status="full"）。
     ここで登録したカードは status="approx" になり、あとで envcards に書き直すためのもの。

  ・カードは JSON（cards_net.json）で渡す。1枚の形：
      {"key": "n_xxx", "name": "...", "cost": 4, "civ": "F", "kind": "C",
       "power": 5000, "brk": 1, "races": ["dragon"], "blocker": false, "sa": false, "mach": false, "gs": false, "trig": false,
       "noatkp": false,
       "fx": [["draw", 1], ["destroy", {"max_power": 3000}]],
       "source": "https://…（カードの載っているページ）", "text": "効果を自分の言葉で要約したもの", "omitted": "再現しなかった部分"}
  ・出た時（クリーチャー）／唱えた時（呪文）の効果は、下の決まった部品の並びで表す。
    部品で表せない効果は「省いた」と omitted に書く（なかったことにはしない）。
  ・進化・革命チェンジ・ツインパクト・場に残るメタ効果は、この形式では持ち込めない。
  ・noatkp＝相手プレイヤーを攻撃できない（ブロッカー専用のカードなど）。

  部品（fx）：limit は {"max_power": N} か {"max_cost": N} に、必要なら "untapped": true を足したもの
    ["draw", n]                        自分がn枚引く
    ["ramp", n]                        山札の上からn枚をマナへ
    ["look", n, "creature"|"any"]      山札の上n枚から1枚を手札へ（残りは下）
    ["destroy", limit]                 相手のクリーチャー1体を破壊
    ["destroy_all", limit]             相手のクリーチャーのうち limit に合うものをすべて破壊
    ["bounce", n, limit?]              相手のクリーチャーをn体手札へ
    ["mass_bounce_hand"]               自分の手札の枚数以下のコストの相手のクリーチャーをすべて手札へ
    ["to_mana", n, limit?]             相手のクリーチャーをn体マナへ
    ["tap", n]                         相手のクリーチャーをn体タップ
    ["discard", n]                     相手の手札をランダムにn枚捨てさせる
    ["shield_add", n]                  山札の上からシールドをn枚足す
    ["lose_shield", n]                 自分のシールドをn枚墓地へ（デメリット）
    ["mill_self", n]                   自分の山札の上n枚を墓地へ（デメリット）
    ["self_destroy"]                   このクリーチャー自身を破壊（出た時に自壊する札）

  python netcards.py cards_net.json        読み込めるかの検査
"""
import json
import re

from cards3 import BY_KEY, POOL, Card

CIVS = set("LWDFN")
FX_NAMES = {"lose_shield", "draw", "ramp", "look", "destroy", "destroy_all", "bounce", "mass_bounce_hand", "to_mana", "tap",
            "discard", "shield_add", "mill_self", "self_destroy"}
KEY_RE = re.compile(r"^n_[a-z0-9_]{1,30}$")
FX = {}          # key → 部品の並び（役割の数え上げに使う）


def validate(d):
    """カード1枚の記述を検査する。問題があれば文字列を返し、なければ None"""
    for f in ("key", "name", "cost", "civ", "kind", "source", "text"):
        if f not in d:
            return f"{f} がない"
    if not KEY_RE.match(str(d["key"])):
        return "key は n_ で始まる英小文字・数字・_ にしてください"
    if d["key"] in BY_KEY:
        return "key が重複している"
    if not isinstance(d["cost"], int) or not 0 <= d["cost"] <= 12:
        return "cost は0〜12の整数"
    if d["kind"] not in ("C", "S"):
        return "kind は C か S（このしくみで持ち込めるのはクリーチャーと呪文だけ）"
    civ = d["civ"]
    if not civ or not set(civ) <= CIVS:
        return "civ は L W D F N の組み合わせ"
    if not str(d["source"]).startswith("https://"):
        return "source は https:// で始まる出典が必要"
    if d["kind"] == "C" and not isinstance(d.get("power"), int):
        return "クリーチャーには power が必要"
    brk = d.get("brk", 1)
    if not isinstance(brk, int) or not 1 <= brk <= 5:
        return "brk は1〜5"
    for x in d.get("fx", []):
        if not isinstance(x, list) or not x or x[0] not in FX_NAMES:
            return f"知らない部品：{x}"
        if x[0] == "self_destroy" and d["kind"] != "C":
            return "self_destroy はクリーチャーだけ"
    return None


def make_card(d):
    return Card(d["key"], d["name"], d["cost"], d["civ"], kind=d["kind"], power=d.get("power", 0), brk=d.get("brk", 1),
                races=tuple(d.get("races", ())), sa=bool(d.get("sa")), blocker=bool(d.get("blocker")),
                mach=bool(d.get("mach")), trig=bool(d.get("trig")), gs=bool(d.get("gs")), noatkp=bool(d.get("noatkp")),
                note=(d["text"] + (f"／省いた：{d['omitted']}" if d.get("omitted") else "")))


def _limit_pred(s, i, lim):
    """相手の場の1体が limit に合うかを返す関数"""
    lim = lim or {}
    up = lim.get("untapped", False)
    mp = lim.get("max_power")
    mc = lim.get("max_cost")

    def pred(z):
        if up and z.tap:
            return False
        if mp is not None and s.power(1 - i, z) > mp:
            return False
        if mc is not None and z.c.cost > mc:
            return False
        return True
    return pred


def _run_fx(fx):
    def run(s, i, u=None):
        o = s.P[1 - i]
        p = s.P[i]
        for x in fx:
            t = x[0]
            if t == "draw":
                s.draw(i, x[1])
            elif t == "ramp":
                s.ramp(i, x[1])
            elif t == "look":
                want = x[2] if len(x) > 2 else "any"
                s.dig(i, x[1], (lambda k: BY_KEY[k].kind == "C") if want == "creature" else (lambda k: True), "bottom")
            elif t in ("destroy", "bounce", "to_mana"):
                if o.protect:
                    continue
                n = 1 if t == "destroy" else x[1]
                lim = x[1] if t == "destroy" else (x[2] if len(x) > 2 else None)
                for _ in range(n):
                    z = s.target(i, _limit_pred(s, i, lim))
                    if z is None:
                        break
                    s.leave(1 - i, z, {"destroy": "grave", "bounce": "hand", "to_mana": "mana"}[t], by_opp=True,
                            destroy=(t == "destroy"))
            elif t == "destroy_all":
                if o.protect:
                    continue
                pred = _limit_pred(s, i, x[1])
                for z in o.board[:]:
                    if z in o.board and z.c.kind == "C" and not z.jd and pred(z):
                        s.leave(1 - i, z, "grave", by_opp=True, destroy=True)
            elif t == "mass_bounce_hand":
                if o.protect:
                    continue
                n = len(p.hand)
                for z in o.board[:]:
                    if z in o.board and z.c.kind == "C" and not z.jd and z.c.cost <= n:
                        s.leave(1 - i, z, "hand", by_opp=True)
            elif t == "tap":
                for _ in range(x[1]):
                    z = s.target(i, lambda z: not z.tap)
                    if z is not None:
                        z.tap = True
            elif t == "discard":
                for _ in range(x[1]):
                    s.discard_random(1 - i)
            elif t == "lose_shield":
                for _ in range(x[1]):
                    if p.sh:
                        k, _up = p.sh.pop()
                        p.grave.append(k)
                        s.shield_left()
            elif t == "mill_self":
                s.mill(i, x[1])
            elif t == "shield_add":
                for _ in range(x[1]):
                    s.add_shield(i)
            elif t == "self_destroy":
                if u is not None and u in p.board:
                    s.leave(i, u, "grave", destroy=True)
    return run


def register(cards):
    """検査を通ったカードを登録して、登録したキーを返す。通らなかったものは (key, 理由) の一覧で返す"""
    import engine3
    ok, bad = [], []
    for d in cards:
        why = validate(d)
        if why:
            bad.append((d.get("key"), why))
            continue
        c = make_card(d)
        POOL.append(c)
        BY_KEY[c.key] = c
        FX[c.key] = [list(x) for x in d.get("fx", [])]
        civ = set(c.civ)
        engine3.MCIV[c.key] = "".join(sorted(civ))
        engine3.MULTI[c.key] = len(civ) >= 2
        engine3.PRI[c.key] = c.cost + (2 if d.get("fx") else 0) + (1 if c.blocker else 0)
        if d.get("fx"):
            fn = _run_fx(d["fx"])
            if c.kind == "C":
                engine3.ENTER[c.key] = fn
            else:
                engine3.SPELL[c.key] = fn
        if c.kind == "S" and c.key not in engine3.SPELL:
            engine3.SPELL[c.key] = lambda s, i: None
        import envreg
        envreg.STATUS[c.key] = ("approx", "部品の並びでの近似登録（envcards に書き直すまでの間に合わせ）",
                                d.get("source", ""), d.get("text", ""), c.name)
        envreg.ROLES.setdefault(c.key, "")
        ok.append(c.key)
    return ok, bad


def load(path="cards_net.json"):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return [], []
    return register(data["cards"] if isinstance(data, dict) else data)


if __name__ == "__main__":
    import sys
    ok, bad = load(sys.argv[1] if len(sys.argv) > 1 else "cards_net.json")
    print("登録できた：", len(ok), "枚", [BY_KEY[k].name for k in ok])
    for k, w in bad:
        print("×", k, w)
