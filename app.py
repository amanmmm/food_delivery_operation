
import html
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import run_pipeline, DB


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FoodFlow | Operations Dashboard",
    page_icon="🍃",
    layout="wide",
)


# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

    .stApp {
        background: #f3f7fb;
        color: #19384a;
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: #103746;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    .hero {
        background: linear-gradient(120deg, #103746, #168b7c);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 24px;
        color: white;
    }

    .hero h1 {
        color: white !important;
        font-size: 34px;
        margin: 8px 0;
    }

    .hero p {
        color: #e2f4f1 !important;
        font-size: 15px;
    }

    .kicker {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2.5px;
        color: #0c8b80 !important;
        text-transform: uppercase;
    }

    .section-title {
        color: #17394a !important;
        font-size: 23px;
        font-weight: 800;
        margin-top: 25px;
        margin-bottom: 5px;
    }

    .section-subtitle {
        color: #657d8d !important;
        font-size: 13px;
        margin-bottom: 16px;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dce7ee;
        border-radius: 16px;
        padding: 20px;
        min-height: 120px;
        box-shadow: 0 5px 16px rgba(20, 55, 72, 0.05);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p {
        color: #526b7b !important;
        opacity: 1 !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div {
        color: #12384b !important;
        font-weight: 800 !important;
    }

    .summary-card {
        background: white;
        border: 1px solid #dce7ee;
        border-left: 5px solid #168b7c;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        color: #203746 !important;
        box-shadow: 0 5px 16px rgba(20, 55, 72, 0.05);
    }

    .summary-card h3,
    .summary-card p,
    .summary-card strong {
        color: #203746 !important;
        opacity: 1 !important;
        line-height: 1.7;
    }

    .footer {
        text-align: center;
        color: #718394 !important;
        font-size: 12px;
        padding: 30px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE HELPERS
# =========================================================

def read_table(table_name):
    """Read a database table safely."""
    if not Path(DB).exists():
        return pd.DataFrame()

    allowed_tables = {
        "orders",
        "riders",
        "delivery_events",
        "pipeline_runs",
    }

    if table_name not in allowed_tables:
        return pd.DataFrame()

    try:
        with sqlite3.connect(DB) as con:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name}",
                con,
            )
    except Exception:
        return pd.DataFrame()


def get_column(df, possible_names):
    """Find a column without assuming a particular capitalization."""
    lookup = {str(c).lower(): c for c in df.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def safe_text(value):
    """Escape text before showing it inside an HTML card."""
    return html.escape(str(value))


def to_minutes(value):
    """Convert a value to a number of minutes."""
    if pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🍃 FoodFlow")
    st.caption("Delivery operations intelligence")
    st.divider()

    st.markdown("### Pipeline")

    if st.button("▶ Run data pipeline", use_container_width=True):
        try:
            with st.spinner("Processing delivery data..."):
                run_pipeline()

            st.success("Pipeline completed.")
            st.rerun()

        except Exception as exc:
            st.error(f"Pipeline failed: {exc}")

    st.divider()
    st.markdown("### Dashboard")
    st.write("📦 Order overview")
    st.write("🚚 Delivery performance")
    st.write("❌ Cancellation analysis")
    st.write("📍 Zone comparison")
    st.write("💡 Operational summary")


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div style="font-size:11px;letter-spacing:3px;font-weight:800;color:#b8e8df;">
            FOODFLOW · DATA ENGINEERING
        </div>
        <h1>Food Delivery Operations</h1>
        <p>
            Monitor delivery performance, identify operational bottlenecks,
            and turn daily delivery data into actionable decisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD DATA
# =========================================================

orders = read_table("orders")
events = read_table("delivery_events")
riders = read_table("riders")

if orders.empty:
    st.warning("No orders were found in the database.")

    st.markdown("### Initialize the project")

    st.code(
        "python -m src.generate_data\n"
        "python -m src.pipeline\n"
        "streamlit run app.py",
        language="powershell",
    )

    st.stop()


# =========================================================
# IDENTIFY ORDER COLUMNS
# =========================================================

id_col = get_column(orders, ["order_id", "id"])
created_col = get_column(orders, ["created_at", "order_time"])
status_col = get_column(orders, ["status", "order_status"])
promised_col = get_column(
    orders,
    ["promised_minutes", "promised_duration", "delivery_promise_minutes"],
)
zone_col = get_column(orders, ["zone", "delivery_zone", "zone_name"])
rider_col = get_column(orders, ["rider_id"])

if created_col:
    orders[created_col] = pd.to_datetime(
        orders[created_col],
        errors="coerce",
    )
    orders["_day"] = orders[created_col].dt.strftime("%Y-%m-%d")
else:
    orders["_day"] = "Unknown"


# =========================================================
# DELIVERY EVENT PROCESSING
# =========================================================

event_order_col = get_column(events, ["order_id"])
event_type_col = get_column(events, ["event_type", "event", "status"])
event_time_col = get_column(events, ["event_time", "timestamp", "created_at"])

delivered_times = {}
pickup_times = {}

if (
    not events.empty
    and event_order_col
    and event_type_col
    and event_time_col
):
    events[event_time_col] = pd.to_datetime(
        events[event_time_col],
        errors="coerce",
    )

    event_names = (
        events[event_type_col]
        .astype(str)
        .str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
    )

    delivered_rows = events[
        event_names.isin(["delivered", "delivery_completed", "completed"])
    ]

    pickup_rows = events[
        event_names.isin(["picked_up", "pickup", "pickedup"])
    ]

    delivered_times = (
        delivered_rows.sort_values(event_time_col)
        .groupby(event_order_col)[event_time_col]
        .last()
        .to_dict()
    )

    pickup_times = (
        pickup_rows.sort_values(event_time_col)
        .groupby(event_order_col)[event_time_col]
        .last()
        .to_dict()
    )


# =========================================================
# DATE FILTER
# =========================================================

available_dates = sorted(
    orders["_day"].dropna().unique().tolist(),
    reverse=True,
)

available_dates = [d for d in available_dates if d != "Unknown"]

if not available_dates:
    st.error("Order timestamps could not be read from the database.")
    st.stop()

st.markdown(
    '<div class="kicker">Reporting period</div>',
    unsafe_allow_html=True,
)

selected_day = st.selectbox(
    "Select operational date",
    available_dates,
)

day_orders = orders[orders["_day"] == selected_day].copy()

if day_orders.empty:
    st.info("There are no orders for this date.")
    st.stop()


# =========================================================
# NORMALIZE ORDER STATUS
# =========================================================

if status_col:
    day_orders["_status"] = (
        day_orders[status_col]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )
else:
    day_orders["_status"] = ""

completed_statuses = {
    "delivered",
    "completed",
    "complete",
    "success",
}

canceled_statuses = {
    "canceled",
    "cancelled",
    "cancellation",
}

day_orders["_is_canceled"] = day_orders["_status"].isin(
    canceled_statuses
)

day_orders["_is_completed"] = day_orders["_status"].isin(
    completed_statuses
)

total_orders = len(day_orders)
canceled = int(day_orders["_is_canceled"].sum())
completed = int(day_orders["_is_completed"].sum())

# If status is not stored on orders, use delivery events to identify
# delivered orders. Do not infer cancellations from missing events.
if not status_col or completed == 0:
    if id_col and delivered_times:
        completed = int(
            day_orders[id_col].astype(str).isin(
                [str(k) for k in delivered_times]
            ).sum()
        )

# Correct cancellation rate: canceled orders / all orders.
cancel_rate = (
    (canceled / total_orders) * 100
    if total_orders > 0
    else 0.0
)


# =========================================================
# DELIVERY DURATIONS AND LATE ORDERS
# =========================================================

day_orders["_delivery_minutes"] = None
day_orders["_late"] = False

for index, order in day_orders.iterrows():
    order_id = order[id_col] if id_col else None

    if order_id is None:
        continue

    delivered_at = delivered_times.get(order_id)
    pickup_at = pickup_times.get(order_id)

    created_at = order[created_col] if created_col else None

    # Delivery time is pickup-to-delivery when both events exist.
    # Otherwise use order-created-to-delivered.
    start_time = pickup_at if pickup_at is not None else created_at

    if delivered_at is not None and start_time is not None:
        try:
            duration = (
                pd.Timestamp(delivered_at) - pd.Timestamp(start_time)
            ).total_seconds() / 60

            if duration >= 0:
                day_orders.at[index, "_delivery_minutes"] = duration
        except (TypeError, ValueError):
            pass

    # Compare total order duration against promised duration.
    # This avoids comparing pickup-to-delivery time with a promise
    # that may start at order creation.
    if (
        delivered_at is not None
        and created_at is not None
        and promised_col
    ):
        try:
            promise = float(order[promised_col])
            total_duration = (
                pd.Timestamp(delivered_at) - pd.Timestamp(created_at)
            ).total_seconds() / 60

            if promise > 0 and total_duration > promise:
                day_orders.at[index, "_late"] = True
        except (TypeError, ValueError):
            pass


# If a promise column exists, calculate late rate from order-level
# comparisons. Otherwise show a safe zero rather than guessing.
completed_rows = day_orders[day_orders["_is_completed"]]

if promised_col and not completed_rows.empty:
    late_rate = (
        completed_rows["_late"].astype(bool).sum()
        / len(completed_rows)
        * 100
    )
else:
    late_rate = 0.0

durations = pd.to_numeric(
    day_orders["_delivery_minutes"],
    errors="coerce",
).dropna()

avg_duration = float(durations.mean()) if not durations.empty else 0.0


# =========================================================
# KPI CARDS
# =========================================================

st.markdown(
    '<div class="section-title">Daily performance</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-subtitle">Operational snapshot for {safe_text(selected_day)}</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Total orders", f"{total_orders:,}")

with k2:
    st.metric("Delivered orders", f"{completed:,}")

with k3:
    st.metric(
        "Average delivery time",
        f"{avg_duration:.1f} min" if avg_duration else "N/A",
    )

with k4:
    st.metric("Canceled orders", f"{canceled:,}")


# =========================================================
# DELIVERY HEALTH
# =========================================================

st.markdown(
    '<div class="section-title">Delivery health</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">Understand delays and cancellations at a glance.</div>',
    unsafe_allow_html=True,
)

health1, health2 = st.columns(2)

with health1:
    st.markdown("**⏱️ Late delivery rate**")
    st.progress(min(max(late_rate / 100, 0), 1))
    st.markdown(f"**{late_rate:.1f}%** of delivered orders were late.")

    if not promised_col:
        st.caption(
            "Late rate requires a promised-duration column in the orders table."
        )
    elif late_rate > 0:
        st.warning("Some orders exceeded their promised duration.")
    else:
        st.success("No late deliveries were identified by the available data.")

with health2:
    st.markdown("**❌ Cancellation rate**")
    st.progress(min(max(cancel_rate / 100, 0), 1))
    st.markdown(
        f"**{cancel_rate:.1f}%** of orders were canceled "
        f"({canceled} of {total_orders})."
    )

    if canceled > 0:
        st.warning(
            f"{canceled} canceled orders detected. "
            "Review cancellation reasons and patterns."
        )
    else:
        st.success("No canceled orders were recorded for this date.")


# =========================================================
# CHARTS
# =========================================================

st.markdown(
    '<div class="section-title">Explore operations</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">A visual breakdown of the selected day.</div>',
    unsafe_allow_html=True,
)

chart1, chart2 = st.columns(2)

with chart1:
    status_df = pd.DataFrame({
        "Status": ["Delivered", "Canceled", "Other / In progress"],
        "Orders": [
            completed,
            canceled,
            max(total_orders - completed - canceled, 0),
        ],
    })

    status_df = status_df[status_df["Orders"] > 0]

    if not status_df.empty:
        fig = px.pie(
            status_df,
            names="Status",
            values="Orders",
            hole=0.60,
            title="Order status breakdown",
            color="Status",
            color_discrete_map={
                "Delivered": "#168b7c",
                "Canceled": "#e36b78",
                "Other / In progress": "#e7b45c",
            },
        )

        fig.update_traces(
            textinfo="label+percent",
            textposition="outside",
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#203746",
            margin=dict(l=15, r=15, t=55, b=15),
            height=350,
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No order status data is available.")


with chart2:
    if zone_col and zone_col in day_orders.columns:
        zone_df = day_orders.copy()

        zone_df["_delivered_count"] = zone_df["_is_completed"].astype(int)

        zone_stats = (
            zone_df.groupby(zone_col, dropna=False)
            .agg(
                Orders=(zone_col, "size"),
                Delivered=("_delivered_count", "sum"),
                Canceled=("_is_canceled", "sum"),
            )
            .reset_index()
        )

        zone_stats[zone_col] = (
            zone_stats[zone_col].fillna("Unknown").astype(str)
        )

        fig = px.bar(
            zone_stats,
            x=zone_col,
            y=["Delivered", "Canceled"],
            barmode="group",
            title="Delivered and canceled orders by zone",
            color_discrete_map={
                "Delivered": "#168b7c",
                "Canceled": "#e36b78",
            },
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#203746",
            margin=dict(l=15, r=15, t=55, b=15),
            height=350,
            legend_title_text="Order status",
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("**Orders by status**")
        st.info(
            "Add a zone column to the orders table to compare operational "
            "performance across zones."
        )


# =========================================================
# HOURLY ORDERS
# =========================================================

if created_col:
    st.markdown(
        '<div class="section-title">Order activity by hour</div>',
        unsafe_allow_html=True,
    )

    hourly_df = day_orders.dropna(subset=[created_col]).copy()

    if not hourly_df.empty:
        hourly_df["Hour"] = hourly_df[created_col].dt.hour

        hourly_counts = (
            hourly_df.groupby("Hour")
            .size()
            .reset_index(name="Orders")
        )

        fig = px.bar(
            hourly_counts,
            x="Hour",
            y="Orders",
            title="Orders created throughout the day",
            color_discrete_sequence=["#168b7c"],
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#203746",
            margin=dict(l=15, r=15, t=55, b=15),
            height=300,
            xaxis=dict(dtick=1, title="Hour of day"),
            yaxis=dict(title="Number of orders"),
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No usable timestamps are available for hourly analysis.")


# =========================================================
# OPERATIONAL SUMMARY
# =========================================================

st.markdown(
    '<div class="section-title">Operational intelligence</div>',
    unsafe_allow_html=True,
)

if canceled > 0 and cancel_rate >= 15:
    issue_title = "Elevated order cancellations"
    finding = (
        f"{canceled} of {total_orders} orders were canceled "
        f"({cancel_rate:.1f}%)."
    )
    action = (
        "Inspect cancellation reasons, customer wait times, rider availability, "
        "and restaurant preparation delays."
    )

elif canceled > 0:
    issue_title = "Order cancellations detected"
    finding = (
        f"{canceled} of {total_orders} orders were canceled "
        f"({cancel_rate:.1f}%)."
    )
    action = (
        "Review the canceled orders and identify common reasons, zones, "
        "and time periods."
    )

elif late_rate > 0:
    issue_title = "Late deliveries"
    finding = f"{late_rate:.1f}% of completed orders exceeded the promise."
    action = (
        "Inspect pickup waits, route duration, and rider availability "
        "for late orders."
    )

else:
    issue_title = "Daily delivery performance"
    finding = (
        f"{completed} delivered orders and {canceled} canceled orders "
        f"were recorded for {selected_day}."
    )
    action = (
        "Continue monitoring delivery duration, late orders, and cancellation "
        "patterns as more data becomes available."
    )

st.markdown(
    f"""
    <div class="summary-card">
        <div class="kicker">Operations brief · {safe_text(selected_day)}</div>
        <h3>{safe_text(issue_title)}</h3>
        <p><strong>Main finding:</strong> {safe_text(finding)}</p>
        <p><strong>Recommended action:</strong> {safe_text(action)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SOURCE ORDERS
# =========================================================

with st.expander("🔎 Inspect source orders"):
    st.dataframe(
        day_orders.drop(
            columns=["_day", "_status", "_is_canceled", "_is_completed",
                     "_delivery_minutes", "_late"],
            errors="ignore",
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download daily orders CSV",
        data=day_orders.to_csv(index=False).encode("utf-8"),
        file_name=f"foodflow_orders_{selected_day}.csv",
        mime="text/csv",
    )


# =========================================================
# PIPELINE AUDIT
# =========================================================

with st.expander("🧾 Pipeline audit trail"):
    audit_df = read_table("pipeline_runs")

    if not audit_df.empty:
        st.dataframe(
            audit_df.tail(10),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No pipeline audit records are available.")


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        FOODFLOW · LOCAL-FIRST DATA ENGINEERING DEMO
        <br>
        Python · SQL · Streamlit · Incremental Data Pipeline
    </div>
    """,
    unsafe_allow_html=True,
)
