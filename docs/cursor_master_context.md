# CSV Analyst Assistant - Master Context

## 1. Project Name

**CSV Analyst Assistant**

## 2. Timeline

The total project timeline is **3 weeks**.  
The current focus is **Week 1: backend setup and evaluation design**.

## 3. Team Context

This is a **two-person team** project.

- Backend lead: project owner for backend architecture, data execution, validation, and evaluation workflows
- Teammate focus: frontend/UI and integration

## 4. Project Goal

The goal is to build a web application where a user uploads a CSV file and asks questions in natural language. The system should use an LLM to convert each question into a structured query representation. The backend should validate that structured query and execute it using pandas. The app should return:

- an answer,
- a chart when relevant, and
- a short explanation.

## 5. Backend Scope

### Supported task types

- `summary_stat`
- `grouped_aggregation`
- `filtered_aggregation`
- `time_series`

### Out of scope

Do **not** support the following in the core implementation:

- arbitrary free-form code generation as the main execution method
- multi-table joins
- forecasting
- agent workflows
- advanced conversational memory
- complicated multi-step analytics beyond the four supported task types

## 6. Architecture

The target architecture is:

- Streamlit frontend
- Python backend
- pandas for execution
- pydantic for schemas
- requests/OpenAI-compatible API for LLM calls
- pytest for tests

## 7. LLM Design Philosophy

Use the LLM primarily for structured intent parsing and, where useful, short explanation generation. Do not rely on the LLM for unrestricted code generation. Prioritize validated deterministic execution over model-generated pandas code.

## 8. Evaluation Requirements

Evaluation is a first-class requirement for this course project. The system must be evaluated across multiple models, prompts, and measurable outcomes, and results must be reproducible and documented.

The project requirements are:

- We must evaluate the system with at least 4 LLMs.
- We must test at least 3–4 prompt variants.
- We must use clear quantitative metrics.
- We must build or identify an evaluation dataset with at least 100 evaluation data points/questions.
- We must compare what worked and did not work across model/prompt combinations.
- The experimental work must be completed by presentation time.
- The GitHub repository must be documented.

## 9. Backend Priorities

Order of implementation:

1. repo scaffold
2. schemas and constants
3. validator
4. analytics engine
5. charts
6. prompts
7. llm router
8. evaluation scripts
9. tests
10. app wiring

## 10. Code Expectations

All backend code should be production-minded for a course setting:

- modular Python
- docstrings
- type hints where reasonable
- robust error handling
- consistent return formats
- easy to document in GitHub

## 11. Cursor Instruction

Cursor should treat this file and the rest of `docs/` as the source of truth, keep implementations aligned with the documented scope, and avoid adding extra features not listed here unless explicitly requested.
