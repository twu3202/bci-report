"""Release the v7 extension batch (reviewed 2026-10-02) as aggregate-only JSON.

Two questions, two fixed classical baselines, nothing shared between them:

- YSU, twenty further people. Does a rejection threshold fitted on each new
  person (96 of their own labelled windows) separate "a command is intended"
  from "none is" better than one threshold fixed on the four-person pilot? The
  pilot published on 2026-09-27 is this design's development set; none of its
  people is scored here.
- LTRSVP, nine people. Does a P300 target decoder trained on a 5-Hz recording
  carry over to a different, 10-Hz recording as well as a decoder trained on the
  other 10-Hz recording? Rate and recording change together, and so does the
  time between them: the original study presented the rates from the lowest to
  the highest, not randomised, and how the released files map onto that sequence
  is not documented. No answer here is about image rate alone.

Its own publication boundary, as with every batch. The website inputs are the
two sanitized aggregates. The independent audits are pinned by hash and checked
for PASS against those exact bytes, but never copied: they carry private
storage paths. What this export refuses:
- per-person values: the YSU aggregate's per-participant ranges, and which
  people were helped or harmed (how many is published);
- thresholds, scores, predictions and features — by key, and the fixed global
  threshold by value as well;
- any rate that does not follow from whole window counts, and any summary
  figure that does not follow from the counts it is published beside.

    python3 pipeline/publication/export_extension_update.py
"""
from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261002'
MANIFEST = REVIEW / 'extension-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'extension-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/extension-update.json',
           PROJECT / 'site/public/data/extension-update.json')
PUBLISHED = PROJECT / 'site/public/data'

# Per-person distributions, and anything that is a decoder's internals rather
# than its result. Keys are refused by exact name and by fragment.
REFUSED_KEYS = PER_PERSON_KEYS | {'q1', 'q3', 'range', 'private_evidence', 'private_evidence_sha256'}
REFUSED_KEY_FRAGMENTS = ('threshold', 'prediction', 'probabilit', 'feature', 'private', 'range',
                         'participant_id', 'per_person', 'per_participant')
# Archive names of the YSU release (S01.zip … S24.zip) and LTRSVP file stems.
SOURCE_IDS = re.compile(r'\bS(?:0[1-9]|1\d|2[0-4])\b|rsvp_\d+Hz_\d+')
TOL = 1e-12

STATES = {  # the aggregate's key -> what the person was doing
    'NS1': 'looking at a central image, flicker off',
    'NS2': 'looking at a white wall, resting',
    'NS3': 'looking at a central image while the surrounding targets flicker',
}
RULES = {
    'global': {'label': 'Global threshold',
               'fitted_on': 'the calibration windows of the four pilot people only; no label from the new person',
               'target_person_labels': 0},
    'personal': {'label': 'Personal threshold',
                 'fitted_on': "the new person's own calibration windows: 48 with a command intended and 48 "
                              'without, the non-control states pooled 1:1:2',
                 'target_person_labels': 96},
}
RATES = (5, 6, 10)
# What the LTRSVP pages say about presentation order rests on these sentences,
# read from the original publication and recorded, with their URL, in the
# manifest's decisionHistory. The export refuses to state the order without them.
ORDER_QUOTES = ('presented from the lowest to the highest presentation rate',
                'order of the conditions across subjects was not randomised')


def bound_audit(record, summary, summary_sha, protocol_sha, label):
    """The audit passed, and it audited these exact bytes under this protocol and runner."""
    audit, audit_sha = pinned(record['numericalAudit'], f'{label} audit')
    require(audit['status'] == 'PASS', f'{label}: the independent audit did not pass')
    require(audit['public_summary_sha256'] == summary_sha, f'{label}: the audit checked a different aggregate')
    require(audit['protocol_sha256'] == summary['protocol_sha256'] == protocol_sha,
            f'{label}: protocol identity differs between aggregate, audit and pinned protocol')
    require(audit['runner_sha256'] == summary['runner_sha256'], f'{label}: runner identity differs')
    require(audit['completed_at_utc'] > summary['created_at_utc'], f'{label}: the audit predates the aggregate')
    return audit, audit_sha


def close(a, b, label):
    require(abs(a - b) < TOL, f'{label}: {a!r} does not equal {b!r}')


