"""Release the 2026-09-23 expansion batch as aggregate-only JSON.

Its own publication boundary again, for the same reason as the 2026-09-22 one:
the earlier manifests never covered this batch. What is different here is the
population. ds004584 is a clinical cohort — 100 people with Parkinson's disease
and 49 controls — so this export refuses more than the earlier ones do:

- per-person fields, as before;
- the per-group age means and sex counts. They sit in the reviewed audit and
  they are aggregates, but a demographic profile of a diagnosis-specific group
  is exactly what /data-use/ says this site does not publish. The confound
  comparator's score makes the same point without them;
- the L-FAME per-condition band ratios. Twelve recordings from six people: a
  minimum or a maximum there is one person's recording.

The age-and-sex comparator is published, and is marked as excluded from every
model comparison. It is not an EEG model.

    python3 pipeline/publication/export_clinical_update.py
"""
from __future__ import annotations

import json
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20260923'
MANIFEST = REVIEW / 'clinical-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'clinical-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/clinical-update.json',
           PROJECT / 'site/public/data/clinical-update.json')

# A clinical cohort's demographics, and the band descriptors of a six-person
# cohort. Both are aggregates; neither is published. See the module docstring.
DEMOGRAPHIC_KEYS = {'age_mean', 'age_means', 'gender_counts', 'sex_counts', 'confound_context',
                    'age', 'gender', 'sex', 'education', 'updrs', 'moca', 'medication'}
DESCRIPTOR_KEYS = {'delta_1_4', 'theta_4_8', 'alpha_8_13', 'beta_13_30', 'high_30_45',
                   'filename_task_token_recording_descriptors'}
REFUSED_KEYS = PER_PERSON_KEYS | DEMOGRAPHIC_KEYS | DESCRIPTOR_KEYS

MODELS = {
    'spectral_logistic': {
        'label': 'Relative-spectrum logistic regression',
        'inputs': 'EEG only',
        'excluded_from_model_comparisons': False,
    },
    'demographics_only': {
        'label': 'Age and sex only',
        'inputs': 'no EEG',
        'excluded_from_model_comparisons': True,
        'why_here': ('A confound comparator, not an EEG model. It shows what this cohort can be '
                     'separated by without any brain signal, and it never enters a model ranking.'),
    },
}


def metric_block(row, audited):
    """One model's published numbers, taken from the result and checked against the replay."""
    for key, name in (('balanced_accuracy', 'balanced_accuracy'), ('macro_f1', 'macro_f1'),
                      ('auroc', 'roc_auc')):
        require(row[key] == audited['metrics'][name],
                f'{row["model"]}: {key} disagrees with the independent audit')
    lower, upper = row['balanced_accuracy_descriptive_95']
    replayed = audited['descriptive_stratified_bootstrap_95']['balanced_accuracy']
    require([lower, upper] == replayed, f'{row["model"]}: interval disagrees with the audit')
    return {
        'mean_balanced_accuracy': row['balanced_accuracy'],
        'balanced_accuracy_bootstrap_95': [lower, upper],
        'macro_f1': row['macro_f1'],
        'auroc': row['auroc'],
    }


