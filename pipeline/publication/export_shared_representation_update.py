"""Release route 2 of the decision-research roadmap, one representation and several questions, as aggregate-only JSON.

Does one shared encoder with fixed heads answer several questions as well as a question-conditioned head, or as
separate models, for less? Route 2 compared independent task models (A), a shared encoder with one linear head per
question (B-lin), the same encoder with one shared hidden layer (B-sh) and that layer conditioned on the question's
identity by FiLM (C1), at matched data and compute: EEGNet from scratch (E1, three seeds) and frozen CBraMod features
(L1, three seeds) as the primary levels, CBraMod adapted by LoRA (E2, one seed) as a secondary one. Motor imagery on
OpenBMI (51 people) and sleep on BOAS (100 people) are primary; EESM19 (20 people, one seed) is a crude replication.

Its own publication boundary, as with every batch. The website input is the release candidate. Every
{source, value} block in it is re-resolved against the pinned file it names; the consolidated aggregate, the two
audited run-root aggregates, the named parts of the audit work files, the frozen protocol, the BOAS rights review
and the three independent audits are pinned by SHA-256, opened and checked, never copied. What this export refuses:
- per-person and per-fold values: the release candidate's OpenBMI per-person percentiles (by key, fragment and
  value); the BOAS ones never reached this machine;
- a BOAS figure without its three stated gaps and attribution, a BOAS cell of fewer than 20 people, demographics,
  dates and measured compute time;
- a flag its interval does not give, a gate its arm's interval does not give, a route sentence the counted questions
  and the cost ledger do not give, a contrast that is not the difference of its arms, and a figure the pinned
  handoff does not state.

    python3 pipeline/publication/export_shared_representation_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261007'
MANIFEST = REVIEW / 'shared-representation-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'shared-representation-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/shared-representation-update.json',
           PROJECT / 'site/public/data/shared-representation-update.json')
# The released records route 2's OpenBMI and EESM19 rights must equal. Released files: read, never written.
SITE_MATRIX = PROJECT / 'site/src/data/mvp.json'
SITE_LARGE_SOURCE = PROJECT / 'site/src/data/large-source-update.json'

ROUTE = 'one-representation'
RUN_ID = 'decision-route2-v1/20261006'
CANDIDATE_STATUS = 'pending user approval'   # the state the candidate was sealed in; the manifest is the approval
DELTA = 2.0                                  # pp balanced accuracy, fixed by the owner at the freeze
LOG_P3 = math.log(0.8)                       # P3 and S4: the dedicated model must remove 20% of the remaining error
BOAS_MIN_PEOPLE = 20
NOT_SUPPORTED = 'The fixed-heads sentence is not supported'
TOL = 1e-9

# The pinned files the candidate's {source, value} blocks name, and the manifest key that pins each.
PINNED = {
    'aggregate.json': 'aggregate',
    'aggregate-primary.full.json': 'aggregatePrimary',
    'aggregate-secondary.full.json': 'aggregateSecondary',
    'audit-work.boas-extract.json': 'auditExtract',
    'protocol.json': 'protocol',
    'boas-rights-review.json': 'boasRightsReview',
    'audit-primary.json': ('independentAudits', 'primary'),
    'audit-secondary.json': ('independentAudits', 'secondary'),
    'audit-e2-sleep.json': ('independentAudits', 'e2Sleep'),
}
# Named in nested blocks of the consolidated aggregate only; bound through its hash, not opened here.
NOT_OPENED = {'stage0-report.json'}

# Candidate result keys, the domain token its pointers use, and the dataset id the export uses.
DATASETS = (('MI', 'MI', 'openbmi'), ('BOAS', 'sleep', 'boas'), ('EESM19', 'eesm19', 'eesm19'))
PRIMARY_QUESTIONS = {'MI': ('MI-A', 'MI-B'), 'sleep': ('SL-A', 'SL-E', 'SL-F')}
PRIMARY_COUNT = 21                           # P1 5, P2 5, P3 1, P4 5, P5 5
# Which bound decides the margin flag (protocol decision_rules.flags; the handoff's "analogues").
UPPER = {'P1', 'P4', 'P5', 'S1', 'S2', 'S3-P1', 'S3-P5', 'S5', 'S6-P1', 'S7', 'S8', 'S13-P1', 'S14', 'X1'}
LOWER = {'P2', 'S3-P2', 'S6-P2', 'S10', 'S12', 'S12-P2', 'S13-P2'}
DESCRIPTIVE = {'S11'}
LEVEL_OF_BLOCK = {'S2_S5_S10': 'E1', 'S6': 'E1', 'S12': 'E1', 'S4': 'E1', 'S11': 'E1', 'S13': 'E1', 'S3': 'E2',
                  'S7_S8_S14_X1': 'L1'}
GATES = ('pass', 'floor', 'ceiling: equivalence uninformative')
REPRESENTATION = {'steegformer-base-pooled': 'ST-EEGFormer Base, pooled', 'cbramod-pooled': 'CBraMod, pooled',
                  'cbramod-tokens-f16': 'CBraMod tokens', 'reve-large-pooled': 'REVE Large, pooled'}
# Who attached a secondary entry's gate (D-S3), by the opening words of the candidate's label.
GATE_BY = (('independent secondary audit (D-S3)', 'independent secondary audit'),
           ('run (frozen stage 2)', 'run'),
           ('E2-sleep scorer', 'E2-sleep scorer, recomputed by its independent audit'),
           ('none: descriptive contrast', 'none: descriptive'),
           ('level B-lin gate (frozen rule)', 'level gate'))
# The cost ledger: exact items compare exactly; measured times count only beyond 1.2x (shared GPU).
EXACT_ITEMS = ('parameters', 'steps', 'passes_per_window', 'head_macs')
TIMED_ITEMS = {'step_seconds': 'step_time', 'latency_seconds': 'batch_time'}
TIMED_FACTOR = 1.2

# Per-person distributions, per-fold values, compute time and what the pages leave out on purpose.
REFUSED_KEYS = PER_PERSON_KEYS | {'p10', 'p50', 'p90', 'p10_pp', 'p50_pp', 'p90_pp', 'per_person_value',
                                  'steps_per_fold', 'gpu_seconds_per_fit', 'gpu_seconds_per_fit_set', 'compute_time',
                                  'pilot_sd', 'removed_pointers', 'age', 'sex', 'bmi', 'pid', 'splits'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_fold', 'per_night', 'per_recording', 'percentile',
                         'median', 'spread', 'participant_id', 'record_id', 'subject', 'prediction', 'probabilities',
                         'private', 'elapsed', 'seconds', 'minutes', 'hours', 'platform', 'basename', 'p10', 'p50',
                         'p90', 'discrepanc', 'pilot')
# Path roots and host:path forms only: naming this operator's machines or volumes here would itself be the leak.
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|\b[\w.-]+:(?:~|/(?!/))', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub-\d+|\bsubj\d+|\.npz\b|\.npy\b|\.edf\b|\.mat\b|\.private\b|DECISIONS\.md|\bpid\s*\d',
                        re.IGNORECASE)

DESIGN = {
    'questions_asked_by': ('Every question is a label-backed classification target from one dataset, asked by '
                           'identifier: a learned 16-dimensional embedding of the question\'s index, never language.'),
    'levels': {
        'E1': ('EEGNet trained from scratch in its published configuration; the shared trunk has 2,096 parameters on '
               'motor imagery and 1,200 on sleep. Three seeds. Primary.'),
        'L1': 'Frozen CBraMod features with the heads trained on top. Three seeds. Primary.',
        'E2': ('CBraMod adapted by LoRA (rank 4) together with the heads. One seed. Secondary; on sleep it ran after '
               'every other result was known (owner decision, 7 October 2026).'),
    },
    'arms': {
        'A': 'One independent model per question.',
        'B-lin': 'One shared encoder with one linear head per question: the fixed heads.',
        'B-sh': ('One shared encoder, one shared hidden layer (width 66 on E1 motor imagery by the ±10% parameter '
                 'rule, 64 elsewhere) and one output per question.'),
        'C1': 'B-sh plus FiLM conditioning from the question\'s 16-dimensional embedding: the question-conditioned head.',
        '-fz': 'The same head on frozen CBraMod features; B-lin-fz-sgd trains the linear heads by SGD.',
    },
    'matching': ('B-lin, B-sh and C1 share initialisation, batch order and step count, see the same windows and labels '
                 'and run one encoder pass per window. A trains one encoder per question; that cost is what sharing '
                 'saves, and the ledger counts it.'),
    'folds': ('Five person-disjoint outer folds per dataset (all sessions or nights of a person in one fold); no '
               'validation set, no early stopping; the final epoch is scored.'),
    'metric': ('Balanced accuracy averaged per person, then equally over people. It compares set-ups and is not a '
               'deployment error rate. P3 and S4 compare AUROC through log R, R = (1 - AUROC of the dedicated model) / '
               '(1 - AUROC of the read-out).'),
    'single_seed': 'A one-seed entry resamples people only and carries no training-run variance.',
    'canary': ('Before any fit, a ridge classifier on each window\'s per-channel mean and log-variance, trained and '
               'tested within the first fold\'s training people only. A question it answers at a balanced accuracy of '
               '0.85 or more is demoted: reported, never counted. No question was demoted.'),
    'headroom_gate': ('A question\'s entries count for a route sentence only if the 95% interval of the level\'s '
                      'fixed-head (B-lin) arm lies above chance + 5 pp and below 95%; otherwise they are reported and '
                      'labelled floor or ceiling. For P3 only the floor applies: the read-out\'s AUROC interval must '
                      'lie above 0.55.'),
    'freeze': ('The protocol was frozen on 2026-10-06 at 07:17 UTC and amended eight times for engineering only (A1-A8) '
               'before the first stage-1 fit at 09:24 UTC; delta, the P3 cut, the canary and the gates are identical '
               'in every version. Outer-test labels were masked until scoring. Nothing was selected on test results; '
               'no fit failed and nothing was re-run.'),
}
# The anchors the handoff names, as the frozen protocol lists them (topic and link; titles are not restated here).
LITERATURE_URLS = ('https://arxiv.org/abs/2609.25845', 'https://arxiv.org/abs/2604.25131',
                   'https://arxiv.org/abs/2508.17742', 'https://arxiv.org/abs/1709.07871',
                   'https://arxiv.org/abs/1609.09106')
# The candidate's not-run arms, and what this file says about each.
NOT_RUN = (('Ying 2025 (S9)', {'arm': 'Ying 2025 multi-night sleep (S9)',
                               'status': 'deferred by the owner before the freeze; nothing was run'}),
           ('E2 MI at 3 seeds', {'arm': 'E2 on motor imagery at three seeds',
                                 'status': ('not scheduled: E2 ran at one seed as a secondary arm, so the E1 sharing '
                                            'contrast keeps the label small-CNN trunk sharing')}))
# What was declared or allowed but not computed, each tied to the candidate's record by its opening words.
NOT_REPORTED = (
    ('B-lin-fz-ridge reference row', 'not_reported',
     {'item': 'The ridge reference row on frozen CBraMod features (G-1)',
      'status': ('Declared in the frozen draft, never implemented, and not computed afterwards: it would be new fits, '
                 'and each choice it leaves open would be made after every result is known. No decision uses it.')}),
    ('secondary per-arm publish items', 'not_reported',
     {'item': 'Arm-level results of the secondary arms (interval, AUROC, log loss, per-seed means)',
      'status': ('Not produced by the frozen stage 2; each secondary contrast carries the mean balanced accuracy of '
                 'its two arms.')}),
    ('P3 at E2', 'not_reported',
     {'item': 'P3 at E2',
      'status': 'Not declared for the E2-sleep block, so its five wake-or-sleep fits feed no contrast.'}),
    ('counts of people whose paired contrast', 'boas_filter',
     {'item': 'Counts of people whose paired contrast is above or below zero',
      'status': 'Allowed by the BOAS review, not computed by the frozen stage 2, and not added afterwards.'}),
)
# The E1 sharing boundary is conditional on a run that was not scheduled; the export states the outcome instead.
E2_MI_CONDITIONAL = " (unless E2 MI was run at 3 seeds)."
E2_MI_OUTCOME = '; E2 on motor imagery ran at one seed, as a secondary arm.'


# ---------------------------------------------------------------------------- helpers
def close(a, b, label, tol=TOL):
    require(finite(a, b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def finite(*values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def ref_of(route, key):
    return route[key[0]][key[1]] if isinstance(key, tuple) else route[key]


def resolve(files, source):
    """A JSON pointer into one of the pinned files."""
    name, _, pointer = source.partition('#')
    require(name in files, f'a reference into an unpinned file: {source}')
    node = files[name]
    for tok in pointer.split('/')[1:] if pointer else []:
        tok = tok.replace('~1', '/').replace('~0', '~')
        if isinstance(node, list):
            require(tok.isdigit() and int(tok) < len(node), f'a reference that does not resolve: {source}')
            node = node[int(tok)]
        else:
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


def reresolve(candidate, files):
    """Every {source, value} block equals the pinned file's value at that pointer, nested blocks included."""
    seen = {'top': 0, 'nested': 0, 'bound_through_parent': 0}

    def walk(node, trail, depth):
        if isinstance(node, dict):
            if isinstance(node.get('source'), str) and '#' in node['source'] and 'value' in node:
                name = node['source'].partition('#')[0]
                if depth and name in NOT_OPENED:
                    seen['bound_through_parent'] += 1
                else:
                    require(same(node['value'], resolve(files, node['source'])),
                            f'{trail}: the value differs from {node["source"]}')
                    seen['nested' if depth else 'top'] += 1
                for k, v in node.items():
                    walk(v, f'{trail}/{k}', depth + (k == 'value'))
                return
            for k, v in node.items():
                walk(v, f'{trail}/{k}', depth)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f'{trail}[{i}]', depth)
    walk(candidate, '$', 0)
    for finding in candidate['key_findings']:
        for ref in finding['refs']:
            resolve(files, ref)
    return seen


