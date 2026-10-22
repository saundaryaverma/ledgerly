"""Monthly numbers, budgets, and plain-English insights.

Every insight is built from numbers computed here. If an LLM rewrites the insights to sound
friendlier, verify_numbers() checks that every dollar amount and percentage it wrote matches a
number we computed. If even one doesn't, we throw the rewrite away and show the plain version."""
import json
import os
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models import Budget, Transaction

EXCLUDED = {"Transfers"}  # moving money between your own accounts isn't spending or income


def month_bounds(month):
    y, m = map(int, month.split("-"))
    start = date(y, m, 1)
    end = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return start, end


def previous_month(month):
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _transactions(session, month):
    start, end = month_bounds(month)
    q = select(Transaction).where(Transaction.date >= start, Transaction.date < end).order_by(Transaction.date)
    return session.scalars(q).all()


def summarize(session, month):
    txs = _transactions(session, month)
    income = sum((t.amount for t in txs if t.amount > 0 and t.category not in EXCLUDED), Decimal("0"))
    by_cat, by_merchant, counts = defaultdict(Decimal), defaultdict(Decimal), defaultdict(int)
    for t in txs:
        if t.amount < 0 and t.category not in EXCLUDED:
            by_cat[t.category] += -t.amount
            by_merchant[t.merchant] += -t.amount
            counts[t.category] += 1
    spending = sum(by_cat.values(), Decimal("0"))
    net = income - spending
    return {
        "month": month,
        "income": float(income),
        "spending": float(spending),
        "net": float(net),
        "savings_rate": round(float(net / income) * 100, 1) if income > 0 else None,
        "by_category": [{"category": c, "amount": float(a), "count": counts[c],
                         "share": round(float(a / spending) * 100, 1) if spending else 0.0}
                        for c, a in sorted(by_cat.items(), key=lambda kv: -kv[1])],
        "top_merchants": [{"merchant": m, "amount": float(a)}
                          for m, a in sorted(by_merchant.items(), key=lambda kv: -kv[1])[:5]],
        "transaction_count": len(txs),
        "uncategorized": sum(1 for t in txs if t.category == "Uncategorized"),
    }


def budget_status(session, summary):
    spent = {c["category"]: c["amount"] for c in summary["by_category"]}
    out = []
    for b in session.scalars(select(Budget).order_by(Budget.category)).all():
        limit = float(b.monthly_limit)
        used = spent.get(b.category, 0.0)
        out.append({"category": b.category, "limit": limit, "spent": used,
                    "remaining": round(limit - used, 2), "percent_used": round(used / limit * 100, 1) if limit else 0.0})
    return out


def _money(x):
    return f"${x:,.2f}"


def facts(summary, prior, budgets):
    """Plain, template-written insights. Each carries the exact numbers it states."""
    out = []
    cats = summary["by_category"]
    if cats:
        top = cats[0]
        out.append({"text": f"Your biggest category was {top['category']} at {_money(top['amount'])}, "
                            f"{top['share']}% of your spending.",
                    "numbers": [top["amount"], top["share"]]})
    if summary["savings_rate"] is not None:
        if summary["net"] >= 0:
            out.append({"text": f"You saved {_money(summary['net'])}, {summary['savings_rate']}% of your income.",
                        "numbers": [summary["net"], summary["savings_rate"]]})
        else:
            out.append({"text": f"You spent {_money(-summary['net'])} more than you earned this month.",
                        "numbers": [-summary["net"]]})
    if prior and prior["by_category"]:
        before = {c["category"]: c["amount"] for c in prior["by_category"]}
        changes = [(c["category"], c["amount"], before[c["category"]]) for c in cats
                   if before.get(c["category"])]
        if changes:
            cat, now, then = max(changes, key=lambda x: abs(x[1] - x[2]))
            pct = round((now - then) / then * 100, 1)
            direction = "up" if pct > 0 else "down"
            out.append({"text": f"{cat} was {_money(now)}, {direction} {abs(pct)}% from {_money(then)} last month.",
                        "numbers": [now, abs(pct), then]})
    for b in budgets:
        if b["spent"] > b["limit"]:
            over = round(b["spent"] - b["limit"], 2)
            out.append({"text": f"You're {_money(over)} over your {b['category']} budget of {_money(b['limit'])}.",
                        "numbers": [over, b["limit"]]})
    subs = next((c for c in cats if c["category"] == "Subscriptions"), None)
    if subs:
        out.append({"text": f"Subscriptions cost {_money(subs['amount'])} across {subs['count']} charges.",
                    "numbers": [subs["amount"], subs["count"]]})
    return out


_NUM = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?(%?)")


def verify_numbers(text, allowed):
    """True only if every number in the text matches one we computed (to the cent, or 0.1 for %)."""
    for value, pct in _NUM.findall(text):
        n = float(value.replace(",", ""))
        tol = 0.051 if pct else 0.005
        if not any(abs(n - a) <= tol or (not pct and abs(n - round(a)) < 0.5 and n == round(n)) for a in allowed):
            return False
    return True


def llm_rewriter():
    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL") or None)
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    def rewrite(fact_texts):
        prompt = ("Rewrite these personal finance facts as short, friendly sentences, one per line. "
                  "Use only the numbers given, written exactly as given. Do not add any new numbers.\n\n"
                  + "\n".join(fact_texts))
        resp = client.chat.completions.create(model=model, temperature=0.3,
                                              messages=[{"role": "user", "content": prompt}])
        return [l.strip("-• ").strip() for l in resp.choices[0].message.content.splitlines() if l.strip()]

    return rewrite


def insights(summary, prior, budgets, rewrite=None):
    base = facts(summary, prior, budgets)
    allowed = [n for f in base for n in f["numbers"]]
    if rewrite and base:
        try:
            lines = rewrite([f["text"] for f in base])
        except Exception:
            lines = []
        if lines and all(verify_numbers(l, allowed) for l in lines):
            return {"source": "ai", "verified": True, "items": lines}
        return {"source": "template", "verified": True, "items": [f["text"] for f in base],
                "note": "AI rewrite discarded: it contained a number we could not verify."}
    return {"source": "template", "verified": True, "items": [f["text"] for f in base]}
