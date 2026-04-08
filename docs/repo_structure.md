# Repository Structure Guide: CSV Analyst Assistant

## 1. Repository Tree (Target Structure)

```text
csv-analyst-assistant/
README.md
requirements.txt
.gitignore
.env.example
app/main.py
app/config.py
app/constants.py
app/schemas.py
app/prompts.py
app/llm_router.py
app/validator.py
app/analytics.py
app/charts.py
app/evaluation.py
app/utils.py
data/raw/
data/processed/
data/benchmarks/benchmark_questions.csv
notebooks/benchmark_design.ipynb
scripts/run_router_eval.py
scripts/run_end_to_end_eval.py
scripts/generate_expected_answers.py
outputs/eval_runs/
outputs/figures/
outputs/logs/
tests/test_validator.py
tests/test_analytics.py
tests/test_llm_router.py
docs/project_brief.md
docs/backend_scope.md
docs/evaluation_requirements.md
docs/week1_plan.md
docs/repo_structure.md
docs/cursor_master_context.md
```

## 2. What Each Folder Is For

- `app/`  
  Core application and backend modules: input parsing, validation, analytics execution, chart preparation, evaluation logic, and shared utilities.

- `data/`  
  Data storage by lifecycle stage:
  - `data/raw/`: original input CSV files
  - `data/processed/`: cleaned/transformed intermediate outputs
  - `data/benchmarks/`: benchmark dataset files for evaluation

- `notebooks/`  
  Exploratory and design notebooks, especially for benchmark design and early analysis experiments.

- `scripts/`  
  Programmatic entry points for evaluation workflows (router-only and end-to-end experiments), plus expected-answer generation.

- `outputs/`  
  Generated artifacts from experiments and runs:
  - `outputs/eval_runs/`: per-run metrics and detailed result files
  - `outputs/figures/`: plots from analysis/evaluation
  - `outputs/logs/`: execution logs and debugging traces

- `tests/`  
  Automated tests for backend reliability and regression checks.

- `docs/`  
  Project documentation: scope, architecture choices, evaluation requirements, planning, and team context.

## 3. Important Files and Modules

### Root Files

- `README.md`  
  Primary project entry point: setup, usage, evaluation workflow, and high-level structure.

- `requirements.txt`  
  Python dependency list for consistent local and CI environment setup.

- `.gitignore`  
  Rules to exclude virtual environments, temporary files, logs, and generated artifacts from version control.

- `.env.example`  
  Template of required environment variables (for API keys/config), without exposing secrets.

### Core App Modules (`app/`)

- `main.py`  
  Streamlit app entry point and top-level UI-to-backend wiring.

- `config.py`  
  Environment/config loading and runtime settings (models, limits, paths, provider options).

- `constants.py`  
  Central definitions for allowed task types, aggregations, operators, chart types, and defaults.  
  Role: reduce magic strings and keep behavior consistent across modules.

- `schemas.py`  
  Structured data models (typically pydantic) for parsed intents, filters, and result contracts.  
  Role: enforce schema correctness and provide typed interfaces between LLM parsing and backend execution.

- `prompts.py`  
  Prompt templates/variants used to map natural-language questions into structured query objects.  
  Role: standardize prompt behavior and enable controlled prompt-level experimentation.

- `llm_router.py`  
  Model/provider abstraction layer that routes prompt calls to selected LLMs through a common interface.  
  Role: make multi-model comparison and switching straightforward without changing business logic.

- `validator.py`  
  Validation logic for structured queries against CSV schema and rule constraints.  
  Role: gatekeeper before execution (column checks, type compatibility, filter validity, task constraints).

- `analytics.py`  
  Deterministic pandas execution engine for supported task types (`summary_stat`, `grouped_aggregation`, `filtered_aggregation`, `time_series`).  
  Role: produce reliable computed answers from validated requests.

- `charts.py`  
  Chart data preparation helpers and chart-type mapping logic for frontend rendering.  
  Role: generate consistent plotting payloads from backend outputs.

- `evaluation.py`  
  Evaluation utilities for interpretation and end-to-end scoring (metrics, run summaries, analysis helpers).  
  Role: centralize measurement logic for reproducible experiments.

- `utils.py`  
  Shared helper functions (formatting, coercion, safe conversions, small reusable utilities).  
  Role: avoid duplication and keep core modules focused.

### Data, Scripts, and Tests

- `data/benchmarks/benchmark_questions.csv`  
  Main benchmark dataset of evaluation questions and expected fields/answers.

- `notebooks/benchmark_design.ipynb`  
  Notebook for designing and iterating benchmark structure/questions.

- `scripts/run_router_eval.py`  
  Runs interpretation-focused experiments (LLM parsing quality and structured output correctness).

- `scripts/run_end_to_end_eval.py`  
  Runs full pipeline evaluation from question -> parse -> validate -> execute -> score.

- `scripts/generate_expected_answers.py`  
  Utility to compute or assist with generating gold expected answers for benchmark entries.

- `tests/test_validator.py`  
  Tests for validation rule correctness and error behavior.

- `tests/test_analytics.py`  
  Tests for analytics correctness across supported task types.

- `tests/test_llm_router.py`  
  Tests for routing logic, normalization behavior, and provider error handling (usually mocked).

### Documentation Files (`docs/`)

- `docs/project_brief.md`: concise project purpose and deliverables.
- `docs/backend_scope.md`: backend technical boundaries and design constraints.
- `docs/evaluation_requirements.md`: professor-aligned experiment requirements and metrics.
- `docs/week1_plan.md`: day-by-day Week 1 execution plan.
- `docs/repo_structure.md`: repository structure reference (this file).
- `docs/cursor_master_context.md`: master context and scope alignment guidance.

## 4. Why This Structure Supports Documentation and Reproducible Evaluation

- **Separation of concerns**: core execution (`app/`), experiment automation (`scripts/`), artifacts (`outputs/`), and docs (`docs/`) are clearly separated.
- **Repeatable experiments**: script-driven evaluation and benchmark files make runs reproducible and comparable across models/prompts.
- **Traceable outputs**: run artifacts and logs are stored in dedicated output directories for analysis and reporting.
- **Maintainable documentation**: project intent, scope, and evaluation requirements live in versioned markdown files.
- **Testable backend**: targeted tests for validation, analytics, and routing reduce regressions as the project evolves.
