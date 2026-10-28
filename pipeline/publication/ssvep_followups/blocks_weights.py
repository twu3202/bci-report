"""The weighting blocks of the SSVEP follow-ups release: cards 12 to 14 (harmonic gap, fixed decay, rising weights).

Three audited route 3 follow-ups, all untrained and candidate-conditioned, read from their own aggregates and turned
into study blocks for `ssvep-followups-update.json`, which its assembler puts under `studies` (plan section 2.1):

- `harmonic_gap` (card 12, queue row 15): where the harmonic sum's two points over joint CCA come from. Joint CCA (J),
  the common-direction sum (B), the harmonic sum (S) and the diagnostic score J + G on BETA held-out and Wearable-102
  dry and wet; the nine-comparison primary family (the true-minus-mean-distractor gap G and the two bridge steps J to B
  and B to S, in three cohorts) with its 99.44% Bonferroni family intervals; G and the coupling residual R in
  squared-correlation units; pairwise win fractions, which are not accuracies; the symmetric two-order allocation
  (descriptive accounting); the BETA decision changes as shares of the 11,200 decisions; the label-free reference
  check as counts only. From `results/Harmonic Gap Aggregate Results.json` and `Reference Geometry QC Aggregate.json`.
- `fixed_decay` (card 13, queue row 14): one fixed rule, n^-1.25 + 0.25, on the three harmonics (H3) and on
  filter-bank CCA's seven sub-bands; the prespecified 90% equivalence interval and its 0.5-point margin on BETA
  held-out; seen-32 and Wearable-102 dry and wet. From `results/Fixed Decay Aggregate Results.json`; its
  retrospective ratio table is not selected.
- `rising_weights` (card 14, queue row 20): flat against the rising vector [1, 1.5, 1.9] on the same three harmonic
  correlations; BETA held-out is the single prespecified criterion; seen-32 and Wearable-102 dry and wet; the
  exact-profile rows as a rounding check. From `results/Rising Weight Aggregate Results.json`.

Every input is pinned by SHA-256 (PINS) and refused unless it is byte for byte the pinned file and the study's
release approval and reviews bind that hash. Release status is read from each study's `state/release-approval.json`
and its reviews, never from an execution terminal's own status field. Every number is the source's own double:
nothing is rounded, rescaled or recomputed, and units stay fractions (accuracies and their differences) or
squared-correlation score units (G and R). The single exception is declared: the harmonic gap's all-trial decision
counts are published as shares, count / 11,200, one division each, and the counts themselves are not selected.
The pinned protocols, receipts and approvals carry private storage paths, host names and the comment thread's
figures, so they are read and checked here, never copied; only named fields are selected from them.

Cross-checks, not sources: the released `new-ssvep-frequencies-update.json` (card 5's CCA and card 7's matched CCA),
the coherence aggregate (its CCA and harmonic sum, which tie this round's seen-32 to route 3's seen_ba) and the
practical B/D aggregate (card 11's filter-bank CCA) are read for bit-for-bit equality checks only; no value of theirs
is copied. A level that equals one of them names it in `same_estimate_as`.

A block is a mapping with the fields of the B1 to B3 blocks (see blocks_cca.py), plus `interval_level` on every level
and contrast (card 12 mixes 99.44% family intervals with nominal 95% ones):
- `source_sha256`, `review_sha256` (the interpretation review that accepted the source), `approval_sha256` (the
  study's release approval), and the other pinned records by name;
- `interval_method`: `{method, draws, seeds: {dataset: seed}, level}` plus `shared_draws`; card 12 adds `family`;
- `design`: the datasets, the endpoints with their candidate counts and chance levels, and the scores or arms;
- `levels`: `{id: {estimate, interval, interval_level, unit, people, seeds, origin}}`, plus `same_estimate_as` where
  a released or same-round level carries the same double; an id is `<code>/<endpoint>`, endpoints `u8` (BETA
  held-out 8-way), `seen_ba` (BETA seen 32-way), `dry` and `wet` (Wearable-102); `interval` is null where the source
  gives a level without one (fixed decay), never zero;
- `contrasts`: `{id: {role, left, right, estimate, interval, interval_level, unit, people, seeds, flags}}`; `role`
  is `primary`, `secondary` or `rounding_check`;
- `contrast_limitations`, `undefined`, `not_run`, `checks`, `limitations_keys`, `display_names`, `export_codes` as in
  the B3 blocks; `export_codes` cover the levels, the contrasts and (card 12) the gap statistics; every other record
  carries its own `export_codes`.
Card 12 adds `family`, `gap`, `win_fractions`, `allocation`, `transitions`, `identity` and `reference_check`;
card 13 adds `equivalence`; card 14 adds `criterion`.

What a block refuses: per-person, per-fold, per-seed, per-window and per-frequency values (the reference check's
frequencies above all), predictions, raw counts, the comment thread's figures and point bets (D23: the new cards state
only their prespecified criteria), private paths and host names, version labels, update markers and ranking words.

    python3 pipeline/publication/ssvep_followups/blocks_weights.py      # builds and prints the counts; writes nothing
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
from ssvep_followups.blocks_cca import (  # noqa: E402  (the B3 helpers, unchanged)
    REFUSED_TEXT, RANKING, VERSION_LABEL, close, count, location, number, numeric_leaves, pointer, require, resolve,
    sha)

# ---------------------------------------------------------------------------- pinned inputs
# Paths are relative to the project; `research/...` resolves under `researchRoot` when local_paths.json sets one.
_H, _F, _R = ('research/decision_route3_harmonic_gap_20261021', 'research/decision_route3_fixed_decay_20261022',
              'research/decision_route3_rising_weights_20261025')
PINS = {
    # card 12, harmonic gap
    'gap_export': {'path': f'{_H}/results/Harmonic Gap Aggregate Results.json',
                   'sha256': '32d9337e915bf062e2ad49c049e8313d5bf55f23afe07e77901ccef74c30a9e8'},
    'gap_reference_qc': {'path': f'{_H}/results/Reference Geometry QC Aggregate.json',
                         'sha256': '1cc54ee70bc3e9cf304c8ce4b4dfa2e85869ee0422275caadfd24ed256b96bea'},
    'gap_protocol': {'path': f'{_H}/protocol.json',
                     'sha256': 'b555200c9bfbaa6e9ea6ee601a48575977abf5f1005f8553d4186359fc629cd7'},
    'gap_freeze': {'path': f'{_H}/execution-freeze.json',
                   'sha256': '979037d30298cec69f4cdcaf3a0ed63deacdfae3ec23b4ab57ea3de53cc83c2a'},
    'gap_numerical_review': {'path': f'{_H}/review/Independent Harmonic Gap Numerical Result Review.json',
                             'sha256': '83ff4212d2022e663268b08f80541508d4a0bb8d3d0b107b38efa7e38be84ad5'},
    'gap_interpretation_receipt': {'path': f'{_H}/review/Interpretation Review Receipt.json',
                                   'sha256': '912504d6f30956a9421b9cfd5b3642534916276746ebb509aad6b1811c8424c5'},
    'gap_interpretation_review': {'path': f'{_H}/review/Interpretation Review.md',
                                  'sha256': '88ea82716046c1ce04fdd4516b65984cb7c2ab3aa0142087d02c241cd100e1e9'},
    'gap_text_receipt': {'path': f'{_H}/review/Handoff Text Review Receipt.json',
                         'sha256': '515ee5ba93f24f55f6852569a8ca886fc98942ebf31af096aabf01796b0f6b98'},
    'gap_text_review': {'path': f'{_H}/review/Handoff Text Review.md',
                        'sha256': '968cbfce24c9f6e576ffee2d70c748919951ee8fa50a25f25c0edc3f345bb1b2'},
    'gap_release_approval': {'path': f'{_H}/state/release-approval.json',
                             'sha256': 'c20938849706faf5b73326e8bde3f09f510e085b317039f27ad49f3078689904'},
    # card 13, fixed decay
    'decay_export': {'path': f'{_F}/results/Fixed Decay Aggregate Results.json',
                     'sha256': 'c33ef5084a2c4892e60676ef37c0ddc856f7c2d632c4ceaa1b1a35e53cc3016d'},
    'decay_protocol': {'path': f'{_F}/protocol.json',
                       'sha256': 'cc75d31490a4d9ede1cac848f9bde587e4cadfb190a2dc48de084716416fefb5'},
    'decay_freeze': {'path': f'{_F}/execution-freeze.json',
                     'sha256': '74e2b933815d6f68b1b2949d8e2d67e10bf904c4270174b8402461570f204a73'},
    'decay_execution_review': {'path': f'{_F}/execution-review.json',
                               'sha256': '8fab5f60dfdd1322fc71296a951b8fcbd7644c387b44b6085ad7b478b11bfaec'},
    'decay_audit_receipt': {'path': f'{_F}/review/independent-result-audit-receipt.json',
                            'sha256': '59a7cfa486cd0861b4d10e7d0738075d1555e4957223eac496c7eb1a91576525'},
    'decay_review': {'path': f'{_F}/review/Interpretation and Handoff Review.json',
                     'sha256': 'f172c2c9e78e1f5bf82ec888bb910d3247943f843d86a3d3d238d8485426e41f'},
    'decay_release_approval': {'path': f'{_F}/state/release-approval.json',
                               'sha256': 'af311af29820703ae186b72b6986e5758f2910f16cd2cb42869b76ab5629a610'},
    # card 14, rising weights
    'rise_export': {'path': f'{_R}/results/Rising Weight Aggregate Results.json',
                    'sha256': '13eb89eaee9e64f0f7a7465ae6ae7a97110e034f1ea01cd684051e3573dbb882'},
    'rise_protocol': {'path': f'{_R}/protocol.json',
                      'sha256': '0839e4432a6cd49fa5c3379633207e1d5a3acae3f79c17287b1570f7a2488676'},
    'rise_freeze': {'path': f'{_R}/execution-freeze.json',
                    'sha256': 'b209b4c60e1d4db35d088b93407c3a5df0d8d4e95dedbd930d59d31aadd51d2f'},
    'rise_execution_review': {'path': f'{_R}/execution-review.json',
                              'sha256': 'b38516cbf0780d53ee59971ddf8de4ade1326fc09e300b9a3fb614aa0c6bccd7'},
    'rise_audit_receipt': {'path': f'{_R}/review/result-audit-receipt.json',
                           'sha256': '364aa2284ac65643725c7d3e39eb3aa23ae97afad2f44f66f14b1a46c999cb51'},
    'rise_review': {'path': f'{_R}/review/interpretation-review.json',
                    'sha256': 'f4ab241ec1a3312f3cc602b6d962f1a92b616618e560db5b14d33369a0a15572'},
    'rise_release_approval': {'path': f'{_R}/state/release-approval.json',
                              'sha256': '86eee3ca1ca3bd3a002860936594c545aac4da05781d9218ca044a6aa320a302'},
    # Cross-checks only: equal doubles, never a copy source.
    'released': {'path': 'site/src/data/new-ssvep-frequencies-update.json',
                 'sha256': '197028bdc4dadd9713f6d408bb64204147fdfe39a686e7e119e4988aaf863ee0'},
    'coherence_export': {'path': 'research/decision_route3_coherence_eigen_20261020/evidence/Completed Aggregate Results.json',
                         'sha256': '9ee6cc3a9a46c76faeec00b3d7b57a5fb66993389f85d001a443507becc6717d'},
    'practical_bd_export': {'path': 'research/ssvep_practical_suite_20261020/raw_followup/review/BD Aggregate Results.json',
                            'sha256': '21495d28ed65606aed7e8b41b3c2e565ac4789aaa43109557d1e662bf0c94fd7'},
}
TEXT_PINS = {'gap_interpretation_review', 'gap_text_review'}
SERVED = {'released': 'site/public/data/new-ssvep-frequencies-update.json'}   # must be the same bytes as the src copy
RELEASED_FILE, RELEASED_ID = 'new-ssvep-frequencies-update.json', 'new-ssvep-frequencies-update-20261020'
CROSS_CHECK_PINS = ('released', 'coherence_export', 'practical_bd_export')
# For the release manifest only: the handoffs are context, never a copy source, and stay out of the blocks. Each bound
# hash is the one the study's release approval binds (and the integration queue row names).
HANDOFF_CONTEXT = {
    'harmonic_gap': {'bound_sha256': 'a266d13aaa8f7c8b25b7445f106d887bb916fcabb31a8ff39ed6f85bcee0a900',
                     'bound_by': 'gap_release_approval', 'queue_row': 15},
    'fixed_decay': {'bound_sha256': 'eba5bbe96eff8adb1d569f2601dcca6906ed007216491800e48a3f81c78db9ab',
                    'bound_by': 'decay_release_approval', 'queue_row': 14},
    'rising_weights': {'bound_sha256': 'c193eb076aa2a65f780d230b51ca45e6b716cfaf9974bc212d5fdf5e052013e8',
                       'bound_by': 'rise_release_approval', 'queue_row': 20},
}
STUDIES = ('harmonic_gap', 'fixed_decay', 'rising_weights')
CARDS = {'harmonic_gap': (12, 'harmonic-gap'), 'fixed_decay': (13, 'fixed-decay'), 'rising_weights': (14, 'rising-weights')}
EXPORT_OF = {'harmonic_gap': 'gap_export', 'fixed_decay': 'decay_export', 'rising_weights': 'rise_export'}
REVIEW_OF = {'harmonic_gap': 'gap_interpretation_receipt', 'fixed_decay': 'decay_review', 'rising_weights': 'rise_review'}
APPROVAL_OF = {'harmonic_gap': 'gap_release_approval', 'fixed_decay': 'decay_release_approval',
               'rising_weights': 'rise_release_approval'}
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'approval_sha256', 'interval_method', 'design', 'levels', 'contrasts',
                'contrast_limitations', 'undefined', 'not_run', 'checks', 'limitations_keys', 'display_names',
                'export_codes')

PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
SCORE, SCORE_DIFFERENCE = 'squared correlation', 'difference of squared correlations'
WIN_FRACTION = 'pairwise win fraction'
NO_TRAINING = 'no training'
METHOD = 'paired person bootstrap, percentile interval'
DRAWS, LEVEL, EQUIVALENCE_LEVEL = 20000, 0.95, 0.90
FAMILY_SIZE, FAMILY_ALPHA = 9, 0.05
TOL = 1e-12
BETA, WEARABLE = 'BETA', 'Wearable-102'
SEEDS = {'harmonic_gap': {BETA: 20261021, WEARABLE: 20261022},
         'fixed_decay': {BETA: 2026102201, WEARABLE: 2026102202},
         'rising_weights': {BETA: 2026102501, WEARABLE: 2026102502}}

# ---------------------------------------------------------------------------- endpoints and codes
# site endpoint id -> the study's cohort key. u8 and seen_ba are route 3's spelling of the same two BETA tasks (checked
# through CCA and the harmonic sum against card 5 and the coherence aggregate); dry and wet are card 7's.
GAP_COHORTS = {'u8': 'BETA-held8', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'}
DECAY_COHORTS = {'H3': {'u8': 'BETA-held8', 'seen_ba': 'BETA-seen32', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'},
                 'FBCCA': {'u8': 'BETA-FBCCA-held8', 'seen_ba': 'BETA-FBCCA-seen32'}}
RISE_COHORTS = {'u8': 'BETA-held8', 'seen_ba': 'BETA-seen32', 'dry': 'Wearable-dry', 'wet': 'Wearable-wet'}
DATASET_OF = {'u8': BETA, 'seen_ba': BETA, 'dry': WEARABLE, 'wet': WEARABLE}
CANDIDATES = {'u8': 8, 'seen_ba': 32, 'dry': 12, 'wet': 12}

GAP_ARMS = {'J': 'accuracy_J', 'B': 'accuracy_shared', 'S': 'accuracy_free', 'JplusG': 'accuracy_JplusG'}
GAP_PRIMARY = {('B', 'J'): 'accuracy_S_shared_minus_S_joint', ('S', 'B'): 'accuracy_S_free_minus_S_shared'}
GAP_SECONDARY = {('S', 'J'): 'increment_J_to_free', ('JplusG', 'J'): 'increment_J_to_JplusG',
                 ('S', 'JplusG'): 'increment_JplusG_to_free'}
GAP_DUPLICATES = {'increment_J_to_shared': 'accuracy_S_shared_minus_S_joint',
                  'increment_shared_to_free': 'accuracy_S_free_minus_S_shared'}
GAP_PRIMARY_GAP = ('G true minus mean distractor', 'G_true_minus_mean_distractor')
GAP_STATS = {'G true': 'mean_true_G', 'G mean distractor': 'mean_distractor_G',
             'R true': 'mean_true_R', 'R mean distractor': 'mean_distractor_R',
             'R true minus mean distractor': 'R_true_minus_mean_distractor'}
GAP_WIN = 'G_true_vs_distractor_pairwise_probability_including_half_exact_ties'
GAP_ALLOCATION = {'G': 'symmetric_path_G', 'R': 'symmetric_path_R'}
GAP_NOT_SELECTED = ('mean_true_Delta', 'mean_distractor_Delta', 'Delta_true_minus_mean_distractor',
                    'G_true_minus_fixed_J_distractor', 'R_true_minus_fixed_J_distractor',
                    'Delta_true_minus_fixed_J_distractor')
GAP_EDGES = {'J->shared': ('J', 'B'), 'shared->free': ('B', 'S'), 'J->free': ('J', 'S'),
             'J->JplusG': ('J', 'JplusG'), 'JplusG->free': ('JplusG', 'S')}
EDGE_SHARES = (('wrong_to_right', 'rescue'), ('right_to_wrong', 'harm'), ('unchanged_right', 'stable_correct'),
               ('wrong_both', 'stable_wrong'), ('changed', 'prediction_change'))
DECAY_ARMS = {'FLAT': 'accuracy_flat', 'DECAY': 'accuracy_decay'}
RISE_ARMS = ('flat', 'literal_rise', 'exact_rise')
RISE_CONTRASTS = {('literal_rise', 'flat'): 'literal_rise_minus_flat', ('exact_rise', 'flat'): 'exact_rise_minus_flat',
                  ('exact_rise', 'literal_rise'): 'exact_rise_minus_literal_rise'}

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
HARMONIC_SUM = 'harmonic sum (no training)'
FBCCA_NAME = 'filter-bank CCA (seven sub-bands)'
DISPLAY_NAMES = {
    'harmonic_gap': {'J': 'joint CCA', 'B': 'common-direction sum', 'S': HARMONIC_SUM,
                     'JplusG': 'joint CCA plus gap (diagnostic score)'},
    'fixed_decay': {'H3-FLAT': HARMONIC_SUM, 'H3-DECAY': 'harmonic sum with decay weights (no training)',
                    'FBCCA-FLAT': 'filter-bank CCA with flat sub-band weights (no training)',
                    'FBCCA-DECAY': FBCCA_NAME},
    'rising_weights': {'flat': HARMONIC_SUM, 'literal_rise': 'rising weights 1, 1.5, 1.9 (no training)',
                       'exact_rise': 'rising weights, exact profile (no training)'},
}
# The plan's name key rows this package touches (site name first, export codes second); the others are card names.
NAME_KEY = (
    ('joint CCA', 'J in the harmonic-gap export: the same scores as CCA-RAW'),
    ('common-direction sum', 'B'),
    (HARMONIC_SUM, 'S in the harmonic-gap export, H3-FLAT in the fixed-decay export, flat in the rising-weight '
                   'export: one set of scores'),
    (FBCCA_NAME, 'FBCCA-DECAY in the fixed-decay export: the same scores as FBCCA-M3-N7-H5 at 2 s and 8 electrodes'),
)

# ---------------------------------------------------------------------------- limitations, not run, declared edits
# key -> (pinned input, JSON pointer, phrase the field must contain); pointer '' is a whole text record.
LIMITATION_SOURCES = {
    'harmonic_gap': {
        'family_intervals_govern': ('gap_interpretation_receipt', '/required_limits/0',
                                    'Nine-family adjusted primary intervals govern positive claims'),
        'dry_bridge_unresolved': ('gap_interpretation_receipt', '/required_limits/1',
                                  'Wearable dry accuracy bridge unresolved after adjustment'),
        'no_b_over_j_resolved': ('gap_interpretation_receipt', '/required_limits/2',
                                 'No B-over-J contrast resolved; not equivalence'),
        'allocation_not_a_cause': ('gap_interpretation_receipt', '/required_limits/3',
                                   'operational allocation is not unique physiological causality'),
        'no_training': ('gap_interpretation_receipt', '/required_limits/4', 'No training or generic question learning'),
        'reused_benchmarks': ('gap_interpretation_receipt', '/required_limits/5',
                              'not untouched external confirmation'),
        'joint_cca_not_top_eigenvalue_of_sum': ('gap_interpretation_review', '',
                                                'J=B is generally false for overlapping finite-window harmonic '
                                                'reference spaces'),
        'residual_signed': ('gap_protocol', '/scores/R', 'signed reference-coupling residual'),
        'gap_in_score_units': ('gap_interpretation_review', '', 'These are dimensionless score gaps, not percentages'),
        'win_fractions_not_accuracies': ('gap_text_review', '',
                                         'Pairwise win fractions are explicitly distinguished from classification '
                                         'accuracy'),
        'allocation_descriptive': ('gap_export', '/path_interpretation',
                                   'descriptive operational allocation; not causal or physiological mediation'),
        'secondary_intervals_descriptive': ('gap_interpretation_review', '',
                                            'Do not use these secondary nominal intervals to override the unresolved '
                                            'adjusted dry primary contrast'),
        'transitions_not_disjoint': ('gap_interpretation_review', '',
                                     'the sets of rescued/harmed trials need not be disjoint'),
        'mean_distractor_not_strongest': ('gap_interpretation_review', '',
                                          'Mean distractors are not the strongest competitor'),
        'gap_is_an_association': ('gap_interpretation_review', '',
                                  'Larger true-candidate G is compatible with genuine harmonic-specific spatial '
                                  'structure'),
        'same_people_dry_wet': ('gap_interpretation_review', '',
                                'with the same Wearable people contributing dry and wet conditions'),
        'no_wet_dry_test': ('gap_interpretation_review', '',
                            'Larger wet than dry point gaps do not constitute a tested wet/dry difference'),
        'reference_check_label_free': ('gap_text_review', '', 'reference-only checks, without outcome subgroup claims'),
    },
    'fixed_decay': {
        'equivalence_not_met': ('decay_review', '/findings/1', 'interval lies entirely below -0.5 pp'),
        'equivalence_approximate': ('decay_protocol', '/statistics/primary_equivalence_rule',
                                    'approximate equivalence inference'),
        'within_construction_only': ('decay_review', '/findings/2',
                                     'changes weights within the same seven-subband/five-harmonic construction'),
        'secondary_descriptive': ('decay_review', '/findings/3', 'All secondary 95% intervals remain nominal/descriptive'),
        'harmonic_weighting_is_adaptation': ('decay_protocol', '/limits/1',
                                             'Applying Chen subband weights to harmonic index is an adaptation'),
        'no_optimality_claim': ('decay_protocol', '/limits/2',
                                'No claim of optimality or ceiling from a single fixed decay rule'),
        'reused_datasets': ('decay_protocol', '/limits/0', 'not untouched confirmation'),
        'wearable_units_and_windows': ('decay_protocol', '/limits/4',
                                       'Wearable as-stored units and onset/window mismatch remain'),
    },
    'rising_weights': {
        'single_primary': ('rise_protocol', '/statistics/primary', 'BETA held8 literal rising minus flat accuracy'),
        'secondary_descriptive': ('rise_protocol', '/statistics/secondary',
                                  'Exact-profile and seen32/Wearable contrasts nominal descriptive only; no '
                                  'equivalence or familywise claim'),
        'exact_profile_rounding_check': ('rise_review', '/checks/3',
                                         'descriptive rounding sensitivity, not selected replacement or equivalence '
                                         'claim'),
        'dry_decrement_wet_unresolved': ('rise_review', '/checks/4',
                                         'Dry decrement has nominal negative interval; wet and seen32 intervals cross '
                                         'zero'),
        'coverage_heuristic': ('rise_protocol', '/limits/1',
                               'Nesting coverage counts and summed band weights are heuristics'),
        'passbands_wider_than_nominal': ('rise_protocol', '/limits/2',
                                         'Actual passbands are expanded nominal bands and have smooth transitions'),
        'no_alpha_test': ('rise_protocol', '/limits/4', 'alpha explanation remains untested'),
        'no_learned_weights': ('rise_protocol', '/limits/3', 'No weights learned, exponent search'),
        'reused_cohorts': ('rise_protocol', '/limits/0', 'not untouched confirmation'),
    },
}
# contrast id ('X minus Y' for every endpoint, 'X minus Y/<endpoint>' for one) -> limitation keys
CONTRAST_LIMITATIONS = {
    'harmonic_gap': {'B minus J': ('no_b_over_j_resolved',), 'S minus B/dry': ('dry_bridge_unresolved',),
                     'S minus J': ('secondary_intervals_descriptive',),
                     'JplusG minus J': ('secondary_intervals_descriptive',),
                     'S minus JplusG': ('secondary_intervals_descriptive',)},
    'fixed_decay': {'H3-DECAY minus H3-FLAT/u8': ('equivalence_not_met', 'equivalence_approximate'),
                    'FBCCA-DECAY minus FBCCA-FLAT': ('within_construction_only',)},
    'rising_weights': {'exact_rise minus flat': ('exact_profile_rounding_check',),
                       'exact_rise minus literal_rise': ('exact_profile_rounding_check',),
                       'literal_rise minus flat/dry': ('dry_decrement_wet_unresolved',),
                       'literal_rise minus flat/wet': ('dry_decrement_wet_unresolved',)},
}
# item -> (pinned input, JSON pointer, phrase); nothing in this release runs these items later.
NOT_RUN_SOURCES = {
    'harmonic_gap': {
        'a learned head on the same statistics': ('gap_interpretation_review', '',
                                                  'it does not revisit the learned-head contribution'),
        'eigenvector stability, source separation or a physiological intervention': (
            'gap_interpretation_review', '',
            'No eigenvector stability, physical source separation, or intervention on physiology was tested'),
    },
    'fixed_decay': {
        'other exponents, offsets or harmonic counts': ('decay_protocol', '/statistics/failure_policy',
                                                        'new exponent/offset, harmonic count selection'),
    },
    'rising_weights': {
        'a pre-stimulus alpha or noise measurement': ('rise_protocol', '/limits/4',
                                                      'No pre-stimulus alpha/noise measurement exists in this test'),
        'a weight search or frequency-dependent normalization': ('rise_protocol', '/limits/3',
                                                                 'exponent search, frequency-dependent normalization'),
    },
}
DECLARED_EDITS = {
    'harmonic_gap': (
        'schema and intervals strings not selected; the interval method is read from the frozen protocol',
        'the nominal 95% intervals of the nine family contrasts not selected; their 99.44% family intervals govern',
        'increment_J_to_shared and increment_shared_to_free not selected: the same values as the two family bridge '
        'contrasts',
        'Delta metrics and the margins against the strongest joint-CCA distractor not selected',
        'primary_positive not selected; the flags are derived from the family interval and checked against it',
        'BETA edges published as shares of the 11,200 held-out decisions (count / 11,200); the counts not selected',
        'Wearable-102 edges not selected',
        'the reference check published as counts and its threshold; the candidate frequencies, norms and residuals '
        'not selected',
        'independent_audit implementation strings not selected; pass flags and maximum errors kept',
        'accuracy_shared and accuracy_free named B and S, prediction_change named changed, stable_correct named '
        'unchanged_right and stable_wrong named wrong_both',
        'BETA-held8, Wearable-dry and Wearable-wet named u8, dry and wet in ids (route 3 and card 7 spelling of the '
        'same tasks)',
        'every level carries "no training" in place of seeds',
    ),
    'fixed_decay': (
        'retrospective_gap_ratio not selected: the ratio table and the dry reconstruction stay in the research folder',
        'transitions not selected',
        'point_inside_margin not selected: the point bet of the comment thread (D23); the equivalence interval kept',
        'role strings not selected; roles read from the frozen protocol',
        'the release approval names the numerical audit by a private path; its receipt is pinned by its own hash',
        'H3 and FBCCA flat and decay arms named H3-FLAT, H3-DECAY, FBCCA-FLAT and FBCCA-DECAY; BETA-held8, '
        'BETA-seen32, Wearable-dry and Wearable-wet named u8, seen_ba, dry and wet in ids',
        'levels carry interval null: the aggregate gives arm accuracies without intervals',
        'every level carries "no training" in place of seeds',
    ),
    'rising_weights': (
        'the accuracy block not selected; arm_levels kept (the same accuracies to the last place, with intervals)',
        'transitions not selected',
        'supports_primary_benefit and role not selected; the criterion is derived from the interval and checked',
        'the release approval point-bet fields not selected (D23); the prespecified criterion kept',
        'BETA-held8, BETA-seen32, Wearable-dry and Wearable-wet named u8, seen_ba, dry and wet in ids',
        'every level carries "no training" in place of seeds',
    ),
}
# For the release manifest's not-published list.
NOT_PUBLISHED = (
    'The fixed-decay retrospective gap-to-gain ratio table and its dry reconstruction.',
    'Per-frequency values of any kind, including the reference check’s candidate frequencies: the check is published '
    'as counts.',
    'All-trial decision counts: the harmonic-gap decision changes on BETA held-out are published as shares of the '
    '11,200 decisions; the Wearable-102 decision changes and the fixed-decay and rising-weight transitions are not '
    'published.',
    'The harmonic-gap Delta means and the margins against the strongest joint-CCA distractor.',
    'Point predictions from the comment thread on these three cards (D23): each card states its prespecified '
    'criterion.',
)

# ---------------------------------------------------------------------------- what no block may carry
REFUSED_KEYS = set(FORBIDDEN_KEYS) | {
    'pid', 'job', 'private_root', 'rows', 'status', 'release_status', 'path', 'paths', 'range', 'chain', 'interpretation',
    'epochs', 'near_orthogonal_frequencies_hz', 'frequencies', 'retrospective_gap_ratio', 'point_bet',
    'point_inside_margin', 'primary_positive_point', 'rescue', 'harm', 'stable_correct', 'stable_wrong', 'comment',
    'thread_bet', 'bet', 'forecast'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_seed', 'subject', 'prediction', 'probabilit', 'confusion', 'percentile', 'quantile',
                         'feature', 'private', 'path', 'host', 'elapsed', 'seconds', 'timing', 'memory', 'device',
                         'checkpoint', 'fifty', '055', '_utc', 'frequencies', '_hz', 'gap_ratio', 'ratio_')
EXTRA_REFUSED_TEXT = re.compile(
    r'\.(?:npz|npy|edf|mat|pt|ckpt|py)\b|\b\d+(?:\.\d+)?\s*Hz\b|(?<![\w-])(?:updated?|added|newly)(?![\w.-])'
    r'|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b'
    r'|commenter|\bbet\b|forecast|huggingface', re.IGNORECASE)


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
    text = resolve(docs[name], ptr)
    require(isinstance(text, str) and phrase in text, f'{label}: {name} {ptr} does not state {phrase!r}')


def bound(value, digest, label):
    require(value == digest, f'{label}: binds {str(value)[:12]}, pinned {digest[:12]}')


def interval(ci, point, label, lower=0.0, upper=1.0):
    require(isinstance(ci, list) and len(ci) == 2, f'{label}: no interval')
    lo, hi = ci
    require(all(number(v) for v in (lo, hi, point)), f'{label}: not a finite interval')
    require(lower <= lo <= point <= hi <= upper, f'{label}: the interval does not hold its point')
    return [lo, hi]


def level(estimate, ci, people, label, unit=PROPORTION, ci_level=LEVEL):
    """A level; `ci` None where the source gives the level without an interval."""
    require(number(estimate) and 0.0 <= estimate <= 1.0, f'{label}: not a proportion')
    return {'estimate': estimate, 'interval': None if ci is None else interval(ci, estimate, label),
            'interval_level': None if ci is None else ci_level, 'unit': unit, 'people': people, 'seeds': NO_TRAINING,
            'origin': 'new'}


def contrast(estimate, ci, role, left, right, levels, label, ci_level=LEVEL):
    """A paired contrast, refused unless it is the difference of its two levels."""
    require(number(estimate), f'{label}: not a number')
    close(estimate, levels[left]['estimate'] - levels[right]['estimate'], f'{label} is not the difference of its levels')
    require(levels[left]['people'] == levels[right]['people'], f'{label}: the two levels have other people')
    iv = interval(ci, estimate, label, lower=-1.0)
    return {'role': role, 'left': left, 'right': right, 'estimate': estimate, 'interval': iv, 'interval_level': ci_level,
            'unit': DIFFERENCE, 'people': levels[left]['people'], 'seeds': NO_TRAINING,
            'flags': {'interval_includes_zero': iv[0] <= 0 <= iv[1]}}


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
        keys = CONTRAST_LIMITATIONS[study].get(cid, ()) + CONTRAST_LIMITATIONS[study].get(cid.split('/')[0], ())
        if keys:
            require(set(keys) <= set(LIMITATION_SOURCES[study]), f'{study} {cid}: a limitation is not sourced')
            out[cid] = list(keys)
    for key in CONTRAST_LIMITATIONS[study]:
        require(any(cid == key or cid.split('/')[0] == key for cid in contrasts), f'{study}: no contrast {key!r}')
    return out


def display_names(study, levels):
    codes = list(dict.fromkeys(lid.split('/')[0] for lid in levels))
    require(set(codes) == set(DISPLAY_NAMES[study]), f'{study}: display names differ from the codes {codes}')
    return {c: DISPLAY_NAMES[study][c] for c in codes}


def endpoint(e, windows, label):
    """An endpoint record; chance is one over the candidates the study names."""
    return {'dataset': DATASET_OF[e], 'candidate_count': CANDIDATES[e], 'chance': 1 / CANDIDATES[e],
            'decisions': windows, 'label': label}


def bootstrap(protocol_seeds, draws, study):
    want = SEEDS[study]
    got = {BETA: protocol_seeds['BETA'], WEARABLE: protocol_seeds['Wearable']}
    require(got == want and draws == DRAWS, f'{study}: bootstrap seeds or draws')
    return {'method': METHOD, 'draws': draws, 'seeds': got, 'level': LEVEL,
            'shared_draws': 'Wearable-102 dry and wet share one set of person draws'}


# ---------------------------------------------------------------------------- harmonic gap (card 12)
def gap_block(docs, digests):
    ex, qc, protocol, fz, nr, ir, irm, tr, ap = (docs[k] for k in (
        'gap_export', 'gap_reference_qc', 'gap_protocol', 'gap_freeze', 'gap_numerical_review',
        'gap_interpretation_receipt', 'gap_interpretation_review', 'gap_text_receipt', 'gap_release_approval'))
    # The release approval binds every record this block reads; the reviews bind the aggregate.
    art = ap['artifact_sha256']
    for name, key in (('gap_protocol', 'protocol.json'), ('gap_freeze', 'execution-freeze.json'),
                      ('gap_export', 'results/Harmonic Gap Aggregate Results.json'),
                      ('gap_reference_qc', 'results/Reference Geometry QC Aggregate.json'),
                      ('gap_numerical_review', 'review/Independent Harmonic Gap Numerical Result Review.json'),
                      ('gap_interpretation_receipt', 'review/Interpretation Review Receipt.json'),
                      ('gap_text_receipt', 'review/Handoff Text Review Receipt.json')):
        bound(art[key], digests[name], f'harmonic gap approval {key}')
    require(ap['status'] == 'PASS' and ap['numerical_audit_status'] == 'PASS'
            and ap['independent_interpretation_and_text_review'] == 'PASS' and ap['primary_family_size'] == FAMILY_SIZE
            and ap['training_fits'] == 0 and ap['website_edited'] is False, 'harmonic gap: the release approval')
    bound(fz['protocol_sha256'], digests['gap_protocol'], 'harmonic gap freeze protocol')
    bound(nr['freeze_sha256'], digests['gap_freeze'], 'harmonic gap numerical review freeze')
    bound(nr['protocol_sha256'], digests['gap_protocol'], 'harmonic gap numerical review protocol')
    require(nr['status'] == 'PASS' and nr['failures'] == [] and nr['numerical_provenance_status'] == 'PASS',
            'harmonic gap: the numerical review did not pass')
    bound(ir['review_sha256'], digests['gap_interpretation_review'], 'harmonic gap interpretation receipt review')
    for key, name in (('protocol.json', 'gap_protocol'), ('execution-freeze.json', 'gap_freeze'),
                      ('results/Harmonic Gap Aggregate Results.json', 'gap_export')):
        bound(ir['bound_sha256'][key], digests[name], f'harmonic gap interpretation receipt {key}')
    require(ir['decision'] == 'PASS_BOUNDED_INTERPRETATION', 'harmonic gap: the interpretation review did not pass')
    ba = tr['bound_artifacts']
    for key, name in (('protocol.json', 'gap_protocol'), ('results/Harmonic Gap Aggregate Results.json', 'gap_export'),
                      ('review/Independent Harmonic Gap Numerical Result Review.json', 'gap_numerical_review'),
                      ('review/Handoff Text Review.md', 'gap_text_review')):
        bound(ba[key], digests[name], f'harmonic gap text receipt {key}')
    bound(tr['focused_rebind']['qc_json_sha256'], digests['gap_reference_qc'], 'harmonic gap text receipt QC')
    require(tr['decision'] == 'PASS_HANDOFF_TEXT' and tr['checks']['primary_family_intervals'] == FAMILY_SIZE
            and tr['focused_rebind']['paragraph_matches_qc_json'] is True, 'harmonic gap: the text review')

    # The export, primary by primary, against the numerical review's own reconstruction.
    pairs = [x for c in GAP_COHORTS.values() for x in numeric_leaves(nr['primary'][c], ex['cohorts'][c]['metrics'])]
    worst = float(max(abs(a - b) for _, a, b in pairs))
    require(len(pairs) == FAMILY_SIZE * 5 and worst <= TOL, f'harmonic gap: the export differs from the review by {worst!r}')

    # Interval method, family and endpoints from the frozen protocol.
    st = protocol['statistics']
    method = bootstrap({'BETA': st['bootstrap_seed_beta'], 'Wearable': st['bootstrap_seed_wearable']},
                       st['bootstrap_draws'], 'harmonic_gap')
    require(ex['bootstrap_draws'] == st['bootstrap_draws'] and st['all_intervals_percentile_linear'] is True
            and 'participant paired' in ex['intervals'] and st['nominal_descriptive_interval_quantiles'] == [0.025, 0.975],
            'harmonic gap: interval rule')
    require('both Wearable conditions' in st['bootstrap_generator'], 'harmonic gap: dry and wet do not share draws')
    q = st['primary_interval_quantiles']
    family_level = q[1] - q[0]
    close(family_level, 1 - FAMILY_ALPHA / FAMILY_SIZE, 'harmonic gap family level')
    close(q[0], FAMILY_ALPHA / FAMILY_SIZE / 2, 'harmonic gap family lower quantile')
    require(st['family_size'] == ex['primary_family_size'] == FAMILY_SIZE and 'Bonferroni' in st['primary_rule']
            and 'family99.444444%' in ex['intervals'], 'harmonic gap: the family')
    planned = [(p['cohort'], p['metric']) for p in st['primary_family']]
    want = [(c, m) for c in GAP_COHORTS.values()
            for m in (GAP_PRIMARY_GAP[1], GAP_PRIMARY[('B', 'J')], GAP_PRIMARY[('S', 'B')])]
    require(planned == want, 'harmonic gap: the family differs from the protocol')
    stated(docs, 'gap_protocol', '/statistics/zero_crossing', 'unresolved, not equivalence', 'zero crossing')

    datasets = protocol['datasets']
    beta, wear = datasets['BETA'], datasets['Wearable']
    ref = protocol['reference']
    window_s = ref['n_samples'] // ref['sample_rate_hz']
    require(ref['n_samples'] == 2 * ref['sample_rate_hz'] and window_s == 2 and ref['harmonics'] == 3 and beta['shape'][1] == wear['shape'][1] == 8,
            'harmonic gap: window, harmonics or channels')
    require(beta['people'] == 70 and wear['people'] == 102 and beta['classes'] == 40 and wear['classes'] == 12
            and len(beta['candidate_sets']) == 5 and {len(v) for v in beta['candidate_sets'].values()} == {8}
            and wear['conditions'] == {'0': 'dry', '1': 'wet'}, 'harmonic gap: the datasets changed')
    endpoints, people = {}, {}
    for e, c in GAP_COHORTS.items():
        co = ex['cohorts'][c]
        require(co['candidates'] == CANDIDATES[e] and co['trials'] == co['participants'] * co['trials_per_person'],
                f'harmonic gap {e}: candidates or trials')
        people[e] = co['participants']
        endpoints[e] = endpoint(e, co['trials'], 'BETA held-out 8-way' if e == 'u8' else f'Wearable-102 {e} 12-way')
        endpoints[e]['distractors'] = CANDIDATES[e] - 1
        endpoints[e]['role'] = 'primary'
    require(people == {'u8': beta['people'], 'dry': wear['people'], 'wet': wear['people']}
            and endpoints['u8']['decisions'] == 11200 and endpoints['dry']['decisions'] == 12240,
            'harmonic gap: people or decisions')
    require(ap['participant_counts'] == {'BETA': 70, 'Wearable': 102}
            and ap['trial_counts'] == {'BETA': 11200, 'Wearable': 24480}, 'harmonic gap: the approval counts')

    # The export's metric set, accounted for: selected, duplicate or declared not selected.
    known = (set(GAP_ARMS.values()) | set(GAP_PRIMARY.values()) | set(GAP_SECONDARY.values()) | set(GAP_DUPLICATES)
             | {GAP_PRIMARY_GAP[1], GAP_WIN} | set(GAP_STATS.values()) | set(GAP_ALLOCATION.values())
             | set(GAP_NOT_SELECTED))
    for c in GAP_COHORTS.values():
        require(set(ex['cohorts'][c]['metrics']) == known, f'harmonic gap {c}: the metric set changed')

    levels, contrasts, gap, codes = {}, {}, {}, {}
    family_members = []
    for e, c in GAP_COHORTS.items():
        m = ex['cohorts'][c]['metrics']
        for code, key in GAP_ARMS.items():
            lid = f'{code}/{e}'
            levels[lid] = level(m[key]['estimate'], m[key]['ci95'], people[e], f'harmonic gap {lid}')
            codes[lid] = ['#' + pointer('cohorts', c, 'metrics', key)]
        # The nine-comparison family, cohort by cohort in the protocol's order: G gap, J to B, B to S.
        g = m[GAP_PRIMARY_GAP[1]]
        gid = f'{GAP_PRIMARY_GAP[0]}/{e}'
        iv = interval(g['ci_family99_444'], g['estimate'], f'harmonic gap {gid}', lower=-3.0, upper=3.0)
        require(g['primary_positive'] is (iv[0] > 0), f'harmonic gap {gid}: primary_positive is not the family interval')
        gap[gid] = {'role': 'primary', 'estimate': g['estimate'], 'interval': iv, 'interval_level': family_level,
                    'unit': SCORE_DIFFERENCE, 'people': people[e],
                    'flags': {'interval_includes_zero': iv[0] <= 0 <= iv[1], 'family_member': True}}
        codes[gid] = ['#' + pointer('cohorts', c, 'metrics', GAP_PRIMARY_GAP[1])]
        family_members.append(gid)
        for (left, right), key in GAP_PRIMARY.items():
            cid = f'{left} minus {right}/{e}'
            x = m[key]
            c_ = contrast(x['estimate'], x['ci_family99_444'], 'primary', f'{left}/{e}', f'{right}/{e}', levels,
                          f'harmonic gap {cid}', ci_level=family_level)
            require(x['primary_positive'] is (c_['interval'][0] > 0), f'harmonic gap {cid}: primary_positive')
            c_['flags']['family_member'] = True
            contrasts[cid], codes[cid] = c_, ['#' + pointer('cohorts', c, 'metrics', key)]
            family_members.append(cid)
        for dup, key in GAP_DUPLICATES.items():
            require(m[dup]['estimate'] == m[key]['estimate'] and m[dup]['ci95'] == m[key]['ci95'],
                    f'harmonic gap {c}: {dup} is not {key}')
        for (left, right), key in GAP_SECONDARY.items():
            cid = f'{left} minus {right}/{e}'
            x = m[key]
            contrasts[cid] = contrast(x['estimate'], x['ci95'], 'secondary', f'{left}/{e}', f'{right}/{e}', levels,
                                      f'harmonic gap {cid}')
            codes[cid] = ['#' + pointer('cohorts', c, 'metrics', key)]
        # G and R in squared-correlation units, nominal 95%.
        for sid, key in GAP_STATS.items():
            x = m[key]
            diff = 'minus' in sid
            gid2 = f'{sid}/{e}'
            iv = interval(x['ci95'], x['estimate'], f'harmonic gap {gid2}', lower=-3.0, upper=3.0)
            gap[gid2] = {'role': 'secondary', 'estimate': x['estimate'], 'interval': iv, 'interval_level': LEVEL,
                         'unit': SCORE_DIFFERENCE if diff else SCORE, 'people': people[e],
                         'flags': {'interval_includes_zero': iv[0] <= 0 <= iv[1]}}
            codes[gid2] = ['#' + pointer('cohorts', c, 'metrics', key)]
        for q_ in ('G', 'R'):
            close(gap[f'{q_} true/{e}']['estimate'] - gap[f'{q_} mean distractor/{e}']['estimate'],
                  gap[f'{q_} true minus mean distractor/{e}']['estimate'], f'harmonic gap {q_} {e}: not a difference')
        require(all(gap[f'G {w}/{e}']['estimate'] >= 0 for w in ('true', 'mean distractor')),
                f'harmonic gap {e}: a negative mean G')
    require(len(family_members) == FAMILY_SIZE, 'harmonic gap: not nine family members')

    # G favours the true candidate in all three cohorts: the protocol's across-source rule.
    gap_lowers = [gap[f'{GAP_PRIMARY_GAP[0]}/{e}']['interval'][0] for e in GAP_COHORTS]
    family = {'comparisons': FAMILY_SIZE, 'adjustment': 'Bonferroni', 'interval_level': family_level,
              'members': family_members, 'all_gap_intervals_above_zero': all(v > 0 for v in gap_lowers),
              'resolved': [i for i in family_members
                           if not (contrasts.get(i) or gap[i])['flags']['interval_includes_zero']]}
    stated(docs, 'gap_protocol', '/statistics/question_confirmation', 'requires allthree cohort primary simultaneous',
           'across-cohort rule')

    win = {}
    for e, c in GAP_COHORTS.items():
        x = ex['cohorts'][c]['metrics'][GAP_WIN]
        win[e] = {'estimate': x['estimate'], 'interval': interval(x['ci95'], x['estimate'], f'harmonic gap win {e}'),
                  'interval_level': LEVEL, 'unit': WIN_FRACTION, 'label': 'pairwise win fraction (not an accuracy)',
                  'accuracy': False, 'ties': 'half credit for exact ties', 'distractors': CANDIDATES[e] - 1,
                  'people': people[e], 'export_codes': ['#' + pointer('cohorts', c, 'metrics', GAP_WIN)]}

    allocation = {'label': 'descriptive accounting', 'unit': DIFFERENCE,
                  'rule': 'the average of the two prespecified orders, J to B to S and J to JplusG to S'}
    for e, c in GAP_COHORTS.items():
        m = ex['cohorts'][c]['metrics']
        row = {}
        for part, key in GAP_ALLOCATION.items():
            x = m[key]
            iv = interval(x['ci95'], x['estimate'], f'harmonic gap allocation {part} {e}', lower=-1.0)
            row[part] = {'estimate': x['estimate'], 'interval': iv, 'interval_level': LEVEL,
                         'export_codes': ['#' + pointer('cohorts', c, 'metrics', key)]}
        lv = {k: levels[f'{k}/{e}']['estimate'] for k in GAP_ARMS}
        close(row['G']['estimate'], 0.5 * ((lv['JplusG'] - lv['J']) + (lv['S'] - lv['B'])), f'allocation G {e}')
        close(row['R']['estimate'], 0.5 * ((lv['B'] - lv['J']) + (lv['S'] - lv['JplusG'])), f'allocation R {e}')
        close(row['G']['estimate'] + row['R']['estimate'], contrasts[f'S minus J/{e}']['estimate'],
              f'allocation {e}: the two parts do not add to S minus J')
        allocation[e] = row
    stated(docs, 'gap_protocol', '/statistics/decision_outputs/3', 'descriptive path allocation only', 'allocation')

    # Decision changes on BETA held-out, as shares of all its decisions.
    edges = ex['cohorts'][GAP_COHORTS['u8']]['edges']
    require(set(edges) == set(GAP_EDGES), 'harmonic gap: the edge set changed')
    n = endpoints['u8']['decisions']
    transitions = {'endpoint': 'u8', 'unit': 'share of all decisions on the task', 'decisions': n,
                   'denominator': 'all 11,200 BETA held-out decisions', 'edges': {},
                   'export_codes': ['#' + pointer('cohorts', GAP_COHORTS['u8'], 'edges')]}
    require(n == 11200, 'harmonic gap: the BETA held-out decisions are not 11,200')
    for key, (frm, to) in GAP_EDGES.items():
        t = edges[key]
        require(t['trials'] == n and all(count(t[s]) and t[s] >= 0 for _, s in EDGE_SHARES),
                f'harmonic gap edge {key}: counts')
        require(t['rescue'] + t['harm'] + t['stable_correct'] + t['stable_wrong'] == n,
                f'harmonic gap edge {key}: the four outcomes do not cover the decisions')
        require(t['prediction_change'] >= t['rescue'] + t['harm'], f'harmonic gap edge {key}: changes')
        sh = {k: t[s] / n for k, s in EDGE_SHARES}
        net = f'{to} minus {frm}/u8'
        close(sh['wrong_to_right'] - sh['right_to_wrong'], contrasts[net]['estimate'],
              f'harmonic gap edge {key}: the net change is not {net}')
        close(sh['unchanged_right'] + sh['right_to_wrong'], levels[f'{frm}/u8']['estimate'],
              f'harmonic gap edge {key}: does not start from {frm}')
        close(sh['unchanged_right'] + sh['wrong_to_right'], levels[f'{to}/u8']['estimate'],
              f'harmonic gap edge {key}: does not end at {to}')
        transitions['edges'][f'{frm} to {to}'] = {'from': frm, 'to': to, **sh, 'net_equals': net}
    stated(docs, 'gap_protocol', '/statistics/decision_outputs/1', 'alltrial rescue/harm/stable counts', 'edges')

    # The identity: J is not in general B; R = B - J is reported beside G.
    sc = protocol['scores']
    for k, phrase in (('S_free', 'sum_h lambda_max(A_h)'), ('S_shared', 'lambda_max(sum_h A_h)'),
                      ('S_joint', 'equal to rawCCA rho squared'), ('G', 'S_free-S_shared >=0'),
                      ('R', 'S_shared-S_joint, signed'), ('Delta', 'S_free-S_joint=G+R'),
                      ('J_plus_G', 'predefined diagnostic alternate path')):
        stated(docs, 'gap_protocol', f'/scores/{k}', phrase, f'score {k}')
    require(sc['decision_arms'] == ['S_joint', 'S_shared', 'S_free', 'J_plus_G'], 'harmonic gap: decision arms')
    identity = {
        'scores': {'J': 'top eigenvalue of the joint-reference matrix: joint CCA squared',
                   'B': 'top eigenvalue of the summed per-harmonic matrices',
                   'S': 'sum over the three harmonics of each harmonic matrix’s top eigenvalue',
                   'JplusG': 'J plus G, a prespecified diagnostic score'},
        'quantities': {'G': 'S minus B, never below zero: the common-direction relaxation gap',
                       'R': 'B minus J, either sign: the reference-coupling residual',
                       'Delta': 'S minus J, equal to G plus R'},
        'joint_cca_equals_top_eigenvalue_of_sum': False,
        'reason': 'separate harmonic reference subspaces are generally not orthogonal over a finite window',
        'residual_reported_beside_gap': True,
        'limitation_key': 'joint_cca_not_top_eigenvalue_of_sum',
        'export_codes': ['gap_protocol#/scores'],
    }

    # The label-free reference check: counts only, never the candidates it names.
    src = qc['sources']
    require(qc['new_EEG_or_label_computation'] is False and 'label_free' in qc['status'], 'reference check: labels')
    reference_check = {'measure': 'cross-block Frobenius norm between the harmonic reference blocks',
                       'threshold': src['BETA']['threshold'], 'label_free': True, 'outcome_subgroups': False,
                       'limitation_key': 'reference_check_label_free', 'export_codes': []}
    for name, key in ((BETA, 'BETA'), (WEARABLE, 'Wearable')):
        s = src[key]
        require(s['threshold'] == 1e-10 and s['reference_full_rank'] is True
                and s['near_orthogonal_count'] + s['nonorthogonal_count'] == s['candidate_count']
                and len(s['near_orthogonal_frequencies_hz']) == s['near_orthogonal_count'],
                f'reference check {key}: counts')
        reference_check[name] = {'candidates': s['candidate_count'], 'at_or_below_threshold': s['near_orthogonal_count'],
                                 'above_threshold': s['nonorthogonal_count'], 'reference_full_rank': True}
        reference_check['export_codes'] += ['gap_reference_qc#' + pointer('sources', key, f)
                                            for f in ('candidate_count', 'near_orthogonal_count', 'nonorthogonal_count')]
    require((reference_check[BETA]['candidates'], reference_check[BETA]['at_or_below_threshold'])
            == (beta['classes'], 8) and reference_check[WEARABLE]['candidates'] == wear['classes'],
            'reference check: not 8 of 40 BETA candidates')

    design = {
        'datasets': {BETA: {'people': beta['people'], 'targets': beta['classes'], 'windows': endpoints['u8']['decisions'],
                            'frequency_rotations': len(beta['candidate_sets']), 'endpoints': ['u8']},
                     WEARABLE: {'people': wear['people'], 'targets': wear['classes'],
                                'windows_per_sensor': endpoints['dry']['decisions'], 'sensors': ['dry', 'wet'],
                                'endpoints': ['dry', 'wet']}},
        'endpoints': endpoints,
        'window_length_s': window_s,
        'channels': beta['shape'][1],
        'harmonics': ref['harmonics'],
        'training_fits': protocol['training_fits'],
        'scores': [{'code': c, 'training': NO_TRAINING, 'role': 'diagnostic' if c == 'JplusG' else 'score'}
                   for c in GAP_ARMS],
    }
    audit = ex['independent_audit']
    require(all(audit[c]['passed'] is True for c in GAP_COHORTS.values()), 'harmonic gap: the embedded audit')
    checks = {
        'release_approval': {'passed': True, 'artifacts_bound': len(art)},
        'numerical_review': {'passed': True, 'failures': len(nr['failures']),
                             'chunks': sum(v['chunks'] for v in nr['source_qc'].values()),
                             'primary_max_error': nr['primary_audit_max_abs_error'],
                             'oracle_rows_per_source': len(nr['numerical_oracle']['BETA']['rows']),
                             'export_equals_review': {'values': len(pairs), 'max_absolute_difference': worst,
                                                      'tolerance': TOL}},
        'interpretation_review': {'passed': True, 'required_limits': len(ir['required_limits'])},
        'handoff_text_review': {'passed': True, 'family_intervals_checked': tr['checks']['primary_family_intervals']},
        'embedded_independent_audit': {e: {'passed': True, 'max_absolute_error': audit[c]['max_absolute_error']}
                                       for e, c in GAP_COHORTS.items()},
    }
    return {
        'card': CARDS['harmonic_gap'][0], 'anchor': CARDS['harmonic_gap'][1],
        'source_sha256': digests['gap_export'],
        'review_sha256': digests['gap_interpretation_receipt'],
        'approval_sha256': digests['gap_release_approval'],
        'reference_qc_sha256': digests['gap_reference_qc'],
        'protocol_sha256': digests['gap_protocol'],
        'freeze_sha256': digests['gap_freeze'],
        'numerical_review_sha256': digests['gap_numerical_review'],
        'interpretation_review_sha256': digests['gap_interpretation_review'],
        'text_review_sha256': digests['gap_text_review'],
        'text_receipt_sha256': digests['gap_text_receipt'],
        'interval_method': dict(method, family={'comparisons': FAMILY_SIZE, 'adjustment': 'Bonferroni',
                                                'level': family_level}),
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('harmonic_gap', contrasts),
        'family': family,
        'gap': gap,
        'win_fractions': win,
        'allocation': allocation,
        'transitions': transitions,
        'identity': identity,
        'reference_check': reference_check,
        'undefined': [],
        'not_run': not_run('harmonic_gap', docs),
        'checks': checks,
        'limitations_keys': limitations('harmonic_gap', docs),
        'display_names': display_names('harmonic_gap', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- fixed decay (card 13)
def decay_block(docs, digests):
    ex, protocol, fz, er, au, rv, ap = (docs[k] for k in (
        'decay_export', 'decay_protocol', 'decay_freeze', 'decay_execution_review', 'decay_audit_receipt',
        'decay_review', 'decay_release_approval'))
    bound(ap['aggregate_sha256'], digests['decay_export'], 'fixed decay approval aggregate')
    bound(ap['protocol_sha256'], digests['decay_protocol'], 'fixed decay approval protocol')
    bound(ap['freeze_sha256'], digests['decay_freeze'], 'fixed decay approval freeze')
    bound(ap['interpretation_review_sha256'], digests['decay_review'], 'fixed decay approval review')
    bound(rv['aggregate_sha256'], digests['decay_export'], 'fixed decay review aggregate')
    bound(fz['protocol_sha256'], digests['decay_protocol'], 'fixed decay freeze protocol')
    bound(er['freeze_sha256'], digests['decay_freeze'], 'fixed decay execution review freeze')
    bound(er['protocol_sha256'], digests['decay_protocol'], 'fixed decay execution review protocol')
    require(ap['status'] == 'PASS' and ap['all_six_rows_reported'] is True and ap['no_fitted_models'] is True,
            'fixed decay: the release approval')
    require(rv['status'] == 'PASS' and rv['blocking_fixes'] == [], 'fixed decay: the interpretation review')
    require(er['status'] == 'PASS', 'fixed decay: the execution review')
    out = json.loads(au['stdout'])
    bound(out['freeze_sha256'], digests['decay_freeze'], 'fixed decay audit freeze')
    require(au['status'] == 'PASS' and au['returncode'] == 0 and out['status'] == 'PASS' and out['cohorts'] == 6
            and out['all_predictions_exact'] is True and out['bootstrap_endpoints_replayed'] is True,
            'fixed decay: the independent audit')

    st, sc = protocol['statistics'], protocol['scoring']
    method = bootstrap(st['seeds'], st['bootstrap_draws'], 'fixed_decay')
    require(ex['bootstrap_seed'] == st['seeds'] and ex['bootstrap_draws'] == st['bootstrap_draws']
            and st['percentile'] == 'numpy.quantile linear' and 'dry and wet share' in st['resampling'],
            'fixed decay: interval rule')
    margin = st['primary_margin_accuracy_fraction']
    require(margin == 0.005 and 'strictly within(-0.005,+0.005)' in st['primary_equivalence_rule']
            and st['primary'] == 'BETA-held8 harmonic decay minus flat accuracy', 'fixed decay: the primary rule')
    # One rule, n^-1.25 + 0.25, on the harmonics and on the sub-bands.
    require('(h**(-1.25)+0.25)*q_h' in sc['decay'] and 'h=1..3' in sc['decay'] and sc['flat'] == 'sum(q_h)'
            and '(band**(-1.25)+0.25)*rho_band**2' in sc['FBCCA_decay'] and 'bands1..7' in sc['FBCCA_decay']
            and sc['harmonic_columns'] == [0, 2, 4] and sc['harmonic_inputs_already_squared'] is True
            and sc['training_fits'] == 0 and sc['hyperparameter_search'] is False, 'fixed decay: the rule changed')
    fb = protocol['fbcca']
    require(fb['enabled'] is True and fb['bands'] == 7 and fb['harmonics'] == 5 and 'only pooling weights change'
            in fb['method'], 'fixed decay: the filter-bank construction')
    beta, wear = protocol['datasets']['BETA'], protocol['datasets']['Wearable']
    require(beta['people'] == 70 and wear['people'] == 102 and beta['classes'] == 40 and wear['classes'] == 12,
            'fixed decay: the datasets changed')
    require(set(ex['cohorts']) == {c for v in DECAY_COHORTS.values() for c in v.values()},
            'fixed decay: the cohort set changed')
    require(ex['units'].startswith('accuracy fractions'), 'fixed decay: units')

    levels, contrasts, codes, endpoints = {}, {}, {}, {}
    roles = {}
    for construction, cohorts in DECAY_COHORTS.items():
        for e, c in cohorts.items():
            co = ex['cohorts'][c]
            want_people = beta['people'] if DATASET_OF[e] == BETA else wear['people']
            require(co['participants'] == want_people, f'fixed decay {c}: people')
            ep = endpoint(e, co['trials'], {'u8': 'BETA held-out 8-way', 'seen_ba': 'BETA seen 32-way',
                                            'dry': 'Wearable-102 dry 12-way', 'wet': 'Wearable-102 wet 12-way'}[e])
            require(endpoints.setdefault(e, ep) == ep, f'fixed decay {e}: two endpoint records')
            for arm, key in DECAY_ARMS.items():
                lid = f'{construction}-{arm}/{e}'
                levels[lid] = level(co[key], None, co['participants'], f'fixed decay {lid}')
                codes[lid] = ['#' + pointer('cohorts', c, key)]
            cid = f'{construction}-DECAY minus {construction}-FLAT/{e}'
            primary = construction == 'H3' and e == 'u8'
            require((co['role'] == 'primary_equivalence') is primary
                    and (primary or co['role'] == 'nominal_descriptive'), f'fixed decay {c}: role')
            contrasts[cid] = contrast(co['decay_minus_flat'], co['ci95_descriptive'],
                                      'primary' if primary else 'secondary', f'{construction}-DECAY/{e}',
                                      f'{construction}-FLAT/{e}', levels, f'fixed decay {cid}')
            codes[cid] = ['#' + pointer('cohorts', c, 'decay_minus_flat'), '#' + pointer('cohorts', c, 'ci95_descriptive')]
            roles[cid] = co['role']
    require(endpoints['u8']['decisions'] == 11200 and endpoints['seen_ba']['decisions'] == 44800
            and endpoints['dry']['decisions'] == endpoints['wet']['decisions'] == 12240
            and st['BETA_held8_trials'] == 11200 and st['BETA_seen32_opportunities'] == 44800
            and st['Wearable_trials_per_condition'] == 12240, 'fixed decay: decisions')
    endpoints['seen_ba']['decisions_note'] = 'seen-frequency decision opportunities across the rotations'
    require(len(st['secondary']) == len(contrasts) - 1, 'fixed decay: the secondary contrasts differ from the protocol')

    # The single primary: approximate equivalence on BETA held-out, a 90% interval inside the margin.
    primary = 'H3-DECAY minus H3-FLAT/u8'
    p = ex['cohorts'][DECAY_COHORTS['H3']['u8']]
    ci90 = interval(p['ci90'], p['decay_minus_flat'], 'fixed decay 90% interval', lower=-1.0)
    require(ci90[0] >= contrasts[primary]['interval'][0] and ci90[1] <= contrasts[primary]['interval'][1],
            'fixed decay: the 90% interval is not inside the 95% interval')
    require(p['margin_accuracy_fraction'] == margin, 'fixed decay: the margin')
    met = -margin < ci90[0] and ci90[1] < margin
    require(p['equivalent_90ci'] is met and ap['primary_equivalence_supported'] is met,
            'fixed decay: the equivalence flag is not the interval')
    equivalence = {'contrast': primary, 'interval': ci90, 'interval_level': EQUIVALENCE_LEVEL, 'margin': margin,
                   'margin_unit': DIFFERENCE, 'rule': 'the paired 90% interval lies strictly inside the margin',
                   'met': met, 'interval_beyond_margin': ci90[1] < -margin or ci90[0] > margin,
                   'export_codes': ['#' + pointer('cohorts', DECAY_COHORTS['H3']['u8'], k)
                                    for k in ('ci90', 'margin_accuracy_fraction', 'equivalent_90ci')]}
    contrasts[primary]['flags']['equivalence_met'] = met

    design = {
        'datasets': {BETA: {'people': beta['people'], 'targets': beta['classes'], 'endpoints': ['u8', 'seen_ba']},
                     WEARABLE: {'people': wear['people'], 'targets': wear['classes'], 'sensors': ['dry', 'wet'],
                                'endpoints': ['dry', 'wet']}},
        'endpoints': endpoints,
        'rule': {'weight': 'n^-1.25 + 0.25', 'exponent': 1.25, 'offset': 0.25, 'flat': 'every weight 1',
                 'origin': 'the sub-band weights of the published filter-bank CCA recipe'},
        'constructions': {
            'H3': {'pooled': 'the three harmonic-local leading squared canonical correlations', 'terms': 3,
                   'n': 'harmonic number', 'codes': ['H3-FLAT', 'H3-DECAY'], 'endpoints': list(DECAY_COHORTS['H3'])},
            'FBCCA': {'pooled': 'the squared canonical correlations of the seven filter-bank sub-bands', 'terms': fb['bands'],
                      'harmonics_per_band': fb['harmonics'], 'n': 'sub-band number',
                      'codes': ['FBCCA-FLAT', 'FBCCA-DECAY'], 'endpoints': list(DECAY_COHORTS['FBCCA'])},
        },
        'harmonic_and_sub_band_weights_are_different_operations': True,
        'each_contrast_changes_weights_within_one_construction': True,
        'training_fits': sc['training_fits'],
    }
    stated(docs, 'decay_protocol', '/fbcca/method', 'Published M3 recipe', 'published recipe')
    checks = {
        'release_approval': {'passed': True},
        'interpretation_review': {'passed': True, 'blocking_fixes': len(rv['blocking_fixes'])},
        'execution_review': {'passed': True},
        'independent_audit': {'passed': True, 'cohorts': out['cohorts'], 'decisions_replayed_exactly': True,
                              'bootstrap_endpoints_replayed': True},
    }
    return {
        'card': CARDS['fixed_decay'][0], 'anchor': CARDS['fixed_decay'][1],
        'source_sha256': digests['decay_export'],
        'review_sha256': digests['decay_review'],
        'approval_sha256': digests['decay_release_approval'],
        'protocol_sha256': digests['decay_protocol'],
        'freeze_sha256': digests['decay_freeze'],
        'execution_review_sha256': digests['decay_execution_review'],
        'audit_receipt_sha256': digests['decay_audit_receipt'],
        'interval_method': dict(method, equivalence={'level': EQUIVALENCE_LEVEL, 'margin': margin}),
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('fixed_decay', contrasts),
        'equivalence': equivalence,
        'undefined': [],
        'not_run': not_run('fixed_decay', docs),
        'checks': checks,
        'limitations_keys': limitations('fixed_decay', docs),
        'display_names': display_names('fixed_decay', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- rising weights (card 14)
def rise_block(docs, digests):
    ex, protocol, fz, er, au, rv, ap = (docs[k] for k in (
        'rise_export', 'rise_protocol', 'rise_freeze', 'rise_execution_review', 'rise_audit_receipt', 'rise_review',
        'rise_release_approval'))
    bound(ap['aggregate_sha256'], digests['rise_export'], 'rising approval aggregate')
    bound(ap['protocol_sha256'], digests['rise_protocol'], 'rising approval protocol')
    bound(ap['freeze_sha256'], digests['rise_freeze'], 'rising approval freeze')
    bound(ap['numerical_review_sha256'], digests['rise_audit_receipt'], 'rising approval numerical review')
    bound(ap['interpretation_review_sha256'], digests['rise_review'], 'rising approval interpretation review')
    bound(rv['aggregate_sha256'], digests['rise_export'], 'rising review aggregate')
    bound(rv['result_audit_receipt_sha256'], digests['rise_audit_receipt'], 'rising review audit')
    bound(au['freeze_sha256'], digests['rise_freeze'], 'rising audit freeze')
    bound(fz['protocol_sha256'], digests['rise_protocol'], 'rising freeze protocol')
    bound(er['freeze_sha256'], digests['rise_freeze'], 'rising execution review freeze')
    require(ap['status'] == 'PASS' and ap['no_fits'] is True, 'rising: the release approval')
    require(rv['status'] == 'PASS' and rv['blockers'] == [], 'rising: the interpretation review')
    require(au['status'] == 'PASS' and er['status'] == 'PASS', 'rising: the audit or the execution review')

    # The export, leaf by leaf, against the independent audit's own reconstruction.
    pairs = list(numeric_leaves(au['cohorts'], ex['cohorts']))
    worst = float(max(abs(a - b) for _, a, b in pairs))
    require(worst <= TOL, f'rising: the export differs from the audit by {worst!r}')

    st, sc, w = protocol['statistics'], protocol['scoring'], protocol['weights']
    method = bootstrap(st['seeds'], st['bootstrap_draws'], 'rising_weights')
    require(ex['bootstrap_seed'] == st['seeds'] and ex['bootstrap_draws'] == st['bootstrap_draws']
            and st['percentile'] == 'linear' and 'paired Wearable dry/wet sharedraws' in st['resampling'],
            'rising: interval rule')
    require(sc['arms'] == ['flat', 'rising_literal', 'rising_exact'] and sc['harmonic_columns'] == [0, 2, 4]
            and sc['input_already_squared_correlation'] is True and sc['weights_candidate_independent'] is True
            and sc['new_fits'] == 0 and sc['tuning'] is False, 'rising: the arms changed')
    exact = w['rounding_sensitivity_exact']
    # The exact profile is the cumulative fixed-decay weight, normalised to its first term (the protocol's formula).
    d = [n ** -1.25 + 0.25 for n in (1, 2, 3)]
    for i, v in enumerate(exact):
        close(v, sum(d[:i + 1]) / d[0], f'rising: exact weight {i + 1} is not the protocol formula')
    require(w['primary_literal'] == [1.0, 1.5, 1.9] and w['formula_exact'].startswith('cumsum(n**(-1.25)+0.25'),
            'rising: the weights changed')
    beta, wear = protocol['datasets']['BETA'], protocol['datasets']['Wearable']
    require(beta['people'] == 70 and wear['people'] == 102 and beta['classes'] == 40 and wear['classes'] == 12,
            'rising: the datasets changed')
    require(set(ex['cohorts']) == set(RISE_COHORTS.values()), 'rising: the cohort set changed')

    levels, contrasts, codes, endpoints = {}, {}, {}, {}
    for e, c in RISE_COHORTS.items():
        co = ex['cohorts'][c]
        want_people = beta['people'] if DATASET_OF[e] == BETA else wear['people']
        require(co['participants'] == want_people, f'rising {c}: people')
        endpoints[e] = endpoint(e, co['trials'], {'u8': 'BETA held-out 8-way', 'seen_ba': 'BETA seen 32-way',
                                                  'dry': 'Wearable-102 dry 12-way', 'wet': 'Wearable-102 wet 12-way'}[e])
        require((co['role'] == 'primary_positive_benefit') is (e == 'u8'), f'rising {c}: role')
        for arm in RISE_ARMS:
            x = co['arm_levels'][arm]
            close(x['estimate'], co['accuracy'][arm], f'rising {c} {arm}: the two accuracy fields differ')
            lid = f'{arm}/{e}'
            levels[lid] = level(x['estimate'], x['ci95'], co['participants'], f'rising {lid}')
            codes[lid] = ['#' + pointer('cohorts', c, 'arm_levels', arm)]
        require(set(co['contrasts']) == set(RISE_CONTRASTS.values()), f'rising {c}: the contrast set changed')
        for (left, right), key in RISE_CONTRASTS.items():
            x = co['contrasts'][key]
            cid = f'{left} minus {right}/{e}'
            role = ('primary' if e == 'u8' else 'secondary') if left == 'literal_rise' else 'rounding_check'
            contrasts[cid] = contrast(x['estimate'], x['ci95'], role, f'{left}/{e}', f'{right}/{e}', levels,
                                      f'rising {cid}')
            codes[cid] = ['#' + pointer('cohorts', c, 'contrasts', key, k) for k in ('estimate', 'ci95')]
    require(endpoints['u8']['decisions'] == 11200 and endpoints['seen_ba']['decisions'] == 44800
            and endpoints['dry']['decisions'] == endpoints['wet']['decisions'] == 12240, 'rising: decisions')
    endpoints['seen_ba']['decisions_note'] = 'seen-frequency decision opportunities across the rotations'

    # The single prespecified criterion: the paired 95% interval lies wholly above zero.
    primary = 'literal_rise minus flat/u8'
    met = contrasts[primary]['interval'][0] > 0
    require(st['primary'] == 'BETA held8 literal rising minus flat accuracy'
            and 'lower endpoint>0' in st['primary_benefit'], 'rising: the primary rule')
    require(ex['cohorts']['BETA-held8']['supports_primary_benefit'] is met and au['supports_primary_benefit'] is met
            and ap['primary_95CI_lower_positive'] is met, 'rising: the criterion flags are not the interval')
    close(ap['literal_BETA_gain_pp'], 100 * contrasts[primary]['estimate'], 'rising: the approval gain', tol=1e-9)
    criterion = {'contrast': primary, 'rule': 'the paired 95% interval lies wholly above zero', 'met': met,
                 'prespecified': True, 'export_codes': codes[primary]}
    contrasts[primary]['flags']['criterion_met'] = met

    design = {
        'datasets': {BETA: {'people': beta['people'], 'targets': beta['classes'], 'endpoints': ['u8', 'seen_ba']},
                     WEARABLE: {'people': wear['people'], 'targets': wear['classes'], 'sensors': ['dry', 'wet'],
                                'endpoints': ['dry', 'wet']}},
        'endpoints': endpoints,
        'pooled': 'the three harmonic-local leading squared canonical correlations',
        'weights': {'flat': [1.0, 1.0, 1.0], 'literal_rise': list(w['primary_literal']), 'exact_rise': list(exact)},
        'exact_profile': 'cumulative sum of n^-1.25 + 0.25 over n = 1 to 3, divided by its first term',
        'same_vector_for_every_candidate': True,
        'training_fits': sc['new_fits'],
    }
    rec = au['cohorts']
    checks = {
        'release_approval': {'passed': True},
        'interpretation_review': {'passed': True, 'blockers': len(rv['blockers'])},
        'execution_review': {'passed': True},
        'independent_audit': {'passed': True, 'cohorts': len(rec),
                              'export_equals_audit': {'values': len(pairs), 'max_absolute_difference': worst,
                                                      'tolerance': TOL}},
    }
    return {
        'card': CARDS['rising_weights'][0], 'anchor': CARDS['rising_weights'][1],
        'source_sha256': digests['rise_export'],
        'review_sha256': digests['rise_review'],
        'approval_sha256': digests['rise_release_approval'],
        'protocol_sha256': digests['rise_protocol'],
        'freeze_sha256': digests['rise_freeze'],
        'execution_review_sha256': digests['rise_execution_review'],
        'audit_receipt_sha256': digests['rise_audit_receipt'],
        'interval_method': method,
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': contrast_limitations('rising_weights', contrasts),
        'criterion': criterion,
        'undefined': [],
        'not_run': not_run('rising_weights', docs),
        'checks': checks,
        'limitations_keys': limitations('rising_weights', docs),
        'display_names': display_names('rising_weights', levels),
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- one set of scores
def same_scores(blocks, docs):
    """What cards 5, 7, 9 and 11 print and these cards reuse is one set of scores: equal doubles, named once."""
    gap, decay, rise = (blocks[s]['levels'] for s in STUDIES)
    rel = docs['released']
    require(rel['release_id'] == RELEASED_ID, 'the released SSVEP file is another release')
    diag, card7 = rel['studies']['cca_diagnostics']['levels'], rel['studies']['wearable_transfer']['levels']
    coh, bd = docs['coherence_export']['arms'], docs['practical_bd_export']['arms']['w500-c8/FBCCA-M3-N7-H5']
    pairs = [
        # (level, the same double elsewhere, its name)
        (gap['J/u8'], diag['CCA-RAW/u8']['estimate'], f'{RELEASED_ID} cca_diagnostics CCA-RAW/u8'),
        (gap['J/u8'], coh['CCA-RAW']['held8']['mean'], 'coherence CCA-RAW held8'),
        (gap['J/dry'], card7['CCA-RAW/dry']['estimate'], f'{RELEASED_ID} wearable_transfer CCA-RAW/dry'),
        (gap['J/wet'], card7['CCA-RAW/wet']['estimate'], f'{RELEASED_ID} wearable_transfer CCA-RAW/wet'),
        (gap['S/u8'], coh['RAW-HARM-SUM']['held8']['mean'], 'coherence RAW-HARM-SUM held8'),
        (decay['H3-FLAT/seen_ba'], coh['RAW-HARM-SUM']['seen32']['mean'], 'coherence RAW-HARM-SUM seen32'),
        (rise['flat/seen_ba'], coh['RAW-HARM-SUM']['seen32']['mean'], 'coherence RAW-HARM-SUM seen32'),
        (decay['FBCCA-DECAY/u8'], bd['held8']['mean'], 'practical B/D FBCCA-M3-N7-H5 2 s 8 electrodes held8'),
        (decay['FBCCA-DECAY/seen_ba'], bd['seen32']['mean'], 'practical B/D FBCCA-M3-N7-H5 2 s 8 electrodes seen32'),
    ]
    # The coherence aggregate's seen32 is route 3's seen_ba: its CCA is card 5's to the last bit.
    require(coh['CCA-RAW']['seen32']['mean'] == diag['CCA-RAW/seen_ba']['estimate'],
            'the coherence seen32 is not route 3\'s seen_ba')
    for e in ('u8', 'dry', 'wet'):
        pairs += [(decay[f'H3-FLAT/{e}'], gap[f'S/{e}']['estimate'], f'harmonic_gap S/{e}'),
                  (rise[f'flat/{e}'], gap[f'S/{e}']['estimate'], f'harmonic_gap S/{e}')]
    pairs += [(rise['flat/seen_ba'], decay['H3-FLAT/seen_ba']['estimate'], 'fixed_decay H3-FLAT/seen_ba')]
    for lv, value, name in pairs:
        close(lv['estimate'], value, f'{name}: not the same score', tol=0.0)
        lv.setdefault('same_estimate_as', []).append(name)
    return len(pairs)


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
        require(not (len(value) > 3 and all(number(v) for v in value)), f'{trail}: a list of values (per frequency?)')
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        if re.fullmatch(r'[0-9a-f]{64}', value):
            return
        require(not REFUSED_TEXT.search(value), f'{trail}: refused text {value!r}')
        require(not EXTRA_REFUSED_TEXT.search(value), f'{trail}: refused text {value!r}')
        require(not VERSION_LABEL.search(value), f'{trail}: a version label {value!r}')
        require(not RANKING.search(value), f'{trail}: a ranking word {value!r}')
        require(not re.search(r'(?<![\d.])5{2}(?![\d])', value), f'{trail}: refused figure {value!r}')
    elif isinstance(value, float):
        require(math.isfinite(value) and abs(value - 11 / 20) > 1e-12 and abs(value - 55) > 1e-9,
                f'{trail}: refused value {value!r}')


def withheld_values(docs):
    """Doubles the three aggregates hold that no block selects, for the leak check here and in the assembler: the
    ratio table, the Delta and fixed-distractor metrics, the nominal intervals of the family contrasts and the
    reference geometry, less any double that a selected source field also holds."""
    held, shown = set(_floats(docs['decay_export']['retrospective_gap_ratio'])), set()
    for c in GAP_COHORTS.values():
        m = docs['gap_export']['cohorts'][c]['metrics']
        held |= set(_floats({k: m[k] for k in GAP_NOT_SELECTED}))
        held |= set(_floats([m[k]['ci95'] for k in (GAP_PRIMARY_GAP[1], *GAP_PRIMARY.values(), *GAP_DUPLICATES)]))
        shown |= set(_floats([m[k] for k in (*GAP_ARMS.values(), *GAP_SECONDARY.values(), *GAP_STATS.values(), GAP_WIN,
                                              *GAP_ALLOCATION.values())]))
        shown |= set(_floats([[m[k]['estimate'], m[k]['ci_family99_444']]
                              for k in (GAP_PRIMARY_GAP[1], *GAP_PRIMARY.values())]))
    held |= set(_floats({k: v for s in docs['gap_reference_qc']['sources'].values() for k, v in s.items()
                         if k != 'threshold'}))
    for co in docs['decay_export']['cohorts'].values():
        shown |= set(_floats([co.get(k) for k in ('accuracy_flat', 'accuracy_decay', 'decay_minus_flat',
                                                  'ci95_descriptive', 'ci90', 'margin_accuracy_fraction')]))
    for co in docs['rise_export']['cohorts'].values():
        shown |= set(_floats([co['accuracy'], co['arm_levels'],
                              [[x['estimate'], x['ci95']] for x in co['contrasts'].values()]]))
    return held - shown - {0.0, 1.0}


def build_blocks(pins=None) -> dict:
    """The three weighting blocks, keyed harmonic_gap, fixed_decay and rising_weights."""
    docs, digests = load(pins)
    for study, h in HANDOFF_CONTEXT.items():
        ap = docs[h['bound_by']]
        handoff = (ap['artifact_sha256']['Harmonic Gap Mechanism Results Handoff.md'] if study == 'harmonic_gap'
                   else ap['handoff_sha256'])
        bound(handoff, h['bound_sha256'], f'{study} handoff')
    blocks = {'harmonic_gap': gap_block(docs, digests), 'fixed_decay': decay_block(docs, digests),
              'rising_weights': rise_block(docs, digests)}
    same_scores(blocks, docs)
    for name, block in blocks.items():
        require(all(f in block for f in BLOCK_FIELDS), f'{name}: a block field is missing')
        require(block['source_sha256'] == digests[EXPORT_OF[name]] and block['review_sha256'] == digests[REVIEW_OF[name]]
                and block['approval_sha256'] == digests[APPROVAL_OF[name]], f'{name}: another source or review')
        require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']) | set(block.get('gap', {})),
                f'{name}: export codes do not cover the levels, contrasts and gap statistics')
        for c in block['contrasts'].values():
            require(c['left'] in block['levels'] and c['right'] in block['levels'], f'{name}: a contrast side is no level')
    validate_public(blocks)
    scrub_check(blocks)
    leaked = withheld_values(docs) & set(_floats(blocks))
    require(not leaked, f'a withheld value reached a block: {sorted(leaked)[:3]}')
    return blocks


def _floats(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from _floats(x)
    elif isinstance(v, list):
        for x in v:
            yield from _floats(x)
    elif isinstance(v, float):
        yield v


if __name__ == '__main__':
    built = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'limitations': len(b['limitations_keys'])} for s, b in built.items()}, indent=2))
