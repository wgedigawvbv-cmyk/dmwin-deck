"""cardspec1.json の29枚（「青寂の精霊龍 カーネル」は env2 で実装済みなので除く）

  dmwiki の本文で確かめ直して、cardspec1.json の記述を直したところ：
  ・改竄の炎 ボルメテウス・ハック：「相手のクリーチャーは出たターンに攻撃できない」はハイパーモード側の能力。
    ハイパーモードのパワーは5000（通常2000）。
  ・華謡の精霊カンツォーネ：破壊された時に動かすのは「墓地にある」下のカード。
  ・ハンプティ・ルピア：種族は「アーマード・ファイアー・バード」。G・ストライクあり。
  ・～西方より来る激流の竜騎公～：5つ目の能力は「クリーチャーが自分（プレイヤー）を攻撃する時」。
  ・王導聖霊 アルファディオス：NEOドリーム・クリーチャー（ドリーム・クリーチャー）。
  ・闘門の精霊ウェルキウス：コスト軽減はない。「出た時」と「バトルに勝った時」は同じ1つの能力。
  ・コレンココ・タンク：ガードマンあり。クリーチャー側にW・ブレイカーはない。
  ・マーシャル・クロウラー：シールド化した枚数と同じ数、自分のシールドを自分でブレイクする。
  ・邪脳の魔法陣：G・ストライクあり。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, free_play, worst_hand
from envcards.env0 import guardman, fx_dream, race_like, star_evo_rep

W = "https://dmwiki.net/"


# ================================================================ 共通の小道具
def shield_to_hand(s, i):
    """自分のシールドを1つ手札に加える（そのS・トリガーは使えない）。加えたら True"""
    p = s.P[i]
    if not p.sh:
        return False
    j = len(p.sh) - 1
    while j >= 0 and p.sh[j][1]:          # 表向きのシールド（城など）は残す
        j -= 1
    if j < 0:
        j = len(p.sh) - 1
    p.hand.append(p.sh.pop(j)[0])
    s.shield_left()
    return True


def ramp1(s, i):
    """山札の上から1枚をタップしてマナゾーンへ。置いたカードを返す（置けなければ None）"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return None
    k = p.deck.pop()
    if s.has(1 - i, "robin"):
        p.deck.insert(0, k)
        return None
    s.add_mana(i, k, True, src="deck")
    return k


def raid(s, i, u, n=3):
    """超魂レイド：山札の上からn枚を表向きにし、進化元にできるカード1枚を下に置く。残りは山札の下へ"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    e = u.c.evo or ""
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.kind == "C" and not c.evo and (set(c.civ) & set(e)) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        u.under.insert(0, best)
        s.ev(f"　超魂レイド：{BY_KEY[best].name} を下に置く")
    for k in top:
        p.deck.insert(0, k)


def meclaid(s, i, n, pred):
    """メクレイドN：山札の上から3枚を見て、条件に合うコストN以下のクリーチャー1体をただで出す。残りは山札の下へ"""
    p = s.P[i]
    m = min(3, len(p.deck) - 1)
    if m <= 0:
        return
    top = [p.deck.pop() for _ in range(m)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > n or (c.evo and not c.neo) or not pred(c):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
    for k in top:
        p.deck.insert(0, k)
    if best is not None:
        s.ev(f"　メクレイド{n}：{BY_KEY[best].name}")
        s.enter(i, best, "deck", False)


def cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたままただで唱える（墓地には行かない）"""
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


# ================================================================ 改竄の炎 ボルメテウス・ハック
def fx_bolhack(s, owner, u, i, k, src, summon, res):
    """相手のクリーチャーは、相手の手札以外のゾーンからは出られない"""
    if i != owner and src != "hand":
        return "no"
    return res


def w_entturn(s, i, u):
    """出たターンを覚えておく（ハイパーモードの「出たターンに攻撃できない」の判定用）"""
    if u.c.kind == "C":
        u.x["ent_t"] = s.turn


def al_bolhack(s, i, u):
    """ハイパーモードのボルメテウス・ハックが相手にいれば、このターン出たクリーチャーは攻撃できない"""
    if u.x.get("ent_t") != s.turn:
        return False
    for z in s.P[1 - i].board:
        if z.k == "e_bolhack" and z.hyper:
            return True
    return False


add("e_bolhack", "改竄の炎 ボルメテウス・ハック", 2, "W", power=2000, zrush=True,
    races=("millionflame", "hyperbeast"), pri=4, roles="dis",
    fatex=fx_bolhack, enterwatch=w_entturn, atklock=al_bolhack,
    powerx=lambda s, i, u, atk: 3000 if u.hyper else 0,
    text="相手のクリーチャーは、相手の手札以外のゾーンからは出られない（踏み倒し・蘇生封じ）。"
         "Zラッシュ：シールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する。"
         "ハイパーモード中はパワー5000になり、相手のクリーチャーは出たターンに攻撃できない",
    source=W + "《改竄の炎 ボルメテウス・ハック》")


# ================================================================ 煌ノ裁徒 ダイヤモン星
def ca_daiyamon(s, i, k, n):
    """相手がカードを使うコストを少なくする能力を無効にする（基本コストまで戻す）"""
    if n <= 0:
        return n
    for z in s.P[1 - i].board:
        if z.k == "e_daiyamon":
            return max(n, BY_KEY[k].cost)
    return n


def gs_daiyamon(s, i, cards):
    """ほかのコスト軽減の後に効かせたいので、この判定をコスト変化の列の最後へ回す"""
    if ca_daiyamon in E.COSTAURA and E.COSTAURA[-1] is not ca_daiyamon:
        E.COSTAURA.remove(ca_daiyamon)
        E.COSTAURA.append(ca_daiyamon)


