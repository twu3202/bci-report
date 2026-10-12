"""Independent audit of pilot-studies-update.json: every figure in the served file against the pinned sources.

A separate program from export_pilot_studies_update.py. It shares no extraction code with that export: it reads the
served bytes, the review manifest and the approved aggregate exports the manifest pins (and, for the few counts no
export carries, the pinned handoffs and the BINGO deliverables), builds its own table of what every figure must be,
and compares the two one for one:

- every number and every null in the served file has an expected value here, and every expected value is in the
  served file: nothing unaudited, nothing missing;
- copied figures equal the source export exactly, type included; derived ones (chance levels, the Orthosis error
  share, shuffle means and observed ranges, the handwriting channel-trial count) are recomputed here;
- each source export is the byte-identical file its own approval or finalization record names, and the served file
  names the same hashes and the manifest it was built from; the two served copies are one;
- each interval_excludes_zero flag follows from its interval; no Orthosis per-person value (the matched-difference
  range, the three-person response-clean scores) appears anywhere, nor the handwriting mask-only control's withheld
  bounds (five people, its interval null); a source the manifest holds has no result and none of its figures in the file.

    python3 pipeline/publication/audit_pilot_studies_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261012'
MANIFEST = REVIEW / 'pilot-studies-release-manifest.json'
AUDIT = REVIEW / 'pilot-studies-export-audit.json'
SERVED = (PROJECT / 'site/src/data/pilot-studies-update.json', PROJECT / 'site/public/data/pilot-studies-update.json')
BATCH = 'research/paired_biosignal_pilots_20261011/'
IDS = ('orthosis-64ch-classical', 'orthosis-58ch-classical', 'orthosis-eegpt-vs-58ch', 'bingo-cross-language',
       'handwriting-mask-aware', 'refed-stored-clip')
O64, O58, OFM, BINGO, HAND, REFED = IDS
WORDS = {'one': 1, 'two': 2, 'three': 3, 'five': 5, 'eight': 8, 'ten': 10, 'sixteen': 16, 'seventeen': 17,
         'twenty': 20, 'eighty-two': 82}
TRIVIAL = {0.0, 0.25, 0.5, 1.0}


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(ref):
    raw = (PROJECT / ref['path']).read_bytes()
    check(digest(raw) == ref['sha256'], f'{ref["path"]}: not the pinned bytes')
    return raw


def jload(ref):
    return json.loads(load(ref))


def text(ref):
    return load(ref).decode()


def batch_name(ref):
    check(BATCH in ref['path'], f'{ref["path"]}: not in the paired-biosignal batch')
    return ref['path'].split(BATCH, 1)[1]


def handoff_int(source, pattern, label):
    m = re.search(pattern, source)
    check(m is not None, f'{label}: the pinned text does not state it')
    g = m.group(1).replace(',', '')
    return int(g) if g.isdigit() else WORDS[g.lower()]


# ---------------------------------------------------------------------------- the approval bindings
def binding(src):
    """The export hash each source's own final record names, read here, not taken from the manifest."""
    sid = src['id']
    if sid == O64:
        rec = jload(src['approval'])
        return rec['sha256'][batch_name(src['export'])]
    if sid == O58:
        return jload(src['approval'])['public_export_sha256']
    if sid == OFM:
        return jload(src['finalization'])['final_export_sha256']
    if sid == BINGO:
        return jload(src['finalization'])['approved_export_sha256']
    if sid == HAND:
        return jload(src['finalization'])['final_output_hashes'][batch_name(src['export'])]
    if sid == REFED:
        return jload(src['approval'])['public_export_sha256']
    raise AuditFailure(f'{sid}: no binding rule')


# ---------------------------------------------------------------------------- what every figure must be
MET = {'balanced_accuracy': 'balanced_accuracy', 'auroc': 'auroc', 'auprc': 'average_precision'}


