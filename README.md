# BCI Report

An English-language workbench for public EEG evaluation. Every score is reported
with the protocol that produced it — cohort, electrode count, training budget,
chance level and known limitations — rather than as a universal model ranking.

**Status: research preview `research-preview-20260920`, live at <https://bci.report>.**
8 protocols · 7 distinct datasets · 39 displayed configurations · 9 methods.

The same 39 results are mirrored as a Hugging Face dataset,
[`Twu31/bci-report`](https://huggingface.co/datasets/Twu31/bci-report), built by
`pipeline/publication/build_hf_dataset.py` from the payload the site already
serves — no second export path, so both mirrors pass the same gate.

> ### Scope of this repository
>
> Raw EEG, model weights and per-participant results are **not** here and must
> not be added — see `.gitignore` and `/data-use/` on the site.
>
> `docs/` is gitignored: internal planning, run records and interpretation
> notes, written for the operator and a reviewer rather than for readers. It
> stays on disk and out of the public record. Absolute paths are gitignored the
> same way (`pipeline/publication/local_paths.json`); everything committed uses
> `<evidence-root>/`, `<repo>/` and `<workstation-home>/` placeholders instead of
> naming one machine's directory layout.

> ### The name `bciarena` still appears, on purpose
>
> The project was renamed from BCI Arena on 2026-09-20. Two places keep the old
> string and should not be "fixed":
>
> - `run_by: "bciarena"` is a stable internal provenance tag written into every
>   `verified_results.csv` row. It is never displayed; renaming it would
>   invalidate the existing store. See the comment at `pipeline/validation.py`.
> - `research/` holds dated records of decisions made when the project was still
>   heading for `bciarena.ai`, including why that domain was dropped. Editing
>   them to match a later rename would make the evidence trail say something
>   that was not true at the time.

## Layout

| Path | What it is |
|---|---|
| `site/` | The Astro static site. The page reads only `site/src/data/mvp.json`. |
| `pipeline/publication/` | The release boundary: `export_snapshot.py` builds the public snapshot from reviewed runs; `check_site_artifact.py` inspects the built payload. |
| `pipeline/` | Literature catalogue, verified-result store, news ingestion with a manual approval gate. |
| `data/` | Hand-maintained catalogues (models, benchmarks, verified results, curated news). |
| `docs/` | **Not in git.** Plans, run records and interpretation notes. Internal. |
| `research/` | Rights and privacy review evidence, screening and acquisition records. |
| `experiments/` | **Not in git.** Raw data, prepared arrays, weights, run outputs (7+ GB, local and on an external volume). |

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

The release tests and the export both need the run outputs, which live on an
external volume. Copy `pipeline/publication/local_paths.example.json` to
`local_paths.json` and point it at your own; without it the tests that read real
runs skip rather than pass quietly. Regenerating the published snapshot:

```bash
.venv/bin/python pipeline/publication/export_snapshot.py \
  --manifest research/publication_review_20260920/release-manifest.json \
  --legacy   research/publication_review_20260920/previous-mvp.private.json \
  --batch    "$(jq -r .batchState pipeline/publication/local_paths.json)" \
  --beta-root "$(jq -r .betaRoot pipeline/publication/local_paths.json)" \
  --output   research/publication_review_20260920/release-output
```

Then copy `mvp.json` to `site/src/data/` and `data/*` to `site/public/data/`.

## Still open

1. **Zone settings live outside this repository.** HTTP→HTTPS is a zone switch
   (Cloudflare → SSL/TLS → Edge Certificates → Always Use HTTPS), enabled
   2026-09-20; `http://bci.report/` now answers `301` to the HTTPS origin. It
   could not have been fixed from here: `_redirects` matches path only and
   explicitly does not support scheme or domain rules — a rule was written,
   deployed, proven ineffective and removed. The same ceiling applies to
   everything else at the zone: the OAuth token wrangler obtains carries
   `zone:read` only, which is the whole zone scope the login flow offers, so
   DNS and Email Routing changes need the dashboard or a separately created API
   token.
2. **The domain receives mail but does not send it.** `contact@bci.report` and
   `privacy@bci.report` are live and were verified end to end on 2026-09-20
   (public-resolver MX and SPF, verified destination, enabled rules, catch-all
   left at `drop`, and a real message from an outside mailbox delivered).
   Cloudflare Email Routing is inbound forwarding only, and sending *as* the
   domain was declined for now on cost, so replies come from the maintainer's
   own mailbox — `/data-use/` says so. DMARC is `p=reject`, which is what a
   non-sending domain wants; adding sending later means revisiting SPF, DKIM and
   DMARC together. One switch for all of it: `site/src/data/site.ts`.
3. **The host injects an analytics beacon.** Cloudflare Web Analytics adds
   `static.cloudflareinsights.com/beacon.min.js` to every response at the edge.
   The site's own CSP (`script-src 'self'`) blocks it, so it does not execute,
   and `/data-use/` remains accurate as written. If Web Analytics is ever wanted
   for real, both have to change together — the CSP to let it load, and that
   sentence to disclose it.
4. The superseded `site/.git.superseded-20260920` holds the previous single-commit
   history, which contained per-participant rows. It is local only and is
   gitignored. Do not push it anywhere.
