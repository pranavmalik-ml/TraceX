from typing import Dict, Any, List, Optional


class MockTaintAdapter:
    """Mock implementation of TaintAdapter for testing"""
    
    def __init__(self):
        # Mock taint data with multiple sources support
        self.mock_taint = {
            "T1001": {
                "transaction_id": "T1001",
                "source_account": "FRAUD_SOURCE",
                "tainted_amount": 50000,
                "sources": {
                    "FRAUD_SOURCE": 50000
                },
                "clean_amount": 0,
                "taint_percentage": 100.0
            },
            "T1002": {
                "transaction_id": "T1002",
                "source_account": "A002",
                "tainted_amount": 27000,
                "sources": {
                    "FRAUD_SOURCE": 27000
                },
                "clean_amount": 3000,
                "taint_percentage": 90.0
            },
            "T1003": {
                "transaction_id": "T1003",
                "source_account": "A002",
                "tainted_amount": 15000,
                "sources": {
                    "FRAUD_SOURCE": 15000
                },
                "clean_amount": 5000,
                "taint_percentage": 75.0
            },
            "T1004": {
                "transaction_id": "T1004",
                "source_account": "A003",
                "tainted_amount": 13500,
                "sources": {
                    "FRAUD_SOURCE": 13500
                },
                "clean_amount": 1500,
                "taint_percentage": 90.0
            },
            "T1005": {
                "transaction_id": "T1005",
                "source_account": "A003",
                "tainted_amount": 13500,
                "sources": {
                    "FRAUD_SOURCE": 13500
                },
                "clean_amount": 1500,
                "taint_percentage": 90.0
            },
            "T1006": {
                "transaction_id": "T1006",
                "source_account": "A004",
                "tainted_amount": 15000,
                "sources": {
                    "FRAUD_SOURCE": 15000
                },
                "clean_amount": 5000,
                "taint_percentage": 75.0
            },
            "T1007": {
                "transaction_id": "T1007",
                "source_account": "A005",
                "tainted_amount": 9000,
                "sources": {
                    "FRAUD_SOURCE": 9000
                },
                "clean_amount": 1000,
                "taint_percentage": 90.0
            },
            "T1008": {
                "transaction_id": "T1008",
                "source_account": "A006",
                "tainted_amount": 7200,
                "sources": {
                    "FRAUD_SOURCE": 7200
                },
                "clean_amount": 800,
                "taint_percentage": 90.0
            },
            # Multiple fraud sources scenario
            "T2001": {
                "transaction_id": "T2001",
                "source_account": "A001",
                "tainted_amount": 30000,
                "sources": {
                    "FRAUD_SOURCE_1": 20000,
                    "FRAUD_SOURCE_2": 10000
                },
                "clean_amount": 0,
                "taint_percentage": 100.0
            },
            "T2002": {
                "transaction_id": "T2002",
                "source_account": "A010",
                "tainted_amount": 30000,
                "sources": {
                    "FRAUD_SOURCE_1": 20000,
                    "FRAUD_SOURCE_2": 10000
                },
                "clean_amount": 0,
                "taint_percentage": 100.0
            },
            # Clean money transaction
            "T3001": {
                "transaction_id": "T3001",
                "source_account": "A002",
                "tainted_amount": 0,
                "sources": {},
                "clean_amount": 5000,
                "taint_percentage": 0.0
            }
        }
    
    def get_taint_flow(self, transaction_id: str, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get taint flow information for a transaction
        """
        taint_info = self.mock_taint.get(transaction_id, {})
        
        if not taint_info:
            return {
                "transaction_id": transaction_id,
                "tainted_amount": 0,
                "sources": {},
                "clean_amount": 0,
                "taint_percentage": 0.0
            }
        
        # If specific source requested, filter
        if source_id and "sources" in taint_info:
            specific_amount = taint_info["sources"].get(source_id, 0)
            result = taint_info.copy()
            result["tainted_amount"] = specific_amount
            return result
        
        return taint_info
    
    def get_taint_by_account(self, account_id: str, 
                            transaction_ids: List[str]) -> Dict[str, Any]:
        """
        Get taint information aggregated by account
        """
        total_tainted = 0
        total_clean = 0
        source_contributions = {}
        
        for tx_id in transaction_ids:
            taint_info = self.get_taint_flow(tx_id)
            if taint_info:
                total_tainted += taint_info.get("tainted_amount", 0)
                total_clean += taint_info.get("clean_amount", 0)
                for source, amount in taint_info.get("sources", {}).items():
                    source_contributions[source] = source_contributions.get(source, 0) + amount
        
        total_amount = total_tainted + total_clean
        
        return {
            "account_id": account_id,
            "total_tainted": total_tainted,
            "total_clean": total_clean,
            "total_amount": total_amount,
            "taint_percentage": (total_tainted / total_amount * 100) if total_amount > 0 else 0,
            "source_contributions": source_contributions
        }
    
    def get_multiple_source_taint(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get taint information for multiple fraud sources
        """
        return self.mock_taint.get(transaction_id, {})
    
    def get_source_contributions(self, transaction_ids: List[str]) -> Dict[str, float]:
        """
        Aggregate source contributions across multiple transactions
        """
        total_contributions = {}
        
        for tx_id in transaction_ids:
            taint_info = self.get_taint_flow(tx_id)
            if taint_info and "sources" in taint_info:
                for source, amount in taint_info["sources"].items():
                    total_contributions[source] = total_contributions.get(source, 0) + amount
        
        return total_contributions
    
    def get_taint_path(self, path_accounts: List[str], 
                      transactions: List[str]) -> Dict[str, Any]:
        """
        Get taint information for a complete path
        """
        path_taint = {
            "accounts": path_accounts,
            "total_tainted": 0,
            "source_contributions": {},
            "account_taint": {}
        }
        
        for i, account in enumerate(path_accounts):
            # Find transactions involving this account
            account_txns = []
            for tx_id in transactions:
                txn = self.get_taint_flow(tx_id)
                if txn and (txn.get("source_account") == account or 
                           (i > 0 and tx_id in transactions[:i])):
                    account_txns.append(tx_id)
            
            if account_txns:
                account_taint = self.get_taint_by_account(account, account_txns)
                path_taint["account_taint"][account] = account_taint
                path_taint["total_tainted"] += account_taint.get("total_tainted", 0)
                
                for source, amount in account_taint.get("source_contributions", {}).items():
                    path_taint["source_contributions"][source] = \
                        path_taint["source_contributions"].get(source, 0) + amount
        
        return path_taint
