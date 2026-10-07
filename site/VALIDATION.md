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

Since 2026-10-04, route 1 of the decision-research roadmap, reliable decisions
(`reliable-decisions-update.json`, owner approved): its own section on
`/topics/when-not-to-act/`, `#reliable-decisions`, after the idle methods and
limits and before `#decision-research`, whose slice stays a figure-free plan.
The roadmap now carries one status per route (`data-route-status`: route 1
`run`, linking its results; routes 2 and 3 `not_run`, linking nothing), the
section `data-status="plan"` and `data-run-status="route-1-run"`, a status line
and a Jev scope sentence that say so, and none of the old "no experiment has
been run" wording. In the new section every figure is a leaf of the route-1
export (`data-fig`, re-read by the topic loop), the same multiset in both
languages, and every figure-like token is a value of that export as the site
formats it (a new format, `sgn3`, prints signed three-decimal differences of
AURC, NLL and ECE). Pinned there: BETA and EEGMAT methods in the export's order,
never re-sorted; each method's fixed-threshold coverage with its score bar and,
in the same row, how many people had nothing accepted; nothing accepted is a
dash and "not defined", never 0% (the fixed-threshold error, S-risk's error and
its error-minus-target); fewer than ten accepted is a count of wrong among
accepted with an "unstable" flag, never a rate; every contrast cell carries the
verdict its interval supports, matched exactly ("no difference resolved"
contains "difference resolved"), on the coverage pairs, the matched-coverage
pairs, both learned-reject contrasts, error minus target and the four
recalibration changes; the EEGMAT matched coverage is unstable with no verdict
and no rate; certified folds, folds over their own target and a "nominal
guarantee", never a guarantee; labels per new person in every recalibration
row; the LoRA sentence with its figures and link; raw probability quality "not
applicable", never a number, where a score has none; the robustness panel
collapsed by default, ds003810 in it and labelled crude, the sensitivity arms as
fold counts with no accuracy, and the idle protocol and the BNCI2015-001 arm
figure-free with the hold's register row linked; every required limitation in
the page's language; "deployment rate" only negated, no ranking word, no
out-of-distribution claim; the three recordings' credits and the six method
sources; the audit counts. The EEGMAT, BETA and ds003810 pages carry a route-1
group with the people who had nothing accepted and each contrast's verdict
beside its figure, and the EEGNet, LaBraM, CBraMod and CCA pages its rows; the
when-not-to-act Dataset markup names the file; the release log, data use and the
home card's cohort pins include it. These checks were mutation-tested on a copy
of `dist/` (`SITE_DIST`): each of 28 injected violations was caught by the
assertion written for it.

Also since 2026-10-04, the v9 foundation-model boundary
(`foundation-models-update.json` and one `foundation-models-<protocol>.csv` per
core protocol, owner approved): eleven further models, sixteen encoder
checkpoints, as frozen probes on the eight core protocols, nine adapted on
EEGMAT. The batch's files are registered (release log, feed, API page, home
Dataset markup) before any page prints them; the pages come in a later commit.
Read from `dist/`: the served JSON is byte-identical to the source; one result,
no status-only source and no hold; the eight core protocols in the matrix order;
sixteen checkpoints, thirteen matrix rows before the three masking-ablation
siblings; no v9 row in the released matrix (`experiments.json` keeps its bytes);
one cell per checkpoint and protocol, and the two cells not run (BrainOmni on the
two one-second ERP protocols) null with their reason, never 0. Pretraining
exposure is the owner's sourced statement: a dataset absent from the authors'
list reads "not in the authors' published pretraining list (checked
2026-10-04)", no statement says "not exposed" or claims proof, ST-EEGFormer on
BETA and SingLEM on TMNRED are the only exposed cells, every ZUNA 1.1 cell and
only those is unknown, every cell carries its statement, and LaBraM and CBraMod
are absent from their authors' lists on all seven datasets with a source link
each; ZUNA 1.1's research-use sentence travels with its rows. Each CSV starts
with its core results CSV's columns and carries the core protocol's values in
them; every row fits the header; one row per checkpoint in the JSON's order;
name, panel and exposure statement equal the JSON; `scoring_seconds` is empty
(timings came from a shared GPU and are not published); a cell not run is empty
with its reason; idle rates are the counts over 60 and the abstaining people the
JSON's; balanced accuracy and its interval are the JSON's in percent; and the
chance flag, in the CSV and in the JSON, follows the interval and the released
chance level. The release log names the batch and its manifest. The CSVs carry
100 × the proportion rounded to 12 decimals, so a tie such as 63.25 prints as
63.3, as the approved handoff does; a page should print matrix figures from the
CSV (`pct1raw`), not the JSON proportion. These checks were mutation-tested on a
copy of `dist/` (`SITE_DIST`; where an assertion reads the source export, the
source too, restored afterwards): each of 32 injected violations was caught by
the assertion written for it. `check_site_artifact.py` re-derives the JSON and
all eight CSVs from the pinned inputs and holds the nine files to their export
audit (`foundation-models-export-audit.json`); the export itself re-resolves
every traced figure of the release candidate and checks each frozen-probe, idle
and adaptation figure against the approved handoff's tables, row by row
(`pipeline/publication/test_foundation_models_update.py` forges each link).

