"""担当23：DM26-RP1（逆札篇 第1弾 逆転神VS切札竜）の未実装カード15枚

出典：dmwiki.net の各カードの個別ページ。1枚につき別の質問で2回ずつ読み、
      コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が2回とも一致することを確かめた。
      あやしかった3枚（英王のM スターマン／獣王のB ペガサス／プラスワン・スパーク）は、さらに
      PukiWiki の template プラグイン（`?plugin=template&refer=《カード名》`）で生の wiki ソースの
      cardtable の行を読んで、種族・パワー・コスト・S・トリガーの有無を裏取りした。
      《魂王のE ソウル・フェニックス》と《非神のN キキ》は下調べの段階で個別ページを読んでいなかったので、
      個別ページを2回＋ソウル・フェニックスは生ソースも読んで確かめた（どちらも食い違いなし）。

  この15枚に入っている仕組み
    ・「五大王」のリメイクサイクル5枚（スターマン／ペガサス／ナーガ／デス・フェニックス／ソウル・フェニックス）。
      全部が「攻撃する時または離れた時」の同じ誘発を持つ、ふつうの進化クリーチャー。
    ・シールド・プラス（自分のシールド1つの下に、山札の上から1枚を裏向きで置く）
    ・シールド・セイバー（自分のシールドがブレイクされる時、かわりにこのクリーチャーを破壊する）
    ・G城の「表向きで自分のシールドゾーンに置かれた時」の誘発（我竜塔第五層 海底鬼面城）
    ・Zラッシュ＋ハイパーモードの札3枚（ガナストラ／キキ／ボルメテウス・ザンジ）
    ・「このクリーチャーがタップした時」の誘発（非神のN キキ）
    ・表向きのシールドがあるとコストが3下がる呪文（ガルド・ブレイン）

  注意：《我竜塔第五層 海底鬼面城》は、殿堂入りの城《海底鬼面城》とは別のカード（こちらはG城で、
        置かれた時に相手のクリーチャーを2体まで手札に戻す。常在能力は持たない）。

  誘発はすべてエンジンの差し込み口で受けている（タップした時＝tapwatch、G城が置かれた時＝castle、
  シールドがブレイクされる直前＝breakpre、シールドが離れた時＝shieldout）。見回り（ポーリング）は使っていない。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, free_play, move
from envcards.env0 import discard_choice, own_loss

W = "https://dmwiki.net/"
SRC = {
    "k23_starman": W + "《英王のM スターマン》",
    "k23_pegasus": W + "《獣王のB ペガサス》",
    "k23_naga": W + "《蛇王のL ナーガ》",
    "k23_deathphoenix": W + "《死王のK デス・フェニックス》",
    "k23_soulphoenix": W + "《魂王のE ソウル・フェニックス》",
    "k23_mirzamkid": W + "《幸せの精霊ミルザム・キッド》",
    "k23_ganastra": W + "《一神のI ガナストラ》",
    "k23_plusspark": W + "《プラスワン・スパーク》",
    "k23_advent": W + "《アドベント・チャージャー》",
    "k23_kiki": W + "《非神のN キキ》",
    "k23_hyoryu": W + "《漂流大陸の進撃》",
    "k23_galdbrain": W + "《ガルド・ブレイン》",
    "k23_kimenjo": W + "《我竜塔第五層 海底鬼面城》",
    "k23_zanji": W + "《腐食の炎 ボルメテウス・ザンジ》",
    "k23_jegal": W + "《解体人形ジェガル》",
}


# ================================================================ 共通の小道具
def _opp_cre(s, i):
    """相手のクリーチャー全部（「すべて」の効果用。選ぶのではないのでジャストダイバーも含む）"""
    return [z for z in s.P[1 - i].board if z.c.kind == "C"]


def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので出せない）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _both(fn):
    """「攻撃する時または離れた時」：attack= と left= の両方に同じ処理を渡すための組を作る"""
    return fn, (lambda s, i, u, dest: fn(s, i, u))


def _evo_rule(civ, name):
    """進化元になれるクリーチャーがデッキに4体いるか（playrule）"""
    def f(deck, k):
        n = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and (set(civ) & set(BY_KEY[kk].civ)))
        if n < 4:
            return f"進化元（{name}のクリーチャー）が4体いない"
        return None
    return f


# ================================================================ 英王のM スターマン
def a_starman(s, i, u):
    """攻撃する時または離れた時、1枚引き、その後、手札を1枚シールド化してもよい

    どの札をシールドにするかは全デッキ共通の決まり：手札のうちいちばん重要度の低い1枚。
    裏向きで置く（表向きにすると、そのシールドのS・トリガーが使えなくなるだけで得がない）。
    手札が1枚しかない時は置かない。"""
    s.draw(i, 1)
    p = s.P[i]
    if len(p.hand) < 2 or s.over:
        return
    k = min(p.hand, key=E.PRI.get)
    p.hand.remove(k)
    if not s.add_shield(i, k, False):
        p.hand.append(k)
        return
    s.ev(f"　スターマン：手札の {BY_KEY[k].name} を裏向きのシールドにした")


_f, _l = _both(a_starman)
add("k23_starman", "英王のM スターマン", 4, "LW", power=8000, brk=2, evo="LW",
    races=("starnoid",), pri=6, roles="draw shd atk",
    attack=_f, left=_l, playrule=_evo_rule("LW", "光か水"),
    text="進化：光または水のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが攻撃する時または離れた時、1枚引く。その後、自分の手札を1枚、"
         "表向きまたは裏向きでシールド化してもよい"
         "（手札のうち重要度のいちばん低い1枚を裏向きで置く。手札が1枚だけの時は置かない）",
    source=SRC["k23_starman"])


# ================================================================ 獣王のB ペガサス
def a_pegasus(s, i, u):
    """攻撃する時または離れた時、山札の上から1枚を表向きにする。
    コスト3以下のクリーチャーなら出してもよい。出さなければ山札の下に置く"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    c = BY_KEY[k]
    s.ev(f"　ペガサス：山札の上の {c.name} を表向きにした")
    if c.cost <= 3 and _playable_cre(c) and s.fate(i, k, "deck", False) == "ok":
        s.enter(i, k, "deck", False)
        return
    p.deck.insert(0, k)