def val(block, label):
    require(isinstance(block, dict) and 'source' in block and 'value' in block, f'{label}: not a traced block')
    return block['value']


def inner(block, label):
    """The value of a traced block whose value is itself a traced block (the aggregate citing its own source)."""
    v = val(block, label)
    while isinstance(v, dict) and set(v) == {'source', 'value'}:
        v = v['value']
    return v


def interval(ci, point, label, lo=None, hi=None):
    require(isinstance(ci, list) and len(ci) == 2 and finite(*ci) and ci[0] <= ci[1], f'{label}: no two-sided interval')
    require(finite(point) and ci[0] <= point <= ci[1], f'{label}: the interval does not contain its point')
    require((lo is None or ci[0] >= lo) and (hi is None or ci[1] <= hi), f'{label}: the interval leaves the range')
    return [ci[0], ci[1]]


def gate_of(ci, chance):
    """The headroom gate (protocol decision_rules.headroom_gate), from the arm's interval."""
    if ci[0] <= chance + 0.05:
        return 'floor'
    if ci[1] >= 0.95:
        return 'ceiling: equivalence uninformative'
    return 'pass'


def short_names(x, y):
    """The names a difference flag gives the two sides ("difference: A higher", "primary K higher")."""
    if y.startswith('readout['):
        return 'dedicated head', 'stage-posterior readout'
    split = lambda a: (a.split('(')[0], a[a.index('(') + 1:-1]) if a.endswith(')') and '(' in a else (a, '')
    (bx, sx), (by, sy) = split(x), split(y)
    if bx == by:
        return sx, {'primary': 'primary K'}.get(sy, sy)
    base = lambda b: 'A' if b.startswith('A_') else b
    return base(bx), base(by)


def flags(v, kind, label):
    """Both flags and the wording follow from the interval and the margin rule, and from nothing else."""
    lo, hi = v['ci95_log_R'] if kind == 'log_r' else v['ci95_pp']
    if kind == 'log_r':
        difference = ('difference: dedicated model leaves less error' if hi < 0 else
                      'difference: read-out leaves less error' if lo > 0 else 'no difference shown')
        if LOG_P3 < lo and hi < -LOG_P3:
            margin = 'equivalent within delta'
        else:
            margin = 'non-inferior' if lo > LOG_P3 else 'margin not met'
    else:
        wx, wy = short_names(v['x'], v['y'])
        difference = (f'difference: {wx} higher' if lo > 0 else f'difference: {wy} higher' if hi < 0
                      else 'no difference shown')
        if kind == 'descriptive':
            margin = 'not applicable (descriptive contrast)'
        elif -DELTA < lo and hi < DELTA:
            margin = 'equivalent within delta'
        else:
            margin = 'non-inferior' if (hi < DELTA if kind == 'upper' else lo > -DELTA) else 'margin not met'
    require(v['difference_flag'] == difference, f'{label}: the difference flag "{v["difference_flag"]}" does not follow '
            f'from the interval ("{difference}")')
    require(v['margin_flag'] == margin, f'{label}: the margin flag "{v["margin_flag"]}" does not follow from the '
            f'interval ("{margin}")')
    wording = ('inconclusive at this sample size' if (difference, margin) == ('no difference shown', 'margin not met')
               else f'{difference}; {margin}')
    require(v['wording'] == wording, f'{label}: the wording does not follow from the flags')
    return difference, margin, wording


def kind_of(entry_id):
    if entry_id == 'P3' or entry_id.startswith('S4-'):
        return 'log_r'
    for group, kind in ((UPPER, 'upper'), (LOWER, 'lower'), (DESCRIPTIVE, 'descriptive')):
        if entry_id in group:
            return kind
    raise ValueError(f'{entry_id}: no margin rule for this entry')


