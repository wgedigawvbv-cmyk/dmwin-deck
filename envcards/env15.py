"""cardspec5.json の22枚（key は e_ 始まり）

  調べ直して直したところ（dmwiki のカード本文を読んで確かめた）
    ・終止の時計 ザ・ミュート：「S・トリガー・プラス」で、プラス側の能力（相手はクリーチャーで攻撃できない）は
      S・トリガーで出した時だけ働く。2枚引いて1枚捨てる方はいつでも働く。
    ・ガチンコ・ジャッジ：表向きにしたカードは山札の一番下に置く。同じコストなら仕掛けた側の勝ち（引き分けはない）。
      R.S.F.K. の本文は「自分が負けるか中止するまで繰り返し、勝った回数だけ相手のシールドをブレイクする」。
    ・剛撃聖霊シェバ・エリクシアの「バラバラエティ5」は、自分のバトルゾーンにコストの異なるエレメントが5つ以上ある時に働く。
    ・ルピア＆ガ：ナテハのターン終わりの能力は強制（「〜してもよい」ではない）。
    ・喜びの夜 エルボロム・ハッピーは光文明のデーモン・コマンド、料理猫のプワソンは光文明のドリームメイトで合っていた。
    ・DG-パルテノンは「DGフィールド」＝バトルゾーンに出る無色のカード。クロスギアではないので、
      このシミュレーターではタマシード（kind="T"）として扱った。
    ・禁断の轟速 ブラックゾーンの cardspec にあった「侵略時は出た時効果が起動しない」という注記は誤りなので無視した
      （S級侵略で出ても「出た時」は働く）。

  ドリームメイトの種族名は、すでにある《ピザスターのアンティハムト》と同じ "dream" を使っている。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move, free_play, worst_hand, is_cmd
from envcards.env0 import he_costx, he_payx, owner_of

W = "https://dmwiki.net/"
U_NATEHA = ("https://dmwiki.net/%E3%80%8A%E3%83%AB%E3%83%94%E3%82%A2%EF%BC%86"
            "%E3%82%AC%EF%BC%9A%E3%83%8A%E3%83%86%E3%83%8F%E3%80%8B")
U_PETENZ = "https://dmwiki.net/%E3%80%8A%E3%83%9A%E3%83%86%E3%83%B3%E3%82%BA%E3%83%BB%E3%82%B2%E3%83%BC%E3%83%88%E3%80%8B"


# ================================================================ この版で共通に使う小道具
def _atklock(s, i, u):
    """このターン攻撃できない：プレイヤーごと（e_noatk）とカード1枚ごと（e_noatk1）"""
    return s.P[i].x.get("e_noatk") == s.turn or u.x.get("e_noatk1") == s.turn


E.ATKLOCK.append(_atklock)


def _stop_atk(s, j):
    """このターン、プレイヤー j のクリーチャーは攻撃できない"""
    s.P[j].x["e_noatk"] = s.turn


def _dream(u):
    """自分のドリームメイト・クリーチャーか"""
    return u.c.kind == "C" and "dream" in u.c.races


def _ndream(s, i):
    return sum(1 for z in s.P[i].board if _dream(z))


def _evo_rule(civ, n=4):
    """進化元になれるクリーチャーが n 体いるか（playrule 用）"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and set(civ) & set(BY_KEY[kk].civ))
        return None if c >= n else f"進化元になる{civ}のクリーチャーが{n}体いない"
    return f


def gachinko(s, i):
    """ガチンコ・ジャッジを1回行う（勝ったら True）。互いに山札の上から1枚を見せて一番下に置く。
    同じコストなら仕掛けた側（i）の勝ち"""
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
    return BY_KEY[a].cost >= cb


# ================================================================ 終止の時計 ザ・ミュート
def e_myuto(s, i, u):
    """出た時：S・トリガーで出たならこのターン相手は攻撃できない。そして2枚引いて1枚捨てる"""
    p = s.P[i]
    if s.tp != i:                      # 相手のターンに出た＝S・トリガーで出た（S・トリガー・プラス）
        _stop_atk(s, 1 - i)
        s.ev("　S・トリガー・プラス：このターン、相手はクリーチャーで攻撃できない")
    if not p.deck:
        return
    n = len(p.hand)
    s.draw(i, 2)
    if s.over or len(p.hand) <= n:
        return
    k = worst_hand(s, i)
    if k is not None and k in p.hand:
        s.discard(i, k)


