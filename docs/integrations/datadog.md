# Datadog

Export Datadog logs from Log Explorer, then hand them to rlm-logger.

## Export from Datadog

1. Open **Logs → Log Explorer**. Filter to the incident window and service (`service:checkout-worker status:error`).
2. Click the **⚙ → Download as JSON** (or **NDJSON**) button above the list.
3. Save as `dd-incident.json`.

rlm-logger auto-detects all three common Datadog shapes:

- NDJSON with the modern envelope: `{"id": "...", "attributes": {"timestamp": ..., "service": ..., "status": ..., "message": ...}}`.
- The REST v2 response wrapper: `{"data": [{"attributes": {...}}, ...], "meta": {...}}` — the top-level `data` array is auto-flattened.
- Legacy `content` envelope: `{"id": "...", "content": {"timestamp": ..., ...}}`.

Fields normalized: `attributes.timestamp` → `ts`, `attributes.service` → `service`, `attributes.status` → `level`, `attributes.message` → `msg`. Nested `attributes.attributes.trace_id` survives in `raw`.

## Ask

```bash
rlm ask "why are payment-gateway 401s spiking?" \
  --logs ./dd-incident.json \
  --out payment-incident.rlm.json
```

## Notes

- If you have the Datadog CLI and an API key, `datadog-ci` can dump a search result to NDJSON in a shell script — rlm-logger will read that directly.
- `trace_id` fields are preserved in the raw row, so the agent can cross-reference traces when you ask.
