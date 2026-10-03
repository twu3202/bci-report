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
fragment in the release version (printed as "mirror … · upstream …"). Beside the
privacy sentence the page must print the dataset's reviewed rights note from the
public-data register (verbatim on `/`, the Chinese with the English beside it on
`/zh/`), and the sleep protocol its consent caveat, each claim of which must be in
the released review note; no other protocol carries one. The home page's protocol
dialog must apply the same treatment, and its privacy sentence must equal the
protocol page's. A protocol without a chance level (idle) must not promise one in
its description, dek or markup, and its dek must name the idle false-activation
rate.

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

Its follow-up review added: the LTRSVP matrix note must say that the diagonal is
the same-rate run b after a long break; the YSU extension's non-control table ends
with a pooled row for both rules, read from the export, which must be the sum of
the states above it (the short answer's "fewer overall" reads it); a dataset page's
cite block names one upstream dataset, a topic page's several; the model-adaptation
hero eyebrow names both halves of the page without the "zero labels" label, which
stays on `#adaptation`, and `#next-day` must say that design uses the test
person's own day-B labels; the calibration-budget `#next-day` note has a heading
that stands on its own; any "RSS" on the model-adaptation page, in any case, fails
the memory check; and that page's Dataset markup names the engineering check's
file in `distribution` but nothing from it in `variableMeasured`.

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
plus the core-matrix rows it prints through a protocol page (the idle table on
when-not-to-act, the frozen LaBraM readout on model-adaptation), in both languages
and in its Markdown copy.

Also since 2026-10-02, the home page and its hubs: one main navigation on every
page (Questions, Results, Protocols, Methods, Datasets, Releases, API, Data use),
with the current page marked; the Questions hub `/topics/` as every topic page's
middle breadcrumb, and BreadcrumbList on English topic and entity pages; every
topic card exactly once under its group, and every number a card prints is a
cohort size pinned to its payload or a value of that payload; the transfer-coverage
map (home and hub) prints cohort sizes only — each `data-fig` re-read and the key
entries pinned to their payload field, no score, held entries figure-free and
linking only the holds register, not-measured entries with no link; hold cards are
links that land; the corrections link counts the register; the directory band
counts what it links to; the old home anchors `#models`, `#datasets`, `#news` still
land; and the moved sections are complete — every model card on `/methods/` with
when its status was checked (REVE Base with its display-layer override, source and
released status), every field note, every register row on `/datasets/`.

Since 2026-10-03, the large-source batch (`large-source-update.json`): Dreem sleep
staging has its own question, `/topics/sleep-staging/`, and OpenBMI broadened
`/topics/calibration-budget/` (`#next-session`); each source has a dataset page.
Every figure on the new sections carries `data-fig` and is re-read from the
export, the same figures appear in both languages, and every figure-like token
there (one-decimal percentages, pp, kappas, grouped counts) must be a value of the
export formatted as the site formats it, or a number in the export's own text — a
typed figure, or one from the unpublished 40-person OpenBMI snapshot, has nothing
to match. Dreem: DOD-H and DOD-O each in its own section and dataset group, never
pooled; an arm's accuracy is never printed without the same arm's balanced
accuracy within 220 characters (page, description, dataset page), and shares its
table row or sits in the adjacent dataset row; a null (the N1 precision of a stage
never predicted) is a dash with its reason, never a number, one dash per null;
every "chance" (随机水平) on those pages is a denial, and no Dreem plot or group
carries a chance line; no cross-cohort comparison and no clinical or diagnostic
claim; the record and epoch accounting add up and are printed; the hold is
figure-free on the page, in the register, on the home card and on the map; the
credits (paper, deposit DOI, pinned repository revision, MIT as the deposit
declares it) and each cohort's statements — as the paper gives them, and which one
is missing — are printed. OpenBMI: 54 = 1 + 2 + 51, 3,060 held-out trials, 408
jobs; the protocol; both baselines at every budget with intervals; every mean
change carries how many people declined, in its own cell and within reach wherever
its pp is printed (short answer and descriptions included); a change whose interval
includes zero says it is not established, exactly then; the cohort is expanded,
not a replication, and the earlier snapshot is history. These checks were
mutation-tested on a copy of `dist/` (`SITE_DIST`): each of 23 injected violations
was caught by the assertion written for it.

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
