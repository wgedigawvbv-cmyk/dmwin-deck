"""担当58：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚

出典：dmwiki.net の各カードページ（1枚ごとに、別の質問で2回ずつ読んで突き合わせた）。
      通常ページ `https://dmwiki.net/《カード名》` と、生の wiki ソース
      `https://dmwiki.net/?plugin=template&refer=《カード名》` の両方を読み、
      cardtable（文明・コスト・種類・種族・パワー）と能力行の並びが2回とも一致することを確かめた。

  この15枚の中身（再録なので元が古い。ほとんどが「パワー12000以上」とジャイアントの札）
    ・パワー12000以上の組（DMRP-04 魔／聖 の「超獣王来烈伝」系）
      　デデカブラ／ヴァム・ウィングダム／界王類咆哮目 ジュラノキル＝コストが1〜2なのにパワー12000。
      　そのかわり「攻撃できない」か「パワー12000以上で攻撃した味方がいないと攻撃できない」。
      　ジーク・ナハトファルター（コスト11・18000・Q・ブレイカー）と
      　龍装者 ジスタジオ（自分のパワー12000以上はバトルに負けた時以外離れない）がその組の軸。
    ・ジャイアントの組（DM24〜のアカネ／マリニャン系）
      　アシステスト・シネラリア（ジャイアントのコスト-1＋ウルトラ・セイバー）、
      　爆翠月 アカネ（ハイパーエナジー）、チアスカーレット アカネ（マナから召喚＋ジャイアント・メクレイド8）、
      　完璧妖精マリニャンX（マナから召喚＋相手の「出た時」を止める）。
    ・そのほか：貝獣 パウアー（捨てられた時に4枚引く）、デスマッチ・ビートル（ガードマン＋踏み倒しにバトル）、
      　環嵐！ホールインワン・ヘラクレス（タマシード/クリーチャー）、ナイター・ファイアフライ（S・トリガー）、
      　五番龍 レイクポーチャー ParZero（ブロッカー＋ジャストダイバー）、キャディ・ビートル（踏み倒しメタ）。

  調べ直して意外だった点
    ・《デデカブラ》と《界王類咆哮目 ジュラノキル》は、デュエプレ版（DMPP-32）だと
      T・ブレイカーや「パワー12000以上が6体なければ攻撃できない」が付くが、
      **TCG版は「このクリーチャーは攻撃できない」の1行だけ**でブレイカーを持たない。
      wiki のページは両方の版を並べて載せているので、TCG版の欄だけを採った。
    ・《ジーク・ナハトファルター》も同じで、「最大マナ5以上」「山札4枚以下なら誘発しない」
      「パワー12000以上が3体以上なら3枚」はデュエプレ版の条件。TCG版は無条件で2枚。
    ・《環嵐！ホールインワン・ヘラクレス》は**タマシード/クリーチャー**で、
      自分の自然のクリーチャー・タマシードが4つ以上ないとクリーチャーとして扱われない。
    ・ウルトラ・セイバーは、ふつうのセイバー（破壊だけ）と違い
      「離れる時」すべて（手札・マナ・シールド送りも）を置き換える。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move, opp_all
from envcards.env0 import (guardman, he_costx, he_payx, lock_until_my_turn, own_loss,
                           race_cost_down, worst_own)

W = "https://dmwiki.net/"
SRC = {
    "k58_pauaa": W + "《貝獣 パウアー》",
    "k58_zieku": W + "《ジーク・ナハトファルター》",
    "k58_dedekabura": W + "《デデカブラ》",
    "k58_vamu": W + "《ヴァム・ウィングダム／ソニック・ダンス》",
    "k58_juranokiru": W + "《界王類咆哮目 ジュラノキル／ジュラスティック・ハウル》",
    "k58_deathmatch": W + "《デスマッチ・ビートル》",
    "k58_herakures": W + "《環嵐！ホールインワン・ヘラクレス》",
    "k58_jisutajio": W + "《龍装者 ジスタジオ》",
    "k58_shinerariya": W + "《アシステスト・シネラリア》",
    "k58_firefly": W + "《ナイター・ファイアフライ》",
    "k58_lakepoacher": W + "《五番龍 レイクポーチャー ParZero》",
    "k58_caddy": W + "《キャディ・ビートル》",
    "k58_bakusuigetsu": W + "《爆翠月 アカネ》",
    "k58_chiascarlet": W + "《チアスカーレット アカネ》",
    "k58_marinyan": W + "《完璧妖精マリニャンX》",
}


# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払って出せる（進化元が要らない）クリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _summon_cost(s, i, k, av):
    """手札以外から召喚する時のコスト（軽減の差し込み口だけを見る）"""
    n = BY_KEY[k].cost
    f = E.COSTX.get(k)
    if f is not None:
        n = f(s, i, av)
    for g in E.COSTAURA:
        n = g(s, i, k, n)
    return max(0, n)


def _mana_acts(s, i, av, cv, name, pred):
    """自分のマナゾーンから pred に合うクリーチャーを召喚する手（コストは支払う）。

    召喚するカード自身はコストに使えないので、残りのマナで払えるものだけを並べる。"""
    p = s.P[i]
    if s.manaexec(i):
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not _plain_cre(c) or not pred(c):
            continue
        n = _summon_cost(s, i, k, av)
        if n > av - 1:
            continue
        rest = list(p.mana)
        rest.remove(k)
        cv2 = set("".join(E.MCIV[x] for x in rest))
        if (n == 0 or cv2.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append((name, k, n))
    return out


def _mana_summon(s, i, k, n):
    """マナゾーンの k を n マナ支払って召喚する"""
    p = s.P[i]
    if k not in p.mana or len(p.mana) - p.mused <= n:
        return False
    p.mused += n
    s.take_mana(i, k)
    s.ev(f"　マナゾーンから召喚：{BY_KEY[k].name}（{n}マナ）")
    s.enter(i, k, "mana", True)
    return True


def _best_mana_card(s, i, pred=None):
    """自分のマナゾーンのうち、いちばん重要度の高いカード（手札に戻す先を選ぶ）"""
    p = s.P[i]
    cs = [k for k in p.mana if pred is None or pred(BY_KEY[k])]
    return max(cs, key=E.PRI.get) if cs else None


def _mana_to_hand(s, i, pred=None):
    k = _best_mana_card(s, i, pred)
    if k is None:
        return False
    s.take_mana(i, k)
    s.P[i].hand.append(k)
    s.ev(f"　マナゾーンの {BY_KEY[k].name} を手札に戻す")
    return True


def _mekureido(s, i, n, pred, what):
    """メクレイドN：山札の上から3枚を見て、条件に合うコストN以下のカード1枚をただで使う。残りは山札の下へ"""
    p = s.P[i]
    m = min(3, len(p.deck) - 1)
    if m <= 0:
        return
    top = [p.deck.pop() for _ in range(m)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost <= n and pred(c) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        s.ev(f"　{what}：{BY_KEY[best].name} をコストを支払わずに使う")
        if _plain_cre(BY_KEY[best]) and s.fate(i, best, "deck", False) == "ok":
            s.enter(i, best, "deck", False)
        else:
            top.append(best)
    for k in top:
        p.deck.insert(0, k)


def _is_giant(c):
    return "giant" in c.races


def _cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたままコストを支払わずに唱える"""
    if not s.spell_ok(i, cost):
        return
    s.P[i].spl += 1
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    if not s.over:
        fn(s, i)
    s.spc = prev


