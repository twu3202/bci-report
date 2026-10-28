"""Independent audit of ssvep-followups-update.json: every figure in the served file against the pinned sources.

A separate program from export_ssvep_followups_update.py and from the five block modules it assembles
(ssvep_followups/blocks_xspec.py, blocks_eigen.py, blocks_pooling.py, blocks_practical.py, blocks_weights.py). It
imports none of them: it reads the served bytes, the release manifest and the files the manifest pins, re-derives
every study block from the ORIGINAL aggregates by its own reading of them, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- levels and contrasts are read from each study's own aggregate (the cross-spectral copy of gate A1, the coherence
  aggregate, the A/C summary's embedded verified aggregates, the B/D aggregate, the three weighting aggregates), with
  ids worked out here from the aggregates' own labels; every contrast must equal the difference of its two levels;
- a reused comparator must equal the card it comes from (card 5 and card 7 in the released 2026-10-20 file, card 8 in
  the cross-spectral aggregate, card 9 in the coherence aggregate, card 10 in the A/C summary) to the last bit, and the
  whitened-readout gap of card 8 is re-derived as the difference of the two source levels;
- the shares of card 12 are recomputed as count / 11,200 from the aggregate's edge counts; the reference check is
  recomputed as counts; the CPU component medians are read from the timing aggregate, wall clock only;
- the designs, the interval methods and every check count are recomputed from the protocols, approvals, reviews and
  receipts;
- every export code points into its source at the value the served file gives;
- strings are compared where a source gives them; every other string sits under a prefix or a leaf this audit names
  as editorial (display names, limitation keys, card wording), whose wording the export and its tests check;
- each shared row's interval home, whether its cards' intervals differ, and its aliases are worked out here from the
  intervals this audit derives and the display names; the context-only pins are checked bound by a pinned record;
- last, the served bytes must equal the export program's fresh build from the same manifest bytes, run in a separate
  process: that binds every editorial string by bytes, while this program still imports none of the export's code;
- the two served copies are one, the served file names the manifest it was built from, the released 2026-10-20 file
  keeps the bytes its own export audit names, and no private path, no private user, host or volume name, no withheld
  value, no part of the comment thread and no form of the commenter's confidence figure is in it.

    python3 pipeline/publication/audit_ssvep_followups_export.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PUBLICATION = Path(__file__).resolve().parent
LOCAL = PUBLICATION / 'local_paths.json'
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'ssvep-followups-release-manifest.json'
AUDIT = REVIEW / 'ssvep-followups-export-audit.json'
SERVED = (PROJECT / 'site/src/data/ssvep-followups-update.json',
          PROJECT / 'site/public/data/ssvep-followups-update.json')
RELEASED_SERVED = (PROJECT / 'site/src/data/new-ssvep-frequencies-update.json',
                   PROJECT / 'site/public/data/new-ssvep-frequencies-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"

STUDIES = ('xspec', 'coherence_eigen', 'harmonic_pooling', 'harmonic_pooling_wearable', 'practical_settings',
           'harmonic_gap', 'fixed_decay', 'rising_weights')
NO_TRAINING, DETERMINISTIC = 'no training', 'deterministic fit'
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
SCORE, SCORE_DIFFERENCE, WIN = 'squared correlation', 'difference of squared correlations', 'pairwise win fraction'
EXPORT_NAME = {'u8': 'held8', 'seen_ba': 'seen32'}
TOL = 1e-12
# The editorial decisions this audit holds the file to (plan section 2.1, owner decisions D23, D25, D28).
CARDS = ((8, 'cross-spectral', ['xspec']), (9, 'eigenvalue-pooling', ['coherence_eigen']),
         (10, 'harmonic-pooling', ['harmonic_pooling', 'harmonic_pooling_wearable']),
         (11, 'practical-settings', ['practical_settings']), (12, 'harmonic-gap', ['harmonic_gap']),
         (13, 'fixed-decay', ['fixed_decay']), (14, 'rising-weights', ['rising_weights']))
NOT_RUN_ROWS = {'xspec': 2, 'coherence_eigen': 3, 'harmonic_pooling': 2, 'harmonic_pooling_wearable': 3,
                'practical_settings': 4, 'harmonic_gap': 2, 'fixed_decay': 1, 'rising_weights': 2}
# The 2 s / 8-electrode cell of card 11 and the codes card 10 and card 5 give the same pipelines.
ANCHOR_CELL = 'w500-c8'
B_TO_A = {'CCA-RAW-H3': 'CCA-RAW', 'RAW-HARM-SUM-H3': 'RAW-HARM-SUM', 'RAW-LEAD3-RIDGE': 'RAW-LEAD3-RIDGE',
          'EIG-RAW6-RIDGE': 'EIG-RAW'}
# Strings this audit does not derive: the modules' and the export's editorial wording, checked by them and their tests
# and bound by bytes through fresh_build().
EDITORIAL = (
    ('title',), ('metric_units',), ('scope',), ('placement',), ('endpoints',), ('interval_adjustment',),
    ('name_key',), ('shared_estimates',), ('engineering_disclosures',),
    ('rights', 'datasets', 'beta', 'published_here'), ('rights', 'datasets', 'wearable_102', 'published_here'),
    ('rights', 'credits', 'fbcca', 'name'), ('rights', 'credits', 'fbcca', 'method_page'),
    ('rights', 'credits', 'fbcca', 'used_for'))
EDITORIAL_IN_STUDY = ('limitations_keys', 'display_names', 'contrast_limitations', 'anchor', 'answers_not_run',
                      'identity', 'qualifiers')
# Leaf names whose strings are the modules' wording inside the derived sections (every figure beside them is derived).
EDITORIAL_LEAVES = {'method', 'conditional_on', 'paired_across', 'shared_draws', 'adjustment', 'training', 'variant',
                    'item', 'name', 'basis', 'label', 'ties', 'rule', 'denominator', 'statistics', 'components',
                    'candidate_order', 'tie_rule', 'same_cohort_as', 'same_windows_as', 'amplitude', 'dataset',
                    'average_of', 'role', 'endpoint', 'measure', 'limitation_key', 'pooled', 'exact_profile', 'n',
                    'weight', 'flat', 'margin_unit', 'decisions_note', 'description', 'filter', 'score', 'realisation',
                    'input', 'page', 'en', 'zh', 'sub_band_weights', 'clock', 'unit', 'statistic',
                    'buffers', 'amortised', 'readout_head', 'family', 'code', 'reason',
                    'same_estimate_as', 'roles'}


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def location(path):
    path = str(path)
    if Path(path).is_absolute():
        return Path(path)
    if path.startswith('research/'):
        try:
            root = json.loads(LOCAL.read_text()).get('researchRoot')
        except FileNotFoundError:
            root = None
        return (Path(root) if root else PROJECT / 'research') / path[len('research/'):]
    return PROJECT / path


def raw(ref):
    data = location(ref['path']).read_bytes()
    check(digest(data) == ref['sha256'], f'{Path(ref["path"]).name}: not the pinned bytes')
    return data


def doc(ref):
    data = raw(ref)
    return json.loads(data) if ref['path'].endswith('.json') else data.decode('utf-8')


def same(a, b):
    """Equal, type included: an int is not a float and a boolean is not a number."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def walk(doc_, ptr):
    cur = doc_
    for tok in ptr.split('/')[1:] if ptr else []:
        tok = tok.replace('~1', '/').replace('~0', '~')
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    return cur


def ptr(*tokens):
    return ''.join('/' + str(x).replace('~', '~0').replace('/', '~1') for x in tokens)


def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    else:
        yield trail, value


def nums(value):
    return [v for _, v in leaves(value) if is_number(v)]


def show(path):
    return '/'.join(map(str, path))


def word_count(text, pattern):
    words = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6, 'two': 2, 'three': 3}
    m = re.search(pattern, text)
    check(m is not None, f'no {pattern!r} in the record')
    g = m.group(1)
    return int(g.replace(',', '')) if g[0].isdigit() else words[g]


class Table:
    """What the served file must hold: figures (numbers, booleans, nulls) and the strings the sources give."""

    def __init__(self):
        self.figures, self.strings, self.sets = {}, {}, {}

    def unordered(self, path, rows):
        self.sets[path] = sorted(json.dumps(r, sort_keys=True) for r in rows)

    def put(self, path, value, kind='copied'):
        if isinstance(value, dict):
            for k, v in value.items():
                self.put(path + (k,), v, kind)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                self.put(path + (i,), v, kind)
        elif isinstance(value, str):
            check(self.strings.get(path, value) == value, f'{show(path)}: two expected strings')
            self.strings[path] = value
        else:
            want = NULL if value is None else value
            if path in self.figures:
                old = self.figures[path][0]
                check((old is NULL and want is NULL) or (old is not NULL and want is not NULL and same(old, want)),
                      f'{show(path)}: two expected values')
            self.figures[path] = (want, kind)


# ---------------------------------------------------------------------------- the sources
def sources(manifest):
    s = {'owner': doc(manifest['approval']['ownerDecisions'])}
    for group in ('planning', 'published', 'credits', 'crossChecks'):
        for k, r in manifest[group].items():
            s[k] = doc(r)
    for m, block in manifest['blocks'].items():
        for k, r in block['pins'].items():
            s[f'{m}:{k}'] = doc(r)
    for study, h in manifest['handoffContext'].items():
        s[f'handoff:{study}'] = doc(h)
        if 'queue_handoff' in h:
            s[f'queue_handoff:{study}'] = doc(h['queue_handoff'])
    for k, r in manifest['contextPins'].items():
        raw(r)                                            # context only: its bytes are checked, nothing is read
        check(r['role'] == 'context only, never a copy source', f'context {k}: a copy source')
        by = manifest['blocks'][r['block']]['pins'][r['bound_by']]
        text = raw(by).decode('utf-8')
        check((r['binding'] == 'sha256' and r['sha256'] in text)
              or (r['binding'] == 'file name' and Path(r['path']).name in text),
              f'context {k}: {r["bound_by"]} does not bind it')
    return s


def level(t, path, mean, ci, people, seeds, origin, extra=None):
    if ci is not None:
        check(len(ci) == 2 and ci[0] <= mean <= ci[1], f'{show(path)}: the source interval does not hold its point')
    t.put(path, {'estimate': mean, 'interval': None if ci is None else list(ci), 'unit': PROPORTION, 'people': people,
                 'seeds': seeds, 'origin': origin} | (extra or {}))


def contrast(t, path, est, role, left, right, mean, ci, people, seeds, flags, unit=DIFFERENCE, extra=None):
    check(abs(est[left] - est[right] - mean) <= TOL, f'{show(path)}: not the difference of its levels')
    check(ci[0] <= mean <= ci[1], f'{show(path)}: the source interval does not hold its point')
    t.put(path, {'role': role, 'left': left, 'right': right, 'estimate': mean, 'interval': list(ci), 'unit': unit,
                 'people': people, 'seeds': seeds, 'flags': flags} | (extra or {}))


def below_two_decimals(ci):
    return [side for side, b in zip(('lower', 'upper'), ci) if b != 0 and abs(b * 100) < 0.005]


def card_of(released, study):
    return next(c for c in released['placement']['cards'] if study in c['studies'])


def put_hashes(t, P, pins, fields):
    for field, pin in fields.items():
        t.put(P + (field,), pins[pin]['sha256'])


