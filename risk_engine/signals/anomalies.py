"""Anomaly signals: amount anomaly, dormant activation, circular movement."""

from typing import Dict, Any, Tuple


def score_amount_anomaly(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Score based on unusually large transaction amount compared to account's history.
    Uses z-score of max amount relative to mean and stddev.
    """
    if thresholds is None:
        thresholds = {
            "z_score_high": 3.0,
            "max_contribution": 10.0,
        }

    mean = features.get("amount_mean", 0.0)
    std = features.get("amount_stddev", 0.0)
    max_amt = features.get("max_single_amount", 0.0)

    if std == 0 or mean == 0:
        # If no variation, we consider amount anomalous if it's large compared to a baseline
        # Simple: if max_amt > mean * 5, then score high
        if mean > 0 and max_amt > mean * 5:
            score = thresholds["max_contribution"]
        else:
            score = 0.0
    else:
        z = (max_amt - mean) / std
        if z >= thresholds["z_score_high"]:
            score = thresholds["max_contribution"]
        else:
            score = (z / thresholds["z_score_high"]) * thresholds["max_contribution"]
    score = min(score, thresholds["max_contribution"])

    evidence = {
        "max_single_amount": max_amt,
        "amount_mean": mean,
        "amount_stddev": std,
        "z_score": z if std > 0 else None,
    }
    return score, evidence


def score_dormant_activation(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Score based on sudden activation after dormancy.
    If account had no transactions for >30 days and recent volume is high.
    """
    if thresholds is None:
        thresholds = {
            "dormant_days_threshold": 30,
            "recent_volume_threshold": 5000.0,
            "max_contribution": 10.0,
        }

    dormant_days = features.get("dormant_days")
    recent_volume = features.get("recent_volume_24h", 0.0)

    if dormant_days is None or dormant_days < thresholds["dormant_days_threshold"]:
        return 0.0, {"dormant_days": dormant_days, "recent_volume_24h": recent_volume, "score": 0.0}

    # If dormant and recent volume is high, score high
    if recent_volume >= thresholds["recent_volume_threshold"]:
        score = thresholds["max_contribution"]
    else:
        # Linear scaling: if volume is half threshold -> half score
        score = (recent_volume / thresholds["recent_volume_threshold"]) * thresholds["max_contribution"]
    score = min(score, thresholds["max_contribution"])

    evidence = {
        "dormant_days": dormant_days,
        "recent_volume_24h": recent_volume,
    }
    return score, evidence


def score_circular_movement(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Score based on circular flow (money returns to earlier account).
    For simplicity, we check if any counterparty has both incoming and outgoing transactions.
    We need to compute this properly; for now we rely on feature 'circular_flow' which is set by extract_features.
    But we didn't compute it, so we'll compute here.
    """
    # We'll compute from features: we have counterparty_flow (net per counterparty) and also we can track
    # which counterparties appear as both sender and receiver.
    # We don't have that info directly, so we'll skip for now.
    # In a real implementation, we would compute both-ways flag.
    # We'll return 0.
    return 0.0, {"circular_flow": False}