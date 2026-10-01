"""Release the LaBraM adaptation batch (reviewed 2026-10-01) as aggregate-only JSON.

One question: when a foundation model meets new people on a known task, which
update is worth trying — training only a classification head, the last encoder
block as well, or a rank-4 LoRA adapter? The three arms share the checkpoint,
folds, initial heads, batch orders, five-epoch recipe and three seeds, so their
differences are paired within each person.

Its own publication boundary, as with every batch. What this export refuses:
- per-person and per-fold values, and which people were helped or harmed;
- memory figures. The per-seed records hold allocator samples and a
  process-wide high-water mark: lower bounds, not per-method peaks;
- any figure from the cross-day experiment. It ran on a source whose
  2026-09-20 editorial hold stands, so it is listed as status only;
- any mean or interval the independent replay did not reproduce.

And what it adds, deliberately: a pointer to the core matrix's frozen LaBraM
readout on the same people and folds. The head-only arm here is a short
gradient-trained head; without the pointer a reader would take its score for
the best a frozen encoder can do. The pointer carries no number — the page reads
that one from experiments.json, where it was published.

    python3 pipeline/publication/export_adaptation_update.py
"""
from __future__ import annotations

import json
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261001'
MANIFEST = REVIEW / 'adaptation-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'adaptation-export-audit.json'
SNAPSHOT = PROJECT / 'site/src/data/mvp.json'
OUTPUTS = (PROJECT / 'site/src/data/adaptation-update.json',
           PROJECT / 'site/public/data/adaptation-update.json')

REFUSED_KEYS = PER_PERSON_KEYS | {
    'q1', 'q3', 'range', 'person_metrics_sha256', 'run_root',
    'sampled_max_mps_allocated_bytes', 'sampled_max_mps_driver_bytes',
    'cumulative_process_rss_high_water_bytes',
}
PEOPLE = 36
ARMS = {
    'frozen': {'label': 'Head only',
               'updates': 'a linear classification head; the whole encoder stays frozen'},
    'last-block': {'label': 'Last block + head',
                   'updates': 'the final transformer block and the same head; every earlier part stays frozen'},
    'lora-r4': {'label': 'LoRA rank 4 + head',
                'updates': 'rank-4 adapters on all twelve fused QKV weights and the same head; '
                           'the original encoder weights stay frozen'},
}
CONTRASTS = {
    'lora-r4_minus_frozen': ('lora-r4', 'frozen'),
    'last-block_minus_frozen': ('last-block', 'frozen'),
    'lora-r4_minus_last-block': ('lora-r4', 'last-block'),
}
METRICS = ('balanced_accuracy', 'macro_f1')
SEED_MEAN_KEY = {'balanced_accuracy': 'mean_balanced_accuracy', 'macro_f1': 'mean_macro_f1'}


def seed_records(record, protocol_sha, summary):
    """Every seed passed its own replay, on the bytes the aggregate says it used."""
    listed = {a['seed']: a for a in summary['input_audits']}
    out = {}
    for s in record['seeds']:
        seed_summary, seed_sha = pinned(s['summary'], f'seed {s["seed"]} summary')
        seed_audit, seed_audit_sha = pinned(s['numericalAudit'], f'seed {s["seed"]} audit')
        require(seed_audit['status'] == 'pass', f'seed {s["seed"]}: replay did not pass')
        require(seed_audit['summary_sha256'] == seed_sha, f'seed {s["seed"]}: replay checked a different summary')
        require(seed_summary['protocol_sha256'] == protocol_sha, f'seed {s["seed"]}: another protocol')
        require(seed_summary['completed_fits'] == 15 and seed_summary['people'] == PEOPLE,
                f'seed {s["seed"]}: incomplete')
        require(listed[s['seed']]['summary_sha256'] == seed_sha and listed[s['seed']]['audit_sha256'] == seed_audit_sha,
                f'seed {s["seed"]}: the aggregate was built from different seed files')
        out[s['seed']] = seed_summary
    require(sorted(out) == sorted(summary['seeds']), 'the aggregate and the manifest name different seeds')
    return out


def matrix_reference(ref, protocol, snapshot):
    """Locate the matrix row the page prints beside the head-only arm, and prove it shares the folds."""
    track = next(t for t in snapshot['tracks'] if t['id'] == ref['trackId'])
    rows = [r for r in track['rows'] if r['name'] == ref['model'] and r['mode'] == ref['mode']]
    require(len(rows) == 1, 'matrix reference: expected exactly one row')
    require(protocol['input_identities']['dataset-protocol.json']['sha256'] == track['protocolSha'],
            'matrix reference: the adaptation run used a different dataset protocol from the matrix track')
    require(track['subjects'] == PEOPLE, 'matrix reference: a different cohort')
    return {'file': ref['file'], 'track_id': ref['trackId'], 'model': ref['model'], 'training_mode': ref['mode'],
            'same_people_and_folds': True, 'paired_with_these_arms': False, 'why': ref['why']}


