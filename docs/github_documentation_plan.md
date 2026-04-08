# GitHub Documentation Plan: CSV Analyst Assistant

## Purpose

This document defines how the repository should be documented so a professor or TA can quickly understand:

- what the project does,
- how it is implemented,
- how to run it,
- how evaluation was performed, and
- how to verify results.

The goal is a clear, academically rigorous, and reproducible project repository.

## 1. README Requirements

The main `README.md` should include the following sections:

- project overview
- problem statement
- features
- repository structure
- setup instructions
- how to run the Streamlit app
- supported query types
- evaluation methodology
- benchmark dataset
- models evaluated
- prompt variants
- metrics
- example questions
- limitations
- future work
- team responsibilities

Guidance:

- keep each section concise but specific,
- include runnable commands where relevant,
- link to deeper docs in `docs/` for technical details.

## 2. Code Documentation Expectations

Code modules should follow consistent documentation and readability practices:

- docstrings for modules, classes, and key functions
- type hints where reasonable
- readable, descriptive function names
- consistent return types across similar functions
- comments only where useful (especially for non-obvious logic)

This ensures maintainability and makes grading easier by reducing ambiguity in backend behavior.

## 3. Docs Folder Expectations

The `docs/` folder should provide structured project context beyond the README. Each file has a clear purpose:

- scope/context docs define what the project is and is not doing,
- backend docs define architecture and execution constraints,
- evaluation docs define experiment design and metrics,
- planning docs show implementation timeline and prioritization,
- structure docs explain repository organization for fast onboarding.

Why this matters for an academic repo:

- demonstrates planning rigor,
- shows traceable decision-making,
- helps evaluators map implementation to documented intent,
- improves clarity during presentation and report writing.

## 4. Reproducibility Expectations

The repository should make it easy to:

- install dependencies
- run the app
- run tests
- run evaluation scripts
- inspect saved outputs

Minimum reproducibility standard:

- one clear setup path (environment + dependencies),
- scripted evaluation entry points,
- stable output directories for run artifacts and logs,
- documentation that maps commands to expected outputs.

## 5. Week 1 Documentation Deliverables

Week 1 documentation deliverables:

- starter README
- docs folder populated
- initial repo guide
- initial evaluation plan

These deliverables establish the baseline documentation required for Weeks 2-3 experiments, implementation polish, and final presentation/report preparation.