def whole(rate, k, n, label):
    """A published rate must be a whole count of windows over its denominator."""
    require(isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0, f'{label}: not a count')
    close(rate, k / n, label)
    return k


def interval(block, label):
    lo, hi = block
    require(0 <= lo <= hi <= 1, f'{label}: not an interval of proportions')
    return [lo, hi]


def consent_record(record):
    """The YSU consent statement was read for the 2026-09-27 release; reuse that record, unchanged."""
    ref = record['consentRecord']
    manifest, _ = pinned(ref, 'ysu consent record')
    found = [s for s in manifest['sources'] if s['id'] == ref['sourceId']]
    require(len(found) == 1, 'ysu: the referenced consent record is missing')
    prior = found[0]
    require(approved(prior), 'ysu: the referenced record carries no complete approval')
    for k in ('source', 'license', 'licenseUrl', 'attribution'):
        require(prior[k] == record[k], f'ysu: the referenced record names a different {k}')
    require('written informed consent' in prior['privacyReview'] and 'ethics committee' in prior['privacyReview'],
            'ysu: the referenced record does not state consent and ethics approval')
    return prior


def development_pilot(record, protocol, per_person_cal):
    """The pilot is published, reviewed, and is exactly the four donors of the global rule."""
    ref = record['developmentPilot']
    audit = json.loads((PROJECT / ref['exportAudit']).read_text())
    raw = (PUBLISHED / ref['file']).read_bytes()
    require(audit['status'] == 'pass' and sha(raw) == audit['export_sha256'],
            'ysu: the development pilot is not the reviewed published file')
    pilot = json.loads(raw)['results'][ref['resultId']]
    require(protocol['global_donor_cal_count'] == pilot['people'] * per_person_cal,
            'ysu: the global rule was not fitted on the pilot people alone')
    return {'file': ref['file'], 'result_id': ref['resultId'], 'people': pilot['people'],
            'role': 'development set: the global rule is fitted on its people only, and none of them is '
                    'among the people scored here'}


