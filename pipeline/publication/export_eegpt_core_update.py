"""Release EEGPT's eight core-matrix cells and its pretraining-attribution rows, aggregate-only, beside the core matrix.

EEGPT ran in the same runs as the published LaBraM rows of all eight core protocols and, except on idle, the CBraMod
rows, with only the encoder swapped, and in the pretraining-attribution study on mi-rest (ds003810) and EEGMAT. Its scores were held while its
checkpoint's licence could not be read; the owner's decisions of 2026-10-12 and 2026-10-13 publish them as they were
computed, without a re-run (option A of the core review), as a frozen row beside the core matrix, the way the further
foundation encoders sit there, and its attribution rows beside the published LaBraM and CBraMod rows. Nothing released
changes: experiments.json, the protocol files, the results CSVs, deployment-topics.json and the further-encoder export
keep their bytes; a page that shows the new row next to a core row reads both files at build time.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- each accuracy cell from the run summary whose SHA-256 its core track already publishes (summarySha), and only if
  that run's independent audit (auditSha) passed with the same EEGPT values, the dataset protocol is the published one
  (protocolSha), and the same summary's LaBraM and CBraMod results are the published rows: the same run;
- idle's counts from its run summary's cohort aggregate, equal to that run's audit (the idle track's auditSha), and its
  window balanced accuracy and AUROC from the review's recomputation, equal to an independent second recomputation;
- the attribution rows and contrasts from the public attribution audit, in the published deployment-topics fields and
  with the strings of the published LaBraM and CBraMod rows of the same track and dataset;
- the exposure cells from the review's proposal, worded with the further-encoder formula; every footnote fact from the
  pinned runner code, encoder source, pretraining script, run protocols and paper.
The run summaries, protocols and audits are byte copies of the run root's files kept in the review's git-ignored
evidence folder: they carry private storage paths, so they are pinned and checked, never published.

What this export refuses:
- per-trial, per-person, per-fold and per-class values, thresholds, features, predictions, timings, devices and memory,
  by key and by fragment; the per-seed random-initialisation scores and BETA's duration-group summaries by value;
  private paths, host and volume names (read at run time from the pinned records that carry them, never spelled here);
- a cell from another run, an interval that does not hold its mean, a chance flag or relation the intervals do not
  support, a figure that is not the one the pinned records state;
- a version label, an update marker or a month used as a label in the text, Jev, the weights called Apache-2.0, and a
  claim these results do not support unless it is negated.

    python3 pipeline/publication/export_eegpt_core_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261013'
MANIFEST = REVIEW / 'eegpt-core-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'eegpt-core-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/eegpt-core-update.json',
           PROJECT / 'site/public/data/eegpt-core-update.json')
RELEASE_ID = 'eegpt-core-update-20261013'
SCHEMA = 'bci-report-eegpt-core-update-v1'
MODEL = 'eegpt'

PROTOCOLS = ('mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target', 'semantic-target', 'sleep-scalp')
SCORED = tuple(p for p in PROTOCOLS if p != 'idle')
PARALLEL = {'mi-rest': 'ds003810', 'arithmetic-rest': 'physionet-eegmat-1.0.0', 'p300-target': 'ds006593',
            'semantic-target': 'ds005383', 'sleep-scalp': 'eesm19-scalp-sleep'}
MONTAGE = {'beta-8ch': 'posterior8', 'beta-4ch': 'posterior4'}
EXPOSURE_DATASET = {'mi-rest': 'ds003810', 'idle': 'ds005342', 'beta-8ch': 'beta', 'beta-4ch': 'beta',
                    'arithmetic-rest': 'eegmat', 'p300-target': 'ds006593', 'semantic-target': 'ds005383',
                    'sleep-scalp': 'eesm19'}
ALIASES = {'T3': 'T7', 'T4': 'T8', 'T5': 'P7', 'T6': 'P8'}      # run_suite.py, before the channel dictionary
PRETRAINING_DATASETS = ('PhysioMI', 'HGD', 'TSU', 'SEED', 'M3CV')
ATTRIBUTION = (('ds003810', 'fixed'), ('ds003810', 'selected'), ('physionet-eegmat-1.0.0', 'fixed'),
               ('physionet-eegmat-1.0.0', 'selected'))
TRACK = {'fixed': 'pretraining-attribution-fixed', 'selected': 'pretraining-attribution-selected'}
RANDOM_SEEDS = (20260919, 20260920, 20260921)
CORE_DATE, EXPOSURE_CHECKED = '2026-09-20', '2026-10-12'
PAPER_DOI = '10.52202/079017-1239'
TOL = 1e-12

# Per-person distributions, a decoder's internals, timings, and what this release leaves out on purpose.
REFUSED_KEYS = PER_PERSON_KEYS | {
    'minimum', 'maximum', 'range', 'q1', 'q3', 'p10', 'p90', 'seconds', 'total_seconds', 'fit_and_predict_seconds',
    'score_invocation_seconds', 'scripted_idle_exposure_seconds', 'random_seed_bas', 'random_seed_sample_sd',
    'short_duration_group_balanced_accuracy', 'long_duration_group_balanced_accuracy', 'calibration_grid',
    'participants_with_negative_delta', 'checks', 'seal', 'source_files', 'splits'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_class', 'subject',
                         'prediction', 'probabilit', 'threshold', 'feature', 'confusion', 'percentile', 'quantile',
                         'median', 'elapsed', 'timing', 'wall', 'rss', 'memory', 'device', 'platform', 'environment',
                         'private', 'path', 'host', 'folder', 'duration_group', 'monte_carlo', 'sensitivity')
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
# Upstream participant names, raw-file extensions, and the private run records by name (the served files are named
# <protocol>-protocol.json and are allowed).
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\.(?:npz|npy|edf|mat)\b|(?<![\w-])(?:summary|independent-audit'
                        r'|dataset-protocol|engine-protocol|artifacts|batch-state|latest-batch-state)\.json', re.IGNORECASE)
TRIVIAL = {0.0, 0.2, 0.25, 0.5, 1.0}   # chance levels and fixed design values that per-person fractions can equal
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
CLAIMS = re.compile(r'\bonline\b|real-time|closed-loop|\bclinical\b|\bmedical\b|zero-shot|\bcausal|\bcaused\b'
                    r'|unseen pretraining|certified unseen|\bendorse|superior|equivalen|significan|state[- ]of[- ]the[- ]art'
                    r'|\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none)\b|n't\b", re.IGNORECASE)


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool)


def close(a, b, label, tol=TOL):
    require(number(a) and number(b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def percent(v):
    """A proportion in percent, as the core rows carry it: 100 x v, rounded to 12 decimals (as the further-encoder
    CSVs do), so a decimal tie prints as its decimal rounding and not as a binary artefact of the unit change."""
    return round(100 * v, 12)


def interval(iv, point, label, lo_bound=0.0, hi_bound=1.0):
    require(isinstance(iv, list) and len(iv) == 2 and all(number(v) for v in iv), f'{label}: no two-sided interval')
    require(lo_bound <= iv[0] <= point <= iv[1] <= hi_bound, f'{label}: the interval does not hold its point')
    return [iv[0], iv[1]]


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def stated(text, phrase, label):
    require(phrase in text, f'{label}: the pinned record does not state {phrase!r}')


def pct2(v):
    return f'{100 * v:.2f}'


def quoted_names(block):
    return [n.upper() for n in re.findall(r"""['"]([A-Za-z0-9]+)['"]""", block)]


