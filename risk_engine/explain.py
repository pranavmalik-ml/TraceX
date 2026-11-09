"""Explanation generation for risk results."""

from typing import List, Dict, Any
from .models import RiskResult, SignalContribution


def explain_risk(result: RiskResult) -> List[Dict[str, Any]]:
    """
    Generate a list of reason dictionaries from the risk result.
    This is essentially the signals list in the output contract.
    """
    # The result already contains signals; we just format them.
    return [
        {
            "code": sig.code,
            "label": sig.label,
            "contribution": sig.contribution,
            "evidence": sig.evidence,
        }
        for sig in result.signals
    ]