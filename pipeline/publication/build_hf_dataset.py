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
import io
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
import export_later_sessions_update as later_export
import export_questions_in_language_update as questions_export
import export_new_ssvep_frequencies_update as ssvep_export
import export_data_quality_update as quality_export
import export_clinical_iesseeg_update as iesseeg_export
import export_neurolm_eegmat_update as neurolm_export
import export_beyond_scalp_update as beyond_export
import export_pilot_studies_update as pilot_export
import export_eegpt_core_update as eegpt_export
import export_ssvep_followups_update as followups_export
import export_neurorvq_update as neurorvq_export
import export_eegmat_ten_second_update as ten_second_export
import export_dataset_checks_update as checks_export
from ssvep_followups import blocks_cca

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


def later_payload():
    """The later-sessions export (WBCIC-SHU, longitudinal RSVP, Forenzo), refused unless it matches its own review audit."""
    raw = (PUBLISHED/'later-sessions-update.json').read_bytes()
    audit = json.loads(later_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Later-sessions export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Later-sessions payload is not the reviewed one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


def questions_payload():
    """Route 3 (questions in language) and its wording lists, refused unless both match their own review audit."""
    raw = (PUBLISHED/'questions-in-language-update.json').read_bytes()
    wordings = (PUBLISHED/'questions-in-language-wordings.json').read_bytes()
    audit = json.loads(questions_export.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', 'Questions-in-language export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], 'Questions-in-language payload is not the reviewed one'
    assert hashlib.sha256(wordings).hexdigest() == audit['wordings_sha256'], 'Questions-in-language wordings are not the reviewed ones'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, wordings, payload


def reviewed_payload(name, module, label):
    """A served file refused unless its bytes and its manifest are the ones its own export audit passed."""
    raw = (PUBLISHED/name).read_bytes()
    audit = json.loads(module.EXPORT_AUDIT.read_text())
    assert audit['status'] == 'pass', f'{label} export review did not pass'
    assert hashlib.sha256(raw).hexdigest() == audit['export_sha256'], f'{label} payload is not the reviewed one'
    assert hashlib.sha256(module.MANIFEST.read_bytes()).hexdigest() == audit['manifest_sha256'], f'{label} manifest is not the audited one'
    payload = json.loads(raw)
    validate_public(payload)
    return raw, payload


# The 2026-10-20 release: four result exports, each refused unless it is the one its own audit passed.
RELEASE_20261020 = (('new-ssvep-frequencies-update.json', ssvep_export, 'SSVEP follow-ups'),
                    ('data-quality-update.json', quality_export, 'Data quality'),
                    ('clinical-iesseeg-update.json', iesseeg_export, 'Clinical IESSEEG'),
                    ('neurolm-eegmat-update.json', neurolm_export, 'NeuroLM EEGMAT'))


# The 2026-10-28 release: four result exports, each refused unless it is the one its own audit passed. The fifth release
# of that day, the open register's second dated version, ships as its CSV below. None of them adds rows to the merged
# CSVs: each ships as its own file, like the 2026-10-20 ones.
RELEASE_20261028 = (('ssvep-followups-update.json', followups_export, 'SSVEP follow-ups'),
                    ('neurorvq-update.json', neurorvq_export, 'NeuroRVQ'),
                    ('eegmat-ten-second-update.json', ten_second_export, 'Ten-second EEGMAT'),
                    ('dataset-checks-update.json', checks_export, 'Dataset checks'))

# The open register's dated versions, each held to its own release's audit and manifest. Named here rather than read
# from export_open_register, whose constants move to the newest date: the 20261020 files stay served byte for byte
# beside the 20261028 ones (their bytes cite that release's hold ids), and both ship.
REGISTER_VERSIONS = ('20261020', '20261028')


def register_review(date):
    return PROJECT/f'research/publication_review_{date}/register'


def register_audit(date):
    """A register version's audit, refused unless it passed and its manifest is the audited one."""
    audit = json.loads((register_review(date)/'open-register-export-audit.json').read_text())
    assert audit['status'] == 'pass' and audit['release_id'] == f'open-register-update-{date}', f'Register {date}: audit'
    manifest = (register_review(date)/'open-register-release-manifest.json').read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == audit['manifest_sha256'], f'Register {date}: manifest is not the audited one'
    return audit


def register_csv(date='20261020'):
    """The open register's dataset ladder as its audit bound it. Only the CSV ships here: it carries no comparison
    finding about another upload (owner decision D3 keeps those to bci.report and its JSON)."""
    raw = (PUBLISHED/f'open-register-{date}.csv').read_bytes()
    audit = register_audit(date)
    assert hashlib.sha256(raw).hexdigest() == audit['csv_sha256'], f'Register CSV {date} is not the reviewed one'
    later = [d for d in REGISTER_VERSIONS if d > date]
    for d in later[:1]:
        # The next version's audit names this one's served bytes as unchanged.
        prev = register_audit(d)['previous_version']
        assert prev['release_id'] == f'open-register-update-{date}' and prev['served_unchanged'] is True, f'Register {d}: previous'
        assert hashlib.sha256(raw).hexdigest() == prev['csv_sha256'], f'Register CSV {date} changed after release'
    return raw


def register_json(date):
    """The register's JSON, read here only for the card's counts; it stays on bci.report (owner decision D3)."""
    raw = (PUBLISHED/f'open-register-{date}.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == register_audit(date)['export_sha256'], f'Register JSON {date} is not the reviewed one'
    for d in [d for d in REGISTER_VERSIONS if d > date][:1]:
        assert hashlib.sha256(raw).hexdigest() == register_audit(d)['previous_version']['json_sha256'], f'Register JSON {date} changed'
    payload = json.loads(raw)
    validate_public(payload)
    return payload


def beyond_payload():
    """The results beyond scalp EEG (human fNIRS, macaque intracortical spiking, an fNIRS coverage check)."""
    return reviewed_payload('beyond-scalp-update.json', beyond_export, 'Beyond-scalp')


def pilot_payload():
    """The pilot studies (Orthosis in three configurations of one cohort, BINGO, the handwriting analysis, REFED)."""
    return reviewed_payload('pilot-studies-update.json', pilot_export, 'Pilot-studies')


def eegpt_payload():
    """EEGPT's eight core-matrix cells and its pretraining-attribution rows, a frozen row beside the core matrix."""
    return reviewed_payload('eegpt-core-update.json', eegpt_export, 'EEGPT core')


def credit(rights):
    """A served credit line as the card prints it: the people and the record, without the site's own closing line."""
    return rights['attribution'].split(' Derived analysis by BCI Report')[0]


def beyond_paragraph():
    """The card's beyond-scalp paragraph: cohorts, species and the gates read from the served file, with credit and licence."""
    p = beyond_payload()[1]
    r, d = p['results'], p['datasets']
    assert set(r) == {'bak-fnirs-loso', 'nlb-mc-rtt-velocity', 'ds007420-optical-coverage'}, sorted(r)
    assert {s['id'] for s in p['status_only']} == {'falcon-h2-preparation', 'rabut-fus-preparation'}
    bak, nlb, opt = r['bak-fnirs-loso'], r['nlb-mc-rtt-velocity'], r['ds007420-optical-coverage']
    assert nlb['cohort']['animals'] == 1 and nlb['comparison']['ridge_better']['mae_m_per_s'] is False
    assert opt['gates']['classifier'] == 'held'
    assert d['nlb-mc-rtt']['consent_and_ethics']['subjects'] == 'animal'
    licences = '; '.join(f"{d[k]['rights']['name'].split(' · ')[0]}: {d[k]['rights']['license']}" for k in d)
    credits = ' · '.join(credit(d[k]['rights']) for k in d)
    return f"""`beyond-scalp-update.json`: what can be measured and decoded **beyond scalp
EEG**? Each entry is its own species, signal and metric: none is compared with
scalp EEG, none joins the `results` table, and they share no ranking. Human fNIRS
(Bak et al., {bak['cohort']['people']} people): right-hand, left-hand and foot tapping classified by a
fixed shrinkage LDA in a person left out of training, against a training prior;
**executed movement, not motor imagery**, offline, and systemic or motion effects
are not excluded. One macaque's motor-cortex spiking (MC_RTT, prepared for the
Neural Latents Benchmark): finger velocity decoded by a ridge on held-out trials
of the same session, against the training mean, on five metrics, including the
one on which the ridge is worse. **With one animal every figure is that
animal's**, no interval is reported, and it is not an official Neural Latents
Benchmark score. A numerical coverage check of human fNIRS recordings (ds007420,
{opt['cohort']['people']} people): counts only, and **no classifier score**, because the task codes
have no verified lookup and the event durations disagree. FALCON H2 (human
intracortical handwriting) and Rabut et al. (human functional ultrasound) are
prepared, not scored. MC_RTT is animal data, collected under procedures approved
by institutional animal care and use committees; the human sources' ethics and
consent statements are in the file. Licences, from each repository's record:
{licences}. Credit: {credits}"""


def pilot_paragraph():
    """The card's pilot-studies paragraph. Cohorts, the EEGPT terms, BINGO's rights and the handwriting dataset's stated
    gap are read from the served file, and the BINGO and handwriting sentences follow their publication switches."""
    p = pilot_payload()[1]
    r, d = p['results'], p['datasets']
    o, fm, refed = r['orthosis-64ch-classical'], r['orthosis-eegpt-vs-58ch'], r['refed-stored-clip']
    m = fm['model']
    assert m['weights_licence'] is None and m['weights_distributed'] is False and m['code_licence'] == 'Apache-2.0'
    assert fm['paired']['interval_excludes_zero'] is False
    c = o['cohort']
    if d['bingo-imagined-speech']['publication'] == 'released':
        b = r['bingo-cross-language']
        assert b['delivered_signal']['verified_against_file'] is False and b['contrast']['interval_excludes_zero'] is False
        bingo = f"""BINGO Greek and English inner speech ({b['cohort']['source_fields']} subject fields as the source
defines them): a fixed spectral baseline near its 15-class prior in every
direction, within and across languages, **a negative result for this baseline
only**. The source states no licence; consent is as the project's public
deliverable D3.1 (version 3.0) reports it, for its NATO-alphabet recordings in
the same laboratory, and no ethics-approval reference is published. The project
documents artifact cleaning (ASR, FORCe) on the continuous recordings before trials were cut
(D3.1, version 2.0), not re-verified against the file. """
    else:
        bingo = 'A BINGO inner-speech pilot is held for its rights, with no figure. '
    if d['eeg-fnirs-handwriting']['publication'] == 'released':
        h, hce = r['handwriting-mask-aware'], d['eeg-fnirs-handwriting']['consent_and_ethics']
        assert h['arms']['mask_only']['balanced_accuracy']['interval_95'] is None
        assert h['contrasts']['relative_eeg_minus_time_only']['interval_excludes_zero'] is False
        assert all(h['contrasts'][k]['interval_excludes_zero'] is True for k in ('relative_eeg_minus_mask_only', 'relative_eeg_minus_mask_plus_time'))
        assert hce['gap'].startswith('No ethics-approval or informed-consent statement was found.') and hce['basis'].startswith('owner decision')
        handwriting = f"""A mask-aware EEG analysis of a handwriting competition
dataset ({h['cohort']['people']} people, four released coded labels): with channels that sit flat at
a digital rail masked, relative EEG is just above the training-majority control
and above the missingness-mask and mask-plus-time controls, and **not
separated from elapsed time and trial order**; a data-quality and methods case
study on a reused development cohort, **not handwriting recognition**. No
ethics-approval or informed-consent statement was found, on the dataset card or
in a participating team's challenge paper; the aggregates are published with
that gap stated, by the owner's decision. """
    else:
        handwriting = 'A mask-aware EEG analysis of a handwriting dataset is held for its rights review, with no figure. '
    licences = '; '.join(f"{v['rights']['name'].split(' (')[0]}: {v['rights']['license']}" for k, v in d.items()
                         if v['publication'] == 'released')
    credits = ' · '.join(credit(v['rights']) for v in d.values() if v['publication'] == 'released')
    return f"""`pilot-studies-update.json`: **small pilots, outside every leaderboard and
model ranking**. The Orthosis error-detection dataset ({c['people']} people, {c['runs']} runs,
{c['events']:,} recorded device events: one cohort, counted once) in three
configurations: a 64-channel classical EEG baseline, the same baseline on the 58
channels EEGPT supports, and frozen EEGPT with the same supervised probe against
those matched classical features, whose paired interval spans zero: **neither
arm is shown to be better, and the two are not shown to be equivalent**. The
labels are recorded injected device events, not subjective error recognition,
and movement, muscle or device artifacts may contribute; the EEGPT probe is trained on the other people's labels
(not zero-shot), and overlap with EEGPT's pretraining data is not excluded.
EEGPT's code licence, {m['code_licence']}, covers {m['code_licence_scope']}; its checkpoint licence is
unresolved, **no original or converted weights are distributed**, and its
core-matrix cells are in `eegpt-core-update.json`, below. {bingo}{handwriting}REFED
({refed['cohort']['nominal_folders']} nominal participant folders, {refed['cohort']['clips']} stored clips): a computational
diagnostic in which source-only controls have smaller errors than EEG, with no
interval and no physiological or population claim. Further arms are status
only, with no figure. Licences: {licences}. Credit: {credits}"""


def eegpt_paragraph():
    """The card's EEGPT paragraph: what the file holds, its reading rule, the footnotes that travel with the cells and the
    model's terms, each checked against the served file; no figure that the file's own tables do not carry."""
    p = eegpt_payload()[1]
    m, cells, ex = p['model'], {c['protocol']: c for c in p['cells']}, p['pretraining_exposure']
    assert m['weights_licence'] is None and m['weights_distributed'] is False and m['code_licence'] == 'Apache-2.0'
    assert 'source code only' in m['code_licence_scope'] and m['endorsement'] == 'none implied'
    assert p['pilot_comparison']['leaderboard'] is False and p['directory_status']['suggested_status'] == 'Evaluated'
    assert ex['counts'] == {'exposed': 0, 'not_exposed': 7, 'unknown': 0} and set(ex['context']) == {'beta-8ch', 'beta-4ch'}
    assert {f['id'] for f in p['footnotes']} == {'one-second-patch-grid', 'untrained-channel-embeddings', 'tsinghua-benchmark-context',
                                                 'shorter-than-pretraining', 'fixed-readout', 'source-rate', 'idle-run'}
    assert cells['idle']['interval'] is None and all(c['interval_95'] for k, c in cells.items() if k != 'idle')
    assert all(c['paired_participant_bootstrap_95'][0] > 0 for c in p['pretraining_attribution']['paired_contrasts'])
    scored = len(cells) - 1
    return f"""`eegpt-core-update.json`: **EEGPT beside the core matrix**, a frozen row like
the further foundation encoders', from the same runs as the published LaBraM
rows and, except on idle, the CBraMod rows, with only the encoder swapped,
published as computed, without a re-run. Its {len(cells)} core-matrix cells: balanced accuracy with a participant-bootstrap
interval, macro F1 and the chance level on {scored} protocols (each percent figure
also in the core rows' units), and on the idle protocol ({cells['idle']['people']} people) counts and
window metrics with no interval. Its pretraining-attribution rows on mi-rest and
EEGMAT, in the fields of `deployment-topics.json`: the pretrained encoder against
the mean of three random initialisations, under a fixed and a train-selected
readout, with paired intervals. **Kept apart from `results`, and not a
ranking**: EEGPT is above or below a published row only where their 95%
intervals do not overlap, and several of those gaps are narrow; the file gives
each in percentage points. Footnotes travel with the cells: one-second windows
ran as four 0.25-second patches with no padding; on BETA with eight channels two
channel embeddings were never trained in pretraining; every core window is
shorter than EEGPT's 4-second pretraining window; the readout is the site's fixed
probe, not the authors' learnable spatial filter and linear head. None of the
seven core datasets is in EEGPT's published pretraining list — not proof that a
recording was never seen — and BETA's relation to the Tsinghua benchmark that is
in it is stated beside the BETA cells. EEGPT's code licence, {m['code_licence']}, covers
{m['code_licence_scope']}; its checkpoint licence is unresolved, **no original or
converted weights are distributed**, and no author endorsement is implied. The
pilot comparison in `pilot-studies-update.json` stays outside every leaderboard."""


def catalogued_elsewhere(snapshot):
    """Catalogued methods with no core-matrix row that have rows in a later export: (name, file), in catalogue order."""
    in_core = {r['name'] for t in snapshot['tracks'] for r in t['rows']}
    fm = json.loads(foundation_payload()[0])['results']['foundation-models-v9']
    complete = {r['model'] for r in fm['frozen_probe'] if r['status'] == 'complete'}
    fm_names = {m['name'] for m in fm['models'] if m['id'] in complete}
    eegpt = eegpt_payload()[1]
    eegpt_names = {eegpt['model']['name']} if any(c['status'] == 'complete' for c in eegpt['cells']) else set()
    out = []
    for m in snapshot['models']:
        n = m['name']
        if n in in_core:
            continue
        if n in fm_names:
            out.append((n, 'foundation-models-update.json'))
        elif n in eegpt_names:
            out.append((n, 'eegpt-core-update.json'))
    return out


def pilot_small_cohort():
    """The handwriting analysis's five people, in the card's small-cohort paragraph, while its switch releases it."""
    d = pilot_payload()[1]['datasets']['eeg-fnirs-handwriting']
    if d['publication'] != 'released':
        return ''
    return """ The handwriting
analysis has five people: its intervals are percentiles of resampled
five-person means, not one person's score, and its mask-only control's interval
is not published, because its bounds would show individual people's scores."""


def later_paragraph():
    """The card's later-sessions paragraph: what the file holds, with the cohort sizes read from it."""
    r = later_payload()[1]['results']
    assert set(r) == {'wbcic-cross-session-cpu', 'wbcic-frozen-cbramod', 'rsvp-later-visits', 'forenzo-continuous-control'}, sorted(r)
    return """`later-sessions-update.json`: does a decoder trained on a person's earlier
session still work later, with no labels from the later session? Motor imagery
on WBCIC-SHU from session 1 to session 3 (a relative-spectral ridge baseline and
frozen CBraMod features with a ridge readout; the two-class and three-class
cohorts are kept apart); RSVP target detection at the publisher's nominal Day 7,
Day 80 and Day 200 visits (AUROC with average precision beside it, since targets
are about 2.5% of events); and continuous cursor tracking on Forenzo & He, kept
as a negative result: the fixed ridge had higher overall error than a constant
source-mean comparator on every admitted record, with means, medians and the
upper tail all published. Same-person session transfer, offline; not online
control and not a ranking."""


def questions_paragraph():
    """The card's route-3 paragraph; the BOAS gaps and credit are read from the served export."""
    raw, _, payload = questions_payload()
    c = payload['boas_conditions']
    return f"""`questions-in-language-update.json` and `questions-in-language-wordings.json`:
route 3 of the decision-research roadmap, **questions in language**. One small
head over frozen EEG features, asked each question by a question number, a label
template or a natural-language description, on SSVEP (BETA) and sleep (BOAS).
Seen questions in their training wording, rewordings and questions the EEG head
was never trained on are separate results, never pooled into one zero-shot
number. In short: words matched question numbers on seen sleep questions but
cost accuracy on SSVEP; most rewordings cost accuracy; questions the head was
never trained on were not answered usefully; negation, a boundary probe, was not
understood. 35 pre-declared comparisons, no multiplicity correction; the
pre-run permutation checks, including two that failed before the owner-approved
third passed, are disclosed in the file. The wordings file holds the full
wording lists, the held-out partition and the derangements (the site's own
text, CC BY 4.0). **BOAS is published with three stated gaps**:
{' '.join(c['gaps'])} Participants are {c['participants']}. BOAS: {c['attribution']}"""


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


# The Jev-style section: what "Jev-style" means, in the site's own sentence (site/src/data/decision-research.ts
# `jevStyle`, with TypeSafe's launch post linked), and the paper the plan started from, cited as the route-3 export cites
# it. Nothing about what it is not (owner, 2026-10-08). Links only; no figure, no date, no version label.
JEV_PAGE = 'https://bci.report/jev-style/'
TYPESAFE_JEV = 'https://typesafe.ai/blog/introducing-system-one-models-and-jev'
JEV_STYLE = ('“Jev-style” here means the interface of a decision model like [TypeSafe’s Jev]({url}), applied to EEG: '
             'encode the recording once, then answer several explicit, typed questions about it, each with a probability.')
JEV_ROUTES = [
    ('Reliable decisions', 'when a decoder should decline to decide', 'https://bci.report/topics/when-not-to-act/#reliable-decisions'),
    ('One model, several questions', 'one shared representation against separate models', 'https://bci.report/topics/shared-encoder/'),
    ('Questions in language', 'questions asked in words, including ones the EEG head was never trained on', 'https://bci.report/topics/questions-in-language/'),
]


def jev_section():
    """The card's "Jev-style evaluation" section: the site's definition, and the vision paper as the route-3 export cites it."""
    origin = json.loads((PUBLISHED/'questions-in-language-update.json').read_text())['results']['questions-in-language']['route']['origin']
    assert origin['cite'].startswith('Yu & Yao, 2026 · Visual Jev'), 'Visual Jev cited as Yu & Yao, 2026'
    routes = '\n'.join(f"- [{name}]({url}): {what}." for name, what, url in JEV_ROUTES)
    return f"""## Jev-style evaluation

{JEV_STYLE.format(url=TYPESAFE_JEV)} The research plan started from a vision paper
that applies the same idea to images: {origin['cite']}
([arXiv:{origin['arxiv']}]({origin['url']})).

BCI Report asks whether this holds up on public EEG data in three routes,
gathered on [Jev-style questions on EEG: the evidence]({JEV_PAGE}):

{routes}

Each route's page gives its figures with their intervals, its limits and the
release they come from; the third is mostly a negative result for questions the
EEG head was never trained on."""


def release_20261020_paragraph():
    rows = sum(1 for _ in csv.DictReader(io.StringIO(register_csv().decode('utf8'))))
    return f"""`new-ssvep-frequencies-update.json`: **six follow-up experiments on BETA and one on
Wearable-102** asking what lets a decoder answer an SSVEP frequency it never
trained on: reference-spectrum queries, matching heads, phase jitter and phase
ramps, CCA's mechanism, and a bounded learned correction on top of CCA.
`data-quality-update.json`: **Shin2022 checked end to end**, a participant-held-out
diagnostic with its coverage accounting; eldBETA and ZuCo 2.0 as status only.
`clinical-iesseeg-update.json`: **an infant case-control pilot (IESSEEG)** with age and
recording-setting controls and frozen NeuroLM probes; point estimates, no clinical use.
`neurolm-eegmat-update.json`: **NeuroLM's frozen tokenizer features on EEGMAT**, a
separate panel beside the pilot studies.
`open-register-20261020.csv`: **the open register's dataset ladder** as its first
release froze it, {rows} rows, each dataset with the furthest of five verification
steps it had reached and the gaps; kept byte for byte, with the current ladder in
`open-register-20261028.csv`, below."""


# ---------------------------------------------------------------------------- the 2026-10-28 release
# One card paragraph per batch of the day. Every figure, count, licence and credit is read from the served file and
# formatted here; the wording around them is fixed, and each claim it makes is asserted against the file first.
WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}


def word(n):
    return WORDS[n]


def pct(x):
    """A proportion as a percent with two decimals. A value that would print as 0.00 is refused, not misprinted."""
    assert x == 0 or abs(100 * x) >= 0.005, x
    return f'{100 * x:.2f}%'


def pp(x):
    """A difference of proportions in signed percentage points, two decimals; never a rounded ±0.00."""
    assert x == 0 or abs(100 * x) >= 0.005, x
    return f'{100 * x:+.2f}'


def lower_first(text):
    return text[0].lower() + text[1:]


def bracket(interval, signed=False):
    f = pp if signed else (lambda v: pct(v)[:-1])
    return f'[{f(interval[0])}, {f(interval[1])}]'


def release_20261028_payload(name):
    """One of the day's four result files, as its audit bound it, with the earlier files it rests on held unchanged."""
    module = {n: m for n, m, _ in RELEASE_20261028}[name]
    label = {n: l for n, _, l in RELEASE_20261028}[name]
    raw, payload = reviewed_payload(name, module, label)
    audit = json.loads(module.EXPORT_AUDIT.read_text())
    unchanged = dict(audit.get('released_file_unchanged', {}))
    if 'released_file_sha256' in audit:            # the SSVEP follow-ups: cards 1 to 7 stay in the released file
        unchanged[payload['placement']['reads_with']['file']] = audit['released_file_sha256']
    for served, digest in unchanged.items():
        assert hashlib.sha256((PUBLISHED/served).read_bytes()).hexdigest() == digest, f'{label}: {served} changed'
    assert payload['placement']['leaderboard'] is False, f'{label}: on a leaderboard'
    return raw, payload


def followups_paragraph():
    """Cards 8 to 14 of the SSVEP page: what each asks, the cohorts, one untrained baseline's figures, the interval rules,
    the CPU component record and the credits, read from the served file."""
    p = release_20261028_payload('ssvep-followups-update.json')[1]
    cards, s = p['placement']['cards'], p['studies']
    assert [c['card'] for c in cards] == list(range(8, 15)) and p['placement']['reads_with']['cards'] == list(range(1, 8))
    assert cards[0]['supersedes'] == {'release_id': p['placement']['reads_with']['release_id'],
                                      'file': p['placement']['reads_with']['file'], 'entry': 'status_only'}
    asks = dict(FOLLOWUP_CARDS)
    assert [c['anchor'] for c in cards] == list(asks), 'a card the card paragraph does not describe'
    beta = s['xspec']['design']['dataset']
    wearable = s['harmonic_pooling_wearable']['design']['dataset']
    assert all(beta['people'] == (st['design'].get('dataset') or st['design']['datasets']['BETA'])['people'] for st in s.values()
               if st is not s['harmonic_pooling_wearable']), 'one BETA cohort'
    on_wearable = [e for e in p['endpoints'] if e['id'] == 'wearable_12'][0]
    ps = s['practical_settings']
    fb, cell = ps['design']['fbcca'], ps['design']['cells']
    anchor = ps['cpu_components']['anchor_cell']
    c = next(x for x in cell if x['id'] == anchor)
    level = ps['levels'][f'{anchor}/{fb["code"]}/u8']
    cca = next(m['code'] for m in ps['design']['methods'] if m['code'].startswith('CCA-'))
    diff = ps['contrasts'][f'{anchor}/{fb["code"]} minus {anchor}/{cca}/u8']
    assert level['seeds'] == 'no training' and fb['trained_head'] is False and diff['flags']['interval_includes_zero'] is False
    assert diff['interval'][0] > 0 and p['rights']['credits']['fbcca']['used_for'] == fb['description']['en']
    other = fb['other_recipe_on_site']
    held = next(e for e in p['endpoints'] if e['id'] == 'u8')
    adj = {a['card']: a for a in p['interval_adjustment']['adjusted']}
    assert set(adj) == {12, 13} and p['interval_adjustment']['other_intervals_adjusted'] is False
    assert adj[12]['adjustment'] == 'Bonferroni'
    cpu = ps['cpu_components']['measurement']
    assert cpu['threads'] == 1 and cpu['buffers'] == 'warm' and cpu['summed'] is False and cpu['gpu'] is False
    r = p['rights']['datasets']
    assert all('commercial scientific research' in t for t in (r['beta']['publication_conditions'][0], r['wearable_102']['consent_scope']))
    assert r['beta']['license'] == r['wearable_102']['license']
    fbcca = p['rights']['credits']['fbcca']
    assert fbcca['code_distributed'] is False
    described = '; '.join(f"card {x['card']}, {asks[x['anchor']]}" for x in cards)
    return f"""`ssvep-followups-update.json`: **{word(len(cards))} more follow-ups on SSVEP frequencies a
decoder never trained on**, cards {cards[0]['card']} to {cards[-1]['card']} of the site's page, read with
`{p['placement']['reads_with']['file']}` (cards {p['placement']['reads_with']['cards'][0]} to {p['placement']['reads_with']['cards'][-1]}, kept byte for byte; card {cards[0]['card']}'s
results here replace the status entry it carries): {described}. All {word(len(cards))} use the
BETA cohort ({beta['people']} people, {beta['targets']} target frequencies); cards {', '.join(str(x) for x in on_wearable['cards'][:-1])} and {on_wearable['cards'][-1]}
also report Wearable-102 ({wearable['people']} people, {' and '.join(wearable['sensors'])} sensors). Untrained
{fb['description']['en']} ({fbcca['short']}), reached {pct(level['estimate'])} {bracket(level['interval'])} on the {held['task'].lower()}
task with {c['window_s']:g}-second windows and {word(c['electrodes'])} electrodes, {pp(diff['estimate'])} pp
{bracket(diff['interval'], True)} over CCA on the same windows; the page https://bci.report{other['page']}
reports a different filter-bank recipe ({word(other['sub_bands'])} {other['filter']} sub-bands). Seen and
held-out frequencies are separate tasks, reported side by side. Card {adj[12]['card']} uses
{adj[12]['adjustment']}-adjusted {100 * adj[12]['level']:.2f}% intervals over {word(adj[12]['comparisons'])} comparisons for
{adj[12]['applies_to']}, and card {adj[13]['card']} a {100 * adj[13]['level']:g}% interval for {adj[13]['applies_to']};
no other interval is adjusted. Card {ps['card']} also gives CPU component medians in
milliseconds, measured {cpu['buffers']} on one thread and never summed ({ps['cpu_components']['label']['en']}).
Every figure compares set-ups on fixed splits, outside every leaderboard. BETA and
Wearable-102 are both {r['beta']['license']}, with participant consent described for noncommercial
scientific research. Credit: {r['beta']['citation'].rstrip('.')}; {r['wearable_102']['dataset_citation'].rstrip('.')};
filter-bank CCA, {fbcca['reference']}"""


# What each of cards 8 to 14 asks, in the order of the served placement (asserted above).
FOLLOWUP_CARDS = (
    ('cross-spectral', 'a learned readout over cross-spectral matrices'),
    ('eigenvalue-pooling', 'coherence and eigenvalue heads'),
    ('harmonic-pooling', 'pooling rules over the harmonics, with the BETA heads run unchanged on Wearable-102'),
    ('practical-settings', 'filter-bank CCA with shorter windows and fewer electrodes'),
    ('harmonic-gap', "where the harmonic sum's gain over joint CCA comes from"),
    ('fixed-decay', 'fixed decaying weights on the harmonics and on filter-bank sub-bands'),
    ('rising-weights', 'rising harmonic weights'),
)


def neurorvq_paragraph():
    """NeuroRVQ's frozen backbone on three tasks: the file's scope, each task's primary difference with its reading, the
    exposure, the gates of the protocols not run, and the terms; no weights distributed."""
    p = release_20261028_payload('neurorvq-update.json')[1]
    m, pl, ex = p['model'], p['placement'], p['pretraining_exposure']
    assert pl['counted_in_pilots'] is False and pl['core_matrix_row'] is False and pl['pointers_carry_figures'] is False
    assert m['frozen'] is True and m['fine_tuning'] is False and m['weights_distributed'] is False and m['endorsement'] == 'none implied'
    assert p['rights']['code']['licence'] == p['rights']['weights']['licence'] == 'CC BY-NC 4.0'
    assert p['rights']['weights']['weights_distributed'] is False
    assert ex['status'] == 'unknown' and not any(d['named_in_list'] for d in ex['datasets']) and ex['per_checkpoint_list_published'] is False
    blocks = []
    for b in p['blocks']:
        d = b['paired_difference']
        assert d['interval_includes_zero'] == (d['interval_95'][0] <= 0 <= d['interval_95'][1])
        assert d['interval_95'][0] <= d['difference'] <= d['interval_95'][1]
        blocks.append(f"{b['title']} ({b['dataset']}, {b['cohort']['people']} people): {d['label']}, "
                      f"{pp(d['difference'])} pp {bracket(d['interval_95'], True)}; {d['reading']}.")
    not_run = [g['protocol'] for g in p['protocols_not_run']]
    credits = ' · '.join(credit(v) for v in p['rights']['datasets'].values())
    return f"""`neurorvq-update.json`: **{p['title']}**, a separate panel on the pilot studies
page, outside the pilot count and every leaderboard and model ranking. {p['scope']}
{' '.join(blocks)} Every score uses {m['variant']}; {lower_first(m['authors_wrapper']['text'])}
Pretraining exposure is {ex['status']} for all {word(len(ex['datasets']))} datasets: none is named in NeuroRVQ's published
pretraining list, and no per-checkpoint list is published. Not run: {', '.join(f'`{x}`' for x in not_run)}, each
with its gate in the file. {p['rights']['summary']} No endorsement by NeuroRVQ's authors is
implied. Credit: NeuroRVQ, arXiv:{m['arxiv_id']} ({m['repository']}) · {credits}"""


def ten_second_paragraph():
    """EEG-Captioner and AXON on ten-second EEGMAT windows: the scope and cohort, each encoder against Welch band power
    with the source-QC totals beside the scores, what is not computed, and the terms."""
    p = release_20261028_payload('eegmat-ten-second-update.json')[1]
    pl, qc, iv = p['placement'], p['source_annotation_qc'], p['interval']
    assert pl['counted_in_pilots'] is False and pl['core_matrix_row'] is False
    assert iv['both_span_zero'] is True and p['encoder_contrast']['published'] is False
    cap, ax = p['eeg_captioner'], p['axon']
    diffs = [e['paired_difference'] for e in (cap, ax)]
    assert all(d['interval_includes_zero'] and d['interval_95'][0] <= 0 <= d['interval_95'][1] for d in diffs)
    assert diffs[0]['reading'] == diffs[1]['reading']
    assert cap['caption_result'] is False and cap['language_model_loaded'] is False
    assert cap['identity']['weights_distributed'] is False and ax['identity']['weights_distributed'] is False
    assert cap['pretraining_exposure'] == ax['pretraining_exposure'] == 'unknown'
    welch = next(a for a in ax['arms'] if a['role'] == 'baseline')
    pretraining = next(x['text'] for x in ax['limitations'] if x['id'] == 'pretraining-not-isolated')
    order = next(x['text'] for x in p['limitations'] if x['id'] == 'recording-order')
    scores = ', and '.join(f"{d['label']}, {pp(d['difference'])} pp {bracket(d['interval_95'], True)}" for d in diffs)
    return f"""`eegmat-ten-second-update.json`: **two frozen encoders on ten-second arithmetic and
rest windows**, a separate panel on the pilot studies page, outside the pilot count
and every leaderboard and model ranking. {p['scope']} {scores}:
for each, {diffs[0]['reading']}. {qc['beside_every_score']} {qc['scope']}
{cap['scope']} For AXON the Welch figures are {welch['note']}. {pretraining}
{p['encoder_contrast']['text']} {p['separate_from_two_second_results']['text']} {order}
Pretraining exposure is {cap['pretraining_exposure']} for both encoders. {p['rights']['summary']} No endorsement by
either model's authors is implied. Credit: {credit(p['rights']['dataset'])}"""


def dataset_checks_paragraph():
    """Four public datasets read from their files: Kim beta-range's training-free CCA baseline, MIND's conditional
    stored-marker case with both licence statements, and Damm and NeBULA as one-person status cases with no score."""
    p = release_20261028_payload('dataset-checks-update.json')[1]
    kim, mind = p['kim2025-beta-range'], p['mind2026']
    assert [c['id'] for c in p['cases']] == ['kim2025-beta-range', 'mind2026', 'damm', 'nebula']
    assert p['placement']['core_matrix'] is False
    k, res = kim['cohort'], kim['result']
    assert kim['method']['training_free'] is True and kim['method']['tuning'] is False and res['equals_balanced_accuracy'] is True
    assert res['accuracy_interval_95'][0] > res['chance'] and k['complete_cohort'] is True
    hold = next(h for h in p['holds'] if h['case'] == 'kim2025-beta-range')
    caveat = lambda case, cid: next(c['text'] for c in case['caveats'] if c['id'] == cid)
    prim = mind['primary']
    assert [x['pair'] for x in prim['pairs']] == ['4/5', '6/7'] and mind['status'] == 'released_conditional'
    runs_each, rest = divmod(prim['runs'], prim['record_ids'])
    assert rest == 0 and runs_each == prim['folds_for_each_record_id'] and 'third is held out' in prim['design']
    assert set(mind['rights']['licenses_stated']) == {'CC BY 4.0', 'CC BY-NC 4.0'}
    one = p['one_person']
    assert one['cases'] == ['eldbeta', 'damm', 'nebula'] and all(p[x]['status'] == 'score_held' for x in ('damm', 'nebula'))
    assert all(p[x]['design']['participants_run'] == 1 for x in ('damm', 'nebula'))
    short = lambda x: p[x]['rights']['name'].split(':')[0].split(' (')[0]
    licences = '; '.join(f"{short(x)}: {p[x]['rights']['license']}" for x in ('kim2025-beta-range', 'damm', 'nebula'))
    # Damm's rights gap stays beside its licence: its README cites a LICENSE file the pinned tree does not hold.
    damm_terms = p['damm']['rights']['terms']
    assert damm_terms['license_file_present'] is False and damm_terms['data_licence']['value'] == p['damm']['rights']['license']
    credits = ' · '.join(credit(p[x]['rights']) for x in ('kim2025-beta-range', 'mind2026', 'damm', 'nebula'))
    return f"""`dataset-checks-update.json`: **{word(len(p['cases']))} public EEG datasets read from their
files**, on the data-quality page, outside every leaderboard and the core matrix.
Kim beta-range SSVEP ({k['participants']} participants, {k['targets']} targets from {kim['intake']['frequency_lowest_hz']:.1f} to
{kim['intake']['frequency_highest_hz']:.1f} Hz): training-free standard CCA on {kim['method']['window_seconds']:g}-second windows reached a mean
participant accuracy of {pct(res['mean_participant_accuracy'])} {bracket(res['accuracy_interval_95'])} against a chance level of
{100 * res['chance']:g}% ({res['chance_basis']}). {caveat(kim, 'interval')} {hold['reason']}
MIND, a conditional case: {lower_first(mind['task'])} {caveat(mind, 'record-ids')} CSP + LDA beside an
ordinal lookup and a majority control for each pair, on {prim['record_ids']} record IDs with
{word(runs_each)} runs each, two training and the third held out. {caveat(mind, 'stored-marker-windows')}
{caveat(mind, 'terms')} Damm finger motor imagery and NeBULA are status cases of one person each,
beside eldBETA in `data-quality-update.json`: {lower_first(one['sentence'])} Ethics and consent
statements, or their gaps, are in the file for each case. Licences: {licences}; MIND
as above. For Damm, {lower_first(damm_terms['license_file_note'])} Credit: {credits}"""


def register_20261028_paragraph():
    """The open register's second dated version: its CSV, what moved since the first, and the model rows on the site."""
    date, prev = REGISTER_VERSIONS[1], REGISTER_VERSIONS[0]
    rows = list(csv.DictReader(io.StringIO(register_csv(date).decode('utf8'))))
    now, before = register_json(date), register_json(prev)
    old = {e['id'] for e in before['entries']}
    fresh = [e for e in now['entries'] if e['id'] not in old]
    models = [e for e in fresh if e['kind'] == 'model']
    merged = old - {e['id'] for e in now['entries']}
    # The day's dataset checks, in their own order, each with exactly one site row of its own.
    cases = [c['id'] for c in release_20261028_payload('dataset-checks-update.json')[1]['cases']]
    sites = [next(e for e in fresh if e['id'].startswith(f'r-site-{c}')) for c in cases]
    assert len({e['id'] for e in sites}) == len(cases) == len([e for e in fresh if e['kind'] == 'site_dataset'])
    assert all(m.startswith('r-moabb-') for m in merged) and len(merged) == len(sites)
    assert len(rows) == now['counts']['rows']['dataset'] == before['counts']['rows']['dataset']
    site_steps = {e['level'] for e in sites}
    scored = [e for e in models if e['level'] == 4]
    listed = [e for e in models if e['level'] == 1]
    assert len(site_steps) == 1 and len(scored) + len(listed) == len(models)
    assert {e['name'] for e in scored} == {'NeuroRVQ', 'EEG-Captioner', 'AXON'}
    assert all(any(f['code'] == 'hold' for f in e['findings']) for e in listed), 'a step-1 row without its hold'
    names = ', '.join(e['name'].split(' · ')[0] for e in sites[:-1]) + ' and ' + sites[-1]['name'].split(' · ')[0]
    step = now['level_definitions']
    return f"""`open-register-{date}.csv`: **the open register's dataset ladder**, {len(rows)} rows:
every dataset bci.report lists, with the furthest of five verification steps it
has reached and the gaps. The {word(len(sites))} datasets checked in `dataset-checks-update.json` ({names})
have rows of their own at step {site_steps.pop()}, “{step['dataset']['4']['en']}”, each with its MOABB record group merged
into it. The model rows stay on the site: NeuroRVQ, EEG-Captioner and AXON at step
{scored[0]['level']}, “{step['model']['4']['en']}”, and {word(len(listed))} further models at step {listed[0]['level']}, “{step['model']['1']['en']}”,
with their holds. The full register, with its findings, is at
https://bci.report/datasets/register/ and https://bci.report/methods/register/."""


def release_20261028_section():
    """The day's five card paragraphs, in the order the release log lists them, each checked against the thread rule:
    the commenter is never named and the figure never appears (read through blocks_cca.REFUSED_TEXT)."""
    text = '\n\n'.join((followups_paragraph(), neurorvq_paragraph(), ten_second_paragraph(),
                        dataset_checks_paragraph(), register_20261028_paragraph()))
    hits = {m.group(0).lower() for m in blocks_cca.REFUSED_TEXT.finditer(re.sub(r'https?://\S+', ' ', text))}
    assert not hits, f'refused text in the card: {sorted(hits)}'
    return text


def card(snapshot, n_rows, topics, n_foundation=128):
    tracks = len(snapshot['tracks'])
    # Methods that actually produced a row, not the size of the model catalogue.
    # The card said 18 for a table containing 9, because `snapshot['models']`
    # also lists methods reviewed but not yet scored.
    models = len({r['name'] for t in snapshot['tracks'] for r in t['rows']})
    catalogued = len(snapshot['models'])
    # A catalogued method scored outside `results.csv` still has a row: REVE Base in the foundation-model export, EEGPT
    # in its own. The card said 9 of 18 after both had been scored, then told the reader a method with no row had not
    # been run, right after the EEGPT paragraph.
    scored_elsewhere = catalogued_elsewhere(snapshot)
    scored = models + len(scored_elsewhere)
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

{later_paragraph()}

{questions_paragraph()}

{beyond_paragraph()}

{pilot_paragraph()}

{eegpt_paragraph()}

{release_20261020_paragraph()}

{release_20261028_section()}

{scored} of {catalogued} catalogued methods have been scored ({models} in `results.csv`;
{' and '.join(f'{n} in `{f}`' for n, f in scored_elsewhere)}). A catalogued method
with no row in any file has not been run, which is not the same as having
failed.

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
  in `foundation-models-update.json`), nor for EEGPT (checked 12 October 2026;
  in `eegpt-core-update.json`). The released protocol files keep their
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

