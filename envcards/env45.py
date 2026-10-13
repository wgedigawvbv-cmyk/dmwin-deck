"""担当45：DM26-EX2「悪感謝祭 カリスマBEST」の未実装カード15枚（key は k45_）

出典：dmwiki.net の各カードページ。15枚すべてについて、カードページ
      （https://dmwiki.net/《カード名》）と生の wiki ソース（?plugin=template&refer=《カード名》）を
      別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらも一致することを確かめた。

  この札束に入っている仕組み
    ・**G・リンク（ゴッド）** … 《聖霊左神ジャスティス》の「左G・リンク」。`godlink=("L", ())` で
      位置を宣言し、つなぐ操作は `freeacts=`／`actapply=` の追加の手（`s.can_link`／`s.god_link`）で出す。
      「リンクしている間シールドをさらに1枚ブレイクする」は `brkx=`（リンクの頭をたどって判定）。
      《ゴッド・ゲート》《ゴッド・シグナル》の「ゴッドを探す／出す」部分も実装できている。
    ・**墓地進化GV**（煉獄邪神M・R・C・ロマノフ）＝墓地の闇か火のクリーチャー3体の上に重ねて出す。
      `freeacts=`／`actapply=` の手として作り、3枚を `u.under` に入れた（メテオバーンの弾になる）。
    ・**進化GV・Ω**（不敬合成王 ロマティックダム・アルキング）＝墓地・マナ・バトルゾーンから1体ずつ。
      バトルゾーンの1体は `s.enter(..., on=)` で下に、残り2枚を `u.under` に足した。
    ・**エクストラEXライフ**（同）＝出る時シールド2枚。離れる時はそのうち1つを墓地に置いて残る。
      「『EXライフ』シールドが離れた時」は `shieldout=` で誘発させている（見回りではない）。
    ・**G-NEO進化＋メガメテオバーン3**（魔誕導師ブラックルシファー）。
      「次の自分のターンのはじめまで、相手のクリーチャーが出た時に破壊する」は `enterwatch=` で、
      持ち主の `p.x` に期限のターン番号を入れて見ている。
    ・**天才シンパシー**（伝説の正体 ギュウジン丸）＝自分の水のクリーチャー1体につきコスト-10。
    ・**革命チェンジ＋ブロッカー／スピードアタッカーの付与**（竜皇神 ボルシャック・バクテラス）。
      「各ターンの終わりに自分の他のクリーチャーをすべてアンタップ」は `tendp=`
      （バトルゾーンが空でも呼ばれる差し込み口）で書いた。
    ・**相手のターンの終わりにただで唱える呪文**（「ちくしょおおおおおおっー!!」）。
      「そのターン自分のクリーチャーが破壊されていたか」は `leavewatch=` で記録している。
    ・**山札からバトルゾーン／マナゾーンに置かれるのを山札の下に置き換える**（DG 〜裁キノ刻〜）。
      バトルゾーンぶんは `fatex=`（"no" を返すと src="deck" のカードは山札の下に戻る）で、
      マナゾーンぶんは `manain=` で置き直している（エンジンの `manarep=` は墓地にしか送れない）。

  調べ直して意外だった点
    ・《DG 〜裁キノ刻～》は城やフィールドではなく**無色・コスト2・パワー2000のクリーチャー（メタリカ）**。
      3つめの能力は**両方のプレイヤー**に効く（自分の山札からの踏み倒しも止まる）。
      ページ名の「〜」は波ダッシュ（U+301C）で、全角チルダでは開けなかった。
    ・《竜皇神 ボルシャック・バクテラス》は名前に「神」が付くがゴッドではなく、
      **アーマード・ドラゴン単一種族の革命チェンジ**（コスト7以上の多色の《ボルシャック》から）。
      スピードアタッカーを与えるのは「自分の**他の**クリーチャー」で、自分自身は得ない。
    ・《伝説の正体 ギュウジン丸》はコスト**71**・パワー**71000**で、天才シンパシーの軽減は
      1体につき**10**（シンパシーの10倍）。6体以上を山札に戻させたら特殊勝利。
    ・《マントラ・ルピア》はシノビだが**ニンジャ・ストライクを持たない**（スピードアタッカーだけ）。
    ・《聖霊左神ジャスティス》は**無色**（ゴッド・ノヴァ）。パワー表記は「8000+」で素のパワーは8000。
    ・《煉獄邪神M・R・C・ロマノフ》のコストは**20**で、軽減は「すべての墓地のカード1枚につき1」。
      両者の墓地を数えるので、終盤にはほぼ最低コストまで落ちる。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy
from envcards.env0 import discard_choice, owner_of, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k45_mantra": W + "《マントラ・ルピア》",
    "k45_chara": W + "《チャラ・ルピア》",
    "k45_bakuteras": W + "《竜皇神 ボルシャック・バクテラス》",
    "k45_gyujin": W + "《伝説の正体 ギュウジン丸》",
    "k45_zetsubo": W + "《絶望と反魂と滅殺の決断》",
    "k45_mrcromanov": W + "《煉獄邪神M・R・C・ロマノフ》",
    "k45_arkacrown": W + "《天罪堕将 アルカクラウン》",
    "k45_blacklucifer": W + "《魔誕導師ブラックルシファー》",
    "k45_alking": W + "《不敬合成王 ロマティックダム・アルキング》",
    "k45_justice": W + "《聖霊左神ジャスティス》",
    "k45_dg": W + "《DG 〜裁キノ刻〜》",
    "k45_chikusho": W + "《「ちくしょおおおおおおっー!!」》",
    "k45_heavensgate": W + "《ヘブンズ・ゲート》",
    "k45_godgate": W + "《ゴッド・ゲート》",
    "k45_godsignal": W + "《ゴッド・シグナル》",
}


# ---------------------------------------------------------------- G・リンク（共通の道具）
# ゴッドを横につないで1体のクリーチャーとして扱う。パワーは合計、能力と文明は併せ持ち、
# 離れる時は構成しているカードのうち1枚だけが離れる（エンジンの `parts`／`god_link` が面倒を見る）。
# つなぐ操作は「自分のメインステップ中の追加の手」として出す（エンジンの決まり）。
# 位置（左 L・中央 C・右 R）が重ならない組み合わせだけつなげられる
# （「左G・リンク」は「中央」か「右」を持つゴッドの左にしか付けない、という決まりをこれで表している）。
_GL_KEYS = frozenset(("k45_justice",))
_GL_ACT = "x:k45_glink"


def _gl_head(s, i, u):
    """u を含んでいるクリーチャー（リンクの頭）。リンクしていなければ u 自身"""
    for z in s.P[i].board:
        if z is u or u in z.link:
            return z
    return u


def _gl_linked(s, i, u):
    """u がいまG・リンクしているか"""
    return bool(_gl_head(s, i, u).link)


def _gl_ok(s, i, u, base):
    """u を base の横につなげるか（エンジンの可否＋G・リンクの位置が重ならないこと）"""
    if u.link or u.k not in E.GODLINK or not s.can_link(i, u, base):
        return False
    pos = {E.GODLINK[z.k][0] for z in s.parts(base) if z.k in E.GODLINK}
    return bool(pos) and E.GODLINK[u.k][0] not in pos


def _gl_acts(s, i, av, cv):
    """追加の手：このモジュールのゴッドを、自分の場のゴッドの横につなぐ
    （u 側が自分のモジュールのカードの組だけを出すので、ほかのモジュールと重複しない）"""
    out = []
    bd = s.P[i].board
    for u in bd:
        if u.k not in _GL_KEYS:
            continue
        for base in bd:
            if base is not u and _gl_ok(s, i, u, base):
                out.append((_GL_ACT, u.uid, base.uid))
    return out


def _gl_apply(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k in _GL_KEYS), None)
    base = next((z for z in p.board if z.uid == a[2]), None)
    if u is None or base is None or not _gl_ok(s, i, u, base):
        return
    p.board.remove(u)
    if u.tap:
        base.tap = True        # つなぐ相手が1体でもタップしていれば、1体のクリーチャーはタップしたまま
    s.god_link(i, u, base)


# ================================================================ 共通の道具
def _plain_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので除く）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _top(s, i, n):
    """山札の上からn枚を取り出す（山札は1枚残す）"""
    p = s.P[i]
    n = min(n, len(p.deck) - 1)
    if n <= 0:
        return []
    return [p.deck.pop() for _ in range(n)]


def _bottom(s, i, ks):
    """好きな順序で山札の下に置く"""
    p = s.P[i]
    for k in ks:
        p.deck.insert(0, k)


def _armored(c):
    """アーマード・カードか（種族名が「アーマード」で始まるもの）"""
    return any(r == "armored" or r.startswith("armored") for r in c.races)


def _dragon(c):
    """ドラゴン・クリーチャーか（種族名に「ドラゴン」を含むもの。ドラゴノイドは含まない）"""
    if c.kind != "C":
        return False
    return any("dragon" in r and r != "dragonoid" for r in c.races)


def _god(c):
    """ゴッドか（ゴッド・ノヴァなども含む）"""
    return any("god" in r for r in c.races)


def _minus_power(s, i, t, n, who):
    """相手のクリーチャー t のパワーをこのターン -n する（0以下なら破壊される）"""
    t.pw -= n
    s.ev(f"　{who}：{t.c.name} のパワーをこのターン-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _put_from_hand(s, i, pred, n, summon=False):
    """手札から条件に合うカードを n 体まで、コストを支払わずに出す（重要度の高いものから）"""
    p = s.P[i]
    done, skip = 0, set()
    while done < n and not s.over:
        cands = [k for k in p.hand if k not in skip and pred(BY_KEY[k])]
        if not cands:
            break
        k = max(cands, key=E.PRI.get)
        if s.fate(i, k, "hand", summon) != "ok":
            skip.add(k)
            continue
        p.hand.remove(k)
        s.ev(f"　手札から {BY_KEY[k].name} を{'召喚' if summon else '出す'}（コストを支払わずに）")
        s.enter(i, k, "hand", summon)
        done += 1
    return done


def _civs_in_mana(s, i):
    return set("".join(E.MCIV[k] for k in s.P[i].mana))


# ================================================================ 1 マントラ・ルピア
def e_mantra(s, i, u):
    """出た時、山札の上から2枚を見て、アーマード・カード1枚を表向きでシールド化してもよい"""
    top = _top(s, i, 2)
    if not top:
        return
    cands = [k for k in top if _armored(BY_KEY[k])]
    if cands:
        k = max(cands, key=E.PRI.get)
        if s.add_shield(i, k, True):
            top.remove(k)
            s.ev(f"　マントラ・ルピア：{BY_KEY[k].name} を表向きのシールドにした")
    _bottom(s, i, top)


add("k45_mantra", "マントラ・ルピア", 3, "LF", power=4000, sa=True,
    races=("armoreddragon", "firebird", "mechadelstella", "shinobi"), pri=4, roles="shd atk acc",
    enter=e_mantra,
    text="スピードアタッカー。"
         "このクリーチャーが出た時、自分の山札の上から2枚を見る。"
         "その中からアーマード・カードを1枚、表向きでシールド化してもよい。"
         "残りを好きな順序で山札の下に置く（置くカードは重要度のいちばん高いものを選ぶ）",
    source=SRC["k45_mantra"])


# ================================================================ 2 チャラ・ルピア
def ca_chara(s, i, k, cur):
    """自分のドラゴン・クリーチャーの召喚コストを2少なくする（0以下にはならない＝下限1）"""
    if cur <= 1 or not s.has(i, "k45_chara"):
        return cur
    n = sum(1 for z in s.P[i].board if z.k == "k45_chara")
    if not _dragon(BY_KEY[k]):
        return cur
    return max(1, cur - 2 * n)


add("k45_chara", "チャラ・ルピア", 2, "LF", power=1500, races=("firebird",), pri=3, roles="acc",
    costaura=ca_chara,
    text="自分のドラゴン・クリーチャーの召喚コストを2少なくする。ただしコストは0以下にはならない",
    source=SRC["k45_chara"])


# ================================================================ 3 竜皇神 ボルシャック・バクテラス
def e_bakuteras(s, i, u):
    """出た時、山札の上から4枚を見て、その中の（自身以外の）アーマードを好きな数出す"""
    top = _top(s, i, 4)
    if not top:
        return
    for k in sorted(top, key=lambda x: -E.PRI[x]):
        if s.over:
            break
        c = BY_KEY[k]
        if k == "k45_bakuteras" or not _armored(c):
            continue
        if c.kind == "C":
            if not _plain_cre(c) or s.fate(i, k, "deck", False) != "ok":
                continue
            top.remove(k)
            s.ev(f"　ボルシャック・バクテラス：山札から {c.name} を出す")
            s.enter(i, k, "deck", False)
        elif c.kind == "T":
            top.remove(k)
            s.ev(f"　ボルシャック・バクテラス：山札から {c.name} を出す")
            s.place_tama(i, k)
    _bottom(s, i, top)


def _other_bakuteras(s, j, u):
    """u 以外の《竜皇神 ボルシャック・バクテラス》が自分の場にいるか（「自分の他の」の判定）"""
    return any(z.k == "k45_bakuteras" and z is not u for z in s.P[j].board)


def bo_bakuteras(s, u):
    """自分の他のクリーチャーすべてにブロッカーを与える"""
    if u.c.kind != "C":
        return False
    return _other_bakuteras(s, owner_of(s, u), u)


def sa_bakuteras(s, i, u):
    """自分の他のクリーチャーすべてにスピードアタッカーを与える"""
    return u.c.kind == "C" and _other_bakuteras(s, i, u)


def tdp_bakuteras(s, j):
    """各ターンの終わりに、自分の他のクリーチャーをすべてアンタップする"""
    if not s.has(j, "k45_bakuteras"):
        return
    n = 0
    for z in s.P[j].board:
        if z.c.kind == "C" and z.tap and _other_bakuteras(s, j, z):
            z.tap = False
            n += 1
    if n:
        s.ev(f"　ボルシャック・バクテラス：ターンの終わりに自分の他のクリーチャー{n}体をアンタップ")


def _bakuteras_src(c):
    return c.kind == "C" and c.cost >= 7 and "ボルシャック" in c.name and len(set(c.civ)) >= 2


add("k45_bakuteras", "竜皇神 ボルシャック・バクテラス", 10, "LF", power=17000, brk=3,
    races=("armoreddragon",), pri=13, roles="fin atk blk acc",
    enter=e_bakuteras, blockok=bo_bakuteras, saok=sa_bakuteras, tendp=tdp_bakuteras,
    changex=lambda s, i, u: _bakuteras_src(u.c),
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items()
                                         if kk != k and _bakuteras_src(BY_KEY[kk])) >= 2
    else "革命チェンジの元（コスト7以上の多色の《ボルシャック》）が2枚ない",
    text="革命チェンジ：コスト7以上の、名前に《ボルシャック》とある多色クリーチャー。T・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から4枚を見て、その中から"
         "《竜皇神 ボルシャック・バクテラス》ではないアーマードを好きな数出す（出せるものはすべて出す）。"
         "残りを好きな順序で山札の下に置く。"
         "自分の他のクリーチャーすべてに「ブロッカー」と「スピードアタッカー」を与える。"
         "各ターンの終わりに、自分の他のクリーチャーをすべてアンタップする",
    source=SRC["k45_bakuteras"])


# ================================================================ 4 伝説の正体 ギュウジン丸
def cx_gyujin(s, i, av):
    """天才シンパシー：自分の水のクリーチャー1体につきコストを10少なくする（0以下にはならない）"""
    n = sum(1 for z in s.P[i].board if z.c.kind == "C" and "W" in z.c.civ)
    return max(0, 71 - 10 * n)


def e_gyujin(s, i, u):
    """召喚で出た時、相手は自身のクリーチャーをすべて山札に加えてシャッフルする。6体以上なら勝ち"""
    if not u.x.get("summoned"):
        return
    o = s.P[1 - i]
    n = 0
    for z in list(o.board):
        if s.over:
            break
        if z.c.kind != "C":
            continue
        if s.leave(1 - i, z, "deck", by_opp=True):
            n += 1
    if n:
        s.rng.shuffle(o.deck)
    s.ev(f"　ギュウジン丸：相手のクリーチャー{n}体を山札に加えてシャッフル")
    if n >= 6:
        s.win(i, "伝説の正体 ギュウジン丸")


add("k45_gyujin", "伝説の正体 ギュウジン丸", 71, "W", power=71000, brk=99,
    races=("theanswer",), pri=15, roles="fin rem",
    costx=cx_gyujin, enter=e_gyujin,
    text="天才シンパシー：水のクリーチャー（このクリーチャーの召喚コストは、"
         "バトルゾーンにある自分の水のクリーチャー1体につき10少なくなる。ただしコストは0以下にならない）。"
         "ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "このクリーチャーが召喚によって出た時、相手は自身のクリーチャーをすべて山札に加えてシャッフルする。"
         "相手がこうして6体以上山札に加えたなら、自分はゲームに勝つ",
    note="コスト71・軽減は水のクリーチャー1体につき10なので、召喚するには"
         "バトルゾーンに自分の水のクリーチャーが7体ほど必要。envtest の試験場面では"
         "その盤面が作れないため「使える場面」が0になることがある（実装自体は動く）",
    source=SRC["k45_gyujin"])


# ================================================================ 5 絶望と反魂と滅殺の決断
def _zetsu_rev(c):
    return c.cost <= 4 and "D" in c.civ


def _zetsu_one(s, i):
    """3つのモードから、いちばん効き目の大きいものを1つ選ぶ（全デッキ共通の決まり）"""
    p, o = s.P[i], s.P[1 - i]
    t = s.target(i)
    v_kill = -1
    if t is not None:
        v_kill = s.val(t) + 5 if s.power(1 - i, t) <= 4000 else 1
    g = [k for k in set(p.grave)
         if BY_KEY[k].kind == "C" and not BY_KEY[k].evo and _zetsu_rev(BY_KEY[k])]
    v_rev = max((E.PRI[k] for k in g), default=-1)
    v_dis = 3 if o.hand else -1
    if t is not None and v_kill >= v_rev and v_kill >= v_dis:
        _minus_power(s, i, t, 4000, "絶望と反魂と滅殺の決断")
    elif g and v_rev >= v_dis:
        s.ev("　絶望と反魂と滅殺の決断：墓地からコスト4以下の闇のクリーチャーを出す")
        s.revive(i, _zetsu_rev, "grave")
    elif o.hand:
        s.ev("　絶望と反魂と滅殺の決断：相手は自身の手札を1枚捨てる")
        discard_choice(s, 1 - i)


def sp_zetsubo(s, i):
    for _ in range(2):
        if s.over:
            return
        _zetsu_one(s, i)


def fa_zetsubo(s, i, av, cv):
    """自分の墓地からも唱えられる（コストは普通に支払う）"""
    p = s.P[i]
    if "k45_zetsubo" not in p.grave or av < 5 or "D" not in cv:
        return []
    if not s.spell_ok(i, 5) or s.manaexec(i):
        return []
    return [("x:k45_zetsu", "k45_zetsubo", 5)]


def ap_zetsubo(s, a):
    i = s.tp
    p = s.P[i]
    if "k45_zetsubo" not in p.grave or len(p.mana) - p.mused < a[2]:
        return
    p.mused += a[2]
    p.grave.remove("k45_zetsubo")
    s.ev(f"呪文：絶望と反魂と滅殺の決断（自分の墓地から、{a[2]}マナ）")
    s.cast(i, "k45_zetsubo")
    if "k45_zetsubo" in p.grave:               # 唱えた後は墓地のかわりに山札の下へ
        p.grave.remove("k45_zetsubo")
        p.deck.insert(0, "k45_zetsubo")


add("k45_zetsubo", "絶望と反魂と滅殺の決断", 5, "D", kind="S", pri=7, roles="rem dis acc fin",
    spell=sp_zetsubo, freeacts=fa_zetsubo, actapply={"x:k45_zetsu": ap_zetsubo},
    text="この呪文を自分の墓地から唱えてもよい。そうしたら、唱えた後、墓地のかわりに山札の下に置く。"
         "次の中から2回選ぶ（同じものを選んでもよい）。"
         "(1)相手は自身の手札を1枚選び、捨てる／"
         "(2)コスト4以下の闇のクリーチャーまたはオーラを1つ、自分の墓地から出す／"
         "(3)相手のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを-4000する"
         "（パワー0以下のクリーチャーは破壊される）。"
         "どれを選ぶかは、倒せる相手の重要度・墓地から出せるクリーチャーの重要度・相手の手札の有無を"
         "見比べて機械的に決める",
    note="オーラ（オレガ・オーラ）はこのシミュレーターに無いので、"
         "(2)は墓地のクリーチャーだけを出す",
    status="partial", source=SRC["k45_zetsubo"])


# ================================================================ 6 煉獄邪神M・R・C・ロマノフ
def _mrc_src(c):
    return c.kind == "C" and bool(set("DF") & set(c.civ))


def cx_mrcromanov(s, i, av):
    """すべての墓地にあるカード1枚につきコストを1少なくする（下限1）"""
    g = len(s.P[0].grave) + len(s.P[1].grave)
    return max(1, 20 - g)


def fa_mrcromanov(s, i, av, cv):
    """墓地進化GV：墓地の闇または火のクリーチャー3体の上に重ねて出す"""
    p = s.P[i]
    if "k45_mrcromanov" not in p.hand:
        return []
    if sum(1 for k in p.grave if _mrc_src(BY_KEY[k])) < 3:
        return []
    n = cx_mrcromanov(s, i, av)
    if n <= av and cv.issuperset("DF") and s.fate(i, "k45_mrcromanov", "hand", True) == "ok":
        return [("x:k45_mrc", "k45_mrcromanov", n)]
    return []


def ap_mrcromanov(s, a):
    i = s.tp
    p = s.P[i]
    if "k45_mrcromanov" not in p.hand or len(p.mana) - p.mused < a[2]:
        return
    cres = sorted((k for k in p.grave if _mrc_src(BY_KEY[k])), key=E.PRI.get)[:3]
    if len(cres) < 3:
        return
    p.mused += a[2]
    p.hand.remove("k45_mrcromanov")
    for k in cres:
        p.grave.remove(k)
    s.ev(f"墓地進化GV：煉獄邪神M・R・C・ロマノフ（{a[2]}マナ、墓地の闇・火のクリーチャー3体の上に）")
    u = s.enter(i, "k45_mrcromanov", "hand", True)
    if u is not None:
        u.under.extend(cres)
    else:
        p.grave.extend(cres)


def a_mrcromanov(s, i, u):
    """メテオバーン：攻撃する時、下のカードを3枚まで墓地に置き、1枚につき墓地の闇か火の
    コスト6以下の呪文をただで唱え、唱えた後は山札の下に置く"""
    p = s.P[i]

    def ok(k):
        c = BY_KEY[k]
        return c.kind == "S" and c.cost <= 6 and bool(set("DF") & set(c.civ))

    for _ in range(3):
        if s.over or not u.under:
            break
        cands = [k for k in p.grave if ok(k)]
        if not cands:
            break
        k = max(cands, key=E.PRI.get)
        if not s.spell_ok(i, BY_KEY[k].cost):
            break
        z = min(u.under, key=lambda x: E.PRI[x])
        u.under.remove(z)
        s.grave_put(i, z)
        if k not in p.grave:
            break
        p.grave.remove(k)
        s.ev(f"　メテオバーン：墓地の {BY_KEY[k].name} をコストを支払わずに唱える")
        s.cast(i, k)
        if k in p.grave:
            p.grave.remove(k)
            p.deck.insert(0, k)


add("k45_mrcromanov", "煉獄邪神M・R・C・ロマノフ", 20, "DF", power=17000, brk=3, evo="gv",
    races=("god", "darklord", "knight"), pri=14, roles="fin rem atk",
    costx=cx_mrcromanov, attack=a_mrcromanov,
    freeacts=fa_mrcromanov, actapply={"x:k45_mrc": ap_mrcromanov},
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items()
                                         if kk != k and _mrc_src(BY_KEY[kk])) >= 8
    else "墓地進化GVの元になる闇か火のクリーチャーが8枚ない",
    text="墓地進化GV：闇または火のクリーチャーを3体自分の墓地から選び、このクリーチャーをその上に重ねつつ出す。"
         "このクリーチャーの召喚コストは、すべての墓地にあるカード1枚につき1少なくなる"
         "（ただしコストは1より少なくならない）。T・ブレイカー。"
         "メテオバーン：このクリーチャーが攻撃する時、このクリーチャーの下にあるカードを3枚まで墓地に置いてもよい。"
         "こうして墓地に置いたカード1枚につき、闇または火の、コスト6以下の呪文を1枚"
         "自分の墓地からコストを支払わずに唱え、山札の下に置く（重要度のいちばん高い呪文から唱える）",
    note="唱える呪文はツインパクトの呪文側を含めていない（呪文カードだけ）。"
         "墓地進化GVの元は墓地の闇か火のクリーチャーのうち重要度の低い3枚を選ぶ",
    status="partial", source=SRC["k45_mrcromanov"])


# ================================================================ 7 天罪堕将 アルカクラウン
def e_arkacrown(s, i, u):
    """出た時、山札の上から5枚を見て、コスト7以下の各文明のクリーチャーを1体ずつ出してもよい"""
    top = _top(s, i, 5)
    if not top:
        return
    used = set()
    for k in sorted(top, key=lambda x: -E.PRI[x]):
        if s.over:
            break
        c = BY_KEY[k]
        if not _plain_cre(c) or c.cost > 7:
            continue
        free = [x for x in c.civ if x not in used]
        if not free:
            continue
        if s.fate(i, k, "deck", False) != "ok":
            continue
        used.add(free[0])
        top.remove(k)
        s.ev(f"　アルカクラウン：山札から {c.name} を出す（{free[0]}の分）")
        s.enter(i, k, "deck", False)
    _bottom(s, i, top)


add("k45_arkacrown", "天罪堕将 アルカクラウン", 9, "LDN", power=12000, brk=3,
    races=("angelcommand", "demoncommand", "lostcrusader", "command"), pri=12, roles="fin acc atk",
    enter=e_arkacrown,
    text="T・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から5枚を見る。その中から、コスト7以下の"
         "各文明のクリーチャーを1体ずつ選び、出してもよい（文明がまだ埋まっていないものから、"
         "重要度の高い順に出す）。その後、残りを好きな順序で山札の下に置く",
    note="多色クリーチャーは、まだ使っていない文明のうち最初のものの分として数える"
         "（どの文明の枠に当てるかの選び方は全デッキ共通の決まり）",
    source=SRC["k45_arkacrown"])


# ================================================================ 8 魔誕導師ブラックルシファー
def _bl_feed(s, i, u):
    """出た時または自分のターンのはじめに、自分のマナゾーンと墓地から最大1枚ずつ下に置く"""
    p = s.P[i]
    if p.grave:
        k = min(p.grave, key=E.PRI.get)
        p.grave.remove(k)
        u.under.append(k)
        s.ev(f"　ブラックルシファー：墓地の {BY_KEY[k].name} を下に置く")
    if len(u.under) < 3 and len(p.mana) - p.mused >= 3:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        u.under.append(k)
        s.ev(f"　ブラックルシファー：マナの {BY_KEY[k].name} を下に置く")


def e_blacklucifer(s, i, u):
    _bl_feed(s, i, u)


def t_blacklucifer(s, i, u):
    _bl_feed(s, i, u)


def a_blacklucifer(s, i, u):
    """メガメテオバーン3：攻撃する時、下のカードを3枚墓地に置いてもよい。そうしたら、
    次の自分のターンのはじめまで、相手のクリーチャーが出た時にそれを破壊する"""
    if len(u.under) < 3:
        return
    for _ in range(3):
        z = min(u.under, key=lambda x: E.PRI[x])
        u.under.remove(z)
        s.grave_put(i, z)
    s.P[i].x["k45_bl_until"] = s.turn + (1 if s.tp == i else 0)
    s.ev("　メガメテオバーン3：次の自分のターンのはじめまで、相手のクリーチャーが出た時に破壊する")


def ew_blacklucifer(s, i, u):
    """相手のクリーチャーが出た時、それを破壊する（メガメテオバーン3の効果の間だけ）"""
    if u.c.kind != "C":
        return
    if s.P[1 - i].x.get("k45_bl_until", -1) < s.turn:
        return
    if u not in s.P[i].board:
        return
    s.ev(f"　ブラックルシファー：出てきた {u.c.name} を破壊")
    s.leave(i, u, "grave", by_opp=True, destroy=True)


add("k45_blacklucifer", "魔誕導師ブラックルシファー", 6, "DFN", power=11000, brk=2, gs=True,
    evo="DFN", neo=True, gneo=True, races=("demoncommand", "command"), pri=9,
    roles="trg rem atk acc",
    enter=e_blacklucifer, tstart=t_blacklucifer, attack=a_blacklucifer, enterwatch=ew_blacklucifer,
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items()
                                         if kk != k and BY_KEY[kk].kind == "C"
                                         and set("DFN") & set(BY_KEY[kk].civ)) >= 4
    else "G-NEO進化の元になる闇・火・自然のクリーチャーが4枚ない",
    text="G・ストライク。"
         "G-NEO進化：闇、火、または自然のクリーチャー1体の上に置いてもよい"
         "（進化元なしで召喚してもよい。離れる時はかわりに下のカードがすべて離れる）。W・ブレイカー。"
         "このクリーチャーが出た時または自分のターンのはじめに、自分のマナゾーンと墓地から"
         "カードを最大1枚ずつ、このクリーチャーの下に置いてもよい。"
         "メガメテオバーン3：このクリーチャーが攻撃する時、このクリーチャーの下にあるカードを"
         "3枚墓地に置いてもよい。そうしたら、次の自分のターンのはじめまで、"
         "相手のクリーチャーが出た時、そのクリーチャーを破壊する",
    note="下に置くカードは、墓地からは必ず（重要度のいちばん低い1枚）、"
         "マナからは「下が3枚未満で、そのターン使えるマナが3つ以上残る時」だけ取る"
         "（マナを削りすぎないための全デッキ共通の決まり）",
    source=SRC["k45_blacklucifer"])


# ================================================================ 9 不敬合成王 ロマティックダム・アルキング
def e_alking(s, i, u):
    """エクストラEXライフ：出す時、自分の山札の上から2枚をシールド化する"""
    p = s.P[i]
    got = []
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        k = p.deck.pop()
        if s.add_shield(i, k, False):
            got.append(k)
        else:
            p.deck.append(k)
            break
    u.x["k45_ex"] = tuple(got)
    if got:
        s.ev(f"　エクストラEXライフ：シールドを{len(got)}枚置いた")


def rep_alking(s, i, u, dest, destroy_):
    """離れる時、かわりにエクストラEXライフのシールド1つを墓地に置く"""
    if u.k != "k45_alking":
        return False
    p = s.P[i]
    for k in (u.x.get("k45_ex") or ()):
        j = next((x for x, (kk, up) in enumerate(p.sh) if kk == k and not up), None)
        if j is None:
            continue
        s.take_shield(i, j, "grave")       # so_alking が誘発して下のカードを1枚墓地へ
        s.ev("　エクストラEXライフ：シールド1つを墓地に置いて アルキング は残る")
        return True
    u.x["k45_ex"] = ()
    return False


def so_alking(s, i, k, up, dest):
    """「EXライフ」シールドが自分のシールドゾーンを離れた時、下のカードを1枚墓地に置く。
    それが進化ではないクリーチャーなら、自分の墓地から出す"""
    for u in s.P[i].board:
        if u.k != "k45_alking":
            continue
        got = u.x.get("k45_ex") or ()
        if k not in got:
            continue
        lst = list(got)
        lst.remove(k)
        u.x["k45_ex"] = tuple(lst)
        if not u.under:
            return
        pick = [x for x in u.under if _plain_cre(BY_KEY[x]) and not BY_KEY[x].evo]
        z = max(pick, key=E.PRI.get) if pick else min(u.under, key=lambda x: E.PRI[x])
        u.under.remove(z)
        c = BY_KEY[z]
        s.ev(f"　アルキング：下の {c.name} を墓地に置く")
        s.grave_put(i, z)
        p = s.P[i]
        if c.kind == "C" and not c.evo and z in p.grave and s.fate(i, z, "grave", False) == "ok":
            p.grave.remove(z)
            s.ev(f"　アルキング：墓地から {c.name} を出す")
            s.enter(i, z, "grave", False)
        return


def gs_alking(s, di, k):
    """自分のシールドゾーンにあるディスペクターすべてにG・ストライクを与える"""
    return s.has(di, "k45_alking") and "dispector" in BY_KEY[k].races


def fa_alking(s, i, av, cv):
    """進化GV・Ω：自分の墓地・マナゾーン・バトルゾーンからクリーチャーを1体ずつ選んで重ねて出す"""
    p = s.P[i]
    if "k45_alking" not in p.hand:
        return []
    if av < 10 or not cv.issuperset("LWDFN"):
        return []                              # マナから進化元を1枚取るので、コスト9＋1枚ぶん要る
    if not any(BY_KEY[k].kind == "C" for k in p.grave):
        return []
    if not any(BY_KEY[k].kind == "C" for k in p.mana):
        return []
    if worst_own(s, i) is None:
        return []
    if s.fate(i, "k45_alking", "hand", True) != "ok":
        return []
    return [("x:k45_alking", "k45_alking", 9)]


def ap_alking(s, a):
    i = s.tp
    p = s.P[i]
    if "k45_alking" not in p.hand:
        return
    gc = [k for k in p.grave if BY_KEY[k].kind == "C"]
    mc = [k for k in p.mana if BY_KEY[k].kind == "C"]
    bz = worst_own(s, i)
    if not gc or not mc or bz is None or len(p.mana) - p.mused < a[2] + 1:
        return
    gk = min(gc, key=E.PRI.get)
    mk = min(mc, key=E.PRI.get)
    p.mused += a[2]
    p.hand.remove("k45_alking")
    p.grave.remove(gk)
    s.take_mana(i, mk)
    s.ev(f"進化GV・Ω：不敬合成王 ロマティックダム・アルキング（{a[2]}マナ、墓地・マナ・バトルゾーンから1体ずつ）")
    u = s.enter(i, "k45_alking", "hand", True, on=bz)
    if u is not None:
        u.under.extend([gk, mk])
    else:
        p.grave.append(gk)
        p.mana.append(mk)


add("k45_alking", "不敬合成王 ロマティックダム・アルキング", 9, "LWDFN", power=25000, brk=99,
    evo="gv", races=("newworlddragon", "dispector"), pri=15, roles="fin shd trg acc",
    enter=e_alking, leaverep=rep_alking, shieldout=so_alking, gsok=gs_alking,
    freeacts=fa_alking, actapply={"x:k45_alking": ap_alking},
    playrule=lambda deck, k: None if sum(v for kk, v in deck.items()
                                         if kk != k and BY_KEY[kk].kind == "C") >= 12
    else "進化GV・Ωの元になるクリーチャーが12枚ない",
    text="進化GV・Ω：自分の墓地、マナゾーン、バトルゾーンからクリーチャーを1体ずつ選び、"
         "このクリーチャーをその上に重ねつつ出す。"
         "エクストラEXライフ（このクリーチャーを出す時、自分の山札の上から2枚をシールド化する。"
         "このクリーチャーが離れる時、かわりにそのシールドのうち1つを墓地に置く）。"
         "ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "「EXライフ」シールドが自分のシールドゾーンを離れた時、このクリーチャーの下にあるカードを"
         "1枚、墓地に置く。それが進化ではないクリーチャーなら、自分の墓地から出す。"
         "自分のシールドゾーンにあるディスペクターすべてに「G・ストライク」を与える",
    note="マナゾーンから進化元を1枚取るので、コスト9に加えてマナが1枚余分に必要"
         "（エンジンのマナは枚数でしか数えないため、支払いと進化元の取り合いを避けている）",
    status="partial", source=SRC["k45_alking"])


# ================================================================ 10 聖霊左神ジャスティス
def e_justice(s, i, u):
    """出た時、山札の上から5枚を見て、コスト6以下の呪文1枚をただで唱えてもよい。残りを墓地に置く"""
    top = _top(s, i, 5)
    if not top:
        return
    cands = [k for k in top if BY_KEY[k].kind == "S" and BY_KEY[k].cost <= 6
             and s.spell_ok(i, BY_KEY[k].cost)]
    if cands:
        k = max(cands, key=E.PRI.get)
        top.remove(k)
        s.ev(f"　聖霊左神ジャスティス：{BY_KEY[k].name} をコストを支払わずに唱える")
        s.cast(i, k)
    for k in top:
        if s.over:
            return
        s.grave_put(i, k)


def bx_justice(s, i, u):
    """リンクしている間、シールドをさらに1枚多くブレイクする（W・ブレイカー＋1＝3枚）"""
    if _gl_linked(s, i, u):
        return u.c.brk + 1
    return None


add("k45_justice", "聖霊左神ジャスティス", 7, "", power=8000, brk=2,
    races=("god", "godnova", "angelcommand", "command"), pri=9, roles="acc fin atk",
    enter=e_justice, godlink=("L", ()), brkx=bx_justice,
    freeacts=_gl_acts, actapply={_GL_ACT: _gl_apply},
    text="無色のゴッド・ノヴァ。W・ブレイカー。"
         "このクリーチャーが出た時、自分の山札の上から5枚を見る。その中からコスト6以下の呪文を1枚、"
         "コストを支払わずに唱えてもよい（重要度のいちばん高いものを唱える）。残りを墓地に置く。"
         "左G・リンク（「中央G・リンク」または「右G・リンク」を持つゴッドの左側にリンクしてもよい。"
         "リンクしたゴッドはパワーを合計した1体のクリーチャーになり、能力と文明を併せ持ち、"
         "離れる時はそのうち1枚だけが離れる。つなぐのは自分のメインステップ中の追加の手として行う）。"
         "リンクしている間、このクリーチャーはシールドをさらに1枚ブレイクする（合計3枚）",
    source=SRC["k45_justice"])


# ================================================================ 11 DG 〜裁キノ刻〜
def ap_dg(s, i, u, atk):
    """名前に《DG》とある自分の他のクリーチャーすべてのパワーを+5000する"""
    if u.c.kind != "C" or "DG" not in u.c.name:
        return 0
    return 5000 * sum(1 for z in s.P[i].board if z.k == "k45_dg" and z is not u)


def fx_dg(s, owner, u, i, k, src, summon, res):
    """いずれかのプレイヤーの山札からバトルゾーンにカードが置かれる時、かわりに山札の一番下へ
    （エンジンは「出られない（no）」の時、src が山札なら山札の下に戻す）"""
    if src == "deck":
        return "no"
    return res


def mi_dg(s, i, k, src):
    """いずれかのプレイヤーの山札からマナゾーンにカードが置かれる時、かわりに山札の一番下へ"""
    if src != "deck":
        return
    if not (s.has(0, "k45_dg") or s.has(1, "k45_dg")):
        return
    p = s.P[i]
    if k not in p.mana:
        return
    s.take_mana(i, k)
    p.deck.insert(0, k)
    s.ev(f"　DG 〜裁キノ刻〜：{BY_KEY[k].name} はマナゾーンのかわりに山札の下へ")


add("k45_dg", "DG 〜裁キノ刻〜", 2, "", power=2000, noatk=True, races=("metallica",),
    pri=4, roles="dis",
    aurap=ap_dg, fatex=fx_dg, manain=mi_dg,
    text="無色のメタリカ。このクリーチャーは攻撃できない。"
         "名前に《DG》とある自分の他のクリーチャーすべてのパワーを+5000する。"
         "いずれかのプレイヤーの山札からバトルゾーンまたはマナゾーンにカードが置かれる時、"
         "かわりにそのプレイヤーはそのカードを自身の山札の一番下に置く（両方のプレイヤーに効く）",
    note="マナゾーンぶんは、エンジンに「マナに置かれるのを別のゾーンに置き換える」差し込み口が"
         "墓地送り（manarep）しかないので、`manain=`（マナに置かれた時）でいったん置いてから"
         "山札の下に置き直している。結果は同じだが、「自分のマナから離れた時」の誘発が"
         "1回通ってしまう（REQUEST_45.md に要望を書いた）",
    status="partial", source=SRC["k45_dg"])


# ================================================================ 12 「ちくしょおおおおおおっー!!」
def sp_chikusho(s, i):
    """相手のクリーチャーを1体破壊する。その後、手札をすべて捨てて3枚引いてもよい"""
    t = s.target(i)
    if t is not None:
        s.ev(f"　ちくしょおおおおおおっー!!：{t.c.name} を破壊")
        destroy(s, i, t)
    if s.over:
        return
    p = s.P[i]
    if len(p.hand) <= 2 and len(p.deck) > 3:
        n = len(p.hand)
        for k in list(p.hand):
            if s.over:
                return
            if k in p.hand:
                s.discard(i, k)
        s.ev(f"　ちくしょおおおおおおっー!!：手札{n}枚をすべて捨てて3枚引く")
        s.draw(i, 3)


def lw_chikusho(s, i, u, dest, destroy_):
    """そのターン自分のクリーチャーが破壊されたかを書き留める（手札にこの呪文がある時だけ）"""
    if not destroy_ or u.c.kind != "C":
        return
    if "k45_chikusho" not in s.P[i].hand:
        return
    s.P[i].x["k45_chiku_t"] = s.turn


def tdp_chikusho(s, i):
    """相手のターンの終わりに、条件がそろっていればコストを支払わずに唱える"""
    if s.tp == i:
        return
    p = s.P[i]
    if "k45_chikusho" not in p.hand:
        return
    if p.x.get("k45_chiku_t") != s.turn:
        return
    cv = _civs_in_mana(s, i)
    if "D" not in cv or "F" not in cv:
        return
    if not s.spell_ok(i, 6):
        return
    p.hand.remove("k45_chikusho")
    s.ev("呪文：「ちくしょおおおおおおっー!!」（相手のターンの終わりに、コストを支払わずに）")
    s.cast(i, "k45_chikusho")


add("k45_chikusho", "「ちくしょおおおおおおっー!!」", 6, "DF", kind="S", pri=7, roles="rem draw dis",
    spell=sp_chikusho, leavewatch=lw_chikusho, tendp=tdp_chikusho,
    text="相手のターンの終わりに、そのターン自分のクリーチャーが破壊されていて、"
         "自分のマナゾーンに闇のカードと火のカードがそれぞれ1枚以上あれば、"
         "この呪文をコストを支払わずに唱えてもよい。"
         "相手のクリーチャーを1体選び、破壊する。"
         "その後、自分の手札をすべて捨ててもよい。そうしたら、カードを3枚引く",
    note="手札を捨てて引き直すのは「手札が2枚以下の時」だけにした（引く枚数で損をしないための"
         "全デッキ共通の決まり）",
    source=SRC["k45_chikusho"])


# ================================================================ 13 ヘブンズ・ゲート
def _hg_ok(c):
    return c.kind == "C" and "L" in c.civ and c.blocker and not (c.evo and not c.neo)


def sp_heavensgate(s, i):
    """光の「ブロッカー」を持つ進化ではないクリーチャーを2体まで、自分の手札から出す"""
    n = _put_from_hand(s, i, _hg_ok, 2)
    if not n:
        s.ev("　ヘブンズ・ゲート：出せる光のブロッカーが手札にない")


add("k45_heavensgate", "ヘブンズ・ゲート", 6, "L", kind="S", trig=True, pri=7, roles="trg blk fin",
    spell=sp_heavensgate,
    text="S・トリガー。光の「ブロッカー」を持つ進化ではないクリーチャーを2体まで、自分の手札から出す"
         "（重要度のいちばん高いものから出す）",
    note="カードに書かれた「ブロッカー」を持つクリーチャーだけを出せる。"
         "他のカードから後からブロッカーを与えられるクリーチャーは対象にしていない",
    status="partial", source=SRC["k45_heavensgate"])


# ================================================================ 14 ゴッド・ゲート
def sp_godgate(s, i):
    """山札の上から5枚を見て、コスト9以下のゴッド1体を出す。その後、手札からゴッドを1体ただで召喚"""
    top = _top(s, i, 5)
    got = None
    for k in sorted(top, key=lambda x: -E.PRI[x]):
        c = BY_KEY[k]
        if _god(c) and _plain_cre(c) and c.cost <= 9 and s.fate(i, k, "deck", False) == "ok":
            got = k
            break
    if got is not None:
        top.remove(got)
        s.ev(f"　ゴッド・ゲート：山札から {BY_KEY[got].name} を出す")
    _bottom(s, i, top)
    if got is None:
        return
    s.enter(i, got, "deck", False)
    if s.over:
        return
    base = next((u for u in s.P[i].board if u.k == got), None)
    if base is None:
        return
    # 「そのゴッドにリンクできる」＝G・リンクの位置（左・中央・右）が、いま出したゴッドと重ならないこと。
    # つなげる相手が決まっているゴッド（mates）なら、その組に入っていることも見る。
    pos = {E.GODLINK[z.k][0] for z in s.parts(base) if z.k in E.GODLINK}
    keys = {z.k for z in s.parts(base)}

    def linkable(c):
        g = E.GODLINK.get(c.key)
        if g is None or not _plain_cre(c) or c.key in keys:
            return False
        if g[1] and not any(x in g[1] for x in keys):
            return False
        mates2 = E.GODLINK[base.k][1] if base.k in E.GODLINK else ()
        if mates2 and c.key not in mates2:
            return False
        return bool(pos) and g[0] not in pos

    before = {id(u) for u in s.P[i].board}
    if _put_from_hand(s, i, linkable, 1, summon=True) and base in s.P[i].board:
        # 召喚したゴッドを、そのまま横につなぐ（「リンクできるゴッドを召喚する」呪文なので、
        # 2体のまま離して置いておくとカードの意図から外れる）
        new = next((u for u in s.P[i].board if id(u) not in before and u.k in E.GODLINK), None)
        if new is not None and not new.link and s.can_link(i, new, base):
            s.P[i].board.remove(new)
            if new.tap:
                base.tap = True
            s.god_link(i, new, base)


add("k45_godgate", "ゴッド・ゲート", 6, "W", kind="S", trig=True, pri=7, roles="trg acc fin",
    spell=sp_godgate,
    text="S・トリガー。自分の山札の上から5枚を見る。その中からコスト9以下のゴッド・クリーチャーを"
         "1体出してもよい。残りを好きな順序で山札の下に置く。その後、そのゴッドにリンクできる"
         "ゴッド・クリーチャーを1体、自分の手札からコストを支払わずに召喚してもよい",
    status="full", source=SRC["k45_godgate"])


# ================================================================ 15 ゴッド・シグナル
def sp_godsignal(s, i):
    """自分の山札からゴッド1体を選んで相手に見せ、山札をシャッフルして、その1枚を山札の上に置く"""
    p = s.P[i]
    cands = [k for k in set(p.deck) if _god(BY_KEY[k])]
    if not cands:
        s.ev("　ゴッド・シグナル：山札にゴッドがいない")
        return
    k = max(cands, key=E.PRI.get)
    p.deck.remove(k)
    s.rng.shuffle(p.deck)
    p.deck.append(k)                   # 山札の上（draw は末尾から取る）
    s.ev(f"　ゴッド・シグナル：{BY_KEY[k].name} を山札の一番上に置いた")


add("k45_godsignal", "ゴッド・シグナル", 1, "W", kind="S", trig=True, pri=2, roles="trg acc",
    spell=sp_godsignal,
    text="S・トリガー。自分の山札を見る。その中からゴッドを1体選び、相手に見せてもよい。"
         "その後、山札をシャッフルして、選んだカードを山札の一番上に置く"
         "（重要度のいちばん高いゴッドを選ぶ）",
    source=SRC["k45_godsignal"])
