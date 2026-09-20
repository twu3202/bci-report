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

from export_snapshot import validate_public

PROJECT = Path(__file__).resolve().parents[2]
PUBLISHED = PROJECT/'site/public/data'

# The eight protocol tables share one header, so they merge into a single table
# the dataset viewer can render. `protocol_id` keeps them separable.
MERGED = 'results.csv'


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


def card(snapshot, n_rows):
    tracks, models = len(snapshot['tracks']), len(snapshot['models'])
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
  - config_name: default
    data_files: {MERGED}
---

# BCI Report — aggregate EEG decoding results

Cohort-level results for {tracks} public EEG decoding protocols, each reported
with the protocol that produced it: cohort size, electrode count, evaluation
mode, chance level, training budget and known limitations. Release
`{snapshot['releaseId']}`, reviewed {snapshot['generatedAt'][:10]}.

Rendered, with the charts and the method notes: **<https://bci.report>**

## What this contains

`{MERGED}` — {n_rows} rows, one per (protocol, model) pair, {tracks} protocols,
{models} methods. `protocols/` carries the full descriptor for each protocol
(preprocessing, split, budget, audit hashes). `snapshot.json` is the complete
machine-readable release the website itself reads.

Every row carries its own `license`, `license_url` and `attribution`, so a row
lifted out of this table keeps its credit with it.

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

    (output/'snapshot.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False)+'\n')
    (output/'README.md').write_text(card(snapshot, len(rows)))

    return {'rows': len(rows), 'protocols': len(snapshot['tracks']),
            'models': len(snapshot['models']),
            'files': sorted(str(p.relative_to(output)) for p in output.rglob('*') if p.is_file())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
