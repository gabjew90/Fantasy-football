"""The props modules calc reuses (props/journal.py, props/persist.py), imported
the way they import each other: props/ on sys.path and bare module names, so
calc and the journal share one module object each (one JOURNAL_ROOT, one
RECORD_ROOT). The journal's grading imports settle and calls.py; that indirect
import is user-approved (2026-10-10). Nothing here reaches props/engine."""

from __future__ import annotations

import sys
from pathlib import Path

PROPS = Path(__file__).resolve().parents[1]
if str(PROPS) not in sys.path:
    sys.path.insert(0, str(PROPS))

import journal  # noqa: E402
import persist  # noqa: E402

__all__ = ["journal", "persist"]
