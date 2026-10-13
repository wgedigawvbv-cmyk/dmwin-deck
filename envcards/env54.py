"""担当54：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚（コスト8の札）

出典：dmwiki.net の各カードページ（1枚ずつ、別の質問で2回読んで突き合わせた）。
      ページが開けない札（名前が違っていた札）は、カードラッシュ（cardrush-dm.jp）の
      商品一覧で正式名を取り直してから、もう一度 dmwiki を開いて確かめた。

  担当表の名前と実際のカードの食い違い（調べ直して分かったこと）
    ・「ミステリー・ディザスター」は単独のカードではなく、
      《カブトリアル・クーガ／ミステリー・ディザスター》の**呪文側**だった
      （dmwiki に《ミステリー・ディザスター》単独のページは無い）。担当表の8番は2番と同じカード。
    ・「トワイライトMk.1 Type ホーガン」はツインパクトで、正式名は
      《トワイライトMk.1 Type ホーガン／「イチバンになってみせる！」》（DM25-EX1 3/89）。
    ・「摩破目 ナトゥーラ・トプス」もツインパクトで、正式名は
      《摩破目 ナトゥーラ・トプス／ストンピング・ウィード》。
    ・《ドンジャングルS7》は、紙版にも**マッハファイター**がある（1回目の読みで落ちていた）。
    ・《松苔ラックス》はコスト8でパワー3000（コストを下げる能力は持っていない）。

  この札束で使った仕組み
    ・「相手の『このクリーチャーが出た時』能力を持つクリーチャーを封じる」2枚
      （《黒豆だんしゃく》は出た後にマナへ送る誘発、《ア：ニーオ：マクア》は出る時の置換）。
    ・スマッシュ・バースト（攻撃する時、ツインパクトの呪文側をバトルゾーンに置いたまま、
      コストを支払わずに唱える）＝《トワイライトMk.1 Type ホーガン》。
    ・マジボンバー7（《雷龍 ヴァリヴァリウス》）／ムゲンクライム2（《闇参謀グラン・ギニョール》）。
    ・「可能ならこのクリーチャーを攻撃する」（《ドンジャングルS7》）は、
      相手の攻撃先を縛る差し込み口（atktargetlock＝ATKTARGETLOCK と noatkplock＝NOATKPX）で書いた。
    ・EXライフ2枚（《勝災電融王 ギュカウツ・マグル》《斬龍電融 オロチリュウセイ》）。

  殿堂入り・プレミアム殿堂
    dmwiki の15枚のカードページには、どれも殿堂入り／プレミアム殿堂の記載が無かった。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move
from envcards.env0 import exlife_enter, exlife_rep, lock_until_my_turn, race_like

W = "https://dmwiki.net/"
SRC = {
    "k54_garawarudo": W + "《ボルシャック・ガラワルド》",
    "k54_kuga": W + "《カブトリアル・クーガ／ミステリー・ディザスター》",
    "k54_kuromame": W + "《黒豆だんしゃく／白米男しゃく》",
    "k54_granguignol": W + "《闇参謀グラン・ギニョール》",
    "k54_nicol": W + "《ニコル・ボーラス》",
    "k54_gyukautsu": W + "《勝災電融王 ギュカウツ・マグル》",
    "k54_orochi": W + "《斬龍電融 オロチリュウセイ》",
    "k54_donjungle": W + "《ドンジャングルS7》",
    "k54_hogan": W + "《トワイライトMk.1 Type ホーガン／「イチバンになってみせる！」》",
    "k54_makua": W + "《ア：ニーオ：マクア》",
    "k54_naturatops": W + "《摩破目 ナトゥーラ・トプス／ストンピング・ウィード》",
    "k54_wancopy": W + "《名犬機 ワンコピー／101匹コピット大冒険》",
    "k54_varivarius": W + "《雷龍 ヴァリヴァリウス》",
    "k54_matsukoke": W + "《松苔ラックス》",
}

K_DON = "k54_donjungle"
K_GG = "k54_granguignol"
K_MAKUA = "k54_makua"
K_KUROMAME = "k54_kuromame"
K_OROCHI = "k54_orochi"
K_HOGAN = "k54_hogan"
K_VARI = "k54_varivarius"


# ================================================================ 共通の道具
def _can_out(s, i, k, src):
    """そのカードを src からバトルゾーンに出せるか（進化クリーチャーは進化元が要る）"""
    c = BY_KEY[k]
    if c.kind != "C":
        return False
    if c.evo and not c.neo and s.evo_src(i, k) is None:
        return False
    return s.fate(i, k, src, False) == "ok"


def _out(s, i, k, src):
    """クリーチャー1体を出す（カードは呼び出す側が元のゾーンから取り除いておく）"""
    c = BY_KEY[k]
    on = s.evo_src(i, k) if (c.evo and not c.neo) else None
    return s.enter(i, k, src, False, on=on)


def _put_element(s, i, k):
    """エレメント1つを出す／置く（カードは呼び出す側が元のゾーンから取り除いておく）"""
    c = BY_KEY[k]
    if c.kind == "C":
        _out(s, i, k, "deck")
    elif c.kind == "T":
        s.place_tama(i, k)
    elif c.kind == "G":
        s.place_castle(i, k)
    elif c.kind == "X":
        gu = E.U(k)
        gu.sick = False
        s.P[i].board.append(gu)
        fn = E.ENTER.get(k)
        if fn is not None:
            fn(s, i, gu)
    else:
        s.P[i].deck.insert(0, k)


def _best_in_mana(s, i):
    """自分のマナゾーンでいちばん重要度の高いカード。
    「マナから手札（や山札の上）に戻してもよい」の共通の決まり：
    手札のどのカードより大事で、そのターンに使うマナが1つ残るなら戻す"""
    p = s.P[i]
    if not p.mana or len(p.mana) - p.mused < 2:
        return None
    k = max(p.mana, key=E.PRI.get)
    best_hand = max((E.PRI[x] for x in p.hand), default=0)
    return k if E.PRI[k] > best_hand else None


def _cast_bz(s, i, k):
    """ツインパクトの呪文側を、バトルゾーンに置いたままコストを支払わずに唱える（スマッシュ・バースト）。

    `s.cast` は唱えた後にカードを墓地に置いてしまうので使えない（カードはバトルゾーンに残る）。
    そのため cast の中身から「墓地に置く」だけを外したものをここに書いている。"""
    p = s.P[i]
    c = BY_KEY[k]
    cost = c.twin[0] if c.twin else c.cost
    if not s.spell_ok(i, cost):
        return False
    p.spl += 1
    s.note("cast", i, k)
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    E.SPELL[k](s, i)
    s.spc = prev
    return True


def pr_neo(deck, k):
    """NEO進化は進化元なしでも召喚できるので、デッキの中身の条件は無い"""
    return None


# ---------------------------------------------------------------- バトルの補正
def _bp(s, i, u, atk=False):
    """バトル中のパワー（《ドンジャングルS7》のバトル中+6000を含む）"""
    w = s.power(i, u, atk)
    if u.k == K_DON and s.abi(i, u):
        w += 6000
    return w


def bf_k54_don(s, ai, au, di, du, a_dies, d_dies):
    """《ドンジャングルS7》：バトル中、このクリーチャーのパワーを+6000する。

    パワーの大小だけで決まっていた分を直し、スレイヤーなど他の理由で決まった分は残す"""
    abon = 6000 if (au.k == K_DON and s.abi(ai, au)) else 0
    dbon = 6000 if (du.k == K_DON and s.abi(di, du)) else 0
    if not abon and not dbon:
        return a_dies, d_dies
    ap0 = s.power(ai, au, True)
    dp0 = s.power(di, du)
    ap, dp = ap0 + abon, dp0 + dbon
    if (ap0 <= dp0) != (ap <= dp):
        a_dies = ap <= dp or au.k == "kuzen"
    if (dp0 <= ap0) != (dp <= ap):
        d_dies = dp <= ap or du.k == "kuzen"
    return a_dies, d_dies


WINFX = {}        # 「このクリーチャーがバトルに勝った時」：キー → fn(s, i, u)


def bf_k54_win(s, ai, au, di, du, a_dies, d_dies):
    """「このクリーチャーがバトルに勝った時」（相手のパワーがこちらより小さい時に勝ち）"""
    if au.k not in WINFX and du.k not in WINFX:
        return a_dies, d_dies
    ap = _bp(s, ai, au, True)
    dp = _bp(s, di, du)
    if au.k in WINFX and dp < ap and s.abi(ai, au):
        WINFX[au.k](s, ai, au)
    elif du.k in WINFX and ap < dp and s.abi(di, du):
        WINFX[du.k](s, di, du)
    return a_dies, d_dies


E.BATTLEFX.append(bf_k54_don)
E.BATTLEFX.append(bf_k54_win)


# ================================================================ ボルシャック・ガラワルド
def cx_garawarudo(s, i, av):
    """召喚コストを、バトルゾーンのクリーチャー1体につき1少なくする（0より少なくはならない）"""
    return max(0, 8 - s.ncre(0) - s.ncre(1))


def a_garawarudo(s, i, u):
    """出た時または攻撃する時、相手のクリーチャー1体を選んでバトルさせてもよい。

    「〜してもよい」は共通の決まりで機械的に決める：バトルに勝てる相手のうち重要度のいちばん高いものを選び、
    勝てる相手がいなければ選ばない（損な取り引きはしない）"""
    if u not in s.P[i].board:
        return
    ap = _bp(s, i, u, True)
    t = s.target(i, lambda z: _bp(s, 1 - i, z) < ap)
    if t is None:
        return
    s.ev(f"　ボルシャック・ガラワルド：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


def win_garawarudo(s, i, u):
    """バトルに勝った時、カードを1枚引いてもよい"""
    s.draw(i, 1)


WINFX["k54_garawarudo"] = win_garawarudo

add("k54_garawarudo", "ボルシャック・ガラワルド", 8, "F", power=9000, brk=2, sa=True,
    races=("armoreddragon", "dragon"), pri=9, roles="rem atk fin draw",
    costx=cx_garawarudo, enter=a_garawarudo, attack=a_garawarudo,
    text="このクリーチャーの召喚コストを、バトルゾーンにあるクリーチャー1体につき1少なくする"
         "（どちらのクリーチャーも数える。コストは0より少なくならない）。"
         "スピードアタッカー、W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、相手のクリーチャー1体を選んでもよい。"
         "そのクリーチャーとこのクリーチャーをバトルさせる。"
         "このクリーチャーがバトルに勝った時、カードを1枚引いてもよい。"
         "バトルさせる相手は、勝てるクリーチャーのうち重要度のいちばん高いものを選び、"
         "勝てる相手がいなければ選ばない（全デッキ共通の決まり）",
    source=SRC["k54_garawarudo"])


# ================================================================ カブトリアル・クーガ／ミステリー・ディザスター
def win_kuga(s, i, u):
    """バトルに勝った時、山札の上から3枚を表向きにし、クリーチャー1体を手札に加えてもよい。残りはマナゾーンへ"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    cres = [k for k in top if BY_KEY[k].kind == "C"]
    if cres:
        k = max(cres, key=E.PRI.get)
        top.remove(k)
        p.hand.append(k)
        s.ev(f"　カブトリアル・クーガ：{BY_KEY[k].name} を手札に加える")
    for k in top:
        s.add_mana(i, k, src="deck")


