"""Transaction velocity signal."""

from typing import Dict, Any, Tuple


def score_velocity(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Score based on transaction velocity (transactions per hour).

    Uses the 1h and 24h velocity. Higher velocity => higher score.
    """
    if thresholds is None:
        thresholds = {
            "velocity_1h_high": 10.0,   # transactions per hour
            "velocity_24h_high": 5.0,
            "max_contribution": 15.0,
        }

    vel_1h = features.get("velocity_1h", 0.0)
    vel_24h = features.get("velocity_24h", 0.0)

    # Score: linear interpolation between threshold and max
    def score_for_velocity(vel, threshold_high, max_score):
        if vel <= 0:
            return 0.0
        if vel >= threshold_high:
            return max_score
        else:
            return (vel / threshold_high) * max_score

    score_1h = score_for_velocity(vel_1h, thresholds["velocity_1h_high"], thresholds["max_contribution"] * 0.6)
    score_24h = score_for_velocity(vel_24h, thresholds["velocity_24h_high"], thresholds["max_contribution"] * 0.4)

    # Combine: sum and cap
    total = score_1h + score_24h
    # Cap to max_contribution
    total = min(total, thresholds["max_contribution"])

    evidence = {
        "velocity_1h": vel_1h,
        "velocity_24h": vel_24h,
        "score_1h": score_1h,
        "score_24h": score_24h,
    }
    return total, evidence
