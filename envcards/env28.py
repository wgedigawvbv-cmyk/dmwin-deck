"""担当28：DM26-RP2（逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼︎）の未実装カード15枚（45/77〜59/77）

  出典：dmwiki.net のカード個別ページ（`https://dmwiki.net/《カード名》`）と、
        PukiWiki の生ソース（`?plugin=template&refer=《カード名》`）。
        カードごとに**別の質問で2回ずつ**読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
        どちらでも一致することを確かめた。数値が片方しか読めなかった札（パワーや効果の後半が
        「…」で切れていた札）は、その1点だけを聞く3回目の質問で確かめている
        （ピエロ・ニケ・カツえもん逆・ロビー・カツドン・ドレミ・テック・エリカッチュ。・カイザー・ビクトリー）。
        生ソースの cardtable で、15枚いずれも**ハイパーモード欄の区切り（`BGCOLOR(#cde):|c|`）が無い**
        ことも確かめた（＝この15枚にハイパーモードを持つカードは1枚もない）。

  この15枚の骨組み
    ・「アウトレイジ・コマンドMAX／革命軍／ハムカツ団」の多色サイクル（48 ニケ・49 カツえもん逆・
      50 ロビー・52 カツドン）。文明の組み合わせが1枚ずつ違う（光水・光自然・水闇・火自然）。
      既存の《V頂神話 カツムゲン》（env25）と同じ種族の並びで、リメイク元の能力をそのまま持つ札が多い。
    ・コストの条件が無い「革命チェンジ：〈文明〉のクリーチャー」のコモン・サイクル
      （53 タイム槍 ドレミ＝光／59 【問銃】テック＝水）。
    ・「鎧亜寄生パラス・◯◯」のスペース・チャージ（45 ピエロ＝SC-水）。
      この版のエンジンには `manain=`（自分のマナゾーンにカードが置かれた時）があるので、
      env26／env27 の見回りではなく**差し込み口でそのまま**書いた。
    ・「極◯秘伝◯◯」（47 極勝秘伝カイザー・ビクトリー）。コスト3の呪文＋アタック・チャンス＋リサイクル。
      env27 が同じサイクルを4枚実装しているが、**数値は流用せず1枚ずつ読み直した**
      （アタック・チャンスの文明＝自然、リサイクルも[自然(4)]、効果はマナ加速＋マナ回収）。
    ・「ラクシャ」のシールド・ゴー（55 神判のラクシャ コットン）。
    ・「熱血の親衛隊」5枚サイクルの1枚（56 ラプソディ）。残りは別の担当。

  調べ直して意外だった点
    ・《D2-W革命のボルトロン》（51/77）は**名前に「D2-W」が付くがD2フィールドではなく、ふつうのクリーチャー**
      だった（ソニック・コマンド／イニシャルズW、パワー10000、W・ブレイカー）。
      タマシードにはせず、封印を自分のクリーチャーに置くデメリット持ちの素のクリーチャーとして実装した。
      生ソースの cardtable でも「種類：クリーチャー」で、Dスイッチも「他のD2フィールドが出た時」も無い。
    ・《熱血の羅刹 メフィス・トリック》は「羅刹」「デーモン・コマンド」なのに**光文明**（闇ではない）。
    ・《雪精 エリカッチュ。》の種族は「スノーフェアリー」ではなく**「スノーフェアリー風」**
      （env26 の《獣音類武士目 グローバル・ステージ》と同じ `snowfu`）。コスト2でパワー8000だが攻撃できない。
    ・「革命チェンジ：〈文明〉のクリーチャー」のコモン2枚には**コストの条件がまったく無い**
      （「コスト5以上の」等が付かない）。サイクルだと思って既存の札から数値を流用すると間違う。
    ・《宇宙 バリアスキー》は種族に「S級侵略者」を持つが、**侵略の能力そのものは持たない**
      （dmwiki も「史上初の非進化のS級侵略者」と書いている）。だから `invade=` は付けていない。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, move
from envcards.env0 import lock_until_my_turn, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k28_pierro": W + "《鎧亜寄生パラス・ピエロ》",
    "k28_erikacchu": W + "《雪精 エリカッチュ。》",
    "k28_kaiser": W + "《極勝秘伝カイザー・ビクトリー》",
    "k28_nike": W + "《熱血刃 ニケ》",
    "k28_katsuemon": W + "《刀の3号 カツえもん逆》",
    "k28_robby": W + "《超熱血 ロビー》",
    "k28_boltron": W + "《D2-W革命のボルトロン》",
    "k28_katsudon": W + "《V闘龍 カツドン》",
    "k28_doremi": W + "《タイム槍 ドレミ》",
    "k28_mephis": W + "《熱血の羅刹 メフィス・トリック》",
    "k28_cotton": W + "《神判のラクシャ コットン》",
    "k28_rhapsody": W + "《熱血の親衛隊ラプソディ》",
    "k28_banana": W + "《ホーリー・出す・バナナ》",
    "k28_barrier": W + "《宇宙 バリアスキー》",
    "k28_tech": W + "《【問銃】テック》",
}

CIVNAME = {"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}


# ================================================================ 共通の道具
def _powered_brk(s, i, u):
    """パワード・ブレイカー：パワー6000ごとにシールドをもう1つブレイクする"""
    return 1 + s.power(i, u, True) // 6000


def _freeze_one(s, i, label):
    """相手のクリーチャー1体をタップし、次の自分のターンのはじめまでアンタップしないようにする"""
    t = s.target(i)
    if t is None:
        return
    s.tap_cre(1 - i, t)
    t.frz = 1
    s.ev(f"　{label}：{t.c.name} をタップして起こさない")


def _bounce_one(s, i, label):
    """相手のクリーチャー1体を持ち主の手札に戻す"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　{label}：{t.c.name} を持ち主の手札に戻す")
    move(s, i, t, "hand")


