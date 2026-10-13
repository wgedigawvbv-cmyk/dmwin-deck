"""そのデッキで「そもそも出せるか」の判定（第3版）

デッキを組み替えたときに、色が足りない、革命チェンジの元がいない、進化元がいない、といった
「引いても出せないカード」が混ざらないようにするための判定。進化（evolve7.py）が、
出せないカードを入れて遊ばせてしまう試行を減らすために使う。

判定の考え方（実在の7リストがすべて通るように、いちばん厳しい値から決めた）
  トリガー：S・トリガー／G・ストライクを持つカードは、シールドゾーンから色を問わず使えるので「出せる」とみなす
            （公式の入賞リストには、色が合わないS・トリガーの1枚差しが実在する）。
  侵略　　：コストを払わずコマンドの上に重ねるので色は問わない。かわりに、侵略元になるコマンドの数で判定する（PLAYRULE）。
  ツインパクト：どちらかの面が使えれば「出せる」とみなす（呪文側だけ使うための1枚差しがあるため）。
  色　　　：単色のカードは、そのカード以外でその文明を持つカードが COLOR_MIN 枚以上ある（マナに置いて色を出す）。
            多色のカードは MULTI_MIN 枚でよい（多色カード自身がマナで色を出すため。水単チェンジサイバーの公式リストは
            光を出すカードがミケランジェロとミラダンテ槍の2枚だけで、互いに色を供給して成立している）。
            ただし墓地などからただで出せるカード（FREE）は色を問わない。
  チェンジ：革命チェンジするカードは、元になれるクリーチャー（文明が合い、パワーが足りる）が CHANGE_MIN 枚以上ある。
  相棒　　：創世竜ループの部品（レヴィヤ・トラップ・パーリ・ヴァルハラ）は、創世竜が PARTNER の枚数ないと働かない。
  進化　　：進化クリーチャーは、進化元になれるクリーチャーが EVO_MIN 枚以上ある（NEO進化は不要）。
"""
from cards3 import BY_KEY, CHANGE

COLOR_MIN = 4
MULTI_MIN = 1
CHANGE_MIN = 3
EVO_MIN = 4
NOCOLOR = set()                           # コストを支払わずに出すので色がいらないカード（侵略・S級侵略など）
FREE = {"crossfire"}                      # 墓地にクリーチャーが6体以上あればただで出せる（色は問わない）
GRAVE_MAKERS = {"kuzen", "obza", "margani", "doom", "artel", "jaouga", "scarlet", "venom"}   # 墓地を肥やす・墓地を使うカード
GRAVE_MIN = 8                             # FREE のカードは、墓地を肥やすカードがこれだけないと「出せる」とは言えない
PARTNER = {"leviya": ("zen", 3), "trap": ("zen", 3), "parli": ("zen", 3), "valhalla": ("zen", 3)}   # 「相棒がいないと働かない」札（創世竜ループの部品）
PLAYRULE = {}                             # 新カード用：キー → fn(deck, k) -> 出せない理由 or None（色の判定のあとに使い、進化・チェンジの標準判定のかわりになる）
ATK_POWER = {"crossfire": 1000000}        # 攻撃中のパワー（チェンジ元になれるか）


def _invade_keys():
    """侵略を持つカード（コストを払わずコマンドの上に重ねるので色を問わない）"""
    import engine3
    return engine3.INVADEX


def _atk_power(c):
    return ATK_POWER.get(c.key, c.power)


def _has(deck, k, pred):
    return sum(v for kk, v in deck.items() if kk != k and pred(BY_KEY[kk]))


def why_not(deck, k):
    """出せないカードなら、その理由（文字）を返す。出せるなら None"""
    c = BY_KEY[k]
    if k in FREE:
        if sum(v for kk, v in deck.items() if kk in GRAVE_MAKERS) < GRAVE_MIN:
            return f"墓地を肥やすカードが{GRAVE_MIN}枚ない"
    elif k in NOCOLOR or k in _invade_keys():
        pass                                # 侵略はコストを払わず重ねるので、色はいらない（元になるコマンドの数で見る）
    elif c.trig or c.gs or (c.twin and c.twin[2]):
        pass                                # S・トリガー／G・ストライクはシールドから使えるので、色がなくても働く
    elif c.civ or c.twin:
        sides = [c.civ] + ([c.twin[1]] if c.twin else [])
        why = None
        for civ in sides:                       # ツインパクトはどちらかの面が使えればよい
            need = COLOR_MIN if len(civ) == 1 else MULTI_MIN
            bad = next((x for x in civ if _has(deck, k, lambda e, x=x: x in e.civ) < need), None)
            if bad is None:
                why = None
                break
            why = f"色（{bad}を出せるカードが{need}枚ない）"
        if why:
            return why
        if c.twin:                              # 呪文側が使えるなら、進化・チェンジの条件は問わない
            tciv = c.twin[1]
            tneed = COLOR_MIN if len(tciv) == 1 else MULTI_MIN
            if all(_has(deck, k, lambda e, x=x: x in e.civ) >= tneed for x in tciv):
                return None
    if k in PLAYRULE:
        return PLAYRULE[k](deck, k)
    if k in PARTNER:
        p, n = PARTNER[k]
        if deck.get(p, 0) < n:
            return f"相棒の{BY_KEY[p].name}が{n}枚ない"
    if k in CHANGE:
        civ, need = CHANGE[k]
        n = _has(deck, k, lambda e: e.kind == "C" and not e.noatk and (civ is None or set(civ) & set(e.civ))
                 and _atk_power(e) >= need)
        if n < CHANGE_MIN:
            return f"革命チェンジの元が{CHANGE_MIN}体いない"
    if c.evo and not c.neo and c.evo != "grave":
        if c.evo in ("cyberv",):
            n = _has(deck, k, lambda e: c.evo in e.races)
        else:
            n = _has(deck, k, lambda e: e.kind == "C" and bool(set(c.evo) & set(e.civ)))
        if n < EVO_MIN:
            return f"進化元が{EVO_MIN}体いない"
    return None


def dead(deck):
    """出せないカード：{カード: (枚数, 理由)}"""
    out = {}
    for k, v in deck.items():
        r = why_not(deck, k)
        if r:
            out[k] = (v, r)
    return out


def dead_copies(deck):
    return sum(v for v, _ in dead(deck).values())


if __name__ == "__main__":
    import engine3                      # 新カードを登録してから見る
    from cards3 import DECKS
    for n, d in DECKS.items():
        print(n, "出せないカード", dead(d) or "なし")