add("e_daiyamon", "煌ノ裁徒 ダイヤモン星", 2, "L", power=2500, blocker=True, noatkp=True, gs=True,
    races=("metallica", "sabakist", "rexstars"), pri=5, roles="blk trg dis",
    costaura=ca_daiyamon, gamestart=gs_daiyamon,
    text="G・ストライク（手札に加える時、相手のクリーチャー1体を選び、このターン攻撃できなくする）。ブロッカー。"
         "このクリーチャーは相手プレイヤーを攻撃できない。"
         "相手がカードを使うコストを少なくする能力は無効になる（コストを支払わずに使う能力は使える）",
    note="コスト軽減の無効化は「基本コストまで戻す」として書いたので、代替コストの札も基本コストに戻る",
    source=W + "《煌ノ裁徒 ダイヤモン星》")


# ================================================================ 華謡の精霊カンツォーネ
def e_canzone(s, i, u):
    raid(s, i, u, 3)
    t = s.target(i, kinds="CTX")
    if t is not None:
        s.ev(f"　カンツォーネ：{t.c.name} をシールド化")
        move(s, i, t, "shield")


def d_canzone(s, i, u):
    """破壊された時、下にあったカードを墓地から、NEO・進化クリーチャーの下か、表向きのシールドにする"""
    p = s.P[i]
    ks = []
    for k in u.under:
        if k in p.grave:
            p.grave.remove(k)
            ks.append(k)
    if not ks:
        return
    tgt = None
    for z in p.board:
        if z.c.kind == "C" and (z.c.neo or z.c.evo):
            tgt = z
            break
    if tgt is not None:
        tgt.under.extend(ks)
        s.ev(f"　カンツォーネ：下にあった{len(ks)}枚を {tgt.c.name} の下へ")
        return
    k = max(ks, key=E.PRI.get)
    ks.remove(k)
    if s.add_shield(i, k, up=True):
        s.ev(f"　カンツォーネ：{BY_KEY[k].name} を表向きのシールドに")
    else:
        ks.append(k)
    for x in ks:
        p.grave.append(x)


add("e_canzone", "華謡の精霊カンツォーネ", 4, "L", power=5500, evo="LWN", neo=True, blocker=True,
    races=("magic", "angelcommand", "command"), pri=7, roles="blk rem shd",
    enter=e_canzone, destroyed=d_canzone,
    text="NEO進化（自分の光・水・自然のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。ブロッカー。"
         "超魂レイド：出た時、山札の上から3枚を表向きにし、進化元にできるカード1枚をこの下に置いてよい（残りは山札の下）。"
         "出た時、相手のエレメント1つを選んでシールド化してもよい。"
         "破壊された時、下にあったカードを墓地から、自分のNEO・進化クリーチャー1体の下に置くか、表向きのシールドにする",
    note="最後の能力で「すべてを1つのシールドにする」部分は、このシミュレーターが1つのシールドに複数枚を持てないため、"
         "1枚だけを表向きのシールドにし、残りは墓地に残す近似にした",
    source=W + "《華謡の精霊カンツォーネ》")


# ================================================================ ハンプティ・ルピア
def e_humpty(s, i, u):
    o = s.P[1 - i]
    if not o.hand:
        return
    costs = {z.c.cost for z in o.board if z.c.kind == "C" and not z.jd}
    k = max(o.hand, key=lambda x: (1 if BY_KEY[x].cost in costs else 0, E.PRI[x]))
    before = o.hand.count(k)
    s.discard(1 - i, k)
    if o.hand.count(k) == before:          # マッドネスなどで捨てられなかった
        return
    n = BY_KEY[k].cost
    t = s.target(i, lambda z: z.c.cost == n)
    if t is not None:
        destroy(s, i, t)


add("e_humpty", "ハンプティ・ルピア", 3, "LDF", power=3500, gs=True, races=("armored", "firebird"),
    pri=5, roles="dis rem trg", enter=e_humpty,
    text="G・ストライク。出た時、相手の手札を見て1枚選んで捨てさせる。その後、捨てさせたカードと同じコストの"
         "相手のクリーチャー1体を選んで破壊する（捨てられなければ破壊しない）",
    source=W + "《ハンプティ・ルピア》")


# ================================================================ カクラリコ
def w_kakurariko(s, i, u):
    """相手のクリーチャーが召喚以外で出た時、それを山札の下に置く"""
    if u.c.kind != "C" or u.x.get("summoned"):
        return
    for z in s.P[1 - i].board:
        if z.k == "e_kakurariko":
            s.ev(f"　カクラリコ：{u.c.name} を山札の下へ")
            move(s, 1 - i, u, "deck")
            return


def l_kakurariko(s, i, u, dest):
    """相手のターン中に離れた時、1枚引いて1枚捨てる"""
    if s.tp == i:
        return
    s.draw(i)
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)


add("e_kakurariko", "カクラリコ", 2, "W", power=2000, races=("cyberlord",), pri=4, roles="dis draw",
    enterwatch=w_kakurariko, left=l_kakurariko,
    text="相手のクリーチャーが召喚以外の方法で出た時、そのクリーチャーを山札の下に置く（S・トリガーなどの召喚には働かない）。"
         "相手のターン中にこのクリーチャーが場を離れた時、1枚引いて手札を1枚捨てる",
    source=W + "《カクラリコ》")


# ================================================================ ～西方より来る激流の竜騎公～
def cx_seihou(s, i, av):
    return 3 if s.evo_src(i, "e_seihou") is not None else 6


def e_seihou(s, i, u):
    p = s.P[i]
    s.draw(i, 3)
    k = worst_hand(s, i)
    if k is not None and k in p.hand:
        p.hand.remove(k)
        p.deck.append(k)
        s.ev(f"　手札の {BY_KEY[k].name} を山札の上に置く")


