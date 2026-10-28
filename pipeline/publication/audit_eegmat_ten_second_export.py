"""Independent audit of eegmat-ten-second-update.json: every figure in the served file against the pinned sources.

A separate program from export_eegmat_ten_second_update.py. It shares no code with that export and imports nothing
from it: it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what
every number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- the scores, paired differences and intervals are read from where the export does not read them where a second
  record exists: AXON's from the corrected audit's independent scores (the export reads the released aggregate);
  EEG-Captioner's from the audit outcome, required equal to the interpretation review's verified percentage points and
  to the four-decimal figures AXON's frozen protocol records as known beforehand;
- derived figures are recomputed here from other fields than the export reads: the cohort from AXON's protocol and the
  QC summary by fold, the QC rule from the handoff's text, the head from AXON's protocol, the bootstrap from AXON's
  protocol, dimensions and flags from the handoffs, identities from the strict-load packet and the probe handoff;
- labels, readings, the beside-score lines, identities, licences, hashes and the not-published list are checked as
  strings;
- the two served copies are one, the served file names the manifest it was built from, and no per-fold, pooled,
  confusion, QC-breakdown or accounting value, no private path and no private user, host or volume name is in it.

    python3 pipeline/publication/audit_eegmat_ten_second_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'eegmat-ten-second-release-manifest.json'
AUDIT = REVIEW / 'eegmat-ten-second-export-audit.json'
SERVED = (PROJECT / 'site/src/data/eegmat-ten-second-update.json',
          PROJECT / 'site/public/data/eegmat-ten-second-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
# The editorial decisions this audit holds the file to (plan section 2.3 and the manifest's preview defaults).
TITLES = {'eeg_captioner': 'EEG-Captioner encoder, mean-token 256-d + ridge', 'axon': 'AXON, 512-d + ridge'}
WELCH = 'Welch band power (95-d, 0.5–45 Hz, ten-second windows)'
NOTES = {'eeg_captioner': 'matched for this run',
         'axon': 'the same predictions reused without refitting; not matched for normalisation or parameter count'}
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')
LIMITATION_IDS = ['recording-order', 'exposure', 'axon-inputs', 'upstream-recording', 'scope']
AXON_LIMITATION_IDS = ['pretraining-not-isolated', 'outcomes-known']
NOT_RANKED = ['core-matrix', 'frozen-rows', 'labram-last-block', 'neurolm-panel', 'neurorvq-panel']


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw(ref):
    data = (PROJECT / ref['path']).read_bytes()
    check(digest(data) == ref['sha256'], f'{Path(ref["path"]).name}: not the pinned bytes')
    return data


def same_number(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


def num(token):
    token = token.replace(',', '')
    return float(token) if '.' in token else int(token)


def find(pattern, text, label):
    m = re.search(pattern, re.sub(r'\s+', ' ', text))
    check(m is not None, f'{label}: the pinned record no longer states it')
    return m


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {'manifest': manifest}
    for group in ('captioner', 'axon', 'planning', 'published'):
        s[group] = {}
        for k, r in manifest[group].items():
            if isinstance(r, dict):
                data = raw(r)
                s[group][k] = json.loads(data) if r['path'].endswith('.json') else data.decode('utf-8')
    return s


def scores(s):
    """Both subsections' figures, each from the record this audit reads for it."""
    c, a = s['captioner'], s['axon']
    out = c['outcome']['aggregate_scores']
    cap = {'encoder': out['encoder']['mean_subject_BA'], 'baseline': out['baseline']['mean_subject_BA'],
           'difference': out['mean_difference'], 'interval': list(out['descriptive_fixed_cohort_bootstrap95'])}
    nv = c['interpretation']['numeric_verification']
    check(nv['paired_mean_difference_pp'] / 100 == cap['difference']
          and [v / 100 for v in nv['bootstrap95_pp']] == cap['interval'], 'the interpretation review verified others')
    known = re.sub(r'\s+', '', a['protocol']['claim_limits']['known_prior'])
    check(f'Captioner{100 * cap["encoder"]:.4f}%' in known and f'baseline{100 * cap["baseline"]:.4f}%' in known
          and f'difference{100 * cap["difference"]:.4f}pp' in known
          and f'interval[{100 * cap["interval"][0]:.4f},{100 * cap["interval"][1]:+.4f}]' in known,
          'AXON’s protocol recorded other EEG-Captioner figures')
    ind = a['correctedAudit']['aggregate_independent_scores']
    ax = {'encoder': ind['axon']['mean_subject_BA'], 'baseline': ind['baseline']['mean_subject_BA'],
          'difference': ind['mean_difference'], 'interval': list(ind['bootstrap']['percentile95'])}
    check(ax['baseline'] == cap['baseline'], 'the corrected audit scored another baseline')
    for x in (cap, ax):
        check(x['interval'][0] <= x['difference'] <= x['interval'][1], 'an interval does not hold its estimate')
        check(abs(x['encoder'] - x['baseline'] - x['difference']) <= 1e-12, 'a difference is not its arms’')
    return cap, ax


