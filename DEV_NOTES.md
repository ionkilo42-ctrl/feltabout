# Development Notes

## Backend Schema Patch (2026-05-08)

CORS was already configured correctly in `services/api/app/main.py`.

`/reflections` was failing because `reflection_outputs` was missing newer metadata columns. Patched directly in local PostgreSQL:

- `prompt_version`
- `model_provider`
- `model_name`
- `generation_mode`
- `safety_version`
- `human_review_status`

Confirmed:

```bash
curl http://localhost:8000/reflections
# 200 OK
```

Future cleanup: add proper migration tooling or a schema sync script.