# ---------------------------------------------------------------------------- card 8, the cross-spectral scorer
def study_xspec(t, s, pins):
    P = ('studies', 'xspec')
    ex, pr, au, ap, er = (s[f'xspec:{k}'] for k in (
        'xspec_export', 'xspec_protocol', 'xspec_audit', 'xspec_approval', 'xspec_execution_review'))
    review, handoff, runner = s['xspec:xspec_review'], s['xspec:xspec_handoff'], s['xspec:xspec_runner']
    rel = s['released']
    diag = rel['studies']['cca_diagnostics']
    card5 = card_of(rel, 'cca_diagnostics')
    check(ap['verified_aggregate_sha256'] == pins['xspec_export']['sha256'] == au['aggregate_sha256']
          and ap['status'] == 'APPROVED_AGGREGATE_HANDOFF', 'xspec: the approval does not bind the A1 copy')
    st = pr['statistics']
    check(ex['bootstrap_n'] == st['bootstrap_draws'] and ex['bootstrap_seed'] == st['bootstrap_seed'], 'xspec: draws')
    check("np.quantile(b,[.025,.975],method='linear')" in runner, 'xspec: the runner percentile rule')
    lvl = int(re.match(r'percentile(\d+)', st['interval']).group(1)) / 100
    t.put(P + ('interval_method',), {'draws': ex['bootstrap_n'], 'seed': ex['bootstrap_seed'], 'level': lvl})
    t.put(P + ('design', 'dataset'), diag['design']['dataset'])
    t.put(P + ('design', 'endpoints'), diag['design']['endpoints'])
    t.put(P + ('design', 'harmonics'), diag['design']['harmonics'])
    sa = pr['source_admission']
    t.put(P + ('design',), {'source_windows_per_fit': sa['rows_per_fit'],
                            'seen_frequencies_per_fit': sa['candidates_per_fit'], 'main_fits': pr['main_fit_count']})
    cells, mlp = pr['main_cells'], pr['mlp']
    for i, c in enumerate(cells):
        row = {'code': c, 'fits': cells[c]['fits'], 'input_count': cells[c]['features']}
        if c == 'XS-MLP':
            row |= {'training_seeds': len(mlp['seeds']), 'hidden_units': mlp['shape'][1], 'training_epochs': mlp['epochs']}
        t.put(P + ('design', 'arms', i), row)
    reused = [c for c in ex['arms'] if c not in cells]
    for i, c in enumerate(reused):
        t.put(P + ('design', 'comparators', i), {'code': c, 'card': card5['card']})
    people = ex['person_count']
    est, worst = {}, 0.0
    for c, arm in ex['arms'].items():
        for e, src in EXPORT_NAME.items():
            m = arm[src]
            lid = f'{c}/{e}'
            if c in reused:
                twin = diag['levels'][lid]
                diff = max(abs(a - b) for a, b in zip([m['mean']] + m['ci95'], [twin['estimate']] + twin['interval']))
                check(diff <= TOL, f'xspec {lid}: not card 5’s level')
                worst = max(worst, diff)
                level(t, P + ('levels', lid), m['mean'], m['ci95'], people, twin['seeds'], 'reused_cca_diagnostics')
            else:
                level(t, P + ('levels', lid), m['mean'], m['ci95'], people,
                      len(mlp['seeds']) if c == 'XS-MLP' else DETERMINISTIC, 'new')
            est[lid] = m['mean']
    for c in reused:
        t.put(P + ('reused', c), {'card': card5['card'], 'study': 'cca_diagnostics', 'anchor': card5['anchor'], 'code': c})
    primary = {tuple(x) for x in st['primary_held8']}
    ridge = {c for c in cells if c != 'XS-MLP'} | {'SHARED-RIDGE'}
    for c in ex['contrasts']:
        a, b, e = c['a'], c['b'], 'u8' if c['metric'] == 'held8' else 'seen_ba'
        ci = c['ci95']
        flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1]}
        flags |= {k: c[k] for k in ('above_zero', 'below_zero', 'strict_equivalence_2pp',
                                    'prespecified_noninferiority_to_CCA')}
        if below_two_decimals(ci):
            flags['bound_below_two_decimals'] = below_two_decimals(ci)
        seeds = len(mlp['seeds']) if 'XS-MLP' in (a, b) else DETERMINISTIC if {a, b} & ridge else NO_TRAINING
        contrast(t, P + ('contrasts', f'{a} minus {b}/{e}'), est,
                 'primary' if (c['metric'] == 'held8' and (a, b) in primary) else 'secondary',
                 f'{a}/{e}', f'{b}/{e}', c['mean'], ci, people, seeds, flags)
    # The whitened readout against CCA: no planned contrast; the difference of the two source levels.
    check(not any({c['a'], c['b']} == {'XS-RIDGE-W', 'CCA-RAW'} for c in ex['contrasts']), 'xspec: a W-CCA contrast')
    row = re.findall(r'^\| XS-RIDGE-W \| (-?[\d.]+) \| (-?[\d.]+) \| (-?[\d.]+) \|$', handoff, re.MULTILINE)
    check(len(row) == 1, 'xspec: the handoff gives no descriptive gap')
    for e, printed in (('u8', row[0][0]), ('seen_ba', row[0][2])):
        gap = est[f'XS-RIDGE-W/{e}'] - est[f'CCA-RAW/{e}']
        check(f'{100 * gap:.2f}' == printed, f'xspec: the {e} gap is not the handoff’s {printed}')
        t.put(P + ('descriptive_gaps', f'XS-RIDGE-W minus CCA-RAW/{e}'),
              {'left': f'XS-RIDGE-W/{e}', 'right': f'CCA-RAW/{e}', 'estimate': gap, 'unit': DIFFERENCE,
               'export_codes': ['#' + ptr('arms', 'XS-RIDGE-W', EXPORT_NAME[e]),
                                '#' + ptr('arms', 'CCA-RAW', EXPORT_NAME[e])]},
              'derived')
    t.unordered(P + ('undefined',), [{'contrast': 'XS-RIDGE-W minus CCA-RAW', 'reason': 'not_a_planned_contrast'}])
    af, can = pr['audit_fits'], pr['canaries']['training_label_permutation']
    ridge_refits, mlp_refits = af['independent_ridge_refits']['count'], len(af['mlp_full_refits'])
    check(au['total_fits'] == pr['main_fit_count'] + af['bridge_count'] + can['count'] + ridge_refits + mlp_refits,
          'xspec: the fit counts do not add up')
    t.put(P + ('checks',), {
        'release_approval': {'approved': ap['status'] == 'APPROVED_AGGREGATE_HANDOFF'},
        'release_review': {'passed': 'PASS for root' in review,
                           'technical_holds': 0 if 'There are **no remaining technical audit holds**' in review else None},
        'execution_review': {'passed': er['status'] == 'PASS'},
        'release_audit': {'passed': au['audit_status'].startswith('PASS'), 'sealed_artifacts': au['seal_artifact_count'],
                          'source_admission_sets': au['source_admission_sets_verified'],
                          'metric_entries_recomputed': au['metric_entries_recomputed'],
                          'retained_payloads_rehashed': au['retained_payloads_rehashed'],
                          'archived_originals_rehashed': au['archived_originals_rehashed']},
        'fits': {'main': pr['main_fit_count'], 'additional': au['total_fits'] - pr['main_fit_count'],
                 'total': au['total_fits'], 'bridges': af['bridge_count'], 'canaries': can['count'],
                 'independent_ridge_refits': ridge_refits, 'independent_mlp_refits': mlp_refits,
                 'mlp_forward_reconstructions': af['mlp_forward_reconstructions']},
        'cca_identity': {'pairs': pr['identity_audit']['all_pair_count']},
        'pre_score_corrections': {'count': word_count(handoff, r'(\w+) disclosed pre-score engineering corrections')},
        'same_scores_as_card_5': {'passed': worst <= TOL, 'card': card5['card'], 'max_absolute_difference': worst},
    }, 'derived')
    t.put(P + ('checks', 'same_scores_as_card_5', 'codes'), reused)
    t.put(P + ('checks', 'same_scores_as_card_5', 'tolerance'), TOL, 'editorial')
    put_hashes(t, P, pins, {'source_sha256': 'xspec_export', 'review_sha256': 'xspec_review',
                            'audit_summary_sha256': 'xspec_audit', 'approval_sha256': 'xspec_approval',
                            'protocol_sha256': 'xspec_protocol', 'freeze_sha256': 'xspec_freeze',
                            'execution_review_sha256': 'xspec_execution_review', 'caveats_sha256': 'xspec_caveats',
                            'runner_sha256': 'xspec_runner', 'released_sha256': 'released'})
    return est


# ---------------------------------------------------------------------------- card 9, coherence and eigenvalue
def study_eigen(t, s, pins, xpins):
    P = ('studies', 'coherence_eigen')
    ex, pr, au, ap, er = (s[f'eigen:{k}'] for k in (
        'eigen_export', 'eigen_protocol', 'eigen_audit', 'eigen_approval', 'eigen_execution_review'))
    numerical, review = s['eigen:eigen_numerical_review'], s['eigen:eigen_review']
    xs, xpr = s['xspec:xspec_export'], s['xspec:xspec_protocol']
    rel = s['released']
    diag = rel['studies']['cca_diagnostics']
    card5, card8 = card_of(rel, 'cca_diagnostics'), next(c for c in rel['placement']['cards'] if c['card'] == 8)
    check(ap['aggregate_sha256'] == pins['eigen_export']['sha256'] == au['aggregate_sha256']
          and ap['status'] == 'APPROVED_AGGREGATE_HANDOFF', 'eigen: the approval does not bind the aggregate')
    st = pr['statistics']
    check("np.quantile(b,[.025,.975],method='linear')" in s['xspec:xspec_runner'], 'eigen: the imported percentile rule')
    t.put(P + ('interval_method',), {'draws': st['bootstrap_draws'], 'seed': st['bootstrap_seed'], 'level': 0.95})
    dataset = diag['design']['dataset']
    t.put(P + ('design', 'dataset'), dataset)
    t.put(P + ('design', 'endpoints'), diag['design']['endpoints'])
    t.put(P + ('design', 'harmonics'), diag['design']['harmonics'])
    sa = pr['source_admission']
    t.put(P + ('design',), {'source_windows_per_fit': sa['rows_per_fit'],
                            'seen_frequencies_per_fit': sa['candidates_per_fit'], 'main_fits': pr['main_fit_count']})
    cells, controls = pr['main_cells'], pr['analytic_controls']
    for i, c in enumerate(cells):
        t.put(P + ('design', 'arms', i), {'code': c, 'input_count': cells[c],
                                          'fits': dataset['person_folds'] * dataset['frequency_rotations']}, 'derived')
    for i, c in enumerate(controls):
        t.put(P + ('design', 'controls', i, 'code'), c)
    reused = [c for c in ex['arms'] if c not in cells and c not in controls]
    from_card8 = [c for c in reused if c in xpr['main_cells']]
    for i, c in enumerate(reused):
        t.put(P + ('design', 'comparators', i), {'code': c, 'card': card8['card'] if c in from_card8 else card5['card']})
    people = ex['person_count']
    est, worst = {}, {5: 0.0, 8: 0.0}
    for c, arm in ex['arms'].items():
        for e, src in EXPORT_NAME.items():
            m, lid = arm[src], f'{c}/{e}'
            if c in from_card8:
                twin = xs['arms'][c][src]
                d = max(abs(a - b) for a, b in zip([m['mean']] + m['ci95'], [twin['mean']] + twin['ci95']))
                worst[8] = max(worst[8], d)
                check(d <= TOL, f'eigen {lid}: not card 8’s level')
                level(t, P + ('levels', lid), m['mean'], m['ci95'], people, DETERMINISTIC, 'reused_xspec')
            elif c in reused:
                twin = diag['levels'][lid]
                d = max(abs(a - b) for a, b in zip([m['mean']] + m['ci95'], [twin['estimate']] + twin['interval']))
                worst[5] = max(worst[5], d)
                check(d <= TOL, f'eigen {lid}: not card 5’s level')
                level(t, P + ('levels', lid), m['mean'], m['ci95'], people, twin['seeds'], 'reused_cca_diagnostics')
            else:
                level(t, P + ('levels', lid), m['mean'], m['ci95'], people,
                      DETERMINISTIC if c in cells else NO_TRAINING, 'new')
            est[lid] = m['mean']
    check(ex['arms']['JOINT-TOP'] == ex['arms']['CCA-RAW'], 'eigen: JOINT-TOP is not CCA')
    for c in reused:
        card = card8 if c in from_card8 else card5
        t.put(P + ('reused', c), {'card': card['card'], 'study': 'xspec' if c in from_card8 else 'cca_diagnostics',
                                  'anchor': card['anchor'], 'code': c})
    primary = {tuple(x) for x in st['primary_held8']}
    untrained = set(controls) | {'CCA-RAW'}
    claim = ex['prespecified_eigenvalue_claim']
    for c in ex['contrasts']:
        a, b, e = c['a'], c['b'], 'u8' if c['metric'] == 'held8' else 'seen_ba'
        ci = c['ci95']
        flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'above_zero': c['above_zero'],
                 'below_zero': c['below_zero']}
        check(c['above_zero'] is (ci[0] > 0) and c['below_zero'] is (ci[1] < 0), f'eigen {a} minus {b}: sign flags')
        if below_two_decimals(ci):
            flags['bound_below_two_decimals'] = below_two_decimals(ci)
        if (a, b, c['metric']) == ('EIG-RAW', 'CCA-RAW', 'held8'):
            check(claim['paired_difference'] == c, 'eigen: the claim names another contrast')
            flags |= {'strict_5pp_equivalence': claim['strict_5pp_equivalence'],
                      'strict_5pp_noninferiority': claim['strict_5pp_noninferiority']}
        contrast(t, P + ('contrasts', f'{a} minus {b}/{e}'), est,
                 'primary' if (c['metric'] == 'held8' and (a, b) in primary) else 'secondary', f'{a}/{e}', f'{b}/{e}',
                 c['mean'], ci, people, NO_TRAINING if {a, b} <= untrained else DETERMINISTIC, flags)
    low = [c for c in ex['contrasts'] if (c['a'], c['b']) == ('EIG-SPEC', 'SPEC-HARM-SUM')][0]['ci95'][0]
    check(low == -2.2321428571386387e-06, 'eigen: the EIG-SPEC pooling lower bound is not the source double')
    pairs = 0
    for a_, b_ in ((au['verified_aggregate_arms'], ex['arms']), (au['all_13_verified_contrasts'], ex['contrasts']),
                   (au['verified_prespecified_eigenvalue_claim'], claim)):
        for path, v in leaves(a_):
            w = b_
            for k in path:
                w = w[k]
            if is_number(v):
                check(abs(v - w) <= TOL, f'eigen: the aggregate differs from the release audit at {show(path)}')
                pairs += 1
    fits = {'main': pr['main_fit_count'], 'independent_refits': pr['independent_refit_count'],
            'bridges': pr['bridge_count'], 'canaries': pr['canary_count'], 'total': pr['total_fit_count']}
    check(fits['total'] == sum(v for k, v in fits.items() if k != 'total') == au['total_fits'], 'eigen: fit counts')
    gate, qc = au['geometry_gate'], au['geometry_qc_summary']
    t.put(P + ('checks',), {
        'release_approval': {'approved': ap['status'] == 'APPROVED_AGGREGATE_HANDOFF'},
        'numerical_review': {'passed': 'Technical PASS' in numerical, 'technical_holds': len(au['technical_holds'])},
        'interpretation_review': {'passed': '**Interpretation PASS.**' in review},
        'execution_review': {'passed': er['status'] == 'PASS'},
        'release_audit': {'passed': au['status'].startswith('PASS'), 'sealed_artifacts': au['seal_artifacts_verified'],
                          'source_admission_sets': au['source_admission_sets_verified'],
                          'metric_entries_reconstructed': au['metric_entries_reconstructed'],
                          'contrasts_reconstructed': au['formal_contrasts_reconstructed']},
        'fits': fits,
        'cca_identity': {'pairs': gate['identity_pairs'],
                         'decisions_identical': au['joint_top_CCA_squared_max_absolute_error'] == 0.0},
        'coherence_zero_gate': {'gated_pairs': qc['coherence_gated_pairs'], 'of': qc['coherence_total_pairs']},
        'aggregate_equals_release_audit': {'passed': True, 'numeric_values': pairs},
        'joint_top_equals_cca': {'passed': ex['arms']['JOINT-TOP'] == ex['arms']['CCA-RAW']},
        'same_scores_as_card_5': {'passed': worst[5] <= TOL, 'card': card5['card'], 'max_absolute_difference': worst[5]},
        'same_scores_as_card_8': {'passed': worst[8] <= TOL, 'card': card8['card'], 'max_absolute_difference': worst[8]},
    }, 'derived')
    t.put(P + ('checks', 'same_scores_as_card_5', 'codes'), [c for c in reused if c not in from_card8])
    t.put(P + ('checks', 'same_scores_as_card_8', 'codes'), from_card8)
    for k in ('same_scores_as_card_5', 'same_scores_as_card_8'):
        t.put(P + ('checks', k, 'tolerance'), TOL, 'editorial')
    t.put(P + ('answers_not_run', 0), {'card': 6, 'same_inputs_as_card_6': False}, 'editorial')
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'eigen_export', 'review_sha256': 'eigen_review',
                            'numerical_review_sha256': 'eigen_numerical_review', 'audit_summary_sha256': 'eigen_audit',
                            'approval_sha256': 'eigen_approval', 'protocol_sha256': 'eigen_protocol',
                            'freeze_sha256': 'eigen_freeze', 'execution_review_sha256': 'eigen_execution_review',
                            'runner_sha256': 'eigen_runner', 'released_sha256': 'released'})
    return est


