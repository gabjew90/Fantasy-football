"""Your scenario: price a game again under YOUR workload assumptions (DECISIONS #153).

The user's judgment enters as opportunity, not as yards or catches: how many
targets or carries a player gets, how much the team throws or runs, and his
efficiency. Everything else follows from the same simulation the board uses:
receptions and receiving yards share one target draw, the starting QB's
passing yards are his receivers' yards, and a fixed team total means what one
player gains his teammates lose.

    score_game.py ... --assume "Woody Marks: carries=14" --assume "HOU: pass=-3"

Grammar, one rule per --assume, keys comma-separated:

    PLAYER may carry his team to tell two same-named players apart:
    'Mike Williams (NYJ): targets=6'. Names match loosely ('woody marks',
    'DJ Moore' for 'D.J. Moore').

    PLAYER: targets=N    targets per game (teammates and the depth receivers
                         give up the difference in proportion; the team total
                         does not move)
    PLAYER: carries=N    carries per game, the effective number the
                         simulation gives him (teammates give up the
                         difference in proportion)
    PLAYER: catch=P      catch rate (68% or 0.68)
    PLAYER: ypt=N        yards per target
    PLAYER: ypc=N        yards per carry
    TEAM:   pass=+N      team targets per game, change (e.g. -3)
    TEAM:   rush=+N      team carries per game, change
    TEAM:   ypt=+P%      every receiver's yards per target, change in percent

Team rules apply first, then efficiency, then targets and carries (so
'targets=8' means 8 of the team's adjusted total). The probabilities that
come out are EXPERIMENTAL and conditional on the assumptions, which are
assumptions, not confidence intervals. No touchdown price is adjusted.
"""
from __future__ import annotations

import re

import numpy as np

import model as MODEL
from model import norm_name

PLAYER_KEYS = ("targets", "carries", "catch", "ypt", "ypc")
TEAM_KEYS = ("pass", "rush", "ypt")
N_SOLVE, SEED = 8000, 20261004
MAX_SHARE = 0.95

WORDS = {"targets": "targets per game", "carries": "carries per game", "catch": "catch rate",
         "ypt": "yards per target", "ypc": "yards per carry", "pass": "team targets per game",
         "rush": "team carries per game"}


def _number(v: str, key: str, raw: str) -> tuple[float, bool]:
    s = v.strip().replace(" ", "")
    pct = s.endswith("%")
    try:
        x = float(s.rstrip("%"))
    except ValueError:
        raise ValueError(f"'{raw}': {key}={v.strip()} is not a number") from None
    if not np.isfinite(x):
        raise ValueError(f"'{raw}': {key}={v.strip()} is not a number")
    return x, pct