def names_list(source, start_pattern, label):
    """A Python list literal of channel names in a pinned source file, from its assignment to the closing bracket."""
    m = re.search(start_pattern + r'(.*?)\]', source, re.S)
    require(m is not None, f'{label}: the list is not in the pinned source')
    return quoted_names(m.group(1))


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def floats(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from floats(v)
    elif isinstance(value, list):
        for v in value:
            yield from floats(v)
    elif isinstance(value, float):
        yield value


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {'review': {}, 'published': {}, 'runs': {}, 'public': {}, 'code': {}, 'rights': {}}
    rv = manifest['review']
    for k in ('coreVerification', 'idleVerification', 'independentRecomputation', 'exposureProposal'):
        docs['review'][k] = pinned(rv[k], k)[0]
    for k in ('memo', 'coreVerificationNotes', 'idleVerificationNotes', 'compatibilityAndRights', 'inventory'):
        docs['review'][k] = pinned_text(rv[k], k)
    for k, r in manifest['published'].items():
        docs['published'][k] = pinned(r, k)[0]
    for p in PROTOCOLS:
        run = manifest['runs'][p]
        docs['runs'][p] = {k: (pinned(r, f'{p} {k}') if k != 'models' else (pinned_text(r, f'{p} {k}'), r['sha256']))
                           for k, r in run.items()}
    docs['batch'] = pinned(manifest['batchState'], 'batch state')[0]
    for k, r in manifest['publicRecords'].items():
        docs['public'][k] = pinned(r, k)
    for k, r in manifest['code'].items():
        docs['code'][k] = pinned_text(r, k)
    docs['paper'] = pinned_text(manifest['paper']['text'], 'paper text')
    pdf = (PROJECT / manifest['paper']['pdf']['path']).read_bytes()
    require(sha(pdf) == manifest['paper']['pdf']['sha256'], 'paper PDF: not the pinned bytes')
    for k, r in manifest['rights'].items():
        docs['rights'][k] = pinned_text(r, k) if k == 'codeLicence' else pinned(r, k)[0]
    return docs


def private_names(docs):
    """The volume, home and host names the private records use, read from them, never spelled in this file."""
    text = json.dumps([docs['runs'][p]['audit'][0] for p in PROTOCOLS]) + json.dumps(docs['batch'])
    names = set(re.findall(r'/Volumes/([^/\s"]+)/([^/\s"]+)', text))
    names = {n for pair in names for n in pair}
    names |= set(re.findall(r'/(?:home|Users)/([^/\s"]+)/', text))
    for ds in docs['batch']['datasets']:
        for r in ds['runs']:
            host = r['environment']['host']
            names |= {t for t in re.split(r'[-_.]', host) if len(t) >= 4 and re.search(r'\d', t)}
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- the accuracy cells
def same_run(track, results, label, ids=None):
    """The run's own results for the published rows of this track are the published rows: the same run."""
    rows = {r['id']: r for r in track['rows']}
    checked = []
    for rid in ids or ('labram', 'cbramod'):
        r, s = rows[rid], results[rid]
        close(r['y'], 100 * s['ba'], f'{label}: published {rid} balanced accuracy', 1e-9)
        close(r['x'], s['f1'], f'{label}: published {rid} macro F1', 1e-12)
        close(r['interval'][0], 100 * s['ci'][0], f'{label}: published {rid} lower bound', 1e-9)
        close(r['interval'][1], 100 * s['ci'][1], f'{label}: published {rid} upper bound', 1e-9)
        require(r['subjects'] == s['people'], f'{label}: published {rid} cohort differs')
        checked.append(rid)
    return checked


def parallel_cell(p, docs, track, code, label):
    (summary, s_sha), (audit, a_sha) = docs['summary'], docs['audit']
    (dproto, d_sha), (eproto, _) = docs['datasetProtocol'], docs['engineProtocol']
    require(s_sha == track['summarySha'] and a_sha == track['auditSha'] and d_sha == track['protocolSha'],
            f'{label}: not the run whose summary, audit and protocol the core track publishes')
    require(summary['status'] == 'complete' and summary['failures'] == [] and summary['dataset'] == PARALLEL[p]
            and MODEL in summary['planned_models'], f'{label}: the run summary is not a complete run with EEGPT')
    res = {r['model']: r for r in summary['results']}
    require(set(res) == set(summary['planned_models']) and all(r['dataset'] == PARALLEL[p] for r in res.values()),
            f'{label}: the summary lists other results')
    e = res[MODEL]
    ba, f1, ci = e['subject_mean_balanced_accuracy'], e['subject_mean_macro_f1'], e['descriptive_subject_bootstrap_95']
    # The audit: passed, every check passed, and its EEGPT model entry and metric check carry the same values.
    require(audit['status'] == 'pass' and audit['dataset'] == PARALLEL[p] and audit['no_models_retrained'] is True
            and all(c['status'] == 'pass' for c in audit['checks']), f'{label}: the run audit did not pass')
    am = {m['model']: m for m in audit['models']}
    require(am[MODEL]['status'] == 'audited' and am[MODEL]['subject_mean_balanced_accuracy'] == ba
            and am[MODEL]['subject_mean_macro_f1'] == f1 and am[MODEL]['descriptive_subject_bootstrap_95'] == ci,
            f'{label}: the audit lists other EEGPT values')
    checks = {c['name']: c for c in audit['checks']}
    met = checks['eegpt.per_subject_metrics_and_ci']
    require(met['subject_mean_balanced_accuracy'] == ba and met['descriptive_subject_bootstrap_95'] == ci
            and met['participants'] == e['participants'], f'{label}: the audit recomputed other values')
    cov = checks['eegpt.prediction_coverage']
    require(cov['samples'] == e['trials'] and cov['classes'] == e['classes'], f'{label}: the audit covered other trials')
    rep = checks['eegpt.ridge_head_replay_and_train_only_scaler']
    require(0.0 <= rep['max_abs_replay_score_error'] <= 1e-13 and rep['classifier_refit'] is False
            and rep['feature_shape'] == [e['trials'], 2048], f'{label}: the saved heads do not replay')
    require(checks['eegpt.artifact_hashes']['status'] == 'pass', f'{label}: the EEGPT files are not the sealed ones')
    # The engine protocol of the run: seed, ridge head, and EEGPT in the model set.
    require(eproto['seed'] == 20260919 and eproto['ridge']['alpha'] == 100.0 and MODEL in eproto['models']
            and eproto['ridge']['scaler'] == 'training-only StandardScaler', f'{label}: another engine protocol')
    published = {k: {'ba': res[k]['subject_mean_balanced_accuracy'], 'f1': res[k]['subject_mean_macro_f1'],
                     'ci': res[k]['descriptive_subject_bootstrap_95'], 'people': res[k]['participants']}
                 for k in ('labram', 'cbramod')}
    same = same_run(track, published, label)
    require(float(dproto['window_seconds']).is_integer(), f'{label}: a fractional window')
    window = int(dproto['window_seconds'])
    require(window in (1, 2, 30) and dproto['dataset_id'] == PARALLEL[p], f'{label}: another dataset protocol')
    channels = [ALIASES.get(c.upper(), c.upper()) for c in dproto['channels']]
    require(len(channels) == track['rows'][0]['channels'], f'{label}: the protocol has another montage')
    return {'ba': ba, 'f1': f1, 'ci': ci, 'people': e['participants'], 'trials': e['trials'], 'classes': e['classes'],
            'channels': channels, 'window': window, 'source_hz': float(dproto['sfreq']), 'same_run_as': same,
            'audit_checks': len(audit['checks']), 'seed': eproto['seed'],
            'head_replay_max_error': rep['max_abs_replay_score_error'],
            'summary_sha256': s_sha, 'audit_sha256': a_sha, 'protocol_sha256': d_sha}


def beta_cell(p, docs, track, public_beta, label):
    (summary, s_sha), (audit, a_sha), (proto, pr_sha) = docs['summary'], docs['audit'], docs['protocol']
    require(s_sha == track['summarySha'] and a_sha == track['auditSha'] and pr_sha == track['protocolSha'],
            f'{label}: not the run whose summary, audit and protocol the core track publishes')
    montage = MONTAGE[p]
    res = {r['model']: r for r in summary['results'] if r['montage'] == montage}
    require(len(summary['results']) == 12 and set(res) == {'cca', 'spectral-ridge', 'labram', MODEL, 'cbramod', 'eegnet'},
            f'{label}: the summary lists other results')
    e = res[MODEL]
    ba, f1, ci = e['subject_mean_balanced_accuracy'], e['subject_mean_macro_f1'], e['descriptive_subject_bootstrap_95_percentile']
    require(audit['status'] == 'passed' and audit['all_passed'] is True and audit['failed_comparisons'] == 0
            and audit['failures'] == [] and audit['errors'] == [], f'{label}: the BETA audit did not pass')
    ac = {c['comparison']: c for c in audit['comparisons']}[f'{montage}/{MODEL}']
    require(ac['status'] == 'passed' and ac['predictions'] == e['trials']
            and ac['subject_mean_balanced_accuracy_recomputed'] == ba and ac['subject_mean_macro_f1_recomputed'] == f1
            and ac['participant_bootstrap_95_recomputed'] == ci, f'{label}: the audit recomputed other values')
    pb, _ = public_beta
    require(pb['independent_audit_sha256'] == a_sha and pb['independent_audit_status'] == 'passed',
            f'{label}: the public BETA summary names another audit')
    pe = next(r for r in pb['results'] if r['model'] == MODEL and r['montage'] == montage)
    require(pe['subject_mean_balanced_accuracy'] == ba and pe['subject_mean_macro_f1'] == f1
            and pe['descriptive_subject_bootstrap_95_percentile'] == ci, f'{label}: the public BETA summary differs')
    require(proto['montages'][montage] == e['channels'] and proto['preprocessing']['epoch_seconds_relative_to_stimulus_onset']
            == [0, 2] and proto['probe']['alpha'] == 100.0, f'{label}: another BETA protocol')
    stated(proto['metrics']['bootstrap'], '10000 draws of70participants, seed20260912', label)
    published = {k: {'ba': res[k]['subject_mean_balanced_accuracy'], 'f1': res[k]['subject_mean_macro_f1'],
                     'ci': res[k]['descriptive_subject_bootstrap_95_percentile'], 'people': res[k]['subjects']}
                 for k in ('labram', 'cbramod')}
    same = same_run(track, published, label)
    require(e['nominal_chance'] * 100 == track['chanceLevel'], f'{label}: another chance level')
    return {'ba': ba, 'f1': f1, 'ci': ci, 'people': e['subjects'], 'trials': e['trials'], 'classes': 40,
            'channels': list(e['channels']), 'window': 2, 'source_hz': float(proto['preprocessing']['source_rate_hz']),
            'same_run_as': same, 'audit_checks': None, 'seed': 20260912, 'head_replay_max_error': None,
            'summary_sha256': s_sha, 'audit_sha256': a_sha, 'protocol_sha256': pr_sha}


def idle_cell(docs, track, review, label):
    (summary, s_sha), (audit, a_sha), (proto, pr_sha) = docs['summary'], docs['audit'], docs['protocol']
    models_src, models_sha = docs['models']
    require(a_sha == track['auditSha'], f'{label}: not the audit the idle track publishes')
    require(audit['passed'] is True and audit['errors'] == [] and audit['protocol_sha256'] == summary['protocol_sha256']
            == pr_sha and audit['audited_models_sha256'] == models_sha, f'{label}: the idle audit did not pass these files')
    replayed = [r for r in audit['output']['results_recomputed'] if r['model'] == 'EEGPT']
    require(len(replayed) == 4 and all(r['feature_head_train_only_replayed'] is True and r['trigger_recomputed'] is True
                                       for r in replayed), f'{label}: the idle audit did not replay the EEGPT heads')
    agg = {a['model']: a for a in summary['aggregate']}
    rec = {a['model']: a for a in audit['output']['aggregate_counts_recomputed']}
    e, r = agg['EEGPT'], rec['EEGPT']
    for k in ('subjects', 'idle_false_trigger_trials', 'idle_trials', 'mi_detected_trials', 'mi_trials',
              'always_abstain_subjects'):
        require(count(e[k]) and e[k] == r[k], f'{label}: the audit recomputed another {k}')
    # Same run as the published LaBraM idle row; the published CBraMod and Deep4Net rows are from another run.
    rows = {row['name']: row for row in track['rows']}
    same, other = [], []
    for name, row in rows.items():
        if name in agg:
            a = agg[name]
            close(row['x'], 100 * a['idle_false_trigger_trials'] / a['idle_trials'], f'{label}: published {name}', 1e-9)
            close(row['y'], 100 * a['mi_detected_trials'] / a['mi_trials'], f'{label}: published {name}', 1e-9)
            require(row['abstain'] == a['always_abstain_subjects'], f'{label}: published {name} abstentions differ')
            same.append(row['id'])
        else:
            other.append(row['id'])
    require('labram' in same and 'cbramod' in other, f'{label}: LaBraM must be from this run and CBraMod from another')
    stated(' '.join(track['protocol']), 'Additional models use protocol ds005342-sitting-cue-gated-expanded-mvp-v1', label)
    # The window metrics: the review's recomputation, equal to the independent one; counts equal the September summary.
    iv, ind = review['idleVerification'], review['independentRecomputation']
    ir = iv['eegpt_idle_result']
    require(iv['source_integrity_mac']['summary_json_sha256'] == s_sha
            and iv['source_integrity_mac']['independent_audit_json_sha256'] == a_sha
            and iv['source_integrity_mac']['protocol_json_sha256'] == pr_sha, f'{label}: the review checked other files')
    require((ir['people'], ir['idle_false_activations'], ir['idle_trials'], ir['commands_detected'], ir['command_trials'],
             ir['always_abstain_people']) == (e['subjects'], e['idle_false_trigger_trials'], e['idle_trials'],
                                              e['mi_detected_trials'], e['mi_trials'], e['always_abstain_subjects']),
            f'{label}: the review recomputed other counts')
    require(ir['cue_gated_reconfirmed']['recomputed_equals_september'] is True, f'{label}: the counts were not reconfirmed')
    require(all(v == ir['people'] for v in ir['checks_out_of_4_people'].values()), f'{label}: a per-person check failed')
    si = ind['results']['idle']
    require(ind['status'] == 'all_recomputations_agree_no_disagreement' and si['window_auroc'] == ir['window_auroc']
            and si['window_balanced_accuracy'] == ir['window_balanced_accuracy']
            and si['counts'] == {'idle_false': e['idle_false_trigger_trials'], 'mi_detected': e['mi_detected_trials'],
                                 'always_abstain': e['always_abstain_subjects']}
            and si['diff_vs_stageB_claim'] == {'auroc': 0.0, 'ba': 0.0}, f'{label}: the independent recomputation differs')
    require(abs(si['window_auroc'] * si['pairs_total'] - si['auroc_x_8100']) < 1e-9 and si['tied_pairs_total'] == 0,
            f'{label}: the AUROC is not a whole number of window pairs')
    cv = iv['implementation_check_against_v9']['CBraMod (expanded_mvp_v1 run, the published idle CBraMod row)']
    require(cv['equal_to_v9_validation'] is True, f'{label}: the definitions do not reproduce the further-encoder rows')
    require(iv['definitions']['threshold'].endswith('ties -> highest threshold') and proto['threshold_grid']
            == [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.01], f'{label}: another threshold rule')
    require(proto['windows']['duration_seconds'] == 2 and 'C=0.1' in proto['frozen_encoder_heads']['classifier']
            and '2048 features' in proto['frozen_encoder_heads']['eegpt_pooling'], f'{label}: another idle protocol')
    channels = names_list(models_src, r'CHANNELS\s*=\s*\[', f'{label} channels')
    require(len(channels) == track['rows'][0]['channels'] == ir['channels'], f'{label}: another montage')
    return {'people': e['subjects'], 'idle_false': e['idle_false_trigger_trials'], 'idle_trials': e['idle_trials'],
            'detected': e['mi_detected_trials'], 'command_trials': e['mi_trials'],
            'abstain': e['always_abstain_subjects'], 'window_ba': ir['window_balanced_accuracy'],
            'window_auroc': ir['window_auroc'], 'channels': channels, 'window': 2, 'same_run_as': same,
            'other_run': other, 'summary_sha256': s_sha, 'audit_sha256': a_sha, 'protocol_sha256': pr_sha}


def review_figures(cells, memo, core_notes, core_ver, batch):
    """The figures the pages print are the ones the review states, and every recorded copy of them agrees."""
    for p in SCORED:
        c = cells[p]
        stated(memo, f'{pct2(c["ba"])} [{pct2(c["ci"][0])}, {pct2(c["ci"][1])}]', f'{p} memo')
    for p in ('mi-rest', 'arithmetic-rest', 'beta-8ch', 'beta-4ch'):
        c, v = cells[p], core_ver['core_cells'][p]
        require(v['balanced_accuracy'] == c['ba'] and v['macro_f1'] == c['f1'] and v['bootstrap_95'] == c['ci']
                and v['participants'] == c['people'] and v['trials'] == c['trials']
                and all(d == 0.0 for d in v['max_abs_difference_vs_records'].values()),
                f'{p}: the read-only verification recomputed other values')
        stated(core_notes, f'| {p} | {c["people"]} / {c["trials"]:,} / {c["classes"]} | {pct2(c["ba"])} | '
                           f'{pct2(c["ci"][0])}–{pct2(c["ci"][1])} |', f'{p} verification notes')
    batch_res = {(ds['dataset'], r['model']): r for ds in batch['datasets'] for run in ds['runs'] for r in run['results']}
    for p, ds in PARALLEL.items():
        b, c = batch_res[(ds, MODEL)], cells[p]
        require(b['subject_mean_balanced_accuracy'] == c['ba'] and b['descriptive_subject_bootstrap_95'] == c['ci']
                and b['subject_mean_macro_f1'] == c['f1'], f'{p}: the batch state records other values')
    require(core_ver['status'] == 'pass' and core_ver['summary']['failed'] == 0
            and core_ver['summary']['passed'] == core_ver['summary']['checks'] == len(core_ver['checks'])
            and all(c['result'] == 'pass' for c in core_ver['checks']), 'the read-only verification did not pass')


# ---------------------------------------------------------------------------- footnote facts
def encoder_facts(code, paper, cells, docs):
    """The architecture and the four facts the footnotes state, each read from the pinned code, protocols or paper."""
    beta_src, suite, enc, pre = code['betaRunner'], code['parallelRunner'], code['encoderSource'], code['pretrainingScript']
    arch = re.search(r'EEGTransformer\(img_size=\[n,512\], patch_size=(\d+), embed_num=(\d+), embed_dim=(\d+),\s*'
                     r'depth=(\d+), num_heads=(\d+)', beta_src)
    require(arch is not None, 'the encoder builder is not in the pinned BETA runner')
    patch, tokens, dim, depth, heads = map(int, arch.groups())
    stated(beta_src, "expected_hash = '9ce130abd9f66cd6141b15918c35760da62ffc86b90f611cdf7b4cf4cb0585df'", 'encoder weights')
    stated(beta_src, 'v = resample_poly(b,128,125,axis=-1).astype(\'float32\') / 1000', 'encoder input')
    stated(beta_src, 'z = model(tensor,chan_ids=ids).mean(1).flatten(1)', 'encoder pooling')
    stated(beta_src, 'expected_dim = 2048', 'encoder pooling')
    stated(suite, "model,ids,meta=BETA.build_encoder(slug,names)", 'parallel runner reuses the encoder builder')
    stated(suite, "if slug=='eegpt' and window==1:\n            model.num_patches=(len(names),4);"
                  "model.patch_embed.num_patches=(len(names),4)", 'one-second patch grid')
    stated(suite, "if seconds not in (1,2,30):raise ValueError(f'Unsupported frozen-encoder duration {seconds}; no padding "
                  "allowed')", 'no padding')
    stated(suite, "aliases={'T3':'T7','T4':'T8','T5':'P7','T6':'P8'}", 'channel aliases')
    stated(suite, 'SEED=20260919', 'parallel bootstrap seed')
    stated(suite, 'rng=np.random.default_rng(SEED)\n    boot=ba[rng.integers(0,len(ba),(10000,len(ba)))].mean(1)',
           'parallel bootstrap')
    stated(beta_src, 'rng = np.random.default_rng(20260912)\n    boot = ba[rng.integers(0,70,size=(10000,70))].mean(1)',
           'BETA bootstrap')
    # The encoder treats each time patch on its own: batch and patches are flattened before attention, and the patch
    # count is only asserted.
    stated(enc, 'x = x.flatten(0, 1) # BmN, mC, D', 'per-patch encoding')
    stated(enc, 'assert N==self.num_patches[1] and C==self.num_patches[0]', 'per-patch encoding')
    dictionary = names_list(enc, r'CHANNEL_DICT = \{k\.upper\(\):v for v,k in enumerate\(\s*\[', 'channel dictionary')
    pretrain = names_list(pre, r'use_channels_names = \[', 'pretraining montage')
    require(len(dictionary) == len(set(dictionary)) == 62 and len(pretrain) == len(set(pretrain)) == 58
            and set(pretrain) <= set(dictionary), 'the channel dictionary or the pretraining montage changed')
    unused = [c for c in dictionary if c not in pretrain]
    require(unused == ['AF7', 'AF8', 'PO5', 'PO6'], f'unused dictionary names: {unused}')
    stated(pre, 'temporal_interpolation(x, 256*4) / 1000', 'pretraining window and units')
    untrained = {}
    for p in PROTOCOLS:
        ch = cells[p]['channels']
        require(all(c in dictionary for c in ch), f'{p}: a channel outside the dictionary')
        untrained[p] = [c for c in ch if c in unused]
    require({p: u for p, u in untrained.items() if u} == {'beta-8ch': ['PO5', 'PO6']},
            'only BETA 8-channel may use untrained channel embeddings')
    # The paper: the five pretraining datasets, the 58 electrodes, 256 Hz, the 64-sample (250 ms) patch, 4 s crops,
    # the average reference and millivolts; and the authors' probe, an adaptive spatial filter with a linear head.
    stated(flat(paper), 'Table 1: Datasets for pretraining and downstream tasks', 'paper')
    for name in PRETRAINING_DATASETS:
        require(re.search(rf'^\s*(?:pretraining Datasets\s+)?{name}\s', paper, re.M), f'paper: {name} not in Table 1')
    for phrase in ('We used 58 electrodes (M = 58)', 'sampling rate of fs = 256 Hz',
                   'Each patch has a time length of d = 64, corresponding to a 250ms time window',
                   'cropping (4s), re-referencing (average)', 'scaling (mV)',
                   'adaptive spatial filters (1 × 1 convolution)', 'TSU [37]',
                   '[37] Yijun Wang, Xiaogang Chen, Xiaorong Gao, and Shangkai Gao. A benchmark dataset for ssvep-'):
        stated(flat(paper), flat(phrase), 'paper')
    require(patch == 64 and tokens == 4 and dim == 512 and depth == 8 and heads == 8, 'another encoder configuration')
    return {'patch_samples': patch, 'summary_tokens': tokens, 'embed_dim': dim, 'depth': depth, 'heads': heads,
            'dictionary': len(dictionary), 'pretrain_channels': len(pretrain), 'unused': unused,
            'untrained': untrained}


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


# ---------------------------------------------------------------------------- the payload's parts
FOOTNOTES = {
    'one-second-patch-grid': (
        ('p300-target', 'semantic-target'),
        'On the P300 and semantic targets, one-second windows ran as four real 0.25-second patches: the patch grid was '
        'set to four after the encoder was built, with no padding. EEGPT’s encoder treats each time patch on its own, so this is numerically the same as '
        'building it for 256-sample inputs, as the Orthosis pilot built it for its 128-sample windows.'),
    'untrained-channel-embeddings': (
        ('beta-8ch',),
        'PO5 and PO6 use channel embeddings that EEGPT’s pretraining never trained: they are two of the four names in '
        'its 62-name channel dictionary (AF7, AF8, PO5, PO6) that its 58-electrode pretraining montage leaves out. The '
        'other six channels here, and all four of the 4-channel subset, use trained embeddings.'),
    'tsinghua-benchmark-context': (
        ('beta-8ch', 'beta-4ch'),
        'For context: BETA is not in EEGPT’s published pretraining list, but the Tsinghua 40-target SSVEP benchmark '
        '(Wang et al., 2017) is, as TSU. BETA’s authors describe BETA as an extension of that benchmark, from the same '
        'group with the same 40-target layout and its own recordings; whether anyone took part in both is not stated.'),
    'shorter-than-pretraining': (
        PROTOCOLS,
        'Every core window is shorter than EEGPT’s 4-second pretraining window: 1 or 2 seconds, and sleep as fifteen '
        '2-second segments. The encoder computes each 0.25-second patch the same way at any length; a shorter window '
        'gives fewer patches to average.'),
    'fixed-readout': (
        PROTOCOLS,
        'The readout is the site’s fixed probe on the frozen summary tokens, as for the published LaBraM and CBraMod '
        'rows: ridge (alpha 100) on 2,048 pooled values, and on idle a per-person logistic head. It is not the authors’ downstream probe, a '
        'learnable spatial filter with a linear head, and the windows are fed without the average reference EEGPT was '
        'pretrained with.'),
    'source-rate': (
        ('mi-rest',),
        'ds003810 is recorded at 125 Hz; its windows reach the encoder upsampled to 256 Hz, so they carry nothing above '
        '62.5 Hz.'),
    'idle-run': (
        ('idle',),
        'Same run as the published LaBraM idle row; the published CBraMod idle row comes from another run, so a '
        'comparison with it is across runs. The window balanced accuracy and AUROC were computed from this run’s saved '
        'probabilities with the definitions of the further foundation-encoder rows; the run itself recorded the counts.'),
}


def footnotes(facts, cells, pilot):
    patch_s = facts['patch_samples'] / 256
    # The Orthosis pilot built the encoder at its own window length, the method the patch-grid note compares with.
    pilot_in = pilot['results']['orthosis-eegpt-vs-58ch']['encoder_input']
    require(pilot_in['sampling_hz'] == 256 and pilot_in['samples'] == 128, 'the pilot encoder input changed')
    sleep_segments = cells['sleep-scalp']['window'] // 2
    windows = sorted({cells[p]['window'] for p in PROTOCOLS if p != 'sleep-scalp'})
    require(windows == [1, 2] and sleep_segments == 15 and patch_s == 0.25, 'the windows changed')
    require(cells['mi-rest']['source_hz'] == 125.0, 'the mi-rest source rate changed')
    require(sorted(p for p in PROTOCOLS if cells[p]['window'] == 1) == ['p300-target', 'semantic-target'],
            'the one-second protocols changed')
    f = {
        'one-second-patch-grid': {'window_seconds': 1, 'patches': 4, 'patch_samples': facts['patch_samples'],
                                  'encoder_sampling_hz': 256, 'padding': False, 'equivalent_input_samples': 256,
                                  'pilot_input_samples': pilot_in['samples']},
        'untrained-channel-embeddings': {'dictionary_names': facts['dictionary'],
                                         'pretraining_electrodes': facts['pretrain_channels'],
                                         'unused_in_pretraining': facts['unused'],
                                         'channels_affected': facts['untrained']['beta-8ch']},
        'tsinghua-benchmark-context': {'in_pretraining_list': 'TSU',
                                       'benchmark': 'Wang et al. 2017, doi:10.1109/TNSRE.2016.2627556',
                                       'beta_paper': 'https://doi.org/10.3389/fnins.2020.00627',
                                       'exposure_status_unchanged': True},
        'shorter-than-pretraining': {'pretraining_window_seconds': 4, 'core_window_seconds': [1, 2],
                                     'sleep_segments': sleep_segments, 'sleep_segment_seconds': 2,
                                     'patch_seconds': patch_s},
        'fixed-readout': {'ridge_alpha': 100, 'pooled_dimension': 2048, 'idle_logistic_c': 0.1,
                          'average_reference': False},
        'source-rate': {'source_sampling_hz': 125, 'canonical_sampling_hz': 250, 'encoder_sampling_hz': 256,
                        'highest_frequency_hz': 62.5},
        'idle-run': {'same_run_rows': cells['idle']['same_run_as'], 'other_run_rows': cells['idle']['other_run']},
    }
    out = []
    for fid, (protocols, text) in FOOTNOTES.items():
        out.append({'id': fid, 'protocols': list(protocols),
                    'placement': 'row' if tuple(protocols) == PROTOCOLS else 'cell', 'text': text, 'facts': f[fid]})
    return out


def exposure(proposal, fm, paper):
    """The seven dataset cells as the review proposed them, worded with the further-encoder formula."""
    pm, v9 = proposal['model'], fm['results']['foundation-models-v9']['pretraining_exposure']
    require(proposal['status'] == 'proposal_only_not_exported' and pm['key'] == MODEL and pm['checked_on']
            == EXPOSURE_CHECKED, 'another exposure proposal')
    statement = f"not in the authors' published pretraining list (checked {EXPOSURE_CHECKED})"
    require(v9['statements']['not_exposed'] == statement.replace(EXPOSURE_CHECKED, v9['checked_on']),
            'the further-encoder statement formula changed')
    require(proposal['counts'] == {'exposed': 0, 'not_exposed': 7, 'unknown': 0}, 'the proposal counts changed')
    first = None
    cells = []
    for c in proposal['cells']:
        require(c['model'] == MODEL and c['status'] == 'not_exposed' and c['confidence'] == 'high'
                and c['statement'] == statement and c['basis'] == 'corpus enumerated; absent',
                f'exposure {c["dataset"]}: not the proposed cell')
        end = 'no in-house source.'
        require(end in c['evidence'], f'exposure {c["dataset"]}: another evidence text')
        lead = c['evidence'][:c['evidence'].index(end) + len(end)]
        require(first in (None, lead), 'the exposure cells do not share their evidence')
        first = lead
        cells.append({'dataset': c['dataset'], 'protocols': c['protocols'], 'status': c['status'],
                      'confidence': c['confidence'], 'statement': statement, 'basis': c['basis'], 'evidence': lead,
                      'urls': c['urls']})
    require(sorted(p for c in cells for p in c['protocols']) == sorted(PROTOCOLS)
            and {c['dataset'] for c in cells} == set(EXPOSURE_DATASET.values()), 'the exposure cells do not cover the matrix')
    for name in PRETRAINING_DATASETS:
        stated(lead, name, 'exposure evidence')
    require(f'https://doi.org/{PAPER_DOI}' in pm['primary_sources'], 'the proposal cites another paper')
    block = {
        'checked_on': EXPOSURE_CHECKED,
        'definition': v9['definition'],
        'status_vocabulary': v9['status_vocabulary'],
        'statement': statement,
        'wording_rule': v9['wording_rule'],
        'model': {
            'key': MODEL, 'name': 'EEGPT',
            'corpus': ('Five public datasets, as the paper’s Table 1 lists them: PhysioMI (PhysioNet motor imagery and '
                       'execution), HGD, TSU (the Tsinghua 40-target SSVEP benchmark), SEED and M3CV; 58 electrodes, '
                       '256 Hz, millivolts, average reference, 4-second windows.'),
            'corpus_listing': pm['corpus_listing'],
            'author_downstream_use': pm['author_downstream_use'],
            'primary_sources': pm['primary_sources'],
        },
        'cells': cells,
        'counts': dict(proposal['counts']),
        'context': {'beta-8ch': 'tsinghua-benchmark-context', 'beta-4ch': 'tsinghua-benchmark-context'},
    }
    by_protocol = {p: c for c in cells for p in c['protocols']}
    return block, by_protocol


def attribution(public_audit, auditor_src, auditor_sha, topics, core_ver, cells):
    """The eight EEGPT rows and four contrasts, in the published fields and with the published rows' strings."""
    audit, audit_sha = public_audit
    require(audit['status'] == 'pass' and audit['auditor_sha256'] == auditor_sha, 'the public attribution audit did not pass')
    require(audit_sha in topics['provenance']['evidence_sha256'], 'the published attribution rows cite another audit')
    stated(auditor_src, 'np.random.default_rng(20260920).integers(0,len(delta),(10000,len(delta)))', 'attribution bootstrap')
    stated(auditor_src, 'ALPHAS=[100.,10000.,1.]', 'attribution heads')
    packages = {(p['dataset'], p['mode'], p['condition']): p for p in audit['packages']}
    contrasts = {(c['dataset'], c['mode'], c['model']): c for c in audit['contrasts']}
    published_rows = [r for r in topics['rows'] if r['track'] in TRACK.values()]
    published_contrasts = [c for c in topics['paired_contrasts'] if c['track'] in TRACK.values()]
    # Method parity: the published LaBraM and CBraMod rows and contrasts are this audit's, value for value.
    for c in published_contrasts:
        mode = next(m for m, t in TRACK.items() if t == c['track'])
        a = contrasts[(c['dataset_id'], mode, c['model'])]
        require(a['delta'] == c['difference'] and a['paired_participant_bootstrap_95'] == c['paired_participant_bootstrap_95'],
                f'published contrast {c["model"]} {c["dataset_id"]} {mode}: not this audit’s')
    verified = {(c['dataset'], c['mode'], c['model']): c for c in core_ver['attribution_contrasts']}
    e1 = next(c for c in core_ver['checks'] if c['id'] == 'E1')
    require(e1['result'] == 'pass' and all(d == {'y_pred_disagreements': 0, 'scores_max_abs_diff': 0.0}
                                           for d in e1['detail'].values()) and set(e1['detail']) == {d for d, _ in ATTRIBUTION},
            'the fixed-head pretrained predictions are not shown to be the core run’s')
    candidate = core_ver['candidate_eegpt_attribution_rows_in_published_schema']
    rows, out_contrasts = [], []
    for ds, mode in ATTRIBUTION:
        track = TRACK[mode]
        a = contrasts[(ds, mode, MODEL)]
        require(a['pass'] is True and a['checkpoint_release_status'] == 'hold-unresolved-weight-license',
                f'{ds} {mode}: another audit record')
        pre = packages[(ds, mode, 'eegpt-pretrained')]
        rnd = [packages[(ds, mode, f'eegpt-random-{s}')] for s in RANDOM_SEEDS]
        for pk in [pre] + rnd:
            require(pk['pass'] is True and pk['head_replay_max_error'] == 0.0, f'{ds} {mode}: a package did not pass')
        require(pre['mean_balanced_accuracy'] == a['pretrained_ba'], f'{ds} {mode}: another pretrained score')
        close(sum(p['mean_balanced_accuracy'] for p in rnd) / 3, a['random_mean_ba'], f'{ds} {mode}: random mean', 1e-12)
        close(a['pretrained_ba'] - a['random_mean_ba'], a['delta'], f'{ds} {mode}: difference', 1e-12)
        g = verified[(ds, mode, MODEL)]
        require(g['pretrained_ba'] == a['pretrained_ba'] and g['random_mean_ba'] == a['random_mean_ba']
                and g['delta'] == a['delta'] and g['paired_participant_bootstrap_95'] == a['paired_participant_bootstrap_95']
                and [v for k, v in g.items() if k.startswith('max_abs_difference')] == [0.0, 0.0],
                f'{ds} {mode}: the read-only verification recomputed another contrast')
        if mode == 'fixed':   # the same predictions as the core cell
            core = cells['mi-rest' if ds == 'ds003810' else 'arithmetic-rest']
            require(a['pretrained_ba'] == core['ba'] and pre['participants'] == core['people']
                    and pre['trials'] == core['trials'], f'{ds}: the fixed-head pretrained row is not the core cell')
        ref = next(r for r in published_rows if r['track'] == track and r['dataset_id'] == ds and r['model'] == 'labram'
                   and r['initialization'] == 'pretrained')
        refc = next(c for c in published_contrasts if c['track'] == track and c['dataset_id'] == ds)
        interval(a['paired_participant_bootstrap_95'], a['delta'], f'{ds} {mode}: paired', -1.0, 1.0)
        for init, value, seeds in (('pretrained', a['pretrained_ba'], 1), ('constructor-random-mean', a['random_mean_ba'], 3)):
            row = {'id': f'{track}-{MODEL}-{ds}-{"pretrained" if seeds == 1 else "random-mean"}', 'track': track,
                   'protocol_id': ref['protocol_id'], 'dataset_id': ds, 'model': MODEL, 'metric': ref['metric'],
                   'value': value, 'confidence_interval_95': None, 'participants': pre['participants'],
                   'trials': pre['trials'], 'initialization': init, 'encoder_seed_count': seeds,
                   'training_regime': ref['training_regime'], 'head_selection': ref['head_selection']}
            require(set(row) == set(ref), f'{row["id"]}: not the published row fields')
            rows.append(row)
        contrast = {'track': track, 'model': MODEL, 'dataset_id': ds, 'participants': pre['participants'],
                    'comparison': refc['comparison'], 'difference': a['delta'],
                    'paired_participant_bootstrap_95': a['paired_participant_bootstrap_95'], 'unit': refc['unit'],
                    'interpretation': refc['interpretation']}
        require(set(contrast) == set(refc), f'{ds} {mode}: not the published contrast fields')
        out_contrasts.append(contrast)
    # The review's draft rows say the same, field for field.
    strip = lambda r: {k: v for k, v in r.items() if k != 'id'}
    require([strip(r) for r in rows] == candidate['rows'], 'the review drafted other rows')
    require([{k: v for k, v in c.items() if k != 'interpretation'} for c in out_contrasts] == candidate['paired_contrasts'],
            'the review drafted other contrasts')
    sel = next(r for r in published_rows if r['track'] == TRACK['selected'])
    return {
        'topic': 'does-pretraining-help',
        'beside': 'the published LaBraM and CBraMod rows of deployment-topics.json, which keeps its bytes',
        'fields': 'the row and paired-contrast fields of deployment-topics.json',
        'rows': rows,
        'paired_contrasts': out_contrasts,
        'method': {
            'comparison': 'the pretrained encoder against three constructor-random initialisations of the same '
                          'architecture, each read out with the same head on the same folds',
            'random_initialisation_seeds': list(RANDOM_SEEDS),
            'heads': {'fixed': 'ridge, alpha 100', 'selected': sel['head_selection']},
            'bootstrap': {'draws': 10000, 'seed': 20260920, 'unit': 'participant',
                          'statistic': 'the mean over participants of the pretrained score minus the mean of the three '
                                       'random-initialisation scores'},
            'equal_to_core_cells': 'The fixed-head pretrained rows are the core-matrix EEGPT cells of mi-rest and '
                                        'arithmetic-rest: the same predictions.',
        },
        'interpretation_limits': topics['interpretation_limits']['attribution'],
    }


def comparisons(cells, tracks, release):
    out = []
    for p in SCORED:
        c = cells[p]
        lo, hi = percent(c['ci'][0]), percent(c['ci'][1])
        rows = []
        for r in tracks[p]['rows']:
            r_lo, r_hi = r['interval']
            rel = 'above' if lo > r_hi else 'below' if hi < r_lo else 'overlap'
            gap = round(lo - r_hi, 12) if rel == 'above' else round(r_lo - hi, 12) if rel == 'below' else None
            require(gap is None or gap > 0, f'{p} {r["id"]}: a gap that is not one')
            rows.append({'row': r['id'], 'name': r['name'], 'family': r['family'], 'relation': rel, 'gap_pp': gap})
        apart = [r for r in rows if r['gap_pp'] is not None]
        narrow = min(apart, key=lambda r: r['gap_pp']) if apart else None
        out.append({'protocol': p, 'rows': rows,
                    'relations': {k: [r['row'] for r in rows if r['relation'] == k] for k in ('above', 'below', 'overlap')},
                    'smallest_gap': None if narrow is None else {'row': narrow['row'], 'gap_pp': narrow['gap_pp']}})
    return {
        'rule': ('Above or below only when the marginal 95% intervals do not overlap; otherwise overlap. The gap is the '
                 'distance between the two intervals in percentage points (from the percent figures, rounded to 12 '
                 'decimals). Descriptive: the same people under two encoders are not tested pairwise here.'),
        'published_reference_release': release,
        'protocols': out,
        'smallest_gap': ('Among the rows EEGPT is above or below, the one whose interval is nearest, with that gap: '
                         'how narrow the clearest call on the protocol is. Not an order of rows.'),
        'idle': ('No interval on the idle protocol, so no relation is called; its counts sit beside the published rows, '
                 'of which LaBraM is from the same run.'),
    }


def rights(track, people):
    record = {k: track[k] for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview',
                                    'reviewedAt', 'reviewBasis', 'rightsScope')}
    record['name'] = track['dataset']
    require(record['reviewedAt'] == CORE_DATE and record['rightsScope'] == 'Personal noncommercial research; aggregate '
            'results only', f'{track["id"]}: another rights record')
    record['published_here'] = (
        'Reused unchanged from the review of the same recordings for the core matrix. Published here for EEGPT: '
        + ('test-trial counts of idle false activations and commands detected within 3 s, how many people always '
           'abstained, and the cohort-mean window balanced accuracy and AUROC; no interval'
           if track['id'] == 'idle' else
           'the cohort balanced accuracy with its participant-bootstrap interval, macro F1 and the cohort size')
        + '; no per-person, per-fold or per-trial value.')
    return record


