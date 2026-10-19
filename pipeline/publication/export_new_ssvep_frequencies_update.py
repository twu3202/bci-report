"""Release the seven route 3 follow-ups on new SSVEP frequencies, aggregate-only, on their own question page.

Seven audited follow-ups to route 3 answer one question: what lets a decoder answer an SSVEP frequency it never trained
on? Six run on the BETA cohort route 3 studied (cards 1 to 6: the reference-spectrum query, the head and feature
follow-up with the two softmax heads, the phase jitter, the phase ramp, the CCA mechanism diagnostics and the CCA
adapter); the seventh runs the adapter's 105 models unchanged on Wearable-102 (card 7). The owner's decision D1 of
2026-10-19 publishes them in their own file on a new page; questions-in-language-update.json, deployment-topics.json
and mvp.json keep their bytes.

The study blocks are built by the three block modules (ssvep_followups/blocks_query.py, blocks_phase.py,
blocks_cca.py), each from its own audited exports, reviews and receipts, pinned by SHA-256; this assembler adds what
spans the studies and binds the whole to the release manifest:
- the manifest pins exactly the files each block module pins, and each study's source export is the one the
  verified handoff readings name and the module's block carries;
- `cohort` (the cards 1 to 6 scope), `wearable` (card 7's own scope) and `endpoints` are read from the blocks and
  required equal across every study that states them; the core 40-way chance is the core matrix's BETA track value;
- `name_key` is the plan's name key (site names first, export codes second), each row holding the codes the blocks
  give that name, and every code of every block in exactly one row;
- `rights` copies the released BETA and Wearable-102 records (BETA's attribution up to its repository line, which
  carries the Figshare version tag; Wearable-102 without its operator-facing publication conditions), the corrigendum
  facts from the REF2 phase table its protocol pins, and CBraMod's licence from the core matrix's model record;
- `provenance` names the manifest and every study's source export by SHA-256.

What this export refuses:
- a block module that pins other bytes than the manifest, a source export the readings did not verify, a cohort or
  endpoint figure two studies state differently, a code without a row in the name key;
- per-person, per-fold, per-seed and per-window values, predictions, features and timings, by key and by fragment, and
  the adapter's per-seed accuracies, its CROP-RESIDUAL transitions and the Wearable-102 contrast against the
  cropped-spectrum check by value; private paths, host, volume and user names (read at run time from the pinned
  records that carry them);
- the commenter's confidence figure in any form (R5 M7: no value equal to it as a fraction or a percentage, no key
  built on it, no token of it in any text), the commenter's name, a comment anchor, and the bet outside the phase ramp;
- a version label, a month or an update marker in the text, Jev, an unnegated claim of a ranking or of clinical or
  real-time use, and an "X, not Y" hedge in the text this file adds.

    python3 pipeline/publication/export_new_ssvep_frequencies_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import require, sha
from ssvep_followups import blocks_cca, blocks_phase, blocks_query

PROJECT = Path(__file__).resolve().parents[2]
PUBLICATION = Path(__file__).resolve().parent
LOCAL = PUBLICATION / 'local_paths.json'             # optional `researchRoot`: where this machine keeps research/
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'new-ssvep-frequencies-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'new-ssvep-frequencies-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/new-ssvep-frequencies-update.json',
           PROJECT / 'site/public/data/new-ssvep-frequencies-update.json')
RELEASE_ID = 'new-ssvep-frequencies-update-20261020'
SCHEMA = 'bci-report-new-ssvep-frequencies-update-v1'
PARENT_RELEASE = 'questions-in-language-update-20261008'

MODULES = {'query': blocks_query, 'phase': blocks_phase, 'cca': blocks_cca}
STUDIES = ('ref', 'ref2', 'softmax', 'phase_jitter', 'phase_ramp', 'cca_diagnostics', 'cca_adapter', 'wearable_transfer')
COHORT_STUDIES = STUDIES[:-1]
# card -> (anchor, studies), plan section 2.1; card 8 is the cross-spectral status card and carries no figures (D9).
CARDS = ((1, 'reference-spectrum', ('ref',)), (2, 'head-and-features', ('ref2', 'softmax')),
         (3, 'phase-jitter', ('phase_jitter',)), (4, 'phase-ramp', ('phase_ramp',)),
         (5, 'cca-mechanism', ('cca_diagnostics',)), (6, 'cca-correction', ('cca_adapter',)),
         (7, 'wearable-transfer', ('wearable_transfer',)), (8, 'cross-spectral', ()))
# The plan's name key (section 2.1), in its order: site name, export codes as the key prints them.
NAME_KEY = (
    ('question number', 'ID'),
    ('numeric code', 'NUM'),
    ('label template', 'TPL'),
    ('reference spectrum', 'REF'),
    ('reference with stimulus phase', 'REFc-0'),
    ('fixed spectrum match (no training)', 'TEMPLATE'),
    ('plain spectrum', 'L0'),
    ('complex spectrum', 'L0c'),
    ('frozen CBraMod features', 'L1'),
    ('FiLM head', 'FS'),
    ('matching head', 'MATCH'),
    ('CCA (no training)', 'CCA-RAW'),
    ('Hann-tapered CCA', 'CCA-HANN-C/U'),
    ('cropped-spectrum match (no training)',
     'SUBSPACE-CROP in the diagnostics export, CCA-CROP in the adapter export: one set of scores'),
    ('channel-energy average', 'CHANNEL-JOINT/HARMONIC'),
    ('shared ridge scorer', 'SHARED-RIDGE'),
    ('energy head', 'ENERGY-FS'),
    ('adapted head', 'ADAPT-FS'),
    ('CCA with learned correction', 'RAW-RESIDUAL'),
    ('cropped match with learned correction', 'CROP-RESIDUAL'),
    ('cropped-spectrum check (Wearable-102)', 'CCA-CROP in the Wearable export'),
)
CODE_ALIASES = {'CCA': 'CCA-RAW'}      # the query and phase exports spell CCA-RAW as CCA
ID_REASON = 'cannot_ask_unseen'
TOL = 1e-12

REFUSED_KEYS = {'pid', 'job', 'private_root', 'remote_root', 'indices_sha256', 'per_seed_descriptive', 'privacy',
                'protected_trials', 'exported_at_utc', 'updated_at', 'release_governed_by', 'one_period_prediction',
                'interpretation', 'epochs', 'path', 'handoff_path', 'export_path'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_seed', 'subject', 'prediction', 'probabilit', 'confusion', 'percentile',
                         'quantile', 'elapsed', 'timing', 'memory', 'device', 'host', 'private', 'path', 'fifty',
                         '055', '_utc')
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\bSubject\d+|\.(?:npz|npy|edf|mat|pt|ckpt|py)\b', re.IGNORECASE)
# R5 M7, the token rule for the commenter's confidence figure (page text and every string of this file).
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                              re.IGNORECASE)
HASH = re.compile(r'[0-9a-f]{64}')        # a SHA-256 may hold any digit pair
CONFIDENCE_VALUE = 11 / 20             # the figure as a fraction, written as a ratio so it is never spelled here
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
CLAIMS = re.compile(r'outperform|\bbeats?\b|superior|\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|leaderboard'
                    r'|state[- ]of[- ]the[- ]art|significan|equivalen|\bcausal|\bclinical\b|\bmedical\b|\bonline\b'
                    r'|real-time|closed-loop|zero-shot|\bendorse', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none|nothing|outside)\b|n't\b", re.IGNORECASE)
HEDGE = re.compile(r',\s+not\s|\bnot\s+\w+(?:\s+\w+){0,4},\s+but\b', re.IGNORECASE)
# Released records copied as they are (they carry review dates, versions and their own wording).
VERBATIM = re.compile(r'^\$\.rights\.(?:datasets\.\w+\.(?!published_here|cards|consent_scope)|cbramod\.license'
                      r'|corrigendum\.url)')


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def research_root():
    try:
        config = json.loads(LOCAL.read_text())
    except FileNotFoundError:
        config = {}
    root = config.get('researchRoot')
    return Path(root) if root else PROJECT / 'research'


def location(path):
    """A manifest path on this machine: `research/...` under `researchRoot` when local_paths.json sets one."""
    path = str(path)
    if Path(path).is_absolute():
        return Path(path)
    if path.startswith('research/'):
        return research_root() / path[len('research/'):]
    return PROJECT / path


def read_pinned(ref, label):
    raw = location(ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {Path(ref["path"]).name} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return json.loads(raw) if ref['path'].endswith('.json') else raw.decode('utf-8')


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


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield f'{trail}.<key>', k
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif number(value):
        yield value


def one(values, label):
    """The single value every study states, or a refusal naming the disagreement."""
    distinct = {json.dumps(v, sort_keys=True) for v in values}
    require(len(distinct) == 1, f'{label}: the studies state {sorted(distinct)}')
    return values[0]


# ---------------------------------------------------------------------------- inputs and bindings
def load(manifest):
    """The pinned inputs this assembler reads itself; the block modules read and check their own."""
    docs = {'owner': read_pinned(manifest['approval']['ownerDecisions'], 'owner decisions'),
            'readings': read_pinned(manifest['planning']['readings'], 'readings')}
    for k, r in manifest['published'].items():
        docs[k] = read_pinned(r, k)
    for k, r in manifest['credits'].items():
        docs[k] = read_pinned(r, k)
    for m, block in manifest['blocks'].items():
        for k, r in block['pins'].items():
            docs[f'{m}:{k}'] = read_pinned(r, f'{m} {k}')
    return docs


def module_pins(manifest):
    """The manifest pins exactly what each block module pins: a pin changed in one place only is refused."""
    for m, module in MODULES.items():
        block = manifest['blocks'][m]
        require(block['module'] == f'pipeline/publication/ssvep_followups/{Path(module.__file__).name}',
                f'{m}: the manifest names another module')
        require(block['pins'] == {k: dict(v) for k, v in module.PINS.items()},
                f'{m}: the manifest pins other files than {Path(module.__file__).name}')
        require(tuple(block['studies']) == tuple(s for s in STUDIES if manifest['sources'][s]['block'] == m),
                f'{m}: the manifest assigns other studies')


def declared_edits(manifest):
    """The manifest declares exactly the edits each module applies; the CCA module selects, and declares what not."""
    de = manifest['declaredEdits']
    require(tuple(de) == STUDIES, 'declared edits: not one entry per study')
    for study in STUDIES:
        m = manifest['sources'][study]['block']
        require(de[study]['applied_by'] == m, f'{study}: declared edits name another module')
        if m == 'cca':
            require(de[study]['not_selected'] == list(blocks_cca.DECLARED_EDITS[study]),
                    f'{study}: the declared edits differ from the module')
            continue
        module = MODULES[m]
        want = [{'op': op, 'pointer': ptr} | ({'to': new} if op in ('rename', 'replace') else {})
                for op, ptr, _, new in module.EDITS[study]]
        require(de[study]['edits'] == want, f'{study}: the declared edits differ from the module')
    require(any(e['op'] == 'rename' and e.get('to') == 'training_epochs' for e in de['ref']['edits']),
            'ref: the epochs rename is not declared')


def bindings(docs, manifest):
    owner = docs['owner']
    require(owner['freeze_date'] == manifest['freeze_date'].replace('-', '') == RELEASE_ID.rsplit('-', 1)[1],
            'the freeze date is not the release id’s')
    require('seven SSVEP follow-ups (new-ssvep-frequencies)' in owner['decisions']['D1']['answer'],
            'owner decision D1 does not publish the SSVEP follow-ups')
    defaults = owner['decisions']['defaults_stated_to_owner_and_not_objected']
    require('linked, not named' in defaults['D6'] and 'no figures' in defaults['D9'] and 'R1_R5' in defaults,
            'the owner defaults D6, D9 or R1_R5 changed')
    # Each study's source export is the one the verified handoff readings name, byte for byte.
    readings = {e['id']: e['result'] for e in docs['readings']}
    for study in STUDIES:
        src = manifest['sources'][study]
        pin = manifest['blocks'][src['block']]['pins'][src['export']]
        r = readings.get(src['readings'])
        require(r is not None and r['status'] in ('release_ready', 'partly_ready'), f'{study}: no reading')
        asset = [a for a in r['files_for_public_assets'] if a['path'].endswith('/' + pin['path'])]
        require(len(asset) == 1 and asset[0]['matches'] is True and asset[0]['sha256_actual'] == pin['sha256'],
                f'{study}: the readings verified another export')
    # The handoffs are context only: each bound hash is the one its receipt binds.
    for study, h in manifest['handoffContext'].items():
        require(h == {k: v for k, v in blocks_cca.HANDOFF_CONTEXT[study].items()} | {'role': h['role']}
                and h['role'] == 'context only, never a copy source', f'{study}: handoff context differs from B3')
    for key, rv in manifest['reviews'].items():
        require(rv['pin'] in manifest['blocks'][rv['block']]['pins'], f'{key}: the review is not pinned')


def build_blocks(manifest):
    """The eight study blocks, each module given the manifest's own pins."""
    built = {}
    for m, module in MODULES.items():
        pins = {k: dict(v) for k, v in manifest['blocks'][m]['pins'].items()}
        built.update(module.build_blocks(pins))
    require(set(built) == set(STUDIES), f'the modules built {sorted(built)}')
    blocks = {s: built[s] for s in STUDIES}
    for study in STUDIES:
        src = manifest['sources'][study]
        pins = manifest['blocks'][src['block']]['pins']
        require(blocks[study]['source_sha256'] == pins[src['export']]['sha256'], f'{study}: another source export')
        require(blocks[study]['review_sha256'] == pins[src['review']]['sha256'], f'{study}: another review')
    return blocks


