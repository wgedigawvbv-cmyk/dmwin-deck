"""担当17：公式大会入賞デッキにあった未実装カード12枚

  出典は各カードの source（デュエル・マスターズWiki のカードページ）。入賞リストは
  https://dm.takaratomy.co.jp/coverage/dmgp2025-2ndb_deck

  能力は省かずに1枚ずつ書いた。エンジンに差し込み口がなくて表せなかったところだけ status="partial" にして note に書いた。
  「〜を選ぶ」「〜してもよい」は、重要度PRIの高い相手のカード／低い自分のカードを選ぶという全デッキ共通の決まりで機械的に決めた。

  調べ直して分かったこと
    ・《DARK MATERIAL COMPLEX》だけが殿堂入り（他の11枚は殿堂リストに名前がない。dmwiki の殿堂入り一覧で確認）。
    ・《洗打の妖精》はカード名の読みが「スクラブ・フェアリー」で、種族はジャイアント／スノーフェアリーだが
      文明は自然ではなく**水**（カード枠の表記「洗打の妖精 UC 水文明 (2)」と、採用デッキが青系ばかりなことで確認）。
    ・《異端流し オニカマス》は dmwiki・遊々亭の2つを読んでも「ブロックされない」の記載が出てこなかったので入れていない。
      踏み倒しメタの方は「相手のターン中」「〜してもよい」と書かれていたが、
      このカードの働き（召喚以外で出たクリーチャーを止める）としては常時・強制と読むのが自然なのでそちらで実装した（note に書いた）。
    ・「超魂X」はすでに env1／env10／env18 で「このカードがクリーチャーの下にあれば、その上のクリーチャーに能力を与える」
      として実装されていたので、《貴布人 テブルカッケ＝エディ》も同じ形に合わせた。

  この版で新しく書いた仕組み
    ・ワールド・ブレイカー＝brk=99（env10 のヘヴィ・デス・メタルと同じ）。
    ・「アンタップしない」＝自分のターンのはじめ（tstart）に、エンジンがアンタップした後でもう一度タップする。
    ・「相手のクリーチャーが攻撃するなら攻撃先は自分が選ぶ」＝ guard（ガードマンの差し込み口）で攻撃先を付け替える。
    ・「相手は呪文を唱えられない（次の自分のターンのはじめまで）」＝ spelllock ＋ プレイヤーの x に期限を書く。
    ・「選んだ数字のコストの呪文・攻撃・ブロックを止める」＝ spelllock ／ atklock ／ blocklock の3つを使う。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, free_play, worst_hand
from envcards.env0 import SLAYER, owner_of

W = "https://dmwiki.net/"


# ================================================================ 共通の小道具
def _fb(c):
    """ファイアー・バードか（アーマード・ファイアー・バードも含む）"""
    return "firebird" in c.races or "armoredfirebird" in c.races


def _minus_power(s, i, t, n):
    """相手のクリーチャー t のパワーを n 下げる（0以下になれば破壊）"""
    t.pw -= n
    s.ev(f"　{t.c.name} のパワーを-{n}")
    if s.power(1 - i, t) <= 0 and t in s.P[1 - i].board:
        s.leave(1 - i, t, "grave", by_opp=True, destroy=True)


def _opp_watch(s, i, key):
    """出たクリーチャー（持ち主 i）の相手側に key があれば、その相手の番号を返す"""
    j = 1 - i
    return j if any(z.k == key for z in s.P[j].board) else None


# ================================================================ DARK MATERIAL COMPLEX
def _complex_feed(s, i, u):
    """山札の上から1枚を表向きにしてこのクリーチャーの下に置く（任意：下が10枚未満なら置く）

    8枚そろえばアンタップできるので置くのが得。攻撃するたび1枚減るので、少し余裕を持って10枚までためる。"""
    p = s.P[i]
    if len(p.deck) <= 1 or len(u.under) >= 10:
        return
    u.under.append(p.deck.pop())
    s.ev(f"　DARK MATERIAL COMPLEX の下に1枚置く（{len(u.under)}枚）")
    if len(u.under) >= 8 and u.tap:
        u.tap = False
        s.ev("　8枚目が置かれたのでアンタップする")


def e_complex(s, i, u):
    """タップしてバトルゾーンに出る"""
    u.tap = True


def ts_complex(s, i, u):
    """自分のターンのはじめに1枚置く。下が7枚以下ならアンタップしない（エンジンが起こした後でタップし直す）"""
    _complex_feed(s, i, u)
    if len(u.under) <= 7:
        u.tap = True


def lw_complex(s, i, u, dest, destroy_):
    """他のクリーチャーが離れた時（どちらのプレイヤーのものでも）、下に1枚置く"""
    if u.c.kind != "C":
        return
    for j in (0, 1):
        for z in s.P[j].board:
            if z.k == "eb_complex" and z is not u:
                _complex_feed(s, j, z)


def rep_complex(s, i, u, dest, destroy_):
    """下のカードが7枚以下なら離れない"""
    return u.k == "eb_complex" and len(u.under) <= 7


def a_complex(s, i, u):
    """攻撃する時、下のカード1枚を墓地に置いてもよい。それがクリーチャーなら墓地から出す
    （置くのは、墓地から出せるいちばん重要なクリーチャー。出せるものが無ければ使わない）"""
    p = s.P[i]
    best, bv = None, -1
    for k in u.under:
        c = BY_KEY[k]
        if c.kind != "C" or (c.evo and not c.neo):
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    u.under.remove(best)
    s.ev(f"　下の {BY_KEY[best].name} を墓地に置く")
    s.grave_put(i, best)
    if best in p.grave and s.fate(i, best, "grave", False) == "ok":
        p.grave.remove(best)
        s.ev(f"　墓地から {BY_KEY[best].name} を出す")
        s.enter(i, best, "grave", False)


add("eb_complex", "DARK MATERIAL COMPLEX", 1, "D", power=25000, brk=99, pri=10,
    races=("pandorabox",), roles="fin atk",
    enter=e_complex, tstart=ts_complex, attack=a_complex, leavewatch=lw_complex, leaverep=rep_complex,
    text="ワールド・ブレイカー（相手のシールドをすべてブレイクする）。このクリーチャーはタップしてバトルゾーンに出る。"
         "他のクリーチャーが離れた時、または自分のターンのはじめに、自分の山札の上から1枚を表向きにして"
         "このクリーチャーの下に置いてもよい。"
         "このクリーチャーの下にカードが7枚以下なら、このクリーチャーは離れず、アンタップもしない。"
         "攻撃する時、このクリーチャーの下のカードを1枚、墓地に置いてもよい。"
         "そのカードがクリーチャーなら、そのまま自分の墓地から出す",
    note="殿堂入り（公式ルールではデッキに1枚まで）。"
         "山札から下に置くのは、下が10枚未満の時だけにした（攻撃のたびに1枚減るので8枚を保つための余裕。山札切れも防ぐ）",
    source=W + "《DARK MATERIAL COMPLEX》")


# ================================================================ 異端流し オニカマス
def w_onikamasu(s, i, u):
    """相手が召喚以外の方法でクリーチャーを出した時、そのクリーチャーを持ち主の手札に戻す"""
    if u.c.kind != "C" or u.x.get("summoned"):
        return
    if _opp_watch(s, i, "eb_onikamasu") is None:
        return
    s.ev(f"　異端流し オニカマス：{u.c.name} を持ち主の手札に戻す")
    s.leave(i, u, "hand", by_opp=True)


def tl_onikamasu(s, by, u):
    """相手に選ばれない"""
    return u.k == "eb_onikamasu" and by != owner_of(s, u)


add("eb_onikamasu", "異端流し オニカマス", 2, "W", power=2000, pri=4, races=("mutopia",), roles="dis atk",
    enterwatch=w_onikamasu, tgtlock=tl_onikamasu,
    text="このクリーチャーは相手に選ばれない（相手はこのクリーチャーを攻撃したりブロックしたりはできる）。"
         "相手が召喚以外の方法でクリーチャーをバトルゾーンに出した時、そのクリーチャーを持ち主の手札に戻す",
    note="dmwiki と遊々亭では踏み倒しメタが「相手のターン中」「戻してもよい」と書かれていたが、"
         "このカードの働きからすると常時・強制と読むのが自然なので、ターンを問わず必ず戻す形にした",
    source=W + "《異端流し オニカマス》")


# ================================================================ 奇天烈 シャッフ
def _shuff_nums(s, i):
    """プレイヤー i に今かかっている「選ばれた数字」"""
    return [n for (n, exp) in s.P[1 - i].x.get("shuff", ()) if exp >= s.turn]


def _shuff_pick(s, i):
    """数字の選び方（全デッキ共通の機械的な決まり）：
    相手のバトルゾーンにいるクリーチャーのコストのうち、止めて得が大きいもの。
    相手のクリーチャーが1体もいなければ、相手のマナゾーンでいちばん多いコスト（相手のデッキの山を推し量る）"""
    o = s.P[1 - i]
    sc = {}
    for z in o.board:
        if z.c.kind == "C":
            sc[z.c.cost] = sc.get(z.c.cost, 0) + s.val(z)
    if not sc:
        for k in o.mana:
            c = BY_KEY[k]
            sc[c.cost] = sc.get(c.cost, 0) + 1
    if not sc:
        return 4
    return max(sorted(sc), key=lambda n: (sc[n], n))


def _shuff_lock(s, i, u):
    """数字を1つ選ぶ（次の自分のターンのはじめまで続く）"""
    n = _shuff_pick(s, i)
    p = s.P[i]
    xs = [(a, b) for (a, b) in p.x.get("shuff", ()) if b >= s.turn]
    xs.append((n, s.turn + 1))
    p.x["shuff"] = xs             # 新しい並びを入れる（clone と共有しないように書き換えない）
    s.ev(f"　奇天烈 シャッフ：数字 {n} を選ぶ（相手はコスト{n}の呪文を唱えられず、"
         f"コスト{n}のクリーチャーで攻撃もブロックもできない）")


def lk_shuff(s, i, cost):
    return cost in _shuff_nums(s, i)


def al_shuff(s, i, u):
    return u.c.kind == "C" and u.c.cost in _shuff_nums(s, i)


def bl_shuff(s, u):
    return u.c.kind == "C" and u.c.cost in _shuff_nums(s, owner_of(s, u))


add("eb_shuff", "奇天烈 シャッフ", 4, "W", power=4000, pri=7,
    races=("magiccommand", "command", "greatmechaoh", "invader"), roles="dis",
    enter=_shuff_lock, attack=_shuff_lock, spelllock=lk_shuff, atklock=al_shuff, blocklock=bl_shuff,
    text="このクリーチャーが出た時、および攻撃する時、数字を1つ選ぶ。次の自分のターンのはじめまで、"
         "相手はその数字と同じコストを持つ呪文を唱えられず、"
         "その数字と同じコストを持つクリーチャーで攻撃もブロックもできない",
    source=W + "《奇天烈 シャッフ》")


# ================================================================ 水神 ミヅハノメノカミ
def _steal_etb(s, i, k):
    """相手の山札から墓地に置いたクリーチャーの「出た時」能力を、自分が使う"""
    fn = E.ENTER.get(k)
    if fn is None:
        return
    u = E.U(k)
    u.sick = False
    u.x["summoned"] = False
    s.ev(f"　{BY_KEY[k].name} の「出た時」の能力を自分が使う")
    fn(s, i, u)


def e_mizuhanome(s, i, u):
    """相手は山札の上からクリーチャーが出るまで表向きにし、そのクリーチャーを墓地に置き、山札をシャッフルする。
    自分は、こうして墓地に置いたクリーチャーの「出た時」の能力を使ってもよい"""
    o = s.P[1 - i]
    rest, got = [], None
    while len(o.deck) > 1:
        k = o.deck.pop()
        if BY_KEY[k].kind == "C":
            got = k
            break
        rest.append(k)
    for k in rest:
        o.deck.append(k)
    if rest:
        s.rng.shuffle(o.deck)
    if got is None:
        return
    s.ev(f"　相手の山札から {BY_KEY[got].name} を墓地に置く")
    s.grave_put(1 - i, got)
    s.rng.shuffle(o.deck)
    if not s.over:
        _steal_etb(s, i, got)


def tl_mizuhanome(s, by, u):
    """呪文によって相手に選ばれない（いま呪文を唱えている時だけ働く）"""
    return u.k == "eb_mizuhanome" and by != owner_of(s, u) and s.spc is not None


def gd_mizuhanome(s, di, au, tu):
    """相手のクリーチャーが攻撃するなら、その攻撃先は自分（守る側）が選ぶ。
    選び方は守りの共通の決まりと同じ：バトルに勝てるクリーチャーがいればそれ、
    いなければ、そのまま通すと負ける時だけ、失うのがいちばん安いクリーチャーで受ける"""
    d = s.P[di]
    if not any(z.k == "eb_mizuhanome" for z in d.board):
        return None
    ap = s.power(1 - di, au, True)
    win, cheap = None, None
    for z in d.board:
        if z.c.kind != "C" or z is tu:
            continue
        if s.power(di, z) > ap and au.k != "kuzen":
            if win is None or s.val(z) < s.val(win):
                win = z
        if cheap is None or s.val(z) < s.val(cheap):
            cheap = z
    if win is not None:
        return win
    if tu is None and not d.sh and not d.protect:
        return cheap
    return None


add("eb_mizuhanome", "水神 ミヅハノメノカミ", 5, "W", power=8000, brk=2, blocker=True, pri=8,
    races=("mizugami", "lostcrusader", "dragon"), roles="blk dis rem",
    enter=e_mizuhanome, tstart=e_mizuhanome, tgtlock=tl_mizuhanome, guard=gd_mizuhanome,
    text="ブロッカー、W・ブレイカー。このクリーチャーは、呪文によって相手に選ばれない。"
         "このクリーチャーが出た時、および自分のターンのはじめに、相手は自分の山札の上から"
         "クリーチャーが出るまで表向きにし、そのクリーチャーを墓地に置き、山札をシャッフルする。"
         "自分は、こうして墓地に置いたクリーチャーの「出た時」で始まる能力をすべて使ってもよい。"
         "相手のクリーチャーが攻撃するなら、その攻撃先は自分が選ぶ",
    note="横取りした「出た時」の能力は、他のカードの能力を借りる共通の入口（USEETB）がエンジンにないため、"
         "バトルゾーンにいないカードとして実行している。そのため"
         "「このクリーチャー自身を動かす」部分（自分をアンタップする・自分の下にカードを置く等）は働かない。"
         "また「攻撃先は自分が選ぶ」は、守る側が攻撃先を決め直す差し込み口（ATKRETARGET）がないため"
         "ガードマン（GUARD）で代用しており、攻撃の宣言より後で決まる"
         "（相手は攻撃を宣言する時点では本来の攻撃先を選べる）",
    status="partial", source=W + "《水神 ミヅハノメノカミ》")


# ================================================================ カレイコの黒像
def mr_kaleiko(s, i, k, src):
    """山札からマナゾーンに置かれる時、かわりに墓地に置く"""
    return src == "deck" and any(z.k == "eb_kaleiko" for j in (0, 1) for z in s.P[j].board)


def fx_kaleiko(s, owner, u, i, k, src, summon, res):
    """山札からバトルゾーンに出ようとした時、かわりに墓地に置く"""
    if src == "deck" and res == "ok":
        return "grave"
    return res


add("eb_kaleiko", "カレイコの黒像", 3, "D", kind="T", pri=4, races=("oracle", "rexstars"), roles="dis",
    manarep=mr_kaleiko, fatex=fx_kaleiko,
    text="シンカライズ（このタマシードをクリーチャーであるかのように扱い、この上に進化クリーチャーを置いてもよい）。"
         "いずれかのプレイヤーの山札から、手札以外のゾーンにカードが置かれる時、"
         "かわりにそのプレイヤーはそのカードを墓地に置く",
    note="置き換えられるのは「山札からマナゾーン」と「山札からバトルゾーン」まで。"
         "「山札からシールドゾーン」（シールド追加）は、シールドに置くのを置き換える差し込み口（SHIELDREP）が"
         "エンジンにないので止められない（`shieldin=` は置かれた後の見張りなので、"
         "これで墓地へ送るとシールドが一度置かれてしまい、Zラッシュや「シールドが離れた時」を"
         "誤って誘発させてしまう）",
    status="partial", source=W + "《カレイコの黒像》")
E.SHINKA.add("eb_kaleiko")


# ================================================================ 貴布人 テブルカッケ＝エディ
def e_eddy(s, i, u):
    """出た時、自分の山札の上から3枚を墓地に置いてもよい（墓地から召喚するためのカードをためるので置く）"""
    if len(s.P[i].deck) > 4:
        s.mill(i, 3)


def acts_eddy(s, i, av, cv):
    """超魂X：下にこのカードがあるクリーチャーは「自分のターン中、自分の墓地からクリーチャー1体を召喚してもよい」を得る"""
    if s.manaexec(i):
        return []
    p = s.P[i]
    for z in p.board:
        if z.c.kind != "C" or "eb_eddy" not in z.under or z.x.get("eddyt") == s.turn:
            continue
        best, bv, bn = None, -1, 0
        for k in sorted(set(p.grave)):
            c = BY_KEY[k]
            if c.kind != "C" or (c.evo and not c.neo):
                continue
            n = s.ccost(i, k, av)
            if n > av or (n > 0 and not cv.issuperset(c.civ)):
                continue
            if s.fate(i, k, "grave", True) != "ok":
                continue
            if E.PRI[k] > bv:
                best, bv, bn = k, E.PRI[k], n
        if best is not None:
            return [("x:eddy", z.uid, best, bn)]
    return []


def ap_eddy(s, a):
    i = s.tp
    p = s.P[i]
    z = next((x for x in p.board if x.uid == a[1]), None)
    k = a[2]
    if z is None or k not in p.grave or z.x.get("eddyt") == s.turn:
        return
    z.x["eddyt"] = s.turn
    p.mused += a[3]
    p.grave.remove(k)
    s.ev(f"超魂X：墓地から {BY_KEY[k].name} を召喚（{a[3]}マナ）")
    s.enter(i, k, "grave", True)


add("eb_eddy", "貴布人 テブルカッケ＝エディ", 3, "D", power=3000, pri=4,
    races=("abyssroyal", "fusioner"), roles="rem acc",
    enter=e_eddy, freeacts=acts_eddy, actapply={"x:eddy": ap_eddy},
    text="スレイヤー（バトルする相手のクリーチャーを、パワーに関係なく破壊する）。"
         "出た時、自分の山札の上から3枚を墓地に置いてもよい。"
         "超魂X（このカードがクリーチャーの下にあれば、そのクリーチャーにも以下の能力を与える）："
         "自分のターン中、自分の墓地にあるクリーチャー1体を召喚してもよい",
    note="超魂Xで与える「墓地から召喚」は、下にこのカードがあるクリーチャー1体につき各ターン1回までにした"
         "（回数の上限がカードに書かれておらず、上限なしだと手順が終わらなくなるため）。"
         "このカードを「クリーチャーの下に置く」手順そのものは、"
         "エンジンに「クリーチャーを別のクリーチャーの下に置く」共通の手（PUTUNDER）がないため、"
         "六番龍 シックスフォール Par滝など別のカードの効果で下に置かれた時だけ働く",
    status="partial", source=W + "《貴布人 テブルカッケ＝エディ》")
SLAYER.add("eb_eddy")


# ================================================================ 魔誕翔天マルピア
def e_marupia(s, i, u):
    """出た時、次のうちいずれか1つを選ぶ：①シールドを1つブレイクする　②相手のクリーチャー1体のパワーを-4000

    選び方（共通の決まり）：-4000で破壊できる相手がいればそれを選び、いなければシールドをブレイクする"""
    t = s.target(i, lambda z: s.power(1 - i, z) <= 4000)
    if t is not None:
        _minus_power(s, i, t, 4000)
        return
    if s.P[1 - i].sh:
        s.ev("　魔誕翔天マルピア：シールドを1つブレイクする")
        s.break_sh(i, 1)
        return
    t = s.target(i)
    if t is not None:
        _minus_power(s, i, t, 4000)


add("eb_marupia", "魔誕翔天マルピア", 3, "DF", power=4000, trig=True, pri=4,
    races=("demoncommand", "command", "firebird"), roles="trg rem atk",
    enter=e_marupia,
    text="S・トリガー。このクリーチャーが出た時、次のうちいずれか1つを選ぶ。"
         "①このクリーチャーは、シールドを1つブレイクする。"
         "②相手のクリーチャー1体を選び、このターン、そのパワーを-4000する",
    source=W + "《魔誕翔天マルピア》")


# ================================================================ ピース・盾・ルピア
def e_peaceshield(s, i, u):
    if s.tp != i:               # 相手のターンに出た＝シールドから出た（S・トリガー・プラス）
        s.ev("　S・トリガー・プラス：相手のクリーチャーをすべてタップする")
        for z in s.P[1 - i].board:
            if z.c.kind == "C":
                s.tap_cre(1 - i, z)
    s.dig(i, 3, lambda k: "dragon" in BY_KEY[k].races or _fb(BY_KEY[k]))


add("eb_peaceshield", "ピース・盾・ルピア", 4, "L", power=3500, blocker=True, trig=True, pri=5,
    races=("armoredfirebird", "firebird", "armored"), roles="blk trg draw",
    enter=e_peaceshield,
    text="S・トリガー・プラス（シールドゾーンから使った時は、下の追加の能力も使える）。ブロッカー。"
         "出た時、自分の山札の上から3枚を見て、その中からドラゴンまたはファイアー・バード1枚を手札に加えてもよい。"
         "残りを好きな順序で山札の下に置く。"
         "プラス：シールドゾーンから使っていたら、相手のクリーチャーをすべてタップする",
    source=W + "《ピース・盾・ルピア》")


# ================================================================ 奇石 ミクセル／ジャミング・チャフ
def w_mixel(s, i, u):
    """相手のマナゾーンのカードの枚数よりコストが大きい相手のクリーチャーが出た時、山札の一番下に置く"""
    if u.c.kind != "C" or u.c.cost <= len(s.P[i].mana):
        return
    if _opp_watch(s, i, "eb_mixel") is None:
        return
    s.ev(f"　奇石 ミクセル：{u.c.name} を山札の一番下に置く")
    s.leave(i, u, "deck", by_opp=True)


def sp_mixel(s, i):
    """ジャミング・チャフ（呪文側）"""
    s.P[i].x["chaf"] = s.turn + 1
    s.ev("　ジャミング・チャフ：次の自分のターンのはじめまで、相手は呪文を唱えられない")
    s.draw(i)


def lk_mixel(s, i, cost):
    return s.P[1 - i].x.get("chaf", -1) >= s.turn


add("eb_mixel", "奇石 ミクセル / ジャミング・チャフ", 2, "L", power=2000, twin=(5, "L", False), pri=4,
    races=("metallica",), roles="dis draw",
    enterwatch=w_mixel, spell=sp_mixel, spelllock=lk_mixel,
    text="相手のマナゾーンにあるカードの枚数より大きいコストを持つ相手のクリーチャーがバトルゾーンに出た時、"
         "相手はそのクリーチャーを自分の山札の一番下に置く。"
         "呪文側《ジャミング・チャフ》（光5）：次の自分のターンのはじめまで、相手は呪文を唱えられない。カードを1枚引く",
    source=W + "《奇石 ミクセル／ジャミング・チャフ》")


# ================================================================ 洗打の妖精
def w_scrub(s, i, u):
    """相手のクリーチャーが出た時、それが相手のマナゾーンの枚数よりコストが大きければ持ち主の手札に戻す"""
    if u.c.kind != "C" or u.c.cost <= len(s.P[i].mana):
        return
    if _opp_watch(s, i, "eb_scrub") is None:
        return
    s.ev(f"　洗打の妖精：{u.c.name} を持ち主の手札に戻す")
    s.leave(i, u, "hand", by_opp=True)


add("eb_scrub", "洗打の妖精", 2, "W", power=1000, gs=True, jd=True, pri=3,
    races=("giant", "snow"), roles="dis trg",
    enterwatch=w_scrub,
    text="G・ストライク（相手の攻撃中にシールドゾーンから手札に加える時に見せて、相手のクリーチャー1体を"
         "このターン攻撃できなくする）。ジャストダイバー（出たターン、相手に選ばれず攻撃もされない）。"
         "相手のクリーチャーが出た時、それが相手のマナゾーンにあるカードの枚数より大きいコストを持つなら、"
         "そのクリーチャーを持ち主の手札に戻してもよい",
    source=W + "《洗打の妖精》")


# ================================================================ 葉鳴妖精ハキリ
def px_hakiri(s, i, u, atk):
    """相手のターン中、パワー+4000"""
    return 4000 if s.tp != i else 0


def a_hakiri(s, i, u):
    """攻撃する時、自分のマナゾーンのカードの枚数以下のコストのクリーチャー1体を、手札からコストを支払わずに召喚してもよい"""
    p = s.P[i]
    lim = len(p.mana)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > lim or (c.evo and not c.neo):
            continue
        if s.fate(i, k, "hand", True) != "ok":
            continue
        if E.PRI[k] > bv:
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.hand.remove(best)
    s.ev(f"　葉鳴妖精ハキリ：手札から {BY_KEY[best].name} をコストを支払わずに召喚")
    s.enter(i, best, "hand", True)


add("eb_hakiri", "葉鳴妖精ハキリ", 2, "N", power=2000, pri=5, races=("snow",), roles="atk acc",
    powerx=px_hakiri, attack=a_hakiri,
    text="相手のターン中、このクリーチャーのパワーは+4000される。"
         "このクリーチャーが攻撃する時、自分のマナゾーンにあるカードの枚数以下のコストを持つクリーチャー1体を、"
         "自分の手札からコストを支払わずに召喚してもよい",
    source=W + "《葉鳴妖精ハキリ》")


# ================================================================ ネ申・マニフェスト
def e_manifest(s, i, u):
    s.draw(i, 3)
    for _ in range(2):
        k = worst_hand(s, i)
        if k is None:
            break
        s.discard(i, k)


def w_manifest(s, i, u):
    """シンカパワー：このカードの上に進化クリーチャーが置かれた時、
    次の自分のターンのはじめまで、そのクリーチャーはブロックされず、相手に選ばれない"""
    if u.c.kind == "C" and u.under and u.under[0] == "eb_manifest":
        u.x["mani"] = s.turn + 1
        s.ev("　シンカパワー：次の自分のターンのはじめまで、ブロックされず、相手に選ばれない")


def ub_manifest(s, i, u):
    return u.x.get("mani", -1) >= s.turn


def tl_manifest(s, by, u):
    return u.x.get("mani", -1) >= s.turn and by != owner_of(s, u)


add("eb_manifest", "ネ申・マニフェスト", 3, "W", power=2000, pri=4, races=("trix", "rexstars"), roles="draw atk",
    enter=e_manifest, enterwatch=w_manifest, unbok=ub_manifest, tgtlock=tl_manifest,
    text="出た時、カードを3枚引き、その後、自分の手札を2枚捨てる。"
         "シンカパワー（このカードの上に進化クリーチャーが置かれた時に働く）："
         "次の自分のターンのはじめまで、そのクリーチャーはブロックされず、相手に選ばれない",
    source=W + "《ネ申・マニフェスト》")
