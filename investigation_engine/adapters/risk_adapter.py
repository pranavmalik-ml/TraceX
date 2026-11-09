from typing import Dict, Any, Optional, List


class RiskAdapter:
    """Adapter for risk engine"""
    
    def get_risk(self, account_id: str) -> Dict[str, Any]:
        """
        Get risk score for an account
        
        Returns:
            Dict with score, level, and reasons
        """
        raise NotImplementedError("RiskAdapter.get_risk must be implemented")
    
    def get_risk_batch(self, account_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get risk scores for multiple accounts
        """
        raise NotImplementedError("RiskAdapter.get_risk_batch must be implemented")