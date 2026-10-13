"""Independent audit of eegpt-core-update.json: every figure in the served file against the pinned sources.

A separate program from export_eegpt_core_update.py. It shares no code with that export and imports nothing from it:
it reads the served bytes, the release manifest and the files the manifest pins, builds its own table of what every
number, flag and null in the served file must be, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- the accuracy cells are read from where the export does not read them: the run audits' own recomputed metrics
  (parallel batch: the per-model metric check; BETA: the audit's recomputed comparison), and equal every other
  recorded copy (the run summary, the batch state, the public BETA summary, the review's read-only verification);
  idle's counts from its audit's recomputed aggregate and its window metrics from the independent recomputation;
- derived figures are recomputed here: chance flags, the percent blocks, the comparison gaps and relations against the
  published rows, the attribution random-initialisation means and differences, the pooled dimension, the patch
  counts and every footnote fact, from the pinned protocols, runner code, encoder source, pretraining script and paper;
- the attribution rows carry the published LaBraM and CBraMod rows' strings and the public audit's values; the rights
  blocks are the released core tracks' records; the model block names the checkpoint the reassessment names;
- the two served copies are one, the served file names the manifest it was built from, and no per-person value, no
  per-seed random-initialisation score, no duration-group summary and no private host or volume name is in it.

    python3 pipeline/publication/audit_eegpt_core_export.py
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261013'
MANIFEST = REVIEW / 'eegpt-core-release-manifest.json'
AUDIT = REVIEW / 'eegpt-core-export-audit.json'
SERVED = (PROJECT / 'site/src/data/eegpt-core-update.json', PROJECT / 'site/public/data/eegpt-core-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"
ENCODER_HZ = 256  # EEGPT's input rate, read from the paper below


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


def text(ref):
    return raw(ref).decode('utf-8')


def squash(s):
    return re.sub(r'\s+', ' ', s).strip()


def pct(v):
    return round(100 * v, 12)


def same_number(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    return type(a) is type(b) and a == b


# ---------------------------------------------------------------------------- what the sources say
def sources(manifest):
    s = {'manifest': manifest}
    s['mvp'] = doc(manifest['published']['coreMatrix'])
    s['topics'] = doc(manifest['published']['deploymentTopics'])
    s['pilot'] = doc(manifest['published']['pilotStudies'])
    s['fm'] = doc(manifest['published']['foundationModels'])
    s['runs'] = {}
    for p, run in manifest['runs'].items():
        if p == 'note':
            continue
        s['runs'][p] = {k: (text(r) if r['path'].endswith('.py') else doc(r)) for k, r in run.items()}
        s['runs'][p]['sha'] = {k: r['sha256'] for k, r in run.items()}
    s['batch'] = doc(manifest['batchState'])
    s['beta_public'] = doc(manifest['publicRecords']['betaSummary'])
    s['attr'] = doc(manifest['publicRecords']['attributionAudit'])
    s['code'] = {k: text(r) for k, r in manifest['code'].items()}
    s['paper'] = squash(text(manifest['paper']['text']))
    rv = manifest['review']
    s['core_ver'] = doc(rv['coreVerification'])
    s['idle_ver'] = doc(rv['idleVerification'])
    s['indep'] = doc(rv['independentRecomputation'])
    s['proposal'] = doc(rv['exposureProposal'])
    s['reassess'] = doc(manifest['rights']['reassessment'])
    s['terms'] = doc(manifest['rights']['checkpointTerms'])
    return s


def protocol_order(mvp):
    return [t['id'] for t in mvp['tracks']]


def channel_names(source, opener):
    m = re.search(opener + r'(.*?)\]', source, re.S)
    check(m is not None, f'no channel list after {opener!r}')
    return [n.upper() for n in re.findall(r"""['"]([A-Za-z0-9]+)['"]""", m.group(1))]


