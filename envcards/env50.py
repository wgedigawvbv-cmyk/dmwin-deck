"""担当50：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚（key は k50_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）と
      生の wiki ソース（?plugin=template&refer=《カード名》）を**別の質問で2回ずつ**読み、
      コスト・文明・種類・種族・パワー・ブレイク数・能力本文がどちらも一致することを確かめた。
      《月下旋壊 ド・リュミーズ》の別のコスト（捨てるのが「カード」か「魔導具」か）と
      《「無月」の頂 ＄スザーク＄》の4つめの能力だけは、文言が効果の大きさを決めるので3回読んだ。

  この札束の中身は【水闇魔導具】一式で、入っている仕組み
    ・**無月の門・絶**（＄スザーク＄・卍月 ガ・リュザーク 卍）＝各ターンの終わりに、自分の魔導具と
      墓地の魔導具カードを合計**6つ**選び、その上に手札／墓地からコストを支払わずに召喚する。
    ・**夢幻無月の門**（ガル・ラガンザーク）＝自分の魔導具クリーチャーが出た時または魔導具呪文を
      唱えた時に、合計**4つ**で同じことをする。
      エンジンに「無月の門」という専用の差し込み口は無いが、`tendp=`／`enterwatch=`／`spellwatch=` と
      `s.enter(on=…)` で**そのまま書ける**ので近似にはしていない（env38 の虚無月の門と同じ形）。
    ・**S・トリガー・プラス**（堕呪 ボックドゥ）＝相手のターンで、そのターン自分のシールドが
      2つ以上ブレイクされていればP能力も使う（`p.brk_t` がその枚数）。
    ・**スーパー・S・トリガー**（堕呪 ギャプドゥ）＝`shieldcast=` でシールドから直接唱え、
      その時シールドが0枚ならS能力も使う。
    ・**呪文の別のコスト**（月下旋壊 ド・リュミーズ）＝魔導具2枚を手札から捨てて唱える（`freeacts=`）。
    ・**EXライフ＋コスト－90**（頂上混成 ガリュディアス・モモミーズ'22）。

  魔導具の数え方について（大事）
    このシミュレーターでは、すでにある 魔導具 のカード（k32_vaipoi／k37_grideria／k39_jigus／k46_vogenm）が
    種族 `"magic"` で登録されているが、`"magic"` は**種族「マジック」**（華謡の精霊カンツォーネ、
    巨魔天 アオフェシーなど）にも使われていて区別がつかない。
    そこでこの担当分では、魔導具のカードに `"magic"` と**別の印 `"madogu"`** の両方を付け、
    無月の門の数え方は「`"madogu"` を持つ」＋「すでにある魔導具カードのキー（MADOGU_OTHER）」で数える。
    こうすると、同じ弾の《好詠音愛 クロカミ》（種族マジック・マーメイド＝マジック）を
    魔導具として数えてしまう事故が起きない。逆に、ほかの担当の `"magic"` を見る札
    （env38 の虚無月の門など）からは、この担当分の魔導具もちゃんと魔導具として数えられる。

  調べ直して意外だった点（最後の返答にも書いた）
    ・《堕呪 ボックドゥ》は古い《堕呪 シュノドゥ》の上位版で、**S・トリガーではなく
      S・トリガー・プラス**（DM23-EX1 の新規カード）。名前が堕呪サイクルなので古い札だと思い込みやすい。
    ・《月下旋壊 ド・リュミーズ》は**呪文なのに種族がドルスザク**（魔導具ではない）。
      だから自分自身は無月の門の数には入らない。
    ・《頂上混成 ガリュディアス・モモミーズ'22》は素のコストが**99**・パワー**99000**で、
      「墓地にクリーチャーではないカードが4枚以上」で**90下がって9**になる。
    ・《ガル・ラガンザーク》《「無月」の頂 ＄スザーク＄》《月下旋壊 ド・リュミーズ》
      《ストリーミング・シェイパー》の4枚が**殿堂入り**。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move
from envcards.env0 import (SLAYER, discard_choice, exlife_enter, exlife_rep, lock_until_my_turn, owner_of,
                           worst_own)

W = "https://dmwiki.net/"
SRC = {
    "k50_gonpadu": W + "《堕呪 ゴンパドゥ》",
    "k50_baredu": W + "《堕呪 バレッドゥ》",
    "k50_bokkudu": W + "《堕呪 ボックドゥ》",
    "k50_eavo": W + "《堕呪 エアヴォ》",
    "k50_kurokami": W + "《好詠音愛 クロカミ》",
    "k50_suzark": W + "《「無月」の頂 ＄スザーク＄》",
    "k50_gashagon": W + "《凶鬼98号 ガシャゴン／堕呪 ブラッドゥ》",
    "k50_garlagan": W + "《ガル・ラガンザーク》",
    "k50_garyuzaku": W + "《卍月 ガ・リュザーク 卍／「すべて見えているぞ！」》",
    "k50_momomies": W + "《頂上混成 ガリュディアス・モモミーズ'22》",
    "k50_gyapudu": W + "《堕呪 ギャプドゥ》",
    "k50_ukidu": W + "《堕呪 ウキドゥ》",
    "k50_dorumiis": W + "《月下旋壊 ド・リュミーズ》",
    "k50_shaper": W + "《ストリーミング・シェイパー》",
    "k50_oriotis": W + "《オリオティス・ジャッジ》",
}

# すでにほかの担当が登録している「魔導具」のカード。種族 "magic" は種族「マジック」とも
# かぶっているので、魔導具かどうかはこの表と印 "madogu" で決める（ファイル先頭の説明を参照）。
MADOGU_OTHER = frozenset({"k32_vaipoi", "k37_grideria", "k39_jigus", "k46_vogenm"})


# ================================================================ 共通の小道具
def _madogu(c):
    """そのカードが魔導具か"""
    return "madogu" in c.races or c.key in MADOGU_OTHER


def _madogu_n(s, i):
    """自分の魔導具の数（バトルゾーンにあるもの＋墓地にある魔導具カード）"""
    n = 0
    for z in s.P[i].board:
        if _madogu(z.c):
            n += 1
    for k in s.P[i].grave:
        if _madogu(BY_KEY[k]):
            n += 1
    return n


def _put_from_hand(s, i, pred=None):
    """クリーチャー1体を自分の手札からコストを支払わずに出す（重要度のいちばん高いもの）"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo):
            continue
        if pred is not None and not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return False
    s.ev(f"　{BY_KEY[best].name} を手札から出す")
    return free_play(s, i, best)


