"""Independent audit of new-ssvep-frequencies-update.json: every figure in the served file against the pinned sources.

A separate program from export_new_ssvep_frequencies_update.py and from the three block modules it assembles
(ssvep_followups/blocks_query.py, blocks_phase.py, blocks_cca.py). It imports none of them: it reads the served bytes,
the release manifest and the files the manifest pins, re-derives every study block from the original research exports
by its own reading of them, and compares the two one for one:

- every number, boolean and null in the served file has an expected value here, and every expected value is in the
  served file, type included: nothing unaudited, nothing missing;
- levels and contrasts are read from each study's own audited export (the one-vs-rest head from the live route 3
  file), with the level and contrast ids worked out here from the export's own labels; every contrast must equal the
  difference of its two levels;
- the declared edits are applied here from the plan's list, not from the modules: the REF `epochs` rename, CCA's seeds
  as "no training", and nothing of the dropped jitter and ramp fields;
- the cohort, the Wearable-102 scope, the endpoints and every check count are recomputed from the protocols, receipts
  and reviews; the bet threshold is read from the ramp protocol's record of the thread;
- every export code points into the source export at the value the served file gives;
- strings are compared where a source gives them; every other string sits under a prefix this audit names as
  editorial (display names, limitation keys, card text), which the export and its tests check;
- the two served copies are one, the served file names the manifest it was built from, and no private path, no
  private user, host or volume name, no withheld value and no form of the commenter's confidence figure is in it.

    python3 pipeline/publication/audit_new_ssvep_frequencies_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
LOCAL = Path(__file__).resolve().parent / 'local_paths.json'
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'new-ssvep-frequencies-release-manifest.json'
AUDIT = REVIEW / 'new-ssvep-frequencies-export-audit.json'
SERVED = (PROJECT / 'site/src/data/new-ssvep-frequencies-update.json',
          PROJECT / 'site/public/data/new-ssvep-frequencies-update.json')
NULL = object()   # an expected JSON null, kept apart from "no rule"

STUDIES = ('ref', 'ref2', 'softmax', 'phase_jitter', 'phase_ramp', 'cca_diagnostics', 'cca_adapter', 'wearable_transfer')
NO_TRAINING, DETERMINISTIC = 'no training', 'deterministic fit'
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
EXPORT_NAME = {'u8': 'held8_accuracy', 'seen_ba': 'seen32_balanced_accuracy'}
ID_REASON = 'cannot_ask_unseen'
# The editorial decisions this audit holds the file to (plan section 2.1, the owner's defaults D6 and D9).
CARDS = ((1, 'reference-spectrum', ['ref']), (2, 'head-and-features', ['ref2', 'softmax']),
         (3, 'phase-jitter', ['phase_jitter']), (4, 'phase-ramp', ['phase_ramp']),
         (5, 'cca-mechanism', ['cca_diagnostics']), (6, 'cca-correction', ['cca_adapter']),
         (7, 'wearable-transfer', ['wearable_transfer']), (8, 'cross-spectral', []))
NAME_KEY = (
    ('question number', 'ID'), ('numeric code', 'NUM'), ('label template', 'TPL'), ('reference spectrum', 'REF'),
    ('reference with stimulus phase', 'REFc-0'), ('fixed spectrum match (no training)', 'TEMPLATE'),
    ('plain spectrum', 'L0'), ('complex spectrum', 'L0c'), ('frozen CBraMod features', 'L1'), ('FiLM head', 'FS'),
    ('matching head', 'MATCH'), ('CCA (no training)', 'CCA-RAW'), ('Hann-tapered CCA', 'CCA-HANN-C/U'),
    ('cropped-spectrum match (no training)',
     'SUBSPACE-CROP in the diagnostics export, CCA-CROP in the adapter export: one set of scores'),
    ('channel-energy average', 'CHANNEL-JOINT/HARMONIC'), ('shared ridge scorer', 'SHARED-RIDGE'),
    ('energy head', 'ENERGY-FS'), ('adapted head', 'ADAPT-FS'), ('CCA with learned correction', 'RAW-RESIDUAL'),
    ('cropped match with learned correction', 'CROP-RESIDUAL'),
    ('cropped-spectrum check (Wearable-102)', 'CCA-CROP in the Wearable export'))
RIGHTS_CARDS = {'beta': [1, 2, 3, 4, 5, 6, 7], 'wearable_102': [7], 'corrigendum': [2, 3], 'cbramod': [1]}
# Strings this audit does not derive: the modules' and the export's editorial wording, checked by them and their tests.
EDITORIAL = (
    ('title',), ('question',), ('metric_units',), ('scope',), ('placement',), ('thread', 'role'), ('cohort',),
    ('wearable',), ('endpoints',), ('name_key',), ('rights', 'datasets', 'beta', 'published_here'),
    ('rights', 'datasets', 'wearable_102', 'published_here'), ('rights', 'datasets', 'wearable_102', 'name'),
    ('rights', 'corrigendum', 'name'), ('rights', 'corrigendum', 'used_for'), ('rights', 'cbramod', 'name'),
    ('rights', 'cbramod', 'method_page'), ('rights', 'cbramod', 'used_for'))
EDITORIAL_IN_STUDY = ('limitations_keys', 'display_names', 'contrast_limitations', 'export_codes')
# Leaf names whose strings are the modules' wording inside the derived sections (every figure beside them is derived).
EDITORIAL_LEAVES = {'training', 'variant', 'name', 'role', 'label', 'same_definition_as', 'method', 'conditional_on',
                    'scale', 'instances_unit', 'arm', 'against', 'unit', 'averaged_over', 'denominator', 'metric',
                    'differs_in', 'item', 'export_codes', 'bundles', 'computed_on', 'amplitude', 'dataset'}
DERIVED_SECTIONS = ('design', 'interval_method', 'transitions', 'protection', 'cca_definition', 'not_run', 'levels',
                    'contrasts')


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
    for t in ptr.split('/')[1:] if ptr else []:
        t = t.replace('~1', '/').replace('~0', '~')
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    else:
        yield trail, value


def show(path):
    return '/'.join(map(str, path))


class Table:
    """What the served file must hold: figures (numbers, booleans, nulls) and the strings the sources give."""

    def __init__(self):
        self.figures, self.strings, self.sets = {}, {}, {}

    def unordered(self, path, rows):
        """A list whose order is the module's choice: compared as a multiset of rows."""
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
                check(same(self.figures[path][0], want) if want is not NULL else self.figures[path][0] is NULL,
                      f'{show(path)}: two expected values')
            self.figures[path] = (want, kind)


# ---------------------------------------------------------------------------- the sources
def sources(manifest):
    s = {'owner': doc(manifest['approval']['ownerDecisions']), 'readings': doc(manifest['planning']['readings'])}
    for k, r in manifest['published'].items():
        s[k] = doc(r)
    for k, r in manifest['credits'].items():
        s[k] = doc(r)
    for m, block in manifest['blocks'].items():
        for k, r in block['pins'].items():
            s[f'{m}:{k}'] = doc(r)
    return s


def level(t, path, estimate, lo, hi, unit, people, seeds, origin):
    check(lo <= estimate <= hi, f'{show(path)}: the source interval does not hold its point')
    t.put(path, {'estimate': estimate, 'interval': [lo, hi], 'unit': unit, 'people': people, 'seeds': seeds,
                 'origin': origin})


def contrast(t, path, levels, role, left, right, estimate, lo, hi, people, seeds, flags):
    check(abs(levels[left] - levels[right] - estimate) <= 1e-12, f'{show(path)}: not the difference of its levels')
    check(lo <= estimate <= hi, f'{show(path)}: the source interval does not hold its point')
    t.put(path, {'role': role, 'left': left, 'right': right, 'estimate': estimate, 'interval': [lo, hi],
                 'unit': DIFFERENCE, 'people': people, 'seeds': seeds, 'flags': flags})


def unit_of(endpoint):
    return DIFFERENCE if endpoint == 'cost' else PROPORTION


