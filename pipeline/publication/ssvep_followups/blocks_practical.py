"""The practical-settings block of the SSVEP follow-ups release: card 11 (queue rows 33 and 30).

Filter-bank CCA, shorter windows and fewer electrodes: the practical suite's modules B and D on BETA, read from their
audited aggregate and turned into one study block for `ssvep-followups-update.json`, which its assembler puts under
`studies`, with the CPU component measurements of D25 as its `cpu_components` record:

- `practical_settings`: five fixed pipelines (CCA, the harmonic sum, the top-three ridge, the eigenvalue head and
  untrained filter-bank CCA with seven Chebyshev sub-bands and five harmonics) in six prospectively declared cells
  (0.5, 1 and 2 s windows inside the authors' 3-100 Hz preprocessing, cropped before any new filtering; eight or four
  recorded electrodes); 60 levels on the held-out 8-way and seen 32-way tasks, the seen-32 levels descriptive; all 41
  held-out contrasts with each study's own primary or secondary role (seven primary: B's filter-bank CCA against the
  harmonic sum at 2 s and 8 electrodes, D's eigenvalue head against the harmonic sum in every cell), grouped into
  method, window and electrode contrasts; 2,000 draws with seed 20261015. `grid` keeps the prospective grid order
  (cells, then methods), never a score order. The 2 s / 8 electrode cell reproduces card 10's module A values and
  card 5's CCA bit for bit; `reproduces` names each pair and both roles, which differ.
- `cpu_components`: warm single-thread CPU wall-clock medians [min, max] of three measured calls (one warm-up
  excluded) for six components in all six cells at batch sizes 1 and 8, from the component timing aggregate. They are
  components and are never summed; the block carries no host, processor, system or runtime label (D25), and its label
  says what the figures are not: sensor-to-decision or online latency.

Release status is read from `state/BD-release-approval.json` (which binds the aggregate, both independent reviews,
the text receipts and the handoff) and `results/Component Timing Release Approval.json`, never from the aggregate's
own `release_status`. Every number is the source's own double: nothing is rounded, rescaled or recomputed; accuracy
units stay fractions and timings stay milliseconds. Every level and contrast is checked against the approved B/D
handoff's tables, and every timing group against the approved timing handoff's grid, at the four decimals they print.
The pinned protocols, receipts and handoffs carry private storage paths and the host's name, so they are read and
checked here, never copied; only named fields are selected from them.

The block has the fields of the blocks of the 2026-10-20 release (see blocks_cca.py), with these differences:
- a level id is `<cell>/<code>/<endpoint>` (the aggregate's own `<cell>/<code>` spelling, endpoints `u8` and
  `seen_ba`), so the code is the id's second part; `display_names` maps codes;
- a contrast id is `<left> minus <right>/u8` with `<left>` and `<right>` in the aggregate's spelling;
  `contrast_groups` lists the method, window and electrode contrasts in the protocol's order and `design.primary`
  names B's and D's primaries;
- `qualifiers` holds the 0.5 s electrode qualifier (methods whose four-electrode mean exceeds their eight-electrode
  mean at 0.5 s; no paired interval exists for these pairs, so no figure is carried);
- `undefined` holds filter-bank CCA against the top-three ridge at 2 s / 8 electrodes, which has no paired interval;
- `design.fbcca` holds the recipe and the other filter-bank recipe the site reports (route 3's S11);
- a `cpu_components` export code is a selector, `timing_aggregate#component_summaries[cell=…][batch=…][component=…]`,
  with the site component code (COMPONENTS maps it to the aggregate's): a list index would be a bare number in the
  text, and one of them is the token the release's rule on the commenter's figure refuses.

    python3 pipeline/publication/ssvep_followups/blocks_practical.py   # builds and prints the counts; writes nothing
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
_B = f'{_P}/raw_followup'
_T = 'research/product_direction_20261020/timing'
_C = 'research/decision_route3_coherence_eigen_20261020'
PINS = {
    'bd_aggregate': {'path': f'{_B}/review/BD Aggregate Results.json',
                     'sha256': '21495d28ed65606aed7e8b41b3c2e565ac4789aaa43109557d1e662bf0c94fd7'},
    'bd_approval': {'path': f'{_P}/state/BD-release-approval.json',
                    'sha256': 'e6c4bb2d48aa0b4d1473f63582182c78d336faf86251790fa61d237a09602e01'},
    'bd_numerical_review': {'path': f'{_B}/review/Independent B D Supplemental Numerical and Provenance Review.md',
                            'sha256': 'ab12e5096fcde5d7ca3e37dd1c60340bf59d4fe25adc6dbe89b4f093facef23c'},
    'bd_audit_receipt': {'path': f'{_B}/review/Independent B D Complete Vectorized Audit Receipt.json',
                         'sha256': '576abf521a85769ab37e5f5e33484ab62cd86a9b4947ce20de80c4ed812c5c22'},
    'bd_interpretation_review': {'path': f'{_B}/review/Independent B D Interpretation Review.md',
                                 'sha256': '3e61084b1c444ccc030eba582f827080204754ea03e5dc4f735d0475e5554864'},
    'bd_text_review': {'path': f'{_B}/review/B D English Text Review Receipt.json',
                       'sha256': 'c54b968c63d8f8e58e4f81adea78accc714ed5aac6972105a6d8ac10defe8fd0'},
    'bd_text_rebind': {'path': f'{_B}/review/Final B D Handoff Text Rebind.json',
                       'sha256': 'd965f94f155f199205ce015afd3231a68fa14cd20a6c193f9ac4477e04a106db'},
    'bd_handoff': {'path': f'{_P}/Practical SSVEP B and D Results Handoff.md',
                   'sha256': '1b30a3e1d5dc7fe96cf199b63c05c85a711dc87ef90fcb3131b61ede19e728f5'},
    'bd_protocol': {'path': f'{_B}/bd-mac-protocol.json',
                    'sha256': '5963bbf7a0efb2267238a581b73170df3afa5861d950cf3a48abe58e04989aef'},
    'bd_freeze': {'path': f'{_B}/bd-mac-freeze.json',
                  'sha256': '9483f1536604f27ab97cfa80ea47976f667db1cb9382fed021d024187f659ba2'},
    # The filter-bank core the protocol pins by hash: the Chebyshev type I design (cheb1ord, cheby1) it realises.
    'fbcca_core': {'path': f'{_P}/scripts/fbcca_core.py',
                   'sha256': '803d62deb56a0210b1180d8ed97337f241631441b144b8c6fd99d9a2e99cd48d'},
    # Cross-checks, never copied: card 10's module A, card 9's study and the released file (cards 5 and 6).
    'ac_summary': {'path': f'{_P}/evidence/AC Release Audit Summary.json',
                   'sha256': 'daaa8dedbc8bcbf220b4c7788632ff71405827154f82ad0ef396c8590b682923'},
    'coherence_aggregate': {'path': f'{_C}/evidence/Completed Aggregate Results.json',
                            'sha256': '9ee6cc3a9a46c76faeec00b3d7b57a5fb66993389f85d001a443507becc6717d'},
    'released': {'path': 'site/src/data/new-ssvep-frequencies-update.json',
                 'sha256': '197028bdc4dadd9713f6d408bb64204147fdfe39a686e7e119e4988aaf863ee0'},
    # The other filter-bank recipe on the site: route 3's S11, as its protocol defines it and its file serves it.
    'route3_protocol': {'path': 'research/decision_route3_20261007/protocol.json',
                        'sha256': '922dc0848f58f379bd68f99a4c2d982253a9e7fa8693eed54466f0f9d368a223'},
    'route3': {'path': 'site/src/data/questions-in-language-update.json',
               'sha256': '2583b5958c24e02898929c354e16653e50e33704aaaee37927e158f9d72d01dd'},
    # D25: the CPU component measurements and their release records.
    'timing_aggregate': {'path': f'{_T}/results/Component Timing Aggregates.json',
                         'sha256': 'b0d16d93103ac66427fb62b7b0505e106c4e31db04bbd8d349fe80959b4b5f57'},
    'timing_approval': {'path': f'{_T}/results/Component Timing Release Approval.json',
                        'sha256': '362049bbec64325f6c26af012834d3aaf77e9327512082f55dbc99e27e02e553'},
    'timing_review': {'path': f'{_T}/review/Independent Component Timing Result Review.md',
                      'sha256': 'bdf86512e63a7e015ce792986de8a4a0bb909fb3812c83eb086b578946834b05'},
    'timing_receipt': {'path': f'{_T}/review/Independent Component Timing Result Receipt.json',
                       'sha256': '87ed43b2dd9945d0e3f05232fb7a95ebbe5e5c1b51be2669a2092037f1d7edfb'},
    'timing_handoff': {'path': f'{_T}/CPU Component Timing Results Handoff.md',
                       'sha256': '4790aa0d4470c8c2228ad6057060c429f25c3fbc13212a2a6cff0331702ea940'},
    'timing_protocol': {'path': f'{_T}/execution/protocol.frozen.json',
                        'sha256': '95eecd8b34fd8158c2e6f605ce03c344f8cf87c2800e7798392a33b501c93385'},
}
TEXT_PINS = {'bd_numerical_review', 'bd_interpretation_review', 'bd_handoff', 'fbcca_core', 'timing_review',
             'timing_handoff'}
SERVED = {'released': 'site/public/data/new-ssvep-frequencies-update.json',     # same bytes as the src copies
          'route3': 'site/public/data/questions-in-language-update.json'}
RELEASED_FILE, RELEASED_ID = 'new-ssvep-frequencies-update.json', 'new-ssvep-frequencies-update-20261020'
ROUTE3_FILE, ROUTE3_ID = 'questions-in-language-update.json', 'questions-in-language-update-20261008'
# For the release manifest only: each handoff is context and a cross-check of printed values, never a copy source.
HANDOFF_CONTEXT = {
    'practical_settings': {'bound_sha256': '1b30a3e1d5dc7fe96cf199b63c05c85a711dc87ef90fcb3131b61ede19e728f5',
                           'bound_by': 'bd_approval'},
    'cpu_components': {'bound_sha256': '4790aa0d4470c8c2228ad6057060c429f25c3fbc13212a2a6cff0331702ea940',
                       'bound_by': 'timing_approval'},
}
# The approval's artifact keys (repo-relative to the suite) for the pins it binds.
APPROVAL_ARTIFACTS = {
    'raw_followup/review/BD Aggregate Results.json': 'bd_aggregate',
    'raw_followup/review/Independent B D Supplemental Numerical and Provenance Review.md': 'bd_numerical_review',
    'raw_followup/review/Independent B D Complete Vectorized Audit Receipt.json': 'bd_audit_receipt',
    'raw_followup/review/Independent B D Interpretation Review.md': 'bd_interpretation_review',
    'raw_followup/review/B D English Text Review Receipt.json': 'bd_text_review',
    'raw_followup/review/Final B D Handoff Text Rebind.json': 'bd_text_rebind',
    'Practical SSVEP B and D Results Handoff.md': 'bd_handoff',
}
TIMING_ARTIFACTS = {
    'CPU Component Timing Results Handoff.md': 'timing_handoff',
    'results/Component Timing Aggregates.json': 'timing_aggregate',
    'review/Independent Component Timing Result Review.md': 'timing_review',
    'review/Independent Component Timing Result Receipt.json': 'timing_receipt',
    'execution/protocol.frozen.json': 'timing_protocol',
}
STUDY = 'practical_settings'
STUDIES = (STUDY,)
CARD, ANCHOR = 11, 'practical-settings'
BLOCK_FIELDS = ('source_sha256', 'review_sha256', 'interval_method', 'levels', 'contrasts', 'undefined', 'not_run',
                'checks', 'limitations_keys', 'display_names', 'export_codes')

ENDPOINTS = {'u8': 'held8', 'seen_ba': 'seen32'}      # site id -> aggregate spelling (route 3's spelling of the tasks)
PROPORTION, DIFFERENCE = 'proportion', 'difference of proportions'
NO_TRAINING, DETERMINISTIC = 'no training', 'deterministic fit'
SEED, DRAWS, LEVEL = 20261015, 2000, 0.95
METHOD = 'paired person bootstrap, percentile interval'
TOL = 1e-12
ANCHOR_CELL = 'w500-c8'                                # the B cell: 2 s and 8 electrodes, card 10's setting
LEARNED = ('RAW-LEAD3-RIDGE', 'EIG-RAW6-RIDGE')
RAW_FAMILY = ('CCA-RAW-H3', 'RAW-HARM-SUM-H3', 'RAW-LEAD3-RIDGE', 'EIG-RAW6-RIDGE')
FBCCA = 'FBCCA-M3-N7-H5'

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
FBCCA_NAME = 'filter-bank CCA (seven sub-bands)'
DISPLAY_NAMES = {
    'CCA-RAW-H3': 'CCA (no training)',          # the released name of the same scores (card 5); not in the plan's key
    'RAW-HARM-SUM-H3': 'harmonic sum (no training)',
    'RAW-LEAD3-RIDGE': 'top-three ridge',
    'EIG-RAW6-RIDGE': 'eigenvalue head',
    FBCCA: FBCCA_NAME,
}
NAME_KEY = (
    ('harmonic sum (no training)', 'RAW-HARM-SUM-H3'),
    ('eigenvalue head', 'EIG-RAW6-RIDGE'),
    ('top-three ridge', 'RAW-LEAD3-RIDGE'),
    (FBCCA_NAME, FBCCA),
    ('CCA (no training)', 'CCA-RAW-H3 in the practical B/D export: the same scores as CCA-RAW at 2 s and 8 electrodes'),
)
# card 10 / card 5 / card 9 twins of the 2 s / 8 electrode cell (this code -> the code there)
A_TWIN = {'CCA-RAW-H3': 'CCA-RAW', 'RAW-HARM-SUM-H3': 'RAW-HARM-SUM', 'RAW-LEAD3-RIDGE': 'RAW-LEAD3-RIDGE',
          'EIG-RAW6-RIDGE': 'EIG-RAW'}
RECIPE = {
    'en': 'filter-bank CCA (seven Chebyshev sub-bands, five harmonics), our SciPy realisation of the published recipe',
    'zh': '滤波器组 CCA（七个切比雪夫子带、五个谐波），我们按已发表方法用 SciPy 实现',
}
CPU_LABEL = {
    'en': 'components; not sensor-to-decision or online latency',
    'zh': '各组件的计时；不是从传感器到决策的延迟，也不是在线延迟',
}
# The six timed components, in the protocol's order: aggregate code -> (site code, site name).
COMPONENTS = {
    'native_crop_validation_copy': ('crop', 'crop, validation and copy'),
    'raw_window_filter_float32': ('raw_filter', 'raw 6–80 Hz filter'),
    'raw_geometry_shared_superset': ('raw_geometry', 'shared raw CCA geometry'),
    'fbcca_filter_geometry_score': ('fbcca', 'filter-bank CCA: filter, geometry and scores'),
    'cached_features_fixed_f0_r0_ridge_lead3': ('top3_readout', 'top-three ridge readout on cached statistics'),
    'cached_features_fixed_f0_r0_ridge_eig6': ('eigenvalue_readout', 'eigenvalue head readout on cached statistics'),
}
# The approved handoff's grid labels for the same components (for the printed-value cross-check only).
HANDOFF_COMPONENT = {
    'native_crop_validation_copy': 'Crop / validation / copy',
    'raw_window_filter_float32': 'Raw 6–80 Hz filter',
    'raw_geometry_shared_superset': 'Shared raw CCA/eigenfeature geometry',
    'fbcca_filter_geometry_score': 'FBCCA filter / geometry / scores',
    'cached_features_fixed_f0_r0_ridge_lead3': 'Cached-feature LEAD3 readout',
    'cached_features_fixed_f0_r0_ridge_eig6': 'Cached-feature EIG6 readout',
}

# ---------------------------------------------------------------------------- limitations, not run, declared edits
# key -> (pinned input, JSON pointer, phrase the field must contain); pointer '' is a whole text record.
_IR = 'bd_interpretation_review'
LIMITATION_SOURCES = {
    'same_cohort_follow_up': (_IR, '', 'not untouched external confirmation'),
    'unadjusted_intervals': (_IR, '', 'Neither seven primary tests nor the 41-test family receives a familywise '
                                      'discovery guarantee'),
    'no_equivalence_margin': (_IR, '', 'Crossing zero means unresolved, not equivalence'),
    'seen_descriptive': (_IR, '', 'their arm intervals are descriptive'),
    'complete_pipelines': (_IR, '', 'The FBCCA advantage therefore compares complete pipelines'),
    'observation_window_not_latency': (_IR, '', 'not strictly causal acquisition-to-decision latency'),
    'author_preprocessing_inherited': (_IR, '', 'It cannot undo the inherited author 3–100 Hz zero-phase '
                                                'preprocessing/downsampling'),
    'recorded_subset_not_headset': (_IR, '', 'It does not validate a physical four-channel headset'),
    'eight_not_always_better': (_IR, '', 'Small reversed mean differences in the shortest raw-family cells also '
                                         'preclude an unqualified statement that eight channels always help'),
    'one_learning_contrast_positive': (_IR, '', 'Only one of the six D primary learning contrasts is nominal positive'),
    'candidates_supplied': (_IR, '', 'Known candidate-frequency sin/cos references are available at test time'),
    'no_forty_way_claim': (_IR, '', 'no 40-way performance or online spelling claim follows'),
    'not_foundation_model_evidence': (_IR, '', 'Its stronger result is no evidence for a foundation model'),
    'not_bitwise_matlab': ('bd_protocol', '/design/preprocessing/fbcca/scope', 'not bitwise MATLAB replication'),
    'other_recipe_on_site': ('route3_protocol', '/secondary_contrasts/S11', '5 sub-bands'),
}
CPU_LIMITATION_SOURCES = {
    'components_never_summed': ('timing_handoff', '', 'Do not add medians of separately timed components and present '
                                                      'the sum as measured end-to-end latency'),
    'not_sensor_to_decision': ('timing_handoff', '', 'not sensor-to-decision latency or an online BCI test'),
    'shared_geometry_counted_once': ('timing_handoff', '', 'must not be counted four times'),
    'readouts_exclude_extraction': ('timing_handoff', '', 'Those readouts exclude feature extraction'),
    'forty_candidates': ('timing_handoff', '', 'this timing computes 40 candidate scores'),
    'three_warm_repetitions': ('timing_handoff', '', 'Only three measured repetitions per fixed cell/batch/component '
                                                     'are available'),
    'wall_times_used': ('timing_handoff', '', 'Use wall times for those small components'),
    'one_head_not_average': ('timing_handoff', '', 'not a 35-head ensemble'),
    'unmeasured_stages': ('timing_handoff', '', 'decision/argmax and 35-head ensembling are unmeasured'),
    'batch_amortised_not_lone_trial': ('timing_handoff', '', 'it is not the latency of a lone arriving trial'),
    'anchor_not_chosen_by_speed': ('timing_handoff', '', 'not a fastest-case selection'),
    'no_hardware_recommendation': ('timing_handoff', '', 'No timing confidence intervals, broad hardware comparison or '
                                                         'hardware recommendation is established'),
}
# Contrast kind or method pair -> limitation key, the caveat that sits next to that evidence.
CONTRAST_LIMITATIONS = {
    ('method', FBCCA, 'RAW-HARM-SUM-H3'): 'complete_pipelines',
    ('method', FBCCA, 'CCA-RAW-H3'): 'complete_pipelines',
    ('method', 'EIG-RAW6-RIDGE', 'RAW-HARM-SUM-H3'): 'one_learning_contrast_positive',
    ('window',): 'observation_window_not_latency',
    ('electrodes',): 'recorded_subset_not_headset',
}
NOT_RUN_SOURCES = {
    'minimum practical margin': (_IR, '', 'No minimum practical margin or deployment threshold was frozen'),
    'ablation of the filter bank, the harmonic count and the pooling': (
        _IR, '', 'Mechanistic attribution would need new predeclared ablations'),
    'online performance or information transfer rate': (_IR, '', 'online performance or ITR'),
    'a physical four-electrode headset': (_IR, '', 'It does not validate a physical four-channel headset'),
}
UNDEFINED_SOURCE = (_IR, '', 'Not preregistered/reported')
DECLARED_EDITS = {
    'practical_settings': (
        'release_status not selected; state/BD-release-approval.json and the reviews it binds supersede it',
        'interpretation, multiplicity and population strings not selected; the page writes its own copy from '
        'limitations_keys',
        'above_zero, below_zero and interpretation restated as interval_includes_zero and direction, both derived '
        'from the interval and checked against the source labels',
        'global prediction seal and fit-count summary not selected; the aggregate is pinned by its own hash',
        'held8 and seen32 named u8 and seen_ba in ids (route 3 spelling of the same tasks)',
        'training-free pipelines carry "no training" and ridge heads "deterministic fit" in place of seeds',
        'whole-evaluation and audit run times not selected; they are not latency',
        'the descriptive 2 s / 8 electrode difference of filter-bank CCA against the top-three ridge not selected: '
        'no paired interval was registered (undefined)',
    ),
    'cpu_components': (
        'cpu_ms_per_call and cpu_ms_per_trial not selected: zero readings at this scale; the handoff says to use wall '
        'times',
        'host, processor, core count, operating system, storage and runtime versions not selected (D25: no host label)',
        'accounting, quiescence, bindings, launcher and audit seconds not selected',
        'component codes renamed to site codes; the head the readouts used is described, its fold and rotation are '
        'not named',
        'wall_ms_per_trial published as wall_ms_amortised (batch cost divided by the batch size)',
    ),
}

# ---------------------------------------------------------------------------- what no block may carry
REFUSED_KEYS = set(FORBIDDEN_KEYS) | {
    'pid', 'job', 'private_root', 'rows', 'privacy', 'status', 'release_status', 'at_utc', 'updated_at', 'path',
    'handoff_path', 'interpretation', 'multiplicity', 'population', 'thread_bet', 'accounting', 'quiescence',
    'bindings', 'cpu_ms_per_call', 'cpu_ms_per_trial', 'total', 'sum', 'end_to_end'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_seed', 'prediction', 'probabilit', 'feature', 'private', 'path', 'host', 'elapsed',
                         'seconds', 'timing', 'checkpoint', 'device', 'subject', '_utc', 'canary', 'fifty', '055',
                         'latency', 'total', 'summed_ms', 'end_to_end')
REFUSED_TEXT = re.compile(                                 # blocks_cca's rule, plus /dev, the model and host words
    CCA_REFUSED_TEXT.pattern + r'|/dev\b|\bJev\b'
    r'|threadripper|ryzen|\bamd\b|(?<![\d.])7965(?!\d)|epyc|xeon|\bintel\b|linux|ubuntu|darwin|macos|\bmac\b|arm64'
    r'|ext4|\bsda\b'
    r'|(?:python|numpy|scipy)\s*\d|logical cores|physical cores', re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
RANKING = re.compile(r'\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|state[- ]of[- ]the[- ]art|superior'
                     r'|significan|outperform|fastest', re.IGNORECASE)
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
    return f'{x * 100:.4f}'


def s4(x):
    return f'{x * 100:+.4f}'


def direction(iv):
    return 'above zero' if iv[0] > 0 else 'below zero' if iv[1] < 0 else 'unresolved'


def code_of(lid):
    return lid.split('/')[1]


def seeds_of(code):
    return DETERMINISTIC if code in LEARNED else NO_TRAINING


def level(metric, people, seeds, label):
    require(isinstance(metric, dict) and number(metric.get('mean')) and isinstance(metric.get('ci95'), list)
            and len(metric['ci95']) == 2, f'{label}: no mean and interval')
    return {'estimate': metric['mean'], 'interval': interval(*metric['ci95'], metric['mean'], label), 'unit': PROPORTION,
            'people': people, 'seeds': seeds, 'origin': 'new'}


def contrast(c, role, levels, people, label):
    """A paired contrast, refused unless it is the difference of its two levels and its source flags agree."""
    left, right = f'{c["a"]}/u8', f'{c["b"]}/u8'
    est = c['mean']
    close(est, levels[left]['estimate'] - levels[right]['estimate'], f'{label} is not the difference of its levels')
    iv = interval(*c['ci95'], est, label, lower=-1.0)
    d = direction(iv)
    require(c['above_zero'] == (iv[0] > 0) and c['below_zero'] == (iv[1] < 0), f'{label}: sign flags')
    require(c['interpretation'] == {'above zero': 'nominal_positive', 'below zero': 'nominal_negative',
                                    'unresolved': 'unresolved'}[d], f'{label}: the source reads {c["interpretation"]!r}')
    seeds = DETERMINISTIC if code_of(left) in LEARNED or code_of(right) in LEARNED else NO_TRAINING
    return {'role': role, 'left': left, 'right': right, 'estimate': est, 'interval': iv, 'unit': DIFFERENCE,
            'people': people, 'seeds': seeds, 'flags': {'interval_includes_zero': iv[0] <= 0 <= iv[1], 'direction': d}}


def not_run(docs):
    rows = []
    for item, (name, ptr, phrase) in NOT_RUN_SOURCES.items():
        stated(docs, name, ptr, phrase, f'B/D not run {item!r}')
        rows.append({'item': item, 'run_in': None})
    return rows


def keys_from(sources, docs, label):
    keys = []
    for key, (name, ptr, phrase) in sources.items():
        stated(docs, name, ptr, phrase, f'{label} limitation {key}')
        keys.append(key)
    return keys


# ---------------------------------------------------------------------------- the binding chain
def check_bindings(docs, digests):
    """The B/D approval binds the aggregate, protocol, freeze, both reviews, the text receipts and the handoff; the
    timing approval binds its aggregate, review, receipt, protocol and handoff; the two share one prediction seal."""
    ap, agg, fz = docs['bd_approval'], docs['bd_aggregate'], docs['bd_freeze']
    require(ap['status'] == 'PASS' and ap['scientific_result_release_approved'] is True, 'B/D: not approved')
    bound(ap['aggregate_sha256'], digests['bd_aggregate'], 'B/D approval aggregate')
    bound(ap['protocol_sha256'], digests['bd_protocol'], 'B/D approval protocol')
    bound(ap['freeze_sha256'], digests['bd_freeze'], 'B/D approval freeze')
    for key, pin in APPROVAL_ARTIFACTS.items():
        bound(ap['artifact_sha256'][key], digests[pin], f'B/D approval {pin}')
    bound(ap['artifact_sha256']['Practical SSVEP B and D Results Handoff.md'],
          HANDOFF_CONTEXT['practical_settings']['bound_sha256'], 'B/D handoff')
    nra = ap['numeric_release_audit']
    require(nra['status'] == 'PASS' and nra['contrasts'] == 41 and nra['arms'] == 30 and nra['new_fits'] == 0
            and nra['private_records_exported'] is False, 'B/D: the numerical release audit')
    bound(nra['aggregate_sha256'], digests['bd_aggregate'], 'B/D numerical audit aggregate')
    bound(nra['protocol_sha256'], digests['bd_protocol'], 'B/D numerical audit protocol')
    require(ap['global_prediction_seal_sha256'] == nra['seal_sha256'] == agg['global_prediction_seal_sha256'],
            'B/D: another prediction seal')
    bound(fz['protocol_sha256'], digests['bd_protocol'], 'B/D freeze protocol')
    rc = docs['bd_audit_receipt']
    require(rc['status'] == 'PASS' and rc['process_exit_code'] == 0, 'B/D: the audit receipt')
    bound(rc['review_sha256'], digests['bd_numerical_review'], 'B/D audit receipt review')
    bound(rc['freeze_sha256'], digests['bd_freeze'], 'B/D audit receipt freeze')
    tr, rb = docs['bd_text_review'], docs['bd_text_rebind']
    require(tr['decision'].startswith('PASS') and tr['actionable_interpretation_issues'] == [], 'B/D: the text review')
    bound(tr['bindings']['raw_followup/review/BD Aggregate Results.json'], digests['bd_aggregate'], 'B/D text review')
    require(rb['decision'] == 'PASS_final_text_rebind' and rb['actionable_issues'] == [], 'B/D: the text rebind')
    bound(rb['bindings']['Practical SSVEP B and D Results Handoff.md'], digests['bd_handoff'], 'B/D text rebind')
    nr, ir = docs['bd_numerical_review'], docs['bd_interpretation_review']
    require('PASS for independent numerical and provenance release review' in nr, 'B/D: the numerical review verdict')
    for h in (digests['bd_aggregate'], digests['bd_protocol'], digests['bd_freeze'], agg['global_prediction_seal_sha256']):
        require(h in nr, f'B/D: the numerical review does not name {h[:12]}')
    require('Decision: interpretation PASS' in ir, 'B/D: the interpretation review verdict')
    require('exact ordered agreement of all 41 aggregate contrasts with the frozen roster' in ir,
            'B/D: the roster check')
    fb = docs['bd_protocol']['design']['preprocessing']['fbcca']
    bound(fb['reviewed_core_sha256'], digests['fbcca_core'], 'B/D filter-bank core')
    require(digests['fbcca_core'] in docs['bd_protocol']['import_hashes'].values(), 'B/D: the core is not imported')

    tp, tg, trc, tpr = (docs[k] for k in ('timing_approval', 'timing_aggregate', 'timing_receipt', 'timing_protocol'))
    require(tp['status'] == 'PASS' and tp['method_whole_pipeline_latencies_measured'] == 0
            and tp['no_private_records_published'] is True, 'timing: not approved')
    for key, pin in TIMING_ARTIFACTS.items():
        bound(tp['artifacts_sha256'][key], digests[pin], f'timing approval {pin}')
    bound(tp['artifacts_sha256']['CPU Component Timing Results Handoff.md'],
          HANDOFF_CONTEXT['cpu_components']['bound_sha256'], 'timing handoff')
    require(tp['coverage'] == {'groups': 72, 'calls': 288, 'warmups_per_group': 1, 'measured_repeats_per_group': 3},
            'timing: coverage')
    require(tg['status'] == 'PASS' and all(v is True for v in tg['checks'].values())
            and tg['component_summary_count'] == 72 and tg['method_timing_summary_count'] == 0, 'timing: aggregate')
    require(trc['status'] == 'PASS' and all(v is True for v in trc['checks'].values()), 'timing: the review receipt')
    require({a['sha256'] for a in trc['local_artifacts']} == {digests['timing_aggregate'], digests['timing_review']},
            'timing: the receipt binds other files')
    require('PASS for aggregate component timing release' in docs['timing_review'], 'timing: the review verdict')
    # The timed code and heads are the B/D run's: one prediction seal, one filter-bank core.
    require(tpr['head_seal_sha256'] == agg['global_prediction_seal_sha256'], 'timing: another head seal')
    require(digests['fbcca_core'] in tpr['input_sha256'].values(), 'timing: another filter-bank core')
    require(tpr['threads'] == 1 and tpr['warmups'] == 1 and tpr['repetitions'] == 3 and tpr['batch_sizes'] == [1, 8]
            and len(tpr['candidates_hz']) == 40, 'timing: the frozen workload')
    proto_cells = [c['id'] for c in docs['bd_protocol']['design']['cells']]
    require([c['id'] for c in tpr['cells']] == proto_cells and tpr['methods'] == docs['bd_protocol']['design']['methods'],
            'timing: not the B/D cells and methods')
    for name in ('released', 'route3'):
        require(docs[name]['release_id'] == {'released': RELEASED_ID, 'route3': ROUTE3_ID}[name],
                f'{name}: another release')


# ---------------------------------------------------------------------------- design
def fbcca_recipe(docs):
    fb = docs['bd_protocol']['design']['preprocessing']['fbcca']
    core = docs['fbcca_core']
    require(fb['subbands'] == 7 and fb['harmonics'] == 5 and len(fb['pass_lows_hz']) == 7, 'filter-bank recipe')
    require(fb['weights'] == 'n**(-1.25)+0.25, n1..7' and fb['aggregation'] == 'sum(weights*rho**2)',
            'filter-bank weights')
    require('cheb1ord' in core and 'cheby1(order, .5, wn, btype="bandpass", fs=fs, output="sos")' in core
            and 'sosfiltfilt' in core and fb['realization_ripple_db'] == 0.5, 'filter-bank: not a Chebyshev type I design')
    s11 = docs['route3_protocol']['secondary_contrasts']['S11']
    require('5 sub-bands' in s11 and 'Butterworth' in s11 and 'Nh=5' in s11, 'route 3 S11: another recipe')
    r3 = resolve(docs['route3'], '/results/questions-in-language/secondary/parts/SSVEP-L0-secondary/levels/S11 FBCCA levels')
    require(number(r3['u8']['estimate']), 'route 3 S11: no held-out level')
    return {
        'code': FBCCA,
        'description': dict(RECIPE),
        'sub_bands': fb['subbands'],
        'filter': 'Chebyshev type I, forward-backward, second-order sections',
        'pass_band_low_edges_hz': list(fb['pass_lows_hz']),
        'pass_band_high_edge_hz': fb['pass_high_hz'],
        'harmonics': fb['harmonics'],
        'sub_band_weights': 'n^-1.25 + 0.25 for sub-band n = 1 to 7',
        'score': 'weighted sum of squared canonical correlations',
        'trained_head': False,
        'realisation': 'our SciPy realisation of the published recipe',
        'bitwise_replication_of_the_matlab_code': False,
        'input': 'the authors’ preprocessed window, cropped before its own filtering',
        'other_recipe_on_site': {'release_id': ROUTE3_ID, 'code': 'S11', 'sub_bands': 5, 'filter': 'Butterworth',
                                 'harmonics': 5, 'page': '/topics/questions-in-language/',
                                 'export_codes': [f'{ROUTE3_FILE}#' + pointer(
                                     'results', 'questions-in-language', 'secondary', 'parts', 'SSVEP-L0-secondary',
                                     'levels', 'S11 FBCCA levels', 'u8'),
                                     'route3_protocol#' + pointer('secondary_contrasts', 'S11')]},
    }


def design_of(docs, people):
    d = docs['bd_protocol']['design']
    inp, ch, sf, pre = d['input'], d['channels'], d['source_fitting'], d['preprocessing']
    require(inp['people'] == people == 70 and inp['blocks_per_person'] == 4 and len(inp['frequencies_hz']) == 40
            and inp['source_rate_hz'] == 250, 'B/D: the BETA input')
    require('Author3-100Hz zero-phase filtered/downsampled' in inp['source_preprocessing'], 'B/D: author preprocessing')
    require('crop before every new noncausal operation' in pre['common_support'], 'B/D: crop before filtering')
    stated(docs, _IR, '', 'avoids borrowing later real samples during the new project filtering', 'B/D crop first')
    require(pre['raw_family']['methods'] == list(RAW_FAMILY)
            and pre['raw_family']['filter'].startswith('scipy.signal.butter(4,[6,80],fs=250')
            and 'sosfiltfilt' in pre['raw_family']['filter'] and d['geometry']['H3'] == 3, 'B/D: the raw family')
    require(sf['participant_folds'] == 7 and sf['source_people'] == 60 and sf['source_candidates'] == 32
            and sf['source_trials_per_fit'] == 7680 and sf['hyperparameter_tuning'] is False
            and sf['historical_head_reuse'] is False, 'B/D: source fitting')
    require([ch['eight'][i] for i in ch['four_indices_in_eight']] == ch['four'], 'B/D: the four are not of the eight')
    cohort = docs['released']['cohort']
    require((cohort['people'], cohort['targets'], cohort['windows']) == (people, 40, 11200), 'B/D: another cohort')
    endpoints = {e['id']: e for e in docs['released']['endpoints']}
    return {
        'dataset': {'name': 'BETA', 'people': people, 'targets': cohort['targets'], 'windows': cohort['windows'],
                    'recording_blocks': inp['blocks_per_person'], 'person_folds': sf['participant_folds'],
                    'frequency_rotations': cohort['frequency_rotations'], 'rate_hz': inp['source_rate_hz'],
                    'amplitude': 'as stored', 'same_cohort_as': 'cards 1 to 6 and 8 to 10'},
        'preprocessing': {'author_band_hz': [3, 100], 'author_zero_phase': True,
                          'crop_before_new_filtering': True, 'new_filtering_borrows_later_samples': False},
        'cells': [{'id': c['id'], 'window_s': c['seconds'], 'samples': c['samples'], 'electrodes': c['channels']}
                  for c in d['cells']],
        'electrodes': {'eight': list(ch['eight']), 'four': list(ch['four']), 'four_are_recorded_subset_of_eight': True},
        'endpoints': {'u8': {'candidate_count': endpoints['u8']['candidates'], 'chance': endpoints['u8']['chance'],
                             'role': 'primary and secondary contrasts'},
                      'seen_ba': {'candidate_count': endpoints['seen_ba']['candidates'],
                                  'chance': endpoints['seen_ba']['chance'], 'role': 'descriptive'}},
        'source_per_fit': {'people': sf['source_people'], 'frequencies': sf['source_candidates'],
                           'windows': sf['source_trials_per_fit']},
        'fits': {'main': sf['main_fits'], 'independent_refits': sf['independent_refits'],
                 'hyperparameter_tuning': False, 'reused_heads': False},
        'raw_family': {'codes': list(RAW_FAMILY), 'band_hz': [6, 80], 'filter': 'Butterworth order 4, forward-backward',
                       'harmonics': d['geometry']['H3']},
        'fbcca': fbcca_recipe(docs),
        'methods': [{'code': m, 'training': ('ridge fitted on source people' if m in LEARNED else NO_TRAINING),
                     'family': 'filter bank' if m == FBCCA else 'raw'} for m in d['methods']],
    }


# ---------------------------------------------------------------------------- the block
def planned_contrasts(protocol):
    """(left, right, role, kind) in the protocol's order, the aggregate's `<cell>/<code>` spelling."""
    st = protocol['design']['statistics']
    out = []
    for c in st['primary_contrasts']:
        out.append((f'{c["cell"]}/{c["left"]}', f'{c["cell"]}/{c["right"]}', 'primary', 'method', c['module']))
    for c in st['secondary_contrasts']:
        if 'cell' in c:
            out.append((f'{c["cell"]}/{c["left"]}', f'{c["cell"]}/{c["right"]}', 'secondary', 'method', None))
        else:
            kind = 'window' if c['left_cell'][:4] != c['right_cell'][:4] else 'electrodes'
            out.append((f'{c["left_cell"]}/{c["method"]}', f'{c["right_cell"]}/{c["method"]}', 'secondary', kind, None))
        require(c['candidate_set'] == 'held8', 'B/D: a contrast on another task')
    return out


def contrast_limitation(kind, left, right):
    key = (CONTRAST_LIMITATIONS.get((kind,)) if kind != 'method'
           else CONTRAST_LIMITATIONS.get((kind, left.split('/')[1], right.split('/')[1])))
    return key


def handoff_tables(docs, levels, contrasts, cells, methods):
    """Every level and contrast at the four decimals the approved handoff prints, row by row."""
    text = docs['bd_handoff']
    for e in ENDPOINTS:
        for c in cells:
            row = (f'| {c["seconds"]:g} s / {c["channels"]} | '
                   + ' | '.join(f4(levels[f'{c["id"]}/{m}/{e}']['estimate']) for m in methods) + ' |')
            require(row in text, f'B/D {c["id"]} {e}: the approved handoff does not print {row!r}')
    for cid, c in contrasts.items():
        a, b = c['left'][:-3], c['right'][:-3]
        label = {'above zero': 'nominal_positive', 'below zero': 'nominal_negative', 'unresolved': 'unresolved'}
        row = (f'| {c["role"]} | {a} | {b} | {s4(c["estimate"])} | [{s4(c["interval"][0])}, {s4(c["interval"][1])}] '
               f'| {label[c["flags"]["direction"]]} |')
        require(row in text, f'{cid}: the approved handoff does not print {row!r}')


def reproduced(docs, levels, contrasts):
    """The 2 s / 8 electrode cell is card 10's module A, bit for bit, and its CCA card 5's; roles stay each study's."""
    A = docs['ac_summary']['verified_A_aggregate']
    card5 = docs['released']['studies']['cca_diagnostics']['levels']
    coh = docs['coherence_aggregate']
    out = []
    for code, twin in A_TWIN.items():
        for e, src in ENDPOINTS.items():
            lid = f'{ANCHOR_CELL}/{code}/{e}'
            m = A['arms'][twin][src]
            require(levels[lid]['estimate'] == m['mean'] and levels[lid]['interval'] == m['ci95'],
                    f'{lid} is not card 10’s {twin}/{e}')
            out.append({'here': lid, 'card': 10, 'study': 'harmonic_pooling', 'there': f'{twin}/{e}'})
            if code == 'CCA-RAW-H3':
                require(levels[lid]['estimate'] == card5[f'CCA-RAW/{e}']['estimate']
                        and levels[lid]['interval'] == card5[f'CCA-RAW/{e}']['interval'], f'{lid} is not card 5’s CCA')
                out.append({'here': lid, 'card': 5, 'study': 'cca_diagnostics', 'there': f'CCA-RAW/{e}'})
    require(len(A['contrasts']) == 6, 'card 10: module A has another contrast family')
    roles_a = ['primary'] * 3 + ['secondary'] * 3          # module A's protocol order (checked in blocks_pooling)
    for i, c in enumerate(A['contrasts']):
        a = next((k for k, v in A_TWIN.items() if v == c['a']), None)
        b = next((k for k, v in A_TWIN.items() if v == c['b']), None)
        cid = f'{ANCHOR_CELL}/{a} minus {ANCHOR_CELL}/{b}/u8'
        if a and b and cid in contrasts:
            here = contrasts[cid]
            require(here['estimate'] == c['mean'] and here['interval'] == c['ci95'], f'{cid} is not card 10’s contrast')
            out.append({'here': cid, 'card': 10, 'study': 'harmonic_pooling', 'there': f'{c["a"]} minus {c["b"]}/u8',
                        'role_here': here['role'], 'role_there': roles_a[i]})
    cid = f'{ANCHOR_CELL}/EIG-RAW6-RIDGE minus {ANCHOR_CELL}/RAW-HARM-SUM-H3/u8'
    k, c9 = next((i, c) for i, c in enumerate(coh['contrasts']) if (c['a'], c['b'], c['metric']) ==
                 ('EIG-RAW', 'RAW-HARM-SUM', 'held8'))
    require(contrasts[cid]['estimate'] == c9['mean'] and contrasts[cid]['interval'] == c9['ci95'],
            f'{cid} is not card 9’s contrast')
    out.append({'here': cid, 'card': 9, 'study': 'coherence_eigen', 'there': 'EIG-RAW minus RAW-HARM-SUM/u8',
                'role_here': contrasts[cid]['role'], 'export_code': 'coherence_aggregate#' + pointer('contrasts', k)})
    require(any(r.get('role_here') != r.get('role_there') for r in out if r['card'] == 10 and 'role_here' in r),
            'B/D: the plan says the roles differ from card 10’s; they do not')
    return out


