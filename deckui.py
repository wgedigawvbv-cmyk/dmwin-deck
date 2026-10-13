#!/usr/bin/env python3
r"""デッキを作る画面（HTML）を作る — 608枚のカードを検索して、クリックで40枚を組む

  ■ これは何か
  実装済みのカード全部を1枚のHTMLに書き出す。ブラウザで開くと、
    ・名前・文明・コスト・種類・役割で絞り込んで探せる
    ・クリックで入れる／右クリック（長押し）で抜く。4枚（殿堂入りは1枚）の上限は自動で止まる
    ・マナカーブ・文明の内訳・役割の充足・平均コストがその場で出る
    ・40枚そろったかどうかを常に見ている
    ・「書き出し」で solo.py / matrix8.py がそのまま読めるテキストになる
    ・そのテキストを貼り付けて読み込み直せる（作りかけのデッキを持ち運べる）
    ・**このデッキのゴール（どこを達成とみなすか）をその場で組み立てて、mygoals.json に書き出せる**
  カードの数字と役割は、このシミュレーターの実装そのものから書き出すので、
  **画面に出るカードは必ず一人回しで回せる**（未実装のカードは出てこない）。

  ■ 使い方（PowerShell）
    python deckui.py                       deckui.html を作る（既定）
    python deckui.py --out mypage.html     置き場所を変える
    python deckui.py --cards cards_ui.json カードのデータだけJSONで書き出す
    python deckui.py --open                作ってそのまま既定のブラウザで開く

  できたHTMLは1枚で完結している（外部のファイルを読まない）ので、そのまま配っても動く。

  ■ 画面で作ったデッキを測るまで
    1. 画面の「書き出し」を押して、出てきたテキストを mydeck.txt に保存する
    2. python solo.py --deck-file mydeck.txt --games 3000 --pilot plan
    3. python solo.py --deck-file mydeck.txt --compare 火水闇ジャオウガ --games 3000
    4. 画面の「ゴール」欄で作ったJSONを mygoals.json に保存すると、2 と 3 がゴールも一緒に測る
       （python goals.py --validate で書き方を確かめられる）
"""
import argparse
import json
import os
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))

CIVJA = {"L": "光", "W": "水", "D": "闇", "F": "火", "N": "自然"}
KINDJA = {"C": "クリーチャー", "S": "呪文", "T": "タマシード", "G": "城", "X": "クロスギア", "K": "禁断"}
ROLEJA = {"acc": "加速", "draw": "手札", "rem": "除去", "blk": "ブロッカー", "trg": "受け",
          "atk": "攻め", "dis": "妨害", "fin": "決め札", "shd": "盾追加"}


# ------------------------------------------------------------------ カードのデータ
def card_data():
    """実装済みの全カードを、画面で使う形にして返す"""
    import archetypes
    import decks8                     # noqa: F401  （カードを登録してから使う）
    import engine3 as E
    import envreg
    import roles3
    from cards3 import BY_KEY

    cards = []
    for k, c in sorted(BY_KEY.items(), key=lambda x: (x[1].cost, x[1].name)):
        st = envreg.STATUS.get(k)
        cards.append({
            "k": k,
            "n": c.name,
            "c": c.cost,
            "v": c.civ,                                  # 文明（LWDFN の並び。無色は空）
            "t": c.kind,                                 # C呪文…の種類
            "p": c.power,
            "b": c.brk,                                  # 割れる盾の枚数（W・ブレイカーなら2）
            "r": sorted(roles3.roles(k)),                # 役割
            "x": sorted(c.races),
            "l": archetypes.LIMIT.get(k, 4),             # デッキに入れられる上限
            "s": (st[0] if st else "full"),              # full＝効果を書き切った／partial＝一部省いた
            "i": E.PRI.get(k, c.cost),                   # 重要度（操縦が「強い札」として並べる順）
            "w": "".join(x for x in (
                "SA" if c.sa else "", "MF" if c.mach else "", "BL" if c.blocker else "",
                "ST" if c.trig else "", "GS" if c.gs else "", "JD" if c.jd else "",
                "EV" if c.evo else "", "TW" if c.twin else "") if x),
            "d": (c.note or "")[:400],
        })
    import goals
    return {
        "site": site(),
        "cards": cards,
        "civja": CIVJA, "kindja": KINDJA, "roleja": ROLEJA,
        "target": roles3.TARGET,
        "decks": _sample_decks(),
        "conds": {k: list(v) for k, v in goals.COND.items()},   # 書ける条件（goals.py と同じ表）
        "goals": goals.load(None, mine=False),                  # 見本のゴール（goals.json）
        "hows": list(goals.HOWS),                               # special_win に書ける決まり方
    }


SITE_DEFAULT = {
    "name": "デュエマ デッキ工房",
    "tagline": "実装済みのカードから40枚を組んで、一人回しでデータを取る",
    "author": "", "author_url": "", "source_url": "",
    "unofficial": "このページは個人が作った非公式のツールです。デュエル・マスターズに関する権利は"
                  "株式会社タカラトミーおよびWizards of the Coastに帰属します。"
                  "公式から承認・後援を受けたものではありません。",
    "support": [], "card_links": [], "shops": [], "ad_html": "", "og": {},
}


def site(path=None):
    """公開するときの設定（site.json）を読む。無ければ既定のまま"""
    p = path or os.path.join(HERE, "site.json")
    d = dict(SITE_DEFAULT)
    if os.path.exists(p):
        try:
            raw = json.load(open(p, encoding="utf-8"))
        except Exception as e:                       # noqa: BLE001
            raise SystemExit(f"site.json が読めません：{e}")
        for k, v in raw.items():
            if not k.startswith("_"):
                d[k] = v
    return d


def _sample_decks():
    """画面の「お手本」に出す、実装済みデッキ（名前 → {カード名: 枚数}）

    表に出す名前は **使用者の名前・ハンドルを外した版**（decks8.anon_one）。
    入賞リストの出典は公式カバレージなので情報自体は公開されているが、
    画面に「この人はこのデッキを使った」と出す必要はない。
    大会・順位・デッキの型は残るので、デッキを組む側が失うものはない。"""
    import decks8
    from cards3 import BY_KEY
    names = sorted(decks8.DECKS8)
    anon = decks8.anon_map(names)          # 同じ名前になるものを①②…で見分ける
    out = {}
    for n in names:
        out[decks8.short(anon[n])] = {BY_KEY[k].name: v for k, v in decks8.DECKS8[n].items()}
    return out


# ------------------------------------------------------------------ 画面を作る
# スマホで開く時に要る宣言。これが無いと、携帯のブラウザは幅980pxの画面として組むので、
# 「狭い画面では縦に積む」という指定がまったく効かない（文字が豆粒になる）。
DOCHEAD = """<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!--META-->
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='5' y='3' width='17' height='24' rx='2' fill='%238a2f24'/%3E%3Crect x='10' y='5' width='17' height='24' rx='2' fill='%23c8a227' stroke='%23fbfaf7' stroke-width='1.5'/%3E%3C/svg%3E">
<style>
  :root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px);
          padding-bottom: env(safe-area-inset-bottom, 0px); }
  html, body { margin: 0; }
  body { font: 14px system-ui, sans-serif; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
</head><body>
"""
DOCTAIL = "\n</body></html>\n"


def _meta(st):
    """SNSに貼ったときの見え方（OGP）。公開して広めるなら、ここが入口になる"""
    nm = st.get("name") or SITE_DEFAULT["name"]
    tg = st.get("tagline") or ""
    og = st.get("og") or {}
    out = [f'<meta name="description" content="{_esc(tg)}">',
           f'<meta property="og:title" content="{_esc(nm)}">',
           f'<meta property="og:description" content="{_esc(tg)}">',
           '<meta property="og:type" content="website">',
           '<meta name="twitter:card" content="summary_large_image">']
    if og.get("url"):
        out.append(f'<meta property="og:url" content="{_esc(og["url"])}">')
    if og.get("image"):
        out.append(f'<meta property="og:image" content="{_esc(og["image"])}">')
        out.append(f'<meta name="twitter:image" content="{_esc(og["image"])}">')
    return "\n".join(out) + "\n"


def _esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def document(body, st=None):
    """1枚で完結するHTMLにする（スマホ向けの宣言と、SNS向けの見え方を付ける）"""
    st = st if st is not None else site()
    return DOCHEAD.replace("<!--META-->", _meta(st)) + body + DOCTAIL