# ---------------------------------------------------------------------------- cards 1 and 2
def study_ref(t, s, src):
    P = ('studies', 'ref')
    run = src['results']['questions-in-language-ref']
    est = {}
    for block, feat in (('REF-ssvep-L0', 'L0'), ('REF-ssvep-L1', 'L1')):
        for name, lv in run['descriptive'][block]['levels'].items():
            arm, e = name.split(' ')
            lid = f'{arm}/{e}' if arm in ('CCA', 'TEMPLATE') else f'{feat}-FS-{arm}/{e}'
            check(lv['excluded_people'] == 0 and lv['unit'] == unit_of(e), f'REF {name}')
            if arm == 'CCA':
                check(lv['seeds'] == 1, 'REF: CCA has one seed in the source')    # declared edit: "no training"
            level(t, P + ('levels', lid), lv['estimate'], *lv['interval_95'], lv['unit'], lv['people'],
                  NO_TRAINING if arm == 'CCA' else lv['seeds'], lv['origin'])
            est[lid] = lv['estimate']
    labels = re.compile(r'^REF (?:- (\w+), (held-eight accuracy|seen-32 balanced accuracy)'
                        r'|held-eight - matched-seen-eight accuracy)$')
    draws, gates = set(), {}
    for part in ('primary', 'secondary'):
        for blk in run[part]['blocks']:
            feat = {'REF-ssvep-L0': 'L0', 'REF-ssvep-L1': 'L1'}[blk['block']]
            gates[feat] = blk['gates']
            for entry in blk['entries']:
                m = labels.match(entry['label'])
                check(m is not None, f'REF: unknown contrast label {entry["label"]!r}')
                if m.group(1):
                    e = 'u8' if m.group(2).startswith('held') else 'seen_ba'
                    left = f'{feat}-FS-REF/{e}'
                    right = f'CCA/{e}' if m.group(1) == 'CCA' else f'{feat}-FS-{m.group(1)}/{e}'
                else:
                    left, right = f'{feat}-FS-REF/u8', f'{feat}-FS-REF/m8'
                check(entry['excluded_people'] == 0 and entry['unit'] == DIFFERENCE, 'REF contrast')
                draws.add(entry['draws'])
                contrast(t, P + ('contrasts', f'{feat}/{entry["id"]}'), est, entry['role'], left, right,
                         entry['estimate'], *entry['interval_95'], entry['people'], entry['seeds'],
                         {k: entry[k] for k in ('difference', 'margin_pass', 'margin_rule')})
    head = {f: g['headroom']['interval'] for f, g in gates.items()}
    check(len({(h['seed'], h['level']) for h in head.values()}) == 1 and len(draws) == 1, 'REF: bootstrap')
    t.put(P + ('interval_method',), {'seed': head['L0']['seed'], 'draws': draws.pop(), 'level': head['L0']['level']})
    design = {('training_epochs' if k == 'epochs' else k): v for k, v in run['design'].items()}   # declared rename
    check('epochs' in run['design'] and 'training_epochs' not in run['design'], 'REF: the rename has no source')
    t.put(P + ('design',), design)
    a = run['audits']
    t.put(P + ('checks', 'audit'), {k: a[k] for k in ('status', 'release_eligible', 'main_models_reconstructed',
                                                      'canary_fits', 'fixed_independent_refits', 'argmax_exact')})
    t.put(P + ('checks', 'audit', 'numeric_metrics'),
          {k: a['numeric_metrics'][k] for k in ('status', 'components', 'contrasts', 'metric_atol', 'bootstrap_draws',
                                                 'all_draws_pairing_verified', 'template_reconstructed')})
    t.put(P + ('checks', 'headroom'), {f: g['headroom']['pass'] for f, g in gates.items()})
    t.put(P + ('checks', 'canary'), {f: g['ref_canary'] for f, g in gates.items()})
    t.put(P + ('checks', 'excluded_people'), max(lv['excluded_people'] for b in ('REF-ssvep-L0', 'REF-ssvep-L1')
                                                 for lv in run['descriptive'][b]['levels'].values()), 'derived')
    t.unordered(P + ('undefined',), [{'level': f'{f}-FS-ID/{e}', 'reason': ID_REASON} for f in ('L0', 'L1')
                               for e in ('u8', 'u3', 'cost')])
    # Two of REF's not-run items are what REF2 ran: the matching head and the fundamental-only reference.
    later = {'Matching/bilinear head': 'ref2', 'Fundamental-only reference ablation': 'ref2'}
    t.put(P + ('not_run',), [{'item': i, 'run_in': later.get(i)} for i in run['not_run']])
    return est


def study_ref2(t, s, src, protocol):
    P = ('studies', 'ref2')
    agg = src['aggregate']
    new_cells = {c['id'] for c in protocol['scope']['cells']}
    est, boots, cells = {}, set(), []
    for lid, lv in agg['levels'].items():
        cell, e = lid.split('/')
        cells.append(cell)
        boots.add((lv['draws'], lv['seed'], lv['level']))
        check(lv['excluded_people'] == 0, f'REF2 {lid}')
        origin = 'new' if cell in new_cells else ('reused_ref' if cell == 'L0-FS-REF' else 'reused_parent')
        if cell == 'CCA':
            check(lv['seeds'] == 1, 'REF2: CCA has one seed in the source')
        level(t, P + ('levels', lid), lv['point'], lv['lo'], lv['hi'], unit_of(e), lv['people'],
              NO_TRAINING if cell == 'CCA' else lv['seeds'], origin)
        est[lid] = lv['point']
    for cid, c in agg['contrasts'].items():
        boots.add((c['draws'], c['seed'], c['level']))
        contrast(t, P + ('contrasts', cid), est, c['role'], f'{c["left"]}/{c["metric"]}', f'{c["right"]}/{c["metric"]}',
                 c['point'], c['lo'], c['hi'], c['people'], c['seeds'],
                 {k: c[k] for k in ('difference', 'equivalent_within_2pp', 'noninferiority_to_CCA',
                                    'meaningful_head_gain')})
    check(len(boots) == 1, 'REF2: more than one bootstrap')
    draws, seed, lvl = boots.pop()
    t.put(P + ('interval_method',), {'seed': seed, 'draws': draws, 'level': lvl})
    a = src['audit']
    t.put(P + ('checks', 'audit'), {k: a[k] for k in ('status', 'release_eligible', 'main_models_reconstructed',
                                                      'canary_fits', 'fixed_independent_refits', 'argmax_exact')})
    t.put(P + ('checks', 'audit', 'numeric_metrics'),
          {k: a['numeric_metrics'][k] for k in ('status', 'components', 'contrasts', 'metric_atol', 'bootstrap_draws',
                                                 'all_draws_pairing_verified')})
    t.put(P + ('checks',), {'completion': src['completion']['status'], 'counts': src['counts'],
                            'headroom': {g: h['pass'] for g, h in agg['headroom'].items()}})
    t.put(P + ('checks', 'excluded_people'), max(lv['excluded_people'] for lv in agg['levels'].values()), 'derived')
    ids = [c for c in dict.fromkeys(cells) if c.endswith('-ID')]
    t.unordered(P + ('undefined',), [{'level': f'{c}/{e}', 'reason': ID_REASON} for c in ids for e in ('u8', 'u3', 'cost')])
    t.put(P + ('not_run',), [])
    return est


def study_softmax(t, s, src, parent):
    P = ('studies', 'softmax')
    agg = src['aggregate']
    est, boots = {}, set()
    for arm, lv in agg['levels'].items():
        boots.add((lv['draws'], lv['seed'], lv['level']))
        level(t, P + ('levels', f'L0-{arm}/seen_ba'), lv['point'], lv['lo'], lv['hi'], PROPORTION, lv['people'],
              lv['seeds'], 'new')
        est[f'L0-{arm}/seen_ba'] = lv['point']
    bsh = parent['results']['questions-in-language']['descriptive']['P-ssvep-L0']['levels']['B-sh seen_ba']
    level(t, P + ('levels', 'L0-BSH-BCE/seen_ba'), bsh['estimate'], *bsh['interval_95'], PROPORTION, bsh['people'],
          bsh['seeds'], 'reused_parent')
    est['L0-BSH-BCE/seen_ba'] = bsh['estimate']
    for part in ('primary', 'secondary'):
        c = agg[part]
        boots.add((c['draws'], c['seed'], c['level']))
        left, right = c['name'].split(' minus ')
        contrast(t, P + ('contrasts', c['name']), est, part, f'L0-{left}/seen_ba', f'L0-{right}/seen_ba', c['point'],
                 c['lo'], c['hi'], c['people'], c['seeds'],
                 {k: c[k] for k in ('equivalent_strict_2pp', 'equivalence_margin')})
    check(len(boots) == 1, 'softmax: more than one bootstrap')
    draws, seed, lvl = boots.pop()
    t.put(P + ('interval_method',), {'seed': seed, 'draws': draws, 'level': lvl})
    a = src['audit']
    t.put(P + ('checks',), {'audit': {k: a[k] for k in ('status', 'metrics', 'reconstructions', 'independent_refits')},
                            'completion': src['completion']['status'], 'counts': src['counts']})
    t.unordered(P + ('undefined',), [{'level': f'{lid.split("/")[0]}/u8', 'reason': ID_REASON} for lid in est])
    t.put(P + ('not_run',), [])