# ---------------------------------------------------------------------------- card 10, pooling (A on BETA, C on Wearable)
def direction(ci):
    return 'above zero' if ci[0] > 0 else 'below zero' if ci[1] < 0 else 'unresolved'


def study_pooling(t, s, pins):
    P = ('studies', 'harmonic_pooling')
    sm, ap = s['pooling:ac_summary'], s['pooling:ac_approval']
    A, pa = sm['verified_A_aggregate'], s['pooling:ac_protocol']['modules']['A']
    rel, coh = s['released'], s['pooling:coherence_aggregate']
    check(ap['summary_sha256'] == pins['ac_summary']['sha256'] and ap['aggregate_sha256'] == sm['aggregate_sha256']
          and ap['status'] == 'APPROVED_AGGREGATE_A_C_HANDOFF', 'A/C: the approval does not bind the summary')
    st = pa['statistics']
    check(f'default_rng({st["bootstrap_seed"]}).integers(0,70,size=({st["bootstrap_draws"]},70))'
          in s['pooling:pooling_runner'], 'A: the runner draws')
    t.put(P + ('card',), 10, 'editorial')
    t.put(P + ('interval_method',), {'draws': st['bootstrap_draws'], 'seed': st['bootstrap_seed'],
                                     'level': int(re.search(r'nominal(\d+)%CI', st['multiplicity']).group(1)) / 100})
    cohort = rel['cohort']
    t.put(P + ('design', 'dataset'), {'people': A['person_count'], 'targets': cohort['targets'],
                                      'windows': cohort['windows'], 'person_folds': cohort['person_folds'],
                                      'frequency_rotations': A['rotations']})
    ends = {e['id']: e for e in rel['endpoints']}
    for e in ('u8', 'seen_ba'):
        t.put(P + ('design', 'endpoints', e), {'candidate_count': ends[e]['candidates'], 'chance': ends[e]['chance']})
    m = re.search(r'(\d+)trainrows(\d+)people(\d+)freq', pa['split'])
    t.put(P + ('design', 'source_per_fit'), {'windows': int(m.group(1)), 'people': int(m.group(2)),
                                             'frequencies': int(m.group(3))}, 'derived')
    c = sm['A_counts']
    t.put(P + ('design', 'fit_operations'), {'main': c['main'], 'independent_refits': c['independent_refits'],
                                             'bridges': c['bridges'], 'label_permutation_check': c['canaries'],
                                             'total': c['total_fits']})
    from_card9 = [k for k in A['arms'] if k in coh['arms'] and k != 'CCA-RAW' and A['arms'][k] == coh['arms'][k]]
    for i, code in enumerate(A['arms']):
        t.put(P + ('design', 'arms', i, 'code'), code)
        if code == pa['fitted_arm']:
            t.put(P + ('design', 'arms', i), {'fits': pa['main_fits'], 'independent_refits': pa['independent_refits']})
        if code in from_card9 or code == 'CCA-RAW':
            t.put(P + ('design', 'arms', i, 'reused_from_card'), 9 if code in from_card9 else 5, 'derived')
    t.put(P + ('design', 'contrast_family'), {'primary': len(pa['primary_contrasts']),
                                              'secondary': len(pa['secondary_contrasts']),
                                              'multiplicity_adjusted': not st['multiplicity'].startswith('none'),
                                              'equivalence_margin': None}, 'derived')
    people = A['person_count']
    est = {}
    card5 = rel['studies']['cca_diagnostics']['levels']
    for code, arm in A['arms'].items():
        for e, src in EXPORT_NAME.items():
            mt, lid = arm[src], f'{code}/{e}'
            if code == 'CCA-RAW':
                check(mt['mean'] == card5[lid]['estimate'] and mt['ci95'] == card5[lid]['interval'],
                      f'A {lid}: not card 5’s level')
            origin = ('reused_coherence_eigen' if code in from_card9 else
                      'reused_cca_diagnostics' if code == 'CCA-RAW' else 'new')
            level(t, P + ('levels', lid), mt['mean'], mt['ci95'], people,
                  DETERMINISTIC if code in ('RAW-LEAD3-RIDGE', 'EIG-RAW', 'EIG-JOINT') else NO_TRAINING, origin)
            est[lid] = mt['mean']
    card9 = {'card': 9, 'study': 'coherence_eigen', 'anchor': 'eigenvalue-pooling'}
    c5 = card_of(rel, 'cca_diagnostics')
    for code in from_card9:
        t.put(P + ('reused', code), card9 | {'code': code}, 'editorial')
    t.put(P + ('reused', 'CCA-RAW'), {'card': c5['card'], 'study': 'cca_diagnostics', 'anchor': c5['anchor'],
                                      'code': 'CCA-RAW'})
    planned = ([(a, b, 'primary') for a, b in pa['primary_contrasts']]
               + [(a, b, 'secondary') for a, b in pa['secondary_contrasts']])
    learned = {'RAW-LEAD3-RIDGE', 'EIG-RAW', 'EIG-JOINT'}
    for (a, b, role), cc in zip(planned, A['contrasts']):
        check((cc['a'], cc['b'], cc['metric']) == (a, b, 'held8'), 'A: the contrasts differ from the protocol')
        ci = cc['ci95']
        flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'direction': direction(ci)}
        if est[f'{a}/u8'] == est[f'{b}/u8']:
            flags['levels_equal'] = True
        contrast(t, P + ('contrasts', f'{a} minus {b}/u8'), est, role, f'{a}/u8', f'{b}/u8', cc['mean'], ci, people,
                 DETERMINISTIC if {a, b} & learned else NO_TRAINING, flags)
    err = sm['A_score_max_errors']
    t.put(P + ('checks',), {
        'release_review': {'passed': 'Technical PASS for the completed A/C chain' in s['pooling:ac_release_review'],
                           'technical_holds': len(sm['technical_holds'])},
        'interpretation_review': {'passed': 'PASS for the bounded aggregate interpretation'
                                  in s['pooling:ac_interpretation_review']},
        'release_approval': {'approved': ap['status'] == 'APPROVED_AGGREGATE_A_C_HANDOFF'},
        'source_admission_sets': c['source_admission_sets'],
        'score_max_errors': {k: err[k] for k in ('forward_from_saved_cache', 'independent_refit', 'bridge')},
        'metric_and_contrast_max_error': sm['A_metric_and_6_contrast_max_error'],
        'metric_values_rebuilt': sm['A_person_rotation_metric_entries'],
        'reused_levels_bit_identical': {'card 9': from_card9, 'card 5': ['CCA-RAW']},
    })
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'ac_summary', 'review_sha256': 'ac_release_review',
                            'interpretation_review_sha256': 'ac_interpretation_review',
                            'release_approval_sha256': 'ac_approval', 'protocol_sha256': 'ac_protocol',
                            'freeze_sha256': 'ac_freeze'})
    t.put(P + ('embedded_aggregate_sha256',), sm['aggregate_sha256']['A'])
    t.put(P + ('reused_source_sha256',), {'coherence_aggregate': pins['coherence_aggregate']['sha256'],
                                          'released': pins['released']['sha256']})
    return est, A


def study_wearable(t, s, pins):
    P = ('studies', 'harmonic_pooling_wearable')
    sm = s['pooling:ac_summary']
    C, pc, cnt = sm['verified_C_aggregate'], s['pooling:ac_protocol']['modules']['C'], sm['C_counts']
    rel = s['released']
    rw = rel['studies']['wearable_transfer']
    c7 = card_of(rel, 'wearable_transfer')
    check(f'default_rng({C["bootstrap_seed"]}).integers(0,102,size=({C["bootstrap_draws"]},102))'
          in s['pooling:transfer_runner'] and 'np.percentile(v[draws].mean(axis=1),[2.5,97.5])'
          in s['pooling:transfer_runner'], 'C: the runner draws and percentile rule')
    t.put(P + ('card',), 10, 'editorial')
    t.put(P + ('interval_method',), {'draws': C['bootstrap_draws'], 'seed': C['bootstrap_seed'], 'level': 0.95})
    d = rw['design']['dataset']
    windows = cnt['target_rows']
    t.put(P + ('design', 'dataset'), {'name': 'Wearable-102', 'people': C['people'], 'targets': d['targets'],
                                      'frequency_range_hz': [min(pc['frequencies_hz']), max(pc['frequencies_hz'])],
                                      'windows': windows, 'windows_per_sensor': windows // len(C['conditions']),
                                      'sensors': C['conditions'], 'window_s': d['window_s']})
    check(d['frequency_range_hz'] == [min(pc['frequencies_hz']), max(pc['frequencies_hz'])], 'C: another range')
    for k in C['conditions']:
        t.put(P + ('design', 'endpoints', k), {'candidate_count': len(pc['frequencies_hz']), 'chance': C['chance'],
                                               'windows': windows // len(C['conditions'])})
    t.put(P + ('design', 'source_heads'), {'learned_arms': cnt['learned_arms'],
                                           'heads_per_learned_arm': cnt['heads_per_arm'],
                                           'source_heads': cnt['source_heads'], 'collapsed_to_one_affine_function': True,
                                           'coefficients': {a: {'weights': w, 'bias': 1}
                                                            for a, w in pc['head_widths'].items()},
                                           'target_fits': cnt['target_fits'],
                                           'target_selection': pc['target_selection'],
                                           'retraining': pc['fit_count'] != 0})
    for i, code in enumerate(pc['methods']):
        t.put(P + ('design', 'methods', i, 'code'), code)
        if code == 'CCA-RAW':
            t.put(P + ('design', 'methods', i), {'level_only': True, 'card': c7['card']})
    t.put(P + ('design', 'contrast_family'), {'primary': len(pc['primary_pairs']), 'secondary': len(pc['secondary_pairs']),
                                              'per_sensor': True, 'multiplicity_adjusted': False,
                                              'equivalence_margin': None}, 'derived')
    people = C['people']
    est = {}
    learned = set(pc['head_widths'])
    for code in pc['methods']:
        for k in C['conditions']:
            mt, lid = C['levels'][k][code], f'{code}/{k}'
            if code == 'CCA-RAW':
                check(mt['mean'] == rw['levels'][lid]['estimate'], f'C {lid}: not card 7’s level')
                level(t, P + ('levels', lid), mt['mean'], None, people, NO_TRAINING, 'reused_wearable_transfer')
                t.put(P + ('level_only', lid), f'wearable_transfer {lid}')
            else:
                level(t, P + ('levels', lid), mt['mean'], mt['ci95'], people,
                      DETERMINISTIC if code in learned else NO_TRAINING, 'new')
            est[lid] = mt['mean']
    t.put(P + ('reused', 'CCA-RAW'), {'card': c7['card'], 'study': 'wearable_transfer', 'anchor': c7['anchor'],
                                      'code': 'CCA-RAW'})
    planned = ([(a, b, 'primary') for a, b in pc['primary_pairs']] + [(a, b, 'secondary') for a, b in pc['secondary_pairs']])
    for k in C['conditions']:
        for a, b, role in planned:
            cc = C['contrasts'][k][f'{a} minus {b}']
            check(cc['primary'] is (role == 'primary'), f'C {a} minus {b}: role')
            ci = cc['ci95']
            flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'direction': direction(ci)}
            if est[f'{a}/{k}'] == est[f'{b}/{k}']:
                check(abs(cc['mean']) <= 1e-15, f'C {a} minus {b}/{k}: equal levels, a nonzero contrast')
                flags['levels_equal'] = True
            contrast(t, P + ('contrasts', f'{a} minus {b}/{k}'), est, role, f'{a}/{k}', f'{b}/{k}', cc['mean'], ci,
                     people, DETERMINISTIC if {a, b} & learned else NO_TRAINING, flags)
    t.put(P + ('checks',), {
        'release_review': {'passed': 'Technical PASS for the completed A/C chain' in s['pooling:ac_release_review'],
                           'technical_holds': len(sm['technical_holds'])},
        'interpretation_review': {'passed': 'PASS for the bounded aggregate interpretation'
                                  in s['pooling:ac_interpretation_review']},
        'release_approval': {'approved': s['pooling:ac_approval']['status'] == 'APPROVED_AGGREGATE_A_C_HANDOFF'},
        'explicit_35_head_average_max_errors': sm['C_explicit_35head_score_max_errors'],
        'collapsed_function_max_errors': sm['C_collapsed_affine_max_errors'],
        'metric_and_contrast_max_error': sm['C_metric_and_10_contrast_max_error'],
        'metric_values_rebuilt': sm['C_person_condition_metric_entries'],
        'source_head_bindings': sm['source_head_binding_entries'],
        'matched_cca_equals_card7': {k: C['levels'][k]['CCA-RAW']['mean'] == rw['levels'][f'CCA-RAW/{k}']['estimate']
                                     for k in C['conditions']},
    })
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'ac_summary', 'review_sha256': 'ac_release_review',
                            'interpretation_review_sha256': 'ac_interpretation_review',
                            'release_approval_sha256': 'ac_approval', 'protocol_sha256': 'ac_protocol',
                            'freeze_sha256': 'ac_freeze'})
    t.put(P + ('embedded_aggregate_sha256',), sm['aggregate_sha256']['C'])
    t.put(P + ('reused_source_sha256',), {'released': pins['released']['sha256'],
                                          'wear_protocol': pins['wear_protocol']['sha256'],
                                          'wear_freeze': pins['wear_freeze']['sha256']})
    return est


