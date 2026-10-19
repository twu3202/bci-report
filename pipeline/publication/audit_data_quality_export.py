"""Independent audit of data-quality-update.json: every figure in the served file against the pinned sources.

A separate program from export_data_quality_update.py. It shares no code with that export and imports nothing from
it: it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what
every number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- figures are read from where the export does not read them, wherever a second record states them: Shin2022's arms
  from the release audit's independent reconstruction (the export reads the research export; both must agree), the
  run chain from the label audit's integrity block and the duplicate review's prose, the window chain from the frozen
  protocol and the census review, the catalog and header cap from the duplicate review, eldBETA's counts from its
  release audit and raw QC aggregate and its cohort size from the MOABB catalog row, the decision difference from the
  release review's prose; derived figures (the flat-on-some-channels count, the windows outside the analysed ones,
  the percentages, the interval level, the window length in seconds) are recomputed here;
- the consent, ethics and terms strings are the A3 record's, and every quotation is found verbatim in the capture the
  record names, whose SHA-256 is checked; each attribution names the record's creators and DOI and ends with the
  site's sentence;
- the two served copies are one, the served file names the manifest it was built from, and no withheld value, held
  eldBETA score, ZuCo 2.0 run value, register-only figure, private host, storage name or path is in it.

    python3 pipeline/publication/audit_data_quality_export.py
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'data-quality-release-manifest.json'
AUDIT = REVIEW / 'data-quality-export-audit.json'
SERVED = (PROJECT / 'site/src/data/data-quality-update.json', PROJECT / 'site/public/data/data-quality-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
ENDING = 'Derived analysis by BCI Report; not endorsed by the authors.'


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


def visible(text):
    """A capture's text as A3 quoted it: tags removed, entities decoded, whitespace collapsed."""
    return squash(html.unescape(re.sub(r'<[^>]+>', ' ', text)))


def says(text, phrase, label):
    check(squash(phrase) in squash(text), f'{label}: the pinned record does not say {phrase!r}')