The v9 rows on the pages (same day, owner approved): each protocol page has a
section of its own, `#foundation-v9`, after the released table and before the
limits, and the home page's per-protocol table a group under the released rows.
On every protocol page, in both languages: thirteen matrix rows in the export's
family order, never re-sorted, and the masking ablation in its own collapsed
panel (the paper-recommended row, then its three siblings); each row equals its
CSV row column by column and in order, every figure from that CSV; a cell not
run (BrainOmni on the two one-second ERP protocols) prints "Not run" with the
export's reason and no figure but its channels, never a zero; the chance flags
follow the core rule (at or below chance, else an interval reaching it) and the
CSV's own flag columns agree; the exposure badge (in the authors' list) or
"Exposure unknown" and the statement are the exposure table's, with a source
link from that cell, ZUNA 1.1 unknown on every cell and only ZUNA 1.1 carrying
the research-use sentence; each row's footnote mark leads to the export's row
footnote; one weights-licence entry per family with its licence note and paper;
the plot is the released rows and every scored v9 matrix row; no ranking word and
no exposure claim beyond the authors' lists. Beside the released pretraining
sentence, which stays verbatim, a dated note gives LaBraM's and CBraMod's
sourced statement with every source link of their cells. On arithmetic-rest the
EEGMAT adaptation (LaBraM for context, then the nine adapted encoders in the
export's order) prints every arm, change, people moved and trainable-parameter
figure from the v9 JSON, the verdict its interval supports, and why the others
were not adapted. Protocol pages now carry a cite block (the core and v9
releases), and their Dataset markup names the v9 CSV. The home page embeds the
rows as JSON (`#fm-rows`), which `workbench.ts` reads and the DOM double is
handed from `dist/`: every value equals the CSV at the precision the table
prints, the chance flag is computed from the CSV's full values, and the prose is
the export's (or the translation table's). The rendered table counts its v9
group, carries each figure, flag, badge and the research-use sentence, the
ablation panel and the CSV link follow the protocol, the first paint of the v9
group equals the script's render, a v9 row's dialog carries its exposure with
source, footnote and licence, and the protocol dialog the dated LaBraM/CBraMod
statement. The snapshot's note counts the v9 matrix rows and says they are not
ranked against it; the matrix key no longer says "Best". The model directory has
one card per entry the export suggests (status, method page, parameters as
`m2` figures, weights licence and note; ZUNA 1.1's research-use sentence, LUNA's
no-endorsement and ERP-FM's non-commercial terms), REVE Base evaluated since
2026-10-04 with the released status beside it, MIRepNet and EEG-DINO catalogue
only, EEGPT unchanged. Each of the ten new method pages has a group per protocol
(a checkpoint not run named with its reason), the EEGMAT adaptation where the
model was adapted, every checkpoint's revision, hash, parameters, licence,
rights review, footnote and notes, and an exposure table per dataset with its
sources and caveats; LaBraM and CBraMod have the same table. Every method page
has a "Measured on … · Protocols …" line linking exactly the dataset and
protocol pages its groups are read on (a group where nothing was run does not count). The seven core dataset pages carry a v9
group per protocol after the released one, EEGMAT the adaptation. The
translation table (`foundation-models-zh.ts`) is keyed by the export's exact
English: every key matches a text of the export and every translation carries
exactly its numbers. does-pretraining-help, model-adaptation and data use state
LaBraM's and CBraMod's exposure as the authors' lists show it, linked and dated,
and the old "unresolved"/"not certified" wording is gone. The protocols index
counts the v9 rows it links to, the release log names the protocols and methods
hubs (and so does the feed), and the sitemap dates every changed page 2026-10-04. Checks that the v9
pages changed: the topic Measured-on derivation counts only bare protocol links
(a v9 group links `#foundation-v9`), the model-card count includes the v9 cards,
and the WebMCP tool returns the v9 rows with their release. These checks were
mutation-tested on a copy of `dist/` (`SITE_DIST`): each of 48 injected
violations was caught by the assertion written for it.

The v9 findings on the questions (same day, owner approved): does-pretraining-help
gains `#v9-encoders` after the pretrained-versus-random controls and before their
methods and limits — sleep (the new rows whose intervals lie above every released
sleep row), BETA (above CBraMod, none above training-free CCA), the EEGMAT
adaptation (LaBraM for context, then the nine encoders in the export's order: the
frozen-probe table's ridge readout, the trained head and LoRA, the paired change
with the people who moved and the verdict its interval supports, both
trainable-parameter budgets; one fixed recipe on one task, not a ranking, LoRA
budgets differ), REVE Base against Large and the masking ablation (each read in
prose, its full table in a collapsed panel), the required limitations in the page's
words and the weights licences; fewer-electrodes gains `#v9-montage` after its two
paired comparisons — BETA at eight and four electrodes and six-channel sleep, for
the released rows and the new ones; model-adaptation a figure-free pointer to the
adaptation table. Pinned from `dist/`: every figure in the two sections is a leaf
of the v9 JSON, the protocol's v9 CSV or experiments.json, and a row figure sits on
an element naming its protocol and row (`data-fm-topic`, `data-core-topic`) whose
values include it; every figure-like token is a value of those files as the site
prints it, or a number in their text; the same figures in both languages, in order;
rows in the export's family order, never sorted; each relation (above, overlapping
or below LaBraM, CBraMod and the best released non-foundation row) is the export's,
and the words the page gives it are the ones it implies; every balanced accuracy
printed with an interval carries the chance flag of the core rule (50% for the
adaptation arms); an exposed cell carries its badge, an unknown one "Exposure
unknown", a cell not in the list none; ZUNA 1.1's research-use sentence travels
with its rows and only those; no ranking word once the denials are set aside, and
no exposure claim beyond the lists. Every claim the prose makes is re-derived from
the export: the encoders above every released sleep row (EEGNet's interval
included) and that no new row clears the best released row on another protocol;
the BETA rows and masking siblings above CBraMod, none above standard CCA, the
exposed cells ST-EEGFormer's and below CBraMod; the adaptation verdicts on each
side; REVE Large at or above Base everywhere, where their intervals separate, and
where the other two size pairs do; the protocols on which no masking pair
separates, and the separated pair changing both factors; the two non-montage
encoders losing accuracy with intervals apart, no new row gaining at four
electrodes with intervals apart, the montage encoders above CBraMod at both
montages, SingLEM below every other sleep row, standard CCA the highest
four-electrode score with no new row above it. For a released row the montage table
states only whether its two intervals overlap: no released file states that
difference. The per-person leak check on fewer-electrodes reads the page without
`#v9-montage` (33.3% is a v9 interval bound there). The Measured-on derivation also
reads the rows a topic prints through a protocol page from the page itself
(`data-core-topic`, `data-fm-topic`), and a topic that prints released rows from
experiments.json must name the core release without having to print the matrix
LaBraM readout. Does-pretraining-help's card counts the v9 checkpoints and
fewer-electrodes' names BETA's people and electrodes; the two new transfer-map
entries (Person: the v9 adaptation; Sensor: BETA, eight vs. four electrodes, a
comparison) are pinned to the export. The release log names both topics, and the
sitemap dates the three topics and the hub 2026-10-04. These checks were
mutation-tested on a copy of `dist/` (`SITE_DIST`): each of 56 injected violations
was caught by the assertion written for it.

