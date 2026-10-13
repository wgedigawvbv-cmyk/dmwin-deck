"""担当21：DM26-RP1「逆札篇 第1弾 逆転神VS切札竜」の未実装カード15枚（key は k21_）

  調べ方
    dmwiki.net のカード個別ページと、PukiWiki の template プラグインで取れる生の wiki ソース
    （?plugin=template&refer=《カード名》）を、カードごとに別の質問で2回ずつ読み、
    コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が一致することを確かめた。
    超化獣（ハイパーモード）の札は、どの能力がハイパーモードの枠（BGCOLOR の行）に入っているかを
    生ソースと解説文の両方で突き合わせた。

  この15枚に入っている仕組み
    ・超化獣／Zラッシュ（シールドが離れたらハイパーモード）…… ゴッダマ・ルピア、闘龍騎アポロヌス・ドラグーン、
      武神のF オルメガス、王神のO プロディジー。W・ブレイカーや T・ブレイカーがハイパーモード側にある札がある。
    ・G城（kind="G"。表向きのシールドとして置き、表向きのまま離れる時は墓地へ）のサイクル4枚
      （ホワイト・ネオウェーブ／ブルー・ツナミ／ブラック・エクスプロード／レッド・プロミネンス）。
      既実装の《魂が休む庭園 グリーン・グランドクロス》と合わせて5文明ぶんのサイクル。
    ・ウラ・ニンジャ・ストライク（呪遁の化身＝2・自然／雷遁の開眼者ウッズ＝4・光）
    ・シールド送り・山札の下送りによるエレメント除去（ガル・キーン／ウッズ）

  差し込み口の使い方
    ・G城の「表向きでシールドゾーンに置かれた時／離れた時」は `shieldin=` / `shieldout=`（_si_21 / _so_21）。
    ・「自分のターンのはじめに」は `turnstart=`、「カードを引いた時」は `drawwatch=`、
      「相手のクリーチャーがタップした時」は `tapwatch=`、ウラ・ニンジャ・ストライクの
      「ブロックした時」は `blockreact=`。
    ・《呪遁の化身》の「自分のシールドゾーンを離れたカードをマナゾーンに置く」は `shieldrep=`（S・バック）。
      離れるカードのキーに関わらず行き先を変えられるので、ブレイクでも効果でも同じように通る。
    ・シールドを離す時は必ず `s.take_shield` を通す（`p.sh` を直接いじると上の2つが通らない）。

  調べ直して意外だった点
    ・《メタルカオスクラッパー・ドラゴン》はコスト6・パワー5000だが W・ブレイカーを持たない。
    ・《闘龍騎アポロヌス・ドラグーン》の「相手のクリーチャーがタップした時に破壊」は、
      解説文によるとブロックやガードマンで攻撃先を変えた相手を焼くための能力。
    ・《武神のF オルメガス》のハイパーモードは T・ブレイカー（ブレイク3）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all
from envcards.env0 import discard_choice, lock_until_my_turn, owner_of

W = "https://dmwiki.net/"
SRC = {
    "k21_garlie": W + "《電磁麗姫ガルリー》",
    "k21_goddama": W + "《ゴッダマ・ルピア》",
    "k21_inferno": W + "《インフェルノ・ドラグーン》",
    "k21_metalchaos": W + "《メタルカオスクラッパー・ドラゴン》",
    "k21_apollonus": W + "《闘龍騎アポロヌス・ドラグーン》",
    "k21_jyuton": W + "《呪遁の化身》",
    "k21_olmegas": W + "《武神のF オルメガス》",
    "k21_galgatan": W + "《ジェネラル・ガルガタン》",
    "k21_neowave": W + "《創造の天空城 ホワイト・ネオウェーブ》",
    "k21_tsunami": W + "《深き知識の神殿 ブルー・ツナミ》",
    "k21_explode": W + "《覇王の前線基地 ブラック・エクスプロード》",
    "k21_prominence": W + "《燃え尽きぬ館 レッド・プロミネンス》",
    "k21_galkeen": W + "《超電磁工兵ガル・キーン》",
    "k21_woods": W + "《雷遁の開眼者ウッズ》",
    "k21_prodigy": W + "《王神のO プロディジー》",
}


# ================================================================ 共通の小道具
def _castle_n(s, i, key):
    """key の G城が、i の表向きのシールドとして何枚あるか"""
    return sum(1 for k, up in s.P[i].sh if up and k == key)


def _playable_cre(c):
    """コストを支払わずに、進化元なしでバトルゾーンに出せるクリーチャーか"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _summon_cost(s, i, k, av):
    """手札以外から召喚する時のコスト（軽減の差し込み口だけを見る）"""
    n = BY_KEY[k].cost
    f = E.COSTX.get(k)
    if f is not None:
        n = f(s, i, av)
    for g in E.COSTAURA:
        n = g(s, i, k, n)
    return max(0, n)