def practical_block(docs, digests):
    agg, proto = docs['bd_aggregate'], docs['bd_protocol']
    st = proto['design']['statistics']
    require(agg['aggregate_only'] is True, 'B/D: the aggregate is not aggregate-only')
    require(agg['participant_count'] == st['participant_units'] == 70
            and agg['rotations'] == st['rotations_per_person'] == 5, 'B/D: people')
    require(agg['bootstrap_draws'] == st['bootstrap_draws'] == DRAWS
            and agg['bootstrap_seed'] == st['bootstrap_seed'] == SEED, 'B/D: bootstrap')
    require(st['interval'] == 'Nominal paired95percentile', 'B/D: the interval rule')
    stated(docs, 'bd_numerical_review', '', f'exact default_rng({SEED}) 2000×70 resampling indices', 'B/D draws reviewed')
    stated(docs, 'bd_numerical_review', '', '41 contrast means and percentile intervals', 'B/D percentile reviewed')
    require(st['primary_count'] == agg['primary_contrasts'] == 7 and st['secondary_count'] == agg['secondary_contrasts']
            == 34, 'B/D: the contrast counts')
    require(st['minimum_practical_margin'] is None and st['best_cell_selection'] is False
            and st['external_confirmation'] is False, 'B/D: margin or selection')
    require(agg['main_fits'] == proto['design']['source_fitting']['main_fits'] == 420
            and agg['independent_refits'] == 420, 'B/D: fits')
    people = agg['participant_count']
    cells = proto['design']['cells']
    methods = tuple(proto['design']['methods'])
    require(set(methods) == set(DISPLAY_NAMES) and methods[-1] == FBCCA and methods[:-1] == RAW_FAMILY, 'B/D: methods')
    require(proto['design']['B_is_cell'].startswith(ANCHOR_CELL), 'B/D: B is another cell')
    grid_keys = [f'{c["id"]}/{m}' for c in cells for m in methods]
    require(list(agg['arms']) == grid_keys, 'B/D: the aggregate is not in the prospective grid order')

    levels, codes = {}, {}
    for key in grid_keys:
        code = key.split('/')[1]
        for e, src in ENDPOINTS.items():
            lid = f'{key}/{e}'
            levels[lid] = level(agg['arms'][key][src], people, seeds_of(code), f'B/D {lid}')
            codes[lid] = ['#' + pointer('arms', key, src)]
    grid = {'order': 'prospective', 'cells': [c['id'] for c in cells], 'methods': list(methods),
            'table': {e: [[f'{c["id"]}/{m}/{e}' for m in methods] for c in cells] for e in ENDPOINTS},
            'roles': {'u8': 'primary and secondary contrasts', 'seen_ba': 'descriptive'}}

    planned = planned_contrasts(proto)
    require([(c['a'], c['b'], c['role']) for c in agg['contrasts']] == [p[:3] for p in planned],
            'B/D: the aggregate contrasts differ from the protocol')
    contrasts, groups, primary, limits = {}, {'method': [], 'window': [], 'electrodes': []}, {'B': [], 'D': []}, {}
    for i, ((a, b, role, kind, module), c) in enumerate(zip(planned, agg['contrasts'])):
        require(c['metric'] == 'held8', f'B/D {a} minus {b}: not a held-out contrast')
        cid = f'{a} minus {b}/u8'
        contrasts[cid] = contrast(c, role, levels, people, f'B/D {cid}')
        codes[cid] = ['#' + pointer('contrasts', i)]
        groups[kind].append(cid)
        if module:
            primary[module].append(cid)
        key = contrast_limitation(kind, a, b)
        if key:
            limits[cid] = [key]
    require([len(v) for v in groups.values()] == [26, 10, 5] and [len(v) for v in primary.values()] == [1, 6],
            'B/D: the contrast groups')
    handoff_tables(docs, levels, contrasts, cells, methods)

    # What the reviews state about the groups must be what the intervals show.
    def dirs(ids):
        return [contrasts[x]['flags']['direction'] for x in ids]
    fb_cca = [x for x in groups['method'] if f'/{FBCCA} minus ' in x and x.split(' minus ')[1].split('/')[1] == 'CCA-RAW-H3']
    stated(docs, _IR, '', 'All six registered FBCCA-minus-CCA secondary contrasts are nominal positive', 'B/D FBCCA')
    require(len(fb_cca) == 6 and set(dirs(fb_cca)) == {'above zero'}, 'B/D: filter-bank CCA against CCA')
    stated(docs, _IR, '', 'All ten registered 0.5-minus-2-second contrasts are nominal negative', 'B/D windows')
    require(set(dirs(groups['window'])) == {'below zero'}, 'B/D: the window contrasts')
    stated(docs, _IR, '', 'all five registered four-minus-eight-channel contrasts at one second are nominal negative',
           'B/D electrodes')
    require(set(dirs(groups['electrodes'])) == {'below zero'}
            and all(x.startswith('w250-c4/') for x in groups['electrodes']), 'B/D: the electrode contrasts')
    require(dirs(primary['D']).count('above zero') == 1, 'B/D: one D primary is nominal positive')
    stated(docs, _IR, '', 'All six LEAD3-minus-HARM-SUM and all six EIG6-minus-LEAD3 secondary intervals cross zero',
           'B/D learning secondaries')
    learn = [x for x in groups['method'] if contrasts[x]['role'] == 'secondary'
             and (code_of(contrasts[x]['left']), code_of(contrasts[x]['right'])) in
             (('RAW-LEAD3-RIDGE', 'RAW-HARM-SUM-H3'), ('EIG-RAW6-RIDGE', 'RAW-LEAD3-RIDGE'))]
    require(len(learn) == 12 and set(dirs(learn)) == {'unresolved'}, 'B/D: the learning secondaries')

    # The 0.5 s qualifier: where four recorded electrodes have the higher mean, no interval is registered.
    short = [c['id'] for c in cells if c['seconds'] == 0.5]
    require(len(short) == 2 and short[0].endswith('-c4') and short[1].endswith('-c8'), 'B/D: the 0.5 s cells')
    reversed_ = [m for m in methods if levels[f'{short[0]}/{m}/u8']['estimate'] > levels[f'{short[1]}/{m}/u8']['estimate']]
    require(reversed_ and set(reversed_) <= set(RAW_FAMILY), 'B/D: the 0.5 s qualifier does not hold as stated')
    require(not any(f'{short[0]}/{m} minus {short[1]}/{m}/u8' in contrasts for m in methods),
            'B/D: a 0.5 s electrode contrast exists after all')
    qualifiers = {'eight_electrodes_not_always_better': {
        'cells': short, 'endpoint': 'u8', 'methods_four_above_eight': reversed_, 'paired_interval': None,
        'basis': 'level means; no paired interval was registered for these pairs',
        'limitation_key': 'eight_not_always_better'}}

    stated(docs, *UNDEFINED_SOURCE, 'B/D filter-bank CCA against the top-three ridge')
    undefined_cid = f'{ANCHOR_CELL}/{FBCCA} minus {ANCHOR_CELL}/RAW-LEAD3-RIDGE/u8'
    require(undefined_cid not in contrasts, 'B/D: an unplanned contrast')
    undefined = [{'contrast': undefined_cid, 'reason': 'no paired interval was registered'}]

    adapter_not_run = [r['item'] for r in docs['released']['studies']['cca_adapter']['not_run']]
    require('filter-bank CCA' in adapter_not_run, 'card 6 no longer lists filter-bank CCA as not run')

    design = design_of(docs, people)
    design['primary'] = primary
    checks = {
        'release_approval': {'approved': True},
        'numerical_review': {'passed': True,
                             'sealed_payloads_rehashed': docs['bd_audit_receipt']['payloads_verified_in_completed_check'],
                             'admissions': docs['bd_approval']['numeric_release_audit']['counts']['admissions'],
                             'refit_decisions': docs['bd_approval']['numeric_release_audit']['counts']['refit_decisions'],
                             'score_max_error': docs['bd_approval']['numeric_release_audit']['max_errors']['score_error'],
                             'metric_max_error': docs['bd_approval']['numeric_release_audit']['max_errors']['metric_error']},
        'interpretation_review': {'passed': True, 'roster_agreement': True},
        'text_review': {'passed': True},
        'grid_order_is_prospective': True,
    }
    return {
        'card': CARD,
        'anchor': ANCHOR,
        'source_sha256': digests['bd_aggregate'],
        'review_sha256': digests['bd_numerical_review'],
        'interpretation_review_sha256': digests['bd_interpretation_review'],
        'release_approval_sha256': digests['bd_approval'],
        'protocol_sha256': digests['bd_protocol'],
        'freeze_sha256': digests['bd_freeze'],
        'cross_check_sha256': {'ac_summary': digests['ac_summary'], 'coherence_aggregate': digests['coherence_aggregate'],
                               'released': digests['released'], 'route3': digests['route3'],
                               'route3_protocol': digests['route3_protocol']},
        'interval_method': {'method': METHOD, 'draws': DRAWS, 'seed': SEED, 'level': LEVEL,
                            'paired_across': 'methods, cells and rotations within each sampled person'},
        'design': design,
        'grid': grid,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_groups': groups,
        'contrast_limitations': limits,
        'qualifiers': qualifiers,
        'reproduces': reproduced(docs, levels, contrasts),
        'answers_not_run': [{'card': 6, 'study': 'cca_adapter', 'item': 'filter-bank CCA', 'arms': [FBCCA],
                             'inputs': 'the authors’ preprocessed window, cropped before the filter bank'}],
        'undefined': undefined,
        'not_run': not_run(docs),
        'checks': checks,
        'limitations_keys': keys_from(LIMITATION_SOURCES, docs, 'B/D'),
        'display_names': {m: DISPLAY_NAMES[m] for m in methods},
        'export_codes': codes,
        'cpu_components': cpu_components(docs, digests, cells),
    }