def ysu_extension(record):
    summary, summary_sha = pinned(record['summary'], 'ysu aggregate')
    protocol, protocol_sha = pinned(record['protocol'], 'ysu protocol')
    audit, _ = bound_audit(record, summary, summary_sha, protocol_sha, 'ysu')
    consent_record(record)
    require(audit['mode'] == 'deep', 'ysu: the audit ran in shallow mode')
    people = summary['completed_participant_count']
    require(people == summary['planned_participant_count'] == len(protocol['planned_participants'])
            == audit['counts']['completed_participants'] == 20, 'ysu: the cohort is not the planned twenty')
    require(summary['missing_participant_count'] == 0 == audit['counts']['missing_participants'],
            'ysu: a planned person is missing')
    require(summary['analysis_id'] == protocol['protocol_id'], 'ysu: aggregate and protocol differ')
    require(record['source'].endswith(summary['source_revision'].split(':')[1] + '.v3')
            and summary['source_revision'].endswith(':v3'), 'ysu: another source revision')

    # Every person contributes the same windows, so a participant mean of an
    # acceptance rate is the pooled window rate. Checked, not assumed.
    tests, split = summary['test_counts'], protocol['fixed_splits']
    per_person = {}
    for key, n in tests.items():
        require(n % people == 0 and n // people == split[key]['windows_per_partition'],
                f'ysu: {key} windows are not equal across people')
        per_person[key] = n // people
    per_person_cal = sum(s['windows_per_partition'] for s in split.values())
    require(per_person_cal == RULES['personal']['target_person_labels'] == sum(per_person.values()),
            'ysu: calibration and test partitions are not 96 windows each')
    require(split['CS']['windows_per_partition'] == split['NS1']['windows_per_partition']
            + split['NS2']['windows_per_partition'] + split['NS3']['windows_per_partition'],
            'ysu: control and pooled non-control windows are not 48 each')
    require(audit['counts']['prediction_rows'] == people * per_person_cal * len(RULES),
            'ysu: the audit did not check every scored window of both rules')

    rules, exact_ba = [], {}
    for rid, shape in RULES.items():
        arm = summary['arms'][rid]
        cs, counts = arm['CS'], arm['CS_counts']
        n = counts['n']
        require(n == tests['CS'], f'ysu/{rid}: control windows differ from the test partition')
        for block in cs.values():
            require(block['defined_participant_count'] == people, f'ysu/{rid}: a rate is undefined for someone')
        accepted = whole(cs['acceptance_coverage']['mean'], counts['accept_count'], n, f'ysu/{rid} coverage')
        both = whole(cs['correct_and_accepted_rate']['mean'], counts['accepted_frequency_correct_count'], n,
                     f'ysu/{rid} correct and accepted')
        recognised = whole(cs['frequency_accuracy']['mean'], counts['frequency_correct_count'], n,
                           f'ysu/{rid} frequency recognised')
        states, fa_k, fa_n = [], 0, 0
        for key, condition in STATES.items():
            s = arm['NS'][key]
            require(s['n'] == tests[key] and s['participant']['defined_participant_count'] == people,
                    f'ysu/{rid}/{key}: windows differ from the test partition')
            k = whole(s['participant']['mean'], s['false_accept_count'], s['n'], f'ysu/{rid}/{key}')
            states.append({'state': key, 'condition': condition, 'accepted': k, 'tested': s['n']})
            fa_k, fa_n = fa_k + k, fa_n + s['n']
        # Detection BA = (coverage + 1 − pooled non-control false acceptance) / 2, from the counts.
        ba = (Fraction(accepted, n) + 1 - Fraction(fa_k, fa_n)) / 2
        close(arm['balanced_accuracy']['mean'], float(ba), f'ysu/{rid} detection BA')
        exact_ba[rid] = ba
        rules.append({
            'id': rid, **shape,
            'detection_balanced_accuracy': {
                'mean': arm['balanced_accuracy']['mean'],
                'bootstrap_95': interval(arm['balanced_accuracy']['bootstrap_mean_ci95'], f'ysu/{rid} BA')},
            'control_windows': {'tested': n, 'frequency_recognised': recognised, 'accepted': accepted,
                                'accepted_and_correct': both},
            'accepted_window_accuracy_mean_over_people': cs['accepted_frequency_accuracy']['mean'],
            'false_acceptance': states,
            'non_control_pooled': {'accepted': fa_k, 'tested': fa_n},
            'equal_state_detection_balanced_accuracy': arm['equal_NS_condition_BA']['mean'],
        })
    g, p = rules
    require(g['control_windows']['frequency_recognised'] == p['control_windows']['frequency_recognised'],
            'ysu: the frequency classifier differs between rules')

    d = summary['paired_BA_personal_minus_global']
    require(d['helped'] + d['harmed'] + d['tied'] == people, 'ysu: helped + harmed + tied is not the cohort')
    require(Fraction(d['exact_fraction']) == exact_ba['personal'] - exact_ba['global'],
            'ysu: the paired difference does not follow from the counts')
    close(d['mean'], float(Fraction(d['exact_fraction'])), 'ysu paired mean')
    lo, hi = d['bootstrap_mean_ci95']
    require(lo <= d['mean'] <= hi, 'ysu: the paired mean lies outside its interval')
    # The reading the page prints, held to the numbers: detection rose, end-to-end output did not.
    require(d['mean'] > 0 and p['control_windows']['accepted_and_correct'] <= g['control_windows']['accepted_and_correct'],
            'ysu: the trade-off the page describes no longer holds')
    require(all(ps['accepted'] <= gs['accepted'] for gs, ps in zip(g['false_acceptance'], p['false_acceptance'])),
            'ysu: the personal rule does not lower false acceptance in every state')

    return {
        'id': 'ysu-async-ssvep-extension',
        'question': 'does a rejection threshold fitted on each new person separate intended commands from '
                    'non-control better than one fixed on other people, and at what cost',
        'protocol_id': summary['analysis_id'],
        'generalization': 'twenty further people of the same release, scored under rules fixed before scoring; '
                          'an extension within one dataset, not an external validation',
        'development_pilot': development_pilot(record, protocol, per_person_cal),
        'cohort': {'people': people, 'people_missing': 0,
                   'test_windows_each_person': {'control': per_person['CS'], **{k: per_person[k] for k in STATES}},
                   'calibration_windows_each_person': per_person_cal,
                   'global_rule_calibration_windows': protocol['global_donor_cal_count']},
        'method': {
            'decoder': 'fixed sinusoidal CCA on eight occipital and parietal channels (PO7, PO3, POz, PO4, PO8, '
                       'O1, Oz, O2), three harmonics; the frequency with the largest correlation is the command',
            'window': '1.5 seconds scored per separately collected trial',
            'acceptance': 'a window is accepted as a command when its largest CCA correlation clears the rule; '
                          'each rule is chosen to maximise detection balanced accuracy on its calibration windows',
            'same_test_windows': 'both rules score the same 96 held-out windows of each person, disjoint from '
                                 'the calibration windows',
            'detection_balanced_accuracy': 'the mean of control-window acceptance and non-control rejection, the '
                                           'three non-control states pooled 1:1:2 as collected; it measures whether '
                                           'a command is detected, not whether the accepted frequency is right',
            'weighting': 'every person contributes the same windows, so the participant means of acceptance and '
                         'false acceptance equal the pooled window rates; accepted-window accuracy is the mean of '
                         "each person's rate and is shown only beside coverage and the end-to-end rate",
            'interval_kind': 'descriptive whole-person bootstrap, 20,000 draws, conditional on the four pilot '
                             'people and on each realised calibration partition',
        },
        'rules': rules,
        'paired_difference': {
            'comparison': 'personal minus global threshold, same people and windows',
            'metric': 'detection_balanced_accuracy',
            'mean': d['mean'], 'exact_fraction': d['exact_fraction'], 'bootstrap_95': [lo, hi],
            'helped': d['helped'], 'harmed': d['harmed'], 'tied': d['tied'],
        },
        'reading': 'Detection balanced accuracy rose and false acceptance fell in every non-control state, while '
                   'the share of control windows both accepted and correct did not rise: a better detector here is '
                   'not better command accuracy.',
        'rate_kind': 'offline window-level rates, not false activations per hour',
        'limitations': [
            'An extension within one dataset: the twenty people share the pilot\'s source, lab and protocol. It is '
            'not validation on an independent cohort.',
            "The personal rule uses 96 labelled windows from the person; the comparison cannot separate fitting to "
            'the person from simply having those labels.',
            'Calibration and test windows are fixed index partitions; the source does not establish their order in '
            'time, so this is not a calibrate-earlier, use-later experiment.',
            'Separately collected, pre-epoched windows in a fixed mixture of states: window rates only, not false '
            'activations per hour, latency, information transfer rate or how often commands occur in real use.',
            'The source states no physical amplitude unit, so nothing here depends on one.',
            'No clinical or population claim; fixed CCA has no pretraining, so no pretraining claim applies.',
        ],
        'independent_audit': {'status': 'pass', 'mode': 'deep', 'people': people,
                              'scored_windows_checked': audit['counts']['prediction_rows']},
        'rights': rights(record),
    }


