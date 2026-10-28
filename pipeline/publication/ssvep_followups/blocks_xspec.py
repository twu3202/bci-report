"""The cross-spectral block of the SSVEP follow-ups release: card 8 (queue row 21), a shared scorer on the
cross-spectral matrix.

One audited route 3 follow-up on the BETA cohort, read from its own aggregate and turned into the study block `xspec`
for `ssvep-followups-update.json`, which the assembler of that file puts under `studies`. Four new learned readouts of
the channel-by-channel matrices at the fundamental and two harmonics (XS-RIDGE, XS-RIDGE-W, XS-MLP, XS-RIDGE-Q) beside
four comparators the run reused from card 5's sealed scores (CCA, the cropped-spectrum match, the channel-energy
average, the shared ridge scorer); ten prespecified paired contrasts, two of them primary, on two endpoints.

The aggregate was copied read-only from the run host (gate A1 of the plan) into
`research/publication_review_20261028/inputs/xspec-aggregate.json`; it is refused unless it is byte for byte the
aggregate the study's release approval and release audit bind. Release status is read from
`state/release-approval.json`, never from the aggregate's own frozen `release_status` field. Every input is pinned by
SHA-256 (PINS). Every number is the source's own double: nothing is rounded or rescaled, units stay fractions. A
contrast must equal the difference of its two levels and an interval must hold its point; the source's own flags must
follow the protocol's stated rules; contrast roles are the protocol's and must equal the handoff's table. The four
reused comparators must equal card 5's released levels in `site/src/data/new-ssvep-frequencies-update.json` (to 1e-12;
they are bit-identical) and carry card 5's site names, and the run's pinned comparators must be card 5's protocol and
freeze. The pinned protocol, review, handoff and runner carry private storage paths, so they are read and checked here,
never copied; only named fields are selected.

The declared edits (DECLARED_EDITS lists them for the manifest): the frozen release status, the run seal hash, the
per-seed MLP means, the random-pairing and canary accuracies, the free-text aggregation and multiplicity strings are
not selected; `held8` and `seen32` are named `u8` and `seen_ba` in ids, card 5's spelling of the same two tasks,
checked through CCA's own value; ridge arms carry "deterministic fit" and training-free comparators "no training"
where the MLP carries its seed count. The handoff's historical-point and band lines (thread predictions, D23) and its
CCA identity approximation table are not selected.

A block has the fields of the released blocks (blocks_cca.py):
- `source_sha256`, `review_sha256` (the independent release review), and the other pinned records by name;
- `interval_method`: `{method, draws, seed, level}`, read from the aggregate and the protocol, the percentile rule from
  the pinned runner;
- `design`: the cohort (card 5's, checked), the endpoints, the arms with their fit and input counts;
- `levels`: `{id: {estimate, interval, unit, people, seeds, origin}}`; an id is `<export code>/<endpoint>`; `origin` is
  `new` or `reused_cca_diagnostics`, and `reused` says which card each reused code comes from;
- `contrasts`: `{id: {role, left, right, estimate, interval, unit, people, seeds, flags}}`; `role` is `primary` or
  `secondary`; `flags` hold the source's own flags (checked against the protocol's rules) plus
  `interval_includes_zero`, derived here, and `bound_below_two_decimals` where a nonzero bound prints as 0.00 in pp;
- `contrast_limitations`: `{contrast id: [limitation key]}`, the caveat that sits next to that evidence;
- `descriptive_gaps`: the whitened readout against CCA, a difference of two levels with no planned interval (the
  handoff's descriptive table states it); `undefined`: that pair, as not a planned contrast;
- `not_run`: `[{item, run_in}]`; `checks`: reviews, approval and audit, pass or fail and counts only;
- `limitations_keys`, `display_names`, `export_codes` (`#<JSON pointer>` into the aggregate, plus
  `cca_diagnostics#<pointer>` and `new-ssvep-frequencies-update.json#<pointer>` for a reused level).

    python3 pipeline/publication/ssvep_followups/blocks_xspec.py      # builds and prints the counts; writes nothing
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

from export_snapshot import validate_public               # noqa: E402
from ssvep_followups import blocks_cca as cca              # noqa: E402  the shared helpers and refusal vocabulary

require, sha, number, count, close = cca.require, cca.sha, cca.number, cca.count, cca.close
location, pointer, resolve, interval = cca.location, cca.pointer, cca.resolve, cca.interval
stated, bound, numeric_leaves = cca.stated, cca.bound, cca.numeric_leaves

# ---------------------------------------------------------------------------- pinned inputs
# Paths are relative to the project; `research/...` resolves under `researchRoot` when local_paths.json sets one.
_X = 'research/decision_route3_xspec_20261019'
_R = 'research/publication_review_20261028'
RELEASED_PATH = 'site/src/data/new-ssvep-frequencies-update.json'
PINS = {
    # Gate A1: the run's metrics/aggregate.json, copied read-only and hash-checked.
    'xspec_export': {'path': f'{_R}/inputs/xspec-aggregate.json',
                     'sha256': '272bac552fdf509b4cc9bae930782de6a5673194a4989bcbdcbef3b4f1214a0c'},
    'xspec_protocol': {'path': f'{_X}/protocol.json',
                       'sha256': 'c54fcef3bb1d281e4e210a665f9b880caf45523f7f8df45adac188f403a13fed'},
    'xspec_freeze': {'path': f'{_X}/execution-freeze.json',
                     'sha256': '0f670e30dfa837cb319be0b714e31176953ebc5e49bf97b80ac702fc7c812682'},
    'xspec_execution_review': {'path': f'{_X}/execution-review.json',
                               'sha256': 'c8d5d41a23d3376bb8549e866da894feb91dcc30f6d57ecba4f77a6a7fde253e'},
    'xspec_review': {'path': f'{_X}/review/Independent Results Release Review.md',
                     'sha256': '1e2231f6dd551fc5105ead5bd48f656e9d26b491d52b441d071ad61c0270763e'},
    'xspec_audit': {'path': f'{_X}/evidence/Release Audit Summary.json',
                    'sha256': 'c9af237dee103388f1313f5ed57b3516c26cd17668ab10198838dccdd3c859d7'},
    'xspec_approval': {'path': f'{_X}/state/release-approval.json',
                       'sha256': '46de8d019dfa6bc0d66dc2b6d94d126585bcea21641abbc8acdd93b0228c3e26'},
    'xspec_caveats': {'path': f'{_X}/state/pre-score-interpretation-caveats.json',
                      'sha256': 'c77f984cb667112cf2bbea4f2a685d6884c8bd1566779c0c2735226c0fd5e5b4'},
    'xspec_handoff': {'path': f'{_X}/Cross-Spectral Shared-Weight Scorer Results Handoff.md',
                      'sha256': '884565105c98c0a9bee005f6d6857838b42c19eb8a5e88d96055bec347306cb4'},
    'xspec_runner': {'path': f'{_X}/scripts/run_xspec.py',
                     'sha256': '624388668471e8d20f60772556fcef0d4f362685655e0ac531363f93dff7aef5'},
    # The released 2026-10-20 payload (D28: it keeps its bytes): card 5's levels, names, cohort and card anchors.
    'released': {'path': RELEASED_PATH,
                 'sha256': '197028bdc4dadd9713f6d408bb64204147fdfe39a686e7e119e4988aaf863ee0'},
}
TEXT_PINS = {'xspec_review', 'xspec_handoff', 'xspec_runner'}
SERVED = {'released': 'site/public/data/new-ssvep-frequencies-update.json'}   # must be the same bytes as the src copy
RELEASED_FILE = 'new-ssvep-frequencies-update.json'                          # its served name, as export_codes cite it
RELEASED_ID = 'new-ssvep-frequencies-update-20261020'
# For the release manifest: the handoff is pinned for its contrast table and stated phrases, never a copy source.
HANDOFF_CONTEXT = {'xspec': {'bound_sha256': '884565105c98c0a9bee005f6d6857838b42c19eb8a5e88d96055bec347306cb4',
                             'bound_by': 'xspec_approval'}}

STUDY, CARD, ANCHOR = 'xspec', 8, 'cross-spectral'
STUDIES = (STUDY,)
BLOCK_FIELDS = cca.BLOCK_FIELDS
ENDPOINTS = {'u8': 'held8', 'seen_ba': 'seen32'}          # site id -> aggregate spelling
PROPORTION, DIFFERENCE = cca.PROPORTION, cca.DIFFERENCE
NO_TRAINING, DETERMINISTIC = cca.NO_TRAINING, cca.DETERMINISTIC
SEED, DRAWS, LEVEL = 20261015, 2000, 0.95
METHOD = cca.METHOD                                       # 'paired person bootstrap, percentile interval'
TOL = 1e-12

NEW_ARMS = ('XS-RIDGE', 'XS-RIDGE-W', 'XS-MLP', 'XS-RIDGE-Q')
RIDGE_ARMS = ('XS-RIDGE', 'XS-RIDGE-W', 'XS-RIDGE-Q', 'SHARED-RIDGE')
# The comparators the run reused from card 5's sealed scores: code here -> code in card 5's block.
REUSED = {'CCA-RAW': 'CCA-RAW', 'SUBSPACE-CROP': 'SUBSPACE-CROP', 'CHANNEL-HARMONIC': 'CHANNEL-HARMONIC',
          'SHARED-RIDGE': 'SHARED-RIDGE'}
REUSED_FROM = {'card': 5, 'study': 'cca_diagnostics', 'origin': 'reused_cca_diagnostics'}

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
DISPLAY_NAMES = {
    'XS-RIDGE': 'cross-spectral ridge',
    'XS-RIDGE-W': 'whitened cross-spectral ridge',
    'XS-MLP': 'cross-spectral MLP',
    'XS-RIDGE-Q': 'cross-spectral ridge with quadrature',
    # Card 5's names, one name for one set of scores (checked against the released block).
    'CCA-RAW': 'CCA (no training)',
    'SUBSPACE-CROP': cca.CROPPED_MATCH,
    'CHANNEL-HARMONIC': 'channel-energy average',
    'SHARED-RIDGE': 'shared ridge scorer',
}
# The plan's name key rows this package adds (site name first, export codes second); card 5's rows stay as released.
NAME_KEY = (
    ('cross-spectral ridge', 'XS-RIDGE'),
    ('whitened cross-spectral ridge', 'XS-RIDGE-W'),
    ('cross-spectral ridge with quadrature', 'XS-RIDGE-Q'),
    ('cross-spectral MLP', 'XS-MLP'),
)

# ---------------------------------------------------------------------------- the protocol's declaration rules
# flag -> (the protocol's rule text under statistics.rules_pp, the rule on a [lo, hi] interval in fractions)
RULES = {
    'above_zero': ('above_zero', 'lower>0', lambda lo, hi: lo > 0),
    'below_zero': ('below_zero', 'upper<0', lambda lo, hi: hi < 0),
    'strict_equivalence_2pp': ('equivalence', 'lower>-2 and upper<2', lambda lo, hi: lo > -0.02 and hi < 0.02),
}
NONINFERIORITY = ('XS-MLP', 'CCA-RAW', 'held8')          # the one prespecified non-inferiority contrast
NONINFERIORITY_RULE = 'lower>-2 for prespecified XS-MLP-CCA-RAW'

# ---------------------------------------------------------------------------- limitations, not run, declared edits
# key -> (pinned input, JSON pointer, phrase the field must contain); pointer '' is a whole text record.
LIMITATION_SOURCES = {
    'same_cohort_follow_up': ('xspec_handoff', '', 'This is an already studied dataset with frozen follow-up '
                                                   'decisions, not external validation.'),
    'unseen_means_excluded_from_fitting': ('xspec_handoff', '', '“Unseen” means excluded from supervised fitting '
                                                                'under these splits'),
    'unadjusted_intervals': ('xspec_protocol', '/statistics/multiplicity', 'none; all contrasts disclosed'),
    'comparators_reused': ('xspec_handoff', '', 'Comparators reuse sealed historical scores under the same matched '
                                                'protocol.'),
    'not_a_fixed_quadratic_form': ('xspec_caveats', '/notes/0', 'not a fixed quadratic form in raw EEG'),
    'whitening_composite_recipe': ('xspec_caveats', '/notes/1', 'composite whitening-feature recipe comparison'),
    'mlp_ridge_bundled_changes': ('xspec_caveats', '/notes/2',
                                  'changes nonlinearity, loss, regularization, optimizer and capacity'),
    'within_harmonic_matrices_only': ('xspec_handoff', '', 'they are not all cross-harmonic second-order interactions'),
    'mlp_seeds_averaged': ('xspec_protocol', '/mlp/primary_seed_aggregation', 'not logit ensemble'),
    'whitened_vs_cca_descriptive': ('xspec_approval', '/release_scope', 'no claim of formal W-CCA noninferiority'),
    'spectral_coordinates_vs_raw_cca': ('xspec_handoff', '', 'Primary cells retain Hann/cropped spectral coordinates '
                                                             'while CCA-RAW does not.'),
    'cropped_match_not_a_ceiling': ('xspec_handoff', '', 'SUBSPACE-CROP is useful context, not a proven ceiling for '
                                                         'learned scorers.'),
    'rotation_not_delay_invariance': ('xspec_protocol', '/feature_contract/physical_invariance_claim',
                                      'no general finite-window waveform-delay invariance'),
    'quadrature_direction_unresolved': ('xspec_handoff', '', 'This does not demonstrate that quadrature information '
                                                             'is absent or useless for every model.'),
    'nested_gain_scope': ('xspec_handoff', '', "It does not explain every earlier head's failure or establish "
                                               'universal sufficiency of second-order terms.'),
    'pre_score_engineering_corrections': ('xspec_handoff', '', 'Two disclosed pre-score engineering corrections '
                                                               'occurred'),
    'release_audit_scope': ('xspec_review', '', 'This release audit did not repeat supervised fits'),
}
CONTRAST_LIMITATIONS = {
    'XS-RIDGE minus SHARED-RIDGE': ('nested_gain_scope',),
    'XS-MLP minus CCA-RAW': ('spectral_coordinates_vs_raw_cca',),
    'XS-RIDGE minus CCA-RAW': ('spectral_coordinates_vs_raw_cca',),
    'XS-RIDGE-W minus XS-RIDGE': ('whitening_composite_recipe',),
    'XS-MLP minus XS-RIDGE': ('mlp_ridge_bundled_changes',),
    'XS-RIDGE-Q minus XS-RIDGE': ('quadrature_direction_unresolved',),
}
# item -> (pinned input, JSON pointer, phrase); nothing in this release runs these items later.
NOT_RUN_SOURCES = {
    'raw-time learned cell': ('xspec_handoff', '', 'The optional raw-time learned cell was prospectively deferred'),
    'cross-harmonic second-order terms': ('xspec_handoff', '', 'they are not all cross-harmonic second-order '
                                                               'interactions'),
}
DECLARED_EDITS = {
    'xspec': (
        'release_status not selected; state/release-approval.json records the approval',
        'prediction_seal_sha256 not selected; it is checked against the release audit',
        'per_seed_descriptive not selected (per-seed MLP means)',
        'random_pairing not selected (random-pairing accuracies); the chance levels come from the protocol',
        'canary_real_label_accuracy_descriptive_only not selected (canary accuracies)',
        'MLP_aggregation and multiplicity strings not selected; the page writes its own copy from limitations_keys',
        'held8 and seen32 named u8 and seen_ba in ids (card 5\'s spelling of the same two tasks, checked through '
        'CCA\'s own value)',
        'ridge arms carry "deterministic fit", training-free comparators "no training", XS-MLP its seed count',
        'the handoff\'s historical-point and band lines not selected (thread predictions stay on card 4, D23)',
        'the handoff\'s CCA identity approximation table not selected; the identity pair count is kept under checks',
        'descriptive_gaps holds XS-RIDGE-W minus CCA-RAW as the difference of the two source levels, with no '
        'interval, as the handoff\'s descriptive table states it',
    ),
}

# ---------------------------------------------------------------------------- what no block may carry
REFUSED_KEYS = set(cca.REFUSED_KEYS) | {
    'per_seed_descriptive', 'random_pairing', 'canary_real_label_accuracy_descriptive_only',
    'evaluation_random_pairing_descriptive', 'MLP_aggregation', 'existing_normalized_xs_ridge_bet',
    'prespecified_eigenvalue_claim', 'point_absolute_gap_within5pp', 'thread_bet', 'remote_root', 'interpretation',
    'epochs', 'multiplicity'}
REFUSED_KEY_FRAGMENTS = tuple(cca.REFUSED_KEY_FRAGMENTS) + (
    'per_window', 'confusion', 'percentile', 'quantile', 'memory', 'fifty', '055', 'random_pairing', 'canary_real',
    'historical', 'thread', 'comment')
# The thread's lines (D23): the historical 39% point, the 32-36% band, the 65% and 75.9% figures, the 70% bet.
THREAD_TEXT = re.compile(r'\b39(?:\.0+)?\s*%|\b32\s*[–-]\s*36\b|\b75\.9\b|historical|\bbet\b|commenter|hugging\s*face',
                         re.IGNORECASE)
THREAD_VALUES = (0.39, 0.32, 0.36, 0.65, 0.70, 0.759)
CONFIDENCE_VALUE = 11 / 20                                # written as a ratio so it is never spelled here


# ---------------------------------------------------------------------------- helpers
def read_pins(pins, expected, text_pins, served):
    """Every pinned input, refused unless it is byte for byte the pinned file. Returns ({name: doc}, {name: sha})."""
    require(set(pins) == set(expected), f'pins: expected {sorted(expected)}')
    docs, digests = {}, {}
    for name, ref in pins.items():
        raw = location(ref['path']).read_bytes()
        digest = sha(raw)
        require(digest == ref['sha256'], f'{name}: {Path(ref["path"]).name} is {digest[:12]}, pinned {ref["sha256"][:12]}')
        docs[name] = raw.decode('utf-8') if name in text_pins else json.loads(raw)
        digests[name] = digest
    for name, path in served.items():
        require(sha(location(path).read_bytes()) == digests[name],
                f'{name}: the served copy differs from the copy the site builds from')
    return docs, digests


def load(pins=None):
    return read_pins(pins or PINS, PINS, TEXT_PINS, SERVED)


def inputs_available(pins=None):
    """Whether the pinned inputs are on this machine; the research folders are local, not in the repository."""
    return (all(location(r['path']).exists() for r in (pins or PINS).values())
            and all(location(p).exists() for p in SERVED.values()))


def floats(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from floats(v)
    elif isinstance(value, list):
        for v in value:
            yield from floats(v)
    elif isinstance(value, float):
        yield value


def level(metric, people, seeds, origin, label):
    """A level copied from an aggregate metric block {mean, ci95}."""
    require(isinstance(metric, dict) and set(metric) == {'mean', 'ci95'} and len(metric['ci95']) == 2,
            f'{label}: not a level with an interval')
    return {'estimate': metric['mean'], 'interval': interval(*metric['ci95'], metric['mean'], label), 'unit': PROPORTION,
            'people': people, 'seeds': seeds, 'origin': origin}


def same_level(lv, twin, label, tol=TOL):
    """A reused level equals the level of the card it comes from: numbers to `tol`, every other field exactly."""
    for k in ('unit', 'people', 'seeds'):
        require(lv[k] == twin[k], f'{label}: {k} {lv[k]!r} differs from {twin[k]!r}')
    pairs = [(lv['estimate'], twin['estimate'])] + list(zip(lv['interval'], twin['interval']))
    for a, b in pairs:
        close(a, b, f'{label} differs from the card it reuses', tol)
    return max(abs(a - b) for a, b in pairs)


def display_floor(iv):
    """The bounds of a difference that are not zero but print as 0.00 in percentage points (pp2)."""
    return [side for side, b in zip(('lower', 'upper'), iv) if b != 0 and abs(b * 100) < 0.005]


def paired_contrast(source, role, left, right, levels, people, seeds, label):
    """A paired contrast {mean, ci95} from the aggregate, refused unless it is the difference of its two levels."""
    require(isinstance(source.get('ci95'), list) and len(source['ci95']) == 2, f'{label}: no interval')
    est = source['mean']
    close(est, levels[left]['estimate'] - levels[right]['estimate'], f'{label} is not the difference of its levels')
    iv = interval(*source['ci95'], est, label, lower=-1.0)
    flags = {'interval_includes_zero': iv[0] <= 0 <= iv[1]}
    low = display_floor(iv)
    if low:
        flags['bound_below_two_decimals'] = low
    return {'role': role, 'left': left, 'right': right, 'estimate': est, 'interval': iv, 'unit': DIFFERENCE,
            'people': people, 'seeds': seeds, 'flags': flags}


def contrast_table(text, label):
    """The handoff's table of formal contrasts: [(left, right, metric, role)] in its own order."""
    rows = re.findall(r'^\| (Primary|Secondary) \| (held8|seen32) \| (\S+) − (\S+) \|', text, re.MULTILINE)
    require(rows, f'{label}: the handoff states no contrast table')
    return [(a, b, m, r.lower()) for r, m, a, b in rows]


