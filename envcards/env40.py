"""担当40：DM26-EX1「ますますつよいパック 25の援軍」／DM26-EX2「悪感謝祭 カリスマBEST」の15枚

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）と
      生の wiki ソース（?plugin=template&refer=《カード名》）を別の質問で2回ずつ読み（数字や能力文が
      1回しか読めなかった6枚は3回）、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      一致することを確かめた。キーワード能力の定義（超魂X・S-MAX進化）は、その用語のページも開いて確かめた。

  この札束に入っている仕組み
    ・**超魂X**（邪眼魔凰デス・フェニックス／～墓碑に刻まれし魔弾の名～／夢の轟速 ザ・ランド）。
      「これがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える」。
      下にいる間も働くので、`attack=`（キーごと）ではなく `atkwatch=` で
      「自分のキーか、攻撃しているクリーチャーの under に自分のキーがあるか」を見ている。
    ・**S-MAX進化＋CRY-S-MAX進化**（CRY-S-MAX ジャオウガ）。進化元なしで出せ（`evo` ＋ `neo=True` ＋
      `evox` が常に False）、負ける時／離れる時に「自分の表向きのカード3枚を破壊」か
      「自分のシールドを1つ墓地に置く」で置き換える（`loserep=` と `leaverep=`）。
    ・**SSS級侵略［覇道］＋究極進化**（SSS級侵略 カリスマゾーン）。進化クリーチャーの上に置く進化で、
      バトルゾーン・手札・マナゾーンから水／火／自然の進化コマンドの上に重ねられる（`INVZONE`）。
      破壊される時はかわりにマナゾーンへ（`leavedest=`）。
    ・**スター進化**（終来王鬼 ジャオウガ）。`envcards.env0.star_evo_rep` を使った（退化が成り立つ）。
    ・**S革命チェンジ**（世界竜皇 ボルシャック・ヒカリスマ）＋「相手のクリーチャーでないカードの実行を
      置き換えて墓地に置く」呪文メタ。
    ・**アビスラッシュ＋革命チェンジ：アビス**（フォック＝ザ＝ダーティ）。墓地からコストを払って召喚し、
      そのターンは相手プレイヤーだけを攻撃でき、ターンの終わりに山札の下へ
      （`u.sa` ＋ `atktargetlock=` で「クリーチャーは攻撃できない」を足して、プレイヤー限定にした）。
    ・**G・G・G**（“逆悪襲”ブランド）＝手札が1枚以下なら召喚コストを6少なくする（`costx=`）。
    ・**タマシード：デーモン・コマンド＋シンカライズ＋G・ストライク**の「魔法陣」3枚。
      「このカードを自分の手札からマナゾーンに置いた時、アンタップする」は `manain=` で書いた
      （多色カードはエンジンがタップ状態でマナに置くので、`p.mused` を1戻している）。
    ・**墓地の枚数で軽くなる別のコスト**（炎氷渦と鎮魂禍の決断）＝`spcost=`。2回選ぶモード呪文。
    ・**鬼エンド**（CRY-S-MAX ジャオウガ）＝攻撃の終わりに、シールドが0のプレイヤーがいればアンタップ。
    ・**相手のターンのはじめの誘発**（鬼羅王女プリン）＝`turnstart=` で、ターンプレイヤーの相手側として見る。

  調べ直して意外だった点
    ・「魔法陣」3枚は**どれも3色のタマシード**で、名前が闇っぽいのに《邪眼の魔法陣》は**光/水/自然**。
      2回とも同じだったので誤記ではない（《邪尾》が光/火/自然、《邪爪》が闇/火/自然）。
    ・《鬼羅王女プリン》はブロッカーもW・ブレイカーも持たない、能力1つだけのカード。
      ブレイク数は1。コスト5・パワー5000の水/自然のジャイアント・ハンター/エイリアン。
    ・《“逆悪襲”ブランド》の G・G・G は**6**軽減（コスト7なので最低1マナ）。
      《“轟轟轟”ブランド》の7軽減とは違う。読み方は「ギャラクシー」。
    ・《終来王鬼 ジャオウガ》は火単色のコスト5で、出た時に**進化クリーチャーかタマシードを手札に加え、
      そのコスト以下の相手のクリーチャーかタマシードを破壊する**（手札に加えた札のコストが上限）。
    ・《嵐神 ミヅハノクエビコ》は**相手の山札の上から3枚**を表向きにして、その中の呪文を自分がただで唱える。
      唱えた呪文は相手のカードなので、唱えた後は相手の墓地に置くようにした。
    ・《邪眼魔凰デス・フェニックス》はゴッド・ガルドだが、このシミュレーターに**G・リンクはない**。
      超魂Xは下にいる時の能力付与なので、こちらは書けた。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, is_cmd
from envcards.env0 import SLAYER, race_like, star_evo_rep

W = "https://dmwiki.net/"
SRC = {
    "k40_purin": W + "《鬼羅王女プリン》",
    "k40_fock": W + "《フォック＝ザ＝ダーティ》",
    "k40_jagan": W + "《邪眼の魔法陣》",
    "k40_jabi": W + "《邪尾の魔法陣》",
    "k40_jasou": W + "《邪爪の魔法陣》",
    "k40_kesshin": W + "《炎氷渦と鎮魂禍の決断》",
    "k40_gyakuakushu": W + "《“逆悪襲”ブランド》",
    "k40_hikarisma": W + "《世界竜皇 ボルシャック・ヒカリスマ》",
    "k40_deathphoenix": W + "《邪眼魔凰デス・フェニックス》",
    "k40_charismazone": W + "《SSS級侵略 カリスマゾーン》",
    "k40_crysmax": W + "《CRY-S-MAX ジャオウガ》",
    "k40_shuraiouki": W + "《終来王鬼 ジャオウガ》",
    "k40_mizuha": W + "《嵐神 ミヅハノクエビコ》",
    "k40_bohi": W + "《～墓碑に刻まれし魔弾の名～》",
    "k40_theland": W + "《夢の轟速 ザ・ランド》",
}

MANA_FULL = 7        # マナがこの枚数以上あれば、山札から取ったカードはマナに置かずに手札へ
KEEP_PRI = 7         # これ以上に重要なカードは、マナに置かずに手札へ（全デッキ共通の決まり）


# ================================================================ 共通の道具
def _soul(u, key):
    """超魂X：自分自身か、攻撃しているクリーチャーの下に自分がいるか"""
    return u.k == key or key in u.under


def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _spell_cost(c):
    """呪文として唱える時のコスト（ツインパクトは呪文側のコスト）。呪文として使えなければ None"""
    if c.kind == "S":
        return c.cost
    if c.twin:
        return c.twin[0]
    return None


def _to_hand_or_mana(s, i, k):
    """山札の上から取った1枚を、手札に加えるかマナゾーンに置く（全デッキ共通の決まり）。
    手札が空、重要なカード、マナが足りている時は手札へ。それ以外はマナを伸ばす"""
    p = s.P[i]
    return (not p.hand) or E.PRI[k] >= KEEP_PRI or len(p.mana) >= MANA_FULL


def _put_free(s, i, k, zn):
    """手札かマナゾーンの1枚を、コストを支払わずにバトルゾーンに出す（クリーチャー・タマシード）"""
    p = s.P[i]
    c = BY_KEY[k]
    if zn == "mana":
        if k not in p.mana:
            return False
        s.take_mana(i, k)
    else:
        if k not in p.hand:
            return False
        p.hand.remove(k)
    if c.kind == "C":
        s.enter(i, k, zn, False)
    else:
        s.place_tama(i, k)
    return True


def mi_jinzou(s, i, k, src):
    """「このカードを自分の手札からマナゾーンに置いた時、アンタップする」（魔法陣の3枚で共通）。

    多色カードはエンジンが `p.mused` を1増やしてタップ状態で置くので、それを戻すとアンタップになる。"""
    if src != "hand" or k not in ("k40_jagan", "k40_jabi", "k40_jasou"):
        return
    p = s.P[i]
    if p.mused > 0:
        p.mused -= 1
        s.ev(f"　{BY_KEY[k].name}：手札からマナゾーンに置いたのでアンタップする")


def atl_onlyp(s, i, u, t):
    """「このターン、そのクリーチャーは相手プレイヤーを攻撃できる」＝クリーチャーは攻撃できない。

    印は u.x に書くので、この担当のカードが働いた時だけ効く。"""
    return u.x.get("k40_onlyp") == s.turn


def te_eotdie(s, i, u):
    """「このターンの終わりに破壊する」の印が付いたクリーチャーを破壊する（炎氷渦と鎮魂禍の決断）"""
    if not u.x.get("k40_eotdie"):
        return
    if u in s.P[i].board:
        s.leave(i, u, "grave", destroy=True)


E.ATKTARGETLOCK.append(atl_onlyp)
E.TENDALL.append(te_eotdie)


# ================================================================ 鬼羅王女プリン
def _purin_look(s, i):
    """自分の山札の上から1枚を見てもよい。そうしたら、手札に加えるか、タップしてマナゾーンに置く"""
    p = s.P[i]
    if not p.deck:
        return
    k = p.deck[-1]
    if _to_hand_or_mana(s, i, k):
        s.ev(f"　鬼羅王女プリン：山札の上の {BY_KEY[k].name} を手札へ")
        s.draw(i, 1)
    else:
        s.ev(f"　鬼羅王女プリン：山札の上の {BY_KEY[k].name} をタップしてマナゾーンへ")
        s.ramp(i, 1, tapped=True)


def ts_purin(s, i):
    """相手のターンのはじめに（i＝そのターンのプレイヤー。プリンの持ち主は 1 - i）"""
    j = 1 - i
    if not s.has(j, "k40_purin"):
        return
    for _ in range(sum(1 for z in s.P[j].board if z.k == "k40_purin")):
        if s.over:
            return
        _purin_look(s, j)


add("k40_purin", "鬼羅王女プリン", 5, "WN", power=5000,
    races=("giant", "hunter", "alien"), pri=6, roles="acc draw",
    enter=lambda s, i, u: _purin_look(s, i), turnstart=ts_purin,
    text="このクリーチャーが出た時、または相手のターンのはじめに、自分の山札の上から1枚を見てもよい。"
         "そうしたら、それを手札に加えるか、タップしてマナゾーンに置く。"
         "手札が空のとき・重要なカードのとき・マナが7枚以上あるときは手札に加え、"
         "それ以外はマナを伸ばす（全デッキ共通の決まり）",
    source=SRC["k40_purin"])


# ================================================================ フォック＝ザ＝ダーティ
def e_fock(s, i, u):
    """出た時、山札の上から4枚を表向きにし、その中のクリーチャー1体を手札かマナゾーンへ。残りは墓地"""
    p = s.P[i]
    n = min(4, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cres = [k for k in top if BY_KEY[k].kind == "C"]
    if cres:
        k = max(cres, key=E.PRI.get)
        top.remove(k)
        if _to_hand_or_mana(s, i, k):
            p.hand.append(k)
            s.ev(f"　フォック＝ザ＝ダーティ：{BY_KEY[k].name} を手札へ")
        else:
            s.add_mana(i, k, src="deck")
            s.ev(f"　フォック＝ザ＝ダーティ：{BY_KEY[k].name} をマナゾーンへ")
    for k in top:
        s.grave_put(i, k)


def fa_fock(s, i, av, cv):
    """アビスラッシュ：このクリーチャーを自分の墓地から召喚してもよい"""
    p = s.P[i]
    if "k40_fock" not in p.grave or s.manaexec(i):
        return []
    n = s.ccost(i, "k40_fock", av)
    if n > av or (n > 0 and not cv.issuperset("DN")):
        return []
    if s.fate(i, "k40_fock", "grave", True) != "ok":
        return []
    return [("x:k40abyss", n)]


def ap_fock(s, a):
    i = s.tp
    p = s.P[i]
    if "k40_fock" not in p.grave:
        return
    p.mused += a[1]
    p.grave.remove("k40_fock")
    s.ev(f"アビスラッシュ：フォック＝ザ＝ダーティ（墓地から召喚・{a[1]}マナ）")
    z = s.enter(i, "k40_fock", "grave", True)
    if z is not None:
        z.sa = True                      # そのターン攻撃できる
        z.x["k40_onlyp"] = s.turn        # ただし相手プレイヤーだけ
        z.eot = True                     # ターンの終わりに山札の下へ


add("k40_fock", "フォック＝ザ＝ダーティ", 5, "DN", power=5000,
    races=("abyssroyal", "abyss"), pri=7, roles="acc draw atk",
    enter=e_fock, freeacts=fa_fock, actapply={"x:k40abyss": ap_fock},
    changex=lambda s, i, u: race_like(u.c, "abyss"),
    playrule=lambda deck, k: None,
    text="アビスラッシュ（このクリーチャーを自分の墓地から召喚してもよい。そうしたら、このターン、"
         "このクリーチャーは相手プレイヤーを攻撃でき、このターンの終わりに山札の下に置かれる）。"
         "革命チェンジ：アビス（自分のアビスが攻撃する時、そのクリーチャーと手札にあるこのクリーチャーを"
         "入れ替えてもよい）。"
         "このクリーチャーが出た時、自分の山札の上から4枚を表向きにする。その中からクリーチャーを1体、"
         "手札に加えるかマナゾーンに置く。残りを墓地に置く",
    note="コスト5で普通に召喚もできるので、playrule の制限は付けていない",
    source=SRC["k40_fock"])


# ================================================================ 邪眼の魔法陣
def e_jagan(s, i, u):
    """出た時、山札の上から1枚を見る。シールド化するか、手札に加えるか、マナゾーンに置く"""
    p = s.P[i]
    if not p.deck:
        return
    k = p.deck[-1]
    if len(p.sh) <= 2:
        s.ev(f"　邪眼の魔法陣：山札の上の {BY_KEY[k].name} をシールド化")
        s.add_shield(i)
    elif _to_hand_or_mana(s, i, k):
        s.ev(f"　邪眼の魔法陣：山札の上の {BY_KEY[k].name} を手札へ")
        s.draw(i, 1)
    else:
        s.ev(f"　邪眼の魔法陣：山札の上の {BY_KEY[k].name} をマナゾーンへ")
        s.ramp(i, 1, tapped=False)


add("k40_jagan", "邪眼の魔法陣", 3, "LWN", kind="T", gs=True,
    races=("demoncommand", "command"), pri=4, roles="shd acc draw",
    enter=e_jagan, manain=mi_jinzou,
    text="G・ストライク。シンカライズ（このタマシードがクリーチャーであるかのように、"
         "この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、自分の山札の上から1枚を見る。それをシールド化するか、手札に加えるか、"
         "あるいはマナゾーンに置く（シールドが2つ以下ならシールド化、"
         "重要なカードやマナが足りている時は手札、それ以外はマナ。全デッキ共通の決まり）。"
         "このカードを自分の手札からマナゾーンに置いた時、アンタップする",
    source=SRC["k40_jagan"])
E.SHINKA.add("k40_jagan")


# ================================================================ 邪尾の魔法陣
def e_jabi(s, i, u):
    """出た時、1枚引く。その後、コスト3以下のコマンドを1つ、自分の手札かマナゾーンから出してもよい"""
    s.draw(i, 1)
    p = s.P[i]
    best, bv, zn = None, -1, None
    for z, zone in (("hand", p.hand), ("mana", p.mana)):
        if z == "mana" and s.manaexec(i):
            continue
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.cost > 3 or not is_cmd(c) or c.kind not in ("C", "T"):
                continue
            if c.kind == "C" and (not _playable_cre(c) or s.fate(i, k, z, False) != "ok"):
                continue
            if E.PRI[k] > bv:
                best, bv, zn = k, E.PRI[k], z
    if best is None:
        return
    s.ev(f"　邪尾の魔法陣：{'手札' if zn == 'hand' else 'マナ'}から {BY_KEY[best].name} を出す")
    _put_free(s, i, best, zn)


add("k40_jabi", "邪尾の魔法陣", 4, "LFN", kind="T", gs=True,
    races=("demoncommand", "command"), pri=5, roles="draw acc",
    enter=e_jabi, manain=mi_jinzou,
    text="G・ストライク。シンカライズ（このタマシードがクリーチャーであるかのように、"
         "この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、カードを1枚引く。その後、コスト3以下のコマンドを1つ、"
         "自分の手札またはマナゾーンから出してもよい（重要度のいちばん高いものを出す）。"
         "このカードを自分の手札からマナゾーンに置いた時、アンタップする",
    source=SRC["k40_jabi"])
E.SHINKA.add("k40_jabi")


# ================================================================ 邪爪の魔法陣
def _jasou_grave(s, j, who):
    """プレイヤー j の墓地のカードを好きな枚数（＝全部）選び、シャッフルして山札の下に置く"""
    p = s.P[j]
    if not p.grave:
        return
    cs = list(p.grave)
    del p.grave[:]
    s.rng.shuffle(cs)
    for k in cs:
        p.deck.insert(0, k)
    s.ev(f"　邪爪の魔法陣：{who}の墓地の{len(cs)}枚をシャッフルして山札の下へ")


def _jasou_bottom(s, i, t=None, mk=None):
    """コスト4以下のエレメント1つ、またはマナゾーンのカード1枚を持ち主の山札の下に置く。
    そのカードの持ち主は、自身の山札の上から1枚をマナゾーンに置く"""
    j = 1 - i
    if t is not None:
        s.ev(f"　邪爪の魔法陣：{t.c.name} を山札の下へ")
        if not s.leave(j, t, "deck", by_opp=True):
            return
    elif mk is not None:
        if mk not in s.P[j].mana:
            return
        s.take_mana(j, mk)
        s.P[j].deck.insert(0, mk)
        s.ev(f"　邪爪の魔法陣：相手のマナの {BY_KEY[mk].name} を山札の下へ")
    else:
        return
    s.ramp(j, 1, tapped=False)


def e_jasou(s, i, u):
    """出た時、次の中から1回選ぶ（効き目のいちばん大きいものを選ぶ）"""
    p, o = s.P[i], s.P[1 - i]
    t = s.target(i, lambda z: z.c.cost <= 4, kinds="CTX")
    if t is not None and s.val(t) >= 4:
        _jasou_bottom(s, i, t=t)
    elif len(o.grave) >= 6:
        _jasou_grave(s, 1 - i, "相手")
    elif t is not None:
        _jasou_bottom(s, i, t=t)
    elif o.mana:
        _jasou_bottom(s, i, mk=max(o.mana, key=E.PRI.get))
    elif p.grave and len(p.deck) <= 6:
        _jasou_grave(s, i, "自分")


add("k40_jasou", "邪爪の魔法陣", 3, "DFN", kind="T", gs=True,
    races=("demoncommand", "command"), pri=5, roles="rem dis",
    enter=e_jasou, manain=mi_jinzou,
    text="G・ストライク。シンカライズ（このタマシードがクリーチャーであるかのように、"
         "この上に進化クリーチャーを置いてもよい）。"
         "このタマシードが出た時、次の中から1回選ぶ。"
         "(1)プレイヤー1人の墓地にあるカードを好きな枚数選ぶ。その持ち主はそれらをシャッフルし、山札の下に置く／"
         "(2)コスト4以下のエレメントを1つ、またはマナゾーンにあるカードを1枚選び、持ち主の山札の下に置く。"
         "そのカードの持ち主は、自身の山札の上から1枚をマナゾーンに置く。"
         "どちらを選ぶかは、取り除ける相手のエレメントの重要度と相手の墓地の枚数で機械的に決める。"
         "このカードを自分の手札からマナゾーンに置いた時、アンタップする",
    source=SRC["k40_jasou"])
E.SHINKA.add("k40_jasou")


# ================================================================ 炎氷渦と鎮魂禍の決断
def sc_kesshin(s, i, k):
    """自分の墓地にカードが6枚以上あれば、水/闇/火(4)を支払って唱えてもよい"""
    return 4 if len(s.P[i].grave) >= 6 else 6


def _kesshin_revivable(s, i):
    best, bv = None, -1
    for k in sorted(set(s.P[i].grave)):
        c = BY_KEY[k]
        if c.kind == "C" and not c.evo and c.cost <= 5 and E.PRI[k] > bv \
                and s.fate(i, k, "grave", False) == "ok":
            best, bv = k, E.PRI[k]
    return best, bv


def _kesshin_one(s, i):
    p, o = s.P[i], s.P[1 - i]
    t = s.target(i, kinds="CTX")
    v2 = (s.val(t) + 1) if t is not None else (1 if o.hand else -1)
    v1 = 3 if (len(p.hand) <= 2 and len(p.deck) > len(p.hand) + 2) else 0
    _, v3 = _kesshin_revivable(s, i)
    if t is not None and v2 >= v1 and v2 >= v3:
        s.ev(f"　炎氷渦と鎮魂禍の決断：{t.c.name} を手札に戻し、相手の手札を1枚捨てさせる")
        s.leave(1 - i, t, "hand", by_opp=True)
        s.discard_random(1 - i)
    elif v3 >= v1 and v3 >= 0:
        s.ev("　炎氷渦と鎮魂禍の決断：墓地からコスト5以下のクリーチャーを出す")
        z = s.revive(i, lambda c: c.cost <= 5)
        if z is not None:
            z.sa = True
            z.x["k40_eotdie"] = 1
    elif v1 > 0 or (v2 < 0 and v3 < 0):
        n = len(p.hand)
        s.ev(f"　炎氷渦と鎮魂禍の決断：手札{n}枚をすべて捨て、{n + 1}枚引く")
        for k in list(p.hand):
            if k in p.hand:
                s.discard(i, k)
        s.draw(i, n + 1)


def sp_kesshin(s, i):
    for _ in range(2):
        if s.over:
            return
        _kesshin_one(s, i)


add("k40_kesshin", "炎氷渦と鎮魂禍の決断", 6, "WDF", kind="S", pri=7, roles="rem dis draw acc",
    spell=sp_kesshin, spcost=sc_kesshin, tendall=te_eotdie,
    text="自分の墓地にカードが6枚以上あれば、この呪文を水/闇/火(4)支払って唱えてもよい。"
         "次の中から2回選ぶ（同じものを選んでもよい）。"
         "(1)自分の手札をすべて捨て、その枚数より1枚多くカードを引く／"
         "(2)相手のエレメントを1つ選び、持ち主の手札に戻す。その後、相手の手札を1枚見ないで選び、捨てさせる／"
         "(3)コスト5以下のクリーチャーを1体、自分の墓地から出す。そのクリーチャーに「スピードアタッカー」を"
         "与え、このターンの終わりに破壊する。"
         "どれを選ぶかは、取り除ける相手のエレメントの重要度・自分の手札の枚数・墓地から出せるクリーチャーの"
         "重要度を比べて機械的に決める（全デッキ共通の決まり）",
    source=SRC["k40_kesshin"])


# ================================================================ “逆悪襲”ブランド
def cx_gyakuakushu(s, i, av):
    """G・G・G：自分の手札が1枚以下なら、このクリーチャーの召喚コストを6少なくする"""
    return 1 if len(s.P[i].hand) <= 1 else 7


def e_gyakuakushu(s, i, u):
    """出た時、相手のパワー6000以下のクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 6000)
    if t is None:
        return
    destroy(s, i, t)