WINFX["k54_kuga"] = win_kuga


def sp_mystery(s, i):
    """ミステリー・ディザスター：山札をシャッフルし、上から1枚を表向きにする。
    クリーチャーなら出す。そうでなければマナゾーンへ"""
    p = s.P[i]
    s.rng.shuffle(p.deck)
    if len(p.deck) <= 1:
        return
    k = p.deck[-1]
    c = BY_KEY[k]
    if c.kind == "C":
        if not _can_out(s, i, k, "deck"):
            s.ev(f"　ミステリー・ディザスター：{c.name} は出せないので山札の上に残る")
            return
        p.deck.pop()
        s.ev(f"　ミステリー・ディザスター：{c.name} を出す")
        _out(s, i, k, "deck")
    else:
        p.deck.pop()
        s.ev(f"　ミステリー・ディザスター：{c.name} をマナゾーンに置く")
        s.add_mana(i, k, src="deck")


add("k54_kuga", "カブトリアル・クーガ / ミステリー・ディザスター", 8, "N", power=13000, brk=3, mach=True,
    races=("gransect",), twin=(5, "N", False), pri=9, roles="atk fin acc draw",
    spell=sp_mystery,
    text="クリーチャー側：マッハファイター、T・ブレイカー。"
         "このクリーチャーがバトルに勝った時、自分の山札の上から3枚を表向きにする。"
         "その中からクリーチャーを1体、自分の手札に加えてもよい（重要度のいちばん高いものを選ぶ）。残りをマナゾーンに置く。"
         "呪文側「ミステリー・ディザスター」（コスト5・自然）：自分の山札をシャッフルし、その後、上から1枚目を表向きにする。"
         "それがクリーチャーなら出す。そうでなければ、マナゾーンに置く",
    note="進化クリーチャーが表向きになった時は、進化元がなければ出せないので山札の上に残す（公式の「出せない場合は元のまま」）",
    source=SRC["k54_kuga"])