def accuracy_cells(s):
    """Each accuracy cell from its run audit's recomputation, required equal to every other recorded copy."""
    tracks = {t['id']: t for t in s['mvp']['tracks']}
    batch = {(d['dataset'], r['model']): r for d in s['batch']['datasets'] for run in d['runs'] for r in run['results']}
    cells = {}
    for p, run in s['runs'].items():
        if p == 'idle':
            continue
        t = tracks[p]
        check(run['sha']['audit'] == t['auditSha'] and run['sha']['summary'] == t['summarySha'],
              f'{p}: the manifest pins another run than the core track publishes')
        if 'datasetProtocol' in run:          # the parallel batch
            check(run['sha']['datasetProtocol'] == t['protocolSha'], f'{p}: another dataset protocol')
            audit, summary, dp, ep = run['audit'], run['summary'], run['datasetProtocol'], run['engineProtocol']
            checks = {c['name']: c for c in audit['checks']}
            m, cov = checks['eegpt.per_subject_metrics_and_ci'], checks['eegpt.prediction_coverage']
            f1 = next(x for x in audit['models'] if x['model'] == 'eegpt')['subject_mean_macro_f1']
            check(m['status'] == 'pass' and cov['status'] == 'pass' and audit['status'] == 'pass', f'{p}: audit')
            c = {'ba': m['subject_mean_balanced_accuracy'], 'ci': m['descriptive_subject_bootstrap_95'], 'f1': f1,
                 'people': m['participants'], 'trials': cov['samples'], 'classes': cov['classes'],
                 'channels': len(dp['channels']), 'window': int(dp['window_seconds']), 'seed': ep['seed'],
                 'source_hz': dp['sfreq'], 'replay': checks['eegpt.ridge_head_replay_and_train_only_scaler'][
                     'max_abs_replay_score_error'], 'ridge_alpha': ep['ridge']['alpha'],
                 'canonical': ep['native_to_canonical']}
            sres = next(r for r in summary['results'] if r['model'] == 'eegpt')
            bres = batch[(dp['dataset_id'], 'eegpt')]
            for other in (sres, bres):
                check(other['subject_mean_balanced_accuracy'] == c['ba'] and other['subject_mean_macro_f1'] == c['f1']
                      and other['descriptive_subject_bootstrap_95'] == c['ci'], f'{p}: a recorded copy differs')
            draws = re.search(r'boot=ba\[rng\.integers\(0,len\(ba\),\((\d+),len\(ba\)\)\)\]', s['code']['parallelRunner'])
            check(draws is not None and f'SEED={c["seed"]}' in s['code']['parallelRunner'], f'{p}: bootstrap settings')
            c['draws'] = int(draws.group(1))
        else:                                 # BETA
            check(run['sha']['protocol'] == t['protocolSha'], f'{p}: another BETA protocol')
            montage = t['protocolId'].rsplit('/', 1)[1]
            audit, proto = run['audit'], run['protocol']
            a = next(x for x in audit['comparisons'] if x['comparison'] == f'{montage}/eegpt')
            check(a['status'] == 'passed' and audit['all_passed'] is True, f'{p}: BETA audit')
            boot = proto['metrics']['bootstrap']
            draws, seed = re.search(r'(\d+) draws', boot), re.search(r'seed(\d+)', boot)
            ep = proto['preprocessing']['epoch_seconds_relative_to_stimulus_onset']
            c = {'ba': a['subject_mean_balanced_accuracy_recomputed'], 'ci': a['participant_bootstrap_95_recomputed'],
                 'f1': a['subject_mean_macro_f1_recomputed'], 'people': proto['dataset']['participants'],
                 'trials': a['predictions'], 'classes': proto['dataset']['classes'],
                 'channels': len(proto['montages'][montage]), 'window': ep[1] - ep[0], 'seed': int(seed.group(1)),
                 'draws': int(draws.group(1)), 'replay': None, 'montage': proto['montages'][montage]}
            for other in [r for r in run['summary']['results'] + s['beta_public']['results']
                          if r['model'] == 'eegpt' and r['montage'] == montage]:
                check(other['subject_mean_balanced_accuracy'] == c['ba'] and other['subject_mean_macro_f1'] == c['f1']
                      and other['descriptive_subject_bootstrap_95_percentile'] == c['ci'], f'{p}: a recorded copy differs')
        v = s['core_ver']['core_cells'].get(p)
        if v:
            check(v['balanced_accuracy'] == c['ba'] and v['bootstrap_95'] == c['ci'] and v['macro_f1'] == c['f1'],
                  f'{p}: the read-only verification differs')
        c['chance'] = t['chanceLevel']
        cells[p] = c
    return cells


