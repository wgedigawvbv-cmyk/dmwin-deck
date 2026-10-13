#!/usr/bin/env python3
"""現環境の新カードを、カードプールとエンジンに登録する道具（envcards/*.py が使う）

  add(key, name, cost, civ, kind="C", power=0, brk=1, races=(), twin=None, evo=None, neo=False, …,
      enter=fn, spell=fn, attack=fn, destroyed=fn, left=fn, tstart=fn, tend=fn,
      powerx=fn, brkx=fn, costx=fn, cantatk=fn, evox=fn, changex=fn, react=fn, fatex=fn,
      invade=fn, gamestart=fn, payx=fn, spcost=fn, discardx=fn,                 ← キーごとの差し込み口
      aurap=fn, costaura=fn, atklock=fn, blocklock=fn, atktargetlock=fn, atkwatch=fn, leavewatch=fn,
      enterwatch=fn, breakwatch=fn, battlefx=fn, leaverep=fn, breakrep=fn, brkplus=fn, blockok=fn,
      saok=fn, unbok=fn, spelllock=fn, tgtlock=fn, freeacts=fn,                             ← 全体にかかる差し込み口
      actapply={"x:名前": fn}, nograve=True,
      pri=数, roles="draw rem", playrule=fn, status="full", text="カードの効果を自分の言葉で", note="省いた点", source="URL")

  ・関数の形は engine3.py の先頭にある差し込み口の説明のとおり。
  ・kind："C" クリーチャー／"S" 呪文／"T" タマシード／"G" G城／"X" クロスギア／"K" 禁断の鼓動
  ・status＝実装の正確さ：full＝カードに書かれている効果を全部／partial＝省いた部分がある（note に書く）。
    「どれを選ぶか」「任意効果を使うか」は、このシミュレーター全体の決まりどおり機械的に決める（省略ではない）。
  ・すでに同じキーがあれば何もしない（子プロセスで読み込み直しても安全）。
"""
import engine3
from cards3 import BY_KEY, POOL, Card

STATUS = {}      # key -> (status, note, source)
ROLES = {}       # key -> 役割の文字（roles3.py が読む）
DICT_HOOKS = {"attack": "ATTACK", "destroyed": "DESTROYED", "left": "LEFT", "tstart": "TSTART", "tend": "TEND",
              "powerx": "POWERX", "brkx": "BRKX", "costx": "COSTX", "cantatk": "CANTATK", "evox": "EVOX",
              "changex": "CHANGEX", "react": "REACT", "fatex": "FATEX", "invade": "INVADEX", "gamestart": "GAMESTART",
              "payx": "PAYX", "spcost": "SPCOST", "discardx": "DISCARDX", "atkswap": "ATKSWAP", "chargex": "CHARGEX",
              "castle": "CASTLEX", "blockreact": "BLOCKREACT",
              "shielddest": "SHIELDDEST", "shieldcast": "SHIELDCAST", "evosrc": "EVOSRC",
              "blockdone": "BLOCKDONE"}
LIST_HOOKS = {"tgtlock": "TGTLOCK", "aurap": "AURAP", "costaura": "COSTAURA", "atklock": "ATKLOCK", "blocklock": "BLOCKLOCK",
              "atktargetlock": "ATKTARGETLOCK", "atkwatch": "ATKWATCH", "leavewatch": "LEAVEWATCH",
              "enterwatch": "ENTERWATCH", "breakwatch": "BREAKWATCH", "battlefx": "BATTLEFX", "leaverep": "LEAVEREP",
              "breakrep": "BREAKREP", "brkplus": "BRKPLUS", "blockok": "BLOCKOK", "saok": "SAOK", "unbok": "UNBOK",
              "spelllock": "SPELLLOCK", "freeacts": "FREE_ACTS", "atkend": "ATKEND", "manarep": "MANAREP",
              "spellwatch": "SPELLWATCH", "tstartall": "TSTARTALL", "manaleave": "MANALEAVE",
              "leavedest": "LEAVEDEST", "guard": "GUARD", "discardwatch": "DISCARDWATCH", "tendall": "TENDALL",
              "noatkplock": "NOATKPX", "noatkign": "NOATKIGN", "trigok": "TRIGOK", "machok": "MACHOK",
              "loserep": "LOSEREP", "manaexec": "MANAEXEC", "gsok": "GSOK",
              "shieldin": "SHIELDIN", "shieldout": "SHIELDOUT", "breakpre": "BREAKPRE",
              "tapwatch": "TAPWATCH", "drawwatch": "DRAWWATCH", "manain": "MANAIN",
              "blockwatch": "BLOCKWATCH", "chosenwatch": "CHOSENWATCH", "mustatk": "MUSTATK",
              "battleswap": "BATTLESWAP", "turnstart": "TURNSTART", "tendp": "TENDP",
              "mustpick": "MUSTPICK",
              "abilock": "ABILOCK", "spcostaura": "SPCOSTAURA", "mustatktgt": "MUSTATKTGT", "shieldrep": "SHIELDREP", "gswatch": "GSWATCH",
              "entertriglock": "ENTERTRIGLOCK", "tamain": "TAMAIN", "nogsx": "NOGSX"}


