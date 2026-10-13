"""これまでネットから持ってきていた34枚。効果をすべてカードどおりに実装した

  以前は「部品の並び（引く・破壊する…）」で近いものに置き換えていたが、近似や省略をやめて1枚ずつ書き直した。
  調べ直して直したところ：青銅の鎧とクリムゾン・ハンマーはS・トリガーを持たない／ブレインブルーは呪文ではなくクリーチャー／
  デス・ハンズはコスト7・パワー2000で破壊にパワーの条件がない／クルクル・トラップに自分のマナを増やす効果はない／
  ゴースト・タッチは「見ないで選んで捨てさせる」＝ランダム。
  正式名称が略称だったもの：知識の青 ブレインブルー、凶殺皇 デス・ハンズ、絶海の虎将 ティガウォック、
  清浄の精霊ウル、光輪の精霊 ピカリエ、青寂の精霊龍 カーネル、闇鎧亜ジャック・アルカディアス、モエル 鬼スナイパー。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import SLAYER, lock_until_my_turn, race_like

W = "https://dmwiki.net/"
M = "https://m.dmwiki.net/"


def _one(s, i, pred=None):
    return s.target(i, pred)


# ================================================================ 呪文（除去）
def sp_demonhand(s, i):
    t = _one(s, i)
    if t is not None:
        destroy(s, i, t)


add("n_demonhand", "デーモン・ハンド", 6, "D", kind="S", trig=True, pri=7, roles="rem trg", spell=sp_demonhand,
    text="S・トリガー。相手のクリーチャー1体を選んで破壊する", source=W + "《デーモン・ハンド》")


def sp_naturaltrap(s, i):
    t = _one(s, i)
    if t is not None:
        move(s, i, t, "mana")


add("n_naturaltrap", "ナチュラル・トラップ", 6, "N", kind="S", trig=True, pri=7, roles="rem trg", spell=sp_naturaltrap,
    text="S・トリガー。相手のクリーチャー1体を選び、持ち主のマナゾーンに置く（破壊ではないので「破壊された時」は働かない）",
    source=W + "《ナチュラル・トラップ》")


def sp_volcarrow(s, i):
    """パワー6000以下を破壊 → その後、自分のシールドを1つ墓地に置く（どちらも強制）"""
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 6000)
    if t is not None:
        destroy(s, i, t)
    p = s.P[i]
    for j in range(len(p.sh) - 1, -1, -1):
        if not p.sh[j][1]:
            p.grave.append(p.sh.pop(j)[0])
            s.shield_left()
            return
    if p.sh:
        p.grave.append(p.sh.pop()[0])
        s.shield_left()


add("n_volcarrow", "ボルカニック・アロー", 2, "F", kind="S", trig=True, pri=4, roles="rem trg", spell=sp_volcarrow,
    text="S・トリガー。パワー6000以下のクリーチャー1体を破壊する。その後、自分のシールドを1つ選び、墓地に置く（両方強制）",
    source=W + "《ボルカニック・アロー》")


def sp_deathchaser(s, i):
    t = _one(s, i, lambda z: not z.tap)
    if t is not None:
        destroy(s, i, t)


add("n_deathchaser", "デス・チェイサー", 5, "D", kind="S", trig=True, pri=6, roles="rem trg", spell=sp_deathchaser,
    text="S・トリガー。相手のタップされていない（アンタップしている）クリーチャー1体を破壊する。"
         "攻撃してタップされたクリーチャーは選べない", source=W + "《デス・チェイサー》")


def sp_ghosttouch(s, i):
    s.discard_random(1 - i)


add("n_ghosttouch", "ゴースト・タッチ", 2, "D", kind="S", trig=True, pri=3, roles="dis trg", spell=sp_ghosttouch,
    text="S・トリガー。相手の手札を1枚、見ないで選んで捨てさせる（＝ランダム）", source=W + "《ゴースト・タッチ》")


def sp_crimson(s, i):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 2000)
    if t is not None:
        destroy(s, i, t)


add("n_crimson", "クリムゾン・ハンマー", 2, "F", kind="S", pri=3, roles="rem", spell=sp_crimson,
    text="相手のパワー2000以下のクリーチャー1体を破壊する（S・トリガーはない）", source=W + "《クリムゾン・ハンマー》")


def sp_plusone(s, i):
    t = _one(s, i)
    if t is not None:
        move(s, i, t, "hand")
    s.draw(i)


add("n_plusone", "プラスワン・ゲート", 3, "W", kind="S", trig=True, pri=5, roles="rem draw trg", spell=sp_plusone,
    text="S・トリガー。相手のクリーチャー1体を持ち主の手札に戻し、その後1枚引く", source=M + "《プラスワン・ゲート》")


def sp_mizudokei(s, i):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 3000)
    if t is not None:
        move(s, i, t, "hand")


add("n_mizudokei", "時を戻す水時計", 1, "W", kind="S", trig=True, pri=3, roles="rem trg", spell=sp_mizudokei,
    text="S・トリガー。相手のパワー3000以下のクリーチャー1体を持ち主の手札に戻す", source=M + "《時を戻す水時計》")


def sp_kurukuru(s, i):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 5000)
    if t is not None:
        move(s, i, t, "mana")


add("n_kurukuru", "クルクル・トラップ", 4, "N", kind="S", trig=True, pri=5, roles="rem trg", spell=sp_kurukuru,
    text="S・トリガー。相手のパワー5000以下のクリーチャー1体を持ち主のマナゾーンに置く", source=M + "《クルクル・トラップ》")


def sp_goldenden(s, i):
    t = _one(s, i, lambda z: not z.tap)
    if t is not None:
        move(s, i, t, "mana")
    s.ramp(i, 1)


add("n_goldenden", "ゴールデンデン・トラップ", 7, "N", kind="S", trig=True, pri=8, roles="rem acc trg", spell=sp_goldenden,
    text="S・トリガー。相手のアンタップしているクリーチャー1体を持ち主のマナゾーンに置く（パワーの条件はない）。"
         "その後、自分の山札の上から1枚をマナゾーンに置く", source=M + "《ゴールデンデン・トラップ》")


def sp_shiketsu(s, i):
    s.mill(i, 2)
    t = _one(s, i, lambda z: not z.tap)
    if t is not None:
        destroy(s, i, t)


add("n_shiketsu", "死煙の霧", 5, "D", kind="S", trig=True, pri=6, roles="rem trg", spell=sp_shiketsu,
    text="S・トリガー。自分の山札の上から2枚を墓地に置く。その後、相手のアンタップしているクリーチャー1体を破壊する"
         "（墓地に置くのが先）", source=M + "《死煙の霧》")


def sp_flashspark(s, i):
    o = s.P[1 - i]
    for _ in range(2):
        t = _one(s, i, lambda z: not z.tap)
        if t is None:
            break
        t.tap = True
    n = sum(1 for u in o.board if u.c.kind == "C" and u.tap)
    if n:
        s.draw(i, n)


add("n_flashspark", "フラッシュ・スパーク", 6, "L", kind="S", trig=True, pri=7, roles="dis draw trg", spell=sp_flashspark,
    text="S・トリガー。相手のクリーチャーを2体タップする。その後、相手のタップしているクリーチャー1体につき1枚引く"
         "（もともとタップしていたクリーチャーも数える）", source=M + "《フラッシュ・スパーク》")


def sc_yuuki(s, i, k):
    return 2 if len(s.P[i].hand) == 1 else 6


def sp_yuuki(s, i):
    p = s.P[i]
    t = _one(s, i, lambda z: z.c.cost <= 7)
    if t is not None:
        destroy(s, i, t)
    s.ramp(i, 1)
    cands = [x for x in p.mana if BY_KEY[x].kind == "C"]
    if cands:
        k = max(cands, key=E.PRI.get)
        if E.PRI[k] >= 5:
            s.take_mana(i, k)
            p.hand.append(k)
            s.ev(f"　マナから {BY_KEY[k].name} を手札へ")


add("n_yuuki", "勇気の絆", 6, "FN", kind="S", trig=True, pri=7, roles="rem acc trg", spell=sp_yuuki, spcost=sc_yuuki,
    text="S・トリガー。自分の手札がこのカード1枚だけなら、火・自然の2マナで唱えてもよい。"
         "相手のコスト7以下のクリーチャー1体を破壊する。その後、自分の山札の上から1枚をマナゾーンに置き、"
         "自分のマナゾーンからクリーチャー1体を手札に戻してもよい", source=M + "《勇気の絆》")


def sp_rainbow(s, i):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 3000)
    if t is not None:
        destroy(s, i, t)
    if sum(1 for k in s.P[i].mana if E.MULTI[k]) >= 2:      # マナ武装2：マナに多色が2枚以上
        s.ramp(i, 1)


add("n_rainbow", "レインボー・ライフ", 4, "FN", kind="S", trig=True, pri=5, roles="rem acc trg", spell=sp_rainbow,
    text="S・トリガー。相手のパワー3000以下のクリーチャー1体を破壊する。"
         "マナ武装2：自分のマナゾーンに多色カードが2枚以上あれば、山札の上から1枚をマナゾーンに置く",
    source=M + "《レインボー・ライフ》")


# ================================================================ クリーチャー
def e_bronze(s, i, u):
    s.ramp(i, 1)


add("n_bronze", "青銅の鎧", 3, "N", power=1000, races=("beastfolk",), pri=4, roles="acc", enter=e_bronze,
    text="出た時、自分の山札の上から1枚をマナゾーンに置く（S・トリガーはない）", source=W + "《青銅の鎧》")


def e_surfer(s, i, u):
    t = _one(s, i)
    if t is not None:
        move(s, i, t, "hand")


add("n_surfer", "アクア・サーファー", 6, "W", power=2000, trig=True, races=("liquid",), pri=7, roles="rem trg",
    enter=e_surfer,
    text="S・トリガー。出た時、クリーチャー1体を選び、持ち主の手札に戻してもよい", source=W + "《アクア・サーファー》")


def e_brainblue(s, i, u):
    s.draw(i)


add("n_brainblue", "知識の青 ブレインブルー", 3, "W", power=3000, trig=True, races=("cyberlord", "shinobi"), pri=4,
    roles="draw trg", enter=e_brainblue,
    text="S・トリガー（クリーチャーなので、コストを支払わず召喚する）。出た時、1枚引く",
    source=M + "《知識の青+ブレインブルー》")


def e_deathhands(s, i, u):
    t = _one(s, i)
    if t is not None:
        destroy(s, i, t)


add("n_deathhands", "凶殺皇 デス・ハンズ", 7, "D", power=2000, trig=True, races=("darklord",), pri=8, roles="rem trg",
    enter=e_deathhands,
    text="S・トリガー。出た時、相手のクリーチャー1体を選んで破壊する（パワーの条件はない）",
    source=M + "《凶殺皇+デス・ハンズ》")


def e_muramasa(s, i, u):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 1000)
    if t is not None:
        destroy(s, i, t)


add("n_muramasa", "ムラマサのコンセント", 3, "F", power=1000, trig=True, races=("xenoparts",), pri=4, roles="rem trg",
    enter=e_muramasa,
    text="S・トリガー。出た時、相手のパワー1000以下のクリーチャー1体を破壊する", source=M + "《ムラマサのコンセント》")


def e_tigerg(s, i, u):
    for z in opp_all(s, i, lambda z: s.power(1 - i, z) <= 2000):
        if z in s.P[1 - i].board:
            destroy(s, i, z)


add("n_tigerg", "火焔タイガーグレンオー", 7, "F", power=2000, trig=True, races=("flame", "samurai"), pri=8,
    roles="rem trg", enter=e_tigerg,
    text="S・トリガー。出た時、相手のパワー2000以下のクリーチャーをすべて破壊する", source=M + "《火焔タイガーグレンオー》")


def e_moeru(s, i, u):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 4000)
    if t is not None:
        destroy(s, i, t)


def w_moeru(s, i, u):
    """自分のコスト7以上のクリーチャーが出た時にも働く"""
    if u.c.cost < 7 or u.k == "n_moeru":
        return
    for z in s.P[i].board:
        if z.k == "n_moeru":
            e_moeru(s, i, z)
            return


add("n_moeru", "モエル 鬼スナイパー", 5, "F", power=1000, trig=True, races=("humanoid", "hunter"), pri=6, roles="rem trg",
    enter=e_moeru, enterwatch=w_moeru,
    text="S・トリガー。このクリーチャー、または自分のコスト7以上のクリーチャーが出た時、"
         "相手のパワー4000以下のクリーチャー1体を破壊する（場に残っている間くり返し働く）",
    source=M + "《モエル+鬼スナイパー》")


def e_oort(s, i, u):
    t = _one(s, i, lambda z: s.power(1 - i, z) <= 3000)
    if t is not None:
        destroy(s, i, t)


def l_oort(s, i, u, dest):
    """離れた時も同じ効果（破壊でなくても働く）"""
    e_oort(s, i, u)


add("n_oort", "オールトザウルス", 3, "F", power=1000, trig=True, races=("rockbeast",), pri=5, roles="rem trg",
    enter=e_oort, left=l_oort,
    text="S・トリガー。このクリーチャーが出た時、または離れた時、相手のパワー3000以下のクリーチャー1体を破壊する"
         "（離れる理由は破壊でなくてもよい）", source=M + "《オールトザウルス》")


add("n_bolshack", "ボルシャック・ドラゴン", 6, "F", power=6000, brk=2, races=("armoreddragon", "dragon"), pri=8,
    roles="atk fin",
    powerx=lambda s, i, u, atk: (1000 * sum(1 for k in s.P[i].grave if "F" in BY_KEY[k].civ)) if atk else 0,
    text="W・ブレイカー。このクリーチャーが攻撃中、自分の墓地にある火のカード1枚につきパワー+1000"
         "（カードの種類は問わない）", source=M + "《ボルシャック・ドラゴン》")


def e_pikarie(s, i, u):
    s.draw(i)


add("n_pikarie", "光輪の精霊 ピカリエ", 4, "L", power=4000, blocker=True, noatkp=True, races=("angelcommand", "command"),
    pri=5, roles="blk draw", enter=e_pikarie,
    text="ブロッカー。このクリーチャーは相手プレイヤーを攻撃できない。出た時、1枚引いてもよい",
    source=M + "《光輪の精霊+ピカリエ》")


def e_uru(s, i, u):
    """クリーチャー1体を選び、タップまたはアンタップする（自分のクリーチャーも選べる）"""
    t = _one(s, i, lambda z: not z.tap)
    if t is not None:
        t.tap = True
        return
    mine = [z for z in s.P[i].board if z.c.kind == "C" and z.tap and z is not u]
    if mine:
        max(mine, key=lambda z: s.power(i, z)).tap = False
        return
    t = _one(s, i)
    if t is not None:
        t.tap = True


add("n_uru", "清浄の精霊ウル", 6, "L", power=4000, blocker=True, trig=True, noatkp=True,
    races=("angelcommand", "command"), pri=7, roles="blk dis trg", enter=e_uru,
    text="S・トリガー、ブロッカー。このクリーチャーは相手プレイヤーを攻撃できない。"
         "出た時、クリーチャー1体を選び、タップするかアンタップする（自分のクリーチャーも選べる）",
    source=M + "《清浄の精霊ウル》")


def cx_tigawok(s, i, av):
    return max(1, 7 - s.P[i].drawn)


def e_tigawok(s, i, u):
    s.draw(i, 3)


add("n_tigawok", "絶海の虎将 ティガウォック", 7, "W", power=6000, brk=2, blocker=True, races=("mutopia",), pri=9,
    roles="blk draw", enter=e_tigawok, costx=cx_tigawok,
    text="ブロッカー、W・ブレイカー。このクリーチャーの召喚コストは、そのターンに自分が引いたカード1枚につき1少なくなる"
         "（1より下がらない）。出た時、3枚まで引く", source=M + "《絶海の虎将+ティガウォック》")


def e_rudezana(s, i, u):
    """1枚引く。その後、自分の手札の枚数以下のコストの相手のクリーチャーをすべて手札に戻す"""
    s.draw(i)
    n = len(s.P[i].hand)
    for z in opp_all(s, i, lambda z: z.c.cost <= n):
        if z in s.P[1 - i].board:
            move(s, i, z, "hand")


add("n_rudezana", "ルード・ザーナ", 7, "W", power=5000, trig=True, blocker=True, races=("cybercommand", "command", "dragon"),
    pri=9, roles="blk draw rem trg", enter=e_rudezana,
    text="S・トリガー、ブロッカー。出た時、1枚引く。その後、自分の手札の枚数以下のコストを持つ相手のクリーチャーを"
         "すべて持ち主の手札に戻す（引いた後の手札の枚数で数える）", source=M + "《ルード・ザーナ》")


def e_jack(s, i, u):
    """相手のコスト4以下のカード1枚を持ち主の墓地に置く（破壊ではない）"""
    t = s.target(i, lambda z: z.c.cost <= 4, "CTX")
    if t is not None:
        s.leave(1 - i, t, "grave", by_opp=True)


add("n_jack", "闇鎧亜ジャック・アルカディアス", 4, "DF", power=1000, trig=True, races=("spiritquartz", "lostcrusader"),
    pri=6, roles="rem trg", enter=e_jack,
    text="S・トリガー、スレイヤー（バトルした相手のクリーチャーを破壊する）。出た時、バトルゾーンにある相手のコスト4以下の"
         "カード1枚を選び、持ち主の墓地に置く（破壊ではないので「破壊されない」効果を無視する）",
    source=W + "《闇鎧亜ジャック・アルカディアス》")
SLAYER.add("n_jack")


def e_kernel(s, i, u):
    t = _one(s, i)
    if t is not None:
        lock_until_my_turn(s, i, t)
        s.ev(f"　{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("n_kernel", "青寂の精霊龍 カーネル", 5, "LW", power=3500, trig=True, blocker=True,
    races=("angeldragon", "dragon", "revolution"), pri=6, roles="blk dis trg", enter=e_kernel,
    text="S・トリガー、ブロッカー。出た時、相手のクリーチャー1体を選ぶ。次の自分のターンのはじめまで、"
         "そのクリーチャーは攻撃もブロックもできない", source=M + "《青寂の精霊龍+カーネル》")


def e_zaru(s, i, u):
    for _ in range(2):
        t = _one(s, i, lambda z: not z.tap)
        if t is None:
            break
        t.tap = True


def w_zaru(s, i, u):
    """超魂X：下に純粋ZARU-36があるクリーチャーが攻撃する時、相手1体をタップし、次の相手のターンに起こさない"""
    if "n_zaru" not in u.under:
        return
    t = _one(s, i, lambda z: not z.tap) or _one(s, i)
    if t is not None:
        t.tap = True
        t.frz = 1
        s.ev(f"　超魂X：{t.c.name} をタップし、次の相手のターンにアンタップしない")


add("n_zaru", "純粋ZARU-36", 5, "L", power=4500, trig=True, races=("shine", "technosamurai", "fusioner"), pri=6,
    roles="dis trg", enter=e_zaru, atkwatch=w_zaru,
    text="S・トリガー。出た時、相手のクリーチャーを2体までタップする。超魂X：このカードがクリーチャーの下にあるなら、"
         "その上のクリーチャーは「攻撃する時、相手のクリーチャー1体をタップし、次の相手のターンのはじめにアンタップしない」を得る",
    source=W + "《純粋ZARU-36》")


add("n_toring", "轟速 ザ・トリング", 2, "FN", power=4000, mach=True, races=("soniccommand", "command", "invader"),
    pri=4, roles="atk",
    text="マッハファイター（出たターンに、タップしていない相手のクリーチャーも攻撃できる）。火のコマンドなので"
         "侵略の元・封印外しになる", source=W + "《轟速 ザ・トリング》")
