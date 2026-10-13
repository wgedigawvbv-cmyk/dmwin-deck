"""全国大会2025 エリア代表決定戦 関東大会Aブロック（2ブロック構築）の入賞デッキ2つの未実装札12枚

  出典は公式カードDBのカード詳細ページ（https://dm.takaratomy.co.jp/card/detail/?id=…）。
  デッキリストのページ（https://dm.takaratomy.co.jp/coverage/area25kt_decklist_a ）から各カードの詳細ページをたどり、
  12枚すべてについて「公式カードDB」と「dmwiki.net」の2か所で、本文・コスト・文明・種族・パワー・
  ブレイク数が一致することを確かめた（食い違いは1枚もなかった）。

  「〜を選ぶ」「〜してもよい」は、このシミュレーター共通の決まり
  （相手からは重要度PRIの高いもの、自分からは低いもの）で機械的に決めている。デッキごとの作戦は書いていない。

  デッキ（1）：バブル・ボール／ツイン・シックス／ド:コータ／ロック・ポロン／ダンマ＝ダンマダン／
                        「特攻」の鬼 ヨミノ晴明-1.0／爆藍月 スケルハンター／邪心臓の魔法陣
  デッキ（2）：～時空の工兵～／～紺碧の奇術師～／六番龍 シックスフォール Par滝／超魂設計図
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, dig2, worst_hand
from envcards.env0 import SLAYER, he_costx, he_payx, owner_of

D = "https://dm.takaratomy.co.jp/card/detail/?id="


# ================================================================ 共通の小道具
def _cost6_down(key):
    """「自分のコスト6以上のカードを使うコストを1少なくする（0以下にはならない）」
    ＝場にあるそのカード1枚につき1少なくする"""
    def f(s, i, k, cur):
        if cur <= 1 or BY_KEY[k].cost < 6:
            return cur
        n = sum(1 for z in s.P[i].board if z.k == key)
        return max(1, cur - n) if n else cur
    return f


def _cost6_down_sp(key):
    """同じ軽減を呪文の側（SPCOSTAURA＝spcost を通るもの）にもかける。返すのは増減の値"""
    def f(s, i, k, twin=False):
        c = BY_KEY[k]
        cost = c.twin[0] if twin else c.cost     # ツインパクトの呪文側は呪文側のコストで見る
        if cost < 6:
            return 0
        n = sum(1 for z in s.P[i].board if z.k == key)
        if not n:
            return 0
        return max(1, cost - n) - cost
    return f


def _opp_cre(s, i):
    """相手の、選べるクリーチャー（ジャストダイバーは除く）"""
    return [z for z in s.P[1 - i].board if z.c.kind == "C" and not z.jd]


def _minus_power(s, i, t, n):
    """相手のクリーチャー t のパワーをこのターン n 下げる（0以下になれば破壊）"""
    t.pw -= n
    s.ev(f"　{t.c.name} はこのターン パワー-{n}")
    if s.power(1 - i, t) <= 0:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


# ================================================================ バブル・ボール
def tw_bubbleball(s, i, u):
    """このクリーチャーがタップした時、カードを1枚引く

    全体に効く差し込み口なので、自分のカードのタップだけを見る。
    タップした状態で出た時は tap_cre を通らないので、正しく引かない。"""
    if u.k != "ec_bubbleball":
        return
    s.ev("　バブル・ボール：タップしたので1枚引く")
    s.draw(i)


add("ec_bubbleball", "バブル・ボール", 1, "W", power=2000, noatk=True, races=("cyberv",),
    pri=3, roles="draw", tapwatch=tw_bubbleball,
    text="このクリーチャーは攻撃できない。このクリーチャーがタップした時、カードを1枚引く"
         "（ハイパーエナジーやジャオウガの支払い、相手のタップ能力など、どんなタップでも引く）",
    source=D + "dm24ex3-056")


# ================================================================ ツイン・シックス
def w_twinsix(s, i, u):
    """自分のコスト6以上のクリーチャーが出た時、カードを1枚引いてもよい"""
    if u.c.kind != "C" or u.c.cost < 6:
        return
    n = sum(1 for z in s.P[i].board if z.k == "ec_twinsix")
    if n:
        s.ev(f"　ツイン・シックス：コスト6以上が出たので{n}枚引く")
        s.draw(i, n)


add("ec_twinsix", "ツイン・シックス", 2, "W", power=2000, jd=True, races=("splashqueen",),
    pri=4, roles="draw acc", costaura=_cost6_down("ec_twinsix"), spcostaura=_cost6_down_sp("ec_twinsix"),
    enterwatch=w_twinsix, status="full",
    text="ジャストダイバー（出た時、次の自分のターンのはじめまで相手に選ばれず、攻撃されない）。"
         "自分のコスト6以上のカードを使うコストを1少なくする（0以下にはならない）。"
         "自分のコスト6以上のクリーチャーが出た時、カードを1枚引いてもよい",
    source=D + "dm24rp3-037")


# ================================================================ ド:コータ
def e_dokota(s, i, u):
    """出た時、相手のクリーチャー1体のパワーをこのターン-3000（0以下なら破壊）"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 3000) or s.target(i)
    if t is None:
        return
    _minus_power(s, i, t, 3000)


