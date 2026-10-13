"""担当39：DM26-EX1「ますますつよいパック 25の援軍」の再録カード15枚（key は k39_）

出典：dmwiki.net の各カードページ（1枚ごとに別の質問で2回読み、cardtable 行の
      コスト・文明・種類・種族・パワーと、能力本文がどちらも一致することを確かめた）。
      本文が切れる札は生の wiki ソース（?plugin=template&refer=…）も読んで突き合わせた。

  この札束に入っている仕組み
    ・シンパシー［相手のマナゾーンにあるカード］（十四番龍 アクロスラピュタズ Par青天井）
      ……ふつうのシンパシーと逆で、**相手の**マナが多いほど安くなる
    ・フシギバース［自然(13)］（ブラキオ龍樹）＝自分のクリーチャーをタップしてマナに置き、
      差額を払って墓地から召喚する
    ・進化V（超聖竜シデン・ギャラクシー／戦極竜ヴァルキリアス・ムサシ）＝クリーチャー2体を重ねる
    ・究極進化MAX（超神羅ギャラクシー・デスティニー）＝究極進化クリーチャーの上にしか置けない
    ・メテオバーン（シデン・ギャラクシー）＝下のカードを墓地に置いて、種族ごとに別の効果
    ・スマッシュ・バースト（水晶の記録 ゼノシャーク）＝攻撃する時に呪文側をただで唱える
    ・ハイパー化／ハイパーモード（超光喜 エルボロム）
    ・EXライフ＋「タップした時にアンタップ」＋特殊勝利（頂上電融 ジョルト・ザ・ジョクスト4th）

  調べ直して意外だった点（最後の返答にも書いた）
    ・《呪烏竜 ACE-Curase／繁栄の鏡》は、クリーチャー側が水/闇のコスト15なのに
      呪文側《繁栄の鏡》が**自然**のコスト4。出た時の効果が「手札をすべて超次元ゾーンへ」で、
      このシミュレーターに超次元ゾーンが無いので、そこだけ近似した。
    ・《十四番龍 アクロスラピュタズ Par青天井》のシンパシーは**相手の**マナを数える。
    ・《翼速 ザ・ウイング》の「自分のクリーチャーがタップした時に1枚引く」には回数制限が無い。
    ・《超神羅ギャラクシー・デスティニー》の種族は「ガイア・コマンド/ルナーズ・サンガイザー」と
      書かれていた（3回読んで同じ。見慣れない種族名だが、ほかのカードと組み合わないので影響はない）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add
from envcards.env0 import exlife_enter, exlife_rep, own_loss

W = "https://dmwiki.net/"
SRC = {
    "k39_across": W + "《十四番龍 アクロスラピュタズ Par青天井》",
    "k39_brachio": W + "《ブラキオ龍樹》",
    "k39_obee": W + "《十番龍 オービーメイカー Par100》",
    "k39_shiden": W + "《超聖竜シデン・ギャラクシー》",
    "k39_curase": W + "《呪烏竜 ACE-Curase／繁栄の鏡》",
    "k39_jolt": W + "《頂上電融 ジョルト・ザ・ジョクスト4th》",
    "k39_nine": W + "《偽りの王 ナンバーナイン／歓喜の歌》",
    "k39_wing": W + "《翼速 ザ・ウイング》",
    "k39_xeno": W + "《水晶の記録 ゼノシャーク／クリスタル・メモリー》",
    "k39_jigus": W + "《堕魔 ジグス★ガルビ》",
    "k39_musashi": W + "《戦極竜ヴァルキリアス・ムサシ》",
    "k39_destiny": W + "《超神羅ギャラクシー・デスティニー》",
    "k39_jin": W + "《若頭 鬼流院 刃》",
    "k39_spellblue": W + "《アクア・スペルブルー／インビンシブル・オーラ》",
    "k39_elborom": W + "《超光喜 エルボロム》",
}


# ================================================================ 共通の小道具
def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので出せない）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _element_card(c):
    """マナゾーンから出せるエレメントのカードか（呪文はエレメントではない）"""
    if c.kind == "C":
        return _playable_cre(c)
    return c.kind in ("T", "G", "X")


def _mana_to_field(s, j, k):
    """プレイヤー j のマナゾーンのエレメント1枚をバトルゾーンに出す（アクロスラピュタズの入れ替え用）"""
    c = BY_KEY[k]
    if k not in s.P[j].mana:
        return False
    if c.kind == "C":
        if s.fate(j, k, "mana", False) != "ok":
            return False
        s.take_mana(j, k)
        s.enter(j, k, "mana", False)
    elif c.kind == "T":
        s.take_mana(j, k)
        s.place_tama(j, k)
    elif c.kind == "G":
        s.take_mana(j, k)
        s.place_castle(j, k)
    elif c.kind == "X":
        s.take_mana(j, k)
        u = E.U(k)
        u.sick = False
        s.P[j].board.append(u)
        fn = E.ENTER.get(k)
        if fn is not None:
            fn(s, j, u)
    else:
        return False
    return True


def _ultimate(c):
    """究極進化クリーチャーか（このシミュレーターに「究極進化」の印が無いので、
    カードの説明文に「究極進化」と書かれた進化クリーチャーで判定する。
    自分と同じ「究極進化MAX」のカードは進化元にできないので外す）"""
    if c.kind != "C" or not c.evo:
        return False
    n = c.note or ""
    return "究極進化" in n and "究極進化MAX" not in n


def _st_spell_cost(k):
    """「S・トリガー」を持つ呪文か（ツインパクトの呪文側も見る）。唱えるコストか None を返す"""
    c = BY_KEY[k]
    if c.kind == "S" and c.trig:
        return c.cost, False
    if c.twin and c.twin[2]:
        return c.twin[0], True
    return None


# ================================================================ 1 十四番龍 アクロスラピュタズ Par青天井
def cx_across(s, i, av):
    """シンパシー［相手のマナゾーンにあるカード］：相手のマナ1枚につき1少なくする（0以下にならない）"""
    return max(1, 14 - len(s.P[1 - i].mana))


def at_across(s, i, u):
    """攻撃する時、バトルゾーンのエレメント1つと、その持ち主のマナゾーンにある、それよりコストが
    小さいエレメント1つを選んでもよい。持ち主はそれらを入れ替える

    どれを選ぶかは全デッキ共通の決まり：相手のいちばん重要なエレメントをマナへ送り、
    かわりに相手のマナにあるいちばん安いエレメントをバトルゾーンへ出す
    （自分側に使うと必ず損になるので、相手だけを選ぶ）。"""
    o = s.P[1 - i]
    t = s.target(i, kinds="CTGX")
    if t is None:
        return
    cands = [k for k in o.mana if _element_card(BY_KEY[k]) and BY_KEY[k].cost < t.c.cost]
    if not cands:
        return
    k = min(cands, key=E.PRI.get)
    if not s.leave(1 - i, t, "mana", by_opp=True):
        return
    s.ev(f"　アクロスラピュタズ：{t.c.name} をマナへ、かわりにマナの {BY_KEY[k].name} をバトルゾーンへ")
    _mana_to_field(s, 1 - i, k)


add("k39_across", "十四番龍 アクロスラピュタズ Par青天井", 14, "N", power=19000, brk=4, mach=True,
    races=("giantdragon", "giant", "dragon"), pri=13, roles="rem fin atk",
    costx=cx_across, attack=at_across,
    text="シンパシー［相手のマナゾーンにあるカード］（このクリーチャーの召喚コストを、"
         "相手のマナゾーンにあるカード1枚につき1少なくする。ただし0以下にはならない）。"
         "マッハファイター（出たターンに相手のクリーチャーを攻撃できる）。Q・ブレイカー。"
         "このクリーチャーが攻撃する時、バトルゾーンにあるエレメントを1つと、その持ち主のマナゾーンにある、"
         "それよりコストが小さいエレメントを1つ選んでもよい。選ばれたエレメントの持ち主は、それらを入れ替える"
         "（相手のいちばん重要なエレメントをマナへ、相手のマナのいちばん安いエレメントをバトルゾーンへ）",
    source=SRC["k39_across"])


# ================================================================ 2 ブラキオ龍樹
def _fushigi_opt(s, i):
    """フシギバース［自然(13)］：マナに置くクリーチャーと、支払うコストの組（なければ None）

    13 からそのクリーチャーのコストを引いた数を払う（自然1より少なくならない）。
    払える中で、失うのがいちばん安いクリーチャーを選ぶ（全デッキ共通の決まり）。"""
    p = s.P[i]
    av = len(p.mana) - p.mused
    best, bv = None, None
    for z in p.board:
        if z.c.kind != "C" or z.tap:
            continue
        n = max(1, 13 - z.c.cost)
        if n > av:
            continue
        v = (own_loss(s, i, z), n)
        if bv is None or v < bv:
            best, bv = (z, n), v
    return best


def fa_brachio(s, i, av, cv):
    p = s.P[i]
    if "k39_brachio" not in p.grave or "N" not in cv:
        return []
    o = _fushigi_opt(s, i)
    if o is None:
        return []
    if s.fate(i, "k39_brachio", "grave", True) != "ok":
        return []
    return [("x:k39_fushigi", o[1])]


def ap_brachio(s, a):
    i = s.tp
    p = s.P[i]
    if "k39_brachio" not in p.grave:
        return
    o = _fushigi_opt(s, i)
    if o is None:
        return
    z, n = o
    s.tap_cre(i, z)
    pre = p.mused
    if z in p.board:
        s.leave(i, z, "mana")
    if p.mused == pre:                     # 単色なら「タップして置く」分を自分で数える
        p.mused = min(len(p.mana), p.mused + 1)
    p.mused += n
    if "k39_brachio" not in p.grave:
        return
    p.grave.remove("k39_brachio")
    s.ev(f"フシギバース[自然(13)]：ブラキオ龍樹（{z.c.name} をタップしてマナに置き、{n}マナ）")
    s.enter(i, "k39_brachio", "grave", True)


def etl_brachio(s, i, u):
    """相手のクリーチャーが出て、相手のクリーチャーの能力がトリガーする時、かわりにトリガーしない
    （i＝そのクリーチャーを出した側。ブラキオ龍樹を持っているのはその相手）"""
    if u.c.kind != "C":
        return False
    return s.has(1 - i, "k39_brachio")


add("k39_brachio", "ブラキオ龍樹", 11, "N", power=23000, brk=4,
    races=("giantdragon", "giant", "dragon", "fujijuoukoku"), pri=12, roles="fin dis atk",
    freeacts=fa_brachio, actapply={"x:k39_fushigi": ap_brachio}, entertriglock=etl_brachio,
    text="Q・ブレイカー。相手のクリーチャーが出て、相手のクリーチャーの能力がトリガーする時、"
         "かわりにその能力はトリガーしない。"
         "フシギバース［自然(13)］：自分のクリーチャー1体をタップしてマナゾーンに置き、"
         "13からそのクリーチャーのコストを引いた数のコストを支払って、"
         "このクリーチャーを自分の墓地から召喚してもよい（自然1より少なくはならない）",
    note="「相手のクリーチャーが出た時の能力をトリガーさせない」は entertriglock= で書いた。"
         "エンジンはこの差し込み口で「出た時」（ENTER）と「クリーチャーが出た時」（ENTERWATCH）の"
         "両方をまとめて止めるので、相手のクリーチャーが出たことで誘発する"
         "自分側の「相手のクリーチャーが出た時」までいっしょに止まる（そこだけ本物より少し広い）",
    status="full", source=SRC["k39_brachio"])


# ================================================================ 3 十番龍 オービーメイカー Par100
def _obee_n(s, i):
    p = s.P[i]
    if p.x.get("k39_obee_turn") != s.turn:
        return 0
    return p.x.get("k39_obee_n", 0)


def _obee_count(s, i, u, kinds):
    """このターンに出した自分の自然のクリーチャー／タマシードを数える（軽減用）。

    数えるだけで盤面は変えない（全体に効く差し込み口だが、対戦の進みには影響しない）。"""
    if u.c.kind not in kinds or "N" not in u.c.civ:
        return
    p = s.P[i]
    if p.x.get("k39_obee_turn") != s.turn:
        p.x["k39_obee_turn"] = s.turn
        p.x["k39_obee_n"] = 0
    p.x["k39_obee_n"] = p.x.get("k39_obee_n", 0) + 1


def ew_obee(s, i, u):
    """自分の自然のクリーチャーが出た時"""
    _obee_count(s, i, u, "C")


def ti_obee(s, i, u):
    """自分の自然のタマシードが置かれた時"""
    _obee_count(s, i, u, "T")


def cx_obee(s, i, av):
    """このターン中に出した自分の自然のクリーチャー1体またはタマシード1つにつき、
    召喚コストを3少なくする（0以下にならない）"""
    return max(1, 10 - 3 * _obee_n(s, i))


def etl_obee(s, i, u):
    """シビルカウント5：自分の自然のクリーチャーまたはタマシードが合計5つ以上あれば、
    相手のターン中、相手のクリーチャーまたはタマシードが出てもその能力はトリガーしない
    （i＝そのカードを出した側。オービーメイカーを持っているのはその相手）"""
    if u.c.kind not in "CT" or s.tp != i:
        return False
    j = 1 - i
    if not s.has(j, "k39_obee"):
        return False
    n = sum(1 for z in s.P[j].board if z.c.kind in "CT" and "N" in z.c.civ)
    return n >= 5


add("k39_obee", "十番龍 オービーメイカー Par100", 10, "N", power=19000, brk=4, mach=True,
    races=("giantdragon", "giant", "dragon"), pri=13, roles="fin dis atk",
    costx=cx_obee, enterwatch=ew_obee, tamain=ti_obee, entertriglock=etl_obee,
    text="このターン中に出した自分の、自然のクリーチャー1体または自然のタマシード1つにつき、"
         "このクリーチャーの召喚コストを3少なくする（ただし0以下にはならない）。"
         "マッハファイター。Q・ブレイカー。"
         "シビルカウント5：自分の自然の、クリーチャーまたはタマシードが合計5つ以上あれば、"
         "相手のターン中、相手の、クリーチャーまたはタマシードが出てその能力がトリガーする時、"
         "かわりにその能力はトリガーしない",
    note="軽減は自然のクリーチャー（enterwatch=）と自然のタマシード（tamain=）の両方を数えている。"
         "シビルカウント5の「相手の出た時の能力をトリガーさせない」は entertriglock= で書いたが、"
         "エンジンがこの差し込み口を見るのはクリーチャーが出る時だけで、"
         "タマシードが置かれる時（place_tama）には見ないので、"
         "相手のタマシードの「置かれた時」の能力は止められない。"
         "また、エンジンはこの差し込み口で「出た時」と「クリーチャーが出た時」をまとめて止めるので、"
         "相手のクリーチャーが出たことで誘発する自分側の能力までいっしょに止まる",
    status="partial", source=SRC["k39_obee"])


# ================================================================ 4 超聖竜シデン・ギャラクシー
def _shiden_src_ok(z):
    return z.c.kind == "C" and ("dragon" in z.c.races or "angelcommand" in z.c.races)


def _shiden_srcs(s, i):
    """進化Vの進化元にできる2体（タップしているもの、失って安いものから）"""
    cs = [z for z in s.P[i].board if _shiden_src_ok(z)]
    return sorted(cs, key=lambda z: (0 if z.tap else 1, own_loss(s, i, z)))


def fa_shiden(s, i, av, cv):
    p = s.P[i]
    if "k39_shiden" not in p.hand or len(_shiden_srcs(s, i)) < 2:
        return []
    n = BY_KEY["k39_shiden"].cost
    if n > av or not cv.issuperset(set("LF")):
        return []
    if s.fate(i, "k39_shiden", "hand", True) != "ok":
        return []
    return [("x:k39_shidenv", n)]


def ap_shiden(s, a):
    i = s.tp
    p = s.P[i]
    if "k39_shiden" not in p.hand:
        return
    srcs = _shiden_srcs(s, i)
    if len(srcs) < 2 or s.fate(i, "k39_shiden", "hand", True) != "ok":
        return
    p.hand.remove("k39_shiden")
    p.mused += a[1]
    base, other = srcs[0], srcs[1]
    s.ev("進化V：超聖竜シデン・ギャラクシー（ドラゴンまたはエンジェル・コマンド2体の上に置く）")
    u = s.enter(i, "k39_shiden", "hand", True, on=base)
    if u is None:
        return
    if other in p.board:
        p.board.remove(other)
        u.under = u.under + [other.k] + other.under


def _mb_pick(under):
    """メテオバーンで墓地に置く下のカードを2枚まで選ぶ（ドラゴンとエンジェル・コマンドを1枚ずつ取る）"""
    idx = []
    for r in ("dragon", "angelcommand"):
        for j, k in enumerate(under):
            if j in idx:
                continue
            if r in BY_KEY[k].races:
                idx.append(j)
                break
    return sorted(idx[:2])


def at_shiden(s, i, u):
    """メテオバーン：各ターン、はじめて攻撃する時、下のカードを2枚まで墓地に置いてもよい。
    ドラゴン・カードを置いたらアンタップし、エンジェル・コマンド・カードを置いたら
    このターン破壊されるかわりにとどまる"""
    if u.x.get("k39_mb") == s.turn or not u.under:
        return
    idx = _mb_pick(u.under)
    if not idx:
        return                              # ドラゴンもエンジェル・コマンドも無いなら置かない
    u.x["k39_mb"] = s.turn
    put = [u.under[j] for j in idx]
    u.under = [k for j, k in enumerate(u.under) if j not in idx]
    for k in put:
        s.grave_put(i, k)
    s.ev(f"　メテオバーン：シデン・ギャラクシーの下のカード{len(put)}枚を墓地に置いた")
    if any("dragon" in BY_KEY[k].races for k in put):
        u.tap = False
        s.ev("　　ドラゴンを置いたのでアンタップ")
    if any("angelcommand" in BY_KEY[k].races for k in put):
        u.x["k39_stay"] = s.turn
        s.ev("　　エンジェル・コマンドを置いたので、このターンは破壊されずとどまる")


def rep_shiden(s, i, u, dest, destroy):
    if u.k != "k39_shiden" or not destroy:
        return False
    if u.x.get("k39_stay") != s.turn:
        return False
    s.ev("　シデン・ギャラクシー：破壊されるかわりにバトルゾーンにとどまる")
    return True


def pr_shiden(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and not (BY_KEY[kk].evo and not BY_KEY[kk].neo)
            and ("dragon" in BY_KEY[kk].races or "angelcommand" in BY_KEY[kk].races))
    return None if n >= 4 else "進化元（ドラゴンかエンジェル・コマンド）が4体いない"


add("k39_shiden", "超聖竜シデン・ギャラクシー", 5, "LF", power=15000, brk=3, evo="LF",
    races=("angelcommand", "command", "armoreddragon", "dragon", "samurai"), pri=11, roles="atk fin",
    costx=lambda s, i, av: 99, freeacts=fa_shiden, actapply={"x:k39_shidenv": ap_shiden},
    attack=at_shiden, leaverep=rep_shiden, playrule=pr_shiden,
    evox=_shiden_src_ok,
    text="進化V：ドラゴンまたはエンジェル・コマンドいずれかのクリーチャー2体を重ねた上に置く。"
         "T・ブレイカー。"
         "メテオバーン：各ターン、はじめてこのクリーチャーが攻撃する時、このクリーチャーの下にあるカードを"
         "2枚まで墓地に置いてもよい。こうしてドラゴン・カードを置いたら、このクリーチャーをアンタップする。"
         "こうしてエンジェル・コマンド・カードを置いたら、このクリーチャーがこのターンに破壊される時、"
         "かわりにバトルゾーンにとどまる"
         "（下のカードはドラゴン1枚とエンジェル・コマンド1枚を取れるように選び、"
         "どちらも無い時は置かない）",
    note="進化Vは「2体まとめて下に置く」ので、ふつうの進化の手（1体の上に置く）は出さず、"
         "追加の手（進化V）だけで出す形にした。"
         "envtest の effect_smoke は△になるが、これは試験の場面に進化元が1体しか置かれず、"
         "また進化Vの手の名前にカードのキーが入らないため（進化元2体を置いた場面で別に動作を確かめた）",
    source=SRC["k39_shiden"])


# ================================================================ 5 呪烏竜 ACE-Curase／繁栄の鏡
def e_curase(s, i, u):
    """出た時、各プレイヤーは自身の手札をすべて超次元ゾーンに置く。
    その後、各プレイヤーは自身のマナゾーンにあるクリーチャーをすべて手札に戻す"""
    for j in (0, 1):
        p = s.P[j]
        n = len(p.hand)
        for k in list(p.hand):
            if k in p.hand:
                p.hand.remove(k)
                s.grave_put(j, k)
        if n:
            s.ev(f"　ACE-Curase：プレイヤー{j}の手札{n}枚を手札から取り除く（超次元ゾーンの代わりに墓地）")
    for j in (0, 1):
        p = s.P[j]
        back = [k for k in p.mana if BY_KEY[k].kind == "C"]
        for k in back:
            if k in p.mana:
                s.take_mana(j, k)
                p.hand.append(k)
        if back:
            s.ev(f"　ACE-Curase：プレイヤー{j}のマナのクリーチャー{len(back)}枚を手札へ")


def sp_hanei(s, i):
    """繁栄の鏡：山札の上から2枚をタップしてマナゾーンに置く。
    その後、自分のマナゾーンからカードを2枚まで手札に戻す"""
    p = s.P[i]
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        k = p.deck.pop()
        s.add_mana(i, k, tapped=True, src="deck")
        s.ev(f"　繁栄の鏡：山札の上の {BY_KEY[k].name} をタップしてマナへ")
    got = 0
    while got < 2 and len(p.mana) >= 3:
        k = max(p.mana, key=E.PRI.get)
        if E.PRI[k] < 3:
            break                           # 戻しても得にならない安い札は戻さない
        s.take_mana(i, k)
        p.hand.append(k)
        s.ev(f"　繁栄の鏡：マナの {BY_KEY[k].name} を手札へ")
        got += 1


add("k39_curase", "呪烏竜 ACE-Curase／繁栄の鏡", 15, "WD", power=30000, brk=99,
    races=("kingcommanddragon", "command", "dragon", "origin"), twin=(4, "N", False),
    pri=14, roles="fin dis acc",
    enter=e_curase, spell=sp_hanei,
    text="【クリーチャー側：呪烏竜 ACE-Curase（水/闇15・キング・コマンド・ドラゴン／オリジン・パワー30000）】"
         "ワールド・ブレイカー（相手のシールドをすべてブレイクする）。"
         "このクリーチャーが出た時、各プレイヤーは自身の手札をすべて超次元ゾーンに置く。"
         "その後、各プレイヤーは自身のマナゾーンにあるクリーチャーをすべて手札に戻す。"
         "【呪文側：繁栄の鏡（自然4）】自分の山札の上から2枚をタップしてマナゾーンに置く。"
         "その後、自分のマナゾーンからカードを2枚まで手札に戻す"
         "（重要度の高い2枚を戻す。マナゾーンが3枚未満になるなら戻さない）",
    note="「手札をすべて超次元ゾーンに置く」は、このシミュレーターに超次元ゾーンが無いので"
         "墓地に置くことで近似した（本来は戻ってこないゾーン。墓地だと蘇生・回収の的になるので弱い近似）",
    status="partial", source=SRC["k39_curase"])


# ================================================================ 6 頂上電融 ジョルト・ザ・ジョクスト4th
def at_jolt(s, i, u):
    """攻撃する時、相手のクリーチャー1体を選んでもよい。それとこのクリーチャーをバトルさせる

    「選んでもよい」は全デッキ共通の決まりで、勝てる相手（パワーが下のもの）のうち
    いちばん重要なものを選ぶ。"""
    w = s.power(i, u, True)
    t = s.target(i, lambda z: s.power(1 - i, z) < w)
    if t is None:
        return
    s.ev(f"　ジョルト・ザ・ジョクスト4th：{t.c.name} とバトルする")
    s.battle(i, u, 1 - i, t)


def tw_jolt(s, i, u):
    """各ターン、このクリーチャーがはじめてタップした時、自分のマナゾーンに
    ドラゴン・カードまたはジョーカーズ・カードが合計5枚以上あれば、このクリーチャーをアンタップする"""
    if u.k != "k39_jolt" or s.over:
        return
    if u.x.get("k39_tapped") == s.turn:
        return
    u.x["k39_tapped"] = s.turn
    p = s.P[i]
    n = sum(1 for k in p.mana if "dragon" in BY_KEY[k].races or "jokers" in BY_KEY[k].races)
    if n < 5:
        return
    u.tap = False
    s.ev(f"　ジョルト・ザ・ジョクスト4th：マナのドラゴン／ジョーカーズが{n}枚なのでアンタップ")


def ae_jolt(s, i, u):
    """このクリーチャーの攻撃の終わりに、相手のシールドもクリーチャーもなければ、自分はゲームに勝つ"""
    if u.k != "k39_jolt" or s.over:
        return
    o = s.P[1 - i]
    if o.sh or any(z.c.kind == "C" for z in o.board):
        return
    s.win(i, "ジョルト・ザ・ジョクスト4th")


add("k39_jolt", "頂上電融 ジョルト・ザ・ジョクスト4th", 7, "WFN", power=10000, brk=2, sa=True,
    races=("dispector", "gaialcommanddragon", "command", "dragon", "jokers"), pri=12, roles="fin atk rem",
    enter=exlife_enter, leaverep=exlife_rep, attack=at_jolt, tapwatch=tw_jolt, atkend=ae_jolt,
    unbok=lambda s, i, u: u.k == "k39_jolt",
    text="EXライフ（出た時に山札の上から1枚をこのクリーチャーの下にシールドとして置き、"
         "離れる時はかわりにそのシールドを墓地に置いてバトルゾーンに残る）。"
         "スピードアタッカー。W・ブレイカー。このクリーチャーはブロックされない。"
         "このクリーチャーが攻撃する時、相手のクリーチャーを1体選んでもよい。"
         "その選んだクリーチャーとこのクリーチャーをバトルさせる（勝てる相手だけを選ぶ）。"
         "各ターン、このクリーチャーがはじめてタップした時、自分のマナゾーンに"
         "ドラゴン・カードまたはジョーカーズ・カードが合計5枚以上あれば、このクリーチャーをアンタップする。"
         "このクリーチャーの攻撃の終わりに、相手のシールドもクリーチャーもなければ、自分はゲームに勝つ",
    source=SRC["k39_jolt"])


# ================================================================ 7 偽りの王 ナンバーナイン／歓喜の歌
def sl_nine(s, i, cost):
    """相手は呪文を唱えられない（i＝唱えようとしている側）"""
    return s.has(1 - i, "k39_nine")


def sp_kanki(s, i):
    """歓喜の歌：山札の上から9枚を見て、その中からコスト9のカードを1枚手札に加えてもよい。
    残りをシャッフルして山札の下に置く"""
    k = s.dig(i, 9, lambda k: BY_KEY[k].cost == 9, "bottom")
    if k is None:
        s.ev("　歓喜の歌：山札の上9枚にコスト9のカードが無かった")
    else:
        s.ev(f"　歓喜の歌：{BY_KEY[k].name} を手札に加えた")


add("k39_nine", "偽りの王 ナンバーナイン／歓喜の歌", 9, "L", power=9000, brk=2,
    races=("kingcommanddragon", "command", "dragon", "unknown"), twin=(3, "L", False),
    pri=11, roles="dis fin draw",
    spelllock=sl_nine, spell=sp_kanki,
    text="【クリーチャー側：偽りの王 ナンバーナイン（光9・キング・コマンド・ドラゴン／アンノウン・パワー9000）】"
         "W・ブレイカー。相手は呪文を唱えられない。"
         "【呪文側：歓喜の歌（光3）】自分の山札の上から9枚を見る。その中からコスト9のカードを1枚、"
         "表向きにしてから手札に加えてもよい。残りをシャッフルし、山札の下に置く",
    source=SRC["k39_nine"])


# ================================================================ 8 翼速 ザ・ウイング
def cx_wing(s, i, av):
    """自分のクリーチャーが相手のより多ければ、召喚コストを3少なくする"""
    return 3 if s.ncre(i) > s.ncre(1 - i) else 6


def tw_wing(s, i, u):
    """自分のクリーチャーがタップした時、カードを1枚引いてもよい"""
    if u.c.kind != "C" or s.over or not s.has(i, "k39_wing"):
        return
    p = s.P[i]
    for _ in range(sum(1 for z in p.board if z.k == "k39_wing")):
        if s.over or len(p.deck) <= 1:
            return                          # 山札が尽きるなら引かない（任意の効果）
        s.draw(i, 1)
        s.ev("　翼速 ザ・ウイング：自分のクリーチャーがタップしたので1枚引く")


def lw_wing(s, i, u, dest, destroy):
    """自分の他のクリーチャーが離れた時、このクリーチャーをアンタップしてもよい"""
    if u.c.kind != "C" or u.k == "k39_wing" or s.over:
        return
    for z in s.P[i].board:
        if z.k == "k39_wing" and z.tap:
            z.tap = False
            s.ev("　翼速 ザ・ウイング：他のクリーチャーが離れたのでアンタップ")


add("k39_wing", "翼速 ザ・ウイング", 6, "L", power=6000, brk=2, blocker=True,
    races=("armoredsoniccommand", "soniccommand", "command", "armored"), pri=8, roles="draw blk atk",
    costx=cx_wing, tapwatch=tw_wing, leavewatch=lw_wing,
    text="自分のクリーチャーが相手のより多ければ、このクリーチャーの召喚コストを3少なくする。"
         "ブロッカー。W・ブレイカー。"
         "自分のクリーチャーがタップした時、カードを1枚引いてもよい（山札が尽きる時は引かない）。"
         "自分の他のクリーチャーが離れた時、このクリーチャーをアンタップしてもよい",
    source=SRC["k39_wing"])


# ================================================================ 9 水晶の記録 ゼノシャーク／クリスタル・メモリー
def sp_crystal(s, i):
    """クリスタル・メモリー：自分の山札を見て、その中から1枚手札に加える。その後、山札をシャッフルする"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    best = max(p.deck, key=lambda k: (E.PRI[k] - 3 * p.hand.count(k), k))
    p.deck.remove(best)
    p.hand.append(best)
    s.rng.shuffle(p.deck)
    s.ev(f"　クリスタル・メモリー：山札から {BY_KEY[best].name} を手札へ")


