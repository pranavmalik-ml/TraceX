from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from .models import InvestigationCase, CaseStatus
from .adapters import DataAdapter, GraphAdapter, TaintAdapter, RiskAdapter


class CaseManager:
    """Manages investigation cases"""
    
    def __init__(self):
        self.cases: Dict[str, InvestigationCase] = {}
        self.data_adapter = DataAdapter()
        self.graph_adapter = GraphAdapter()
        self.taint_adapter = TaintAdapter()
        self.risk_adapter = RiskAdapter()
    
    def create_case(self, request: Dict[str, Any]) -> InvestigationCase:
        """
        Create a new investigation case
        
        Args:
            request: Case creation request with required fields
            
        Returns:
            InvestigationCase object
        """
        required_fields = ["source_account", "fraud_transaction_id", "fraud_amount"]
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
        
        case = InvestigationCase(
            case_id=request.get("case_id", f"CASE-{uuid4().hex[:8].upper()}"),
            source_account=request["source_account"],
            fraud_transaction_id=request["fraud_transaction_id"],
            fraud_amount=request["fraud_amount"],
            direction=request.get("direction", "forward"),
            max_hops=request.get("max_hops", 5),
            start_time=datetime.fromisoformat(request.get("start_time", datetime.now().isoformat())),
            end_time=datetime.fromisoformat(request.get("end_time", datetime.now().isoformat())),
            status=CaseStatus.CREATED
        )
        
        self.cases[case.case_id] = case
        return case
    
    def validate_case(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a case creation request
        
        Returns:
            Validation result with success flag and messages
        """
        validation_result = {
            "success": True,
            "messages": []
        }
        
        required_fields = ["source_account", "fraud_transaction_id", "fraud_amount"]
        for field in required_fields:
            if field not in request:
                validation_result["success"] = False
                validation_result["messages"].append(f"Missing required field: {field}")
        
        if "fraud_amount" in request and request["fraud_amount"] <= 0:
            validation_result["success"] = False
            validation_result["messages"].append("fraud_amount must be positive")
        
        if "source_account" in request:
            try:
                account = self.data_adapter.get_account(request["source_account"])
                if not account:
                    validation_result["success"] = False
                    validation_result["messages"].append(f"Source account {request['source_account']} not found")
            except NotImplementedError:
                pass
        
        if "fraud_transaction_id" in request:
            try:
                transaction = self.data_adapter.get_transaction(request["fraud_transaction_id"])
                if not transaction:
                    validation_result["success"] = False
                    validation_result["messages"].append(f"Transaction {request['fraud_transaction_id']} not found")
            except NotImplementedError:
                pass
        
        return validation_result
    
    def get_case(self, case_id: str) -> Optional[InvestigationCase]:
        """Get a case by ID"""
        return self.cases.get(case_id)
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[InvestigationCase]:
        """Update a case"""
        case = self.cases.get(case_id)
        if not case:
            return None
        
        for key, value in updates.items():
            if hasattr(case, key):
                setattr(case, key, value)
        
        case.updated_at = datetime.now()
        return case
    
    def get_case_summary(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the case"""
        case = self.cases.get(case_id)
        if not case:
            return None
        
        return {
            "case_id": case.case_id,
            "status": case.status.value,
            "source_account": case.source_account,
            "fraud_amount": case.fraud_amount,
            "tainted_amount_traced": case.tainted_amount_traced,
            "path_count": len(case.paths),
            "suspicious_account_count": len(case.suspicious_accounts),
            "finding_count": len(case.findings),
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat()
        }
