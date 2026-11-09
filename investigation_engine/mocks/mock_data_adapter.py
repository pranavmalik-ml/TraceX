from typing import Dict, Any, List, Optional
from datetime import datetime


class MockDataAdapter:
    """Mock implementation of DataAdapter for testing"""
    
    def __init__(self):
        # Mock transaction data
        self.mock_transactions = {
            "T1001": {
                "transaction_id": "T1001",
                "source_account": "A001",
                "destination_account": "A002",
                "amount": 50000,
                "timestamp": "2026-08-17T10:00:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1002": {
                "transaction_id": "T1002",
                "source_account": "A002",
                "destination_account": "A003",
                "amount": 30000,
                "timestamp": "2026-08-17T10:15:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1003": {
                "transaction_id": "T1003",
                "source_account": "A002",
                "destination_account": "A004",
                "amount": 20000,
                "timestamp": "2026-08-17T10:30:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1004": {
                "transaction_id": "T1004",
                "source_account": "A003",
                "destination_account": "A005",
                "amount": 15000,
                "timestamp": "2026-08-17T11:00:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1005": {
                "transaction_id": "T1005",
                "source_account": "A003",
                "destination_account": "A006",
                "amount": 15000,
                "timestamp": "2026-08-17T11:15:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1006": {
                "transaction_id": "T1006",
                "source_account": "A004",
                "destination_account": "A007",
                "amount": 20000,
                "timestamp": "2026-08-17T11:30:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1007": {
                "transaction_id": "T1007",
                "source_account": "A005",
                "destination_account": "A008",
                "amount": 10000,
                "timestamp": "2026-08-17T12:00:00",
                "type": "transfer",
                "currency": "USD"
            },
            "T1008": {
                "transaction_id": "T1008",
                "source_account": "A006",
                "destination_account": "A009",
                "amount": 8000,
                "timestamp": "2026-08-17T12:15:00",
                "type": "transfer",
                "currency": "USD"
            },
            # Multiple fraud sources scenario
            "T2001": {
                "transaction_id": "T2001",
                "source_account": "A001",
                "destination_account": "A010",
                "amount": 30000,
                "timestamp": "2026-08-17T13:00:00",
                "type": "transfer",
                "currency": "USD"
            },
            # Clean money scenario
            "T3001": {
                "transaction_id": "T3001",
                "source_account": "A002",
                "destination_account": "A003",
                "amount": 5000,
                "timestamp": "2026-08-17T10:20:00",
                "type": "transfer",
                "currency": "USD"
            }
        }
        
        # Mock account data
        self.mock_accounts = {
            "A001": {
                "account_id": "A001", 
                "type": "source", 
                "owner": "Customer 1",
                "fraud_amount": 50000,
                "balance": 100000,
                "created_at": "2025-01-01T00:00:00"
            },
            "A002": {
                "account_id": "A002", 
                "type": "intermediary", 
                "owner": "Customer 2",
                "balance": 75000,
                "created_at": "2025-02-01T00:00:00"
            },
            "A003": {
                "account_id": "A003", 
                "type": "intermediary", 
                "owner": "Customer 3",
                "balance": 45000,
                "created_at": "2025-03-01T00:00:00"
            },
            "A004": {
                "account_id": "A004", 
                "type": "intermediary", 
                "owner": "Customer 4",
                "balance": 35000,
                "created_at": "2025-04-01T00:00:00"
            },
            "A005": {
                "account_id": "A005", 
                "type": "destination", 
                "owner": "Customer 5",
                "balance": 25000,
                "created_at": "2025-05-01T00:00:00"
            },
            "A006": {
                "account_id": "A006", 
                "type": "destination", 
                "owner": "Customer 6",
                "balance": 22000,
                "created_at": "2025-06-01T00:00:00"
            },
            "A007": {
                "account_id": "A007", 
                "type": "destination", 
                "owner": "Customer 7",
                "balance": 30000,
                "created_at": "2025-07-01T00:00:00"
            },
            "A008": {
                "account_id": "A008", 
                "type": "destination", 
                "owner": "Customer 8",
                "balance": 15000,
                "created_at": "2025-08-01T00:00:00"
            },
            "A009": {
                "account_id": "A009", 
                "type": "destination", 
                "owner": "Customer 9",
                "balance": 12000,
                "created_at": "2025-09-01T00:00:00"
            },
            "A010": {
                "account_id": "A010", 
                "type": "destination", 
                "owner": "Customer 10",
                "balance": 40000,
                "created_at": "2025-10-01T00:00:00"
            }
        }
        
        # Mock account transaction mapping
        self.mock_account_transactions = {
            "A001": ["T1001", "T2001"],
            "A002": ["T1001", "T1002", "T1003", "T3001"],
            "A003": ["T1002", "T1004", "T1005", "T3001"],
            "A004": ["T1003", "T1006"],
            "A005": ["T1004", "T1007"],
            "A006": ["T1005", "T1008"],
            "A007": ["T1006"],
            "A008": ["T1007"],
            "A009": ["T1008"],
            "A010": ["T2001"]
        }
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details"""
        return self.mock_transactions.get(transaction_id)
    
    def get_transactions_by_account(self, account_id: str, 
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all transactions for an account within time range"""
        transaction_ids = self.mock_account_transactions.get(account_id, [])
        transactions = []
        
        for tx_id in transaction_ids:
            txn = self.mock_transactions.get(tx_id)
            if txn:
                # Filter by time if provided
                if start_time:
                    txn_time = datetime.fromisoformat(txn["timestamp"])
                    if txn_time < start_time:
                        continue
                if end_time:
                    txn_time = datetime.fromisoformat(txn["timestamp"])
                    if txn_time > end_time:
                        continue
                transactions.append(txn)
        
        return transactions
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account details"""
        return self.mock_accounts.get(account_id)
    
    def get_account_balance(self, account_id: str) -> Optional[float]:
        """Get account balance"""
        account = self.mock_accounts.get(account_id)
        return account.get("balance") if account else None
    
    def get_account_transaction_count(self, account_id: str) -> int:
        """Get number of transactions for an account"""
        return len(self.mock_account_transactions.get(account_id, []))