The review of the 2026-10-04 batches (2026-10-05) added, for route 1: the export no
longer carries the candidate's promise that class-conditional rows "are given" — it
refuses those rows (acceptance per class, pooled on EEGMAT and ds003810, a spread
over BETA's 40 targets), so its first boundary says they were not carried and
`not_published` names them as they are, and the check holds both; the BNCI2015-001
item in `not_published` carries the date the holds register gives the hold (opened
2026-09-20, restated 2026-10-01); and route 1's roadmap entry, which planned
acceptance per class and reliability, says those were not published in this update
(EN and ZH). Mutation-tested on a copy of `dist/` (the source export too, restored
afterwards): each of 5 injected violations was caught.

For the v9 wording, the same review found rows ranked where intervals overlap: on
BETA standard CCA's interval overlaps EEGNet's (and at four electrodes spectral
ridge's), so "stays the highest row", "the best published non-foundation row" and
"keeps the highest four-electrode score" are gone. The ranking check no longer sets
"best published non-foundation row" aside, and treats "stays/keeps the highest" (仍是
最高) as ranking words. Pinned: the key under each does-pretraining-help table names
the reference row by its point estimate and, where its interval overlaps another
released non-foundation row's, says so (BETA: EEGNet), and claims no overlap where
there is none (sleep); fewer-electrodes' heading, sentence and short answer say no new
encoder lies above standard CCA at four electrodes and name the new and released rows
whose intervals overlap it, the released ones with their figures; the release log (EN,
ZH) and the feed say no new row lies above standard CCA and state BETA and TMNRED as
being in ST-EEGFormer's and SingLEM's published lists, not "pretrained on". The Hugging
Face card is held to the same in `test_hf_card.py`. Mutation-tested on a copy of
`dist/`: each of 11 injected violations was caught.

Data use, 4 October: the section said "no new model" for the whole date, although the
v9 review of the same day added sixteen checkpoints whose weights carry terms. It now
has two entries. Route 1's sentence is scoped to route 1. The v9 entry is pinned: one
row per core protocol carrying its 2026-09-20 rights record, reused unchanged, with its
v9 "Published here" scope, verbatim from the served JSON, and its source, licence and
v9 rows linked; one row per model family listing every checkpoint with its revision
(REVE's named versions included; "revision not in the release" for the three masking
siblings), its licence note and the owner's decision, verbatim; the entry states REVE's
licence accepted by the owner, LUNA's CC BY-ND with no endorsement implied, ERP-FM's
non-commercial terms, ZUNA 1.1's research use, that no author endorses the results,
that exposure is not proof, that timings and memory are not published and that the
audits are pinned by hash, and links the release. Mutation-tested on a copy of `dist/`:
each of 7 injected violations was caught.

Licence notes and ZUNA 1.1's sentence travel with the v9 rows everywhere (same review):
on every dataset page's v9 groups and the ZUNA method page, each ZUNA 1.1 row carries
the research-use sentence and no other row does, and its EEGMAT adaptation rows also
say its exposure is unknown; every v9 group on a dataset or method page prints the
weights terms of the checkpoints in its rows — each licence by name, REVE's versions
where REVE is there, no endorsement — and links the protocol page's full list, which
must exist. The weights-licence lists (`FmLicences.astro`) on the protocol pages,
does-pretraining-help and now fewer-electrodes name REVE's versions ("REVE Base @
dc2a075c · REVE Large @ 317531c7", from the export's revisions, because REVE's licence
asks for the version to be named); the protocol pages and fewer-electrodes add that no
model's authors endorse the results (does-pretraining-help says so in its limits).
fewer-electrodes gains one licence entry per family in the export's order, with
licence, note and paper, and the v9 limitations does-pretraining-help carries — small
cohorts (BETA's and sleep's people as figures), descriptive bootstraps with no
multiplicity correction and an occasional non-overlap expected by chance, balanced
designs as method comparisons, new people on the same task and setup, windows shorter
than the pretraining contexts. On the two BETA protocol pages, whose released
limitation says "pretraining overlap unknown", a dated pointer to the exposure
statement follows it, and no other page carries one. Mutation-tested on a copy of
`dist/`: each of 15 injected violations was caught.

Route 1 on the page (same review): its two LaBraM arms print the 1 October adaptation
release's seed-20260922 means, while model-adaptation and does-pretraining-help print
the three-seed means, so the Q1 cells say "the published seed-20260922 mean, 1 October
adaptation release" (no other row's cell names a seed), the lede says which value it
is, and the LoRA sentence says "seed 20260922". Three formats print a second decimal
where one would read as zero (`pp2`, `sgn2`, `pct2`, in `entities.ts` and the
check's `fmt`): a non-zero route-1 figure never prints as ±0.0 or 0.0% on the topic
or the dataset pages, so a lower bound of +0.02 (resolved) and one of exactly 0 (not)
no longer print alike, and one window in 2,160 is a coverage of 0.05%; the route-1
row checks pick the same format. ds003810's contrasts are called secondary, not "no
primary contrast" beside printed contrasts; the rejection paragraph no longer sets
BETA's gain against EEGMAT's ("only"), and says the two are not compared; and
model-adaptation gains a figure-free pointer to the LoRA sentence (`#rd-lora`), which
must land. Mutation-tested on a copy of `dist/` (both languages and the Markdown copies
where the figure parity and copy checks would otherwise fire first): each of 11
injected violations was caught.

The home table (same review): the v9 rows' long checkpoint names, their modes and ZUNA
1.1's research-use line inherited the table's `nowrap`, so the first column grew from
234 px to 364 px and no score was visible at 375 px, and the table overflowed at
1280 px. They now wrap; the DOM doubles cannot measure layout, so the built CSS is held
to the wrapping rule and to left-aligned names. Measured with headless Chromium on a
`file://` copy of `dist/`, every protocol tab, EN and ZH: the first column is 227–283
px at 375 px (the widest is a released row's mode, as before), with the score column
on screen, and the table fits 896/896 at 1280 px. The v9 group's heading says how many
of its rows were not run on that protocol ("· 1 not run on this protocol", so 13 rows
agree with the protocols index's 12 scored), and the snapshot note says BrainOmni Base
ran on six of the eight protocols. Mutation-tested on a copy of `dist/` (the client
script's source too, restored afterwards): each of 5 injected violations was caught.

The Markdown copies of the new sections (same review). The generic copy check only
looks for figures in elements whose class is exactly `metric`, `num` or `fig`, and
accepts them anywhere in the copy, so most interval bounds and coverages in the route-1
and v9 sections were not held to their copies, and `llms-full.txt` is assembled from
those copies. For `#reliable-decisions`, every protocol page's `#foundation-v9`,
`#v9-encoders`, `#v9-montage` and every route-1 and v9 group on the dataset and method
pages, in both languages, the check now takes the printed `data-fig` texts in order and
requires them as an ordered subsequence of the matching section of `index.md` (found
by its heading, ending at the next heading of the same level), each occurrence bounded
as a number; and every decimal, percentage or grouped figure at least as often in the
copy as on the page outside SVG, `aria-hidden` and visually hidden labels (a plot's
value list repeats a table's figures, so order alone could match the plot and miss a
changed cell). Every English copy that `llms-full.txt` assembles must be in it
verbatim. About 7,600 figures are read. Mutation-tested on a copy of `dist/` with the
review's five changes (route-1 EN and ZH 28.4%→28.5%, a C2 bound +1.6→+1.9 pp, a
beta-8ch v9 bound 41.9%→42.9%, fewer-electrodes 37.0%→37.9%) and seven more (an order
change, `llms-full.txt` alone, a dataset and two method-page groups): each of 12 was
caught, one of them first by the generic check.

The v9 export's own prose (same review): it carried the candidate's limitation
"EEGMamba not exposed at medium confidence" and the approval as "user-approved". The
export now restates the exposure limitation as the authors' published lists show them
(checked 2026-10-04; not proof), names the approval "owner-approved", and says in its
wording rule that a cell's confidence rates how closely its source enumerates the
corpus, not how certain it is that the recordings were never seen; it refuses a
candidate whose exposure limitation reads otherwise. Pinned: no "not exposed" and no
"user-approved" in the JSON or any CSV, the restated limitation and the confidence
sentence (the translation table follows the new English). The idle protocol page's v9
lede no longer promises an interval rule its counts cannot follow: it says they are
counts with no interval, so no row is called above or below another, and only the
protocols with intervals state the overlap rule. Mutation-tested on a copy of `dist/`
(a served file edited with its source and its listed SHA-256, at the same size): each
of 5 injected violations was caught.

The Chinese protocol pages' "第九轮各行的说明" (notes on the v9 rows) printed the CSV's
English only, while footnotes and licences beside them were in Chinese. The CSV's notes
join the export's sentences (the model's, then the cell's); each sentence is now in the
translation table and printed in Chinese with the English beside it, and the build
refuses a row whose CSV notes are not those sentences. Pinned: the English page prints
the CSV's notes verbatim, the Chinese page every sentence in Chinese with its English
original, and every translation carries exactly its English's numbers (the existing
table check). Mutation-tested: each of 4 injected violations was caught.

The home page's v9 row dialog (same review) prints the notes in the page's language
(the Chinese with the English beside it) and, for REVE, the model version its licence
asks to be named ("Model version: REVE Large @ 317531c7"). The embedded rows carry
both (`notes`, `notesOriginal`, `version`) and are held to the export: a version for
the REVE checkpoints only, the notes as the protocol pages print them. Mutation-tested
(the client script's source too, restored afterwards): each of 3 injected violations
was caught.

The follow-up review of the same batches (2026-10-05) found REVE's two row footnotes
stating the no-mean-removal sensitivity run with every sign reversed: the candidate's
"changes P300 by -0.71 and sleep by +1.40" are the aggregate's primary-minus-sensitivity
differences. The export now restates both from the aggregate's two balanced accuracies
("scores P300 0.71 percentage points higher and sleep 1.40 lower"; REVE Large "P300 2.06
… lower and sleep 0.93 lower"), refuses a footnote whose direction or size disagrees with
them and a candidate footnote it has not read, and the REVE notes say the run "is stated
in the row footnote" (the site publishes it nowhere else). The manifest records every
restatement of the candidate's text (`restatements`: these two, the exposure limitation
and "owner-approved"), and the export requires that record to be exactly what it does.
Pinned: neither "changes P300 by" nor "reported separately" in the JSON or any CSV, each
REVE footnote's size and direction in the JSON and every CSV row, the note, and 高/低 in
the Chinese (numbers alone cannot tell them apart). Mutation-tested on a copy of `dist/`
(the source export and translation table too, restored afterwards): each of 4 injected
violations was caught.

Same review: BrainOmni's BETA change from eight to four electrodes is exactly
(1451 − 2431) / 11200 = −0.0875, but the export stored the difference of two binary
proportions, −0.08749999999999997, and the pages printed −8.7 pp where the candidate's
−8.75 gives −8.8 (the site rounds exact ties up everywhere else, e.g. 63.25 → 63.3 from
the CSV). The export now stores every difference it derives (large minus base, four
minus eight) rounded to 12 decimals and refuses one that would print otherwise than the
half-up rounding of the candidate's stated value. Pinned: those 37 differences are stored
at 12 decimals, and every one-decimal v9 figure (`pct1`, `pp1`, `sgn1` from
`foundation-models-update.json`) on every page prints as the half-up rounding of its
stored value's 12-decimal form, so a float artefact cannot flip a printed digit.
Mutation-tested on a copy of `dist/`: each of 2 injected violations was caught.

Route 1's file misdescribed itself (same review): `not_published` said it carried no
ds003810 figure other than the fixed-threshold coverage and the learned-reject
contrasts, and ds003810's privacy review (printed in data use's route-1 table) said the
same, while the file carries ds003810's published accuracy, the error accepting
everything, the selective error at the fixed threshold with its count and unstable flag,
and the certified-risk fold counts, all aggregate, and the handoff's own table prints
them. They stay; the item now names what is withheld (secondary seeds and ensembles, the
coverage-target rule, the rankings, probability quality and recalibration) and the
privacy review lists what is published. The export checks every `not_published` item
against the file by its opening words (an item with no check is refused, so a reworded
claim must say how it is checked; three prose items have nothing to look for) and holds
ds003810's methods to exactly the fields the review lists. Pinned: no "every ds003810
figure other than"; each withheld field absent from the file; the data-use row prints
the review and the review names each field the file carries, and nothing more is
carried. Mutation-tested on a copy of `dist/` (the source export too, restored
afterwards): each of 4 injected violations was caught.

The route-1 handoff asks for its required limitations "on any page that shows route-1
results", and the route-1 groups on the EEGMAT, BETA and ds003810 pages and the EEGNet,
LaBraM, CBraMod and CCA pages carried only "a method comparison on a balanced protocol"
and the verdicts (same review). Each now carries, under its rows and without a figure,
its protocol's boundary and the three route-wide limitations that bear on every figure
in it — calibration on cross-fit inner models, rejecting likely errors is not
out-of-distribution detection, the difference rule with no multiplicity correction —
printed from the export (`reliable-decisions-limits.ts` reads them by their opening
words, so a changed export fails the build), in Chinese from a table keyed by that
English, and links `#rd-limits` for the rest; on ds003810 the note and each contrast row
say the contrasts are secondary. The Chinese row note now reads "没有任何试次被接受的被试：
0 名（共 70 名）". Pinned on all 20 groups: the note, its protocol, each sentence (the
export's English verbatim, the table's Chinese), no `data-fig`, the link, "secondary"
on ds003810 and only there; and the table's keys are limitations of the export, with
their numbers, in Chinese, keeping 交叉拟合, 分布外 and 不做多重比较校正.
Mutation-tested on a copy of `dist/` (the translation table too, restored afterwards):
each of 8 injected violations was caught. The out-of-distribution sentence's source URL is
linked as itself; in the first build the Chinese after it (no space before "）。") joined the
link, so each note's one link must have its text as its address, printable ASCII, and be
the export's literature URL (one more injected violation, caught).

The copy check above held the named sections and entity groups, but two places on this
branch still reached the Markdown copies and `llms-full.txt` with nothing holding them
(same review): the home page's per-protocol table (its v9 group and masking-ablation
rows) and the topic pages' short answers (does-pretraining-help's prints v9 figures).
Now, in both languages: each v9 and ablation row of the home table's first paint
carries, in its own row of `index.md`'s matching table and in the same row order, the
page's figure tokens in order (so `llms-full.txt`, held verbatim to the English copy,
carries them too); and every topic page's short answer in its copy (the first paragraph
under its heading) has exactly the page's `[[…]]`-marked figures, in order, as its bold
text. Mutation-tested on a copy of `dist/` with the review's four changes (a home v9
bound in the English copy and `llms-full.txt`, the same in the Chinese copy, and the
does-pretraining-help short answer's 79.6% in each language) and two more (an ablation
row's bound, two rows swapped): each of 6 was caught.