# ---------------------------------------------------------------------------- cards 3 and 4
LATER = {'Same augmentation on FS-NUM': 'phase_ramp', 'MATCH head follow-up': 'phase_ramp',
         'CCA-derived features or residuals': 'cca_adapter'}


def study_jitter(t, s, src, score, protocol, audit, canary, bridge, interp, prov, release):
    P = ('studies', 'phase_jitter')
    check('one_period_prediction' in src and 'release_governed_by' in src, 'jitter: the dropped fields have no source')
    est, cell_of, boots = {}, {}, set()
    design_arms = []
    proto_arms = {a['id']: a for a in protocol['arms']}
    for arm in src['arms']:
        cell = arm['name'].split(' ')[0]
        cell_of[arm['id']] = cell
        for e, m in arm['metrics'].items():
            boots.add((m['draws'], m['seed'], m['level']))
            check(same(score['levels'][f'{arm["id"]}/{e}'], m), f'jitter {cell}/{e}: not the canonical score')
            origin = 'new' if not arm['historical_reuse'] else ('reused_ref2' if cell.startswith('L0c-') else 'reused_ref')
            level(t, P + ('levels', f'{cell}/{e}'), m['point'], m['lo'], m['hi'], PROPORTION, m['people'], m['seeds'],
                  origin)
            est[f'{cell}/{e}'] = m['point']
        if arm['id'] in proto_arms:
            pa = proto_arms[arm['id']]
            delay = {'training_delay_seconds': pa['tau_seconds'],
                     'delay_uses_training_label': pa['uses_training_labels_for_augmentation']}
            features, head, query = 'L0c', 'FS', 'REFc-0'          # the protocol's builder: arm="REFc-0", head_kind="FS"
            check('arm="REFc-0"' in protocol['model']['builder'] and 'head_kind="FS"' in protocol['model']['builder']
                  and protocol['historical_control']['cell'] == 'L0c-FS-REFc-0', 'jitter: the delay arms')
        else:
            delay = {'training_delay_seconds': None, 'delay_uses_training_label': None}
            features, head, query = re.fullmatch(r'(L0c?)-(FS)-(REFc-0|REF)', cell).groups()
        design_arms.append({'arm': arm['id'], 'cell': cell, 'features': features, 'head': head, 'query': query,
                            'historical_reuse': arm['historical_reuse']} | delay)
    check(same(src['contrasts'], score['contrasts']), 'jitter: the export contrasts are not the canonical score')
    for cid, c in src['contrasts'].items():
        boots.add((c['draws'], c['seed'], c['level']))
        flags = {'role_as_stated': c['role']}
        if cid == 'P1':
            flags |= {'positive_primary': score['positive_primary'], 'meaningful_primary': score['meaningful_primary']}
        contrast(t, P + ('contrasts', cid), est, 'primary' if c['role'] == 'single primary' else 'secondary',
                 f'{cell_of[c["left"]]}/{c["metric"]}', f'{cell_of[c["right"]]}/{c["metric"]}', c['point'], c['lo'],
                 c['hi'], c['people'], c['seeds'], flags)
    check(len(boots) == 1, 'jitter: more than one bootstrap')
    draws, seed, lvl = boots.pop()
    check(protocol['statistics']['bootstrap']['seed'] == seed, 'jitter: the protocol seed')
    t.put(P + ('interval_method',), {'draws': draws, 'seed': seed, 'level': lvl})
    aug = protocol['augmentation']
    t.put(P + ('design',), {'dataset': src['dataset'], 'model': src['model'], 'endpoints': src['metrics'],
                            'arms': design_arms, 'delay': {k: aug[k] for k in ('formula', 'draw', 'queries', 'inference')}})
    ns = audit['numerical_summary']
    t.put(P + ('checks', 'audit'), {k: audit[k] for k in (
        'status', 'release_eligible', 'main_models_reconstructed', 'canary_models_reconstructed',
        'fixed_independent_refits', 'baseline_bridge_fits', 'total_optimizer_invocations', 'argmax_exact',
        'metric_bootstrap_atol')})
    t.put(P + ('checks', 'audit', 'numerical_summary'), {'status': ns['status'], 'bootstrap_draws': ns['bootstrap_draws']})
    t.put(P + ('checks', 'audit', 'numerical_summary', 'contrasts'), len(ns['contrast_ids']), 'derived')
    t.put(P + ('checks', 'randomized_label'), {'status': canary['status'], 'fits': canary['observed_fits']})
    t.put(P + ('checks', 'randomized_label'), {'cells': len(canary['cells']), 'cells_passed': sum(
        c['includes_zero'] is True for c in canary['cells'].values())}, 'derived')
    t.put(P + ('checks', 'bridge'), {'status': bridge['status'], 'fits': bridge['bridge_fits']})
    t.put(P + ('checks', 'reviews'), {'scientific': interp['status'], 'provenance': prov['status']})
    t.put(P + ('checks', 'release'), {'status': release['status'], 'release_eligible': release['release_eligible']})
    t.put(P + ('checks', 'export_equals_canonical_score'),
          all(same(score['levels'][f'{a["id"]}/{e}'], m) for a in src['arms'] for e, m in a['metrics'].items()),
          'derived')
    t.put(P + ('caveats',), src['caveats'])
    t.put(P + ('intervals',), src['intervals'])
    t.unordered(P + ('undefined',), [])
    t.put(P + ('not_run',), [{'item': i, 'run_in': LATER.get(i)} for i in protocol['deferred']])
    return est


