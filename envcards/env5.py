"""赤白アーマード・サムライ（クロスギア） と 禁断型 火自然バイク（侵略）

  クロスギアのジェネレート／クロス、侍流ジェネレート、メクレイド、侵略・S級侵略、パワード・ブレイカー、
  Zラッシュ、ハイパーモードを実装した。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move, opp_all
import playable3

from envcards.env0 import FREECROSS, GEARRED, crossed, gears_on, is_cmd, lock_until_my_turn, owner_of


def _cmd_sources(deck, k, civ):
    """侵略元になるコマンド（文明が合うもの）の枚数"""
    return sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
               and "command" in BY_KEY[kk].races and (civ is None or civ in BY_KEY[kk].civ))

W = "https://dmwiki.net/"
SAM = "samurai"
DRA = "dragon"


def _mine(s, i, pred):
    return [u for u in s.P[i].board if pred(u)]


def _elems(s, i, civ=None):
    """自分のエレメント（クリーチャー・タマシード・クロスギア・G城）の数。civ を指定するとその文明のもの"""
    return sum(1 for u in s.P[i].board if civ is None or civ in u.c.civ)


def _mekureido(s, i, n, pred, what):
    """メクレイドX：山札の上3枚から、条件に合うカード1枚をコストを支払わずに使う"""
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
        p.hand.append(best)
        s.ev(f"　{what}：{BY_KEY[best].name} をただで使う")
        if not free_play(s, i, best):
            p.hand.remove(best)
            top.append(best)
    for k in top:
        p.deck.insert(0, k)


# ================================================================ 赤白サムライ
add("n_kottopi", "コットピ・ルピア", 2, "F", power=2000, zrush=True, races=("firebird", "hyperbeast"), pri=5,
    roles="acc atk",
    costaura=lambda s, i, k, cur: max(0, cur - 1) if (DRA in BY_KEY[k].races or "hyperbeast" in BY_KEY[k].races)
    and any(z.k == "n_kottopi" for z in s.P[i].board) and cur > 0 else cur,
    saok=lambda s, i, u: (DRA in u.c.races or ("hyperbeast" in u.c.races and u.k != "n_kottopi"))
    and any(z.k == "n_kottopi" and z.hyper for z in s.P[i].board),
    text="自分のドラゴンと超化獣の召喚コストを1少なくする（0より下がらない）。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモード（パワー5000）。"
         "ハイパーモード中、自分のドラゴンと他の超化獣すべてにスピードアタッカーを与える",
    source=W + "《コットピ・ルピア》")
E.HYPER_POW["n_kottopi"] = 3000


def _samurai_gen(s, i, u):
    """侍流ジェネレート：出た時、手札のクロスギア1枚をただでジェネレートしてよい"""
    p = s.P[i]
    gs = [k for k in sorted(set(p.hand)) if BY_KEY[k].kind == "X"]
    if not gs:
        return
    k = max(gs, key=E.PRI.get)
    s.ev(f"　侍流ジェネレート：{BY_KEY[k].name}")
    free_play(s, i, k)


def _buei_shot(s, i, u):
    """自分のシールドを1つブレイクして、相手のパワー6000以下を破壊する"""
    p = s.P[i]
    t = s.target(i, lambda z: s.power(1 - i, z) <= 6000)
    if t is None or not p.sh:
        return
    s.break_sh(1 - i, 1)                    # 自分のシールドをブレイクする（S・トリガーも働く）
    if t in s.P[1 - i].board:
        destroy(s, i, t)


def e_buei(s, i, u):
    _samurai_gen(s, i, u)
    _buei_shot(s, i, u)


add("n_buei", "ボルメテウス・武者・ドラゴン「武偉」", 4, "F", power=6000, brk=2,
    races=("armoreddragon", DRA, "armoredsamurai", SAM), pri=7, roles="rem atk",
    enter=e_buei, attack=_buei_shot,
    text="W・ブレイカー。侍流ジェネレート：出た時、自分の手札にあるクロスギア1枚をコストを支払わずにジェネレートしてよい。"
         "出た時と攻撃する時、自分のシールドを1つブレイクしてよい。そうしたら、相手のパワー6000以下のクリーチャー1体を破壊する",
    source=W + "《ボルメテウス・武者・ドラゴン「武偉」》")


def e_musashi(s, i, u):
    """出た時、自分の火のエレメントの数以下のコストの相手のエレメント1つを破壊し、
    自分の光のエレメント1つにつき1枚引く"""
    n = _elems(s, i, "F")
    t = s.target(i, lambda z: z.c.cost <= n, "CTX")
    if t is not None:
        destroy(s, i, t)
    d = _elems(s, i, "L")
    if d:
        s.draw(i, d)


def a_musashi(s, i, u):
    """攻撃する時、手札から、手札の枚数以下のコストの進化でないサムライかアーマードを1枚ただで使う"""
    p = s.P[i]
    n = len(p.hand)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.cost > n or (c.evo and not c.neo):
            continue
        if not (SAM in c.races or "armoredsamurai" in c.races or "armoreddragon" in c.races):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　ムサシ「弐天」：{BY_KEY[best].name} をただで使う")
        free_play(s, i, best)


add("n_musashi", "ヴァルキリアス・武者・ムサシ「弐天」", 5, "LF", power=6000, brk=2, gs=True,
    races=("armoreddragon", DRA, "armoredsamurai", SAM), pri=8, roles="rem draw atk trg",
    enter=e_musashi, attack=a_musashi,
    text="G・ストライク、W・ブレイカー。出た時、自分の火のエレメントの数以下のコストを持つ相手のエレメント1つを破壊し、"
         "その後、自分の光のエレメント1つにつき1枚引いてよい。"
         "攻撃する時、自分の手札から、手札の枚数以下のコストを持つ進化でないサムライかアーマードを1枚、"
         "コストを支払わずに使ってよい", source=W + "《ヴァルキリアス・武者・ムサシ「弐天」》")


def _firebirds(s, i):
    return sum(1 for z in s.P[i].board if "firebird" in z.c.races)


def e_arkzeos(s, i, u):
    _mekureido(s, i, 5, lambda c: "armoreddragon" in c.races or "armoredsamurai" in c.races, "アーマード・メクレイド5")


def w_arkzeos(s, i, u):
    """各ターン1度、自分のファイアー・バードが出た時、相手のクリーチャー1体とバトルしてよい"""
    if "firebird" not in u.c.races:
        return
    p = s.P[i]
    for z in p.board:
        if z.k == "n_arkzeos" and p.x.get("ark_turn") != s.turn:
            w = s.power(i, z)
            t = s.target(i, lambda x: s.power(1 - i, x) < w)
            if t is not None:
                p.x["ark_turn"] = s.turn
                s.ev(f"　アークゼオスが {t.c.name} とバトル")
                s.battle(i, z, 1 - i, t)
            return


add("n_arkzeos", "ボルシャック・アークゼオス", 5, "F", power=5000, races=("armoreddragon", DRA), pri=8, roles="rem atk fin",
    enter=e_arkzeos, enterwatch=w_arkzeos,
    powerx=lambda s, i, u, atk: 3000 * _firebirds(s, i) if u.k == "n_arkzeos" else 0,
    brkx=lambda s, i, u: 1 + s.power(i, u, True) // 6000 if u.k == "n_arkzeos" else None,
    text="パワード・ブレイカー（パワー6000ごとにブレイクするシールドが1つ増える）。"
         "自分のファイアー・バード1体につきこのクリーチャーのパワー+3000。"
         "出た時、アーマード・メクレイド5（山札の上から3枚を見て、その中のコスト5以下のアーマードを1枚ただで使ってよい）。"
         "各ターン1度、自分のファイアー・バードが出た時、相手のクリーチャー1体を選んでバトルしてもよい",
    source=W + "《ボルシャック・アークゼオス》")


def e_mdante12(s, i, u):
    """出た時、手札の光のコスト5以下の呪文を1枚ただで唱えてよい。唱えなければ1枚引く。
    ファイナル革命：革命チェンジで出た時、次の相手のターンの終わりまで相手はコスト7以下のクリーチャーを召喚できない"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "S" and "L" in c.civ and c.cost <= 5 and s.spell_ok(i, c.cost) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　ミラダンテⅫ：{BY_KEY[best].name} をただで唱える")
        free_play(s, i, best)
    else:
        s.draw(i)
    if s.atk is u and p.x.get("finrev_t") != s.turn:
        p.x["finrev_t"] = s.turn            # ファイナル革命は、どのカードでも1ターンに1回だけ
        s.P[1 - i].x["no7"] = s.turn + 2
        s.ev("　ファイナル革命：相手は次のターンの終わりまでコスト7以下を召喚できない")


