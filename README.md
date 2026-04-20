# CSV Analyst Assistant

A Python + Streamlit app that helps you analyze CSV files by translating user questions into **structured intents** and running **validated Pandas operations** to produce trustworthy tables, summaries, and charts.

## Overview

- **What it does**: Upload a CSV, ask natural-language questions, get computed answers + charts.
- **How it works**: LLM → structured intent → validation/safety checks → Pandas execution → formatted results.
- **Why structured**: Reduces hallucinations and makes evaluation repeatable.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

- Copy `.env.example` to `.env`
- Fill in provider keys (if using an LLM API)

## Running the app

```bash
streamlit run app/main.py
```

## Project website (GitHub Pages)

This repository (**`ahonakarim/ise547project`**) includes a **static** landing page under `docs/` that you can host for free on **GitHub Pages** (HTML and CSS only; it cannot run Streamlit).

1. Push the `main` branch to GitHub (`https://github.com/ahonakarim/ise547project`).
2. **Before the first workflow run**, open **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**, then **Save**. (If you skip this, deployment fails because GitHub has not registered a Pages site for the repository yet.)
3. The workflow `.github/workflows/deploy-github-pages.yml` publishes `docs/` on each push. After a successful run, the site is available at:

   `https://ahonakarim.github.io/ise547project/`

The interactive Streamlit app still needs a Python host (for example [Streamlit Community Cloud](https://streamlit.io/cloud)). Edit `docs/index.html` to add a prominent link once your app URL is live.

## Real datasets (insurance, yellow taxi, online retail)

1. Place your files locally (or use the defaults in the materialize script: `~/Downloads/...`).
2. Materialize canonical CSVs under `data/raw/` (recommended; caps large sources for a laptop-friendly MVP):

```bash
python scripts/materialize_real_datasets.py \
  --insurance ~/Downloads/insurance.csv \
  --yellow-parquet ~/Downloads/yellow_tripdata_2026-01.parquet \
  --retail-zip ~/Downloads/online_retail_II.csv.zip
```

This writes `insurance.csv`, `yellow_tripdata_2026_01.csv` (first 100k Parquet rows), and `online_retail_ii.csv` (first 120k lines from the zip). Tune caps with `--yellow-max-rows` / `--retail-max-rows`.

Alternatively, set paths in `.env` (see `.env.example`) so `app.dataset_loader.load_dataset` reads directly from Parquet/zip without copying.

- **Logical dataset ids**: `insurance`, `yellow_tripdata_2026_01`, `online_retail_ii`
- **Real-data benchmark**: `data/benchmarks/benchmark_questions_real.csv`
- **Expected answers (real benchmark)**:  
  `python scripts/generate_expected_answers.py --benchmark data/benchmarks/benchmark_questions_real.csv --output outputs/eval_runs/expected_answers_real.jsonl`

Large materialized CSVs are gitignored by default; small `insurance.csv` and the real benchmark CSV can be committed if you want.

## Frontend (MVP)

The Streamlit frontend lets you:

- choose a built-in dataset (processed or raw CSV under `data/`)
- preview the dataset and view basic dataset stats/columns
- ask a natural-language question (or use example question buttons)
- view the interpreted structured query
- view returned outputs (message, scalar value, table, chart when available)

Supported query types are limited to:

- `summary_stat`
- `grouped_aggregation`
- `filtered_aggregation`
- `time_series`

## Evaluation

This repo includes scripts and data scaffolding for benchmarking the router/intent parsing and end-to-end correctness.

- **Benchmarks input**: `data/benchmarks/benchmark_questions.csv` (synthetic) or `data/benchmarks/benchmark_questions_real.csv`
- **Run router-focused eval**: `scripts/run_router_eval.py` (add `--benchmark ...` for the real set)
- **Run end-to-end eval**: `scripts/run_end_to_end_eval.py`
- **Outputs**:
  - `outputs/eval_runs/` (structured run artifacts)
  - `outputs/figures/` (plots)
  - `outputs/logs/` (logs)

## Repository structure

```
ise547project/
  app/                      # Streamlit app + core logic
  data/                     # raw/processed/benchmarks
  docs/                     # scope and evaluation docs
  notebooks/                # exploration / benchmark design
  outputs/                  # eval artifacts, figures, logs
  scripts/                  # runnable evaluation utilities
  tests/                    # unit tests
  README.md
  requirements.txt
  .gitignore
  .env.example
```
