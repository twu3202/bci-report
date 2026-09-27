"""Release the 2026-09-27 expansion batch as aggregate-only JSON.

Three questions about context: does a P300 calibration carry across a display
change, what drives a score recorded while walking, and does an SSVEP decoder
fire when no command is intended. Plus a one-person technical pilot. All fixed
CPU baselines: nothing here is a foundation-model or PEFT result.

Its own publication boundary, as with every batch. What this export refuses:
- per-person fields. The reviewed inputs carry each cohort's minimum, maximum,
  median and quartiles, and the pilot's per-participant ranges; with 4 or 21
  people each of those is one person's score;
- any number not recomputed by an independent audit. The P300 direction-specific
  means are correct but were not re-derived, so they stay out;
- a held source. The asynchronous SSVEP pilot is scored and audited, but its
  consent statement has not been read; its extractor is ready and runs only
  once its manifest decision records a complete approval.

    python3 pipeline/publication/export_context_update.py
"""
from __future__ import annotations

import json
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20260927'
MANIFEST = REVIEW / 'context-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'context-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/context-update.json',
           PROJECT / 'site/public/data/context-update.json')

# Quartiles and ranges describe individual people at these cohort sizes.
REFUSED_KEYS = PER_PERSON_KEYS | {'q1', 'q3', 'range', 'private_run_dir', 'private_source',
                                  'private_evidence', 'private_outputs_root', 'output_path'}

TIMINGS = {  # published key -> key in the reviewed inputs
    'onset_corrected': 'literature_latency_corrected',
    'recorded_tag': 'canonical_recorded_tag',
}
P300_MODELS = {
    'mean_window_logreg': 'Mean-window logistic regression',
    'spatiotemporal_shrinkage_lda': 'Spatiotemporal shrinkage LDA',
}


def case(aggregate, case_id):
    found = [c for c in aggregate['cases'] if c['id'] == case_id]
    require(len(found) == 1, f'{case_id}: expected one case in the aggregate file')
    return found[0]


def audited_metric(block, replay, label):
    """Mean and interval, provided the independent audit recomputed the same values."""
    require(block['mean'] == replay['mean'], f'{label}: mean differs from the independent audit')
    require(block['bootstrap_mean_ci95'] == replay['bootstrap_mean_ci95'],
            f'{label}: interval differs from the independent audit')
    require(block['n_participants'] == 21, f'{label}: unexpected cohort size')
    return {'mean': block['mean'], 'bootstrap_95': block['bootstrap_mean_ci95']}


def vr_pc(record, aggregate):
    c = case(aggregate, record['caseId'])
    audit, _ = pinned(record['numericalAudit'], 'p300 audit')
    retention, _ = pinned(record['retentionRecord'], 'p300 retention')
    require(audit['status'] == 'PASS', 'p300: audit did not pass')
    require(audit['all_prediction_groups_refitted'] == 168, 'p300: not every fitted model was reproduced')
    require(audit['maximum_feature_abs_error'] == 0 and audit['maximum_refit_probability_abs_error'] == 0,
            'p300: reproduction was not exact')
    replay = audit['independently_recomputed_participant_macro']
    source_blocks = {'literature_latency_corrected': c['primary_metrics'],
                     'canonical_recorded_tag': c['prespecified_zero_shift_metrics']}
    timings = {}
    for public, key in TIMINGS.items():
        timings[public] = [
            {'id': model, 'label': label,
             'balanced_accuracy': audited_metric(source_blocks[key][model]['balanced_accuracy'],
                                                 replay[key][model]['balanced_accuracy'], f'{model}/{key}/BA'),
             'auroc': audited_metric(source_blocks[key][model]['auroc'],
                                     replay[key][model]['auroc'], f'{model}/{key}/AUROC')}
            for model, label in P300_MODELS.items()]
    unique, per_timing = retention['unique_source'], retention['per_timing']
    require(unique['participants'] == c['people'] and unique['labeled_events'] == c['unique_labeled_events'],
            'p300: retention record disagrees with the aggregate')
    require(retention['effect_on_scores'].startswith('None'), 'p300: retention change affects scores')
    return {
        'id': 'vr-pc-p300', 'protocol_id': retention['protocol_id'],
        'question': 'does a P300 calibration carry over when the same person changes display',
        'classes': 2, 'chance_level': 0.5, 'metric': 'balanced_accuracy',
        'generalization': c['generalization'],
        'same_display_reference': False,
        'cohort': {
            'people': c['people'], 'recordings': c['physical_recordings'],
            'labeled_events': unique['labeled_events'], 'target_events': unique['target_events'],
            'non_target_events': unique['non_target_events'],
            'retained_epochs': {public: per_timing[key]['retained_epochs'] for public, key in TIMINGS.items()},
            'rejected_epochs': {public: per_timing[key]['dropped_epochs'] for public, key in TIMINGS.items()},
        },
        'method': {
            'transfer': 'each person is calibrated on one display and tested on the other, in both directions; '
                        'the two directions are averaged within the person, then across the 21 people',
            'timing': {'onset_corrected': 'primary: source-reported tag-to-visual-onset offsets, +19 samples on '
                                          'the PC and +60 on the VR headset at 512 Hz',
                       'recorded_tag': 'prespecified sensitivity: epochs at the recorded tag, no shift'},
            'rejection': 'fixed 500 microvolt peak-to-peak epoch rejection',
            'selection': 'neither timing scheme was chosen from test scores',
            'interval_kind': 'participant bootstrap; descriptive',
        },
        'timings': timings,
        'limitations': c['limitations'] + [
            'No same-display reference was run, so the result says how well calibration carries over, '
            'not how much the display change costs.',
            'A mean onset correction does not remove event-to-event timing jitter.',
        ],
        'independent_audit': {'fitted_models_reproduced': audit['all_prediction_groups_refitted'],
                              'raw_feature_sets_rebuilt': audit['raw_feature_sets_independently_rebuilt']},
        'rights': rights(record),
    }