def fx_mdante12(s, owner, u, i, k, src, summon, res):
    if i != owner and summon and BY_KEY[k].cost <= 7 and s.P[i].x.get("no7", -1) >= s.turn:
        return "no"
    return res


add("n_mdante12", "時の法皇 ミラダンテⅫ", 8, "LW", power=12000, brk=3, races=("angelcommand", DRA, "revolution", "command"),
    pri=12, roles="fin dis draw",
    enter=e_mdante12, fatex=fx_mdante12,
    changex=lambda s, i, u: bool(set("LW") & set(u.c.civ)) and DRA in u.c.races and u.c.cost >= 5,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                         and set("LW") & set(BY_KEY[kk].civ) and DRA in BY_KEY[kk].races
                                         and BY_KEY[kk].cost >= 5) >= 3 else "革命チェンジの元が3体いない",
    text="革命チェンジ（光か水のコスト5以上のドラゴンが攻撃する時、入れ替えて出せる）。T・ブレイカー。"
         "出た時、自分の手札から光のコスト5以下の呪文1枚をコストを支払わずに唱えてよい。唱えなければ1枚引く。"
         "ファイナル革命：革命チェンジで出た時、そのターンに他のファイナル革命を使っていなければ、"
         "次の相手のターンの終わりまで、相手はコスト7以下のクリーチャーを召喚できない",
    source=W + "《時の法皇 ミラダンテXII》")


