"""担当53：DM26-SD1「ドキドキつよいデッキ 25の王道」の再録カード15枚

出典：dmwiki.net の各カードページ（1枚ずつ、別の質問で2回ずつ読んで突き合わせた）。
      《流星アーシュ》は本文が切れたので英語版 Wiki（duelmasters.fandom.com）でも裏取りした。

  この札束に入っている仕組み
    ・ドラゴン支援（地封院ギャイ／流星アーシュ／ボルシャック・栄光・ルピア／伍代ドーラ／
      龍世界 〜龍の降臨する地〜／紅に染まりし者「王牙」／永遠のリュウセイ・カイザー）
    ・マジック（アビス・レボリューションの種族）の一団。
      フレンド・バースト（他のマジックをタップして呪文側を場に置いたまま唱える）、
      メガ・ラスト・バースト（離れて手札・マナ・墓地に置かれた時、呪文側をただで唱える）、
      革命チェンジ：マジック、マジックのコスト軽減
    ・ガチンコ・ジャッジ（紅に染まりし者「王牙」）
    ・マッドネス（永遠のリュウセイ・カイザー）

  調べ直して意外だったこと
    ・《歌舞音愛 ヒメカット》《Napo獅子-Vi無粋》《調律師ピーカプ》《イシカワ・ハンドシーカー》は
      担当表には片面の名前しか書いていないが、**どれもツインパクト**だった（正式名で開き直した）。
    ・《永遠のリュウセイ・カイザー》はコスト8・パワー8000。殿堂入りではない（dmwiki に記載なし）。
    ・《龍世界 〜龍の降臨する地〜》はクリーチャーでも城でもなく、
      **「ドラゴニック・フィールド」というカードタイプ**（D2フィールドではない）。この1枚しか存在しない。
    ・《ボルシャック・栄光・ルピア》は dmwiki では **火/自然の多色**（英語版 Wiki は火単色と書いていて
      食い違ったので、dmwiki を2回読んで多色を採った）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, worst_hand
from envcards.env0 import SLAYER, discard_choice, race_like

W = "https://dmwiki.net/"
SRC = {
    "k53_gyai": W + "《地封院ギャイ》",
    "k53_ash": W + "《流星アーシュ》",
    "k53_glorylupia": W + "《ボルシャック・栄光・ルピア》",
    "k53_ouga": W + "《紅に染まりし者「王牙」／クリムゾン・ビクトリー》",
    "k53_godora": W + "《伍代ドーラ》",
    "k53_ryusekai": W + "《龍世界 〜龍の降臨する地〜》",
    "k53_aqvibrato": W + "《AQvibrato》",
    "k53_mogiringo": W + "《アシスター・Mogi林檎》",
    "k53_himekat": W + "《歌舞音愛 ヒメカット／♪蛙の子 遭えるの何処？好きと謂ひて》",
    "k53_napo": W + "《Napo獅子-Vi無粋／♪オレの歌 聞けよ聞かなきゃ 殴り合い》",
    "k53_pikapu": W + "《調律師ピーカプ／♪音速で 本番中に チューニング》",
    "k53_karakuri": W + "《芸魔隠狐 カラクリバーシ》",
    "k53_testarossa": W + "《灼熱の演奏 テスタ・ロッサ》",
    "k53_ishikawa": W + "《イシカワ・ハンドシーカー／♪聞くだけで 才能バレる このチューン》",
    "k53_eienryusei": W + "《永遠のリュウセイ・カイザー》",
}

ELEM = "CTX"        # エレメント（バトルゾーンのクリーチャー・タマシード・クロスギア）


# ================================================================ 共通の道具
def _dragon(c):
    """ドラゴン・カードか。

    種族名に「ドラゴン」を含む種族はドラゴンに含まれる（ドラゴノイドだけは別）ので、
    races に "dragon" を入れ忘れているカード（ほかの担当のぶん）も拾えるように部分一致で見る。"""
    if "dragon" in c.races:
        return True
    return any("dragon" in r for r in c.races if r != "dragonoid")


def _dragon_cre(c):
    return c.kind == "C" and _dragon(c)


def _magic(c):
    """マジックか（種族名が「マジック・〜」の種族はすべてマジックに含まれる）。

    ほかの担当のカードは races に "magic" を入れていないものがある（例：("magicmarfolk",)）ので、
    部分一致で見る。"""
    return race_like(c, "magic")


def _outrage(c):
    return race_like(c, "outrage")


def _plain_cre(c):
    """進化元を用意しなくても出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _reveal_top(s, i, n):
    """山札の上から n 枚を取り出して返す（山札は1枚残す。エンジンの dig / mill と同じ決まり）"""
    p = s.P[i]
    n = min(n, max(0, len(p.deck) - 1))
    return [p.deck.pop() for _ in range(n)]