def orth_rows(rows, R, out):
    for r in rows:
        A = R + ('arms', r['arm'], MET[r['metric']])
        out[A + ('mean',)] = r['mean']
        out[A + ('interval_95', 0)] = r['person_bootstrap_95ci'][0]
        out[A + ('interval_95', 1)] = r['person_bootstrap_95ci'][1]


def orth_common(e, R, out, derived):
    m = e['method']
    C = R + ('cohort',)
    out.update({C + ('people',): m['eligible_people'], C + ('runs',): m['eligible_runs'],
                C + ('events',): m['eligible_events'], C + ('standard_events',): m['class_counts']['standard'],
                C + ('error_events',): m['class_counts']['device_error']})
    out[C + ('error_share',)] = m['class_counts']['device_error'] / sum(m['class_counts'].values())
    derived.add(C + ('error_share',))
    S = R + ('signal',)
    out.update({S + ('eeg_channels',): m['eeg_channels'], S + ('sampling_hz',): m['sampling_hz'],
                S + ('window_seconds', 0): m['decision_window_seconds'][0],
                S + ('window_seconds', 1): m['decision_window_seconds'][1], S + ('window_samples',): m['window_samples']})
    out[R + ('chance_level',)] = 1 / len(m['class_counts'])
    derived.add(R + ('chance_level',))


def perm(values, P, out, derived, mean=None):
    out[P + ('replicates',)] = len(values)
    if mean is None:
        out[P + ('balanced_accuracy_mean',)] = math.fsum(values) / len(values)
        derived.add(P + ('balanced_accuracy_mean',))
    else:
        out[P + ('balanced_accuracy_mean',)] = mean
    out[P + ('observed_range', 0)] = min(values)
    out[P + ('observed_range', 1)] = max(values)


def orthosis_64(e, handoff, out, derived, secret):
    R = ('results', O64)
    orth_common(e, R, out, derived)
    orth_rows(e['primary_results'], R, out)
    out[R + ('configuration', 'values_per_event')] = int(re.match(r'(\d+) fixed', e['method']['features']).group(1))
    X = R + ('cohort', 'exclusions')
    out[X + ('baseline_runs',)] = handoff_int(handoff, r'(\w+) baseline runs were excluded', 'baseline runs')
    out[X + ('targets_without_following_movement',)] = handoff_int(handoff, r'([\w-]+) targets lacked an observed', 'targets')
    out[X + ('windows_crossing_boundary',)] = handoff_int(handoff, r'and (\w+) window crossed a boundary', 'windows')
    md = e['matched_eeg_minus_confound_balanced_accuracy']
    D = R + ('eeg_minus_confound',)
    out[D + ('balanced_accuracy_difference', 'mean')] = md['matched_person_mean']
    out[D + ('balanced_accuracy_difference', 'interval_95')] = None
    people = e['method']['eligible_people']
    out[D + ('people',)] = people
    check(md['all_person_differences_positive'] is True, 'orthosis: not every person had EEG above the confound')
    out[D + ('people_with_eeg_above_confound',)] = people
    p = e['permutation_control']
    perm(p['means'], R + ('permutation_control', 'balanced_accuracy'), out, derived, p['mean'])
    s = e['secondary_results']
    S = R + ('response_clean_subset',)
    out.update({S + ('events',): s['response_clean_events'], S + ('error_events',): s['class_counts']['device_error'],
                S + ('standard_events',): s['class_counts']['standard'],
                S + ('people_with_both_classes',): s['defined_people_for_class_dependent_metrics']})
    out[R + ('independent_audit', 'people')] = people
    secret += list(md['range'])
    for a in s['aggregates']:
        secret += [a['mean'], *a['person_bootstrap_95ci']]


def orthosis_58(e, out, derived):
    R = ('results', O58)
    orth_common(e, R, out, derived)
    orth_rows(e['primary_results'], R, out)
    out[R + ('configuration', 'values_per_event')] = int(re.match(r'(\d+) fixed', e['method']['features']).group(1))
    p = e['permutation_control']
    perm(p['means'], R + ('permutation_control', 'balanced_accuracy'), out, derived, p['mean'])
    out[R + ('independent_audit', 'people')] = e['method']['eligible_people']


