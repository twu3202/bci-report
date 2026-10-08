"""Independent audit of questions-in-language-update.json and questions-in-language-wordings.json.

A separate program from export_questions_in_language_update.py. It shares no extraction code with that export and
does not read the release candidate the export is built from. It reads the two served files, the review manifest
and, by their pinned hashes, the consolidated aggregate, the two audited aggregates, the protocol, the stage-0 report
and the two numerical audits; it builds its own table of what every figure must be and compares the two one for one:

- every number and every null in either served file has an expected value here, and every expected value is in the
  file: nothing unaudited, nothing missing;
- copied figures equal their source exactly, type included: each primary entry equals the audited primary aggregate
  and, for SSVEP, numerical audit A2's own recomputed value; each secondary entry equals the audited secondary
  aggregate, with A4's match flags; every level, contrast, read-off and flip rate equals the audited aggregates;
- derived figures are recomputed here: chance-corrected values, R from log R, the headroom floor, the S9 harmonic
  means, counts of cells and entries;
- every difference flag, margin flag and route-sentence rule is recomputed from its interval and the frozen margin;
- every BOAS figure states its n and pools at least 20 people; no S10 per-frequency or interior-only value and no
  pre-run check value reaches either file;
- the wording lists re-serialise to the hash the protocol and the stage-0 report record, and the partition, grid,
  derangements and NUM code are the protocol's; the two served copies of each file are byte-identical.

    python3 pipeline/publication/audit_questions_in_language_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261008'
MANIFEST = REVIEW / 'questions-in-language-release-manifest.json'
AUDIT = REVIEW / 'questions-in-language-export-audit.json'
SERVED = (PROJECT / 'site/src/data/questions-in-language-update.json',
          PROJECT / 'site/public/data/questions-in-language-update.json')
SERVED_WORDINGS = (PROJECT / 'site/src/data/questions-in-language-wordings.json',
                   PROJECT / 'site/public/data/questions-in-language-wordings.json')
R = ('results', 'questions-in-language')
BLOCKS = ('P-ssvep-L0', 'P-ssvep-L1', 'P-sleep-L1')
ENTRY_PARTS = ('S1', 'S2', 'S3-sleep', 'S3-ssvep', 'S4-sleep-L1', 'S4-ssvep-L0', 'S4-ssvep-L1', 'S5-sleep-L1',
               'S5-ssvep-L0')
BOAS_DATASET = 'BOAS'
MARGIN = 0.02                    # 2 pp, as a difference of proportions (protocol decision_rules.margins)


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(ref):
    raw = (PROJECT / ref['path']).read_bytes()
    check(digest(raw) == ref['sha256'], f'{ref["path"]}: not the pinned bytes')
    return json.loads(raw)


def unwrap(node):
    """A {source, value} block's value, nested blocks included."""
    while isinstance(node, dict) and 'source' in node and 'value' in node:
        node = node['value']
    return node


# ---------------------------------------------------------------------------- the frozen rules, re-implemented
def expected_flags(kind, lo, hi):
    if kind == 'log R':
        diff = 'difference: the read-off leaves less error' if lo > 0 else 'no difference shown'
        bound = math.log(1.25)
        if lo > -bound and hi < bound:
            return diff, 'equivalent within the margin'
        return diff, 'non-inferior' if hi < bound else 'margin not met'
    diff = ('difference: language arm higher' if lo > 0 else 'difference: reference higher' if hi < 0
            else 'no difference shown')
    if kind == 'difference only':
        return diff, 'not applicable (difference only)'
    if lo > -MARGIN and hi < MARGIN:
        return diff, 'equivalent within the margin'
    return diff, 'non-inferior' if lo > -MARGIN else 'margin not met'


def expected_rule(diff, margin, kind):
    if kind == 'difference only':
        return -1
    against = diff in ('difference: reference higher', 'difference: the read-off leaves less error')
    met = margin in ('equivalent within the margin', 'non-inferior')
    if against:
        return 2 if met else 1
    if diff == 'difference: language arm higher':
        return 3
    return 4 if margin == 'equivalent within the margin' else 5 if margin == 'non-inferior' else 6


def kind_of(entry_type):
    return {'P3': 'log R', 'P4_nn': 'difference only', 'P4_num': 'difference only', 'P5': 'difference only'}.get(
        entry_type, 'margin')