def idle_cell(s):
    run = s['runs']['idle']
    t = next(x for x in s['mvp']['tracks'] if x['id'] == 'idle')
    check(run['sha']['audit'] == t['auditSha'] and run['audit']['passed'] is True, 'idle: not the published audit')
    a = next(x for x in run['audit']['output']['aggregate_counts_recomputed'] if x['model'] == 'EEGPT')
    sm = next(x for x in run['summary']['aggregate'] if x['model'] == 'EEGPT')
    check(all(sm[k] == a[k] for k in a), 'idle: the summary and its audit differ')
    ind = s['indep']['results']['idle']
    check(ind['counts'] == {'idle_false': a['idle_false_trigger_trials'], 'mi_detected': a['mi_detected_trials'],
                            'always_abstain': a['always_abstain_subjects']}, 'idle: the independent counts differ')
    iv = s['idle_ver']['eegpt_idle_result']
    check(iv['window_balanced_accuracy'] == ind['window_balanced_accuracy'] and iv['window_auroc'] == ind['window_auroc'],
          'idle: the two recomputations differ')
    check(abs(ind['window_auroc'] - ind['auroc_x_8100'] / ind['pairs_total']) < 1e-15, 'idle: AUROC is not pairs/8100')
    names = channel_names(run['models'], r'CHANNELS\s*=\s*\[')
    proto = run['protocol']
    c_value = re.search(r'C=([0-9.]+)', proto['frozen_encoder_heads']['classifier'])
    same, other = [], []
    for row in t['rows']:
        (same if row['name'] in {x['model'] for x in run['summary']['aggregate']} else other).append(row['id'])
    return {'people': a['subjects'], 'idle_false': a['idle_false_trigger_trials'], 'idle_trials': a['idle_trials'],
            'detected': a['mi_detected_trials'], 'command_trials': a['mi_trials'], 'abstain': a['always_abstain_subjects'],
            'window_ba': ind['window_balanced_accuracy'], 'window_auroc': ind['window_auroc'], 'channels': len(names),
            'window': proto['windows']['duration_seconds'], 'logistic_c': float(c_value.group(1)),
            'same': same, 'other': other}


def encoder(s):
    m = re.search(r'EEGTransformer\(img_size=\[n,512\], patch_size=(\d+), embed_num=(\d+), embed_dim=(\d+),\s*depth=(\d+), '
                  r'num_heads=(\d+)', s['code']['betaRunner'])
    check(m is not None, 'the encoder builder is not in the pinned runner')
    patch, tokens, dim, depth, heads = map(int, m.groups())
    paper = s['paper']
    check(f'Each patch has a time length of d = {patch}, corresponding to a 250ms time window' in paper
          and f'sampling rate of fs = {ENCODER_HZ} Hz' in paper, 'the paper states another patch or rate')
    win = re.search(r'cropping \((\d+)s\), re-referencing \(average\)', paper)
    elec = re.search(r'We used (\d+) electrodes', paper)
    dictionary = channel_names(s['code']['encoderSource'], r'CHANNEL_DICT = \{k\.upper\(\):v for v,k in enumerate\(\s*\[')
    pretrain = channel_names(s['code']['pretrainingScript'], r'use_channels_names = \[')
    check(int(elec.group(1)) == len(pretrain), 'the paper and the pretraining script name other electrode counts')
    return {'patch': patch, 'tokens': tokens, 'dim': dim, 'depth': depth, 'heads': heads,
            'pretrain_window': int(win.group(1)), 'dictionary': dictionary, 'pretrain': pretrain}