def clinical(record):
    results, _ = pinned(record['results'], 'ds004584 results')
    audit, _ = pinned(record['numericalAudit'], 'ds004584 audit')
    require(audit['status'] == 'pass' and audit['failed_check'] is None, 'ds004584: audit did not pass')
    require(all(c['pass'] for c in audit['checks'].values()), 'ds004584: a named check did not pass')
    agg = audit['aggregate']
    rows = [r for r in results['results'] if r['dataset'].startswith('OpenNeuro ds004584')]
    require({r['model'] for r in rows} == set(MODELS), 'ds004584: unexpected model set')
    require(len(rows) == agg['models'], 'ds004584: model count disagrees with the audit')
    require(all(r['people'] == agg['people'] for r in rows), 'ds004584: cohort size disagrees with the audit')
    require(record['comparator']['id'] in MODELS, 'ds004584: the comparator is not one of the models')
    require(MODELS[record['comparator']['id']]['excluded_from_model_comparisons'],
            'ds004584: the manifest names a comparator that is not marked excluded')

    models = []
    for row in rows:
        shape = MODELS[row['model']]
        audited = agg['audited_results'][row['model']]
        models.append({'id': row['model'], **{k: v for k, v in shape.items()},
                       **metric_block(row, audited)})
    require(sum(m['excluded_from_model_comparisons'] for m in models) == 1,
            'ds004584: exactly one row is the confound comparator')

    return {
        'id': 'ds004584', 'dataset': rows[0]['dataset'],
        'question': 'can resting-state EEG separate a clinical group from controls, and how much of that is age and sex',
        'classes': 2, 'chance_level': 0.5, 'metric': 'balanced_accuracy',
        'evaluation_unit': rows[0]['evaluation_unit'],
        'cohort': {
            'people': agg['people'],
            'composition': '100 people with Parkinson\'s disease and 49 controls, one site',
            'folds': agg['folds'],
            'windows': agg['windows'],
            'selection': 'five stratified participant folds; every person is held out exactly once, '
                         'and all of a person\'s windows stay together',
        },
        'models': models,
        'method': {
            'features': '60 named channels shared by four source layouts; first 120 seconds; 30 disjoint '
                        'four-second windows; log relative power in five bands spanning 1-45 Hz',
            'aggregation': '300 features averaged within each person, so the classifier sees one vector '
                           'per person rather than 4,470 independent examples',
            'classifier': 'training-fold-only StandardScaler and a fixed balanced logistic regression (C=1)',
            'tuning': 'one split seed, no held-out tuning',
            'interval_kind': 'descriptive stratified participant bootstrap, 2,000 resamples; descriptive '
                             'because the cross-validation training folds overlap',
        },
        'claim_boundary': record['claimBoundary'],
        'independent_audit': {
            'replayed': f'{agg["raw_people_checked"]} recordings and {agg["raw_windows_checked"]} spectral '
                        'windows with a separate FFT, all classifiers refit',
            'maximum_metric_difference': audit['checks']['metrics_bootstrap_and_result_hashes']['maximum_metric_difference'],
            'maximum_feature_difference': audit['checks']['independent_numpy_fft_features']['maximum_absolute_difference'],
        },
        'rights': rights(record),
    }


def status_only(record, results):
    """A source with no score: what was checked, what is missing, and why nothing is published."""
    entry = {'id': record['id'], 'name': record['name'], 'status': 'status_only',
             'scores_published': False, 'reason': record['reason'],
             'rights': {k: record[k] for k in ('source', 'license', 'licenseUrl', 'attribution') if k in record},
             'verification': record['verification']}
    if record['id'] == 'ds004902':
        hold, _ = pinned(record['holdRecord'], 'ds004902 hold')
        require(hold['new_held_out_scores_generated'] is False, 'ds004902: the hold record reports scores')
        require(hold['status'] == 'BLOCKED_SOURCE_WAVEFORM_CONTRACT', 'ds004902: unexpected hold status')
        entry['source_defect'] = {
            'files_with_short_payloads': hold['waveform_length_mismatches'],
            'affected_task_counts': hold['affected_task_counts'],
            'declared_duration_seconds': hold['declared_duration_seconds'],
            'complete_frame_duration_range_seconds': hold['complete_frame_duration_range_seconds'],
            'source_identity': hold['source_identity_status'],
            'reader_ruled_out': hold['header_reader_status'],
            'redownload_would_help': hold['same_object_redownload_useful'],
        }
    if record['id'] == 'lfame':
        audit, _ = pinned(record['descriptiveAudit'], 'lfame descriptive audit')
        require(audit['status'] == 'pass', 'lfame: descriptive audit did not pass')
        counts = results['lfame']
        require(counts['files'] == audit['raw_files_verified'], 'lfame: file count disagrees with the audit')
        require(counts['windows'] == audit['complete_four_second_windows'], 'lfame: window count disagrees')
        require(counts['classification_results'] is False, 'lfame: a classifier result appeared')
        entry['described'] = {'people': counts['people'], 'recordings': counts['files'],
                              'complete_windows': counts['windows'],
                              'endpoint': counts['endpoint'],
                              'numbers_published': False}
    return entry