add("k40_gyakuakushu", "“逆悪襲”ブランド", 7, "F", power=9000, brk=2, sa=True,
    races=("beatjockey",), pri=8, roles="rem atk fin",
    costx=cx_gyakuakushu, enter=e_gyakuakushu,
    text="G・G・G：自分の手札が1枚以下なら、このクリーチャーの召喚コストを6少なくする"
         "（ただし1より少なくならない）。"
         "スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、相手のパワー6000以下のクリーチャーを1体選び、破壊する",
    source=SRC["k40_gyakuakushu"])


# ================================================================ 世界竜皇 ボルシャック・ヒカリスマ
def _hika_fill(s, i, u):
    """自分の山札の上から2枚を見て、1枚を表向きでシールド化し、もう1枚を手札に加える"""
    p = s.P[i]
    n = min(2, len(p.deck))
    if n <= 0:
        return
    top = sorted((p.deck.pop() for _ in range(n)), key=E.PRI.get)
    sh = top[0]
    if not s.add_shield(i, sh, True):
        p.hand.append(sh)
    else:
        s.ev(f"　ボルシャック・ヒカリスマ：{BY_KEY[sh].name} を表向きのシールドに")
    for k in top[1:]:
        p.hand.append(k)
        s.ev(f"　ボルシャック・ヒカリスマ：{BY_KEY[k].name} を手札へ")


