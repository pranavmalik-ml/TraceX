from typing import Dict, Any, List, Optional


class TaintAdapter:
    """Adapter for taint engine"""
    
    def get_taint_flow(self, transaction_id: str, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get taint flow information for a transaction
        
        Args:
            transaction_id: Transaction ID
            source_id: Optional specific source ID to filter
            
        Returns:
            Dict with taint information
        """
        raise NotImplementedError("TaintAdapter.get_taint_flow must be implemented")
    
    def get_taint_by_account(self, account_id: str, 
                            transaction_ids: List[str]) -> Dict[str, Any]:
        """
        Get taint information aggregated by account
        """
        raise NotImplementedError("TaintAdapter.get_taint_by_account must be implemented")
    
    def get_multiple_source_taint(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get taint information for multiple fraud sources
        """
        raise NotImplementedError("TaintAdapter.get_multiple_source_taint must be implemented")
    
    def get_source_contributions(self, transaction_ids: List[str]) -> Dict[str, float]:
        """
        Aggregate source contributions across multiple transactions
        """
        raise NotImplementedError("TaintAdapter.get_source_contributions must be implemented")