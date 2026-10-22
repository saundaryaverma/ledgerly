from tests.conftest import SAMPLE, upload


def test_import_sample_and_reimport_is_idempotent(client):
    text = open(SAMPLE).read()
    first = upload(client, text).json()
    assert first["imported"] == len(text.strip().splitlines()) - 1
    again = upload(client, text).json()
    assert again["imported"] == 0 and again["skipped_duplicates"] == first["imported"]


def test_bad_csv_is_a_clear_422(client):
    r = upload(client, "Date,Description,Amount\nnope,X,1\n")
    assert r.status_code == 422 and "Row 2" in r.json()["detail"]


def test_months_and_transactions(loaded):
    assert loaded.get("/api/months").json() == ["2026-09", "2026-08", "2026-07"]
    txs = loaded.get("/api/transactions", params={"month": "2026-09"}).json()
    assert txs and all(t["date"].startswith("2026-09") for t in txs)
    assert loaded.get("/api/transactions", params={"month": "Sept"}).status_code == 422


def test_summary_math_is_consistent(loaded):
    s = loaded.get("/api/summary", params={"month": "2026-09"}).json()
    assert round(sum(c["amount"] for c in s["by_category"]), 2) == round(s["spending"], 2)
    assert round(s["income"] - s["spending"], 2) == round(s["net"], 2)
    assert s["income"] == 2400.0  # Zelle transfers are excluded from income and spending
    assert all(c["category"] != "Transfers" for c in s["by_category"])
    assert s["insights"]["items"]


def test_correcting_a_category_teaches_the_merchant(loaded):
    txs = loaded.get("/api/transactions", params={"month": "2026-09"}).json()
    book = next(t for t in txs if t["merchant"] == "Kinokuniya Bookstore")
    r = loaded.patch(f"/api/transactions/{book['id']}", json={"category": "Shopping"})
    assert r.status_code == 200
    every_month = [t for m in ("2026-07", "2026-08", "2026-09")
                   for t in loaded.get("/api/transactions", params={"month": m}).json()
                   if t["merchant"] == "Kinokuniya Bookstore"]
    assert every_month and all(t["category"] == "Shopping" and t["category_source"] == "user" for t in every_month)
    new = upload(loaded, "Date,Description,Amount\n10/02/2026,KINOKUNIYA BOOKSTORE NY,-22.00\n").json()
    assert new["categorized_by"]["user"] == 1  # the next import remembers the correction


def test_invalid_category_rejected(loaded):
    t = loaded.get("/api/transactions", params={"month": "2026-09"}).json()[0]
    assert loaded.patch(f"/api/transactions/{t['id']}", json={"category": "Snacks"}).status_code == 422
    assert loaded.patch("/api/transactions/999999", json={"category": "Dining"}).status_code == 404


def test_budget_flows_into_summary_and_insights(loaded):
    assert loaded.put("/api/budgets/Dining", json={"monthly_limit": 50}).status_code == 200
    assert loaded.put("/api/budgets/Income", json={"monthly_limit": 50}).status_code == 422
    assert loaded.put("/api/budgets/Dining", json={"monthly_limit": -5}).status_code == 422
    s = loaded.get("/api/summary", params={"month": "2026-09"}).json()
    dining = next(b for b in s["budgets"] if b["category"] == "Dining")
    assert dining["spent"] > dining["limit"] and dining["remaining"] < 0
    assert any("over your Dining budget" in i for i in s["insights"]["items"])