def _to_bottom(s, i, ks):
    p = s.P[i]
    for k in ks:
        p.deck.insert(0, k)


def _ramp_top(s, i, tapped=True):
    """山札の上から1枚をマナゾーンに置く。置いたカードのキーを返す
    （相手にロビンフッドがいるとマナに置けないので山札の下へ。エンジンの ramp と同じ決まり）"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return None
    k = p.deck.pop()
    if s.has(1 - i, "robin"):
        p.deck.insert(0, k)
        return None
    s.add_mana(i, k, tapped, src="deck")
    return k


def _opp_elems(s, i, pred=None):
    """相手のバトルゾーンのエレメントすべて（「すべて」なので、選ばれない効果やジャストダイバーも含む）"""
    return [z for z in list(s.P[1 - i].board) if z.c.kind in ELEM and (pred is None or pred(z))]


def _gachinko(s, i):
    """ガチンコ・ジャッジを1回行う（勝ったら True）。互いに山札の上から1枚を見せて一番下に置き、
    コストが大きいほうが勝つ。同じコストなら仕掛けた側（i）の勝ち"""
    p, o = s.P[i], s.P[1 - i]
    if not p.deck:
        return False
    a = p.deck.pop()
    p.deck.insert(0, a)
    cb = -1
    if o.deck:
        b = o.deck.pop()
        o.deck.insert(0, b)
        cb = BY_KEY[b].cost
    s.ev(f"　ガチンコ・ジャッジ：{BY_KEY[a].name}（{BY_KEY[a].cost}） 対 {cb}")
    return BY_KEY[a].cost >= cb


def _cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたままコストを支払わずに唱える（墓地には行かない）"""
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


def mega_last_burst(key, cost, fn):
    """メガ・ラスト・バースト：このクリーチャーが離れて手札・マナゾーン・墓地に置かれた時、
    このカードの呪文側をコストを支払わずに唱えてもよい（唱えた後、そのカードは墓地に置かれる）"""
    def f(s, i, u, dest):
        if u.k != key or s.over or dest not in ("hand", "mana", "grave"):
            return
        if not s.spell_ok(i, cost):
            return
        p = s.P[i]
        if dest == "hand" and key in p.hand:
            p.hand.remove(key)
        elif dest == "mana" and key in p.mana:
            s.take_mana(i, key)
        elif dest == "grave" and key in p.grave:
            p.grave.remove(key)
        else:
            return                            # 置かれたはずのゾーンに無い（別の効果で動いた）
        s.ev(f"　メガ・ラスト・バースト：{BY_KEY[key].name} の呪文側をコストを支払わずに唱える")
        s.cast(i, key, twin=True)
    return f


# ================================================================ 1. 地封院ギャイ
def e_gyai(s, i, u):
    """出た時、山札の上から3枚を表向きにし、その中のドラゴン・クリーチャーを手札に加え、
    残りをタップしてマナゾーンに置く（「好きな数」は全部もらう）"""
    p = s.P[i]
    top = _reveal_top(s, i, 3)
    if not top:
        return
    got = [k for k in top if _dragon_cre(BY_KEY[k])]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    if got:
        s.ev(f"　地封院ギャイ：ドラゴン{len(got)}枚を手札へ")
    robin = s.has(1 - i, "robin")
    for k in top:
        if robin:
            p.deck.insert(0, k)
        else:
            s.add_mana(i, k, True, src="deck")


def fa_gyai(s, i, av, cv):
    """自分のターン中、ドラゴン・クリーチャーを1体、自分のマナゾーンから召喚してもよい（コストは支払う）"""
    p = s.P[i]
    if not s.has(i, "k53_gyai") or s.manaexec(i) or p.x.get("k53_gyai_t") == s.turn:
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not _dragon_cre(c):
            continue
        if c.evo and not c.neo and s.evo_src(i, k) is None:
            continue
        n = s.ccost(i, k, av)
        if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:k53gyai", k, n))
    return out


