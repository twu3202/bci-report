"""Release the 2026-09-22 evidence batch as aggregate-only JSON.

A separate publication boundary from the 2026-09-20 release, on purpose: that
release's manifests never covered this batch, and extending them would have made
it look as though they had. Each source here carries its own editorial decision
in research/publication_review_20260922/evidence-release-manifest.json, and only
a source whose decision is `aggregate_preview` reaches the output.

What is deliberately dropped from the reviewed summaries:
- per-person distribution fields (min, max, median, quartiles). With ten or
  nineteen people, a minimum is one person's score, which is exactly what the
  site says it does not publish;
- summed confusion matrices, private artifact paths and input inventories;
- the LoRA smoke test's elapsed seconds, which must not be read as a training
  cost. Its parameter counts are published; its runtime is not.

    python3 pipeline/publication/export_evidence_update.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from export_snapshot import approved, validate_public

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20260922'
MANIFEST = REVIEW / 'evidence-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'evidence-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/evidence-update.json',
           PROJECT / 'site/public/data/evidence-update.json')

# Keys that describe individual people when the cohort is ten or nineteen.
PER_PERSON_KEYS = {'min', 'max', 'median', 'p25', 'p75', 'confusion_matrix_sum',
                   'private_artifacts', 'elapsed_seconds'}
RIGHTS_FIELDS = ('name', 'task', 'source', 'version', 'license', 'licenseUrl', 'attribution',
                 'privacyReview', 'reviewedAt', 'reviewBasis')
PHANTOM_ORDER = ('Brain', 'Eyes', 'Walking', 'Neck', 'Facial', 'All')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned(ref, label):
    """Read a reviewed input, refusing it unless it is byte-for-byte the pinned one."""
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return json.loads(raw), digest


def replayed(record, label):
    """The summary, provided its independent replay passed against these exact bytes."""
    summary, summary_sha = pinned(record['summary'], label + ' summary')
    audit, _ = pinned(record['numericalAudit'], label + ' audit')
    status = audit.get('status') or audit.get('independent_replay', {}).get('status')
    require(status in ('pass', 'complete_replay_verified'), f'{label}: replay status {status!r}')
    if 'summary_sha256' in audit:
        require(audit['summary_sha256'] == summary_sha, f'{label}: replay checked a different summary')
    return summary, audit


def interval(bootstrap):
    return [bootstrap['lower'], bootstrap['upper']]


def rights(record):
    return {k: record[k] for k in RIGHTS_FIELDS if k in record}


def eesm23(record):
    s, audit = replayed(record, 'eesm23')
    res, cohort, modes = s['results'], s['cohort'], s['modalities']
    # Coverage comes from the independent replay, which verified it; the summary must agree.
    require(audit['paired_cached_rows_verified'] == cohort['paired_fully_finite_rows'], 'eesm23: epoch count disagrees')
    require(audit['source_rows_verified'] == cohort['source_rows'], 'eesm23: source epoch count disagrees')
    require(audit['retained_people_verified'] == cohort['people'], 'eesm23: people count disagrees')
    paired = res['paired_scalp_minus_in_ear']

    def config(key, channels, **extra):
        return {'id': key, 'channels': channels, **extra,
                'mean_balanced_accuracy': res[key]['balanced_accuracy_distribution']['mean'],
                'balanced_accuracy_bootstrap_95': interval(res[key]['balanced_accuracy_bootstrap_95_percent']),
                'mean_macro_f1': res[key]['macro_f1_distribution']['mean']}

    return {
        'id': 'eesm23', 'dataset': s['dataset'], 'protocol_id': s['protocol_id'],
        'question': 'paired in-ear versus scalp sleep staging on identical epochs',
        'classes': 5, 'chance_level': 0.2, 'metric': 'person_mean_balanced_accuracy',
        'cohort': {
            'people': audit['retained_people_verified'],
            'nights_used': audit['retained_nights_verified'], 'nights_in_source': audit['source_nights_verified'],
            'epochs_used': audit['paired_cached_rows_verified'], 'epochs_in_source': audit['source_rows_verified'],
            'coverage_fraction': audit['paired_epoch_coverage_fraction'],
            'selection': 'paired complete-case: both configurations use the identical epochs',
        },
        'configurations': [
            config('in_ear', modes['in_ear']['channels'], channel_note=modes['in_ear']['interpretation']),
            config('scalp', modes['scalp']['classifier_channels'],
                   excluded_file_slots=modes['scalp']['excluded_file_slots'],
                   channel_note=modes['scalp']['interpretation']),
        ],
        'paired_difference': {
            'comparison': 'scalp minus in-ear',
            'mean': paired['delta_distribution']['mean'],
            'bootstrap_95': interval(paired['mean_delta_bootstrap_95_percent']),
            'interval_kind': 'descriptive person bootstrap; not a population guarantee',
            'people_scalp_higher': paired['people_scalp_higher'],
            'people_in_ear_higher': paired['people_in_ear_higher'],
            'people_tied': paired['people_tied'],
        },
        'method': s['method'],
        'limitations': s['limitations'],
        'rights': rights(record),
    }


def alphawaves(record):
    s, _ = replayed(record, 'alphawaves')
    res, cfg = s['results'], s['configurations']
    paired = res['paired_all16_minus_posterior4']

    def config(key):
        return {'id': key, 'channels': cfg[key]['channels'], 'evidence_state': cfg[key]['evidence_state'],
                'mean_balanced_accuracy': res[key]['balanced_accuracy_distribution']['mean'],
                'balanced_accuracy_bootstrap_95': interval(res[key]['balanced_accuracy_bootstrap_95_percent']),
                'mean_macro_f1': res[key]['macro_f1_distribution']['mean']}

    return {
        'id': 'alphawaves', 'dataset': s['dataset'], 'protocol_id': s['protocol_id'],
        'question': 'eyes open versus eyes closed with four posterior versus all sixteen electrodes',
        'classes': 2, 'chance_level': 0.5, 'metric': 'person_mean_balanced_accuracy',
        'cohort': {'people': s['cohort']['selected_recordings'],
                   'recordings_in_source': s['cohort']['source_recordings_preserved'],
                   'episodes': s['cohort']['epochs'],
                   'selection': s['cohort']['excluded_recording']},
        'configurations': [config('posterior4'), config('all16')],
        'paired_difference': {
            'comparison': 'all sixteen minus posterior four',
            'mean': paired['delta_distribution']['mean'],
            'bootstrap_95': interval(paired['mean_delta_bootstrap_95_percent']),
            'interval_kind': 'descriptive person bootstrap; not a population guarantee',
            'people_all16_higher': paired['people_all16_higher'],
            'people_posterior4_higher': paired['people_posterior4_higher'],
            'people_tied': paired['people_tied'],
        },
        'method': s['method'],
        'limitations': s['limitations'],
        'rights': rights(record),
    }


def phantom(record):
    s, _ = replayed(record, 'phantom')
    require(s['independent_replay']['failed_check_count'] == 0, 'phantom: replay recorded failures')
    require(set(s['conditions']) == set(PHANTOM_ORDER), 'phantom: unexpected conditions')

    # `value`, not `median`: the scrub refuses any key named like a per-person
    # percentile, and keeping that rule strict is worth one indirection. What
    # the value is gets stated once, in `summary_statistic` below.
    def metric(block):
        return {'value': block['median_across_fold_source_medians'],
                'fold_range': [block['minimum_fold_source_median'], block['maximum_fold_source_median']]}

    return {
        'id': 'phantom', 'dataset': s['dataset'], 'scope': s['scope'],
        'unit': 'one physical head phantom; no human participants',
        'model': s['model'], 'split': s['split'], 'inference': s['inference'],
        'summary_statistic': 'median across folds of the within-fold median across ten brain sources',
        'conditions': [{'condition': c, 'folds': s['conditions'][c]['fold_count'],
                        'sources_per_fold': s['conditions'][c]['sources_per_fold'],
                        'signed_correlation_r': metric(s['conditions'][c]['heldout_signed_pearson_r']),
                        'predictive_r_squared': metric(s['conditions'][c]['heldout_predictive_r_squared'])}
                       for c in PHANTOM_ORDER],
        'reading': ('Neither column is accuracy. Predictive R² is not bounded below by zero: a negative '
                    'value means the prediction is further from the true source than a constant would be.'),
        'limitations': s['limitations'],
        'rights': rights(record),
    }


def roadmap(manifest):
    plan = manifest['roadmap']
    require(plan['status'] == 'planned', 'roadmap status must stay "planned" until real-data scores exist')
    check, _ = pinned(plan['engineeringCheck'], 'lora check')
    review = json.loads((PROJECT / plan['independentReview']['path']).read_bytes())
    require(check['status'] == 'pass', 'lora check did not pass')
    require(review['status'].startswith('pass'), 'lora review did not pass')
    passed = {
        'identical output at zero adapter initialization': check['zero_initialization_max_error'] == 0,
        'frozen encoder weights unchanged after updates': check['frozen_parameters_unchanged'] is True,
        'finite, nonzero adapter gradients in every block': all(g['minimum_b_gradient_norm'] > 0 for g in check['gradient_checks']),
        'exact adapter save and reload': check['adapter_reload_max_error'] == 0,
        'exact merged-weight equivalence': check['merged_output_max_error'] == 0,
    }
    require(all(passed.values()), f'lora check: {[k for k, v in passed.items() if not v]}')
    return {
        'id': 'peft', 'status': 'planned', 'real_eeg_results_available': False,
        'description': plan['allowedDescription'],
        'engineering_check': {
            'signals': 'synthetic', 'model': check['model'], 'target': check['target'],
            'rank': check['rank'], 'alpha': check['alpha'],
            'base_encoder_parameters': check['base_encoder_parameters'],
            'adapter_parameters': check['adapter_parameters'],
            'adapter_fraction': check['adapter_fraction_of_base_parameters'],
            'adapter_float32_bytes': check['adapter_fp32_tensor_bytes'],
            'binary_head_parameters_if_added': check['binary_linear_head_parameters_if_added'],
            'checks_passed': sorted(passed),
            'not_established': check['limitations'],
            'review': review['status'],
        },
    }


EXTRACT = {'eesm23': eesm23, 'alphawaves': alphawaves, 'phantom': phantom}


def scrub_check(value, trail='$'):
    """Refuse any per-person or private field that slipped through an extractor."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in PER_PERSON_KEYS, f'per-person or private field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    results, included, held = {}, [], []
    for record in manifest['sources']:
        if record['decision'] == 'aggregate_preview':
            require(approved(record), f'{record["id"]}: approval record is incomplete')
            results[record['id']] = EXTRACT[record['id']](record)
            included.append(record['id'])
        else:
            held.append({'id': record['id'], 'decision': record['decision']})
    payload = {
        'schema_version': 'bci-report-evidence-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': ('balanced accuracy and differences are proportions in [0,1] (multiply by 100 for '
                         'percent or percentage points); correlation r and predictive R² are dimensionless'),
        'scope': ('Separate questions on separate data. Nothing here extends the eight-protocol matrix or '
                  'the four deployment topics, and no two results share a ranking.'),
        'results': results,
        'roadmap': {'peft': roadmap(manifest)},
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included},
    }
    scrub_check(payload)
    validate_public(payload)
    return payload, held


def inputs_available():
    """Whether the pinned research inputs are on this machine.

    They are not in the public repository: the research handoffs they sit in
    carry private paths and unapproved results, so they stay local. A clone can
    still verify the published file against the committed audit hash; only the
    maintainer's checkout can re-derive it from the pinned inputs.
    """
    manifest = json.loads(MANIFEST.read_bytes())
    refs = [manifest['roadmap']['engineeringCheck'], manifest['roadmap']['independentReview']]
    for s in manifest['sources']:
        refs += [s[k] for k in ('summary', 'numericalAudit') if k in s]
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
        'included': payload['provenance']['included'], 'held_or_excluded': held,
        'checks': ['pinned summary and audit bytes', 'independent replay passed against the same summary',
                   'complete approval record per included source', 'per-person fields refused',
                   'no private paths or participant identifiers', 'roadmap status fixed at planned'],
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
