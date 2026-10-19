"""Independent audit of neurolm-eegmat-update.json: every figure in the served file against the pinned sources.

A separate program from export_neurolm_eegmat_update.py. It shares no code with that export and imports nothing from it:
it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what every
number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- the scores and paired differences are read from where the export does not read them: the producer aggregate that the
  interpretation review pins and the independent numerical audit checked (the export reads the approved export), and
  they equal the readings' verified numbers digit for digit;
- derived figures are recomputed here: the interval flags, the interval level, the window and patch counts, the fold
  sizes, the dimensions, the parameter count and its float32 state size, the exposure facts, the adapter and the core
  protocol facts, from the protocol, receipts, preflight, stage inspection and the core run's protocols and runner;
- the labels, readings, rights records, licences, hashes and the not-published list are checked as strings;
- the two served copies are one, the served file names the manifest it was built from, and no measured compute, no
  private path and no private user, host or volume name is in it.

    python3 pipeline/publication/audit_neurolm_eegmat_export.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'neurolm-eegmat-release-manifest.json'
AUDIT = REVIEW / 'neurolm-eegmat-export-audit.json'
SERVED = (PROJECT / 'site/src/data/neurolm-eegmat-update.json', PROJECT / 'site/public/data/neurolm-eegmat-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
# The editorial decisions this audit holds the file to (plan section 2.5 and the owner's defaults).
LABELS = {'tokenizer_mean': 'tokenizer features', 'log_bandpower': 'band power', 'gpt_mean': 'GPT hidden states'}
ORDER = [('tokenizer_mean', 'log_bandpower'), ('gpt_mean', 'tokenizer_mean'), ('gpt_mean', 'log_bandpower')]
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')
LIMITATION_IDS = ['exposure', 'adapter', 'band-power', 'recording-order', 'capacity', 'random-initialisation',
                  'interval', 'development-cohort', 'ica', 'scope']


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


def doc(ref):
    return json.loads(raw(ref))


def text(ref):
    return raw(ref).decode('utf-8')


def same_number(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


def num(token):
    return float(token) if '.' in token else int(token)


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {'manifest': manifest}
    for group in ('research', 'planning', 'published', 'core'):
        s[group] = {}
        for k, r in manifest[group].items():
            if isinstance(r, dict):
                s[group][k] = doc(r) if r['path'].endswith('.json') else text(r)
    return s


def expected_table(s, served):
    E = {}
    rs, core = s['research'], s['core']
    pending, proto, audit = rs['pendingAggregate'], rs['protocol'], rs['numericalAudit']
    src, pre, stage = rs['export'], rs['preflight'], rs['stageInspection']
    smoke = rs['smokeEvidence']['files']['smoke-attempt-03.json']
    data, ad, feats = proto['data'], proto['adapter'], proto['features']

    # the export the site reads equals the producer aggregate the numerical audit checked
    check(src['aggregate'] == pending['aggregate'] and src['paired_contrasts'] == pending['paired_contrasts'],
          'the approved export and the audited aggregate differ')
    check(audit['status'] == 'passed' and audit['paired_bootstrap_match'] is True
          and audit['binding']['protocol_sha256'] == pending['binding']['protocol_sha256']
          == s['manifest']['research']['protocol']['sha256'], 'the numerical audit checked another aggregate')

    # placement
    rel = rs['releaseRecord']
    defaults = ' '.join(s['manifest']['approval']['previewDefaults'])
    check('outside the pilot count' in defaults, 'the approval no longer places it outside the pilot count')
    E[('placement', 'counted_in_pilots')] = False
    E[('placement', 'leaderboard')] = rel['overall_leaderboard_eligible']
    arith = next(t for t in s['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    E[('placement', 'core_matrix_row')] = any('neurolm' in r['name'].lower() for r in arith['rows'])
    E[('placement', 'new_dataset_count')] = src['new_dataset_count_increment']
    E[('placement', 'new_model_count')] = 0

    # cohort
    blocks = re.search(r';(\d+)one-second blocks x(\d+)channels=(\d+)patches', ad['patch_order'])
    conditions = len(re.findall(r'->', data['label_rule']))
    cohort = {'people': pending['participants'], 'recordings': data['edf_records'], 'conditions': conditions,
              'retained_seconds': ad['retained_record_seconds'], 'window_seconds': ad['window_seconds'],
              'windows_per_recording': ad['windows_per_record'], 'windows': pending['windows'],
              'channels': len(data['channels']), 'source_sampling_hz': ad['input_sfreq_hz'],
              'sampling_hz': ad['output_sfreq_hz'], 'folds': proto['split']['fold_count']}
    check(cohort['recordings'] == conditions * cohort['people']
          and cohort['windows'] == cohort['recordings'] * cohort['windows_per_recording'], 'the cohort does not add up')
    for k, v in cohort.items():
        E[('cohort', k)] = v
    for i, n in enumerate(audit['coverage']['fold_participants']):
        E[('cohort', 'fold_sizes_people', i)] = n

    # model
    sr = smoke['strict_restore']
    check(smoke['checkpoint_state']['tensor_bytes'] == 4 * sr['parameters'], 'the restored state is not float32')
    E[('model', 'parameters')] = sr['parameters']
    E[('model', 'restored_state_entries')] = sr['model_state_keys']
    E[('model', 'checkpoint', 'bytes')] = proto['checkpoint']['bytes']
    for k, key in (('layers', 'n_layer'), ('heads', 'n_head'), ('width', 'n_embd'), ('context_tokens', 'block_size')):
        E[('model', 'architecture', k)] = stage['model_args'][key]
    E[('model', 'frozen')] = src['foundation_parameters_frozen']
    E[('model', 'fine_tuning')] = audit['new_backbone_training']
    E[('model', 'text_generation')] = src['text_generation_used']
    E[('model', 'language_model_head')] = feats['gpt_mean']['call_counts_per_batch']['LM_head'] > 0
    check(src['release_scope'] == 'aggregate pilot card only; no raw data, per-person records or checkpoints',
          'the release scope changed')
    E[('model', 'weights_distributed')] = False

    # exposure
    names = pre['exposure']['pretraining_dataset_names']
    E[('pretraining_exposure', 'published_pretraining_list', 'datasets')] = len(names)
    E[('pretraining_exposure', 'published_pretraining_list', 'includes_eegmat')] = any(
        re.search(r'eegmat|mental arithmetic|workload', n, re.I) for n in names)
    cs = ('pretraining_exposure', 'checkpoint_stage')
    E[cs + ('checkpoint_epoch',)] = stage['epoch']
    E[cs + ('iteration',)] = stage['iteration']
    E[cs + ('learning_rate',)] = stage['selected_config']['learning_rate']
    E[cs + ('instruction_tuning_verified',)] = pre['hf']['instruction_tuned_checkpoint_verified']

    # adapter
    f, rp = ad['filter'], ad['resample']
    adapter = {'own_adapter': ad['new_declared_adapter'], 'source_sampling_hz': ad['input_sfreq_hz'],
               'sampling_hz': ad['output_sfreq_hz'], 'filter_order': f['order'], 'zero_phase': f['zero_phase_offline'],
               'offline': f['zero_phase_offline'], 'notch': not ad['notch'].startswith('none'),
               'amplitude_divisor': pre['input']['amplitude_divisor'], 'window_patches': int(blocks.group(3)),
               'patch_seconds': ad['window_seconds'] // int(blocks.group(1))}
    check(int(blocks.group(2)) == cohort['channels'] and int(blocks.group(1)) * cohort['channels'] == int(blocks.group(3)),
          'the patches do not tile the window')
    for k, v in adapter.items():
        E[('adapter', k)] = v
    E[('adapter', 'resample', 'up')], E[('adapter', 'resample', 'down')] = rp['up'], rp['down']
    E[('adapter', 'band_pass_hz', 0)], E[('adapter', 'band_pass_hz', 1)] = f['low_hz'], f['high_hz']
    for i, hz in enumerate(pre['input']['notch_hz']):
        E[('adapter', 'official_notch_hz', i)] = hz

    # probe
    head = re.search(r'RidgeClassifier\(alpha=(\d+),', proto['probe']['pipeline'][1])
    E[('probe', 'alpha')] = int(head.group(1))
    E[('probe', 'fits')] = proto['probe']['fits']
    E[('probe', 'hyperparameter_search')] = not proto['probe']['all_final_no_hpo']
    E[('probe', 'sealed_before_scoring')] = 'after prediction manifest sealed' in proto['probe']['labels']

    # arms: scores from the audited aggregate, dimensions from the protocol, no interval per arm
    check([a['id'] for a in served['arms']] == list(LABELS), 'the arms are not in the handoff’s order')
    for i, a in enumerate(LABELS):
        E[('arms', i, 'dimension')] = feats[a]['dimension']
        E[('arms', i, 'balanced_accuracy')] = pending['aggregate'][a]['equal_person_balanced_accuracy']
        E[('arms', i, 'macro_f1')] = pending['aggregate'][a]['equal_person_macro_f1']
        E[('arms', i, 'interval_95')] = NULL
    check(feats['log_bandpower']['dimension'] == cohort['channels'] * len(feats['log_bandpower']['bands_hz']),
          'band power is not channels by bands')

    # chance
    chance = re.search(r'Binary balanced-accuracy chance is (\d+)%', text(s['manifest']['research']['handoff']))
    E[('chance_level', 'balanced_accuracy')] = int(chance.group(1)) / 100
    E[('chance_level', 'macro_f1')] = NULL

    # paired contrasts
    pairs = {(c['a'], c['b']): c for c in pending['paired_contrasts']}
    check([(c['a'], c['b']) for c in served['paired_contrasts']] == ORDER, 'the contrasts are not in the reviewed order')
    for i, ab in enumerate(ORDER):
        c = pairs[ab]
        for j, m in enumerate(c['metric_order']):
            base = ('paired_contrasts', i, m)
            lo, hi = c['interval95'][j]
            check(lo <= c['estimate'][j] <= hi, f'{ab} {m}: the interval does not hold its estimate')
            E[base + ('difference',)] = c['estimate'][j]
            E[base + ('interval_95', 0)], E[base + ('interval_95', 1)] = lo, hi
            E[base + ('interval_includes_zero',)] = lo <= 0 <= hi

    # interval
    pb = proto['metrics']['paired_bootstrap']
    lo_p, hi_p = pb['interval_percentiles']
    E[('interval', 'level')] = (hi_p - lo_p) / 100
    E[('interval', 'resamples')] = pb['resamples']
    E[('interval', 'seed')] = pb['seed']
    E[('interval', 'same_resamples_all_contrasts')] = pb['same_resamples_all_contrasts']
    E[('interval', 'fixed_fits')] = src['bootstrap']['fixed_fits']

    # the core protocol, from its own pinned files
    dp, ep, runner = core['datasetProtocol'], core['engineProtocol'], core['runner']
    sc = ('separate_from_core',)
    E[sc + ('shared_windows',)] = (f'First {ad["retained_record_seconds"]} s of each recording; '
                                   f'{ad["windows_per_record"]} contiguous nonoverlapping {ad["window_seconds"]} s windows'
                                   in dp['preprocessing'] and dp['window_seconds'] == ad['window_seconds'])
    E[sc + ('shared_channels',)] = [c.upper() for c in dp['channels']] == list(data['channels'])
    E[sc + ('shared_fold_rule',)] = ("'fold_assignment':'sorted subject index modulo fold_count'" in runner
                                     and 'modulo5' in proto['split']['rule'] and dp['fold_count'] == cohort['folds'])
    E[sc + ('shared_head',)] = (ep['ridge']['alpha'] == E[('probe', 'alpha')] and ep['ridge']['solver'] == 'cholesky'
                                and ep['ridge']['class_weight'] == 'balanced' and 'solver=cholesky' in
                                proto['probe']['pipeline'][1] and 'class_weight=balanced' in proto['probe']['pipeline'][1])
    E[sc + ('core_band_pass',)] = 'no rejection, filtering' not in dp['preprocessing']
    E[sc + ('core_sampling_hz',)] = int(re.search(r'resample_poly to(\d+)Hz', ep['native_to_canonical']).group(1))
    spec = re.search(r"'spectral':'Welch at(\d+)Hz, [^']*?log relative PSD([\d.]+)-([\d.]+)Hz", runner)
    E[sc + ('core_spectral_ridge', 'band_hz', 0)] = num(spec.group(2))
    E[sc + ('core_spectral_ridge', 'band_hz', 1)] = num(spec.group(3))
    E[sc + ('core_spectral_ridge', 'sampling_hz')] = int(spec.group(1))
    bands = feats['log_bandpower']['bands_hz']
    E[sc + ('pilot_band_power', 'band_hz', 0)] = bands[0][0]
    E[sc + ('pilot_band_power', 'band_hz', 1)] = bands[-1][1]
    E[sc + ('pilot_band_power', 'sampling_hz')] = feats['log_bandpower']['sampling_rate_hz']

    # rights
    paper = next(p for p in rs['paperRecord']['opportunities'] if p['id'] == 'neurolm')
    E[('rights', 'checkpoint', 'model_card_bytes')] = pre['hf']['card_bytes']
    E[('rights', 'checkpoint', 'model_card_terms')] = 'model card body empty' not in paper['licenses']['weights']
    E[('rights', 'checkpoint', 'gated')] = pre['hf']['gated']
    E[('rights', 'checkpoint', 'weights_distributed')] = False

    # audits
    na = ('audits', 'independent_numerical_audit')
    E[na + ('artifacts_hash_verified',)] = audit['unique_artifacts_hash_verified']
    E[na + ('refits',)] = audit['linear_refits_completed']
    E[na + ('refits_exact',)] = audit['all_refit_predictions_exact']
    E[na + ('saved_decisions_reconstructed',)] = audit['all_saved_decisions_reconstructed']
    E[na + ('bootstrap_max_abs_difference',)] = audit['numerical_max_absolute_differences']['manual_paired_interval']
    E[na + ('checkpoint_loads',)] = audit['foundation_checkpoint_loads']
    return E


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest):
    rs, rm = s['research'], manifest['research']
    src, pre, proto = rs['export'], rs['preflight'], rs['protocol']
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['freeze_date']
          and manifest['freeze_date'].replace('-', '') == manifest['release_id'].rsplit('-', 1)[1], 'another release')
    check(served['status'] == 'aggregate_preview' == manifest['approval']['decision'], 'another decision')
    for a in served['arms']:
        check(a['label'] == LABELS[a['id']], f'{a["id"]}: not the reviewed label')
    for c in served['paired_contrasts']:
        for m in ('balanced_accuracy', 'macro_f1'):
            x = c[m]
            want = SPANS_ZERO if x['interval_includes_zero'] else (
                f'the interval lies {"below" if x["interval_95"][1] < 0 else "above"} zero; descriptive, from this one '
                f'cohort')
            check(x['reading'] == want, f'{c["id"]} {m}: another reading')
    check(served['paired_contrasts'][0]['role'] == 'question'
          and all(c['role'] == 'descriptive' for c in served['paired_contrasts'][1:]), 'the contrast roles changed')
    check(served['cohort']['channel_names'] == proto['data']['channels'], 'another montage')
    m = served['model']
    check(m['checkpoint']['sha256'] == src['checkpoint_sha256'] == proto['checkpoint']['sha256']
          and m['checkpoint']['revision'] == src['checkpoint_revision'] == pre['hf']['revision']
          and m['source_revision'] == proto['code_revision'] == pre['code']['revision']
          and m['repository'] == pre['code']['repo']
          and m['checkpoint']['repository'] == f'https://huggingface.co/{pre["hf"]["repo_id"]}', 'another model')
    paper = next(p for p in rs['paperRecord']['opportunities'] if p['id'] == 'neurolm')
    check(m['paper'] in paper['sources'] and m['paper_title'] == paper['title'], 'another paper')
    ex = served['pretraining_exposure']
    check(ex['status'] == 'unknown' and ex['checkpoint_stage']['status'] == 'unknown'
          and ex['checkpoint_stage']['initialised_from'] == rs['stageInspection']['selected_config']['init_from']
          and ex['instruction_tasks'] == list(pre['instruction_tasks']) and ex['eegmat_instruction_task'] == 'Workload'
          and ex['checked_on'] == pre['checked_date'], 'the exposure is not the pinned facts')
    r = served['rights']
    track = next(t for t in s['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt', 'reviewBasis',
              'rightsScope'):
        check(r['dataset'][k] == track[k], f'the EEGMAT rights record is not the released one ({k})')
    check(r['dataset']['name'] == track['dataset'], 'the rights record names another dataset')
    lic = next(f for f in pre['minimal_assets']['source_files'] if f['path'] == 'LICENSE')
    check(r['code']['licence'] == pre['code']['license'] == 'MIT'
          and r['code']['licence_file_sha256'] == lic['sha256_measured'] == proto['source_sha256']['LICENSE'],
          'the code licence is not the pinned one')
    check(r['checkpoint']['licence'] == 'CC BY 4.0' and pre['hf']['license_metadata'] == 'cc-by-4.0'
          and r['checkpoint']['checked_on'] == pre['checked_date'], 'the checkpoint licence is not the stated one')
    check([x['id'] for x in served['limitations']] == LIMITATION_IDS, 'the limitations changed')
    pv = served['provenance']
    check(pv['source_export_sha256'] == {'neurolm-eegmat': rm['export']['sha256']}
          and pv['research_release_sha256'] == rm['releaseRecord']['sha256']
          and pv['protocol_sha256'] == rm['protocol']['sha256'] == src['protocol_sha256']
          and pv['numerical_audit_sha256'] == rm['numericalAudit']['sha256'], 'provenance differs')
    au = served['audits']
    check(au['independent_numerical_audit']['sha256'] == rm['numericalAudit']['sha256']
          and au['reviews'] == {'execution': rm['executionReview']['sha256'],
                                'numerical_audit': rm['numericalAuditReview']['sha256'],
                                'interpretation': rm['interpretationReview']['sha256']}, 'another audit named')
    check(served['not_published'] == manifest['notPublished'], 'the not-published list is not the manifest’s')
    check(served['release_record']['research_release_status'] == rs['releaseRecord']['status'],
          'another research release status')


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
    rs = s['research']
    blob = json.dumps(rs['protocol']) + json.dumps(rs['smokeEvidence']['root'])
    names = {x for pair in re.findall(r'/home/([^/"\s]+)/([^/"\s]+)/', blob) for x in pair}
    for pattern in (r'(\w+) was not mounted', r'on both Mac and (\w+)'):
        names |= set(re.findall(pattern, rs['handoff']))
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Measured compute: worker times and memory, never published."""
    rs = s['research']
    out = {float(x) for x in re.findall(r'(\d+\.\d+) seconds', rs['handoff'])}
    out |= {float(x) for x in re.findall(r'about (\d+\.\d+) GiB', rs['handoff'])}
    for f in rs['smokeEvidence']['files'].values():
        if isinstance(f, dict):
            out |= {f[k] for k in ('elapsed_seconds', 'peak_rss_bytes') if isinstance(f.get(k), (int, float))}
    out |= {rs['numericalAudit']['peak_rss_bytes'], rs['stageInspection']['elapsed_seconds']}
    return out - {0.0, 0.5, 1.0, 2.0}


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

    # The copied figures are the ones the readings verified, digit for digit.
    r = next(e for e in s['planning']['readings'] if e['id'] == manifest['planning']['readings']['entry'])['result']
    verified = set()
    for n in r['public_numbers']:
        for field in ('value', 'interval'):
            verified |= {float(t) for t in re.findall(r'[-+]?\d+\.\d+(?:e-?\d+)?', n.get(field, ''))}

    found = dict(leaves(served))
    copied_keys = {'balanced_accuracy', 'macro_f1', 'difference', 'interval_95'}
    exact = recomputed = nulls = 0
    for path, value in found.items():
        check(path in E, f'{"/".join(map(str, path))}: a figure with no audit rule')
        want = E[path]
        if want is NULL:
            check(value is None, f'{"/".join(map(str, path))}: a null became {value!r}')
            nulls += 1
            continue
        check(same_number(value, want), f'{"/".join(map(str, path))}: {value!r} where the sources give {want!r}')
        if path[0] in ('arms', 'paired_contrasts') and [k for k in path if isinstance(k, str)][-1] in copied_keys:
            check(value in verified, f'{"/".join(map(str, path))}: a figure the readings did not verify')
            exact += 1
        else:
            recomputed += 1
    missing = [p for p in E if p not in found]
    check(not missing, f'expected figures missing from the served file: {missing[:3]}')

    published = {v for v in found.values() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    secret = withheld(s)
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
        'auditor': 'pipeline/publication/audit_neurolm_eegmat_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins, takes the scores and paired differences '
                         'from the producer aggregate that the interpretation review pins and the independent numerical '
                         'audit checked (the export reads the approved export), requires them equal to the readings’ '
                         'verified numbers, and derives every other figure by its own reading of the protocol, receipts, '
                         'preflight, stage inspection and core run files.'),
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'nulls_kept': nulls,
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'scores and paired differences equal the audited producer aggregate, the approved export and the readings’ '
            'verified numbers',
            'interval flags, interval level, cohort counts, fold sizes, patches, dimensions, the parameter count and the '
            'exposure and adapter facts are recomputed from the pinned protocol and receipts',
            'the core protocol facts are read from the core run’s pinned dataset and engine protocols and runner',
            'labels, readings, the EEGMAT rights record, the licences per part, the hashes and the not-published list '
            'are checked as strings',
            'no measured compute, no private path and no private user, host or volume name in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'the approved export, protocol, producer, numerical audit and three reviews: pinned in the manifest and '
                'bound by the research release record, which the export checks',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
            ],
            'not_bound': [
                'the NeuroLM features themselves: the independent numerical audit refitted the heads from the sealed '
                'values and did not re-extract them; this audit opens no sealed file',
                'prose, the limitation texts and the release record are checked by the export, not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
