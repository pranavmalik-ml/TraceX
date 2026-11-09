# TraceX Risk Engine

A rule-based risk scoring engine for accounts and transactions, designed to produce explainable scores (0–100) with evidence.

## Features

- Extracts behavioural features from transaction history.
- Computes contributions from 9 risk signals (velocity, fan-in, fan-out, rapid movement, taint exposure, multiple fraud sources, amount anomaly, dormant activation, circular movement).
- Aggregates scores with configurable weights and caps.
- Produces deterministic output with risk level and per-signature evidence.
- Designed for easy threshold tuning without code changes.
- ML-ready (Isolation Forest can be added as a separate experiment).

## Installation

Clone the repository and install dependencies (if any; uses only standard library).

## To get output in json
from risk_engine import calculate_risk, to_json

# ... after obtaining result    
json_string = to_json(result)
print(json_string)

serialise is used for it and made to get json output user work is given above