def _mugetsu_gate(key, need):
    """無月の門：自分の魔導具と墓地にある魔導具カードを合計 need 個選び、その上にこのクリーチャーを
    自分の手札または墓地からコストを支払わずに召喚する（返り値：召喚できたら True）。

    どれを選ぶかは全デッキ共通の決まりで機械的に決める：墓地の魔導具のうち重要度の低いものから使い、
    足りない分だけバトルゾーンの魔導具のうち失うのがいちばん安いものを使う（env38 の虚無月の門と同じ）。
    バトルゾーンの魔導具は「その上に召喚」＝下のカードになるので、離れたことにはならない。"""
    def gate(s, i):
        p = s.P[i]
        zn = "hand" if key in p.hand else ("grave" if key in p.grave else None)
        if zn is None or s.over:
            return False
        gr = sorted([x for x in p.grave if x != key and _madogu(BY_KEY[x])], key=E.PRI.get)
        bd = sorted([z for z in p.board if _madogu(z.c)], key=lambda z: s.val(z))
        if len(gr) + len(bd) < need:
            return False
        if s.fate(i, key, zn, True) != "ok":
            return False
        pick_g = gr[:need]
        pick_b = bd[: need - len(pick_g)]
        zone = p.hand if zn == "hand" else p.grave
        zone.remove(key)
        for x in pick_g:
            p.grave.remove(x)
        base = pick_b[0] if pick_b else None
        s.ev(f"　無月の門：{BY_KEY[key].name} を魔導具{need}つの上に召喚（コストを支払わずに）")
        u = s.enter(i, key, zn, True, on=base)
        if u is None:
            for x in pick_g:                     # 出られなかったら墓地の魔導具は戻す
                p.grave.append(x)
            return False
        for z in pick_b[1:]:
            if z in p.board:
                p.board.remove(z)
                u.under = u.under + [z.k] + z.under
        u.under = u.under + pick_g
        return True
    return gate




# ---------------------------------------------------------------- スーパー・S・トリガー
_SST = {}        # そのS能力を使える状態で唱えられたか（キーごと）


def _sst_cast(key):
    """スーパー・S・トリガー：このカードをシールドゾーンから手札に加える時、コストを支払わずにすぐ唱える。
    その時シールドが1つもなければ（nsh==0）S能力も使う。

    SHIELDCAST なので、ブレイクでも効果でシールドから手札に来る時でも通り、
    「手札に来たのに唱えず、同じターンに手札から唱えた」時にS能力が付くこともない。"""
    def f(s, i, k, nsh):
        p = s.P[i]
        if k not in p.hand or not s.spell_ok(i, BY_KEY[k].cost):
            return False                         # 唱えられないなら、ふつうに手札に加えたままにする
        p.hand.remove(k)
        s.trig[i] += 1
        s.ev(f"　スーパー・S・トリガー：{BY_KEY[k].name}")
        if nsh <= 0:
            p.x["k50_sst"] = key                 # シールドが1つもないのでS能力も使える
        try:
            s.cast(i, k)
        finally:
            if s.P[i].x.get("k50_sst") == key:
                s.P[i].x["k50_sst"] = None
        return True
    return f


