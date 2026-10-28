"""Release the seven SSVEP follow-ups of this round, aggregate-only: cards 8 to 14 of /topics/new-ssvep-frequencies/.

Seven audited route 3 follow-ups on SSVEP frequencies a decoder never trained on, each read from its own aggregate:
the cross-spectral scorer (card 8, queue row 21), the coherence and eigenvalue heads (card 9, row 12), the pooling of
CCA's per-harmonic statistics on BETA and Wearable-102 (card 10, row 32), filter-bank CCA with shorter windows and
fewer electrodes, with the CPU component measurements (card 11, rows 33 and 30), the harmonic gap (card 12, row 15),
the fixed decay weighting (card 13, row 14) and the rising harmonic weights (card 14, row 20). The owner's decision D14
of 2026-10-28 publishes them; D28 keeps new-ssvep-frequencies-update.json as released, and this file's card 8 entry
supersedes that file's card 8 status entry. The page reads both files.

The study blocks are built by the five block modules (ssvep_followups/blocks_xspec.py, blocks_eigen.py,
blocks_pooling.py, blocks_practical.py, blocks_weights.py), each from its own audited aggregates, reviews and
approvals, pinned by SHA-256; this assembler adds what spans the studies and binds the whole to the release manifest:
- the manifest pins exactly the files each block module pins (blocks_eigen also reads card 8's pins, the xspec
  module's), and each study's source, review and approval are the ones its block carries;
- each study's handoff is pinned by the hash its release approval binds and its queue row names, and stays context
  (queue row 30 names the parent handoff that asked for the CPU component timings, pinned beside the timing handoff);
  the manifest's `contextPins` (receipts and records an approval or a disclosure rests on) are each checked bound by
  a pinned record, by SHA-256 or by file name;
- `placement.cards` gives cards 8 to 14 with their anchors, studies and endpoints, card 8 superseding the released
  status entry; `endpoints` and `interval_methods` are read from the blocks and required equal wherever two state them;
- `name_key` maps site names to export codes (plan section 2.1), every code of every block in exactly one row, an
  alias naming the primary site names it stands for (`alias_of`); `shared_estimates` names the levels that are one
  set of scores under one primary site name, checked equal to the last bit, with their `aliases`, the card whose
  interval the page prints (`interval_home`) and whether the cards' own intervals differ (`intervals_differ_by_card`);
  every card's source interval stays in its study block;
- `engineering_disclosures` states the two cross-spectral pre-score corrections, the coherence zero-energy edge fix
  and the synthetic suite that timed out (not counted as a pass), each phrase checked in its pinned record;
- `rights` copies BETA's and Wearable-102's released records from the released file and credits FBCCA (Chen et al.
  2015) from the site's method profile; `provenance` names the manifest and every source by SHA-256.

What this export refuses:
- a block module that pins other bytes than the manifest, a handoff its approval or queue row does not name, a
  released file whose bytes differ from the 2026-10-20 export audit's, two studies stating one figure differently;
- per-person, per-fold, per-seed, per-window and per-frequency values, predictions, features and run times, by key and
  by fragment, and the withheld values of the cross-spectral, coherence, weighting and timing aggregates by value;
  private paths, host, volume and user names (read at run time from the pinned records that carry them);
- the commenter's confidence figure in any form, the commenter's name and the comment thread (D23: the new cards state
  only their prespecified criteria);
- a version label, a month or an update marker in the text, Jev, an unnegated claim of a ranking or of clinical or
  real-time use, and an "X, not Y" hedge in the text this file adds.

    python3 pipeline/publication/export_ssvep_followups_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import require, sha
from ssvep_followups import blocks_cca, blocks_eigen, blocks_pooling, blocks_practical, blocks_weights, blocks_xspec

PROJECT = Path(__file__).resolve().parents[2]
PUBLICATION = Path(__file__).resolve().parent
LOCAL = PUBLICATION / 'local_paths.json'             # optional `researchRoot`: where this machine keeps research/
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'ssvep-followups-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'ssvep-followups-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/ssvep-followups-update.json',
           PROJECT / 'site/public/data/ssvep-followups-update.json')
RELEASE_ID = 'ssvep-followups-update-20261028'
SCHEMA = 'bci-report-ssvep-followups-update-v1'
RELEASED_ID = 'new-ssvep-frequencies-update-20261020'
RELEASED_FILE = 'new-ssvep-frequencies-update.json'
RELEASED_SERVED = PROJECT / 'site/public/data/new-ssvep-frequencies-update.json'
PAGE = '/topics/new-ssvep-frequencies/'

MODULES = {'xspec': blocks_xspec, 'eigen': blocks_eigen, 'pooling': blocks_pooling, 'practical': blocks_practical,
           'weights': blocks_weights}
STUDIES = ('xspec', 'coherence_eigen', 'harmonic_pooling', 'harmonic_pooling_wearable', 'practical_settings',
           'harmonic_gap', 'fixed_decay', 'rising_weights')
COMPONENT = 'cpu_components'                         # card 11's CPU component record (D25), inside its study block
# card -> (anchor, studies), plan section 2.1, in the handoff's thread order; cards 1 to 8 keep their anchors.
CARDS = ((8, 'cross-spectral', ('xspec',)), (9, 'eigenvalue-pooling', ('coherence_eigen',)),
         (10, 'harmonic-pooling', ('harmonic_pooling', 'harmonic_pooling_wearable')),
         (11, 'practical-settings', ('practical_settings',)), (12, 'harmonic-gap', ('harmonic_gap',)),
         (13, 'fixed-decay', ('fixed_decay',)), (14, 'rising-weights', ('rising_weights',)))
SUPERSEDED_CARD = 8
ENDPOINT_ORDER = ('u8', 'seen_ba', 'dry', 'wet')
ENDPOINT_TASKS = (('u8', 'Held-out 8-way', ('u8',)), ('seen_ba', 'Seen 32-way balanced', ('seen_ba',)),
                  ('wearable_12', 'Wearable-102 12-way', ('dry', 'wet')))
# The plan's name key (section 2.1), one row per site name, in the plan's order. The plan's combined rows ("coherence
# head, signed coherence head"; "cross-spectral ridge, whitened, with quadrature") are one row per name here, with the
# names the blocks give; the plan puts CCA-RAW under "joint CCA", the released file names it "CCA (no training)", and
# the released name stands (one name for one set of scores).
NAME_ORDER = ('harmonic sum (no training)', 'joint CCA', 'common-direction sum', 'eigenvalue head',
              'joint eigenvalue head', 'spectral eigenvalue head', 'spectral harmonic sum (no training)',
              'coherence head', 'signed coherence head', 'top-three ridge', 'harmonic max (no training)',
              'all-component sum (no training)', 'joint all-component sum (no training)', 'cross-spectral ridge',
              'whitened cross-spectral ridge', 'cross-spectral ridge with quadrature', 'cross-spectral MLP',
              'filter-bank CCA (seven sub-bands)')
# One set of scores under one site name (the held-out and seen doubles every listed level must share to the last bit).
SHARED = (
    ('CCA (no training)', 'u8', (('xspec', 'CCA-RAW/u8'), ('coherence_eigen', 'CCA-RAW/u8'),
                                 ('coherence_eigen', 'JOINT-TOP/u8'), ('harmonic_pooling', 'CCA-RAW/u8'),
                                 ('practical_settings', 'w500-c8/CCA-RAW-H3/u8'), ('harmonic_gap', 'J/u8')),
     ('cca_diagnostics', 'CCA-RAW/u8')),
    ('CCA (no training)', 'seen_ba', (('xspec', 'CCA-RAW/seen_ba'), ('coherence_eigen', 'CCA-RAW/seen_ba'),
                                      ('coherence_eigen', 'JOINT-TOP/seen_ba'), ('harmonic_pooling', 'CCA-RAW/seen_ba'),
                                      ('practical_settings', 'w500-c8/CCA-RAW-H3/seen_ba')),
     ('cca_diagnostics', 'CCA-RAW/seen_ba')),
    ('matched CCA', 'dry', (('harmonic_pooling_wearable', 'CCA-RAW/dry'), ('harmonic_gap', 'J/dry')),
     ('wearable_transfer', 'CCA-RAW/dry')),
    ('matched CCA', 'wet', (('harmonic_pooling_wearable', 'CCA-RAW/wet'), ('harmonic_gap', 'J/wet')),
     ('wearable_transfer', 'CCA-RAW/wet')),
    ('harmonic sum (no training)', 'u8', (('coherence_eigen', 'RAW-HARM-SUM/u8'), ('harmonic_pooling', 'RAW-HARM-SUM/u8'),
                                          ('practical_settings', 'w500-c8/RAW-HARM-SUM-H3/u8'), ('harmonic_gap', 'S/u8'),
                                          ('fixed_decay', 'H3-FLAT/u8'), ('rising_weights', 'flat/u8')), None),
    ('harmonic sum (no training)', 'seen_ba', (('coherence_eigen', 'RAW-HARM-SUM/seen_ba'),
                                               ('harmonic_pooling', 'RAW-HARM-SUM/seen_ba'),
                                               ('practical_settings', 'w500-c8/RAW-HARM-SUM-H3/seen_ba'),
                                               ('fixed_decay', 'H3-FLAT/seen_ba'), ('rising_weights', 'flat/seen_ba')),
     None),
    ('harmonic sum (no training)', 'dry', (('harmonic_pooling_wearable', 'RAW-HARM-SUM/dry'), ('harmonic_gap', 'S/dry'),
                                           ('fixed_decay', 'H3-FLAT/dry'), ('rising_weights', 'flat/dry')), None),
    ('harmonic sum (no training)', 'wet', (('harmonic_pooling_wearable', 'RAW-HARM-SUM/wet'), ('harmonic_gap', 'S/wet'),
                                           ('fixed_decay', 'H3-FLAT/wet'), ('rising_weights', 'flat/wet')), None),
    ('eigenvalue head', 'u8', (('coherence_eigen', 'EIG-RAW/u8'), ('harmonic_pooling', 'EIG-RAW/u8'),
                               ('practical_settings', 'w500-c8/EIG-RAW6-RIDGE/u8')), None),
    ('eigenvalue head', 'seen_ba', (('coherence_eigen', 'EIG-RAW/seen_ba'), ('harmonic_pooling', 'EIG-RAW/seen_ba'),
                                    ('practical_settings', 'w500-c8/EIG-RAW6-RIDGE/seen_ba')), None),
    ('top-three ridge', 'u8', (('harmonic_pooling', 'RAW-LEAD3-RIDGE/u8'),
                               ('practical_settings', 'w500-c8/RAW-LEAD3-RIDGE/u8')), None),
    ('top-three ridge', 'seen_ba', (('harmonic_pooling', 'RAW-LEAD3-RIDGE/seen_ba'),
                                    ('practical_settings', 'w500-c8/RAW-LEAD3-RIDGE/seen_ba')), None),
    ('filter-bank CCA (seven sub-bands)', 'u8', (('practical_settings', 'w500-c8/FBCCA-M3-N7-H5/u8'),
                                                 ('fixed_decay', 'FBCCA-DECAY/u8')), None),
    ('filter-bank CCA (seven sub-bands)', 'seen_ba', (('practical_settings', 'w500-c8/FBCCA-M3-N7-H5/seen_ba'),
                                                      ('fixed_decay', 'FBCCA-DECAY/seen_ba')), None),
)
# A site name a shared row's levels may carry beside its primary one: "joint CCA" is JOINT-TOP on card 9 and J on card
# 12, the same scores as CCA (no training) on BETA and as card 7's matched CCA on Wearable-102.
ALIASES = {'CCA (no training)': {'joint CCA'}, 'matched CCA': {'joint CCA'}}
# The engineering disclosures (plan section 2.1): each row's phrases must stand in the pinned record it names.
DISCLOSURES = (
    {'card': 8, 'study': 'xspec', 'stage': 'before scoring', 'kind': 'engineering correction',
     'what': 'a package metadata and module version declaration that did not match, corrected before BETA was '
             'processed',
     'scientific_protocol_changed': False, 'supervised_accuracy_used': False,
     'stated_in': ('xspec', 'xspec_handoff', '', (
         'Two disclosed pre-score engineering corrections occurred',
         'a package metadata/module version declaration mismatch before BETA processing',
         'No supervised accuracy was used for either correction.'))},
    {'card': 8, 'study': 'xspec', 'stage': 'before scoring', 'kind': 'engineering correction',
     'what': 'float32 centring in a scalar identity diagnostic, corrected to float64 with the tolerances unchanged',
     'scientific_protocol_changed': False, 'supervised_accuracy_used': False,
     'stated_in': ('xspec', 'xspec_handoff', '', (
         'float32 centering in a scalar identity diagnostic, corrected to float64 without changing the scientific '
         'protocol or tolerances',
         'No supervised accuracy was used for either correction.'))},
    {'card': 9, 'study': 'coherence_eigen', 'stage': 'before execution', 'kind': 'edge correction',
     'what': 'the frozen zero-channel-energy rule enforced where squaring the channel energy underflows, covered by a '
             'synthetic regression test',
     'scientific_protocol_changed': False, 'real_inputs_processed_before': False,
     'stated_in': ('eigen', 'eigen_freeze', '/pre_execution_correction',
                   ('Enforce frozen zero-channel-energy rule even when energy squaring underflows',
                    'No real follow-up input processed or fits yet.'))},
    {'card': 9, 'study': 'coherence_eigen', 'stage': 'before execution', 'kind': 'synthetic test suite',
     'what': 'an initial synthetic test suite timed out and is not counted as a pass; a bounded synthetic-only '
             'rerun passed all its tests',
     'counted_as_pass': False, 'rerun_tests_passed': 20,
     'stated_in': ('eigen', 'eigen_handoff', '', (
         'An initial synthetic filesystem suite timed out', 'it is not counted as a pass',
         'A bounded final synthetic-only run on a temporary memory filesystem passed all 20 tests'))},
)
WEIGHTS_NOT_PUBLISHED = blocks_weights.NOT_PUBLISHED[:4]   # the fifth is restated release-wide (D23, cards 8 to 14)
TOL = 1e-12

REFUSED_KEYS = {'pid', 'job', 'private_root', 'remote_root', 'indices_sha256', 'per_seed_descriptive', 'privacy',
                'protected_trials', 'exported_at_utc', 'updated_at', 'release_governed_by', 'one_period_prediction',
                'interpretation', 'epochs', 'path', 'handoff_path', 'export_path', 'thread', 'thread_bet', 'bet',
                'release_status', 'random_pairing', 'canary_real_label_accuracy_descriptive_only',
                'retrospective_gap_ratio', 'cpu_ms_per_call', 'cpu_ms_per_trial', 'frequencies_hz',
                'near_orthogonal_frequencies_hz', 'candidates_hz'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_seed', 'subject', 'prediction', 'probabilit', 'confusion', 'percentile', 'quantile',
                         'elapsed', 'timing', 'memory', 'device', 'host', 'private', 'path', 'fifty', '055', '_utc',
                         'seconds', 'latency', 'checkpoint', 'canary', 'comment', 'forecast')
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\bSubject\d+|\.(?:npz|npy|edf|mat|pt|ckpt|py)\b', re.IGNORECASE)
# R5 M7, the token rule for the commenter's confidence figure (page text and every string of this file).
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                              re.IGNORECASE)
HASH = re.compile(r'[0-9a-f]{64}')        # a SHA-256 may hold any digit pair
CONFIDENCE_VALUE = 11 / 20             # the figure as a fraction, written as a ratio so it is never spelled here
THREAD_TEXT = re.compile(r'huggingface|hugging face|/posts/|commenter|comment thread|\bbet\b', re.IGNORECASE)
HOST_TEXT = re.compile(r'threadripper|ryzen|\bamd\b|(?<![\d.])7965(?!\d)|epyc|xeon|\bintel\b|ubuntu|darwin|macos'
                       r'|\btrx\w*|gal4|bigdata', re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d'
                           r'|\bgenerated \d', re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
CLAIMS = re.compile(r'outperform|\bbeats?\b|superior|\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|leaderboard'
                    r'|state[- ]of[- ]the[- ]art|significan|equivalen|\bcausal|\bclinical\b|\bmedical\b|\bonline\b'
                    r'|real-time|closed-loop|zero-shot|\bendorse|fastest', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none|nothing|outside)\b|n't\b", re.IGNORECASE)
HEDGE = re.compile(r',\s+not\s|\bnot\s+\w+(?:\s+\w+){0,4},\s+but\b', re.IGNORECASE)
# Released records copied as they are (they carry review dates, versions and their own wording).
VERBATIM = re.compile(r'^\$\.rights\.(?:datasets\.\w+\.(?!published_here|cards)|credits\.fbcca\.(?:reference|short)$)')


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


def floats(value):
    return {v for v in numbers(value) if isinstance(v, float)}


def one(values, label):
    """The single value every study states, or a refusal naming the disagreement."""
    distinct = {json.dumps(v, sort_keys=True) for v in values}
    require(len(distinct) == 1, f'{label}: the studies state {sorted(distinct)}')
    return values[0]


def approval_of(block):
    return block.get('approval_sha256') or block.get('release_approval_sha256')


def endpoint_of(level_id):
    return level_id.rsplit('/', 1)[1]


# ---------------------------------------------------------------------------- inputs and bindings
def module_pins(manifest):
    """The manifest pins exactly what each block module pins: a pin changed in one place only is refused."""
    require(tuple(manifest['blocks']) == tuple(MODULES), 'the manifest lists other block modules')
    for m, module in MODULES.items():
        block = manifest['blocks'][m]
        require(block['module'] == f'pipeline/publication/ssvep_followups/{Path(module.__file__).name}',
                f'{m}: the manifest names another module')
        require(block['pins'] == {k: dict(v) for k, v in module.PINS.items()},
                f'{m}: the manifest pins other files than {Path(module.__file__).name}')
        require(tuple(block['studies']) == tuple(s for s in STUDIES if manifest['sources'][s]['block'] == m),
                f'{m}: the manifest assigns other studies')
        require(tuple(block['studies']) == tuple(module.STUDIES), f'{m}: the module builds other studies')
    require(manifest['blocks']['eigen']['reads_pins_of'] == 'xspec', 'eigen: card 8’s pins are read from xspec')


def declared_edits(manifest):
    """The manifest declares exactly what each module leaves out, study by study."""
    de = manifest['declaredEdits']
    require(tuple(de) == STUDIES + (COMPONENT,), 'declared edits: not one entry per study')
    for study, entry in de.items():
        m = manifest['sources'][study]['block'] if study in STUDIES else manifest['componentSource'][study]['block']
        require(entry['applied_by'] == m, f'{study}: declared edits name another module')
        require(entry['not_selected'] == list(MODULES[m].DECLARED_EDITS[study]),
                f'{study}: the declared edits differ from the module')


def load(manifest):
    """The pinned inputs this assembler reads itself; the block modules read and check their own."""
    docs = {'owner': read_pinned(manifest['approval']['ownerDecisions'], 'owner decisions')}
    for group in ('planning', 'published', 'credits', 'crossChecks'):
        for k, r in manifest[group].items():
            docs[k] = read_pinned(r, k)
    for study, h in manifest['handoffContext'].items():
        docs[f'handoff:{study}'] = read_pinned(h, f'{study} handoff')
        if 'queue_handoff' in h:
            docs[f'queue_handoff:{study}'] = read_pinned(h['queue_handoff'], f'{study} queue row handoff')
    for m, block in manifest['blocks'].items():
        for k, r in block['pins'].items():
            docs[f'{m}:{k}'] = read_pinned(r, f'{m} {k}')
    for k, r in manifest['contextPins'].items():
        docs[f'context:{k}'] = read_pinned(r, f'context {k}')
    return docs


def context_bindings(manifest):
    """Each context-only pin is bound by a pinned record: by its SHA-256, or by its file name where the record names it
    so. Context pins are never a copy source and nothing of them enters the file."""
    for k, r in manifest['contextPins'].items():
        require(r['role'] == 'context only, never a copy source', f'context {k}: a copy source')
        by = manifest['blocks'][r['block']]['pins'].get(r['bound_by'])
        require(by is not None, f'context {k}: bound by an unpinned record')
        text = location(by['path']).read_bytes().decode('utf-8')
        if r['binding'] == 'sha256':
            require(r['sha256'] in text, f'context {k}: {r["bound_by"]} does not bind its SHA-256')
        else:
            require(r['binding'] == 'file name' and Path(r['path']).name in text,
                    f'context {k}: {r["bound_by"]} does not name it')


def module_docs(manifest):
    """Each module's own reading of its pins (the module re-checks every hash)."""
    p = {m: {k: dict(v) for k, v in b['pins'].items()} for m, b in manifest['blocks'].items()}
    return {m: MODULES[m].load(p[m])[0] for m in MODULES}


