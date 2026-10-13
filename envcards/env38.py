"""担当38：DM26-EX1「ますますつよいパック 25の援軍」の再録カード15枚（key は k38_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ（https://dmwiki.net/《カード名》）を
      **別の質問で2回ずつ**読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらも一致することを確かめた。《邪魂龍 ジャビビルブラッド》は「どの能力がハイパーモード中だけか」を
      決めるために、生の wiki ソース（?plugin=template&refer=…）で区切り（BGCOLOR(#cde):|c|）の位置も読んだ。
      ページ名が分からず "Spam check failed" になった3枚（鬼羅.Star／ブルー・インパルス／ギ・ルーギリン）は、
      検索で正式なページ名（全角の ＜＞・／・！ と、「」のうしろの空白）を突き止めてから読み直した。

  この札束に入っている仕組み
    ・**虹帝双極∞**（天上天下双極∞）。山札の上3枚を表向きにし、ツインパクトの呪文側をただで唱え、
      唱えた後は墓地ではなくクリーチャー側を出す。残りはマナゾーンへ。
    ・**エターナル・Ω**（VAN・ベートーベン）＝`leavedest=` で行き先を手札に変える。
      「相手のコマンド／ドラゴンが出る時、かわりに墓地に置く」は `fatex=` で書いた。
    ・**スター進化**（鬼羅.Star）＝env0 の `star_evo_rep`（退化が成り立つように必ずこれを使う）。
    ・**超無限進化**（ジ・エンド・オブ・ユニバース）＝「クリーチャー1体以上の上に置く」。
      エンジンの進化は1体の上にしか置けないので、2体以上まとめて下に置く手を `freeacts=` で足した。
      これが無いと**メガメテオバーン10**（下のカード10枚を墓地に置いて特殊勝利）が成り立たない。
    ・**究極進化MAX**（ロマノフカイザー・NEX）＝究極進化クリーチャーの上にしか置けない。
    ・**スマッシュ・バースト**（ブルー・インパルス）＝攻撃する時、呪文側を場に置いたままただで唱える。
    ・**虚無月の門**（ギ・ルーギリン）＝魔導具呪文を唱えた時、魔導具4つの上に手札・墓地から召喚。
    ・**ヨビニオン**（ハルカス／ダイダロス）、**ハイパーエナジー**（ボウダン＝ロウ）、
      **ハイパー化・ハイパーモード**（ジャビビルブラッド）、**NEO進化＋侵略**（レッドアウト）、
      **B・A・D 2＋追加ターン**（クラッシュ“覇道”）、**禁断の鼓動＋禁断解放**（禁断 ～解放せしX～）。

  調べ直して意外だった点
    ・《「修羅」の頂 VAN・ベートーベン》は**無色**（civ=""）でパワー**14000**。手札に戻すのは
      「相手のクリーチャーすべて」で、自分の場は残る。しかも**召喚によって出た時**だけ。
    ・《勝利龍装 クラッシュ“覇道”》の素のコストは**10**で、B・A・D 2 を使って8。
      「破壊された時、これがタップされていれば」追加ターンなので、B・A・D で自壊する前提の札。
    ・《禁断 ～解放せしX～》は**手札からコスト2で出す禁断の鼓動**で、裏返る先のカードが無い
      （封印が全部外れた時に「禁断解放」の効果だけが起きる）。
    ・《無限銀河ジ・エンド・オブ・ユニバース》は**光のフェニックス**でコスト7・パワー17000。
    ・《邪魂龍 ジャビビルブラッド》の**W・ブレイカーと「アビスが攻撃する時」はハイパーモード中だけ**
      （素はパワー4000・1枚ブレイクのブロッカー）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import (FLIP, discard_choice, he_costx, he_payx, lock_until_my_turn, owner_of, race_like,
                           star_evo_rep)

W = "https://dmwiki.net/"
SRC = {
    "k38_tenjou": W + "《天上天下双極∞》",
    "k38_van": W + "《「修羅」の頂 VAN・ベートーベン》",
    "k38_kira": W + "《「正義星帝」 ＜鬼羅.Star＞》",
    "k38_theend": W + "《無限銀河ジ・エンド・オブ・ユニバース》",
    "k38_emotional": W + "《神聖龍 エモーショナル・ハードコア》",
    "k38_blue": W + "《ブルー・インパルス／「真実を見極めよ、ジョニー！」》",
    "k38_girugirin": W + "《卍 ギ・ルーギリン 卍／卍獄ブレイン》",
    "k38_harukas": W + "《ヨビニオン・ハルカス》",
    "k38_boudan": W + "《超暴淵 ボウダン＝ロウ》",
    "k38_jabibil": W + "《邪魂龍 ジャビビルブラッド》",
    "k38_redout": W + "《悪名き侵略 レッドアウト》",
    "k38_romanov": W + "《超神羅ロマノフカイザー・NEX》",
    "k38_crash": W + "《勝利龍装 クラッシュ“覇道”》",
    "k38_daidalos": W + "《魔誕の猛将ダイダロス》",
    "k38_kaihou": W + "《禁断 ～解放せしX～》",
}


# ================================================================ 共通の道具
def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化元が要る進化クリーチャーは除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードを元の場所に置いたままコストを支払わずに唱える（墓地に行かない）"""
    if not s.spell_ok(i, cost):
        return
    s.P[i].spl += 1
    s.note("cast", i, k)
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    if not s.over:
        fn(s, i)
    s.spc = prev


