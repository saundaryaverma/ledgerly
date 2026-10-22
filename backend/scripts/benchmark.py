"""Measures import speed and summary latency against a running Ledgerly API.

    python scripts/benchmark.py --url http://localhost:8000 --rows 10000

Builds a synthetic CSV by resampling sample_data/transactions.csv across two years."""
import argparse
import csv
import io
import random
import statistics
import time
from pathlib import Path

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://localhost:8000")
ap.add_argument("--rows", type=int, default=10_000)
args = ap.parse_args()

rng = random.Random(1)
src = list(csv.DictReader(open(Path(__file__).parents[1] / "sample_data" / "transactions.csv")))
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["Date", "Description", "Amount"])
for i in range(args.rows):
    r = rng.choice(src)
    w.writerow([f"{rng.randint(1, 12):02d}/{rng.randint(1, 28):02d}/{2024 + i % 2}", r["Description"],
                f"{float(r['Amount']) * rng.uniform(0.8, 1.2):.2f}"])

c = httpx.Client(base_url=args.url, timeout=300)
t = time.perf_counter()
res = c.post("/api/import", files={"file": ("bench.csv", buf.getvalue().encode(), "text/csv")}).json()
print(f"import: {res['imported']} rows in {time.perf_counter() - t:.2f}s, categorized by {res['categorized_by']}")
lat = []
for _ in range(50):
    t = time.perf_counter()
    c.get("/api/summary", params={"month": "2025-06"})
    lat.append((time.perf_counter() - t) * 1000)
lat.sort()
print(f"summary latency: p50 {statistics.median(lat):.1f} ms, p95 {lat[int(0.95 * len(lat)) - 1]:.1f} ms")
