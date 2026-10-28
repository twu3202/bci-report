"""Independent audit of neurorvq-update.json: every figure in the served file against the pinned sources.

A separate program from export_neurorvq_update.py. It shares no code with that export and imports nothing from it: it
reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what every
number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- the scores, paired differences and intervals are the study audit receipts' values (the only full-precision record),
  and each must also round to the figures the study's interpretation review checked and the study handoff prints,
  which the export does not read for this purpose;
- every other figure is derived here from sources the export reads differently or not at all: the restore counts from
  the prospective protocols and the release approval's gate name, the pooled size from the protocol's pooling text,
  the cohort from the header-admission summary and the core matrix's released tracks, the resampling ratios from the
  protocol text, the core sampling rate of EEGMAT from the released NeuroLM panel, the dimensions from the protocols'
  comparator text, the exposure counts from the loader and exposure contract;
- the labels, readings, licences, rights records, hashes, caveat keys and the not-published list are checked as strings;
- the figures the limitation texts, the scope, the arm definitions and the audit boundaries quote must be the figures
  derived here, and every text outside provenance must hash to the reviewed text the manifest records, so an edited
  sentence or an added text key fails;
- three statements of what was done are held to records read here: the EEGMAT filter runs over the retained first
  minute of each recording (the protocol's record extent), the P300 cache's original preparation was not re-run (the P300
  receipt's caveats), and the EEGMAT audit read both arms' values from the producer's sealed files without re-extracting
  them (its audit program, pinned beside the receipt);
- the two served copies are one, the served file names the manifest it was built from, and no measured compute, no
  above-50% count, no private path and no private user, host or volume name is in it.

    python3 pipeline/publication/audit_neurorvq_export.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'neurorvq-release-manifest.json'
AUDIT = REVIEW / 'neurorvq-export-audit.json'
SERVED = (PROJECT / 'site/src/data/neurorvq-update.json', PROJECT / 'site/public/data/neurorvq-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
ORDER = ['eegmat', 'mi-rest', 'p300-target']
PROTOCOL = {'eegmat': 'arithmetic-rest', 'mi-rest': 'mi-rest', 'p300-target': 'p300-target'}
# The editorial decisions this audit holds the file to (plan section 2.2 and the manifest's preview defaults).
ARMS = {
    'eegmat': [('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
               ('band-power', 'band power', 'matched comparator', 'spectral')],
    'mi-rest': [('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
                ('temporal-means', 'temporal means', 'primary comparator', 'temporal'),
                ('band-power', 'band power', 'descriptive comparator', 'spectral')],
    'p300-target': [('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
                    ('temporal-means', 'temporal means', 'primary comparator', 'temporal')],
}
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')
BELOW_ZERO = 'the interval lies below zero; descriptive, from this one cohort'
LIMITATION_IDS = ['variant', 'transfer', 'exposure', 'input-scale', 'input-eegmat', 'input-cache', 'units',
                  'dimensions', 'p300-windows', 'eegmat-order', 'development-cohort', 'interval', 'separation', 'scope',
                  'rights']
# Caveats every block carries, and those of one task (the sources state the input scale, the scope and EEGMAT's
# development use as limits of each result they apply to).
EVERY_BLOCK = {'variant', 'transfer', 'exposure', 'input-scale', 'dimensions', 'interval', 'separation', 'scope',
               'rights'}
ONLY = {'eegmat': {'input-eegmat', 'eegmat-order', 'development-cohort'}, 'mi-rest': {'input-cache', 'units'},
        'p300-target': {'input-cache', 'units', 'p300-windows'}}
NOT_RUN = ['semantic-target', 'beta-4ch', 'beta-8ch', 'idle', 'sleep-scalp']
COUNT_WORDS = {'ONE': 1, 'TWO': 2, 'FOUR': 4, 'EIGHT': 8}
TEXT_EXCLUDED = ('provenance',)    # the manifest's own hash lives there, so the reviewed text cannot cover it


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
    text = raw(ref).decode('utf-8')
    name = Path(ref['path']).name
    return json.loads(text) if name.endswith('.json') or name in ('neurorvq_hf.txt', 'neurorvq_repo.txt') else text


def same_number(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


def squash(text):
    return re.sub(r'\s+', '', text)


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {'manifest': manifest, 'research': {}}
    for task, refs in manifest['research'].items():
        s['research'][task] = {k: doc(r) for k, r in refs.items()}
    for group in ('model', 'handoff', 'published'):
        s[group] = {k: doc(r) for k, r in manifest[group].items()}
    s['owner'] = doc(manifest['approval']['ownerDecisions'])
    s['licence_bytes'] = [raw(manifest['model'][k]) for k in ('codeLicence', 'weightsLicence')]
    return s


def queue_entry(s, task):
    return next(p for p in s['research'][task]['queue']['protocols'] if p['protocol_id'] == task)


def track(s, task):
    return next(t for t in s['published']['coreMatrix']['tracks'] if t['id'] == PROTOCOL[task])


def scores(s, task):
    """The receipt's values, held to the interpretation review's and the handoff's printed figures."""
    au = s['research'][task]['audit']
    if task == 'eegmat':
        m = {k: (v['mean_participant_balanced_accuracy'], v['mean_participant_macro_f1']) for k, v in au['methods'].items()}
        est, ci = au['mean_difference'], au['paired_person_bootstrap_percentile95']
        review = s['research'][task]['interpretationReview']['numerical_consistency']
        for k in m:
            check(f'{100 * m[k][0]:.4f}%' in review and f'{m[k][1]:.5f}'.lstrip('0') in review,
                  f'{task} {k}: not the interpretation review’s figures')
        check(f'difference{100 * est:+.4f}pp' in review
              and f'interval[{100 * ci[0]:.4f},{100 * ci[1]:+.4f}]pp' in review, f'{task}: another interval reviewed')
    else:
        m = {k: (v['balanced_accuracy'], v['macro_f1']) for k, v in au['mean_participant_metrics'].items()}
        est, ci = au['primary_delta_mean'], au['paired_participant_CI95']
        ir = s['research'][task]['interpretationReview']
        reviewed = json.dumps(ir.get('numerical_text_checks', {})) + json.dumps(ir.get('passed_checks', []))
        check(f'{100 * est:.4f}' in reviewed and f'{100 * ci[0]:.4f},{100 * ci[1]:.4f}' in squash(reviewed),
              f'{task}: another difference reviewed')
        if task == 'p300-target':
            for k in m:
                check(f'{100 * m[k][0]:.4f}%' in reviewed and f'{m[k][1]:.6f}' in reviewed,
                      f'{task} {k}: not the interpretation review’s figures')
    handoff = s['research'][task]['handoff']
    for k, (ba, f1) in m.items():
        check(f'{100 * ba:.4f}%' in handoff, f'{task} {k}: the handoff prints another balanced accuracy')
        check(f'{f1:.{5 if task == "eegmat" else 6}f}' in handoff, f'{task} {k}: the handoff prints another macro-F1')
    check(ci[0] <= est <= ci[1], f'{task}: the interval does not hold its estimate')
    return m, est, ci