def _yobinion(s, i, u):
    """ヨビニオン：召喚によって出た時、山札の上から、これよりコストの小さいクリーチャーが出るまで表向きにし、
    そのクリーチャーを出す。残りを山札の下に置く"""
    if not u.x.get("summoned"):
        return
    p = s.P[i]
    flipped, got = [], None
    while len(p.deck) > 1:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and c.cost < u.c.cost:
            got = k
            break
        flipped.append(k)
    if got is not None:
        if _playable_cre(BY_KEY[got]):
            s.ev(f"　ヨビニオン：{BY_KEY[got].name} を出す")
            s.enter(i, got, "deck", False)
        else:
            flipped.append(got)             # 進化クリーチャーは進化元がなく出せない
    for k in flipped:
        p.deck.insert(0, k)


def _ultimate(c):
    """究極進化クリーチャーか（このシミュレーターには「究極進化」の印が無いので、
    カードの説明文に「究極進化」と書かれているかで判定する）"""
    return c.kind == "C" and bool(c.evo) and "究極進化" in (c.note or "")


# ================================================================ 1 天上天下双極∞
def sp_tenjou(s, i):
    """虹帝双極∞：山札の上から3枚を表向きにし、ツインパクトの呪文側をただで唱えてよい。
    そうしたら、その呪文を唱えた後、墓地に置くかわりに（クリーチャー側を）出す。残りをマナゾーンに置く"""
    p = s.P[i]
    n = min(3, max(0, len(p.deck) - 1))
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    for k in sorted([x for x in top if BY_KEY[x].twin], key=lambda x: -E.PRI[x]):
        if s.over:
            break
        c = BY_KEY[k]
        if not s.spell_ok(i, c.twin[0]):
            continue
        top.remove(k)
        s.ev(f"　天上天下双極∞：{c.name} の呪文側をコストを支払わずに唱える")
        s.cast(i, k, twin=True)
        if s.over or k not in p.grave:
            continue                        # 山札の下に行く呪文・チャージャーなどは、そのカードの指示どおり
        p.grave.remove(k)
        if c.kind == "C" and (not c.evo or c.neo or s.evo_src(i, k) is not None):
            s.ev(f"　天上天下双極∞：{c.name} を墓地に置くかわりに出す")
            s.enter(i, k, "deck", False, on=(s.evo_src(i, k) if (c.evo and not c.neo) else None))
        elif c.kind == "T":
            s.place_tama(i, k)
        else:
            s.grave_put(i, k)               # クリーチャー側を出せないなら墓地へ
    for k in top:
        s.add_mana(i, k)


add("k38_tenjou", "天上天下双極∞", 9, "N", kind="S", pri=10, roles="acc fin draw",
    spell=sp_tenjou,
    text="虹帝双極∞：自分の山札の上から3枚を表向きにする。こうして表向きにしたツインパクトカードの"
         "呪文側を、コストを支払わずに唱えてもよい。そうしたら、その呪文を唱えた後、"
         "墓地に置くかわりにクリーチャー側を出す。残りをマナゾーンに置く"
         "（唱える順番は重要度の高いものから。クリーチャー側が出せない時だけ墓地に置く）",
    source=SRC["k38_tenjou"])


# ================================================================ 2 「修羅」の頂 VAN・ベートーベン
def e_van(s, i, u):
    """召喚によって出た時、相手のクリーチャーをすべて持ち主の手札に戻す"""
    if not u.x.get("summoned"):
        return
    for z in opp_all(s, i):
        move(s, i, z, "hand")


def fx_van(s, owner, u, i, k, src, summon, res):
    """相手の、コマンドまたはドラゴンのクリーチャーが出る時、かわりに墓地に置く"""
    if i == owner or res != "ok":
        return res
    c = BY_KEY[k]
    if c.kind == "C" and ("command" in c.races or "dragon" in c.races):
        return "grave"
    return res


def ld_van(s, i, u, dest, destroy_):
    """エターナル・Ω：このクリーチャーが離れる時、かわりに手札に戻す"""
    if u.k != "k38_van" or dest == "hand":
        return None
    return "hand"


add("k38_van", "「修羅」の頂 VAN・ベートーベン", 11, "", power=14000, brk=3,
    races=("kingcommanddragon", "command", "dragon", "unknown", "zenith"), pri=13, roles="rem dis fin",
    enter=e_van, fatex=fx_van, leavedest=ld_van,
    text="T・ブレイカー。このクリーチャーが召喚によって出た時、相手のクリーチャーをすべて持ち主の手札に戻す。"
         "相手の、コマンドまたはドラゴンのクリーチャーが出る時、かわりに持ち主の墓地に置く。"
         "エターナル・Ω（このクリーチャーが離れる時、かわりに手札に戻す）",
    source=SRC["k38_van"])


