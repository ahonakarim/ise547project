# Evaluation Requirements: CSV Analyst Assistant

## 1. Why Evaluation Is Central

Evaluation is a core requirement of this project, not an optional add-on. CSV Analyst Assistant is both:

- a working application, and
- an experiment on how model and prompt choices affect reliability in structured data analysis.

Because of this, evaluation is one of the most important grading components. The project must demonstrate measurable evidence of what works, what fails, and why.

## 2. Required Experimental Variables

The evaluation plan must explicitly include the following professor requirements:

- the system must be tested with at least **4 language models**
- the system must be tested with at least **3–4 prompt variants**
- experiments must be run **programmatically**, not manually through chat interfaces

Implementation implication: all runs should be driven by scripts (for example, batch evaluation scripts in `scripts/`) so results are reproducible.

## 3. Benchmark Dataset Requirement

The evaluation setup should include at least **100 evaluation data points/questions**.

For this project, the evaluation dataset will be a benchmark set of natural-language CSV analysis questions with:

- gold structured labels, and
- expected answers (scalar, grouped output, or expected chart intent depending on task type).

This benchmark is the single source used for model and prompt comparison.

## 4. Benchmark Structure

The benchmark question dataset should be stored in a structured tabular format (CSV or equivalent) and include fields such as:

- `question_id`
- `dataset_name`
- `question_text`
- `task_type`
- `metric_column`
- `aggregation`
- `groupby_column`
- filter fields
- time fields
- expected chart type
- expected answer

Recommended practical shape:

- one row per benchmark question,
- normalized representations for filters/time fields (or JSON-encoded fields if needed),
- versioned dataset updates to preserve experiment traceability.

## 5. Evaluation Levels

Evaluation should be run at two levels.

### A. Interpretation Evaluation

Goal: determine whether the model parsed the question into the correct structured query.

Key question: **Did the model parse the question correctly?**

Metrics:

- task type accuracy
- metric column accuracy
- groupby accuracy
- filter extraction accuracy
- exact structured query match

### B. End-to-End Evaluation

Goal: measure whether the full system produced the correct final output.

Key question: **Did the system produce the correct final answer?**

Metrics:

- scalar answer accuracy
- grouped/table answer correctness
- chart type correctness
- execution success rate
- overall end-to-end accuracy

## 6. Prompt Variants

The project should compare at least these prompt styles:

- minimal
- schema-aware
- few-shot
- strict anti-hallucination

All prompt variants should use the same benchmark and be evaluated with the same metric definitions for fair comparison.

## 7. Model Comparison

The project should compare at least **4 models** using the same benchmark and prompt structure.

Comparison policy:

- same question set,
- same prompt variant definitions,
- same scoring logic,
- same output schema for logs/results.

This ensures differences are attributable to model behavior rather than inconsistent evaluation setup.

## 8. Outputs to Save

Every evaluation run should save per-question records including:

- model name
- prompt variant
- question ID
- parse success
- interpretation correctness
- execution success
- final answer correctness
- error type if any

Recommended output artifacts:

- run-level summary metrics file,
- per-question detailed results file,
- optional error analysis slices by task type/model/prompt.

## 9. Expected Week 1 Evaluation Deliverables

Week 1 evaluation deliverables:

- benchmark schema finalized
- initial benchmark questions drafted
- 4 candidate models selected
- 3–4 prompt variants defined
- evaluation scripts scaffolded

These deliverables establish the minimum infrastructure needed to execute full experiments in Weeks 2–3.