# ---------------------------------------------------------------------------- what spans the studies
def cohort_block(blocks):
    """Cards 1 to 6: one cohort, stated once, and equal in every study that states it."""
    ref = blocks['ref']['design']
    designs = {s: blocks[s]['design']['dataset'] for s in ('phase_jitter', 'phase_ramp', 'cca_diagnostics',
                                                           'cca_adapter')}
    people = one([ref['people']] + [d['people'] for d in designs.values()]
                 + [lv['people'] for s in COHORT_STUDIES for lv in blocks[s]['levels'].values()]
                 + [c['people'] for s in COHORT_STUDIES for c in blocks[s]['contrasts'].values()], 'people')
    windows = one([ref['trials']] + [d['windows'] for d in designs.values()], 'windows')
    folds = one([ref['participant_folds']] + [d['person_folds'] for d in designs.values()], 'person folds')
    rotations = one([ref['frequency_rotations']] + [d['frequency_rotations'] for d in designs.values()], 'rotations')
    targets = one([d['targets'] for d in designs.values()], 'targets')
    # Every trained level: the fixed spectrum match (TEMPLATE) has one deterministic fit, the CCA scorers none.
    seeds = one([len(ref['fit_seeds'])] + [d['training_seeds'] for s, d in designs.items() if s != 'cca_diagnostics']
                + [lv['seeds'] for s in COHORT_STUDIES for lid, lv in blocks[s]['levels'].items()
                   if isinstance(lv['seeds'], int) and not lid.startswith('TEMPLATE/')], 'training seeds')
    seen, held = ref['source_frequencies_per_rotation'], ref['held_frequencies_per_rotation']
    require(seen + held == targets and blocks['cca_diagnostics']['design']['endpoints']['u8']['candidate_count'] == held
            and blocks['cca_diagnostics']['design']['endpoints']['seen_ba']['candidate_count'] == seen,
            'the seen and held-out frequencies do not split the targets')
    require(ref['window_seconds'] == 2, 'the windows are not two seconds')
    diag = blocks['cca_diagnostics']['design']
    return {
        'cards': [1, 2, 3, 4, 5, 6],
        'studies': list(COHORT_STUDIES),
        'dataset': 'BETA',
        'people': people,
        'targets': targets,
        'windows': windows,
        'window_seconds': ref['window_seconds'],
        'person_folds': folds,
        'frequency_rotations': rotations,
        'seen_frequencies': seen,
        'held_out_frequencies': held,
        'training_seeds': seeds,
        'same_cohort_as': PARENT_RELEASE,
        'unseen_means': 'unseen by the trained part of the decoder',
        'card5': {'training_free_scorers': diag['training_free_scorers'], 'ridge_fits': diag['ridge_fits']},
    }


