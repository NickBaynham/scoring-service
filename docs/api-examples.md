# API examples

Base URL examples use `http://localhost:8000`. **GET /** redirects to **Swagger UI** (`/docs`) so you can explore and try requests interactively; the same contract is available as JSON at `/openapi.json`.

Add `-H "X-API-Key: ..."` if `API_KEY` is configured.

Optional tracing: send `X-Request-ID: <uuid>` on requests; the API echoes it on responses.

## Health

```bash
curl -s http://localhost:8000/health | jq .
```

## Register a document

```bash
curl -s -X POST http://localhost:8000/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_1",
    "raw_text": "Our platform is used by 80% of firms in the sector.",
    "profile": "credibility_v1"
  }' | jq .
```

## Enqueue scoring

```bash
curl -s -X POST http://localhost:8000/v1/score-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "<DOCUMENT_ID>",
    "tenant_id": "tenant_1",
    "profile": "credibility_v1"
  }' | jq .
```

The server persists the job, **commits** the transaction, then (if `JOB_QUEUE_BACKEND=sqs`) publishes the `job_id` to SQS.

## Job status

```bash
curl -s "http://localhost:8000/v1/score-jobs/<JOB_ID>?tenant_id=tenant_1" | jq .
```

## Document scores

```bash
curl -s "http://localhost:8000/v1/documents/<DOCUMENT_ID>/scores?tenant_id=tenant_1&profile=credibility_v1" | jq .
```

## OpenAPI

- Swagger UI: `/` (redirect) or `/docs`
- Raw schema: `/openapi.json`
- ReDoc: `/redoc`
- **Static copy** in the repo: [`swagger.html`](swagger.html) + [`openapi.json`](openapi.json). Regenerate the JSON with `make openapi-export`, then serve the `docs/` directory over HTTP (see the main README) so the browser can load the spec.