# ---------------------------------------------------------------------------- what every figure must be
class Table:
    def __init__(self):
        self.copied, self.derived, self.flags = {}, {}, []

    def copy(self, path, value):
        check(path not in self.copied and path not in self.derived, f'{path}: two rules')
        self.copied[path] = value

    def derive(self, path, value):
        check(path not in self.copied and path not in self.derived, f'{path}: two rules')
        self.derived[path] = value

    def fig(self, path, src, keys=('point', 'lo', 'hi', 'people', 'seeds')):
        """A level or contrast: estimate, interval, n and seeds from a bootstrap record."""
        self.copy(path + ('estimate',), src['point'])
        self.copy(path + ('interval_95', 0), src['lo'])
        self.copy(path + ('interval_95', 1), src['hi'])
        self.copy(path + ('people',), src['people'])
        if 'seeds' in keys and 'seeds' in src:
            self.copy(path + ('seeds',), src['seeds'])


def entry(t, path, src, wrapper):
    """A pre-declared entry from its audited aggregate row, and its derived values from the consolidated one."""
    t.fig(path, src)
    t.copy(path + ('rule',), src['rule'])
    for k, n in src['resampled_wording_kinds'].items():
        t.copy(path + ('resampled_wording_kinds', k), n)
    kind = kind_of(src['type'])
    diff, margin = expected_flags(kind, src['lo'], src['hi'])
    t.flags.append((path, diff, margin, expected_rule(diff, margin, kind), src))
    if 'chance_corrected' in wrapper:
        c = wrapper['chance_corrected']['chance']
        t.copy(path + ('chance_corrected', 'chance'), c)
        for i, k in enumerate(('point', 'lo', 'hi')):
            want = src[k] / (1 - c)
            got = wrapper['chance_corrected'][k]
            check(math.isclose(got, want, rel_tol=1e-12, abs_tol=1e-15), f'{path}: chance-corrected {k}')
            t.copy(path + (('chance_corrected', 'estimate') if i == 0 else ('chance_corrected', 'interval_95', i - 1)),
                   got)
    if 'R' in wrapper:
        for i, k in enumerate(('point', 'lo', 'hi')):
            got = wrapper['R'][k]
            check(math.isclose(got, math.exp(src[k]), rel_tol=1e-12), f'{path}: R {k} is not exp(log R)')
            t.copy(path + (('r', 'estimate') if i == 0 else ('r', 'interval_95', i - 1)), got)


def primary(t, agg, agg_p, a2):
    a2_by = {}
    for e in a2['entries']:
        a2_by.setdefault(e['block'], []).append(e)
    t.copy(R + ('primary', 'entries_count'), agg['primary']['entries_count'])
    for b_i, block in enumerate(agg['primary']['blocks']):
        audited = agg_p['blocks'][b_i]
        P = R + ('primary', 'blocks', b_i)
        t.copy(P + ('people',), block['people'])
        t.copy(P + ('seeds',), block['seeds'])
        t.copy(P + ('gates', 'triviality', 'threshold'), audited['gates']['triviality']['threshold'])
        a2_rows = a2_by[f'{block["domain"]}/{block["level"]}']
        check(len(a2_rows) == len(audited['entries']) == len(block['entries']), f'{block["block"]}: entry counts')
        for e_i, (wrapper, src, a2e) in enumerate(zip(block['entries'], audited['entries'], a2_rows)):
            check(unwrap(wrapper) == src, f'{block["block"]}/{e_i}: the aggregates disagree')
            check(a2e['label'] == src['label'] and a2e['max_abs_diff_point_lo_hi'] == 0.0
                  and all(a2e[k] is True for k in ('difference_flag_match', 'margin_flag_match', 'rule_match',
                                                   'sentence_match', 'counts_match')),
                  f'{block["block"]}/{e_i}: audit A2 did not reproduce it')
            if block['dataset'] != BOAS_DATASET:   # A2 carries its own recomputed SSVEP values
                check((a2e['audit_point'], a2e['audit_lo'], a2e['audit_hi']) == (src['point'], src['lo'], src['hi']),
                      f'{block["block"]}/{e_i}: A2 recomputed another value')
            entry(t, P + ('entries', e_i), src, wrapper)
    fam = unwrap(agg['primary']['family_sentences'])
    for pid in ('P1', 'P2', 'P3', 'P4', 'P5'):     # a family rule only where every entry reached the same one
        rules = {e['rule'] for b in agg_p['blocks'] for e in b['entries'] if e['id'] == pid}
        check(fam[pid]['rule'] == (rules.pop() if len(rules) == 1 else None), f'{pid}: the family rule')
        t.copy(R + ('primary', 'family_sentences', pid, 'rule'), fam[pid]['rule'])


