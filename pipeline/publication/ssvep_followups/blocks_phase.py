"""The phase blocks of the new-SSVEP-frequencies release: cards 3 and 4 (phase jitter, phase ramp).

Two audited route 3 follow-ups on the same BETA cohort, read from their own files and turned into study blocks for
`new-ssvep-frequencies-update.json`, which the assembler of that file (B4) puts under `studies`:

- `phase_jitter`: the complex-spectrum FiLM head with the phase-carrying reference query, trained with a random
  common delay (0-125 ms, or up to one period of the training label's frequency), beside its no-delay control and the
  magnitude-reference head on the plain spectrum; one primary and five secondary contrasts, from the public export
  `exports/phase-jitter-v1.json`. The canonical score it reproduces is pinned by hash and checked equal, never served.
- `phase_ramp`: six head/query cells trained with a random phase ramp of up to one stimulus period, their six
  no-ramp controls, the two plain-spectrum comparators and CCA; six primary and seven secondary contrasts, from the
  sealed score `review/final-trx/score/main.private.json`, with the release status taken from `audit/aggregate.json`.

Every input is pinned by SHA-256 (PINS) and refused unless it is byte for byte the pinned file and the study's
reviews and receipts bind that hash. Every number is the source's own double: nothing is rounded, rescaled or
recomputed, and units stay fractions. The pinned protocols and receipts carry private storage paths, so they are read
and checked here, never copied; only named fields are selected from them.

The declared edits (plan section 3, and the phase wording review, R5), applied to a working copy of each source
before anything is selected, each refused unless it finds exactly what it names (EDITS):
- jitter: the misread one-period reference block and the operator `release_governed_by` path are removed;
- ramp: the pre-audit status, the misread reference flags and the `interpretation` string are removed (its clauses
  survive as limitation keys, M3 included), and every CCA level's `seeds: 1` becomes "no training";
- ramp: `thread_bet` is added, `{held8_threshold, source_url}` (M5, M7), read from the thread as the protocols
  record it; it appears in this block only.

A block is a mapping with the fields of the B1 blocks (see blocks_query.py):
- `source_sha256`, `review_sha256` (the interpretation review that binds the source), `provenance_review_sha256`,
  `wording_review_sha256` (R5), and `canonical_score_sha256` (jitter) or `audit_sha256` (ramp);
- `interval_method`: `{method, draws, seed, level, conditional_on}`, exactly as R5 M3 words it, checked against the
  source and both protocols;
- `design`: the dataset, the arms or cells with their training delay, the endpoints, and the delay rule;
- `levels`: `{id: {estimate, interval, unit, people, seeds, origin}}`; an id is `<cell>/<endpoint>`, with the
  source's own cell spelling (`COMMON-125MS`, `FS-REF`, `L0c-FS-REF`, `L0-FS-REF`, `CCA`); `origin` is `new`,
  `reused_ref`, `reused_ref2` or `reused_parent`, and every reused level is checked against the study it comes from;
- `contrasts`: `{id: {role, left, right, estimate, interval, unit, people, seeds, flags}}`; `role` is `primary` or
  `secondary` (jitter: one primary; ramp: six), `flags` are the source's flags as it states them;
- `undefined`: `[{level, reason}]`, the held-out endpoints the question-number cells cannot have, absent from `levels`;
- `not_run`: `[{item, run_in}]`, the protocol's deferred list, with the study of this release that later ran the item;
- `checks`: the audits', gates' and reviews' pass or fail and counts;
- `limitations_keys`: keys of the limitations the page states (LIMITATION_SOURCES gives each key's source sentence);
- `display_names`, `export_codes`: as in B1; an export code is `#<JSON pointer>` into the study's own source.
Kept verbatim on request of R5 (section 6): jitter `caveats` (seven strings) and `intervals`; ramp `multiplicity`
and `undefined_metrics`. The ramp block also carries `thread_bet`.

    python3 pipeline/publication/ssvep_followups/blocks_phase.py      # builds and prints the counts; writes nothing
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:                      # run directly rather than imported from the pipeline
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public               # noqa: E402

PROJECT = PUBLICATION.parents[1]
LOCAL = PUBLICATION / 'local_paths.json'                   # optional `researchRoot`: where this machine keeps research/

# ---------------------------------------------------------------------------- pinned inputs
# Paths are relative to the project; `research/...` resolves under `researchRoot` when local_paths.json sets one.
JIT = 'research/decision_route3_phase_jitter_20261015'
RAMP = 'research/decision_route3_phaseaug_20261016'
PINS = {
    'jitter_export': {'path': f'{JIT}/exports/phase-jitter-v1.json',
                      'sha256': '7232ce0000738b25a3e7eb95a0b82a2999c22e55e4b6673ff822d80c31535ef3'},
    'jitter_score': {'path': f'{JIT}/exports/phase-jitter-aggregate.json',        # canonical score, by hash only
                     'sha256': '74eb6de8524588e5b9ac7854973b87bac31a9a977ea96cda6c00f9ca8eb59bdc'},
    'jitter_protocol': {'path': f'{JIT}/protocol.json',
                        'sha256': '8dbe7f458d14631bc111b6439bf55ce5deed6d11c1c3e0fb5ad4bbde729e1a71'},
    'jitter_interpretation': {'path': f'{JIT}/review/final-interpretation-review.json',
                              'sha256': 'ca2e5db29b5cc760f67869368248d5b1217e8ead964002fe82331892b51059fa'},
    'jitter_provenance': {'path': f'{JIT}/review/final-provenance-review.json',
                          'sha256': 'ad6350346bdeff29067b06113df853a70e02e82197888a8f0cbbdb92ea65f5c7'},
    'jitter_release': {'path': f'{JIT}/state/release-status.json',
                       'sha256': '776efd6aa26b6702c78986733ebaf292309d4e8c0548a3c8073e2298bf5d8a56'},
    'jitter_audit': {'path': f'{JIT}/review/completed-run/aggregate.json',
                     'sha256': '67c3974e1345f11cb23e2fb3ce9a346ec61f60a29f5b5b91aa9478c68d7381c4'},
    'jitter_canary': {'path': f'{JIT}/review/completed-run/canary-gate.json',
                      'sha256': '019c026a4d779d76f731ba2946688aeeaa4b617c28718fea7224c606dbdc4128'},
    'jitter_bridge': {'path': f'{JIT}/review/completed-run/bridge-gate.json',
                      'sha256': 'ea1197ce7ede964a161db9faf50829d8fb3001961a2dcdabc65560fcf56ee980'},
    'ramp_score': {'path': f'{RAMP}/review/final-trx/score/main.private.json',
                   'sha256': '7498eb5cf79d2f807ab6e12584fdaa76c3542a703701c7fc9e0e31a1164bc8d2'},
    'ramp_audit': {'path': f'{RAMP}/review/final-trx/audit/aggregate.json',
                   'sha256': '41ff565b37247a8842c947e98769aefc058602d9bd51b2550015c0c963e12fb6'},
    'ramp_protocol': {'path': f'{RAMP}/protocol.json',
                      'sha256': 'd28a6e3cdf0928fa7f55c9dc19b335a4eb3e43180cb1f31903c6a0f41c916f6a'},
    'ramp_interpretation': {'path': f'{RAMP}/review/release-interpretation-review.json',
                            'sha256': 'af55b077127724fa9537e07c7f259ea8623c6d6322b654e0dd7d2cdc4efadeaa'},
    'ramp_provenance': {'path': f'{RAMP}/review/release-provenance-review.json',
                        'sha256': '942ad85d8a4aca6dfd334081aebd02876b80e9e569a8ef1259754d05621e54f3'},
    'ramp_release': {'path': f'{RAMP}/review/release-status.json',
                     'sha256': '4044b7668d440cf84faffd25386603d6428ab1ab0f5b7c9cd3e27f22f93ce3ee'},
    'ramp_canary': {'path': f'{RAMP}/review/canary-gate.json',
                    'sha256': '35c58ffe467dfd7b6d4138793bafa537283e70c1f3cd390f150bb9d272271198'},
    # The studies the reused levels come from (the same bytes B1 pins), and the study that ran a deferred item.
    'ref_export': {'path': 'research/decision_route3_ref_20261013/Reference Spectrum Query Audited Results.json',
                   'sha256': '211510622bec8320d77d71074a42ad1b3299958a5629e11f480a1161ebccce64'},
    'ref2_export': {'path': 'research/decision_route3_ref2_20261014/exports/final-aggregate-evidence.json',
                    'sha256': 'a0df66fc8e9f049936c00179699935d5bec79a2923459273626fa8207a318763'},
    'cca_adapter_export': {'path': 'research/decision_route3_cca_adapter_20261015/exports/'
                                   'CCA Adapter Aggregate Results.json',
                           'sha256': '6f68114e4d431beb4903f68e3e2d4549da825d8f94d2ff3a776e368a7b3dca2b'},
    # R5, the wording re-confirmation whose corrections these blocks apply (Markdown, read as text).
    'wording_review': {'path': 'research/publication_review_20261020/reviews/phase-wording-review.md',
                       'sha256': '5c019b411714cbeaf7acff715326e2e938b67d101e06c10b7c70fa1e5eebca6c', 'text': True},
}
SOURCE_OF = {'phase_jitter': 'jitter_export', 'phase_ramp': 'ramp_score'}
REVIEW_OF = {'phase_jitter': 'jitter_interpretation', 'phase_ramp': 'ramp_interpretation'}
PROVENANCE_OF = {'phase_jitter': 'jitter_provenance', 'phase_ramp': 'ramp_provenance'}

STUDIES = ('phase_jitter', 'phase_ramp')
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'interval_method', 'levels', 'contrasts', 'undefined', 'not_run',
                'checks', 'limitations_keys', 'display_names', 'export_codes')
EXTRA_FIELDS = {
    'phase_jitter': ('provenance_review_sha256', 'wording_review_sha256', 'canonical_score_sha256', 'design',
                     'caveats', 'intervals'),
    'phase_ramp': ('provenance_review_sha256', 'wording_review_sha256', 'audit_sha256', 'design', 'multiplicity',
                   'undefined_metrics', 'thread_bet'),
}
ENDPOINTS = ('u8', 'seen_ba', 'm8', 'nn8', 'u3', 'cost')
HELD_OUT_ENDPOINTS = ('u8', 'u3', 'cost')     # what a fixed set of seen outputs cannot have (cost = u8 - m8)
DIFFERENCE_ENDPOINTS = {'cost'}
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
NO_TRAINING = 'no training'
SEED, DRAWS, LEVEL = 20261007, 2000, 0.95
TOL = 1e-12                  # a contrast against the difference of its levels, a cost against u8 - m8
REUSE_TOL = 1e-15            # a reused level against the study it comes from (the jitter export differs by 1 ulp)

# R5 M3, word for word: the interval method of both blocks, with the clause the ramp `interpretation` drop would lose.
INTERVAL_METHOD = {'method': 'hierarchical paired bootstrap', 'draws': DRAWS, 'seed': SEED, 'level': LEVEL,
                   'conditional_on': 'fixed person folds and three training seeds; five fixed rotations averaged first'}

# R5 M5 and M7: the bet as the thread states it, with the plain post URL (no comment anchor, no name, no confidence).
THREAD_POST = 'https://huggingface.co/posts/Twu31/109502481720473'
THREAD_BET_KEYS = ('held8_threshold', 'source_url')

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
DISPLAY_NAMES = {
    'ID': 'question number',
    'NUM': 'numeric code',
    'REF': 'reference spectrum',
    'REFc-0': 'reference with stimulus phase',
    'L0': 'plain spectrum',
    'L0c': 'complex spectrum',
    'FS': 'FiLM head',
    'MATCH': 'matching head',
    'CCA': 'CCA (no training)',              # the name key's CCA-RAW; these sources spell the same scorer CCA
    # Not in the name key. Worded from the card 3 lead as R5 section 5 corrects it.
    'COMMON-125MS': '0–125 ms delay',
    'COMMON-ONE-PERIOD': 'one-period delay',
}
NAME_KEY_ALIASES = {'CCA': 'CCA-RAW'}
NOT_IN_NAME_KEY = ('COMMON-125MS', 'COMMON-ONE-PERIOD')
DELAYS = ('COMMON-125MS', 'COMMON-ONE-PERIOD')

# ---------------------------------------------------------------------------- the two designs
# jitter export arm -> (level cell, features, head, query, origin)
JITTER_ARMS = {
    'A': ('COMMON-125MS', 'L0c', 'FS', 'REFc-0', 'new'),
    'B': ('COMMON-ONE-PERIOD', 'L0c', 'FS', 'REFc-0', 'new'),
    'C': ('L0c-FS-REFc-0', 'L0c', 'FS', 'REFc-0', 'reused_ref2'),
    'M': ('L0-FS-REF', 'L0', 'FS', 'REF', 'reused_ref'),
}
JITTER_ENDPOINTS = ('u8', 'seen_ba')
JITTER_ROLES = {'single primary': 'primary', 'descriptive secondary': 'secondary'}
JITTER_CONTRASTS = ('P1', 'S1', 'S2', 'S3', 'S4', 'S5')
JITTER_P1_FLAGS = ('positive_primary', 'meaningful_primary')     # the canonical score's own flags for P1

RAMP_CELLS = ('FS-REF', 'FS-NUM', 'FS-ID', 'MATCH-REF', 'MATCH-NUM', 'MATCH-ID')
RAMP_COMPARATORS = ('L0c-FS-REF', 'L0c-FS-NUM', 'L0c-FS-ID', 'L0c-MATCH-REF', 'L0c-MATCH-NUM', 'L0c-MATCH-ID',
                    'L0-FS-REF', 'L0-FS-NUM', 'CCA')
RAMP_ID_CELLS = ('FS-ID', 'MATCH-ID', 'L0c-FS-ID', 'L0c-MATCH-ID')
RAMP_CONTRASTS = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7')
RAMP_FLAGS = ('difference', 'equivalent_within_2pp', 'noninferiority_to_CCA')
RAMP_AUGMENTATION = 'COMMON-ONE-PERIOD'
REF_ORIGIN = {'new': 'reused_ref', 'reused_parent': 'reused_parent'}   # REF's origin of a level -> its origin here

# ---------------------------------------------------------------------------- declared edits
# The value the dropped reference blocks name, written as a ratio so the figure itself is never spelled here.
DROPPED_REFERENCE = 11 / 20
REFERENCE_FLAGS = {'point_meets': False, 'above_reference': False, 'below_reference': True}
RAMP_INTERPRETATION = ('Fixed-split BETA recipe; conditional bootstrap uncertainty; phase ramp approximates a time '
                       'shift; no phase-alone or sole-head diagnosis.')


def pointer(*tokens):
    """An RFC 6901 JSON pointer from its reference tokens (the level keys contain '/')."""
    return ''.join('/' + str(t).replace('~', '~0').replace('/', '~1') for t in tokens)


EDITS = {
    'phase_jitter': (
        ('remove', '/one_period_prediction', {'reference': DROPPED_REFERENCE} | REFERENCE_FLAGS, None),
        ('remove', '/release_governed_by', '../state/release-status.json', None),
    ),
    'phase_ramp': (
        ('remove', '/status', 'scored_pending_release_audit', None),
        ('remove', '/fifty_five_reference', {'FS-REF': REFERENCE_FLAGS, 'MATCH-REF': REFERENCE_FLAGS}, None),
        ('remove', '/interpretation', RAMP_INTERPRETATION, None),
    ) + tuple(('replace', pointer('levels', f'CCA/{e}', 'seeds'), 1, NO_TRAINING) for e in ENDPOINTS),
}
DROPPED_KEYS = {'phase_jitter': ('one_period_prediction', 'release_governed_by'),
                'phase_ramp': ('status', 'fifty_five_reference', 'interpretation')}
# Field names the blocks never use anywhere (plan section 4.2 B2): `status` is dropped from the score's top level
# only, and stays the name of each receipt's pass or fail under `checks`.
NEVER_KEYS = frozenset(('one_period_prediction', 'release_governed_by', 'fifty_five_reference', 'interpretation'))

# ---------------------------------------------------------------------------- limitations
# key -> (pinned input, JSON pointer into its original bytes, a phrase the sentence there must contain). The page
# writes each limitation in its own words; the key says which source sentence it states. No cited sentence may carry
# the dropped reference figure, so none can be lifted onto the page with it.
LIMITATION_SOURCES = {
    'phase_jitter': {
        'delay_on_windowed_coefficients': ('jitter_export', '/caveats/0', 'already windowed coefficients'),
        'one_period_range_uses_training_label': ('jitter_export', '/caveats/1', 'depends on the assigned training'),
        'queries_and_test_windows_unchanged': ('jitter_export', '/caveats/2', 'all reference queries remain unchanged'),
        'phase_is_label_information': ('jitter_export', '/caveats/3', 'label-correlated information'),
        'no_chance_or_phase_irrelevance_claim': ('jitter_export', '/caveats/4', 'chance equivalence'),
        'magnitude_head_differs_in_recipe': ('jitter_export', '/caveats/5', 'feature/query recipe and capacity'),
        'exposed_beta_not_external': ('jitter_export', '/caveats/6', 'not a new external validation'),
        'conditional_intervals': ('jitter_export', '/intervals/conditional_on', 'three training seeds'),
        'secondary_unadjusted': ('jitter_export', '/intervals/secondary_intervals', 'unadjusted for multiplicity'),
        'fixed_range_not_uniform_phase': ('jitter_protocol', '/arms/0/interpretation',
                                          'not a uniform fundamental phase distribution'),
        'randomized_label_check_limit': ('jitter_protocol', '/canary/interpretation', 'does not prove absence'),
        'recipe_specific_result': ('jitter_interpretation', '/interpretation/scope', 'do not establish phase irrelevance'),
    },
    'phase_ramp': {
        'percent_and_points': ('ramp_interpretation', '/required_limits/0', 'percentage points denote a difference'),
        'different_tasks_use_m8': ('ramp_interpretation', '/required_limits/1', 'candidate sets differ'),
        'id_held_out_undefined': ('ramp_interpretation', '/required_limits/2', 'undefined for ID'),
        'all_cells_and_contrasts': ('ramp_interpretation', '/required_limits/3', 'All six cells and all 13 contrasts'),
        'conditional_intervals': ('ramp_interpretation', '/required_limits/4',
                                  'conditional on fixed source folds and three seeds'),
        'cca_one_seed_axis_s7_only': ('ramp_interpretation', '/required_limits/5', 'Only S7'),
        'feature_recipe_confound': ('ramp_interpretation', '/required_limits/6', 'normalization, dimension and capacity'),
        'reproducibility_not_replication': ('ramp_interpretation', '/required_limits/7',
                                            'not independent external replication'),
        'unadjusted_contrasts': ('ramp_score', '/multiplicity', 'no multiplicity correction'),
        'no_phase_alone_or_sole_head_diagnosis': ('ramp_score', '/interpretation',
                                                  'no phase-alone or sole-head diagnosis'),
        'phase_is_label_information': ('ramp_protocol', '/interpretation/0', 'valid label-correlated information'),
        'ramp_approximates_time_shift': ('ramp_protocol', '/interpretation/1', 'not literal raw recropping'),
        'harmonic_phases_coupled': ('ramp_protocol', '/interpretation/2', 'harmonic closure preserved'),
        'delay_uses_training_label': ('ramp_protocol', '/interpretation/3', 'Passing canaries does not prove'),
        'queries_and_test_windows_unchanged': ('ramp_protocol', '/interpretation/4', 'Queries remain fixed'),
        'heads_not_initialisation_matched': ('ramp_protocol', '/heads/initialization', 'initiallogits differ'),
        'near_zero_match_cost_is_not_transfer': ('ramp_interpretation', '/forbidden_causal_overclaims/5',
                                                 'MATCH held8 and m8 are both near chance'),
    },
}
# Where the sources state that a question-number cell has no held-out endpoint, and what they say there.
UNDEFINED_SOURCES = (
    ('ramp_protocol', '/inputs/query_variants/ID/scaling', 'no direct held-frequency queries'),
    ('ramp_protocol', '/analysis/endpoints/u8', 'undefined for ID'),
    ('ramp_interpretation', '/required_limits/2', 'never zero or chance-imputed'),
)
UNDEFINED_REASON = 'cannot_ask_unseen'        # B1's reason code: the route 3 file's own field, can_ask_unseen false

# The jitter protocol's deferred items that a later study of this release ran, and the codes that show it.
RUN_LATER = {
    'Same augmentation on FS-NUM': ('phase_ramp', ('FS-NUM',)),
    'MATCH head follow-up': ('phase_ramp', ('MATCH-REF', 'MATCH-NUM', 'MATCH-ID')),
    'CCA-derived features or residuals': ('cca_adapter', ('ADAPT-FS', 'RAW-RESIDUAL')),
}


# ---------------------------------------------------------------------------- helpers
def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    path = str(path)
    if Path(path).is_absolute():
        return Path(path)
    if path.startswith('research/'):
        return research_root() / path[len('research/'):]
    return PROJECT / path


def tokens(ptr):
    require(ptr == '' or ptr.startswith('/'), f'{ptr!r} is not a JSON pointer')
    return [t.replace('~1', '/').replace('~0', '~') for t in ptr[1:].split('/')] if ptr else []


def resolve(doc, ptr):
    cur = doc
    for t in tokens(ptr):
        if isinstance(cur, list):
            require(t.isdigit() and int(t) < len(cur), f'{ptr}: no item {t}')
            cur = cur[int(t)]
        else:
            require(isinstance(cur, dict) and t in cur, f'{ptr}: no field {t!r}')
            cur = cur[t]
    return cur


def same(a, b):
    """Equality that also matches types, so False never stands for 0 or 1 for True."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def apply_edits(doc, edits, label):
    """A copy of `doc` with the declared edits applied; each must find exactly the value it names."""
    out = copy.deepcopy(doc)
    for op, ptr, expected, new in edits:
        parts = tokens(ptr)
        require(parts, f'{label}: an edit cannot act on the whole document')
        head = resolve(out, pointer(*parts[:-1]))
        last = parts[-1]
        require(same(resolve(out, ptr), expected), f'{label}: {ptr} is not what the declared edit names')
        if op == 'remove':
            del head[last]
        elif op == 'replace':
            head[last] = new
        else:
            raise ValueError(f'{label}: unknown edit {op!r}')
    return out