# ---------------------------------------------------------------------------- card 11, practical settings
def study_practical(t, s, pins, A):
    P = ('studies', 'practical_settings')
    agg, pr, ap = s['practical:bd_aggregate'], s['practical:bd_protocol'], s['practical:bd_approval']
    d, st = pr['design'], pr['design']['statistics']
    rel = s['released']
    check(ap['aggregate_sha256'] == pins['bd_aggregate']['sha256'] and ap['status'] == 'PASS'
          and ap['scientific_result_release_approved'] is True, 'B/D: the approval does not bind the aggregate')
    check(agg['bootstrap_draws'] == st['bootstrap_draws'] and agg['bootstrap_seed'] == st['bootstrap_seed']
          and st['interval'] == 'Nominal paired95percentile', 'B/D: draws or interval')
    t.put(P + ('card',), 11, 'editorial')
    t.put(P + ('interval_method',), {'draws': agg['bootstrap_draws'], 'seed': agg['bootstrap_seed'],
                                     'level': int(re.search(r'paired(\d+)percentile', st['interval']).group(1)) / 100})
    inp, sf, ch, pre = d['input'], d['source_fitting'], d['channels'], d['preprocessing']
    cohort = rel['cohort']
    t.put(P + ('design', 'dataset'), {'people': agg['participant_count'], 'targets': len(inp['frequencies_hz']),
                                      'windows': cohort['windows'], 'recording_blocks': inp['blocks_per_person'],
                                      'person_folds': sf['participant_folds'],
                                      'frequency_rotations': agg['rotations'], 'rate_hz': inp['source_rate_hz']})
    band = re.search(r'Author(\d+)-(\d+)Hz', inp['source_preprocessing'])
    t.put(P + ('design', 'preprocessing'), {'author_band_hz': [int(band.group(1)), int(band.group(2))],
                                            'author_zero_phase': 'zero-phase' in inp['source_preprocessing'],
                                            'crop_before_new_filtering': 'crop before every new noncausal operation'
                                            in pre['common_support'],
                                            'new_filtering_borrows_later_samples': False}, 'derived')
    for i, c in enumerate(d['cells']):
        t.put(P + ('design', 'cells', i), {'id': c['id'], 'window_s': c['seconds'], 'samples': c['samples'],
                                           'electrodes': c['channels']})
    t.put(P + ('design', 'electrodes'), {'eight': ch['eight'], 'four': ch['four'],
                                         'four_are_recorded_subset_of_eight':
                                             [ch['eight'][i] for i in ch['four_indices_in_eight']] == ch['four']})
    ends = {e['id']: e for e in rel['endpoints']}
    for e in ('u8', 'seen_ba'):
        t.put(P + ('design', 'endpoints', e), {'candidate_count': ends[e]['candidates'], 'chance': ends[e]['chance']})
    t.put(P + ('design', 'source_per_fit'), {'people': sf['source_people'], 'frequencies': sf['source_candidates'],
                                             'windows': sf['source_trials_per_fit']})
    t.put(P + ('design', 'fits'), {'main': sf['main_fits'], 'independent_refits': sf['independent_refits'],
                                   'hyperparameter_tuning': sf['hyperparameter_tuning'],
                                   'reused_heads': sf['historical_head_reuse']})
    rb = re.search(r'butter\((\d+),\[(\d+),(\d+)\]', pre['raw_family']['filter'])
    t.put(P + ('design', 'raw_family'), {'codes': pre['raw_family']['methods'],
                                         'band_hz': [int(rb.group(2)), int(rb.group(3))],
                                         'harmonics': d['geometry']['H3']}, 'derived')
    fb = pre['fbcca']
    s11 = s['practical:route3_protocol']['secondary_contrasts']['S11']
    check('5 sub-bands' in s11 and 'Butterworth' in s11 and 'Nh=5' in s11, 'route 3 S11: another recipe')
    t.put(P + ('design', 'fbcca'), {'code': d['methods'][-1], 'sub_bands': fb['subbands'],
                                    'pass_band_low_edges_hz': fb['pass_lows_hz'],
                                    'pass_band_high_edge_hz': fb['pass_high_hz'],
                                    'harmonics': fb['harmonics'], 'trained_head': False,
                                    'bitwise_replication_of_the_matlab_code':
                                        'not bitwise MATLAB replication' not in fb['scope']})
    r3 = s['practical:route3']
    t.put(P + ('design', 'fbcca', 'other_recipe_on_site'),
          {'release_id': r3['release_id'], 'code': 'S11', 'sub_bands': int(re.search(r'(\d+) sub-bands', s11).group(1)),
           'harmonics': int(re.search(r'Nh=(\d+)', s11).group(1)),
           'export_codes': ['questions-in-language-update.json#' + ptr(
               'results', 'questions-in-language', 'secondary', 'parts', 'SSVEP-L0-secondary', 'levels',
               'S11 FBCCA levels', 'u8'), 'route3_protocol#' + ptr('secondary_contrasts', 'S11')]}, 'derived')
    learned = ('RAW-LEAD3-RIDGE', 'EIG-RAW6-RIDGE')
    for i, mth in enumerate(d['methods']):
        t.put(P + ('design', 'methods', i, 'code'), mth)
    primary = {'B': [], 'D': []}
    for c in st['primary_contrasts']:
        primary[c['module']].append(f'{c["cell"]}/{c["left"]} minus {c["cell"]}/{c["right"]}/u8')
    t.put(P + ('design', 'primary'), primary)
    people = agg['participant_count']
    cells = [c['id'] for c in d['cells']]
    keys = [f'{c}/{mth}' for c in cells for mth in d['methods']]
    check(list(agg['arms']) == keys, 'B/D: not the prospective grid order')
    t.put(P + ('grid',), {'cells': cells, 'methods': d['methods'],
                          'table': {e: [[f'{c}/{mth}/{e}' for mth in d['methods']] for c in cells] for e in EXPORT_NAME}})
    t.put(P + ('grid', 'order'), 'prospective', 'editorial')
    est = {}
    for key in keys:
        for e, src in EXPORT_NAME.items():
            mt = agg['arms'][key][src]
            level(t, P + ('levels', f'{key}/{e}'), mt['mean'], mt['ci95'], people,
                  DETERMINISTIC if key.split('/')[1] in learned else NO_TRAINING, 'new')
            est[f'{key}/{e}'] = mt['mean']
    groups = {'method': [], 'window': [], 'electrodes': []}
    roles = {}
    for cc in agg['contrasts']:
        a, b = cc['a'], cc['b']
        cid = f'{a} minus {b}/u8'
        ci = cc['ci95']
        kind = 'method' if a.split('/')[0] == b.split('/')[0] else ('window' if a[:4] != b[:4] else 'electrodes')
        groups[kind].append(cid)
        roles[cid] = cc['role']
        check(cc['metric'] == 'held8' and cc['above_zero'] is (ci[0] > 0) and cc['below_zero'] is (ci[1] < 0),
              f'B/D {cid}: flags')
        seeds = DETERMINISTIC if a.split('/')[1] in learned or b.split('/')[1] in learned else NO_TRAINING
        contrast(t, P + ('contrasts', cid), est, cc['role'], f'{a}/u8', f'{b}/u8', cc['mean'], ci, people, seeds,
                 {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'direction': direction(ci)})
    t.put(P + ('contrast_groups',), groups, 'derived')
    short = [c['id'] for c in d['cells'] if c['seconds'] == 0.5]
    four, eight = sorted(short, key=lambda c: c.endswith('c8'))
    above = [mth for mth in d['methods'] if est[f'{four}/{mth}/u8'] > est[f'{eight}/{mth}/u8']]
    t.put(P + ('qualifiers', 'eight_electrodes_not_always_better'),
          {'cells': [four, eight], 'methods_four_above_eight': above, 'paired_interval': None})
    fb_code = d['methods'][-1]
    undefined = f'{ANCHOR_CELL}/{fb_code} minus {ANCHOR_CELL}/RAW-LEAD3-RIDGE/u8'
    check(undefined not in roles, 'B/D: the filter-bank CCA against the top-three ridge has a contrast')
    t.unordered(P + ('undefined',), [{'contrast': undefined, 'reason': 'no paired interval was registered'}])
    # The 2 s / 8-electrode cell reproduces card 10 (module A) and card 5, bit for bit.
    rows = []
    card5 = rel['studies']['cca_diagnostics']['levels']
    for code, twin in B_TO_A.items():
        for e, src in EXPORT_NAME.items():
            lid = f'{ANCHOR_CELL}/{code}/{e}'
            check(est[lid] == A['arms'][twin][src]['mean'], f'{lid}: not card 10’s')
            rows.append({'here': lid, 'card': 10, 'study': 'harmonic_pooling', 'there': f'{twin}/{e}'})
            if twin == 'CCA-RAW':
                check(est[lid] == card5[f'CCA-RAW/{e}']['estimate'], f'{lid}: not card 5’s')
                rows.append({'here': lid, 'card': 5, 'study': 'cca_diagnostics', 'there': f'CCA-RAW/{e}'})
    pa = s['pooling:ac_protocol']['modules']['A']
    a_roles = {tuple(x): 'primary' for x in pa['primary_contrasts']} | {tuple(x): 'secondary'
                                                                        for x in pa['secondary_contrasts']}
    for cc in A['contrasts']:
        here = [k for k, v in B_TO_A.items() if v == cc['a']], [k for k, v in B_TO_A.items() if v == cc['b']]
        if here[0] and here[1]:
            cid = f'{ANCHOR_CELL}/{here[0][0]} minus {ANCHOR_CELL}/{here[1][0]}/u8'
            if cid in roles:
                rows.append({'here': cid, 'card': 10, 'study': 'harmonic_pooling', 'there': f'{cc["a"]} minus {cc["b"]}/u8',
                             'role_here': roles[cid], 'role_there': a_roles[(cc['a'], cc['b'])]})
    coh = s['practical:coherence_aggregate']
    k = next(i for i, c in enumerate(coh['contrasts'])
             if (c['a'], c['b'], c['metric']) == ('EIG-RAW', 'RAW-HARM-SUM', 'held8'))
    cid = f'{ANCHOR_CELL}/EIG-RAW6-RIDGE minus {ANCHOR_CELL}/RAW-HARM-SUM-H3/u8'
    bd_c = next(c for c in agg['contrasts'] if f'{c["a"]} minus {c["b"]}/u8' == cid)
    check(bd_c['mean'] == coh['contrasts'][k]['mean'] and bd_c['ci95'] == coh['contrasts'][k]['ci95'],
          f'{cid}: not card 9’s')
    rows.append({'here': cid, 'card': 9, 'study': 'coherence_eigen', 'there': 'EIG-RAW minus RAW-HARM-SUM/u8',
                 'role_here': roles[cid], 'export_code': 'coherence_aggregate#' + ptr('contrasts', k)})
    t.unordered(P + ('reproduces',), rows)
    nra, rc = ap['numeric_release_audit'], s['practical:bd_audit_receipt']
    t.put(P + ('checks',), {
        'release_approval': {'approved': ap['status'] == 'PASS' and ap['scientific_result_release_approved'] is True},
        'numerical_review': {'passed': 'PASS for independent numerical and provenance release review'
                             in s['practical:bd_numerical_review'],
                             'sealed_payloads_rehashed': rc['payloads_verified_in_completed_check'],
                             'admissions': nra['counts']['admissions'], 'refit_decisions': nra['counts']['refit_decisions'],
                             'score_max_error': nra['max_errors']['score_error'],
                             'metric_max_error': nra['max_errors']['metric_error']},
        'interpretation_review': {'passed': 'Decision: interpretation PASS' in s['practical:bd_interpretation_review'],
                                  'roster_agreement': 'exact ordered agreement of all 41 aggregate contrasts with the '
                                                      'frozen roster' in s['practical:bd_interpretation_review']},
        'text_review': {'passed': s['practical:bd_text_review']['decision'].startswith('PASS')},
        'grid_order_is_prospective': list(agg['arms']) == keys,
    }, 'derived')
    t.put(P + ('answers_not_run', 0, 'card'), 6, 'editorial')
    put_hashes(t, P, pins, {'source_sha256': 'bd_aggregate', 'review_sha256': 'bd_numerical_review',
                            'interpretation_review_sha256': 'bd_interpretation_review',
                            'release_approval_sha256': 'bd_approval', 'protocol_sha256': 'bd_protocol',
                            'freeze_sha256': 'bd_freeze'})
    t.put(P + ('cross_check_sha256',), {k: pins[k]['sha256'] for k in (
        'ac_summary', 'coherence_aggregate', 'released', 'route3', 'route3_protocol')})
    cpu_components(t, s, pins, P + ('cpu_components',), cells)
    return est


