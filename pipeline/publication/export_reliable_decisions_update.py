"""Release route 1 of the decision-research roadmap, reliable decisions, as aggregate-only JSON.

When should a decoder decline to decide, and how much is its confidence worth?
Route 1 rescored the saved test outputs of models this site already publishes —
no classifier was retrained, and every full-coverage balanced accuracy equals
the published one — under four policies: a fixed threshold on calibrated
confidence, a coverage target, a certified selective risk, and a learned reject
option. It also measured probability quality and what a person-specific
recalibration costs in that person's labels. Primary protocols: EEGMAT
(arithmetic and rest, 36 people) and BETA (eight-channel SSVEP, 70 people);
ds003810 (motor imagery and rest, 10 people) is a crude secondary protocol.

Its own publication boundary, as with every batch. The website input is the
release candidate. Every {source, value} block in it is re-resolved against the
two pinned aggregates; the protocol, its superseded first freeze and both stage-0
audits are pinned and checked; the two independent audits are bound by the
hashes the candidate and the handoff record, never opened, because they carry
private storage paths. What this export refuses:
- per-person and per-fold values: the candidate's person-level percentiles and
  its median temperature over folds, by key, by fragment and by value; how many
  people had nothing accepted is published, which people is not;
- the idle protocol (another unit than the page's idle figures) and every figure
  of the BNCI2015-001 arm (an editorial hold stands);
- a zero-accepted error turned into a number, an interval that does not hold its
  mean, a verdict the interval does not support, a contrast that is not the
  difference of the levels it compares, an accuracy that is not the site's, and
  any page reading the numbers no longer support.

    python3 pipeline/publication/export_reliable_decisions_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261004'
MANIFEST = REVIEW / 'reliable-decisions-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'reliable-decisions-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/reliable-decisions-update.json',
           PROJECT / 'site/public/data/reliable-decisions-update.json')
# The published values route 1's full-coverage accuracies must equal. Released
# files: read, never written.
SITE_MATRIX = PROJECT / 'site/src/data/mvp.json'
SITE_ADAPTATION = PROJECT / 'site/src/data/adaptation-update.json'

ROUTE = 'reliable-decisions'
RUN_ID = 'decision-route1-v1/20261004'
CANDIDATE_STATUS = 'pending user approval'   # the state the candidate was sealed in; the manifest is the approval
RESOLVED = 'difference resolved (paired 95% interval excludes 0)'
UNSTABLE_BELOW = 10
TOL = 1e-12

# Per-person distributions, per-fold values and what the pages leave out on purpose.
REFUSED_KEYS = PER_PERSON_KEYS | {'p10', 'p50', 'p90', 'q1', 'q3', 'minimum', 'maximum', 'range', 'n_defined',
                                  'median_T_over_folds', 'person_spread_10_50_90', 'per_class_acceptance',
                                  'per_class_acceptance_min_median_max', 'reliability_bins_calibrated',
                                  'reliability_bins_raw', 'rc_curve_20', 'brier_decomposition_calibrated',
                                  'ece_equal_width_15', 'environment', 'compute_time', 'idle', 'bnci'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_fold', 'per_class', 'percentile', 'median', 'spread',
                         'participant_id', 'record_id', 'subject', 'prediction', 'probabilities', 'selector_output',
                         'rc_curve', 'reliability_bin', 'private', 'elapsed', 'seconds', 'minutes', 'platform',
                         'basename', 'bnci', 'idle', 'p10', 'p50', 'p90')
# Path roots only: naming this operator's machines or volumes here would itself be the leak.
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', re.IGNORECASE)
# Per-person files and the run's internal log. The reviewed privacy notes name the sources' own
# metadata files (subject-info.csv, participants.tsv) to say they are never published; those stay.
SOURCE_IDS = re.compile(r'\bsub-\d+|\bsubj\d+|\.npz\b|\.edf\b|\.mat\b|\.private\b|DECISIONS\.md', re.IGNORECASE)

PRIMARY = ('arithmetic-rest', 'beta-8ch')
SECONDARY = 'mi-rest'
SOURCE_OF = {'arithmetic-rest': 'eegmat', 'beta-8ch': 'beta', 'mi-rest': 'ds003810'}
PROTOCOL = {
    'arithmetic-rest': {'people': 36, 'outer_folds': 5, 'n': 2160, 'classes': 2, 'unit': 'windows',
                        'methods': ('spectral-ridge', 'eegnet', 'labram-frozen-ce', 'labram-lora-r4')},
    'beta-8ch': {'people': 70, 'outer_folds': 7, 'n': 11200, 'classes': 40, 'unit': 'trials',
                 'methods': ('cca', 'cbramod', 'eegnet')},
    'mi-rest': {'people': 10, 'outer_folds': 5, 'n': 1200, 'classes': 2, 'unit': 'windows',
                'methods': ('spectral-ridge', 'cbramod', 'eegnet')},
}
# Display labels, and the published value each full-coverage accuracy must equal.
METHOD = {
    'spectral-ridge': ('Spectral ridge', 'matrix', 'spectral-ridge'),
    'eegnet': ('EEGNet', 'matrix', 'eegnet'),
    'cca': ('Standard CCA', 'matrix', 'cca'),
    'cbramod': ('CBraMod', 'matrix', 'cbramod'),
    'labram-frozen-ce': ('LaBraM · head only, encoder frozen', 'adaptation', 'frozen'),
    'labram-lora-r4': ('LaBraM · LoRA rank 4 + head', 'adaptation', 'lora-r4'),
}
ADAPTATION_SEED = 20260922
# The labelled prefix of each new person that the personal temperature is fitted on.
PREFIX = {
    ('arithmetic-rest', 'k5'): ('first 5 windows of each recording, then a one-window gap', 10),
    ('arithmetic-rest', 'k10'): ('first 10 windows of each recording, then a one-window gap', 20),
    ('beta-8ch', 'prefix'): ('block 1 (one trial per target)', 40),
}
TEST_COVERAGES = ('0.5', '0.7', '0.8', '0.9')

PRIMARY_AUDIT_FAILED = 'run-result description of degenerate R1 temperatures matches the computation'
SECONDARY_AUDIT_CHECKS = 15

DESIGN = {
    'inputs': ('The saved test scores of models this site already publishes, on the same people and outer folds. No '
               'outer-test score was recomputed and no classifier was retrained; temperature scaling keeps the '
               'predicted label, so every full-coverage balanced accuracy equals the published one.'),
    'calibration_data': ('Participant-disjoint inner out-of-fold scores. In each outer fold the training people form '
                         'four inner groups, and each group is scored by a model trained on the other three. No test '
                         'person is in any calibration set. Inner models see about three quarters of the training '
                         'people, so they may be less confident than the full model whose scores are tested; this '
                         'approximation is part of every calibrated figure.'),
    'policies': {
        'fixed_cutoff': 'F: accept a trial when its calibrated top-class probability is at least 0.8 (temperature '
                        'scaling fitted on the calibration scores).',
        'coverage_target': 'S-cov: accept the most confident trials, with the cut-off set from calibration quantiles '
                           'so that 80% of trials should be accepted.',
        'risk_certification': 'S-risk: selection with guaranteed risk (SGR, delta 0.05) on the calibration scores, '
                              'certifying a selective error no higher than r*, here the relative target: half the '
                              'calibration error. A fold where nothing can be certified accepts nothing.',
        'learned_reject': 'L: an L2 logistic selector on the raw top-1 and top-2 scores and their margin, plus 16 '
                          'principal components of a model-independent spectral descriptor (C = 1, untuned), '
                          'trained on the calibration scores to predict which trials the classifier gets wrong.',
        'ranking': 'S ranks trials by calibrated top-class probability, L by the selector. Error at a test coverage '
                   'takes the most confident share of the test trials under that ranking, so it measures the '
                   'ranking alone.',
        'recalibration': 'R0: the population temperature, no label from the new person. R1: a personal temperature '
                         'fitted on a labelled prefix of the new person\'s own trials. R-unl: the population '
                         'temperature, with only the coverage cut-off re-set from the same prefix, unlabelled. All '
                         'three are scored on the same remaining trials.',
    },
    'uncertainty': ('Paired participant-cluster bootstrap over the test people of a protocol: 2,000 resamples, seed '
                    '20261002, 95% percentile intervals, the same resampled people for every method, policy and '
                    'arm. No multiplicity correction.'),
    'wording_rule': ('A contrast is called a difference only when its paired 95% interval excludes 0; otherwise "no '
                     'difference resolved". No ranking where intervals overlap. Descriptive levels are never called '
                     'differences.'),
    'unstable_below_accepted': UNSTABLE_BELOW,
    'zero_accepted': 'A policy that accepts nothing has no error rate: null, never zero.',
    'freeze': ('The protocol was frozen and amended once (A1) before any stage-1 computation. Thresholds, '
               'temperatures and selectors were written and hashed before scoring; outer-test labels were masked '
               'during stage 1; nothing was selected by test results; degenerate fits were flagged and kept.'),
}
# Titles and authors checked against each arXiv record on 2026-10-04.
LITERATURE = [
    {'id': 'temperature-scaling', 'cite': 'Guo, Pleiss, Sun & Weinberger, ICML 2017 · On calibration of modern neural networks',
     'url': 'https://arxiv.org/abs/1706.04599'},
    {'id': 'sgr', 'cite': 'Geifman & El-Yaniv, 2017 · Selective classification for deep neural networks',
     'url': 'https://arxiv.org/abs/1705.08500'},
    {'id': 'selectivenet', 'cite': 'Geifman & El-Yaniv, ICML 2019 · SelectiveNet: a deep neural network with an integrated reject option',
     'url': 'https://proceedings.mlr.press/v97/geifman19a.html'},
    {'id': 'aurc', 'cite': 'Geifman, Uziel & El-Yaniv, ICLR 2019 · Bias-reduced uncertainty estimation for deep neural classifiers (AURC)',
     'url': 'https://arxiv.org/abs/1805.08206'},
    {'id': 'equal-mass-ece', 'cite': 'Nixon et al., 2019 · Measuring calibration in deep learning',
     'url': 'https://arxiv.org/abs/1904.01685'},
    {'id': 'ood-mi', 'cite': 'Mulder, Valdenegro-Toro, Sburlea & de Jong, 2026 · The challenge of out-of-distribution detection in motor imagery BCIs',
     'url': 'https://arxiv.org/abs/2603.13324'},
]


# ---------------------------------------------------------------------------- helpers
def close(a, b, label, tol=TOL):
    require(isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float))
            and not isinstance(b, bool) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def finite(*values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def resolve(aggregates, source):
    """A JSON pointer into one of the two pinned aggregates."""
    name, _, pointer = source.partition('#')
    require(name in aggregates, f'a reference into an unpinned file: {source}')
    node = aggregates[name]
    for tok in pointer.split('/')[1:] if pointer else []:
        tok = tok.replace('~1', '/').replace('~0', '~')
        require(isinstance(node, dict) and tok in node, f'a reference that does not resolve: {source}')
        node = node[tok]
    return node


def same(value, source):
    """Equal, or for a dict a key subset of the source object, recursively; booleans are not numbers."""
    if isinstance(value, dict):
        return isinstance(source, dict) and all(k in source and same(v, source[k]) for k, v in value.items())
    if isinstance(value, list):
        return isinstance(source, list) and len(value) == len(source) and all(same(a, b) for a, b in zip(value, source))
    if isinstance(value, bool) or isinstance(source, bool):
        return value is source
    return value == source


def reresolve(candidate, aggregates):
    """Every {source, value} block of the candidate is the aggregate's value at that pointer."""
    seen = 0

    def walk(node, trail):
        nonlocal seen
        if isinstance(node, dict):
            if isinstance(node.get('source'), str) and node['source'].startswith('aggregate-') and 'value' in node:
                require(same(node['value'], resolve(aggregates, node['source'])),
                        f'{trail}: the value differs from {node["source"]}')
                seen += 1
            for k, v in node.items():
                walk(v, f'{trail}/{k}')
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f'{trail}[{i}]')
    walk(candidate, '$')
    for finding in candidate['key_findings']:
        for ref in finding['refs']:
            resolve(aggregates, ref)
    return seen


