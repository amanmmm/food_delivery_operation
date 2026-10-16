
from pathlib import Path
from datetime import datetime, timedelta
import random
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def generate():
    random.seed(19)
    DATA.mkdir(parents=True, exist_ok=True)

    zones = ["North", "Central", "South", "West"]

    riders = pd.DataFrame([
        {
            "rider_id": f"R{i:03d}",
            "rider_name": f"Rider {i:03d}",
            "home_zone": zones[(i - 1) % 4]
        }
        for i in range(1, 13)
    ])

    riders.to_csv(DATA / "riders.csv", index=False)

    orders = []
    events = []
    event_number = 1

    base = datetime(2026, 10, 1, 9, 0)

    for i in range(1, 241):
        created = base + timedelta(
            minutes=random.randint(0, 60 * 24 * 13)
        )

        zone = zones[(i + random.randint(0, 3)) % 4]
        promised = random.choice([25, 30, 35, 40])

        cancelled = random.random() < (
            0.16 if zone == "South" else 0.08
        )

        pickup_delay = random.randint(4, 24)
        if zone == "West":
            pickup_delay += 8

        trip_duration = random.randint(12, 42)
        if zone == "South":
            trip_duration += 12

        rider = random.choice(riders["rider_id"].tolist())

        orders.append({
            "order_id": f"O{i:04d}",
            "created_at": created.isoformat(timespec="seconds"),
            "zone": zone,
            "promised_minutes": promised,
            "rider_id": (
                "" if cancelled and random.random() < 0.25
                else rider
            ),
            "status": "cancelled" if cancelled else "completed"
        })

        if cancelled:
            cancel_time = created + timedelta(
                minutes=random.randint(2, 18)
            )

            events.append({
                "event_id": f"E{event_number:05d}",
                "order_id": f"O{i:04d}",
                "event_type": "cancelled",
                "event_time": cancel_time.isoformat(timespec="seconds")
            })
            event_number += 1
            continue

        assigned = created + timedelta(
            minutes=random.randint(1, 6)
        )

        picked_up = assigned + timedelta(minutes=pickup_delay)
        delivered = picked_up + timedelta(minutes=trip_duration)

        lifecycle = [
            ("created", created),
            ("assigned", assigned),
            ("picked_up", picked_up),
            ("delivered", delivered)
        ]

        for event_type, event_time in lifecycle:
            events.append({
                "event_id": f"E{event_number:05d}",
                "order_id": f"O{i:04d}",
                "event_type": event_type,
                "event_time": event_time.isoformat(timespec="seconds")
            })
            event_number += 1

    pd.DataFrame(orders).to_csv(
        DATA / "orders.csv", index=False
    )

    pd.DataFrame(events).to_csv(
        DATA / "delivery_events.csv", index=False
    )

    print(f"Generated {len(orders)} orders.")
    print(f"Generated {len(riders)} riders.")
    print(f"Generated {len(events)} delivery events.")
    print(f"Files saved in: {DATA}")


if __name__ == "__main__":
    generate()
