"""担当57：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚（ジョーカーズ／レクスターズ系）

出典：dmwiki.net の各カードページ。**15枚すべてを別の質問で2回ずつ読み、
コスト・文明・種類・種族・パワー・ブレイク数・能力の本文が2回とも一致することを確かめた。**

  この15枚に入っている仕組み
    ・キリフダッシュ［自然(2)］（モモダチ モンキッド／がんばれ！ガンバンジー）
      ＝「自分のクリーチャーの攻撃の終わりに、そのクリーチャーがその攻撃中にシールドをブレイクしていれば、
         [自然(2)]を支払って手札から召喚してもよい」。`breakwatch=` で印を立て `atkend=` で召喚する。
    ・おとり（がんばれ！ガンバンジー）＝「相手のクリーチャーが攻撃する時、可能ならこのクリーチャーを攻撃する」。
      エンジンの `guard=`（攻撃先を引き受ける差し込み口）で書いた。タップして出るのでプレイヤーへの攻撃も引き受ける。
    ・スーパー・S・トリガー（爆殺!! 覇悪怒楽苦）＝ `shieldcast=`。シールドが1つもなければ S能力（S−）も使う。
    ・ヨビニオン（激ウマ！王道じるしのモモダンゴ）＋「ジョーカーズが出たら墓地のかわりにマナへ」＝ `nograve=True` で
      呪文の行き先を自分で決める。
    ・シンカライズのタマシード4枚（ジョーカーズ／スロットン／ゲラッチョの心絵・コーライルの海幻）＝ `E.SHINKA`。
    ・スター進化（アルカディアス・モモキング）＝ `env0.star_evo_rep`（退化が成り立つ）。
    ・S-MAX進化（MAX・ザ・ジョニー）＝進化元が要らないので普通のクリーチャーとして登録し、
      「負けるのを置き換える」を `loserep=`、「2体目は出せない」を `fatex=` で書いた。
      パワード・ブレイカーは `brkx=`、「各ブレイクの前にシールド化」は `breakpre=`。

  調べ直して意外だった点
    ・《モモダチ モンキッド》は既実装の《ヒトリダチ モンキッド》（k34_monkid）とは**別のカード**。
      同じく《ゲラッチョの心絵》は《ゲラッチョ重役／「ミーのチョーおすすめゲラ！」》（k31_geracho）とは別。
    ・《ムシ無視のんのん》は「バトル中、パワーを+4000する」だけで、パワーアタッカーではない
      （ブロックされた時・攻撃された時のバトルでも+4000になる）。
    ・《MAX・ザ・ジョニー》の勝利条件は「攻撃の終わりに自分のシールドが**10以上**」。
      ブレイクの前に自分のシールドを増やすので、ブレイクしながらシールドが増える。
    ・《爆殺!! 覇悪怒楽苦》のS能力は「**火の、進化ではない**クリーチャー」を出す（火でないクリーチャーは出せない）。
    ・殿堂入り・プレミアム殿堂の記載はこの15枚のどのページにも無かった。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all, free_play, worst_hand
from envcards.env0 import SLAYER, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k57_monkid": W + "《モモダチ モンキッド》",
    "k57_pyonchiki": W + "《タイムピョンチキ／オラオラ・ジョーカーズ》",
    "k57_joking": W + "《MMM-ジョーキング》",
    "k57_sanninshu": W + "《我ら、モモダチ三人衆!!!》",
    "k57_ganbanjee": W + "《がんばれ！ガンバンジー》",
    "k57_nonnon": W + "《ムシ無視のんのん／灰になるほどヒート》",
    "k57_bakusatsu": W + "《爆殺!! 覇悪怒楽苦》",
    "k57_momodango": W + "《激ウマ！王道じるしのモモダンゴ》",
    "k57_maxjohnny": W + "《MAX・ザ・ジョニー》",
    "k57_jokerskokoroe": W + "《ジョーカーズの心絵》",
    "k57_slotton": W + "《スロットンの心絵》",
    "k57_geracho": W + "《ゲラッチョの心絵》",
    "k57_korile": W + "《コーライルの海幻》",
    "k57_arcadias": W + "《アルカディアス・モモキング》",
    "k57_gingamax": W + "《護天!銀河MAX》",
}
JK = ("jokers", "rexstars")


# ================================================================ 共通の道具
def _until_my_turn(s, i):
    """「次の自分のターンのはじめまで」の期限（env0.lock_until_my_turn と同じ数え方）"""
    return s.turn + (1 if s.tp == i else 0)


def bo_k57(s, u):
    """このモジュールが与えた「ブロッカー」（期限つき）。印が付いたカードだけに効く"""
    return u.x.get("k57_blk", -1) >= s.turn


def so_k57(s, i, u):
    """このモジュールが与えた「スピードアタッカー」（期限つき）"""
    return u.x.get("k57_sa", -1) >= s.turn


def _grant(s, i, u, blk=False, sa=False):
    lim = _until_my_turn(s, i)
    if blk:
        u.x["k57_blk"] = lim
    if sa:
        u.x["k57_sa"] = lim


def _best_from_hand(s, i, pred):
    """手札のうち条件に合う、いちばん重要度の高いカード"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        if pred(BY_KEY[k]) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    return best