def val(block, label):
    require(isinstance(block, dict) and 'source' in block and 'value' in block, f'{label}: not a traced block')
    return block['value']


def interval(v, label):
    ci = v.get('ci95')
    require(isinstance(ci, list) and len(ci) == 2 and finite(*ci) and ci[0] <= ci[1], f'{label}: no two-sided interval')
    require(finite(v['point']) and ci[0] <= v['point'] <= ci[1], f'{label}: the interval does not contain its point')
    return [ci[0], ci[1]]


def level(v, point, label, lo=None, hi=None):
    """A descriptive level with its bootstrap interval; it equals the full-sample value it describes."""
    require(v['kind'] == 'descriptive' and v['excludes_zero'] is None, f'{label}: a level must be descriptive')
    close(v['point'], point, label)
    iv = interval(v, label)
    require((lo is None or iv[0] >= lo) and (hi is None or iv[1] <= hi), f'{label}: the interval leaves the range')
    return {'mean': point, 'interval_95': iv}


def difference(block, label, expected=None, tol=1e-9):
    """A pre-declared paired contrast. Its verdict follows from its interval and from nothing else."""
    v = val(block, label)
    require(v['kind'] == 'difference', f'{label}: not a difference')
    require(v['undefined_draws'] == 0 and v['defined_draws'] == 2000, f'{label}: not every bootstrap draw is defined')
    require(not v.get('point_unstable') and not v.get('unstable_draws'), f'{label}: unstable, so no verdict')
    iv = interval(v, label)
    excludes = iv[0] > 0 or iv[1] < 0
    require(v['excludes_zero'] is excludes, f'{label}: excludes_zero does not follow from the interval')
    verdict = block.get('verdict', '')
    require((verdict == RESOLVED) if excludes else verdict.startswith('no difference resolved'),
            f'{label}: the verdict "{verdict}" does not follow from the interval')
    if expected is not None:
        close(v['point'], expected, f'{label}: the contrast is not the difference of its levels', tol)
    return {'mean': v['point'], 'interval_95': iv, 'excludes_zero': excludes}