def orthosis_fm(e, classical, out, derived):
    R = ('results', OFM)
    orth_common(e, R, out, derived)
    orth_rows(e['primary_results'], R, out)
    shared = {(r['arm'], r['metric']): r for r in classical['primary_results']}
    for r in e['primary_results']:
        if r['arm'] != 'eegpt2048':
            check(shared[(r['arm'], r['metric'])] == r, f'{OFM}: a classical row is not the classical export’s')
    pd = e['paired_primary_difference']
    P = R + ('paired',)
    out[P + ('balanced_accuracy_difference', 'mean')] = pd['mean']
    out[P + ('balanced_accuracy_difference', 'interval_95', 0)] = pd['person_bootstrap_95ci'][0]
    out[P + ('balanced_accuracy_difference', 'interval_95', 1)] = pd['person_bootstrap_95ci'][1]
    out[P + ('people',)] = e['method']['eligible_people']
    for a in ('eegpt2048', 'classical58'):
        s = e['permutation_control']['macro_person_balanced_accuracy'][a]
        perm(s['means'], R + ('permutation_control', a), out, derived, s['mean'])
    mo, ms = e['model'], e['method']
    out[R + ('model', 'encoder_parameters')] = mo['target_encoder_parameters']
    out[R + ('model', 'weights_licence')] = None
    check(mo['checkpoint_license'] == 'unverified', f'{OFM}: the checkpoint licence is no longer unverified')
    out[R + ('encoder_input', 'channels')] = mo['architecture']['img_size'][0]
    out[R + ('encoder_input', 'samples')] = ms['encoder_resampling']['output_samples']
    out[R + ('encoder_input', 'sampling_hz')] = ms['encoder_resampling']['output_sampling_hz']
    seal = re.search(r'(\d+) prediction arms per fold sealed before separate scoring; (\d+) fitted probes', ms['prediction_seal'])
    out[R + ('fits', 'folds')] = e['method']['eligible_people']
    out[R + ('fits', 'sealed_arms_per_fold')] = int(seal.group(1))
    out[R + ('fits', 'fitted_probes')] = int(seal.group(2))
    pv = e['provenance']
    out.update({R + ('independent_audit', 'people'): e['method']['eligible_people'],
                R + ('independent_audit', 'metric_rows_recomputed'): pv['all_metric_rows_recomputed'],
                R + ('independent_audit', 'aggregate_rows_recomputed'): pv['all_aggregates_recomputed'],
                R + ('independent_audit', 'source_only_refits'): pv['source_only_refits'],
                R + ('independent_audit', 'largest_refit_difference'): pv['maximum_refit_probability_difference']})


