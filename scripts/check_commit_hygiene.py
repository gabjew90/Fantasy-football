"""Refuse commits that mix generated gate-pattern state with code changes.

`state/*.json` is written by the scheduled in-season workflows. When it rides
along in a feature commit -- which `git add -A` does silently and often; six
commits in this repo's history did it -- two things break. The state history
stops being a readable record of what the manager actually did and when, and a
revert of the code change also reverts live state.

State commits belong to the workflows that produce them, on their own.

    python scripts/check_commit_hygiene.py            # staged changes
    python scripts/check_commit_hygiene.py --range main...HEAD
"""

from __future__ import annotations

import argparse
import subprocess
import sys

STATE_PREFIX = "state/"
CODE_PREFIXES = ("draftkit/", "manager/", "scripts/", "tests/")


def offending(paths: list[str]) -> tuple[list[str], list[str]]:
    """(state files, code files) when BOTH are present, else ([], []).

    Separators are normalised here rather than only at the git boundary: this
    runs on a Windows host, and a check that silently passes because it was
    handed backslashes is worse than no check.
    """
    norm = [p.replace("\\", "/") for p in paths]
    state = sorted(p for p in norm if p.startswith(STATE_PREFIX))
    code = sorted(p for p in norm if p.startswith(CODE_PREFIXES))
    return (state, code) if state and code else ([], [])


def changed(rng: str | None) -> list[str]:
    cmd = (["git", "diff", "--name-only", rng] if rng
           else ["git", "diff", "--cached", "--name-only"])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default=None,
                    help="git range to check instead of the staged index")
    a = ap.parse_args()

    state, code = offending(changed(a.range))
    if not state:
        return 0
    print("commit hygiene: state/ changes are mixed with code changes.\n")
    print("  state:", ", ".join(state))
    print("  code :", ", ".join(code[:6]) + (" ..." if len(code) > 6 else ""))
    print("\nCommit the state files separately, or unstage them:")
    print(f"  git restore --staged {' '.join(state)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
