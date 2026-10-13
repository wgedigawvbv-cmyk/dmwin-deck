#!/usr/bin/env python3
"""創作者（creator.py）が「詰まった」ときに、Claude API のネット検索で実在カードを探して cards_net.json に足す（手元のPC用）

  ※ ここで足したカードは「部品の並び」での近似登録になる（status="approx"）。
     本番の82枚は envcards/*.py にカードどおりに書いてあるので、ここで見つけたカードも
     あとで envcards に書き直すのが前提（cards.md の status を見れば、どれが近似かわかる）。

  準備（PowerShell）：
      pip install anthropic
      setx ANTHROPIC_API_KEY "（自分のキー。チャットには貼らない）"      ← 設定後、PowerShell を開き直す

  使い方：
      python creator.py --net claude --net-file cards_net.json          詰まると自動でここが呼ばれる（近似登録）
      python fetch_cards.py cards_net_wishlist.json cards_net.json      単独で試す
      python creator.py --types claude        新しいデッキタイプも自動で探す（fetch_types）

  ・探した結果は netcards.py の形式（部品の並び）に直して書き出す。検査（validate）に通らなかったカードは捨てる。
  ・検索は1回あたり最大 MAX_SEARCHES 回。費用は検索回数と出力量で決まる（目安：数十円〜百数十円）。
  ・出典（https://…）がないカード、カードテキストを確認できなかったカードは受け付けない。
  ・サイトの文章はそのままコピーせず、効果を自分の言葉で要約して text に入れさせる。
"""
import json
import os
import re
import sys

import netcards

MODEL = os.environ.get("DM_AI_MODEL", "claude-sonnet-5-5")
MAX_SEARCHES = 10
MAX_CONTINUE = 4

SYSTEM = (
    "あなたはデュエル・マスターズ（オリジナル形式）のカードに詳しい調査係です。"
    "必ず検索で実在を確認したカードだけを答え、確認できないものは出さないでください。推測でカードを作らないこと。"
)

PROMPT = """デュエル・マスターズのデッキを自分で作るAIが、環境のデッキに勝てず詰まっています。弱点は次のとおりです。

{wish}

この弱点を補う実在のカードを、ネットで検索して8〜12枚探してください。条件：
- 色は {civs} のどれか（それらだけの組み合わせ、または無色）。
- オリジナル形式で使える（プレミアム殿堂は不可。殿堂入り＝1枚制限は可）。
- シミュレーターが表せるのは、クリーチャーか呪文で、キーワードは ブロッカー・スピードアタッカー・マッハファイター・W/T・ブレイカー・S・トリガー・G・ストライク、
  出た時／唱えた時の効果は次の部品の並びだけ：
    ["draw", n]（n枚引く）／["ramp", n]（山札の上からn枚マナへ）／["look", n, "creature" か "any"]（上n枚から1枚を手札へ）／
    ["destroy", {{"max_power": N}}] か ["destroy", {{"max_cost": N}}]（相手1体を破壊）／["bounce", n]／["to_mana", n]／["tap", n]／
    ["discard", n]（相手の手札をランダムにn枚）／["shield_add", n]
- 進化、革命チェンジ、ツインパクト、場にいる間ずっと効く効果、複雑な条件つきの効果を持つカードは選ばない。
  効果の一部が部品で表せないカードは、表せない部分を omitted に書いて入れてよい。

最後に、次の形のJSONだけを ```json で囲んで出力してください（説明文は JSON の外に書かない）：
{{"cards": [
  {{"key": "n_英小文字の識別名", "name": "カード名", "cost": 3, "civ": "N", "kind": "C か S", "power": 3000, "brk": 1,
    "races": ["種族"], "blocker": false, "sa": false, "mach": false, "gs": false, "trig": false,
    "fx": [["draw", 1]], "source": "https://…（確認したカードページ）", "text": "効果を自分の言葉で要約", "omitted": "再現しなかった部分（なければ空）"}}
]}}
文明は L光 W水 D闇 F火 N自然 の文字で、複数なら続けて書く（例 "DF"）。呪文は power を書かない。"""


def _client():
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY が設定されていません（README の準備を見てください）")
    return anthropic.Anthropic()


def ask(prompt, client=None):
    client = client or _client()
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES,
              "user_location": {"type": "approximate", "country": "JP", "timezone": "Asia/Tokyo"}}]
    messages = [{"role": "user", "content": prompt}]
    content = []
    for _ in range(MAX_CONTINUE):
        resp = client.messages.create(model=MODEL, max_tokens=8000, system=SYSTEM, messages=messages, tools=tools)
        content.extend(resp.content)
        if resp.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": resp.content}]
    # 最後の検索結果のあとの文章だけを使う（途中の「検索します」を避ける）
    out, seen = [], False
    for b in content:
        if getattr(b, "type", "") == "web_search_tool_result":
            out, seen = [], True
        elif getattr(b, "type", "") == "text":
            out.append(b.text)
    return "".join(out)