_f, _l = _both(a_pegasus)
add("k23_pegasus", "獣王のB ペガサス", 3, "LN", power=8500, brk=2, evo="LN",
    races=("saintpegasus",), pri=6, roles="acc atk",
    attack=_f, left=_l, playrule=_evo_rule("LN", "光か自然"),
    text="進化：光または自然のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが攻撃する時または離れた時、自分の山札の上から1枚を表向きにする。"
         "それがコスト3以下のクリーチャーなら出してもよい。出さなければ、そのカードを山札の下に置く"
         "（出せるクリーチャーなら必ず出す）",
    source=SRC["k23_pegasus"])


# ================================================================ 蛇王のL ナーガ
def a_naga(s, i, u):
    """攻撃する時または離れた時、相手のクリーチャー1体を選ぶ。相手はそれを破壊するか山札の上に置く

    選ぶのはこのクリーチャーの持ち主（重要度のいちばん高い相手のクリーチャー）。
    行き先を決めるのは相手なので、カードを手元に残せる「山札の上」を選ぶ（全デッキ共通の決まり）。"""
    o = s.P[1 - i]
    t = s.target(i)
    if t is None:
        return
    k = t.k
    n0 = len(o.deck)
    if not s.leave(1 - i, t, "deck", by_opp=True):
        return
    if len(o.deck) > n0 and o.deck[0] == k:
        o.deck.pop(0)                        # エンジンの「山札へ」は山札の下なので、上に入れ直す
        o.deck.append(k)
    s.ev(f"　ナーガ：相手は {BY_KEY[k].name} を山札の上に置いた")


_f, _l = _both(a_naga)
add("k23_naga", "蛇王のL ナーガ", 3, "WD", power=8000, brk=2, evo="WD",
    races=("naga",), pri=6, roles="rem atk",
    attack=_f, left=_l, playrule=_evo_rule("WD", "水か闇"),
    text="進化：水または闇のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが攻撃する時または離れた時、相手のクリーチャーを1体選ぶ。"
         "相手はそのクリーチャーを、破壊するか自身の山札の上に置く"
         "（選ぶのは相手の重要度のいちばん高いクリーチャー。行き先を決めるのは相手なので、"
         "カードを手元に残せる山札の上を選ぶ）",
    source=SRC["k23_naga"])