def _sst_used(s, i, key):
    """この呪文が、自分のシールドが1つもない状態でシールドゾーンから唱えられたか（S能力を使えるか）"""
    p = s.P[i]
    if p.x.get("k50_sst") == key:
        p.x["k50_sst"] = None
        return True
    return False


# ================================================================ 1 堕呪 ゴンパドゥ
def sp_gonpadu(s, i):
    """自分の山札の上から3枚を見る。その中から1枚を手札に加え、残りを好きな順序で山札の下に置く"""
    s.dig(i, 3, lambda k: True, "bottom")


add("k50_gonpadu", "堕呪 ゴンパドゥ", 2, "W", kind="S", races=("madogu",), pri=3, roles="draw",
    spell=sp_gonpadu,
    text="自分の山札の上から3枚を見る。その中から1枚を手札に加え、残りを好きな順序で山札の下に置く"
         "（手札に無い札のうち重要度のいちばん高いものを取る）",
    source=SRC["k50_gonpadu"])


# ================================================================ 2 堕呪 バレッドゥ
def sp_baredu(s, i):
    """カードを2枚引き、自分の手札を1枚捨てる"""
    s.draw(i, 2)
    discard_choice(s, i)


add("k50_baredu", "堕呪 バレッドゥ", 2, "W", kind="S", races=("madogu",), pri=3, roles="draw",
    spell=sp_baredu,
    text="カードを2枚引き、自分の手札を1枚捨てる（捨てるのは手札のうち重要度のいちばん低い札）",
    source=SRC["k50_baredu"])


# ================================================================ 3 堕呪 ボックドゥ
def sp_bokkudu(s, i):
    """S・トリガー・プラス。P−相手のエレメントを1つ選び、持ち主の手札に戻す。
    相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない"""
    p = s.P[i]
    if s.tp != i and p.brk_t >= 2:               # 相手のターンで、このターン自分の盾が2つ以上割られた
        t = s.target(i, kinds="CTX")
        if t is not None:
            s.ev(f"　S・トリガー・プラス：{t.c.name} を持ち主の手札に戻す")
            move(s, i, t, "hand")
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　堕呪 ボックドゥ：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k50_bokkudu", "堕呪 ボックドゥ", 2, "W", kind="S", trig=True, races=("madogu",),
    pri=4, roles="trg dis rem",
    spell=sp_bokkudu,
    text="S・トリガー・プラス（このカードを自分のシールドゾーンから手札に加える時、"
         "コストを支払わずにすぐ唱えてもよい。それが相手のターンで、そのターン中に自分のシールドが"
         "2つ以上ブレイクされていれば、このカードにP能力を与える）。"
         "P−相手のエレメントを1つ選び、持ち主の手札に戻す。"
         "相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない",
    note="S・トリガー・プラスのP能力は、「相手のターン中に唱え、そのターン自分のシールドが2つ以上"
         "ブレイクされている」（s.tp != 自分 かつ p.brk_t >= 2）で判定している",
    source=SRC["k50_bokkudu"])


# ================================================================ 4 堕呪 エアヴォ
def sp_eavo(s, i):
    """バトルゾーンにあるコスト7以下のカードを1枚選び、持ち主の手札に戻す"""
    t = s.target(i, lambda u: u.c.cost <= 7, kinds="CTX")
    if t is not None:
        s.ev(f"　堕呪 エアヴォ：{t.c.name} を持ち主の手札に戻す")
        move(s, i, t, "hand")
        return
    z = worst_own(s, i, lambda u: u.c.cost <= 7)     # 相手に対象がいなければ自分のいちばん安いもの
    if z is None:
        return
    s.ev(f"　堕呪 エアヴォ：自分の {z.c.name} を手札に戻す")
    s.leave(i, z, "hand")


add("k50_eavo", "堕呪 エアヴォ", 4, "W", kind="S", trig=True, races=("madogu",),
    pri=5, roles="trg rem",
    spell=sp_eavo,
    text="S・トリガー。バトルゾーンにあるコスト7以下のカードを1枚選び、持ち主の手札に戻す"
         "（相手のいちばん重要なものを選ぶ。相手に対象がなければ、自分のいちばん安いものを戻す）",
    source=SRC["k50_eavo"])


# ================================================================ 5 好詠音愛 クロカミ
def sa_kurokami(s, i, k, twin=False):
    """自分の呪文を唱えるコストを1少なくする（ただし0以下にはならない＝1止まり）。

    `spcostaura=` は呪文（`spcost` を通るカード）全体にかかるので、
    クロカミが場にある持ち主の呪文だけに効くよう必ず確かめる。場の枚数ぶん重なる。"""
    c = BY_KEY[k]
    if not (c.kind == "S" or twin):          # ツインパクトの呪文側も「呪文」
        return 0
    cost = c.twin[0] if twin else c.cost
    n = sum(1 for z in s.P[i].board if z.k == "k50_kurokami")
    if not n:
        return 0
    return -min(n, max(0, cost - 1))


