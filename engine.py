"""窓理論のゲームエンジン

基本ルール：40枚、シールド5枚、初期手札5枚、先攻1ターン目はドローなし、毎ターン1枚マナチャージ。
判断ロジックはデッキに依存しない汎用のもの（デッキの経路と、相手の経路を知っている前提）。
"""
import random
from dataclasses import dataclass, field

from cards import BY_KEY, CHAIN_NEED, LOOP_MANA, LOOP_SPELLS, deck_paths, deck_defense


@dataclass(eq=False)
class Unit:
    card: object
    tapped: bool = False
    sick: bool = True
    entered: int = 0


class Player:
    def __init__(self, name, counts, aggr, rng):
        self.name = name
        self.counts = counts
        self.aggr = aggr
        self.deck = [BY_KEY[k] for k, n in counts.items() for _ in range(n)]
        rng.shuffle(self.deck)
        self.shields = [self.deck.pop() for _ in range(5)]
        self.hand = [self.deck.pop() for _ in range(5)]
        self.mana = 0
        self.board = []
        self.spells = 0      # このターンに唱えた呪文の数
        self.summons = 0     # このターンに出したクリーチャーの数
        self.paths = deck_paths(counts)
        self.defense = deck_defense(counts)

    def closes(self, kind):
        return any(kind in u.card.closes for u in self.board)


KEEP = {"ramp": 3, "draw": 2, "b1": 2, "b2": 4, "b3": 5, "sa2": 6, "sa3": 6, "swap": 8,
        "m_trig": 6, "m_free": 6, "m_spell": 6, "m_attack": 6, "m_summon": 6, "m_free_p": 7, "m_spell_p": 7,
        "removal": 6, "wipe": 5, "handes_c": 4, "handes_s": 4,
        "t_stop": 3, "t_tap": 3, "t_remove": 4, "t_wipe": 4, "t_block": 3, "t_big": 5,
        "counter0": 8, "blocker": 3, "shield": 3}


