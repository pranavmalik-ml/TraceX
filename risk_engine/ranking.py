"""Rank entities by risk score."""

from typing import List
from .models import RiskResult


def rank_entities(results: List[RiskResult]) -> List[RiskResult]:
    """Return results sorted by risk_score descending."""
    return sorted(results, key=lambda r: r.risk_score, reverse=True)