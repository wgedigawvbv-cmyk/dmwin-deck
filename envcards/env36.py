"""担当36：DM26-EX1「ますますつよいパック 25の援軍」の未実装カード15枚（N2〜N16）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ（数字が1回しか読めなかった3枚は3回）読み、コスト・文明・種類・種族・
      パワー・ブレイク数・能力本文が一致することを確かめた。

  この札束に入っている仕組み
    ・**ドラゴン・ワールド・ブレイカー**（星龍ゴージャス・アース）。相手のシールドをすべてブレイクし、
      **各ブレイクの前に自分の山札の上から1枚をシールド化する**。`breakpre=` で書いた
      （`s.atk` がこのクリーチャー自身かを見てから効かせる）。
    ・**ゴージャス・シンパシー**（同）。自分のドラゴン・クリーチャー1体につきコスト-5、下限5。
    ・**侍流ジェネレート＋好きな数のクロス**（バザガベルグ・閃光・ドラゴン）。
      クロスギアが4つ以上クロスされていれば離れない（`leaverep=`）。
    ・**ラスト・バースト**（大地無双 カイザー「勝」）＝破壊された時に呪文側をただで唱える。
      **スマッシュ・バースト**（邪幽 ジャヴェール）＝攻撃する時に呪文側を場に置いたまま唱える。
    ・**ハンター・メクレイド10**（勝利の大地）。
    ・**アビスラッシュ**（邪幽 ジャヴェール）。墓地からコストを払って召喚し、そのターン攻撃でき、
      ターンの終わりに山札の下へ（`freeacts=`／`actapply=`、`u.sa` と `u.eot`）。
    ・**チャージャー**（ガチャンコ・チャージャー）＝`nograve=True` ＋ 呪文の最後で `s.add_mana`。
    ・**ヨビニオン**（ヨビニオン・コオニ）。
    ・**バラバラエティ3**（五輪の従者 呼勇気）＝コストが互いに違う自分のエレメントが3つ以上あれば能力を得る。
    ・**鬼エンド**（鬼ヶ魔槍 ジャオウガ）。クリーチャーが攻撃する時、シールドが0のプレイヤーがいれば
      手札からただで召喚。自分の攻撃でも相手の攻撃でも誘発するので `atkwatch=` で両方を見ている。
    ・**Zラッシュ＋ハイパーモード**（“絶闘乱襲”ブランド）。出たターンだけマナゾーンから召喚できる。
    ・**EXライフ＋「タップした時」**（邪闘魔縛 ウェロマノフ＝ルキウス B）。
      EXライフのシールドを失った時の分は `envcards.env0.EXLOST` に登録した。
    ・**S級侵略［超轟速］**（禁断の超轟速 バイオレットゾーン）。手札・墓地・バトルゾーンから重ねられる。
    ・**シンカライズ＋全体破壊**（「正義の記念碑」。《アポカリプス・デイ》のリメイク）。
    ・**自分のエレメントは離れない＋すべてのエレメントを破壊**（インビンシブル・アポカリプス）。

  調べ直して意外だった点
    ・《大地無双 カイザー「勝」》はコスト4・パワー4000の**ブロッカー**で、呪文側《勝利の大地》が
      コスト8のS・トリガー（ハンター・メクレイド10）。クリーチャー側のほうがずっと軽い。
    ・《龍素記号Si サインサイクリカ》は**両面の文明が違う**（クリーチャー側が光/闇、呪文側が光/水）。
      2回とも同じだったので誤記ではない（ページの色分類も「白青黒」になっている）。
    ・《“絶闘乱襲”ブランド》の**スピードアタッカーと「攻撃する時、手札がなければ1枚引く」は
      ハイパーモード中だけ**（生の wiki ソースの `BGCOLOR(#cde):|c|` の位置で確かめた）。
      素のパワーは3000、ハイパーモードで5000。
    ・《愛羅特攻の忠剣ハチ公》の身代わりは「自分の**他の**クリーチャー」で、
      ハチ公自身は破壊できない（ページの裁定欄にそう書いてある）。1枚につき各ターン1度。
    ・《インビンシブル・アポカリプス》はコスト13のS・トリガーではなく**G・ストライク**持ちの呪文。
      「自分のエレメントは離れない」を先に適用するので、実質は一方的な全体破壊になる。
    ・《ガチャンコ ガジェロボ》の攻撃・ブロック止めは「そのクリーチャー」ではなく
      **相手のクリーチャー全体**がそのターン攻撃もブロックもできない、と書かれている。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, is_cmd, worst_hand
from envcards.env0 import SLAYER, EXLOST, discard_choice, exlife_enter, exlife_rep, gears_on, owner_of, own_loss

W = "https://dmwiki.net/"
SRC = {
    "k36_bazagaberg": W + "《バザガベルグ・閃光・ドラゴン》",
    "k36_kaizersho": W + "《大地無双 カイザー「勝」／勝利の大地》",
    "k36_javel": W + "《邪幽 ジャヴェール／「ヤベーのを見たいか？」》",
    "k36_gorgeous": W + "《星龍ゴージャス・アース》",
    "k36_gadgerobo": W + "《ガチャンコ ガジェロボ／ガチャンコ・チャージャー》",
    "k36_kooni": W + "《ヨビニオン・コオニ》",
    "k36_hachiko": W + "《愛羅特攻の忠剣ハチ公》",
    "k36_signcyclica": W + "《龍素記号Si サインサイクリカ／ザーディアン・サイン》",
    "k36_koyuki": W + "《五輪の従者 呼勇気／「名誉ある勝利を！」》",
    "k36_invincible": W + "《インビンシブル・アポカリプス》",
    "k36_onigamaso": W + "《鬼ヶ魔槍 ジャオウガ》",
    "k36_brand": W + "《“絶闘乱襲”ブランド》",
    "k36_weromanov": W + "《邪闘魔縛 ウェロマノフ＝ルキウス B》",
    "k36_violetzone": W + "《禁断の超轟速 バイオレットゾーン》",
    "k36_kinenhi": W + "《「正義の記念碑」》",
}


# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _top(s, i, n):
    """山札の上からn枚を取り出す（山札は1枚残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    return [p.deck.pop() for _ in range(n)] if n > 0 else []