# ================================================================ 1 貝獣 パウアー
def _pauaa_draw(s, i):
    s.draw(i, 4)


def e_pauaa(s, i, u):
    """出た時、4枚引いてもよい（引いて損になる場面はないので引く）"""
    _pauaa_draw(s, i)


def dw_pauaa(s, i, k):
    """相手の呪文やクリーチャーの能力で自分の手札から捨てられた時、4枚引いてもよい

    全体に効く差し込み口なので、このカードが捨てられた時だけ働く。"""
    if k != "k58_pauaa":
        return
    if s.tp == i and not s.dcby:
        return                          # 自分のターンに自分で払った分は「相手の能力による」ではない
    s.ev("　貝獣 パウアー：捨てられたので4枚引く")
    _pauaa_draw(s, i)


add("k58_pauaa", "貝獣 パウアー", 7, "W", power=5000, blocker=True, races=("mutopia",), pri=7,
    roles="draw blk",
    enter=e_pauaa, discardwatch=dw_pauaa,
    text="ブロッカー。このクリーチャーが出た時、または相手の呪文やクリーチャーの能力によって"
         "このカードが自分の手札から捨てられた時、カードを4枚引いてもよい",
    source=SRC["k58_pauaa"])


# ================================================================ 2 ジーク・ナハトファルター
def ts_zieku(s, i):
    """自分のターンのはじめに、このクリーチャーを自分のマナゾーンから手札に戻してもよい

    （バトルゾーンに何もなくても呼ばれる turnstart= で書く。
      戻すのは「そのターンに召喚できる見込みがある時」だけ＝残りのマナで払えるかで機械的に決める）"""
    p = s.P[i]
    if "k58_zieku" not in p.mana:
        return
    if len(p.mana) - 1 < BY_KEY["k58_zieku"].cost:
        return
    s.take_mana(i, "k58_zieku")
    p.hand.append("k58_zieku")
    s.ev("　ジーク・ナハトファルター：マナゾーンから手札に戻る")