# ================================================================ 死王のK デス・フェニックス
def a_deathphoenix(s, i, u):
    """攻撃する時または離れた時、各プレイヤーは自身の手札を1枚選んで捨てる。その後、自分は1枚引く"""
    discard_choice(s, i)
    discard_choice(s, 1 - i)
    s.draw(i, 1)


_f, _l = _both(a_deathphoenix)
add("k23_deathphoenix", "死王のK デス・フェニックス", 4, "DF", power=9000, brk=2, evo="DF",
    races=("phoenix",), pri=7, roles="dis draw atk",
    attack=_f, left=_l, playrule=_evo_rule("DF", "闇か火"),
    text="進化：闇または火のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが攻撃する時または離れた時、各プレイヤーは自身の手札を1枚選び、捨てる。"
         "その後、自分はカードを1枚引く"
         "（どちらのプレイヤーも、自分の手札のうち重要度のいちばん低い1枚を捨てる）",
    source=SRC["k23_deathphoenix"])


# ================================================================ 魂王のE ソウル・フェニックス
def a_soulphoenix(s, i, u):
    """攻撃する時または離れた時、自分と相手のクリーチャーを1体ずつ選び、その2体をバトルさせる

    組み合わせは全デッキ共通の決まりで決める：「相手から取り除ける値打ち − 自分が失う痛さ」が
    いちばん大きい組を選ぶ（スター進化の退化の補正は own_loss / s.val に入っている）。"""
    mine = [z for z in s.P[i].board if z.c.kind == "C"]
    opp = [z for z in s.P[1 - i].board if z.c.kind == "C" and not z.jd]
    if not mine or not opp:
        return
    best, bv = None, None
    for a in mine:
        ap = s.power(i, a, True)
        for d in opp:
            dp = s.power(1 - i, d)
            v = (s.val(d) if dp <= ap else 0) - (own_loss(s, i, a) if ap <= dp else 0)
            if bv is None or v > bv:
                best, bv = (a, d), v
    a, d = best
    s.ev(f"　ソウル・フェニックス：{a.c.name} と {d.c.name} をバトルさせる")
    s.battle(i, a, 1 - i, d)


_f, _l = _both(a_soulphoenix)
add("k23_soulphoenix", "魂王のE ソウル・フェニックス", 5, "FN", power=13000, brk=3, evo="FN",
    races=("phoenix",), pri=9, roles="rem atk fin",
    attack=_f, left=_l, playrule=_evo_rule("FN", "火か自然"),
    status="partial",
    note="エンジンのバトルの処理は、1体目を「攻撃している側」として扱う（攻撃中だけ強くなるカードが"
         "少し強く計算される）。効果によるバトルと攻撃によるバトルを区別する仕組みがないため",
    text="進化：火または自然のクリーチャー1体の上に置く。T・ブレイカー。"
         "このクリーチャーが攻撃する時または離れた時、自分と相手のクリーチャーを1体ずつ選ぶ。"
         "その2体をバトルさせる"
         "（「相手から取り除ける値打ち − 自分が失う痛さ」がいちばん大きい組み合わせを選ぶ）",
    source=SRC["k23_soulphoenix"])


# ================================================================ 幸せの精霊ミルザム・キッド
def e_mirzamkid(s, i, u):
    """シールド・プラス：出た時、山札の上から1枚を裏向きで自分のシールド1つの下に置いてもよい"""
    p = s.P[i]
    if not p.sh or len(p.deck) <= 1:
        return
    k = p.deck.pop()
    p.x["k23_splus"] = (p.x.get("k23_splus") or ()) + (k,)      # clone が浅い写しなので tuple で入れ替える
    s.ev(f"　シールド・プラス：山札の上から1枚を自分のシールドの下に置いた（束の下は{len(p.x['k23_splus'])}枚）")


