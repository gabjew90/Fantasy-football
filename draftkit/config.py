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


class Config:
    def __init__(self, data: dict[str, Any], root: Path):
        self._data = data
        self.root = root

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        p = Path(path) if path else DEFAULT_CONFIG
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data, p.resolve().parent)

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