def _playable_cre(c):
    """進化元なしで出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


# ---------------------------------------------------------------- キリフダッシュ［自然(2)］
_KIRI = ("k57_monkid", "k57_ganbanjee")


def bw_kirifuda(s, ai, di, n):
    """キリフダッシュの条件：いま攻撃しているクリーチャーが、この攻撃中にシールドをブレイクしたことを覚える。

    全体に効く差し込み口なので、キリフダッシュを持つこの2枚のどちらかが手札にある時だけ働く。"""
    p = s.P[ai]
    if not any(k in p.hand for k in _KIRI):
        return
    u = s.atk
    if u is not None:
        p.x["k57_brk"] = (s.turn, u.uid)


def _kirifuda(key, cost=2, civ="N"):
    """キリフダッシュ：自分のクリーチャーの攻撃の終わりに、そのクリーチャーがその攻撃中に
    シールドをブレイクしていれば、[civ(cost)]を支払って手札から召喚してもよい（払えるなら召喚する）"""
    def f(s, i, u):
        p = s.P[i]
        if key not in p.hand:
            return
        if p.x.get("k57_brk") != (s.turn, u.uid):
            return
        if len(p.mana) - p.mused < cost or not set(civ) <= E.civs(p):
            return
        if s.fate(i, key, "hand", True) != "ok":
            return
        p.hand.remove(key)
        p.mused += cost
        s.ev(f"　キリフダッシュ[自然({cost})]：{BY_KEY[key].name} を{cost}マナで召喚")
        s.enter(i, key, "hand", True)
    return f


# ================================================================ モモダチ モンキッド
def e_monkid(s, i, u):
    """出た時、自分の山札の上から1枚目をマナゾーンに置く"""
    s.ramp(i, 1)


add("k57_monkid", "モモダチ モンキッド", 3, "N", power=1000, races=("jokers", "teamkirifuda"),
    pri=4, roles="acc",
    enter=e_monkid, breakwatch=bw_kirifuda, atkend=_kirifuda("k57_monkid"),
    text="＜キリフダッシュ＞[自然(2)]（自分のクリーチャーの攻撃の終わりに、そのクリーチャーがその攻撃中に"
         "シールドをブレイクしていれば、このクリーチャーを[自然(2)]支払って手札から召喚してもよい。"
         "払えるなら召喚する）。このクリーチャーが出た時、自分の山札の上から1枚目をマナゾーンに置く",
    source=SRC["k57_monkid"])


# ================================================================ タイムピョンチキ／オラオラ・ジョーカーズ
def _pyon_win(s, i):
    """バトルに勝った時、山札の上から2枚をマナゾーンに置いてもよい。
    そうしたら、自分のマナゾーンのカードを1枚手札に戻す（マナは1枚増えて手札も1枚増えるので必ず行う）"""
    p = s.P[i]
    if len(p.deck) <= 2:
        return
    s.ramp(i, 2)
    if not p.mana:
        return
    k = max(p.mana, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　タイムピョンチキ：マナの {BY_KEY[k].name} を手札へ")


def bf_pyon(s, ai, au, di, du, a_dies, d_dies):
    if au.k == "k57_pyonchiki" and d_dies and not a_dies:
        _pyon_win(s, ai)
    if du.k == "k57_pyonchiki" and a_dies and not d_dies:
        _pyon_win(s, di)
    return a_dies, d_dies


def sp_oraora(s, i):
    """オラオラ・ジョーカーズ：自分の山札の上から1枚をマナゾーンに置く。そのカードがジョーカーズなら1枚引く"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    if s.has(1 - i, "robin"):
        p.deck.insert(0, p.deck.pop())
        return
    k = p.deck.pop()
    s.add_mana(i, k, src="deck")
    s.ev(f"　オラオラ・ジョーカーズ：{BY_KEY[k].name} をマナゾーンへ")
    if "jokers" in BY_KEY[k].races:
        s.draw(i)


add("k57_pyonchiki", "タイムピョンチキ／オラオラ・ジョーカーズ", 4, "N", power=5000, mach=True,
    races=JK, twin=(3, "N", False), pri=5, roles="acc atk draw",
    battlefx=bf_pyon, spell=sp_oraora,
    text="マッハファイター。このクリーチャーがバトルに勝った時、自分の山札の上から2枚をマナゾーンに置いてもよい。"
         "そうしたら、自分のマナゾーンのカードを1枚（重要度のいちばん高いもの）手札に戻す。"
         "呪文側《オラオラ・ジョーカーズ》（自然3）：自分の山札の上から1枚をマナゾーンに置く。"
         "そのカードがジョーカーズなら、カードを1枚引く",
    source=SRC["k57_pyonchiki"])


