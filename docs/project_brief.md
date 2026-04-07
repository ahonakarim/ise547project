# Project Brief: CSV Analyst Assistant

## 1. Project Overview

CSV Analyst Assistant is a web application that lets users upload a CSV file and ask questions in plain English. Typical questions include requests for averages, grouped comparisons, filtered results, and time trends. The goal is to produce useful analytical outputs without requiring users to write code.

## 2. Problem Statement

Many users have tabular data but do not know pandas, SQL, or dashboard tools well enough to analyze it quickly. Even basic questions can become time-consuming when users need technical query skills. A natural-language interface can lower this barrier and make data analysis more accessible for non-expert users.

## 3. Proposed Solution

The system uses an LLM to map each user question into a structured analysis request. That request is then passed to a validated pandas backend that executes the query safely and accurately. This approach combines flexible language understanding with constrained, reliable execution.

## 4. Why This Project Fits the Course

This project directly aligns with course goals by combining practical LLM usage, prompting strategy, and empirical evaluation. It also produces tangible deliverables expected in the course format: a working website and a documented GitHub repository.

## 5. Team Roles

- I am the backend lead.
- My responsibilities are schema design, validation, analytics execution, evaluation pipeline, and benchmark creation.
- My teammate is focused more on frontend/UI, app integration, and result presentation.

## 6. Deliverables

- working website
- documented GitHub repository
- evaluation experiments
- presentation
- report

## 7. Scope Summary

The project is intentionally scoped to four supported query types:

- `summary_stat`
- `grouped_aggregation`
- `filtered_aggregation`
- `time_series`

## 8. Success Criteria

Success means:

- the system can correctly interpret and answer benchmark questions
- the system can be evaluated across multiple models and prompt variants
- the backend is reproducible and documented
