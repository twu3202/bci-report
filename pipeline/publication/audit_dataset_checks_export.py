"""Independent audit of dataset-checks-update.json: every figure in the served file against the pinned sources.

A separate program from export_dataset_checks_update.py. It shares no code with that export and imports nothing from
it: it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what
every number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- figures are read from where the export does not read them, wherever a second record states them: Kim's design from
  the gate review's prospective scope, its bootstrap settings from the audit's readiness record, its method from the
  gate review and the schema record, and its headline figures checked against the handoff's prose; MIND's counts from
  the workflow closure and the aggregate, its processing facts and resampling settings from the handoff's prose (the
  export reads the frozen protocol), its contrasts against the arithmetic review; Damm's counts from the independent
  audit, the intake QC, the README capture and the execution review; NeBULA's from the EEG audit, the EMG structure
  admission, the EMG metadata and the handoffs' prose (the export reads the boundary diagnostics, the protocols and
  the structure receipt), and its participant counts from the paper, the research intake's file manifest and MOABB's
  catalogue (the export reads the record's description and A2's capture of its files); derived figures (chance, the shifted accuracy interval, seconds from samples, the tie total,
  whether a range spans zero, whether the EMG and EEG lengths agree) are recomputed here;
- the consent, ethics and terms strings are the A2 record's, and every quotation is found verbatim in the capture the
  record names, whose SHA-256 and shasum sidecar are checked; each attribution names the record's creators and DOI
  and ends with the site's sentence;
- the two served copies are one, the served file names the manifest it was built from, data-quality-update.json
  keeps the bytes the 2026-10-20 audit recorded, and no held Damm or NeBULA score, withheld MIND or Kim value,
  register-only figure, private host, storage name or path is in it.

    python3 pipeline/publication/audit_dataset_checks_export.py
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'dataset-checks-release-manifest.json'
AUDIT = REVIEW / 'dataset-checks-export-audit.json'
SERVED = (PROJECT / 'site/src/data/dataset-checks-update.json', PROJECT / 'site/public/data/dataset-checks-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
ENDING = 'Derived analysis by BCI Report; not endorsed by the authors.'
KIM, MIND, DAMM, NEBULA = 'kim2025-beta-range', 'mind2026', 'damm', 'nebula'
CONDITIONS = ('free', 'low', 'high')


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw(ref):
    data = (PROJECT / ref['path']).read_bytes()
    check(digest(data) == ref['sha256'], f'{ref["path"]}: not the pinned bytes')
    return data


def squash(s):
    return re.sub(r'\s+', ' ', s).strip()


def nospace(s):
    return re.sub(r'\s+', '', s)


def visible(text):
    return squash(html.unescape(re.sub(r'<[^>]+>', ' ', text)))


def says(text, phrase, label):
    check(squash(phrase) in squash(text), f'{label}: the pinned record does not say {phrase!r}')


def says_tight(text, phrase, label):
    check(nospace(phrase) in nospace(text), f'{label}: the pinned record does not say {phrase!r}')


def same_value(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


def number_in(text, pattern, label, group=1):
    m = re.search(pattern, squash(text))
    check(m is not None, f'{label}: not stated in the pinned record')
    return m.group(group)


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {}
    for group in ('sources', 'withheldReference'):
        for k, ref in manifest[group].items():
            data = raw(ref)
            s[k] = data.decode('utf-8') if ref['path'].endswith(('.md', '.txt', '.py')) else json.loads(data)
    s['a2'] = json.loads(raw(manifest['consent']['statements']))
    s['capture'] = {}

    def walk(v):
        if isinstance(v, dict):
            if v.get('capture_file') and v.get('capture_sha256'):
                f, h = v['capture_file'], v['capture_sha256']
                data = (PROJECT / f).read_bytes()
                check(digest(data) == h, f'{f}: not the capture the A2 record names')
                if '/evidence/captures/' in f:
                    check((PROJECT / (f + '.sha256')).read_text().split()[0] == h, f'{f}: its shasum sidecar differs')
                s['capture'][f] = data.decode('utf-8')
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    for key in (KIM, MIND, DAMM, NEBULA):
        walk(s['a2']['sources'][key])
    return s


def released(manifest):
    """data-quality-update.json is the file the 2026-10-20 audit recorded, in both served copies."""
    p = manifest['published']
    data = (PROJECT / p['dataQuality']['path']).read_bytes()
    public = (PROJECT / p['dataQuality']['path'].replace('site/src/data', 'site/public/data')).read_bytes()
    old = json.loads(raw(p['dataQualityExportAudit']))
    check(digest(data) == p['dataQuality']['sha256'] == old['export_sha256'] and data == public
          and old['manifest_sha256'] == digest(raw(p['dataQualityManifest'])),
          'data-quality-update.json is not the file the 2026-10-20 release recorded')
    return digest(data)


# ---------------------------------------------------------------------------- the expected table
def expected_table(s, served):
    E = {}
    E[('placement', 'leaderboard')] = False
    E[('placement', 'core_matrix')] = False
    kim_expected(E, s)
    mind_expected(E, s, served[MIND]['contrasts'])
    damm_expected(E, s, served)
    nebula_expected(E, s, served)
    return E


def kim_expected(E, s):
    ag, gr, sc, rd, hd = s['kimAggregate'], s['kimGateReview'], s['kimSchema'], s['kimAuditReadiness'], s['kimHandoff']
    k = (KIM,)
    scope = gr['prospective_baseline']['scope']
    m = re.match(r'(\d+) participants x (\d+) within-day blocks x (\d+) targets = (\d+) trials', scope)
    check(m is not None, 'Kim: the gate review scope')
    participants, blocks_each, targets, trials = (int(x) for x in m.groups())
    check(ag['participants'] == participants and ag['trials'] == trials, 'Kim: the aggregate and the gate review differ')
    c = k + ('cohort',)
    E[c + ('participants',)] = participants
    E[c + ('blocks',)] = participants * blocks_each
    E[c + ('blocks_each',)] = sc['shape'][3]
    check(sc['shape'][3] == blocks_each, 'Kim: blocks per participant')
    E[c + ('recording_days_each',)] = 1                       # "within-day blocks"
    E[c + ('trials',)] = trials
    E[c + ('targets',)] = len(sc['stored_frequency_hz'])
    check(len(sc['stored_frequency_hz']) == targets, 'Kim: targets')
    E[c + ('trials_per_target_each',)] = trials // (participants * targets)
    E[c + ('complete_cohort',)] = ag['participants'] == participants
    # The result: the audit aggregate, checked against the handoff's prose; chance and the shifted interval recomputed.
    chance = 1 / len(sc['stored_frequency_hz'])
    check(chance == ag['prior_chance'], 'Kim: chance')
    lo, hi = ag['participant_bootstrap_95_percentile']
    says(hd, f'**{100 * ag["mean_accuracy"]:.4f}% mean participant accuracy**', 'Kim headline')
    says(hd, f'**[{100 * (lo + chance):.4f}%, {100 * (hi + chance):.4f}%]**', 'Kim accuracy interval')
    says(hd, f'**+{100 * ag["mean_difference"]:.4f} percentage points**, interval **[{100 * lo:.4f}, {100 * hi:.4f}]pp**',
         'Kim difference')
    r = k + ('result',)
    E[r + ('mean_participant_accuracy',)] = ag['mean_accuracy']
    E[r + ('equals_balanced_accuracy',)] = True
    says(hd, 'participant accuracy equals balanced accuracy for this complete balanced cohort', 'Kim balance')
    E[r + ('chance',)] = chance
    E[r + ('difference_from_chance',)] = ag['mean_difference']
    E[r + ('difference_interval_95', 0)] = lo
    E[r + ('difference_interval_95', 1)] = hi
    E[r + ('accuracy_interval_95', 0)] = lo + chance
    E[r + ('accuracy_interval_95', 1)] = hi + chance
    i = k + ('interval',)
    E[i + ('level',)] = float(number_in(s['kimProtocol']['outcome'], r'percentile(\d+)%', 'Kim level')) / 100
    E[i + ('resamples',)] = rd['bootstrap_replicates']
    E[i + ('seed',)] = rd['bootstrap_seed']
    E[i + ('descriptive',)] = 'descriptive' in hd
    E[i + ('test',)] = False
    says(' '.join(s['kimInterpretationReview']['verified_interpretation']), 'bootstrap is not a permutation-null test',
         'Kim no test')
    # The method: the gate review and the schema record (the export reads the protocol).
    pb = gr['prospective_baseline']
    me = k + ('method',)
    E[me + ('training_free',)] = 'training-free' in pb['name']
    E[me + ('tuning',)] = False
    says(' '.join(s['kimFinalApproval']['verification']), 'no outcome-based exclusions or tuning', 'Kim tuning')
    E[me + ('trials_dropped',)] = 0
    says(hd, 'No participant, channel or trial was silently dropped or repaired.', 'Kim dropped')
    E[me + ('channels',)] = len(pb['channels'])
    E[me + ('sampling_hz',)] = sc['sampling_rate_hz']
    w0, w1 = (int(x) for x in re.search(r'\[(\d+):(\d+)\)', pb['window']).groups())
    E[me + ('window_seconds',)] = int(number_in(pb['window'], r'Only (\d+) seconds primary', 'Kim window'))
    check((w1 - w0) == E[me + ('window_seconds',)] * sc['sampling_rate_hz'], 'Kim: the window samples')
    E[me + ('window_samples',)] = w1 - w0
    b0, b1 = (int(x) for x in re.search(r'Butterworth (\d+)-(\d+) Hz', pb['filter']).groups())
    E[me + ('band_hz', 0)] = b0
    E[me + ('band_hz', 1)] = b1
    E[me + ('filter_order',)] = {'second-order': 2}[re.search(r'(second-order)', pb['filter']).group(1)]
    E[me + ('harmonics',)] = len(pb['harmonics'])
    # The intake: the asset manifest and the schema record.
    am = s['kimAssetManifest']
    ik = k + ('intake',)
    E[ik + ('task_files',)] = am['file_count']
    E[ik + ('md5_checked',)] = len(am['files'])
    E[ik + ('md5_matched',)] = sum(f['supplied_md5'] == f['computed_md5'] for f in am['files'])
    E[ik + ('rest_and_questionnaire_acquired',)] = not am['rest_and_questionnaire_excluded']
    freqs = sc['stored_frequency_hz']
    check(sorted(freqs) == sorted(round(14 + j + 0.2 * i, 6) for i in range(5) for j in range(8)), 'Kim: the frequencies')
    E[ik + ('frequency_lowest_hz',)] = min(freqs)
    E[ik + ('frequency_highest_hz',)] = max(freqs)
    E[ik + ('distinct_frequencies',)] = len(set(freqs))
    E[ik + ('stored_order_ascending',)] = freqs == sorted(freqs)
    E[ik + ('moabb_list_ascending',)] = any('monotonically ascending' in f for f in s['kimSourceEvidence']['moabb_adapter']['findings'])
    E[ik + ('checks_before_any_score',)] = 'before ANY CCA score' in s['kimProtocol']['eligibility']
    hc = k + ('how_checked', 3)
    E[hc + ('fixtures',)] = rd['fixture_trials']
    E[hc + ('fixtures_matched',)] = ag['fixture_match_count']
    E[hc + ('fixture_design', 'participants')] = len(rd['fixture_participants'])
    E[hc + ('fixture_design', 'blocks')] = len(rd['fixture_block_indices'])
    E[hc + ('fixture_design', 'targets')] = len(rd['fixture_target_indices'])
    E[k + ('method_link',)] = False
    a2 = s['a2']['sources'][KIM]
    lic = a2['licence']['data']
    record = json.loads(s['capture'][lic['capture_file']])
    versions = json.loads(s['capture'][lic['latest_check']['capture_file']])
    t = k + ('rights', 'terms', 'data_licence')
    E[t + ('pinned_version',)] = record['version']
    E[t + ('versions_listed',)] = len(versions)
    E[t + ('pinned_version_is_latest',)] = record['version'] == max(v['version'] for v in versions)
    E[k + ('rights', 'terms', 'paper_cited_version', 'version')] = json.loads(
        s['capture'][lic['paper_cited_version']['capture_file']])['version']
    consent_expected(E, k, a2)


def consent_expected(E, k, a2):
    c = k + ('consent_and_ethics',)
    E[c + ('ethics_approval', 'stated')] = a2['ethics_quote'] != 'gap'
    E[c + ('informed_consent', 'stated')] = a2['consent']['stated']
    e = a2['ethics_committee_and_number']
    if e['committee'] == 'gap':
        E[c + ('ethics_approval', 'body')] = NULL
    if e['number'] == 'gap':
        E[c + ('ethics_approval', 'approval_number')] = NULL
    if a2['consent']['stated'] is False:
        for f in ('kind', 'quote', 'location'):
            E[c + ('informed_consent', f)] = NULL


def mind_expected(E, s, served_contrasts):
    ag, wc, hd, st, ac = (s['mindAggregate'], s['mindWorkflowClosure'], s['mindHandoff'], s['mindScheduleStructure'],
                          s['mindArithmeticChecks'])
    k = (MIND,)
    check(wc['primary_record_IDs'] == ag['primary_record_IDs'] and wc['secondary_record_IDs'] == ag['secondary_record_IDs']
          and wc['OOF_trials'] == ag['total_trials'] and wc['raw_EEG_preparation_completed_runs'] == ag['numerically_eligible_runs'],
          'MIND: the closure and the aggregate differ')
    runs_each = ag['primary_runs'] // ag['primary_record_IDs']
    markers = ag['primary_trials'] // ag['primary_runs']
    says(hd, f'rather than the required {markers}', 'MIND markers per run')
    cov = k + ('coverage',)
    E[cov + (0, 'count')] = wc['raw_EEG_preparation_completed_runs'] + ag['metadata_overfull_runs_excluded']
    E[cov + (0, 'record_ids')] = wc['primary_record_IDs'] + wc['secondary_record_IDs']
    E[cov + (0, 'runs_for_each_record_id')] = runs_each
    E[cov + (1, 'count')] = ag['metadata_overfull_runs_excluded']
    E[cov + (1, 'class_markers_required')] = markers
    E[cov + (2, 'count')] = wc['raw_EEG_preparation_completed_runs']
    E[cov + (2, 'trials')] = wc['OOF_trials']
    E[cov + (2, 'numeric_check_failures')] = ag['numeric_QC_failures']
    E[cov + (3, 'count')] = ag['primary_runs']
    E[cov + (3, 'record_ids')] = wc['primary_record_IDs']
    E[cov + (3, 'trials')] = ag['primary_trials']
    E[cov + (4, 'count')] = ag['secondary_runs']
    E[cov + (4, 'record_ids')] = wc['secondary_record_IDs']
    E[cov + (4, 'trials')] = ag['secondary_trials']
    says(hd, f'**88 recordings and 3,520 trials**', 'MIND coverage')
    p = k + ('primary',)
    E[p + ('record_ids',)] = wc['primary_record_IDs']
    E[p + ('runs',)] = ag['primary_runs']
    E[p + ('trials',)] = ag['primary_trials']
    E[p + ('folds_for_each_record_id',)] = runs_each
    pairs = [tuple(x) for x in s['mindProtocol']['labels_and_windows']['pairs']]
    arms = (('csp_lda', 'csp'), ('ordinal_lookup', 'order'), ('majority', 'majority'))
    cm = {(r[0], r[1], r[2]): r[4] for r in ac['CM_metric_checks']}
    for i, (a, b) in enumerate(pairs):
        key = f'{a}_{b}'
        for panel in ('primary', 'secondary'):
            m = ag['metrics'][panel][key]['mean_record_ID_balanced_accuracy']
            E[(MIND, panel, 'pairs', i, 'codes', 0)] = a
            E[(MIND, panel, 'pairs', i, 'codes', 1)] = b
            for name, src in arms:
                check(abs(cm[(panel, key, src)] - m[src]) < 1e-12, f'MIND {panel} {key}: the arithmetic review differs')
                E[(MIND, panel, 'pairs', i, name)] = m[src]
    order = [(c['pair'], c['control']) for c in served_contrasts]
    check(order == [('4/5', 'ordinal_lookup'), ('4/5', 'majority'), ('6/7', 'ordinal_lookup'), ('6/7', 'majority')],
          'MIND: the contrasts are not the four prespecified ones, ordinal first')
    review = {(c['pair'], c['control']): c for c in ac['contrasts']}
    for i, (pair, control_name) in enumerate(order):
        key, control = pair.replace('/', '_'), {'ordinal_lookup': 'order', 'majority': 'majority'}[control_name]
        c = review[(key, control)]
        m = ag['metrics']['primary'][key]
        diff = m['mean_paired_ID_differences'][control]
        lo, hi = m['descriptive_ID_resampling_percentiles'][control]
        check(abs(100 * diff - c['difference_pp']) < 1e-9 and abs(100 * lo - c['range_pp'][0]) < 1e-9
              and abs(100 * hi - c['range_pp'][1]) < 1e-9, f'MIND {key} {control}: the arithmetic review differs')
        sign = '+' if diff >= 0 else '−'
        says(hd, f'CSP − {"ordinal" if control == "order" else "majority"} | {sign}{abs(100 * diff):.2f} pp', 'MIND contrast')
        E[(MIND, 'contrasts', i, 'mean_difference')] = diff
        E[(MIND, 'contrasts', i, 'resampling_range', 0)] = lo
        E[(MIND, 'contrasts', i, 'resampling_range', 1)] = hi
        E[(MIND, 'contrasts', i, 'range_spans_zero')] = lo <= 0 <= hi
    check(len(ac['contrasts']) == 4, 'MIND: the review checks four contrasts')
    rs = k + ('resampling',)
    E[rs + ('draws',)] = int(number_in(hd, r'percentiles of ([\d,]+) paired \*\*record-ID resamples\*\*', 'MIND draws').replace(',', ''))
    E[rs + ('percentiles', 0)] = float(number_in(hd, r'Ranges are the ([\d.]+)th and ([\d.]+)th percentiles', 'MIND pct'))
    E[rs + ('percentiles', 1)] = float(number_in(hd, r'Ranges are the ([\d.]+)th and ([\d.]+)th percentiles', 'MIND pct', 2))
    E[rs + ('seed',)] = int(number_in(hd, r'one shared index table and seed (\d+)', 'MIND seed'))
    E[rs + ('shared_index_table',)] = True
    E[rs + ('confidence_interval',)] = False
    E[rs + ('test',)] = False
    says(hd, 'not population confidence intervals or confirmatory significance tests', 'MIND ranges')
    for i, (a, b) in enumerate(pairs):
        key = f'{a}_{b}'
        q = st['pairs'][key]
        sp = (MIND, 'schedule', 'pairs', i)
        E[sp + ('schedules',)] = q['unique_sequences']
        E[sp + ('trials_per_schedule',)] = q['length']
        E[sp + ('complementary',)] = q['exact_complements']
        E[sp + ('primary_ids_repeating_one_schedule',)] = q['primary_all_three_same']
        E[sp + ('primary_ids_mixing_schedules',)] = q['primary_mixed']
    says(hd, 'six use the same schedule in all three runs for pair 4/5, and five do so for pair 6/7', 'MIND schedules')
    sc = k + ('secondary',)
    E[sc + ('record_ids',)] = wc['secondary_record_IDs']
    E[sc + ('runs',)] = ag['secondary_runs']
    E[sc + ('trials',)] = ag['secondary_trials']
    E[sc + ('interval',)] = NULL
    check(not any(ag['metrics']['secondary'][f'{a}_{b}']['bootstrap_performed'] for a, b in pairs), 'MIND: a secondary interval')
    E[sc + ('pooled_with_primary',)] = not ag['primary_and_secondary_not_pooled']
    pr = k + ('processing',)
    E[pr + ('channels',)] = len(s['mindProtocol']['channels_and_decode']['order'])
    says(hd, '64 channels in one consistent order, 1,000 Hz sampling', 'MIND channels')
    E[pr + ('sampling_hz',)] = int(number_in(hd, r'64 channels in one consistent order, ([\d,]+) Hz sampling', 'MIND fs').replace(',', ''))
    E[pr + ('auxiliary_channels_used',)] = False
    says(hd, 'auxiliary HEO/VEO/EKG/EMG/Trigger channels were not added', 'MIND auxiliary')
    E[pr + ('band_hz', 0)] = int(number_in(hd, r'fixed MNE (\d+)–(\d+) Hz FIR filter', 'MIND band'))
    E[pr + ('band_hz', 1)] = int(number_in(hd, r'fixed MNE (\d+)–(\d+) Hz FIR filter', 'MIND band', 2))
    E[pr + ('resampled_hz',)] = int(number_in(hd, r'polyphase resampled to (\d+) Hz', 'MIND resampled'))
    E[pr + ('window_after_marker_seconds', 0)] = int(number_in(hd, r'\*\*\[(\d+),(\d+)\) seconds after each stored class marker\*\*', 'MIND window'))
    E[pr + ('window_after_marker_seconds', 1)] = int(number_in(hd, r'\*\*\[(\d+),(\d+)\) seconds after each stored class marker\*\*', 'MIND window', 2))
    E[pr + ('window_samples',)] = int(number_in(hd, r'yielding ([\d,]+) samples', 'MIND samples').replace(',', ''))
    E[pr + ('csp_components',)] = {'four': 4}[number_in(hd, r'Every fold fitted (\w+)-component CSP', 'MIND CSP')]
    E[pr + ('fitted_on_training_runs_only',)] = True
    says(hd, 'shrinkage LDA on training runs only', 'MIND training runs')
    E[pr + ('search',)] = False
    says(hd, 'There was no parameter, window, component, or cohort search using scores.', 'MIND search')
    ipc = ag['independent_prediction_comparison']
    E[k + ('how_checked', 0, 'trials')] = ipc['rows']
    E[k + ('how_checked', 1, 'max_decision_difference')] = ipc['max_abs_error']
    E[k + ('dataset_page',)] = False
    tm = k + ('rights', 'terms')
    for i, read in enumerate((False, False, False, True)):
        E[tm + ('statements', i, 'read_in_this_release')] = read
    E[tm + ('terms_of_use_page_read',)] = False
    E[tm + ('aggregate_only',)] = True
    E[tm + ('redistributed',)] = s['mindProtocol']['scientific_limits_remain']['raw_redistribution'] != 'NOT_AUTHORIZED'
    E[tm + ('publisher_checksum_verified',)] = s['mindProtocol']['source']['publisher_checksum_verified']
    a2 = s['a2']['sources'][MIND]
    consent_expected(E, k, a2)
    if a2['ethics_consent_source']['captured_at'] is None:
        E[k + ('consent_and_ethics', 'read_at')] = NULL


def damm_expected(E, s, served):
    au, qc, adj, er, pr = (s['dammAudit'], s['dammIntakeQc']['scientific_schema_findings'], s['dammScopeAdjudication'],
                           s['dammExecutionReview'], s['dammProtocol'])
    k = (DAMM,)
    a2 = s['a2']['sources'][DAMM]
    readme = s['capture'][a2['licence']['readme']['capture_file']]
    d = k + ('design',)
    check('sub-01 random runs only' in au['scope'], 'Damm: the audit scope')
    E[d + ('participants_run',)] = 1
    E[d + ('published_participants',)] = int(number_in(readme, r'## Participants - (\d+) participants', 'Damm README'))
    E[d + ('runs_used',)] = len(pr['directions'])
    E[d + ('classes',)] = len(pr['labels'])
    E[d + ('delivered_cues',)] = au['trials']
    E[d + ('trials_per_held_out_run',)] = au['trials'] // len(pr['directions'])
    E[d + ('trials_per_class_per_run',)] = au['trials'] // len(pr['directions']) // len(pr['labels'])
    E[d + ('directions',)] = len(pr['directions'])
    f = k + ('files',)
    E[f + ('edf_channels',)] = qc['edf_channels_all']
    E[f + ('scalp_channels',)] = au['channels']
    fs = int(number_in(readme, r'Sampling frequency:\*\* (\d+) Hz', 'Damm README fs'))
    E[f + ('sampling_hz',)] = fs
    E[f + ('run_seconds',)] = qc['duration_s_all']
    E[f + ('samples_per_run',)] = au['calibration']['1']['shape'][1]
    E[f + ('state_blocks_per_run',)] = int(number_in(' '.join(er['independently_verified']), r'contiguous stream,(\d+) blocks', 'Damm blocks'))
    ev = adj['timing_basis']['evidence']
    white = int(number_in(ev, r'white/fixation(\d+) samples each', 'Damm white'))
    finger = int(number_in(ev, r'finger(\d+);', 'Damm finger'))
    check(white % fs == 0 and finger % fs == 0, 'Damm: the durations')
    E[f + ('white_seconds',)] = white // fs
    E[f + ('fixation_seconds',)] = white // fs
    E[f + ('cue_seconds',)] = finger // fs
    E[f + ('sample_column_present',)] = qc['actual_sample_column_present']
    E[f + ('cue_samples_reconstructed',)] = 'reconstruct' in s['dammHandoff']
    E[f + ('edf_scaling_applied_once',)] = 'physical scaling once' in ' '.join(er['independently_verified'])
    variants = served[DAMM]['variants']
    check([v['id'] for v in variants] == pr['variants'], 'Damm: the variants are not the protocol’s, in its order')
    for i, v in enumerate(pr['variants']):
        vv = (DAMM, 'variants', i)
        signal = not v.startswith('order_')
        E[vv + ('signal_input',)] = signal
        if signal:
            E[vv + ('channels',)] = len(pr['central_channels']) if 'central' in v else au['channels']
            window = 'sensitivity' if v.startswith('sensitivity') else 'precue' if v.startswith('precue') else 'primary'
            E[vv + ('window_seconds', 0)] = pr['windows_s'][window][0]
            E[vv + ('window_seconds', 1)] = pr['windows_s'][window][1]
        else:
            E[vv + ('channels',)] = NULL
            E[vv + ('window_seconds',)] = NULL
    E[k + ('variant_directions_audited',)] = au['variant_directions']
    fl = k + ('flags',)
    says(s['dammHandoff'], 'All variants and both directions were frozen before scoring.', 'Damm frozen')
    E[fl + ('variants_fixed_before_scoring',)] = True
    says(s['dammHandoff'], 'No best variant was selected and no controls were discarded.', 'Damm retained')
    E[fl + ('all_variants_retained',)] = True
    E[fl + ('independent_audit_passed',)] = au['status'].startswith('PASS')
    E[fl + ('score_published',)] = False
    E[fl + ('sequential_runs_evaluated',)] = False
    E[fl + ('physical_trigger_timing_validated',)] = False
    E[fl + ('additional_participant_acquired',)] = False
    says(s['dammHandoff'], 'No additional participant was acquired or selected using outcomes.', 'Damm one participant')
    E[k + ('rights', 'licenseUrl')] = NULL
    E[k + ('rights', 'terms', 'license_file_present')] = a2['licence']['license_file']['present']
    consent_expected(E, k, a2)


def nebula_expected(E, s, served):
    au, ad, md, eh, ph = (s['nebulaEegAudit'], s['nebulaEmgAdmission'], s['nebulaEmgMetadata'], s['nebulaEegHandoff'],
                          s['nebulaEmgPilotHandoff'])
    k = (NEBULA,)
    a2 = s['a2']['sources'][NEBULA]
    record = json.loads(s['capture'][a2['licence']['data']['capture_file']])
    rc = s['nebulaEmgReceipt']['conditions']
    d = k + ('design',)
    check(au['scope'].startswith('one participant'), 'NeBULA: the audit scope')
    E[d + ('participants_run',)] = 1
    # The counts as each source states them: the paper (the export reads the record's description), the research
    # intake's file manifest (the export reads A2's capture of the record) and MOABB's catalogue.
    pc = d + ('participant_counts',)
    paper = visible(s['capture'][a2['capture_file']])
    E[pc + ('paper_and_record_description',)] = int(number_in(paper, r'We enlisted (\d+) healthy participants', 'NeBULA paper'))
    check(f'collected from {E[pc + ("paper_and_record_description",)]} healthy participants' in visible(record['description']),
          'NeBULA: the record description states another count')
    intake = json.loads(s['nebulaFileManifest'])
    check(intake['doi'] == '10.6084/m9.figshare.27301629.v1', 'NeBULA: the research file manifest is another record')
    E[pc + ('participant_archives_in_record',)] = sum(1 for f in intake['files'] if re.fullmatch(r'sub-\d+\.zip', f['name']))
    moabb = [e for e in s['moabbCatalog']['entries'] if e['Dataset'] == 'NeBULA2025']
    check(len(moabb) == 1, 'NeBULA: the MOABB catalogue row')
    E[pc + ('moabb_catalog',)] = int(moabb[0]['#Subj'])
    E[d + ('targets',)] = len(rc['free']['events']['targets'])
    E[d + ('trials',)] = au['trials']
    for c in CONDITIONS:
        E[d + ('trials_by_condition', c)] = rc[c]['events']['quartets']
    says(eh, 'All complete delivered StartTrial/Go/Reach/EndTrial quartets are retained: 29 free, 30 low and 30 high.',
         'NeBULA trials')
    E[d + ('missing_trial_fabricated',)] = False
    E[d + ('folds',)] = len(CONDITIONS)
    eeg = k + ('eeg',)
    E[eeg + ('channels',)] = au['channels']
    E[eeg + ('sampling_hz',)] = int(number_in(eh, r'IEEE float32 at ([\d,]+) Hz', 'NeBULA fs').replace(',', ''))
    says(eh, 'The primary half-open epoch is `[Go, Go + 2 seconds)`', 'NeBULA window')
    says(eh, 'The precue control uses `[Go − 0.5 seconds, Go)`', 'NeBULA precue')
    E[eeg + ('window_ms', 0)] = 0
    E[eeg + ('window_ms', 1)] = 2 * 1000
    E[eeg + ('precue_window_ms', 0)] = -500
    E[eeg + ('precue_window_ms', 1)] = 0
    E[eeg + ('band_hz', 0)] = int(number_in(eh, r'fourth-order Butterworth SOS (\d+)–(\d+) Hz', 'NeBULA band'))
    E[eeg + ('band_hz', 1)] = int(number_in(eh, r'fourth-order Butterworth SOS (\d+)–(\d+) Hz', 'NeBULA band', 2))
    emg = k + ('emg',)
    E[emg + ('rows',)] = int(number_in(ad['admitted']['layout'], r'^(\d+) rows', 'NeBULA rows'))
    E[emg + ('sampling_hz',)] = {v['SamplingFrequency'] for v in md['emg'].values()}.pop()
    w = re.search(r'samples \[(\d+),(\d+)\) after Go, with precue \[(-?\d+),(\d+)\)', squash(ph))
    check(w is not None, 'NeBULA: the EMG windows')
    E[emg + ('window_ms', 0)] = int(w.group(1))
    E[emg + ('window_ms', 1)] = int(w.group(2))
    E[emg + ('precue_window_ms', 0)] = int(w.group(3))
    E[emg + ('precue_window_ms', 1)] = int(w.group(4))
    E[emg + ('band_hz', 0)] = int(number_in(ph, r'Butterworth SOS, (\d+)–(\d+) Hz', 'NeBULA EMG band'))
    E[emg + ('band_hz', 1)] = int(number_in(ph, r'Butterworth SOS, (\d+)–(\d+) Hz', 'NeBULA EMG band', 2))
    arms = served[NEBULA]['arms']
    check([a['id'] for a in arms['eeg']] == ['primary', 'precue', 'central', 'order', 'shuffle']
          and set(au['scores']) == {'primary', 'precue', 'central', 'order', 'shuffle'}, 'NeBULA: the EEG arms')
    for i, a in enumerate(arms['eeg']):
        E[(NEBULA, 'arms', 'eeg', i, 'signal_input')] = a['id'] != 'order'
    pa = s['nebulaEmgPilotAggregate']
    fold_arms = {('emg_' + a if a == 'precue' else a) for a in pa['descriptive_scores']['folds'][0]['arms']}
    check([a['id'] for a in arms['emg_and_fusion']] == ['emg', 'fusion', 'emg_precue', 'emg_shuffle', 'fusion_shuffle']
          and fold_arms == {a['id'] for a in arms['emg_and_fusion']}, 'NeBULA: the EMG arms are not the audited ones')
    for i, _ in enumerate(arms['emg_and_fusion']):
        E[(NEBULA, 'arms', 'emg_and_fusion', i, 'signal_input')] = True
    E[k + ('arms', 'eeg_fits')] = au['heldout_fits']
    check(pa['independent_audit']['checks']['all_15_fixed_lda_models'] is True, 'NeBULA: the EMG fits')
    E[k + ('arms', 'emg_and_fusion_fits')] = int(number_in(ph, r'produced \*\*(\d+) new fits\*\*', 'NeBULA EMG fits'))
    E[k + ('arms', 'pretrained_model')] = False
    E[k + ('arms', 'eeg_features_recomputed_for_fusion')] = pa['independent_audit']['raw_eeg_recomputed']
    E[k + ('arms', 'independently_audited')] = pa['independent_audit']['status'] == 'PASS' and au['status'].startswith('PASS')
    ff = k + ('file_facts',)
    ties = ad['admitted']['boundary_ties']
    E[ff + ('boundary_ties',)] = sum(ties.values())
    for c in CONDITIONS:
        E[ff + ('boundary_ties_by_condition', c)] = ties[c]
    says(eh, f'Original markers contain {sum(ties.values())} exact EndTrial/next StartTrial boundary ties', 'NeBULA ties')
    E[ff + ('backward_overlaps',)] = sum(s['nebulaBoundaryAdjudication']['evidence']['negative'])
    E[ff + ('first_parse_stopped_before_features',)] = True
    says(eh, 'The first attempt stopped before QA completion, features, models or scores', 'NeBULA first attempt')
    E[ff + ('parser_fix_reviewed',)] = s['nebulaBoundaryAdjudication']['decision'].startswith('PASS')
    E[ff + ('rerun_within_original_budget',)] = s['nebulaEegReleaseApproval']['budget_reset'] is False
    E[ff + ('emg_channel_rows',)] = md['channels_tsv']['rows']
    E[ff + ('emg_channels_in_metadata',)] = {v['EMGChannelCount'] for v in md['emg'].values()}.pop()
    E[ff + ('emg_rows_relabelled',)] = False
    E[ff + ('stored_markers',)] = int(number_in(ad['admitted']['events'], r'^(\d+) rows', 'NeBULA markers'))
    E[ff + ('complete_quartets',)] = int(number_in(ad['admitted']['events'], r'rows,(\d+) complete quartets', 'NeBULA quartets'))
    E[ff + ('markers_match_eeg_files',)] = 'exact common EEG-marker labels/order/sample positions' in ad['admitted']['events']
    eeg_len = {re.search(r'task-(\w+?)_eeg', r['marker']).group(1): r['n_samples_from_ZIP_size_only']
               for r in s['nebulaBoundaryAggregate']['runs']}
    E[ff + ('emg_eeg_sample_lengths_equal',)] = all(rc[c]['structure']['columns'] == eeg_len[c] for c in CONDITIONS)
    fl = k + ('flags',)
    for f in ('score_published', 'order_diagnostic_comparison_published', 'additional_participant_acquired',
              'physical_synchronisation_verified', 'amplitude_calibration_verified'):
        E[fl + (f,)] = False
    check(s['nebulaEmgIntakeReleaseApproval']['physical_calibration_or_sync_verified'] is False, 'NeBULA: calibration')
    lic = a2['licence']['data']
    versions = json.loads(s['capture'][lic['latest_check']['capture_file']])
    t = k + ('rights', 'terms')
    E[t + ('data_licence', 'pinned_version')] = record['version']
    E[t + ('data_licence', 'versions_listed')] = len(versions)
    E[t + ('data_licence', 'pinned_version_is_latest')] = record['version'] == max(v['version'] for v in versions)
    E[t + ('zenodo_13627307', 'registered_public_record')] = a2['licence']['zenodo_13627307']['resolves']
    E[t + ('zenodo_13627307', 'terms')] = NULL
    consent_expected(E, k, a2)


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest):
    check(served['release_id'] == manifest['release_id'] == 'dataset-checks-update-20261028', 'another release')
    check(served['generated_at'] == manifest['release_date'], 'another release date')
    check(served['schema_version'] == 'bci-report-dataset-checks-update-v1', 'another schema')
    check([c['id'] for c in served['cases']] == [KIM, MIND, DAMM, NEBULA]
          and [c['status'] for c in served['cases']] == ['released', 'released_conditional', 'score_held', 'score_held'],
          'other cases')
    check(served['placement']['sections'] == [KIM, MIND, DAMM, NEBULA]
          and served['placement']['page_order'] == ['shin2022', KIM, MIND, 'eldbeta', DAMM, NEBULA, 'zuco2'],
          'another section order')
    check(served['one_person']['cases'] == ['eldbeta', DAMM, NEBULA], 'the one-person lead covers other cases')
    sentence = served['one_person']['sentence']
    body = json.dumps(served, ensure_ascii=False)
    check(body.count('With one person every score') == 1 and len(re.findall(r'(?i)that person|this person', body)) == 1
          and re.search(r'(?i)would be (?:that|this|one|the) (?:person|participant)', body) is None,
          'the one-person sentence is not stated once')
    # Kim's sealing: stated once, with the limit the execution approval and the handoff give.
    says(' '.join(s['kimFinalApproval']['reporting_limits']), 'temporal/process separation, not independent label blindness',
         'Kim sealing limit')
    says(s['kimHandoff'], 'the class axis is structurally known', 'Kim sealing limit')
    sealing = [h['text'] for h in served[KIM]['how_checked'] if h['id'] == 'sealed-before-scoring']
    check(len(sealing) == 1 and 'process separation, not blinded labels, because the stored class order is known'
          in sealing[0] and body.count('process separation') == 1, 'Kim: the sealing limit is not stated once')
    check(served[KIM]['aliases'] == ['Kim2025BetaRange', 'Figshare 28806815', 'doi:10.1038/s41597-025-06032-2']
          and served[KIM]['dataset_page'] == '/datasets/kim2025-beta-range/', 'Kim: the aliases or the dataset page')
    check(served[KIM]['hold']['id'] == 'kim-amplitude-dependent-models' and served[DAMM]['held']['id']
          == 'damm-one-participant-score' and served[NEBULA]['held']['id'] == 'nebula-one-participant-scores', 'the hold ids')
    # Consent, ethics and terms are the A2 record's, and each quotation is in its capture.
    for case in (KIM, DAMM, NEBULA, MIND):
        src = s['a2']['sources'][case]
        ce = served[case]['consent_and_ethics']
        q = lambda v: None if v == 'gap' else v
        check(ce['ethics_approval']['quote'] == q(src['ethics_quote']) and ce['informed_consent']['quote']
              == q(src['consent_quote']) and ce['ethics_approval']['body'] == q(src['ethics_committee_and_number']['committee'])
              and ce['ethics_approval']['approval_number'] == q(src['ethics_committee_and_number']['number'])
              and ce['informed_consent'].get('kind') == src['consent'].get('kind')
              and ce['gaps'] == [g for g in src['gaps'] if g['field'].startswith(('consent', 'ethics'))],
              f'{case}: the consent and ethics block is not the A2 record’s')
        if case == MIND:
            ecs = src['ethics_consent_source']
            receipt = (PROJECT / ecs['capture_file']).read_bytes()
            check(digest(receipt) == ecs['capture_sha256'] == ce['capture_sha256'] and ce['read_from'] == ecs['read_from'],
                  'MIND: the consent source')
            text = receipt.decode('utf-8')
            for quote in (src['ethics_quote'], src['consent_quote'], src['licence']['paper']['quote']):
                check(squash(quote) in squash(text), 'MIND: a quotation is not in the intake receipt')
            check(ce['informed_consent']['location'] == re.sub(r'(\d)v\d+\b', r'\1', src['consent']['location']),
                  'MIND: the consent location')
        else:
            check(ce['read_from'] == src['read_from'] and ce['capture_sha256'] == src['capture_sha256']
                  and ce['read_at'] == src['captured_at'] and ce['informed_consent']['location'] == src['consent'].get('location'),
                  f'{case}: the consent source')
            page = s['capture'][src['capture_file']]
            for quote in (q(src['ethics_quote']), q(src['consent_quote'])):
                if quote:
                    check(squash(quote) in squash(page) or squash(quote) in visible(page),
                          f'{case}: a quotation is not in its capture: {quote[:40]!r}')
    # Attribution and licences, against the captured records.
    kr = served[KIM]['rights']
    rec = json.loads(s['capture'][s['a2']['sources'][KIM]['licence']['data']['capture_file']])
    attribution_check(KIM, kr, rec['doi'], [a['full_name'] for a in rec['authors']] + ['Kyungho Won', 'Sung Chan Jun'],
                      rec['title'])
    check(kr['license'] == rec['license']['name'] and kr['licenseUrl'] == rec['license']['url'], 'Kim: the licence')
    nr = served[NEBULA]['rights']
    rec = json.loads(s['capture'][s['a2']['sources'][NEBULA]['licence']['data']['capture_file']])
    attribution_check(NEBULA, nr, rec['doi'], [a['full_name'] for a in rec['authors']], rec['title'])
    check(nr['license'] == 'CC BY 4.0' and rec['license']['name'] == 'CC BY'
          and nr['licenseUrl'] == rec['license']['url'], 'NeBULA: the licence')
    dd = json.loads(s['capture'][s['a2']['sources'][DAMM]['licence']['data']['capture_file']])
    dr = served[DAMM]['rights']
    names = [f'{n.split(", ")[1]} {n.split(", ")[0]}' for n in dd['Authors']]
    attribution_check(DAMM, dr, dd['DatasetDOI'].removeprefix('doi:'), names, dd['Name'].strip())
    check(dr['license'] == dd['License'] == 'CC0', 'Damm: the licence')
    mr = served[MIND]['rights']
    mrec = s['a2']['sources'][MIND]['licence']['sciencedb_record']
    page = s['capture'][mrec['capture_file']]
    check(squash(mrec['quote']) in squash(page), 'MIND: the record licence quote is not in its capture')
    ld = next(json.loads(m.group(1)) for m in re.finditer(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', page, re.S)
              if '"identifier":"https://doi.org/10.57760/sciencedb.34326"' in m.group(1).replace(' ', ''))
    attribution_check(MIND, mr, '10.57760/sciencedb.34326', [c['name'] for c in ld['creator']],
                      ld['name'].replace('：', ': '))
    st = {t['source']: t['value'] for t in mr['terms']['statements']}
    check(st == {'paper': 'CC BY 4.0', 'archive dataset description': 'CC BY 4.0', 'MOABB adapter': 'CC BY-NC 4.0',
                 'ScienceDB record page': 'CC BY-NC 4.0'} and ld['license'] == 'https://creativecommons.org/licenses/by-nc/4.0/',
          'MIND: the four licence statements')
    says(s['mindAdapter'], 'license="CC-BY-NC-4.0"', 'MIND adapter licence')
    check(served[MIND]['secondary'].keys() == {'record_ids', 'runs', 'trials', 'design', 'interval', 'pooled_with_primary',
                                               'pairs', 'text'}, 'MIND: the secondary panel carries other fields')
    check(served['not_published'] == manifest['notPublished'], 'the not-published list is not the manifest’s')
    check(served['holds'] == manifest['holds'], 'the holds are not the manifest’s')
    pv, src = served['provenance'], manifest['sources']
    check(pv['source_export_sha256'] == {KIM: src['kimAggregate']['sha256'], MIND: src['mindAggregate']['sha256']}
          and pv['release_approval_sha256'][KIM] == src['kimReleaseApproval']['sha256']
          and pv['release_approval_sha256'][MIND] == src['mindInterpretationReview']['sha256']
          and pv['release_approval_sha256'][DAMM] == src['dammReleaseApproval']['sha256']
          and pv['evidence_sha256']['consent_statements'] == manifest['consent']['statements']['sha256']
          and pv['source_export_sha256'][KIM].startswith('b3043fb0') and pv['source_export_sha256'][MIND].startswith('ff43f57f'),
          'the provenance names other files')
    check(s['kimReleaseApproval']['independent_audit_sha256'] == src['kimAggregate']['sha256']
          and s['mindInterpretationReview']['aggregate_sha256'] == src['mindAggregate']['sha256']
          and s['mindInterpretationReview']['decision'] == 'APPROVED_INTERNAL_CONDITIONAL_HANDOFF',
          'a release record binds another aggregate')
    return sentence


def attribution_check(case, r, doi, creators, title):
    check(r['attribution'].endswith(ENDING) and doi in r['attribution'] and title in r['attribution']
          and all(c in r['attribution'] for c in creators), f'{case}: the attribution does not name the record')


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


def all_leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from all_leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from all_leaves(v, trail + (i,))
    else:
        yield trail, value


def private_names(s):
    blob = s['kimHandoff'] + s['mindHandoff'] + s['dammHandoff'] + s['nebulaEegHandoff'] + s['nebulaEmgIntakeHandoff']
    blob += json.dumps(s['mindProtocol']) + json.dumps(s['nebulaEmgIntakeInterpretationReview'])
    names = {x for pair in re.findall(r'/(?:home|Users|Volumes|mnt)/([^/\s`"]+)/([^/\s`"]+)', blob) for x in pair}
    hosts = set(re.findall(r'\b(?:on|or) ([A-Z][A-Za-z]{1,8}\d+)\b', blob)) | set(re.findall(r'\b([A-Z]{3,6}\d*) under\b', blob))
    hosts |= set(re.findall(r'site/([A-Z][a-z]{2,8}\d+)/', blob))
    names |= hosts | {re.sub(r'\d+$', '', h) for h in hosts if re.fullmatch(r'[A-Z]+\d*', h)}
    return {n for n in names if len(n) >= 3}


def held(s):
    """Every Damm and NeBULA score the withheld records hold."""
    fl = set()
    for v in s['dammAudit']['scores'].values():
        fl |= {v['accuracy'], v['balanced_accuracy']}
    for arm in s['nebulaEegAudit']['scores'].values():
        fl.add(arm['descriptive_macro_balanced_accuracy'])
        fl |= {x for f in arm['folds'] for x in (f['accuracy'], f['balanced_accuracy'])}

    def floats(v):
        if isinstance(v, dict):
            for x in v.values():
                yield from floats(x)
        elif isinstance(v, list):
            for x in v:
                yield from floats(x)
        elif isinstance(v, float):
            yield v
    fl |= set(floats(s['nebulaEmgPilotAggregate']['descriptive_scores']))
    return fl - {0.0, 0.5, 1.0, 0.2}


def withheld(s):
    """Values the sources hold that the release does not publish, as floats and as distinctive counts."""
    ag = s['mindAggregate']
    means = {v for p in ag['metrics'].values() for m in p.values() for v in m['mean_record_ID_balanced_accuracy'].values()}
    fl = {x for p in ag['metrics'].values() for m in p.values() for a in m['pooled_metrics'].values()
          for x in (a['accuracy'], a['balanced_accuracy'], a['macro_F1'])} - means
    fl |= set(ag['metrics']['secondary']['4_5']['mean_paired_ID_differences'].values())
    fl |= {ag['resource_accounting']['elapsed_seconds'], ag['resource_accounting']['charged_CPU_seconds']}
    ka = s['kimAggregate']
    fl |= {ka['elapsed_seconds'], ka['execution_receipt']['wall_seconds'], ka['execution_receipt']['CPU_seconds']}
    fl |= held(s)
    md = s['mindProtocol']['actual_metadata']
    it = set(md['two_noncanonical_run_event_counts']) | {md['cue3_count'], md['unmatched_class_cues']}
    it |= set(s['mindWorkflowClosure']['true_data_model_fit_calls'].values())
    it |= {ag['counts']['prepare']['EEG_bytes_extracted'], s['kimAssetManifest']['total_bytes'], s['kimSchema']['sample_count']}
    return fl - {0.0, 0.5, 1.0, 0.95, 0.025, 0.2}, it


def text_checks(served_text, served, s):
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root|opt)/', served_text) is None, 'a private path')
    private = private_names(s)
    check(len(private) >= 4, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', served_text, re.I) is None,
              'a private host or storage name reached the served file')
    for pattern, why in ((r'BI2013a|Brain Invaders', 'register-only BI2013a'),
                         (r'ICLR|OpenReview|submission|iMINDBench|NEAR-Bench', 'a submission reference'),
                         (r'(?<![\d.])55(?:\.0+)?\s*%|fifty[- ]five', 'the commenter’s figure'),
                         (r'\bsub-\d|\bsubj\d|task-(?:free|low|high|random)|\.vmrk|\.edf\b|\.csv\b', 'a file or participant id'),
                         (r'\b(?:21|26) both|both-correct|EMG-only-correct|fusion-only-correct', 'a paired count'),
                         (r'(?i)\bjev\b', 'Jev'), (r'\bV4\b|MIND V4', 'a version label')):
        check(re.search(pattern, served_text) is None, f'{why} reached the served file')
    for case in (DAMM, NEBULA):
        for trail, v in all_leaves(served[case]):
            check(not isinstance(v, float), f'{case}/{trail}: a fraction in a one-person case')
            check(not any(isinstance(t, str) and re.search(r'accuracy|correct|chance|macro|balanced|interval|paired', t)
                          for t in trail), f'{case}/{trail}: a held-score field')
            if isinstance(v, str) and trail[-1] not in ('attribution', 'source', 'read_from', 'capture_sha256',
                                                        'pinned_commit', 'pinned_snapshot') and trail[-2:-1] != ('reviewBasis',):
                check('%' not in v and re.search(r'(?<![\w.])\d+\.\d{2}(?!\w|\.\d)|(?<![\w.])0\.\d+', v) is None,
                      f'{case}/{trail}: a score-like figure in a one-person case')
        # No comparison of a held score, with or without a number: in the case, its hold line and its record line.
        texts = [v for _, v in all_leaves(served[case]) if isinstance(v, str)]
        texts += [h['reason'] for h in served['holds'] if h['case'] == case] + [served['release_record'][case]]
        for v in texts:
            m = re.search(r'(?i)\b(?:higher|lower|exceed\w*|above|below|compared?|comparison|better|worse|versus|vs\.?'
                          r'|outperform\w*|beats?|surpass\w*|than|at chance)\b', v)
            check(m is None, f'{case}: a comparison word ({m and m.group(0)!r}) in a one-person case')
    for v in sorted(held(s)):
        check(f'{100 * v:.2f}' not in served_text, f'a held score reached the served file as text ({100 * v:.2f})')


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    s = sources(manifest)
    dq = released(manifest)
    check(served['provenance']['released_file_sha256'] == {'data-quality-update.json': dq}, 'the released-file hash')
    E = expected_table(s, served)
    string_checks(s, served, manifest)

    found = dict(leaves(served))
    copied_keys = {'mean_participant_accuracy', 'difference_from_chance', 'difference_interval_95', 'csp_lda',
                   'ordinal_lookup', 'majority', 'mean_difference', 'resampling_range', 'max_decision_difference'}
    exact = recomputed = nulls = flags = 0
    for path, value in found.items():
        label = '/'.join(map(str, path))
        check(path in E, f'{label}: a figure with no audit rule')
        want = E[path]
        if want is NULL:
            check(value is None, f'{label}: a null became {value!r}')
            nulls += 1
            continue
        check(same_value(value, want), f'{label}: {value!r} where the sources give {want!r}')
        if isinstance(value, bool):
            flags += 1
        elif any(k in copied_keys for k in path if isinstance(k, str)):
            exact += 1
        else:
            recomputed += 1
    missing = [p for p in E if p not in found]
    check(not missing, f'expected figures missing from the served file: {missing[:3]}')

    fl, it = withheld(s)
    pub_f = {v for v in found.values() if isinstance(v, float)}
    pub_i = {v for v in found.values() if isinstance(v, int) and not isinstance(v, bool)}
    check(not (fl & pub_f), f'a withheld value reached the served file: {sorted(fl & pub_f)[:3]}')
    check(not (it & pub_i), f'a withheld count reached the served file: {sorted(it & pub_i)[:3]}')
    text_checks(served_bytes[0].decode(), served, s)

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_dataset_checks_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins, and takes Kim’s design from the gate '
                         'review’s scope and its bootstrap settings from the audit readiness record (the export reads '
                         'the aggregate and the protocol), MIND’s counts from the workflow closure and its processing '
                         'facts and resampling settings from the handoff’s prose (the export reads the frozen protocol), '
                         'Damm’s counts from the independent audit, the README capture and the execution review, '
                         'NeBULA’s from the EEG audit, the EMG structure admission, the EMG metadata and the handoffs '
                         '(the export reads the boundary diagnostics, the protocols and the structure receipt) and its '
                         'participant counts from the paper, the research file manifest and MOABB’s catalogue (the '
                         'export reads the record’s description and the A2 capture of its files), and every derived '
                         'figure from its own arithmetic on those.'),
        'cases': [c['id'] for c in served['cases']],
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'flags': flags,
        'nulls_kept': nulls,
        'withheld_values_checked_absent': len(fl) + len(it),
        'released_file_unchanged': {'data-quality-update.json': dq},
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every pinned input is the file the manifest names, and every A2 capture has the SHA-256 the record and its '
            'shasum sidecar give',
            'data-quality-update.json keeps the bytes the 2026-10-20 export audit recorded, in both served copies',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'Kim’s figures are the audit aggregate’s, its accuracy interval the difference interval plus chance, and '
            'its headline figures the handoff’s prose at four decimals',
            'MIND’s panels and contrasts are the aggregate’s and agree with the arithmetic review; the secondary panel '
            'carries no interval and no schedule field',
            'no Damm or NeBULA case holds a fraction, a percentage, a held-score field or a held value as text, and '
            'no comparison word in its text, hold line or record line',
            'consent, ethics and terms are the A2 record’s, and every quotation is found verbatim in its capture',
            'the one-person sentence is stated once, and no hold reason restates it',
            'Kim’s sealing is stated once, with the limit the execution approval and the handoff give',
            'no withheld pooled metric, accounting figure, private host, storage name, path, file or participant '
            'identifier, register-only content or submission reference is in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'research aggregates, release approvals, reviews, protocols and handoffs: pinned in the manifest, '
                'with the aggregates, approvals and protocols named in the served provenance',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
                'consent and ethics: the A2 record, pinned in the manifest, and its captures, pinned by the record',
            ],
            'not_bound': [
                'sealed predictions and private score files are verified by the research audits, whose records are '
                'pinned; this audit does not open them',
                'prose, the arm and variant names, the caveats, the holds and the release record are checked by the '
                'export; this audit checks only the one-person sentence, Kim’s sealing limit and the comparison words '
                'of the one-person cases',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
