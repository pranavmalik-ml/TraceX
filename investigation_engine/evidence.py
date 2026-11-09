from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

from .models import Path, Evidence
from .adapters import DataAdapter, GraphAdapter, TaintAdapter, RiskAdapter


class EvidenceCollector:
    """Collects evidence from various sources"""
    
    def __init__(self):
        self.data_adapter = DataAdapter()
        self.graph_adapter = GraphAdapter()
        self.taint_adapter = TaintAdapter()
        self.risk_adapter = RiskAdapter()
    
    def collect_all_evidence(self, case_id: str, paths: List[Path],
                           source_account: str, fraud_transaction_id: str) -> List[Evidence]:
        """Collect all evidence for an investigation"""
        evidence = []
        
        graph_evidence = self.collect_graph_evidence(case_id, paths)
        evidence.extend(graph_evidence)
        
        taint_evidence = self.collect_taint_evidence(case_id, paths, fraud_transaction_id)
        evidence.extend(taint_evidence)
        
        risk_evidence = self.collect_risk_evidence(case_id, paths)
        evidence.extend(risk_evidence)
        
        context_evidence = self.collect_transaction_context(case_id, paths)
        evidence.extend(context_evidence)
        
        return evidence
    
    def collect_graph_evidence(self, case_id: str, paths: List[Path]) -> List[Evidence]:
        """Collect evidence from graph paths"""
        evidence = []
        
        for path in paths:
            evidence.append(Evidence(
                evidence_id=f"graph_{uuid4().hex[:8]}",
                evidence_type="graph",
                source="GraphAdapter",
                data={
                    "case_id": case_id,
                    "path": path.accounts,
                    "hops": path.hops,
                    "total_amount": path.total_amount,
                    "transactions": path.transactions,
                    "path_key": "-".join(path.accounts)
                }
            ))
        
        return evidence
    
    def collect_taint_evidence(self, case_id: str, paths: List[Path],
                              fraud_transaction_id: str) -> List[Evidence]:
        """Collect evidence from taint analysis"""
        evidence = []
        processed_txns = set()
        
        for path in paths:
            for transaction_id in path.transactions:
                if transaction_id not in processed_txns:
                    processed_txns.add(transaction_id)
                    try:
                        taint_info = self.taint_adapter.get_taint_flow(transaction_id)
                        if taint_info:
                            evidence.append(Evidence(
                                evidence_id=f"taint_{uuid4().hex[:8]}",
                                evidence_type="taint",
                                source="TaintAdapter",
                                data={
                                    "case_id": case_id,
                                    "transaction_id": transaction_id,
                                    "tainted_amount": taint_info.get("tainted_amount", 0),
                                    "sources": taint_info.get("sources", {}),
                                    "clean_amount": taint_info.get("clean_amount", 0),
                                    "path_key": "-".join(path.accounts) if path.accounts else ""
                                }
                            ))
                    except NotImplementedError:
                        pass
        
        try:
            if fraud_transaction_id not in processed_txns:
                fraud_taint = self.taint_adapter.get_taint_flow(fraud_transaction_id)
                if fraud_taint:
                    evidence.append(Evidence(
                        evidence_id=f"taint_fraud_{uuid4().hex[:8]}",
                        evidence_type="taint",
                        source="TaintAdapter",
                        data={
                            "case_id": case_id,
                            "transaction_id": fraud_transaction_id,
                            "fraud_source": True,
                            "tainted_amount": fraud_taint.get("tainted_amount", 0),
                            "sources": fraud_taint.get("sources", {})
                        }
                    ))
        except NotImplementedError:
            pass
        
        return evidence
    
    def collect_risk_evidence(self, case_id: str, paths: List[Path]) -> List[Evidence]:
        """Collect evidence from risk scoring"""
        evidence = []
        accounts_seen = set()
        
        for path in paths:
            for account_id in path.accounts:
                if account_id not in accounts_seen:
                    accounts_seen.add(account_id)
                    try:
                        risk_info = self.risk_adapter.get_risk(account_id)
                        if risk_info:
                            evidence.append(Evidence(
                                evidence_id=f"risk_{uuid4().hex[:8]}",
                                evidence_type="risk",
                                source="RiskAdapter",
                                data={
                                    "case_id": case_id,
                                    "account_id": account_id,
                                    "score": risk_info.get("score", 0),
                                    "level": risk_info.get("level", "UNKNOWN"),
                                    "reasons": risk_info.get("reasons", [])
                                }
                            ))
                    except NotImplementedError:
                        pass
        
        return evidence
    
    def collect_transaction_context(self, case_id: str, paths: List[Path]) -> List[Evidence]:
        """Collect transaction context evidence"""
        evidence = []
        transactions_seen = set()
        
        for path in paths:
            for transaction_id in path.transactions:
                if transaction_id not in transactions_seen:
                    transactions_seen.add(transaction_id)
                    try:
                        transaction = self.data_adapter.get_transaction(transaction_id)
                        if transaction:
                            evidence.append(Evidence(
                                evidence_id=f"txn_{uuid4().hex[:8]}",
                                evidence_type="transaction",
                                source="DataAdapter",
                                data={
                                    "case_id": case_id,
                                    "transaction_id": transaction_id,
                                    "source_account": transaction.get("source_account"),
                                    "destination_account": transaction.get("destination_account"),
                                    "amount": transaction.get("amount", 0),
                                    "timestamp": transaction.get("timestamp"),
                                    "type": transaction.get("type", "unknown")
                                }
                            ))
                    except NotImplementedError:
                        pass
        
        return evidence