add("e_myuto", "終止の時計 ザ・ミュート", 3, "W", power=3000, trig=True, races=("magic", "outrage"), pri=4,
    roles="draw trg dis", enter=e_myuto,
    text="S・トリガー・プラス。出た時、2枚まで引いてもよく、引いたなら手札を1枚捨てる。"
         "S・トリガーで出した時は、さらにこのターン、相手はクリーチャーで攻撃できない",
    source=W + "《終止の時計 ザ・ミュート》")


# ================================================================ ルピア＆ガ：ナテハ
def t_nateha(s, i, u):
    """自分のターンの終わりに、自分のシールド1つを墓地に置き、その後1枚引く（強制）"""
    p = s.P[i]
    if not p.sh:
        return
    j = next((j for j in range(len(p.sh) - 1, -1, -1) if not p.sh[j][1]), len(p.sh) - 1)
    k = p.sh.pop(j)[0]
    s.grave_put(i, k)
    s.shield_left()
    s.ev(f"　ナテハ：自分のシールド1つ（{BY_KEY[k].name}）を墓地に置いて1枚引く")
    s.draw(i)


add("e_nateha", "ルピア＆ガ：ナテハ", 2, "D", power=2000, races=("firebird", "abyss"), pri=3, roles="draw",
    tend=t_nateha,
    text="自分のターンの終わりに、自分のシールドを1つ墓地に置く。その後、カードを1枚引く（強制）",
    source=U_NATEHA)


# ================================================================ ソウルサンライト コハク
def e_sunkohaku(s, i, u):
    """出た時：次の自分のターンのはじめまで、このクリーチャーは離れない"""
    u.x["e_noleave"] = s.turn + (1 if s.tp == i else 0)


def rep_sunkohaku(s, i, u, dest, destroy_):
    return u.x.get("e_noleave", -1) >= s.turn


def ca_sunkohaku(s, i, k, n):
    """自分のNEOクリーチャーの召喚コストを1少なくする（場にあるか、クリーチャーの下にあるか＝超魂X）"""
    if n <= 1 or not BY_KEY[k].neo:
        return n
    for z in s.P[i].board:
        if z.k == "e_sunkohaku" or "e_sunkohaku" in z.under:
            return n - 1
    return n


add("e_sunkohaku", "ソウルサンライト コハク", 2, "L", power=2000, races=("giant", "snow", "fusioner"), pri=3,
    roles="acc", enter=e_sunkohaku, leaverep=rep_sunkohaku, costaura=ca_sunkohaku,
    text="出た時、次の自分のターンのはじめまで、このクリーチャーはバトルゾーンを離れない。"
         "自分のNEOクリーチャーの召喚コストを1少なくする（1より下がらない）。"
         "超魂X：このカードがクリーチャーの下にあるなら、その上のクリーチャーもこのコスト軽減を持つ",
    source=W + "《ソウルサンライト コハク》")


# ================================================================ 宿禰マロン
def e_maron(s, i, u):
    """出た時：山札の上から4枚をタップしてマナへ置き、そうしたらマナから2枚を山札の上に置く"""
    p = s.P[i]
    before = len(p.mana)
    s.ramp(i, 4, True)
    if len(p.mana) <= before:
        return
    picks = []
    for _ in range(2):
        cands = [k for k in p.mana if k not in picks or p.mana.count(k) > picks.count(k)]
        if not cands:
            break
        picks.append(max(cands, key=E.PRI.get))
    picks.sort(key=E.PRI.get)              # 重要度の高いものを最後に置く＝山札の一番上になる
    for k in picks:
        if k in p.mana:
            s.take_mana(i, k)
            p.deck.append(k)
    if picks:
        s.ev(f"　宿禰マロン：マナから{len(picks)}枚を山札の上に置いた")


add("e_maron", "宿禰マロン", 5, "LFN", power=5500, blocker=True,
    races=("apollonia", "armoreddragon", "earthdragon", "dragon"), pri=7, roles="acc blk", enter=e_maron,
    text="ブロッカー。出た時、山札の上から4枚をタップしてマナゾーンに置いてもよい。"
         "そうしたら、自分のマナゾーンから2枚を好きな順で山札の上に置く（差し引き2枚マナが増える）",
    source=W + "《宿禰マロン》")


