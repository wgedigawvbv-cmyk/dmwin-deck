#!/usr/bin/env python3
"""ネットで調べた「新しいデッキタイプ」の40枚（創作者が詰まった時に試す）

  出典は遊々亭のデッキ紹介記事（記事番号を source に書いた）。採用カードと枚数は記事の本文（文字）から読み取った。
  記事のリストのうち、次の場合は入れ替えて40枚にそろえ、その内容を subs に書いた。
    ・ドリーム・クリーチャー（デッキに1枚まで）や殿堂入り（1枚まで）の枚数がルールを超えているもの
    ・カード名を特定できなかったもの
  LIMIT は「デッキに入れられる上限」（殿堂入り・ドリーム・禁断は1枚、プレミアム殿堂は0枚＝使えない）。
  カードの説明文から自動で集めるので、カードを足した時に書き足す必要はない。
"""
import re

import engine3                       # noqa: F401  （新カードを登録してから使う）
import envreg
from cards3 import BY_KEY

LIMIT = {
    # もとの札束の殿堂入り（1枚まで）
    "shunsen": 1, "magnum": 1, "saitan": 1, "gio": 1,
}
# ネットで調べたカードのうち、殿堂入り・プレミアム殿堂・禁断は「デッキに1枚まで」。
# カードの説明文（text）や省いた点（note）に書いてある語から自動で集める（書き忘れを防ぐため）。
#   ※ ドリーム・クリーチャーは「同じ名前のものを2体以上バトルゾーンに出せない」という場の制限で、
#      デッキに入れる枚数の制限ではない（公式カバレージの入賞リストに4枚積みが実在する）。場の制限は fx_dream で実装。
#   ※ この分類はカードの説明文からの自動判定なので誤りが混じりうる。デッキを新しく作る時（creator）にだけ使い、
#      公式リストの読み込み（decks8.py）には使わない。
_LIMIT_WORDS = re.compile(r"殿堂入り|プレミアム殿堂|禁断（|禁断の鼓動|デッキに1枚")
for _k, _v in envreg.STATUS.items():
    if _LIMIT_WORDS.search((_v[3] or "") + " " + (_v[1] or "")):
        LIMIT[_k] = 1
# プレミアム殿堂（使用禁止）の判定は、公式カバレージの入賞リストに載っているカードもあって当てにならないため、
# 「使えない（0枚）」扱いはしない。1枚までの扱いにとどめる。
LIMIT["n_kindan"] = 1
LIMIT["n_dokindam"] = 1

