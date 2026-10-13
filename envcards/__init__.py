"""現環境の新カード。モジュールごとに分担して実装し、ここで全部を読み込む

  env0 共通の仕組み（クロスギア・封印・禁断・スター進化）／env1 7デッキの1枚差し／env2 ネットから持ってきた札
  env3 青黒デスパペット／env4 クローシス モウジャキンガ・ドロマーロストクルセイダー／env5 赤白サムライ・火自然バイク
  env6 cards3 の抜けの直し／env10〜env15 cardspec0〜5.json の162枚
  env16〜env18 公式カバレージ（DMGP2025-2nd Day2／全国大会2025 関東Aブロック）の入賞リストにあった37枚
    env16 闇王ゼーロ・ブラック・ビッグバン系13枚（key は ea_）
    env17 水闇とルピア・ハキリ系12枚（key は eb_）
    env18 2ブロック構築の12枚（key は ec_）
  env36 DM26-EX1「ますますつよいパック 25の援軍」の15枚（key は k36_）
  読み込む順は名前の並び順（env0, env1, env10, …, env18, env2, …）。env0 以外に依存しないこと。
"""
import importlib
import os

LOADED = []
_here = os.path.dirname(__file__)
MODULES = sorted(f[:-3] for f in os.listdir(_here) if f.startswith("env") and f.endswith(".py"))
for _m in MODULES:
    importlib.import_module(f"envcards.{_m}")
    LOADED.append(_m)