def _take_best_mana(s, i, label, floor=5):
    """自分のマナゾーンからいちばん大事なカード1枚を手札に戻す（floor 未満の値打ちしか無ければ戻さない）。
    戻したら True。任意効果の時だけ floor を使う（必ず戻す効果は floor=0 で呼ぶ）"""
    p = s.P[i]
    if not p.mana:
        return False
    k = max(p.mana, key=E.PRI.get)
    if E.PRI[k] < floor:
        return False
    s.take_mana(i, k)
    p.hand.append(k)
    s.ev(f"　{label}：マナゾーンから {BY_KEY[k].name} を手札へ")
    return True


def _cast_free(s, i, k, dest="grave"):
    """呪文をコストを支払わずに唱える（カードは呼ぶ側がゾーンから取り除いておく）。
    唱えた後の行き先は dest（"grave"＝墓地／"deck"＝山札の下）"""
    p = s.P[i]
    c = BY_KEY[k]
    p.spl += 1
    s.first_play(i, c.cost)
    prev = s.spc
    s.spc = c.cost
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, k)
    fn = E.SPELL.get(k)
    if fn is not None and not s.over:
        fn(s, i)
    s.spc = prev
    if dest == "deck":
        p.deck.insert(0, k)
    else:
        s.grave_put(i, k)
    s.noncre(i)


# ---------------------------------------------------------------- アタック・チャンス
def ac_watch(key, civ, useful):
    """アタック・チャンス：自分の〈civ〉のパワー4000以上のクリーチャーが攻撃する時、
    手札のこの呪文をコストを支払わずに唱えてもよい（効き目がある時だけ使う。手札の複数枚にも働く）"""
    def f(s, i, u):
        p = s.P[i]
        if key not in p.hand:                     # 自分のカードが手札に無い対戦では何もしない
            return
        if u.c.kind != "C" or civ not in u.c.civ:
            return
        if s.power(i, u, True) < 4000:
            return
        c = BY_KEY[key]
        for _ in range(4):
            if s.over or s.stop or key not in p.hand:
                return
            if not s.spell_ok(i, c.cost) or not useful(s, i):
                return
            p.hand.remove(key)
            s.ev(f"　アタック・チャンス：{c.name} をコストを支払わずに唱える")
            _cast_free(s, i, key, "grave")
    return f