def w_seihou(s, i, u):
    """各ターン1度、クリーチャーが自分（プレイヤー）を攻撃する時、山札の上の1枚を見て、使うか手札に加える"""
    me = 1 - i
    p = s.P[me]
    if p.x.get("seihou_t") == s.turn or len(p.deck) <= 1:
        return
    if not any(z.k == "e_seihou" for z in p.board):
        return
    p.x["seihou_t"] = s.turn
    n = len(p.hand)
    k = p.deck.pop()
    p.hand.append(k)
    s.ev(f"　竜騎公：山札の上の {BY_KEY[k].name} を見る")
    if BY_KEY[k].cost <= n:
        free_play(s, me, k)


add("e_seihou", "～西方より来る激流の竜騎公～", 6, "W", power=6000, brk=2, evo="LWD", neo=True,
    races=("liquid", "poseidia", "dragon", "steamknight"), pri=8, roles="draw trg",
    costx=cx_seihou, enter=e_seihou, atkwatch=w_seihou,
    text="NEO進化（自分の光・水・闇のクリーチャー1体の上に置いてもよい）。NEO進化として召喚するなら召喚コストが3少ない。"
         "W・ブレイカー。出た時、3枚引き、手札を1枚山札の上に置く。"
         "各ターン1度、クリーチャーが自分を攻撃する時、山札の上の1枚を見て、自分の手札の枚数以下のコストなら"
         "コストを支払わずに使ってよい。使わないなら手札に加える",
    note="コスト軽減は「進化元が場にいればコスト3」として書いた（このシミュレーターは召喚の前に進化かどうかを決められない）",
    source=W + "《～西方より来る激流の竜騎公～》")


# ================================================================ ボルシャック・ドリーム・ドラゴン
def cx_bolsdream(s, i, av):
    n = sum(1 for k in s.P[i].mana if "dragon" in BY_KEY[k].races)
    return 4 if n >= 4 else 7


def w_bolsdream(s, i, u):
    """各ターン1度、自分のドラゴンが出た時、相手のクリーチャー1体をタップする"""
    if u.c.kind != "C" or "dragon" not in u.c.races:
        return
    for z in s.P[i].board:
        if z.k == "e_bolsdream" and z.x.get("tap_t") != s.turn:
            z.x["tap_t"] = s.turn
            t = s.target(i, lambda x: not x.tap) or s.target(i)
            if t is not None:
                t.tap = True
                s.ev(f"　ボルシャック・ドリーム・ドラゴン：{t.c.name} をタップ")
            return


def a_bolsdream(s, i, u):
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    c = BY_KEY[k]
    s.ev(f"　山札の上を表向きに：{c.name}")
    if c.kind == "C" and "dragon" in c.races and not (c.evo and not c.neo):
        s.enter(i, k, "deck", False)
    else:
        s.grave_put(i, k)


add("e_bolsdream", "ボルシャック・ドリーム・ドラゴン", 7, "LFN", power=11000, brk=2, sa=True,
    races=("armoreddragon", "dragon"), pri=11, roles="atk fin dis",
    costx=cx_bolsdream, enterwatch=w_bolsdream, attack=a_bolsdream,
    text="自分のマナゾーンにドラゴン・カードが4枚以上あれば、召喚コストが3少なくなる。スピードアタッカー、W・ブレイカー。"
         "各ターン1度、自分のドラゴンが出た時、相手のクリーチャー1体をタップしてよい。"
         "攻撃する時、山札の上から1枚を表向きにする。ドラゴンならそれを出し、それ以外は墓地に置く",
    source=W + "《ボルシャック・ドリーム・ドラゴン》")


# ================================================================ お目覚めメイ様
def _dreammates(s, i):
    return sum(1 for z in s.P[i].board if z.c.kind == "C" and "dreammate" in z.c.races)


def a_omezame(s, i, u):
    if _dreammates(s, i) >= 7:
        s.win(i, "お目覚めメイ様")


add("e_omezame", "お目覚めメイ様", 1, "N", power=1000, races=("dreammate", "hunter"), pri=3, roles="fin",
    attack=a_omezame, cantatk=lambda s, i, u: _dreammates(s, i) < 7,
    text="相手プレイヤーを攻撃してブロックされなかった時、自分のドリームメイトが7体以上いれば自分はゲームに勝つ。"
         "そうでなければその攻撃を中止する",
    note="「攻撃を中止する」は、ドリームメイトが7体未満なら攻撃できない、という近似にした。"
         "また、ブロックされた場合に勝ちにならない点と、クリーチャーを攻撃した場合は勝ちにならない点は表せていない。殿堂入り（1枚制限）",
    source=W + "《お目覚めメイ様》")


# ================================================================ 王導聖霊 アルファディオス
def cx_odoalpha(s, i, av):
    n = sum(1 for k in s.P[i].mana if "angelcommand" in BY_KEY[k].races)
    return 5 if n >= 3 else 7


def sl_odoalpha(s, i, cost):
    """相手は光ではない呪文を唱えられない"""
    if not any(z.k == "e_odoalpha" for z in s.P[1 - i].board):
        return False
    p = s.P[i]
    for k in p.hand:
        c = BY_KEY[k]
        if c.kind == "S" and c.cost == cost and "L" in c.civ:
            return False
        if c.twin and c.twin[0] == cost and "L" in c.twin[1]:
            return False
    for k in p.mana:
        c = BY_KEY[k]
        if c.kind == "S" and c.manaok and c.cost == cost and "L" in c.civ:
            return False
    return True