def bindings(docs, manifest):
    owner = docs['owner']
    require(owner['freeze_date'] == manifest['freeze_date'].replace('-', '') == RELEASE_ID.rsplit('-', 1)[1],
            'the freeze date is not the release id’s')
    d = owner['decisions']
    require('the seven SSVEP studies (rows 12, 14, 15, 20, 21, 32, 33)' in d['D14']['answer'],
            'owner decision D14 does not publish the seven SSVEP studies')
    defaults = d['defaults_stated_to_owner_and_not_objected']
    require('new cards state only their prespecified criteria' in defaults['D23 (Q9)']
            and 'never summed, no host label' in defaults['D25 (Q11)']
            and 'new-ssvep-frequencies-update.json keeps its bytes' in defaults['D28 (Q14)']
            and 'D6 (the HF commenter is not named)' in d['carried_over'], 'the owner defaults D6, D23, D25 or D28 changed')
    a1 = owner['gates']['A1']
    require(a1['status'] == 'done' and a1['sha256'] == manifest['blocks']['xspec']['pins']['xspec_export']['sha256']
            and a1['local'] == manifest['blocks']['xspec']['pins']['xspec_export']['path'],
            'gate A1: the cross-spectral aggregate is not the copy the owner record names')
    # Each study's handoff: the hash its module, its approval's binding and its queue row name.
    rows = docs['queue']['rows']
    for study, h in manifest['handoffContext'].items():
        m = h['block']
        module = MODULES[m]
        require(h['role'] == 'context only, never a copy source', f'{study}: a handoff is a copy source')
        if study in getattr(module, 'HANDOFF_CONTEXT', {}):
            ctx = module.HANDOFF_CONTEXT[study]
            require(ctx['bound_sha256'] == h['sha256'] and ctx['bound_by'] == h['bound_by'],
                    f'{study}: the handoff differs from the module’s')
        pin = next((k for k, v in manifest['blocks'][m]['pins'].items() if v['path'] == h['path']), None)
        require(pin is None or manifest['blocks'][m]['pins'][pin]['sha256'] == h['sha256'], f'{study}: two handoff pins')
        src = manifest['sources'].get(study) or manifest['componentSource'][study]
        require(h['queue_row'] == src['queue_row'], f'{study}: another queue row than its source')
        # The queue row names the study's handoff, or, for the CPU components, the parent handoff that asked for them.
        named = h.get('queue_handoff', h)
        row = rows[h['queue_row']]
        require(row['source_sha256'] == named['sha256'] and row['canonical_handoff'] == named['path'],
                f'{study}: queue row {h["queue_row"]} names another handoff')
        if named is not h:
            require(named['role'] == h['role'] and named['states'] in docs[f'queue_handoff:{study}'],
                    f'{study}: the queue row’s handoff does not ask for this study')
    context_bindings(manifest)
    # The released file keeps its bytes (D28): the 2026-10-20 export audit's hash, both served copies.
    rel, audit10 = manifest['published']['released'], docs['releasedAudit']
    require(audit10['status'] == 'pass' and audit10['export_sha256'] == rel['sha256']
            and audit10['manifest_sha256'] == manifest['published']['releasedManifest']['sha256']
            and audit10['release_id'] == RELEASED_ID == docs['released']['release_id'],
            'the released file is not the one the 2026-10-20 export audit names')
    require(sha(RELEASED_SERVED.read_bytes()) == rel['sha256'], 'the served released copy differs')
    for m, block in manifest['blocks'].items():
        for k, r in block['pins'].items():
            if r['path'] == rel['path']:
                require(r['sha256'] == rel['sha256'], f'{m} {k}: another released file')
    cards = {c['card']: c for c in docs['released']['placement']['cards']}
    require(cards[SUPERSEDED_CARD] == {'card': SUPERSEDED_CARD, 'anchor': 'cross-spectral', 'studies': [],
                                       'status_only': True}, 'the released card 8 is not the status entry')
    require(manifest['crossChecks']['cca_diagnostics']['sha256']
            == docs['releasedManifest']['blocks']['cca']['pins']['diag_export']['sha256'],
            'the CCA diagnostics export is not card 5’s')