def at_xeno(s, i, u):
    """スマッシュ・バースト：攻撃する時、このカードの呪文側を、バトルゾーンに置いたまま
    コストを支払わずに唱えてもよい"""
    cost = BY_KEY["k39_xeno"].twin[0]
    if s.over or not s.spell_ok(i, cost):
        return
    p = s.P[i]
    p.spl += 1
    s.note("cast", i, "k39_xeno")
    s.first_play(i, cost)
    prev = s.spc
    s.spc = cost
    s.ev("　スマッシュ・バースト：クリスタル・メモリー をコストを支払わずに唱える")
    for f in E.SPELLWATCH:
        if not s.over:
            f(s, i, "k39_xeno")
    if not s.over:
        sp_crystal(s, i)
    s.spc = prev


add("k39_xeno", "水晶の記録 ゼノシャーク／クリスタル・メモリー", 3, "W", power=1000,
    races=("mutopia",), twin=(4, "W", True), pri=6, roles="draw atk trg",
    attack=at_xeno, spell=sp_crystal,
    text="【クリーチャー側：水晶の記録 ゼノシャーク（水3・ムートピア・パワー1000）】"
         "スマッシュ・バースト：このクリーチャーが攻撃する時、このカードの呪文側を、"
         "バトルゾーンに置いたままコストを支払わずに唱えてもよい。"
         "【呪文側：クリスタル・メモリー（水4）】S・トリガー。"
         "自分の山札を見て、その中から1枚手札に加える。その後、山札をシャッフルする"
         "（手札に無い札のうち重要度のいちばん高いものを取る）",
    source=SRC["k39_xeno"])