def limitations(sources, docs, label):
    keys = []
    for key, (name, ptr, phrase) in sources.items():
        stated(docs, name, ptr, phrase, f'{label} limitation {key}')
        keys.append(key)
    return keys


def not_run(sources, docs, label):
    rows = []
    for item, (name, ptr, phrase) in sources.items():
        stated(docs, name, ptr, phrase, f'{label} not run {item!r}')
        rows.append({'item': item, 'run_in': None})
    return rows


def contrast_limitations(mapping, sources, contrasts, label):
    out = {}
    for cid in contrasts:
        keys = mapping.get(cid.split('/')[0])
        if keys:
            require(set(keys) <= set(sources), f'{label} {cid}: a limitation is not sourced')
            out[cid] = list(keys)
    return out


def display_names(names, levels, label):
    codes = list(dict.fromkeys(lid.split('/')[0] for lid in levels))
    require(set(codes) <= set(names), f'{label}: no display name for {set(codes) - set(names)}')
    return {c: names[c] for c in codes}


def comparator_hash(protocol, suffix, label):
    hits = [v for k, v in protocol['comparator_hashes'].items() if k.endswith(suffix)]
    require(len(hits) == 1, f'{label}: the protocol pins no single {suffix}')
    return hits[0]


def released_card5(docs):
    """Card 5's released block and the released card anchors, checked to be the 2026-10-20 release as released."""
    rel = docs['released']
    require(rel['release_id'] == RELEASED_ID, 'released: another release id')
    cards = {c['card']: c for c in rel['placement']['cards']}
    require(cards[5]['studies'] == ['cca_diagnostics'] and cards[5]['anchor'] == 'cca-mechanism',
            'released: card 5 is not the CCA diagnostics')
    require(cards[CARD]['anchor'] == ANCHOR and cards[CARD]['studies'] == [] and cards[CARD].get('status_only') is True,
            'released: card 8 is not the cross-spectral status card')
    return rel['studies']['cca_diagnostics'], cards