def cpu_components(t, s, pins, P, cells):
    """D25: warm single-thread wall-clock medians [min, max] of the measured calls, wall time only, no host label."""
    tg, tp, ta = s['practical:timing_aggregate'], s['practical:timing_protocol'], s['practical:timing_approval']
    check(ta['status'] == 'PASS' and ta['method_whole_pipeline_latencies_measured'] == 0, 'timing: the approval')
    site = {'native_crop_validation_copy': 'crop', 'raw_window_filter_float32': 'raw_filter',
            'raw_geometry_shared_superset': 'raw_geometry', 'fbcca_filter_geometry_score': 'fbcca',
            'cached_features_fixed_f0_r0_ridge_lead3': 'top3_readout',
            'cached_features_fixed_f0_r0_ridge_eig6': 'eigenvalue_readout'}
    order = []
    for r in tg['component_summaries']:
        check(r['measured_calls'] == tp['repetitions'] and r['warmup_calls'] == tp['warmups'], 'timing: calls')
        gid = f'{r["cell"]}/{r["batch"]}/{site[r["component"]]}'
        order.append(gid)
        for k in ('median', 'min', 'max'):
            check(abs(r['wall_ms_per_trial'][k] - r['wall_ms_per_call'][k] / r['batch']) <= 1e-9,
                  f'timing {gid}: not the batch cost per trial')
        t.put(P + ('groups', gid), {'cell': r['cell'], 'batch': r['batch'], 'component': site[r['component']],
                                    'wall_ms_per_call': {k: r['wall_ms_per_call'][k] for k in ('median', 'min', 'max')},
                                    'wall_ms_amortised': {k: r['wall_ms_per_trial'][k] for k in ('median', 'min', 'max')}})
        t.put(P + ('export_codes', gid), [f'timing_aggregate#component_summaries[cell={r["cell"]}][batch={r["batch"]}]'
                                          f'[component={site[r["component"]]}]'])
    check([g.split('/')[0] for g in order[::12]] == cells, 'timing: not the B/D cells in their order')
    t.put(P + ('order',), order)
    t.put(P + ('components',), [{'code': c} for c in dict.fromkeys(site[r['component']] for r in tg['component_summaries'])])
    t.put(P + ('anchor_cell',), ANCHOR_CELL)
    t.put(P + ('measurement',), {'measured_calls': tp['repetitions'], 'warmup_calls_excluded': tp['warmups'],
                                 'threads': tp['threads'], 'gpu': False, 'candidates': len(tp['candidates_hz']),
                                 'batch_sizes': tp['batch_sizes'], 'summed': False})
    t.put(P + ('checks',), {'release_approval': {'approved': ta['status'] == 'PASS'},
                            'review': {'passed': 'PASS for aggregate component timing release'
                                       in s['practical:timing_review']},
                            'groups': len(order), 'calls_measured': len(order) * tp['repetitions'],
                            'whole_method_measurements': ta['method_whole_pipeline_latencies_measured']}, 'derived')
    put_hashes(t, P, pins, {'source_sha256': 'timing_aggregate', 'review_sha256': 'timing_review',
                            'receipt_sha256': 'timing_receipt', 'release_approval_sha256': 'timing_approval',
                            'protocol_sha256': 'timing_protocol'})


# ---------------------------------------------------------------------------- cards 12 to 14, the weighting studies
GAP_COHORTS = {'u8': 'BETA-held8', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'}
GAP_ARMS = {'J': 'accuracy_J', 'B': 'accuracy_shared', 'S': 'accuracy_free', 'JplusG': 'accuracy_JplusG'}
GAP_FAMILY = {'B minus J': 'accuracy_S_shared_minus_S_joint', 'S minus B': 'accuracy_S_free_minus_S_shared'}
GAP_SECONDARY = {'S minus J': 'increment_J_to_free', 'JplusG minus J': 'increment_J_to_JplusG',
                 'S minus JplusG': 'increment_JplusG_to_free'}
GAP_STATS = {'G true': 'mean_true_G', 'G mean distractor': 'mean_distractor_G', 'R true': 'mean_true_R',
             'R mean distractor': 'mean_distractor_R', 'R true minus mean distractor': 'R_true_minus_mean_distractor'}
CANDIDATES = {'u8': 8, 'seen_ba': 32, 'dry': 12, 'wet': 12}
TASK_LABEL = {'u8': 'BETA held-out 8-way', 'seen_ba': 'BETA seen 32-way', 'dry': 'Wearable-102 dry 12-way',
              'wet': 'Wearable-102 wet 12-way'}


def weights_interval(t, P, seeds, draws):
    t.put(P + ('interval_method',), {'draws': draws, 'seeds': {'BETA': seeds['BETA'], 'Wearable-102': seeds['Wearable']},
                                     'level': 0.95})


def study_gap(t, s, pins):
    P = ('studies', 'harmonic_gap')
    ex, qc, pr, nr, ir, tr, ap = (s[f'weights:{k}'] for k in (
        'gap_export', 'gap_reference_qc', 'gap_protocol', 'gap_numerical_review', 'gap_interpretation_receipt',
        'gap_text_receipt', 'gap_release_approval'))
    check(ap['status'] == 'PASS' and ap['artifact_sha256']['results/Harmonic Gap Aggregate Results.json']
          == pins['gap_export']['sha256'], 'harmonic gap: the approval')
    st = pr['statistics']
    t.put(P + ('card',), 12, 'editorial')
    weights_interval(t, P, {'BETA': st['bootstrap_seed_beta'], 'Wearable': st['bootstrap_seed_wearable']},
                     st['bootstrap_draws'])
    q = st['primary_interval_quantiles']
    family = q[1] - q[0]
    check(abs(family - (1 - 0.05 / st['family_size'])) <= TOL and 'Bonferroni' in st['primary_rule'], 'gap: the family')
    t.put(P + ('interval_method', 'family'), {'comparisons': st['family_size'], 'level': family})
    beta, wear = pr['datasets']['BETA'], pr['datasets']['Wearable']
    co = {e: ex['cohorts'][c] for e, c in GAP_COHORTS.items()}
    ref = pr['reference']
    t.put(P + ('design', 'datasets', 'BETA'), {'people': beta['people'], 'targets': beta['classes'],
                                               'windows': co['u8']['trials'],
                                               'frequency_rotations': len(beta['candidate_sets']), 'endpoints': ['u8']})
    t.put(P + ('design', 'datasets', 'Wearable-102'), {'people': wear['people'], 'targets': wear['classes'],
                                                       'windows_per_sensor': co['dry']['trials'],
                                                       'sensors': [wear['conditions'][k]
                                                                   for k in sorted(wear['conditions'])],
                                                       'endpoints': ['dry', 'wet']})
    for e in GAP_COHORTS:
        check(co[e]['candidates'] == CANDIDATES[e], f'gap {e}: candidates')
        t.put(P + ('design', 'endpoints', e), {'dataset': 'BETA' if e == 'u8' else 'Wearable-102',
                                               'candidate_count': co[e]['candidates'], 'chance': 1 / co[e]['candidates'],
                                               'decisions': co[e]['trials'], 'label': TASK_LABEL[e],
                                               'distractors': co[e]['candidates'] - 1})
    t.put(P + ('design',), {'window_length_s': ref['n_samples'] // ref['sample_rate_hz'], 'channels': beta['shape'][1],
                            'harmonics': ref['harmonics'], 'training_fits': pr['training_fits']}, 'derived')
    for i, code in enumerate(GAP_ARMS):
        t.put(P + ('design', 'scores', i, 'code'), code)
    est, family_members, resolved = {}, [], []
    gap_lowers = []
    for e, c in GAP_COHORTS.items():
        m, n = co[e]['metrics'], co[e]['participants']
        for code, key in GAP_ARMS.items():
            lid = f'{code}/{e}'
            level(t, P + ('levels', lid), m[key]['estimate'], m[key]['ci95'], n, NO_TRAINING, 'new',
                  {'interval_level': 0.95})
            est[lid] = m[key]['estimate']
        g = m['G_true_minus_mean_distractor']
        gid = f'G true minus mean distractor/{e}'
        ci = g['ci_family99_444']
        gap_lowers.append(ci[0])
        t.put(P + ('gap', gid), {'role': 'primary', 'estimate': g['estimate'], 'interval': ci, 'interval_level': family,
                                 'unit': SCORE_DIFFERENCE, 'people': n,
                                 'flags': {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'family_member': True}})
        family_members.append(gid)
        if not ci[0] <= 0 <= ci[1]:
            resolved.append(gid)
        for cid, key in GAP_FAMILY.items():
            x = m[key]
            a, b = cid.split(' minus ')
            ci = x['ci_family99_444']
            contrast(t, P + ('contrasts', f'{cid}/{e}'), est, 'primary', f'{a}/{e}', f'{b}/{e}', x['estimate'], ci, n,
                     NO_TRAINING, {'interval_includes_zero': ci[0] <= 0 <= ci[1], 'family_member': True},
                     extra={'interval_level': family})
            family_members.append(f'{cid}/{e}')
            if not ci[0] <= 0 <= ci[1]:
                resolved.append(f'{cid}/{e}')
        for cid, key in GAP_SECONDARY.items():
            x = m[key]
            a, b = cid.split(' minus ')
            ci = x['ci95']
            contrast(t, P + ('contrasts', f'{cid}/{e}'), est, 'secondary', f'{a}/{e}', f'{b}/{e}', x['estimate'], ci, n,
                     NO_TRAINING, {'interval_includes_zero': ci[0] <= 0 <= ci[1]}, extra={'interval_level': 0.95})
        for sid, key in GAP_STATS.items():
            x = m[key]
            ci = x['ci95']
            t.put(P + ('gap', f'{sid}/{e}'), {'role': 'secondary', 'estimate': x['estimate'], 'interval': ci,
                                              'interval_level': 0.95,
                                              'unit': SCORE_DIFFERENCE if 'minus' in sid else SCORE, 'people': n,
                                              'flags': {'interval_includes_zero': ci[0] <= 0 <= ci[1]}})
        w = m['G_true_vs_distractor_pairwise_probability_including_half_exact_ties']
        t.put(P + ('win_fractions', e), {'estimate': w['estimate'], 'interval': w['ci95'], 'interval_level': 0.95,
                                         'unit': WIN, 'accuracy': False, 'distractors': co[e]['candidates'] - 1,
                                         'people': n, 'export_codes': ['#' + ptr('cohorts', c, 'metrics',
                                                                                 'G_true_vs_distractor_pairwise_'
                                                                                 'probability_including_half_exact_ties')]})
        for part, key in (('G', 'symmetric_path_G'), ('R', 'symmetric_path_R')):
            x = m[key]
            t.put(P + ('allocation', e, part), {'estimate': x['estimate'], 'interval': x['ci95'], 'interval_level': 0.95,
                                                'export_codes': ['#' + ptr('cohorts', c, 'metrics', key)]})
        check(abs(m['symmetric_path_G']['estimate'] + m['symmetric_path_R']['estimate']
                  - m['increment_J_to_free']['estimate']) <= TOL, f'gap {e}: the allocation does not add up')
    t.put(P + ('allocation', 'unit'), DIFFERENCE)
    t.put(P + ('family',), {'comparisons': st['family_size'], 'interval_level': family, 'members': family_members,
                            'all_gap_intervals_above_zero': all(v > 0 for v in gap_lowers), 'resolved': resolved},
          'derived')
    # Decision changes on BETA held-out as shares of all its decisions: count / decisions, one division each.
    n = co['u8']['trials']
    names = {'J->shared': ('J', 'B'), 'shared->free': ('B', 'S'), 'J->free': ('J', 'S'), 'J->JplusG': ('J', 'JplusG'),
             'JplusG->free': ('JplusG', 'S')}
    shares = (('wrong_to_right', 'rescue'), ('right_to_wrong', 'harm'), ('unchanged_right', 'stable_correct'),
              ('wrong_both', 'stable_wrong'), ('changed', 'prediction_change'))
    t.put(P + ('transitions',), {'decisions': n, 'unit': 'share of all decisions on the task',
                                 'export_codes': ['#' + ptr('cohorts', GAP_COHORTS['u8'], 'edges')]})
    t.put(P + ('transitions', 'endpoint'), 'u8')
    for key, (frm, to) in names.items():
        edge = ex['cohorts'][GAP_COHORTS['u8']]['edges'][key]
        check(edge['trials'] == n, f'gap edge {key}: decisions')
        sh = {k: edge[src] / n for k, src in shares}
        check(abs(sh['wrong_to_right'] - sh['right_to_wrong'] - (est[f'{to}/u8'] - est[f'{frm}/u8'])) <= TOL,
              f'gap edge {key}: the net change is not the level difference')
        t.put(P + ('transitions', 'edges', f'{frm} to {to}'), {'from': frm, 'to': to, **sh,
                                                               'net_equals': f'{to} minus {frm}/u8'}, 'derived')
    # The label-free reference check, counts only.
    src = qc['sources']
    t.put(P + ('reference_check', 'threshold'), src['BETA']['threshold'])
    t.put(P + ('reference_check',), {'label_free': qc['new_EEG_or_label_computation'] is False,
                                     'outcome_subgroups': False,
                                     'export_codes': ['gap_reference_qc#' + ptr('sources', k, f)
                                                      for k in ('BETA', 'Wearable')
                                                      for f in ('candidate_count', 'near_orthogonal_count',
                                                                'nonorthogonal_count')]})
    for name, k in (('BETA', 'BETA'), ('Wearable-102', 'Wearable')):
        t.put(P + ('reference_check', name), {'candidates': src[k]['candidate_count'],
                                              'at_or_below_threshold': src[k]['near_orthogonal_count'],
                                              'above_threshold': src[k]['nonorthogonal_count'],
                                              'reference_full_rank': src[k]['reference_full_rank']})
    check((src['BETA']['candidate_count'], src['BETA']['near_orthogonal_count']) == (40, 8), 'gap: not 8 of 40')
    t.put(P + ('identity',), {'joint_cca_equals_top_eigenvalue_of_sum': False, 'residual_reported_beside_gap': True},
          'editorial')
    t.put(P + ('identity', 'export_codes'), ['gap_protocol#/scores'])
    check('S_shared-S_joint, signed' in pr['scores']['R'] and 'S_free-S_joint=G+R' in pr['scores']['Delta'],
          'gap: the identity')
    au = ex['independent_audit']
    pairs = [(a, b) for c in GAP_COHORTS.values() for _, a, b in paired(nr['primary'][c], ex['cohorts'][c]['metrics'])]
    worst = float(max(abs(a - b) for a, b in pairs))
    t.put(P + ('checks',), {
        'release_approval': {'passed': ap['status'] == 'PASS', 'artifacts_bound': len(ap['artifact_sha256'])},
        'numerical_review': {'passed': nr['status'] == 'PASS', 'failures': len(nr['failures']),
                             'chunks': sum(v['chunks'] for v in nr['source_qc'].values()),
                             'primary_max_error': nr['primary_audit_max_abs_error'],
                             'oracle_rows_per_source': len(nr['numerical_oracle']['BETA']['rows']),
                             'export_equals_review': {'values': len(pairs), 'max_absolute_difference': worst}},
        'interpretation_review': {'passed': ir['decision'] == 'PASS_BOUNDED_INTERPRETATION',
                                  'required_limits': len(ir['required_limits'])},
        'handoff_text_review': {'passed': tr['decision'] == 'PASS_HANDOFF_TEXT',
                                'family_intervals_checked': tr['checks']['primary_family_intervals']},
        'embedded_independent_audit': {e: {'passed': au[c]['passed'], 'max_absolute_error': au[c]['max_absolute_error']}
                                       for e, c in GAP_COHORTS.items()},
    }, 'derived')
    t.put(P + ('checks', 'numerical_review', 'export_equals_review', 'tolerance'), TOL, 'editorial')
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'gap_export', 'review_sha256': 'gap_interpretation_receipt',
                            'approval_sha256': 'gap_release_approval', 'reference_qc_sha256': 'gap_reference_qc',
                            'protocol_sha256': 'gap_protocol', 'freeze_sha256': 'gap_freeze',
                            'numerical_review_sha256': 'gap_numerical_review',
                            'interpretation_review_sha256': 'gap_interpretation_review',
                            'text_review_sha256': 'gap_text_review', 'text_receipt_sha256': 'gap_text_receipt'})
    return est


