"""Build the Hugging Face dataset payload from the already-published site data.

The point of this script is that it adds no new export path. It reads
`site/public/data/`, which is the exact payload `check_site_artifact.py` has
already inspected and the site already serves, and reshapes it for the Hugging
Face dataset viewer. Anything that reaches Hugging Face has therefore passed the
same gate as anything that reaches the website. Re-running the leak scan here is
deliberate duplication: this script can be run against a hand-edited `dist/`, and
a second check is cheaper than discovering a per-participant column on a public
mirror that other people have already cloned.

    python3 pipeline/publication/build_hf_dataset.py --output <dir>
"""
import argparse
import csv
import json
from pathlib import Path

import hashlib

from export_snapshot import validate_public
from export_deployment_topics import EXPORT_AUDIT

PROJECT = Path(__file__).resolve().parents[2]
PUBLISHED = PROJECT/'site/public/data'

# The eight protocol tables share one header, so they merge into a single table
# the dataset viewer can render. `protocol_id` keeps them separable.
MERGED = 'results.csv'
TOPICS = 'topics.csv'


def topic_payload():
    """The reviewed topic export, refused unless it is byte-for-byte the approved one.

    The topic rows reach Hugging Face through the same file the site downloads,
    checked against the same audit `check_site_artifact.py` uses. Mirroring an
    export that drifted from its review would publish numbers nobody approved.
    """
    raw = (PUBLISHED/'deployment-topics.json').read_bytes()
    audit = json.loads(EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Topic export review did not pass'
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == audit['export_sha256'], (
        f'Topic payload {digest[:12]} is not the reviewed {audit["export_sha256"][:12]}')
    payload = json.loads(raw)
    validate_public(payload)
    return payload


def flatten(rows, interval_key=None):
    """One CSV row per record, with a single list field split into low/high columns."""
    keys = list(rows[0].keys())
    header = []
    for k in keys:
        header.extend([k+'_low', k+'_high'] if k == interval_key else [k])
    out = []
    for record in rows:
        line = []
        for k in keys:
            value = record.get(k)
            if k == interval_key:
                low, high = (value or [None, None])[:2]
                line.extend([low, high])
            elif isinstance(value, (list, dict)):
                line.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            else:
                line.append(value)
        out.append(line)
    return header, out


def load_tables():
    rows, header = [], None
    for path in sorted(PUBLISHED.glob('*-results.csv')):
        table = list(csv.reader(path.read_text().splitlines()))
        if header is None:
            header = table[0]
        assert table[0] == header, f'{path.name} has a different schema; merge would misalign columns'
        rows.extend(table[1:])
    return header, rows


def attribution_table(snapshot):
    """Credit lines, generated from the data so they cannot drift from it.

    Only datasets that actually contributed a number are listed. The register
    also carries datasets reviewed and excluded, and crediting those here would
    imply they are part of this release.
    """
    used = {t['dataset'] for t in snapshot['tracks']}
    lines = ['| Dataset | License | Attribution |', '|---|---|---|']
    for entry in snapshot['datasets']:
        if entry['name'] not in used:
            continue
        license_cell = (f"[{entry['license']}]({entry['licenseUrl']})"
                        if entry.get('licenseUrl') else entry['license'])
        lines.append(f"| [{entry['name']}]({entry['source']}) | {license_cell} | {entry['attribution']} |")
    return '\n'.join(lines)


def protocol_table(snapshot):
    lines = ['| Protocol | Dataset | Cohort | Electrodes | Chance | Metric |', '|---|---|---|---|---|---|']
    for t in snapshot['tracks']:
        chance = 'none — see note' if t.get('chanceLevel') is None else f"{t['chanceLevel']}%"
        electrodes = sorted({r['channels'] for r in t['rows']})
        lines.append(f"| `{t['id']}` | {t['dataset']} | {t['subjects']} | "
                     f"{' / '.join(str(c) for c in electrodes)} | {chance} | {t['yLabel']} |")
    return '\n'.join(lines)


def card(snapshot, n_rows, topics):
    tracks = len(snapshot['tracks'])
    # Methods that actually produced a row, not the size of the model catalogue.
    # The card said 18 for a table containing 9, because `snapshot['models']`
    # also lists methods reviewed but not yet scored.
    models = len({r['name'] for t in snapshot['tracks'] for r in t['rows']})
    catalogued = len(snapshot['models'])
    n_topic_rows = len(topics['rows'])
    n_topics = len(topics['topics'])
    n_contrasts = len(topics['paired_contrasts'])
    n_seed_groups = len(topics['seed_sensitivity'])
    topic_slugs = ', '.join(f"`{t['id']}`" for t in topics['topics'])
    datasets = len({t['dataset'] for t in snapshot['tracks']})
    return f"""---
license: cc-by-4.0
language:
  - en
tags:
  - eeg
  - brain-computer-interface
  - benchmark
  - neurotechnology
  - electroencephalography
pretty_name: 'BCI Report: aggregate EEG decoding results'
size_categories:
  - n<1K
configs:
  - config_name: results
    data_files: {MERGED}
  - config_name: topics
    data_files: {TOPICS}
  - config_name: contrasts
    data_files: contrasts.csv
  - config_name: seed_sensitivity
    data_files: seed-sensitivity.csv
---

# BCI Report

**Every EEG decoding score, reported with the protocol that produced it.**

[Website](https://bci.report) · [中文](https://bci.report/zh/) · [Code](https://github.com/twu3202/bci-report) ·
[Data use & privacy](https://bci.report/data-use/)

{n_rows + n_topic_rows} reviewed measurements from public EEG datasets, each
carrying the cohort, electrode count, evaluation mode, chance level and training
budget that produced it. Release `{snapshot['releaseId']}`, reviewed
{snapshot['generatedAt'][:10]}.

```python
from datasets import load_dataset

load_dataset("Twu31/bci-report", "results")   # {n_rows} protocol × model scores
load_dataset("Twu31/bci-report", "topics")    # {n_topic_rows} deployment-condition measurements
```

## What is in here

**Two separate bodies of measurement.** Not one ranking, and rows from one do
not belong in a table with rows from the other.

| Config | Rows | What it covers | Unit |
|---|---:|---|---|
| `results` | {n_rows} | {models} methods × {tracks} fixed protocols, {datasets} public datasets | percent |
| `topics` | {n_topic_rows} | {n_topics} deployment questions: {topic_slugs} | **proportion [0,1]** |
| `contrasts` | {n_contrasts} | paired within-participant differences | percentage points |
| `seed_sensitivity` | {n_seed_groups} | repeated training runs of one model | percent |

Alongside: `protocols/` (full descriptor per protocol — preprocessing, split,
budget, audit hashes), `snapshot.json` and `deployment-topics.json` (the reviewed
exports the website itself reads).

Every row in `{MERGED}` carries its own `license`, `license_url` and
`attribution`, so a row lifted out of that table keeps its credit with it;
`{TOPICS}` cites its sources in `deployment-topics.json` under
`dataset_citations`.

{models} of {catalogued} catalogued methods have been scored. A method with no
row has not been run, which is not the same as having failed.

## What this does not contain

**No raw EEG, no per-participant scores, no participant identifiers, no
recordings, no embeddings, no model weights.** This is a results table, not a
data mirror. Reach the recordings through the `source` column and follow that
source's own terms — several of the underlying datasets are redistributable and
several are not, and this repository does not relicense any of them.

## Read this before ranking anything

- **Chance level differs per protocol.** 50% for the binary tasks, 2.5% for
  40-class BETA SSVEP, 20% for five-stage sleep. A 57% SSVEP result is far above
  chance; a 57% binary result is barely above it. Sorting the table by
  `primary_percent` across protocols compares numbers that do not share a scale.
- **Intervals are descriptive, not confidence intervals.** They are bootstrap
  spreads over the scoring set. They do not support significance claims.
- **Most comparisons use one seed.** Two protocols add a three-seed EEGNet
  sensitivity check; the main table keeps its original fixed seed.
- **Electrode subsets are not headsets.** Four- and eight-electrode subsets of
  laboratory recordings do not validate a physical four- or eight-channel device.
- **Pretraining overlap is unknown** where checkpoint-level records are
  unavailable, so a frozen foundation encoder may have seen related data.

And for `{TOPICS}` specifically:

- **The unit changes.** `value` is a proportion in [0,1] here, a percent in
  `{MERGED}`. `contrasts.csv` differences are percentage points. Concatenating
  the two tables without rescaling silently divides one of them by 100.
- **{n_topic_rows} measurements are not {n_topic_rows} studies.** They are
  protocol-specific rows across {n_topics} questions; a question's rows share a
  cohort and a protocol, so they are not independent evidence.
- **Seed spread is not a confidence interval.** `seed-sensitivity.csv` reports
  what repeated training runs of the same model on the same data did. It
  describes the optimizer, not the population, and it cannot be read as an error
  bar on a participant mean.
- **These four questions do not extend the {tracks}-protocol matrix.** Different
  protocols, different cohorts, separately reviewed. Keep them apart.

## A small cohort is close to its parts

The idle protocol has a cohort of four, and at that size a published mean can be
turned back into a count: 1.7% of 60 command trials is one detection, and since
two of the four participants selected an always-abstain threshold, that detection
belongs to one of the remaining two.

These counts are published anyway, because a false-activation rate of zero
produced by people who never activate is the more misleading number. What a
reader cannot recover is which person is which — participants are unidentified
here and in the public source recordings, and no demographic, session or ordering
information is published that would let anyone line them up.

Treat "aggregate" as a description of what is published, not as a claim that it
cannot be inverted.

## Protocols

{protocol_table(snapshot)}

## Source datasets and attribution

Results were computed from these public datasets. Credit belongs to their
original authors; this repository adds only the measurements.

{attribution_table(snapshot)}

## License

The `cc-by-4.0` tag covers **the aggregate result tables and protocol
descriptors in this repository** — measurements this project produced. It does
not and cannot relicense the underlying recordings, whose terms are listed per
row and per dataset above.

## Corrections

Scientific corrections, benchmark-method questions, and rights, privacy or
attribution concerns are welcome, including ones that would withdraw a published
result — affected results can be withheld while an issue is reviewed.
Open a discussion here, or write to <contact@bci.report> for scientific
corrections and <privacy@bci.report> for rights, privacy and withdrawal
requests. Please do not send raw EEG, participant names or health records.

Full source review, privacy reasoning and interpretation caveats:
<https://bci.report/data-use/>
"""


def build(output):
    snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
    validate_public(snapshot)

    header, rows = load_tables()
    forbidden = ('subjectResults', '/Users/', '/Volumes/', '/home/',
                 'train_subjects', 'test_subjects', 'y_true', 'y_pred')
    for row in rows:
        for cell in row:
            assert not any(token in cell for token in forbidden), f'leak in results row: {cell[:80]}'
    assert 'participants' in header, 'cohort size column missing; the caveat would have nothing to stand on'
    assert not any(c.lower() in {'subject', 'subject_id', 'participant_id'} for c in header), header

    output.mkdir(parents=True, exist_ok=True)
    (output/'protocols').mkdir(exist_ok=True)

    with (output/MERGED).open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)

    for path in sorted(PUBLISHED.glob('*-protocol.json')):
        descriptor = json.loads(path.read_text())
        validate_public(descriptor)
        (output/'protocols'/path.name.replace('-protocol', '')).write_text(
            json.dumps(descriptor, indent=2, ensure_ascii=False)+'\n')

    topics = topic_payload()
    for name, records, interval in ((TOPICS, topics['rows'], 'confidence_interval_95'),
                                    ('contrasts.csv', topics['paired_contrasts'],
                                     'paired_participant_bootstrap_95'),
                                    ('seed-sensitivity.csv', topics['seed_sensitivity'], None)):
        head, lines = flatten(records, interval)
        assert not any(c.lower() in {'subject', 'subject_id', 'participant_id'} for c in head), head
        with (output/name).open('w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(head)
            writer.writerows(lines)

    (output/'deployment-topics.json').write_text(
        json.dumps(topics, indent=2, ensure_ascii=False)+'\n')
    (output/'snapshot.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False)+'\n')
    (output/'README.md').write_text(card(snapshot, len(rows), topics))

    return {'rows': len(rows), 'protocols': len(snapshot['tracks']),
            'models': len(snapshot['models']),
            'topicRows': len(topics['rows']), 'topics': len(topics['topics']),
            'contrasts': len(topics['paired_contrasts']),
            'seedGroups': len(topics['seed_sensitivity']),
            'files': sorted(str(p.relative_to(output)) for p in output.rglob('*') if p.is_file())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