# ================================================================ 3 「正義星帝」 ＜鬼羅.Star＞
def _kira_put(s, i):
    """コスト4以下のクリーチャーを1体、自分の手札から出してもよい"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if not _playable_cre(c) or c.cost > 4:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　鬼羅.Star：手札から {BY_KEY[best].name} を出す")
    s.enter(i, best, "hand", False)


def e_kira(s, i, u):
    """出た時または攻撃する時、1枚引く。その後、コスト4以下のクリーチャーを1体、手札から出してもよい"""
    s.draw(i, 1)
    if not s.over:
        _kira_put(s, i)


def bo_kira(s, u):
    """自分のコスト4以下のクリーチャーすべてに「ブロッカー」を与える"""
    if u.c.kind != "C" or u.c.cost > 4:
        return False
    return s.has(owner_of(s, u), "k38_kira")


def ta_kira(s, i, u):
    """自分のターンの終わりに、自分のコスト4以下のクリーチャーをアンタップする"""
    if s.tp != i or u.c.kind != "C" or u.c.cost > 4 or not u.tap:
        return
    if not s.has(i, "k38_kira"):
        return
    u.tap = False


def pr_kira(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and ("L" in BY_KEY[kk].civ or "rexstars" in BY_KEY[kk].races))
    return None if n >= 4 else "進化元になる光／レクスターズのクリーチャーが4体いない"


add("k38_kira", "「正義星帝」 ＜鬼羅.Star＞", 5, "L", power=8500, brk=2, evo="L",
    races=("metallica", "humanoid", "rexstars"), pri=9, roles="draw blk atk fin",
    enter=e_kira, attack=e_kira, playrule=pr_kira,
    evox=lambda s, i, u: u.c.kind == "C" and ("rexstars" in u.c.races or "L" in u.c.civ),
    leaverep=star_evo_rep("k38_kira", "「正義星帝」 ＜鬼羅.Star＞"),
    blockok=bo_kira, tendall=ta_kira,
    text="スター進化：レクスターズまたは光の、クリーチャー1体の上に置く"
         "（離れる時は一番上のこのカードだけが離れ、下のクリーチャーが残る）。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、カードを1枚引く。その後、コスト4以下のクリーチャーを1体、"
         "自分の手札から出してもよい。"
         "自分のコスト4以下のクリーチャーすべてに「ブロッカー」を与え、自分のターンの終わりにそれらをアンタップする",
    note="dmwiki のカードページでは殿堂の状態がはっきり読み取れなかった（プレミアム殿堂一覧には載っていない）ので、"
         "殿堂の扱いは書いていない。デッキ構築の上限は archetypes.LIMIT の担当",
    source=SRC["k38_kira"])


# ================================================================ 4 無限銀河ジ・エンド・オブ・ユニバース
def at_theend(s, i, u):
    """メガメテオバーン10：攻撃する時、下のカード10枚を墓地に置いてもよい。そうしたら自分はゲームに勝つ"""
    if len(u.under) < 10:
        return
    for _ in range(10):
        s.grave_put(i, u.under.pop())
    s.ev("　メガメテオバーン10：下のカード10枚を墓地に置いた")
    s.win(i, "ジ・エンド・オブ・ユニバース")


def fa_theend(s, i, av, cv):
    """超無限進化：クリーチャー2体以上をまとめて下に置く手（1体だけなら普通の進化で出せる）"""
    p = s.P[i]
    if "k38_theend" not in p.hand:
        return []
    if sum(1 for z in p.board if z.c.kind == "C") < 2:
        return []
    n = s.ccost(i, "k38_theend", av)
    if n > av or (n > 0 and "L" not in cv):
        return []
    return [("x:k38_theend_max", n)]


def ap_theend(s, a):
    i = s.tp
    p = s.P[i]
    if "k38_theend" not in p.hand:
        return
    cre = [z for z in p.board if z.c.kind == "C"]
    if len(cre) < 2 or s.fate(i, "k38_theend", "hand", True) != "ok":
        return
    base = cre[0]
    others = cre[1:]
    p.hand.remove("k38_theend")
    p.mused += a[1]
    s.ev(f"超無限進化：無限銀河ジ・エンド・オブ・ユニバース（自分のクリーチャー{len(cre)}体の上に置く）")
    u = s.enter(i, "k38_theend", "hand", True, on=base)
    if u is None:
        return
    for z in others:
        if z in p.board:
            p.board.remove(z)
            u.under = u.under + [z.k] + z.under


def pr_theend(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and not BY_KEY[kk].evo)
    return None if n >= 8 else "進化元になるクリーチャーが8体いない"


add("k38_theend", "無限銀河ジ・エンド・オブ・ユニバース", 7, "L", power=17000, brk=3, evo="LWDFN",
    races=("phoenix",), pri=12, roles="fin atk",
    attack=at_theend, playrule=pr_theend, evox=lambda s, i, u: u.c.kind == "C",
    freeacts=fa_theend, actapply={"x:k38_theend_max": ap_theend},
    text="超無限進化：クリーチャー1体以上の上に置く（2体以上まとめて下に置く手も出る）。T・ブレイカー。"
         "メガメテオバーン10：このクリーチャーが攻撃する時、このクリーチャーの下にあるカードを10枚、"
         "墓地に置いてもよい。そうしたら、自分はゲームに勝つ（置けるなら必ず置く）",
    source=SRC["k38_theend"])


# ================================================================ 5 神聖龍 エモーショナル・ハードコア
def _emo_pick(s, i):
    """無視するクリーチャーの名前を1つ選ぶ（自分に見えるゾーンの、相手のいちばん重要なクリーチャー）"""
    o = s.P[1 - i]
    best, bv = None, -1
    for z in o.board:
        if z.c.kind == "C" and E.PRI[z.k] > bv:
            best, bv = z.k, E.PRI[z.k]
    if best is not None:
        return best
    for zone in (o.mana, o.grave):
        for k in zone:
            if BY_KEY[k].kind == "C" and E.PRI[k] > bv:
                best, bv = k, E.PRI[k]
    return best


def e_emotional(s, i, u):
    """出た時、《神聖龍 エモーショナル・ハードコア》以外のクリーチャーの名前を1つ選ぶ"""
    k = _emo_pick(s, i)
    if k is None or k == "k38_emotional":
        return
    u.x["emo"] = k
    s.ev(f"　エモーショナル・ハードコア：{BY_KEY[k].name} の能力をすべて無視する")


def _emo_named(s, u):
    """u の名前が、どちらかの《神聖龍 エモーショナル・ハードコア》に指定されているか"""
    for j in (0, 1):
        for z in s.P[j].board:
            if z.k == "k38_emotional" and z.x.get("emo") == u.k:
                return True
    return False


def ab_emotional(s, i, u):
    """選んだ名前を持つクリーチャーの能力をすべて無視する
    （エンジンの ABILOCK。ブロッカー・出た時・攻撃する時・ターンの始め終わり・離れた時が止まる）"""
    return u.c.kind == "C" and _emo_named(s, u)


def al_emotional(s, i, u):
    """能力を無視されたクリーチャーは「スピードアタッカー」「マッハファイター」を失う
    （出たターンに攻撃できなくなる）"""
    return u.sick and (u.c.sa or u.c.mach) and _emo_named(s, u)


def bp_emotional(s, i, u):
    """能力を無視されたクリーチャーはW・ブレイカー等を失う（ブレイク数を1に戻す）"""
    if u.c.brk <= 1 or u.c.brk >= 99 or not _emo_named(s, u):
        return 0
    return 1 - u.c.brk


def tl_emotional(s, by, u):
    """自分の他のオラクルがあれば、相手はこのクリーチャーを選べない"""
    if u.k != "k38_emotional":
        return False
    return any(z is not u and z.c.kind in "CT" and race_like(z.c, "oracle") for z in s.P[1 - by].board)


add("k38_emotional", "神聖龍 エモーショナル・ハードコア", 7, "L", power=9500, brk=2, blocker=True,
    races=("oracledragon", "oracle", "dragon", "oraclion"), pri=9, roles="blk dis fin",
    enter=e_emotional, abilock=ab_emotional, atklock=al_emotional, brkplus=bp_emotional,
    tgtlock=tl_emotional,
    text="ブロッカー。W・ブレイカー。"
         "このクリーチャーが出た時、《神聖龍 エモーショナル・ハードコア》以外のクリーチャーの名前を1つ選ぶ"
         "（相手のバトルゾーン→マナゾーン→墓地の順に、いちばん重要なクリーチャーの名前を選ぶ）。"
         "選んだ名前を持つクリーチャーの能力をすべて無視する。"
         "自分の他のオラクルがあれば、相手はこのクリーチャーを選べない（攻撃とブロックはできる）",
    note="「能力をすべて無視する」は abilock=（エンジンの ABILOCK）で書いた。"
         "これで止まるのは、ブロッカー／「出た時」／「攻撃する時」／ターンのはじめ・終わり／"
         "「離れた時」「破壊された時」。さらに atklock= と brkplus= で、"
         "スピードアタッカー・マッハファイターとブレイク数（W・ブレイカー等を1枚ブレイクに戻す）も止めている。"
         "まだ止められないのは、パワー加算・コスト軽減のような常在能力と、"
         "ジャストダイバー／ブロックされない／S・トリガー／G・ストライク／スレイヤー"
         "（それぞれを無視する差し込み口がエンジンに無い。REQUEST_38.md に書いた）",
    status="partial", source=SRC["k38_emotional"])


# ================================================================ 6 ブルー・インパルス／「真実を見極めよ、ジョニー！」
def sp_blue(s, i):
    """クリーチャーを3体まで選び、持ち主の手札に戻す（相手の重要なものから選ぶ）"""
    for _ in range(3):
        if s.over:
            return
        t = s.target(i)
        if t is None:
            return
        move(s, i, t, "hand")


def at_blue(s, i, u):
    """スマッシュ・バースト：攻撃する時、呪文側を場に置いたままコストを支払わずに唱える"""
    s.ev("　スマッシュ・バースト：「真実を見極めよ、ジョニー！」をコストを支払わずに唱える")
    _cast_inplace(s, i, "k38_blue", 7, sp_blue)


def tp_blue(s, i):
    """相手のターンの終わりに、相手のクリーチャーが自分より4体以上多く、自分の《ブルー・インパルス》が
    なければ、このクリーチャーをコストを支払わずに召喚してもよい"""
    if s.tp == i or s.over:
        return
    p = s.P[i]
    if "k38_blue" not in p.hand or s.has(i, "k38_blue"):
        return
    if s.ncre(1 - i) - s.ncre(i) < 4:
        return
    if s.fate(i, "k38_blue", "hand", True) != "ok":
        return
    p.hand.remove("k38_blue")
    s.ev("　ブルー・インパルス：相手のクリーチャーが4体以上多いので、コストを支払わずに召喚")
    s.enter(i, "k38_blue", "hand", True)


add("k38_blue", "ブルー・インパルス／「真実を見極めよ、ジョニー！」", 10, "W", power=12000, brk=3,
    races=("spriggan", "mutopia"), twin=(7, "W", True), pri=11, roles="rem trg fin atk",
    spell=sp_blue, attack=at_blue, tendp=tp_blue,
    text="クリーチャー側《ブルー・インパルス》（水10・スプリガン／ムートピア・パワー12000）："
         "相手のターンの終わりに、その相手のクリーチャーが自分より4体以上多く、"
         "自分の《ブルー・インパルス》がなければ、このクリーチャーをコストを支払わずに召喚してもよい。"
         "T・ブレイカー。スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱える）。"
         "呪文側《「真実を見極めよ、ジョニー！」》（水7・S・トリガー）："
         "クリーチャーを3体まで選び、持ち主の手札に戻す（相手の重要なクリーチャーから選ぶ）",
    source=SRC["k38_blue"])


# ================================================================ 7 卍 ギ・ルーギリン 卍／卍獄ブレイン
def sp_gokubrain(s, i):
    """卍獄ブレイン：カードを1枚引く"""
    s.draw(i, 1)


def _magic_card(c):
    return "madogu" in c.races


def sw_girugirin(s, i, k):
    """虚無月の門：自分の魔導具呪文を唱えた時、自分の魔導具と墓地の魔導具カードを合計4つ選び、
    その上にこのクリーチャーを手札または墓地からコストを支払わずに召喚してもよい"""
    if not _magic_card(BY_KEY[k]):
        return
    p = s.P[i]
    zn = "hand" if "k38_girugirin" in p.hand else ("grave" if "k38_girugirin" in p.grave else None)
    if zn is None or s.over:
        return
    gr = sorted([x for x in p.grave if _magic_card(BY_KEY[x])], key=E.PRI.get)
    bd = sorted([z for z in p.board if _magic_card(z.c)], key=lambda z: s.val(z))
    if len(gr) + len(bd) < 4:
        return
    if s.fate(i, "k38_girugirin", zn, True) != "ok":
        return
    pick_g = gr[:4]
    pick_b = bd[: 4 - len(pick_g)]
    zone = p.hand if zn == "hand" else p.grave
    zone.remove("k38_girugirin")
    for x in pick_g:
        p.grave.remove(x)
    base = pick_b[0] if pick_b else None
    s.ev("　虚無月の門：卍 ギ・ルーギリン 卍 を魔導具4つの上に召喚（コストを支払わずに）")
    u = s.enter(i, "k38_girugirin", zn, True, on=base)
    if u is None:
        for x in pick_g:                     # 出られなかったら元に戻す
            p.grave.append(x)
        return
    for z in pick_b[1:]:
        if z in p.board:
            p.board.remove(z)
            u.under = u.under + [z.k] + z.under
    u.under = u.under + pick_g


add("k38_girugirin", "卍 ギ・ルーギリン 卍／卍獄ブレイン", 8, "W", power=9000, brk=2, blocker=True,
    races=("mutopia", "dorusuzaku"), twin=(1, "W", False), pri=10, roles="blk draw atk fin",
    spell=sp_gokubrain, spellwatch=sw_girugirin,
    unbok=lambda s, i, u: u.c.kind == "C" and s.has(i, "k38_girugirin"),
    text="クリーチャー側《卍 ギ・ルーギリン 卍》（水8・ムートピア／ドルスザク・パワー9000）："
         "虚無月の門：自分の魔導具呪文を唱えた時、自分の、魔導具と墓地にある魔導具カードを合計4つ選び、"
         "その上にこのクリーチャーを、自分の手札または墓地からコストを支払わずに召喚してもよい"
         "（墓地の魔導具から先に選び、足りない分だけバトルゾーンの魔導具を使う）。"
         "ブロッカー。W・ブレイカー。自分のクリーチャーはブロックされない。"
         "呪文側《卍獄ブレイン》（水1）：カードを1枚引く",
    note="「魔導具呪文」は、このシミュレーターではカード1枚に両面の種族がまとめて入っているので、"
         "「種族に魔導具を持つ呪文（ツインパクトの呪文側を含む）」で判定している（いま当てはまるのは3枚）",
    source=SRC["k38_girugirin"])


# ================================================================ 8 ヨビニオン・ハルカス
def e_harukas(s, i, u):
    _yobinion(s, i, u)


def w_harukas(s, i, u):
    """自分のクリーチャーが出た時、そのクリーチャーと同じコストを持つ自分の他のクリーチャーがなければ、
    相手のクリーチャー1体を選ぶ。次の自分のターンのはじめまで、それは攻撃もブロックもできない。その後1枚引く"""
    if u.c.kind != "C":
        return
    p = s.P[i]
    n = sum(1 for z in p.board if z.k == "k38_harukas")
    if not n:
        return
    if any(z is not u and z.c.kind == "C" and z.c.cost == u.c.cost for z in p.board):
        return
    for _ in range(n):
        if s.over:
            return
        t = s.target(i)
        if t is not None:
            lock_until_my_turn(s, i, t)
            s.ev(f"　ヨビニオン・ハルカス：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")
        s.draw(i, 1)


add("k38_harukas", "ヨビニオン・ハルカス", 5, "W", power=6000, brk=2, blocker=True,
    races=("liquid",), pri=8, roles="blk draw dis",
    enter=e_harukas, enterwatch=w_harukas,
    text="ヨビニオン（このクリーチャーを召喚した後、自分の山札の上から1枚ずつ表向きにする。"
         "こうして最初に出た、これよりコストの小さいクリーチャーを出し、残りを山札の下に置く）。"
         "ブロッカー。W・ブレイカー。"
         "自分のクリーチャーが出た時、そのクリーチャーと同じコストを持つ自分の他のクリーチャーがなければ、"
         "相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、その選んだクリーチャーは攻撃もブロックもできない。"
         "その後、カードを1枚引く（選べる相手がいなくても引く）",
    source=SRC["k38_harukas"])


# ================================================================ 9 超暴淵 ボウダン＝ロウ
def _boudan_fx(s, i, u):
    """自分の山札の上から5枚まで墓地に置く。その後、コスト5以下の、コストが異なるクリーチャーを
    好きな数、自分の墓地から出す"""
    s.mill(i, 5)
    for cost in range(5, -1, -1):
        if s.over:
            return
        s.revive(i, (lambda n: (lambda c: c.cost == n))(cost), "grave")


def e_boudan(s, i, u):
    if u.x.get("summoned"):
        _boudan_fx(s, i, u)


def a_boudan(s, i, u):
    """相手プレイヤーを攻撃する時だけ誘発する（s.atktgt が None ならプレイヤーへの攻撃）"""
    if s.atktgt is None:
        _boudan_fx(s, i, u)


add("k38_boudan", "超暴淵 ボウダン＝ロウ", 10, "D", power=13000, brk=3,
    races=("abyssroyal", "abyss"), pri=12, roles="fin rem acc",
    enter=e_boudan, attack=a_boudan,
    costx=he_costx("k38_boudan"), payx=he_payx("k38_boudan"),
    text="ハイパーエナジー（このクリーチャーを召喚する時、コストが異なる自分のクリーチャーを好きな数"
         "タップしてもよい。こうしてタップしたクリーチャー1体につき、召喚コストを2少なくする）。"
         "T・ブレイカー。"
         "このクリーチャーが召喚によって出た時または相手プレイヤーを攻撃する時、自分の山札の上から5枚まで"
         "墓地に置く。その後、コスト5以下の、コストが異なるクリーチャーを好きな数、自分の墓地から出す"
         "（コストの大きいものから、コストごとに重要度のいちばん高い1体を出す）",
    note="",
    status="full", source=SRC["k38_boudan"])


# ================================================================ 10 邪魂龍 ジャビビルブラッド
E.HYPER_POW["k38_jabibil"] = 6000          # パワー4000 → ハイパーモード10000（W・ブレイカーは既定の2枚）


def _jab_grave_sa(s, i, u):
    """自分の墓地から出たクリーチャーか（出たターンに相手プレイヤーを攻撃できる）"""
    return u.c.kind == "C" and u.x.get("src") == "grave" and s.has(i, "k38_jabibil")


def sa_jabibil(s, i, u):
    return _jab_grave_sa(s, i, u)


def atl_jabibil(s, i, u, t):
    """「相手プレイヤーを攻撃できる」だけなので、出たターンはクリーチャーを攻撃できない"""
    if not u.sick or u.c.sa or u.c.mach:
        return False
    return _jab_grave_sa(s, i, u)


def fa_jabibil(s, i, av, cv):
    """ハイパー化：自分の他のクリーチャーを1体タップする"""
    for u in s.P[i].board:
        if u.k == "k38_jabibil" and not u.hyper:
            if any(z is not u and z.c.kind == "C" and not z.tap for z in s.P[i].board):
                return [("x:k38_hyper_jab", u.uid)]
    return []


def ap_jabibil(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k == "k38_jabibil"), None)
    if u is None or u.hyper:
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=s.val))
    u.hyper = True
    s.ev("ハイパー化：邪魂龍 ジャビビルブラッド（他のクリーチャー1体をタップ）")


def aw_jabibil(s, i, u):
    """ハイパーモード中：各ターン、はじめて自分のアビスが攻撃する時、山札の上から2枚を墓地に置き、
    その後コスト3以下のアビス・クリーチャー1体を自分の墓地から出してもよい"""
    if not race_like(u.c, "abyss"):
        return
    if not any(z.k == "k38_jabibil" and z.hyper for z in s.P[i].board):
        return
    p = s.P[i]
    if p.x.get("k38_jab_t") == s.turn:
        return
    p.x["k38_jab_t"] = s.turn
    s.ev("　ジャビビルブラッド：自分のアビスが攻撃したので山札の上から2枚を墓地に置く")
    s.mill(i, 2)
    s.revive(i, lambda c: c.cost <= 3 and race_like(c, "abyss"), "grave")


add("k38_jabibil", "邪魂龍 ジャビビルブラッド", 4, "D", power=4000, blocker=True,
    races=("abyssdragon", "abyss", "dragon", "hyperbeast"), pri=7, roles="blk acc atk",
    saok=sa_jabibil, atktargetlock=atl_jabibil, atkwatch=aw_jabibil,
    freeacts=fa_jabibil, actapply={"x:k38_hyper_jab": ap_jabibil},
    text="ブロッカー。自分の墓地から出たクリーチャーはすべて、出たターンに相手プレイヤーを攻撃できる。"
         "ハイパー化：自分の他のクリーチャーを1体タップする（自分のメインステップ中にハイパーモードを解放でき、"
         "次の自分のターンのはじめまで続く）。"
         "ハイパーモード中はパワー10000・W・ブレイカーになり、"
         "各ターン、はじめて自分のアビスが攻撃する時、自分の山札の上から2枚を墓地に置く。"
         "その後、コスト3以下のアビス・クリーチャーを1体、自分の墓地から出してもよい",
    source=SRC["k38_jabibil"])


# ================================================================ 11 悪名き侵略 レッドアウト
def sa_redout(s, i, u):
    """自分の火のクリーチャーすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and "F" in u.c.civ and s.has(i, "k38_redout")