def e_hikarisma(s, i, u):
    """「革命チェンジ」によって出た時（ふつうに召喚して出た時は誘発しない）"""
    if "src" in u.x:
        return               # s.enter で出た＝召喚や踏み倒し。革命チェンジは U を直に作るので src が無い
    _hika_fill(s, i, u)


def sl_hikarisma(s, i, cost, k=None):
    """相手がクリーチャーでないカードを実行する時、自分の表向きのシールドを使って墓地に置く。

    カードの文に文明・種族の条件はないので、呪文のキー k は見ない
    （k が渡らない呼び出しでも同じように止める）。"""
    j = 1 - i
    if not s.has(j, "k40_hikarisma"):
        return False
    return any(up for (_, up) in s.P[j].sh)


add("k40_hikarisma", "世界竜皇 ボルシャック・ヒカリスマ", 8, "LWF", power=12500, brk=3, sa=True,
    races=("armoreddragon", "armored", "dragon"), pri=11, roles="fin atk shd draw dis",
    enter=e_hikarisma, attack=_hika_fill, spelllock=sl_hikarisma,
    changex=lambda s, i, u: u.c.cost >= 5 and race_like(u.c, "armored"),
    changezone=("hand", "shield"),          # S革命チェンジ：表向きのシールドからも入れ替えられる
    playrule=lambda deck, k: None,
    status="partial",
    text="S革命チェンジ：コスト5以上のアーマード（自分のコスト5以上のアーマードが攻撃する時、"
         "そのクリーチャーと、手札または表向きでシールドゾーンにあるこのクリーチャーを入れ替えてもよい）。"
         "スピードアタッカー。T・ブレイカー。"
         "このクリーチャーが「革命チェンジ」によって出た時または攻撃する時、自分の山札の上から2枚を見る。"
         "その中から1枚を表向きでシールド化し、もう1枚を手札に加える。"
         "相手がクリーチャーではないカードを実行する時、かわりに自分のシールドゾーンにある表向きのカードを"
         "1枚裏向きにし、その実行するカードを持ち主の墓地に置いてもよい",
    note="S革命チェンジは changezone=(\"hand\", \"shield\") で、手札と表向きのシールドの両方から"
         "入れ替えられるようにした。"
         "「相手がクリーチャーでないカードの実行を置き換えて墓地に置く」は、"
         "実行を置き換える差し込み口がエンジンにないので、"
         "『自分の表向きのシールドが1つ以上あれば相手は呪文を唱えられない』という近似にした。"
         "表向きのシールドを裏向きにして使い切る消費と、呪文以外（タマシード・城・クロスギア）への"
         "効き目は表せていない（REQUEST_40.md に書いた）",
    source=SRC["k40_hikarisma"])


