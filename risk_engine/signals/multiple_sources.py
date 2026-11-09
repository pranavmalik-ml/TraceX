"""Multiple fraud sources signal."""

from typing import Dict, Any, Tuple


def score_multiple_sources(features: Dict[str, Any], thresholds: Dict[str, float] = None) -> Tuple[float, Dict[str, Any]]:
    """Score based on number of distinct taint sources."""
    if thresholds is None:
        thresholds = {
            "sources_high": 2,   # 2 or more sources
            "max_contribution": 10.0,
        }

    num_sources = features.get("number_of_taint_sources", 0)
    score = 0.0
    if num_sources > 0:
        if num_sources >= thresholds["sources_high"]:
            score = thresholds["max_contribution"]
        else:
            score = (num_sources / thresholds["sources_high"]) * thresholds["max_contribution"]
    score = min(score, thresholds["max_contribution"])

    evidence = {
        "number_of_taint_sources": num_sources,
        "threshold_high": thresholds["sources_high"],
    }
    return score, evidence