def descriptive(t, agg, agg_s):
    cc = agg['primary_descriptive']['chance_corrected_levels']['value']
    for block in BLOCKS:
        src = agg_s['primary_blocks_descriptive'][block]
        D = R + ('descriptive', block)
        for name, x in src['levels'].items():
            t.fig(D + ('levels', name), x)
            if name in cc[block]:
                c = cc[block][name]
                t.copy(D + ('levels', name, 'chance'), c['chance'])
                for i, k in enumerate(('point', 'lo', 'hi')):
                    want = (x[k] - c['chance']) / (1 - c['chance'])
                    check(math.isclose(c[k], want, rel_tol=1e-12, abs_tol=1e-15), f'{block} {name}: chance-corrected')
                    t.copy(D + ('levels', name, 'chance_corrected') + (('estimate',) if i == 0 else ('interval_95', i - 1)),
                           c[k])
        for name, x in src.items():
            if isinstance(x, dict) and 'point' in x:
                t.fig(D + ('contrasts', name), x)
        for group in ('generalisation_costs', 'S15', 'seen_auroc_per_predicate', 'log_loss'):
            for name, x in src.get(group, {}).items():
                t.fig(D + (group, name), x)
        if 'chance_3way_mean' in src:
            t.copy(D + ('chance_3way_mean', 'stored'), src['chance_3way_mean'])


def pre_run(t, agg, agg_p, agg_s, s0, a4):
    P = R + ('pre_run_checks',)
    C = P + ('canaries',)
    r3, r4, r5 = (s0[k] for k in ('permutation_canary_revision_3', 'permutation_canary_revision_4_gate',
                                  'permutation_canary_revision_5_gate'))
    t.copy(C + ('revision_3', 'intervals'), r3['intervals'])
    t.copy(C + ('revision_3', 'intervals_excluding_chance'), r3['intervals_excluding_chance'])
    t.copy(C + ('revision_4', 'fits'), r4['fits'])
    t.copy(C + ('revision_4', 'intervals'), r4['intervals'])
    t.copy(C + ('revision_4', 'intervals_excluding_chance'), r4['intervals_excluding_chance'])
    check(not r3['pass'] and not r4['pass'] and r5['pass'], 'the canary outcomes')
    d = r5['descriptive']
    for k, v in (('configurations', len(r5['by_configuration'])), ('replicates', 20), ('fits', r5['fits']),
                 ('level', 0.999), ('bootstrap_draws', 2000), ('intervals', r5['intervals']),
                 ('intervals_excluding_zero', r5['intervals_excluding_zero']),
                 ('single_head_tests', d['single_head_tests']),
                 ('cells_with_single_head_failures_in_both_directions',
                  d['cells_with_single_head_failures_in_both_directions']['boas']
                  + d['cells_with_single_head_failures_in_both_directions']['ssvep'])):
        t.copy(C + ('revision_5', k), v)
    check('20 replicate heads' in r5['design'] and '99.9%' in r5['interval'] and '2000 draws' in r5['interval'],
          'the revision-5 design as the stage-0 report states it')
    ex = d['single_head_intervals_excluding_exact_chance']
    t.copy(C + ('revision_5', 'single_head_intervals_excluding_exact_chance', 'above'), ex['above'])
    t.copy(C + ('revision_5', 'single_head_intervals_excluding_exact_chance', 'below'), ex['below'])
    t.derive(C + ('revision_5', 'single_head_intervals_excluding_exact_chance', 'total'), ex['above'] + ex['below'])
    a4c = a4['checks']['canary_disclosure']
    check(a4c['r5_single_head']['exact'] == {'above': ex['above'], 'below': ex['below']}
          and a4c['r5_intervals_excluding_zero'] == r5['intervals_excluding_zero'], 'A4 reproduced other counts')
    scope = s0['token_rule']['scope']
    S = P + ('decision_s0b6', 'token_rule')
    t.copy(S + ('rotations_passed',), len(scope['stops_run']['rotations']))
    t.copy(S + ('multilingual_e5_small', 'rotations'), scope['e5_number_pieces_only']['rows'])
    t.copy(S + ('multilingual_e5_small', 'number_pieces_only_rule_passed'), scope['e5_number_pieces_only']['rows'])
    t.copy(S + ('multilingual_e5_small', 'full_rule_passed'), sum(scope['e5_number_pieces_only']['full_rule_pass']))
    num = s0['numeracy_probe']
    for k, v in num['spearman_rho'].items():
        t.copy(P + ('numeracy_probe', 'spearman_rho', k), v)
    t.copy(P + ('numeracy_probe', 'pairs'), num['pairs'])
    G = P + ('gates',)
    for block, chance in (('P-ssvep-L0', 1 / 32), ('P-ssvep-L1', 1 / 32), ('P-sleep-L1', 1 / 5)):
        x = agg_s['primary_blocks_descriptive'][block]['levels']['ID seen_ba']
        H = G + ('headroom', block)
        t.fig(H, x)
        t.copy(H + ('chance',), chance)
        t.derive(H + ('floor',), chance + 0.05)
        t.copy(H + ('ceiling',), 0.95)
        check(x['lo'] > chance + 0.05 and x['hi'] < 0.95, f'{block}: the headroom gate')
    triv = agg['pre_run_checks']['gates']['triviality']
    thresholds = {'BETA': agg_p['blocks'][0]['gates']['triviality']['threshold'],
                  'BOAS': agg_p['blocks'][2]['gates']['triviality']['threshold'],
                  'EESM19': agg_s['parts']['S1']['gates']['triviality']['threshold']}
    for ds, th in thresholds.items():
        t.copy(G + ('triviality', ds, 'threshold'), th)
        t.copy(G + ('triviality', ds, 'training_people'), triv[ds]['people'])
    p3_primary = sum(e['type'] == 'P3' for b in agg_p['blocks'] for e in b['entries'])
    p3_secondary = sum(e['type'] == 'P3' for p in agg_s['parts'].values() for e in p.get('entries', []))
    for k, v in (('primary_cells', p3_primary), ('primary_cells_passing', p3_primary),
                 ('secondary_cells', p3_secondary), ('secondary_cells_passing', p3_secondary)):
        t.derive(G + ('readoff_floor', k), v)
    fit = s0['fit_check']
    t.copy(G + ('fit_check', 'fits'), fit['fits'])
    for dl, epochs in fit['epochs_final_recipe'].items():
        t.copy(G + ('fit_check', 'by_domain_and_level', dl, 'training_epochs'), epochs)
        t.derive(G + ('fit_check', 'by_domain_and_level', dl, 'failed_fits'), len(fit['by_domain_level'][dl]['failed_fits']))
    sh = agg['pre_run_checks']['gates']['shuffled_eeg_scorer_check']
    t.copy(G + ('shuffled_eeg_scorer_check', 'cells'), sh['cells'])
    t.copy(G + ('shuffled_eeg_scorer_check', 'cells_within_3_se'), sh['cells_within_3_se'])
    t.derive(G + ('shuffled_eeg_scorer_check', 'ssvep_cells'), len(sh['ssvep_cells']))
    t.derive(G + ('shuffled_eeg_scorer_check', 'boas_cells'), sh['cells'] - len(sh['ssvep_cells']))
    check(agg_p['shuffled_eeg_check_pass'] is True, 'the shuffled-EEG check did not pass')