def study_ramp(t, s, score, protocol, audit, canary, interp, prov, release, ref_src, jitter_protocol):
    P = ('studies', 'phase_ramp')
    for k in ('status', 'fifty_five_reference', 'interpretation'):
        check(k in score, f'ramp: the dropped field {k} has no source')
    ref_origin = {}
    for name, lv in ref_src['results']['questions-in-language-ref']['descriptive']['REF-ssvep-L0']['levels'].items():
        arm, e = name.split(' ')
        ref_origin[f'{arm}/{e}' if arm in ('CCA', 'TEMPLATE') else f'L0-FS-{arm}/{e}'] = lv['origin']
    new_cells = [c['id'] for c in protocol['cells']]
    est, boots = {}, set()
    for lid, lv in score['levels'].items():
        cell, e = lid.split('/')
        boots.add((lv['draws'], lv['seed'], lv['level']))
        if cell in new_cells:
            origin = 'new'
        elif cell.startswith('L0c-'):
            origin = 'reused_ref2'
        else:
            origin = {'new': 'reused_ref', 'reused_parent': 'reused_parent'}[ref_origin[lid]]
        if cell == 'CCA':
            check(lv['seeds'] == 1, 'ramp: CCA has one seed in the source')
        level(t, P + ('levels', lid), lv['point'], lv['lo'], lv['hi'], unit_of(e), lv['people'],
              NO_TRAINING if cell == 'CCA' else lv['seeds'], origin)
        est[lid] = lv['point']
    for cid, c in score['contrasts'].items():
        boots.add((c['draws'], c['seed'], c['level']))
        contrast(t, P + ('contrasts', cid), est, c['role'], f'{c["left"]}/{c["metric"]}', f'{c["right"]}/{c["metric"]}',
                 c['point'], c['lo'], c['hi'], c['people'], c['seeds'],
                 {k: c[k] for k in ('difference', 'equivalent_within_2pp', 'noninferiority_to_CCA')})
    check(len(boots) == 1, 'ramp: more than one bootstrap')
    draws, seed, lvl = boots.pop()
    check(protocol['analysis']['bootstrap']['seed'] == seed, 'ramp: the protocol seed')
    t.put(P + ('interval_method',), {'draws': draws, 'seed': seed, 'level': lvl})
    ds, split, an = protocol['dataset'], protocol['split'], protocol['analysis']
    ends = {}
    for e in ('u8', 'seen_ba'):
        n = int(re.search(r'chance1/(\d+)', an['endpoints'][e]).group(1))
        ends[e] = {'candidate_count': n, 'chance': 1 / n}
    n = int(re.search(r'same(\d+)frequencies', an['endpoints']['m8']).group(1))
    ends['m8'] = {'candidate_count': n, 'chance': 1 / n}
    rule = protocol['augmentation']['rule']
    tau = re.search(r'tau=([\w/]+)', rule).group(1)
    aug = protocol['augmentation']
    t.put(P + ('design',), {
        'dataset': {'name': ds['name'], 'people': ds['people'], 'targets': ds['targets'], 'windows': ds['windows'],
                    'person_folds': split['people_folds']},
        'cells': [{'cell': c['id'], 'features': c['level'], 'head': c['head'], 'query': c['arm'],
                   'parameters': c['parameters']['total'], 'control': c['historical_id'],
                   'augmentation': c['augmentation']} for c in protocol['cells']],
        'comparators': an['comparators'],
        'delay': {'training_delay_seconds': tau} | {k: aug[k] for k in ('formula', 'draw', 'queries', 'inference')}})
    t.put(P + ('design', 'dataset'), {'frequency_rotations': len(split['rotations']),
                                      'training_seeds': len(split['seeds'])}, 'derived')
    t.put(P + ('design', 'endpoints'), ends, 'derived')
    t.put(P + ('design', 'delay', 'delay_uses_training_label'), 'f_assigned_source_label' in tau, 'derived')
    ns = audit['numerical_summary']
    t.put(P + ('checks', 'audit'), {k: audit[k] for k in (
        'status', 'release_eligible', 'main_models_reconstructed', 'canary_models_reconstructed',
        'fixed_independent_refits', 'baseline_bridge_fits', 'total_optimizer_invocations', 'argmax_exact',
        'metric_bootstrap_atol')})
    t.put(P + ('checks', 'audit', 'numerical_summary'), {'status': ns['status'], 'bootstrap_draws': ns['bootstrap_draws']})
    t.put(P + ('checks', 'audit', 'numerical_summary', 'contrasts'), len(ns['contrast_ids']), 'derived')
    t.put(P + ('checks', 'randomized_label'), {'status': canary['status'], 'fits': canary['observed_fits']})
    t.put(P + ('checks', 'randomized_label'), {'cells': len(canary['cells']), 'cells_passed': sum(
        c['includes_zero'] is True for c in canary['cells'].values())}, 'derived')
    bg = prov['final_verification']['bridge_gate']
    t.put(P + ('checks', 'bridge'), {'status': 'pass' if bg['pass'] is True else 'fail', 'fits': bg['fits']})
    t.put(P + ('checks', 'reviews'), {'scientific': interp['status'], 'provenance': prov['status']})
    t.put(P + ('checks', 'release'), {'status': release['status'], 'release_eligible': release['release_eligible']})
    t.put(P + ('checks', 'excluded_people'), max(lv.get('excluded_people', 0) for lv in score['levels'].values()),
          'derived')
    t.put(P + ('multiplicity',), score['multiplicity'])
    t.put(P + ('undefined_metrics',), score['undefined_metrics'])
    t.unordered(P + ('undefined',), [{'level': f'{c}/{e}', 'reason': ID_REASON} for c, es in score['undefined_metrics'].items()
                               for e in es])
    t.put(P + ('not_run',), [{'item': i, 'run_in': LATER.get(i)} for i in protocol['deferred']])
    # The bet as the thread states it: "unseen clears <n>", over the plain post URL.
    m = re.search(r'\bunseen clears (\d+)\b', protocol['source_evidence']['comment_quote'])
    t.put(P + ('thread_bet',), {'held8_threshold': int(m.group(1)) / 100,
                                'source_url': jitter_protocol['comment']['url'].split('#', 1)[0]}, 'derived')
    return est


# ---------------------------------------------------------------------------- cards 5 to 7
def study_diagnostics(t, s, ex, protocol, review, hv, handoff_review):
    P = ('studies', 'cca_diagnostics')
    sm = ex['summary']
    arms = list(protocol['arms'])
    people = sm['person_count']
    est = {}
    for code in arms:
        for e, name in EXPORT_NAME.items():
            m = sm['arms'][code][name]
            level(t, P + ('levels', f'{code}/{e}'), m['mean'], *m['ci95'], PROPORTION, people,
                  DETERMINISTIC if code == 'SHARED-RIDGE' else NO_TRAINING, 'new')
            est[f'{code}/{e}'] = m['mean']
    for left, right in protocol['metrics']['contrasts']:
        key = f'{left} minus {right}'
        pair = [sm['contrasts'][key][name] for name in EXPORT_NAME.values()]
        identical = all(m['mean'] == 0.0 and m['ci95'] == [0.0, 0.0] for m in pair)
        for e, name in EXPORT_NAME.items():
            m = sm['contrasts'][key][name]
            flags = {'interval_includes_zero': m['ci95'][0] <= 0 <= m['ci95'][1]}
            if identical:
                check(est[f'{left}/{e}'] == est[f'{right}/{e}'], f'diagnostics {key}: zero, yet the levels differ')
                flags['identical_results'] = True
            contrast(t, P + ('contrasts', f'{key}/{e}'), est, 'prespecified', f'{left}/{e}', f'{right}/{e}', m['mean'],
                     *m['ci95'], people, DETERMINISTIC if 'SHARED-RIDGE' in (left, right) else NO_TRAINING, flags)
    t.put(P + ('interval_method',), {'draws': sm['bootstrap_n'], 'seed': sm['bootstrap_seed'],
                                     'level': int(re.search(r'percentile(\d+)CI', protocol['metrics']['bootstrap'])
                                                  .group(1)) / 100})
    split = protocol['split']
    rotations = split['rotations']
    targets = len({f for r in rotations.values() for f in r})
    chance = sm['random_pairing']['exact_expectation']
    held = {len(r) for r in rotations.values()}.pop()
    t.put(P + ('design',), {
        'dataset': {'people': people, 'targets': targets, 'windows': protocol['shape'][0], 'person_folds': split['folds'],
                    'frequency_rotations': sm['rotations']},
        'endpoints': {'u8': {'candidate_count': held, 'chance': chance[EXPORT_NAME['u8']]},
                      'seen_ba': {'candidate_count': split['source_queries_per_fit'],
                                  'chance': chance[EXPORT_NAME['seen_ba']]}},
        'harmonics': len(protocol['harmonics']), 'training_free_scorers': len(arms) - 1, 'ridge_fits': split['ridge_fits'],
        'scorers': [{'code': c} if c != 'SHARED-RIDGE' else {'code': c, 'fits': split['ridge_fits'],
                                                     'source_windows_per_fit': split['source_rows_per_fit'],
                                                     'seen_frequencies_per_fit': split['source_queries_per_fit']}
                    for c in arms]}, 'derived')
    audit, gates, rp = ex['audit'], ex['gates'], sm['random_pairing']
    analytic = audit['analytic']['arms']
    ranks = gates['preflight']['reference_ranks']
    rr = gates['raw-reconstruction']
    l0c = gates['l0c-equivalence']
    t.put(P + ('checks',), {
        'release_review': {'accepted': review['accepted'], 'blockers': len(review['blockers'])},
        'handoff_review': {'accepted': handoff_review['accepted'], 'blockers': len(handoff_review['blockers'])},
        'independent_hash_verification': {'passed': hv['passed'], 'artifact_receipts': hv['verified_artifact_receipts'],
                                          'sealed_artifacts': hv['verified_sealed_artifacts']},
        'raw_cca_reconstruction': {'passed': rr['passed'], 'windows': protocol['shape'][0],
                                   'max_absolute_error': rr['max_absolute_error'],
                                   'identical_argmax_sets': len(rr['identical_argmax'])},
        'cropped_coordinates_match_earlier_cache': {'passed': l0c['passed'], 'rows_checked': len(l0c['rows']),
                                                    'coordinate_max_error': l0c['coordinate_max_error'],
                                                    'score_max_error': l0c['cca_max_error']},
        'independent_analytic_spot_check': {'passed': audit['analytic']['passed'],
                                            'rows_checked': len(audit['analytic']['rows']),
                                            'scorers_checked': len([k for k in analytic if k in arms]),
                                            'max_absolute_error': max(v['max_absolute_error'] for v in analytic.values())},
        'independent_ridge_refits': {'passed': audit['all_ridge_argmax_equal'], 'refits': audit['ridge_refits'],
                                     'of': split['ridge_fits'], 'max_score_error': audit['ridge_max_score_error']},
        'person_metrics_bootstraps_and_contrasts_recomputed': {
            'passed': audit['all_person_metrics_match'] and audit['all_aggregate_bootstraps_and_contrasts_match']},
        'reference_subspace_preflight': {'passed': gates['preflight']['passed'], 'tests': gates['preflight']['tests'],
                                         'reference_subspace_dimension': {r for v in ranks.values() for r in v}.pop(),
                                         'candidates': {len(v) for v in ranks.values()}.pop(), 'domains': len(ranks)},
        'random_pairing': {'descriptive_only': rp['descriptive_only'], 'permutations': rp['permutations'],
                           'seed': rp['seed'],
                           'exact_expectation': {e: chance[n] for e, n in EXPORT_NAME.items()},
                           'means': {c: {e: rp['arms'][c][n]['mean'] for e, n in EXPORT_NAME.items()} for c in arms}},
    }, 'derived')
    t.unordered(P + ('undefined',), [])
    t.put(P + ('not_run',), [{'run_in': None}])
    return est, {'people': people, 'targets': targets, 'windows': protocol['shape'][0], 'folds': split['folds'],
                 'rotations': sm['rotations'], 'held': held, 'seen': split['source_queries_per_fit'],
                 'chance': chance, 'scorers': len(arms) - 1, 'ridge_fits': split['ridge_fits']}