def build_blocks(manifest):
    """The eight study blocks, each module given the manifest's own pins."""
    p = {m: {k: dict(v) for k, v in b['pins'].items()} for m, b in manifest['blocks'].items()}
    built = {}
    for m, module in MODULES.items():
        built.update(module.build_blocks(p[m], p['xspec']) if m == 'eigen' else module.build_blocks(p[m]))
    require(set(built) == set(STUDIES), f'the modules built {sorted(built)}')
    blocks = {s: built[s] for s in STUDIES}
    for study in STUDIES:
        src, pins = manifest['sources'][study], p[manifest['sources'][study]['block']]
        require(blocks[study]['source_sha256'] == pins[src['export']]['sha256'], f'{study}: another source')
        require(blocks[study]['review_sha256'] == pins[src['review']]['sha256'], f'{study}: another review')
        require(approval_of(blocks[study]) == pins[src['approval']]['sha256'], f'{study}: another approval')
    cpu, src = blocks['practical_settings'][COMPONENT], manifest['componentSource'][COMPONENT]
    require(cpu['source_sha256'] == p['practical'][src['export']]['sha256']
            and cpu['review_sha256'] == p['practical'][src['review']]['sha256']
            and cpu['release_approval_sha256'] == p['practical'][src['approval']]['sha256'], 'cpu components: sources')
    return blocks