def secondary(t, agg, agg_s, a4):
    S = R + ('secondary', 'parts')
    a4_by = {}
    for e in a4['entries']:
        a4_by.setdefault(e['part'], []).append(e)
    for pid in ENTRY_PARTS:
        part, wrapped = agg_s['parts'][pid], agg['secondary']['parts'][pid]
        t.copy(S + (pid, 'gates', 'triviality', 'threshold'), part['gates']['triviality']['threshold'])
        rows = a4_by[pid]
        check(len(rows) == len(part['entries']) == len(wrapped['entries']), f'{pid}: entry counts')
        for i, (src, wrapper, a4e) in enumerate(zip(part['entries'], wrapped['entries'], rows)):
            check(unwrap(wrapper) == src and a4e['label'] == src['label'], f'{pid}/{i}: the aggregates disagree')
            check(all(a4e[k] is True for k in ('difference_flag_match', 'margin_flag_match', 'rule_match',
                                               'counts_match', 'aggregate_equals_private')), f'{pid}/{i}: A4')
            # A4's explained discrepancies: D-1 (EESM19 'asleep' read-offs at float64 saturation, up to 1.5e-5 on
            # log R) and D-2 (two S2 sentences, wording only). Nothing else may differ.
            check(a4e['max_abs_diff_point_lo_hi'] <= 1e-9 or (pid == 'S1' and 'asleep' in src['label']
                                                              and a4e['max_abs_diff_point_lo_hi'] < 2e-5),
                  f'{pid}/{i}: A4 recomputed another value')
            check(a4e['sentence_match'] is True or (pid == 'S2' and src['type'] == 'P3' and src['rule'] == 2),
                  f'{pid}/{i}: A4 recomputed another sentence')
            entry(t, S + (pid, 'entries', i), src, wrapper)
    s6 = agg_s['parts']['S6']
    for w, cell in s6['cells'].items():
        for k, x in cell.items():
            t.fig(S + ('S6', 'cells', w, k), x)
    for k, x in agg_s['parts']['S13-sleep'].items():
        if k == 'what':
            continue
        t.fig(S + ('S13-sleep', 'rows', k), x)
        d, m = expected_flags('log R', x['lo'], x['hi'])
        t.flags.append((S + ('S13-sleep', 'rows', k), d, m, None, x))
    for pid in ('SSVEP-L0-secondary', 'SSVEP-L1-secondary'):
        for k, x in agg_s['parts'][pid].items():
            if k == 'what':
                continue
            if k.startswith('S10 rotation'):
                path = S + (pid, 'per_rotation_tpl_minus_cca_8_way', x['label'])
            elif 'difference' in x:
                path = S + (pid, 'rows', k)
            elif 'point' in x:
                t.fig(S + (pid, 'levels', k), x)
                continue
            else:
                for m, y in x.items():
                    if m == 'harmonic_mean':
                        s_, u_ = x['seen_truth']['point'], x['unseen_truth']['point']
                        check(math.isclose(y, 2 * s_ * u_ / (s_ + u_), rel_tol=1e-12), f'{pid} {k}: harmonic mean')
                        t.copy(S + (pid, 'levels', k, m), y)
                    else:
                        t.fig(S + (pid, 'levels', k, m), y)
                continue
            t.fig(path, x)
            d, m = expected_flags('margin', x['lo'], x['hi'])
            t.flags.append((path, d, m, None, x))
    for pid in ('S8-L0', 'S8-L1'):
        for k, x in agg_s['parts'][pid].items():
            if k in ('what', 'notes', 'levels (descriptive)') or x.get('status') == 'not defined':
                continue
            t.fig(S + (pid, 'rows', k), x)
            d, m = expected_flags('margin', x['lo'], x['hi'])
            t.flags.append((S + (pid, 'rows', k), d, m, None, x))
    for sensor, name in (('0', 'dry'), ('1', 'wet')):
        for k, x in agg_s['parts']['S12']['by_sensor'][sensor].items():
            t.fig(S + ('S12', 'by_sensor', name, k), x)
            d, m = expected_flags('margin', x['lo'], x['hi'])
            t.flags.append((S + ('S12', 'by_sensor', name, k), d, m, None, x))
    F = R + ('secondary', 'flip_rates')
    for pid in ('flip-ssvep-L0', 'flip-ssvep-L1', 'flip-sleep-L1'):
        x = agg_s['parts'][pid]
        # BOAS states its n; the SSVEP rates are over the BETA block's people.
        n = x['people'] if 'sleep' in pid else agg['primary']['blocks'][0]['people']
        for arm in ('TPL', 'DESC'):
            for k, v in x[arm].items():
                t.copy(F + (pid, arm, k, 'rate'), v)
                t.copy(F + (pid, arm, k, 'people'), n)
        t.copy(F + (pid, 'between_ID_seeds', 'rate'), x['ref_between_ID_seeds'])
        t.copy(F + (pid, 'between_ID_seeds', 'people'), n)


