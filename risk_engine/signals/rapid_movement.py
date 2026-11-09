"""Rapid fund movement signal: funds moved out quickly after incoming."""

from typing import Dict, Any, Tuple


def score_rapid_movement(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """Score based on low median outgoing delay (quick turnover)."""
    if thresholds is None:
        thresholds = {
            "delay_threshold_minutes": 10.0,   # below this is rapid
            "max_contribution": 20.0,
        }

    median_delay = features.get("median_outgoing_delay_minutes")
    if median_delay is None:
        # No outgoing transactions, so no rapid movement
        return 0.0, {"median_outgoing_delay_minutes": None}

    # Score: if delay is 0 -> max, if delay >= threshold -> 0, linear in between
    if median_delay <= 0:
        score = thresholds["max_contribution"]
    elif median_delay >= thresholds["delay_threshold_minutes"]:
        score = 0.0
    else:
        # linear interpolation
        score = thresholds["max_contribution"] * (1 - median_delay / thresholds["delay_threshold_minutes"])

    evidence = {
        "median_outgoing_delay_minutes": median_delay,
        "threshold_minutes": thresholds["delay_threshold_minutes"],
    }
    return score, evidence