def numeric_pairs(a, b, trail=''):
    """(pointer, a, b) for every number of a at the same place in b."""
    if isinstance(a, dict):
        for k, v in a.items():
            yield from numeric_pairs(v, b[k], f'{trail}/{k}')
    elif isinstance(a, list):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from numeric_pairs(x, y, f'{trail}/{i}')
    elif is_number(a):
        yield trail, a, b


def study_adapter(t, s, ex, protocol, nr, ir, rs, binding, diag_est, diag_ex):
    P = ('studies', 'cca_adapter')
    trained, baselines = list(protocol['arms']), list(protocol['baselines'])
    seeds = len(protocol['split']['seeds'])
    people = ex['n_people']
    est = {}
    twin = {'CCA-RAW': 'CCA-RAW', 'CCA-CROP': 'SUBSPACE-CROP'}
    for code in ex['arms']:
        for e, name in EXPORT_NAME.items():
            m = ex['arms'][code][name]
            if code in baselines:     # the diagnostics' own scores, bit for bit
                dm = diag_ex['summary']['arms'][twin[code]][name]
                check(m == dm, f'adapter {code}/{e}: not the diagnostics {twin[code]} scores')
            level(t, P + ('levels', f'{code}/{e}'), m['mean'], *m['ci95'], PROPORTION, people,
                  NO_TRAINING if code in baselines else seeds, 'reused_cca_diagnostics' if code in baselines else 'new')
            est[f'{code}/{e}'] = m['mean']
    corr = re.search(r'(\w+) descending canonical correlations', protocol['features']['z']).group(1)
    words = {'Six': 6, 'Five': 5, 'Four': 4, 'Three': 3, 'Two': 2}
    for c in ex['contrasts']:
        left, right = c['left'], c['right']
        for e, name in EXPORT_NAME.items():
            m = c['metrics'][name]
            flags = {'interval_includes_zero': m['ci95'][0] <= 0 <= m['ci95'][1]}
            if (left, right) == ('ADAPT-FS', 'ENERGY-FS'):
                flags['added_input'] = {'canonical_correlations': words[corr]}
            contrast(t, P + ('contrasts', f'{left} minus {right}/{e}'), est, 'prespecified', f'{left}/{e}', f'{right}/{e}',
                     m['mean'], *m['ci95'], people, seeds if left in trained or right in trained else NO_TRAINING, flags)
    rec = nr['checks']['independent_numerical_recomputation']
    t.put(P + ('interval_method',), {'draws': ex['resamples'], 'seed': rec['bootstrap_seed']})
    t.put(P + ('interval_method', 'level'), 0.95 if 'np.percentile(samples, [2.5, 97.5])' in s['cca:adapter_runner']
          else None, 'derived')
    rd = ex['residual_diagnostics']['RAW-RESIDUAL']
    names = {'wrong_to_right': 'wrong_to_correct', 'right_to_wrong': 'correct_to_wrong',
             'wrong_to_different_wrong': 'changed_wrong_to_wrong', 'unchanged_right': 'unchanged_correct',
             'unchanged_wrong': 'unchanged_incorrect', 'changed': 'changed'}
    for e, name in EXPORT_NAME.items():
        t.put(P + ('transitions', e), {k: rd[name][v] for k, v in names.items()})
    margins = {rd[n]['protected_margin'] for n in EXPORT_NAME.values()}
    check(len(margins) == 1, 'adapter: more than one protected margin')
    t.put(P + ('protection',), {'protected_margin': margins.pop(),
                                'protected_instances': {e: rd[n]['protected_trials'] for e, n in EXPORT_NAME.items()}})
    t.put(P + ('protection', 'protected_flips'), max(rd[n]['protected_flips'] for n in EXPORT_NAME.values()), 'derived')
    split, model, training = protocol['split'], protocol['model'], protocol['training']
    params = int(re.search(r'ENERGY/ADAPT have(\d+)parameters', model['adapter']).group(1))
    resid = int(re.search(r'residual arm adds one global-bias scalar \((\d+)\)', model['adapter']).group(1))
    t.put(P + ('design',), {
        'dataset': {'people': diag_est['people'], 'targets': diag_est['targets'], 'windows': diag_est['windows'],
                    'person_folds': split['folds'], 'frequency_rotations': len(split['rotations']),
                    'training_seeds': seeds},
        'endpoints': {'u8': {'candidate_count': diag_est['held'], 'chance': diag_est['chance'][EXPORT_NAME['u8']]},
                      'seen_ba': {'candidate_count': split['source_queries_per_fit'],
                                  'chance': diag_est['chance'][EXPORT_NAME['seen_ba']]}},
        'arms': [{'code': c, 'fits': split['fits_per_arm'], 'parameters': resid if c.endswith('RESIDUAL') else params}
                 for c in trained] + [{'code': c} for c in baselines],
        'trained_fits': split['total_main_fits'], 'training_epochs': training['epochs'],
        'steps_per_fit': training['steps_per_fit']}, 'derived')
    ct, ai, fa = (nr['checks'][k] for k in ('complete_training', 'artifact_integrity', 'features_and_admission'))
    pairs = list(numeric_pairs(nr['aggregate_findings'], ex))
    t.put(P + ('checks',), {
        'numerical_review': {'passed': nr['passed'], 'blockers': len(nr['remaining_blockers'])},
        'interpretation_review': {'passed': ir['passed'], 'blockers': len(ir['remaining_blockers'])},
        'release_receipt': {'complete': rs['status'] == 'audited_complete_aggregate_handoff_ready',
                            'incomplete_arms': len(rs['incomplete_arms'])},
        'binding_review': {'cleared': 'Safe, with five required copy fixes' in binding and t.adapter_sha in binding},
        'export_equals_numerical_review': {'passed': max(abs(a - b) for _, a, b in pairs) <= 1e-12,
                                           'numeric_values': len(pairs),
                                           'max_absolute_difference': max(abs(a - b) for _, a, b in pairs),
                                           'tolerance': 1e-12},
        'complete_training': {'passed': ct['passed'], 'fits': ct['main_fits'], 'independent_refits': ct['independent_refits'],
                              'independent_refits_exact': ct['independent_refit_models_exact'],
                              'reconstructions': ct['functional_reconstruction_gates'],
                              'reconstruction_max_logit_error': ct['functional_reconstruction_max_logit_error']},
        'artifact_integrity': {'passed': ai['passed'], 'receipt_targets_rehashed': ai['receipt_targets_rehashed'],
                               'seal_entries': ai['seal_inventory_entries']},
        'analytic_inputs': {'passed': fa['passed'], 'source_scaler_checks': fa['fresh_source_split_and_scaler_checks'],
                            'rows_checked': fa['independent_feature_spotcheck_rows']},
        'independent_recomputation': {'passed': rec['passed'], 'max_metric_error': rec['max_private_metric_absolute_error'],
                                      'outcomes_exhaustive': rec['five_outcomes_exclusive_and_exhaustive'],
                                      'net_equals_gain': rec['rescue_minus_harm_equals_accuracy_delta']},
        'same_scores_as_diagnostics': {'passed': all(ex['arms'][c] == diag_ex['summary']['arms'][twin[c]]
                                                     for c in baselines), 'codes': sorted(baselines)},
    }, 'derived')
    t.unordered(P + ('undefined',), [{'contrast': 'ADAPT-FS minus CCA-RAW', 'reason': 'not_a_planned_contrast'}])
    check(not any({c['left'], c['right']} == {'ADAPT-FS', 'CCA-RAW'} for c in ex['contrasts']),
          'adapter: the adapted head against CCA alone has a contrast')
    t.put(P + ('not_run',), [{'run_in': None}] * 4)
    return est