# ================================================================ 黒豆だんしゃく／白米男しゃく
def w_kuromame(s, i, u):
    """相手の「このクリーチャーが出た時」で始まる能力を持つクリーチャーが出た時、そのクリーチャーをマナゾーンに置く"""
    if u.c.kind != "C" or u.k not in E.ENTER:
        return
    if not s.has(1 - i, K_KUROMAME):
        return
    if u not in s.P[i].board:
        return
    s.ev(f"　黒豆だんしゃく：{u.c.name} を持ち主のマナゾーンに置く")
    s.leave(i, u, "mana", by_opp=True)


def sp_hakumai(s, i):
    """白米男しゃく：山札の上から1枚をマナゾーンに置く。その後、マナから1枚を手札に戻してもよい"""
    s.ramp(i, 1, tapped=False)
    k = _best_in_mana(s, i)
    if k is None:
        return
    s.take_mana(i, k)
    s.P[i].hand.append(k)
    s.ev(f"　白米男しゃく：マナの {BY_KEY[k].name} を手札に戻す")


add("k54_kuromame", "黒豆だんしゃく / 白米男しゃく", 8, "N", power=12000, brk=3,
    races=("gransect", "specials"), twin=(3, "N", False), pri=8, roles="dis fin acc",
    spell=sp_hakumai, enterwatch=w_kuromame,
    text="クリーチャー側：T・ブレイカー。"
         "相手の、「このクリーチャーが出た時」で始まる能力を持つクリーチャーがバトルゾーンに出た時、"
         "そのクリーチャーを持ち主のマナゾーンに置く。"
         "呪文側「白米男しゃく」（コスト3・自然）：自分の山札の上から1枚目をマナゾーンに置く。"
         "その後、カードを1枚、自分のマナゾーンから手札に戻してもよい"
         "（手札のどのカードより重要度が高く、そのターンに使うマナが1つ残る時だけ戻す）",
    note="「『このクリーチャーが出た時』で始まる能力を持つ」の判定は、"
         "エンジンの「出た時」の差し込み口を持つかどうかで見ている。"
         "そのため、公式では反応しない「召喚した時」（ヨビニオンなど）や「出す時」（EXライフ）の札にも反応してしまう",
    source=SRC["k54_kuromame"])


