"""Independent audit of clinical-iesseeg-update.json: every figure in the served file against the pinned sources.

A separate program from export_clinical_iesseeg_update.py. It shares no code with that export and imports nothing from
it: it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what
every number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- the score blocks are read from where the export does not read them: the independent numerical audits that the two
  release reviews bind (the export copies the research exports and requires them equal), arm by arm in the order of
  each study's protocol;
- the cohort and fold structure from the cohort timing QC audit's selection record; the age band's counts from the
  release reviews' numeric checks; the input-cohort QC from the same audit's recomputed aggregate and distributions;
  every method figure from the pinned protocol of its study; the audit counts from the reviews' numerical records;
- derived figures are recomputed here: the chance level, the frequency resolution, the token length, the display flags,
  the EEG-input and comparison flags, the redistribution and update flags;
- the dataset strings equal the release card at the pinned revision and the reviews' attribution records; the model
  strings equal the NeuroLM review's provenance; the provenance hashes equal the manifest's pins;
- the two served copies are one, the served file names the manifest it was built from, and no per-fold metric, no
  per-group age summary, no private path, host or storage name and no conference or submission reference is in it.

    python3 pipeline/publication/audit_clinical_iesseeg_export.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'clinical-iesseeg-release-manifest.json'
AUDIT = REVIEW / 'clinical-iesseeg-export-audit.json'
SERVED = (PROJECT / 'site/src/data/clinical-iesseeg-update.json', PROJECT / 'site/public/data/clinical-iesseeg-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
COPIED_SECTIONS = ('pooled', 'age_le_2', 'audit', 'input_qc', 'age_band', 'counts')


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


def doc(ref):
    return json.loads(raw(ref))


def squash(s):
    return re.sub(r'\s+', ' ', s).strip()


def same_value(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


def float_leaves(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from float_leaves(x)
    elif isinstance(v, list):
        for x in v:
            yield from float_leaves(x)
    elif isinstance(v, float):
        yield v


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    src = manifest['sources']
    s = {k: (squash(raw(r).decode('utf-8')) if r['path'].endswith(('.md', 'LICENSE')) else doc(r)) for k, r in src.items()}
    s['card_raw'] = raw(src['releaseCard']).decode('utf-8')
    s['handoffs_raw'] = raw(src['controlsHandoff']).decode('utf-8') + raw(src['neurolmHandoff']).decode('utf-8')
    s['scored'] = doc(manifest['withheldReference']['controlsScoredAggregates'])
    s['metadata'] = doc(manifest['withheldReference']['cohortMetadataAudit'])
    s['clinical'] = doc(manifest['published']['clinical'])
    return s


def reviewed(s, manifest):
    """The reviews approve the pinned exports and bind the numerical audits and protocols this audit reads from."""
    src = manifest['sources']
    for study in ('controls', 'neurolm'):
        rv = s[f'{study}ReleaseReview']
        check(rv['status'] == 'independent_aggregate_release_review_passed', f'{study}: the review did not pass')
        check(rv['export_sha256'] == src[f'{study}Export']['sha256'], f'{study}: the review approves another export')
        values = set(rv['reviewed_artifact_sha256'].values())
        check(src[f'{study}NumericalAudit']['sha256'] in values and src[f'{study}Protocol']['sha256'] in values,
              f'{study}: the review does not bind the numerical audit or protocol read here')
    cpu = s['controlsReleaseReview']['reviewed_artifact_sha256']
    check(cpu['evidence/dataset-access-20261016/iesseeg-README.md'] == src['releaseCard']['sha256']
          and cpu['evidence/dataset-access-20261016/iesseeg-LICENSE'] == src['releaseLicence']['sha256'],
          'the CPU review binds another release card')


def card_facts(s):
    card = squash(s['card_raw'])
    title = re.search(r'Please cite \*\*(.+?)\*\*', card).group(1)
    reuse = re.search(r'The (\d+) case clinician-selected EEG segments were previously analyzed by (.+?), \*(.+?)\*', card)
    return {'text': card, 'title': title, 'segments': int(reuse.group(1)), 'study': reuse.group(2),
            'study_title': reuse.group(3)}


def ordered(dist, key=int):
    pairs = [(key(k), v) for k, v in dist.items()]
    return sorted(pairs, key=lambda kv: (-kv[1], kv[0]))


# ---------------------------------------------------------------------------- the expected table
def expected_table(s, served):
    E, derived = {}, set()

    def put(path, value, how='copied'):
        E[path] = value
        if how == 'derived':
            derived.add(path)

    cr, nr = s['controlsReleaseReview'], s['neurolmReleaseReview']
    increment = cr['claims_review']['canonical_dataset_increment']
    check(increment == nr['claims_review']['canonical_dataset_increment'], 'the reviews state other count increments')
    check('outside overall' in cr['scope'] and 'outside overall' in nr['claims_review']['release_scope'],
          'a review places the result on a leaderboard')
    put(('placement', 'leaderboard'), False, 'derived')
    put(('placement', 'dataset_page'), increment > 0, 'derived')
    put(('counts', 'new_canonical_datasets'), increment)
    put(('counts', 'new_model_identity'), nr['claims_review']['new_model_identity'])
    put(('counts', 'new_dataset_pages'), increment)
    disclaimer = s['clinical'].get('medical_disclaimer')
    put(('medical_disclaimer',), isinstance(disclaimer, str) and 'Not a diagnosis' in disclaimer, 'derived')

    card = card_facts(s)
    put(('dataset', 'prior_reuse', 'case_segments'), card['segments'])

    # cohort, from the QC audit's selection record and the protocols
    qc, cp, np_ = s['cohortQcAudit'], s['controlsProtocol'], s['neurolmProtocol']
    sel = qc['selection']
    folds = sel['folds']
    check(len({(f['outer_train_people'], f['outer_test_people'], f['case'], f['control']) for f in folds}) == 1,
          'the folds are not all the same shape')
    classes = len(s['controlsNumericalAudit']['aggregate']['EEG']['pooled']['confusion_tn_fp_fn_tp']) // 2
    put(('cohort', 'people'), sel['people'])
    put(('cohort', 'cases'), sel['case_pre'])
    put(('cohort', 'controls'), sel['control'])
    put(('cohort', 'classes'), classes, 'derived')
    put(('cohort', 'chance_level'), 1 / classes, 'derived')
    put(('cohort', 'seconds_analysed'), cp['window_seconds'])
    put(('cohort', 'channels'), len(cp['channels']), 'derived')
    put(('cohort', 'folds'), len(folds), 'derived')
    put(('cohort', 'train_people'), folds[0]['outer_train_people'])
    put(('cohort', 'held_out_people'), folds[0]['outer_test_people'])
    put(('cohort', 'held_out_cases'), folds[0]['case'])
    put(('cohort', 'held_out_controls'), folds[0]['control'])

    # the age band, from the reviews' numeric checks and the protocol's subgroup rule
    band = cr['numeric_checks']['age_le_2_n_cases_controls']
    check(band == nr['numeric_checks']['age_le_2_n_cases_controls'], 'the reviews checked other age bands')
    put(('age_band', 'maximum_age_years'), int(re.search(r'age <= (\d+) years', cp['subgroup']).group(1)))
    put(('age_band', 'people'), band[0])
    put(('age_band', 'cases'), band[1])
    put(('age_band', 'controls'), band[2])
    same = cr['numeric_checks']['same_sealed_predictions_no_subgroup_refits']
    put(('age_band', 'same_predictions'), same)
    put(('age_band', 'refit'), not same, 'derived')

    # input-cohort QC
    ra = qc['recomputed_aggregate']
    put(('input_qc', 'assets'), qc['payload_hashes_verified'])
    put(('input_qc', 'bytes'), qc['payload_bytes_verified'])
    put(('input_qc', 'recordings'), ra['records_completed'])
    put(('input_qc', 'recordings_passed'), ra['passed'])
    put(('input_qc', 'recordings_held'), ra['held'])
    put(('input_qc', 'recordings_with_gaps'), ra['records_with_gaps'])
    for i, (c, n) in enumerate(ordered(qc['distributions']['scalp_channels'])):
        put(('input_qc', 'scalp_channels', i, 'channels'), c)
        put(('input_qc', 'scalp_channels', i, 'recordings'), n)
    for i, (hz, n) in enumerate(ordered(qc['distributions']['scalp_sampling_hz'], lambda k: int(float(k)))):
        put(('input_qc', 'sampling_hz', i, 'hz'), hz)
        put(('input_qc', 'sampling_hz', i, 'recordings'), n)

    # display flags
    check(cp['confidence_intervals'].startswith('deferred; none') and s['neurolmExport']['confidence_intervals'] is None,
          'a protocol specified intervals')
    put(('display', 'interval'), NULL, 'derived')
    prior = s['controlsNumericalAudit']['aggregate']['SOURCE_PRIOR']['pooled']
    put(('display', 'f1_headline'), not (prior['f1'] > prior['balanced_accuracy']), 'derived')

    # the spectral method, from its protocol
    f, w = cp['features'], cp['features']['welch']
    put(('controls', 'method', 'feature_count'), f['total'])
    put(('controls', 'method', 'features_per_channel'), f['per_channel'])
    put(('controls', 'method', 'welch_window_seconds'), w['seconds'])
    put(('controls', 'method', 'welch_overlap'), w['overlap_fraction'])
    put(('controls', 'method', 'frequency_resolution_hz'), 1 / w['seconds'], 'derived')
    for i, b in enumerate(f['bands_hz']):
        for j, edge in enumerate(b):
            put(('controls', 'method', 'bands_hz', i, j), edge)
    put(('controls', 'method', 'logistic_c'), cp['model']['C'])

    # the score blocks, from the independent numerical audits, in protocol order
    for study, protocol, audit in (('controls', cp, s['controlsNumericalAudit']), ('neurolm', np_, s['neurolmNumericalAudit'])):
        for i, arm in enumerate(protocol['arms']):
            eeg = study == 'neurolm' or 'EEG' in arm
            put((study, 'arms', i, 'eeg_input'), eeg, 'derived')
            put((study, 'arms', i, 'excluded_from_model_comparisons'), not eeg, 'derived')
            for block in ('pooled', 'age_le_2'):
                for k, v in audit['aggregate'][arm][block].items():
                    if isinstance(v, list):
                        for j, x in enumerate(v):
                            put((study, 'arms', i, block, k, j), x)
                    else:
                        put((study, 'arms', i, block, k), v)

    # the spectral audit counts, from the CPU numerical audit
    ca = s['controlsNumericalAudit']
    for k, v in (('models', ca['models']), ('learned_refits', ca['learned_refits']), ('prior_checks', ca['prior_checks']),
                 ('reconstructed_predictions', ca['reconstructed_predictions']),
                 ('independent_feature_checks', ca['feature_spot_checks']),
                 ('max_feature_error', ca['manual_fft_feature_max_absolute_error']),
                 ('max_probability_error', max(ca['reconstruction_max_absolute_error'], ca['refit_max_probability_error']))):
        put(('controls', 'audit', k), v)

    # NeuroLM: model flags from the review's provenance and the protocol; method figures from the protocol
    prov, att = nr['provenance'], np_['attention']
    put(('neurolm', 'model', 'weights_updated'), not nr['claims_review']['checkpoint_not_updated'], 'derived')
    put(('neurolm', 'model', 'text_tokens'), att['text_tokens'])
    put(('neurolm', 'model', 'generation'), att['generation'])
    put(('neurolm', 'model', 'redistributed'), not prov['model_code_checkpoint_and_data_not_redistributed'], 'derived')
    put(('rights', 'redistributed'), not prov['model_code_checkpoint_and_data_not_redistributed'], 'derived')
    pre = np_['preprocessing']
    fs = pre['bandpass']['fs']
    put(('neurolm', 'method', 'sampling_hz'), fs)
    put(('neurolm', 'method', 'resample_factor'), pre['resampling']['down'] // pre['resampling']['up'], 'derived')
    for j, x in enumerate(pre['bandpass']['hz']):
        put(('neurolm', 'method', 'bandpass_hz', j), x)
    for j, x in enumerate(pre['notch']['hz']):
        put(('neurolm', 'method', 'notch_hz', j), x)
    put(('neurolm', 'method', 'amplitude_divisor'), pre['amplitude_divisor'])
    m = re.search(r'(\d+) nonoverlapping(\d+)s windows', ' '.join(pre['sequence']))
    put(('neurolm', 'method', 'windows'), int(m.group(1)))
    put(('neurolm', 'method', 'window_seconds'), int(m.group(2)))
    shape = np_['patches']['shape']
    put(('neurolm', 'method', 'tokens_per_window'), shape[1])
    put(('neurolm', 'method', 'token_seconds'), shape[2] // fs, 'derived')
    put(('neurolm', 'method', 'dimensions'), np_['representations']['dimensions'])

    # NeuroLM audit counts, from the review's numerical-audit boundary record
    nb = nr['numerical_audit_boundary']
    for k, v in (('independent_refits', nb['independent_supervised_head_refits']),
                 ('held_out_predictions_reconstructed', nb['reconstructed_predictions']),
                 ('reconstruction_error', nb['reconstruction_max_absolute_error']),
                 ('refit_error', nb['refit_max_probability_error']),
                 ('source_hash_checks', nb['source_asset_hashes_verified_by_numerical_auditor']),
                 ('feature_receipts_checked', nb['feature_receipt_hashes_layout_finiteness_verified']),
                 ('real_neural_features_independently_recomputed', nb['real_neural_features_independently_reextracted'])):
        put(('neurolm', 'audit', k), v)
    return E, derived, card


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest, card):
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['release_date'],
          'another release')
    check(served['schema_version'].startswith('bci-report-clinical-iesseeg-update'), 'another schema')
    cr, nr = s['controlsReleaseReview'], s['neurolmReleaseReview']
    ar, prov = cr['attribution_review'], nr['provenance']
    d = served['dataset']
    check(d['revision'] == prov['dataset_revision'] == s['controlsExport']['revision'], 'another revision')
    check(d['url'] == prov['dataset_url'] and d['release_card_url'] == ar['readme_url'] == prov['dataset_readme_url']
          and d['licence_file_url'] == ar['license_url'] == prov['dataset_license_url'], 'another pinned URL')
    check(d['licence'] == ar['dataset_annotation_license_declaration'] == prov['dataset_annotation_license_declaration'],
          'another licence')
    check(d['requested_citation'] == card['title'] == ar['publisher_requested_title'] == prov['dataset_citation'],
          'the requested citation is not the card’s')
    check(d['prior_reuse']['study'] == card['study'] == ar['source_study_attribution']
          and d['prior_reuse']['study_title'] == card['study_title'] == ar['source_study_title'],
          'the prior-reuse declaration is not the card’s')
    check(d['ethics_as_stated']['quote'] in card['text'] and served['cohort']['age_matching_as_stated']['quote'] in card['text'],
          'a quotation is not on the release card')
    check(d['ethics_as_stated']['source'] == ar['readme_url'], 'the quotation names another source')
    check(served['rights']['license'] == d['licence'] and served['rights']['source'] == d['url'], 'the rights record differs')
    for study, protocol in (('controls', s['controlsProtocol']), ('neurolm', s['neurolmProtocol'])):
        check([a['id'] for a in served[study]['arms']] == protocol['arms'], f'{study}: the arms are not the protocol’s')
    model = served['neurolm']['model']
    check(model['checkpoint_sha256'] == prov['checkpoint_sha256'] == s['neurolmProtocol']['checkpoint_sha256']
          and model['source_revision'] == prov['model_source_revision'] and model['source_url'] == prov['model_source_url'],
          'another NeuroLM checkpoint or source')
    unverified = prov['checkpoint_instruction_stage_and_participant_exposure_unverified']
    check(unverified is True and model['checkpoint_stage'] == model['pretraining_exposure'] == 'unknown',
          'the checkpoint stage or exposure is stated as known')
    rv = cr['verified_numerical_audit_receipt']
    ca = served['controls']['audit']
    check((ca['protocol_sha256'], ca['score_sha256'], ca['seal_sha256']) == (rv['protocol_sha256'], rv['score_sha256'],
                                                                             rv['seal_sha256']), 'the CPU audit names other files')
    nb = nr['numerical_audit_boundary']
    na = served['neurolm']['audit']
    check((na['seal_sha256'], na['score_sha256']) == (nb['seal_sha256'], nb['score_sha256']), 'the NeuroLM audit names other files')
    check(served['display']['primary_metric'] == s['controlsProtocol']['metrics'][0]
          and cr['claims_review']['primary_metric_prespecified_balanced_accuracy'] is True, 'another primary metric')
    for col in served['display']['columns']:
        check(col['block'] in ('pooled', 'age_le_2') and col['metric'] in served['controls']['arms'][0][col['block']],
              f'a display column names no published field: {col}')
    check(not any(c['metric'] == 'f1' for c in served['display']['columns']), 'F1 is a display column')
    src = manifest['sources']
    pv = served['provenance']
    check(pv['source_export_sha256'] == {'controls': src['controlsExport']['sha256'], 'neurolm': src['neurolmExport']['sha256']}
          and pv['release_review_sha256'] == {'controls': src['controlsReleaseReview']['sha256'],
                                              'neurolm': src['neurolmReleaseReview']['sha256']}
          and pv['numerical_audit_sha256'] == {'controls': src['controlsNumericalAudit']['sha256'],
                                               'neurolm': src['neurolmNumericalAudit']['sha256']}
          and pv['protocol_sha256'] == {'controls': src['controlsProtocol']['sha256'],
                                        'neurolm': src['neurolmProtocol']['sha256']}
          and pv['cohort_qc_audit_sha256'] == src['cohortQcAudit']['sha256']
          and pv['release_card_sha256'] == {'readme': src['releaseCard']['sha256'], 'licence': src['releaseLicence']['sha256']},
          'the provenance hashes are not the manifest’s pins')
    check(served['not_published'] == manifest['notPublished'] and served['holds'] == manifest['holds'],
          'the not-published list or holds are not the manifest’s')
    check(served['medical_disclaimer_wording'] == {'file': 'clinical-update.json', 'field': 'medical_disclaimer'},
          'the disclaimer points elsewhere')


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


def keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys(v)


def private_names(s):
    text = s['handoffs_raw']
    names = {x for pair in re.findall(r'/(?:home|Users)/([^/\s`]+)/([^/\s`]+)', text) for x in pair}
    names |= {x for pair in re.findall(r'stay on (\w+)|Mac or (\w+)', text) for x in pair if x}
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Per-fold metrics and per-group age summaries, less what the approved blocks themselves carry."""
    out = set()
    for arm in s['scored']['scores'].values():
        out |= set(float_leaves(arm['per_fold'])) | set(float_leaves(arm['age_le_2_years']['per_fold']))
    for group in s['metadata']['age_summary'].values():
        out |= set(float_leaves({k: v for k, v in group.items() if k != 'available_n'}))
    approved = set(float_leaves(s['controlsNumericalAudit']['aggregate'])) | set(float_leaves(s['neurolmNumericalAudit']['aggregate']))
    return out - approved - {0.0, 0.25, 0.5, 0.75, 1.0}


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    s = sources(manifest)
    reviewed(s, manifest)
    E, derived, card = expected_table(s, served)
    string_checks(s, served, manifest, card)

    found = dict(leaves(served))
    exact = recomputed = nulls = 0
    for path, value in found.items():
        check(path in E, f'{"/".join(map(str, path))}: a figure with no audit rule')
        want = E[path]
        if want is NULL:
            check(value is None, f'{"/".join(map(str, path))}: a null became {value!r}')
            nulls += 1
            continue
        check(same_value(value, want), f'{"/".join(map(str, path))}: {value!r} where the sources give {want!r}')
        if path in derived:
            recomputed += 1
        else:
            exact += 1
    missing = [p for p in E if p not in found]
    check(not missing, f'expected figures missing from the served file: {missing[:3]}')

    published = {v for v in found.values() if isinstance(v, float)}
    secret = withheld(s)
    check(len(secret) >= 20, 'too few withheld values read from the pinned records')
    check(not (secret & published), f'a withheld value reached the served file: {sorted(secret & published)[:3]}')
    text_blob = served_bytes[0].decode()
    for group in s['metadata']['age_summary'].values():
        check(f'{group["mean_years"]:.3f}' not in text_blob, 'a per-group age mean reached the served file')
    banned_keys = re.compile(r'age_mean|mean_years|median|quartile|sex|gender|per_fold|participant_id|patient_id')
    check(not any(banned_keys.search(k) for k in keys(served)), 'a demographic or per-fold field reached the served file')
    private = private_names(s)
    check(len(private) >= 3, 'no private names read from the pinned handoffs')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text_blob, re.I) is None,
              'a private host or storage name reached the served file')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')
    check(re.search(r'ICLR|OpenReview|NeurIPS|submission|conference', text_blob, re.I) is None,
          'a conference or submission reference reached the served file')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_clinical_iesseeg_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins, and takes the score blocks from the '
                         'independent numerical audits the release reviews bind (the export copies the research exports), '
                         'the cohort and fold structure from the cohort timing QC audit’s selection record, the age band '
                         'from the reviews’ numeric checks, the audit counts from the reviews’ numerical records, and '
                         'every derived figure from its own arithmetic on those.'),
        'arms': {'controls': [a['id'] for a in served['controls']['arms']],
                 'neurolm': [a['id'] for a in served['neurolm']['arms']]},
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'nulls_kept': nulls,
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'both release reviews passed, approve the pinned exports, and bind the numerical audits, protocols and '
            'release card read here',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'all ten score blocks, all-100 and age <=2, equal the independent numerical audits value for value, in '
            'protocol order',
            'cohort, folds, age band and input-cohort QC equal the QC audit’s selection and recomputed aggregate and the '
            'reviews’ numeric checks',
            'method figures equal the pinned protocols; audit counts equal the reviews’ numerical records',
            'dataset strings equal the release card at the pinned revision and both reviews’ attribution records; the '
            'model strings equal the NeuroLM review’s provenance; provenance hashes equal the manifest’s pins',
            'no per-fold metric, per-group age summary or demographic field, no private host, storage name or path, '
            'and no conference or submission reference, in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'research exports, release reviews, numerical audits, protocols, cohort QC audit, release card and '
                'licence: pinned in the manifest and named in the served provenance',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
            ],
            'not_bound': [
                'the private seal, score and prediction files are named by SHA-256 only; the reviews verified them, and '
                'this audit does not open them',
                'labels, captions, limitations, the release record and other prose are checked by the export, not by '
                'this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