def parse(text):
    """返答から JSON を取り出す（```json で囲まれていなくても、最初の { から最後の } までを試す）"""
    m = re.search(r"```json\s*(.*?)```", text, re.S)
    body = m.group(1) if m else text[text.find("{"):text.rfind("}") + 1]
    data = json.loads(body)
    return data["cards"] if isinstance(data, dict) else data


def screen(cards, known=()):
    """検査を通ったものだけを返す（理由つきで捨てたものも返す）"""
    keep, drop = [], []
    seen = set(known)
    for d in cards:
        d = dict(d)
        why = netcards.validate(d) if d.get("key") not in seen else "key が重複している"
        if why is None and not d.get("text"):
            why = "text が空"
        if why:
            drop.append((d.get("name") or d.get("key"), why))
            continue
        seen.add(d["key"])
        keep.append(d)
    return keep, drop


TYPES_PROMPT = """デュエル・マスターズのデッキを自分で作るAIが、環境のデッキに勝てず詰まっています。弱点は次のとおりです。

{wish}

いまの環境（オリジナル形式）で結果を出している、これまで試していない新しいデッキタイプを、ネットで検索して3〜5種類探してください。
各タイプについて、デッキ紹介記事や大会結果の本文（文字）から、核になるカードとその採用枚数を読み取ってください。画像でしか読めないものは使わない。
カードの文章や記事の文章はそのままコピーせず、自分の言葉で短く要約すること。
シミュレーターに登録済みのカードのキーは次のとおりです（核にはこれを優先して使う）：{known}
登録されていないカードのうち、クリーチャーか呪文で、下の部品だけで表せるものは cards に入れてよい：
  ["draw", n]／["ramp", n]／["look", n, "creature" か "any"]／["destroy", {{"max_power": N}}]／["bounce", n]／["to_mana", n]／["tap", n]／["discard", n]／["shield_add", n]
進化・革命チェンジ・ツインパクト・場に残る効果のカードは入れない（omitted に書いて省く）。

最後に次の形のJSONだけを ```json で囲んで出力してください：
{{"types": [{{"name": "タイプ名", "source": "https://…（記事のURL）", "core": {{"キー": 枚数}}, "note": "自分の言葉の要約", "omitted": "再現できなかった主要カード"}}],
  "cards": [（fetch と同じ形のカード。なければ空）]}}"""


def fetch_types(wishlist, types_path, cards_path, client=None):
    """新しいデッキタイプを検索して types_path に足し、必要なカードを cards_path に足す"""
    from cards3 import BY_KEY
    known = "、".join(sorted(BY_KEY))
    text = ask(TYPES_PROMPT.format(wish=json.dumps(wishlist, ensure_ascii=False, indent=1), known=known), client)
    m = re.search(r"```json\s*(.*?)```", text, re.S)
    data = json.loads(m.group(1) if m else text[text.find("{"):text.rfind("}") + 1])
    old = {"types": []}
    if os.path.exists(types_path):
        old = json.load(open(types_path, encoding="utf-8"))
    names = {t["name"] for t in old["types"]}
    new_types = [t for t in data.get("types", []) if t.get("name") not in names and str(t.get("source", "")).startswith("https://")
                 and isinstance(t.get("core"), dict)]
    old["types"] += new_types
    json.dump(old, open(types_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    oldc = json.load(open(cards_path, encoding="utf-8")).get("cards", []) if os.path.exists(cards_path) else []
    keep, drop = screen(data.get("cards", []), known=[c["key"] for c in oldc])
    for n, w in drop:
        print(f"  捨てた：{n}（{w}）")
    json.dump({"cards": oldc + keep}, open(cards_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  デッキタイプ {len(new_types)}種、カード {len(keep)}枚を足しました")
    return new_types


def fetch(wishlist, out_path, client=None):
    civs = "・".join(sorted({c for w in wishlist["wants"] for c in w["civs"]})) or "任意"
    wish = json.dumps(wishlist, ensure_ascii=False, indent=1)
    text = ask(PROMPT.format(wish=wish, civs=civs), client)
    cards = parse(text)
    old = []
    if os.path.exists(out_path):
        old = json.load(open(out_path, encoding="utf-8")).get("cards", [])
    keep, drop = screen(cards, known=[c["key"] for c in old])
    for n, w in drop:
        print(f"  捨てた：{n}（{w}）")
    json.dump({"cards": old + keep}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  {len(keep)}枚を {out_path} に足しました")
    return keep


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("python fetch_cards.py cards_net_wishlist.json cards_net.json")
    fetch(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