# ---------------------------------------------------------------------------- the expected table
def expected_table(s, served):
    E = {}
    order = protocol_order(s['mvp'])
    tracks = {t['id']: t for t in s['mvp']['tracks']}
    acc = accuracy_cells(s)
    idle = idle_cell(s)
    enc = encoder(s)
    mvp_eegpt = next(m for m in s['mvp']['models'] if m['name'] == 'EEGPT')

    # model
    E[('model', 'encoder_parameters')] = mvp_eegpt['parameters']
    arch = {'patch_samples': enc['patch'], 'patch_seconds': enc['patch'] / ENCODER_HZ, 'encoder_sampling_hz': ENCODER_HZ,
            'embed_dim': enc['dim'], 'depth': enc['depth'], 'heads': enc['heads'], 'summary_tokens': enc['tokens'],
            'pooled_dimension': enc['tokens'] * enc['dim']}
    for k, v in arch.items():
        E[('model', 'architecture', k)] = v
    E[('model', 'weights_licence')] = NULL
    E[('model', 'weights_distributed')] = False
    E[('model', 'pretraining', 'electrodes')] = len(enc['pretrain'])
    E[('model', 'pretraining', 'channel_dictionary')] = len(enc['dictionary'])
    E[('model', 'pretraining', 'window_seconds')] = enc['pretrain_window']
    E[('model', 'pretraining', 'sampling_hz')] = ENCODER_HZ

    # protocols and cells
    for i, p in enumerate(order):
        t = tracks[p]
        c = idle if p == 'idle' else acc[p]
        chance = None if t['chanceLevel'] is None else t['chanceLevel'] / 100
        E[('protocols', i, 'people')] = c['people']
        E[('protocols', i, 'channels')] = c['channels']
        E[('protocols', i, 'window_seconds')] = c['window']
        E[('protocols', i, 'chance_level')] = NULL if chance is None else chance
        if p == 'sleep-scalp':
            E[('protocols', i, 'segments', 'count')] = c['window'] // 2
            E[('protocols', i, 'segments', 'each_seconds')] = 2
        base = ('cells', i)
        if p == 'idle':
            for k, v in (('people', c['people']), ('channels', c['channels']), ('idle_false_activations', c['idle_false']),
                         ('idle_trials', c['idle_trials']), ('commands_detected', c['detected']),
                         ('command_trials', c['command_trials']), ('always_abstain_people', c['abstain']),
                         ('window_balanced_accuracy', c['window_ba']), ('window_auroc', c['window_auroc'])):
                E[base + (k,)] = v
            E[base + ('interval',)] = NULL
            E[base + ('percent', 'idle_false_activation')] = pct(c['idle_false'] / c['idle_trials'])
            E[base + ('percent', 'command_detection')] = pct(c['detected'] / c['command_trials'])
            E[base + ('percent', 'window_balanced_accuracy')] = pct(c['window_ba'])
        else:
            lo, hi = c['ci']
            for k, v in (('balanced_accuracy', c['ba']), ('macro_f1', c['f1']), ('people', c['people']),
                         ('trials', c['trials']), ('classes', c['classes']), ('channels', c['channels']),
                         ('chance_level', chance)):
                E[base + (k,)] = v
            E[base + ('interval_95', 0)], E[base + ('interval_95', 1)] = lo, hi
            E[base + ('interval_includes_chance',)] = lo <= chance <= hi
            E[base + ('at_or_below_chance',)] = c['ba'] <= chance
            E[base + ('interval', 'level')] = 0.95
            E[base + ('interval', 'draws')] = c['draws']
            E[base + ('interval', 'seed')] = c['seed']
            E[base + ('percent', 'balanced_accuracy')] = pct(c['ba'])
            E[base + ('percent', 'interval_95', 0)] = pct(lo)
            E[base + ('percent', 'interval_95', 1)] = pct(hi)
            E[base + ('percent', 'chance_level')] = t['chanceLevel']

    # footnote facts, each from the pinned protocols, code and paper
    pw = enc['pretrain_window']
    one_s = sorted(p for p in order if p != 'idle' and acc.get(p, {}).get('window') == 1)
    check(one_s == ['p300-target', 'semantic-target'], 'the one-second protocols are not P300 and semantic target')
    check("model.num_patches=(len(names),4);model.patch_embed.num_patches=(len(names),4)" in s['code']['parallelRunner'],
          'the one-second patch grid is not in the pinned runner')
    unused = [n for n in enc['dictionary'] if n not in enc['pretrain']]
    beta8 = acc['beta-8ch']['montage']
    sleep_w = acc['sleep-scalp']['window']
    canonical = int(re.search(r'to(\d+)Hz', acc['mi-rest']['canonical']).group(1))
    non_sleep = sorted({(idle if p == 'idle' else acc[p])['window'] for p in order if p != 'sleep-scalp'})
    pilot_in = s['pilot']['results']['orthosis-eegpt-vs-58ch']['encoder_input']
    check(pilot_in['sampling_hz'] == ENCODER_HZ, 'the pilot encoder ran at another rate')
    facts = {
        'one-second-patch-grid': {'window_seconds': 1, 'patches': ENCODER_HZ // enc['patch'], 'patch_samples': enc['patch'],
                                  'encoder_sampling_hz': ENCODER_HZ, 'padding': False,
                                  'equivalent_input_samples': ENCODER_HZ,
                                  # the Orthosis pilot's own encoder input length, from the released pilot file
                                  'pilot_input_samples': pilot_in['samples']},
        'untrained-channel-embeddings': {'dictionary_names': len(enc['dictionary']),
                                         'pretraining_electrodes': len(enc['pretrain'])},
        'tsinghua-benchmark-context': {'exposure_status_unchanged': True},
        'shorter-than-pretraining': {'pretraining_window_seconds': pw, 'sleep_segments': sleep_w // 2,
                                     'sleep_segment_seconds': 2, 'patch_seconds': enc['patch'] / ENCODER_HZ},
        'fixed-readout': {'ridge_alpha': int(acc['mi-rest']['ridge_alpha']), 'pooled_dimension': enc['tokens'] * enc['dim'],
                          'idle_logistic_c': idle['logistic_c'], 'average_reference': False},
        'source-rate': {'source_sampling_hz': int(acc['mi-rest']['source_hz']), 'canonical_sampling_hz': canonical,
                        'encoder_sampling_hz': ENCODER_HZ, 'highest_frequency_hz': acc['mi-rest']['source_hz'] / 2},
    }
    check(max(non_sleep) < pw and 2 < pw, 'a core window is not shorter than the pretraining window')
    strings_expected = {
        'untrained-channel-embeddings': {'unused_in_pretraining': unused,
                                         'channels_affected': [n for n in beta8 if n in unused]},
        'shorter-than-pretraining': {'core_window_seconds': non_sleep},
        'idle-run': {'same_run_rows': idle['same'], 'other_run_rows': idle['other']},
    }
    for j, f in enumerate(served['footnotes']):
        for k, v in facts.get(f['id'], {}).items():
            E[('footnotes', j, 'facts', k)] = v
        for k, v in strings_expected.get(f['id'], {}).items():
            if all(isinstance(x, int) for x in v):
                for n, x in enumerate(v):
                    E[('footnotes', j, 'facts', k, n)] = x
            else:
                check(f['facts'].get(k) == v, f'footnote {f["id"]}: {k} differs from the pinned sources')

    # comparisons against every published row
    scored = [p for p in order if p != 'idle']
    for k, p in enumerate(scored):
        lo, hi = pct(acc[p]['ci'][0]), pct(acc[p]['ci'][1])
        rows = served['comparisons']['protocols'][k]['rows']
        check(served['comparisons']['protocols'][k]['protocol'] == p
              and [r['row'] for r in rows] == [r['id'] for r in tracks[p]['rows']], f'{p}: the comparison rows differ')
        for m, r in enumerate(tracks[p]['rows']):
            r_lo, r_hi = r['interval']
            if lo > r_hi:
                rel, gap = 'above', round(lo - r_hi, 12)
            elif hi < r_lo:
                rel, gap = 'below', round(r_lo - hi, 12)
            else:
                rel, gap = 'overlap', NULL
            check(rows[m]['relation'] == rel and rows[m]['name'] == r['name'] and rows[m]['family'] == r['family'],
                  f'{p} against {r["id"]}: another relation')
            E[('comparisons', 'protocols', k, 'rows', m, 'gap_pp')] = gap
        gaps = {r['row']: E[('comparisons', 'protocols', k, 'rows', m, 'gap_pp')] for m, r in enumerate(rows)}
        apart = {row: g for row, g in gaps.items() if g is not NULL}
        sm = served['comparisons']['protocols'][k]['smallest_gap']
        if apart:
            least = min(apart.values())
            check(sm is not None and apart.get(sm['row']) == least, f'{p}: the smallest gap names another row')
            E[('comparisons', 'protocols', k, 'smallest_gap', 'gap_pp')] = least
        else:
            E[('comparisons', 'protocols', k, 'smallest_gap')] = NULL
        rel_lists = served['comparisons']['protocols'][k]['relations']
        check(rel_lists == {x: [r['row'] for r in rows if r['relation'] == x] for x in ('above', 'below', 'overlap')},
              f'{p}: the relation lists differ from the rows')

    # exposure counts
    statuses = [c['status'] for c in s['proposal']['cells']]
    for k in ('exposed', 'not_exposed', 'unknown'):
        E[('pretraining_exposure', 'counts', k)] = statuses.count(k)

    # attribution, from the public audit
    attr = s['attr']
    pk = {(x['dataset'], x['mode'], x['condition']): x for x in attr['packages']}
    con = {(x['dataset'], x['mode'], x['model']): x for x in attr['contrasts']}
    seeds = sorted(int(c.rsplit('-', 1)[1]) for (_, _, c) in pk if c.startswith('eegpt-random-'))
    seeds = sorted(set(seeds))
    track_of = {'pretraining-attribution-fixed': 'fixed', 'pretraining-attribution-selected': 'selected'}
    published = [r for r in s['topics']['rows'] if r['track'] in track_of]
    pc = [c for c in s['topics']['paired_contrasts'] if c['track'] in track_of]
    order_attr = [(c['dataset_id'], track_of[c['track']]) for c in pc if c['model'] == 'labram']
    for n, (ds, mode) in enumerate(order_attr):
        c = con[(ds, mode, 'eegpt')]
        pre = pk[(ds, mode, 'eegpt-pretrained')]
        rnd = [pk[(ds, mode, f'eegpt-random-{x}')] for x in seeds]
        check(abs(statistics.fmean(x['mean_balanced_accuracy'] for x in rnd) - c['random_mean_ba']) < 1e-12
              and abs(c['pretrained_ba'] - c['random_mean_ba'] - c['delta']) < 1e-12
              and pre['mean_balanced_accuracy'] == c['pretrained_ba'], f'{ds} {mode}: the audit does not add up')
        ref = next(r for r in published if r['dataset_id'] == ds and track_of[r['track']] == mode and r['model'] == 'labram'
                   and r['initialization'] == 'pretrained')
        for j, (init, value, count) in enumerate((('pretrained', c['pretrained_ba'], 1),
                                                  ('constructor-random-mean', c['random_mean_ba'], len(rnd)))):
            i = 2 * n + j
            row = served['pretraining_attribution']['rows'][i]
            for key in ('track', 'protocol_id', 'metric', 'training_regime', 'head_selection'):
                check(row[key] == ref[key], f'attribution row {i}: {key} is not the published rows’')
            check(row['dataset_id'] == ds and row['model'] == 'eegpt' and row['initialization'] == init,
                  f'attribution row {i}: another row')
            for key, v in (('value', value), ('confidence_interval_95', NULL), ('participants', pre['participants']),
                           ('trials', pre['trials']), ('encoder_seed_count', count)):
                E[('pretraining_attribution', 'rows', i, key)] = v
        sc = served['pretraining_attribution']['paired_contrasts'][n]
        refc = next(x for x in pc if x['dataset_id'] == ds and track_of[x['track']] == mode)
        for key in ('track', 'comparison', 'unit', 'interpretation'):
            check(sc[key] == refc[key], f'attribution contrast {n}: {key} is not the published contrasts’')
        check(sc['dataset_id'] == ds and sc['model'] == 'eegpt', f'attribution contrast {n}: another contrast')
        E[('pretraining_attribution', 'paired_contrasts', n, 'participants')] = pre['participants']
        E[('pretraining_attribution', 'paired_contrasts', n, 'difference')] = c['delta']
        for b in (0, 1):
            E[('pretraining_attribution', 'paired_contrasts', n, 'paired_participant_bootstrap_95', b)] = \
                c['paired_participant_bootstrap_95'][b]
    for n, x in enumerate(seeds):
        E[('pretraining_attribution', 'method', 'random_initialisation_seeds', n)] = x
    boot = re.search(r'np\.random\.default_rng\((\d+)\)\.integers\(0,len\(delta\),\((\d+),len\(delta\)\)\)',
                     s['code']['attributionAuditor'])
    E[('pretraining_attribution', 'method', 'bootstrap', 'draws')] = int(boot.group(2))
    E[('pretraining_attribution', 'method', 'bootstrap', 'seed')] = int(boot.group(1))

    # audits
    shas = list(dict.fromkeys(s['runs'][p]['sha']['audit'] for p in order))
    for k, a in enumerate(shas):
        p = next(q for q in order if s['runs'][q]['sha']['audit'] == a)
        E[('audits', 'runs', k, 'head_replay_max_error')] = (NULL if p == 'idle' or acc[p]['replay'] is None
                                                             else acc[p]['replay'])
    cv = s['core_ver']['summary']
    E[('audits', 'review_read_only_check', 'items')] = cv['checks']
    E[('audits', 'review_read_only_check', 'passed')] = cv['passed']

    # the pilot comparison: same checkpoint, outside every leaderboard
    pr = s['pilot']['results']['orthosis-eegpt-vs-58ch']
    E[('pilot_comparison', 'leaderboard')] = pr['leaderboard']
    E[('pilot_comparison', 'same_checkpoint')] = (pr['model']['checkpoint']['sha256']
                                                  == s['reassess']['checkpoint_identity']['original_sha256'])
    return E, acc, idle