def audits(t, files):
    A = R + ('audits',)
    a1, a2, a3, a4 = files
    t.copy(A + ('primary_conformance', 'checks'), a1['checks_total'])
    t.copy(A + ('primary_conformance', 'failed'), a1['checks_failed'])
    t.copy(A + ('secondary_conformance', 'checks'), a3['checks_total'])
    t.copy(A + ('secondary_conformance', 'failed'), a3['checks_failed'])
    summary = a2['checks']['metrics_contrasts_intervals_flags_sentences']['summary']
    n2 = int(summary.split(' comparisons')[0].replace(',', ''))
    t.copy(A + ('primary_numeric', 'comparisons'), n2)
    t.derive(A + ('primary_numeric', 'numeric_values'),
             sum(g['values_compared'] for g in a2['checks']['metrics_contrasts_intervals_flags_sentences']['groups'].values()))
    t.derive(A + ('primary_numeric', 'mismatches'), 0)
    t.derive(A + ('primary_numeric', 'entries_recomputed'), len(a2['entries']))
    note = a4['verdict_note']
    n4, out4 = note.split(' comparisons, ')[0], note.split(' comparisons, ')[1].split(' outside tolerance')[0]
    t.copy(A + ('secondary_numeric', 'comparisons'), int(n4.replace(',', '')))
    t.copy(A + ('secondary_numeric', 'outside_tolerance'), int(out4))
    check(', 0 unexplained' in note, 'A4 left something unexplained')
    t.derive(A + ('secondary_numeric', 'unexplained'), 0)
    t.derive(A + ('secondary_numeric', 'entries_recomputed'), len(a4['entries']))


