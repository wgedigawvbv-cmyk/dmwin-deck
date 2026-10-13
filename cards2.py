"""窓で定義したカードプール（第2版）

第1版（cards.py）に、公式カバレージの対戦で見えた仕組みを足したもの。
カードは「具体的な効果」ではなく、窓（いつ × どこから × 何をするか × タダか有料か）に対する働きで定義する。

経路（勝ち筋）
  ATTACK : 場に並べたクリーチャーで割ってダイレクトアタック
  SWAP   : 攻撃中に手札からタダで大型と入れ替える（一手封殺の入れ替え＝ドギラゴン逆型を含む）
  RUSH   : 手札から1ターンで並べて殴り切る（連鎖展開アタッカー＋2回攻撃。der'Bande 型）
  WB     : 墓地をためて、タダで出る全ブレイクで決める（墓地ソース型）
  CHAIN  : 連鎖をそろえて、攻撃した瞬間に特殊勝利（ゴルギーオージャー型）
  LOOP   : 呪文ループで勝つ（創世竜ループ型）
  CLOOP  : クリーチャーの出し入れのループで勝つ（ドッコイループ型）

閉じる効果（場にいる間、相手の窓を閉じる）
  C_TRIG   : 相手はS・トリガーを使えない（G・ストライクは止まらない）
  C_FREE   : 相手はコストを払わずにクリーチャーを出せない（入れ替え・連鎖・タダで出る全ブレイク・手札受け・トリガー召喚）
  C_SPELL  : 相手は各ターン呪文を1回までしか唱えられない
  C_ATTACK : 相手のクリーチャーは出たターンに攻撃できない
  C_SUMMON : 相手は各ターンクリーチャーを1体までしか出せない
  C_HIT    : 相手は各ターン、クリーチャー1体でしか攻撃できない（一手封殺の入れ替えだけが持つ）
  C_SMALL  : 相手はコスト3以下のクリーチャーを出せない（小型一掃の大型だけが持つ）

守り
  先置き：メタクリーチャー（上の閉じる効果）。1枚で複数の働きを持つものがある
  攻撃中：S・トリガー（盾から）、G・ストライク（盾から。相手1体の攻撃を止める）、
          手札受け（攻撃された時に手札からタダで出てブロック）、0コスト受け（ダイレクトアタックを止める）、
          捨てられると出る札（相手の手札破壊を逆用する）
  盾を増やす
"""
from dataclasses import dataclass

CLOSURES = ("C_TRIG", "C_FREE", "C_SPELL", "C_ATTACK", "C_SUMMON", "C_HIT", "C_SMALL")
CLOSURE_JA = {"C_TRIG": "トリガー封じ", "C_FREE": "踏み倒し封じ", "C_SPELL": "呪文制限", "C_ATTACK": "出たターン攻撃不可",
              "C_SUMMON": "展開制限", "C_HIT": "攻撃は1体まで", "C_SMALL": "小型禁止"}
PATHS = ("ATTACK", "SWAP", "RUSH", "WB", "CHAIN", "LOOP", "CLOOP")
PATH_JA = {"ATTACK": "並べて殴る", "SWAP": "入れ替え", "RUSH": "1ターン速攻", "WB": "全ブレイク", "CHAIN": "連鎖の特殊勝利",
           "LOOP": "呪文ループ", "CLOOP": "クリーチャーループ"}
COMBO = {"CHAIN", "LOOP", "CLOOP"}        # 殴らずに勝つ経路
# どの封殺がどの経路を止めるか
STOPS = {"C_FREE": {"SWAP", "CHAIN", "WB", "RUSH"}, "C_SPELL": {"LOOP"}, "C_SUMMON": {"CHAIN", "CLOOP", "RUSH"},
         "C_HIT": {"ATTACK"}, "C_SMALL": {"RUSH", "CLOOP"}, "C_ATTACK": {"RUSH", "CHAIN"}, "C_TRIG": set()}


@dataclass(frozen=True)
class Card:
    key: str
    name: str
    kind: str                 # creature / spell / field（場に残る土台。呪文制限・展開制限の対象外）
    cost: int
    breaks: int = 0
    sa: bool = False          # 出たターンに攻撃できる
    attacks: int = 1          # 1ターンに攻撃できる回数
    blocker: bool = False
    protect: bool = False     # 除去されない
    closes: tuple = ()
    trig: str = ""            # S・トリガー：stop / tap / remove / wipe / block / big
    gstrike: bool = False     # G・ストライク：盾から割られた時、相手1体の攻撃を止める
    ramp: int = 0
    draw: int = 0
    handes: int = 0
    removal: int = 0
    shield_add: int = 0
    role: str = ""