def selected(op, n, people, label, cov_iv=None, err_iv=None):
    """An operating point: accepted of n, its coverage, and its selective error, which needs something accepted."""
    require(op['n'] == n and count(op['accepted']) and 0 <= op['accepted'] <= n, f'{label}: accepted is not a count of {n}')
    close(op['coverage'], op['accepted'] / n, f'{label}: coverage is not accepted / n')
    require(op['unstable'] is (op['accepted'] < UNSTABLE_BELOW), f'{label}: the unstable flag does not follow the count')
    out = {'n': n, 'accepted': op['accepted'], 'coverage': op['coverage']}
    if cov_iv is not None:
        out['coverage_interval_95'] = level(cov_iv, op['coverage'], label + ' coverage', 0.0, 1.0)['interval_95']
    if op['accepted'] == 0:
        require(op['selective_error'] is None, f'{label}: nothing accepted, yet an error rate (a null turned into a number)')
        out.update(selective_error=None, selective_error_status='not defined: nothing accepted', unstable=True)
        if err_iv is not None:
            require(err_iv['point'] is None and err_iv.get('ci95') is None
                    and err_iv.get('point_status') == 'not defined: zero accepted', f'{label}: an interval without anything accepted')
    else:
        e = op['selective_error']
        require(finite(e) and 0.0 <= e <= 1.0, f'{label}: an error outside [0, 1]')
        wrong = e * op['accepted']
        require(abs(wrong - round(wrong)) < 1e-9, f'{label}: the error is not a whole count of accepted {label}')
        out.update(selective_error=e, accepted_wrong=round(wrong), unstable=op['unstable'])
        if err_iv is not None:
            require(err_iv['point_accepted'] == op['accepted'], f'{label}: the error interval counts other trials')
            out['selective_error_interval_95'] = level(err_iv, e, label + ' error', 0.0, 1.0)['interval_95']
    if 'zero_coverage_people' in op:
        z = op['zero_coverage_people']
        require(count(z) and 0 <= z <= people, f'{label}: people with nothing accepted is not a count of {people}')
        require(z == people if op['accepted'] == 0 else z < people, f'{label}: people with nothing accepted disagrees '
                'with the pooled count')
        out['people_with_nothing_accepted'] = z
    return out


def site_balanced_accuracy(matrix, adaptation, protocol, method):
    """The published value route 1's full-coverage accuracy must equal, and where it is published."""
    _, kind, key = METHOD[method]
    if kind == 'matrix':
        track = next(t for t in matrix['tracks'] if t['id'] == protocol)
        row = next(r for r in track['rows'] if r['id'] == key)
        return row['y'] / 100, {'file': 'experiments.json', 'release': matrix['releaseId'], 'track': protocol,
                                'row': row['name']}
    require(protocol == 'arithmetic-rest', f'{method}: LaBraM arms exist on EEGMAT only')
    res = adaptation['results']['eegmat-labram-adaptation']
    arm = next(a for a in res['arms'] if a['id'] == key)
    seed = next(s for s in arm['balanced_accuracy']['per_seed_means'] if s['seed'] == ADAPTATION_SEED)
    return seed['mean'], {'file': 'adaptation-update.json', 'release': adaptation['release_id'], 'arm': key,
                          'seed': ADAPTATION_SEED}