def parse(rules, teams) -> list[dict]:
    """--assume strings -> rules. teams: this game's two abbreviations. Raises
    ValueError with a plain reason on anything it cannot read."""
    teams = {t.upper() for t in teams}
    out = []
    for raw in rules or []:
        who, sep, body = str(raw).partition(":")
        who = " ".join(who.split())
        if not sep or not who or not body.strip():
            raise ValueError(f"'{raw}': write it as 'PLAYER: key=value' or 'TEAM: key=value'")
        team_of = None
        m_ = re.fullmatch(r"(.+?)\s*\(([A-Za-z]{2,3})\)", who)
        if m_ and m_.group(2).upper() in teams:
            who, team_of = m_.group(1).strip(), m_.group(2).upper()
        is_team = who.upper() in teams and team_of is None
        allowed = TEAM_KEYS if is_team else PLAYER_KEYS
        for kv in body.split(","):
            k, eq, v = kv.partition("=")
            k = k.strip().lower()
            if not eq or k not in allowed:
                raise ValueError(f"'{raw}': '{kv.strip()}' -- {'team' if is_team else 'player'} keys are "
                                 + ", ".join(allowed))
            x, pct = _number(v, k, raw)
            if is_team:
                if k == "ypt" and not pct:
                    raise ValueError(f"'{raw}': a team's ypt is a percent change, e.g. ypt=-5%")
                if k != "ypt" and pct:
                    raise ValueError(f"'{raw}': {k} is a change in {WORDS[k]}, e.g. {k}=-3")
                if not v.strip().startswith(("+", "-")):
                    # 'NO: pass=42' was read as 42 MORE targets (2026-10-05); a team value is
                    # always a change, so it must carry its sign
                    eg = "ypt=-5%" if k == "ypt" else f"{k}=+6"
                    raise ValueError(f"'{raw}': a team's {k} is a CHANGE, not a total -- write the sign, "
                                     f"e.g. {eg}")
                if k == "ypt" and x <= -100:
                    raise ValueError(f"'{raw}': ypt cannot fall by 100% or more")
            else:
                if k == "catch":
                    x = x / 100 if (pct or x > 1) else x
                    if not 0 < x <= 1:
                        raise ValueError(f"'{raw}': catch rate must be between 0 and 100%")
                elif pct:
                    raise ValueError(f"'{raw}': {k} is {WORDS[k]}, not a percent")
                elif x < 0 or (k in ("ypt", "ypc") and x == 0):
                    raise ValueError(f"'{raw}': {k} must be positive")
            out.append({"who": who.upper() if is_team else who, "team": is_team, "key": k, "value": x,
                        "team_of": who.upper() if is_team else team_of,
                        "text": f"{who.upper() if is_team else who}: {k}={v.strip()}"})
    return out


def resolve_players(rules, names, teams, out_names=()) -> list[dict]:
    """Each player rule's name as the report spells it, and his team. Loose
    match (model.norm_name); a name on both teams needs its team; a player
    ruled out says so. Raises ValueError."""
    by = {}
    for n, t in zip(names, teams):
        by.setdefault(norm_name(n), []).append((n, t))
    out_keys = {norm_name(n) for n in out_names}
    resolved = []
    for r in rules:
        if r["team"]:
            resolved.append(r)
            continue
        hits = [h for h in by.get(norm_name(r["who"]), []) if r["team_of"] in (None, h[1])]
        if not hits:
            why = ("is ruled out for this game, so he has no line to move" if norm_name(r["who"]) in out_keys
                   else "is not in this game's player list (check the spelling against the report)")
            raise ValueError(f"{r['who']} {why}")
        if len(hits) > 1:
            raise ValueError(f"{r['who']} plays for both teams' lists: write '{r['who']} ({hits[0][1]}): ...'")
        n, t = hits[0]
        resolved.append({**r, "who": n, "team_of": t, "text": r["text"].replace(r["who"], n, 1)})
    return resolved


def describe(rules) -> str:
    return "; ".join(r["text"] for r in rules)


def apply_before_sim(M, env, rules):
    """Team volume, efficiency and targets, applied to copies of the priced
    players M and the team environment env. Carries are solved later, inside
    the simulation loop (solve_carries), where the rush sampler's inputs exist.
    Returns (M, env)."""
    M = M.copy()
    env = {t: dict(v) for t, v in env.items()}
    for r in (r for r in rules if r["team"]):
        t = r["who"]
        if r["key"] == "pass":
            env[t]["targets"] = max(env[t]["targets"] + r["value"], 1.0)
        elif r["key"] == "rush":
            env[t]["carries"] = max(env[t]["carries"] + r["value"], 1.0)
        else:
            m = M.team == t
            M.loc[m, "ypt"] = M.loc[m, "ypt"] * (1 + r["value"] / 100)
    col = {"catch": "cr", "ypt": "ypt", "ypc": "ypc"}
    me = lambda r: (M.name == r["who"]) & (M.team == r["team_of"])
    for r in (r for r in rules if not r["team"] and r["key"] in col):
        M.loc[me(r), col[r["key"]]] = r["value"]
    # targets: the named players are fixed at their new share; every other
    # tracked teammate AND the depth receivers ('other') give up the difference
    # in proportion, so the team total never moves
    for t in M.team.unique():
        m = M.team == t
        want = {r["who"]: r["value"] for r in rules
                if not r["team"] and r["key"] == "targets" and r["team_of"] == t}
        fixed = M.index[m & M.name.isin(want.keys())]
        if not len(fixed):
            continue
        new = {i: want[M.at[i, "name"]] / env[t]["targets"] for i in fixed}
        tot_new, tot_old = sum(new.values()), float(M.loc[fixed, "ts"].clip(lower=0).sum())
        if tot_new > MAX_SHARE:
            raise ValueError(f"{t}: the targets you set add up to {100 * tot_new:.0f}% of the team's "
                             f"{env[t]['targets']:.1f} per game; the most is {100 * MAX_SHARE:.0f}%")
        rest = m & ~M.index.isin(fixed)
        g = (1 - tot_new) / max(1 - tot_old, 1e-9)
        M.loc[rest, "ts"] = M.loc[rest, "ts"].clip(lower=0) * g
        for i, s in new.items():
            M.at[i, "ts"] = s
    return M, env