# ================================================================ 邪眼魔凰デス・フェニックス
def e_deathphoenix(s, i, u):
    """出た時、相手のクリーチャーを1体選び、破壊する"""
    t = s.target(i)
    if t is None:
        return
    destroy(s, i, t)


def aw_deathphoenix(s, i, u):
    """超魂X：攻撃する時、これよりコストの小さい呪文を手札か墓地からただで唱える（唱えた後は山札の下）"""
    if not _soul(u, "k40_deathphoenix"):
        return
    p = s.P[i]
    best, bv, zn = None, -1, None
    for z, zone in (("hand", p.hand), ("grave", p.grave)):
        if z == "grave" and s.manaexec(i):
            continue
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            sc = _spell_cost(c)
            if sc is None or sc >= u.c.cost or not s.spell_ok(i, sc):
                continue
            if E.PRI[k] > bv:
                best, bv, zn = k, E.PRI[k], z
    if best is None:
        return
    (p.hand if zn == "hand" else p.grave).remove(best)
    s.ev(f"　超魂X：{BY_KEY[best].name} を{'手札' if zn == 'hand' else '墓地'}からただで唱える")
    s.cast(i, best, bool(BY_KEY[best].twin))
    if best in p.grave:
        p.grave.remove(best)
        p.deck.insert(0, best)


