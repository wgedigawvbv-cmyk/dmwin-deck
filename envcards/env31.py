"""担当31：DM26-RP3（逆札篇 第3弾 勝敵！逆転おこせ鬼の∞ディスペクター!!）の未実装カード15枚

  出典：dmwiki.net の各カードページ（通常ページ `https://dmwiki.net/《カード名》` と
        生の wiki ソース `?plugin=template&refer=《カード名》`）を、カードごとに**別の質問で2回ずつ**読み、
        コスト・文明・種類・種族・パワー・ブレイク数・能力本文がどちらでも一致することを確かめた。
        数値が片方の読みで切れていた3枚（バイギャラドスツ・アイングダン・ドラマチック息子）は
        3回目の質問で確かめ直した。15枚いずれもハイパーモード欄（`BGCOLOR(#cde):|c|`）は無い。

  内訳（番号は DM26-RP3 の通し番号）
    ・2/77  七王を統べる者 魔王ザダン（闇13・墓地が7枚以上なら6マナ＆墓地から召喚）
    ・3/77  ドラマチック息子（火4・J・O・E 2 と「山札の上から召喚」を配るジョーカーズ）
    ・4/77  ミノガミ＆オウ禍武斗／T.2.D.（自然9/4・ツインパクト）
    ・5/77〜10/77「◯◯逆夢 ◯◯」6枚（EXライフ持ちのディスペクター）
    ・11/77 黎悪銃と邪煉哀の決断（光闇自然9・「次の中から2回選ぶ」）
    ・12/77 激アツポンの助（無色1）／13/77 にやにYAH（光6）
    ・14/77 ノヴァルチャ・ハレイズ（光4）／15/77 裏魔導書グリモア-I章（水4）
    ・16/77 ゲラッチョ重役／「ミーのチョーおすすめゲラ！」（闇6/3・ツインパクト）

  この弾の新しい（このシミュレーターに無かった）仕組みと、その書き方
    ・**スーパー・S・トリガー**（14/77・15/77）：S・トリガーと同じに唱えられ、
      「その時自分のシールドが1つもなければ」追加で「S-」の能力も使う。
      `shieldcast=`（`fn(s, i, k, nsh)`、nsh＝その時のシールドの枚数）で唱え、
      nsh==0 なら S 能力も使う（`SUPER_S` にも登録して魔王ザダンから使えるようにした）。
    ・**キズナ／KZ能力**（5/77）：出た時、自分のクリーチャーのKZ能力を1つ使う。
      モジュール内の `KZ` に「key → KZ能力」を登録し、場のクリーチャーの中から重要度のいちばん高いものを使う。
    ・**Jビッグ1**（13/77）：自分の他のジョーカーズの「出た時」の能力を1つ使う。
      env19 の `use_cip` と同じ形（場にいるそのクリーチャーを渡して `ENTER` を呼ぶ・入れ子は2回まで）。
    ・**J・O・E 2**（3/77）：コスト-2で召喚し、ターンの終わりに山札の下へ置いて1枚引く。
      「少なくして召喚してもよい」という選択なので、`costaura` で常に安くするのではなく
      `freeacts=`／`actapply=` で「J・O・E で召喚する手」を別に足した（普通のコストの手も残る）。
    ・**W・シンパシー**（6/77）：自分のシールドゾーンの表向きのカード1枚につきコスト-2。
      自分の `costx=` と、手札のクリーチャー全部に配る `costaura=` の2つで書いた。
    ・**B・A・D 2**（8/77）：払えない時だけコスト-2にし、そのターンの終わりに自分を破壊する。
    ・**スーパーガードマン**（10/77）：`battleswap=`（BATTLESWAP）で書いた。
      ブロックで起きたバトルも効果で起きたバトルも引き受ける。

  調べ直して意外だった点
    ・「◯◯逆夢 ◯◯」は6枚サイクルだが、**共通なのは EXライフ だけ**で中身はまるで違う。
      リリオクパングだけが「キズナ／KZ能力」、サヴェスヴァークだけが「W・シンパシー」、
      スコラッシュだけが「B・A・D 2」、アイングダンだけが「スーパーガードマン」を持つ。
      ブレイク数も W（10500/8000/11000/11000）と T（12000/12000）に分かれ、
      コストも 8・9・7・11・7・8 とそろっていない。サイクルだと思って流用すると全部間違う。
    ・《歓扉逆夢 バイギャラドスツ》は dmwiki のタグが「コスト4」になっているが、cardtable 行は (7)。
      www.dmwiki.net 側の同じページを開き直して (7)・パワー8000 を確認した（タグ側の誤り）。
    ・《激アツポンの助》は《ゾンビポンの助》（無色0・出たらすぐ破壊される）のリメイクのようで、
      コストも能力もまるで別物（無色1・パワー3000・G・ストライク・攻撃できない）。元カードとは無関係に実装した。
    ・《煌風逆夢 サヴェスヴァーク》は「カードが表向きで自分のシールドゾーンに置かれた時」に引くので、
      自分の攻撃時能力（表向きのシールド化）と噛み合って、攻撃するたびに1枚引く。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move, worst_hand
from envcards.env0 import EXLOST, SLAYER, exlife_enter, exlife_rep, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k31_zadan": W + "《七王を統べる者 魔王ザダン》",
    "k31_dramatic": W + "《ドラマチック息子》",
    "k31_minogami": W + "《ミノガミ＆オウ禍武斗／T.2.D.》",
    "k31_lilio": W + "《蒸光逆夢 リリオクパング》",
    "k31_saves": W + "《煌風逆夢 サヴェスヴァーク》",
    "k31_baigya": W + "《歓扉逆夢 バイギャラドスツ》",
    "k31_scorash": W + "《勝次逆夢 スコラッシュ“覇嵐”》",
    "k31_ashino": W + "《羅明逆夢 アシュノムカメイ》",
    "k31_aingdan": W + "《鉄禍逆夢 アイングダン・オウマ武斗ン》",
    "k31_ketsudan": W + "《黎悪銃と邪煉哀の決断》",
    "k31_gekiatsu": W + "《激アツポンの助》",
    "k31_niyani": W + "《にやにYAH》",
    "k31_nova": W + "《ノヴァルチャ・ハレイズ》",
    "k31_grimoire": W + "《裏魔導書グリモア-I章》",
    "k31_geracho": W + "《ゲラッチョ重役／「ミーのチョーおすすめゲラ！」》",
}

KZ = {}             # キズナ用：key -> KZ能力 fn(s, i, u)
SUPER_S = {}        # スーパー・S・トリガー：key -> S能力 fn(s, i)
ELEM = "CTX"        # エレメント（バトルゾーンにあるクリーチャー・タマシード・クロスギア）


# ================================================================ 共通の小道具
def _cast_free(s, i, k, dest="grave", twin=False):
    """コストを支払わずに呪文を唱える（カードは呼ぶ側がゾーンから取り除いておく）。
    唱えた後の行き先を dest で決める（"grave"／"deck"＝山札の下／None＝どこにも置かない）"""
    p = s.P[i]
    c = BY_KEY[k]
    cost = c.twin[0] if (twin and c.twin) else c.cost
    p.spl += 1
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    fn = E.SPELL.get(k)
    if fn is not None and not s.over:
        fn(s, i)
    s.spc = prev
    if dest == "grave":
        s.grave_put(i, k)
    elif dest == "deck":
        p.deck.insert(0, k)
    if not twin:
        s.noncre(i)


def _faceup(s, i):
    """自分のシールドゾーンにある表向きのカードの枚数"""
    return sum(1 for _k, up in s.P[i].sh if up)


def _elements(s, i):
    return [u for u in s.P[i].board if u.c.kind in ELEM]


def _worst_element(s, i):
    """自分のエレメントのうち、失うのがいちばん安いもの（クリーチャーは env0 の決まりで選ぶ）"""
    z = worst_own(s, i)
    if z is not None:
        return z
    els = _elements(s, i)
    return min(els, key=lambda x: E.PRI[x.k]) if els else None


def _plain_cre(k):
    """進化元を用意せずに出せるクリーチャーか"""
    c = BY_KEY[k]
    return c.kind == "C" and not (c.evo and not c.neo)


def _hand_or_mana(s, i, k):
    """山札から表向きにしたカードを手札かマナに置く（全デッキ共通の機械的な決まり）"""
    p = s.P[i]
    if E.PRI[k] >= 5 or len(p.mana) >= 7:
        p.hand.append(k)
        return "hand"
    s.add_mana(i, k, True, src="deck")
    return "mana"


def _enter_depth(s, i, key, cap=2):
    """入れ子の深さを数える（効果の中で同じ効果が何度も起きて止まらなくなるのを防ぐ）。
    使えるなら元の深さ（int）を返し、深すぎるなら None を返す"""
    p = s.P[i]
    d = p.x.get(key, 0)
    if d >= cap:
        return None
    p.x[key] = d + 1
    return d


def _undepth(s, i, key, d):
    s.P[i].x[key] = d


# ---------------------------------------------------------------- EXライフ（この弾の6枚ぶん）
# EXライフは env0 の共通の形（enter=exlife_enter / leaverep=exlife_rep）を使う。
# 「EXライフのシールドが離れた時」の誘発は、自分の leaverep に書いても
# LEAVEREP の先頭に登録された側が勝ってしまうので、envcards.env0 の EXLOST に登録する
# （exlife_rep がキーごとに必ず呼んでくれる）。


# ---------------------------------------------------------------- スーパー・S・トリガー
def _sst_cast(key, sfn):
    """スーパー・S・トリガー：このカードを自分のシールドゾーンから手札に加える時、
    コストを支払わずにすぐ唱える。その時自分のシールドが1つもなければ（nsh==0）、S能力も使う。

    SHIELDCAST なので、ブレイクでも効果でシールドから手札に加わる時でも通り、
    「手札に来たのに唱えず、同じターンに手札から唱えた」時にS能力が付くこともない。
    S能力を呪文のどこで使うかはカードごとに違う（《ドドンガ轟キャイエス》は破壊より先）ので、
    印を立てて `spell=` の中の `_sst_used` で見る形にしている"""
    def f(s, i, k, nsh):
        p = s.P[i]
        if k not in p.hand or not s.spell_ok(i, BY_KEY[k].cost):
            return False                       # 唱えられないなら、ふつうに手札に加えたままにする
        p.hand.remove(k)
        s.trig[i] += 1
        s.ev(f"　スーパー・S・トリガー：{BY_KEY[k].name}")
        if nsh <= 0:
            p.x["k31_sst"] = key               # シールドが1つもないのでS能力も使える
        try:
            s.cast(i, k)
        finally:
            if s.P[i].x.get("k31_sst") == key:
                s.P[i].x["k31_sst"] = None
        return True
    return f


def _sst_used(s, i, key):
    """この呪文が、自分のシールドが1つもない状態でシールドゾーンから唱えられたか（S能力を使えるか）"""
    p = s.P[i]
    if p.x.get("k31_sst") == key:
        p.x["k31_sst"] = None
        return True
    return False


def _super_s(key, sfn):
    """スーパー・S・トリガーを1か所で登録する。
    SUPER_S は《七王を統べる者 魔王ザダン》が「シールドがないものとしてS能力も使う」ために引く表
    （env32 も同じ表に登録している）"""
    SUPER_S[key] = sfn
    return _sst_cast(key, sfn)


# ---------------------------------------------------------------- スーパーガードマン
def super_guardman(key, cond=None):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーを
    タップしてバトルさせてもよい（BATTLESWAP。ブロックで起きたバトルも効果で起きたバトルも引き受ける。
    攻撃先を変えるわけではないので、攻撃されたクリーチャー自身はシールドをブレイクできる）。

    使うかどうかは共通の決まりで機械的に決める：バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける。
    （どのカードがガードマン系を持つかは engine3.GUARDMEN で引ける）"""
    E.GUARDMEN.add(key)

    def f(s, di, du, ai, au):
        if du is None:
            return None
        ap = s.power(ai, au, True)
        for z in s.P[di].board:
            if z.k != key or z.c.kind != "C" or z.tap or z is du:
                continue
            if cond is not None and not cond(s, di, z):
                continue
            if s.power(di, z) > ap or s.val(du) > s.val(z):
                s.tap_cre(di, z)
                return z
        return None
    return f