# ---------------------------------------------------------------------------- per method
def method_block(protocol, mid, m, contrasts, matrix, adaptation, stage0, primary=True):
    design = PROTOCOL[protocol]
    n, people, folds = design['n'], design['people'], design['outer_folds']
    where = f'{protocol}/{mid}'
    counts = val(m['counts'], where + ' counts')
    require(counts['n_trials'] == n and counts['n_people'] == people and counts['primary_arm'] == 'cross-fit',
            f'{where}: another cohort or arm')
    fba = val(m['full_coverage_balanced_accuracy'], where)
    require(fba['balanced_accuracy_equals_published'] is True, f'{where}: the accuracy is not the published one')
    close(fba['balanced_accuracy'], fba['published_balanced_accuracy'], where + ' accuracy', 1e-12)
    site_value, site_ref = site_balanced_accuracy(matrix, adaptation, protocol, mid)
    close(fba['published_balanced_accuracy'], site_value, where + ': the site value')
    audited = stage0['published_balanced_accuracy']['methods'][f'{protocol}/{mid}']
    require(audited['pass'] is True, f'{where}: the stage-0 audit did not confirm the published accuracy')
    close(audited['published'], site_value, where + ': the stage-0 audit read another value')

    iv = val(m['intervals'], where + ' intervals')
    ops = {k: val(b, f'{where} {k}') for k, b in m['operating_points'].items()}
    flags = val(m['flags'], where + ' flags')
    require(flags['outer_folds'] == folds, f'{where}: another number of outer folds')
    accept_all = val(m['baselines'], where)['accept_all']
    require(accept_all['accepted'] == n and accept_all['coverage'] == 1.0, f'{where}: accept-all is not everything')
    # Balanced or uniform by design: accepting everything errs on exactly one minus the balanced accuracy.
    close(accept_all['selective_error'], 1 - fba['balanced_accuracy'], where + ' accept-all error', 1e-12)

    out = {
        'id': mid, 'label': METHOD[mid][0], 'seed': counts['seed'],
        'balanced_accuracy': fba['balanced_accuracy'], 'site_value': site_ref,
        'error_accepting_everything': accept_all['selective_error'],
        'fixed_cutoff': {'cutoff': 0.8, **selected(ops['F-cal@0.8'], n, people, where + ' F-cal@0.8',
                                                   iv['F-cal@0.8:coverage'], iv['F-cal@0.8:error'])},
    }
    rk = {}
    for key, name in (('S (calibrated MSP)', 'S'), ('L (selector)', 'L')):
        r = val(m['ranking'][key], f'{where} {name}')
        at = r['error_at_matched_test_coverage']
        require(sorted(at) == list(TEST_COVERAGES), f'{where} {name}: other test coverages')
        points = []
        for c in TEST_COVERAGES:
            p = at[c]
            close(p['coverage'], float(c), f'{where} {name} {c}')
            require(p['accepted'] == round(float(c) * n) and not p['unstable'] and finite(p['selective_error']),
                    f'{where} {name} {c}: not the share of test trials it names')
            points.append({'coverage': p['coverage'], 'accepted': p['accepted'], 'selective_error': p['selective_error']})
        rk[name] = r
        out[f'ranking_{name}'] = {
            'aurc': level(iv[f'aurc_{name}'], r['aurc'], f'{where} AURC {name}', 0.0, 1.0),
            'error_at_80': level(iv[f'err08_{name}'], at['0.8']['selective_error'], f'{where} err@0.8 {name}', 0.0, 1.0),
            'error_at_test_coverage': points,
        }
    if primary:
        out['coverage_target'] = {'target': 0.8, **selected(ops['S-cov@0.8'], n, people, where + ' S-cov@0.8',
                                                            iv['S-cov@0.8:coverage'], iv['S-cov@0.8:error'])}
        require(ops['S-cov@0.8']['target_coverage'] == 0.8, f'{where}: another coverage target')
    # The learned reject option against the calibrated confidence of the same classifier.
    out['learned_minus_confidence'] = {
        'aurc': difference(contrasts[f'C1:{mid}:AURC(L)-AURC(S)'], f'{where} C1',
                           rk['L']['aurc'] - rk['S']['aurc']),
        'error_at_80': difference(contrasts[f'C2:{mid}:err@0.8(L)-err@0.8(S)'], f'{where} C2',
                                  rk['L']['error_at_matched_test_coverage']['0.8']['selective_error']
                                  - rk['S']['error_at_matched_test_coverage']['0.8']['selective_error']),
    }
    # Certified selective risk at the relative target, and its measured failures.
    sr = ops['S-risk@relative']
    certified = flags['certified_folds_by_risk_threshold']['S-risk@relative']
    require(sr['certified_folds'] == certified and count(certified) and 0 <= certified <= folds,
            f'{where}: certified folds disagree')
    require(certified + sr['folds_not_defined'] == folds, f'{where}: certified + not certified is not every fold')
    require((sr['accepted'] == 0) is (certified == 0), f'{where}: a fold was certified yet nothing accepted, or the reverse')
    require(count(sr['folds_violating']) and 0 <= sr['folds_violating'] <= certified, f'{where}: folds over r*')
    risk = {'delta': 0.05, 'target': 'relative', 'outer_folds': folds, 'certified_folds': certified,
            'folds_over_target': sr['folds_violating'],
            **selected(sr, n, people, where + ' S-risk', iv['S-risk@relative:coverage'] if primary else None,
                       iv['S-risk@relative:error'] if primary else None)}
    c6 = contrasts[f'C6:{mid}:S-risk(rel) error - r*']
    if sr['accepted'] == 0:
        require(sr['r_star_weighted'] is None, f'{where}: a target without anything accepted')
        v = val(c6, where + ' C6')
        require(v['point'] is None and v.get('ci95') is None and v['status'] == 'not defined: zero accepted',
                f'{where}: C6 must be not defined when nothing is accepted')
        risk.update(target_weighted=None, error_minus_target=None, error_minus_target_status='not defined: nothing accepted')
    else:
        require(finite(sr['r_star_weighted']) and 0 < sr['r_star_weighted'] < 1, f'{where}: r*')
        risk['target_weighted'] = sr['r_star_weighted']
        risk['error_minus_target'] = difference(c6, where + ' C6', sr['selective_error'] - sr['r_star_weighted'])
        require(val(c6, where)['point_accepted'] == sr['accepted'], f'{where}: C6 counts other trials')
    if primary:
        ab = ops['S-risk@abs-0.1']
        require(ab['certified_folds'] == flags['certified_folds_by_risk_threshold']['S-risk@abs-0.1'], f'{where}: abs 0.1')
        risk['absolute_target_0_1'] = {'certified_folds': ab['certified_folds'], 'folds_over_target': ab['folds_violating']}
    out['risk_certification'] = risk
    if not primary:
        return out

    # Probability quality at full coverage.
    cal = val(m['probability_quality_calibrated'], where + ' calibrated')
    raw = val(m['probability_quality_raw'], where + ' raw')
    quality = {'calibrated': {
        'nll': level(iv['nll_cal'], cal['nll'], where + ' NLL'),
        'ece': level(iv['ece_cal'], cal['ece_equal_mass_15'], where + ' ECE', 0.0, 1.0),
        'brier': level(iv['brier_cal'], cal['brier'], where + ' Brier', 0.0, 2.0),
    }}
    close(cal['accuracy'], 1 - accept_all['selective_error'], where + ' calibrated accuracy')
    if isinstance(raw, str):
        require(raw.startswith('not applicable'), f'{where}: raw quality is neither a value nor not applicable')
        require('nll_raw' not in iv, f'{where}: a raw interval without raw probabilities')
        quality['raw'] = None
        quality['raw_status'] = 'not applicable: this score type has no raw probability'
    else:
        quality['raw'] = {'nll': level(iv['nll_raw'], raw['nll'], where + ' raw NLL'),
                          'ece': level(iv['ece_raw'], raw['ece_equal_mass_15'], where + ' raw ECE', 0.0, 1.0)}
    temp = val(m['temperature'], where + ' temperature')
    require(count(temp['degenerate_temperatures'])
            and temp['degenerate_temperatures'] == len(flags['population_temperature_degenerate_folds']),
            f'{where}: degenerate population temperatures disagree')
    quality['degenerate_population_temperature_folds'] = temp['degenerate_temperatures']
    out['probability_quality'] = quality

    # Recalibration: what a personal temperature changes, and the labels it costs.
    recal = []
    for key, prefix in m['recalibration'].items():
        description, labels = PREFIX[(protocol, key)]
        arms = val(prefix['arms'], f'{where} {key}')
        require(arms['labels_per_new_person'] == {'R0': 0, 'R-unl': 0, 'R1': [labels]},
                f'{where} {key}: another label cost than {labels} per new person')
        c5 = prefix['C5']
        r0, r1, ru = arms['R0'], arms['R1'], arms['R-unl']
        degenerate = flags['recalibration_R1_per_person_temperature'][key]
        require(degenerate['people'] == people and count(degenerate['degenerate_R1_temperatures'])
                and 0 <= degenerate['degenerate_R1_temperatures'] <= people, f'{where} {key}: degenerate personal temperatures')
        recal.append({
            'prefix': key, 'labelled_prefix': description, 'labels_per_new_person': labels,
            'scored_trials': arms['matched_remaining_trials'],
            'people_with_degenerate_personal_temperature': degenerate['degenerate_R1_temperatures'],
            'nll_change': difference(c5['nll R1-R0'], f'{where} {key} NLL', r1['nll'] - r0['nll']),
            'ece_change': difference(c5['ece R1-R0'], f'{where} {key} ECE', r1['ece_equal_mass_15'] - r0['ece_equal_mass_15']),
            'aurc_change': difference(c5['aurc R1-R0'], f'{where} {key} AURC', r1['aurc'] - r0['aurc']),
            'unlabelled_cutoff_gap_change': difference(c5['|S-cov gap| R-unl-R0'], f'{where} {key} R-unl gap',
                                                       abs(ru['S-cov@0.8']['coverage_gap']) - abs(r0['S-cov@0.8']['coverage_gap'])),
        })
        # What remains after the prefix: on EEGMAT the next window of each of a person's two recordings is also
        # left out, as a gap; BETA's block 1 is the whole prefix.
        removed = labels + 2 if protocol == 'arithmetic-rest' else labels
        require(arms['matched_remaining_trials'] == n - removed * people,
                f'{where} {key}: the scored trials are not what remains after the prefix')
    out['recalibration'] = recal
    return out


