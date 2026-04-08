# Week 1 Backend Implementation Plan

## Context

This plan is for **Week 1** of a **3-week** graduate course project: **CSV Analyst Assistant**.  
Role context: **backend lead**.  
Week 1 priority: lock scope, set up evaluation foundations, and implement core backend modules that enable reliable end-to-end experiments.

---

## Day 1 - Scope, Repo Foundation, and Backend Philosophy

### Objective

Establish project structure, scope boundaries, and backend design principles so implementation stays focused and reproducible.

### Tasks

- Create and verify repository folder/file scaffold for app, data, docs, scripts, outputs, tests.
- Write foundational scope docs (`project_scope`, backend scope, evaluation requirements context docs).
- Finalize supported backend task types:
  - `summary_stat`
  - `grouped_aggregation`
  - `filtered_aggregation`
  - `time_series`
- Explicitly define non-goals (no arbitrary code execution, no multi-table joins, no forecasting, etc.).
- Decide and document structured execution philosophy:
  - LLM for intent parsing only
  - backend for deterministic validated execution
- Align team responsibilities for backend vs frontend integration boundaries.

### Deliverables by End of Day

- Clean repository structure in place.
- Written scope documentation committed and internally aligned.
- Documented supported task taxonomy and out-of-scope list.
- Clear backend philosophy statement for all future implementation decisions.

---

## Day 2 - Schema, Constants, Data Selection, and Benchmark Start

### Objective

Define structured interfaces and bootstrap benchmark assets required for robust evaluation.

### Tasks

- Define output/result schema for backend responses (dictionary-like consistent keys):
  - `result_type`, `value`, `table`, `chart_data`, `message`, `error`
- Define structured query schema fields (pydantic models), including:
  - `task_type`, `metric_column`, `aggregation`, `groupby_column`, `filters`, `time_column`, `time_granularity`, `chart_type`
- Create constants module:
  - allowed task types
  - allowed aggregations
  - allowed operators
  - allowed chart types
  - default limits/error codes/messages
- Choose initial evaluation datasets (small but diverse).
- Start benchmark question dataset draft:
  - create schema/header
  - draft first batch of representative questions across all 4 task types.

### Deliverables by End of Day

- First-pass `schemas` and `constants` modules.
- Standardized backend result format definition.
- Selected dataset list for benchmarking.
- Initial benchmark dataset file and first draft question set.

---

## Day 3 - Validation Layer (Safety and Correctness Gate)

### Objective

Build a strong validation layer that blocks invalid requests before analytics execution.

### Tasks

- Implement validation module for structured query checks.
- Add column existence validation against uploaded DataFrame schema.
- Add type compatibility checks:
  - numeric checks for numeric aggregations
  - datetime checks for time-series operations
- Define and implement filter validation:
  - allowed operators
  - value compatibility with column dtype
  - null-handling and edge-case behavior
- Enforce task-specific requirements:
  - required fields per `task_type`
  - disallowed field combinations
- Define clear, consistent validation errors for frontend and evaluation logs.

### Deliverables by End of Day

- Working validator module with explicit rule coverage.
- Validation rule table documented (what is checked and why).
- Basic manual validation tests passing on sample queries.

---

## Day 4 - Analytics Engine (Core Execution)

### Objective

Implement deterministic pandas execution for all four supported query types and verify behavior on sample data.

### Tasks

- Implement analytics functions for:
  - `summary_stat`
  - `grouped_aggregation`
  - `filtered_aggregation`
  - `time_series`
- Ensure each function accepts validated inputs and returns standardized result format.
- Implement stable sorting/formatting conventions for reproducibility.
- Handle edge cases:
  - empty filter results
  - missing values in metric/group columns
  - unsupported aggregation-task combinations
- Manually test with sample CSV data and known expected outcomes.

### Deliverables by End of Day

- Functional analytics engine with four task handlers.
- Manual test notebook or script results showing expected outputs.
- Documented edge-case behavior decisions.

---

## Day 5 - Chart Utilities and Benchmark Expansion

### Objective