def _bottom(s, i, ks):
    for k in ks:
        s.P[i].deck.insert(0, k)


def _mekureido(s, i, n, pred, what):
    """メクレイドX：山札の上3枚から、条件に合うカード1枚をコストを支払わずに使う。残りは山札の下へ"""
    top = _top(s, i, 3)
    best, bv = None, -1
    for k in top:
        c = BY_KEY[k]
        if c.cost <= n and pred(c) and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        s.P[i].hand.append(best)
        s.ev(f"　{what}：{BY_KEY[best].name} をコストを支払わずに使う")
        if not free_play(s, i, best):
            if best in s.P[i].hand:
                s.P[i].hand.remove(best)
            top.append(best)
    _bottom(s, i, top)


def _cast_inplace(s, i, k, cost, fn):
    """ツインパクトの呪文側を、カードをバトルゾーンに置いたままコストを支払わずに唱える（墓地に行かない）"""
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


def _samurai_gen(s, i, u):
    """侍流ジェネレート：出た時、自分の手札のクロスギア1枚をただでジェネレートしてよい"""
    gs = [k for k in sorted(set(s.P[i].hand)) if BY_KEY[k].kind == "X"]
    if not gs:
        return
    k = max(gs, key=E.PRI.get)
    s.ev(f"　侍流ジェネレート：{BY_KEY[k].name}")
    free_play(s, i, k)


def _elements(s, j):
    """プレイヤー j のエレメントの数（バトルゾーンのカード＋表向きのG城）"""
    q = s.P[j]
    return len(q.board) + sum(1 for k, up in q.sh if up and BY_KEY[k].kind == "G")


def _elem_costs(s, j):
    """プレイヤー j のエレメントのコストの集合（バラバラエティの判定用）"""
    q = s.P[j]
    out = {u.c.cost for u in q.board}
    out |= {BY_KEY[k].cost for k, up in q.sh if up and BY_KEY[k].kind == "G"}
    return out


def _burn_castles(s, j):
    """プレイヤー j の表向きのG城をすべて墓地へ（全体破壊でエレメントとして巻き込む）"""
    q = s.P[j]
    for idx in range(len(q.sh) - 1, -1, -1):
        k, up = q.sh[idx]
        if up and BY_KEY[k].kind == "G":
            s.take_shield(j, idx, "grave")


def _minus_power(s, i, t, n, who):
    """相手のクリーチャー t のパワーをこのターン -n する（0以下なら破壊される）"""
    t.pw -= n
    s.ev(f"　{who}：{t.c.name} のパワーをこのターン-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _abyss(c):
    """アビス・カードか（種族名にアビスを含む）"""
    return any("abyss" in r for r in c.races)


def _cmd_rule(civ, n=4):
    """侵略元になるコマンドが n 体いるデッキか（playrule 用）"""
    def f(deck, k):
        m = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and is_cmd(BY_KEY[kk]) and set(civ) & set(BY_KEY[kk].civ))
        return None if m >= n else f"侵略元になる{civ}のコマンドが{n}体いない"
    return f


# ================================================================ バザガベルグ・閃光・ドラゴン
def e_bazagaberg(s, i, u):
    """侍流ジェネレート、その後、自分のクロスギアを好きな数ただでこのクリーチャーにクロスする

    「自分のクリーチャーにクロス」はどのクリーチャーでもよいが、4つ以上クロスされていれば
    このクリーチャーが離れなくなるので、全部このクリーチャー自身に寄せる（機械的な決め方）。"""
    _samurai_gen(s, i, u)
    if u not in s.P[i].board:
        return
    n = 0
    for g in s.P[i].board:
        if g.c.kind == "X" and g.x.get("on") != u.uid:
            g.x["on"] = u.uid
            n += 1
    if n:
        s.ev(f"　バザガベルグ・閃光・ドラゴン：クロスギア{n}つをただで自身にクロス")


def rep_bazagaberg(s, i, u, dest, destroy_):
    """クロスギアが4つ以上クロスされていれば離れない"""
    return u.k == "k36_bazagaberg" and len(gears_on(s, i, u)) >= 4


add("k36_bazagaberg", "バザガベルグ・閃光・ドラゴン", 4, "L", power=6000, brk=2, blocker=True,
    races=("armoreddragon", "dragon", "samurai"), pri=7, roles="blk atk",
    enter=e_bazagaberg, leaverep=rep_bazagaberg,
    text="ブロッカー、W・ブレイカー。"
         "侍流ジェネレート（このクリーチャーが出た時、自分の手札のクロスギア1枚をコストを支払わずに"
         "ジェネレートしてもよい）。"
         "このクリーチャーが出た時、自分のクロスギアを好きな数、コストを支払わずに自分のクリーチャーに"
         "クロスしてもよい（離れなくなる条件を満たすため、すべてこのクリーチャー自身にクロスする）。"
         "このクリーチャーにクロスギアが4つ以上クロスされていれば、このクリーチャーは離れない",
    source=SRC["k36_bazagaberg"])