def withheld(docs_export, published):
    """Values the aggregate holds that this release does not publish (per-seed means, canary and random-pairing
    accuracies), less any value the same aggregate also publishes in a selected field and the chance levels."""
    held = set(floats({k: docs_export[k] for k in ('per_seed_descriptive', 'canary_real_label_accuracy_descriptive_only')
                       if k in docs_export}))
    for key in ('random_pairing', 'evaluation_random_pairing_descriptive'):
        for arm in docs_export.get(key, {}).values():
            held |= set(floats(arm.get('permutation_mean', {})))
    return held - set(floats(published)) - {0.125, 0.03125}


# ---------------------------------------------------------------------------- the cross-spectral scorer (card 8)
def xspec_block(docs, digests):
    ex, protocol, fz, er, audit, approval, caveats = (docs[k] for k in (
        'xspec_export', 'xspec_protocol', 'xspec_freeze', 'xspec_execution_review', 'xspec_audit', 'xspec_approval',
        'xspec_caveats'))
    review, handoff, runner = docs['xspec_review'], docs['xspec_handoff'], docs['xspec_runner']

    # Release status: the approval, never the aggregate's own frozen field.
    require(approval['status'] == 'APPROVED_AGGREGATE_HANDOFF', 'xspec: the release approval does not approve')
    bound(approval['verified_aggregate_sha256'], digests['xspec_export'], 'xspec approval export')
    bound(approval['independent_summary_sha256'], digests['xspec_audit'], 'xspec approval audit')
    bound(approval['handoff_sha256'], digests['xspec_handoff'], 'xspec approval handoff')
    require(approval['independent_review'] == 'review/Independent Results Release Review.md',
            'xspec: the approval names another review')
    bound(audit['aggregate_sha256'], digests['xspec_export'], 'xspec audit export')
    bound(audit['protocol_sha256'], digests['xspec_protocol'], 'xspec audit protocol')
    bound(audit['freeze_sha256'], digests['xspec_freeze'], 'xspec audit freeze')
    bound(audit['execution_review_sha256'], digests['xspec_execution_review'], 'xspec audit execution review')
    bound(audit['prediction_seal_sha256'], ex['prediction_seal_sha256'], 'xspec audit seal')
    bound(fz['protocol_sha256'], digests['xspec_protocol'], 'xspec freeze protocol')
    bound(fz['code_sha256']['run_xspec.py'], digests['xspec_runner'], 'xspec freeze runner')
    bound(er['freeze_sha256'], digests['xspec_freeze'], 'xspec execution review freeze')
    bound(er['protocol_sha256'], digests['xspec_protocol'], 'xspec execution review protocol')
    bound(er['code_sha256']['run_xspec.py'], digests['xspec_runner'], 'xspec execution review runner')
    for name in ('xspec_export', 'xspec_protocol', 'xspec_freeze', 'xspec_execution_review'):
        require(digests[name] in review, f'xspec: the release review does not bind {name}')
    require('PASS for root' in review and 'There are **no remaining technical audit holds**' in review,
            'xspec: the release review did not pass')
    require(er['status'] == 'PASS', 'xspec: the execution review did not pass')
    require(audit['audit_status'] == 'PASS_FOR_ROOT_RELEASE_DECISION' and audit['all_sealed_payload_hashes_match'] is True
            and audit['all_metrics_after_seal'] is True and audit['artifact_mutation'] is False,
            'xspec: the release audit did not pass')
    require(number(audit['metric_max_absolute_discrepancy']) and audit['metric_max_absolute_discrepancy'] <= TOL
            and audit['identity_summary_max_absolute_discrepancy'] == 0.0, 'xspec: the release audit recomputation')
    require(caveats['supervised_fits_or_accuracy_seen'] is False and caveats['scientific_protocol_changed'] is False,
            'xspec: the interpretation caveats do not predate the results')
    require(ex['aggregate_only'] is True, 'xspec: the aggregate is not aggregate-only')

    # Interval rule: the aggregate's draws and seed, the protocol's percentile rule, the runner's quantiles.
    st = protocol['statistics']
    require(ex['bootstrap_n'] == st['bootstrap_draws'] == DRAWS, 'xspec: bootstrap draws')
    require(ex['bootstrap_seed'] == st['bootstrap_seed'] == SEED, 'xspec: bootstrap seed')
    require(st['interval'].startswith('percentile95') and 'identical draws' in st['interval'], 'xspec: interval rule')
    require("np.quantile(b,[.025,.975],method='linear')" in runner, 'xspec: the runner takes no percentile interval')
    require(st['multiplicity'].startswith('none;'), 'xspec: multiplicity')

    # Card 5: the same cohort, and the run's pinned comparators are card 5's study.
    diag, cards = released_card5(docs)
    bound(comparator_hash(protocol, 'cca_diagnostics_20261015/protocol.json', 'xspec'), diag['protocol_sha256'],
          'xspec comparators protocol')
    bound(comparator_hash(protocol, 'cca_diagnostics_20261015/execution-freeze.json', 'xspec'), diag['freeze_sha256'],
          'xspec comparators freeze')
    dataset = dict(diag['design']['dataset'])
    people = ex['person_count']
    require(people == dataset['people'] == 70 and ex['rotations'] == dataset['frequency_rotations'] == 5,
            'xspec: not card 5\'s people and rotations')
    stated(docs, 'xspec_handoff', '', 'Seven participant folds × five frequency rotations', 'xspec folds')
    require(dataset['person_folds'] == 7 and protocol['identity_audit']['argmax_decision_count'] == dataset['windows'],
            'xspec: not card 5\'s folds and windows')
    split_fits = dataset['person_folds'] * dataset['frequency_rotations']
    sa = protocol['source_admission']
    require(sa['candidates_per_fit'] == 32 and sa['rows_per_fit'] == 7680, 'xspec: source admission')
    endpoints = {e: dict(v) for e, v in diag['design']['endpoints'].items()}
    rp = protocol['canaries']['evaluation_random_pairing']
    require(set(endpoints) == set(ENDPOINTS) and endpoints['u8']['chance'] == rp['exact_expected_held8'] == 1 / 8
            and endpoints['seen_ba']['chance'] == rp['exact_expected_seen32'] == 1 / 32, 'xspec: endpoints or chance')
    require(diag['design']['harmonics'] == 3, 'xspec: card 5 harmonics')
    stated(docs, 'xspec_handoff', '', 'Matrices are full **within each of three harmonics**', 'xspec harmonics')

    # The arms: the four cells of the protocol, then the four reused comparators, in the aggregate's order.
    cells = protocol['main_cells']
    require(tuple(cells) == NEW_ARMS and tuple(ex['arms']) == NEW_ARMS + tuple(REUSED), 'xspec: the arm set changed')
    mlp = protocol['mlp']
    seeds = mlp['seeds']
    require(len(seeds) == len(set(seeds)) == 3 and 'not logit ensemble' in mlp['primary_seed_aggregation'],
            'xspec: MLP seeds')
    for c in NEW_ARMS:
        require(cells[c]['fits'] == split_fits * (len(seeds) if c == 'XS-MLP' else 1), f'xspec: {c} fit count')
    require(protocol['main_fit_count'] == sum(cells[c]['fits'] for c in NEW_ARMS), 'xspec: main fit count')
    seeds_of = {c: DETERMINISTIC for c in NEW_ARMS} | {'XS-MLP': len(seeds)}

    levels, codes, reused, worst = {}, {}, {}, 0.0
    for code in ex['arms']:
        for e, src in ENDPOINTS.items():
            lid = f'{code}/{e}'
            if code in REUSED:
                there = f'{REUSED[code]}/{e}'
                twin = diag['levels'][there]
                lv = level(ex['arms'][code][src], people, twin['seeds'], REUSED_FROM['origin'], f'xspec {lid}')
                worst = max(worst, same_level(lv, twin, f'xspec {lid} (card 5 {there})'))
                codes[lid] = ['#' + pointer('arms', code, src),
                              REUSED_FROM['study'] + diag['export_codes'][there][0],
                              f'{RELEASED_FILE}#' + pointer('studies', REUSED_FROM['study'], 'levels', there)]
            else:
                lv = level(ex['arms'][code][src], people, seeds_of[code], 'new', f'xspec {lid}')
                codes[lid] = ['#' + pointer('arms', code, src)]
            levels[lid] = lv
        if code in REUSED:
            require(DISPLAY_NAMES[code] == diag['display_names'][REUSED[code]], f'xspec {code}: two names for one set '
                                                                                 'of scores')
            reused[code] = {'card': REUSED_FROM['card'], 'study': REUSED_FROM['study'],
                            'anchor': cards[REUSED_FROM['card']]['anchor'], 'code': REUSED[code]}

    # Contrasts: the protocol's ten, in its order and with its roles; the handoff's table states the same.
    planned = [(a, b, 'held8', 'primary') for a, b in st['primary_held8']]
    planned += [(a, b, 'held8', 'secondary') for a, b in st['secondary_held8']]
    require(st['secondary_seen32'] == 'each of fourXS cells minus SHARED-RIDGE' and len(NEW_ARMS) == 4,
            'xspec: the seen-32 contrasts')
    planned += [(c, 'SHARED-RIDGE', 'seen32', 'secondary') for c in NEW_ARMS]
    require(len(planned) == st['formal_paired_contrast_count'] == len(ex['contrasts']) == 10, 'xspec: ten contrasts')
    require([(c['a'], c['b'], c['metric']) for c in ex['contrasts']] == [p[:3] for p in planned],
            'xspec: the aggregate contrasts differ from the protocol')
    require(contrast_table(handoff, 'xspec') == planned, 'xspec: the handoff states other contrasts or roles')
    rules = st['rules_pp']
    for flag, (rule_key, text, _) in RULES.items():
        require(rules[rule_key] == text, f'xspec: the protocol rule for {flag} changed')
    require(rules['noninferiority_to_CCA'] == NONINFERIORITY_RULE, 'xspec: the non-inferiority rule changed')

    contrasts = {}
    for i, (c, (a, b, metric, role)) in enumerate(zip(ex['contrasts'], planned)):
        e = next(k for k, v in ENDPOINTS.items() if v == metric)
        cid = f'{a} minus {b}/{e}'
        pair = (a, b)
        n_seeds = len(seeds) if 'XS-MLP' in pair else DETERMINISTIC if set(pair) & set(RIDGE_ARMS) else NO_TRAINING
        out = paired_contrast(c, role, f'{a}/{e}', f'{b}/{e}', levels, people, n_seeds, f'xspec {cid}')
        lo, hi = out['interval']
        for flag, (_, _, rule) in RULES.items():
            require(c[flag] is rule(lo, hi), f'xspec {cid}: {flag} does not follow the protocol rule')
            out['flags'][flag] = c[flag]
        ni = c['prespecified_noninferiority_to_CCA']
        require(ni is ((lo > -0.02) if (a, b, metric) == NONINFERIORITY else None),
                f'xspec {cid}: non-inferiority does not follow the protocol rule')
        out['flags']['prespecified_noninferiority_to_CCA'] = ni
        contrasts[cid], codes[cid] = out, ['#' + pointer('contrasts', i)]

    # The whitened readout against CCA: a difference of two levels with no planned interval, as the handoff states.
    require(not any({c['left'].split('/')[0], c['right'].split('/')[0]} == {'XS-RIDGE-W', 'CCA-RAW'}
                    for c in contrasts.values()), 'xspec: a contrast of XS-RIDGE-W against CCA-RAW was not planned')
    stated(docs, 'xspec_handoff', '', 'W was not the prespecified CCA non-inferiority cell', 'xspec undefined')
    undefined = [{'contrast': 'XS-RIDGE-W minus CCA-RAW', 'reason': 'not_a_planned_contrast'}]
    row = re.findall(r'^\| XS-RIDGE-W \| (-?[\d.]+) \| (-?[\d.]+) \| (-?[\d.]+) \|$', handoff, re.MULTILINE)
    require(len(row) == 1, 'xspec: the handoff states no descriptive gap for XS-RIDGE-W')
    gaps = {}
    for e, stated_pp in (('u8', row[0][0]), ('seen_ba', row[0][2])):
        left, right = f'XS-RIDGE-W/{e}', f'CCA-RAW/{e}'
        gap = levels[left]['estimate'] - levels[right]['estimate']
        require(f'{gap * 100:.2f}' == stated_pp, f'xspec: the {e} gap is not the handoff\'s {stated_pp}')
        gaps[f'XS-RIDGE-W minus CCA-RAW/{e}'] = {
            'left': left, 'right': right, 'estimate': gap, 'unit': DIFFERENCE,
            'basis': 'difference of the two levels; no planned contrast and no interval',
            'export_codes': codes[left][:1] + codes[right][:1]}

    # Counts only: fits, identity pairs, the release audit's rehash and recomputation counts.
    af, can = protocol['audit_fits'], protocol['canaries']['training_label_permutation']
    ridge_refits, mlp_refits = af['independent_ridge_refits']['count'], len(af['mlp_full_refits'])
    additional = af['bridge_count'] + can['count'] + ridge_refits + mlp_refits
    require(protocol['main_fit_count'] == audit['main_fits'] == approval['main_fits'] == 210, 'xspec: main fits')
    require(additional == audit['additional_fits'] == approval['additional_fits'] == 118, 'xspec: additional fits')
    require(audit['total_fits'] == af['total_fits_including_canaries'] == 210 + additional, 'xspec: total fits')
    require(audit['audit_counts'] == {'bridges': af['bridge_count'], 'audit-refits': ridge_refits + mlp_refits,
                                      'audit-forward': af['mlp_forward_reconstructions']}, 'xspec: audit counts')
    stated(docs, 'xspec_handoff', '', 'All **210 main fits** and **118 additional fits** completed', 'xspec fits')
    identity = protocol['identity_audit']
    require(identity['all_pair_count'] == dataset['windows'] * dataset['targets'] == 448000, 'xspec: identity pairs')
    stated(docs, 'xspec_handoff', '', 'reproduces sealed CCA² over all **448,000 trial–candidate pairs**',
           'xspec identity')
    stated(docs, 'xspec_handoff', '', 'All **706 retained payloads** and **720 archived originals** were independently '
           'rehashed', 'xspec recovery rehash')
    require(audit['retained_payloads_rehashed'] == 706 and audit['archived_originals_rehashed'] == 720,
            'xspec: recovery rehash counts')
    checks = {
        'release_approval': {'approved': True},
        'release_review': {'passed': True, 'technical_holds': 0},
        'execution_review': {'passed': True},
        'release_audit': {'passed': True, 'sealed_artifacts': audit['seal_artifact_count'],
                          'source_admission_sets': audit['source_admission_sets_verified'],
                          'metric_entries_recomputed': audit['metric_entries_recomputed'],
                          'retained_payloads_rehashed': audit['retained_payloads_rehashed'],
                          'archived_originals_rehashed': audit['archived_originals_rehashed']},
        'fits': {'main': protocol['main_fit_count'], 'additional': additional, 'total': audit['total_fits'],
                 'bridges': af['bridge_count'], 'canaries': can['count'], 'independent_ridge_refits': ridge_refits,
                 'independent_mlp_refits': mlp_refits, 'mlp_forward_reconstructions': af['mlp_forward_reconstructions']},
        'cca_identity': {'pairs': identity['all_pair_count']},
        'pre_score_corrections': {'count': 2},
        'same_scores_as_card_5': {'passed': True, 'card': REUSED_FROM['card'], 'codes': list(REUSED),
                                  'tolerance': TOL, 'max_absolute_difference': worst},
    }

    design = {
        'dataset': dataset,
        'endpoints': endpoints,
        'harmonics': diag['design']['harmonics'],
        'source_windows_per_fit': sa['rows_per_fit'],
        'seen_frequencies_per_fit': sa['candidates_per_fit'],
        'arms': [{'code': c, 'training': 'ridge fitted on source people' if c != 'XS-MLP'
                  else 'MLP trained on source people', 'fits': cells[c]['fits'], 'input_count': cells[c]['features']}
                 for c in NEW_ARMS],
        'comparators': [{'code': c, 'training': 'ridge fitted on source people' if c == 'SHARED-RIDGE' else NO_TRAINING,
                         'card': REUSED_FROM['card']} for c in REUSED],
        'main_fits': protocol['main_fit_count'],
    }
    for row in design['arms']:
        if row['code'] == 'XS-MLP':
            require(mlp['shape'][0] == cells['XS-MLP']['features'] and mlp['shape'][2] == 1, 'xspec: MLP shape')
            row.update(training_seeds=len(seeds), hidden_units=mlp['shape'][1], training_epochs=mlp['epochs'])
    for row in design['comparators']:
        variant = next((s.get('variant') for s in diag['design']['scorers'] if s['code'] == row['code']), None)
        if variant:
            row['variant'] = variant
    return {
        'source_sha256': digests['xspec_export'],
        'review_sha256': digests['xspec_review'],
        'audit_summary_sha256': digests['xspec_audit'],
        'approval_sha256': digests['xspec_approval'],
        'protocol_sha256': digests['xspec_protocol'],
        'freeze_sha256': digests['xspec_freeze'],
        'execution_review_sha256': digests['xspec_execution_review'],
        'caveats_sha256': digests['xspec_caveats'],
        'runner_sha256': digests['xspec_runner'],
        'released_sha256': digests['released'],
        'interval_method': {'method': METHOD, 'draws': ex['bootstrap_n'], 'seed': ex['bootstrap_seed'], 'level': LEVEL},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations(CONTRAST_LIMITATIONS, LIMITATION_SOURCES, contrasts, 'xspec'),
        'descriptive_gaps': gaps,
        'reused': reused,
        'undefined': undefined,
        'not_run': not_run(NOT_RUN_SOURCES, docs, 'xspec'),
        'checks': checks,
        'limitations_keys': limitations(LIMITATION_SOURCES, docs, 'xspec'),
        'display_names': display_names(DISPLAY_NAMES, levels, 'xspec'),
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
        require(not (len(value) > 2 and all(count(v) for v in value)), f'{trail}: an integer list (row indices?)')
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not cca.REFUSED_TEXT.search(value), f'{trail}: refused text {value!r}')
        require(not cca.VERSION_LABEL.search(value), f'{trail}: a version label {value!r}')
        require(not cca.RANKING.search(value), f'{trail}: a ranking word {value!r}')
        require(not THREAD_TEXT.search(value), f'{trail}: a thread line {value!r}')
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        require(math.isfinite(value), f'{trail}: not finite')
        require(abs(value - CONFIDENCE_VALUE) > 1e-12 and abs(value - 100 * CONFIDENCE_VALUE) > 1e-9,
                f'{trail}: refused value {value!r}')
        require(not (isinstance(value, float) and any(value == t for t in THREAD_VALUES)),
                f'{trail}: a thread figure {value!r}')


def finish(blocks, withheld_values):
    """The checks every block of this package passes before it leaves the module."""
    for name, block in blocks.items():
        require(all(f in block for f in BLOCK_FIELDS), f'{name}: a block field is missing')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
                f'{name}: export codes do not cover the levels and contrasts')
        for c in block['contrasts'].values():
            require(c['left'] in block['levels'] and c['right'] in block['levels'], f'{name}: a contrast side is no level')
        for lid, lv in block['levels'].items():
            require(lv['origin'] == 'new' or lid.split('/')[0] in block['reused'], f'{name} {lid}: unlabelled reuse')
        require(not withheld_values & set(floats(block)), f'{name}: a withheld value is in the block')
    validate_public(blocks)
    scrub_check(blocks)
    return blocks


def build_from(docs, digests):
    block = xspec_block(docs, digests)
    held = withheld(docs['xspec_export'], {k: docs['xspec_export'][k] for k in ('arms', 'contrasts')})
    return finish({STUDY: block}, held)


def build_blocks(pins=None) -> dict:
    """The cross-spectral study block, keyed xspec."""
    return build_from(*load(pins))


if __name__ == '__main__':
    built = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'limitations': len(b['limitations_keys'])} for s, b in built.items()}, indent=2))