C = Card
POOL = [
    # ---- 土台 ----
    C("ramp", "ブースト", "creature", 2, breaks=1, ramp=1),
    C("mendel", "確率ブースト呪文", "spell", 2, role="mendel"),          # 山札の上2枚のうち、コスト5以上のクリーチャーをマナへ
    C("castle", "軽減の土台", "field", 1, role="castle"),                # 自分のクリーチャーのコストを1減らす
    C("draw", "2ドロー呪文", "spell", 2, draw=2),
    C("mill", "墓地肥やし呪文", "spell", 2, draw=1, role="mill"),        # 山札の上3枚を墓地へ、1枚引く
    # ---- 並べて殴る ----
    C("b1", "小型アタッカー", "creature", 2, breaks=1),
    C("b2", "W・ブレイカー", "creature", 4, breaks=2),
    C("b3", "T・ブレイカー", "creature", 6, breaks=3),
    C("src", "入れ替えの元になる大型", "creature", 3, breaks=2, role="src"),
    # ---- 手札から1ターンで決める ----
    C("sa1", "小型スピードアタッカー", "creature", 3, breaks=1, sa=True),
    C("sa2", "SA W・ブレイカー", "creature", 5, breaks=2, sa=True),
    C("sa3", "SA T・ブレイカー", "creature", 7, breaks=3, sa=True),
    C("rush", "連鎖展開アタッカー", "creature", 3, breaks=1, sa=True, role="rush"),   # 出た時1枚引き、手札のコスト3以下を1体タダで出す
    C("dbl", "2回攻撃フィニッシャー", "creature", 4, breaks=2, sa=True, attacks=2),
    C("dig", "山札から展開する呪文", "spell", 3, role="dig"),            # 山札の上5枚から、コスト3以下のクリーチャーを2体までタダで出す
    C("wb", "墓地がたまると出る全ブレイク", "creature", 7, breaks=99, sa=True, role="wb"),   # 墓地6枚以上でタダ
    # ---- 入れ替え ----
    C("swap", "入れ替えT・ブレイカー", "creature", 7, breaks=3, role="swap"),
    C("swap_lock", "一手封殺の入れ替え", "creature", 8, breaks=3, blocker=True, closes=("C_HIT",), role="swap_lock"),
    # ---- 殴らずに勝つ ----
    C("chain", "連鎖パーツ", "creature", 4, breaks=1, draw=1, role="chain"),
    C("chain_fin", "連鎖フィニッシャー", "creature", 5, breaks=2, sa=True, role="chain_fin"),
    C("loop_spell", "ループ呪文", "spell", 3, role="loop_spell"),
    C("loop_engine", "呪文ループの核", "creature", 3, breaks=1, role="loop_engine"),
    C("cl_engine", "クリーチャーループの核", "creature", 3, breaks=1, draw=1, role="cl_engine"),
    C("cl_piece", "ループのパーツ", "creature", 2, breaks=1, role="cl_piece"),
    # ---- メタクリーチャー（1枚1役） ----
    C("m_trig", "トリガー封じ", "creature", 3, breaks=1, closes=("C_TRIG",)),
    C("m_free", "踏み倒し封じ", "creature", 2, breaks=1, closes=("C_FREE",)),
    C("m_spell", "呪文制限", "creature", 2, breaks=1, closes=("C_SPELL",)),
    C("m_attack", "出たターン攻撃不可", "creature", 3, breaks=1, closes=("C_ATTACK",)),
    C("m_summon", "展開制限", "creature", 3, breaks=1, closes=("C_SUMMON",)),
    # ---- メタクリーチャー（1枚で複数の働き） ----
    C("chakra", "呪文ロック＋ブロッカー＋盾追加", "creature", 4, breaks=2, blocker=True, closes=("C_SPELL",), shield_add=1),
    C("rod", "除去＋展開ロック＋打点", "creature", 5, breaks=2, removal=1, closes=("C_SUMMON",)),
    C("vt", "小型一掃＋小型禁止の大型", "creature", 6, breaks=3, closes=("C_SMALL",), role="vt"),   # 相手の数だけ軽くなる
    # ---- 壊す ----
    C("removal", "除去呪文", "spell", 2, removal=1),
    C("wipe", "全体除去呪文", "spell", 6, removal=3),
    C("handes_c", "手札破壊クリーチャー", "creature", 3, breaks=1, handes=1),
    C("handes_s", "手札破壊呪文", "spell", 2, handes=1),
    # ---- S・トリガー ----
    C("t_stop", "T:ターン終了", "spell", 5, trig="stop"),
    C("t_tap", "T:全体タップ", "spell", 4, trig="tap"),
    C("t_remove", "T:1体除去", "spell", 3, trig="remove", removal=1),
    C("t_wipe", "T:2体除去", "spell", 6, trig="wipe", removal=2),
    C("t_block", "T:ブロッカー召喚", "creature", 4, breaks=1, blocker=True, trig="block"),
    C("t_big", "T:大型召喚", "creature", 6, breaks=3, trig="big"),
    # ---- そのほかの守り ----
    C("gs", "G・ストライクつきクリーチャー", "creature", 3, breaks=1, gstrike=True),
    C("ninja", "手札受け", "creature", 4, breaks=1, blocker=True, role="ninja"),      # 攻撃された時、マナ4以上なら手札からタダで出てブロック
    C("madness", "捨てられると出る札", "creature", 5, breaks=2, role="madness"),      # 相手に捨てさせられるとタダで出て、相手を1体手札に戻す
    C("counter0", "0コスト受け", "creature", 6, breaks=2, role="counter0"),
    C("blocker", "ブロッカー", "creature", 3, breaks=1, blocker=True),
    C("shield", "盾追加呪文", "spell", 3, shield_add=1, draw=1),
]
BY_KEY = {c.key: c for c in POOL}
KEYS = [c.key for c in POOL]