def study_wearable(t, s, ex, protocol, ns, ir, rs, note, dvw, adapter_protocol):
    P = ('studies', 'wearable_transfer')
    src = protocol['source']
    seeds = len(src['seeds'])
    people = ex['n_target_people']
    ci = 'paired_person_bootstrap_percentile_95ci'
    est = {}
    strata = ex['primary_strata'] + ex['secondary_strata']
    for code in ('RAW-RESIDUAL', 'CCA-RAW', 'CCA-CROP'):
        for st in strata:
            m = ex['strata'][st]['metrics'][code]
            check(ex['strata'][st]['n_people'] == people, f'Wearable-102 {st}: people')
            level(t, P + ('levels', f'{code}/{st}'), m['mean'], *m[ci], PROPORTION, people,
                  seeds if code == 'RAW-RESIDUAL' else NO_TRAINING, 'new')
            est[f'{code}/{st}'] = m['mean']
    key = ex['primary_contrast']
    left, right = key.split('_minus_')
    for st in strata:
        m = ex['strata'][st]['metrics'][key]
        contrast(t, P + ('contrasts', f'{key}/{st}'), est, 'primary' if st in ex['primary_strata'] else 'secondary',
                 f'{left}/{st}', f'{right}/{st}', m['mean'], *m[ci], people, seeds,
                 {'interval_includes_zero': m[ci][0] <= 0 <= m[ci][1]})
    b = ex['bootstrap']
    t.put(P + ('interval_method',), {'draws': b['replicates'], 'seed': b['seed']})
    t.put(P + ('interval_method', 'level'), int(re.search(r'percentile(\d+)%', b['interval']).group(1)) / 100, 'derived')
    inp = protocol['input']
    freqs = inp['frequencies']
    m3, m4 = note['definitions']['transfer_matched_cca'], note['definitions']['dry_vs_wet_cca']
    t.put(P + ('design',), {
        'dataset': {'people': inp['subjects'], 'targets': ex['n_candidates'], 'frequency_range_hz': [min(freqs), max(freqs)],
                    'windows': ex['n_target_trials'], 'windows_per_sensor': ex['strata']['dry']['n_trials'],
                    'channels': len(inp['model_channel_names']), 'window_s': inp['epoch_relative_stimulus_s']},
        'source_models': {'models': src['models'], 'person_folds': len(src['folds']),
                          'frequency_rotations': len(src['rotations']), 'training_seeds': seeds,
                          'parameters_per_model': src['parameters_per_model'],
                          'window_s': src['source_epoch_relative_stimulus_s'], 'retraining': not ex['no_retraining'],
                          'ensemble': not ex['no_ensemble']},
        'endpoints': {st: {'candidate_count': ex['n_candidates'], 'chance': ex['chance'],
                           'windows': ex['strata'][st]['n_trials']} for st in strata},
        'methods': [{'code': left}, {'code': m3['export_key'], 'harmonics': len(m3['harmonics'])},
                    {'code': ex['secondary_comparator']}]}, 'derived')
    t.put(P + ('design', 'dataset', 'sensors'), [inp['sensors'][k] for k in sorted(inp['sensors'])])
    rows = {r['id']: (i, r) for i, r in enumerate(dvw['rows'])}
    dry, wet = rows['wearable-sensor-transfer-006'][1], rows['wearable-sensor-transfer-005'][1]
    method = re.search(r'([\d,]+) draws, seed (\d+), percentile', note['numbers'][2]['interval_method'])
    t.put(P + ('cca_definition',), {
        'matched_cca': {'code': m3['export_key'], 'harmonics': len(m3['harmonics']),
                        'reference_columns': m3['reference_columns'],
                        'same_as_model_term': 'matched CCA is the CCA built into the models'
                                              in m3['same_as_model_term']},
        'dry_vs_wet_cca': {'harmonics': len(m4['harmonics']), 'reference_columns': m4['reference_columns'],
                           'release_id': dvw['release_id'],
                           'equals_accuracy_here': 'balanced accuracy equals accuracy' in note['differences']['metric']['effect'],
                           'dry': {'row_id': dry['id'], 'estimate': dry['value'], 'interval': dry['confidence_interval_95']},
                           'wet': {'row_id': wet['id'], 'estimate': wet['value'], 'interval': wet['confidence_interval_95']},
                           'interval_method': {'draws': int(method.group(1).replace(',', '')),
                                               'seed': int(method.group(2)), 'level': 0.95}},
        'same_windows': note['differences']['windows']['difference'] == 'none',
        'windows_per_sensor': ex['strata']['dry']['n_trials'],
        'fact': note['card7']['a2_fact_for_plan_template'],
    }, 'derived')
    rec, prec = ns['reconstruction'], ex['precision_diagnostic_counts']
    t.put(P + ('checks',), {
        'numerical_summary': {'passed': ns['status'] == 'passed', 'models_reconstructed': rec['model_count'],
                              'windows_per_model': rec['rows_per_model'], 'argmax_mismatches': rec['argmax_mismatches'],
                              'max_absolute_error': rec['maximum_absolute_error'],
                              'metrics_max_discrepancy': ns['numerical']['maximum_absolute_metrics_discrepancy'],
                              'rows_checked': rec['feature_rows']},
        'interpretation_review': {'approved': ir['status'] == 'approved', 'blocking_findings': len(ir['blocking_findings'])},
        'release_receipt': {'complete': rs['status'] == 'audited_complete_aggregate_handoff_ready',
                            'model_inferences': rs['completed_model_inferences'],
                            'reconstructions': rs['completed_all_trial_reconstructions']},
        'cca_float64_against_float32': {'argmax_mismatches': {st: prec[st]['cca_float64_vs_float32_argmax_mismatches']
                                                              for st in strata}},
        'cca_definition_note': {'passed': note['verification']['synthetic_check']['passed'],
                                'three_harmonic_code_agreement_max_difference': note['verification']['synthetic_check'][
                                    'results']['transfer_code_vs_dry_vs_wet_code_at_three_harmonics_max_abs_diff']},
    }, 'derived')
    t.unordered(P + ('undefined',), [])
    t.put(P + ('not_run',), [{'run_in': None}] * 3)
    check(src['seeds'] == adapter_protocol['split']['seeds'] and src['arm'] == 'RAW-RESIDUAL',
          'Wearable-102: the source models are not the adapter fits')
    return est, {'people': people, 'targets': ex['n_candidates'], 'freqs': [min(freqs), max(freqs)],
                 'windows': ex['n_target_trials'], 'per_sensor': ex['strata']['dry']['n_trials'],
                 'span': inp['epoch_relative_stimulus_s'], 'models': src['models'], 'retraining': not ex['no_retraining'],
                 'harmonics': len(m3['harmonics']), 'chance': ex['chance']}


# ---------------------------------------------------------------------------- what spans the studies
def spanning(t, s, manifest, ref_src, diag, wear):
    ref_design = ref_src['results']['questions-in-language-ref']['design']
    ramp = s['phase:ramp_protocol']
    for a, b, label in ((ref_design['people'], diag['people'], 'people'), (ramp['dataset']['people'], diag['people'], 'people'),
                        (ref_design['trials'], diag['windows'], 'windows'), (ramp['dataset']['windows'], diag['windows'], 'windows'),
                        (ref_design['participant_folds'], diag['folds'], 'folds'),
                        (ramp['split']['people_folds'], diag['folds'], 'folds'),
                        (ref_design['frequency_rotations'], diag['rotations'], 'rotations'),
                        (ref_design['source_frequencies_per_rotation'], diag['seen'], 'seen'),
                        (ref_design['held_frequencies_per_rotation'], diag['held'], 'held'),
                        (len(ref_design['fit_seeds']), len(ramp['split']['seeds']), 'seeds'),
                        (ramp['dataset']['targets'], diag['targets'], 'targets')):
        check(a == b, f'the cohort: two sources state {label} as {a} and {b}')
    t.put(('cohort',), {'cards': [1, 2, 3, 4, 5, 6], 'people': diag['people'], 'targets': diag['targets'],
                        'windows': diag['windows'], 'window_seconds': ref_design['window_seconds'],
                        'person_folds': diag['folds'], 'frequency_rotations': diag['rotations'],
                        'seen_frequencies': diag['seen'], 'held_out_frequencies': diag['held'],
                        'training_seeds': len(ramp['split']['seeds']),
                        'card5': {'training_free_scorers': diag['scorers'], 'ridge_fits': diag['ridge_fits']}}, 'derived')
    span = wear['span'][1] - wear['span'][0]
    check(abs(span - round(span)) < 1e-9, 'Wearable-102: the window')
    t.put(('wearable',), {'cards': [7], 'people': wear['people'], 'targets': wear['targets'],
                          'frequency_range_hz': wear['freqs'], 'windows_per_sensor': wear['per_sensor'],
                          'windows': wear['windows'], 'window_seconds': round(span), 'source_models': wear['models'],
                          'retraining': wear['retraining'], 'matched_cca_harmonics': wear['harmonics']}, 'derived')
    an = ramp['analysis']['endpoints']
    k8, k32 = (int(re.search(r'chance1/(\d+)', an[e]).group(1)) for e in ('u8', 'seen_ba'))
    tracks = [x for x in s['coreMatrix']['tracks'] if x['id'] in ('beta-8ch', 'beta-4ch')]
    check(len({x['chanceLevel'] for x in tracks}) == 1, 'the core BETA chance level')
    t.put(('endpoints',), [
        {'candidates': k8, 'chance': 1 / k8, 'cards': [1, 2, 3, 4, 5, 6]},
        {'candidates': k32, 'chance': 1 / k32, 'cards': [1, 2, 3, 4, 5, 6]},
        {'candidates': diag['targets'], 'chance': tracks[0]['chanceLevel'] / 100, 'cards': [], 'separate_page': True},
        {'candidates': wear['targets'], 'chance': wear['chance'], 'cards': [7]},
        {'candidates': None, 'chance': None, 'cards': [], 'defined': False}], 'derived')
    t.put(('endpoints', 2, 'pages'), [f'/protocols/{x["id"]}/' for x in tracks])
    t.put(('placement',), {'leaderboard': False, 'new_dataset_count': 0, 'new_model_count': 0,
                           'cards': [{'card': c, 'anchor': a, 'studies': st} | ({} if st else {'status_only': True})
                                     for c, a, st in CARDS]}, 'editorial')
    t.put(('thread',), {'url': s['phase:jitter_protocol']['comment']['url'].split('#', 1)[0], 'commenter_named': False},
          'editorial')
    t.put(('name_key',), [{'site_name': n, 'export_codes': x, 'in_page_key': True} for n, x in NAME_KEY], 'editorial')
    t.put(('cohort',), {'dataset': ramp['dataset']['name'], 'same_cohort_as': s['route3']['release_id']})
    for key, cards in RIGHTS_CARDS.items():
        t.put(('rights',) + (('datasets', key) if key in ('beta', 'wearable_102') else (key,)) + ('cards',), cards,
              'editorial')