Wording from the same review: when-not-to-act reads the rejection gain per protocol
("is read per protocol; the two are not compared"), not as a cross-protocol "differs by
protocol" (因协议而异); its EEGMAT recalibration sentence counts the NLL rises "with the
interval excluding zero" (three of four; EEGNet's point estimate rose too, unresolved),
re-derived from the export; does-pretraining-help says REVE Large's point estimate is at
or above Base's, since their intervals overlap on three protocols; and no Chinese copy
has a space before a full-width mark (the converter spaced two adjacent elements, so
fewer-electrodes' closing bracket, which opened the next element, read "（−6.1 pp ）";
it is now plain text between them). Mutation-tested on a copy of `dist/`: each of 4
injected violations was caught.

The home page's v9 rows (same review). Their weights terms, REVE's versions and the
no-endorsement sentence were only in each row's dialog: a terms line now sits under the
v9 rows, before the masking-ablation panel, as on the dataset pages (every licence by
name, REVE by version, no endorsement), linking the current protocol page's full list —
the script moves the link with the protocol tab. The snapshot note's "13 further
foundation encoders" now says what they are, from the export: checkpoints of 11 models,
with 3 more of one of them in the masking ablation, 16 in all (the release log and data
use count models and checkpoints). And the v9 group's heading, a cell as wide as the
table, was cut at 375 px after "13 further foundation encoders": its words are now held
in a label that wraps within the visible box and stays there while the rows scroll
sideways (`position: sticky`). Measured with headless Chromium on the built pages, every
protocol tab, EN and ZH, at 320, 375 and 1280 px, with the table scrolled 400 px
sideways too: the heading's text lies within the table's visible box in every case
(two to four lines on a phone), and no page scrolls sideways. Pinned: the terms line
(each licence, REVE's versions, no endorsement, the link), the link following the
protocol in the DOM double, the counts, the label in both first paints and the
script's render, and the built CSS rule. Mutation-tested on a copy of `dist/` (the
client script's source too, restored afterwards): each of 5 injected violations was
caught.

The v9 caveats on the protocol pages (same review). Each `#foundation-v9` lede gave the
grouping rule, but not the multiplicity caveat the topics carry: on every protocol with
intervals it now says each interval is a descriptive participant bootstrap with no
multiplicity correction, and that with 126 frozen cells an occasional non-overlap is
expected by chance (the idle page, whose rows are counts, does not); and on every
protocol that the encoders see its published windows, usually shorter than their
pretraining contexts. EEGMamba's exposure (its list read from the official code, the
paper not read, medium confidence) was stated on does-pretraining-help, the release log
and its method page, but its cells read like the high-confidence ones in the protocol
pages' exposure key and fewer-electrodes' "Pretraining exposure" limitation; both now
say it. Pinned in both languages, with the 126 re-counted from the export. Mutation-tested
on a copy of `dist/`: each of 5 injected violations was caught.