def bingo(e, handoff, v2, v3, out, derived):
    R = ('results', BINGO)
    order = ('train_gr_test_gr', 'train_gr_test_eng', 'train_eng_test_eng', 'train_eng_test_gr')
    for i, d in enumerate(order):
        D = R + ('directions', i)
        main, oth = e['main'][d], e['other']
        for key, src in (('balanced_accuracy', main), ('top3_accuracy', oth[f'{d}/main/top3_accuracy']),
                         (('controls', 'order_only', 'balanced_accuracy'), oth[f'{d}/order/balanced_accuracy']),
                         (('controls', 'high_frequency_ratio', 'balanced_accuracy'), oth[f'{d}/artifact/balanced_accuracy'])):
            K = D + (key if isinstance(key, tuple) else (key,))
            out[K + ('mean',)] = src['mean']
            out[K + ('interval_95', 0)] = src['percentile_2_5_97_5'][0]
            out[K + ('interval_95', 1)] = src['percentile_2_5_97_5'][1]
        out[D + ('controls', 'class_prior', 'balanced_accuracy', 'mean')] = oth[f'{d}/prior/balanced_accuracy']['mean']
        values = [oth[f'{d}/permutation_{k:02d}/balanced_accuracy']['mean'] for k in range(20)]
        perm(values, D + ('controls', 'label_shuffle', 'balanced_accuracy'), out, derived)
    c = e['contrasts']
    for key, P in (('transfer_minus_within', R + ('contrast',)),
                   ('gr_cross_minus_within', R + ('contrast', 'by_training_language', 'greek')),
                   ('eng_cross_minus_within', R + ('contrast', 'by_training_language', 'english'))):
        out[P + ('balanced_accuracy_difference', 'mean')] = c[key]['mean']
        out[P + ('balanced_accuracy_difference', 'interval_95', 0)] = c[key]['percentile_2_5_97_5'][0]
        out[P + ('balanced_accuracy_difference', 'interval_95', 1)] = c[key]['percentile_2_5_97_5'][1]
    out.update({R + ('cohort', 'source_fields'): e['source_defined_subject_fields'], R + ('cohort', 'trials'): e['retained_trials'],
                R + ('signal', 'channels'): e['channel_count'], R + ('signal', 'sampling_hz'): e['sample_rate_hz'],
                R + ('signal', 'window_seconds', 0): e['nominal_window_seconds'][0],
                R + ('signal', 'window_seconds', 1): e['nominal_window_seconds'][1],
                R + ('signal', 'values_per_trial'): e['features'], R + ('classes',): e['classes'],
                R + ('chance', 'balanced_accuracy'): e['class_prior_balanced_accuracy']})
    out[R + ('chance', 'top3_accuracy')] = 3 / e['classes']
    derived.add(R + ('chance', 'top3_accuracy'))
    out[R + ('signal', 'window_samples')] = handoff_int(handoff, r'exactly (\d+) samples', 'window samples')
    gr = handoff_int(handoff, r'supplies (\d+) Greek', 'Greek trials')
    en = handoff_int(handoff, r'Greek and (\d+) English trials', 'English trials')
    out.update({R + ('cohort', 'trials_per_held_out_field', 'greek'): gr,
                R + ('cohort', 'trials_per_held_out_field', 'english'): en,
                R + ('cohort', 'trials_per_noun_and_language'): handoff_int(handoff, r'with (\w+) trials per noun and language', 'per noun'),
                R + ('cohort', 'training_rows'): handoff_int(handoff, r'\(([\d,]+) rows\)', 'training rows')})
    F = R + ('fits',)
    out.update({F + ('main_models',): handoff_int(handoff, r'produce (\d+) main models', 'main models'),
                F + ('order_and_high_frequency_controls',): handoff_int(handoff, r'(\d+) order/high-frequency controls', 'controls'),
                F + ('shuffled_label_fits',): handoff_int(handoff, r'(\d+) shuffled-label fits', 'shuffles'),
                F + ('class_prior_outputs',): handoff_int(handoff, r'and (\d+) unfitted class-prior predictions', 'priors'),
                F + ('sealed_checkpoints',): handoff_int(handoff, r'All (\d+) prediction checkpoints were sealed', 'sealed')})
    a = e['audit']
    out.update({R + ('independent_audit', 'source_fields'): e['source_defined_subject_fields'],
                R + ('independent_audit', 'refitted_models'): a['independent_main_control_refits'],
                R + ('independent_audit', 'refitted_shuffle_models'): a['independent_permutation_refits'],
                R + ('independent_audit', 'largest_refit_difference'): a['max_refit_abs_error'],
                R + ('independent_audit', 'reconstructed_models'): handoff_int(handoff, r'reconstructed all (\d+) fitted-model', 'reconstructed')})
    # The source's own documents.
    flat2, flat3 = re.sub(r'\s+', ' ', v2), re.sub(r'\s+', ' ', v3)
    T = R + ('protocol', 'timeline_seconds')
    for key, pattern in (('word_shown', r't = (-?[\d.]+) s: A randomly selected lexical item'),
                         ('word_removed_countdown', r't = (-?[\d.]+) s: The lexical item is removed'),
                         ('fixation_inner_speech_onset', r't = (-?[\d.]+) s: A fixation cross \(“\+”\) appears, signaling participants'),
                         ('end', r't = (-?[\d.]+) s: The fixation cross disappears, marking the end of the trial. Participants then')):
        m = re.search(pattern, flat2)
        check(m is not None, f'bingo protocol {key}: not in D3.1 version 2.0')
        out[T + (key,)] = float(m.group(1))
    out[R + ('protocol', 'nouns')] = handoff_int(flat2, r'we identified (\d+) words in English and Greek', 'nouns')
    out[R + ('protocol', 'repetitions_per_noun')] = handoff_int(flat2, r'completes \w+ \((\d+)\) repetitions per lexical item', 'reps')
    m = re.search(r'EEGNet achieves an overall mean accuracy of ([\d.]+)%, indicating performance at chance level', flat3)
    check(m is not None and 'LOSO-CV (26-class)' in flat3, 'bingo: D3.1 version 3.0 does not report it')
    out[R + ('project_reported', 'mean_accuracy_percent')] = float(m.group(1))
    classes = handoff_int(flat3, r'using a (\d+)-word vocabulary', 'vocabulary')
    out[R + ('project_reported', 'classes')] = classes
    out[R + ('project_reported', 'chance_level')] = 1 / classes
    derived.add(R + ('project_reported', 'chance_level'))