def seeds_of(v, label, log_r=False):
    per = v['per_seed']
    require(isinstance(per, list) and (per == []) is v['single_seed'] and (v['single_seed'] or len(per) == 3),
            f'{label}: per-seed points disagree with single_seed')
    out = []
    for i, s in enumerate(per):
        require(s['seed_index'] == i and not s.get('nonfinite_draws'), f'{label}: seed {i}')
        out.append({'seed_index': i, ('log_r' if log_r else 'estimate_pp'): s['point'],
                    ('interval_95' if log_r else 'interval_95_pp'): interval([s['lo'], s['hi']], s['point'],
                                                                            f'{label} seed {i}')})
    if per and not log_r:
        close(sum(s['point'] for s in per) / len(per), v['estimate_pp'], f'{label}: the seeds do not average to the '
              'estimate', 1e-9)
    return out


def gate_label(entry, label):
    """A secondary entry's gate and who attached it (D-S3)."""
    g = entry.get('gate_label')
    require(g is not None, f'{label}: a secondary entry without its gate label')
    value = g['value'] if 'value' in g else g
    by = g.get('by') or value.get('by')
    names = [short for opening, short in GATE_BY if by.startswith(opening)]
    require(len(names) == 1, f'{label}: an unknown gate provenance "{by}"')
    gate = value['gate']
    require(gate in GATES or (gate == 'not applicable' and names[0] == 'none: descriptive'), f'{label}: gate "{gate}"')
    return gate, names[0]


# ---------------------------------------------------------------------------- entries
def contrast(v, label, role, gate=None, gate_by=None, extra=None):
    """A balanced-accuracy contrast: its flags, its arms and its seeds follow from its numbers."""
    kind = kind_of(v['id'])
    require(kind != 'log_r', f'{label}: not a balanced-accuracy contrast')
    n = v['included_people']
    require(count(n) and n >= BOAS_MIN_PEOPLE, f'{label}: a cell of {n} people')
    lo_hi = interval(v['ci95_pp'], v['estimate_pp'], label)
    difference, margin, wording = flags(v, kind, label)
    means = v['mean_ba']
    require(list(means) == [v['x'], v['y']] and all(finite(m) and 0 <= m <= 1 for m in means.values()),
            f'{label}: the arm means are not its two arms\'')
    close(100 * (means[v['x']] - means[v['y']]), v['estimate_pp'], f'{label}: the contrast is not the difference of '
          'its arms', 1e-9)
    gate = v.get('gate') if gate is None else gate
    if 'gate' in v:
        require(v['gate'] == gate, f'{label}: two gates')
    require(gate in GATES or gate == 'not applicable', f'{label}: gate "{gate}"')
    out = {'id': v['id'], 'role': role, 'level': v.get('level') or LEVEL_OF_BLOCK[v['block']],
           'question': v['question'], 'x': v['x'], 'y': v['y'], 'included_people': n,
           'estimate_pp': v['estimate_pp'], 'interval_95_pp': lo_hi, 'difference': difference, 'margin': margin,
           'wording': wording, 'single_seed': v['single_seed'], 'gate': gate}
    if gate_by:
        out['gate_attached_by'] = gate_by
    out['mean_balanced_accuracy'] = dict(means)
    out['per_seed'] = seeds_of(v, label)
    if 'level' in v and 'block' in v:
        require(LEVEL_OF_BLOCK[v['block']] == v['level'], f'{label}: level and block disagree')
    for k in ('label', 'canary', 'block', 'note'):
        if v.get(k) is not None:
            out[k] = v[k]
    if v.get('feature'):
        out['representation'] = REPRESENTATION[v['feature']]
    if extra:
        out.update(extra)
    return out


def log_ratio(v, label, role, gate=None, gate_by=None):
    """P3 and S4: log R with its interval; R follows from the two AUROCs, the gate from the read-out's AUROC interval."""
    require(kind_of(v['id']) == 'log_r', f'{label}: not a log-R entry')
    n = v['included_people']
    require(count(n) and n >= BOAS_MIN_PEOPLE, f'{label}: a cell of {n} people')
    lo_hi = interval(v['ci95_log_R'], v['log_R'], label)
    difference, margin, wording = flags(v, 'log_r', label)
    auc = v['auroc_mean']
    require(all(finite(a) and 0.5 <= a < 1 for a in auc.values()), f'{label}: AUROC')
    close((1 - auc['dedicated']) / (1 - auc['marginal']), v['R'], f'{label}: R is not the ratio of remaining errors')
    close(math.log(v['R']), v['log_R'], f'{label}: log R')
    close(auc['dedicated'] - auc['marginal'], v['auroc_difference'], f'{label}: AUROC difference')
    gate_ci = interval(v['gate_interval_marginal_auroc'], auc['marginal'], label + ' read-out AUROC', 0.0, 1.0)
    want = 'pass' if gate_ci[0] > 0.55 else 'floor'
    require(v['gate'] == want and (gate is None or gate == want), f'{label}: the gate does not follow the read-out\'s '
            'AUROC interval')
    ba = v['balanced_accuracy']
    out = {'id': v['id'], 'role': role, 'level': 'E1', 'question': v['question'], 'dedicated': v['dedicated'],
           'read_out_of': v['marginal_of'], 'included_people': n, 'log_r': v['log_R'], 'interval_95': lo_hi,
           'r': v['R'], 'auroc': {'dedicated': auc['dedicated'], 'read_out': auc['marginal']},
           'balanced_accuracy': {'dedicated': ba['dedicated'], 'read_out': ba['marginal']},
           'difference': difference, 'margin': margin, 'wording': wording, 'single_seed': v['single_seed'],
           'gate': want, 'read_out_auroc_interval_95': gate_ci}
    if gate_by:
        out['gate_attached_by'] = gate_by
    out['per_seed'] = seeds_of(v, label, log_r=True)
    return out


# ---------------------------------------------------------------------------- per dataset
def questions_of(protocol, domain, prevalence, people):
    items = protocol['draft']['questions']['MI_openbmi' if domain == 'MI' else 'sleep_boas']['items']
    require(prevalence['people'] == people, f'{domain}: another cohort in the prevalence table')
    out = []
    for it in items:
        q = prevalence['questions'][it['id']]
        total = q['windows_defined']
        require(sum(q['counts'].values()) == total and list(q['counts']) == list(it['answers'])
                and list(q['share']) == list(it['answers']), f'{it["id"]}: counts are not its answers\'')
        for a, c in q['counts'].items():
            close(q['share'][a], c / total, f'{it["id"]} {a}: share is not count / windows')
        require(q['people_defined'] == people, f'{it["id"]}: another number of people')
        out.append({'id': it['id'], 'question': it['question'], 'answers': it['answers'], 'role': it['role'],
                    'defined_on': it['defined_on'], 'windows': total, 'people': q['people_defined'],
                    'counts': q['counts'], 'shares': q['share']})
    require(prevalence['questions'] and [q['id'] for q in out] == list(prevalence['questions']), f'{domain}: questions')
    return out


def canary_of(block, label, threshold, demoted):
    c = inner(block, label)
    require(count(c['training_people']) and demoted == [], f'{label}: the canary demoted a question')
    out = []
    for q, x in c['questions'].items():
        require(x['label'] == ('passes canary' if x['preprocessed_ba'] < threshold else 'answerable from window statistics')
                and x['label'] == 'passes canary', f'{label} {q}: the canary label does not follow its value')
        out.append({'id': q, 'balanced_accuracy': x['preprocessed_ba'], 'balanced_accuracy_unfiltered': x['unfiltered_ba'],
                    'label': x['label']})
    return {'training_people': c['training_people'], 'demotes_at': threshold, 'questions': out}


def arms_of(per_arm, metrics, people, label):
    """Every arm's balanced accuracy with its interval, and its cohort-level probability metrics."""
    out = []
    rename = {'logloss_mean': 'log_loss', 'auroc_mean': 'auroc', 'kappa_mean': 'cohen_kappa',
              'per_seed_mean_ba': 'per_seed_means'}
    for key, block in per_arm.items():
        level, _, arm, question = key.split('/')
        v = val(block, f'{label} {key}')
        require(v['included_people'] == people and v['seeds'] == 3, f'{key}: another cohort or seed count')
        row = {'level': level, 'arm': arm, 'question': question, 'mean': v['mean_ba'],
               'interval_95': interval(v['ci95'], v['mean_ba'], key, 0.0, 1.0), 'chance': v['chance'],
               'included_people': v['included_people'], 'seeds': v['seeds']}
        if key in metrics:
            m = val(metrics[key], key)
            require(set(m) <= set(rename), f'{key}: unexpected metrics {sorted(set(m) - set(rename))}')
            for k, name in rename.items():
                if k in m:
                    row[name] = m[k]
            seeds = m['per_seed_mean_ba']
            require(len(seeds) == 3 and all(0 <= s <= 1 for s in seeds), f'{key}: per-seed means')
            close(sum(seeds) / 3, v['mean_ba'], f'{key}: the seed means do not average to the mean', 1e-9)
        out.append(row)
    require(set(metrics) <= set(per_arm), f'{label}: metrics for an arm without a balanced accuracy')
    return out


