# Project scope: CSV Analyst Assistant

## Goal

Build a **CSV Analyst Assistant** that answers questions about a user-provided CSV using a backend designed for **reliability and evaluation**:

- Convert natural-language questions into **structured intents** (a constrained schema)
- Validate intents against dataset metadata and safety rules
- Execute a **restricted set of Pandas operations** derived from the validated intent
- Return results as tables + summaries + charts, with artifacts suitable for benchmarking

## Non-goals

- Free-form code generation/execution (no arbitrary Python from the LLM)
- Complex multi-dataset joins across many uploads (start with single-CSV workflows)
- Building a full BI semantic layer (dimensions/measures), at least initially

## System design (backend-oriented)

### 1) Data ingestion and profiling

- Load uploaded CSV into a DataFrame.
- Produce lightweight metadata used for validation and prompting:
  - column names, inferred dtypes, missingness, basic stats, cardinality
  - optional: sample rows (bounded) for LLM grounding

### 2) Structured intent parsing

The LLM is asked to produce a **JSON-serializable intent** that matches `app/schemas.py`, for example:

- query type: `summary`, `filter`, `groupby_aggregate`, `top_k`, `time_series`, `correlation`, `distribution`
- selected columns and derived fields
- filters with operators and typed values
- aggregations (sum/mean/count/etc.)
- requested chart type and axes (optional)

This intent is produced by prompt templates in `app/prompts.py`.

### 3) Validation and safety

Before any computation:

- **Schema validation**: required fields present, types correct, enums in allowed set.
- **Column validation**: referenced columns exist; dtype compatibility checks (e.g., numeric required).
- **Operation constraints**: only allow operations we explicitly support (no arbitrary eval).
- **Resource constraints**: row/column limits, timeouts, and bounded sampling for display.
- **Determinism for eval**: normalize ordering, rounding, and consistent formatting where possible.

Validation logic lives in `app/validator.py`.

### 4) Execution engine (validated Pandas)

Translate the validated intent into Pandas operations:

- filtering
- grouping + aggregation
- sorting + top-k
- pivot/crosstab (if supported)
- time-series resampling (if supported)

Analytics logic lives in `app/analytics.py`, with chart generation in `app/charts.py`.

### 5) LLM routing

Support multiple providers/models behind a single interface:

- A router in `app/llm_router.py` selects provider/model based on task type, latency/cost constraints, or environment configuration.
- Providers can be enabled/disabled via `app/config.py` and `.env`.

### 6) Evaluation

Evaluation is treated as a first-class feature:

- Define benchmark questions in `data/benchmarks/benchmark_questions.csv`
- Run scripted evaluations that produce versioned artifacts in `outputs/eval_runs/`
- Track:
  - intent validity rate
  - execution success rate
  - answer correctness against expected answers (where available)
  - chart generation success

Implementation entrypoints are in `scripts/`, with supporting logic in `app/evaluation.py`.