# ---------------------------------------------------------------------------- what spans the studies
def card_endpoints(blocks, studies):
    found = {endpoint_of(lid) for s in studies for lid in blocks[s]['levels']}
    return [e for e in ENDPOINT_ORDER if e in found]


def placement_block(blocks):
    cards = []
    for card, anchor, studies in CARDS:
        for s in studies:
            b = blocks[s]
            require(b.get('card', card) == card and b.get('anchor', anchor) == anchor, f'{s}: another card or anchor')
        entry = {'card': card, 'anchor': anchor, 'studies': list(studies), 'endpoints': card_endpoints(blocks, studies)}
        if card == SUPERSEDED_CARD:
            entry['supersedes'] = {'release_id': RELEASED_ID, 'file': RELEASED_FILE, 'entry': 'status_only'}
        cards.append(entry)
    return {
        'page': PAGE, 'group': 'adapting', 'leaderboard': False, 'new_page_count': 0, 'new_dataset_count': 0,
        'new_model_count': 0,
        'card_order': 'the order of the consolidated handoff; cards 1 to 8 keep their numbers and anchors',
        'reads_with': {'release_id': RELEASED_ID, 'file': RELEASED_FILE, 'cards': [1, 2, 3, 4, 5, 6, 7]},
        'cards': cards,
    }