# ---------------------------------------------------------------------------- string checks
def string_checks(s, served, acc, manifest):
    order = protocol_order(s['mvp'])
    tracks = {t['id']: t for t in s['mvp']['tracks']}
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['reviewed_at'],
          'another release')
    check([p['id'] for p in served['protocols']] == order and [c['protocol'] for c in served['cells']] == order,
          'the protocols are not in the core order')
    statement = f"not in the authors' published pretraining list (checked {s['proposal']['model']['checked_on']})"
    by_protocol = {p: c for c in s['proposal']['cells'] for p in c['protocols']}
    for i, p in enumerate(order):
        t, e, c = tracks[p], served['protocols'][i], served['cells'][i]
        check(e['title'] == t['title'] and e['dataset'] == t['dataset'] and e['protocol_id'] == t['protocolId']
              and e['type'] == t['type'], f'{p}: another protocol')
        run = s['runs'][p]['sha']
        check(e['run']['audit_sha256'] == t['auditSha'] == run['audit'] and e['run']['summary_sha256'] == run['summary'],
              f'{p}: another run named')
        rights = e['rights']
        for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt',
                  'reviewBasis', 'rightsScope'):
            check(rights[k] == t[k], f'{p}: the rights record is not the released one ({k})')
        check(rights['name'] == t['dataset'], f'{p}: the rights record names another dataset')
        ex = by_protocol[p]
        check(c['exposure'] == {'status': ex['status'], 'confidence': ex['confidence'], 'statement': statement}
              and c['model'] == 'eegpt' and c['status'] == 'complete', f'{p}: another exposure or status')
    m = served['model']
    ci = s['reassess']['checkpoint_identity']
    check(m['checkpoint']['sha256'] == ci['original_sha256'] and m['checkpoint']['file'] == ci['original_filename']
          and m['checkpoint']['tensor_conversion_sha256'] == ci['tensor_derivative_sha256'], 'another checkpoint')
    check(m['source_revision'] == manifest['code']['encoderSource']['revision']
          and m['paper'] == f'https://doi.org/{manifest["paper"]["doi"]}', 'another source or paper')
    check(s['terms']['resolved_checkpoint_license'] is None and m['code_licence'] == 'Apache-2.0'
          and 'unresolved' in m['weights_licence_status'], 'the licence fields changed')
    pv = served['provenance']
    check(pv['public_records_sha256'] == {'beta_summary': manifest['publicRecords']['betaSummary']['sha256'],
                                          'attribution_audit': manifest['publicRecords']['attributionAudit']['sha256']}
          and pv['run_summary_sha256'] == {p: s['runs'][p]['sha']['summary'] for p in order}, 'provenance differs')
    check(served['not_published'] == manifest['notPublished'], 'the not-published list is not the manifest’s')
    ids = [f['id'] for f in served['footnotes']]
    for c in served['cells']:
        check(set(c['footnotes']) <= set(ids) and c['footnotes'] == [f['id'] for f in served['footnotes']
                                                                      if c['protocol'] in f['protocols']],
              f'{c["protocol"]}: footnotes not attached as listed')
    check(served['directory_status']['released_status'] == next(x for x in s['mvp']['models'] if x['name'] == 'EEGPT')['status'],
          'another released directory status')


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
    blob = json.dumps([s['runs'][p]['audit'] for p in s['runs']]) + json.dumps(s['batch'])
    names = {x for pair in re.findall(r'/Volumes/([^/"\s]+)/([^/"\s]+)', blob) for x in pair}
    names |= set(re.findall(r'/(?:home|Users)/([^/"\s]+)/', blob))
    for d in s['batch']['datasets']:
        for r in d['runs']:
            names |= {x for x in re.split(r'[-_.]', r['environment']['host']) if len(x) >= 4 and re.search(r'\d', x)}
    return {n for n in names if len(n) >= 3}