def a_odoalpha(s, i, u):
    p = s.P[i]
    s.draw(i, 1 + len(u.under))
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind not in ("C", "T") or "angelcommand" not in c.races:
            continue
        if c.kind == "C" and c.evo and not c.neo:
            continue
        if E.PRI[k] > bv and (c.kind != "C" or s.fate(i, k, "hand", False) == "ok"):
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　アルファディオス：手札から {BY_KEY[best].name} を出す")
        free_play(s, i, best)


add("e_odoalpha", "王導聖霊 アルファディオス", 7, "LWN", power=12500, brk=3, evo="LWN", neo=True,
    races=("angelcommand", "command"), pri=12, roles="fin draw dis",
    costx=cx_odoalpha, enter=lambda s, i, u: raid(s, i, u, 3), attack=a_odoalpha,
    spelllock=sl_odoalpha, fatex=fx_dream,
    text="ドリーム・クリーチャー。自分のマナゾーンにエンジェル・コマンド・カードが3枚以上あれば、光／水／自然の5マナで召喚してよい。"
         "NEO進化（自分の光・水・自然のクリーチャー1体の上に置いてもよい）。"
         "超魂レイド：出た時、山札の上から3枚を表向きにし、進化元にできるカード1枚をこの下に置いてよい。T・ブレイカー。"
         "相手は光以外の呪文を唱えられない。"
         "攻撃する時、このクリーチャーに含まれるカード1枚につき1枚引いてよい。その後、エンジェル・コマンドを1つ手札から出してよい",
    note="「光以外の呪文を唱えられない」は、エンジンが呪文のコストしか渡さないため「同じコストの光の呪文が手札にあれば唱えられる」"
         "という近似にした。ドリーム・クリーチャーのデッキ1枚制限は archetypes.LIMIT に書けていない",
    source=W + "《王導聖霊 アルファディオス》")


# ================================================================ 「大蛇」の鬼 ジャドク丸
def _onitime(s):
    return len(s.P[0].sh) + len(s.P[1].sh) <= 6


def e_jadoku(s, i, u):
    shield_to_hand(s, i)
    t = s.target(i, lambda z: not z.tap)
    if t is not None:
        destroy(s, i, t)


add("e_jadoku", "「大蛇」の鬼 ジャドク丸", 3, "D", power=2000, races=("demonio", "onifuda"), pri=5,
    roles="rem draw atk", enter=e_jadoku,
    powerx=lambda s, i, u, atk: 4000 if _onitime(s) else 0,
    brkx=lambda s, i, u: 2 if _onitime(s) else None,
    text="出た時、自分のシールドを1つ手札に加える（そのS・トリガーは使えない）。"
         "その後、相手のアンタップしているクリーチャー1体を選んで破壊する。"
         "鬼タイム：自分と相手のシールドの合計が6つ以下なら、パワー+4000されW・ブレイカーを得る",
    source=W + "《「大蛇」の鬼 ジャドク丸》")


# ================================================================ 冒険妖精ポレコ
def bw_poreko(s, ai, di, n):
    a = s.atk
    if a is not None and a.k == "e_poreko":
        a.x["broke"] = s.turn


def t_poreko(s, i, u):
    if u.x.get("broke") == s.turn:
        s.ev("　ポレコ：手札に戻る")
        s.leave(i, u, "hand")


add("e_poreko", "冒険妖精ポレコ", 1, "N", power=2000, races=("snow", "rexstars"), pri=3, roles="atk",
    breakwatch=bw_poreko, tend=t_poreko,
    text="自分のターンの終わりに、このターン中にこのクリーチャーがシールドをブレイクしていたら、このクリーチャーを手札に戻す",
    source=W + "《冒険妖精ポレコ》")


# ================================================================ ヘルコプ太の心絵
add("e_herukoputa", "ヘルコプ太の心絵", 1, "N", kind="T", races=("jokers", "rexstars"), pri=3, roles="draw",
    enter=lambda s, i, u: s.dig(i, 4, lambda k: BY_KEY[k].kind == "C" and bool(BY_KEY[k].evo)),
    text="シンカライズ（このタマシードをクリーチャーであるかのように、この上に進化クリーチャーを置いてよい）。"
         "出た時、山札の上から4枚を見て、その中から進化クリーチャー1体を相手に見せて手札に加えてよい（残りは山札の下）",
    source=W + "《ヘルコプ太の心絵》")
E.SHINKA.add("e_herukoputa")


# ================================================================ 禁断英雄 モモキングダムX
def _momox_n(z):
    return 1 + len(z.under)


def _momox_full(s, i, z):
    """含まれるカードが6枚になった：このターン、相手のクリーチャーすべてのパワーを-99999する"""
    o = s.P[1 - i]
    s.ev("　モモキングダムX：相手のクリーチャーすべてのパワーを-99999")
    for x in o.board[:]:
        if x.c.kind != "C" or x not in o.board:
            continue
        x.pw -= 99999
        if s.power(1 - i, x) <= 0:
            s.leave(1 - i, x, "grave", by_opp=True, destroy=True)


def e_momox(s, i, u):
    """禁断スター進化：進化ではないレクスターズが出るまで表向きにし、それを下に置く。その後シャッフル"""
    p = s.P[i]
    seen = []
    while len(p.deck) > 1:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and not c.evo and "rexstars" in c.races:
            u.under.insert(0, k)
            s.ev(f"　禁断スター進化：{c.name} を下に置く")
            break
        seen.append(k)
    p.deck.extend(seen)
    s.rng.shuffle(p.deck)
    if _momox_n(u) >= 6:
        _momox_full(s, i, u)


