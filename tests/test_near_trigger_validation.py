from near_trigger_validation import (
    STATUS_ACCUMULATING,
    STATUS_DEFERRED,
    STATUS_PASS,
    evaluate_near_trigger_validation,
)


def test_accumulating_until_minimum_evidence_is_met():
    verdict = evaluate_near_trigger_validation({
        "shadow_episodes": 149,
        "unique_symbols": 74,
        "shadow_breakouts_3d": 45,
        "shadow_breakouts_5d": 60,
        "control_episodes": 300,
        "control_breakouts_3d": 30,
        "control_breakouts_5d": 45,
    })
    assert verdict.status == STATUS_ACCUMULATING
    assert verdict.evidence_ready is False
    assert verdict.primary_pass is None


def test_pass_requires_absolute_rate_and_lift_gates():
    verdict = evaluate_near_trigger_validation({
        "shadow_episodes": 200,
        "unique_symbols": 100,
        "shadow_breakouts_3d": 60,
        "shadow_breakouts_5d": 80,
        "control_episodes": 400,
        "control_breakouts_3d": 60,
        "control_breakouts_5d": 80,
    })
    assert verdict.status == STATUS_PASS
    assert verdict.evidence_ready is True
    assert verdict.primary_pass is True
    assert verdict.shadow_onset_rate_3d == 0.30
    assert verdict.shadow_onset_rate_5d == 0.40
    assert verdict.lift_3d == 2.0
    assert verdict.lift_5d == 2.0


def test_deferred_when_absolute_rate_passes_but_lift_fails():
    verdict = evaluate_near_trigger_validation({
        "shadow_episodes": 200,
        "unique_symbols": 100,
        "shadow_breakouts_3d": 50,
        "shadow_breakouts_5d": 70,
        "control_episodes": 400,
        "control_breakouts_3d": 80,
        "control_breakouts_5d": 100,
    })
    assert verdict.status == STATUS_DEFERRED
    assert verdict.evidence_ready is True
    assert verdict.primary_pass is False
    assert any(f.startswith("lift_3d") for f in verdict.failures)
    assert any(f.startswith("lift_5d") for f in verdict.failures)


def test_deferred_when_lift_passes_but_absolute_rate_fails():
    verdict = evaluate_near_trigger_validation({
        "shadow_episodes": 200,
        "unique_symbols": 100,
        "shadow_breakouts_3d": 30,
        "shadow_breakouts_5d": 50,
        "control_episodes": 400,
        "control_breakouts_3d": 20,
        "control_breakouts_5d": 30,
    })
    assert verdict.status == STATUS_DEFERRED
    assert verdict.evidence_ready is True
    assert verdict.primary_pass is False
    assert any(f.startswith("shadow_onset_rate_3d") for f in verdict.failures)
    assert any(f.startswith("shadow_onset_rate_5d") for f in verdict.failures)
