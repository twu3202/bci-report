"""Independent audit of beyond-scalp-update.json: every figure in the served file against the pinned sources.

A separate program from export_beyond_scalp_update.py. It shares no extraction code with that export: it reads the
served bytes, the review manifest and the pinned sources it names (the three independent result audits, the two
protocols and the readiness records, the analysis-stage record, and for three counts no structured source carries, the
pinned handoff and notes), builds its own table of what every figure and every flag must be, and compares them one for
one:

- every number, null and boolean in the served file has an expected value here, and every expected value is in the
  served file: nothing unaudited, nothing missing;
- copied figures equal the pinned source exactly, type included; derived ones (chance level, class recalls from the
  confusion tables, shares, the retained bins, the ridge-versus-mean directions) are recomputed here;
- each licence in the served file is the one its pinned repository record names;
- no withheld value (a confusion-table cell, a runtime, a normal-equation residual, an acquisition total, a free-space
  reading) appears anywhere in the file, and no private path or server name does;
- each source audit and readiness record is the pinned file, and the two served copies are one.

    python3 pipeline/publication/audit_beyond_scalp_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261012'
MANIFEST = REVIEW / 'beyond-scalp-release-manifest.json'
AUDIT = REVIEW / 'beyond-scalp-export-audit.json'
SERVED = (PROJECT / 'site/src/data/beyond-scalp-update.json', PROJECT / 'site/public/data/beyond-scalp-update.json')
BAK, NLB, OPT, H2, FUS = ('bak-fnirs-loso', 'nlb-mc-rtt-velocity', 'ds007420-optical-coverage',
                          'falcon-h2-preparation', 'rabut-fus-preparation')
PRIVATE = ('/home/', '/Users/', '/Volumes/', 'TRX50', 'Gal4', 'BCI_Arena', '.nwb', '.snirf', '.mat"', 'sub-')


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pinned(ref):
    raw = (PROJECT / ref['path']).read_bytes()
    check(digest(raw) == ref['sha256'], f'{ref["path"]}: not the pinned bytes')
    return raw


def load_json(ref):
    return json.loads(load_pinned(ref))


def from_text(text, pattern, label):
    m = re.search(pattern, text)
    check(m is not None, f'{label}: the pinned text does not state it')
    return int(m.group(1).replace(',', ''))


# ---------------------------------------------------------------------------- what every figure must be
def bak(src, handoff):
    protocol, audit = load_json(src['protocol']), load_json(src['resultAudit'])
    R = ('results', BAK)
    out, flags = {}, {}
    co, sp, feat = protocol['cohort'], protocol['split'], protocol['features']
    out.update({R + ('cohort', 'people'): audit['participants'], R + ('cohort', 'trials'): audit['trials'],
                R + ('cohort', 'trials_each_person'): co['trials_per_person'],
                R + ('cohort', 'trials_each_class_each_person'): co['trials_per_class_per_person'],
                R + ('design', 'folds'): audit['folds'], R + ('design', 'training_people'): sp['train_people'],
                R + ('design', 'training_trials'): sp['train_trials'], R + ('design', 'test_trials'): sp['test_trials'],
                R + ('signal', 'channels'): from_text(handoff, r'The supplied (\d+) columns are', 'channels'),
                R + ('signal', 'sampling_rate_hz'): protocol['representation']['fs_hz'],
                R + ('signal', 'observation_window_s'): feat['windows_seconds'][-1][1],
                R + ('signal', 'features'): audit['features'],
                R + ('uncertainty', 'draws'): protocol['scoring']['uncertainty']['draws'],
                R + ('uncertainty', 'seed'): protocol['scoring']['uncertainty']['seed'],
                R + ('independent_audit', 'people'): audit['participants']})
    for i, v in enumerate(feat['baseline_seconds']):
        out[R + ('signal', 'baseline_window_s', i)] = v
    for i, w in enumerate(feat['windows_seconds']):
        for j, v in enumerate(w):
            out[R + ('signal', 'feature_windows_s', i, j)] = v
    classes = len(protocol['mapping']) - 1          # keys "0", "1", "2" and "crosschecks"
    chance = 1 / classes
    out[R + ('primary_metric', 'chance_level')] = ('derived', chance)
    res = audit['results']
    for arm, key in (('shrinkage_lda', 'lda'), ('source_prior', 'source_prior')):
        A = R + ('arms', arm)
        r = res[key]
        out[A + ('balanced_accuracy', 'mean')] = r['participant_macro_balanced_accuracy']
        cm = r['confusion_matrix']
        for i, name in enumerate(('right_hand', 'left_hand', 'foot')):
            recall = cm[i][i] / sum(cm[i])
            check(math.isclose(recall, r['class_recall'][i], rel_tol=0, abs_tol=1e-15), f'{key}: recall {i} differs')
            out[A + ('class_recall', name)] = ('derived', recall)
    iv = res['lda']['descriptive_bootstrap_95_percent']
    out[R + ('arms', 'shrinkage_lda', 'balanced_accuracy', 'interval_95', 0)] = iv[0]
    out[R + ('arms', 'shrinkage_lda', 'balanced_accuracy', 'interval_95', 1)] = iv[1]
    flags[R + ('arms', 'shrinkage_lda', 'balanced_accuracy', 'interval_excludes_chance')] = iv[0] > chance
    withheld = {*(c for row in res['lda']['confusion_matrix'] for c in row), audit['runtime']['launcher_total_seconds']}
    return out, flags, withheld


NLB_HIGHER = {'r2_uniform_average': True, 'r2_x': True, 'r2_y': True, 'rmse_m_per_s': False, 'mae_m_per_s': False}


def nlb(src):
    protocol, audit = load_json(src['protocol']), load_json(src['resultAudit'])
    note = load_pinned(src['readinessNote']).decode()
    R = ('results', NLB)
    out, flags = {}, {}
    ds, inp, pre = protocol['dataset'], protocol['input'], protocol['preprocessing']
    lo, hi = pre['candidate_bin_indices_inclusive']
    rows = pre['expected_rows_before_finite_mask']
    out.update({R + ('cohort', 'animals'): ds['subjects'], R + ('cohort', 'sessions'): ds['sessions'],
                R + ('cohort', 'training_trials'): inp['training_file_split_counts']['train'],
                R + ('cohort', 'validation_trials'): inp['training_file_split_counts']['val'],
                R + ('cohort', 'trial_ms'): from_text(note, r'segments are (\d+) ms each', 'trial length'),
                R + ('cohort', 'input_neurons'): inp['input_neurons'],
                R + ('cohort', 'unused_neurons'): inp['heldout_neurons_not_inputs'],
                R + ('signal', 'bin_ms'): pre['bin_ms'], R + ('signal', 'smoothing_bins'): pre['causal_smoothing']['bins'],
                R + ('signal', 'history_lags'): len(pre['history_lags_bins']),
                R + ('signal', 'neural_support_ms'): pre['total_neural_support_ms'],
                R + ('signal', 'features'): pre['features_before_constant_column_removal'],
                R + ('signal', 'target_lag_ms'): pre['target']['lag_ms'],
                R + ('signal', 'retained_bins_each_trial'): ('derived', hi - lo + 1),
                R + ('signal', 'training_rows'): rows['train'], R + ('signal', 'validation_rows'): rows['val'],
                R + ('signal', 'rows_excluded'): sum(pre['observed_gap_exclusions'].values()),
                R + ('coverage', 'validation_rows_scored'): audit['validation_rows'],
                R + ('coverage', 'scored_share'): audit['scored_coverage'],
                R + ('independent_audit', 'rows_reconstructed'): audit['all_feature_rows_independently_reconstructed']})
    check(rows['val'] == audit['validation_rows'], 'nlb: the protocol and the audit disagree on validation rows')
    ridge, base = audit['models']['ridge'], audit['models']['training_mean_baseline']
    for m, higher in NLB_HIGHER.items():
        out[R + ('arms', 'ridge', m)] = ridge[m]
        out[R + ('arms', 'training_mean', m)] = base[m]
        flags[R + ('metrics', m, 'higher_is_better')] = higher
        flags[R + ('comparison', 'ridge_better', m)] = ridge[m] > base[m] if higher else ridge[m] < base[m]
    withheld = {audit['ridge_normal_equation_max_abs_residual']}
    return out, flags, withheld


def optical(src):
    ready, audit = load_json(src['readiness']), load_json(src['resultAudit'])
    quality = load_pinned(src['qualityNote']).decode()
    R = ('results', OPT)
    out, flags = {}, {}
    vc, lv, aux = audit['value_counts'], ready['label_verification'], ready['auxiliary_metadata']
    for i, w in enumerate(ready['geometry']['wavelengths_nm']):
        out[R + ('wavelengths_nm', i)] = w
    out.update({R + ('cohort', 'people'): ready['participants'], R + ('cohort', 'recordings'): audit['recordings'],
                R + ('cohort', 'recordings_excluded'): from_text(quality, r'\| Recordings checked / excluded \| \d+ / (\d+) \|',
                                                                 'exclusions'),
                R + ('cohort', 'channels_each_recording'): ready['geometry']['wavelength_measurements'],
                R + ('cohort', 'recording_channels'): audit['channel_instances'],
                R + ('cohort', 'optical_time_points'): ready['optical_metadata']['optical_samples_total'],
                R + ('counts', 'optical_values'): audit['optical_values'],
                R + ('counts', 'constant_channels'): audit['constant_channels'],
                R + ('shares', 'finite'): ('derived', vc['finite'] / audit['optical_values']),
                R + ('shares', 'positive'): ('derived', vc['positive'] / audit['optical_values']),
                R + ('gates', 'event_duration_s', 'events_table'): lv['tsv_task_duration_seconds'],
                R + ('gates', 'event_duration_s', 'optical_files'): lv['snirf_task_duration_seconds'],
                R + ('gates', 'event_duration_s', 'cited_paper'): lv['cited_paper_ball_duration_seconds'],
                R + ('gates', 'auxiliary_clock_hold_recordings'): aux['affected_recordings'],
                R + ('independent_audit', 'recordings'): audit['recordings']})
    for k in ('finite', 'positive', 'zero', 'negative', 'nonfinite'):
        out[R + ('counts', k)] = vc[k]
    check(audit['optical_values'] == ready['optical_metadata']['optical_samples_total']
          * ready['geometry']['wavelength_measurements'], 'ds007420: values are not time points times channels')
    flags[R + ('gates', 'task_code_lookup_verified')] = (lv['ball_hand_mapping'] is not None
                                                          and lv['motion_code_mapping'] is not None)
    withheld = {ready['pin']['acquired_bytes'], ready['pin']['acquired_assets']}
    return out, flags, withheld


def falcon_h2(src, i):
    ready = load_json(src['readiness'])
    v, run = ready['verified'], ready['first_run']
    P = ('status_only', i, 'preparation')
    out = {P + ('participants',): v['human_subjects'], P + ('recording_dates',): v['distinct_dates'],
           P + ('files',): v['files'], P + ('channels',): v['shape_channels'],
           P + ('held_in_calibration_trials',): v['trials_by_split']['held_in_calib'],
           P + ('minival_trials',): v['trials_by_split']['held_in_minival'],
           P + ('minival_trials_also_in_calibration',): run['split_policy']['excluded_calibration_trials'],
           P + ('training_candidate_trials',): run['training_trials'],
           P + ('held_out_calibration_trials',): v['trials_by_split']['held_out_calib'],
           P + ('symbols',): run['vocabulary']['symbols'],
           P + ('ctc_classes_with_blank',): run['vocabulary']['ctc_classes_including_blank']}
    return out, {('status_only', i, 'scores_published'): False}


def rabut_fus(src, i, stage):
    ready = load_json(src['readiness'])
    human = next(e for e in ready['experiments'] if e['id'] == 'human')
    s = stage['prepared_not_scored']['rabut_fus']
    P = ('status_only', i, 'preparation')
    out = {P + ('participants',): human['paper_n'], P + ('runs',): s['runs'],
           P + ('drawing_runs',): s['paradigms']['drawing'], P + ('guitar_runs',): s['paradigms']['guitar'],
           P + ('mixed_speech_reading_runs',): s['paradigms']['mixed_speech_reading'],
           P + ('frames',): s['frames'], P + ('rest_frames',): s['rest_frames'],
           P + ('activity_frames',): s['activity_frames']}
    return out, {('status_only', i, 'scores_published'): False}


def consent_flags(manifest, served_datasets):
    flags = {}
    for d in manifest['datasets']:
        D = ('datasets', d['id'], 'consent_and_ethics')
        flags[D + ('ethics_approval', 'stated')] = True
        if d['consentEthics']['subjects'] == 'human':
            flags[D + ('informed_consent', 'stated')] = True
        else:
            flags[D + ('informed_consent', 'stated')] = False
            flags[D + ('informed_consent', 'applicable')] = False
    check(set(served_datasets) == {d['id'] for d in manifest['datasets']}, 'the served datasets differ from the manifest')
    return flags


LICENCE_NAMES = {'CC BY 4.0': 'CC BY 4.0', 'CC0': 'CC0-1.0', 'spdx:CC-BY-4.0': 'CC BY 4.0',
                 'cc-by-nc-4.0': 'CC BY-NC 4.0'}


def record_licence(ref):
    rec = load_json(ref)
    if 'license' in rec and isinstance(rec['license'], dict):          # figshare
        return LICENCE_NAMES[rec['license']['name']]
    if 'license' in rec and isinstance(rec['license'], list):          # DANDI
        return LICENCE_NAMES[rec['license'][0]]
    if 'License' in rec:                                                 # BIDS dataset_description
        return LICENCE_NAMES[rec['License']]
    return LICENCE_NAMES[rec['metadata']['rights'][0]['id']]           # CaltechData


# ---------------------------------------------------------------------------- the comparison
def leaves(value, trail=()):
    """Every number, null and boolean in the served file, with its path."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    elif value is None or isinstance(value, (bool, int, float)):
        yield trail, value


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served = [p.read_bytes() for p in SERVED]
    check(served[0] == served[1], 'the two served copies differ')
    text = served[0].decode()
    payload = json.loads(served[0])
    check(payload['release_id'] == manifest['release_id'] and payload['provenance']['manifest_sha256'] == digest(manifest_bytes),
          'the served file names another manifest')
    for token in PRIVATE:
        check(token not in text, f'a private path, server name or file name in the served file: {token}')

    src = {s['id']: s for s in manifest['sources']}
    check(tuple(src) == (BAK, NLB, OPT, H2, FUS), 'the manifest names other sources')
    prov = payload['provenance']
    included = [sid for sid in (BAK, NLB, OPT) if src[sid]['decision'] == 'aggregate_preview']
    check(prov['included'] == included == list(payload['results']), 'the served results are not the approved ones')
    for sid in included:
        check(prov['source_audit_sha256'][sid] == digest(load_pinned(src[sid]['resultAudit'])),
              f'{sid}: the served file names another audit')
    for sid in (H2, FUS):
        check(prov['source_readiness_sha256'][sid] == digest(load_pinned(src[sid]['readiness'])),
              f'{sid}: the served file names another readiness record')
    handoff = load_pinned(manifest['batch']['handoff']).decode()
    check(prov['handoff_sha256'] == manifest['batch']['handoff']['sha256'], 'the served file names another handoff')
    stage = load_json(manifest['batch']['analysisStage'])

    expected, flags, withheld = {}, {}, set()
    makers = {BAK: lambda: bak(src[BAK], handoff), NLB: lambda: nlb(src[NLB]), OPT: lambda: optical(src[OPT])}
    for sid in included:
        e, f, w = makers[sid]()
        expected.update(e)
        flags.update(f)
        withheld |= w
    check([e['id'] for e in payload['status_only']] == [H2, FUS], 'the status-only entries differ')
    for i, (sid, fn) in enumerate(((H2, lambda i: falcon_h2(src[H2], i)), (FUS, lambda i: rabut_fus(src[FUS], i, stage)))):
        e, f = fn(i)
        expected.update(e)
        flags.update(f)
    flags.update(consent_flags(manifest, payload['datasets']))
    withheld.add(stage['last_live_check']['free_server_gib'])

    found = dict(leaves(payload))
    found_numbers = {p: v for p, v in found.items() if not isinstance(v, bool)}
    found_flags = {p: v for p, v in found.items() if isinstance(v, bool)}
    unaudited = sorted(map(str, set(found_numbers) - set(expected)))
    missing = sorted(map(str, set(expected) - set(found_numbers)))
    check(not unaudited, f'figures in the served file with no audit rule: {unaudited[:5]}')
    check(not missing, f'audited figures missing from the served file: {missing[:5]}')
    exact = derived = 0
    for path, want in expected.items():
        got = found_numbers[path]
        if isinstance(want, tuple) and want[0] == 'derived':
            check(got is not None and math.isclose(got, want[1], rel_tol=1e-15, abs_tol=0), f'{path}: {got!r} != {want[1]!r}')
            derived += 1
        else:
            check(type(got) is type(want) and got == want, f'{path}: {got!r} != {want!r}')
            exact += 1
    check(set(found_flags) == set(flags), f'flags differ: {sorted(map(str, set(found_flags) ^ set(flags)))[:5]}')
    for path, want in flags.items():
        check(found_flags[path] is want, f'{path}: the flag does not follow from the sources')

    # Licences: each the one its repository record names.
    for d in manifest['datasets']:
        lic = record_licence(d['licenseRecord'])
        check(payload['datasets'][d['id']]['rights']['license'] == lic, f'{d["id"]}: the served licence is not the record\'s')
    for e in payload['status_only']:
        check(e['rights']['license'] == payload['datasets'][e['dataset']]['rights']['license'],
              f'{e["id"]}: the status entry names another licence')

    # Withheld values stay out, by value.
    published = [v for v in found_numbers.values() if v is not None]
    for v in withheld:
        check(v not in published, f'a withheld value reached the served file: {v!r}')

    by_entry = {sid: sum(1 for p in expected if p[:2] == ('results', sid)) for sid in included}
    by_entry.update({sid: sum(1 for p in expected if p[:2] == ('status_only', i)) for i, sid in enumerate((H2, FUS))})
    return {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': digest(served[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_beyond_scalp_export.py',
        'independence': 'A separate program from the export. It reads the served bytes, the review manifest and the '
                        'pinned sources (the three independent result audits, the two protocols, the three readiness '
                        'records and the analysis-stage record, plus the pinned handoff and notes for three counts no '
                        'structured source carries), builds its own table of what every figure and flag must be and '
                        'shares no extraction code with the export.',
        'source_audit_sha256': {sid: prov['source_audit_sha256'][sid] for sid in included},
        'source_readiness_sha256': prov['source_readiness_sha256'],
        'included': payload['provenance']['included'], 'status_only': payload['provenance']['status_only'],
        'holds': payload['provenance']['holds'],
        'figures_compared': len(expected), 'figures_by_entry': by_entry,
        'copied_exactly': exact, 'recomputed': derived, 'flags_compared': len(flags),
        'withheld_values_checked_absent': len(withheld),
        'figures_from_pinned_text': [
            'Bak channels (40): the handoff ("The supplied 40 columns are 20 oxy and 20 deoxy signals"); the protocol '
            'lists the channel order but no count',
            'MC_RTT trial length (600 ms): the pinned NLB readiness note ("These 1,080 segments are 600 ms each")',
            'ds007420 recordings excluded (0): the pinned optical quality note ("Recordings checked / excluded | 60 / 0")',
        ],
        'checks': [
            'each source audit and readiness record is the pinned file and the one the served file names; the served '
            'file names the manifest it was built from and the pinned handoff; the two served copies are byte-identical',
            'every number and boolean in the served file has an expected value derived here from the pinned sources, '
            'and every expected value is in the file: no unaudited figure or flag and no missing one',
            'copied figures equal the source exactly, type included; the chance level (one over the protocol\'s '
            'classes), the class recalls (diagonal over row of each audited confusion table), the coverage shares and '
            'the retained bins are recomputed here',
            'the ridge-versus-mean direction of every MC_RTT metric is recomputed from the audited values; the '
            'classifier interval flag from the audited interval and the chance level',
            'each licence is the one its pinned repository record names',
            'no confusion-table cell, runtime, normal-equation residual, acquisition total or free-space reading '
            'reaches the file; no private path, server name or raw-file name does',
        ],
        'audit_bindings': {
            'bound': [
                'source audit and readiness bytes: pinned in the manifest and named in the served file',
                'every figure and flag: equal to its pinned source or recomputed from it',
            ],
            'not_bound': [
                'the hash chains behind each audit (protocols, implementations, freeze and preparation reviews) and the '
                'rights quotes are verified by the export, not re-read here',
                'prose in the served file is checked by the export (numerals against the pinned sources, claims, labels '
                'and identifiers by pattern), not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