def w_momox(s, i, u):
    """自分の他のレクスターズが出た時、山札の上から1枚をこのクリーチャーの下に置いてよい"""
    if u.c.kind != "C" or "rexstars" not in u.c.races:
        return
    p = s.P[i]
    for z in p.board:
        if z.k != "e_momokingdamx" or z is u:
            continue
        if len(p.deck) <= 1:
            return
        before = _momox_n(z)
        z.under.insert(0, p.deck.pop())
        if before < 6 <= _momox_n(z):
            _momox_full(s, i, z)
        return


add("e_momokingdamx", "禁断英雄 モモキングダムX", 2, "DF", power=99999, brk=3,
    evo="star", neo=True, evox=lambda s, i, u: False,      # スター進化：進化元は場から選ばず、山札から下に置く
    races=("jokers", "kindan", "rexstars"), pri=11, roles="fin rem atk",
    enter=e_momox, enterwatch=w_momox, leaverep=star_evo_rep("e_momokingdamx", "モモキングダムX"),
    cantatk=lambda s, i, u: _momox_n(u) < 6,
    tgtlock=lambda s, by, u: u.k == "e_momokingdamx" and _momox_n(u) < 6,
    text="禁断スター進化：出た時、山札の上から進化ではないレクスターズが出るまで表向きにし、それをこの下に置く（その後シャッフル）。"
         "自分の他のレクスターズが出た時、山札の上から1枚をこの下に置いてよい。"
         "含まれるカードが6枚以上でなければ、攻撃できず、相手に選ばれない。"
         "含まれるカードが6枚になった時、このターン、相手のクリーチャーすべてのパワーを-99999する。T・ブレイカー",
    note="禁断スター進化は「進化元を場から選ばず、召喚時に山札から下に置く」ものとして、普通に召喚できるカードとして書いた"
         "（離れる時に一番上の1枚だけが離れる＝退化は実装してある）。"
         "プレミアム殿堂コンビ（《未来王龍 モモキングJO》との同時使用禁止）はカードプールに相手がいないので扱っていない",
    source=W + "《禁断英雄 モモキングダムX》")


# ================================================================ 紅き団長 ドギラゴン悪
def _dogiaku_src(c):
    return c.kind == "C" and bool(set("DF") & set(c.civ)) and "dragon" in c.races and c.cost >= 5


def e_dogiaku(s, i, u):
    """ファイナル革命：革命チェンジで出た時、山札の上2枚を墓地に置き、墓地からコスト7以下の多色クリーチャーを出す"""
    p = s.P[i]
    if s.atk is not u or p.x.get("finrev_t") == s.turn:
        return
    p.x["finrev_t"] = s.turn
    s.ev("　ファイナル革命：山札の上2枚を墓地に置く")
    s.mill(i, 2)
    s.revive(i, lambda c: c.cost <= 7 and E.MULTI[c.key])


def w_dogiaku(s, i, u):
    """各ターン1度、自分の多色クリーチャーが出た時、相手のクリーチャー1体とバトルさせる"""
    if u.c.kind != "C" or not E.MULTI[u.k]:
        return
    for z in s.P[i].board:
        if z.k != "e_dogiaku" or z.x.get("btl_t") == s.turn:
            continue
        t = s.target(i)
        if t is None:
            return
        z.x["btl_t"] = s.turn
        s.ev(f"　ドギラゴン悪：{t.c.name} とバトル")
        s.battle(i, z, 1 - i, t)
        return


add("e_dogiaku", "紅き団長 ドギラゴン悪", 8, "DF", power=13000, brk=3, sa=True,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=12, roles="fin atk rem",
    enter=e_dogiaku, enterwatch=w_dogiaku,
    changex=lambda s, i, u: _dogiaku_src(u.c),
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and _dogiaku_src(BY_KEY[kk])) >= 3
    else "革命チェンジの元になる闇か火のコスト5以上のドラゴンが3体いない",
    text="革命チェンジ（闇か火のコスト5以上のドラゴンが攻撃する時、入れ替えて出せる）。スピードアタッカー、T・ブレイカー。"
         "各ターン1度、自分の多色クリーチャーが出た時、相手のクリーチャー1体を選び、このクリーチャーとバトルさせてよい。"
         "ファイナル革命：革命チェンジで出た時、このターンまだ他のファイナル革命を使っていなければ、山札の上から2枚を墓地に置き、"
         "自分の墓地からコスト7以下の多色クリーチャー1体を出す",
    source=W + "《紅き団長 ドギラゴン悪》")


# ================================================================ サイバー・チューン
def sp_cybertune(s, i):
    s.draw(i, 3)
    for _ in range(2):
        k = worst_hand(s, i)
        if k is None:
            break
        s.discard(i, k)


add("e_cybertune", "サイバー・チューン", 3, "W", kind="S", trig=True, pri=4, roles="draw trg", spell=sp_cybertune,
    text="S・トリガー。3枚引き、その後、自分の手札を2枚捨てる",
    source=W + "《サイバー・チューン》")


# ================================================================ 黄昏ミミ＆トワイライトMk.3 -挑戦のヒロイン-
def e_tasogaremimi(s, i, u):
    n = 8 if u.under else 5
    meclaid(s, i, n, lambda c: race_like(c, "cyber"))


def w_tasogaremimi(s, i, u):
    """各ターン1度、自分の他のサイバー・クリーチャーが出た時、クリーチャー1体を持ち主の手札に戻してよい"""
    if u.c.kind != "C" or not race_like(u.c, "cyber"):
        return
    for z in s.P[i].board:
        if z.k != "e_tasogaremimi" or z is u or z.x.get("bn_t") == s.turn:
            continue
        t = s.target(i)
        if t is None:
            return
        z.x["bn_t"] = s.turn
        s.ev(f"　黄昏ミミ：{t.c.name} を持ち主の手札へ")
        move(s, i, t, "hand")
        return


