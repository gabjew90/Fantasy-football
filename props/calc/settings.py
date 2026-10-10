"""Load props/calc/settings.yaml and enforce its two rules: at most 8 tuned
settings, each with a plain-English comment."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.yaml"
MAX_TUNED = 8
TUNED_NAMES = ("carry_r", "day_sd", "target_r", "completion_r", "k_ypc", "k_catch", "k_ypr", "k_ypcomp")


def problems(text: str) -> list[str]:
    """What is wrong with a settings file's text, or [] when it is valid."""
    out = []
    data = yaml.safe_load(text) or {}
    tuned = data.get("tuned") or {}
    fixed = data.get("fixed_not_tuned") or {}
    if set(data) != {"tuned", "fixed_not_tuned"}:
        out.append(f"top-level blocks must be tuned and fixed_not_tuned, got {sorted(data)}")
    if len(tuned) > MAX_TUNED:
        out.append(f"{len(tuned)} tuned settings; the cap is {MAX_TUNED}")
    if set(tuned) != set(TUNED_NAMES):
        out.append(f"tuned settings {sorted(tuned)} differ from the named list {sorted(TUNED_NAMES)}")
    for key in list(tuned) + list(fixed):
        if not re.search(rf"^\s+{re.escape(key)}:[^#\n]*#\s*\S", text, re.M):
            out.append(f"{key} has no plain-English comment")
    return out


def load(path: Path = SETTINGS_PATH) -> dict:
    """{"tuned": {...}, "fixed": {...}}; raises on an invalid file."""
    text = path.read_text(encoding="utf-8")
    bad = problems(text)
    if bad:
        raise ValueError(f"{path}: " + "; ".join(bad))
    data = yaml.safe_load(text)
    return {"tuned": dict(data["tuned"]), "fixed": dict(data["fixed_not_tuned"])}
