<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="site/public/logo-dark.svg">
  <img src="site/public/logo.svg" alt="BCI Report logo: a head seen from above with five electrode sites" width="96">
</picture>

# BCI Report

**Every EEG decoding score, reported with the protocol that produced it.**

[![Website](https://img.shields.io/badge/site-bci.report-b3450e)](https://bci.report)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-Twu31%2Fbci--report-yellow)](https://huggingface.co/datasets/Twu31/bci-report)
[![Results licence](https://img.shields.io/badge/results-CC%20BY%204.0-blue)](LICENSE-DATA)
[![Code licence](https://img.shields.io/badge/code-MIT-blue)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23123296.svg)](https://doi.org/10.5281/zenodo.23123296)

[Website](https://bci.report) · [中文](https://bci.report/zh/) · [Dataset](https://huggingface.co/datasets/Twu31/bci-report) · [Data use & privacy](https://bci.report/data-use/)

</div>

---

A benchmark is only readable with its conditions. BCI Report publishes EEG
decoding results together with the cohort, electrode count, evaluation mode,
chance level, training budget and known limitations that produced each number —
and refuses to collapse them into one ranking, because the protocols do not
share a scale.

39 model-by-protocol scores across 8 fixed protocols and 7 public datasets, and
82 measurements across four deployment questions. Later batches are reviewed and
released on their own: in-ear versus scalp sleep staging, four electrodes against
sixteen, and a physical-phantom artifact test (22 September); a 149-person
Parkinson's and control comparison printed beside an age-and-sex-only confound
comparator (23 September); screen-to-VR P300 transfer, treadmill walking speed
beside a movement-nuisance comparator, and an asynchronous SSVEP non-control
pilot (27 September); LaBraM adapted to new people three ways — head only,
last block, rank-4 LoRA — with one matched recipe and three seeds (1 October);
and that SSVEP non-control test extended to twenty further people under a
pilot-fixed and a personal rejection threshold, plus a P300 decoder trained at
one image rate and tested at another (2 October); and two simple sleep-staging
baselines on healthy and sleep-apnoea cohorts kept as separate experiments,
with accuracy beside balanced accuracy, plus a motor-imagery decoder carried to
each person's next session with 0 to 40 labelled trials from it (3 October);
and when a decoder should decline to decide — a fixed confidence threshold, a
coverage target, a certified selective risk and a learned reject option, with
probability quality and a per-person recalibration's label cost, on saved test
scores of published models, as method comparisons rather than deployment error
rates (4 October); and sixteen further foundation-model encoder checkpoints, from
eleven models, as frozen probes on the same eight protocols with only the encoder
swapped, nine of them also adapted on EEGMAT, each cell marked with whether its
dataset is in the model authors' published pretraining list (4 October); and
whether one shared encoder with a fixed head per question answers several
questions as well as a question-conditioned head or separate models, for less —
motor imagery and sleep, at matched data and compute, every contrast with a
margin fixed before any result, and a new sleep source published with three
stated gaps in its consent and ethics record (7 October).
They are kept apart rather than summed, because they measure different things. Research results, not
diagnosis. No raw EEG, no per-participant scores, no model weights.

## Get the data

```python
from datasets import load_dataset

load_dataset("Twu31/bci-report", "results")   # 39 protocol × model scores
load_dataset("Twu31/bci-report", "topics")    # 82 deployment-condition measurements
```

Or straight from the site, no account:

```bash
curl -O https://bci.report/data/experiments.json        # full release snapshot
curl -O https://bci.report/data/deployment-topics.json  # four deployment questions
curl -O https://bci.report/data/evidence-update.json    # the 22 September batch
curl -O https://bci.report/data/clinical-update.json    # the 23 September batch
curl -O https://bci.report/data/context-update.json     # the 27 September batch
curl -O https://bci.report/data/adaptation-update.json  # the 1 October batch
curl -O https://bci.report/data/extension-update.json   # the 2 October batch
curl -O https://bci.report/data/large-source-update.json  # the 3 October batch
curl -O https://bci.report/data/reliable-decisions-update.json  # the 4 October batch
curl -O https://bci.report/data/foundation-models-update.json   # the 4 October foundation models
curl -O https://bci.report/data/foundation-models-beta-8ch.csv  # their rows, one CSV per protocol
curl -O https://bci.report/data/shared-representation-update.json  # the 7 October batch
```

What each file holds, loading examples and how to cite a release:
[bci.report/api](https://bci.report/api/).

## What is measured

| Protocol | Dataset | Cohort | Chance |
|---|---|---:|---:|
| Motor imagery vs. rest | ds003810 | 10 | 50% |
| SSVEP, 4 and 8 electrodes | BETA | 70 | 2.5% |
| P300 target | ds006593 | 21 | 50% |
| Semantic target | TMNRED | 30 | 50% |
| Mental arithmetic | EEGMAT | 36 | 50% |
| Sleep staging | EESM19 | 20 | 20% |
| Idle false activation | ds005342 | 4 | — |

Nine questions sit alongside, each with its own protocol:
[dry vs. wet electrodes](https://bci.report/topics/dry-vs-wet/) ·
[screen to VR](https://bci.report/topics/screen-to-vr/) ·
[fewer electrodes](https://bci.report/topics/fewer-electrodes/) ·
[clinical groups](https://bci.report/topics/clinical-groups/) ·
[standing, walking, running](https://bci.report/topics/on-the-move/) ·
[what calibration buys](https://bci.report/topics/calibration-budget/) ·
[which part of a pretrained model to update](https://bci.report/topics/model-adaptation/) ·
[when not to act](https://bci.report/topics/when-not-to-act/) ·
[does pretraining help](https://bci.report/topics/does-pretraining-help/)

Every dataset and every method also has its own page, gathering each figure
measured on it wherever it appears on the site:
[datasets](https://bci.report/datasets/) (BETA, EESM19, the wearable dry/wet
SSVEP set, the Mobile BCI set, …) ·
[methods](https://bci.report/methods/) (EEGNet, LaBraM, CBraMod, CCA, FBCCA,
eTRCA, …). So does each core-matrix protocol:
[protocols](https://bci.report/protocols/) gives each one its cohort, split,
electrodes, window, training mode, chance level and every method's score.
Those pages add no number of their own; the site's checks re-read every figure
on them from the download it came from.

For assistants and agents: [llms.txt](https://bci.report/llms.txt) indexes every
page with its short answer, [llms-full.txt](https://bci.report/llms-full.txt)
holds every English page in one file, and every page has a Markdown copy at
`<page>/index.md`.

**Jev-style decision models for EEG** — a research plan, not a result: can one
EEG representation answer several explicit questions, and know when to abstain?
It sits on [when not to act](https://bci.report/topics/when-not-to-act/#decision-research),
next to the measured idle-protocol trade-off it would build on. Not an
integration with Jev, and no results yet.

Every reviewed release, each download with its SHA-256, and a dated register of
what was held back: [bci.report/releases](https://bci.report/releases/).

## Read this before ranking anything

- **Chance level differs per protocol.** 57% on 40-class SSVEP is far above
  chance; 57% on a binary task is barely above it. Sorting across protocols
  compares numbers that do not share a scale.
- **Intervals are descriptive.** Bootstrap spreads over the scoring set, not
  confidence intervals, and not a basis for significance claims.
- **Most comparisons use one seed.** Two protocols add a three-seed check.
- **Electrode subsets are not headsets.** A 4-channel subset of a lab recording
  does not validate a 4-channel device.
- **A small cohort is close to its parts.** The idle protocol has four people,
  and its published mean can be turned back into a count. The arithmetic is
  [written out on the site](https://bci.report/data-use/#small-cohorts) rather
  than left for a reader to discover.

## How it is built

Private sources → fixed local experiments → independent audits → source and
model release decisions → reviewed export → `site/dist/` → host.

Raw EEG, trial rows, participant identifiers, embeddings, trained heads and
pretrained weights never cross the export boundary. Every published number is
reproduced from pinned inputs and checked against a review audit before it can
ship; the Hugging Face mirror is built from the same bytes the site serves, so
there is no second export path.

```bash
cd site && npm run build && node scripts/check-workbench.mjs
.venv/bin/python -m unittest discover -s pipeline/publication -p 'test_*.py'
.venv/bin/python -m unittest discover -s pipeline/tests -p 'test_*.py'
.venv/bin/python pipeline/publication/check_site_artifact.py
```

Passing these is not proof of anonymity. They match known-bad shapes and cannot
reason about reconstruction from small denominators — which is why the idle
cohort's invertibility is disclosed rather than asserted away.

| Path | What it is |
|---|---|
| `site/` | The Astro site. Zero framework JS; the coverage matrix is server-rendered. |
| `pipeline/publication/` | The release boundary: reviewed export, artifact inspection, dataset mirror. |
| `pipeline/` | Literature catalogue, verified-result store, news ingestion with a manual gate. |
| `data/` | Hand-maintained catalogues of models, benchmarks and verified results. |
| `research/` | Rights and privacy review evidence, per dataset. |

## Corrections

Scientific corrections, benchmark-method questions, and rights, privacy or
attribution concerns are welcome — **including ones that would withdraw a
published result.** Affected results can be withheld while an issue is reviewed.

Open an issue, or write to <contact@bci.report> for scientific corrections and
<privacy@bci.report> for rights, privacy and withdrawal requests. Please do not
send raw EEG, participant names or health records.

## Credit and licence

Results were computed from public datasets released by other researchers. Credit
belongs to them; this project adds only the measurements. Every published row
carries its own source, licence and attribution.

| What | Licence |
|---|---|
| Aggregate results: the result tables and protocol descriptors in `site/public/data/`, served under `bci.report/data/` (see the [data API](https://bci.report/api/)) and mirrored on Hugging Face | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — see [LICENSE-DATA](LICENSE-DATA) |
| Code: the site, the publication pipeline and their scripts | [MIT](LICENSE) |
| The EEG recordings the results were computed from | Their authors' own terms. Not in this repository; each [dataset page](https://bci.report/datasets/) names the source and its licence |

CC BY 4.0 covers the measurements this project produced — it does not and
cannot relicense the underlying recordings, which keep their own terms.

To cite a release, use [CITATION.cff](CITATION.cff) (GitHub's "Cite this
repository"), and cite the upstream dataset each figure was computed on — every
[dataset page](https://bci.report/datasets/) gives its credit line. Every topic,
dataset and method page also ends with a "Cite this page" block naming the
releases its figures come from. New releases appear in the
[Atom feed](https://bci.report/releases.xml).

Every GitHub release is archived on Zenodo with its own version DOI; the
concept DOI [10.5281/zenodo.23123296](https://doi.org/10.5281/zenodo.23123296)
always resolves to the newest one, and is the one to cite. `.zenodo.json`
describes the repository for that archive; it is written by
`site/scripts/write-zenodo-metadata.mjs` from `CITATION.cff` and the built
dataset pages, and the site checks hold it to them.

> **Known limits.** Six of eight core protocols run a single seed, the smallest
> cohort is four people, and 9 of 18 catalogued methods have been scored. Each
> page states its own limits next to its numbers.