# ================================================================ 10 堕魔 ジグス★ガルビ
def _magic_count(s, i, u):
    """自分の魔導具の数（バトルゾーン＋下に重なったカード＋墓地）"""
    n = 0
    for z in s.P[i].board:
        if "madogu" in z.c.races:
            n += 1
        for k in z.under:
            if "madogu" in BY_KEY[k].races:
                n += 1
    for k in s.P[i].grave:
        if "madogu" in BY_KEY[k].races:
            n += 1
    return n


def ew_jigus(s, i, u):
    """自分の「無月の門」を使った時、このクリーチャーを自分の墓地からタップして出してもよい

    このシミュレーターに「無月の門」という仕組みが無いので、
    「自分のドルスザク・クリーチャーが、魔導具が合計4つ以上ある状態で手札か墓地から出た時」で近似した。"""
    p = s.P[i]
    if "k39_jigus" not in p.grave or s.over:
        return
    if u.c.kind != "C" or "dorusuzaku" not in u.c.races:
        return
    if u.x.get("src") not in ("hand", "grave"):
        return
    if _magic_count(s, i, u) < 4:
        return
    if s.fate(i, "k39_jigus", "grave", False) != "ok":
        return
    p.grave.remove("k39_jigus")
    s.ev("　無月の門を使ったので、堕魔 ジグス★ガルビ が墓地からタップして出る")
    z = s.enter(i, "k39_jigus", "grave", False)
    if z is not None:
        s.tap_cre(i, z)


