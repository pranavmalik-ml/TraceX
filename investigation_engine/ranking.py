from typing import List, Dict, Any
from .models import Path, Evidence, SuspiciousAccount, RiskLevel


class AccountRanker:
    """Ranks accounts based on evidence"""
    
    def rank_accounts(self, paths: List[Path], evidence: List[Evidence],
                     fraud_amount: float) -> List[SuspiciousAccount]:
        """Rank accounts by suspiciousness"""
        account_evidence = self._group_evidence_by_account(paths, evidence)
        ranked_accounts = []
        
        for account_id, evs in account_evidence.items():
            risk_score = self._calculate_risk_score(account_id, evs)
            risk_level = self._get_risk_level(risk_score)
            reasons = self._get_risk_reasons(evs)
            tainted_exposure = self._calculate_tainted_exposure(evs)
            connected_paths = self._get_connected_paths(account_id, paths)
            
            suspicious_account = SuspiciousAccount(
                account_id=account_id,
                risk_score=risk_score,
                risk_level=risk_level,
                reasons=reasons,
                evidence=evs,
                connected_paths=connected_paths,
                tainted_exposure=tainted_exposure,
                total_volume=self._calculate_total_volume(evs),
                path_count=len(connected_paths)
            )
            
            ranked_accounts.append(suspicious_account)
        
        ranked_accounts.sort(key=lambda x: x.risk_score, reverse=True)
        return ranked_accounts
    
    def _group_evidence_by_account(self, paths: List[Path],
                                  evidence: List[Evidence]) -> Dict[str, List[Evidence]]:
        """Group evidence by account"""
        account_evidence = {}
        
        accounts = set()
        for path in paths:
            accounts.update(path.accounts)
        
        for account_id in accounts:
            account_evidence[account_id] = []
        
        for ev in evidence:
            if ev.evidence_type == "risk":
                account_id = ev.data.get("account_id")
                if account_id in account_evidence:
                    account_evidence[account_id].append(ev)
            elif ev.evidence_type == "taint":
                path = ev.data.get("path", [])
                for account_id in path:
                    if account_id in account_evidence:
                        account_evidence[account_id].append(ev)
            elif ev.evidence_type == "transaction":
                source = ev.data.get("source_account")
                destination = ev.data.get("destination_account")
                if source in account_evidence:
                    account_evidence[source].append(ev)
                if destination in account_evidence:
                    account_evidence[destination].append(ev)
        
        return account_evidence
    
    def _calculate_risk_score(self, account_id: str, evidences: List[Evidence]) -> int:
        """Calculate risk score for an account"""
        risk_score = 0
        
        for ev in evidences:
            if ev.evidence_type == "risk":
                risk_score = ev.data.get("score", 0)
                break
        
        tainted = self._calculate_tainted_exposure(evidences)
        if tainted > 0:
            risk_score = min(100, risk_score + 10)
        
        path_count = len(self._get_connected_paths(account_id, []))
        if path_count > 3:
            risk_score = min(100, risk_score + 5)
        
        return min(100, risk_score)
    
    def _get_risk_level(self, score: int) -> RiskLevel:
        """Get risk level from score"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        elif score > 0:
            return RiskLevel.LOW
        else:
            return RiskLevel.UNKNOWN
    
    def _get_risk_reasons(self, evidences: List[Evidence]) -> List[str]:
        """Get risk reasons from evidence"""
        reasons = []
        for ev in evidences:
            if ev.evidence_type == "risk":
                reasons.extend(ev.data.get("reasons", []))
            elif ev.evidence_type == "transaction":
                if ev.data.get("amount", 0) > 100000:
                    reasons.append("large_transaction_amount")
            elif ev.evidence_type == "taint":
                if ev.data.get("tainted_amount", 0) > 0:
                    reasons.append("receiving_tainted_funds")
        
        return list(set(reasons))
    
    def _calculate_tainted_exposure(self, evidences: List[Evidence]) -> float:
        """Calculate tainted exposure for an account"""
        total_tainted = 0
        for ev in evidences:
            if ev.evidence_type == "taint":
                total_tainted += ev.data.get("tainted_amount", 0)
        return total_tainted
    
    def _calculate_total_volume(self, evidences: List[Evidence]) -> float:
        """Calculate total transaction volume for an account"""
        total_volume = 0
        for ev in evidences:
            if ev.evidence_type == "transaction":
                total_volume += ev.data.get("amount", 0)
        return total_volume
    
    def _get_connected_paths(self, account_id: str, paths: List[Path]) -> List[str]:
        """Get paths connected to an account"""
        connected = []
        for path in paths:
            if account_id in path.accounts:
                connected.append("-".join(path.accounts))
        return connected