# ---------------------------------------------------------------------------- per protocol
def protocol_block(protocol, block, record, matrix, adaptation, stage0):
    design = PROTOCOL[protocol]
    d = val(block['design'], protocol + ' design')
    require(d['people'] == design['people'] and d['outer_folds'] == design['outer_folds'] and d['primary_contrasts'] is True,
            f'{protocol}: another design')
    require(list(block['methods']) == list(design['methods']), f'{protocol}: other methods')
    contrasts = block['contrasts']
    methods = [method_block(protocol, mid, block['methods'][mid], contrasts, matrix, adaptation, stage0)
               for mid in design['methods']]
    by_id = {m['id']: m for m in methods}
    ids = design['methods']
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pairs.append({'a': a, 'b': b, **difference(contrasts[f'C3:{a} minus {b}:F-cal@0.8 coverage'],
                                                       f'{protocol} C3 {a} - {b}',
                                                       by_id[a]['fixed_cutoff']['coverage'] - by_id[b]['fixed_cutoff']['coverage'])})
    cstar = val(contrasts['C3:c* = min over methods of F-cal@0.8 coverage'], protocol + ' c*')
    close(cstar['point'], min(m['fixed_cutoff']['coverage'] for m in methods), protocol + ' c*')
    common_n = math.ceil(round(cstar['point'] * design['n'], 9))
    common = {'coverage': cstar['point'], 'coverage_interval_95': interval(cstar, protocol + ' c*'),
              'accepted': common_n, 'unstable': common_n < UNSTABLE_BELOW}
    if common['unstable']:
        common['verdict'] = 'unstable: fewer than 10 accepted trials at the common coverage, so no verdict'
        for mid in ids:
            v = val(contrasts[f'C3(b):{mid}:S error at common coverage c*'], protocol)
            require(v['point_unstable'] is True and v['point_accepted'] == common_n, f'{protocol} {mid}: c* unstable flag')
    else:
        common['errors'] = []
        for mid in ids:
            v = val(contrasts[f'C3(b):{mid}:S error at common coverage c*'], f'{protocol} {mid} c*')
            require(v['point_accepted'] == common_n and v['point_unstable'] is False, f'{protocol} {mid}: c* count')
            common['errors'].append({'id': mid, **level(v, v['point'], f'{protocol} {mid} error at c*', 0.0, 1.0)})
        err = {e['id']: e['mean'] for e in common['errors']}
        common['differences'] = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                common['differences'].append({'a': a, 'b': b, **difference(
                    contrasts[f'C3:{a} minus {b}:S error at common coverage c*'], f'{protocol} c* {a} - {b}',
                    err[a] - err[b])})
    out = {
        'protocol': protocol, 'dataset': record['name'], 'role': 'primary', 'task': record['task'],
        'people': design['people'], 'outer_folds': design['outer_folds'], 'classes': design['classes'],
        'test_items': design['n'], 'unit': design['unit'],
        'boundary': val(block['boundary'], protocol + ' boundary'),
        'methods': methods,
        'fixed_cutoff_coverage_differences': pairs,
        'common_coverage': common,
        'rights': rights(record) | {'coreTrack': record['coreTrack']},
    }
    if protocol == 'arithmetic-rest':
        f, l = by_id['labram-frozen-ce'], by_id['labram-lora-r4']
        q = lambda m, k, which: m['probability_quality'][which][k]['mean']
        out['lora_minus_head_only'] = {
            'nll_calibrated': difference(contrasts['C4:nll_cal LoRA-r4 minus frozen-CE'], 'C4 NLL cal',
                                         q(l, 'nll', 'calibrated') - q(f, 'nll', 'calibrated')),
            'ece_calibrated': difference(contrasts['C4:ece_cal LoRA-r4 minus frozen-CE'], 'C4 ECE cal',
                                         q(l, 'ece', 'calibrated') - q(f, 'ece', 'calibrated')),
            'nll_raw': difference(contrasts['C4:nll_raw LoRA-r4 minus frozen-CE'], 'C4 NLL raw',
                                  q(l, 'nll', 'raw') - q(f, 'nll', 'raw')),
            'ece_raw': difference(contrasts['C4:ece_raw LoRA-r4 minus frozen-CE'], 'C4 ECE raw',
                                  q(l, 'ece', 'raw') - q(f, 'ece', 'raw')),
            'head_only_degenerate_population_temperature_folds':
                f['probability_quality']['degenerate_population_temperature_folds'],
        }
    return out


def mi_rest_block(block, record, matrix, adaptation, stage0):
    design = PROTOCOL[SECONDARY]
    d = val(block['design'], 'mi-rest design')
    require(d['people'] == design['people'] and d['primary_contrasts'] is False, 'mi-rest: it must stay without primary contrasts')
    methods = [method_block(SECONDARY, mid, block['methods'][mid], block['contrasts'], matrix, adaptation, stage0, primary=False)
               for mid in design['methods']]
    for m in methods:
        m.pop('ranking_S'), m.pop('ranking_L')
        r = m['risk_certification']
        require(r['certified_folds'] == 0 and r['accepted'] == 0, 'mi-rest: the pages say S-risk accepted nothing here')
    return {'protocol': SECONDARY, 'dataset': record['name'], 'role': 'secondary, crude', 'task': record['task'],
            'people': design['people'], 'outer_folds': design['outer_folds'], 'classes': design['classes'],
            'test_items': design['n'], 'unit': design['unit'],
            'boundary': val(block['boundary'], 'mi-rest boundary'), 'label': 'crude: ten people, two per test fold',
            'methods': methods, 'rights': rights(record) | {'coreTrack': record['coreTrack']}}


