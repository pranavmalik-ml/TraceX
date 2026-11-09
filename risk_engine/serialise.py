"""Helpers to convert RiskResult to JSON‑compatible dictionaries."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Dict, Any
from .models import RiskResult, SignalContribution


class EnhancedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for dataclasses and datetime objects."""
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_risk_result(result: RiskResult) -> Dict[str, Any]:
    """
    Convert a RiskResult object into the exact output contract dictionary.

    The returned dict can be passed directly to json.dumps().
    """
    return {
        "entity_id": result.entity_id,
        "entity_type": result.entity_type,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "signals": [
            {
                "code": sig.code,
                "label": sig.label,
                "contribution": sig.contribution,
                "evidence": sig.evidence,   # Already a dict
            }
            for sig in result.signals
        ],
        "model_version": result.model_version,
    }


def to_json(result: RiskResult, indent: int = 2) -> str:
    """
    Serialize a RiskResult directly to a JSON string.
    """
    return json.dumps(
        serialize_risk_result(result),
        indent=indent,
        cls=EnhancedJSONEncoder
    )
