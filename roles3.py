#!/usr/bin/env python3
"""カードの「役割」を数える（第3版・創作者用）

  役割（8種）：acc 加速／draw 手札を増やす／rem 除去・バウンス・マナ送り／blk ブロッカー／
              trg S・トリガーの防御／atk 攻め（速攻・マッハ・W以上で軽い）／dis 妨害（手札破壊・タップ・墓地戻し）／
              fin 決め札（コスト8以上かT・ブレイカー）／shd シールドを増やす
  ・envcards/*.py で実装したカードは、登録の時に書いた roles の文字をそのまま使う。
  ・部品の並びで近似登録したカードは、効果の部品（netcards.FX）とキーワードから自動で数える。
  ・cards3.py の実在カードは、キーワードから自動で数えた上に、効果をもつカードだけ下の表で手で足している
    （手作業の近似。ここが違えば役割の数え方が変わる）。
  ・役割が0のカードは「どの役割も担わない札」。薄い札から先にデッキから外す。
"""
import envreg
import netcards
from cards3 import BY_KEY

ROLES = ("acc", "draw", "rem", "blk", "trg", "atk", "dis", "fin", "shd")
TARGET = {"acc": 6, "draw": 6, "rem": 6, "blk": 6, "trg": 6, "atk": 8, "dis": 3, "fin": 3, "shd": 2}

MANUAL = {
    "kohaku": "acc draw", "chakra": "shd", "vt": "rem fin", "clock": "dis", "eringi": "draw acc dis",
    "anti": "draw atk", "dagra": "acc", "katsuemon": "rem draw", "everlast": "fin", "dogigyaku": "fin",
    "leviya": "acc", "trap": "rem", "parli": "dis", "jasmine": "acc", "manhattan": "rem dis",
    "wokanna": "rem", "esmel": "acc", "princess": "rem", "leaf": "draw", "hangyaku": "rem",
    "robin": "dis", "ops": "rem fin", "vamilia": "rem dis", "artel": "rem fin", "jaouga": "fin rem",
    "scarlet": "fin", "gigan": "fin", "dangerdeon": "fin", "obza": "fin rem", "shako": "fin",
    "doom": "fin", "shuto": "atk", "crossfire": "atk fin", "kuzen": "atk acc", "mirai": "acc draw",
    "saitan": "draw", "tenbin": "dis", "shinten": "acc draw", "efc": "fin", "majin": "rem",
    "strato": "draw", "kerola": "dis", "keikan": "dis", "fujin": "atk", "testa": "atk",
    "tensai": "atk dis", "klin": "rem dis", "zen": "acc", "derbande": "dis", "viride": "dis",
    "zaze": "dis", "lelady": "trg rem", "apul": "trg draw", "gio": "draw", "takkyu": "atk",
}


def roles(k):
    c = BY_KEY[k]
    r = set(MANUAL.get(k, "").split()) | set(envreg.ROLES.get(k, "").split())
    if c.blocker:
        r.add("blk")
    if c.trig:
        r.add("trg")
    if c.mach or c.sa:
        r.add("atk")
    if c.kind == "C" and c.cost >= 8:
        r.add("fin")
    if c.kind == "C" and c.brk >= 3:
        r.add("fin")
    if c.kind == "C" and c.brk >= 2 and c.cost <= 6 and not c.noatkp:
        r.add("atk")
    for x in netcards.FX.get(k, []):
        t = x[0]
        if t in ("draw", "look"):
            r.add("draw")
        elif t == "ramp":
            r.add("acc")
        elif t in ("destroy", "destroy_all", "bounce", "to_mana", "mass_bounce_hand"):
            r.add("rem")
        elif t in ("tap", "discard"):
            r.add("dis")
        elif t == "shield_add":
            r.add("shd")
    return r & set(ROLES)


def coverage(deck, skip=None):
    cov = dict.fromkeys(ROLES, 0)
    for k, n in deck.items():
        if k == skip:
            n -= 1
        for r in roles(k):
            cov[r] += n
    return cov


def need(r, cov):
    """役割 r がまだ足りない度合い（0.15〜1）"""
    return max(0.15, 1 - cov[r] / TARGET[r])


def value(k, cov):
    """k を（いまの役割の数 cov のデッキに）入れる価値。複数の役割を担うほど大きい"""
    rs = roles(k)
    if not rs:
        return 0.1
    return sum(need(r, cov) for r in rs)


def thinness(deck):
    """デッキの各札について、その1枚を抜いた場合のデッキでの価値（低いほど薄い）"""
    return {k: value(k, coverage(deck, skip=k)) for k in deck}


def stats(deck):
    cov = coverage(deck)
    multi = sum(n for k, n in deck.items() if len(roles(k)) >= 2)
    zero = sum(n for k, n in deck.items() if not roles(k))
    return cov, multi, zero
