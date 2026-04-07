# Backend Scope: CSV Analyst Assistant

## 1. Backend Objective

The backend is responsible for converting a validated structured request into deterministic analytics results. Concretely, it must:

1. accept a structured query produced by the LLM layer,
2. validate that query against the uploaded CSV schema and task constraints,
3. execute the approved operation using pandas, and
4. return structured results that the frontend can render reliably.

The backend is the enforcement layer for correctness, safety, and reproducibility.

## 2. Supported Task Types

Only the following task types are in scope for execution.

### `summary_stat`

**Definition:** Compute a single aggregate statistic over one metric column (for example: mean, max, min, sum, count).

**Example user questions:**
- What is the average sales value?
- What is the maximum age?

### `grouped_aggregation`

**Definition:** Group records by a categorical or discrete column and compute an aggregate metric per group.

**Example user questions:**
- Which region has the highest total profit?
- Show average charges by smoker status.

### `filtered_aggregation`

**Definition:** Apply one or more filters, then compute an aggregate over the filtered subset.

**Example user questions:**
- What is the average charge for smokers?
- How many records have age greater than 65?

### `time_series`

**Definition:** Aggregate or summarize values over time using a valid datetime column and optional granularity (for example: day, week, month).

**Example user questions:**
- Show monthly sales trends.
- Plot revenue over time.

## 3. Unsupported Features

The backend will **not** support:

- unrestricted code generation and execution
- multi-table joins
- forecasting
- advanced conversational follow-up memory
- arbitrary charting requests beyond the supported set
- multi-step agent workflows

These are explicit non-goals for this project phase and should not be introduced implicitly.

## 4. Structured Query Design

The LLM must output a constrained structured schema (for example via pydantic model validation). The schema should include fields such as:

- `task_type`
- `metric_column`
- `aggregation`
- `groupby_column`
- `filters`
- `time_column`
- `time_granularity`
- `chart_type`

Design intent:

- keep the schema expressive enough for the four supported task types,
- keep it narrow enough to validate deterministically,
- avoid open-ended fields that imply arbitrary execution.

## 5. Validation Philosophy

Every structured query must be validated before execution. Validation should fail fast with clear error messages. At minimum, validation includes:

- column existence checks
- numeric type checks where aggregation requires numeric data
- datetime compatibility checks for time-series queries
- valid filter checks (supported operators, value type compatibility)
- compatibility checks between task type and chart type

Validation is mandatory; no query reaches the analytics layer without passing this gate.

## 6. Execution Philosophy

All analytics must be performed by backend pandas code. The LLM may assist with intent parsing (and optional explanation text), but it must not directly generate or execute arbitrary code in the execution path.

Execution should be:

- deterministic where possible,
- auditable through logs and structured outputs,
- constrained to the supported operations.

## 7. Result Format

Backend functions should return a consistent dictionary-like structure so frontend integration and evaluation are stable. Typical keys include:

- `result_type`
- `value`
- `table`
- `chart_data`
- `message`
- `error`

Not every key is required for every task, but the shape should remain predictable and documented.

## 8. Backend Responsibilities for Week 1

Week 1 backend priorities:

- define schema and constants
- implement validator
- implement analytics functions
- build benchmark dataset
- build evaluation scripts
- prepare reproducible experiments

This week focuses on backend foundation and evaluation readiness rather than feature expansion.