def _splus_take(s, j, n=1):
    """束の下に置いたカードを n 枚取り出す（p.x は clone が浅い写しなので tuple で入れ替える）"""
    p = s.P[j]
    ex = p.x.get("k23_splus") or ()
    n = min(n, len(ex))
    if n <= 0:
        return ()
    take, p.x["k23_splus"] = ex[:n], ex[n:]
    return take


def bw_splus(s, ai, di, n):
    """シールドがブレイクされた時：束の下のカードも同じ数だけ手札に加え、そのS・トリガーも使える"""
    take = _splus_take(s, di, n)
    if not take:
        return
    for k in take:
        s.P[di].hand.append(k)
        s.ev(f"　シールド・プラス：束の下の {BY_KEY[k].name} も手札に加わった")
    for k in take:
        if s.over or s.stop:
            break
        if k in s.P[di].hand:
            s.trigger(di, k)


def so_splus(s, j, k, up, dest):
    """ブレイク以外の理由でシールドが離れた時：束の下のカードも同じ行き先へ付いていく

    （ブレイクの時は dest が "break" で来る。手札に加わった分のS・トリガーは、
      シールドの取り除きが全部終わったあとの breakwatch でまとめて処理する）"""
    if dest == "break" or not (s.P[j].x.get("k23_splus") or ()):
        return
    for x in _splus_take(s, j, 1):
        s.put_zone(j, x, dest)
        s.ev(f"　シールド・プラス：束の下の {BY_KEY[x].name} も {dest} へ付いていった")


add("k23_mirzamkid", "幸せの精霊ミルザム・キッド", 3, "L", power=4000,
    races=("angelcommand", "command"), pri=3, roles="shd draw",
    enter=e_mirzamkid, breakwatch=bw_splus, shieldout=so_splus, status="partial",
    note="このシミュレーターのシールドゾーンは1枚ずつの並びで、「シールドの束」がない"
         "（シールド1つに何枚重なっているかを持てない）。そこで、下に置いたカードはプレイヤーごとに"
         "別に覚えておき、どのシールドが束だったかは区別せず、シールドが離れた枚数だけ"
         "束の下のカードも同じ行き先へ送っている（ブレイクなら手札に加えてS・トリガーも使える）。"
         "シールドの数そのものは増えない（ここは実物と同じ）",
    text="シールド・プラス：このクリーチャーが出た時、自分の山札の上から1枚を裏向きで"
         "自分のシールド1つの下に置いてもよい（そのシールドの束は1つと数える）。"
         "束になったシールドがブレイクされると、下のカードも手札に加わり、そのS・トリガーも使える",
    source=SRC["k23_mirzamkid"])


# ================================================================ 一神のI ガナストラ
add("k23_ganastra", "一神のI ガナストラ", 1, "L", power=2000, blocker=True, zrush=True,
    races=("god", "hyperbeast"), pri=2, roles="blk",
    noatkplock=lambda s, i, u: u.k == "k23_ganastra" and not u.hyper,
    text="ブロッカー。ハイパーモード状態でなければ、このクリーチャーは相手プレイヤーを攻撃できない。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する。"
         "ハイパーモード中はパワー6000になり、W・ブレイカーを得て、相手プレイヤーも攻撃できる",
    source=SRC["k23_ganastra"])
E.HYPER_POW["k23_ganastra"] = 4000


# ================================================================ プラスワン・スパーク
def sp_plusspark(s, i):
    """相手のクリーチャーをすべてタップする。その後、1枚引く"""
    n = 0
    for z in _opp_cre(s, i):
        if not z.tap:
            n += 1
        s.tap_cre(1 - i, z)                  # u.tap を直接書くと「タップした時」が誘発しない
    if n:
        s.ev(f"　プラスワン・スパーク：相手のクリーチャー{n}体をタップした")
    s.draw(i, 1)


add("k23_plusspark", "プラスワン・スパーク", 5, "L", kind="S", trig=True, pri=6, roles="trg dis draw",
    spell=sp_plusspark,
    text="S・トリガー。相手のクリーチャーをすべてタップする。その後、カードを1枚引く",
    source=SRC["k23_plusspark"])