Two released texts the v9 batch overtook (same review). The 2025-10-24 field note on
`/methods/` still says REVE Base "is not yet available in our local test pool": it keeps
its words (`mvp.json` is a released payload), and a dated note after them, dated with the
v9 export, says REVE Base and Large have since been evaluated and links REVE's method
page. And ERP-FM's revision in data use's weights table is a file id whose own text says
"sha256 is the identity", so the checkpoint's SHA-256 is printed beside it. Pinned in both
languages; mutation-tested on a copy of `dist/`: each of 3 injected violations was
caught. Measured with headless Chromium: `/methods/`, `/data-use/` and the other pages
this review changed scroll sideways at neither 320 nor 375 px.

Route 1's file still described ds003810 as carrying less than it does (second follow-up
review of 2026-10-05). Under the fixed threshold each method also carries whole-person
bootstrap intervals for its coverage and, where something was accepted, its selective
error; the certified-risk block carries the rule's settings and what accepting nothing
leaves (n, accepted, a coverage of zero, all ten people with nothing accepted, null
errors), not only fold counts; and the export compared only top-level keys. The figures
stay (no page prints the intervals). The privacy review, printed in data use's ds003810
row, now names them ("each with its whole-person bootstrap interval where defined"; "the
certified-risk rule's settings (delta and target) and fold counts, with nothing accepted:
a coverage of zero, all ten people with nothing accepted, and so no error and no error
relative to the target"), and the export holds every nested field of each ds003810
method — the fixed threshold with nothing or some accepted, the certified-risk block
with its nothing-accepted values, each learned-reject contrast — to that shape, both
where it builds the panel and in the check of `not_published`'s ds003810 item ("What the
file carries for ds003810 is what its privacy review lists"). The manifest, both JSON
copies, the export audit and the build record are refreshed. Pinned: the two phrases on
the data-use row, each block's keys in order, the certified-risk block's values.
Mutation-tested on a copy of `dist/` (the source and served JSON edited together at the
same size, with the listed SHA-256, restored afterwards): each of 6 injected violations
was caught by the assertion written for it; the export tests refuse five more.

The copy checks above read `data-fig` texts, the home table's rows and the short
answers, so v9 figures written as plain text still reached the Markdown copies and
`llms-full.txt` with nothing holding them (same review, second round). REVE's row
footnotes state the sensitivity run's size and direction in words, and a copy (with
`llms-full.txt`) that said "lower" for "higher", 1.41 for 1.40, 2.07 for 2.06 or 低 for
高 passed. Now, in both languages: each protocol page prints one footnote per distinct
row footnote of the export, in order, and its copy's footnote list is exactly those
items, verbatim — in English the export's `row_footnote`, in Chinese the translation
table's text followed by the English; and on every method page with checkpoints, each
checkpoint's copy carries every term the page prints (parameters, revision, licence,
rights, notes, adaptation) as printed, and its row footnote verbatim. `llms-full.txt`,
held verbatim to every English copy, carries them too. About 256 footnotes and 326
terms are read.

