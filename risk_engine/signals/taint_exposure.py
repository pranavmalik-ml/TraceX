"""Taint exposure signal: proportion/amount of tainted funds handled."""

from typing import Dict, Any, Tuple


def score_taint_exposure(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """Score based on tainted amount and proportion."""
    if thresholds is None:
        thresholds = {
            "taint_proportion_high": 0.5,   # 50% tainted
            "taint_amount_high": 10000.0,   # high tainted amount
            "max_contribution": 20.0,
        }

    prop_in = features.get("proportion_tainted_in", 0.0)
    prop_out = features.get("proportion_tainted_out", 0.0)
    total_tainted = features.get("total_tainted_amount", 0.0)

    # Score based on max proportion or amount
    # We'll compute score from proportion and amount, then combine (max or sum capped)
    score_prop = 0.0
    if prop_in > 0 or prop_out > 0:
        max_prop = max(prop_in, prop_out)
        if max_prop >= thresholds["taint_proportion_high"]:
            score_prop = thresholds["max_contribution"] * 0.7  # weight 70%
        else:
            score_prop = (max_prop / thresholds["taint_proportion_high"]) * thresholds["max_contribution"] * 0.7

    score_amount = 0.0
    if total_tainted > 0:
        if total_tainted >= thresholds["taint_amount_high"]:
            score_amount = thresholds["max_contribution"] * 0.3
        else:
            score_amount = (total_tainted / thresholds["taint_amount_high"]) * thresholds["max_contribution"] * 0.3

    total_score = min(score_prop + score_amount, thresholds["max_contribution"])

    evidence = {
        "proportion_tainted_in": prop_in,
        "proportion_tainted_out": prop_out,
        "total_tainted_amount": total_tainted,
        "score_proportion": score_prop,
        "score_amount": score_amount,
    }
    return total_score, evidence