add("ec_dokota", "ド:コータ", 2, "D", power=1000, trig=True, races=("noirabyss", "abyss"),
    pri=3, roles="rem trg", enter=e_dokota,
    text="S・トリガー。出た時、相手のクリーチャー1体を選ぶ。このターン、そのクリーチャーのパワーを-3000する"
         "（パワー0以下のクリーチャーは破壊される。倒せる相手がいればそれを、いなければ重要度のいちばん高い相手を選ぶ）",
    source=D + "spdeck13-006")


# ================================================================ ロック・ポロン
def w_rockporon(s, i, u):
    """自分のコスト6以上のクリーチャーが出た時、相手1体を選んでバトルさせてもよい"""
    if u.c.kind != "C" or u.c.cost < 6 or not s.has(i, "ec_rockporon"):
        return
    for _ in range(sum(1 for z in s.P[i].board if z.k == "ec_rockporon")):
        if s.over or s.stop or u not in s.P[i].board:
            return
        ap = s.power(i, u)
        best, bv = None, -1
        for t in _opp_cre(s, i):
            if s.power(1 - i, t) <= ap and s.val(t) > bv:
                best, bv = t, s.val(t)
        if best is None:                   # 勝てる相手がいなければ選ばない
            return
        s.ev(f"　ロック・ポロン：{u.c.name} と {best.c.name} をバトルさせる")
        s.battle(i, u, 1 - i, best)


add("ec_rockporon", "ロック・ポロン", 2, "F", power=1000, races=("firebird",),
    pri=4, roles="acc rem", costaura=_cost6_down("ec_rockporon"), spcostaura=_cost6_down_sp("ec_rockporon"),
    enterwatch=w_rockporon,
    atktargetlock=lambda s, i, u, t: t.k == "ec_rockporon", status="full",
    text="このクリーチャーは攻撃されない。自分のコスト6以上のカードを実行するコストを1少なくする"
         "（0以下にはならない）。自分のコスト6以上のクリーチャーが出た時、相手のクリーチャー1体を選んでもよい。"
         "その2体をバトルさせる（勝てる相手がいる時だけ、重要度のいちばん高い相手を選ぶ）",
    source=D + "dm25ex3-TF07")


# ================================================================ ダンマ＝ダンマダン
def _danma_kill(s, i):
    """墓地の枚数ぶんパワーを下げて倒せる相手がいるか"""
    n = len(s.P[i].grave)
    return s.target(i, lambda z: s.power(1 - i, z) <= 1000 * n) if n else None


def e_danmadanman(s, i, u):
    """出た時、次のうち1つを選ぶ。進化クリーチャーなら両方選んでもよい"""
    both = bool(u.under)
    draw = both or _danma_kill(s, i) is None
    if draw:
        s.draw(i, 3)
        for _ in range(2):
            k = worst_hand(s, i)
            if k is None:
                break
            s.discard(i, k)
    if both or not draw:
        n = len(s.P[i].grave)
        t = _danma_kill(s, i) or s.target(i)
        if t is not None and n:
            _minus_power(s, i, t, 1000 * n)