def handwriting(e, earlier, result_audit, handoff, out, derived, secret):
    R = ('results', HAND)
    r = e['results']['primary_and_contrasts']
    for a, v in r['arms'].items():
        A = R + ('arms', a, 'balanced_accuracy')
        if a == 'mask_only':
            # Withheld: five people whose mask-only scores sit so close to 25% that the bounds would show individual
            # scores. The interval stays null, and its bounds (chance aside) must appear nowhere in the file.
            out.update({A + ('mean',): v['mean'], A + ('interval_95',): None})
            secret += [b for b in v['percentile_2_5_97_5'] if b not in TRIVIAL]
            continue
        out.update({A + ('mean',): v['mean'], A + ('interval_95', 0): v['percentile_2_5_97_5'][0],
                    A + ('interval_95', 1): v['percentile_2_5_97_5'][1]})
    for k, v in r['contrasts'].items():
        C = R + ('contrasts', k, 'balanced_accuracy_difference')
        out.update({C + ('mean',): v['mean'], C + ('interval_95', 0): v['percentile_2_5_97_5'][0],
                    C + ('interval_95', 1): v['percentile_2_5_97_5'][1]})
    pm = e['results']['permutation_person_macro_ba']
    for a in ('relative_eeg', 'mask_only', 'time_only', 'mask_plus_time'):
        perm([v for k, v in sorted(pm.items()) if k.split('/')[0] == a], R + ('label_shuffle', 'representations', a),
             out, derived)
    co = e['cohort']
    out.update({R + ('cohort', 'people'): co['development_people'], R + ('cohort', 'sessions'): co['sessions'],
                R + ('cohort', 'events'): co['original_events'], R + ('cohort', 'trials'): co['eligible_trials'],
                R + ('cohort', 'quarantined_events'): co['preserved_quarantines'], R + ('cohort', 'classes'): co['classes']})
    out[R + ('chance_level',)] = 1 / co['classes']
    derived.add(R + ('chance_level',))
    dist = sorted((int(k), v) for k, v in e['results']['final_mask_distribution'].items())
    check(e['results']['raw_mask_distribution'] == e['results']['final_mask_distribution'], 'handwriting: histograms differ')
    V = R + ('availability',)
    channels = handoff_int(handoff, r'Only (\d+) header-identified EEG channels are read', 'channels')
    out[V + ('channels_recorded',)] = channels
    out[V + ('available_channels_per_trial', 'fewest')] = dist[0][0]
    out[V + ('available_channels_per_trial', 'most')] = dist[-1][0]
    for i, (k, v) in enumerate(dist):
        out[V + ('trials_by_available_channels', i, 'channels')] = k
        out[V + ('trials_by_available_channels', i, 'trials')] = v
    out[V + ('channel_trials',)] = co['eligible_trials'] * channels
    check(out[V + ('channel_trials',)] == handoff_int(handoff, r'Across ([\d,]+) channel-trials', 'channel-trials'),
          'handwriting: the channel-trials do not add up')
    rc = e['results']['reason_counts']
    for k, src in (('constant', 'constant'), ('lower_rail', 'lower_rail'), ('upper_rail', 'upper_rail'),
                   ('nonfinite', 'nonfinite'), ('invalid_denominator', 'denominator_invalid')):
        out[V + ('flags', k)] = rc[src]
    ea = {a['arm']: a for a in earlier['aggregate']}
    for a in ('logistic', 'shrinkage_lda'):
        A = R + ('earlier_analysis', 'arms', a, 'balanced_accuracy')
        out.update({A + ('mean',): ea[a]['person_mean']['balanced_accuracy'],
                    A + ('interval_95', 0): ea[a]['person_bootstrap_95ci']['balanced_accuracy'][0],
                    A + ('interval_95', 1): ea[a]['person_bootstrap_95ci']['balanced_accuracy'][1]})
    q, b = earlier['quality_flags'], earlier['bounded_posthoc_quality']
    Q = R + ('earlier_analysis', 'quality_findings')
    out.update({Q + ('windows',): q['digital_rail']['total_eligible_epochs'],
                Q + ('windows_with_a_rail_sample',): q['digital_rail']['epochs'],
                Q + ('windows_over_500_microvolts',): q['ptp_greater_than_500uV']['epochs'],
                Q + ('inspected_windows',): b['windows'], Q + ('channel_windows',): b['total_channel_windows'],
                Q + ('rail_flat_channel_windows',): b['rail_flat_channel_windows']})
    out.update({R + ('independent_audit', 'people'): result_audit['people'],
                R + ('independent_audit', 'reconstructed_models'): result_audit['reconstructed_models'],
                R + ('independent_audit', 'refitted_models'): result_audit['independent_true_label_refits'],
                R + ('independent_audit', 'refitted_shuffle_models'): result_audit['independent_permutation_refits'],
                R + ('independent_audit', 'largest_refit_difference'): e['audit']['max_refit_abs_error']})