# ---------------------------------------------------------------- リサイクル
def rc_acts(key, civ, cost=4):
    """リサイクル[civ(cost)]：自分の墓地からこの呪文を唱える手を追加する"""
    name = "x:" + key

    def f(s, i, av, cv):
        p = s.P[i]
        if key not in p.grave or av < cost or civ not in cv:
            return []
        if s.manaexec(i) or not s.spell_ok(i, BY_KEY[key].cost):
            return []
        return [(name,)]
    return f


def rc_apply(key, civ, cost=4):
    def f(s, a):
        i = s.tp
        p = s.P[i]
        if key not in p.grave or len(p.mana) - p.mused < cost:
            return
        p.mused += cost
        p.grave.remove(key)
        s.ev(f"リサイクル：{BY_KEY[key].name}（{CIVNAME[civ]}{cost}マナ／唱えた後は山札の下）")
        _cast_free(s, i, key, "deck")
    return f


def _hiden_text(civ, body):
    """「極◯秘伝◯◯」の共通の説明文"""
    c = CIVNAME[civ]
    return (f"アタック・チャンス：{c}のパワー4000以上のクリーチャー"
            f"（自分の{c}のパワー4000以上のクリーチャーが攻撃する時、"
            "このカードを手札からコストを支払わずに唱えてもよい）。"
            + body +
            f"リサイクル[{c}(4)]（この呪文は自分の墓地から{c}を含む4マナを支払って唱えてもよい。"
            "そうして唱えた後は、墓地のかわりに山札の下に置く）")


# ---------------------------------------------------------------- 革命チェンジ（コストの条件が無い版）
def pr_change(civ, n=3):
    """革命チェンジの「出せるデッキか」：元になれるクリーチャー（攻撃できる〈civ〉のクリーチャー）が n 体以上いるか"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and not BY_KEY[kk].noatk
                and civ in BY_KEY[kk].civ)
        return None if c >= n else f"革命チェンジの元になる{CIVNAME[civ]}のクリーチャーが{n}体いない"
    return f


def cx_change(civ):
    """革命チェンジ：〈civ〉のクリーチャー（コストやパワーの条件は無い）"""
    def f(s, i, u):
        return u.c.kind == "C" and civ in u.c.civ
    return f


def _change_text(civ):
    c = CIVNAME[civ]
    return (f"革命チェンジ：{c}のクリーチャー"
            f"（自分の{c}のクリーチャーが攻撃する時、そのクリーチャーと手札にあるこのクリーチャーを"
            "入れ替えてもよい。コストやパワーの条件は無い）。")


# ================================================================ 45/77 鎧亜寄生パラス・ピエロ
def a_pierro(s, i, u):
    """攻撃する時、自分の山札の上から1枚をマナゾーンに置いてもよい"""
    if len(s.P[i].deck) <= 1:
        return
    s.ramp(i, 1, tapped=False)


def mi_pierro(s, i, k, src):
    """スペース・チャージ SC-水：自分のマナゾーンに水のカードが置かれた時、カードを1枚引く
    （ピエロが場にいる数だけ誘発する。山札が切れる時は使わない）"""
    if "W" not in E.MCIV.get(k, ""):
        return
    p = s.P[i]
    n = sum(1 for z in p.board if z.k == "k28_pierro" and z.c.kind == "C")
    for _ in range(n):
        if s.over or len(p.deck) <= 1:
            return
        s.ev("　SC-水：鎧亜寄生パラス・ピエロでカードを1枚引く")
        s.draw(i, 1)


add("k28_pierro", "鎧亜寄生パラス・ピエロ", 3, "N", power=3000,
    races=("lostcrusader", "alien"), pri=4, roles="acc draw",
    attack=a_pierro, manain=mi_pierro,
    text="このクリーチャーが攻撃する時、自分の山札の上から1枚をマナゾーンに置いてもよい。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、そのカードの文明に合うSC能力を使ってもよい）。"
         "SC-水：カードを1枚引く",
    source=SRC["k28_pierro"])


# ================================================================ 46/77 雪精 エリカッチュ。
def w_erikacchu(s, i, u):
    """相手のクリーチャーが手札以外から出た時、このクリーチャーとそのクリーチャーをバトルさせてもよい
    （使うかどうかは全デッキ共通の決まり：相手を倒せる時だけ仕掛け、相打ちになるなら
    失うのより相手の方が大事な時だけ仕掛ける）"""
    if u.c.kind != "C" or u.x.get("src", "hand") == "hand":
        return
    j = 1 - i
    for z in list(s.P[j].board):
        if z.k != "k28_erikacchu" or z.c.kind != "C":
            continue
        if z not in s.P[j].board or u not in s.P[i].board or s.over:
            continue
        ap, dp = s.power(j, z, True), s.power(i, u)
        if ap < dp:
            continue                             # 相手を倒せないのに自分だけ失う
        if ap == dp and s.val(u) < s.val(z):
            continue                             # 相打ちになるが、失う方が大事
        s.ev(f"　雪精 エリカッチュ。：手札以外から出た {u.c.name} とバトルする")
        s.battle(j, z, i, u)
        return


def bs_erikacchu(s, di, du, ai, au):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこれをタップしてバトルさせる

    引き受けるかどうかは全デッキ共通の決まり：バトルに勝てるか、守る相手のほうが大事な時だけ。
    攻撃先は変えないので、攻撃されたクリーチャーのほうは本物どおりそのまま残る。"""
    if du.k == "k28_erikacchu":
        return None
    ap = s.power(ai, au, True)
    for z in s.P[di].board:
        if z.k != "k28_erikacchu" or z.c.kind != "C" or z.tap or z is du:
            continue
        if s.power(di, z) > ap or s.val(du) > s.val(z):
            s.tap_cre(di, z)
            return z
    return None