def gates_of(gates, arms, label):
    by_key = {(a['level'], a['arm'], a['question']): a for a in arms}
    out = []
    for key, block in gates.items():
        level, _, question = key.split('/')
        g = val(block, f'{label} gate {key}')
        arm = by_key[(level, g['arm'], question)]
        close(g['mean_ba'], arm['mean'], f'{key}: the gate reads another arm', 1e-12)
        require(g['ci95'] == arm['interval_95'] and g['chance'] == arm['chance'], f'{key}: the gate reads another interval')
        require(g['gate'] == gate_of(g['ci95'], g['chance']), f'{key}: the gate does not follow the arm\'s interval')
        out.append({'level': level, 'question': question, 'arm': g['arm'], 'mean': g['mean_ba'],
                    'interval_95': g['ci95'], 'chance': g['chance'], 'floor': round(g['chance'] + 0.05, 10),
                    'gate': g['gate']})
    return out


def ledger_of(block, label):
    """The E1 cost ledger: exact items, and the two indicative times measured interleaved on a shared GPU."""
    led = val(block, label)
    out = {}
    for arm, x in led.items():
        row = {'parameters': x['parameters']}
        if 'parameters_split' in x:
            split = x['parameters_split']
            require(sum(split.values()) == x['parameters'], f'{label} {arm}: the parameter split does not add up')
            row['parameters_by_part'] = split
        require(count(x['passes_per_window']) and count(x['head_macs']) and finite(x['steps']), f'{label} {arm}: items')
        row.update(mean_steps_per_fit=x['steps'], encoder_passes_per_window=x['passes_per_window'],
                   head_macs_per_window=x['head_macs'], step_time_s=x['step_seconds'], batch_time_s=x['latency_seconds'])
        out[arm] = row
    out['timing'] = ('step_time_s (one optimiser step) and batch_time_s (one 256-window batch answering every question) '
                     'were measured interleaved across arms in one stage-0 micro-benchmark on a shared GPU: indicative, '
                     'and in the "for less" rule a time counts only beyond 1.2x. Parameters, steps, passes and '
                     'multiply-accumulates are exact.')
    return out, led


def for_less(led):
    """The ledger rule: B-lin is "for less" than C1 if no item is higher and at least one is lower."""
    b, c = led['B-lin'], led['C1']
    lower = [k for k in EXACT_ITEMS if b[k] < c[k]] + [n for k, n in TIMED_ITEMS.items() if c[k] > TIMED_FACTOR * b[k]]
    higher = [k for k in EXACT_ITEMS if b[k] > c[k]] + [n for k, n in TIMED_ITEMS.items() if b[k] > TIMED_FACTOR * c[k]]
    return {'for_less': not higher and bool(lower), 'lower': lower, 'higher': higher}


def route_sentence(block, domain, entries, canary, led, label):
    """The domain's route sentence follows from its counted questions' P1 flags and the ledger (protocol rule)."""
    rs = val(block, label)
    p1 = {e['question']: e for e in entries if e['id'] == 'P1'}
    passes = {q['id'] for q in canary['questions'] if q['label'] == 'passes canary'}
    counted = [q for q in PRIMARY_QUESTIONS[domain] if p1[q]['gate'] == 'pass' and q in passes]
    excluded = {q: p1[q]['gate'] for q in PRIMARY_QUESTIONS[domain] if q not in counted}
    higher = {q: p1[q]['interval_95_pp'] for q in counted if p1[q]['interval_95_pp'][0] > 0}
    met = all(p1[q]['margin'] in ('equivalent within delta', 'non-inferior') for q in counted)
    ledger = for_less(led)
    require(rs['counted'] == counted and rs['excluded'] == excluded, f'{label}: the counted questions do not follow '
            'from the gates')
    require(rs['c1_significantly_higher'] == higher, f'{label}: the questions where C1 is higher')
    require(rs['margin_all_met'] is met, f'{label}: margin_all_met')
    back = {v: k for k, v in TIMED_ITEMS.items()}
    require(rs['ledger_b_lin_for_less_than_c1'] == {'for_less': ledger['for_less'],
                                                     'higher': [back.get(k, k) for k in ledger['higher']],
                                                     'lower': [back.get(k, k) for k in ledger['lower']]},
            f'{label}: the ledger does not give the candidate\'s "for less"')
    supported = bool(counted) and met and ledger['for_less']
    require(counted and (rs['sentence'] == NOT_SUPPORTED) is (not supported), f'{label}: the sentence does not follow')
    return {'sentence': rs['sentence'], 'supported': supported, 'counted': counted, 'excluded': excluded,
            'conditioned_head_higher': higher, 'margin_met_on_every_counted_question': met,
            'fixed_heads_for_less': ledger['for_less'], 'fixed_heads_lower_on': ledger['lower'],
            'fixed_heads_higher_on': ledger['higher']}


def derived_sentences(entry, derived, label):
    """The audit's per-question sentences (D-5) follow from the entry's flags and gate (protocol rule)."""
    rules = {'P1': [('conditioned head better on q', entry['difference'] == 'difference: C1 higher')],
             'P5': [('conditioning itself adds nothing on q', entry['margin'] in ('equivalent within delta', 'non-inferior'))],
             'P2': [('sharing costs accuracy on q', entry['difference'] == 'difference: A higher'),
                    # At E1 always with the label (protocol route_sentences_per_domain, D14).
                    ('sharing costs at most delta on q' + (' (small-CNN trunk sharing)' if entry['level'] == 'E1' else ''),
                     entry['margin'] in ('equivalent within delta', 'non-inferior'))],
             'P3': [('derivable question needs no own model', entry['margin'] in ('equivalent within delta', 'non-inferior'))],
             'P4': []}[entry['id']]
    want = [s for s, holds in rules if holds]
    counts = entry['gate'] == 'pass'
    require(derived['gate'] == entry['gate'] and derived['counts_for_route_sentence'] is counts,
            f'{label}: the audit counted it otherwise')
    require(derived['sentences_if_counted'] == want and derived['stated'] == (want if counts else []),
            f'{label}: the audit\'s sentences do not follow from the flags')
    return derived['stated']


def entries_of(result, domain, gates, derived, label):
    """The primary entries (and S1, the secondary frozen-level conditioning contrast), with their gates."""
    gate_at = {(g['level'], g['question']): g['gate'] for g in gates}
    out = []
    for e in result['primary_entries']:
        v = val(e['ref'], label)
        where = f'{label} {v["id"]} {v.get("level")} {v["question"]}'
        require(v['domain'] == domain, f'{where}: another domain')
        if v['id'] == 'P3':
            x = log_ratio(v, where, 'primary')
        elif v['id'] == 'S1':
            gate, by = gate_label(e, where)
            require(gate == gate_at[(v['level'], v['question'])], f'{where}: S1 carries another gate than its level\'s')
            x = contrast(v, where, 'secondary', gate, by)
        else:
            x = contrast(v, where, 'primary')
            require(x['gate'] == gate_at[(v['level'], v['question'])], f'{where}: the gate is not its level\'s')
        if x['role'] == 'primary':
            key = f'{x["level"]}/{domain}/{x["id"]}/{x["question"]}'
            x['sentences_derived_by_audit'] = derived_sentences(x, val(derived[key], key), where)
        out.append(x)
    return out


def secondary_of(entries, label, skip_block=None):
    out = []
    for e in entries:
        v = val(e['ref'], label)
        if skip_block and v['block'] == skip_block:
            continue
        where = f'{label} {v["id"]} {v["question"]}'
        if 'descriptive' in v:      # the S11 stage-only read-out from the true current stage
            require(v['id'] == 'S11-oracle' and v['descriptive'] is True and v['people'] >= BOAS_MIN_PEOPLE
                    and 0 <= v['mean_ba'] <= 1, f'{where}: the oracle read-out')
            gate, by = gate_label(e, where)
            require((gate, by) == ('not applicable', 'none: descriptive'), f'{where}: a descriptive row with a gate')
            out.append({'id': v['id'], 'role': 'descriptive', 'level': 'E1', 'question': v['question'],
                        'included_people': v['people'], 'mean': v['mean_ba'], 'gate': gate, 'gate_attached_by': by,
                        'block': v['block'], 'read_out_from': 'the true current stage'})
            continue
        gate, by = gate_label(e, where)
        if kind_of(v['id']) == 'log_r':
            out.append(log_ratio(v, where, 'secondary', gate, by) | {'block': v['block']})
        else:
            out.append(contrast(v, where, 'descriptive' if v['id'] in DESCRIPTIVE else 'secondary', gate, by))
    return out


def s2_level1(blocks, gates, label):
    """S2 at Level 1: not reported by the frozen stage 2, computed by the independent secondary audit (D-S2)."""
    gate_at = {(g['level'], g['question']): g['gate'] for g in gates}
    out = []
    for block in blocks:
        v = dict(val(block, label))
        require(v['id'] == 'S2' and v['level'] == 'L1 (CBraMod, 3 seeds)', f'{label}: not S2 at Level 1')
        v['level'] = 'L1'
        out.append(contrast(v, f'{label} {v["question"]}', 'secondary', gate_at[('L1', v['question'])], 'level gate',
                            extra={'computed_by': ('the independent secondary audit, from the frozen Level-1 '
                                                   'predictions with the frozen bootstrap; the frozen stage 2 did '
                                                   'not report it')}))
    return out