def word_count(text):
    return COUNT_WORDS[text.upper()]


def expected_table(s, served):
    E = {}
    rs, md, manifest = s['research'], s['model'], s['manifest']
    owner = s['owner']['decisions']
    d19 = owner['defaults_stated_to_owner_and_not_objected']['D19 (Q5)']

    # placement
    pl = ('placement',)
    E[pl + ('pointers_carry_figures',)] = 'figure-free pointers' not in d19
    E[pl + ('counted_in_pilots',)] = 'uncounted panel' not in d19
    E[pl + ('method_page',)] = 'no method page' not in d19
    E[pl + ('leaderboard',)] = False
    check('Do not merge this score into a global ranking' in rs['eegmat']['handoff'], 'the handoff allows a ranking')
    E[pl + ('core_matrix_row',)] = any('neurorvq' in r['name'].lower() for t in s['published']['coreMatrix']['tracks']
                                       for r in t['rows'])
    E[pl + ('foundation_encoder_table',)] = 'neurorvq' in json.dumps(s['published']['foundationModels']).lower()
    datasets_on_site = {t['dataset'] for t in s['published']['coreMatrix']['tracks']}
    E[pl + ('new_dataset_count',)] = sum(track(s, t)['dataset'] not in datasets_on_site for t in ORDER)
    check(any('no new dataset, model or pilot in any counter' in x for x in manifest['approval']['previewDefaults']),
          'the counts default changed')
    E[pl + ('new_model_count',)] = 0

    # model: restore counts from the prospective protocols, the gate name and the acceptance
    sl = rs['backbone']['strictLoad']
    pm = rs['mi-rest']['protocol']['model']
    check(rs['p300-target']['protocol']['model'] == pm, 'the two prospective protocols name other backbones')
    gate = re.fullmatch(r'FAIL_MISSING_([A-Z]+)_AFFINE_STATE_ENTRIES', rs['eegmat']['approval']['original_full_wrapper_gate'])
    check(gate is not None, 'another wrapper gate')
    pool = re.search(r'concatenation of (\w+)(\d{3}) branches;(\d+)dim', pm['pooling'])
    check(pool is not None, 'the protocol states another pooling')
    branches, width, dim = word_count(pool.group(1)), int(pool.group(2)), int(pool.group(3))
    check(branches * width == dim, 'the pooled size is not the branches joined')
    eps = re.search(r'parameterfreeeps([\d.e-]+),', rs['eegmat']['protocol']['encoder']['strict_load_gate'])
    hf = md['weightsListing']
    fm = next(x for x in md['contract']['artifacts'] if x['rfilename'] == md['contract']['minimum_acquisition']['file'])
    sib = {x['rfilename']: x for x in hf['siblings']}
    m = ('model',)
    E[m + ('checkpoint', 'bytes')] = sib[fm['rfilename']]['size']
    E[m + ('restore', 'strict')] = sl['decision'].startswith('PASS_STRICT')
    E[m + ('restore', 'trained_tensors')] = pm['keys']
    E[m + ('restore', 'trained_elements')] = pm['elements']
    E[m + ('restore', 'checkpoint_tensors')] = pm['keys'] + pm['discarded_checkpoint_keys']
    check(sl['actual_checkpoint_keys'] == pm['keys'] + pm['discarded_checkpoint_keys'], 'the checkpoint counts differ')
    elements = re.search(r'contains (\d+) finite float32 tensors /([\d, ]+) elements', rs['eegmat']['handoff'])
    check(elements is not None and int(elements.group(1)) == E[m + ('restore', 'checkpoint_tensors')],
          'the handoff counts another checkpoint')
    E[m + ('restore', 'checkpoint_elements')] = int(re.sub(r'[, ]', '', elements.group(2)))
    E[m + ('restore', 'unused_checkpoint_tensors')] = pm['discarded_checkpoint_keys']
    E[m + ('restore', 'coverage')] = sl['element_coverage']
    E[m + ('authors_wrapper', 'strict_restore')] = not rs['eegmat']['approval']['original_full_wrapper_gate'].startswith('FAIL')
    E[m + ('authors_wrapper', 'missing_normalisation_tensors')] = word_count(gate.group(1))
    bn = m + ('branch_normalisation',)
    E[bn + ('parameter_free',)] = 'parameter-free' in pm['pooling'] or 'parameterfree' in rs['eegmat']['protocol']['encoder']['strict_load_gate']
    E[bn + ('branches',)] = branches
    E[bn + ('width',)] = width
    E[bn + ('epsilon',)] = float(eps.group(1))
    consts = sl['source_default_equivalence']['explicit_constants']
    E[bn + ('source_default_scale',)] = consts['fc_norm_1.weight']['value']
    E[bn + ('source_default_shift',)] = consts['fc_norm_1.bias']['value']
    E[m + ('pooling', 'branches')] = branches
    E[m + ('pooling', 'branch_width')] = width
    E[m + ('pooling', 'dimension')] = dim
    arch = md['contract']['architecture']['constructor']
    E[m + ('architecture', 'depth')] = arch['depth']
    E[m + ('architecture', 'heads')] = arch['num_heads']
    E[m + ('architecture', 'width')] = arch['embed_dim']
    E[m + ('frozen',)] = 'the encoder stays frozen' in rs['eegmat']['handoff']
    E[m + ('fine_tuning',)] = 'No hyperparameter selection, fine-tuning' not in rs['eegmat']['handoff']
    E[m + ('weights_distributed',)] = False

    # exposure
    pc = md['contract']['pretraining_corpus']
    ex = ('pretraining_exposure',)
    E[ex + ('published_pretraining_list', 'corpora')] = len(pc['datasets'])
    E[ex + ('published_pretraining_list', 'public')] = sum('proprietary' not in n.lower() for n in pc['datasets'])
    E[ex + ('published_pretraining_list', 'proprietary')] = sum('proprietary' in n.lower() for n in pc['datasets'])
    E[ex + ('per_checkpoint_list_published',)] = 'not accompanied by inspected per-checkpoint' not in pc['checkpoint_binding']
    keys = {'eegmat': 'eegmat', 'mi-rest': 'ds003810', 'p300-target': 'ds006593'}
    rows = {x['key']: x for x in md['contract']['core_exposure']}
    for i, t in enumerate(ORDER):
        E[ex + ('datasets', i, 'named_in_list')] = rows[keys[t]]['named_corpus_overlap'] != 'not_named_in_paper_Table6'

    # probe and interval
    probe = rs['eegmat']['protocol']['probe']
    E[('probe', 'alpha')] = int(probe['alpha'])
    check(float(E[('probe', 'alpha')]) == probe['alpha'], 'a fractional alpha')
    E[('probe', 'hyperparameter_search')] = probe['hyperparameter_search']
    E[('probe', 'fine_tuning')] = False
    stages = rs['eegmat']['protocol']['execution']['stages']
    E[('probe', 'sealed_before_scoring')] = stages.index('seal_all_predictions') < stages.index('separate_score_process')
    bs = rs['eegmat']['protocol']['metrics']['bootstrap']
    lo_p, hi_p = re.search(r'percentilelinear([\d.]+)/([\d.]+)', bs).groups()
    E[('interval', 'level')] = (float(hi_p) - float(lo_p)) / 100
    E[('interval', 'resamples')] = rs['eegmat']['audit']['bootstrap_resamples']
    E[('interval', 'seed')] = rs['eegmat']['audit']['seed']
    E[('interval', 'fixed_fits')] = 'no model-refitbootstrap' in bs
    E[('chance_level', 'balanced_accuracy')] = 1 / len(rs['eegmat']['protocol']['input']['label_meaning'])
    E[('chance_level', 'macro_f1')] = NULL

    # the blocks
    check([b['id'] for b in served['blocks']] == ORDER, 'the blocks are not in the plan’s order')
    neurolm_core_hz = s['published']['neurolmEegmat']['separate_from_core']['core_sampling_hz']
    for i, t in enumerate(ORDER):
        B = ('blocks', i)
        r = rs[t]
        au, tr = r['audit'], track(s, t)
        n_windows = int(tr['observations'].split(' epochs')[0].replace(',', ''))
        folds = int(re.search(r'· (\d+) participant-disjoint folds', tr['observations']).group(1))
        ch_core = int(tr['exposure'].split(' channels')[0])
        sec_core = int(re.search(r'(\d+)-second windows', tr['exposure']).group(1))
        if t == 'eegmat':
            hs, p, ad = r['headerSummary'], r['protocol']['input'], r['protocol']['adapter']
            cohort = {'people': hs['people'], 'recordings': hs['records'], 'retained_seconds': p['seconds_per_record'],
                      'window_seconds': sec_core, 'windows_per_recording': n_windows // hs['records'],
                      'windows': n_windows, 'channels': hs['channels'], 'folds': folds}
            bp = re.search(r'N=(\d+),Wn=\[([\d.]+),([\d.]+)\]', ad['bandpass'])
            chain = {'source_sampling_hz': hs['sampling_hz'], 'sampling_hz': md['contract']['input_contract']['sampling_hz']
                     if 'sampling_hz' in md['contract']['input_contract'] else p['output_rate_hz'],
                     'filter_order': int(bp.group(1)), 'forward_backward': 'filtfilt' in ad['bandpass'],
                     'clip_microvolts': max(ad['clip_uv']), 'epoch_demean': ad['demean'],
                     'rereference': ad['rereference'], 'amplitude_divisor': ad['amplitude_divisor']}
            for j, hz in enumerate(ad['notches_hz']):
                E[B + ('input_chain', 'notch_hz', j)] = hz
            E[B + ('input_chain', 'band_pass_hz', 0)] = float(bp.group(2))
            E[B + ('input_chain', 'band_pass_hz', 1)] = float(bp.group(3))
            core_hz = neurolm_core_hz
            same_prepared = False
        else:
            q, pr = queue_entry(s, t), r['protocol']
            cohort = {'people': tr['subjects'], 'windows': n_windows, 'window_seconds': sec_core, 'channels': ch_core,
                      'folds': folds}
            ratio = re.search(r'MI(\d+)/(\d+)' if t == 'mi-rest' else r'resample_poly(\d+)/(\d+)', pr['adapter']['resampling'])
            up, down = int(ratio.group(1)), int(ratio.group(2))
            src = int(q['source_hz'])
            chain = {'source_sampling_hz': src, 'sampling_hz': src * up // down,
                     'epoch_demean': 'mean removed' in json.dumps(q['preprocessing']),
                     'further_filter': 'No new notch, bandpass' not in pr['adapter']['filter_reference'],
                     'clip': 'no new clipping' not in pr['adapter']['amplitude'],
                     'rereference': 'rereference' not in pr['adapter']['filter_reference'],
                     'amplitude_divisor': 1 if 'no /100' in pr['adapter']['amplitude'] else 100}
            E[B + ('input_chain', 'resample', 'up')] = up
            E[B + ('input_chain', 'resample', 'down')] = down
            core_hz = src
            same_prepared = q['recorded_input_sha256']['protocol.json'] == tr['protocolSha'] and \
                au['source_cache_hashes'] == q['recorded_input_sha256']
            if t == 'p300-target':
                bal = re.search(r'(\d+)target\+(\d+)nontarget each', pr['prepared_cohort_limitations'])
                E[B + ('cohort', 'balance', 'target')] = int(bal.group(1))
                E[B + ('cohort', 'balance', 'non_target')] = int(bal.group(2))
                check(cohort['people'] * (int(bal.group(1)) + int(bal.group(2))) == n_windows, 'p300: the balance')
        for k, v in cohort.items():
            E[B + ('cohort', k)] = v
        for k, v in chain.items():
            E[B + ('input_chain', k)] = v
        check(au['participants'] == cohort['people'] and au['rows'] == n_windows, f'{t}: the audit scored another cohort')
        ct = B + ('core_track',)
        E[ct + ('core_rows',)] = any('neurorvq' in x['name'].lower() for x in tr['rows'])
        E[ct + ('same_people',)] = tr['subjects'] == au['participants']
        E[ct + ('same_window_count',)] = n_windows == au['rows']
        E[ct + ('same_prepared_windows',)] = same_prepared
        E[ct + ('own_resampling',)] = core_hz != chain['sampling_hz']
        # recomputed comparators: no comparator score equals any core row of the protocol
        m_, est, ci = scores(s, t)
        core_vals = {v for x in tr['rows'] for v in (x['y'] / 100, x['x'])}
        E[ct + ('comparators_recomputed',)] = not any(m_[k][0] in core_vals or m_[k][1] in core_vals for k in m_)
        # arms
        check([(a['id'], a['label'], a['role']) for a in served['blocks'][i]['arms']]
              == [(a, l, ro) for a, l, ro, _ in ARMS[t]], f'{t}: not the reviewed arms')
        dims = {'neurorvq': dim}
        if t == 'eegmat':
            dims['band-power'] = int(re.search(r'(\d+)D log Welch bandpower', r['protocol']['controls']['primary']).group(1))
        else:
            comp = r['protocol']['comparators']
            if t == 'mi-rest':
                dims['temporal-means'] = int(re.search(r'MI(\d+)dim', comp['primary_all_tasks']).group(1))
                dims['band-power'] = int(re.search(r';(\d+)dim', comp['secondary_mi_only']).group(1))
            else:
                dims['temporal-means'] = int(re.search(r'=(\d+)D', comp['primary']).group(1))
        for j, (aid, _, _, key) in enumerate(ARMS[t]):
            E[B + ('arms', j, 'dimension')] = dims[aid]
            E[B + ('arms', j, 'balanced_accuracy')] = m_[key][0]
            E[B + ('arms', j, 'macro_f1')] = m_[key][1]
            E[B + ('arms', j, 'interval_95')] = NULL
        a0, a1 = ARMS[t][0][3], ARMS[t][1][3]
        check(abs(m_[a0][0] - m_[a1][0] - est) <= 1e-12, f'{t}: the difference is not the arms’')
        pd = B + ('paired_difference',)
        E[pd + ('difference',)] = est
        E[pd + ('interval_95', 0)] = ci[0]
        E[pd + ('interval_95', 1)] = ci[1]
        E[pd + ('interval_includes_zero',)] = ci[0] <= 0 <= ci[1]
        E[B + ('fits',)] = len(ARMS[t]) * folds
        # audit
        ad_ = B + ('audit',)
        if t == 'eegmat':
            E[ad_ + ('heads_refit',)] = au['refitted_heads']
            E[ad_ + ('held_out_outputs_reproduced',)] = au['OOF_predictions_exact']
            E[ad_ + ('comparator_values_bitwise',)] = NULL
            E[ad_ + ('backbone_values_reextracted',)] = not any('full neural re-extraction not repeated' in x
                                                                for x in au['limitations'])
        else:
            E[ad_ + ('heads_refit',)] = au['heads_refit']
            E[ad_ + ('held_out_outputs_reproduced',)] = au['predictions_reproduced']
            E[ad_ + ('comparator_values_bitwise',)] = (au.get('baseline_feature_equality')
                                                       or au.get('all_feature_equality')) == 'bitwise'
            E[ad_ + ('backbone_values_reextracted',)] = (r['neuralAudit']['neural_feature_reextraction'] if t == 'mi-rest'
                                                         else au['neural_feature_reextraction'])
        check(E[ad_ + ('heads_refit',)] == E[B + ('fits',)]
              and E[ad_ + ('held_out_outputs_reproduced',)] == n_windows * len(ARMS[t]), f'{t}: the audit coverage')

    # rights
    E[('rights', 'weights', 'same_file_as_code')] = s['licence_bytes'][0] == s['licence_bytes'][1]
    E[('rights', 'weights', 'weights_distributed')] = False
    return E


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, manifest):
    rs, md = s['research'], s['model']
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['freeze_date']
          and manifest['freeze_date'].replace('-', '') == manifest['release_id'].rsplit('-', 1)[1]
          == s['owner']['freeze_date'], 'another release')
    check(served['status'] == 'aggregate_preview' == manifest['approval']['decision'], 'another decision')
    check(served['schema_version'] == 'bci-report-neurorvq-update-v1', 'another schema')
    for i, t in enumerate(ORDER):
        b = served['blocks'][i]
        check(b['protocol'] == PROTOCOL[t] and b['protocol_page'] == f'/protocols/{PROTOCOL[t]}/'
              and b['dataset'] == track(s, t)['dataset'], f'{t}: another protocol or dataset')
        x = b['paired_difference']
        check(x['a'] == 'neurorvq' and x['b'] == ARMS[t][1][0] and x['metric'] == 'balanced_accuracy'
              and x['role'] == 'primary', f'{t}: another contrast')
        check(x['reading'] == (SPANS_ZERO if x['interval_includes_zero'] else BELOW_ZERO)
              and (x['interval_includes_zero'] or x['interval_95'][1] < 0), f'{t}: another reading')
        check(b['audit']['sha256'] == manifest['research'][t]['audit']['sha256'], f'{t}: another audit named')
        if t == 'mi-rest':
            check(b['audit']['supplement_sha256'] == manifest['research'][t]['neuralAudit']['sha256'], 'mi: supplement')
        check(set(b['caveat_keys']) <= set(LIMITATION_IDS), f'{t}: a caveat key without its caveat')
        check(set(b['caveat_keys']) == EVERY_BLOCK | ONLY[t], f'{t}: the limitations changed for this block')
        check(served['pretraining_exposure']['datasets'][i]['task'] == t
              and served['pretraining_exposure']['datasets'][i]['status'] == 'unknown', f'{t}: exposure')
    check({k for b in served['blocks'] for k in b['caveat_keys']} == set(LIMITATION_IDS)
          and [x['id'] for x in served['limitations']] == LIMITATION_IDS, 'the limitations changed')
    check([x['protocol'] for x in served['protocols_not_run']] == NOT_RUN, 'another list of protocols not run')
    # model identity
    ct, hf, gh = md['contract'], md['weightsListing'], md['codeListing']
    mo = served['model']
    fm = next(x for x in ct['artifacts'] if x['rfilename'] == ct['minimum_acquisition']['file'])
    check(mo['checkpoint']['sha256'] == fm['lfs']['sha256'] == rs['backbone']['strictLoad']['checkpoint_sha256']
          == md['download']['sha256'] and mo['checkpoint']['revision'] == ct['weights_revision'] == hf['sha']
          and mo['source_revision'] == ct['code_revision'] and mo['repository'] == gh['html_url']
          and mo['checkpoint']['repository'] == f'https://huggingface.co/{hf["id"]}'
          and mo['checkpoint']['file'] == fm['rfilename'], 'another model')
    check(f'arxiv:{mo["arxiv_id"]}' in hf['tags'] and mo['arxiv_id'] in ct['paper']
          and mo['paper'] == f'https://arxiv.org/abs/{mo["arxiv_id"]}', 'another paper')
    check(mo['variant'] == 'the released backbone with parameter-free branch normalisation and mean-token pooling',
          'another variant wording')
    ex = served['pretraining_exposure']
    check(ex['status'] == 'unknown' and ex['checked_on'] == ct['checked_on'], 'the exposure is not the contract’s')
    # rights
    r = served['rights']
    title = s['licence_bytes'][0].decode('utf-8').splitlines()[0].strip()
    check(title == 'Attribution-NonCommercial 4.0 International' and r['code']['licence'] == r['weights']['licence']
          == 'CC BY-NC 4.0' and r['code']['licence_title'] == r['weights']['licence_title'] == title,
          'the licences are not the licence files’')
    check(r['code']['url'] == f'{gh["html_url"]}/blob/{ct["code_revision"]}/LICENSE'
          and r['weights']['url'] == f'https://huggingface.co/{hf["id"]}/blob/{ct["weights_revision"]}/LICENSE',
          'the licence links name other revisions')
    receipts = {x['file']: x for x in md['licenceReceipts']}
    check(r['code']['checked_on'] == receipts['LICENSE']['checked'] == r['weights']['checked_on']
          == receipts['hf_LICENSE.txt']['checked'], 'another check date')
    for t in ORDER:
        tr = track(s, t)
        rec = r['datasets'][t]
        check(rec['name'] == tr['dataset'], f'{t}: the rights record names another dataset')
        for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt',
                  'reviewBasis', 'rightsScope'):
            check(rec[k] == tr[k], f'{t}: the rights record is not the released one ({k})')
    # provenance and release record
    pv, mr = served['provenance'], manifest['research']
    check(pv['source_export_sha256'] == {t: mr[t]['audit']['sha256'] for t in ORDER}
          and pv['release_approval_sha256'] == {t: mr[t]['approval']['sha256'] for t in ORDER}
          and pv['handoff_sha256'] == {t: mr[t]['handoff']['sha256'] for t in ORDER}
          and pv['protocol_sha256'] == {t: mr[t]['protocol']['sha256'] for t in ORDER}
          and pv['released_files_unchanged'] == [Path(x['path']).name for x in manifest['published'].values()],
          'provenance differs')
    check(served['release_record']['research_release_status'] == {t: rs[t]['approval']['status'] for t in ORDER}
          and all(v == 'PASS_INTERNAL_AGGREGATE_HANDOFF' for v in served['release_record']['research_release_status'].values()),
          'another research release status')
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


