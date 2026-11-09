from __future__ import annotations

import csv
import io
import sqlite3
from collections import defaultdict, deque
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import networkx as nx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(__file__).resolve().parent / "tracex.db"
FRONTEND = ROOT / "frontend"
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="TraceX API", version="1.0.0", description="Explainable multi-hop fraud-fund tracing demo API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY, sender TEXT NOT NULL, receiver TEXT NOT NULL,
            amount TEXT NOT NULL CHECK(CAST(amount AS REAL) > 0), timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY, title TEXT NOT NULL, origin_account TEXT NOT NULL,
            origin_amount TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        count = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if count == 0:
            with (ROOT / "data" / "transactions.csv").open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    con.execute("INSERT OR IGNORE INTO transactions(transaction_id,sender,receiver,amount,timestamp) VALUES(?,?,?,?,?)",
                                (row["transaction_id"], row["sender"], row["receiver"], row["amount"], row["timestamp"]))


class TransactionIn(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=80)
    sender: str = Field(min_length=1, max_length=120)
    receiver: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    timestamp: datetime

    @field_validator("sender", "receiver", "transaction_id")
    @classmethod
    def strip_fields(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank")
        return value


class CaseIn(BaseModel):
    case_id: str = Field(min_length=1, max_length=80)
    title: str = Field(default="Fraud investigation", max_length=200)
    origin_account: str = Field(min_length=1, max_length=120)
    origin_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class TraceIn(BaseModel):
    origin_account: str = Field(min_length=1)
    origin_amount: Decimal = Field(gt=0)
    source_id: str = "CASE_SOURCE"
    max_hops: int = Field(default=8, ge=1, le=8)


def transactions():
    with db() as con:
        rows = con.execute("SELECT * FROM transactions ORDER BY timestamp, transaction_id").fetchall()
    return [dict(r) for r in rows]


def graph_for(rows):
    graph = nx.MultiDiGraph()
    for t in rows:
        graph.add_edge(t["sender"], t["receiver"], key=t["transaction_id"], **t)
    return graph


def account_risk(account, rows, taint_ratio=0.0):
    incoming = [x for x in rows if x["receiver"] == account]
    outgoing = [x for x in rows if x["sender"] == account]
    counterparties = {x["sender"] for x in incoming} | {x["receiver"] for x in outgoing}
    signals = []
    def add(label, score, evidence):
        if score > 0: signals.append({"signal": label, "score": round(score, 1), "evidence": evidence})
    add("Fan-in", min(18, len({x['sender'] for x in incoming}) * 4), f"{len({x['sender'] for x in incoming})} incoming counterparties")
    add("Fan-out", min(18, len({x['receiver'] for x in outgoing}) * 4), f"{len({x['receiver'] for x in outgoing})} outgoing counterparties")
    add("Transaction velocity", min(16, max(0, len(incoming)+len(outgoing)-2) * 2), f"{len(incoming)+len(outgoing)} observed transactions")
    add("Taint exposure", min(35, taint_ratio * 35), f"{taint_ratio*100:.1f}% estimated taint exposure")
    rapid = False
    times = sorted(datetime.fromisoformat(x["timestamp"]) for x in incoming + outgoing)
    if len(times) > 1:
        rapid = any((b-a).total_seconds() <= 3600 for a,b in zip(times,times[1:]))
    add("Rapid movement", 13 if rapid else 0, "Transactions within one hour" if rapid else "No rapid sequence detected")
    score = min(100, sum(s["score"] for s in signals))
    level = "CRITICAL" if score >= 70 else "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW"
    return {"account": account, "risk_score": round(score,1), "risk_level": level, "signals": signals, "transaction_count": len(incoming)+len(outgoing), "counterparty_count": len(counterparties)}


def trace_result(payload: TraceIn, rows):
    origin = payload.origin_account.strip()
    graph = graph_for(rows)
    if origin not in graph:
        raise HTTPException(404, f"Origin account '{origin}' was not found in transaction data")
    # Bounded BFS retains transaction-level edges and shortest hop distance.
    distances = {origin: 0}; queue = deque([origin]); visited_edges = []
    while queue:
        node = queue.popleft()
        if distances[node] >= payload.max_hops: continue
        edges = sorted(graph.out_edges(node, keys=True, data=True), key=lambda e: (e[3]["timestamp"], e[2]))
        for u,v,key,data in edges:
            visited_edges.append(data)
            if v not in distances:
                distances[v] = distances[u] + 1
                queue.append(v)
    reachable = set(distances)
    selected = [r for r in rows if r["sender"] in reachable and r["receiver"] in reachable and distances.get(r["receiver"], 999) <= payload.max_hops]
    # Run the proportional-taint ledger in chronological order. Unknown external inflows remain clean.
    balances = defaultdict(Decimal); source_balances = defaultdict(lambda: defaultdict(Decimal)); tx_attribution=[]
    balances[origin] = payload.origin_amount
    source_balances[origin][payload.source_id] = payload.origin_amount
    for row in sorted(selected, key=lambda x:(x["timestamp"],x["transaction_id"])):
        amount = Decimal(row["amount"]); sender=row["sender"]; receiver=row["receiver"]
        total = balances[sender]
        if amount > total:
            # Untracked/clean funds are not assumed tainted; do not invent source attribution.
            total = amount if total == 0 else total
            if amount > balances[sender] and balances[sender] > 0:
                # Spend the tracked pool proportionally, and treat the excess as clean.
                spend = balances[sender]
            else: spend = amount
        else: spend = amount
        if balances[sender] <= 0:
            source_transfer = {}
        else:
            source_transfer = {sid: (spend * val / balances[sender]) for sid,val in source_balances[sender].items() if val > 0}
        tainted = sum(source_transfer.values(), Decimal("0"))
        clean_spend = amount - tainted
        balances[sender] = max(Decimal("0"), balances[sender] - spend)
        for sid,val in source_transfer.items():
            source_balances[sender][sid] -= val
            source_balances[receiver][sid] += val
        balances[receiver] += amount
        tx_attribution.append({"transaction_id":row["transaction_id"],"sender":sender,"receiver":receiver,"amount":str(amount),"tainted_amount":str(tainted),"clean_amount":str(clean_spend),"taint_sources":{k:str(v) for k,v in source_transfer.items()},"timestamp":row["timestamp"]})
    accounts=[]
    for account,hop in sorted(distances.items(), key=lambda x:(x[1],x[0])):
        taint=sum(source_balances[account].values(),Decimal("0"))
        total=balances[account]
        ratio=float(taint/total) if total>0 else 0
        risk=account_risk(account,rows,ratio)
        accounts.append({"account":account,"hops":hop,"tracked_balance":str(total),"tainted_balance":str(taint),"clean_balance":str(max(Decimal(0),total-taint)),"taint_ratio":round(ratio,4),"risk":risk})
    edges=[]
    for r in tx_attribution:
        if r["sender"] in reachable and r["receiver"] in reachable:
            edges.append({"id":r["transaction_id"],"source":r["sender"],"target":r["receiver"],"amount":r["amount"],"tainted_amount":r["tainted_amount"],"timestamp":r["timestamp"]})
    total_taint=sum((sum(source_balances[a].values(),Decimal("0")) for a in reachable),Decimal("0"))
    return {"origin_account":origin,"source_id":payload.source_id,"max_hops":payload.max_hops,"accounts":accounts,"transactions":tx_attribution,"edges":edges,"summary":{"accounts_traced":len(accounts),"transactions_processed":len(tx_attribution),"tainted_funds_currently_traced":str(total_taint),"highest_hop":max(distances.values(),default=0),"method":"Proportional taint allocation (research assumption; not LIBR)","risk_model":"Explainable deterministic rules; not trained XGBoost"}}


@app.get("/api/health")
def health(): return {"status":"ok","service":"TraceX API","version":"1.0.0"}

@app.get("/api/dashboard")
def dashboard():
    rows=transactions(); accounts={x["sender"] for x in rows}|{x["receiver"] for x in rows}
    total=sum((Decimal(x["amount"]) for x in rows),Decimal("0"))
    return {"transaction_count":len(rows),"account_count":len(accounts),"transaction_volume":str(total),"case_count":(db().execute("SELECT COUNT(*) FROM cases").fetchone()[0]),"recent_transactions":rows[-8:]}

@app.get("/api/transactions")
def get_transactions(): return transactions()

@app.post("/api/transactions")
def add_transaction(item: TransactionIn):
    try:
        with db() as con:
            con.execute("INSERT INTO transactions(transaction_id,sender,receiver,amount,timestamp) VALUES(?,?,?,?,?)",(item.transaction_id,item.sender,item.receiver,str(item.amount),item.timestamp.isoformat(sep=" ")))
    except sqlite3.IntegrityError: raise HTTPException(409,"Transaction ID already exists")
    return {"status":"created","transaction_id":item.transaction_id}

@app.post("/api/transactions/upload")
async def upload_transactions(file: UploadFile = File(...), replace: bool = False):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(400,"Upload a CSV file")
    raw=(await file.read()).decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(raw)); required={"transaction_id","sender","receiver","amount","timestamp"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)): raise HTTPException(400,"CSV must contain: transaction_id,sender,receiver,amount,timestamp")
    valid=[]
    for n,row in enumerate(reader, start=2):
        try:
            amount=Decimal(row["amount"]); ts=datetime.fromisoformat(row["timestamp"].strip())
            if amount<=0 or not row["transaction_id"].strip() or not row["sender"].strip() or not row["receiver"].strip(): raise ValueError()
            valid.append((row["transaction_id"].strip(),row["sender"].strip(),row["receiver"].strip(),str(amount),ts.isoformat(sep=" ")))
        except (ValueError,InvalidOperation,TypeError): raise HTTPException(400,f"Invalid row {n}")
    with db() as con:
        if replace: con.execute("DELETE FROM transactions")
        try: con.executemany("INSERT INTO transactions(transaction_id,sender,receiver,amount,timestamp) VALUES(?,?,?,?,?)",valid)
        except sqlite3.IntegrityError: raise HTTPException(409,"Duplicate transaction ID in file or database; no rows imported")
    return {"status":"imported","count":len(valid),"replaced":replace}

@app.post("/api/cases")
def create_case(item: CaseIn):
    try:
        with db() as con: con.execute("INSERT INTO cases(case_id,title,origin_account,origin_amount) VALUES(?,?,?,?)",(item.case_id,item.title,item.origin_account,str(item.origin_amount)))
    except sqlite3.IntegrityError: raise HTTPException(409,"Case ID already exists")
    return {"status":"created","case_id":item.case_id}

@app.get("/api/cases")
def list_cases():
    with db() as con: return [dict(x) for x in con.execute("SELECT * FROM cases ORDER BY created_at DESC")]

@app.post("/api/trace")
def trace(item: TraceIn): return trace_result(item,transactions())

@app.get("/api/accounts")
def list_accounts():
    rows=transactions(); names=sorted({x["sender"] for x in rows}|{x["receiver"] for x in rows})
    return [account_risk(name,rows) for name in names]

@app.get("/")
def home(): return FileResponse(FRONTEND/"index.html")

app.mount("/static",StaticFiles(directory=FRONTEND),name="static")