add("ec_danmadanman", "ダンマ＝ダンマダン", 4, "WDF", power=4000, trig=True, evo="WDF", neo=True,
    races=("abyssroyal", "abyss"), pri=6, roles="draw rem trg", enter=e_danmadanman,
    text="S・トリガー。NEO進化（自分の水・闇・火のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。"
         "出た時、次のうち1つを選ぶ。これが進化クリーチャーなら両方選ぶ。"
         "(1)カードを3枚引き、自分の手札を2枚捨てる (2)相手のクリーチャー1体を選び、このターン、"
         "そのパワーを自分の墓地のカード1枚につき-1000する。"
         "（進化していない時は、墓地の枚数で倒せる相手がいればそちらを、いなければ引くほうを選ぶ）",
    note="シールドからS・トリガーで出す時は、エンジンがS・トリガーのクリーチャーを単体で出すため、"
         "NEO進化として自分のクリーチャーの上に重ねることはできない（普通に召喚する時は重ねられる）",
    source=D + "dm25ex3-033")


# ================================================================ 「特攻」の鬼 ヨミノ晴明-1.0
def e_yomino(s, i, u):
    """出た時、相手の手札を見て1枚選び、捨てさせる"""
    o = s.P[1 - i]
    if not o.hand:
        return
    k = max(o.hand, key=E.PRI.get)
    s.ev(f"　「特攻」の鬼 ヨミノ晴明-1.0：相手の手札の {BY_KEY[k].name} を捨てさせる")
    s.discard(1 - i, k)


add("ec_yomino", "「特攻」の鬼 ヨミノ晴明-1.0", 6, "D", power=3000, races=("demonio",),
    pri=7, roles="dis atk", enter=e_yomino,
    costx=he_costx("ec_yomino"), payx=he_payx("ec_yomino"),
    text="ハイパーエナジー（召喚する時、コストが互いに違う自分のクリーチャーを好きな数タップしてよい。"
         "1体につき召喚コストを2少なくする。0以下にはならない）。"
         "スレイヤー（バトルした後、相手クリーチャーを破壊する）。"
         "出た時、相手の手札を見て1枚選び、捨てさせる（重要度のいちばん高い札を選ぶ）",
    source=D + "dm24rp4-036")
SLAYER.add("ec_yomino")


# ================================================================ 爆藍月 スケルハンター
def e_skelhunter(s, i, u):
    s.draw(i, 2)


def w_skelhunter(s, i, u):
    """相手のクリーチャーは、出たターンに攻撃できない"""
    if u.c.kind == "C" and any(z.k == "ec_skelhunter" for z in s.P[1 - i].board):
        u.lock = s.turn


def ae_skelhunter(s, i, u):
    """ターンのはじめ以外はアンタップしない：攻撃の後の再アンタップを止める"""
    if u.re and s.has(1 - i, "ec_skelhunter"):
        u.re = False
        s.ev("　爆藍月 スケルハンター：ターンのはじめ以外はアンタップしない")


add("ec_skelhunter", "爆藍月 スケルハンター", 7, "W", power=7000, brk=2, races=("greatmechaoh",),
    pri=9, roles="draw dis fin", enter=e_skelhunter,
    costx=he_costx("ec_skelhunter"), payx=he_payx("ec_skelhunter"),
    enterwatch=w_skelhunter, atkend=ae_skelhunter, status="partial",
    text="ハイパーエナジー（召喚する時、コストが互いに違う自分のクリーチャーを好きな数タップしてよい。"
         "1体につき召喚コストを2少なくする。0以下にはならない）。W・ブレイカー。"
         "出た時、カードを2枚引いてもよい。相手のクリーチャーは、出たターンに攻撃できない。"
         "相手のクリーチャーは、ターンのはじめ以外、アンタップしない",
    note="「ターンのはじめ以外アンタップしない」は、エンジンのアンタップに差し込み口（UNTAPLOCK／UNTAPWATCH）が"
         "なく、アンタップが start_turn や各カードの中に散って書かれているため、"
         "攻撃の後に自分からアンタップする能力（リ・アンタップ）だけを止めている。"
         "《攻守の天秤》のような呪文による全体アンタップや、《零獄接続王 ロマノグリラ天風》のような"
         "自分を起こす能力は止められない",
    source=D + "dm26rp1-TD004")


# ================================================================ 邪心臓の魔法陣
def e_jashinzo(s, i, u):
    """出た時、手札を1枚捨て、3枚まで引き、もう1度手札を1枚捨てる"""
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)
    s.draw(i, 3)
    k = worst_hand(s, i)
    if k is not None:
        s.discard(i, k)