# ---------------------------------------------------------------------------- D25: CPU component measurements
def cpu_components(docs, digests, cells):
    tg, tpr = docs['timing_aggregate'], docs['timing_protocol']
    rows = tg['component_summaries']
    order = [(c['id'], b, comp) for c in cells for b in tpr['batch_sizes'] for comp in COMPONENTS]
    require([(r['cell'], r['batch'], r['component']) for r in rows] == order,
            'timing: the summaries are not in the predefined cell/batch/component order')
    text = docs['timing_handoff']
    groups, codes = {}, {}
    for i, r in enumerate(rows):
        require(r['warmup_calls'] == 1 and r['measured_calls'] == 3, f'timing {i}: calls')
        call, amort = r['wall_ms_per_call'], r['wall_ms_per_trial']
        for m in (call, amort):
            require(set(m) == {'median', 'min', 'max'} and all(number(v) and v > 0 for v in m.values())
                    and m['min'] <= m['median'] <= m['max'], f'timing {i}: not a median within its range')
        for k in ('median', 'min', 'max'):
            close(amort[k], call[k] / r['batch'], f'timing {i} {k}: not the batch cost divided by the batch size')
        f = lambda m: f'{m["median"]:.4f} [{m["min"]:.4f}, {m["max"]:.4f}]'      # noqa: E731
        row = f'| {r["cell"]} | {r["batch"]} | {HANDOFF_COMPONENT[r["component"]]} | {f(call)} | {f(amort)} |'
        require(row in text, f'timing {i}: the approved handoff does not print {row!r}')
        site = COMPONENTS[r['component']][0]
        gid = f'{r["cell"]}/{r["batch"]}/{site}'
        groups[gid] = {'cell': r['cell'], 'batch': r['batch'], 'component': site,
                       'wall_ms_per_call': {k: call[k] for k in ('median', 'min', 'max')},
                       'wall_ms_amortised': {k: amort[k] for k in ('median', 'min', 'max')}}
        codes[gid] = [f'timing_aggregate#component_summaries[cell={r["cell"]}][batch={r["batch"]}][component={site}]']
    stated(docs, 'timing_handoff', '', 'one numerical thread, no GPU', 'timing threads')
    stated(docs, 'timing_handoff', '', 'Warm-ups are excluded from medians/minima/maxima', 'timing warm-ups')
    return {
        'source_sha256': digests['timing_aggregate'],
        'review_sha256': digests['timing_review'],
        'receipt_sha256': digests['timing_receipt'],
        'release_approval_sha256': digests['timing_approval'],
        'protocol_sha256': digests['timing_protocol'],
        'label': dict(CPU_LABEL),
        'measurement': {'clock': 'wall', 'unit': 'ms', 'statistic': 'median [min, max]',
                        'measured_calls': tpr['repetitions'], 'warmup_calls_excluded': tpr['warmups'],
                        'threads': tpr['threads'], 'gpu': False, 'buffers': 'warm', 'candidates': len(tpr['candidates_hz']),
                        'batch_sizes': list(tpr['batch_sizes']), 'summed': False,
                        'amortised': 'batch cost divided by the batch size',
                        'readout_head': 'one fixed released head per cell; the 35-head average was not timed'},
        'anchor_cell': ANCHOR_CELL,
        'components': [{'code': code, 'name': name} for code, name in COMPONENTS.values()],
        'groups': groups,
        'order': list(groups),
        'limitations_keys': keys_from(CPU_LIMITATION_SOURCES, docs, 'timing'),
        'checks': {'release_approval': {'approved': True}, 'review': {'passed': True},
                   'groups': len(groups), 'calls_measured': len(groups) * tpr['repetitions'],
                   'whole_method_measurements': docs['timing_approval']['method_whole_pipeline_latencies_measured']},
        'export_codes': codes,
    }


