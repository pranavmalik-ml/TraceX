from typing import List, Dict, Any
from uuid import uuid4

from .models import Path, Evidence, EvidenceChain


class EvidenceCorrelator:
    """Correlates evidence from different sources"""
    
    def __init__(self):
        self.taint_adapter = None
    
    def correlate(self, paths: List[Path], evidence: List[Evidence],
                 source_account: str, fraud_amount: float) -> List[EvidenceChain]:
        """Correlate evidence into evidence chains"""
        if not paths:
            return []
        
        chains = []
        path_evidence_map = self._group_evidence_by_path(paths, evidence)
        
        for path in paths:
            path_key = "-".join(path.accounts)
            path_evidences = path_evidence_map.get(path_key, [])
            
            chain_nodes = self._build_chain_nodes(path, path_evidences)
            total_tainted = sum(node.get("tainted_amount", 0) for node in chain_nodes if node.get("tainted_amount"))
            source_contributions = self._aggregate_source_contributions(path_evidences)
            
            if not source_contributions and path.source_contributions:
                source_contributions = path.source_contributions
            
            chains.append(EvidenceChain(
                source_account=source_account,
                fraud_amount=fraud_amount,
                nodes=chain_nodes,
                total_tainted_traced=total_tainted if total_tainted > 0 else path.tainted_amount,
                source_contributions=source_contributions,
                path_id=path_key
            ))
        
        return chains
    
    def _group_evidence_by_path(self, paths: List[Path], 
                               evidence: List[Evidence]) -> Dict[str, List[Evidence]]:
        """Group evidence by path using path keys"""
        path_evidence = {}
        
        for path in paths:
            path_key = "-".join(path.accounts)
            path_evidence[path_key] = []
        
        for ev in evidence:
            if ev.evidence_type == "graph":
                path_key = ev.data.get("path_key", "")
                if path_key in path_evidence:
                    path_evidence[path_key].append(ev)
            elif ev.evidence_type in ["taint", "transaction"]:
                for path in paths:
                    if ev.data.get("transaction_id") in path.transactions:
                        path_key = "-".join(path.accounts)
                        if path_key in path_evidence:
                            path_evidence[path_key].append(ev)
                            break
            elif ev.evidence_type == "risk":
                account_id = ev.data.get("account_id")
                for path in paths:
                    if account_id in path.accounts:
                        path_key = "-".join(path.accounts)
                        if path_key in path_evidence:
                            path_evidence[path_key].append(ev)
                            break
        
        return path_evidence
    
    def _build_chain_nodes(self, path: Path, evidences: List[Evidence]) -> List[Dict[str, Any]]:
        """Build nodes for an evidence chain"""
        nodes = []
        
        for i, account_id in enumerate(path.accounts):
            node = {
                "account": account_id,
                "position": i,
                "is_source": i == 0,
                "is_intermediary": 0 < i < len(path.accounts) - 1,
                "is_destination": i == len(path.accounts) - 1
            }
            
            if i > 0:
                prev_tx = None
                for ev in evidences:
                    if (ev.evidence_type == "transaction" and 
                        ev.data.get("source_account") == path.accounts[i-1] and 
                        ev.data.get("destination_account") == account_id):
                        prev_tx = ev
                        break
                
                if prev_tx:
                    node["incoming_amount"] = prev_tx.data.get("amount", 0)
                    node["transaction_id"] = prev_tx.evidence_id
            
            tainted = 0
            sources = {}
            clean_amount = 0
            
            for ev in evidences:
                if ev.evidence_type == "taint":
                    if i > 0 and node.get("transaction_id") and ev.data.get("transaction_id") in path.transactions:
                        tainted = ev.data.get("tainted_amount", 0)
                        sources = ev.data.get("sources", {})
                        clean_amount = ev.data.get("clean_amount", 0)
                    elif i == 0 and ev.data.get("fraud_source"):
                        tainted = ev.data.get("tainted_amount", 0)
                        sources = ev.data.get("sources", {})
            
            if tainted == 0 and i > 0 and path.tainted_amount > 0:
                tainted = path.tainted_amount * (path.total_amount / len(path.accounts) if path.total_amount > 0 else 0)
            
            if tainted > 0:
                node["tainted_amount"] = tainted
                if sources:
                    node["source_contributions"] = sources
                if clean_amount > 0:
                    node["clean_amount"] = clean_amount
            
            for ev in evidences:
                if ev.evidence_type == "risk" and ev.data.get("account_id") == account_id:
                    node["risk_score"] = ev.data.get("score", 0)
                    node["risk_level"] = ev.data.get("level", "UNKNOWN")
                    node["risk_reasons"] = ev.data.get("reasons", [])
                    break
            
            if account_id in path.risk_scores and "risk_score" not in node:
                node["risk_score"] = path.risk_scores[account_id]
            
            nodes.append(node)
        
        return nodes
    
    def _aggregate_source_contributions(self, evidences: List[Evidence]) -> Dict[str, float]:
        """Aggregate source contributions from evidence"""
        contributions = {}
        
        for ev in evidences:
            if ev.evidence_type == "taint":
                sources = ev.data.get("sources", {})
                for source, amount in sources.items():
                    contributions[source] = contributions.get(source, 0) + amount
        
        return contributions