def cg_jashinzo(s, i):
    """自分の手札からマナゾーンに置いた時、アンタップする（多色の置きタップを戻す）"""
    p = s.P[i]
    if p.mused > 0:
        p.mused -= 1
        s.ev("　邪心臓の魔法陣：アンタップしてマナゾーンに置く")


add("ec_jashinzo", "邪心臓の魔法陣", 3, "WDF", kind="T", gs=True, races=("demoncommand", "command"),
    pri=4, roles="draw acc trg", enter=e_jashinzo, chargex=cg_jashinzo,
    text="G・ストライク（相手の攻撃時に手札から見せて、相手のクリーチャー1体をこのターン攻撃できなくする）。"
         "シンカライズ（このタマシードの上に進化クリーチャーを置いてもよい）。"
         "出た時、自分の手札を1枚捨て、カードを3枚まで引き、もう1度自分の手札を1枚捨てる。"
         "このカードを自分の手札からマナゾーンに置いた時、アンタップする",
    source=D + "dm26sd1-w006")
E.SHINKA.add("ec_jashinzo")


# ================================================================ ～時空の工兵～
def t_jiku(s, i, u):
    """自分のターンの終わりに、山札の上から1枚を表向きにして下に置いてもよい"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    u.under.append(k)
    s.ev(f"　～時空の工兵～：山札の上から {BY_KEY[k].name} を下に置く")


def d_jiku(s, i, u):
    """破壊された時、下にあったカードをすべて墓地から手札に戻す"""
    p = s.P[i]
    back = []
    for k in u.under:
        if k in p.grave:
            p.grave.remove(k)
            back.append(k)
    if back:
        p.hand.extend(back)
        s.ev(f"　～時空の工兵～：下にあった{len(back)}枚を墓地から手札に戻す")


add("ec_jiku", "～時空の工兵～", 2, "W", power=1000, gs=True, evo="LWD", neo=True,
    races=("greatmechaoh", "steamknight"), pri=3, roles="trg draw", tend=t_jiku, destroyed=d_jiku,
    text="G・ストライク（相手の攻撃時に手札から見せて、相手のクリーチャー1体をこのターン攻撃できなくする）。"
         "NEO進化（自分の光・水・闇のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。"
         "自分のターンの終わりに、自分の山札の上から1枚を表向きにしてこのクリーチャーの下に置いてもよい。"
         "このクリーチャーが破壊された時、下にあったカードをすべて墓地から手札に戻す",
    source=D + "dm25rp2-033")


# ================================================================ ～紺碧の奇術師～
def e_konpeki(s, i, u):
    """出た時、1枚引く。進化クリーチャーなら、もう1枚引き、手札1枚をシールド化し、シールド1つを手札に加える"""
    p = s.P[i]
    s.draw(i)
    if not u.under:
        return
    s.draw(i)
    k = worst_hand(s, i)
    if k is not None:
        p.hand.remove(k)
        if s.add_shield(i, k):
            s.ev(f"　～紺碧の奇術師～：手札の {BY_KEY[k].name} をシールドにする")
        else:
            p.hand.append(k)
    j = next((j for j in range(len(p.sh)) if not p.sh[j][1]), None)   # いちばん古い裏向きのシールド
    if j is None:
        return
    p.hand.append(p.sh.pop(j)[0])
    s.shield_left()
    s.ev("　～紺碧の奇術師～：シールドを1つ手札に加えた（そのS・トリガーは使えない）")


add("ec_konpeki", "～紺碧の奇術師～", 3, "W", power=3000, trig=True, blocker=True, evo="LWD", neo=True,
    races=("liquid", "steamknight"), pri=5, roles="blk trg draw", enter=e_konpeki,
    text="S・トリガー。NEO進化（自分の光・水・闇のクリーチャー1体の上に置いてもよいし、普通に召喚してもよい）。"
         "ブロッカー。出た時、カードを1枚引く。これが進化クリーチャーなら、カードをもう1枚引き、"
         "自分の手札を1枚シールド化し、自分のシールドを1つ手札に加える（そのS・トリガーは使えない）。"
         "シールド化するのは手札でいちばん要らない札、手札に加えるのはいちばん古い裏向きのシールド",
    note="シールドからS・トリガーで出す時は、エンジンがS・トリガーのクリーチャーを単体で出すため、"
         "NEO進化として自分のクリーチャーの上に重ねることはできない（普通に召喚する時は重ねられる）",
    source=D + "dm25ex3-008")


# ================================================================ 六番龍 シックスフォール Par滝
def _stack(s, j, a, b):
    """プレイヤー j のクリーチャー a を、同じプレイヤーのクリーチャー b の下に置く"""
    p = s.P[j]
    if a is b or a not in p.board or b not in p.board:
        return False
    p.board.remove(a)
    b.under = [a.k] + a.under + b.under
    s.ev(f"　六番龍 シックスフォール Par滝：{a.c.name} を {b.c.name} の下に置く")
    return True


def e_sixfall(s, i, u):
    """出た時、各プレイヤー1人につき、そのプレイヤーのクリーチャー2体を選び、1体をもう1体の下に置いてもよい"""
    o = _opp_cre(s, i)
    if len(o) >= 2:                      # 相手：いちばん大事なクリーチャーを、次に大事なものの下にしまう
        o.sort(key=s.val, reverse=True)
        _stack(s, 1 - i, o[0], o[1])
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    fus = [z for z in mine if "fusioner" in z.c.races]
    if fus and len(mine) >= 2:           # 自分：下に置かれて働く札（フュージョナー）を主力の下に置く
        a = min(fus, key=s.val)
        hosts = [z for z in mine if z is not a]
        if hosts:
            _stack(s, i, a, max(hosts, key=s.val))


def _sixfall_cost(z):
    """超魂Xの能力を持っているクリーチャーの、基準になるコスト（持っていなければ None）"""
    if z.c.kind == "C" and (z.k == "ec_sixfall" or "ec_sixfall" in z.under):
        return z.c.cost
    return None


def tl_sixfall(s, by, u):
    """これよりコストが小さいカードの効果によって、相手に選ばれない"""
    n = _sixfall_cost(u)
    if n is None or by == owner_of(s, u):
        return False
    return s.spc is not None and s.spc < n


def tgl_sixfall(s, i, u, t):
    """これよりコストが小さいクリーチャーに攻撃されない"""
    n = _sixfall_cost(t)
    return n is not None and u.c.cost < n


add("ec_sixfall", "六番龍 シックスフォール Par滝", 4, "W", power=4000,
    races=("giantdragon", "giant", "dragon", "fusioner"), pri=6, roles="dis blk",
    enter=e_sixfall, tgtlock=tl_sixfall, atktargetlock=tgl_sixfall, status="partial",
    text="出た時、各プレイヤー1人につき、そのプレイヤーのクリーチャーを2体選び、"
         "そのうち1体をもう1体の下に置いてもよい（相手からは重要度のいちばん高いクリーチャーを次に高いものの下に入れて"
         "場から外し、自分では下に置かれて働くフュージョナーを主力の下に置く）。"
         "超魂X（このカードがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える）。"
         "このクリーチャーは、これよりコストが小さいカードの効果によって相手に選ばれない。"
         "このクリーチャーは、これよりコストが小さいクリーチャーに攻撃されない",
    note="「これよりコストが小さいカードの効果で選ばれない」は、エンジンが"
         "いま解決している能力の発生元カードのコスト（SRCC）を覚えておらず、"
         "いま唱えている呪文のコスト（s.spc）しか見られないため、呪文に対してだけ働く。"
         "クリーチャーやタマシードの能力が選ぶ時は、その能力を出しているカードのコストが分からないので止められない",
    source=D + "dm25ex3-rp2S02")


# ================================================================ 超魂設計図
def sp_chokon(s, i):
    """山札の上6枚を表向きにし、NEOクリーチャー1体とフュージョナー・カード1枚を手札に加える"""
    got = dig2(s, i, 6, [lambda k: BY_KEY[k].kind == "C" and BY_KEY[k].neo,
                         lambda k: "fusioner" in BY_KEY[k].races])
    for k in got:
        s.ev(f"　超魂設計図：{BY_KEY[k].name} を手札に加える")


add("ec_chokon", "超魂設計図", 2, "N", kind="S", gs=True, pri=3, roles="draw trg", spell=sp_chokon,
    text="G・ストライク（相手の攻撃時に手札から見せて、相手のクリーチャー1体をこのターン攻撃できなくする）。"
         "唱えた時、自分の山札の上から6枚を表向きにする。その中からNEOクリーチャー1体と"
         "フュージョナー・カード1枚を手札に加え、残りを好きな順序で山札の下に置く",
    source=D + "dm25rp1-047")
