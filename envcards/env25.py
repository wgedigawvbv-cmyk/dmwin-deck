"""担当25：DM26-RP2（逆札篇 第2弾 燃えろ禁断！逆転のドギラゴン革命‼︎）の未実装カード15枚

出典：dmwiki.net の各カードの個別ページ。1枚につき**別の質問で2回ずつ**読み、
      コスト・文明・カードの種類・種族・パワー・ブレイク数・能力の本文が2回とも一致することを確かめた。
      《熱血V龍 ガイギンガ》はさらにカードラッシュの商品ページ（26RP2 S5/S11、product/56557）の
      本文と突き合わせた（dmwiki の生 wiki ソースは要約で切られて読めなかったため）。
      キーワード能力《パワード・ブレイカー》は専用ページで定義（パワー6000ごとに1つ多くブレイク）を確かめた。
      《スーパーガードマン》も専用ページで定義（自分の他のクリーチャーがバトルする時、
      かわりにこのクリーチャーをタップしてバトルさせてもよい）を確かめた。

  この15枚に入っている仕組み
    ・「◯の絆」サイクル4枚（永遠／神極／零黒／勇愛）。既存の《叛逆の絆》と同じ、
      革命0トリガー＋「出た時または攻撃する時」を持つふつうの進化クリーチャー。
      （《勇愛の絆》は既存の《勇気の絆》とは別のカード）
    ・パワー・ガチンコ・ジャッジ（熱血の名 修羅丸／勝利宣言 鬼丸「V」）
    ・ソウルシフト（進化元のコストぶん召喚コストが下がる。極まる九極 Q.⁹）
    ・スペース・チャージ（マナゾーンにカードが置かれた時のSC能力。鎧亜目邪王類 デス＝ヴェルムート）
    ・パワード・ブレイカー（ヴェルムート／武将利と威嚇命の決断の3つめのモード）
    ・アタック・チャンス＋「2回選ぶ」モード呪文（武将利と威嚇命の決断）
    ・ファイナル革命＋スーパーガードマン（百族の団長 プチョヘンザ斧）
    ・バトル中パワー∞＋「コストを支払わずに出た相手とバトル」（V頂神話 カツムゲン）
    ・封印を付けて墓地から出す（不明な不透明 メモッタ）

  リメイク元と混同しないように、全部「正式名で個別ページを開いて」確かめた。
  とくに《百族の団長 プチョヘンザ斧》（コスト10・光自然・22500・Q・ブレイカー）は
  元の《百族の長 プチョヘンザ》とは別のカードで、ファイナル革命の内容も「パワーがより小さい相手だけ」。
  《V頂神話 カツムゲン》も、名前の似た既存カードとは無関係のコスト8・火自然・13000・T・ブレイカー。

  エンジンに仕組みがなくて近づけたのは「ターンを追加する」（ガイギンガ）だけ。
  スーパーガードマンは `battleswap=`、スペース・チャージは `manain=`、「相手が選んだ時」は `chosenwatch=`、
  ファイナル革命の「そのターン1回」は `s.P[i].final_turn` で、どれも差し込み口でそのまま書いてある。
"""
import engine3 as E
from cards3 import BY_KEY

from envreg import add, destroy, free_play, move
from envcards.env0 import SLAYER, discard_choice, own_loss, worst_own

W = "https://dmwiki.net/"
SRC = {
    "k25_gaiginga": W + "《熱血V龍 ガイギンガ》",
    "k25_eien": W + "《永遠の絆》",
    "k25_pucho": W + "《百族の団長 プチョヘンザ斧》",
    "k25_katsumugen": W + "《V頂神話 カツムゲン》",
    "k25_q9": W + "《極まる九極 Q.⁹》",
    "k25_shinkyoku": W + "《神極の絆》",
    "k25_shuramaru": W + "《熱血の名 修羅丸》",
    "k25_reikoku": W + "《零黒の絆》",
    "k25_memotta": W + "《不明な不透明 メモッタ》",
    "k25_yuuai": W + "《勇愛の絆》",
    "k25_gachirobo2": W + "《ガチャンコ ガチロボ弐号機》",
    "k25_onimaruv": W + "《勝利宣言 鬼丸「V」》",
    "k25_verumut": W + "《鎧亜目邪王類 デス＝ヴェルムート》",
    "k25_bushori": W + "《武将利と威嚇命の決断》",
    "k25_delzarbara": W + "《連戦の精霊龍 デルザルバーラ》",
}


# ================================================================ 共通の小道具
def _playable_cre(c):
    """コストを支払わずに出せるクリーチャーか（進化は進化元が要るので出せない）"""
    return c.kind == "C" and not (c.evo and not c.neo)


def _is_element(c):
    """エレメント（クリーチャー・タマシード・クロスギア・G城）か"""
    return c.kind in "CTXG"


def _can_put(s, i, k):
    """いまこのカードをコストを支払わずに出せるか（進化クリーチャーは進化元が場にいるかも見る）"""
    c = BY_KEY[k]
    if not _is_element(c):
        return False
    if c.kind == "C" and c.evo and not c.neo:
        return s.evo_src(i, k) is not None
    return True


def _put_free(s, i, k, src="deck", summon=False):
    """ゾーンから取り除いてある1枚を、コストを支払わずに出す。出せたら True、出せなければ False（カードは呼び出し側に戻る）"""
    p = s.P[i]
    c = BY_KEY[k]
    if c.kind == "C":
        on = None
        if c.evo and not c.neo:
            on = s.evo_src(i, k)
            if on is None:
                return False
        if s.fate(i, k, src, summon) != "ok":
            return False
        s.enter(i, k, src, summon, on=on)
        return True
    if c.kind == "T":
        s.place_tama(i, k)
        return True
    if c.kind == "X":
        gu = E.U(k)
        gu.sick = False
        p.board.append(gu)
        fn = E.ENTER.get(k)
        if fn is not None:
            fn(s, i, gu)
        return True
    if c.kind == "G":
        s.place_castle(i, k)
        return True
    return False


