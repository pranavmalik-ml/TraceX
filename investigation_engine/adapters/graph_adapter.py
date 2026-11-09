from typing import List, Dict, Any, Optional
from datetime import datetime


class GraphAdapter:
    """Adapter for graph engine"""
    
    def trace_forward(self, source: str, max_hops: int, 
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Trace forward from source account
        
        Returns:
            List of paths with account list and amounts
        """
        raise NotImplementedError("GraphAdapter.trace_forward must be implemented")
    
    def trace_backward(self, target: str, max_hops: int,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Trace backward from target account
        
        Returns:
            List of paths with account list and amounts
        """
        raise NotImplementedError("GraphAdapter.trace_backward must be implemented")
    
    def get_adjacent_accounts(self, account_id: str, direction: str = "both") -> List[str]:
        """Get accounts adjacent to the given account"""
        raise NotImplementedError("GraphAdapter.get_adjacent_accounts must be implemented")