add("k40_deathphoenix", "邪眼魔凰デス・フェニックス", 7, "WDF", power=8000, brk=2, sa=True,
    races=("godgulde", "god", "phoenix", "dragonzombie", "fusioner"), pri=9, roles="rem atk fin",
    enter=e_deathphoenix, atkwatch=aw_deathphoenix,
    text="スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、相手のクリーチャーを1体選び、破壊する。"
         "超魂X（これがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える）"
         "このクリーチャーが攻撃する時、このクリーチャーよりコストが小さい呪文を1枚、"
         "自分の手札または墓地からコストを支払わずに唱えてもよい。"
         "そうしたら、それを唱えた後、墓地のかわりに山札の下に置く。"
         "唱える呪文は、コストが足りるもののうち重要度のいちばん高いものを選ぶ"
         "（ツインパクトは呪文側のコストで見る）",
    source=SRC["k40_deathphoenix"])


# ================================================================ SSS級侵略 カリスマゾーン
def e_charismazone(s, i, u):
    """出た時、相手はこれよりパワーの小さい自身のクリーチャーをすべて、シャッフルして山札の下に置く"""
    mine = s.power(i, u)
    o = s.P[1 - i]
    outs = [x for x in o.board if x.c.kind == "C" and s.power(1 - i, x) < mine]
    s.rng.shuffle(outs)                 # シャッフルして山札の下に置く（下に積む順序を混ぜる）
    n = 0
    for z in outs:
        if z not in o.board:
            continue
        if s.leave(1 - i, z, "deck", by_opp=True):
            n += 1
    if n:
        s.ev(f"　カリスマゾーン：相手のパワーの小さいクリーチャー{n}体を山札の下へ")