def aw_redout(s, i, u):
    """自分の他の火のクリーチャーが攻撃する時、手札を1枚捨ててもよい。そうしたら1枚引く"""
    if u.k == "k38_redout" or u.c.kind != "C" or "F" not in u.c.civ:
        return
    p = s.P[i]
    n = sum(1 for z in p.board if z.k == "k38_redout")
    for _ in range(n):
        if s.over or not p.hand or len(p.deck) <= 1:
            return
        discard_choice(s, i)
        s.ev("　レッドアウト：手札を1枚捨てて1枚引く")
        s.draw(i, 1)


def pr_redout(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "F" in BY_KEY[kk].civ)
    return None if n >= 4 else "NEO進化／侵略の元になる火のクリーチャーが4体いない"


add("k38_redout", "悪名き侵略 レッドアウト", 4, "F", power=6000, brk=2, evo="F", neo=True,
    races=("soniccommand", "command", "invader"), pri=8, roles="atk draw fin",
    invade=lambda s, i, u: u.c.kind == "C" and "F" in u.c.civ, playrule=pr_redout,
    saok=sa_redout, atkwatch=aw_redout,
    text="NEO進化：火のクリーチャー1体の上に置いてもよい（進化元なしで召喚してもよい）。"
         "侵略：火のクリーチャー（自分の火のクリーチャーが攻撃する時、手札のこのカードをその上に重ねて出せる）。"
         "W・ブレイカー。自分の火のクリーチャーすべてに「スピードアタッカー」を与える。"
         "自分の他の火のクリーチャーが攻撃する時、自分の手札を1枚捨ててもよい。そうしたら、カードを1枚引く"
         "（手札といちばん要らない札を入れ替える形で、手札と山札があれば必ず行う）",
    source=SRC["k38_redout"])