# ================================================================ 2/77 七王を統べる者 魔王ザダン
def cx_zadan(s, i, av):
    """自分の墓地にカードが7枚以上あれば召喚コストを7少なくする"""
    return 6 if len(s.P[i].grave) >= 7 else 13


def _zadan_pick(s, i):
    """自分の墓地にあるカードの枚数以下のコストを持つ闇のカードを1枚（重要度のいちばん高いもの）"""
    p = s.P[i]
    n = len(p.grave)
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if "D" not in E.MCIV[k] or c.cost > n or E.PRI[k] <= bv:
            continue
        if c.kind == "C":
            if not _plain_cre(k) or s.fate(i, k, "grave", False) != "ok":
                continue
        elif c.kind == "S":
            if not s.spell_ok(i, c.cost):
                continue
        elif c.kind == "G" and s.has(1 - i, "fujin"):
            continue
        best, bv = k, E.PRI[k]
    return best


def a_zadan(s, i, u):
    """出た時または攻撃する時、墓地の闇のカード1枚をコストを支払わずに使う。
    スーパー・S・トリガーを持つなら、シールドがないものとしてそのS能力も使う。
    呪文は唱えた後、墓地のかわりに山札の下へ"""
    d = _enter_depth(s, i, "k31_zad_d")
    if d is None:
        return
    try:
        _zadan_use(s, i)
    finally:
        _undepth(s, i, "k31_zad_d", d)


