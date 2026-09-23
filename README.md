<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="site/public/logo-dark.svg">
  <img src="site/public/logo.svg" alt="BCI Report logo: a head seen from above with five electrode sites" width="96">
</picture>

# BCI Report

**Every EEG decoding score, reported with the protocol that produced it.**

[![Website](https://img.shields.io/badge/site-bci.report-b3450e)](https://bci.report)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-Twu31%2Fbci--report-yellow)](https://huggingface.co/datasets/Twu31/bci-report)
[![License](https://img.shields.io/badge/results-CC%20BY%204.0-blue)](https://creativecommons.org/licenses/by/4.0/)

[Website](https://bci.report) · [中文](https://bci.report/zh/) · [Dataset](https://huggingface.co/datasets/Twu31/bci-report) · [Data use & privacy](https://bci.report/data-use/)

</div>

---

A benchmark is only readable with its conditions. BCI Report publishes EEG
decoding results together with the cohort, electrode count, evaluation mode,
chance level, training budget and known limitations that produced each number —
and refuses to collapse them into one ranking, because the protocols do not
share a scale.

39 model-by-protocol scores across 8 fixed protocols and 7 public datasets;
82 measurements across four deployment questions; and a 22 September evidence
update — a paired in-ear versus scalp sleep comparison, four posterior
electrodes against sixteen for eyes open or closed, a physical-phantom artifact
test, and the status of planned adaptation experiments, which have no results
yet; and a 23 September clinical update — a 149-person Parkinson's and control
comparison published beside an age-and-sex-only confound comparator, with three
holds that produced no score at all. They are kept apart rather than summed,
because they measure different things. Research results, not diagnosis. No raw
EEG, no per-participant scores, no model weights.

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
```

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

Six deployment questions sit alongside, each with its own protocol:
[dry vs. wet electrodes](https://bci.report/topics/dry-vs-wet/) ·
[fewer electrodes](https://bci.report/topics/fewer-electrodes/) ·
[clinical groups](https://bci.report/topics/clinical-groups/) ·
[standing, walking, running](https://bci.report/topics/on-the-move/) ·
[what calibration buys](https://bci.report/topics/calibration-budget/) ·
[does pretraining help](https://bci.report/topics/does-pretraining-help/)

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

The aggregate result tables and protocol descriptors are
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). That covers the
measurements this project produced — it does not and cannot relicense the
underlying recordings, which keep their own terms.

> **Status: research preview.** Six of eight protocols run a single seed, the
> smallest cohort is four people, and 9 of 18 catalogued methods have been
> scored. The label comes off when that changes, not before.
