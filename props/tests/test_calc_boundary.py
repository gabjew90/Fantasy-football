"""props/calc/ (the parlay-leg calculator, DECISIONS #231) must not import the
props engine. It is a user-approved exception to "no parallel engines" only
because it shares nothing with it; an import would make it a second front end
on the engine's numbers. Same AST pattern as test_boundary.py, plus a text
check for the sys.path route the engine's own scripts use."""

from __future__ import annotations

import ast
import re
from pathlib import Path

CALC = Path(__file__).resolve().parents[1] / "calc"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
    return out


def _engine_imports(path: Path) -> list[str]:
    bad = [m for m in _imports(path) if m == "props.engine" or m.startswith("props.engine.")
           or m.split(".")[0] in {"engine", "scripts"}]
    text = path.read_text(encoding="utf-8")
    if re.search(r"sys\.path.*engine|engine.*sys\.path|importlib.*engine", text):
        bad.append("sys.path/importlib route to the engine")
    return bad


def test_calc_exists():
    assert (CALC / "__init__.py").exists()


def test_calc_never_imports_the_engine():
    offenders = [f"{p.relative_to(CALC).as_posix()}: {b}"
                 for p in sorted(CALC.rglob("*.py")) for b in _engine_imports(p)]
    assert not offenders, "props/calc must not import props/engine:\n" + "\n".join(offenders)


def test_the_check_catches_each_route(tmp_path):
    cases = {"a.py": "import props.engine.scripts.model\n",
             "b.py": "from props.engine import x\n",
             "c.py": "import sys\nsys.path.insert(0, 'props/engine/scripts')\nimport model\n",
             "d.py": "from scripts import score_game\n"}
    for name, src in cases.items():
        f = tmp_path / name
        f.write_text(src, encoding="utf-8")
        assert _engine_imports(f), name
    ok = tmp_path / "ok.py"
    ok.write_text("from core import fetch\nfrom . import odds\n", encoding="utf-8")
    assert not _engine_imports(ok)