def wearable_scope(blocks):
    """Card 7's own scope strip: Wearable-102 and the unchanged BETA models, apart from the cohort of cards 1 to 6."""
    w = blocks['wearable_transfer']
    d, sm = w['design']['dataset'], w['design']['source_models']
    span = d['window_s'][1] - d['window_s'][0]
    require(abs(span - round(span)) < 1e-9, 'Wearable-102: the window is not whole seconds')
    require(set(d['sensors']) == set(STRATA_SENSORS) and d['windows'] == d['windows_per_sensor'] * len(d['sensors']),
            'Wearable-102: sensors or windows')
    require({lv['people'] for lv in w['levels'].values()} == {d['people']}, 'Wearable-102: people')
    require('prior_use_overlap_snapshot' in w['limitations_keys'], 'Wearable-102: the overlap caveat is missing')
    matched = next(m for m in w['design']['methods'] if m['code'] == 'CCA-RAW')
    require(matched['harmonics'] == w['cca_definition']['matched_cca']['harmonics'], 'Wearable-102: matched CCA')
    return {
        'cards': [7],
        'studies': ['wearable_transfer'],
        'dataset': d['name'],
        'people': d['people'],
        'targets': d['targets'],
        'frequency_range_hz': list(d['frequency_range_hz']),
        'windows_per_sensor': d['windows_per_sensor'],
        'windows': d['windows'],
        'window_seconds': round(span),
        'sensors': list(d['sensors']),
        'recordings': d['amplitude'],
        'source_dataset': sm['dataset'],
        'source_models': sm['models'],
        'retraining': sm['retraining'],
        'matched_cca_harmonics': matched['harmonics'],
        'participant_overlap_with_beta': 'possible: the documentation cannot rule it out',
        'overlap_limitation_key': 'prior_use_overlap_snapshot',
    }