def same_value(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {}
    for k, ref in manifest['sources'].items():
        data = raw(ref)
        s[k] = data.decode('utf-8') if ref['path'].endswith('.md') else json.loads(data)
    for k, ref in manifest['withheldReference'].items():
        s[k] = json.loads(raw(ref))
    s['a3'] = json.loads(raw(manifest['consent']['statements']))
    s['fm'] = json.loads(raw(manifest['published']['foundationModels']))
    s['capture'] = {}
    for key in ('shin2022', 'eldbeta'):
        src = s['a3']['sources'][key]
        lic = src['licence']['data']
        for f, h in ((src['capture_file'], src['capture_sha256']), (lic['capture_file'], lic['capture_sha256']),
                     (lic['latest_check']['capture_file'], lic['latest_check']['capture_sha256'])):
            data = (REVIEW / f).read_bytes()
            check(digest(data) == h, f'{f}: not the capture the A3 record names')
            check((REVIEW / (f + '.sha256')).read_text().split()[0] == h, f'{f}: its shasum sidecar differs')
            s['capture'][f] = data.decode('utf-8')
    return s


def catalog_row(s, adapter):
    return next(e for e in s['moabbShortlist']['entries'] if e['adapter'] == adapter)['catalog_metadata']


def number_in(text, pattern, label):
    m = re.search(pattern, squash(text))
    check(m is not None, f'{label}: not stated in the pinned record')
    return m.group(1)


# ---------------------------------------------------------------------------- the expected table
def expected_table(s, served):
    E = {}
    pr, au, la, cr = s['shinProtocol'], s['shinReleaseAudit'], s['shinLabelDuplicateAudit'], s['shinCensusReview']
    dup, sem, rr = s['shinDuplicateReview'], s['shinLabelSemantics'], s['shinResultReview']
    ex = s['shinExport']

    E[('placement', 'leaderboard')] = False
    E[('placement', 'core_matrix')] = False

    # Shin2022 scope, from the label semantics evidence (the export reads the protocol) and the catalog row.
    cat = catalog_row(s, 'Shin2022')
    ch = int(number_in(sem, r'The sampled source configuration is \d+ Hz, (\d+) channels', 'channels'))
    hz = int(number_in(sem, r'The sampled source configuration is (\d+) Hz', 'sampling rate'))
    sc = ('shin2022', 'scope')
    E[sc + ('participants',)] = au['coverage']['participants']
    E[sc + ('recording_days_each',)] = int(cat['#Sess'])
    E[sc + ('channels',)] = ch
    E[sc + ('sampling_hz',)] = hz
    E[sc + ('human_recordings_only',)] = True
    E[sc + ('foundation_models',)] = ex['models_are_foundation_models']
    E[sc + ('leaderboard',)] = False
    E[sc + ('core_matrix',)] = False
    E[('shin2022', 'labels', 'outcome_used')] = pr['labels']['result_code_is_label']

    # Method and interval, from the protocol, recomputed where they follow from it.
    f, ci = pr['features'], pr['confidence_interval']
    m = ('shin2022', 'method')
    E[m + ('folds',)] = pr['folds']['outer_fold_count']
    check(pr['folds']['outer_fold_count'] == pr['participant_count'], 'one fold per participant')
    E[m + ('training_participants_each_fold',)] = pr['participant_count'] - 1
    E[m + ('window_samples',)] = f['segment_samples']
    E[m + ('window_seconds',)] = f['segment_samples'] / pr['fs']
    check(f['main_arm_feature_count'] == f['channel_count'] * len(f['band_bins_hz_inclusive']), 'feature count')
    E[m + ('features',)] = f['channel_count'] * len(f['band_bins_hz_inclusive'])
    (a0, a1), (b0, b1) = f['band_bins_hz_inclusive']
    for k, v in ((('bands_hz', 'alpha', 0), a0), (('bands_hz', 'alpha', 1), a1), (('bands_hz', 'beta', 0), b0),
                 (('bands_hz', 'beta', 1), b1), (('reference_band_hz', 0), f['reference_bins_hz_inclusive'][0]),
                 (('reference_band_hz', 1), f['reference_bins_hz_inclusive'][1])):
        E[m + k] = v
    E[m + ('ridge_alpha',)] = pr['arms']['spectral_ridge']['alpha']
    E[m + ('tuning',)] = pr['model']['hyperparameter_search']
    E[m + ('hypothesis_tests',)] = pr['metrics']['hypothesis_tests'] != 'none'
    E[m + ('label_from_outcome',)] = pr['labels']['result_code_is_label']
    lo_p, hi_p = (float(x) for x in re.findall(r'percentiles([\d.]+)and([\d.]+)', ci['interval'])[0])
    iv = ('shin2022', 'interval')
    E[iv + ('level',)] = round((hi_p - lo_p) / 100, 12)
    E[iv + ('resamples',)] = au['bootstrap']['resamples']
    E[iv + ('seed',)] = au['bootstrap']['seed']
    says(rr, 'one shared10-column index matrix', 'shared index matrix')
    E[iv + ('one_index_matrix_for_all_arms',)] = True
    says(ci['interpretation'], 'Descriptive participant-cluster uncertainty', 'descriptive interval')
    E[iv + ('descriptive',)] = True

    # The three arms: the release audit's independent reconstruction.
    for i, a in enumerate(au['independent_metrics']):
        for k in ('participant_mean_balanced_accuracy', 'pooled_balanced_accuracy_secondary'):
            E[('shin2022', 'arms', i, k)] = a[k]
        for j in (0, 1):
            E[('shin2022', 'arms', i, 'participant_bootstrap_percentile_95', j)] = a['participant_bootstrap_percentile_95'][j]

    # The coverage chain, from other records than the export reads, each re-added here.
    integ, ob, part = la['integrity'], la['observed'], la['partial_run']
    views = integ['record_count_with_companions_verified']
    says(sem, f'All {views} headers show', 'recorded runs')
    pairs = ob['signal_duplicate_groups']
    says(dup, 'There are **nine exact raw duplicate groups, each of size two**, all within one participant and all '
              'pairing **BW30 with NT0**.', 'duplicate pairs')
    check(pairs == 9, 'the duplicate review counts nine pairs')
    distinct = ob['unique_signal_payloads']
    says(dup, f'yields{distinct}unique raw/signal payloads', 'distinct runs')
    check(views - pairs == distinct, 'distinct runs do not add up')
    says(dup, 'One view is an incomplete planned run.', 'incomplete run')
    incomplete = 1
    complete = pr['complete_unique_records']
    says(dup, f'gives{complete}complete unique records; all have 24 closed windows, 12 per target', 'complete runs')
    check(distinct - incomplete == complete, 'complete runs do not add up')
    closed = pr['source_closed_windows']
    check(closed == complete * 24, 'closed windows do not add up')
    distinct_closed = closed + part['closed_feedback_windows']
    check(distinct_closed == ob['unique_closed_feedback_windows'], 'distinct closed windows do not add up')
    m = re.search(r'([\d,]+) instructed-right and ([\d,]+) instructed-left', squash(dup))
    check(m is not None, 'closed windows by target: not stated in the duplicate review')
    by_closed = {'1': int(m.group(1).replace(',', '')), '2': int(m.group(2).replace(',', ''))}
    check(by_closed['1'] + by_closed['2'] == closed, 'closed windows by target do not add up')
    cov = pr['eligibility']['coverage']
    short, by_short = cov['short_windows'], cov['short_by_target']
    eligible, by_eligible = cr['unique_windows'], cr['target_denominators']
    check(closed - short == eligible == cov['original_duration_eligible_windows'], 'duration-eligible windows')
    check(all(by_closed[t] - by_short[t] == by_eligible[t] for t in ('1', '2')), 'duration-eligible by target')
    sv = pr['signal_validity']
    invalid, by_invalid = sv['excluded_signal_invalid_windows'], sv['excluded_by_target']
    valid, by_valid = sv['eligible_windows'], sv['eligible_by_target']
    check(eligible - invalid == valid and all(by_eligible[t] - by_invalid[t] == by_valid[t] for t in ('1', '2')),
          'signal-valid windows')
    all_flat = cr['independent_categories']['all16_constant']['affected_windows']
    says(rr, f'The{all_flat}all-channel flat windows are a subset of those13', 'flat windows')
    check(cr['independent_categories']['any_channel_constant']['affected_windows'] == invalid, 'constant windows')
    says(rr, f'Coverage is{valid}/{closed}={sv["coverage_of2400_percent"]}%, or{valid}/{eligible}=99.4178% of',
         'coverage percentages')
    check(abs(sv['coverage_of2233_percent'] - 100 * valid / eligible) < 1e-9 and sv['coverage_of2400_percent']
          == 100 * valid / closed, 'coverage percentages do not follow from the counts')
    steps = {
        'recorded_runs': {'count': views},
        'byte_identical_pairs': {'count': pairs, 'within_one_participant': ob['all_duplicate_groups_within_participant']},
        'distinct_runs': {'count': distinct, 'closed_windows': distinct_closed},
        'incomplete_run_held': {'count': incomplete},
        'complete_runs': {'count': complete, 'participants': pr['participant_count'],
                          'windows_per_run_by_target': {'1': 12, '2': 12}},
        'closed_windows': {'count': closed, 'by_target': by_closed},
        'shorter_than_one_second': {'count': short, 'by_target': by_short},
        'duration_eligible': {'count': eligible, 'by_target': by_eligible},
        'signal_invalid': {'count': invalid, 'by_target': by_invalid, 'flat_on_all_channels': all_flat,
                           'flat_on_some_channels': invalid - all_flat,
                           'non_finite_input_windows': cr['independent_categories']['nonfinite_input']['affected_windows']},
        'signal_valid': {'count': valid, 'by_target': by_valid, 'percent_of_closed_windows': sv['coverage_of2400_percent'],
                         'percent_of_duration_eligible': sv['coverage_of2233_percent'],
                         'participants_with_both_targets': pr['participant_count'] if sv['all10participants_both_targets']
                         else None},
    }
    chain = served['shin2022']['coverage_chain']
    check([c['id'] for c in chain] == list(steps), 'the coverage chain lists other steps or another order')
    for i, (sid, want) in enumerate(steps.items()):
        for k, v in want.items():
            if isinstance(v, dict):
                for t, x in v.items():
                    E[('shin2022', 'coverage_chain', i, k, t)] = x
            else:
                E[('shin2022', 'coverage_chain', i, k)] = v

    # The catalog against the files: the trial length from the catalog row, the cap from the duplicate review.
    cap = int(number_in(dup, r'6\.016s versus the(\d+)s cap', 'feedback cap'))
    E[('shin2022', 'catalog', 'catalog_trial_seconds')] = int(cat['Trial (s)'])
    E[('shin2022', 'catalog', 'header_feedback_cap_seconds')] = cap
    E[('shin2022', 'catalog', 'headers_read')] = views

    # How it was checked.
    hc = served['shin2022']['how_checked']
    check([h['id'] for h in hc] == ['strict-protocol-stopped', 'score-free-census', 'second-protocol-frozen',
                                    'predictions-sealed', 'independent-audit', 'release-review'], 'the checks changed')
    says(s['shinZeroPowerReview'], 'Diagnostic evidence records zero fitted models.', 'strict protocol')
    E[('shin2022', 'how_checked', 0, 'models_fitted')] = 0
    E[('shin2022', 'how_checked', 1, 'windows')] = eligible
    E[('shin2022', 'how_checked', 1, 'models_trained')] = cr['models_trained']
    E[('shin2022', 'how_checked', 1, 'scores_computed')] = cr['scores_computed']
    E[('shin2022', 'how_checked', 2, 'scores_inspected_during_design')] = pr['authorization']['scores_inspected_during_design']
    E[('shin2022', 'how_checked', 4, 'metrics_reproduced')] = au['independent_metrics'] == ex['metrics']
    diff = float(number_in(rr, r'maximum absolute decision difference([\d.e-]+),', 'decision difference'))
    check(diff == au['independent_audit_max_decision_error'], 'the review and the audit state other differences')
    E[('shin2022', 'how_checked', 4, 'max_decision_difference')] = diff

    # Rights, terms and consent: numbers and flags.
    for case, key in (('shin2022', 'shin2022'), ('eldbeta', 'eldbeta')):
        src = s['a3']['sources'][key]
        lic = src['licence']['data']
        record = json.loads(s['capture'][lic['capture_file']])
        versions = json.loads(s['capture'][lic['latest_check']['capture_file']])
        t = (case, 'rights', 'terms', 'data_licence')
        E[t + ('pinned_version',)] = record['version']
        E[t + ('versions_listed',)] = len(versions)
        E[t + ('pinned_version_is_latest',)] = record['version'] == max(v['version'] for v in versions)
        c = (case, 'consent_and_ethics')
        E[c + ('ethics_approval', 'stated')] = src['ethics']['stated']
        E[c + ('informed_consent', 'stated')] = src['consent']['stated']
        if src['ethics']['approval_number'] is None:
            E[c + ('ethics_approval', 'approval_number')] = NULL

    # eldBETA: counts from the release audit and the raw QC aggregate; the cohort from the MOABB catalog row.
    ea, qc, ee = s['eldbetaReleaseAudit'], s['eldbetaRawQc'], s['eldbetaExport']
    k = ('eldbeta', 'counts')
    E[k + ('participants_run',)] = ea['participants']
    E[k + ('published_participants',)] = int(catalog_row(s, 'Liu2022EldBETA')['#Subj'])
    E[k + ('blocks',)] = ea['blocks']
    E[k + ('targets',)] = ea['targets']
    E[k + ('trials',)] = ea['trials']
    E[k + ('trials_passing_checks',)] = qc['valid_trials']
    E[k + ('trials_dropped',)] = qc['trials_dropped']
    E[k + ('non_finite_values_in_analysed_windows',)] = qc['selected_window_nonfinite_values']
    E[k + ('non_finite_values_outside_analysed_windows',)] = (qc['continuous_nonfinite_values']
                                                              - qc['selected_window_nonfinite_values'])
    says(s['eldbetaHandoff'], 'It applies the original affine physical/digital calibration', 'header calibration')
    E[('eldbeta', 'flags', 'header_calibration_applied')] = True
    E[('eldbeta', 'flags', 'derived_matlab_epochs_used')] = not any('unused' in x and 'MAT' in x for x in ee['limitations'])
    E[('eldbeta', 'flags', 'recordings_repaired')] = not ee['source_qc']['no_raw_crop_repair_or_mutation']
    E[('eldbeta', 'flags', 'score_published')] = False

    # ZuCo 2.0: flags only, from the independent alignment audit and the intake gate.
    za, gate = s['zucoAlignmentAudit'], s['zucoIntakeGate']
    z = ('zuco2', 'flags')
    E[z + ('fixation_times_outside_recording',)] = (za['flags']['onset_beyond_recording'] > 0
                                                    or za['flags']['end_beyond_recording'] > 0)
    E[z + ('stimulus_markers_within_recording',)] = za['markers_within_recording']
    E[z + ('timing_corrected',)] = 'no repair' not in za['action']
    E[z + ('rows_removed',)] = 'deletion' not in za['action']
    E[z + ('score_computed',)] = 'score' not in za['action']
    E[z + ('data_redistributed',)] = 'No public subject/text redistribution authorized' not in gate['terms']['limit']
    E[('zuco2', 'consent_and_ethics', 'read')] = False
    return E


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest):
    check(served['release_id'] == manifest['release_id'] == 'data-quality-update-20261020', 'another release')
    check(served['generated_at'] == manifest['release_date'], 'another release date')
    check(served['schema_version'] == 'bci-report-data-quality-update-v1', 'another schema')
    check([c['id'] for c in served['cases']] == ['shin2022', 'eldbeta', 'zuco2'], 'other cases')
    ex, au = s['shinExport'], s['shinReleaseAudit']
    check(au['independent_metrics'] == ex['metrics'], 'the research export and its audit differ')
    arms = served['shin2022']['arms']
    check([a['arm'] for a in arms] == [m['arm'] for m in ex['metrics']], 'the arms are not the export’s, in its order')
    for a, m in zip(arms, ex['metrics']):
        check(all(same_value(a[k], v) if not isinstance(v, list) else a[k] == v for k, v in m.items()),
              f'{a["arm"]}: not the export’s fields verbatim')
    check([a['role'] for a in arms] == ['reference', 'eeg', 'retrospective_control'], 'the arm roles changed')
    check(served['shin2022']['labels']['classes'] == {k: v.split(',')[0] for k, v in
                                                      s['shinProtocol']['labels']['class_meaning'].items()}, 'labels')
    # Consent, ethics and terms are the A3 record's, and each quotation is in its capture.
    for case in ('shin2022', 'eldbeta'):
        src = s['a3']['sources'][case]
        ce = served[case]['consent_and_ethics']
        check(ce['ethics_approval']['statement'] == src['ethics']['statement']
              and ce['ethics_approval']['quote'] == src['ethics_quote'] and ce['ethics_approval']['body'] == src['ethics']['body']
              and ce['informed_consent']['statement'] == src['consent']['statement']
              and ce['informed_consent']['quote'] == src['consent_quote'] and ce['read_from'] == src['read_from']
              and ce['capture_sha256'] == src['capture_sha256'] and ce['read_at'] == src['captured_at']
              and ce['gaps'] == src['gaps'], f'{case}: the consent and ethics block is not the A3 record’s')
        page = visible(s['capture'][src['capture_file']])
        for q in (src['ethics_quote'], src['consent_quote'], src['licence']['paper']['quote']):
            check(squash(q) in page, f'{case}: a quotation is not in its capture: {q[:40]!r}')
        record = json.loads(s['capture'][src['licence']['data']['capture_file']])
        desc = visible(record['description'])
        for t in served[case]['rights']['terms']['other_terms_stated']:
            if t['stated_by'].startswith('Figshare'):
                check(squash(t['quote']) in desc, f'{case}: a term is not in the record description')
            else:
                check(squash(t['quote']) in page, f'{case}: a term is not in the paper capture')
        r = served[case]['rights']
        authors = [a['full_name'] for a in record['authors']]
        check(r['license'] == record['license']['name'] and r['licenseUrl'] == record['license']['url']
              and r['source'] == f'https://doi.org/{record["doi"]}', f'{case}: another licence or source')
        check(r['attribution'].endswith(ENDING) and record['doi'] in r['attribution']
              and all(a in r['attribution'] for a in authors) and record['title'] in r['attribution'],
              f'{case}: the attribution does not name the record')
        check(r['terms']['data_licence']['capture_sha256'] == src['licence']['data']['capture_sha256'],
              f'{case}: another licence capture')
    # ZuCo 2.0 identity from the intake gate.
    ident, terms = s['zucoIntakeGate']['identity'], s['zucoIntakeGate']['terms']
    zs = served['zuco2']['source']
    check(zs['accession'] == ident['dataset_id'] and f'https://doi.org/{zs["doi"]}' == ident['version_doi']
          and zs['url'] == ident['version_base'] and zs['licence_as_stated'] == terms['dataset_declared_license']
          and zs['citation'] == terms['acknowledgement'], 'ZuCo 2.0: another identity')
    # The SingLEM fact is the released exposure row's.
    rel = served['eldbeta']['related']
    pe = s['fm']['results']['foundation-models-v9']['pretraining_exposure']
    cell = next(c for c in pe['cells'] if c['model'] == rel['model'] and c['dataset'] == rel['dataset'])
    check('Only eldBETA' in cell['evidence'] and 'different database from BETA' in cell['evidence']
          and next(m for m in pe['models'] if m['key'] == rel['model'])['name'] == rel['model_name'],
          'the SingLEM exposure row says otherwise')
    check(served['not_published'] == manifest['notPublished'], 'the not-published list is not the manifest’s')
    check(served['holds'] == manifest['holds'], 'the holds are not the manifest’s')
    pv = served['provenance']
    src = manifest['sources']
    check(pv['source_export_sha256'] == {'shin2022': src['shinExport']['sha256'], 'eldbeta': src['eldbetaExport']['sha256']}
          and pv['release_audit_sha256'] == {'shin2022': src['shinReleaseAudit']['sha256'],
                                             'eldbeta': src['eldbetaReleaseAudit']['sha256']}
          and pv['protocol_sha256']['shin2022'] == src['shinProtocol']['sha256']
          and pv['protocol_sha256']['eldbeta'] == s['eldbetaReleaseAudit']['protocol_sha256']
          and pv['evidence_sha256']['consent_statements'] == manifest['consent']['statements']['sha256'],
          'the provenance names other files')


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
    blob = s['moabbWebsiteHandoff'] + s['eldbetaHandoff'] + s['zucoHandoff']
    names = {x for pair in re.findall(r'/(?:home|Users|Volumes|mnt)/([^/\s`]+)/([^/\s`]+)', blob) for x in pair}
    hosts = set(re.findall(r'\b(?:on|or) ([A-Z][A-Za-z]{1,8}\d+)\b', blob))
    names |= hosts | {re.sub(r'\d+$', '', h) for h in hosts}
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Values the sources hold that the release does not publish, as floats and as larger counts."""
    fl, it = set(), set()
    la, pr, cr = s['shinLabelDuplicateAudit'], s['shinProtocol'], s['shinCensusReview']
    dc = la['duration_and_coverage']
    fl |= set(dc['feedback_quantiles_seconds'].values()) | {dc['feedback_mean_seconds']}
    fl.add(la['decision']['one_second_planning_contract']['coverage_percent'])
    for blk in (dc, pr['eligibility']['coverage']):
        it |= {v for key, v in blk.items() if 'per_participant' in key}
    for c in cr['independent_categories'].values():
        it |= set(c['participant_denominator_min_max']) | set(c['unflagged_windows_per_participant_min_max'])
    it |= {la['observed']['samples_including_duplicate_views'], la['observed']['extra_duplicate_closed_windows'],
           la['observed']['closed_feedback_windows_including_duplicate_views']}
    au = s['shinReleaseAudit']
    fl |= {a['cpu_seconds'] for a in au['accounting']} | {a['wall_seconds'] for a in au['accounting']}
    it |= {au['combined_output_bytes'], au['source_bytes']}
    cat = catalog_row(s, 'Shin2022')
    catalog = {int(cat['#Trials']), int(cat['#Runs'])}
    ee = s['eldbetaExport']
    held = {ee['top1_accuracy'], ee['fixed_first_frequency_comparator']['accuracy'],
            ee['independent_audit']['max_correlation_residual']}
    fl |= held
    blob = json.dumps(s['zucoFollowup']) + json.dumps(s['zucoAlignmentAudit'])
    fl |= {float(x) for x in re.findall(r'-?\d+\.\d+', blob)}
    it |= {int(x) for x in re.findall(r'(?<![\d.])\d{3,}(?![\d.])', json.dumps(s['zucoAlignmentAudit']))}
    fl -= {0.0, 0.5, 0.95, 1.0}
    return fl, {v for v in it if v > 16} | catalog | {ee['correct']}


def text_checks(served_text, served, s):
    flat_text = served_text
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', flat_text) is None, 'a private path')
    private = private_names(s)
    check(len(private) >= 3, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', flat_text, re.I) is None,
              'a private host or storage name reached the served file')
    for pattern, why in ((r'BI2013a|Brain Invaders|2669187|1494163', 'register-only BI2013a'),
                         (r'ICLR|OpenReview|submission|iMINDBench|NEAR-Bench', 'a submission reference'),
                         (r'(?<![\d.])55(?:\.0+)?\s*%|fifty[- ]five', 'the commenter’s figure'),
                         (r'\b26\s*/\s*63\b|\b26 of 63\b|41\.27|11\.11', 'the held eldBETA score'),
                         (r'sub-[A-Za-z]|\bYAC\b|run-6\b|4,?287,?888|2\^32', 'a ZuCo 2.0 run code or value'),
                         (r'\b2,?640\b', 'MOABB’s catalog trial count'),
                         (r'(?i)\bjev\b', 'Jev')):
        check(re.search(pattern, flat_text) is None, f'{why} reached the served file')
    for trail, v in all_leaves(served['zuco2']):
        if trail in (('id',), ('section',), ('name',)) or trail[:1] == ('source',):
            continue
        check(not isinstance(v, (int, float)) or isinstance(v, bool), f'zuco2/{trail}: a figure')
        check(not (isinstance(v, str) and re.search(r'\d', v)), f'zuco2/{trail}: a digit')
    for trail, _ in all_leaves(served['eldbeta']):
        check(not any(isinstance(t, str) and re.search(r'accuracy|correct|comparator|top1|residual', t) for t in trail),
              f'eldbeta/{trail}: a held-score field')


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    s = sources(manifest)
    E = expected_table(s, served)
    string_checks(s, served, manifest)

    found = dict(leaves(served))
    copied_keys = {'participant_mean_balanced_accuracy', 'pooled_balanced_accuracy_secondary',
                   'participant_bootstrap_percentile_95', 'max_decision_difference', 'percent_of_duration_eligible',
                   'percent_of_closed_windows'}
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
        'auditor': 'pipeline/publication/audit_data_quality_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins, and takes Shin2022’s arms from the release '
                         'audit’s independent reconstruction (the export reads the research export), the run chain from '
                         'the label audit’s integrity block and the duplicate review, the window chain from the frozen '
                         'protocol and the census review, eldBETA’s counts from its release audit and raw QC aggregate '
                         'and its cohort size from the MOABB catalog row (the export reads the research export and the '
                         'Figshare record), and every derived figure from its own arithmetic on those.'),
        'cases': [c['id'] for c in served['cases']],
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'flags': flags,
        'nulls_kept': nulls,
        'withheld_values_checked_absent': len(fl) + len(it),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every pinned input is the file the manifest names, and every A3 capture has the SHA-256 the record and its '
            'shasum sidecar give',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'Shin2022’s three arms equal the release audit’s independent reconstruction and are the export’s fields '
            'verbatim, in its order',
            'the coverage chain adds up from 110 recorded runs to 2220 signal-valid windows, link by link, from records '
            'other than those the export reads where a second record exists',
            'eldBETA’s counts equal its release audit and raw QC aggregate; no held score, comparator or residual and no '
            'held-score field is in the file',
            'the ZuCo 2.0 case carries no figure or digit outside its anchor, name and source identity, and its flags '
            'follow the independent alignment audit',
            'consent, ethics and terms are the A3 record’s, and every quotation is found verbatim in its capture',
            'no per-participant range, duration distribution, catalog count, held eldBETA figure, ZuCo 2.0 run value, '
            'register-only content, submission reference, private host, storage name or path is in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'research exports, release audits, protocol, label and duplicate audit, census review and raw QC '
                'aggregate: pinned in the manifest and named in the served provenance',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
                'consent and ethics: the A3 record, pinned in the manifest, and its captures, pinned by the record',
            ],
            'not_bound': [
                'the sealed predictions and private score files are verified by the research release audits, whose '
                'records are pinned; this audit does not open them',
                'prose, the arm descriptions, the holds and the release record are checked by the export, not by this '
                'audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