add("e_tasogaremimi", "黄昏ミミ＆トワイライトMk.3 -挑戦のヒロイン-", 5, "W", power=8000, brk=2, evo="W", neo=True,
    races=("cybercommand", "command"), pri=8, roles="rem atk draw",
    enter=e_tasogaremimi, enterwatch=w_tasogaremimi,
    text="NEO進化（自分の水のクリーチャー1体の上に置いてもよい）。W・ブレイカー。"
         "出た時、これが進化クリーチャーならサイバー・メクレイド8、進化クリーチャーでなければサイバー・メクレイド5を行う"
         "（山札の上から3枚を見て、その中からコスト以下のサイバー・クリーチャー1体をただで出す。残りは山札の下）。"
         "各ターン1度、自分の他のサイバー・クリーチャーが出た時、クリーチャー1体を選び、持ち主の手札に戻してよい",
    source=W + "《黄昏ミミ＆トワイライトMk.3 -挑戦のヒロイン-》")


# ================================================================ コレンココ・タンク / ボント・プラントボ
def e_korenkoko(s, i, u):
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    for k in top:
        c = BY_KEY[k]
        if c.kind == "C" and c.power >= 12000:
            p.hand.append(k)
            s.ev(f"　コレンココ・タンク：{c.name} を手札に")
        else:
            s.add_mana(i, k, True, src="deck")


def sp_korenkoko(s, i):
    k = ramp1(s, i)
    if k is not None and BY_KEY[k].kind == "C" and BY_KEY[k].power >= 12000:
        ramp1(s, i)


add("e_korenkoko", "コレンココ・タンク / ボント・プラントボ", 6, "N", power=12000, noatkp=True,
    races=("gransect",), twin=(3, "N", False), pri=8, roles="acc draw blk",
    enter=e_korenkoko, spell=sp_korenkoko, guard=guardman("e_korenkoko"),
    text="クリーチャー側：ガードマン。このクリーチャーは相手プレイヤーを攻撃できない。"
         "出た時、山札の上から3枚を表向きにし、その中のパワー12000以上のクリーチャーを好きな数手札に加え、"
         "残りをタップしてマナゾーンに置く。"
         "呪文側「ボント・プラントボ」（コスト3）：山札の上から1枚をマナゾーンに置く。"
         "それがパワー12000以上のクリーチャーなら、もう1枚マナゾーンに置く",
    source=W + "《コレンココ・タンク／ボント・プラントボ》")


# ================================================================ ROYAL-減亜5
def e_royalgenia(s, i, u):
    p = s.P[i]
    if not p.hand:
        return
    neo = [k for k in p.hand if BY_KEY[k].neo]
    k = min(neo, key=E.PRI.get) if neo else worst_hand(s, i)
    if k is None or k not in p.hand:
        return
    p.hand.remove(k)
    s.add_mana(i, k, True, src="hand")
    s.ev(f"　ROYAL-減亜5：手札の {BY_KEY[k].name} をタップしてマナへ")
    if BY_KEY[k].neo:
        s.draw(i)


add("e_royalgenia", "ROYAL-減亜5", 2, "N", power=1000, races=("dreammate", "technosamurai"), pri=4,
    roles="acc draw", enter=e_royalgenia,
    text="出た時、自分の手札を1枚、タップしてマナゾーンに置いてよい。そのカードがNEOクリーチャーなら1枚引く",
    source=W + "《ROYAL-減亜5》")


# ================================================================ 邪脳の魔法陣
def e_janou(s, i, u):
    p = s.P[i]
    s.mill(i, 3)
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > 4 or E.PRI[k] <= bv:
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　邪脳の魔法陣：墓地から {BY_KEY[best].name} をただで使う")
        free_play(s, i, best, "grave")


def cg_janou(s, i):
    """自分の手札からマナゾーンに置いた時、アンタップして置く（多色の置きタップを戻す）"""
    p = s.P[i]
    if p.mused > 0:
        p.mused -= 1


add("e_janou", "邪脳の魔法陣", 5, "LWD", kind="T", gs=True, races=("demoncommand", "command"), pri=6,
    roles="trg acc", enter=e_janou, chargex=cg_janou,
    text="G・ストライク。シンカライズ（このタマシードの上に進化クリーチャーを置いてよい）。"
         "出た時、自分の山札の上から3枚を墓地に置いてよい。その後、自分の墓地からコスト4以下のクリーチャーではないカード1枚を"
         "コストを支払わずに使ってよい。このカードを自分の手札からマナゾーンに置いた時、アンタップして置く",
    source=W + "《邪脳の魔法陣》")
E.SHINKA.add("e_janou")


# ================================================================ パクリオ
def e_pakurio(s, i, u):
    o = s.P[1 - i]
    if not o.hand:
        return
    k = max(o.hand, key=E.PRI.get)
    o.hand.remove(k)
    if s.add_shield(1 - i, k):
        s.ev(f"　パクリオ：相手の手札の {BY_KEY[k].name} を相手のシールドに")
    else:
        o.hand.append(k)


add("e_pakurio", "パクリオ", 4, "W", power=1000, races=("cyberlord",), pri=5, roles="dis", enter=e_pakurio,
    text="出た時、相手の手札を見て1枚選び、そのカードを相手のシールドとして置いてよい（相手はそのカードを使えなくなる）",
    source=W + "《パクリオ》")


# ================================================================ 闘門の精霊ウェルキウス
def _welkius_go(s, i):
    p = s.P[i]
    s.draw(i)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or not c.blocker or (c.evo and not c.neo):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is not None and best in p.hand:
        p.hand.remove(best)
        s.ev(f"　ウェルキウス：手札から {BY_KEY[best].name} を出す")
        s.enter(i, best, "hand", False)