# ================================================================ アドベント・チャージャー
def sp_advent(s, i):
    """コスト3以下のクリーチャーでないカード1枚を手札からただで使ってもよい。
    チャージャー：唱えた後、墓地のかわりにマナゾーンに置く"""
    p = s.P[i]
    fuj = s.has(1 - i, "fujin")
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > 3 or p.ban == c.cost:
            continue                         # ツインパクトはクリーチャーのカードなので対象外
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if c.kind == "G" and fuj:
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        s.ev(f"　アドベント・チャージャー：手札の {BY_KEY[best].name} をコストを支払わずに使う")
        free_play(s, i, best)
    s.add_mana(i, "k23_advent")


add("k23_advent", "アドベント・チャージャー", 4, "L", kind="S", nograve=True, pri=4, roles="acc",
    spell=sp_advent,
    text="コスト3以下の、クリーチャーではないカード1枚を、自分の手札からコストを支払わずに実行してもよい"
         "（使えるもののうち重要度のいちばん高い1枚を使う）。"
         "チャージャー：この呪文を唱えた後、墓地に置くかわりにマナゾーンに置く",
    source=SRC["k23_advent"])


# ================================================================ 非神のN キキ
def tw_kiki(s, i, u):
    """このクリーチャーがタップした時、カードを1枚引いてもよい（tapwatch）"""
    if u.k != "k23_kiki":
        return
    if len(s.P[i].deck) > 1 and not s.over:
        s.ev("　キキ：タップしたのでカードを1枚引く")
        s.draw(i, 1)


add("k23_kiki", "非神のN キキ", 2, "W", power=2000, blocker=True, zrush=True,
    races=("god", "hyperbeast"), pri=3, roles="blk draw",
    tapwatch=tw_kiki,
    text="ブロッカー。このクリーチャーがタップした時、カードを1枚引いてもよい"
         "（山札が1枚しかない時は引かない）。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する。"
         "ハイパーモード中はパワー6000になり、W・ブレイカーを得る",
    source=SRC["k23_kiki"])
E.HYPER_POW["k23_kiki"] = 4000


# ================================================================ 漂流大陸の進撃
def sp_hyoryu(s, i):
    """次の自分のターンのはじめまで、自分のクリーチャーはすべて攻撃もブロックもされない"""
    s.P[i].x["k23_hyoryu"] = s.turn + (1 if s.tp == i else 0)
    s.ev("　漂流大陸の進撃：次の自分のターンのはじめまで、自分のクリーチャーは攻撃もブロックもされない")


def _hyoryu_on(s, j):
    return s.P[j].x.get("k23_hyoryu", -1) >= s.turn


add("k23_hyoryu", "漂流大陸の進撃", 5, "W", kind="S", pri=5, roles="dis fin",
    spell=sp_hyoryu,
    atktargetlock=lambda s, i, u, t: _hyoryu_on(s, 1 - i),
    unbok=lambda s, i, u: _hyoryu_on(s, i),
    text="次の自分のターンのはじめまで、自分のクリーチャーはすべて攻撃されず、ブロックもされない"
         "（相手は自分のクリーチャーを攻撃先に選べず、自分のクリーチャーの攻撃はブロックされない。"
         "自分のプレイヤーへの攻撃は止まらない）",
    source=SRC["k23_hyoryu"])


# ================================================================ ガルド・ブレイン
def sc_galdbrain(s, i, k):
    """自分のシールドゾーンに表向きのカードがあれば、唱えるコストを3少なくする"""
    return 1 if any(up for _, up in s.P[i].sh) else 4


add("k23_galdbrain", "ガルド・ブレイン", 4, "W", kind="S", pri=4, roles="draw",
    spell=lambda s, i: s.draw(i, 2), spcost=sc_galdbrain,
    text="自分のシールドゾーンに表向きのカードが1枚でもあれば、この呪文を唱えるコストを3少なくする"
         "（最低1マナ）。カードを2枚引く",
    source=SRC["k23_galdbrain"])


