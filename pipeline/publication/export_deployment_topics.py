"""Release the independently audited deployment topics as aggregate-only JSON.

This is an explicit publication boundary, not a raw benchmark-results exporter.
The manifest pins the reviewed evidence; new runs need their own review before
they can enter this release. The original experiment matrix remains unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import statistics

from export_snapshot import approved, validate_public

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20260920'
MANIFEST = REVIEW / 'topic-release-manifest.json'
OUTPUTS = (PROJECT / 'site/src/data/deployment-topics.json',
           PROJECT / 'site/public/data/deployment-topics.json')
EXPORT_AUDIT = REVIEW / 'topic-export-audit.json'

TOPICS = {
    'dry-vs-wet': ['wearable-sensor-transfer'],
    'on-the-move': ['mobile-ssvep-5s', 'mobile-ssvep-2s', 'mobile-erp'],
    'calibration-budget': ['wearable-calibration', 'wearable-etrca-calibration'],
    'does-pretraining-help': ['pretraining-attribution-fixed',
                             'pretraining-attribution-selected', 'fixed-classical-control'],
}
ROW_FIELDS = set(('adapter_status baseline_window_seconds calibration_blocks channels condition '
    'confidence_interval_95 dataset_id encoder_seed_count encoder_status feature_window_seconds '
    'fixed_covariance_shrinkage head_selection id initialization labeled_target_trials metric '
    'modality model participants protocol_amendment protocol_id seed_count source_sensor '
    'speed_m_s target_sensor test_blocks track training_regime trials value window_seconds').split())
CONTRAST_FIELDS = set(('comparison dataset_id difference interpretation modality model '
    'paired_participant_bootstrap_95 participants track unit').split())
SEED_FIELDS = set(('model protocol backend participants trials runs mean_balanced_accuracy '
    'sample_standard_deviation minimum maximum full_range uncertainty_kind comparability_note '
    'input_audit_digests').split())
SEED_RUN_FIELDS = {'seed', 'balanced_accuracy', 'macro_f1', 'prediction_sha256', 'verification_sha256'}
EXISTING_DATASETS = {'ds003810', 'physionet-eegmat-1.0.0', 'ds005383', 'ds006593',
                     'eesm19-scalp-sleep', 'BETA'}
SEED_DATASETS = {'ds005383': 'ds005383', 'ds006593': 'ds006593',
                 'eesm19-scalp-sleep': 'eesm19-scalp-sleep',
                 'BETA-posterior4': 'BETA', 'BETA-posterior8': 'BETA'}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_fields(record, fields, label):
    require(not set(record) - fields, f'Unknown {label} fields: {set(record) - fields}')
    return copy.deepcopy(record)


def proportion(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1, f'Invalid {label}')


def close(actual, expected, label):
    require(math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12), f'Mismatch: {label}')


def build_export(source_bytes, audit, rights, base_manifest, manifest):
    """Pure validation boundary; callers verify all input-file hashes first."""
    source_sha = sha_bytes(source_bytes)
    require(source_sha == manifest['inputs']['aggregate']['sha256'], 'Unreviewed aggregate bytes')
    source = json.loads(source_bytes)
    require(audit['status'] == 'pass' and audit['aggregate_sha256'] == source_sha,
            'Independent audit is missing, failed, or stale')
    require(audit['prior_reviewed_rows_and_contrasts_unchanged'] is True,
            'Prior scientific review does not cover these rows')
    require(source['status'] == 'audited_aggregate_candidate_for_publisher_review',
            'Source is not the reviewed candidate')
    require(manifest['decision'] == 'publish_aggregate_topics', 'Topic release is not approved')

    new_rights = {r['id']: r for r in rights['datasets']}
    base_rights = {r['id']: r for r in base_manifest['datasets']}
    allowed_datasets = set(manifest['approved_dataset_ids'])
    citations = copy.deepcopy(source['dataset_citations'])
    for citation in citations:
        review = new_rights[citation['source_review_id']]
        require(review['decision'] == 'candidate_for_aggregate_benchmark_publication',
                f'Dataset review revoked: {citation["id"]}')
        require(citation['id'] in allowed_datasets, 'Dataset outside release manifest')
        require(citation['decision'] == review['decision'], 'Citation review mismatch')
        # The reviewed representation and conditions must survive publication.
        identity = {k: v for k, v in review['identity'].items() if k != 'local_path'}
        require(citation['identity'] == identity, 'Citation identity differs from rights review')
        require(citation['publication_conditions'] == review['publication_conditions'],
                'Dataset publication conditions changed')
        citation['decision'] = 'aggregate_publication_only'
    for dataset_id in sorted(EXISTING_DATASETS):
        record = base_rights[dataset_id]
        require(approved(record), f'Existing source review revoked: {dataset_id}')
        citations.append({
            'id': dataset_id, 'source_review_id': dataset_id,
            'decision': 'aggregate_publication_only',
            'identity': {'title': record['name'], 'version': record['version'],
                         'license': record['license'], 'license_url': record['licenseUrl'],
                         'dataset_citation': record['attribution'],
                         'representation': record['provenance']},
            'primary_sources': list(dict.fromkeys([record['source']] + record['reviewBasis'])),
            'publication_conditions': [record['rightsRestrictions'],
                'Cohort aggregates only; no participant records, EEG signals, or individual predictions.'],
        })
    require({c['id'] for c in citations} == allowed_datasets, 'Incomplete dataset citations')
    require(len(citations) == len(allowed_datasets), 'Duplicate dataset citations')

    tracks = {t for group in TOPICS.values() for t in group}
    models = set(manifest['approved_model_ids'])
    rows = [checked_fields(r, ROW_FIELDS, 'row') for r in source['rows']]
    require(len(rows) == audit['aggregate_rows'] == manifest['counts']['measurements'],
            'Wrong measurement count')
    require(len({r['id'] for r in rows}) == len(rows), 'Duplicate measurement ID')
    require({r['track'] for r in rows} == tracks, 'Unknown or missing track')
    for row in rows:
        require(row['model'] in models, f'Unapproved model: {row["model"]}')
        require(row['dataset_id'] in allowed_datasets, 'Unapproved row dataset')
        require(row['metric'] in ('participant_mean_balanced_accuracy', 'participant_mean_roc_auc'),
                'Unknown metric')
        proportion(row['value'], 'score')
        if row.get('confidence_interval_95') is not None:
            lo, hi = row['confidence_interval_95']
            proportion(lo, 'CI lower'); proportion(hi, 'CI upper')
            require(lo <= hi, 'Reversed confidence interval')
        require(row['participants'] >= 2 and row['trials'] >= row['participants'],
                'Invalid aggregate cohort')
    contrasts = [checked_fields(r, CONTRAST_FIELDS, 'contrast') for r in source['paired_contrasts']]
    require(len(contrasts) == audit['paired_contrasts'] == manifest['counts']['paired_contrasts'],
            'Wrong contrast count')
    for contrast in contrasts:
        require(contrast['track'] in tracks and contrast['model'] in models, 'Unknown contrast')
        require(math.isfinite(contrast['difference']) and -1 <= contrast['difference'] <= 1,
                'Invalid contrast difference')
        lo, hi = contrast['paired_participant_bootstrap_95']
        require(-1 <= lo <= hi <= 1, 'Invalid contrast confidence interval')
        if 'dataset_id' in contrast:
            require(contrast['dataset_id'] in allowed_datasets, 'Unapproved contrast dataset')

    seeds = [checked_fields(s, SEED_FIELDS, 'seed summary') for s in source['seed_sensitivity']]
    require(len(seeds) == audit['seed_protocols'] == manifest['counts']['seed_protocols'],
            'Wrong seed protocol count')
    require({s['protocol'] for s in seeds} == set(SEED_DATASETS), 'Unknown seed protocol')
    audited_runs = {(r['protocol'], r['seed']): r for r in audit['seed_runs']}
    for summary in seeds:
        require(summary['model'] == 'eegnet' and summary['backend'] == 'mps',
                'Seed summaries mix unreviewed models or backends')
        require(len(summary['runs']) == 3 and
                {r['seed'] for r in summary['runs']} == {20260919, 20260920, 20260921},
                'Wrong seed set')
        for run in summary['runs']:
            checked_fields(run, SEED_RUN_FIELDS, 'seed run')
            observed = audited_runs[(summary['protocol'], run['seed'])]
            require(observed['pass'] is True and observed['backend'] == summary['backend'],
                    'Seed run failed or backend mismatch')
            require((observed['participants'], observed['trials']) ==
                    (summary['participants'], summary['trials']), 'Seed cohort mismatch')
            for metric in ('balanced_accuracy', 'macro_f1'):
                proportion(run[metric], metric)
                close(run[metric], observed[metric + '_recomputed'], 'audited seed metric')
        values = [r['balanced_accuracy'] for r in summary['runs']]
        for field, value in (('mean_balanced_accuracy', statistics.mean(values)),
                             ('sample_standard_deviation', statistics.stdev(values)),
                             ('minimum', min(values)), ('maximum', max(values)),
                             ('full_range', max(values) - min(values))):
            close(summary[field], value, field)

    result = {
        'schema_version': 'bci-report-public-deployment-topics-v1',
        'release_id': manifest['release_id'], 'generated_at': source['generated_at'],
        'status': 'reviewed_aggregate_research_preview',
        'metric_units': source['metric_units'],
        'scope': 'Personal noncommercial research; aggregate results and methods only.',
        'coverage': {'topics': len(TOPICS), 'measurements': len(rows),
                     'paired_contrasts': len(contrasts), 'seed_protocols': len(seeds),
                     'seed_runs': sum(len(s['runs']) for s in seeds),
                     'note': 'Measurements are protocol-specific rows, not independent studies or a global ranking.'},
        'topics': [{'id': k, 'tracks': v,
                    'measurements': sum(r['track'] in v for r in rows)} for k, v in TOPICS.items()],
        'rows': rows, 'paired_contrasts': contrasts, 'seed_sensitivity': seeds,
        'dataset_citations': citations, 'method_references': source['method_references'],
        'interpretation_limits': source['interpretation_limits'],
        'provenance': {'reviewed_aggregate_sha256': source_sha,
                       'independent_auditor_sha256': audit['auditor_sha256'],
                       'review_date': manifest['reviewed_at'],
                       'evidence_sha256': [item['sha256'] for item in source['evidence_digests']]},
    }
    validate_public(result)
    return result


def load_reviewed_export():
    manifest = json.loads(MANIFEST.read_text())
    inputs = {}
    for name, record in manifest['inputs'].items():
        payload = (PROJECT / record['path']).read_bytes()
        require(sha_bytes(payload) == record['sha256'], f'Reviewed input changed: {name}')
        inputs[name] = payload if name == 'aggregate' else json.loads(payload)
    return build_export(inputs['aggregate'], inputs['audit'], inputs['rights'],
                        inputs['base_manifest'], manifest)


def serialized_export():
    return (json.dumps(load_reviewed_export(), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    payload = serialized_export()
    result = json.loads(payload)
    for path in OUTPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(payload)
        temporary.replace(path)
    audit = {'status': 'pass', 'release_id': result['release_id'],
             'export_sha256': sha_bytes(payload), 'coverage': result['coverage'],
             'checks': ['pinned reviewed inputs', 'passing independent scientific audit',
                        'explicit dataset and model approvals', 'metric and cohort validation',
                        'same-backend seed summaries recomputed', 'aggregate-only privacy scan',
                        'identical page-data and download copies']}
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