def bf_welkius(s, ai, au, di, du, a_dies, d_dies):
    """自分のクリーチャーがバトルに勝った時にも働く"""
    for j, win, lose in ((ai, not a_dies, d_dies), (di, not d_dies, a_dies)):
        if win and lose and not s.over and any(z.k == "e_welkius" for z in s.P[j].board):
            _welkius_go(s, j)
    return a_dies, d_dies


add("e_welkius", "闘門の精霊ウェルキウス", 9, "L", power=7500, brk=2, blocker=True,
    races=("angelcommand", "command"), pri=11, roles="blk draw fin",
    enter=lambda s, i, u: _welkius_go(s, i), battlefx=bf_welkius,
    text="ブロッカー、W・ブレイカー。このクリーチャーが出た時、または自分のクリーチャーがバトルに勝った時、1枚引く。"
         "その後、ブロッカーを持つクリーチャー1体を自分の手札から出してよい",
    source=W + "《闘門の精霊ウェルキウス》")


# ================================================================ 豪運の絆
def sp_gouun(s, i):
    p = s.P[i]
    t = s.target(i)
    if t is not None and E.PRI[t.k] >= 5:
        move(s, i, t, "hand")
        return
    n = 0
    for _ in range(2):
        k = worst_hand(s, i)
        if k is None or k not in p.hand:
            break
        p.hand.remove(k)
        p.deck.insert(0, k)
        n += 1
    s.draw(i, n + 1)


add("e_gouun", "豪運の絆", 2, "WF", kind="S", trig=True, pri=4, roles="draw rem trg", spell=sp_gouun,
    text="S・トリガー。次のうちいずれか1つを選ぶ。"
         "(a) 自分の手札を2枚まで山札の下に置き、その後、置いた枚数より1枚多く引く。"
         "(b) 相手のクリーチャー1体を選び、持ち主の手札に戻す",
    source=W + "《豪運の絆》")


# ================================================================ 超竜バジュラズテラ
def e_bajurasutera(s, i, u):
    for j in (0, 1):
        q = s.P[j]
        for k in q.mana[:]:
            if "dragon" in BY_KEY[k].races:
                continue
            if k in q.mana:
                s.take_mana(j, k)
                s.grave_put(j, k)
    s.ev("　バジュラズテラ：両者のマナゾーンからドラゴン以外を墓地へ")


add("e_bajurasutera", "超竜バジュラズテラ", 9, "F", power=12000, brk=3, evo="dragon",
    races=("armoreddragon", "dragon"), pri=12, roles="rem fin",
    enter=e_bajurasutera, evox=lambda s, i, u: "dragon" in u.c.races,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                        and "dragon" in BY_KEY[kk].races) >= 4
    else "進化元になるドラゴン・クリーチャーが4体いない",
    text="進化（自分のドラゴン・クリーチャー1体の上に置く）。T・ブレイカー。"
         "出た時、各プレイヤーは、ドラゴン・カード以外のカードをすべて自分のマナゾーンから墓地に置く",
    source=W + "《超竜バジュラズテラ》")


# ================================================================ フェアリー・ギフト
def sp_fairygift(s, i):
    s.P[i].x["gift"] = s.turn
    s.ev("　フェアリー・ギフト：次に召喚するクリーチャー1体のコストを3少なくする")


def ca_gift(s, i, k, n):
    if n <= 1 or BY_KEY[k].kind != "C":
        return n
    if s.P[i].x.get("gift") == s.turn:
        return max(1, n - 3)
    return n


def w_gift(s, i, u):
    """1体召喚したら軽減を使い切る"""
    p = s.P[i]
    if p.x.get("gift") == s.turn and u.x.get("summoned") and s.tp == i:
        p.x["gift"] = -1


add("e_fairygift", "フェアリー・ギフト", 1, "N", kind="S", pri=3, roles="acc",
    spell=sp_fairygift, costaura=ca_gift, enterwatch=w_gift,
    text="このターン、次に召喚する自分のクリーチャー1体の召喚コストを3少なくする（1より下がらない）",
    note="プレミアム殿堂（公式ルールでは使えない）",
    source=W + "《フェアリー・ギフト》")


# ================================================================ 闘争類拳嘩目 ステゴロ・カイザー / お清めシャラップ
def a_stegoro(s, i, u):
    p = s.P[i]
    ramp1(s, i)
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        if E.PRI[k] >= 5:
            s.take_mana(i, k)
            p.hand.append(k)
            s.ev(f"　ステゴロ・カイザー：マナから {BY_KEY[k].name} を手札へ")


def sp_stegoro(s, i):
    p = s.P[i]
    ramp1(s, i)
    if len(p.deck) <= 6 and p.grave:
        ks = p.grave[:]
        del p.grave[:]
        p.deck.extend(ks)
        s.rng.shuffle(p.deck)
        s.ev(f"　お清めシャラップ：自分の墓地{len(ks)}枚を山札に加えてシャッフル")
        return
    o = s.P[1 - i]
    if o.grave:
        ks = o.grave[:]
        del o.grave[:]
        o.deck.extend(ks)
        s.rng.shuffle(o.deck)
        s.ev(f"　お清めシャラップ：相手の墓地{len(ks)}枚を山札に加えてシャッフル")


add("e_stegoro", "闘争類拳嘩目 ステゴロ・カイザー / お清めシャラップ", 7, "N", power=9000, brk=2, mach=True,
    races=("jurassiccommanddragon", "command", "dragon", "hunter"), twin=(3, "N", False), pri=9,
    roles="acc atk dis", attack=a_stegoro, spell=sp_stegoro,
    text="クリーチャー側：マッハファイター、W・ブレイカー。攻撃する時、自分の山札の上から1枚をマナゾーンに置き、"
         "その後、自分のマナゾーンからカード1枚を手札に戻してよい。"
         "呪文側「お清めシャラップ」（コスト3）：自分の山札の上から1枚をマナゾーンに置く。その後、プレイヤー1人の墓地から"
         "カードを好きな枚数選び、そのプレイヤーはそれを山札に加えてシャッフルする",
    source=W + "《闘争類拳嘩目 ステゴロ・カイザー／お清めシャラップ》")


