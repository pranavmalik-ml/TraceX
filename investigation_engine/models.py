from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from uuid import uuid4


class CaseStatus(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class RiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class FindingType(Enum):
    SUSPICIOUS_ACCOUNT = "suspicious_account"
    INTERMEDIARY = "intermediary"
    MULE_ACCOUNT = "mule_account"
    FUND_SPLITTING = "fund_splitting"
    FUND_CONSOLIDATION = "fund_consolidation"
    LAYERING = "layering"
    CLEAN_MIXING = "clean_mixing"
    MULTIPLE_SOURCES = "multiple_sources"
    INCOMPLETE_DATA = "incomplete_data"
    HIGH_RISK_PATH = "high_risk_path"


@dataclass
class Evidence:
    """Evidence collected from various sources"""
    evidence_id: str
    evidence_type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Path:
    """A path in the transaction graph"""
    accounts: List[str]
    total_amount: float
    tainted_amount: float
    hops: int
    transactions: List[str] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    source_contributions: Dict[str, float] = field(default_factory=dict)
    risk_scores: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accounts": self.accounts,
            "total_amount": self.total_amount,
            "tainted_amount": self.tainted_amount,
            "hops": self.hops,
            "transactions": self.transactions,
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "source_contributions": self.source_contributions,
            "risk_scores": self.risk_scores
        }


@dataclass
class SuspiciousAccount:
    """An account identified as potentially suspicious"""
    account_id: str
    risk_score: int
    risk_level: RiskLevel
    reasons: List[str]
    evidence: List[Evidence] = field(default_factory=list)
    connected_paths: List[str] = field(default_factory=list)
    tainted_exposure: float = 0.0
    total_volume: float = 0.0
    path_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "reasons": self.reasons,
            "evidence": [e.to_dict() for e in self.evidence],
            "connected_paths": self.connected_paths,
            "tainted_exposure": self.tainted_exposure,
            "total_volume": self.total_volume,
            "path_count": self.path_count
        }


@dataclass
class Finding:
    """A structured finding from the investigation"""
    finding_id: str
    finding_type: FindingType
    description: str
    confidence: float
    accounts: List[str]
    evidence_links: List[Evidence]
    is_incomplete: bool = False
    severity: str = "MEDIUM"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "accounts": self.accounts,
            "evidence_links": [e.to_dict() for e in self.evidence_links],
            "is_incomplete": self.is_incomplete,
            "severity": self.severity
        }


@dataclass
class EvidenceChain:
    """A chain of correlated evidence"""
    source_account: str
    fraud_amount: float
    nodes: List[Dict[str, Any]]
    total_tainted_traced: float
    source_contributions: Dict[str, float] = field(default_factory=dict)
    path_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_account": self.source_account,
            "fraud_amount": self.fraud_amount,
            "nodes": self.nodes,
            "total_tainted_traced": self.total_tainted_traced,
            "source_contributions": self.source_contributions,
            "path_id": self.path_id
        }


@dataclass
class SourceContribution:
    """Contribution from a specific fraud source"""
    source_id: str
    amount: float
    paths: List[Path]
    accounts_reached: Set[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "amount": self.amount,
            "paths": [p.to_dict() for p in self.paths],
            "accounts_reached": list(self.accounts_reached)
        }


@dataclass
class InvestigationCase:
    """An investigation case"""
    case_id: str
    source_account: str
    fraud_transaction_id: str
    fraud_amount: float
    direction: str
    max_hops: int
    start_time: datetime
    end_time: datetime
    status: CaseStatus = CaseStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tainted_amount_traced: float = 0.0
    paths: List[Path] = field(default_factory=list)
    suspicious_accounts: List[SuspiciousAccount] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    evidence_chains: List[EvidenceChain] = field(default_factory=list)
    source_contributions: List[SourceContribution] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "source_account": self.source_account,
            "fraud_transaction_id": self.fraud_transaction_id,
            "fraud_amount": self.fraud_amount,
            "direction": self.direction,
            "max_hops": self.max_hops,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tainted_amount_traced": self.tainted_amount_traced,
            "paths": [p.to_dict() for p in self.paths],
            "suspicious_accounts": [sa.to_dict() for sa in self.suspicious_accounts],
            "findings": [f.to_dict() for f in self.findings],
            "evidence": [e.to_dict() for e in self.evidence],
            "evidence_chains": [ec.to_dict() for ec in self.evidence_chains],
            "source_contributions": [sc.to_dict() for sc in self.source_contributions],
            "error": self.error
        }


@dataclass
class InvestigationResult:
    """Complete investigation result"""
    case_id: str
    status: CaseStatus
    fraud_amount: float
    tainted_amount_traced: float
    paths: List[Path]
    suspicious_accounts: List[SuspiciousAccount]
    findings: List[Finding]
    evidence: List[Evidence]
    evidence_chains: List[EvidenceChain]
    source_contributions: List[SourceContribution]
    investigation_summary: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "status": self.status.value,
            "fraud_amount": self.fraud_amount,
            "tainted_amount_traced": self.tainted_amount_traced,
            "paths": [p.to_dict() for p in self.paths],
            "suspicious_accounts": [sa.to_dict() for sa in self.suspicious_accounts],
            "findings": [f.to_dict() for f in self.findings],
            "evidence": [e.to_dict() for e in self.evidence],
            "evidence_chains": [ec.to_dict() for ec in self.evidence_chains],
            "source_contributions": [sc.to_dict() for sc in self.source_contributions],
            "investigation_summary": self.investigation_summary,
            "error": self.error
        }