# ================================================================ 闇参謀グラン・ギニョール
def _mugen_cands(s, i):
    return [z for z in s.P[i].board if z.c.kind == "C" and not z.tap]


def fa_granguignol(s, i, av, cv):
    """ムゲンクライム2：自分のクリーチャー2体をタップし、水か闇の2マナで手札か墓地から召喚する"""
    p = s.P[i]
    if av < 2 or not (cv & set("WD")):
        return []
    if len(_mugen_cands(s, i)) < 2:
        return []
    out = []
    for zn, zone in (("hand", p.hand), ("grave", p.grave)):
        if K_GG in zone and s.fate(i, K_GG, zn, True) == "ok":
            out.append(("x:k54_mugen_gg", zn))
    return out


def ap_granguignol(s, a):
    i = s.tp
    p = s.P[i]
    zn = a[1]
    zone = p.hand if zn == "hand" else p.grave
    if K_GG not in zone or len(p.mana) - p.mused < 2:
        return
    cands = _mugen_cands(s, i)
    if len(cands) < 2:
        return
    for z in sorted(cands, key=lambda z: s.val(z))[:2]:
        s.tap_cre(i, z)
    p.mused += 2
    zone.remove(K_GG)
    s.ev(f"ムゲンクライム2：闇参謀グラン・ギニョール（{'手札' if zn == 'hand' else '墓地'}から召喚）")
    s.enter(i, K_GG, zn, True)


def e_granguignol(s, i, u):
    """出た時、次のうちいずれか1つを選ぶ。
    (1)他のクリーチャー1体を持ち主の手札に戻す／(2)山札の上から2枚を墓地に置き、そのどちらか1枚を手札に戻す"""
    p = s.P[i]
    t = s.target(i, lambda z: z is not u)
    v2 = 3 if len(p.deck) > 2 else -1
    if t is not None and s.val(t) >= v2:
        s.ev(f"　グラン・ギニョール：{t.c.name} を持ち主の手札に戻す")
        move(s, i, t, "hand")
        return
    if v2 < 0:
        return
    got = s.mill(i, 2)
    if not got:
        return
    k = max(got, key=E.PRI.get)
    if k in p.grave:
        p.grave.remove(k)
        p.hand.append(k)
        s.ev(f"　グラン・ギニョール：墓地に置いた {BY_KEY[k].name} を手札に戻す")


add("k54_granguignol", "闇参謀グラン・ギニョール", 8, "WD", power=4000, trig=True,
    races=("demoncommand", "command", "teamzero"), pri=7, roles="trg rem draw",
    enter=e_granguignol, freeacts=fa_granguignol, actapply={"x:k54_mugen_gg": ap_granguignol},
    text="ムゲンクライム2：自分のクリーチャーを2体タップし、水か闇の2マナを支払って、"
         "このクリーチャーを自分の手札または墓地から召喚してもよい。"
         "S・トリガー。"
         "このクリーチャーが出た時、次のうちいずれか1つを選ぶ。"
         "(1)他のクリーチャーを1体選び、持ち主の手札に戻す／"
         "(2)自分の山札の上から2枚を墓地に置いてもよい。そうしたら、そのうちのどちらか1枚を手札に戻す。"
         "どちらを選ぶかは、戻せる相手のクリーチャーの重要度で機械的に決める（全デッキ共通の決まり）",
    note="タップする2体は、失うのがいちばん安い（重要度のいちばん低い）クリーチャーを選ぶ",
    source=SRC["k54_granguignol"])


# ================================================================ ニコル・ボーラス
def e_nicol(s, i, u):
    """出た時、相手は自身の手札から7枚選び、捨てる"""
    o = s.P[1 - i]
    for _ in range(7):
        if s.over or not o.hand:
            break
        k = min(o.hand, key=E.PRI.get)
        s.discard(1 - i, k, by_opp=True)
    s.ev("　ニコル・ボーラス：相手は手札から7枚を捨てる")