def paired(a, b, trail=''):
    """(pointer, a, b) for every number of a at the same place in b."""
    if isinstance(a, dict):
        for k, v in a.items():
            yield from paired(v, b[k], f'{trail}/{k}')
    elif isinstance(a, list):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from paired(x, y, f'{trail}/{i}')
    elif is_number(a):
        yield trail, a, b


def study_decay(t, s, pins):
    P = ('studies', 'fixed_decay')
    ex, pr, au, rv, ap = (s[f'weights:{k}'] for k in (
        'decay_export', 'decay_protocol', 'decay_audit_receipt', 'decay_review', 'decay_release_approval'))
    check(ap['aggregate_sha256'] == pins['decay_export']['sha256'] and ap['status'] == 'PASS', 'decay: the approval')
    st, sc, fb = pr['statistics'], pr['scoring'], pr['fbcca']
    t.put(P + ('card',), 13, 'editorial')
    weights_interval(t, P, st['seeds'], st['bootstrap_draws'])
    margin = st['primary_margin_accuracy_fraction']
    t.put(P + ('interval_method', 'equivalence'),
          {'level': int(re.match(r'(\d+)% paired', st['primary_equivalence_rule']).group(1)) / 100, 'margin': margin})
    beta, wear = pr['datasets']['BETA'], pr['datasets']['Wearable']
    t.put(P + ('design', 'datasets'), {'BETA': {'people': beta['people'], 'targets': beta['classes'],
                                                'endpoints': ['u8', 'seen_ba']},
                                       'Wearable-102': {'people': wear['people'], 'targets': wear['classes'],
                                                        'sensors': ['dry', 'wet'], 'endpoints': ['dry', 'wet']}})
    cohorts = {'H3': {'u8': 'BETA-held8', 'seen_ba': 'BETA-seen32', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'},
               'FBCCA': {'u8': 'BETA-FBCCA-held8', 'seen_ba': 'BETA-FBCCA-seen32'}}
    for e, c in cohorts['H3'].items():
        co = ex['cohorts'][c]
        t.put(P + ('design', 'endpoints', e), {'dataset': 'BETA' if e in ('u8', 'seen_ba') else 'Wearable-102',
                                               'candidate_count': CANDIDATES[e], 'chance': 1 / CANDIDATES[e],
                                               'decisions': co['trials'], 'label': TASK_LABEL[e]})
    m = re.search(r'\(h\*\*\(-([\d.]+)\)\+([\d.]+)\)', sc['decay'])
    t.put(P + ('design', 'rule'), {'exponent': float(m.group(1)), 'offset': float(m.group(2))}, 'derived')
    t.put(P + ('design', 'constructions', 'H3'), {'terms': len(sc['harmonic_columns']), 'codes': ['H3-FLAT', 'H3-DECAY'],
                                                  'endpoints': list(cohorts['H3'])})
    t.put(P + ('design', 'constructions', 'FBCCA'), {'terms': fb['bands'], 'harmonics_per_band': fb['harmonics'],
                                                     'codes': ['FBCCA-FLAT', 'FBCCA-DECAY'],
                                                     'endpoints': list(cohorts['FBCCA'])})
    t.put(P + ('design',), {'harmonic_and_sub_band_weights_are_different_operations': True,
                            'each_contrast_changes_weights_within_one_construction': 'only pooling weights change'
                            in fb['method'], 'training_fits': sc['training_fits']}, 'derived')
    est = {}
    for cons, ends in cohorts.items():
        for e, c in ends.items():
            co = ex['cohorts'][c]
            n = co['participants']
            for arm, key in (('FLAT', 'accuracy_flat'), ('DECAY', 'accuracy_decay')):
                lid = f'{cons}-{arm}/{e}'
                level(t, P + ('levels', lid), co[key], None, n, NO_TRAINING, 'new', {'interval_level': None})
                est[lid] = co[key]
            ci = co['ci95_descriptive']
            role = 'primary' if co['role'] == 'primary_equivalence' else 'secondary'
            flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1]}
            if role == 'primary':
                flags['equivalence_met'] = co['equivalent_90ci']
            contrast(t, P + ('contrasts', f'{cons}-DECAY minus {cons}-FLAT/{e}'), est, role, f'{cons}-DECAY/{e}',
                     f'{cons}-FLAT/{e}', co['decay_minus_flat'], ci, n, NO_TRAINING, flags, extra={'interval_level': 0.95})
    p = ex['cohorts']['BETA-held8']
    ci90 = p['ci90']
    met = -margin < ci90[0] and ci90[1] < margin
    check(met is p['equivalent_90ci'] is ap['primary_equivalence_supported'], 'decay: the margin test')
    t.put(P + ('equivalence',), {'contrast': 'H3-DECAY minus H3-FLAT/u8', 'interval': ci90, 'interval_level': 0.9,
                                 'margin': p['margin_accuracy_fraction'], 'met': met,
                                 'interval_beyond_margin': ci90[1] < -margin or ci90[0] > margin,
                                 'export_codes': ['#' + ptr('cohorts', 'BETA-held8', k)
                                                  for k in ('ci90', 'margin_accuracy_fraction', 'equivalent_90ci')]})
    out = json.loads(au['stdout'])
    t.put(P + ('checks',), {
        'release_approval': {'passed': ap['status'] == 'PASS'},
        'interpretation_review': {'passed': rv['status'] == 'PASS', 'blocking_fixes': len(rv['blocking_fixes'])},
        'execution_review': {'passed': s['weights:decay_execution_review']['status'] == 'PASS'},
        'independent_audit': {'passed': au['status'] == 'PASS' and out['status'] == 'PASS', 'cohorts': out['cohorts'],
                              'decisions_replayed_exactly': out['all_predictions_exact'],
                              'bootstrap_endpoints_replayed': out['bootstrap_endpoints_replayed']},
    }, 'derived')
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'decay_export', 'review_sha256': 'decay_review',
                            'approval_sha256': 'decay_release_approval', 'protocol_sha256': 'decay_protocol',
                            'freeze_sha256': 'decay_freeze', 'execution_review_sha256': 'decay_execution_review',
                            'audit_receipt_sha256': 'decay_audit_receipt'})
    return est