def add(key, name, cost, civ, kind="C", power=0, brk=1, races=(), twin=None, evo=None, neo=False,
        enter=None, spell=None, pri=None, roles="", playrule=None, status="full", note="", source="", text="",
        actapply=None, nograve=False, **kw):
    hooks = {h: kw.pop(h) for h in list(kw) if h in DICT_HOOKS or h in LIST_HOOKS}
    godlink = kw.pop("godlink", None)        # G・リンク：("L"|"R"|"C", (つなげる相手のキー, …))
    changezone = kw.pop("changezone", None)  # 革命チェンジで探すゾーン：("hand", "shield") など
    if key in BY_KEY:
        return BY_KEY[key]
    c = Card(key, name, cost, civ, kind=kind, power=power, brk=brk, races=tuple(races), twin=twin, evo=evo, neo=neo,
             note=(text + (f"／省いた：{note}" if note else "")), **kw)
    POOL.append(c)
    BY_KEY[key] = c
    civset = set(civ) | (set(twin[1]) if twin else set())
    engine3.MCIV[key] = "".join(sorted(civset))
    engine3.MULTI[key] = len(civset) >= 2
    engine3.PRI[key] = pri if pri is not None else cost
    if enter is not None:
        engine3.ENTER[key] = enter
    if spell is not None:
        engine3.SPELL[key] = spell
    elif kind == "S" or twin:
        engine3.SPELL.setdefault(key, lambda s, i: None)
    for h, fn in hooks.items():
        if h in DICT_HOOKS:
            getattr(engine3, DICT_HOOKS[h])[key] = fn
        else:
            # 全体に効く差し込み口は、同じ関数を2回登録すると効果が2回かかる。
            # サイクルの何枚かに同じ関数を渡してしまう事故が実際に起きた
            # （ササゲールの costaura を4枚に渡して軽減が4回かかり、コスト5が0になった）ので、
            # 同じ関数オブジェクトの重ね登録は黙って1回にまとめる。
            lst = getattr(engine3, LIST_HOOKS[h])
            if not any(x is fn for x in lst):
                lst.append(fn)
    for nm, fn in (actapply or {}).items():
        engine3.ACTAPPLY[nm] = fn
    if nograve:
        engine3.NOGRAVE.add(key)
    if playrule is not None:
        import playable3
        playable3.PLAYRULE[key] = playrule
    STATUS[key] = (status, note, source, text, name)
    ROLES[key] = roles
    if godlink is not None:
        pos, mates = godlink if isinstance(godlink, (tuple, list)) and len(godlink) == 2 else (godlink, ())
        engine3.GODLINK[key] = (pos, tuple(mates))
    if changezone is not None:
        engine3.CHANGEZONE[key] = tuple(changezone)

    return c


# ---------------------------------------------------------------- よく使う道具
def destroy(s, i, t):
    """i から見た相手の t を破壊する"""
    return s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def move(s, i, t, dest):
    return s.leave(1 - i, t, dest, by_opp=True)


def opp_all(s, i, pred=None, kinds="C"):
    """i から見た相手の場のカード（選べないものは除く）"""
    return [u for u in s.P[1 - i].board if u.c.kind in kinds and not u.jd and (pred is None or pred(u))]


def has_race(c, r):
    return r in c.races


def is_cmd(c):
    """コマンドかどうか（侵略元・封印外しの条件）"""
    return "command" in c.races


def my_cre(s, i, pred=None):
    return [u for u in s.P[i].board if u.c.kind == "C" and (pred is None or pred(u))]


def dig2(s, i, n, picks):
    """山札の上n枚を見て、picks（条件の並び）ごとに1枚ずつ手札へ。残りは山札の下へ"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return []
    top = [p.deck.pop() for _ in range(n)]
    got = []
    for pred in picks:
        best, bv = None, -99
        for k in top:
            if pred(k):
                v = engine3.PRI[k] - 3 * p.hand.count(k)
                if v > bv:
                    best, bv = k, v
        if best is not None:
            top.remove(best)
            p.hand.append(best)
            got.append(best)
    for k in top:
        p.deck.insert(0, k)
    return got


def worst_hand(s, i, skip=()):
    p = s.P[i]
    cs = [k for k in p.hand if k not in skip]
    return min(cs, key=engine3.PRI.get) if cs else None


def best_hand(s, i, pred=None):
    p = s.P[i]
    cs = [k for k in p.hand if pred is None or pred(k)]
    return max(cs, key=engine3.PRI.get) if cs else None


def free_play(s, i, k, src="hand"):
    """手札などからコストを支払わずに1枚使う（クリーチャー・呪文・タマシード・G城・クロスギア）"""
    p = s.P[i]
    zone = {"hand": p.hand, "mana": p.mana, "grave": p.grave}[src]
    if k not in zone:
        return False
    c = BY_KEY[k]
    if c.kind == "C":
        if s.fate(i, k, src, False) != "ok":
            return False
        zone.remove(k)
        s.enter(i, k, src, False)
    elif c.kind == "S":
        if not s.spell_ok(i, c.cost):
            return False
        zone.remove(k)
        s.cast(i, k)
    elif c.kind == "T":
        zone.remove(k)
        s.place_tama(i, k)
    elif c.kind == "X":
        zone.remove(k)
        gu = engine3.U(k)
        gu.sick = False
        p.board.append(gu)
        fn = engine3.ENTER.get(k)
        if fn is not None:
            fn(s, i, gu)
    else:
        zone.remove(k)
        s.place_castle(i, k)
    return True