Other v9 counts reached the copies outside the regions those checks read (same
review). Now: every transfer-map entry on `/`, `/zh/`, `/topics/` and `/zh/topics/`
carries its figures on its own link line in the copy ("…#v9-adaptation) n=36"); each
topic card's copy line is the card as printed, and the does-pretraining-help,
fewer-electrodes and when-not-to-act cards end with their counts derived from the
exports (16 further checkpoints; BETA, 8 and 4 electrodes, 70 people; route 1's 36 and
70 people); the home snapshot note's copy is the page's paragraph, with its 13, 11, 3,
16 and BrainOmni's six counted from the export; every paragraph after the heading of
each `#foundation-v9`, `#reliable-decisions`, `#v9-encoders` and `#v9-montage` is in
its copy section as printed (whitespace aside), with the 126 frozen cells re-counted on
the seven protocols that have intervals; and the methods hub's model cards carry their
parameters in their own subsections. No v9 or route-1 `data-fig` on any page may lie
outside a region a copy check reads (about 7,500 today), so a figure placed elsewhere
fails until something holds it. Mutation-tested on a copy of `dist/` with the review's
twenty edits (REVE's footnotes on the p300-target, sleep-scalp and REVE pages, EN with
`llms-full.txt` and ZH; the snapshot note's 16, 11 and 13 and the Chinese 共 16 个 and
11 个模型; both map entries and both card counts on the home page and the hub; the 126)
and seven more (two footnotes swapped, a checkpoint's and a hub card's parameters, the
Chinese 126, map entry and card count, route 1's card): each of 27 was caught, 25 by the
assertion written for it and the two parameter edits first by the generic copy check.

`check_site_artifact.py` now compares the built payload against the recorded build
and **fails on drift**; re-run it with `--accept` after an intended change. Before
2026-09-20 it overwrote the record with whatever was on disk, so it could not
detect a hand-edited `dist/`.

Since 2026-10-05 the API page's Python example reads the CSV straight from its
`/data/` URL with `pd.read_csv`: a Cloudflare configuration rule (the owner's
dashboard) turns the browser check off for `/data/*`, `/llms.txt`, `/llms-full.txt`
and `*/index.md`, and urllib was tested against them that day. The check requires
that call in both languages and refuses the old `requests` + `io.StringIO`
workaround and the sentence saying urllib is refused. It cannot see the dashboard:
if the rule is removed, the example stops running and no check fails.

Since 2026-10-06 the home masthead counts what the protocol pages carry. The lede
names the core matrix's protocols, datasets and methods (from `experiments.json`) and
the v9 matrix encoders (from the v9 export), dated by the v9 release, and never adds the
two into one total; the stat rail keeps the core matrix's four counts in order (the
share card prints the same four), and a line under it counts the v9 matrix encoders and
links the protocols hub. Pinned in both languages. Mutation-tested on a copy of `dist/`:
each of 8 injected violations (a count or the date in either lede, a summed total, the
rail's order, the encoder line's count, link or presence) was caught by the assertion
written for it. The same day's copy edit cut maxims, repeated caveats and the site
describing its own layout across the home page, the hubs, the protocol, dataset and
method pages and the ten topics; no cut sentence was pinned, and every pinned figure,
limitation, licence, hold and count still holds.