def string_leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from string_leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from string_leaves(v, trail + (i,))
    elif isinstance(value, str):
        yield trail, value


def text_digest(served):
    """The SHA-256 of every string in the served file outside provenance: a compact JSON list of [path, text] pairs in
    file order, UTF-8. Any changed, added, removed or moved text changes it."""
    pairs = [['/'.join(map(str, t)), v] for t, v in string_leaves(served) if t[0] not in TEXT_EXCLUDED]
    return digest(json.dumps(pairs, ensure_ascii=False, separators=(',', ':')).encode())


def plain(x):
    """A number as the texts print it: 44.5 stays 44.5, 50.0 becomes 50."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def prose_figures(served, E):
    """The figures the reader-visible texts quote are the ones this audit derived from the sources."""
    lim = {x['id']: x['text'] for x in served['limitations']}
    word = {v: k.lower() for k, v in COUNT_WORDS.items()}
    m, ec = ('model',), ('blocks', 0, 'input_chain')
    dim = E[m + ('pooling', 'dimension')]
    arm = lambda i, j: E[('blocks', i, 'arms', j, 'dimension')]
    notches = [plain(E[ec + ('notch_hz', j)]) for j in range(sum(1 for k in E if k[:4] == ec + ('notch_hz',)))]
    hz = E[ec + ('sampling_hz',)]
    check(E[('blocks', 1, 'input_chain', 'sampling_hz')] == E[('blocks', 2, 'input_chain', 'sampling_hz')] == hz,
          'the chains reach different rates')
    want = {
        'variant': [f'{E[m + ("restore", "trained_tensors")]} trained tensors restore strictly',
                    f'the {word[E[m + ("pooling", "branches")]]} {E[m + ("pooling", "branch_width")]}-value branches '
                    f'joined into {dim} values',
                    f'{word[E[m + ("authors_wrapper", "missing_normalisation_tensors")]]} normalisation tensors'],
        'transfer': [f'alpha {E[("probe", "alpha")]}'],
        'exposure': [f'list of {E[("pretraining_exposure", "published_pretraining_list", "corpora")]} pretraining '
                     f'corpora'],
        'input-eegmat': [f'the first {E[("blocks", 0, "cohort", "retained_seconds")]} seconds',
                         f'notches at {", ".join(notches[:-1])} and {notches[-1]} Hz',
                         f'{plain(E[ec + ("band_pass_hz", 0)])}–{plain(E[ec + ("band_pass_hz", 1)])} Hz band-pass',
                         f'±{E[ec + ("clip_microvolts",)]} µV',
                         f'from {E[ec + ("source_sampling_hz",)]} to {hz} Hz'],
        'input-cache': [f'from {E[("blocks", 1, "input_chain", "source_sampling_hz")]} and '
                        f'{E[("blocks", 2, "input_chain", "source_sampling_hz")]} Hz to {hz} Hz'],
        'dimensions': [f'NeuroRVQ’s {dim} values against {arm(0, 1)} band powers on EEGMAT, {arm(1, 1):,} temporal '
                       f'means and {arm(1, 2)} band powers on motor imagery, and {arm(2, 1)} temporal means on P300'],
        'p300-windows': [f'{E[("blocks", 2, "cohort", "balance", "target")]} target and '
                         f'{E[("blocks", 2, "cohort", "balance", "non_target")]} non-target epochs per person'],
        'interval': [f'{round(100 * E[("interval", "level")])}% interval from {E[("interval", "resamples")]:,} paired '
                     f'participant resamples'],
    }
    for lid, phrases in want.items():
        for phrase in phrases:
            check(phrase in lim[lid], f'{lid}: the text does not quote {phrase!r}')
    people = [E[('blocks', i, 'cohort', 'people')] for i in range(len(ORDER))]
    check(f'alpha {E[("probe", "alpha")]}' in served['scope'] and f'{dim} pooled values' in served['scope']
          and f'{people[0]} people on EEGMAT, {people[1]} on motor imagery against rest and {people[2]} on P300'
          in served['scope'], 'scope: the text quotes other figures')
    for i, b in enumerate(served['blocks']):
        for j, a in enumerate(b['arms']):
            d = E[('blocks', i, 'arms', j, 'dimension')]
            check(a['definition'].endswith(f'joined into {d} values') if a['id'] == 'neurorvq'
                  else a['definition'].startswith(f'{d:,} '), f'{b["id"]} {a["id"]}: the definition quotes another size')
        boundary = b['audit']['boundary']
        check(f'all {E[("blocks", i, "audit", "heads_refit")]} heads' in boundary
              and f'all {E[("blocks", i, "audit", "held_out_outputs_reproduced")]:,} held-out predictions' in boundary,
              f'{b["id"]}: the audit boundary quotes other counts')


def what_was_done(s, served, E):
    """Three statements of the texts about what was done, held to the pinned records read here."""
    lim = {x['id']: x['text'] for x in served['limitations']}
    e = s['research']['eegmat']
    # the EEGMAT filter runs over the retained first minute of each recording as one block
    seconds, rate = e['protocol']['input']['seconds_per_record'], e['headerSummary']['sampling_hz']
    check(seconds == E[('blocks', 0, 'cohort', 'retained_seconds')] == 60
          and e['protocol']['adapter']['filter_record_extent'].startswith(
              f'First {seconds * rate} native samples only, independently per recording, before windowing')
          and 'filters the retained first minute of each recording as one block before cutting it into windows'
          in lim['scope'], 'scope: the text describes another filtering extent')
    # the P300 cache's original preparation from the raw files was not re-run
    caveats = ' '.join(s['research']['p300-target']['audit']['caveats'])
    check('historical runtime not independently reconstructed' in caveats
          and 'the P300 cache’s original preparation from the raw files was not re-run' in lim['units'],
          'units: the text describes the P300 cache’s preparation otherwise')
    # the EEGMAT audit read both arms' values from the producer's sealed files and re-extracted neither
    prog = e['auditProgram']
    loads = re.search(r"for method,width in \[\('(\w+)',(\d+)\),\('(\w+)',(\d+)\)\]:\s*"
                      r"x=np\.load\(root/\(method\+'\.npy'\),allow_pickle=False\)", prog)
    check(loads is not None and 'sealed artifact' in prog and 'import torch' not in prog, 'eegmat: the audit program '
                                                                                          'reads its values otherwise')
    read = {loads.group(1): int(loads.group(2)), loads.group(3): int(loads.group(4))}
    keys = {a[3]: j for j, a in enumerate(ARMS['eegmat'])}
    check(set(read) == set(keys) == set(e['audit']['methods'])
          and all(read[k] == E[('blocks', 0, 'arms', j, 'dimension')] for k, j in keys.items())
          and E[('blocks', 0, 'audit', 'backbone_values_reextracted')] is False
          and all(f"'{x}'" in prog for x in e['audit']['limitations'])
          and served['blocks'][0]['audit']['boundary'].endswith(
              'it read both arms’ values from the producer’s sealed files and did not re-extract them.'),
          'eegmat: the audit boundary describes another reach')


def private_names(s):
    blob = json.dumps(s['research']['eegmat']['protocol'])
    names = {x for pair in re.findall(r'/(?:home|mnt)/([^/"\s]+)/([^/"\s]+)/', blob) for x in pair}
    h = s['research']['eegmat']['handoff']
    for pattern in (r'tests passed on (\w+) after', r'change, (\w+) access or source deletion'):
        names |= set(re.findall(pattern, h))
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Measured compute and the above-50% counts, never published."""
    rs = s['research']
    out = set()
    for t in ORDER:
        out |= {float(x) for x in re.findall(r'(\d+\.\d+)\s*(?:wall |CPU )?seconds', rs[t]['handoff'])}
    e = rs['eegmat']['audit']
    for m in e['methods'].values():
        out |= {m['above_chance_count'], m['above_chance_fraction']}
    out |= {e['elapsed_seconds'], *e['terminal_budgets'].values()}
    for d in (rs['mi-rest']['audit'], rs['mi-rest']['neuralAudit'], rs['p300-target']['audit']):
        out |= {v for k, v in d.items() if isinstance(v, (int, float)) and re.search(r'seconds|RSS|unix', k)}
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
        if path[0] == 'blocks' and [k for k in path if isinstance(k, str)][-1] in copied_keys:
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
    check(len(private) >= 4, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}', text_blob, re.I) is None,
              'a private user, host or volume name reached the served file')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')
    check(re.search(r'eugenehp|apache', text_blob, re.I) is None, 'the third-party conversion reached the served file')

    prose_figures(served, E)
    what_was_done(s, served, E)
    reviewed = manifest.get('reviewedText') or {}
    check(reviewed.get('excludes') == list(TEXT_EXCLUDED), 'the manifest records no reviewed text')
    text_sha = text_digest(served)
    check(text_sha == reviewed.get('sha256'), 'a text differs from the reviewed text the manifest pins: review the change '
                                              f'and record its SHA-256 ({text_sha}) there')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_neurorvq_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins. The scores, differences and intervals are '
                         'the study audit receipts’ values, the only full-precision record, and must also match the '
                         'figures each interpretation review checked and each handoff prints. Every other figure is '
                         'derived by its own reading: restore counts from the prospective protocols and the approval’s '
                         'gate name, cohorts from the header summary and the released core tracks, resampling ratios '
                         'and dimensions from the protocols’ text, the EEGMAT core rate from the released NeuroLM '
                         'panel, and the exposure counts from the contract’s corpus list.'),
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed, 'nulls_kept': nulls,
        'reviewed_text_sha256': text_sha,
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'scores, paired differences and intervals equal the study audit receipts and round to the figures the '
            'interpretation reviews checked and the handoffs print',
            'restore counts, pooled size, cohorts, resampling ratios, dimensions, fits, audit coverage and exposure '
            'counts are recomputed from the protocols, queues, header summary, released core tracks and contract',
            'labels, readings, licences, licence links, the released dataset records, hashes, caveat keys and the '
            'not-published list are checked as strings',
            'the figures the limitation texts, the scope, the arm definitions and the audit boundaries quote equal the '
            'figures derived here',
            'the EEGMAT filtering extent, the P300 cache’s unrepeated preparation and the EEGMAT audit’s reach, as the '
            'texts state them, follow from the protocol, the P300 receipt and the EEGMAT audit program',
            'every text in the file outside provenance, added keys included, hashes to the reviewed text the manifest '
            'pins',
            'no measured compute, no above-50% count, no private path, no private user, host or volume name and no '
            'third-party conversion in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'each study’s audit receipt, handoff and interpretation review: pinned in the manifest and bound by the '
                'study’s release approval, which the export checks',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
                'the reader-visible text: bound as a whole to the SHA-256 the manifest records for the reviewed text, '
                'and its quoted figures to the figures derived here',
            ],
            'not_bound': [
                'the extracted values themselves: the EEGMAT audit read both arms’ values from the producer’s sealed '
                'files without re-extracting them; this audit opens no sealed file',
                'the wording itself: the export’s text rules check claims, hedges, labels and names; this audit only '
                'holds the text to the reviewed bytes',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
