from decimal import Decimal

import pytest

from app.csv_import import ImportError_, parse


def test_signed_amount_and_formats():
    rows = parse("Date,Description,Amount\n09/03/2026,COFFEE,-4.50\n2026-09-04,PAYROLL,\"$2,400.00\"\n")
    assert [r["amount"] for r in rows] == [Decimal("-4.50"), Decimal("2400.00")]
    assert rows[1]["date"].isoformat() == "2026-09-04"


def test_debit_credit_columns_and_parentheses():
    rows = parse("Posted Date,Payee,Debit,Credit\n09/01/2026,RENT,1450.00,\n09/15/2026,PAYROLL,,2400\n09/16/2026,REFUND,(12.00),\n")
    assert [r["amount"] for r in rows] == [Decimal("-1450.00"), Decimal("2400.00"), Decimal("-12.00")]


def test_identical_purchases_same_day_are_both_kept():
    rows = parse("Date,Description,Amount\n09/03/2026,MTA,-2.90\n09/03/2026,MTA,-2.90\n")
    assert len({r["fingerprint"] for r in rows}) == 2


def test_bad_row_reports_row_number():
    with pytest.raises(ImportError_, match="Row 3"):
        parse("Date,Description,Amount\n09/03/2026,COFFEE,-4.50\nnot a date,X,-1\n")


def test_missing_columns():
    with pytest.raises(ImportError_, match="Date column"):
        parse("When,What,Amount\n1,2,3\n")
