from typing import Dict, Any, Optional
from datetime import datetime

from .models import InvestigationCase, CaseStatus, InvestigationResult
from .case_manager import CaseManager
from .forward_trace import ForwardTracer
from .backward_trace import BackwardTracer
from .evidence import EvidenceCollector
from .correlation import EvidenceCorrelator
from .ranking import AccountRanker
from .findings import FindingGenerator
from .report import ReportGenerator


class InvestigationWorkflow:
    """Orchestrates the complete investigation workflow"""
    
    def __init__(self):
        self.case_manager = CaseManager()
        self.forward_tracer = ForwardTracer()
        self.backward_tracer = BackwardTracer()
        self.evidence_collector = EvidenceCollector()
        self.evidence_correlator = EvidenceCorrelator()
        self.account_ranker = AccountRanker()
        self.finding_generator = FindingGenerator()
        self.report_generator = ReportGenerator()
    
    def start_investigation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a complete investigation workflow
        
        Args:
            request: Investigation request
            
        Returns:
            Investigation result as dict
        """
        try:
            # 1. Create and validate case
            validation = self.case_manager.validate_case(request)
            if not validation["success"]:
                return {
                    "error": "Validation failed",
                    "messages": validation["messages"],
                    "status": "failed"
                }
            
            case = self.case_manager.create_case(request)
            case.status = CaseStatus.INVESTIGATING
            self.case_manager.update_case(case.case_id, {"status": CaseStatus.INVESTIGATING})
            
            # 2. Perform tracing based on direction
            if case.direction in ["forward", "both"]:
                forward_result = self.forward_tracer.trace_forward(
                    case.case_id,
                    case.source_account,
                    case.max_hops
                )
                case.paths.extend(forward_result.paths)
            
            if case.direction in ["backward", "both"]:
                backward_result = self.backward_tracer.trace_backward(
                    case.case_id,
                    case.source_account,
                    case.max_hops
                )
                case.paths.extend(backward_result.paths)
            
            # 3. Collect evidence
            evidence = self.evidence_collector.collect_all_evidence(
                case.case_id,
                case.paths,
                case.source_account,
                case.fraud_transaction_id
            )
            case.evidence = evidence
            
            # 4. Correlate evidence
            evidence_chains = self.evidence_correlator.correlate(
                case.paths,
                evidence,
                case.source_account,
                case.fraud_amount
            )
            case.evidence_chains = evidence_chains
            
            # 5. Rank suspicious accounts
            suspicious_accounts = self.account_ranker.rank_accounts(
                case.paths,
                evidence,
                case.fraud_amount
            )
            case.suspicious_accounts = suspicious_accounts
            
            # 6. Generate findings
            findings = self.finding_generator.generate_findings(
                case.paths,
                evidence,
                case.evidence_chains,
                case.suspicious_accounts
            )
            case.findings = findings
            
            # 7. Generate report
            result = self.report_generator.generate_report(case)
            
            # 8. Update case status
            case.status = CaseStatus.COMPLETED
            case.tainted_amount_traced = sum(p.tainted_amount for p in case.paths)
            self.case_manager.update_case(case.case_id, {
                "status": CaseStatus.COMPLETED,
                "tainted_amount_traced": case.tainted_amount_traced
            })
            
            return result.to_dict()
            
        except Exception as e:
            if 'case' in locals():
                case.status = CaseStatus.PARTIAL if case.paths else CaseStatus.FAILED
                case.error = str(e)
                self.case_manager.update_case(case.case_id, {
                    "status": case.status,
                    "error": str(e)
                })
                
                result = self.report_generator.generate_report(case)
                return result.to_dict()
            
            return {
                "error": str(e),
                "status": "failed",
                "case_id": request.get("case_id", "unknown")
            }