def design_and_boas(t, protocol, agg_s, a4, served):
    for i, r in enumerate(protocol['route_sentence_rules']['first_match_order']):
        t.copy(R + ('design', 'route_sentence_rules', 'first_match_order', i, 'rule'), r['rule'])
    m = protocol['decision_rules']['margins']
    t.copy(R + ('design', 'margins', 'delta_pp'), m['accuracy_pp'])
    t.copy(R + ('design', 'margins', 'p3_ratio'), m['P3_log_R_ratio'])
    d11 = agg_s['boas_d11']
    parts = served['results']['questions-in-language']['secondary']['parts']
    flips = served['results']['questions-in-language']['secondary']['flip_rates']
    marked = {p for p, x in parts.items() if x.get('boas') is True} | {p for p, x in flips.items() if x['boas'] is True}
    check(marked == {p for p in d11['parts'] if '/' not in p}, 'the BOAS parts are not the ones the D11 check names')
    smallest = min(boas_people(served['results']['questions-in-language']))
    check(smallest == a4['checks']['boas_d11']['min_people'] and a4['checks']['boas_d11']['cells_below_20'] == [],
          'the smallest BOAS cell is not the one audit A4 found')
    t.copy(('boas_conditions', 'minimum_cell_people'), d11['min_people_per_cell'])
    t.copy(('boas_conditions', 'smallest_cell_people'), a4['checks']['boas_d11']['min_people'])


def wordings(t, w, protocol, agg, s0, manifest_sha):
    lists = w['lists']
    data = (json.dumps(lists, indent=2, ensure_ascii=False) + '\n').encode()
    check(digest(data) == protocol['stage0b']['lists_file_sha256'] == s0['wordings']['lists_file_sha256']
          == w['provenance']['wording_lists_sha256'], 'the wording lists are not the hashed lists')
    texts = 0

    def walk(v):
        nonlocal texts
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            texts += 1
    walk(lists)
    t.derive(('texts',), texts)
    for path, v in leaves(lists):           # bound byte for byte by the hash above (names left null stay null)
        t.copy(('lists',) + path, v)
    for path, v in leaves(protocol['wordings']['kinds']):
        t.copy(('kinds',) + path, v)
    check(texts == agg['wordings']['texts_in_lists'], 'the wording count')
    spec, declared = protocol['analysis_spec'], protocol['declared_now']
    for i, f in enumerate(spec['grid']):
        t.copy(('frequency_grid_hz', i), f)
    for r, fs in declared['partition'].items():
        for i, f in enumerate(fs):
            t.copy(('held_out_partition_hz', f'rotation {r}', i), f)
    for i, f in enumerate(spec['s8_heldout']):
        t.copy(('s8_held_out_band_hz', i), f)
    num = declared['num_code']
    for k, v in num.items():
        if isinstance(v, list):
            for i, x in enumerate(v):
                t.copy(('num_code', k, i), x)
        else:
            t.copy(('num_code', k), v)
    for k, e in protocol['text_encoders_pinned'].items():
        t.copy(('text_encoders', k, 'parameters'), e['params'])
    check(w['derangements']['sleep_by_seed'] == declared['sleep_derangements']
          and w['derangements']['motor_imagery_by_seed'] == declared['mi_derangements']
          and w['derangements']['ssvep_s10_by_rotation_and_seed_index'] == declared['ssvep_shuf_derangements'],
          'the derangements are not the protocol\'s')
    check(w['provenance']['manifest_sha256'] == manifest_sha, 'the wordings file names another manifest')


# ---------------------------------------------------------------------------- comparison
def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    elif value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        yield trail, value


def boas_people(value, inside=False):
    if isinstance(value, dict):
        here = inside or value.get('boas') is True or value.get('dataset') == BOAS_DATASET
        if here and isinstance(value.get('people'), int):
            yield value['people']
        for k, x in value.items():
            yield from boas_people(x, here)
    elif isinstance(value, list):
        for x in value:
            yield from boas_people(x, inside)


def boas_figures_state_n(value, inside=False, n=None, trail=()):
    """Every BOAS figure carries its n, or is a sub-figure (chance-corrected, R) of a cell that does."""
    if isinstance(value, dict):
        here = inside or value.get('boas') is True or value.get('dataset') == BOAS_DATASET
        own = value['people'] if isinstance(value.get('people'), int) else n
        if here and ('estimate' in value or 'rate' in value):
            check(own is not None and own >= 20, f'{trail}: a BOAS figure without an n of at least 20')
        for k, x in value.items():
            boas_figures_state_n(x, here, own if ('estimate' in value or 'rate' in value) else None, trail + (k,))
    elif isinstance(value, list):
        for i, x in enumerate(value):
            boas_figures_state_n(x, inside, n, trail + (i,))


def node_at(payload, path):
    node = payload
    for k in path:
        node = node[k]
    return node


