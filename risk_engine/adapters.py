"""Adapters for consuming external data (taint, graph)."""

from typing import Dict, List, Optional
from .models import Context, Transaction, TaintData, GraphData


class TaintAdapter:
    """
    Adapter to convert external taint data into the internal format.
    This is a placeholder; in reality, it would fetch from a Taint Engine.
    """
    @staticmethod
    def adapt(taint_records: List[Dict]) -> Dict[str, TaintData]:
        """
        Convert list of taint records (with tx_id, tainted_amount, sources)
        into dict mapping tx_id -> TaintData.
        """
        result = {}
        for rec in taint_records:
            result[rec["tx_id"]] = TaintData(
                tx_id=rec["tx_id"],
                tainted_amount=rec.get("tainted_amount", 0.0),
                taint_sources=rec.get("sources", [])
            )
        return result


class GraphAdapter:
    """
    Adapter for graph data (counterparty relationships, cycles).
    """
    @staticmethod
    def adapt(graph_records: List[Dict]) -> GraphData:
        # For now, return a placeholder
        return GraphData()