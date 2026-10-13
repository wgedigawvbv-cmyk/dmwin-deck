"""窓で定義したカードプール

カードは「具体的な効果」ではなく、窓に対して何をするかで定義する。

窓 = いつ × どこから × 何をするか × タダか有料か

経路（勝ち筋が通る窓の列）
  ATTACK  : 自分のターン・場から・攻撃してシールドを割り、ダイレクトアタック
  SWAP    : 自分の攻撃中・手札から・タダで大型と入れ替える（革命チェンジ型）
  CHAIN   : 自分のターン・手札から・タダで連鎖展開 → 攻撃した瞬間に特殊勝利（ゴルギーオージャー型）
  LOOP    : 自分のターン・手札から・呪文を何度も唱えて勝つ（呪文ループ型）

閉じる効果（場にいる間、相手の窓を閉じる）
  C_TRIG   : 相手はS・トリガーを使えない
  C_FREE   : 相手はコストを払わずにカードを出せない（入れ替え・連鎖・0コスト受け・トリガー召喚を止める）
  C_SPELL  : 相手は各ターン呪文を1回までしか唱えられない
  C_ATTACK : 相手のクリーチャーは出たターンに攻撃できない
  C_SUMMON : 相手は各ターンクリーチャーを2体までしか出せない

守り
  トリガー（シールドから・相手の攻撃中・タダ）：時間を買う／除去／召喚
  0コスト受け（手札から・相手の攻撃中・タダ）：シールド0枚で攻撃されたら攻撃を止める
  ブロッカー、盾追加

閉じたものを壊す／守る
  除去（自分のターン・有料）、手札破壊、保護（場を離れない）
"""
from dataclasses import dataclass, field

CLOSURES = ("C_TRIG", "C_FREE", "C_SPELL", "C_ATTACK", "C_SUMMON")
CLOSURE_JA = {"C_TRIG": "トリガー封じ", "C_FREE": "踏み倒し封じ", "C_SPELL": "呪文制限",
              "C_ATTACK": "出たターン攻撃不可", "C_SUMMON": "展開制限"}
PATHS = ("ATTACK", "SWAP", "CHAIN", "LOOP")
PATH_JA = {"ATTACK": "攻撃で割る", "SWAP": "入れ替え", "CHAIN": "連鎖の特殊勝利", "LOOP": "呪文ループ"}


@dataclass(frozen=True)
class Card:
    key: str
    name: str
    kind: str                 # creature / spell
    cost: int
    breaks: int = 0
    sa: bool = False          # 出たターンに攻撃できる
    blocker: bool = False
    protect: bool = False     # 除去されない（場を離れない）
    closes: tuple = ()        # 閉じる窓
    trig: str = ""            # stop / tap / remove / wipe / block / big
    ramp: int = 0
    draw: int = 0
    handes: int = 0
    removal: int = 0
    shield_add: int = 0
    role: str = ""            # swap / chain / chain_fin / loop_spell / loop_engine / counter0