def w_zieku(s, i, u):
    """自分のパワー12000以上のクリーチャーが出た時、山札の上から2枚をマナゾーンに置き、
    その後クリーチャー1体を自分のマナゾーンから手札に戻す（強制）"""
    if not s.has(i, "k58_zieku"):
        return
    if u.c.kind != "C" or u not in s.P[i].board or s.power(i, u) < 12000:
        return
    for z in list(s.P[i].board):
        if z.k != "k58_zieku" or s.over:
            continue
        s.ev("　ジーク・ナハトファルター：山札の上から2枚をマナゾーンへ")
        s.ramp(i, 2, tapped=False)
        _mana_to_hand(s, i, lambda c: c.kind == "C")


add("k58_zieku", "ジーク・ナハトファルター", 11, "N", power=18000, brk=4, races=("gransect",), pri=12,
    roles="acc fin",
    turnstart=ts_zieku, enterwatch=w_zieku,
    text="自分のターンのはじめに、このクリーチャーを自分のマナゾーンから手札に戻してもよい。"
         "Q・ブレイカー（シールドを4つブレイクする）。"
         "自分のパワー12000以上のクリーチャーが出た時、自分の山札の上から2枚をマナゾーンに置く。"
         "その後、クリーチャーを1体、自分のマナゾーンから手札に戻す",
    note="「パワー12000以上のクリーチャーが出た時」は、バトルゾーンにこのクリーチャーがいる間だけ働く"
         "ものとして実装した（マナゾーンで働くのは、はじめの『手札に戻してもよい』の1行だけ）。"
         "マナゾーンから手札に戻すかどうかは、『残りのマナでこのターン召喚できるか』で機械的に決める。"
         "デュエル・マスターズ プレイス版の条件（最大マナ5以上・山札4枚以下なら誘発しない・"
         "パワー12000以上が3体以上なら3枚）はTCG版には無いので入れていない",
    source=SRC["k58_zieku"])


# ================================================================ 3 デデカブラ
add("k58_dedekabura", "デデカブラ", 1, "N", power=12000, noatk=True, races=("gransect",), pri=4,
    roles="blk",
    text="このクリーチャーは攻撃できない（コスト1でパワー12000だけの壁。"
         "「パワー12000以上」を数える効果の種になる）",
    note="デュエル・マスターズ プレイス版（DMPP-32）のT・ブレイカーと"
         "「自分のパワー12000以上のクリーチャーが6体以上なければ攻撃できない」はTCG版には無い",
    source=SRC["k58_dedekabura"])


