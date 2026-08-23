"""The three pre-season graders, frozen for the season-long scoreboard.

Sources:
- BOARD: reports/draft_review.md (our model's projected starter points, Aug 23)
- LEAGUE: the consensus table posted to the league chat post-draft
- WIZARD: the "Omnibeta Degens Draft Card" grade ORDER (construction lens; its
  points column repeated the league table, so rank is what it contributed)
"""

from __future__ import annotations

# team display name -> (our board pts, league grader pts, wizard rank 1..12)
LENSES: dict[str, tuple[int, int, int]] = {
    "farmerjamal":       (1989, 1995, 10),
    "bankerkyle":        (1881, 2040, 6),
    "ayatollahabdullah": (1806, 2009, 9),
    "ArcticAces":        (1805, 2015, 5),
    "Tulchh":            (1765, 1937, 7),
    "cbarone":           (1755, 1969, 2),
    "Lord2Pale":         (1680, 1923, 12),
    "vincenzo31":        (1676, 2016, 3),
    "Dizzydean6":        (1656, 1845, 11),
    "DihtrickCohones":   (1639, 2046, 4),
    "rybryethguy":       (1618, 2060, 8),
    "StinkyDillPickle":  (1611, 1998, 1),
}


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


def scoreboard_md(actual_points: dict[str, float]) -> str:
    """Cumulative actual points per team vs the three pre-season orderings."""
    teams = [t for t in LENSES if t in actual_points]
    if len(teams) < 3:
        return "## Three-lens scoreboard\n_not enough completed weeks yet_"
    actual = [actual_points[t] for t in teams]
    a_rank = _ranks(actual)
    board_r = _ranks([LENSES[t][0] for t in teams])
    league_r = _ranks([LENSES[t][1] for t in teams])
    wizard_r = _ranks([LENSES[t][2] for t in teams], descending=False)
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
