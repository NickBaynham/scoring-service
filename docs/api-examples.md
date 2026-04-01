# API examples

Base URL examples use `http://localhost:8000`. Add `-H "X-API-Key: ..."` if `API_KEY` is configured.

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

## Job status

```bash
curl -s "http://localhost:8000/v1/score-jobs/<JOB_ID>?tenant_id=tenant_1" | jq .
```

## Document scores

```bash
curl -s "http://localhost:8000/v1/documents/<DOCUMENT_ID>/scores?tenant_id=tenant_1&profile=credibility_v1" | jq .
```

## OpenAPI

- Swagger UI: `/docs`
- Raw schema: `/openapi.json`
