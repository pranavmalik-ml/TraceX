import unittest
from datetime import datetime, timedelta
from risk_engine.features import extract_features
from risk_engine.models import Context, Transaction, TaintData


class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now()
        self.account = "A001"

    def test_empty_transactions(self):
        context = Context(transactions=[], taint_data={})
        features = extract_features(self.account, context)
        self.assertEqual(features["total_tx_count"], 0)
        self.assertEqual(features["unique_in_counterparties"], 0)

    def test_basic_transactions(self):
        txs = [
            Transaction(tx_id="t1", from_account="C1", to_account=self.account, amount=100,
                        timestamp=self.now - timedelta(minutes=5)),
            Transaction(tx_id="t2", from_account=self.account, to_account="C2", amount=50,
                        timestamp=self.now - timedelta(minutes=2)),
        ]
        context = Context(transactions=txs, taint_data={})
        features = extract_features(self.account, context)
        self.assertEqual(features["total_in_amount"], 100)
        self.assertEqual(features["total_out_amount"], 50)
        self.assertEqual(features["unique_in_counterparties"], 1)
        self.assertEqual(features["unique_out_counterparties"], 1)
        self.assertIsNotNone(features["median_outgoing_delay_minutes"])

if __name__ == "__main__":
    unittest.main()