add("k39_jigus", "堕魔 ジグス★ガルビ", 6, "D", power=6000, brk=2,
    races=("mafigang", "madogu", "mugetsu"), pri=7, roles="atk blk",
    enterwatch=ew_jigus,
    text="W・ブレイカー。"
         "自分の「無月の門」を使った時、このクリーチャーを自分の墓地からタップして出してもよい",
    note="「無月の門」という仕組みがこのシミュレーターに無いので、"
         "「自分のドルスザク・クリーチャーが、自分の魔導具（バトルゾーン＋下のカード＋墓地）が"
         "合計4つ以上ある状態で、手札か墓地から出た時」で近似した"
         "（いまドルスザクのカードは2枚しかないので、働く場面はまれ）",
    status="partial", source=SRC["k39_jigus"])


# ================================================================ 11 戦極竜ヴァルキリアス・ムサシ
def _musashi_srcs(s, i):
    cs = [z for z in s.P[i].board if z.c.kind == "C" and "samurai" in z.c.races]
    return sorted(cs, key=lambda z: (0 if z.tap else 1, own_loss(s, i, z)))


def fa_musashi(s, i, av, cv):
    p = s.P[i]
    if "k39_musashi" not in p.hand or len(_musashi_srcs(s, i)) < 2:
        return []
    n = BY_KEY["k39_musashi"].cost
    if n > av or "F" not in cv:
        return []
    if s.fate(i, "k39_musashi", "hand", True) != "ok":
        return []
    return [("x:k39_musashiv", n)]


