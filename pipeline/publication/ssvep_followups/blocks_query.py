"""The query and head blocks of the new-SSVEP-frequencies release: cards 1 and 2 (REF, REF2, softmax).

Three audited route 3 follow-ups on the same BETA cohort, read from their own exports and turned into study blocks
for `new-ssvep-frequencies-update.json`, which the assembler of that file (B4) puts under `studies`:

- `ref`: the reference-spectrum query (REF), four primary L0 and four secondary L1 contrasts, the fixed spectrum
  match (TEMPLATE) and the reused route 3 comparators, from `Reference Spectrum Query Audited Results.json`;
- `ref2`: the matching head, the complex spectrum, the phase-carrying query and the fundamental-only reference,
  twelve primary contrasts over 90 components, from the REF2 `final-aggregate-evidence.json`;
- `softmax`: the two softmax-trained heads on seen frequencies, one primary and one secondary contrast, from the
  softmax `final-aggregate-evidence.json`; the one-vs-rest head (route 3's B-sh) they are compared with is cited,
  point and interval, from the live route 3 file `site/src/data/questions-in-language-update.json`.

Every input is pinned by SHA-256 (PINS) and refused unless it is byte for byte the pinned file and the study's
review binds that hash. Every number is the source's own double: nothing is rounded, rescaled or recomputed, and
units stay fractions (proportions, and differences of proportions). The pinned files carry private storage paths and
operator status strings, so they are read and checked here, never copied.

The declared edits of the release plan (section 3), applied to a working copy of each export before anything is
selected, each refused unless it finds exactly what it names (EDITS):
- REF: the pending-publication status and the operator review-path line are removed, the Jev line is removed from
  the limitations, `design.epochs` is renamed `training_epochs`;
- REF2 and softmax: the private run roots and receipt paths are removed (matched by pattern, never spelled here),
  and the pre-audit pending status strings are removed;
- every CCA level's `seeds: 1` becomes "no training".

A block is a mapping with these fields:
- `source_sha256`, `review_sha256` (and `parent_sha256` on softmax): the pinned bytes it is read from;
- `interval_method`: `{method, seed, draws, level}`, the study's own bootstrap;
- `design` (REF only): the export's design record after the declared rename;
- `levels`: `{id: {estimate, interval, unit, people, seeds, origin}}`; an id is `<features>-<head>-<query>/<endpoint>`
  for a trained head and `<scorer>/<endpoint>` for a training-free scorer (the REF2 export's own spelling);
- `contrasts`: `{id: {role, left, right, estimate, interval, unit, people, seeds, flags}}`; `left` and `right` are
  level ids, `flags` are the source's flags as it states them;
- `undefined`: `[{level, reason}]`, the endpoints an arm cannot have (a fixed set of seen outputs cannot name a
  held-out frequency), absent from `levels`;
- `not_run`: `[{item, run_in}]`, the export's own list, with the study of this release that later ran the item;
- `checks`: the audit's pass or fail and counts;
- `limitations_keys`: keys of the limitations the page states (LIMITATION_SOURCES gives each key's source sentence);
- `display_names`: the site name of every code the block's ids use (section 2.1's name key);
- `export_codes`: `{level or contrast id: [where it is in the source]}`, as `#<JSON pointer>` into the study's export
  or `questions-in-language-update.json#<JSON pointer>` into the live route 3 file.

    python3 pipeline/publication/ssvep_followups/blocks_query.py      # builds and prints the counts; writes nothing
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
PINS = {
    'ref_export': {'path': 'research/decision_route3_ref_20261013/Reference Spectrum Query Audited Results.json',
                   'sha256': '211510622bec8320d77d71074a42ad1b3299958a5629e11f480a1161ebccce64'},
    'ref_review': {'path': 'research/decision_route3_ref_20261013/review/release-conformance-review.json',
                   'sha256': 'e419bf003d129108b949d7e0219096bd3a3908cf993ab432d7b36ae0c9b3d60c'},
    'ref2_export': {'path': 'research/decision_route3_ref2_20261014/exports/final-aggregate-evidence.json',
                    'sha256': 'a0df66fc8e9f049936c00179699935d5bec79a2923459273626fa8207a318763'},
    'ref2_review': {'path': 'research/decision_route3_ref2_20261014/review/Final Result Release Review.json',
                    'sha256': '94c0cdf78cce0f978ec6be2e3d38ccf6597a1cf189a4a6940f60d09d3d6397f4'},
    'ref2_protocol': {'path': 'research/decision_route3_ref2_20261014/protocol.json',
                      'sha256': 'b16a173d304bf48cffc5d274156881a12987fbfbc275a39f37a1b5d9a5e5d4be'},
    'softmax_export': {'path': 'research/decision_route3_softmax_20261014/exports/final-aggregate-evidence.json',
                       'sha256': '957e29f5559dbc8361599469e51f5d4b3c2281febafad398315fa5a679da4823'},
    'softmax_review': {'path': 'research/decision_route3_softmax_20261014/review/Final Result Release Review.json',
                       'sha256': '7701fb476bbf4a048c5614d44de1628d6dfb06da1dd6509b801a615f204493c6'},
    'softmax_baseline': {'path': 'research/decision_route3_softmax_20261014/Existing Baseline Audit.json',
                         'sha256': '34ad81d8d500b921f642f8a6b336e523bf19a27e4c91e6d17136a7d317ac04ce'},
    'softmax_runtime_review': {
        'path': 'research/decision_route3_softmax_20261014/recovery_20261015/Softmax Guard Recovery Review.json',
        'sha256': 'cc8874fc11455723a636e1a7a5a8875bda05493b6b383494e01befda712c8b51'},
    # The live route 3 file: the B-sh (one-vs-rest) interval, and which question forms can ask an unseen frequency.
    'parent': {'path': 'site/src/data/questions-in-language-update.json',
               'sha256': '2583b5958c24e02898929c354e16653e50e33704aaaee37927e158f9d72d01dd'},
}
PARENT_SERVED = 'site/public/data/questions-in-language-update.json'   # must be the same bytes as the src copy
PARENT_FILE = 'questions-in-language-update.json'                      # its served name, as export_codes cite it
PARENT_RELEASE = 'questions-in-language-update-20261008'
REVIEW_OF = {'ref': 'ref_review', 'ref2': 'ref2_review', 'softmax': 'softmax_review'}
EXPORT_OF = {'ref': 'ref_export', 'ref2': 'ref2_export', 'softmax': 'softmax_export'}

STUDIES = ('ref', 'ref2', 'softmax')
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'interval_method', 'levels', 'contrasts', 'undefined', 'not_run',
                'checks', 'limitations_keys', 'display_names', 'export_codes')
ENDPOINTS = ('u8', 'seen_ba', 'm8', 'nn8', 'u3', 'cost')
HELD_OUT_ENDPOINTS = ('u8', 'u3', 'cost')     # what a fixed set of seen outputs cannot have (cost = u8 - m8)
DIFFERENCE_ENDPOINTS = {'cost'}
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
NO_TRAINING = 'no training'
SEED, DRAWS, LEVEL = 20261007, 2000, 0.95
METHOD = 'hierarchical paired bootstrap over people and fold-shared seed indices'
TOL = 1e-12

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
DISPLAY_NAMES = {
    'ID': 'question number',
    'NUM': 'numeric code',
    'TPL': 'label template',
    'REF': 'reference spectrum',
    'REFc-0': 'reference with stimulus phase',
    'TEMPLATE': 'fixed spectrum match (no training)',
    'L0': 'plain spectrum',
    'L0c': 'complex spectrum',
    'L1': 'frozen CBraMod features',
    'FS': 'FiLM head',
    'MATCH': 'matching head',
    'CCA': 'CCA (no training)',              # the name key's CCA-RAW; these exports spell the same scorer CCA
    # Not in the name key. Worded from card 2's lead and the route 3 page's name for B-sh, "one output per question".
    'REF1': 'fundamental-only reference',
    'LINEAR-CE': 'plain 32-way softmax',
    'BSH-CE': 'one output per question, softmax training',
    'BSH-BCE': 'one output per question, one-vs-rest training',
}
NAME_KEY_ALIASES = {'CCA': 'CCA-RAW'}         # this module's code -> the name key's export code
NOT_IN_NAME_KEY = ('REF1', 'LINEAR-CE', 'BSH-CE', 'BSH-BCE')
TRAINING_FREE = ('CCA', 'TEMPLATE')

# ---------------------------------------------------------------------------- declared edits (plan section 3)
LOCAL_ROOT = '<private storage path>'          # an edit's expected value that is matched by pattern, never spelled
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
REF_ROOT = '/results/questions-in-language-ref'
REF_PENDING = 'scientific_audit_passed_pending_owner_publication'
REF_REVIEW_LINE = ('review/release-conformance-review.json must pass; the review is an operator artifact and is not '
                   'needed as a public asset.')
REF_JEV_LINE = ('The EEG FiLM interface is inspired by the Jev-style encode-once/answer-many idea; this is not a test '
                'of the original Jev system.')


def pointer(*tokens):
    """An RFC 6901 JSON pointer from its reference tokens (the REF2 level keys contain '/')."""
    return ''.join('/' + str(t).replace('~', '~0').replace('/', '~1') for t in tokens)


def _cca_seed_edits(study):
    if study == 'ref':
        return tuple(('replace', pointer(*REF_ROOT[1:].split('/'), 'descriptive', block, 'levels', f'CCA {e}', 'seeds'),
                      1, NO_TRAINING)
                     for block in ('REF-ssvep-L0', 'REF-ssvep-L1') for e in ENDPOINTS)
    return tuple(('replace', pointer('aggregate', 'levels', f'CCA/{e}', 'seeds'), 1, NO_TRAINING) for e in ENDPOINTS)


EDITS = {
    'ref': (
        ('remove', '/status', REF_PENDING, None),
        ('remove', '/independent_handoff_review_required', REF_REVIEW_LINE, None),
        ('remove', f'{REF_ROOT}/limitations/7', REF_JEV_LINE, None),
        ('rename', f'{REF_ROOT}/design/epochs', 60, 'training_epochs'),
    ) + _cca_seed_edits('ref'),
    'ref2': (
        ('remove', '/remote_root', LOCAL_ROOT, None),
        ('remove', '/completion/recovery_overlay', LOCAL_ROOT, None),
        ('remove', '/aggregate/status', 'scored_pending_independent_audit', None),
    ) + _cca_seed_edits('ref2'),
    'softmax': (
        ('remove', '/remote_root', LOCAL_ROOT, None),
        ('remove', '/audit/original_full_receipt_remains_private', LOCAL_ROOT, None),
        ('remove', '/aggregate/status', 'private_pending_independent_audit', None),
    ),
}

# ---------------------------------------------------------------------------- limitations and undefined endpoints
# key -> (pinned input, JSON pointer into its original bytes, a phrase the sentence there must contain). The page
# writes each limitation in its own words; the key says which source sentence it states.
LIMITATION_SOURCES = {
    'ref': {
        'same_cohort_one_recipe': ('ref_export', f'{REF_ROOT}/limitations/0', 'previously studied BETA cohort'),
        'unadjusted_intervals': ('ref_export', f'{REF_ROOT}/limitations/1', 'no multiplicity correction'),
        'recipe_as_a_whole': ('ref_export', f'{REF_ROOT}/limitations/2', 'no isolated causal attribution'),
        'head_not_isolated': ('ref_export', f'{REF_ROOT}/limitations/3', 'sole bottleneck'),
        'cca_keeps_temporal_information': ('ref_export', f'{REF_ROOT}/limitations/4',
                                           'multichannel temporal information'),
        'structural_zero_cost': ('ref_export', f'{REF_ROOT}/limitations/5', 'structurally zero'),
        'reference_spectrum_definition': ('ref_export', f'{REF_ROOT}/limitations/6',
                                          'quadrature-pooled reference-subspace spectrum'),
        'l1_u3_phase': ('ref_export', f'{REF_ROOT}/limitations/8', 'associated stimulus phase'),
        'tpl_wordings_averaged': ('ref_export', f'{REF_ROOT}/descriptive/REF-ssvep-L0/levels/TPL u8/method_note',
                                  'wordings averaged'),
        'cca_raw_eeg_comparator': ('ref_export', f'{REF_ROOT}/descriptive/REF-ssvep-L0/levels/CCA u8/method_note',
                                   'Raw-EEG CCA'),
        'template_untrained': ('ref_export', f'{REF_ROOT}/descriptive/REF-ssvep-L0/levels/TEMPLATE u8/method_note',
                               'no trained parameters'),
    },
    'ref2': {
        'unadjusted_intervals': ('ref2_export', '/aggregate/multiplicity', 'no multiplicity correction'),
        'recipe_specific': ('ref2_export', '/aggregate/interpretation', 'specific to these recipes'),
        'u3_phase_and_id': ('ref2_export', '/aggregate/u3_caveat', 'also differ in phase'),
        'l0c_recipe_as_a_whole': ('ref2_review', '/release_caveats/1', 'not an isolated causal phase test'),
        'stimulus_phase_assumptions': ('ref2_review', '/release_caveats/2', 'zero modeled latency'),
        'match_one_recipe': ('ref2_review', '/release_caveats/3', 'one fixed rank-64 bilinear recipe'),
        'refc0_gain_within_l0c': ('ref2_review', '/release_caveats/4', 'within-L0c gain'),
        'unseen_by_the_head': ('ref2_review', '/release_caveats/5', 'omitted from the trained EEG head'),
        'id_and_m8_endpoints': ('ref2_review', '/release_caveats/6', 'm8 must not be replaced'),
        'structural_zero_cost': ('ref2_review', '/release_caveats/8', 'structural under this rotation scheme'),
        'compatibility_reader_recovery': ('ref2_review', '/release_caveats/9', 'candidate identity contract'),
    },
    'softmax': {
        'bsh_one_vs_rest_loss': ('softmax_baseline', '/existing_baseline/loss', 'weighted one-vs-rest'),
        'objective_and_architecture_change': ('softmax_review', '/interpretation/3', 'changes the full objective'),
        'no_ceiling_or_causal_claim': ('softmax_review', '/interpretation/4', 'information ceiling'),
        'seen_only': ('softmax_review', '/interpretation/5', 'These are seen32 results'),
        'runtime_guard_recovery': ('softmax_runtime_review', '/guard_fix_assessment/fix',
                                   'hashes the frozen manifest and each frozen code file'),
        'motivated_by_known_results': ('softmax_runtime_review', '/scientific_limitations/5',
                                       'motivated by known historical results'),
    },
}
# reason -> where each study's source states it, and what it must say there.
UNDEFINED_SOURCES = {
    'ref': ('parent', '/results/questions-in-language/design/question_forms/ID/can_ask_unseen', False),
    'ref2': ('ref2_export', '/aggregate/u3_caveat', 'ID has no direct held-query predictions'),
    'softmax_ce': ('softmax_review', '/interpretation/5', 'Native unseen decoding is not applicable'),
    'softmax_bce': ('parent', '/results/questions-in-language/design/question_forms/B-sh/can_ask_unseen', False),
}
UNDEFINED_REASON = 'cannot_ask_unseen'        # the route 3 file's own field: can_ask_unseen false

# REF's not-run items that REF2 ran, and the REF2 codes that show it.
RUN_LATER = {'Matching/bilinear head': ('ref2', 'MATCH'), 'Fundamental-only reference ablation': ('ref2', 'REF1')}

# ---------------------------------------------------------------------------- REF: labels -> level ids
REF_BLOCKS = {'REF-ssvep-L0': 'L0', 'REF-ssvep-L1': 'L1'}
REF_QUERIES = ('REF', 'NUM', 'ID', 'TPL')
REF_CONTRASTS = {   # id -> (label in the export, left, right) with {f} the feature level
    'R1': ('REF - NUM, held-eight accuracy', '{f}-FS-REF/u8', '{f}-FS-NUM/u8'),
    'R2': ('REF - ID, seen-32 balanced accuracy', '{f}-FS-REF/seen_ba', '{f}-FS-ID/seen_ba'),
    'R3': ('REF - CCA, held-eight accuracy', '{f}-FS-REF/u8', 'CCA/u8'),
    'R4': ('REF held-eight - matched-seen-eight accuracy', '{f}-FS-REF/u8', '{f}-FS-REF/m8'),
}
REF2_FLAGS = ('difference', 'equivalent_within_2pp', 'noninferiority_to_CCA', 'meaningful_head_gain')
REF2_HEADROOM = ('L0-FS', 'L0-MATCH', 'L0c-FS', 'L0c-MATCH')
SOFTMAX_ARMS = ('LINEAR-CE', 'BSH-CE')
SOFTMAX_CONTRASTS = {'primary': ('BSH-CE minus BSH-BCE', 'L0-BSH-CE/seen_ba', 'L0-BSH-BCE/seen_ba'),
                     'secondary': ('BSH-CE minus LINEAR-CE', 'L0-BSH-CE/seen_ba', 'L0-LINEAR-CE/seen_ba')}
PARENT_BSH = pointer('results', 'questions-in-language', 'descriptive', 'P-ssvep-L0', 'levels', 'B-sh seen_ba')


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


def _parent_of(doc, ptr):
    parts = tokens(ptr)
    require(parts, 'an edit cannot act on the whole document')
    head = doc
    for t in parts[:-1]:
        head = head[int(t)] if isinstance(head, list) else head[t]
    return head, parts[-1]


def _matches(value, expected):
    if expected is LOCAL_ROOT:
        return isinstance(value, str) and bool(LOCAL_ROOTS.search(value))
    return type(value) is type(expected) and value == expected


def apply_edits(doc, edits, label):
    """A copy of `doc` with the declared edits applied; each must find exactly the value it names."""
    out = copy.deepcopy(doc)
    for op, ptr, expected, new in edits:
        head, last = _parent_of(out, ptr)
        current = resolve(out, ptr)
        require(_matches(current, expected), f'{label}: {ptr} is not what the declared edit names')
        if op == 'remove':
            if isinstance(head, list):
                head.pop(int(last))
            else:
                del head[last]
        elif op == 'replace':
            head[int(last) if isinstance(head, list) else last] = new
        elif op == 'rename':
            require(isinstance(head, dict) and new not in head, f'{label}: {ptr} cannot be renamed to {new!r}')
            items = list(head.items())
            head.clear()
            head.update((new if k == last else k, v) for k, v in items)
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
        docs[name], digests[name] = json.loads(raw), digest
    served = location(PARENT_SERVED).read_bytes()
    require(sha(served) == digests['parent'], 'the served route 3 file differs from the copy the site builds from')
    return docs, digests


def inputs_available(pins=None):
    """Whether the pinned inputs are on this machine; the research folders are local, not in the repository."""
    return all(location(r['path']).exists() for r in (pins or PINS).values()) and location(PARENT_SERVED).exists()


def interval(lo, hi, point, label, lower=0.0, upper=1.0):
    require(all(number(v) for v in (lo, hi, point)), f'{label}: not a finite interval')
    require(lower <= lo <= point <= hi <= upper, f'{label}: the interval does not hold its point')
    return [lo, hi]


def level(estimate, lo, hi, unit, people, seeds, origin, label):
    lower = -1.0 if unit == DIFFERENCE else 0.0
    return {'estimate': estimate, 'interval': interval(lo, hi, estimate, label, lower=lower), 'unit': unit,
            'people': people, 'seeds': seeds, 'origin': origin}


def codes_of(ids):
    """The codes a block's ids are made of, for its display names: 'L0c-MATCH-REFc-0/u8' -> L0c, MATCH, REFc-0."""
    out = []
    for i in ids:
        cell = i.split('/')[0]
        if cell in TRAINING_FREE:
            parts = [cell]
        else:
            m = re.fullmatch(r'(L0c|L0|L1)-(FS|MATCH|LINEAR-CE|BSH-CE|BSH-BCE)(?:-(REFc-0|REF1|REF|NUM|ID|TPL))?', cell)
            require(m is not None, f'{i}: not a level id')
            parts = [p for p in m.groups() if p]
        out += [p for p in parts if p not in out]
    return out


