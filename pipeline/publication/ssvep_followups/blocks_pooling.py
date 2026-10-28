"""The pooling blocks of the SSVEP follow-ups release: card 10, pooling CCA's per-harmonic statistics (queue row 32).

The practical suite's modules A and C, read from the A/C release audit summary that embeds both verified aggregates,
and turned into two study blocks for `ssvep-followups-update.json`, which its assembler puts under `studies`:

- `harmonic_pooling` (module A, BETA held-out and seen tasks): the top-three ridge (35 new fits) beside the fixed
  pooling rules (harmonic max, all-component sum, joint all-component sum) and the comparators it reuses unchanged
  (the eigenvalue heads and the harmonic sum of card 9, CCA of card 5); three primary and three secondary held-out
  contrasts, 2,000 draws with seed 20261015; the seen-32 levels are descriptive;
- `harmonic_pooling_wearable` (module C, Wearable-102 dry and wet): the 35 BETA heads of each learned arm averaged
  into one affine function and run unchanged (0 target fits) on the windows of card 7, ties by the first native
  candidate index; one primary and four secondary contrasts per sensor, 2,000 draws with seed 20261020, conditional on
  the fixed source heads. Its CCA row is a level only: it is card 7's matched CCA, and the block refuses it unless the
  estimate equals the value card 7 released (`site/src/data/new-ssvep-frequencies-update.json`).

Release status is read from `state/AC-release-approval.json` and the two reviews it binds, never from the summary's
own status, its `root_final_release_approval_pending` flag or the aggregates' `release_status`. The approval binds the
separate A and C aggregate files by hash; they are not on this machine, so the summary's embedded copies are used,
the approval must bind the same hashes the summary names, and every contrast is checked against the release review's
tables and every level against the approved handoff's tables at the four decimals they print. Every number is the
source's own double: nothing is rounded, rescaled or recomputed, and units stay fractions. The pinned protocol,
summary and reviews carry private storage paths, so they are read and checked here, never copied.

A block is a mapping with the fields of the blocks of the 2026-10-20 release (see blocks_cca.py):
- `source_sha256` (the summary), `review_sha256` (the release review), and the other pinned records by name;
- `interval_method`: `{method, draws, seed, level}`, plus `conditional_on` for the Wearable-102 block;
- `design`: the dataset, the endpoints with their chance levels and roles, and the arms;
- `levels`: `{id: {estimate, interval, unit, people, seeds, origin}}`; an id is `<code>/<endpoint>` (`u8`, `seen_ba`;
  `dry`, `wet`); `origin` is `new`, `reused_cca_diagnostics` (card 5), `reused_coherence_eigen` (card 9) or
  `reused_wearable_transfer` (card 7), and a reused level is checked bit for bit against its source;
- `level_only`: `{level id: the card 7 level it is}`; such a level has `interval: None`;
- `contrasts`: `{id: {role, left, right, estimate, interval, unit, people, seeds, flags}}`; `role` is the study's own
  `primary` or `secondary`; `flags` are derived here (`interval_includes_zero`, `direction`, `levels_equal`);
- `contrast_limitations`, `undefined`, `not_run`, `checks`, `limitations_keys`, `display_names`, `export_codes` as in
  the earlier blocks; `export_codes` point into the summary (`#<JSON pointer>`), the coherence aggregate
  (`coherence_aggregate#…`) or the released file (`new-ssvep-frequencies-update.json#…`).

    python3 pipeline/publication/ssvep_followups/blocks_pooling.py     # builds and prints the counts; writes nothing
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:                      # run directly rather than imported from the pipeline
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import FORBIDDEN_KEYS, validate_public  # noqa: E402
from ssvep_followups.blocks_cca import (                   # noqa: E402  generic helpers, shared with cards 5 to 7
    REFUSED_TEXT as CCA_REFUSED_TEXT, bound, close, count, interval, location, number, pointer, require, resolve,
    sha)

# ---------------------------------------------------------------------------- pinned inputs
# Paths are relative to the project; `research/...` resolves under `researchRoot` when local_paths.json sets one.
_P = 'research/ssvep_practical_suite_20261020'
_C = 'research/decision_route3_coherence_eigen_20261020'
_W = 'research/decision_route3_external_20261015'
PINS = {
    'ac_summary': {'path': f'{_P}/evidence/AC Release Audit Summary.json',
                   'sha256': 'daaa8dedbc8bcbf220b4c7788632ff71405827154f82ad0ef396c8590b682923'},
    'ac_approval': {'path': f'{_P}/state/AC-release-approval.json',
                    'sha256': 'f690cddd9670b5def27f84ab8bbb34a696db07b559d52197d85c256a11bf6e95'},
    'ac_release_review': {'path': f'{_P}/review/Independent A and C Release Review.md',
                          'sha256': '01004af64d42f9d63ff9c45872ecb41533b6e750b2a41911f9d26df5bc834cf9'},
    'ac_interpretation_review': {'path': f'{_P}/review/Independent A and C Interpretation Review.md',
                                 'sha256': '50da109cadf47c46551d20e854d4b03360863b19ac106dbe43b3b5a2d34bbd6c'},
    'ac_handoff': {'path': f'{_P}/Practical SSVEP A and C Results Handoff.md',
                   'sha256': 'aa6cdfd4b43bc9111545057104ce7a58cb5bafbbb3b8eaf85685293462e3dc0f'},
    'ac_protocol': {'path': f'{_P}/protocol.json',
                    'sha256': 'af34d538e689a6c9d49124d828b59989bb5ddf359a862818949ae7ce5f840ae5'},
    'ac_freeze': {'path': f'{_P}/execution-freeze.json',
                  'sha256': '0eb0cf8d07f4a560aa3842d6351e06369ac5c999d8238dec1ad3e411ba97bc78'},
    'ac_execution_review': {'path': f'{_P}/execution-review.json',
                            'sha256': 'b608a5189605c49cb654f83c2dc7bbe1708a0d59335e5e739433b1dfe9fc4dbe'},
    'pooling_runner': {'path': f'{_P}/scripts/run_pooling.py',
                       'sha256': 'de76ba6e3b437dcc226c61a94b099a732f007c406d9dea71a77ac9bcfef6add3'},
    'transfer_runner': {'path': f'{_P}/scripts/run_transfer.py',
                        'sha256': '00d9a0a5eaa25eb4d9ecc634a1d70eca9f7aea76e576c42339c81e76a8fe6c81'},
    # Card 9's study: the eigenvalue heads, the harmonic sum and CCA that module A reuses unchanged.
    'coherence_aggregate': {'path': f'{_C}/evidence/Completed Aggregate Results.json',
                            'sha256': '9ee6cc3a9a46c76faeec00b3d7b57a5fb66993389f85d001a443507becc6717d'},
    'coherence_approval': {'path': f'{_C}/state/release-approval.json',
                           'sha256': '4a0beb364285bdf3c4550eb7c89a1180acf5e565175c40195cc951d8c0a42702'},
    # Card 7's study: which windows, channel order, candidates and CCA the Wearable-102 block shares with it.
    'wear_protocol': {'path': f'{_W}/protocol.json',
                      'sha256': '079acad5374eb1b45245bb57c51ba384c5532eb7046d3b246634a592d02e223b'},
    'wear_freeze': {'path': f'{_W}/freeze.json',
                    'sha256': 'd24ddc66a542c80c06196935f5a6183e33782e0bbe72a7c0c53a80258cc1de30'},
    # The released 2026-10-20 file (D28: it keeps its bytes): card 5's CCA and card 7's matched CCA as released.
    'released': {'path': 'site/src/data/new-ssvep-frequencies-update.json',
                 'sha256': '197028bdc4dadd9713f6d408bb64204147fdfe39a686e7e119e4988aaf863ee0'},
}
TEXT_PINS = {'ac_release_review', 'ac_interpretation_review', 'ac_handoff', 'pooling_runner', 'transfer_runner'}
SERVED = {'released': 'site/public/data/new-ssvep-frequencies-update.json'}   # must be the same bytes as the src copy
RELEASED_FILE = 'new-ssvep-frequencies-update.json'                        # its served name, as export_codes cite it
RELEASED_ID = 'new-ssvep-frequencies-update-20261020'
# For the release manifest only: the handoff is context and a cross-check of printed levels, never a copy source.
HANDOFF_CONTEXT = {
    'harmonic_pooling': {'bound_sha256': 'aa6cdfd4b43bc9111545057104ce7a58cb5bafbbb3b8eaf85685293462e3dc0f',
                         'bound_by': 'ac_approval'},
    'harmonic_pooling_wearable': {'bound_sha256': 'aa6cdfd4b43bc9111545057104ce7a58cb5bafbbb3b8eaf85685293462e3dc0f',
                                  'bound_by': 'ac_approval'},
}
APPROVED = 'APPROVED_AGGREGATE_A_C_HANDOFF'
STUDIES = ('harmonic_pooling', 'harmonic_pooling_wearable')
CARD, ANCHOR = 10, 'harmonic-pooling'
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'interval_method', 'levels', 'contrasts', 'undefined', 'not_run',
                'checks', 'limitations_keys', 'display_names', 'export_codes')

ENDPOINTS = {'u8': 'held8', 'seen_ba': 'seen32'}      # site id -> summary spelling (route 3's spelling of the tasks)
CONDITIONS = ('dry', 'wet')
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
NO_TRAINING, DETERMINISTIC = 'no training', 'deterministic fit'
A_SEED, C_SEED, DRAWS, LEVEL = 20261015, 20261020, 2000, 0.95
METHOD = 'paired person bootstrap, percentile interval'
TOL = 1e-12
NOISE = 1e-15                       # a contrast of two equal levels may carry float noise of this size, never more

# ---------------------------------------------------------------------------- arms and the name key (plan 2.1)
A_ARMS = ('RAW-HARM-MAX', 'RAW-HARM-ALLSUM', 'JOINT-ALLSUM', 'RAW-LEAD3-RIDGE', 'EIG-RAW', 'EIG-JOINT',
          'RAW-HARM-SUM', 'CCA-RAW')                         # the summary's order
A_FROM_COHERENCE = ('EIG-RAW', 'EIG-JOINT', 'RAW-HARM-SUM')   # card 9's levels, reused unchanged
A_FROM_CARD5 = ('CCA-RAW',)                                   # card 5's CCA, reused unchanged
# Where a reused level comes from: card, study, anchor (cards 5 and 7 from the released placement, card 9 from the
# plan's card table) and the code there.
REUSED_FROM = {'reused_cca_diagnostics': (5, 'cca_diagnostics'), 'reused_coherence_eigen': (9, 'coherence_eigen'),
               'reused_wearable_transfer': (7, 'wearable_transfer')}
CARD9_ANCHOR = 'eigenvalue-pooling'
LEARNED = ('RAW-LEAD3-RIDGE', 'EIG-RAW', 'EIG-JOINT')
DISPLAY_NAMES = {
    'harmonic_pooling': {
        'RAW-HARM-MAX': 'harmonic max (no training)',
        'RAW-HARM-ALLSUM': 'all-component sum (no training)',
        'JOINT-ALLSUM': 'joint all-component sum (no training)',
        'RAW-LEAD3-RIDGE': 'top-three ridge',
        'EIG-RAW': 'eigenvalue head',
        'EIG-JOINT': 'joint eigenvalue head',
        'RAW-HARM-SUM': 'harmonic sum (no training)',
        'CCA-RAW': 'CCA (no training)',               # card 5's name as released; the plan's 'joint CCA' row differs
    },
    'harmonic_pooling_wearable': {
        'EIG-RAW': 'eigenvalue head',
        'EIG-JOINT': 'joint eigenvalue head',
        'RAW-LEAD3-RIDGE': 'top-three ridge',
        'CCA-RAW': 'matched CCA',                     # card 7's name as released: the row is card 7's level
        'RAW-HARM-SUM': 'harmonic sum (no training)',
        'RAW-HARM-MAX': 'harmonic max (no training)',
        'RAW-HARM-ALLSUM': 'all-component sum (no training)',
        'JOINT-ALLSUM': 'joint all-component sum (no training)',
    },
}
# The plan's name key rows this package owns (site name first, export codes second).
NAME_KEY = (
    ('harmonic sum (no training)', 'RAW-HARM-SUM'),
    ('eigenvalue head', 'EIG-RAW'),
    ('joint eigenvalue head', 'EIG-JOINT'),
    ('top-three ridge', 'RAW-LEAD3-RIDGE'),
    ('harmonic max (no training)', 'RAW-HARM-MAX'),
    ('all-component sum (no training)', 'RAW-HARM-ALLSUM'),
    ('joint all-component sum (no training)', 'JOINT-ALLSUM'),
)
# What each arm pools, from the protocol's own definitions (checked in arms_of()).
POOLING = {
    'RAW-HARM-MAX': ('raw', 'leading component of each harmonic', 'max'),
    'RAW-HARM-ALLSUM': ('raw', 'all six components', 'sum'),
    'JOINT-ALLSUM': ('joint', 'all six components', 'sum'),
    'RAW-LEAD3-RIDGE': ('raw', 'leading component of each harmonic', 'ridge'),
    'EIG-RAW': ('raw', 'all six components', 'ridge'),
    'EIG-JOINT': ('joint', 'all six components', 'ridge'),
    'RAW-HARM-SUM': ('raw', 'leading component of each harmonic', 'sum'),
    'CCA-RAW': ('joint', 'top joint canonical correlation', 'none'),
}

# ---------------------------------------------------------------------------- limitations, not run, declared edits
# key -> (pinned input, JSON pointer, phrase the field must contain); pointer '' is a whole text record.
LIMITATION_SOURCES = {
    'harmonic_pooling': {
        'same_cohort_follow_up': ('ac_protocol', '/modules/A/exposure', 'notuntouchedconfirmation'),
        'unadjusted_intervals': ('ac_protocol', '/modules/A/statistics/multiplicity', 'no family-wisediscoveryclaim'),
        'no_equivalence_margin': ('ac_protocol', '/modules/A/statistics/equivalence', 'do notinfer fromcrossingzero'),
        'seen_descriptive': ('ac_protocol', '/modules/A/statistics/seen32', 'armCIs descriptive'),
        'eigenfeatures_carry_cca_statistics': ('ac_interpretation_review', '',
                                               'eigenfeatures already supply CCA-derived adaptive statistics'),
        'pooling_rules_only': ('ac_interpretation_review', '', 'not universal second-component irrelevance'),
        'no_learned_lead3_advantage': ('ac_release_review', '', 'A does not establish a learned LEAD3 advantage'),
    },
    'harmonic_pooling_wearable': {
        'stored_amplitude_units': ('ac_protocol', '/modules/C/limitations/0', 'Wearableunitsundocumented'),
        'window_onset_and_filter': ('ac_protocol', '/modules/C/limitations/1',
                                    'Wearable[0.14,2.14]sstimuluswindowversusBETA[0,2]s'),
        'candidates_supplied_off_grid': ('ac_protocol', '/modules/C/limitations/2', 'numericcandidatesprovided'),
        'prior_use_overlap': ('ac_protocol', '/modules/C/limitations/3', 'unknowncrossdatasetparticipantoverlap'),
        'no_single_factor': ('ac_protocol', '/modules/C/limitations/4', 'nofactorattribution'),
        'intervals_conditional_on_heads': ('ac_interpretation_review', '',
                                           'uncertainty is explicitly conditional on frozen source heads'),
        'average_not_compact_model': ('ac_interpretation_review', '', 'not as an independently trained compact model'),
        'not_comparable_with_beta_tasks': ('ac_interpretation_review', '', 'not ranked as matched absolute-accuracy tasks'),
        'not_unknown_frequency_discovery': ('ac_interpretation_review', '', 'this is not unknown-frequency discovery'),
        'not_pristine_external_validation': ('ac_interpretation_review', '',
                                             'preclude a pristine external-validation claim'),
        'unadjusted_intervals': ('ac_protocol', '/modules/C/contrasts', 'No multiplicity-adjusteddiscoveryclaim'),
        'no_equivalence_margin': ('ac_interpretation_review', '',
                                  'No A/C equivalence or noninferiority margin was registered'),
    },
}
CONTRAST_LIMITATIONS = {
    'harmonic_pooling': {'RAW-LEAD3-RIDGE minus RAW-HARM-SUM': 'no_learned_lead3_advantage',
                         'RAW-HARM-ALLSUM minus RAW-HARM-SUM': 'pooling_rules_only',
                         'RAW-HARM-MAX minus RAW-HARM-SUM': 'pooling_rules_only',
                         'EIG-JOINT minus JOINT-ALLSUM': 'eigenfeatures_carry_cca_statistics'},
    'harmonic_pooling_wearable': {'EIG-RAW minus RAW-HARM-SUM': 'no_equivalence_margin'},
}
NOT_RUN_SOURCES = {
    'harmonic_pooling': {
        'equivalence margin': ('ac_protocol', '/modules/A/statistics/equivalence', 'notdeclared'),
        'paired seen-32 contrasts': ('ac_protocol', '/modules/A/statistics/seen32', 'no additionalcontrastdecision'),
    },
    'harmonic_pooling_wearable': {
        'equivalence margin': ('ac_interpretation_review', '', 'No A/C equivalence or noninferiority margin was registered'),
        'target fitting, target scaling or head selection': (
            'ac_protocol', '/modules/C/limitations/5', 'No targetfitting/targetscaler/targetselection/refit'),
        'one-factor attribution of units, window, reference, hardware or cohort': (
            'ac_protocol', '/modules/C/limitations/4', 'nofactorattribution'),
    },
}
DECLARED_EDITS = {
    'harmonic_pooling': (
        'status, root_final_release_approval_pending and verified_A_aggregate.release_status not selected; '
        'state/AC-release-approval.json and the two reviews it binds supersede them',
        'private_root, timestamps, stage completion times, ledgers, budget accounting, verification records and '
        'elapsed seconds not selected',
        'payload byte counts, read caps, seal hashes and the permutation canary target count not selected; fit '
        'operation counts and reconstruction errors kept as checks',
        'held8 and seen32 named u8 and seen_ba in ids (route 3 spelling of the same tasks)',
        'above_zero and below_zero restated as interval_includes_zero and direction, both derived from the interval',
        'training-free arms carry "no training" and ridge heads "deterministic fit" in place of seeds',
        'the separate A aggregate file is not on this machine; its verified copy embedded in the summary is used and '
        'the approval must bind the hash the summary names',
    ),
    'harmonic_pooling_wearable': (
        'the CCA-RAW intervals (seed 20261020) not selected: the row is card 7 matched CCA, a level only',
        'claim_scope, model_collection and multiplicity free text not selected; the page writes its own copy from '
        'limitations_keys',
        'the twelve candidate frequencies not selected; their count, range and native order rule are kept',
        'prediction seal, reconstruction and freeze hashes not selected; the summary is pinned by its own hash',
        'per-arm score reconstruction errors kept as checks; payload byte counts not selected',
        'the separate C aggregate file is not on this machine; its verified copy embedded in the summary is used and '
        'the approval must bind the hash the summary names',
    ),
}

# ---------------------------------------------------------------------------- what no block may carry
REFUSED_KEYS = set(FORBIDDEN_KEYS) | {
    'pid', 'job', 'private_root', 'rows', 'privacy', 'status', 'release_status', 'release_eligibility',
    'root_final_release_approval_pending', 'at_utc', 'updated_at', 'path', 'handoff_path', 'ledgers_preserved',
    'budget_accounting', 'verification_records', 'claim_scope', 'model_collection', 'multiplicity', 'interpretation',
    'thread_bet', 'frequencies_hz'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_seed', 'prediction', 'probabilit', 'feature', 'private', 'path', 'host', 'elapsed',
                         'seconds', 'timing', 'checkpoint', 'device', 'subject', '_utc', 'canary', 'fifty', '055')
REFUSED_TEXT = re.compile(CCA_REFUSED_TEXT.pattern + r'|\bJev\b', re.IGNORECASE)   # blocks_cca's rule, plus the model
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
RANKING = re.compile(r'\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|state[- ]of[- ]the[- ]art|superior'
                     r'|significan|outperform', re.IGNORECASE)
CONFIDENCE_VALUE = 11 / 20          # the commenter's figure as a fraction, written as a ratio so it is never spelled
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])')   # R5 M7, any string


# ---------------------------------------------------------------------------- helpers
def load(pins=None):
    """Every pinned input, refused unless it is byte for byte the pinned file. Returns ({name: doc}, {name: sha})."""
    pins = pins or PINS
    require(set(pins) == set(PINS), f'pins: expected {sorted(PINS)}')
    docs, digests = {}, {}
    for name, ref in pins.items():
        raw = location(ref['path']).read_bytes()
        digest = sha(raw)
        require(digest == ref['sha256'], f'{name}: {Path(ref["path"]).name} is {digest[:12]}, pinned {ref["sha256"][:12]}')
        docs[name] = raw.decode('utf-8') if name in TEXT_PINS else json.loads(raw)
        digests[name] = digest
    for name, served in SERVED.items():
        require(sha(location(served).read_bytes()) == digests[name],
                f'{name}: the served copy differs from the copy the site builds from')
    return docs, digests


def inputs_available(pins=None):
    """Whether the pinned inputs are on this machine; the research folders are local, not in the repository."""
    return (all(location(r['path']).exists() for r in (pins or PINS).values())
            and all(location(p).exists() for p in SERVED.values()))


def stated(docs, name, ptr, phrase, label):
    text = resolve(docs[name], ptr) if ptr else docs[name]
    require(isinstance(text, str) and phrase in text, f'{label}: {name} {ptr or "text"} does not state {phrase!r}')


def f4(x):
    """A fraction at the four percentage decimals the reviews print."""
    return f'{x * 100:.4f}'


def direction(iv):
    return 'above zero' if iv[0] > 0 else 'below zero' if iv[1] < 0 else 'unresolved'


def metric_of(metric, label):
    require(isinstance(metric, dict) and number(metric.get('mean')) and isinstance(metric.get('ci95'), list)
            and len(metric['ci95']) == 2, f'{label}: no mean and interval')
    return metric['mean'], interval(*metric['ci95'], metric['mean'], label)


def level(metric, people, seeds, origin, label):
    est, iv = metric_of(metric, label)
    return {'estimate': est, 'interval': iv, 'unit': PROPORTION, 'people': people, 'seeds': seeds, 'origin': origin}


def contrast(metric, role, left, right, levels, people, seeds, label):
    """A paired contrast, refused unless it is the difference of its two levels; its flags derived from the interval."""
    require(isinstance(metric, dict) and number(metric.get('mean')) and isinstance(metric.get('ci95'), list)
            and len(metric['ci95']) == 2, f'{label}: no mean and interval')
    est = metric['mean']
    close(est, levels[left]['estimate'] - levels[right]['estimate'], f'{label} is not the difference of its levels')
    iv = interval(*metric['ci95'], est, label, lower=-1.0)
    flags = {'interval_includes_zero': iv[0] <= 0 <= iv[1], 'direction': direction(iv)}
    if levels[left]['estimate'] == levels[right]['estimate']:
        require(abs(est) <= NOISE, f'{label}: equal levels, yet the contrast is {est!r}')
        flags['levels_equal'] = True                    # prints as 0.00; the sign of the noise is not a direction
    return {'role': role, 'left': left, 'right': right, 'estimate': est, 'interval': iv, 'unit': DIFFERENCE,
            'people': people, 'seeds': seeds, 'flags': flags}


def input_hash(hashes, suffix, label):
    found = [v for k, v in hashes.items() if k.endswith(suffix)]
    require(len(found) == 1, f'{label}: the protocol pins no single {suffix}')
    return found[0]


def limitations(study, docs):
    keys = []
    for key, (name, ptr, phrase) in LIMITATION_SOURCES[study].items():
        stated(docs, name, ptr, phrase, f'{study} limitation {key}')
        keys.append(key)
    return keys


def not_run(study, docs):
    rows = []
    for item, (name, ptr, phrase) in NOT_RUN_SOURCES[study].items():
        stated(docs, name, ptr, phrase, f'{study} not run {item!r}')
        rows.append({'item': item, 'run_in': None})
    return rows


def contrast_limitations(study, contrasts):
    out = {}
    for cid in contrasts:
        key = CONTRAST_LIMITATIONS[study].get(cid.split('/')[0])
        if key:
            require(key in LIMITATION_SOURCES[study], f'{study} {cid}: limitation {key} is not sourced')
            out[cid] = [key]
    return out


def display_names(study, levels):
    codes = list(dict.fromkeys(lid.split('/')[0] for lid in levels))
    missing = set(codes) - set(DISPLAY_NAMES[study])
    require(not missing, f'{study}: no display name for {missing}')
    return {c: DISPLAY_NAMES[study][c] for c in codes}


def reused_of(levels, released):
    """{code: {card, study, anchor, code}} for every level a block reuses, as the card 8 and 9 blocks name them."""
    anchors = {c['card']: c['anchor'] for c in released['placement']['cards']} | {9: CARD9_ANCHOR}
    out = {}
    for lid, lv in levels.items():
        if lv['origin'] != 'new':
            card, study = REUSED_FROM[lv['origin']]
            code = lid.split('/')[0]
            require(out.get(code, {}).get('card', card) == card, f'{code}: reused from two cards')
            out[code] = {'card': card, 'study': study, 'anchor': anchors[card], 'code': code}
    return out


def seeds_of(code):
    return DETERMINISTIC if code in LEARNED else NO_TRAINING


def pair_seeds(a, b):
    return DETERMINISTIC if a in LEARNED or b in LEARNED else NO_TRAINING


# ---------------------------------------------------------------------------- the binding chain
def check_bindings(docs, digests):
    """The approval binds the summary, both reviews, the protocol and freeze, and the aggregates the summary names."""
    s, ap, fz, er = docs['ac_summary'], docs['ac_approval'], docs['ac_freeze'], docs['ac_execution_review']
    rr, ir = docs['ac_release_review'], docs['ac_interpretation_review']
    require(ap['status'] == APPROVED, f'A/C: the release approval is {ap["status"]!r}')
    bound(ap['summary_sha256'], digests['ac_summary'], 'A/C approval summary')
    bound(ap['numerical_review_sha256'], digests['ac_release_review'], 'A/C approval release review')
    bound(ap['interpretation_review_sha256'], digests['ac_interpretation_review'], 'A/C approval interpretation review')
    bound(ap['protocol_sha256'], digests['ac_protocol'], 'A/C approval protocol')
    bound(ap['freeze_sha256'], digests['ac_freeze'], 'A/C approval freeze')
    bound(ap['handoff_sha256'], digests['ac_handoff'], 'A/C approval handoff')
    for study, h in HANDOFF_CONTEXT.items():
        require(h['bound_by'] == 'ac_approval', f'{study}: the handoff is bound by another record')
        bound(ap['handoff_sha256'], h['bound_sha256'], f'{study} handoff')
    require(ap['B_D_results_included'] is False, 'A/C: the approval includes B/D results')
    require(ap['aggregate_sha256'] == s['aggregate_sha256'] and set(s['aggregate_sha256']) == {'A', 'C'},
            'A/C: the approval binds other aggregates than the summary names')
    require(ap['global_seal_sha256'] == s['global_seal_sha256'] == s['verified_A_aggregate']['global_seal_sha256'],
            'A/C: the global seal differs between approval and summary')
    bound(s['freeze_sha256'], digests['ac_freeze'], 'A/C summary freeze')
    bound(s['protocol_sha256'], digests['ac_protocol'], 'A/C summary protocol')
    bound(s['verified_C_aggregate']['freeze_sha256'], digests['ac_freeze'], 'C aggregate freeze')
    require(s['verified_C_aggregate']['prediction_seal_sha256'] == s['module_seal_sha256']['transfer'],
            'C aggregate: another prediction seal')
    require(s['all_new_A_C_payload_SHA256_verified'] is True and s['technical_holds'] == [], 'A/C: a technical hold')
    bound(fz['protocol_sha256'], digests['ac_protocol'], 'A/C freeze protocol')
    require(set(fz['module_scopes']) == {'A', 'C'} and set(fz['held_modules']) == {'B', 'D'}, 'A/C: freeze scope')
    bound(fz['code_sha256']['run_pooling.py'], digests['pooling_runner'], 'A/C freeze pooling runner')
    bound(fz['code_sha256']['run_transfer.py'], digests['transfer_runner'], 'A/C freeze transfer runner')
    require(er['status'] == 'PASS', 'A/C: the execution review did not pass')
    bound(er['freeze_sha256'], digests['ac_freeze'], 'A/C execution review freeze')
    bound(er['protocol_sha256'], digests['ac_protocol'], 'A/C execution review protocol')
    # The two reviews the approval binds: their verdicts, and the hashes they reviewed.
    require('Technical PASS for the completed A/C chain; no technical holds.' in rr, 'A/C: the release review verdict')
    require('PASS for the bounded aggregate interpretation' in ir, 'A/C: the interpretation review verdict')
    for h in (*s['aggregate_sha256'].values(), digests['ac_freeze'], digests['ac_protocol'], s['global_seal_sha256']):
        require(h in rr, f'A/C: the release review does not name {h[:12]}')
    # Card 9's study: approved, and the one module A's protocol pins (freeze and prediction seal).
    ca, pa = docs['coherence_approval'], docs['ac_protocol']['modules']['A']
    require(ca['status'] == 'APPROVED_AGGREGATE_HANDOFF', 'coherence: the release approval')
    bound(ca['aggregate_sha256'], digests['coherence_aggregate'], 'coherence approval aggregate')
    bound(pa['prior_freeze_sha256'], ca['freeze_sha256'], 'module A prior freeze')
    bound(input_hash(pa['input_hashes'], '_20261020/prediction-seal.json', 'module A'), ca['prediction_seal_sha256'],
          'module A prior prediction seal')
    pc = docs['ac_protocol']['modules']['C']
    for arm in ('EIG-RAW', 'EIG-JOINT'):
        bound(pc['head_freeze_sha256'][arm], ca['freeze_sha256'], f'module C {arm} source heads')
    require(docs['released']['release_id'] == RELEASED_ID, 'the released file is another release')


def review_tables(docs, block_contrasts):
    """Every contrast at the four decimals the release review prints, row by row."""
    rr = docs['ac_release_review']
    for cid, c in block_contrasts.items():
        key, stratum = cid.rsplit('/', 1)
        a, b = key.split(' minus ')
        cell = f'{f4(c["estimate"])} [{f4(c["interval"][0])}, {f4(c["interval"][1])}]'
        role = c['role'].capitalize()
        row = (f'| {role} | {a} − {b} | {cell} |' if stratum == 'u8'
               else f'| {stratum} | {role} | {key} | {cell} |')
        require(row in rr, f'{cid}: the release review does not print {row!r}')


def handoff_levels(docs, levels, codes, columns, label):
    """Every level at the four decimals the approved handoff prints: one row per arm, one column per endpoint."""
    text = docs['ac_handoff']
    for code in codes:
        cells = []
        for col in columns:
            lv = levels[f'{code}/{col}']
            m, iv = lv.get('_metric', (lv['estimate'], lv['interval']))
            cells.append(f'{f4(m)} [{f4(iv[0])}, {f4(iv[1])}]')
        row = f'| {code} | ' + ' | '.join(cells) + ' |'
        require(row in text, f'{label} {code}: the approved handoff does not print {row!r}')


# ---------------------------------------------------------------------------- module A, BETA (card 10, first block)
def arms_of(protocol_a):
    """The arm list with what each pools; refused unless the protocol defines the analytic arms and columns so."""
    analytic = protocol_a['analytic_arms']
    require(analytic == {'RAW-HARM-MAX': 'max(raw[...,0::2])', 'RAW-HARM-ALLSUM': 'sum(raw[...,0:6])',
                         'JOINT-ALLSUM': 'sum(joint[...,0:6])'}, 'module A: the analytic arms changed')
    require(protocol_a['fitted_arm'] == 'RAW-LEAD3-RIDGE' and protocol_a['columns'] == [0, 2, 4],
            'module A: the fitted arm or its columns changed')
    rows = []
    for code in A_ARMS:
        statistics, components, rule = POOLING[code]
        row = {'code': code, 'statistics': statistics, 'components': components, 'rule': rule,
               'training': ('ridge fitted on source people' if code in LEARNED else NO_TRAINING)}
        if code == 'RAW-LEAD3-RIDGE':
            row.update(fits=protocol_a['main_fits'], independent_refits=protocol_a['independent_refits'])
        if code in A_FROM_COHERENCE + A_FROM_CARD5:
            row['reused_from_card'] = 9 if code in A_FROM_COHERENCE else 5
        rows.append(row)
    return rows


def pooling_block(docs, digests):
    s, released = docs['ac_summary'], docs['released']
    A, pa = s['verified_A_aggregate'], docs['ac_protocol']['modules']['A']
    st, counts = pa['statistics'], s['A_counts']
    require(A['aggregate_only'] is True, 'module A: the aggregate is not aggregate-only')
    require(st['people'] == A['person_count'] == 70 and st['rotations'] == A['rotations'] == 5, 'module A: people')
    require(st['bootstrap_draws'] == DRAWS and st['bootstrap_seed'] == A_SEED, 'module A: bootstrap')
    stated(docs, 'pooling_runner', '', f'default_rng({A_SEED}).integers(0,70,size=({DRAWS},70))', 'module A draws')
    stated(docs, 'ac_release_review', '', f"regenerated A's 2,000 paired 70-person bootstrap draws (seed {A_SEED})",
           'module A draws reviewed')
    require(st['formal_contrast_count'] == 6 and st['candidate_set'] == 'held8', 'module A: contrast family')
    require(pa['main_fits'] == A['main_fits'] == counts['main'] == 35
            and pa['independent_refits'] == counts['independent_refits'] == 35
            and pa['bridge_fits'] == counts['bridges'] == 3 and pa['canary_fits'] == counts['canaries'] == 1
            and pa['total_fit_operations'] == A['total_fit_operations'] == counts['total_fits'] == 74,
            'module A: the fit counts differ')
    require('70people7folds' in pa['split'] and '7680trainrows60people32freq' in pa['split'], 'module A: the split')
    cohort = released['cohort']
    require((cohort['people'], cohort['person_folds'], cohort['frequency_rotations']) == (70, 7, 5),
            'module A: not the cohort of cards 1 to 6')
    require(tuple(A['arms']) == A_ARMS, 'module A: the arm set changed')
    people = A['person_count']

    levels, codes = {}, {}
    coherence = docs['coherence_aggregate']['arms']
    card5 = released['studies']['cca_diagnostics']['levels']
    for code in A_ARMS:
        origin = ('reused_coherence_eigen' if code in A_FROM_COHERENCE
                  else 'reused_cca_diagnostics' if code in A_FROM_CARD5 else 'new')
        for e, src in ENDPOINTS.items():
            lid = f'{code}/{e}'
            levels[lid] = level(A['arms'][code][src], people, seeds_of(code), origin, f'module A {lid}')
            codes[lid] = ['#' + pointer('verified_A_aggregate', 'arms', code, src)]
            if code in A_FROM_COHERENCE + A_FROM_CARD5:     # every reused comparator: the same doubles, bit for bit
                require(A['arms'][code][src] == coherence[code][src], f'module A {lid} is not card 9’s level')
                codes[lid].append('coherence_aggregate#' + pointer('arms', code, src))
            if code in A_FROM_CARD5:
                rel = card5[lid]
                require(rel['estimate'] == levels[lid]['estimate'] and rel['interval'] == levels[lid]['interval'],
                        f'module A {lid} is not card 5’s released level')
                codes[lid].append(f'{RELEASED_FILE}#' + pointer('studies', 'cca_diagnostics', 'levels', lid))

    planned = ([(a, b, 'primary') for a, b in pa['primary_contrasts']]
               + [(a, b, 'secondary') for a, b in pa['secondary_contrasts']])
    require([(c['a'], c['b']) for c in A['contrasts']] == [(a, b) for a, b, _ in planned],
            'module A: the summary contrasts differ from the protocol')
    contrasts = {}
    for i, ((a, b, role), c) in enumerate(zip(planned, A['contrasts'])):
        require(c['metric'] == 'held8', f'module A {a} minus {b}: not a held-out contrast')
        cid = f'{a} minus {b}/u8'
        con = contrast(c, role, f'{a}/u8', f'{b}/u8', levels, people, pair_seeds(a, b), f'module A {cid}')
        iv = con['interval']
        require(c['above_zero'] == (iv[0] > 0) and c['below_zero'] == (iv[1] < 0), f'module A {cid}: sign flags')
        contrasts[cid], codes[cid] = con, ['#' + pointer('verified_A_aggregate', 'contrasts', i)]
    require([c['role'] for c in contrasts.values()] == ['primary'] * 3 + ['secondary'] * 3, 'module A: roles')
    review_tables(docs, contrasts)
    handoff_levels(docs, levels, A_ARMS, ENDPOINTS, 'module A')
    stated(docs, 'ac_interpretation_review', '',
           f'LEAD3 is {f4(levels["RAW-LEAD3-RIDGE/u8"]["estimate"])}% on BETA held-eight versus '
           f'{f4(levels["RAW-HARM-SUM/u8"]["estimate"])}% for RAW-HARM-SUM', 'module A headline levels')

    chance = {e['id']: e for e in released['endpoints']}
    design = {
        'dataset': {'name': 'BETA', 'people': people, 'targets': cohort['targets'], 'windows': cohort['windows'],
                    'person_folds': cohort['person_folds'], 'frequency_rotations': A['rotations'],
                    'candidate_order': 'ascending', 'tie_rule': 'first ascending candidate index',
                    'same_cohort_as': 'cards 1 to 6, 8 and 9'},
        'endpoints': {'u8': {'candidate_count': chance['u8']['candidates'], 'chance': chance['u8']['chance'],
                             'role': 'contrasts'},
                      'seen_ba': {'candidate_count': chance['seen_ba']['candidates'],
                                  'chance': chance['seen_ba']['chance'], 'role': 'descriptive'}},
        'source_per_fit': {'people': 60, 'frequencies': 32, 'windows': 7680},
        'fit_operations': {'main': counts['main'], 'independent_refits': counts['independent_refits'],
                           'bridges': counts['bridges'], 'label_permutation_check': counts['canaries'],
                           'total': counts['total_fits']},
        'arms': arms_of(pa),
        'contrast_family': {'primary': 3, 'secondary': 3, 'endpoint': 'u8', 'multiplicity_adjusted': False,
                            'equivalence_margin': None},
    }
    errs = s['A_score_max_errors']
    checks = {
        'release_review': {'passed': True, 'technical_holds': len(s['technical_holds'])},
        'interpretation_review': {'passed': True},
        'release_approval': {'approved': True},
        'source_admission_sets': s['A_counts']['source_admission_sets'],
        'score_max_errors': {'forward_from_saved_cache': errs['forward_from_saved_cache'],
                             'independent_refit': errs['independent_refit'], 'bridge': errs['bridge']},
        'metric_and_contrast_max_error': s['A_metric_and_6_contrast_max_error'],
        'metric_values_rebuilt': s['A_person_rotation_metric_entries'],
        'reused_levels_bit_identical': {'card 9': list(A_FROM_COHERENCE), 'card 5': list(A_FROM_CARD5)},
    }
    return {
        'card': CARD,
        'anchor': ANCHOR,
        'source_sha256': digests['ac_summary'],
        'review_sha256': digests['ac_release_review'],
        'interpretation_review_sha256': digests['ac_interpretation_review'],
        'release_approval_sha256': digests['ac_approval'],
        'protocol_sha256': digests['ac_protocol'],
        'freeze_sha256': digests['ac_freeze'],
        'embedded_aggregate_sha256': s['aggregate_sha256']['A'],
        'reused_source_sha256': {'coherence_aggregate': digests['coherence_aggregate'], 'released': digests['released']},
        'interval_method': {'method': METHOD, 'draws': DRAWS, 'seed': A_SEED, 'level': LEVEL,
                            'paired_across': 'arms, with each person’s five rotations kept together'},
        'design': design,
        'levels': levels,
        'level_only': {},
        'reused': reused_of(levels, docs['released']),
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('harmonic_pooling', contrasts),
        'undefined': [],
        'not_run': not_run('harmonic_pooling', docs),
        'checks': checks,
        'limitations_keys': limitations('harmonic_pooling', docs),
        'display_names': display_names('harmonic_pooling', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- module C, Wearable-102 (second block)
def same_windows_as_card7(docs):
    """Module C runs on card 7's windows, channel order, candidate order, CCA and tie rule: refused otherwise."""
    pc, wp, wf = docs['ac_protocol']['modules']['C'], docs['wear_protocol'], docs['wear_freeze']
    target = {k.rsplit('/', 1)[1]: v for k, v in pc['expected_input_hashes'].items()
              if k.startswith(pc['target_root'] + '/')}           # the target cache, matched by its root, never copied
    for name in ('epochs250.npy', 'labels.npy', 'subjects.npy', 'sensors.npy', 'trials.json'):
        require(target.get(name) == wf['input_sha256'][name], f'module C: {name} is not card 7’s')
    require(pc['channel_order'] == wp['input']['channel_order'], 'module C: another channel order')
    require(pc['frequencies_hz'] == wp['input']['frequencies'], 'module C: another candidate order')
    require('threecenteredsin/cos harmonics' in pc['geometry_domain']
            and 'three sine/cosine harmonics' in wp['methods']['comparator'], 'module C: another CCA reference')
    require(pc['controls']['CCA-RAW'].startswith('sqrt(jointtop)'), 'module C: CCA is not the joint top correlation')
    require('first index in the frozen native Wearable target-axis frequency order' in pc['tie_rule']
            and 'first index in the documented target-axis frequency order' in wp['methods']['ties'],
            'module C: another tie rule')
    rw = docs['released']['studies']['wearable_transfer']
    m3 = rw['cca_definition']['matched_cca']
    require(m3['code'] == 'CCA-RAW' and m3['harmonics'] == 3 and rw['cca_definition']['same_windows'] is True,
            'module C: card 7’s matched CCA is not the three-harmonic CCA-RAW')
    return rw