# ================================================================ 我竜塔第五層 海底鬼面城
def ca_kimenjo(s, j, k):
    """このG城が表向きで自分のシールドゾーンに置かれた時、相手のクリーチャーを2体まで手札に戻す"""
    s.ev("　海底鬼面城：表向きで自分のシールドゾーンに置かれた → 相手のクリーチャーを2体まで手札に戻す")
    for _ in range(2):
        if s.over:
            return
        t = s.target(j)
        if t is None:
            break
        move(s, j, t, "hand")


add("k23_kimenjo", "我竜塔第五層 海底鬼面城", 4, "W", kind="G", pri=5, roles="rem shd",
    castle=ca_kimenjo,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地に置く）。"
         "このG城が表向きで自分のシールドゾーンに置かれた時、相手のクリーチャーを2体まで選び、"
         "持ち主の手札に戻す（重要度のいちばん高いクリーチャーから戻す）。"
         "殿堂入りの《海底鬼面城》とは別のカードで、常在能力は持たない",
    source=SRC["k23_kimenjo"])


# ================================================================ 腐食の炎 ボルメテウス・ザンジ
def e_zanji(s, i, u):
    """出た時、相手のクリーチャー1体を選び、このターン、そのクリーチャーのパワーを−4000する"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 4000) or s.target(i)
    if t is None:
        return
    t.pw -= 4000
    s.ev(f"　ボルメテウス・ザンジ：{t.c.name} のパワーをこのターン-4000")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


add("k23_zanji", "腐食の炎 ボルメテウス・ザンジ", 3, "D", power=2000, zrush=True,
    races=("millionflame", "hyperbeast"), pri=4, roles="rem blk",
    enter=e_zanji,
    blockok=lambda s, u: u.k == "k23_zanji" and u.hyper,
    text="このクリーチャーが出た時、相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを"
         "−4000する（パワー0以下のクリーチャーは破壊される。倒せる相手がいればその中で重要度のいちばん"
         "高いものを、いなければ重要度のいちばん高いものを選ぶ）。"
         "Zラッシュ：自分のシールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する。"
         "ハイパーモード中はパワー8000になり、ブロッカーとW・ブレイカーを得る",
    source=SRC["k23_zanji"])
E.HYPER_POW["k23_zanji"] = 6000


# ================================================================ 解体人形ジェガル
def d_jegal(s, i, u):
    """破壊された時、コスト3以上のクリーチャー1体を自分の墓地から手札に戻してもよい"""
    p = s.P[i]
    cands = [k for k in sorted(set(p.grave)) if BY_KEY[k].kind == "C" and BY_KEY[k].cost >= 3]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　ジェガル：墓地の {BY_KEY[k].name} を手札に戻した")


def bp_jegal(s, ai, di, n):
    """シールド・セイバー：ブレイクされる枚数を、ジェガルを破壊したぶんだけ減らす（breakpre）

    身代わりにするかどうかは全デッキ共通の決まり：このままだとシールドが1つも残らない時だけ守る。
    「割れた後に戻す」のではなく「割られる枚数を減らす」ので、シールドが離れたことによる誘発
    （Zラッシュなど）も、このターンにブレイクされた枚数の数えも、守ったぶんは起こらない。"""
    if n <= 0:
        return n
    d = s.P[di]
    while n > 0 and len(d.sh) - n <= 0:
        z = next((x for x in d.board if x.k == "k23_jegal" and x.c.kind == "C"), None)
        if z is None:
            break
        if not s.leave(di, z, "grave", destroy=True):
            break
        s.ev("　シールド・セイバー：ジェガルを破壊して、シールドのブレイクを1つ防いだ")
        n -= 1
        if s.over:
            break
    return n


add("k23_jegal", "解体人形ジェガル", 2, "D", power=2000,
    races=("puppet",), pri=3, roles="shd draw",
    destroyed=d_jegal, breakpre=bp_jegal,
    text="シールド・セイバー：自分のシールドがブレイクされる時、かわりにこのクリーチャーを破壊してもよい"
         "（このまま割られるとシールドが1つも残らない時に身代わりにする）。"
         "このクリーチャーが破壊された時、コスト3以上のクリーチャー1体を自分の墓地から手札に戻してもよい"
         "（墓地のうち重要度のいちばん高いものを戻す）",
    source=SRC["k23_jegal"])
