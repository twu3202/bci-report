# BCI Report validation

## What is checked

`scripts/check-workbench.mjs` exercises the page's application state with minimal
DOM doubles: protocol switching across all eight tracks, family filtering, sorting,
the empty state, both dialogs, download links, invalid tool input, CSV row counts
and English-only data. It also pins the caveats that must travel with a number
rather than live only in a dialog — the seed rank on seed-tested tracks, the
always-abstain count on the idle track, and the chance-level flags and reference
line on every task with a defined chance level. It also checks the four built topic
pages, their canonical/breadcrumb/download metadata, the 82-row/18-contrast/5-seed
extension shape, byte identity between source and downloadable JSON, and the
protocol distinctions that must remain separate.

The protocol pages (`/protocols/` and `/protocols/<id>/`, both languages, since
2026-10-02) are held to the dataset and method page checks — every figure carries
`data-fig` and is re-read from the protocol's own results CSV or protocol JSON —
and, on top of that: every method with a score has a row with all of its figures,
the chance flags and single-seed flag travel with the number, the chance level (or
why there is none) is printed, each matrix method not run is named beside the
"not a failure" caveat, the payload's protocol text is printed verbatim, the
English page carries Dataset markup whose distribution is the protocol's CSV and
JSON, every local link resolves, and the dataset and method pages and the home
matrix's column headings link to it. Each table row must equal the same row of
the protocol's results CSV, column by column and in order. Two payload fields are
deliberately not verbatim: the privacy review (reviewer notes; the page prints one
site-written sentence and links the protocol JSON that holds it) and a JSON
fragment in the release version (printed as "mirror … · upstream …"). A protocol
without a chance level (idle) must not promise one in its description, dek or
markup.

The independent review of the 2026-10-02 merge added: "later recording" (and
之后的记录 / 之后一段) may appear only in a sentence about one rate, on every page,
Markdown copy, agent file, the feed and the extension export, because LTRSVP run b
is later than run a only within a rate; the image-rate section states the
presentation order the original publication reports and what PhysioNet does not
document; the dataset pages print the people behind each paired mean beside it;
the YSU short answer qualifies the personal threshold; each scrolling table in the
non-control section has its own name; the Chinese register prints the English
original beside each licence and rights-review note; and the chart colours in
`workbench.ts` must equal the legend swatches in `generated.css`.

```sh
node scripts/check-workbench.mjs        # from site/
npm run build
cd .. && .venv/bin/python -m unittest discover -s pipeline/publication -p 'test_*.py'
cd .. && .venv/bin/python pipeline/publication/check_site_artifact.py
```

Since 2026-10-02 it also holds the discoverability and citation layer to its
sources: the served `og.png` must be the bitmap `generate-brand-assets.py`
recorded in `scripts/brand-assets.json` (a text check cannot see the badge that
outlived the site's), with its size and alt text on every page; the home Dataset
markup must carry the newest release, every served file and every topic Dataset;
`/releases.xml` must list every release with each file's served size and SHA-256;
only `/data/*` may be read cross-origin; every topic, dataset and method page must
end with a "Cite this page" block naming exactly the releases its figures come
from, in both languages and in its Markdown copy; names that live in table
buttons or `#` links must survive into the Markdown tables; and `LICENSE`,
`LICENSE-DATA`, `CITATION.cff` and `.zenodo.json` must agree (the last is written
by `scripts/write-zenodo-metadata.mjs`; re-run it after the build when a dataset
page is added).

Also since 2026-10-02: the LaBraM adaptation result and the next-day statuses are
their own topic, `/topics/model-adaptation/`, and every check that pinned them on
`/topics/calibration-budget/` moved with them (arm, contrast, seed and cost
figures; the matrix readout beside the head-only arm; no winner between LoRA and
the last block; the Alpha Waves −1.6 pp exclusion slice; a figure-free next-day
section, now with the cross-session status). The page, its card, its snippets and
the EEGMAT and LaBraM groups must call the evidence "new people, same task, zero
labels from the test person"; calibration-budget keeps figure-free notes at
`#adaptation` and `#next-day`; every holds-register link must land on an anchor.
A topic that prints a figure from another file marks it with `data-fig`, which is
re-read from that file, and its cite block must name that file's release — so a
topic that prints the core matrix's frozen LaBraM readout names the core release.
And every topic page carries a "Measured on … · Methods …" line under its hero
that links exactly the dataset and method pages whose result groups point at it,
in both languages and in its Markdown copy.

`check_site_artifact.py` now compares the built payload against the recorded build
and **fails on drift**; re-run it with `--accept` after an intended change. Before
2026-09-20 it overwrote the record with whatever was on disk, so it could not
detect a hand-edited `dist/`.

## What is NOT checked

- The automated checks are not a browser visual review or an accessibility audit; the manual browser coverage is recorded below.
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

The existing public site is bci.report. Contact addresses are configured in
`src/data/site.ts`. The four-topic extension has been built and reviewed locally;
this task has not deployed it. The publishing session should deploy only the
reviewed `site/dist` payload, never the repository, local research directories,
or the superseded Git history.

The topic export is generated by
`pipeline/publication/export_deployment_topics.py` from pinned reviewed evidence.
The artifact check reproduces that export and rejects drift in either its page-data
or public-download copy. New benchmark runs do not enter this release automatically.

Local browser QA for the four topic pages covered desktop and 390-pixel mobile
layouts, navigation, the homepage cards, and console errors. A table positioning
fix prevents hidden accessibility labels from widening the mobile page. This is
not a comprehensive accessibility audit. The temporary preview is stopped after QA.
