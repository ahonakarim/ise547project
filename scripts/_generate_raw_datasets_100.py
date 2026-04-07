"""One-off deterministic generator: expand data/raw/*.csv to >=100 rows each.

Run from repo root: python scripts/_generate_raw_datasets_100.py
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
N = 100


def _u(i: int, salt: int) -> float:
    """Deterministic [0,1) pseudo-random from index."""
    x = (1103515245 * (i + 1) + 12345 + salt * 7919) & 0x7FFFFFFF
    return x / 0x7FFFFFFF


def write_sales() -> None:
    regions = ("West", "East", "South", "North")
    categories = ("Office Supplies", "Apparel", "Electronics", "Furniture")
    path = RAW / "sales_data.csv"
    start = date(2024, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["order_id", "order_date", "region", "category", "sales", "profit", "discount"]
        )
        for i in range(N):
            oid = f"SO-{1000 + i}"
            od = (start + timedelta(days=3 * i)).isoformat()
            region = regions[i % 4]
            category = categories[i % 4]
            u1, u2, u3 = _u(i, 1), _u(i, 2), _u(i, 3)
            sales = round(145.0 + u1 * 285.0, 2)
            profit = round(sales * (0.035 + u2 * 0.24), 2)
            if profit < 2.0:
                profit = round(2.0 + u2 * 18.0, 2)
            # Ensure benchmark filters discount > 0.2 still match some rows
            if i % 11 == 0:
                discount = round(0.21 + (i % 6) * 0.015, 2)
            else:
                discount = round(0.02 + u3 * 0.16, 2)
            w.writerow([oid, od, region, category, sales, profit, discount])


def write_insurance() -> None:
    regions = ("southeast", "southwest", "northeast", "northwest")
    path = RAW / "insurance_data.csv"
    start = date(2024, 1, 3)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["record_id", "record_date", "age", "bmi", "children", "smoker", "region", "charges"]
        )
        for i in range(N):
            rid = f"IN-{2000 + i}"
            rd = (start + timedelta(days=5 * i)).isoformat()
            age = 22 + ((i * 13) % 46)
            if i % 9 == 0:
                age = 66 + (i % 2)
            bmi = round(19.0 + _u(i, 4) * 15.5, 1)
            children = i % 5
            smoker = "yes" if i % 2 == 1 else "no"
            region = regions[i % 4]
            base = 2800.0 + _u(i, 5) * 3200.0
            if smoker == "yes":
                base += 4200.0 + _u(i, 6) * 5200.0
            if age > 55:
                base += 800.0 + _u(i, 7) * 1400.0
            charges = round(base + children * 420.0 + bmi * 95.0, 2)
            w.writerow([rid, rd, age, bmi, children, smoker, region, charges])


def write_retail() -> None:
    channels = ("store", "phone", "online")
    payments = ("wallet", "cash", "card")
    path = RAW / "retail_orders.csv"
    start = date(2024, 2, 1)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["order_id", "order_date", "channel", "payment_method", "items_count", "order_value"]
        )
        for i in range(N):
            oid = f"RO-{3000 + i}"
            od = (start + timedelta(days=2 * i)).isoformat()
            channel = channels[i % 3]
            payment_method = payments[i % 3]
            items_count = 1 + (i % 8)
            u = _u(i, 8)
            unit = 9.0 + u * 16.0
            order_value = round(18.0 + items_count * unit + (i % 7) * 3.1, 2)
            w.writerow([oid, od, channel, payment_method, items_count, order_value])


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    write_sales()
    write_insurance()
    write_retail()
    print(f"Wrote {N}-row datasets to {RAW}")


if __name__ == "__main__":
    main()