# ================================================================ 大地無双 カイザー「勝」／勝利の大地
def e_kaizersho(s, i, u):
    """出た時、山札の上から2枚をタップしてマナゾーンに置き、その後マナから1枚を手札に戻す"""
    p = s.P[i]
    s.ramp(i, 2, True)
    if p.mana:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　カイザー「勝」：マナの {BY_KEY[k].name} を手札へ")


def sp_kaizersho(s, i):
    """勝利の大地：ハンター・メクレイド10"""
    _mekureido(s, i, 10, lambda c: "hunter" in c.races, "ハンター・メクレイド10")


def d_kaizersho(s, i, u):
    """ラスト・バースト：破壊された時、呪文側をコストを支払わずに唱えてもよい"""
    p = s.P[i]
    if "k36_kaizersho" in p.grave and s.spell_ok(i, 8):
        p.grave.remove("k36_kaizersho")
        s.ev("　ラスト・バースト：勝利の大地をコストを支払わずに唱える")
        s.cast(i, "k36_kaizersho", True)


add("k36_kaizersho", "大地無双 カイザー「勝」 / 勝利の大地", 4, "WN", power=4000, blocker=True,
    races=("bluecommanddragon", "greencommanddragon", "command", "dragon", "hunter"),
    twin=(8, "N", True), pri=6, roles="acc blk trg",
    enter=e_kaizersho, spell=sp_kaizersho, destroyed=d_kaizersho,
    text="クリーチャー側：ブロッカー。出た時、自分の山札の上から2枚をタップしてマナゾーンに置き、"
         "その後、カードを1枚、自分のマナゾーンから手札に戻す（重要度のいちばん高いカードを戻す）。"
         "ラスト・バースト（このクリーチャーが破壊された時、このカードの呪文側をコストを支払わずに"
         "唱えてもよい）。"
         "呪文側《勝利の大地》（自然8・S・トリガー）：ハンター・メクレイド10"
         "（自分の山札の上から3枚を見て、その中のコスト10以下のハンター1枚をコストを支払わずに使い、"
         "残りを山札の下に置く）",
    source=SRC["k36_kaizersho"])


# ================================================================ 邪幽 ジャヴェール／「ヤベーのを見たいか？」
def sp_javel(s, i):
    """山札の上から1枚をタップしてマナゾーンに置く。マナがすべてアビス・カードなら相手1体を-2000"""
    p = s.P[i]
    s.ramp(i, 1, True)
    if p.mana and all(_abyss(BY_KEY[k]) for k in p.mana):
        t = s.target(i)
        if t is not None:
            _minus_power(s, i, t, 2000, "「ヤベーのを見たいか？」")


def a_javel(s, i, u):
    """スマッシュ・バースト：攻撃する時、呪文側を場に置いたままただで唱えてもよい"""
    if u.k != "k36_javel":
        return
    s.ev("　スマッシュ・バースト：「ヤベーのを見たいか？」をコストを支払わずに唱える")
    _cast_inplace(s, i, "k36_javel", 2, sp_javel)


def lw_javel(s, i, u, dest, destroy_):
    """各ターンに1度、自分のアビスが離れた時、相手は自身の手札を1枚選んで捨てる"""
    if not _abyss(u.c):
        return
    if u.k != "k36_javel" and not s.has(i, "k36_javel"):
        return
    p = s.P[i]
    if p.x.get("k36_javel_t") == s.turn:
        return
    p.x["k36_javel_t"] = s.turn
    s.ev("　邪幽 ジャヴェール：自分のアビスが離れたので相手は手札を1枚捨てる")
    discard_choice(s, 1 - i)


def fa_javel(s, i, av, cv):
    """アビスラッシュ：このクリーチャーを自分の墓地から召喚してもよい"""
    p = s.P[i]
    if "k36_javel" not in p.grave or s.manaexec(i):
        return []
    n = s.ccost(i, "k36_javel", av)
    if n > av or (n > 0 and not cv.issuperset("DN")):
        return []
    if s.fate(i, "k36_javel", "grave", True) != "ok":
        return []
    return [("x:k36abyss", n)]


def ap_javel(s, a):
    i = s.tp
    p = s.P[i]
    if "k36_javel" not in p.grave:
        return
    p.mused += a[1]
    p.grave.remove("k36_javel")
    s.ev(f"アビスラッシュ：邪幽 ジャヴェール（墓地から召喚・{a[1]}マナ）")
    z = s.enter(i, "k36_javel", "grave", True)
    if z is not None:
        z.sa = True        # そのターン攻撃できる
        z.eot = True       # ターンの終わりに山札の下へ


add("k36_javel", "邪幽 ジャヴェール / 「ヤベーのを見たいか？」", 5, "DN", power=8000, brk=2, mach=True,
    races=("abyssdragon", "abyss", "dragon"), twin=(2, "DN", False), pri=8, roles="acc rem dis atk",
    attack=a_javel, spell=sp_javel, leavewatch=lw_javel,
    freeacts=fa_javel, actapply={"x:k36abyss": ap_javel},
    text="クリーチャー側：マッハファイター、W・ブレイカー。"
         "アビスラッシュ（このクリーチャーを自分の墓地から召喚してもよい。そうしたら、このターン、"
         "このクリーチャーは攻撃でき、ターンの終わりに山札の下に置かれる）。"
         "スマッシュ・バースト（このクリーチャーが攻撃する時、このカードの呪文側を、バトルゾーンに"
         "置いたままコストを支払わずに唱えてもよい）。"
         "各ターンに1度、自分のアビスが離れた時、相手は自身の手札を1枚選んで捨てる。"
         "呪文側《「ヤベーのを見たいか？」》（闇/自然2）：自分の山札の上から1枚をタップして"
         "マナゾーンに置く。その後、自分のマナゾーンにあるカードがすべてアビス・カードなら、"
         "相手のクリーチャー1体のパワーをこのターン-2000する",
    source=SRC["k36_javel"])


