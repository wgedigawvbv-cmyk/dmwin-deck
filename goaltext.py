#!/usr/bin/env python3
r"""ゴールを**文章で書く**（条件の種類を選ばなくてよくする）

  ■ なぜ必要か
  ゴール工房では、条件を25種類の中から選び、カード名と数を入れて組み立てる。
  正確に書けるが、**何を選べばいいかが分からない**。使う人が頭に持っているのは
  「ユニバースを下に仕込んで、退化で表に出して、メテオバーンで勝つ」という**筋**であって、
  `in_play_or_under` と `entered` と `special_win` ではない。

  そこで、その筋をそのまま書いてもらい、こちらが条件に直す。

      モモキングダムXが出る
      ユニバースを下に仕込む
      ユニバースが表に出る
      ユニバースで特殊勝利する

  ■ 大事にしたこと：**読み返しを必ず出す**
  文章を読む以上、読み違えは必ず起きる。だから組み立てた条件を**もう一度日本語に戻して**
  見せる（`explain`）。使う人は自分の文と読み返しを見比べて、違えば書き直せばよい。
  読み取れなかった言葉は黙って捨てず、「ここが読めなかった」と返す。

  ■ 仕組み
  1行＝1つの部品。行を言い回しの表（PATTERNS）に当てて条件を決める。
  カード名は、デッキの中のカード → カードプール全部、の順に探す（短い書き方でも当たるように）。
  当てはまる言い回しが無ければ、その行は読めなかったものとして返す。

  機械学習も外部のAPIも使わない。**同じ文を入れれば必ず同じ条件が出る**ので、
  何がどう読まれたかを後から追える。ブラウザの中（Pyodide）でもそのまま動く。

  ■ 使い方
      python goaltext.py "ユニバースを下に仕込む / ユニバースが表に出る / ユニバースで特殊勝利する"
      python goaltext.py --deck ユニバース --file mygoal.txt
      python goaltext.py --explain ユニバース特殊勝利      既にあるゴールを文章にして見せる
"""
import argparse
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ 文字をそろえる
_KANSUU = {"〇": "0", "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
           "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def norm(s):
    """全角と半角、大文字と小文字、かっこの違いを吸収する"""
    s = unicodedata.normalize("NFKC", str(s))
    for a, b in _KANSUU.items():
        s = s.replace(a + "体", b + "体").replace(a + "枚", b + "枚").replace(a + "マナ", b + "マナ")
    return s.strip()


def _clean_card(s):
    """カード名らしき文字列から、かっこや助詞のくずを落とす"""
    s = norm(s).strip(" 　")
    s = re.sub(r"^[《<「【]|[》>」】]$", "", s).strip()
    s = re.sub(r"^(自分の|味方の|こちらの|相手の|敵の)", "", s).strip()
    return s


# ------------------------------------------------------------------ カード名を当てる
class Cards:
    """カード名を当てる係。デッキの中のカードを優先して探す"""

    def __init__(self, deck=None):
        import envcards                   # noqa: F401  現環境のカードを登録してから数える
        from cards3 import BY_KEY
        self.by_key = BY_KEY
        self.all = [(k, c.name) for k, c in BY_KEY.items()]
        self.deck = set(deck or ())
        self._cache = {}

    def _cands(self, q):
        qn = norm(q).lower()
        if not qn:
            return []
        exact = [(k, n) for k, n in self.all if norm(n).lower() == qn]
        if exact:
            return exact
        # 書いた言葉がカード名に含まれる（「ユニバース」→《究極銀河ユニバース》）
        hit = [(k, n) for k, n in self.all if qn in norm(n).lower()]
        if not hit:
            # 逆向き（カード名のほうが短い）
            hit = [(k, n) for k, n in self.all if len(norm(n)) >= 3 and norm(n).lower() in qn]
        return hit

    def find(self, q):
        """返り値：(カード名, 迷った候補の並び)。見つからなければ (None, 候補)"""
        q = _clean_card(q)
        if q in self._cache:
            return self._cache[q]
        hit = self._cands(q)
        if not hit:
            out = (None, [])
        else:
            mine = [x for x in hit if x[0] in self.deck]
            pool = mine or hit
            if len(pool) == 1:
                out = (pool[0][1], [])
            else:
                # いちばん短い名前＝書いた言葉に近いものを採る。同点なら迷ったとして候補を返す
                pool = sorted(pool, key=lambda x: len(x[1]))
                if len(pool) > 1 and len(pool[0][1]) == len(pool[1][1]):
                    out = (None, [n for _k, n in pool[:6]])
                else:
                    out = (pool[0][1], [n for _k, n in pool[1:6]])
        self._cache[q] = out
        return out


# ------------------------------------------------------------------ 言い回しの表
# (正規表現, 作る関数)。上から順に当てる。card= はカード名の入る場所、n= は数。
def _num(m, name="n", d=1):
    try:
        return int(m.group(name))
    except (IndexError, TypeError, ValueError):
        return d


def _card_cond(kind):
    def f(m, cx):
        nm, cands = cx.cards.find(m.group("card"))
        if nm is None:
            cx.miss.append((m.group("card"), cands))
            return None
        c = _num(m, "n", 1)
        return {kind: nm, "count": c} if c > 1 else {kind: nm}
    return f


def _plain(kind, default=1):
    def f(m, cx):
        return {kind: _num(m, "n", default)}
    return f


CARD = r"(?P<card>[^、,／/]+?)"      # 読点をまたがない（『Aが出る、かつマナ7枚』を1枚のカード名と読まないため）
N = r"(?P<n>\d+)"
P = r"[をがはもの]?"          # 助詞。『クリーチャーが3体』『クリーチャーを3体』のどちらでも読む

PATTERNS = [
    # ---- 決着
    (rf"{CARD}(?:で|により|の)?(?:メテオバーン)?(?:特殊勝利|特殊的な勝利)",
     lambda m, cx: (lambda r: {"special_win": r[0]} if r[0] else cx.fail(m.group("card"), r[1]))(
         cx.cards.find(m.group("card")))),
    (r"(?:特殊勝利|特殊的な勝利)", lambda m, cx: {"special_win": True}),
    (r"(?:ダイレクトアタック|ダイレクト|殴り切|殴りきり|直接攻撃)", lambda m, cx: {"direct_attack": True}),
    (r"(?:相手を)?(?:山札切れ|デッキアウト|ライブラリアウト)(?:にする|させる)?", lambda m, cx: {"opp_deck_at_most": 0}),
    (r"(?:とにかく|どんな形でも)?勝(?:つ|利する|ち切る|てる)", lambda m, cx: {"win": True}),
    # ---- ターン
    (rf"{N}\s*ターン目?まで", _plain("turn_at_most")),
    # ---- 盾
    (rf"相手の(?:盾|シールド){P}\s*{N}\s*(?:枚|つ)以下", _plain("opp_shields_at_most")),
    (rf"相手の(?:盾|シールド){P}\s*{N}\s*(?:枚|つ)以上", _plain("opp_shields_at_least")),
    (r"(?:相手の)?(?:盾|シールド)[をがはもの]?(?:全部|すべて|全て)?割(?:る|り切る|りきる|り切って)",
     lambda m, cx: {"opp_shields_at_most": 0}),
    (rf"(?:自分の)?(?:盾|シールド){P}\s*{N}\s*(?:枚|つ)以上", _plain("my_shields_at_least")),
    (rf"(?:自分の)?(?:盾|シールド){P}\s*{N}\s*(?:枚|つ)以下", _plain("my_shields_at_most")),
    # ---- 山札・マナ・手札
    (rf"相手の(?:山札|デッキ){P}\s*{N}\s*枚以下", _plain("opp_deck_at_most")),
    (rf"(?:自分の)?(?:山札|デッキ){P}\s*{N}\s*枚以下", _plain("my_deck_at_most")),
    (rf"相手の(?:山札|デッキ){P}(?:残り)?\s*{N}\s*枚(?:まで)?(?:削|減ら)", _plain("opp_deck_at_most")),
    (rf"(?:自分の)?(?:山札|デッキ){P}(?:残り)?\s*{N}\s*枚(?:まで)?(?:削|減ら)", _plain("my_deck_at_most")),
    (rf"(?:マナ|マナゾーン){P}\s*{N}\s*(?:枚|マナ)?以上", _plain("mana_at_least")),
    (rf"{N}\s*マナ(?:以上)?(?:ため|溜め|貯め|並べ|そろえ|揃え|まで伸ば|伸ば)", _plain("mana_at_least")),
    (rf"(?:手札|手){P}\s*{N}\s*枚以上", _plain("hand_at_least")),
    # ---- 盤面の数
    (rf"相手の(?:クリーチャー|生物|面){P}\s*{N}\s*体以下", _plain("opp_creatures_at_most")),
    (r"相手の(?:場|盤面|クリーチャー)[をがはもの]?(?:空|0体|0|全部|すべて|全て|更地)(?:にする|に出来|にでき|消す)?",
     lambda m, cx: {"opp_creatures_at_most": 0}),
    (rf"(?:すぐ殴れる|すぐに殴れる|アンタップ(?:している)?|動ける|起きている)(?:クリーチャー|面|の)?{P}\s*{N}\s*体(?:以上)?",
     _plain("untapped_at_least")),
    (rf"(?:打点|ブレイク数?|割れる盾){P}\s*{N}\s*(?:点|枚)?以上", _plain("breaks_at_least")),
    (rf"{N}\s*打点", _plain("breaks_at_least")),
    (rf"(?:パワー(?:合計|の合計)?){P}\s*{N}\s*以上", _plain("total_power_at_least")),
    (rf"(?:自分の)?(?:クリーチャー|生物|面|進化元|タネ){P}\s*{N}\s*体(?:以上)?(?:並べ|そろえ|揃え|出す|立て|用意)",
     _plain("creatures_at_least")),
    (rf"(?:自分の)?(?:クリーチャー|生物|面|進化元|タネ){P}\s*{N}\s*体以上", _plain("creatures_at_least")),
    (rf"{N}\s*体(?:以上)?(?:並べ|そろえ|揃え|立て)", _plain("creatures_at_least")),
    # ---- カードを指す（数つき）
    (rf"{CARD}{P}\s*{N}\s*(?:体|枚)(?:以上)?(?:並べ|そろえ|揃え|出す|立て|用意)", _card_cond("in_play")),
    (rf"{CARD}{P}\s*{N}\s*(?:体|枚)以上", _card_cond("in_play")),
    # ---- カードを指す（場所・出来事）
    (rf"相手の(?:場|盤面)に\s*{CARD}\s*{P}(?:いる|いて|ある|あって|立って|残って)", _card_cond("opp_in_play")),
    (rf"{CARD}{P}(?:下に|進化元に)(?:仕込|置|入れ|用意|敷)", _card_cond("in_play_or_under")),
    (rf"{CARD}{P}(?:下|進化元)に(?:ある|いる|入って|ある状態)", _card_cond("in_play_or_under")),
    (rf"{CARD}{P}(?:墓地に(?:落と|置|送|ため|溜め)|捨て)", _card_cond("in_grave")),
    (rf"{CARD}{P}墓地に(?:ある|いる|落ちて)", _card_cond("in_grave")),
    (rf"{CARD}{P}(?:唱え|使(?:う|える)|召喚|プレイ)", _card_cond("played")),
    (rf"{CARD}{P}(?:表に出|めくれ|表向きに)", _card_cond("entered")),
    (rf"{CARD}{P}(?:場に)?出(?:る|た|す|せる)", _card_cond("entered")),
    (rf"{CARD}{P}(?:場に)?(?:着地|踏み倒)", _card_cond("entered")),
    (rf"{CARD}{P}(?:場に)?(?:いる|いて|ある|あって|立って|並んで|残って|そろって|揃って|並ぶ)", _card_cond("in_play")),
]
PATTERNS = [(re.compile(p), f) for p, f in PATTERNS]

# 意味を持たない字（読み残しとして数えない）
_FILLER = re.compile(r"^[\u3040-\u309f\s、。．・,.\-—～~…ー]*$")
# ひらがなと句読点だけなら、送りがなや『〜にする』のような言い回しの残りとみなす。
# 漢字・カタカナ・英数が残っていれば、読めなかった言葉として必ず返す。


class _Cx:
    def __init__(self, cards):
        self.cards = cards
        self.miss = []

    def fail(self, word, cands):
        self.miss.append((word, cands))
        return None


# ------------------------------------------------------------------ 1行を読む
_ANY = re.compile(r"\s*(?:または|もしくは|あるいは)\s*")


def _scan(text, cx):
    """1つの文から、当てはまる条件を**全部**拾う。

    以前は「最初に当たった言い回しだけ」を採っていたので、
    『5ターン目までに勝つ』が {win} だけになり、ターンの条件が落ちていた。
    いまは当たった所を文から取り除いて、取れなくなるまで繰り返す。
    同じ所で複数当たるときは、**文の先頭に近いほう・長いほう**を採る。"""
    out = []
    s = text
    for _ in range(8):
        # 当たった言い回しを全部集め、文の先頭に近いほう・長いほうから試す。
        # **条件が作れなかったものは文を食べない**（ここが抜けていて、
        #  『ユニバースが表に』をカード名と読んで外し、文ごと消してしまっていた）。
        cands = []
        for rx, fn in PATTERNS:
            m = rx.search(s)
            if m:
                cands.append(((m.start(), -(m.end() - m.start())), m, fn))
        cands.sort(key=lambda x: x[0])
        hit = None
        for _k, m, fn in cands:
            n0 = len(cx.miss)
            c = fn(m, cx)
            if c:
                hit = (m, c)
                break
            del cx.miss[n0:]          # 当たらなかった読み方の記録は残さない
        if hit is None:
            break
        m, c = hit
        # 『ダイレクトアタックで勝つ』の「勝つ」のように、勝ち方が書いてあるのに
        # さらに「どんな形でも勝った」を足すと条件が増えるだけなので、足さない
        if c == {"win": True} and any(k in x for x in out
                                      for k in ("direct_attack", "special_win", "opp_deck_at_most")):
            c = None
        if c:
            out.append(c)
        s = (s[:m.start()] + " " + s[m.end():]).strip()
        if not s or _FILLER.match(s):
            s = ""
            break
    return out, s


def parse_line(line, cards):
    """1行 → (条件, 読めなかった言葉の並び)。条件が作れなければ (None, …)"""
    cx = _Cx(cards)
    raw = norm(line)
    s = raw
    # 「一度でも」
    ever = bool(re.search(r"(?:一度でも|いちどでも|どこかで|いずれかの時点で)", s))
    if ever:
        s = re.sub(r"(?:一度でも|いちどでも|どこかで|いずれかの時点で)", "", s)
    # 「〜がいない」「〜を使わずに」
    neg = False
    m = re.search(r"^(.+?)\s*[をがはも]?\s*(?:いない|出ていない|出さない|使わない|使わず|無し|なし)(?:で)?$", s)
    if m:
        s, neg = m.group(1), True

    def one(part):
        cs, left = _scan(part, cx)
        if not cs:
            # 言い回しが無く、カード名だけ書かれている → 「場にいる」とみなす
            nm, cands = cx.cards.find(part)
            if nm:
                return {"in_play": nm}, ""
            return None, part
        return ({"all": cs} if len(cs) > 1 else cs[0]), left

    # 「Xを使わずにYする」＝ X を否定したうえで Y
    m = re.match(r"^(?P<neg>.+?)[をがはも]?(?:使わずに|使わず|使わないで|出さずに|出さず|なしで|無しで)\s*(?P<rest>.+)$", s)
    if m:
        c1, _m1 = parse_line(m.group("neg") + "を使う", cards)
        c2, m2 = parse_line(m.group("rest"), cards)
        cs = [x for x in ({"not": c1} if c1 else None, c2) if x]
        if cs:
            cond = {"all": cs} if len(cs) > 1 else cs[0]
            if ever:
                cond = {"ever": cond}
            return cond, (m2 or [])

    if _ANY.search(s):
        # 「AまたはBが場にいる」…… A には言い回しが付いていないので、B の言い回しを借りる
        frags = [p for p in _ANY.split(s) if p.strip()]
        tail = frags[-1]
        cs, lefts = [], []
        for i, f in enumerate(frags):
            c, left = one(f)
            if c is None and i < len(frags) - 1:
                nm, _ = cx.cards.find(f)
                if nm:
                    c, left = one(tail.replace(_clean_card(tail), f, 1) if _clean_card(tail) in tail else f), ""
                    if isinstance(c, tuple):
                        c, left = c
            if c:
                cs.append(c)
            elif left:
                lefts.append(left)
        cond = {"any": cs} if len(cs) > 1 else (cs[0] if cs else None)
        left = "／".join(lefts)
    else:
        # 「、」「かつ」で区切られていれば、それぞれを読んでから束ねる。
        # 区切りが無い文（『相手の場を空にして8マナためる』）は _scan が複数拾う。
        pieces = [x for x in re.split(r"\s*(?:かつ|そして|、|,)\s*", s) if x.strip()]
        if len(pieces) > 1:
            cs, lefts = [], []
            for pc in pieces:
                c, lf = one(pc)
                if c:
                    cs.append(c)
                elif lf:
                    lefts.append(lf)
            cond = {"all": cs} if len(cs) > 1 else (cs[0] if cs else None)
            left = "／".join(lefts)
        else:
            cond, left = one(s)

    if cond is None:
        return None, cx.miss or [(raw, [])]
    if left and not _FILLER.match(left):
        cx.miss.append((left, []))
    if ever:
        cond = {"ever": cond}
    if neg:
        cond = {"not": cond}
    return cond, cx.miss


# ------------------------------------------------------------------ 文章ぜんぶ
def parse(text, deck=None, name=None, decks=None):
    """文章 → (ゴールの辞書, 読み取りの記録)

    1行＝1つの部品。「名前: 文」と書けば部品の名前になる。
    `#` で始まる行と空行は読み飛ばす。`/` でも部品を区切れる。"""
    cards = deck if isinstance(deck, Cards) else Cards(deck)
    body = norm(text).replace("／", "\n").replace(" / ", "\n")
    parts, notes = [], []
    for raw in body.splitlines():
        l = raw.strip()
        if not l or l.startswith("#"):
            continue
        l = re.sub(r"\s*←.*$", "", l).strip()      # 「←ここをゴール地点にする」の印は読み飛ばす
        if not l:
            continue
        pname = None
        m = re.match(r"^(.{1,24}?)\s*[:：]\s*(.+)$", l)
        if m:
            pname, l = m.group(1), m.group(2)
        cond, miss = parse_line(l, cards)
        miss = [{"word": w, "cands": c} for w, c in (miss or [])]
        if cond is None:
            notes.append({"line": raw, "ok": False, "read": "", "miss": miss, "hint": ""})
            continue
        parts.append({"name": pname or l[:20], "when": cond})
        notes.append({"line": raw, "ok": True, "read": say(cond), "miss": miss,
                      "hint": _hint(cond)})
    goal = {"name": name or (parts[0]["name"] if parts else "名前のないゴール"),
            "decks": list(decks or []),
            "parts": parts}
    if parts:
        goal["goal_at"] = parts[-1]["name"]
    return goal, notes


def _hint(cond):
    """読めたうえで、たぶんこう書きたかったのでは、という助言（黙って変えない）"""
    txt = json.dumps(cond, ensure_ascii=False)
    if "ever" in cond:
        return ""
    if '"in_play_or_under"' in txt or '"creatures_at_least"' in txt or '"breaks_at_least"' in txt:
        return ("盤面は次の瞬間に崩れます。崩れても数えたいなら、文の頭に「一度でも」を付けてください")
    return ""


# ------------------------------------------------------------------ 条件 → 日本語（読み返し）
_SAY = {
    "in_play": "{v}が場にいる", "in_play_or_under": "{v}が場にいる（下に入っているものも数える）",
    "opp_in_play": "相手の場に{v}がいる", "entered": "{v}がこの試合で場に出た",
    "played": "{v}をこの試合で使った", "in_grave": "{v}が墓地にある",
    "in_play_all": "{v}が全部そろっている", "in_play_any": "{v}のどれかがいる",
    "creatures_at_least": "自分のクリーチャーが{v}体以上",
    "opp_creatures_at_most": "相手のクリーチャーが{v}体以下",
    "total_power_at_least": "自分のパワー合計が{v}以上",
    "untapped_at_least": "すぐ殴れるクリーチャーが{v}体以上",
    "breaks_at_least": "いま割れる盾が{v}枚以上",
    "opp_shields_at_most": "相手の盾が{v}枚以下", "opp_shields_at_least": "相手の盾が{v}枚以上",
    "my_shields_at_least": "自分の盾が{v}枚以上", "my_shields_at_most": "自分の盾が{v}枚以下",
    "mana_at_least": "マナが{v}枚以上", "hand_at_least": "手札が{v}枚以上",
    "opp_deck_at_most": "相手の山札が{v}枚以下", "my_deck_at_most": "自分の山札が{v}枚以下",
    "turn_at_most": "自分の{v}ターン目まで",
}


def say(cond):
    """条件1つを日本語に戻す（読み返し用）"""
    if not isinstance(cond, dict) or not cond:
        return "（空）"
    if "all" in cond:
        return "、かつ".join(say(c) for c in cond["all"])
    if "any" in cond:
        return "、または".join(say(c) for c in cond["any"])
    if "not" in cond:
        return say(cond["not"]) + "、ではない"
    if "ever" in cond:
        return "一度でも「" + say(cond["ever"]) + "」になった"
    k = next(iter(cond))
    v = cond[k]
    n = cond.get("count")
    if k == "win":
        return "勝った" if v else "勝っていない"
    if k == "direct_attack":
        return "ダイレクトアタックで勝った"
    if k == "special_win":
        return "特殊勝利で勝った" if v is True else f"《{v}》で特殊勝利した"
    if k in _SAY:
        vv = "・".join(f"《{x}》" for x in v) if isinstance(v, list) else (
            f"《{v}》" if isinstance(v, str) else v)
        s = _SAY[k].format(v=vv)
        if n and n > 1:
            s += f"（{n}つ以上）"
        return s
    return f"{k}={v}"


def explain(goal):
    """ゴール（辞書）を文章に戻す。1部品1行"""
    out = []
    ps = goal.get("parts")
    if ps:
        for p in ps:
            mark = " ←ここをゴール地点にする" if p.get("name") == goal.get("goal_at") else ""
            out.append(f"{p.get('name', '')}: {say(p.get('when', {}))}{mark}")
    elif goal.get("when"):
        out.append(say(goal["when"]))
    return "\n".join(out)


# ------------------------------------------------------------------ 読み取りの記録を見せる
def report(notes):
    out = []
    for n in notes:
        if n["ok"]:
            out.append(f"○ {n['line']}")
            out.append(f"    → {n['read']}")
        else:
            out.append(f"× {n['line']}")
            out.append("    → 読み取れませんでした")
        for m in n["miss"]:
            if m["cands"]:
                out.append(f"    ！『{m['word']}』はどれか決められません：" + "・".join(m["cands"][:5]))
            else:
                out.append(f"    ！『{m['word']}』に当たるカードが見つかりません")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="ゴールを文章で書く")
    ap.add_argument("text", nargs="*", help="文章（/ か改行で部品に分ける）")
    ap.add_argument("--file", help="文章の書かれたテキストファイル")
    ap.add_argument("--deck", help="デッキ名（カード名をそのデッキの中から優先して探す）")
    ap.add_argument("--name", help="ゴールの名前")
    ap.add_argument("--explain", help="既にあるゴールを文章にして見せる（ゴールの名前）")
    ap.add_argument("--json", action="store_true", help="JSONだけを出す")
    a = ap.parse_args()
    import envcards                  # noqa: F401
    if a.explain:
        import goals
        tab = goals.load_goals()
        g = tab.get(a.explain) or next((x for x in tab.values() if a.explain in x.get("name", "")), None)
        if g is None:
            raise SystemExit(f"『{a.explain}』というゴールがありません（python goals.py --list）")
        print(f"【{g['name']}】")
        print(explain(g))
        return
    txt = open(a.file, encoding="utf-8").read() if a.file else " / ".join(a.text)
    if not txt.strip():
        raise SystemExit("文章を渡してください（例： python goaltext.py \"ユニバースを出す / 特殊勝利する\"）")
    deck = None
    if a.deck:
        import solo
        d, nm = solo.load_deck(a.deck)
        deck, a.deck = set(d), nm
    goal, notes = parse(txt, deck, a.name, [a.deck] if a.deck else None)
    if a.json:
        print(json.dumps({"goals": [goal]}, ensure_ascii=False, indent=1))
        return
    print("【読み取り】")
    print(report(notes))
    print()
    print("【mygoals.json に貼り付けるもの】")
    print(json.dumps({"goals": [goal]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
