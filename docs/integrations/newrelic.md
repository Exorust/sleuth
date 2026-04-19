# New Relic

Export NRQL results from New Relic One, then point rlm-logger at the file.

## Export from New Relic

1. Go to **Query your data** (NRQL). Run something like:
   ```sql
   SELECT timestamp, service.name, log.level, message, trace.id
   FROM Log
   WHERE service.name = 'checkout'
   SINCE 2 hours ago
   LIMIT MAX
   ```
2. Click **⋮ → Export → JSON** on the result panel.
3. Save as `nr-incident.json`.

rlm-logger auto-detects:

- Flat NRQL rows: `{"timestamp": 1713322684000, "service.name": "checkout", "log.level": "ERROR", "message": "..."}` — epoch ms + dotted keys.
- Wrapped NRQL response: `{"results": [{"events": [...]}]}` — the `events` array is auto-flattened.

Fields normalized: epoch-ms `timestamp` → `ts`, `service.name` (or `entity.name`) → `service`, `log.level` → `level`, `message` → `msg`. `trace.id` stays in `raw`.

## Ask

```bash
rlm ask "why did checkout latency spike at 03:04?" \
  --logs ./nr-incident.json \
  --out checkout-latency.rlm.json
```

## Notes

- NRQL times are milliseconds since epoch. rlm-logger converts to UTC automatically.
- If you use New Relic's `nrql` CLI, pipe to a file: `nrql "SELECT ... FROM Log ..." --json > nr-incident.json`.
