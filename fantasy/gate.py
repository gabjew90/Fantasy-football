"""The decision gate: may this answer be a personal verdict, or only conditional?

It reads what the run actually retrieved (the Manifest and the league view),
never a hand-written receipt. The fantasy skill's check_decision_gate.py
passed on `scoring_verified: true` typed by the model while two Yahoo scoring
values were wrong; here a check is a comparison the code makes.

Checks:
  roster read after the request   the league roster was fetched during this run
  scoring matches the league      every scoring key in the league yaml equals
                                  the platform's value, stat by stat; a key the
                                  platform does not report is UNVERIFIED, which
                                  fails -- it is not assumed to match
  inputs not stale                no input was served from an older copy after
                                  a failed refresh
  lineup covered                  every player the decision needs has a
                                  projection (or a stated reason he is zero)

A FAIL does not stop the command. It turns the verdict into a CONDITIONAL
comparison and names the failing check.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.manifest import Manifest


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class GateResult:
    checks: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def line(self) -> str:
        if self.passed:
            return "LEAGUE DATA GATE: PASS"
        failed = [f"{c.name} ({c.detail})" for c in self.checks if not c.passed]
        return "LEAGUE DATA GATE: FAIL -- " + "; ".join(failed) + " -- the verdict below is CONDITIONAL"

    def to_dict(self) -> dict:
        return {"passed": self.passed, "checks": [c.__dict__ for c in self.checks]}


def scoring_diffs(yaml_scoring: dict, platform_scoring: dict, tol: float = 1e-9):
    """(mismatched [(key, yaml, platform)], unverified [key])."""
    mism, unverified = [], []
    for k, v in (yaml_scoring or {}).items():
        if k not in (platform_scoring or {}):
            unverified.append(k)
        elif abs(float(v) - float(platform_scoring[k])) > tol:
            mism.append((k, float(v), float(platform_scoring[k])))
    return mism, sorted(unverified)


def scoring_only(yaml_scoring: dict, platform_scoring: dict) -> GateResult:
    """Just the scoring check, for a command that uses no roster."""
    g = GateResult()
    mism, unverified = scoring_diffs(yaml_scoring, platform_scoring)
    detail = "; ".join([f"{k}: yaml {a} vs platform {b}" for k, a, b in mism]
                       + [f"{k}: platform does not report it" for k in unverified])
    g.checks.append(Check("scoring matches the league", not mism and not unverified,
                          detail or f"{len(yaml_scoring)} keys verified"))
    return g


def evaluate(manifest: Manifest, yaml_scoring: dict, platform_scoring: dict,
             needed: list, projections: dict) -> GateResult:
    g = GateResult()
    roster = manifest.get("league roster")
    g.checks.append(Check(
        "roster read after the request", manifest.read_after_start("league roster"),
        "fetched during this run" if manifest.read_after_start("league roster")
        else f"{(roster or {}).get('status', 'not read')} copy from {(roster or {}).get('fetched_at_utc') or 'unknown time'}"))
    g.checks += scoring_only(yaml_scoring, platform_scoring).checks
    stale = manifest.stale()
    g.checks.append(Check("inputs not stale", not stale,
                          "; ".join(f"{e['name']} {e['status']}" for e in stale) or "all fresh or cached"))
    missing = [str(p) for p in needed if str(p) not in projections]
    g.checks.append(Check("lineup covered", not missing,
                          f"no projection for {', '.join(missing)}" if missing else f"{len(needed)} players"))
    return g
