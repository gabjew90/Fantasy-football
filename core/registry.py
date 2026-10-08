"""Every model and projection source, with its status and its evidence.

The rule (docs/plans/2026-09-24-consolidation-plan.md, section 4): a
component that prices a prop or projects fantasy points is registered here or
it does not exist. tests/test_core_guardrails.py fails on an entry whose
module or evidence file is missing, and on a status without what it requires.

Statuses:
  live         in use, and `evidence` names the validation artifact(s) that
               earned it the place
  provisional  in use WITHOUT validation; `note` must say why and what would
               validate it. This is the honest label for, e.g., the TD market
               blend weight -- not a way around the rule
  shadow       computed and logged beside a live component, never shown as the
               answer; `evidence` names the harness comparing them
  deprecated   still in the tree, scheduled for deletion; `retire_in` names the
               consolidation step that deletes it

Promotion (shadow or provisional -> live) needs a measured harness delta, not
a predicted one (CLAUDE.md: measure before cutting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

KINDS = ("prop_model", "projection_source", "range_model", "measurement")
STATUSES = ("live", "provisional", "shadow", "deprecated")


@dataclass(frozen=True)
class Component:
    name: str
    kind: str
    module: str                      # repo-relative path of the code that computes it
    status: str
    evidence: tuple[str, ...] = ()   # repo-relative validation artifacts
    note: str = ""
    retire_in: str = ""              # consolidation step, for deprecated entries
    markets: tuple[str, ...] = field(default=())


COMPONENTS: tuple[Component, ...] = (
    # ------------------------------------------------------------- props
    Component("receiving_hier_v2", "prop_model", "props/engine/scripts/model.py", "live",
              evidence=("reports/yardage_harness.md", "reports/width_tuning.md",
                        "props/engine/resources/model_registry.md",
                        "reports/current_settings_check_2026-10-06.md", "reports/round34_receiving_joint.md"),
              note="with the width settings (props-v1.20, resources/width_params.json, tuned on 2022-23): "
                   "passed all four harness checks on 2024-25 -- beats baseline A each season, unbiased, "
                   "19.0% / 19.2% outside p10-p90, every 60-90% bucket within 3 points (yards exactly at "
                   "the limit). Since: target-share concentration 40 -> 60 (round 34, DECISIONS #195, kept "
                   "under the spread rule #204); re-checked at the current settings "
                   "(reports/current_settings_check_2026-10-06.md) both stay inside the width bar, but at the "
                   "main line the Over hits ~3 points more often than the engine on receiving yards and 1.4 on "
                   "receptions (#197). At Sleeper's real lines (weeks 2-4) the engine trails the market (#202). "
                   "Not yet tested against posted lines (eligibility.VALIDATED_MARKETS)",
              markets=("player_receptions", "player_reception_yds")),
    Component("rush_yds_v0", "prop_model", "props/engine/scripts/model.py", "live",
              evidence=("reports/yardage_harness.md", "reports/width_tuning.md", "reports/width_tuning_qb.md",
                        "reports/round30_conversion.md", "reports/round29_market_runs.md",
                        "reports/current_settings_check_2026-10-06.md"),
              note="props-v1.21 (DECISIONS #100): starting QBs (carry grid + kneel-downs, own width "
                   "settings) pass all four checks -- 22.0% outside p10-p90, worst bucket 2.9 points; running "
                   "backs 20.3% and 3.4 points, 0.4 over the calibration limit -- USER DECISION: noise, kept "
                   "live. Known: backs run ~4% low (shares summing past 1 are scaled down); QBs ran ~12% "
                   "high in 2025. The run-defense adjustment is measured to help. Since: the carry-share "
                   "rescale (round 15, #133); yards-per-carry log-sd 0.30 -> 0.15 (round 30, #189); the backs' "
                   "carries 50% toward the market (round 39, #204). QB rushing is OFF THE BOARD (#188, #190): "
                   "simulated, never priced or recorded. Current width (current_settings_check): backs' "
                   "rushing too narrow in the tails (23.4% outside the 80% range). Not tested against posted "
                   "lines",
              markets=("player_rush_yds",)),
    Component("pass_yds_v0", "prop_model", "props/engine/scripts/model.py", "live",
              evidence=("reports/yardage_harness.md", "reports/rush_rec_calibration.md",
                        "reports/round38_qb_passing_bias.md"),
              note="props-v1.24 (DECISIONS #105): the starting QB's passing yards from his receivers' draws "
                   "in the same simulation, plus the depth receivers, times a starter's share. 2024-25: "
                   "actual/model 0.986, 18.1% outside p10-p90, beats baseline A pooled (+1.08, interval "
                   "excludes 0) and in 2025; 2024's interval includes 0 (+0.86); a 16-bet 80-90% bucket "
                   "misses by 18 points and Over 60-70% by 3.2 (all others within 3) -- USER DECISION: "
                   "priced, bar unchanged. The gain is early season (weeks 2-4 +4.9); from week 5 it ties "
                   "baseline A. The starter is the depth-chart QB first (DECISIONS #105). CORRECTED "
                   "2026-10-06: graded on the QB who actually started, the width FAILS (14.4% outside, too "
                   "wide; #187) and the Over at the main line ran ~6 points above the engine (#196-#197). "
                   "Round 38 ships (implied points ^0.2, x1.04; #199, the width guard overridden by the user; "
                   "replicated on four seeds, #203): most of the bias gone, still too wide (11.9%). Not "
                   "tested against posted lines",
              markets=("player_pass_yds",)),
    Component("rush_rec_sum_v0", "prop_model", "props/engine/scripts/score_game.py", "live",
              evidence=("reports/rush_rec_calibration.md", "reports/current_settings_check_2026-10-06.md"),
              note="a back's (or receiver's) rushing + receiving yards: the sum of his rushing and "
                   "receiving draws in each simulation, QBs excluded; priced since it passed its 2022-25 "
                   "calibration check (width 0.223, bias +1.7%, no band fails; residual correlation +0.044, "
                   "so independent draws hold; DECISIONS #187). After round 30 the whole-chain width FAILS "
                   "(24.9% outside the 80% range, too narrow in the tails; current_settings_check). Not "
                   "tested against posted lines",
              markets=("player_rush_reception_yds",)),
    Component("anytime_td_v1", "prop_model", "props/engine/scripts/td_v1.py", "live",
              evidence=("reports/td_v1.md", "reports/td_layer1.md", "reports/td_layer2.md"),
              note="layers 1-2: team TD count and per-channel scorer shares",
              markets=("player_anytime_td",)),
    Component("td_joint_v0", "prop_model", "props/engine/scripts/td_joint.py", "live",
              evidence=("props/engine/resources/td_parlay_gate.json", "reports/td_layer3.md"),
              note="layer 3: only the pair classes the parlay gate opens are shown",
              markets=("player_anytime_td",)),
    Component("td_market_v0", "prop_model", "props/engine/scripts/td_market.py", "provisional",
              note="layer 4 blend at a provisional weight 0.5; props/blend.py fits the "
                   "real weight once 300 v1 calls settle",
              markets=("player_anytime_td",)),
    Component("props_fantasy_export", "projection_source", "props/engine/scripts/score_game.py",
              "provisional",
              note="fantasy points from the props engine's joint simulation (fantasy_points_*.csv); since "
                   "step 3 the MODEL answer of `nfl fantasy scenario`, keyed by gsis_id. Never backtested as "
                   "fantasy points: a walk-forward against weekly actuals would validate it. Passing is not "
                   "modelled, so a QB row is rushing only"),

    # ---------------------------------------------------------- fantasy
    Component("sleeper_weekly", "projection_source", "fantasy/sources/sleeper_weekly.py", "provisional",
              note="Sleeper's weekly projection in league scoring. Its errors are measured (the "
                   "dispersion_v0 reports: ~7 points per player-week, RB outcomes ran under it in "
                   "2025) but its accuracy has never been compared with market_points; the ledger's "
                   "graded weeks will do that"),
    Component("market_points", "projection_source", "fantasy/sources/market_points.py", "live",
              evidence=("fantasy/resources/market_shape_params.json",),
              note="posted Sleeper Picks lines converted to expected points; the shape table's "
                   "holdout (2024 ratios on 2025) is in its holdout_check block. Partial coverage: "
                   "only players with posted markets, never a QB's passing TDs"),
    Component("dispersion_v0", "range_model", "fantasy/dispersion.py", "live",
              evidence=("reports/dispersion_v0.omnibeta.md", "reports/dispersion_v0.keefamania.md",
                        "fantasy/resources/dispersion_v0.omnibeta.json",
                        "fantasy/resources/dispersion_v0.keefamania.json"),
              note="fit 2024, tested 2025: the p10-p90 range held 81.6% (Omnibeta) / 80.5% "
                   "(Keefamania) of outcomes and beat a bucket-scaled normal by ~2% on pinball loss; "
                   "QB is no better than that baseline and its low tail runs heavy -- stated with every "
                   "QB range"),
    Component("noise_bands_v0", "measurement", "fantasy/evidence.py", "live",
              evidence=("reports/noise_bands_v0.md", "fantasy/resources/noise_bands_v0.json"),
              note="week-to-week noise of each role-defining usage metric (snap, target, carry, air-yard "
                   "share, WOPR) by position and usage level (robust SD); the change threshold is calibrated "
                   "to a 5% false-alarm rate on shuffled 2024 seasons and fires 3.3-7.0% on shuffled 2025 "
                   "seasons; bands within 12% across seasons"),
    Component("weekly_blend_v0", "projection_source", "fantasy/weekly.py", "provisional",
              note="the weekly mean `nfl fantasy lineup` optimises: Sleeper, blended with market_points "
                   "where the player has a full market board, at a weight decaying from 0.6 in week 1 to 0 "
                   "by week 9 (config.yaml fantasy.market_weight). The user's framework, not a measurement: "
                   "every decision records both inputs, so the ledger can grade the blend against each"),
    Component("rest_of_season_consensus", "projection_source", "manager/consensus.py",
              "provisional",
              note="Sleeper + ESPN + FantasyPros rescaled to a common basis; the ledger "
                   "has no graded weeks yet, which is what would validate it (the Tuesday job "
                   "that graded it retired with the cron stack, DECISIONS #212: grading is "
                   "manager.ledger.grade_week, run by hand)"),
    Component("fantasypros", "projection_source", "manager/fantasypros.py", "live",
              evidence=("reports/fpros_gate.md",)),
    Component("external_season_lines", "projection_source", "draftkit/external.py", "live",
              evidence=("reports/sheet_compare.keefamania.md", "reports/source_gate.md"),
              note="season lines (FantasyPros sheet, Sleeper/Rotowire, ESPN) scored in league "
                   "scoring; the draft board's projection"),
    Component("model_projection", "projection_source", "draftkit/projections.py", "deprecated",
              evidence=("reports/projection_backtest.omnibeta.md",),
              retire_in="2027 draft prep",
              note="the in-house season model; lost its own backtest. Draft-only, frozen: still "
                   "Omnibeta's draft source and the board-identity path (DECISIONS #108)"),
)


def problems(components=COMPONENTS, root: Path = REPO_ROOT) -> list[str]:
    """Everything wrong with the registry, as sentences. Empty means valid."""
    out, seen = [], set()
    for c in components:
        where = f"{c.name}:"
        if c.name in seen:
            out.append(f"{where} registered twice")
        seen.add(c.name)
        if c.kind not in KINDS:
            out.append(f"{where} unknown kind {c.kind!r}")
        if c.status not in STATUSES:
            out.append(f"{where} unknown status {c.status!r}")
        if not (root / c.module).is_file():
            out.append(f"{where} module {c.module} does not exist")
        for e in c.evidence:
            if not (root / e).is_file():
                out.append(f"{where} evidence {e} does not exist")
        if c.status in ("live", "shadow") and not c.evidence:
            out.append(f"{where} {c.status} needs evidence (a validation artifact)")
        if c.status == "provisional" and not c.note:
            out.append(f"{where} provisional needs a note saying why and what would validate it")
        if c.status == "deprecated" and not c.retire_in:
            out.append(f"{where} deprecated needs retire_in")
    return out


def by_status(status: str, components=COMPONENTS) -> list[Component]:
    return [c for c in components if c.status == status]