E.GUARDMEN.add("k28_erikacchu")              # 「ガードマンを持つクリーチャー」の判定に入れる


add("k28_erikacchu", "雪精 エリカッチュ。", 2, "N", power=8000, noatk=True,
    races=("snowfu",), pri=4, roles="blk rem",
    battleswap=bs_erikacchu, enterwatch=w_erikacchu,
    text="スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
         "バトルさせてもよい）。このクリーチャーは攻撃できない。"
         "相手のクリーチャーが手札以外から出た時、このクリーチャーとそのクリーチャーをバトルさせてもよい",
    source=SRC["k28_erikacchu"])


# ================================================================ 47/77 極勝秘伝カイザー・ビクトリー
def sp_kaiser(s, i):
    """自分の山札の上から1枚をマナゾーンに置く。その後、カード1枚を自分のマナゾーンから手札に戻してもよい"""
    s.ramp(i, 1, tapped=False)
    _take_best_mana(s, i, "極勝秘伝カイザー・ビクトリー", floor=5)


def _kaiser_useful(s, i):
    """アタック・チャンスで唱える価値があるか（山札が残っているか、戻す価値のあるマナがあるか）"""
    p = s.P[i]
    if len(p.deck) > 1:
        return True
    return bool(p.mana) and E.PRI[max(p.mana, key=E.PRI.get)] >= 5


add("k28_kaiser", "極勝秘伝カイザー・ビクトリー", 3, "N", kind="S", pri=4, roles="acc draw",
    spell=sp_kaiser, atkwatch=ac_watch("k28_kaiser", "N", _kaiser_useful),
    freeacts=rc_acts("k28_kaiser", "N"), actapply={"x:k28_kaiser": rc_apply("k28_kaiser", "N")},
    text=_hiden_text("N", "自分の山札の上から1枚をマナゾーンに置く。その後、カード1枚を、"
                          "自分のマナゾーンから手札に戻してもよい。"),
    source=SRC["k28_kaiser"])


# ================================================================ 48/77 熱血刃 ニケ
def e_nike(s, i, u):
    _freeze_one(s, i, "熱血刃 ニケ")


def l_nike(s, i, u, dest):
    _freeze_one(s, i, "熱血刃 ニケ")


add("k28_nike", "熱血刃 ニケ", 3, "LW", power=4500, jd=True,
    races=("outragecommand", "command", "revolution", "hamukatsu"), pri=5, roles="dis rem",
    enter=e_nike, left=l_nike,
    text="ジャストダイバー（出た時、次の自分のターンのはじめまで、相手に選ばれず攻撃されない）。"
         "このクリーチャーが出た時または離れた時、相手のクリーチャー1体を選んでタップする。"
         "次の自分のターンのはじめまで、そのクリーチャーはアンタップしない",
    source=SRC["k28_nike"])


