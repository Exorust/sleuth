# Honeycomb

Export Honeycomb events from a query, then let Sleuth read them.

## Export from Honeycomb

1. Open your dataset in Honeycomb. Build a query for the incident window, e.g. filter `service.name = payment-gateway` with `error.message exists`.
2. On the results, click **⋯ → Download as JSON**.
3. Save as `hc-incident.json`.

Sleuth auto-detects:

- Events-API shape: `{"time": "...", "samplerate": 1, "data": {"service.name": "...", "level": "...", "error.message": "...", "trace.trace_id": "..."}}`.
- Query response wrapper: `{"events": [...]}` — the array is auto-flattened.

Fields normalized: `time` → `ts`, `data.service.name` (or `data.service`) → `service`, `data.level` (or `data.log.level`) → `level`, `data.message` / `data.error.message` / `data.name` → `msg`. `trace.trace_id` stays in `raw`.

## Ask

```bash
sleuth ask "what caused the error spike on payment-gateway?" \
  --logs ./hc-incident.json \
  --out payment-incident.sleuth.json
```

## Notes

- Honeycomb's structured data is the highest-signal input of the four integrations. Dotted keys (`service.name`, `trace.trace_id`) survive into `raw` and the agent can cite them directly.
- Sample-rate is preserved in the raw row so the agent knows when it's looking at sampled data.