def withheld(agg, s0):
    """The S10 breakdowns and the pre-run check values: none may reach either file."""
    out = set()

    def take(v, keys):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in keys and isinstance(x, float):
                    out.add(x)
                else:
                    take(x, keys)
        elif isinstance(v, list):
            for x in v:
                take(x, keys)
    for level in agg['s10_breakdowns']['value']['levels'].values():
        take(level['per_frequency'], {'point', 'lo', 'hi'})
        take(level['interior_only'], {'point', 'lo', 'hi'})
    take(s0['fit_check']['by_domain_level'], {'ID', 'TPL', 'DESC', 'SHUF', 'NUM', 'B-sh'})
    for k in ('permutation_canary_revision_3', 'permutation_canary_revision_4_gate', 'permutation_canary_revision_5_gate'):
        take(s0[k], {'point', 'lo', 'hi', 'D', 'metric_mean', 'between_replicate_sd_metric'})
    take(agg['pre_run_checks']['gates']['shuffled_eeg_scorer_check']['ssvep_cells'], {'mean', 'mc_se'})
    out |= {x['value'] for x in agg['pre_run_checks']['gates']['triviality'].values() if isinstance(x['value'], float)}
    return out


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served = [p.read_bytes() for p in SERVED]
    served_w = [p.read_bytes() for p in SERVED_WORDINGS]
    check(served[0] == served[1] and served_w[0] == served_w[1], 'the two served copies differ')
    payload, w = json.loads(served[0]), json.loads(served_w[0])
    manifest_sha = digest(manifest_bytes)
    check(payload['release_id'] == w['release_id'] == manifest['release_id']
          and payload['provenance']['manifest_sha256'] == manifest_sha, 'the served files name another manifest')
    route = manifest['route']
    check(payload['provenance']['release_candidate_sha256'] == route['releaseCandidate']['sha256'],
          'the served file names another release candidate')
    agg, agg_p, agg_s = load(route['aggregate']), load(route['aggregatePrimary']), load(route['aggregateSecondary'])
    protocol, s0 = load(route['protocol']), load(route['stage0Report'])
    ia = route['independentAudits']
    a1, a2, a3, a4 = (load(ia[k]) for k in ('primaryConformance', 'primaryNumeric', 'secondaryConformance',
                                            'secondaryNumeric'))
    check(a1['pass'] is True and a3['pass'] is True and a2['verdict'] == a4['verdict'] == 'pass', 'an audit failed')
    check(a2['inputs']['aggregate-primary.json'] == route['aggregatePrimary']['sha256']
          and a4['inputs']['aggregate-secondary.json'] == route['aggregateSecondary']['sha256'],
          'the numerical audits checked other aggregates')
    check(agg['inputs_sha256']['aggregate-primary.json'] == route['aggregatePrimary']['sha256']
          and agg['inputs_sha256']['aggregate-secondary.json'] == route['aggregateSecondary']['sha256'],
          'the consolidated aggregate cites other aggregates')

    t = Table()
    primary(t, agg, agg_p, a2)
    descriptive(t, agg, agg_s)
    pre_run(t, agg, agg_p, agg_s, s0, a4)
    secondary(t, agg, agg_s, a4)
    audits(t, (a1, a2, a3, a4))
    design_and_boas(t, protocol, agg_s, a4, payload)
    tw = Table()
    wordings(tw, w, protocol, agg, s0, manifest_sha)

    results = {}
    for name, table, doc in (('results', t, payload), ('wordings', tw, w)):
        expected = {**table.copied, **table.derived}
        found = dict(leaves(doc))
        unaudited = sorted(map(str, set(found) - set(expected)))
        missing = sorted(map(str, set(expected) - set(found)))
        check(not unaudited, f'{name}: figures with no audit rule: {unaudited[:5]}')
        check(not missing, f'{name}: audited figures missing from the served file: {missing[:5]}')
        exact = derived = 0
        for path, want in table.copied.items():
            got = found[path]
            check(type(got) is type(want) and got == want, f'{path}: {got!r} != {want!r}')
            exact += 1
        for path, want in table.derived.items():
            got = found[path]
            check(type(got) is type(want) and (got == want or (isinstance(want, float)
                                                               and math.isclose(got, want, rel_tol=1e-15))),
                  f'{path}: {got!r} != {want!r}')
            derived += 1
        results[name] = {'figures': len(expected), 'copied_exactly': exact, 'recomputed': derived}

    # Flags and rules, from the intervals and the frozen margin.
    n_flags = 0
    for path, diff, margin, rule, src in t.flags:
        node = node_at(payload, path)
        check((node['difference'], node['margin']) == (diff, margin) == (src['difference'], src['margin']),
              f'{path}: the flags do not follow from the interval')
        if rule is not None:
            check(node['rule'] == rule == src['rule'], f'{path}: the rule does not follow from the flags')
        n_flags += 1

    # BOAS: every figure states its n, and none pools fewer than 20 people.
    boas_figures_state_n(payload['results'])
    boas_n = list(boas_people(payload['results']))
    check(min(boas_n) >= 20, 'a BOAS cell under 20 people')

    # Withheld values: none in either file, unless an audited figure has the same value.
    published = {v for _, v in leaves(payload) if isinstance(v, float)} | {v for _, v in leaves(w) if isinstance(v, float)}
    audited_values = {v for table in (t, tw) for v in {**table.copied, **table.derived}.values() if isinstance(v, float)}
    leaked = (withheld(agg, s0) & published) - audited_values
    check(not leaked, f'a withheld value reached a served file: {sorted(leaked)[:3]}')
    n_withheld = len(withheld(agg, s0))

    primary_n = sum(len(b['entries']) for b in payload['results']['questions-in-language']['primary']['blocks'])
    secondary_n = sum(len(p.get('entries', [])) for p in payload['results']['questions-in-language']['secondary']['parts'].values())
    return {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': digest(served[0]), 'wordings_sha256': digest(served_w[0]), 'manifest_sha256': manifest_sha,
        'release_candidate_sha256': route['releaseCandidate']['sha256'],
        'auditor': 'pipeline/publication/audit_questions_in_language_export.py',
        'independence': ('A separate program from the export. It does not read the release candidate the export is '
                         'built from: it reads the two served files, the review manifest and, by their pinned hashes, '
                         'the consolidated aggregate, the two audited aggregates, the protocol, the stage-0 report and '
                         'the numerical audits A2 and A4, builds its own table of what every figure must be, and '
                         'shares no extraction code with the export.'),
        'included': payload['provenance']['included'], 'status_only': payload['status_only'],
        'holds': payload['provenance']['holds'],
        'figures_compared': results['results']['figures'] + results['wordings']['figures'],
        'figures_by_file': {'questions-in-language-update.json': results['results'],
                            'questions-in-language-wordings.json': results['wordings']},
        'primary_entries': primary_n, 'secondary_entries': secondary_n,
        'flags_and_rules_recomputed': n_flags,
        'boas_cells': len(boas_n), 'smallest_boas_cell': min(boas_n),
        'withheld_values_checked_absent': n_withheld,
        'checks': [
            'the two served copies of each file are byte-identical; both files name the manifest they were built '
            'from, and the results file the release candidate',
            'every number and null in either file has an expected value derived here, and every expected value is '
            'in the file: no unaudited figure and no missing one',
            'each primary entry equals the audited primary aggregate, which the consolidated aggregate cites '
            'unchanged; numerical audit A2 matched every flag, rule, sentence and count, and its own recomputed '
            'SSVEP values equal the published ones exactly',
            'each secondary entry equals the audited secondary aggregate; audit A4 matched every flag, rule and '
            'count, and its only differences are the explained ones (D-1: EESM19 "asleep" read-offs at float64 '
            'saturation; D-2: two S2 sentences, wording only)',
            'levels, contrasts, generalisation costs, read-offs, per-stage AUROC, log loss, S6, S8, S9 to S13, '
            'S12 and flip rates equal the audited aggregates; S12 sensor 0 is dry and 1 is wet',
            'chance-corrected values, R from log R, the headroom floor (chance + 5 pp), the S9 harmonic means and '
            'the cell and entry counts are recomputed here',
            'every difference flag, margin flag and route-sentence rule is recomputed from its interval and the '
            'frozen 2-pp margin (log 1.25 for log R)',
            'pre-run checks: the canary outcomes and counts are the stage-0 report\'s and audit A4 reproduced them; '
            'the token-rule, numeracy, fit-check and shuffled-EEG counts are the stage-0 report\'s and the '
            'consolidated aggregate\'s; no check value of any kind reaches either file',
            'every BOAS figure states its n, or belongs to a cell that does, and every BOAS cell pools at least 20 '
            'people',
            'no S10 per-frequency or interior-only value reaches either file',
            'the wording lists re-serialise to the hash the protocol and the stage-0 report record; the grid, the '
            'held-out partition, the S8 band, the NUM code, the derangements and the text encoders are the '
            'protocol\'s',
        ],
        'audit_bindings': {
            'bound': [
                'aggregates, protocol, stage-0 report and numerical audits: by the hashes the manifest pins, '
                'cross-checked against the hashes the consolidated aggregate and the audits record',
                'every figure: equal to its audited source or recomputed from it',
            ],
            'not_bound': [
                'the release candidate\'s {source, value} references, the conformance audits\' checks, the handoff\'s '
                'figures, the BOAS conditions and the rights records are checked by the export, not re-read here',
                'prose in the served files (sentences, notes, disclosures) is checked by the export against its pinned '
                'sources and by pattern, not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
