# viewer

Static case-file viewer for rlm-logger. Deployed to `rlm.sh` via Vercel.

```bash
cd viewer
npm install
npm run dev       # http://localhost:4321
npm run build
npm run test:e2e
```

Default demo renders `examples/checkout-incident/incident.rlm.json` + `ground_truth.json`.
Drop any `.rlm.json` file onto the page (wiring pending) or pass `?url=` to load a remote case file.

Design tokens: see `tailwind.config.mjs`. Dark-first, JetBrains Mono + Inter Tight, `#ff6b3d` accent.