The same holds for the smallest cohorts in the later files. MC_RTT is one
macaque, so every figure about it is that animal's own. REFED's errors pool two
nominal participant folders, and no per-folder value is published, because one
folder's value and the mean would give away the other. The Orthosis pilot has
eight people, and no per-person value, minimum or range is published.{pilot_small_cohort()}

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
    raw_later, _ = later_payload()
    (output/'later-sessions-update.json').write_bytes(raw_later)
    raw_questions, raw_wordings, _ = questions_payload()
    (output/'questions-in-language-update.json').write_bytes(raw_questions)
    (output/'questions-in-language-wordings.json').write_bytes(raw_wordings)
    raw_beyond, _ = beyond_payload()
    (output/'beyond-scalp-update.json').write_bytes(raw_beyond)
    raw_pilot, _ = pilot_payload()
    (output/'pilot-studies-update.json').write_bytes(raw_pilot)
    raw_eegpt, _ = eegpt_payload()
    (output/'eegpt-core-update.json').write_bytes(raw_eegpt)
    for name, module, label in RELEASE_20261020:
        (output/name).write_bytes(reviewed_payload(name, module, label)[0])
    for name, _, _ in RELEASE_20261028:
        (output/name).write_bytes(release_20261028_payload(name)[0])
    for date in REGISTER_VERSIONS:
        (output/f'open-register-{date}.csv').write_bytes(register_csv(date))
    (output/'deployment-topics.json').write_text(
        json.dumps(topics, indent=2, ensure_ascii=False)+'\n')
    (output/'snapshot.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False)+'\n')
    (output/'README.md').write_text(card(snapshot, len(rows), topics, len(foundation_rows)))
    # The card's logo. Not data, so it bypasses the data checks above; it is the
    # tiled raster from site/public/, which survives the Hub's dark theme.
    shutil.copyfile(PROJECT/'site/public/logo.png', output/'logo.png')
    # The thread rule over everything that ships, read through blocks_cca.REFUSED_TEXT (no literal of the name here):
    # the card and the 2026-10-28 files match none of it; earlier files match only ordinary words and figures that the
    # rule also catches ('pending', 'superseded', a 0.55 or a 55% in a released table).
    ordinary = {'pending', 'superseded', '0.55', '55%'}
    day = {name for name, _, _ in RELEASE_20261028} | {f'open-register-{REGISTER_VERSIONS[-1]}.csv', 'README.md'}
    for path in output.rglob('*'):
        if path.suffix not in {'.json', '.csv', '.md'}:
            continue
        text = re.sub(r'https?://[^\s"\'<>)]+', ' ', path.read_text())
        hits = {m.group(0).lower() for m in blocks_cca.REFUSED_TEXT.finditer(text)}
        assert hits <= (set() if path.name in day else ordinary), f'refused text in {path.name}: {sorted(hits)}'

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