STRATA_SENSORS = ('dry', 'wet')


def endpoints_block(blocks, core):
    def chance(study, e):
        ep = blocks[study]['design']['endpoints'][e]
        return {'candidate_count': ep['candidate_count'], 'chance': ep['chance']}

    u8 = one([chance(s, 'u8') for s in ('phase_jitter', 'phase_ramp', 'cca_diagnostics', 'cca_adapter')], 'u8')
    seen = one([chance(s, 'seen_ba') for s in ('phase_jitter', 'phase_ramp', 'cca_diagnostics', 'cca_adapter')], 'seen')
    beta_tracks = [t for t in core['tracks'] if t['id'] in ('beta-8ch', 'beta-4ch')]
    require(len(beta_tracks) == 2, 'the core matrix lists other BETA tracks')
    core_chance = one([t['chanceLevel'] for t in beta_tracks], 'core chance') / 100
    w = blocks['wearable_transfer']['design']
    wear = one([w['endpoints'][s]['chance'] for s in ('dry', 'wet', 'all')], 'Wearable-102 chance')
    wear_k = one([w['endpoints'][s]['candidate_count'] for s in ('dry', 'wet', 'all')], 'Wearable-102 candidates')
    targets = blocks['cca_diagnostics']['design']['dataset']['targets']
    require(abs(core_chance - 1 / targets) <= TOL and abs(u8['chance'] - 1 / u8['candidate_count']) <= TOL
            and abs(seen['chance'] - 1 / seen['candidate_count']) <= TOL and abs(wear - 1 / wear_k) <= TOL,
            'a chance level is not one over its candidates')
    # ID has no held-out endpoint in every study that asks by question number.
    id_rows = [u for s in ('ref', 'ref2', 'phase_ramp') for u in blocks[s]['undefined'] if '-ID/' in u['level']]
    require(id_rows and all(u['reason'] == ID_REASON and u['level'].split('/')[1] in ('u8', 'u3', 'cost')
                            for u in id_rows), 'ID: another undefined reason')
    return [
        {'id': 'u8', 'task': 'Held-out 8-way', 'candidates': u8['candidate_count'], 'chance': u8['chance'],
         'cards': [1, 2, 3, 4, 5, 6]},
        {'id': 'seen_ba', 'task': 'Seen 32-way balanced', 'candidates': seen['candidate_count'],
         'chance': seen['chance'], 'cards': [1, 2, 3, 4, 5, 6]},
        {'id': 'core_40', 'task': 'Core 40-way', 'candidates': targets, 'chance': core_chance, 'cards': [],
         'pages': [f'/protocols/{t["id"]}/' for t in beta_tracks], 'separate_page': True},
        {'id': 'wearable_12', 'task': 'Wearable-102 12-way', 'candidates': wear_k, 'chance': wear, 'cards': [7]},
        {'id': 'id_held_out', 'task': 'ID on held-out', 'candidates': None, 'chance': None, 'cards': [],
         'defined': False, 'reason': ID_REASON},
    ]