def endpoints_block(blocks):
    """The endpoint strip of cards 8 to 14: candidates and chance read from every block that states them."""
    out = []
    for eid, task, ids in ENDPOINT_TASKS:
        stated = []
        for s in STUDIES:
            for e, ep in blocks[s]['design'].get('endpoints', {}).items():
                if e in ids:
                    stated.append({'candidate_count': ep['candidate_count'], 'chance': ep['chance']})
        ep = one(stated, f'endpoint {eid}')
        require(abs(ep['chance'] - 1 / ep['candidate_count']) <= TOL, f'{eid}: chance is not one over the candidates')
        cards = [c for c, _, studies in CARDS if set(card_endpoints(blocks, studies)) & set(ids)]
        row = {'id': eid, 'task': task, 'candidates': ep['candidate_count'], 'chance': ep['chance'], 'cards': cards}
        if eid == 'wearable_12':
            row['sensors'] = list(ids)
        out.append(row)
    return out


def interval_methods_block(blocks):
    """Each card's own interval, as its block states it; the adjusted ones named once."""
    rows = [{'card': c, 'study': s, **blocks[s]['interval_method']} for c, _, studies in CARDS for s in studies]
    adjusted = []
    for row in rows:
        im = blocks[row['study']]['interval_method']
        if 'family' in im:
            f = im['family']
            require(f['adjustment'] == 'Bonferroni' and abs(f['level'] - (1 - 0.05 / f['comparisons'])) <= TOL,
                    f'{row["study"]}: the family level is not the Bonferroni level')
            adjusted.append({'card': row['card'], 'study': row['study'], 'applies_to': 'the primary family',
                             'adjustment': f['adjustment'], 'comparisons': f['comparisons'], 'level': f['level']})
        if 'equivalence' in im:
            adjusted.append({'card': row['card'], 'study': row['study'],
                             'applies_to': 'the prespecified margin test of the primary contrast',
                             'level': im['equivalence']['level'], 'margin': im['equivalence']['margin']})
        require(im['level'] == 0.95, f'{row["study"]}: another nominal level')
    require([a['card'] for a in adjusted] == [12, 13], 'only cards 12 and 13 adjust an interval')
    return rows, {'adjusted': adjusted, 'other_intervals_adjusted': False}