def sw_kurokami(s, i, k):
    """自分が呪文を唱えた時、相手のクリーチャーを1体選ぶ。
    次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない"""
    n = sum(1 for z in s.P[i].board if z.k == "k50_kurokami")
    if not n:
        return
    for _ in range(n):
        if s.over:
            return
        t = s.target(i, lambda u: u.x.get("lockuntil", -1) < s.turn)
        if t is None:
            return
        lock_until_my_turn(s, i, t)
        s.ev(f"　好詠音愛 クロカミ：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k50_kurokami", "好詠音愛 クロカミ", 3, "W", power=2000, jd=True, races=("magic", "mermaid"),
    pri=5, roles="acc dis",
    spellwatch=sw_kurokami, spcostaura=sa_kurokami,
    text="ジャストダイバー（出た時、次の自分のターンのはじめまで、相手に選ばれず攻撃されない）。"
         "自分の呪文を唱えるコストを1少なくする（0以下にはならない）。"
         "自分が呪文を唱えた時、相手のクリーチャーを1体選ぶ。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない",
    status="full", source=SRC["k50_kurokami"])


# ================================================================ 6 「無月」の頂 ＄スザーク＄
_gate_suzark = _mugetsu_gate("k50_suzark", 6)


def tp_suzark(s, i):
    """無月の門・絶：各ターンの終わりに、魔導具と墓地の魔導具カードを合計6つ選び、その上に召喚してもよい"""
    _gate_suzark(s, i)


def _suzark_hit(s, i, u):
    """相手のクリーチャーを1体選んで破壊し、相手の手札を1枚見ないで選び、捨てさせる"""
    t = s.target(i)
    if t is not None:
        s.ev(f"　＄スザーク＄：{t.c.name} を破壊")
        destroy(s, i, t)
    o = s.P[1 - i]
    if o.hand and not s.over:
        k = o.hand[s.rng.randrange(len(o.hand))]
        s.ev("　＄スザーク＄：相手の手札を1枚見ないで選んで捨てさせる")
        s.discard(1 - i, k, by_opp=True)


def e_suzark(s, i, u):
    if u.x.get("summoned"):                      # 「召喚によって出た時」だけ
        _suzark_hit(s, i, u)


def at_suzark(s, i, u):
    _suzark_hit(s, i, u)


def _suzark_grave(s, j):
    """相手（j）の墓地にカードが置かれた：＄スザーク＄の持ち主は1枚引いてもよい"""
    i = 1 - j
    for _ in range(sum(1 for z in s.P[i].board if z.k == "k50_suzark")):
        if s.over:
            return
        s.draw(i, 1)


def lw_suzark(s, j, u, dest, destroy_):
    """相手のカードが墓地に置かれた時（バトルゾーンから）"""
    if dest != "grave" or not s.has(1 - j, "k50_suzark"):
        return
    _suzark_grave(s, j)


def dw_suzark(s, j, k):
    """相手が手札を捨てた時"""
    if not s.has(1 - j, "k50_suzark"):
        return
    _suzark_grave(s, j)


def sw_suzark(s, j, k):
    """相手が呪文を唱えた時（唱えた後に墓地に置かれるぶん。ツインパクトの呪文側も墓地に行く）"""
    if k in E.NOGRAVE or not s.has(1 - j, "k50_suzark"):
        return
    _suzark_grave(s, j)


def so_suzark(s, j, k, up, dest):
    """相手のシールドが墓地に置かれた時"""
    if dest != "grave" or not s.has(1 - j, "k50_suzark"):
        return
    _suzark_grave(s, j)


add("k50_suzark", "「無月」の頂 ＄スザーク＄", 10, "D", power=15000, brk=3,
    races=("dorusuzaku", "mafigang", "zenith"), pri=13, roles="fin rem dis atk draw",
    enter=e_suzark, attack=at_suzark, tendp=tp_suzark,
    leavewatch=lw_suzark, discardwatch=dw_suzark, spellwatch=sw_suzark, shieldout=so_suzark,
    text="無月の門・絶：各ターンの終わりに、自分の、魔導具と墓地にある魔導具カードを合計6つ選び、"
         "その上にこのクリーチャーを、自分の手札または墓地からコストを支払わずに召喚してもよい。"
         "T・ブレイカー。"
         "このクリーチャーが召喚によって出た時または攻撃する時、相手のクリーチャーを1体選んで破壊し、"
         "相手の手札を1枚見ないで選び、捨てさせる。"
         "相手の墓地にどこからでもカードが置かれた時、カードを1枚引いてもよい",
    note="2024年3月11日から殿堂入り（デッキに1枚まで）。"
         "「相手の墓地にどこからでもカードが置かれた時」は、エンジンに「墓地に置かれた時」の差し込み口が"
         "無いので、拾える4つの道（バトルゾーンから墓地へ・手札から捨てる・呪文を唱えた後・"
         "シールドから墓地へ）だけで誘発させている。**山札から墓地（マナ破壊・山札破壊）とマナゾーンから"
         "墓地の分は引けない**。無月の門・絶の6つは、墓地の魔導具のうち重要度の低いものから使い、"
         "足りない分だけバトルゾーンの魔導具を下に置く",
    status="partial", source=SRC["k50_suzark"])