# ================================================================ 12 超神羅ロマノフカイザー・NEX
def e_romanov(s, i, u):
    """出た時、相手のクリーチャーを2体選び破壊する。その後、相手のマナゾーンのカードを2枚選び墓地に置く"""
    for _ in range(2):
        if s.over:
            return
        t = s.target(i)
        if t is None:
            break
        destroy(s, i, t)
    o = s.P[1 - i]
    for _ in range(2):
        if s.over or not o.mana:
            return
        k = max(o.mana, key=E.PRI.get)
        s.take_mana(1 - i, k)
        s.grave_put(1 - i, k)
        s.ev(f"　ロマノフカイザー・NEX：相手のマナの {BY_KEY[k].name} を墓地へ")


def l_romanov(s, i, u, dest):
    """離れた時、自分の山札からアーマード・ドラゴンまたは名前に《ロマノフ》とあるクリーチャー1体を出してもよい"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.deck)):
        c = BY_KEY[k]
        if not _playable_cre(c):
            continue
        if "armoreddragon" not in c.races and "ロマノフ" not in c.name:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.deck.remove(best)
    s.ev(f"　ロマノフカイザー・NEX：山札から {BY_KEY[best].name} を出す")
    s.enter(i, best, "deck", False)


def pr_romanov(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and _ultimate(BY_KEY[kk]))
    return None if n >= 2 else "進化元になる究極進化クリーチャーが2体いない"


add("k38_romanov", "超神羅ロマノフカイザー・NEX", 7, "F", power=25000, brk=99, evo="F",
    races=("armoreddragon", "dragon"), pri=13, roles="rem fin atk",
    enter=e_romanov, left=l_romanov, playrule=pr_romanov,
    evox=lambda s, i, u: _ultimate(u.c),
    text="究極進化MAX：自分の究極進化クリーチャー1体の上に置く。"
         "ワールド・ブレイカー（このクリーチャーは相手のシールドをすべてブレイクする）。"
         "このクリーチャーが出た時、相手のクリーチャーを2体選び、破壊する。"
         "その後、相手のマナゾーンにあるカードを2枚選び、持ち主の墓地に置く。"
         "このクリーチャーが離れた時、自分の山札を見る。その中からアーマード・ドラゴン・クリーチャーまたは"
         "名前に《ロマノフ》とあるクリーチャーを1体出してもよい",
    note="究極進化クリーチャーは、このシミュレーターに「究極進化」の印が無いので、"
         "カードの説明文に「究極進化」と書かれた進化クリーチャーで判定している。"
         "そういうカードはいま1枚しかないので、実際にはほとんど出せない（元のカードも同じ理由で出しにくい札）",
    source=SRC["k38_romanov"])


# ================================================================ 13 勝利龍装 クラッシュ“覇道”
def cx_crash(s, i, av):
    """B・A・D 2：マナが足りない時だけ召喚コストを2少なくする（そうしたらターンの終わりに自壊する）"""
    return 10 if 10 <= av else 8


def payx_crash(s, i, k, n):
    if 10 > len(s.P[i].mana) - s.P[i].mused:
        s.P[i].x["k38_bad"] = s.turn


def e_crash(s, i, u):
    p = s.P[i]
    if p.x.get("k38_bad") == s.turn and u.x.get("summoned"):
        p.x["k38_bad"] = -1
        u.x["k38_bad"] = s.turn
        s.ev("　B・A・D 2：このターンの終わりにこのクリーチャーを破壊する")


def t_crash(s, i, u):
    if u.x.get("k38_bad") == s.turn:
        u.x["k38_bad"] = -1
        s.ev("　B・A・D 2：勝利龍装 クラッシュ“覇道” を破壊する")
        s.leave(i, u, "grave", destroy=True)


def d_crash(s, i, u):
    """破壊された時、これがタップされていれば、このターンの後に自分のターンを追加する"""
    if not u.tap:
        return
    s.P[i].extra += 1
    s.ev("　勝利龍装 クラッシュ“覇道”：このターンの後に自分のターンを追加する")


add("k38_crash", "勝利龍装 クラッシュ“覇道”", 10, "F", power=9000, brk=2, sa=True,
    races=("dragonguild", "beatjockey"), pri=12, roles="fin atk",
    costx=cx_crash, payx=payx_crash, enter=e_crash, tend=t_crash, destroyed=d_crash,
    powerx=lambda s, i, u, atk: 5000 if atk else 0,
    text="B・A・D 2（このクリーチャーの召喚コストを2少なくしてもよい。そうしたら、このターンの終わりに"
         "このクリーチャーを破壊する。マナが足りない時だけ使う）。スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが破壊された時、これがタップされていれば、このターンの後に自分のターンを追加する。"
         "バトル中、このクリーチャーのパワーを+5000する",
    note="「バトル中＋5000」は、エンジンに「バトル中」の印が無いので、"
         "《百万超邪 クロスファイア》と同じ「攻撃している時だけ＋5000」にした"
         "（ブロッカーを持たない札なので、守る側としてバトルすることはほぼ無い。"
         "そのかわり、攻撃できる相手クリーチャーの範囲も+5000ぶん広く見える）。"
         "追加ターンは s.P[i].extra で本物の追加ターンにしたが、エンジンの追加ターンは"
         "「いまターンを行っているプレイヤーがもう1回」という形なので、"
         "相手のターン中に破壊された時は、自分の次のターンの後ろに付く（1ターンぶん遅れる）",
    status="partial", source=SRC["k38_crash"])


# ================================================================ 14 魔誕の猛将ダイダロス
E.GUARDMEN.add("k38_daidalos")


def e_daidalos(s, i, u):
    _yobinion(s, i, u)


def at_daidalos(s, i, u):
    """攻撃する時、相手のパワー4000以下のクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 4000)
    if t is None:
        return
    s.ev(f"　ダイダロス：{t.c.name} を破壊")
    destroy(s, i, t)