def name_key_block(blocks, released, shared):
    """One row per site name: the codes each block gives it; every code of every block in exactly one row. A name that
    shared rows list as an alias carries `alias_of`, the primary site names of those rows."""
    given = {}
    for study in STUDIES:
        for code, name in blocks[study]['display_names'].items():
            given.setdefault(name, []).append({'study': study, 'code': code})
    notes, keyed = {}, set()
    for m in MODULES.values():                 # the modules' name key rows: a plain code, or a code with its note
        for name, text in m.NAME_KEY:
            keyed.add(name)
            if ' ' in text and text not in notes.setdefault(name, []):
                notes[name].append(text)
    released_names = {r['site_name'] for r in released['name_key']}

    def row(name, codes, key):
        out = {'site_name': name, 'export_codes': ', '.join(dict.fromkeys(c['code'] for c in codes)), 'codes': codes,
               'key': key}
        if notes.get(name):
            out['note'] = '; '.join(notes[name])
        return out
    rows = []
    for name in NAME_ORDER:
        codes = given.pop(name, [])
        require(codes and name in keyed, f'name key: no block or module row for {name!r}')
        rows.append(row(name, codes, 'released' if name in released_names else 'new'))
    for name, codes in given.items():       # card 5 and 7 names as released, and names one card uses
        rows.append(row(name, codes, 'released' if name in released_names else 'card'))
    placed = [(c['study'], c['code']) for r in rows for c in r['codes']]
    require(len(placed) == len(set(placed)), 'name key: a code sits in two rows')
    require(all(r['key'] == 'new' for r in rows[:len(NAME_ORDER)]), 'name key: a plan row is a released name')
    alias_of = {}
    for r in shared:
        for a in r.get('aliases', []):
            alias_of.setdefault(a, []).append(r['site_name'])
    by_name = {r['site_name']: r for r in rows}
    for a, names in alias_of.items():
        require(a in by_name, f'name key: no row for the alias {a!r}')
        by_name[a]['alias_of'] = list(dict.fromkeys(names))
    return rows


def card_of_study(study):
    return next(c for c, _, studies in CARDS if study in studies)


def shared_estimates_block(blocks, released):
    """One set of scores per row, with its primary site name, its aliases, and its interval's home card.

    Every card keeps its own source interval in its study block. `interval_home` is the card that first released the
    level with an interval (card 5 or card 7 for a level released on 2026-10-20, else the first card of this release
    whose block gives one); `intervals_differ_by_card` says whether the intervals the cards give for the row's scores
    differ (each study's bootstrap draws its own). The page prints a shared level's interval on its home card only and
    names that card elsewhere."""
    released_cards = {s: c['card'] for c in released['placement']['cards'] for s in c['studies']}
    out = []
    for name, e, members, rel in SHARED:
        values = [blocks[s]['levels'][lid]['estimate'] for s, lid in members]
        if rel:
            values.append(released['studies'][rel[0]]['levels'][rel[1]]['estimate'])
        require(len(set(values)) == 1, f'{name} {e}: not one set of scores')
        shown = [blocks[s]['display_names'][lid.split('/')[-2]] for s, lid in members]
        aliases = sorted(set(shown) - {name})
        require(set(aliases) <= ALIASES.get(name, set()), f'{name} {e}: another site name among {aliases}')
        # The intervals, in card order: the released level's first, then each card's own.
        cards = [card_of_study(s) for s, _ in members]
        require(cards == sorted(cards), f'{name} {e}: the levels are not in card order')
        stated = [(card, blocks[s]['levels'][lid]['interval']) for card, (s, lid) in zip(cards, members)]
        if rel:
            stated.insert(0, (released_cards[rel[0]], released['studies'][rel[0]]['levels'][rel[1]]['interval']))
        with_interval = [(card, iv) for card, iv in stated if iv is not None]
        require(with_interval, f'{name} {e}: no card gives an interval')
        home = with_interval[0][0]
        for (s, lid), card in zip(members, cards):     # a level a block marks as reused names the home card
            r = blocks[s].get('reused', {}).get(lid.split('/')[-2])
            require(r is None or r['card'] == home, f'{s} {lid}: reused from card {r and r["card"]}, home {home}')
        row = {'site_name': name, 'endpoint': e, 'levels': [{'study': s, 'level': lid} for s, lid in members]}
        if aliases:
            row['aliases'] = aliases
        if rel:
            row['released_level'] = {'release_id': RELEASED_ID, 'study': rel[0], 'level': rel[1]}
        row['interval_home'] = home
        row['intervals_differ_by_card'] = len({json.dumps(iv) for _, iv in with_interval}) > 1
        out.append(row)
    return out


def disclosures_block(mdocs, blocks):
    out = []
    for d in DISCLOSURES:
        m, pin, ptr, phrases = d['stated_in']
        for phrase in phrases:
            blocks_cca.stated(mdocs[m], pin, ptr, phrase, f'disclosure card {d["card"]}')
        row = {k: v for k, v in d.items() if k != 'stated_in'}
        row['stated_in_sha256'] = sha(MODULES[m].location(MODULES[m].PINS[pin]['path']).read_bytes())
        require(row['stated_in_sha256'] == MODULES[m].PINS[pin]['sha256'], f'disclosure: {pin} changed')
        out.append(row)
    require(sum(r['study'] == 'xspec' for r in out) == blocks['xspec']['checks']['pre_score_corrections']['count'],
            'the cross-spectral corrections are not the two the block counts')
    require('zero_energy_edge_fix' in blocks['coherence_eigen']['limitations_keys']
            and 'synthetic_suite_timeout_not_a_pass' in blocks['coherence_eigen']['limitations_keys'],
            'card 9 does not carry its disclosures')
    return out