# ---------------------------------------------------------------------------- boundary
def scrub_check(value, trail='$'):
    """Refuse a key, string or value this release must not carry, anywhere in the block."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS, f'{trail}.{k}: refused key')
            require(not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS), f'{trail}.{k}: refused key fragment')
            scrub_check(k, f'{trail}.<key>')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        require(not (len(value) > 3 and all(count(v) for v in value) and trail.split('.')[-1] != 'pass_band_low_edges_hz'),
                f'{trail}: an integer list (row indices?)')
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
    """The practical-settings study block (card 11), keyed practical_settings, with its CPU component record."""
    docs, digests = load(pins)
    check_bindings(docs, digests)
    block = practical_block(docs, digests)
    require(all(f in block for f in BLOCK_FIELDS), f'{STUDY}: a block field is missing')
    require(set(block['export_codes']) == set(block['levels']) | set(block['contrasts']),
            f'{STUDY}: export codes do not cover the levels and contrasts')
    for c in block['contrasts'].values():
        require(c['left'] in block['levels'] and c['right'] in block['levels'], f'{STUDY}: a contrast side is no level')
    cpu = block['cpu_components']
    require(set(cpu['export_codes']) == set(cpu['groups']) == set(cpu['order']), 'cpu components: export codes')
    blocks = {STUDY: block}
    validate_public(blocks)
    scrub_check(blocks)
    return blocks


if __name__ == '__main__':
    built = build_blocks()[STUDY]
    print(json.dumps({STUDY: {'levels': len(built['levels']), 'contrasts': len(built['contrasts']),
                              'limitations': len(built['limitations_keys']),
                              'cpu_component_groups': len(built['cpu_components']['groups'])}}, indent=2))
