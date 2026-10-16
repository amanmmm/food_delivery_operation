
# FoodFlow — Food Delivery Operations Analytics

## Overview

FoodFlow is a local-first data engineering project that ingests
food delivery orders, riders, and delivery events incrementally.
It calculates daily delivery and cancellation metrics and provides
an operational summary based on the measured data.

## Technology stack

- Python
- Pandas
- SQLite
- Streamlit
- Plotly
- Pytest
- Optional local Ollama model

## Features

- Incremental ingestion with unique primary keys
- Daily delivery-time and cancellation metrics
- Late-delivery and zone analysis
- Interactive dashboard with date selection
- Evidence-based operational summary
- Pipeline audit trail
- Automated validation tests
- Synthetic sample data

## Project structure

- `app.py`: dashboard
- `src/generate_data.py`: synthetic source generator
- `src/pipeline.py`: incremental ingestion
- `src/metrics.py`: daily analytics
- `src/ai/summary.py`: summary interface
- `src/ai/providers.py`: summary implementations
- `tests/test_pipeline.py`: validation tests
- `data/`: CSV source data
- `warehouse/`: local SQLite database

## Setup

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate synthetic data:

```bash
python -m src.generate_data
```

Run the pipeline:

```bash
python -m src.pipeline
```

Launch the dashboard:

```bash
streamlit run app.py
```

Run tests:

```bash
python -m pytest -q
```

## Data model

- `orders`: one record per order
- `riders`: synthetic rider dimension
- `delivery_events`: append-only lifecycle events
- `delivery_facts`: SQL view of order lifecycle timestamps
- `pipeline_runs`: ingestion audit records

## Metric definitions

Delivery duration is the time between pickup and delivery.
Late deliveries exceed their promised duration.
Cancellation rate is cancelled orders divided by orders
created on the selected day.

## AI summary

The default provider uses local rule-based logic.
An optional Ollama provider can generate a natural-language
summary locally. No cloud API key is required.

## Testing

The test suite checks incremental idempotency, event integrity,
and positive delivery durations.

## Data privacy

The demo uses synthetic data only. Do not commit secrets,
credentials, or real customer data.

## Limitations

The dataset is synthetic. The operational issue ranking is a
prototype heuristic and should not be treated as a production
severity model without validated thresholds.

## Demo

Record a 5–8 minute walkthrough covering setup, architecture,
pipeline execution, dashboard metrics, tests, and the repeated-run
edge case.