def rights_block(docs, blocks):
    rel = docs['released']['rights']['datasets']
    beta, wear = rel['beta'], rel['wearable_102']
    require(beta['license'] == wear['license'] == 'CC BY 4.0', 'another dataset licence')
    fb = docs['entityProfiles']['methods']['fbcca']
    require('Chen et al. 2015' in fb['aliases'] and fb['reference'].startswith('Chen X, Wang Y, Gao S, Jung T-P, Gao X.')
            and fb['reference_url'] == 'https://doi.org/10.1088/1741-2560/12/4/046008', 'the FBCCA profile changed')

    def uses_beta(design):
        return 'BETA' in design.get('datasets', {}) or design.get('dataset', {}).get('name') == 'BETA'
    beta_cards = [c for c, _, studies in CARDS if any(uses_beta(blocks[s]['design']) for s in studies)]
    wear_cards = [c for c, _, studies in CARDS if set(card_endpoints(blocks, studies)) & {'dry', 'wet'}]
    fb_cards = [c for c, _, studies in CARDS
                if any(code.startswith('FBCCA') for s in studies for code in blocks[s]['display_names'])]
    people = one([blocks[s]['design']['dataset']['people'] for s in STUDIES if 'dataset' in blocks[s]['design']
                  and blocks[s]['design']['dataset']['name'] == 'BETA'], 'BETA people')
    wpeople = one([blocks['harmonic_pooling_wearable']['design']['dataset']['people']]
                  + [blocks[s]['design']['datasets']['Wearable-102']['people']
                     for s in ('harmonic_gap', 'fixed_decay', 'rising_weights')],
                  'Wearable-102 people')
    recipe = blocks['practical_settings']['design']['fbcca']['description']['en']
    # The CPU components timed the B/D run's own heads and cells (blocks_practical binds the head seal), on BETA windows.
    practical = blocks['practical_settings']
    require(COMPONENT in practical and practical['design']['dataset']['name'] == 'BETA',
            'the CPU component medians are not measured on the BETA windows of card 11')
    return {
        'datasets': {
            'beta': {**{k: beta[k] for k in ('name', 'license', 'licenseUrl', 'source', 'rights_reviewed',
                                             'rights_record', 'citation')},
                     'publication_conditions': list(beta['publication_conditions']),
                     'cards': beta_cards,
                     'published_here': (f'Cohort aggregates over the {people} people for cards 8 to 14: levels and '
                                        'paired contrasts with their intervals, gap statistics in squared-correlation '
                                        'units, decision-change shares and check counts; and CPU component medians '
                                        'measured on BETA windows. No per-person, per-fold, per-rotation, per-window '
                                        'or per-frequency value.')},
            'wearable_102': {**{k: wear[k] for k in ('name', 'title', 'paper_citation', 'license',
                                                     'canonical_version_doi', 'local_representation',
                                                     'dataset_citation', 'readme', 'consent_scope')},
                             'primary_sources': list(wear['primary_sources']),
                             'cards': wear_cards,
                             'published_here': (f'Cohort aggregates over the {wpeople} people, by sensor, for cards '
                                                f'{", ".join(map(str, wear_cards[:-1]))} and {wear_cards[-1]}: levels and '
                                                'paired contrasts with their intervals, gap statistics and check '
                                                'counts. No per-person, per-window, per-frequency or questionnaire '
                                                'value.')},
        },
        'credits': {
            'fbcca': {'name': 'FBCCA', 'short': 'Chen et al. 2015', 'reference': fb['reference'],
                      'reference_url': fb['reference_url'], 'method_page': '/methods/fbcca/', 'cards': fb_cards,
                      'used_for': recipe, 'code_distributed': False},
        },
    }


def cross_checks(blocks):
    """Reused levels carry the card they come from; the levels in `reused` exist; the bet stays on card 4."""
    for s in STUDIES:
        for code, r in blocks[s].get('reused', {}).items():
            require(r['card'] in (5, 7, 8, 9) and any(lid.split('/')[-2] == code for lid in blocks[s]['levels']),
                    f'{s} {code}: a reused level without its card')
        require('thread_bet' not in blocks[s], f'{s}: a thread prediction on a new card')


# ---------------------------------------------------------------------------- the boundary
def private_names(mdocs):
    """The user, project, volume and host names the private records use, read from them."""
    text = ''.join(json.dumps(mdocs[m][k]) for m, k in (
        ('xspec', 'xspec_protocol'), ('eigen', 'eigen_protocol'), ('pooling', 'ac_protocol'),
        ('practical', 'bd_protocol'), ('practical', 'timing_protocol'), ('weights', 'gap_protocol'),
        ('weights', 'decay_protocol'), ('weights', 'rise_protocol')))
    names = set()
    for root in ('home', 'Volumes', 'mnt', 'Users'):
        for a, b in re.findall(rf'/{root}/([^/\s"]+)/([^/\s"]+)', text):
            names.add(a)
            if re.search(r'[_\d]|[a-z][A-Z]|^[A-Z]+$', b):     # project folders, not plain words
                names.add(b)
    names |= set(re.findall(r'"([a-z]+)_code"', text)) & set(re.findall(r'"([a-z]+)_private"', text))
    return {n for n in names if len(n) >= 3}