def presentation_order(record):
    """What is known and unknown about the order of the recordings, as the manifest recorded it.

    Known, from the original publication: the rates were presented from the
    lowest to the highest, in an order not randomised across participants. Not
    known: how the two released files of each rate map onto that sequence;
    PhysioNet says only that, within a rate, file a came first and a long break
    followed. The reading must be on record, quoted and with its source, before
    the export states it.
    """
    quotes = [q for h in record.get('decisionHistory', []) for q in h.get('quotes', [])]
    for phrase in ORDER_QUOTES:
        require(any(phrase in q['text'] and q['source'] == 'https://doi.org/10.1371/journal.pone.0178498' for q in quotes),
                f'ltrsvp: the presentation order is stated without its recorded source ("{phrase}")')
    require(any('which one was taken first' in q['text'] and q['source'] == record['source'] for q in quotes),
            'ltrsvp: the within-rate order is stated without its recorded source')
    return {
        'known': 'the original publication reports that the three rates were presented from the lowest to the '
                 'highest, an order not randomised across participants; PhysioNet reports that, within a rate, run a '
                 'was recorded first and a long break followed',
        'not_documented': 'how the two released files of each rate map onto the ascending sequence',
        'consequence': 'a cross-rate cell also differs in elapsed time, fatigue and practice, not only in rate and '
                       'recording',
        'sources': sorted({q['source'] for q in quotes}),
    }


