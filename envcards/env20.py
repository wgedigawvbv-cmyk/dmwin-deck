"""担当20：DM26-RP1（逆札篇 第1弾 逆転神VS切札竜）の未実装カード15枚

出典：dmwiki.net の各カードページ（https://dmwiki.net/《カード名》）。
      1枚ずつ、別の質問で2回読み（通常ページと PukiWiki の template プラグインで取れる生の wiki ソース）、
      コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が一致することを確かめた。
      突き合わせで分かった食い違い：
        ・《邪眼鎧悪ロマノフⅣ世》は1回目の読みで「ブロッカー」が落ちていた（生ソースに ''ブロッカー'' があった）。
        ・《爆焔ジェット・メモッタ》の山札の上から召喚は、カードの本文に回数制限が書かれていないが、
          dmwiki の解説とタグが「各ターンに1度だけ」としている。それに従って各ターン1回で実装した。
        ・《傀儡秘宝ベンゾルス》の墓地召喚も同じで、本文は「自分のターン中」だけ、解説は「ターン1」。
          各ターン1回で実装した。

  この弾の新しい仕組み（この担当分に出てきたもの）
    ・Zラッシュ＋ハイパーモード（ヘヴィ・ウィン・メタル／パロロ／ボルメテウス・ソル）
    ・自分のシールドを自分でブレイクして「逆転」の条件を作る（ブライゼジェネレイド）
    ・G城（ザ・ラムーン／ジ・オリジナル）。シールドの下にカードを置いて1つのシールドとして扱う
    ・シールド・フォース（インビンシブル・ギャラクシー）
    ・手札進化（エクストリーム・キリコ）
    ・パワード・ブレイカー（ボルバルザーク・紫電／レオパルズ・ホーン）
    ・クロスギアの自動クロス（シデンズ・ソウル）

  シールドゾーンの出入りは、エンジンの `shieldin=` / `shieldout=` で受けている
  （ザ・ラムーン／ジ・オリジナル／ロマノフⅣ世／霊騎ガルテオ）。
  シールドを離す時は必ず `s.take_shield` を通すこと（`p.sh` を直接いじると上の2つが通らない）。
  残っている見回りは《二重のA ボルバルザーク・紫電》の「アンタップした時」だけ
  （エンジンに「アンタップした時」の差し込み口がないため）。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move, opp_all
from envcards.env0 import worst_own

W = "https://dmwiki.net/"
SRC = {
    "k20_heavywin": W + "《逆転龍神ヘヴィ・ウィン・メタル》",
    "k20_galaxy": W + "《叡智のW インビンシブル・ギャラクシー》",
    "k20_kiriko": W + "《偉形のX エクストリーム・キリコ》",
    "k20_braize": W + "《冥幽のU ブライゼジェネレイド》",
    "k20_ramoon": W + "《神羅の銀月 ザ・ラムーン》",
    "k20_origin": W + "《神帝の黒月 ジ・オリジナル》",
    "k20_benzols": W + "《傀儡秘宝ベンゾルス》",
    "k20_memotta": W + "《爆焔ジェット・メモッタ》",
    "k20_shiden": W + "《二重のA ボルバルザーク・紫電》",
    "k20_leopard": W + "《圧倒するレオパルズ・ホーン》",
    "k20_romanov4": W + "《邪眼鎧悪ロマノフⅣ世》",
    "k20_shidens": W + "《聖竜鎧 シデンズ・ソウル》",
    "k20_paroro": W + "《魅神のG パロロ》",
    "k20_galteo": W + "《霊騎ガルテオ》",
    "k20_bolsol": W + "《戦技の炎 ボルメテウス・ソル》",
}

_DEPTH = [0]            # 見回りの入れ子を止める安全装置
_BRKD = [0]             # 自分のクリーチャーが破壊されるたびのブレイクの入れ子を止める安全装置


# ================================================================ 共通の道具
def _castle(s, i, key):
    """key のG城が、プレイヤー i のシールドゾーンに表向きで置かれているか"""
    for k, up in s.P[i].sh:
        if up and k == key:
            return True
    return False


def _ncastle(s, i, key):
    """key のG城が、表向きのシールドとして何枚置かれているか"""
    return sum(1 for k, up in s.P[i].sh if up and k == key)


def _board(s, i, key):
    return [u for u in s.P[i].board if u.k == key]


def _worst_hand_card(s, i):
    p = s.P[i]
    return min(p.hand, key=E.PRI.get) if p.hand else None


def _take_shield(s, i, up=False, best=True):
    """自分のシールド1つを手札に加える（S・トリガーは使わない）。up=False なら表向きのカードを含まないシールドから選ぶ。
    どのシールドを取るかは全デッキ共通の決まりで、いちばん重要度の高いカードを取る。
    シールドゾーンの出口は `s.take_shield` の1か所なので、必ずそれを通す
    （表向きのG城だけは、離れる時かわりに墓地へ置くという決まりに従う）"""
    p = s.P[i]
    cand = [j for j, (k, u) in enumerate(p.sh) if (u == up or up is None)]
    if not cand:
        return None
    plain = [j for j in cand if not (p.sh[j][1] and BY_KEY[p.sh[j][0]].kind == "G")]
    cand = plain or cand                     # 墓地に行ってしまう表向きのG城は、ほかにあれば避ける
    j = (max if best else min)(cand, key=lambda x: E.PRI[p.sh[x][0]])
    k, upj = p.sh[j]
    dest = "grave" if (upj and BY_KEY[k].kind == "G") else "hand"
    r = s.take_shield(i, j, dest)
    return None if r is None else k


def _free_element(s, i, mx, skip=None):
    """手札からコストを支払わずに使えるエレメント（コスト mx 以下）のうち、いちばん重要度の高いもの"""
    p = s.P[i]
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if k == skip or c.cost > mx or E.PRI[k] <= bv:
            continue
        if c.kind == "C":
            if (c.evo and not c.neo) or s.fate(i, k, "hand", False) != "ok":
                continue
        elif c.kind == "S":
            if not s.spell_ok(i, c.cost):
                continue
        elif c.kind == "G":
            if s.tp == i and s.has(1 - i, "fujin"):
                continue
        best, bv = k, E.PRI[k]
    return best


# ================================================================ シールドゾーンの出入り（shieldin= / shieldout=）
def _si_20(s, i, k, up):
    """カードがプレイヤー i のシールドゾーンに置かれた時（表向きだけを見る）"""
    if not up or s.over:
        return
    if k == "k20_ramoon":
        _ramoon_place(s, i)
    if k == "k20_origin" and not s.over:
        _origin_fire(s, i)
    if not s.over:
        _romanov_fire(s, i)          # 表向きのカードが置かれた：ロマノフⅣ世（場にいなければ何もしない）


def _so_20(s, i, k, up, dest):
    """カードがプレイヤー i のシールドゾーンを離れた時（dest＝"break" ならブレイク）"""
    if s.over:
        return
    if up and k == "k20_ramoon":
        _ramoon_under(s, i, dest)
    if up and k == "k20_origin" and not s.over:
        _origin_fire(s, i)
    if not s.over:
        _galteo_fire(s, i)           # シールドゾーンを離れた：霊騎ガルテオ（場にいなければ何もしない）


# ---------------------------------------------------------------- 見回り（「アンタップした時」だけ）
def _poll(s):
    """「アンタップした時」を、タップの状態の変化から気づく
    （エンジンに「アンタップした時」の差し込み口がないため、紫電のためだけに残してある）"""
    if s.over or _DEPTH[0] > 6:
        return
    _DEPTH[0] += 1
    try:
        for j in (0, 1):
            _poll_untap(s, j)
    finally:
        _DEPTH[0] -= 1


def _poll_untap(s, j):
    for u in s.P[j].board:
        if u.k != "k20_shiden":
            continue
        was = u.x.get("k20_wastap")
        u.x["k20_wastap"] = u.tap
        if was and not u.tap:
            _shiden_untapped(s, j, u)


# ---------------------------------------------------------------- 全体にかかる差し込み口（1か所ずつ登録）
def _w_enter(s, i, u):
    _shidens_on_enter(s, i, u)
    _poll(s)


def _w_leave(s, i, u, dest, destroy_):
    if destroy_ and u.c.kind == "C":
        _heavywin_onkill(s, i)
        for z in _board(s, i, "k20_braize"):
            z.tap = False
    _poll(s)


def _w_tstart(s, i, u):
    _poll(s)


def _w_break(s, ai, di, n):
    """ブレイクの後：ザ・ラムーンの下から手札に加わったカードのS・トリガーを使う"""
    for j in (ai, di):
        q = s.P[j].x.get("k20_ramq")
        if not q:
            continue
        s.P[j].x["k20_ramq"] = ()
        for x in q:
            if s.over or s.stop:
                break
            if x in s.P[j].hand:
                s.trigger(j, x)
    _poll(s)


def _tendp_20(s, i):
    """ターンの終わり：ジ・オリジナルは自分のターンの終わりにカードを1枚引いてもよい"""
    if s.tp != i or s.over:
        return
    for _ in range(_ncastle(s, i, "k20_origin")):
        if s.over:
            return
        s.draw(i, 1)
        s.ev("　ジ・オリジナル：自分のターンの終わりにカードを1枚引く")


def _mustatk_20(s, i):
    """ハイパーモード中の逆転龍神ヘヴィ・ウィン・メタル：相手のクリーチャーは可能なら攻撃する"""
    for u in s.P[1 - i].board:
        if u.k == "k20_heavywin" and u.hyper:
            return True
    return False


def _mustpick_20(s, by, cands):
    """神帝の黒月 ジ・オリジナル：相手がクリーチャーを選ぶなら、かわりに自分が選ぶ
    （＝候補のうち、自分がいちばん失ってもかまわないものを選ばせる）"""
    me = 1 - by
    if not _castle(s, me, "k20_origin"):
        return None
    mine = [u for u in cands if u in s.P[me].board and u.c.kind == "C"]
    if len(mine) <= 1:
        return None
    return min(mine, key=lambda z: (E.PRI[z.k] + len(z.under), z.uid))


def _w_atkwatch(s, i, u):
    _ramoon_attack(s, i, u)
    _shidens_on_attack(s, i, u)
    _poll(s)


def _w_atkend(s, i, u):
    if u.k == "k20_shiden" and u.x.get("k20_atkt") != s.turn:
        u.x["k20_atkt"] = s.turn
        if u.tap:
            u.tap = False
            s.ev("　ボルバルザーク・紫電：最初の攻撃の終わりにアンタップ")
            _shiden_untapped(s, i, u)
            u.x["k20_wastap"] = False
    _poll(s)


def _rep_leave(s, i, u, dest, destroy_):
    """離れるのを置き換える：ギャラクシーのSF／ザ・ラムーンの「離れない」／シデンズ・ソウルを外す／ガルテオのエスケープ"""
    if u.c.kind != "C":
        return False
    for z in _board(s, i, "k20_galaxy"):
        if _sf_on(s, i, z):
            s.ev(f"　SF−自分のクリーチャーは離れない：{u.c.name} は離れない")
            return True
    if u.x.get("k20_noleave", -1) >= s.turn:
        s.ev(f"　ザ・ラムーン：{u.c.name} は離れない")
        return True
    for g in s.P[i].board:
        if g.k == "k20_shidens" and g.c.kind == "X" and g.x.get("on") == u.uid:
            g.x["on"] = None
            s.ev(f"　シデンズ・ソウル：かわりにクロスギアを外して {u.c.name} は残る")
            return True
    if destroy_ and u.k == "k20_galteo" and s.P[i].sh:
        k = _take_shield(s, i, up=None)
        if k is not None:
            s.ev("　エスケープ：霊騎ガルテオはシールド1つを手札に加えて残る")
            return True
    return False


def _blockok(s, u):
    """ハイパーモード中のブロッカー"""
    if not u.hyper:
        return False
    return u.k in ("k20_heavywin", "k20_bolsol")


def _saok(s, i, u):
    """シデンズ・ソウルをクロスしたクリーチャーはスピードアタッカー"""
    for g in s.P[i].board:
        if g.k == "k20_shidens" and g.c.kind == "X" and g.x.get("on") == u.uid:
            return True
    return False


def _battlefx(s, ai, au, di, du, a_dies, d_dies):
    """戦技の炎 ボルメテウス・ソル（ハイパーモード）：タップした時、このターンすべてのバトルに勝つ"""
    if au.k == "k20_bolsol" and au.hyper and au.tap:
        a_dies, d_dies = False, True
    if du.k == "k20_bolsol" and du.hyper and du.tap:
        a_dies, d_dies = True, False
    return a_dies, d_dies


# ================================================================ 1. 逆転龍神ヘヴィ・ウィン・メタル
def _heavywin_use(s, i, u):
    """出た時または攻撃する時：自分の他のクリーチャーを1体破壊してもよい。
    そうしたら1枚引き、相手のクリーチャーを1体選んで破壊する"""
    if s.over or u not in s.P[i].board:
        return
    t = s.target(i)
    if t is None:
        return
    z = worst_own(s, i, pred=lambda x: x is not u)
    if z is None or s.val(z) > s.val(t):
        return
    if not s.leave(i, z, "grave", destroy=True):
        return
    s.ev(f"　ヘヴィ・ウィン・メタル：自分の {z.c.name} を破壊")
    s.draw(i, 1)
    t = s.target(i)
    if t is not None:
        destroy(s, i, t)


def _heavywin_onkill(s, i):
    """自分のクリーチャーが破壊された時、シールドを1つブレイクしてもよい"""
    if s.over or _BRKD[0] > 3 or not _board(s, i, "k20_heavywin"):
        return
    if not s.P[1 - i].sh:
        return
    _BRKD[0] += 1
    try:
        s.ev("　ヘヴィ・ウィン・メタル：自分のクリーチャーが破壊されたのでシールドを1つブレイク")
        s.break_sh(i, 1)
    finally:
        _BRKD[0] -= 1


def _brk_heavywin(s, i, u):
    if not u.hyper:
        return None
    return max(1, len(s.P[1 - i].sh))        # ワールド・ブレイカー


E.HYPER_POW["k20_heavywin"] = 34000

add("k20_heavywin", "逆転龍神ヘヴィ・ウィン・メタル", 5, "DF", power=5000,
    races=("god", "hyperbeast"), zrush=True, pri=9, roles="rem draw atk fin blk",
    enter=_heavywin_use, attack=_heavywin_use, brkx=_brk_heavywin,
    leavewatch=_w_leave, mustatk=_mustatk_20,
    text="出た時または攻撃する時、自分の他のクリーチャーを1体破壊してもよい。そうしたら1枚引き、"
         "相手のクリーチャーを1体選んで破壊する（自分の失うのがいちばん安いクリーチャーと、"
         "相手のいちばん重要なクリーチャーを選ぶ全デッキ共通の決まりで、割に合う時だけ使う）。"
         "自分のクリーチャーが破壊された時、シールドを1つブレイクしてもよい。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモード）。"
         "ハイパーモード中はパワー39000・ブロッカー・ワールド・ブレイカー（相手のシールドをすべてブレイク）で、"
         "相手のクリーチャーは可能なら攻撃する（攻撃できるクリーチャーがいる間、相手はターンを終えられない）",
    source=SRC["k20_heavywin"])


# ================================================================ 2. 叡智のW インビンシブル・ギャラクシー
def _sf_on(s, i, u):
    """シールド・フォースで選んだシールドが、まだシールドゾーンにあるか
    （シールドに見分けがつかないので、いちばん下のシールドを選んだものとして扱う）"""
    sf = u.x.get("k20_sf")
    if sf is None:
        return False
    p = s.P[i]
    return bool(p.sh) and p.sh[0] == sf


def _e_galaxy(s, i, u):
    """シールド・フォース：出す時、自分のシールドを1つ選んでもよい"""
    p = s.P[i]
    if p.sh:
        u.x["k20_sf"] = p.sh[0]
        s.ev("　シールド・フォース：自分のシールドを1つ選んだ（自分のクリーチャーは離れない）")


def _a_galaxy(s, i, u):
    """攻撃した時：1枚引いてもよい。その後シールド1つを手札に加えてもよい。その後手札1枚をシールド化してもよい"""
    p = s.P[i]
    if len(p.deck) > 1:
        s.draw(i, 1)
    if s.over or not p.sh:
        return
    got = _take_shield(s, i, up=False)
    if got is None:
        got = _take_shield(s, i, up=None)
    if got is not None:
        s.ev(f"　インビンシブル・ギャラクシー：シールドの {BY_KEY[got].name} を手札へ（S・トリガーは使えない）")
    k = _worst_hand_card(s, i)
    if k is not None:
        p.hand.remove(k)
        if not s.add_shield(i, k, False):
            p.hand.append(k)
        else:
            s.ev(f"　インビンシブル・ギャラクシー：手札の {BY_KEY[k].name} を裏向きでシールド化")


def _bd_galaxy(s, i, b, au):
    """ブロックした時（i＝ブロックした側、b＝ブロックしたこのクリーチャー）。
    攻撃した時と同じ能力が誘発する（エンジンの blockdone= で受ける）"""
    _a_galaxy(s, i, b)


add("k20_galaxy", "叡智のW インビンシブル・ギャラクシー", 6, "L", power=9000, brk=2,
    races=("angelcommand",), blocker=True, pri=9, roles="blk draw shd atk",
    enter=_e_galaxy, attack=_a_galaxy, blockdone=_bd_galaxy, leaverep=_rep_leave,
    text="ブロッカー。W・ブレイカー。シールド・フォース（出す時、自分のシールドを1つ選んでもよい。"
         "そのシールドがシールドゾーンにある間、SF能力を与える）。SF−自分のクリーチャーは離れない。"
         "攻撃またはブロックした時、1枚引いてもよい。その後、自分のシールド1つを手札に加えてもよい"
         "（S・トリガーは使えない）。その後、自分の手札1枚を裏向きでシールド化してもよい"
         "（シールドからは重要度の高いカードを取り、シールド化するのは手札でいちばん要らないカード）",
    note="シールド・フォースで選んだ1つを見分ける仕組みがエンジンにない"
         "（シールドは（カード, 表向きか）の並びで、同じカードのシールドを区別できない）ため、"
         "いちばん下のシールドを選んだものとして扱い、それがシールドゾーンにある間だけSF能力が働く。"
         "いちばん下のシールドが離れたあと、同じカードが同じ向きでいちばん下に来た時だけ見誤る",
    status="partial", source=SRC["k20_galaxy"])


# ================================================================ 3. 偉形のX エクストリーム・キリコ
def _kiriko_src(s, i):
    """手札進化の元になれる、手札の水のクリーチャー（いちばん要らないもの）"""
    cs = [k for k in s.P[i].hand if k != "k20_kiriko" and BY_KEY[k].kind == "C" and "W" in BY_KEY[k].civ]
    return min(cs, key=E.PRI.get) if cs else None


def _evosrc_kiriko(s, i):
    """手札進化：手札の水のクリーチャー1体を進化元にする（エンジンが取り出して下に積む）"""
    k = _kiriko_src(s, i)
    if k is None:
        return None
    s.P[i].x["k20_kiri"] = k
    return ("hand", k)


def _e_kiriko(s, i, u):
    p = s.P[i]
    # 進化元はエンジンが出た後に手札から下へ移すので、「手札の枚数」からは除いて数える
    src = p.x.pop("k20_kiri", None)
    s.draw(i, 3)
    if s.over:
        return
    mx = len(p.hand) - (1 if src in p.hand else 0)
    best = _free_element(s, i, mx, skip=src)
    if best is not None:
        s.ev(f"　エクストリーム・キリコ：手札の {BY_KEY[best].name} をコストを支払わずに使う")
        free_play(s, i, best, "hand")


def _pr_kiriko(deck, k):
    n = sum(v for kk, v in deck.items()
            if kk != k and BY_KEY[kk].kind == "C" and "W" in BY_KEY[kk].civ)
    return None if n >= 4 else "手札進化の元になる水のクリーチャーが4体いない"


add("k20_kiriko", "偉形のX エクストリーム・キリコ", 6, "W", power=12000, brk=3,
    races=("cyberlord", "origin"), evo="hand", pri=11, roles="draw atk fin",
    enter=_e_kiriko, evosrc=_evosrc_kiriko, playrule=_pr_kiriko,
    text="手札進化：自分の手札にある水のクリーチャー1体の上に重ねつつ出す（手札にそれがなければ召喚できない）。"
         "T・ブレイカー。出た時、カードを3枚引く。その後、自分の手札の枚数以下のコストを持つエレメントを1つ、"
         "自分の手札からコストを支払わずに使ってもよい（重要度のいちばん高いものを使う）",
    source=SRC["k20_kiriko"])


# ================================================================ 4. 冥幽のU ブライゼジェネレイド
def _e_braize(s, i, u):
    """出た時、このクリーチャーは自分のシールドを2つブレイクする"""
    if s.P[i].sh:
        s.ev("　ブライゼジェネレイド：自分のシールドを2つブレイク")
        s.break_sh(1 - i, 2)


def _fa_braize(s, i, av, cv):
    p = s.P[i]
    if "k20_braize" not in p.grave or len(p.sh) < 2 or av < 3 or "D" not in cv:
        return []
    if worst_own(s, i) is None or s.fate(i, "k20_braize", "grave", True) != "ok":
        return []
    return [("x:k20_braize",)]


def _ap_braize(s, a):
    i = s.tp
    p = s.P[i]
    if "k20_braize" not in p.grave or len(p.sh) < 2 or len(p.mana) - p.mused < 3:
        return
    z = worst_own(s, i)
    if z is None or not s.leave(i, z, "grave", destroy=True):
        return
    if "k20_braize" not in p.grave:
        return
    p.mused += 3
    p.grave.remove("k20_braize")
    s.ev(f"ブライゼジェネレイド：自分の {z.c.name} を破壊し、闇3マナで墓地から召喚")
    s.enter(i, "k20_braize", "grave", True)


add("k20_braize", "冥幽のU ブライゼジェネレイド", 5, "D", power=9000, brk=2,
    races=("dragonzombie",), blocker=True, pri=8, roles="blk rem atk fin",
    enter=_e_braize,
    text="ブロッカー。W・ブレイカー。自分のシールドが2つ以上あれば、自分のクリーチャーを1体破壊し、"
         "闇3マナを支払って、このクリーチャーを自分の墓地から召喚してもよい"
         "（破壊するのは自分の失うのがいちばん安いクリーチャー）。"
         "出た時、このクリーチャーは自分のシールドを2つブレイクする（自分のS・トリガーは使える）。"
         "自分のクリーチャーが破壊された時、このクリーチャーをアンタップする",
    source=SRC["k20_braize"])


# ================================================================ 5. 神羅の銀月 ザ・ラムーン
def _ramoon_place(s, j):
    """表向きで置かれた時、山札の上から2枚を裏向きでこのシールドの下に置く"""
    p = s.P[j]
    under = []
    for _ in range(2):
        if len(p.deck) <= 1:
            break
        under.append(p.deck.pop())
    if not under:
        return
    # p.x は clone で浅く写されるので、list ではなく tuple で持つ
    p.x["k20_ramu"] = tuple(p.x.get("k20_ramu") or ()) + (tuple(under),)
    s.ev(f"　ザ・ラムーン：山札の上から{len(under)}枚をこのシールドの下に置く")


def _ramoon_under(s, j, dest):
    """ザ・ラムーンのシールドが離れた：下に置いた2枚も同じ行き先へ送る
    （ブレイクなら手札に加え、そのS・トリガーを使えるようにする＝_w_break でまとめて使う）"""
    p = s.P[j]
    stack = tuple(p.x.get("k20_ramu") or ())
    if not stack:
        return
    under, p.x["k20_ramu"] = stack[0], stack[1:]
    if dest == "break" or dest == "hand":
        p.hand.extend(under)
        if dest == "break":
            p.x["k20_ramq"] = tuple(p.x.get("k20_ramq") or ()) + tuple(under)
        s.ev(f"　ザ・ラムーンの下の{len(under)}枚も手札に加わる")
        return
    for x in under:
        s.put_zone(j, x, dest if dest in ("grave", "mana", "deck", "decktop") else "grave")
    s.ev(f"　ザ・ラムーンの下の{len(under)}枚も同じ行き先へ")


def _ramoon_attack(s, i, u):
    """各ターン、はじめて自分のクリーチャーが攻撃する時、そのクリーチャーは離れない。その後1枚引く"""
    if u.c.kind != "C" or not _castle(s, i, "k20_ramoon"):
        return
    p = s.P[i]
    if p.x.get("k20_ramt") == s.turn:
        return
    p.x["k20_ramt"] = s.turn
    u.x["k20_noleave"] = s.turn + 1
    s.ev(f"　ザ・ラムーン：{u.c.name} は次の自分のターンのはじめまで離れない")
    s.draw(i, 1)


add("k20_ramoon", "神羅の銀月 ザ・ラムーン", 4, "L", kind="G", pri=5, roles="shd draw",
    atkwatch=_w_atkwatch, shieldin=_si_20, shieldout=_so_20, breakwatch=_w_break,
    text="G城（使ったら表向きでシールド化される。表向きでシールドゾーンを離れる時、かわりに墓地に置く）。"
         "表向きで自分のシールドゾーンに置かれた時、自分の山札の上から2枚を裏向きでこのシールドの下に置く"
         "（3枚で1つのシールドとして扱い、ブレイクされると下の2枚も手札に加わってS・トリガーが使える）。"
         "各ターン、はじめて自分のクリーチャーが攻撃する時、次の自分のターンのはじめまで、"
         "そのクリーチャーは離れない。その後、カードを1枚引く",
    source=SRC["k20_ramoon"])


# ================================================================ 6. 神帝の黒月 ジ・オリジナル
def _origin_fire(s, j):
    """表向きで置かれた時または離れた時、相手のタップしているクリーチャーを好きな数、持ち主の手札に戻す"""
    for t in opp_all(s, j, lambda u: u.tap):
        if s.over:
            return
        if t in s.P[1 - j].board:
            s.ev(f"　ジ・オリジナル：相手の {t.c.name} を手札に戻す")
            move(s, j, t, "hand")


add("k20_origin", "神帝の黒月 ジ・オリジナル", 5, "W", kind="G", pri=7, roles="rem draw dis",
    shieldin=_si_20, shieldout=_so_20, tendp=_tendp_20, mustpick=_mustpick_20,
    text="G城（使ったら表向きでシールド化される。表向きでシールドゾーンを離れる時、かわりに墓地に置く）。"
         "表向きで自分のシールドゾーンに置かれた時または離れた時、相手のタップしているクリーチャーを"
         "好きな数選び、持ち主の手札に戻してもよい（タップしている相手のクリーチャーをすべて戻す）。"
         "自分のターンの終わりに、カードを1枚引いてもよい。"
         "相手がクリーチャーを選ぶ時、かわりに自分が選ぶ"
         "（＝候補のうち、自分がいちばん失ってもかまわないクリーチャーを選ばせる）",
    source=SRC["k20_origin"])


# ================================================================ 7. 傀儡秘宝ベンゾルス
def _e_benzols(s, i, u):
    """出た時、山札の上から3枚まで墓地に置く。こうして置いたS・トリガー1枚につき相手を1体破壊してもよい"""
    got = s.mill(i, 3)
    n = 0
    for k in got:
        c = BY_KEY[k]
        if c.trig or (c.twin and c.twin[2]):
            n += 1
    if n:
        s.ev(f"　ベンゾルス：墓地に置いたS・トリガーは{n}枚")
    for _ in range(n):
        if s.over:
            return
        t = s.target(i)
        if t is None:
            return
        destroy(s, i, t)


def _benz_cands(s, i, av):
    p = s.P[i]
    cv = E.civs(p)
    out = []
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind != "C" or c.evo:
            continue
        n = c.cost
        if n > av or not cv.issuperset(c.civ):
            continue
        if s.fate(i, k, "grave", True) != "ok":
            continue
        out.append(k)
    return out


def _fa_benzols(s, i, av, cv):
    p = s.P[i]
    if not s.has(i, "k20_benzols") or p.x.get("k20_benzt") == s.turn:
        return []
    return [("x:k20_benz", k) for k in sorted(_benz_cands(s, i, av))]


def _ap_benzols(s, a):
    i = s.tp
    p = s.P[i]
    k = a[1]
    if p.x.get("k20_benzt") == s.turn or k not in p.grave or not s.has(i, "k20_benzols"):
        return
    n = BY_KEY[k].cost
    if len(p.mana) - p.mused < n:
        return
    p.x["k20_benzt"] = s.turn
    p.mused += n
    p.grave.remove(k)
    s.ev(f"ベンゾルス：墓地から {BY_KEY[k].name} を召喚（{n}マナ）")
    s.enter(i, k, "grave", True)


add("k20_benzols", "傀儡秘宝ベンゾルス", 7, "D", power=5000, trig=True,
    races=("pandorabox", "puppet"), pri=8, roles="trg rem fin",
    enter=_e_benzols,
    text="S・トリガー。出た時、自分の山札の上から3枚まで墓地に置く。こうして墓地に置いた「S・トリガー」を持つ"
         "カード1枚につき、相手のクリーチャーを1体選び、破壊してもよい（重要度の高い方から選ぶ）。"
         "自分のターン中、クリーチャーを1体、自分の墓地からコストを支払って召喚してもよい",
    note="エンジンの不足ではなくカードの本文の不明点。墓地からの召喚について、カードの本文には回数制限が"
         "書かれていないが、dmwiki の解説とタグは「各ターンに1度だけ」としている。解説に従って各ターン1回にした"
         "（本文どおりなら無制限で、動きが大きく変わるので partial のままにしてある）。"
         "墓地から召喚できるのは進化でないクリーチャーだけにしてある",
    status="partial", source=SRC["k20_benzols"])


# ================================================================ 8. 爆焔ジェット・メモッタ
def _fa_memotta(s, i, av, cv):
    p = s.P[i]
    if not s.has(i, "k20_memotta") or p.x.get("k20_memot") == s.turn or len(p.deck) <= 1:
        return []
    k = p.deck[-1]
    c = BY_KEY[k]
    if c.kind != "C" or c.cost > 6 or "hyperbeast" not in c.races or (c.evo and not c.neo):
        return []
    if s.fate(i, k, "deck", True) != "ok":
        return []
    return [("x:k20_memotta",)]


def _ap_memotta(s, a):
    i = s.tp
    p = s.P[i]
    if p.x.get("k20_memot") == s.turn or len(p.deck) <= 1 or not s.has(i, "k20_memotta"):
        return
    k = p.deck[-1]
    c = BY_KEY[k]
    if c.kind != "C" or c.cost > 6 or "hyperbeast" not in c.races or (c.evo and not c.neo):
        return
    p.x["k20_memot"] = s.turn
    p.deck.pop()
    s.ev(f"爆焔ジェット・メモッタ：山札の上の {c.name} をコストを支払わずに召喚")
    s.enter(i, k, "deck", True)


add("k20_memotta", "爆焔ジェット・メモッタ", 4, "F", power=5000, gs=True,
    races=("unknown",), pri=5, roles="trg acc atk",
    text="G・ストライク。自分のターン中、自分の山札の上から1枚をいつでも見てもよい。"
         "自分のターン中、コスト6以下の超化獣クリーチャーを1体、"
         "自分の山札の上からコストを支払わずに召喚してもよい",
    note="エンジンの不足ではなくカードの本文の不明点。山札の上からの召喚について、カードの本文には回数制限が"
         "ないが、dmwiki の解説とタグは「各ターンに1度だけ」としている。解説に従って各ターン1回にした"
         "（本文どおりなら無制限で、動きが大きく変わるので partial のままにしてある）。"
         "「山札の上から1枚を見てもよい」は、このシミュレーターが山札の中身を隠していないので何もしない",
    status="partial", source=SRC["k20_memotta"])


# ================================================================ 9. 二重のA ボルバルザーク・紫電
def _shiden_untapped(s, i, u):
    """アンタップした時、そのターン、このクリーチャーのパワーを2倍にする"""
    if u.x.get("k20_dt") != s.turn:
        u.x["k20_dt"] = s.turn
        u.x["k20_dn"] = 0
    u.x["k20_dn"] = u.x.get("k20_dn", 0) + 1
    s.ev(f"　ボルバルザーク・紫電：アンタップしてパワーが2倍（{u.x['k20_dn']}回目）")


def _px_shiden(s, i, u, atk):
    if u.x.get("k20_dt") != s.turn:
        return 0
    n = u.x.get("k20_dn", 0)
    return u.c.power * (2 ** n - 1) if n else 0


def _brk_powered(s, i, u):
    return 1 + s.power(i, u, True) // 6000


def _e_shiden(s, i, u):
    s.tap_cre(i, u)
    u.x["k20_wastap"] = True
    s.ev("　ボルバルザーク・紫電：タップして出た")


def _left_shiden(s, i, u, dest):
    """離れた時、自分の手札をすべて捨ててもよい。そうしたら3枚引く"""
    p = s.P[i]
    if len(p.hand) >= 3 or len(p.deck) <= 1:
        return
    for k in list(p.hand):
        if k in p.hand:
            s.discard(i, k)
    s.ev("　ボルバルザーク・紫電：手札をすべて捨てて3枚引く")
    s.draw(i, 3)


add("k20_shiden", "二重のA ボルバルザーク・紫電", 3, "F", power=4000,
    races=("armoreddragon", "samurai"), pri=7, roles="atk fin draw",
    enter=_e_shiden, powerx=_px_shiden, brkx=_brk_powered, left=_left_shiden,
    atkend=_w_atkend, tstartall=_w_tstart,
    text="パワード・ブレイカー（パワー6000ごとにシールドをもう1つブレイクする）。"
         "このクリーチャーをタップして出してもよい（アンタップの時にパワーが2倍になるので、必ずタップして出す）。"
         "このクリーチャーがアンタップした時、そのターン、このクリーチャーのパワーを2倍にする。"
         "各ターン、このクリーチャーの最初の攻撃の終わりに、このクリーチャーをアンタップする。"
         "このクリーチャーが離れた時、自分の手札をすべて捨ててもよい。そうしたら3枚引く"
         "（手札が2枚以下の時だけ使う）",
    note="エンジンには「タップした時」（tapwatch=）はあるが「アンタップした時」の差し込み口がないため、"
         "自分でアンタップする場面（最初の攻撃の終わり）はその場で誘発させ、"
         "それ以外（ターンのはじめのアンタップ、ほかのカードの効果によるアンタップ）は"
         "タップの状態を見回って気づく形にした（ターンのはじめ・終わり、クリーチャーが出た時・離れた時、"
         "攻撃の宣言と終わり、ブレイク、打てる手を数える時）。"
         "相手のターン中に相手の効果でアンタップされた場合は、気づくのが少し遅れる。"
         "パワー2倍は、カードに書かれているパワー（4000）を倍にする形で重ねている"
         "（ほかの効果で増えた分までは倍にしない）",
    status="partial", source=SRC["k20_shiden"])


# ================================================================ 10. 圧倒するレオパルズ・ホーン
def _px_leopard(s, i, u, atk):
    return 1000 * len(s.P[i].mana)


def _mana_types(s, i):
    return len({BY_KEY[k].kind for k in s.P[i].mana})


def _leopard_mana(s, i):
    """自分のマナゾーンにカードタイプが4つ以上あれば、マナの数字を2にする（使えるマナを2倍にする）"""
    p = s.P[i]
    if p.x.get("k20_leot") == s.turn:
        return
    if not s.has(i, "k20_leopard") or _mana_types(s, i) < 4:
        return
    p.x["k20_leot"] = s.turn
    p.mused -= len(p.mana)
    s.ev("　レオパルズ・ホーン：マナの数字が2になる（使えるマナが2倍）")


def _fa_leopard(s, i, av, cv):
    """G・ゼロ：バトルゾーンにクリーチャーが7体以上あれば、コストを支払わずに召喚してもよい"""
    p = s.P[i]
    if "k20_leopard" not in p.hand:
        return []
    if s.ncre(0) + s.ncre(1) < 7 or s.fate(i, "k20_leopard", "hand", True) != "ok":
        return []
    return [("x:k20_gzero",)]


def _ap_leopard(s, a):
    i = s.tp
    p = s.P[i]
    if "k20_leopard" not in p.hand or s.ncre(0) + s.ncre(1) < 7:
        return
    p.hand.remove("k20_leopard")
    s.ev("G・ゼロ：圧倒するレオパルズ・ホーン（コストを支払わずに召喚）")
    s.enter(i, "k20_leopard", "hand", True)


def _w_free(s, i, av, cv):
    """打てる手を数える時：アンタップの見回りと、レオパルズ・ホーンのマナの数字"""
    if s.over:
        return []
    _poll(s)
    if s.over:
        return []
    _leopard_mana(s, i)
    if s.over:
        return []
    out = []
    out += _fa_leopard(s, i, av, cv)
    out += _fa_braize(s, i, av, cv)
    out += _fa_benzols(s, i, av, cv)
    out += _fa_memotta(s, i, av, cv)
    return out


add("k20_leopard", "圧倒するレオパルズ・ホーン", 6, "N", power=0, races=("hornbeast",), mach=True,
    pri=10, roles="atk fin acc",
    powerx=_px_leopard, brkx=_brk_powered, freeacts=_w_free,
    actapply={"x:k20_gzero": _ap_leopard, "x:k20_braize": _ap_braize,
              "x:k20_benz": _ap_benzols, "x:k20_memotta": _ap_memotta},
    text="G・ゼロ：バトルゾーンにクリーチャーが7体以上あれば、このクリーチャーをコストを支払わずに召喚してもよい。"
         "マッハファイター。パワード・ブレイカー（パワー6000ごとにシールドをもう1つブレイクする）。"
         "パワーは0000＋自分のマナゾーンのカード1枚につき+1000。"
         "自分のマナゾーンにカードタイプが4つ以上あれば、自分のマナゾーンにあるカードのマナの数字を2にする",
    note="「マナの数字を2にする」は、エンジンがマナを1枚＝1マナで数えているため、"
         "自分のターンのはじめの手番で「使えるマナを枚数ぶん増やす」形で表した。"
         "そのターンの途中でマナが増えた分は2にならず1のままになる",
    status="partial", source=SRC["k20_leopard"])


# ================================================================ 11. 邪眼鎧悪ロマノフⅣ世
def _romanov_fire(s, j):
    """カードが自分のシールドゾーンに表向きで置かれた時、相手のクリーチャーを1体選び、破壊してもよい"""
    for _ in _board(s, j, "k20_romanov4"):
        if s.over:
            return
        t = s.target(j)
        if t is None:
            return
        s.ev("　ロマノフⅣ世：表向きのシールドが置かれたので相手を1体破壊")
        destroy(s, j, t)


def _e_romanov4(s, i, u):
    """出た時、山札の上から3枚まで墓地に置く。その後、コスト4以下のクリーチャーでないカードを1枚
    墓地からコストを支払わずに使ってもよい（呪文なら唱えた後、墓地のかわりに山札の下へ）"""
    p = s.P[i]
    s.mill(i, 3)
    if s.over:
        return
    best, bv = None, -1
    for k in sorted(set(p.grave)):
        c = BY_KEY[k]
        if c.kind == "C" or c.cost > 4 or E.PRI[k] <= bv:
            continue
        if c.kind == "S" and not s.spell_ok(i, c.cost):
            continue
        if c.kind == "G" and s.tp == i and s.has(1 - i, "fujin"):
            continue
        best, bv = k, E.PRI[k]
    if best is None:
        return
    spell = BY_KEY[best].kind == "S"
    s.ev(f"　ロマノフⅣ世：墓地の {BY_KEY[best].name} をコストを支払わずに使う")
    if free_play(s, i, best, "grave") and spell and best in p.grave:
        p.grave.remove(best)
        p.deck.insert(0, best)
        s.ev("　　唱えた呪文は墓地のかわりに山札の下へ")


add("k20_romanov4", "邪眼鎧悪ロマノフⅣ世", 5, "LD", power=6000, brk=2, blocker=True,
    races=("darklord", "dragonzombie", "knight"), pri=8, roles="blk rem draw fin",
    enter=_e_romanov4, shieldin=_si_20,
    text="ブロッカー。W・ブレイカー。出た時、自分の山札の上から3枚まで墓地に置く。その後、コスト4以下の、"
         "クリーチャーではないカードを1枚、自分の墓地からコストを支払わずに使ってもよい"
         "（重要度のいちばん高いものを使う）。こうして呪文を唱えたなら、唱えた後、墓地のかわりに山札の下に置く。"
         "カードが自分のシールドゾーンに表向きで置かれた時、相手のクリーチャーを1体選び、破壊してもよい",
    source=SRC["k20_romanov4"])


# ================================================================ 12. 聖竜鎧 シデンズ・ソウル
def _shidens_gears(s, i):
    return [g for g in s.P[i].board if g.k == "k20_shidens" and g.c.kind == "X"]


def _shidens_cross(s, i, g, cu):
    g.x["on"] = cu.uid
    s.ev(f"　シデンズ・ソウル：コストを支払わずに {cu.c.name} にクロス")


def _shidens_on_enter(s, i, u):
    """自分のクリーチャーが出た時、ただでそのクリーチャーにクロスしてもよい。
    その後、相手は自身のアンタップしているクリーチャーを1体選び、タップする"""
    if u.c.kind != "C":
        return
    for g in _shidens_gears(s, i):
        if g.x.get("on") == u.uid:
            continue
        if g.x.get("on") and not (u.sick and not u.tap):
            continue                    # すでにクロスしているなら、SAが要るクリーチャーにだけ移す
        _shidens_cross(s, i, g, u)
        oth = [z for z in s.P[1 - i].board if z.c.kind == "C" and not z.tap]
        if oth:
            z = min(oth, key=lambda x: (E.PRI[x.k] + len(x.under), x.uid))
            s.tap_cre(1 - i, z)
            s.ev(f"　シデンズ・ソウル：相手は自分の {z.c.name} をタップした")


def _shidens_on_attack(s, i, u):
    """クロスしたクリーチャーが攻撃する時、ただで自分の他のクリーチャーにクロスしてもよい"""
    for g in _shidens_gears(s, i):
        if g.x.get("on") != u.uid:
            continue
        cand = [z for z in s.P[i].board if z.c.kind == "C" and z is not u and z.sick and not z.tap]
        if not cand:
            continue
        _shidens_cross(s, i, g, max(cand, key=lambda z: s.power(i, z)))


add("k20_shidens", "聖竜鎧 シデンズ・ソウル", 3, "LF", kind="X", races=("samurai",), gs=True,
    pri=4, roles="trg atk",
    enterwatch=_w_enter, saok=_saok,
    text="G・ストライク。クロスギア（自分のターン中、コストを支払ってクリーチャー1体にクロスしてもよい。"
         "そのクリーチャーが離れても、このクロスギアは残る）。"
         "自分のクリーチャーが出た時、このクロスギアをコストを支払わずにそのクリーチャーにクロスしてもよい。"
         "その後、相手は自身のアンタップしているクリーチャーを1体選び、タップする"
         "（相手はいちばん失ってもかまわないクリーチャーをタップする）。"
         "クロスしたクリーチャーに「スピードアタッカー」を与え、そのクリーチャーが攻撃する時、"
         "このクロスギアをコストを支払わずに自分の他のクリーチャーにクロスしてもよい"
         "（スピードアタッカーが要る、出たばかりのクリーチャーに移す）。"
         "クロスしたクリーチャーが離れる時、かわりにこのクロスギアを外してもよい",
    source=SRC["k20_shidens"])


# ================================================================ 13. 魅神のG パロロ
def _e_paroro(s, i, u):
    """出た時、山札の上から1枚をタップしてマナゾーンに置く。その後、カードを1枚マナゾーンから墓地に置く"""
    p = s.P[i]
    s.ramp(i, 1, tapped=True)
    if p.mana:
        k = min(p.mana, key=E.PRI.get)
        s.take_mana(i, k)
        s.grave_put(i, k)
        s.ev(f"　パロロ：マナの {BY_KEY[k].name} を墓地へ")


def _tend_paroro(s, i, u):
    """ハイパーモード：自分のターンの終わりにタップしていれば、マナの枚数以下のコストのクリーチャーを墓地から出す"""
    if not u.hyper or not u.tap:
        return
    n = len(s.P[i].mana)
    if s.revive(i, lambda c: c.cost <= n) is not None:
        s.ev("　パロロ（ハイパーモード）：墓地からクリーチャーを出した")


E.HYPER_POW["k20_paroro"] = 3000

add("k20_paroro", "魅神のG パロロ", 3, "DN", power=4000, races=("god", "hyperbeast"), mach=True,
    zrush=True, pri=6, roles="acc rem atk",
    enter=_e_paroro, tend=_tend_paroro,
    text="マッハファイター。出た時、自分の山札の上から1枚をタップしてマナゾーンに置く。その後、カードを1枚、"
         "自分のマナゾーンから墓地に置く（いちばん重要度の低いカードを置く）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモード）。"
         "ハイパーモード中はパワー7000・W・ブレイカーになり、自分のターンの終わりにこのクリーチャーが"
         "タップしていれば、自分のマナゾーンにあるカードの枚数以下のコストのクリーチャー1体を"
         "自分の墓地から出してもよい（重要度のいちばん高いものを出す）",
    source=SRC["k20_paroro"])


# ================================================================ 14. 霊騎ガルテオ
def _galteo_fire(s, j):
    """各ターンに1度、カードが自分のシールドゾーンを離れた時、相手のクリーチャーを1体選び、タップしてもよい"""
    for u in _board(s, j, "k20_galteo"):
        if s.over:
            return
        if u.x.get("k20_galt") == s.turn:
            continue
        t = s.target(j, lambda x: not x.tap)
        if t is None:
            continue
        u.x["k20_galt"] = s.turn
        s.tap_cre(1 - j, t)
        s.ev(f"　霊騎ガルテオ：相手の {t.c.name} をタップ")


add("k20_galteo", "霊騎ガルテオ", 5, "L", power=4000, trig=True, blocker=True,
    races=("arkseraphim", "origin"), pri=6, roles="trg blk dis",
    shieldout=_so_20, leaverep=_rep_leave,
    text="S・トリガー。ブロッカー。各ターンに1度、カードが自分のシールドゾーンを離れた時、"
         "相手のクリーチャーを1体選び、タップしてもよい（重要度のいちばん高いアンタップしているものを選ぶ）。"
         "エスケープ（このクリーチャーが破壊される時、かわりに自分のシールドを1つ手札に加えてもよい。"
         "その「S・トリガー」は使えない。表向きのG城しか残っていない場合は、"
         "G城の決まりどおり墓地に置かれる）",
    source=SRC["k20_galteo"])


# ================================================================ 15. 戦技の炎 ボルメテウス・ソル
def _e_bolsol(s, i, u):
    """出た時、表向きのカードを含まないシールド1つを手札に加える（S・トリガーは使えない）。
    その後、自分の手札を1枚、表向きでシールド化する"""
    p = s.P[i]
    k = _take_shield(s, i, up=False)
    if k is not None:
        s.ev(f"　ボルメテウス・ソル：シールドの {BY_KEY[k].name} を手札へ（S・トリガーは使えない）")
    x = _worst_hand_card(s, i)
    if x is not None:
        p.hand.remove(x)
        if not s.add_shield(i, x, True):
            p.hand.append(x)
        else:
            s.ev(f"　ボルメテウス・ソル：手札の {BY_KEY[x].name} を表向きでシールド化")


E.HYPER_POW["k20_bolsol"] = 4000

add("k20_bolsol", "戦技の炎 ボルメテウス・ソル", 4, "L", power=4000, gs=True, zrush=True,
    races=("millionflame", "hyperbeast"), pri=6, roles="trg blk shd atk",
    enter=_e_bolsol, blockok=_blockok, battlefx=_battlefx,
    text="G・ストライク。出た時、自分の、表向きのカードを含まないシールドを1つ手札に加える"
         "（S・トリガーは使えない。重要度のいちばん高いカードを取る）。その後、自分の手札を1枚、"
         "表向きでシールド化する（いちばん要らないカードを置く）。"
         "Zラッシュ（シールドが離れたら、次の自分のターンのはじめまでハイパーモード）。"
         "ハイパーモード中はパワー8000・ブロッカー・W・ブレイカーになり、"
         "このクリーチャーがタップした時、このターン、このクリーチャーはすべてのバトルに勝つ",
    source=SRC["k20_bolsol"])