def ap_musashi(s, a):
    i = s.tp
    p = s.P[i]
    if "k39_musashi" not in p.hand:
        return
    srcs = _musashi_srcs(s, i)
    if len(srcs) < 2 or s.fate(i, "k39_musashi", "hand", True) != "ok":
        return
    p.hand.remove("k39_musashi")
    p.mused += a[1]
    base, other = srcs[0], srcs[1]
    s.ev("進化V：戦極竜ヴァルキリアス・ムサシ（サムライ・クリーチャー2体の上に置く）")
    u = s.enter(i, "k39_musashi", "hand", True, on=base)
    if u is None:
        return
    if other in p.board:
        p.board.remove(other)
        u.under = u.under + [other.k] + other.under


def e_musashi(s, i, u):
    """出た時、進化ではないサムライ・クリーチャーを2体まで手札から出してもよい。
    それらに「スピードアタッカー」を与え、そのターンの終わりに破壊する"""
    p = s.P[i]
    for _ in range(2):
        if s.over:
            return
        cands = [k for k in sorted(set(p.hand))
                 if BY_KEY[k].kind == "C" and "samurai" in BY_KEY[k].races and not BY_KEY[k].evo]
        if not cands:
            return
        k = max(cands, key=E.PRI.get)
        if s.fate(i, k, "hand", False) != "ok":
            return
        p.hand.remove(k)
        s.ev(f"　ヴァルキリアス・ムサシ：手札から {BY_KEY[k].name} を出す（SA・ターンの終わりに破壊）")
        z = s.enter(i, k, "hand", False, sa=True)
        if z is not None:
            z.x["k39_musashi_eot"] = s.turn


