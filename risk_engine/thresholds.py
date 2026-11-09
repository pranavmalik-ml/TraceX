"""Default thresholds and weights for signals."""

from typing import Dict, Any


def get_default_thresholds() -> Dict[str, Any]:
    """Return default thresholds for all signals."""
    return {
        "velocity": {
            "velocity_1h_high": 10.0,
            "velocity_24h_high": 5.0,
            "max_contribution": 15.0,
        },
        "fan_in": {
            "fan_in_high": 10,
            "max_contribution": 10.0,
        },
        "fan_out": {
            "fan_out_high": 10,
            "max_contribution": 15.0,
        },
        "rapid_movement": {
            "delay_threshold_minutes": 10.0,
            "max_contribution": 20.0,
        },
        "taint_exposure": {
            "taint_proportion_high": 0.5,
            "taint_amount_high": 10000.0,
            "max_contribution": 20.0,
        },
        "multiple_sources": {
            "sources_high": 2,
            "max_contribution": 10.0,
        },
        "amount_anomaly": {
            "z_score_high": 3.0,
            "max_contribution": 10.0,
        },
        "dormant_activation": {
            "dormant_days_threshold": 30,
            "recent_volume_threshold": 5000.0,
            "max_contribution": 10.0,
        },
        "circular_movement": {
            "max_contribution": 10.0,
        },
        "risk_levels": {
            "LOW": 20,
            "MEDIUM": 40,
            "HIGH": 70,
            "CRITICAL": 100,
        }
    }