def _zadan_use(s, i):
    p = s.P[i]
    k = _zadan_pick(s, i)
    if k is None:
        return
    c = BY_KEY[k]
    if c.kind == "S":
        p.grave.remove(k)
        s.ev(f"　魔王ザダン：墓地の {c.name} をコストを支払わずに唱える（唱えた後は山札の下）")
        _cast_free(s, i, k, dest="deck")
    else:
        s.ev(f"　魔王ザダン：墓地の {c.name} をコストを支払わずに使う")
        if not free_play(s, i, k, "grave"):
            return
    fn = SUPER_S.get(k)
    if fn is not None and not s.over:
        s.ev("　　スーパー・S・トリガー：シールドがないものとしてS能力も使う")
        fn(s, i)


def fa_zadan(s, i, av, cv):
    """自分の墓地にカードが7枚以上あれば、墓地から召喚してもよい"""
    p = s.P[i]
    if "k31_zadan" not in p.grave or len(p.grave) < 7 or "D" not in cv:
        return []
    n = s.ccost(i, "k31_zadan", av)
    if n > av or s.fate(i, "k31_zadan", "grave", True) != "ok":
        return []
    return [("x:k31_zadan", n)]


def ap_zadan(s, a):
    i = s.tp
    p = s.P[i]
    if "k31_zadan" not in p.grave:
        return
    p.grave.remove("k31_zadan")
    p.mused += a[1]
    s.ev(f"墓地から召喚：七王を統べる者 魔王ザダン（{a[1]}マナ）")
    s.enter(i, "k31_zadan", "grave", True)


add("k31_zadan", "七王を統べる者 魔王ザダン", 13, "D", power=7000, brk=2, races=("mafigang",),
    pri=12, roles="fin atk rem draw",
    enter=a_zadan, attack=a_zadan, costx=cx_zadan, freeacts=fa_zadan, actapply={"x:k31_zadan": ap_zadan},
    text="スレイヤー。W・ブレイカー。自分の墓地にカードが7枚以上あれば、このクリーチャーの召喚コストを7少なくし、"
         "自分の墓地から召喚してもよい。このクリーチャーが出た時または攻撃する時、"
         "自分の墓地にあるカードの枚数以下のコストを持つ闇のカード1枚を、墓地からコストを支払わずに使ってもよい"
         "（重要度のいちばん高いものを選ぶ）。それがスーパー・S・トリガーを持つなら、"
         "自分のシールドが1つもないものとしてそのS能力も使う。こうして呪文を唱えたなら、"
         "唱えた後に墓地のかわりに山札の下に置く",
    source=SRC["k31_zadan"])
SLAYER.add("k31_zadan")


# ================================================================ 3/77 ドラマチック息子
def _jok_cre(k):
    c = BY_KEY[k]
    return c.kind == "C" and "jokers" in c.races and _plain_cre(k)


def fa_dramatic(s, i, av, cv):
    """自分のターン中、ジョーカーズ・クリーチャーを山札の上から召喚してもよい（コストは支払う）。
    手札と山札の上のジョーカーズ・クリーチャーは「J・O・E 2」（コスト-2・ターンの終わりに山札の下＋1枚引く）"""
    p = s.P[i]
    if not s.has(i, "k31_dramatic"):
        return []
    out = []
    cands = [("hand", k) for k in sorted(set(p.hand)) if _jok_cre(k)]
    if len(p.deck) > 1 and _jok_cre(p.deck[-1]):
        cands.append(("deck", p.deck[-1]))
    for src, k in cands:
        c = BY_KEY[k]
        base = s.ccost(i, k, av)
        for joe in (0, 1):
            if src == "hand" and not joe:
                continue                   # 手札からの普通の召喚は、もともと打てる手にある
            n = max(0, base - 2) if joe else base
            if n > av or (n > 0 and not cv.issuperset(c.civ)):
                continue
            if s.fate(i, k, src, True) != "ok":
                continue
            out.append(("x:k31_joe", k, src, n, joe))
    return out


def ap_joe(s, a):
    i = s.tp
    p = s.P[i]
    k, src, n, joe = a[1], a[2], a[3], a[4]
    if src == "hand":
        if k not in p.hand:
            return
        p.hand.remove(k)
    else:
        if len(p.deck) <= 1 or p.deck[-1] != k:
            return
        p.deck.pop()
    p.mused += n
    how = "J・O・E 2" if joe else "山札の上から召喚"
    s.ev(f"{how}：{BY_KEY[k].name}（{n}マナ）")
    u = s.enter(i, k, src, True)
    if u is not None and joe:
        u.x["k31_joe"] = s.turn


def te_joe(s, i, u):
    """J・O・E：こうして出したクリーチャーを、そのターンの終わりに山札の下に置いて1枚引く"""
    if u.x.get("k31_joe") != s.turn:
        return
    p = s.P[i]
    if u not in p.board:
        return
    p.board.remove(u)
    p.deck.insert(0, u.k)
    for k in u.under:
        p.deck.insert(0, k)
    s.ev(f"　J・O・E 2：{u.c.name} を山札の下に置いて1枚引く")
    s.draw(i)


add("k31_dramatic", "ドラマチック息子", 4, "F", power=5000, races=("jokers",), pri=7, roles="acc atk draw",
    freeacts=fa_dramatic, actapply={"x:k31_joe": ap_joe}, tendall=te_joe,
    saok=lambda s, i, u: "jokers" in u.c.races and s.has(i, "k31_dramatic"),
    text="自分のターン中、自分の山札の上から1枚をいつでも見てもよい。"
         "自分のターン中、ジョーカーズ・クリーチャーを自分の山札の上からコストを支払って召喚してもよい。"
         "自分の手札または山札の上にあるジョーカーズ・クリーチャーすべてに「J・O・E 2」を与える"
         "（コストを2少なくして召喚してもよく、こうして出したらそのターンの終わりに山札の下に置いて1枚引く）。"
         "自分のジョーカーズすべてに「スピードアタッカー」を与える",
    source=SRC["k31_dramatic"])


# ================================================================ 4/77 ミノガミ＆オウ禍武斗／T.2.D.
def _twin_in_mana(s, j):
    """プレイヤー j のマナゾーンにある、マナの枚数以下のコストのツインパクト呪文"""
    n = len(s.P[j].mana)
    return [k for k in sorted(set(s.P[j].mana)) if BY_KEY[k].twin and BY_KEY[k].twin[0] <= n]


def e_minogami(s, i, u):
    """出た時、各プレイヤーのマナゾーンから、そのプレイヤーのマナの枚数以下のコストのツインパクト呪文を
    それぞれ1枚まで選ぶ。自分がそれらをコストを支払わずに唱え、すべて唱えた後、
    その持ち主が自分の墓地からそのエレメント側を出す"""
    picks = []
    for j in (i, 1 - i):
        cands = _twin_in_mana(s, j)
        if cands:
            picks.append((j, max(cands, key=E.PRI.get)))
    if not picks:
        return
    d = _enter_depth(s, i, "k31_mino_d")
    if d is None:
        return
    try:
        _minogami_do(s, i, picks)
    finally:
        _undepth(s, i, "k31_mino_d", d)


