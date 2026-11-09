from typing import Dict, Any, Optional, List


class MockRiskAdapter:
    """Mock implementation of RiskAdapter for testing"""
    
    def __init__(self):
        # Mock risk data with detailed reasons
        self.mock_risk = {
            "A001": {
                "score": 0,
                "level": "LOW",
                "reasons": ["source_account", "no_risk_factors"],
                "risk_factors": {
                    "transaction_velocity": 0,
                    "high_volume": False,
                    "new_account": False,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A002": {
                "score": 65,
                "level": "HIGH",
                "reasons": ["intermediary", "rapid_fund_movement", "large_volume"],
                "risk_factors": {
                    "transaction_velocity": 75,
                    "high_volume": True,
                    "new_account": False,
                    "multiple_counterparties": True,
                    "rapid_movement": True,
                    "high_fan_out": True,
                    "large_fund_flow": False
                }
            },
            "A003": {
                "score": 87,
                "level": "CRITICAL",
                "reasons": ["rapid_fund_movement", "high_fan_out", "large_fund_flow", "multiple_receiving_accounts"],
                "risk_factors": {
                    "transaction_velocity": 92,
                    "high_volume": True,
                    "new_account": False,
                    "multiple_counterparties": True,
                    "rapid_movement": True,
                    "high_fan_out": True,
                    "large_fund_flow": True
                }
            },
            "A004": {
                "score": 72,
                "level": "HIGH",
                "reasons": ["rapid_fund_movement", "intermediary", "large_volume"],
                "risk_factors": {
                    "transaction_velocity": 80,
                    "high_volume": True,
                    "new_account": False,
                    "multiple_counterparties": True,
                    "rapid_movement": True,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A005": {
                "score": 45,
                "level": "MEDIUM",
                "reasons": ["destination_account", "receiving_tainted_funds", "new_account"],
                "risk_factors": {
                    "transaction_velocity": 30,
                    "high_volume": False,
                    "new_account": True,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A006": {
                "score": 45,
                "level": "MEDIUM",
                "reasons": ["destination_account", "receiving_tainted_funds", "new_account"],
                "risk_factors": {
                    "transaction_velocity": 30,
                    "high_volume": False,
                    "new_account": True,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A007": {
                "score": 55,
                "level": "MEDIUM",
                "reasons": ["destination_account", "receiving_tainted_funds", "high_volume"],
                "risk_factors": {
                    "transaction_velocity": 40,
                    "high_volume": True,
                    "new_account": False,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A008": {
                "score": 35,
                "level": "LOW",
                "reasons": ["destination_account", "receiving_tainted_funds"],
                "risk_factors": {
                    "transaction_velocity": 20,
                    "high_volume": False,
                    "new_account": False,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A009": {
                "score": 35,
                "level": "LOW",
                "reasons": ["destination_account", "receiving_tainted_funds"],
                "risk_factors": {
                    "transaction_velocity": 20,
                    "high_volume": False,
                    "new_account": False,
                    "multiple_counterparties": False,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            },
            "A010": {
                "score": 50,
                "level": "MEDIUM",
                "reasons": ["destination_account", "receiving_tainted_funds", "multiple_sources"],
                "risk_factors": {
                    "transaction_velocity": 25,
                    "high_volume": False,
                    "new_account": False,
                    "multiple_counterparties": True,
                    "rapid_movement": False,
                    "high_fan_out": False,
                    "large_fund_flow": False
                }
            }
        }
    
    def get_risk(self, account_id: str) -> Dict[str, Any]:
        """
        Get risk score for an account
        """
        return self.mock_risk.get(account_id, {
            "score": 0, 
            "level": "UNKNOWN", 
            "reasons": ["account_not_found"],
            "risk_factors": {}
        })
    
    def get_risk_batch(self, account_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get risk scores for multiple accounts
        """
        results = {}
        for account_id in account_ids:
            results[account_id] = self.get_risk(account_id)
        return results
    
    def get_risk_by_type(self, account_type: str) -> List[Dict[str, Any]]:
        """
        Get all accounts of a specific type with their risk scores
        """
        results = []
        for account_id, risk_data in self.mock_risk.items():
            # In a real implementation, you'd have account type mapping
            results.append({
                "account_id": account_id,
                "risk": risk_data
            })
        return results
    
    def get_high_risk_accounts(self, threshold: int = 60) -> List[Dict[str, Any]]:
        """
        Get accounts with risk score above threshold
        """
        results = []
        for account_id, risk_data in self.mock_risk.items():
            if risk_data.get("score", 0) >= threshold:
                results.append({
                    "account_id": account_id,
                    "risk": risk_data
                })
        return sorted(results, key=lambda x: x["risk"]["score"], reverse=True)
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get summary of all risk scores
        """
        total_accounts = len(self.mock_risk)
        critical = sum(1 for r in self.mock_risk.values() if r.get("level") == "CRITICAL")
        high = sum(1 for r in self.mock_risk.values() if r.get("level") == "HIGH")
        medium = sum(1 for r in self.mock_risk.values() if r.get("level") == "MEDIUM")
        low = sum(1 for r in self.mock_risk.values() if r.get("level") == "LOW")
        
        return {
            "total_accounts": total_accounts,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "average_score": sum(r.get("score", 0) for r in self.mock_risk.values()) / total_accounts if total_accounts > 0 else 0
        }