# ================================================================ 7 凶鬼98号 ガシャゴン／堕呪 ブラッドゥ
SLAYER.add("k50_gashagon")


def at_gashagon(s, i, u):
    """攻撃した時、自分の手札を1枚捨てる"""
    discard_choice(s, i)


def bd_gashagon(s, i, b, au):
    """ブロックした時、自分の手札を1枚捨てる"""
    discard_choice(s, i)


def sp_bladdu(s, i):
    """プレイヤーを1人選ぶ。そのプレイヤーは、自身の墓地を山札に加えてシャッフルする。カードを1枚引く"""
    p = s.P[i]
    # 山札が尽きかけていれば自分を選んで山札を作り直し、ふだんは相手を選んで墓地の資源を流す
    j = i if (len(p.deck) <= 5 and p.grave) else 1 - i
    q = s.P[j]
    if q.grave:
        q.deck.extend(q.grave)
        q.grave = []
        s.rng.shuffle(q.deck)
        s.ev(f"　堕呪 ブラッドゥ：{'自分' if j == i else '相手'}の墓地を山札に加えてシャッフル")
    s.draw(i, 1)


add("k50_gashagon", "凶鬼98号 ガシャゴン／堕呪 ブラッドゥ", 3, "D", power=5000, blocker=True,
    races=("mafigang", "madogu"), twin=(2, "W", False), pri=5, roles="blk rem dis draw",
    attack=at_gashagon, blockdone=bd_gashagon, spell=sp_bladdu,
    text="クリーチャー側《凶鬼98号 ガシャゴン》（闇3・マフィ・ギャング／魔導具・パワー5000）："
         "ブロッカー。スレイヤー（バトルした相手のクリーチャーを破壊する）。"
         "このクリーチャーが攻撃またはブロックした時、自分の手札を1枚捨てる"
         "（手札のうち重要度のいちばん低い札）。"
         "呪文側《堕呪 ブラッドゥ》（水2・魔導具）：プレイヤーを1人選ぶ。"
         "そのプレイヤーは、自身の墓地を山札に加えてシャッフルする。カードを1枚引く"
         "（自分の山札が5枚以下なら自分、ふだんは相手を選ぶ）",
    source=SRC["k50_gashagon"])


# ================================================================ 8 ガル・ラガンザーク
_gate_garlagan = _mugetsu_gate("k50_garlagan", 4)


def ew_garlagan(s, i, u):
    """夢幻無月の門：自分の魔導具クリーチャーが出た時"""
    if u.c.kind != "C" or not _madogu(u.c):
        return
    _gate_garlagan(s, i)


def sw_garlagan(s, i, k):
    """夢幻無月の門：自分の魔導具呪文を唱えた時"""
    if not _madogu(BY_KEY[k]):
        return
    _gate_garlagan(s, i)


def tl_garlagan(s, by, u):
    """このクリーチャーは、呪文によって相手に選ばれない（s.spc＝いま唱えている呪文のコスト）"""
    return u.k == "k50_garlagan" and s.spc is not None


def fx_garlagan(s, j, u, i, k, src, summon, res):
    """相手のターン中に相手のクリーチャーが召喚以外の方法で出る時、かわりにそのクリーチャーを墓地に置く"""
    if i == j or summon or res != "ok" or s.tp != i:
        return res
    return "grave"


add("k50_garlagan", "ガル・ラガンザーク", 8, "WD", power=9000, brk=2, blocker=True,
    races=("dorusuzaku", "mafigang"), pri=11, roles="blk dis fin",
    enterwatch=ew_garlagan, spellwatch=sw_garlagan, tgtlock=tl_garlagan, fatex=fx_garlagan,
    text="夢幻無月の門：自分の魔導具クリーチャーが出た時または自分の魔導具呪文を唱えた時、自分の、"
         "魔導具と墓地にある魔導具カードを合計4つ選び、その上にこのクリーチャーを、"
         "自分の手札または墓地からコストを支払わずに召喚してもよい。"
         "ブロッカー。W・ブレイカー。このクリーチャーは、呪文によって相手に選ばれない。"
         "相手のターン中に相手のクリーチャーが召喚以外の方法で出る時、かわりにそのクリーチャーを墓地に置く",
    note="2023年3月20日から殿堂入り（デッキに1枚まで）。"
         "「魔導具呪文」は、このシミュレーターではツインパクトの両面の種族が1枚にまとまっているので、"
         "「種族に魔導具を持つ呪文（ツインパクトの呪文側を含む）」で判定している",
    source=SRC["k50_garlagan"])


