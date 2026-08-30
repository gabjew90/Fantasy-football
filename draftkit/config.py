"""Config loading. One YAML file at repo root drives every stage."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config.yaml"

SKILL_POSITIONS = ("QB", "RB", "WR", "TE")
ALL_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self, data: dict[str, Any], root: Path, league: str | None = None):
        self._data = data
        self.root = root
        self.league_name = league

    @classmethod
    def load(cls, path: str | Path | None = None,
             league: str | None = None) -> "Config":
        """Globals from config.yaml, deep-merged under leagues/<name>.yaml.

        League selection precedence: explicit arg > DRAFTKIT_LEAGUE env >
        default_league in config.yaml. A missing league file is a loud error —
        never silently fall back to another league's facts.
        """
        p = Path(path) if path else DEFAULT_CONFIG
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        root = p.resolve().parent
        name = league or os.environ.get("DRAFTKIT_LEAGUE") or data.get("default_league")
        if name:
            lf = root / "leagues" / f"{name}.yaml"
            if not lf.exists():
                raise FileNotFoundError(
                    f"league config not found: {lf} — create it or run "
                    f"`python -m draftkit onboard <league_id> --name {name}`")
            with open(lf, encoding="utf-8") as f:
                data = _deep_merge(data, yaml.safe_load(f) or {})
        return cls(data, root, name)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    @property
    def league_id(self) -> str:
        return str(self._data["league_id"])

    @property
    def draft_id(self) -> str:
        return str(self._data["draft_id"])

    def path(self, kind: str) -> Path:
        p = self.root / self._data["paths"][kind]
        os.makedirs(p, exist_ok=True)
        return p

    @property
    def baselines(self) -> dict[str, int]:
        return dict(self._data["replacement_baselines"])

    @property
    def pool_sizes(self) -> dict[str, int]:
        return dict(self._data["pool_sizes"])
