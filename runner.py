#!/usr/bin/env python3
r"""一人回しを「要求（JSON）から回して、まとめを返す」ところだけにしたもの

  同じ計算を2か所から呼ぶ。
    serve.py  … PCをサーバーにして、同じWi-Fiのスマホから（計算はPC）
    webrun.py … ブラウザの中で動くPython（Pyodide）から（計算はその端末）
  どちらも通る道を1本にしておけば、「PCで出る数字とウェブで出る数字が違う」ことが起きない。

  prepare(要求)  要求を調べて、そのまま回せる形にする。おかしいところはここで止める
  run(用意したもの, 進み具合の知らせ)  実際に回して、まとめ（solo.summarize の形）を返す
"""
import os
import time

MAXGAMES = 20000
PROCS = [1]          # 1 より大きいと、そのコア数で分けて回す（ブラウザの中では 1 のまま）


def _resolve(deck_names):
    """{カード名: 枚数} を {キー: 枚数} に直す。知らない名前は分かる形で返す"""
    import decks8
    from cards3 import BY_KEY
    idx = decks8._index()
    out, miss = {}, []
    for nm, v in deck_names.items():
        k = decks8.find(str(nm), idx)
        if k is None:
            miss.append(str(nm))
        else:
            out[k] = out.get(k, 0) + int(v)
    if miss:
        raise ValueError("知らないカード：" + "、".join(miss[:8]))
    if not out:
        raise ValueError("デッキが空です")
    n = sum(out.values())
    if n > 60:
        raise ValueError(f"{n}枚は多すぎます")
    for k, v in out.items():
        if v > 4:
            raise ValueError(f"{BY_KEY[k].name} が{v}枚あります")
    return out


def prepare(req):
    """要求を調べて、そのまま回せる形にする。**要求を受け取ったその場で**呼ぶ。

    おかしいところ（知らないカード、5枚以上、書き方のおかしいゴール）は、
    計算を始める前にここで止めて、スマホにすぐ理由を返す。"""
    import goals
    import solo
    if not isinstance(req, dict):
        raise ValueError("要求の形がおかしい")
    o = {"deck": _resolve(req.get("deck") or {}),
         "name": (str(req.get("name") or "名前のないデッキ"))[:40]}
    o["games"] = max(10, min(MAXGAMES, int(req.get("games", 1000))))
    o["pilot"] = req.get("pilot") if req.get("pilot") in ("greedy", "plan", "random") else "plan"
    o["first"] = req.get("first") if req.get("first") in ("1st", "2nd", "both") else "both"
    o["wall"] = req.get("wall") if req.get("wall") in solo.WALLS else "blank"
    o["wsh"] = max(0, min(10, int(req.get("wall_shields", 5))))
    o["maxt"] = max(3, min(40, int(req.get("maxturn", solo.MAXT))))
    g = req.get("goal") or None
    o["goal"] = g if isinstance(g, dict) else None
    o["goal_at"] = req.get("goal_at") or None
    if o["goal"] is not None:
        for _nm, w in goals.parts_of(o["goal"]):       # 書き方がおかしければここで止まる
            goals._one(w)
        goals.goal_when(o["goal"], o["goal_at"])
    return o


def run(o, on_progress=None):
    """用意した要求（prepare の戻り）を実際に回して、まとめを返す。

    on_progress(done, total) があれば、ときどき呼んで進み具合を知らせる。
    PCのサーバー（serve.py）からも、ブラウザの中のPython（webrun.py）からも、同じここを通る。"""
    import goals
    import solo
    deck, name, games = o["deck"], o["name"], o["games"]
    pilot, first, wall, wsh, maxt = o["pilot"], o["first"], o["wall"], o["wsh"], o["maxt"]
    gspec, gat = o["goal"], o["goal_at"]
    gf = goals._one(goals.goal_when(gspec, gat)[0]) if (gspec and pilot == "plan") else None

    opp, _olab = solo.make_wall(wall, wsh)
    firsts = {"1st": [0], "2nd": [1], "both": [0, 1]}[first]
    jobs = [(deck, opp, 1 + i * 7919, pilot, None, name, maxt,
             firsts[i % len(firsts)], gspec, False, wsh, gat) for i in range(games)]
    t0 = time.time()
    rs = []
    procs = PROCS[0]
    if procs > 1 and games >= 200:
        from multiprocessing import Pool
        with Pool(procs) as pool:
            for r in pool.imap_unordered(solo.job, jobs, chunksize=max(1, games // (procs * 16))):
                rs.append(r)
                if on_progress and len(rs) % 25 == 0:
                    on_progress(len(rs), games)
    else:
        pilot_f = solo.make_pilot(pilot, None, name, gf)
        for a in jobs:
            rs.append(solo.one(a[0], a[1], a[2], pilot_f, solo.pilot_passive,
                               a[6], a[7], a[8], a[9], a[10], a[11]))
            if on_progress and len(rs) % 25 == 0:
                on_progress(len(rs), games)
    secs = time.time() - t0
    meta = {"pilot": pilot, "vs": f"壁（{wall}／盾{wsh}）", "secs": secs,
            "ms_per_game": secs / games * 1000, "seed": 1, "wall": wall, "wall_shields": wsh,
            "first_label": {"1st": "先攻のみ", "2nd": "後攻のみ", "both": "先攻後攻を半分ずつ"}[first]}
    if gspec:
        meta["goal_name"] = gspec.get("name", "")
        meta["goal_label"] = gspec.get("label", "")
        meta["goal_at"] = goals.goal_when(gspec, gat)[1]
        meta["goal_ordered"] = bool(gspec.get("ordered", True))
    out = solo.summarize(deck, name, rs, meta)
    out.pop("deck", None)                          # 画面では使わないので返さない（軽くする）
    if on_progress:
        on_progress(games, games)
    return out
