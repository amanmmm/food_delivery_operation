
from pathlib import Path
import sqlite3
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "warehouse" / "foodflow.db"


def calculate_metrics(day: str):
    with sqlite3.connect(DB) as con:
        orders = pd.read_sql_query(
            "SELECT * FROM orders", con
        )

        facts = pd.read_sql_query(
            "SELECT * FROM delivery_facts", con
        )

    empty_result = {
        "day": day,
        "total_orders": 0,
        "completed": 0,
        "cancelled": 0,
        "avg_delivery_minutes": None,
        "late_rate_pct": 0.0,
        "cancellation_rate_pct": 0.0,
        "zone_data": [],
        "trend_data": [],
        "evidence": {
            "top_issue": "No orders for this day",
            "detail": "No orders were created on this date.",
            "recommended_action": "Choose a date with order activity."
        }
    }

    if orders.empty:
        return empty_result

    orders["created_at"] = pd.to_datetime(orders["created_at"])
    facts["created_at"] = pd.to_datetime(facts["created_at"])

    for column in [
        "picked_up_at", "delivered_at", "cancelled_at"
    ]:
        facts[column] = pd.to_datetime(
            facts[column], errors="coerce"
        )

    day_orders = orders[
        orders["created_at"].dt.strftime("%Y-%m-%d") == day
    ]

    day_facts = facts[
        facts["created_at"].dt.strftime("%Y-%m-%d") == day
    ].copy()

    if day_orders.empty:
        return empty_result

    total = len(day_orders)

    cancelled = int(
        (day_orders["status"].str.lower() == "cancelled").sum()
    )

    delivered = day_facts.dropna(
        subset=["picked_up_at", "delivered_at"]
    ).copy()

    delivered["delivery_minutes"] = (
        delivered["delivered_at"] - delivered["picked_up_at"]
    ).dt.total_seconds() / 60

    delivered["late"] = (
        delivered["delivery_minutes"]
        > pd.to_numeric(delivered["promised_minutes"])
    )

    avg = (
        round(float(delivered["delivery_minutes"].mean()), 1)
        if not delivered.empty else None
    )

    late_count = int(delivered["late"].sum())

    late_rate = (
        round(late_count / len(delivered) * 100, 1)
        if not delivered.empty else 0.0
    )

    cancellation_rate = round(cancelled / total * 100, 1)

    zone = delivered.groupby(
        "zone", as_index=False
    ).agg(
        avg_minutes=("delivery_minutes", "mean"),
        orders=("order_id", "count")
    )

    zone["avg_minutes"] = zone["avg_minutes"].round(1)

    trend = delivered.groupby(
        delivered["created_at"].dt.hour
    ).agg(
        avg_minutes=("delivery_minutes", "mean"),
        orders=("order_id", "count")
    ).reset_index()

    trend.columns = ["hour", "avg_minutes", "orders"]
    trend["avg_minutes"] = trend["avg_minutes"].round(1)

    # Each candidate has a score, issue name, evidence, and action.
    candidates = [
        (
            cancellation_rate,
            "Elevated cancellations",
            f"{cancelled} of {total} orders were cancelled "
            f"({cancellation_rate}%).",
            "Review cancellation reasons and restaurant readiness "
            "before dispatch."
        ),
        (
            late_rate,
            "Late deliveries",
            f"{late_count} of {len(delivered)} deliveries exceeded "
            f"their promised duration ({late_rate}%).",
            "Inspect pickup waits and route duration for late orders."
        )
    ]

    if not zone.empty:
        slowest = zone.sort_values(
            "avg_minutes", ascending=False
        ).iloc[0]

        candidates.append((
            float(slowest["avg_minutes"]),
            f"Slowest delivery zone: {slowest['zone']}",
            f"{slowest['zone']} averaged "
            f"{slowest['avg_minutes']:.1f} minutes across "
            f"{int(slowest['orders'])} deliveries.",
            f"Review rider coverage and dispatch queues in "
            f"{slowest['zone']}."
        ))

    _, issue, detail, action = max(
        candidates, key=lambda item: item[0]
    )

    return {
        "day": day,
        "total_orders": total,
        "completed": int(day_facts["delivered_at"].notna().sum()),
        "cancelled": cancelled,
        "avg_delivery_minutes": avg,
        "late_rate_pct": late_rate,
        "cancellation_rate_pct": cancellation_rate,
        "zone_data": zone.to_dict("records"),
        "trend_data": trend.to_dict("records"),
        "evidence": {
            "top_issue": issue,
            "detail": detail,
            "recommended_action": action,
            "cancelled": cancelled,
            "total_orders": total,
            "late_rate_pct": late_rate
        }
    }
