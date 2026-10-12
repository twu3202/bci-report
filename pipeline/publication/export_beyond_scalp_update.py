"""Release the non-scalp batch, aggregate-only: what can be measured and decoded beyond scalp EEG?

From the batch's handoff (and its review), each source with its own protocol, reviews and independent audit, nothing
shared between them but the page:

- the Bak 2019 fNIRS dataset: a fixed shrinkage-LDA classifier of executed right-hand, left-hand and foot tapping,
  leaving one whole person out of 30, against a training-prior comparator (human, fNIRS);
- MC_RTT of the Neural Latents Benchmark: a fixed ridge decoder of finger velocity from intracortical spiking on the
  stored training and validation trials of one session, against a training-mean comparator (one macaque);
- ds007420: a label-independent numerical coverage check of every optical value of its 60 recordings, counts only;
  its classifier is a hold (human, fNIRS);
- FALCON H2 (human intracortical handwriting) and the human functional ultrasound runs of Rabut et al.: status only,
  prepared and not scored, with the preparation counts the handoff states.

Its own publication boundary, as with every batch. The website inputs are the independent result audits and the
readiness records; the protocols, reviews, implementations, notes, the handoff and its review are pinned by hash and
checked against those exact bytes, never copied: they carry private storage paths and server names. The rights evidence
(each source's repository record and the paper or record its consent, ethics or animal-care statement is read from) is
pinned the same way and its quotes are checked against it.

What this export refuses:
- per-person, per-recording, per-channel, per-trial, per-fold and per-row values, confusion matrices, coefficients,
  predictions, features, identifiers, recording dates, cue texts and measured compute, by key, by fragment and by value;
- a figure that is not the audit's, an interval that does not hold its mean, a count that does not add up, a reading the
  numbers no longer support (a classifier interval that reaches chance, a ridge that is no longer worse on absolute
  error), a version label or an update marker in the text, and a claim of online control, clinical use, motor imagery,
  an official benchmark score, localization or neural origin that is not negated.

    python3 pipeline/publication/export_beyond_scalp_update.py
"""
from __future__ import annotations

import html
import json
import math
import re
from datetime import datetime
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261012'
MANIFEST = REVIEW / 'beyond-scalp-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'beyond-scalp-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/beyond-scalp-update.json',
           PROJECT / 'site/public/data/beyond-scalp-update.json')
RELEASE_ID = 'beyond-scalp-update-20261012'
SCHEMA = 'bci-report-beyond-scalp-update-v1'
QUESTION = 'What can be measured and decoded beyond scalp EEG?'

BAK, NLB, OPT = 'bak-fnirs-loso', 'nlb-mc-rtt-velocity', 'ds007420-optical-coverage'
H2, FUS = 'falcon-h2-preparation', 'rabut-fus-preparation'
RESULTS, STATUS = (BAK, NLB, OPT), (H2, FUS)
DATASETS = {'bak-fnirs': BAK, 'nlb-mc-rtt': NLB, 'ds007420': OPT, 'falcon-h2': H2, 'rabut-fus': FUS}
DECISIONS = {BAK: ('aggregate_preview', 'hold'), NLB: ('aggregate_preview', 'hold'), OPT: ('aggregate_preview', 'hold'),
             H2: ('status_only',), FUS: ('status_only',)}

# Per-person distributions, a decoder's internals and what this batch leaves out on purpose: refused by exact key and
# by fragment.
REFUSED_KEYS = PER_PERSON_KEYS | {'minimum', 'maximum', 'p10', 'p90', 'q1', 'q3', 'range', 'per_class', 'resources',
                                  'coefficients', 'weights', 'checkpoint', 'cue', 'cues', 'dates'}
REFUSED_KEY_FRAGMENTS = ('prediction', 'probabilit', 'feature_row', 'private', 'participant_id', 'record_id',
                         'per_person', 'per_participant', 'per_record', 'per_recording', 'per_channel', 'per_trial',
                         'per_fold', 'per_row', 'minimum', 'maximum', 'quantile', 'percentile', 'confusion', 'pooled',
                         'basename', 'path', 'wall', 'seconds_total', 'runtime', 'gib', 'bytes', 'rss', 'elapsed',
                         'host', 'server', 'coefficient', 'residual', 'timestamp')
# Upstream file and participant names: raw-file extensions, BIDS subject labels, the trial participant's code, the
# macaque's name and the fUS participant's letter.
SOURCE_IDS = re.compile(r'\.(?:mat|zip|h5|hdf5|nwb|snirf|npz|npy|edf|bdf|tsv)\b|\bsub-\w+|\bT5\b|\bIndy\b|\bLoco\b'
                        r'|\bparticipant J\b', re.IGNORECASE)
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|Gal4|TRX50|BCI_Arena',
                            re.IGNORECASE)
# The date rule: no internal version label ("v9", "(v1)") and no update marker in the text. DOIs keep their ".v2"
# (preceded by a dot or a slash, so not matched).
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'\b(?:updated?|added|new)\b|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d|'
                           r'\bin this (?:update|release|version)\b', re.IGNORECASE)
# Claims these results do not support, allowed only in a sentence that negates them.
CLAIMS = re.compile(r'\bonline\b|real-time|closed-loop|\bclinical\b|zero-shot|motor imagery|\bcausal|\bcaused\b'
                    r'|official (?:NLB|Neural Latents Benchmark|FALCON|benchmark|challenge)|co-smoothing'
                    r'|locali[sz]ation|neural origin|brain-only|signal quality|cross-day|\bendorse', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|unsupported|unverified|unconfirmed|unestablished|"
                      r"none)\b|n't\b|\brules? out\b|\bruled out\b", re.IGNORECASE)
