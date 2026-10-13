"""担当27：DM26-RP2（逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼︎）の未実装カード15枚

  出典：dmwiki.net の各カードページ（通常ページと生の wiki ソース `?plugin=template&refer=…` の2通りを、
        別の質問で1枚ずつ2回読み、コスト・文明・種類・種族・パワー・ブレイク数・能力本文が
        どちらでも一致することを確かめた）。15枚いずれもハイパーモード欄の区切り
        （`BGCOLOR(#cde):|c|`）は無く、ハイパーモードを持つ札は1枚もなかった。

  この15枚は3つのサイクル＋単独4枚でできている（番号は DM26-RP2 の通し番号）
    ・「極◯秘伝◯◯」（31・35・39・43）：コスト3の呪文。
      「アタック・チャンス：〈自分の文明〉のパワー4000以上のクリーチャー」と
      「リサイクル[〈文明〉(4)]（墓地から4マナで唱え、唱えた後は墓地でなく山札の下）」を共通で持つ。
    ・「◯英雄 ◯◯」（32・37・40・44）：コスト5・S・トリガーのコマンド・ドラゴン。
      素のパワーは4000（アワザ＝カーンだけ5000）で、「マナ武装3：自分のマナゾーンに〈文明〉のカードが
      3枚以上あれば、パワー+4000してW・ブレイカーを与える」を共通で持つ。出た時の効果は文明ごとに別。
    ・「鎧亜寄生パラス・◯◯」（34・38・41）：コスト2のロスト・クルセイダー／エイリアン。
      「スペース・チャージ（自分のマナゾーンにカードが置かれた時、そのカードの文明に合うSC能力を使ってもよい）」
      を共通で持つ。SC能力の文明は自分の文明とは別（水の札がSC-火、闇の札がSC-自然、火の札がSC-光）。
    ・単独：30 光器セイント・ガチ・マリア（パワー・ガチンコ・ジャッジでシールドを増やす）、
      33 救済のラクシャ ミルク／42 連射のラクシャ ユキメ（どちらも「シールド・ゴー」持ち）、
      36 熱血の星夜 アバター・イン・ザ・ラブ（自分のクリーチャーを破壊して召喚コスト-4）。

  この弾の新しい（このシミュレーターに無かった）仕組みと、その書き方
    ・パワー・ガチンコ・ジャッジ：互いに山札の上から1枚を表向きにして自分の山札の一番下に置き、
      パワーを比べる。パワーのないカードは0。仕掛けた側は「相手以上」で勝ち（引き分けは無い）。
      env15 の `gachinko`（コストを比べる版）と同じ形で `power_gachinko` を書いた。
    ・アタック・チャンス：`atkwatch=` で、条件に合う自分のクリーチャーが攻撃した時に手札からただで唱える。
    ・リサイクル：`freeacts=`／`actapply=` で「墓地から4マナで唱える」手を追加し、唱えた後は山札の下へ。
    ・シールド・ゴー：`destroyed=` で墓地から表向きのシールドとして置き、`shielddest=` で
      「表向きのままシールドゾーンを離れる時の行き先」を墓地に変える（ブレイクでも効果でも通る。
      1枚ごとに決まるので、ほかのシールド・ゴーの札と同時にブレイクされても取り合いにならない）。
    ・スペース・チャージ：`manain=`（自分のマナゾーンにカードが置かれた時）で、
      置かれたその場で誘発させている（`sc_manain(キー, 文明, 処理)` で3枚分を作っている）。

  調べ直して意外だった点
    ・《光器セイント・ガチ・マリア》は《光器セイント・マリア》系のリメイクに見えるが、ブロッカーを持たない。
      元カードと混同しないよう、キーワード能力の有無だけを聞く質問で3回目の確認をした（能力は1行だけ）。
    ・《凶英雄 アカトクロ》が破壊するのは相手の「アンタップしている」クリーチャー（タップしている方ではない）。
    ・「鎧亜寄生パラス」のSC能力の文明は、そのカード自身の文明とずれている（サイクルだと思って流用すると間違う）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, move
from envcards.env0 import worst_own

W = "https://dmwiki.net/"
SRC = {
    "k27_gachimaria": W + "《光器セイント・ガチ・マリア》",
    "k27_lionel": W + "《極俺秘伝ライオネル・ガード》",
    "k27_cogito": W + "《理英雄 コギトL》",
    "k27_milk": W + "《救済のラクシャ ミルク》",
    "k27_boxer": W + "《鎧亜寄生パラス・ボクサー》",
    "k27_roses": W + "《極智秘伝ローゼス・チューン》",
    "k27_avatar": W + "《熱血の星夜 アバター・イン・ザ・ラブ》",
    "k27_akatokuro": W + "《凶英雄 アカトクロ》",
    "k27_magician": W + "《鎧亜寄生パラス・マジシャン》",
    "k27_suspense": W + "《極呪秘伝サスペンス・マインド》",
    "k27_gaigunshin": W + "《撃英雄 ガイグンシン》",
    "k27_music": W + "《鎧亜寄生パラス・ミュージック》",
    "k27_yukime": W + "《連射のラクシャ ユキメ》",
    "k27_greatcrash": W + "《極命秘伝グレート・クラッシュ》",
    "k27_awaza": W + "《牙英雄 アワザ＝カーン》",
}

CIVNAME = {"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}


# ================================================================ 共通の道具
def power_gachinko(s, i):
    """パワー・ガチンコ・ジャッジを1回行う（i が勝ったら True）。

    互いに自分の山札の上から1枚を表向きにして、自分の山札の一番下に置く。
    そのカードのパワーが相手以上なら、仕掛けた側（i）の勝ち。パワーを持たないカードは0として扱う。
    山札が無い側は0のカードを見せたものとして扱う（引き分けは無い）。"""
    p, o = s.P[i], s.P[1 - i]
    if not p.deck:
        return False
    a = p.deck.pop()
    p.deck.insert(0, a)
    pa = BY_KEY[a].power
    pb, nb = 0, "なし"
    if o.deck:
        b = o.deck.pop()
        o.deck.insert(0, b)
        pb, nb = BY_KEY[b].power, BY_KEY[b].name
    s.ev(f"　パワー・ガチンコ・ジャッジ：{BY_KEY[a].name}({pa}) 対 {nb}({pb})")
    return pa >= pb


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
    """アタック・チャンス：自分の〈civ〉のパワー4000以上のクリーチャーが攻撃した時、
    手札のこの呪文をコストを支払わずに唱えてもよい（効き目がある時だけ使う。手札の複数枚にも働く）"""
    def f(s, i, u):
        p = s.P[i]
        c = BY_KEY[key]
        if u.c.kind != "C" or civ not in u.c.civ:
            return
        if s.power(i, u, True) < 4000:
            return
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


# ---------------------------------------------------------------- マナ武装3（「◯英雄」サイクル）
def _armed(s, i, civ, n=3):
    """マナ武装：自分のマナゾーンに〈civ〉のカードが n 枚以上あるか"""
    return sum(1 for k in s.P[i].mana if civ in E.MCIV[k]) >= n


def hero_px(civ):
    def f(s, i, u, atk):
        return 4000 if _armed(s, i, civ) else 0
    return f


def hero_brk(civ):
    def f(s, i, u):
        return 2 if _armed(s, i, civ) else None
    return f


def _hero_text(civ, body):
    """「◯英雄 ◯◯」の共通の説明文"""
    c = CIVNAME[civ]
    return ("S・トリガー（シールドゾーンから手札に加える時、コストを支払わずにすぐ出してもよい）。"
            + body +
            f"マナ武装3：自分のマナゾーンに{c}のカードが3枚以上あれば、"
            "このクリーチャーのパワーを+4000し、W・ブレイカーを与える")


# ---------------------------------------------------------------- シールド・ゴー
def sgo_destroyed(s, i, u):
    """シールド・ゴー：このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する"""
    p = s.P[i]
    if u.k not in p.grave:
        return
    p.grave.remove(u.k)
    if not s.add_shield(i, u.k, True):
        p.grave.append(u.k)
        return
    s.ev(f"　シールド・ゴー：{u.c.name} を表向きのシールドとして置く")


def sd_sgo(s, i, k, up, dest):
    """シールド・ゴー：表向きのままシールドゾーンを離れる時は、かわりに墓地に置く（shielddest）

    行き先を1枚ごとに決めるので、ほかのシールド・ゴーのカードと同時にブレイクされても、
    どちらもきちんと墓地へ行く（キーごとの差し込み口なので取り合いにならない）。"""
    return "grave" if up else dest


# ---------------------------------------------------------------- スペース・チャージ
def sc_manain(key, civ, fn):
    """スペース・チャージ：自分のマナゾーンにカードが置かれた時（manain）に、
    そのカードの文明が civ を含んでいればSC能力を使う（場にある key 1枚ごとに1回）"""
    def g(s, i, k, src):
        if civ not in E.MCIV.get(k, ""):
            return
        for u in list(s.P[i].board):
            if u.k == key and u.c.kind == "C" and u in s.P[i].board and not s.over:
                fn(s, i, u, k)
    return g


# ---------------------------------------------------------------- パワード・ブロッカー
PB = {"k27_boxer": 8000}


def _bl_mark(s, u):
    """ブロックできるかを調べられた時に印をつける（「ブロック中」を知るため。ブロックは止めない）。
    can_block は choose_block から、まだアンタップしているブロッカー候補について呼ばれる"""
    if u.k in PB and s.atk is not None and u.c.kind == "C" and not u.tap:
        u.x["k27_pb"] = (s.turn, s.atk.uid)
    return False


def _px_pb(s, i, u, atk):
    """パワード・ブロッカー：ブロック中だけパワーを+する"""
    if u.k not in PB or s.atk is None:
        return 0
    return PB[u.k] if u.x.get("k27_pb") == (s.turn, s.atk.uid) else 0


# ================================================================ 30/77 光器セイント・ガチ・マリア
def ts_gachimaria(s, i, u):
    """自分のターンのはじめに、相手とパワー・ガチンコ・ジャッジする。勝ったら山札の上1枚をシールド化"""
    if not power_gachinko(s, i):
        return
    if s.add_shield(i):
        s.ev("　ガチ・マリア：勝ったので山札の上から1枚をシールド化")


add("k27_gachimaria", "光器セイント・ガチ・マリア", 2, "L", power=2500,
    races=("mechadelsol", "hunter"), pri=3, roles="shd",
    tstart=ts_gachimaria,
    text="自分のターンのはじめに、相手とパワー・ガチンコ・ジャッジしてもよい。勝ったら、"
         "自分の山札の上から1枚を新しいシールドとして置く"
         "（パワー・ガチンコ・ジャッジ：互いに自分の山札の上から1枚を表向きにして自分の山札の一番下に置き、"
         "自分のカードのパワーが相手以上なら自分の勝ち。パワーを持たないカードは0として扱う）。"
         "損はしないので毎ターン必ず行う。元になった《光器セイント・マリア》と違い、ブロッカーは持たない",
    source=SRC["k27_gachimaria"])


# ================================================================ 31/77 極俺秘伝ライオネル・ガード
def sp_lionel(s, i):
    s.add_shield(i)


def _u_lionel(s, i):
    return len(s.P[i].deck) > 1


add("k27_lionel", "極俺秘伝ライオネル・ガード", 3, "L", kind="S", pri=4, roles="shd",
    spell=sp_lionel, atkwatch=ac_watch("k27_lionel", "L", _u_lionel),
    freeacts=rc_acts("k27_lionel", "L"), actapply={"x:k27_lionel": rc_apply("k27_lionel", "L")},
    text=_hiden_text("L", "自分の山札の上から1枚を新しいシールドとして置く。"),
    source=SRC["k27_lionel"])


# ================================================================ 32/77 理英雄 コギトL
def en_cogito(s, i, u):
    """出た時、相手のクリーチャーを2体まで選び、持ち主の手札に戻す"""
    for _ in range(2):
        if s.over:
            return
        t = s.target(i)
        if t is None:
            return
        s.ev(f"　コギトL：{t.c.name} を持ち主の手札へ")
        move(s, i, t, "hand")


add("k27_cogito", "理英雄 コギトL", 5, "W", power=4000, trig=True,
    races=("crystalcommand", "command", "dragon"), pri=7, roles="rem trg",
    enter=en_cogito, powerx=hero_px("W"), brkx=hero_brk("W"),
    text=_hero_text("W", "出た時、相手のクリーチャーを2体まで選び、持ち主の手札に戻す"
                         "（相手のいちばん重要なクリーチャーから選ぶ）。"),
    source=SRC["k27_cogito"])


# ================================================================ 33/77 救済のラクシャ ミルク
def mp_milk(s, by, cands):
    """相手がクリーチャーを選ぶなら、可能ならミルクを選ぶ（mustpick）

    cands は相手の効果の条件（pred）で絞り終えた候補なので、
    「パワー3000以下を選ぶ」のようにミルクが条件に合わない時は横取りせず、
    相手は本来どおり自由に選べる（これが「可能なら」の意味）。"""
    for u in cands:
        if u.k == "k27_milk":
            return u
    return None


add("k27_milk", "救済のラクシャ ミルク", 3, "W", power=3000,
    races=("oracle", "humanoid"), pri=4, roles="blk shd",
    mustpick=mp_milk, destroyed=sgo_destroyed, shielddest=sd_sgo,
    text="相手がクリーチャーを選ぶなら、可能ならこのクリーチャーを選ぶ。"
         "シールド・ゴー（このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する。"
         "表向きのままシールドゾーンを離れる時は、かわりに墓地に置く）",
    source=SRC["k27_milk"])


# ================================================================ 34/77 鎧亜寄生パラス・ボクサー
def _atk_ready(s, i, u):
    """u はいま攻撃できるか（legal_attack と同じ条件。攻撃先があるかは見ない）"""
    c = u.c
    if c.kind != "C" or u.tap:
        return False
    ign = bool(E.NOATKIGN) and any(f(s, i, u) for f in E.NOATKIGN)
    if (c.noatk and not ign) or (u.lock == s.turn and not ign):
        return False
    if (u.k in E.CANTATK and E.CANTATK[u.k](s, i, u)) or any(f(s, i, u) for f in E.ATKLOCK):
        return False
    full = ((not u.sick) or u.sa or c.sa or s.has(i, "jaouga") or bool(c.evo and u.under)
            or bool(E.SAOK and any(f(s, i, u) for f in E.SAOK)))
    mf = u.sick and (c.mach or (u.k == "dagra" and u.hyper)
                     or bool(E.MACHOK and any(f(s, i, u) for f in E.MACHOK)))
    return full or mf


def sc_boxer(s, i, u, k):
    """SC-火：相手のクリーチャー1体を選ぶ。次の自分のターンのはじめまで、それは可能なら攻撃する"""
    t = s.target(i)
    if t is None:
        return
    t.x["k27_must"] = s.turn + (1 if s.tp == i else 0)
    s.ev(f"　SC-火：{t.c.name} は次の自分のターンのはじめまで、可能なら攻撃する")


def ma_boxer(s, i):
    """攻撃の強制：強制されているクリーチャーが攻撃できる間は、ターンを終えられない"""
    for u in s.P[i].board:
        if u.x.get("k27_must", -1) >= s.turn and _atk_ready(s, i, u):
            return True
    return False


add("k27_boxer", "鎧亜寄生パラス・ボクサー", 2, "W", power=1000, blocker=True,
    races=("lostcrusader", "alien"), pri=3, roles="blk dis",
    blocklock=_bl_mark, powerx=_px_pb,
    manain=sc_manain("k27_boxer", "F", sc_boxer), mustatk=ma_boxer,
    text="ブロッカー。パワード・ブロッカー+8000（ブロック中、このクリーチャーのパワーを+8000する）。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、そのカードの文明に合うSC能力を使ってもよい）。"
         "SC-火：相手のクリーチャーを1体選ぶ。次の自分のターンのはじめまで、そのクリーチャーは可能なら攻撃する",
    note="SC-火の「可能なら攻撃する」は、エンジンの攻撃の強制がプレイヤー単位"
         "（攻撃できるクリーチャーがいる間ターンを終えられない）なので、"
         "「選ばれたクリーチャーが攻撃できる間、その持ち主はターンを終えられない」と書いた。"
         "そのため、持ち主がほかのクリーチャーで攻撃してもターンを終えられてしまい、"
         "選ばれたクリーチャーが必ず攻撃するとは限らない（クリーチャー1体ごとの強制の差し込み口がまだ無い）",
    status="partial", source=SRC["k27_boxer"])


# ================================================================ 35/77 極智秘伝ローゼス・チューン
def sp_roses(s, i):
    """カードを3枚引き、自分の手札を2枚、好きな順序で山札の上に置く
    （いちばん要らない2枚を戻し、そのうちまだ使える方を上に＝先に引く側に置く）"""
    p = s.P[i]
    s.draw(i, 3)
    sel = []
    for _ in range(2):
        if not p.hand or s.over:
            break
        k = min(p.hand, key=E.PRI.get)
        p.hand.remove(k)
        sel.append(k)
    for k in sel:
        s.put_zone(i, k, "decktop")
    if sel:
        s.ev(f"　ローゼス・チューン：手札{len(sel)}枚を山札の上に置く")


def _u_roses(s, i):
    return len(s.P[i].deck) >= 3


add("k27_roses", "極智秘伝ローゼス・チューン", 3, "W", kind="S", pri=4, roles="draw",
    spell=sp_roses, atkwatch=ac_watch("k27_roses", "W", _u_roses),
    freeacts=rc_acts("k27_roses", "W"), actapply={"x:k27_roses": rc_apply("k27_roses", "W")},
    text=_hiden_text("W", "カードを3枚引き、自分の手札を2枚、好きな順序で山札の上に置く"
                          "（いちばん要らない2枚を戻し、そのうちまだ使える方を上に置く）。"),
    source=SRC["k27_roses"])


# ================================================================ 36/77 熱血の星夜 アバター・イン・ザ・ラブ
def cx_avatar(s, i, av):
    """召喚する時、自分のクリーチャーを1体破壊してもよい。そうしたら召喚コストを4少なくする
    （払えるならそのまま払い、足りない時だけ破壊する）"""
    p = s.P[i]
    base = BY_KEY["k27_avatar"].cost
    if base <= av or worst_own(s, i) is None or base - 4 > av:
        p.x["k27_av"] = (s.turn, 0)
        return base
    p.x["k27_av"] = (s.turn, 1)
    return base - 4


def py_avatar(s, i, k, n):
    rec = s.P[i].x.get("k27_av")
    if rec is None or rec[0] != s.turn or not rec[1]:
        return
    z = worst_own(s, i)
    if z is None:
        return
    s.ev(f"　アバター・イン・ザ・ラブ：自分の {z.c.name} を破壊して召喚コストを4少なくする")
    s.leave(i, z, "grave", destroy=True)


add("k27_avatar", "熱血の星夜 アバター・イン・ザ・ラブ", 7, "D", power=8000, brk=2, blocker=True,
    races=("angelcommand", "command", "unknown"), pri=9, roles="blk fin",
    costx=cx_avatar, payx=py_avatar,
    text="このクリーチャーを召喚する時、自分のクリーチャーを1体破壊してもよい。そうしたら、"
         "このクリーチャーの召喚コストを4少なくする"
         "（7マナ払えるならそのまま召喚し、足りない時だけ、失うのがいちばん安い自分のクリーチャーを破壊する）。"
         "ブロッカー。W・ブレイカー",
    source=SRC["k27_avatar"])


# ================================================================ 37/77 凶英雄 アカトクロ
def en_akatokuro(s, i, u):
    """出た時、相手のアンタップしているクリーチャーを1体選び、破壊する"""
    t = s.target(i, lambda x: not x.tap)
    if t is None:
        return
    s.ev(f"　アカトクロ：アンタップしている {t.c.name} を破壊")
    destroy(s, i, t)


add("k27_akatokuro", "凶英雄 アカトクロ", 5, "D", power=4000, trig=True,
    races=("demoncommand", "command", "dragon"), pri=7, roles="rem trg",
    enter=en_akatokuro, powerx=hero_px("D"), brkx=hero_brk("D"),
    text=_hero_text("D", "出た時、相手のアンタップしているクリーチャーを1体選び、破壊する"
                         "（相手のいちばん重要なものを選ぶ）。"),
    source=SRC["k27_akatokuro"])


# ================================================================ 38/77 鎧亜寄生パラス・マジシャン
def sc_magician(s, i, u, k):
    """SC-自然：自分のシールドを1つマナゾーンに置いてもよい（各ターン1度）"""
    p = s.P[i]
    if u.x.get("k27_sc") == s.turn or len(p.sh) < 2:
        return
    for j in range(len(p.sh) - 1, -1, -1):
        if p.sh[j][1]:
            continue
        u.x["k27_sc"] = s.turn              # 先に立てる（マナに置くとSCがまた誘発するため）
        kk = p.sh[j][0]
        s.take_shield(i, j, "mana")         # シールドゾーンの出口はここ1か所
        s.ev(f"　SC-自然：シールド1つ（{BY_KEY[kk].name}）をマナゾーンへ")
        return


add("k27_magician", "鎧亜寄生パラス・マジシャン", 2, "D", power=2000, gs=True,
    races=("lostcrusader", "alien"), pri=3, roles="acc trg",
    manain=sc_manain("k27_magician", "N", sc_magician),
    text="G・ストライク（このカードをシールドゾーンから手札に加える時、表向きにして相手のクリーチャー1体を"
         "選んでもよい。このターン、そのクリーチャーは攻撃できない）。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、そのカードの文明に合うSC能力を使ってもよい）。"
         "SC-自然：自分のシールドを1つマナゾーンに置いてもよい。この能力は各ターン1度しか使えない"
         "（シールドが2つ以上ある時だけ、裏向きのシールドを1つマナゾーンに置く）",
    source=SRC["k27_magician"])


# ================================================================ 39/77 極呪秘伝サスペンス・マインド
def sp_suspense(s, i):
    s.discard_random(1 - i)


def _u_suspense(s, i):
    return bool(s.P[1 - i].hand)


add("k27_suspense", "極呪秘伝サスペンス・マインド", 3, "D", kind="S", pri=4, roles="dis",
    spell=sp_suspense, atkwatch=ac_watch("k27_suspense", "D", _u_suspense),
    freeacts=rc_acts("k27_suspense", "D"), actapply={"x:k27_suspense": rc_apply("k27_suspense", "D")},
    text=_hiden_text("D", "相手の手札を1枚、見ないで選んで捨てさせる（無作為に1枚）。"),
    source=SRC["k27_suspense"])


# ================================================================ 40/77 撃英雄 ガイグンシン
def en_gaigunshin(s, i, u):
    """出た時、パワーの合計がこのクリーチャーのパワー以下になるように相手のクリーチャーを好きな数選び、破壊する"""
    budget = s.power(i, u)
    for _ in range(8):
        if s.over:
            return
        t = s.target(i, lambda x: s.power(1 - i, x) <= budget)
        if t is None:
            return
        budget -= s.power(1 - i, t)
        s.ev(f"　ガイグンシン：{t.c.name} を破壊（残りパワー{budget}）")
        destroy(s, i, t)


add("k27_gaigunshin", "撃英雄 ガイグンシン", 5, "F", power=4000, trig=True,
    races=("gaialcommand", "command", "dragon"), pri=8, roles="rem trg",
    enter=en_gaigunshin, powerx=hero_px("F"), brkx=hero_brk("F"),
    text=_hero_text("F", "出た時、パワーの合計がこのクリーチャーのパワー以下になるように相手のクリーチャーを"
                         "好きな数選び、破壊する（相手のいちばん重要なクリーチャーから、"
                         "パワーの合計が収まる範囲で順に選ぶ）。"),
    source=SRC["k27_gaigunshin"])


# ================================================================ 41/77 鎧亜寄生パラス・ミュージック
def px_music(s, i, u, atk):
    """バトル中のパワー+3000（攻撃側のパワーとして見られる時はここで足す）"""
    return 3000 if atk else 0


def bfx_music(s, ai, au, di, du, a_dies, d_dies):
    """バトル中のパワー+3000（守る側として見られる時。ほかのバトル補正＝スレイヤー等は壊さない）"""
    if du.k != "k27_music":
        return a_dies, d_dies
    ap = s.power(ai, au, True) + (2000 if au.k == "testa" else 0)
    dp0 = s.power(di, du) + (2000 if du.k == "testa" else 0)
    dp = dp0 + 3000
    ba = ap <= dp0 or du.k == "kuzen"
    bd = dp0 <= ap or au.k == "kuzen"
    na = ap <= dp or du.k == "kuzen"
    nd = dp <= ap or au.k == "kuzen"
    return (a_dies if a_dies != ba else na), (d_dies if d_dies != bd else nd)


def sc_music(s, i, u, k):
    """SC-光：相手のクリーチャーを1体選び、タップする。次の自分のターンのはじめまでアンタップしない"""
    t = s.target(i, lambda x: not x.tap) or s.target(i)
    if t is None:
        return
    s.tap_cre(1 - i, t)
    t.frz = 1
    s.ev(f"　SC-光：{t.c.name} をタップし、次の自分のターンのはじめまでアンタップしない")


add("k27_music", "鎧亜寄生パラス・ミュージック", 2, "F", power=2000,
    races=("lostcrusader", "alien"), pri=3, roles="dis atk",
    powerx=px_music, battlefx=bfx_music, manain=sc_manain("k27_music", "L", sc_music),
    text="バトル中、このクリーチャーのパワーを+3000する。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、そのカードの文明に合うSC能力を使ってもよい）。"
         "SC-光：相手のクリーチャーを1体選び、タップする。"
         "次の自分のターンのはじめまで、そのクリーチャーはアンタップしない",
    source=SRC["k27_music"])


# ================================================================ 42/77 連射のラクシャ ユキメ
def en_yukime(s, i, u):
    """出た時、相手とパワー・ガチンコ・ジャッジする。負けたらこのクリーチャーを破壊する"""
    if power_gachinko(s, i):
        s.ev("　ユキメ：パワー・ガチンコ・ジャッジに勝ったので場に残る")
        return
    s.ev("　ユキメ：パワー・ガチンコ・ジャッジに負けたので破壊される")
    s.leave(i, u, "grave", destroy=True)


add("k27_yukime", "連射のラクシャ ユキメ", 1, "F", power=4000,
    races=("oracle", "humanoid"), pri=4, roles="atk",
    enter=en_yukime, destroyed=sgo_destroyed, shielddest=sd_sgo,
    text="このクリーチャーが出た時、相手とパワー・ガチンコ・ジャッジする（任意ではない）。"
         "自分が負けたら、このクリーチャーを破壊する。"
         "シールド・ゴー（このクリーチャーが破壊された時、自分の墓地から表向きでシールド化する。"
         "表向きのままシールドゾーンを離れる時は、かわりに墓地に置く）",
    source=SRC["k27_yukime"])


# ================================================================ 43/77 極命秘伝グレート・クラッシュ
def sp_greatcrash(s, i):
    t = s.target(i, lambda x: s.power(1 - i, x) <= 5000)
    if t is None:
        return
    s.ev(f"　グレート・クラッシュ：{t.c.name} を破壊")
    destroy(s, i, t)


def _u_greatcrash(s, i):
    return s.target(i, lambda x: s.power(1 - i, x) <= 5000) is not None


add("k27_greatcrash", "極命秘伝グレート・クラッシュ", 3, "F", kind="S", pri=5, roles="rem",
    spell=sp_greatcrash, atkwatch=ac_watch("k27_greatcrash", "F", _u_greatcrash),
    freeacts=rc_acts("k27_greatcrash", "F"), actapply={"x:k27_greatcrash": rc_apply("k27_greatcrash", "F")},
    text=_hiden_text("F", "相手のパワー5000以下のクリーチャーを1体選び、破壊する"
                          "（相手のいちばん重要なものを選ぶ）。"),
    source=SRC["k27_greatcrash"])


# ================================================================ 44/77 牙英雄 アワザ＝カーン
def en_awaza(s, i, u):
    """このクリーチャーをタップして出してもよい
    （タップしていないと相手に攻撃されないので、攻撃を引き受ける3つめの能力が働かない。
      出たターンはどちらでも攻撃できないため、必ずタップして出す。
      「タップして出る」のは自分でタップするのとは違うので、タップした時の誘発は起こさない）"""
    u.tap = True
    s.ev("　アワザ＝カーン：タップして出る")


def _mf(s, i, u):
    """u がマッハファイター（タップしていないクリーチャーも攻撃できる）として攻撃しているか"""
    return bool(u.sick and (u.c.mach or (u.k == "dagra" and u.hyper)
                            or (E.MACHOK and any(f(s, i, u) for f in E.MACHOK))))


def _awaza_tgt(s, i, u):
    """攻撃しようとしているクリーチャー u が、いま攻撃できる《牙英雄 アワザ＝カーン》（なければ None）"""
    mf = None
    ap = None
    for z in s.P[1 - i].board:
        if z.k != "k27_awaza" or z.c.kind != "C" or z.jd:
            continue
        if mf is None:
            mf, ap = _mf(s, i, u), s.power(i, u, True)
        if not z.tap and not mf:
            continue
        if s.power(1 - i, z) > ap:
            continue
        return z
    return None


def atl_awaza(s, i, u, t):
    """相手のクリーチャーが攻撃するなら、可能ならアワザ＝カーンを攻撃する（ほかのクリーチャーは攻撃できない）"""
    if t.k == "k27_awaza":
        return False
    return _awaza_tgt(s, i, u) is not None


def nop_awaza(s, i, u):
    """アワザ＝カーンを攻撃できるなら、プレイヤーは攻撃できない"""
    return _awaza_tgt(s, i, u) is not None


add("k27_awaza", "牙英雄 アワザ＝カーン", 5, "N", power=5000, trig=True,
    races=("jurassiccommand", "command", "dragon"), pri=8, roles="blk trg",
    enter=en_awaza, atktargetlock=atl_awaza, noatkplock=nop_awaza,
    powerx=hero_px("N"), brkx=hero_brk("N"),
    text=_hero_text("N", "このクリーチャーをタップして出してもよい（攻撃を引き受けるために必ずタップして出す）。"
                         "相手のクリーチャーが攻撃するなら、可能ならこのクリーチャーを攻撃する"
                         "（このクリーチャーを攻撃できる相手のクリーチャーは、"
                         "ほかのクリーチャーもプレイヤーも攻撃できない）。"),
    source=SRC["k27_awaza"])