def expected_table(s, served):
    E = {}
    c, a, pub, m = s['captioner'], s['axon'], s['published'], s['manifest']
    out, ap, ch, ih = c['outcome'], c['approval'], c['handoff'], c['intakeHandoff']
    ag, ap2, ah, ca = a['aggregate'], a['protocol'], a['handoff'], a['correctedAudit']
    defaults = ' '.join(m['approval']['previewDefaults'])
    cap, ax = scores(s)

    # placement
    arith = next(t for t in pub['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    check('outside the pilot count' in defaults and 'No shared table' in defaults
          and 'no new dataset, model or pilot in any counter' in defaults, 'the preview defaults changed')
    E[('placement', 'counted_in_pilots')] = False
    E[('placement', 'leaderboard')] = ap['main_comparison_leaderboard_allowed'] or a['review']['main_leaderboard_eligible']
    E[('placement', 'core_matrix_row')] = any(re.search(r'captioner|axon', r['name'], re.I) for r in arith['rows'])
    E[('placement', 'new_dataset_count')] = 0 if arith['dataset'] == ag['dataset'] else 1
    E[('placement', 'new_model_count')] = 0
    E[('placement', 'shared_table')] = False

    # cohort: AXON's protocol, the QC summary by fold and the aggregate's folds
    folds = ag['outer_subject_folds']
    qf = out['QC_summary_aggregate']['fold'].values()
    cohort = {'people': sum(folds), 'recordings': sum(x['recordings'] for x in qf),
              'conditions': len(out['QC_summary_aggregate']['condition']), 'windows': ap2['cohort']['windows'],
              'window_seconds': ap2['cohort']['window_seconds'], 'channels': len(ap2['cache_channel_order']),
              'sampling_hz': ap2['cohort']['sfreq'], 'folds': len(folds)}
    cohort['windows_per_recording'] = cohort['windows'] // cohort['recordings']
    cohort['retained_seconds'] = cohort['window_seconds'] * cohort['windows_per_recording']
    check(cohort['recordings'] == cohort['conditions'] * cohort['people']
          and cohort['windows'] == cohort['recordings'] * cohort['windows_per_recording']
          and ap2['cohort']['samples'] == cohort['window_seconds'] * cohort['sampling_hz'], 'the cohort does not add up')
    for k, v in cohort.items():
        E[('cohort', k)] = v
    E[('cohort', 'same_windows_both_encoders')] = (ap2['inputs']['physical']['sha256']
                                                   == out['audit']['checked_files']['physical.npy'])
    pre = find(r'(whole-record)(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)Hz/(\d+)Hz/notch/resample(\d+)Hz', ap2['active_preprocessing'][0],
               'AXON cache preprocessing')
    E[('cohort', 'preprocessing', 'whole_recording')] = pre.group(1) == 'whole-record'
    E[('cohort', 'preprocessing', 'band_pass_hz', 0)] = num(pre.group(2))
    E[('cohort', 'preprocessing', 'band_pass_hz', 1)] = num(pre.group(3))
    E[('cohort', 'preprocessing', 'notch_hz')] = num(pre.group(4))
    E[('cohort', 'preprocessing', 'sampling_hz')] = num(pre.group(5))

    # source annotation QC: totals by fold, the rule from the handoff's text
    q = ('source_annotation_qc',)
    eligible = sum(x['source_eligible_windows'] for x in qf)
    E[q + ('windows',)] = sum(x['flagged_windows'] for x in qf) + eligible
    E[q + ('windows_meeting_rules',)] = eligible
    E[q + ('recordings',)] = sum(x['recordings'] for x in qf)
    E[q + ('recordings_flagged',)] = sum(x['bad_trials'] for x in qf)
    r1 = find(r'flagged-channel ratio >(\d+(?:\.\d+)?) or summed BAD-annotation duration ratio >(\d+(?:\.\d+)?)', ch, 'QC rule')
    r2 = find(r'Its (\d+) µV peak and (\d+) µV flat parameters are MNE adjacent-sample amplitude criteria, with (\d+)% '
              r'channel threshold and (\d+(?:\.\d+)?)-second minimum duration', ch, 'QC rule')
    r3 = find(r"The source's (\d+) µV hard-peak segment rule", ch, 'QC rule')
    for key, token in (('flagged_channel_ratio_above', r1.group(1)), ('bad_duration_ratio_above', r1.group(2)),
                       ('channel_peak_uv', r2.group(1)), ('channel_flat_uv', r2.group(2)),
                       ('channel_bad_percent', r2.group(3)), ('minimum_bad_duration_s', r2.group(4)),
                       ('segment_hard_peak_uv', r3.group(1))):
        E[q + ('rule', key)] = num(token)
    unused = "did not modify either arm's input or determine inclusion" in re.sub(r'\s+', ' ', ch)
    E[q + ('selects_windows',)] = not unused
    E[q + ('changes_inputs',)] = not unused
    E[q + ('recomputed_by_audit',)] = ap['source_QC_recomputed']

    # probe: AXON's protocol
    head = ap2['heads']['head']
    rc = find(r'RidgeClassifier\(alpha=(\d+),class_weight=balanced,fit_intercept=(True|False),solver=svd', head, 'head')
    E[('probe', 'alpha')] = int(rc.group(1))
    E[('probe', 'fit_intercept')] = rc.group(2) == 'True'
    E[('probe', 'fits_per_representation')] = ap2['heads']['fits']
    E[('probe', 'hyperparameter_search')] = 'There is no hyperparameter search' not in ch
    E[('probe', 'encoder_fine_tuning')] = 'There is no hyperparameter search, encoder fine-tuning' not in ah
    E[('probe', 'sealed_before_scoring')] = 'global prediction sealing' in ch and 'global prediction sealing' in ah
    E[('probe', 'shared_by_both_encoders')] = rc.group(0) in c['protocol']['splits_heads_metrics']['head']

    # interval: AXON's protocol, compared with EEG-Captioner's addendum
    u, bc = ap2['uncertainty'], c['protocol']['prospective_addendum']['bootstrap']
    pct = find(r'percentile(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)', u['interval'], 'AXON interval')
    E[('interval', 'level')] = (float(pct.group(2)) - float(pct.group(1))) / 100
    E[('interval', 'draws')] = u['replicates']
    E[('interval', 'seed')] = u['seed']
    E[('interval', 'same_rule_both_encoders')] = (bc['replicates'], bc['seed'], bc['unit'], bc['purpose']) == (
        u['replicates'], u['seed'], u['unit'], u['purpose'])
    E[('interval', 'prespecified')] = (c['protocol']['prospective_addendum']['admitted_before_outcomes'] is True
                                       and 'No AXON outcome existed at freeze' in ap2['claim_limits']['known_prior'])
    E[('interval', 'both_span_zero')] = all(x['interval'][0] <= 0 <= x['interval'][1] for x in (cap, ax))

    # EEG-Captioner: dimensions and input from the handoffs, scores from the audit outcome
    e = ('eeg_captioner',)
    dim = num(find(r'mean-pooled to a (\d+)-dimensional representation', ch, 'pooling').group(1))
    E[e + ('representation', 'dimension')] = dim
    E[e + ('representation', 'tokens')] = num(find(r"The encoder's (\d+) tokens", ch, 'tokens').group(1))
    E[e + ('input', 'measured_channels')] = num(find(r'The (\d+) required measured channels', ch, 'channels').group(1))
    E[e + ('input', 'zero_oz_channel')] = 'inserts the permitted zero Oz channel' in ch
    shape = find(r'`\[batch,(\d+),(\d+),(\d+)\]` and divides by (\d+)', ch, 'encoder input')
    E[e + ('input', 'model_channels')] = num(shape.group(1))
    E[e + ('input', 'amplitude_divisor')] = num(shape.group(4))
    E[e + ('encoder_only',)] = 'Qwen, the projector and language LoRA were not used' in ch
    E[e + ('caption_result',)] = 'No caption correctness or language-conditioning result is produced here' not in ch
    E[e + ('language_model_loaded',)] = 'Qwen, the projector and language LoRA were not used' not in ch
    welch = num(find(r'Matched (\d+)-dimensional Welch bandpower baseline', ch, 'Welch').group(1))
    E[e + ('arms', 0, 'dimension')] = dim
    E[e + ('arms', 0, 'balanced_accuracy')] = cap['encoder']
    E[e + ('arms', 1, 'dimension')] = welch
    E[e + ('arms', 1, 'balanced_accuracy')] = cap['baseline']
    E[e + ('baseline', 'matched')] = f'Matched {welch}-dimensional Welch' in ch
    E[e + ('baseline', 'fitted_in_this_run')] = 'baseline' in out['audit']['arms'] and out['audit'][
        'independent_heads_recomputed'] is True
    E[e + ('identity', 'encoder_bytes')] = num(find(r'Encoder artifact: ([\d,]+) bytes', ch, 'encoder bytes').group(1))
    for k, v in (('frozen', True), ('fine_tuning', False), ('weights_distributed', False)):
        E[e + ('identity', k)] = v
    E[e + ('rights', 'weights', 'distributed')] = False
    au = out['audit']
    E[e + ('audit', 'rows_reproduced')] = au['rows']
    E[e + ('audit', 'feature_max_abs_error')] = max(au['feature_max_abs_error'].values())
    E[e + ('audit', 'heads_refitted')] = au['independent_heads_recomputed']
    hard = num(find(r'reproduced all ([\d,]+) hard predictions exactly', ch, 'refits').group(1))
    E[e + ('audit', 'hard_predictions_reproduced_exactly')] = hard == 2 * cohort['windows']
    # The bound on the refitted heads' decision scores: the power of ten above the errors the handoff rounds.
    errs = find(r'maximum decision-score errors were approximately `([\d.]+e-\d+)` and `([\d.]+e-\d+)`', ch, 'head errors')
    E[e + ('audit', 'head_decision_score_error_below')] = 10 ** math.ceil(math.log10(max(map(float, errs.groups()))))
    E[e + ('audit', 'scores_and_bootstrap_matched')] = 'All metrics and the paired bootstrap matched.' in ch
    E[e + ('audit', 'raw_preprocessing_recomputed')] = au['raw_preprocessing_recomputed']
    E[e + ('audit', 'source_qc_recomputed')] = au['source_QC_recomputed']
    E[e + ('audit', 'producer_helpers_imported')] = 'imports no producer scientific helpers' not in out['authorship']

    # AXON: the protocol, the handoff, the corrected audit, the packet and the access record
    x = ('axon',)
    adim = ap2['features']['shape'][1]
    E[x + ('representation', 'dimension')] = adim
    E[x + ('input', 'measured_channels')] = ap2['numeric_gate']['shape'][1]
    E[x + ('input', 'reordered_to_model_order')] = ap2['permutation'] != list(range(len(ap2['permutation'])))
    nosynth = ap2['active_preprocessing'][2]
    E[x + ('input', 'zero_oz_channel')] = not nosynth.startswith('No syntheticOz')
    E[x + ('input', 'divided_by_100')] = '/100' not in nosynth.split(',additional')[0]
    E[x + ('input', 'own_standardisation')] = 'AXON internal per-window' in ap2['active_preprocessing'][1]
    E[x + ('input', 'template_positions')] = ap2['geometry_gate']['status'] == 'PASS_NOMINAL_TEMPLATE_EXPLICIT_MAPPING_ONLY'
    E[x + ('input', 'digitised_positions')] = ap2['geometry_gate']['measured_subject_geometry_verified']
    E[x + ('native_head_used',)] = 'never use its logits as task accuracy' not in ap2['model']['untrained_head']
    E[x + ('arms', 0, 'dimension')] = adim
    E[x + ('arms', 0, 'balanced_accuracy')] = ax['encoder']
    E[x + ('arms', 1, 'dimension')] = num(find(r'Previously audited (\d+)-dimensional Welch baseline', ah,
                                              'AXON Welch').group(1))
    E[x + ('arms', 1, 'balanced_accuracy')] = ax['baseline']
    unmatched = 'is not normalization/parameter-count matched' in ap2['baseline']
    E[x + ('baseline', 'matched')] = not unmatched
    E[x + ('baseline', 'fitted_in_this_run')] = 'do not rerun baseline' not in ap2['baseline']
    E[x + ('baseline', 'matched_normalisation')] = not unmatched
    E[x + ('baseline', 'matched_parameter_count')] = not unmatched
    E[x + ('baseline', 'isolates_pretraining')] = 'cannot isolate the contribution of pretraining' not in ah
    E[x + ('numerical_input_check', 'windows_passed')] = num(find(r'All (\d+) pass the separate AXON numerical', ah,
                                                                 'AXON gate').group(1))
    E[x + ('numerical_input_check', 'windows')] = ap2['numeric_gate']['shape'][0]
    E[x + ('numerical_input_check', 'minimum_channel_std_uv')] = ap2['numeric_gate']['minimum_exclusive_uV']
    E[x + ('numerical_input_check', 'separate_from_source_qc')] = 'These are different gates' in ah
    E[x + ('identity', 'checkpoint_bytes')] = num(find(r'\*\*([\d,]+) bytes\*\*', a['loadPacket'], 'AXON bytes').group(1))
    for k, v in (('frozen', True), ('fine_tuning', False), ('weights_distributed', False)):
        E[x + ('identity', k)] = v
    E[x + ('rights', 'checkpoint', 'gated')] = a['access']['gated']
    E[x + ('rights', 'checkpoint', 'distributed')] = False
    fc, agau, term = a['featureComparison']['aggregate'], ag['audit'], ca['terminal']
    E[x + ('audit', 'raw_preprocessing_recomputed')] = ap2['claim_limits']['raw_preprocessing_recomputed']
    E[x + ('audit', 'first_audit', 'kept')] = agau['original_feature_reconstruction'] == 'FAIL retained'
    E[x + ('audit', 'first_audit', 'rtol')] = fc['rtol']
    E[x + ('audit', 'first_audit', 'atol')] = fc['atol']
    cx = x + ('audit', 'corrected_audit')
    E[cx + ('rows_reproduced',)] = fc['counts']['forwards']
    E[cx + ('byte_identical',)] = fc['features_sha256'] == fc['producer_features_sha256']
    E[cx + ('feature_max_abs_error',)] = fc['max_abs_error']
    E[cx + ('heads_refitted',)] = term['correction_counts']['head_fits'] == cohort['folds']
    E[cx + ('tolerance_relaxed',)] = term['tolerances_modified']
    E[x + ('audit', 'production_unchanged')] = agau['producer_predictions_unchanged']
    E[x + ('audit', 'producer_rerun')] = agau['producer_rerun']

    # paired differences, with their flags
    for key, vals in (('eeg_captioner', cap), ('axon', ax)):
        pd = (key, 'paired_difference')
        E[pd + ('difference',)] = vals['difference']
        E[pd + ('interval_95', 0)], E[pd + ('interval_95', 1)] = vals['interval']
        E[pd + ('interval_includes_zero',)] = vals['interval'][0] <= 0 <= vals['interval'][1]

    # no encoder contrast; separation from the two-second results
    E[('encoder_contrast', 'published')] = 'no encoder-against-encoder difference' not in defaults
    E[('encoder_contrast', 'same_inputs')] = (E[e + ('input', 'zero_oz_channel')] == E[x + ('input', 'zero_oz_channel')]
                                              and not E[x + ('input', 'reordered_to_model_order')])
    E[('encoder_contrast', 'axon_ran_after_outcomes_known')] = 'known prospectively' in ap2['claim_limits']['known_prior']
    sp = ('separate_from_two_second_results',)
    core = pub['neurolmEegmat']['separate_from_core']
    E[sp + ('ranked_against_two_second_results',)] = 'not ranked against any two-second EEGMAT result' not in defaults
    E[sp + ('window_seconds',)] = cohort['window_seconds']
    E[sp + ('two_second_window_seconds',)] = next(p for p in pub['eegptCore']['protocols']
                                                  if p['id'] == 'arithmetic-rest')['window_seconds']
    E[sp + ('core_band_pass',)] = core['core_band_pass']
    E[sp + ('core_sampling_hz',)] = core['core_sampling_hz']
    return E, cap, ax, cohort


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest, cohort):
    c, a, pub = s['captioner'], s['axon'], s['published']
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['freeze_date']
          and manifest['freeze_date'].replace('-', '') == manifest['release_id'].rsplit('-', 1)[1], 'another release')
    check(served['status'] == 'aggregate_preview' == manifest['approval']['decision'], 'another decision')
    check(served['placement']['anchor'] == 'eegmat-ten-second' and served['placement']['page'] == '/topics/pilot-studies/'
          and served['placement']['subsections'] == ['eeg_captioner', 'axon'], 'another placement')
    for key in ('eeg_captioner', 'axon'):
        b = served[key]
        check(b['title'] == TITLES[key] and b['arms'][0]['label'] == TITLES[key] and b['arms'][1]['label'] == WELCH
              and b['arms'][1]['note'] == NOTES[key] and [x['role'] for x in b['arms']] == ['encoder', 'baseline'],
              f'{key}: not the reviewed labels')
        pd = b['paired_difference']
        want = SPANS_ZERO if pd['interval_includes_zero'] else None
        check(pd['reading'] == want, f'{key}: another reading')
        check(pd['a'] == b['arms'][0]['id'] and pd['b'] == b['arms'][1]['id'] == 'welch-band-power',
              f'{key}: another contrast')
        check(b['pretraining_exposure'] == 'unknown', f'{key}: the exposure is not the pinned fact')
    check(a['aggregate']['quality_scope']['pretraining_exposure'] == 'unknown', 'AXON’s exposure was resolved')
    check('Unknown pretraining exposure' in json.dumps(c['protocol']['limitations']), 'EEG-Captioner’s exposure changed')
    check(served['cohort']['channel_names'] == a['protocol']['cache_channel_order'], 'another montage')
    qc = served['source_annotation_qc']
    check(qc['beside_every_score'] == (f'{qc["windows_meeting_rules"]} of {qc["windows"]} windows meet '
                                       f'EEG-Captioner’s source annotation-QC rules, and {qc["recordings_flagged"]} of '
                                       f'{qc["recordings"]} recordings are flagged by them.'), 'another QC line')
    n = served['axon']['numerical_input_check']
    check(n['beside_score'] == f'AXON’s own numerical input check passed {n["windows_passed"]} of {n["windows"]}, a '
                               f'different check', 'another numerical-check line')
    # identities
    ch, ih = c['handoff'], c['intakeHandoff']
    ci = served['eeg_captioner']['identity']
    w = re.search(r'Weight repository: `([\w-]+/[\w-]+)`, revision `([0-9a-f]{40})`', ch)
    src = re.search(r'Source repository: `([\w-]+/[\w-]+)`, commit `([0-9a-f]{40})`', ch)
    enc = re.search(r'Encoder artifact: [\d,]+ bytes; SHA-256 `([0-9a-f]{64})`', ch)
    check(w and src and enc, 'the probe handoff no longer states the identity')
    check(ci['hf_repository'] == f'https://huggingface.co/{w.group(1)}' and ci['hf_revision'] == w.group(2)
          and ci['source_repository'] == f'https://github.com/{src.group(1)}' and ci['source_revision'] == src.group(2)
          == c['protocol']['identity']['source_revision'] and ci['encoder_sha256'] == enc.group(1)
          == c['protocol']['identity']['encoder_sha256'], 'another EEG-Captioner identity')
    check(f'revision `{w.group(2)}`' in ih and f'SHA-256 `{enc.group(1)}`' in ih, 'the intake names another encoder')
    ai, ag = served['axon']['identity'], a['aggregate']
    pk = a['loadPacket']
    check(ai['hf_repository'] == f'https://huggingface.co/{ag["checkpoint_repository"]}'
          and ai['hf_revision'] == ag['checkpoint_revision'] == a['access']['sha']
          and ai['checkpoint_sha256'] == ag['checkpoint_sha256'] == a['protocol']['model']['checkpoint']['sha256']
          and ai['source_revision'] == ag['source_commit'] and f'braindecode/braindecode@{ag["source_commit"]}' in pk
          and f'LFS SHA256 `{ag["checkpoint_sha256"]}`' in pk, 'another AXON identity')
    check(ai['source_repository'] == 'https://github.com/braindecode/braindecode'
          and ai['module'] == 'braindecode.models.AXON' and '[`braindecode.models.AXON`]' in a['card'],
          'another AXON module')
    # licences per part, as the sources state them
    cr, ar = served['eeg_captioner']['rights'], served['axon']['rights']
    check(cr['code']['licence'] == 'MIT' and '(MIT code)' in ch and 'Source code: MIT.' in ih, 'EEG-Captioner code')
    check(cr['weights']['licence'] == 'Apache-2.0' and '(Apache-2.0 portable weight metadata)' in ch
          and 'Portable weight metadata: Apache-2.0.' in ih, 'EEG-Captioner weights')
    check(ar['checkpoint']['licence'] == 'Apache-2.0' and re.search(r'^license: apache-2\.0$', a['card'], re.M)
          and a['access']['cardData']['license'] == 'apache-2.0', 'AXON checkpoint licence')
    check(ar['module']['licence'] == 'Apache-2.0' and ar['project']['licence'] == 'BSD-3-Clause'
          and 'AXON has per-file Apache-2.0 terms while the project root license is BSD-3-Clause' in pk,
          'AXON module and project licences')
    # the dataset's released record
    track = next(t for t in pub['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    rd = served['rights']['dataset']
    for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt', 'reviewBasis',
              'rightsScope'):
        check(rd[k] == track[k], f'the EEGMAT rights record is not the released one ({k})')
    check(rd['name'] == track['dataset'] and served['cohort']['source'] == track['source'], 'another dataset')
    check([x['id'] for x in served['limitations']] == LIMITATION_IDS, 'the limitations changed')
    check([x['id'] for x in served['axon']['limitations']] == AXON_LIMITATION_IDS, 'AXON’s own limitations changed')
    check([x['id'] for x in served['separate_from_two_second_results']['not_ranked_against']] == NOT_RANKED,
          'the separation list changed')
    rm, ra = manifest['captioner'], manifest['axon']
    pv = served['provenance']
    check(pv['source_export_sha256'] == {'eeg-captioner': rm['outcome']['sha256'], 'axon': ra['aggregate']['sha256']}
          and pv['release_approval_sha256'] == {'eeg-captioner': rm['approval']['sha256'], 'axon': ra['review']['sha256']}
          and pv['protocol_sha256'] == {'eeg-captioner': rm['protocol']['sha256'], 'axon': ra['protocol']['sha256']},
          'provenance differs')
    check(c['approval']['independent_outcome_sha256'] == rm['outcome']['sha256']
          and a['review']['release_files_sha256'][Path(ra['aggregate']['path']).name] == ra['aggregate']['sha256'],
          'an approval names another aggregate')
    rs = served['release_record']['research_release_status']
    check(rs == {'eeg_captioner': c['approval']['status'], 'axon': a['review']['decision']}, 'another research status')
    check(served['release_record']['research_release'] == manifest['releaseRecord']['researchRelease']
          and c['approval']['publication_authorized'] is False
          and 'does not itself authorise publication' in served['release_record']['research_release'],
          'the research release reads as an authorisation the approval does not make')
    check(served['not_published'] == manifest['notPublished'], 'the not-published list is not the manifest’s')


# ---------------------------------------------------------------------------- the served file
def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    elif value is None or isinstance(value, (bool, int, float)):
        yield trail, value


def private_names(s):
    a, c = s['axon'], s['captioner']
    blob = json.dumps(a['protocol']) + c['handoff'] + a['handoff'] + c['intakeHandoff']
    names = {x for pair in re.findall(r'/home/([^/"\s`]+)/([^/"\s`]+)/', blob) for x in pair}
    names |= {x for pair in re.findall(r'/mnt/([^/"\s`]+)/([^/"\s`]+)/', blob) for x in pair}
    names |= set(re.findall(r'(?:private|acquired) on (\w+)', blob))
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Per-fold, pooled, confusion, QC-breakdown and accounting values: never published."""
    c, a = s['captioner'], s['axon']
    out = set()
    for src in (c['outcome']['aggregate_scores'], a['aggregate']['results']):
        for arm in ('encoder', 'baseline', 'axon'):
            if arm in src:
                out |= set(src[arm]['folds'].values()) | {src[arm]['pooled']['macroF1']}
                out |= {v for row in src[arm]['pooled']['confusion_matrix'] for v in row}
    for x in c['outcome']['QC_summary_aggregate']['condition'].values():
        out.add(x['flagged_channels'])
    for x in c['outcome']['QC_summary_aggregate']['fold'].values():
        out |= {x['flagged_channels'], x['recordings'], x['bad_trials'], x['flagged_windows']}
    out |= set(c['outcome']['audit']['head_max_abs_error'].values())
    out |= {c['outcome']['guard'][k] for k in ('charged_wall_seconds', 'charged_CPU_seconds', 'peak_observed_RSS_bytes')}
    out |= {c['ledger'][k] for k in ('charged_wall_seconds', 'charged_CPU_seconds', 'peak_observed_RSS_bytes')}
    out |= {a['aggregate']['audit'][k] for k in ('real_forward_counts',
                                                  'CPU_cumulative_including_nonrefundable_preparation_and_cleanup_reserves')}
    t = a['correctedAudit']['terminal']
    out |= {t[k] for k in ('elapsed_seconds', 'audit_correction_CPU_seconds', 'prior_study_CPU_seconds', 'peak_RSS_bytes',
                           'total_real_forwards_if_complete')}
    return out - {0.0, 0.5, 1.0, 2.0}


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    s = sources(manifest)
    E, cap, ax, cohort = expected_table(s, served)
    string_checks(s, served, manifest, cohort)

    found = dict(leaves(served))
    copied_keys = {'balanced_accuracy', 'difference', 'interval_95'}
    copied = {cap['encoder'], cap['baseline'], cap['difference'], *cap['interval'],
              ax['encoder'], ax['baseline'], ax['difference'], *ax['interval']}
    exact = recomputed = nulls = 0
    for path, value in found.items():
        check(path in E, f'{"/".join(map(str, path))}: a figure with no audit rule')
        want = E[path]
        if want is NULL:
            check(value is None, f'{"/".join(map(str, path))}: a null became {value!r}')
            nulls += 1
            continue
        check(same_number(value, want), f'{"/".join(map(str, path))}: {value!r} where the sources give {want!r}')
        if [k for k in path if isinstance(k, str)][-1] in copied_keys:
            check(value in copied, f'{"/".join(map(str, path))}: not a figure of the pinned aggregates')
            exact += 1
        else:
            recomputed += 1
    missing = [p for p in E if p not in found]
    check(not missing, f'expected figures missing from the served file: {missing[:3]}')

    published = {v for v in found.values() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    secret = withheld(s) - {cap['encoder'], cap['baseline'], ax['encoder'], ax['baseline']}
    check(not (secret & published), f'a withheld value reached the served file: {sorted(secret & published)[:3]}')
    text_blob = served_bytes[0].decode()
    private = private_names(s)
    check(len(private) >= 3, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}', text_blob, re.I) is None,
              'a private user, host or volume name reached the served file')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_eegmat_ten_second_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins. AXON’s scores, difference and interval come '
                         'from the corrected audit’s independent scores (the export reads the released aggregate); '
                         'EEG-Captioner’s from the audit outcome, required equal to the interpretation review’s verified '
                         'percentage points and to the figures AXON’s frozen protocol recorded as known beforehand. '
                         'Every other figure is derived by its own reading of AXON’s protocol, the QC summary by fold, '
                         'the handoffs’ text, the strict-load packet and the access record.'),
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'nulls_kept': nulls,
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'scores, paired differences and intervals equal the corrected audit’s independent scores (AXON) and the '
            'audit outcome, the interpretation review and AXON’s protocol (EEG-Captioner); the AXON baseline equals the '
            'EEG-Captioner run’s',
            'cohort counts, preprocessing, the QC totals and rule, the head, the bootstrap, dimensions and the audit '
            'flags are recomputed from AXON’s protocol, the QC summary by fold and the handoffs',
            'titles, baseline notes, readings, the beside-score lines, identities, the licences per part, the EEGMAT '
            'rights record, the hashes, the limitation lists, the research-release wording and the not-published list '
            'are checked as strings',
            'no per-fold, pooled, confusion, QC-breakdown or accounting value, no private path and no private user, '
            'host or volume name in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'EEG-Captioner’s audit outcome, handoff and interpretation review: bound by its release approval; AXON’s '
                'aggregate and handoff: bound by its independent release review, which pins the corrected audit, the '
                'feature comparison and the frozen protocol; the export checks both',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
            ],
            'not_bound': [
                'the encoders’ features themselves: both research audits recomputed them from sealed arrays this audit '
                'does not open, and neither recomputed the raw preprocessing or the source QC',
                'prose, the limitation texts and the release record are checked by the export; this audit checks the '
                'limitation lists by id and the research-release wording only',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