def e_rafululu(s, i, u):
    s.P[1 - i].x["nospell"] = s.turn + 2
    s.ev("　ラフルル・ラブ：相手は次のターンの終わりまで呪文を唱えられない")


def sp_rafululu(s, i):
    p = s.P[i]
    s.draw(i, 3)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "S" and c.cost <= 5 and s.spell_ok(i, c.cost) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　「未来から来る、だからミラクル」：{BY_KEY[best].name} をただで唱える")
        free_play(s, i, best)


add("n_rafululu", "音卿の精霊龍 ラフルル・ラブ / 「未来から来る、だからミラクル」", 7, "LW", power=7000, brk=2,
    races=("angelcommand", DRA, "revolution", "command"), twin=(6, "LW", False), pri=10, roles="dis draw fin",
    enter=e_rafululu, spell=sp_rafululu,
    changex=lambda s, i, u: bool(set("LW") & set(u.c.civ)) and DRA in u.c.races,
    spelllock=lambda s, i, cost: s.P[i].x.get("nospell", -1) >= s.turn,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                         and set("LW") & set(BY_KEY[kk].civ) and DRA in BY_KEY[kk].races) >= 3
    else "革命チェンジの元が3体いない",
    text="クリーチャー側：革命チェンジ（光か水のドラゴン）。W・ブレイカー。"
         "出た時、次の相手のターンの終わりまで、相手は呪文を唱えられない。"
         "呪文側「未来から来る、だからミラクル」（コスト6）：3枚引く。その後、手札からコスト5以下の呪文1枚を"
         "コストを支払わずに唱えてよい", source=W + "《音卿の精霊龍 ラフルル・ラブ》")


# ================================================================ クロスギア
def _is_dra_sam(c):
    return DRA in c.races or SAM in c.races or "armoredsamurai" in c.races


add("n_zangeki", "竜装 ザンゲキ・マッハアーマー", 4, "F", kind="X", races=(SAM,), pri=6, roles="acc atk",
    costaura=lambda s, i, k, cur: max(0, cur - 1) if _is_dra_sam(BY_KEY[k]) and cur > 0 and any(
        z.c.kind == "X" and z.k == "n_zangeki" and crossed(s, i, z) is None for z in s.P[i].board) else cur,
    aurap=lambda s, i, u, atk: 2000 if u.c.kind == "C" and _is_dra_sam(u.c) and any(
        z.k == "n_zangeki" and (lambda c: c is not None and _is_dra_sam(c.c))(crossed(s, i, z))
        for z in s.P[i].board if z.c.kind == "X") else 0,
    saok=lambda s, i, u: _is_dra_sam(u.c) and any(
        z.k == "n_zangeki" and (lambda c: c is not None and _is_dra_sam(c.c))(crossed(s, i, z))
        for z in s.P[i].board if z.c.kind == "X"),
    text="クロスギア。クロスされていない間、自分のドラゴンとサムライの召喚コストを1少なくする。"
         "ドラゴンかサムライにクロスされている間、自分のドラゴンとサムライすべてのパワーを+2000し、"
         "スピードアタッカーを与える。《ボルメテウス・武者・ドラゴン》という名前のクリーチャーには"
         "コストを支払わずにクロスしてよい", source=W + "《竜装 ザンゲキ・マッハアーマー》")
