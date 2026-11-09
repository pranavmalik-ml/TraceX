"""Fan-out signal: number of unique outgoing counterparties."""

from typing import Dict, Any, Tuple


def score_fan_out(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """Score based on many outgoing counterparties."""
    if thresholds is None:
        thresholds = {
            "fan_out_high": 10,
            "max_contribution": 15.0,
        }

    unique_out = features.get("unique_out_counterparties", 0)
    score = 0.0
    if unique_out > 0:
        if unique_out >= thresholds["fan_out_high"]:
            score = thresholds["max_contribution"]
        else:
            score = (unique_out / thresholds["fan_out_high"]) * thresholds["max_contribution"]
    score = min(score, thresholds["max_contribution"])

    evidence = {
        "unique_out_counterparties": unique_out,
        "threshold_high": thresholds["fan_out_high"],
    }
    return score, evidence