# ================================================================ 星龍ゴージャス・アース
def cx_gorgeous(s, i, av):
    """ゴージャス・シンパシー：自分のドラゴン・クリーチャー1体につきコスト-5（4以下にならない）"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and "dragon" in z.c.races)
    return max(5, 25 - 5 * n)


def bp_gorgeous(s, ai, di, n):
    """ドラゴン・ワールド・ブレイカー：各ブレイクの前に自分の山札の上から1枚をシールド化する"""
    u = s.atk
    if u is None or u.k != "k36_gorgeous":
        return n
    if not any(z is u for z in s.P[ai].board):
        return n
    m = min(n, len(s.P[di].sh))
    for _ in range(m):
        s.add_shield(ai)
    if m:
        s.ev(f"　ドラゴン・ワールド・ブレイカー：ブレイクの前に自分のシールドを{m}つ増やす")
    return n


SLAYER.add("k36_gorgeous")

add("k36_gorgeous", "星龍ゴージャス・アース", 25, "LWDFN", power=25000, brk=99,
    sa=True, mach=True, jd=True, races=("worlddragon", "dragon"), pri=14, roles="fin atk rem shd",
    costx=cx_gorgeous, breakpre=bp_gorgeous,
    text="ゴージャス・シンパシー：自分のドラゴン・クリーチャー（このクリーチャーの召喚コストを、"
         "自分のドラゴン・クリーチャー1体につき5少なくする。ただしコストは4以下にならない）。"
         "スピードアタッカー、マッハファイター、ジャストダイバー、スレイヤー。"
         "ドラゴン・ワールド・ブレイカー（このクリーチャーは相手のシールドをすべてブレイクする。"
         "各ブレイクの前に、自分の山札の上から1枚をシールド化する）",
    note="ドラゴン・ワールド・ブレイカーの「または表向きにしてから自分のシールド1つの上に置く」"
         "（シールドを重ねる）側は、このシミュレーターにシールドを重ねる仕組みがないので選べない。"
         "もう一方の「山札の上から1枚をシールド化する」を毎回選ぶ形にした",
    status="partial", source=SRC["k36_gorgeous"])


# ================================================================ ガチャンコ ガジェロボ／ガチャンコ・チャージャー
def w_gadgerobo(s, i, u):
    """相手のクリーチャーが出た時、自分のクリーチャーが3体以上あれば、
    そのターン、相手のクリーチャーは攻撃もブロックもできない"""
    if u.c.kind != "C":
        return
    j = owner_of(s, u)
    o = 1 - j
    if not s.has(o, "k36_gadgerobo") or s.ncre(o) < 3:
        return
    if s.P[j].x.get("k36_gadgerobo_t") == s.turn:
        return
    s.P[j].x["k36_gadgerobo_t"] = s.turn
    s.ev("　ガチャンコ ガジェロボ：このターン、相手のクリーチャーは攻撃もブロックもできない")


def al_gadgerobo(s, i, u):
    return s.P[i].x.get("k36_gadgerobo_t") == s.turn


def bl_gadgerobo(s, u):
    return s.P[owner_of(s, u)].x.get("k36_gadgerobo_t") == s.turn


def _gadgerobo_number(s, i):
    """「6以上の数字を1つ選ぶ」：山札に一番多く残っているコスト（6以上）を宣言する。
    表向きにする前に決めなければいけないので、見てから決めるのではなく山札の中身から機械的に選ぶ"""
    cnt = {}
    for k in s.P[i].deck:
        c = BY_KEY[k].cost
        if c >= 6:
            cnt[c] = cnt.get(c, 0) + 1
    if not cnt:
        return 6
    return max(sorted(cnt), key=lambda c: (cnt[c], c))


def sp_gadgerobo(s, i):
    """ガチャンコ・チャージャー：6以上の数字を1つ選び、上から3枚のうち同じコストのカードを手札に加える"""
    p = s.P[i]
    num = _gadgerobo_number(s, i)
    s.ev(f"　ガチャンコ・チャージャー：数字は{num}を選んだ")
    top = _top(s, i, 3)
    best, bv = None, -1
    for k in top:
        if BY_KEY[k].cost == num and E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is not None:
        top.remove(best)
        p.hand.append(best)
        s.ev(f"　ガチャンコ・チャージャー：{BY_KEY[best].name} を手札へ")
    _bottom(s, i, top)
    s.add_mana(i, "k36_gadgerobo")
    s.ev("　チャージャー：ガチャンコ・チャージャーをマナゾーンへ")


add("k36_gadgerobo", "ガチャンコ ガジェロボ / ガチャンコ・チャージャー", 8, "W", power=9000, brk=2, gs=True,
    races=("greatmechaoh", "invader"), twin=(3, "W", False), nograve=True, pri=9, roles="dis acc draw",
    enterwatch=w_gadgerobo, atklock=al_gadgerobo, blocklock=bl_gadgerobo, spell=sp_gadgerobo,
    text="クリーチャー側：G・ストライク、W・ブレイカー。"
         "相手のクリーチャーが出た時、自分のクリーチャーが3体以上あれば、そのターン、"
         "相手のクリーチャーは攻撃もブロックもできない。"
         "呪文側《ガチャンコ・チャージャー》（水3）：6以上の数字を1つ選ぶ。"
         "自分の山札の上から3枚を表向きにし、その中から、その選んだ数字と同じコストのカードを1枚"
         "手札に加え、残りを山札の下に置く。チャージャー（唱えた後、墓地ではなくマナゾーンに置く）。"
         "選ぶ数字は、表向きにする前に決めなければいけないので、自分の山札にいちばん多く残っている"
         "コスト（6以上）を機械的に宣言する",
    source=SRC["k36_gadgerobo"])


# ================================================================ ヨビニオン・コオニ
def e_kooni(s, i, u):
    """ヨビニオン：召喚した時、山札の上からこれよりコストの小さいクリーチャーが出るまで表向きにする"""
    if not u.x.get("summoned"):
        return
    p = s.P[i]
    flipped, got = [], None
    while len(p.deck) > 1:
        k = p.deck.pop()
        c = BY_KEY[k]
        if c.kind == "C" and c.cost < u.c.cost:
            got = k
            break
        flipped.append(k)
    if got is not None:
        if _plain_cre(BY_KEY[got]):
            s.ev(f"　ヨビニオン：{BY_KEY[got].name} を出す")
            s.enter(i, got, "deck", False)
        else:
            flipped.append(got)             # 進化クリーチャーは進化元がなく出せない
    _bottom(s, i, flipped)


def w_kooni(s, i, u):
    """各ターン、自分の2体目のクリーチャーが出た時、自分の山札の上から3枚を墓地に置いてもよい"""
    if u.c.kind != "C" or not s.has(i, "k36_kooni"):
        return
    p = s.P[i]
    if p.ent != 2 or p.x.get("k36_kooni_t") == s.turn or len(p.deck) <= 6:
        return
    p.x["k36_kooni_t"] = s.turn
    s.ev("　ヨビニオン・コオニ：2体目のクリーチャーが出たので山札の上から3枚を墓地へ")
    s.mill(i, 3)


def l_kooni(s, i, u, dest):
    """離れた時、コスト5以上のクリーチャー1体を自分の墓地から手札に戻してもよい"""
    p = s.P[i]
    cands = [k for k in sorted(set(p.grave)) if BY_KEY[k].kind == "C" and BY_KEY[k].cost >= 5]
    if not cands:
        return
    k = max(cands, key=E.PRI.get)
    p.grave.remove(k)
    p.hand.append(k)
    s.ev(f"　ヨビニオン・コオニ：墓地の {BY_KEY[k].name} を手札へ")


add("k36_kooni", "ヨビニオン・コオニ", 4, "D", power=3000, races=("demonio",), pri=5, roles="acc draw",
    enter=e_kooni, enterwatch=w_kooni, left=l_kooni,
    text="ヨビニオン（このクリーチャーを召喚した時、自分の山札の上から1枚ずつ表向きにし、"
         "こうして最初に出た、これよりコストの小さいクリーチャーを出す。残りを山札の下に置く）。"
         "各ターン、自分の2体目のクリーチャーが出た時、自分の山札の上から3枚を墓地に置いてもよい"
         "（山札が7枚以上ある時だけ置く）。"
         "このクリーチャーが離れた時、コスト5以上のクリーチャー1体を自分の墓地から手札に戻してもよい",
    source=SRC["k36_kooni"])


# ================================================================ 愛羅特攻の忠剣ハチ公
def _hunters(s, i):
    return sum(1 for z in s.P[i].board if z.c.kind == "C" and "hunter" in z.c.races)


def a_hachiko(s, i, u):
    """攻撃する時、自分のハンター・クリーチャーが4体以上あれば、自分の他のクリーチャーをすべてアンタップする"""
    if u.k != "k36_hachiko" or _hunters(s, i) < 4:
        return
    n = 0
    for z in s.P[i].board:
        if z is not u and z.c.kind == "C" and z.tap:
            z.tap = False
            n += 1
    if n:
        s.ev(f"　愛羅特攻の忠剣ハチ公：自分の他のクリーチャー{n}体をアンタップ")


def rep_hachiko(s, i, u, dest, destroy_):
    """各ターンに1度、自分のハンターが離れる時、かわりに自分の他のクリーチャー1体を破壊してもよい"""
    if u.c.kind != "C" or "hunter" not in u.c.races:
        return False
    if not s.has(i, "k36_hachiko"):
        return False
    p = s.P[i]
    if p.x.get("k36_hachiko_t") == s.turn or p.x.get("k36_hachiko_in"):
        return False
    cands = [z for z in p.board if z.c.kind == "C" and z is not u and z.k != "k36_hachiko"]
    if not cands:
        return False
    t = min(cands, key=lambda z: own_loss(s, i, z))
    if own_loss(s, i, t) >= own_loss(s, i, u):
        return False                      # 身代わりのほうが高くつくならしない
    p.x["k36_hachiko_t"] = s.turn
    p.x["k36_hachiko_in"] = 1
    try:
        s.ev(f"　愛羅特攻の忠剣ハチ公：{u.c.name} のかわりに {t.c.name} を破壊")
        s.leave(i, t, "grave", destroy=True)
    finally:
        p.x["k36_hachiko_in"] = 0
    return True


add("k36_hachiko", "愛羅特攻の忠剣ハチ公", 9, "F", power=8000, brk=2, sa=True, gs=True,
    races=("flame", "command", "flamemonster", "hunter"), pri=10, roles="atk fin blk",
    attack=a_hachiko, leaverep=rep_hachiko,
    text="G・ストライク、スピードアタッカー、W・ブレイカー。"
         "このクリーチャーが攻撃する時、自分のハンター・クリーチャーが4体以上あれば、"
         "自分の他のクリーチャーをすべてアンタップする。"
         "各ターンに1度、自分のハンター・クリーチャーが離れる時、かわりに自分の他のクリーチャーを"
         "1体破壊してもよい（このクリーチャー自身は身代わりにできない。"
         "失うのがいちばん安いクリーチャーを選び、離れるクリーチャーより安い時だけ身代わりにする）",
    source=SRC["k36_hachiko"])


# ================================================================ 龍素記号Si サインサイクリカ／ザーディアン・サイン
def d_signcyclica(s, i, u):
    """破壊された時、コスト5以下のクリーチャー1体を自分の墓地から出してもよい"""
    s.revive(i, lambda c: c.cost <= 5, "grave")


def sp_signcyclica(s, i):
    """ザーディアン・サイン：コスト7以下の多色コマンド・クリーチャー1体を自分の手札から出す"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if not _plain_cre(c) or c.cost > 7 or not is_cmd(c) or not E.MULTI[k]:
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　ザーディアン・サイン：手札から {BY_KEY[best].name} を出す")
    s.enter(i, best, "hand", False)


