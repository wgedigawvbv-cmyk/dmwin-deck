"""クローシス モウジャキンガ と ドロマーロストクルセイダー（遊々亭のデッキ紹介記事の採用リストから）

  EXライフ、キリフダッシュ、ササゲール、Jクライム、G・NEO進化、ウルトラ・セイバー、シンパシー、ハイパーエナジーなど、
  カードに書かれている仕組みをそのまま実装した。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import (discard_choice, exlife_enter, exlife_rep, fx_dream, he_costx, he_payx, lock_until_my_turn,
                           owner_of, race_cost_down)

W = "https://dmwiki.net/"
LOST = "lostcrusader"


def _lost(c):
    return LOST in c.races


# ================================================================ クローシス モウジャキンガ
def e_mouja(s, i, u):
    """出た時、相手のシールド1つ・クリーチャー1体・手札1枚（ランダム）を相手の墓地に置く"""
    exlife_enter(s, i, u)
    o = s.P[1 - i]
    if o.sh:
        j = next((j for j in range(len(o.sh) - 1, -1, -1) if not o.sh[j][1]), len(o.sh) - 1)
        o.grave.append(o.sh.pop(j)[0])
        s.shield_left()
        s.ev("　相手のシールド1つを墓地へ")
    t = s.target(i)
    if t is not None:
        move(s, i, t, "grave")
    s.discard_random(1 - i)


def ae_mouja(s, i, u):
    """攻撃の終わりに、1枚引いて1枚捨てる。捨てたのが多色ならアンタップする"""
    if u.k != "n_mouja":
        return
    p = s.P[i]
    s.draw(i)
    if not p.hand:
        return
    multi = [k for k in p.hand if E.MULTI[k]]
    k = min(multi or p.hand, key=E.PRI.get)
    s.discard(i, k)
    if E.MULTI[k]:
        u.tap = False
        s.ev("　多色を捨てたのでモウジャキンガはアンタップする")


def w_mouja_kiri(s, i, u):
    """キリフダッシュ：自分のクリーチャーが攻撃する時、手札から水・闇・火を含む5マナで召喚してよい"""
    p = s.P[i]
    if "n_mouja" not in p.hand or s.has(i, "n_mouja"):
        return
    if len(p.mana) - p.mused < 5 or not set("WDF") <= E.civs(p):
        return
    if s.fate(i, "n_mouja", "hand", True) != "ok":
        return
    p.hand.remove("n_mouja")
    p.mused += 5
    s.ev("　キリフダッシュ：勝敵逆夢王 モウジャキンガを5マナで召喚")
    s.enter(i, "n_mouja", "hand", True)


def pay_mouja(s, i, k, n):
    """ササゲール2でコストが下がっていたら、マキシ-2を1体破壊する"""
    for z in s.P[i].board:
        if z.k == "n_maxi":
            s.ev("　ササゲール2：爆衆 マキシ-2 を破壊してコストを2下げた")
            s.leave(i, z, "grave", destroy=True)
            return


add("n_mouja", "勝敵逆夢王 モウジャキンガ", 8, "WDF", power=11000, brk=2, blocker=True, sa=True,
    races=("exdreamer", "dispector", "jokers", "dragon", "demonio"), pri=12, roles="fin rem dis blk atk draw",
    enter=e_mouja, atkend=ae_mouja, atkwatch=w_mouja_kiri, leaverep=exlife_rep, fatex=fx_dream, payx=pay_mouja,
    text="ブロッカー、スピードアタッカー、W・ブレイカー、EXライフ（出た時に山札の上から1枚を下にシールドとして置き、"
         "離れる時はかわりにそのシールドを失う）。キリフダッシュ[水/闇/火(5)]：自分のクリーチャーが攻撃する時、"
         "手札から5マナで召喚してよい。出た時、相手のシールド1つ、相手のクリーチャー1体、相手の手札1枚（ランダム）を"
         "すべて相手の墓地に置く。攻撃の終わりに、1枚引いて手札を1枚捨てる。捨てたのが多色なら、このクリーチャーをアンタップする。"
         "ドリーム・クリーチャー（同じ名前のものは場に1体まで。デッキに入れる枚数の制限はない）",
    source=W + "《勝敵逆夢王 モウジャキンガ》")


def w_maxi(s, i, u):
    """相手のマナの枚数より大きいコストの相手のクリーチャーが出た時、それを破壊する"""
    if u.c.kind != "C" or not any(z.k == "n_maxi" for z in s.P[1 - i].board):
        return
    if u.c.cost > len(s.P[i].mana) and u in s.P[i].board:
        s.ev(f"　マキシ-2：マナより大きいコストの {u.c.name} を破壊")
        s.leave(i, u, "grave", by_opp=True, destroy=True)


add("n_maxi", "爆衆 マキシ-2", 2, "F", power=2000, races=("beatjockey", "distas"), pri=5, roles="rem dis",
    enterwatch=w_maxi, costaura=race_cost_down("dispector", 2, "n_maxi"),
    text="相手のマナゾーンのカードの枚数より大きいコストを持つ相手のクリーチャーが出た時、そのクリーチャーを破壊する。"
         "ササゲール2：自分のディスペクターの召喚コストを2少なくしてよい。そうしたらこのカードを破壊する",
    source=W + "《爆衆 マキシ-2》")


def mr_ningyo(s, i, k, src):
    """相手のターン中、相手が手札以外から自分のマナゾーンに置くカードを墓地に置き換える"""
    return s.tp == i and any(z.k == "n_ningyo" for z in s.P[1 - i].board)


add("n_ningyo", "星空に浮かぶニンギョ", 2, "D", power=1000, gs=True, races=("mafigang", "rexstars"), pri=4,
    roles="dis trg", manarep=mr_ningyo,
    text="G・ストライク、スレイヤー。相手のターン中、相手が自分の手札以外から自分のマナゾーンにカードを置く時、"
         "かわりに墓地に置く（手札からのマナチャージや、手札から出ようとしたクリーチャーのマナ置き換えは止まらない）",
    source=W + "《星空に浮かぶニンギョ》")
from envcards.env0 import SLAYER                      # noqa: E402
SLAYER.add("n_ningyo")


def e_aisha(s, i, u):
    """出た時、相手の手札をランダムに1枚捨てさせる。その後、自分の手札を1枚捨ててもよく、
    そうしたら相手のクリーチャー1体のパワーをこのターン-4000する"""
    s.discard_random(1 - i)
    p = s.P[i]
    t = s.target(i)
    if t is not None and p.hand:
        k = min(p.hand, key=E.PRI.get)
        s.discard(i, k)
        t.pw -= 4000
        s.ev(f"　{t.c.name} のパワーを-4000")
        if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
            s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def swap_aisha(s, i, u):
    """Jクライム8：攻撃する時、自分の墓地のコスト8以下のジョーカーズと入れ替える"""
    p = s.P[i]
    best, bv = None, E.PRI["n_aisha"]
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind == "C" and "jokers" in c.races and c.cost <= 8 and not (c.evo and not c.neo) and E.PRI[k] > bv:
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


add("n_aisha", "アイシャセー神", 4, "D", power=4000, races=("jokers",), pri=7, roles="dis rem",
    enter=e_aisha, atkswap=swap_aisha,
    text="スレイヤー。出た時、相手の手札を1枚ランダムに捨てさせる。その後、自分の手札を1枚捨ててもよく、そうしたら"
         "相手のクリーチャー1体を選び、このターンそのパワーを-4000する。"
         "Jクライム8：このクリーチャーが攻撃する時、自分の墓地にあるコスト8以下のジョーカーズ・クリーチャー1体と"
         "入れ替えてもよい（入れ替えたこのクリーチャーは破壊として墓地に置かれ、出てきたクリーチャーが攻撃を続ける）",
    source=W + "《アイシャセー神》")
SLAYER.add("n_aisha")


def e_jazzy(s, i, u):
    """出た時、山札の上3枚を墓地に置いてもよい。その後、墓地からクリーチャー1体を手札に戻し、
    そのコスト以下の相手のクリーチャー1体を破壊する"""
    p = s.P[i]
    s.mill(i, 3)
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        if BY_KEY[k].kind == "C" and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.grave.remove(best)
    p.hand.append(best)
    n = BY_KEY[best].cost
    s.ev(f"　墓地から {BY_KEY[best].name} を手札へ（コスト{n}以下を破壊）")
    t = s.target(i, lambda z: z.c.cost <= n)
    if t is not None:
        destroy(s, i, t)


def _jazzy_evo(s, i):
    return any(z.k == "n_jazzy" and z.under for z in s.P[i].board)


add("n_jazzy", "邪龍 ジャジーブラッド", 4, "WDF", power=6000, brk=2, evo="WDF", neo=True, gneo=True,
    races=("abyss", "dragon"), pri=8, roles="rem draw atk",
    enter=e_jazzy, saok=lambda s, i, u: _jazzy_evo(s, i), unbok=lambda s, i, u: _jazzy_evo(s, i),
    text="G・NEO進化（自分の水・闇・火のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。W・ブレイカー。"
         "出た時、自分の山札の上から3枚を墓地に置いてもよい。その後、自分の墓地からクリーチャー1体を手札に戻し、"
         "そのクリーチャーのコスト以下の相手のクリーチャー1体を選んで破壊する。"
         "これが進化クリーチャーなら、自分のクリーチャーすべてにスピードアタッカーを与え、ブロックされない",
    source=W + "《邪龍 ジャジーブラッド》")


def w_bonkigo(s, i, u):
    """相手のクリーチャーが出た時、そのターン攻撃できない。ただで出されていたら1枚引いてもよい"""
    if u.c.kind != "C" or not any(z.k == "n_bonkigo" for z in s.P[1 - i].board):
        return
    u.lock = s.turn
    if not u.x.get("summoned"):
        s.draw(1 - i)


def sp_bonkigo(s, i):
    """数字を1つ選ぶ。次の自分のターンのはじめまで、そのコストの相手のクリーチャーは攻撃もブロックもできない"""
    o = s.P[1 - i]
    cnt = {}
    for z in o.board:
        if z.c.kind == "C":
            cnt[z.c.cost] = cnt.get(z.c.cost, 0) + 10 + E.PRI[z.k]
    for k in o.hand:
        cnt[BY_KEY[k].cost] = cnt.get(BY_KEY[k].cost, 0) + 1
    if not cnt:
        return
    n = max(sorted(cnt), key=cnt.get)
    o.x["froze"] = (n, s.turn + (1 if s.tp == i else 0))
    s.ev(f"　コスト{n}の相手のクリーチャーは攻撃もブロックもできない")


def _froze(s, j, u):
    fc = s.P[j].x.get("froze")
    return bool(fc and u.c.cost == fc[0] and s.turn <= fc[1])


add("n_bonkigo", "ボン・キゴマイム / ♪やせ蛙 ラッキーナンバー ここにあり", 3, "W", power=4000,
    races=("magicmarfolk",), twin=(2, "W", False), pri=6, roles="dis",
    enterwatch=w_bonkigo, spell=sp_bonkigo,
    atklock=lambda s, i, u: _froze(s, i, u), blocklock=lambda s, u: _froze(s, owner_of(s, u), u),
    text="クリーチャー側：相手のクリーチャーが出た時、そのクリーチャーはそのターン攻撃できない。さらに、それがコストを"
         "支払わずに出されていたら1枚引いてもよい。"
         "呪文側《♪やせ蛙 ラッキーナンバー ここにあり》（コスト2）：数字を1つ選ぶ。次の自分のターンのはじめまで、"
         "そのコストの相手のクリーチャーは攻撃もブロックもできない",
    source=W + "《ボン・キゴマイム／♪やせ蛙 ラッキーナンバー ここにあり》")


# ================================================================ ドロマーロストクルセイダー
add("n_wadachie", "ワダチエノミコト", 2, "W", power=1000, races=("mizugami", LOST), pri=4, roles="draw",
    enter=lambda s, i, u: s.draw(i),
    text="出た時、1枚引く", source=W + "《ワダチエノミコト》")


def e_wadashisuto(s, i, u):
    if any(z is not u and _lost(z.c) for z in s.P[i].board):
        s.draw(i)


def rep_wadashisuto(s, i, u, dest, destroy_):
    """ウルトラ・セイバー：自分のロスト・クルセイダーが離れる時、かわりにこのクリーチャーを破壊してよい"""
    if not _lost(u.c) or u.k == "n_wadashisuto":
        return False
    for z in s.P[i].board:
        if z.k == "n_wadashisuto":
            s.ev(f"　ウルトラ・セイバー：ワダシストノミコトを破壊して {u.c.name} を守る")
            s.leave(i, z, "grave", destroy=True)
            return True
    return False


def _lost_down(s, i, k):
    """ロスト・クルセイダーの呪文のコストを1下げる（ワダシストノミコト）"""
    n = BY_KEY[k].cost
    if any(z.k == "n_wadashisuto" for z in s.P[i].board):
        n = max(0, n - 1)
    return n


add("n_wadashisuto", "ワダシストノミコト", 3, "W", power=2000, races=("mizugami", LOST), pri=6, roles="draw blk",
    enter=e_wadashisuto, leaverep=rep_wadashisuto, costaura=race_cost_down(LOST, 1, "n_wadashisuto"),
    text="出た時、自分のバトルゾーンに他のロスト・クルセイダーがいれば1枚引く。自分のロスト・クルセイダー・カードの"
         "コストを1少なくする（0より下がらない。呪文にもかかる）。"
         "ウルトラ・セイバー：ロスト・クルセイダー（自分のロスト・クルセイダーが離れる時、かわりにこのクリーチャーを"
         "破壊してよい。破壊以外の離れ方も肩代わりできる）",
    source=W + "《ワダシストノミコト》")


add("n_wadakani", "ワダカニノミコト", 2, "W", power=1000, blocker=True, races=("mizugami", LOST), pri=5, roles="blk dis",
    atklock=lambda s, i, u: u.sick and any(z.k == "n_wadakani" for z in s.P[1 - i].board),
    powerx=lambda s, i, u, atk: 1000 * len(s.P[i].hand) if (u.k == "n_wadakani" and s.tp != i) else 0,
    text="ブロッカー。相手のクリーチャーは、出たターンには攻撃できない（スピードアタッカーやマッハファイターも封じる）。"
         "相手のターン中、自分の手札1枚につきこのクリーチャーのパワー+1000",
    source=W + "《ワダカニノミコト》")


add("n_wadaebi", "ワダエビノミコト", 3, "W", power=4000, gs=True, jd=True, races=("mizugami", LOST),
    meta=("LIMIT2",), pri=6, roles="dis trg",
    text="G・ストライク、ジャストダイバー。各ターン、相手はクリーチャーを2体までしか出せない",
    source=W + "《ワダエビノミコト》")


def cx_fukafuchi(s, i, av):
    """水3マナで召喚してもよい（そうしたら出た時に自分のクリーチャー1体を手札に戻す）"""
    others = [z for z in s.P[i].board if z.c.kind == "C"]
    if av >= 6 and not others:
        return 6
    return 3


def pay_fukafuchi(s, i, k, n):
    s.P[i].x["fuka_cheap"] = (n == 3)


def e_fukafuchi(s, i, u):
    if not s.P[i].x.pop("fuka_cheap", False):
        return
    p = s.P[i]
    cands = [z for z in p.board if z.c.kind == "C" and z is not u] or [u]
    z = min(cands, key=s.val)
    s.ev(f"　軽く出した代償：{z.c.name} を手札に戻す")
    s.leave(i, z, "hand")


def w_fukafuchi_lost(s, i, u):
    """自分のロスト・クルセイダーが出た時、1枚引いてもよい"""
    if _lost(u.c) and any(z.k == "n_fukafuchi" for z in s.P[i].board):
        s.draw(i)


def _fuka_react(s, j):
    """相手（j）がカードを実行した時、相手のターンに1度だけ、手札から水のロスト・クルセイダーを出す"""
    i = 1 - j
    p = s.P[i]
    if s.tp != j or not any(z.k == "n_fukafuchi" for z in p.board):
        return
    if p.x.get("fuka_turn") == s.turn:
        return
    n = len(p.hand)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" and _lost(c) and "W" in c.civ and c.cost <= n and not (c.evo and not c.neo):
            if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
                best, bv = k, E.PRI[k]
    if best is None:
        return
    p.x["fuka_turn"] = s.turn
    p.hand.remove(best)
    s.ev(f"　フカフチノカミ：手札から {BY_KEY[best].name} を出す")
    s.enter(i, best, "hand", False)


add("n_fukafuchi", "水蜃 フカフチノカミ", 6, "W", power=8000, brk=2, races=("mizugami", LOST), pri=9,
    roles="draw rem blk",
    costx=cx_fukafuchi, payx=pay_fukafuchi, enter=e_fukafuchi,
    enterwatch=lambda s, i, u: (w_fukafuchi_lost(s, i, u), _fuka_react(s, i))[0],
    spellwatch=lambda s, i, k: _fuka_react(s, i),
    text="W・ブレイカー。水3マナで召喚してもよい。そのように軽く召喚した場合、出た時に自分のクリーチャー1体を手札に戻す。"
         "自分のロスト・クルセイダーが出た時、1枚引いてもよい。"
         "相手のターンに1度、相手がカードを実行した時、自分の手札から、手札の枚数以下のコストを持つ水のロスト・クルセイダーを"
         "1つ出してもよい", source=W + "《水蜃 フカフチノカミ》")


def cx_mizuha(s, i, av):
    """シンパシー：自分のロスト・クルセイダー・クリーチャー1体につきコスト-1（2より下がらない）"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and _lost(z.c))
    return max(2, 12 - n)