def withheld(s):
    out = set()
    for r in s['runs']['idle']['summary']['results']:
        if r['model'] == 'EEGPT':
            out |= {r['idle_false_trigger_fraction'], r['mi_detection_fraction'],
                    r['descriptive_false_triggers_per_scripted_idle_minute']}
    for x in s['attr']['packages']:
        if x['condition'].startswith('eegpt-random-'):
            out.add(x['mean_balanced_accuracy'])
    for r in s['beta_public']['results']:
        if r['model'] == 'eegpt':
            out |= {r['short_duration_group_balanced_accuracy'], r['long_duration_group_balanced_accuracy']}
    for c in s['core_ver']['attribution_contrasts']:
        if c['model'] == 'eegpt':
            out |= set(c['random_seed_bas']) | {c['random_seed_sample_sd']}
    return out - {0.0, 0.2, 0.25, 0.5, 1.0}


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    s = sources(manifest)
    E, acc, idle = expected_table(s, served)
    string_checks(s, served, acc, manifest)

    found = dict(leaves(served))
    exact = recomputed_n = nulls = 0
    copied_keys = {'balanced_accuracy', 'macro_f1', 'interval_95', 'window_balanced_accuracy', 'window_auroc', 'value',
                   'difference', 'paired_participant_bootstrap_95'}
    for path, value in found.items():
        check(path in E, f'{"/".join(map(str, path))}: a figure with no audit rule')
        want = E[path]
        if want is NULL:
            check(value is None, f'{"/".join(map(str, path))}: a null became {value!r}')
            nulls += 1
            continue
        check(same_number(value, want), f'{"/".join(map(str, path))}: {value!r} where the sources give {want!r}')
        if any(k in copied_keys for k in path if isinstance(k, str)) and 'percent' not in path:
            exact += 1
        else:
            recomputed_n += 1
    missing = [p for p in E if p not in found]
    check(not missing, f'expected figures missing from the served file: {missing[:3]}')

    published = {v for _, v in found.items() if isinstance(v, float)}
    secret = withheld(s)
    check(not (secret & published), f'a withheld value reached the served file: {sorted(secret & published)[:3]}')
    text_blob = served_bytes[0].decode()
    private = private_names(s)
    check(len(private) >= 3, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text_blob, re.I) is None,
              'a private host or volume name reached the served file')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_eegpt_core_export.py',
        'independence': ('A separate program from the export, importing nothing from it. It reads the served bytes, the '
                         'release manifest and the files the manifest pins, and takes the accuracy cells from the run '
                         'audits’ own recomputations (the export reads the run summaries), idle’s counts from its '
                         'audit’s recomputed aggregate and its window metrics from the independent second '
                         'recomputation, and every derived figure from its own arithmetic on those.'),
        'protocols': protocol_order(s['mvp']),
        'figures_compared': len(E), 'copied_exactly': exact, 'recomputed': recomputed_n, 'nulls_kept': nulls,
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every run file is the one whose SHA-256 its core track publishes (summary, audit, dataset protocol)',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'accuracy cells equal the run audits’ recomputed metrics and every other recorded copy: the run summary, '
            'the batch state, the public BETA summary and the review’s read-only verification',
            'idle counts equal the run audit’s recomputed aggregate; its window metrics equal the independent '
            'recomputation, and the AUROC is a whole number of window pairs',
            'chance flags, percent blocks and every comparison gap and relation against the published rows are '
            'recomputed here',
            'attribution rows and contrasts: values from the public audit, random-initialisation means and differences '
            'recomputed from its packages, strings equal to the published LaBraM and CBraMod rows',
            'footnote facts from the pinned runner, encoder source, pretraining script, protocols and paper',
            'rights blocks are the released core tracks’ records; the checkpoint is the one the reassessment names',
            'no per-person value, per-seed random-initialisation score or duration-group summary, and no private host, '
            'volume or path, in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'run summaries, audits and dataset protocols: pinned in the manifest and equal to the SHA-256 the '
                'released core tracks publish',
                'public BETA summary and attribution audit: pinned in the manifest and named in the served provenance',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
            ],
            'not_bound': [
                'the per-file seals of the saved predictions are verified by the review’s read-only check, whose record '
                'is pinned; this audit does not open the saved predictions',
                'prose, the exposure evidence text and the release record are checked by the export, not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
