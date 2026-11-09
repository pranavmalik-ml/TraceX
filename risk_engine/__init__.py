"""
TraceX Risk Engine - Rule-based risk scoring for accounts and transactions.
"""

from unittest import result

from .models import RiskResult, SignalContribution, Evidence
from .scoring import calculate_risk
from .explain import explain_risk
from .ranking import rank_entities
from .features import extract_features
from .adapters import TaintAdapter, GraphAdapter
from .serialise import serialize_risk_result, to_json

__all__ = [
    "RiskResult",
    "SignalContribution",
    "Evidence",
    "calculate_risk",
    "explain_risk",
    "rank_entities",
    "extract_features",
    "TaintAdapter",
    "GraphAdapter",
    "serialize_risk_result",
    "to_json"
]