def ld_charismazone(s, i, u, dest, destroy_):
    """このクリーチャーが破壊される時、かわりにマナゾーンに置く"""
    if u.k != "k40_charismazone" or not destroy_:
        return None
    return "mana"


def pr_charismazone(deck, k):
    cmd = sum(v for kk, v in deck.items()
              if kk != k and BY_KEY[kk].kind == "C" and BY_KEY[kk].evo and is_cmd(BY_KEY[kk])
              and set("WFN") & set(BY_KEY[kk].civ))
    evo = sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C" and BY_KEY[kk].evo)
    if cmd >= 2 or evo >= 4:
        return None
    return "侵略元になる水・火・自然の進化コマンドも、進化元になる進化クリーチャーも足りない"


add("k40_charismazone", "SSS級侵略 カリスマゾーン", 8, "WFN", power=14000, brk=3, evo="WFN",
    races=("soniccommand", "command", "sinvader"), pri=12, roles="fin atk rem",
    enter=e_charismazone, leavedest=ld_charismazone, playrule=pr_charismazone,
    evox=lambda s, i, u: bool(u.c.evo),
    invade=lambda s, i, u: bool(u.c.evo) and is_cmd(u.c) and bool(set("WFN") & set(u.c.civ)),
    text="究極進化（進化クリーチャー1体の上に置く）。"
         "SSS級侵略［覇道］：水、火、または自然の進化コマンド（自分の指定のクリーチャーが攻撃する時、"
         "バトルゾーン、自分の手札、マナゾーンにあるこのカードをその上に置いてもよい）。"
         "T・ブレイカー。"
         "このクリーチャーが出た時、相手はこのクリーチャーよりパワーが小さい自身のクリーチャーをすべて、"
         "シャッフルして山札の下に置く。"
         "このクリーチャーが破壊される時、かわりにマナゾーンに置く",
    note="envtest.effect_smoke は場に進化クリーチャーがいない場面しか作らないので「使えた場面0」になる（△）。"
         "進化クリーチャーを置いた場面と、水／火／自然の進化コマンドの攻撃からの侵略は別に確かめた",
    source=SRC["k40_charismazone"])
E.INVZONE["k40_charismazone"] = ("hand", "mana", "board")


# ================================================================ CRY-S-MAX ジャオウガ
def _crysmax_faceup(s, i, u):
    """自分の表向きのカード（マナゾーン・表向きのシールド・バトルゾーン）。安いものから"""
    p = s.P[i]
    out = []
    for k in p.mana:
        out.append((E.PRI[k], "mana", k))
    for k, up in p.sh:
        if up:
            out.append((E.PRI[k], "shieldup", k))
    for z in p.board:
        if z is not u:
            out.append((s.val(z), "board", z))
    out.sort(key=lambda x: x[0])
    return out


def _crysmax_pay(s, i, u):
    """CRY-S-MAX進化：かわりに自分の表向きのカードを3枚破壊するか、自分のシールドを1つ墓地に置く"""
    p = s.P[i]
    if u.x.get("k40_busy") or u not in p.board:
        return False
    cand = _crysmax_faceup(s, i, u)
    u.x["k40_busy"] = 1
    try:
        if len(p.sh) >= 2 or (len(cand) < 3 and p.sh):
            j = min(range(len(p.sh)), key=lambda x: E.PRI[p.sh[x][0]])
            s.take_shield(i, j, "grave")
            s.ev("　CRY-S-MAX進化：かわりに自分のシールドを1つ墓地に置く")
            return True
        if len(cand) < 3:
            return False
        s.ev("　CRY-S-MAX進化：かわりに自分の表向きのカード3枚を破壊する")
        for _, zn, v in cand[:3]:
            if zn == "mana":
                if v in p.mana:
                    s.take_mana(i, v)
                    s.grave_put(i, v)
            elif zn == "shieldup":
                j = next((x for x, (kk, up) in enumerate(p.sh) if up and kk == v), None)
                if j is not None:
                    s.take_shield(i, j, "grave")
            elif v in p.board:
                s.leave(i, v, "grave", destroy=True)
        return True
    finally:
        u.x["k40_busy"] = 0


