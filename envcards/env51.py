"""担当51：DM26-SD1「ドキドキつよいデッキ 25の王道」の未実装カード15枚

出典：dmwiki.net の各カードページ（1枚につき、本文と生の wiki ソース（?plugin=template）を
      別の質問で2回ずつ読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
      どちらも一致することを確かめた）。

  調べ直して意外だった点
    ・《「必然」の頂 リュウセイ》は単体のカードではなく、ツインパクト
      《「必然」の頂 リュウセイ／「オレの勝利だオフコース！」》だった（担当表の名前は片面だけ）。
      片面の名前で dmwiki を開くと "Spam check failed" が返るので、正式名で開き直して確かめた。
    ・《T・T・T》はコスト3（光／水／火）。3つのモードのうち1つを選ぶ呪文で、
      3つ目は《キリモミ・ヤマアラシ》と同じ「次に召喚するクリーチャーのコストを減らして
      スピードアタッカーを与える」能力（減らす数が3）。この2枚は同じ仕組みを共有させた。
    ・《光鎧龍ホーリーグレイス》は古いカードの再録ではなく、S・トリガーに
      「相手のターンに出て、そのターンに自分のシールドが2つ以上割られていなければ自壊する」
      という現代的な制限が付いている。
    ・《ボルメテウス・サファイア・ドラゴン》はプレミアム殿堂（2007-01-15）→殿堂入り（2015-09-19）
      →殿堂解除（2020-12-18）と動いていて、**いまは制限なし**。

  この札束で使った差し込み口
    ・`spelllock=`（ファイナル・ストップ：次の相手のターンの終わりまで呪文を唱えられない）
    ・`costaura=` ＋ `enterwatch=`（キリモミ・ヤマアラシ／T・T・T の「次に召喚する1体」）
    ・`saok=`（リュウセイ：自分のクリーチャーすべてにスピードアタッカー）
    ・`loserep=`（リュウセイ：負けるかわりに自分のハンターを1つ破壊。各ターン1回）
    ・`breakrep=`（サファイア：ブレイクしたシールドを手札に加えるかわりに墓地へ）
    ・`freeacts=`／`actapply=`（ツインパクト呪文側のコスト軽減。エンジンは
      ツインパクト呪文側のコストを `CARD[k].twin[0]` 固定で見るため、`spcost=` が効かない。
      REQUEST_51.md に書いた）
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move, opp_all, worst_hand, best_hand, free_play
from envcards.env0 import race_like

W = "https://dmwiki.net/"
SRC = {
    "k51_finalstop": W + "《ファイナル・ストップ》",
    "k51_kirimomi": W + "《キリモミ・ヤマアラシ》",
    "k51_ryuen": W + "《最期の竜炎》",
    "k51_yuuai": W + "《勇愛の天秤》",
    "k51_burnfinger": W + "《バーニング・フィンガー》",
    "k51_ttt": W + "《T・T・T》",
    "k51_anno": W + "《庵野水晶》",
    "k51_ryusei": W + "《「必然」の頂 リュウセイ／「オレの勝利だオフコース！」》",
    "k51_bff": W + "《B.F.F. モーメント》",
    "k51_himeouga": W + "《姫と王牙の剣》",
    "k51_vcharon": W + "《Vチャロン》",
    "k51_jenny": W + "《解体人形ジェニー》",
    "k51_holygrace": W + "《光鎧龍ホーリーグレイス》",
    "k51_valkyrias": W + "《超竜ヴァルキリアス》",
    "k51_bolsapphire": W + "《ボルメテウス・サファイア・ドラゴン》",
}
DRA = "dragon"


# ================================================================ 共通の道具
def _elem(s, i, pred=None):
    """相手のエレメント（バトルゾーンのクリーチャー・タマシード・クロスギア）を1つ選ぶ"""
    return s.target(i, pred, kinds="CTX")


def _discard_one(s, i, k):
    """手札の k を捨てる。実際に手札から離れたら True（マッドネスで残ったら False）"""
    if k is None or k not in s.P[i].hand:
        return False
    s.discard(i, k)
    return k not in s.P[i].hand


# ================================================================ 1 ファイナル・ストップ
def sp_finalstop(s, i):
    """次の相手のターンの終わりまで、相手は呪文を唱えられない。カードを1枚引く"""
    o = s.P[1 - i]
    o.x["k51_nospell"] = s.turn + (1 if s.tp == i else 0)
    s.ev("　ファイナル・ストップ：次の相手のターンの終わりまで、相手は呪文を唱えられない")
    s.draw(i, 1)


def sl_finalstop(s, i, cost):
    """全体に効く差し込み口。この札が立てた期限（自分の x）だけを見るので、
    この札が入っていない対戦では必ず False になる"""
    return s.P[i].x.get("k51_nospell", -1) >= s.turn


add("k51_finalstop", "ファイナル・ストップ", 4, "L", kind="S", pri=5, roles="dis draw",
    spell=sp_finalstop, spelllock=sl_finalstop,
    text="次の相手のターンの終わりまで、相手は呪文を唱えられない。その後、カードを1枚引く",
    source=SRC["k51_finalstop"])


# ================================================================ 2 キリモミ・ヤマアラシ（と T・T・T の3つめ）
def _set_cut(s, i, n):
    """「このターン、次に召喚する自分のクリーチャーのコストを n 少なくする」をかける
    （tuple で持つ。list を入れると clone 同士で共有されて盤面が壊れる）"""
    s.P[i].x["k51_cut"] = (s.turn, n)


def _cut(s, i):
    t, n = s.P[i].x.get("k51_cut", (-1, 0))
    return n if t == s.turn else 0


def ca_cut(s, i, k, cur):
    """次に召喚する自分のクリーチャーのコストを少なくする（コストは0以下にならない＝最低1）"""
    n = _cut(s, i)
    if not n or cur <= 1 or BY_KEY[k].kind != "C":
        return cur
    return max(1, cur - n)


def w_cut(s, i, u):
    """そのクリーチャーが出た時、そのターン、そのクリーチャーにスピードアタッカーを与える

    全体に効く差し込み口なので、この2枚が期限を書き込んだ時だけ働く。"""
    if not _cut(s, i) or not u.x.get("summoned") or u.x.get("src") != "hand":
        return
    s.P[i].x["k51_cut"] = (-1, 0)
    u.sa = True
    s.ev(f"　{u.c.name} にスピードアタッカーを与える（キリモミ・ヤマアラシ／T・T・T）")


def sp_kirimomi(s, i):
    _set_cut(s, i, 1)
    s.ev("　キリモミ・ヤマアラシ：次に召喚するクリーチャーのコストを1少なくする")


add("k51_kirimomi", "キリモミ・ヤマアラシ", 1, "F", kind="S", pri=2, roles="acc atk",
    spell=sp_kirimomi, costaura=ca_cut, enterwatch=w_cut,
    text="このターン、次に召喚する自分のクリーチャーのコストを1少なくする（コストは0以下にはならない）。"
         "そのクリーチャーが出た時、このターン、そのクリーチャーに「スピードアタッカー」を与える",
    source=SRC["k51_kirimomi"])


# ================================================================ 3 最期の竜炎
def sp_ryuen(s, i):
    """自分の手札を1枚捨てる。こうして捨てたカード以下のコストの相手のエレメント1つを破壊する

    どれを捨てるかは全デッキ共通の決まりで機械的に決める：
    「その札で壊せる相手のいちばんの値打ち − その札の重要度」がいちばん大きい札を捨てる。
    壊せる相手がいなければ、この式はいちばん安い手札を選ぶ（捨てるのは強制）。"""
    p = s.P[i]
    if not p.hand:
        return
    pick, bv = None, None
    for k in set(p.hand):
        lim = BY_KEY[k].cost
        ts = opp_all(s, i, lambda u: u.c.cost <= lim, kinds="CTX")
        gain = max((s.val(t) for t in ts), default=0) - E.PRI[k]
        if bv is None or gain > bv:
            pick, bv = k, gain
    if pick is None:
        return
    lim = BY_KEY[pick].cost
    if not _discard_one(s, i, pick):
        return
    t = _elem(s, i, lambda u: u.c.cost <= lim)
    if t is None:
        return
    s.ev(f"　最期の竜炎：コスト{lim}以下の {t.c.name} を破壊")
    destroy(s, i, t)


add("k51_ryuen", "最期の竜炎", 1, "F", kind="S", trig=True, pri=3, roles="rem trg",
    spell=sp_ryuen,
    text="S・トリガー。自分の手札を1枚捨てる。こうして捨てたカード以下のコストを持つ相手のエレメント1つを選び、"
         "破壊する（捨てる札は、いちばん値打ちの高い相手のエレメントに手が届く中でいちばん安いものを選ぶ）",
    source=SRC["k51_ryuen"])


# ================================================================ 4 勇愛の天秤
def sp_yuuai(s, i):
    """次のうちいずれか1つを選ぶ：
    ・手札を1枚捨て、その後カードを2枚引く
    ・相手のパワー2000以下のクリーチャーを1体破壊する
    （破壊できる相手がいればそちらを選ぶ、という全デッキ共通の機械的な決め方）"""
    t = s.target(i, lambda u: s.power(1 - i, u) <= 2000)
    if t is not None:
        s.ev(f"　勇愛の天秤：パワー2000以下の {t.c.name} を破壊")
        destroy(s, i, t)
        return
    _discard_one(s, i, worst_hand(s, i))
    s.draw(i, 2)


add("k51_yuuai", "勇愛の天秤", 2, "F", kind="S", trig=True, pri=4, roles="rem draw trg",
    spell=sp_yuuai,
    text="S・トリガー。次のうちいずれか1つを選ぶ："
         "(a)自分の手札を1枚捨て、その後カードを2枚引く／(b)相手のパワー2000以下のクリーチャーを1体破壊する"
         "（パワー2000以下の相手がいれば(b)、いなければ(a)を選ぶ）",
    source=SRC["k51_yuuai"])


# ================================================================ 5 バーニング・フィンガー
def sp_burnfinger(s, i):
    """自分の手札を1枚捨て、カードを2枚引く。
    S・トリガー・プラスで唱えた時（＝相手のターンで、そのターン自分の盾が2つ以上割られている時）は、
    P能力として相手のコスト6以下のエレメント1つも破壊する"""
    plus = s.tp != i and s.P[i].brk_t >= 2
    _discard_one(s, i, worst_hand(s, i))
    s.draw(i, 2)
    if not plus:
        return
    t = _elem(s, i, lambda u: u.c.cost <= 6)
    if t is None:
        return
    s.ev(f"　バーニング・フィンガー（P能力）：コスト6以下の {t.c.name} を破壊")
    destroy(s, i, t)


add("k51_burnfinger", "バーニング・フィンガー", 2, "F", kind="S", trig=True, pri=4, roles="draw rem trg",
    spell=sp_burnfinger,
    text="S・トリガー・プラス（シールドから手札に加える時にただで唱えてよい。それが相手のターンで、"
         "そのターン自分のシールドが2つ以上ブレイクされていれば、P能力も得る）。"
         "自分の手札を1枚捨て、カードを2枚引く。"
         "P−相手のコスト6以下のエレメント1つを選び、破壊する"
         "（相手のターンに唱えられるのはシールドからだけなので、「相手のターン＋盾2つ以上」でP能力の判定をしている）",
    source=SRC["k51_burnfinger"])


# ================================================================ 6 T・T・T
def sp_ttt(s, i):
    """次のうちいずれか1つを選ぶ：相手を3体までタップ／3枚引く／次の召喚のコストを3少なくしてSAを与える

    選び方は全デッキ共通の機械的な決まり：
    アンタップの相手が2体以上いればタップ、
    次の召喚が3軽くなれば手札のクリーチャーに手が届くならコスト軽減、どちらでもなければ3枚引く。"""
    p = s.P[i]
    if sum(1 for u in s.P[1 - i].board if u.c.kind == "C" and not u.tap and not u.jd) >= 2:
        for _ in range(3):
            t = s.target(i, lambda u: not u.tap)
            if t is None:
                break
            s.tap_cre(1 - i, t)
            s.ev(f"　T・T・T：{t.c.name} をタップ")
        return
    av = len(p.mana) - p.mused
    cv = E.civs(p)
    for k in p.hand:
        c = BY_KEY[k]
        if (c.kind == "C" and not (c.evo and not c.neo) and cv.issuperset(c.civ)
                and c.cost > av and max(1, c.cost - 3) <= av):
            _set_cut(s, i, 3)
            s.ev("　T・T・T：次に召喚するクリーチャーのコストを3少なくする")
            return
    s.draw(i, 3)


add("k51_ttt", "T・T・T", 3, "LWF", kind="S", pri=5, roles="dis draw acc",
    spell=sp_ttt, costaura=ca_cut, enterwatch=w_cut,
    text="次のうちいずれか1つを選ぶ："
         "(a)相手のクリーチャーを3体まで選び、タップする／(b)カードを3枚引く／"
         "(c)このターン、次に召喚する自分のクリーチャーのコストを3少なくする（0以下にはならない）。"
         "そのクリーチャーが出た時、このターン、そのクリーチャーに「スピードアタッカー」を与える",
    source=SRC["k51_ttt"])


# ================================================================ 7 庵野水晶
def e_anno(s, i, u):
    s.draw(i, 2)


def at_anno(s, i, u):
    """攻撃する時、コスト6以下の呪文を1枚、手札か墓地からただで唱えてよい。
    唱えた後は墓地のかわりに山札の下へ"""
    p = s.P[i]
    best, bv, src = None, -1, None
    for zone, nm in ((p.hand, "hand"), (p.grave, "grave")):
        for k in sorted(set(zone)):
            c = BY_KEY[k]
            if c.kind != "S" or c.cost > 6 or not s.spell_ok(i, c.cost):
                continue
            if E.PRI[k] > bv:
                best, bv, src = k, E.PRI[k], nm
    if best is None:
        return
    s.ev(f"　庵野水晶：{BY_KEY[best].name} を{'手札' if src == 'hand' else '墓地'}からただで唱える")
    if free_play(s, i, best, src) and best in p.grave:
        p.grave.remove(best)
        p.deck.insert(0, best)
        s.ev(f"　{BY_KEY[best].name} は墓地のかわりに山札の下へ")


add("k51_anno", "庵野水晶", 6, "LWF", power=7000, brk=2, blocker=True, sa=True,
    races=("kingcommanddragon", "command", DRA), pri=9, roles="draw blk atk fin",
    enter=e_anno, attack=at_anno,
    text="ブロッカー、スピードアタッカー、W・ブレイカー。出た時、カードを2枚引く。"
         "攻撃する時、コスト6以下の呪文を1枚、自分の手札または墓地からコストを支払わずに唱えてもよい。"
         "それを唱えた後、墓地のかわりに山札の下に置く（重要度のいちばん高い呪文を選ぶ）",
    source=SRC["k51_anno"])


# ================================================================ 8 「必然」の頂 リュウセイ／「オレの勝利だオフコース！」
KR = "k51_ryusei"


def sa_ryusei(s, i, u):
    """自分のクリーチャーすべてに「スピードアタッカー」を与える（場にいる間だけ）"""
    return u.c.kind == "C" and s.has(i, KR)


def lr_ryusei(s, i, how):
    """各ターンに1度、自分がゲームに負ける時、かわりに自分のハンターを1つ破壊してもよい"""
    if not s.has(i, KR):
        return False
    p = s.P[i]
    if p.x.get("k51_ryusei_t") == s.turn:
        return False
    hs = [z for z in p.board if race_like(z.c, "hunter")]
    if not hs:
        return False
    z = min(hs, key=s.val)
    p.x["k51_ryusei_t"] = s.turn
    s.ev(f"　「必然」の頂 リュウセイ：負けるかわりに {z.c.name} を破壊する")
    s.leave(i, z, "grave", destroy=True)
    return True


def _off_cost(s, i):
    """「オレの勝利だオフコース！」の実際のコスト（相手のクリーチャー1体につき1少ない。最低1）"""
    n = 6 - sum(1 for u in s.P[1 - i].board if u.c.kind == "C")
    return max(1, n)


def sp_offcourse(s, i):
    """パワー4000以下のクリーチャーをすべて破壊する（自分のものも破壊する）"""
    for j in (0, 1):
        for z in s.P[j].board[:]:
            if z.c.kind != "C" or z not in s.P[j].board:
                continue
            if s.power(j, z) <= 4000:
                s.ev(f"　「オレの勝利だオフコース！」：{z.c.name} を破壊")
                s.leave(j, z, "grave", by_opp=(j != i), destroy=True)


def fa_ryusei(s, i, av, cv):
    """ツインパクト呪文側をコスト軽減して唱える追加の手
    （エンジンはツインパクト呪文側のコストを固定で見るので、軽減はここで作る）"""
    p = s.P[i]
    if KR not in p.hand:
        return []
    n = _off_cost(s, i)
    if n >= 6 or n > av or "F" not in cv or not s.spell_ok(i, 6):
        return []
    return [("x:k51_offcourse", n)]


def ap_offcourse(s, a):
    i = s.tp
    p = s.P[i]
    if KR not in p.hand:
        return
    p.hand.remove(KR)
    p.mused += a[1]
    s.ev(f"呪文：「オレの勝利だオフコース！」（呪文側・{a[1]}マナ）")
    s.cast(i, KR, True)


add(KR, "「必然」の頂 リュウセイ／「オレの勝利だオフコース！」", 10, "F", power=12000, brk=3, gs=True,
    races=("redcommanddragon", "command", DRA, "gianthunter", "hunter", "zenith"),
    twin=(6, "F", False), pri=12, roles="fin atk rem",
    spell=sp_offcourse, saok=sa_ryusei, loserep=lr_ryusei,
    freeacts=fa_ryusei, actapply={"x:k51_offcourse": ap_offcourse},
    text="クリーチャー側《「必然」の頂 リュウセイ》（火10・レッド・コマンド・ドラゴン／ジャイアント・ハンター／"
         "ゼニス・12000）：G・ストライク、T・ブレイカー。自分のクリーチャーすべてに「スピードアタッカー」を与える。"
         "各ターンに1度、自分がゲームに負ける時、かわりに自分のハンターを1つ破壊してもよい。"
         "呪文側《「オレの勝利だオフコース！」》（火6）：相手のクリーチャー1体につきこの呪文のコストを1少なくする"
         "（0以下にはならない）。パワー4000以下のクリーチャーをすべて破壊する",
    source=SRC["k51_ryusei"])


# ================================================================ 9 B.F.F. モーメント
def sp_bff(s, i):
    """カードを1枚引く。自分の手札の枚数以下のコストを持つ相手のクリーチャーをすべて手札に戻す"""
    s.draw(i, 1)
    n = len(s.P[i].hand)
    for t in opp_all(s, i, lambda u: u.c.cost <= n):
        if t in s.P[1 - i].board:
            s.ev(f"　B.F.F. モーメント：コスト{t.c.cost}の {t.c.name} を手札へ")
            move(s, i, t, "hand")


add("k51_bff", "B.F.F. モーメント", 6, "W", kind="S", trig=True, pri=7, roles="rem trg draw",
    spell=sp_bff,
    text="S・トリガー。カードを1枚引く。その後、自分の手札の枚数以下のコストを持つ相手のクリーチャーを"
         "すべて、持ち主の手札に戻す（手札の枚数は、引いた後のこの呪文を除いた枚数で数える）",
    source=SRC["k51_bff"])


# ================================================================ 10 姫と王牙の剣
def _give_sa(s, i, skip=None):
    """自分のクリーチャー1体にスピードアタッカーを与える
    （召喚酔いで攻撃できないクリーチャーを優先し、その中でパワーの高いものを選ぶ）"""
    cs = [z for z in s.P[i].board
          if z.c.kind == "C" and z is not skip and not z.sa and not s.kw(z, "sa")]
    if not cs:
        return None
    z = max(cs, key=lambda x: (1 if (x.sick and not x.tap) else 0, s.power(i, x, True)))
    z.sa = True
    s.ev(f"　姫と王牙の剣：{z.c.name} にスピードアタッカーを与える")
    return z


def sp_himeouga(s, i):
    """このターン、自分のクリーチャー1体にスピードアタッカーを与える。
    自分の手札を1枚超次元ゾーンに置いてもよい。そうしたら、真上の能力をもう1度使う

    超次元ゾーンはこのシミュレーターに無いので、「二度と戻らないゾーンへ送る」＝
    手札から取り除いてどこにも置かない、として扱う（ゲーム中の働きは同じ）。"""
    p = s.P[i]
    first = _give_sa(s, i)
    if first is None:
        return
    second = [z for z in p.board if z.c.kind == "C" and z is not first and z.sick and not z.tap
              and not z.sa and not s.kw(z, "sa")]
    if not second or not p.hand:
        return
    k = worst_hand(s, i)
    if k is None:
        return
    p.hand.remove(k)
    s.ev(f"　姫と王牙の剣：{BY_KEY[k].name} を超次元ゾーンへ置き、もう1度使う")
    _give_sa(s, i, skip=first)


add("k51_himeouga", "姫と王牙の剣", 1, "F", kind="S", pri=2, roles="atk",
    spell=sp_himeouga, status="partial",
    note="超次元ゾーンがこのシミュレーターに無いので、2つめの能力の支払い（手札1枚を超次元ゾーンへ）は"
         "「手札から取り除いてどのゾーンにも置かない」で代えている。超次元ゾーンからカードが戻る仕組みは"
         "どこにも無いので働きは同じだが、ゾーンの枚数を数える効果からは見えない",
    text="このターン、自分のクリーチャー1体に「スピードアタッカー」を与える。"
         "自分の手札を1枚超次元ゾーンに置いてもよい。そうしたら、真上の能力をもう1度使う"
         "（召喚酔いのクリーチャーを優先して選ぶ。2体目が居る時だけ手札を支払う）",
    source=SRC["k51_himeouga"])


# ================================================================ 11 Vチャロン
def _vcharon_pick(s, i):
    """どちらのプレイヤーを選ぶか（全デッキ共通の機械的な決まり：
    手札の重要度の合計が大きい側を選ぶ。ただし自分を選ぶのは山札が足りている時だけ）"""
    p, o = s.P[i], s.P[1 - i]
    need = len(p.hand) + len(p.sh) + 2
    mine = sum(E.PRI[k] for k in p.hand)
    opp = sum(E.PRI[k] for k in o.hand)
    if opp >= mine or len(p.deck) < need:
        return 1 - i
    return i


def e_vcharon(s, i, u):
    """出た時、プレイヤーを1人選ぶ。そのプレイヤーは手札をすべて山札の下に置いて同じ枚数引き、
    その後シールドをすべて山札の下に置いて同じ枚数を山札の上からシールド化する"""
    j = _vcharon_pick(s, i)
    p = s.P[j]
    s.ev(f"　Vチャロン：プレイヤー{j} の手札とシールドを引き直させる")
    n = len(p.hand)
    for k in sorted(p.hand, key=E.PRI.get):
        p.deck.insert(0, k)
    del p.hand[:]
    s.draw(j, n)
    m = len(p.sh)
    for idx in range(m - 1, -1, -1):
        if s.over:
            return
        s.take_shield(j, idx, "deck")
    for _ in range(m):
        if s.over or not s.add_shield(j):
            break


add("k51_vcharon", "Vチャロン", 7, "", power=8000, brk=2, races=("jokers",), pri=8, roles="dis shd draw",
    enter=e_vcharon,
    text="無色（ジョーカーズ）。W・ブレイカー。"
         "出た時、プレイヤーを1人選ぶ。そのプレイヤーは自身の手札をすべて好きな順序で山札の下に置き、"
         "同じ枚数のカードを引く。その後、そのプレイヤーは自身のシールドゾーンのカードをすべて好きな順序で"
         "山札の下に置き、同じ枚数のカードを山札の上からシールド化する"
         "（手札の重要度の合計が大きい側を選ぶ。自分を選ぶのは山札が足りている時だけ）",
    source=SRC["k51_vcharon"])


# ================================================================ 12 解体人形ジェニー
def e_jenny51(s, i, u):
    """出た時、相手の手札を見て1枚選び、捨てさせる（重要度のいちばん高い札を選ぶ）"""
    k = best_hand(s, 1 - i)
    if k is None:
        return
    s.ev(f"　解体人形ジェニー：相手の手札の {BY_KEY[k].name} を捨てさせる")
    s.discard(1 - i, k, by_opp=True)


add("k51_jenny", "解体人形ジェニー", 4, "D", power=1000, races=("puppet",), pri=5, roles="dis",
    enter=e_jenny51,
    text="出た時、相手の手札を見て1枚選び、捨てさせる（重要度のいちばん高いカードを選ぶ）",
    source=SRC["k51_jenny"])


# ================================================================ 13 光鎧龍ホーリーグレイス
def e_holygrace(s, i, u):
    """出た時、相手のクリーチャーをすべてタップする。
    相手のターンに出た時、このターンに2つ以上自分のシールドがブレイクされていなければ、これを破壊する"""
    for z in s.P[1 - i].board[:]:
        if z.c.kind == "C" and not z.tap:
            s.tap_cre(1 - i, z)
    s.ev("　光鎧龍ホーリーグレイス：相手のクリーチャーをすべてタップ")
    if s.tp != i and s.P[i].brk_t < 2 and u in s.P[i].board:
        s.ev("　ホーリーグレイス：相手のターンに出て、自分の盾が2つ以上割られていないので自壊")
        s.leave(i, u, "grave", destroy=True)


add("k51_holygrace", "光鎧龍ホーリーグレイス", 6, "L", power=6500, brk=2, trig=True,
    races=("apolloniadragon", "armored", DRA), pri=7, roles="rem trg dis",
    enter=e_holygrace,
    text="S・トリガー、W・ブレイカー。出た時、相手のクリーチャーをすべてタップする。"
         "相手のターンにこのクリーチャーが出た時、このターンに2つ以上自分のシールドがブレイクされていなければ、"
         "このクリーチャーを破壊する",
    source=SRC["k51_holygrace"])


# ================================================================ 14 超竜ヴァルキリアス
def e_valkyrias(s, i, u):
    """出た時、進化ではないドラゴン・クリーチャーを1体、自分のマナゾーンから出してもよい"""
    p = s.P[i]
    cs = [k for k in set(p.mana)
          if BY_KEY[k].kind == "C" and DRA in BY_KEY[k].races and not BY_KEY[k].evo]
    if not cs:
        return
    k = max(cs, key=E.PRI.get)
    if s.fate(i, k, "mana", False) != "ok":
        return
    s.take_mana(i, k)
    s.ev(f"　超竜ヴァルキリアス：マナゾーンから {BY_KEY[k].name} を出す")
    s.enter(i, k, "mana", False)


def pr_valkyrias(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and not BY_KEY[kk].evo
            and "armoreddragon" in BY_KEY[kk].races)
    return None if n >= 4 else "進化元（アーマード・ドラゴン）が4体いない"


add("k51_valkyrias", "超竜ヴァルキリアス", 9, "F", power=13000, brk=3, evo="F",
    races=("armoreddragon", DRA), pri=11, roles="atk fin acc",
    enter=e_valkyrias, evox=lambda s, i, u: "armoreddragon" in u.c.races, playrule=pr_valkyrias,
    text="進化：アーマード・ドラゴン・クリーチャー1体の上に置く。T・ブレイカー。"
         "出た時、進化ではないドラゴン・クリーチャーを1体、自分のマナゾーンから出してもよい"
         "（マナゾーンの重要度のいちばん高いドラゴンを出す）",
    source=SRC["k51_valkyrias"])


# ================================================================ 15 ボルメテウス・サファイア・ドラゴン
KS = "k51_bolsapphire"


def px_sapphire(s, i, u, atk):
    """パワーアタッカー+3000"""
    return 3000 if atk else 0


def br_sapphire(s, ai, di, broken):
    """このクリーチャーがシールドをブレイクする時、相手はそのシールドを手札に加えるかわりに墓地に置く

    全体に効く差し込み口なので、攻撃しているのがこのクリーチャー自身の時だけ働く。"""
    if s.atk is None or s.atk.k != KS or not s.has(ai, KS):
        return False
    for k, up in broken:
        s.shield_to(di, k, up, "grave")
    s.ev("　ボルメテウス・サファイア・ドラゴン：割ったシールドは手札でなく墓地へ")
    return True


add(KS, "ボルメテウス・サファイア・ドラゴン", 10, "F", power=11000, brk=3, sa=True,
    races=("armoreddragon", DRA), pri=12, roles="fin atk",
    powerx=px_sapphire, breakrep=br_sapphire,
    text="スピードアタッカー、パワーアタッカー+3000、T・ブレイカー。"
         "このクリーチャーがシールドをブレイクする時、相手はそのシールドを手札に加えるかわりに墓地に置く"
         "（墓地に置かれるのでS・トリガーもG・ストライクも使われない）。"
         "殿堂の歩み：2007-01-15にプレミアム殿堂、2015-09-19に殿堂入りへ降格、2020-12-18に殿堂解除。"
         "いまは枚数制限なしなので、デッキ構築の制限は付けていない",
    source=SRC["k51_bolsapphire"])