# ================================================================ MMM-ジョーキング
def react_joking(s, di, au):
    """相手のクリーチャーが自分（プレイヤー）を攻撃する時、自分のシールドが1つもなく、
    自分のマナゾーンに光文明と自然文明があれば、このクリーチャーを手札から出してもよい"""
    d = s.P[di]
    if "k57_joking" not in d.hand or s.atktgt is not None or d.sh:
        return False
    cv = E.civs(d)
    if "L" not in cv or "N" not in cv:
        return False
    if s.fate(di, "k57_joking", "hand", False) != "ok":
        return False
    d.hand.remove("k57_joking")
    s.ev("　MMM-ジョーキング：シールドが0なので手札から出る")
    s.enter(di, "k57_joking", "hand", False)
    return True


def a_joking(s, i, u):
    """攻撃する時、1枚引く。その後、コスト4以下のクリーチャー1体またはコスト4以下のタマシード1枚を手札から出してもよい"""
    s.draw(i)
    if s.over:
        return
    k = _best_from_hand(s, i, lambda c: c.cost <= 4 and (_playable_cre(c) or c.kind == "T"))
    if k is not None:
        s.ev(f"　MMM-ジョーキング：手札から {BY_KEY[k].name} を出す")
        free_play(s, i, k)


add("k57_joking", "MMM-ジョーキング", 5, "LN", power=6000, brk=2, blocker=True, mach=True,
    races=("jokersdragon", "jokers", "dragon", "rexstars"), pri=7, roles="blk atk draw",
    react=react_joking, attack=a_joking,
    text="相手のクリーチャーが自分を攻撃する時、自分のシールドが1つもなく、自分のマナゾーンに光文明と自然文明が"
         "あれば、このクリーチャーを自分の手札から出してもよい。ブロッカー。マッハファイター。W・ブレイカー。"
         "このクリーチャーが攻撃する時、カードを1枚引く。その後、コスト4以下のクリーチャーを1体、"
         "またはコスト4以下のタマシードを1枚、自分の手札から出してもよい",
    source=SRC["k57_joking"])


# ================================================================ 我ら、モモダチ三人衆!!!
def e_sanninshu(s, i, u):
    """出た時、自分の山札の上から1枚目をマナゾーンに置く"""
    s.ramp(i, 1)


def t_sanninshu(s, i, u):
    """自分のターンのはじめに、自分のシールドを1つ手札に加えてもよい。
    ただし、その「S・トリガー」は使えない（シールドが2つ以上ある時だけ行う＝0枚にはしない）"""
    p = s.P[i]
    if len(p.sh) < 2:
        return
    j = max(range(len(p.sh)), key=lambda x: E.PRI[p.sh[x][0]])
    r = s.take_shield(i, j, "hand")
    if r is not None:
        s.ev(f"　我ら、モモダチ三人衆!!!：シールドの {BY_KEY[r[0]].name} を手札へ（S・トリガーは使えない）")


add("k57_sanninshu", "我ら、モモダチ三人衆!!!", 3, "FN", power=3000, gs=True, races=JK,
    pri=4, roles="acc trg draw",
    enter=e_sanninshu, tstart=t_sanninshu,
    text="G・ストライク（相手の攻撃中、このクリーチャーを自分のシールドゾーンから手札に加える時、表向きにして"
         "相手のクリーチャー1体を選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "このクリーチャーが出た時、自分の山札の上から1枚目をマナゾーンに置く。"
         "自分のターンのはじめに、自分のシールドを1つ手札に加えてもよい。ただし、その「S・トリガー」は使えない"
         "（シールドが2つ以上ある時だけ加える。加えるのは重要度のいちばん高いシールド）",
    source=SRC["k57_sanninshu"])


# ================================================================ がんばれ！ガンバンジー
def e_ganbanjee(s, i, u):
    """このクリーチャーをタップしてバトルゾーンに出してもよい
    （おとりの能力を働かせるため必ずタップして出す。召喚酔いで出たターンは攻撃できないので損がない）"""
    s.tap_cre(i, u)


def gd_ganbanjee(s, di, au, tu):
    """相手のクリーチャーが攻撃する時、可能ならこのクリーチャーを攻撃する（おとり）。

    全体に効く差し込み口なので、このカードが自分の場にある時だけ働く。
    タップしていれば攻撃できる＝プレイヤーへの攻撃も引き受ける。"""
    if not s.has(di, "k57_ganbanjee"):
        return None
    for z in s.P[di].board:
        if z.k == "k57_ganbanjee" and z.c.kind == "C" and z.tap and z is not tu:
            return z
    return None


add("k57_ganbanjee", "がんばれ！ガンバンジー", 6, "N", power=4000, trig=True,
    races=("jokers", "teamkirifuda"), pri=6, roles="trg dis",
    enter=e_ganbanjee, guard=gd_ganbanjee, breakwatch=bw_kirifuda, atkend=_kirifuda("k57_ganbanjee"),
    text="S・トリガー。＜キリフダッシュ＞[自然(2)]（自分のクリーチャーの攻撃の終わりに、そのクリーチャーが"
         "その攻撃中にシールドをブレイクしていれば、このクリーチャーを[自然(2)]支払って手札から召喚してもよい）。"
         "このクリーチャーをタップしてバトルゾーンに出してもよい（おとりを働かせるため必ずタップして出す）。"
         "相手のクリーチャーが攻撃する時、可能ならこのクリーチャーを攻撃する",
    source=SRC["k57_ganbanjee"])


