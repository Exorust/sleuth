# Splunk

Export your Splunk search results, then ask Sleuth what happened.

## Export from Splunk

1. Run your SPL in Splunk Web (Cloud or Enterprise). Narrow the time range to the incident window — e.g. `index=prod sourcetype=checkout-worker earliest=-2h@h latest=@h`.
2. Above the results table, click **Export** → **JSON**.
3. Save the file locally as `incident.json` (or `.jsonl` — either works).

Sleuth auto-detects both Splunk shapes:

- The wrapped `{"preview": false, "offset": 0, "result": {"_time": ..., "_raw": ...}}` one-line-per-event export.
- The flat variant where each line is the `result` dict directly.

Fields normalized: `_time` → `ts`, `sourcetype`/`source`/`host` → `service`, `level`/`severity` → `level`, `_raw` → `msg`.

## Ask

```bash
sleuth ask "why did checkout start returning 5xx around 02:58?" \
  --logs ./incident.json \
  --out checkout-incident.sleuth.json
```

Open the case file in the [viewer](https://exorust.github.io/sleuth/viewer/) or paste the `root_cause` + `remediation` into your postmortem doc.

## Notes

- Logs never leave your laptop. Sleuth reads the file locally, runs the agent locally, and writes the case file locally.
- Sensitive fields (Bearer tokens, Stripe keys, AWS creds) are redacted at ingest before anything hits the LLM.
- Large exports are fine — ingest streams line-by-line and caps at 2 GiB / 50M rows.