ARCHETYPES = {
    "青黒デスパペット": {
        "source": "https://yuyu-tei.jp/ （遊々亭のデッキ紹介記事 26808）",
        "note": "人形（デスパペット）で相手の手札を削りながら殴るデッキ。記事の筆者はドッコイループに強いと書いている",
        "subs": "記事のとおり。以前はドリーム・クリーチャーを「デッキに1枚まで」と誤って読み、切札竜を1枚に削って"
                "裏斬隠 テンサイ・ハートを2枚足していたが、公式カバレージの入賞リストに2枚積みが実在したので記事の3枚に戻した"
                "（ドリーム・クリーチャーの制限は「同じ名前のものは場に1体まで」）",
        "deck": {"n_jenny": 4, "klin": 4, "n_mary": 4, "vamilia": 4, "n_cobra": 4, "n_bolrev": 3, "n_baiken": 3,
                 "tensai": 2, "n_jenimoon": 4, "n_ochakai": 4, "n_petpuppet": 4},
    },
    "クローシス モウジャキンガ": {
        "source": "https://yuyu-tei.jp/ （遊々亭のデッキ紹介記事 27531）",
        "note": "人形と墓地を使う水闇火。アイシャセー神のJクライムで墓地からモウジャキンガを引っぱり出す",
        "subs": "記事のとおりモウジャキンガ4枚に戻した。以前はドリーム・クリーチャーを「デッキに1枚まで」と誤って読み、"
                "1枚に削って邪龍 ジャジーブラッド2枚と同期の妖精1枚を足していた"
                "（ドリーム・クリーチャーの制限は「同じ名前のものは場に1体まで」）",
        "deck": {"n_maxi": 4, "n_ningyo": 4, "klin": 4, "vamilia": 4, "n_aisha": 4, "artel": 4, "n_mouja": 4,
                 "jaouga": 3, "fujin": 3, "n_jazzy": 2, "douki": 2, "n_bonkigo": 2},
    },
    "赤白サムライ": {
        "source": "https://yuyu-tei.jp/ （遊々亭のデッキ紹介記事 26628）",
        "note": "クロスギアをジェネレートしてクロスし、サムライで一気に殴る火光のデッキ",
        "subs": "記事はクロスギアの合計14枚だが、どのクロスギアを何枚かは記事から読み取れなかったので、"
                "代表的な5種に割り振った（ザンゲキ4・ドスファング4・センゴク2・ゴウソク2・タイショウ2）",
        "deck": {"n_kottopi": 4, "chakra": 4, "n_buei": 4, "n_musashi": 4, "n_arkzeos": 4, "n_zaru": 4,
                 "n_mdante12": 1, "n_rafululu": 1, "n_zangeki": 4, "n_dosufang": 4, "n_sengoku": 2,
                 "n_gousoku": 2, "n_taisho": 2},
    },
    "ドロマーロストクルセイダー": {
        "source": "https://yuyu-tei.jp/ （遊々亭のデッキ紹介記事 27232）",
        "note": "ロスト・クルセイダー（ワダ○○ノミコト）で手札を増やし、相手の動きを縛って瀑水神で場を流す",
        "subs": "なし（記事のリストどおり）",
        "deck": {"n_wadachie": 4, "n_wadashisuto": 4, "n_wadakani": 4, "n_wadaebi": 4, "n_fukafuchi": 4,
                 "n_mizuha": 4, "n_orugeito": 2, "vt": 2, "n_lostsign": 4, "n_shukumei": 4, "douki": 4},
    },
    "禁断型火自然バイク": {
        "source": "https://yuyu-tei.jp/ （遊々亭のデッキ紹介記事 27082）",
        "note": "火のコマンドで攻撃して侵略を重ね、コマンドを出すたびに禁断の封印が外れる",
        "subs": "記事の「クライアッシュ1枚」「バイオレッド3枚」はカード名を特定できなかった。"
                "また禁断は4枚と読めたがルール上1枚までなので1枚にした。"
                "空いた7枚は赤い稲妻 テスタ・ロッサ4枚と鬼星の絆 フウジン天3枚に替えた",
        "deck": {"n_toring": 4, "n_rowin": 4, "n_dock": 4, "n_redmad": 4, "n_redzonef": 4, "kabocha": 4,
                 "shuto": 3, "n_redzonez": 1, "n_sekkeizu": 4, "n_kindan": 1, "testa": 4, "fujin": 3},
    },
}


def check(name=None):
    """40枚か、知らないカードがないか、枚数の上限を超えていないかを見る"""
    bad = []
    for n, a in ARCHETYPES.items():
        if name and n != name:
            continue
        d = a["deck"]
        if sum(d.values()) != 40:
            bad.append((n, f"{sum(d.values())}枚"))
        for k, v in d.items():
            if k not in BY_KEY:
                bad.append((n, f"知らないカード {k}"))
            elif v > LIMIT.get(k, 4):
                bad.append((n, f"{BY_KEY[k].name} が{v}枚（上限{LIMIT.get(k, 4)}枚）"))
    return bad


if __name__ == "__main__":
    import playable3
    print("枚数と上限：", check() or "問題なし")
    for n, a in ARCHETYPES.items():
        d = a["deck"]
        print(f"\n【{n}】{sum(d.values())}枚")
        print("  " + "、".join(f"{BY_KEY[k].name}×{v}" for k, v in sorted(d.items(), key=lambda kv: BY_KEY[kv[0]].cost)))
        print("  出せないカード：", playable3.dead(d) or "なし")
