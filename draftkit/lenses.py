"""The three pre-season graders, frozen for the season-long scoreboard.

Sources:
- BOARD: reports/draft_review.md (our model's projected starter points, Aug 23)
- LEAGUE: the consensus table posted to the league chat post-draft
- WIZARD: the "Omnibeta Degens Draft Card" grade ORDER (construction lens; its
  points column repeated the league table, so rank is what it contributed)
"""

from __future__ import annotations

def load_lenses(cfg) -> dict[str, tuple[int, int, int]]:
    """Frozen pre-season grader table for THIS league, from its yaml.

    League facts never live in this module (multi-league rule): a league with
    no `lenses:` block degrades the scoreboard to off with a banner, and must
    never silently inherit another league's numbers.
    """
    block = (cfg.get("lenses") or {}) if cfg is not None else {}
    out: dict[str, tuple[int, int, int]] = {}
    for team, v in block.items():
        if isinstance(v, (list, tuple)) and len(v) == 3:
            out[str(team)] = (int(v[0]), int(v[1]), int(v[2]))
    return out


def spearman(rank_a: list[int], rank_b: list[int]) -> float:
    n = len(rank_a)
    if n < 2:
        return 0.0
    d2 = sum((a - b) ** 2 for a, b in zip(rank_a, rank_b))
    return 1 - (6 * d2) / (n * (n * n - 1))


def _ranks(values: list[float], descending: bool = True) -> list[int]:
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=descending)
    ranks = [0] * len(values)
    for r, i in enumerate(order, 1):
        ranks[i] = r
    return ranks


def scoreboard_md(actual_points: dict[str, float], cfg=None) -> str:
    """Cumulative actual points per team vs the three pre-season orderings.

    The grader table is a LEAGUE fact read from the league yaml; a league
    without one degrades the scoreboard to off with a banner rather than
    borrowing another league's numbers.
    """
    lenses = load_lenses(cfg)
    if not lenses:
        return ("## Three-lens scoreboard\n_off for this league — its yaml has "
                "no `lenses:` block (frozen pre-season grader table)_")
    teams = [t for t in lenses if t in actual_points]
    if len(teams) < 3:
        return "## Three-lens scoreboard\n_not enough completed weeks yet_"
    actual = [actual_points[t] for t in teams]
    a_rank = _ranks(actual)
    board_r = _ranks([lenses[t][0] for t in teams])
    league_r = _ranks([lenses[t][1] for t in teams])
    wizard_r = _ranks([lenses[t][2] for t in teams], descending=False)
    rows = sorted(zip(teams, actual, a_rank), key=lambda r: -r[1])
    lines = ["## Three-lens scoreboard (season to date)",
             "",
             "| team | actual pts | our board said | league table said | wizard said |",
             "|---|---|---|---|---|"]
    for t, pts, _ in rows:
        i = teams.index(t)
        lines.append(f"| {t} | {pts:.0f} | #{board_r[i]} | #{league_r[i]} | #{wizard_r[i]} |")
    lines += ["",
              f"Rank agreement with reality so far — our board: "
              f"**{spearman(a_rank, board_r):+.2f}** · league table: "
              f"**{spearman(a_rank, league_r):+.2f}** · wizard: "
              f"**{spearman(a_rank, wizard_r):+.2f}** (1.0 = perfect)"]
    return "\n".join(lines)