def named_codes(text):
    """The export codes a name-key cell names: 'CCA-HANN-C/U' -> CCA-HANN-C, CCA-HANN-U; prose cells by token."""
    if ' ' not in text:
        first, *rest = text.split('/')
        stem = first.rsplit('-', 1)[0]
        return [first] + [f'{stem}-{r}' for r in rest]
    return re.findall(r'\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b', text)


def name_key_block(blocks):
    """The plan's name key with the codes each block gives every name; every code lands in exactly one row."""
    given = {}
    for study in STUDIES:
        for code, name in blocks[study]['display_names'].items():
            given.setdefault(name, []).append({'study': study, 'code': code})
    rows = []
    for name, text in NAME_KEY:
        codes = given.pop(name, [])
        require(codes, f'name key: no block uses {name!r}')
        named = set(named_codes(text))
        require({CODE_ALIASES.get(c['code'], c['code']) for c in codes} <= named,
                f'name key: {name!r} holds codes its cell does not name')
        rows.append({'site_name': name, 'export_codes': text, 'codes': codes, 'in_page_key': True})
    for name, codes in given.items():        # names the blocks use beyond the plan's key (card 2, card 3, card 7)
        rows.append({'site_name': name, 'export_codes': '/'.join(dict.fromkeys(c['code'] for c in codes)),
                     'codes': codes, 'in_page_key': False})
    placed = [(c['study'], c['code']) for r in rows for c in r['codes']]
    require(len(placed) == len(set(placed)), 'name key: a code sits in two rows')
    crop = next(r for r in rows if r['site_name'] == 'cropped-spectrum match (no training)')
    require({(c['study'], c['code']) for c in crop['codes']} == {('cca_diagnostics', 'SUBSPACE-CROP'),
                                                               ('cca_adapter', 'CCA-CROP')},
            'name key: the cropped-spectrum match is not one name for the diagnostics and adapter scores')
    return rows