# ================================================================ ペテンズ・ゲート
def sp_petenz(s, i):
    """相手のクリーチャーをすべてタップし、1枚引いて、自分のシールドをすべてブレイクする"""
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            s.tap_cre(1 - i, z)
    s.draw(i)
    n = len(s.P[i].sh)
    if n and not s.over:
        s.ev("　ペテンズ・ゲート：自分のシールドをすべてブレイクする")
        s.break_sh(1 - i, n)               # 自分のシールドを割る（自分のS・トリガーが働く）


add("e_petenz", "ペテンズ・ゲート", 8, "LWD", kind="S", trig=True, pri=9, roles="dis draw trg", spell=sp_petenz,
    text="S・トリガー。相手のクリーチャーをすべてタップする。その後、自分は1枚引き、自分のシールドをすべてブレイクする"
         "（自分のS・トリガーが働く）",
    source=U_PETENZ)


# ================================================================ 料理猫のプワソン／料理長のラビシェフ（ドリームメイト）
def cx_pwason(s, i, av):
    """シンパシー：自分のドリームメイト1体につきコスト-1"""
    return max(1, 8 - _ndream(s, i))


def e_pwason(s, i, u):
    """出た時・攻撃する時：1枚引き、その後コスト5以下のドリームメイトを手札から1つ出してもよい"""
    s.draw(i)
    if s.over:
        return
    best, bv = None, -1
    for k in sorted(set(s.P[i].hand)):
        c = BY_KEY[k]
        if c.cost <= 5 and "dream" in c.races and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　プワソン：手札から {BY_KEY[best].name} を出す")
        free_play(s, i, best)


def bok_pwason(s, u):
    """自分のドリームメイトすべてにブロッカーを与える"""
    if not _dream(u):
        return False
    return s.has(owner_of(s, u), "e_pwason")


add("e_pwason", "料理猫のプワソン", 8, "L", power=9500, brk=2, evo="dream", races=("dream",), pri=10,
    roles="draw blk atk fin", enter=e_pwason, attack=e_pwason, costx=cx_pwason, blockok=bok_pwason,
    evox=lambda s, i, u: u.c.kind == "C" and "dream" in u.c.races,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items() if kk != k and BY_KEY[kk].kind == "C"
                                         and "dream" in BY_KEY[kk].races) >= 4 else "進化元のドリームメイトが4体いない",
    text="進化（自分のドリームメイト・クリーチャー1体の上に置く）。W・ブレイカー。"
         "シンパシー：自分のドリームメイト1体につき召喚コストが1少なくなる（1より下がらない）。"
         "出た時または攻撃する時、1枚引き、その後コスト5以下のドリームメイトを1つ、手札から出してもよい。"
         "自分のドリームメイト・クリーチャーすべてに「ブロッカー」を与える",
    source=W + "《料理猫のプワソン》")


def e_rabishef(s, i, u):
    """出た時：自分のドリームメイト1体につき1枚引いてもよい"""
    n = _ndream(s, i)
    if n:
        s.draw(i, n)


def w_rabishef(s, i, u):
    """自分のドリームメイトが攻撃する時、相手のクリーチャー1体をタップしてもよい"""
    if not _dream(u) or not s.has(i, "e_rabishef"):
        return
    t = s.target(i, lambda z: not z.tap)
    if t is not None:
        s.tap_cre(1 - i, t)
        s.ev(f"　ラビシェフ：{t.c.name} をタップ")


def ap_rabishef(s, i, u, atk):
    """自分の他のドリームメイトのパワーを+3000"""
    if u.k == "e_rabishef" or not _dream(u) or not s.has(i, "e_rabishef"):
        return 0
    return 3000


