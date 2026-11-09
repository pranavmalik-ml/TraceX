"""Feature extraction from raw transaction data."""

from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics

from .models import Context, Transaction


def extract_features(account_id: str, context: Context) -> Dict[str, Any]:
    """
    Compute a set of numerical features for a given account.

    Returns a dict with keys like:
        - total_in, total_out, net_flow
        - count_in, count_out
        - unique_in_counterparties, unique_out_counterparties
        - avg_in_amount, avg_out_amount
        - median_outgoing_delay_minutes (time from receiving to sending)
        - tainted_in_amount, tainted_out_amount, tainted_total
        - proportion_tainted_in, proportion_tainted_out
        - number_of_taint_sources
        - transaction_velocity_1h, _6h, _24h, _7d
        - dormant_days (days since last transaction before window)
        - recent_volume (last 24h)
        - circular_flow (whether money returns to an earlier counterparty)
        - max_single_amount
        - amount_stddev (over all amounts)
        - etc.
    """
    transactions = context.transactions
    # Filter transactions involving account_id (either as sender or receiver)
    account_txs = [
        tx for tx in transactions
        if tx.from_account == account_id or tx.to_account == account_id
    ]

    if not account_txs:
        # No activity -> all features zero or default
        return _default_features()

    # Time windows
    now = max(tx.timestamp for tx in account_txs)  # reference time
    windows = {
        "1h": now - timedelta(hours=1),
        "6h": now - timedelta(hours=6),
        "24h": now - timedelta(hours=24),
        "7d": now - timedelta(days=7),
    }

    features = {
        "account_id": account_id,
        "now": now,
        "total_tx_count": len(account_txs),
        "total_in_amount": 0.0,
        "total_out_amount": 0.0,
        "count_in": 0,
        "count_out": 0,
        "unique_in_counterparties": set(),
        "unique_out_counterparties": set(),
        "incoming_amounts": [],
        "outgoing_amounts": [],
        "outgoing_delays": [],  # minutes from incoming to outgoing
        "in_timestamps": [],
        "out_timestamps": [],
        "all_amounts": [],
        "tainted_in_amount": 0.0,
        "tainted_out_amount": 0.0,
        "taint_sources": set(),
        "counterparty_flow": defaultdict(float),  # net flow to each counterparty
        "first_tx_time": None,
        "last_tx_time": None,
        "window_counts": {win: 0 for win in windows},
        "window_in_counts": {win: 0 for win in windows},
        "window_out_counts": {win: 0 for win in windows},
        "window_amounts": {win: 0.0 for win in windows},
    }

    # Helper to check if tx falls within window
    def in_window(tx, win_start):
        return tx.timestamp >= win_start

    # Process transactions sorted by time
    sorted_txs = sorted(account_txs, key=lambda t: t.timestamp)
    features["first_tx_time"] = sorted_txs[0].timestamp
    features["last_tx_time"] = sorted_txs[-1].timestamp

    # For each transaction, update features
    for tx in sorted_txs:
        is_in = tx.to_account == account_id
        amount = tx.amount
        features["all_amounts"].append(amount)

        if is_in:
            features["total_in_amount"] += amount
            features["count_in"] += 1
            features["unique_in_counterparties"].add(tx.from_account)
            features["incoming_amounts"].append(amount)
            features["in_timestamps"].append(tx.timestamp)
            # Check taint
            taint = context.taint_data.get(tx.tx_id)
            if taint:
                features["tainted_in_amount"] += taint.tainted_amount
                features["taint_sources"].update(taint.taint_sources)
        else:
            features["total_out_amount"] += amount
            features["count_out"] += 1
            features["unique_out_counterparties"].add(tx.to_account)
            features["outgoing_amounts"].append(amount)
            features["out_timestamps"].append(tx.timestamp)
            taint = context.taint_data.get(tx.tx_id)
            if taint:
                features["tainted_out_amount"] += taint.tainted_amount
                features["taint_sources"].update(taint.taint_sources)

        # Circular flow: track net flow per counterparty
        if is_in:
            features["counterparty_flow"][tx.from_account] += amount
        else:
            features["counterparty_flow"][tx.to_account] -= amount

        # Window counts
        for win_label, win_start in windows.items():
            if in_window(tx, win_start):
                features["window_counts"][win_label] += 1
                if is_in:
                    features["window_in_counts"][win_label] += 1
                else:
                    features["window_out_counts"][win_label] += 1
                features["window_amounts"][win_label] += amount

    # Compute derived features
    features["unique_in_counterparties"] = len(features["unique_in_counterparties"])
    features["unique_out_counterparties"] = len(features["unique_out_counterparties"])

    # Average amounts
    features["avg_in_amount"] = statistics.mean(features["incoming_amounts"]) if features["incoming_amounts"] else 0.0
    features["avg_out_amount"] = statistics.mean(features["outgoing_amounts"]) if features["outgoing_amounts"] else 0.0

    # Outgoing delay: for each outgoing, find the most recent incoming before it
    # For simplicity, we'll compute the median delay between incoming and outgoing transactions
    # (we consider that funds could be from any previous incoming, but we approximate by pairing each outgoing
    #  with the closest incoming before it)
    if features["in_timestamps"] and features["out_timestamps"]:
        # Sort incoming timestamps
        in_times = sorted(features["in_timestamps"])
        out_times = sorted(features["out_timestamps"])
        delays = []
        for out_time in out_times:
            # Find most recent incoming <= out_time
            prev_in = None
            for in_time in in_times:
                if in_time <= out_time:
                    prev_in = in_time
                else:
                    break
            if prev_in:
                delay_minutes = (out_time - prev_in).total_seconds() / 60.0
                delays.append(delay_minutes)
        if delays:
            features["median_outgoing_delay_minutes"] = statistics.median(delays)
        else:
            features["median_outgoing_delay_minutes"] = None
    else:
        features["median_outgoing_delay_minutes"] = None

    # Proportion tainted
    total_in = features["total_in_amount"]
    total_out = features["total_out_amount"]
    features["proportion_tainted_in"] = features["tainted_in_amount"] / total_in if total_in > 0 else 0.0
    features["proportion_tainted_out"] = features["tainted_out_amount"] / total_out if total_out > 0 else 0.0
    features["total_tainted_amount"] = features["tainted_in_amount"] + features["tainted_out_amount"]
    features["number_of_taint_sources"] = len(features["taint_sources"])

    # Velocity per hour
    # We can compute average per hour for each window
    for win_label, win_start in windows.items():
        hours = (now - win_start).total_seconds() / 3600.0
        if hours > 0:
            features[f"velocity_{win_label}"] = features["window_counts"][win_label] / hours
        else:
            features[f"velocity_{win_label}"] = 0.0

    # Dormancy: days since last transaction before a reference point
    # We'll compute as days since last transaction before 30 days ago? Better: we consider a "dormant" if no activity in last 30 days
    # We'll compute last_active_days = (now - last_tx_time).days
    if features["last_tx_time"]:
        features["dormant_days"] = (now - features["last_tx_time"]).days
    else:
        features["dormant_days"] = None

    # Recent volume (last 24h)
    features["recent_volume_24h"] = features["window_amounts"]["24h"]

    # Circular movement: check if any counterparty has both in and out flows that cancel partially
    # We can flag if net flow to a counterparty is small relative to total volume
    total_volume = features["total_in_amount"] + features["total_out_amount"]
    circular = False
    if total_volume > 0:
        for cpty, net in features["counterparty_flow"].items():
            # If the absolute net flow is less than 20% of total volume and there are transactions both ways
            # (we don't have direct both-ways data here, but we can check if we have both in and out to same cpty)
            # Actually, we can compute if there are both incoming and outgoing with same counterparty
            # We'll simplify: check if counterparty appears both as sender and receiver
            # We'll need to track counterparty sets for both directions
            pass
    # For now, we'll set circular_flow = False (we could implement later)
    features["circular_flow"] = False

    # Amount anomaly: we can compute z-score of amount relative to account's history?
    # We'll compute max single amount and compare to average/median
    features["max_single_amount"] = max(features["all_amounts"]) if features["all_amounts"] else 0.0
    if features["all_amounts"]:
        features["amount_stddev"] = statistics.stdev(features["all_amounts"]) if len(features["all_amounts"]) > 1 else 0.0
        features["amount_mean"] = statistics.mean(features["all_amounts"])
    else:
        features["amount_stddev"] = 0.0
        features["amount_mean"] = 0.0

    return features


