from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import Path, InvestigationResult, CaseStatus
from .adapters import DataAdapter, GraphAdapter, TaintAdapter


class BackwardTracer:
    """Traces funds backward from a target"""
    
    def __init__(self):
        self.data_adapter = DataAdapter()
        self.graph_adapter = GraphAdapter()
        self.taint_adapter = TaintAdapter()
    
    def trace_backward(self, case_id: str, target_account: str, max_hops: int,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> InvestigationResult:
        """
        Trace funds backward from the target account
        
        Args:
            case_id: Case identifier
            target_account: Target account ID
            max_hops: Maximum number of hops to trace
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            InvestigationResult with backward traces
        """
        paths = []
        
        try:
            graph_paths = self.graph_adapter.trace_backward(
                target_account,
                max_hops,
                start_time,
                end_time
            )
            
            for graph_path in graph_paths:
                path = Path(
                    accounts=graph_path["path"],
                    total_amount=graph_path.get("amount", 0),
                    tainted_amount=graph_path.get("tainted_amount", 0),
                    hops=graph_path.get("hops", len(graph_path["path"]) - 1),
                    transactions=graph_path.get("transactions", [])
                )
                
                taint_info = self._get_path_taint(path)
                path.tainted_amount = taint_info.get("tainted_amount", path.tainted_amount)
                path.source_contributions = taint_info.get("source_contributions", {})
                
                paths.append(path)
        
        except NotImplementedError:
            pass
        
        total_tainted = sum(p.tainted_amount for p in paths)
        
        return InvestigationResult(
            case_id=case_id,
            status=CaseStatus.COMPLETED,
            fraud_amount=self._get_fraud_amount(target_account),
            tainted_amount_traced=total_tainted,
            paths=paths,
            suspicious_accounts=[],
            findings=[],
            evidence=[],
            evidence_chains=[],
            source_contributions=[],
            investigation_summary=f"Backward tracing completed from {target_account}, found {len(paths)} paths"
        )
    
    def _get_path_taint(self, path: Path) -> Dict[str, Any]:
        """Get taint information for a path"""
        if not path.transactions:
            return {"tainted_amount": 0, "source_contributions": {}}
        
        total_tainted = 0
        source_contributions = {}
        
        try:
            for tx_id in path.transactions:
                taint_info = self.taint_adapter.get_taint_flow(tx_id)
                if taint_info:
                    total_tainted += taint_info.get("tainted_amount", 0)
                    for source, amount in taint_info.get("sources", {}).items():
                        source_contributions[source] = source_contributions.get(source, 0) + amount
        except NotImplementedError:
            pass
        
        return {
            "tainted_amount": total_tainted,
            "source_contributions": source_contributions
        }
    
    def _get_fraud_amount(self, target_account: str) -> float:
        """Get the fraud amount for a target account"""
        try:
            account = self.data_adapter.get_account(target_account)
            if account:
                return account.get("fraud_amount", 0)
        except NotImplementedError:
            pass
        return 0