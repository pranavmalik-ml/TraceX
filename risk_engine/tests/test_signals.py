import unittest
from risk_engine.signals.velocity import score_velocity
from risk_engine.signals.fan_in import score_fan_in
from risk_engine.signals.fan_out import score_fan_out
from risk_engine.signals.rapid_movement import score_rapid_movement
from risk_engine.signals.taint_exposure import score_taint_exposure
from risk_engine.signals.multiple_sources import score_multiple_sources
from risk_engine.signals.anomalies import score_amount_anomaly, score_dormant_activation


class TestSignals(unittest.TestCase):
    def test_velocity(self):
        features = {"velocity_1h": 12, "velocity_24h": 4}
        score, evidence = score_velocity(features)
        self.assertAlmostEqual(score, 13.8)  # 9.0 from 1h + 4.8 from 24h

    def test_fan_in(self):
        features = {"unique_in_counterparties": 5}
        score, evidence = score_fan_in(features)
        self.assertAlmostEqual(score, 5.0)  # 5/10 * 10

    def test_rapid_movement(self):
        features = {"median_outgoing_delay_minutes": 2}
        score, evidence = score_rapid_movement(features)
        self.assertAlmostEqual(score, 16.0)  # 20*(1-2/10)

    def test_taint_exposure(self):
        features = {"proportion_tainted_in": 0.4, "proportion_tainted_out": 0.0, "total_tainted_amount": 8000}
        score, evidence = score_taint_exposure(features)
        # proportion part: 0.4/0.5 * 20*0.7 = 11.2; amount part: 8000/10000 * 20*0.3 = 4.8; total 16.0
        self.assertAlmostEqual(score, 16.0)

if __name__ == "__main__":
    unittest.main()