def parameters_of(block, label, prefix):
    rows = {}
    for key, x in inner(block, label).items():
        if not key.startswith(prefix):
            continue
        p = x['parameters']
        require(p['encoder'] + p['heads'] + p['conditioning'] == p['total'], f'{key}: the parameters do not add up')
        rows[key] = {k: p[k] for k in ('encoder', 'heads', 'conditioning', 'total')}
    return rows


def windows_of(prep, label):
    p = inner(prep, label)
    dropped = p['qc_by_array_type']['epoch']['dropped']
    require(p['slots'] - sum(dropped.values()) == p['kept'], f'{label}: kept is not slots minus dropped')
    names = {'constant_channel': 'constant_channel', 'ptp_over_1000uV': 'peak_to_peak_over_1000_uv',
             'source_nan_flag': 'source_missing_value_flag'}
    return {'unit': '30-s epochs', 'scored': p['slots'], 'qc_passing': p['kept'],
            'dropped': {names[k]: v for k, v in dropped.items()}}, p


def rights_of(record, extra=None):
    out = rights(record) | {'reviewedAt': record['reviewedAt']}
    if extra:
        out.update(extra)
    return out


# ---------------------------------------------------------------------------- E2 sleep
def e2_sleep(boas, secondary_entries, audit, label='E2 sleep'):
    block = boas['e2_sleep']
    gates = inner(block['gates_E2_B-lin'], label + ' gates')
    gate_rows = []
    for q, g in gates.items():
        require(g['people'] == 100 and g['gate'] == gate_of(g['ci95'], g['chance']), f'{label} {q}: gate')
        gate_rows.append({'level': 'E2', 'question': q, 'arm': 'B-lin', 'mean': g['mean_ba'],
                          'interval_95': interval(g['ci95'], g['mean_ba'], f'{label} {q}', 0.0, 1.0),
                          'chance': g['chance'], 'floor': round(g['chance'] + 0.05, 10), 'gate': g['gate'],
                          'included_people': g['people']})
    entries = []
    for e in secondary_entries:
        v = val(e['ref'], label)
        if v['block'] != 'S3':
            continue
        gate, by = gate_label(e, label)
        require(gate == gates[v['question']]['gate'] and v['level'] == 'E2' and v['single_seed'] is True,
                f'{label} {v["id"]} {v["question"]}: the gate is not the E2 B-lin arm\'s')
        if 'B-lin' in v['mean_ba']:
            close(v['mean_ba']['B-lin'], gates[v['question']]['mean_ba'], f'{label} {v["id"]}: B-lin', 1e-12)
        entries.append(contrast(v, f'{label} {v["id"]} {v["question"]}', 'secondary', gate, by))
    require(len(entries) == 9 and sorted({e['id'] for e in entries}) == ['S3-P1', 'S3-P2', 'S3-P5'],
            f'{label}: the block declares P1, P2 and P5 on three questions')
    grid = val(block['heads_and_lora'], label)
    require(val(block['audit'], label) == 'pass' and audit['verdict'] == 'pass', f'{label}: the audit did not pass')
    checks = audit['checks']
    require(len(checks) == 25 and all(v is True for v in checks.values()), f'{label}: an audit check did not pass')
    res = audit['results']
    require(res['grid']['fits'] == 35 and res['grid']['all_complete_exact_steps'] is True
            and res['grid']['head_parameters'] == grid['head_parameters']
            and res['grid']['lora_parameters'] == grid['lora_parameters'], f'{label}: the grid')
    require(res['scores']['entries_recomputed'] == res['scores']['entries_equal'] == 9
            and res['scores']['min_included_people'] >= BOAS_MIN_PEOPLE, f'{label}: the recomputation')
    ck = res['checkpoints']
    # Every scanned place, by name and by content (the audit names the places; they are not repeated here).
    scans = [v for v in ck.values() if isinstance(v, dict) and 'name_hits' in v]
    left = sum(len(v[h]) for v in scans for h in ('name_hits', 'content_hits'))
    mirrors = [x for v in scans for k, x in v.items() if k.startswith('pt_in_')]
    require(len(scans) == 2 and left == 0 and not any(mirrors), f'{label}: a resume checkpoint was left')
    require(checks['checkpoint_ledger_each_written_then_deleted_at_completion']
            and checks['run_condition_and_design_fixed_at_freeze'], f'{label}: the checkpoint ledger or the design')
    chron = res['chronology']
    require(all(chron[k] is True for k in ('tools_frozen_before_first_production_event', 'all_fits_completed_after_tool_freeze',
                                           'manifest_after_last_fit_done', 'scored_once_after_manifest')),
            f'{label}: the chronology')
    design = res['design_fixed_at_freeze']
    require(design['projection_primary_gpu_hours'] <= 6.0, f'{label}: the run condition was not met')
    return {
        'level': 'E2', 'block': 'S3', 'role': 'secondary', 'seeds': 1, 'fits': res['grid']['fits'],
        'run_after_other_results': True,
        'disclosure': val(block['disclosure'], label),
        'chronology': {'tools_frozen_at': chron['tools_frozen_at'], 'first_fit_completed_at': chron['first_fit_completed'],
                       'last_fit_completed_at': chron['last_fit_completed'], 'block_frozen_at': chron['manifest_at'],
                       'scored_at': chron['scored_at'], 'audited_at': audit['at']},
        'resume_checkpoints': {
            'rule': ('Temporary and private: written only under the run root, only to resume a fit across segments, '
                     'deleted when that fit completed, never copied anywhere (owner decision, 7 October 2026).'),
            'written': ck['production_writes'], 'fits_that_wrote_one': ck['fits_with_checkpoints'],
            'left_after_the_run': left},
        'gates': gate_rows,
        'head_parameters': grid['head_parameters'], 'lora_parameters': grid['lora_parameters'],
        'note': 'The five A(SL-B) fits feed no contrast: the block declares P1, P2 and P5 only.',
        'entries': entries,
    }


# ---------------------------------------------------------------------------- audits
def audits_block(candidate, audits, pins, handoff):
    p, s, e = audits['primary'], audits['secondary'], audits['e2Sleep']
    for name, a, key in (('primary', p, 'primary'), ('secondary', s, 'secondary'), ('E2-sleep', e, 'e2_sleep')):
        require(a['verdict'] == 'pass' and val(candidate['audits'][key]['verdict'], name) == 'pass',
                f'the independent {name} audit did not pass')
        require(a['run_id'] == RUN_ID, f'the {name} audit names another run')
        require(pins[key] in handoff, f'the handoff does not record the {name} audit\'s hash')
    for name, a in (('primary', p), ('secondary', s)):
        require(len(a['checks']) == 10 and all(c['pass'] is True for c in a['checks'].values()),
                f'the independent {name} audit failed a check')
    pm = p['checks']['metrics_contrasts_intervals_verdicts_recomputed']['detail']
    sm = s['checks']['metrics_contrasts_intervals_verdicts_recomputed']['detail']
    require(pm['mismatches_float32'] == [] and pm['max_abs_diff_float32'] == 0.0, 'the primary audit found a mismatch')
    require(sm['mismatches_float32'] == 0 and sm['max_abs_diff_float32'] == 0.0 and sm['entries'] == 76,
            'the secondary audit found a mismatch')
    protocol_sha = candidate['sources_sha256']['protocol.json']
    require(p['inputs']['protocol.json'] == s['inputs']['protocol.json'] == protocol_sha,
            'the audits checked another protocol')
    carried = candidate['audits']['discrepancies_to_carry']
    require([c.split(':')[0] for c in carried] == ['D-5', 'D-S2', 'D-S3', 'E2 sleep'],
            'the items that must travel with the results changed')
    return {
        'primary': {'sha256': pins['primary'], 'verdict': 'pass', 'checks': len(p['checks']), 'passed': len(p['checks']),
                    'values_recomputed': pm['comparisons'], 'mismatches': 0},
        'secondary': {'sha256': pins['secondary'], 'verdict': 'pass', 'checks': len(s['checks']),
                      'passed': len(s['checks']), 'entries': sm['entries'], 'values_recomputed': sm['comparisons'],
                      'mismatches': 0},
        'e2_sleep': {'sha256': pins['e2_sleep'], 'verdict': 'pass', 'checks': len(e['checks']),
                     'passed': len(e['checks']), 'entries_recomputed': e['results']['scores']['entries_recomputed'],
                     'mismatches': 0},
        'must_travel': carried,
        'note': ('Each audit re-implements the definitions without importing the study code and recomputes from the '
                 'frozen predictions at the stored precision. They stay in the private run root and are bound here by '
                 'hash. Their discrepancies change no number, flag or gate.'),
    }


