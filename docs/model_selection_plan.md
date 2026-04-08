# Model Selection Plan: CSV Analyst Assistant

## 1. Requirement

This project must evaluate **at least 4 language models** as part of the experimental methodology.

Model comparison is a required component of the evaluation, not an optional extension.

## 2. Practical Constraints

For this academic project, using the absolute newest models is not required. Low-cost or free-access models are acceptable as long as they support the project’s structured query extraction workflow.

The model set should be chosen to balance quality with practical execution constraints (budget, access, and time).

## 3. Selection Criteria

Candidate models should be selected using the following criteria:

- affordability
- API accessibility
- reliability
- ability to follow structured output instructions
- reasonable latency for batch experiments

Additional considerations:

- stable availability during the project timeline,
- clear usage limits/quotas,
- predictable error behavior for scripted retries/logging.

## 4. Evaluation Use

All selected models will be tested under the same experimental conditions:

- same benchmark question set,
- same prompt variants,
- same output schema,
- same scoring metrics and logging format.

This ensures fair comparison and helps isolate true model differences from pipeline differences.

## 5. Expected Week 1 Deliverable

By the end of Week 1, the team should have:

- at least 4 candidate models identified
- a way to call them programmatically
- a plan for pilot testing them on a small subset of benchmark questions

These deliverables establish a workable baseline for larger model comparisons in Weeks 2-3.