# ================================================================ 9 卍月 ガ・リュザーク 卍／「すべて見えているぞ！」
_gate_garyuzaku = _mugetsu_gate("k50_garyuzaku", 6)


def tp_garyuzaku(s, i):
    """無月の門・絶：各ターンの終わりに、魔導具と墓地の魔導具カードを合計6つ選び、その上に召喚してもよい"""
    _gate_garyuzaku(s, i)


def ts_garyuzaku(s, i):
    """相手のターンのはじめに、相手は自身のマナゾーンにあるカードを3枚までしかアンタップできない"""
    if not s.has(1 - i, "k50_garyuzaku"):
        return
    p = s.P[i]
    n = max(0, len(p.mana) - 3)
    if p.mused < n:
        p.mused = n
        s.ev("　卍月 ガ・リュザーク 卍：相手はマナを3枚までしかアンタップできない")


# ---- 呪文側「すべて見えているぞ！」：相手は各ターン1度までしか攻撃もブロックもできない ----
def _acted(s, j):
    """このターン、プレイヤー j がクリーチャーで攻撃かブロックをした回数"""
    v = s.P[j].x.get("k50_act")
    return v[1] if v is not None and v[0] == s.turn else 0


def _act_add(s, j):
    s.P[j].x["k50_act"] = (s.turn, _acted(s, j) + 1)


def aw_mieteru(s, i, u):
    """攻撃を宣言した：回数を数える（「すべて見えているぞ！」の判定用）"""
    _act_add(s, i)


def bw_mieteru(s, i, au, b):
    """ブロックされた：ブロックした側の回数を数える"""
    _act_add(s, 1 - i)


def _mie_on(s, j):
    """プレイヤー j が「すべて見えているぞ！」で縛られているか（唱えた側の記録を見る）"""
    return s.P[1 - j].x.get("k50_mie", -1) >= s.turn


def al_mieteru(s, i, u):
    return _mie_on(s, i) and _acted(s, i) >= 1


def bl_mieteru(s, u):
    j = owner_of(s, u)
    return _mie_on(s, j) and _acted(s, j) >= 1


def sp_mieteru(s, i):
    """次の自分のターンのはじめまで、相手は各ターン1度までしか、クリーチャーで攻撃もブロックもできない"""
    p = s.P[i]
    until = s.turn + (1 if s.tp == i else 0)
    if p.x.get("k50_mie", -1) < until:
        p.x["k50_mie"] = until
    s.ev("　すべて見えているぞ！：次の自分のターンのはじめまで、"
         "相手は各ターン1度までしか攻撃もブロックもできない")


add("k50_garyuzaku", "卍月 ガ・リュザーク 卍／「すべて見えているぞ！」", 9, "D", power=11000, brk=2,
    races=("masterdorusuzaku", "dorusuzaku", "mafigang"), twin=(5, "W", True),
    pri=12, roles="fin dis atk trg",
    tendp=tp_garyuzaku, turnstart=ts_garyuzaku, spell=sp_mieteru,
    atkwatch=aw_mieteru, blockwatch=bw_mieteru, atklock=al_mieteru, blocklock=bl_mieteru,
    text="クリーチャー側《卍月 ガ・リュザーク 卍》（闇9・マスター・ドルスザク／マフィ・ギャング・"
         "パワー11000）：無月の門・絶：各ターンの終わりに、自分の、魔導具と墓地にある魔導具カードを"
         "合計6つ選び、その上にこのクリーチャーを、自分の手札または墓地からコストを支払わずに"
         "召喚してもよい。相手のターンのはじめに、相手は自身のマナゾーンにあるカードを"
         "3枚までしかアンタップできない。W・ブレイカー。"
         "呪文側《「すべて見えているぞ！」》（水5・S・トリガー）："
         "次の自分のターンのはじめまで、相手は各ターン1度までしか、クリーチャーで攻撃もブロックもできない",
    note="「各ターン1度までしか攻撃もブロックもできない」は、攻撃とブロックを合わせて1回までと読んで"
         "実装した（攻撃1回とブロック1回で別枠ではない）",
    source=SRC["k50_garyuzaku"])


# ================================================================ 10 頂上混成 ガリュディアス・モモミーズ'22
def cx_momomies(s, i, av):
    """自分の墓地にクリーチャーではないカードが4枚以上あれば、召喚コストを90少なくする"""
    n = sum(1 for k in s.P[i].grave if BY_KEY[k].kind != "C")
    return 9 if n >= 4 else 99