def gait(record, aggregate):
    c = case(aggregate, record['caseId'])
    result, result_sha = pinned(record['result'], 'gait result')
    audit, _ = pinned(record['numericalAudit'], 'gait audit')
    split, _ = pinned(record['splitAudit'], 'gait split audit')
    require(audit['status'] == 'PASS' and audit['metrics_reproduced'] is True, 'gait: audit did not pass')
    require(audit['participant_overlap_across_train_test'] is False, 'gait: participants leak across folds')
    require(audit['audited_result_sha256'] == result_sha, 'gait: the audit checked a different result')
    require(split['status'] == 'PASS' and split['all_people_have_three_distinct_speeds'] and split['held_person_absent'],
            'gait: split audit did not pass')
    require(split['source_result_sha256'] == result_sha, 'gait: split audit checked a different result')
    require(c['results'] == result['results'], 'gait: aggregate file disagrees with the audited result')

    shape = {
        'spectral_logistic': {'label': 'Relative spectral bands',
                              'inputs': 'five relative frequency bands on each of 19 scalp channels',
                              'comparator': False},
        'nuisance_logistic': {'label': 'Movement-nuisance features',
                              'inputs': 'three amplitude, low-frequency and line-frequency features',
                              'comparator': True},
    }
    models = []
    for key, s in shape.items():
        r = result['results'][key]
        # Every person contributes all three speeds, so accuracy and balanced
        # accuracy coincide and the accuracy bootstrap is the BA interval.
        require(abs(r['accuracy'] - r['balanced_accuracy']) < 1e-9, f'gait/{key}: classes are not balanced')
        require(r['participants'] == result['people'] == 58, f'gait/{key}: unexpected cohort size')
        models.append({'id': key, **s, 'balanced_accuracy': r['balanced_accuracy'],
                       'balanced_accuracy_bootstrap_95': r['participant_bootstrap_accuracy_95'],
                       'macro_f1': r['macro_f1']})
    return {
        'id': 'gait-eeg',
        'question': 'what might drive a speed score recorded while walking',
        'classes': 3, 'chance_level': result['chance_balanced_accuracy'], 'metric': 'balanced_accuracy',
        'generalization': c['generalization'],
        'not_for_model_rankings': True,
        'cohort': {
            'people_acquired': result['acquired_people'], 'people_scored': result['people'],
            'recordings_scored': result['recordings'], 'seconds_per_recording': c['whole_record_seconds'],
            'people_excluded': result['held_people'], 'recordings_excluded': result['held_recordings'],
            'exclusion': 'malformed channel labels in one source file; excluded before any scoring, no channels relabelled',
            'scalp_channels': result['scalp_channels_after_source_rereference'],
        },
        'method': {
            'reference': "the authors' linked-ear re-reference, which reconstructs 19 scalp channels",
            'split': 'five participant-disjoint folds; each whole 58-second recording is one sample',
            'classifier': 'training-only standardisation and a fixed regularised logistic regression',
            'interval_kind': 'participant bootstrap conditioned on the fitted folds; descriptive',
        },
        'models': models,
        'limitations': c['limitations'],
        'rights': rights(record),
    }