def rights_strings(t, s):
    beta = s['route3']['datasets']['beta']
    cites = {c['id']: c for c in s['deploymentTopics']['dataset_citations']}
    w = cites['zhu2021-wearable102-author-snapshot-20260920']
    t.put(('rights', 'datasets', 'beta'), {k: beta[k] for k in ('name', 'license', 'licenseUrl', 'source',
                                                                'rights_reviewed', 'rights_record')})
    t.put(('rights', 'datasets', 'beta', 'citation'), beta['attribution'].split(' Figshare ')[0])
    t.put(('rights', 'datasets', 'beta', 'publication_conditions'), cites['BETA']['publication_conditions'])
    t.put(('rights', 'datasets', 'wearable_102'), {k: w['identity'][k] for k in (
        'title', 'paper_citation', 'license', 'canonical_version_doi', 'local_representation')})
    t.put(('rights', 'datasets', 'wearable_102', 'dataset_citation'), w['identity']['canonical_dataset_citation'])
    t.put(('rights', 'datasets', 'wearable_102', 'primary_sources'), w['primary_sources'])
    reading = next(e['result'] for e in s['readings'] if e['id'] == 'BETA to Wearable102 external transfer')
    wd = next(d for d in reading['datasets_and_attribution'] if 'Zhu2021' in d['name'])
    t.put(('rights', 'datasets', 'wearable_102', 'readme'), re.search(r'Readme (\S+)', wd['doi_or_url']).group(1))
    t.put(('rights', 'datasets', 'wearable_102', 'consent_scope'),
          re.search(r'The paper describes consent for [^;.]+', wd['licence']).group(0) + '.')
    a = s['phaseTable']['sourceauthority']
    t.put(('rights', 'corrigendum'), {'revision': a['description_revision'], 'url': a['description_url'],
                                      'sha256': a['description_sha256'],
                                      'mirror': re.search(r'datasets/([^/]+/[^/]+)/', a['description_url']).group(1)})
    cb = next(x for x in s['coreMatrix']['models'] if x['name'] == 'CBraMod')
    t.put(('rights', 'cbramod'), {'license': cb['license'], 'repository': cb['url']})


def export_codes(served, s, manifest):
    """Every export code of a level or contrast points into its source at the value the served file gives."""
    named = {'cca_diagnostics': s['cca:diag_export'], 'questions-in-language-update.json': s['route3'],
             'deployment-topics.json': s['deploymentTopics'], 'wear_cca_definition': s['cca:wear_cca_definition']}
    checked = 0
    for study in STUDIES:
        src = manifest['sources'][study]
        source = s[f'{src["block"]}:{src["export"]}']
        block = served['studies'][study]
        items = {**block['levels'], **block['contrasts']}
        check(set(block['export_codes']) == set(items), f'{study}: export codes do not cover the levels and contrasts')
        for lid, codes in block['export_codes'].items():
            for code in codes:
                where, ptr = code.split('#', 1)
                target = walk(named[where] if where else source, ptr)
                value = next(target[k] for k in ('estimate', 'point', 'mean') if k in target)
                check(value == items[lid]['estimate'], f'{study} {lid}: {code} holds another value')
                checked += 1
    return checked


# ---------------------------------------------------------------------------- the boundary
def private_names(s):
    text = ''.join(json.dumps(s[k]) for k in ('query:ref2_export', 'query:softmax_export', 'phase:jitter_protocol',
                                              'phase:ramp_protocol', 'cca:diag_protocol', 'cca:adapter_protocol',
                                              'cca:wear_protocol'))
    names = set()
    for root in ('home', 'Volumes', 'mnt', 'Users'):
        for a, b in re.findall(rf'/{root}/([^/\s"]+)/([^/\s"]+)', text):
            names |= {a} | ({b} if re.search(r'[_\d]|^[A-Z]+$', b) else set())
    names |= set(re.findall(r'"([a-z]+)_code"', text)) & set(re.findall(r'"([a-z]+)_private"', text))
    return {n for n in names if len(n) >= 3}


def withheld(s):
    adapter, wear = s['cca:adapter_export'], s['cca:wear_export']

    def nums(v):
        return {x for _, x in leaves(v) if isinstance(x, float)}
    held = nums({k: v for k, v in adapter['per_seed_descriptive'].items() if k not in ('CCA-CROP', 'CCA-RAW')})
    held |= nums(adapter['residual_diagnostics']['CROP-RESIDUAL'])
    shown = nums(adapter['arms']) | nums(adapter['contrasts']) | nums(adapter['residual_diagnostics']['RAW-RESIDUAL'])
    for st in wear['strata'].values():
        held |= nums(st['metrics']['RAW-RESIDUAL_minus_CCA-CROP'])
        shown |= nums({k: v for k, v in st['metrics'].items() if k != 'RAW-RESIDUAL_minus_CCA-CROP'})
    return held - shown - {0.0, 1.0}