def _spell_civ(k):
    """いま唱えようとしている呪文の文明。ツインパクトは呪文側の文明を返す"""
    c = BY_KEY[k]
    if c.kind != "S" and c.twin:
        return c.twin[1]
    return c.civ


def sl_momomies(s, i, cost, k=None):
    """相手は光ではない呪文を唱えられない"""
    if k is None:
        return False                         # 呪文が分からない時は止めない
    if not s.has(1 - i, "k50_momomies"):
        return False
    return "L" not in _spell_civ(k)


def te_momomies(s, i, u):
    """自分のターンの終わりに、クリーチャーを1体、自分の手札から出してもよい"""
    _put_from_hand(s, i)


add("k50_momomies", "頂上混成 ガリュディアス・モモミーズ'22", 99, "LWF", power=99000, brk=3, sa=True,
    races=("dispector", "jokersdragon", "dorusuzaku"), pri=13, roles="fin atk dis shd",
    costx=cx_momomies, enter=exlife_enter, leaverep=exlife_rep, spelllock=sl_momomies, tend=te_momomies,
    text="自分の墓地にクリーチャーではないカードが4枚以上あれば、このクリーチャーの召喚コストを"
         "90少なくする。EXライフ（出す時、自分の山札の上から1枚をシールド化する。離れる時、"
         "かわりにそのシールドを墓地に置く）。スピードアタッカー。T・ブレイカー。"
         "相手は光ではない呪文を唱えられない。"
         "自分のターンの終わりに、クリーチャーを1体、自分の手札から出してもよい"
         "（手札のうち重要度のいちばん高いクリーチャー）",
    note="envtest の effect_smoke は墓地がクリーチャーだけの場面なのでコストが99のまま＝0回になるが、"
         "実際の対戦（game_smoke）では墓地に呪文がたまってコスト9で召喚されている",
    source=SRC["k50_momomies"])


# ================================================================ 11 堕呪 ギャプドゥ
def sp_gyapudu(s, i):
    """カードを1枚引く。S−次の相手のターンのはじめまで、相手のクリーチャーは攻撃もブロックもできない"""
    s.draw(i, 1)
    if not _sst_used(s, i, "k50_gyapudu"):
        return
    # 「次の**相手の**ターンのはじめまで」なので、相手から見た lock_until_my_turn と同じ長さ
    until = s.turn + (0 if s.tp == i else 1)
    n = 0
    for z in s.P[1 - i].board:
        if z.c.kind == "C" and z.x.get("lockuntil", -1) < until:
            z.x["lockuntil"] = until
            n += 1
    if n:
        s.ev(f"　S能力：相手のクリーチャー{n}体は次の相手のターンのはじめまで攻撃もブロックもできない")


add("k50_gyapudu", "堕呪 ギャプドゥ", 2, "W", kind="S", trig=True, races=("madogu",),
    pri=4, roles="trg draw dis",
    spell=sp_gyapudu, shieldcast=_sst_cast("k50_gyapudu"),
    text="スーパー・S・トリガー（この呪文を自分のシールドゾーンから手札に加える時、"
         "コストを支払わずにすぐ唱えてもよい。その時、自分のシールドが1つもなければ、"
         "この呪文にS能力を与える）。カードを1枚引く。"
         "S−次の相手のターンのはじめまで、相手のクリーチャーは攻撃もブロックもできない",
    source=SRC["k50_gyapudu"])


# ================================================================ 12 堕呪 ウキドゥ
def sp_ukidu(s, i):
    """シールドを1つ見る。それを持ち主の墓地に置いてもよい。
    そうしたら、そのプレイヤーは自身の山札の上から1枚目をシールド化する。カードを1枚引く"""
    p, o = s.P[i], s.P[1 - i]
    tgt = None
    for j, (k, _up) in enumerate(p.sh):          # 自分の魔導具の盾があれば墓地へ（無月の門の数を増やす）
        if _madogu(BY_KEY[k]):
            tgt = (i, j)
            break
    if tgt is None and o.sh:                     # なければ相手の盾のうち重要度のいちばん高いもの
        j = max(range(len(o.sh)), key=lambda x: E.PRI[o.sh[x][0]])
        tgt = (1 - i, j)
    if tgt is not None:
        jo, j = tgt
        r = s.take_shield(jo, j, "grave")
        if r is not None:
            s.ev(f"　堕呪 ウキドゥ：{'自分' if jo == i else '相手'}のシールド1つを墓地に置いて置き直す")
            s.add_shield(jo)
    s.draw(i, 1)


add("k50_ukidu", "堕呪 ウキドゥ", 2, "W", kind="S", races=("madogu",), pri=3, roles="draw shd",
    spell=sp_ukidu,
    text="シールドを1つ見る。それを持ち主の墓地に置いてもよい。そうしたら、そのプレイヤーは"
         "自身の山札の上から1枚目をシールド化する。カードを1枚引く"
         "（自分の盾に魔導具があればそれを墓地へ。なければ相手の盾のうち重要度のいちばん高いものを墓地へ）",
    source=SRC["k50_ukidu"])


