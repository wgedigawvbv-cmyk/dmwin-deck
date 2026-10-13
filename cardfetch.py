#!/usr/bin/env python3
"""知らないカードを調べて、実装の下書きを作る道具

  「このデッキを動かしたいが、カードが実装されていない」という時に使う。
  やることは3つ。

    1. デッキリスト（カード名と枚数）を読んで、**未実装のカードを洗い出す**
    2. そのカードの性能（コスト・文明・種類・種族・パワー・ブレイク数・本文）を**調べて JSON に貯める**
    3. 貯めた JSON から、**実装の下書き（envcards/envNN.py の add(...) の形）と、
       自動で埋められなかった点の TODO** を書き出す

  3つのうち 2 だけは、このコンテナからは**自力でできない**。
  dm.takaratomy.co.jp と dmwiki.net への直接の取得はプロキシに拒否されるため、
  カードの本文を取ってくるのは「Claude が WebFetch で読む」か「あなたの PC で `--fetch` を使う」かになる。
  だからこの道具は、**取ってきた本文を渡せば残りを全部やる**形にしてある。

  ■ 使い方（Windows / PowerShell）

    # (1) デッキリストから未実装のカードを洗い出す
    python cardfetch.py --missing mydeck.json
    python cardfetch.py --missing-text mydeck.txt      # 「4 カード名」の行が並んだテキストでもよい

    # (2a) 自分の PC で本文を取ってくる（PC はこれらのサイトに届くので動く）
    python cardfetch.py --fetch "カード名" "カード名2" --out cardspec_new.json

    # (2b) Claude に読んでもらった本文を貯める（このコンテナではこちら）
    python cardfetch.py --add-text "カード名" --file 本文を貼ったファイル.txt --out cardspec_new.json

    # (3) 実装の下書きを作る
    python cardfetch.py --draft cardspec_new.json --module env36 --prefix k36_ > envcards/env36_draft.py

  ■ 下書きでできること・できないこと
    できる：コスト・文明・カードの種類・種族・パワー・ブレイク数と、
            **文章から機械的に分かるキーワード**（S・トリガー、ブロッカー、スピードアタッカー、
            マッハファイター、ジャストダイバー、G・ストライク、W/T/Q・ブレイカー、
            攻撃できない、プレイヤーを攻撃できない、スレイヤー、進化、NEO進化、革命チェンジ、侵略 など）。
    できない：**キーワードでない効果の中身**（「出た時、〜」の本体）。
            これは差し込み口を選んで書く仕事なので、下書きでは `# TODO:` として本文を貼り出すだけにする。
            ここを人（または Claude）が埋める。嘘の実装を自動生成しないために、わざとそうしてある。
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 本文から機械的に分かるキーワード
CIV_WORD = [("光", "L"), ("水", "W"), ("闇", "D"), ("火", "F"), ("自然", "N")]
KIND_WORD = [("クロスギア", "X"), ("タマシード", "T"), ("城", "G"), ("呪文", "S"),
             ("フィールド", "T"), ("クリーチャー", "C")]
KEYWORDS = [
    # (正規表現, add() に渡す引数, 説明)
    (r"S・?トリガー(?!・?プラス)", ("trig", True), "S・トリガー"),
    (r"G・?ストライク", ("gs", True), "G・ストライク"),
    (r"ブロッカー", ("blocker", True), "ブロッカー"),
    (r"スピードアタッカー", ("sa", True), "スピードアタッカー"),
    (r"マッハファイター", ("mach", True), "マッハファイター"),
    (r"ジャストダイバー", ("jd", True), "ジャストダイバー"),
    (r"W・?ブレイカー", ("brk", 2), "W・ブレイカー"),
    (r"T・?ブレイカー", ("brk", 3), "T・ブレイカー"),
    (r"Q・?ブレイカー", ("brk", 4), "Q・ブレイカー"),
    (r"ワールド・?ブレイカー", ("brk", 99), "ワールド・ブレイカー"),
    (r"このクリーチャーは攻撃できない", ("noatk", True), "攻撃できない"),
    (r"プレイヤーを攻撃できない", ("noatkp", True), "プレイヤーを攻撃できない"),
    (r"Zラッシュ", ("zrush", True), "Zラッシュ"),
    (r"NEO進化", ("neo", True), "NEO進化"),
]
HOOK_HINT = [
    (r"(出た時|出た時、)", "enter=", "出た時"),
    (r"(攻撃する時|攻撃する時、)", "attack=", "攻撃する時"),
    (r"(破壊された時|破壊される時)", "destroyed= / leaverep=", "破壊された時／破壊される時"),
    (r"(離れた時|離れる時)", "left= / leaverep= / leavedest=", "離れた時／離れる時"),
    (r"ターンのはじめ", "tstart= / tstartall=", "ターンのはじめ"),
    (r"ターンの終わり", "tend= / tendall=", "ターンの終わり"),
    (r"革命チェンジ", "changex= ＋ playrule=", "革命チェンジ"),
    (r"侵略", "invade= ＋ engine3.INVZONE", "侵略"),
    (r"EXライフ", "enter=exlife_enter, leaverep=exlife_rep（env0）", "EXライフ"),
    (r"(スーパー)?ガードマン", "guard=env0.guardman(key)", "ガードマン"),
    (r"シールド(ゾーン)?に(置かれた|加えられた)", "shieldin=", "シールドゾーンに置かれた時"),
    (r"マナゾーンに置かれた時", "manain=", "マナゾーンに置かれた時"),
    (r"(タップした時|タップされた時)", "tapwatch=", "タップした時"),
    (r"(引いた時|カードを引いた時)", "drawwatch=", "引いた時"),
    (r"ブロックした時", "blockreact= / blockwatch=", "ブロックした時"),
    (r"選ばれた時", "chosenwatch=", "相手に選ばれた時"),
    (r"(可能なら|必ず)攻撃", "mustatk=", "攻撃の強制"),
    (r"封印", "s.seal / s.unseal（env0）", "封印"),
    (r"超次元|GR|オレガ・?オーラ", "※このシミュレーターに該当ゾーンがない → partial", "超次元／GR／オレガ・オーラ"),
    (r"ハイパー(化|モード)", "engine3.HYPER_POW / HYPER_BRK", "ハイパーモード"),
    (r"スペース・?チャージ", "manain=", "スペース・チャージ"),
    (r"ササゲール", "freeacts= で「ささげて出す手」を作る（env32/env35 を手本に）", "ササゲール"),
]


def norm(x):
    x = unicodedata.normalize("NFKC", str(x))
    return "".join(x.split()).lower()


# ---------------------------------------------------------------- 1. 未実装の洗い出し
def read_deck(path):
    """デッキリストを {カード名: 枚数} で返す。JSON（decks8 の形）とテキストの両方を受ける"""
    raw = open(path, encoding="utf-8").read()
    if raw.lstrip().startswith("{"):
        d = json.loads(raw)
        if "decks" in d:
            out = {}
            for e in d["decks"]:
                for k, v in e["cards"].items():
                    out[k] = out.get(k, 0) + int(v)
            return out
        return {k: int(v) for k, v in d.items()}
    out = {}
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        # 「4 カード名」「カード名 x4」「カード名 4」の3通りを受ける。
        # 最後の形は、数を 1〜4 に限る（枚数は多くて4枚なので）。限らないと
        # 《キング・ザ・スロットン7 / 7777777》のような名前の数字を枚数と読んでしまう。
        m = (re.match(r"^(\d+)\s*[x×･・]?\s*(.+)$", ln) or re.match(r"^(.+?)\s*[x×]\s*(\d+)$", ln)
             or re.match(r"^(.+?)\s+([1-4])$", ln))
        if m:
            a, b = m.groups()
            n, nm = (int(a), b) if a.isdigit() else (int(b), a)
        else:
            n, nm = 1, ln
        out[nm.strip()] = out.get(nm.strip(), 0) + n
    return out


def missing(deck):
    """未実装のカード名を返す（実装済みのものは (名前, キー) で返す）"""
    sys.path.insert(0, HERE)
    import decks8
    idx = decks8._index()
    miss, have = [], []
    for nm, v in deck.items():
        k = decks8.find(nm, idx)
        (have if k else miss).append((nm, v, k))
    return miss, have


# ---------------------------------------------------------------- 2. 本文を取ってくる／貯める
def fetch(names, out_path, wait=5.0):
    """あなたの PC で動かす用：dmwiki からカードの本文を取ってくる。
    このコンテナではプロキシに拒否されるので動かない（その時は --add-text を使う）"""
    try:
        import requests
    except ImportError:
        raise SystemExit("requests が必要です： python -m pip install requests")
    got = load_spec(out_path)
    for nm in names:
        url = "https://dmwiki.net/" + f"《{nm}》"
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "personal-study-script/1.0"})
            r.raise_for_status()
            text = r.text
        except Exception as e:                      # noqa: BLE001
            print(f"× {nm}：取得できませんでした（{e}）", file=sys.stderr)
            continue
        got[nm] = parse(nm, text, url)
        print(f"○ {nm}", file=sys.stderr)
        time.sleep(wait)
    save_spec(got, out_path)
    return got


def add_text(name, text, out_path, source=""):
    """すでに取ってきた本文（Claude が WebFetch で読んだものなど）を貯める"""
    got = load_spec(out_path)
    got[name] = parse(name, text, source or "（手で貼った本文）")
    save_spec(got, out_path)
    return got


def load_spec(path):
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_spec(d, path):
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存：{path}（{len(d)}枚）", file=sys.stderr)


def parse(name, text, source):
    """本文から、機械的に分かるところだけ取り出す（分からない所は None のまま残す）"""
    t = re.sub(r"<[^>]+>", " ", text)
    t = unicodedata.normalize("NFKC", t)
    d = {"name": name, "source": source, "raw": t[:4000]}
    m = re.search(r"(光|水|闇|火|自然)(?:/(?:光|水|闇|火|自然))*\s*文明\s*\(?(\d+)\)?", t)
    if m:
        d["cost"] = int(m.group(2))
    m = re.search(r"コスト\s*[:：]?\s*(\d+)", t)
    if "cost" not in d and m:
        d["cost"] = int(m.group(1))
    civ = "".join(c for w, c in CIV_WORD if re.search(w + r"\s*文明", t))
    if civ:
        d["civ"] = "".join(sorted(set(civ), key="LWDFN".index))
    for w, k in KIND_WORD:
        if re.search(r"種類\s*[:：]?\s*[^\n]{0,12}" + w, t) or re.search(w + r"\s*[:：]", t):
            d["kind"] = k
            break
    m = re.search(r"パワー\s*[:：]?\s*(\d+)", t) or re.search(r"\s(\d{3,6})\s*$", t, re.M)
    if m:
        d["power"] = int(m.group(1))
    d["keywords"] = [desc for pat, _a, desc in KEYWORDS if re.search(pat, t)]
    d["args"] = {}
    for pat, (a, v), _desc in KEYWORDS:
        if re.search(pat, t):
            d["args"][a] = v
    d["hooks"] = [(hint, desc) for pat, hint, desc in HOOK_HINT if re.search(pat, t)]
    return d


# ---------------------------------------------------------------- 3. 実装の下書き
def draft(spec, module, prefix):
    out = [f'"""{module}.py の下書き（cardfetch.py が作った。**そのままでは不完全**）',
           "",
           "  機械的に分かるところ（コスト・文明・種類・種族・パワー・ブレイク数・キーワード）だけ埋めてある。",
           "  `# TODO:` の所は、カードの本文を読んで差し込み口を選んで書く仕事が残っている。",
           "  嘘の実装を自動で作らないために、わざと空けてある。",
           '  書き方は ENV_IMPL_GUIDE.md を読むこと。"""',
           "import engine3 as E                                      # noqa: F401",
           "from cards3 import BY_KEY                                # noqa: F401",
           "",
           "from envreg import add, destroy, free_play, move, opp_all  # noqa: F401",
           "from envcards.env0 import worst_own, own_loss              # noqa: F401",
           ""]
    for no, (nm, d) in enumerate(spec.items(), 1):
        # カード名は日本語なので key には使えない。通し番号にして、名前はコメントで示す
        # （あとで読みやすい綴りに直してよい。key を変えるのは実装前のいまだけ安全）
        ascii_part = re.sub(r"[^a-z0-9]", "", norm(nm))[:14]
        key = prefix + (ascii_part or f"c{no:02d}")
        out.append("")
        out.append("# " + "=" * 60 + f" {nm}")
        out.append(f"# 出典：{d.get('source', '')}")
        for hint, desc in d.get("hooks", []):
            out.append(f"# TODO: {desc} → {hint}")
        body = (d.get("raw") or "").strip().replace("\n", " ")[:600]
        if body:
            out.append(f"# 本文（取ってきたもの。自分の言葉に書き直して text= に入れる）：\n#   {body}")
        args = dict(d.get("args") or {})
        if "cost" not in d:
            out.append("# TODO: コストが読み取れなかった。確かめて 0 を直すこと")
        if not d.get("civ"):
            out.append('# TODO: 文明が読み取れなかった。確かめて "" を直すこと（無色なら "" のまま）')
        if "kind" not in d:
            out.append('# TODO: カードの種類が読み取れなかった。C/S/T/G/X を確かめること')
        out.append("# TODO: races（種族）・pri（重要度）・roles（役割）・text（自分の言葉の説明）を埋めること")
        kw = [f'kind="{d.get("kind", "C")}"']
        if d.get("power"):
            kw.append(f'power={d["power"]}')
        for a, v in args.items():
            kw.append(f"{a}={v!r}")
        kw += ["races=()",
               f'pri={d.get("cost", 0)}',
               'roles=""',
               'status="partial"',
               'note="（ここに省いた点を書く。無ければ status を full にして note を空に）"',
               'text="（ここに効果を自分の言葉で）"',
               f'source="{d.get("source", "")}"']
        out.append(f'add("{key}", "{nm}", {d.get("cost", 0)}, "{d.get("civ", "")}",\n    '
                   + ",\n    ".join(kw) + ")")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 入口