def ta_musashi(s, i, u):
    """ムサシが出したクリーチャーを、そのターンの終わりに破壊する"""
    if u.x.get("k39_musashi_eot") != s.turn:
        return
    s.ev(f"　ヴァルキリアス・ムサシ：ターンの終わりなので {u.c.name} を破壊")
    s.leave(i, u, "grave", destroy=True)


def pr_musashi(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "samurai" in BY_KEY[kk].races)
    return None if n >= 4 else "進化元（サムライ・クリーチャー）が4体いない"


add("k39_musashi", "戦極竜ヴァルキリアス・ムサシ", 6, "F", power=11000, brk=2, evo="F",
    races=("humanoid", "armoreddragon", "dragon", "samurai"), pri=10, roles="atk fin",
    costx=lambda s, i, av: 99, freeacts=fa_musashi, actapply={"x:k39_musashiv": ap_musashi},
    enter=e_musashi, tendall=ta_musashi, playrule=pr_musashi,
    evox=lambda s, i, u: u.c.kind == "C" and "samurai" in u.c.races,
    text="進化V：サムライ・クリーチャー2体を重ねた上に置く。W・ブレイカー。"
         "このクリーチャーが出た時、進化ではないサムライ・クリーチャーを2体まで、自分の手札から出してもよい。"
         "そのクリーチャーに「スピードアタッカー」を与える。そのターンの終わりに、それらを破壊する",
    note="進化Vは「2体まとめて下に置く」ので、ふつうの進化の手（1体の上に置く）は出さず、"
         "追加の手（進化V）だけで出す形にした。"
         "envtest の effect_smoke は△になるが、これは試験の場面にサムライが置かれていないためで、"
         "サムライ2体を置いた場面では進化Vも「出た時」も動くことを確かめた",
    source=SRC["k39_musashi"])