# ================================================================ ムシ無視のんのん／灰になるほどヒート
def px_nonnon(s, i, u, atk):
    """バトル中、このクリーチャーのパワーを+4000する（攻撃してバトルする分はここで足す）"""
    return 4000 if atk else 0


def _nonnon_win(s, i):
    """バトルに勝った時、自分の手札からコスト5以下のジョーカーズ・クリーチャーを1体出してもよい"""
    k = _best_from_hand(s, i, lambda c: _playable_cre(c) and c.cost <= 5 and "jokers" in c.races)
    if k is not None:
        s.ev(f"　ムシ無視のんのん：バトルに勝ったので {BY_KEY[k].name} を出す")
        free_play(s, i, k)


def bf_nonnon(s, ai, au, di, du, a_dies, d_dies):
    """「バトル中、パワーを+4000」を守る側のバトルにも効かせ、「バトルに勝った時」を処理する。

    攻める側の+4000は powerx で入っているので、ここで足すのは守る側の分だけ。"""
    if au.k != "k57_nonnon" and du.k != "k57_nonnon":
        return a_dies, d_dies
    if du.k == "k57_nonnon":
        ap = s.power(ai, au, True)
        dp = s.power(di, du) + 4000
        if d_dies and dp > ap and au.k not in SLAYER and au.k != "kuzen":
            d_dies = False                      # パワー負けで死ぬ分だけ取り消す（スレイヤー等は残す）
        if ap <= dp:
            a_dies = True
    if au.k == "k57_nonnon" and d_dies and not a_dies:
        _nonnon_win(s, ai)
    if du.k == "k57_nonnon" and a_dies and not d_dies:
        _nonnon_win(s, di)
    return a_dies, d_dies


def sp_heat(s, i):
    """灰になるほどヒート：自分の手札からコスト6以下のジョーカーズ・クリーチャーを1体出してもよい。
    そうしたら、相手のクリーチャーを1体選び、その2体をバトルさせてもよい"""
    k = _best_from_hand(s, i, lambda c: _playable_cre(c) and c.cost <= 6 and "jokers" in c.races)
    if k is None:
        return
    before = set(id(z) for z in s.P[i].board)
    if not free_play(s, i, k):
        return
    u = next((z for z in s.P[i].board if id(z) not in before and z.k == k), None)
    if u is None or s.over:
        return
    t = s.target(i)
    if t is not None:
        s.ev(f"　灰になるほどヒート：{u.c.name} と {t.c.name} をバトルさせる")
        s.battle(i, u, 1 - i, t)


add("k57_nonnon", "ムシ無視のんのん／灰になるほどヒート", 6, "F", power=4000, races=("jokers",),
    twin=(5, "F", True), pri=7, roles="atk rem trg",
    powerx=px_nonnon, battlefx=bf_nonnon, spell=sp_heat,
    text="バトル中、このクリーチャーのパワーを+4000する。このクリーチャーがバトルに勝った時、"
         "自分の手札からコスト5以下のジョーカーズ・クリーチャーを1体出してもよい。"
         "呪文側《灰になるほどヒート》（火5・S・トリガー）：自分の手札からコスト6以下のジョーカーズ・クリーチャーを"
         "1体出してもよい。そうしたら、相手のクリーチャーを1体選び、その2体をバトルさせてもよい",
    source=SRC["k57_nonnon"])


# ================================================================ 爆殺!! 覇悪怒楽苦
def _sst_cast(key):
    """スーパー・S・トリガー：シールドゾーンから手札に加える時、コストを支払わずにすぐ唱える。
    その時自分のシールドが1つもなければ（nsh==0）、この呪文にS能力を与える"""
    def f(s, i, k, nsh):
        p = s.P[i]
        if k not in p.hand or not s.spell_ok(i, BY_KEY[k].cost):
            return False
        p.hand.remove(k)
        s.trig[i] += 1
        s.ev(f"　スーパー・S・トリガー：{BY_KEY[k].name}")
        if nsh <= 0:
            p.x["k57_sst"] = key
        try:
            s.cast(i, k)
        finally:
            if s.P[i].x.get("k57_sst") == key:
                s.P[i].x["k57_sst"] = None
        return True
    return f


def _sst_used(s, i, key):
    p = s.P[i]
    if p.x.get("k57_sst") == key:
        p.x["k57_sst"] = None
        return True
    return False