SLAYER.add("k36_signcyclica")

add("k36_signcyclica", "龍素記号Si サインサイクリカ / ザーディアン・サイン", 6, "LD", power=6500, brk=2,
    blocker=True, races=("crystalcommanddragon", "command", "dragon"), twin=(5, "LW", True),
    pri=8, roles="blk trg acc rem",
    destroyed=d_signcyclica, spell=sp_signcyclica,
    text="クリーチャー側：ブロッカー、スレイヤー、W・ブレイカー。"
         "このクリーチャーが破壊された時、コスト5以下のクリーチャー1体を自分の墓地から出してもよい。"
         "呪文側《ザーディアン・サイン》（光/水5・S・トリガー）：コスト7以下の多色コマンド・"
         "クリーチャー1体を自分の手札から出す",
    note="クリーチャー側は光/闇、呪文側は光/水と両面で文明が違う（dmwiki を2回読んで確かめた）。"
         "エンジンはツインパクトの呪文側の文明を twin= で持つので、そのまま書けている",
    source=SRC["k36_signcyclica"])


# ================================================================ 五輪の従者 呼勇気／「名誉ある勝利を！」
def sa_koyuki(s, i, u):
    """バラバラエティ3：コストが異なる自分のエレメントが3つ以上あれば、自分のクリーチャーすべてにSA"""
    if u.c.kind != "C" or not s.has(i, "k36_koyuki"):
        return False
    return len(_elem_costs(s, i)) >= 3