def _shield_or_mana(s, i, k):
    """1枚をシールド化する。フウジン天などで置けなければマナゾーンへ（カードを消さないため）"""
    if not s.add_shield(i, k):
        s.add_mana(i, k, src="deck")


def _best_own(s, i, pred=None):
    """自分のクリーチャーのうち、パワーを上げる値打ちがいちばん高いもの（アンタップを優先、次にパワー）"""
    best, bv = None, None
    for z in s.P[i].board:
        if z.c.kind != "C" or (pred is not None and not pred(z)):
            continue
        v = (0 if z.tap else 1, s.power(i, z), E.PRI[z.k])
        if bv is None or v > bv:
            best, bv = z, v
    return best


def _opp_cre(s, i):
    """相手のクリーチャー全部（「すべて」の効果用。選ぶのではないのでジャストダイバーも含む）"""
    return [z for z in s.P[1 - i].board if z.c.kind == "C"]


def pr_evo(civ, n=4):
    """進化クリーチャーの「出せるデッキか」：進化元になれるクリーチャーが n 体以上いるか"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and set(civ) & set(BY_KEY[kk].civ))
        return None if c >= n else f"進化元が{n}体いない"
    return f


def pr_change(civ, pw, n=3):
    """革命チェンジの「出せるデッキか」：元になれるクリーチャーが n 体以上いるか"""
    def f(deck, k):
        c = sum(v for kk, v in deck.items()
                if kk != k and BY_KEY[kk].kind == "C" and not BY_KEY[kk].noatk
                and set(civ) & set(BY_KEY[kk].civ) and BY_KEY[kk].power >= pw)
        return None if c >= n else f"革命チェンジの元が{n}体いない"
    return f


def kizuna_react(key, civ):
    """革命0トリガー（「◯の絆」サイクル共通）：自分のシールドが0枚で攻撃された時、このカードを手札から表向きにし、
    山札の上が「その文明の、進化ではないクリーチャー」ならそれを出して、このカードをその上に置く。
    既存の《叛逆の絆》（engine3 の REACT）とまったく同じ仕組みで書いてある"""
    def f(s, di, au):
        d = s.P[di]
        if d.sh or key not in d.hand or len(d.deck) <= 1:
            return False
        k = d.deck[-1]
        c = BY_KEY[k]
        if c.kind != "C" or civ not in c.civ or c.evo:
            return False
        if s.fate(di, k, "deck", False) != "ok" or s.fate(di, key, "hand", False) != "ok":
            return False
        d.deck.pop()
        d.hand.remove(key)                       # 先に手札から表向きにする
        s.ev(f"　革命0トリガー：{c.name} を出して {BY_KEY[key].name} を重ねる")
        base = s.enter(di, k, "deck", False)
        if base is None or base not in d.board:
            d.hand.append(key)                   # 進化元が出なければ手札に戻る
            return False
        return s.enter(di, key, "hand", False, on=base) is not None
    return f


def _gachinko(s, i):
    """パワー・ガチンコ・ジャッジ：両者が自分の山札の上から1枚を表向きにする。
    自分のカードのパワーが相手以上なら自分の勝ち（パワーのないカードは0）。
    相手のカードは山札の下に置く。返り値は (勝ったか, 自分が表向きにしたカード)。
    自分のカードの行き先は呼び出し側が決める（山札の下に置くか、効果に使う）"""
    p, o = s.P[i], s.P[1 - i]
    if len(p.deck) <= 1 or len(o.deck) <= 1:
        return None, None
    mk = p.deck.pop()
    ok = o.deck.pop()
    o.deck.insert(0, ok)
    return BY_KEY[mk].power >= BY_KEY[ok].power, mk


def _battle_fix(s, ai, au, di, du, a_dies, d_dies, abon, dbon):
    """バトル中だけのパワー加算を、バトルの結果に反映する
    （パワーの大小だけで決まっていた分を直し、スレイヤーなど他の理由で決まった分は残す）"""
    ap0 = s.power(ai, au, True) + (2000 if au.k == "testa" else 0)
    dp0 = s.power(di, du) + (2000 if du.k == "testa" else 0)
    ap, dp = ap0 + abon, dp0 + dbon
    if (ap0 <= dp0) != (ap <= dp):
        a_dies = ap <= dp or au.k == "kuzen" or du.k in SLAYER
    if (dp0 <= ap0) != (dp <= ap):
        d_dies = dp <= ap or du.k == "kuzen" or au.k in SLAYER
    return a_dies, d_dies


# ================================================================ 熱血V龍 ガイギンガ（S5/S11）
def _gaiginga_chosen(s, i, u):
    """「相手がこのクリーチャーを選んだ時、このターンの後に自分のターンを追加する」
    （エンジンの追加ターン＝`s.P[i].extra` を1つ増やす）"""
    s.P[i].extra += 1
    s.ev("　熱血V龍 ガイギンガ：このターンの後に自分のターンを追加する")


def a_gaiginga(s, i, u):
    """出た時または攻撃する時、山札の上から1枚を表向きにしてもよい。
    それがコスト4以下のエレメントなら出してもよい。出さなければ手札に加える"""
    p = s.P[i]
    if len(p.deck) <= 1:
        return
    k = p.deck.pop()
    c = BY_KEY[k]
    if c.cost <= 4 and _can_put(s, i, k) and _put_free(s, i, k):
        s.ev(f"　熱血V龍 ガイギンガ：山札の上の {c.name} を出す")
        return
    p.hand.append(k)
    s.ev(f"　熱血V龍 ガイギンガ：山札の上の {c.name} を手札へ")


def cw_gaiginga(s, i, u, by):
    """相手がこのクリーチャーを選んだ時（chosenwatch。i＝持ち主、by＝選んだ側）"""
    if u.k != "k25_gaiginga":
        return
    _gaiginga_chosen(s, i, u)


def gd_gaiginga(s, di, au, tu):
    """攻撃先に選ばれた時も「相手が選んだ時」に当たる。

    エンジンの攻撃の差し込み口のうち、守る側に**実際の攻撃先**が渡るのはガードマン（GUARD）だけなので、
    そこで攻撃先がこのカードかどうかを見て誘発させる（攻撃先は変えないので None を返す）。
    ブロックしてバトルになった時は攻撃先ではないので、ここでは誘発しない。"""
    if tu is not None and tu.k == "k25_gaiginga":
        _gaiginga_chosen(s, di, tu)
    return None


add("k25_gaiginga", "熱血V龍 ガイギンガ", 5, "F", power=6000, brk=2, sa=True,
    races=("gaialcommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=8, roles="atk fin acc",
    enter=a_gaiginga, attack=a_gaiginga, chosenwatch=cw_gaiginga, guard=gd_gaiginga,
    powerx=lambda s, i, u, atk: 4000 if atk else 0,
    text="スピードアタッカー。パワーアタッカー+4000。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、自分の山札の上から1枚を表向きにしてもよい。"
         "それがコスト4以下のエレメントなら出してもよい。こうして出さなければ、それを手札に加える。"
         "相手がこのクリーチャーを選んだ時、このターンの後に自分のターンを追加する"
         "（回数の制限はないので、選ばれるたびに1ターン増える）",
    source=SRC["k25_gaiginga"])


# ================================================================ 永遠の絆（S6/S11）
def a_eien(s, i, u):
    """出た時または攻撃する時、相手のクリーチャー1体を選び、持ち主のマナゾーンに置く"""
    t = s.target(i)
    if t is None:
        return
    s.ev(f"　永遠の絆：{t.c.name} を持ち主のマナゾーンへ")
    move(s, i, t, "mana")


add("k25_eien", "永遠の絆", 3, "N", power=9000, brk=2, evo="N",
    races=("redcommanddragon", "command", "dragon", "hunter", "alien"), pri=7, roles="rem atk trg",
    enter=a_eien, attack=a_eien, react=kizuna_react("k25_eien", "N"), playrule=pr_evo("N"),
    text="革命0トリガー：クリーチャーが自分を攻撃する時、自分のシールドが1つもなければ、このカードを手札から"
         "表向きにしてもよい。そうしたら山札の上から1枚を表向きにし、それが自然の進化ではないクリーチャーなら出して、"
         "このカードをその上に置く。進化：自然のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、相手のクリーチャー1体を選び、持ち主のマナゾーンに置く",
    note="革命0トリガーは本来「プレイヤーが攻撃された時」だけだが、エンジンの差し込み口（REACT）が"
         "クリーチャーへの攻撃でも呼ばれるため、既存の《叛逆の絆》と同じく、どちらの攻撃でも使える形になっている",
    source=SRC["k25_eien"])


# ================================================================ 百族の団長 プチョヘンザ斧（S8/S11）
def e_pucho(s, i, u):
    """ファイナル革命：革命チェンジで出た時、そのターンに他のファイナル革命を使っていなければ、
    このクリーチャーよりパワーが小さい相手のクリーチャーをすべて持ち主のマナゾーンに置く"""
    if "src" in u.x:                         # 召喚・踏み倒しで出た時は働かない（革命チェンジ限定）
        return
    p = s.P[i]
    if p.final_turn == s.turn:                # そのターンに他のファイナル革命を使っている
        return
    p.final_turn = s.turn
    w = s.power(i, u)
    s.ev(f"　ファイナル革命：パワー{w}より小さい相手のクリーチャーをすべてマナゾーンへ")
    for z in _opp_cre(s, i):
        if z in s.P[1 - i].board and s.power(1 - i, z) < w:
            s.leave(1 - i, z, "mana", by_opp=True)


def ae_pucho(s, i, u):
    """このクリーチャーの攻撃の終わりに、山札の上から3枚を見て、
    エレメントを最大1つ出し、1枚をシールド化し、残りをマナゾーンに置く
    （ATKEND はどのクリーチャーの攻撃の終わりでも呼ばれるので、自分のカードかを必ず確かめる）"""
    if u.k != "k25_pucho":
        return
    p = s.P[i]
    n = min(3, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best = None
    for k in top:
        if not _can_put(s, i, k):
            continue
        if best is None or E.PRI[k] > E.PRI[best]:
            best = k
    if best is not None:
        top.remove(best)
        if _put_free(s, i, best):
            s.ev(f"　プチョヘンザ斧：{BY_KEY[best].name} を出す")
        else:
            top.append(best)
    if top:
        k = max(top, key=E.PRI.get)
        top.remove(k)
        _shield_or_mana(s, i, k)
    for k in top:
        s.add_mana(i, k, src="deck")


def bs_pucho(s, di, du, ai, au):
    """スーパーガードマン：自分の他のクリーチャーがバトルする時、かわりにこれをタップしてバトルさせる

    引き受けるかどうかは全デッキ共通の決まりで機械的に決める：バトルに勝てるか、
    守る相手のほうが大事な時だけ引き受ける（env0.guardman と同じ決まり）。
    攻撃先そのものは変わらないので、攻撃されたクリーチャーのほうは本物どおりそのまま残る。"""
    if du.k == "k25_pucho":
        return None
    ap = s.power(ai, au, True)
    for z in s.P[di].board:
        if z.k != "k25_pucho" or z.c.kind != "C" or z.tap or z is du:
            continue
        if s.power(di, z) > ap or s.val(du) > s.val(z):
            s.tap_cre(di, z)
            return z
    return None


E.GUARDMEN.add("k25_pucho")                  # 「ガードマンを持つクリーチャー」を数えるカード用


add("k25_pucho", "百族の団長 プチョヘンザ斧", 10, "LN", power=22500, brk=4, mach=True,
    races=("jurassiccommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=13,
    roles="fin rem blk atk",
    enter=e_pucho, atkend=ae_pucho, battleswap=bs_pucho,
    changex=lambda s, i, u: bool(set("LN") & set(u.c.civ)) and s.power(i, u, True) >= 12000,
    playrule=pr_change("LN", 12000),
    text="革命チェンジ：光または自然の、パワー12000以上のクリーチャー。マッハファイター。"
         "スーパーガードマン（自分の他のクリーチャーがバトルする時、かわりにこのクリーチャーをタップして"
         "バトルさせてもよい）。Q・ブレイカー。"
         "このクリーチャーの攻撃の終わりに、自分の山札の上から3枚を見る。その中からエレメントを最大1つ出し、"
         "1枚をシールド化し、残りをマナゾーンに置く。"
         "ファイナル革命：このクリーチャーが革命チェンジによって出た時、そのターンに他のファイナル革命を"
         "使っていなければ、このクリーチャーよりパワーが小さい相手のクリーチャーをすべて持ち主のマナゾーンに置く",
    source=SRC["k25_pucho"])


# ================================================================ V頂神話 カツムゲン（S11/S11）
def _katsumugen_win(s, j, u):
    """バトルに勝った時、自分の手札を1枚捨ててもよい。そうしたら2枚引く。
    こうしてパワー6000以上のクリーチャーを捨てたら、このクリーチャーをアンタップする"""
    p = s.P[j]
    if not p.hand or len(p.deck) <= 1:
        return
    big = [k for k in p.hand if BY_KEY[k].kind == "C" and BY_KEY[k].power >= 6000]
    k = min(big, key=E.PRI.get) if big else min(p.hand, key=E.PRI.get)
    s.discard(j, k)
    s.ev(f"　カツムゲン：{BY_KEY[k].name} を捨てて2枚引く")
    s.draw(j, 2)
    if BY_KEY[k].kind == "C" and BY_KEY[k].power >= 6000 and u in p.board:
        u.tap = False
        s.ev("　カツムゲン：アンタップする")


def bf_katsumugen(s, ai, au, di, du, a_dies, d_dies):
    """バトル中、これのパワーを∞にする（スレイヤーだけは効く）。バトルに勝った時の効果もここで処理する"""
    if au.k == "k25_katsumugen":
        u, j, a_dies, d_dies = au, ai, du.k in SLAYER, True
    elif du.k == "k25_katsumugen":
        u, j, a_dies, d_dies = du, di, True, au.k in SLAYER
    else:
        return a_dies, d_dies
    mine = a_dies if u is au else d_dies
    other = d_dies if u is au else a_dies
    if other and not mine and not s.over:
        _katsumugen_win(s, j, u)
    return a_dies, d_dies


def w_katsumugen(s, i, u):
    """相手のクリーチャーがコストを支払わずに出た時、このクリーチャーとそのクリーチャーをバトルさせてもよい"""
    if u.c.kind != "C" or u.x.get("summoned"):
        return
    j = 1 - i
    for z in s.P[j].board[:]:
        if z.k != "k25_katsumugen" or z not in s.P[j].board or u not in s.P[i].board:
            continue
        s.ev(f"　カツムゲン：コストを支払わずに出た {u.c.name} とバトルする")
        s.battle(j, z, i, u)
        return


add("k25_katsumugen", "V頂神話 カツムゲン", 8, "FN", power=13000, brk=3, sa=True,
    races=("outragecommand", "command", "revolution", "hamukatsu"), pri=12, roles="fin atk draw dis",
    battlefx=bf_katsumugen, enterwatch=w_katsumugen,
    changex=lambda s, i, u: bool(set("FN") & set(u.c.civ)) and s.power(i, u, True) >= 8000,
    playrule=pr_change("FN", 8000),
    text="革命チェンジ：火または自然の、パワー8000以上のクリーチャー。スピードアタッカー。T・ブレイカー。"
         "相手のクリーチャーがコストを支払わずに出た時、このクリーチャーとそのクリーチャーをバトルさせてもよい。"
         "バトル中、またはこれを山札で表向きにしている間、これのパワーを∞にする。"
         "このクリーチャーがバトルに勝った時、自分の手札を1枚捨ててもよい。そうしたらカードを2枚引く。"
         "こうしてパワー6000以上のクリーチャーを捨てたら、このクリーチャーをアンタップする",
    note="「山札で表向きにしている間パワー∞」は、山札を表向きにする効果の判定に"
         "パワーを使うカードがこのシミュレーターにないので、結果が変わらない（実装していない）。"
         "バトル中のパワー∞は「必ずバトルに勝ち、バトルでは死なない」として書いた"
         "（パワーを見ないスレイヤーだけは通る）",
    status="partial", source=SRC["k25_katsumugen"])


# ================================================================ 極まる九極 Q.⁹（1/77）
def cx_q9(s, i, av):
    """ソウルシフト：召喚コストを進化元のコストの数だけ少なくする（0以下にはならない）"""
    src = s.evo_src(i, "k25_q9")
    return max(1, 9 - (src.c.cost if src is not None else 0))


def l_q9(s, i, u, dest):
    """離れた時、その下にコスト9のクリーチャーがあれば、山札の上から9枚を見て、
    その中から光のコスト9のクリーチャーを1体出してもよい。残りをシャッフルして山札の下に置く"""
    if not any(BY_KEY[k].kind == "C" and BY_KEY[k].cost == 9 for k in u.under):
        return
    p = s.P[i]
    n = min(9, len(p.deck) - 1)
    if n <= 0:
        return
    top = [p.deck.pop() for _ in range(n)]
    best = None
    for k in top:
        c = BY_KEY[k]
        if c.kind != "C" or c.cost != 9 or "L" not in c.civ or not _can_put(s, i, k):
            continue
        if best is None or E.PRI[k] > E.PRI[best]:
            best = k
    if best is not None:
        top.remove(best)
        if _put_free(s, i, best):
            s.ev(f"　極まる九極 Q.⁹：山札から {BY_KEY[best].name} を出す")
        else:
            top.append(best)
    s.rng.shuffle(top)
    for k in top:
        p.deck.insert(0, k)


add("k25_q9", "極まる九極 Q.⁹", 9, "L", power=12500, brk=3, blocker=True, gs=True, evo="L",
    races=("angelcommanddragon", "command", "dragon", "invader", "hamukatsu"), pri=11, roles="blk trg fin",
    costx=cx_q9, left=l_q9, playrule=pr_evo("L"),
    text="G・ストライク。ソウルシフト（このクリーチャーの召喚コストを進化元のコストの数だけ少なくする。"
         "ただしコストは0以下にならない）。進化：光のクリーチャー1体の上に置く。ブロッカー。T・ブレイカー。"
         "このクリーチャーが離れた時、その下にコスト9のクリーチャーがあれば、自分の山札の上から9枚を見る。"
         "その中から光のコスト9のクリーチャーを1体出してもよい。残りをシャッフルして山札の下に置く",
    note="ソウルシフトの軽減は、エンジンが進化元に選ぶクリーチャー（アンタップで重要度の低いもの）の"
         "コストで数えている。全デッキ共通の進化元の選び方をそのまま使っているので、"
         "いちばんコストの高い進化元をわざわざ選び直しはしない",
    source=SRC["k25_q9"])


# ================================================================ 神極の絆（2/77）
def a_shinkyoku(s, i, u):
    """出た時または攻撃する時、自分の山札の上から1枚をシールド化する"""
    if s.add_shield(i):
        s.ev("　神極の絆：山札の上から1枚をシールド化")


add("k25_shinkyoku", "神極の絆", 4, "L", power=8500, brk=2, blocker=True, evo="L",
    races=("oraclecommand", "command"), pri=7, roles="blk shd trg atk",
    enter=a_shinkyoku, attack=a_shinkyoku, react=kizuna_react("k25_shinkyoku", "L"), playrule=pr_evo("L"),
    text="革命0トリガー：クリーチャーが自分を攻撃する時、自分のシールドが1つもなければ、このカードを手札から"
         "表向きにしてもよい。そうしたら山札の上から1枚を表向きにし、それが光の進化ではないクリーチャーなら出して、"
         "このカードをその上に置く。進化：光のクリーチャー1体の上に置く。ブロッカー。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、自分の山札の上から1枚をシールド化する",
    note="革命0トリガーは本来「プレイヤーが攻撃された時」だけだが、エンジンの差し込み口（REACT）が"
         "クリーチャーへの攻撃でも呼ばれるため、既存の《叛逆の絆》と同じく、どちらの攻撃でも使える形になっている",
    source=SRC["k25_shinkyoku"])


# ================================================================ 熱血の名 修羅丸（4/77）
def ts_shuramaru(s, i, u):
    """自分のターンのはじめに、相手とパワー・ガチンコ・ジャッジしてもよい。
    自分が勝ったら、こうして表向きにしたクリーチャーを山札の下に置くかわりに、コストを支払わずに召喚してもよい。
    こうして召喚したら、このクリーチャーを手札に戻す"""
    p = s.P[i]
    won, mk = _gachinko(s, i)
    if mk is None:
        return
    c = BY_KEY[mk]
    s.ev(f"　修羅丸：パワー・ガチンコ・ジャッジ（{c.name}）→ {'勝ち' if won else '負け'}")
    if won and c.kind == "C" and _put_free(s, i, mk, "deck", summon=True):
        s.ev(f"　修羅丸：{c.name} をコストを支払わずに召喚")
        if u in p.board:
            s.leave(i, u, "hand")
        return
    p.deck.insert(0, mk)


add("k25_shuramaru", "熱血の名 修羅丸", 4, "W", power=10000, blocker=True, noatk=True,
    races=("humanoid", "kingcommanddragon", "command", "dragon", "unknown"), pri=6, roles="blk acc",
    tstart=ts_shuramaru,
    text="ブロッカー。このクリーチャーは攻撃できない。"
         "自分のターンのはじめに、相手とパワー・ガチンコ・ジャッジしてもよい"
         "（両者が山札の上から1枚を表向きにし、パワーが相手以上なら自分の勝ち。パワーのないカードは0）。"
         "自分が勝ったら、こうして自分が表向きにしたクリーチャーを山札の下に置くかわりに、"
         "コストを支払わずに召喚してもよい。こうして召喚したら、このクリーチャーを手札に戻す",
    note="ガチンコ・ジャッジを「してもよい」は、山札が両者2枚以上あれば必ずする（損がないため）。"
         "勝って表向きにしたのが進化クリーチャーの時は、進化元を要するので召喚せず山札の下に置く",
    source=SRC["k25_shuramaru"])


# ================================================================ 零黒の絆（5/77）
def e_reikoku(s, i, u):
    """出た時、このターン、相手のクリーチャーすべてのパワーを-4000する"""
    o = s.P[1 - i]
    s.ev("　零黒の絆：相手のクリーチャーすべてのパワーを-4000")
    for z in _opp_cre(s, i):
        if z not in o.board:
            continue
        z.pw -= 4000
        if s.power(1 - i, z) <= 0:
            s.leave(1 - i, z, "grave", by_opp=True, destroy=True)


add("k25_reikoku", "零黒の絆", 4, "D", power=8000, brk=2, blocker=True, evo="D",
    races=("outragecommand", "command", "demoncommanddragon", "dragon"), pri=7, roles="blk rem trg atk",
    enter=e_reikoku, react=kizuna_react("k25_reikoku", "D"), playrule=pr_evo("D"),
    text="革命0トリガー：クリーチャーが自分を攻撃する時、自分のシールドが1つもなければ、このカードを手札から"
         "表向きにしてもよい。そうしたら山札の上から1枚を表向きにし、それが闇の進化ではないクリーチャーなら出して、"
         "このカードをその上に置く。進化：闇のクリーチャー1体の上に置く。ブロッカー。W・ブレイカー。"
         "このクリーチャーが出た時、このターン、相手のクリーチャーすべてのパワーを-4000する"
         "（パワーが0以下になったクリーチャーは破壊される）",
    note="革命0トリガーは本来「プレイヤーが攻撃された時」だけだが、エンジンの差し込み口（REACT）が"
         "クリーチャーへの攻撃でも呼ばれるため、既存の《叛逆の絆》と同じく、どちらの攻撃でも使える形になっている",
    source=SRC["k25_reikoku"])


# ================================================================ 不明な不透明 メモッタ（6/77）
def e_memotta(s, i, u):
    """召喚によって出た時、山札の上から3枚を墓地に置く。その後、コストの合計が5以下になるように、
    進化ではないクリーチャーを2体まで、封印を1枚ずつ付けて自分の墓地から出す"""
    if not u.x.get("summoned"):
        return
    p = s.P[i]
    s.mill(i, 3)
    left = 5
    for _ in range(2):
        if s.over:
            return
        best, bv = None, -1
        for k in sorted(set(p.grave)):
            c = BY_KEY[k]
            if not _playable_cre(c) or c.cost > left:
                continue
            if E.PRI[k] > bv and s.fate(i, k, "grave", False) == "ok":
                best, bv = k, E.PRI[k]
        if best is None:
            return
        p.grave.remove(best)
        left -= BY_KEY[best].cost
        if len(p.deck) > 1:
            z = E.U(best)
            z.sick = False
            z.x["sealcards"] = [p.deck.pop()]
            p.sealed.append((z, 1))
            s.ev(f"　メモッタ：墓地から {BY_KEY[best].name} を封印1つ付けて出す")
        else:
            s.ev(f"　メモッタ：墓地から {BY_KEY[best].name} を出す（封印に置く山札がない）")
            s.enter(i, best, "grave", False)


add("k25_memotta", "不明な不透明 メモッタ", 4, "D", power=6000, brk=2, pri=6, roles="acc atk",
    enter=e_memotta,
    text="W・ブレイカー。このクリーチャーが召喚によって出た時、自分の山札の上から3枚を墓地に置く。"
         "その後、コストの合計が5以下になるように、進化ではないクリーチャーを2体まで、"
         "封印を1枚ずつ付けて自分の墓地から出す"
         "（封印されているクリーチャーはバトルゾーンにないものとして扱われ、"
         "文明の合うコマンドが出ると封印が外れて働きだす）。公式の種族表記は「？？？」",
    note="種族「？？？」は何とも組み合わないので races は空にした。"
         "封印を付けて出すクリーチャーは、公式の裁定どおり「出た時」の能力が誘発しない形で書いてある"
         "（バトルゾーンを経由せず、封印されたまま置く）",
    source=SRC["k25_memotta"])


# ================================================================ 勇愛の絆（7/77）
def a_yuuai(s, i, u):
    """出た時または攻撃する時、相手のコスト6以下のエレメントを1つ選び、破壊する"""
    t = s.target(i, lambda z: z.c.cost <= 6, kinds="CTX")
    if t is None:
        return
    s.ev(f"　勇愛の絆：{t.c.name} を破壊")
    destroy(s, i, t)


add("k25_yuuai", "勇愛の絆", 4, "F", power=9000, brk=2, evo="F",
    races=("gaialcommanddragon", "command", "dragon", "humanoidbomb", "dragnor"), pri=7, roles="rem trg atk",
    enter=a_yuuai, attack=a_yuuai, react=kizuna_react("k25_yuuai", "F"), playrule=pr_evo("F"),
    text="革命0トリガー：クリーチャーが自分を攻撃する時、自分のシールドが1つもなければ、このカードを手札から"
         "表向きにしてもよい。そうしたら山札の上から1枚を表向きにし、それが火の進化ではないクリーチャーなら出して、"
         "このカードをその上に置く。進化：火のクリーチャー1体の上に置く。W・ブレイカー。"
         "このクリーチャーが出た時または攻撃する時、相手のコスト6以下のエレメントを1つ選び、破壊する",
    note="革命0トリガーは本来「プレイヤーが攻撃された時」だけだが、エンジンの差し込み口（REACT）が"
         "クリーチャーへの攻撃でも呼ばれるため、既存の《叛逆の絆》と同じく、どちらの攻撃でも使える形になっている。"
         "エレメントのうちG城はシールドゾーンに置かれる作りなので、選べるのは"
         "クリーチャー・タマシード・クロスギア（既存カードと同じ扱い）。"
         "既存の《勇気の絆》とは別のカード",
    source=SRC["k25_yuuai"])


# ================================================================ ガチャンコ ガチロボ弐号機（8/77）
def a_gachirobo2(s, i, u):
    """攻撃する時、山札の上から3枚を表向きにする。それがすべて同じコストのクリーチャーなら出す。
    そうでなければ好きな順序で山札の下に置く"""
    p = s.P[i]
    if len(p.deck) - 1 < 3:
        return
    top = [p.deck.pop() for _ in range(3)]
    cs = [BY_KEY[k] for k in top]
    if all(c.kind == "C" for c in cs) and len({c.cost for c in cs}) == 1:
        s.ev(f"　ガチロボ弐号機：3枚ともコスト{cs[0].cost}のクリーチャー → すべて出す")
        for k in top:
            if s.over or not _put_free(s, i, k):
                p.deck.insert(0, k)
    else:
        for k in sorted(top, key=E.PRI.get):
            p.deck.insert(0, k)


add("k25_gachirobo2", "ガチャンコ ガチロボ弐号機", 8, "F", power=5000, sa=True,
    races=("greatmechaoh", "invader"), pri=9, roles="atk fin acc",
    attack=a_gachirobo2,
    costx=lambda s, i, av: 5 if s.ncre(i) == 0 else 8,
    saok=lambda s, i, u: len(s.P[1 - i].sh) <= 2 and s.has(i, "k25_gachirobo2"),
    text="自分のクリーチャーがなければ、このクリーチャーの召喚コストを3少なくする。スピードアタッカー。"
         "このクリーチャーが攻撃する時、自分の山札の上から3枚を表向きにする。"
         "それがすべて同じコストのクリーチャーなら出す。そうでなければ、好きな順序で山札の下に置く。"
         "相手のシールドが2つ以下なら、自分のクリーチャーすべてに「スピードアタッカー」を与える",
    note="表向きにした進化クリーチャーは、場に進化元がいなければ出せないので山札の下に置いている"
         "（出せない進化クリーチャーはそのまま置かれる、という本来のルールどおり）",
    source=SRC["k25_gachirobo2"])


# ================================================================ 勝利宣言 鬼丸「V」（9/77）
def _onimaru_give(s, i):
    """相手は自身のクリーチャーまたはシールドを1つ選び、持ち主のマナゾーンに置く
    （選ぶのは相手なので、相手から見ていちばん損の小さいほうを出す。シールドの値打ちは残り枚数で見る）"""
    o = s.P[1 - i]
    z = worst_own(s, 1 - i)
    cv = own_loss(s, 1 - i, z) if z is not None else None
    sv = (12 if len(o.sh) <= 1 else 8 if len(o.sh) == 2 else 5) if o.sh else None
    if cv is not None and (sv is None or cv <= sv):
        s.ev(f"　鬼丸「V」：相手は {z.c.name} をマナゾーンに置いた")
        s.leave(1 - i, z, "mana", by_opp=True)
        return True
    if sv is not None:
        k, up = o.sh.pop(0)
        s.shield_left()
        for f in E.SHIELDOUT:
            f(s, 1 - i, k, up, "mana")
        s.add_mana(1 - i, k, src="shield")
        s.ev(f"　鬼丸「V」：相手はシールド1つ（{BY_KEY[k].name}）をマナゾーンに置いた")
        return True
    return False


def ae_onimaru(s, i, u):
    """攻撃の終わりに、自分が負けるか中止するまで相手とパワー・ガチンコ・ジャッジする。
    その後、こうして自分が勝った回数、相手は自身のクリーチャーかシールドを1つマナゾーンに置く
    （ATKEND はどのクリーチャーの攻撃の終わりでも呼ばれるので、自分のカードかを必ず確かめる）"""
    if u.k != "k25_onimaru":
        return
    p = s.P[i]
    wins = 0
    for _ in range(20):
        won, mk = _gachinko(s, i)
        if mk is None:
            break
        p.deck.insert(0, mk)
        if not won:
            s.ev(f"　鬼丸「V」：ガチンコ・ジャッジに負けた（{BY_KEY[mk].name}）")
            break
        wins += 1
    if wins:
        s.ev(f"　鬼丸「V」：ガチンコ・ジャッジに{wins}回勝った")
    for _ in range(wins):
        if s.over or not _onimaru_give(s, i):
            break


def bf_onimaru(s, ai, au, di, du, a_dies, d_dies):
    """バトル中、このクリーチャーのパワーを+5000する"""
    ab = 5000 if au.k == "k25_onimaruv" else 0
    db = 5000 if du.k == "k25_onimaruv" else 0
    if not ab and not db:
        return a_dies, d_dies
    return _battle_fix(s, ai, au, di, du, a_dies, d_dies, ab, db)


add("k25_onimaruv", "勝利宣言 鬼丸「V」", 10, "N", power=9000, brk=2, mach=True,
    races=("humanoid", "greencommanddragon", "command", "dragon", "hunter", "alien"), pri=12,
    roles="fin rem atk",
    atkend=ae_onimaru, battlefx=bf_onimaru,
    text="マッハファイター。W・ブレイカー。バトル中、このクリーチャーのパワーを+5000する。"
         "このクリーチャーの攻撃の終わりに、自分が負けるか中止するまで、相手とパワー・ガチンコ・ジャッジする"
         "（両者が山札の上から1枚を表向きにし、パワーが相手以上なら自分の勝ち。表向きにしたカードは山札の下へ）。"
         "その後、こうして自分が勝った回数、次の効果を使う。"
         "▶相手は自身のクリーチャーまたはシールドを1つ選び、持ち主のマナゾーンに置く",
    note="ガチンコ・ジャッジは「負けるか中止するまで」なので、負けるまで必ず続ける（20回で打ち切り）。"
         "相手が何を出すかは全デッキ共通の決まりで決めている（いちばん失って痛くないクリーチャーと、"
         "シールド1つを残り枚数で値踏みして、安いほうを出す）",
    source=SRC["k25_onimaruv"])


# ================================================================ 鎧亜目邪王類 デス＝ヴェルムート（10/77）
def _sc_use(s, j, k):
    """スペース・チャージ：マナゾーンに置かれたカードの文明に合うSC能力を1つ使う
    （合うものが複数あれば、いちばん効く1つを全デッキ共通の決まりで選ぶ）"""
    p = s.P[j]
    if not any(z.k == "k25_verumut" for z in p.board):
        return
    o = s.P[1 - j]
    civ = E.MCIV.get(k, "")
    cands = []
    if "W" in civ:
        t = s.target(j)
        if t is not None:
            cands.append((10 + s.val(t), "W", t))
    if "D" in civ and o.hand:
        cands.append((6, "D", None))
    if "L" in civ and len(p.deck) > 1:
        cands.append((4, "L", None))
    if "F" in civ:
        z = _best_own(s, j)
        if z is not None:
            cands.append((2, "F", z))
    if not cands:
        return
    cands.sort(key=lambda c: -c[0])
    _, mode, t = cands[0]
    if mode == "W":
        s.ev(f"　SC―水：{t.c.name} を持ち主の手札に戻す")
        move(s, j, t, "hand")
    elif mode == "D":
        s.ev("　SC―闇：相手は手札を1枚選んで捨てる")
        discard_choice(s, 1 - j)
    elif mode == "L":
        s.ev("　SC―光：自分の山札の上から1枚をシールド化する")
        s.add_shield(j)
    else:
        s.ev(f"　SC―火：{t.c.name} のパワーを+6000")
        t.pw += 6000


def mi_verumut(s, j, k, src):
    """スペース・チャージ：自分のマナゾーンにカードが置かれた時（manain。src＝元のゾーン）"""
    _sc_use(s, j, k)


add("k25_verumut", "鎧亜目邪王類 デス＝ヴェルムート", 5, "N", power=6000, mach=True,
    races=("jurassiccommanddragon", "command", "dragon", "revolution", "hamukatsu"), pri=7,
    roles="acc rem atk draw",
    enter=lambda s, i, u: s.ramp(i, 2, True),
    brkx=lambda s, i, u: 1 + s.power(i, u, True) // 6000,
    manain=mi_verumut,
    text="マッハファイター。パワード・ブレイカー（パワー6000ごとにシールドをもう1つブレイクする）。"
         "このクリーチャーが出た時、自分の山札の上から2枚をタップしてマナゾーンに置く。"
         "スペース・チャージ（自分のマナゾーンにカードが置かれた時、その文明に合うSC能力を使ってもよい）。"
         "SC―光：自分の山札の上から1枚をシールド化する。"
         "SC―水：相手のクリーチャーを1体選び、持ち主の手札に戻す。"
         "SC―闇：相手は自身の手札を1枚選び、捨てる。"
         "SC―火：このターン、自分のクリーチャー1体のパワーを+6000する",
    source=SRC["k25_verumut"])


# ================================================================ 武将利と威嚇命の決断（11/77）
def _bush_lock(s, i):
    """数字を1つ選ぶ：相手がいちばん唱えたい呪文のコストを選ぶ。(数字, 値打ち)"""
    o = s.P[1 - i]
    sc = {}
    for k in o.hand:
        c = BY_KEY[k]
        if c.kind == "S":
            sc[c.cost] = sc.get(c.cost, 0) + 10 + E.PRI[k]
        elif c.twin:
            sc[c.twin[0]] = sc.get(c.twin[0], 0) + 5
    for k in o.deck:
        c = BY_KEY[k]
        if c.kind == "S":
            sc[c.cost] = sc.get(c.cost, 0) + 1
    if not sc:
        return None, -1
    n = max(sorted(sc), key=sc.get)
    return n, max(1, min(14, sc[n] // 3))


def _bush_one(s, i):
    """3つのモードから1つ選ぶ（同じものを2回選んでもよいので、1回ぶんをこの関数で決める）"""
    n, v1 = _bush_lock(s, i)
    t = s.target(i, lambda z: s.power(1 - i, z) <= 8000)
    v2 = 6 + s.val(t) if t is not None else -1
    z = _best_own(s, i, lambda x: not x.c.noatk)
    v3 = (3 + s.power(i, z) // 3000) if z is not None else -1
    if v2 > 0 and v2 >= v1 and v2 >= v3:
        s.ev(f"　武将利と威嚇命の決断：{t.c.name} を破壊")
        destroy(s, i, t)
    elif v3 > 0 and v3 >= v1:
        z.pw += s.power(i, z)
        z.x["k25_pb"] = s.turn
        s.ev(f"　武将利と威嚇命の決断：{z.c.name} のパワーを2倍にしパワード・ブレイカーを与える")
    elif v1 > 0:
        s.P[1 - i].ban = n
        s.ev(f"　武将利と威嚇命の決断：コスト{n}の呪文を次の自分のターンまで唱えられなくする")


def sp_bushori(s, i):
    for _ in range(2):
        if s.over:
            return
        _bush_one(s, i)


def w_bushori(s, i, u):
    """アタック・チャンス：水・火・自然のパワー8000以上の自分のクリーチャーが攻撃する時、ただで唱えてもよい"""
    if "k25_bushori" not in s.P[i].hand:
        return
    if not (set("WFN") & set(u.c.civ)) or s.power(i, u, True) < 8000:
        return
    if not s.spell_ok(i, 6):
        return
    s.ev("　アタック・チャンス：武将利と威嚇命の決断をコストを支払わずに唱える")
    free_play(s, i, "k25_bushori", "hand")


def bp_bushori(s, i, u):
    """モード3で与えたパワード・ブレイカー（そのターンだけ）"""
    if u.x.get("k25_pb", -1) != s.turn:
        return 0
    return max(0, 1 + s.power(i, u, True) // 6000 - u.c.brk)


add("k25_bushori", "武将利と威嚇命の決断", 6, "WFN", kind="S", pri=7, roles="rem dis atk",
    spell=sp_bushori, atkwatch=w_bushori, brkplus=bp_bushori,
    text="アタック・チャンス：水、火、または自然の、パワー8000以上のクリーチャー"
         "（自分のその条件のクリーチャーが攻撃する時、このカードをコストを支払わずに唱えてもよい）。"
         "次の中から2回選ぶ。同じものを選んでもよい。"
         "▶数字を1つ選ぶ。次の自分のターンのはじめまで、相手はその数字と同じコストの呪文を唱えられない。"
         "▶相手のパワー8000以下のクリーチャーを1体選び、破壊する。"
         "▶自分のクリーチャーを1体選ぶ。このターン、そのクリーチャーのパワーを2倍にし、"
         "「パワード・ブレイカー」を与える",
    note="どのモードを選ぶかは全デッキ共通の決まりで決めている"
         "（取り除ける相手の値打ち／相手の手札と山札にある呪文のコストの偏り／"
         "自分のいちばん攻めているクリーチャーのパワーを比べる）",
    source=SRC["k25_bushori"])


# ================================================================ 連戦の精霊龍 デルザルバーラ（12/77）
def e_delzarbara(s, i, u):
    """出た時、自分の光のクリーチャー1体につき1枚引いてもよい。
    その後、光のコスト4以下のクリーチャーを1体、自分の手札から出してもよい"""
    p = s.P[i]
    n = sum(1 for z in p.board if z.c.kind == "C" and "L" in z.c.civ)
    if n and len(p.deck) > n:
        s.ev(f"　デルザルバーラ：光のクリーチャー{n}体ぶん引く")
        s.draw(i, n)
    best, bv = None, -1
    for k in sorted(set(p.hand)):
        c = BY_KEY[k]
        if c.kind != "C" or c.cost > 4 or "L" not in c.civ or not _can_put(s, i, k):
            continue
        if E.PRI[k] > bv and s.fate(i, k, "hand", False) == "ok":
            best, bv = k, E.PRI[k]
    if best is None:
        return
    p.hand.remove(best)
    if _put_free(s, i, best, "hand"):
        s.ev(f"　デルザルバーラ：手札から {BY_KEY[best].name} を出す")
    else:
        p.hand.append(best)


add("k25_delzarbara", "連戦の精霊龍 デルザルバーラ", 5, "L", power=5000, blocker=True,
    races=("angelcommanddragon", "command", "dragon", "revolution"), pri=7, roles="draw blk acc",
    enter=e_delzarbara,
    text="ブロッカー。このクリーチャーが出た時、自分の光のクリーチャー1体につきカードを1枚引いてもよい。"
         "その後、光のコスト4以下のクリーチャーを1体、自分の手札から出してもよい",
    note="引く枚数より山札が少ない時は引かない（山札切れで負けないため）",
    source=SRC["k25_delzarbara"])