FREECROSS["n_zangeki"] = lambda s, i, gu, cu: cu.k == "n_buei"


def e_dosufang(s, i, u):
    _mekureido(s, i, 5, lambda c: SAM in c.races or "armoredsamurai" in c.races or "technosamurai" in c.races,
               "サムライ・メクレイド5")


def w_dosufang(s, i, u):
    """クロス先のクリーチャーが攻撃する時にもサムライ・メクレイド5"""
    if any(g.k == "n_dosufang" for g in gears_on(s, i, u)):
        e_dosufang(s, i, u)


add("n_dosufang", "竜牙 リュウジン・ドスファング", 5, "LF", kind="X",
    races=("armoreddragon", DRA, "armoredsamurai", SAM), pri=7, roles="atk draw",
    enter=e_dosufang, atkwatch=w_dosufang,
    text="クロスギア。ジェネレートされた時、またはクロスされているクリーチャーが攻撃する時、サムライ・メクレイド5"
         "（山札の上から3枚を見て、その中のコスト5以下のサムライを1枚ただで使ってよい）。"
         "サムライ・クリーチャーにはコストを支払わずにクロスしてよい", source=W + "《竜牙 リュウジン・ドスファング》")
FREECROSS["n_dosufang"] = lambda s, i, gu, cu: SAM in cu.c.races or "armoredsamurai" in cu.c.races