def solve_carries(rs, fixed, effective):
    """Input carry shares that give each fixed player j the effective carries
    per game the user set. rs: the team's input shares; fixed: {j: carries};
    effective(shares) -> mean carries per player (the rush sampler, own
    generator). The others keep their proportions and give up the difference
    so the shares' total stays put. Two passes settle the joint case."""
    rs = [max(float(v), 0.0) for v in rs]
    if not fixed:
        return rs
    S = sum(rs)
    others = [i for i in range(len(rs)) if i not in fixed]
    base_others = sum(rs[i] for i in others)
    if base_others <= 0:
        raise ValueError("no teammate carries to take from or give back")
    cur = list(rs)

    def with_fixed(vals):
        s = list(cur)
        for j, v in vals.items():
            s[j] = v
        left = S - sum(s[j] for j in fixed)
        if left < 0:
            return None
        for i in others:
            s[i] = rs[i] * left / base_others
        return s

    for _ in range(2):
        for j, target in fixed.items():
            lo, hi = 0.0, min(MAX_SHARE, S)
            def eff_at(x):
                s = with_fixed({**{k: cur[k] for k in fixed}, j: x})
                return np.inf if s is None else float(effective(s)[j])
            if eff_at(hi) < target:
                raise ValueError(f"{target:g} carries per game is more than the team's carries allow")
            for _ in range(16):
                mid = 0.5 * (lo + hi)
                if eff_at(mid) < target:
                    lo = mid
                else:
                    hi = mid
            cur[j] = 0.5 * (lo + hi)
            nxt = with_fixed({k: cur[k] for k in fixed})
            if nxt is None:                  # the midpoint sat just past feasible: take the low end
                cur[j] = lo
                nxt = with_fixed({k: cur[k] for k in fixed})
            cur = nxt
    got = effective(cur)
    miss = {j: got[j] for j, want in fixed.items() if abs(got[j] - want) > 0.3}
    if miss:
        raise ValueError("these carries cannot all be met together: "
                         + ", ".join(f"you set {fixed[j]:g}, the most the team allows is about {v:.1f}"
                                     for j, v in miss.items()))
    return cur


def rush_effective_fn(env_carries, carries_r, ypc, resid, width, p_resid, p_kneel, qb_i):
    """effective(shares) for solve_carries: mean simulated carries per player,
    on its own generator (common random numbers), never the pricing stream."""
    def f(shares):
        car, _yds, _ = MODEL.simulate_team_rush(np.random.default_rng(SEED), N_SOLVE, env_carries, carries_r,
                                                shares, ypc, resid, width=width, player_resid=p_resid,
                                                player_kneel=p_kneel, qb_index=qb_i)
        return [float(c.mean()) for c in car]
    return f


def net_per_100(price, p_win, p_lose):
    """Expected net per $100 staked at an American price."""
    a = float(price)
    pay = a if a > 0 else 10000 / abs(a)
    return p_win * pay - p_lose * 100
