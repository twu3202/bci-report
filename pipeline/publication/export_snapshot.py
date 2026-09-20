"""Export reviewed aggregate evidence, never EEG, trial rows or participant IDs.

The release manifest is an editorial decision, not an automated legal opinion.
Unknown sources fail closed. All website-facing fields are explicitly selected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import statistics
from pathlib import Path

MODEL_NAMES = {
    'spectral-ridge': ('Spectral ridge', 'classical'),
    'temporal-ridge': ('Temporal ridge', 'classical'),
    'cca': ('Standard CCA', 'classical'),
    'csp-lda': ('CSP+LDA', 'classical'),
    'labram': ('LaBraM', 'foundation'),
    'eegpt': ('EEGPT', 'foundation'),
    'cbramod': ('CBraMod', 'foundation'),
    'eegnet': ('EEGNet', 'small'),
}
TRACK_FIELDS = (
    'id title short dataset subtitle type subjects observations exposure status '
    'xLabel yLabel limitation protocol protocolId version elapsed peakGb auditSha source'
).split()
ROW_FIELDS = (
    'id name family parameters channels mode x y xDetail yDetail abstain seconds subjects note'
).split()
FORBIDDEN_KEYS = {
    'subjectResults', 'subject_id', 'subject_ids', 'participant_id', 'participant_ids',
    'train_subjects', 'test_subjects', 'source_files', 'y_true', 'y_pred',
    'predictions', 'embeddings', 'waveforms', 'epochs', 'date_of_birth',
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# A leak is as likely to arrive as a mapping key ({"sub-001": {...}}) as a value,
# and a path root is not always one of four literals. Both checks below are
# deliberately broad: a false positive costs one rewritten sentence in a manifest,
# a false negative publishes participant data.
LOCAL_PATH = re.compile(
    r'(?:^|[\s"\'(<])(?:'
    r'[A-Za-z]:[\\/]'                                      # C:\… D:/… any drive
    r'|\\\\[^\s\\]+'                                       # \\server\share
    r'|/(?:Users|Volumes|home|mnt|media|private|tmp|var|opt|srv|root)(?:/|\b)'
    r')', re.IGNORECASE)
PARTICIPANT_ID = re.compile(
    r'\b(?:sub|subj|subject|participant|pt)[-_ ]?\d+\b'     # sub-7, subject_002, participant 3
    r'|\b[A-Z]\d{2}[TE]\b',                                # BNCI-style A01T / A02E
    re.IGNORECASE)


def validate_public(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in FORBIDDEN_KEYS:
                raise ValueError(f'Individual/source data field cannot be exported: {trail}.{k}')
            if isinstance(k, str):
                validate_public(k, f'{trail}.<key:{k}>')
            validate_public(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            validate_public(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        if LOCAL_PATH.search(value):
            raise ValueError(f'Local path cannot be exported: {trail}')
        if PARTICIPANT_ID.search(value):
            raise ValueError(f'Participant identifier cannot be exported: {trail}')
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'Nonfinite metric: {trail}')


def _reviewed(item):
    """A news item publishes only on an explicit review flag; anything else raises."""
    if item.get('reviewed') is not True:
        raise ValueError(f'Unreviewed news item cannot be exported: {item.get("title", "<untitled>")!r}')
    return True


def approved(record):
    return record.get('decision') == 'aggregate_preview' and all(record.get(k) for k in (
        'source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview',
        'reviewedAt', 'reviewBasis',
    ))


def rights_fields(record):
    return {k: record[k] for k in (
        'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt', 'reviewBasis'
    )} | {'rightsScope': 'Personal noncommercial research; aggregate results only',
         'pretrainingOverlap': 'Unknown unless explicitly documented; no unseen-pretraining claim.'}


def clean_legacy(track, record):
    if not approved(record):
        raise ValueError('Source has no aggregate-preview decision')
    checked = {}
    for i, path in enumerate(record['legacyAuditFiles']):
        audit_path = Path(path)
        audit = read(audit_path)
        if audit.get('passed') is not True or audit.get('errors'):
            raise ValueError('Legacy independent audit did not pass')
        expected = track['auditSha'] if i == 0 else track['extensionProtocol']['auditSha']
        if sha(audit_path) != expected:
            raise ValueError('Legacy audit hash changed')
        aggregate = (audit['output']['aggregate_counts_recomputed'] if i == 0
                     else audit['checks']['aggregate']['recomputed'])
        checked.update({r['model']: r for r in aggregate})
    for row in track['rows']:
        a = checked[row['name']]
        for actual, expected in ((row['x'], 100*a['idle_false_trigger_trials']/a['idle_trials']),
                                 (row['y'], 100*a['mi_detected_trials']/a['mi_trials'])):
            if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
                raise ValueError('Legacy score differs from audited counts')
        if row['subjects'] != a['subjects'] or row['abstain'] != a['always_abstain_subjects']:
            raise ValueError('Legacy cohort counts differ from audit')
    clean = {k: track[k] for k in TRACK_FIELDS}
    clean['protocol'] = list(track['protocol'])
    clean['rows'] = []
    for row in track['rows']:
        item = {k: row.get(k) for k in ROW_FIELDS}
        item['note'] = ('Fixed calibration rule; 60 training trials and 30 calibration trials per participant. '
                        'Four-person case study; cohort aggregates only, no subgroup or population claim.')
        if 'interval' in row:
            item['interval'] = row['interval']
        clean['rows'].append(item)
    clean.update(rights_fields(record))
    clean['source'] = record['source']
    clean['backend'] = 'Apple M5 / MPS and CPU'
    clean['chanceLevel'] = None
    clean['selection'] = 'Single fixed configuration; no test-set hyperparameter selection.'
    if track.get('extensionProtocol'):
        e = track['extensionProtocol']
        clean['protocol'].append('Additional models use protocol ' + e['protocolId'] +
                                 '; independent audit SHA256: ' + e['auditSha'] + '.')
        clean['elapsed'] += e['elapsed']
        clean['peakGb'] = max(clean['peakGb'], e['peakGb'])
    validate_public(clean)
    return clean


def matching_audit(results, audit):
    if audit.get('status') != 'pass':
        raise ValueError('Independent numerical audit has not passed')
    audited = {r['model']: r for r in audit['models']}
    if set(audited) != {r['model'] for r in results}:
        raise ValueError('Audit and summary model sets differ')
    for r in results:
        a = audited[r['model']]
        if a.get('status') != 'audited':
            raise ValueError('Unaudited model')
        for k in ('subject_mean_balanced_accuracy', 'subject_mean_macro_f1'):
            if not math.isclose(a[k], r[k], rel_tol=0, abs_tol=1e-12):
                raise ValueError('Summary metric differs from independent audit')
        if a['descriptive_subject_bootstrap_95'] != r['descriptive_subject_bootstrap_95']:
            raise ValueError('Summary interval differs from independent audit')


def make_row(result, channels, epochs, subjects, beta=False):
    name, family = MODEL_NAMES[result['model']]
    mode = ('Frozen encoder + ridge head' if family == 'foundation' else
            f'Scratch · {epochs} epochs' if family == 'small' else
            'Known-frequency reference · no fitting' if result['model'] == 'cca' else
            'Supervised fit')
    interval = result['descriptive_subject_bootstrap_95_percentile' if beta else 'descriptive_subject_bootstrap_95']
    return {
        'id': result['model'], 'name': name, 'family': family, 'parameters': None,
        'channels': channels, 'mode': mode,
        'x': result['subject_mean_macro_f1'],
        'y': result['subject_mean_balanced_accuracy'] * 100,
        'xDetail': 'Mean across held-out participants',
        'yDetail': f'Descriptive 95% interval: {interval[0]*100:.1f}–{interval[1]*100:.1f}%',
        'interval': [v*100 for v in interval], 'abstain': None,
        'seconds': result['total_seconds' if beta else 'seconds'], 'subjects': subjects,
        'note': ('One fixed configuration. Foundation encoders remain frozen; small networks train from scratch. '
                 'These scores do not establish optimal fine-tuned performance. '
                 'No individual predictions or participant-level results are distributed.'),
    }


def make_parallel(entry, record):
    if not approved(record) or entry['dataset'] == 'nm000123':
        raise ValueError('Dataset is not released for aggregate preview')
    if len(entry['runs']) != 1:
        raise ValueError('Select one exact run; multiple runs are ambiguous')
    run = Path(entry['runs'][0]['path'])
    summary = read(run/'summary.json')
    audit = read(run/'independent-audit.json')
    matching_audit(summary['results'], audit)
    if summary['status'] != 'complete' or summary['failures']:
        raise ValueError('Incomplete run cannot be published')
    p = read(run/'dataset-protocol.json')
    engine = read(run/'engine-protocol.json')
    env = read(run/'environment.json')
    result = summary['results'][0]
    n, epochs = result['participants'], engine['eegnet']['epochs']
    preprocessing = p['preprocessing']
    preprocessing = ('; '.join(f'{k}: {v}' for k, v in preprocessing.items())
                     if isinstance(preprocessing, dict) else preprocessing)
    limitations = p.get('limitations', [])
    track = {
        'id': record['trackId'], 'title': record['title'], 'short': record['short'],
        'dataset': record['name'], 'subtitle': record['subtitle'], 'type': 'accuracy',
        'subjects': n, 'observations': f"{result['trials']:,} epochs · {p['fold_count']} participant-disjoint folds",
        'exposure': f"{len(p['channels'])} channels · {p['window_seconds']:g}-second windows",
        'status': 'Research preview', 'xLabel': 'Macro F1', 'yLabel': 'Balanced accuracy',
        'limitation': record.get('limitation', ' '.join(limitations)),
        'protocol': [
            f"{p['fold_count']} participant-disjoint folds. All recordings from a person stay together. "
            'Each person contributes to the held-out predictions once.',
            preprocessing,
            f"One fixed seed ({engine['seed']}); no early stopping or test-based tuning. "
            f'EEGNet trains for {epochs} epochs per fold. Frozen encoders use training-only standardized ridge heads (alpha 100).',
            'Labels: ' + ', '.join(p['class_names']) + '.',
            f"Uniform-guessing reference: {100/result['classes']:.2f}%. "
            'Scores weight participants equally. Intervals describe participant variation; cross-validation training sets overlap.',
        ] + limitations,
        'protocolId': f"parallel-fixed-subject-folds-v1/{entry['dataset']}",
        'version': record['version'], 'elapsed': sum(r['seconds'] for r in summary['results']),
        'peakGb': None, 'auditSha': sha(run/'independent-audit.json'),
        'source': record['source'], 'backend': 'Apple M5 / MPS' if env['device']=='mps' else 'Local Ubuntu / CUDA',
        'chanceLevel': 100/result['classes'], 'selection': 'One fixed seed and training budget; multi-seed sensitivity pending.',
        'rows': [make_row(r, len(p['channels']), epochs, n) for r in summary['results']],
        'summarySha': sha(run/'summary.json'), 'protocolSha': sha(run/'dataset-protocol.json'),
    } | rights_fields(record)
    validate_public(track)
    return track


def make_beta(root, record):
    if not approved(record):
        raise ValueError('BETA has no aggregate-preview decision')
    p, s = read(root/'protocol.json'), read(root/'summary.json')
    audit_path = root.with_name(root.name+'-independent-audit.json')
    audit = read(audit_path)
    if audit.get('all_passed') is not True or audit.get('passed_comparisons') != 12 or audit.get('failures'):
        raise ValueError('BETA independent audit incomplete')
    if len(s['results']) != 12:
        raise ValueError('BETA comparison count changed')
    audited = {r['comparison']: r for r in audit['comparisons']}
    if set(audited) != {r['montage']+'/'+r['model'] for r in s['results']}:
        raise ValueError('BETA audit model sets differ')
    for r in s['results']:
        a = audited[r['montage']+'/'+r['model']]
        if a['status'] != 'passed':
            raise ValueError('BETA model has not passed audit')
        for metric in ('subject_mean_balanced_accuracy', 'subject_mean_macro_f1'):
            if not math.isclose(r[metric], a[metric+'_recomputed'], rel_tol=0, abs_tol=1e-12):
                raise ValueError('BETA summary differs from independently recomputed metric')
        if r['descriptive_subject_bootstrap_95_percentile'] != a['participant_bootstrap_95_recomputed']:
            raise ValueError('BETA interval differs from audit')
    tracks = []
    for montage in ('posterior8', 'posterior4'):
        rows = [r for r in s['results'] if r['montage']==montage]
        channels = len(p['montages'][montage])
        track = {
            'id': f'beta-{channels}ch', 'title': f'SSVEP · {channels} channels', 'short': 'Transfer to a new person',
            'dataset': 'BETA', 'subtitle': f'40 visual targets · {channels} posterior electrodes',
            'type': 'accuracy', 'subjects': 70, 'observations': '11,200 trials · 7 participant-disjoint folds',
            'exposure': f'{channels} channels selected from a 64-channel recording · 2-second windows',
            'status': 'Research preview', 'xLabel': 'Macro F1', 'yLabel': 'Balanced accuracy',
            'limitation': ('Near-floor scores are not ordered reliably between the 8- and 4-electrode subsets. '
                           'Electrode subsets from laboratory recordings do not validate a physical low-channel cap. '
                           'Prompted SSVEP does not measure idle false activations. Single-seed results; pretraining overlap unknown.'),
            'protocol': [
                'Seven participant-disjoint folds: train on 60 people, test on ten. All four blocks stay with their participant.',
                'Two seconds from stimulus onset; no visual-latency shift. Source data were already zero-phase filtered. '
                'Additional 6–80 Hz filtering applies to each selected window separately.',
                'Microvolt units are inferred from an independently documented loader, not explicitly stated in the author MAT description. '
                'Inconsistent phase metadata are unused by all methods.',
                'Standard CCA uses known frequencies and three harmonics without training labels. '
                'Frozen encoders use training-only standardized ridge heads (alpha 100). '
                'EEGNet trains from scratch for 20 epochs with one seed (20260912).',
                'Electrodes: ' + ', '.join(p['montages'][montage]) + '.',
                'Uniform-guessing reference: 2.5%. Descriptive 95% intervals resample participants; training sets overlap across folds.',
                'No cross-task overall ranking, model fine-tuning optimum or hardware benchmark is claimed.',
            ],
            'protocolId': p['protocol_id']+'/'+montage, 'version': record['version'],
            'elapsed': sum(r['total_seconds'] for r in rows), 'peakGb': None,
            'auditSha': sha(audit_path), 'summarySha': sha(root/'summary.json'),
            'protocolSha': sha(root/'protocol.json'), 'source': record['source'],
            'backend': 'Apple M5 / MPS and CPU', 'chanceLevel': 2.5,
            'selection': 'One fixed seed and training budget; multi-seed sensitivity pending.',
            'rows': [make_row(r,channels,20,70,beta=True) for r in rows],
        } | rights_fields(record)
        validate_public(track); tracks.append(track)
    return tracks


def build(manifest, legacy, batch, beta_root):
    records = {r['id']: r for r in manifest['datasets']}
    if len(records) != len(manifest['datasets']):
        raise ValueError('Duplicate dataset decision')
    if len({m['id'] for m in manifest['models']}) != len(manifest['models']):
        raise ValueError('Duplicate model decision')
    for entry in manifest['models']:
        if MODEL_NAMES.get(entry['id'], (entry['name'],))[0] != entry['name']:
            raise ValueError(f"Manifest name for {entry['id']!r} does not match the published name")
    tracks = []
    if approved(records.get('BETA', {})):
        tracks.extend(make_beta(beta_root, records['BETA']))
    for entry in batch['datasets']:
        record = records.get(entry['dataset'], {})
        if approved(record):
            tracks.append(make_parallel(entry, record))
    for track in legacy['tracks']:
        record = records.get(track['dataset'], {})
        if approved(record):
            tracks.append(clean_legacy(track, record))
    if not tracks:
        raise ValueError('No reviewed aggregate result available')
    model_decisions = {m['id']: m for m in manifest['models']}
    for track in tracks:
        track['rows'] = [r for r in track['rows']
                         if model_decisions.get(r['id'], {}).get('decision') == 'aggregate_preview']
        if not track['rows']:
            raise ValueError('No reviewed models in selected protocol')
        for row in track['rows']:
            row['modelRights'] = model_decisions[row['id']]['rightsNote']
        track['elapsed'] = sum(row['seconds'] for row in track['rows'])
        track['version'] = next((r['version'] for r in manifest['datasets']
                                  if r.get('trackId')==track['id']), track['version'])
    tracks.sort(key=lambda t: records.get(next((r['id'] for r in manifest['datasets']
                   if r.get('trackId')==t['id']), t['dataset']), {}).get('order', 99))
    directories = []
    for record in manifest['datasets']:
        directories.append({
            'name': record['name'], 'task': record['task'], 'subjects': record.get('subjects', '—'),
            'channels': record.get('channels', '—'), 'size': record.get('size','—'),
            'status': 'Aggregate results' if approved(record) else 'Not in this release',
            'detail': record['publicNote'], 'source': record['source'], 'license': record['license'],
            'licenseUrl': record.get('licenseUrl'), 'evaluated': approved(record),
            'attribution': record.get('attribution',''), 'reviewedAt': record.get('reviewedAt'),
            'decision': record['decision'],
        })
    public_models = [{k: m.get(k) for k in ('id','name','family','parameters','status','note','license','url')}
                     for m in legacy['models']]
    for slug in ('cca','spectral-ridge','temporal-ridge'):
        name, family = MODEL_NAMES[slug]
        if any(r['id']==slug for t in tracks for r in t['rows']) and not any(m['name']==name for m in public_models):
            public_models.append({'id':slug,'name':name,'family':family,'parameters':None,'status':'Evaluated',
                                  'note':'Fixed reference method; inspect each task for input features and fit protocol.',
                                  'license':'Implementation-specific; no third-party weights distributed',
                                  'url':'https://scikit-learn.org/stable/'})
    for model in public_models:
        decision = next((m for m in manifest['models'] if m['name']==model['name']), None)
        if decision:
            model['license'] = decision['rightsNote']
            published = decision['decision']=='aggregate_preview'
            model['status'] = 'Evaluated' if published else 'Rights review pending'
            if not published:
                model['note'] = ('Evaluated locally, but no score is published in this release: '
                                 'the checkpoint license is unresolved. Results are withheld pending '
                                 'that review, not because the model failed to run.')
        elif model['status']=='Evaluated':
            model['status'] = 'Not in this release'
    if manifest.get('seedSensitivity'):
        source = Path(manifest['seedSensitivity'])
        sensitivity = read(source)
        seed_audit_path = source.with_name('independent-aggregate-audit.json')
        seed_audit = read(seed_audit_path)
        if seed_audit['status']!='pass' or seed_audit['aggregate_sha256']!=sha(source):
            raise ValueError('Seed sensitivity has no matching independent audit')
        audited = {(r['dataset'],r['seed']):r for r in seed_audit['results']}
        for d in sensitivity['datasets']:
            record = records.get(d['dataset'], {})
            target = next((t for t in tracks if t['id']==record.get('trackId')), None)
            if not target: continue
            values = []
            for row in d['seeds']:
                a = audited[d['dataset'],row['seed']]
                if abs(a['balanced_accuracy']-row['balanced_accuracy'])>1e-12:
                    raise ValueError('Seed summary disagrees with independent audit')
                values.append(row['balanced_accuracy']*100)
            if len(values)!=3: raise ValueError('Expected three predetermined seeds')
            target['seedSensitivity'] = {
                'model':'EEGNet', 'seeds':[r['seed'] for r in d['seeds']],
                'balancedAccuracyPercent': values,
                'meanPercent': statistics.mean(values),
                'sampleSdPercentagePoints': statistics.stdev(values),
                'rangePercentagePoints':max(values)-min(values),
                'auditSha':sha(seed_audit_path),
                'scope':'Same participants, folds, preprocessing and 20-epoch budget. Three seeds measure initialization variability, not population uncertainty. Main table retains its preselected seed; no best-seed selection.',
            }
            note = (f"EEGNet three-seed mean {statistics.mean(values):.2f}%; "
                    f"sample SD {statistics.stdev(values):.2f} percentage points; "
                    f"range {min(values):.2f}–{max(values):.2f}%. "
                    'Main table retains the original fixed seed; this is not a confidence interval.')
            target['selection'] = note
            target['protocol'].append(note)
            for row in target['rows']:
                if row['id']=='eegnet': row['note'] += ' '+note
    snapshot = {
        'generatedAt': manifest['reviewedAt'], 'releaseId': manifest['releaseId'],
        'tracks': tracks, 'models': public_models, 'datasets': directories,
        # The field allowlist drops `reviewed`, so it has to be enforced here or
        # an unreviewed item publishes silently — the flag is the whole gate.
        'news': [{k:n[k] for k in ('tag','date','title','summary','source','sourceUrl')}
                 for n in legacy['news'] if _reviewed(n)],
        'evidencePolicy': ('Only explicitly reviewed cohort-level research results are exported. '
                           'Raw EEG, individual results and model weights stay outside the website. '
                           'Each comparison states its source, license, protocol and limitations. No cross-task overall score.'),
        'releaseScope': 'Personal noncommercial research · no advertising, paid access or EEG uploads',
        'coverage': {'displayedComparisons':sum(len(t['rows']) for t in tracks),'displayedProtocols':len(tracks),
                     'completedBatchComparisons':batch['totals']['completed_comparisons'],
                     'completedBatchDatasets':batch['totals']['completed_datasets']},
    }
    validate_public(snapshot)
    return snapshot


def write(snapshot, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'mvp.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n')
    public = destination/'data'
    if public.exists():
        for stale in public.iterdir():
            stale.unlink()
    public.mkdir(exist_ok=True)
    (public/'experiments.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n')
    for track in snapshot['tracks']:
        protocol={k:v for k,v in track.items() if k!='rows'}
        (public/f"{track['id']}-protocol.json").write_text(json.dumps(protocol,indent=2,ensure_ascii=False)+'\n')
        stream=io.StringIO(); writer=csv.writer(stream, lineterminator='\n')
        writer.writerow(['dataset','dataset_version','protocol_id','model','evaluation_mode','channels',
                         'participants','primary_metric','primary_percent','secondary_metric','secondary_value',
                         'descriptive_interval_low_percent','descriptive_interval_high_percent',
                         'always_abstain_participants','chance_level_percent','scoring_seconds',
                         'source','license','license_url','attribution','scope','model_rights'])
        for row in track['rows']:
            # Splatting an unchecked list into a fixed-width row shifts every later
            # column if it is ever not a pair, so bind it explicitly.
            low, high = row.get('interval') or ('', '')
            writer.writerow([track['dataset'],track['version'],track['protocolId'],row['name'],row['mode'],row['channels'],
                             row['subjects'],track['yLabel'],row['y'],track['xLabel'],row['x'],
                             low,high,row.get('abstain') if row.get('abstain') is not None else '',
                             track.get('chanceLevel') if track.get('chanceLevel') is not None else '',
                             row['seconds'],track['source'],track['license'],track['licenseUrl'],
                             track['attribution'],track['rightsScope'],row['modelRights']])
        (public/f"{track['id']}-results.csv").write_text(stream.getvalue())


def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--legacy',type=Path,required=True); p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--beta-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    snapshot=build(read(a.manifest),read(a.legacy),read(a.batch),a.beta_root)
    write(snapshot,a.output)
    print(json.dumps({'release':snapshot['releaseId'],**snapshot['coverage'],'output':str(a.output)}))


if __name__=='__main__': main()
