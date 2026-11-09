import unittest
from datetime import datetime, timedelta
from risk_engine.scoring import calculate_risk
from risk_engine.features import extract_features
from risk_engine.models import Context, Transaction


class TestScoring(unittest.TestCase):
    def test_risk_scoring(self):
        now = datetime.now()
        account = "A001"
        txs = [
            Transaction(tx_id="t1", from_account="C1", to_account=account, amount=1000,
                        timestamp=now),
            Transaction(tx_id="t2", from_account=account, to_account="C2", amount=900,
                        timestamp=now + timedelta(minutes=1)),
            Transaction(tx_id="t3", from_account=account, to_account="C3", amount=100,
                        timestamp=now + timedelta(minutes=2)),
        ]
        context = Context(transactions=txs, taint_data={})
        features = extract_features(account, context)
        result = calculate_risk(account, "account", features)
        self.assertGreater(result.risk_score, 0)
        self.assertEqual(result.entity_id, account)
        self.assertIn(result.risk_level, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.assertTrue(len(result.signals) > 0)

if __name__ == "__main__":
    unittest.main()