# ================================================================ サケビ・ポエムシャウター / ♪いつまでも オレ様の歌は 終わらねぇ
def sp_sakebi(s, i):
    mine = [z for z in s.P[i].board if z.c.kind == "C" and z.tap]
    if mine:
        z = max(mine, key=lambda x: s.power(i, x))
        z.tap = False
        s.ev(f"　♪いつまでも：{z.c.name} をアンタップ")
    s.break_sh(i, 1)


def bf_sakebi(s, ai, au, di, du, a_dies, d_dies):
    """自分のクリーチャーがバトルに勝った時、呪文側をバトルゾーンに置いたままただで唱えてよい"""
    for j, win, lose in ((ai, not a_dies, d_dies), (di, not d_dies, a_dies)):
        if not (win and lose) or s.over:
            continue
        for z in s.P[j].board:
            if z.k == "e_sakebi":
                s.ev("　サケビ・ポエムシャウター：呪文側をただで唱える")
                cast_inplace(s, j, "e_sakebi", 4, sp_sakebi)
                break
    return a_dies, d_dies


add("e_sakebi", "サケビ・ポエムシャウター / ♪いつまでも オレ様の歌は 終わらねぇ", 5, "F", power=6000, brk=2, sa=True,
    races=("magic", "beatjockey"), twin=(4, "F", False), pri=8, roles="atk fin",
    spell=sp_sakebi, battlefx=bf_sakebi,
    powerx=lambda s, i, u, atk: 3000 if atk else 0,
    text="クリーチャー側：スピードアタッカー、W・ブレイカー。バトル中、このクリーチャーのパワーは+3000される。"
         "自分のクリーチャーがバトルに勝った時、このカードの呪文側を、バトルゾーンに置いたままコストを支払わずに唱えてよい。"
         "呪文側「♪いつまでも オレ様の歌は 終わらねぇ」（コスト4）：自分のクリーチャー1体をアンタップし、相手のシールドを1つブレイクする",
    note="「バトル中+3000」は、このクリーチャーが攻撃している時だけ反映している"
         "（相手の攻撃を受ける側のバトルでは、エンジンにバトル中かどうかを知る手がかりがないため反映していない）",
    source=W + "《サケビ・ポエムシャウター／♪いつまでも オレ様の歌は 終わらねぇ》 , "
               "https://yuyu-tei.jp/sell/dm/card/dm23rp4/10005")


# ================================================================ ヤット・パウル
add("e_yattopaul", "ヤット・パウル", 2, "D", power=2000, races=("firebird",), pri=4, roles="draw",
    enter=lambda s, i, u: shield_to_hand(s, i),
    text="出た時、自分のシールドを1つ手札に加える（そのS・トリガーは使えない）",
    source=W + "《ヤット・パウル》 , https://yuyu-tei.jp/sell/dm/card/dmex17/10121")


# ================================================================ マーシャル・クロウラー
def e_marshalcrawler(s, i, u):
    """手札を好きな枚数シールド化し、その後、同じ数の自分のシールドをブレイクする"""
    p = s.P[i]
    cands = []
    for k in p.hand:
        c = BY_KEY[k]
        if c.trig or (c.twin and c.twin[2]) or c.gs:
            cands.append(k)
    cands.sort(key=E.PRI.get, reverse=True)
    n = 0
    for k in cands[:3]:
        if k not in p.hand:
            continue
        p.hand.remove(k)
        if s.add_shield(i, k):
            n += 1
        else:
            p.hand.append(k)
    if n:
        s.ev(f"　マーシャル・クロウラー：手札{n}枚をシールド化し、自分のシールドを{n}つブレイク")
        s.break_sh(1 - i, n)


add("e_marshalcrawler", "マーシャル・クロウラー", 8, "W", power=8000, brk=2, races=("eartheater",), pri=10,
    roles="shd trg draw", enter=e_marshalcrawler,
    text="W・ブレイカー。出た時、自分の手札を好きな枚数シールド化してよい。その後、このクリーチャーは同じ数の"
         "自分のシールドをブレイクする（割れたシールドのS・トリガーは使える）",
    note="シールド化する枚数は、S・トリガー／G・ストライクを持つ手札を3枚までという決め方にした",
    source=W + "《マーシャル・クロウラー》")


# ================================================================ フォース・アゲイン
def sp_forceagain(s, i):
    p = s.P[i]
    cands = [z for z in p.board if z.c.kind == "C" and not (z.c.evo and not z.c.neo)]
    if not cands:
        return
    best = max(cands, key=lambda z: (1 if z.k in E.ENTER else 0, E.PRI[z.k]))
    k = best.k
    if not s.leave(i, best, "grave", destroy=True):
        return
    if k in p.grave and s.fate(i, k, "grave", False) == "ok":
        p.grave.remove(k)
        s.ev(f"　フォース・アゲイン：{BY_KEY[k].name} を墓地から出す")
        s.enter(i, k, "grave", False)


add("e_forceagain", "フォース・アゲイン", 4, "W", kind="S", trig=True, pri=5, roles="trg rem", spell=sp_forceagain,
    text="S・トリガー。自分のクリーチャー1体を破壊し、その後、そのクリーチャーを自分の墓地からバトルゾーンに出す"
         "（「出た時」の能力をもう一度使える）",
    note="プレミアム殿堂（公式ルールでは使えない）",
    source=W + "《フォース・アゲイン》")