def rep_mizuha(s, i, u, dest, destroy_):
    """自分のロスト・クルセイダーは破壊以外では離れない"""
    if destroy_ or not _lost(u.c):
        return False
    return any(z.k == "n_mizuha" for z in s.P[i].board)


def e_mizuha(s, i, u):
    """召喚して出た時、各プレイヤーはバトルゾーンと墓地のカードをすべて超次元ゾーンに置く。その後3枚まで引く"""
    if not u.x.get("summoned"):
        return
    s.ev("　ミヅハノオオミカミ：バトルゾーンと墓地のカードをすべて超次元ゾーンへ")
    for j in (1 - i, i):
        q = s.P[j]
        for z in q.board[:]:
            if z in q.board:
                s.leave(j, z, "grave", by_opp=(j != i))
    for j in (0, 1):
        s.P[j].grave.clear()
    s.draw(i, 3)


add("n_mizuha", "瀑水神 ミヅハノオオミカミ", 12, "LWD", power=17500, brk=3, blocker=True,
    races=("mizugami", LOST, "dragon"), pri=13, roles="fin rem blk draw",
    costx=cx_mizuha, leaverep=rep_mizuha, enter=e_mizuha,
    text="シンパシー：自分のロスト・クルセイダー・クリーチャー1体につきコスト-1（2より下がらない）。"
         "ブロッカー、T・ブレイカー。自分のロスト・クルセイダー・クリーチャーは、破壊以外の方法では離れない。"
         "召喚によって出た時、各プレイヤーは自分のバトルゾーンと墓地にあるカードをすべて超次元ゾーンに置く。"
         "その後、自分は3枚まで引く", source=W + "《瀑水神 ミヅハノオオミカミ》")