# ================================================================ 4 ヴァム・ウィングダム／ソニック・ダンス
def sp_sonicdance(s, i):
    """ソニック・ダンス：相手のパワー7000以下のクリーチャー1体を持ち主のマナゾーンに置く"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 7000)
    if t is None:
        return
    move(s, i, t, "mana")


def aw_vamu(s, i, u):
    """このターン、パワー12000以上で攻撃した自分のクリーチャーを覚えておく

    全体に効く差し込み口なので、ヴァム・ウィングダムが場にいる時だけ記録する。"""
    if not s.has(i, "k58_vamu"):
        return
    if u.c.kind == "C" and s.power(i, u, True) >= 12000:
        s.P[i].x["k58_p12"] = s.turn


def ca_vamu(s, i, u):
    """このターン、パワー12000以上で攻撃していた自分のクリーチャーがいなければ攻撃できない"""
    return s.P[i].x.get("k58_p12") != s.turn


def a_vamu(s, i, u):
    """スマッシュ・バースト：攻撃する時、呪文側を場に置いたままコストを支払わずに唱えてもよい"""
    s.ev("　スマッシュ・バースト：ソニック・ダンス をコストを支払わずに唱える")
    _cast_inplace(s, i, "k58_vamu", 3, sp_sonicdance)


add("k58_vamu", "ヴァム・ウィングダム／ソニック・ダンス", 2, "N", power=12000, brk=3,
    races=("gransect",), twin=(3, "N", False), pri=7, roles="atk rem",
    spell=sp_sonicdance, attack=a_vamu, atkwatch=aw_vamu, cantatk=ca_vamu,
    text="クリーチャー側（自然・コスト2・パワー12000）："
         "このターン、パワー12000以上で攻撃していた自分のクリーチャーがいなければ、このクリーチャーは攻撃できない。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。T・ブレイカー。"
         "呪文側「ソニック・ダンス」（自然・コスト3）："
         "相手のパワー7000以下のクリーチャーを1体選び、持ち主のマナゾーンに置く",
    note="「パワー12000以上で攻撃していた味方がいるか」は、ヴァム・ウィングダムが場にいる間の"
         "攻撃だけを数える（場にいなかった間の攻撃は覚えない）。"
         "ヴァム自身はパワー12000なので、同名の2体目や他の12000以上が先に攻撃すれば攻撃できる",
    source=SRC["k58_vamu"])


# ================================================================ 5 界王類咆哮目 ジュラノキル／ジュラスティック・ハウル
def sp_jurassichowl(s, i):
    """相手は、自身のマナゾーンのカードの枚数よりコストが大きいクリーチャーをすべてマナゾーンに置く"""
    n = len(s.P[1 - i].mana)
    for z in opp_all(s, i, lambda x: x.c.cost > n):
        if s.over:
            return
        move(s, i, z, "mana")


add("k58_juranokiru", "界王類咆哮目 ジュラノキル／ジュラスティック・ハウル", 1, "N", power=12000,
    noatk=True, races=("jurassiccommanddragon", "command", "dragon"), twin=(3, "N", False),
    pri=6, roles="rem",
    spell=sp_jurassichowl,
    text="クリーチャー側（自然・コスト1・パワー12000）：このクリーチャーは攻撃できない。"
         "呪文側「ジュラスティック・ハウル」（自然・コスト3）："
         "相手は、自身のマナゾーンにあるカードの枚数よりコストが大きいクリーチャーをすべて、"
         "自身のマナゾーンに置く（枚数は唱えた時の枚数で数える）",
    note="デュエル・マスターズ プレイス版のT・ブレイカーはTCG版には無い",
    source=SRC["k58_juranokiru"])


# ================================================================ 6 デスマッチ・ビートル
def w_deathmatch(s, i, u):
    """相手のターン中に、相手のクリーチャーがコストを支払わずに出た時、
    このクリーチャーとそのクリーチャーをバトルさせてもよい

    i＝出した側。デスマッチ・ビートルの持ち主は 1-i。"""
    d = 1 - i
    if not s.has(d, "k58_deathmatch"):
        return
    if s.tp != i or u.c.kind != "C" or u.x.get("summoned") or u not in s.P[i].board:
        return
    me = next((z for z in s.P[d].board if z.k == "k58_deathmatch" and z.c.kind == "C"), None)
    if me is None:
        return
    if s.power(d, me) <= s.power(i, u) and own_loss(s, d, me) >= s.val(u):
        return                           # 勝てず、しかも割に合わないならバトルしない
    s.ev(f"　デスマッチ・ビートル：踏み倒された {u.c.name} とバトルする")
    s.battle(d, me, i, u)


add("k58_deathmatch", "デスマッチ・ビートル", 2, "N", power=13000, noatk=True,
    races=("giant", "insect"), pri=6, roles="blk rem",
    guard=guardman("k58_deathmatch"), enterwatch=w_deathmatch,
    text="ガードマン（このクリーチャーをタップして、相手クリーチャーの攻撃先を、"
         "自分の他のクリーチャーからこのクリーチャーに変更してもよい）。"
         "このクリーチャーは攻撃できない。"
         "相手のターン中に、相手のクリーチャーがコストを支払わずに出た時、"
         "このクリーチャーとそのクリーチャーをバトルさせてもよい"
         "（バトルに勝てる時、または相手のほうが値打ちが大きい時だけバトルする）",
    source=SRC["k58_deathmatch"])


# ================================================================ 7 環嵐！ホールインワン・ヘラクレス
def _hera_cre(s, i):
    """自分の自然のクリーチャーまたは自然のタマシードが合計4つ以上あるか"""
    n = 0
    for z in s.P[i].board:
        if z.c.kind in "CT" and "N" in z.c.civ:
            n += 1
    return n >= 4


def e_herakures(s, i, u):
    """出た時、プレイヤーを1人選ぶ。そのプレイヤーは自身の墓地をシャッフルし、山札の下に置く"""
    p = s.P[i]
    # 相手の墓地の資源を消すのが基本。自分の山札が尽きかけている時だけ、自分の墓地を山札に戻す
    j = i if (len(p.deck) <= 5 and p.grave) else 1 - i
    q = s.P[j]
    if not q.grave:
        return
    ks = sorted(q.grave)
    s.rng.shuffle(ks)
    del q.grave[:]
    for k in ks:
        q.deck.insert(0, k)
    s.ev(f"　ホールインワン・ヘラクレス：プレイヤー{j}の墓地{len(ks)}枚を山札の下へ")


def a_herakures(s, i, u):
    """攻撃する時、相手のクリーチャー1体を持ち主のマナゾーンに置く。
    その後、自分の山札の上から2枚までマナゾーンに置く"""
    t = s.target(i)
    if t is not None:
        move(s, i, t, "mana")
    s.ramp(i, 2, tapped=False)


def fa_herakures(s, i, av, cv):
    """自分のターンに一度、クリーチャー1体を自分のマナゾーンから召喚してもよい"""
    if not any(z.k == "k58_herakures" and z.x.get("k58_hera") != s.turn for z in s.P[i].board):
        return []
    return _mana_acts(s, i, av, cv, "x:k58hera", lambda c: True)


def ap_herakures(s, a):
    i = s.tp
    me = next((z for z in s.P[i].board
               if z.k == "k58_herakures" and z.x.get("k58_hera") != s.turn), None)
    if me is None:
        return
    if _mana_summon(s, i, a[1], a[2]):
        me.x["k58_hera"] = s.turn


add("k58_herakures", "環嵐！ホールインワン・ヘラクレス", 4, "N", power=12000, brk=3,
    races=("giant", "insect", "ace"), pri=9, roles="acc rem fin",
    enter=e_herakures, attack=a_herakures,
    freeacts=fa_herakures, actapply={"x:k58hera": ap_herakures},
    cantatk=lambda s, i, u: not _hera_cre(s, i),
    text="タマシード/クリーチャー（自然・コスト4・パワー12000・ACE）。T・ブレイカー。"
         "このタマシードが出た時、プレイヤーを1人選ぶ。そのプレイヤーは、自身の墓地をシャッフルし、"
         "山札の下に置く（ふつうは相手を選び、自分の山札が5枚以下の時だけ自分を選ぶ）。"
         "自分のターンに一度、クリーチャーを1体、自分のマナゾーンから召喚してもよい（コストは支払う）。"
         "自分の自然のクリーチャーまたは自然のタマシードが合計4つ以上なければ、"
         "バトルゾーンにあるこのタマシードはクリーチャーとして扱わない。"
         "このクリーチャーが攻撃する時、相手のクリーチャーを1体選び、持ち主のマナゾーンに置く。"
         "その後、自分の山札の上から2枚までマナゾーンに置く",
    note="このシミュレーターには「タマシードとクリーチャーを行き来するカード」の仕組みが無いので、"
         "クリーチャー（kind=\"C\"）として登録し、"
         "「自然のクリーチャーまたはタマシードが4つ未満なら攻撃もブロックもできない」で近づけた。"
         "4つ未満の間も、相手の除去や攻撃の相手としては（本来はタマシードなので選べないはずだが）"
         "クリーチャーとして扱われてしまう",
    status="partial", source=SRC["k58_herakures"])


# ================================================================ 8 龍装者 ジスタジオ
def bf_jisutajio(s, ai, au, di, du, a_dies, d_dies):
    """バトルに負けて離れるクリーチャーに印を付ける（ジスタジオの「バトルに負けた時以外」の判定用）"""
    if not (s.has(ai, "k58_jisutajio") or s.has(di, "k58_jisutajio")):
        return a_dies, d_dies
    if a_dies:
        au.x["k58_bl"] = 1
    if d_dies:
        du.x["k58_bl"] = 1
    return a_dies, d_dies


def lr_jisutajio(s, i, u, dest, destroy_):
    """自分のパワー12000以上のクリーチャーは、バトルに負けた時以外、離れない"""
    if not s.has(i, "k58_jisutajio") or u.c.kind != "C":
        return False
    if u.x.pop("k58_bl", None) is not None:
        return False                     # バトルに負けた時はふつうに離れる
    if s.power(i, u) < 12000:
        return False
    s.ev(f"　龍装者 ジスタジオ：{u.c.name}（パワー12000以上）は離れない")
    return True


add("k58_jisutajio", "龍装者 ジスタジオ", 8, "N", power=15000, brk=3,
    races=("dragonguild", "dragon", "gransect"), pri=12, roles="blk fin",
    guard=guardman("k58_jisutajio"), battlefx=bf_jisutajio, leaverep=lr_jisutajio,
    text="ガードマン（このクリーチャーをタップして、相手クリーチャーの攻撃先を、"
         "自分の他のクリーチャーからこのクリーチャーに変更してもよい）。T・ブレイカー。"
         "自分のパワー12000以上のクリーチャーは、バトルに負けた時以外、離れない"
         "（このクリーチャー自身もパワー15000なので守られる）",
    note="「バトルに負けた時」の判定は、バトルの結果が決まった時点で負けるほうに印を付けて行う。"
         "印を付けた後に他のカードの置き換え効果でそのクリーチャーが結局離れなかった場合、"
         "その印が次の1回まで残ることがある（守りが1回だけ外れる方向にずれる）",
    source=SRC["k58_jisutajio"])


# ================================================================ 9 アシステスト・シネラリア
def e_shinerariya(s, i, u):
    """出た時、自分の他のジャイアントがあれば1枚引く"""
    if any(z is not u and _is_giant(z.c) for z in s.P[i].board):
        s.draw(i, 1)


def lr_shinerariya(s, i, u, dest, destroy_):
    """ウルトラ・セイバー：ジャイアント（自分のジャイアントが離れる時、
    かわりにこのクリーチャーを破壊してもよい。守る値打ちのあるものだけ守る）"""
    if not _is_giant(u.c):
        return False
    me = next((z for z in s.P[i].board
               if z.k == "k58_shinerariya" and z is not u and not z.x.get("k58_usav")), None)
    if me is None or E.PRI[u.k] < E.PRI["k58_shinerariya"]:
        return False
    me.x["k58_usav"] = 1
    s.ev(f"　ウルトラ・セイバー：アシステスト・シネラリアを破壊して {u.c.name} を守る")
    s.leave(i, me, "grave", destroy=True)
    return True


add("k58_shinerariya", "アシステスト・シネラリア", 3, "W", power=2000, races=("giant", "snow"),
    pri=5, roles="draw acc",
    enter=e_shinerariya, costaura=race_cost_down("giant", 1, src="k58_shinerariya"),
    leaverep=lr_shinerariya,
    text="このクリーチャーが出た時、自分の他のジャイアントがあれば、カードを1枚引く。"
         "自分のジャイアントを使うコストを1少なくする（0より少なくはならない）。"
         "ウルトラ・セイバー：ジャイアント（自分のジャイアントがバトルゾーンを離れる時、"
         "かわりにこのクリーチャーを破壊してもよい。守るほうが重要度の高い時だけ守る）",
    source=SRC["k58_shinerariya"])


# ================================================================ 10 ナイター・ファイアフライ
def e_firefly(s, i, u):
    """出た時、相手のクリーチャー1体を手札に戻す。その後、相手のクリーチャー1体を選び、
    次の自分のターンのはじめまで攻撃もブロックもできない"""
    t = s.target(i)
    if t is not None:
        move(s, i, t, "hand")
    t2 = s.target(i)
    if t2 is None:
        return
    lock_until_my_turn(s, i, t2)
    s.ev(f"　ナイター・ファイアフライ：{t2.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k58_firefly", "ナイター・ファイアフライ", 6, "W", power=4000, trig=True,
    races=("giant", "insect"), pri=7, roles="trg rem dis",
    enter=e_firefly,
    text="S・トリガー。このクリーチャーが出た時、相手のクリーチャーを1体選び、持ち主の手札に戻す。"
         "その後、相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、"
         "そのクリーチャーは攻撃もブロックもできない",
    source=SRC["k58_firefly"])


# ================================================================ 11 五番龍 レイクポーチャー ParZero
def e_lakepoacher(s, i, u):
    """出た時、自分の山札の上から6枚を見る。そのうち2枚を手札に加え、残りを山札の下に置く。
    その後、自分の手札を1枚見せてもよい。そうしたら、そのカードと同じコストの
    相手のクリーチャー1体を持ち主の手札に戻す"""
    p = s.P[i]
    n = min(6, len(p.deck) - 1)
    if n > 0:
        top = [p.deck.pop() for _ in range(n)]
        for _ in range(min(2, len(top))):
            k = max(top, key=E.PRI.get)
            top.remove(k)
            p.hand.append(k)
            s.ev(f"　レイクポーチャー ParZero：{BY_KEY[k].name} を手札に加える")
        for k in top:
            p.deck.insert(0, k)
    costs = {BY_KEY[k].cost for k in p.hand}
    if not costs:
        return
    t = s.target(i, lambda z: z.c.cost in costs)
    if t is None:
        return
    s.ev(f"　レイクポーチャー ParZero：手札を見せて コスト{t.c.cost} の {t.c.name} を手札に戻す")
    move(s, i, t, "hand")


add("k58_lakepoacher", "五番龍 レイクポーチャー ParZero", 5, "W", power=8000, brk=2,
    blocker=True, jd=True, races=("giantdragon", "giant", "dragon"), pri=10,
    roles="draw blk rem",
    enter=e_lakepoacher,
    text="ブロッカー。ジャストダイバー（出た時、次の自分のターンのはじめまで、"
         "このクリーチャーは相手に選ばれず、攻撃もされない）。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から6枚を見る。そのうち2枚を手札に加え、"
         "残りを好きな順序で山札の下に置く。その後、自分の手札を1枚見せてもよい。そうしたら、"
         "そのカードと同じコストの相手のクリーチャーを1体選び、持ち主の手札に戻す"
         "（手札に加える2枚と、戻す相手のクリーチャーは重要度で機械的に選ぶ）",
    source=SRC["k58_lakepoacher"])


# ================================================================ 12 キャディ・ビートル
def fx_caddy(s, owner, u, i, k, src, summon, res):
    """相手のターン中、相手が、自身のマナゾーンのカードの枚数よりコストが大きい
    クリーチャーを出す時、かわりにマナゾーンに置く"""
    if u.k != "k58_caddy" or i == owner or s.tp != i or res != "ok":
        return res
    if BY_KEY[k].cost > len(s.P[i].mana):
        return "mana"
    return res


def ld_caddy(s, i, u, dest, destroy_):
    """このクリーチャーが破壊される時、墓地に置くかわりにマナゾーンに置く"""
    if u.k != "k58_caddy" or not destroy_ or dest != "grave":
        return None
    return "mana"


add("k58_caddy", "キャディ・ビートル", 2, "N", power=1000, races=("giant", "insect"), pri=4,
    roles="dis",
    fatex=fx_caddy, leavedest=ld_caddy,
    text="相手のターン中、相手が、自身のマナゾーンのカードの枚数よりコストが大きいクリーチャーを出す時、"
         "かわりにそのクリーチャーを持ち主のマナゾーンに置く。"
         "このクリーチャーが破壊される時、墓地に置くかわりに自分のマナゾーンに置く",
    source=SRC["k58_caddy"])


# ================================================================ 13 爆翠月 アカネ
def bf_bakusuigetsu(s, ai, au, di, du, a_dies, d_dies):
    """このクリーチャーがバトルに勝った時、自分の山札の上から1枚をマナゾーンに置いてもよい。
    そうしたら、自分のマナゾーンから1枚、手札に戻してもよい"""
    for me, foe, j, me_dies, foe_dies in ((au, du, ai, a_dies, d_dies), (du, au, di, d_dies, a_dies)):
        if me.k != "k58_bakusuigetsu" or me_dies or not foe_dies or s.over:
            continue
        s.ev("　爆翠月 アカネ：バトルに勝ったので山札の上から1枚をマナゾーンへ")
        s.ramp(j, 1, tapped=False)
        p = s.P[j]
        if len(p.mana) - p.mused >= 2:
            _mana_to_hand(s, j)
    return a_dies, d_dies


add("k58_bakusuigetsu", "爆翠月 アカネ", 5, "N", power=5000, mach=True, races=("giant", "snow"),
    pri=8, roles="acc rem atk",
    costx=he_costx("k58_bakusuigetsu"), payx=he_payx("k58_bakusuigetsu"), battlefx=bf_bakusuigetsu,
    text="ハイパーエナジー（このクリーチャーを召喚する時、コストの異なる自分のクリーチャーを"
         "好きな数タップしてもよい。この召喚のコストは、タップしたクリーチャー1体につき2少なくなる。"
         "ただし0より少なくはならない）。マッハファイター（出たターン、タップしていない"
         "クリーチャーも攻撃できる）。"
         "このクリーチャーがバトルに勝った時、自分の山札の上から1枚をマナゾーンに置いてもよい。"
         "そうしたら、自分のマナゾーンからカードを1枚、手札に戻してもよい"
         "（手札に戻すのは、そのターンに使えるマナが2つ以上余る時だけ。戻すのは重要度のいちばん高いカード）",
    source=SRC["k58_bakusuigetsu"])


# ================================================================ 14 チアスカーレット アカネ
def fa_chiascarlet(s, i, av, cv):
    """自分のターン中、ジャイアント・クリーチャー1体を自分のマナゾーンから召喚してもよい"""
    if not any(z.k == "k58_chiascarlet" and z.x.get("k58_cs") != s.turn for z in s.P[i].board):
        return []
    return _mana_acts(s, i, av, cv, "x:k58cs", _is_giant)


def ap_chiascarlet(s, a):
    i = s.tp
    me = next((z for z in s.P[i].board
               if z.k == "k58_chiascarlet" and z.x.get("k58_cs") != s.turn), None)
    if me is None:
        return
    if _mana_summon(s, i, a[1], a[2]):
        me.x["k58_cs"] = s.turn
        s.ramp(i, 1, tapped=False)


def a_chiascarlet(s, i, u):
    """攻撃する時、自分の他のジャイアント1つをマナゾーンに置いてもよい。
    そうしたら、ジャイアント・メクレイド8をする"""
    z = worst_own(s, i, lambda x: x is not u and _is_giant(x.c))
    if z is None:
        return
    if not s.leave(i, z, "mana"):
        return
    s.ev(f"　チアスカーレット アカネ：{z.c.name} をマナゾーンに置いてジャイアント・メクレイド8")
    _mekureido(s, i, 8, _is_giant, "ジャイアント・メクレイド8")


add("k58_chiascarlet", "チアスカーレット アカネ", 5, "N", power=7000, brk=2, mach=True,
    races=("giant", "snow"), pri=10, roles="acc atk rem",
    attack=a_chiascarlet, freeacts=fa_chiascarlet, actapply={"x:k58cs": ap_chiascarlet},
    text="マッハファイター。W・ブレイカー。"
         "自分のターン中、ジャイアント・クリーチャーを1体、自分のマナゾーンから召喚してもよい"
         "（コストは支払う。このクリーチャー1体につき各ターン1回）。"
         "そうしたら、自分の山札の上から1枚をマナゾーンに置く。"
         "このクリーチャーが攻撃する時、自分の他のジャイアントを1つ、マナゾーンに置いてもよい。"
         "そうしたら、ジャイアント・メクレイド8する"
         "（山札の上から3枚を見て、その中のコスト8以下のジャイアント1枚をコストを支払わずに使う）",
    note="マナゾーンに置くジャイアントは、失うのがいちばん安いものを選ぶ（全デッキ共通の決まり）",
    source=SRC["k58_chiascarlet"])


# ================================================================ 15 完璧妖精マリニャンX
def fa_marinyan(s, i, av, cv):
    """このクリーチャーを、自分のマナゾーンから召喚してもよい"""
    if "k58_marinyan" not in s.P[i].mana:
        return []
    return _mana_acts(s, i, av, cv, "x:k58mari", lambda c: c.key == "k58_marinyan")


def ap_marinyan(s, a):
    _mana_summon(s, s.tp, "k58_marinyan", a[2])


def etl_marinyan(s, i, u):
    """相手のクリーチャーが出て、その能力がトリガーする時、
    自分のスノーフェアリーが5つ以上あれば、かわりにトリガーしない

    i＝出した側。マリニャンXの持ち主は 1-i。
    止まるのは**出たクリーチャー自身の**「出た時」だけなので、
    ほかのカードの「クリーチャーが出た時」（ENTERWATCH）はそのまま誘発させる
    （エンジンはこの差し込み口が True を返すと ENTERWATCH も飛ばしてしまうため、
    飛ばされる分をここで同じ順に回しておく）。"""
    d = 1 - i
    if u.c.kind != "C":
        return False
    if not any(z.k == "k58_marinyan" and s.abi(d, z) for z in s.P[d].board):
        return False
    n = sum(1 for z in s.P[d].board if z.c.kind in "CT" and "snow" in z.c.races)
    if n < 5:
        return False
    if not s.abi(i, u):
        return False                       # もともと能力が働かない（エンジンも ENTERWATCH を飛ばす）
    s.ev(f"　完璧妖精マリニャンX：{u.c.name} の「出た時」は誘発しない")
    for f in E.ENTERWATCH:
        if not s.over:
            f(s, i, u)
    return True


add("k58_marinyan", "完璧妖精マリニャンX", 5, "N", power=8000, brk=2, mach=True,
    races=("giant", "snow"), pri=10, roles="atk dis",
    freeacts=fa_marinyan, actapply={"x:k58mari": ap_marinyan}, entertriglock=etl_marinyan,
    text="このクリーチャーを、自分のマナゾーンから召喚してもよい（コストは支払う）。"
         "マッハファイター。W・ブレイカー。"
         "相手のクリーチャーが出て、その能力がトリガーする時、"
         "自分のスノーフェアリーが5つ以上あれば、かわりにトリガーしない",
    note="止まるのは出たクリーチャー自身の「出た時」だけ。"
         "エンジンの「出た時を誘発させない」差し込み口は、他のカードの「クリーチャーが出た時」まで"
         "飛ばしてしまうので、飛ばされる分（ENTERWATCH）をこのカードの側で同じ順に呼び直している。"
         "数えるスノーフェアリーは、クリーチャーとタマシードのエレメント",
    source=SRC["k58_marinyan"])