def e_taisho(s, i, u):
    """ジェネレートされた時、山札の上3枚からサムライを好きな数手札に加える"""
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if SAM in BY_KEY[k].races or "armoredsamurai" in BY_KEY[k].races
           or "technosamurai" in BY_KEY[k].races]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    if got:
        s.ev(f"　天装 タイショウ・アームズ：サムライ{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)


add("n_taisho", "天装 タイショウ・アームズ", 3, "L", kind="X", races=("angelcommand", "armoredsamurai", SAM), pri=5,
    roles="draw blk", enter=e_taisho,
    blockok=lambda s, u: u.c.kind == "C" and any(g.k == "n_taisho" for g in gears_on(s, owner_of(s, u), u)),
    text="クロスギア。ジェネレートされた時、山札の上から3枚を見て、その中のサムライを好きな数だけ手札に加え、"
         "残りを山札の下に置く。クロスされているクリーチャーにブロッカーを与える",
    source=W + "《天装 タイショウ・アームズ》")


add("n_sengoku", "竜装 センゴク・トッパアーマー", 3, "F", kind="X", races=(SAM,), pri=5, roles="acc atk",
    costaura=lambda s, i, k, cur: max(0, cur - 1) if DRA in BY_KEY[k].races and cur > 0 and any(
        z.k == "n_sengoku" and crossed(s, i, z) is None for z in s.P[i].board if z.c.kind == "X") else cur,
    aurap=lambda s, i, u, atk: 2000 * sum(1 for g in gears_on(s, i, u) if g.k == "n_sengoku") if u.c.kind == "C" else 0,
    brkplus=lambda s, i, u: sum(1 for g in gears_on(s, i, u) if g.k == "n_sengoku") if u.c.kind == "C" else 0,
    text="クロスギア。クロスされていない間、自分のドラゴンの召喚コストを1少なくしてよい（0以下にはならない）。"
         "クロスされているクリーチャーのパワーを+2000し、シールドを1つ多くブレイクする。"
         "名前に《武者》《大和》《紫電》とある自分のクリーチャーにはコストを支払わずにクロスしてよい",
    source=W + "《竜装 センゴク・トッパアーマー》")
FREECROSS["n_sengoku"] = lambda s, i, gu, cu: any(x in cu.c.name for x in ("武者", "大和", "紫電"))


def _gousoku_here(s, i):
    return any(z.k == "n_gousoku" for z in s.P[i].board if z.c.kind == "X")


add("n_gousoku", "竜装 ゴウソク・タキオンアーマー", 2, "F", kind="X",
    races=("armoreddragon", DRA, "armoredsamurai", SAM), pri=4, roles="acc",
    costaura=lambda s, i, k, cur: max(0, cur - 1) if (SAM in BY_KEY[k].races or "armoredsamurai" in BY_KEY[k].races)
    and cur > 0 and _gousoku_here(s, i) else cur,
    aurap=lambda s, i, u, atk: 1000 * sum(1 for g in gears_on(s, i, u) if g.k == "n_gousoku") if u.c.kind == "C" else 0,
    text="クロスギア。自分のクロスギアをジェネレートするコストとクロスするコストを1少なくする（0以下にはならない）。"
         "自分のサムライ・クリーチャーの召喚コストを1少なくする。クロスされているクリーチャーのパワーを+1000",
    source=W + "《竜装 ゴウソク・タキオンアーマー》")
GEARRED.append(lambda s, i, k: 1 if _gousoku_here(s, i) else 0)


# ================================================================ 禁断型 火自然バイク
def e_rowin(s, i, u):
    """出た時、自分のマナゾーンのカード1枚を手札に戻してよい。戻したら、自分の墓地から2枚までマナゾーンに置く"""
    p = s.P[i]
    if not p.mana or not p.grave:
        return
    k = max(p.mana, key=E.PRI.get)
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　ザ・ロウィン：マナから {BY_KEY[k].name} を手札へ")
    for _ in range(2):
        if not p.grave:
            break
        g = max(p.grave, key=E.PRI.get)
        p.grave.remove(g)
        s.add_mana(i, g)


add("n_rowin", "轟速 ザ・ロウィン", 3, "FN", power=4000, sa=True, mach=True, gs=True,
    races=("soniccommand", "command", "invader"), pri=6, roles="atk acc trg", enter=e_rowin,
    text="G・ストライク、スピードアタッカー、マッハファイター。出た時、自分のマナゾーンのカード1枚を手札に戻してよい。"
         "そうしたら、自分の墓地からカード2枚までをマナゾーンに置く", source=W + "《轟速 ザ・ロウィン》")


def _dock_here(s, i):
    return any(z.k == "n_dock" or "n_dock" in z.under for z in s.P[i].board)


def w_dock(s, i, u):
    """相手のエレメントが手札以外から出た時、それを破壊する"""
    if not _dock_here(s, 1 - i):
        return
    if u.x.get("summoned") is False and u in s.P[i].board:
        s.ev(f"　ザ・ドック：踏み倒された {u.c.name} を破壊")
        s.leave(i, u, "grave", by_opp=True, destroy=True)


add("n_dock", "轟速 ザ・ドック", 3, "F", power=3000, sa=True, races=("soniccommand", "command", "invader", "fusioner"),
    pri=6, roles="atk rem", enterwatch=w_dock,
    saok=lambda s, i, u: "n_dock" in u.under,
    text="スピードアタッカー。相手のエレメントが相手の手札以外から出た時、そのエレメントを破壊する"
         "（召喚や呪文で出たものは破壊しない）。超魂X：このカードがクリーチャーの下にあるなら、"
         "その上のクリーチャーにもスピードアタッカーと上の破壊能力を与える", source=W + "《轟速 ザ・ドック》")


def e_redmad(s, i, u):
    """出た時、山札の上から1枚をマナゾーンに置き、そのカードよりコストが小さい相手のエレメント1つを破壊してよい"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    s.add_mana(i, k, src="deck")
    n = BY_KEY[k].cost
    s.ev(f"　レッドマッド：{BY_KEY[k].name} をマナへ（コスト{n}未満を破壊）")
    t = s.target(i, lambda z: z.c.cost < n, "CTX")
    if t is not None:
        destroy(s, i, t)


add("n_redmad", "S級原始 レッドマッド", 5, "WFN", power=8000, brk=2, jd=True, evo="WFN",
    races=("soniccommand", "command", "sinvader"), pri=9, roles="atk rem acc",
    enter=e_redmad, invade=lambda s, i, u: is_cmd(u.c),
    playrule=lambda deck, k: None if _cmd_sources(deck, k, None) >= 4 else "侵略元になるコマンドが4体いない",
    text="進化（自分の水・火・自然のクリーチャー1体の上に置く）。W・ブレイカー、ジャストダイバー。"
         "S級侵略［原始］：自分のコマンドが攻撃する時、手札またはマナゾーンからこのカードをその上に重ねてよい。"
         "出た時、自分の山札の上から1枚をマナゾーンに置く。その後、そのカードよりコストが小さい相手のエレメント1つを"
         "破壊してもよい", source=W + "《S級原始 レッドマッド》")
E.INVZONE["n_redmad"] = ("hand", "mana")


def ae_redzonef(s, i, u):
    """各ターン最初の攻撃の終わりに、アンタップして一番上（自分自身）を破壊する（下のコマンドが残る）"""
    if u.k != "n_redzonef" or u.x.get("rzf") == s.turn or not u.under:
        return
    p = s.P[i]
    if u not in p.board:
        return
    j = p.board.index(u)
    base, rest = u.under[0], u.under[1:]
    nu = E.U(base)
    nu.under = rest
    nu.tap = False
    nu.sick = False
    p.board[j] = nu
    s.note("surface", i, nu.k)
    s.grave_put(i, "n_redzonef")
    nu.x["rzf"] = s.turn
    s.ev(f"　レッドゾーンF：自身を破壊してアンタップした {nu.c.name} が残る")


add("n_redzonef", "覇帝なき侵略 レッドゾーンF", 6, "F", power=11000, brk=2, evo="F",
    races=("soniccommand", "command", "invader"), pri=10, roles="atk fin",
    atkend=ae_redzonef, invade=lambda s, i, u: is_cmd(u.c) and "F" in u.c.civ,
    playrule=lambda deck, k: None if _cmd_sources(deck, k, "F") >= 4 else "侵略元になる火のコマンドが4体いない",
    text="進化（自分の火のクリーチャー1体の上に置く）。W・ブレイカー。侵略［火のコマンド］。"
         "このクリーチャーの攻撃中、相手はG・ストライクを使えない。"
         "各ターン、このクリーチャーの最初の攻撃の終わりに、このクリーチャーをアンタップし、一番上のカード"
         "（このカード自身）を破壊する（下のコマンドがアンタップして残るので、もう一度侵略できる）",
    source=W + "《覇帝なき侵略 レッドゾーンF》")
E.NOGS.add("n_redzonef")


def e_redzonez(s, i, u):
    """進化でないクリーチャーの上に置かれた時、相手のシールド1つを相手の墓地に置く"""
    if not u.under or BY_KEY[u.under[0]].evo:
        return
    o = s.P[1 - i]
    if not o.sh:
        return
    j = next((j for j in range(len(o.sh) - 1, -1, -1) if not o.sh[j][1]), len(o.sh) - 1)
    o.grave.append(o.sh.pop(j)[0])
    s.shield_left()
    s.ev("　レッドゾーンZ：相手のシールド1つを墓地へ（ブレイクではない）")


add("n_redzonez", "熱き侵略 レッドゾーンZ", 6, "F", power=11000, brk=2, evo="F",
    races=("soniccommand", "command", "invader"), pri=10, roles="atk fin",
    enter=e_redzonez, invade=lambda s, i, u: is_cmd(u.c) and "F" in u.c.civ,
    playrule=lambda deck, k: None if _cmd_sources(deck, k, "F") >= 4 else "侵略元になる火のコマンドが4体いない",
    text="進化（自分の火のクリーチャー1体の上に置く）。W・ブレイカー。侵略［火のコマンド］。"
         "進化でないクリーチャーの上に置かれて出た時、相手のシールドを1つ選び、相手の墓地に置く"
         "（ブレイクではないのでS・トリガーは使えない）。殿堂入り（デッキに1枚）",
    source=W + "《熱き侵略 レッドゾーンZ》")


def sp_sekkeizu(s, i):
    """山札の上から6枚を見て、その中の進化クリーチャーをすべて手札に加える"""
    p = s.P[i]
    n = min(6, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    got = [k for k in top if BY_KEY[k].evo]
    for k in got:
        top.remove(k)
        p.hand.append(k)
    s.ev(f"　進化設計図：進化クリーチャー{len(got)}枚を手札へ")
    for k in top:
        p.deck.insert(0, k)


add("n_sekkeizu", "進化設計図", 2, "N", kind="S", trig=True, pri=4, roles="draw trg", spell=sp_sekkeizu,
    text="S・トリガー。自分の山札の上から6枚を見る。その中の進化クリーチャーをすべて手札に加え、"
         "残りを好きな順序で山札の下に置く", source=W + "《進化設計図》")


playable3.NOCOLOR.update({"n_redmad", "n_redzonef", "n_redzonez"})