# ---------------------------------------------------------------------------- BOAS
def boas_conditions(candidate, review, review_text, record, smallest):
    req = candidate['boas_requirements']
    approval = review['ownerApproval']
    require(review['status'] == 'approved_by_owner_publishable_with_stated_gaps' and approval['given'] is True
            and approval['date'] == '2026-10-07', 'BOAS: the rights review is not approved by the owner')
    require(review['recommendation']['category'] == 'publishable_with_stated_gaps'
            and review['recommendation']['manifestDecisionIfApproved'] == record['decision'] == 'aggregate_preview',
            'BOAS: the manifest decision is not the approved one')
    require('2026-10-07' in review_text and 'publishable with stated gaps' in review_text,
            'BOAS: the review text does not state the approval')
    gaps = review['recommendation']['gapsToStateOnAnyPage']
    require(val(req['gaps_to_state_on_any_page'], 'gaps') == gaps == record['rightsReview']['gaps'] and len(gaps) == 3,
            'BOAS: the three gaps are not the review\'s')
    attribution = review['attribution']['proposedText']
    require(val(req['attribution'], 'attribution') == attribution == record['attribution'],
            'BOAS: the attribution is not the review\'s')
    require(val(req['review'], 'review')['given'] is True, 'BOAS: the candidate does not carry the approval')
    constraints = review['participantProtection']['constraints']
    require("pseudonymised in the public release" in constraints[7] and record['rightsReview']['participants']
            == 'pseudonymised in the public release', 'BOAS: the participants wording')
    require("Bitbrain's headband" in constraints[8] and "Bitbrain's headband" in record['rightsReview']['notAnEvaluationOf'],
            'BOAS: not an evaluation of the headband')
    require(record['rightsReview']['reviewedAt'] == review['reviewedAt']
            and record['rightsReview']['ownerApprovalDate'] == approval['date'], 'BOAS: review dates')
    # The draft privacy review, with its "Published here" clause replaced by what route 2 publishes (handoff).
    draft = review['draftPrivacyReview']
    head, _, rest = draft.partition(' Published here: ')
    _, _, tail = rest.partition('. ')
    require(record['privacyReview'].startswith(head + ' Published here: ') and record['privacyReview'].endswith(' ' + tail),
            'BOAS: the privacy review is not the reviewed draft')
    require('counts of people above or below zero' not in record['privacyReview'],
            'BOAS: the privacy review names a figure route 2 does not produce')
    for url in record['reviewBasis']:
        require(any(b.startswith(url) for b in review['reviewBasis']), f'BOAS: {url} is not in the review basis')
    require(record['license'] == 'CC0-1.0' and review['license']['declared'] == 'CC0'
            and record['licenseUrl'] == review['license']['licenseUrl'], 'BOAS: the licence')
    require(record['source'] == review['dataset']['source'], 'BOAS: the source')
    filt = val(req['filter'], 'filter')
    removed = val(filt['removed_at_fetch'], 'removed')
    require(len(removed) == 16 and all('percentile' in r for r in removed), 'BOAS: the percentiles removed at the fetch')
    require(smallest >= BOAS_MIN_PEOPLE, f'BOAS: a cell of {smallest} people')
    return {
        'owner_approval': {'approved_on': approval['date'], 'decision': 'publishable with stated gaps',
                           'conditions': approval['conditions']},
        'gaps': gaps,
        'attribution': attribution,
        'participants': 'pseudonymised in the public release',
        'not_an_evaluation_of': record['rightsReview']['notAnEvaluationOf'],
        'minimum_cell_people': BOAS_MIN_PEOPLE,
        'smallest_cell_people': smallest,
        'filter': ('The 16 BOAS per-person percentile entries were removed before the files left the private run '
                   'root, and the stage-0 pilot standard deviations are not carried. Only the polysomnography EEG and '
                   'the human-consensus stage labels were used; age, sex and BMI were never loaded.'),
    }


def boas_people(result):
    """Every count of people behind a BOAS figure."""
    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ('included_people', 'people', 'training_people') and count(x):
                    yield x
                else:
                    yield from walk(x)
        elif isinstance(v, list):
            for x in v:
                yield from walk(x)
    return list(walk(result['datasets']['boas']))


# ---------------------------------------------------------------------------- what the file says it leaves out
def all_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from all_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_keys(v)


def check_not_published(result, items):
    """Each not_published item is a claim about this file; the file must bear it out (pattern of 2026-10-05)."""
    keys = set(all_keys(result))
    tokens = {t for k in keys for t in re.split(r'[_\-/ ()\[\]]+', k.lower()) if t}
    text = json.dumps(result, ensure_ascii=False)

    def none_of(pattern):
        return not [k for k in keys if re.search(pattern, k, re.IGNORECASE)]
    rules = {
        'Per-window predictions and probabilities': lambda: none_of(
            r'prediction|probabilit|per_person|per_participant|per_night|per_recording|per_fold|fold_assign|feature|weights$'),
        'The per-person 10th, 50th and 90th percentiles': lambda: none_of(r'^p\d0|percentile|spread|median'),
        'The BOAS stage-0 pilot standard deviations': lambda: none_of(r'pilot|(^|_)sds?($|_)|std'),
        'Any BOAS cell of fewer than 20 people': lambda: (
            min(boas_people(result)) >= BOAS_MIN_PEOPLE
            and not tokens & {'age', 'sex', 'bmi', 'date', 'dates', 'clock', 'night', 'nights', 'hypnogram', 'trace',
                              'demographics'}),
        'Measured compute time': lambda: none_of(r'gpu|hours|wall|seconds|elapsed|steps_per_fold|by_block|guard'),
        'The text of the audits\' discrepancy lists': lambda: none_of(r'discrepanc|verdict_note') and 'D-1' not in text,
        'The per-recording metadata behind the third BOAS gap': lambda: 'EDF' not in text and 'PI22' not in text,
        'The release candidate\'s generated headline sentences and the handoff\'s prose': lambda: none_of(r'finding|headline'),
        'The handoff, the release candidate, the aggregates, the protocol, the BOAS rights review': None,
    }
    used = []
    for item in items:
        hits = [k for k in rules if item.startswith(k)]
        require(len(hits) == 1, f'not_published: no check for the item "{item[:70]}"')
        require(rules[hits[0]] is None or rules[hits[0]](),
                f'not_published: the file carries what the item says it leaves out: "{item[:70]}"')
        used.append(hits[0])
    require(sorted(used) == sorted(rules), 'not_published: an item is missing or named twice')


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


def withheld_values(candidate):
    """The OpenBMI per-person percentiles the candidate carries: refused by value too."""
    out = []
    for item in candidate['computed_not_proposed_for_site']:
        if item['ref'] is None:
            continue
        for q in val(item['ref'], item['item']).values():
            out += [q[k] for k in ('p10_pp', 'p50_pp', 'p90_pp') if isinstance(q.get(k), float)]
    return out


def bindings(route, candidate, files, handoff, manifest):
    """The candidate, the aggregate and the handoff name what they were built from; each is the pinned file."""
    require(candidate['run_id'] == route['runId'] == RUN_ID and candidate['route'] == ROUTE, 'another run or route')
    for name in ('aggregate.json', 'aggregate-primary.full.json', 'aggregate-secondary.full.json', 'protocol.json',
                 'audit-primary.json', 'audit-secondary.json', 'audit-e2-sleep.json'):
        require(files[name]['run_id'] == RUN_ID, f'{name} names another run')
    agg = files['aggregate.json']
    for name, key in PINNED.items():
        digest = ref_of(route, key)['sha256']
        require(candidate['sources_sha256'][name] == digest, f'the candidate names another {name}')
        if name != 'aggregate.json':
            require(agg['inputs_sha256'][name] == digest, f'the aggregate names another {name}')
    for name in ('aggregate.json', 'aggregate-primary.full.json', 'aggregate-secondary.full.json'):
        require(files[name]['protocol_sha256'] == route['protocol']['sha256'], f'{name} names another protocol')
    for key in ('releaseCandidate', 'aggregate', 'aggregatePrimary', 'aggregateSecondary', 'auditExtract', 'protocol',
                'boasRightsReview', 'boasRightsReviewText'):
        require(route[key]['sha256'] in handoff, f'the handoff does not record the {key} hash')
    require(candidate['status'] == CANDIDATE_STATUS and agg['status'] == CANDIDATE_STATUS,
            'the candidate is not in the state it was sealed in')
    require(files['protocol.json']['frozen_at'].startswith('2026-10-06T07:17')
            and [a['id'] for a in files['protocol.json']['amendments']] == [f'A{i}' for i in range(1, 9)],
            'the protocol is not the one frozen at 07:17 with eight amendments')
    for sentence in DESIGN['freeze'].split('. '):
        require(sentence.rstrip('.') in handoff, f'the handoff does not state the freeze: "{sentence[:50]}"')
    rules = files['protocol.json']['draft']['decision_rules']
    margins = val(candidate['margins'], 'margins')
    require(margins['delta_pp_balanced_accuracy'] == DELTA and margins['P3_min_error_removed'] == 0.2
            and margins['canary_demotes_at'] == 0.85, 'the margins are not the frozen ones')
    require(inner(candidate['wording_rule'], 'wording') == rules['flags'], 'the wording rule changed')
    return rules, margins


