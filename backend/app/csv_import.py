"""Reads bank CSV exports. Handles the two common layouts:
a single signed Amount column, or separate Debit and Credit columns."""
import csv
import hashlib
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d %b %Y")


class ImportError_(ValueError):
    pass


def _date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    raise ImportError_(f"Unrecognized date: {text!r}")


def _money(text):
    cleaned = (text or "").replace("$", "").replace(",", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    if not cleaned:
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ImportError_(f"Unrecognized amount: {text!r}")


def parse(content):
    """Returns a list of dicts: date, description, amount, fingerprint. Raises ImportError_ with
    the row number on bad data, so the user knows exactly what to fix."""
    reader = csv.DictReader(io.StringIO(content.lstrip("﻿")))
    if not reader.fieldnames:
        raise ImportError_("The file is empty.")
    cols = {f.strip().lower(): f for f in reader.fieldnames}
    date_col = next((cols[c] for c in ("date", "transaction date", "posted date") if c in cols), None)
    desc_col = next((cols[c] for c in ("description", "name", "memo", "payee") if c in cols), None)
    if not date_col or not desc_col:
        raise ImportError_("Need a Date column and a Description column.")
    rows, seen = [], {}
    for n, row in enumerate(reader, start=2):
        try:
            if "amount" in cols:
                amount = _money(row[cols["amount"]])
            elif "debit" in cols or "credit" in cols:
                debit = _money(row.get(cols.get("debit", ""), "")) or Decimal("0")
                credit = _money(row.get(cols.get("credit", ""), "")) or Decimal("0")
                amount = credit - abs(debit)
            else:
                raise ImportError_("Need an Amount column, or Debit and Credit columns.")
            if amount is None:
                continue
            d, desc = _date(row[date_col]), row[desc_col].strip()
        except ImportError_ as e:
            raise ImportError_(f"Row {n}: {e}") from None
        key = f"{d}|{desc}|{amount}"
        seen[key] = seen.get(key, 0) + 1  # the same coffee twice in one day is two real purchases
        fingerprint = hashlib.sha256(f"{key}|{seen[key]}".encode()).hexdigest()
        rows.append({"date": d, "description": desc, "amount": amount, "fingerprint": fingerprint})
    return rows