def bp_rabishef(s, i, u):
    """自分の他のドリームメイトにパワード・ブレイカー（パワー6000ごとに1枚多く割る）"""
    if u.k == "e_rabishef" or not _dream(u) or not s.has(i, "e_rabishef"):
        return 0
    return max(0, 1 + s.power(i, u, True) // 6000 - u.c.brk)


add("e_rabishef", "料理長のラビシェフ", 5, "LN", power=5500, blocker=True, races=("dream",), pri=7,
    roles="draw blk dis atk", enter=e_rabishef, atkwatch=w_rabishef, aurap=ap_rabishef, brkplus=bp_rabishef,
    text="ブロッカー。出た時、自分のドリームメイト1体につき1枚引いてもよい。"
         "自分のドリームメイトが攻撃する時、相手のクリーチャー1体をタップしてもよい。"
         "自分の他のドリームメイトすべてに「パワード・ブレイカー」を与え、パワーを+3000する",
    source=W + "《料理長のラビシェフ》")


# ================================================================ 我竜塔第八層 バルザーク（G城）
def _barzark_fire(s, j):
    p = s.P[j]
    k = worst_hand(s, j)
    if k is not None and k in p.hand:
        s.discard(j, k)
    s.draw(j, 2)


def dw_barzark(s, j, k):
    """各ターン、はじめて自分の手札を捨てた時、1枚引いてもよい（表向きのシールドとして置かれている間）"""
    p = s.P[j]
    if p.x.get("barzark_t") == s.turn:
        return
    for x, up in p.sh:
        if x == "e_barzark" and up:
            p.x["barzark_t"] = s.turn
            s.ev("　バルザーク：このターンはじめて手札を捨てた → 1枚引く")
            s.draw(j)
            return


def so_barzark(s, j, k, up, dest):
    """表向きのこのシールドがシールドゾーンを離れた時、手札を1枚捨てて2枚引く

    全体に効く差し込み口なので、離れたカードがこのカードの時だけ働く。
    shieldout はシールドゾーンの出口（take_shield）1か所を通るので、
    ブレイクでも効果で手札やマナに行く時でも拾える。"""
    if k != "e_barzark" or not up:
        return
    s.ev("　バルザーク：表向きのシールドが離れた → 手札1枚を捨てて2枚引く")
    _barzark_fire(s, j)


add("e_barzark", "我竜塔第八層 バルザーク", 2, "F", kind="G", pri=3, roles="draw", shieldout=so_barzark,
    discardwatch=dw_barzark,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "各ターン、はじめて自分の手札を捨てた時、1枚引いてもよい。"
         "この表向きのシールドが表向きのままシールドゾーンを離れた時、自分の手札を1枚捨てて2枚引く",
    source=W + "《我竜塔第八層 バルザーク》")


# ================================================================ 禁断の轟速 ブラックゾーン
def e_blackzone(s, i, u):
    """出た時：相手は自身のパワーが一番小さいクリーチャーすべてに封印を1つずつ付ける"""
    o = s.P[1 - i]
    cs = [z for z in o.board if z.c.kind == "C"]
    if not cs:
        return
    mn = min(s.power(1 - i, z) for z in cs)
    for z in cs:
        if z in o.board and s.power(1 - i, z) == mn:
            s.seal(1 - i, z, 1)


def _df_cmd(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and is_cmd(BY_KEY[kk]) and set("DF") & set(BY_KEY[kk].civ))
    return None if n >= 4 else "侵略元になる闇か火のコマンドが4体いない"


add("e_blackzone", "禁断の轟速 ブラックゾーン", 7, "DF", power=12000, brk=3, evo="DF",
    races=("soniccommand", "command", "sinvader"), pri=11, roles="atk fin dis rem",
    enter=e_blackzone, invade=lambda s, i, u: is_cmd(u.c) and bool(set("DF") & set(u.c.civ)), playrule=_df_cmd,
    text="進化（自分の闇または火のクリーチャー1体の上に置く）。T・ブレイカー。"
         "S級侵略［轟速］：自分の闇または火のコマンドが攻撃する時、手札・墓地・バトルゾーンから"
         "このカードをその上に重ねてよい。"
         "出た時、相手は自身のパワーが一番小さいクリーチャーすべてに封印を1つずつ付ける",
    source=W + "《禁断の轟速 ブラックゾーン》")
E.INVZONE["e_blackzone"] = ("hand", "grave", "board")


# ================================================================ 飛ベル津バサ「曲通風」
add("e_hiberutsubasa", "飛ベル津バサ「曲通風」", 2, "W", power=2000, gs=True, jd=True,
    races=("adamunit", "demonio", "rexstars"), pri=3, roles="trg dis", status="partial",
    note="「相手が自身の山札を1枚以上見る時または表向きにする時、かわりに山札の上から1枚目を表向きにする」"
         "置換効果は省いた。山札を見る処理がエンジンの dig・revive・mill と各カードのサーチに散っていて、"
         "まとめて通す差し込み口（DECKLOOK）がないため",
    text="G・ストライク（シールドから手札に加える時に表向きにし、相手のクリーチャー1体を選べる。"
         "このターンそれは攻撃できない）。ジャストダイバー（出た時、次の自分のターンのはじめまで相手に選ばれず攻撃されない）",
    source=W + "《飛ベル津バサ「曲通風」》")


# ================================================================ DG-パルテノン ～龍の創り出される地～
def e_parthenon(s, i, u):
    s.draw(i)


def fx_parthenon(s, owner, u, i, k, src, summon, res):
    """すべてのプレイヤーは各ターン、クリーチャーを3体までしか出せない"""
    if s.P[i].ent >= 3:
        return "no"
    return res


def sl_parthenon(s, i, cost):
    """すべてのプレイヤーは各ターン、呪文を3枚までしか唱えられない"""
    return s.P[i].spl >= 3 and (s.has(i, "e_parthenon") or s.has(1 - i, "e_parthenon"))


add("e_parthenon", "DG-パルテノン ～龍の創り出される地～", 2, "", kind="T", pri=3, roles="draw dis",
    enter=e_parthenon, fatex=fx_parthenon, spelllock=sl_parthenon,
    text="無色のDGフィールド（バトルゾーンに出て残るカード。このシミュレーターではタマシードとして扱う）。"
         "出た時、1枚引く。すべてのプレイヤーは各ターン、クリーチャーを3体までしか出せず、呪文を3枚までしか唱えられない",
    source=W + "《DG-パルテノン 〜龍の創り出される地〜》")
E.STAY.add("e_parthenon")


# ================================================================ 神判のカルマ コットン／ジャッジ・水晶チャージャー
def w_cotton(s, i, u):
    """相手のクリーチャーが出た時、そのターン、そのクリーチャーは攻撃できない"""
    if u.c.kind != "C" or not s.has(1 - i, "e_cotton"):
        return
    u.x["e_noatk1"] = s.turn
    s.ev(f"　コットン：{u.c.name} はこのターン攻撃できない")


def sp_cotton(s, i):
    """相手のマナゾーンの枚数よりコストが大きい相手のエレメント1つを山札の下へ。その後、この呪文はマナゾーンへ"""
    n = len(s.P[1 - i].mana)
    t = s.target(i, lambda z: z.c.cost > n, "CTX")
    if t is not None:
        move(s, i, t, "deck")
    s.add_mana(i, "e_cotton")


add("e_cotton", "神判のカルマ コットン / ジャッジ・水晶チャージャー", 2, "L", power=2000,
    races=("oracleceres", "humanoid"), twin=(3, "L", False), pri=4, roles="dis rem acc",
    enterwatch=w_cotton, spell=sp_cotton, nograve=True,
    text="クリーチャー側：相手のクリーチャーが出た時、そのターン、そのクリーチャーは攻撃できない。"
         "呪文側（ジャッジ・水晶チャージャー、光3）：相手のマナゾーンのカードの枚数よりコストが大きい相手のエレメント1つを"
         "持ち主の山札の下に置く。水晶チャージャー：唱えた後、墓地に置くかわりにマナゾーンに置く"
         "（本来は裏向きだが、このシミュレーターでは表向きで置く）",
    source=W + "《神判のカルマ コットン／ジャッジ・水晶チャージャー》")


# ================================================================ R.S.F.K.／オールイン・チャージャー
def a_rsfk(s, i, u):
    """攻撃する時：負けるまでガチンコ・ジャッジをくり返し、勝った回数だけ相手のシールドをブレイクする"""
    n = 0
    for _ in range(20):
        if not gachinko(s, i):
            break
        n += 1
    s.ev(f"　R.S.F.K.：ガチンコ・ジャッジに{n}回勝った")
    if n and s.P[1 - i].sh and not s.over:
        s.break_sh(i, n)


def sp_allin(s, i):
    """ガチンコ・ジャッジに勝てば1枚引く。チャージャー：唱えた後マナゾーンへ"""
    if gachinko(s, i):
        s.ev("　オールイン・チャージャー：ガチンコ・ジャッジに勝って1枚引く")
        s.draw(i)
    s.add_mana(i, "e_rsfk")


add("e_rsfk", "R.S.F.K. / オールイン・チャージャー", 7, "F", power=5000, sa=True,
    races=("redcommanddragon", "command", "dragon", "hunter", "alien"), twin=(3, "F", False), pri=9,
    roles="atk fin acc draw", attack=a_rsfk, spell=sp_allin, nograve=True,
    text="クリーチャー側：スピードアタッカー。攻撃する時、自分が負けるまで相手とガチンコ・ジャッジをくり返し、"
         "勝った回数だけ相手のシールドをブレイクする（ガチンコ・ジャッジ＝互いに山札の上から1枚を見せて一番下に置き、"
         "コストが大きい方が勝つ。同じコストなら仕掛けた側の勝ち）。"
         "呪文側（オールイン・チャージャー、火3）：ガチンコ・ジャッジに勝てば1枚引く。チャージャー：唱えた後マナゾーンに置く",
    source=W + "《R.S.F.K.／オールイン・チャージャー》")


# ================================================================ 地封龍 ギャイア
def fx_gyaia(s, owner, u, i, k, src, summon, res):
    """相手の「出た時」能力を持つクリーチャーが出る時、かわりに持ち主のマナゾーンに置く"""
    if i != owner and res == "ok" and k in E.ENTER:
        return "mana"
    return res


def acts_gyaia(s, i, av, cv):
    """自分のターン中、自分のマナゾーンからクリーチャーを1体召喚してもよい（コストは支払う。各ターン1体）

    進化クリーチャーも、バトルゾーンに進化元がいれば召喚できる（NEO進化は進化元なしでもよい）。"""
    p = s.P[i]
    if not s.has(i, "e_gyaia") or s.manaexec(i) or p.x.get("e_gyaia_t") == s.turn:
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C":
            continue
        if c.evo and not c.neo and s.evo_src(i, k) is None:
            continue
        n = s.ccost(i, k, av)
        if n <= av and (n == 0 or cv.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:gyaia", k, n))
    return out


def ap_gyaia(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana:
        return
    on = s.evo_src(i, k) if BY_KEY[k].evo else None
    if BY_KEY[k].evo and not BY_KEY[k].neo and on is None:
        return
    p.x["e_gyaia_t"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"ギャイア：マナゾーンから召喚 {BY_KEY[k].name}（{a[2]}マナ）")
    s.enter(i, k, "mana", True, on=on)


add("e_gyaia", "地封龍 ギャイア", 9, "N", power=18000, brk=4, races=("gaiacommanddragon", "command", "dragon"),
    pri=12, roles="fin atk dis rem", fatex=fx_gyaia, freeacts=acts_gyaia, actapply={"x:gyaia": ap_gyaia},
    text="Q・ブレイカー。相手の「出た時」の能力を持つクリーチャーが出る時、かわりにそのクリーチャーを持ち主のマナゾーンに置く。"
         "自分のターン中、自分のマナゾーンからクリーチャーを1体召喚してもよい（コストは支払う。"
         "進化クリーチャーは、バトルゾーンの進化元の上に重ねて召喚する）",
    source=W + "《地封龍 ギャイア》")


# ================================================================ 天革の騎令嬢 ミラクルステラ
def _stella(s, i):
    """プレイヤー i が実行した：ステラの持ち主は1枚引き、このターン i のクリーチャーは攻撃できない"""
    j = 1 - i
    if not s.has(j, "e_mirastella"):
        return
    s.draw(j)
    _stop_atk(s, i)
    s.ev("　ミラクルステラ：1枚引き、このターン相手のクリーチャーは攻撃できない")


def w_stella_enter(s, i, u):
    if u.c.kind == "C" and u.x.get("summoned"):
        _stella(s, i)


def w_stella_spell(s, i, k):
    _stella(s, i)


add("e_mirastella", "天革の騎令嬢 ミラクルステラ", 6, "W", power=8000, brk=2, blocker=True, gs=True, jd=True,
    races=("angelcommanddragon", "command", "dragon", "revolution"), pri=8, roles="blk draw dis trg",
    enterwatch=w_stella_enter, spellwatch=w_stella_spell,
    status="partial",
    note="クリーチャーの召喚（enterwatch＋x[\"summoned\"]）と呪文（spellwatch）は拾えるが、"
         "タマシード・G城・クロスギアを相手が実行した時は検知できない。"
         "カードを実行した時に呼ばれる差し込み口（PLAYWATCH）がエンジンになく、"
         "place_tama／place_castle／クロスギアの実行に見張りがないため",
    text="G・ストライク、ブロッカー、ジャストダイバー、W・ブレイカー。"
         "相手がカードを実行した時、自分は1枚引いてもよい。このターン、相手のクリーチャーは攻撃できない",
    source=W + "《天革の騎令嬢 ミラクルステラ》")


# ================================================================ うららかもも＆ミノマル ー献身のヒロインー
def cx_urara(s, i, av):
    """G・ゼロ：自分のパワー12000以上のクリーチャーが4体以上あれば0マナ"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and s.power(i, z) >= 12000)
    return 0 if n >= 4 else 10


def sl_urara(s, i, cost):
    """相手がクリーチャーでないカードを実行するのを止める（マナゾーンへの置き換えの近似）"""
    return s.has(1 - i, "e_urara")


add("e_urara", "うららかもも＆ミノマル ー献身のヒロインー", 10, "N", power=15000, brk=3, gs=True, mach=True,
    evo="N", neo=True, races=("gransect",), pri=12, roles="fin atk dis trg",
    costx=cx_urara, spelllock=sl_urara,
    status="partial",
    note="「各ターンに一度、相手のクリーチャーでないカードを、かわりに持ち主のマナゾーンに置いてもよい」を、"
         "相手が呪文を唱えられないという形で近似した。カードの実行そのものを置き換える差し込み口（EXECREP）が"
         "エンジンになく、実行の入口が apply の play／spell の枝と cast／place_tama／place_castle に分かれている"
         "ため、「かわりにマナゾーンに置く」という形には書けない"
         "（そのため、実際には止められるのが呪文だけで、各ターン1回ではなくそのターン中ずっとになっている）",
    text="NEO進化（自分の自然のクリーチャー1体の上に置いてもよい）。T・ブレイカー、マッハファイター、G・ストライク。"
         "G・ゼロ：自分のパワー12000以上のクリーチャーが4体以上あれば、コストを支払わずに召喚してもよい。"
         "各ターンに一度、相手がクリーチャーでないカードを実行する時、かわりにそのカードを持ち主のマナゾーンに置いてもよい",
    source="https://yuyu-tei.jp/index.php/buy/dm/card/dm25ex1/10118")


# ================================================================ 七王無き宮殿
def sp_shichiou(s, i):
    """相手は手札を見せ、その中の多色カードをすべて捨てる"""
    o = s.P[1 - i]
    for k in [x for x in o.hand if E.MULTI[x]]:
        if k in o.hand:
            s.discard(1 - i, k)


add("e_shichiou", "七王無き宮殿", 4, "D", kind="S", pri=5, roles="dis", spell=sp_shichiou,
    text="相手は自分の手札を見せ、その中の多色カードをすべて捨てる", source=W + "《七王無き宮殿》")


# ================================================================ 時の革命 ミラダンテ
def e_miradante(s, i, u):
    """出た時：相手のクリーチャーをすべてタップし、次の相手のターンのはじめにアンタップしない"""
    for z in s.P[1 - i].board:
        if z.c.kind == "C":
            s.tap_cre(1 - i, z)
            z.frz = 1
    s.ev("　ミラダンテ：相手のクリーチャーをすべてタップ（次の相手のターンにアンタップしない）")


def fx_miradante(s, owner, u, i, k, src, summon, res):
    """革命0：自分のシールドが1枚もなければ、相手はクリーチャーを召喚できない"""
    if i != owner and summon and not s.P[owner].sh:
        return "no"
    return res


add("e_miradante", "時の革命 ミラダンテ", 8, "L", power=13500, brk=3, evo="L",
    races=("angelcommanddragon", "command", "dragon", "revolution"), pri=11, roles="fin atk dis",
    enter=e_miradante, fatex=fx_miradante, playrule=_evo_rule("L"),
    text="進化（自分の光のクリーチャー1体の上に置く）。T・ブレイカー。"
         "出た時、相手のクリーチャーをすべてタップする。それらは次の相手のターンのはじめにアンタップしない。"
         "革命0：自分のシールドが1枚もなければ、相手はクリーチャーを召喚できない",
    source=W + "《時の革命 ミラダンテ》")


# ================================================================ 剛撃聖霊シェバ・エリクシア
def e_sheba(s, i, u):
    """出た時：コストの合計が7以下になるように、自分のマナゾーンからクリーチャーを2体まで出す"""
    p = s.P[i]
    budget = 7
    for _ in range(2):
        best, bv = None, -1
        for k in sorted(set(p.mana)):
            c = BY_KEY[k]
            if c.kind == "C" and not c.evo and c.cost <= budget and E.PRI[k] > bv:
                if s.fate(i, k, "mana", False) == "ok":
                    best, bv = k, E.PRI[k]
        if best is None:
            return
        s.take_mana(i, best)
        budget -= BY_KEY[best].cost
        s.ev(f"　シェバ・エリクシア：マナゾーンから {BY_KEY[best].name}")
        s.enter(i, best, "mana", False)
        if s.over:
            return


def rep_sheba(s, i, u, dest, destroy_):
    """バラバラエティ5：自分のクリーチャーは破壊以外の方法では離れない"""
    if destroy_ or u.c.kind != "C" or not s.has(i, "e_sheba"):
        return False
    return len({z.c.cost for z in s.P[i].board}) >= 5


add("e_sheba", "剛撃聖霊シェバ・エリクシア", 8, "LN", power=18000, brk=4, blocker=True,
    races=("giant", "angelcommand", "command"), pri=11, roles="fin blk atk acc",
    enter=e_sheba, leaverep=rep_sheba,
    text="ブロッカー、Q・ブレイカー。出た時、コストの合計が7以下になるように、クリーチャーを2体まで自分のマナゾーンから出す。"
         "バラバラエティ5：自分のバトルゾーンにコストの異なるエレメントが5つ以上あれば、"
         "自分のクリーチャーは破壊以外の方法ではバトルゾーンを離れない",
    source=W + "《剛撃聖霊シェバ・エリクシア》")


# ================================================================ 喜びの夜 エルボロム・ハッピー
def ign_elborom(s, i, u):
    """自分のクリーチャーが持つ「攻撃できない」能力をすべて無視する（召喚酔いは無視されない）"""
    return u.c.kind == "C" and s.has(i, "e_elborom")


def e_elborom(s, i, u):
    """出た時：自分のタップしているクリーチャー1体につき1枚引く"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and z.tap)
    if n:
        s.draw(i, n)


add("e_elborom", "喜びの夜 エルボロム・ハッピー", 7, "L", power=9500, brk=2, blocker=True,
    races=("demoncommand", "command"), pri=9, roles="blk draw",
    enter=e_elborom, costx=he_costx("e_elborom"), payx=he_payx("e_elborom"), noatkign=ign_elborom,
    text="ハイパーエナジー：召喚する時、コストの異なる自分のクリーチャーを好きな数タップしてよく、"
         "1体につき召喚コストが2少なくなる。ブロッカー、W・ブレイカー。"
         "出た時、自分のタップしているクリーチャー1体につき1枚引く。"
         "自分のクリーチャーが持つ「攻撃できない」能力をすべて無視する",
    source=W + "《喜びの夜 エルボロム・ハッピー》")


# ================================================================ サイバー・Ｎ・ワールド
def e_cybern(s, i, u):
    """出た時：各プレイヤーは手札と墓地を山札に加えてシャッフルし、それぞれ5枚引く"""
    for j in (i, 1 - i):
        p = s.P[j]
        p.deck.extend(p.hand)
        p.deck.extend(p.grave)
        del p.hand[:]
        del p.grave[:]
        s.rng.shuffle(p.deck)
    s.ev("　サイバー・N・ワールド：互いに手札と墓地を山札に加えてシャッフルし、5枚引く")
    for j in (i, 1 - i):
        if s.over:
            return
        s.draw(j, 5)


add("e_cybern", "サイバー・Ｎ・ワールド", 6, "W", power=6000, brk=2, races=("cybercommand", "command"), pri=8,
    roles="draw dis", enter=e_cybern,
    text="W・ブレイカー。出た時、各プレイヤーは自分の手札と墓地をすべて山札に加えてシャッフルし、"
         "その後それぞれ5枚引く。殿堂入り（デッキに1枚）",
    source=W + "《サイバー・N・ワールド》")


# ================================================================ 龍脈術 落城の計
def sp_rakujou(s, i):
    t = s.target(i, lambda z: z.c.cost <= 6, "CTX")
    if t is not None:
        move(s, i, t, "hand")


add("e_rakujou", "龍脈術 落城の計", 3, "W", kind="S", trig=True, pri=5, roles="rem trg", spell=sp_rakujou,
    text="S・トリガー。バトルゾーンにあるコスト6以下のカードを1枚選び、持ち主の手札に戻す",
    source=W + "《龍脈術 落城の計》")