def display_names(levels):
    codes = codes_of(levels)
    order = [c for c in DISPLAY_NAMES if c in codes]
    require(set(order) == set(codes), f'no display name for {sorted(set(codes) - set(order))}')
    return {c: DISPLAY_NAMES[c] for c in order}


def limitations(study, docs):
    keys = []
    for key, (doc, ptr, phrase) in LIMITATION_SOURCES[study].items():
        text = resolve(docs[doc], ptr)
        require(isinstance(text, str) and phrase in text, f'{study} limitation {key}: {doc} {ptr} does not say {phrase!r}')
        require('Jev' not in text, f'{study} limitation {key}: a Jev line is not a limitation of this study')
        keys.append(key)
    return keys


def undefined(study, levels, cells):
    rows = []
    for cell in cells:
        for e in HELD_OUT_ENDPOINTS if study != 'softmax' else ('u8',):
            lid = f'{cell}/{e}'
            require(lid not in levels, f'{study}: {lid} is defined, yet its arm cannot ask an unseen frequency')
            rows.append({'level': lid, 'reason': UNDEFINED_REASON})
    return rows


def stated(docs, source):
    doc, ptr, expected = source
    value = resolve(docs[doc], ptr)
    if isinstance(expected, str):
        require(isinstance(value, str) and expected in value, f'{doc} {ptr} does not state {expected!r}')
    else:
        require(value is expected, f'{doc} {ptr} is {value!r}, not {expected!r}')


