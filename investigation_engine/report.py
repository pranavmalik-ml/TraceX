from typing import Dict, Any
from datetime import datetime

from .models import InvestigationCase, InvestigationResult, CaseStatus


class ReportGenerator:
    """Generates investigation reports"""
    
    def generate_report(self, case: InvestigationCase) -> InvestigationResult:
        """Generate a complete investigation report"""
        summary_parts = []
        
        summary_parts.append(f"Investigation Case {case.case_id}")
        summary_parts.append(f"Source Account: {case.source_account}")
        summary_parts.append(f"Fraud Amount: {case.fraud_amount}")
        summary_parts.append(f"Status: {case.status.value}")
        
        if case.error:
            summary_parts.append(f"Error: {case.error}")
        
        if case.paths:
            summary_parts.append(f"\nFound {len(case.paths)} transaction paths:")
            for i, path in enumerate(case.paths, 1):
                summary_parts.append(
                    f"  Path {i}: {' → '.join(path.accounts)} "
                    f"(Total: {path.total_amount}, Tainted: {path.tainted_amount})"
                )
        
        if case.suspicious_accounts:
            summary_parts.append(f"\nIdentified {len(case.suspicious_accounts)} suspicious accounts:")
            for account in case.suspicious_accounts[:5]:
                summary_parts.append(
                    f"  {account.account_id}: Score {account.risk_score} "
                    f"({account.risk_level.value}) - {', '.join(account.reasons[:2])}"
                )
            if len(case.suspicious_accounts) > 5:
                summary_parts.append(f"  ... and {len(case.suspicious_accounts) - 5} more")
        
        if case.findings:
            summary_parts.append(f"\nFindings:")
            for i, finding in enumerate(case.findings[:5], 1):
                summary_parts.append(f"  {i}. {finding.description}")
            if len(case.findings) > 5:
                summary_parts.append(f"  ... and {len(case.findings) - 5} more")
        
        if case.evidence_chains:
            summary_parts.append(f"\nTainted Amount Traced: {case.tainted_amount_traced}")
            
            for chain in case.evidence_chains:
                if chain.source_contributions:
                    summary_parts.append("  Source Contributions:")
                    for source, amount in chain.source_contributions.items():
                        summary_parts.append(f"    {source}: {amount}")
        
        investigation_summary = "\n".join(summary_parts)
        
        return InvestigationResult(
            case_id=case.case_id,
            status=case.status,
            fraud_amount=case.fraud_amount,
            tainted_amount_traced=case.tainted_amount_traced,
            paths=case.paths,
            suspicious_accounts=case.suspicious_accounts,
            findings=case.findings,
            evidence=case.evidence,
            evidence_chains=case.evidence_chains,
            source_contributions=case.source_contributions,
            investigation_summary=investigation_summary,
            error=case.error
        )