def ysu(record, aggregate):
    """Ready for when the hold is lifted; build() runs it only for a complete approval."""
    c = case(aggregate, record['caseId'])
    summary, summary_sha = pinned(record['result'], 'ysu summary')
    audit, _ = pinned(record['numericalAudit'], 'ysu audit')
    require(audit['status'] == 'PASS', 'ysu: audit did not pass')
    require(audit['hashes']['public_summary_sha256'] == summary_sha, 'ysu: the audit checked a different summary')
    m, n = summary['metrics'], summary['heldout_counts']
    require(m == c['metrics'] and n == c['heldout_counts'], 'ysu: aggregate file disagrees with the summary')

    def count(rate, of):
        k = round(rate * of)
        require(abs(k / of - rate) < 1e-9, 'ysu: a pooled rate is not a whole count')
        return k
    cs = n['CS']
    recognised = count(m['CS_frequency_accuracy']['pooled'], cs)
    accepted = count(m['CS_acceptance_coverage']['pooled'], cs)
    correct_accepted = count(m['CS_correct_and_accepted_rate']['pooled'], cs)
    require(abs(correct_accepted / accepted - m['accepted_CS_frequency_accuracy']['pooled']) < 1e-9,
            'ysu: accepted-window accuracy does not follow from the counts')
    names = {'NS1': 'central image, flicker off', 'NS2': 'looking at a white wall, resting',
             'NS3': 'central image while the surrounding stimuli flicker'}
    return {
        'id': 'ysu-async-ssvep',
        'question': 'does an SSVEP decoder accept a window when no command is intended',
        'pilot': True, 'people': summary['participant_count'],
        'method': {'decoder': 'fixed sinusoidal CCA on eight occipital and parietal channels',
                   'rejection': 'per-person thresholds fitted on calibration trials only',
                   'window': '1.5 seconds per separately collected trial'},
        # Conditional accuracy never travels without its coverage and end-to-end rate.
        'control_windows': {'tested': cs, 'frequency_recognised': recognised, 'accepted': accepted,
                            'accepted_and_correct': correct_accepted},
        'control_vs_non_control_balanced_accuracy': m['pooled_detection_balanced_accuracy']['pooled'],
        'false_acceptance': [{'condition': names[k], 'accepted': v['false_accept_count'], 'tested': v['n']}
                             for k, v in m['window_false_acceptance_rate_by_condition'].items()],
        'rate_kind': 'offline window-level rates, not false activations per hour',
        'limitations': c['limitations'],
        'rights': rights(record),
    }


def stieger(record, aggregate):
    note = [t for t in aggregate['technical_notes'] if t['id'] == 'stieger-longitudinal-feasibility']
    require(len(note) == 1, 'stieger: technical note missing')
    note = note[0]
    audit, _ = pinned(record['numericalAudit'], 'stieger audit')
    require(note['public_numeric_model_scores_included'] is False, 'stieger: a score was included')
    require(note['audit_status'] == 'PASS', 'stieger: audit did not pass')
    require(audit['feature_table']['identity_rows'] == note['eligible_trials'], 'stieger: trial count disagrees')
    require(audit['freeze_and_provenance']['heldout_scores_existed_at_observation'] is False,
            'stieger: protocol frozen after scores existed')
    return {'id': 'stieger-longitudinal', 'name': record['name'], 'status': 'status_only',
            'scores_published': False, 'reason': record['reason'],
            'feasibility': {'people': note['people'], 'sessions': note['sessions'],
                            'trials_in_source': note['source_trials'], 'trials_eligible': note['eligible_trials'],
                            'split': 'chronological: earlier sessions train, later sessions test'},
            'rights': {k: record[k] for k in ('source', 'license', 'licenseUrl', 'attribution')}}


EXTRACT = {'vr-pc-p300': vr_pc, 'gait-eeg': gait, 'ysu-async-ssvep': ysu}
STATUS = {'stieger-longitudinal': stieger}


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS, f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    aggregate, _ = pinned(manifest['aggregate'], 'v6 aggregate')
    require(aggregate['new_foundation_model_scores'] is False and aggregate['new_peft_scores'] is False,
            'this export has no foundation-model or PEFT path')
    results, status, included, held = {}, [], [], []
    for record in manifest['sources']:
        if record['decision'] == 'aggregate_preview':
            require(approved(record), f'{record["id"]}: approval record is incomplete')
            results[record['id']] = EXTRACT[record['id']](record, aggregate)
            included.append(record['id'])
        elif record['decision'] == 'status_only':
            status.append(STATUS[record['id']](record, aggregate))
        else:
            require(record['decision'] == 'hold', f'{record["id"]}: unknown decision')
            held.append(record)
    payload = {
        'schema_version': 'bci-report-context-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': 'balanced accuracy and macro F1 are proportions in [0,1]; AUROC is dimensionless',
        'scope': ('Fixed CPU baselines on separate questions and separate data. No foundation-model or PEFT '
                  'result. Nothing here extends the eight-protocol matrix, and no two results share a ranking.'),
        'results': results,
        'status_only': status,
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included},
    }
    scrub_check(payload)
    validate_public(payload)
    # A source held for its consent documentation leaves no trace, not even its name.
    text = json.dumps(payload)
    for record in held:
        for trace in (record['id'], record['name'], record['source'].rsplit('/', 1)[-1]):
            require(trace not in text, f'held source {record["id"]} leaked into the export: {trace}')
    return payload, [r['id'] for r in held] + [s['id'] for s in status]


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    refs = [manifest['aggregate']]
    for s in manifest['sources']:
        refs += [s[k] for k in ('result', 'numericalAudit', 'splitAudit', 'retentionRecord') if k in s]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    payload, _ = build(MANIFEST.read_bytes())
    return (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload, not_included = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'included': payload['provenance']['included'], 'held_or_status_only': not_included,
        'checks': ['pinned aggregate, result and audit bytes',
                   'every published mean and interval equals the independent audit',
                   'audits bound to the exact result files they checked',
                   'complete approval record per included source',
                   'per-person fields, quartiles and ranges refused',
                   'held source absent by id, name and record number',
                   'no foundation-model or PEFT result',
                   'no private paths or participant identifiers'],
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