def a_nicol(s, i, u):
    """攻撃する時、相手のクリーチャーを1体破壊する"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　ニコル・ボーラス：{t.c.name} を破壊する")
    destroy(s, i, t)


add("k54_nicol", "ニコル・ボーラス", 8, "WDF", power=7000, brk=2,
    races=("elderdragon", "dragon", "planeswalker"), pri=10, roles="dis rem fin",
    enter=e_nicol, attack=a_nicol,
    text="W・ブレイカー。"
         "このクリーチャーが出た時、相手は自身の手札から7枚選び、捨てる"
         "（相手が選ぶので、重要度のいちばん低い札から捨てる）。"
         "このクリーチャーが攻撃する時、相手のクリーチャーを1体、破壊する",
    source=SRC["k54_nicol"])


# ================================================================ 勝災電融王 ギュカウツ・マグル
def e_gyukautsu(s, i, u):
    """EXライフ。出た時、山札の上から4枚を見て、コストの合計が9以下になるよう多色クリーチャーを好きな数出す"""
    exlife_enter(s, i, u)
    p = s.P[i]
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    budget = 9
    while not s.over:
        best, bv = None, -1
        for k in top:
            c = BY_KEY[k]
            if not c.multi or c.kind != "C" or c.cost > budget:
                continue
            if not _can_out(s, i, k, "deck"):
                continue
            if E.PRI[k] > bv:
                best, bv = k, E.PRI[k]
        if best is None:
            break
        top.remove(best)
        budget -= BY_KEY[best].cost
        s.ev(f"　ギュカウツ・マグル：{BY_KEY[best].name} を出す（残りのコスト枠 {budget}）")
        _out(s, i, best, "deck")
    for k in top:
        p.deck.insert(0, k)


add("k54_gyukautsu", "勝災電融王 ギュカウツ・マグル", 8, "WFN", power=15000, brk=3,
    races=("dispector", "outrage", "theanswer"), pri=11, roles="fin acc shd",
    enter=e_gyukautsu, leaverep=exlife_rep,
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。T・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から4枚を見る。"
         "その中からコストの合計が9以下になるよう、多色クリーチャーを好きな数選び、出す。"
         "残りを好きな順序で山札の下に置く（重要度の高い多色クリーチャーから順に出す）",
    source=SRC["k54_gyukautsu"])


# ================================================================ 斬龍電融 オロチリュウセイ
def e_orochi(s, i, u):
    exlife_enter(s, i, u)


def sa_orochi(s, i, u):
    """自分のクリーチャーすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and s.has(i, K_OROCHI)


def fa_orochi(s, i, av, cv):
    """自分のターン中、山札の上から1枚をいつでも見てもよい。クリーチャーなら召喚してもよい（コストは支払う）"""
    p = s.P[i]
    if not s.has(i, K_OROCHI) or len(p.deck) <= 1:
        return []
    k = p.deck[-1]
    c = BY_KEY[k]
    if c.kind != "C":
        return []
    n = s.ccost(i, k, av)
    if n > av or (n > 0 and not cv.issuperset(c.civ)):
        return []
    if c.evo and not c.neo and s.evo_src(i, k) is None:
        return []
    if s.fate(i, k, "deck", True) != "ok":
        return []
    return [("x:k54_orotop", k, n)]


def ap_orochi(s, a):
    i = s.tp
    p = s.P[i]
    k, n = a[1], a[2]
    if not s.has(i, K_OROCHI) or not p.deck or p.deck[-1] != k:
        return
    if len(p.mana) - p.mused < n:
        return
    p.deck.pop()
    p.mused += n
    c = BY_KEY[k]
    on = s.evo_src(i, k) if (c.evo and not c.neo) else None
    s.ev(f"オロチリュウセイ：山札の上の {c.name} を召喚（{n}マナ）")
    s.enter(i, k, "deck", True, on=on)


add("k54_orochi", "斬龍電融 オロチリュウセイ", 8, "WFN", power=17000, brk=3,
    races=("dispector", "cyberlord", "redcommanddragon", "command", "dragon"), pri=11,
    roles="fin atk shd acc",
    enter=e_orochi, leaverep=exlife_rep, saok=sa_orochi,
    freeacts=fa_orochi, actapply={"x:k54_orotop": ap_orochi},
    text="EXライフ（出た時に山札の上から1枚を自分の下にシールドとして置き、離れる時はかわりにそのシールドを"
         "墓地に置いて残る）。T・ブレイカー。"
         "自分のクリーチャーすべてに「スピードアタッカー」を与える。"
         "自分のターン中、自分の山札の上から1枚をいつでも見てもよい。それがクリーチャーなら、召喚してもよい"
         "（コストは支払う）",
    note="山札の上から召喚するのは、進化元が見つかる進化クリーチャーか、進化でないクリーチャーだけ。"
         "山札を0枚にしないため、山札が1枚の時は使わない",
    source=SRC["k54_orochi"])


# ================================================================ ドンジャングルS7
def e_donjungle(s, i, u):
    """出た時、パワー7000以下のクリーチャーを1体、自分のマナゾーンから出してもよい"""
    s.revive(i, lambda c: c.power <= 7000, "mana")


