from app.analytics import facts, insights, previous_month, verify_numbers

SUMMARY = {"income": 2400.0, "spending": 2100.0, "net": 300.0, "savings_rate": 12.5, "transaction_count": 10,
           "by_category": [{"category": "Rent & Utilities", "amount": 1600.0, "share": 76.2, "count": 3},
                           {"category": "Dining", "amount": 300.0, "share": 14.3, "count": 12},
                           {"category": "Subscriptions", "amount": 50.47, "share": 2.4, "count": 4}]}
PRIOR = {"by_category": [{"category": "Dining", "amount": 450.0, "share": 20, "count": 15}], "transaction_count": 8}


def test_previous_month_wraps_year():
    assert previous_month("2026-01") == "2025-12" and previous_month("2026-09") == "2026-08"


def test_facts_state_computed_numbers():
    texts = [f["text"] for f in facts(SUMMARY, PRIOR, [])]
    assert "Your biggest category was Rent & Utilities at $1,600.00, 76.2% of your spending." in texts
    assert "You saved $300.00, 12.5% of your income." in texts
    assert "Dining was $300.00, down 33.3% from $450.00 last month." in texts


def test_verifier_accepts_only_known_numbers():
    allowed = [1600.0, 76.2, 300.0, 12.5]
    assert verify_numbers("You saved $300 this month, about 12.5% of your pay.", allowed)
    assert not verify_numbers("You saved $350 this month.", allowed)
    assert not verify_numbers("Rent was 80% of spending.", allowed)


def test_ai_rewrite_kept_when_numbers_check_out():
    out = insights(SUMMARY, PRIOR, [], rewrite=lambda lines: ["Nice! You saved $300.00, 12.5% of your income."])
    assert out["source"] == "ai"


def test_ai_rewrite_with_invented_number_is_discarded():
    out = insights(SUMMARY, PRIOR, [], rewrite=lambda lines: ["You saved $310 - great job!"])
    assert out["source"] == "template" and "discarded" in out["note"]


def test_over_budget_fact():
    budgets = [{"category": "Dining", "limit": 250.0, "spent": 300.0, "remaining": -50.0, "percent_used": 120.0}]
    assert any("$50.00 over your Dining budget" in f["text"] for f in facts(SUMMARY, None, budgets))