def _default_features() -> Dict[str, Any]:
    """Return zero/default features for an account with no transactions."""
    return {
        "account_id": "",
        "now": datetime.now(),
        "total_tx_count": 0,
        "total_in_amount": 0.0,
        "total_out_amount": 0.0,
        "count_in": 0,
        "count_out": 0,
        "unique_in_counterparties": 0,
        "unique_out_counterparties": 0,
        "incoming_amounts": [],
        "outgoing_amounts": [],
        "outgoing_delays": [],
        "in_timestamps": [],
        "out_timestamps": [],
        "all_amounts": [],
        "tainted_in_amount": 0.0,
        "tainted_out_amount": 0.0,
        "taint_sources": set(),
        "counterparty_flow": defaultdict(float),
        "first_tx_time": None,
        "last_tx_time": None,
        "window_counts": {},
        "window_in_counts": {},
        "window_out_counts": {},
        "window_amounts": {},
        "unique_in_counterparties": 0,
        "unique_out_counterparties": 0,
        "avg_in_amount": 0.0,
        "avg_out_amount": 0.0,
        "median_outgoing_delay_minutes": None,
        "proportion_tainted_in": 0.0,
        "proportion_tainted_out": 0.0,
        "total_tainted_amount": 0.0,
        "number_of_taint_sources": 0,
        "velocity_1h": 0.0,
        "velocity_6h": 0.0,
        "velocity_24h": 0.0,
        "velocity_7d": 0.0,
        "dormant_days": None,
        "recent_volume_24h": 0.0,
        "circular_flow": False,
        "max_single_amount": 0.0,
        "amount_stddev": 0.0,
        "amount_mean": 0.0,
    }