def e_orugeito(s, i, u):
    t = s.target(i)
    if t is not None:
        move(s, i, t, "hand")


add("n_orugeito", "魔誕の斬将オルゲイト", 7, "W", power=7000, brk=2, blocker=True, jd=True,
    races=("demoncommand", "command"), pri=10, roles="blk rem",
    enter=e_orugeito, costx=he_costx("n_orugeito"), payx=he_payx("n_orugeito"),
    text="ハイパーエナジー（召喚する時、コストが互いに違う自分のクリーチャーを好きな数タップしてよい。1体につきコスト-2）。"
         "ブロッカー、ジャストダイバー、W・ブレイカー。出た時、相手のクリーチャー1体を持ち主の手札に戻してもよい",
    note="「相手のターンに相手のクリーチャーの出た時能力がトリガーした時、自分もその能力を使ってよい」は、"
         "他のカードの「出た時」の能力を借りて使う共通の入口（USEETB）がエンジンにないため実装していない。"
         "モジュールの中で真似て書くと、能力の中の「このクリーチャー自身を動かす」部分の扱いと"
         "入れ子の深さの決まりがモジュールごとにばらばらになる（いま3モジュールで別々に書かれている）", status="partial",
    source=W + "《魔誕の斬将オルゲイト》")


def sp_lostsign(s, i):
    """山札をシャッフルし、上4枚からロスト・クルセイダー1体をただで召喚。そのターンブロッカーを与え、
    次の自分のターンのはじめに手札に戻す"""
    p = s.P[i]
    s.rng.shuffle(p.deck)
    n = min(4, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.kind == "C" and _lost(c) and not (c.evo and not c.neo) and E.PRI[k] > bv:
            if s.fate(i, k, "deck", False) == "ok":
                best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        s.ev(f"　断罪のロスト・サイン：{BY_KEY[best].name} をただで召喚")
        u = s.enter(i, best, "deck", False)
        if u is not None:
            u.x["blk_turn"] = s.turn
            u.x["ret_turn"] = s.turn + (2 if s.tp == i else 1)
    for k in top:
        p.deck.insert(0, k)


def ts_return(s, i, u):
    """断罪のロスト・サインで出したクリーチャーを、自分のターンのはじめに手札に戻す"""
    if u.x.get("ret_turn") == s.turn:
        u.x.pop("ret_turn", None)
        s.ev(f"　断罪のロスト・サイン：{u.c.name} を手札に戻す")
        s.leave(i, u, "hand")


add("n_lostsign", "断罪のロスト・サイン", 5, "LW", kind="S", trig=True, pri=7, roles="rem blk trg",
    spell=sp_lostsign, spcost=_lost_down, tstartall=ts_return,
    blockok=lambda s, u: u.x.get("blk_turn") == s.turn,
    text="S・トリガー。自分の山札をシャッフルし、上から4枚を見る。その中からロスト・クルセイダー・クリーチャー1体を"
         "コストを支払わずに召喚してよい。残りを山札の下に置く。そのクリーチャーはこのターンブロッカーを得て、"
         "次の自分のターンのはじめに手札に戻る", source=W + "《断罪のロスト・サイン》")


def sp_shukumei(s, i):
    """2枚引く。その後、自分の手札の枚数以下のコストの相手のクリーチャーをすべて手札に戻す"""
    s.draw(i, 2)
    n = len(s.P[i].hand)
    for z in opp_all(s, i, lambda z: z.c.cost <= n):
        if z in s.P[1 - i].board:
            move(s, i, z, "hand")


def ch_shukumei(s, i):
    """手札からマナゾーンに置いた時、手札のロスト・クルセイダーを見せてアンタップする"""
    p = s.P[i]
    if any(_lost(BY_KEY[k]) for k in p.hand) and p.mused > 0:
        p.mused -= 1
        s.ev("　宿命の決闘：ロスト・クルセイダーを見せてアンタップして置く")


add("n_shukumei", "宿命の決闘", 6, "LWD", kind="S", trig=True, pri=8, roles="draw rem trg acc",
    spell=sp_shukumei, spcost=_lost_down, chargex=ch_shukumei,
    text="S・トリガー。2枚引く。その後、自分の手札の枚数以下のコストを持つ相手のクリーチャーをすべて持ち主の手札に戻す"
         "（引いた後の枚数で数える）。このカードを手札からマナゾーンに置いた時、手札のロスト・クルセイダー・カード1枚を"
         "表向きにしてよい。そうしたら、このカードをアンタップする", source=W + "《宿命の決闘》")
