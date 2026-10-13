"""第2版の出発点になるデッキ12種類（現実のデッキタイプをなぞったもの。カード名ではなく働きで組んである）

(カード構成, 性質)  性質：1＝毎ターン動く、0＝待つ（手札の速攻札を抱えて、決め切れるターンに一気に出す）
"""
from cards2 import max_copies

SEEDS = {
    "連鎖速攻（der'Bande型）": ({"rush": 8, "sa1": 6, "dbl": 4, "dig": 4, "castle": 4, "ramp": 4, "chakra": 2,
                             "m_free": 4, "gs": 4}, 0),
    "小型速攻（赤単型）": ({"sa1": 8, "b1": 8, "rush": 8, "sa2": 4, "dbl": 4, "removal": 4, "gs": 4}, 1),
    "ドラゴンビート（ドギラゴン王道型）": ({"mendel": 8, "sa2": 8, "swap": 4, "rod": 4, "chakra": 4, "sa3": 4, "b3": 4,
                                 "t_big": 4}, 0),
    "全ブレイク（墓地ソース型）": ({"mill": 8, "draw": 8, "wb": 4, "sa1": 8, "removal": 4, "handes_s": 4, "gs": 4}, 0),
    "一手封殺（ウィリデ・ドギラゴン逆型）": ({"castle": 4, "src": 8, "swap_lock": 4, "m_free": 4, "m_summon": 4, "chakra": 4,
                                   "vt": 2, "ramp": 6, "gs": 4}, 0),
    "呪文ループ（創世竜ループ型）": ({"loop_spell": 4, "loop_engine": 4, "ramp": 8, "draw": 8, "t_stop": 4, "t_remove": 4,
                              "removal": 4, "shield": 4}, 0),
    "クリーチャーループ（ドッコイ型）": ({"cl_engine": 4, "cl_piece": 8, "draw": 8, "ramp": 8, "t_stop": 4, "removal": 4,
                                "blocker": 4}, 0),
    "連鎖の特殊勝利（ゴルギーオージャー型）": ({"chain": 8, "chain_fin": 4, "ramp": 8, "draw": 8, "t_stop": 2, "t_tap": 2,
                                     "blocker": 4, "b2": 4}, 0),
    "手札破壊コントロール（邪眼帝型）": ({"handes_c": 8, "handes_s": 8, "chakra": 4, "rod": 4, "blocker": 4, "removal": 4,
                                "b2": 4, "shield": 4}, 0),
    "カウンター（バイケン型）": ({"ninja": 8, "madness": 8, "counter0": 4, "swap": 4, "b2": 8, "draw": 4, "removal": 4}, 0),
    "メタビート": ({"m_free": 4, "m_spell": 4, "m_summon": 4, "m_trig": 4, "b1": 8, "sa1": 8, "vt": 4, "rod": 4}, 1),
    "受け（トリガー）": ({"ramp": 8, "t_stop": 4, "t_tap": 3, "t_remove": 4, "t_wipe": 2, "t_block": 4, "t_big": 3,
                    "counter0": 4, "removal": 4, "b3": 4}, 0),
}
PASSIVE = ({"draw": 8, "shield": 0}, 0)   # 使わない（一人回しは engine2 側で、何もしない相手を作る）


def check(name, counts):
    assert sum(counts.values()) == 40, (name, sum(counts.values()))
    assert all(v <= max_copies(k) for k, v in counts.items()), (name, counts)


for _n, (_c, _a) in SEEDS.items():
    check(_n, _c)