def ap_gyai(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana or not s.has(i, "k53_gyai"):
        return
    c = BY_KEY[k]
    on = s.evo_src(i, k) if c.evo else None
    if c.evo and not c.neo and on is None:
        return
    p.x["k53_gyai_t"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"地封院ギャイ：マナゾーンからドラゴンを召喚 {c.name}（{a[2]}マナ）")
    s.enter(i, k, "mana", True, on=on)


add("k53_gyai", "地封院ギャイ", 6, "N", power=7000, brk=2,
    races=("gaiacommanddragon", "command", "dragon"), pri=8, roles="acc draw atk",
    enter=e_gyai, freeacts=fa_gyai, actapply={"x:k53gyai": ap_gyai},
    text="W・ブレイカー。出た時、自分の山札の上から3枚を表向きにする。"
         "その中から好きな数のドラゴン・クリーチャーを手札に加え、残りをタップしてマナゾーンに置く"
         "（ドラゴンは全部もらう）。"
         "自分のターン中、ドラゴン・クリーチャーを1体、自分のマナゾーンから召喚してもよい（コストは支払う）",
    note="マナからの召喚は各ターン1体まで（カードの「1体」をそう読んだ）",
    source=SRC["k53_gyai"])


# ================================================================ 2. 流星アーシュ
def e_ash(s, i, u):
    """出た時、山札の上から1枚をタップしてマナに置き、その後マナからドラゴン・クリーチャー1体を手札に戻し、
    そのドラゴン以下のコストの相手のクリーチャー1体を持ち主の手札に戻す"""
    p = s.P[i]
    _ramp_top(s, i)
    cands = [k for k in sorted(set(p.mana)) if _dragon_cre(BY_KEY[k])]
    if not cands:
        return
    top = max(BY_KEY[k].cost for k in cands)
    t = s.target(i, lambda z, c=top: z.c.cost <= c)
    if t is not None:
        # 相手のそのクリーチャーに届く中で、いちばん安いドラゴンをマナから戻す（マナを減らしすぎない）
        reach = [k for k in cands if BY_KEY[k].cost >= t.c.cost]
        k = min(reach, key=lambda x: (BY_KEY[x].cost, E.PRI[x])) if reach else max(cands, key=E.PRI.get)
    else:
        k = max(cands, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　流星アーシュ：マナの {BY_KEY[k].name} を手札へ")
    if t is not None and t in s.P[1 - i].board and t.c.cost <= BY_KEY[k].cost:
        move(s, i, t, "hand")


add("k53_ash", "流星アーシュ", 5, "WN", power=5000, blocker=True, trig=True,
    races=("bluecommanddragon", "greencommanddragon", "command", "dragon", "hunter"),
    pri=7, roles="trg blk rem acc",
    enter=e_ash,
    text="S・トリガー。ブロッカー。"
         "出た時、自分の山札の上から1枚をタップして自分のマナゾーンに置き、その後、"
         "ドラゴン・クリーチャーを1体、自分のマナゾーンから手札に戻す。"
         "そのドラゴン以下のコストの相手のクリーチャーを1体選び、持ち主の手札に戻す"
         "（戻すドラゴンは、重要度のいちばん高い相手のクリーチャーに届く中でいちばん安いものを選ぶ）",
    source=SRC["k53_ash"])


# ================================================================ 3. ボルシャック・栄光・ルピア
def e_glorylupia(s, i, u):
    """出た時、山札の上から1枚をタップしてマナに置く。それがドラゴン・カードなら、もう1枚置く"""
    k = _ramp_top(s, i)
    if k is None:
        return
    s.ev(f"　ボルシャック・栄光・ルピア：{BY_KEY[k].name} をマナへ")
    if _dragon(BY_KEY[k]):
        _ramp_top(s, i)


add("k53_glorylupia", "ボルシャック・栄光・ルピア", 3, "FN", power=4000,
    races=("firebird", "armoreddragon", "armored", "dragon"), pri=5, roles="acc",
    enter=e_glorylupia,
    text="出た時、自分の山札の上から1枚をタップしてマナゾーンに置く。"
         "それがドラゴン・カードなら、自分の山札の上からもう1枚、タップしてマナゾーンに置く",
    note="文明は dmwiki の表記どおり火/自然の多色（英語版 Wiki は火単色と書いていて食い違う）",
    source=SRC["k53_glorylupia"])


# ================================================================ 4. 紅に染まりし者「王牙」／クリムゾン・ビクトリー
def a_ouga(s, i, u):
    """攻撃する時、相手とガチンコ・ジャッジする。勝ったら山札の上から3枚を見て、
    その中からドラゴン・クリーチャー1体を出してもよい。残りを山札の下に置く"""
    if not _gachinko(s, i):
        return
    top = _reveal_top(s, i, 3)
    if not top:
        return
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if _dragon_cre(c) and _plain_cre(c) and E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
    _to_bottom(s, i, top)
    if best is not None:
        s.ev(f"　王牙：ガチンコ・ジャッジに勝って {BY_KEY[best].name} を出す")
        s.enter(i, best, "deck", False)


def sp_crimsonvictory(s, i):
    """パワー2000以下のクリーチャーをすべて破壊する（自分のものも破壊する）"""
    for j in (1 - i, i):
        for z in list(s.P[j].board):
            if z.c.kind != "C" or z not in s.P[j].board:
                continue
            if s.power(j, z) <= 2000:
                s.leave(j, z, "grave", by_opp=(j != i), destroy=True)


add("k53_ouga", "紅に染まりし者「王牙」／クリムゾン・ビクトリー", 8, "F", power=8000, brk=2, sa=True,
    races=("humanoiddragon", "dragon", "hunter", "alien"), twin=(4, "F", True),
    pri=10, roles="atk fin trg rem",
    attack=a_ouga, spell=sp_crimsonvictory,
    text="クリーチャー側：スピードアタッカー、W・ブレイカー。"
         "攻撃する時、相手とガチンコ・ジャッジする（互いに山札の上から1枚を見せて一番下に置き、"
         "コストが大きいほうが勝つ。同じコストなら仕掛けた側の勝ち）。"
         "自分が勝ったら、自分の山札の上から3枚を見て、その中からドラゴン・クリーチャー1体を出してもよい。"
         "残りを山札の下に置く。"
         "呪文側（クリムゾン・ビクトリー、火4）：S・トリガー。パワー2000以下のクリーチャーをすべて破壊する"
         "（自分のクリーチャーも破壊される）",
    source=SRC["k53_ouga"])


# ================================================================ 5. 伍代ドーラ
def cx_godora(s, i, av):
    """召喚コストを、自分のマナゾーンにあるドラゴン・カード1枚につき1少なくする（コストは2以下にならない）"""
    n = sum(1 for k in s.P[i].mana if _dragon(BY_KEY[k]))
    return max(3, 15 - n)


def a_godora(s, i, u):
    """攻撃する時、相手のクリーチャー1体を選んでもよい。それとこのクリーチャーをバトルさせる"""
    if u not in s.P[i].board:
        return
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　伍代ドーラ：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


SLAYER.add("k53_godora")

add("k53_godora", "伍代ドーラ", 15, "DFN", power=15000, brk=3, sa=True, gs=True,
    races=("redcommanddragon", "command", "dragon"), pri=13, roles="fin atk rem trg",
    costx=cx_godora, attack=a_godora,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "このクリーチャーの召喚コストを、自分のマナゾーンにあるドラゴン・カード1枚につき1少なくする"
         "（ただしコストは2以下にならない＝3が下限）。"
         "スピードアタッカー。スレイヤー（バトルした相手のクリーチャーを破壊する）。T・ブレイカー。"
         "攻撃する時、相手のクリーチャー1体を選んでもよい。その選んだクリーチャーとこのクリーチャーをバトルさせる"
         "（重要度のいちばん高い相手のクリーチャーを選ぶ）",
    source=SRC["k53_godora"])


# ================================================================ 6. 龍世界 〜龍の降臨する地〜
def t_ryusekai(s, i, u):
    """自分のターンのはじめに、自分の山札の上から1枚を墓地に置く。
    それが進化ではないドラゴンなら、このフィールドを破壊して、そのドラゴンを出してもよい"""
    p = s.P[i]
    got = s.mill(i, 1)
    if not got or s.over:
        return
    k = got[0]
    c = BY_KEY[k]
    if not (_dragon_cre(c) and not c.evo) or k not in p.grave:
        return
    if u not in p.board or s.fate(i, k, "grave", False) != "ok":
        return
    p.grave.remove(k)
    s.ev(f"　龍世界：このフィールドを破壊して {c.name} を出す")
    s.leave(i, u, "grave", destroy=True)
    s.enter(i, k, "grave", False)


E.STAY.add("k53_ryusekai")        # 場に残って働くので、創世竜の下には置かない

add("k53_ryusekai", "龍世界 〜龍の降臨する地〜", 3, "F", kind="T", races=("dragonworld",),
    pri=5, roles="acc fin", tstart=t_ryusekai,
    text="ドラゴニック・フィールド：ドラゴン・ワールド。"
         "自分のターンのはじめに、自分の山札の上から1枚を墓地に置く。"
         "それが進化ではないドラゴンなら、このフィールドを破壊してもよい。そうしたら、そのドラゴンを出す"
         "（出せるなら必ず出す）",
    note="「フィールド」というカードタイプがこのシミュレーターに無いので、"
         "バトルゾーンに残るクリーチャーでないカード＝タマシード（kind=\"T\"）として置いている。"
         "エレメントとして選ばれる・破壊される点は同じだが、"
         "D2フィールドではないこと（D2フィールドと置き換わらない）は表せていない",
    status="partial", source=SRC["k53_ryusekai"])


# ================================================================ 7. AQvibrato
add("k53_aqvibrato", "AQvibrato", 2, "W", power=1000, races=("magic", "liquid"),
    pri=3, roles="draw",
    enter=lambda s, i, u: s.draw(i, 1),
    text="出た時、カードを1枚引く",
    source=SRC["k53_aqvibrato"])


# ================================================================ 8. アシスター・Mogi林檎
def ca_mogiringo(s, i, k, cur):
    """各ターンに一度、自分のマジックを使うコストを1少なくする（コストは0以下にならない）"""
    if cur <= 1:
        return cur
    c = BY_KEY[k]
    if c.kind != "C" or not _magic(c):
        return cur
    p = s.P[i]
    if not any(z.k == "k53_mogiringo" for z in p.board):
        return cur
    if p.x.get("k53_mogi_t") == s.turn:
        return cur
    return max(1, cur - 1)


def sa_mogiringo(s, i, k, twin=False):
    """各ターンに一度、自分のマジック呪文を使うコストを1少なくする（0以下にはならない）。

    `spcostaura=` は呪文全体にかかるので、Mogi林檎が場にある持ち主のマジック呪文だけに
    効くよう必ず確かめる。各ターン一度なので、重ねずに1だけ下げる。
    ツインパクトの呪文側も「呪文」なので、そのときは呪文側のコストで見る。"""
    c = BY_KEY[k]
    if not (c.kind == "S" or twin):          # ツインパクトの呪文側も「呪文」
        return 0
    cost = c.twin[0] if twin else c.cost
    if cost <= 1 or not _magic(c):
        return 0
    p = s.P[i]
    if not any(z.k == "k53_mogiringo" for z in p.board):
        return 0
    if p.x.get("k53_mogi_t") == s.turn:
        return 0
    return -1


def sw_mogiringo(s, i, k):
    """マジック呪文に軽減が効いた分も、そのターンの一度として数える"""
    if not _magic(BY_KEY[k]) or not s.has(i, "k53_mogiringo"):
        return
    p = s.P[i]
    if p.x.get("k53_mogi_t") == s.turn:
        return
    p.x["k53_mogi_t"] = s.turn


def ew_mogiringo(s, i, u):
    """軽減が効いたマジックの召喚が1回あったら、そのターンはもう軽減しない"""
    if u.c.kind != "C" or not u.x.get("summoned") or not _magic(u.c):
        return
    p = s.P[i]
    if not any(z.k == "k53_mogiringo" and z is not u for z in p.board):
        return
    if p.x.get("k53_mogi_t") == s.turn:
        return
    p.x["k53_mogi_t"] = s.turn


add("k53_mogiringo", "アシスター・Mogi林檎", 2, "W", power=2000, jd=True,
    races=("magicmarfolk", "magic"), pri=4, roles="acc",
    costaura=ca_mogiringo, spcostaura=sa_mogiringo,
    enterwatch=ew_mogiringo, spellwatch=sw_mogiringo,
    text="ジャストダイバー（出たターン、相手に選ばれず攻撃もされない）。"
         "各ターンに一度、自分のマジックを使うコストを1少なくしてもよい。ただしコストは0以下にならない"
         "（軽減が効いた召喚が1回あったら、そのターンはもう効かない）",
    status="full", source=SRC["k53_mogiringo"])


# ================================================================ 9. 歌舞音愛 ヒメカット／♪蛙の子 遭えるの何処？好きと謂ひて
def sp_himekat(s, i):
    """相手のエレメントを2つまで選び、持ち主の手札に戻す"""
    for _ in range(2):
        if s.over:
            return
        t = s.target(i, kinds=ELEM)
        if t is None:
            return
        move(s, i, t, "hand")


def e_himekat(s, i, u):
    """マジック・フレンド・バースト：出た時、自分の他のマジック・クリーチャーを1体タップしてもよい。
    そうしたら、このカードの呪文側を、バトルゾーンに置いたままコストを支払わずに唱える"""
    p = s.P[i]
    cands = [z for z in p.board if z is not u and z.c.kind == "C" and _magic(z.c) and not z.tap]
    if not cands or not s.spell_ok(i, 4):
        return
    if s.target(i, kinds=ELEM) is None:
        return                                # 戻せる相手のエレメントが無いなら、自分をタップしない
    z = min(cands, key=s.val)
    s.tap_cre(i, z)
    s.ev(f"　マジック・フレンド・バースト：{z.c.name} をタップして呪文側を唱える")
    _cast_inplace(s, i, "k53_himekat", 4, sp_himekat)


def dw_himekat(s, j, k):
    """相手のターン中、相手がそのターンで2枚目以降のカードを引いた時、自分もカードを1枚引いてもよい"""
    if s.over or s.tp != j:
        return
    o = 1 - j
    if not s.has(o, "k53_himekat") or s.P[j].drawn < 2:
        return
    for z in list(s.P[o].board):
        if z.k == "k53_himekat" and not s.over:
            s.draw(o, 1)


add("k53_himekat", "歌舞音愛 ヒメカット／♪蛙の子 遭えるの何処？好きと謂ひて", 2, "W", power=2000,
    races=("magicmermaid", "magic"), twin=(4, "W", False), pri=5, roles="rem draw",
    enter=e_himekat, spell=sp_himekat, drawwatch=dw_himekat,
    text="クリーチャー側：マジック・フレンド・バースト（出た時、自分の他のマジック・クリーチャーを1体"
         "タップしてもよい。そうしたら、このカードの呪文側を、バトルゾーンに置いたまま"
         "コストを支払わずに唱える）。"
         "相手のターン中、相手がそのターンで2枚目以降のカードを引いた時、自分もカードを1枚引いてもよい。"
         "呪文側（♪蛙の子 遭えるの何処？好きと謂ひて、水4・マジック・ソング）："
         "相手のエレメントを2つまで選び、持ち主の手札に戻す",
    note="フレンド・バーストは、戻せる相手のエレメントがある時だけ使う"
         "（自分のクリーチャーをタップするだけ損になるのを避ける、全デッキ共通の決まり）",
    source=SRC["k53_himekat"])


# ================================================================ 10. Napo獅子-Vi無粋／♪オレの歌 聞けよ聞かなきゃ 殴り合い
def cx_napo(s, i, av):
    """自分のマジック・クリーチャーがあれば、召喚コストを1少なくする"""
    if any(z.c.kind == "C" and _magic(z.c) for z in s.P[i].board):
        return 4
    return 5


def e_napo(s, i, u):
    """出た時、手札を2枚まで捨て、その枚数より1枚多くカードを引く"""
    n = 0
    for _ in range(2):
        k = worst_hand(s, i)
        if k is None:
            break
        s.discard(i, k)
        n += 1
    s.draw(i, n + 1)


def sp_napo(s, i):
    """相手のコスト2以下のエレメントをすべて破壊する"""
    for z in _opp_elems(s, i, lambda x: x.c.cost <= 2):
        if z in s.P[1 - i].board:
            destroy(s, i, z)


add("k53_napo", "Napo獅子-Vi無粋／♪オレの歌 聞けよ聞かなきゃ 殴り合い", 5, "F", power=6000, brk=2, sa=True,
    races=("magicnitrodragon", "magic", "dragon"), twin=(3, "F", False),
    pri=8, roles="atk draw rem fin",
    costx=cx_napo, enter=e_napo, left=mega_last_burst("k53_napo", 3, sp_napo), spell=sp_napo,
    text="クリーチャー側：自分のマジック・クリーチャーがあれば、このクリーチャーの召喚コストを1少なくする。"
         "出た時、手札を2枚まで捨て、その枚数より1枚多くカードを引く（重要度の低い2枚を捨てて3枚引く）。"
         "メガ・ラスト・バースト（このクリーチャーが離れて、手札、マナゾーン、または墓地に置かれた時、"
         "このカードの呪文側をコストを支払わずに唱えてもよい）。スピードアタッカー、W・ブレイカー。"
         "呪文側（♪オレの歌 聞けよ聞かなきゃ 殴り合い、火3・マジック・ソング）："
         "相手のコスト2以下のエレメントをすべて破壊する",
    source=SRC["k53_napo"])


# ================================================================ 11. 調律師ピーカプ／♪音速で 本番中に チューニング
def sp_pikapu(s, i):
    """このターン、自分のクリーチャー1体に「スピードアタッカー」を与え、
    そのクリーチャーの最初の攻撃の終わりにそのクリーチャーをアンタップする"""
    p = s.P[i]
    a = s.atk
    if s.tp == i and a is not None and a in p.board and not a.re:
        a.re = True
        s.ev(f"　♪音速で 本番中に チューニング：{a.c.name} は最初の攻撃の後アンタップする")
        return
    cs = [z for z in p.board if z.c.kind == "C" and not z.c.noatk and not z.re]
    if not cs:
        return
    z = max(cs, key=lambda x: (1 if (x.sick and not x.sa and not x.c.sa) else 0,
                               0 if x.tap else 1, s.power(i, x)))
    z.sa = True
    z.re = True
    s.ev(f"　♪音速で 本番中に チューニング：{z.c.name} にスピードアタッカー")


add("k53_pikapu", "調律師ピーカプ／♪音速で 本番中に チューニング", 4, "F", power=4000, sa=True,
    races=("magicmachineeater", "magic"), twin=(3, "F", False),
    pri=5, roles="atk",
    left=mega_last_burst("k53_pikapu", 3, sp_pikapu), spell=sp_pikapu,
    text="クリーチャー側：スピードアタッカー。"
         "メガ・ラスト・バースト（このクリーチャーが離れて、手札、マナゾーン、または墓地に置かれた時、"
         "このカードの呪文側をコストを支払わずに唱えてもよい）。"
         "呪文側（♪音速で 本番中に チューニング、火3・マジック・ソング）："
         "このターン、自分のクリーチャー1体に「スピードアタッカー」を与え、"
         "そのクリーチャーの最初の攻撃の終わりにそのクリーチャーをアンタップする"
         "（いま攻撃しているクリーチャーがいればそれ、いなければ召喚酔いしている"
         "いちばんパワーの高いクリーチャーを選ぶ）",
    source=SRC["k53_pikapu"])


# ================================================================ 12. 芸魔隠狐 カラクリバーシ
def e_karakuri(s, i, u):
    """出た時、カードを1枚引き、その後、コスト3以下の呪文を1枚、
    自分の手札からコストを支払わずに唱えてもよい"""
    s.draw(i, 1)
    if s.over:
        return
    p = s.P[i]
    best, bv, tw = None, -1, False
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "S" and c.cost <= 3 and s.spell_ok(i, c.cost):
            if E.PRI[k] > bv:
                best, bv, tw = k, E.PRI[k], False
        elif c.twin and c.twin[0] <= 3 and s.spell_ok(i, c.twin[0]):
            if E.PRI[k] > bv:
                best, bv, tw = k, E.PRI[k], True
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　カラクリバーシ：{BY_KEY[best].name} をコストを支払わずに唱える")
    s.cast(i, best, twin=tw)


def pr_karakuri(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and _magic(BY_KEY[kk]))
    return None if n >= 3 else "革命チェンジの元（マジック・クリーチャー）が3体いない"


add("k53_karakuri", "芸魔隠狐 カラクリバーシ", 5, "WF", power=4000, sa=True, gs=True,
    races=("magicmonster", "magic", "gamecommand", "command"), pri=8, roles="draw atk trg",
    enter=e_karakuri, changex=lambda s, i, u: _magic(u.c), playrule=pr_karakuri,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャーを1体選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "革命チェンジ：マジック（自分のマジックが攻撃する時、そのクリーチャーと手札にある"
         "このクリーチャーを入れ替えてもよい）。スピードアタッカー。"
         "出た時、カードを1枚引き、その後、コスト3以下の呪文を1枚、"
         "自分の手札からコストを支払わずに唱えてもよい（ツインパクトの呪文側も選べる。"
         "重要度のいちばん高いものを唱える）",
    source=SRC["k53_karakuri"])


# ================================================================ 13. 灼熱の演奏 テスタ・ロッサ
def e_testarossa(s, i, u):
    """出た時、自分の手札からマジックまたはアウトレイジを1枚捨ててもよい。そうしたら、カードを2枚引く"""
    p = s.P[i]
    if len(p.deck) < 2:
        return                                # 引けないなら捨てない
    cands = [k for k in p.hand if _magic(BY_KEY[k]) or _outrage(BY_KEY[k])]
    if not cands:
        return
    k = min(cands, key=E.PRI.get)
    s.discard(i, k)
    s.draw(i, 2)


add("k53_testarossa", "灼熱の演奏 テスタ・ロッサ", 3, "F", power=1000, sa=True,
    races=("magicoutrage", "magic"), pri=4, roles="draw atk",
    enter=e_testarossa,
    text="スピードアタッカー。"
         "出た時、自分の手札からマジックまたはアウトレイジを1枚捨ててもよい。そうしたら、カードを2枚引く"
         "（捨てるのは条件に合う中で重要度のいちばん低い1枚）",
    source=SRC["k53_testarossa"])


# ================================================================ 14. イシカワ・ハンドシーカー／♪聞くだけで 才能バレる このチューン
def sp_ishikawa(s, i):
    """カードを2枚引き、自分の手札を1枚捨てる"""
    s.draw(i, 2)
    if not s.over:
        discard_choice(s, i)


add("k53_ishikawa", "イシカワ・ハンドシーカー／♪聞くだけで 才能バレる このチューン", 2, "W", power=1000,
    blocker=True, races=("magicmarfolk", "magic"), twin=(3, "W", False),
    pri=4, roles="blk draw",
    left=mega_last_burst("k53_ishikawa", 3, sp_ishikawa), spell=sp_ishikawa,
    text="クリーチャー側：ブロッカー。"
         "メガ・ラスト・バースト（このクリーチャーが離れて、手札、マナゾーン、または墓地に置かれた時、"
         "このカードの呪文側をコストを支払わずに唱えてもよい）。"
         "呪文側（♪聞くだけで 才能バレる このチューン、水3・マジック・ソング）："
         "カードを2枚引き、自分の手札を1枚捨てる",
    source=SRC["k53_ishikawa"])


# ================================================================ 15. 永遠のリュウセイ・カイザー
def sa_eienryusei(s, i, u):
    """自分のクリーチャーすべてに「スピードアタッカー」を与える"""
    return u.c.kind == "C" and s.has(i, "k53_eienryusei")


def ew_eienryusei(s, i, u):
    """相手のクリーチャーは、タップして出る"""
    if u.c.kind != "C" or not s.has(1 - i, "k53_eienryusei"):
        return
    if u in s.P[i].board and not u.tap:
        s.tap_cre(i, u)


def dx_eienryusei(s, i, k):
    """マッドネス：相手の呪文の効果または相手のクリーチャーの能力によって
    このカードが自分の手札から捨てられる時、かわりに出してもよい"""
    if k != "k53_eienryusei" or s.over:
        return False
    if not (s.dcby or s.tp != i):
        return False                          # 自分が払うコストで捨てる分では出ない
    p = s.P[i]
    if k not in p.hand or s.fate(i, k, "hand", False) != "ok":
        return False
    p.hand.remove(k)
    s.ev("　マッドネス：永遠のリュウセイ・カイザーは捨てられるかわりにバトルゾーンへ")
    s.enter(i, k, "hand", False)
    return True


add("k53_eienryusei", "永遠のリュウセイ・カイザー", 8, "F", power=8000, brk=2,
    races=("redcommanddragon", "command", "dragon", "hunter"), pri=11, roles="atk fin dis",
    saok=sa_eienryusei, enterwatch=ew_eienryusei, discardx=dx_eienryusei,
    text="W・ブレイカー。自分のクリーチャーすべてに「スピードアタッカー」を与える。"
         "相手のクリーチャーは、タップして出る。"
         "相手の呪文の効果または相手のクリーチャーの能力によって、"
         "このクリーチャーが自分の手札から捨てられる時、かわりに出してもよい（マッドネス）",
    note="マッドネスの「相手の呪文・能力によって」は、エンジンの s.dcby（相手の能力で捨てさせられた印）と、"
         "「相手のターン中に自分の手札から捨てられた」ことで見ている。"
         "もとからあるカード（ロビンフッド・ヴァミリアなど）は s.discard を by_opp 無しで呼ぶので、"
         "s.dcby だけでは拾えないため（REQUEST_53.md に書いた）。"
         "そのため、相手のターン中に自分のS・トリガー呪文で自分の手札を捨てた時にも誘発する（まれな場面）",
    source=SRC["k53_eienryusei"])
