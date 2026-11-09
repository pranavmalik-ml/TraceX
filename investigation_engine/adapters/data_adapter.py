from typing import Dict, Any, List, Optional
from datetime import datetime


class DataAdapter:
    """Adapter for transaction data"""
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details"""
        # Implementation should connect to actual data source
        raise NotImplementedError("DataAdapter.get_transaction must be implemented")
    
    def get_transactions_by_account(self, account_id: str, 
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all transactions for an account within time range"""
        raise NotImplementedError("DataAdapter.get_transactions_by_account must be implemented")
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account details"""
        raise NotImplementedError("DataAdapter.get_account must be implemented")