def _don_lure(s, ai, u):
    """ai のクリーチャー u が攻撃できるドンジャングル（なければ None）"""
    if not s.has(1 - ai, K_DON):
        return None
    ap = s.power(ai, u, True)
    mf = u.sick and (s.kw(u, "mach") or bool(E.MACHOK and any(f(s, ai, u) for f in E.MACHOK)))
    for z in s.P[1 - ai].board:
        if z.k != K_DON or z.c.kind != "C" or z.jd:
            continue
        if not s.abi(1 - ai, z):
            continue
        if not z.tap and not mf:
            continue
        if s.power(1 - ai, z) > ap:
            continue
        return z
    return None


def atl_donjungle(s, i, u, t):
    """相手のクリーチャーが攻撃する時、可能ならこのクリーチャーを攻撃する（他のクリーチャーは攻撃できない）"""
    if t.k == K_DON:
        return False
    return _don_lure(s, i, u) is not None


def nop_donjungle(s, i, u):
    """ドンジャングルを攻撃できるなら、プレイヤーも攻撃できない"""
    return _don_lure(s, i, u) is not None


add("k54_donjungle", "ドンジャングルS7", 8, "N", power=8000, brk=2, mach=True,
    races=("jokers",), pri=8, roles="acc dis blk",
    enter=e_donjungle, atktargetlock=atl_donjungle, noatkplock=nop_donjungle,
    text="マッハファイター、W・ブレイカー。"
         "このクリーチャーが出た時、パワー7000以下のクリーチャーを1体、自分のマナゾーンから出してもよい。"
         "バトル中、このクリーチャーのパワーを+6000する。"
         "相手のクリーチャーが攻撃する時、可能ならこのクリーチャーを攻撃する",
    note="「バトル中+6000」はバトルの勝ち負けの判定に入れている（バトル以外で見えるパワーは8000のまま）",
    source=SRC["k54_donjungle"])


# ================================================================ トワイライトMk.1 Type ホーガン／「イチバンになってみせる！」
def cx_hogan(s, i, av):
    """召喚する時、手札のサイバー・カードを好きな枚数表向きにしてよい。1枚につきコストを1少なくする（0以下にならない）"""
    p = s.P[i]
    n = sum(1 for k in p.hand if race_like(BY_KEY[k], "cyber"))
    if K_HOGAN in p.hand and race_like(BY_KEY[K_HOGAN], "cyber"):
        n -= 1                                   # 召喚するこのカード自身は手札から表向きにできない
    return max(0, 8 - max(0, n))


def sp_ichiban(s, i):
    """「イチバンになってみせる！」：山札をシャッフルし、上から1枚を表向きにする。
    エレメントなら出してもよい。呪文ならコストを支払わずに唱えてもよい"""
    p = s.P[i]
    s.rng.shuffle(p.deck)
    if len(p.deck) <= 1:
        return
    k = p.deck[-1]
    c = BY_KEY[k]
    if c.kind == "S":
        if s.spell_ok(i, c.cost):
            p.deck.pop()
            s.ev(f"　イチバンになってみせる！：{c.name} をコストを支払わずに唱える")
            s.cast(i, k)
        return
    if c.kind == "C" and not _can_out(s, i, k, "deck"):
        s.ev(f"　イチバンになってみせる！：{c.name} は出せないので山札の上に残る")
        return
    p.deck.pop()
    s.ev(f"　イチバンになってみせる！：{c.name} を出す")
    _put_element(s, i, k)


def a_hogan(s, i, u):
    """スマッシュ・バースト：攻撃する時、呪文側をバトルゾーンに置いたままコストを支払わずに唱えてもよい"""
    _cast_bz(s, i, K_HOGAN)


add("k54_hogan", "トワイライトMk.1 Type ホーガン / 「イチバンになってみせる！」", 8, "W",
    power=8000, brk=2, gs=True, evo="W", neo=True,
    races=("cybercommand", "command"), twin=(5, "W", False), pri=8, roles="acc atk fin",
    costx=cx_hogan, attack=a_hogan, spell=sp_ichiban, playrule=pr_neo,
    text="クリーチャー側：NEO進化（自分の水のクリーチャー1体の上に置いてもよい。進化元なしで召喚してもよい）。"
         "このクリーチャーを召喚する時、自分の手札から好きな枚数のサイバー・カードを表向きにしてもよい。"
         "こうして表向きにしたカード1枚につき、このクリーチャーの召喚コストを1少なくする"
         "（コストは0以下にならない。手札のサイバー・カードはすべて表向きにする）。"
         "G・ストライク、W・ブレイカー。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい）。"
         "呪文側「イチバンになってみせる！」（コスト5・水）：自分の山札をシャッフルし、上から1枚を表向きにする。"
         "それがエレメントなら、出してもよい。呪文なら、コストを支払わずに唱えてもよい",
    note="「サイバー・カード」は種族名に「サイバー」を含むカードで数えている"
         "（ツインパクトの呪文側だけがサイバーの札は、このシミュレーターでは種族を持たないので数えられない）",
    source=SRC["k54_hogan"])