def wearable_block(docs, digests):
    s = docs['ac_summary']
    C, pc, counts = s['verified_C_aggregate'], docs['ac_protocol']['modules']['C'], s['C_counts']
    rw = same_windows_as_card7(docs)
    require(C['aggregate_only'] is True, 'module C: the aggregate is not aggregate-only')
    require(C['people'] == pc['statistics']['people'] == counts['people'] == rw['design']['dataset']['people'] == 102,
            'module C: people')
    require(C['bootstrap_draws'] == pc['statistics']['bootstrap_draws'] == DRAWS
            and C['bootstrap_seed'] == pc['statistics']['bootstrap_seed'] == C_SEED, 'module C: bootstrap')
    stated(docs, 'transfer_runner', '', f'default_rng({C_SEED}).integers(0,102,size=({DRAWS},102))', 'module C draws')
    stated(docs, 'transfer_runner', '', 'np.percentile(v[draws].mean(axis=1),[2.5,97.5])', 'module C percentile rule')
    stated(docs, 'ac_release_review', '', f"C's 2,000 paired 102-person draws (seed {C_SEED})", 'module C draws reviewed')
    stated(docs, 'ac_release_review', '', 'C uses the same draws for dry and wet', 'module C shared draws')
    require(C['conditions'] == list(CONDITIONS) == pc['statistics']['conditions'], 'module C: conditions')
    close(C['chance'], 1 / 12, 'module C chance')
    close(C['chance'], rw['design']['dataset']['targets'] ** -1, 'module C chance against card 7')
    require(pc['fit_count'] == 0 == counts['target_fits'] and pc['target_fitting'] is False
            and pc['target_selection'] is False, 'module C: target fitting')
    require(pc['ensemble_heads'] == counts['heads_per_arm'] == 35 and counts['source_heads'] == 105
            and counts['learned_arms'] == 3 and counts['analytic_arms'] == 5, 'module C: the source heads')
    require(pc['head_widths'] == {'EIG-RAW': 6, 'EIG-JOINT': 6, 'RAW-LEAD3-RIDGE': 3}, 'module C: head widths')
    stated(docs, 'ac_interpretation_review', '', 'EIG-RAW and EIG-JOINT collapse to six coefficients plus a bias, '
           'while LEAD3 collapses to three coefficients plus a bias', 'module C collapsed functions')
    windows = counts['target_rows']
    require(windows == rw['design']['dataset']['windows'] == 24480
            and counts['trials_per_person_condition'] * counts['people'] * len(CONDITIONS) == windows,
            'module C: windows')
    methods = tuple(pc['methods'])
    require(all(tuple(C['levels'][k]) == methods for k in CONDITIONS), 'module C: the method set changed')
    people = C['people']

    card7 = rw['levels']
    levels, codes, level_only = {}, {}, {}
    for code in methods:
        for k in CONDITIONS:
            lid = f'{code}/{k}'
            m = C['levels'][k][code]
            if code == 'CCA-RAW':
                est, iv = metric_of(m, f'module C {lid}')
                require(est == card7[lid]['estimate'], f'module C {lid} is not card 7’s released matched CCA')
                levels[lid] = {'estimate': est, 'interval': None, 'unit': PROPORTION, 'people': people,
                               'seeds': NO_TRAINING, 'origin': 'reused_wearable_transfer', '_metric': (est, iv)}
                level_only[lid] = f'wearable_transfer {lid}'
                codes[lid] = ['#' + pointer('verified_C_aggregate', 'levels', k, code),
                              f'{RELEASED_FILE}#' + pointer('studies', 'wearable_transfer', 'levels', lid)]
            else:
                levels[lid] = level(m, people, seeds_of(code), 'new', f'module C {lid}')
                codes[lid] = ['#' + pointer('verified_C_aggregate', 'levels', k, code)]
    handoff_levels(docs, levels, methods, CONDITIONS, 'module C')
    for lv in levels.values():
        lv.pop('_metric', None)

    planned = ([(a, b, 'primary') for a, b in pc['primary_pairs']]
               + [(a, b, 'secondary') for a, b in pc['secondary_pairs']])
    require(len(planned) == 5 and '2primary8secondary' in pc['contrasts'], 'module C: the contrast family')
    contrasts = {}
    for k in CONDITIONS:
        require(list(C['contrasts'][k]) == [f'{a} minus {b}' for a, b, _ in planned],
                f'module C {k}: the summary contrasts differ from the protocol')
        for a, b, role in planned:
            key = f'{a} minus {b}'
            c = C['contrasts'][k][key]
            require(c['primary'] is (role == 'primary'), f'module C {key}/{k}: role')
            cid = f'{key}/{k}'
            contrasts[cid] = contrast(c, role, f'{a}/{k}', f'{b}/{k}', levels, people, pair_seeds(a, b),
                                      f'module C {cid}')
            codes[cid] = ['#' + pointer('verified_C_aggregate', 'contrasts', k, key)]
    require(sum(c['role'] == 'primary' for c in contrasts.values()) == 2 and len(contrasts) == 10, 'module C: roles')
    review_tables(docs, contrasts)

    design = {
        'dataset': {'name': 'Wearable-102', 'people': people, 'targets': rw['design']['dataset']['targets'],
                    'frequency_range_hz': rw['design']['dataset']['frequency_range_hz'], 'windows': windows,
                    'windows_per_sensor': windows // len(CONDITIONS), 'sensors': list(CONDITIONS),
                    'window_s': rw['design']['dataset']['window_s'], 'amplitude': 'as stored',
                    'candidate_order': 'native order, unsorted', 'tie_rule': 'first native candidate index',
                    'same_windows_as': 'wearable_transfer'},
        'endpoints': {k: {'candidate_count': rw['design']['dataset']['targets'], 'chance': C['chance'],
                          'windows': windows // len(CONDITIONS), 'role': 'primary and secondary contrasts'}
                      for k in CONDITIONS},
        'source_heads': {'dataset': 'BETA', 'learned_arms': counts['learned_arms'],
                         'heads_per_learned_arm': counts['heads_per_arm'], 'source_heads': counts['source_heads'],
                         'collapsed_to_one_affine_function': True,
                         'coefficients': {arm: {'weights': w, 'bias': 1} for arm, w in pc['head_widths'].items()},
                         'average_of': 'the scores of all 35 heads, equal weights',
                         'target_fits': counts['target_fits'], 'target_selection': False, 'retraining': False},
        'methods': [{'code': code, 'training': ('BETA heads, run unchanged' if code in LEARNED else NO_TRAINING)}
                    | ({'level_only': True, 'card': 7} if code == 'CCA-RAW' else {}) for code in methods],
        'contrast_family': {'primary': 1, 'secondary': 4, 'per_sensor': True, 'multiplicity_adjusted': False,
                            'equivalence_margin': None},
    }
    checks = {
        'release_review': {'passed': True, 'technical_holds': len(s['technical_holds'])},
        'interpretation_review': {'passed': True},
        'release_approval': {'approved': True},
        'explicit_35_head_average_max_errors': dict(s['C_explicit_35head_score_max_errors']),
        'collapsed_function_max_errors': dict(s['C_collapsed_affine_max_errors']),
        'metric_and_contrast_max_error': s['C_metric_and_10_contrast_max_error'],
        'metric_values_rebuilt': s['C_person_condition_metric_entries'],
        'source_head_bindings': s['source_head_binding_entries'],
        'matched_cca_equals_card7': {k: True for k in CONDITIONS},
    }
    return {
        'card': CARD,
        'anchor': ANCHOR,
        'source_sha256': digests['ac_summary'],
        'review_sha256': digests['ac_release_review'],
        'interpretation_review_sha256': digests['ac_interpretation_review'],
        'release_approval_sha256': digests['ac_approval'],
        'protocol_sha256': digests['ac_protocol'],
        'freeze_sha256': digests['ac_freeze'],
        'embedded_aggregate_sha256': s['aggregate_sha256']['C'],
        'reused_source_sha256': {'released': digests['released'], 'wear_protocol': digests['wear_protocol'],
                                 'wear_freeze': digests['wear_freeze']},
        'interval_method': {'method': METHOD, 'draws': DRAWS, 'seed': C_SEED, 'level': LEVEL,
                            'conditional_on': 'the fixed 35 source heads of each learned arm',
                            'paired_across': 'methods and both sensors (one set of draws)'},
        'design': design,
        'levels': levels,
        'level_only': level_only,
        'reused': reused_of(levels, docs['released']),
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('harmonic_pooling_wearable', contrasts),
        'undefined': [],
        'not_run': not_run('harmonic_pooling_wearable', docs),
        'checks': checks,
        'limitations_keys': limitations('harmonic_pooling_wearable', docs),
        'display_names': display_names('harmonic_pooling_wearable', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- boundary
def scrub_check(value, trail='$'):
    """Refuse a key, string or value this release must not carry, anywhere in the blocks."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS, f'{trail}.{k}: refused key')
            require(not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS), f'{trail}.{k}: refused key fragment')
            scrub_check(k, f'{trail}.<key>')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        require(not (len(value) > 3 and all(count(v) for v in value)), f'{trail}: an integer list (row indices?)')
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(re.fullmatch(r'[0-9a-f]{64}', value) or not REFUSED_TEXT.search(value), f'{trail}: refused text {value!r}')
        require(re.fullmatch(r'[0-9a-f]{64}', value) or not CONFIDENCE_TOKEN.search(value), f'{trail}: the token {value!r}')
        require(not VERSION_LABEL.search(value), f'{trail}: a version label {value!r}')
        require(not RANKING.search(value), f'{trail}: a ranking word {value!r}')
    elif isinstance(value, float):
        require(math.isfinite(value), f'{trail}: not finite')
        require(abs(value - CONFIDENCE_VALUE) > 1e-12 and abs(value - 100 * CONFIDENCE_VALUE) > 1e-9,
                f'{trail}: refused value {value!r}')


def build_blocks(pins=None) -> dict:
    """The two pooling study blocks, keyed harmonic_pooling and harmonic_pooling_wearable."""
    docs, digests = load(pins)
    check_bindings(docs, digests)
    blocks = {'harmonic_pooling': pooling_block(docs, digests), 'harmonic_pooling_wearable': wearable_block(docs, digests)}
    for name, block in blocks.items():
        require(all(f in block for f in BLOCK_FIELDS), f'{name}: a block field is missing')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
                f'{name}: export codes do not cover the levels and contrasts')
        for c in block['contrasts'].values():
            require(c['left'] in block['levels'] and c['right'] in block['levels'], f'{name}: a contrast side is no level')
        for lid, lv in block['levels'].items():
            require((lv['interval'] is None) == (lid in block['level_only']), f'{name} {lid}: an interval rule')
    validate_public(blocks)
    scrub_check(blocks)
    return blocks


if __name__ == '__main__':
    built = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'limitations': len(b['limitations_keys'])} for s, b in built.items()}, indent=2))