def refed(e, audit, out):
    R = ('results', REFED)
    s = e['sample']
    out.update({R + ('cohort', 'nominal_folders'): s['nominal_participant_groups'],
                R + ('cohort', 'videos'): s['unique_shared_video_ids'], R + ('cohort', 'clips'): s['stored_clips']})
    for i, key in enumerate(('shared_stimulus_person_holdout', 'joint_person_video_holdout')):
        C = R + ('conditions', i)
        sc, cov = e['method']['split_conditions'][key], e['metrics']['source_video_lookup_coverage'][key]
        out.update({C + ('folds',): sc['folds'], C + ('training_clips_per_fold',): sc['training_clips_per_fold'],
                    C + ('held_clips_per_fold',): sc['held_clips_per_fold'], C + ('clips_scored',): cov['held_clips'],
                    C + ('lookup_matched_videos',): cov['matched_source_video_ids']})
        for arm, v in e['metrics']['pooled'][key].items():
            out[C + ('arms', arm, 'equal_axis_mae')] = v['equal_axis_mean_MAE']
    qu = e['quality']
    out.update({R + ('quality', 'clips_checked'): qu['stored_clips_audited'],
                R + ('quality', 'channel_clip_rows'): qu['channel_clip_rows_audited'],
                R + ('quality', 'clips_or_channels_removed'): qu['clips_or_channels_removed'],
                R + ('independent_audit', 'assertions'): audit['checks']['assertions_passed'],
                R + ('independent_audit', 'categories'): audit['checks']['unique_categories'],
                R + ('independent_audit', 'largest_metric_difference'):
                    audit['numerical_verification']['maximum_metric_absolute_error']})


