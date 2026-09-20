# BCI Arena MVP

English static EEG evaluation workbench. Data is imported from `src/data/mvp.json`, which the parent experiment pipeline exports after independent review.

The page offers three task-specific comparisons, configuration details, model and dataset catalogs, research updates and downloadable CSV/JSON. Research-only catalog entries have no scores.

- `npm run dev -- --background`: temporary local preview.
- `node scripts/check-workbench.mjs`: application-state and public-export checks.
- Build and publish through the installed Sites workflow using the existing `.openai/hosting.json` project.
- Stop the development preview with `astro dev stop` after work.

See `VALIDATION.md` for test scope. No backend GPU, raw EEG, checkpoint distribution, telemetry SDK or automated local updater is needed by the site.