def model_block(manifest, pilot, mvp_models, docs, facts):
    pm = pilot['results']['orthosis-eegpt-vs-58ch']['model']
    re_ = docs['rights']['reassessment']
    terms = docs['rights']['checkpointTerms']
    ci = re_['checkpoint_identity']
    require(re_['status'] == 'aggregate_hold_is_self_imposed_not_verified_publisher_ban'
            and re_['recommendation']['legal_certification'] is False, 'the reassessment changed')
    require(ci['original_sha256'] == pm['checkpoint']['sha256'] == terms['checkpoint_identity']['original_sha256']
            and ci['tensor_derivative_sha256'] == pm['checkpoint']['tensor_conversion_sha256']
            and ci['original_filename'] == pm['checkpoint']['file'], 'another checkpoint')
    require(terms['resolved_checkpoint_license'] is None and terms['explicit_checkpoint_usage_terms_verified'] is False,
            'the checkpoint terms are no longer unresolved; the model block must be reviewed')
    mr = next(r for r in docs['rights']['modelRights']['records'] if r['model'] == 'EEGPT')
    require(mr['checkpoint_license']['license'] is None and mr['checkpoint_sha256'] == ci['original_sha256']
            and mr['code_license']['license'] == 'Apache-2.0', 'the earlier model-rights record changed')
    require(docs['rights']['checkpointRecheck']['explicit_weight_license_found'] is False
            and docs['rights']['checkpointRecheck']['resolved_license'] is None, 'the earlier recheck changed')
    lic = docs['rights']['codeLicence']
    require(flat(lic).startswith('Apache License Version 2.0, January 2004')
            and manifest['rights']['codeLicence']['retrievedFrom'].endswith(f'{pm["source_revision"]}/LICENSE'),
            'the code licence is not Apache 2.0 at the pinned revision')
    mm = next(m for m in mvp_models if m['name'] == 'EEGPT')
    require(mm['parameters'] == pm['encoder_parameters'] and mm['status'] == 'Rights review pending',
            'the released directory entry changed')
    require(manifest['code']['encoderSource']['revision'] == pm['source_revision'], 'another source revision')
    require(pm['weights_licence'] is None and pm['weights_distributed'] is False and pm['code_licence'] == 'Apache-2.0',
            'the pilot model block changed')
    paper = manifest['paper']
    return {
        'id': MODEL, 'name': 'EEGPT', 'method_slug': pm['method_slug'], 'family': 'foundation',
        'paper': f'https://doi.org/{paper["doi"]}', 'paper_pdf': paper['pdfUrl'], 'paper_title': paper['title'],
        'paper_venue': paper['venue'],
        'repository': pm['repository'], 'source_revision': pm['source_revision'],
        'checkpoint': dict(pm['checkpoint']),
        'encoder_parameters': pm['encoder_parameters'],
        'architecture': {'patch_samples': facts['patch_samples'], 'patch_seconds': facts['patch_samples'] / 256,
                         'encoder_sampling_hz': 256, 'embed_dim': facts['embed_dim'], 'depth': facts['depth'],
                         'heads': facts['heads'], 'summary_tokens': facts['summary_tokens'], 'pooled_dimension': 2048},
        'input': ('the published 250 Hz microvolt windows, resampled to 256 Hz and divided by 1,000 (millivolts); only '
                  'the recorded channels, each as its channel token (T3, T4, T5 and T6 named T7, T8, P7 and P8); no '
                  'interpolation, padding, zero-filled channels or average reference'),
        'pooling': 'the four summary tokens averaged over time patches and concatenated: 2,048 values per window',
        'mode': 'Frozen encoder + ridge head', 'idle_mode': 'Frozen encoder + linear head',
        'pretraining': {'datasets': list(PRETRAINING_DATASETS), 'electrodes': facts['pretrain_channels'],
                        'channel_dictionary': facts['dictionary'], 'window_seconds': 4, 'sampling_hz': 256,
                        'reference': 'average', 'units': 'mV'},
        'code_licence': pm['code_licence'],
        'code_licence_scope': pm['code_licence_scope'],
        'weights_licence': None,
        'weights_licence_status': pm['weights_licence_status'],
        'weights_distributed': False,
        'weights_note': pm['weights_note'],
        'endorsement': 'none implied',
        'rights_review': ('Published by the owner’s decision, aggregate results only, as the pilot comparison is. The '
                          'checkpoint’s licence could not be read; no publisher prohibition on independently computed '
                          'aggregate results was found; no original or converted weights are distributed.'),
    }


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