# ---------------------------------------------------------------------------- secondary arms
def seeds_block(arm):
    rows = []
    for protocol in PRIMARY:
        p = arm['protocols'][protocol]
        for key, m in p['methods'].items():
            if key.endswith('@ensemble'):
                continue                       # an ensemble has no selector, so no learned-reject contrast
            model, _, seed = key.partition('@seed-')
            require(model in METHOD and seed.isdigit(), f'seeds: unexpected row {key}')
            c = p['contrasts']
            rows.append({'protocol': protocol, 'method': model, 'label': METHOD[model][0], 'seed': int(seed),
                         'learned_minus_confidence': {
                             'aurc': difference(c[f'C1:{key}:AURC(L)-AURC(S)'], f'seeds {protocol} {key} C1'),
                             'error_at_80': difference(c[f'C2:{key}:err@0.8(L)-err@0.8(S)'], f'seeds {protocol} {key} C2')}})
    return {'description': ('Every saved secondary seed of the trained methods, each with its own cross-fit, '
                            'temperature, cut-offs and selector, scored on that seed\'s saved test predictions. '
                            'Seeds are never treated as people; no contrast is drawn between seeds or with the '
                            'primary row.'),
            'rows': rows}


def risk_arm_block(arm, name, description):
    rows = []
    for protocol in PRIMARY:
        for key, m in arm['protocols'][protocol]['methods'].items():
            model, _, variant = key.partition('@')
            require(model in METHOD, f'{name}: unexpected row {key}')
            op = val(m['operating_points']['S-risk@relative'], f'{name} {key}')
            folds = PROTOCOL[protocol]['outer_folds']
            require(count(op['certified_folds']) and op['certified_folds'] + op['folds_not_defined'] == folds
                    and 0 <= op['folds_violating'] <= op['certified_folds'], f'{name} {key}: fold counts')
            require((op['accepted'] == 0) is (op['certified_folds'] == 0), f'{name} {key}: certified yet nothing accepted')
            rows.append({'protocol': protocol, 'method': model, 'label': METHOD[model][0], 'variant': variant,
                         'outer_folds': folds, 'certified_folds': op['certified_folds'],
                         'folds_over_target': op['folds_violating']})
    return {'description': description, 'published': 'risk-certification fold counts only; never an accuracy',
            'rows': rows}


def ljoint_block(arm):
    rows = []
    for protocol in PRIMARY:
        c = arm['protocols'][protocol]['contrasts']
        rows.append({'protocol': protocol, 'learned_minus_confidence': {
            'aurc': difference(c['C1:eegnet-selectivenet:AURC(L)-AURC(S)'], f'L-joint {protocol} C1'),
            'error_at_80': difference(c['C2:eegnet-selectivenet:err@0.8(L)-err@0.8(S)'], f'L-joint {protocol} C2')}})
    check = val(arm['paper_check'], 'L-joint paper check')
    require('geifman19a' in check['source'], 'L-joint: the loss was not checked against the paper')
    return {'description': ('Exploratory. A SelectiveNet-style EEGNet (alpha 0.5, lambda 32, target coverage 0.8) '
                            'trained with its own selection head g. Within the same model, g is compared with the '
                            'calibrated confidence of its own classifier head; positive means g is worse. It changes '
                            'the classifier, so its accuracy is not the site\'s and is not published here, and it is '
                            'never compared with the primary learned-reject contrasts.'),
            'source': 'https://proceedings.mlr.press/v97/geifman19a.html', 'rows': rows}


# ---------------------------------------------------------------------------- boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source file or participant identifier in export: {trail}')
        require(not PRIVATE_TOKENS.search(value), f'private host or path in export: {trail}')


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, float):
        yield value


DESIGN_CONSTANTS = {0.05, 0.5, 0.7, 0.8, 0.9}


def pooled_operating_points(result):
    """Every published operating point: accepted of n, with its coverage checked to be accepted / n."""
    for p in [*result['protocols'].values(), result['robustness']['mi_rest']]:
        for m in p['methods']:
            for key in ('fixed_cutoff', 'coverage_target', 'risk_certification'):
                if key in m:
                    yield m[key]
            for r in ('ranking_S', 'ranking_L'):
                yield from m.get(r, {}).get('error_at_test_coverage', [])


def withheld_values(candidate):
    """The person percentiles and the per-fold median temperatures the candidate carries: refused by value too."""
    out = []
    for section in (candidate['primary'],):
        for protocol in section.values():
            for m in protocol['methods'].values():
                spread = m.get('person_spread_10_50_90', {}).get('value', {})
                for q in spread.values():
                    if isinstance(q, dict):
                        out += [q[k] for k in ('p10', 'p50', 'p90') if isinstance(q.get(k), float)]
                out.append(m['temperature']['value']['median_T_over_folds'])
    return [v for v in out if v not in (0.0, 1.0)]


