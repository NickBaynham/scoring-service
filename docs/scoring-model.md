# Scoring model — credibility_v1

## Dimensions

| Dimension | Meaning (high = better unless noted) |
|-----------|--------------------------------------|
| **logical_soundness** | Structure of arguments and inference. |
| **claim_verifiability** | Whether claims could be checked against evidence. |
| **evidence_support** | Support within the text for assertions. |
| **internal_consistency** | Absence of contradictions. |
| **hallucination_risk** | Risk of fabricated detail (**higher = worse**). |

## Aggregation

```
overall = 0.25·LS + 0.20·CV + 0.20·ES + 0.20·IC + 0.15·(1 − HR)
```

Where **LS/CV/ES/IC** are 0–1 “higher is better” and **HR** is hallucination risk 0–1.

## Confidence

**Confidence** is the **arithmetic mean** of per-dimension `confidence` fields returned by the model. It encodes **self-rated uncertainty**, not a calibrated probability.

## Why hallucination risk is inverted

Risk is a “badness” metric. The overall score is a “goodness” metric, so the formula uses **(1 − HR)** so that higher risk lowers the headline score.

## Caveats

- Scores are **not** legal or financial advice.
- Models may **miss** subtle issues or **over-flag** stylistic choices.
- **Domain-specific** fact-checking requires external data sources.