def ltrsvp(record):
    summary, summary_sha = pinned(record['summary'], 'ltrsvp aggregate')
    protocol, protocol_sha = pinned(record['protocol'], 'ltrsvp protocol')
    audit, _ = bound_audit(record, summary, summary_sha, protocol_sha, 'ltrsvp')
    c = audit['counts']
    people = summary['participant_count']
    require(people == len(protocol['people']) == c['participants'] == 9, 'ltrsvp: not the nine complete people')
    require(summary['physical_recordings'] == protocol['selected_recording_count']
            == c['physical_recordings_rehashed_and_reextracted'] == people * 2 * len(RATES), 'ltrsvp: recordings')
    require(summary['fits'] == protocol['planned_fit_count'] == c['independent_refits'] == people * len(RATES),
            'ltrsvp: fits')
    require(summary['evaluation_cells'] == protocol['planned_evaluation_cells'] == c['evaluation_cells']
            == people * len(RATES) ** 2, 'ltrsvp: evaluation cells')
    excluded = len(protocol['excluded_metadata_incomplete_people'])
    require(protocol['source_selection'].endswith('no performance selection.'), 'ltrsvp: selection by score')
    require(summary['source_url'] == record['source'] and summary['source_version'] == '1.0.0'
            and protocol['source_doi'] in record['attribution'], 'ltrsvp: another source')
    require(protocol['source_license'].startswith(record['license'].replace(' 1.0', '')),
            'ltrsvp: the licence differs from the pinned protocol')
    s = audit['numerical_stability']
    require(s['raw_feature_fixed_model_changed_predictions'] == 0 and s['raw_feature_fixed_model_changed_confusion_cells'] == 0
            and s['saved_feature_refit_probability_maximum_absolute_error'] == 0
            and all(v == 0 for v in s['raw_feature_fixed_model_aggregate_differences'].values()),
            'ltrsvp: the independent replay did not reproduce every decision and aggregate')

    order = presentation_order(record)

    cells = {(m['source_rate_hz'], m['target_rate_hz']): m for m in summary['matrix']}
    require(sorted(cells) == [(a, b) for a in RATES for b in RATES], 'ltrsvp: the matrix is not complete')
    # Same run-b test events whatever the training rate. This export checks the
    # counts; that they are the same events is asserted by the aggregate (its
    # estimand) and by the audit (same-target paired contrast, prediction
    # identities). Both assertions are required here, not assumed.
    require('identical10hz-beventidentities' in summary['primary_estimand'].replace(' ', '').lower(),
            'ltrsvp: the aggregate no longer asserts identical 10-Hz run-b test events')
    require(any(v.startswith('same-target paired primary contrast') for v in audit['verified'])
            and any(v.startswith('all prediction identities') for v in audit['verified']),
            'ltrsvp: the audit no longer records the same-target pairing it checked')
    events = {}
    for t in RATES:
        counts = {(cells[(s_, t)]['target_n'], cells[(s_, t)]['non_target_n']) for s_ in RATES}
        require(len(counts) == 1, f'ltrsvp: test-event counts at {t} Hz differ between training rates')
        events[t] = counts.pop()
    matrix = []
    for (src, tgt), m in sorted(cells.items()):
        matrix.append({'train_rate_hz': src, 'test_rate_hz': tgt,
                       'balanced_accuracy': {'mean': m['balanced_accuracy']['participant_mean'],
                                             'bootstrap_95': interval(m['balanced_accuracy']['bootstrap_mean_ci95'],
                                                                      f'ltrsvp {src}->{tgt} BA')},
                       'auroc': {'mean': m['auroc']['participant_mean'],
                                 'bootstrap_95': interval(m['auroc']['bootstrap_mean_ci95'], f'ltrsvp {src}->{tgt} AUROC')},
                       'target_events': m['target_n'], 'non_target_events': m['non_target_n']})

    d = summary['primary_paired_BA_5a_to_10b_minus_10a_to_10b']
    cross, same = cells[(5, 10)], cells[(10, 10)]
    close(d['mean'], cross['balanced_accuracy']['participant_mean'] - same['balanced_accuracy']['participant_mean'],
          'ltrsvp paired mean')
    close(d['mean'], float(Fraction(d['exact_fraction'])), 'ltrsvp exact fraction')
    require(d['lower'] + d['higher'] + d['tied'] == people, 'ltrsvp: lower + higher + tied is not the cohort')
    lo, hi = d['bootstrap_mean_ci95']
    require(lo <= d['mean'] <= hi, 'ltrsvp: the paired mean lies outside its interval')
    a = summary['secondary_paired_AUROC_contrast']
    close(a['mean'], cross['auroc']['participant_mean'] - same['auroc']['participant_mean'], 'ltrsvp AUROC contrast')
    alo, ahi = a['bootstrap_mean_ci95']
    crosses = lo < 0 < hi
    # The page says the interval crosses zero and claims no rate effect; if that stops being true, stop here.
    require(crosses and alo < 0 < ahi, 'ltrsvp: the interval no longer crosses zero; the page wording must be reviewed')

    def arm(cell, label):
        return {'id': label, 'train_rate_hz': cell['source_rate_hz'], 'test_rate_hz': cell['target_rate_hz'],
                'balanced_accuracy': {'mean': cell['balanced_accuracy']['participant_mean'],
                                      'bootstrap_95': cell['balanced_accuracy']['bootstrap_mean_ci95']},
                'auroc': {'mean': cell['auroc']['participant_mean'], 'bootstrap_95': cell['auroc']['bootstrap_mean_ci95']}}

    return {
        'id': 'ltrsvp-rate-transfer',
        'question': 'does a P300 target decoder trained on one recording at one image rate carry over to a different '
                    'recording at another rate',
        'protocol_id': summary['analysis_id'],
        'classes': 2, 'chance_level': 0.5, 'metric': 'balanced_accuracy',
        'generalization': 'same person, another recording: train on run a at one rate, test on run b at the same '
                          'or another rate. Within a rate, run b followed run a after a long break. Across rates the '
                          'original study presented the rates from the lowest to the highest, not randomised across '
                          'participants, and how the released files map onto that sequence is not documented',
        'presentation_order': order,
        'not_causal': True,
        'cohort': {'people': people, 'people_in_release': people + excluded, 'people_excluded': excluded,
                   'exclusion': 'missing both recordings at one rate in the release; excluded from file metadata '
                                'before any scoring',
                   'recordings': summary['physical_recordings'], 'source_fits': summary['fits'],
                   'evaluation_cells': summary['evaluation_cells'],
                   'unique_test_events': sum(t + n for t, n in events.values())},
        'method': {
            'stimuli': 'aerial images of London shown one after another at 5, 6 or 10 per second; targets contain '
                       'an airplane',
            'signal': "eight posterior channels (PO8, PO7, PO3, PO4, P7, P8, O1, O2) as released, 0.15-28 Hz by the "
                      'producer, 2048 Hz; no added filtering, re-reference or artifact rejection',
            'inputs': 'six 100-ms channel means from 0.1 to 0.7 s after each image, minus that image\'s '
                        '-0.2 to 0 s mean: 48 per image',
            'classifier': 'standardisation fitted on the training recording, then class-balanced logistic '
                          'regression (C = 1); target when its probability is at least 0.5',
            'selection': 'none: no hyperparameter, threshold, artifact rule or seed chosen from any score',
            'interval_kind': 'descriptive whole-person bootstrap, 20,000 draws; images and cells add no people',
        },
        'primary': {
            'test': 'the same 10-Hz run-b test events in both arms: equal counts checked here, identity asserted by '
                    'the aggregate and its audit',
            'target_events': events[10][0], 'non_target_events': events[10][1],
            'arms': [arm(cross, 'trained-5hz'), arm(same, 'trained-10hz')],
        },
        'paired_difference': {
            'comparison': 'trained at 5 Hz minus trained at 10 Hz, both tested on the same 10-Hz run-b images',
            'metric': 'balanced_accuracy',
            'mean': d['mean'], 'exact_fraction': d['exact_fraction'], 'bootstrap_95': [lo, hi],
            'interval_crosses_zero': crosses,
            'people_lower': d['lower'], 'people_higher': d['higher'], 'people_tied': d['tied'],
        },
        'secondary_auroc_difference': {'mean': a['mean'], 'bootstrap_95': [alo, ahi],
                                       'interval_crosses_zero': alo < 0 < ahi},
        'reading': 'Lower on average after training at the slower rate, but the interval crosses zero: no change '
                   'is established, and rate, recording and time in the session are confounded, so none could be '
                   'attributed to rate.',
        'matrix': matrix,
        'limitations': [
            'Rate and recording change together: training at another rate also means another recording, another '
            'number of images and another class balance. Not a causal effect of image rate.',
            'Order: the original study presented the rates from the lowest to the highest, not randomised across '
            'participants, and how the two released files of each rate map onto that sequence is not documented. A '
            'cross-rate cell therefore also differs in elapsed time, fatigue and practice.',
            'Nine people. The 81 cells and the thousands of test images add no people; intervals summarise the nine.',
            'At these rates the baseline and response windows of one image contain its neighbours, so nothing '
            'here isolates a target response.',
            'Offline and fixed: no online latency, information transfer rate, false activations per hour, new-person '
            'transfer, clinical claim, foundation-model or fine-tuning result.',
        ],
        'independent_audit': {'status': 'pass', 'recordings_rehashed_and_reextracted': c['physical_recordings_rehashed_and_reextracted'],
                              'models_refitted': c['independent_refits'], 'evaluation_cells': c['evaluation_cells']},
        'rights': rights(record),
    }


