"""Ledgerly API.

POST  /api/import              upload a bank CSV
GET   /api/months              months that have data
GET   /api/transactions        list a month's transactions
PATCH /api/transactions/{id}   fix a category (Ledgerly remembers the merchant)
GET   /api/summary             income, spending, savings rate, categories, budgets, insights
PUT   /api/budgets/{category}  set a monthly budget"""
import re
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import analytics, categorize, csv_import
from app.db import Base, engine, get_session
from app.models import CATEGORIES, Budget, Rule, Transaction

app = FastAPI(title="Ledgerly")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(engine)

_ASK = categorize.llm_categorizer()
_REWRITE = analytics.llm_rewriter()
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


class CategoryUpdate(BaseModel):
    category: str


class BudgetIn(BaseModel):
    monthly_limit: float = Field(gt=0, le=1_000_000)


def _tx(t):
    return {"id": t.id, "date": t.date.isoformat(), "description": t.description, "merchant": t.merchant,
            "amount": float(t.amount), "category": t.category, "category_source": t.category_source}


@app.get("/api/categories")
def categories():
    return CATEGORIES


@app.post("/api/import")
async def import_csv(file: UploadFile, session: Session = Depends(get_session)):
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(413, "File too large (5 MB max).")
    try:
        rows = csv_import.parse(raw.decode("utf-8", errors="replace"))
    except csv_import.ImportError_ as e:
        raise HTTPException(422, str(e))
    learned = {r.merchant.lower(): r.category for r in session.scalars(select(Rule))}
    existing = set(session.scalars(select(Transaction.fingerprint)))
    added, sources = 0, {"user": 0, "rule": 0, "ai": 0, "none": 0}
    for row in rows:
        if row["fingerprint"] in existing:
            continue
        merchant, category, source = categorize.categorize(row["description"], row["amount"], learned, _ASK)
        session.add(Transaction(merchant=merchant, category=category, category_source=source, **row))
        existing.add(row["fingerprint"])
        sources[source] += 1
        added += 1
    session.commit()
    return {"imported": added, "skipped_duplicates": len(rows) - added, "categorized_by": sources}


@app.get("/api/months")
def months(session: Session = Depends(get_session)):
    dates = session.scalars(select(Transaction.date)).all()
    return sorted({d.strftime("%Y-%m") for d in dates}, reverse=True)


@app.get("/api/transactions")
def list_transactions(month: str, session: Session = Depends(get_session)):
    if not re.match(MONTH, month):
        raise HTTPException(422, "month must look like 2026-09")
    start, end = analytics.month_bounds(month)
    q = select(Transaction).where(Transaction.date >= start, Transaction.date < end).order_by(Transaction.date.desc())
    return [_tx(t) for t in session.scalars(q)]


@app.patch("/api/transactions/{tx_id}")
def update_category(tx_id: int, body: CategoryUpdate, session: Session = Depends(get_session)):
    if body.category not in CATEGORIES:
        raise HTTPException(422, f"category must be one of {CATEGORIES}")
    t = session.get(Transaction, tx_id)
    if not t:
        raise HTTPException(404, "Transaction not found")
    rule = session.scalar(select(Rule).where(func.lower(Rule.merchant) == t.merchant.lower()))
    if rule:
        rule.category = body.category
    else:
        session.add(Rule(merchant=t.merchant, category=body.category))
    # Apply the correction to every transaction from this merchant the user hasn't set by hand.
    same = session.scalars(select(Transaction).where(func.lower(Transaction.merchant) == t.merchant.lower()))
    updated = 0
    for other in same:
        if other.id == t.id or other.category_source != "user":
            other.category, other.category_source = body.category, "user"
            updated += 1
    session.commit()
    return {"updated": updated, "learned_rule": {"merchant": t.merchant, "category": body.category}}


@app.put("/api/budgets/{category}")
def set_budget(category: str, body: BudgetIn, session: Session = Depends(get_session)):
    if category not in CATEGORIES or category in ("Income", "Transfers"):
        raise HTTPException(422, "Pick a spending category")
    b = session.scalar(select(Budget).where(Budget.category == category))
    if b:
        b.monthly_limit = Decimal(str(body.monthly_limit))
    else:
        session.add(Budget(category=category, monthly_limit=Decimal(str(body.monthly_limit))))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Budget changed at the same time; try again")
    return {"category": category, "monthly_limit": body.monthly_limit}


@app.get("/api/summary")
def summary(month: str, session: Session = Depends(get_session)):
    if not re.match(MONTH, month):
        raise HTTPException(422, "month must look like 2026-09")
    s = analytics.summarize(session, month)
    prior = analytics.summarize(session, analytics.previous_month(month))
    budgets = analytics.budget_status(session, s)
    return {**s, "budgets": budgets,
            "insights": analytics.insights(s, prior if prior["transaction_count"] else None, budgets, _REWRITE)}
