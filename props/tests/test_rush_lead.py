"""Round 15: the carry-share rescale with the correction split away from the
lead back (model.rescale_rush_shares, width setting rush_norm_lead)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402

# QB (index 0, left alone), lead back, #2 back, a receiver's jet sweeps
SHORT = [0.10, 0.45, 0.15, 0.02]           # backs + WR = 0.62; target 1 - 0.12 - 0.10 = 0.78
OVER = [0.10, 0.55, 0.35, 0.05]            # 0.95 > 0.78


def _w(**kw):
    return {"rush_other_share": 0.12, "rush_norm_strength": 1.0, "rush_norm_qb": False, **kw}


def test_off_and_proportional_are_unchanged():
    assert np.array_equal(M.rescale_rush_shares(SHORT, {}, 0), np.array(SHORT))
    old = M.rescale_rush_shares(SHORT, _w(), 0)                       # #103's multiplicative form
    assert old[1:].sum() == pytest.approx(0.78) and old[0] == 0.10
    assert np.allclose(M.rescale_rush_shares(SHORT, _w(rush_norm_lead=1.0), 0), old), \
        "lead weight 1.0 at full strength is #103's proportional rescale"


def test_lead_zero_puts_the_whole_correction_on_the_others():
    for shares in (SHORT, OVER):
        out = M.rescale_rush_shares(shares, _w(rush_norm_lead=0.0), 0)
        assert out[1] == pytest.approx(shares[1]), "the lead back's share is untouched"
        assert out.sum() == pytest.approx(0.88), "everyone priced sums to 1 - other"
    short = M.rescale_rush_shares(SHORT, _w(rush_norm_lead=0.0), 0)
    assert short[0] == SHORT[0], "no overshoot: the QB's raw share"
    assert short[2] / SHORT[2] == pytest.approx(short[3] / SHORT[3]), "the others share it in proportion"


def _sampler_qb_share(rs, qb=0):
    """The QB's share of the carries after the sampler's own normalisation
    (simulate_team_rush: 'rest' fills to 1, then everything is divided by the total)."""
    rs = np.asarray(rs, dtype=float)
    p = np.append(rs, max(1.0 - rs.sum(), 0.0))
    return (p / p.sum())[qb]


@pytest.mark.parametrize("shares", [SHORT, OVER, [0.12, 0.70, 0.40, 0.03]])
@pytest.mark.parametrize("strength", [0.5, 1.0])
@pytest.mark.parametrize("lead", [0.0, 0.5, 1.0])
def test_the_qb_gets_exactly_the_share_the_shipped_sampler_gives_him(shares, strength, lead):
    out = M.rescale_rush_shares(shares, _w(rush_norm_lead=lead, rush_norm_strength=strength), 0)
    assert _sampler_qb_share(out) == pytest.approx(_sampler_qb_share(shares)), \
        "the rescale moves the backs only (round 15: the QB used to gain ~2% in overshoot games)"


def test_partial_lead_weight_and_strength():
    half = M.rescale_rush_shares(SHORT, _w(rush_norm_lead=0.5, rush_norm_strength=0.5), 0)
    gap = (0.78 - 0.62) * 0.5
    wts = np.array([0.45 * 0.5, 0.15, 0.02])
    assert np.allclose(half[1:], np.array(SHORT[1:]) + gap * wts / wts.sum())


def test_an_overshoot_never_goes_negative():
    tiny = [0.0, 0.90, 0.01, 0.0]             # 0.91 against 0.88, lead weight 0: only 0.01 to take from
    out = M.rescale_rush_shares(tiny, _w(rush_norm_lead=0.0), None)
    assert (out >= 0).all() and out[1] == pytest.approx(0.90)


def test_validate_and_off_default():
    assert M.WIDTH_OFF["rush_norm_lead"] is None
    assert M.validate_width({"rush_norm_lead": 0.25})["rush_norm_lead"] == 0.25
    with pytest.raises(ValueError):
        M.validate_width({"rush_norm_lead": 1.5})


def test_the_shipped_settings_carry_the_round_15_rescale():
    import json
    w = M.validate_width(json.loads((ENGINE.parent / "resources" / "width_params.json").read_text(encoding="utf-8")))
    assert (w["rush_other_share"], w["rush_norm_strength"], w["rush_norm_qb"], w["rush_norm_lead"]) == (0.12, 0.5, False, 1.0)


def test_tied_lead_backs_share_the_lead_weight_whatever_the_order():
    a = M.rescale_rush_shares([0.10, 0.40, 0.40, 0.02], _w(rush_norm_lead=0.0), 0)
    b = M.rescale_rush_shares([0.10, 0.02, 0.40, 0.40], _w(rush_norm_lead=0.0), 0)
    assert a[1] == a[2] == pytest.approx(0.40) and b[2] == b[3] == pytest.approx(0.40)
    assert a[3] == pytest.approx(b[1]), "the same correction whatever the roster order"


def test_the_scorer_and_the_harness_hand_the_rush_sim_the_same_inputs():
    """The harness grades what prices only if both call sites pass the width
    settings and the starting QB: without qb_index the QB guard has no QB."""
    import re
    for script in ("score_game.py", "backtest.py"):
        src = (ENGINE / script).read_text(encoding="utf-8")
        calls = re.findall(r"simulate_team_rush\((.*?)\)\s*\n", src, flags=re.S)
        assert calls, script
        for c in calls:
            assert "width=" in c and "qb_index=" in c, f"{script}: {c[:80]}"
