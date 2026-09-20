# BCI Report

An English-language workbench for public EEG evaluation. Every score is reported
with the protocol that produced it — cohort, electrode count, training budget,
chance level and known limitations — rather than as a universal model ranking.

**Status: research preview `research-preview-20260920`, not yet launched.**
8 protocols · 7 distinct datasets · 39 displayed configurations · 9 methods.

> ### ⚠ Before making this repository public
>
> It is private for a reason. `docs/` and parts of `research/` contain local
> machine paths (`/Users/…`, `<evidence-root>/…`, `<workstation-home>/…`), the two
> workstation hostnames, and internal planning notes — including the prelaunch
> handoff, which says on its own first page that it is internal. None of it is a
> credential and none of it is participant data, but it is not written for
> publication. Review `docs/` and `research/` before changing visibility.
>
> Raw EEG, model weights and per-participant results are **not** in this
> repository and must not be added — see `.gitignore` and `/data-use/` on the site.

## Layout

| Path | What it is |
|---|---|
| `site/` | The Astro static site. The page reads only `site/src/data/mvp.json`. |
| `pipeline/publication/` | The release boundary: `export_snapshot.py` builds the public snapshot from reviewed runs; `check_site_artifact.py` inspects the built payload. |
| `pipeline/` | Literature catalogue, verified-result store, news ingestion with a manual approval gate. |
| `data/` | Hand-maintained catalogues (models, benchmarks, verified results, curated news). |
| `docs/` | Plans, run records and result interpretation notes. Internal. |
| `research/` | Rights and privacy review evidence, screening and acquisition records. |
| `experiments/` | **Not in git.** Raw data, prepared arrays, weights, run outputs (7+ GB, local and on the Gal4 SSD). |

## What is published

Only cohort-level aggregates. The flow is: private sources → fixed local
experiments → independent audits → source and model release decisions →
field-selected export → `site/dist/` → host → visitor. Raw EEG, trial rows,
participant identifiers, embeddings, trained heads and pretrained weights never
cross the export boundary. Aggregate publication does not by itself resolve
every upstream processing right, which is what the review evidence in
`research/publication_review_20260920/` is for.

## Checks

```bash
cd site && npm run build && node scripts/check-workbench.mjs
.venv/bin/python -m unittest discover -s pipeline/publication -p 'test_*.py'
.venv/bin/python -m unittest discover -s pipeline/tests -p 'test_*.py'
.venv/bin/python pipeline/publication/check_site_artifact.py
```

`check_site_artifact.py` compares the built payload against the recorded build
and fails on drift; re-run with `--accept` after an intended change. Passing it
is not proof of anonymity — it matches known-bad shapes and cannot reason about
reconstruction from small denominators. See `site/VALIDATION.md`.

Regenerating the published snapshot needs the Gal4 SSD mounted:

```bash
.venv/bin/python pipeline/publication/export_snapshot.py \
  --manifest research/publication_review_20260920/release-manifest.json \
  --legacy   research/publication_review_20260920/previous-mvp.private.json \
  --batch    <evidence-root>/benchmarks/parallel-v1/20260919/batch-state.json \
  --beta-root <evidence-root>/benchmarks/beta-ssvep-v1/run-20260913-mps-v2 \
  --output   research/publication_review_20260920/release-output
```

Then copy `mvp.json` to `site/src/data/` and `data/*` to `site/public/data/`.

## Open before launch

1. **The domain receives mail but does not send it.** `contact@bci.report` and
   `privacy@bci.report` are live and were verified end to end on 2026-09-20
   (public-resolver MX and SPF, verified destination, enabled rules, catch-all
   left at `drop`, and a real message from an outside mailbox delivered).
   Cloudflare Email Routing is inbound forwarding only, and sending *as* the
   domain was declined for now on cost, so replies come from the maintainer's
   own mailbox — `/data-use/` says so. No `_dmarc` record exists yet; a
   non-sending domain wants a strict policy, and adding sending later means
   revisiting SPF, DKIM and DMARC together. One switch for all of it:
   `site/src/data/site.ts`.
2. **Not deployed.** `bci.report` is registered and its zone is in the account.
   `site/wrangler.jsonc` pins the deploy scope to `./dist` — a dry run resolves
   to the same 28 files `check_site_artifact.py` accepts — but nothing has been
   published. The OAuth token wrangler obtains carries `zone:read` only, which
   is the whole zone scope the login flow offers, so DNS and Email Routing
   changes need the dashboard or a scoped API token.
3. The superseded `site/.git.superseded-20260920` holds the previous single-commit
   history, which contained per-participant rows. It is local only and is
   gitignored. Do not push it anywhere.