def handoff_figures(result):
    """The figures the pages print, written as the pinned handoff writes them: each must be there."""
    pp = lambda e: f'| {e["estimate_pp"]:+.2f} | [{e["interval_95_pp"][0]:+.2f}, {e["interval_95_pp"][1]:+.2f}] |'
    lr = lambda e: f'| {e["log_r"]:+.3f} | [{e["interval_95"][0]:+.3f}, {e["interval_95"][1]:+.3f}] |'
    pc = lambda r: f'{100 * r["mean"]:.1f}% ({100 * r["interval_95"][0]:.1f}–{100 * r["interval_95"][1]:.1f})'
    out = []
    for d in result['datasets'].values():
        rows = [*d.get('entries', []), *d.get('secondary', []), *d.get('e2_sleep', {}).get('entries', [])]
        for e in rows:
            if 'log_r' in e:
                out.append(lr(e))
            elif 'estimate_pp' in e:
                out.append(pp(e))
        for a in d.get('arms', []):
            if a['arm'] != 'A_SL-B':
                out.append(pc(a))
        for g in d.get('e2_sleep', {}).get('gates', []):
            out.append(pc(g))
        for arm, row in d.get('ledger', {}).items():
            if arm != 'timing':
                out.append(f'{row["parameters"]:,}')
    return out


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    route = manifest['route']
    require(route['id'] == ROUTE and manifest['approval']['decision'] == 'aggregate_preview'
            and manifest['approval']['date'] == manifest['reviewed_at'], 'no recorded approval for route 2')
    require(manifest['approval']['candidateStatusAtSeal'] == CANDIDATE_STATUS, 'the approval names another candidate state')
    require([d['date'] for d in manifest['approval']['ownerDecisions']] == ['2026-10-06'] + ['2026-10-07'] * 4,
            'the approval does not record the owner decisions of 2026-10-06 and 2026-10-07')
    require([s['id'] for s in manifest['sources']] == [d for _, _, d in DATASETS], 'the manifest names other sources')
    require(manifest['holds'] == [], 'route 2 has no hold')
    handoff = pinned_text(route['handoff'], 'handoff')
    candidate, candidate_sha = pinned(route['releaseCandidate'], 'release candidate')
    require(candidate_sha in handoff, 'the handoff does not record the release candidate')
    files = {name: pinned(ref_of(route, key), name)[0] for name, key in PINNED.items()}
    review_text = pinned_text(route['boasRightsReviewText'], 'BOAS rights review (text)')
    rules, margins = bindings(route, candidate, files, handoff, manifest)
    refs = reresolve(candidate, files)
    protocol = files['protocol.json']
    audits = {'primary': files['audit-primary.json'], 'secondary': files['audit-secondary.json'],
              'e2Sleep': files['audit-e2-sleep.json']}
    pins = {'primary': route['independentAudits']['primary']['sha256'],
            'secondary': route['independentAudits']['secondary']['sha256'],
            'e2_sleep': route['independentAudits']['e2Sleep']['sha256']}

    # Rights: OpenBMI is the released 2026-10-03 record, EESM19 the released sleep-scalp core track.
    records = {s['id']: s for s in manifest['sources']}
    for record in records.values():
        require(record['decision'] == 'aggregate_preview' and approved(record), f'{record["id"]}: approval record is incomplete')
        require(record['reviewedAt'] == manifest['reviewed_at'], f'{record["id"]}: reviewed on another date')
    openbmi = json.loads(SITE_LARGE_SOURCE.read_bytes())['results']['openbmi-cross-session-calibration']['rights']
    for k in ('name', 'source', 'license', 'licenseUrl', 'attribution', 'reviewBasis'):
        require(records['openbmi'][k] == openbmi[k], f'openbmi: {k} differs from the released 2026-10-03 record')
    require(records['openbmi']['privacyReview'].startswith(openbmi['privacyReview'] + ' Reused unchanged from the '
                                                           '2026-10-03 review'), 'openbmi: the privacy review is not the reviewed one')
    track = next(t for t in json.loads(SITE_MATRIX.read_bytes())['tracks'] if t['id'] == 'sleep-scalp')
    for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'reviewBasis'):
        require(records['eesm19'][k] == track[k], f'eesm19: {k} differs from the reviewed core track')
    require(records['eesm19']['privacyReview'].startswith(track['privacyReview'] + ' Reused unchanged from the '
                                                          '2026-09-20 review'), 'eesm19: the privacy review is not the reviewed one')

    threshold = margins['canary_demotes_at']
    demotions = inner(candidate['canary_demotions'], 'demotions')
    results = candidate['results']
    datasets = {}
    for ckey, domain, did in DATASETS:
        r = results[ckey]
        if did == 'eesm19':
            entries = secondary_of(r['secondary_entries'], 'EESM19')
            require(all(e['id'].startswith('S13-') and e['included_people'] == 20 and e['single_seed']
                        and e.get('label') == 'crude (20 people), one seed' for e in entries) and len(entries) == 6,
                    'EESM19: the S13 entries are crude, one seed, 20 people')
            windows, prep = windows_of(r['preparation'], 'EESM19 preparation')
            require(prep['people'] == 20, 'EESM19: another cohort')
            windows['unit'] = '30-s epochs (first scorer)'
            datasets[did] = {
                'dataset': 'EESM19', 'domain': 'sleep', 'role': 'secondary, crude', 'description': r['dataset'],
                'people': prep['people'], 'seeds': 1, 'label': 'crude (20 people), one seed',
                'windows': {k: v for k, v in windows.items() if k != 'scored'} | {'stored': windows['scored']},
                'questions': ['SL-A', 'SL-E', 'SL-F'],
                'stage_only_readout': ('Not computed here (S11 is defined on BOAS only): on EESM19, SL-E and SL-F are '
                                       'largely predictable from the current stage.'),
                'canary': canary_of(r['canary'], 'EESM19 canary', threshold, demotions['eesm19']),
                'secondary': entries,
                'parameters': parameters_of(results['MI']['cost_ledger_secondary_exact_by_audit'], 'EESM19 ledger',
                                            'E1/eesm19/'),
                'rights': rights_of(records[did]),
            }
            continue
        people = 51 if did == 'openbmi' else 100
        prevalence = val(r['windows_and_prevalence' if did == 'openbmi' else 'epochs_and_prevalence'], f'{did} prevalence')
        arms = arms_of(r['per_arm_balanced_accuracy'], r['probability_metrics'], people, did)
        gates = gates_of(r['gates'], arms, did)
        entries = entries_of(r, domain, gates, r['per_question_sentences_derived_by_audit'], did)
        require(sum(e['role'] == 'primary' for e in entries) == (8 if did == 'openbmi' else 13), f'{did}: primary entries')
        canary = canary_of(r['canary'], f'{did} canary', threshold, demotions[domain])
        ledger, led = ledger_of(r['cost_ledger_E1'], f'{did} ledger')
        # Each primary arm mean in a contrast is the per-arm row's.
        mean_of = {(a['level'], a['arm'], a['question']): a['mean'] for a in arms}
        for e in entries:
            for arm, m in e.get('mean_balanced_accuracy', {}).items():
                if (e['level'], arm, e['question']) in mean_of:
                    close(m, mean_of[(e['level'], arm, e['question'])], f'{did} {e["id"]} {arm}: arm mean', 1e-12)
        out = {
            'dataset': 'OpenBMI' if did == 'openbmi' else 'BOAS', 'domain': 'motor imagery' if did == 'openbmi' else 'sleep',
            'role': 'primary', 'description': r['dataset'], 'people': people,
            'windows': ({'unit': '2-s windows', 'qc_passing': prevalence['qc_passing_windows']} if did == 'openbmi'
                        else windows_of(r['preparation'], 'BOAS preparation')[0]),
            'questions': questions_of(protocol, domain, prevalence, people),
            'canary': canary,
            'route_sentence': route_sentence(r['route_sentence'], domain, entries, canary, led, f'{did} route sentence'),
            'entries': entries,
            'gates': gates,
            'arms': arms,
            'ledger': ledger,
        }
        if did == 'boas':
            require(out['windows']['qc_passing'] == prevalence['qc_passing_windows'], 'BOAS: QC counts disagree')
            out['secondary'] = secondary_of(r['secondary_entries'], 'BOAS', skip_block='S3') + s2_level1(
                r['S2_level1_computed_by_audit'], gates, 'BOAS S2 L1')
            coh = val(r['coherence_counts'], 'coherence')
            require(all(finite(x) and 0 <= x <= 1 for x in coh.values()), 'coherence: a share outside [0, 1]')
            out['coherence'] = {'what': ('Share of test windows where a dedicated binary head contradicts the same '
                                         'arm\'s five-stage head (K-all arms), and A(SL-B) against A(SL-A).'),
                                'shares': coh}
            out['e2_sleep'] = e2_sleep(r, r['secondary_entries'], audits['e2Sleep'])
            out['rights'] = rights_of(records[did], {k: records[did]['rightsReview'][k] for k in
                                                     ('gaps', 'participants', 'notAnEvaluationOf')}
                                      | {'rightsReviewedAt': records[did]['rightsReview']['reviewedAt'],
                                         'ownerApprovalDate': records[did]['rightsReview']['ownerApprovalDate']})
        else:
            out['secondary'] = secondary_of(r['secondary_entries'], 'OpenBMI') + s2_level1(
                r['S2_level1_computed_by_audit'], gates, 'OpenBMI S2 L1')
            out['secondary_parameters'] = parameters_of(r['cost_ledger_secondary_exact_by_audit'], 'MI ledger', 'E1/MI/')
            out['rights'] = rights_of(records[did])
        datasets[did] = out
    primary = [e for d in datasets.values() for e in d.get('entries', []) if e['role'] == 'primary']
    require(len(primary) == PRIMARY_COUNT, f'{len(primary)} primary entries, not {PRIMARY_COUNT}')
    smallest = min(boas_people({'datasets': datasets}))

    # Boundaries, with the E1 sharing conditional resolved by what was run.
    bounds = val(candidate['boundaries']['protocol'], 'boundaries')
    hits = [i for i, b in enumerate(bounds) if b.endswith(E2_MI_CONDITIONAL)]
    require(len(hits) == 1, 'the E1 sharing boundary changed: re-read its condition')
    bounds = [b[:-len(E2_MI_CONDITIONAL)] + E2_MI_OUTCOME if i in hits else b for i, b in enumerate(bounds)]
    not_run = val(candidate['not_run'], 'not run')
    require([n['arm'] for n in not_run] == ['Ying 2025 (S9)', 'E2 MI at 3 seeds (P2 co-primary)']
            and all(any(n['arm'].startswith(k) for n in not_run) for k, _ in NOT_RUN), 'the not-run arms changed')
    reported = val(candidate['not_reported'], 'not reported')
    boas_filter = val(candidate['boas_requirements']['filter'], 'filter')
    for opening, where, _ in NOT_REPORTED:
        pool = [x['item'] for x in reported] if where == 'not_reported' else [boas_filter['not_computed']]
        require(any(p.lower().startswith(opening.lower()) for p in pool), f'not reported: "{opening}" is not the candidate\'s')
    anchors = {a['url']: a['topic'] for a in protocol['draft']['literature_anchors']}
    require(all(u in anchors for u in LITERATURE_URLS), 'a literature anchor is not the protocol\'s')

    result = {
        'id': ROUTE,
        'title': 'One representation, several questions: shared encoders, fixed heads and question-conditioned heads',
        'run_id': RUN_ID,
        'design': DESIGN | {
            'margin': {'delta_pp': margins['delta_pp_balanced_accuracy'], 'p3_min_error_removed': margins['P3_min_error_removed'],
                       'fixed': 'by the owner on 2026-10-06, at the freeze, before any pilot result'},
            'flags': rules['flags'],
            'margin_bound': {'upper': ('P1, P4, P5 and their analogues: the upper bound of the more complex arm '
                                       'minus the simpler one below +delta'),
                             'lower': 'P2, S10 and S12: the lower bound of shared minus independent above -delta',
                             'log_r': 'P3 and S4: the lower bound of log R above log 0.8'},
            'route_sentence_rule': rules['route_sentences_per_domain']['fixed_heads_do_as_well_for_less'],
            'uncertainty': candidate['uncertainty_method'],
            'multiplicity': inner(candidate['multiplicity'], 'multiplicity'),
        },
        'datasets': datasets,
        'boas_conditions': boas_conditions(candidate, files['boas-rights-review.json'], review_text, records['boas'],
                                           smallest),
        'boundaries': {'protocol': bounds, 'secondary': val(candidate['boundaries']['secondary'], 'secondary'),
                       'added': inner(candidate['boundaries']['added'], 'added')},
        'not_run': [x for _, x in NOT_RUN],
        'not_reported': [x for _, _, x in NOT_REPORTED],
        'audits': audits_block(candidate, audits, pins, handoff),
        'literature': [{'topic': anchors[u], 'url': u} for u in LITERATURE_URLS],
    }
    payload = {
        'schema_version': 'bci-report-shared-representation-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': ('balanced accuracy, AUROC, Cohen\'s kappa, shares and the arms\' means are proportions in [0,1]; '
                         'estimate_pp and interval_95_pp are percentage points of balanced accuracy (x minus y); log_r is '
                         'the natural log of R; log loss is in nats per window; step_time_s and batch_time_s are '
                         'seconds, indicative; counts of people, windows, parameters and multiply-accumulates are whole '
                         'numbers'),
        'scope': ('Route 2 of the decision-research roadmap: shared encoders with fixed heads, question-conditioned '
                  'heads and independent models at matched data and compute, on motor imagery (OpenBMI) and sleep '
                  '(BOAS), with EESM19 as a crude replication. Every figure compares set-ups; none is a deployment '
                  'error rate, and nothing is ranked where intervals overlap. Every BOAS figure travels with the '
                  'three stated gaps and the attribution in boas_conditions.'),
        'results': {ROUTE: result},
        'status_only': [],
        'holds': [],
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'release_candidate_sha256': candidate_sha,
                       'references_reresolved': refs['top'] + refs['nested'],
                       'references_bound_through_the_aggregate': refs['bound_through_parent'],
                       'included': [ROUTE], 'inputs': [s['id'] for s in manifest['sources']], 'holds': []},
    }
    scrub_check(payload)
    validate_public(payload)
    check_not_published(result, payload['not_published'])
    # Refused by value too: an OpenBMI person percentile equal to a published number is a leak.
    published = set(numbers(payload))
    leaked = [v for v in withheld_values(candidate) if v in published]
    require(not leaked, f'a per-person value reached the export: {leaked[:3]}')
    for phrase in handoff_figures(result):
        require(phrase in handoff, f'the handoff does not state {phrase!r}')
    return payload


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    route = manifest['route']
    refs = [route['handoff'], route['releaseCandidate'], route['boasRightsReviewText']] + [ref_of(route, k) for k in PINNED.values()]
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    prov = payload['provenance']
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'release_candidate_sha256': prov['release_candidate_sha256'],
        'included': prov['included'], 'inputs': prov['inputs'], 'status_only': [], 'holds': [],
        'checks': [
            'pinned handoff, release candidate, consolidated aggregate, both run-root aggregates, the audit work '
            'extract, the protocol, the BOAS rights review (JSON and text) and the three independent audits',
            f'every {{source, value}} block of the release candidate re-resolves to the pinned file it names '
            f'({prov["references_reresolved"]} references; {prov["references_bound_through_the_aggregate"]} nested ones '
            'name the stage-0 report and are bound through the consolidated aggregate\'s hash)',
            'the candidate, the aggregate and the handoff record every pinned hash; the aggregates and the audits name '
            'the same run and protocol; the protocol is the one frozen at 07:17 UTC with eight engineering amendments',
            'the three independent audits passed (10, 10 and 25 checks; no mismatch in 1,673 and 971 recomputed values; '
            'the 9 E2-sleep entries equal; no resume checkpoint left); the handoff records each hash',
            'every difference flag, margin flag and wording follows from its interval and the frozen margin (2.0 pp; '
            'log 0.8 for P3 and S4); every contrast is the difference of its arms\' means; per-seed points average to '
            'the estimate; R is the ratio of remaining errors',
            'every gate follows from its arm\'s interval (chance + 5 pp to 95%; read-out AUROC above 0.55 for P3 and '
            'S4); E2-sleep gates from the E2 B-lin arm; secondary gates carry who attached them',
            'each route sentence follows from the counted questions\' P1 flags and the cost ledger\'s "for less" rule; '
            'the audit\'s per-question sentences follow from the flags',
            '21 primary entries; every per-arm interval holds its mean and the per-seed means average to it; '
            'counts equal windows and shares; the canary demoted nothing',
            'BOAS: the owner-approved review, its three gaps and attribution in the candidate, the manifest and the '
            'file; every BOAS cell pools at least 20 people; the privacy review is the reviewed draft with its '
            '"Published here" clause replaced',
            'OpenBMI and EESM19 rights are the released records\'',
            'every not_published item is checked against the file',
            'per-person percentiles refused by key, fragment and value; no demographics, dates or measured compute time',
            'the printed figures are the ones the pinned handoff states',
            'no private paths or hosts, file or participant identifiers',
        ],
        'audit_bindings': {
            'bound': [
                'release candidate bytes: pinned here, and recorded in the handoff',
                'every candidate figure: equal, at its JSON pointer, to the pinned file it names',
                'aggregates, protocol, audit extract and BOAS rights review: by the hashes the candidate, the aggregate '
                'and the handoff record',
                'independent audits: opened and checked here, by the hashes the candidate, the aggregate and the '
                'handoff record',
            ],
            'not_bound': [
                'the stage-0 report, which the aggregate cites for the canary and preparation counts: bound through the '
                'aggregate\'s hash, not opened here (its file name marks it private)',
            ],
        },
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