def load(pins=None):
    """Every pinned input, refused unless it is byte for byte the pinned file. Returns ({name: doc}, {name: sha})."""
    pins = pins or PINS
    docs, digests = {}, {}
    for name, ref in pins.items():
        raw = location(ref['path']).read_bytes()
        digest = sha(raw)
        require(digest == ref['sha256'], f'{name}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
        docs[name] = raw.decode('utf-8') if ref.get('text') else json.loads(raw)
        digests[name] = digest
    return docs, digests


def inputs_available(pins=None):
    """Whether the pinned inputs are on this machine; the research folders are local, not in the repository."""
    return all(location(r['path']).exists() for r in (pins or PINS).values())


def interval(lo, hi, point, label, lower=0.0, upper=1.0):
    require(all(number(v) for v in (lo, hi, point)), f'{label}: not a finite interval')
    require(lower <= lo <= point <= hi <= upper, f'{label}: the interval does not hold its point')
    return [lo, hi]


def level(estimate, lo, hi, unit, people, seeds, origin, label):
    lower = -1.0 if unit == DIFFERENCE else 0.0
    return {'estimate': estimate, 'interval': interval(lo, hi, estimate, label, lower=lower), 'unit': unit,
            'people': people, 'seeds': seeds, 'origin': origin}


def bootstrap_of(obj, label):
    require((obj['draws'], obj['seed'], obj['level']) == (DRAWS, SEED, LEVEL), f'{label}: another bootstrap')
    require(obj.get('excluded_people', 0) == 0, f'{label}: excludes people')


def checked_contrast(levels, cid, left, right, estimate, label):
    require(left in levels and right in levels, f'{label}: {cid} compares levels this block does not hold')
    diff = levels[left]['estimate'] - levels[right]['estimate']
    require(abs(diff - estimate) <= TOL, f'{label}: {cid} is {estimate!r}, its levels differ by {diff!r}')


def reused(row, source, label):
    """A reused level against the level of the study it comes from: same interval, same point to REUSE_TOL."""
    require(abs(row['estimate'] - source[0]) <= REUSE_TOL and row['interval'] == list(source[1:]),
            f'{label}: not the level of the study it is reused from')


def ref_levels(docs):
    """REF's plain-spectrum levels, by this module's ids, as (point, lo, hi, origin)."""
    run = docs['ref_export']['results']['questions-in-language-ref']
    out = {}
    for name, lv in run['descriptive']['REF-ssvep-L0']['levels'].items():
        arm, endpoint = name.split(' ')
        lid = f'{arm}/{endpoint}' if arm in ('CCA', 'TEMPLATE') else f'L0-FS-{arm}/{endpoint}'
        out[lid] = (lv['estimate'], *lv['interval_95'], lv['origin'])
    return out


def ref2_levels(docs):
    return {lid: (lv['point'], lv['lo'], lv['hi']) for lid, lv in docs['ref2_export']['aggregate']['levels'].items()}


def codes_of(cells):
    """The codes a block's cells are made of: 'L0c-MATCH-REF' -> L0c, MATCH, REF; 'COMMON-125MS' -> itself."""
    out = []
    for cell in cells:
        if cell == 'CCA' or cell in DELAYS:
            parts = [cell]
        else:
            m = re.fullmatch(r'(?:(L0c|L0)-)?(FS|MATCH)-(REFc-0|REF|NUM|ID)', cell)
            require(m is not None, f'{cell}: not a cell id')
            parts = [p for p in m.groups() if p]
        out += [p for p in parts if p not in out]
    return out


def display_names(cells):
    codes = codes_of(cells)
    order = [c for c in DISPLAY_NAMES if c in codes]
    require(set(order) == set(codes), f'no display name for {sorted(set(codes) - set(order))}')
    return {c: DISPLAY_NAMES[c] for c in order}


def stated(docs, doc, ptr, phrase, label):
    text = resolve(docs[doc], ptr)
    require(isinstance(text, str) and phrase in text, f'{label}: {doc} {ptr} does not say {phrase!r}')
    return text


def limitations(study, docs):
    keys = []
    for key, (doc, ptr, phrase) in LIMITATION_SOURCES[study].items():
        text = stated(docs, doc, ptr, phrase, f'{study} limitation {key}')
        require('55' not in text, f'{study} limitation {key}: its source sentence carries the dropped figure')
        keys.append(key)
    return keys


def not_run(items):
    return [{'item': item, 'run_in': RUN_LATER[item][0] if item in RUN_LATER else None} for item in items]


PRIVATE = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/|trx|gal4|bci_arena',
                     re.IGNORECASE)