def dataset_nulls(manifest, out):
    """Statements a source does not make stay null."""
    for d in manifest['datasets']:
        ce = d['consentEthics']
        D = ('datasets', d['id'], 'consent_and_ethics')
        if ce['status'] == 'owner_decision':
            out[D + ('ethics_approval', 'statement')] = None
        elif ce['status'] == 'not_stated':
            out[D + ('ethics_approval', 'statement')] = None
            out[D + ('informed_consent', 'statement')] = None


# ---------------------------------------------------------------------------- walking the served file
def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    elif value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        yield trail, value


def flags(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == 'interval_excludes_zero':
                yield trail, v
            yield from flags(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flags(v, trail + (i,))


def floats(value):
    return [v for _, v in leaves(value) if isinstance(v, float)]


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served = [p.read_bytes() for p in SERVED]
    check(served[0] == served[1], 'the two served copies differ')
    payload = json.loads(served[0])
    check(payload['release_id'] == manifest['release_id'] and payload['provenance']['manifest_sha256'] == digest(manifest_bytes),
          'the served file names another manifest')
    src = {s['id']: s for s in manifest['sources']}
    check(tuple(src) == IDS, 'the manifest names other sources')
    released = [s for s in IDS if src[s]['publication'] == 'released']
    held = [s for s in IDS if src[s]['publication'] == 'status_only']
    check(sorted(released + held) == sorted(IDS), 'a source is neither released nor held')
    check(list(payload['results']) == released and payload['provenance']['held_sources'] == held,
          'the served results are not the manifest’s released sources')

    exports, bound = {}, {}
    for sid in IDS:
        raw = load(src[sid]['export'])
        bound[sid] = binding(src[sid])
        check(bound[sid] == digest(raw), f'{sid}: its approval record names other export bytes')
        exports[sid] = json.loads(raw)
    check(payload['provenance']['source_export_sha256'] == {s: digest(load(src[s]['export'])) for s in released},
          'the served file names other export bytes')

    expected, derived, secret = {}, set(), []
    orthosis_64(exports[O64], text(src[O64]['handoff']), expected, derived, secret)
    orthosis_58(exports[O58], expected, derived)
    orthosis_fm(exports[OFM], exports[O58], expected, derived)
    bdocs = next(d for d in manifest['datasets'] if d['id'] == 'bingo-imagined-speech')['sourceDocuments']
    bingo(exports[BINGO], text(src[BINGO]['handoff']), text(bdocs['datasetDocumentation']['text']),
          text(bdocs['consentDocument']['text']), expected, derived)
    handwriting(exports[HAND], jload(src[HAND]['earlierExport']), jload(src[HAND]['resultAudit']),
                text(src[HAND]['handoff']), expected, derived, secret)
    refed(exports[REFED], jload(src[REFED]['resultAudit']), expected)
    held_figures = {}
    for sid in held:   # a held source's figures are not expected anywhere, and must not appear
        held_figures[sid] = {v for p, v in expected.items() if p[:2] == ('results', sid) and isinstance(v, float)}
        expected = {p: v for p, v in expected.items() if p[:2] != ('results', sid)}
    dataset_nulls(manifest, expected)

    found = dict(leaves(payload))
    unaudited = sorted(map(str, set(found) - set(expected)))
    missing = sorted(map(str, set(expected) - set(found)))
    check(not unaudited, f'figures in the served file with no audit rule: {unaudited[:5]}')
    check(not missing, f'audited figures missing from the served file: {missing[:5]}')
    exact = recomputed = nulls = 0
    for path, want in expected.items():
        got = found[path]
        if want is None:
            check(got is None, f'{path}: a null became {got!r}')
            nulls += 1
        elif path in derived:
            check(got is not None and type(got) is type(want) and math.isclose(got, want, rel_tol=1e-12, abs_tol=0),
                  f'{path}: {got!r} != {want!r}')
            recomputed += 1
        else:
            check(type(got) is type(want) and got == want, f'{path}: {got!r} != {want!r}')
            exact += 1

    n_flags = 0
    for trail, flag in flags(payload):
        node = payload
        for k in trail:
            node = node[k]
        ivs = [v['interval_95'] for v in node.values() if isinstance(v, dict) and isinstance(v.get('interval_95'), list)]
        check(len(ivs) == 1 and flag == (ivs[0][0] > 0 or ivs[0][1] < 0), f'{trail}: the flag does not follow')
        n_flags += 1

    published = set(floats(payload))
    for v in secret:
        check(v in TRIVIAL or v not in published, f'a per-person value reached the served file: {v!r}')
    held_checked = 0
    for sid in held:
        for v in held_figures[sid] - TRIVIAL:
            check(v not in published, f'{sid}: a held figure reached the served file: {v!r}')
            held_checked += 1
        check(not any(sid in str(p) for p in found), f'{sid}: a held result has a figure')

    by_result = {sid: sum(1 for p in expected if p[:2] == ('results', sid)) for sid in released}
    return {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': digest(served[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_pilot_studies_export.py',
        'independence': 'A separate program from the export. It reads the served bytes, the review manifest, the six '
                        'pinned approved exports and the approval or finalization record that names each one, plus '
                        'the pinned handoffs and BINGO deliverables for the few counts no export carries; it builds its '
                        'own table of what every figure must be and shares no extraction code with the export.',
        'source_export_sha256': {sid: bound[sid] for sid in IDS},
        'included': released, 'held_sources': held, 'status_only': [s['id'] for s in payload['status_only']],
        'holds': payload['provenance']['holds'],
        'figures_compared': len(expected), 'figures_by_result': by_result,
        'copied_exactly': exact, 'recomputed': recomputed, 'nulls_kept': nulls, 'interval_flags_recomputed': n_flags,
        'per_person_values_checked_absent': len(secret), 'held_values_checked_absent': held_checked,
        'figures_from_text_only': [
            'Orthosis exclusions (8 baseline runs, 82 targets without a following movement, 1 window crossing a '
            'boundary): the pinned Orthosis baseline handoff',
            'BINGO window samples, trials per language per held-out field, trials per noun and language, training rows, '
            'fit and checkpoint counts and reconstructed models: the pinned BINGO handoff',
            'BINGO protocol timeline, nouns and repetitions: D3.1 version 2.0 (pinned text); the project-reported '
            'subject-independent accuracy and vocabulary: D3.1 version 3.0 (pinned text)',
            'handwriting channels recorded and channel-trials: the pinned mask-aware handoff',
        ],
        'checks': [
            'each export is the pinned file and the one its own approval, handoff check or finalization record names; '
            'the served file names the same hashes for the released sources and the manifest it was built from; the '
            'two served copies are byte-identical',
            'every number and null in the served file has an expected value derived here from the exports, and every '
            'expected value is in the file: no unaudited figure and no missing one',
            'copied figures equal the source export exactly, type included; chance levels, the Orthosis error share, '
            'shuffle means (with their observed ranges as the extremes of the replicates) and the handwriting '
            'channel-trial count are recomputed here',
            'the classical and control rows of the EEGPT comparison equal the separately approved 58-channel classical '
            'export, row for row',
            'nulls stay null: the Orthosis matched-difference interval (none computed), the handwriting mask-only '
            'control’s interval (withheld), the EEGPT weights licence, and consent or ethics statements a source does not '
            'make',
            'every interval_excludes_zero flag follows from its interval',
            'no Orthosis per-person value (the matched EEG-minus-confound range and the three-person response-clean '
            'scores) reaches the file, nor the bounds of the handwriting mask-only control’s withheld interval',
            'a source the manifest holds has no result, and none of its export’s figures appears in the file',
        ],
        'audit_bindings': {
            'bound': [
                'source export bytes: pinned in the manifest, named by each source’s own approval record, named in the '
                'served file',
                'every figure: equal to its export leaf, or recomputed from export leaves, or read from the pinned text '
                'listed under figures_from_text_only',
            ],
            'not_bound': [
                'the QA records, release decisions and independent result audits behind each export are verified by the '
                'export (their verdicts and hash chains), not re-read here',
                'rights evidence (licence records, consent quotes) and prose in the served file are checked by the '
                'export, not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
