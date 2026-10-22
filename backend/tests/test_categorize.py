import pytest

from app.categorize import categorize, clean_merchant, validate_llm_category


@pytest.mark.parametrize("raw,clean", [
    ("SQ *BLUE BOTTLE COFFEE 8823 NY", "Blue Bottle Coffee"),
    ("TRADER JOE'S #540 NEW YORK NY", "Trader Joe's"),
    ("NETFLIX.COM 866-579-7172 CA", "Netflix"),
    ("AMAZON MKTPL*2K4L19 AMZN.COM/BILL WA", "Amazon"),
    ("UBER *TRIP HELP.UBER.COM", "Uber"),
    ("CVS/PHARMACY #02931", "CVS Pharmacy"),
    ("RENT PAYMENT - 512 W 112TH ST", "Rent"),
])
def test_clean_merchant(raw, clean):
    assert clean_merchant(raw) == clean


def test_keyword_rules_and_income():
    assert categorize("TRADER JOE'S #540", -40, {})[1:] == ("Groceries", "rule")
    assert categorize("PAYROLL NYU DIRECT DEP", 2400, {})[1:] == ("Income", "rule")
    assert categorize("ZELLE TO PRIYA", -50, {})[1] == "Transfers"


def test_keyword_match_respects_word_boundaries():
    # 'fee' must not match inside 'coffee'
    assert categorize("BLUE BOTTLE COFFEE", -5, {})[1] == "Dining"


def test_learned_rule_beats_keywords():
    assert categorize("STARBUCKS STORE 11823", -6, {"starbucks": "Groceries"})[1:] == ("Groceries", "user")


def test_unknown_merchant_without_ai_is_uncategorized():
    assert categorize("KINOKUNIYA BOOKSTORE NY", -30, {})[1:] == ("Uncategorized", "none")


def test_ai_answer_must_be_a_real_category():
    assert categorize("KINOKUNIYA BOOKSTORE", -30, {}, lambda d, a: "Shopping")[1:] == ("Shopping", "ai")
    assert categorize("KINOKUNIYA BOOKSTORE", -30, {}, lambda d, a: "Books & Hobbies")[1:] == ("Uncategorized", "none")
    assert validate_llm_category(" groceries. ") == "Groceries"
    assert validate_llm_category("Groceries or Dining") is None


def test_ai_failure_falls_back_safely():
    def broken(d, a):
        raise TimeoutError
    assert categorize("KINOKUNIYA BOOKSTORE", -30, {}, broken)[1] == "Uncategorized"
