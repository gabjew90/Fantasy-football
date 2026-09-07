"""Provenance: what produced this brief, so a bad one can be attributed.

Every recommendation is a claim, and a claim you cannot trace is a claim you
cannot debug. When a brief looks wrong the first question is always the same
-- was the logic wrong or was the input wrong -- and those need opposite
fixes. Without the code commit, the config hash and each source's as-of
timestamp there is no way to tell them apart after the fact.

Cheap by construction: two short git calls with a hard timeout, hashes over
files already on disk. Never raises; an unknown field reads "unknown" and the
brief still ships.
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("manager")

_GIT_TIMEOUT = 5


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(("git", *args), capture_output=True, text=True,
                             timeout=_GIT_TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def commit() -> tuple[str, bool]:
    """(short sha, dirty). ('unknown', False) outside a work tree."""
    sha = _git("rev-parse", "--short", "HEAD")
    if not sha:
        return "unknown", False
    dirty = bool((_git("status", "--porcelain") or "").strip())
    return sha, dirty


def file_hash(path) -> str | None:
    """sha256 prefix of a file, or None when it is absent."""
    p = Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def league_name(ctx) -> str | None:
    """The Cfg is an OBJECT, not a dict: the league name is an attribute and
    cfg.get("...") silently returns None for it."""
    cfg = ctx.get("cfg")
    return getattr(cfg, "league_name", None) or ctx.get("league_name")


def config_hash(ctx) -> str | None:
    """Hash of the league file actually in force, so a settings edit is
    visible in the brief that first ran under it."""
    name = league_name(ctx)
    if not name:
        return None
    return file_hash(Path("leagues") / f"{name}.yaml")


def stamp(ctx, sources: dict | None = None) -> dict:
    """The provenance block carried by a brief (and later by a ledger row)."""
    sha, dirty = commit()
    return {
        "commit": sha,
        "dirty": dirty,
        "config_hash": config_hash(ctx),
        "league": league_name(ctx),
        "week": ctx.get("week"),
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": dict(sources or {}),
    }


def render(st: dict) -> str:
    """One collapsed footer. Readable, greppable, and diffs cleanly week to
    week because the field order is fixed."""
    src = st.get("sources") or {}
    src_line = " · ".join(f"{k} {v}" for k, v in sorted(src.items())) or "none recorded"
    dirty = " (uncommitted changes)" if st.get("dirty") else ""
    return (
        "<details><summary>provenance</summary>\n\n"
        f"- code: `{st.get('commit')}`{dirty}\n"
        f"- league config: `{st.get('config_hash') or 'unknown'}`\n"
        f"- league/week: {st.get('league') or '?'} week {st.get('week') or '?'}\n"
        f"- generated: {st.get('generated_at')}\n"
        f"- sources: {src_line}\n"
        "</details>"
    )
