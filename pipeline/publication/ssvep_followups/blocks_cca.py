"""The CCA blocks of the new-SSVEP-frequencies release: cards 5 to 7 (CCA diagnostics, CCA adapter, Wearable-102).

Three audited route 3 follow-ups, read from their own exports and turned into study blocks for
`new-ssvep-frequencies-update.json`, which the assembler of that file (B4) puts under `studies`:

- `cca_diagnostics`: where CCA's lead on held-out frequencies comes from; six training-free scorers and one shared
  ridge scorer (35 fits) on the BETA cohort, seven prespecified contrasts on two endpoints, from
  `exports/aggregate-evidence.json`;
- `cca_adapter`: temporal CCA with a bounded learned correction, its controls and its two CCA baselines; six
  prespecified contrasts on two endpoints, the decision transitions and the protected margin, from
  `exports/CCA Adapter Aggregate Results.json` only (R1 binding review: the handoff is context, never a source);
- `wearable_transfer`: the 105 unchanged BETA models of the adapter study on Wearable-102, against matched CCA, dry
  and wet primary and both sensors secondary, with the cropped-spectrum check under its own name, from
  `exports/wearable102-frozen-transfer.json`, and the A2 fact on which CCA it reports.

Every input is pinned by SHA-256 (PINS) and refused unless it is byte for byte the pinned file and the study's reviews
and receipts bind that hash; the transfer's freeze must bind the adapter study's release records. Every number is the
source's own double: nothing is rounded, rescaled or recomputed, and units stay fractions. A contrast must equal the
difference of its two levels, an interval must hold its point, the adapter export must equal its numerical review's
aggregate, and the two exports that carry CCA and the cropped-spectrum match must carry bit-identical scores for them:
one set of scores under one site name. The pinned protocols and receipts carry private storage paths and operator
status strings, so they are read and checked here, never copied; only named fields are selected from them.

The declared edits (plan section 3; DECLARED_EDITS lists them per study for the manifest):
- the diagnostics' private root, job block (process id, timestamps, status), stale release status, row indices and
  random-pairing ranges are not selected; the adapter's runner status, bootstrap index hash, per-seed values and
  privacy string are not selected; the transfer's free-text strings and its contrast against the cropped check are not
  selected;
- the endpoints `held8_accuracy` and `seen32_balanced_accuracy` are named `u8` and `seen_ba` in level and contrast ids,
  the route 3 spelling of the same two tasks, checked through CCA's own value on the live route 3 file;
- every CCA and training-free level carries "no training" where a trained level carries its seed count;
- the adapter's `protected_trials` is published as `protected_instances`, labelled as prediction instances.

A block is a mapping with the fields of the B1 blocks (see blocks_query.py):
- `source_sha256`, `review_sha256` (the review that accepted the source), and the other pinned records by name;
- `interval_method`: `{method, draws, seed, level}` plus `conditional_on` where the study states it; every block is a
  paired person bootstrap with seed 20261015, the adapter's seed read from its numerical review and its percentile
  rule from its pinned runner, because the export carries neither;
- `design`: the dataset, the endpoints with their chance levels, and the scorers, arms or models;
- `levels`: `{id: {estimate, interval, unit, people, seeds, origin}}`; an id is `<export code>/<endpoint>` (`u8`,
  `seen_ba`; `dry`, `wet`, `all` for Wearable-102); `origin` is `new` or `reused_cca_diagnostics`, and a reused level
  is checked bit for bit against the diagnostics block;
- `contrasts`: `{id: {role, left, right, estimate, interval, unit, people, seeds, flags}}`; `role` is `prespecified`
  (cards 5 and 6) or `primary`/`secondary` (card 7); `flags` are derived here and say which interval holds zero, which
  contrast is a pair of identical results and what a bundled contrast bundles;
- `contrast_limitations`: `{contrast id: [limitation key]}`, the caveat that sits next to that evidence;
- `undefined`: `[{contrast, reason}]`, the comparison that has no planned interval (adapted head against CCA alone);
- `not_run`: `[{item, run_in}]`; `checks`: the reviews', audits' and gates' pass or fail and counts;
- `limitations_keys`: keys of the limitations the page states (LIMITATION_SOURCES gives each key's source sentence);
- `display_names`: the site name of every code the block's ids use (section 2.1's name key; the Wearable-102
  cropped-spectrum check keeps its own name); `export_codes`: `{id: ['#<JSON pointer>']}` into the study's export,
  plus `cca_diagnostics#<JSON pointer>` for a reused level.
The adapter block adds `transitions` (shares of all decisions on the task, not of CCA's errors) and `protection`
(the export's raw `protected_margin`); the Wearable-102 block adds `cca_definition` (the A2 fact).

    python3 pipeline/publication/ssvep_followups/blocks_cca.py      # builds and prints the counts; writes nothing
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

from export_snapshot import FORBIDDEN_KEYS, validate_public  # noqa: E402

PROJECT = PUBLICATION.parents[1]
LOCAL = PUBLICATION / 'local_paths.json'                   # optional `researchRoot`: where this machine keeps research/

# ---------------------------------------------------------------------------- pinned inputs
# Paths are relative to the project; `research/...` resolves under `researchRoot` when local_paths.json sets one.
_D, _A, _W = ('research/decision_route3_cca_diagnostics_20261015', 'research/decision_route3_cca_adapter_20261015',
              'research/decision_route3_external_20261015')
_R = 'research/publication_review_20261020'
PINS = {
    'diag_export': {'path': f'{_D}/exports/aggregate-evidence.json',
                    'sha256': 'fae60f74c73c99c441aedca3ad0d8c2fe7a9360e83fec0348e53962c4a53b1cf'},
    'diag_protocol': {'path': f'{_D}/protocol.json',
                      'sha256': '92a4c24e320277b064a2eb2ce8357f90714e5a7a0aca2d0ae19fe1a474a12195'},
    'diag_freeze': {'path': f'{_D}/execution-freeze.json',
                    'sha256': 'd98eb3f78f8fe18518d7d41f2dae0fb2901547e9fc10569563f55c66ee7f40fc'},
    'diag_review': {'path': f'{_D}/review/Final Result Release Review.json',
                    'sha256': 'c9db74cd35d1559a7375b0c8f6e5cc22055525098f68e0c58caceae6f9183d80'},
    'diag_hash_verification': {'path': f'{_D}/review/Independent Release Hash Verification.json',
                               'sha256': 'dab529224e16db3b1913737a20553174a1265af123ac0bddc5428af2b3bc9f4d'},
    'diag_handoff_review': {'path': f'{_D}/review/final-handoff-review.json',
                            'sha256': 'f9fd999be41a561ecd498f05e4db344bc065f277f60547ecb2925b21343a98d8'},
    'adapter_export': {'path': f'{_A}/exports/CCA Adapter Aggregate Results.json',
                       'sha256': '6f68114e4d431beb4903f68e3e2d4549da825d8f94d2ff3a776e368a7b3dca2b'},
    'adapter_protocol': {'path': f'{_A}/protocol.json',
                         'sha256': '22826d2ceae1a46968fffabf56951d84abbbce3f75d8a4962f3ad385228194ca'},
    'adapter_freeze': {'path': f'{_A}/execution-freeze.json',
                       'sha256': '29bdbe5af3601385e8e3ef47d72985132278be269939d63a01f4b9708e8fa3b1'},
    'adapter_numerical_review': {'path': f'{_A}/review/release-numerical-audit.json',
                                 'sha256': 'e880280e330f03a280281936e01a52371d4ca3e4c383e4a527a28b106fd12e5c'},
    'adapter_review': {'path': f'{_A}/review/release-interpretation-review.json',
                       'sha256': '4e1a38171be118d0c4d1b0f145c4b24578b18af349cccfa265c4aec335f9d4ac'},
    'adapter_release_status': {'path': f'{_A}/state/release-status.json',
                               'sha256': '9f4929bbda746079ad1bfc8625f9d0c2eaebd099b505f33a2eaf0663821680bd'},
    'adapter_runner': {'path': f'{_A}/scripts/run_adapter.py',
                       'sha256': 'dc304bd80a21d79ed24f3d5cf0d5e879a37129d90d724532e1c39f3be963da10'},
    'adapter_binding_review': {'path': f'{_R}/reviews/cca-adapter-binding-review.md',
                               'sha256': '957c9de845b8f1fd4e521cfadbf27059f8f64cd84cb76c0a613d14f0df43201f'},
    'wear_export': {'path': f'{_W}/exports/wearable102-frozen-transfer.json',
                    'sha256': '9c94a14be0b55822fe7dd359b6f02bb07340e4b0bb3d74d3479bbd4219cb50f6'},
    'wear_protocol': {'path': f'{_W}/protocol.json',
                      'sha256': '079acad5374eb1b45245bb57c51ba384c5532eb7046d3b246634a592d02e223b'},
    'wear_freeze': {'path': f'{_W}/freeze.json',
                    'sha256': 'd24ddc66a542c80c06196935f5a6183e33782e0bbe72a7c0c53a80258cc1de30'},
    'wear_review': {'path': f'{_W}/review/release-interpretation-review.json',
                    'sha256': 'd12eb3600827cd6c9babe4aa5d2a90026db80cd9db39b03e43a3bcc7d3aa99d1'},
    'wear_numerical_summary': {'path': f'{_W}/review/release-numerical-summary.json',
                               'sha256': 'dd6ca7671893901444e60b1525a0add8d29756cf2ecb9803c345730365125448'},
    'wear_release_status': {'path': f'{_W}/state/release-status.json',
                            'sha256': '756b368478469c8057b566a378a70e0424cdde39fab3abfcdeae4bbc1f4992a5'},
    # A2: which CCA the transfer reports, and the dry-versus-wet values it is set beside.
    'wear_cca_definition': {'path': f'{_R}/notes/wearable-cca-definition.json',
                            'sha256': '5d3684165974b5b260c4afb3b55f90ed2cba635fe3cbb43158b020f684a65224'},
    'dry_vs_wet': {'path': 'site/src/data/deployment-topics.json',
                   'sha256': '708e6daad94bad3e32a4602af276e40d559e262741e92196a3590a74c6d9232f'},
    # The live route 3 file: CCA's own u8 and seen_ba, to show the endpoint rename names the same two tasks.
    'route3': {'path': 'site/src/data/questions-in-language-update.json',
               'sha256': '2583b5958c24e02898929c354e16653e50e33704aaaee37927e158f9d72d01dd'},
}
TEXT_PINS = {'adapter_runner', 'adapter_binding_review'}
# For the release manifest only (R1 section 1.5): the handoffs are context, never a copy source, and stay out of
# the blocks. Each bound hash is checked against the receipt or review that binds it.
HANDOFF_CONTEXT = {
    'cca_diagnostics': {'bound_sha256': 'b99ea68a507cec8c45f448a49e2db4f490fb723dbf57708ffca568bfa5feaa32',
                        'bound_by': 'diag_handoff_review'},
    'cca_adapter': {'bound_sha256': '61d424e9666b6488108581c5ec7ff6f1c6303afdc238795d75de5eb54ef9ea3d',
                    'bound_by': 'adapter_release_status',
                    'on_disk_sha256': 'f40400108526ca1e412945595f9377d6d3c03ffab91319a2bd400f85a757f625',
                    'difference': 'one inserted space in a table header; no word, figure or claim differs (R1)'},
    'wearable_transfer': {'bound_sha256': '1ee606a6766e9c92a76da31ac2c2f131e32c5bd24d624d94fff001efba85d82d',
                          'bound_by': 'wear_release_status'},
}
SERVED = {'dry_vs_wet': 'site/public/data/deployment-topics.json',      # must be the same bytes as the src copy
          'route3': 'site/public/data/questions-in-language-update.json'}
DRY_VS_WET_FILE = 'deployment-topics.json'                             # its served name, as export_codes cite it
STUDIES = ('cca_diagnostics', 'cca_adapter', 'wearable_transfer')
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'interval_method', 'levels', 'contrasts', 'undefined', 'not_run',
                'checks', 'limitations_keys', 'display_names', 'export_codes')

ENDPOINTS = {'u8': 'held8_accuracy', 'seen_ba': 'seen32_balanced_accuracy'}   # site id -> export spelling
STRATA = ('dry', 'wet', 'all')
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
NO_TRAINING, DETERMINISTIC = 'no training', 'deterministic fit'
SEED, DRAWS, LEVEL = 20261015, 2000, 0.95
METHOD = 'paired person bootstrap, percentile interval'
TOL = 1e-12

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
CROPPED_MATCH = 'cropped-spectrum match (no training)'
DISPLAY_NAMES = {
    'cca_diagnostics': {
        'CCA-RAW': 'CCA (no training)',
        'CCA-HANN-C': 'Hann-tapered CCA',
        'CCA-HANN-U': 'Hann-tapered CCA',
        'SUBSPACE-CROP': CROPPED_MATCH,
        'CHANNEL-JOINT': 'channel-energy average',
        'CHANNEL-HARMONIC': 'channel-energy average',
        'SHARED-RIDGE': 'shared ridge scorer',
    },
    'cca_adapter': {
        'ENERGY-FS': 'energy head',
        'ADAPT-FS': 'adapted head',
        'CROP-RESIDUAL': 'cropped match with learned correction',
        'RAW-RESIDUAL': 'CCA with learned correction',
        'CCA-CROP': CROPPED_MATCH,
        'CCA-RAW': 'CCA (no training)',
    },
    'wearable_transfer': {
        'RAW-RESIDUAL': 'CCA with learned correction',
        'CCA-RAW': 'matched CCA',
        'CCA-CROP': 'cropped-spectrum check (Wearable-102)',
    },
}
# The plan's name key rows this package owns (site name first, export codes second).
NAME_KEY = (
    ('CCA (no training)', 'CCA-RAW'),
    ('Hann-tapered CCA', 'CCA-HANN-C/U'),
    (CROPPED_MATCH, 'SUBSPACE-CROP in the diagnostics export, CCA-CROP in the adapter export: one set of scores'),
    ('channel-energy average', 'CHANNEL-JOINT/HARMONIC'),
    ('shared ridge scorer', 'SHARED-RIDGE'),
    ('energy head', 'ENERGY-FS'),
    ('adapted head', 'ADAPT-FS'),
    ('CCA with learned correction', 'RAW-RESIDUAL'),
    ('cropped match with learned correction', 'CROP-RESIDUAL'),
    ('cropped-spectrum check (Wearable-102)', 'CCA-CROP in the Wearable export'),
)
# Two definitions behind one site name; the protocol's arm text decides which is which.
VARIANTS = {'CCA-HANN-C': ('centred', 'then temporal centering'),
            'CCA-HANN-U': ('uncentred', 'without centering'),
            'CHANNEL-JOINT': ('joint reference span', 'joint6D harmonic-reference span'),
            'CHANNEL-HARMONIC': ('per-harmonic spans', 'for each of3harmonics')}
TRAINING_FREE = ('CCA-RAW', 'CCA-HANN-C', 'CCA-HANN-U', 'SUBSPACE-CROP', 'CHANNEL-JOINT', 'CHANNEL-HARMONIC')
TRANSITIONS = (('wrong_to_right', 'wrong_to_correct'), ('right_to_wrong', 'correct_to_wrong'),
               ('wrong_to_different_wrong', 'changed_wrong_to_wrong'), ('unchanged_right', 'unchanged_correct'),
               ('unchanged_wrong', 'unchanged_incorrect'), ('changed', 'changed'))
OUTCOMES = ('wrong_to_right', 'right_to_wrong', 'wrong_to_different_wrong', 'unchanged_right', 'unchanged_wrong')

# ---------------------------------------------------------------------------- limitations, not run, declared edits
# key -> (pinned input, JSON pointer, phrase the field must contain); pointer '' is a whole text record.
LIMITATION_SOURCES = {
    'cca_diagnostics': {
        'same_cohort_follow_up': ('diag_review', '/required_interpretation/1', 'fixed follow-up on the same11200'),
        'unadjusted_intervals': ('diag_review', '/required_interpretation/0', 'no multiplicity correction'),
        'candidates_known': ('diag_review', '/required_interpretation/2', 'excluded from supervised fitting'),
        'coordinates_before_scaler': ('diag_review', '/required_interpretation/3', 'before per-coordinate source scaling'),
        'no_isolated_cause': ('diag_review', '/required_interpretation/4', 'no isolated pure phase'),
        'crop_changes_metric': ('diag_review', '/required_interpretation/5', 'does not itself prove information destruction'),
        'earlier_heads_descriptive': ('diag_review', '/required_interpretation/6', 'quoted descriptively'),
        'identical_results_different_definitions': ('diag_review', '/accepted_findings/2',
                                                    'identical metrics alone do not establish identical scores'),
        'crop_vs_hann_unresolved': ('diag_review', '/accepted_findings/3', 'no established equivalence claim'),
        'bundled_contrast': ('diag_review', '/accepted_findings/4', 'bundled decoder/aggregation contrast'),
        'ridge_no_seen_gain': ('diag_review', '/accepted_findings/5', 'no demonstrated seen32 gain'),
        'six_row_spot_check': ('diag_protocol', '/audit/numerical', 'on6prespecified rows'),
    },
    'cca_adapter': {
        'same_cohort_follow_up': ('adapter_review', '/required_boundaries/0', 'BETA was previously exposed'),
        'separate_tasks': ('adapter_review', '/required_boundaries/1', 'different candidate counts'),
        'seeds_averaged': ('adapter_review', '/required_boundaries/2', 'Three seed accuracies are averaged'),
        'unadjusted_intervals': ('adapter_review', '/required_boundaries/3', 'descriptive/unadjusted'),
        'candidates_supplied': ('adapter_review', '/required_boundaries/4',
                                'supplied candidate frequencies are explicit analytic inputs'),
        'frequency_code_supplied': ('adapter_protocol', '/features/q', 'Exact original23D NUM code'),
        'no_ablation': ('adapter_review', '/required_boundaries/5', 'No standalone trunk/query ablation'),
        'protection_structural': ('adapter_review', '/required_boundaries/6', 'does not guarantee every decision improves'),
        'protection_bound': ('adapter_protocol', '/model/protection', 'pairwise bounded residual difference<=4logit units'),
        'transitions_share_of_all_decisions': ('adapter_protocol', '/metrics/residual_diagnostics',
                                               'denominator all task trials'),
        'canonical_correlations_from_cropped_match': ('adapter_protocol', '/features/z',
                                                      'Six descending canonical correlations'),
        'bundled_matching_operations': ('adapter_review', '/secondary_interpretations/0',
                                        'does not isolate channel adaptation'),
        'residual_not_uniformly_better': ('adapter_review', '/secondary_interpretations/2',
                                          'residual form is not uniformly superior'),
        'raw_vs_crop_baseline_access': ('adapter_review', '/secondary_interpretations/3',
                                        'does not show learned temporal information extraction'),
        'uncalibrated_scores': ('adapter_protocol', '/model/probabilities', 'not calibrated probabilities'),
    },
    'wearable_transfer': {
        'stored_amplitude_units': ('wear_review', '/mandatory_scope_limits/0',
                                   'Unknown target physical units remain unresolved'),
        'window_onset_and_other_changes': ('wear_review', '/mandatory_scope_limits/1', '0.14 seconds after stimulus onset'),
        'no_equivalence_no_single_cause': ('wear_review', '/mandatory_scope_limits/2', 'Neither equivalence'),
        'candidates_supplied': ('wear_review', '/mandatory_scope_limits/3',
                                'Candidate frequencies are supplied to both methods'),
        'prior_use_overlap_snapshot': ('wear_review', '/mandatory_scope_limits/4', 'possible participant overlap'),
        'mean_over_105_models': ('wear_review', '/review_findings/2', 'not an ensemble'),
        'model_score_contains_cca': ('wear_review', '/review_findings/3', 'fixed raw CCA score inside RAW-RESIDUAL'),
        'intervals_conditional_on_models': ('wear_review', '/review_findings/4', 'conditional on the fixed source models'),
        'cropped_check_diagnostic_only': ('wear_review', '/review_findings/1', 'CCA-CROP as secondary'),
        'not_comparable_with_beta_tasks': ('wear_protocol', '/metrics/not_comparable',
                                           'compare against target matchedCCA only'),
        'cca_harmonic_count': ('wear_cca_definition', '/answer', 'differ in one setting: the harmonic count'),
    },
}
CONTRAST_LIMITATIONS = {
    'cca_diagnostics': {'CCA-HANN-U minus CCA-HANN-C': 'identical_results_different_definitions',
                        'SUBSPACE-CROP minus CCA-HANN-U': 'crop_vs_hann_unresolved',
                        'SUBSPACE-CROP minus CHANNEL-JOINT': 'bundled_contrast',
                        'CHANNEL-HARMONIC minus CHANNEL-JOINT': 'identical_results_different_definitions',
                        'SHARED-RIDGE minus CHANNEL-HARMONIC': 'ridge_no_seen_gain'},
    'cca_adapter': {'ADAPT-FS minus ENERGY-FS': 'bundled_matching_operations',
                    'CROP-RESIDUAL minus ADAPT-FS': 'residual_not_uniformly_better',
                    'RAW-RESIDUAL minus CROP-RESIDUAL': 'raw_vs_crop_baseline_access'},
    'wearable_transfer': {},
}
# item -> (pinned input, JSON pointer, phrase); nothing in this release runs these items later.
NOT_RUN_SOURCES = {
    'cca_diagnostics': {
        'paired contrast with the earlier complex-spectrum heads': (
            'diag_review', '/required_interpretation/6', 'no new preregistered paired contrast'),
    },
    'cca_adapter': {
        'filter-bank CCA': ('adapter_binding_review', '', 'Filter-bank CCA and supervised spatial templates were not compared'),
        'supervised spatial templates': ('adapter_binding_review', '',
                                         'Filter-bank CCA and supervised spatial templates were not compared'),
        'trunk or query ablation': ('adapter_review', '/required_boundaries/5', 'No standalone trunk/query ablation'),
        'simpler learned head on the CCA features': ('adapter_review', '/required_boundaries/5',
                                                     'simpler learned-head comparison'),
    },
    'wearable_transfer': {
        'equivalence margin': ('wear_review', '/mandatory_scope_limits/2', 'Neither equivalence'),
        'one-factor ablations of units, window onset, hardware, people or frequency grid': (
            'wear_review', '/mandatory_scope_limits/1', 'not separately ablated'),
        'target adaptation or retraining': ('wear_protocol', '/methods/selection', 'No retraining'),
    },
}
DECLARED_EDITS = {
    'cca_diagnostics': (
        'private_root not selected',
        'job block not selected (process id, timestamps, producer status)',
        'exported_at_utc and the hashes of private run receipts not selected; the export is pinned by its own hash',
        'summary.release_status and release_eligibility not selected; the release review supersedes them',
        'audit.analytic.rows and gates.l0c-equivalence.rows not selected; only the number of checked rows is kept',
        'gates.preflight.reference_ranks reduced to the common dimension and the counts of candidates and domains',
        'summary.random_pairing ranges not selected; permutation means kept',
        'privacy string not selected',
        'held8_accuracy and seen32_balanced_accuracy named u8 and seen_ba in ids (route 3 spelling of the same tasks)',
        'training-free scorers carry "no training" and the ridge scorer "deterministic fit" in place of seeds',
    ),
    'cca_adapter': (
        'status not selected; state/release-status.json supersedes it',
        'indices_sha256 not selected (hash of private bootstrap indices)',
        'per_seed_descriptive not selected',
        'privacy string not selected',
        'residual_diagnostics.CROP-RESIDUAL not selected; RAW-RESIDUAL transitions kept',
        'protected_trials published as protected_instances, labelled as prediction instances across 3 seeds and '
        '5 rotations',
        'interval seed taken from the numerical review and the percentile rule from the pinned runner',
        'held8_accuracy and seen32_balanced_accuracy named u8 and seen_ba in ids (route 3 spelling of the same tasks)',
        'CCA baselines carry "no training" in place of seeds',
    ),
    'wearable_transfer': (
        'free-text scope, limitations, rights and citations strings not selected (missing spaces; the page writes '
        'its own copy from limitations_keys)',
        'strata.*.metrics.RAW-RESIDUAL_minus_CCA-CROP not selected; the cropped-spectrum check is a level only',
        'status, schema and protocol_id not selected; the export is pinned by its own hash',
        'CCA levels carry "no training" in place of seeds',
    ),
}

# ---------------------------------------------------------------------------- what no block may carry
REFUSED_KEYS = set(FORBIDDEN_KEYS) | {
    'pid', 'job', 'private_root', 'rows', 'indices_sha256', 'per_seed_descriptive', 'privacy', 'status',
    'release_status', 'release_eligibility', 'exported_at_utc', 'updated_at', 'protected_trials', 'range', 'path',
    'handoff_path', 'export_path', 'reference_ranks', 'chain'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_seed',
                         'prediction', 'probabilit', 'feature', 'private', 'path', 'host', 'elapsed', 'seconds',
                         'timing', 'checkpoint', 'device', 'subject', '_utc')
REFUSED_TEXT = re.compile(
    r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root|var|opt)\b|(?:^|[\s(])~/|trx|gal4|bci_arena|\btwu\b'
    r'|\bpending\b|\bsuperseded\b|dipankar|\b55\s*%|\b0\.55\b|fifty[- ]five|五成五', re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
RANKING = re.compile(r'\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|state[- ]of[- ]the[- ]art|superior'
                     r'|significan', re.IGNORECASE)


# ---------------------------------------------------------------------------- helpers
def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool)


def close(a, b, label, tol=TOL):
    require(number(a) and number(b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


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


def pointer(*tokens):
    """An RFC 6901 JSON pointer from its reference tokens."""
    return ''.join('/' + str(t).replace('~', '~0').replace('/', '~1') for t in tokens)


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
    text = resolve(docs[name], ptr)
    require(isinstance(text, str) and phrase in text, f'{label}: {name} {ptr} does not state {phrase!r}')


def bound(value, digest, label):
    require(value == digest, f'{label}: binds {str(value)[:12]}, pinned {digest[:12]}')


def interval(lo, hi, point, label, lower=0.0, upper=1.0):
    require(all(number(v) for v in (lo, hi, point)), f'{label}: not a finite interval')
    require(lower <= lo <= point <= hi <= upper, f'{label}: the interval does not hold its point')
    return [lo, hi]


def level(metric, people, seeds, origin, label, ci='ci95'):
    """A level copied from an export metric block {mean, <ci>}."""
    require(isinstance(metric, dict) and isinstance(metric.get(ci), list) and len(metric[ci]) == 2, f'{label}: no interval')
    return {'estimate': metric['mean'], 'interval': interval(*metric[ci], metric['mean'], label), 'unit': PROPORTION,
            'people': people, 'seeds': seeds, 'origin': origin}


def contrast(metric, role, left, right, levels, people, seeds, label, ci='ci95'):
    """A paired contrast, refused unless it is the difference of its two levels."""
    require(isinstance(metric, dict) and isinstance(metric.get(ci), list) and len(metric[ci]) == 2, f'{label}: no interval')
    est = metric['mean']
    close(est, levels[left]['estimate'] - levels[right]['estimate'], f'{label} is not the difference of its levels')
    iv = interval(*metric[ci], est, label, lower=-1.0)
    return {'role': role, 'left': left, 'right': right, 'estimate': est, 'interval': iv, 'unit': DIFFERENCE,
            'people': people, 'seeds': seeds, 'flags': {'interval_includes_zero': iv[0] <= 0 <= iv[1]}}


def numeric_leaves(a, b, trail=''):
    """(pointer, a, b) for every number of a, at the same place in b; every other leaf must be equal."""
    if isinstance(a, dict):
        require(isinstance(b, dict), f'{trail}: shape differs')
        for k, v in a.items():
            require(k in b, f'{trail}/{k}: missing')
            yield from numeric_leaves(v, b[k], f'{trail}/{k}')
    elif isinstance(a, list):
        require(isinstance(b, list) and len(a) == len(b), f'{trail}: length differs')
        for i, (x, y) in enumerate(zip(a, b)):
            yield from numeric_leaves(x, y, f'{trail}/{i}')
    elif number(a):
        require(number(b), f'{trail}: not a number')
        yield trail, a, b
    else:
        require(a == b, f'{trail}: {a!r} differs from {b!r}')


def protocol_count(text, pattern, label):
    m = re.search(pattern, text)
    require(m is not None, f'{label}: the pinned protocol does not state it')
    return int(m.group(1))


def input_hash(protocol, suffix):
    hashes = [v for k, v in protocol['expected_input_hashes'].items() if k.endswith(suffix)]
    require(len(hashes) == 1, f'the protocol pins no single {suffix}')
    return hashes[0]


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
    require(set(codes) <= set(DISPLAY_NAMES[study]), f'{study}: no display name for {set(codes) - set(DISPLAY_NAMES[study])}')
    return {c: DISPLAY_NAMES[study][c] for c in codes}


def route3_endpoints(docs, cca_levels, label):
    """u8 and seen_ba name the same tasks as the export's held-out 8-way and seen 32-way: CCA's own value agrees."""
    r3 = resolve(docs['route3'], '/results/questions-in-language/descriptive/P-ssvep-L0/levels')
    for e in ENDPOINTS:
        require(cca_levels[f'CCA-RAW/{e}']['estimate'] == r3[f'CCA {e}']['estimate'],
                f'{label}: CCA-RAW/{e} is not route 3\'s CCA {e}')


# ---------------------------------------------------------------------------- CCA mechanism diagnostics (card 5)
def diagnostics_block(docs, digests):
    ex, protocol, rr, hv, hr = (docs[k] for k in ('diag_export', 'diag_protocol', 'diag_review',
                                                  'diag_hash_verification', 'diag_handoff_review'))
    bound(rr['aggregate_evidence_sha256'], digests['diag_export'], 'diagnostics review export')
    bound(rr['protocol_sha256'], digests['diag_protocol'], 'diagnostics review protocol')
    bound(rr['execution_freeze_sha256'], digests['diag_freeze'], 'diagnostics review freeze')
    bound(rr['independent_hash_verification_sha256'], digests['diag_hash_verification'], 'diagnostics review hashes')
    bound(hv['export_sha256'], digests['diag_export'], 'diagnostics hash verification export')
    bound(hv['freeze_sha256'], digests['diag_freeze'], 'diagnostics hash verification freeze')
    bound(hr['aggregate_evidence_sha256'], digests['diag_export'], 'diagnostics handoff review export')
    bound(hr['result_release_review_sha256'], digests['diag_review'], 'diagnostics handoff review')
    bound(ex['hashes']['protocol.json'], digests['diag_protocol'], 'diagnostics export protocol')
    bound(ex['hashes']['execution-freeze.json'], digests['diag_freeze'], 'diagnostics export freeze')
    require(rr['accepted'] is True and rr['accepted_for_aggregate_handoff'] is True and rr['blockers'] == [],
            'diagnostics: the release review did not accept the aggregate')
    require(hr['accepted'] is True and hr['blockers'] == [], 'diagnostics: the handoff review did not accept')
    require(hv['passed'] is True, 'diagnostics: the hash verification did not pass')

    s = ex['summary']
    require(s['aggregate_only'] is True, 'diagnostics: the export is not aggregate-only')
    arms = tuple(protocol['arms'])
    require(tuple(s['arms']) == arms and set(arms) == set(DISPLAY_NAMES['cca_diagnostics'])
            and set(TRAINING_FREE) | {'SHARED-RIDGE'} == set(arms), 'diagnostics: the scorer set changed')

    rule = protocol['metrics']['bootstrap']
    require(s['bootstrap_seed'] == SEED and f'seed{SEED}' in rule, 'diagnostics: bootstrap seed')
    require(s['bootstrap_n'] == DRAWS and rule.startswith(f'{DRAWS}resamples'), 'diagnostics: bootstrap draws')
    require(s['person_count'] == 70 and 'of70people' in rule, 'diagnostics: people')
    require('same indices for allarms andcontrasts' in rule and 'percentile95CI' in rule, 'diagnostics: bootstrap rule')
    require('no multiplicity correction' in protocol['metrics']['multiplicity'], 'diagnostics: multiplicity')
    people = s['person_count']

    split = protocol['split']
    require({len(v) for v in split['rotations'].values()} == {8} and split['source_queries_per_fit'] == 32
            and len(split['rotations']) == s['rotations'] == 5, 'diagnostics: the frequency rotations changed')
    require(split['ridge_fits'] == ex['job']['completed_ridge_fits'] == ex['job']['total_ridge_fits'] == 35,
            'diagnostics: ridge fits incomplete')
    require('deterministic float64 solve' in protocol['ridge']['selection'], 'diagnostics: the ridge is not deterministic')
    require(protocol['harmonics'] == [1, 2, 3] and protocol['shape'][0] == 11200, 'diagnostics: harmonics or windows')
    chance = s['random_pairing']['exact_expectation']
    close(chance[ENDPOINTS['u8']], 1 / 8, 'held-out chance')
    close(chance[ENDPOINTS['seen_ba']], 1 / 32, 'seen chance')

    seeds_of = {code: NO_TRAINING for code in TRAINING_FREE} | {'SHARED-RIDGE': DETERMINISTIC}
    levels, codes = {}, {}
    for code in arms:
        for e, src in ENDPOINTS.items():
            lid = f'{code}/{e}'
            levels[lid] = level(s['arms'][code][src], people, seeds_of[code], 'new', f'diagnostics {lid}')
            codes[lid] = ['#' + pointer('summary', 'arms', code, src)]
    route3_endpoints(docs, levels, 'diagnostics')

    contrasts = {}
    planned = [f'{left} minus {right}' for left, right in protocol['metrics']['contrasts']]
    require(list(s['contrasts']) == planned, 'diagnostics: the export contrasts differ from the protocol')
    stated(docs, 'diag_protocol', '/interpretation/3',
           'jointly changes channel mixing, reference-coefficient optimization and aggregation', 'diagnostics bundle')
    for (left, right), key in zip(protocol['metrics']['contrasts'], planned):
        seeds = DETERMINISTIC if 'SHARED-RIDGE' in (left, right) else NO_TRAINING
        pair = []
        for e, src in ENDPOINTS.items():
            cid = f'{key}/{e}'
            c = contrast(s['contrasts'][key][src], 'prespecified', f'{left}/{e}', f'{right}/{e}', levels, people, seeds,
                         f'diagnostics {cid}')
            contrasts[cid], codes[cid] = c, ['#' + pointer('summary', 'contrasts', key, src)]
            pair.append(c)
        if all(c['estimate'] == 0.0 and c['interval'] == [0.0, 0.0] for c in pair):
            require(all(levels[f'{left}/{e}'] == levels[f'{right}/{e}'] for e in ENDPOINTS),
                    f'diagnostics: {key} is zero but its levels differ')
            for c in pair:
                c['flags']['identical_results'] = True
        if (left, right) == ('SUBSPACE-CROP', 'CHANNEL-JOINT'):
            for c in pair:
                c['flags']['bundles'] = ['cross-channel mixing', 'fitting the reference coefficients', 'aggregation']

    scorers = []
    for code in arms:
        row = {'code': code, 'training': NO_TRAINING if code in TRAINING_FREE else 'ridge fitted on source people'}
        if code in VARIANTS:
            name, phrase = VARIANTS[code]
            require(phrase in protocol['arms'][code], f'diagnostics: {code} is not the {name} variant')
            row['variant'] = name
        if code == 'SHARED-RIDGE':
            row.update(fits=split['ridge_fits'], source_windows_per_fit=split['source_rows_per_fit'],
                       seen_frequencies_per_fit=split['source_queries_per_fit'])
        scorers.append(row)
    design = {
        'dataset': {'name': 'BETA', 'people': people, 'targets': 40, 'windows': protocol['shape'][0],
                    'person_folds': split['folds'], 'frequency_rotations': s['rotations']},
        'endpoints': {'u8': {'candidate_count': 8, 'chance': chance[ENDPOINTS['u8']]},
                      'seen_ba': {'candidate_count': 32, 'chance': chance[ENDPOINTS['seen_ba']]}},
        'harmonics': len(protocol['harmonics']),
        'training_free_scorers': len(TRAINING_FREE),
        'ridge_fits': split['ridge_fits'],
        'scorers': scorers,
    }

    audit, gates, rp = ex['audit'], ex['gates'], s['random_pairing']
    analytic = audit['analytic']['arms']
    require(audit['passed'] is True and audit['analytic']['passed'] is True
            and all(v['passed'] and v.get('argmax_equal', True) for v in analytic.values()), 'diagnostics: audit')
    require(all(gates[g]['passed'] for g in ('raw-reconstruction', 'l0c-equivalence', 'preflight'))
            and all(gates['raw-reconstruction']['identical_argmax'].values()), 'diagnostics: a gate failed')
    ranks = gates['preflight']['reference_ranks']
    require(all(r == 6 for v in ranks.values() for r in v) and {len(v) for v in ranks.values()} == {40},
            'diagnostics: a reference subspace is not six-dimensional')
    require(audit['ridge_refits'] == split['ridge_fits'] and audit['all_ridge_argmax_equal'] is True
            and audit['all_person_metrics_match'] is True and audit['all_aggregate_bootstraps_and_contrasts_match'] is True,
            'diagnostics: the independent recomputation')
    require(rp['descriptive_only'] is True and rp['seed'] == SEED and tuple(rp['arms']) == arms, 'diagnostics: pairing')
    checks = {
        'release_review': {'accepted': True, 'blockers': len(rr['blockers'])},
        'handoff_review': {'accepted': True, 'blockers': len(hr['blockers'])},
        'independent_hash_verification': {'passed': True, 'artifact_receipts': hv['verified_artifact_receipts'],
                                          'sealed_artifacts': hv['verified_sealed_artifacts']},
        'raw_cca_reconstruction': {'passed': True, 'windows': protocol['shape'][0],
                                   'max_absolute_error': gates['raw-reconstruction']['max_absolute_error'],
                                   'identical_argmax_sets': len(gates['raw-reconstruction']['identical_argmax'])},
        'cropped_coordinates_match_earlier_cache': {
            'passed': True, 'rows_checked': len(gates['l0c-equivalence']['rows']),
            'coordinate_max_error': gates['l0c-equivalence']['coordinate_max_error'],
            'score_max_error': gates['l0c-equivalence']['cca_max_error']},
        'independent_analytic_spot_check': {'passed': True, 'rows_checked': len(audit['analytic']['rows']),
                                            'scorers_checked': len([k for k in analytic if k in arms]),
                                            'max_absolute_error': max(v['max_absolute_error'] for v in analytic.values())},
        'independent_ridge_refits': {'passed': True, 'refits': audit['ridge_refits'], 'of': split['ridge_fits'],
                                     'max_score_error': audit['ridge_max_score_error']},
        'person_metrics_bootstraps_and_contrasts_recomputed': {'passed': True},
        'reference_subspace_preflight': {'passed': True, 'tests': gates['preflight']['tests'],
                                         'reference_subspace_dimension': 6, 'candidates': 40, 'domains': len(ranks)},
        'random_pairing': {'descriptive_only': True, 'permutations': rp['permutations'], 'seed': rp['seed'],
                           'exact_expectation': {e: chance[src] for e, src in ENDPOINTS.items()},
                           'means': {code: {e: rp['arms'][code][src]['mean'] for e, src in ENDPOINTS.items()}
                                     for code in arms}},
    }
    return {
        'source_sha256': digests['diag_export'],
        'review_sha256': digests['diag_review'],
        'protocol_sha256': digests['diag_protocol'],
        'freeze_sha256': digests['diag_freeze'],
        'hash_verification_sha256': digests['diag_hash_verification'],
        'handoff_review_sha256': digests['diag_handoff_review'],
        'interval_method': {'method': METHOD, 'draws': s['bootstrap_n'], 'seed': s['bootstrap_seed'], 'level': LEVEL},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('cca_diagnostics', contrasts),
        'undefined': [],
        'not_run': not_run('cca_diagnostics', docs),
        'checks': checks,
        'limitations_keys': limitations('cca_diagnostics', docs),
        'display_names': display_names('cca_diagnostics', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- CCA adapter (card 6)
def adapter_block(docs, digests, diagnostics):
    ex, protocol, nr, ir, rs = (docs[k] for k in ('adapter_export', 'adapter_protocol', 'adapter_numerical_review',
                                                  'adapter_review', 'adapter_release_status'))
    bound(rs['aggregate_sha256'], digests['adapter_export'], 'adapter release receipt export')
    bound(rs['numerical_review_sha256'], digests['adapter_numerical_review'], 'adapter release receipt numerical review')
    bound(rs['interpretation_review_sha256'], digests['adapter_review'], 'adapter release receipt review')
    bound(rs['execution_freeze_sha256'], digests['adapter_freeze'], 'adapter release receipt freeze')
    ev = ir['evidence_sha256']
    bound(ev['exports/CCA Adapter Aggregate Results.json'], digests['adapter_export'], 'adapter review export')
    bound(ev['protocol.json'], digests['adapter_protocol'], 'adapter review protocol')
    bound(ev['execution-freeze.json'], digests['adapter_freeze'], 'adapter review freeze')
    bound(ev['review/release-numerical-audit.json'], digests['adapter_numerical_review'], 'adapter review numerical')
    frozen = nr['checks']['frozen_pins']
    bound(frozen['protocol_sha256'], digests['adapter_protocol'], 'adapter numerical review protocol')
    bound(frozen['execution_freeze_sha256'], digests['adapter_freeze'], 'adapter numerical review freeze')
    bound(frozen['code_sha256']['run_adapter.py'], digests['adapter_runner'], 'adapter numerical review runner')
    bound(docs['adapter_freeze']['code_sha256']['run_adapter.py'], digests['adapter_runner'], 'adapter freeze runner')
    bound(docs['adapter_freeze']['protocol_sha256'], digests['adapter_protocol'], 'adapter freeze protocol')
    bound(nr['checks']['artifact_integrity']['aggregate_sha256'], digests['adapter_export'], 'adapter numerical export')
    require(rs['status'] == 'audited_complete_aggregate_handoff_ready' and rs['incomplete_arms'] == [],
            'adapter: the release receipt is not complete')
    require(nr['passed'] is True and nr['status'] == 'passed_independent_release_review'
            and nr['remaining_blockers'] == [] and all(c['passed'] for c in nr['checks'].values()),
            'adapter: the numerical review did not pass')
    require(ir['passed'] is True and ir['ready_for_handoff'] is True and ir['remaining_blockers'] == []
            and all(v is True for v in ir['aggregate_only_consistency_checks'].values()),
            'adapter: the interpretation review did not pass')
    r1 = docs['adapter_binding_review']
    require(digests['adapter_export'] in r1 and 'Safe, with five required copy fixes' in r1,
            'adapter: the binding review does not clear this export')

    # The export, leaf by leaf, against the numerical review's own recomputed aggregate.
    pairs = list(numeric_leaves(nr['aggregate_findings'], ex))
    worst = max(abs(a - b) for _, a, b in pairs)
    require(worst <= TOL, f'adapter: the export differs from the numerical review by {worst!r}')

    rec = nr['checks']['independent_numerical_recomputation']
    require(ex['unit'] == 'person' and ex['resamples'] == rec['paired_person_bootstrap_resamples'] == DRAWS,
            'adapter: bootstrap unit or draws')
    require(rec['bootstrap_seed'] == SEED and f'seed{SEED}' in protocol['metrics']['bootstrap']
            and 'paired' in protocol['metrics']['bootstrap'], 'adapter: bootstrap seed')
    require('np.percentile(samples, [2.5, 97.5])' in docs['adapter_runner'], 'adapter: the runner takes no percentiles')
    require('no multiplicity adjustment' in protocol['metrics']['multiplicity'], 'adapter: multiplicity')
    stated(docs, 'adapter_review', '/required_boundaries/3', 'conditions on fixed fitted models/splits/seeds',
           'adapter interval conditioning')

    split, model, training = protocol['split'], protocol['model'], protocol['training']
    dz = docs['diag_protocol']
    require(split['folds'] == dz['split']['folds'] and split['rotations'] == dz['split']['rotations'],
            'adapter: the splits are not the diagnostics splits')
    require(input_hash(protocol, '/epochs250.npy') == input_hash(dz, '/epochs250.npy'), 'adapter: different windows')
    require(ex['n_people'] == diagnostics['design']['dataset']['people'], 'adapter: people')
    seeds = split['seeds']
    require(len(seeds) == 3 and training['seeds'] == seeds, 'adapter: training seeds')
    require(ex['seed_aggregation'] == 'mean3seeds then5rotations then70people', 'adapter: seed aggregation')
    trained, baselines = tuple(protocol['arms']), tuple(protocol['baselines'])
    arms = trained + baselines
    require(tuple(ex['arms']) == arms and set(arms) == set(DISPLAY_NAMES['cca_adapter']), 'adapter: the arm set changed')
    require(not any(n in a.upper() for a in arms for n in ('FBCCA', 'FILTER-BANK', 'TRCA')), 'adapter: an untested arm')
    params = protocol_count(model['adapter'], r'ENERGY/ADAPT have(\d+)parameters', 'adapter parameters')
    params_residual = protocol_count(model['adapter'], r'residual arm adds one global-bias scalar \((\d+)\)',
                                     'residual parameters')
    require(params_residual == params + 1, 'adapter: parameter counts')
    require(nr['checks']['complete_training']['main_fits'] == split['total_main_fits'] == 420
            and split['fits_per_arm'] * len(trained) == 420, 'adapter: fit count')
    # The baselines are the diagnostics' own score arrays, pinned as inputs of this study.
    for name in ('/analytic/SUBSPACE-CROP.npy', '/analytic/CCA-RAW.npy'):
        input_hash(protocol, name)
    people = ex['n_people']

    per_seed = ex['per_seed_descriptive']
    levels, codes = {}, {}
    reused = {'CCA-RAW': 'CCA-RAW', 'CCA-CROP': 'SUBSPACE-CROP'}
    for code in arms:
        require(len(per_seed[code]) == (1 if code in baselines else len(seeds)), f'adapter: {code} seed count')
        for e, src in ENDPOINTS.items():
            lid = f'{code}/{e}'
            if code in baselines:
                lv = level(ex['arms'][code][src], people, NO_TRAINING, 'reused_cca_diagnostics', f'adapter {lid}')
                twin = diagnostics['levels'][f'{reused[code]}/{e}']
                require({k: lv[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')} ==
                        {k: twin[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')},
                        f'adapter {lid} differs from diagnostics {reused[code]}/{e}')
                require(DISPLAY_NAMES['cca_adapter'][code] == DISPLAY_NAMES['cca_diagnostics'][reused[code]],
                        f'adapter {code}: two names for one set of scores')
                codes[lid] = ['#' + pointer('arms', code, src),
                              'cca_diagnostics#' + pointer('summary', 'arms', reused[code], src)]
            else:
                lv = level(ex['arms'][code][src], people, len(seeds), 'new', f'adapter {lid}')
                codes[lid] = ['#' + pointer('arms', code, src)]
            levels[lid] = lv
    route3_endpoints(docs, levels, 'adapter')

    planned = [tuple(p) for p in protocol['metrics']['contrasts']]
    require([(c['left'], c['right']) for c in ex['contrasts']] == planned, 'adapter: contrasts differ from the protocol')
    stated(docs, 'adapter_protocol', '/model/ENERGY-FS', 'First6 standardized candidate coordinates zero', 'energy head')
    stated(docs, 'adapter_protocol', '/features/z', 'Same cropped complex coordinates as diagnostics', 'adapter inputs')
    contrasts = {}
    for i, c_ex in enumerate(ex['contrasts']):
        left, right = c_ex['left'], c_ex['right']
        key = f'{left} minus {right}'
        n_seeds = len(seeds) if left in trained or right in trained else NO_TRAINING
        for e, src in ENDPOINTS.items():
            cid = f'{key}/{e}'
            c = contrast(c_ex['metrics'][src], 'prespecified', f'{left}/{e}', f'{right}/{e}', levels, people, n_seeds,
                         f'adapter {cid}')
            if (left, right) == ('ADAPT-FS', 'ENERGY-FS'):
                c['flags']['bundles'] = ['several matching operations']
                c['flags']['added_input'] = {'canonical_correlations': 6, 'computed_on': CROPPED_MATCH}
            contrasts[cid], codes[cid] = c, ['#' + pointer('contrasts', i, 'metrics', src)]
    # The adapted head against CCA alone has no planned contrast and no interval; one that appears is refused.
    require(not any({c['left'].split('/')[0], c['right'].split('/')[0]} == {'ADAPT-FS', 'CCA-RAW'}
                    for c in contrasts.values()), 'adapter: a contrast of ADAPT-FS against CCA-RAW was not planned')
    stated(docs, 'adapter_review', '/secondary_interpretations/1', 'no unplanned interval is introduced', 'adapter undefined')
    undefined = [{'contrast': 'ADAPT-FS minus CCA-RAW', 'reason': 'not_a_planned_contrast'}]

    # Transitions: shares of all decisions on the task; five outcomes, exhaustive; net equals the paired gain.
    stated(docs, 'adapter_protocol', '/metrics/residual_diagnostics', 'denominator all task trials', 'denominator')
    stated(docs, 'adapter_protocol', '/metrics/residual_diagnostics',
           'Protected counts are prediction instances across3seeds and5rotations', 'protected counts')
    rd = ex['residual_diagnostics']
    margins = set()
    for arm, base in (('RAW-RESIDUAL', 'CCA-RAW'), ('CROP-RESIDUAL', 'CCA-CROP')):
        for e, src in ENDPOINTS.items():
            t = rd[arm][src]
            sh = {k: t[s] for k, s in TRANSITIONS}
            require(all(number(v) and 0 <= v <= 1 for v in sh.values()), f'adapter {arm} {e}: a share out of range')
            close(sum(sh[k] for k in OUTCOMES), 1.0, f'adapter {arm} {e}: the five outcomes do not sum to one')
            close(sh['changed'], sh['wrong_to_right'] + sh['right_to_wrong'] + sh['wrong_to_different_wrong'],
                  f'adapter {arm} {e}: changed is not the sum of the three changes')
            close(sh['wrong_to_right'] - sh['right_to_wrong'], contrasts[f'{arm} minus {base}/{e}']['estimate'],
                  f'adapter {arm} {e}: wrong to right minus right to wrong is not the paired gain')
            close(sh['unchanged_right'] + sh['right_to_wrong'], levels[f'{base}/{e}']['estimate'],
                  f'adapter {arm} {e}: the transitions do not start from {base}')
            require(count(t['protected_trials']) and t['protected_flips'] == 0, f'adapter {arm} {e}: a protected flip')
            margins.add(t['protected_margin'])
    require(len(margins) == 1, 'adapter: the protected margin is not one value')
    margin = margins.pop()
    scale = protocol_count(model['CROP-RESIDUAL'], r'logits=(\d+)\*\(rho_crop-0\.5\)', 'logit scale')
    bound_units = protocol_count(model['protection'], r'difference<=(\d+)logit units', 'residual bound')
    require(number(margin) and abs(margin - bound_units / scale) <= 2e-6, 'adapter: the protected margin is not 4/20')
    raw = rd['RAW-RESIDUAL']
    transitions = {
        'arm': 'RAW-RESIDUAL', 'against': 'CCA-RAW', 'unit': 'share of all decisions on the task',
        'averaged_over': 'three seeds, then five rotations, then 70 people',
        'u8': {'denominator': 'all held-out decisions', **{k: raw[ENDPOINTS['u8']][s] for k, s in TRANSITIONS}},
        'seen_ba': {'denominator': 'all seen decisions', **{k: raw[ENDPOINTS['seen_ba']][s] for k, s in TRANSITIONS}},
        'export_codes': ['#' + pointer('residual_diagnostics', 'RAW-RESIDUAL')],
    }
    protection = {'protected_margin': margin, 'scale': 'CCA correlation', 'protected_flips': 0,
                  'protected_instances': {e: raw[src]['protected_trials'] for e, src in ENDPOINTS.items()},
                  'instances_unit': 'prediction instances across 3 seeds and 5 rotations',
                  'export_codes': ['#' + pointer('residual_diagnostics', 'RAW-RESIDUAL', ENDPOINTS['u8'],
                                                 'protected_margin')]}

    design = {
        'dataset': dict(diagnostics['design']['dataset'], training_seeds=len(seeds)),
        'endpoints': copy.deepcopy(diagnostics['design']['endpoints']),
        'arms': [{'code': c, 'training': 'trained on source people and seen frequencies', 'fits': split['fits_per_arm'],
                  'parameters': params_residual if c.endswith('RESIDUAL') else params} for c in trained]
        + [{'code': c, 'training': NO_TRAINING} for c in baselines],
        'trained_fits': split['total_main_fits'],
        'training_epochs': training['epochs'],
        'steps_per_fit': training['steps_per_fit'],
    }
    ct, ai, fa = (nr['checks'][k] for k in ('complete_training', 'artifact_integrity', 'features_and_admission'))
    require(ct['main_fits'] == 420 and ct['independent_refit_models_exact'] is True
            and ct['functional_reconstruction_max_logit_error'] == 0.0, 'adapter: training checks')
    checks = {
        'numerical_review': {'passed': True, 'blockers': len(nr['remaining_blockers'])},
        'interpretation_review': {'passed': True, 'blockers': len(ir['remaining_blockers'])},
        'release_receipt': {'complete': True, 'incomplete_arms': len(rs['incomplete_arms'])},
        'binding_review': {'cleared': True},
        'export_equals_numerical_review': {'passed': True, 'numeric_values': len(pairs),
                                           'max_absolute_difference': worst, 'tolerance': TOL},
        'complete_training': {'passed': True, 'fits': ct['main_fits'], 'independent_refits': ct['independent_refits'],
                              'independent_refits_exact': True, 'reconstructions': ct['functional_reconstruction_gates'],
                              'reconstruction_max_logit_error': ct['functional_reconstruction_max_logit_error']},
        'artifact_integrity': {'passed': ai['passed'], 'receipt_targets_rehashed': ai['receipt_targets_rehashed'],
                               'seal_entries': ai['seal_inventory_entries']},
        'analytic_inputs': {'passed': fa['passed'], 'source_scaler_checks': fa['fresh_source_split_and_scaler_checks'],
                            'rows_checked': fa['independent_feature_spotcheck_rows']},
        'independent_recomputation': {'passed': rec['passed'], 'max_metric_error': rec['max_private_metric_absolute_error'],
                                      'outcomes_exhaustive': rec['five_outcomes_exclusive_and_exhaustive'] is True,
                                      'net_equals_gain': rec['rescue_minus_harm_equals_accuracy_delta'] is True},
        'same_scores_as_diagnostics': {'passed': True, 'codes': sorted(reused)},
    }
    return {
        'source_sha256': digests['adapter_export'],
        'review_sha256': digests['adapter_review'],
        'numerical_review_sha256': digests['adapter_numerical_review'],
        'release_receipt_sha256': digests['adapter_release_status'],
        'protocol_sha256': digests['adapter_protocol'],
        'freeze_sha256': digests['adapter_freeze'],
        'runner_sha256': digests['adapter_runner'],
        'binding_review_sha256': digests['adapter_binding_review'],
        'interval_method': {'method': METHOD, 'draws': ex['resamples'], 'seed': rec['bootstrap_seed'], 'level': LEVEL,
                            'conditional_on': 'the fitted models and the three fixed training seeds'},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('cca_adapter', contrasts),
        'transitions': transitions,
        'protection': protection,
        'undefined': undefined,
        'not_run': not_run('cca_adapter', docs),
        'checks': checks,
        'limitations_keys': limitations('cca_adapter', docs),
        'display_names': display_names('cca_adapter', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- Wearable-102 transfer (card 7)
def wearable_block(docs, digests, adapter):
    ex, protocol, fz, ir, ns, rs, note, dvw = (docs[k] for k in (
        'wear_export', 'wear_protocol', 'wear_freeze', 'wear_review', 'wear_numerical_summary', 'wear_release_status',
        'wear_cca_definition', 'dry_vs_wet'))
    bound(rs['export_sha256'], digests['wear_export'], 'transfer release receipt export')
    bound(rs['numerical_summary_sha256'], digests['wear_numerical_summary'], 'transfer release receipt numerical')
    bound(rs['interpretation_review_sha256'], digests['wear_review'], 'transfer release receipt review')
    bound(rs['freeze_sha256'], digests['wear_freeze'], 'transfer release receipt freeze')
    bound(ir['export_sha256'], digests['wear_export'], 'transfer review export')
    bound(ir['numerical_summary_sha256'], digests['wear_numerical_summary'], 'transfer review numerical')
    bound(ir['protocol_sha256'], digests['wear_protocol'], 'transfer review protocol')
    bound(ir['freeze_sha256'], digests['wear_freeze'], 'transfer review freeze')
    bound(ir['handoff_sha256'], rs['handoff_sha256'], 'transfer review handoff')
    bound(ns['freeze_sha256'], digests['wear_freeze'], 'transfer numerical summary freeze')
    bound(fz['protocol_sha256'], digests['wear_protocol'], 'transfer freeze protocol')
    # The 105 models are the adapter study's RAW-RESIDUAL fits: the freeze binds that study's release records.
    pp = fz['parent_provenance']
    bound(pp['protocol.json'], digests['adapter_protocol'], 'transfer parent protocol')
    bound(pp['execution-freeze.json'], digests['adapter_freeze'], 'transfer parent freeze')
    bound(fz['parent_freeze_sha256'], digests['adapter_freeze'], 'transfer parent freeze')
    bound(pp['review/release-status.json'], digests['adapter_release_status'], 'transfer parent release receipt')
    bound(pp['review/release-numerical-audit.json'], digests['adapter_numerical_review'], 'transfer parent numerical')
    bound(pp['review/release-interpretation-review.json'], digests['adapter_review'], 'transfer parent review')
    bound(pp['predictions-seal.json'], docs['adapter_numerical_review']['checks']['artifact_integrity']['seal_sha256'],
          'transfer parent seal')
    require(rs['status'] == 'audited_complete_aggregate_handoff_ready' and rs['incomplete_evaluations'] == [],
            'wearable: the release receipt is not complete')
    require(ir['status'] == 'approved' and ir['blocking_findings'] == [], 'wearable: the interpretation review')
    require(ns['status'] == 'passed', 'wearable: the numerical summary did not pass')

    b = ex['bootstrap']
    require(b['unit'] == 'person' and b['paired'] is True and b['replicates'] == DRAWS and b['seed'] == SEED,
            'wearable: bootstrap')
    require(b['interval'].startswith('linear percentile95%') and 'conditional on fixed source models' in b['interval'],
            'wearable: interval rule')
    unc = protocol['metrics']['uncertainty']
    require(f'seed{SEED}' in unc and 'Paired subject bootstrap' in unc and 'no confirmatory multiplicity claim' in unc,
            'wearable: protocol bootstrap')

    inp, src = protocol['input'], protocol['source']
    freqs = inp['frequencies']
    require(len(freqs) == len(set(freqs)) == ex['n_candidates'] == 12, 'wearable: frequencies')
    require(src['models'] == ex['n_source_models'] == len(src['folds']) * len(src['rotations']) * len(src['seeds']) == 105,
            'wearable: model count')
    require(src['arm'] == 'RAW-RESIDUAL' and src['seeds'] == docs['adapter_protocol']['split']['seeds'],
            'wearable: the source models are not the adapter fits')
    require(src['parameters_per_model'] == next(a['parameters'] for a in adapter['design']['arms']
                                                if a['code'] == 'RAW-RESIDUAL'), 'wearable: parameter count')
    require(ex['no_ensemble'] is True and ex['no_retraining'] is True, 'wearable: ensemble or retraining')
    require(inp['subjects'] == ex['n_target_people'] == 102, 'wearable: people')
    require(list(inp['epoch_relative_stimulus_s']) == [0.14, 2.14]
            and list(src['source_epoch_relative_stimulus_s']) == [0, 2], 'wearable: window onsets')
    close(ex['chance'], 1 / 12, 'wearable chance')
    require(ex['primary_strata'] == ['dry', 'wet'] and ex['secondary_strata'] == ['all'], 'wearable: strata roles')
    require(ex['primary_contrast'] == 'RAW-RESIDUAL_minus_CCA-RAW' and ex['secondary_comparator'] == 'CCA-CROP',
            'wearable: comparator roles')
    people = ex['n_target_people']
    endpoints = {}
    for s in STRATA:
        st = ex['strata'][s]
        require(st['n_people'] == people, f'wearable {s}: people')
        endpoints[s] = {'candidate_count': ex['n_candidates'], 'chance': ex['chance'], 'windows': st['n_trials'],
                        'role': 'primary' if s in ex['primary_strata'] else 'secondary'}
    require(endpoints['dry']['windows'] == endpoints['wet']['windows'] == 12240
            and endpoints['all']['windows'] == ex['n_target_trials'] == 24480, 'wearable: window counts')
    endpoints['all']['label'] = 'both sensors'

    seeds_of = {'RAW-RESIDUAL': len(src['seeds']), 'CCA-RAW': NO_TRAINING, 'CCA-CROP': NO_TRAINING}
    ci = 'paired_person_bootstrap_percentile_95ci'
    levels, codes = {}, {}
    for code in ('RAW-RESIDUAL', 'CCA-RAW', 'CCA-CROP'):
        for s in STRATA:
            lid = f'{code}/{s}'
            levels[lid] = level(ex['strata'][s]['metrics'][code], people, seeds_of[code], 'new', f'wearable {lid}', ci=ci)
            codes[lid] = ['#' + pointer('strata', s, 'metrics', code)]
    contrasts = {}
    key = ex['primary_contrast']
    for s in STRATA:
        cid = f'{key}/{s}'
        contrasts[cid] = contrast(ex['strata'][s]['metrics'][key], endpoints[s]['role'], f'RAW-RESIDUAL/{s}',
                                  f'CCA-RAW/{s}', levels, people, len(src['seeds']), f'wearable {cid}', ci=ci)
        codes[cid] = ['#' + pointer('strata', s, 'metrics', key)]
    require([c['role'] for c in contrasts.values()] == ['primary', 'primary', 'secondary'], 'wearable: contrast roles')
    require(DISPLAY_NAMES['wearable_transfer']['CCA-CROP'] not in (DISPLAY_NAMES['cca_adapter']['CCA-CROP'],
                                                                   DISPLAY_NAMES['cca_diagnostics']['SUBSPACE-CROP']),
            'wearable: the cropped-spectrum check shares a name with the BETA scores')
    stated(docs, 'wear_protocol', '/methods/comparator', 'three sine/cosine harmonics', 'matched CCA')
    stated(docs, 'wear_protocol', '/methods/diagnostic', 'unchanged source cropped spectral definition', 'cropped check')

    # The A2 fact: which CCA this is, and why the dry-versus-wet page reads slightly differently on the same windows.
    require(note['package'] == 'A2' and note['release_freeze_date'] == '20261020'
            and note['verification']['synthetic_check']['passed'] is True, 'wearable: the A2 note')
    require({digests[k] for k in ('wear_export', 'dry_vs_wet', 'wear_protocol', 'wear_freeze')}
            <= {r['sha256'] for r in note['sources']}, 'wearable: the A2 note read other files')
    m3, m4 = note['definitions']['transfer_matched_cca'], note['definitions']['dry_vs_wet_cca']
    require(m3['harmonics'] == [1, 2, 3] and m3['reference_columns'] == 6 and m3['export_key'] == 'CCA-RAW',
            'wearable: matched CCA definition')
    require(m4['harmonics'] == [1, 2, 3, 4] and m4['reference_columns'] == 8, 'wearable: dry-vs-wet CCA definition')
    stated(docs, 'wear_cca_definition', '/definitions/transfer_matched_cca/same_as_model_term',
           'matched CCA is the CCA built into the models', 'matched CCA is the model term')
    windows = note['differences']['windows']
    require(windows['difference'] == 'none' and fz['input_sha256']['epochs250.npy'] in windows['shared'],
            'wearable: the windows differ')
    rows = {r['id']: (i, r) for i, r in enumerate(dvw['rows'])}
    dvw_values, dvw_codes = {}, []
    for s, row_id in (('dry', 'wearable-sensor-transfer-006'), ('wet', 'wearable-sensor-transfer-005')):
        i, row = rows[row_id]
        dvw_codes.append(f'{DRY_VS_WET_FILE}#' + pointer('rows', i, 'value'))
        require(row['model'] == 'cca' and row['target_sensor'] == s and row['trials'] == endpoints[s]['windows']
                and row['participants'] == people and any(r.startswith(row_id) for r in m4['site_rows']),
                f'wearable: dry-vs-wet row {row_id}')
        dvw_values[s] = {'row_id': row_id, 'estimate': row['value'],
                         'interval': interval(*row['confidence_interval_95'], row['value'], row_id)}
    require(dvw['release_id'] == m4['release_id'], 'wearable: dry-vs-wet release')
    expect = {'strata.dry.metrics.CCA-RAW.mean': levels['CCA-RAW/dry'], 'strata.wet.metrics.CCA-RAW.mean': levels['CCA-RAW/wet'],
              'strata.dry.metrics.CCA-CROP.mean': levels['CCA-CROP/dry'],
              'strata.wet.metrics.CCA-CROP.mean': levels['CCA-CROP/wet'],
              'rows[id=wearable-sensor-transfer-006].value': dvw_values['dry'],
              'rows[id=wearable-sensor-transfer-005].value': dvw_values['wet']}
    for n in note['numbers'] + note['cropped_spectrum_diagnostic']['numbers']:
        want = expect[n['field']]
        require(n['value'] == want['estimate'] and n['interval_95'] == want['interval'],
                f'wearable: the A2 note figure {n["field"]} is not the source value')
    require('10,000 draws, seed 20260920, percentile' in note['numbers'][2]['interval_method'],
            'wearable: the dry-vs-wet interval method')
    require('balanced accuracy equals accuracy' in note['differences']['metric']['effect'], 'wearable: metric')
    fact = note['card7']['a2_fact_for_plan_template']
    cca_definition = {
        'matched_cca': {'code': 'CCA-RAW', 'harmonics': len(m3['harmonics']), 'reference_columns': m3['reference_columns'],
                        'same_as_model_term': True, 'same_definition_as': 'cca_adapter CCA-RAW'},
        'dry_vs_wet_cca': {'harmonics': len(m4['harmonics']), 'reference_columns': m4['reference_columns'],
                           'release_id': dvw['release_id'], 'metric': 'participant-mean balanced accuracy',
                           'equals_accuracy_here': True, 'dry': dvw_values['dry'], 'wet': dvw_values['wet'],
                           'interval_method': {'method': 'person bootstrap, percentile interval', 'draws': 10000,
                                               'seed': 20260920, 'level': LEVEL}},
        'same_windows': True,
        'windows_per_sensor': endpoints['dry']['windows'],
        'differs_in': 'harmonic count',
        'fact': {'en': fact['en'], 'zh': fact['zh']},
        'export_codes': ['wear_cca_definition#' + pointer('card7', 'a2_fact_for_plan_template')] + dvw_codes,
    }

    design = {
        'dataset': {'name': 'Wearable-102', 'people': people, 'targets': ex['n_candidates'],
                    'frequency_range_hz': [min(freqs), max(freqs)], 'windows': ex['n_target_trials'],
                    'windows_per_sensor': endpoints['dry']['windows'], 'sensors': ['dry', 'wet'],
                    'channels': len(inp['model_channel_names']), 'window_s': list(inp['epoch_relative_stimulus_s']),
                    'amplitude': 'as stored'},
        'source_models': {'dataset': 'BETA', 'arm': 'RAW-RESIDUAL', 'models': src['models'],
                          'person_folds': len(src['folds']), 'frequency_rotations': len(src['rotations']),
                          'training_seeds': len(src['seeds']), 'parameters_per_model': src['parameters_per_model'],
                          'window_s': list(src['source_epoch_relative_stimulus_s']), 'retraining': False,
                          'ensemble': False},
        'endpoints': endpoints,
        'methods': [{'code': 'RAW-RESIDUAL', 'role': 'model', 'training': 'trained on BETA, run unchanged'},
                    {'code': 'CCA-RAW', 'role': 'comparator', 'training': NO_TRAINING, 'harmonics': len(m3['harmonics']),
                     'same_definition_as': 'cca_adapter CCA-RAW'},
                    {'code': 'CCA-CROP', 'role': 'diagnostic', 'training': NO_TRAINING,
                     'same_definition_as': 'cca_adapter CCA-CROP'}],
    }
    rec, prec = ns['reconstruction'], ex['precision_diagnostic_counts']
    require(rec['model_count'] == 105 and rec['rows_per_model'] == 24480 and rec['argmax_mismatches'] == 0
            and rec['maximum_absolute_error'] == 0.0 and ns['numerical']['maximum_absolute_metrics_discrepancy'] == 0.0,
            'wearable: reconstruction')
    require(all(prec[s]['cca_float64_vs_float32_argmax_mismatches'] == 0 for s in STRATA), 'wearable: CCA precision')
    checks = {
        'numerical_summary': {'passed': True, 'models_reconstructed': rec['model_count'],
                              'windows_per_model': rec['rows_per_model'], 'argmax_mismatches': rec['argmax_mismatches'],
                              'max_absolute_error': rec['maximum_absolute_error'],
                              'metrics_max_discrepancy': ns['numerical']['maximum_absolute_metrics_discrepancy'],
                              'rows_checked': rec['feature_rows']},
        'interpretation_review': {'approved': True, 'blocking_findings': len(ir['blocking_findings'])},
        'release_receipt': {'complete': True, 'model_inferences': rs['completed_model_inferences'],
                            'reconstructions': rs['completed_all_trial_reconstructions']},
        'cca_float64_against_float32': {'argmax_mismatches': {s: prec[s]['cca_float64_vs_float32_argmax_mismatches']
                                                              for s in STRATA}},
        'cca_definition_note': {'passed': True, 'three_harmonic_code_agreement_max_difference': note['verification'][
            'synthetic_check']['results']['transfer_code_vs_dry_vs_wet_code_at_three_harmonics_max_abs_diff']},
    }
    return {
        'source_sha256': digests['wear_export'],
        'review_sha256': digests['wear_review'],
        'numerical_summary_sha256': digests['wear_numerical_summary'],
        'release_receipt_sha256': digests['wear_release_status'],
        'protocol_sha256': digests['wear_protocol'],
        'freeze_sha256': digests['wear_freeze'],
        'cca_definition_sha256': digests['wear_cca_definition'],
        'dry_vs_wet_sha256': digests['dry_vs_wet'],
        'source_models_sha256': digests['adapter_export'],
        'interval_method': {'method': METHOD, 'draws': b['replicates'], 'seed': b['seed'], 'level': LEVEL,
                            'conditional_on': 'the fixed 105 source models'},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('wearable_transfer', contrasts),
        'cca_definition': cca_definition,
        'undefined': [],
        'not_run': not_run('wearable_transfer', docs),
        'checks': checks,
        'limitations_keys': limitations('wearable_transfer', docs),
        'display_names': display_names('wearable_transfer', levels),
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
        require(not REFUSED_TEXT.search(value), f'{trail}: refused text {value!r}')
        require(not VERSION_LABEL.search(value), f'{trail}: a version label {value!r}')
        require(not RANKING.search(value), f'{trail}: a ranking word {value!r}')
    elif isinstance(value, float):
        require(math.isfinite(value) and value != 0.55, f'{trail}: refused value {value!r}')


def build_blocks(pins=None) -> dict:
    """The three CCA study blocks, keyed cca_diagnostics, cca_adapter and wearable_transfer."""
    docs, digests = load(pins)
    bound(docs['diag_handoff_review']['handoff_sha256'], HANDOFF_CONTEXT['cca_diagnostics']['bound_sha256'],
          'diagnostics handoff')
    bound(docs['adapter_release_status']['handoff_sha256'], HANDOFF_CONTEXT['cca_adapter']['bound_sha256'],
          'adapter handoff')
    require(HANDOFF_CONTEXT['cca_adapter']['on_disk_sha256'][:8] in docs['adapter_binding_review'],
            'adapter handoff: the binding review does not name the file on disk')
    bound(docs['wear_release_status']['handoff_sha256'], HANDOFF_CONTEXT['wearable_transfer']['bound_sha256'],
          'transfer handoff')
    diagnostics = diagnostics_block(docs, digests)
    adapter = adapter_block(docs, digests, diagnostics)
    wearable = wearable_block(docs, digests, adapter)
    blocks = {'cca_diagnostics': diagnostics, 'cca_adapter': adapter, 'wearable_transfer': wearable}
    for name, block in blocks.items():
        require(all(f in block for f in BLOCK_FIELDS), f'{name}: a block field is missing')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
                f'{name}: export codes do not cover the levels and contrasts')
        for c in block['contrasts'].values():
            require(c['left'] in block['levels'] and c['right'] in block['levels'], f'{name}: a contrast side is no level')
    validate_public(blocks)
    scrub_check(blocks)
    return blocks


if __name__ == '__main__':
    built = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'limitations': len(b['limitations_keys'])} for s, b in built.items()}, indent=2))