def sp_koyuki(s, i):
    """「名誉ある勝利を！」：相手のパワー3000以下（マナにツインパクトがあれば5000以下）を1体破壊する"""
    lim = 5000 if any(BY_KEY[k].twin for k in s.P[i].mana) else 3000
    t = s.target(i, lambda z: s.power(1 - i, z) <= lim)
    if t is None:
        return
    s.ev(f"　「名誉ある勝利を！」：パワー{lim}以下の {t.c.name} を破壊")
    destroy(s, i, t)


add("k36_koyuki", "五輪の従者 呼勇気 / 「名誉ある勝利を！」", 6, "LF", power=8000, brk=2,
    blocker=True, gs=True, races=("dreammate", "samurai"), twin=(1, "F", False),
    pri=8, roles="blk atk rem",
    saok=sa_koyuki, spell=sp_koyuki,
    text="クリーチャー側：G・ストライク、ブロッカー、W・ブレイカー。"
         "バラバラエティ3（コストが異なる自分のエレメントが3つ以上あれば、このクリーチャーに"
         "この能力を与える）：自分のクリーチャーすべてに「スピードアタッカー」を与える。"
         "呪文側《「名誉ある勝利を！」》（火1）：相手のパワー3000以下のクリーチャー1体を破壊する。"
         "自分のマナゾーンにツインパクトカードがあれば、かわりにパワー5000以下のクリーチャー1体を破壊する",
    source=SRC["k36_koyuki"])


# ================================================================ インビンシブル・アポカリプス
def rep_invincible(s, i, u, dest, destroy_):
    """次の自分のターンのはじめまで、自分のエレメントは離れない"""
    return s.P[i].x.get("k36_apo", -1) >= s.turn


def sp_invincible(s, i):
    """自分のエレメントが離れなくなり、その後すべてのエレメントを破壊する"""
    p = s.P[i]
    p.x["k36_apo"] = s.turn + (1 if s.tp == i else 0)
    s.ev("　インビンシブル・アポカリプス：次の自分のターンのはじめまで自分のエレメントは離れない")
    s.ev("　インビンシブル・アポカリプス：すべてのエレメントを破壊する")
    for j in (i, 1 - i):
        q = s.P[j]
        for z in q.board[:]:
            if z in q.board:
                s.leave(j, z, "grave", by_opp=(j != i), destroy=True)
    for j in (i, 1 - i):
        if j == i and p.x.get("k36_apo", -1) >= s.turn:
            continue                        # 自分のG城も「離れない」で守られる
        _burn_castles(s, j)


add("k36_invincible", "インビンシブル・アポカリプス", 13, "LF", kind="S", gs=True, pri=12, roles="rem fin",
    spell=sp_invincible, leaverep=rep_invincible,
    text="G・ストライク（このカードを自分のシールドゾーンから手札に加える時、表向きにし、"
         "相手のクリーチャー1体を選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "次の自分のターンのはじめまで、自分のエレメントは離れない。"
         "すべてのエレメントを破壊する（自分のエレメントは先の能力で守られるので、"
         "実際には相手のエレメントだけが破壊される）",
    source=SRC["k36_invincible"])


