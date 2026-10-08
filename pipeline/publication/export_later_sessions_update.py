"""Release four results under one question, aggregate-only: does a decoder trained on an earlier session still work later?

From the large-source batch, each result with its own approved release JSON, handoff, release decision and
independent audits, nothing shared between them but the question:

- WBCIC-SHU, two fixed CPU baselines (a source-majority prior and a relative spectral ridge) trained on each
  person's recording session 1 and tested on session 3, in two separate cohorts (51 two-class, 11 three-class);
- WBCIC-SHU again, frozen CBraMod with a ridge readout fitted on session 1, against that spectral ridge, on the
  same people and trials;
- the longitudinal RSVP source, one ERP baseline trained at the first visit and scored at the publisher's nominal
  Day 7, 80 and 200 visits (15 people);
- Forenzo's continuous-tracking source on KiltHub, a spectral ridge from each record's earliest to latest complete
  session against a source-mean comparator: a negative result, two cohorts and two response arms kept apart.

Its own publication boundary, as with every batch. The website inputs are the four release JSONs. The handoffs,
release decisions, independent audits, root checks and reviews are pinned by hash and checked against those exact
bytes, never copied: they carry private storage paths. The rights evidence (each source's figshare API record and
the Europe PMC full text of its paper) is pinned the same way and its quotes are checked against it.

What this export refuses:
- per-person and per-record values: every minimum, 10th and 90th percentile, every median except the four Forenzo
  ridge medians the handoff requires beside their means, the Forenzo paired minimum (only the count of records it
  implies is published), by key, by fragment and by value;
- confusion matrices, per-class recall, decoder strata, measured compute, identifiers, predictions, features,
  thresholds and private paths;
- a null turned into a number, an interval that does not hold its mean, a count that is not a whole number of
  people or records over the right denominator, a reading the numbers no longer support, a version label or an
  update date in the text, and a claim of online control, intention decoding, causation or zero-shot transfer
  that is not negated.

    python3 pipeline/publication/export_later_sessions_update.py
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
REVIEW = PROJECT / 'research/publication_review_20261008'
MANIFEST = REVIEW / 'later-sessions-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'later-sessions-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/later-sessions-update.json',
           PROJECT / 'site/public/data/later-sessions-update.json')
RELEASE_ID = 'later-sessions-update-20261008'
SCHEMA = 'bci-report-later-sessions-update-v1'
QUESTION = 'Does a decoder trained on an earlier session still work later?'

WBCIC_CPU, WBCIC_FM = 'wbcic-cross-session-cpu', 'wbcic-frozen-cbramod'
RSVP, FORENZO = 'rsvp-later-visits', 'forenzo-continuous-control'
DATASETS = {'wbcic-shu': (WBCIC_CPU, WBCIC_FM), 'longitudinal-rsvp': (RSVP,),
            'forenzo-continuous-tracking': (FORENZO,)}

# Per-person distributions, a decoder's internals and what this batch leaves out on purpose. Refused by exact key
# and by fragment; the one exception is the Forenzo ridge median, at the four paths median_allowed() names.
REFUSED_KEYS = PER_PERSON_KEYS | {'minimum', 'maximum', 'p10', 'p90', 'q1', 'q3', 'range', 'per_class',
                                  'private_audit', 'resources', 'stage_action_wall_seconds'}
REFUSED_KEY_FRAGMENTS = ('threshold', 'prediction', 'probabilit', 'feature', 'private', 'participant_id',
                         'record_id', 'per_person', 'per_participant', 'per_record', 'minimum', 'maximum',
                         'quantile', 'percentile', 'worst', 'p10', 'p90', 'confusion', 'per_class', 'pooled',
                         'combined', 'basename', 'wall_seconds', 'rss', 'elapsed', 'strata', 'stratum', 'path')
# Upstream file and participant names: S1.mat ... S15.mat, S26.zip, sub-01, and any raw-file extension.
SOURCE_IDS = re.compile(r'\bS\d{1,2}\b|\bsub-\d+|\bsess\d+|\bsubj\d+|\.(?:mat|zip|h5|hdf5|npz|npy|bdf|edf|gdf|set|fif)\b'
                        r'|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|Gal4|TRX50', re.IGNORECASE)
# The date rule: no internal version label ("v9", "(v1)") and no update marker in the text. Dataset DOIs keep
# their ".v5" and "/v1" (preceded by a dot or a slash, so not matched).
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'\b(?:updated?|added)\b|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d', re.IGNORECASE)
# Claims these results do not support, allowed only in a sentence that negates them.
CLAIMS = re.compile(r'\bonline\b|real-time|closed-loop|intended[- ]motion|intention|\bclinical\b|zero-shot|\bcausal|\bcaused\b'
                    r'|unseen pretraining|certified unseen|\bendorse', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|without|cannot|unsupported|unverified|unconfirmed|unestablished|"
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


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def stated(text, phrase, label):
    """The release figure the pages print is the one the pinned handoff states."""
    require(phrase in text, f'{label}: the handoff does not state {phrase!r}')


def plain(xml):
    """The running text of a pinned full-text record: tags dropped, entities decoded, whitespace collapsed."""
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', xml))).strip()


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
    elif isinstance(value, float):
        yield value


def written_from(result, sources, label, skip=('rights', 'credits', 'model', 'release_limits', 'pretraining_exposure')):
    """Every numeral in the prose this export writes is one the pinned handoff or release states."""
    allowed = set().union(*(numerals(s) for s in sources))
    for key, value in result.items():
        if key in skip:
            continue
        for trail, text in strings(value, f'{label}.{key}'):
            missing = numerals(text) - allowed
            require(not missing, f'{trail}: the numerals {sorted(missing)} are in no pinned handoff or release')


# ---------------------------------------------------------------------------- rights
def dataset_rights(record):
    """Licence from the pinned repository record; consent and ethics from the pinned paper, each quote found in it."""
    label = record['id']
    require(approved({**record, 'decision': 'aggregate_preview'}), f'{label}: the rights record is incomplete')
    lic, _ = pinned(record['licenseRecord'], f'{label} licence record')
    require(lic['license']['url'] == record['licenseUrl'], f'{label}: the repository names another licence URL')
    names = {'CC BY 4.0': 'CC BY 4.0', 'CC0': 'CC0-1.0'}
    require(names.get(lic['license']['name']) == record['license'], f'{label}: the repository names another licence')
    require(lic['is_public'] is True and lic['is_embargoed'] is False and lic['status'] == 'public',
            f'{label}: the repository record is not public')
    doi = record['source'].removeprefix('https://doi.org/')
    require(lic['doi'] == doi and doi in record['version'] and doi in record['attribution'],
            f'{label}: the repository DOI differs from the record')
    require(any(lic['url_public_api'] in u for u in record['reviewBasis']), f'{label}: the API record is not a basis')
    for a in lic['authors']:
        require(a['full_name'] in record['attribution'], f'{label}: the attribution omits {a["full_name"]}')
    ce = record['consentEthics']
    paper = pinned_text(ce['record'], f'{label} paper')
    text = plain(paper)
    require(ce['status'] == 'stated' and ce['source'] in record['reviewBasis'], f'{label}: consent and ethics are '
            'not stated from a listed source')
    require(f'<article-id pub-id-type="doi">{ce["paperDoi"]}</article-id>' in paper,
            f'{label}: the pinned full text is another paper')
    require(ce['paperDoi'] in record['attribution'], f'{label}: the attribution does not cite the paper read')
    for kind in ('ethics', 'consent'):
        quotes = [q['text'] for q in ce['quotes'] if q['statement'] == kind]
        require(len(quotes) == 1 and quotes[0] in text, f'{label}: the {kind} statement has no quote in the paper')
        require(ce[kind], f'{label}: no {kind} statement recorded')
    return {
        'rights': {k: record[k] for k in ('name', 'task', 'source', 'version', 'license', 'licenseUrl', 'attribution',
                                          'privacyReview', 'reviewedAt', 'reviewBasis')},
        'consent_and_ethics': {
            'ethics_approval': {'stated': True, 'statement': ce['ethics'],
                                'quote': next(q['text'] for q in ce['quotes'] if q['statement'] == 'ethics')},
            'informed_consent': {'stated': True, 'statement': ce['consent'],
                                 'quote': next(q['text'] for q in ce['quotes'] if q['statement'] == 'consent')},
            'read_from': f'{ce["source"]} (doi:{ce["paperDoi"]}), {ce["section"]}, read {ce["record"]["retrievedAt"]}',
        },
    }


# ---------------------------------------------------------------------------- WBCIC-SHU
WBCIC_COHORTS = {
    '2C': {'people': 51, 'label': 'Two-class motor imagery', 'handoff_cpu': 'Two-class MI',
           'handoff_fm': 'Two-class motor imagery', 'classes': ['left hand', 'right hand']},
    '3C': {'people': 11, 'label': 'Three-class motor imagery', 'handoff_cpu': 'Three-class MI',
           'handoff_fm': 'Three-class motor imagery', 'classes': ['left hand', 'right hand', 'foot']},
}
WBCIC_ARMS = {
    'source_prior': ('Source-majority prior', 'predicts, for every session-3 trial, the class most frequent in the '
                     "person's session 1 (the smallest class code on a tie); its balanced accuracy is one over the "
                     'number of classes when every class is present'),
    'relative_spectral_ridge': ('Relative spectral power + ridge', 'Welch relative band power per channel as log '
                                'ratios, standardized on session 1, then a ridge classifier'),
}
CPU_AUDIT_VERDICT = 'pass_exact_saved_results'
PEOPLE = sum(c['people'] for c in WBCIC_COHORTS.values())


def wbcic_cpu(src):
    label = WBCIC_CPU
    release, release_sha = pinned(src['release'], f'{label} release')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    decision, _ = pinned(src['releaseDecision'], f'{label} release decision')
    audit, audit_sha = pinned(src['numericalAudit'], f'{label} audit')
    freeze, _ = pinned(src['rootActivation'], f'{label} root freeze')
    protocol_review, _ = pinned(src['protocolReview'], f'{label} protocol review')
    code_review, code_sha = pinned(src['codeReview'], f'{label} code review')

    # Chain: decision -> release bytes and audit; release -> audit, protocol, activation; freeze -> code review.
    require(decision['export']['sha256'] == release_sha and decision['audit']['sha256'] == audit_sha,
            f'{label}: the release decision names other release or audit bytes')
    require(decision['verdict'] == 'approve_aggregate_handoff_only' and decision['release_eligible'] is True
            and decision['website_or_system_changes'] is False, f'{label}: the decision does not approve an aggregate')
    v = decision['verified']
    require(v['participants'] == v['all_participant_metrics_reproduced'] == v['target_label_members_reextracted']
            == v['saved_model_predictions_reconstructed'] == PEOPLE and v['cohort_bootstraps_reproduced'] == 2,
            f'{label}: the decision did not verify all 62 people and both cohorts')
    require(release['release_status'] == 'audited_aggregate_release_eligible' and release['website_edited'] is False
            and release['model_scope'] == 'source_majority_prior_and_fixed_relative_spectral_ridge_only',
            f'{label}: not the approved two-baseline release')
    prov = release['provenance']
    require(prov['audit_sha256'] == audit_sha, f'{label}: the release names another audit')
    for k, x in audit['pins'].items():
        require(prov[k] == x, f'{label}: release and audit differ on {k}')
    require(audit['verdict'] == CPU_AUDIT_VERDICT and audit['scope']['refitting_performed'] is False
            and audit['scope']['frozen_pipeline_modified'] is False and audit['scope']['cohorts_separate'] is True
            and audit['scope']['target_label_streams_independently_loaded'] == PEOPLE,
            f'{label}: the independent audit did not pass')
    i = audit['integrity']
    require(i['independent_participant_metric_rows_exactly_match'] == PEOPLE
            and i['independent_cohort_summaries_and_paired_bootstraps_exactly_match'] == 2,
            f'{label}: the audit did not reproduce every person and both cohorts')
    require(freeze['verdict'] == 'approve_exact_activation' and freeze['approved'] is True
            and freeze['independent_code_review_sha256'] == code_sha
            and freeze['frozen_protocol_sha256'] == prov['frozen_protocol_sha256']
            and freeze['implementation_sha256'] == prov['production_implementation_sha256']
            and freeze['input_manifest_sha256'] == prov['input_manifest_sha256'],
            f'{label}: the root freeze names another protocol, implementation or review')
    require(code_review['verdict'] == 'pass_exact_implementation' and code_review['approved'] is True,
            f'{label}: the code review did not pass')
    require(protocol_review['verdict'].startswith('ready_to_freeze'), f'{label}: the protocol review did not pass')
    require(when(audit['at_utc']) <= when(release['at_utc']) == when(decision['at_utc']),
            f'{label}: the audit postdates the release, or decision and release are not one act')

    # Every figure is the audited one, value for value.
    require(release['cohorts'] == audit['method_results'], f'{label}: the release cohorts differ from the audit')
    require(release['trial_accounting'] == audit['cohort_accounting'], f'{label}: trial accounting differs')
    require(release['qa_holds_preserved'] == audit['qa_holds'], f'{label}: QA holds differ')
    require(release['source'] == audit['source'] == 'figshare--wbcic-shu-v5', f'{label}: another source version')

    m = release['method']
    require(m['source_session_ordinal'] == 1 and m['test_session_ordinal'] == 3 and m['unused_session_ordinal'] == 2
            and m['target_calibration_labels'] == 0 and m['cohorts_pooled'] is False and m['equal_person_metrics'] is True
            and m['hyperparameter_search'] is False
            and m['ridge'] == {'alpha': 1.0, 'fit_intercept': True, 'class_weight': None, 'solver': 'svd'},
            f'{label}: not the frozen session-1 to session-3 method')
    require(release['participants'] == PEOPLE and release['no_source_or_target_feature_exclusions'] is True,
            f'{label}: not 62 people with no exclusion')

    cohorts, ta = {}, release['trial_accounting']
    for c, shape in WBCIC_COHORTS.items():
        n, k = shape['people'], len(shape['classes'])
        b = release['cohorts'][c]
        require(b['expected_participants'] == b['fitted_participants'] == b['structural_participants']
                == b['balanced_accuracy_defined_participants'] == n and b['held_participants'] == 0,
                f'{label}/{c}: not {n} people, all defined')
        cd = b['conditional_descriptive']
        require(cd['declared_participants'] == cd['defined_participants'] == n and cd['bootstrap_draws'] == 10000,
                f'{label}/{c}: the bootstrap does not cover the declared cohort')
        t = ta[c]
        require(t['source_feature_excluded_trials'] == t['target_feature_excluded_trials'] == 0
                and t['source_delivered_trials'] == t['source_feature_valid_trials']
                and t['target_delivered_trials'] == t['target_feature_valid_trials'], f'{label}/{c}: trials excluded')
        arms = {}
        for arm, (name, desc) in WBCIC_ARMS.items():
            a = b['methods'][arm]
            require(a['primary_status'] == 'defined_complete_declared_cohort'
                    and a['accuracy_defined_participants'] == a['macro_f1_defined_participants'] == n,
                    f'{label}/{c}/{arm}: not defined for every person')
            close(a['primary_balanced_accuracy_mean'], cd['observed_means'][arm], f'{label}/{c}/{arm}: mean')
            require(a['primary_ci_95_percentile'] == cd['ci_95_percentile'][arm], f'{label}/{c}/{arm}: interval')
            ba = a['primary_balanced_accuracy_mean']
            arms[arm] = {'label': name, 'description': desc,
                         'balanced_accuracy': {'mean': ba, 'interval_95': bounded(ba, a['primary_ci_95_percentile'],
                                                                                  f'{label}/{c}/{arm}', 0.0, 1.0)},
                         'accuracy': {'mean': a['accuracy_conditional_mean']},
                         'macro_f1': {'mean': a['macro_f1_conditional_mean']}}
            require(0 <= a['accuracy_conditional_mean'] <= 1 and 0 <= a['macro_f1_conditional_mean'] <= 1,
                    f'{label}/{c}/{arm}: a secondary mean leaves [0,1]')
        # The prior's balanced accuracy is one over the number of classes, with no spread.
        prior = arms['source_prior']['balanced_accuracy']
        close(prior['mean'], 1 / k, f'{label}/{c}: prior balanced accuracy', 1e-15)
        require(all(abs(x - 1 / k) <= 1e-15 for x in prior['interval_95']), f'{label}/{c}: the prior has a spread')
        d = cd['observed_means']['ridge_minus_prior']
        close(d, arms['relative_spectral_ridge']['balanced_accuracy']['mean'] - prior['mean'], f'{label}/{c}: paired mean')
        iv = bounded(d, cd['ci_95_percentile']['ridge_minus_prior'], f'{label}/{c}: paired', -1.0, 1.0)
        require(iv[0] > 0, f'{label}/{c}: the paired interval no longer excludes zero; the reading must be reviewed')
        cohorts[c] = {
            'label': shape['label'], 'classes': shape['classes'], 'people': n, 'chance_level': 1 / k,
            'source_trials': t['source_delivered_trials'], 'target_trials': t['target_delivered_trials'],
            'arms': arms,
            'paired': {'comparison': 'relative spectral ridge minus source prior, the same people and trials',
                       'balanced_accuracy_difference': {'mean': d, 'interval_95': iv},
                       'interval_excludes_zero': iv[0] > 0 or iv[1] < 0, 'people': n},
        }

    src_trials = sum(c['source_trials'] for c in cohorts.values())
    tgt_trials = sum(c['target_trials'] for c in cohorts.values())
    require(src_trials == release['source_trials'] and tgt_trials == release['test_trials'],
            f'{label}: cohort trials do not add up to the release totals')
    q = release['qa_holds_preserved']
    sessions = q['strict_contract_holds_preserved'] + q['strict_contract_passes_preserved']
    require(sessions == 3 * PEOPLE and q['selected_source_or_target_hold_records'] + q['unused_session02_hold_records']
            == q['strict_contract_holds_preserved'] and q['missing_trial_mechanism'] == 'unknown',
            f'{label}: the session holds do not add up')
    delivered, nominal = 40490, 40500

    # Last: the figures the pages print are the ones the pinned handoff states.
    for c, shape in WBCIC_COHORTS.items():
        e = cohorts[c]
        r, p = e['arms']['relative_spectral_ridge']['balanced_accuracy'], e['arms']['source_prior']['balanced_accuracy']
        stated(handoff, f'| {shape["handoff_cpu"]} | {e["people"]} | {100 * p["mean"]:.2f}% | {100 * r["mean"]:.2f}% '
                        f'[{100 * r["interval_95"][0]:.2f}, {100 * r["interval_95"][1]:.2f}] | '
                        f'{100 * e["paired"]["balanced_accuracy_difference"]["mean"]:+.2f} percentage points |',
               f'{label}/{c}')
    stated(handoff, f'Two-class: {cohorts["2C"]["source_trials"]:,} source and {cohorts["2C"]["target_trials"]:,} target '
                    f'trials. Three-class: {cohorts["3C"]["source_trials"]:,} source and {cohorts["3C"]["target_trials"]:,} '
                    f'target trials. Total: {src_trials:,} training and {tgt_trials:,} test trials across 124 selected '
                    'session files.', f'{label} trials')
    stated(handoff, f"Six of the full cohort's {sessions} session records contain fewer trials than the publisher's "
                    f'nominal counts: {delivered:,} delivered trials versus {nominal:,} nominal.', f'{label} holds')

    result = {
        'id': WBCIC_CPU, 'dataset': 'wbcic-shu',
        'title': 'WBCIC-SHU: session 1 to session 3, two fixed CPU baselines',
        'question': "A decoder trained on each person's first recording session and tested on their third, with no "
                    'labels from the third: how far do two fixed CPU baselines get?',
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'generalization': 'the same person, a later recording session: trained on session 1, tested on session 3. '
                          'Not an unseen person and not another dataset.',
        'sessions': {'train': m['source_session_ordinal'], 'test': m['test_session_ordinal'],
                     'unused': m['unused_session_ordinal'], 'target_session_labels': m['target_calibration_labels'],
                     'unit': 'recording-session ordinal',
                     'time_between': 'not stated: the ordinals are not a guaranteed time gap or distinct calendar days'},
        'metric': 'balanced_accuracy',
        'weighting': 'participant-equal: each person counts once in a cohort mean; never a trial-weighted score '
                     'across people, and the two cohorts are never averaged together',
        'cohorts': cohorts,
        'trials': {'source': src_trials, 'target': tgt_trials, 'session_files': 124, 'excluded': 0},
        'session_quality': {
            'sessions': sessions, 'fixed_count_holds': q['strict_contract_holds_preserved'],
            'holds_in_selected_sessions': q['selected_source_or_target_hold_records'],
            'holds_in_unused_session_2': q['unused_session02_hold_records'],
            'delivered_trials': delivered, 'nominal_trials': nominal, 'missing_trial_cause': 'unknown',
            'rule': 'The short sessions are admitted under a reviewed variable-N rule: no filling, truncation, '
                    'balancing or performance-based exclusion, and the original holds stay recorded.',
        },
        'method': {
            'data': "the publisher's processed derivative: 58 anonymous channel indices at 250 Hz in four-second "
                    'epochs; each cohort kept apart',
            'split': "every person's complete session 1 trains, their session 3 is the test; session 2 is unused",
            'spectra': 'Welch relative band power in 4–8, 8–13, 13–30 and 30–40 Hz per channel, as log ratios with a '
                       'floor of 1e-12: 232 values per trial, float64',
            'arms': {arm: desc for arm, (_, desc) in WBCIC_ARMS.items()},
            'ridge': 'StandardScaler fitted on session 1 only; RidgeClassifier with alpha 1, an intercept, no class '
                     'weights and the SVD solver',
            'selection': 'none: no hyperparameter search, target normalization, calibration or abstention',
            'scoring': 'the ordered session-3 labels were opened only by a separate scorer after every prediction was '
                       'sealed; earlier schema checks had inspected label domains and counts',
            'balanced_accuracy': 'per person, the mean recall over the classes; then the mean over the people of '
                                 'the cohort',
        },
        'uncertainty': {
            'kind': 'pointwise 95% percentile interval from 10,000 paired participant bootstrap draws within each '
                    'cohort',
            'conditional_on': 'the fixed trained models and predictions: refitting and preprocessing-selection '
                              'uncertainty are not included',
        },
        'reading': 'In both cohorts the spectral ridge is above the source prior, with paired intervals above zero, '
                   'and the gains are small: a few points of balanced accuracy, with no labels from the test session.',
        'limitations': [
            'One dataset and the same people: trained on recording session 1 and tested on session 3 of each person. '
            'Not an unseen person, another dataset or a held-out-person benchmark.',
            'Session numbers are recording-session ordinals, not a guaranteed time gap or distinct calendar days.',
            'Six of the 186 session records hold fewer trials than the publisher’s nominal count (40,490 delivered '
            'against 40,500 nominal). Three of them are in the selected sessions and are admitted under the reviewed '
            'variable-N rule; the original holds stay recorded. Why the trials are missing is unknown.',
            'The publisher’s processed derivative is used as delivered. The selection history and temporal support of '
            'its reference, filter, epoch and baseline choices are not fully established, and its channel order rests '
            'on the publisher’s procedures and the raw headers, not on a direct raw-to-processed proof.',
            'Offline only: no real-time, causal, clinical, prospective-deployment or physical-amplitude claim.',
            'Two fixed baselines. They say nothing about EEGNet, CSP, any foundation model or LoRA, and nothing about '
            'whether calibration labels from session 3 would help: that needs its own matched arm.',
            'The ordered test labels were read only after every prediction was sealed, but earlier schema checks had '
            'inspected label domains and counts: the investigators were not blind to all target metadata.',
        ],
        'release_limits': release['limits'],
        'claims_not_supported': [
            'not a foundation-model leaderboard or a LoRA comparison',
            'not a held-out-person or cross-dataset result',
            'no real-time, causal, clinical or deployment claim',
            'not a guaranteed time gap between sessions',
        ],
        'independent_audit': {
            'status': 'pass', 'people': PEOPLE,
            'checked': 'every person’s session-3 labels re-extracted and verified, the saved predictions replayed, the '
                       'session-1 scaler statistics recomputed and the ridge normal equations checked; every person’s '
                       'metrics and both cohorts’ paired bootstrap intervals reproduced exactly',
            'not_checked': 'the models were not refitted and the spectral features were not recomputed from the EEG',
        },
    }
    written_from(result, (handoff, json.dumps(release)), label)
    return result, release


# ---------------------------------------------------------------------------- WBCIC-SHU, frozen CBraMod
FM_AUDIT_VERDICT = 'pass_exact_sealed_62_participant_result'


def wbcic_cbramod(src, cpu_release):
    label = WBCIC_FM
    release, release_sha = pinned(src['release'], f'{label} release')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    decision, _ = pinned(src['releaseDecision'], f'{label} release decision')
    audit, audit_sha = pinned(src['numericalAudit'], f'{label} audit')
    root, root_sha = pinned(src['rootCheck'], f'{label} root check')
    activation, _ = pinned(src['rootActivation'], f'{label} root activation')

    require(decision['release_sha256'] == release_sha and decision['independent_result_audit_sha256'] == audit_sha
            and decision['root_check_sha256'] == root_sha, f'{label}: the decision names other bytes')
    require(decision['verdict'] == 'approved_complete_separate_cohort_aggregate_comparison'
            and decision['scientific_aggregate_release_allowed'] is True and decision['website_changed'] is False
            and all(v is True for v in decision['gates'].values()), f'{label}: the decision does not approve it')
    prov = release['provenance']
    require(prov['independent_result_audit_sha256'] == audit_sha and prov['root_aggregate_check_sha256'] == root_sha,
            f'{label}: the release names another audit or root check')
    require(prov['checkpoint_sha256'] == activation['bindings']['checkpoint_sha256'] == src['model']['checkpointSha256'],
            f'{label}: another checkpoint')
    require(prov['input_manifest_sha256'] == root['input_manifest_sha256'] == activation['bindings']['input_manifest_sha256']
            == cpu_release['provenance']['input_manifest_sha256'], f'{label}: another input manifest from the CPU release')
    require(activation['approved'] is True and activation['root_review']['verdict'] == 'approved_exact_immutable_arm',
            f'{label}: the arm was not activated')
    require(audit['verdict'] == FM_AUDIT_VERDICT and audit['integrity']['participants'] == PEOPLE
            and all(audit['integrity'][k] is True for k in ('all_stage_pointers_and_artifacts', 'numpy_predictions_recomputed',
                                                            'participant_metrics_recomputed', 'prediction_seal_predates_target_labels',
                                                            'source_only_scaler_ridge_refits'))
            and audit['pins']['cpu_independent_audit_sha256'] == cpu_release['provenance']['audit_sha256'],
            f'{label}: the independent audit did not pass or names another CPU audit')
    require(root['verdict'].startswith('pass_62') and root['auditor_result_sha256'] == audit_sha,
            f'{label}: the root check did not pass this audit')
    require(when(audit['created_at_utc']) <= when(root['created_at_utc']) <= when(release['created_at_utc'])
            == when(decision['created_at_utc']), f'{label}: an audit postdates the release')
    require(release['release_status'] == 'approved_aggregate_only' and release['target_session_new_label_budget'] == 0
            and release['source_session_labels_used'] is True and release['cross_person_zero_shot'] is False
            and release['fine_tuning_or_lora'] is False and release['model_selection_on_target_scores'] is False
            and release['comparison_on_reused_benchmark_targets'] is True and release['cohorts_not_pooled'] is True,
            f'{label}: not the frozen, reused-target, session-1-readout comparison')
    require(release['counts'] == root['counts'] and release['counts']['participants'] == PEOPLE
            and release['counts']['held_participants'] == 0, f'{label}: counts differ')
    b = release['bootstrap']
    require(b['draws'] == 10000 and b['generator'] == 'PCG64' and b['seed'] == 20261002 and b['order'] == ['2C', '3C'],
            f'{label}: another bootstrap')

    cohorts = {}
    for c, shape in WBCIC_COHORTS.items():
        n, k = shape['people'], len(shape['classes'])
        x, r = release['cohorts'][c], root['cohorts'][c]
        require(x == r, f'{label}/{c}: the release differs from the root check')
        am, ab = audit['cohorts'][c]['metrics'], audit['cohorts'][c]['paired_bootstrap']['primary']
        require(am['declared_participants'] == am['scored_participants'] == ab['defined_pairs'] == n
                and am['held_participants'] == 0, f'{label}/{c}: the audit did not score the cohort')
        close(x['cbramod_balanced_accuracy'], am['primary_complete_cohort_mean'], f'{label}/{c}: audit mean')
        close(x['accuracy'], am['accuracy_participant_mean_conditional'], f'{label}/{c}: audit accuracy')
        close(x['macro_f1'], am['macro_f1_participant_mean_conditional'], f'{label}/{c}: audit macro F1')
        for mine, theirs in ((x['cbramod_ci95'], ab['ci_95_percentile']['cbramod']),
                             (x['paired_difference_ci95'], ab['ci_95_percentile']['cbramod_minus_relative_spectral_ridge'])):
            for a, z in zip(mine, theirs):
                close(a, z, f'{label}/{c}: audit interval')
        cpu = cpu_release['cohorts'][c]['methods']['relative_spectral_ridge']['primary_balanced_accuracy_mean']
        require(x['spectral_ridge_balanced_accuracy'] == cpu, f'{label}/{c}: the spectral ridge is not the CPU release’s')
        t = cpu_release['trial_accounting'][c]
        require(x['participants'] == n and x['source_trials'] == t['source_delivered_trials']
                and x['target_trials'] == t['target_delivered_trials'], f'{label}/{c}: other people or trials')
        ba = x['cbramod_balanced_accuracy']
        close(x['paired_difference'], ba - x['spectral_ridge_balanced_accuracy'], f'{label}/{c}: paired mean')
        iv = bounded(x['paired_difference'], x['paired_difference_ci95'], f'{label}/{c}: paired', -1.0, 1.0)
        require(iv[0] > 0, f'{label}/{c}: the paired interval no longer excludes zero; the reading must be reviewed')
        require(0 <= x['accuracy'] <= 1 and 0 <= x['macro_f1'] <= 1, f'{label}/{c}: a secondary mean leaves [0,1]')
        cohorts[c] = {
            'label': shape['label'], 'classes': shape['classes'], 'people': n, 'chance_level': 1 / k,
            'source_trials': x['source_trials'], 'target_trials': x['target_trials'],
            'frozen_cbramod': {'balanced_accuracy': {'mean': ba, 'interval_95': bounded(ba, x['cbramod_ci95'],
                                                                                        f'{label}/{c}', 0.0, 1.0)},
                               'accuracy': {'mean': x['accuracy']}, 'macro_f1': {'mean': x['macro_f1']}},
            'relative_spectral_ridge': {'balanced_accuracy': {'mean': x['spectral_ridge_balanced_accuracy']},
                                        'same_as': f'{WBCIC_CPU}: the same people, trials and ridge results'},
            'paired': {'comparison': 'frozen CBraMod minus relative spectral ridge, the same people and trials',
                       'balanced_accuracy_difference': {'mean': x['paired_difference'], 'interval_95': iv},
                       'interval_excludes_zero': iv[0] > 0 or iv[1] < 0, 'people': n},
        }

    for c, shape in WBCIC_COHORTS.items():
        e = cohorts[c]
        f, d = e['frozen_cbramod']['balanced_accuracy'], e['paired']['balanced_accuracy_difference']
        stated(handoff, f'| {shape["handoff_fm"]} | {e["people"]} | '
                        f'{100 * e["relative_spectral_ridge"]["balanced_accuracy"]["mean"]:.2f}% | '
                        f'**{100 * f["mean"]:.2f}% [{100 * f["interval_95"][0]:.2f}, {100 * f["interval_95"][1]:.2f}]** | '
                        f'**{100 * d["mean"]:+.2f} percentage points [{100 * d["interval_95"][0]:.2f}, '
                        f'{100 * d["interval_95"][1]:.2f}]** |', f'{label}/{c}')
    stated(handoff, f'{100 * cohorts["2C"]["frozen_cbramod"]["accuracy"]["mean"]:.2f}% / '
                    f'{100 * cohorts["2C"]["frozen_cbramod"]["macro_f1"]["mean"]:.2f}% for two-class and '
                    f'{100 * cohorts["3C"]["frozen_cbramod"]["accuracy"]["mean"]:.2f}% / '
                    f'{100 * cohorts["3C"]["frozen_cbramod"]["macro_f1"]["mean"]:.2f}% for three-class',
           f'{label} secondary')
    model = src['model']
    require(release['attribution']['model_paper'] == model['paper']
            and release['attribution']['dataset_paper'] == 'https://doi.org/10.1038/s41597-025-04826-y',
            f'{label}: another model or dataset paper')
    stated(handoff, model['sourceRevision'], f'{label} source revision')
    stated(handoff, 'The primary model paper describes TUEG pretraining; the pinned repository lists SHU as a '
                    'downstream task.', f'{label} pretraining exposure')

    result = {
        'id': WBCIC_FM, 'dataset': 'wbcic-shu',
        'title': 'WBCIC-SHU: frozen CBraMod against the spectral ridge, session 1 to session 3',
        'question': "Can an EEG model trained on a person's earlier recording session work in a later session "
                    'without new calibration labels?',
        'model_family': 'foundation', 'foundation_model': True, 'encoder': 'frozen', 'fine_tuning': False,
        'lora': False,
        'model': {'name': model['name'], 'method_slug': 'cbramod', 'paper': model['paper'],
                  'checkpoint_sha256': model['checkpointSha256'], 'source_revision': model['sourceRevision'],
                  'readout': "a StandardScaler and RidgeClassifier fitted on each person's session 1 only"},
        'pretraining_exposure': {'status': 'not established', 'statement': model['pretrainingExposure']},
        'generalization': "the same person, a later recording session: each person's session-1 labels train the "
                          'readout. Not cross-person zero-shot decoding.',
        'sessions': {'train': 1, 'test': 3, 'unused': 2, 'target_session_labels': 0,
                     'unit': 'recording-session ordinal',
                     'time_between': 'not stated: the ordinals are not a guaranteed time gap or distinct calendar days'},
        'reused_targets': 'The spectral ridge results existed before this arm was frozen: a comparative follow-up on '
                          'the same test trials, not a fresh untouched test set.',
        'metric': 'balanced_accuracy',
        'weighting': 'participant-equal: each person counts once in a cohort mean, and the two cohorts are never '
                     'averaged together',
        'cohorts': cohorts,
        'method': {
            'adapter': 'resampled from 250 Hz to 200 Hz (polyphase, 4/5) and zero-padded to 800 samples; each trial '
                       'and channel centred and divided by its own standard deviation, with no epsilon; a whole person '
                       'would be rejected on invalid variance, and none was',
            'encoder': 'CBraMod in evaluation mode, every weight frozen, its output projection replaced by identity; '
                       'the four temporal patch embeddings averaged: 58 × 200 = 11,600 values per trial, float32',
            'readout': "a separate StandardScaler and RidgeClassifier fitted on each person's session 1 only: alpha 1, "
                       'SVD solver, intercept, no class weights, no search',
            'not_done': 'no backbone training, LoRA, target-session calibration or adaptation',
            'scoring': 'all 62 sets of predictions were sealed before a separate scorer opened the ordered session-3 '
                       'labels; earlier schema checks had inspected label domains and counts',
        },
        'uncertainty': {
            'kind': 'pointwise 95% percentile interval from 10,000 paired participant bootstrap draws within each '
                    'cohort (PCG64, seed 20261002, two-class then three-class)',
            'paired': 'the difference intervals resample matched per-person differences, not the gap between two '
                      'separately estimated intervals',
            'conditional_on': 'the fixed models and predictions, without refitting: model-selection, '
                              'preprocessing-selection and pretraining-overlap uncertainty are not included',
        },
        'reading': 'In both cohorts frozen CBraMod with a session-1 ridge readout is above the spectral ridge, with '
                   'paired intervals above zero. This compares two fixed pipelines; it does not show that pretraining '
                   'caused the difference.',
        'limitations': [
            'A fixed pipeline comparison on reused benchmark targets: the spectral ridge results existed before this '
            'arm was frozen. A comparative follow-up, not a fresh untouched test set or an independent replication.',
            'No claim that pretraining caused the difference: there is no matched random-weight control, the feature '
            'spaces, their size and the preprocessing differ, and the same ridge alpha does not equalize '
            'regularization across them.',
            'A dimensionless adapter, not a native-amplitude replication: physical amplitude is unresolved, and '
            'upstream benchmark numbers are not reproduced here.',
            'Pretraining exposure is not established for this checkpoint; nothing here certifies that WBCIC-SHU was '
            'unseen in pretraining.',
            'The original six fixed-count holds stay recorded; three affected sessions enter under the reviewed '
            'variable-N rule, without filling, truncation or performance-based exclusion. The cause of the missing '
            'trials is unknown.',
            'Offline evidence only: whole-epoch normalization and the publisher’s offline derivative establish no '
            'causal, online, clinical or closed-loop performance. No LoRA or calibration-budget comparison was run in '
            'this arm.',
            'Same-person session transfer: each person’s session-1 labels are required. Not cross-person zero-shot '
            'decoding and not a label-free decoder.',
            'The three-class cohort is small.',
            'Audit scope: the independent checker refitted the session-1 readouts and recomputed predictions, metrics '
            'and intervals from the saved embeddings; the encoder was not rerun on all the EEG. An earlier fixed '
            'eight-trial adapter pilot was independently replayed and matched exactly.',
        ],
        'release_limits': release['limitations'],
        'claims_not_supported': [
            'not evidence that pretraining caused the difference',
            'not cross-person zero-shot decoding or a label-free decoder',
            'no certified unseen pretraining data',
            'not a replication of upstream benchmark numbers',
            'no online, causal, clinical or closed-loop claim',
            'no LoRA or calibration-budget result',
        ],
        'independent_audit': {
            'status': 'pass', 'people': PEOPLE,
            'checked': 'every artifact chain, the session-1 and session-3 label-stream bindings and the order of '
                       'prediction before scoring; the session-1 readouts refitted and the predictions, metrics and '
                       'paired intervals recomputed from the saved embeddings; then a separate root check rehashed the '
                       'saved arrays and recomputed the metrics and paired intervals',
            'not_checked': 'the full encoder was not rerun on all the EEG during the result audit',
        },
    }
    written_from(result, (handoff, json.dumps(release)), label)
    return result


# ---------------------------------------------------------------------------- longitudinal RSVP
VISITS = (('Day_7', 'Day 7', 7), ('Day_80', 'Day 80', 80), ('Day_200', 'Day 200', 200))
RSVP_PEOPLE = 15
RSVP_METRICS = {'auroc': (0.0, 1.0), 'average_precision': (0.0, 1.0), 'log_loss': (0.0, math.inf),
                'brier_score': (0.0, 1.0), 'ece_10_equal_width': (0.0, 1.0)}


def rsvp(src):
    label = RSVP
    release, release_sha = pinned(src['release'], f'{label} release')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    decision, _ = pinned(src['releaseDecision'], f'{label} release decision')
    prep, prep_sha = pinned(src['preparationAudit'], f'{label} preparation audit')
    fit, fit_sha = pinned(src['predictionAudit'], f'{label} prediction audit')
    score, score_sha = pinned(src['numericalAudit'], f'{label} metric audit')
    final, _ = pinned(src['finalCheck'], f'{label} final check')

    require(decision['export_sha256'] == release_sha and decision['preparation_audit_sha256'] == prep_sha
            and decision['prediction_audit_sha256'] == fit_sha and decision['metric_audit_sha256'] == score_sha,
            f'{label}: the decision names other bytes')
    require(decision['verdict'] == 'approve_audited_aggregate_website_handoff' and decision['website_edited'] is False,
            f'{label}: the decision does not approve it')
    candidate = decision['accepted_candidate_sha256']
    require(score['candidate_sha256'] == candidate == release['provenance']['candidate_sha256'],
            f'{label}: the metric audit checked another aggregate')
    p = release['provenance']
    require(p['preparation_audit_sha256'] == prep_sha and p['prediction_replay_audit_sha256'] == fit_sha
            and p['independent_metric_audit_sha256'] == score_sha, f'{label}: the release names other audits')
    require(score['verdict'] == 'pass_all_45_saved_prediction_metrics_and_aggregate_recomputation'
            and score['participants'] == RSVP_PEOPLE and score['prediction_slots'] == 3 * RSVP_PEOPLE
            and score['absolute_tolerance'] == 1e-12 and score['model_refit'] is False,
            f'{label}: the metric audit did not pass')
    require(fit['verdict'] == 'pass_independent_saved_fit_predictions' and fit['comparison']['successful_participants']
            == RSVP_PEOPLE and fit['comparison']['scientific_holds'] == 0
            and fit['comparison']['compared_predictions'] == score['scored_target_events']
            and 0 <= fit['comparison']['maximum_absolute_difference'] < fit['atol'], f'{label}: the prediction replay')
    require(prep['verdict'] == 'pass_saved_production_provenance_arrays_and_fit_interfaces'
            and prep['totals']['participants'] == RSVP_PEOPLE and prep['totals']['invalid_events'] == 0
            and prep['totals']['valid_events'] == prep['totals']['structural_events']
            and prep['target_label_vectors_loaded'] is False, f'{label}: the preparation audit')
    require(final['verdict'] == 'pass_exact_audited_aggregate_website_handoff' and final['findings'] in ([], None)
            and all(v == 'pass' for v in final['checks'].values()), f'{label}: the final check did not pass')
    fp = final['file_pins']
    require(fp['results/rsvp-longitudinal-retention-cpu-v2-website-release.json'] == release_sha
            and fp['RSVP Longitudinal Retention Benchmark Website Handoff.md'] == src['handoff']['sha256']
            and fp['review/rsvp-longitudinal-retention-root-release-decision-v2.json'] == src['releaseDecision']['sha256'],
            f'{label}: the final check pins other release, handoff or decision bytes')
    require(when(score['at_utc']) <= when(decision['at_utc']) == when(release['released_at_utc'])
            <= when(final['reviewed_at_utc']), f'{label}: the audit, decision, release and check are out of order')
    require(release['release_status'] == 'audited_aggregate_only'
            and all(v is False for v in release['privacy'].values()), f'{label}: not an aggregate-only release')
    ds, model = release['dataset'], release['model']
    require(ds['doi'] == '10.6084/m9.figshare.27201003.v1' and ds['license_record'] == 'CC0' and ds['cohort'] == 'Group A'
            and ds['planned_participants'] == RSVP_PEOPLE, f'{label}: another dataset, licence or cohort')
    require(model['foundation_model'] is False and model['target_blocks'] == [2, 3, 4]
            and model['adaptation'] == 'none on target visits', f'{label}: not the fixed first-visit baseline')

    visits, events = [], 0
    for key, name, day in VISITS:
        v = release['visits'][key]
        require(v['planned_n'] == v['source_model_eligible_n'] == v['visit_scored_n'] == RSVP_PEOPLE
                and v['hold_or_undefined_reason_counts'] == {}, f'{label}/{key}: not every person scored')
        require(all(v['metric_defined_n'][mk] == RSVP_PEOPLE for mk in RSVP_METRICS), f'{label}/{key}: an undefined metric')
        c = v['counts']
        require(c['participants_with_counts'] == RSVP_PEOPLE and c['signal_valid'] == c['structural_eligible']
                and c['signal_invalid'] == 0 and all(x == 0 for x in c['invalid_reason_counts'].values())
                and c['target'] + c['non_target'] == c['structural_eligible'], f'{label}/{key}: the counts do not add up')
        require(c['delivered'] is None and c['delivered_unavailable_reason'], f'{label}/{key}: a null became a number')
        mt = v['metrics']
        for mk in RSVP_METRICS:
            require(mt[mk]['defined_n'] == RSVP_PEOPLE, f'{label}/{key}/{mk}: not defined for every person')
            lo_b, hi_b = RSVP_METRICS[mk]
            require(lo_b <= mt[mk]['mean'] <= hi_b, f'{label}/{key}/{mk}: the mean leaves its range')
        auc = mt['auroc']['mean']
        fc, bs = v['full_cohort_primary'], release['bootstrap'][key]
        require(fc['status'] == 'complete' and fc['mean'] == auc == bs['point'] == v['conditional_descriptive']['mean']
                and v['conditional_descriptive']['denominator'] == bs['n'] == RSVP_PEOPLE,
                f'{label}/{key}: the primary AUROC differs between blocks')
        iv = bounded(auc, [fc['interval']['q025'], fc['interval']['q975']], f'{label}/{key}', 0.0, 1.0)
        require(iv == [bs['q025'], bs['q975']], f'{label}/{key}: two intervals for one mean')
        require(iv[0] > 0.5, f'{label}/{key}: the AUROC interval reaches 0.5; the reading must be reviewed')
        events += c['structural_eligible']
        visits.append({
            'visit': name, 'nominal_day': day, 'people': RSVP_PEOPLE,
            'events': c['structural_eligible'], 'target_events': c['target'], 'non_target_events': c['non_target'],
            'target_share': c['target'] / c['structural_eligible'], 'signal_invalid_events': c['signal_invalid'],
            'delivered_events': None,
            'delivered_events_note': 'not available: the protected scoring interface does not report a delivered-event '
                                     'count, so it stays null, never zero',
            'auroc': {'mean': auc, 'interval_95': iv},
            'average_precision': {'mean': mt['average_precision']['mean']},
            'log_loss': {'mean': mt['log_loss']['mean']},
            'brier_score': {'mean': mt['brier_score']['mean']},
            'ece_10_bins': {'mean': mt['ece_10_equal_width']['mean']},
        })
    require(events == score['scored_target_events'], f'{label}: the visit events are not the audited scored events')
    require(prep['totals']['structural_events'] - events == 4 * 24000,
            f'{label}: the first-visit events are not 72,000 fitting plus 24,000 calibration events')

    ct = release['contrast']
    require(ct['planned_n'] == ct['common_defined_n'] == RSVP_PEOPLE and ct['full_cohort']['status'] == 'complete',
            f'{label}: the contrast does not cover every person')
    d = ct['full_cohort']['mean']
    close(d, visits[2]['auroc']['mean'] - visits[0]['auroc']['mean'], f'{label}: the paired mean')
    require(d == ct['conditional_descriptive']['mean'] == release['bootstrap']['Day_200_minus_Day_7']['point'],
            f'{label}: two contrast means')
    civ = bounded(d, [ct['full_cohort']['interval']['q025'], ct['full_cohort']['interval']['q975']],
                  f'{label}: contrast', -1.0, 1.0)
    bb = release['bootstrap']['Day_200_minus_Day_7']
    require(civ == [bb['q025'], bb['q975']] and bb['n'] == RSVP_PEOPLE, f'{label}: two contrast intervals')
    require(civ[1] < 0, f'{label}: the contrast interval no longer lies below zero; the reading must be reviewed')
    k = ct['decline_at_most_minus_0_05_count']
    require(count(k) and 0 <= k <= RSVP_PEOPLE, f'{label}: the decline count is not a whole number of people')
    close(ct['decline_at_most_minus_0_05_fraction'], k / RSVP_PEOPLE, f'{label}: the decline share')
    require(release['units']['contrast'] == 'absolute_AUROC_difference', f'{label}: another contrast unit')

    # Last: the figures the pages print are the ones the pinned handoff states.
    f4 = lambda x: f'{x:.4f}'
    for v in visits:
        stated(handoff, f'| {v["visit"]} | {v["people"]} | {f4(v["auroc"]["mean"])} '
                        f'({f4(v["auroc"]["interval_95"][0])}–{f4(v["auroc"]["interval_95"][1])}) | '
                        f'{f4(v["average_precision"]["mean"])} | {f4(v["log_loss"]["mean"])} | '
                        f'{f4(v["brier_score"]["mean"])} | {f4(v["ece_10_bins"]["mean"])} |', f'{label}/{v["visit"]}')
    sg = lambda x: f'{x:.4f}'.replace('-', '−')
    stated(handoff, f'**{sg(d)}**', f'{label} contrast')
    stated(handoff, f'**[{sg(civ[0])}, {sg(civ[1])}]**', f'{label} contrast interval')
    stated(handoff, f'Six of {RSVP_PEOPLE} participants ({100 * k / RSVP_PEOPLE:.0f}%)', f'{label} declines')
    require(k == 6, f'{label}: the handoff says six people declined by 0.05 or more')
    stated(handoff, ', '.join(f'{v["target_events"]:,} / {v["events"]:,}' for v in visits[:1]) + ' events at Day 7',
           f'{label} targets')
    for v in visits[1:]:
        stated(handoff, f'{v["target_events"]:,} / {v["events"]:,} at {v["visit"]}', f'{label} targets')
    for n in (f'{3 * 24000:,} source-fit events', '24,000 source-calibration events', f'{events:,} held-out scoring events',
              f'{prep["totals"]["blocks"]} selected blocks', f'All {prep["totals"]["structural_events"]:,} selected events'):
        stated(handoff, n, f'{label} design')

    result = {
        'id': RSVP, 'dataset': 'longitudinal-rsvp',
        'title': 'Longitudinal RSVP: a first-visit decoder at later visits',
        'question': 'How well does an EEG decoder trained at the first visit work at later visits without '
                    'recalibration?',
        'subtitle': 'Same-person, offline RSVP classification; publisher nominal visit labels; no target-session '
                    'adaptation.',
        'model': {'label': 'Normalized ERP features + logistic/Platt (CPU baseline)', 'kind': 'CPU baseline'},
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'generalization': 'the same person at later visits: each person’s first-visit labels train and calibrate '
                          'their own decoder. Not cross-person zero-shot decoding.',
        'cohort': {'group': 'A', 'people': RSVP_PEOPLE, 'group_b': 'not used'},
        'visits': visits,
        'contrast': {
            'comparison': 'Day 200 minus Day 7 AUROC, the same people',
            'auroc_difference': {'mean': d, 'interval_95': civ},
            'interval_excludes_zero': civ[0] > 0 or civ[1] < 0, 'people': RSVP_PEOPLE,
            'people_declined_by_0_05_or_more': k, 'share_declined_by_0_05_or_more': k / RSVP_PEOPLE,
        },
        'design': {
            'first_visit_fit_events': 3 * 24000, 'first_visit_calibration_events': 24000, 'scored_events': events,
            'blocks': prep['totals']['blocks'], 'selected_events': prep['totals']['structural_events'],
            'events_removed_for_signal': prep['totals']['invalid_events'],
            'note': 'structural and valid event counts; overlapping events stay inside their original blocks',
        },
        'units': {
            'auroc': 'a ranking measure from 0 to 1, not classification accuracy',
            'average_precision': 'from 0 to 1, not precision at a chosen threshold',
            'log_loss': 'per event, natural log',
            'brier_score': 'mean squared error of the calibrated probability, 0 to 1',
            'ece_10_bins': 'expected calibration error over 10 equal-width bins, 0 to 1',
            'contrast': 'absolute difference in AUROC',
        },
        'label_coding': 'The paper and the publisher’s sample script code 1 as non-target and 2 as target; the '
                        'release’s Trigger.txt reverses these roles. The paper and script were followed, a precedence '
                        'decided before modeling, and the contradiction stays visible.',
        'method': {
            'split': 'per person, nominal Day 1 blocks 1–3 fit the classifier and block 4 fits Platt calibration; the '
                     'later visits are scored on blocks 2–4, and their block 1 stays reserved',
            'events': '57 EEG channels, −200 to +700 ms around each event, baseline-normalized per event and channel, '
                      'then six 100 ms averages from +100 to +700 ms: 342 values per event, float64; the event column is '
                      'not a feature',
            'classifier': 'a StandardScaler fitted on Day 1 only, then a fixed L2 logistic regression (C = 1, lbfgs, '
                          'at most 2,000 iterations, tolerance 1e-6), and the same fixed logistic form for Platt '
                          'calibration',
            'selection': 'none: no hyperparameter search, target-label calibration, fine-tuning or LoRA; all 15 '
                         'first-visit fits succeeded and all 45 visit predictions were sealed before scoring',
            'weighting': 'every cohort mean weights people equally; counts are event totals',
        },
        'uncertainty': {
            'kind': 'pointwise 95% percentile interval from 10,000 participant bootstrap resamples (PCG64, seed '
                    '20261002, fixed visit and contrast order)',
            'conditional_on': 'the fixed predictions, with no refitting: model-fitting, dataset-selection and '
                              'protocol-selection uncertainty are not included, and there is no multiple-comparison '
                              'adjustment',
            'resampled': 'participants only; splits use whole physical blocks',
        },
        'reading': 'AUROC stays well above chance at every later visit and is lower at Day 200 than at Day 7, with a '
                   'paired interval below zero. Average precision falls too, and targets are rare. This describes this '
                   'cohort and this decoder; it does not show that elapsed time caused the change.',
        'limitations': [
            'Day 7, Day 80 and Day 200 are the publisher’s nominal visit labels, not verified participant-specific '
            'elapsed days.',
            'Same person, one decoder per person: each person’s first-visit labels are required. Not cross-person '
            'zero-shot decoding.',
            'A 15-person observational cohort and one fixed offline baseline: not a clinical diagnostic result, a '
            'real-time deployment validation, evidence of causality or evidence that one foundation model is best.',
            'Targets are rare, about 2.5% of the events at every visit. AUROC is a ranking measure and average '
            'precision is not precision at a chosen threshold: a high AUROC is not a high precision or an online '
            'selection success rate. The target share is descriptive, not a comparator arm.',
            'Event roles and target labels had been inspected during quality checks. They did not enter normalization, '
            'model fitting or calibration, prediction, or any hyperparameter, threshold, abstention or retry decision.',
            'A delivered-event count is not available from the protected scoring interface and stays null.',
            'Audit scope: the saved predictions were independently reconstructed and every visit metric, interval and '
            'the contrast independently recomputed; the full production feature extraction was not independently '
            'repeated.',
        ],
        'release_limits': release['limits'],
        'claims_not_supported': [
            'not cross-person zero-shot generalization',
            'no clinical, real-time or online claim',
            'no causal effect of elapsed time',
            'no fitted continuous decay curve',
            'not a foundation-model ranking',
        ],
        'independent_audit': {
            'status': 'pass', 'people': RSVP_PEOPLE,
            'checked': 'the saved preparation provenance, event identities, masks and features of every selected '
                       'block; all saved predictions reconstructed from the saved scalers and models (largest '
                       'difference 1.11e-16); all 45 visit metrics, the person-level summaries, the intervals and the '
                       'contrast recomputed at an absolute tolerance of 1e-12',
            'not_checked': 'the full production EEG feature extraction was not independently repeated',
        },
    }
    written_from(result, (handoff, json.dumps(release)), label)
    return result


# ---------------------------------------------------------------------------- Forenzo
FORENZO_COHORTS = {'Main': 14, 'Transfer Learning': 14}
FORENZO_ADMITTED = {'Main': 9, 'Transfer Learning': 14}
FORENZO_ARMS = {
    'historical_decoder_velocity_imitation': (
        'Historical decoder velocity',
        "imitates the publisher's stored output of the decoder used at recording time; not intended hand motion "
        'or intended control'),
    'constructed_raw_target_displacement_proxy': (
        'Constructed displacement proxy',
        'a separately fitted target-position-minus-cursor-position proxy in publisher screen coordinates'),
}
FORENZO_METHODS = {'ridge': ('ridge', 'Spectral ridge'), 'source_mean_comparator': ('source_mean', 'Source-mean comparator')}
PRIMARY = 'joint_source_sd_normalized_rmse'
SECONDARY = {  # key -> (range, unit)
    'raw_rmse_x': ((0.0, math.inf), "the response's stored units, horizontal axis"),
    'raw_rmse_y': ((0.0, math.inf), "the response's stored units, vertical axis"),
    'r2_x': ((-math.inf, 1.0), 'coefficient of determination, horizontal axis'),
    'r2_y': ((-math.inf, 1.0), 'coefficient of determination, vertical axis'),
    'pearson_x': ((-1.0, 1.0), 'Pearson correlation, horizontal axis'),
    'pearson_y': ((-1.0, 1.0), 'Pearson correlation, vertical axis'),
}
HOLD_REASONS = {  # the independent review's wording -> what the pages may print
    'pre_metadata_archive_structure: decoder-local run allocation differs from documented contract':
        'the decoder-local run allocation differs from the documented contract',
    'pre_metadata_archive_structure: each session requires one Chance R01 member':
        'a session lacks its required Chance R01 record',
    'response boundary geometry differs':
        'the sample-boundary geometry differs; its exact numeric cause was not independently reconstructed',
}
TAIL_RATIO = 10.0   # the ridge's mean at least ten times its median, for the "severe upper tail" reading


def forenzo(src):
    label = FORENZO
    release, release_sha = pinned(src['release'], f'{label} release')
    handoff = pinned_text(src['handoff'], f'{label} handoff')
    decision, _ = pinned(src['releaseDecision'], f'{label} release decision')
    review, review_sha = pinned(src['independentReview'], f'{label} independent review')

    require(decision['release_export']['sha256'] == release_sha and decision['handoff']['sha256'] == src['handoff']['sha256']
            and decision['independent_review']['sha256'] == review_sha, f'{label}: the decision names other bytes')
    require(decision['verdict'] == 'approve_audited_conditional_cohort_aggregate_negative_result_for_website_handoff'
            and decision['release_approved'] is True and decision['website_edited_or_published'] is False
            and decision['scientific_holds_preserved'] == 5 and decision['release_is_not_raw_data_permission'] is True,
            f'{label}: the decision does not approve it')
    rr = release['release_review']
    require(rr['independent_review_sha256'] == review_sha and rr['handoff_sha256'] == src['handoff']['sha256']
            and rr['reviewed_candidate_sha256'] == decision['candidate_sha256'] and rr['root_accepted_at_utc']
            == decision['approved_at_utc'], f'{label}: the release names another review, handoff or candidate')
    require(release['provenance'] == decision['private_provenance'], f'{label}: release and decision provenance differ')
    require(review['verdict'] == 'pass_release_eligible_cohort_aggregate_negative_result_pending_separate_root_acceptance'
            and review['release_eligible'] is True and review['blocking_findings'] == [], f'{label}: the review did not pass')
    vf = review['verification']
    require(vf['candidate_cohorts_exactly_equal_private_aggregate_and_independent_aggregate_replay'] is True
            and vf['candidate_bootstrap_exactly_equal_private_aggregate'] is True
            and vf['independent_aggregate_maximum_absolute_difference'] == 0 and vf['receipt_sha256_mismatches'] == [],
            f'{label}: the review did not match the aggregate')
    require(when(review['reviewed_at_utc']) <= when(decision['approved_at_utc']), f'{label}: the review postdates the decision')
    require(release['release_approved'] is True and release['participant_level_values_public'] is False
            and release['private_payloads_included'] is False and release['cohorts_combined'] is False
            and release['velocity_displacement_combined'] is False, f'{label}: not an aggregate-only, unpooled release')
    pm = release['primary_metric']
    require(pm['id'] == PRIMARY and pm['lower_is_better'] is True, f'{label}: another primary metric')
    b = release['bootstrap']
    require(b['replicates'] == 10000 and b['seed'] == 20261002 and b['generator'] == 'numpy.random.PCG64',
            f'{label}: another bootstrap')
    ds = release['dataset']
    require(ds['doi'] == '10.1184/R1/25360300.v1' and ds['license']['name'] == 'CC BY 4.0'
            and ds['paper_doi'] == '10.1093/pnasnexus/pgae145', f'{label}: another dataset or licence')
    cov = review['coverage']
    require(sum(cov['original_hold_reasons'].values()) == decision['scientific_holds_preserved']
            and set(cov['original_hold_reasons']) == set(HOLD_REASONS), f'{label}: other hold reasons')

    def summary(block, n, where, rng):
        if block.get('summary', 'present') is None:
            require(block['n'] == 0 and block['reason'] in ('no_defined_values', 'no_defined_pairs'),
                    f'{where}: a null without its reason')
            return {'mean': None, 'interval_95': None, 'records_defined': 0,
                    'undefined': 'a constant prediction has no correlation: null, never zero'}
        require(block['n'] == n, f'{where}: not defined for every admitted record')
        return {'mean': block['mean'], 'interval_95': bounded(block['mean'], block['bootstrap_mean_ci95'], where, *rng),
                'records_defined': n}

    cohorts, secret = {}, []
    for c, candidates in FORENZO_COHORTS.items():
        x, rc = release['cohorts'][c], cov[c]
        n = FORENZO_ADMITTED[c]
        held = candidates - n
        require(x['candidate_participants'] == rc['candidates'] == candidates and x['admitted_participants']
                == x['feature_pass_participants'] == rc['admitted'] == rc['fit_prediction_score_and_independent_audit_pass']
                == n and rc['original_metadata_holds'] == held, f'{label}/{c}: coverage differs from the review')
        arms = {}
        for arm, (name, desc) in FORENZO_ARMS.items():
            a = x['arms'][arm]
            where = f'{label}/{c}/{arm}'
            require(a['arm_fit_pass_participants'] == a['prediction_pass_participants'] == a['score_pass_participants'] == n,
                    f'{where}: not every admitted record scored')
            require(a['failure_reasons'] == ({'upstream_manifest_hold:accepted metadata manifest held participant': held}
                                             if held else {}), f'{where}: other failures than the upstream holds')
            require(a['conditional_on_score_pass'] is bool(held), f'{where}: the conditional flag')
            require(a['rows'] == rc['target_rows_per_arm'] and a['trials'] == rc['target_trials_per_arm']
                    and a['runs'] == rc['target_runs_per_arm'], f'{where}: target coverage differs from the review')
            out = {'label': name, 'records': n, 'target_rows': a['rows'], 'target_trials': a['trials'],
                   'target_runs': a['runs']}
            for mkey, (okey, mlabel) in FORENZO_METHODS.items():
                mt = a['methods'][mkey]
                prim = mt[PRIMARY]
                require(prim['n'] == n, f'{where}/{mkey}: primary not defined for every admitted record')
                entry = {'label': mlabel,
                         'primary': {'mean': prim['mean'],
                                     'interval_95': bounded(prim['mean'], prim['bootstrap_mean_ci95'],
                                                            f'{where}/{mkey}', 0.0)}}
                if mkey == 'ridge':
                    entry['primary']['median'] = prim['median']
                    require(prim['median'] > 0, f'{where}: a ridge median that is not an error')
                entry['secondary'] = {s: summary(mt[s], n, f'{where}/{mkey}/{s}', rng)
                                      for s, (rng, _) in SECONDARY.items()}
                secret += [prim[k] for k in ('minimum', 'p10', 'p90')]
                if mkey != 'ridge':
                    secret.append(prim['median'])
                for s in SECONDARY:
                    if mt[s].get('summary', 'present') is not None:
                        secret += [mt[s][k] for k in ('minimum', 'median', 'p10', 'p90')]
                out[okey] = entry
            pr = a['paired_ridge_minus_source_mean'][PRIMARY]
            require(pr['n'] == n, f'{where}: the paired difference does not cover every record')
            close(pr['mean'], out['ridge']['primary']['mean'] - out['source_mean']['primary']['mean'],
                  f'{where}: the paired mean', 1e-9)
            piv = bounded(pr['mean'], pr['bootstrap_mean_ci95'], f'{where}: paired')
            # The every-record statement: the smallest paired difference is above zero, so every admitted record
            # did worse with the ridge. The minimum itself stays private; only the count it implies is published.
            require(pr['minimum'] > 0, f'{where}: a record where the ridge did not do worse; the reading must be reviewed')
            secret += [pr[k] for k in ('minimum', 'median', 'p10', 'p90')]
            out['paired'] = {'comparison': 'spectral ridge minus source-mean comparator, the same records; positive '
                                           'means the ridge has the larger error',
                             'primary_difference': {'mean': pr['mean'], 'interval_95': piv},
                             'interval_excludes_zero': piv[0] > 0 or piv[1] < 0,
                             'records_with_higher_ridge_error': n, 'records': n}
            ratio = out['ridge']['primary']['mean'] / out['ridge']['primary']['median']
            require(ratio >= TAIL_RATIO, f'{where}: the mean is no longer far above the median; review the tail reading')
            out['upper_tail'] = {
                'ridge_mean_over_median': ratio,
                'reading': "The ridge's mean error is many times its median: a few records carry very large errors. "
                           'No scored record was removed, clipped or winsorized, and the cause of the extreme errors is '
                           'not established.',
            }
            arms[arm] = out
        reasons = [{'reason': HOLD_REASONS[r], 'records': k} for r, k in cov['original_hold_reasons'].items()] if held else []
        cohorts[c] = {
            'publisher_cohort_name': c, 'candidate_records': candidates, 'admitted_records': n,
            'held_before_scoring': held, 'hold_reasons': reasons,
            'conditional_on_admitted_records': bool(held),
            'arms': arms,
        }
    require(sum(r['records'] for r in cohorts['Main']['hold_reasons']) == cohorts['Main']['held_before_scoring'],
            f'{label}: the hold reasons do not add up to the holds')
    rows = sum(cohorts[c]['arms']['historical_decoder_velocity_imitation']['target_rows'] for c in cohorts)
    require(rows == release['held_out_rows_per_arm'] == cov['target_rows_per_separate_arm']
            and release['response_rows_removed'] == cov['response_rows_removed'] == 0
            and cov['successful_response_fit_prediction_score_arms'] == 2 * sum(FORENZO_ADMITTED.values()),
            f'{label}: rows or fits do not add up')
    for c in cohorts:
        a0, a1 = (cohorts[c]['arms'][k] for k in FORENZO_ARMS)
        require(a0['target_rows'] == a1['target_rows'], f'{label}/{c}: the two arms score different rows')

    # Last: the figures the pages print are the ones the pinned handoff states.
    f4 = lambda x: f'{x:.4f}'
    for c in cohorts:
        for arm, (name, _) in FORENZO_ARMS.items():
            e = cohorts[c]['arms'][arm]
            p = e['paired']['primary_difference']
            stated(handoff, f'| {c} | {name} | {e["records"]} | {f4(e["ridge"]["primary"]["mean"])} | '
                            f'{f4(e["ridge"]["primary"]["median"])} | {f4(e["source_mean"]["primary"]["mean"])} | '
                            f'{f4(p["mean"])} [{f4(p["interval_95"][0])}, {f4(p["interval_95"][1])}] |', f'{label}/{c}/{arm}')
    m, t = cohorts['Main']['arms'], cohorts['Transfer Learning']['arms']
    mv, tv = m['historical_decoder_velocity_imitation'], t['historical_decoder_velocity_imitation']
    stated(handoff, f'{mv["target_rows"]:,} rows, {mv["target_trials"]} trials and {mv["target_runs"]} runs for Main, '
                    f'and {tv["target_rows"]:,} rows, {tv["target_trials"]} trials and {tv["target_runs"]} runs for '
                    'Transfer Learning', f'{label} coverage')
    stated(handoff, f'{rows:,} target feature rows', f'{label} rows')
    stated(handoff, f'{cov["admitted_source_target_members"]} admitted source/target members produced '
                    f'{cov["total_source_target_feature_rows"]:,} feature rows', f'{label} members')
    stated(handoff, 'Main includes 9 of 14 candidate records; Transfer Learning includes 14 of 14.', f'{label} admitted')

    result = {
        'id': FORENZO, 'dataset': 'forenzo-continuous-tracking',
        'title': 'Continuous cursor tracking: a fixed decoder from the earliest to the latest session',
        'question': 'Can a fixed EEG decoder trained in one session outperform a constant baseline in a later '
                    'session?',
        'label': 'Offline, same-person, no target-session adaptation',
        'kind': 'negative result',
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'models': {'ridge': 'source-normalized spectral features and a ridge regression (alpha 1, Cholesky), a '
                            'fixed CPU baseline',
                   'source_mean': "the source session's response mean, repeated for every target row"},
        'arms': {arm: {'label': name, 'description': desc} for arm, (name, desc) in FORENZO_ARMS.items()},
        'primary_metric': {
            'id': PRIMARY, 'name': 'Joint source-SD-normalized RMSE', 'lower_is_better': True,
            'unit': 'dimensionless: errors divided by the source session’s response standard deviation; an error, '
                    'not a percentage or a classification accuracy',
            'aggregation': 'each trial averages the normalized squared errors over its eligible rows and both axes '
                           'before the square root; a record averages its target trials equally; a cohort mean weights '
                           'records equally',
        },
        'secondary_metrics': {s: unit for s, (_, unit) in SECONDARY.items()},
        'cohorts': cohorts,
        'coverage': {
            'candidate_records': sum(FORENZO_COHORTS.values()), 'admitted_records': sum(FORENZO_ADMITTED.values()),
            'counting_unit': 'cohort records, not proven unique people',
            'target_rows_per_arm': rows, 'response_rows_removed': release['response_rows_removed'],
            'response_fits': cov['successful_response_fit_prediction_score_arms'],
            'source_target_members': cov['admitted_source_target_members'],
            'input_rows': cov['total_source_target_feature_rows'],
            'note': 'the same target rows support both response arms: two outcomes do not double the independent '
                    'sample',
        },
        'cohort_name_note': 'Transfer Learning is the publisher’s name for how that cohort’s data were collected; no '
                            'transfer-learning model was trained here.',
        'method': {
            'split': 'per admitted record, every eligible non-chance run of the earliest complete recorded session '
                     'trains the model and every eligible run of the latest complete recorded session is the target; '
                     'the sessions are disjoint, and no target label enters fitting, normalization, hyperparameters or '
                     'adaptation',
            'signal': '62 channels at 1,000 Hz, already 0.1–200 Hz band-pass and 60 Hz notch filtered by the '
                        'publisher; five bands, 4–8, 8–12, 12–16, 16–24 and 24–30 Hz, through a 1001-tap Hamming FIR '
                        'reset each trial; the preceding 1,000 filtered power samples averaged, as channel-relative log '
                        'band power with a floor of 1e-12: 310 values per row',
            'timing': 'each row uses a trial-contained 2-second past window and responses step every 40 ms; '
                      'overlapping windows stay inside whole sessions and are never split at random',
            'models': 'per response arm, a StandardScaler and a response scaling fitted on the source session only, '
                      'then Ridge (alpha 1, intercept, Cholesky solver); the comparator repeats the source response '
                      'mean; no tuning, LoRA, target-session calibration or foundation-model inference',
            'scoring': 'every target prediction was sealed before the protected target responses were scored',
        },
        'uncertainty': {
            'kind': 'pointwise 95% percentile interval from 10,000 within-cohort participant bootstrap resamples '
                    '(PCG64, seed 20261002) with paired method draws',
            'conditional_on': 'the fixed predictions: model-refitting, dataset-selection and protocol-selection '
                              'uncertainty are not included; Main is conditional on its admitted records',
        },
        'reading': 'A negative result. In both cohorts and both response arms the spectral ridge has a higher overall '
                   'primary error than the source-mean comparator for every admitted record, and its mean error is far '
                   'above its median: a severe upper tail. A simple constant baseline exposes the failure.',
        'limitations': [
            'The every-record statement is about overall primary error. It does not extend to every recorded-decoder '
            'stratum or to the secondary metrics.',
            'Offline, the same person, whole sessions, no target labels: not online control quality, intended-motion '
            'or intention decoding, clinical validation, a foundation-model ranking, LoRA or target adaptation.',
            'Velocity is the publisher’s stored historical decoder output, not intended hand motion or intended '
            'control; displacement is a separately fitted target-minus-cursor proxy in publisher screen coordinates. '
            'The two outcomes are never combined, and their magnitudes are not compared as if they measured the same '
            'thing.',
            'Main uses 9 of 14 candidate records and is conditional on that admitted subset; five metadata holds '
            'decided before scoring stay recorded. Transfer Learning uses 14 of 14. Records are counted, not proven '
            'unique people, and the two cohorts are never pooled.',
            'The cause of the extreme errors is not established: feature distribution shift, scaling sensitivity or '
            'something else. No scored record was removed, clipped or winsorized. A source-only stability diagnostic '
            'would be a new, separately frozen analysis, not a revision of these scores.',
            'The same target rows support both response arms, so two outcomes do not double the independent sample; '
            'overlapping windows do not enlarge it either.',
            'Session, practice, speed and the historical decoder in use are confounded, and the recorded decoder '
            'labels are observational contexts, not randomized comparisons. The unknown order of decoders within a '
            'session rules out chronological-prefix and online-adaptation claims.',
            'Undefined values stay null, never zero: the constant comparator has no correlation.',
            'Audit scope: the saved features, fits, transforms, predictions, scores, cohort aggregates and bootstrap '
            'were independently replayed; the responses and features were not re-extracted from every raw file.',
        ],
        'release_limits': release['limitations'],
        'claims_not_supported': [
            'no online control quality or closed-loop claim',
            'no intended-motion or intention decoding',
            'no clinical validation',
            'not a foundation-model ranking, and no LoRA or target adaptation',
            'not 23 proven unique people, and the cohorts are never pooled',
            'no reproduction or endorsement of the original paper’s online results',
        ],
        'independent_audit': {
            'status': 'pass', 'records': sum(FORENZO_ADMITTED.values()),
            'checked': 'source fits, transforms and saved predictions replayed numerically; the target responses '
                       'scored independently; the cohort aggregates and bootstrap replayed and matched exactly; a final '
                       'independent review of the release and its claims',
            'not_checked': 'raw responses were not re-extracted from every source file, and the full feature '
                           'extraction was not repeated on all the raw EEG',
        },
    }
    written_from(result, (handoff, json.dumps(release), json.dumps(review)), label)
    return result, secret


# ---------------------------------------------------------------------------- boundary
def median_allowed(trail):
    """The four Forenzo ridge medians, and nothing else, may carry the key 'median'."""
    return re.fullmatch(r'\$\.results\.' + re.escape(FORENZO) + r'\.cohorts\.(?:Main|Transfer Learning)\.arms\.'
                        r'(?:' + '|'.join(FORENZO_ARMS) + r')\.ridge\.primary\.median', trail) is not None


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            if k == 'median' and median_allowed(here):
                require(number(v), f'{here}: not a number')
                continue
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
        require('jev' not in value.lower(), f'{trail}: Jev is not part of this question')


def claims_negated(payload):
    """A claim these results do not support appears only in a sentence that negates it."""
    for trail, text in strings(payload):
        if any(trail.startswith(p) for p in ('$.datasets', '$.provenance')):
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def figure_free(holds):
    """A hold says that no score exists and why; it carries none, not even a number in prose."""
    for h in holds:
        require(set(h) == {'id', 'statement', 'reason', 'scope'}, f'hold {h.get("id")}: unexpected fields')
        require(all(isinstance(v, str) and not re.search(r'\d', v) for v in h.values()),
                f'hold {h["id"]}: a hold carries a figure')
    return holds


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require([d['id'] for d in manifest['datasets']] == list(DATASETS), 'the manifest names other datasets')
    require([s['id'] for s in manifest['sources']] == [WBCIC_CPU, WBCIC_FM, RSVP, FORENZO],
            'the manifest names other sources')
    for s in manifest['sources']:
        require(s['decision'] == 'aggregate_preview', f'{s["id"]}: no other decision has an extractor')
        require(s['id'] in DATASETS[s['dataset']], f'{s["id"]}: filed under another dataset')
    src = {s['id']: s for s in manifest['sources']}

    datasets = {d['id']: dataset_rights(d) for d in manifest['datasets']}
    cpu, cpu_release = wbcic_cpu(src[WBCIC_CPU])
    results = {WBCIC_CPU: cpu, WBCIC_FM: wbcic_cbramod(src[WBCIC_FM], cpu_release), RSVP: rsvp(src[RSVP])}
    results[FORENZO], secret = forenzo(src[FORENZO])
    for rid, r in results.items():
        require(r['dataset'] in datasets and rid in DATASETS[r['dataset']], f'{rid}: no rights record')
    for d, entry in datasets.items():
        entry['results'] = list(DATASETS[d])

    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'question': QUESTION,
        'metric_units': 'balanced accuracy, accuracy, macro F1, AUROC, average precision, Brier score, ECE, shares and '
                        'chance levels are proportions in [0,1]; differences of these are differences of proportions; '
                        'log loss is per event in nats; the Forenzo primary error is a dimensionless source-SD-'
                        'normalized RMSE (lower is better), its raw RMSE is in each response’s stored units, R² and '
                        'Pearson are unitless; counts of people, records, trials, events, rows and runs are whole '
                        'numbers; null means undefined or unavailable, never zero',
        'scope': 'Four results on one question, each from its own approved release: WBCIC-SHU session 1 to session 3 '
                 'with two fixed CPU baselines and with frozen CBraMod; a first-visit ERP decoder at the longitudinal '
                 'RSVP source’s later visits; and a fixed spectral ridge in continuous cursor tracking, a negative '
                 'result. Same person, later session, no labels from the later session in every case. No dataset, '
                 'cohort or response arm is pooled, nothing joins the eight-protocol matrix, and the results share no '
                 'ranking.',
        'results': results,
        'datasets': datasets,
        'status_only': [],
        'holds': figure_free(manifest['holds']),
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': list(results),
                       'holds': [h['id'] for h in manifest['holds']],
                       'source_export_sha256': {s['id']: s['release']['sha256'] for s in manifest['sources']}},
    }
    scrub_check(payload)
    claims_negated(payload)
    validate_public(payload)
    # Per-record values refused by value too: within the Forenzo result, and every nonzero one anywhere.
    published, own = set(numbers(payload)), set(numbers(results[FORENZO]))
    leaked = [v for v in secret if v in own or (v != 0.0 and v in published)]
    require(not leaked, f'{FORENZO}: a per-record value reached the export: {leaked[:3]}')
    return payload


def input_refs(manifest):
    refs = []
    for d in manifest['datasets']:
        refs += [d['licenseRecord'], d['consentEthics']['record']]
    for s in manifest['sources']:
        refs += [v for k, v in s.items() if isinstance(v, dict) and 'sha256' in v and 'path' in v]
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
    # The audit is a separate program: it reads these bytes and the pinned source releases, and nothing of build().
    import audit_later_sessions_export
    return audit_later_sessions_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