def main():
    ap = argparse.ArgumentParser(description="知らないカードを調べて実装の下書きを作る")
    ap.add_argument("--missing", help="デッキリスト（JSON）から未実装のカードを洗い出す")
    ap.add_argument("--missing-text", help="デッキリスト（テキスト）から未実装のカードを洗い出す")
    ap.add_argument("--fetch", nargs="+", help="カード名を dmwiki から取ってくる（あなたのPCで動かす）")
    ap.add_argument("--add-text", help="すでに取ってきた本文を貯める（カード名）")
    ap.add_argument("--file", help="--add-text で読む本文のファイル")
    ap.add_argument("--source", default="", help="--add-text の出典URL")
    ap.add_argument("--out", default="cardspec_new.json", help="貯める先のJSON")
    ap.add_argument("--draft", help="貯めたJSONから実装の下書きを書き出す")
    ap.add_argument("--module", default="env36")
    ap.add_argument("--prefix", default="k36_")
    ap.add_argument("--wait", type=float, default=5.0, help="取得の間隔（秒）")
    a = ap.parse_args()

    if a.missing or a.missing_text:
        deck = read_deck(a.missing or a.missing_text)
        miss, have = missing(deck)
        print(f"デッキ {sum(deck.values())}枚／{len(deck)}種　実装済み {len(have)}種／未実装 {len(miss)}種\n")
        if miss:
            print("未実装のカード：")
            for nm, v, _k in miss:
                print(f"  ×{v}  {nm}")
            print("\n次にやること：")
            print("  あなたのPCで　python cardfetch.py --fetch " +
                  " ".join(f'"{nm}"' for nm, _v, _k in miss[:3]) +
                  (" …" if len(miss) > 3 else "") + f" --out {a.out}")
            print("  または Claude に本文を読んでもらい　python cardfetch.py --add-text \"カード名\" --file 本文.txt")
            print(f"  そのあと　python cardfetch.py --draft {a.out} --module {a.module} --prefix {a.prefix}")
        else:
            print("すべて実装済みです。decks8 でそのまま読み込めます")
        return
    if a.fetch:
        fetch(a.fetch, a.out, a.wait)
        return
    if a.add_text:
        if not a.file:
            raise SystemExit("--add-text には --file で本文のファイルを渡してください")
        add_text(a.add_text, open(a.file, encoding="utf-8").read(), a.out, a.source)
        return
    if a.draft:
        print(draft(load_spec(a.draft), a.module, a.prefix))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