def covered(path, t):
    """A served string with no derived value: an editorial prefix, or an editorial leaf in a derived section."""
    if any(path[:len(p)] == p for p in EDITORIAL) or any(path[:len(p)] == p for p in t.sets):
        return True
    if path[0] != 'studies' or len(path) < 4:
        return False
    if path[2] in EDITORIAL_IN_STUDY:
        return True
    names = [k for k in path[3:] if isinstance(k, str)]
    return path[2] in DERIVED_SECTIONS and bool(names) and names[-1] in EDITORIAL_LEAVES


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
    t = Table()
    q, ph, cc = (manifest['blocks'][b]['pins'] for b in ('query', 'phase', 'cca'))
    t.adapter_sha = cc['adapter_export']['sha256']

    ref_src = s['query:ref_export']
    study_ref(t, s, ref_src)
    study_ref2(t, s, s['query:ref2_export'], s['query:ref2_protocol'])
    study_softmax(t, s, s['query:softmax_export'], s['query:parent'])
    study_jitter(t, s, s['phase:jitter_export'], s['phase:jitter_score'], s['phase:jitter_protocol'],
                 s['phase:jitter_audit'], s['phase:jitter_canary'], s['phase:jitter_bridge'],
                 s['phase:jitter_interpretation'], s['phase:jitter_provenance'], s['phase:jitter_release'])
    study_ramp(t, s, s['phase:ramp_score'], s['phase:ramp_protocol'], s['phase:ramp_audit'], s['phase:ramp_canary'],
               s['phase:ramp_interpretation'], s['phase:ramp_provenance'], s['phase:ramp_release'], ref_src,
               s['phase:jitter_protocol'])
    diag_est, diag = study_diagnostics(t, s, s['cca:diag_export'], s['cca:diag_protocol'], s['cca:diag_review'],
                                       s['cca:diag_hash_verification'], s['cca:diag_handoff_review'])
    study_adapter(t, s, s['cca:adapter_export'], s['cca:adapter_protocol'], s['cca:adapter_numerical_review'],
                  s['cca:adapter_review'], s['cca:adapter_release_status'], s['cca:adapter_binding_review'], diag,
                  s['cca:diag_export'])
    _, wear = study_wearable(t, s, s['cca:wear_export'], s['cca:wear_protocol'], s['cca:wear_numerical_summary'],
                             s['cca:wear_review'], s['cca:wear_release_status'], s['cca:wear_cca_definition'],
                             s['cca:dry_vs_wet'], s['cca:adapter_protocol'])
    spanning(t, s, manifest, ref_src, diag, wear)
    rights_strings(t, s)

    # Hashes, records and lists the manifest and the sources give as strings.
    for study in STUDIES:
        src = manifest['sources'][study]
        pins = manifest['blocks'][src['block']]['pins']
        t.put(('studies', study, 'source_sha256'), pins[src['export']]['sha256'])
        t.put(('studies', study, 'review_sha256'), pins[src['review']]['sha256'])
        t.put(('provenance', 'source_export_sha256', study), pins[src['export']]['sha256'])
    t.put(('provenance', 'manifest_sha256'), digest(manifest_bytes))
    # The other records each block names by hash: the pins of its module, by the manifest's own names.
    record_pins = {
        'softmax': {'parent_sha256': ('query', 'parent')},
        'phase_jitter': {'provenance_review_sha256': ('phase', 'jitter_provenance'),
                         'wording_review_sha256': ('phase', 'wording_review'),
                         'canonical_score_sha256': ('phase', 'jitter_score')},
        'phase_ramp': {'provenance_review_sha256': ('phase', 'ramp_provenance'),
                       'wording_review_sha256': ('phase', 'wording_review'), 'audit_sha256': ('phase', 'ramp_audit')},
        'cca_diagnostics': {'protocol_sha256': ('cca', 'diag_protocol'), 'freeze_sha256': ('cca', 'diag_freeze'),
                            'hash_verification_sha256': ('cca', 'diag_hash_verification'),
                            'handoff_review_sha256': ('cca', 'diag_handoff_review')},
        'cca_adapter': {'numerical_review_sha256': ('cca', 'adapter_numerical_review'),
                        'release_receipt_sha256': ('cca', 'adapter_release_status'),
                        'protocol_sha256': ('cca', 'adapter_protocol'), 'freeze_sha256': ('cca', 'adapter_freeze'),
                        'runner_sha256': ('cca', 'adapter_runner'),
                        'binding_review_sha256': ('cca', 'adapter_binding_review')},
        'wearable_transfer': {'numerical_summary_sha256': ('cca', 'wear_numerical_summary'),
                              'release_receipt_sha256': ('cca', 'wear_release_status'),
                              'protocol_sha256': ('cca', 'wear_protocol'), 'freeze_sha256': ('cca', 'wear_freeze'),
                              'cca_definition_sha256': ('cca', 'wear_cca_definition'),
                              'dry_vs_wet_sha256': ('cca', 'dry_vs_wet'),
                              'source_models_sha256': ('cca', 'adapter_export')},
    }
    for study, fields in record_pins.items():
        for field, (block, pin) in fields.items():
            t.put(('studies', study, field), manifest['blocks'][block]['pins'][pin]['sha256'])
    t.put(('provenance', 'pinned_by_hash_only'), {'phase_jitter_canonical_score': ph['jitter_score']['sha256'],
                                                  'phase_ramp_audit': ph['ramp_audit']['sha256']})
    t.put(('provenance', 'release_reviews_sha256'), {'wording_review': ph['wording_review']['sha256'],
                                                     'adapter_binding_review': cc['adapter_binding_review']['sha256'],
                                                     'wearable_cca_definition': cc['wear_cca_definition']['sha256']})
    t.put(('provenance', 'parent_release'), {'release_id': s['route3']['release_id'],
                                             'sha256': manifest['published']['route3']['sha256']})
    t.put(('provenance', 'released_files_unchanged'),
          [Path(manifest['published'][k]['path']).name for k in ('route3', 'deploymentTopics', 'coreMatrix')])
    rr = manifest['releaseRecord']
    t.put(('release_record',), {'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
                                'rights': rr['rights'], 'research_release': rr['researchRelease'],
                                'binding': rr['binding']})
    t.put(('not_published',), manifest['notPublished'])
    t.put(('schema_version',), 'bci-report-new-ssvep-frequencies-update-v1')
    t.put(('release_id',), manifest['release_id'])
    t.put(('generated_at',), manifest['freeze_date'])
    t.put(('status',), manifest['approval']['decision'])
    codes = export_codes(served, s, manifest)
    for i in range(len(NAME_KEY), len(served['name_key'])):
        t.put(('name_key', i, 'in_page_key'), False, 'editorial')

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
    check(not missing, f'expected values missing from the served file: {[show(p) for p in missing[:3]]}')

    text_blob = served_bytes[0].decode()
    published = {v for v in found.values() if is_number(v)}
    secret = withheld(s)
    check(not (secret & published), f'a withheld value reached the served file: {sorted(secret & published)[:3]}')
    check(all(abs(v - 11 / 20) > 1e-12 and abs(v - 55) > 1e-9 for v in published),
          'the commenter’s confidence figure is a value in the served file')
    for path, value in found.items():
        if isinstance(value, str) and not re.fullmatch(r'[0-9a-f]{64}', value):
            check(not re.search(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                                value, re.I), f'{show(path)}: a token of the commenter’s confidence figure')
    check(not any(re.search(r'fifty|05{2}|prediction', str(k), re.I) for p in found for k in p),
          'a key built on the commenter’s confidence figure')
    private = private_names(s)
    check(len(private) >= 4, 'no private names read from the pinned records')
    for n in private:
        check(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text_blob, re.I) is None,
              'a private user, host or volume name reached the served file')
    thread = served['thread']['url']
    check('twu' not in text_blob.replace(thread, '').lower(), 'a user name outside the thread URL')
    check(re.search(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', text_blob) is None,
          'a private path reached the served file')

    return {
        'status': 'pass', 'release_id': served['release_id'],
        'export_sha256': digest(served_bytes[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_new_ssvep_frequencies_export.py',
        'independence': ('A separate program from the export and from the three block modules, importing none of '
                         'them. It reads the served bytes, the release manifest and the files the manifest pins, '
                         're-derives every study block from the original research exports by its own reading (level and '
                         'contrast ids from the exports’ own labels, the declared edits from the plan’s list), '
                         'and recomputes the cohort, the Wearable-102 scope, the endpoints and every check count from the '
                         'protocols, receipts and reviews.'),
        'figures_compared': len(t.figures), 'copied_exactly': kinds['copied'], 'recomputed': kinds['derived'],
        'editorial': kinds['editorial'], 'nulls_kept': nulls, 'strings_compared': len(t.strings),
        'export_codes_resolved': codes, 'withheld_values_checked_absent': len(secret),
        'checks': [
            'the two served copies are byte-identical, and the served file names the manifest it was built from',
            'every number, flag and null in the served file has an expected value derived here, type included, and '
            'every expected value is in the file',
            'every level and contrast is its study export’s own double (the one-vs-rest head from the live route 3 '
            'file), and every contrast equals the difference of its two levels',
            'the declared edits: REF’s epochs renamed training_epochs, CCA’s seeds given as no training, and '
            'the dropped jitter and ramp fields present in their sources and absent from the served file',
            'the cohort, the Wearable-102 scope, the endpoints and every check count recomputed from the pinned '
            'protocols, receipts, reviews, the A2 note and the core matrix',
            'every export code resolves in its source to the value the served file gives',
            'hashes, released rights records, the corrigendum and CBraMod records, the release record and the '
            'not-published list checked as strings',
            'no withheld value, no form of the commenter’s confidence figure, no private path and no private '
            'user, host or volume name in the served file',
        ],
        'audit_bindings': {
            'bound': [
                'every study’s source export, review, protocol and receipts: pinned in the manifest, and the same '
                'bytes the block modules pin, which the export checks',
                'every figure: equal to a pinned source leaf, or recomputed here from pinned source leaves',
            ],
            'not_bound': [
                'the run outputs behind each export (predictions, seals, fitted models): each study’s own '
                'numerical review recomputed them; this audit opens no sealed file',
                'editorial strings (display names, limitation keys, card anchors, the name key’s rows and the '
                'text this release writes) are checked by the export and its tests, not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