def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            require(not ('frequenc' in k.lower() and isinstance(v, list) and len(v) > 2),
                    f'a list of frequencies in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def authored(trail):
    """Text this assembler writes, apart from the study blocks, the released records and the hashes."""
    return not (trail.startswith(('$.studies', '$.provenance')) or VERBATIM.match(trail)
                or trail in ('$.schema_version', '$.release_id'))


def prose_check(payload, private):
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(HASH.fullmatch(text) or not CONFIDENCE_TOKEN.search(text), f'{trail}: the commenter’s figure never appears')
        require(not blocks_cca.REFUSED_TEXT.search(text), f'{trail}: refused text')
        require(trail.startswith('$.not_published') or not THREAD_TEXT.search(text),
                f'{trail}: the comment thread is not part of the new cards')
        require(not HOST_TEXT.search(text), f'{trail}: a host, processor or system label')
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


def withheld_values(mdocs):
    """Figures the aggregates hold that this release does not publish: the cross-spectral and coherence per-seed,
    canary and random-pairing accuracies, the weighting aggregates' ratio table, Delta metrics and nominal family
    intervals, and the CPU-time readings of the component measurements; less any figure a selected field also holds."""
    x, e = mdocs['xspec']['xspec_export'], mdocs['eigen']['eigen_export']
    held = blocks_xspec.withheld(x, {k: x[k] for k in ('arms', 'contrasts')})
    held |= blocks_xspec.withheld(e, {k: e[k] for k in ('arms', 'contrasts', 'prespecified_eigenvalue_claim')})
    held |= blocks_weights.withheld_values(mdocs['weights'])
    rows = mdocs['practical']['timing_aggregate']['component_summaries']
    cpu = floats([[r.get('cpu_ms_per_call'), r.get('cpu_ms_per_trial')] for r in rows])
    wall = floats([[r['wall_ms_per_call'], r['wall_ms_per_trial']] for r in rows])
    return held | (cpu - wall - {0.0})


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['holds'] == [], 'this release has no hold')
    require(tuple(manifest['sources']) == STUDIES, 'the manifest lists other studies')
    require([manifest['sources'][s]['card'] for s in STUDIES] == [c for c, _, ss in CARDS for _ in ss],
            'the manifest assigns other cards')
    module_pins(manifest)
    declared_edits(manifest)
    docs = load(manifest)
    bindings(docs, manifest)
    mdocs = module_docs(manifest)
    blocks = build_blocks(manifest)
    cross_checks(blocks)
    released = docs['released']
    methods, adjustment = interval_methods_block(blocks)
    shared = shared_estimates_block(blocks, released)
    for item in WEIGHTS_NOT_PUBLISHED:
        require(item in manifest['notPublished'], f'the not-published list leaves out {item[:40]!r}')
    rr = manifest['releaseRecord']
    pins = {m: b['pins'] for m, b in manifest['blocks'].items()}
    cpu_src = manifest['componentSource'][COMPONENT]
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['freeze_date'],
        'status': manifest['approval']['decision'],
        'title': 'New SSVEP frequencies, cards 8 to 14',
        'question': released['question'],
        'placement': placement_block(blocks),
        'metric_units': ('Accuracies, balanced accuracies, decision-change shares, pairwise win fractions and chance '
                         'levels are proportions in [0,1]. An entry with unit "difference of proportions" is a paired '
                         'difference, stored as a proportion: multiply by 100 for percentage points. Entries with unit '
                         '"squared correlation" or "difference of squared correlations" (card 12’s gap G and residual '
                         'R) are score units and never percentages. CPU component figures are milliseconds. Counts of '
                         'people, windows, folds, rotations, fits, draws, calls and candidates are whole numbers. "no '
                         'training" or "deterministic fit" stands where a trained level gives its seed count; null '
                         'means not defined or not computed, never zero.'),
        'scope': ('Seven audited follow-ups to route 3 on SSVEP frequencies a decoder never trained on, cards 8 to 14 '
                  'of the page. All seven use the BETA cohort route 3 studied; cards 10, 12, 13 and 14 also report '
                  'Wearable-102, dry and wet. Card 8 gives the results of the cross-spectral round whose status card '
                  'the earlier file carries. Each study block is read from its own audited aggregate and carries its '
                  'own interval method. Seen and held-out results are separate tasks, reported side by side. Every '
                  'figure compares set-ups on fixed splits.'),
        'endpoints': endpoints_block(blocks),
        'interval_methods': methods,
        'interval_adjustment': adjustment,
        'name_key': name_key_block(blocks, released, shared),
        'shared_estimates': shared,
        'studies': blocks,
        'engineering_disclosures': disclosures_block(mdocs, blocks),
        'rights': rights_block(docs, blocks),
        'release_record': {
            'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
            'rights': rr['rights'], 'research_release': rr['researchRelease'], 'binding': rr['binding'],
        },
        'not_published': list(manifest['notPublished']),
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {s: blocks[s]['source_sha256'] for s in STUDIES}
            | {COMPONENT: pins[cpu_src['block']][cpu_src['export']]['sha256']},
            'release_approval_sha256': {s: approval_of(blocks[s]) for s in STUDIES}
            | {COMPONENT: pins[cpu_src['block']][cpu_src['approval']]['sha256']},
            'handoff_sha256': {s: h['sha256'] for s, h in manifest['handoffContext'].items()},
            'released_file': {'release_id': RELEASED_ID, 'file': RELEASED_FILE,
                              'sha256': manifest['published']['released']['sha256'], 'unchanged': True,
                              'export_audit_sha256': manifest['published']['releasedAudit']['sha256']},
            'owner_decisions_sha256': manifest['approval']['ownerDecisions']['sha256'],
            'plan_sha256': manifest['planning']['plan']['sha256'],
            'queue_sha256': manifest['planning']['queue']['sha256'],
            'consolidated_handoff_sha256': manifest['planning']['consolidatedHandoff']['sha256'],
        },
    }

    scrub_check(payload)
    private = private_names(mdocs)
    require(len(private) >= 4, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    confidence_absent(payload)
    validate_public(payload)
    published = set(numbers(payload))
    leaked = [v for v in withheld_values(mdocs) if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    return payload


def inputs_available():
    """Whether the pinned inputs are on this machine. The research folders are local-only, so a clone checks the served
    file against the committed export audit's hash; only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all(location(r['path']).exists() for r in input_refs(manifest))


def serialized_export(manifest_bytes=None):
    """The served bytes built from `manifest_bytes` (the release manifest's own bytes by default). The audit calls this
    in a separate process to bind every editorial string of the served file to this program."""
    data = MANIFEST.read_bytes() if manifest_bytes is None else manifest_bytes
    return (json.dumps(build(data), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_ssvep_followups_export
    return audit_ssvep_followups_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