# ================================================================ 鬼ヶ魔槍 ジャオウガ
def e_onigamaso(s, i, u):
    """出た時、プレイヤーを1人選ぶ。そのプレイヤーの墓地をシャッフルして山札の下に置き、
    その枚数以下のコストの相手のクリーチャー1体を破壊してもよい"""
    n0, n1 = len(s.P[0].grave), len(s.P[1].grave)
    j = 1 - i if n0 == n1 else (0 if n0 > n1 else 1)   # 墓地の多い方（同数なら相手）を選ぶ
    q = s.P[j]
    cards = q.grave[:]
    del q.grave[:]
    s.rng.shuffle(cards)
    for k in cards:
        q.deck.insert(0, k)
    n = len(cards)
    s.ev(f"　鬼ヶ魔槍 ジャオウガ：{'自分' if j == i else '相手'}の墓地{n}枚を山札の下へ")
    if n <= 0:
        return
    t = s.target(i, lambda z: z.c.cost <= n)
    if t is not None:
        s.ev(f"　鬼ヶ魔槍 ジャオウガ：コスト{n}以下の {t.c.name} を破壊")
        destroy(s, i, t)


def aw_onigamaso(s, i, u):
    """鬼エンド：クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、
    自分のマナゾーンに闇と火文明があれば、このクリーチャーを手札からコストを支払わずに召喚してもよい

    自分の攻撃でも相手の攻撃でも誘発するので、両方のプレイヤーの手札を見る。"""
    if u.c.kind != "C":
        return
    if s.P[0].sh and s.P[1].sh:
        return
    for j in (0, 1):
        p = s.P[j]
        if s.over or "k36_onigamaso" not in p.hand:
            continue
        cv = set("".join(E.MCIV[k] for k in p.mana))
        if not {"D", "F"} <= cv:
            continue
        if s.fate(j, "k36_onigamaso", "hand", True) != "ok":
            continue
        p.hand.remove("k36_onigamaso")
        s.ev("　鬼エンド：鬼ヶ魔槍 ジャオウガをコストを支払わずに召喚")
        s.enter(j, "k36_onigamaso", "hand", True)


SLAYER.add("k36_onigamaso")

add("k36_onigamaso", "鬼ヶ魔槍 ジャオウガ", 6, "DF", power=6000, brk=2, sa=True,
    races=("demonio",), pri=9, roles="atk rem fin dis",
    enter=e_onigamaso, atkwatch=aw_onigamaso,
    text="＜鬼エンド＞：クリーチャーが攻撃する時、シールドが1つもないプレイヤーがいて、"
         "自分のマナゾーンに闇と火文明があれば、このクリーチャーを自分の手札から"
         "コストを支払わずに召喚してもよい。"
         "スピードアタッカー、スレイヤー、W・ブレイカー。"
         "このクリーチャーが出た時、プレイヤーを1人選ぶ。そのプレイヤーは自身の墓地にあるカードの"
         "枚数を数え、シャッフルして山札の下に置く。その後、こうして山札の下に置かれたカードの"
         "枚数以下のコストを持つ相手のクリーチャー1体を破壊してもよい"
         "（墓地の枚数が多いプレイヤーを選ぶ。同数なら相手を選ぶ）",
    source=SRC["k36_onigamaso"])


# ================================================================ “絶闘乱襲”ブランド
def e_brand(s, i, u):
    """出た時、自分の手札を1枚マナゾーンに置いてもよい。出たターンの間、マナから1体召喚できる"""
    p = s.P[i]
    p.x["k36_brand_t"] = s.turn
    k = worst_hand(s, i)
    if k is not None:
        p.hand.remove(k)
        s.add_mana(i, k, src="hand")
        s.ev(f"　“絶闘乱襲”ブランド：手札の {BY_KEY[k].name} をマナゾーンへ")


def a_brand(s, i, u):
    """ハイパーモード中、攻撃する時、自分の手札がなければ1枚引く"""
    if u.k != "k36_brand" or not u.hyper:
        return
    if not s.P[i].hand:
        s.draw(i, 1)


def sa_brand(s, i, u):
    """ハイパーモード中はスピードアタッカー"""
    return u.k == "k36_brand" and u.hyper