Add chart-generation support aligned to task types and significantly expand benchmark/evaluation readiness.

### Tasks

- Build chart helper module for supported chart outputs (for example bar/line where appropriate).
- Map task types to recommended/allowed chart types.
- Ensure chart data payload format is consistent for frontend rendering.
- Continue benchmark construction:
  - broaden domain coverage
  - include ambiguity/challenging phrasing cases
  - include filter and time-granularity variations
- Compute expected answers for first benchmark subset (gold results).

### Deliverables by End of Day

- Chart helper functions integrated with result formatting.
- Expanded benchmark draft with broader question coverage.
- Gold expected answers generated for initial subset.

---

## Day 6 - Prompt Variants and LLM Routing

### Objective

Prepare multi-prompt, multi-model intent parsing pipeline for evaluation.

### Tasks

- Create prompt variants:
  - minimal
  - schema-aware
  - few-shot
  - strict anti-hallucination
- Implement LLM router abstraction:
  - provider/model config selection
  - common request/response normalization
  - error and timeout handling
- Add parser-to-schema flow:
  - prompt -> model output -> structured parse -> validation input
- Test routing and parsing on sample benchmark questions across candidate models.

### Deliverables by End of Day

- Prompt library with 3-4 clearly versioned variants.
- Working `llm_router` module and normalized output contract.
- Sample parsing run logs demonstrating model/prompt behavior.

---

## Day 7 - Evaluation Scripts, Tests, Pilot Experiment, and Week Summary

### Objective

Close Week 1 with executable evaluation scaffolding, baseline tests, and one pilot experiment run.

### Tasks

- Build evaluation helpers:
  - interpretation scoring utilities
  - end-to-end scoring utilities
- Implement evaluation scripts:
  - router/interpretation evaluation
  - end-to-end evaluation
  - run metadata + output saving
- Create tests for critical modules:
  - validator
  - analytics
  - llm router (mocked)
  - evaluation helpers (where feasible)
- Run pilot experiment:
  - limited benchmark subset
  - multiple prompts
  - at least initial model set
- Summarize Week 1 outcomes:
  - what is complete
  - what remains
  - top issues discovered.

### Deliverables by End of Day

- Executable evaluation script scaffolds and output format.
- Baseline automated test suite for core backend pieces.
- Pilot run artifacts in outputs/logs/results.
- Written Week 1 progress summary for team coordination.

---

## Week 1 Success Checklist

- [ ] Scope and non-goals are documented and stable.
- [ ] Structured query schema and result schema are defined.
- [ ] Constants and validation rules are implemented.
- [ ] Analytics engine supports all 4 in-scope task types.
- [ ] Chart helpers return frontend-consumable structures.
- [ ] Benchmark dataset structure is finalized.
- [ ] Initial benchmark questions are drafted and partially gold-labeled.
- [ ] 4 candidate models and 3-4 prompt variants are defined.
- [ ] Evaluation scripts run programmatically.
- [ ] A pilot experiment has been executed and saved.
- [ ] Core backend tests exist and pass for baseline scenarios.

## Most Important Risks to Avoid

- **Scope creep:** adding advanced features before core evaluation pipeline is stable.
- **Over-reliance on LLM output:** skipping strict validation before execution.
- **Inconsistent schemas:** changing field names/contracts mid-week without migration.
- **Manual-only experimentation:** failing to script runs leads to non-reproducible results.
- **Weak benchmark quality:** too few questions or poor coverage across task types.
- **Late integration surprises:** backend result formats not aligned with frontend expectations.

## What Must Be Ready Before Week 2 Begins

- Stable schema + constants + validation contracts.
- Working analytics execution for all supported task types.
- Initial chart output integration path.
- Benchmark framework with meaningful starter question set.
- Prompt variants and model candidates selected for comparative experiments.
- Script-based evaluation pipeline producing saved per-question outputs.
- Baseline tests and documented known limitations.

With these in place, Week 2 can focus on scaling experiments, improving accuracy, and tightening app integration rather than rebuilding backend foundations.
