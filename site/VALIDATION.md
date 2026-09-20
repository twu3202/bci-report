# BCI Arena validation

## What is checked

`scripts/check-workbench.mjs` exercises the page's application state with minimal
DOM doubles: protocol switching across all eight tracks, family filtering, sorting,
the empty state, both dialogs, download links, invalid tool input, CSV row counts
and English-only data. It also pins the caveats that must travel with a number
rather than live only in a dialog — the seed rank on seed-tested tracks, the
always-abstain count on the idle track, and the chance-level flags and reference
line on every task with a defined chance level.

```sh
node scripts/check-workbench.mjs        # from site/
npm run build
cd .. && .venv/bin/python -m unittest discover -s pipeline/publication -p 'test_*.py'
cd .. && .venv/bin/python pipeline/publication/check_site_artifact.py
```

`check_site_artifact.py` now compares the built payload against the recorded build
and **fails on drift**; re-run it with `--accept` after an intended change. Before
2026-09-20 it overwrote the record with whatever was on disk, so it could not
detect a hand-edited `dist/`.

## What is NOT checked

- This is not a browser visual review, and not an accessibility audit.
- The optional WebMCP tool is feature-detected and its mocked contract is checked.
  No supported-browser WebMCP integration has been exercised end to end. The normal
  page controls work without that experimental API.
- Passing the artifact scanner is not proof of anonymity. It matches known-bad
  shapes; it cannot recognise participant-level data published under an innocuous
  key name, nor reason about reconstruction from small denominators.
- Nothing here checks `site/.git`, only `site/dist`.

## Known state at 2026-09-20

Experiment evidence is reviewed outside the website; the export bridge accepts
additions only after their `independent-audit.json` passes, and no unreviewed
literature result enters the workbench.

Open before public launch: no public contact address is published (`src/data/site.ts`
holds the single switch, and the data-use page renders an honest "not yet published"
state until it is set); the Cloudflare account, domain and deploy have not been
created or verified; `site/.git` history still contains per-participant rows from an
earlier export, so the deploy scope must stay `./dist` (pinned in `wrangler.jsonc`).