def rep_crysmax(s, i, u, dest, destroy_):
    if u.k != "k40_crysmax":
        return False
    return _crysmax_pay(s, i, u)


def lose_crysmax(s, i, how):
    if not s.has(i, "k40_crysmax"):
        return False
    u = next((z for z in s.P[i].board if z.k == "k40_crysmax"), None)
    if u is None:
        return False
    return _crysmax_pay(s, i, u)


def e_crysmax(s, i, u):
    """S-MAX進化：自分のS-MAX進化クリーチャーが2体以上あれば、1体を残して残りを手札に戻す"""
    p = s.P[i]
    for z in p.board[:]:
        if z is u or z.k != "k40_crysmax" or z not in p.board:
            continue
        p.board.remove(z)
        p.hand.append(z.k)
        for kk in z.under:
            p.hand.append(kk)
        s.ev("　S-MAX進化：先にいた CRY-S-MAX ジャオウガ を手札に戻す")


def ae_crysmax(s, i, u):
    """＜鬼エンド＞攻撃の終わりに、シールドが1つもないプレイヤーがいれば、このクリーチャーをアンタップする"""
    if u.k != "k40_crysmax":
        return
    if s.P[0].sh and s.P[1].sh:
        return
    if u.tap:
        u.tap = False
        s.ev("　鬼エンド：CRY-S-MAX ジャオウガ をアンタップする")


add("k40_crysmax", "CRY-S-MAX ジャオウガ", 5, "DFN", power=8000, brk=2, mach=True,
    evo="DFN", neo=True, races=("demonio", "onirexstars", "rexstars"), pri=9, roles="atk fin rem",
    enter=e_crysmax, leaverep=rep_crysmax, loserep=lose_crysmax, atkend=ae_crysmax,
    evox=lambda s, i, u: False, playrule=lambda deck, k: None,
    text="S-MAX進化（このクリーチャーは進化元を必要としない。自分のS-MAX進化クリーチャーが2体以上あれば、"
         "そのうちの1体を残し、残りをすべて手札に戻す）。"
         "CRY-S-MAX進化：自分がゲームに負ける時またはこのクリーチャーが離れる時、かわりに自分の表向きの"
         "カードを3枚破壊するか、自分のシールドを1つ墓地に置いてもよい。"
         "マッハファイター。スレイヤー。W・ブレイカー。"
         "＜鬼エンド＞このクリーチャーの攻撃の終わりに、シールドが1つもないプレイヤーがいれば、"
         "このクリーチャーをアンタップする。"
         "置き換えの払い方は、シールドが2つ以上あればシールド1つ（安いほう）、"
         "そうでなければ表向きのカード（マナ・表向きのシールド・バトルゾーン）のうち安い3枚",
    source=SRC["k40_crysmax"])
SLAYER.add("k40_crysmax")