Since 2026-10-06 the home page's "How these results were produced" section prints the released
evidence policy (mvp.json `evidencePolicy`) as released on `/`, and on `/zh/` a Chinese translation
followed by the released English verbatim (`.note-original`, `lang="en"`); the check pins both.

Since 2026-10-07, the route-2 boundary (`shared-representation-update.json`, owner approved:
the decisions of 2026-10-06 that fixed the run and of 2026-10-07 that approved the BOAS rights
review as publishable with stated gaps and ran E2 sleep): one representation answering several
questions, fixed heads on a shared encoder against a question-conditioned head and separate
models, on OpenBMI motor imagery and BOAS sleep with EESM19 as a crude replication. The file is
registered (release log, feed, API page, home Dataset markup, data use) before any page prints
it; the page comes in a later commit. Read from `dist/`: the served JSON is byte-identical to
the source; one result, no status-only source and no hold; OpenBMI, BOAS and EESM19 in that
order, EESM19 crude and one seed; 21 primary entries; every difference flag, margin flag and
wording follows its interval and the 2-pp margin fixed at the freeze (the upper bound for the
conditioned-minus-fixed contrasts, the lower bound for P2, S10 and S12, log 0.8 for P3 and S4,
"not applicable" for the descriptive S11); every contrast is the difference of its two arms'
means; R is the ratio of remaining errors and its gate follows the read-out's AUROC interval;
per-seed points exist exactly for three-seed entries; every level gate follows its arm's
interval (chance + 5 pp to 95%); each route sentence counts exactly the questions that pass
their gate, is supported only if every counted question meets the margin and the ledger makes
the fixed heads cheaper, and a floor-gated entry states no sentence; every secondary entry
carries its gate and who attached it, and S2 at Level 1 is labelled as the independent audit's;
E2 sleep carries its disclosure (run after every other result, design fixed at the freeze), one
seed, its own E2 gates and no resume checkpoint left. BOAS: the three gaps, the attribution and
"pseudonymised in the public release" are in the file's conditions and its rights record alike;
the approval is the owner's of 2026-10-07; every count of people behind a BOAS figure is at least
20 (the smallest, 71); no key in the file names a per-person percentile or a per-fold value. The
release log names the batch and its manifest in both languages, and its English entry states the
gaps, "pseudonymised" and the E2 disclosure; data use prints the three rights records, each
ending with what route 2 publishes (OpenBMI's and EESM19's reused, BOAS new), and a BOAS
paragraph with the three gaps, the credit, the participants' wording and that neither the
headband nor its automatic scoring is used. Mutation-tested on a copy of `dist/` (`SITE_DIST`;
where an assertion reads the source export, the source too, restored afterwards, and the served
file's hash and size re-stated on the release pages and the feed so only the edit differs): each
of 44 injected violations was caught by the assertion written for it.
`check_site_artifact.py` re-derives the JSON from the pinned inputs and holds it to its export
audit (`shared-representation-export-audit.json`); the export re-resolves every traced block of
the release candidate against the file it names (363, the stage-0 report's 5 bound through the
consolidated aggregate), opens the three independent audits and checks their verdicts, and
refuses a flag, gate, route sentence or figure the numbers or the pinned handoff do not give
(`pipeline/publication/test_shared_representation_update.py` forges each link).

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