def sa_daidalos(s, i, u):
    """自分のクリーチャーすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and s.has(i, "k38_daidalos")


def gd_daidalos(s, di, au, tu):
    """自分のクリーチャーすべてに「ガードマン」を与える
    （バトルに勝てるか、守る相手のほうが大事な時だけ引き受ける：全デッキ共通の決まり）"""
    if tu is None or not s.has(di, "k38_daidalos"):
        return None
    ap = s.power(1 - di, au, True)
    for z in s.P[di].board:
        if z.c.kind != "C" or z.tap or z is tu:
            continue
        if s.power(di, z) > ap or s.val(tu) > s.val(z):
            s.tap_cre(di, z)
            return z
    return None


add("k38_daidalos", "魔誕の猛将ダイダロス", 5, "F", power=6000, brk=2,
    races=("demoncommand", "command"), pri=8, roles="rem atk blk",
    enter=e_daidalos, attack=at_daidalos, saok=sa_daidalos, guard=gd_daidalos,
    text="ヨビニオン（このクリーチャーを召喚した後、自分の山札の上から1枚ずつ表向きにする。"
         "こうして最初に出た、これよりコストの小さいクリーチャーを出し、残りを山札の下に置く）。"
         "W・ブレイカー。自分のクリーチャーすべてに「スピードアタッカー」と「ガードマン」を与える。"
         "このクリーチャーが攻撃する時、相手のパワー4000以下のクリーチャーを1体選び、破壊する",
    source=SRC["k38_daidalos"])


# ================================================================ 15 禁断 ～解放せしX～
def fa_kaihou(s, i, av, cv):
    """禁断の鼓動は、エンジンの「カードを使う手」に種類が無いので、追加の手として出す"""
    p = s.P[i]
    if "k38_kaihou" not in p.hand or av < 2 or "F" not in cv or p.ban == 2:
        return []
    if s.has(i, "k38_kaihou"):
        return []
    return [("x:k38_kaihou",)]


def ap_kaihou(s, a):
    i = s.tp
    p = s.P[i]
    if "k38_kaihou" not in p.hand or len(p.mana) - p.mused < 2:
        return
    p.hand.remove("k38_kaihou")
    p.mused += 2
    u = E.U("k38_kaihou")
    u.sick = False
    p.board.append(u)
    s.note("enter", i, "k38_kaihou")
    n = max(0, min(6, len(p.deck) - 1))
    u.x["sealcards"] = [p.deck.pop() for _ in range(n)]
    u.x["seals"] = n
    s.ev(f"禁断 ～解放せしX～ を出した（封印{n}つ）")
    s.first_play(i, 2)
    s.noncre(i)
    s.draw(i, 1)


def flip_kaihou(s, i, u):
    """禁断解放：封印がすべて外れた時、クリーチャー1体を自分の山札、マナゾーン、または墓地から出してもよい"""
    p = s.P[i]
    best, bv, src = None, -1, None
    for zn, zone in (("deck", p.deck), ("mana", p.mana), ("grave", p.grave)):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if not _playable_cre(c):
                continue
            if E.PRI[k] > bv and s.fate(i, k, zn, False) == "ok":
                best, bv, src = k, E.PRI[k], zn
    if best is None:
        return
    if src == "deck":
        p.deck.remove(best)
    elif src == "mana":
        s.take_mana(i, best)
    else:
        p.grave.remove(best)
    s.ev(f"　禁断解放：{'山札' if src == 'deck' else ('マナ' if src == 'mana' else '墓地')}から "
         f"{BY_KEY[best].name} を出す")
    s.enter(i, best, src, False)


FLIP["k38_kaihou"] = flip_kaihou

add("k38_kaihou", "禁断 ～解放せしX～", 2, "F", kind="K", pri=6, roles="draw fin acc",
    freeacts=fa_kaihou, actapply={"x:k38_kaihou": ap_kaihou},
    text="禁断の鼓動。この鼓動が出た時、これに封印を6つ付け、その後、カードを1枚引く。この鼓動は離れない。"
         "禁断解放：この鼓動の封印がすべて外れた時、自分の山札を見る。クリーチャーを1体、"
         "自分の山札、マナゾーン、または墓地から出してもよい"
         "（封印は、自分のコマンドが出るたびに文明の合うものが1つ外れる）",
    note="裏返る先のカードは無い（封印がすべて外れた時に禁断解放の効果だけが起きて、鼓動はそのまま残る）。"
         "「離れない」は env0 が禁断の鼓動すべてに掛けている決まりでそのまま働く",
    source=SRC["k38_kaihou"])
