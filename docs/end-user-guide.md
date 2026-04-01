# End-user guide — VerifiedSignal scoring service

## What this service does

The scoring service evaluates **document credibility** using large language models (LLMs). It does **not** certify truth; it produces **structured signals** (scores, confidence, and issue lists) that downstream products can combine with other evidence.

## Submitting work

1. **Register a document** (optional): `POST /v1/documents` with `tenant_id` and optional `raw_text` or `text_uri`.
2. **Enqueue scoring**: `POST /v1/score-jobs` with `document_id`, `tenant_id`, optional inline `text` / `text_uri`, and `profile` (e.g. `credibility_v1`).
3. **Poll job status**: `GET /v1/score-jobs/{job_id}?tenant_id=...` until `status` is `completed` or `failed`.
4. **Read scores**: `GET /v1/documents/{document_id}/scores?tenant_id=...&profile=credibility_v1`.

If `API_KEY` is set server-side, send header `X-API-Key: <value>`.

## Interpreting scores

- **overall_score** — 0–1, weighted blend of dimensions (see [scoring-model.md](scoring-model.md)).
- **confidence** — Mean of per-dimension confidences; reflects model uncertainty, not statistical confidence intervals.
- **scores** — Per-dimension values; **hallucination_risk** is framed so that **higher = worse** for the document, while the overall formula uses **(1 − risk)** so risk reduces the headline score.
- **issues** — Items with `type`, `severity`, optional `quoted_span`, and `explanation`.

## Limitations

- Outputs depend on the **model**, **prompts**, and **input text only**; there is no live web verification unless you add external tools.
- **Numerical claims** may be flagged without access to proprietary data.
- **Bias** and **hallucinations** in the model can affect scores; use scores as one signal among many.