VERBATIM = re.compile(r'^\$\.protocols\[\d+\]\.rights\.')    # the released rights records, copied as they are


def prose_check(payload, private):
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(not SOURCE_IDS.search(text), f'source file or participant identifier in export: {trail}')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.IGNORECASE),
                    f'private host or volume name in export: {trail}')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        if trail in ('$.schema_version', '$.release_id') or VERBATIM.match(trail):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):   # the release record is dated by design (/releases/, /data-use/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail.startswith(('$.provenance', '$.release_record')) or trail.endswith('.urls') or '.urls[' in trail:
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def weights_not_apache(payload):
    for trail, text in strings(payload):
        if trail == '$.model.code_licence':
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if 'apache' in sentence.lower():
                require(re.search(r'\bcode\b', sentence, re.I) and not re.search(r'weights? (?:are|is) apache', sentence, re.I),
                        f'{trail}: Apache-2.0 not tied to the code: {sentence!r}')
                if re.search(r'\bweights?\b|checkpoint', sentence, re.I):
                    require(NEGATION.search(sentence), f'{trail}: Apache-2.0 beside the weights, unnegated: {sentence!r}')
    m = payload['model']
    require(m['weights_licence'] is None and m['code_licence'] == 'Apache-2.0' and m['weights_distributed'] is False
            and 'unresolved' in m['weights_licence_status'], 'the EEGPT weights’ licence must stay unresolved')


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['holds'] == [], 'this release has no hold')
    docs = load(manifest)
    mvp, topics = docs['published']['coreMatrix'], docs['published']['deploymentTopics']
    fm, pilot = docs['published']['foundationModels'], docs['published']['pilotStudies']
    tracks = {t['id']: t for t in mvp['tracks']}
    require(tuple(tracks) == PROTOCOLS, 'the core matrix lists other protocols')
    require(all(r['id'] != MODEL for t in mvp['tracks'] for r in t['rows']), 'EEGPT is already a core row')
    rv = docs['review']

    cells = {}
    for p in PROTOCOLS:
        if p in PARALLEL:
            cells[p] = parallel_cell(p, docs['runs'][p], tracks[p], docs['code'], p)
        elif p in MONTAGE:
            cells[p] = beta_cell(p, docs['runs'][p], tracks[p], docs['public']['betaSummary'], p)
        else:
            cells[p] = idle_cell(docs['runs'][p], tracks[p], rv, p)
    review_figures(cells, rv['memo'], rv['coreVerificationNotes'], rv['coreVerification'], docs['batch'])
    facts = encoder_facts(docs['code'], docs['paper'], cells, docs)
    stated(flat(rv['compatibilityAndRights']), flat(manifest['betaPaper']['quote']), 'BETA relation')
    stated(flat(rv['compatibilityAndRights']), 'The paper does not say whether anyone took part in both', 'BETA relation')
    stated(rv['memo'], '与用 `img_size=[C,256]` 构造完全等价。后者正是 Orthosis v2 的做法', 'patch-grid equivalence')
    stated(rv['memo'], '各时间 patch 互不交互', 'per-patch encoding')
    stated(flat(manifest['betaPaper']['checked']), flat(manifest['betaPaper']['quote']), 'BETA relation')
    exposure_block, exposure_of = exposure(rv['exposureProposal'], fm, docs['paper'])
    attr = attribution(docs['public']['attributionAudit'], docs['code']['attributionAuditor'],
                       manifest['code']['attributionAuditor']['sha256'], topics, rv['coreVerification'], cells)
    model = model_block(manifest, pilot, mvp['models'], docs, facts)
    notes = footnotes(facts, cells, pilot)
    note_ids = {p: [n['id'] for n in notes if p in n['protocols']] for p in PROTOCOLS}

    protocols, out_cells = [], []
    for p in PROTOCOLS:
        t, c = tracks[p], cells[p]
        chance = None if t['chanceLevel'] is None else t['chanceLevel'] / 100
        entry = {'id': p, 'title': t['title'], 'dataset': t['dataset'], 'type': t['type'], 'protocol_id': t['protocolId'],
                 'people': c['people'], 'channels': len(c['channels']), 'window_seconds': c['window'],
                 'chance_level': chance, 'core_files': [f'{p}-results.csv', f'{p}-protocol.json'],
                 'run': {'same_run_as': c['same_run_as'], 'summary_sha256': c['summary_sha256'],
                         'audit_sha256': c['audit_sha256'], 'protocol_sha256': c['protocol_sha256'],
                         'independent_audit': 'pass'},
                 'rights': rights(t, c['people'])}
        if p == 'sleep-scalp':
            entry['segments'] = {'count': c['window'] // 2, 'each_seconds': 2}
        if p == 'idle':
            entry['run']['other_run_rows'] = c['other_run']
            require(c['people'] == t['subjects'], 'idle: another cohort')
            cell = {'model': MODEL, 'protocol': p, 'status': 'complete', 'people': c['people'],
                    'channels': len(c['channels']), 'idle_false_activations': c['idle_false'],
                    'idle_trials': c['idle_trials'], 'commands_detected': c['detected'],
                    'command_trials': c['command_trials'], 'always_abstain_people': c['abstain'],
                    'window_balanced_accuracy': c['window_ba'], 'window_auroc': c['window_auroc'],
                    'interval': None,
                    'percent': {'idle_false_activation': percent(c['idle_false'] / c['idle_trials']),
                                'command_detection': percent(c['detected'] / c['command_trials']),
                                'window_balanced_accuracy': percent(c['window_ba'])}}
            require(0 <= c['window_ba'] <= 1 and 0 <= c['window_auroc'] <= 1, 'idle: a window metric out of range')
        else:
            require(c['people'] == t['subjects'] and len(c['channels']) == t['rows'][0]['channels'],
                    f'{p}: another cohort or montage than the core track')
            iv = interval(c['ci'], c['ba'], p)
            require(0 <= c['f1'] <= 1, f'{p}: macro F1 out of range')
            cell = {'model': MODEL, 'protocol': p, 'status': 'complete', 'balanced_accuracy': c['ba'],
                    'interval_95': iv, 'macro_f1': c['f1'], 'people': c['people'], 'trials': c['trials'],
                    'classes': c['classes'], 'channels': len(c['channels']), 'chance_level': chance,
                    'interval_includes_chance': iv[0] <= chance <= iv[1], 'at_or_below_chance': c['ba'] <= chance,
                    'interval': {'kind': 'participant bootstrap of the equal-participant mean', 'level': 0.95,
                                 'draws': 10000, 'seed': c['seed'],
                                 'scope': 'descriptive: it ignores cross-validation dependence and carries no '
                                          'multiplicity correction'},
                    'percent': {'balanced_accuracy': percent(c['ba']), 'interval_95': [percent(iv[0]), percent(iv[1])],
                                'chance_level': t['chanceLevel']}}
            require(cell['interval_includes_chance'] is False and cell['at_or_below_chance'] is False,
                    f'{p}: a chance flag changed; the reading must be reviewed')
        ex = exposure_of[p]
        cell['exposure'] = {'status': ex['status'], 'confidence': ex['confidence'], 'statement': ex['statement']}
        cell['footnotes'] = note_ids[p]
        protocols.append(entry)
        out_cells.append(cell)

    cmp_block = comparisons(cells, tracks, mvp['releaseId'])
    rr = manifest['releaseRecord']
    people = {p: cells[p]['people'] for p in PROTOCOLS}
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'title': 'EEGPT on the core matrix',
        'placement': ('a frozen row beside the core matrix on every protocol page, with the foundation encoders and '
                      'never ranked; never merged into experiments.json'),
        'metric_units': ('balanced accuracy, its interval, macro F1, chance levels, the idle window balanced accuracy '
                         'and AUROC and the attribution scores and differences are proportions in [0,1]; each percent '
                         'block gives the same figures × 100, rounded to 12 decimals, in the units of the core rows; '
                         'comparison gaps are percentage points; counts of people, trials, classes, channels and idle '
                         'trials are whole numbers; null means not computed, never zero'),
        'scope': ('EEGPT’s eight core-matrix cells, from the same runs as the published LaBraM rows and, except on '
                  'idle, the CBraMod rows, with only the encoder swapped, and its pretraining-attribution rows on mi-rest and EEGMAT. The cells are '
                  'the runs’ recorded aggregates, checked read-only against the saved predictions; nothing was re-run. '
                  'The pilot comparison on the Orthosis dataset is a separate result and stays outside every '
                  'leaderboard.'),
        'model': model,
        'design': {
            'frozen_probe': ('EEGPT ran in the same runs as the published LaBraM rows and, except on idle, the '
                             'CBraMod rows, with only the encoder swapped: the same published 250 Hz microvolt windows (1 s or 2 s; sleep as 15 '
                             'two-second segments whose outputs are averaged), the same participant-disjoint folds, the '
                             'same heads (ridge, alpha 100, on standardised training-fold values, class-balanced except '
                             'on BETA; idle: a per-person logistic head with a calibration-only rule and a two-in-a-row '
                             'trigger) and the same scoring code. The encoder was frozen, and only recorded channels '
                             'were fed.'),
            'interval': ('Descriptive 95% participant bootstrap of the equal-participant mean, from each run itself '
                         '(10,000 draws; seed 20260919, BETA 20260912). It ignores cross-validation dependence and '
                         'carries no multiplicity correction.'),
            'reading_rule': ('Rows are grouped by family, never ranked. EEGPT is called above or below a published row '
                             'only when their marginal 95% intervals do not overlap, and the gap between the intervals '
                             'is given; several gaps are narrow.'),
            'chance': 'An interval that includes the protocol’s chance level is flagged on its cell; idle has no chance level.',
            'no_rerun': ('Nothing was re-run for this release: no encoder was loaded, no head refitted and no GPU '
                         'used. The cells are the runs’ recorded aggregates, recomputed read-only from the saved '
                         'predictions and equal to every recorded copy.'),
        },
        'protocols': protocols,
        'cells': out_cells,
        'footnotes': notes,
        'comparisons': cmp_block,
        'pretraining_exposure': exposure_block,
        'pretraining_attribution': attr,
        'directory_status': {
            'name': 'EEGPT', 'suggested_status': 'Evaluated',
            'released_status': next(m for m in mvp['models'] if m['name'] == 'EEGPT')['status'],
            'note': ('Evaluated as a frozen encoder on the eight core protocols, in the same runs as the published '
                     'LaBraM rows and, except on idle, the CBraMod rows, and in one pilot comparison outside every '
                     'leaderboard. The checkpoint’s licence remains unresolved, and no original or converted weights '
                     'are distributed; Apache-2.0 covers the repository’s code only.'),
        },
        'pilot_comparison': {'file': 'pilot-studies-update.json', 'result': 'orthosis-eegpt-vs-58ch', 'leaderboard': False,
                             'same_checkpoint': True},
        'release_record': {
            'date': rr['date'], 'decided': ['2026-10-12', '2026-10-13'], 'decision': rr['decision'], 'rights': rr['rights'],
            'eeg_dino': rr['eegDino'], 'attribution_audit_label': rr['attributionAuditLabel'],
            'repository_records': rr['repositoryRecords'],
            'repository_protocols': ['mi-rest', 'arithmetic-rest', 'beta-8ch', 'beta-4ch'],
        },
        'required_limitations': [
            'One fixed recipe: the frozen encoder with the site’s fixed readout, the same as for the published LaBraM '
            'and CBraMod rows, not the authors’ downstream probe. Scores are not EEGPT’s ceiling.',
            f'Small cohorts (motor imagery {people["mi-rest"]} people, P300 {people["p300-target"]}, sleep '
            f'{people["sleep-scalp"]}, idle {people["idle"]}); intervals are descriptive participant bootstraps that '
            'ignore cross-validation dependence and carry no multiplicity correction.',
            'Rows are grouped by family, never ranked. EEGPT is above or below a published row only where the marginal '
            'intervals do not overlap, and several of those gaps are narrow; each is given in percentage points.',
            'Balanced or class-matched designs (P300, semantic target, motor imagery against rest, sampled sleep epochs) '
            'are method comparisons, not detection, false-alarm or latency estimates for real use.',
            'New people, same task and recording setup only: not cross-day, cross-device or cross-dataset evidence; no '
            'deployment or clinical claim.',
            f'Pretraining exposure, as the authors’ published pretraining list shows it (checked {EXPOSURE_CHECKED}): '
            'none of the seven core datasets is in it. A dataset absent from a list is not proof that its recordings '
            'were never seen; BETA’s relation to the Tsinghua benchmark in that list is stated beside the BETA cells.',
            'Idle is four people, reported as counts and cohort-mean window metrics with no interval; the cue-gated '
            'replay is not natural continuous idle.',
            'No author endorsement is implied. The checkpoint’s licence is unresolved; no original or converted weights '
            'are distributed, and Apache-2.0 covers the repository’s code only.',
        ],
        'audits': {
            'runs': [{'protocols': [p for p in PROTOCOLS if cells[p]['audit_sha256'] == a],
                      'status': 'pass', 'sha256': a,
                      'head_replay_max_error': next(cells[p].get('head_replay_max_error') for p in PROTOCOLS
                                                    if cells[p]['audit_sha256'] == a)}
                     for a in dict.fromkeys(cells[p]['audit_sha256'] for p in PROTOCOLS)],
            'saved_heads_replayed': ('In each parallel-batch run audit and the idle run audit, and for both BETA cells '
                                     'and every attribution package in the read-only check of the review, the saved '
                                     'heads applied to the saved values reproduce the saved scores to floating-point '
                                     'precision.'),
            'review_read_only_check': {'items': rv['coreVerification']['summary']['checks'],
                                       'passed': rv['coreVerification']['summary']['passed']},
            'independent_recomputation': ('A second program, sharing no code with the first, recomputed BETA 4-channel, '
                                          'the EEGMAT attribution contrasts and the idle cell from the saved files: no '
                                          'disagreement.'),
        },
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'run_summary_sha256': {p: cells[p]['summary_sha256'] for p in PROTOCOLS},
            'public_records_sha256': {'beta_summary': manifest['publicRecords']['betaSummary']['sha256'],
                                      'attribution_audit': manifest['publicRecords']['attributionAudit']['sha256']},
            'released_files_unchanged': ['experiments.json', 'deployment-topics.json', 'foundation-models-update.json',
                                         'pilot-studies-update.json'],
        },
    }
    # The pilot comparison is the same checkpoint and stays out of every leaderboard.
    pr = pilot['results']['orthosis-eegpt-vs-58ch']
    require(pr['leaderboard'] is False and pilot['datasets'][pr['dataset']]['publication'] == 'released'
            and pr['model']['checkpoint']['sha256'] == model['checkpoint']['sha256'], 'the pilot comparison changed')
    require(any('EEG-DINO' == n['model'] and 'catalogue only' in n['reason']
                for n in fm['results']['foundation-models-v9']['not_run']), 'the EEG-DINO decision changed')

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 3, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    weights_not_apache(payload)
    validate_public(payload)
    # By value: nothing per person, no per-seed random-initialisation score, no duration-group summary.
    published = set(floats(payload))
    withheld = withheld_values(docs)
    leaked = [v for v in withheld if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    return payload


def withheld_values(docs):
    """Figures the sources hold that this release does not publish."""
    out = set()
    summary = docs['runs']['idle']['summary'][0]
    for r in summary['results']:          # EEGPT's per-person idle results
        if r['model'] == 'EEGPT':   # (thresholds and delays are values of the published grids, not checkable by value)
            out |= {r[k] for k in ('idle_false_trigger_fraction', 'mi_detection_fraction',
                                   'descriptive_false_triggers_per_scripted_idle_minute')}
    audit = docs['public']['attributionAudit'][0]
    for p in audit['packages']:
        if p['condition'].startswith(f'{MODEL}-random-'):
            out.add(p['mean_balanced_accuracy'])
    for r in docs['public']['betaSummary'][0]['results']:
        if r['model'] == MODEL:
            out |= {r['short_duration_group_balanced_accuracy'], r['long_duration_group_balanced_accuracy']}
    for c in docs['review']['coreVerification']['attribution_contrasts']:
        if c['model'] == MODEL:
            out.add(c['random_seed_sample_sd'])
            out |= set(c['random_seed_bas'])
    return out - TRIVIAL


def input_refs(manifest):
    refs = []

    def walk(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v:
                refs.append(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(manifest)
    return refs


def inputs_available():
    """Whether the pinned inputs are on this machine. They are not in the public repository: the run records carry
    private storage paths and the review folder is local. A clone still checks the served file against the committed
    export audit's hash; only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_eegpt_core_export
    return audit_eegpt_core_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
