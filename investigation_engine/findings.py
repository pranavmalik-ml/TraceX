from typing import List, Dict, Any
from uuid import uuid4

from .models import Path, Evidence, EvidenceChain, SuspiciousAccount, Finding, FindingType, RiskLevel


class FindingGenerator:
    """Generates structured findings from evidence"""
    
    def generate_findings(self, paths: List[Path], evidence: List[Evidence],
                         evidence_chains: List[EvidenceChain],
                         suspicious_accounts: List[SuspiciousAccount]) -> List[Finding]:
        """Generate findings from evidence"""
        findings = []
        
        for account in suspicious_accounts:
            if account.risk_score >= 60:
                findings.append(self._create_suspicious_account_finding(account))
        
        for chain in evidence_chains:
            for node in chain.nodes:
                if node.get("is_intermediary", False) and node.get("tainted_amount", 0) > 0:
                    findings.append(self._create_intermediary_finding(node, chain))
        
        split_paths = self._find_fund_splitting(paths)
        for split_path in split_paths:
            findings.append(self._create_fund_splitting_finding(split_path))
        
        consolidations = self._find_fund_consolidation(paths)
        for consolidation in consolidations:
            findings.append(self._create_fund_consolidation_finding(consolidation))
        
        for chain in evidence_chains:
            if len(chain.source_contributions) > 1:
                findings.append(self._create_multiple_sources_finding(chain))
        
        for chain in evidence_chains:
            for node in chain.nodes:
                if (node.get("incoming_amount", 0) > 0 and 
                    node.get("tainted_amount", 0) < node.get("incoming_amount", 0) and
                    node.get("tainted_amount", 0) > 0):
                    finding = self._create_clean_mixing_finding(node, chain)
                    if finding:
                        findings.append(finding)
        
        for path in paths:
            if path.tainted_amount > 0 and path.total_amount > 0:
                taint_ratio = path.tainted_amount / path.total_amount
                if taint_ratio > 0.8 and path.hops >= 2:
                    findings.append(self._create_high_risk_path_finding(path))
        
        if not findings and paths:
            findings.append(self._create_incomplete_data_finding())
        elif not findings:
            findings.append(self._create_no_paths_finding())
        
        return findings
    
    def _create_suspicious_account_finding(self, account: SuspiciousAccount) -> Finding:
        """Create a finding for a suspicious account"""
        confidence = min(0.95, account.risk_score / 100.0)
        
        description = (
            f"Account {account.account_id} is a high-priority suspicious account "
            f"with risk score {account.risk_score} ({account.risk_level.value}). "
            f"Reasons: {', '.join(account.reasons[:3])}. "
            f"Tainted exposure: {account.tainted_exposure:.2f}."
        )
        
        severity = "CRITICAL" if account.risk_level == RiskLevel.CRITICAL else "HIGH"
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.SUSPICIOUS_ACCOUNT,
            description=description,
            confidence=confidence,
            accounts=[account.account_id],
            evidence_links=account.evidence[:3],
            severity=severity
        )
    
    def _create_intermediary_finding(self, node: Dict[str, Any], 
                                    chain: EvidenceChain) -> Finding:
        """Create a finding for an intermediary account"""
        account_id = node.get("account")
        tainted = node.get("tainted_amount", 0)
        total = node.get("incoming_amount", 0)
        
        description = (
            f"Account {account_id} is an intermediary in the traced fund path "
            f"carrying {tainted:.2f} in tainted funds"
        )
        
        if total > 0:
            description += f" out of {total:.2f} total incoming funds"
        
        description += ". This account requires investigation."
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.INTERMEDIARY,
            description=description,
            confidence=0.85,
            accounts=[account_id],
            evidence_links=[],
            severity="HIGH"
        )
    
    def _find_fund_splitting(self, paths: List[Path]) -> List[Dict[str, Any]]:
        """Find fund splitting patterns"""
        splits = []
        source_map = {}
        
        for path in paths:
            if len(path.accounts) > 1:
                source = path.accounts[0]
                if source not in source_map:
                    source_map[source] = []
                source_map[source].append(path)
        
        for source, path_list in source_map.items():
            if len(path_list) > 1:
                total_split = sum(p.total_amount for p in path_list)
                splits.append({
                    "source": source,
                    "paths": path_list,
                    "total_split_amount": total_split,
                    "path_count": len(path_list)
                })
        
        return splits
    
    def _create_fund_splitting_finding(self, split_data: Dict[str, Any]) -> Finding:
        """Create a finding for fund splitting"""
        description = (
            f"Fund splitting detected from account {split_data['source']} "
            f"into {split_data['path_count']} separate paths totaling "
            f"{split_data['total_split_amount']:.2f}. This may indicate layering behavior."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.FUND_SPLITTING,
            description=description,
            confidence=0.80,
            accounts=[split_data['source']],
            evidence_links=[],
            severity="HIGH"
        )
    
    def _find_fund_consolidation(self, paths: List[Path]) -> List[Dict[str, Any]]:
        """Find fund consolidation patterns"""
        consolidations = []
        dest_map = {}
        
        for path in paths:
            if len(path.accounts) > 1:
                dest = path.accounts[-1]
                if dest not in dest_map:
                    dest_map[dest] = []
                dest_map[dest].append(path)
        
        for dest, path_list in dest_map.items():
            if len(path_list) > 1:
                total_consolidated = sum(p.total_amount for p in path_list)
                consolidations.append({
                    "destination": dest,
                    "paths": path_list,
                    "total_consolidated": total_consolidated,
                    "path_count": len(path_list)
                })
        
        return consolidations
    
    def _create_fund_consolidation_finding(self, consolidation: Dict[str, Any]) -> Finding:
        """Create a finding for fund consolidation"""
        description = (
            f"Fund consolidation detected at account {consolidation['destination']} "
            f"from {consolidation['path_count']} separate paths totaling "
            f"{consolidation['total_consolidated']:.2f}. This may indicate money mule activity."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.FUND_CONSOLIDATION,
            description=description,
            confidence=0.80,
            accounts=[consolidation['destination']],
            evidence_links=[],
            severity="HIGH"
        )
    
    def _create_multiple_sources_finding(self, chain: EvidenceChain) -> Finding:
        """Create a finding for multiple fraud sources"""
        sources = list(chain.source_contributions.keys())
        
        contrib_details = []
        for source, amount in chain.source_contributions.items():
            contrib_details.append(f"{source}: {amount:.2f}")
        
        description = (
            f"Multiple fraud sources detected at account {chain.source_account}. "
            f"{len(sources)} different fraud sources contributed funds: "
            f"{', '.join(contrib_details)}."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.MULTIPLE_SOURCES,
            description=description,
            confidence=0.90,
            accounts=[chain.source_account],
            evidence_links=[],
            severity="CRITICAL"
        )
    
    def _create_clean_mixing_finding(self, node: Dict[str, Any],
                                    chain: EvidenceChain) -> Finding:
        """Create a finding for clean and tainted money mixing"""
        account_id = node.get("account")
        tainted = node.get("tainted_amount", 0)
        total = node.get("incoming_amount", 0)
        clean = total - tainted
        
        if clean > 0 and tainted > 0:
            description = (
                f"Clean and tainted money mixed in account {account_id}. "
                f"Total incoming: {total:.2f}, Tainted: {tainted:.2f}, Clean: {clean:.2f}. "
                f"This may indicate layering or obfuscation attempts."
            )
            
            return Finding(
                finding_id=f"find_{uuid4().hex[:8]}",
                finding_type=FindingType.CLEAN_MIXING,
                description=description,
                confidence=0.85,
                accounts=[account_id],
                evidence_links=[],
                severity="HIGH"
            )
        return None
    
    def _create_high_risk_path_finding(self, path: Path) -> Finding:
        """Create a finding for high-risk paths"""
        taint_ratio = path.tainted_amount / path.total_amount if path.total_amount > 0 else 0
        
        description = (
            f"High-risk fund path detected: {' → '.join(path.accounts)}. "
            f"Tainted amount: {path.tainted_amount:.2f} ({taint_ratio:.1%} of total). "
            f"This path involves {path.hops} hops and multiple intermediaries."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.HIGH_RISK_PATH,
            description=description,
            confidence=0.90,
            accounts=path.accounts,
            evidence_links=[],
            severity="CRITICAL"
        )
    
    def _create_incomplete_data_finding(self) -> Finding:
        """Create a finding for incomplete data"""
        description = (
            "Investigation data is incomplete. Some transactions or accounts "
            "may be missing. Findings should be considered preliminary and "
            "require further investigation."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.INCOMPLETE_DATA,
            description=description,
            confidence=0.50,
            accounts=[],
            evidence_links=[],
            is_incomplete=True,
            severity="MEDIUM"
        )
    
    def _create_no_paths_finding(self) -> Finding:
        """Create a finding when no paths are found"""
        description = (
            "No transaction paths were found from the source account. "
            "This could indicate no outgoing transactions, data gaps, "
            "or the fraud source may not be connected to this account."
        )
        
        return Finding(
            finding_id=f"find_{uuid4().hex[:8]}",
            finding_type=FindingType.INCOMPLETE_DATA,
            description=description,
            confidence=0.60,
            accounts=[],
            evidence_links=[],
            is_incomplete=True,
            severity="LOW"
        )