def bindings(route, candidate, aggregates, protocol_sha, superseded_sha, stage0, stage0_sha, stage0s, stage0s_sha,
             handoff):
    """The candidate names what it was built from; each named file is the pinned one."""
    require(candidate['run_id'] == route['runId'] == aggregates['aggregate-primary.json']['run_id']
            == aggregates['aggregate-secondary.json']['run_id'] == RUN_ID, 'another run')
    for name in aggregates:
        key = 'aggregatePrimary' if 'primary' in name else 'aggregateSecondary'
        require(candidate['sources'][name]['sha256'] == route[key]['sha256'], f'the candidate names another {name}')
        require(aggregates[name]['protocol_sha256'] == protocol_sha, f'{name} names another protocol')
    require(candidate['protocol']['sha256'] == protocol_sha and candidate['protocol']['superseded_sha256'] == superseded_sha,
            'the candidate names another protocol or superseded freeze')
    require(candidate['frozen_thresholds_sha256']['primary'] == aggregates['aggregate-primary.json']['frozen_thresholds_sha256'],
            'the candidate and the primary aggregate name different frozen thresholds')
    require(aggregates['aggregate-primary.json']['privacy_guard']['person_ids_found'] == 0
            and aggregates['aggregate-secondary.json']['privacy_guard']['person_ids_found'] == 0, 'a person id in an aggregate')
    audits = candidate['audits']
    require(audits['stage0']['sha256'] == stage0_sha and audits['stage0']['status'] == 'pass', 'stage-0 audit')
    require(audits['stage0_secondary']['sha256'] == stage0s_sha and audits['stage0_secondary']['status'] == 'pass',
            'stage-0 secondary audit')
    require(stage0['status'] == 'pass' and stage0['protocol_sha256'] == protocol_sha and all(stage0['hard_checks'].values()),
            'the stage-0 audit did not pass against this protocol')
    require(stage0s['status'] == 'pass' and stage0s['protocol_sha256'] == protocol_sha, 'the stage-0 secondary audit did not pass')
    p, s = audits['primary'], audits['secondary']
    private = route['independentAudits']
    require(p['sha256'] == private['primary'] and s['sha256'] == private['secondary'], 'the candidate names other independent audits')
    require(private['primary'] in handoff and private['secondary'] in handoff and route['releaseCandidate']['sha256'] in handoff,
            'the handoff does not record the hashes bound here')
    failed = [c['name'] for c in p['checks'] if not c['pass']]
    require(p['pass'] is True and len(p['checks']) == 12 and failed == [PRIMARY_AUDIT_FAILED],
            'the independent primary audit failed something other than its documentation check')
    require(s['pass'] is True and len(s['checks']) == SECONDARY_AUDIT_CHECKS and all(c['pass'] for c in s['checks']),
            'the independent secondary audit did not pass every check')
    require(candidate['status'] == CANDIDATE_STATUS, 'the candidate is not in the state it was sealed in')
    return {
        'stage0': {'status': 'pass', 'sha256': stage0_sha},
        'stage0_secondary': {'status': 'pass', 'sha256': stage0s_sha},
        'independent_primary': {
            'sha256': p['sha256'], 'checks': len(p['checks']), 'passed': len(p['checks']) - len(failed),
            'computation_and_freeze': 'pass',
            'failed_check': {'name': PRIMARY_AUDIT_FAILED, 'kind': 'documentation, not computation',
                             'what': ('The run log and the primary run headline said a degenerate personal '
                                      'temperature falls back to the population temperature. The code keeps the '
                                      'degenerate value, as the protocol requires, and every number was computed '
                                      'and reproduced that way.')}},
        'independent_secondary': {'sha256': s['sha256'], 'checks': len(s['checks']), 'passed': len(s['checks'])},
        'note': ('Both independent audits re-implement the definitions without importing the study code and reproduce '
                 'every frozen value and aggregate leaf, bootstrap intervals included. They stay in the private run '
                 'root and are bound by hash.'),
    }