def rights_block(docs, blocks, phase_table_sha):
    beta = docs['route3']['datasets']['beta']
    cites = {c['id']: c for c in docs['deploymentTopics']['dataset_citations']}
    beta_c, wear_c = cites['BETA'], cites['zhu2021-wearable102-author-snapshot-20260920']
    require(beta['license'] == beta_c['identity']['license'] == 'CC BY 4.0' and beta['rights_record']
            == 'reused unchanged from the released record', 'BETA: another rights record')
    require(wear_c['identity']['license'] == 'CC BY 4.0' and wear_c['decision'] == 'aggregate_publication_only',
            'Wearable-102: another rights record')
    reading = next(e['result'] for e in docs['readings'] if e['id'] == 'BETA to Wearable102 external transfer')
    wd = next(d for d in reading['datasets_and_attribution'] if 'Wearable' in d['name'] and 'Zhu2021' in d['name'])
    readme = re.search(r'Readme (https://\S+\.pdf)', wd['doi_or_url'])
    consent = re.search(r'The paper describes consent for noncommercial scientific research', wd['licence'])
    require(readme is not None and consent is not None, 'Wearable-102: the readings no longer give the Readme or consent')
    authority = docs['phaseTable']['sourceauthority']
    m = re.fullmatch(r'https://huggingface\.co/datasets/([^/]+/[^/]+)/resolve/([0-9a-f]{40})/Description\.pdf',
                     authority['description_url'])
    require(m is not None and m.group(2) == authority['description_revision']
            and docs['phaseTable']['convention'] == 'cosine' and docs['phaseTable']['primary_tau_seconds'] == 0.0,
            'the corrigendum record changed')
    require(docs['query:ref2_protocol']['complex_reference']['phase_table_sha256'] == phase_table_sha,
            'the REF2 protocol pins another phase table')
    cbramod = [x for x in docs['coreMatrix']['models'] if x['name'] == 'CBraMod']
    require(len(cbramod) == 1 and cbramod[0]['license'], 'the core matrix has no single CBraMod record')
    require('L1' in blocks['ref']['display_names'] and 'REFc-0' in blocks['ref2']['display_names'],
            'the credited inputs are not used')
    people = blocks['ref']['design']['people']
    # The released attribution, up to its repository line (which carries the Figshare version tag).
    citation, sep, _ = beta['attribution'].partition(' Figshare ')
    require(sep and citation.endswith('doi:10.3389/fnins.2020.00627.') and 'Liu et al.' in citation,
            'BETA: the released attribution changed')
    return {
        'datasets': {
            'beta': {**{k: beta[k] for k in ('name', 'license', 'licenseUrl', 'source', 'rights_reviewed',
                                             'rights_record')},
                     'citation': citation,
                     'publication_conditions': list(beta_c['publication_conditions']),
                     'cards': [1, 2, 3, 4, 5, 6, 7],
                     'published_here': (f'Cohort aggregates over the {people} people for cards 1 to 6, and the source '
                                        'of the 105 models run on Wearable-102 in card 7: levels and paired contrasts '
                                        'with their intervals, transition shares and check counts. No per-person, '
                                        'per-fold, per-rotation or per-window value.')},
            'wearable_102': {'name': 'Wearable-102',
                             **{k: wear_c['identity'][k] for k in ('title', 'paper_citation', 'license',
                                                                   'canonical_version_doi', 'local_representation')},
                             'dataset_citation': wear_c['identity']['canonical_dataset_citation'],
                             'primary_sources': list(wear_c['primary_sources']),
                             'readme': readme.group(1),
                             'consent_scope': consent.group(0) + '.',
                             'cards': [7],
                             'published_here': ('Cohort aggregates over the 102 people, by sensor: the levels of the '
                                                '105 BETA models, matched CCA and the cropped-spectrum check, and the '
                                                'paired contrasts with their intervals. No per-person, per-window or '
                                                'questionnaire value.')},
        },
        'corrigendum': {'name': 'BETA authors’ corrigendum (Description.pdf)', 'mirror': m.group(1),
                        'revision': authority['description_revision'], 'url': authority['description_url'],
                        'sha256': authority['description_sha256'], 'cards': [2, 3],
                        'used_for': ('the stimulus phases of the reference with stimulus phase (REFc-0), converted to '
                                     'the cosine convention with zero latency')},
        'cbramod': {'name': 'CBraMod', 'method_page': '/methods/cbramod/', 'license': cbramod[0]['license'],
                    'repository': cbramod[0]['url'], 'cards': [1],
                    'used_for': 'the frozen CBraMod features (L1) of card 1, the ones route 3 used'},
    }


def same_score(values, label, tol=0.0):
    require(max(values) - min(values) <= tol, f'{label}: the studies state {sorted(set(values))}')