def adaptation(record, snapshot):
    protocol, protocol_sha = pinned(record['protocol'], 'adaptation protocol')
    readiness, _ = pinned(record['readinessReview'], 'readiness review')
    summary, summary_sha = pinned(record['summary'], 'three-seed summary')
    audit, _ = pinned(record['numericalAudit'], 'three-seed audit')
    require(readiness['status'].startswith('pass'), 'the protocol was not reviewed before scoring')
    require(readiness['identity_checks']['primary_seed_output_directory_absent_at_review'] is True,
            'the readiness review saw scores')
    require(summary['protocol_sha256'] == protocol_sha == audit['protocol_sha256'], 'protocol identity differs')
    require(audit['status'] == 'pass' and audit['summary_sha256'] == summary_sha,
            'the aggregate replay did not pass on these bytes')
    v = audit['verified']
    require(v['fits'] == summary['completed_fits'] == 45 and v['unique_people'] == summary['unique_people'] == PEOPLE,
            'fit or cohort count differs from the replay')
    require(v['seed_average_before_person_bootstrap'] and v['all_seed_audits_precede_aggregation']
            and v['exact_fraction_help_harm_tie'], 'the replay did not confirm the aggregation order')
    seeds = seed_records(record, protocol_sha, summary)
    require(protocol['selection'].startswith('none'), 'the protocol allowed selection')

    arms = []
    for arm, shape in ARMS.items():
        a = summary['arms'][arm]
        require(a['balanced_accuracy']['mean'] == audit['aggregate_balanced_accuracy'][arm]
                and a['macro_f1']['mean'] == audit['aggregate_macro_f1'][arm], f'{arm}: differs from the replay')
        metrics = {}
        for metric in METRICS:
            block = a[metric]
            per_seed = []
            for seed in summary['seeds']:
                value = block['per_seed_means'][str(seed)]
                require(value == seeds[seed]['arms'][arm][SEED_MEAN_KEY[metric]],
                        f'{arm}/{metric}/{seed}: differs from the audited seed summary')
                per_seed.append({'seed': seed, 'mean': value})
            metrics[metric] = {'mean': block['mean'], 'bootstrap_95': block['descriptive_person_bootstrap_95'],
                               'per_seed_means': per_seed}
        cost = a['cost_for_15_fits']
        arms.append({'id': arm, **shape, 'trainable_parameters': a['trainable_parameters'],
                     'trainable_tensor_bytes': a['trainable_tensor_bytes'], **metrics,
                     'training_seconds_15_fits': cost['training_seconds'],
                     'evaluation_seconds_15_fits': cost['evaluation_seconds']})

    contrasts = {}
    for metric in METRICS:
        contrasts[metric] = []
        for cid, (minuend, subtrahend) in CONTRASTS.items():
            c = summary['paired_contrasts'][metric][cid]
            require(c['helped'] + c['harmed'] + c['tied'] == PEOPLE, f'{metric}/{cid}: counts do not cover the cohort')
            contrasts[metric].append({'id': cid, 'arm': minuend, 'minus': subtrahend, 'mean_change': c['mean_change'],
                                      'bootstrap_95': c['descriptive_person_bootstrap_95'],
                                      'helped': c['helped'], 'harmed': c['harmed'], 'tied': c['tied']})

    lora = protocol['lora']
    return {
        'id': 'eegmat-labram-adaptation',
        'question': 'which update is worth trying when a foundation model meets new people on a known task',
        'protocol_id': protocol['id'], 'stage': protocol['stage'],
        'classes': 2, 'chance_level': 0.5, 'metric': 'balanced_accuracy',
        'generalization': 'new people, same task and recording setup: five participant-disjoint folds',
        'model': {'name': 'LaBraM Base', 'checkpoint_sha256': protocol['checkpoint_sha256'],
                  'pooling': 'mean over patch tokens of the official forward_features'},
        'cohort': {'people': summary['unique_people'], 'two_second_windows': summary['unique_epochs'],
                   'windows_per_person': summary['unique_epochs'] // summary['unique_people'],
                   'folds': protocol['folds'], 'seeds': summary['seeds'], 'fits': summary['completed_fits']},
        'method': {
            'shared': 'within each seed and fold all three arms start from the same head, see the same '
                      'training batches in the same order, and train for the same five epochs',
            'recipe': {'optimizer': protocol['optimizer']['name'], 'learning_rate': protocol['optimizer']['lr'],
                       'weight_decay': protocol['optimizer']['weight_decay'], 'training_epochs': protocol['epochs'],
                       'batch_size': protocol['batch_size'], 'loss': 'unweighted cross entropy'},
            'lora': {'rank': lora['rank'], 'alpha': lora['alpha'], 'dropout': lora['dropout'], 'target': lora['target']},
            'selection': 'none: no hyperparameter search, validation split, early stopping or checkpoint '
                         'selection; the final epoch is scored',
            'signal': 'the matrix recordings resampled to 200 Hz and divided by 100; no fitted scaler',
            'aggregation': summary['aggregation'],
            'interval_kind': summary['uncertainty'],
            'device': 'one Apple-silicon Mac, PyTorch MPS backend; times are this implementation on this device',
        },
        'arms': arms,
        'paired_contrasts': contrasts,
        'matrix_reference': matrix_reference(record['matrixReference'], protocol, snapshot),
        'limitations': summary['limitations'] + [
            'The head-only arm is a short gradient-trained head on unscaled features, not the strongest frozen readout.',
            'LoRA here is an effective-weight parametrization, not an optimized low-rank kernel; its training time '
            'is this implementation, and fewer trainable weights do not by themselves mean less time or memory.',
            'Intervals are descriptive and ignore the dependence created by shared cross-validation models.',
        ],
        'independent_audit': {'seeds_replayed': v['seed_audits'], 'fits': v['fits'],
                              'participant_metric_cells': v['participant_metric_cells'],
                              'paired_contrasts': v['paired_contrasts']},
        'rights': rights(record),
    }