def fa_brand(s, i, av, cv):
    """このクリーチャーが出たターンの間、クリーチャー1体を自分のマナゾーンから召喚してもよい"""
    p = s.P[i]
    if p.x.get("k36_brand_t") != s.turn or p.x.get("k36_brand_u") == s.turn or s.manaexec(i):
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if c.kind != "C":
            continue
        if c.evo and not c.neo and s.evo_src(i, k) is None:
            continue
        n = s.ccost(i, k, av)
        if n > av - 1:                      # 召喚するカード自身はコストに使えない
            continue
        rest = list(p.mana)
        rest.remove(k)
        cv2 = set("".join(E.MCIV[x] for x in rest))
        if (n == 0 or cv2.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:k36brand", k, n))
    return out


def ap_brand(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana or p.x.get("k36_brand_t") != s.turn or p.x.get("k36_brand_u") == s.turn:
        return
    c = BY_KEY[k]
    on = s.evo_src(i, k) if c.evo else None
    if c.evo and not c.neo and on is None:
        return
    p.x["k36_brand_u"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"　“絶闘乱襲”ブランド：マナゾーンから {c.name} を召喚（{a[2]}マナ）")
    s.enter(i, k, "mana", True, on=on)


add("k36_brand", "“絶闘乱襲”ブランド", 2, "FN", power=3000, zrush=True,
    races=("beatjockey", "hyperbeast"), pri=6, roles="acc atk draw",
    enter=e_brand, attack=a_brand, saok=sa_brand,
    freeacts=fa_brand, actapply={"x:k36brand": ap_brand},
    text="このクリーチャーが出た時、自分の手札を1枚マナゾーンに置いてもよい"
         "（重要度のいちばん低いカードを置く）。"
         "このクリーチャーが出たターンの間、クリーチャー1体を自分のマナゾーンから召喚してもよい"
         "（コストは支払う。そのカード自身はコストに使えない）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードを解放する）。"
         "ハイパーモード中はパワー5000・スピードアタッカーで、攻撃する時、"
         "自分の手札がなければ1枚引く",
    source=SRC["k36_brand"])
E.HYPER_POW["k36_brand"] = 2000


# ================================================================ 邪闘魔縛 ウェロマノフ＝ルキウス B
def _wero_use(s, i, u):
    """カードを1枚、自分のマナゾーンか墓地から手札に戻してもよい。その後、相手は手札を1枚選んで捨てる"""
    p = s.P[i]
    if p.grave:
        k = max(p.grave, key=E.PRI.get)
        p.grave.remove(k)
        p.hand.append(k)
        s.ev(f"　ウェロマノフ＝ルキウス B：墓地の {BY_KEY[k].name} を手札へ")
    elif p.mana:
        k = max(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　ウェロマノフ＝ルキウス B：マナの {BY_KEY[k].name} を手札へ")
    discard_choice(s, 1 - i)


def tw_weromanov(s, i, u):
    """このクリーチャーがタップした時"""
    if u.k != "k36_weromanov":
        return
    _wero_use(s, i, u)


EXLOST["k36_weromanov"] = _wero_use        # EXライフのシールドが離れた時

add("k36_weromanov", "邪闘魔縛 ウェロマノフ＝ルキウス B", 12, "LDN", power=19500, brk=4, blocker=True,
    races=("dispector", "angelcommand", "command", "dragonzombie", "dragon", "knight"),
    pri=13, roles="fin blk dis draw shd",
    enter=exlife_enter, leaverep=exlife_rep, tapwatch=tw_weromanov,
    text="EXライフ（このクリーチャーを出す時、自分の山札の上から1枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドを墓地に置く）。"
         "ブロッカー、Q・ブレイカー。"
         "このクリーチャーがタップした時、またはこのクリーチャーの「EXライフ」シールドが離れた時、"
         "カードを1枚、自分のマナゾーンまたは墓地から手札に戻してもよい。"
         "その後、相手は自身の手札を1枚選んで捨てる"
         "（墓地があれば墓地の重要度のいちばん高いカードを、無ければマナから取る）",
    source=SRC["k36_weromanov"])


# ================================================================ 禁断の超轟速 バイオレットゾーン
def e_violetzone(s, i, u):
    """出た時、相手の手札を1枚見ないで選び捨てさせる。それが呪文なら、自分が墓地からただで唱えてもよい"""
    o = s.P[1 - i]
    if not o.hand:
        return
    k = o.hand[s.rng.randrange(len(o.hand))]
    s.discard(1 - i, k)
    c = BY_KEY[k]
    cost = c.twin[0] if c.twin else c.cost
    twin = bool(c.twin)
    if c.kind != "S" and not twin:
        return
    if k not in o.grave or not s.spell_ok(i, cost):
        return
    o.grave.remove(k)
    s.ev(f"　バイオレットゾーン：捨てさせた {c.name} を相手の墓地からただで唱える")
    s.cast(i, k, twin)
    p = s.P[i]
    if k in p.grave:                        # 唱えた後は持ち主（相手）の墓地に置く
        p.grave.remove(k)
        o.grave.append(k)


add("k36_violetzone", "禁断の超轟速 バイオレットゾーン", 7, "WDF", power=12000, brk=3, evo="WDF",
    races=("soniccommand", "command", "sinvader"), pri=11, roles="atk fin dis",
    enter=e_violetzone, invade=lambda s, i, u: is_cmd(u.c) and bool(set("WDF") & set(u.c.civ)),
    playrule=_cmd_rule("WDF"),
    text="進化：水、闇または火のクリーチャー1体の上に置く。"
         "S級侵略［超轟速］：水、闇または火のコマンド（自分の水・闇・火のコマンドが攻撃する時、"
         "自分の手札、墓地またはバトルゾーンにあるこのクリーチャーをその上に重ねてもよい）。"
         "T・ブレイカー。"
         "このクリーチャーが出た時、相手の手札を1枚見ないで選び、捨てさせる。それが呪文なら、"
         "自分がその呪文を相手の墓地からコストを支払わずに唱えてもよい",
    note="S級侵略の「超次元ゾーンにあるこのクリーチャーを重ねる」側は、"
         "このシミュレーターに超次元ゾーンが無いので手札・墓地・バトルゾーンだけにした",
    status="partial", source=SRC["k36_violetzone"])
E.INVZONE["k36_violetzone"] = ("hand", "grave", "board")


# ================================================================ 「正義の記念碑」
def e_kinenhi(s, i, u):
    """出た時、エレメントが6つ以上あれば、他の進化ではないエレメントをすべて破壊する"""
    if _elements(s, 0) + _elements(s, 1) < 6:
        return
    s.ev("　「正義の記念碑」：他の進化ではないエレメントをすべて破壊する")
    for j in (i, 1 - i):
        q = s.P[j]
        for z in q.board[:]:
            if z is u or z not in q.board or z.c.evo:
                continue
            s.leave(j, z, "grave", by_opp=(j != i), destroy=True)
    for j in (i, 1 - i):
        _burn_castles(s, j)


E.SHINKA.add("k36_kinenhi")

add("k36_kinenhi", "「正義の記念碑」", 8, "L", kind="T", trig=True,
    races=("metallica", "angelcommand", "command", "rexstars"), pri=10, roles="rem trg fin",
    enter=e_kinenhi,
    text="S・トリガー。"
         "シンカライズ（このタマシードがクリーチャーであるかのように、この上に進化クリーチャーを"
         "置いてもよい）。"
         "このタマシードが出た時、エレメントが6つ以上あれば、他の進化ではないエレメントを"
         "すべて破壊する（《アポカリプス・デイ》のリメイク）",
    source=SRC["k36_kinenhi"])