# ================================================================ 49/77 刀の3号 カツえもん逆
def px_katsuemon(s, i, u, atk):
    """自分のクリーチャーが3体以上あれば、このクリーチャーのパワーを+6000する"""
    return 6000 if s.ncre(i) >= 3 else 0


add("k28_katsuemon", "刀の3号 カツえもん逆", 4, "LN", power=6000, blocker=True,
    races=("megacommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=6, roles="blk atk",
    powerx=px_katsuemon, brkx=_powered_brk,
    text="ブロッカー。パワード・ブレイカー（このクリーチャーは、そのパワー6000ごとにシールドをもう1つブレイクする）。"
         "自分のクリーチャーが3体以上あれば、このクリーチャーのパワーを+6000する",
    source=SRC["k28_katsuemon"])


# ================================================================ 50/77 超熱血 ロビー
def lw_robby(s, i, u, dest, destroy):
    """他のクリーチャーが離れた時、そのターン、このクリーチャーのパワーを+2000する
    （どちらのプレイヤーのクリーチャーが離れても誘発する）"""
    if u.c.kind != "C":
        return
    for j in (0, 1):
        if not s.has(j, "k28_robby"):
            continue
        for z in s.P[j].board:
            if z.k == "k28_robby" and z is not u:
                z.pw += 2000


add("k28_robby", "超熱血 ロビー", 3, "WD", power=3000, blocker=True,
    races=("outragecommand", "command", "revolution", "hamukatsu"), pri=5, roles="blk atk",
    brkx=_powered_brk, leavewatch=lw_robby,
    text="ブロッカー。パワード・ブレイカー（このクリーチャーは、そのパワー6000ごとにシールドをもう1つブレイクする）。"
         "他のクリーチャーが離れた時、そのターン、このクリーチャーのパワーを+2000する",
    source=SRC["k28_robby"])


# ================================================================ 51/77 D2-W革命のボルトロン
def t_boltron(s, i, u):
    """自分のターンの終わりに、自分のクリーチャー1体に封印を1つ置く（失うのがいちばん安いものを選ぶ）"""
    t = worst_own(s, i)
    if t is None:
        return
    s.ev(f"　D2-W革命のボルトロン：{t.c.name} に封印を1つ置く")
    s.seal(i, t, 1)


add("k28_boltron", "D2-W革命のボルトロン", 3, "DF", power=10000, brk=2,
    races=("soniccommand", "command", "initialsw"), pri=7, roles="atk fin",
    tend=t_boltron,
    text="W・ブレイカー。自分のターンの終わりに、自分のクリーチャー1体に封印を1つ置く"
         "（封印するには自分の山札の上から1枚を裏向きでそのカードの上に置く。封印されたクリーチャーは"
         "バトルゾーンにないものとして扱う。コマンドが出た時、持ち主はその文明の封印を1つ墓地に置く）",
    source=SRC["k28_boltron"])


# ================================================================ 52/77 V闘龍 カツドン
def e_katsudon(s, i, u):
    """出た時、自分の山札の上から2枚をマナゾーンに置いてもよい。
    そうしたら、カード1枚を自分のマナゾーンから手札に戻す（戻すのは任意ではない）"""
    p = s.P[i]
    if len(p.deck) <= 2:
        return                                  # 山札が足りない時は置かない（置かなければ戻さなくてよい）
    n0 = len(p.mana)
    s.ramp(i, 2, tapped=False)
    if len(p.mana) <= n0:
        return
    _take_best_mana(s, i, "V闘龍 カツドン", floor=0)


add("k28_katsudon", "V闘龍 カツドン", 5, "FN", power=8000, brk=2, sa=True,
    races=("outragecommand", "command", "revolution", "hamukatsu"), pri=8, roles="acc atk draw",
    enter=e_katsudon,
    text="スピードアタッカー。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から2枚をマナゾーンに置いてもよい。"
         "そうしたら、カード1枚を自分のマナゾーンから手札に戻す",
    source=SRC["k28_katsudon"])


# ================================================================ 53/77 タイム槍 ドレミ
def e_doremi(s, i, u):
    """出た時、次の自分のターンのはじめまで、相手はコスト3以下の呪文を唱えられない"""
    s.P[i].x["k28_doremi"] = s.turn + (1 if s.tp == i else 0)
    s.ev("　タイム槍 ドレミ：次の自分のターンのはじめまで、相手はコスト3以下の呪文を唱えられない")


def sl_doremi(s, i, cost):
    """i＝唱えようとしている側。相手のドレミの効果が生きていれば、コスト3以下は唱えられない"""
    if cost > 3:
        return False
    return s.P[1 - i].x.get("k28_doremi", -1) >= s.turn


add("k28_doremi", "タイム槍 ドレミ", 4, "L", power=4500, blocker=True,
    races=("angelcommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=6, roles="blk dis",
    enter=e_doremi, spelllock=sl_doremi, changex=cx_change("L"), playrule=pr_change("L"),
    text=_change_text("L") +
         "ブロッカー。このクリーチャーが出た時、次の自分のターンのはじめまで、"
         "相手はコスト3以下の呪文を唱えられない",
    source=SRC["k28_doremi"])


# ================================================================ 54/77 熱血の羅刹 メフィス・トリック
add("k28_mephis", "熱血の羅刹 メフィス・トリック", 3, "L", power=8000, blocker=True, noatkp=True,
    races=("demoncommand", "command", "unknown"), pri=5, roles="blk",
    text="ブロッカー。このクリーチャーは相手プレイヤーを攻撃できない",
    source=SRC["k28_mephis"])


# ================================================================ 55/77 神判のラクシャ コットン
def d_cotton(s, i, u):
    """シールド・ゴー：このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する"""
    p = s.P[i]
    if u.k not in p.grave:
        return
    p.grave.remove(u.k)
    if not s.add_shield(i, u.k, True):
        p.grave.append(u.k)
        return
    s.ev("　シールド・ゴー：神判のラクシャ コットンを表向きのシールドとして置く")


def sd_cotton(s, i, k, up, dest):
    """シールド・ゴー：表向きのままシールドゾーンを離れる時は、かわりに墓地に置く（shielddest）

    行き先を1枚ごとに決める差し込み口なので、env27 のシールド・ゴー（ミルク・ユキメ）の
    表向きのシールドと同時にブレイクされても、どちらもきちんと墓地へ行く。"""
    return "grave" if up else dest


add("k28_cotton", "神判のラクシャ コットン", 2, "L", power=1500, blocker=True,
    races=("oracle", "humanoid"), pri=3, roles="blk shd",
    destroyed=d_cotton, shielddest=sd_cotton,
    text="ブロッカー。シールド・ゴー（このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する。"
         "表向きのままシールドゾーンを離れる時は、かわりに墓地に置く）",
    source=SRC["k28_cotton"])


# ================================================================ 56/77 熱血の親衛隊ラプソディ
def _nc_count(s, i):
    """場に出ている自分のクリーチャーでない札（タマシード・クロスギア）と、表向きの自分の城の数"""
    p = s.P[i]
    n = sum(1 for z in p.board if z.c.kind in ("T", "X", "G"))
    n += sum(1 for k, up in p.sh if up and BY_KEY[k].kind == "G")
    return n


def fa_rhapsody(s, i, av, cv):
    """「このターンにクリーチャーでないカードを実行したか」を数えるための見回り（手は増やさない）。
    呪文は p.spl（ターンごとに0に戻る）で分かるので、ここではタマシード・クロスギア・城の増え方を見る"""
    p = s.P[i]
    if "k28_rhapsody" not in (p.list or {}):
        return []
    if p.x.get("k28_ncturn") != s.turn:
        p.x["k28_ncturn"] = s.turn
        p.x["k28_ncbase"] = _nc_count(s, i)
        p.x["k28_ncdone"] = 0
    elif not p.x.get("k28_ncdone") and _nc_count(s, i) > p.x.get("k28_ncbase", 0):
        p.x["k28_ncdone"] = 1
    return []


def ca_rhapsody(s, i, u):
    """このターンに自分がクリーチャーでないカードを実行していなければ、このクリーチャーは攻撃できない"""
    p = s.P[i]
    if p.spl > 0:
        return False
    return not (p.x.get("k28_ncturn") == s.turn and p.x.get("k28_ncdone"))


add("k28_rhapsody", "熱血の親衛隊ラプソディ", 1, "L", power=4000, blocker=True,
    races=("initiate", "hunter", "alien"), pri=3, roles="blk",
    cantatk=ca_rhapsody, freeacts=fa_rhapsody, status="partial",
    note="「このターンにクリーチャーでないカードを実行したか」のうち、呪文（ツインパクトの呪文側も含む）は"
         "p.spl でそのまま分かるが、タマシード・クロスギア・城については、エンジンに"
         "「カードを実行した時」の差し込み口（PLAYWATCH）がまだ無いため、打てる手を数える時に"
         "バトルゾーンのタマシード・クロスギアと表向きの城の数が増えたかを見る見回りで代用している。"
         "ふつうに置いた分は同じターンのうちに必ず数えられるが、置いたタマシードがその場で"
         "バトルゾーンから消える場合（《創世竜 Drache derZen》の下に置かれる等）は数えられず、"
         "攻撃できないままになる",
    text="ブロッカー。このターンに自分がクリーチャーでないカードを実行していなければ、"
         "このクリーチャーは攻撃できない",
    source=SRC["k28_rhapsody"])


# ================================================================ 57/77 ホーリー・出す・バナナ
def sp_banana(s, i):
    """自分のクリーチャーを1体アンタップする。次の自分のターンのはじめまで、
    そのクリーチャーのパワーを+4000し、「ブロッカー」を与える
    （アンタップに意味があるタップ状態のものを優先し、そのなかでいちばん大事なものを選ぶ）"""
    p = s.P[i]
    cs = [z for z in p.board if z.c.kind == "C"]
    if not cs:
        return
    taps = [z for z in cs if z.tap]
    t = max(taps or cs, key=s.val)
    t.tap = False
    t.x["k28_banana"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　ホーリー・出す・バナナ：{t.c.name} をアンタップし、パワー+4000とブロッカーを与える")


def ap_banana(s, i, u, atk):
    return 4000 if u.x.get("k28_banana", -1) >= s.turn else 0


def bo_banana(s, u):
    return u.x.get("k28_banana", -1) >= s.turn


add("k28_banana", "ホーリー・出す・バナナ", 2, "L", kind="S", trig=True, pri=3, roles="trg blk",
    spell=sp_banana, aurap=ap_banana, blockok=bo_banana,
    text="S・トリガー。自分のクリーチャーを1体アンタップする。次の自分のターンのはじめまで、"
         "そのクリーチャーのパワーを+4000し、「ブロッカー」を与える",
    source=SRC["k28_banana"])


# ================================================================ 58/77 宇宙 バリアスキー
def e_barrier(s, i, u):
    _bounce_one(s, i, "宇宙 バリアスキー")


def l_barrier(s, i, u, dest):
    _bounce_one(s, i, "宇宙 バリアスキー")


add("k28_barrier", "宇宙 バリアスキー", 5, "W", power=5000, blocker=True,
    races=("magiccommand", "command", "sinvader"), pri=7, roles="blk rem",
    enter=e_barrier, left=l_barrier,
    text="ブロッカー。このクリーチャーが出た時または離れた時、相手のクリーチャー1体を選び、"
         "持ち主の手札に戻してもよい（種族にS級侵略者を持つが、侵略の能力は持たない）",
    source=SRC["k28_barrier"])


# ================================================================ 59/77 【問銃】テック
def e_tech(s, i, u):
    """出た時、相手のクリーチャー1体を選ぶ。次の自分のターンのはじめまで、そのクリーチャーは攻撃もブロックもできない"""
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　【問銃】テック：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k28_tech", "【問銃】テック", 4, "W", power=4000, jd=True,
    races=("crystalcommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=6, roles="dis",
    enter=e_tech, changex=cx_change("W"), playrule=pr_change("W"),
    text=_change_text("W") +
         "ジャストダイバー（出た時、次の自分のターンのはじめまで、相手に選ばれず攻撃されない）。"
         "このクリーチャーが出た時、相手のクリーチャー1体を選ぶ。次の自分のターンのはじめまで、"
         "そのクリーチャーは攻撃もブロックもできない",
    source=SRC["k28_tech"])
