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
import re
import shutil
from pathlib import Path

import hashlib

from export_snapshot import validate_public
from export_deployment_topics import EXPORT_AUDIT
import export_evidence_update as evidence_export
import export_clinical_update as clinical_export
import export_context_update as context_export
import export_adaptation_update as adaptation_export
import export_extension_update as extension_export
import export_large_source_update as large_source_export
import export_reliable_decisions_update as reliable_export
import export_foundation_models_update as foundation_export
import export_shared_representation_update as shared_export

PROJECT = Path(__file__).resolve().parents[2]
PUBLISHED = PROJECT/'site/public/data'

# The eight protocol tables share one header, so they merge into a single table
# the dataset viewer can render. `protocol_id` keeps them separable.
MERGED = 'results.csv'
TOPICS = 'topics.csv'
# The 2026-10-04 foundation-model rows: the site's eight per-protocol CSVs share one
# header, so they stack into one table; `protocol_id` keeps them apart. Never
# merged into MERGED, whose rows are the released matrix.
FOUNDATION = 'foundation-models.csv'


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


def evidence_payload():
    """The 2026-09-22 evidence export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'evidence-update.json').read_bytes()
    audit = json.loads(evidence_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Evidence export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Evidence payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def clinical_payload():
    """The 2026-09-23 clinical export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'clinical-update.json').read_bytes()
    audit = json.loads(clinical_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Clinical export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Clinical payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def context_payload():
    """The 2026-09-27 context export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'context-update.json').read_bytes()
    audit = json.loads(context_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Context export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Context payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def adaptation_payload():
    """The 2026-10-01 adaptation export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'adaptation-update.json').read_bytes()
    audit = json.loads(adaptation_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Adaptation export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Adaptation payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def extension_payload():
    """The 2026-10-02 extension export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'extension-update.json').read_bytes()
    audit = json.loads(extension_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Extension export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Extension payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def large_source_payload():
    """The 2026-10-03 large-source export, refused unless it matches its own review audit."""
    raw = (PUBLISHED/'large-source-update.json').read_bytes()
    audit = json.loads(large_source_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Large-source export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Large-source payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def reliable_payload():
    """The 2026-10-04 route-1 export (reliable decisions), refused unless it matches its own review audit."""
    raw = (PUBLISHED/'reliable-decisions-update.json').read_bytes()
    audit = json.loads(reliable_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Reliable-decisions export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Reliable-decisions payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def foundation_payload():
    """The 2026-10-04 v9 export and its per-protocol CSVs, refused unless they match their own review audit."""
    raw = (PUBLISHED/'foundation-models-update.json').read_bytes()
    audit = json.loads(foundation_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Foundation-model export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Foundation-model payload is not the reviewed one'
    tables = {}
    for name, digest in audit['csv_sha256'].items():
        body = (PUBLISHED/name).read_bytes()
        assert hashlib.sha256(body).hexdigest() == digest, f'{name} is not the reviewed one'
        tables[name] = list(csv.reader(body.decode().splitlines()))
    payload = json.loads(raw)
    validate_public(payload)
    header = next(iter(tables.values()))[0]
    assert all(t[0] == header for t in tables.values()), 'the foundation-model CSVs have different schemas'
    rows = [r for name in sorted(tables) for r in tables[name][1:]]
    return raw, header, rows


def shared_payload():
    """The 2026-10-07 route-2 export (one representation, several questions), refused unless it matches its own review audit."""
    raw = (PUBLISHED/'shared-representation-update.json').read_bytes()
    audit = json.loads(shared_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Shared-representation export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Shared-representation payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def shared_paragraph():
    """The card's route-2 paragraph. Its figures, gaps and credit are read from the served export, and each claim
    it makes is asserted against that export, so the card cannot say what the file does not."""
    r = shared_payload()[1]['results']['one-representation']
    mi, boas, eesm = (r['datasets'][k] for k in ('openbmi', 'boas', 'eesm19'))
    entry = lambda d, i, q: next(e for e in d['entries'] if e['id'] == i and e['question'] == q)
    pp = lambda e: f"{e['estimate_pp']:+.2f} pp [{e['interval_95_pp'][0]:+.2f}, {e['interval_95_pp'][1]:+.2f}]"
    mi_a, sl_a = entry(mi, 'P1', 'MI-A'), entry(boas, 'P1', 'SL-A')
    assert not mi['route_sentence']['supported'] and not boas['route_sentence']['supported'], 'route sentence'
    assert mi_a['difference'] == sl_a['difference'] == 'difference: C1 higher', 'C1 higher'
    assert mi['route_sentence']['fixed_heads_for_less'] and boas['route_sentence']['fixed_heads_for_less'], 'for less'
    assert all(entry(mi, 'P5', q)['margin'] == 'equivalent within delta' for q in ('MI-A', 'MI-B')), 'P5'
    assert entry(boas, 'P5', 'SL-A')['margin'] == 'non-inferior' and entry(boas, 'P5', 'SL-A')['interval_95_pp'][1] < 2, 'P5 sleep: B-sh non-inferior'
    # Where C1's lift over B-lin comes from (S2, B-sh - B-lin, secondary): shown on sleep, inconclusive on motor imagery.
    s2 = lambda d, q: next(e for e in d['secondary'] if e['id'] == 'S2' and e['level'] == 'E1' and e['question'] == q)
    assert s2(boas, 'SL-A')['difference'] == 'difference: B-sh higher', 'S2 sleep'
    assert s2(mi, 'MI-A')['wording'] == 'inconclusive at this sample size', 'S2 motor imagery'
    assert boas['route_sentence']['excluded'] == {'SL-E': 'floor', 'SL-F': 'floor'}, 'floor'
    # The floor is EEGNet's (E1): on frozen CBraMod features and in E2 both questions passed the gate.
    assert [g['gate'] for g in boas['gates'] if g['level'] == 'E1' and g['question'] in ('SL-E', 'SL-F')] == ['floor', 'floor'], 'floor on EEGNet'
    assert all(g['gate'] == 'pass' for g in boas['gates'] if g['level'] != 'E1'), 'pass elsewhere'
    c = r['boas_conditions']
    return f"""`shared-representation-update.json` — reviewed 7 October 2026: route 2 of
the decision-research roadmap, **one representation, several questions**.
Independent models (A), one shared encoder with a fixed linear head per question
(B-lin), a shared hidden layer (B-sh) and that layer conditioned on the
question's identity by FiLM (C1), compared at matched data and compute: EEGNet
trained from scratch and frozen CBraMod features, three seeds each, and CBraMod
adapted by LoRA, one seed and secondary; motor imagery on OpenBMI
({mi['people']} people) and sleep on BOAS ({boas['people']} people), with EESM19
({eesm['people']} people, one seed) as a crude replication. "Fixed heads did as
well for less" is **supported on neither domain**: C1 scored {pp(mi_a)} above
B-lin on imagery against rest and {pp(sl_a)} on five-stage sleep scoring, while
B-lin was the cheaper set-up. C1 against B-sh (the same hidden layer without
conditioning) was equivalent within the 2 pp margin on both motor-imagery
questions and non-inferior on sleep, so the question's identity itself adds
nothing measurable. On sleep B-sh carries the lift over B-lin; on motor imagery
B-sh against B-lin was inconclusive. On sleep, next-epoch change and time of
night were at floor for the fixed heads on EEGNet: reported, not counted. Every contrast carries a
difference flag and a margin flag fixed before any result; with 21 primary
entries and no multiplicity correction, about one in twenty entries with no true
difference may show one by chance. E2 sleep ran after every other result was
known (owner decision; its design was fixed at the freeze). Questions are asked
by identifier, not in language, and these are **method comparisons, never
deployment error rates**. **BOAS is published with three stated gaps**:
{' '.join(c['gaps'])} Participants are {c['participants']}, and only cohort
aggregates of at least {c['minimum_cell_people']} people are published. BOAS:
{c['attribution']}"""


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


def citation_section():
    """The card's Citation section, read from CITATION.cff so the two cannot disagree.

    The BibTeX is the one the site's /api/ page prints: same key, title, author,
    year and release note. CITATION.cff names the newest release (the site's
    checks pin that), so the card cites the release its files belong to.
    """
    cff = (PROJECT/'CITATION.cff').read_text()

    def field(key):
        value = re.search(rf'^{key}: "?([^"\n]+)"?$', cff, re.MULTILINE)
        assert value, f'CITATION.cff has no {key}'
        return value.group(1)

    title, version, released, url = field('title'), field('version'), field('date-released'), field('url')
    doi = field('doi')
    bibtex = '\n'.join([
        '@misc{bcireport,',
        f'  title        = {{{title}}},',
        '  author       = {{BCI Report}},',
        f'  year         = {{{released[:4]}}},',
        f'  howpublished = {{\\url{{{url}}}}},',
        f'  doi          = {{{doi}}},',
        f'  note         = {{Release {version}}}',
        '}',
    ])
    return f"""## Citation

Cite BCI Report and the release you used — this card was built at release
`{version}` ({released}) — and the upstream dataset each figure was computed on:
the attribution table above, and every dataset page at
<{url}/datasets/>, gives its credit. The same citation is in
[CITATION.cff](https://github.com/twu3202/bci-report/blob/main/CITATION.cff),
which GitHub's "Cite this repository" reads, and every topic, dataset and method
page on the site ends with a "Cite this page" block naming the releases its
figures come from. Every release is archived on Zenodo; the concept DOI
[{doi}](https://doi.org/{doi}) resolves to the newest one.

```bibtex
{bibtex}
```"""


def protocol_table(snapshot):
    lines = ['| Protocol | Dataset | Cohort | Electrodes | Chance | Metric |', '|---|---|---|---|---|---|']
    for t in snapshot['tracks']:
        chance = 'none — see note' if t.get('chanceLevel') is None else f"{t['chanceLevel']}%"
        electrodes = sorted({r['channels'] for r in t['rows']})
        lines.append(f"| `{t['id']}` | {t['dataset']} | {t['subjects']} | "
                     f"{' / '.join(str(c) for c in electrodes)} | {chance} | {t['yLabel']} |")
    return '\n'.join(lines)


# The Jev-style section: the scope sentence and the independence line are the route-3 export's own, read from the
# served file, so the card says exactly what the site does. Links only; no figure, no date, no version label.
JEV_PAGE = 'https://bci.report/jev-style/'
JEV_ROUTES = [
    ('Reliable decisions', 'when a decoder should decline to decide', 'https://bci.report/topics/when-not-to-act/#reliable-decisions'),
    ('One model, several questions', 'one shared representation against separate models', 'https://bci.report/topics/shared-encoder/'),
    ('Questions in language', 'questions asked in words, including ones the EEG head was never trained on', 'https://bci.report/topics/questions-in-language/'),
]


def jev_section():
    """The card's "Jev-style evaluation" section, its scope sentence and independence line read from the route-3 export."""
    route = json.loads((PUBLISHED/'questions-in-language-update.json').read_text())['results']['questions-in-language']['route']
    scope, independence = route['jev_scope'], route['independence']
    assert scope.endswith('This is not an integration with Jev and not a Jev model that reads EEG.'), 'Jev scope sentence'
    assert 'independent and not affiliated with the Jev authors' in independence, 'independence line'
    assert route['origin']['cite'].startswith('Yu & Yao, 2026 · Visual Jev'), 'Visual Jev cited as Yu & Yao, 2026'
    routes = '\n'.join(f"- [{name}]({url}): {what}." for name, what, url in JEV_ROUTES)
    return f"""## Jev-style evaluation

{scope} {independence} The pattern comes from a vision paper:
{route['origin']['cite']} ([arXiv:{route['origin']['arxiv']}]({route['origin']['url']})).

BCI Report asks it on public EEG data in three routes, gathered on
[Jev-style questions on EEG: the evidence]({JEV_PAGE}):

{routes}

Each route's page gives its figures with their intervals, its limits and the
release they come from; the third is mostly a negative result for questions the
EEG head was never trained on."""


def card(snapshot, n_rows, topics, n_foundation=128):
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
  - jev-style
  - decision-models
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
  - config_name: foundation_models
    data_files: {FOUNDATION}
---

<p align="center"><img src="https://huggingface.co/datasets/Twu31/bci-report/resolve/main/logo.png" alt="BCI Report logo: a head seen from above with five electrode sites" width="96"></p>

# BCI Report

**Every EEG decoding score, reported with the protocol that produced it.**

[Website](https://bci.report) · [中文](https://bci.report/zh/) · [Code](https://github.com/twu3202/bci-report) ·
[Data use & privacy](https://bci.report/data-use/) · [Every dataset](https://bci.report/datasets/) ·
[Every method](https://bci.report/methods/) · [Data API](https://bci.report/api/)

[BCI Report Explorer](https://huggingface.co/spaces/Twu31/bci-report-explorer): browse these results, or query
them through MCP tools, in a Space that reads one pinned release of this mirror and names it in every answer.

{n_rows + n_topic_rows} reviewed measurements from public EEG datasets, each
carrying the cohort, electrode count, evaluation mode, chance level and training
budget that produced it. Core release `{snapshot['releaseId']}`, reviewed
{snapshot['generatedAt'][:10]}; later batches below, each reviewed on its own.

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
| `foundation_models` | {n_foundation} | 16 further foundation-model checkpoints × {tracks} protocols, frozen probes | percent |

Alongside: `protocols/` (full descriptor per protocol — preprocessing, split,
budget, audit hashes), `snapshot.json` and `deployment-topics.json` (the reviewed
exports the website itself reads).

Every row in `{MERGED}` carries its own `license`, `license_url` and
`attribution`, so a row lifted out of that table keeps its credit with it;
`{TOPICS}` cites its sources in `deployment-topics.json` under
`dataset_citations`.

`evidence-update.json` — the 22 September 2026 batch, reviewed under its own
manifest: a paired in-ear versus scalp sleep comparison (EESM23, 10 people,
identical epochs), four posterior electrodes against all sixteen for eyes open
or closed (Alpha Waves, 19 of the source's 20 recordings), a physical-phantom
artifact test reporting correlation and
predictive R² (dimensionless; R² is negative where the decoder fails and is
published as measured), and the adaptation roadmap as it stood that day
(`planned`; the measured results are in `adaptation-update.json`, below).
Heterogeneous by design, so it ships as JSON rather than as a table.

`clinical-update.json` — the 23 September 2026 batch, reviewed under its own
manifest: a 149-person case/control comparison on a Parkinson's disease data set
(100 patients, 49 controls, one site) published beside an age-and-sex-only
confound comparator, plus three holds that produced no score. **Research
results, not diagnosis**: not diagnostic accuracy, not clinical validation, and
no interpretation of any individual. No participant rows, no clinical scores and
no per-group demographics are published.

`context-update.json` — the 27 September 2026 batch: a P300 calibration carried
from a PC screen to a VR headset and back (21 people, within-person, two fixed
baselines, two timing schemes), and walking-speed classification from
dry-electrode EEG printed beside a movement-nuisance comparator (58 people), and
a four-person pilot of SSVEP windows accepted when no command was intended —
window-level counts, always with coverage beside accuracy. Fixed CPU baselines;
**no foundation-model or fine-tuning result**. One one-person pilot is published
as status only.

`adaptation-update.json` — reviewed 1 October 2026: LaBraM adapted to new people
on EEGMAT mental arithmetic (36 people, five participant-disjoint folds) three
ways — training only a classification head, the last block as well, or rank-4
LoRA — with the same checkpoint, folds, starting heads, batch order and
five-epoch recipe, over three seeds. Cohort means, paired changes with people
helped and harmed, per-seed means, trainable parameters and training time. The
head-only arm is a short gradient-trained head, so the file points to the core
matrix's frozen LaBraM ridge readout on the same folds for scale. **One fixed
recipe, not a tuned ranking**; no memory figures. A next-day experiment on a
source under editorial hold is listed as status only, with no figure.

`extension-update.json` — reviewed 2 October 2026, two fixed classical
baselines. The asynchronous SSVEP non-control test extended to the twenty other
people of the same release, scored under two rejection rules fixed before
scoring: a threshold fitted on the four-person pilot and a personal threshold
fitted on 96 of each person's own windows. Detection balanced accuracy, coverage,
correct-and-accepted output and false acceptance per non-control state for both,
with people helped, harmed and tied. **A better detector here is not better
command accuracy**, and these are window rates, not false activations per hour.
And LTRSVP (PhysioNet, doi:10.13026/C2KX0P; Matran-Fernandez and Poli, PLoS ONE
2017, doi:10.1371/journal.pone.0178498; ODC-By 1.0): a P300 target decoder
trained on one recording at 5 or 10 Hz and tested on a different recording of
the same person at 10 Hz, nine people, with the full 3×3 rate matrix. Within a
rate, run b followed run a after a long break; across rates the original study
presented the rates from the lowest to the highest, not randomised, and how the
released files map onto that sequence is not documented, so a cross-rate cell
also differs in elapsed time, fatigue and practice. The paired interval crosses
zero, and rate and recording change together: **not a causal effect of image
rate**.

`large-source-update.json` — reviewed 3 October 2026, two new sources and two
separate questions, each with two fixed classical CPU baselines and no shared
ranking. Dreem Open Datasets (Guillot et al., IEEE TNSRE 2020,
doi:10.1109/TNSRE.2020.3011181; deposit doi:10.5281/zenodo.15900394, MIT as the
deposit declares it): five-stage sleep staging against the publisher's
consensus in 25 healthy sleepers (DOD-H) and 55 people with obstructive sleep
apnoea (DOD-O), **two separate experiments, never compared with each other**. A
training prior that always predicts N2 and a spectral ridge, with accuracy,
balanced accuracy, macro F1 and Cohen's kappa, the paired balanced-accuracy
gain, and the ridge's per-stage recall, precision and F1. **Read accuracy beside
balanced accuracy**: the ridge reaches about 72% accuracy but 49–57% balanced
accuracy and never predicts N1, so its N1 precision is null — not defined, not
zero. The prior's balanced accuracy sits slightly above one fifth: a floor, not
a chance level. Not clinical, not diagnosis; the recordings' physical units are
unresolved, so amplitude-sensitive models are held with no figure. And OpenBMI
(Lee et al., GigaScience 2019, doi:10.1093/gigascience/giz002; data
doi:10.5524/100542, CC0 1.0): a motor-imagery decoder trained on each person's
first session and tested on the final 60 trials of their second, after 0, 10,
20 or 40 labelled trials from it, 51 people. Every mean change carries how many
people declined; the relative-PSD gain at 40 trials has an interval that
includes zero and is **not established**. An expanded cohort under the same
method, not an independent replication.

`reliable-decisions-update.json` — reviewed 4 October 2026: route 1 of the
decision-research roadmap, **when a decoder should decline to decide**. No
classifier was retrained: the saved test scores of models already published
here — spectral ridge, EEGNet and two LaBraM arms on EEGMAT (36 people), standard
CCA, CBraMod and EEGNet on BETA (70 people) — rescored under a fixed threshold on
calibrated confidence, a coverage target, a certified selective risk (SGR) and a
learned reject option, with NLL, ECE and Brier score and a person-specific
recalibration whose label cost per new person is counted. Every full-coverage
accuracy equals the published one. A fixed threshold accepted 28.4% of BETA
trials for one method and 1.5% for another, so **compare methods at matched
coverage, not at a shared cut-off**; how many people had nothing accepted
travels with every coverage. The learned reject option erred less than the
calibrated confidence for no method. The certified risk accepted nothing on
EEGMAT — **no error rate, not a zero one** — and on BETA some certified folds
exceeded their own target: a nominal guarantee across people. Calibration data
are participant-disjoint inner cross-fit scores, and rejecting likely errors on
known classes is not detecting unfamiliar input. Every contrast
carries its paired person-bootstrap interval and a verdict; nothing is ranked
where intervals overlap. Every protocol is balanced or uniform by design, so
these are **method comparisons, never deployment error rates**. ds003810 is a
crude secondary protocol; the idle protocol (another unit) and a source under
editorial hold are left out.

`foundation-models-update.json` and `{FOUNDATION}` — reviewed 4 October 2026:
eleven further EEG foundation models, sixteen encoder checkpoints (REVE Base and
Large, LUNA Base and Large, BrainOmni Base, CodeBrain, EEGMamba, ST-EEGFormer
Base and Large, four eeg-fm-masking checkpoints, ERP-FM Base, SingLEM and ZUNA
1.1), run as frozen probes on the same eight protocols with the published LaBraM
and CBraMod recipe and only the encoder swapped; nine of them also adapted on
EEGMAT with the 1 October recipe (a head trained on the frozen encoder against
rank-4 LoRA, three seeds; the adaptation rows are in the JSON). `{FOUNDATION}`
stacks the site's eight per-protocol CSVs: its first columns are the `results`
config's, in percent, and the rest give each row's status, panel (matrix or
masking ablation), chance flag, pretraining exposure, licence and footnote.
**Kept apart from `results`, and not a ranking**: rows are grouped by family, and
one is above or below another only where their 95% intervals do not overlap.
Sleep staging is the only protocol where new cells lie entirely above every
published row; elsewhere no new cell lies above the published non-foundation
row with the highest point estimate, and on BETA no new row lies above standard
CCA, which needs no training. Two BrainOmni cells were not run (its tokenizer needs two-second
windows): empty, with the reason, **never zero**. Pretraining exposure is a
sourced statement: BETA is in ST-EEGFormer's published pretraining list and
TMNRED in SingLEM's;
ZUNA 1.1 lists no pretraining data, so its cells are unknown; every other cell,
LaBraM's and CBraMod's included, is **not in the authors' published pretraining
list as checked on 4 October 2026** — not proof that a recording was never
seen. Weights licences travel with every row (REVE Responsible Use License,
LUNA CC BY-ND 4.0, ERP-FM CC BY-NC-SA 4.0; ZUNA 1.1's model card: research use
only, not for diagnosis or clinical use). Timings came from a shared GPU and
are not published.

{shared_paragraph()}

{models} of {catalogued} catalogued methods have been scored. A method with no
row has not been run, which is not the same as having failed.

{jev_section()}

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
- **Pretraining overlap is checked against published lists, not proven
  absent.** For LaBraM and CBraMod, none of the seven datasets is in the
  authors' published pretraining list (checked 4 October 2026; every source is
  in `foundation-models-update.json`). The released protocol files keep their
  original sentence, that overlap is unknown unless documented; recording-level
  overlap was not audited, so a frozen encoder may still have seen related data.

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

### Corrections to released wording

Released files are fixed bytes, so wording errors are corrected here and on the
site rather than in place (full list: <https://bci.report/releases/#corrections>).

- `deployment-topics.json` calls the original ensemble-TRCA method a
  three-filter-bank experiment. The original paper and the reference code's
  tutorials use five sub-bands; three is only the default of the code's
  functions. No score changes.
- For ds003810, the OpenNeuro record asks users to cite Peterson, Galván,
  Hernández and Spies, *A feasibility study of a complete low-cost
  consumer-grade brain-computer interface system*, Heliyon 6(3):e03425 (2020),
  doi:10.1016/j.heliyon.2020.e03425 — in addition to the Data in Brief
  description linked in the rows.

{citation_section()}

## License

The `cc-by-4.0` tag covers **the aggregate result tables and protocol
descriptors in this repository** — measurements this project produced. It does
not and cannot relicense the underlying recordings, whose terms are listed per
row and per dataset above. The code that produced them, on
[GitHub](https://github.com/twu3202/bci-report), is under the MIT License.

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

    raw_evidence, _ = evidence_payload()
    (output/'evidence-update.json').write_bytes(raw_evidence)
    raw_clinical, _ = clinical_payload()
    (output/'clinical-update.json').write_bytes(raw_clinical)
    raw_context, _ = context_payload()
    (output/'context-update.json').write_bytes(raw_context)
    raw_adaptation, _ = adaptation_payload()
    (output/'adaptation-update.json').write_bytes(raw_adaptation)
    raw_extension, _ = extension_payload()
    (output/'extension-update.json').write_bytes(raw_extension)
    raw_large_source, _ = large_source_payload()
    (output/'large-source-update.json').write_bytes(raw_large_source)
    raw_reliable, _ = reliable_payload()
    (output/'reliable-decisions-update.json').write_bytes(raw_reliable)
    raw_foundation, foundation_header, foundation_rows = foundation_payload()
    (output/'foundation-models-update.json').write_bytes(raw_foundation)
    for row in foundation_rows:
        for cell in row:
            assert not any(token in cell for token in forbidden), f'leak in foundation-model row: {cell[:80]}'
    with (output/FOUNDATION).open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(foundation_header)
        writer.writerows(foundation_rows)
    raw_shared, _ = shared_payload()
    (output/'shared-representation-update.json').write_bytes(raw_shared)
    (output/'deployment-topics.json').write_text(
        json.dumps(topics, indent=2, ensure_ascii=False)+'\n')
    (output/'snapshot.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False)+'\n')
    (output/'README.md').write_text(card(snapshot, len(rows), topics, len(foundation_rows)))
    # The card's logo. Not data, so it bypasses the data checks above; it is the
    # tiled raster from site/public/, which survives the Hub's dark theme.
    shutil.copyfile(PROJECT/'site/public/logo.png', output/'logo.png')

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