# ================================================================ 12 超神羅ギャラクシー・デスティニー
def at_destiny(s, i, u):
    """攻撃する時、自分の山札を見る。その中からクリーチャーを2体まで出してもよい"""
    p = s.P[i]
    for _ in range(2):
        if s.over or len(p.deck) <= 1:
            break
        best, bv = None, -1
        for k in sorted(set(p.deck)):
            if not _playable_cre(BY_KEY[k]):
                continue
            if E.PRI[k] > bv and s.fate(i, k, "deck", False) == "ok":
                best, bv = k, E.PRI[k]
        if best is None:
            break
        p.deck.remove(best)
        s.ev(f"　ギャラクシー・デスティニー：山札から {BY_KEY[best].name} を出す")
        s.enter(i, best, "deck", False)
    if not s.over:
        s.rng.shuffle(p.deck)


def pr_destiny(deck, k):
    n = sum(v for kk, v in deck.items() if kk != k and _ultimate(BY_KEY[kk]))
    return None if n >= 2 else "進化元になる究極進化クリーチャーが2体いない"


add("k39_destiny", "超神羅ギャラクシー・デスティニー", 7, "N", power=17000, brk=3, evo="N",
    races=("gaiacommand", "command", "lunarssungaizer"), pri=12, roles="atk fin acc",
    attack=at_destiny, playrule=pr_destiny, evox=lambda s, i, u: _ultimate(u.c),
    text="究極進化MAX：自分の究極進化クリーチャー1体の上に置く。T・ブレイカー。"
         "このクリーチャーが攻撃する時、自分の山札を見る。その中からクリーチャーを2体まで出してもよい。"
         "その後、山札をシャッフルする（重要度のいちばん高いクリーチャーから出す）",
    note="究極進化クリーチャーは、このシミュレーターに「究極進化」の印が無いので、"
         "カードの説明文に「究極進化」と書かれた進化クリーチャーで判定している"
         "（いま当てはまるのは《超神羅星アポロヌス・ドラゲリオン》1枚だけなので、"
         "元のカードと同じ理由で実際にはほとんど出せない）。"
         "envtest の effect_smoke は△になるが、これは試験の場面に究極進化クリーチャーが置かれていないためで、"
         "《超神羅星アポロヌス・ドラゲリオン》を置いた場面では召喚も攻撃時の能力も動くことを確かめた",
    source=SRC["k39_destiny"])


# ================================================================ 13 若頭 鬼流院 刃
def e_jin(s, i, u):
    """出た時、自然のハンター・クリーチャーを好きな数、自分のマナゾーンからタップして出してもよい"""
    p = s.P[i]
    for _ in range(12):
        if s.over:
            return
        cands = [k for k in sorted(set(p.mana))
                 if _playable_cre(BY_KEY[k]) and "N" in BY_KEY[k].civ and "hunter" in BY_KEY[k].races]
        if not cands:
            return
        best = max(cands, key=E.PRI.get)
        if s.fate(i, best, "mana", False) != "ok":
            return
        s.take_mana(i, best)
        s.ev(f"　鬼流院 刃：マナの {BY_KEY[best].name} をタップして出す")
        z = s.enter(i, best, "mana", False)
        if z is None:
            return
        s.tap_cre(i, z)


add("k39_jin", "若頭 鬼流院 刃", 10, "N", power=17000, brk=3,
    races=("gaiacommand", "command", "beastfolk", "hunter"), pri=12, roles="fin acc atk",
    enter=e_jin,
    text="T・ブレイカー。"
         "このクリーチャーが出た時、自然のハンター・クリーチャーを好きな数、"
         "自分のマナゾーンからタップして出してもよい（重要度の高いものから全部出す）",
    note="進化クリーチャーは進化元なしに出せないので、マナから出す対象から外している（共通の決まり）",
    source=SRC["k39_jin"])