def crossday(record):
    audit, _ = pinned(record['numericalAudit'], 'cross-day audit')
    evidence, _ = pinned(record['sourceEvidence'], 'cross-day source evidence')
    require(audit['status'] == 'pass', 'cross-day: replay did not pass')
    checks = audit['checks']
    people = evidence['selected_dataset']['participants']
    require(checks['source_fit_records_and_checkpoints'] == people, 'cross-day: one source model per person')
    return {
        'id': record['id'], 'name': record['name'], 'status': 'status_only', 'scores_published': False,
        'reason': record['reason'],
        'design': {'people': people, 'recording_days': 2,
                   'calibration_labels': [0, 10, 20, 40],
                   'update_rules': [ARMS[a]['label'] for a in ARMS],
                   'fits': checks['source_fit_records_and_checkpoints'] + checks['target_fit_records_and_checkpoints'],
                   'split': 'train on day A; calibrate on the first labeled trials of day B; test every budget on '
                            'the same later day-B trials'},
        'independent_replay': 'pass',
        'rights': {k: record[k] for k in ('source', 'license', 'licenseUrl', 'attribution')},
    }


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS, f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def build(manifest_bytes, snapshot=None):
    manifest = json.loads(manifest_bytes)
    snapshot = snapshot if snapshot is not None else json.loads(SNAPSHOT.read_text())
    handoff = (PROJECT / manifest['handoff']['path']).read_bytes()
    require(sha(handoff) == manifest['handoff']['sha256'], 'handoff: not the pinned bytes')
    stage, _ = pinned(manifest['stageStatus'], 'stage status')
    results, status, included = {}, [], []
    for record in manifest['sources']:
        if record['decision'] == 'aggregate_preview':
            require(approved(record), f'{record["id"]}: approval record is incomplete')
            require(record['id'] == 'eegmat-labram-adaptation', f'{record["id"]}: no extractor')
            results[record['id']] = adaptation(record, snapshot)
            included.append(record['id'])
        else:
            require(record['decision'] == 'status_only', f'{record["id"]}: unknown decision')
            status.append(crossday(record))
    require(stage['status'] == 'declared_test_batch_complete', 'the research batch is not complete')
    payload = {
        'schema_version': 'bci-report-adaptation-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': 'balanced accuracy and macro F1 are proportions in [0,1]; changes are differences of proportions',
        'scope': ('One fixed five-epoch recipe, three update rules, three seeds, on new people for a task the '
                  'model is adapted to. Not a cross-day, cross-device or cross-dataset result, not a tuned-method '
                  'ranking, and not a row of the eight-protocol matrix.'),
        'supersedes_roadmap': {'file': 'evidence-update.json', 'roadmap_id': 'peft',
                               'note': 'That file still records the roadmap as planned, which was true on '
                                       '2026-09-22; it is a release record and is not rewritten.'},
        'results': results,
        'status_only': status,
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included},
    }
    scrub_check(payload)
    validate_public(payload)
    for entry in status:
        text = json.dumps(entry)
        for field in ('balanced_accuracy', 'macro_f1', 'mean_change', 'bootstrap_95'):
            require(f'"{field}"' not in text, f'{entry["id"]}: a status-only entry carries a score')
    return payload, [s['id'] for s in status]


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    refs = [manifest['handoff'], manifest['stageStatus']]
    for s in manifest['sources']:
        refs += [s[k] for k in ('protocol', 'readinessReview', 'summary', 'numericalAudit', 'sourceEvidence')
                 if k in s]
        refs += [x[k] for x in s.get('seeds', []) for k in ('summary', 'numericalAudit')]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    payload, _ = build(MANIFEST.read_bytes())
    return (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload, status_only = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'included': payload['provenance']['included'], 'status_only': status_only,
        'checks': ['pinned protocol, readiness review, summary, audit and per-seed bytes',
                   'protocol reviewed before any score existed',
                   'every arm mean equals the independent three-seed replay',
                   'every per-seed mean equals its own audited seed summary',
                   'helped + harmed + tied covers all 36 people in every contrast',
                   'matrix reference shares the dataset protocol byte for byte, and carries no number',
                   'per-person, per-fold and memory fields refused',
                   'status-only source carries no score',
                   'no private paths or participant identifiers'],
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2))