def cross_checks(blocks):
    """What the cards print side by side is one set of scores: CCA's held-out score is the same double in every study,
    and the reused heads agree to the last bit or, from the jitter export, to one unit in the last place."""
    cca = [blocks[s]['levels']['CCA/u8']['estimate'] for s in ('ref', 'ref2', 'phase_ramp')]
    cca += [blocks[s]['levels']['CCA-RAW/u8']['estimate'] for s in ('cca_diagnostics', 'cca_adapter')]
    same_score(cca, 'CCA held-out')
    same_score([blocks[s]['levels']['L0-FS-REF/u8']['estimate'] for s in ('ref', 'ref2', 'phase_jitter', 'phase_ramp')],
               'reference spectrum held-out', 1e-15)
    same_score([blocks[s]['levels']['L0c-FS-REFc-0/u8']['estimate'] for s in ('ref2', 'phase_jitter')],
               'REFc-0 held-out', 1e-15)
    bet = [s for s in STUDIES if 'thread_bet' in blocks[s]]
    require(bet == ['phase_ramp'] and set(blocks['phase_ramp']['thread_bet']) == {'held8_threshold', 'source_url'}
            and '#' not in blocks['phase_ramp']['thread_bet']['source_url'], 'the bet: phase ramp only, two keys')


# ---------------------------------------------------------------------------- the boundary
def private_names(docs):
    """The user, project, volume and host names the private records use, read from them."""
    text = ''.join(json.dumps(docs[k]) for k in ('query:ref2_export', 'query:softmax_export', 'phase:jitter_protocol',
                                                 'phase:ramp_protocol', 'cca:diag_protocol', 'cca:adapter_protocol',
                                                 'cca:wear_protocol'))
    names = set()
    for root in ('home', 'Volumes', 'mnt', 'Users'):
        for a, b in re.findall(rf'/{root}/([^/\s"]+)/([^/\s"]+)', text):
            names.add(a)
            if re.search(r'[_\d]|[a-z][A-Z]|^[A-Z]+$', b):     # project folders, not plain words
                names.add(b)
    # The run host, as the records key it: the machine that has both a code root and a private root.
    names |= set(re.findall(r'"([a-z]+)_code"', text)) & set(re.findall(r'"([a-z]+)_private"', text))
    return {n for n in names if len(n) >= 3}


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


def authored(trail):
    """Text this assembler writes, apart from the study blocks, the released records and the hashes."""
    return not (trail.startswith(('$.studies', '$.provenance')) or VERBATIM.match(trail)
                or trail in ('$.schema_version', '$.release_id'))


def prose_check(payload, private):
    url = payload['thread']['url']
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(HASH.fullmatch(text) or not CONFIDENCE_TOKEN.search(text),
                f'{trail}: the commenter’s figure never appears')
        require(not blocks_cca.REFUSED_TEXT.search(text), f'{trail}: refused text')
        require('twu' not in text.replace(url, '').lower(), f'{trail}: a user name outside the thread URL')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.IGNORECASE),
                    f'private host or volume name in export: {trail}')
        if trail in ('$.schema_version', '$.release_id') or VERBATIM.match(trail):
            continue
        require(not SOURCE_IDS.search(text), f'source file or participant identifier in export: {trail}')
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):     # the release record is dated by design
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if (not authored(trail) or trail.endswith('.<key>') or trail.startswith('$.release_record')
                or re.search(r'(?:url|readme|page)$', trail)):
            continue
        require(not HEDGE.search(text), f'{trail}: an "X, not Y" hedge: {text!r}')
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def confidence_absent(payload):
    """R5 M7 on the served JSON: no value equal to the figure, no key built on it."""
    for v in numbers(payload):
        require(abs(v - CONFIDENCE_VALUE) > 1e-12 and abs(v - 100 * CONFIDENCE_VALUE) > 1e-9,
                'the commenter’s figure is a value in the export')
    for trail, k in strings(payload):
        if trail.endswith('.<key>'):
            require(not re.search(r'fifty|05{2}|prediction', k, re.IGNORECASE), f'{trail}: key {k!r}')