def _minogami_do(s, i, picks):
    for j, k in picks:
        s.take_mana(j, k)
    for j, k in picks:
        if s.over:
            break
        s.ev(f"　ミノガミ＆オウ禍武斗：{BY_KEY[k].name}（呪文側）をコストを支払わずに唱える")
        _cast_free(s, i, k, dest=None, twin=True)
    for j, k in picks:
        c = BY_KEY[k]
        s.P[j].grave.append(k)
        if s.over or c.kind not in "CT":
            continue
        s.ev(f"　　{c.name} のエレメント側を持ち主のバトルゾーンに出す")
        if not free_play(s, j, k, "grave") and k not in s.P[j].grave:
            s.P[j].grave.append(k)


def sp_t2d(s, i):
    """自分の山札の上から2枚を表向きにする。その中のツインパクトカード1枚につき、
    それを手札に加えるかマナゾーンに置く。残りを山札の下に置く"""
    p = s.P[i]
    n = min(2, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    for k in top:
        if BY_KEY[k].twin:
            z = _hand_or_mana(s, i, k)
            s.ev(f"　T.2.D.：{BY_KEY[k].name} を{'手札' if z == 'hand' else 'マナ'}へ")
        else:
            p.deck.insert(0, k)


add("k31_minogami", "ミノガミ＆オウ禍武斗／T.2.D.", 9, "N", power=14000, brk=3, mach=True,
    races=("gransect",), twin=(4, "N", False), pri=12, roles="fin atk acc draw",
    enter=e_minogami, spell=sp_t2d,
    text="マッハファイター。T・ブレイカー。このクリーチャーが出た時、各プレイヤーのマナゾーンから、"
         "そのプレイヤーのマナゾーンの枚数以下のコストを持つツインパクト呪文をそれぞれ1枚まで選ぶ"
         "（重要度のいちばん高いもの）。自分がそれらを好きな順序でコストを支払わずに唱え、"
         "すべて唱えた後、その持ち主が自分の墓地からそのエレメント側を出す。"
         "呪文側 T.2.D.（自然4）：自分の山札の上から2枚を表向きにし、その中のツインパクトカードを"
         "1枚につき手札に加えるかマナゾーンに置く。残りを好きな順序で山札の下に置く",
    source=SRC["k31_minogami"])


# ================================================================ 5/77 蒸光逆夢 リリオクパング
def kz_lilio(s, i, u):
    """KZ-カードを1枚引く。その後、コスト6以下の呪文を1枚、自分の手札からコストを支払わずに唱えてもよい"""
    p = s.P[i]
    s.draw(i)
    best, bv, tw = None, -1, False
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "S" and c.cost <= 6 and s.spell_ok(i, c.cost) and E.PRI[k] > bv:
            best, bv, tw = k, E.PRI[k], False
        elif c.twin and c.twin[0] <= 6 and s.spell_ok(i, c.twin[0]) and E.PRI[k] > bv:
            best, bv, tw = k, E.PRI[k], True
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　KZ：{BY_KEY[best].name} をコストを支払わずに唱える")
    _cast_free(s, i, best, twin=tw)


KZ["k31_lilio"] = kz_lilio


def _kizuna(s, i, u):
    """キズナ：このクリーチャーが出た時、自分のクリーチャーのKZ能力を1つ使う"""
    cands = [z for z in s.P[i].board if z.c.kind == "C" and z.k in KZ]
    if not cands:
        return
    d = _enter_depth(s, i, "k31_kz_d")
    if d is None:
        return
    z = max(cands, key=lambda x: E.PRI[x.k])
    s.ev(f"　キズナ：{z.c.name} のKZ能力を使う")
    try:
        KZ[z.k](s, i, z)
    finally:
        _undepth(s, i, "k31_kz_d", d)


def e_lilio(s, i, u):
    exlife_enter(s, i, u)
    _kizuna(s, i, u)


def a_lilio(s, i, u):
    """攻撃する時、相手のクリーチャー1体を持ち主の手札に戻してもよい"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　蒸光逆夢 リリオクパング：{t.c.name} を持ち主の手札へ")
    move(s, i, t, "hand")


add("k31_lilio", "蒸光逆夢 リリオクパング", 8, "LW", power=10500, brk=2, blocker=True,
    races=("dispector", "metallica", "mutopia", "specials"), pri=11, roles="blk rem draw shd",
    enter=e_lilio, attack=a_lilio, leaverep=exlife_rep,
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をこのクリーチャーの下にシールドとして置く。"
         "離れる時はかわりにそのシールドを墓地に置く）。ブロッカー。W・ブレイカー。"
         "キズナ（このクリーチャーが出た時、自分のクリーチャーのKZ能力を1つ使う）。"
         "KZ-カードを1枚引く。その後、コスト6以下の呪文を1枚、自分の手札からコストを支払わずに唱えてもよい。"
         "このクリーチャーが攻撃する時、相手のクリーチャー1体を選び、持ち主の手札に戻してもよい",
    source=SRC["k31_lilio"])


# ================================================================ 6/77 煌風逆夢 サヴェスヴァーク
def cx_saves(s, i, av):
    """W・シンパシー：自分のシールドゾーンの表向きのカード1枚につきコスト-2"""
    return max(1, 9 - 2 * _faceup(s, i))


def ca_saves(s, i, k, n):
    """自分の手札にあるクリーチャーすべてに W・シンパシー を与える"""
    if BY_KEY[k].kind != "C" or not s.has(i, "k31_saves"):
        return n
    f = _faceup(s, i)
    return max(1, n - 2 * f) if f else n


def si_saves(s, i, k, up):
    """カードが表向きで自分のシールドゾーンに置かれた時、カードを1枚引いてもよい"""
    if not up or not s.has(i, "k31_saves"):
        return
    s.ev("　煌風逆夢 サヴェスヴァーク：表向きのシールドが置かれたので1枚引く")
    s.draw(i)


def a_saves(s, i, u):
    """攻撃する時、自分の山札の上から2枚を表向きにし、1枚を表向きでシールド化、もう1枚をマナゾーンに置く"""
    p = s.P[i]
    n = min(2, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    top.sort(key=E.PRI.get, reverse=True)
    k = top[0]
    s.ev(f"　煌風逆夢 サヴェスヴァーク：{BY_KEY[k].name} を表向きのシールドへ")
    if not s.add_shield(i, k, True):
        p.deck.insert(0, k)
    if len(top) > 1:
        s.add_mana(i, top[1], True, src="deck")
        s.ev(f"　　{BY_KEY[top[1]].name} をマナゾーンへ")


add("k31_saves", "煌風逆夢 サヴェスヴァーク", 9, "LN", power=12000, brk=3, mach=True,
    races=("dispector", "masterdragon", "metallica", "gransect"), pri=12, roles="fin atk acc shd draw",
    enter=exlife_enter, attack=a_saves, costx=cx_saves, costaura=ca_saves, shieldin=si_saves,
    leaverep=exlife_rep,
    text="W・シンパシー：自分のシールドゾーンにある表向きのカード（このカードのコストを、"
         "自分のシールドゾーンの表向きのカード1枚につき2少なくする。ただしコストは1より少なくならない）。"
         "EXライフ。マッハファイター。T・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札の上から2枚を表向きにする。"
         "その中から1枚を表向きでシールド化し、もう1枚をマナゾーンに置く。"
         "カードが表向きで自分のシールドゾーンに置かれた時、カードを1枚引いてもよい。"
         "自分の手札にあるクリーチャーすべてに「W・シンパシー：自分のシールドゾーンにある表向きのカード」を与える",
    source=SRC["k31_saves"])


# ================================================================ 7/77 歓扉逆夢 バイギャラドスツ
def _baigya_fx(s, i, u):
    """カードを1枚引き、相手のクリーチャー1体を持ち主の山札の下に置く"""
    s.draw(i)
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　歓扉逆夢 バイギャラドスツ：{t.c.name} を持ち主の山札の下へ")
    move(s, i, t, "deck")


def e_baigya(s, i, u):
    exlife_enter(s, i, u)
    _baigya_fx(s, i, u)


EXLOST["k31_baigya"] = _baigya_fx          # EXライフのシールドが離れた時にも同じ効果


def mp_baigya(s, by, cands):
    """相手がクリーチャーを選ぶなら、可能ならこのクリーチャーを選ぶ
    （MUSTPICK。条件で絞り終えた候補に対して呼ばれるので「可能なら」が正しく出る）"""
    for u in cands:
        if u.k == "k31_baigya":
            return u
    return None


add("k31_baigya", "歓扉逆夢 バイギャラドスツ", 7, "WD", power=8000, brk=2,
    races=("dispector", "trix", "jokers"), pri=11, roles="rem draw shd",
    enter=e_baigya, leaverep=exlife_rep, mustpick=mp_baigya,
    text="EXライフ。W・ブレイカー。このクリーチャーが出た時、またはこのクリーチャーの「EXライフ」シールドが離れた時、"
         "カードを1枚引き、相手のクリーチャー1体を選んで持ち主の山札の下に置く。"
         "相手がクリーチャーを選ぶなら、可能ならこのクリーチャーを選ぶ",
    source=SRC["k31_baigya"])


# ================================================================ 8/77 勝次逆夢 スコラッシュ“覇嵐”
def cx_scorash(s, i, av):
    """B・A・D 2：払えない時だけ召喚コストを2少なくする（そうしたらターンの終わりに破壊される）"""
    return 11 if 11 <= av else 9


def payx_scorash(s, i, k, n):
    p = s.P[i]
    if 11 > len(p.mana) - p.mused:        # 11マナ払えないので B・A・D 2 を使った
        p.x["k31_bad"] = s.turn


def e_scorash(s, i, u):
    exlife_enter(s, i, u)
    p = s.P[i]
    if p.x.get("k31_bad") == s.turn and u.x.get("summoned"):
        p.x["k31_bad"] = -1
        u.x["k31_bad"] = s.turn
        s.ev("　B・A・D 2：このターンの終わりにこのクリーチャーを破壊する")


def t_scorash(s, i, u):
    if u.x.get("k31_bad") == s.turn:
        u.x["k31_bad"] = -1
        s.ev("　B・A・D 2：勝次逆夢 スコラッシュ“覇嵐” を破壊する")
        s.leave(i, u, "grave", destroy=True)


def _scorash_ex(s, i, u):
    """EXライフシールドが離れた時、これがタップされていて追加ターン中でなければ、自分のターンを追加する。

    エンジンの追加ターン（`s.P[i].extra`）を使う。end_turn で追加ターンに入ると `s.turn` が2つ進むので、
    与えたターン番号を覚えておけば「いま追加ターン中か」を見分けられる"""
    p = s.P[i]
    if not u.tap or p.x.get("k31_extra") == s.turn:
        return
    p.x["k31_extra"] = s.turn + 2
    p.extra += 1
    s.ev("　勝次逆夢 スコラッシュ“覇嵐”：このターンの後に自分のターンを追加する")


EXLOST["k31_scorash"] = _scorash_ex       # EXライフのシールドが離れた時に誘発する


add("k31_scorash", "勝次逆夢 スコラッシュ“覇嵐”", 11, "WF", power=11000, brk=2, sa=True,
    races=("dispector", "dragonguild", "beatjockey", "mutopia"), pri=12, roles="fin atk shd",
    enter=e_scorash, costx=cx_scorash, payx=payx_scorash, tend=t_scorash, leaverep=exlife_rep,
    text="EXライフ。B・A・D 2（このクリーチャーの召喚コストを2少なくしてもよい。"
         "そうしたらこのターンの終わりにこのクリーチャーを破壊する。マナが足りない時だけ使う）。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーの「EXライフ」シールドが離れた時、これがタップされていて追加ターン中でなければ、"
         "このターンの後に自分のターンを追加する",
    source=SRC["k31_scorash"])


# ================================================================ 9/77 羅明逆夢 アシュノムカメイ
def lw_ashino(s, i, u, dest, destroy_):
    """このターンに破壊された自分のエレメントを覚えておく（この札を入れているデッキだけ）"""
    if not destroy_ or dest != "grave" or u.c.kind not in ELEM:
        return
    p = s.P[i]
    if not p.list or "k31_ashino" not in p.list:
        return
    if p.x.get("k31_dead_t") != s.turn:
        p.x["k31_dead_t"] = s.turn
        p.x["k31_dead"] = ()
    p.x["k31_dead"] = p.x["k31_dead"] + (u.k,)


def t_ashino(s, i, u):
    """自分のターンの終わりに、このターンに破壊された自分のエレメントをすべて墓地から出してもよい"""
    p = s.P[i]
    if p.x.get("k31_dead_t") != s.turn:
        return
    ks = p.x.get("k31_dead") or ()
    if not ks:
        return
    p.x["k31_dead"] = ()
    for k in ks:
        if s.over or k not in p.grave:
            continue
        c = BY_KEY[k]
        if c.kind == "C":
            if not _plain_cre(k) or s.fate(i, k, "grave", False) != "ok":
                continue
            p.grave.remove(k)
            s.ev(f"　羅明逆夢 アシュノムカメイ：墓地から {c.name} を出す")
            s.enter(i, k, "grave", False)
        elif c.kind == "T":
            p.grave.remove(k)
            s.ev(f"　羅明逆夢 アシュノムカメイ：墓地から {c.name} を出す")
            s.place_tama(i, k)


def e_ashino(s, i, u):
    """出た時、自分のシールドゾーンのカード1枚を山札の下に置いてもよい。そうしたらカードを2枚引く"""
    exlife_enter(s, i, u)
    p = s.P[i]
    if len(p.sh) < 2:
        return
    j = next((j for j in range(len(p.sh)) if not p.sh[j][1]), 0)
    s.take_shield(i, j, "deck")            # シールドゾーンの出口は s.take_shield 1か所
    s.ev("　羅明逆夢 アシュノムカメイ：自分のシールド1つを山札の下に置いて2枚引く")
    s.draw(i, 2)


add("k31_ashino", "羅明逆夢 アシュノムカメイ", 7, "DF", power=11000, brk=2, sa=True,
    races=("dispector", "demonio", "mafigang"), pri=11, roles="atk draw fin shd",
    enter=e_ashino, tend=t_ashino, leavewatch=lw_ashino, leaverep=exlife_rep,
    text="EXライフ。スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、自分のシールドゾーンにあるカードを1枚山札の下に置いてもよい"
         "（シールドが2つ以上ある時に、裏向きのものから置く）。そうしたら、カードを2枚引く。"
         "自分のターンの終わりに、このターンに破壊された自分のエレメントをすべて、自分の墓地から出してもよい",
    source=SRC["k31_ashino"])


# ================================================================ 10/77 鉄禍逆夢 アイングダン・オウマ武斗ン
def e_aingdan(s, i, u):
    """出た時、相手のクリーチャー1体を持ち主のマナゾーンに置いてもよい。
    そうしたら、その選んだクリーチャーの「出た時」の能力を自分が1つ使ってもよい"""
    exlife_enter(s, i, u)
    t = s.target(i)
    if t is None:
        return
    k = t.k
    s.ev(f"　鉄禍逆夢 アイングダン：{t.c.name} を持ち主のマナゾーンへ")
    if not move(s, i, t, "mana"):
        return
    fn = E.ENTER.get(k)
    p = s.P[i]
    d = p.x.get("k31_cip", 0)
    if fn is None or s.over or d >= 2:
        return
    p.x["k31_cip"] = d + 1
    z = E.U(k)
    z.sick = False
    s.ev(f"　　{BY_KEY[k].name} の「出た時」の能力を自分が使う")
    fn(s, i, z)
    s.P[i].x["k31_cip"] = d


def t_aingdan(s, i, u):
    """自分のターンの終わりに、自分の手札を1枚捨ててもよい。
    そうしたら次のターン中、相手はカードを1枚までしか実行できない"""
    k = worst_hand(s, i)
    if k is None:
        return
    s.discard(i, k)
    s.P[1 - i].x["k31_ainlock"] = s.turn + 1
    s.ev("　鉄禍逆夢 アイングダン：手札を1枚捨て、次のターン相手はカードを1枚までしか実行できない")


def _ainlocked(s, i):
    p = s.P[i]
    return s.tp == i and p.x.get("k31_ainlock") == s.turn and (p.ent + p.spl) >= 1


def ca_aingdan(s, i, k, n):
    return 99 if _ainlocked(s, i) else n


def sl_aingdan(s, i, cost):
    return _ainlocked(s, i)


add("k31_aingdan", "鉄禍逆夢 アイングダン・オウマ武斗ン", 8, "FN", power=12000, brk=3, sa=True,
    races=("dispector", "gransect", "jokers"), pri=12, roles="fin atk rem dis blk",
    enter=e_aingdan, tend=t_aingdan, leaverep=exlife_rep,
    battleswap=super_guardman("k31_aingdan"), costaura=ca_aingdan, spelllock=sl_aingdan,
    text="EXライフ。スピードアタッカー。T・ブレイカー。"
         "スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
         "バトルさせてもよい）。このクリーチャーが出た時、相手のクリーチャー1体を選び、"
         "持ち主のマナゾーンに置いてもよい。そうしたら、その選んだクリーチャーの"
         "「出た時」にトリガーする能力を、自分が1つ使ってもよい。"
         "自分のターンの終わりに、自分の手札を1枚捨ててもよい。"
         "そうしたら次のターン中、相手はカードを1枚までしか実行できない",
    note="「相手はカードを1枚までしか実行できない」は、クリーチャーの召喚（コストを99にする）と"
         "呪文（spelllock）だけを止めている。タマシード・G城・クロスギアの実行は止められない。"
         "また数え方は「そのターンに出たクリーチャー＋唱えた呪文」なので、効果で踏み倒した分も1枚として数える"
         "（「実行した枚数を制限する」差し込み口は、いまのエンジンにもまだ無い）",
    status="partial", source=SRC["k31_aingdan"])


# ================================================================ 11/77 黎悪銃と邪煉哀の決断
def _ketsu_mode1(s, i):
    """自分の山札の上から3枚を見て、1枚を手札に加え、残りをタップしてマナゾーンに置く"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best = max(top, key=E.PRI.get)
    top.remove(best)
    p.hand.append(best)
    s.ev(f"　決断：上3枚から {BY_KEY[best].name} を手札へ、残り{len(top)}枚をタップしてマナへ")
    for k in top:
        s.add_mana(i, k, True, src="deck")


def _ketsu_mode2_pick(s, i):
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > 9 or c.evo or E.PRI[k] <= bv:
            continue
        if s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    return best


def _ketsu_mode2(s, i):
    """コスト9以下の進化ではないクリーチャー1体を自分の手札から出す。このターンの終わりにそれを破壊する"""
    k = _ketsu_mode2_pick(s, i)
    if k is None:
        return
    s.P[i].hand.remove(k)
    s.ev(f"　決断：手札から {BY_KEY[k].name} を出す（このターンの終わりに破壊）")
    u = s.enter(i, k, "hand", False)
    if u is not None:
        u.x["k31_die"] = s.turn


def te_ketsudan(s, i, u):
    if u.x.get("k31_die") != s.turn:
        return
    u.x["k31_die"] = -1
    s.ev(f"　決断：{u.c.name} を破壊する")
    s.leave(i, u, "grave", destroy=True)


def _ketsu_mode3(s, i):
    """エレメントを2つまで選び、破壊する（相手の重要度の高いものから）"""
    for _ in range(2):
        t = s.target(i, kinds=ELEM)
        if t is None:
            return
        s.ev(f"　決断：{t.c.name} を破壊する")
        destroy(s, i, t)


def _ketsu_one(s, i):
    """3つのモードから1つ。効きめの大きいものを機械的に選ぶ（全デッキ共通の決まり）"""
    p = s.P[i]
    v3 = 0
    for t in sorted((u for u in s.P[1 - i].board if u.c.kind in ELEM and not u.jd),
                    key=s.val, reverse=True)[:2]:
        v3 += s.val(t)
    k2 = _ketsu_mode2_pick(s, i)
    v2 = E.PRI[k2] if k2 is not None else -1
    v1 = 5 if len(p.deck) > 3 else -1
    if v3 >= v2 and v3 >= v1 and v3 > 0:
        _ketsu_mode3(s, i)
    elif v2 >= v1 and v2 > 0:
        _ketsu_mode2(s, i)
    elif v1 > 0:
        _ketsu_mode1(s, i)


def sp_ketsudan(s, i):
    for _ in range(2):
        if s.over:
            return
        _ketsu_one(s, i)


def fa_ketsudan(s, i, av, cv):
    """自分のエレメントを2つ破壊し、[光/闇/自然(5)]支払ってこの呪文を唱えてもよい"""
    p = s.P[i]
    if "k31_ketsudan" not in p.hand or av < 5 or not cv.issuperset("LDN"):
        return []
    if not s.spell_ok(i, 9) or len(_elements(s, i)) < 2:
        return []
    return [("x:k31_ketsu5",)]


def ap_ketsu5(s, a):
    i = s.tp
    p = s.P[i]
    if "k31_ketsudan" not in p.hand or len(_elements(s, i)) < 2:
        return
    s.ev("呪文：黎悪銃と邪煉哀の決断（自分のエレメント2つを破壊して5マナ）")
    for _ in range(2):
        z = _worst_element(s, i)
        if z is None:
            break
        s.leave(i, z, "grave", destroy=True)
    if "k31_ketsudan" not in p.hand:
        return
    p.hand.remove("k31_ketsudan")
    p.mused += 5
    s.cast(i, "k31_ketsudan")


add("k31_ketsudan", "黎悪銃と邪煉哀の決断", 9, "LDN", kind="S", pri=9, roles="rem acc draw fin",
    spell=sp_ketsudan, freeacts=fa_ketsudan, actapply={"x:k31_ketsu5": ap_ketsu5}, tendall=te_ketsudan,
    text="自分のエレメントを2つ破壊し、[光/闇/自然(5)]支払ってこの呪文を唱えてもよい"
         "（失うのがいちばん安いエレメントから破壊する）。次の中から2回選ぶ。同じものを選んでもよい。"
         "▶自分の山札の上から3枚を見る。その中から1枚を手札に加え、残りをタップしてマナゾーンに置く。"
         "▶コスト9以下の、進化ではないクリーチャーを1体、自分の手札から出す。このターンの終わりに、それを破壊する。"
         "▶エレメントを2つまで選び、破壊する。"
         "どれを選ぶかは、取り除ける相手のエレメントの重要度・手札のクリーチャーの重要度・山札の残りで機械的に決める",
    source=SRC["k31_ketsudan"])


# ================================================================ 12/77 激アツポンの助
def si_gekiatsu(s, i, k, up):
    """カードが相手のシールドゾーンに置かれた時、自分はカードを1枚引いてもよい"""
    j = 1 - i
    if not s.has(j, "k31_gekiatsu"):
        return
    s.ev("　激アツポンの助：相手のシールドゾーンにカードが置かれたので1枚引く")
    s.draw(j)


def fa_gekiatsu(s, i, av, cv):
    """自分のジョーカーズ・カードを実行する時、自分のマナゾーンのカードを
    すべての文明を持つかのようにタップしてもよい（文明が足りなくても実行できる手を足す）"""
    p = s.P[i]
    if not s.has(i, "k31_gekiatsu"):
        return []
    out = []
    zen = s.has(i, "zen")
    fuj = s.has(1 - i, "fujin")
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if "jokers" not in c.races:
            continue
        if c.kind == "C":
            n = s.ccost(i, k, av)
            if 0 < n <= av and not cv.issuperset(c.civ) and s.fate(i, k, "hand", True) == "ok":
                if c.evo == "grave":
                    out.append(("x:k31_civ", k, 1))
                elif c.evo:
                    if c.neo:
                        out.append(("x:k31_civ", k, 0))
                    if s.evo_src(i, k) is not None:
                        out.append(("x:k31_civ", k, 1))
                else:
                    out.append(("x:k31_civ", k, 0))
        elif c.kind == "S":
            n = s.spcost(i, k)
            if 0 < n <= av and not cv.issuperset(c.civ) and s.spell_ok(i, c.cost):
                out.append(("x:k31_civ", k, 0))
        elif c.kind == "T":
            n = max(1, c.cost - 2) if zen else c.cost
            if n <= av and not cv.issuperset(c.civ) and p.ban != c.cost:
                out.append(("x:k31_civ", k, 0))
        elif c.kind == "G":
            if c.cost <= av and not cv.issuperset(c.civ) and p.ban != c.cost and not fuj:
                out.append(("x:k31_civ", k, 0))
        if c.twin:
            tc, tciv, _ = c.twin
            if tc <= av and not cv.issuperset(tciv) and s.spell_ok(i, tc):
                out.append(("x:k31_civs", k))
    return out


def ap_civ(s, a):
    i = s.tp
    if a[1] not in s.P[i].hand:
        return
    s.ev("　激アツポンの助：マナをすべての文明を持つかのようにタップする")
    s.play(i, a[1], a[2])


def ap_civs(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.hand:
        return
    p.mused += BY_KEY[k].twin[0]
    p.hand.remove(k)
    s.ev(f"　激アツポンの助：マナをすべての文明として {BY_KEY[k].name}（呪文側）")
    s.cast(i, k, True)


add("k31_gekiatsu", "激アツポンの助", 1, "", power=3000, noatk=True, gs=True, races=("jokers",),
    pri=4, roles="trg draw",
    shieldin=si_gekiatsu, freeacts=fa_gekiatsu,
    actapply={"x:k31_civ": ap_civ, "x:k31_civs": ap_civs},
    text="G・ストライク。このクリーチャーは攻撃できない。"
         "自分のジョーカーズ・カードを実行する時、自分のマナゾーンにあるカードを"
         "すべての文明を持つかのようにタップしてもよい。"
         "カードが相手のシールドゾーンに置かれた時、自分はカードを1枚引いてもよい",
    source=SRC["k31_gekiatsu"])


# ================================================================ 13/77 にやにYAH
def _jbig_cands(s, i, u):
    return [z for z in s.P[i].board
            if z is not u and z.c.kind == "C" and "jokers" in z.c.races and E.ENTER.get(z.k) is not None]


def _jbig(s, i, u):
    """Jビッグ1：自分の他のジョーカーズの、出た時にトリガーする能力を1つ使う"""
    cands = _jbig_cands(s, i, u)
    p = s.P[i]
    d = p.x.get("k31_jbig", 0)
    if not cands or d >= 2:
        return
    z = max(cands, key=lambda x: E.PRI[x.k])
    p.x["k31_jbig"] = d + 1
    s.ev(f"　Jビッグ1：{z.c.name} の「出た時」の能力を使う")
    E.ENTER[z.k](s, i, z)
    s.P[i].x["k31_jbig"] = d


def e_niyani(s, i, u):
    """出た時、次の中から1回選ぶ：▶相手のクリーチャーをすべてタップする ▶Jビッグ1する"""
    o = s.P[1 - i]
    un = [z for z in o.board if z.c.kind == "C" and not z.tap]
    if len(un) >= 2 or not _jbig_cands(s, i, u):
        if un:
            for z in un:
                s.tap_cre(1 - i, z)
            s.ev(f"　にやにYAH：相手のクリーチャーをすべてタップ（{len(un)}体）")
            return
    _jbig(s, i, u)


add("k31_niyani", "にやにYAH", 6, "L", power=3000, trig=True, races=("jokers",), pri=6, roles="trg dis",
    enter=e_niyani,
    text="S・トリガー。このクリーチャーが出た時、次の中から1回選ぶ。"
         "▶相手のクリーチャーをすべてタップする。"
         "▶Jビッグ1する（自分の他のジョーカーズの、Jビッグ1以外の、出た時にトリガーする能力を1つ使う）。"
         "相手にアンタップしているクリーチャーが2体以上いればタップを選び、そうでなければJビッグ1を選ぶ",
    source=SRC["k31_niyani"])


# ================================================================ 14/77 ノヴァルチャ・ハレイズ
def _nova_s(s, i):
    """S-自分の山札の上から2枚をシールド化してもよい"""
    s.ev("　S能力：自分の山札の上から2枚をシールド化")
    s.add_shield(i)
    s.add_shield(i)


def sp_nova(s, i):
    """カードを1枚引く。その後、コストの合計が4以下になるようにクリーチャーを好きな数、自分の手札から出す"""
    p = s.P[i]
    s.draw(i)
    left = 4
    for _ in range(6):
        best, bv = None, -1
        for k in sorted(set(p.hand)):
            c = BY_KEY[k]
            if c.kind != "C" or c.cost > left or not _plain_cre(k) or E.PRI[k] <= bv:
                continue
            if s.fate(i, k, "hand", False) == "ok":
                best, bv = k, E.PRI[k]
        if best is None:
            break
        p.hand.remove(best)
        left -= BY_KEY[best].cost
        s.ev(f"　ノヴァルチャ・ハレイズ：手札から {BY_KEY[best].name} を出す")
        s.enter(i, best, "hand", False)
        if s.over:
            return
    if _sst_used(s, i, "k31_nova"):
        _nova_s(s, i)


add("k31_nova", "ノヴァルチャ・ハレイズ", 4, "L", kind="S", trig=True, pri=6, roles="trg draw shd fin",
    spell=sp_nova, shieldcast=_super_s("k31_nova", _nova_s),
    text="スーパー・S・トリガー（このカードを自分のシールドゾーンから手札に加える時、"
         "コストを支払わずにすぐ唱えてもよい。その時自分のシールドが1つもなければ、このカードにS能力を与える）。"
         "カードを1枚引く。その後、コストの合計が4以下になるようにクリーチャーを好きな数、自分の手札から出す"
         "（重要度の高いものから）。S-自分の山札の上から2枚をシールド化してもよい",
    source=SRC["k31_nova"])


# ================================================================ 15/77 裏魔導書グリモア-I章
def _grimoire_s(s, i):
    """S-コスト9以下の呪文を1枚、いずれかのプレイヤーの墓地からコストを支払わずに唱える。
    唱えた後、墓地のかわりに持ち主の山札の下に置く"""
    best, bv, bj, btw = None, -1, None, False
    for j in (0, 1):
        for k in sorted(set(s.P[j].grave)):
            c = BY_KEY[k]
            if c.kind == "S":
                cost, tw = c.cost, False
            elif c.twin:
                cost, tw = c.twin[0], True
            else:
                continue
            if cost > 9 or not s.spell_ok(i, cost) or E.PRI[k] <= bv:
                continue
            best, bv, bj, btw = k, E.PRI[k], j, tw
    if best is None:
        return
    s.P[bj].grave.remove(best)
    whose = "自分" if bj == i else "相手"
    s.ev(f"　S能力：{whose}の墓地の {BY_KEY[best].name} をコストを支払わずに唱える")
    _cast_free(s, i, best, dest=None, twin=btw)
    s.P[bj].deck.insert(0, best)


def sp_grimoire(s, i):
    """カードを3枚引き、自分の手札を1枚捨てる"""
    s.draw(i, 3)
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)
    if _sst_used(s, i, "k31_grimoire"):
        _grimoire_s(s, i)


add("k31_grimoire", "裏魔導書グリモア-I章", 4, "W", kind="S", trig=True, pri=6, roles="trg draw",
    spell=sp_grimoire, shieldcast=_super_s("k31_grimoire", _grimoire_s),
    text="スーパー・S・トリガー（このカードを自分のシールドゾーンから手札に加える時、"
         "コストを支払わずにすぐ唱えてもよい。その時自分のシールドが1つもなければ、このカードにS能力を与える）。"
         "カードを3枚引き、自分の手札を1枚捨てる。"
         "S-コスト9以下の呪文を1枚、いずれかのプレイヤーの墓地からコストを支払わずに唱える"
         "（重要度のいちばん高いもの）。それを唱えた後、墓地のかわりに持ち主の山札の下に置く",
    source=SRC["k31_grimoire"])


# ================================================================ 16/77 ゲラッチョ重役／「ミーのチョーおすすめゲラ！」
def e_geracho(s, i, u):
    """出た時、相手のクリーチャーを1体選び、破壊する"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ゲラッチョ重役：{t.c.name} を破壊する")
    destroy(s, i, t)


def swap_geracho(s, i, u):
    """Jクライム8：攻撃する時、これと自分の墓地のコスト8以下のジョーカーズ・クリーチャー1体を入れ替えてもよい"""
    p = s.P[i]
    best, bv = None, E.PRI["k31_geracho"]
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind != "C" or "jokers" not in c.races or c.cost > 8 or not _plain_cre(k) or E.PRI[k] <= bv:
            continue
        if s.fate(i, k, "grave", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return None
    j = p.board.index(u)
    p.grave.remove(best)
    s.leave(i, u, "grave", destroy=True)
    nu = E.U(best)
    nu.tap = True
    nu.sick = False
    p.board.insert(min(j, len(p.board)), nu)
    p.ent += 1
    s.ev(f"　Jクライム8：{u.c.name} と墓地の {nu.c.name} を入れ替える")
    fn = E.ENTER.get(best)
    if fn is not None:
        fn(s, i, nu)
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, i, nu)
    return nu if nu in p.board else None


def sp_geracho(s, i):
    """自分の山札の上から3枚を墓地に置く。相手のコスト3以下のクリーチャーを1体選び、破壊する"""
    s.mill(i, 3)
    t = s.target(i, lambda z: z.c.cost <= 3)
    if t is None:
        return
    s.ev(f"　「ミーのチョーおすすめゲラ！」：{t.c.name} を破壊する")
    destroy(s, i, t)


add("k31_geracho", "ゲラッチョ重役／「ミーのチョーおすすめゲラ！」", 6, "D", power=6000, brk=2, gs=True,
    races=("jokers",), twin=(3, "D", False), pri=9, roles="rem trg atk",
    enter=e_geracho, atkswap=swap_geracho, spell=sp_geracho,
    text="G・ストライク。W・ブレイカー。このクリーチャーが出た時、相手のクリーチャーを1体選び、破壊する。"
         "Jクライム8（このクリーチャーが攻撃する時、これと自分の墓地にあるコスト8以下の"
         "ジョーカーズ・クリーチャー1体を入れ替えてもよい。入れ替えたこのクリーチャーは破壊として墓地に置かれ、"
         "出てきたクリーチャーが攻撃を続ける）。"
         "呪文側「ミーのチョーおすすめゲラ！」（闇3）：自分の山札の上から3枚を墓地に置く。"
         "相手のコスト3以下のクリーチャーを1体選び、破壊する",
    source=SRC["k31_geracho"])