C = Card
POOL = [
    # 土台
    C("ramp", "ブースト", "creature", 2, breaks=1, ramp=1),
    C("draw", "2ドロー呪文", "spell", 2, draw=2),
    # 攻撃で割る経路
    C("b1", "小型アタッカー", "creature", 2, breaks=1),
    C("b2", "W・ブレイカー", "creature", 4, breaks=2),
    C("b3", "T・ブレイカー", "creature", 6, breaks=3),
    C("sa2", "SA W・ブレイカー", "creature", 5, breaks=2, sa=True),
    C("sa3", "SA T・ブレイカー", "creature", 7, breaks=3, sa=True),
    # 入れ替え経路
    C("swap", "入れ替えT・ブレイカー", "creature", 7, breaks=3, role="swap"),
    # 連鎖の特殊勝利経路
    C("chain", "連鎖パーツ", "creature", 2, breaks=1, role="chain"),
    C("chain_fin", "連鎖フィニッシャー", "creature", 5, breaks=2, sa=True, role="chain_fin"),
    # 呪文ループ経路
    C("loop_spell", "ループ呪文", "spell", 3, role="loop_spell"),
    C("loop_engine", "ループ機関", "creature", 3, breaks=1, role="loop_engine"),
    # 閉じる効果（メタクリーチャー）
    C("m_trig", "トリガー封じ", "creature", 3, breaks=1, closes=("C_TRIG",)),
    C("m_free", "踏み倒し封じ", "creature", 2, breaks=1, closes=("C_FREE",)),
    C("m_spell", "呪文制限", "creature", 2, breaks=1, closes=("C_SPELL",)),
    C("m_attack", "出たターン攻撃不可", "creature", 3, breaks=1, closes=("C_ATTACK",)),
    C("m_summon", "展開制限", "creature", 3, breaks=1, closes=("C_SUMMON",)),
    C("m_free_p", "踏み倒し封じ（保護つき）", "creature", 4, breaks=1, closes=("C_FREE",), protect=True),
    C("m_spell_p", "呪文制限（保護つき）", "creature", 4, breaks=1, closes=("C_SPELL",), protect=True),
    # 壊す
    C("removal", "除去呪文", "spell", 2, removal=1),
    C("wipe", "全体除去呪文", "spell", 6, removal=3),
    C("handes_c", "手札破壊クリーチャー", "creature", 3, breaks=1, handes=1),
    C("handes_s", "手札破壊呪文", "spell", 2, handes=1),
    # S・トリガー（手札から使うときはコストを払う）
    C("t_stop", "T:ターン終了", "spell", 5, trig="stop"),
    C("t_tap", "T:全体タップ", "spell", 4, trig="tap"),
    C("t_remove", "T:1体除去", "spell", 3, trig="remove", removal=1),
    C("t_wipe", "T:2体除去", "spell", 6, trig="wipe", removal=2),
    C("t_block", "T:ブロッカー召喚", "creature", 4, breaks=1, blocker=True, trig="block"),
    C("t_big", "T:大型召喚", "creature", 6, breaks=3, trig="big"),
    # その他の守り
    C("counter0", "0コスト受け", "creature", 6, breaks=2, role="counter0"),
    C("blocker", "ブロッカー", "creature", 3, breaks=1, blocker=True),
    C("shield", "盾追加呪文", "spell", 3, shield_add=1, draw=1),
]
BY_KEY = {c.key: c for c in POOL}

CHAIN_NEED = 4    # 連鎖フィニッシャーが攻撃したときに勝つのに必要な連鎖カードの数（自身を含む）
LOOP_MANA = 5     # 呪文ループに必要なマナ
LOOP_SPELLS = 3   # 呪文ループで1ターンに唱える呪文の数


def deck_paths(counts):
    """デッキが持っている経路（2枚以上入っているもの）"""
    paths = set()
    breakers = sum(n * BY_KEY[k].breaks for k, n in counts.items() if BY_KEY[k].kind == "creature")
    if breakers >= 20:
        paths.add("ATTACK")
    if counts.get("swap", 0) >= 2:
        paths.add("SWAP")
    if counts.get("chain_fin", 0) >= 2 and counts.get("chain", 0) >= 6:
        paths.add("CHAIN")
    if counts.get("loop_spell", 0) >= 2 and counts.get("loop_engine", 0) >= 2:
        paths.add("LOOP")
    return paths


def deck_closures(counts):
    out = set()
    for k, n in counts.items():
        if n >= 2:
            out |= set(BY_KEY[k].closes)
    return out


def deck_defense(counts):
    trig = sum(n for k, n in counts.items() if BY_KEY[k].trig)
    return {
        "triggers": trig,
        "counter0": counts.get("counter0", 0),
        "blockers": sum(n for k, n in counts.items() if BY_KEY[k].blocker),
        "removal": sum(n for k, n in counts.items() if BY_KEY[k].removal and not BY_KEY[k].trig),
        "handes": sum(n for k, n in counts.items() if BY_KEY[k].handes),
    }