class Game:
    def __init__(self, deck_a, deck_b, rng, first=0, max_rounds=25):
        self.rng = rng
        self.p = [Player("A", deck_a[0], deck_a[1], rng), Player("B", deck_b[0], deck_b[1], rng)]
        self.first = first
        self.max_rounds = max_rounds
        self.winner = None
        self.win_path = None
        self.round = 0
        self.turn_ended = False

    # ---------- 共通 ----------
    def keep_score(self, me, c):
        if c.role == "chain":
            return 7 if "CHAIN" in me.paths else 1
        if c.role == "chain_fin":
            return 9 if "CHAIN" in me.paths else 1
        if c.role == "loop_spell":
            return 10 if "LOOP" in me.paths else 0
        if c.role == "loop_engine":
            return 9 if "LOOP" in me.paths else 1
        return KEEP.get(c.key, 3)

    def can_summon(self, me, opp):
        return not (opp.closes("C_SUMMON") and me.summons >= 2)

    def can_cast_spell(self, me, opp):
        return not (opp.closes("C_SPELL") and me.spells >= 1)

    def enter(self, me, card, tapped=False, sick=True):
        u = Unit(card, tapped=tapped, sick=sick, entered=self.round)
        me.board.append(u)
        me.summons += 1
        return u

    def threat(self, chooser, owner, u):
        """chooser から見た、owner の場の u の危険度（除去の優先度）"""
        s = u.card.breaks * 10
        for k in u.card.closes:
            if (k == "C_TRIG") or (k == "C_FREE" and chooser.paths & {"SWAP", "CHAIN"}) or \
               (k == "C_SPELL" and "LOOP" in chooser.paths) or (k == "C_SUMMON" and "CHAIN" in chooser.paths) or \
               (k == "C_ATTACK"):
                s += 60
            else:
                s += 15
        if u.card.role == "loop_engine":
            s += 70
        if u.card.role in ("chain", "chain_fin") and "CHAIN" in owner.paths:
            s += 35
        return s

    def destroy(self, chooser, owner, n, prefer_untapped=False):
        for _ in range(n):
            cand = [u for u in owner.board if not u.card.protect]
            if not cand:
                return
            cand.sort(key=lambda u: ((not u.tapped) if prefer_untapped else 0, self.threat(chooser, owner, u)),
                      reverse=True)
            owner.board.remove(cand[0])

    def draw(self, me, n=1):
        for _ in range(n):
            if not me.deck:
                return False
            me.hand.append(me.deck.pop())
        return True

    # ---------- 自分のターン ----------
    def chain_count(self, me):
        return sum(1 for u in me.board if u.card.role in ("chain", "chain_fin"))

    def priority(self, me, opp, c):
        k = c.key
        if c.role == "loop_spell" or c.role == "counter0" or c.trig in ("stop", "tap"):
            return None
        if c.role == "swap" and "SWAP" in me.paths and any(u.card.breaks for u in me.board):
            return None   # 入れ替え用に手札に残す
        if c.key == "ramp":
            return 100 if me.mana <= 4 else 5
        if c.closes:
            kind = c.closes[0]
            if me.closes(kind):
                return 25
            relevant = {
                "C_TRIG": opp.defense["triggers"] >= 4,
                "C_FREE": bool(opp.paths & {"SWAP", "CHAIN"}) or opp.defense["counter0"] >= 2,
                "C_SPELL": "LOOP" in opp.paths or opp.defense["triggers"] >= 6,
                "C_ATTACK": bool(opp.paths & {"CHAIN"}) or opp.counts.get("sa2", 0) + opp.counts.get("sa3", 0) >= 4,
                "C_SUMMON": "CHAIN" in opp.paths,
            }[kind]
            return 90 if relevant else 30
        if c.role == "loop_engine":
            return 88 if "LOOP" in me.paths else 20
        if c.role == "chain":
            return 80 if "CHAIN" in me.paths else 25
        if c.role == "chain_fin":
            return 97 if self.chain_count(me) + 1 >= CHAIN_NEED else 35
        if c.removal and c.kind == "spell":
            if not any(not u.card.protect for u in opp.board):
                return None
            best = max(self.threat(me, opp, u) for u in opp.board if not u.card.protect)
            if c.removal >= 2:
                return 75 if sum(1 for u in opp.board if not u.card.protect) >= 3 else None
            return 85 if best >= 60 else (55 if best >= 20 else None)
        if c.handes:
            if not opp.hand:
                return None if c.kind == "spell" else 30
            return 70
        if c.draw and c.kind == "spell" and not c.shield_add:
            return 45
        if c.shield_add:
            return 40
        if c.kind == "creature":
            return 40 + c.cost * 5
        return None

    def main_phase(self, me, opp):
        # マナチャージ
        if me.hand:
            ch = min(me.hand, key=lambda c: (self.keep_score(me, c), self.rng.random()))
            me.hand.remove(ch)
            me.mana += 1
        avail = me.mana
        # 呪文ループの勝ち
        if "LOOP" in me.paths and any(u.card.role == "loop_engine" for u in me.board) and \
                any(c.role == "loop_spell" for c in me.hand) and avail >= LOOP_MANA and \
                not opp.closes("C_SPELL"):
            self.winner, self.win_path = me, "LOOP"
            return
        while avail > 0 and not self.winner:
            opts = []
            for c in me.hand:
                if c.cost > avail:
                    continue
                if c.kind == "spell" and not self.can_cast_spell(me, opp):
                    continue
                if c.kind == "creature" and not self.can_summon(me, opp):
                    continue
                pr = self.priority(me, opp, c)
                if pr is not None:
                    opts.append((pr, c.cost, self.rng.random(), c))
            if not opts:
                break
            opts.sort(key=lambda x: x[:3], reverse=True)
            c = opts[0][3]
            me.hand.remove(c)
            avail -= c.cost
            self.resolve(me, opp, c)

    def resolve(self, me, opp, c):
        if c.kind == "spell":
            me.spells += 1
        else:
            self.enter(me, c)
            if c.role == "chain" and not opp.closes("C_FREE"):
                # 連鎖：手札の連鎖カードをタダで出す（何度でも）
                while self.can_summon(me, opp):
                    nxt = next((x for x in me.hand if x.role in ("chain", "chain_fin")), None)
                    if not nxt:
                        break
                    me.hand.remove(nxt)
                    self.enter(me, nxt)
        if c.ramp and me.deck:
            me.deck.pop()
            me.mana += c.ramp
        if c.draw:
            self.draw(me, c.draw)
        if c.handes:
            for _ in range(c.handes):
                if opp.hand:
                    opp.hand.remove(self.rng.choice(opp.hand))
        if c.removal:
            self.destroy(me, opp, c.removal)
        if c.shield_add:
            for _ in range(c.shield_add):
                if me.deck:
                    me.shields.append(me.deck.pop())

    # ---------- 攻撃 ----------
    def can_attack(self, me, opp, u):
        if u.tapped or u.card.breaks == 0:
            return False
        if u.entered == self.round:
            if opp.closes("C_ATTACK"):
                return False
            return u.card.sa or not u.sick
        return True

    def lethal_possible(self, me, opp, ready):
        breaks = sorted((u.card.breaks for u in ready), reverse=True)
        swap_ok = "SWAP" in me.paths and any(c.role == "swap" for c in me.hand) and not opp.closes("C_FREE")
        if swap_ok and breaks:
            breaks[-1] = max(breaks[-1], 3)
            breaks.sort(reverse=True)
        need, used = len(opp.shields), 0
        got = 0
        for b in breaks:
            if got >= need:
                break
            got += b
            used += 1
        return got >= need and len(breaks) - used >= 1

    def attack_phase(self, me, opp):
        ready = [u for u in me.board if self.can_attack(me, opp, u)]
        # 連鎖の特殊勝利
        fin = next((u for u in ready if u.card.role == "chain_fin"), None)
        if fin and self.chain_count(me) >= CHAIN_NEED:
            self.winner, self.win_path = me, "CHAIN"
            return
        if not ready:
            return
        if not (me.aggr or not opp.shields or self.lethal_possible(me, opp, ready)):
            return
        ready.sort(key=lambda u: u.card.breaks, reverse=True)
        for u in ready:
            if self.winner or self.turn_ended:
                return
            if u not in me.board or u.tapped:
                continue
            u.tapped = True
            attacker, swapped = u, False
            # 入れ替え
            sw = next((c for c in me.hand if c.role == "swap"), None)
            if sw and u.card.breaks < sw.breaks and not opp.closes("C_FREE") and self.can_summon(me, opp):
                me.hand.remove(sw)
                me.board.remove(u)
                me.hand.append(u.card)
                attacker = self.enter(me, sw, tapped=True)
                swapped = True
            # ブロック
            blk = next((b for b in opp.board if b.card.blocker and not b.tapped), None)
            if blk and (not opp.shields or attacker.card.breaks >= 2):
                blk.tapped = True
                continue
            if not opp.shields:
                cnt = next((c for c in opp.hand if c.role == "counter0"), None)
                if cnt and not me.closes("C_FREE") and self.can_summon(opp, me):
                    opp.hand.remove(cnt)
                    if attacker in me.board:
                        me.board.remove(attacker)
                    self.enter(opp, cnt, sick=False)
                    continue
                self.winner, self.win_path = me, ("SWAP" if swapped else "ATTACK")
                return
            for _ in range(min(attacker.card.breaks, len(opp.shields))):
                s = opp.shields.pop()
                self.shield_to(opp, me, s)
                if self.turn_ended:
                    return

    def shield_to(self, owner, attacker_pl, s):
        """割られたシールドの処理。トリガーが使えれば使い、使えなければ手札へ"""
        usable = bool(s.trig) and not attacker_pl.closes("C_TRIG")
        if usable and s.kind == "spell" and not self.can_cast_spell(owner, attacker_pl):
            usable = False
        if usable and s.kind == "creature" and (attacker_pl.closes("C_FREE") or not self.can_summon(owner, attacker_pl)):
            usable = False
        if not usable:
            owner.hand.append(s)
            return
        t = s.trig
        if s.kind == "spell":
            owner.spells += 1
        if t == "stop":
            self.turn_ended = True
        elif t == "tap":
            for u in attacker_pl.board:
                u.tapped = True
        elif t == "remove":
            self.destroy(owner, attacker_pl, 1, prefer_untapped=True)
        elif t == "wipe":
            self.destroy(owner, attacker_pl, 2, prefer_untapped=True)
        elif t in ("block", "big"):
            self.enter(owner, s, sick=False)

    # ---------- 進行 ----------
    def play(self):
        cur = self.first
        for turn in range(self.max_rounds * 2):
            me, opp = self.p[cur], self.p[1 - cur]
            self.round = turn // 2 + 1
            self.turn_ended = False
            me.spells = me.summons = opp.spells = opp.summons = 0
            for u in me.board:
                u.tapped = False
                u.sick = False
            if turn > 0 and not self.draw(me):
                self.winner, self.win_path = opp, "DECKOUT"
                break
            self.main_phase(me, opp)
            if self.winner:
                break
            if not self.turn_ended:
                self.attack_phase(me, opp)
            if self.winner:
                break
            cur = 1 - cur
        return self.winner.name if self.winner else None


def play_match(deck_a, deck_b, n, seed=0):
    """A の勝率（先攻後攻は半々、引き分けは0.5）と勝ち筋の内訳"""
    rng = random.Random(seed)
    w = 0.0
    paths = {}
    rounds = 0
    for i in range(n):
        g = Game(deck_a, deck_b, rng, first=i % 2)
        r = g.play()
        rounds += g.round
        if r == "A":
            w += 1
            paths[g.win_path] = paths.get(g.win_path, 0) + 1
        elif r is None:
            w += 0.5
    return w / n, paths, rounds / n