TOL = 1e-12


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def close(a, b, label, tol=TOL):
    require(number(a) and number(b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def when(stamp):
    return datetime.fromisoformat(stamp.replace(' UTC', '+00:00').replace('Z', '+00:00'))


def bounded(mean, interval, label, lo_bound=-math.inf, hi_bound=math.inf):
    """A published mean and its 95% interval: the interval holds the mean and stays in the metric's range."""
    require(isinstance(interval, list) and len(interval) == 2, f'{label}: no two-sided interval')
    lo, hi = interval
    require(all(number(v) for v in (mean, lo, hi)), f'{label}: a mean or bound is not a finite number')
    require(lo_bound <= lo and hi <= hi_bound, f'{label}: the interval leaves the metric range')
    require(lo <= mean <= hi, f'{label}: the interval does not contain its mean')
    return [lo, hi]


def pinned_bytes(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw, digest


def pinned_text(ref, label):
    return pinned_bytes(ref, label)[0].decode('utf-8')


def stated(text, phrase, label):
    """The release figure the page prints is the one the pinned handoff or note states."""
    require(phrase in text, f'{label}: the pinned text does not state {phrase!r}')


def plain(text, markup=False):
    """Running text: markup tags dropped (HTML and JATS only), entities decoded, soft hyphens removed, whitespace
    collapsed. Extracted PDF text keeps its angle brackets: a "<" in a formula is not a tag."""
    if markup:
        text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    return re.sub(r'\s+', ' ', text.replace('­', '')).strip()


def numerals(text):
    return {n.replace(',', '') for n in re.findall(r'\d[\d,]*(?:\.\d+)?', text)}


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield value


def written_from(result, sources, label, skip=('rights',)):
    """Every numeral in the prose this export writes is one a pinned source states."""
    allowed = set().union(*(numerals(s) for s in sources))
    for key, value in result.items():
        if key in skip:
            continue
        for trail, text in strings(value, f'{label}.{key}'):
            missing = numerals(text) - allowed
            require(not missing, f'{trail}: the numerals {sorted(missing)} are in no pinned source')


def pct(x, places):
    return f'{100 * x:.{places}f}%'


def signed(x, places=6):
    """The handoff's table spelling: a typographic minus for negative values."""
    s = f'{x:.{places}f}'
    return s.replace('-', '−')


# ---------------------------------------------------------------------------- rights
CC = {'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/',
      'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
      'CC BY-NC 4.0': 'https://creativecommons.org/licenses/by-nc/4.0/'}


def licence_of(kind, raw, label):
    """Licence, DOI, credited names and public access, read from the repository's own record."""
    rec = json.loads(raw)
    if kind == 'figshare':
        names = {'CC BY 4.0': 'CC BY 4.0', 'CC0': 'CC0-1.0'}
        require(rec['is_public'] is True and rec['is_embargoed'] is False and rec['status'] == 'public',
                f'{label}: the repository record is not public')
        return {'license': names.get(rec['license']['name']), 'url': rec['license']['url'], 'doi': rec['doi'],
                'credit': [a['full_name'] for a in rec['authors']]}
    if kind == 'dandi':
        names = {'spdx:CC-BY-4.0': 'CC BY 4.0', 'spdx:CC0-1.0': 'CC0-1.0'}
        require(len(rec['license']) == 1, f'{label}: the record names more than one licence')
        require([a['status'] for a in rec['access']] == ['dandi:OpenAccess'], f'{label}: the record is not open access')
        return {'license': names.get(rec['license'][0]), 'url': None, 'doi': rec['doi'], 'credit': [rec['citation']]}
    if kind == 'bids':
        names = {'CC0': 'CC0-1.0'}
        return {'license': names.get(rec['License']), 'url': None, 'doi': rec['DatasetDOI'].removeprefix('doi:'),
                'credit': list(rec['Authors']) + [rec['HowToAcknowledge']]}
    if kind == 'caltechdata':
        names = {'cc-by-nc-4.0': 'CC BY-NC 4.0', 'cc-by-4.0': 'CC BY 4.0'}
        rights = rec['metadata']['rights']
        require(len(rights) == 1, f'{label}: the record names more than one licence')
        acc = rec['access']
        require(acc['record'] == 'public' and acc['files'] == 'public' and acc['embargo']['active'] is False,
                f'{label}: the record or its files are not public')
        credit = []
        for c in rec['metadata']['creators']:
            p = c['person_or_org']
            if p.get('type') == 'personal':
                credit.append(f'{p["given_name"]} {p["family_name"]}')
        return {'license': names.get(rights[0]['id']), 'url': rights[0]['props']['url'],
                'doi': rec['pids']['doi']['identifier'], 'credit': credit}
    raise ValueError(f'{label}: no reader for a {kind} record')


def consent_text(ce, label):
    """The pinned record a consent, ethics or animal-care statement is read from, as running text."""
    rec = ce['record']
    raw = pinned_text(rec, f'{label} consent record')
    for needle in rec['identifies'] + ([ce['paperDoi']] if ce.get('paperDoi') else []):
        require(needle in raw, f'{label}: the pinned consent record is another document (no {needle!r})')
    if 'extractedFrom' in rec:
        pinned_bytes(rec['extractedFrom'], f'{label} consent record source')
    if rec['kind'] == 'dandi':
        d = json.loads(raw)
        raw = d['description'] + ' ' + ' '.join(e['identifier'] for e in d['ethicsApproval'])
    return plain(raw, markup=rec['kind'] in ('html', 'jats'))


def dataset_rights(record):
    """Licence from the pinned repository record; consent and ethics (or animal care) from the pinned paper or record."""
    label = record['id']
    require(approved({**record, 'decision': 'aggregate_preview'}), f'{label}: the rights record is incomplete')
    lr = record['licenseRecord']
    raw, _ = pinned_bytes(lr, f'{label} licence record')
    lic = licence_of(lr['kind'], raw, label)
    require(lic['license'] == record['license'], f'{label}: the repository names another licence')
    require(CC[record['license']] == record['licenseUrl'], f'{label}: the licence URL is not the licence\'s')
    if lic['url']:
        require(lic['url'].startswith(record['licenseUrl'].rstrip('/')), f'{label}: the repository names another licence URL')
    doi = record['source'].removeprefix('https://doi.org/')
    require(lic['doi'] == doi and doi in record['version'] and doi in record['attribution'],
            f'{label}: the repository DOI differs from the record')
    require(lr['retrievedFrom'] in record['reviewBasis'], f'{label}: the licence record is not a review basis')
    for name in lic['credit']:
        require(name in record['attribution'], f'{label}: the attribution omits {name}')
    for extra in ('sourceRecord', 'readmeRecord'):
        if extra in record:
            pinned_bytes(record[extra], f'{label} {extra}')
    require(record['species'] and record['modality'], f'{label}: no species or modality')

    ce = record['consentEthics']
    text = consent_text(ce, label)
    require(ce['status'] == 'stated' and ce['source'] in record['reviewBasis'] + [lr['retrievedFrom']],
            f'{label}: consent and ethics are not stated from a listed source')
    paper = ce.get('paperDoi') or ce.get('paperId')
    if paper:
        require(paper in record['attribution'], f'{label}: the attribution does not cite the paper read')
    quotes = {q['statement']: q['text'] for q in ce['quotes']}
    require(len(quotes) == len(ce['quotes']), f'{label}: two quotes for one statement')
    for kind, quote in quotes.items():
        require(plain(quote) in text, f'{label}: the {kind} statement has no quote in the record')
        require(len(quote.split()) < 15, f'{label}: the {kind} quote is not a short quote')
    read_from = f'{ce["source"]} ({ce["section"]}), read {ce["record"]["retrievedAt"]}'
    if ce.get('readNote'):
        read_from += f' from {ce["readNote"]}'
    if ce['subjects'] == 'human':
        require(set(quotes) == {'ethics', 'consent'} and ce['ethics'] and ce['consent'],
                f'{label}: a human source needs its ethics and its consent statement')
        if 'ethicsRecordText' in ce:   # the dataset's own record names the approval too
            require(ce['ethicsRecordText'] in json.loads(raw).get('EthicsApprovals', []),
                    f'{label}: the dataset record does not name that approval')
        statements = {
            'subjects': 'human',
            'ethics_approval': {'stated': True, 'statement': ce['ethics'], 'quote': quotes['ethics']},
            'informed_consent': {'stated': True, 'statement': ce['consent'], 'quote': quotes['consent']},
        }
    elif ce['subjects'] == 'animal':
        require(set(quotes) == {'animal_care', 'source'} and ce['animalCare'], f'{label}: an animal source needs its '
                'animal-care statement and where the animal was recorded')
        require(ce['consent'].startswith('Not applicable'), f'{label}: informed consent is not marked not applicable')
        statements = {
            'subjects': 'animal',
            'ethics_approval': {'stated': True, 'kind': 'institutional animal care and use committee',
                                'statement': ce['animalCare'], 'quote': quotes['animal_care']},
            'informed_consent': {'stated': False, 'applicable': False, 'statement': ce['consent']},
        }
    else:
        raise ValueError(f'{label}: subjects must be human or animal')
    return {
        'rights': {k: record[k] for k in ('name', 'task', 'source', 'version', 'license', 'licenseUrl', 'attribution',
                                          'privacyReview', 'reviewedAt', 'reviewBasis')},
        'species': record['species'], 'modality': record['modality'],
        'consent_and_ethics': {**statements, 'read_from': read_from},
    }


# ---------------------------------------------------------------------------- the batch
def batch(b):
    handoff = pinned_text(b['handoff'], 'handoff')
    review = pinned_text(b['handoffReview'], 'handoff review')
    validation, _ = pinned(b['handoffValidation'], 'handoff validation')
    stage, _ = pinned(b['analysisStage'], 'analysis stage')
    require(validation['handoff_sha256'] == b['handoff']['sha256'], 'the handoff validation names other handoff bytes')
    require(validation['raw_data_in_project'] is False, 'the handoff validation found raw data in the project')
    require('suitable for aggregate-only website preparation' in review
            and 'Parent closeout: the wording correction was applied' in review,
            'the handoff review does not approve aggregate-only preparation with its correction applied')
    require('these reproduced experiments' not in handoff and 'locally executed experiments' in handoff,
            'the handoff still carries the wording the review corrected')
    require(stage['website_edited'] is False and stage['running_job'] is None and stage['gpu_used'] is False,
            'the analysis stage is not settled')
    return handoff, review, stage


# ---------------------------------------------------------------------------- Bak 2019 fNIRS
BAK_CLASSES = (('right_hand', 'RIGHT', 'right-hand finger tapping'), ('left_hand', 'LEFT', 'left-hand finger tapping'),
               ('foot', 'FOOT', 'foot tapping'))
BAK_AUDIT_DECISION = 'eligible_for_aggregate_release_after_independent_audit'


def bak(src, handoff, stage):
    label = BAK
    protocol, proto_sha = pinned(src['protocol'], f'{label} protocol')
    review_note = pinned_text(src['protocolReview'], f'{label} protocol review')
    freeze, freeze_sha = pinned(src['freezeReview'], f'{label} freeze review')
    _, impl_sha = pinned_bytes(src['implementation'], f'{label} implementation')
    audit, _ = pinned(src['resultAudit'], f'{label} result audit')
    note = pinned_text(src['resultAuditNote'], f'{label} result audit note')

    # Chain: audit -> protocol, implementation, freeze; freeze -> protocol, implementation, label audit.
    require(audit['protocol_sha256'] == proto_sha and audit['code_sha256'] == impl_sha
            and audit['freeze_sha256'] == freeze_sha, f'{label}: the audit names another protocol, code or freeze')
    require(freeze['protocol_sha256'] == proto_sha and freeze['code_sha256'] == impl_sha
            and freeze['label_audit_sha256'] == audit['label_audit_sha256'] == protocol['label_audit_sha256'],
            f'{label}: the freeze review names another protocol, code or label audit')
    require(freeze['decision'] == 'approved_before_scoring' and not freeze['blocking_findings']
            and freeze['heldout_scores_read'] is False and freeze['scoring_performed'] is False,
            f'{label}: the protocol was not approved before scoring')
    require('approved_before_scoring' in review_note and proto_sha in review_note and impl_sha in review_note,
            f'{label}: the protocol review does not approve these bytes')
    require(audit['decision'] == BAK_AUDIT_DECISION and all(v is True for v in audit['checks'].values())
            and audit['refit_performed'] is False and audit['protocol_changed'] is False
            and audit['raw_neural_arrays_read'] is False, f'{label}: the independent audit did not pass')
    require(when(freeze['reviewed_at_utc']) < when(audit['audited_at_utc']), f'{label}: the audit predates the freeze')
    require('eligible for aggregate release after this independent audit' in note, f'{label}: the audit note differs')

    # Cohort and design, from the protocol, agreeing with the audit and the freeze.
    co, sp, feat = protocol['cohort'], protocol['split'], protocol['features']
    people, trials = audit['participants'], audit['trials']
    require(people == co['participants'] == freeze['checks']['audited_participants'] == 30
            and trials == co['total_trials'] == people * co['trials_per_person']
            and co['trials_per_person'] == 3 * co['trials_per_class_per_person']
            and freeze['checks']['class_counts_per_participant'] == [co['trials_per_class_per_person']] * 3,
            f'{label}: the cohort does not add up')
    require(sp['whole_person_groups'] is True and audit['folds'] == people and sp['test_people'] == 1
            and sp['train_people'] == people - 1 and sp['train_trials'] == trials - co['trials_per_person']
            and sp['test_trials'] == co['trials_per_person'] and sp['hyperparameter_search'] == 'none',
            f'{label}: not leave one whole person out')
    windows = feat['windows_seconds']
    channels = 40
    stated(handoff, f'The supplied {channels} columns are 20 oxy and 20 deoxy signals', f'{label} channels')
    require(audit['features'] == channels * len(windows), f'{label}: the feature count is not channels times windows')
    require(feat['channel_selection'] == 'none' and feat['baseline_seconds'] == [-1, 0], f'{label}: features differ')
    fs = protocol['representation']['fs_hz']
    close(fs, 40 / 3, f'{label} sampling rate', 1e-12)
    horizon = windows[-1][1]
    unc = protocol['scoring']['uncertainty']
    require(unc['draws'] == 2000 and unc['interval'] == 'percentile2.5,97.5', f'{label}: another bootstrap')
    chance = protocol['scoring']['chance']
    close(chance, 1 / 3, f'{label} chance')

    # The figures: the audit's, each re-derived where it can be.
    res = audit['results']
    lda, prior = res['lda'], res['source_prior']
    lda_ba = lda['participant_macro_balanced_accuracy']
    lda_iv = bounded(lda_ba, list(lda['descriptive_bootstrap_95_percent']), f'{label} interval', 0, 1)
    prior_ba = prior['participant_macro_balanced_accuracy']
    close(prior_ba, chance, f'{label} prior is chance')
    for arm, block in (('lda', lda), ('source_prior', prior)):
        cm = block['confusion_matrix']
        require(all(sum(row) == trials // 3 for row in cm), f'{label}: {arm} classes are not balanced')
        for i, r in enumerate(block['class_recall']):
            close(r, cm[i][i] / sum(cm[i]), f'{label} {arm} recall {i}')
    require(prior['class_recall'] == [1.0, 0.0, 0.0], f'{label}: the prior does not always predict the first class')
    # The reading: the classifier's interval lies wholly above chance.
    require(lda_iv[0] > chance, f'{label}: the interval no longer lies above chance')

    for phrase in (f'**{pct(lda_ba, 4)}**', f'**{pct(lda_iv[0], 4)}–{pct(lda_iv[1], 4)}**',
                   f'right **{pct(lda["class_recall"][0], 2)}**, left **{pct(lda["class_recall"][1], 2)}**, '
                   f'foot **{pct(lda["class_recall"][2], 2)}**', f'**{pct(prior_ba, 4)}**',
                   f'{people} people, {trials:,} executed-movement trials', f'{audit["features"]} features'):
        stated(handoff, phrase, f'{label} figure')
    stated(note, f'| Shrinkage LDA | {pct(lda_ba, 2)} | {pct(lda_iv[0], 2)[:-1]}–{pct(lda_iv[1], 2)} |', f'{label} note')
    s = stage['completed']['bak2019']
    require(s['status'] == 'audited_aggregate_release_eligible' and s['participants'] == people
            and s['trials'] == trials and s['participant_macro_balanced_accuracy'] == lda_ba and s['prior'] == prior_ba,
            f'{label}: the analysis stage records other figures')

    recall = lambda block: {k: block['class_recall'][i] for i, (k, _, _) in enumerate(BAK_CLASSES)}
    result = {
        'id': BAK, 'dataset': 'bak-fnirs',
        'title': 'Human fNIRS: executed finger and foot tapping, a held-out person',
        'question': 'Can a fixed hemodynamic classifier trained on other people tell which movement a held-out person '
                    'made?',
        'label': 'Locally executed experiment · offline · leave one whole person out',
        'kind': 'decoding result',
        'evidence': 'a locally executed experiment, not a score reported in a paper',
        'species': 'human', 'modality': 'fNIRS',
        'measured_quantity': 'the supplied oxy- and deoxyhemoglobin series, in mM·cm as delivered, not absolute '
                             'concentrations',
        'task': {'classes': [c for _, _, c in BAK_CLASSES],
                 'kind': 'executed movement, cued; not motor imagery'},
        'cohort': {'people': people, 'trials': trials, 'trials_each_person': co['trials_per_person'],
                   'trials_each_class_each_person': co['trials_per_class_per_person']},
        'design': {
            'split': 'leave one person out: each fold fits on the other people and predicts every trial of the held-out '
                     'person; every person is held out once',
            'folds': audit['folds'], 'training_people': sp['train_people'], 'training_trials': sp['train_trials'],
            'test_trials': sp['test_trials'],
        },
        'signal': {
            'channels': channels, 'channel_note': 'twenty oxy- and twenty deoxyhemoglobin series; the supplied files '
                                                  'carry no probe coordinates',
            'sampling_rate_hz': fs, 'baseline_window_s': feat['baseline_seconds'], 'feature_windows_s': windows,
            'observation_window_s': horizon, 'features': audit['features'],
            'processing': 'each window\'s channel mean minus the one-second pre-onset mean; no filtering applied beyond '
                          'the supplied series, whose upstream preprocessing may use future samples',
        },
        'models': {
            'shrinkage_lda': 'standardization and shrinkage LDA (lsqr solver, automatic shrinkage, empirical training '
                             'priors) fitted on the training people only; no channel, feature or hyperparameter search',
            'source_prior': 'the most frequent class among the training trials, ties broken by the fixed class order; '
                            'with balanced classes it predicts right-hand tapping every time',
        },
        'primary_metric': {
            'id': 'participant_macro_balanced_accuracy', 'name': 'Participant-macro balanced accuracy',
            'definition': 'each held-out person\'s balanced accuracy (the mean of the three class recalls), averaged over '
                          'the people with equal weight',
            'unit': 'proportion in [0,1]', 'chance_level': chance,
        },
        'arms': {
            'shrinkage_lda': {'label': 'Shrinkage LDA',
                              'balanced_accuracy': {'mean': lda_ba, 'interval_95': lda_iv,
                                                    'interval_excludes_chance': lda_iv[0] > chance},
                              'class_recall': recall(lda)},
            'source_prior': {'label': 'Training prior (comparator)', 'balanced_accuracy': {'mean': prior_ba},
                             'class_recall': recall(prior)},
        },
        'class_recall_note': 'the recall of each class over all held-out predictions, every person together (the same '
                             'number of trials in each class); a secondary point estimate without an interval',
        'uncertainty': {
            'kind': 'descriptive 95% percentile interval: the fixed participant scores resampled with replacement, '
                    '2,000 draws',
            'draws': unc['draws'], 'seed': unc['seed'],
            'scope': 'It describes variation between people given the fitted folds. The folds share training people, so '
                     'it is not a refit bootstrap and not an independent clinical confidence interval.',
            'comparator': 'The training prior has no interval: every person gets the same score.',
        },
        'reading': 'For a held-out person, the fixed classifier separated right-hand, left-hand and foot tapping well '
                   'above the training prior, and its descriptive interval lies wholly above chance. This is offline '
                   'classification of supplied hemodynamic series over a 15-second window after each task onset.',
        'limitations': [
            'Offline, from the supplied hemodynamic series with a 15-second observation window; the upstream '
            'preprocessing may use future samples. Neither online control nor device response time is shown.',
            'Executed movement, not motor imagery; no clinical or device-effectiveness claim.',
            'One supplied cohort of 30 people. Task-correlated systemic or motion effects are not excluded, so the '
            'result establishes neither a brain-only signal nor cortical localization; the supplied files carry no probe '
            'coordinates.',
            'The interval resamples fixed participant scores from overlapping leave-one-out training sets: not a refit '
            'bootstrap, not an independent clinical confidence interval.',
            'The protocol is this site\'s own; it does not reproduce the authors\' within-person scores.',
        ],
        'claims_not_supported': [
            'not motor imagery',
            'no online or real-time control claim',
            'no clinical or device-effectiveness claim',
            'no cortical localization or brain-versus-systemic-signal claim',
            'not a reproduction of the authors\' scores',
        ],
        'independent_audit': {
            'status': 'pass', 'people': people,
            'checked': 'every input file hash, the marker-to-label order, whole-person folds, training-only scaling, '
                       'the comparator\'s tie rule and prediction alignment; the confusion tables, class recalls, '
                       'primary mean and bootstrap recomputed without the frozen scoring code',
            'not_checked': 'the features were not regenerated from the raw channels and the classifier was not refit',
        },
    }
    secret = {*(c for row in lda['confusion_matrix'] for c in row), audit['runtime']['launcher_total_seconds']}
    secret |= {v for v in prior['descriptive_bootstrap_95_percent'] if v != prior_ba}
    written_from(result, (handoff, note, review_note, json.dumps(protocol), json.dumps(audit)), label)
    return result, secret


# ---------------------------------------------------------------------------- MC_RTT
NLB_METRICS = {
    'r2_uniform_average': ('R², uniform mean of x and y', 'unitless', True, 'R², uniform mean of x/y'),
    'r2_x': ('R², x', 'unitless', True, 'R², x'),
    'r2_y': ('R², y', 'unitless', True, 'R², y'),
    'rmse_m_per_s': ('RMSE', 'm/s', False, 'RMSE, m/s'),
    'mae_m_per_s': ('MAE', 'm/s', False, 'MAE, m/s'),
}


def nlb(src, handoff, stage):
    label = NLB
    protocol, proto_sha = pinned(src['protocol'], f'{label} protocol')
    readiness = pinned_text(src['readinessNote'], f'{label} readiness note')
    prep, _ = pinned(src['preparationReview'], f'{label} preparation review')
    freeze, _ = pinned(src['freezeReview'], f'{label} freeze review')
    _, impl_sha = pinned_bytes(src['implementation'], f'{label} implementation')
    _, auditor_sha = pinned_bytes(src['auditor'], f'{label} auditor')
    audit, _ = pinned(src['resultAudit'], f'{label} result audit')

    require(prep['protocol_sha256'] == freeze['protocol_sha256'] == proto_sha
            and prep['implementation_sha256'] == freeze['implementation_sha256'] == impl_sha,
            f'{label}: the reviews name another protocol or implementation')
    require(audit['auditor_sha256'] == auditor_sha, f'{label}: the audit names another auditor program')
    require(prep['decision'] == 'approved_for_preparation_before_validation_scoring' and not prep['blocking_findings']
            and prep['tests']['failed'] == 0 and prep['tests']['skipped'] == 0 and prep['tests']['passed'] > 0,
            f'{label}: the preparation review did not pass')
    require(freeze['reviewed'] is True and freeze['allow'] == 'nlb_velocity_predict_and_validation_score'
            and freeze['validation_target_values_read_before_freeze'] is False
            and freeze['actual_preparation_counts_match_protocol'] is True
            and freeze['tests_passed'] == prep['tests']['passed'] and freeze['tests_skipped'] == 0,
            f'{label}: the freeze does not allow scoring')
    require(when(prep['reviewed_at_utc']) < when(freeze['reviewed_at_utc']) < when(audit['reviewed_at_utc']),
            f'{label}: preparation, freeze and audit are out of order')
    require(audit['decision'] == 'approved_aggregate_diagnostic_only' and audit['official_nlb_score'] is False
            and audit['test_file_opened'] is False and audit['train_validation_trial_overlap'] == 0
            and audit['metrics_independently_recomputed_with_sklearn'] is True
            and audit['source_only_normalization_coefficients_and_predictions_verified'] is True
            and abs(audit['ridge_normal_equation_max_abs_residual']) < 1e-9, f'{label}: the independent audit did not pass')

    ds, inp, pre = protocol['dataset'], protocol['input'], protocol['preprocessing']
    require(ds['dandiset_id'] == '000129' and ds['version'] == '0.241017.1444' and ds['license'] == 'CC-BY-4.0'
            and ds['species'] == 'macaque' and ds['subjects'] == 1 and ds['sessions'] == 1 and ds['human_subjects'] == 0,
            f'{label}: another dataset or cohort')
    require(protocol['verified']['test_file_opened'] is False and protocol['verified']['validation_target_values_read']
            is False, f'{label}: the test file or validation targets were read before the run')
    split = inp['training_file_split_counts']
    lags = pre['history_lags_bins']
    smooth = pre['causal_smoothing']['bins']
    require(lags == list(range(len(lags))), f'{label}: the history lags are not consecutive')
    require(pre['total_neural_support_ms'] == pre['bin_ms'] * (smooth + len(lags) - 1),
            f'{label}: the neural support does not follow from the bins')
    require(pre['features_before_constant_column_removal'] == inp['input_neurons'] * len(lags),
            f'{label}: the feature count is not neurons times lags')
    lo, hi = pre['candidate_bin_indices_inclusive']
    per_trial = hi - lo + 1
    rows = pre['expected_rows_before_finite_mask']
    require(rows['train'] == split['train'] * per_trial and rows['val'] == split['val'] * per_trial,
            f'{label}: the rows are not trials times retained bins')
    require(pre['observed_gap_exclusions'] == {'train': 0, 'val': 0}, f'{label}: rows were excluded')
    require(audit['validation_rows'] == rows['val'] and audit['scored_coverage'] == 1.0
            and audit['all_feature_rows_independently_reconstructed'] == audit['all_target_rows_independently_reconstructed']
            == rows['train'] + rows['val'], f'{label}: the audit did not score or reconstruct every row')
    model = protocol['model']
    require(model['class'] == 'sklearn.linear_model.Ridge' and model['alpha'] == 10.0 and model['hyperparameter_search']
            is False, f'{label}: another model')
    trial_ms = 600
    stated(readiness, f'These 1,080 segments are {trial_ms} ms each', f'{label} trial length')
    require(split['train'] + split['val'] == 1080, f'{label}: the trials do not add up')

    ridge, base = audit['models']['ridge'], audit['models']['training_mean_baseline']
    require(set(ridge) == set(base) == set(NLB_METRICS), f'{label}: the audit carries other metrics')
    better = {}
    for m, (_, _, higher, row) in NLB_METRICS.items():
        require(number(ridge[m]) and number(base[m]), f'{label}: {m} is not a number')
        better[m] = ridge[m] > base[m] if higher else ridge[m] < base[m]
    close(ridge['r2_uniform_average'], (ridge['r2_x'] + ridge['r2_y']) / 2, f'{label} ridge R² mean', 1e-15)
    close(base['r2_uniform_average'], (base['r2_x'] + base['r2_y']) / 2, f'{label} mean R² mean', 1e-15)
    # The reading the handoff binds: better squared error, worse absolute error.
    require(all(better[m] for m in ('r2_uniform_average', 'r2_x', 'r2_y', 'rmse_m_per_s')),
            f'{label}: the ridge no longer improves squared error')
    require(better['mae_m_per_s'] is False, f'{label}: the ridge is no longer worse on absolute error')
    for m, (_, _, _, row) in NLB_METRICS.items():
        stated(handoff, f'| {row} | {signed(ridge[m])} | {signed(base[m])} |', f'{label} {m}')
    stated(handoff, '**Ridge improves squared error but has worse absolute error.**', f'{label} reading')
    stated(handoff, f'**{rows["train"]:,} training rows and {rows["val"]:,} validation rows**', f'{label} rows')
    stated(handoff, f'{split["train"]} train / {split["val"]} validation trials', f'{label} trials')
    stated(handoff, f'{inp["input_neurons"]} held-in neurons', f'{label} neurons')
    s = stage['completed']['nlb_mc_rtt']
    require(s['status'] == 'audited_diagnostic_aggregate_release_eligible' and s['train_rows'] == rows['train']
            and s['val_rows'] == rows['val'] and s['ridge_r2'] == ridge['r2_uniform_average']
            and s['official_nlb_score'] is False, f'{label}: the analysis stage records other figures')

    result = {
        'id': NLB, 'dataset': 'nlb-mc-rtt',
        'title': 'Macaque intracortical spiking: finger velocity within one session',
        'question': 'How much of a monkey\'s finger velocity does a fixed linear decoder recover from motor-cortex '
                    'spiking, on held-out trials of the same session?',
        'label': 'Locally executed experiment · offline · one macaque, one session · not an official Neural Latents '
                 'Benchmark score',
        'kind': 'decoding result',
        'evidence': 'a locally executed experiment, not a score reported in a paper or on the benchmark leaderboard',
        'species': 'macaque (Macaca mulatta), one animal', 'modality': 'intracortical spiking',
        'measured_quantity': 'spike counts of sorted units recorded by an electrode array in primary motor cortex; the '
                             'decoded quantity is x/y finger velocity',
        'cohort': {'animals': ds['subjects'], 'sessions': ds['sessions'], 'training_trials': split['train'],
                   'validation_trials': split['val'], 'trial_ms': trial_ms, 'input_neurons': inp['input_neurons'],
                   'unused_neurons': inp['heldout_neurons_not_inputs']},
        'design': {
            'split': 'the dataset\'s stored training and validation trials, interleaved within the one session; no '
                     'random row split, and the test file was not opened',
            'neurons': 'the held-in neurons only; the benchmark\'s held-out neurons are not inputs',
        },
        'signal': {
            'bin_ms': pre['bin_ms'], 'smoothing_bins': smooth, 'history_lags': len(lags),
            'neural_support_ms': pre['total_neural_support_ms'],
            'features': pre['features_before_constant_column_removal'],
            'context': 'trailing spike-count history only, reset at every trial and observation gap',
            'target': 'the mean stored x/y finger velocity within a bin shifted by the target lag, in m/s',
            'target_lag_ms': pre['target']['lag_ms'], 'retained_bins_each_trial': per_trial,
            'training_rows': rows['train'], 'validation_rows': rows['val'],
            'rows_excluded': pre['observed_gap_exclusions']['train'] + pre['observed_gap_exclusions']['val'],
        },
        'models': {
            'ridge': 'standardization fitted on the training rows, then ridge regression (alpha 10, Cholesky solver, '
                     'with intercept); training-constant features dropped; no hyperparameter search',
            'training_mean': 'predicts the training rows\' mean velocity for every validation row',
        },
        'metrics': {m: {'name': name, 'unit': unit, 'higher_is_better': higher}
                    for m, (name, unit, higher, _) in NLB_METRICS.items()},
        'arms': {
            'ridge': {'label': 'Ridge on spike-count history', **{m: ridge[m] for m in NLB_METRICS}},
            'training_mean': {'label': 'Training mean (comparator)', **{m: base[m] for m in NLB_METRICS}},
        },
        'comparison': {
            'ridge_better': better,
            'note': 'The ridge improves R² and the root-mean-square error but has a larger mean absolute error than the '
                    'training mean: it is not an unconditional winner, and both directions are shown.',
        },
        'coverage': {'validation_rows_scored': audit['validation_rows'], 'scored_share': audit['scored_coverage']},
        'uncertainty': {
            'kind': 'none reported',
            'reason': 'The validation rows are temporally correlated samples from one animal in one session, not '
                      'independent subjects; no population interval is computed.',
        },
        'reading': 'On held-out trials of the same session, the ridge recovers part of the variance of finger velocity '
                   'where the training mean recovers none, and it lowers the root-mean-square error; its mean absolute '
                   'error is higher than the training mean\'s.',
        'limitations': [
            'One macaque and one recording session, with training and validation trials interleaved within it: no '
            'cross-day, cross-animal or human evidence. With one animal, every figure is that animal\'s.',
            'A separate supervised diagnostic on the stored training and validation trials: not an official Neural '
            'Latents Benchmark score, not co-smoothing and not a latent-model comparison.',
            'The velocity labels were derived offline from finger position, and the box average over each bin differs '
            'from the benchmark\'s own resampling, so equality with the benchmark\'s velocity score is not claimed.',
            'Offline: not a real-time or closed-loop controller demonstration.',
            'The validation rows are temporally correlated samples, not independent subjects.',
        ],
        'claims_not_supported': [
            'not an official Neural Latents Benchmark score and not co-smoothing',
            'no cross-day, cross-animal or human claim',
            'no real-time or closed-loop control claim',
            'the ridge is not better on every metric',
        ],
        'independent_audit': {
            'status': 'pass', 'rows_reconstructed': audit['all_feature_rows_independently_reconstructed'],
            'checked': 'every feature and target row reconstructed independently of the code that produced it; the ridge '
                       'coefficients checked against the normal equations; training-only normalization, prediction '
                       'alignment and every metric recomputed',
            'not_checked': 'the stored velocity itself, which the dataset derives offline from finger position',
        },
    }
    secret = {audit['ridge_normal_equation_max_abs_residual']}
    written_from(result, (handoff, readiness, json.dumps(protocol), json.dumps(audit), json.dumps(prep)), label)
    return result, secret


# ---------------------------------------------------------------------------- ds007420
def optical(src, handoff, stage):
    label = OPT
    ready, _ = pinned(src['readiness'], f'{label} readiness')
    audit, _ = pinned(src['resultAudit'], f'{label} result audit')
    quality = pinned_text(src['qualityNote'], f'{label} quality note')
    labels = pinned_text(src['labelNote'], f'{label} label note')

    require(audit['decision'] == 'eligible_for_aggregate_numerical_coverage_only', f'{label}: not a coverage release')
    pin, geo, lv, aux = ready['pin'], ready['geometry'], ready['label_verification'], ready['auxiliary_metadata']
    require(pin['version'] == '1.0.5' and pin['license'] == 'CC0' and ready['scoring_performed'] is False,
            f'{label}: another version, licence or a scored readiness record')
    people, recordings = ready['participants'], audit['recordings']
    per_rec = geo['wavelength_measurements']
    require(recordings == ready['recordings'] == geo['same_measured_geometry_recordings'],
            f'{label}: the recordings do not agree')
    require(per_rec == 2 * geo['unique_source_detector_pairs'] and len(geo['wavelengths_nm']) == 2,
            f'{label}: the channels are not two wavelengths per pair')
    points = ready['optical_metadata']['optical_samples_total']
    values = audit['optical_values']
    vc = audit['value_counts']
    require(audit['channel_instances'] == recordings * per_rec and values == points * per_rec,
            f'{label}: the channel or value counts do not add up')
    require(vc['finite'] + vc['nonfinite'] == values and vc['positive'] + vc['zero'] + vc['negative'] == vc['finite'],
            f'{label}: the value classes do not partition the values')
    require(vc['finite'] == vc['positive'] == values and audit['constant_channels'] == 0,
            f'{label}: the reading "every value finite and positive, no constant channel" no longer holds')
    stated(handoff, f'**{values:,} / {values:,} values finite and positive**', f'{label} values')
    stated(handoff, f'{people} people, {recordings} recordings, {per_rec} optical channels per recording', f'{label} cohort')
    stated(quality, f'| Recordings checked / excluded | {recordings} / 0 |', f'{label} exclusions')
    stated(quality, f'| Optical time points | {points:,} |', f'{label} time points')
    s = stage['completed']['ds007420']
    require(s['status'] == 'audited_numerical_coverage_only' and s['recordings'] == recordings and s['values'] == values
            and s['finite_positive_fraction'] == vc['positive'] / values, f'{label}: the analysis stage records others')
    durations = {'events_table': lv['tsv_task_duration_seconds'], 'optical_files': lv['snirf_task_duration_seconds'],
                 'cited_paper': lv['cited_paper_ball_duration_seconds']}
    require(len(set(durations.values())) == 3 and lv['ball_hand_mapping'] is None and lv['motion_code_mapping'] is None,
            f'{label}: the label gates the hold rests on are resolved; revisit the hold')
    stated(handoff, 'TSV 1 s, SNIRF stimulus 10 s, cited ball-task description 5 s', f'{label} durations')
    stated(handoff, f'Preserve the {aux["affected_recordings"]} original auxiliary-clock holds', f'{label} aux holds')
    require(aux['clock_synchronization_verified'] is False, f'{label}: the auxiliary clocks are verified; revisit')

    result = {
        'id': OPT, 'dataset': 'ds007420',
        'title': 'Human fNIRS recordings: are the optical values numerically usable?',
        'question': 'Are the optical values of every recording finite and positive, with no exactly constant channel?',
        'label': 'Locally executed check · label-independent · counts only',
        'kind': 'numerical coverage check',
        'evidence': 'a locally executed check, not a score and not a result reported in a paper',
        'species': 'human', 'modality': 'fNIRS',
        'measured_quantity': 'raw optical intensity at two wavelengths for each source–detector pair',
        'wavelengths_nm': geo['wavelengths_nm'],
        'cohort': {'people': people, 'recordings': recordings, 'recordings_excluded': 0,
                   'channels_each_recording': per_rec, 'recording_channels': audit['channel_instances'],
                   'optical_time_points': points},
        'counts': {'optical_values': values, 'finite': vc['finite'], 'positive': vc['positive'], 'zero': vc['zero'],
                   'negative': vc['negative'], 'nonfinite': vc['nonfinite'], 'constant_channels': audit['constant_channels']},
        'shares': {'finite': vc['finite'] / values, 'positive': vc['positive'] / values},
        'definitions': 'Shares use every optical value as the denominator. A constant channel is one whose samples are '
                       'all finite and exactly equal, with no tolerance.',
        'reading': 'Every optical value of every recording is finite and positive, and no channel is exactly constant. '
                   'That is basic numerical coverage, a precondition for further optical processing.',
        'gates': {
            'task_code_lookup_verified': False,
            'event_duration_s': durations,
            'auxiliary_clock_hold_recordings': aux['affected_recordings'],
            'classifier': 'held',
        },
        'limitations': [
            'Coverage counts only: not signal-to-noise, scalp coupling, saturation, motion, wavelength-pair integrity, '
            'physiological plausibility, neural origin, task validity or decoding evidence. Positive, non-constant '
            'values alone cannot establish signal quality.',
            'No classifier score exists. The numeric task codes have no verified lookup to hands or movements, and the '
            'event durations disagree between the events table, the optical files and the cited paper.',
            'The auxiliary motion-sensor clocks are unverified and their holds stand: optical coverage does not repair '
            'them.',
        ],
        'claims_not_supported': [
            'no signal quality, neural origin or activation claim',
            'no decoding score',
        ],
        'independent_audit': {
            'status': 'pass', 'recordings': recordings,
            'checked': 'every channel count reconciled against the recording totals and the aggregate; the code and '
                       'its synthetic tests reviewed',
            'not_checked': 'the raw-signal pass was not repeated',
        },
    }
    secret = {pin['acquired_bytes'], pin['acquired_assets']}
    written_from(result, (handoff, quality, labels, json.dumps(ready), json.dumps(audit)), label)
    return result, secret


# ---------------------------------------------------------------------------- status only
def falcon_h2(src, handoff, stage, rights):
    label = H2
    ready, _ = pinned(src['readiness'], f'{label} readiness')
    note = pinned_text(src['labelNote'], f'{label} label note')
    v, run = ready['verified'], ready['first_run']
    require(ready['dandiset_id'] == '000950' and ready['version'] == '0.241029.1403', f'{label}: another dataset')
    require(v['models_fitted'] is False and v['scoring_performed'] is False and v['test_targets_read'] is False
            and v['neural_value_arrays_read'] is False, f'{label}: not preparation only')
    tr, fl = v['trials_by_split'], v['files_by_split']
    require(sum(fl.values()) == v['files'] and run['minival_trials'] == tr['held_in_minival']
            and run['split_policy']['excluded_calibration_trials'] == tr['held_in_minival']
            and run['training_trials'] == tr['held_in_calib'] - run['split_policy']['excluded_calibration_trials']
            and run['split_policy']['additional_prompt_hash_exclusions'] == 0 and v['all_minival_trials_are_first_two_calibration_recording_events']
            and run['held_out_calibration_trials_used'] == 0, f'{label}: the decontamination does not add up')
    voc = run['vocabulary']
    require(len(voc['codepoints']) == voc['symbols'] and voc['ctc_classes_including_blank'] == voc['symbols'] + 1,
            f'{label}: the vocabulary does not add up')
    s = stage['prepared_not_scored']['falcon_h2']
    require(s['calibration_trials'] == tr['held_in_calib'] and s['minival_trials_all_overlap'] == tr['held_in_minival']
            and s['cleaned_train_candidate'] == run['training_trials']
            and s['heldout_calibration_not_evaluation'] == tr['held_out_calib'], f'{label}: the stage records others')
    stated(handoff, f'all {tr["held_in_minival"]} public minival trials duplicated inside {tr["held_in_calib"]} held-in '
                    'calibration trials', f'{label} overlap')
    stated(handoff, f'The resulting {run["training_trials"]}-trial training candidate is not yet fitted', f'{label} train')
    stated(handoff, f'supplies {voc["symbols"]} symbols plus CTC blank', f'{label} symbols')
    stated(note, f'one human across {v["distinct_dates"]} recording dates', f'{label} dates')
    entry = {
        'id': H2, 'dataset': 'falcon-h2', 'name': 'FALCON H2 · human intracortical handwriting',
        'status': 'status_only', 'scores_published': False,
        'species': 'human, one participant', 'modality': 'intracortical spiking',
        'reason': 'Prepared, not scored: no model has been fitted. The label audit found every public minival trial '
                  'inside the calibration data, so a leakage-safe diagnostic must first remove those trials from '
                  'training.',
        'preparation': {
            'participants': v['human_subjects'], 'recording_dates': v['distinct_dates'], 'files': v['files'],
            'channels': v['shape_channels'], 'held_in_calibration_trials': tr['held_in_calib'],
            'minival_trials': tr['held_in_minival'], 'minival_trials_also_in_calibration': run['split_policy']['excluded_calibration_trials'],
            'training_candidate_trials': run['training_trials'], 'held_out_calibration_trials': tr['held_out_calib'],
            'symbols': voc['symbols'], 'ctc_classes_with_blank': voc['ctc_classes_including_blank'],
        },
        'facts': [
            'The public minival trials were inspected to find the overlap, so a later diagnostic on them would be '
            'exposed, not blinded, and would not be the official FALCON cross-day score.',
            'The held-out calibration trials are inputs for few-shot recalibration, not independent evaluation data.',
            'The cleaned training trials alone carry the symbol set; a CTC decoder adds one class for the blank.',
        ],
        'rights': {k: rights[k] for k in ('source', 'license', 'licenseUrl', 'attribution')},
    }
    written_from(entry, (handoff, note, json.dumps(ready)), label)
    return entry


def rabut_fus(src, handoff, stage, rights):
    label = FUS
    ready, _ = pinned(src['readiness'], f'{label} readiness')
    note = pinned_text(src['labelNote'], f'{label} label note')
    require(ready['dataset']['doi'] == '10.22002/f3y3k-em558' and ready['dataset']['dataset_license'] == 'CC BY-NC 4.0'
            and ready['scoring_performed'] is False, f'{label}: another dataset or a scored readiness record')
    human = next(e for e in ready['experiments'] if e['id'] == 'human')
    require(human['paper_n'] == 1 and human['organism'] == 'human', f'{label}: not one human')
    s = stage['prepared_not_scored']['rabut_fus']
    p = s['paradigms']
    require(s['status'] == 'human_label_time_mapping_verified_no_image_values_read', f'{label}: values were read')
    require(sum(p.values()) == s['runs'] == human['mat_files'] and s['rest_frames'] + s['activity_frames'] == s['frames'],
            f'{label}: the runs or frames do not add up')
    stated(note, f'| **Total** | **{s["runs"]}** | **{s["frames"]:,}** | **{s["rest_frames"]:,}** | '
                 f'**{s["activity_frames"]:,}** |', f'{label} totals')
    stated(handoff, f'Their {s["frames"]:,} frames contain {s["rest_frames"]:,} rest and {s["activity_frames"]:,} '
                    'activity frames', f'{label} frames')
    stated(handoff, 'seven drawing runs, one guitar run, and one mixed speech/reading run', f'{label} runs')
    stated(handoff, 'This is one human, not nine participants', f'{label} one human')
    entry = {
        'id': FUS, 'dataset': 'rabut-fus', 'name': 'Rabut et al. · human functional ultrasound through a cranial window',
        'status': 'status_only', 'scores_published': False,
        'species': 'human, one participant', 'modality': 'functional ultrasound imaging',
        'reason': 'Prepared, not analyzed: frame labels, timestamps and image axes are verified; no Doppler value has '
                  'been read and no decoder has been fitted.',
        'preparation': {
            'participants': human['paper_n'], 'runs': s['runs'], 'drawing_runs': p['drawing'],
            'guitar_runs': p['guitar'], 'mixed_speech_reading_runs': p['mixed_speech_reading'],
            'frames': s['frames'], 'rest_frames': s['rest_frames'], 'activity_frames': s['activity_frames'],
        },
        'facts': [
            'One person, not nine participants: the runs are repeated recordings of one participant.',
            'Only rest versus activity (zero versus nonzero labels) is verified; the speech and reading codes of the '
            'mixed run have no verified individual meaning.',
            'Measured timestamps are used: the nominal block durations in the run labels disagree with the measured '
            'frame timing.',
            'Drawing, guitar and speech or reading are different paradigms and are not pooled into one task.',
        ],
        'rights': {k: rights[k] for k in ('source', 'license', 'licenseUrl', 'attribution')},
    }
    written_from(entry, (handoff, note, json.dumps(ready), json.dumps(s)), label)
    return entry


# ---------------------------------------------------------------------------- boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source file or participant identifier in export: {trail}')
        require(not PRIVATE_TOKENS.search(value), f'private host or path in export: {trail}')
        if trail not in ('$.schema_version', '$.release_id'):   # identifiers, kept as they are
            require(not VERSION_LABEL.search(value), f'a version label in export text: {trail}')
            require(not UPDATE_MARKER.search(value), f'an update marker in export text: {trail}')
        require('jev' not in value.lower(), f'{trail}: Jev is not part of this page')


def claims_negated(payload):
    """A claim these results do not support appears only in a sentence that negates it."""
    for trail, text in strings(payload):
        if any(trail.startswith(p) for p in ('$.datasets', '$.provenance', '$.not_published')) or '.rights.' in trail:
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def figure_free(holds):
    """A hold says that no score exists and why; it carries none, not even a number in prose."""
    for h in holds:
        require(set(h) == {'id', 'statement', 'reason', 'scope'}, f'hold {h.get("id")}: unexpected fields')
        require(all(isinstance(v, str) and not re.search(r'\d', v.replace('ds007420', '')) for v in h.values()),
                f'hold {h["id"]}: a hold carries a figure')
    return holds


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require([d['id'] for d in manifest['datasets']] == list(DATASETS), 'the manifest names other datasets')
    require([s['id'] for s in manifest['sources']] == [*RESULTS, *STATUS], 'the manifest names other sources')
    src = {s['id']: s for s in manifest['sources']}
    for s in manifest['sources']:
        require(s['decision'] in DECISIONS[s['id']], f'{s["id"]}: no extractor for the decision {s["decision"]!r}')
        require(DATASETS[s['dataset']] == s['id'], f'{s["id"]}: filed under another dataset')

    handoff, _, stage = batch(manifest['batch'])
    datasets = {d['id']: dataset_rights(d) for d in manifest['datasets']}
    rights = {d['id']: d for d in manifest['datasets']}

    extract = {BAK: bak, NLB: nlb, OPT: optical}
    results, secret, holds = {}, set(), list(manifest['holds'])
    standby = {h['id']: h for h in manifest.get('standbyHolds', [])}
    for sid in RESULTS:
        if src[sid]['decision'] == 'hold':
            require(sid in standby, f'{sid}: held without a hold entry')
            holds.append(standby[sid])
            continue
        results[sid], s = extract[sid](src[sid], handoff, stage)
        secret |= s
    status = [falcon_h2(src[H2], handoff, stage, rights['falcon-h2']),
              rabut_fus(src[FUS], handoff, stage, rights['rabut-fus'])]
    for did, entry in datasets.items():
        sid = DATASETS[did]
        entry['results'] = [sid] if sid in results else []
        entry['status_only'] = [sid] if sid in STATUS else []
        entry['held'] = [sid] if sid in RESULTS and sid not in results else []

    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'question': QUESTION,
        'metric_units': 'balanced accuracy, class recall, chance levels and shares are proportions in [0,1]; R² is '
                        'unitless; RMSE and MAE are in m/s; sampling rates in Hz, windows and lags in seconds or '
                        'milliseconds as named; counts of people, animals, trials, rows, recordings, channels, values, '
                        'runs and frames are whole numbers',
        'scope': 'Locally executed analyses and prepared sources beyond scalp EEG, each its own species, modality and '
                 'measured quantity: human fNIRS classification of executed movements, macaque intracortical decoding '
                 'of finger velocity, a numerical coverage check of human fNIRS recordings, and two sources prepared '
                 'but not scored (human intracortical handwriting, human functional ultrasound). They share no metric '
                 'and no ranking, none is compared with scalp EEG, and nothing joins the eight-protocol matrix. Every '
                 'figure is this site\'s own experiment, not a score reported in a paper.',
        'results': results,
        'status_only': status,
        'datasets': datasets,
        'holds': figure_free(holds),
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes), 'included': list(results), 'status_only': [e['id'] for e in status],
            'holds': [h['id'] for h in holds],
            'source_audit_sha256': {sid: src[sid]['resultAudit']['sha256'] for sid in results},
            'source_readiness_sha256': {sid: src[sid]['readiness']['sha256'] for sid in STATUS},
            'handoff_sha256': manifest['batch']['handoff']['sha256'],
        },
    }
    scrub_check(payload)
    claims_negated(payload)
    validate_public(payload)
    published = set(numbers(payload))
    leaked = sorted(v for v in secret if v in published)
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    return payload


def input_refs(manifest):
    refs = []
    for d in manifest['datasets']:
        refs += [d['licenseRecord'], d['consentEthics']['record']]
        refs += [d[k] for k in ('sourceRecord', 'readmeRecord') if k in d]
        if 'extractedFrom' in d['consentEthics']['record']:
            refs.append(d['consentEthics']['record']['extractedFrom'])
    refs += [v for v in manifest['batch'].values() if isinstance(v, dict)]
    for s in manifest['sources']:
        refs += [v for v in s.values() if isinstance(v, dict) and 'sha256' in v and 'path' in v]
    return refs


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_beyond_scalp_export
    return audit_beyond_scalp_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
