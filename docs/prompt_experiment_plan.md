# Prompt Experiment Plan: CSV Analyst Assistant

## 1. Goal of Prompt Experiments

Prompt wording can significantly change structured query extraction quality, even when using the same model and benchmark question. Because structured parsing is a critical dependency for backend correctness, prompt design must be evaluated systematically rather than chosen by intuition.

The purpose of these experiments is to identify which prompt style is most reliable for converting natural-language CSV questions into valid, accurate structured queries.

## 2. Fixed Output Schema

All prompt variants must target the same JSON output schema. This is required so results are directly comparable across prompts and models.

Practical implications:

- identical required fields across all variants,
- identical field names and allowed values,
- identical parsing/validation logic downstream.

If schema changes between prompts, metric comparisons become invalid.

## 3. Prompt Variants to Compare

The project will compare four prompt styles:

- **minimal**  
  Short instruction-only prompt with minimal context and no examples.

- **schema-aware**  
  Prompt explicitly describes field definitions, allowed task types, and output constraints.

- **few-shot**  
  Prompt includes representative question-to-JSON examples to guide extraction behavior.

- **strict anti-hallucination**  
  Prompt emphasizes using only known dataset columns, returning null/empty fields when uncertain, and avoiding fabricated values.

Each variant should be versioned and stored so runs are reproducible.

## 4. Comparison Method

The same benchmark questions will be run across all prompt variants, ideally across all 4 selected models.

Comparison protocol:

- keep benchmark input fixed,
- keep output schema fixed,
- vary prompt variant,
- record per-question outcomes,
- aggregate by prompt/model/task type.

This produces fair, apples-to-apples comparisons.

## 5. Evaluation Metrics

Primary metrics:

- task type accuracy
- field-level extraction accuracy
- exact structured match
- parse success rate

These metrics should be computed per prompt variant and also sliced by model and task type.

## 6. Risks

Key risks to monitor during prompt experiments:

- hallucinated columns
- malformed JSON
- omitted fields
- overfitting to examples in few-shot prompts

Mitigation should include strict schema validation, benchmark diversity, and careful review of error categories rather than only top-line accuracy.

## 7. Week 1 Deliverable

By the end of Week 1, the prompt variants should be drafted and tested on a small pilot question set.

Minimum Week 1 output:

- versioned draft prompts for all planned variants,
- pilot run logs/results,
- initial observations on failure modes to guide Week 2 iteration.
