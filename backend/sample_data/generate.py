"""Writes sample_data/transactions.csv: three months of invented transactions for a New York
graduate student, in the messy format banks really export. Fixed seed, so it's reproducible."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

rng = random.Random(42)
MONTHS = [(2026, 7), (2026, 8), (2026, 9)]
RECURRING = [  # (day, description, amount)
    (1, "RENT PAYMENT - 512 W 112TH ST", -1450.00),
    (3, "CON ED OF NY 800-752-6633", None),
    (5, "SPOTIFY USA 877-778-1161", -11.99),
    (9, "NETFLIX.COM 866-579-7172 CA", -15.49),
    (12, "VERIZON WIRELESS PAYMENTS", -65.00),
    (15, "PAYROLL NYU GRAD STIPEND DIRECT DEP", 2400.00),
    (18, "APPLE.COM/BILL 866-712-7753 CA", -2.99),
    (20, "CHATGPT SUBSCRIPTION OPENAI", -20.00),
    (28, "PLANET FITNESS 844-880-7180", -24.99),
]
VARIABLE = [  # (description, low, high, times per month)
    ("SQ *BLUE BOTTLE COFFEE 8823 NY", 4.5, 7.5, 9),
    ("STARBUCKS STORE 11823", 4.0, 8.0, 5),
    ("TRADER JOE'S #540 NEW YORK NY", 28, 85, 4),
    ("KEY FOOD SUPERMARKET 0231", 12, 40, 3),
    ("TST* JOE'S PIZZA BROADWAY", 4.5, 14, 4),
    ("SWEETGREEN 2937 NEW YORK NY", 13, 18, 3),
    ("DOORDASH*CHIPOTLE", 16, 32, 3),
    ("MTA*NYCT PAYGO", 2.9, 2.9, 22),
    ("UBER *TRIP HELP.UBER.COM", 11, 34, 2),
    ("AMAZON MKTPL*2K4L19 AMZN.COM/BILL WA", 9, 70, 3),
    ("CVS/PHARMACY #02931", 6, 30, 2),
    ("KINOKUNIYA BOOKSTORE NY", 15, 45, 1),
    ("NYU BOOKSTORE 70 WASHINGTON", 20, 90, 1),
]


def rows():
    for y, m in MONTHS:
        for day, desc, amt in RECURRING:
            if amt is None:
                amt = -round(rng.uniform(48, 95), 2)
            yield date(y, m, day), desc, amt
        for desc, lo, hi, n in VARIABLE:
            n = max(1, n + rng.randint(-1, 2)) if n > 1 else rng.randint(0, 1)
            for _ in range(n):
                yield date(y, m, rng.randint(1, 28)), desc, -round(rng.uniform(lo, hi), 2)
        yield date(y, m, rng.randint(2, 27)), f"ZELLE TO PRIYA S {rng.randint(1000, 9999)}", -round(rng.uniform(20, 120), 2)
        if m == 8:  # a summer trip, so month-over-month changes have something to show
            yield date(y, m, 14), "JETBLUE 2792139884512", -238.40
            yield date(y, m, 16), "AIRBNB * HMQ4X2 SAN FRANCISCO CA", -412.00
            for _ in range(4):
                yield date(y, m, rng.randint(14, 19)), "DOORDASH*THAI DIner", -round(rng.uniform(18, 35), 2)


if __name__ == "__main__":
    out = Path(__file__).parent / "transactions.csv"
    data = sorted(rows())
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Description", "Amount"])
        for d, desc, amt in data:
            w.writerow([d.strftime("%m/%d/%Y"), desc, f"{amt:.2f}"])
    print(f"wrote {len(data)} rows to {out}")