def build(out_path, data=None, wrap=True):
    """画面を書き出す。
       wrap=True （既定）…ブラウザでそのまま開ける1枚のHTML
       wrap=False       …Artifact など、外側のHTMLを用意してくれる場所に置く用の中身だけ"""
    d = data or card_data()
    html = PAGE.replace("/*__DATA__*/", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    if wrap:
        html = document(html, d["site"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path, len(html), len(d["cards"])


PAGE = r"""<title>デュエマ デッキ工房</title>
<style>
/* 一列のカード帳＋右に組み立て中のデッキ。狭い画面では縦に積む。
   色は「カードの文明」が主役。背景は紙に寄せた温かい灰で、文明色が沈まないようにした。 */
:root {
  --bg: #efece6;  --panel: #fbfaf7;  --line: #d8d2c6;  --fg: #241f18;  --dim: #6d6457;
  --accent: #8a2f24;  --ok: #2f6b3f;  --warn: #9a6a12;
  --civ-L: #c8a227;  --civ-W: #2b6fb5;  --civ-D: #4a3b63;  --civ-F: #b23a2b;  --civ-N: #3f7a45;
  --civ-X: #8b8275;
  --f-disp: "Zen Old Mincho", "Hiragino Mincho ProN", "Yu Mincho", serif;
  --f-body: "Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", system-ui, sans-serif;
  --f-num: "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #16130f;  --panel: #211d18;  --line: #3a332a;  --fg: #ece6da;  --dim: #9e9484;
  --accent: #e0867a;  --ok: #7fc08f;  --warn: #ddb05a;
  --civ-L: #e3c457;  --civ-W: #6aa8e4;  --civ-D: #9d87c4;  --civ-F: #e4786a;  --civ-N: #6fb87a;
  --civ-X: #a79d8e;  color-scheme: dark;
} }
:root[data-theme="dark"] {
  --bg: #16130f;  --panel: #211d18;  --line: #3a332a;  --fg: #ece6da;  --dim: #9e9484;
  --accent: #e0867a;  --ok: #7fc08f;  --warn: #ddb05a;
  --civ-L: #e3c457;  --civ-W: #6aa8e4;  --civ-D: #9d87c4;  --civ-F: #e4786a;  --civ-N: #6fb87a;
  --civ-X: #a79d8e;  color-scheme: dark;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--fg); font-family: var(--f-body); line-height: 1.55; }
html, body { margin: 0; }
.wrap { padding-inline: 16px; padding-block: 18px 40px; max-width: 1360px; margin: 0 auto; }
h1 { font-family: var(--f-disp); font-size: clamp(1.45rem, 1.1rem + 1.4vw, 2.1rem); margin: 0 0 2px;
     letter-spacing: .02em; text-wrap: balance; }
.sub { color: var(--dim); font-size: .82rem; margin: 0 0 16px; }
.cols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 360px); gap: 18px; align-items: start; }
@media (max-width: 900px) { .cols { grid-template-columns: minmax(0, 1fr); } }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 3px; }
.pad { padding: 12px 13px; }
h2 { font-family: var(--f-disp); font-size: .95rem; margin: 0 0 9px; letter-spacing: .06em;
     text-transform: none; color: var(--fg); }
.eyebrow { font-size: .67rem; letter-spacing: .14em; color: var(--dim); text-transform: uppercase;
           font-family: var(--f-num); }

/* ---- 絞り込み ---- */
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }
input[type=search], select, textarea {
  background: var(--panel); color: var(--fg); border: 1px solid var(--line); border-radius: 2px;
  padding: 6px 8px; font: inherit; font-size: .85rem; min-width: 0; }
input[type=search] { flex: 1 1 200px; }
textarea { width: 100%; font-family: var(--f-num); font-size: .78rem; min-height: 150px; resize: vertical; }
button { background: transparent; color: var(--fg); border: 1px solid var(--line); border-radius: 2px;
  padding: 5px 10px; font: inherit; font-size: .82rem; cursor: pointer; }
button:hover { border-color: var(--accent); color: var(--accent); }
button.on { background: var(--fg); color: var(--panel); border-color: var(--fg); }
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible,
.row:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.civbtn { font-weight: 700; min-width: 34px; }
.civbtn[data-c=L] { color: var(--civ-L); } .civbtn[data-c=W] { color: var(--civ-W); }
.civbtn[data-c=D] { color: var(--civ-D); } .civbtn[data-c=F] { color: var(--civ-F); }
.civbtn[data-c=N] { color: var(--civ-N); } .civbtn[data-c=X] { color: var(--civ-X); }
.civbtn.on { background: currentColor; }
.civbtn.on span { color: var(--panel); }

/* ---- カードの一覧 ---- */
.list { max-height: 60vh; overflow: auto; border-top: 1px solid var(--line); }
.row { display: grid; grid-template-columns: 26px 1fr auto; gap: 8px; align-items: baseline;
  padding: 5px 4px; border-bottom: 1px solid var(--line); cursor: pointer; }
.row:hover { background: color-mix(in srgb, var(--accent) 9%, transparent); }
.row.max { opacity: .45; }
.cost { font-family: var(--f-num); font-variant-numeric: tabular-nums; text-align: right;
  font-size: .85rem; color: var(--dim); }
.nm { min-width: 0; }
.nm b { font-weight: 600; font-size: .86rem; }
.meta { font-size: .7rem; color: var(--dim); display: block; }
.civtag { display: inline-block; font-weight: 700; white-space: nowrap; margin-right: .15em; }
.cnt { font-family: var(--f-num); font-size: .78rem; color: var(--accent); min-width: 2.2em;
  text-align: right; font-variant-numeric: tabular-nums; }
.pill { display: inline-block; font-size: .64rem; border: 1px solid var(--line); border-radius: 999px;
  padding: 0 5px; margin-left: 3px; color: var(--dim); }
.pill.lim { color: var(--accent); border-color: var(--accent); }
.pill.part { color: var(--warn); border-color: var(--warn); }

/* ---- 組み立て中のデッキ ---- */
.count { font-family: var(--f-num); font-size: 1.9rem; font-variant-numeric: tabular-nums; line-height: 1; }
.count.ok { color: var(--ok); } .count.bad { color: var(--accent); }
.deckrow { display: grid; grid-template-columns: 1.6em 1fr auto; gap: 6px; align-items: baseline;
  padding: 2px 0; font-size: .82rem; border-bottom: 1px dotted var(--line); }
.deckrow .x { cursor: pointer; color: var(--dim); font-family: var(--f-num); }
.deckrow .x:hover { color: var(--accent); }
.bars { display: grid; gap: 3px; margin-top: 4px; }
.barrow { display: grid; grid-template-columns: 5em 1fr 2.4em; gap: 6px; align-items: center;
  font-size: .74rem; font-family: var(--f-num); font-variant-numeric: tabular-nums; }
.barrow > span:first-child { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar { height: 9px; background: color-mix(in srgb, var(--fg) 10%, transparent); border-radius: 1px; }
.bar i { display: block; height: 100%; background: var(--accent); border-radius: 1px; }
.bar i.ok { background: var(--ok); }
.bar i.warn { background: var(--warn); }
code { font-family: var(--f-num); font-size: .9em; }
.note { font-size: .74rem; color: var(--dim); margin: 6px 0 0; }
.err { font-size: .78rem; color: var(--accent); margin: 4px 0 0; }
.okmsg { font-size: .78rem; color: var(--ok); margin: 4px 0 0; }
.btnrow { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
details { margin-top: 10px; } summary { cursor: pointer; font-size: .82rem; }
.detail { font-size: .76rem; color: var(--dim); border-top: 1px solid var(--line); padding-top: 8px;
  margin-top: 8px; }
/* ---- ゴール工房：文章で書く ---- */
.writebox { border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 3px;
  padding: 10px 11px; margin-bottom: 12px; background: color-mix(in srgb, var(--accent) 4%, transparent); }
.writebox textarea { min-height: 96px; font-family: var(--f-body); font-size: .88rem; line-height: 1.7; }
.gread { margin-top: 8px; font-size: .8rem; line-height: 1.75; }
.gread .ln { display: grid; grid-template-columns: 1.3em 1fr; gap: 4px; align-items: start;
  padding: 2px 0; border-bottom: 1px dotted var(--line); }
.gread .ok { color: var(--ok); } .gread .ng { color: var(--accent); }
.gread .say { color: var(--fg); }
.gread .warn { color: var(--warn); font-size: .95em; }
.gread .dim { color: var(--dim); }
#gfine > summary { margin: 4px 0 8px; color: var(--dim); }

/* ---- ゴール工房 ---- */
.goalsec { margin-top: 18px; }
.part { border: 1px solid var(--line); border-radius: 3px; padding: 9px 10px; margin-bottom: 8px;
  background: color-mix(in srgb, var(--fg) 3%, transparent); }
.part.goalat { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }
.parthead { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 7px; }
.parthead input[type=text] { flex: 1 1 180px; }
.cond { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 4px 0; }
.cond select { flex: 1 1 260px; max-width: 100%; }
.cond input { flex: 0 1 180px; }
.cond .num { flex: 0 0 5.5em; }
input[type=text], input[type=number] { background: var(--panel); color: var(--fg);
  border: 1px solid var(--line); border-radius: 2px; padding: 5px 7px; font: inherit; font-size: .83rem;
  min-width: 0; }
label.gat { display: inline-flex; align-items: center; gap: 4px; font-size: .76rem; color: var(--dim);
  white-space: nowrap; cursor: pointer; }
label.gat input { accent-color: var(--accent); }
.part.goalat label.gat { color: var(--accent); }
.gcols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 420px); gap: 16px; align-items: start; }
@media (max-width: 900px) { .gcols { grid-template-columns: minmax(0, 1fr); } }
pre.json { background: color-mix(in srgb, var(--fg) 5%, transparent); border: 1px solid var(--line);
  border-radius: 2px; padding: 9px; font-family: var(--f-num); font-size: .72rem; line-height: 1.5;
  overflow: auto; max-height: 420px; margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
/* ---- タブ（スマホでは下に固定、PCでは出さない） ---- */
.tabs { display: none; }
.pane { display: block; }
.runhint { font-size: .78rem; color: var(--dim); }
@media (max-width: 900px) {
  .tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0;
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 20;
    background: var(--panel); border-top: 1px solid var(--line);
    padding-bottom: env(safe-area-inset-bottom, 0px); }
  .tabs button { border: 0; border-radius: 0; padding: 11px 2px 10px; font-size: .78rem;
    color: var(--dim); border-top: 2px solid transparent; }
  .tabs button.on { color: var(--accent); border-top-color: var(--accent); background: transparent; }
  .pane { display: none; }
  .pane.on { display: block; }
  .wrap { padding-bottom: 86px; }
  .list { max-height: none; }
  .row { padding: 9px 4px; }
  .goalsec { margin-top: 0; }
}
/* ---- 1枚ずつ増やす・減らすボタン（指で押せる大きさ） ---- */
.pm { display: inline-flex; gap: 4px; }
.pm button { padding: 3px 9px; font-size: .9rem; line-height: 1.1; min-width: 30px; }
@media (max-width: 900px) { .pm button { padding: 6px 12px; min-width: 38px; } }

/* ---- 回す ---- */
.runopts { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 9px; }
.runopts label { display: grid; gap: 3px; font-size: .74rem; color: var(--dim); }
.runopts select, .runopts input { font-size: .85rem; padding: 6px 7px; }
.go { background: var(--accent); color: var(--panel); border-color: var(--accent);
  font-size: .95rem; padding: 10px 22px; font-weight: 700; }
.go:hover { background: var(--fg); border-color: var(--fg); color: var(--panel); }
.go[disabled] { opacity: .5; cursor: default; }
.prog { height: 10px; background: color-mix(in srgb, var(--fg) 10%, transparent); border-radius: 1px;
  margin: 9px 0 4px; overflow: hidden; }
.prog i { display: block; height: 100%; background: var(--accent); width: 0; transition: width .25s linear; }
@media (prefers-reduced-motion: reduce) { .prog i { transition: none; } }
.big { font-family: var(--f-num); font-size: 1.5rem; font-variant-numeric: tabular-nums; }
.res table { border-collapse: collapse; width: 100%; font-size: .78rem; }
.res th, .res td { text-align: right; padding: 3px 5px; border-bottom: 1px solid var(--line);
  font-variant-numeric: tabular-nums; white-space: nowrap; }
.res td:first-child { white-space: normal; min-width: 7em; }
.res th:first-child, .res td:first-child { text-align: left; }
.res th { color: var(--dim); font-weight: 500; font-size: .7rem; }
.res .tw { overflow-x: auto; }
.gauge { display: inline-block; height: 8px; background: var(--accent); border-radius: 1px;
  vertical-align: middle; }
.gauge.ok { background: var(--ok); }
/* ---- ふもと（名乗りと注記） ---- */
footer { margin-top: 22px; padding-top: 14px; border-top: 1px solid var(--line);
  font-size: .74rem; color: var(--dim); line-height: 1.7; }
footer a { color: var(--accent); }
footer .unof { border-left: 2px solid var(--line); padding-left: 9px; margin: 0 0 8px; }
footer .links { display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0 0; }
.ad { margin-top: 12px; }
.ext { font-size: .72rem; }
.ext a { color: var(--accent); margin-right: 8px; white-space: nowrap; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Old+Mincho:wght@400;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap">

<div class="wrap">
  <h1 id="sitename">デュエマ デッキ工房</h1>
  <p class="sub">実装済みの <b id="ncards">—</b> 枚から40枚を組む。ここに出るカードはすべて
    一人回しで回せる。行を押すと1枚入り、<b>＋</b>／<b>−</b> で増減する。
    <span id="svstate"></span></p>

  <div class="cols">
    <section class="card pad pane on" data-tab="cards">
      <div class="eyebrow">カード帳</div>
      <h2>探す</h2>
      <div class="filters">
        <input type="search" id="q" placeholder="名前・種族・効果の言葉で探す（例：ジョーカーズ、マッハファイター）">
        <select id="kind"><option value="">種類すべて</option></select>
        <select id="role"><option value="">役割すべて</option></select>
        <select id="sort">
          <option value="cost">コスト順</option>
          <option value="pri">重要度順</option>
          <option value="power">パワー順</option>
          <option value="name">名前順</option>
        </select>
      </div>
      <div class="filters" id="civs"></div>
      <div class="filters">
        <input type="search" id="cmin" style="flex:0 0 7em" placeholder="コスト≧" inputmode="numeric">
        <input type="search" id="cmax" style="flex:0 0 7em" placeholder="コスト≦" inputmode="numeric">
        <button id="onlydeck">デッキの札だけ</button>
        <span class="note" id="hits"></span>
      </div>
      <div class="list" id="list"></div>
      <div class="detail" id="detail">カードを選ぶと、効果と省いた点がここに出る。</div>
    </section>

    <aside class="card pad pane" data-tab="deck">
      <div class="eyebrow">組み立て中</div>
      <h2 style="display:flex;align-items:baseline;gap:8px">
        <span class="count bad" id="total">0</span><span class="note" style="margin:0">／40枚</span>
      </h2>
      <input type="search" id="dname" placeholder="デッキの名前（書き出しの1行目になる）" style="width:100%">
      <div id="checks"></div>
      <div id="decklist" style="margin-top:8px"></div>

      <div class="eyebrow" style="margin-top:14px">マナカーブ</div>
      <div class="bars" id="curve"></div>

      <div class="eyebrow" style="margin-top:12px">文明</div>
      <div class="bars" id="civbars"></div>

      <div class="eyebrow" style="margin-top:12px">役割の充足</div>
      <div class="bars" id="rolebars"></div>
      <p class="note">目安の枚数（roles3.py の TARGET）に対して足りているか。
        緑＝足りている／黄＝あと少し／赤＝不足。</p>

      <div class="btnrow">
        <button id="export">書き出し</button>
        <button id="importbtn">読み込み</button>
        <button id="share" hidden>共有リンク</button>
        <button id="clear">全部外す</button>
      </div>
      <p class="note" id="sharemsg" hidden></p>
      <details id="io"><summary>テキスト（solo.py / matrix8.py がそのまま読める形）</summary>
        <textarea id="txt" spellcheck="false" placeholder="4 カード名 … の行を貼り付けて「読み込み」"></textarea>
        <div class="btnrow">
          <button id="copy">コピー</button>
          <button id="doimport">このテキストを読み込む</button>
        </div>
        <p class="note">保存したら <code>python solo.py --deck-file mydeck.txt --games 3000 --pilot plan</code></p>
        <p class="err" id="ioerr"></p>
      </details>
      <details>
        <summary>お手本を読み込む（公式入賞リスト）</summary>
        <select id="sample" style="width:100%;margin-top:6px"></select>
        <div class="btnrow"><button id="loadsample">これを読み込む</button></div>
        <p class="note">大会で実際に使われた40枚。1枚ずつ入れ替えて、何が変わるかを測る出発点に。</p>
      </details>
    </aside>
  </div>

  <section class="card pad goalsec pane" data-tab="goal">
    <div class="eyebrow">ゴール工房</div>
    <h2>このデッキは、どこに届いたら「できた」とするか</h2>
    <p class="note" style="margin-top:0">
      一人回しは既定で「相手の盾を割り切るまでのターン数」を測る。けれどデッキの目的がそれでないなら、
      その数字は意味を持たない。ここで<b>目的を部品に分けて書き、どこをゴール地点と呼ぶかを自分で決める</b>。
      部品ごとに「何割の対戦で・何ターン目にそろったか」「どこで止まったか」が
      <code>solo.py</code> の結果に出るので、<b>何が足りなくて崩れたのか</b>が分かる。</p>

    <div class="gcols">
      <div>
        <div class="filters">
          <input type="text" id="gname" placeholder="ゴールの名前（例：ユニバース着地まで）" style="flex:1 1 220px">
          <select id="gbase" style="flex:0 1 220px"><option value="">見本から写す…</option></select>
        </div>
        <div class="filters">
          <input type="text" id="glabel" placeholder="どういう状態を目指すのか（一行の説明）" style="flex:1 1 100%">
        </div>
        <div class="filters">
          <input type="text" id="gdecks" placeholder="当たるデッキ名（名前の一部。読点か半角カンマ区切り）" style="flex:1 1 100%">
        </div>
        <div class="writebox">
          <div class="eyebrow">文章で書く</div>
          <p class="note" style="margin:2px 0 6px">
            <b>1行に1つ、やりたいことをそのまま書く。</b>条件の種類は選ばなくてよい。
            上から順に「ここまで来たら次」という筋になる。</p>
          <textarea id="gtext" spellcheck="false" rows="5"
            placeholder="モモキングダムXが出る&#10;一度でもユニバースを下に仕込む&#10;ユニバースが表に出る&#10;ユニバースで特殊勝利する"></textarea>
          <div class="btnrow" style="margin-top:6px">
            <button id="gtextgo">この文章でゴールを作る</button>
            <button id="gtextback">いまのゴールを文章にする</button>
          </div>
          <div id="gread" class="gread"></div>
        </div>

        <details id="gfine">
          <summary>細かく直す（条件を1つずつ選ぶ）</summary>
        <div id="parts"></div>
        <div class="btnrow">
          <button id="addpart">部品を足す</button>
          <button id="gclear">はじめから</button>
          <label class="gat" style="margin-left:6px"><input type="checkbox" id="gordered" checked>
            順番どおりに通ったかも数える</label>
        </div>
        <p class="note">部品の条件は<b>その時点の盤面を丸ごと</b>書く（前の部品が満たされている前提にしない）。
          そうしておけば、どの部品をゴール地点に選んでも、その条件だけで正しく判定できる。<br>
          <b>一度でも</b>：盤面は動くので「3体並んだ」のような条件は次の瞬間に崩れる。これを付けると、
          一度満たしたらその後ずっと満たしたことになる。<br>
          「場に出た」を測りたいのに踏み倒しで一瞬しか立たないカードは、条件の種類を
          <b>出来事：この試合でこのカードが場に出た</b>にすると取りこぼさない。</p>
        </details>
      </div>

      <div>
        <div class="eyebrow">mygoals.json に貼り付けるもの</div>
        <pre class="json" id="gjson">—</pre>
        <div class="btnrow">
          <button id="gcopy">コピー</button>
        </div>
        <p class="err" id="gerr"></p>
        <p class="note">
          <code>mygoals.json</code> として <code>solo.py</code> と同じ場所に保存する（無ければ
          <code>python goals.py --init</code> でひな形が作れる）。こちらが <code>goals.json</code> より優先される。<br>
          確かめる：<code>python goals.py --validate</code><br>
          測る：<code>python solo.py --deck-file mydeck.txt --games 3000 --pilot plan</code><br>
          ゴール地点を一時的に変える：<code>--goal-at 部品の名前</code>
        </p>
      </div>
    </div>
  </section>

  <section class="card pad goalsec pane" data-tab="run">
    <div class="eyebrow">回す</div>
    <h2 id="runhead">一人回しを始める</h2>
    <p class="note" id="runintro" style="margin-top:0"></p>
    <div class="runopts">
      <label>戦数
        <select id="rgames">
          <option value="300">300（すぐ終わる）</option>
          <option value="1000" selected>1000</option>
          <option value="3000">3000（細かい数字が安定する）</option>
          <option value="8000">8000</option>
        </select></label>
      <label>操縦
        <select id="rpilot">
          <option value="plan" selected>1手先読み（精度が高い）</option>
          <option value="greedy">決まりだけ（速い）</option>
          <option value="random">でたらめ（下限の目安）</option>
        </select></label>
      <label>先攻・後攻
        <select id="rfirst">
          <option value="both" selected>半分ずつ</option>
          <option value="1st">先攻のみ</option>
          <option value="2nd">後攻のみ</option>
        </select></label>
      <label>相手の壁
        <select id="rwall">
          <option value="blank" selected>受けなし（素の速さ）</option>
          <option value="trigger">S・トリガー8枚</option>
          <option value="gs">G・ストライク8枚</option>
          <option value="heavy">両方多め</option>
        </select></label>
      <label>壁の盾
        <select id="rshields">
          <option value="5" selected>5枚</option>
          <option value="3">3枚</option>
          <option value="1">1枚</option>
          <option value="0">0枚</option>
        </select></label>
      <label>ゴール地点
        <select id="rat"><option value="">ゴールを測らない</option></select></label>
    </div>
    <div class="btnrow">
      <button class="go" id="run">回す</button>
      <button id="savedeck">このデッキをPCに保存</button>
      <button id="savegoal">このゴールをPCに保存</button>
      <button id="loaddeck">保存したデッキを開く</button>
    </div>
    <div class="prog" id="progwrap" hidden><i id="prog"></i></div>
    <p class="note" id="runmsg"></p>
    <div class="res" id="res"></div>
  </section>
  <footer id="foot"></footer>
</div>

<nav class="tabs" id="tabs">
  <button data-go="cards" class="on">カード帳</button>
  <button data-go="deck">デッキ<span id="tabcount"></span></button>
  <button data-go="goal">ゴール</button>
  <button data-go="run">回す</button>
</nav>
<datalist id="cardnames"></datalist>
<datalist id="hownames"></datalist>

<script>
const DATA = /*__DATA__*/;
const C = DATA.cards, BYK = {}, BYN = {};
for (const c of C) { BYK[c.k] = c; BYN[c.n] = c; }
const CIVS = ["L", "W", "D", "F", "N", "X"];          // X＝無色
const ROLES = Object.keys(DATA.roleja);
let deck = {};            // {key: 枚数}
let selCiv = new Set(), onlyDeck = false, sel = null;

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const civOf = (c) => c.v || "X";
const total = () => Object.values(deck).reduce((a, b) => a + b, 0);

/* ---- 絞り込みの部品を組む ---- */
$("ncards").textContent = C.length;
for (const [k, v] of Object.entries(DATA.kindja)) $("kind").insertAdjacentHTML("beforeend", `<option value="${k}">${v}</option>`);
for (const r of ROLES) $("role").insertAdjacentHTML("beforeend", `<option value="${r}">${DATA.roleja[r]}</option>`);
$("civs").innerHTML = CIVS.map((c) =>
  `<button class="civbtn" data-c="${c}"><span>${c === "X" ? "無" : DATA.civja[c]}</span></button>`).join("")
  + `<button id="civany" class="on">文明すべて</button>`;
$("civs").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.id === "civany") { selCiv.clear(); } else {
    const c = b.dataset.c; selCiv.has(c) ? selCiv.delete(c) : selCiv.add(c);
  }
  for (const x of $("civs").querySelectorAll(".civbtn")) x.classList.toggle("on", selCiv.has(x.dataset.c));
  $("civany").classList.toggle("on", selCiv.size === 0);
  render();
});
$("onlydeck").addEventListener("click", () => { onlyDeck = !onlyDeck; $("onlydeck").classList.toggle("on", onlyDeck); render(); });
for (const id of ["q", "kind", "role", "sort", "cmin", "cmax"]) $(id).addEventListener("input", render);

const samples = Object.keys(DATA.decks).sort();
$("sample").innerHTML = samples.map((n) => `<option>${esc(n)}</option>`).join("");

/* ---- カードの一覧 ---- */
function matches(c) {
  const q = $("q").value.trim().toLowerCase();
  if (q) {
    const hay = (c.n + " " + c.x.join(" ") + " " + c.d + " " + c.w).toLowerCase();
    if (!hay.includes(q)) return false;
  }
  const k = $("kind").value; if (k && c.t !== k) return false;
  const r = $("role").value; if (r && !c.r.includes(r)) return false;
  if (selCiv.size) { const cv = civOf(c); if (![...cv].some((x) => selCiv.has(x))) return false; }
  const lo = parseInt($("cmin").value, 10), hi = parseInt($("cmax").value, 10);
  if (!isNaN(lo) && c.c < lo) return false;
  if (!isNaN(hi) && c.c > hi) return false;
  if (onlyDeck && !deck[c.k]) return false;
  return true;
}
function sortKey(c) {
  switch ($("sort").value) {
    case "pri": return [-c.i, c.c, c.n];
    case "power": return [-c.p, c.c, c.n];
    case "name": return [c.n];
    default: return [c.c, -c.i, c.n];
  }
}
function civTags(c) {
  return [...civOf(c)].map((x) => `<span class="civtag" style="color:var(--civ-${x})">${x === "X" ? "無" : DATA.civja[x]}</span>`).join("");
}
function render() {
  const rows = C.filter(matches).sort((a, b) => {
    const ka = sortKey(a), kb = sortKey(b);
    for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; }
    return 0;
  });
  $("hits").textContent = `${rows.length}枚`;
  $("list").innerHTML = rows.map((c) => {
    const n = deck[c.k] || 0, full = n >= c.l;
    const pills = (c.l < 4 ? `<span class="pill lim">${c.l}枚まで</span>` : "")
      + (c.s !== "full" ? `<span class="pill part">一部省略</span>` : "")
      + (c.w ? `<span class="pill">${c.w}</span>` : "");
    return `<div class="row${full ? " max" : ""}" tabindex="0" data-k="${c.k}">
      <span class="cost">${c.c}</span>
      <span class="nm"><b>${esc(c.n)}</b>${pills}
        <span class="meta">${civTags(c)} ${DATA.kindja[c.t]}${c.t === "C" ? " " + c.p : ""}
          ${c.r.map((r) => DATA.roleja[r]).join("・")}</span></span>
      <span class="pm"><button data-add="${c.k}" aria-label="1枚入れる">＋</button>
        <span class="cnt">${n ? n + "枚" : ""}</span>
        ${n ? `<button data-sub="${c.k}" aria-label="1枚抜く">−</button>` : ""}</span></div>`;
  }).join("") || `<p class="note" style="padding:10px">当てはまるカードがありません。</p>`;
  for (const el of $("list").querySelectorAll("[data-add]")) el.addEventListener("click", (e) => {
    e.stopPropagation(); add(el.dataset.add, 1);
  });
  for (const el of $("list").querySelectorAll("[data-sub]")) el.addEventListener("click", (e) => {
    e.stopPropagation(); add(el.dataset.sub, -1);
  });
  for (const el of $("list").querySelectorAll(".row")) {
    el.addEventListener("click", () => add(el.dataset.k, 1));
    el.addEventListener("contextmenu", (e) => { e.preventDefault(); add(el.dataset.k, -1); });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); add(el.dataset.k, 1); }
      if (e.key === "Backspace" || e.key === "-") { e.preventDefault(); add(el.dataset.k, -1); }
    });
    el.addEventListener("mouseenter", () => showDetail(el.dataset.k));
    el.addEventListener("focus", () => showDetail(el.dataset.k));
  }
}
function showDetail(k) {
  const c = BYK[k]; if (!c) return;
  sel = k;
  const civ = [...civOf(c)].map((x) => (x === "X" ? "無色" : DATA.civja[x])).join("／");
  $("detail").innerHTML = `<b>${esc(c.n)}</b>　コスト${c.c}・${civ}・${DATA.kindja[c.t]}`
    + (c.t === "C" ? `・パワー${c.p}・盾${c.b}枚割る` : "")
    + (c.x.length ? `　種族 ${esc(c.x.join("／"))}` : "")
    + (c.r.length ? `　役割 ${c.r.map((r) => DATA.roleja[r]).join("・")}` : "")
    + (c.l < 4 ? `　<span style="color:var(--accent)">デッキに${c.l}枚まで</span>` : "")
    + (c.s !== "full" ? `　<span style="color:var(--warn)">実装は一部省略</span>` : "")
    + (c.d ? `<br>${esc(c.d)}` : "")
    + extLinks(c);
}

/* ---- デッキの出し入れ ---- */
function add(k, n) {
  const c = BYK[k]; if (!c) return;
  const cur = deck[k] || 0;
  let v = cur + n;
  if (v < 0) v = 0;
  // 上限より増やすことはできないが、**すでに上限を超えて入っている分は削らない**。
  // 殿堂の判定はカードの説明文からの自動判定なので誤りうる（decks8.py と同じ扱い）。
  if (v > c.l && v > cur) v = Math.max(cur, c.l);
  if (n > 0 && total() - cur + v > 40 && v > cur) v = Math.max(cur, 40 - (total() - cur));
  if (v) deck[k] = v; else delete deck[k];
  update();
}
function update() {
  render(); drawDeck(); save();
  const t = total();
  $("tabcount").textContent = t ? ` ${t}` : "";
}

function bar(label, v, top, cls) {
  const w = Math.max(0, Math.min(1, top ? v / top : 0)) * 100;
  return `<div class="barrow"><span>${label}</span><span class="bar"><i class="${cls || ""}" style="width:${w}%"></i></span><span>${v}</span></div>`;
}
function drawDeck() {
  const t = total();
  $("total").textContent = t;
  $("total").className = "count " + (t === 40 ? "ok" : "bad");
  const rows = Object.entries(deck).map(([k, n]) => [BYK[k], n])
    .sort((a, b) => a[0].c - b[0].c || a[0].n.localeCompare(b[0].n, "ja"));
  $("decklist").innerHTML = rows.length ? rows.map(([c, n]) =>
    `<div class="deckrow"><span class="cnt">${n}</span>
      <span style="min-width:0">${civTags(c)} ${esc(c.n)}</span>
      <span class="x" data-k="${c.k}" role="button" tabindex="0" aria-label="1枚抜く">×</span></div>`).join("")
    : `<p class="note">まだ1枚も入っていない。左の一覧から選ぶか、下の「お手本を読み込む」から。</p>`;
  for (const el of $("decklist").querySelectorAll(".x")) {
    el.addEventListener("click", () => add(el.dataset.k, -1));
    el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); add(el.dataset.k, -1); } });
  }
  // マナカーブ
  const cv = {}; let sum = 0;
  for (const [c, n] of rows) { const b = Math.min(c.c, 8); cv[b] = (cv[b] || 0) + n; sum += c.c * n; }
  const top = Math.max(4, ...Object.values(cv));
  $("curve").innerHTML = [1, 2, 3, 4, 5, 6, 7, 8].map((i) =>
    bar(i === 8 ? "8+" : String(i), cv[i] || 0, top)).join("")
    + (cv[0] ? bar("0", cv[0], top) : "")
    + `<p class="note">平均コスト ${t ? (sum / t).toFixed(2) : "—"}　／　
       3コスト以下 ${rows.reduce((a, [c, n]) => a + (c.c <= 3 ? n : 0), 0)}枚</p>`;
  // 文明
  const cc = {};
  for (const [c, n] of rows) for (const x of civOf(c)) cc[x] = (cc[x] || 0) + n;
  const ctop = Math.max(4, ...Object.values(cc));
  $("civbars").innerHTML = CIVS.filter((x) => cc[x]).map((x) =>
    `<div class="barrow"><span style="color:var(--civ-${x})">${x === "X" ? "無" : DATA.civja[x]}</span>
      <span class="bar"><i style="width:${(cc[x] / ctop) * 100}%;background:var(--civ-${x})"></i></span>
      <span>${cc[x]}</span></div>`).join("")
    || `<p class="note">—</p>`;
  // 役割
  const rc = {};
  for (const [c, n] of rows) for (const r of c.r) rc[r] = (rc[r] || 0) + n;
  $("rolebars").innerHTML = ROLES.map((r) => {
    const v = rc[r] || 0, tg = DATA.target[r] || 1;
    const cls = v >= tg ? "ok" : v >= tg * 0.6 ? "warn" : "";
    return bar(DATA.roleja[r], v, tg, cls);
  }).join("");
  // 点検
  const err = [], warn = [];
  if (t !== 40) err.push(t < 40 ? `あと${40 - t}枚` : `${t - 40}枚多い`);
  for (const [c, n] of rows) {
    if (n > 4) err.push(`${c.n} が${n}枚（同じカードは4枚まで）`);
    else if (n > c.l) warn.push(`${c.n} が${n}枚（殿堂の自動判定では${c.l}枚まで。`
      + `この判定はカードの説明文から自動で付けているので、外れていることもあります）`);
  }
  const kinds = Object.keys(cc).filter((x) => x !== "X").length;
  if (kinds >= 4 && t >= 20) warn.push(`${kinds}文明。色が足りずに使えない事故が増える`);
  const acc = rc.acc || 0;
  if (t >= 30 && acc < 4 && (sum / t) > 4.2) warn.push("平均コストが重いのに加速が少ない");
  const trg = rc.trg || 0;
  if (t >= 30 && trg === 0) warn.push("受け（S・トリガー）が0枚。先に殴られると止められない");
  $("checks").innerHTML = (err.length ? `<p class="err">${err.map(esc).join("／")}</p>` : `<p class="okmsg">40枚そろっている。枚数の上限も満たしている。</p>`)
    + (warn.length ? `<p class="note">気になる点：${warn.map(esc).join("／")}</p>` : "");
}

/* ---- 書き出し・読み込み ---- */
function toText() {
  const nm = $("dname").value.trim();
  const rows = Object.entries(deck).map(([k, n]) => [BYK[k], n])
    .sort((a, b) => a[0].c - b[0].c || a[0].n.localeCompare(b[0].n, "ja"));
  return (nm ? `# ${nm}\n` : "") + `# ${total()}枚（デュエマ デッキ工房で作成）\n`
    + rows.map(([c, n]) => `${n} ${c.n}`).join("\n") + "\n";
}
$("export").addEventListener("click", () => { $("io").open = true; $("txt").value = toText(); $("ioerr").textContent = ""; $("txt").focus(); });
$("importbtn").addEventListener("click", () => { $("io").open = true; $("txt").focus(); });
$("copy").addEventListener("click", async () => {
  const el = $("txt"); if (!el.value) el.value = toText();
  try { await navigator.clipboard.writeText(el.value); $("ioerr").textContent = "コピーしました"; }
  catch (e) { el.select(); $("ioerr").textContent = "コピーできませんでした。選択したので Ctrl+C で。"; }
});
function doImport(text) {
  const miss = [], out = {};
  for (let ln of text.split(/\r?\n/)) {
    ln = ln.trim(); if (!ln || ln.startsWith("#")) continue;
    // 「4 カード名」「カード名 x4」「カード名 4」の3通り。最後の形は数を1〜4に限る
    // （限らないと《キング・ザ・スロットン7 / 7777777》の数字を枚数と読んでしまう）
    let m = ln.match(/^(\d+)\s*[x×･・]?\s*(.+)$/) || ln.match(/^(.+?)\s*[x×]\s*(\d+)$/)
         || ln.match(/^(.+?)\s+([1-4])$/);
    let n = 1, nm = ln;
    if (m) { if (/^\d+$/.test(m[1])) { n = +m[1]; nm = m[2]; } else { n = +m[2]; nm = m[1]; } }
    nm = nm.trim();
    let c = BYN[nm];
    if (!c) { const h = C.filter((x) => x.n.includes(nm) || nm.includes(x.n)); if (h.length === 1) c = h[0]; }
    if (!c) { miss.push(nm); continue; }
    out[c.k] = (out[c.k] || 0) + n;     // 上限は削らずに、下の点検で注意として出す
  }
  deck = out;
  goalForDeck($("dname").value);
  update();
  $("ioerr").textContent = miss.length ? `読めなかった行：${miss.join("、")}（未実装のカードかもしれません）` : "読み込みました";
}
$("doimport").addEventListener("click", () => doImport($("txt").value));
$("clear").addEventListener("click", () => { deck = {}; update(); });
$("loadsample").addEventListener("click", () => {
  const d = DATA.decks[$("sample").value] || {};
  deck = {}; for (const [nm, n] of Object.entries(d)) { const c = BYN[nm]; if (c) deck[c.k] = n; }
  $("dname").value = $("sample").value;
  goalForDeck($("sample").value);
  update();
});
$("dname").addEventListener("input", save);

/* ================================================================ ゴール工房
   目的を「部品」に分けて書き、どこをゴール地点と呼ぶかを自分で決める。
   条件の種類は goals.py の COND と同じ表を読んでいるので、Python 側に条件を足せばここにも出る。 */
const CONDS = DATA.conds || {};
let goal = null;                 // {name, label, decks, at, parts:[{name, conds:[{t,v,n}]}]}

$("cardnames").innerHTML = C.map((c) => `<option value="${esc(c.n)}">`).join("");
$("hownames").innerHTML = (DATA.hows || []).map((h) => `<option value="${esc(h)}">`).join("");
$("gbase").innerHTML = `<option value="">見本から写す…</option>`
  + (DATA.goals || []).map((g, i) => `<option value="${i}">${esc(g.name)}</option>`).join("");

function blankGoal(nm) {
  return { name: nm || "新しいゴール", label: "", decks: [], at: "殴り切れる形", ordered: true,
           auto: true,                    // 自分で書き換えるまでは、デッキに合わせて付け替える
           parts: [{ name: "並べる", mode: "all", conds: [{ t: "creatures_at_least", v: 3, n: 1 }] },
                   { name: "殴り切れる形", mode: "all", conds: [{ t: "breaks_at_least", v: 6, n: 1 }] },
                   { name: "勝つ", mode: "all", conds: [{ t: "win", v: true, n: 1 }] }] };
}
/* goals.json の形（条件の入れ子）を、画面の形（部品＋ANDの条件の並び）に読み直す。
   読み切れない書き方（any / not の入れ子）は、そのまま文字として残して触らせない。 */
function oneCond(w) {
  const orig = w;
  if (!w || typeof w !== "object") return { raw: w };
  let ever = false, neg = false;
  if (w.ever && Object.keys(w).length === 1) { ever = true; w = w.ever; }
  if (w && w.not && Object.keys(w).length === 1) { neg = true; w = w.not; }
  if (!w || typeof w !== "object") return { raw: orig };
  const keys = Object.keys(w).filter((k) => k !== "count");
  if (keys.length !== 1 || !CONDS[keys[0]]) return { raw: orig };
  const t = keys[0];
  let v = w[t];
  if (CONDS[t][1] === "cards" && Array.isArray(v)) v = v.join("、");
  return { t, v, n: w.count || 1, neg, ever };
}
function condsFrom(when) {
  const mode = (when && when.any) ? "any" : "all";
  const list = (when && (when.all || when.any)) ? (when.all || when.any) : [when];
  return { mode, conds: list.map(oneCond) };
}
function goalFrom(g) {
  const parts = (g.parts || [{ name: g.name, when: g.when }]).map((p) => {
    const c = condsFrom(p.when);
    return { name: p.name || "部品", mode: c.mode, conds: c.conds };
  });
  return { name: g.name || "", label: g.label || "", decks: (g.decks || []).slice(),
           ordered: g.ordered !== false,
           at: g.goal_at || parts[parts.length - 1].name, parts };
}
function goalForDeck(nm) {
  /* デッキを読み込んだ時、ゴールもそのデッキのものに付け替える。
     ただし**自分で書いたゴールには触らない**（auto が false になっている）。 */
  if (goal && goal.auto === false) return;
  const hit = (DATA.goals || []).find((g) => (g.decks || []).some((d) => d && nm.includes(d)));
  goal = hit ? goalFrom(hit) : blankGoal(nm);
  goal.auto = true;
  if (!hit) goal.decks = nm ? [nm] : [];
  drawGoal();
}
function drawGoal() {
  if (!goal) return;
  $("gname").value = goal.name;
  $("glabel").value = goal.label;
  $("gdecks").value = goal.decks.join("、");
  $("gordered").checked = goal.ordered !== false;
  const opts = Object.entries(CONDS).map(([k, v]) => [k, v[0]]);
  $("parts").innerHTML = goal.parts.map((p, pi) => {
    const rows = p.conds.map((c, ci) => {
      if (c.raw) {
        return `<div class="cond"><span class="note" style="margin:0">この条件は画面では編集できません：
          <code>${esc(JSON.stringify(c.raw))}</code></span>
          <button data-del="${pi}.${ci}">×</button></div>`;
      }
      const spec = CONDS[c.t] || ["", "num", false];
      let input;
      if (spec[1] === "num") {
        input = `<input type="number" class="num" data-v="${pi}.${ci}" value="${esc(c.v)}">`;
      } else if (spec[1] === "bool") {
        input = `<select data-v="${pi}.${ci}" style="flex:0 1 9em">
          <option value="true"${c.v !== false ? " selected" : ""}>はい</option>
          <option value="false"${c.v === false ? " selected" : ""}>いいえ</option></select>`;
      } else if (spec[1] === "how") {
        input = `<input type="text" list="hownames" data-v="${pi}.${ci}"
          value="${c.v === true ? "" : esc(c.v)}" placeholder="（空＝どの特殊勝利でも）">`;
      } else {
        input = `<input type="text" list="cardnames" data-v="${pi}.${ci}" value="${esc(c.v)}"
          placeholder="${spec[1] === "cards" ? "カード名を読点で区切る" : "カード名"}">`;
      }
      const cnt = spec[2] ? `<input type="number" class="num" data-n="${pi}.${ci}" value="${c.n || 1}"
        title="何枚・何体で満たすか" min="1">` : "";
      return `<div class="cond">
        <select data-t="${pi}.${ci}">${opts.map(([k, ja]) =>
          `<option value="${k}"${k === c.t ? " selected" : ""}>${esc(ja)}</option>`).join("")}</select>
        ${input}${cnt}
        <label class="gat" title="一度でも満たしたら、その後ずっと満たしたことにする">
          <input type="checkbox" data-ever="${pi}.${ci}" ${c.ever ? "checked" : ""}>一度でも</label>
        <label class="gat"><input type="checkbox" data-neg="${pi}.${ci}"
          ${c.neg ? "checked" : ""}>でない</label>
        <button data-del="${pi}.${ci}">×</button></div>`;
    }).join("");
    return `<div class="part${p.name === goal.at ? " goalat" : ""}">
      <div class="parthead">
        <span class="cnt">${pi + 1}</span>
        <input type="text" data-pn="${pi}" value="${esc(p.name)}" placeholder="部品の名前">
        <select data-pm="${pi}" style="flex:0 1 11em" title="この部品の条件のつなぎ方">
          <option value="all"${p.mode !== "any" ? " selected" : ""}>すべて満たす</option>
          <option value="any"${p.mode === "any" ? " selected" : ""}>どれか満たす</option></select>
        <label class="gat"><input type="radio" name="gat" value="${pi}"
          ${p.name === goal.at ? "checked" : ""}>ここをゴール地点にする</label>
        <button data-pdel="${pi}">部品を消す</button>
      </div>
      ${rows}
      <div class="btnrow"><button data-cadd="${pi}">条件を足す</button></div>
    </div>`;
  }).join("");
  bindGoal();
  drawJson();
  if (typeof fillAt === "function") fillAt();
}
function bindGoal() {
  const P = $("parts");
  for (const el of P.querySelectorAll("select,input,button"))
    el.addEventListener("change", () => { goal.auto = false; });
  for (const el of P.querySelectorAll("[data-t]")) el.addEventListener("change", () => {
    const [pi, ci] = el.dataset.t.split(".").map(Number);
    const c = goal.parts[pi].conds[ci];
    c.t = el.value;
    const kind = (CONDS[c.t] || ["", "num"])[1];
    c.v = kind === "num" ? 1 : kind === "bool" ? true : kind === "how" ? true : "";
    drawGoal();
  });
  for (const el of P.querySelectorAll("[data-v]")) el.addEventListener("input", () => {
    const [pi, ci] = el.dataset.v.split(".").map(Number);
    const c = goal.parts[pi].conds[ci];
    const kind = (CONDS[c.t] || ["", "num"])[1];
    if (kind === "num") c.v = parseInt(el.value, 10) || 0;
    else if (kind === "bool") c.v = el.value === "true";
    else if (kind === "how") c.v = el.value.trim() === "" ? true : el.value.trim();
    else c.v = el.value;
    drawJson();
  });
  for (const el of P.querySelectorAll("[data-n]")) el.addEventListener("input", () => {
    const [pi, ci] = el.dataset.n.split(".").map(Number);
    goal.parts[pi].conds[ci].n = Math.max(1, parseInt(el.value, 10) || 1);
    drawJson();
  });
  for (const el of P.querySelectorAll("[data-neg]")) el.addEventListener("change", () => {
    const [pi, ci] = el.dataset.neg.split(".").map(Number);
    goal.parts[pi].conds[ci].neg = el.checked; drawJson();
  });
  for (const el of P.querySelectorAll("[data-ever]")) el.addEventListener("change", () => {
    const [pi, ci] = el.dataset.ever.split(".").map(Number);
    goal.parts[pi].conds[ci].ever = el.checked; drawJson();
  });
  for (const el of P.querySelectorAll("[data-pm]")) el.addEventListener("change", () => {
    goal.parts[+el.dataset.pm].mode = el.value; drawJson();
  });
  for (const el of P.querySelectorAll("[data-pn]")) el.addEventListener("input", () => {
    const pi = +el.dataset.pn, old = goal.parts[pi].name;
    goal.parts[pi].name = el.value;
    if (goal.at === old) goal.at = el.value;
    drawJson();
  });
  for (const el of P.querySelectorAll("[data-del]")) el.addEventListener("click", () => {
    const [pi, ci] = el.dataset.del.split(".").map(Number);
    goal.parts[pi].conds.splice(ci, 1); drawGoal();
  });
  for (const el of P.querySelectorAll("[data-cadd]")) el.addEventListener("click", () => {
    goal.parts[+el.dataset.cadd].conds.push({ t: "creatures_at_least", v: 3, n: 1, neg: false });
    drawGoal();
  });
  for (const el of P.querySelectorAll("[data-pdel]")) el.addEventListener("click", () => {
    if (goal.parts.length <= 1) return;
    goal.parts.splice(+el.dataset.pdel, 1);
    if (!goal.parts.some((p) => p.name === goal.at)) goal.at = goal.parts[goal.parts.length - 1].name;
    drawGoal();
  });
  for (const el of P.querySelectorAll('input[name=gat]')) el.addEventListener("change", () => {
    goal.at = goal.parts[+el.value].name; drawGoal();
  });
}
function condJson(c) {
  if (c.raw) return c.raw;
  const spec = CONDS[c.t] || ["", "num", false];
  let v = c.v;
  if (spec[1] === "cards") v = String(v).split(/[、,]/).map((x) => x.trim()).filter(Boolean);
  const o = {}; o[c.t] = v;
  if (spec[2] && c.n > 1) o.count = c.n;
  const r = c.neg ? { not: o } : o;
  return c.ever ? { ever: r } : r;
}
function goalJson() {
  const parts = goal.parts.map((p) => {
    const cs = p.conds.map(condJson);
    if (cs.length === 1) return { name: p.name, when: cs[0] };
    return { name: p.name, when: p.mode === "any" ? { any: cs } : { all: cs } };
  });
  const o = { name: goal.name, label: goal.label, decks: goal.decks.filter(Boolean),
              goal_at: goal.at, ordered: goal.ordered !== false, parts };
  return { _doc: "自分のゴール表。goals.json より優先されます。python goals.py --validate で確かめられます。",
           goals: [o] };
}
function drawJson() {
  const errs = [];
  if (!goal.name.trim()) errs.push("ゴールの名前がまだ");
  const names = goal.parts.map((p) => p.name.trim());
  if (names.some((x) => !x)) errs.push("名前の無い部品がある");
  if (new Set(names).size !== names.length) errs.push("同じ名前の部品がある（ゴール地点を選べなくなる）");
  if (!names.includes(goal.at)) errs.push("ゴール地点の部品が見つからない");
  for (const p of goal.parts) {
    if (!p.conds.length) { errs.push(`「${p.name}」に条件が無い`); continue; }
    for (const c of p.conds) {
      if (c.raw) continue;
      const kind = (CONDS[c.t] || ["", "num"])[1];
      if ((kind === "card" || kind === "cards") && !String(c.v).trim()) errs.push(`「${p.name}」でカード名がまだ`);
      if (kind === "card" && String(c.v).trim() && !BYN[String(c.v).trim()]
          && !C.some((x) => x.n.includes(String(c.v).trim()))) errs.push(`「${c.v}」というカードは無い`);
    }
  }
  $("gerr").textContent = errs.length ? errs.join("／") : "";
  $("gjson").textContent = JSON.stringify(goalJson(), null, 2);
}
/* ---------------- ゴールを文章で書く ----------------
   読むのはPython（goaltext.py）。画面では読まない。
   同じ文を入れれば必ず同じ条件が出るようにしたいので、読み方を2か所に書かない。
   ウェブ版は裏方（worker）、serve.py 版はサーバーに頼む。
   どちらも無い（deckui.html をそのまま開いた）ときは、その旨を出す。 */
let gseq = 0, gtimer = null, gparsed = null;

function goalTextAvailable() { return WEB || SV; }

function askParse(text) {
  const seq = ++gseq;
  const keys = Object.keys(deck || {});     // 組んでいるデッキのカードを先に探すため
  if (WEB) { getWorker().postMessage({ t: "parsegoal", text, deck: keys, seq }); return; }
  if (SV) {
    api("/api/parse-goal", { text, deck: keys }).then((r) => showRead(r, seq))
      .catch((e) => { $("gread").innerHTML = `<span class="ng">読めませんでした：${esc(e.message)}</span>`; });
  }
}

function showRead(r, seq) {
  if (seq && seq !== gseq) return;            // 古い返事は捨てる（打っている途中の分）
  gparsed = r && r.goal ? r.goal : null;
  const notes = (r && r.notes) || [];
  if (!notes.length) { $("gread").innerHTML = ""; return; }
  $("gread").innerHTML = `<div class="eyebrow">こう読みました</div>` + notes.map((n) => {
    let body = n.ok ? `<span class="say">${esc(n.read)}</span>`
                    : `<span class="ng">読み取れませんでした</span>`;
    (n.miss || []).forEach((m) => {
      body += m.cands && m.cands.length
        ? `<div class="warn">「${esc(m.word)}」はどれか決められません：${esc(m.cands.slice(0, 4).join("・"))}</div>`
        : `<div class="warn">「${esc(m.word)}」に当たるカードが見つかりません</div>`;
    });
    if (n.ok && n.hint) body += `<div class="dim">${esc(n.hint)}</div>`;
    return `<div class="ln"><span class="${n.ok ? "ok" : "ng"}">${n.ok ? "○" : "×"}</span>
      <div><div class="dim">${esc(n.line)}</div>${body}</div></div>`;
  }).join("");
}

$("gtext").addEventListener("input", () => {
  const t = $("gtext").value;
  if (!t.trim()) { $("gread").innerHTML = ""; gparsed = null; return; }
  if (!goalTextAvailable()) {
    $("gread").innerHTML = `<span class="dim">この画面だけでは文章を読めません。
      ウェブ版か <code>python serve.py</code> で開くと、打つそばから読み返しが出ます。
      いまは <code>python goaltext.py "${esc(t.split("\n")[0])}"</code> で確かめられます。</span>`;
    return;
  }
  clearTimeout(gtimer);
  gtimer = setTimeout(() => askParse(t), 400);
});

$("gtextgo").addEventListener("click", () => {
  if (!gparsed || !(gparsed.parts || []).length) {
    $("gread").innerHTML = `<span class="ng">まだ読めた行がありません</span>` + $("gread").innerHTML;
    return;
  }
  const keepName = $("gname").value.trim();
  const keepDecks = $("gdecks").value.trim();
  goal = goalFrom(gparsed);
  goal.auto = false;                 // 自分で書いたゴールは、デッキを変えても上書きしない
  if (keepName) goal.name = keepName;
  if (keepDecks) goal.decks = keepDecks.split(/[、,]/).map((x) => x.trim()).filter(Boolean);
  drawGoal();
  $("gfine").open = true;
});

$("gtextback").addEventListener("click", () => {
  const g = goalJson().goals[0];
  if (WEB) { getWorker().postMessage({ t: "goaltotext", goal: g }); return; }
  if (SV) {
    api("/api/goal-text", { goal: g }).then((r) => { $("gtext").value = r.text || ""; askParse($("gtext").value); })
      .catch(() => {});
    return;
  }
  $("gread").innerHTML = `<span class="dim">ウェブ版か serve.py で開くと使えます</span>`;
});

$("addpart").addEventListener("click", () => {
  goal.auto = false;
  goal.parts.push({ name: `部品${goal.parts.length + 1}`, conds: [{ t: "win", v: true, n: 1 }] });
  drawGoal();
});
$("gclear").addEventListener("click", () => {
  goal = blankGoal($("dname").value); goal.auto = false; drawGoal();
});
$("gordered").addEventListener("change", () => { goal.ordered = $("gordered").checked; drawJson(); });
$("gbase").addEventListener("change", () => {
  const i = $("gbase").value; if (i === "") return;
  goal = goalFrom(DATA.goals[+i]); goal.auto = false; drawGoal();
});
for (const id of ["gname", "glabel", "gdecks"]) $(id).addEventListener("input", () => {
  goal.auto = false;                       // 自分で書いたゴールは、デッキを変えても残す
  goal.name = $("gname").value;
  goal.label = $("glabel").value;
  goal.decks = $("gdecks").value.split(/[、,]/).map((x) => x.trim()).filter(Boolean);
  drawJson();
});
$("gcopy").addEventListener("click", async () => {
  const t = $("gjson").textContent;
  try { await navigator.clipboard.writeText(t); $("gerr").textContent = "コピーしました"; }
  catch (e) {
    const r = document.createRange(); r.selectNodeContents($("gjson"));
    const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
    $("gerr").textContent = "コピーできませんでした。選択したので Ctrl+C で。";
  }
});

/* ================================================================ 名乗りと注記（ふもと）
   公開して人に使ってもらうなら、「非公式である」と権利者をはっきり書くのが決まり。
   中身は site.json で変える（コードは触らない）。 */
const SITE = DATA.site || {};
function drawFoot() {
  if (SITE.name) { document.title = SITE.name; $("sitename").textContent = SITE.name; }
  const L = [];
  if (SITE.source_url) L.push(`<a href="${esc(SITE.source_url)}" target="_blank" rel="noopener">ソース</a>`);
  if (SITE.author) {
    L.push(SITE.author_url
      ? `<a href="${esc(SITE.author_url)}" target="_blank" rel="noopener">作者：${esc(SITE.author)}</a>`
      : `作者：${esc(SITE.author)}`);
  }
  for (const sp of (SITE.support || [])) {
    if (sp && sp.url) L.push(`<a href="${esc(sp.url)}" target="_blank" rel="noopener">${esc(sp.label || "支援")}</a>`);
  }
  $("foot").innerHTML =
    (SITE.unofficial ? `<p class="unof">${esc(SITE.unofficial)}</p>` : "")
    + (SITE.support && SITE.support.length
       ? `<p style="margin:0">このツールは無料です。続けられるよう支えてくれる方は下のリンクから。</p>` : "")
    + (L.length ? `<p class="links">${L.join("")}</p>` : "")
    + (SITE.ad_html ? `<div class="ad">${SITE.ad_html}</div>` : "");
}
/* カードの外部リンク（調べる・買う）。{name} がカード名に置き換わる */
function extLinks(c) {
  const mk = (a) => (a || []).filter((x) => x && x.url).map((x) =>
    `<a href="${esc(encodeURI(x.url.replace("{name}", c.n)))}" target="_blank" rel="noopener">${esc(x.label || "リンク")}</a>`);
  const l = mk(SITE.card_links).concat(mk(SITE.shops));
  return l.length ? `<div class="ext">${l.join("")}</div>` : "";
}

/* ================================================================ タブ（スマホ）
   狭い画面では4つの画面を切り替える。広い画面では全部そのまま出す（タブは隠れる）。 */
function tab(name) {
  for (const el of document.querySelectorAll(".pane")) el.classList.toggle("on", el.dataset.tab === name);
  for (const el of $("tabs").querySelectorAll("button")) el.classList.toggle("on", el.dataset.go === name);
  scrollTo({ top: 0, behavior: "instant" });
  try { localStorage.setItem("dmtab", name); } catch (e) { }
}
$("tabs").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) tab(b.dataset.go); });
try { const t = localStorage.getItem("dmtab"); if (t) tab(t); } catch (e) { }

/* ================================================================ 回す（PCのサーバーに頼む）
   このページがPCの serve.py から配られている時だけ使える。
   ファイルを直接開いた時は、やり方だけを出す。 */
const SV = (typeof window.__SERVER__ === "object" && window.__SERVER__) || null;
const WEB = (typeof window.__WEB__ === "object" && window.__WEB__) || null;
const api = (path, body) => fetch(path + (path.includes("?") ? "&" : "?") + "k=" + encodeURIComponent(SV.token),
  body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
       : {}).then(async (r) => { const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status); return j; });

/* ウェブ版：サーバーを置かず、**見ている端末のブラウザの中でPythonを走らせる**。
   重い計算は worker.js（別スレッド）に任せるので、回している間も画面は動く。 */
let worker = null, webReady = false;
function getWorker() {
  if (worker) return worker;
  worker = new Worker("worker.js");
  worker.onmessage = (e) => {
    const m = e.data || {};
    if (m.t === "status") { $("runmsg").textContent = m.msg; }
    else if (m.t === "ready") { webReady = true; $("run").disabled = false; }
    else if (m.t === "prog") {
      if (m.total) $("prog").style.width = (m.done / m.total * 100) + "%";
      $("runmsg").textContent = `回しています… ${m.done}/${m.total}戦`;
    } else if (m.t === "done") {
      $("run").disabled = false; $("progwrap").hidden = true; $("runmsg").textContent = "";
      showResult(m.result);
    } else if (m.t === "goalparsed") {
      showRead(m.result, m.seq);
    } else if (m.t === "goaltext") {
      $("gtext").value = m.text || "";
      if (m.text) askParse(m.text);
    } else if (m.t === "error") {
      $("run").disabled = false; $("progwrap").hidden = true;
      $("runmsg").innerHTML = `<span style="color:var(--accent)">できませんでした：${esc(m.msg)}</span>`;
    }
  };
  worker.onerror = (e) => {
    $("run").disabled = false; $("progwrap").hidden = true;
    $("runmsg").innerHTML = `<span style="color:var(--accent)">裏方を起こせませんでした：${esc(e.message || "")}
      （index.html をファイルとして直接開いていませんか。http:// で配る必要があります）</span>`;
  };
  return worker;
}

function setRunMode() {
  if (SV) {
    $("svstate").innerHTML = `このページは<b>このPCのサーバー</b>から配られている。「回す」で一人回しを始められる。`;
    $("runhead").textContent = "このPCで一人回しを始める";
    $("runintro").textContent = "計算はPCがする。回している間この画面を閉じてもよい（戻ってくれば続きが見える）。";
  } else if (WEB) {
    $("svstate").innerHTML = `計算は<b>この端末のブラウザの中</b>で走る（サーバーは無い）。`;
    $("runhead").textContent = "この端末のブラウザの中で一人回しを始める";
    $("runintro").innerHTML = "はじめて「回す」を押した時だけ、Python本体の読み込みに十数秒かかる"
      + "（2回目からはすぐ始まる）。PCで直接動かすより2〜4倍遅いので、"
      + "まずは300戦で様子を見るとよい。<b>デッキとゴールはこの端末の中に覚えておく</b>"
      + "（PCには保存できないので、持ち出すときは「書き出し」のテキストを使う）。";
    $("savedeck").hidden = $("savegoal").hidden = $("loaddeck").hidden = true;
    getWorker().postMessage({ t: "boot" });        // 先に起こしておく（押した時に待たせない）
  } else {
    $("svstate").textContent = "";
    $("runhead").textContent = "一人回しを始めるには";
    $("run").disabled = true;
    $("savedeck").disabled = $("savegoal").disabled = $("loaddeck").disabled = true;
    $("runintro").innerHTML = "いまはファイルを直接開いている（計算するところにつながっていない）。"
      + "回すには次のどちらか。<br>"
      + "・PCで <code>python serve.py</code>：同じWi-Fiのスマホから。計算はPCがする（速い）<br>"
      + "・<code>python webbuild.py</code> で作った <code>web\</code> をどこかに置く："
      + "どこからでも。計算は見ている端末のブラウザの中（サーバー不要）<br>"
      + "いまのままでも、デッキとゴールを組んで「書き出し」で持ち出せる。";
  }
}
function fillAt() {
  const sel = $("rat"); const cur = sel.value;
  const names = (goal && goal.parts) ? goal.parts.map((p) => p.name) : [];
  sel.innerHTML = `<option value="">ゴールを測らない</option>`
    + names.map((n) => `<option value="${esc(n)}"${n === goal.at ? " selected" : ""}>${esc(n)}</option>`).join("");
  if (cur && names.includes(cur)) sel.value = cur;
  else if (names.length) sel.value = goal.at;
}
function pct(x) { return (x * 100).toFixed(1) + "%"; }
function gauge(x, w) { return `<span class="gauge" style="width:${Math.max(0, Math.min(1, x)) * (w || 60)}px"></span>`; }

function showResult(d) {
  const k = d.kill || {}, g = d.goal;
  let h = `<h2 style="margin-top:14px">結果　${esc(d.name)}　${d.games}戦　${esc(d.first_label)}　${esc(d.vs)}</h2>`;
  if (g && g.n) {
    h += `<p class="note" style="margin:0">ゴール「${esc(g.name)}」${g.at ? "／地点 " + esc(g.at) : ""}</p>
      <p><span class="big" style="color:var(--ok)">${pct(g.rate)}</span>
         <span class="note">が到達　中央値 ${g.median}ターン　平均 ${g.mean.toFixed(2)}　最速 ${g.fastest}</span></p>`;
    if (g.parts && g.parts.length > 1) {
      h += `<div class="tw"><table><tr><th>部品</th><th>そろう</th><th>順に</th><th>平均T</th><th>ここで止まった</th></tr>`
        + g.parts.map((q) => `<tr><td>${esc(q.name)}${q.name === g.at ? " ◀" : ""}</td>
            <td>${pct(q.rate)}</td><td>${pct(q.ord_rate)} ${gauge(q.ord_rate, 40)}</td>
            <td>${q.mean ? q.mean.toFixed(2) : "－"}</td><td>${pct(q.stopped_here)}</td></tr>`).join("")
        + `</table></div>`;
      const worst = g.parts.reduce((a, b) => (b.stopped_here > a.stopped_here ? b : a));
      if (worst.stopped_here > 0.05) h += `<p class="note">いちばんの関門は「${esc(worst.name)}」。</p>`;
      const sk = g.parts.filter((q) => q.skipped >= 0.01);
      if (sk.length) h += `<p class="note">「そろう」より「順に」が低い部品がある＝前の部品を飛ばして成立している。
        部品の並びが実際の道筋と合っていないかもしれない。</p>`;
    }
  } else if (g) {
    h += `<p class="note">ゴール「${esc(g.name)}」には1戦も届かなかった。</p>`;
  }
  if (k.n) {
    h += `<p><span class="big">${k.mean.toFixed(2)}</span><span class="note">ターンで殴り切る（中央値 ${k.median}／
      ${pct(k.n / d.games)}が決着／最速 ${k.fastest}）</span></p>
      <div class="tw"><table><tr><th>ターン</th>`
      + [3, 4, 5, 6, 7, 8, 10].map((t) => `<th>${t}T</th>`).join("") + `</tr><tr><td>までに決まる</td>`
      + [3, 4, 5, 6, 7, 8, 10].map((t) => `<td>${pct((k.by_turn || {})[t] || 0)}</td>`).join("")
      + `</tr></table></div>`;
  } else {
    h += `<p class="note">1戦も殴り切れなかった。</p>`;
  }
  const bf = d.by_first || {};
  if (Object.keys(bf).length > 1) {
    h += `<div class="tw"><table><tr><th></th><th>戦数</th><th>勝率</th><th>殴り切り平均</th><th>3T事故</th></tr>`
      + Object.entries(bf).map(([lab, v]) => `<tr><td>${lab}</td><td>${v.games}</td>
          <td>${pct(v.win_rate)}</td><td>${v.kill_mean ? v.kill_mean.toFixed(2) + "T" : "－"}</td>
          <td>${pct(v.stuck3)}</td></tr>`).join("") + `</table></div>`;
  }
  h += `<p class="note">初手：3コスト以下が平均 ${d.opening.avg_castable_t3.toFixed(2)}枚／
    2コスト以下が無い初手 ${pct(d.opening.no_1or2)}　事故：3ターン目まで何も出せない ${pct(d.stuck3)}</p>`;
  const rows = Object.values(d.cards).sort((a, b) => b.use_rate - a.use_rate || a.cost - b.cost);
  h += `<details><summary>札ごとの働き（${rows.length}種類）</summary><div class="tw"><table>
    <tr><th>カード</th><th>枚</th><th>コスト</th><th>使えた</th><th>平均T</th><th>腐り</th><th>マナ行き</th></tr>`
    + rows.map((c) => `<tr><td>${esc(c.name)}</td><td>${c.copies}</td><td>${c.cost}</td>
        <td>${pct(c.use_rate)}</td><td>${c.avg_turn ? c.avg_turn.toFixed(1) : "－"}</td>
        <td>${pct(c.idle_rate)}</td><td>${pct(c.mana_rate)}</td></tr>`).join("")
    + `</table></div></details>`;
  if (d.unused && d.unused.length) {
    h += `<p class="note">ほとんど使われない札：${d.unused.map(esc).join("、")}
      （相手の妨害と関係なく腐っている＝抜く候補）</p>`;
  }
  h += `<p class="note">${d.secs.toFixed(1)}秒／1戦 ${d.ms_per_game.toFixed(1)}ミリ秒</p>`;
  $("res").innerHTML = h;
}

let polling = null;
async function poll(id) {
  try {
    const j = await api("/api/job?id=" + encodeURIComponent(id));
    if (j.total) $("prog").style.width = (j.done / j.total * 100) + "%";
    $("runmsg").textContent = j.state === "running"
      ? `回しています… ${j.done}/${j.total || "?"}戦` : "";
    if (j.state === "done") {
      clearInterval(polling); polling = null;
      $("run").disabled = false; $("progwrap").hidden = true;
      showResult(j.result);
    } else if (j.state === "error") {
      clearInterval(polling); polling = null;
      $("run").disabled = false; $("progwrap").hidden = true;
      $("runmsg").innerHTML = `<span style="color:var(--accent)">できませんでした：${esc(j.error)}</span>`;
    }
  } catch (e) {
    clearInterval(polling); polling = null;
    $("run").disabled = false;
    $("runmsg").innerHTML = `<span style="color:var(--accent)">PCにつながりません：${esc(e.message)}</span>`;
  }
}
$("run").addEventListener("click", async () => {
  if (!SV && !WEB) return;
  if (!Object.keys(deck).length) { $("runmsg").textContent = "デッキが空です。"; return; }
  const at = $("rat").value;
  const body = {
    deck: Object.fromEntries(Object.entries(deck).map(([k, n]) => [BYK[k].n, n])),
    name: $("dname").value || "名前のないデッキ",
    games: +$("rgames").value, pilot: $("rpilot").value, first: $("rfirst").value,
    wall: $("rwall").value, wall_shields: +$("rshields").value,
    goal: at ? goalJson().goals[0] : null, goal_at: at || null,
  };
  $("run").disabled = true; $("res").innerHTML = "";
  $("progwrap").hidden = false; $("prog").style.width = "0";
  if (WEB) {
    $("runmsg").textContent = webReady ? "回しています…" : "Python を起こしています…";
    getWorker().postMessage({ t: "run", req: body });
    return;
  }
  $("runmsg").textContent = "送っています…";
  try {
    const j = await api("/api/run", body);
    polling = setInterval(() => poll(j.job), 400);
  } catch (e) {
    $("run").disabled = false; $("progwrap").hidden = true;
    $("runmsg").innerHTML = `<span style="color:var(--accent)">${esc(e.message)}</span>`;
  }
});
$("savedeck").addEventListener("click", async () => {
  try {
    const r = await api("/api/save-deck", { name: $("dname").value || "deck", text: toText() });
    $("runmsg").textContent = `decks\\${r.path} に保存しました`;
  } catch (e) { $("runmsg").textContent = "保存できませんでした：" + e.message; }
});
$("savegoal").addEventListener("click", async () => {
  try {
    const r = await api("/api/save-goals", goalJson());
    $("runmsg").textContent = `${r.path} に保存しました（次からこのゴールが自動で当たります）`;
  } catch (e) { $("runmsg").textContent = "保存できませんでした：" + e.message; }
});
$("loaddeck").addEventListener("click", async () => {
  try {
    const r = await api("/api/saved");
    if (!r.decks.length) { $("runmsg").textContent = "保存したデッキはまだありません。"; return; }
    const names = r.decks.map((d, i) => `${i + 1}. ${d.name}`).join("\n");
    const pick = r.decks.length === 1 ? 1 : null;
    if (pick === null) {
      $("runmsg").innerHTML = "どれを開きますか：<br>" + r.decks.map((d, i) =>
        `<button data-open="${i}">${esc(d.name)}</button>`).join(" ");
      for (const el of $("runmsg").querySelectorAll("[data-open]")) el.addEventListener("click", () => {
        const d = r.decks[+el.dataset.open];
        $("dname").value = d.name; doImport(d.text);
        $("runmsg").textContent = `${d.name} を開きました（${total()}枚）`;
      });
      return;
    }
    $("dname").value = r.decks[0].name; doImport(r.decks[0].text);
    $("runmsg").textContent = `${r.decks[0].name} を開きました（${total()}枚）`;
  } catch (e) { $("runmsg").textContent = "読めませんでした：" + e.message; }
});

/* ================================================================ 共有リンク
   デッキとゴールをURLの中に入れて、そのまま相手に渡せるようにする。
   サーバーに何も置かないので、**渡した相手の端末だけで開いて、そのまま回せる**。
   （Claude の Artifact では URL の # に値を入れられないため、この機能は出さない） */
function b64u(str) {                       // UTF-8 → URLに入れられる文字
  const b = new TextEncoder().encode(str);
  let s = ""; for (const x of b) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function unb64u(t) {
  const s = atob(t.replace(/-/g, "+").replace(/_/g, "/"));
  const b = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) b[i] = s.charCodeAt(i);
  return new TextDecoder().decode(b);
}
function sharePayload() {
  const o = { n: $("dname").value || "", d: deck };
  if (goal && goal.parts && goal.parts.length) o.g = goalJson().goals[0];
  return o;
}
function shareURL() {
  const base = location.origin + location.pathname + location.search;
  return base + "#d=" + b64u(JSON.stringify(sharePayload()));
}
function readShare() {
  const m = (location.hash || "").match(/^#d=(.+)$/);
  if (!m) return false;
  try {
    const o = JSON.parse(unb64u(m[1]));
    const d = {};
    for (const [k, n] of Object.entries(o.d || {})) if (BYK[k]) d[k] = n;
    if (!Object.keys(d).length) return false;
    deck = d;
    $("dname").value = o.n || "";
    if (o.g && o.g.parts) goal = goalFrom(o.g);
    return true;
  } catch (e) { return false; }
}
if (SV || WEB) {
  $("share").hidden = false;
  $("share").addEventListener("click", async () => {
    const u = shareURL();
    $("sharemsg").hidden = false;
    if (u.length > 7000) {
      $("sharemsg").textContent = "リンクが長くなりすぎました（ゴールを短くするか、書き出しのテキストで渡してください）";
      return;
    }
    let copied = false;
    try { await navigator.clipboard.writeText(u); copied = true; } catch (e) { }
    $("sharemsg").innerHTML = (copied ? "コピーしました。" : "")
      + "このリンクを開くと、このデッキとゴールがそのまま入った状態で始まります。"
      + `<br><input type="text" readonly value="${esc(u)}" style="width:100%;margin-top:4px">`
      + (SV ? "<br>※ いまのリンクは同じWi-Fiの中だけで開けます（家の外に渡すならウェブ版を置いてください）。" : "");
    const f = $("sharemsg").querySelector("input");
    if (f) { f.addEventListener("click", () => f.select()); if (!copied) f.select(); }
  });
}

/* ---- 作りかけを覚えておく（この画面を開いた人のブラウザの中だけ） ---- */
function save() {
  try { localStorage.setItem("dmdeck", JSON.stringify({ d: deck, n: $("dname").value, g: goal })); } catch (e) { }
}
const fromLink = readShare();      // 共有リンクで開かれたなら、それが最優先
if (!fromLink) {
  try {
    const s = JSON.parse(localStorage.getItem("dmdeck") || "null");
    if (s && s.d) { deck = s.d; $("dname").value = s.n || ""; }
    if (s && s.g && s.g.parts) goal = s.g;
  } catch (e) { }
}
if (!Object.keys(deck).length) {       // はじめて開いた時は、お手本を1つ入れておく（空の画面では何も分からない）
  const first = samples.find((n) => n.includes("赤零")) || samples[0];
  $("sample").value = first; $("dname").value = first;
  for (const [nm, n] of Object.entries(DATA.decks[first] || {})) { const c = BYN[nm]; if (c) deck[c.k] = n; }
}
if (!goal) {           // はじめて開いた時は、そのデッキ名が当たる見本のゴールを写しておく
  const nm = $("dname").value || "";
  const hit = (DATA.goals || []).find((g) => (g.decks || []).some((d) => d && nm.includes(d)));
  goal = hit ? goalFrom(hit) : blankGoal(nm);
  if (!hit) goal.decks = nm ? [nm] : [];
}
drawFoot();
setRunMode();
drawGoal();
update();
</script>
"""


def main():
    ap = argparse.ArgumentParser(description="デッキを作る画面（HTML）を作る")
    ap.add_argument("--out", help="書き出し先（既定：deckui.html、--bare なら deckui_artifact.html）")
    ap.add_argument("--cards", help="カードのデータだけJSONで書き出す")
    ap.add_argument("--open", action="store_true", help="作ってそのままブラウザで開く")
    ap.add_argument("--bare", action="store_true",
                    help="外側のHTML（doctype・viewport）を付けない。Artifact などに置く用")
    a = ap.parse_args()
    # --bare を --out なしで動かすと、以前は普通の deckui.html を上書きして
    # 外側のHTML（doctype・viewport）が消えたファイルができてしまった。既定の名前を分ける。
    if not a.out:
        a.out = os.path.join(HERE, "deckui_artifact.html" if a.bare else "deckui.html")
    d = card_data()
    if a.cards:
        json.dump(d, open(a.cards, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"カードのデータ：{a.cards}（{len(d['cards'])}枚）")
        if not a.out:
            return
    p, n, nc = build(a.out, d, not a.bare)
    print(f"できました：{p}")
    print(f"  カード {nc}枚／お手本のデッキ {len(d['decks'])}個／{n / 1024:.0f}KB の1枚のHTML")
    print("  ブラウザで開いて、クリックで40枚を組んでください。")
    print("  組んだら「書き出し」→ mydeck.txt に保存 →")
    print("    python solo.py --deck-file mydeck.txt --games 3000 --pilot plan")
    print("  スマホから使うなら： python serve.py")
    if a.open:
        webbrowser.open("file://" + os.path.abspath(p))


if __name__ == "__main__":
    main()
