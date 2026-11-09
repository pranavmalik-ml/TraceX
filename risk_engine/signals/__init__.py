"""Signal implementations."""

from .velocity import score_velocity
from .fan_in import score_fan_in
from .fan_out import score_fan_out
from .rapid_movement import score_rapid_movement
from .taint_exposure import score_taint_exposure
from .multiple_sources import score_multiple_sources
from .anomalies import score_amount_anomaly, score_dormant_activation, score_circular_movement

__all__ = [
    "score_velocity",
    "score_fan_in",
    "score_fan_out",
    "score_rapid_movement",
    "score_taint_exposure",
    "score_multiple_sources",
    "score_amount_anomaly",
    "score_dormant_activation",
    "score_circular_movement",
]