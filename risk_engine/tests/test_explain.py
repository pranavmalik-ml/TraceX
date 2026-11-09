import unittest
from risk_engine.scoring import calculate_risk
from risk_engine.explain import explain_risk
from risk_engine.features import extract_features
from risk_engine.models import Context, Transaction
from datetime import datetime, timedelta

class TestExplain(unittest.TestCase):
    def test_explain(self):
        now = datetime.now()
        account = "A001"
        txs = [
            Transaction(tx_id="t1", from_account="C1", to_account=account, amount=1000,
                        timestamp=now),
            Transaction(tx_id="t2", from_account=account, to_account="C2", amount=900,
                        timestamp=now + timedelta(minutes=1)),
        ]
        context = Context(transactions=txs, taint_data={})
        features = extract_features(account, context)
        result = calculate_risk(account, "account", features)
        reasons = explain_risk(result)
        self.assertEqual(len(reasons), len(result.signals))
        for reason in reasons:
            self.assertIn("code", reason)
            self.assertIn("contribution", reason)
            self.assertIn("evidence", reason)

if __name__ == "__main__":
    unittest.main()