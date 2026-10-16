
from pathlib import Path
from datetime import datetime, timezone
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = ROOT / "warehouse" / "foodflow.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    zone TEXT NOT NULL,
    promised_minutes INTEGER NOT NULL,
    rider_id TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS riders (
    rider_id TEXT PRIMARY KEY,
    rider_name TEXT NOT NULL,
    home_zone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_events (
    event_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    orders_read INTEGER,
    orders_inserted INTEGER,
    riders_read INTEGER,
    riders_inserted INTEGER,
    events_read INTEGER,
    events_inserted INTEGER
);

CREATE VIEW IF NOT EXISTS delivery_facts AS
SELECT
    o.order_id,
    o.created_at,
    o.zone,
    o.promised_minutes,
    o.rider_id,
    o.status,
    MIN(
        CASE WHEN e.event_type = 'picked_up'
        THEN e.event_time END
    ) AS picked_up_at,
    MIN(
        CASE WHEN e.event_type = 'delivered'
        THEN e.event_time END
    ) AS delivered_at,
    MIN(
        CASE WHEN e.event_type = 'cancelled'
        THEN e.event_time END
    ) AS cancelled_at
FROM orders o
LEFT JOIN delivery_events e
    ON o.order_id = e.order_id
GROUP BY o.order_id;
"""


def read_source(filename, columns):
    path = DATA / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. "
            "Run python -m src.generate_data first."
        )

    df = pd.read_csv(path, dtype=str).fillna("")

    missing = set(columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{filename} missing columns: {sorted(missing)}"
        )

    return df[columns]


def run_pipeline():
    DB.parent.mkdir(parents=True, exist_ok=True)

    orders = read_source(
        "orders.csv",
        [
            "order_id", "created_at", "zone",
            "promised_minutes", "rider_id", "status"
        ]
    )

    riders = read_source(
        "riders.csv",
        ["rider_id", "rider_name", "home_zone"]
    )

    events = read_source(
        "delivery_events.csv",
        ["event_id", "order_id", "event_type", "event_time"]
    )

    pd.to_datetime(orders["created_at"], errors="raise")
    pd.to_datetime(events["event_time"], errors="raise")

    orders["promised_minutes"] = pd.to_numeric(
        orders["promised_minutes"], errors="raise"
    ).astype(int)

    if (orders["promised_minutes"] <= 0).any():
        raise ValueError("promised_minutes must be positive")

    if orders["order_id"].duplicated().any():
        raise ValueError("Duplicate order_id in source CSV")

    if riders["rider_id"].duplicated().any():
        raise ValueError("Duplicate rider_id in source CSV")

    if events["event_id"].duplicated().any():
        raise ValueError("Duplicate event_id in source CSV")

    valid_event_types = {
        "created", "assigned", "picked_up",
        "delivered", "cancelled"
    }

    invalid_types = set(events["event_type"]) - valid_event_types

    if invalid_types:
        raise ValueError(f"Invalid event types: {invalid_types}")

    # Reject events referring to orders absent from the source
    # or already stored in the warehouse.
    with sqlite3.connect(DB) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA)

        known_orders = set(
            pd.read_sql_query(
                "SELECT order_id FROM orders", con
            )["order_id"]
        )

        incoming_orders = set(orders["order_id"])
        allowed_orders = known_orders | incoming_orders
        unknown_orders = set(events["order_id"]) - allowed_orders

        if unknown_orders:
            raise ValueError(
                f"Events refer to unknown orders: "
                f"{sorted(unknown_orders)[:5]}"
            )

        counts = []

        batches = [
            ("orders", orders),
            ("riders", riders),
            ("delivery_events", events)
        ]

        for table, df in batches:
            before = con.total_changes

            placeholders = ",".join(["?"] * len(df.columns))

            con.executemany(
                f"INSERT OR IGNORE INTO {table} "
                f"VALUES ({placeholders})",
                df.itertuples(index=False, name=None)
            )

            inserted = con.total_changes - before

            counts.extend([len(df), inserted])

        con.execute(
            """
            INSERT INTO pipeline_runs (
                run_at,
                orders_read, orders_inserted,
                riders_read, riders_inserted,
                events_read, events_inserted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (datetime.now(timezone.utc).isoformat(), *counts)
        )

    result = dict(zip(
        [
            "orders_read", "orders_inserted",
            "riders_read", "riders_inserted",
            "events_read", "events_inserted"
        ],
        counts
    ))

    print("Incremental pipeline complete:", result)
    return result


if __name__ == "__main__":
    run_pipeline()