def checked_contrast(levels, cid, left, right, estimate, label):
    require(left in levels and right in levels, f'{label}: {cid} compares levels this block does not hold')
    diff = levels[left]['estimate'] - levels[right]['estimate']
    require(abs(diff - estimate) <= TOL, f'{label}: {cid} is {estimate!r}, its levels differ by {diff!r}')


def scan(value, trail):
    """What the blocks never carry: pending statuses, private paths, Jev, the forbidden `epochs` key, a 55."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(k != 'epochs', f'{trail}: an `epochs` field (declared rename: training_epochs)')
            scan(k, f'{trail}.<key>')
            scan(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scan(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require('pending' not in value.lower(), f'{trail}: a pending status string')
        require(not LOCAL_ROOTS.search(value), f'{trail}: a private path')
        require('Jev' not in value, f'{trail}: a Jev line')
        require(re.fullmatch(r'[0-9a-f]{64}', value) or '55' not in value, f'{trail}: a 55 in the text')
    elif isinstance(value, float):
        require(math.isfinite(value), f'{trail}: not finite')


# ---------------------------------------------------------------------------- bindings between the pinned files
def check_bindings(docs, digests):
    ref_review, ref2_review, sm_review = docs['ref_review'], docs['ref2_review'], docs['softmax_review']
    require(ref_review['status'] == 'pass' and ref_review['blockers'] == [], 'REF: the conformance review did not pass')
    require(ref_review['delivered_file_sha256'].get('Reference Spectrum Query Audited Results.json')
            == digests['ref_export'], 'REF: the review binds other export bytes')
    require(docs['ref_export']['base_release_id'] == docs['parent']['release_id'] == PARENT_RELEASE,
            'REF: not an extension of the live route 3 release')
    require(ref2_review['status'] == 'accepted_for_aggregate_handoff', 'REF2: the release review did not accept')
    require(ref2_review['export_sha256'] == digests['ref2_export'], 'REF2: the review binds other export bytes')
    require(ref2_review['protocol_sha256'] == digests['ref2_protocol']
            == docs['ref2_export']['source_sha256']['protocol.json'], 'REF2: protocol bytes not the reviewed ones')
    require(sm_review['status'] == 'accepted_for_aggregate_handoff', 'softmax: the release review did not accept')
    require(sm_review['export_sha256'] == digests['softmax_export'], 'softmax: the review binds other export bytes')
    require(sm_review['prior_baseline_audit_sha256'] == digests['softmax_baseline'],
            'softmax: the review binds another baseline audit')
    require(sm_review['accepted_runtime_review_sha256'] == digests['softmax_runtime_review']
            and docs['softmax_runtime_review']['status'] == 'accepted', 'softmax: the runtime review is not the bound one')
    require(sm_review['checks'].get('historical_bce_and_id_points_match_prior_baseline_audit_within_1e_12') is True,
            'softmax: the review did not match the historical B-sh point')


# ---------------------------------------------------------------------------- REF
def build_ref(docs, digests):
    src = apply_edits(docs['ref_export'], EDITS['ref'], 'REF')
    run = src['results']['questions-in-language-ref']
    audits = run['audits']
    require(audits['status'] == 'pass' and audits['release_eligible'] is True
            and audits['numeric_metrics']['status'] == 'pass', 'REF: the numerical audit did not pass')
    require(METHOD.replace('hierarchical paired bootstrap', 'paired hierarchical draws') in run['design']['bootstrap'],
            'REF: the design does not state the hierarchical paired bootstrap')

    levels, codes = {}, {}
    for block, feature in REF_BLOCKS.items():
        for name, lv in run['descriptive'][block]['levels'].items():
            arm, endpoint = name.split(' ')
            require(endpoint in ENDPOINTS, f'REF: unknown endpoint {name}')
            lid = f'{arm}/{endpoint}' if arm in TRAINING_FREE else f'{feature}-FS-{arm}/{endpoint}'
            require(arm in REF_QUERIES + TRAINING_FREE, f'REF: unknown arm {name}')
            require(lv['excluded_people'] == 0, f'REF: {name} excludes people')
            unit = lv['unit']
            require(unit == (DIFFERENCE if endpoint in DIFFERENCE_ENDPOINTS else PROPORTION), f'REF: {name} unit')
            row = level(lv['estimate'], *lv['interval_95'], unit, lv['people'], lv['seeds'], lv['origin'],
                        f'REF {block} {name}')
            where = '#' + pointer(*REF_ROOT[1:].split('/'), 'descriptive', block, 'levels', name)
            if lid in levels:     # CCA is the same raw-EEG comparator in both panels: one level, two places
                require(arm == 'CCA' and levels[lid] == row, f'REF: {lid} differs between the two panels')
                codes[lid].append(where)
            else:
                levels[lid], codes[lid] = row, [where]
    require(not any(n.startswith('TEMPLATE ') for n in run['descriptive']['REF-ssvep-L1']['levels']),
            'REF: the fixed spectrum match is defined on the plain spectrum only')
    require(sum(len(run['descriptive'][b]['levels']) for b in REF_BLOCKS) == audits['numeric_metrics']['components'],
            'REF: not every audited component is a level')
    for lid, row in levels.items():
        cca = lid.startswith('CCA/')
        require(row['seeds'] == (NO_TRAINING if cca else (1 if lid.startswith('TEMPLATE/') else 3)),
                f'REF: {lid} seeds')

    contrasts, draws = {}, set()
    for part in ('primary', 'secondary'):
        for b, block in enumerate(run[part]['blocks']):
            feature = REF_BLOCKS[block['block']]
            for e, entry in enumerate(block['entries']):
                label, left, right = REF_CONTRASTS[entry['id']]
                require(entry['label'] == label and entry['role'] == part, f'REF: {entry["key"]} is not {label}')
                require(entry['excluded_people'] == 0 and entry['unit'] == DIFFERENCE, f'REF: {entry["key"]}')
                cid = f'{feature}/{entry["id"]}'
                left, right = left.format(f=feature), right.format(f=feature)
                checked_contrast(levels, cid, left, right, entry['estimate'], 'REF')
                draws.add(entry['draws'])
                contrasts[cid] = {
                    'role': entry['role'], 'left': left, 'right': right, 'estimate': entry['estimate'],
                    'interval': interval(*entry['interval_95'], entry['estimate'], f'REF {cid}', lower=-1.0),
                    'unit': DIFFERENCE, 'people': entry['people'], 'seeds': entry['seeds'],
                    'flags': {k: entry[k] for k in ('difference', 'margin_pass', 'margin_rule')},
                }
                codes[cid] = ['#' + pointer(*REF_ROOT[1:].split('/'), part, 'blocks', b, 'entries', e)]
    require(len(contrasts) == audits['numeric_metrics']['contrasts'] == 8, 'REF: not 4 + 4 contrasts')

    gates = {feature: [blk['gates'] for p in ('primary', 'secondary') for blk in run[p]['blocks']
                       if blk['block'] == block][0] for block, feature in REF_BLOCKS.items()}
    seeds = {g['headroom']['interval']['seed'] for g in gates.values()}
    levels_of_interval = {g['headroom']['interval']['level'] for g in gates.values()}
    require(draws == {DRAWS} == {audits['numeric_metrics']['bootstrap_draws']}, 'REF: bootstrap draws')
    require(seeds == {SEED} and levels_of_interval == {LEVEL}, 'REF: bootstrap seed or level')
    for feature, g in gates.items():     # the headroom interval is the reused question-number level, exactly
        h = g['headroom']['interval']
        lv = levels[f'{feature}-FS-ID/seen_ba']
        require([h['point'], h['lo'], h['hi']] == [lv['estimate'], *lv['interval']], f'REF: {feature} headroom')

    stated(docs, UNDEFINED_SOURCES['ref'])
    not_run = []
    for item in run['not_run']:
        later = RUN_LATER.get(item)
        not_run.append({'item': item, 'run_in': later[0] if later else None})
    design = copy.deepcopy(run['design'])
    require(design.get('training_epochs') == 60 and 'epochs' not in design, 'REF: the declared rename is not applied')

    return {
        'source_sha256': digests['ref_export'],
        'review_sha256': digests['ref_review'],
        'interval_method': {'method': METHOD, 'seed': SEED, 'draws': DRAWS, 'level': LEVEL},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'undefined': undefined('ref', levels, [f'{f}-FS-ID' for f in REF_BLOCKS.values()]),
        'not_run': not_run,
        'checks': {
            'audit': {k: audits[k] for k in ('status', 'release_eligible', 'main_models_reconstructed', 'canary_fits',
                                             'fixed_independent_refits', 'argmax_exact')}
            | {'numeric_metrics': {k: audits['numeric_metrics'][k] for k in (
                'status', 'components', 'contrasts', 'metric_atol', 'bootstrap_draws', 'all_draws_pairing_verified',
                'template_reconstructed')}},
            'headroom': {f: g['headroom']['pass'] for f, g in gates.items()},
            'canary': {f: g['ref_canary'] for f, g in gates.items()},
            'excluded_people': 0,
        },
        'limitations_keys': limitations('ref', docs),
        'display_names': display_names(levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- REF2
def build_ref2(docs, digests, ref_block):
    src = apply_edits(docs['ref2_export'], EDITS['ref2'], 'REF2')
    agg, audit = src['aggregate'], src['audit']
    require(audit['status'] == 'pass' and audit['release_eligible'] is True
            and audit['numeric_metrics']['status'] == 'pass', 'REF2: the numerical audit did not pass')
    require(src['completion']['status'] == 'audited_complete', 'REF2: the run is not audited complete')
    require('hierarchical paired draws over people, with shared seed-index draws within fold'
            in docs['ref2_protocol']['metrics']['bootstrap'], 'REF2: the protocol does not state the bootstrap')
    new_cells = [c['id'] for c in docs['ref2_protocol']['scope']['cells']]

    levels, codes, cells = {}, {}, []
    for lid, lv in agg['levels'].items():
        cell, endpoint = lid.split('/')
        require(endpoint in ENDPOINTS, f'REF2: unknown endpoint {lid}')
        require((lv['draws'], lv['seed'], lv['level'], lv['excluded_people']) == (DRAWS, SEED, LEVEL, 0),
                f'REF2: {lid} has another bootstrap or excludes people')
        if cell not in cells:
            cells.append(cell)
        origin = 'new' if cell in new_cells else ('reused_ref' if cell == 'L0-FS-REF' else 'reused_parent')
        unit = DIFFERENCE if endpoint in DIFFERENCE_ENDPOINTS else PROPORTION
        levels[lid] = level(lv['point'], lv['lo'], lv['hi'], unit, lv['people'], lv['seeds'], origin, f'REF2 {lid}')
        codes[lid] = ['#' + pointer('aggregate', 'levels', lid)]
        if origin != 'new':      # a reused cell is the REF block's level, to the last bit
            ref_lv = ref_block['levels'][lid]
            require((ref_lv['estimate'], ref_lv['interval'], ref_lv['seeds']) ==
                    (levels[lid]['estimate'], levels[lid]['interval'], levels[lid]['seeds']), f'REF2: {lid} reused')
    require(len(levels) == audit['numeric_metrics']['components'] == 90, 'REF2: not the 90 audited components')
    require(set(new_cells) <= set(cells), 'REF2: a protocol cell has no levels')
    id_cells = [c for c in cells if c.endswith('-ID')]
    for c in cells:
        have = {e for e in ENDPOINTS if f'{c}/{e}' in levels}
        require(have == (set(ENDPOINTS) - set(HELD_OUT_ENDPOINTS) if c in id_cells else set(ENDPOINTS)),
                f'REF2: {c} has endpoints {sorted(have)}')
    for lid, row in levels.items():
        require(row['seeds'] == (NO_TRAINING if lid.startswith('CCA/') else 3), f'REF2: {lid} seeds')

    contrasts = {}
    for cid, c in agg['contrasts'].items():
        require((c['draws'], c['seed'], c['level'], c['excluded_people']) == (DRAWS, SEED, LEVEL, 0),
                f'REF2: {cid} has another bootstrap or excludes people')
        left = f'{c["left"]}/{c["metric"]}'
        right = f'{c["right"]}/{c["metric"]}'
        checked_contrast(levels, cid, left, right, c['point'], 'REF2')
        contrasts[cid] = {
            'role': c['role'], 'left': left, 'right': right, 'estimate': c['point'],
            'interval': interval(c['lo'], c['hi'], c['point'], f'REF2 {cid}', lower=-1.0),
            'unit': DIFFERENCE, 'people': c['people'], 'seeds': c['seeds'],
            'flags': {k: c[k] for k in REF2_FLAGS},
        }
        codes[cid] = ['#' + pointer('aggregate', 'contrasts', cid)]
    require(len(contrasts) == audit['numeric_metrics']['contrasts'] == 12, 'REF2: not twelve contrasts')
    require(all(c['role'] == 'primary' for c in contrasts.values()), 'REF2: the twelve are the primary family')

    headroom = agg['headroom']
    require(tuple(headroom) == REF2_HEADROOM, 'REF2: headroom gates')
    for g, h in headroom.items():
        lv = levels[f'{g}-ID/seen_ba']
        i = h['interval']
        require([i['point'], i['lo'], i['hi']] == [lv['estimate'], *lv['interval']], f'REF2: {g} headroom')
    stated(docs, UNDEFINED_SOURCES['ref2'])

    return {
        'source_sha256': digests['ref2_export'],
        'review_sha256': digests['ref2_review'],
        'interval_method': {'method': METHOD, 'seed': SEED, 'draws': DRAWS, 'level': LEVEL},
        'levels': levels,
        'contrasts': contrasts,
        'undefined': undefined('ref2', levels, id_cells),
        'not_run': [],
        'checks': {
            'audit': {k: audit[k] for k in ('status', 'release_eligible', 'main_models_reconstructed', 'canary_fits',
                                            'fixed_independent_refits', 'argmax_exact')}
            | {'numeric_metrics': {k: audit['numeric_metrics'][k] for k in (
                'status', 'components', 'contrasts', 'metric_atol', 'bootstrap_draws',
                'all_draws_pairing_verified')}},
            'completion': src['completion']['status'],
            'counts': dict(src['counts']),
            'headroom': {g: h['pass'] for g, h in headroom.items()},
            'excluded_people': 0,
        },
        'limitations_keys': limitations('ref2', docs),
        'display_names': display_names(levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- softmax
def build_softmax(docs, digests):
    src = apply_edits(docs['softmax_export'], EDITS['softmax'], 'softmax')
    agg, audit = src['aggregate'], src['audit']
    require(audit['status'] == 'pass' and audit['metrics'] == 'pass', 'softmax: the numerical audit did not pass')
    require(src['completion']['status'] == 'complete', 'softmax: the run is not complete')
    require(docs['softmax_review']['checks'].get('declared_2000_draw_seed_20261007_95pct_people70_seeds3_matches')
            is True, 'softmax: the review did not match the declared bootstrap')

    levels, codes = {}, {}
    for arm in SOFTMAX_ARMS:
        lv = agg['levels'][arm]
        require((lv['draws'], lv['seed'], lv['level']) == (DRAWS, SEED, LEVEL), f'softmax: {arm} bootstrap')
        lid = f'L0-{arm}/seen_ba'
        levels[lid] = level(lv['point'], lv['lo'], lv['hi'], PROPORTION, lv['people'], lv['seeds'], 'new',
                            f'softmax {arm}')
        codes[lid] = ['#' + pointer('aggregate', 'levels', arm)]
    require(set(agg['levels']) == set(SOFTMAX_ARMS), 'softmax: arms')

    # The one-vs-rest head (route 3's B-sh): point and interval from the live route 3 file. The softmax export
    # carries only its point; the baseline audit the review binds carries the same interval from the same bootstrap.
    parent = resolve(docs['parent'], PARENT_BSH)
    lo, hi = parent['interval_95']
    base = docs['softmax_baseline']['existing_baseline']['result']
    require([base['point'], base['lo'], base['hi']] == [parent['estimate'], lo, hi]
            and (base['draws'], base['seed'], base['level'], base['excluded_people']) == (DRAWS, SEED, LEVEL, 0),
            'softmax: the route 3 B-sh interval is not the baseline audit\'s')
    require(abs(agg['historical_descriptive']['BSH-BCE'] - parent['estimate']) <= TOL,
            'softmax: the historical B-sh point is not the route 3 one')
    levels['L0-BSH-BCE/seen_ba'] = level(parent['estimate'], lo, hi, PROPORTION, parent['people'], parent['seeds'],
                                         'reused_parent', 'softmax B-sh')
    codes['L0-BSH-BCE/seen_ba'] = [PARENT_FILE + '#' + PARENT_BSH]

    contrasts = {}
    for part, (name, left, right) in SOFTMAX_CONTRASTS.items():
        c = agg[part]
        require(c['name'] == name, f'softmax: the {part} contrast is {c["name"]!r}')
        require((c['draws'], c['seed'], c['level']) == (DRAWS, SEED, LEVEL), f'softmax: {name} bootstrap')
        checked_contrast(levels, name, left, right, c['point'], 'softmax')
        lower_in, upper_in = -c['equivalence_margin'] < c['lo'], c['hi'] < c['equivalence_margin']
        require(c['equivalent_strict_2pp'] is (lower_in and upper_in), f'softmax: {name} equivalence flag')
        contrasts[name] = {
            'role': part, 'left': left, 'right': right, 'estimate': c['point'],
            'interval': interval(c['lo'], c['hi'], c['point'], f'softmax {name}', lower=-1.0),
            'unit': DIFFERENCE, 'people': c['people'], 'seeds': c['seeds'],
            'flags': {k: c[k] for k in ('equivalent_strict_2pp', 'equivalence_margin')},
        }
        codes[name] = ['#' + pointer('aggregate', part)]
    stated(docs, UNDEFINED_SOURCES['softmax_ce'])
    stated(docs, UNDEFINED_SOURCES['softmax_bce'])

    return {
        'source_sha256': digests['softmax_export'],
        'parent_sha256': digests['parent'],
        'review_sha256': digests['softmax_review'],
        'interval_method': {'method': METHOD, 'seed': SEED, 'draws': DRAWS, 'level': LEVEL},
        'levels': levels,
        'contrasts': contrasts,
        'undefined': undefined('softmax', levels, [lid.split('/')[0] for lid in levels]),
        'not_run': [],
        'checks': {
            'audit': {k: audit[k] for k in ('status', 'metrics', 'reconstructions', 'independent_refits')},
            'completion': src['completion']['status'],
            'counts': dict(src['counts']),
        },
        'limitations_keys': limitations('softmax', docs),
        'display_names': display_names(levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- all three
def build_blocks(pins=None) -> dict:
    """The study blocks `ref`, `ref2` and `softmax`, from the pinned inputs (PINS unless `pins` replaces them)."""
    docs, digests = load(pins)
    check_bindings(docs, digests)
    ref = build_ref(docs, digests)
    blocks = {'ref': ref, 'ref2': build_ref2(docs, digests, ref), 'softmax': build_softmax(docs, digests)}
    for item in ref['not_run']:      # what REF did not run and REF2 did, REF2's codes show
        if item['run_in']:
            require(RUN_LATER[item['item']][1] in blocks[item['run_in']]['display_names'],
                    f'REF not-run item {item["item"]!r} is not in {item["run_in"]}')
    for study, block in blocks.items():
        require(set(BLOCK_FIELDS) <= set(block), f'{study}: missing fields')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
                f'{study}: every level and contrast has its place in the source, and only those')
    scan(blocks, '$')
    validate_public(blocks)
    return blocks


if __name__ == '__main__':
    out = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'undefined': len(b['undefined']), 'limitations': len(b['limitations_keys'])}
                      for s, b in out.items()}, indent=2))