EXTRACT = {'ysu-async-ssvep-extension': ysu_extension, 'ltrsvp-rate-transfer': ltrsvp}


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source participant or file identifier in export: {trail}')


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, float):
        yield value


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    for ref in [manifest['handoff'], *manifest['sourceHandoffs']]:
        require(sha((PROJECT / ref['path']).read_bytes()) == ref['sha256'], f'handoff: {ref["path"]} is not the pinned bytes')
    results, included, secret = {}, [], []
    for record in manifest['sources']:
        require(record['decision'] == 'aggregate_preview', f'{record["id"]}: no other decision has an extractor')
        require(approved(record), f'{record["id"]}: approval record is incomplete')
        results[record['id']] = EXTRACT[record['id']](record)
        included.append(record['id'])
        protocol, _ = pinned(record['protocol'], f'{record["id"]} protocol')
        if 'global_threshold' in protocol:
            secret.append(protocol['global_threshold'])
    payload = {
        'schema_version': 'bci-report-extension-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': 'balanced accuracy, coverage and acceptance are proportions in [0,1]; AUROC is dimensionless; '
                        'differences are differences of proportions; window counts are whole numbers',
        'scope': ('Two fixed classical baselines on two separate questions and data sets: an SSVEP rejection rule '
                  'on twenty further people of one release, and P300 image-rate and recording transfer on nine '
                  'people. No foundation-model or fine-tuning result. Nothing here extends the eight-protocol '
                  'matrix, and the two results share no ranking.'),
        'results': results,
        'status_only': [],
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included},
    }
    scrub_check(payload)
    validate_public(payload)
    published = set(numbers(payload))
    for value in secret:
        require(value not in published, 'a fitted threshold value reached the export')
    return payload


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    refs = [manifest['handoff'], *manifest['sourceHandoffs']]
    for s in manifest['sources']:
        refs += [s[k] for k in ('summary', 'protocol', 'numericalAudit', 'consentRecord') if k in s]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'included': payload['provenance']['included'], 'status_only': [],
        'checks': ['pinned handoffs, aggregates, protocols and independent audits',
                   'each audit passed and names the exact aggregate bytes, protocol and runner',
                   'YSU consent reused from the pinned 2026-09-27 record: same source, licence and attribution',
                   'YSU development pilot is the reviewed published file and the global rule\'s only donors',
                   'every published acceptance rate is a whole count of windows; equal windows per person checked',
                   'detection balanced accuracy and the paired difference follow exactly from the counts',
                   'helped + harmed + tied = 20 (YSU); lower + higher + tied = 9 (LTRSVP)',
                   'LTRSVP: identical test-event counts per test rate (identity asserted by the aggregate and its '
                   'audit); paired means equal the cell means',
                   'LTRSVP: the presentation order is stated only with its quoted sources recorded in the manifest',
                   'the trade-off and interval-crosses-zero readings are re-derived from the numbers',
                   'per-person ranges, thresholds, predictions and features refused by key; global threshold by value',
                   'no private paths, source archive names or participant identifiers'],
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