# 替えのきかない特定のカードは4枚まで。役割で定義したカード（現実では複数の別カードが入る）は8枚まで
UNIQUE = {"swap", "swap_lock", "chain_fin", "loop_spell", "loop_engine", "cl_engine", "counter0", "wipe", "sa3",
          "dbl", "wb", "chakra", "rod", "vt", "castle", "dig"}

CHAIN_NEED = 4     # 連鎖の特殊勝利に必要な連鎖カードの数
LOOP_MANA = 5      # 呪文ループに必要なマナ
CLOOP_MANA = 4     # クリーチャーループに必要なマナ
WB_GRAVE = 6       # 全ブレイクがタダになる墓地の枚数


def max_copies(key):
    return 4 if key in UNIQUE else 8


def is_big(c):
    """確率ブースト呪文でマナに置かれる（コスト5以上のクリーチャー）"""
    return c.kind == "creature" and c.cost >= 5


def deck_paths(counts):
    g = counts.get
    paths = set()
    breakers = sum(n * min(BY_KEY[k].breaks, 3) * BY_KEY[k].attacks for k, n in counts.items() if BY_KEY[k].kind == "creature")
    if breakers >= 20:
        paths.add("ATTACK")
    if g("swap", 0) >= 2 or g("swap_lock", 0) >= 2:
        paths.add("SWAP")
    if g("rush", 0) >= 6 or (g("rush", 0) >= 4 and g("dbl", 0) >= 2):
        paths.add("RUSH")
    if g("wb", 0) >= 2 and g("mill", 0) >= 4:
        paths.add("WB")
    if g("chain_fin", 0) >= 2 and g("chain", 0) >= 6:
        paths.add("CHAIN")
    if g("loop_spell", 0) >= 2 and g("loop_engine", 0) >= 2:
        paths.add("LOOP")
    if g("cl_engine", 0) >= 2 and g("cl_piece", 0) >= 4:
        paths.add("CLOOP")
    return paths


def deck_closures(counts):
    out = set()
    for k, n in counts.items():
        if n >= 2:
            out |= set(BY_KEY[k].closes)
    return out


def deck_defense(counts):
    s = lambda f: sum(n for k, n in counts.items() if f(BY_KEY[k]))
    return {
        "triggers": s(lambda c: bool(c.trig)),
        "gstrike": s(lambda c: c.gstrike),
        "hand": counts.get("ninja", 0) + counts.get("counter0", 0) + counts.get("madness", 0),   # 手札からの受け
        "counter0": counts.get("counter0", 0) + counts.get("ninja", 0),
        "blockers": s(lambda c: c.blocker and c.role != "ninja"),
        "removal": s(lambda c: c.removal and not c.trig),
        "handes": s(lambda c: c.handes),
        "sa": s(lambda c: c.sa),
        "big": s(is_big),
    }


def main_path(counts):
    """デッキタイプの呼び名（一番それらしい経路）"""
    p = deck_paths(counts)
    for name in ("CLOOP", "LOOP", "CHAIN", "WB", "RUSH", "SWAP", "ATTACK"):
        if name in p:
            return name
    return "なし"