# ================================================================ ア：ニーオ：マクア
def fx_makua(s, owner, u, i, k, src, summon, res):
    """各ターンに一度、相手の「このクリーチャーが出た時」能力を持つクリーチャーが出る時、
    かわりに持ち主のマナゾーンに置かせてもよい（出る時の置換）"""
    if i == owner or res != "ok":
        return res
    if BY_KEY[k].kind != "C" or k not in E.ENTER:
        return res
    if s.P[owner].x.get("k54_makua_t") == s.turn:
        return res
    return "mana"


def mi_makua(s, i, k, src):
    """マクアの置換が実際に起きたら「各ターンに一度」を使い切る。

    `fatex`（置換の判定）は「打てる手を数える」途中でも呼ばれるので、そこで使用済みにはできない。
    実際にマナゾーンに置かれた時に数えるため、マナに置かれた時の差し込み口で記録している。"""
    if s.phase == "C" or not s.has(1 - i, K_MAKUA):
        return
    c = BY_KEY[k]
    if c.kind != "C" or k not in E.ENTER:
        return
    p = s.P[1 - i]
    if p.x.get("k54_makua_t") == s.turn:
        return
    p.x["k54_makua_t"] = s.turn


def l_makua(s, i, u, dest):
    """離れた時、相手のアンタップしているクリーチャーを1体選び、持ち主のマナゾーンに置いてもよい"""
    t = s.target(i, lambda z: not z.tap)
    if t is None:
        return
    s.ev(f"　ア：ニーオ：マクア：{t.c.name} を持ち主のマナゾーンに置く")
    move(s, i, t, "mana")


add("k54_makua", "ア：ニーオ：マクア", 8, "N", power=12000, brk=3,
    races=("veilabyss", "abyss"), pri=9, roles="dis rem fin",
    fatex=fx_makua, manain=mi_makua, left=l_makua,
    text="T・ブレイカー。"
         "各ターンに一度、相手の「このクリーチャーが出た時」で始まる能力を持つクリーチャーが出る時、"
         "かわりに、そのクリーチャーを持ち主のマナゾーンに置かせてもよい。"
         "このクリーチャーが離れた時、相手のアンタップしているクリーチャーを1体選び、"
         "持ち主のマナゾーンに置いてもよい",
    note="「『このクリーチャーが出た時』で始まる能力を持つ」の判定は、エンジンの「出た時」の差し込み口を"
         "持つかどうかで見ているので、公式では反応しない「召喚した時」「出す時」の札にも反応する。"
         "「各ターンに一度」は、置換が実際に起きた時（相手のクリーチャーがマナゾーンに置かれた時）に"
         "使用済みにしているため、相手のクリーチャーが別の理由でマナゾーンに置かれたターンは、"
         "この能力が使えなくなることがある",
    source=SRC["k54_makua"])


# ================================================================ 摩破目 ナトゥーラ・トプス／ストンピング・ウィード
def sp_stomping(s, i):
    """ストンピング・ウィード：山札の上から1枚をマナゾーンに置く。
    その後、マナから1枚を山札の上に置いてもよい"""
    s.ramp(i, 1, tapped=False)
    k = _best_in_mana(s, i)
    if k is None:
        return
    s.take_mana(i, k)
    s.put_zone(i, k, "decktop")
    s.ev(f"　ストンピング・ウィード：マナの {BY_KEY[k].name} を山札の上に置く")


add("k54_naturatops", "摩破目 ナトゥーラ・トプス / ストンピング・ウィード", 8, "N", power=12000, brk=3,
    mach=True, races=("jurassiccommanddragon", "command", "dragon"), twin=(3, "N", False),
    pri=8, roles="atk fin acc",
    spell=sp_stomping,
    text="クリーチャー側：マッハファイター、T・ブレイカー。"
         "呪文側「ストンピング・ウィード」（コスト3・自然）：自分の山札の上から1枚をマナゾーンに置く。"
         "その後、カードを1枚、自分のマナゾーンから山札の上に置いてもよい"
         "（手札のどのカードより重要度が高く、そのターンに使うマナが1つ残る時だけ置く）",
    source=SRC["k54_naturatops"])


# ================================================================ 名犬機 ワンコピー／101匹コピット大冒険
def e_wancopy(s, i, u):
    """出た時、山札の上から1枚をタップしてマナゾーンに置く。その後、自分のコスト7以下のクリーチャー1体を選び、
    同じ名前のジョーカーズ1体を自分のマナゾーンから出す"""
    p = s.P[i]
    s.ramp(i, 1, tapped=True)
    best = None
    for z in p.board:
        if z.c.kind != "C" or z.c.cost > 7 or z is u:
            continue
        if z.k not in p.mana or "jokers" not in BY_KEY[z.k].races:
            continue
        if not _can_out(s, i, z.k, "mana"):
            continue
        if best is None or E.PRI[z.k] > E.PRI[best]:
            best = z.k
    if best is None:
        return
    s.take_mana(i, best)
    s.ev(f"　名犬機 ワンコピー：マナゾーンの {BY_KEY[best].name} を出す")
    _out(s, i, best, "mana")


