# TraceX

**Explainable multi-hop transaction tracing and proportional fund-attribution prototype**  
Smart India Hackathon 2026 · Blockchain & Cybersecurity

TraceX is a runnable local end-to-end demonstration of a fraud-fund tracing workflow. It combines transaction ingestion, a bounded directed-graph traversal, a proportional taint ledger, explainable rule-based risk indicators, a persistent SQLite case/transaction store, and a browser dashboard.

> **Status: Working MVP / research prototype — not a production banking or law-enforcement system.** The local web application, API, SQLite persistence, CSV import, trace workflow, graph view, and JSON report export are implemented. This release does not include a trained XGBoost model, PostgreSQL deployment, React/Cytoscape.js, bank/NCRP/CFCFRMS integrations, authentication, or legal LIBR adjudication. The frontend is a lightweight HTML/CSS/JavaScript dashboard with an SVG graph renderer. Do not describe these omitted items as implemented.

## Features

- **CSV ingestion:** validates the five required transaction columns and imports records into SQLite.
- **Persistent storage:** local SQLite database for transactions and investigation case metadata.
- **Multi-hop tracing:** directed multigraph and bounded breadth-first search, configurable from 1 to 8 hops.
- **Source-specific proportional taint:** uses `Decimal` arithmetic to estimate source-linked amounts as balances move through the selected transaction network.
- **Explainable risk indicators:** deterministic signals for fan-in, fan-out, transaction velocity, rapid movement, and taint exposure. Each signal includes evidence text.
- **Investigator dashboard:** summary metrics, trace controls, network visualization, account-level risk ranking, transaction ledger, and CSV import.
- **Export:** download the trace result as a JSON evidence bundle.
- **API documentation:** interactive OpenAPI documentation at `/docs` while the server is running.

## Run locally

Requirements: Python 3.10+.

### Windows PowerShell

```powershell
cd TraceX
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

### macOS / Linux

```bash
cd TraceX
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000**. API docs: **http://127.0.0.1:8000/docs**. On first launch, the application creates `backend/tracex.db` and loads the synthetic sample dataset from `data/transactions.csv`.

## Demo investigation

The included synthetic data contains an origin account `A` with two outgoing transfers totalling ₹70,000. Use:

- Origin account: `A`
- Suspected amount: `70000`
- Source / case ID: `CASE-001`
- Max hops: `8`

Select **Run investigation**. The dashboard saves case metadata, runs the trace, displays reachable accounts and transactions, renders the network, and shows rule-based account risk signals. The JSON report button exports the current trace.

## CSV format

The upload endpoint expects a header row with these exact columns:

```csv
transaction_id,sender,receiver,amount,timestamp
TXN001,ACCOUNT_A,ACCOUNT_B,25000.00,2026-10-01 10:15:00
```

Amounts must be positive decimal values; timestamps must be ISO-compatible. Transaction IDs must be unique. The dashboard's replace option clears the existing ledger before importing. Use synthetic or properly anonymised records only.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard` | Summary metrics and recent transactions |
| GET | `/api/transactions` | List transactions |
| POST | `/api/transactions` | Add one transaction |
| POST | `/api/transactions/upload` | Import CSV (`multipart/form-data`) |
| GET | `/api/accounts` | List accounts with baseline risk indicators |
| GET | `/api/cases` | List saved cases |
| POST | `/api/cases` | Create case metadata |
| POST | `/api/trace` | Run bounded trace and proportional attribution |

### Trace request example

```json
{
  "origin_account": "A",
  "origin_amount": 70000,
  "source_id": "CASE-001",
  "max_hops": 8
}
```

## Tests

```bash
python -m pytest -q
```

Tests cover the original taint-propagation and risk modules plus API health, demo data, trace bounds, attribution invariants, and invalid origins. Passing tests verifies the included prototype behaviours; it does not establish operational readiness or real-world predictive accuracy.

## Methodology and limitations

1. **Proportional allocation is not LIBR.** The ledger distributes tracked taint according to the tracked balance mix at the time of a transfer. Lowest Intermediate Balance Rule and other legal/accounting tracing doctrines have different assumptions and must be assessed separately by qualified domain experts.
2. **Risk is not guilt.** Scores are deterministic heuristic indicators. They are not trained XGBoost probabilities and must not be used as sole grounds for account freezing, enforcement, or adverse action.
3. **Origin balance is an investigator-supplied assumption.** Trace results depend on the accuracy of the origin account, amount, timestamps, and completeness of the supplied ledger. Unobserved inflows and outflows can materially change attribution.
4. **Temporal limitations.** The trace traverses the supplied graph and applies the ledger in timestamp order. It does not yet enforce a source-event timestamp or provide legal-grade transaction chronology reconciliation.
5. **No production integrations.** No live bank rails, NCRP/CFCFRMS, KYC provider, or external institution connector is included.
6. **Security hardening is required.** The local demo has no user authentication/authorization, production secrets management, deployment TLS, investigator audit trail, or production-grade retention controls. Do not expose it publicly or upload real financial/PII data.
7. **Storage is local SQLite.** PostgreSQL migration and production deployment configuration are future work.

## Repository structure

```text
TraceX/
├── backend/              # FastAPI application and SQLite database (created at runtime)
├── frontend/             # Browser dashboard (HTML, CSS, JavaScript)
├── graph_engine/         # NetworkX graph construction and traversal helpers
├── investigation_engine/ # Case workflow, evidence, findings, adapters and mocks
├── risk_engine/          # Feature extraction and explainable rule-based scoring
├── tests/                # Core and API tests
├── data/                 # Synthetic demo transactions
├── taint_propagator_v2.py
├── run.py
└── requirements.txt
```

## License

No open-source license has been applied. Unless a license is added, all rights remain with the copyright holder.