def handoff_figures(result):
    """The figures the pages print, written as the pinned handoff writes them: each must be there."""
    pc = lambda v: f'{100 * v:.1f}%'
    pp = lambda d: f'{100 * d["mean"]:+.1f} [{100 * d["interval_95"][0]:+.1f}, {100 * d["interval_95"][1]:+.1f}]'
    n3 = lambda d: f'{d["mean"]:+.3f} [{d["interval_95"][0]:+.3f}, {d["interval_95"][1]:+.3f}]'
    lv = lambda d: f'{d["mean"]:.3f} ({d["interval_95"][0]:.3f}–{d["interval_95"][1]:.3f})'
    out = []
    for p in result['protocols'].values():
        people, folds = p['people'], p['outer_folds']
        for m in p['methods']:
            f, r, q = m['fixed_cutoff'], m['risk_certification'], m['probability_quality']
            out += [f'{f["accepted"]} / {f["n"]}', pc(f['coverage']), f'{f["people_with_nothing_accepted"]} / {people}',
                    pc(m['balanced_accuracy']), n3(m['learned_minus_confidence']['aurc']),
                    pp(m['learned_minus_confidence']['error_at_80']), lv(m['ranking_S']['aurc']),
                    pc(m['ranking_S']['error_at_80']['mean']), pc(m['ranking_L']['error_at_80']['mean']),
                    f'{r["certified_folds"]} / {folds}', lv(q['calibrated']['nll']), lv(q['calibrated']['ece'])]
            if f['selective_error'] is not None:
                out.append(pc(f['selective_error']))
            if r['error_minus_target']:
                out += [pp(r['error_minus_target']), pc(r['selective_error']), pc(r['target_weighted'])]
            if q['raw']:
                out += [lv(q['raw']['nll']), lv(q['raw']['ece'])]
            for x in m['recalibration']:
                out += [n3(x['nll_change']), n3(x['ece_change']), n3(x['aurc_change']),
                        f'{x["people_with_degenerate_personal_temperature"]} / {people}']
        for e in p['common_coverage'].get('errors', []):
            out.append(pc(e['mean']))
    c4 = result['protocols']['arithmetic-rest']['lora_minus_head_only']
    out += [n3(c4['nll_calibrated']).replace(' [', ' ['), f'{c4["nll_raw"]["mean"]:+.3f}']
    return out


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    route = manifest['route']
    require(route['id'] == ROUTE and manifest['approval']['decision'] == 'aggregate_preview'
            and manifest['approval']['date'] == manifest['reviewed_at'], 'no recorded approval for route 1')
    require(manifest['approval']['candidateStatusAtSeal'] == CANDIDATE_STATUS, 'the approval names another candidate state')
    require([s['id'] for s in manifest['sources']] == [SOURCE_OF[p] for p in (*PRIMARY, SECONDARY)],
            'the manifest names other sources')
    require(manifest['holds'] == [], 'route 1 has no hold')
    handoff = pinned_text(route['handoff'], 'handoff')
    candidate, candidate_sha = pinned(route['releaseCandidate'], 'release candidate')
    aggregates = {'aggregate-primary.json': pinned(route['aggregatePrimary'], 'primary aggregate')[0],
                  'aggregate-secondary.json': pinned(route['aggregateSecondary'], 'secondary aggregate')[0]}
    _, protocol_sha = pinned(route['protocol'], 'protocol')
    _, superseded_sha = pinned(route['supersededProtocol'], 'superseded protocol')
    stage0, stage0_sha = pinned(route['stage0Audit'], 'stage-0 audit')
    stage0s, stage0s_sha = pinned(route['stage0SecondaryAudit'], 'stage-0 secondary audit')
    audits = bindings(route, candidate, aggregates, protocol_sha, superseded_sha, stage0, stage0_sha, stage0s,
                      stage0s_sha, handoff)
    references = reresolve(candidate, aggregates)
    matrix = json.loads(SITE_MATRIX.read_bytes())
    adaptation = json.loads(SITE_ADAPTATION.read_bytes())

    records = {}
    for record in manifest['sources']:
        require(record['decision'] == 'aggregate_preview' and approved(record), f'{record["id"]}: approval record is incomplete')
        track = next(t for t in matrix['tracks'] if t['id'] == record['coreTrack'])
        require(record['protocol'] == record['coreTrack'], f'{record["id"]}: another protocol than its core track')
        for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'reviewBasis'):
            require(record[k] == track[k], f'{record["id"]}: {k} differs from the reviewed core track')
        require(record['privacyReview'].startswith(track['privacyReview']), f'{record["id"]}: the privacy review is not the reviewed one')
        records[record['protocol']] = record

    primary = {p: protocol_block(p, candidate['primary'][p], records[p], matrix, adaptation, stage0) for p in PRIMARY}
    secondary = candidate['secondary']
    result = {
        'id': ROUTE,
        'title': 'Reliable decisions: when a decoder should decline to decide, and what its confidence is worth',
        'run_id': RUN_ID,
        'questions': candidate['questions'],
        'design': DESIGN,
        'protocol_amendment': candidate['protocol']['amendment'],
        # The BNCI2015-001 arm's hash is left out with every other trace of that held source.
        'frozen_thresholds_sha256': {k: v for k, v in candidate['frozen_thresholds_sha256'].items() if k != 'bnci'},
        'protocols': primary,
        'robustness': {
            'mi_rest': mi_rest_block(candidate['primary'][SECONDARY], records[SECONDARY], matrix, adaptation, stage0),
            'seeds': seeds_block(secondary['seeds']),
            'matched_model_holdout': risk_arm_block(
                secondary['matched_model_holdout'], 'matched',
                'The base model is trained on three quarters of the training people and calibrated on the remaining '
                'quarter, so calibration and test scores come from one model. Its accuracy differs from the '
                'site\'s and is not published.'),
            'map_sensitivity': risk_arm_block(
                secondary['map_sensitivity'], 'map sensitivity',
                'Platt scaling (two classes) or vector scaling (BETA) in place of temperature scaling, on the same '
                'calibration scores. These maps can change the predicted label, so their accuracy is not the '
                'site\'s and is not published.'),
            'l_joint': ljoint_block(secondary['l_joint_selectivenet']),
        },
        'boundaries': {
            'all_protocols': candidate['boundaries']['all_protocols'],
            'per_protocol': {p: val(b, p) for p, b in candidate['boundaries']['per_protocol'].items()},
        },
        'audits': audits,
        'literature': LITERATURE,
    }
    require(list(result['boundaries']['per_protocol']) == [*PRIMARY, SECONDARY], 'boundaries for other protocols')
    payload = {
        'schema_version': 'bci-report-reliable-decisions-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': ('coverage, selective error, balanced accuracy, AURC and expected calibration error (ECE, 15 '
                         'equal-mass bins) are proportions in [0,1]; NLL is in nats per trial; the Brier score is the '
                         'multi-class sum of squares; differences are differences of those quantities; counts of '
                         'people, folds and trials are whole numbers; null means not defined, never zero'),
        'scope': ('Route 1 of the decision-research roadmap: selective classification and probability calibration on '
                  'saved test scores of models this site already publishes. Every protocol is balanced or uniform by '
                  'design, so every figure compares methods; none is a deployment error rate. No classifier was '
                  'retrained, nothing extends the eight-protocol matrix, and nothing is ranked where intervals overlap.'),
        'results': {ROUTE: result},
        'status_only': [],
        'holds': [],
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'release_candidate_sha256': candidate_sha,
                       'references_reresolved': references, 'included': [ROUTE],
                       'inputs': [s['id'] for s in manifest['sources']], 'holds': []},
    }
    scrub_check(payload)
    validate_public(payload)
    # Refused by value too. A withheld percentile can equal a published number by coincidence: a design
    # constant (0.5, 0.8) or a pooled coverage that is a verified whole count over n. Those stay; any
    # other equality is a leak.
    published = set(numbers(payload))
    pooled = {x['coverage'] for x in pooled_operating_points(result)}
    leaked = [v for v in withheld_values(candidate) if v in published and v not in pooled | DESIGN_CONSTANTS]
    require(not leaked, f'a per-person or per-fold value reached the export: {leaked[:3]}')
    for phrase in handoff_figures(result):
        require(phrase in handoff, f'the handoff does not state {phrase!r}')
    return payload


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    route = manifest['route']
    refs = [route[k] for k in ('handoff', 'releaseCandidate', 'aggregatePrimary', 'aggregateSecondary', 'protocol',
                               'supersededProtocol', 'stage0Audit', 'stage0SecondaryAudit')]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'release_candidate_sha256': payload['provenance']['release_candidate_sha256'],
        'included': payload['provenance']['included'], 'inputs': payload['provenance']['inputs'],
        'status_only': [], 'holds': [],
        'checks': [
            'pinned handoff, release candidate, both aggregates, protocol, superseded freeze and both stage-0 audits',
            f'every {{source, value}} block of the release candidate re-resolves to its aggregate '
            f'({payload["provenance"]["references_reresolved"]} references)',
            'the candidate names the pinned aggregates, protocol, superseded freeze, stage-0 audits and frozen '
            'thresholds; both aggregates name the same protocol and run',
            'both stage-0 audits passed; the independent primary audit failed only its documentation check; the '
            'independent secondary audit passed all fifteen; the handoff records both hashes',
            'every full-coverage balanced accuracy equals the site value (core matrix, or the adaptation release\'s '
            'seed-20260922 mean) and the stage-0 audit\'s reading of it',
            'coverage is accepted / n; nothing accepted gives a null error, never zero; fewer than 10 accepted is '
            'flagged unstable; an error is a whole count of accepted trials',
            'every interval holds its point; every verdict follows from its interval; every contrast equals the '
            'difference of the levels it compares',
            'certified + uncertified folds is every fold; nothing accepted exactly when nothing is certified; folds '
            'over target never exceed folds certified',
            'labels per new person: 10 and 20 on EEGMAT, 40 on BETA; scored trials are what remains after the prefix',
            'ds003810 stays without primary contrasts and is published as crude',
            'per-person percentiles and per-fold median temperatures refused by key, fragment and value; idle and '
            'BNCI2015-001 refused by key',
            'the printed headline figures are the ones the pinned handoff states',
            'no private paths or hosts, file or participant identifiers',
        ],
        'audit_bindings': {
            'bound': [
                'release candidate bytes: pinned here, and recorded in the handoff',
                'every candidate figure: equal, at its JSON pointer, to the pinned primary or secondary aggregate',
                'aggregates, protocol and stage-0 audits: by the hashes the candidate records',
                'independent audits: by the hashes the candidate and the handoff both record',
            ],
            'not_bound': [
                'the independent audits are not opened here (they carry private storage paths); their pass, and the '
                'nature of the one failed check, are taken from the candidate, whose bytes are pinned',
            ],
        },
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