def study_rise(t, s, pins):
    P = ('studies', 'rising_weights')
    ex, pr, au, rv, ap = (s[f'weights:{k}'] for k in (
        'rise_export', 'rise_protocol', 'rise_audit_receipt', 'rise_review', 'rise_release_approval'))
    check(ap['aggregate_sha256'] == pins['rise_export']['sha256'] and ap['status'] == 'PASS', 'rise: the approval')
    st, sc, w = pr['statistics'], pr['scoring'], pr['weights']
    t.put(P + ('card',), 14, 'editorial')
    weights_interval(t, P, st['seeds'], st['bootstrap_draws'])
    beta, wear = pr['datasets']['BETA'], pr['datasets']['Wearable']
    t.put(P + ('design', 'datasets'), {'BETA': {'people': beta['people'], 'targets': beta['classes'],
                                                'endpoints': ['u8', 'seen_ba']},
                                       'Wearable-102': {'people': wear['people'], 'targets': wear['classes'],
                                                        'sensors': ['dry', 'wet'], 'endpoints': ['dry', 'wet']}})
    cohorts = {'u8': 'BETA-held8', 'seen_ba': 'BETA-seen32', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'}
    for e, c in cohorts.items():
        t.put(P + ('design', 'endpoints', e), {'dataset': 'BETA' if e in ('u8', 'seen_ba') else 'Wearable-102',
                                               'candidate_count': CANDIDATES[e], 'chance': 1 / CANDIDATES[e],
                                               'decisions': ex['cohorts'][c]['trials'], 'label': TASK_LABEL[e]})
    t.put(P + ('design', 'weights'), {'flat': [1.0] * len(sc['harmonic_columns']), 'literal_rise': w['primary_literal'],
                                      'exact_rise': w['rounding_sensitivity_exact']})
    t.put(P + ('design',), {'same_vector_for_every_candidate': sc['weights_candidate_independent'],
                            'training_fits': sc['new_fits']})
    arms = {'flat': 'flat', 'literal_rise': 'literal_rise', 'exact_rise': 'exact_rise'}
    est = {}
    for e, c in cohorts.items():
        co = ex['cohorts'][c]
        n = co['participants']
        for code, key in arms.items():
            x = co['arm_levels'][key]
            level(t, P + ('levels', f'{code}/{e}'), x['estimate'], x['ci95'], n, NO_TRAINING, 'new',
                  {'interval_level': 0.95})
            est[f'{code}/{e}'] = x['estimate']
        for key, x in co['contrasts'].items():
            a, b = key.split('_minus_')
            ci = x['ci95']
            role = ('primary' if e == 'u8' else 'secondary') if (a, b) == ('literal_rise', 'flat') else 'rounding_check'
            flags = {'interval_includes_zero': ci[0] <= 0 <= ci[1]}
            if role == 'primary':
                flags['criterion_met'] = co['supports_primary_benefit']
            contrast(t, P + ('contrasts', f'{a} minus {b}/{e}'), est, role, f'{a}/{e}', f'{b}/{e}', x['estimate'], ci, n,
                     NO_TRAINING, flags, extra={'interval_level': 0.95})
    p = ex['cohorts']['BETA-held8']['contrasts']['literal_rise_minus_flat']
    check(ex['cohorts']['BETA-held8']['supports_primary_benefit'] is (p['ci95'][0] > 0), 'rise: the criterion')
    t.put(P + ('criterion',), {'contrast': 'literal_rise minus flat/u8', 'met': p['ci95'][0] > 0, 'prespecified': True,
                               'export_codes': ['#' + ptr('cohorts', 'BETA-held8', 'contrasts', 'literal_rise_minus_flat', k)
                                                for k in ('estimate', 'ci95')]}, 'derived')
    pairs = list(paired(au['cohorts'], ex['cohorts']))
    t.put(P + ('checks',), {
        'release_approval': {'passed': ap['status'] == 'PASS'},
        'interpretation_review': {'passed': rv['status'] == 'PASS', 'blockers': len(rv['blockers'])},
        'execution_review': {'passed': s['weights:rise_execution_review']['status'] == 'PASS'},
        'independent_audit': {'passed': au['status'] == 'PASS', 'cohorts': len(au['cohorts']),
                              'export_equals_audit': {'values': len(pairs),
                                                      'max_absolute_difference': float(max(abs(a - b)
                                                                                           for _, a, b in pairs))}},
    }, 'derived')
    t.put(P + ('checks', 'independent_audit', 'export_equals_audit', 'tolerance'), TOL, 'editorial')
    t.unordered(P + ('undefined',), [])
    put_hashes(t, P, pins, {'source_sha256': 'rise_export', 'review_sha256': 'rise_review',
                            'approval_sha256': 'rise_release_approval', 'protocol_sha256': 'rise_protocol',
                            'freeze_sha256': 'rise_freeze', 'execution_review_sha256': 'rise_execution_review',
                            'audit_receipt_sha256': 'rise_audit_receipt'})
    return est


def same_estimates(t, served, s):
    """`same_estimate_as` in the weighting blocks names a released or same-round level holding the same double: each
    name is resolved here and its double compared to the last bit."""
    rel, coh, bd = s['released'], s['pooling:coherence_aggregate'], s['practical:bd_aggregate']
    count = 0
    for study in ('harmonic_gap', 'fixed_decay', 'rising_weights'):
        for lid, lv in served['studies'][study]['levels'].items():
            for name in lv.get('same_estimate_as', []):
                if name.startswith(rel['release_id'] + ' '):
                    _, other, there = name.split(' ')
                    value = rel['studies'][other]['levels'][there]['estimate']
                elif name.startswith('coherence '):
                    _, code, metric = name.split(' ')
                    value = coh['arms'][code][metric]['mean']
                elif name.startswith('practical B/D '):
                    m = re.fullmatch(r'practical B/D (\S+) 2 s 8 electrodes (held8|seen32)', name)
                    value = bd['arms'][f'{ANCHOR_CELL}/{m.group(1)}'][m.group(2)]['mean']
                else:
                    other, there = name.split(' ')
                    value = served['studies'][other]['levels'][there]['estimate']
                check(value == lv['estimate'], f'{study} {lid}: {name} holds another double')
                count += 1
    return count


def expected_interval(t, study, lid):
    """The interval this audit expects for a served level: None, or the pair derived from the level's source."""
    P = ('studies', study, 'levels', lid, 'interval')
    if P in t.figures:
        check(t.figures[P][0] is NULL, f'{show(P)}: not an interval')
        return None
    check(P + (0,) in t.figures and P + (1,) in t.figures, f'{study} {lid}: a shared level the sources do not give')
    return [t.figures[P + (0,)][0], t.figures[P + (1,)][0]]


def shared_rows(t, served, s):
    """Each shared row's aliases, the card whose interval the page prints and whether the cards' intervals differ,
    worked out here: the intervals are the ones this audit derives for each level (and the released file's for a level
    released on 2026-10-20), the home is the first card in card order that gives one, the aliases are the display names
    of the row's levels other than its primary site name."""
    rel = s['released']
    rel_card = {st: c['card'] for c in rel['placement']['cards'] for st in c['studies']}
    card = {st: c for c, _, studies in CARDS for st in studies}
    alias_of = {}
    for i, row in enumerate(served['shared_estimates']):
        stated = []
        if 'released_level' in row:
            r = row['released_level']
            check(r['release_id'] == rel['release_id'], f'shared row {i}: another released file')
            stated.append((rel_card[r['study']], rel['studies'][r['study']]['levels'][r['level']]['interval']))
        for x in row['levels']:
            stated.append((card[x['study']], expected_interval(t, x['study'], x['level'])))
        check([c for c, _ in stated] == sorted(c for c, _ in stated), f'shared row {i}: not in card order')
        given = [(c, iv) for c, iv in stated if iv is not None]
        check(bool(given), f'shared row {i}: no card gives an interval')
        t.put(('shared_estimates', i, 'interval_home'), given[0][0], 'derived')
        t.put(('shared_estimates', i, 'intervals_differ_by_card'), len({json.dumps(iv) for _, iv in given}) > 1,
              'derived')
        names = {served['studies'][x['study']]['display_names'][x['level'].split('/')[-2]] for x in row['levels']}
        check(row['site_name'] in names, f'shared row {i}: the primary site name is no level’s display name')
        aliases = sorted(names - {row['site_name']})
        check(('aliases' in row) == bool(aliases), f'shared row {i}: aliases where none, or none listed')
        if aliases:
            t.put(('shared_estimates', i, 'aliases'), aliases)
        for a in aliases:
            alias_of.setdefault(a, []).append(row['site_name'])
    for j, r in enumerate(served['name_key']):
        check(('alias_of' in r) == (r['site_name'] in alias_of), f'name key {r["site_name"]!r}: alias_of')
        if r['site_name'] in alias_of:
            t.put(('name_key', j, 'alias_of'), list(dict.fromkeys(alias_of[r['site_name']])))
    return len(served['shared_estimates'])


def fresh_build(manifest_bytes):
    """The export program's bytes for this manifest, built in a separate process: this audit imports nothing of the
    export or the block modules, and binds the editorial strings it does not derive to that program by these bytes."""
    code = ('import sys; sys.path.insert(0, sys.argv[1]); import export_ssvep_followups_update as ex; '
            'sys.stdout.buffer.write(ex.serialized_export(sys.stdin.buffer.read()))')
    run = subprocess.run([sys.executable, '-c', code, str(PUBLICATION)], input=manifest_bytes, capture_output=True,
                         cwd=PUBLICATION, timeout=900)
    check(run.returncode == 0, f'the export does not build from this manifest: {run.stderr.decode()[-400:]}')
    return run.stdout


# ---------------------------------------------------------------------------- export codes
def selector(s, code):
    m = re.fullmatch(r'timing_aggregate#component_summaries\[cell=([\w-]+)\]\[batch=(\d+)\]\[component=(\w+)\]', code)
    check(m is not None, f'{code}: not a timing selector')
    return m.groups()


def export_codes(served, s, manifest):
    """Every export code of a level, contrast or gap statistic points into its source at the value the file gives."""
    own = {'xspec': s['xspec:xspec_export'], 'coherence_eigen': s['eigen:eigen_export'],
           'harmonic_pooling': s['pooling:ac_summary'], 'harmonic_pooling_wearable': s['pooling:ac_summary'],
           'practical_settings': s['practical:bd_aggregate'], 'harmonic_gap': s['weights:gap_export'],
           'fixed_decay': s['weights:decay_export'], 'rising_weights': s['weights:rise_export']}
    named = {'cca_diagnostics': s['cca_diagnostics'], 'xspec': s['xspec:xspec_export'],
             'coherence_aggregate': s['pooling:coherence_aggregate'], 'new-ssvep-frequencies-update.json': s['released'],
             'questions-in-language-update.json': s['practical:route3'], 'route3_protocol': s['practical:route3_protocol'],
             'gap_protocol': s['weights:gap_protocol'], 'gap_reference_qc': s['weights:gap_reference_qc']}
    checked = 0
    for study in STUDIES:
        block = served['studies'][study]
        items = {**block['levels'], **block['contrasts'], **block.get('gap', {})}
        check(set(block['export_codes']) == set(items), f'{study}: export codes do not cover the figures')
        for lid, codes in block['export_codes'].items():
            served_item = items[lid]
            for code in codes:
                where, pointer_ = code.split('#', 1)
                target = walk(named[where] if where else own[study], pointer_)
                if isinstance(target, dict):
                    value = next(target[k] for k in ('estimate', 'mean', 'point') if k in target)
                    check(value == served_item['estimate'], f'{study} {lid}: {code} holds another value')
                    ivs = [target[k] for k in ('ci95', 'interval', 'ci_family99_444') if k in target]
                    if served_item.get('interval') is not None and ivs:
                        check(served_item['interval'] in ivs, f'{study} {lid}: {code} holds another interval')
                elif isinstance(target, list):
                    check(target == served_item['interval'], f'{study} {lid}: {code} holds another interval')
                else:
                    check(target == served_item['estimate'], f'{study} {lid}: {code} holds another value')
                checked += 1
        for trail, value in leaves(block):
            if 'export_codes' in trail and trail[0] != 'export_codes' and isinstance(value, str):
                where, _, pointer_ = value.partition('#')
                if where == 'timing_aggregate':
                    cell, batch, comp = selector(s, value)
                    group = block['cpu_components']['groups'][f'{cell}/{batch}/{comp}']
                    check(group['cell'] == cell and group['batch'] == int(batch), f'{value}: another group')
                else:
                    walk(named[where] if where else own[study], pointer_)       # resolves, or raises
                checked += 1
    return checked


# ---------------------------------------------------------------------------- what spans the studies
def spanning(t, served, s, manifest):
    rel = s['released']
    ends = {e['id']: e for e in rel['endpoints']}
    t.put(('endpoints', 0), {'candidates': ends['u8']['candidates'], 'chance': ends['u8']['chance']})
    t.put(('endpoints', 1), {'candidates': ends['seen_ba']['candidates'], 'chance': ends['seen_ba']['chance']})
    t.put(('endpoints', 2), {'candidates': ends['wearable_12']['candidates'], 'chance': ends['wearable_12']['chance']})
    t.put(('endpoints',), [{'cards': [8, 9, 10, 11, 12, 13, 14]}, {'cards': [8, 9, 10, 11, 13, 14]},
                           {'cards': [10, 12, 13, 14]}], 'editorial')
    t.put(('placement',), {'leaderboard': False, 'new_page_count': 0, 'new_dataset_count': 0, 'new_model_count': 0,
                           'reads_with': {'cards': [1, 2, 3, 4, 5, 6, 7]},
                           'cards': [{'card': c} for c, _, _ in CARDS]}, 'editorial')
    for i, (c, anchor, studies) in enumerate(CARDS):
        t.put(('placement', 'cards', i), {'anchor': anchor, 'studies': studies})
    released_cards = {c['card']: c for c in rel['placement']['cards']}
    check(released_cards[8].get('status_only') is True and released_cards[8]['anchor'] == 'cross-spectral',
          'the released card 8 is not the status entry')
    t.put(('placement', 'cards', 0, 'supersedes'), {'release_id': rel['release_id'], 'entry': 'status_only'})
    t.put(('question',), rel['question'])
    # Each card's interval method, as the block states it (derived above, study by study).
    for i, (c, study) in enumerate((c, st) for c, _, studies in CARDS for st in studies):
        t.put(('interval_methods', i, 'card'), c, 'editorial')
        t.put(('interval_methods', i, 'study'), study)
        for path, (want, kind) in list(t.figures.items()):
            if path[:3] == ('studies', study, 'interval_method'):
                t.put(('interval_methods', i) + path[3:], None if want is NULL else want, 'derived')
    gst = s['weights:gap_protocol']['statistics']
    q = gst['primary_interval_quantiles']
    dst = s['weights:decay_protocol']['statistics']
    t.put(('interval_adjustment',), {'adjusted': [{'card': 12, 'comparisons': gst['family_size'], 'level': q[1] - q[0]},
                                                  {'card': 13, 'level': 0.9,
                                                   'margin': dst['primary_margin_accuracy_fraction']}],
                                     'other_intervals_adjusted': False}, 'derived')
    # The engineering disclosures: card, flags and the test count as their records state them.
    handoff = s['eigen:eigen_handoff']
    t.put(('engineering_disclosures',), [
        {'card': 8, 'scientific_protocol_changed': False, 'supervised_accuracy_used': False},
        {'card': 8, 'scientific_protocol_changed': False, 'supervised_accuracy_used': False},
        {'card': 9, 'scientific_protocol_changed': False, 'real_inputs_processed_before': False},
        {'card': 9, 'counted_as_pass': 'it is not counted as a pass' not in handoff,
         'rerun_tests_passed': int(re.search(r'passed all (\d+) tests', handoff).group(1))}], 'derived')
    for i, (m, pin) in enumerate((('xspec', 'xspec_handoff'), ('xspec', 'xspec_handoff'), ('eigen', 'eigen_freeze'),
                                  ('eigen', 'eigen_handoff'))):
        t.put(('engineering_disclosures', i, 'stated_in_sha256'), manifest['blocks'][m]['pins'][pin]['sha256'])
    t.put(('engineering_disclosures',), [{'study': 'xspec'}, {'study': 'xspec'}, {'study': 'coherence_eigen'},
                                         {'study': 'coherence_eigen'}])


def rights_strings(t, s, served):
    rel = s['released']['rights']['datasets']
    for k in ('name', 'license', 'licenseUrl', 'source', 'rights_reviewed', 'rights_record', 'citation',
              'publication_conditions'):
        t.put(('rights', 'datasets', 'beta', k), rel['beta'][k])
    for k in ('name', 'title', 'paper_citation', 'license', 'canonical_version_doi', 'local_representation',
              'dataset_citation', 'readme', 'consent_scope', 'primary_sources'):
        t.put(('rights', 'datasets', 'wearable_102', k), rel['wearable_102'][k])
    t.put(('rights', 'datasets', 'beta', 'cards'), [8, 9, 10, 11, 12, 13, 14], 'editorial')
    t.put(('rights', 'datasets', 'wearable_102', 'cards'), [10, 12, 13, 14], 'editorial')
    fb = s['entityProfiles']['methods']['fbcca']
    check('Chen et al. 2015' in fb['aliases'], 'the FBCCA profile has no short citation')
    t.put(('rights', 'credits', 'fbcca'), {'short': 'Chen et al. 2015', 'reference': fb['reference'],
                                           'reference_url': fb['reference_url']})
    t.put(('rights', 'credits', 'fbcca'), {'cards': [11, 13], 'code_distributed': False}, 'editorial')


# ---------------------------------------------------------------------------- the boundary
def private_names(s):
    text = ''.join(json.dumps(s[k]) for k in ('xspec:xspec_protocol', 'eigen:eigen_protocol', 'pooling:ac_protocol',
                                              'practical:bd_protocol', 'practical:timing_protocol',
                                              'weights:gap_protocol', 'weights:decay_protocol', 'weights:rise_protocol'))
    names = set()
    for root in ('home', 'Volumes', 'mnt', 'Users'):
        for a, b in re.findall(rf'/{root}/([^/\s"]+)/([^/\s"]+)', text):
            names |= {a} | ({b} if re.search(r'[_\d]|^[A-Z]+$', b) else set())
    return {n for n in names if len(n) >= 3}


def withheld(s):
    """Doubles the aggregates hold that this release does not publish, less any double a published field also holds."""
    def floats(v):
        return {x for _, x in leaves(v) if isinstance(x, float)}
    held, shown = set(), set()
    for k, keep in (('xspec:xspec_export', ('arms', 'contrasts')),
                    ('eigen:eigen_export', ('arms', 'contrasts', 'prespecified_eigenvalue_claim'))):
        ex = s[k]
        held |= floats({x: ex[x] for x in ('per_seed_descriptive', 'canary_real_label_accuracy_descriptive_only')
                        if x in ex})
        for key in ('random_pairing', 'evaluation_random_pairing_descriptive'):
            for arm in ex.get(key, {}).values():
                held |= floats(arm.get('permutation_mean', {}))
        shown |= floats({x: ex[x] for x in keep})
    held |= floats(s['weights:decay_export']['retrospective_gap_ratio'])
    family = ('G_true_minus_mean_distractor', *GAP_FAMILY.values())
    for c in GAP_COHORTS.values():
        m = s['weights:gap_export']['cohorts'][c]['metrics']
        held |= floats({k: m[k] for k in ('mean_true_Delta', 'mean_distractor_Delta', 'Delta_true_minus_mean_distractor',
                                          'G_true_minus_fixed_J_distractor', 'R_true_minus_fixed_J_distractor',
                                          'Delta_true_minus_fixed_J_distractor')})
        held |= floats([m[k]['ci95'] for k in family])            # the family members' nominal intervals
        shown |= floats([[m[k]['estimate'], m[k]['ci_family99_444']] for k in family])
        shown |= floats([m[k] for k in (*GAP_ARMS.values(), *GAP_SECONDARY.values(), *GAP_STATS.values(),
                                        'G_true_vs_distractor_pairwise_probability_including_half_exact_ties',
                                        'symmetric_path_G', 'symmetric_path_R')])
    for co in s['weights:decay_export']['cohorts'].values():
        shown |= floats([co.get(k) for k in ('accuracy_flat', 'accuracy_decay', 'decay_minus_flat', 'ci95_descriptive',
                                             'ci90', 'margin_accuracy_fraction')])
    for co in s['weights:rise_export']['cohorts'].values():
        shown |= floats([co['arm_levels'], [[x['estimate'], x['ci95']] for x in co['contrasts'].values()]])
    for src in s['weights:gap_reference_qc']['sources'].values():
        held |= floats({k: v for k, v in src.items() if k != 'threshold'})
    rows = s['practical:timing_aggregate']['component_summaries']
    held |= floats([[r.get('cpu_ms_per_call'), r.get('cpu_ms_per_trial')] for r in rows])
    shown |= floats([[r['wall_ms_per_call'], r['wall_ms_per_trial']] for r in rows])
    return held - shown - {0.0, 1.0, 0.125, 0.03125}


def covered(path, t):
    """A served string with no derived value: an editorial prefix, or an editorial leaf in a derived section."""
    if any(path[:len(p)] == p for p in EDITORIAL) or any(path[:len(p)] == p for p in t.sets):
        return True
    if path[0] in ('not_published', 'release_record'):
        return False
    if path[0] != 'studies' or len(path) < 3:
        return path[0] == 'interval_methods' and isinstance(path[-1], str) and path[-1] in EDITORIAL_LEAVES
    if any(k in EDITORIAL_IN_STUDY for k in path[2:] if isinstance(k, str)):
        return True
    if path[2] == 'export_codes' or 'export_codes' in path:
        return True            # resolved one by one in export_codes()
    names = [k for k in path[3:] if isinstance(k, str)]
    return bool(names) and (names[-1] in EDITORIAL_LEAVES or any(n in EDITORIAL_LEAVES for n in names[-2:-1]))


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served_bytes = [p.read_bytes() for p in SERVED]
    check(served_bytes[0] == served_bytes[1], 'the two served copies differ')
    served = json.loads(served_bytes[0])
    check(served['provenance']['manifest_sha256'] == digest(manifest_bytes), 'the served file names another manifest')
    check(served['release_id'] == manifest['release_id'] and served['generated_at'] == manifest['freeze_date'],
          'another release id or date')
    s = sources(manifest)
    # D28: the released file keeps its bytes, the ones its own export audit names.
    released_audit = s['releasedAudit']
    for p in RELEASED_SERVED:
        check(digest(p.read_bytes()) == released_audit['export_sha256'] == manifest['published']['released']['sha256'],
              f'{p.name}: the released file changed')
    check(released_audit['manifest_sha256'] == manifest['published']['releasedManifest']['sha256'],
          'the released export audit names another manifest')
    t = Table()
    pins = {m: b['pins'] for m, b in manifest['blocks'].items()}
    study_xspec(t, s, pins['xspec'])
    study_eigen(t, s, pins['eigen'], pins['xspec'])
    _, A = study_pooling(t, s, pins['pooling'])
    study_wearable(t, s, pins['pooling'])
    study_practical(t, s, pins['practical'], A)
    study_gap(t, s, pins['weights'])
    study_decay(t, s, pins['weights'])
    study_rise(t, s, pins['weights'])
    for study, n in NOT_RUN_ROWS.items():
        t.put(('studies', study, 'not_run'), [{'run_in': None}] * n, 'editorial')
    spanning(t, served, s, manifest)
    rights_strings(t, s, served)

    # Hashes, records and lists the manifest and the sources give as strings.
    for study in STUDIES:
        src = manifest['sources'][study]
        t.put(('provenance', 'source_export_sha256', study), pins[src['block']][src['export']]['sha256'])
        t.put(('provenance', 'release_approval_sha256', study), pins[src['block']][src['approval']]['sha256'])
    cs = manifest['componentSource']['cpu_components']
    t.put(('provenance', 'source_export_sha256', 'cpu_components'), pins[cs['block']][cs['export']]['sha256'])
    t.put(('provenance', 'release_approval_sha256', 'cpu_components'), pins[cs['block']][cs['approval']]['sha256'])
    for study, h in manifest['handoffContext'].items():
        t.put(('provenance', 'handoff_sha256', study), h['sha256'])
        src = manifest['sources'].get(study) or manifest['componentSource'][study]
        check(h['queue_row'] == src['queue_row'], f'{study}: another queue row than its source')
        named = h.get('queue_handoff', h)       # row 30 names the parent handoff that asked for the CPU timings
        row = s['queue']['rows'][h['queue_row']]
        check(row['source_sha256'] == named['sha256'] and row['canonical_handoff'] == named['path'],
              f'{study}: the queue row names another handoff')
        if named is not h:
            check(named['states'] in s[f'queue_handoff:{study}'], f'{study}: the queue row’s handoff asks for another study')
    t.put(('provenance', 'manifest_sha256'), digest(manifest_bytes))
    t.put(('provenance', 'released_file'), {'release_id': s['released']['release_id'],
                                            'file': Path(manifest['published']['released']['path']).name,
                                            'sha256': released_audit['export_sha256'], 'unchanged': True,
                                            'export_audit_sha256': manifest['published']['releasedAudit']['sha256']})
    t.put(('provenance',), {'owner_decisions_sha256': manifest['approval']['ownerDecisions']['sha256'],
                            'plan_sha256': manifest['planning']['plan']['sha256'],
                            'queue_sha256': manifest['planning']['queue']['sha256'],
                            'consolidated_handoff_sha256': manifest['planning']['consolidatedHandoff']['sha256']})
    rr = manifest['releaseRecord']
    t.put(('release_record',), {'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
                                'rights': rr['rights'], 'research_release': rr['researchRelease'],
                                'binding': rr['binding']})
    t.put(('not_published',), manifest['notPublished'])
    t.put(('schema_version',), 'bci-report-ssvep-followups-update-v1')
    t.put(('release_id',), manifest['release_id'])
    t.put(('generated_at',), manifest['freeze_date'])
    t.put(('status',), manifest['approval']['decision'])
    codes = export_codes(served, s, manifest)
    named = same_estimates(t, served, s)
    shared = shared_rows(t, served, s)

    # One for one: every figure has a rule and every rule a figure; every string is derived or editorial.
    found = dict(leaves(served))
    kinds = {'copied': 0, 'derived': 0, 'editorial': 0}
    nulls = 0
    for path, value in found.items():
        if isinstance(value, str):
            if path in t.strings:
                check(value == t.strings[path], f'{show(path)}: {value!r} where the sources give {t.strings[path]!r}')
            else:
                check(covered(path, t), f'{show(path)}: a string with no audit rule')
            continue
        if any(path[:len(p)] == p for p in t.sets):
            continue
        check(path in t.figures, f'{show(path)}: a figure with no audit rule')
        want, kind = t.figures[path]
        if want is NULL:
            check(value is None, f'{show(path)}: a null became {value!r}')
            nulls += 1
            continue
        check(same(value, want), f'{show(path)}: {value!r} where the sources give {want!r}')
        kinds[kind] += 1
    for path, rows in t.sets.items():
        here = served
        for k in path:
            here = here[k]
        check(sorted(json.dumps(r, sort_keys=True) for r in here) == rows, f'{show(path)}: other rows than the sources give')
    missing = [p for p in list(t.figures) + list(t.strings) if p not in found]
    check(not missing, f'expected values missing from the served file: {[show(x) for x in missing[:3]]}')
    # One set of scores under one name: every level the shared rows list holds the same double.
    for row in served['shared_estimates']:
        values = {served['studies'][x['study']]['levels'][x['level']]['estimate'] for x in row['levels']}
        if 'released_level' in row:
            r = row['released_level']
            values.add(s['released']['studies'][r['study']]['levels'][r['level']]['estimate'])
        check(len(values) == 1, f'{row["site_name"]} {row["endpoint"]}: not one set of scores')
    given = sorted((st, c) for st, b in served['studies'].items() for c in b['display_names'])
    placed = sorted((c['study'], c['code']) for r in served['name_key'] for c in r['codes'])
    check(given == placed, 'the name key does not place every code once')

    text_blob = served_bytes[0].decode()
    published = {v for v in found.values() if is_number(v)}
    secret = withheld(s)                  # doubles: an integer count of 8 is not the frequency 8.0 Hz
    leaked = secret & {v for v in published if isinstance(v, float)}
    check(not leaked, f'a withheld value reached the served file: {sorted(leaked)[:3]}')
    check(all(abs(v - 11 / 20) > 1e-12 and abs(v - 55) > 1e-9 for v in published),
          'the commenter’s confidence figure is a value in the served file')
    for path, value in found.items():
        if isinstance(value, str) and not re.fullmatch(r'[0-9a-f]{64}', value):
            check(not re.search(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                                value, re.I), f'{show(path)}: a token of the commenter’s confidence figure')
            if path[0] != 'not_published':
                check(not re.search(r'huggingface|hugging face|/posts/|commenter|comment thread', value, re.I),
                      f'{show(path)}: the comment thread')
    check(not any(re.search(r'fifty|05{2}|prediction|thread_bet', str(k), re.I) for p in found for k in p),
          'a key built on the commenter’s confidence figure or the thread')
    private = private_names(s)
    check(len(private) >= 4, 'no private names read from the pinned records')
    for n in private | {'twu', 'trx50', 'gal4', 'bigdata'}:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text_blob, re.I) is None,
              'a private user, host or volume name reached the served file')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')
    check(re.search(r'threadripper|ryzen|7965WX|epyc|xeon', text_blob, re.I) is None, 'a host processor label')
    # Last: the editorial strings this audit does not derive are bound by bytes to the export program's fresh build.
    check(digest(fresh_build(manifest_bytes)) == digest(served_bytes[0]),
          'the served bytes are not the export’s fresh build from this manifest: an editorial string differs')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'released_file_sha256': released_audit['export_sha256'],
        'auditor': 'pipeline/publication/audit_ssvep_followups_export.py',
        'independence': ('A separate program from the export and from the five block modules, importing none of '
                         'them. It reads the served bytes, the release manifest and the files the manifest pins, '
                         're-derives every study block from the original aggregates by its own reading (level and '
                         'contrast ids from the aggregates’ own labels, roles from the protocols, reuse from the card '
                         'each comparator comes from), and recomputes the designs, the decision-change shares, the '
                         'reference check and every check count from the protocols, approvals, reviews and receipts. '
                         'Its last check runs the export program in a separate process on the same manifest bytes and '
                         'requires the served bytes to equal that build, which binds the editorial strings it does not '
                         'derive.'),
        'figures_compared': len(t.figures), 'copied_exactly': kinds['copied'], 'recomputed': kinds['derived'],
        'editorial': kinds['editorial'], 'nulls_kept': nulls, 'strings_compared': len(t.strings),
        'row_sets_compared': len(t.sets), 'export_codes_resolved': codes, 'same_estimate_names': named,
        'shared_rows_derived': shared, 'context_pins_bound': len(manifest['contextPins']),
        'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'the released new-ssvep-frequencies-update.json keeps the bytes its 2026-10-20 export audit names, in both '
            'served copies',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'every level and contrast is its study aggregate’s own double, and every contrast equals the difference '
            'of its two levels',
            'every reused comparator equals the card it comes from to the last bit: card 5 and card 7 in the released '
            'file, card 8 in the cross-spectral aggregate, card 9 in the coherence aggregate, card 10 in the A/C '
            'summary',
            'card 8’s whitened-readout gap is the difference of the two source levels, as the handoff prints it',
            'card 12’s decision changes are recomputed as count / 11,200 and their net equals the level difference',
            'the designs, interval methods and every check count recomputed from the pinned protocols, approvals, '
            'reviews and receipts; the CPU component medians read from the timing aggregate, wall clock only',
            'every export code resolves in its source to the value the served file gives',
            'each shared row’s interval home, whether its cards’ intervals differ, and its aliases, worked out from '
            'the intervals derived here and the display names; every card keeps its own source interval',
            'every context-only pin has its pinned bytes and is bound by a pinned record, by SHA-256 or by file name; '
            'every handoff is the one its queue row names (row 30: the parent handoff that asked for the CPU timings)',
            'hashes, released rights records, the FBCCA credit, the release record and the not-published list '
            'checked as strings',
            'no withheld value, no part of the comment thread, no form of the commenter’s confidence figure, no '
            'private path, no host label and no private user, host or volume name in the served file',
            'the served bytes equal the export program’s fresh build from the same manifest bytes, run in a separate '
            'process, so every editorial string is the export’s own',
        ],
        'audit_bindings': {
            'bound': [
                'every study’s aggregate, review, approval, protocol and receipts: pinned in the manifest, and the '
                'same bytes the block modules pin, which the export checks',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
                'editorial strings (display names, limitation keys, card anchors, the name key’s rows and the text '
                'this release writes): bound by bytes to the export program’s fresh build; their wording is checked '
                'by the export and its tests',
            ],
            'not_bound': [
                'the run outputs behind each aggregate (predictions, seals, fitted models): each study’s own '
                'numerical review recomputed them; this audit opens no sealed file',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