# ================================================================ 13 月下旋壊 ド・リュミーズ
def sp_dorumiis(s, i):
    """カードを3枚引く"""
    s.draw(i, 3)


def _dorumiis_ready(s, i):
    """別のコストを払えるか：マナが4枚以上でそのうち1枚が魔導具、手札に魔導具2枚"""
    p = s.P[i]
    if len(p.mana) < 4 or not any(_madogu(BY_KEY[k]) for k in p.mana):
        return False
    return sum(1 for k in p.hand if _madogu(BY_KEY[k])) >= 2


def fa_dorumiis(s, i, av, cv):
    p = s.P[i]
    if "k50_dorumiis" not in p.hand or not s.spell_ok(i, 5):
        return []
    if not _dorumiis_ready(s, i):
        return []
    return [("x:k50_dorumiis",)]


def ap_dorumiis(s, a):
    i = s.tp
    p = s.P[i]
    if "k50_dorumiis" not in p.hand or not _dorumiis_ready(s, i):
        return
    p.hand.remove("k50_dorumiis")
    for _ in range(2):
        cands = [k for k in p.hand if _madogu(BY_KEY[k])]
        if not cands:
            break
        s.discard(i, min(cands, key=E.PRI.get))
    s.ev("呪文：月下旋壊 ド・リュミーズ（魔導具2枚を手札から捨てて、コストを支払わずに）")
    s.cast(i, "k50_dorumiis")


add("k50_dorumiis", "月下旋壊 ド・リュミーズ", 5, "W", kind="S", races=("dorusuzaku",),
    pri=6, roles="draw",
    spell=sp_dorumiis,
    freeacts=fa_dorumiis, actapply={"x:k50_dorumiis": ap_dorumiis},
    text="自分のマナゾーンにカードが4枚以上あり、そのうち少なくとも1枚が魔導具なら、"
         "コストを支払うかわりに魔導具を2枚自分の手札から捨てて、この呪文を唱えてもよい。"
         "カードを3枚引く（捨てるのは手札の魔導具のうち重要度の低い2枚）",
    note="2022年8月15日から殿堂入り（デッキに1枚まで）。この呪文は種族ドルスザクで魔導具ではないので、"
         "自分自身は無月の門の数には入らない",
    source=SRC["k50_dorumiis"])


# ================================================================ 14 ストリーミング・シェイパー
def sp_shaper(s, i):
    """自分の山札の上から4枚をすべてのプレイヤーに見せる。
    その中の水のカードをすべて自分の手札に加え、それ以外のカードを自分の墓地に置く"""
    p = s.P[i]
    n = min(4, max(0, len(p.deck) - 1))
    got = 0
    for _ in range(n):
        k = p.deck.pop()
        if "W" in E.MCIV[k]:
            p.hand.append(k)
            got += 1
        else:
            s.grave_put(i, k)
    s.ev(f"　ストリーミング・シェイパー：山札の上{n}枚のうち水のカード{got}枚を手札に、残りを墓地に")


add("k50_shaper", "ストリーミング・シェイパー", 3, "W", kind="S", pri=4, roles="draw",
    spell=sp_shaper,
    text="自分の山札の上から4枚をすべてのプレイヤーに見せる。その中の水のカードをすべて自分の手札に加え、"
         "それ以外のカードを自分の墓地に置く",
    note="2005年3月15日から殿堂入り（デッキに1枚まで）。"
         "山札が尽きて即負けしないよう、ほかの山札を削る効果（mill・dig）と同じく山札は1枚残す",
    source=SRC["k50_shaper"])


# ================================================================ 15 オリオティス・ジャッジ
def sp_oriotis(s, i):
    """各プレイヤーは、自身のマナゾーンにあるカードの枚数以上のコストを持つクリーチャーをすべて、
    好きな順序で自身の山札の下に置く"""
    for j in (1 - i, i):
        q = s.P[j]
        n = len(q.mana)
        for u in [z for z in q.board if z.c.kind == "C" and z.c.cost >= n]:
            if s.over:
                return
            if u in q.board:
                s.ev(f"　オリオティス・ジャッジ：{u.c.name} を山札の下に置く")
                s.leave(j, u, "deck", by_opp=(j != i))


add("k50_oriotis", "オリオティス・ジャッジ", 3, "L", kind="S", trig=True, pri=5, roles="trg rem",
    spell=sp_oriotis,
    text="S・トリガー。各プレイヤーは、自身のマナゾーンにあるカードの枚数以上のコストを持つ"
         "クリーチャーをすべて、好きな順序で自身の山札の下に置く",
    source=SRC["k50_oriotis"])
