"""Risk scoring logic."""

from typing import Dict, Any, List
from .models import RiskResult, SignalContribution
from .signals import (
    score_velocity,
    score_fan_in,
    score_fan_out,
    score_rapid_movement,
    score_taint_exposure,
    score_multiple_sources,
    score_amount_anomaly,
    score_dormant_activation,
    score_circular_movement,
)
from .thresholds import get_default_thresholds


def calculate_risk(entity_id: str, entity_type: str, features: Dict[str, Any],
                   thresholds: Dict[str, Any] = None) -> RiskResult:
    """
    Compute risk score and produce RiskResult.
    """
    if thresholds is None:
        thresholds = get_default_thresholds()

    # Compute each signal contribution
    signal_functions = [
        ("velocity", score_velocity),
        ("fan_in", score_fan_in),
        ("fan_out", score_fan_out),
        ("rapid_movement", score_rapid_movement),
        ("taint_exposure", score_taint_exposure),
        ("multiple_sources", score_multiple_sources),
        ("amount_anomaly", score_amount_anomaly),
        ("dormant_activation", score_dormant_activation),
        ("circular_movement", score_circular_movement),
    ]

    contributions = []
    total_score = 0.0

    for signal_code, signal_func in signal_functions:
        # Each signal function returns (score, evidence_dict)
        score, evidence = signal_func(features, thresholds.get(signal_code, {}))
        # Clamp to 0..max contribution (should be already)
        total_score += score
        contributions.append(SignalContribution(
            code=signal_code.upper(),
            label=_get_label(signal_code),
            contribution=round(score, 2),
            evidence=evidence
        ))

    # Clamp total score to 0..100
    risk_score = max(0.0, min(100.0, total_score))

    # Risk level classification
    risk_level = _classify_risk(risk_score, thresholds.get("risk_levels", {}))

    return RiskResult(
        entity_id=entity_id,
        entity_type=entity_type,
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        signals=contributions,
        model_version="rules-v1"
    )


def _get_label(code: str) -> str:
    """Human-readable label for signal code."""
    labels = {
        "velocity": "Transaction velocity",
        "fan_in": "Fan-in (many incoming counterparties)",
        "fan_out": "Fan-out (many outgoing counterparties)",
        "rapid_movement": "Rapid fund movement",
        "taint_exposure": "Taint exposure",
        "multiple_sources": "Multiple fraud sources",
        "amount_anomaly": "Amount anomaly",
        "dormant_activation": "Dormant activation",
        "circular_movement": "Circular movement",
    }
    return labels.get(code, code.replace("_", " ").title())


def _classify_risk(score: float, levels_config: Dict[str, float]) -> str:
    """
    Classify risk level based on score thresholds.
    Default levels: LOW (<20), MEDIUM (20-40), HIGH (40-70), CRITICAL (>=70)
    """
    default = {"LOW": 20, "MEDIUM": 40, "HIGH": 70, "CRITICAL": 100}
    config = {**default, **levels_config}
    if score < config["LOW"]:
        return "LOW"
    elif score < config["MEDIUM"]:
        return "MEDIUM"
    elif score < config["HIGH"]:
        return "HIGH"
    else:
        return "CRITICAL"