def withheld_values(docs):
    """Figures the study exports hold that this release does not publish, less any figure that the same export also
    publishes in a selected field (one seed's ENERGY-FS score equals the three-seed mean, the margin is one value)."""
    adapter, wear = docs['cca:adapter_export'], docs['cca:wear_export']
    held = set(numbers({k: v for k, v in adapter['per_seed_descriptive'].items() if k not in ('CCA-CROP', 'CCA-RAW')}))
    held |= set(numbers(adapter['residual_diagnostics']['CROP-RESIDUAL']))
    shown = set(numbers(adapter['arms'])) | set(numbers(adapter['contrasts']))
    shown |= set(numbers(adapter['residual_diagnostics']['RAW-RESIDUAL']))
    for s in wear['strata'].values():
        held |= set(numbers(s['metrics']['RAW-RESIDUAL_minus_CCA-CROP']))
        shown |= set(numbers({k: v for k, v in s['metrics'].items() if k != 'RAW-RESIDUAL_minus_CCA-CROP'}))
    return {v for v in held - shown if isinstance(v, float)} - {0.0, 1.0}


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['holds'] == [], 'this release has no hold')
    require(tuple(manifest['sources']) == STUDIES, 'the manifest lists other studies')
    module_pins(manifest)
    declared_edits(manifest)
    docs = load(manifest)
    bindings(docs, manifest)
    blocks = build_blocks(manifest)
    cross_checks(blocks)
    rr = manifest['releaseRecord']
    pins = {s: manifest['blocks'][manifest['sources'][s]['block']]['pins'] for s in STUDIES}
    phase_pins, cca_pins = manifest['blocks']['phase']['pins'], manifest['blocks']['cca']['pins']
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['freeze_date'],
        'status': 'aggregate_preview',
        'title': 'New SSVEP frequencies',
        'question': 'What lets a decoder answer an SSVEP frequency it never trained on?',
        'placement': {
            'page': '/topics/new-ssvep-frequencies/', 'group': 'adapting', 'after': 'questions-in-language',
            'linked_from': '/topics/questions-in-language/#unseen-frequency', 'leaderboard': False,
            'new_dataset_count': 0, 'new_model_count': 0,
            'cards': [{'card': c, 'anchor': a, 'studies': list(s)} | ({} if s else {'status_only': True})
                      for c, a, s in CARDS],
        },
        'metric_units': ('Accuracies, balanced accuracies, transition shares, chance levels and the bet threshold are '
                         'proportions in [0,1]. An entry with unit "difference of proportions" is a paired difference, '
                         'stored as a proportion: multiply by 100 for percentage points. The protected margin is in '
                         'units of CCA correlation. Counts of people, windows, folds, rotations, seeds, fits, parameters '
                         'and prediction instances are whole numbers. "no training" or "deterministic fit" stands where '
                         'a trained level gives its seed count; null means not defined or not computed, never zero.'),
        'scope': ('Seven audited follow-ups to route 3 on SSVEP frequencies a decoder never trained on. Six use the '
                  'BETA cohort route 3 studied (cards 1 to 6); the seventh runs the card 6 models unchanged on '
                  'Wearable-102 (card 7). Each study block is read from its own audited export and carries its own '
                  'interval method. Seen and held-out results are separate tasks, reported side by side. Every figure '
                  'compares set-ups on fixed splits.'),
        'thread': {'url': blocks['phase_ramp']['thread_bet']['source_url'],
                   'role': 'the public Hugging Face post whose comment thread these follow-ups answer',
                   'commenter_named': False},
        'cohort': cohort_block(blocks),
        'wearable': wearable_scope(blocks),
        'endpoints': endpoints_block(blocks, docs['coreMatrix']),
        'name_key': name_key_block(blocks),
        'studies': blocks,
        'rights': rights_block(docs, blocks, manifest['credits']['phaseTable']['sha256']),
        'release_record': {
            'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
            'rights': rr['rights'], 'research_release': rr['researchRelease'], 'binding': rr['binding'],
        },
        'not_published': list(manifest['notPublished']),
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {s: pins[s][manifest['sources'][s]['export']]['sha256'] for s in STUDIES},
            'pinned_by_hash_only': {'phase_jitter_canonical_score': phase_pins['jitter_score']['sha256'],
                                    'phase_ramp_audit': phase_pins['ramp_audit']['sha256']},
            'release_reviews_sha256': {
                key: manifest['blocks'][rv['block']]['pins'][rv['pin']]['sha256']
                for key, rv in (('wording_review', manifest['reviews']['wordingReview']),
                                ('adapter_binding_review', manifest['reviews']['adapterBindingReview']),
                                ('wearable_cca_definition', manifest['reviews']['wearableCcaDefinition']))},
            'parent_release': {'release_id': PARENT_RELEASE,
                               'sha256': manifest['published']['route3']['sha256']},
            'released_files_unchanged': ['questions-in-language-update.json', 'deployment-topics.json', 'mvp.json'],
        },
    }
    require(docs['route3']['release_id'] == PARENT_RELEASE and cca_pins['route3']['sha256']
            == manifest['published']['route3']['sha256'] == manifest['blocks']['query']['pins']['parent']['sha256']
            and cca_pins['dry_vs_wet']['sha256'] == manifest['published']['deploymentTopics']['sha256'],
            'the released files the blocks read are not the ones the manifest publishes beside')

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 4, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    confidence_absent(payload)
    validate_public(payload)
    published = set(numbers(payload))
    leaked = [v for v in withheld_values(docs) if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    return payload


def inputs_available():
    """Whether the pinned inputs are on this machine. The research folders are local-only, so a clone checks the served
    file against the committed export audit's hash; only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all(location(r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_new_ssvep_frequencies_export
    return audit_new_ssvep_frequencies_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
