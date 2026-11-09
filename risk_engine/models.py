"""Data models for risk engine inputs and outputs."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Evidence:
    """Evidence for a signal contribution."""
    # Allow any fields, but we can add some common ones
    value: Any = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalContribution:
    """A single signal's contribution to the risk score."""
    code: str
    label: str
    contribution: float
    evidence: Dict[str, Any]  # key-value pairs for evidence


@dataclass
class RiskResult:
    """Final risk assessment for an entity."""
    entity_id: str
    entity_type: str  # "account" or "transaction"
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    signals: List[SignalContribution]
    model_version: str = "rules-v1"


# --- Input context types ---

@dataclass
class Transaction:
    """A single transaction."""
    tx_id: str
    from_account: str
    to_account: str
    amount: float
    timestamp: datetime
    # optional metadata
    taint_score: Optional[float] = None  # 0..1 fraction of tainted funds
    taint_sources: Optional[List[str]] = None  # list of fraud source IDs


@dataclass
class TaintData:
    """Taint information for a transaction."""
    tx_id: str
    tainted_amount: float
    taint_sources: List[str]  # fraud source IDs


@dataclass
class GraphData:
    """Graph data for counterparty relationships (optional)."""
    # not used in initial implementation, but placeholder
    pass


@dataclass
class Context:
    """All input data needed for feature extraction."""
    transactions: List[Transaction]
    taint_data: Dict[str, TaintData]  # tx_id -> TaintData
    graph_data: Optional[GraphData] = None