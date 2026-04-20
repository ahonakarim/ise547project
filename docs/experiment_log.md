# Experiment Log Template

Use one block per run.

## Run
- **Date:** YYYY-MM-DD
- **Experiment type:** prompt comparison | model comparison
- **Model:** `<model_name>`
- **Prompt variant:** `<minimal | schema_aware | few_shot | strict_anti_hallucination>`
- **Question subset size:** `<N>`
- **Output file path:** `outputs/eval_runs/<file>.csv`

## Results
- **parse_success:** `<count>/<total> (<rate%>)`
- **exact_match:** `<count>/<total> (<rate%>)`

## Main failure patterns
- `<e.g., 429 rate limits>`
- `<e.g., task_type mismatches>`
- `<e.g., chart_type mismatches>`

## Notes
- `<observations, config changes, follow-ups>`

------------

## Run
- **Date:** 2026-04-19
- **Experiment type:** prompt comparison | model comparison
- **Model:** `<model_name>`
- **Prompt variant:** `<minimal | schema_aware | few_shot | strict_anti_hallucination>`
- **Question subset size:** `<N>`
- **Output file path:** `outputs/eval_runs/<file>.csv`

## Results
- **parse_success:** `<count>/<total> (<rate%>)`
- **exact_match:** `<count>/<total> (<rate%>)`

## Main failure patterns
- `<e.g., 429 rate limits>`
- `<e.g., task_type mismatches>`
- `<e.g., chart_type mismatches>`

## Notes
- `<observations, config changes, follow-ups>`

------------

Input file: outputs/eval_runs/prompt_minimal_claude_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   8/10 (80.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 2

------------

Input file: outputs/eval_runs/prompt_schema_aware_claude_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   8/10 (80.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 2

------------

Input file: outputs/eval_runs/prompt_few_shot_claude_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   10/10 (100.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 0

------------

Input file: outputs/eval_runs/prompt_strict_claude_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   8/10 (80.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 2

------------

Input file: outputs/eval_runs/model_claude_fewshot_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   10/10 (100.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 0

------------

Input file: outputs/eval_runs/model_qwen_fewshot_10.csv
Total rows: 10

Core Metrics
------------
parse_success: 10/10 (100.00%)
exact_match:   10/10 (100.00%)

Error Message Counts
--------------------
    10  (empty)

Failed Field Counts
-------------------
task_type_correct: 0
metric_column_correct: 0
aggregation_correct: 0
groupby_column_correct: 0
filter_correct: 0
time_column_correct: 0
time_granularity_correct: 0
chart_type_correct: 0

------------



------------



------------