def sp_copit(s, i):
    """101匹コピット大冒険：山札の上から4枚を見て、1枚をマナゾーンに、1枚を山札の上に、残りを山札の下に置く"""
    p = s.P[i]
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best = max(top, key=E.PRI.get)
    top.remove(best)
    if top:
        worst = min(top, key=E.PRI.get)
        top.remove(worst)
        s.add_mana(i, worst, src="deck")
        s.ev(f"　101匹コピット大冒険：{BY_KEY[worst].name} をマナゾーンへ")
    for k in top:
        p.deck.insert(0, k)
    p.deck.append(best)
    s.ev(f"　101匹コピット大冒険：{BY_KEY[best].name} を山札の一番上に置く")


add("k54_wancopy", "名犬機 ワンコピー / 101匹コピット大冒険", 8, "N", power=9000, brk=2, mach=True,
    races=("jokers",), twin=(4, "N", True), pri=8, roles="acc atk",
    enter=e_wancopy, spell=sp_copit,
    text="クリーチャー側：マッハファイター、W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から1枚目をタップしてマナゾーンに置く。"
         "その後、自分のコスト7以下のクリーチャーを1体選んでもよい。そうしたら、それと同じ名前のジョーカーズを1体、"
         "自分のマナゾーンからバトルゾーンに出す（出せる組み合わせのうち重要度のいちばん高いものを選ぶ）。"
         "呪文側「101匹コピット大冒険」（コスト4・自然、S・トリガー）：自分の山札の上から4枚を見る。"
         "その中から1枚をマナゾーンに、1枚を山札の一番上に置き、残りを好きな順序で自分の山札の一番下に置く"
         "（重要度のいちばん高いものを山札の上に、いちばん低いものをマナゾーンに置く）",
    source=SRC["k54_wancopy"])


# ================================================================ 雷龍 ヴァリヴァリウス
def cx_varivarius(s, i, av):
    """自分のクリーチャーがなければ、召喚コストを3少なくする"""
    return 5 if s.ncre(i) == 0 else 8


def a_varivarius(s, i, u):
    """マジボンバー7：攻撃する時、山札の上から1枚を見て、コスト7以下のクリーチャー1体を
    自分の手札または山札の上から出してもよい"""
    p = s.P[i]
    best, src, bv = None, None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" and c.cost <= 7 and _can_out(s, i, k, "hand") and E.PRI[k] > bv:
            best, src, bv = k, "hand", E.PRI[k]
    if len(p.deck) > 1:
        k = p.deck[-1]
        c = BY_KEY[k]
        if c.kind == "C" and c.cost <= 7 and _can_out(s, i, k, "deck") and E.PRI[k] > bv:
            best, src, bv = k, "deck", E.PRI[k]
    if best is None:
        return
    if src == "hand":
        p.hand.remove(best)
    else:
        p.deck.pop()
    s.ev(f"　マジボンバー7：{BY_KEY[best].name} を{'手札' if src == 'hand' else '山札の上'}から出す")
    _out(s, i, best, src)


def ae_varivarius(s, i, u):
    """このクリーチャーの攻撃の終わりに、自分の山札の上から1枚をシールド化してもよい"""
    if u.k != K_VARI:
        return
    s.add_shield(i)


add("k54_varivarius", "雷龍 ヴァリヴァリウス", 8, "LF", power=11000, brk=2, sa=True,
    races=("nitrodragon", "dragon", "teambomber"), pri=9, roles="atk fin shd acc",
    costx=cx_varivarius, attack=a_varivarius, atkend=ae_varivarius,
    text="自分のクリーチャーがなければ、このクリーチャーの召喚コストを3少なくする。"
         "スピードアタッカー、W・ブレイカー。"
         "マジボンバー7（このクリーチャーが攻撃する時、自分の山札の上から1枚を見る。その後、"
         "コスト7以下のクリーチャーを1体、自分の手札または山札の上から出してもよい）。"
         "このクリーチャーの攻撃の終わりに、自分の山札の上から1枚をシールド化してもよい。"
         "出すクリーチャーは、手札と山札の上のうち重要度のいちばん高いものを選ぶ（全デッキ共通の決まり）",
    source=SRC["k54_varivarius"])


# ================================================================ 松苔ラックス
def e_matsukoke(s, i, u):
    """出た時、相手のクリーチャー1体を選んでもよい。次の自分のターンのはじめまで攻撃もブロックもできない"""
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　松苔ラックス：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k54_matsukoke", "松苔ラックス", 8, "W", power=3000, blocker=True, trig=True,
    races=("jokers",), pri=4, roles="trg blk dis",
    enter=e_matsukoke,
    text="S・トリガー、ブロッカー。"
         "このクリーチャーがバトルゾーンに出た時、相手のクリーチャーを1体選んでもよい。"
         "次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない",
    source=SRC["k54_matsukoke"])