def _bakusatsu_s(s, i):
    """S−自分の山札の上から5枚を見る。その中から、火の、進化ではないクリーチャーを1体出してもよい。
    そうしたら、相手のクリーチャーを1体選び、その2体をバトルさせる。残りを山札の下に置く"""
    p = s.P[i]
    n = min(5, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if _playable_cre(c) and "F" in c.civ and E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    u = None
    if best is not None:
        top.remove(best)
        s.ev(f"　爆殺!! 覇悪怒楽苦（S能力）：{BY_KEY[best].name} を出す")
        u = s.enter(i, best, "deck", False)
    s.rng.shuffle(top)
    for k in top:
        p.deck.insert(0, k)
    if u is None or s.over or u not in s.P[i].board:
        return
    t = s.target(i)
    if t is not None:
        s.ev(f"　爆殺!! 覇悪怒楽苦：{u.c.name} と {t.c.name} をバトルさせる")
        s.battle(i, u, 1 - i, t)


def sp_bakusatsu(s, i):
    """相手のクリーチャーを、コストの合計が8以下になるよう好きな数選び、破壊する"""
    use_s = _sst_used(s, i, "k57_bakusatsu")
    budget = 8
    for _ in range(12):
        if s.over or budget <= 0:
            break
        if not opp_all(s, i, lambda z: z.c.cost <= budget):
            break
        t = s.target(i, lambda z: z.c.cost <= budget)
        if t is None:
            break
        budget -= t.c.cost
        if not destroy(s, i, t):
            break
    if use_s and not s.over:
        _bakusatsu_s(s, i)


add("k57_bakusatsu", "爆殺!! 覇悪怒楽苦", 9, "F", kind="S", pri=9, roles="rem fin trg",
    spell=sp_bakusatsu, shieldcast=_sst_cast("k57_bakusatsu"),
    text="スーパー・S・トリガー（この呪文を自分のシールドゾーンから手札に加える時、コストを支払わずにすぐ"
         "唱えてもよい。その時自分のシールドが1つもなければ、この呪文にS能力を与える）。"
         "相手のクリーチャーを、コストの合計が8以下になるよう好きな数選び、破壊する"
         "（重要度の高いクリーチャーから順に取れるだけ取る）。"
         "S−自分の山札の上から5枚を見る。その中から、火の、進化ではないクリーチャーを1体出してもよい。"
         "そうしたら、相手のクリーチャーを1体選び、その2体をバトルさせる。残りを好きな順序で山札の下に置く",
    source=SRC["k57_bakusatsu"])


# ================================================================ 激ウマ！王道じるしのモモダンゴ
def sp_momodango(s, i):
    """ヨビニオン：山札の上から、この呪文よりコストが小さいクリーチャーが出るまで表向きにし、それを出す。
    残りをシャッフルして山札の下に置く。その後、自分のクリーチャー1体に
    「ブロッカー」と「スピードアタッカー」を次の自分のターンのはじめまで与える。
    ヨビニオンで出したのがジョーカーズなら、唱えた後、墓地のかわりにマナゾーンに置く"""
    p = s.P[i]
    flipped, got = [], None
    while len(p.deck) > 1:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and c.cost < 6:
            got = k
            break
        flipped.append(k)
    jk = False
    if got is not None:
        if _playable_cre(BY_KEY[got]):
            s.ev(f"　ヨビニオン：{BY_KEY[got].name} を出す")
            s.enter(i, got, "deck", False)
            jk = "jokers" in BY_KEY[got].races
        else:
            flipped.append(got)             # 進化クリーチャーは進化元がなく出せない
    s.rng.shuffle(flipped)
    for k in flipped:
        p.deck.insert(0, k)
    cands = [z for z in s.P[i].board if z.c.kind == "C"]
    if cands:
        t = max(cands, key=lambda z: (1 if (z.sick and not z.c.sa) else 0, s.val(z)))
        _grant(s, i, t, blk=True, sa=True)
        s.ev(f"　激ウマ！王道じるしのモモダンゴ：{t.c.name} にブロッカーとスピードアタッカー")
    if jk:
        s.ev("　激ウマ！王道じるしのモモダンゴ：ジョーカーズが出たのでマナゾーンへ")
        s.add_mana(i, "k57_momodango")
    else:
        s.grave_put(i, "k57_momodango")


add("k57_momodango", "激ウマ！王道じるしのモモダンゴ", 6, "LFN", kind="S", trig=True,
    races=("jokers", "teamkirifuda"), pri=7, roles="trg atk",
    spell=sp_momodango, nograve=True, blockok=bo_k57, saok=so_k57,
    text="S・トリガー。ヨビニオン（自分の山札の上から、この呪文よりコストが小さいクリーチャーが出るまで"
         "1枚ずつ表向きにし、そのクリーチャーを出す。残りをシャッフルして山札の下に置く）。"
         "自分のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーに「ブロッカー」と"
         "「スピードアタッカー」を与える（召喚酔いしているいちばん大事なクリーチャーを選ぶ）。"
         "この呪文の「ヨビニオン」で出したのがジョーカーズなら、唱えた後、墓地のかわりにマナゾーンに置く",
    source=SRC["k57_momodango"])


# ================================================================ MAX・ザ・ジョニー
def _max_others(s, i, u):
    """自分の他のジョーカーズまたはレクスターズの数"""
    n = 0
    for z in s.P[i].board:
        if z is u or z.c.kind not in "CT":
            continue
        if "jokers" in z.c.races or "rexstars" in z.c.races:
            n += 1
    return n


def px_maxjohnny(s, i, u, atk):
    """自分の他のジョーカーズまたはレクスターズ1枚につき、このクリーチャーのパワーを+2000する"""
    return 2000 * _max_others(s, i, u)


def bx_maxjohnny(s, i, u):
    """パワード・ブレイカー（パワー5000ごとにシールドを1つ多くブレイクする）"""
    return max(1, s.power(i, u) // 5000)


def bp_maxjohnny(s, ai, di, n):
    """このクリーチャーの各ブレイクの前に、自分の山札の上から1枚目をシールド化する。

    全体に効く差し込み口なので、攻撃しているのがこのクリーチャーの時だけ働く（枚数は減らさない）。"""
    u = s.atk
    if u is None or u.k != "k57_maxjohnny" or not s.has(ai, "k57_maxjohnny"):
        return n
    for _ in range(n):
        if s.over:
            break
        s.add_shield(ai)
    return n


def ae_maxjohnny(s, i, u):
    """このクリーチャーの攻撃の終わりに、自分のシールドが10以上あれば、自分はゲームに勝つ"""
    if u.k != "k57_maxjohnny":
        return
    if len(s.P[i].sh) >= 10:
        s.win(i, "MAX・ザ・ジョニー")


def lose_maxjohnny(s, i, how):
    """自分がゲームに負ける時、かわりにこのクリーチャーを破壊するか、自分の手札から1枚捨てる"""
    p = s.P[i]
    for z in p.board:
        if z.k == "k57_maxjohnny":
            s.ev("　MAX・ザ・ジョニー：負けるかわりにこのクリーチャーを破壊する")
            s.leave(i, z, "grave", destroy=True)
            return True
    if "k57_maxjohnny" in p.hand:
        s.ev("　MAX・ザ・ジョニー：負けるかわりに手札から1枚捨てる")
        s.discard(i, "k57_maxjohnny")
        return True
    return False


def fx_maxjohnny(s, owner, u, i, k, src, summon, res):
    """自分のS-MAX進化クリーチャーが2体以上になる時は、1体だけが残る（2体目は出られず手札に残る）"""
    if i == owner and k == "k57_maxjohnny":
        return "no"
    return res


add("k57_maxjohnny", "MAX・ザ・ジョニー", 6, "L", power=10000, races=JK, pri=12, roles="fin shd atk",
    powerx=px_maxjohnny, brkx=bx_maxjohnny, breakpre=bp_maxjohnny, atkend=ae_maxjohnny,
    loserep=lose_maxjohnny, fatex=fx_maxjohnny,
    text="S-MAX進化（進化元は要らない。自分のS-MAX進化クリーチャーが2体以上になる時は1体だけが残る）。"
         "自分がゲームに負ける時、かわりにこのクリーチャーを破壊するか、自分の手札から《MAX・ザ・ジョニー》を1枚捨てる。"
         "パワード・ブレイカー（パワー5000ごとにシールドを1つ多くブレイクする）。"
         "自分の他のジョーカーズまたはレクスターズ1枚につき、このクリーチャーのパワーを+2000する。"
         "このクリーチャーの各ブレイクの前に、自分の山札の上から1枚目をシールド化する。"
         "このクリーチャーの攻撃の終わりに、自分のシールドが10以上あれば、自分はゲームに勝つ",
    note="「S-MAX進化クリーチャーが2体以上なら1体を残して残りを手札に戻す」は、"
         "2体目が出ようとした時に出られず手札に残る形で書いた（結果は同じ）",
    source=SRC["k57_maxjohnny"])


# ================================================================ ジョーカーズの心絵
def e_jokerskokoroe(s, i, u):
    """出た時、各プレイヤーは自身のクリーチャーとタマシードを最大1つずつ選び、残りをすべて山札に加えてシャッフルする。
    その後、各プレイヤーは、こうして山札に加えたカード1枚につき、自身の山札の上から1枚目をシールド化する"""
    added = [0, 0]
    for j in (0, 1):
        p = s.P[j]
        cre = [z for z in p.board if z.c.kind == "C"]
        tam = [z for z in p.board if z.c.kind == "T"]
        keep = []
        if cre:
            keep.append(max(cre, key=s.val))        # 持ち主が選ぶので、いちばん大事なものを残す
        if tam:
            keep.append(max(tam, key=s.val))
        for z in list(p.board):
            if z.c.kind not in "CT" or z in keep or z not in p.board:
                continue
            n = 1 + len(z.under)
            if s.leave(j, z, "deck", by_opp=(j != i)):
                added[j] += n
        if added[j]:
            s.rng.shuffle(p.deck)
    s.ev(f"　ジョーカーズの心絵：山札に戻したのは 自分{added[i]}枚／相手{added[1 - i]}枚")
    for j in (0, 1):
        for _ in range(added[j]):
            if s.over:
                return
            s.add_shield(j)


add("k57_jokerskokoroe", "ジョーカーズの心絵", 8, "L", kind="T", races=JK, pri=9, roles="rem shd",
    enter=e_jokerskokoroe,
    text="シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、各プレイヤーは自身のクリーチャーとタマシードを最大1つずつ選び、"
         "残りをすべて山札に加えてシャッフルする（持ち主はいちばん大事なものを残す）。その後、各プレイヤーは、"
         "こうして山札に加えたカード1枚につき、自身の山札の上から1枚目をシールド化する",
    source=SRC["k57_jokerskokoroe"])
E.SHINKA.add("k57_jokerskokoroe")


# ================================================================ スロットンの心絵
def e_slotton(s, i, u):
    """出た時、次のうちいずれか1つを選ぶ。
      ▶カードを1枚引く
      ▶光のコスト7以下の進化クリーチャーを1体、自分の手札から出す。
        次の自分のターンのはじめまで、そのクリーチャーに「ブロッカー」を与える
    （進化クリーチャーを出せる時はそちらを選ぶ）"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.evo or c.cost > 7 or "L" not in c.civ:
            continue
        if E.PRI[k] <= bv or s.fate(i, k, "hand", False) != "ok":
            continue
        if s.evo_src(i, k) is None and not c.neo:
            continue
        best, bv = k, E.PRI[k]
    if best is None:
        s.draw(i)
        return
    src = s.evo_src(i, best)
    p.hand.remove(best)
    s.ev(f"　スロットンの心絵：手札から {BY_KEY[best].name} を出す")
    nu = s.enter(i, best, "hand", False, on=src)
    if nu is not None:
        _grant(s, i, nu, blk=True)


add("k57_slotton", "スロットンの心絵", 5, "L", kind="T", trig=True, races=JK, pri=6, roles="draw trg",
    enter=e_slotton, blockok=bo_k57,
    text="S・トリガー。シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを"
         "置いてもよい）。このタマシードが出た時、次のうちいずれか1つを選ぶ。"
         "▶カードを1枚引く。"
         "▶光のコスト7以下の進化クリーチャーを1体、自分の手札から出す。次の自分のターンのはじめまで、"
         "そのクリーチャーに「ブロッカー」を与える（出せる進化クリーチャーがあればこちらを選ぶ）",
    source=SRC["k57_slotton"])
E.SHINKA.add("k57_slotton")


# ================================================================ ゲラッチョの心絵
def e_geracho(s, i, u):
    """出た時、カードを1枚引く。その後、相手は自身のアンタップしているクリーチャーを1体選び、タップする"""
    s.draw(i)
    if s.over:
        return
    o = s.P[1 - i]
    cands = [z for z in o.board if z.c.kind == "C" and not z.tap]
    if not cands:
        return
    t = min(cands, key=s.val)              # 相手が選ぶので、相手のいちばん安いクリーチャー
    s.tap_cre(1 - i, t)
    s.ev(f"　ゲラッチョの心絵：相手は {t.c.name} をタップする")


add("k57_geracho", "ゲラッチョの心絵", 2, "L", kind="T", trig=True, races=JK, pri=3, roles="draw trg dis",
    enter=e_geracho,
    text="S・トリガー。シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを"
         "置いてもよい）。このタマシードが出た時、カードを1枚引く。"
         "その後、相手は自身のアンタップしているクリーチャーを1体選び、タップする",
    source=SRC["k57_geracho"])
E.SHINKA.add("k57_geracho")


# ================================================================ コーライルの海幻
def e_korile(s, i, u):
    """出た時、クリーチャー1体またはタマシード1枚を選ぶ。その持ち主は、それを山札の下に置き、カードを1枚引く
    （強制。相手に選べるものがなければ自分のものを選ぶ）"""
    t = s.target(i, kinds="CT")
    j = 1 - i
    if t is None:
        cands = [z for z in s.P[i].board if z.c.kind in "CT"]
        if not cands:
            return
        t, j = min(cands, key=s.val), i
    s.ev(f"　コーライルの海幻：{t.c.name} を山札の下へ")
    if s.leave(j, t, "deck", by_opp=(j != i)):
        s.draw(j)


add("k57_korile", "コーライルの海幻", 4, "W", kind="T", trig=True, races=("cyberlord", "rexstars"),
    pri=5, roles="rem trg draw",
    enter=e_korile,
    text="S・トリガー。シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを"
         "置いてもよい）。このタマシードが出た時、クリーチャー1体またはタマシードを1枚選ぶ。"
         "その持ち主は、それを山札の下に置き、カードを1枚引く"
         "（相手のいちばん大事なものを選ぶ。相手に選べるものがなければ自分のいちばん安いものを選ぶ）",
    source=SRC["k57_korile"])
E.SHINKA.add("k57_korile")


# ================================================================ アルカディアス・モモキング
def ex_arcadias(s, i, u):
    """スター進化：自分のレクスターズ、光、または火のクリーチャー1体の上に置く"""
    return "rexstars" in u.c.races or "L" in u.c.civ or "F" in u.c.civ


def ap_arcadias(s, i, u, atk):
    """自分の他のレクスターズすべてのパワーを+2000する"""
    if "rexstars" not in u.c.races:
        return 0
    n = sum(1 for z in s.P[i].board if z.k == "k57_arcadias" and z is not u)
    return 2000 * n


def _cast_civ(c, cost):
    """いま唱えようとしている側の文明（ツインパクトは、コストが合う側＝呪文側を見る）。

    エンジンは呪文のコストを、呪文単体なら c.cost、ツインパクトなら c.twin[0] で渡すので、
    どちらの側を唱えようとしているかはコストで見分けられる。"""
    if c.kind == "S" and c.cost == cost:
        return c.civ
    if c.twin and c.twin[0] == cost:
        return c.twin[1]
    return c.civ if c.kind == "S" else (c.twin[1] if c.twin else c.civ)


def sl_arcadias(s, i, cost, k=None):
    """相手は、光ではない呪文を唱えられない（i＝唱えようとしている側）。

    エンジンが呪文のキーを渡すようになったので、文明をそのまま見て止める。
    キーが渡らない呼び出し（コストを支払わずに使う一部の効果）では止めない。"""
    if k is None:
        return False
    if not any(z.k == "k57_arcadias" and s.abi(1 - i, z) for z in s.P[1 - i].board):
        return False
    return "L" not in _cast_civ(BY_KEY[k], cost)


def w_arcadias(s, i, u):
    """各ターン、はじめて出る相手のクリーチャーは、タップして出る（i＝出した側）"""
    if u.c.kind != "C" or not s.has(1 - i, "k57_arcadias"):
        return
    p = s.P[i]
    if p.x.get("k57_arctap") == s.turn:
        return
    p.x["k57_arctap"] = s.turn
    s.tap_cre(i, u)
    s.ev(f"　アルカディアス・モモキング：{u.c.name} はタップして出る")


def pr_arcadias(deck, k):
    n = 0
    for kk, v in deck.items():
        if kk == k:
            continue
        c = BY_KEY[kk]
        if (c.kind == "C" or kk in E.SHINKA) and ("rexstars" in c.races or "L" in c.civ or "F" in c.civ):
            n += v
    return None if n >= 4 else "スター進化の元になるレクスターズ／光／火のクリーチャーが4枚ない"


add("k57_arcadias", "アルカディアス・モモキング", 6, "LF", power=12500, brk=3, evo="LF",
    races=("jokersdragon", "jokers", "dragon", "angelcommand", "command", "rexstars"),
    pri=12, roles="fin dis atk",
    evox=ex_arcadias, leaverep=star_evo_rep("k57_arcadias", "アルカディアス・モモキング"),
    aurap=ap_arcadias, spelllock=sl_arcadias, enterwatch=w_arcadias, playrule=pr_arcadias,
    text="スター進化（自分のレクスターズ、光、または火のクリーチャー1体の上に置く。離れる時は一番上のカード"
         "1枚だけが離れ、下のカードはバトルゾーンに残る）。T・ブレイカー。"
         "自分の他のレクスターズすべてのパワーを+2000する。相手は、光ではない呪文を唱えられない。"
         "各ターン、はじめて出る相手のクリーチャーは、タップして出る",
    note="「光ではない呪文を唱えられない」は、唱えようとしている呪文の文明をそのまま見て止めている"
         "（ツインパクトは呪文側の文明で見るので、光の呪文側は唱えられる）。"
         "タップして出すのは、相手がそのターンはじめて出したクリーチャー1体だけ",
    source=SRC["k57_arcadias"])


# ================================================================ 護天!銀河MAX
def sp_gingamax(s, i):
    """次のうちいずれか1つを選ぶ。バトルゾーンに自分の光のクリーチャーと水のクリーチャーがそれぞれ1体以上あれば、
    両方選んでもよい。
      ▶自分の手札を1枚表向きにして、シールド化する
      ▶相手のクリーチャーを1体選び、持ち主の手札に戻す"""
    p = s.P[i]
    both = (any(z.c.kind == "C" and "L" in z.c.civ for z in p.board)
            and any(z.c.kind == "C" and "W" in z.c.civ for z in p.board))
    t = s.target(i)
    if t is not None:
        s.ev(f"　護天!銀河MAX：{t.c.name} を手札に戻す")
        move(s, i, t, "hand")
    if (both or t is None) and p.hand and not s.over:
        k = worst_hand(s, i)
        if k is not None and k in p.hand:
            p.hand.remove(k)
            if s.add_shield(i, k, True):
                s.ev(f"　護天!銀河MAX：手札の {BY_KEY[k].name} を表向きのシールドに")
            else:
                p.hand.append(k)


add("k57_gingamax", "護天!銀河MAX", 4, "LW", kind="S", trig=True, races=("teamgalaxy",),
    pri=5, roles="rem shd trg",
    spell=sp_gingamax,
    text="S・トリガー。次のうちいずれか1つを選ぶ。バトルゾーンに自分の光のクリーチャーと水のクリーチャーが"
         "それぞれ1体以上あれば、両方選んでもよい。"
         "▶自分の手札を1枚（いちばん要らないもの）表向きにして、シールド化する。"
         "▶相手のクリーチャーを1体（いちばん大事なもの）選び、持ち主の手札に戻す。"
         "（1つだけ選ぶ時は、相手のクリーチャーがいれば手札に戻す方を選ぶ）",
    source=SRC["k57_gingamax"])
