from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

CATEGORIES = [
    "Income", "Rent & Utilities", "Groceries", "Dining", "Transport", "Shopping",
    "Subscriptions", "Health", "Travel", "Entertainment", "Transfers", "Fees", "Uncategorized",
]


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_transaction_fingerprint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(300))
    merchant: Mapped[str] = mapped_column(String(120), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # negative = money out
    category: Mapped[str] = mapped_column(String(40), index=True)
    category_source: Mapped[str] = mapped_column(String(10))  # rule | ai | user | none
    fingerprint: Mapped[str] = mapped_column(String(64))


class Rule(Base):
    """A merchant -> category mapping learned when the user corrects a category."""
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(40))


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(40), unique=True)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