# The integrity record labels one source by its subject range ("lfame-sub003-008").
# That is a participant token, and the export guard rejects it; it is also not a
# name a reader needs. Each source is published under its dataset name.
INTEGRITY_NAMES = {'ds004584': 'OpenNeuro ds004584', 'ds004902': 'OpenNeuro ds004902',
                   'lfame-sub003-008': 'L-FAME six-person expansion'}


def acquisition(manifest):
    record, _ = pinned(manifest['acquisitionIntegrity'], 'acquisition integrity')
    require(record['status'] == 'PASS', 'acquisition integrity did not pass')
    sources = []
    for s in record['sources']:
        require(s['passed'] and s['failed_files'] == 0, f'{s["source"]}: integrity check failed')
        require(s['verified_files'] == s['expected_files'] and s['verified_bytes'] == s['expected_bytes'],
                f'{s["source"]}: counts disagree')
        require(s['source'] in INTEGRITY_NAMES, f'{s["source"]}: no published name for this source')
        sources.append({'source': INTEGRITY_NAMES[s['source']], 'files': s['verified_files'],
                        'bytes': s['verified_bytes']})
    return {'checked_at': record['checked_at'][:10], 'scope': record['scope'], 'sources': sources}


def scrub_check(value, trail='$'):
    """Refuse any per-person, demographic or withheld-descriptor field."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS, f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    published = next(s for s in manifest['sources'] if s['id'] == 'ds004584')
    results, _ = pinned(published['results'], 'batch results')

    clinical_results, status, included = {}, [], []
    for record in manifest['sources']:
        if record['decision'] == 'aggregate_preview':
            require(approved(record), f'{record["id"]}: approval record is incomplete')
            clinical_results[record['id']] = clinical(record)
            included.append(record['id'])
        else:
            require(record['decision'] == 'status_only', f'{record["id"]}: unknown decision')
            status.append(status_only(record, results))

    payload = {
        'schema_version': 'bci-report-clinical-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': ('balanced accuracy and macro F1 are proportions in [0,1] (multiply by 100 for '
                         'percent); AUROC is dimensionless'),
        'scope': ('A clinical research comparison and three holds. Nothing here extends the eight-protocol '
                  'matrix, the deployment topics or the 2026-09-22 evidence update, and no two results '
                  'share a ranking.'),
        'medical_disclaimer': ('Research results on a public data set. Not a diagnosis, not diagnostic '
                               'accuracy, and not a medical device or medical advice.'),
        'results': clinical_results,
        'status_only': status,
        'holds': manifest['holds'],
        'not_published': manifest['notPublished'],
        'acquisition_integrity': acquisition(manifest),
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included},
    }
    scrub_check(payload)
    validate_public(payload)
    return payload, [s['id'] for s in manifest['sources'] if s['decision'] != 'aggregate_preview']


def inputs_available():
    """Whether the pinned research inputs are on this machine; see export_evidence_update."""
    manifest = json.loads(MANIFEST.read_bytes())
    refs = [manifest['acquisitionIntegrity']]
    for s in manifest['sources']:
        refs += [s[k] for k in ('results', 'numericalAudit', 'holdRecord', 'descriptiveAudit') if k in s]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    payload, _ = build(MANIFEST.read_bytes())
    return (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload, held = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'included': payload['provenance']['included'], 'status_only': held,
        'checks': ['pinned result, audit, hold and integrity bytes',
                   'published metrics equal the independent replay',
                   'complete approval record for the published source',
                   'per-person fields refused',
                   'clinical demographic profile refused',
                   'withheld six-person band descriptors refused',
                   'exactly one row marked as the confound comparator',
                   'no private paths or participant identifiers'],
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
