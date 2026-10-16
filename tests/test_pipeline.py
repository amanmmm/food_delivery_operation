
import sqlite3

from src.pipeline import run_pipeline, DB
from src.generate_data import generate


def setup_module():
    # Start tests with a fresh local database.
    if DB.exists():
        DB.unlink()

    generate()


def test_incremental_pipeline_is_idempotent():
    first = run_pipeline()
    second = run_pipeline()

    assert first["events_inserted"] > 0
    assert second["events_inserted"] == 0
    assert second["orders_inserted"] == 0
    assert second["riders_inserted"] == 0


def test_events_have_unique_ids_and_valid_orders():
    with sqlite3.connect(DB) as con:
        event_count = con.execute(
            "SELECT COUNT(*) FROM delivery_events"
        ).fetchone()[0]

        unique_count = con.execute(
            "SELECT COUNT(DISTINCT event_id) FROM delivery_events"
        ).fetchone()[0]

        missing_orders = con.execute("""
            SELECT COUNT(*)
            FROM delivery_events e
            LEFT JOIN orders o ON e.order_id = o.order_id
            WHERE o.order_id IS NULL
        """).fetchone()[0]

    assert event_count == unique_count
    assert missing_orders == 0


def test_delivery_duration_is_positive():
    with sqlite3.connect(DB) as con:
        row = con.execute("""
            SELECT
                (julianday(delivered_at) -
                 julianday(picked_up_at)) * 1440
            FROM delivery_facts
            WHERE delivered_at IS NOT NULL
              AND picked_up_at IS NOT NULL
            LIMIT 1
        """).fetchone()

    assert row is not None
    assert row[0] > 0