FORBIDDEN_KEY = re.compile(r'fifty|05{2}|prediction', re.IGNORECASE)      # R5 M7, the served-JSON key rule
VERSION_LABEL = re.compile(r'(?<![\w.])v\d+\b')


def scan(value, trail):
    """What the blocks never carry: the dropped reference (M7), pending statuses, private paths, names, versions."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(not FORBIDDEN_KEY.search(k), f'{trail}: a key {k!r} for the dropped reference')
            require(k not in NEVER_KEYS, f'{trail}: a {k!r} field, which the declared edits drop')
            require(k != 'thread_bet' or trail == '$.phase_ramp', f'{trail}: the bet belongs to the phase ramp only')
            scan(k, f'{trail}.<key>')
            scan(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scan(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require('pending' not in value.lower(), f'{trail}: a pending status string')
        require(not PRIVATE.search(value), f'{trail}: a private path or host')
        require('twu' not in value.replace(THREAD_POST, '').lower(), f'{trail}: a user name outside the thread URL')
        require('Jev' not in value, f'{trail}: a Jev line')
        require(not VERSION_LABEL.search(value), f'{trail}: a version label')
        require(re.fullmatch(r'[0-9a-f]{64}', value) or '55' not in value, f'{trail}: a 55 in the text')
    elif number(value):
        require(not (abs(value - DROPPED_REFERENCE) <= 1e-12 or abs(value - 100 * DROPPED_REFERENCE) <= 1e-9),
                f'{trail}: the dropped reference value')
    elif isinstance(value, float):
        raise ValueError(f'{trail}: not finite')


# ---------------------------------------------------------------------------- bindings between the pinned files
def check_bindings(docs, digests):
    jx, js = docs['jitter_export'], docs['jitter_score']
    ji, jp, jr = docs['jitter_interpretation'], docs['jitter_provenance'], docs['jitter_release']
    ja, jc, jb = docs['jitter_audit'], docs['jitter_canary'], docs['jitter_bridge']
    require(ji['status'] == jp['status'] == 'approved_for_aggregate_handoff' and ji['release_eligible'] is True
            and jp['release_eligible'] is True and ji['blocking_findings'] == [] == jp['blocking_findings'],
            'jitter: a final review did not approve')
    require(ji['public_export_sha256'] == digests['jitter_export'], 'jitter: the review binds other export bytes')
    for name, file in (('jitter_score', 'exports/phase-jitter-aggregate.json'), ('jitter_protocol', 'protocol.json'),
                       ('jitter_audit', 'review/completed-run/aggregate.json'),
                       ('jitter_canary', 'review/completed-run/canary-gate.json'),
                       ('jitter_bridge', 'review/completed-run/bridge-gate.json'),
                       ('jitter_provenance', 'review/final-provenance-review.json')):
        require(ji['reviewed_sha256'][file] == digests[name], f'jitter: the interpretation review binds another {file}')
    for name, file in (('jitter_export', 'exports/phase-jitter-v1.json'), ('jitter_score',
                       'exports/phase-jitter-aggregate.json'), ('jitter_protocol', 'protocol.json'),
                       ('jitter_interpretation', 'review/final-interpretation-review.json'),
                       ('jitter_provenance', 'review/final-provenance-review.json')):
        require(jr['artifact_sha256'][file] == digests[name], f'jitter: the release receipt binds another {file}')
    require(jr['status'] == 'audited_complete_aggregate_handoff_ready' and jr['release_eligible'] is True
            and jr['unresolved_scientific_or_release_gates'] == [], 'jitter: the release receipt is not complete')
    require(jp['protocol_sha256'] == digests['jitter_protocol'] and jp['numerical_score_sha256']
            == digests['jitter_score'] and jp['aggregate_sha256'] == digests['jitter_audit'],
            'jitter: the provenance review binds other bytes')
    for file, name in (('review/completed-run/canary-gate.json', 'jitter_canary'),
                       ('review/completed-run/bridge-gate.json', 'jitter_bridge')):
        require(jp['local_receipt_sha256'][file] == digests[name], f'jitter: the provenance review binds another {file}')
    require('decision_route3_ref2_20261014' in jp['post_completion_remote_verification']['historical_C']
            and 'decision_route3_ref_20261013' in jp['post_completion_remote_verification']['historical_M'],
            'jitter: the controls are not the REF2 and REF fits')
    require(jx['provenance']['protocol_sha256'] == digests['jitter_protocol']
            and jx['provenance']['canonical_score_sha256'] == digests['jitter_score'],
            'jitter: the export names other protocol or score bytes')
    require(ja['status'] == 'pass' and ja['release_eligible'] is True
            and ja['numerical_score_sha256'] == digests['jitter_score'] == ja['numerical_summary']['numerical_score_sha256'],
            'jitter: the numerical audit did not pass on the canonical score')
    require(js['independently_audited'] is True, 'jitter: the canonical score is not independently audited')
    require(jc['freeze_sha256'] == jb['freeze_sha256'] == ja['freeze_sha256'] == js['freeze_sha256']
            == jx['provenance']['freeze_sha256'] and ja['seals']['canary'] == jc['seal_sha256']
            and ja['seals']['bridge'] == jb['seal_sha256'] and ja['seals']['main'] == js['seal_sha256']
            == jx['provenance']['main_seal_sha256'], 'jitter: a gate or the score belongs to another freeze or seal')

    rs, ra, rp = docs['ramp_score'], docs['ramp_audit'], docs['ramp_protocol']
    ri, rv, rr, rc = docs['ramp_interpretation'], docs['ramp_provenance'], docs['ramp_release'], docs['ramp_canary']
    require(ra['status'] == 'pass' and ra['release_eligible'] is True and ra['numerical_score_sha256']
            == digests['ramp_score'] == ra['numerical_summary']['numerical_score_sha256'],
            'ramp: the numerical audit did not pass on this score')
    require(ra['freeze_sha256'] == rs['freeze_sha256'] == rr['freeze_sha256'] and ra['seals']['main'] == rs['seal_sha256'],
            'ramp: the audit binds another freeze or seal')
    require(rp['experiment_id'] == 'decision_route3_phaseaug_20261016' and rv['evidence_sha256']['execution-freeze.json']
            == rs['freeze_sha256'], 'ramp: the protocol or the reviewed freeze is another run\'s')
    require(ri['status'] == 'approved_for_aggregate_release' and ri['inputs']['score']['sha256'] == digests['ramp_score']
            and ri['inputs']['aggregate']['sha256'] == digests['ramp_audit']
            and ri['inputs']['protocol']['sha256'] == digests['ramp_protocol'],
            'ramp: the interpretation review did not approve these bytes')
    require(all(ri['checks'][k] is True for k in ('six_cells_present', 'thirteen_contrasts_exactly_match_protocol',
                                                  'six_primary_seven_secondary', 'audit_pass_and_release_eligible')),
            'ramp: an interpretation check did not pass')
    require(rv['status'] == 'approved_for_aggregate_release' and rv['blocking_findings'] == []
            and rv['release_hold'] is None, 'ramp: the provenance review did not approve')
    for file, name in (('score/main.private.json', 'ramp_score'), ('audit/aggregate.json', 'ramp_audit'),
                       ('state/canary-gate.json', 'ramp_canary')):
        require(rv['final_receipts_sha256'][file] == digests[name], f'ramp: the provenance review binds another {file}')
    require(rv['evidence_sha256']['protocol.json'] == digests['ramp_protocol'], 'ramp: provenance protocol bytes')
    require(rr['status'] == 'audited_complete' and rr['release_eligible'] is True
            and rr['score_sha256'] == digests['ramp_score'] and rr['protocol_sha256'] == digests['ramp_protocol']
            and rr['reviews']['provenance']['sha256'] == digests['ramp_provenance']
            and rr['reviews']['interpretation']['sha256'] == digests['ramp_interpretation'],
            'ramp: the release receipt binds other bytes')
    require(rc['status'] == 'pass' and rc['freeze_sha256'] == rs['freeze_sha256'] and ra['seals']['canary']
            == rc['seal_sha256'], 'ramp: the randomized-label gate is not this run\'s')

    wording = docs['wording_review']
    require('**Confirmed, with seven required corrections' in wording, 'R5: the wording review did not confirm')
    for name in ('jitter_export', 'jitter_score', 'ramp_score', 'ramp_audit', 'jitter_canary', 'ramp_canary',
                 'jitter_protocol', 'ramp_protocol', 'jitter_interpretation', 'ramp_interpretation'):
        require(digests[name] in wording, f'R5: the wording review did not check {name}')
    require(f'`{THREAD_POST}`' in wording and INTERVAL_METHOD['conditional_on'] in wording,
            'R5: the thread URL or the interval clause is not the reviewed one')


def thread_bet(docs):
    """The bet as the thread record states it (M5, M7): the threshold and the plain post URL, nothing else."""
    quote = docs['ramp_protocol']['source_evidence']['comment_quote']
    m = re.search(r'\bunseen clears (\d+)\b', quote)
    require(m is not None, 'ramp protocol: the comment does not state the held-out threshold')
    threshold = int(m.group(1)) / 100
    require(threshold == 0.39, 'ramp protocol: the threshold is not the thread\'s 39')
    require('tested against the paired39.002976% historical control'
            in docs['ramp_protocol']['source_evidence']['interpretation'],
            'ramp protocol: the commitment is not tested against the plain-spectrum control')
    url = docs['jitter_protocol']['comment']['url']
    require(url.split('#', 1)[0] == THREAD_POST, 'jitter protocol: the comment is not on the thread post')
    return {'held8_threshold': threshold, 'source_url': THREAD_POST}


# ---------------------------------------------------------------------------- phase jitter
def build_jitter(docs, digests):
    src = apply_edits(docs['jitter_export'], EDITS['phase_jitter'], 'jitter')
    for k in DROPPED_KEYS['phase_jitter']:
        require(k not in src, f'jitter: {k} survived its declared edit')
    score, protocol = docs['jitter_score'], docs['jitter_protocol']
    intervals = src['intervals']
    require((intervals['confidence'], intervals['bootstrap_draws']) == (LEVEL, DRAWS)
            and intervals['conditional_on'].lower().rstrip('.')
            == 'fixed folds and three training seeds; five fixed rotations averaged first',
            'jitter: the export states another interval method')
    boot = protocol['statistics']['bootstrap']
    require((boot['replicates'], boot['seed']) == (DRAWS, SEED) and 'person indices first' in boot['draw_order']
            and 'Conditional on the fixed source folds and three training seeds' in boot['scope'],
            'jitter: the protocol states another bootstrap')

    levels, codes, design_arms = {}, {}, []
    require([a['id'] for a in src['arms']] == list(JITTER_ARMS), 'jitter: arms')
    reuse_ref, reuse_ref2 = ref_levels(docs), ref2_levels(docs)
    protocol_arms = {a['id']: a for a in protocol['arms']}
    for i, arm in enumerate(src['arms']):
        cell, features, head, query, origin = JITTER_ARMS[arm['id']]
        require(arm['name'] == cell or arm['name'].startswith(cell + ' '), f'jitter: arm {arm["id"]} is {arm["name"]!r}')
        require(arm['historical_reuse'] is (origin != 'new'), f'jitter: arm {arm["id"]} reuse')
        require(set(arm['metrics']) == set(JITTER_ENDPOINTS), f'jitter: arm {arm["id"]} endpoints')
        for e in JITTER_ENDPOINTS:
            m = arm['metrics'][e]
            bootstrap_of(m, f'jitter {arm["id"]}/{e}')
            lid = f'{cell}/{e}'
            row = level(m['point'], m['lo'], m['hi'], PROPORTION, m['people'], m['seeds'], origin, f'jitter {lid}')
            require(row['people'] == 70 and row['seeds'] == 3, f'jitter: {lid} people or seeds')
            # The export is the canonical score, to the last bit.
            canon = score['levels'][f'{arm["id"]}/{e}']
            require(same(canon, m), f'jitter: {lid} is not the canonical score')
            if origin == 'reused_ref2':
                reused(row, reuse_ref2[lid], f'jitter {lid}')
            elif origin == 'reused_ref':
                reused(row, reuse_ref[lid][:3], f'jitter {lid}')
                require(reuse_ref[lid][3] == 'new', f'jitter: {lid} is not a REF level')
            levels[lid], codes[lid] = row, ['#' + pointer('arms', i, 'metrics', e)]
        entry = {'arm': arm['id'], 'cell': cell, 'features': features, 'head': head, 'query': query,
                 'historical_reuse': arm['historical_reuse']}
        if arm['id'] in protocol_arms:          # the two delay arms: their delay, as the protocol defines it
            p = protocol_arms[arm['id']]
            require(p['name'] == cell, f'jitter protocol: arm {arm["id"]} is {p["name"]!r}')
            entry |= {'training_delay_seconds': p['tau_seconds'],
                      'delay_uses_training_label': p['uses_training_labels_for_augmentation']}
        else:                                    # the two controls were trained without any delay
            entry |= {'training_delay_seconds': None, 'delay_uses_training_label': None}
        design_arms.append(entry)
    require(set(protocol_arms) == {'A', 'B'} and protocol['historical_control']['cell'] == 'L0c-FS-REFc-0'
            and 'unchanged L0c-FS-REFc-0 head' in protocol['scope']
            and 'arm="REFc-0"' in protocol['model']['builder'] and 'head_kind="FS"' in protocol['model']['builder']
            and protocol['model']['parameters']['total'] == src['model']['parameters']
            and src['model']['trained_from_scratch'] is True,
            'jitter protocol: the delay arms are not the complex-spectrum FiLM head with the phase-carrying query')
    require(protocol_arms['A']['tau_seconds'] == '0.125*u' and protocol_arms['A'][
            'uses_training_labels_for_augmentation'] is False and protocol_arms['B']['tau_seconds']
            == 'u/f_assigned_source_label' and protocol_arms['B']['uses_training_labels_for_augmentation'] is True,
            'jitter protocol: the delay ranges are not 0-125 ms and one training-label period')

    contrasts = {}
    require(tuple(src['contrasts']) == JITTER_CONTRASTS and same(src['contrasts'], score['contrasts']),
            'jitter: the contrasts are not the canonical score\'s six')
    declared = {c['id']: c for c in protocol['statistics']['contrasts']}
    require(tuple(declared) == JITTER_CONTRASTS, 'jitter protocol: contrasts')
    for cid, c in src['contrasts'].items():
        bootstrap_of(c, f'jitter {cid}')
        require(c['role'] in JITTER_ROLES, f'jitter: {cid} role {c["role"]!r}')
        require((c['left'], c['metric']) == (declared[cid]['left'], declared[cid]['metric'])
                and (c['right'] == declared[cid]['right'] or (cid == 'S2' and c['right'] == 'M')),
                f'jitter: {cid} is not the declared contrast')
        left = f'{JITTER_ARMS[c["left"]][0]}/{c["metric"]}'
        right = f'{JITTER_ARMS[c["right"]][0]}/{c["metric"]}'
        checked_contrast(levels, cid, left, right, c['point'], 'jitter')
        flags = {'role_as_stated': c['role']}
        if cid == 'P1':
            flags |= {k: score[k] for k in JITTER_P1_FLAGS}
            require(all(isinstance(v, bool) for v in flags.values() if v is not c['role']), 'jitter: P1 flags')
        contrasts[cid] = {
            'role': JITTER_ROLES[c['role']], 'left': left, 'right': right, 'estimate': c['point'],
            'interval': interval(c['lo'], c['hi'], c['point'], f'jitter {cid}', lower=-1.0),
            'unit': DIFFERENCE, 'people': c['people'], 'seeds': c['seeds'], 'flags': flags,
        }
        codes[cid] = ['#' + pointer('contrasts', cid)]
    roles = [c['role'] for c in contrasts.values()]
    require(roles.count('primary') == 1 and contrasts['P1']['role'] == 'primary' and roles.count('secondary') == 5,
            'jitter: P1 is the single primary contrast, the other five secondary')

    canary, bridge, audit = docs['jitter_canary'], docs['jitter_bridge'], docs['jitter_audit']
    require(canary['status'] == 'pass' and canary['observed_fits'] == canary['expected_fits']
            == protocol['inventory']['randomized_label_canary_fits']
            and all(c['includes_zero'] is True for c in canary['cells'].values()), 'jitter: the randomized-label gate')
    require(bridge['status'] == 'pass' and bridge['bridge_fits'] == protocol['inventory']['baseline_bridge_fits'],
            'jitter: the bridge gate')
    summary = audit['numerical_summary']
    require(summary['status'] == 'pass' and tuple(summary['contrast_ids']) == JITTER_CONTRASTS
            and summary['bootstrap_draws'] == DRAWS, 'jitter: the numerical summary')
    augmentation = protocol['augmentation']

    return {
        'source_sha256': digests['jitter_export'],
        'review_sha256': digests['jitter_interpretation'],
        'provenance_review_sha256': digests['jitter_provenance'],
        'wording_review_sha256': digests['wording_review'],
        'canonical_score_sha256': digests['jitter_score'],
        'interval_method': dict(INTERVAL_METHOD),
        'design': {
            'dataset': dict(src['dataset']),
            'model': dict(src['model']),
            'endpoints': copy.deepcopy(src['metrics']),
            'arms': design_arms,
            'delay': {k: augmentation[k] for k in ('formula', 'draw', 'queries', 'inference')},
        },
        'levels': levels,
        'contrasts': contrasts,
        'undefined': [],
        'not_run': not_run(protocol['deferred']),
        'checks': {
            'audit': {k: audit[k] for k in ('status', 'release_eligible', 'main_models_reconstructed',
                                            'canary_models_reconstructed', 'fixed_independent_refits',
                                            'baseline_bridge_fits', 'total_optimizer_invocations', 'argmax_exact',
                                            'metric_bootstrap_atol')}
            | {'numerical_summary': {'status': summary['status'], 'contrasts': len(summary['contrast_ids']),
                                     'bootstrap_draws': summary['bootstrap_draws']}},
            'randomized_label': {'status': canary['status'], 'fits': canary['observed_fits'],
                                 'cells': len(canary['cells']),
                                 'cells_passed': sum(c['includes_zero'] is True for c in canary['cells'].values())},
            'bridge': {'status': bridge['status'], 'fits': bridge['bridge_fits']},
            'reviews': {'scientific': docs['jitter_interpretation']['status'],
                        'provenance': docs['jitter_provenance']['status']},
            'release': {'status': docs['jitter_release']['status'],
                        'release_eligible': docs['jitter_release']['release_eligible']},
            'export_equals_canonical_score': True,
        },
        'limitations_keys': limitations('phase_jitter', docs),
        'display_names': display_names([lid.split('/')[0] for lid in levels]),
        'export_codes': codes,
        'caveats': list(src['caveats']),
        'intervals': dict(intervals),
    }


# ---------------------------------------------------------------------------- phase ramp
def build_ramp(docs, digests):
    src = apply_edits(docs['ramp_score'], EDITS['phase_ramp'], 'ramp')
    for k in DROPPED_KEYS['phase_ramp']:
        require(k not in src, f'ramp: {k} survived its declared edit')
    protocol, audit = docs['ramp_protocol'], docs['ramp_audit']
    analysis = protocol['analysis']
    boot = analysis['bootstrap']
    require((boot['replicates'], boot['seed']) == (DRAWS, SEED) and 'person indices first' in boot['draw_order']
            and 'Conditional on the fixed source folds and three training seeds' in boot['scope']
            and 'Average fixed five rotations' in analysis['aggregation'],
            'ramp: the protocol states another bootstrap')
    require(tuple(c['id'] for c in protocol['cells']) == RAMP_CELLS and tuple(analysis['comparators'])
            == RAMP_COMPARATORS, 'ramp protocol: cells or comparators')
    require(src['independently_audited'] is True and src['main_fits'] == protocol['training']['main_fits'] == 630,
            'ramp: the score is not the audited 630 fits')

    reuse_ref, reuse_ref2 = ref_levels(docs), ref2_levels(docs)
    levels, codes, cells = {}, {}, []
    for lid, lv in src['levels'].items():
        cell, endpoint = lid.split('/')
        require(endpoint in ENDPOINTS, f'ramp: unknown endpoint {lid}')
        require(cell in RAMP_CELLS + RAMP_COMPARATORS, f'ramp: unknown cell {lid}')
        bootstrap_of(lv, f'ramp {lid}')
        if cell not in cells:
            cells.append(cell)
        unit = DIFFERENCE if endpoint in DIFFERENCE_ENDPOINTS else PROPORTION
        if cell in RAMP_CELLS:
            origin = 'new'
        elif cell.startswith('L0c-'):
            origin = 'reused_ref2'
        else:
            origin = REF_ORIGIN[reuse_ref[lid][3]]
        row = level(lv['point'], lv['lo'], lv['hi'], unit, lv['people'], lv['seeds'], origin, f'ramp {lid}')
        require(row['people'] == 70 and row['seeds'] == (NO_TRAINING if cell == 'CCA' else 3),
                f'ramp: {lid} people or seeds')
        if origin == 'reused_ref2':
            reused(row, reuse_ref2[lid], f'ramp {lid}')
        elif origin != 'new':
            reused(row, reuse_ref[lid][:3], f'ramp {lid}')
        levels[lid], codes[lid] = row, ['#' + pointer('levels', lid)]
    require(tuple(cells) == RAMP_CELLS + RAMP_COMPARATORS, 'ramp: the six cells and nine comparators, in order')
    for cell in cells:
        have = {e for e in ENDPOINTS if f'{cell}/{e}' in levels}
        require(have == (set(ENDPOINTS) - set(HELD_OUT_ENDPOINTS) if cell in RAMP_ID_CELLS else set(ENDPOINTS)),
                f'ramp: {cell} has endpoints {sorted(have)}')
        if 'cost' in have:      # cost is u8 - m8, so the three agree
            diff = levels[f'{cell}/u8']['estimate'] - levels[f'{cell}/m8']['estimate']
            require(abs(diff - levels[f'{cell}/cost']['estimate']) <= TOL, f'ramp: {cell} cost')
    require(len(levels) == 78, 'ramp: not the 78 scored levels')

    undefined_metrics = src['undefined_metrics']
    require(same(undefined_metrics, {c: list(HELD_OUT_ENDPOINTS) for c in RAMP_ID_CELLS}),
            'ramp: the undefined endpoints are not ID held-out, u3 and cost')
    require(same(docs['ramp_interpretation']['checks']['id_undefined_endpoints_preserved'], undefined_metrics),
            'ramp: the interpretation review preserved other undefined endpoints')
    for doc, ptr, phrase in UNDEFINED_SOURCES:
        stated(docs, doc, ptr, phrase, 'ramp undefined')

    contrasts = {}
    declared = {c['id']: c for c in analysis['contrasts']}
    require(tuple(src['contrasts']) == RAMP_CONTRASTS == tuple(declared), 'ramp: not the thirteen declared contrasts')
    require(tuple(audit['numerical_summary']['contrast_ids']) == RAMP_CONTRASTS, 'ramp: the audit\'s contrasts')
    for cid, c in src['contrasts'].items():
        bootstrap_of(c, f'ramp {cid}')
        d = declared[cid]
        require((c['left'], c['right'], c['metric'], c['role']) == (d['left'], d['right'], d['metric'], d['role']),
                f'ramp: {cid} is not the declared contrast')
        left, right = f'{c["left"]}/{c["metric"]}', f'{c["right"]}/{c["metric"]}'
        checked_contrast(levels, cid, left, right, c['point'], 'ramp')
        contrasts[cid] = {
            'role': c['role'], 'left': left, 'right': right, 'estimate': c['point'],
            'interval': interval(c['lo'], c['hi'], c['point'], f'ramp {cid}', lower=-1.0),
            'unit': DIFFERENCE, 'people': c['people'], 'seeds': c['seeds'],
            'flags': {k: c[k] for k in RAMP_FLAGS},
        }
        codes[cid] = ['#' + pointer('contrasts', cid)]
    roles = [c['role'] for c in contrasts.values()]
    require(roles == ['primary'] * 6 + ['secondary'] * 7, 'ramp: P1-P6 primary, S1-S7 secondary')
    require(not any(c['flags']['equivalent_within_2pp'] for c in contrasts.values())
            and contrasts['S7']['flags']['noninferiority_to_CCA'] is False
            and [cid for cid, c in contrasts.items() if c['right'] == 'CCA/u8'] == ['S7'],
            'ramp: S7 is the only CCA contrast and fails non-inferiority; nothing is equivalent within 2 points')
    require(src['multiplicity'] == 'Six primary and seven secondary paired contrasts; no multiplicity correction.',
            'ramp: the multiplicity statement')

    canary, prov = docs['ramp_canary'], docs['ramp_provenance']['final_verification']
    require(canary['status'] == 'pass' and canary['observed_fits'] == canary['expected_fits']
            == protocol['canary']['total_fits'] and len(canary['cells']) == prov['canary_gate']['gates'] == 10
            and all(c['includes_zero'] is True for c in canary['cells'].values()), 'ramp: the randomized-label gate')
    require(prov['bridge_gate']['pass'] is True and prov['bridge_gate']['fits'] == audit['baseline_bridge_fits'] == 18
            and prov['independent_refits']['pass'] is True and prov['reconstruction']['pass'] is True,
            'ramp: the bridge, refit or reconstruction verification')

    rule = protocol['augmentation']['rule']
    require('tau=u/f_assigned_source_label' in rule.replace(' ', ''), 'ramp protocol: the delay rule')
    design_cells = []
    for c in protocol['cells']:
        require(c['augmentation'] == RAMP_AUGMENTATION and c['level'] == 'L0c' and c['historical_id'] == f'L0c-{c["id"]}'
                and c['id'] == f'{c["head"]}-{c["arm"]}', f'ramp protocol: cell {c["id"]}')
        design_cells.append({'cell': c['id'], 'features': c['level'], 'head': c['head'], 'query': c['arm'],
                             'parameters': c['parameters']['total'], 'control': c['historical_id'],
                             'augmentation': c['augmentation']})
    endpoints = analysis['endpoints']
    require('chance1/8' in endpoints['u8'] and 'chance1/32' in endpoints['seen_ba'] and 'OTHER4 rotations'
            in endpoints['m8'], 'ramp protocol: the endpoints')
    augmentation = protocol['augmentation']

    return {
        'source_sha256': digests['ramp_score'],
        'review_sha256': digests['ramp_interpretation'],
        'provenance_review_sha256': digests['ramp_provenance'],
        'wording_review_sha256': digests['wording_review'],
        'audit_sha256': digests['ramp_audit'],
        'interval_method': dict(INTERVAL_METHOD),
        'design': {
            'dataset': {'name': protocol['dataset']['name'], 'people': protocol['dataset']['people'],
                        'targets': protocol['dataset']['targets'], 'windows': protocol['dataset']['windows'],
                        'person_folds': protocol['split']['people_folds'],
                        'frequency_rotations': len(protocol['split']['rotations']),
                        'training_seeds': len(protocol['split']['seeds'])},
            'cells': design_cells,
            'comparators': list(analysis['comparators']),
            'endpoints': {'u8': {'candidate_count': 8, 'chance': 1 / 8},
                          'seen_ba': {'candidate_count': 32, 'chance': 1 / 32},
                          'm8': {'candidate_count': 8, 'chance': 1 / 8}},
            'delay': {'training_delay_seconds': 'u/f_assigned_source_label', 'delay_uses_training_label': True}
                     | {k: augmentation[k] for k in ('formula', 'draw', 'queries', 'inference')},
        },
        'levels': levels,
        'contrasts': contrasts,
        'undefined': [{'level': f'{c}/{e}', 'reason': UNDEFINED_REASON}
                      for c in RAMP_ID_CELLS for e in HELD_OUT_ENDPOINTS],
        'not_run': not_run(protocol['deferred']),
        'checks': {
            'audit': {k: audit[k] for k in ('status', 'release_eligible', 'main_models_reconstructed',
                                            'canary_models_reconstructed', 'fixed_independent_refits',
                                            'baseline_bridge_fits', 'total_optimizer_invocations', 'argmax_exact',
                                            'metric_bootstrap_atol')}
            | {'numerical_summary': {'status': audit['numerical_summary']['status'],
                                     'contrasts': len(audit['numerical_summary']['contrast_ids']),
                                     'bootstrap_draws': audit['numerical_summary']['bootstrap_draws']}},
            'randomized_label': {'status': canary['status'], 'fits': canary['observed_fits'],
                                 'cells': len(canary['cells']),
                                 'cells_passed': sum(c['includes_zero'] is True for c in canary['cells'].values())},
            'bridge': {'status': 'pass', 'fits': prov['bridge_gate']['fits']},
            'reviews': {'scientific': docs['ramp_interpretation']['status'],
                        'provenance': docs['ramp_provenance']['status']},
            'release': {'status': docs['ramp_release']['status'],
                        'release_eligible': docs['ramp_release']['release_eligible']},
            'excluded_people': 0,
        },
        'limitations_keys': limitations('phase_ramp', docs),
        'display_names': display_names(cells + [RAMP_AUGMENTATION]),
        'export_codes': codes,
        'multiplicity': src['multiplicity'],
        'undefined_metrics': copy.deepcopy(undefined_metrics),
        'thread_bet': thread_bet(docs),
    }


# ---------------------------------------------------------------------------- both
def build_blocks(pins=None) -> dict:
    """The study blocks `phase_jitter` and `phase_ramp`, from the pinned inputs (PINS unless `pins` replaces them)."""
    docs, digests = load(pins)
    check_bindings(docs, digests)
    blocks = {'phase_jitter': build_jitter(docs, digests), 'phase_ramp': build_ramp(docs, digests)}
    adapter_arms = set(docs['cca_adapter_export']['arms'])
    for study, block in blocks.items():
        for item in block['not_run']:     # what a later study ran, its codes show
            if item['run_in'] == 'phase_ramp':
                require(all(f'{c}/seen_ba' in blocks['phase_ramp']['levels'] for c in RUN_LATER[item['item']][1]),
                        f'{study} not-run item {item["item"]!r} is not in the phase ramp')
            elif item['run_in'] == 'cca_adapter':
                require(set(RUN_LATER[item['item']][1]) <= adapter_arms,
                        f'{study} not-run item {item["item"]!r} is not in the CCA adapter')
            else:
                require(item['run_in'] is None, f'{study}: unknown study {item["run_in"]!r}')
        require(set(BLOCK_FIELDS) | set(EXTRA_FIELDS[study]) == set(block), f'{study}: fields')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
                f'{study}: every level and contrast has its place in the source, and only those')
    scan(blocks, '$')
    validate_public(blocks)
    return blocks


if __name__ == '__main__':
    out = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'primary': sum(c['role'] == 'primary' for c in b['contrasts'].values()),
                          'undefined': len(b['undefined']), 'limitations': len(b['limitations_keys'])}
                      for s, b in out.items()}, indent=2))