# ================================================================ 14 アクア・スペルブルー／インビンシブル・オーラ
def e_spellblue(s, i, u):
    """出た時、自分の山札をシャッフルし、上から1枚を表向きにする。
    そのカードが呪文なら、コストを支払わずに唱えてもよい。呪文でなければ、手札に加える"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    s.rng.shuffle(p.deck)
    k = p.deck.pop()
    c = BY_KEY[k]
    s.ev(f"　アクア・スペルブルー：山札の上の {c.name} を表向きにした")
    if c.kind == "S":
        if s.spell_ok(i, c.cost):
            s.ev("　　呪文なのでコストを支払わずに唱える")
            s.cast(i, k)
        else:
            p.deck.append(k)                # 唱えられないので山札の上に戻す
        return
    p.hand.append(k)
    s.ev(f"　　呪文ではないので {c.name} を手札に加える")


def sp_invaura(s, i):
    """インビンシブル・オーラ：自分の山札の上から3枚まで、シールド化する"""
    for _ in range(3):
        if s.over or not s.add_shield(i):
            return


add("k39_spellblue", "アクア・スペルブルー／インビンシブル・オーラ", 7, "W", power=2000, trig=True,
    races=("liquid", "hunter"), twin=(13, "L", False), pri=7, roles="trg acc shd",
    enter=e_spellblue, spell=sp_invaura,
    text="【クリーチャー側：アクア・スペルブルー（水7・リキッド・ピープル／ハンター・パワー2000）】"
         "S・トリガー。このクリーチャーが出た時、自分の山札をシャッフルし、上から1枚を表向きにする。"
         "そのカードが呪文なら、コストを支払わずに唱えてもよい。呪文でなければ、手札に加える。"
         "【呪文側：インビンシブル・オーラ（光13）】自分の山札の上から3枚まで、シールド化する",
    note="表向きにしたカードがツインパクト（クリーチャー側と呪文側のある札）の場合は、"
         "このシミュレーターではカード1枚の種類がクリーチャーなので「呪文ではない」として手札に加える",
    source=SRC["k39_spellblue"])


# ================================================================ 15 超光喜 エルボロム
def a_elborom(s, i, u):
    """出た時または攻撃する時、1枚引く。その後、自分の手札を1枚シールド化してもよい"""
    s.draw(i, 1)
    p = s.P[i]
    if s.over or len(p.hand) < 2:
        return
    k = min(p.hand, key=E.PRI.get)
    p.hand.remove(k)
    if not s.add_shield(i, k, False):
        p.hand.append(k)
        return
    s.ev(f"　超光喜 エルボロム：手札の {BY_KEY[k].name} をシールド化した")


def fa_elborom(s, i, av, cv):
    """ハイパー化：自分の他のクリーチャーを1体タップしてハイパーモードを解放する"""
    for u in s.P[i].board:
        if u.k == "k39_elborom" and not u.hyper:
            if any(z is not u and z.c.kind == "C" and not z.tap for z in s.P[i].board):
                return [("x:k39_hyper_elb", u.uid)]
    return []


def ap_elborom(s, a):
    i = s.tp
    p = s.P[i]
    u = next((z for z in p.board if z.uid == a[1] and z.k == "k39_elborom"), None)
    if u is None or u.hyper:
        return
    oth = [z for z in p.board if z is not u and z.c.kind == "C" and not z.tap]
    if not oth:
        return
    s.tap_cre(i, min(oth, key=lambda z: own_loss(s, i, z)))
    u.hyper = True
    s.ev("ハイパー化：超光喜 エルボロム（他のクリーチャー1体をタップ）")


def si_elborom(s, i, k, up):
    """このターン自分のシールドゾーンにカードが置かれたことを書き留める（ハイパーモードの条件）"""
    s.P[i].x["k39_elb_shield"] = s.turn


def tep_elborom(s, i):
    """ハイパーモード：各ターンの終わりに、このターン自分のシールドゾーンにカードが置かれていたら、
    「S・トリガー」を持つ呪文を1枚、自分の手札からコストを支払わずに唱えてもよい"""
    p = s.P[i]
    if s.over or p.x.get("k39_elb_shield") != s.turn:
        return
    for u in p.board:
        if s.over or u.k != "k39_elborom" or not u.hyper:
            continue
        best, bv, tw = None, -1, False
        for k in sorted(set(p.hand)):
            r = _st_spell_cost(k)
            if r is None:
                continue
            cost, is_twin = r
            if not s.spell_ok(i, cost):
                continue
            if E.PRI[k] > bv:
                best, bv, tw = k, E.PRI[k], is_twin
        if best is None:
            return
        p.hand.remove(best)
        s.ev(f"　超光喜 エルボロム（ハイパーモード）：{BY_KEY[best].name} をコストを支払わずに唱える")
        s.cast(i, best, twin=tw)


add("k39_elborom", "超光喜 エルボロム", 4, "LW", power=6000, brk=2, blocker=True,
    races=("demoncommand", "command", "hyperbeast"), pri=8, roles="draw blk shd atk",
    enter=a_elborom, attack=a_elborom, shieldin=si_elborom, tendp=tep_elborom,
    freeacts=fa_elborom, actapply={"x:k39_hyper_elb": ap_elborom},
    text="ブロッカー。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、カードを1枚引く。その後、自分の手札を1枚、"
         "シールド化してもよい（手札のうち重要度のいちばん低い1枚を裏向きで置く）。"
         "ハイパー化：自分のメインステップ中、自分の他のクリーチャー1体をタップして、"
         "次の自分のターンのはじめまでハイパーモードを解放してよい。"
         "ハイパーモード中はパワー8500になり、各ターンの終わりに、"
         "このターン自分のシールドゾーンにカードが置かれていたら、「S・トリガー」を持つ呪文を1枚、"
         "自分の手札からコストを支払わずに唱えてもよい",
    source=SRC["k39_elborom"])
E.HYPER_POW["k39_elborom"] = 2500
E.HYPER_BRK["k39_elborom"] = 2
