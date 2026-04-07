# Benchmark Design: CSV Analyst Assistant

## 1. Benchmark Purpose

The benchmark is a core project asset used to quantitatively evaluate system quality. It is required to measure two things:

1. **Structured query interpretation quality** (did the model parse intent correctly?), and
2. **End-to-end answer correctness** (did the full backend pipeline produce the correct final output?).

Without a benchmark, model and prompt comparisons are anecdotal. With a benchmark, comparisons become measurable, reproducible, and defensible.

## 2. Benchmark Unit

Each benchmark row represents **one natural-language question** paired with:

- gold structured labels (intended parsed query fields), and
- expected outputs (scalar or table, plus expected chart type where relevant).

This row-level design allows fine-grained scoring and error analysis by model, prompt, task type, and difficulty.

## 3. Benchmark Categories

The benchmark must include questions across all supported task categories:

- **summary_stat** questions
- **grouped_aggregation** questions
- **filtered_aggregation** questions
- **time_series** questions

Category balance should be tracked so no single type dominates the benchmark.

## 4. Dataset Coverage

Benchmark questions should be distributed across **2-3 datasets** to improve generalization and avoid overfitting to one schema. Suggested dataset types:

- sales data
- healthcare or insurance data
- another dataset with a date column

Coverage goals:

- varied column names and domain language,
- mixed numeric/categorical/time fields,
- realistic user phrasing differences across domains.

## 5. Gold Label Fields

Each benchmark question should be annotated with the following fields:

- `question_id`
- `dataset_name`
- `question_text`
- `task_type`
- `metric_column`
- `aggregation`
- `groupby_column`
- filter fields
- time fields
- `time_column_format` (for example `iso_date` for `YYYY-MM-DD`)
- expected chart type
- expected scalar answer or expected table

Implementation note:

- filter and time fields can be normalized into structured columns or serialized JSON, but schema consistency must be enforced across the full benchmark.

## 6. Difficulty Levels

Each benchmark question should be assigned a difficulty level for analysis slicing.

- **Easy**
  - direct phrasing
  - one clear metric
  - no or minimal filters
  - no ambiguity in task type

- **Medium**
  - one to two constraints (for example filters/grouping)
  - mild phrasing variation
  - potential column synonym ambiguity

- **Hard**
  - more complex phrasing or multiple conditions
  - potentially ambiguous intent requiring precise schema grounding
  - higher risk of parsing or execution mistakes

Difficulty labels support targeted debugging and help explain where models/prompts fail.

## 7. Construction Strategy

The benchmark should be developed incrementally:

1. Start with a smaller seed set spanning all task types and datasets.
2. Validate schema quality and scoring scripts on that seed set.
3. Expand systematically to cover more variations in wording, filters, and time granularity.
4. Grow to **100+ questions** with balanced category and difficulty distribution.

Recommended workflow:

- draft questions,
- annotate gold structured fields,
- compute/verify expected answers,
- run pilot evaluation,
- refine ambiguous or low-quality items.

## 8. Week 1 Benchmark Deliverable

By the end of Week 1, the team should have:

- benchmark schema finalized
- first 30+ questions drafted
- first subset of expected answers computed

These outputs establish the baseline required to run early model/prompt experiments in Week 2.