def _best_hand_cre(s, i, mx):
    """手札のうち、コスト mx 以下でいま出せる、いちばん重要度の高いクリーチャー"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if _playable_cre(c) and c.cost <= mx and E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    return best


def _take_own_shield(s, i, skip=None):
    """自分のシールドを1つ、シールドゾーンから離す（裏向きを上から優先）。
    行き先は手札（表向きのG城だけは、離れる時かわりに墓地に置くという決まりに従う）。
    返り値は (カードのキー, 表向きだったか, 実際の行き先) か None。
    シールドゾーンの出口は s.take_shield の1か所なので、必ずそれを通す
    （p.sh を直接いじると shieldout= / shielddest= が通らなくなる）"""
    p = s.P[i]
    j = None
    for x in range(len(p.sh) - 1, -1, -1):
        if not p.sh[x][1]:
            j = x
            break
    if j is None:
        for x in range(len(p.sh) - 1, -1, -1):
            if p.sh[x][0] != skip:
                j = x
                break
    if j is None:
        return None
    k, up = p.sh[j]
    dest = "grave" if (up and BY_KEY[k].kind == "G") else "hand"
    r = s.take_shield(i, j, dest)
    return None if r is None else (k, up, dest)


# ================================================================ シールドゾーンの出入り・ニンジャの共通部分
def _si_21(s, i, k, up):
    """カードがプレイヤー i のシールドゾーンに置かれた時（表向きだけを見る）"""
    if not up or s.over:
        return
    if k == "k21_neowave":
        s.ev("　ホワイト・ネオウェーブ：表向きでシールドゾーンに置かれた")
        _neowave_fire(s, i)
    elif k == "k21_explode":
        s.ev("　ブラック・エクスプロード：表向きでシールドゾーンに置かれた")
        _explode_revive(s, i)


def _so_21(s, i, k, up, dest):
    """カードがプレイヤー i のシールドゾーンを離れた時（dest＝"break" ならブレイク）"""
    if s.over:
        return
    if up and k == "k21_explode":
        s.ev("　ブラック・エクスプロード：表向きのままシールドゾーンを離れた")
        _explode_revive(s, i)


def _ninja_used(s, di, au):
    """その攻撃中に、この担当のニンジャ能力をもう使ったか"""
    return s.P[di].x.get("k21_ninja") == (s.turn, au.uid)


def _ninja_mark(s, di, au):
    s.P[di].x["k21_ninja"] = (s.turn, au.uid)


# ================================================================ 電磁麗姫ガルリー
def e_garlie(s, i, u):
    """出た時または攻撃する時：相手のクリーチャー1体を、次の自分のターンのはじめまで止める"""
    t = s.target(i)
    if t is None:
        return
    lock_until_my_turn(s, i, t)
    s.ev(f"　電磁麗姫ガルリー：{t.c.name} は次の自分のターンのはじめまで攻撃もブロックもできない")


add("k21_garlie", "電磁麗姫ガルリー", 2, "W", power=1000, races=("splashqueen", "cyberlord"),
    trig=True, jd=True, pri=3, roles="dis trg rem",
    enter=e_garlie, attack=e_garlie,
    text="S・トリガー。ジャストダイバー（出た時、次の自分のターンのはじめまで相手に選ばれず攻撃されない）。"
         "出た時または攻撃する時、相手のクリーチャー1体を選び、次の自分のターンのはじめまで"
         "攻撃もブロックもできなくする",
    source=SRC["k21_garlie"])


# ================================================================ ゴッダマ・ルピア
def e_goddama(s, i, u):
    """出た時：自分のシールド1つを手札に加えてもよい（S・トリガーは使えない）。そうしたら山札の上3枚を墓地へ"""
    p = s.P[i]
    if len(p.sh) < 2:                      # シールドが最後の1つしかない時は回収しない
        return
    x = _take_own_shield(s, i, skip="k21_goddama")
    if x is None:
        return
    k, up, dest = x
    s.ev(f"　ゴッダマ・ルピア：シールドを1つ回収（{BY_KEY[k].name}。S・トリガーは使えない）→ 山札の上3枚を墓地へ")
    s.mill(i, 3)


def rep_goddama(s, i, u, dest, dsy):
    """ハイパーモード：各ターン1度、自分のクリーチャーが破壊される時、
    かわりに墓地のカード3枚を山札の下に置く（そのクリーチャーは破壊されない）"""
    if not dsy or u.c.kind != "C":
        return False
    p = s.P[i]
    for z in p.board:
        if z.k != "k21_goddama" or not z.hyper or z.x.get("k21_god") == s.turn:
            continue
        if len(p.grave) < 3:
            continue
        z.x["k21_god"] = s.turn
        for k in sorted(p.grave, key=E.PRI.get)[:3]:
            p.grave.remove(k)
            p.deck.insert(0, k)
        s.ev(f"　ゴッダマ・ルピア：墓地3枚を山札の下に置き、{u.c.name} は破壊されない")
        return True
    return False


E.HYPER_POW["k21_goddama"] = 3000          # ハイパーモード 6000／W・ブレイカー

add("k21_goddama", "ゴッダマ・ルピア", 3, "D", power=3000, races=("firebird", "hyperbeast"),
    zrush=True, pri=5, roles="draw atk",
    enter=e_goddama, leaverep=rep_goddama,
    text="出た時、自分のシールドを1つ手札に加えてもよい（そのS・トリガーは使えない）。"
         "そうしたら、自分の山札の上から3枚を墓地に置く。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー6000でW・ブレイカーを持ち、各ターン1度、自分のクリーチャーが破壊される時、"
         "かわりに自分の墓地のカード3枚を山札の下に置いてよい",
    source=SRC["k21_goddama"])


# ================================================================ インフェルノ・ドラグーン
def e_inferno(s, i, u):
    """出た時：自分の山札の上から3枚を墓地に置く"""
    s.mill(i, 3)


def d_inferno(s, i, u):
    """破壊された時：このカードを墓地から山札の下に置いてもよい。
    そうしたら、コスト5以下の超化獣クリーチャー1体を自分の墓地から出す"""
    p = s.P[i]
    if "k21_inferno" not in p.grave:
        return
    ok = any(k != "k21_inferno" and _playable_cre(BY_KEY[k]) and BY_KEY[k].cost <= 5
             and "hyperbeast" in BY_KEY[k].races and not BY_KEY[k].evo for k in p.grave)
    if not ok:                             # 出せる超化獣がいないなら、山札の下に置かない（任意）
        return
    p.grave.remove("k21_inferno")
    p.deck.insert(0, "k21_inferno")
    s.ev("　インフェルノ・ドラグーン：自身を山札の下に置き、墓地から超化獣を出す")
    s.revive(i, lambda c: c.cost <= 5 and "hyperbeast" in c.races)


add("k21_inferno", "インフェルノ・ドラグーン", 3, "D", power=1000, races=("tyranodrake",),
    trig=True, blocker=True, pri=4, roles="blk trg",
    enter=e_inferno, destroyed=d_inferno,
    text="S・トリガー。ブロッカー。出た時、自分の山札の上から3枚を墓地に置く。"
         "破壊された時、このカードを墓地から自分の山札の下に置いてもよい。"
         "そうしたら、コスト5以下の超化獣クリーチャー1体を自分の墓地から出す",
    source=SRC["k21_inferno"])


# ================================================================ メタルカオスクラッパー・ドラゴン
def e_metalchaos(s, i, u):
    """出た時：手札を1枚捨ててもよい。そうしたら、その捨てた札よりコストの小さい相手のエレメント1つを破壊する"""
    p = s.P[i]
    best, bk = None, None
    for k in sorted(set(p.hand)):
        t = s.target(i, lambda z, kk=k: z.c.cost < BY_KEY[kk].cost, kinds="CTX")
        if t is None:
            continue
        sc = (s.val(t), -E.PRI[k])
        if best is None or sc > best:
            best, bk = sc, k
    if bk is None:
        return
    if bk in p.hand:
        s.discard(i, bk)
    t = s.target(i, lambda z: z.c.cost < BY_KEY[bk].cost, kinds="CTX")
    if t is None:
        return
    s.ev(f"　メタルカオスクラッパー・ドラゴン：{BY_KEY[bk].name} を捨てて {t.c.name} を破壊")
    destroy(s, i, t)


def a_metalchaos(s, i, u):
    """攻撃する時：パワーの合計が5000以下になるように相手のクリーチャーを好きな数選び、破壊してもよい"""
    cs = sorted(opp_all(s, i), key=lambda z: (-s.val(z), s.power(1 - i, z)))
    tot, pick = 0, []
    for z in cs:
        pw = max(0, s.power(1 - i, z))
        if tot + pw <= 5000:
            tot += pw
            pick.append(z)
    for z in pick:
        if z in s.P[1 - i].board:
            s.ev(f"　メタルカオスクラッパー・ドラゴン：{z.c.name} を破壊（合計{tot}まで）")
            destroy(s, i, z)


add("k21_metalchaos", "メタルカオスクラッパー・ドラゴン", 6, "F", power=5000, races=("armoreddragon",),
    trig=True, pri=8, roles="rem trg atk",
    enter=e_metalchaos, attack=a_metalchaos,
    text="S・トリガー。出た時、自分の手札を1枚捨ててもよい。そうしたら、捨てたカードよりコストが小さい"
         "相手のエレメント1つを選んで破壊する。攻撃する時、パワーの合計が5000以下になるように"
         "相手のクリーチャーを好きな数選び、破壊してもよい",
    source=SRC["k21_metalchaos"])


# ================================================================ 闘龍騎アポロヌス・ドラグーン
def tw_apollonus(s, i, u):
    """自分のターンに相手のクリーチャーがタップした時、そのクリーチャーを破壊する
    （i＝タップしたクリーチャーの持ち主。アポロヌスはその相手側にいる）"""
    o = 1 - i
    if u.c.kind != "C" or s.tp != o or not s.has(o, "k21_apollonus"):
        return
    if s.over or u not in s.P[i].board:
        return
    s.ev(f"　闘龍騎アポロヌス・ドラグーン：タップした {u.c.name} を破壊")
    destroy(s, o, u)


def te_apollonus(s, i, u):
    """ハイパーモード：自分のターンの終わりに、これがタップしていれば、
    相手のアンタップしているコスト4以下のクリーチャーをすべて破壊する"""
    if u.k != "k21_apollonus":
        return
    if s.tp != i or not u.hyper or not u.tap:
        return
    for z in list(s.P[1 - i].board):
        if z.c.kind == "C" and not z.tap and z.c.cost <= 4 and z in s.P[1 - i].board:
            s.ev(f"　闘龍騎アポロヌス・ドラグーン：アンタップしている {z.c.name} を破壊")
            destroy(s, i, z)


E.HYPER_POW["k21_apollonus"] = 6000       # ハイパーモード 10000／W・ブレイカー

add("k21_apollonus", "闘龍騎アポロヌス・ドラグーン", 4, "F", power=4000,
    races=("armoreddragon", "tyranodrake", "hyperbeast"), sa=True, zrush=True, pri=8, roles="rem atk fin",
    tapwatch=tw_apollonus, tendall=te_apollonus,
    text="スピードアタッカー。自分のターンに相手のクリーチャーがタップした時、そのクリーチャーを破壊する"
         "（ブロックしたクリーチャーもタップするので、バトルの前に破壊される）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー10000でW・ブレイカーを持ち、自分のターンの終わりにこのクリーチャーが"
         "タップしていれば、相手のアンタップしているコスト4以下のクリーチャーをすべて破壊する",
    source=SRC["k21_apollonus"])


# ================================================================ 呪遁の化身
def react_jyuton(s, di, au):
    """ウラ・ニンジャ・ストライク2（自然）：相手の攻撃に反応して、手札からただで召喚する"""
    d = s.P[di]
    if "k21_jyuton" not in d.hand or len(d.mana) < 2:
        return False
    if "N" not in E.civs(d) or _ninja_used(s, di, au):
        return False
    if s.fate(di, "k21_jyuton", "hand", True) != "ok":
        return False
    d.hand.remove("k21_jyuton")
    u = s.enter(di, "k21_jyuton", "hand", True)
    if u is None:
        return False
    u.eot = True                           # そのターンの終わりに山札の下へ
    s.trig[di] += 1
    _ninja_mark(s, di, au)
    s.ev("　ウラ・ニンジャ・ストライク2：呪遁の化身")
    return True


def block_jyuton(s, di, au, b):
    """ブロックした時のウラ・ニンジャ・ストライク2（自然）"""
    return react_jyuton(s, di, au)


def _sr_jyuton(s, i, k, up, dest):
    """カードが自分のシールドゾーンから手札または墓地に置かれる時、かわりにマナゾーンに置いてもよい。

    S・バックの差し込み口（shieldrep=）で、離れるカードのキーに関係なく行き先を変える。
    ブレイクでも効果でも、またEXライフのシールドが墓地に行く時も同じように通る。
    受けになる札（S・トリガー・G・ストライク・ツインパクトのS・トリガー）は、
    そのまま手札に加えて使えるようにするほうが得なので置き換えない（全デッキ共通の決まり）"""
    if dest not in ("hand", "grave") or not s.has(i, "k21_jyuton"):
        return None
    c = BY_KEY[k]
    if dest == "hand" and (c.trig or c.gs or (c.twin and c.twin[2])):
        return None
    s.ev(f"　呪遁の化身：{c.name} をシールドゾーンからマナゾーンに置く")
    return "mana"


add("k21_jyuton", "呪遁の化身", 5, "N", power=9000, brk=2, races=("mysterytotem", "origin", "shinobi"),
    mach=True, pri=7, roles="rem acc blk",
    react=react_jyuton, blockreact=block_jyuton,
    shieldrep=_sr_jyuton, status="full",
    text="ウラ・ニンジャ・ストライク2（自然）（相手のクリーチャーが攻撃またはブロックした時、自分のマナに"
         "カードが2枚以上で自然文明があり、その攻撃中にニンジャ・ストライクを使っていなければ、"
         "コストを支払わずに召喚してよい。そのターンの終わりに山札の下に置く）。"
         "マッハファイター。W・ブレイカー。"
         "カードが自分のシールドゾーンから手札または墓地に置かれた時、そのカードをマナゾーンに置いてもよい"
         "（受けになるS・トリガー・G・ストライクの札だけは手札に加えて使う）",
    source=SRC["k21_jyuton"])


# ================================================================ 武神のF オルメガス
def bl_olmegas(s, u):
    """オルメガスは、オルメガスよりパワーの小さいクリーチャーにブロックされない"""
    a = s.atk
    if a is None or a.k != "k21_olmegas" or u.c.kind != "C":
        return False
    ai = owner_of(s, a)
    return s.power(owner_of(s, u), u) < s.power(ai, a, True)


def te_olmegas(s, i, u):
    """ハイパーモード：自分のターンの終わりに、自分のクリーチャーのパワーが一番大きければ2枚引く"""
    if u.k != "k21_olmegas" or s.tp != i or not u.hyper:
        return
    mine = max((s.power(i, z) for z in s.P[i].board if z.c.kind == "C"), default=-1)
    opp = max((s.power(1 - i, z) for z in s.P[1 - i].board if z.c.kind == "C"), default=-1)
    if mine > opp:
        s.ev("　武神のF オルメガス：自分のクリーチャーのパワーが一番大きい → 2枚引く")
        s.draw(i, 2)


add("k21_olmegas", "武神のF オルメガス", 4, "N", power=4000, races=("god", "hyperbeast"),
    mach=True, zrush=True, pri=7, roles="atk draw fin",
    powerx=lambda s, i, u, atk: 8000 if u.hyper else 0,
    brkx=lambda s, i, u: 3 if u.hyper else None,
    blocklock=bl_olmegas, tendall=te_olmegas,
    text="マッハファイター。このクリーチャーは、このクリーチャーよりパワーが小さいクリーチャーに"
         "ブロックされない。Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー12000でT・ブレイカーを持ち、自分のターンの終わりに、"
         "自分のクリーチャーのパワーが一番大きければ2枚引く",
    source=SRC["k21_olmegas"])


# ================================================================ ジェネラル・ガルガタン
def e_galgatan(s, i, u):
    """出た時：マナからコスト2以下のクリーチャーを出してもよい。その後、
    自分のクリーチャーの数以下のコストの相手のクリーチャー1体を、持ち主のマナゾーンに置いてもよい"""
    s.revive(i, lambda c: c.cost <= 2, src="mana")
    t = s.target(i, lambda z: z.c.cost <= s.ncre(i))
    if t is None:
        return
    s.ev(f"　ジェネラル・ガルガタン：{t.c.name} を持ち主のマナゾーンへ")
    move(s, i, t, "mana")


add("k21_galgatan", "ジェネラル・ガルガタン", 3, "N", power=3000, races=("dreammate", "vehiclebee"),
    trig=True, pri=5, roles="acc rem trg",
    enter=e_galgatan,
    text="S・トリガー。出た時、コスト2以下のクリーチャー1体を自分のマナゾーンから出してもよい。"
         "その後、自分のクリーチャーの数以下のコストを持つ相手のクリーチャー1体を選び、"
         "持ち主のマナゾーンに置いてもよい",
    source=SRC["k21_galgatan"])


# ================================================================ 創造の天空城 ホワイト・ネオウェーブ
def _neowave_fire(s, i):
    """1枚引き、その後コスト4以下のクリーチャー1体を手札から出してもよい"""
    p = s.P[i]
    s.draw(i)
    if s.over:
        return
    k = _best_hand_cre(s, i, 4)
    if k is not None and k in p.hand:
        p.hand.remove(k)
        s.ev(f"　ホワイト・ネオウェーブ：手札から {BY_KEY[k].name} を出す")
        s.enter(i, k, "hand", False)


def ts_neowave(s, i):
    """自分のターンのはじめに（バトルゾーンが空でも呼ばれる差し込み口）"""
    for _ in range(_castle_n(s, i, "k21_neowave")):
        if s.over:
            return
        s.ev("　ホワイト・ネオウェーブ：自分のターンのはじめ")
        _neowave_fire(s, i)


add("k21_neowave", "創造の天空城 ホワイト・ネオウェーブ", 5, "LW", kind="G", pri=7, roles="draw atk acc",
    shieldin=_si_21, turnstart=ts_neowave,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地へ）。"
         "このG城が表向きで自分のシールドゾーンに置かれた時、または自分のターンのはじめに、1枚引く。"
         "その後、コスト4以下のクリーチャー1体を自分の手札から出してもよい",
    source=SRC["k21_neowave"])


# ================================================================ 深き知識の神殿 ブルー・ツナミ
_TSU = [False]        # 捨てる処理の中でまた引いた時に入れ子にならないようにする安全装置


def dw_tsunami(s, i, k):
    """自分のターンに自分がカードを引いた時、相手は自身の手札を1枚選んで捨てる"""
    if s.tp != i or s.over or _TSU[0]:
        return
    n = _castle_n(s, i, "k21_tsunami")
    if n <= 0:
        return
    _TSU[0] = True
    try:
        for _ in range(n):
            if s.over or not s.P[1 - i].hand:
                break
            s.ev("　ブルー・ツナミ：相手は自身の手札を1枚選んで捨てる")
            discard_choice(s, 1 - i)
    finally:
        _TSU[0] = False


def aw_tsunami(s, i, u):
    """各ターン、はじめて自分のクリーチャーが攻撃する時、1枚引いてもよい"""
    if s.tp != i or u.c.kind != "C":
        return
    p = s.P[i]
    n = _castle_n(s, i, "k21_tsunami")
    if n <= 0 or p.x.get("k21_tsu_a") == s.turn:
        return
    p.x["k21_tsu_a"] = s.turn
    s.ev("　ブルー・ツナミ：このターンはじめての攻撃 → 1枚引く")
    s.draw(i, n)


add("k21_tsunami", "深き知識の神殿 ブルー・ツナミ", 4, "WD", kind="G", pri=5, roles="dis draw",
    atkwatch=aw_tsunami, drawwatch=dw_tsunami,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地へ）。"
         "自分のターンに自分がカードを引いた時、相手は自身の手札を1枚選んで捨てる。"
         "各ターン、はじめて自分のクリーチャーが攻撃する時、1枚引いてもよい",
    source=SRC["k21_tsunami"])


# ================================================================ 覇王の前線基地 ブラック・エクスプロード
def _explode_revive(s, i):
    s.revive(i, lambda c: c.cost <= 3)


def _sa_target(s, i):
    """スピードアタッカーをもらって得をする自分のクリーチャー（出たターンでアンタップ、まだ攻撃できないもの）"""
    best, bv = None, -1
    for z in s.P[i].board:
        if z.c.kind != "C" or z.tap or z.c.noatk or not z.sick:
            continue
        if z.sa or z.c.sa or z.c.mach:
            continue
        if s.val(z) > bv:
            best, bv = z, s.val(z)
    return best


def w_explode(s, i, u):
    """各ターンに1度、自分のクリーチャーが出た時、そのクリーチャーは自分の他のシールドを1つブレイクしてもよい。
    そうしたら、このターン、自分のクリーチャー1体にスピードアタッカーを与える"""
    if u.c.kind != "C" or s.over:
        return
    p = s.P[i]
    if _castle_n(s, i, "k21_explode") <= 0 or p.x.get("k21_exp_t") == s.turn:
        return
    if len(p.sh) < 2 or _sa_target(s, i) is None:
        return
    p.x["k21_exp_t"] = s.turn
    x = _take_own_shield(s, i, skip="k21_explode")
    if x is None:
        return
    k, up, dest = x
    s.ev(f"　ブラック・エクスプロード：{u.c.name} が自分のシールドを1つブレイク（{BY_KEY[k].name}）")
    if not up and dest == "hand" and k in p.hand:
        s.trigger(i, k)
    t = _sa_target(s, i)
    if t is not None:
        t.sa = True
        s.ev(f"　ブラック・エクスプロード：{t.c.name} にスピードアタッカー")


add("k21_explode", "覇王の前線基地 ブラック・エクスプロード", 4, "DF", kind="G", pri=6, roles="atk fin",
    shieldin=_si_21, shieldout=_so_21, enterwatch=w_explode,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地へ）。"
         "このG城が表向きで自分のシールドゾーンに置かれた時または離れた時、"
         "コスト3以下のクリーチャー1体を自分の墓地から出してもよい。"
         "各ターンに1度、自分のクリーチャーが出た時、そのクリーチャーは自分の他のシールドを1つ"
         "ブレイクしてもよい。そうしたら、このターン、自分のクリーチャー1体にスピードアタッカーを与える",
    source=SRC["k21_explode"])


# ================================================================ 燃え尽きぬ館 レッド・プロミネンス
def acts_prominence(s, i, av, cv):
    p = s.P[i]
    if _castle_n(s, i, "k21_prominence") <= 0 or p.x.get("k21_pr") == s.turn:
        return []
    out = []
    for k in sorted(set(p.mana)):
        c = BY_KEY[k]
        if not _playable_cre(c):
            continue
        n = _summon_cost(s, i, k, av)
        if n > av - 1:                     # 召喚するカード自身はコストに使えない
            continue
        rest = list(p.mana)
        rest.remove(k)
        cv2 = set("".join(E.MCIV[x] for x in rest))
        if (n == 0 or cv2.issuperset(c.civ)) and s.fate(i, k, "mana", True) == "ok":
            out.append(("x:k21prom", k, n))
    return out


def ap_prominence(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if k not in p.mana or p.x.get("k21_pr") == s.turn:
        return
    p.x["k21_pr"] = s.turn
    p.mused += a[2]
    s.take_mana(i, k)
    s.ev(f"　レッド・プロミネンス：マナゾーンから {BY_KEY[k].name} を召喚（{a[2]}マナ）")
    s.enter(i, k, "mana", True)
    s.ramp(i, 1, tapped=True)


def w_prominence(s, i, u):
    """自分のクリーチャーがマナゾーンから出た時、相手のクリーチャー1体を選んでもよい。その2体をバトルさせる
    （どこから出たかは u.x["src"] で分かる）"""
    p = s.P[i]
    if u.c.kind != "C" or u.x.get("src") != "mana" or u not in p.board:
        return
    if _castle_n(s, i, "k21_prominence") <= 0:
        return
    t = s.target(i, lambda z: z.k != "kuzen" and s.power(1 - i, z) < s.power(i, u))
    if t is None:
        return
    s.ev(f"　レッド・プロミネンス：{u.c.name} と {t.c.name} をバトル")
    s.battle(i, u, 1 - i, t)


add("k21_prominence", "燃え尽きぬ館 レッド・プロミネンス", 3, "FN", kind="G", pri=5, roles="acc rem atk",
    freeacts=acts_prominence, actapply={"x:k21prom": ap_prominence},
    enterwatch=w_prominence,
    text="G城（唱えるかわりに表向きのシールドとして置く。表向きのままシールドゾーンを離れる時は墓地へ）。"
         "各ターン、クリーチャー1体を自分のマナゾーンから召喚してもよい（コストは支払う）。"
         "そうしたら、自分の山札の上から1枚をタップしてマナゾーンに置いてもよい。"
         "自分のクリーチャーがマナゾーンから出た時、相手のクリーチャー1体を選んでもよい。その2体をバトルさせる"
         "（マナゾーンから召喚する時のコストには、召喚するカード自身は使えない）",
    source=SRC["k21_prominence"])


# ================================================================ 超電磁工兵ガル・キーン
def e_galkeen(s, i, u):
    """出た時：相手のエレメント1つを選び、持ち主のシールドゾーンに置いてもよい"""
    t = s.target(i, kinds="CTX")
    if t is None:
        return
    s.ev(f"　超電磁工兵ガル・キーン：{t.c.name} を持ち主のシールドゾーンへ")
    move(s, i, t, "shield")


add("k21_galkeen", "超電磁工兵ガル・キーン", 5, "L", power=5000, races=("greatmechaoh",),
    trig=True, pri=6, roles="rem trg",
    enter=e_galkeen,
    text="S・トリガー。出た時、相手のエレメント1つを選び、持ち主のシールドゾーンに置いてもよい（シールド化）",
    source=SRC["k21_galkeen"])


# ================================================================ 雷遁の開眼者ウッズ
def react_woods(s, di, au):
    """ウラ・ニンジャ・ストライク4（光）"""
    d = s.P[di]
    if "k21_woods" not in d.hand or len(d.mana) < 4:
        return False
    if "L" not in E.civs(d) or _ninja_used(s, di, au):
        return False
    if s.fate(di, "k21_woods", "hand", True) != "ok":
        return False
    d.hand.remove("k21_woods")
    u = s.enter(di, "k21_woods", "hand", True)
    if u is None:
        return False
    u.eot = True
    s.trig[di] += 1
    _ninja_mark(s, di, au)
    s.ev("　ウラ・ニンジャ・ストライク4：雷遁の開眼者ウッズ")
    return True


def block_woods(s, di, au, b):
    """ブロックした時のウラ・ニンジャ・ストライク4（光）"""
    return react_woods(s, di, au)


def e_woods(s, i, u):
    """出た時：相手のマナゾーンの枚数よりコストが大きい相手のエレメント1つを、持ち主の山札の下に置く"""
    n = len(s.P[1 - i].mana)
    t = s.target(i, lambda z: z.c.cost > n, kinds="CTX")
    if t is None:
        return
    s.ev(f"　雷遁の開眼者ウッズ：{t.c.name} を持ち主の山札の下へ")
    move(s, i, t, "deck")


add("k21_woods", "雷遁の開眼者ウッズ", 3, "L", power=2500, races=("mechathunder", "origin", "shinobi"),
    pri=5, roles="rem dis",
    react=react_woods, blockreact=block_woods, enter=e_woods,
    text="ウラ・ニンジャ・ストライク4（光）（相手のクリーチャーが攻撃またはブロックした時、自分のマナに"
         "カードが4枚以上で光文明があり、その攻撃中にニンジャ・ストライクを使っていなければ、"
         "コストを支払わずに召喚してよい。そのターンの終わりに山札の下に置く）。"
         "出た時、相手のマナゾーンにあるカードの枚数よりコストが大きい相手のエレメント1つを選び、"
         "持ち主の山札の下に置く",
    source=SRC["k21_woods"])


# ================================================================ 王神のO プロディジー
def bo_prodigy(s, u):
    """ハイパーモード中のプロディジーは、自分の他のクリーチャーすべてにブロッカーを与える"""
    if u.c.kind != "C" or u.k == "k21_prodigy":
        return False
    i = owner_of(s, u)
    return any(z.k == "k21_prodigy" and z.hyper for z in s.P[i].board)


def te_prodigy(s, i, u):
    """ハイパーモード：自分のターンの終わりに、自分の他のクリーチャーをアンタップする"""
    if u.k != "k21_prodigy" or s.tp != i or not u.hyper:
        return
    for z in s.P[i].board:
        if z is not u and z.c.kind == "C" and z.tap:
            z.tap = False
    s.ev("　王神のO プロディジー：自分の他のクリーチャーをアンタップ")


E.HYPER_POW["k21_prodigy"] = 4000          # ハイパーモード 6500／W・ブレイカー

add("k21_prodigy", "王神のO プロディジー", 2, "L", power=2500, races=("god", "hyperbeast"),
    blocker=True, zrush=True, pri=5, roles="blk dis fin",
    blockok=bo_prodigy, tendall=te_prodigy,
    text="ブロッカー。Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモードになる）。"
         "ハイパーモード中はパワー6500でW・ブレイカーを持ち、自分の他のクリーチャーすべてにブロッカーを与え、"
         "それらを自分のターンの終わりにアンタップする",
    source=SRC["k21_prodigy"])