# ================================================================ 終来王鬼 ジャオウガ
def e_shuraiouki(s, i, u):
    """出た時、山札の上5枚から進化クリーチャーかタマシードを1枚手札に加え、
    そのコスト以下の相手のクリーチャーかタマシードを破壊する"""
    p = s.P[i]
    n = min(5, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cands = [k for k in top if BY_KEY[k].kind == "T" or (BY_KEY[k].kind == "C" and BY_KEY[k].evo)]
    got = None
    if cands:
        got = max(cands, key=lambda k: (BY_KEY[k].cost, E.PRI[k]))
        top.remove(got)
        p.hand.append(got)
        s.ev(f"　終来王鬼 ジャオウガ：{BY_KEY[got].name} を相手に見せて手札へ")
    for k in top:
        p.deck.insert(0, k)
    if got is None:
        return
    lim = BY_KEY[got].cost
    t = s.target(i, lambda z: z.c.cost <= lim, kinds="CT")
    if t is None:
        return
    destroy(s, i, t)


def pr_shuraiouki(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C"
            and (race_like(BY_KEY[kk], "rexstars") or "F" in BY_KEY[kk].civ))
    return None if n >= 4 else "スター進化の進化元になるレクスターズか火のクリーチャーが4体いない"


add("k40_shuraiouki", "終来王鬼 ジャオウガ", 5, "F", power=8000, brk=2, evo="F",
    races=("demonio", "onirexstars", "rexstars"), pri=7, roles="rem draw atk",
    enter=e_shuraiouki, leaverep=star_evo_rep("k40_shuraiouki", "終来王鬼 ジャオウガ"),
    evox=lambda s, i, u: (u.c.kind == "C" or u.k in E.SHINKA)
    and (race_like(u.c, "rexstars") or "F" in u.c.civ),
    playrule=pr_shuraiouki,
    text="スター進化：レクスターズまたは火のクリーチャー1体の上に置く"
         "（このクリーチャーが離れる時、かわりに一番上のカード1枚が離れる）。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から5枚を見る。その中から進化クリーチャー1体または"
         "タマシード1枚を相手に見せ、手札に加えてもよい。残りを好きな順序で山札の下に置く。その後、"
         "相手に見せたカードのコスト以下の、相手のクリーチャー1体またはタマシード1枚を破壊する。"
         "手札に加える1枚は、破壊できる範囲がいちばん広くなるコストの高いものを選ぶ",
    note="進化元の「レクスターズ」は、種族名の部分一致（レクスターズ／鬼レクスターズなど）で数えている。"
         "envtest.effect_smoke は場に火のクリーチャーもレクスターズもいない場面しか作らないので"
         "「使えた場面0」になる（△）。火のクリーチャーを置いた場面と、離れた時に下のカードが残る"
         "（退化する）ことは別に確かめた",
    source=SRC["k40_shuraiouki"])


# ================================================================ 嵐神 ミヅハノクエビコ
def _mizuha_steal(s, i, u):
    """相手の山札の上から3枚を表向きにし、その中の呪文1枚を自分がただで唱える。残りは山札の下へ"""
    o = s.P[1 - i]
    p = s.P[i]
    n = min(3, len(o.deck))
    if n <= 0:
        return
    top = [o.deck.pop() for _ in range(n)]
    best, bv = None, -1
    for k in top:
        sc = _spell_cost(BY_KEY[k])
        if sc is not None and s.spell_ok(i, sc) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
    for k in top:
        o.deck.insert(0, k)
    if best is None:
        return
    s.ev(f"　嵐神 ミヅハノクエビコ：相手の山札の {BY_KEY[best].name} をただで唱える")
    s.cast(i, best, bool(BY_KEY[best].twin))
    if best in p.grave:                 # 相手のカードなので、唱えた後は相手の墓地へ
        p.grave.remove(best)
        s.grave_put(1 - i, best)


add("k40_mizuha", "嵐神 ミヅハノクエビコ", 5, "W", power=8000, brk=2, blocker=True,
    races=("mizugami", "lostcrusader", "dragon"), pri=8, roles="blk dis rem draw",
    enter=_mizuha_steal, tstart=_mizuha_steal,
    tgtlock=lambda s, by, u: u.k == "k40_mizuha" and s.spc is not None,
    text="ブロッカー。W・ブレイカー。このクリーチャーは、呪文によって相手に選ばれない。"
         "このクリーチャーが出た時または自分のターンのはじめに、相手は自身の山札の上から3枚を表向きにする。"
         "自分はその中から呪文を1枚選んでもよい。相手は残りを好きな順序で山札の下に置き、"
         "自分は選んだ呪文をコストを支払わずに唱える"
         "（重要度のいちばん高い呪文を選ぶ。ツインパクトは呪文側として唱える）。"
         "唱えた後のカードは相手のものなので相手の墓地に置く",
    source=SRC["k40_mizuha"])


# ================================================================ ～墓碑に刻まれし魔弾の名～
def e_bohi(s, i, u):
    """出た時、相手の手札を1枚見ないで選び捨てさせる。その後、そのコストと同じ枚数、自分の山札を墓地へ"""
    o = s.P[1 - i]
    p = s.P[i]
    if not o.hand:
        return
    k = o.hand[s.rng.randrange(len(o.hand))]
    s.discard(1 - i, k)
    n = BY_KEY[k].cost
    if n > 0 and len(p.deck) > n + 5:
        s.ev(f"　～墓碑に刻まれし魔弾の名～：自分の山札の上から{n}枚を墓地に置く")
        s.mill(i, n)


def aw_bohi(s, i, u):
    """超魂X：攻撃する時、これよりコストの小さいクリーチャーを1体、自分の墓地から出してもよい"""
    if not _soul(u, "k40_bohi"):
        return
    lim = u.c.cost
    z = s.revive(i, lambda c: c.cost < lim)
    if z is None:
        return
    z.sa = True
    z.x["k40_onlyp"] = s.turn            # このターン、相手プレイヤーだけを攻撃できる
    z.eot = True                         # このターンの終わりに山札の下へ


add("k40_bohi", "～墓碑に刻まれし魔弾の名～", 4, "D", power=4000,
    races=("darklord", "dragonzombie", "steamknight", "fusioner"), pri=5, roles="dis acc atk",
    enter=e_bohi, atkwatch=aw_bohi, atktargetlock=atl_onlyp,
    text="このクリーチャーが出た時、相手の手札を1枚見ないで選び、捨てさせる。その後、その捨てたカードの"
         "コストと同じ枚数、自分の山札の上から墓地に置いてもよい（山札が尽きない範囲で置く）。"
         "超魂X（これがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える）"
         "このクリーチャーが攻撃する時、このクリーチャーよりコストが小さいクリーチャーを1体、"
         "自分の墓地から出してもよい。このターン、そのクリーチャーは相手プレイヤーを攻撃でき、"
         "このターンの終わりに山札の下に置かれる",
    source=SRC["k40_bohi"])


# ================================================================ 夢の轟速 ザ・ランド
def aw_theland(s, i, u):
    """超魂X：攻撃する時、山札の上2枚からこれ以下のコストのクリーチャーを1体出し、SAを与える"""
    if not _soul(u, "k40_theland"):
        return
    p = s.P[i]
    n = min(2, len(p.deck))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if _playable_cre(c) and c.cost <= u.c.cost and E.PRI[k] > bv \
                and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
    for k in top:
        p.deck.insert(0, k)
    if best is None:
        return
    s.ev(f"　超魂X：山札の上から {BY_KEY[best].name} を出す（スピードアタッカー）")
    z = s.enter(i, best, "deck", False)
    if z is not None:
        z.sa = True


add("k40_theland", "夢の轟速 ザ・ランド", 5, "F", power=8000, brk=2, sa=True, gs=True,
    races=("soniccommand", "command", "invader", "fusioner"), pri=7, roles="atk acc fin trg",
    atkwatch=aw_theland,
    text="G・ストライク。スピードアタッカー。W・ブレイカー。"
         "超魂X（これがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える）"
         "このクリーチャーが攻撃する時、自分の山札の上から2枚を見る。その中からコストがこのクリーチャー"
         "以下のクリーチャーを1体まで出す。そのクリーチャーは、このターン「スピードアタッカー」を得る。"
         "残りを好きな順序で山札の下に置く",
    source=SRC["k40_theland"])
