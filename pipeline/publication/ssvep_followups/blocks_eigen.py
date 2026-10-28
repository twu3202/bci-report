"""The coherence and eigenvalue block of the SSVEP follow-ups release: card 9 (queue row 12), eigenvalues of the
harmonic matrices, learned or summed.

One audited route 3 follow-up on the BETA cohort, read from its own aggregate and turned into the study block
`coherence_eigen` for `ssvep-followups-update.json`. Five new ridge heads (two coherence-style heads, three eigenvalue
heads) and three untrained analytic controls, beside five comparators the run reused: CCA and the shared ridge scorer
from card 5's sealed scores, and the three cross-spectral ridge readouts of card 8. Thirteen prespecified paired
contrasts, three of them primary, on two endpoints.

The aggregate (`evidence/Completed Aggregate Results.json`, SHA-256 9ee6cc3a...) is refused unless it is byte for byte
the aggregate the study's release approval, release audit and numerical review bind, and unless it equals the release
audit's own verified copy of every arm, contrast and the prespecified eigenvalue rule. Release status is read from
`state/release-approval.json`, never from the aggregate's own frozen `release_status` field. Every number is the
source's own double: nothing is rounded or rescaled, units stay fractions; the EIG-SPEC minus SPEC-HARM-SUM lower bound
stays -2.2321428571386387e-06 (about -0.00022 pp) and is flagged as a bound that prints as 0.00 at two decimals. The
reused comparators must equal card 5's released levels (`site/src/data/new-ssvep-frequencies-update.json`) or card 8's
block (`blocks_xspec.py`) to 1e-12 (they are bit-identical) and carry those cards' site names; the run's pinned
comparators must be card 5's protocol and freeze and card 8's protocol, freeze and seal. JOINT-TOP, the untrained
identity control, must carry CCA's levels exactly.

The declared edits (DECLARED_EDITS): the frozen release status, the run seal hash, the canary and random-pairing
accuracies, the aggregate's free-text multiplicity string and its fit counts (taken under checks from the protocol,
the audit and the approval instead) are not selected; the thread prediction on the existing ridge readout (below 70%,
D23) is not selected; of the prespecified eigenvalue claim, its two prespecified rules are kept as flags on EIG-RAW
minus CCA-RAW and the descriptive point rule is not selected; `held8` and `seen32` are named `u8` and `seen_ba`.

The block has the fields of blocks_xspec.py (see there), with `reused` naming card 5 or card 8 for each reused code,
`origin` `reused_cca_diagnostics` or `reused_xspec`, and `answers_not_run`: the item of card 6's not-run list that the
eigenvalue heads run, with the inputs they ran it on.

    python3 pipeline/publication/ssvep_followups/blocks_eigen.py      # builds and prints the counts; writes nothing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:                      # run directly rather than imported from the pipeline
    sys.path.insert(0, str(PUBLICATION))

from ssvep_followups import blocks_xspec as bx             # noqa: E402  card 8's block and the shared helpers

require, pointer, bound, stated = bx.require, bx.pointer, bx.bound, bx.stated
numeric_leaves, location = bx.numeric_leaves, bx.location

# ---------------------------------------------------------------------------- pinned inputs
_C = 'research/decision_route3_coherence_eigen_20261020'
PINS = {
    'eigen_export': {'path': f'{_C}/evidence/Completed Aggregate Results.json',
                     'sha256': '9ee6cc3a9a46c76faeec00b3d7b57a5fb66993389f85d001a443507becc6717d'},
    'eigen_protocol': {'path': f'{_C}/protocol.json',
                       'sha256': '79ce887cdae5f929f8a42a9a997b85d1d212c205e9d890a2169e8795b55c5a0f'},
    'eigen_freeze': {'path': f'{_C}/execution-freeze.json',
                     'sha256': 'ca3638544774e8e76f2a429d9b042cd65d598fc40a4782c3df5602a197d75896'},
    'eigen_execution_review': {'path': f'{_C}/execution-review.json',
                               'sha256': 'e4f9255da482baf0d9e4aba1f6c0d6f64a9e77b77ee1e7bec2c4bb1cad712f6b'},
    'eigen_audit': {'path': f'{_C}/evidence/Release Audit Summary.json',
                    'sha256': 'cbc4adf361d0f1b364f0341168ddea484c3585b5cf388517299130f0d09a9c92'},
    'eigen_numerical_review': {'path': f'{_C}/review/Independent Numerical Release Review.md',
                               'sha256': '69febd8c5db88c3cceb7e5a95c03cc949774327d894f7466002031e72e9b1eab'},
    'eigen_review': {'path': f'{_C}/review/Independent Interpretation Release Review.md',
                     'sha256': '103ca974bd8ca4083f15e4028b7abeddd2d0aac7b74b720db2d4baa0aae67508'},
    'eigen_approval': {'path': f'{_C}/state/release-approval.json',
                       'sha256': '4a0beb364285bdf3c4550eb7c89a1180acf5e565175c40195cc951d8c0a42702'},
    'eigen_handoff': {'path': f'{_C}/Coherence and Eigenvalue Results Handoff.md',
                      'sha256': 'a53819bd7f7e4c61275017ff955aabd73e933b16aa9e0e0d6175b422c1494db0'},
    'eigen_runner': {'path': f'{_C}/scripts/run_coherence_eigen.py',
                     'sha256': '621f215be034b6641a30dca9e1b63a184b57f80c588f63bbba2f26ec5addfd75'},
    'released': dict(bx.PINS['released']),
}
TEXT_PINS = {'eigen_numerical_review', 'eigen_review', 'eigen_handoff', 'eigen_runner'}
SERVED = dict(bx.SERVED)
HANDOFF_CONTEXT = {'coherence_eigen': {'bound_sha256': 'a53819bd7f7e4c61275017ff955aabd73e933b16aa9e0e0d6175b422c1494db0',
                                       'bound_by': 'eigen_approval'}}

STUDY, CARD, ANCHOR = 'coherence_eigen', 9, 'eigenvalue-pooling'
STUDIES = (STUDY,)
ENDPOINTS = bx.ENDPOINTS
PROPORTION, DIFFERENCE, NO_TRAINING, DETERMINISTIC = bx.PROPORTION, bx.DIFFERENCE, bx.NO_TRAINING, bx.DETERMINISTIC
SEED, DRAWS, LEVEL, METHOD, TOL = bx.SEED, bx.DRAWS, bx.LEVEL, bx.METHOD, bx.TOL

NEW_ARMS = ('COH-ABS', 'COH-SIGNED', 'EIG-SPEC', 'EIG-RAW', 'EIG-JOINT')
CONTROLS = ('JOINT-TOP', 'RAW-HARM-SUM', 'SPEC-HARM-SUM')
# code here -> (card, study, code in that card's block)
REUSED = {'SHARED-RIDGE': (5, 'cca_diagnostics', 'SHARED-RIDGE'), 'CCA-RAW': (5, 'cca_diagnostics', 'CCA-RAW'),
          'XS-RIDGE': (8, 'xspec', 'XS-RIDGE'), 'XS-RIDGE-W': (8, 'xspec', 'XS-RIDGE-W'),
          'XS-RIDGE-Q': (8, 'xspec', 'XS-RIDGE-Q')}
EIGEN_RULE = ('EIG-RAW', 'CCA-RAW', 'held8')              # the sole primary eigenvalue-proximity contrast

# ---------------------------------------------------------------------------- the name key (plan section 2.1)
DISPLAY_NAMES = {
    'COH-ABS': 'coherence head',
    'COH-SIGNED': 'signed coherence head',
    'EIG-SPEC': 'spectral eigenvalue head',
    'EIG-RAW': 'eigenvalue head',
    'EIG-JOINT': 'joint eigenvalue head',
    'JOINT-TOP': 'joint CCA',
    'RAW-HARM-SUM': 'harmonic sum (no training)',
    'SPEC-HARM-SUM': 'spectral harmonic sum (no training)',
}
NAME_KEY = (
    ('harmonic sum (no training)', 'RAW-HARM-SUM'),
    ('joint CCA', 'JOINT-TOP'),
    ('eigenvalue head', 'EIG-RAW'),
    ('joint eigenvalue head', 'EIG-JOINT'),
    ('spectral eigenvalue head', 'EIG-SPEC'),
    ('spectral harmonic sum (no training)', 'SPEC-HARM-SUM'),
    ('coherence head', 'COH-ABS'),
    ('signed coherence head', 'COH-SIGNED'),
)

# ---------------------------------------------------------------------------- limitations, not run, declared edits
LIMITATION_SOURCES = {
    'same_cohort_follow_up': ('eigen_protocol', '/interpretation/0', 'do not make a fresh confirmatoryexternaltest'),
    'unadjusted_intervals': ('eigen_protocol', '/interpretation/5', 'no family-wise discovery guarantee'),
    'intervals_conditional_on_procedure': ('eigen_handoff', '', 'conditional on this fixed training/fold procedure'),
    'held_and_seen_separate': ('eigen_approval', '/release_limits/1', 'Held-eight and seen32 explicitly separated'),
    'comparators_reused': ('eigen_handoff', '', 'Previous comparators are reused from pinned sealed artifacts; no old '
                                                'experiment was rerun.'),
    'cca_statistics_supplied': ('eigen_protocol', '/interpretation/2',
                                'CCA-derived eigenfeatures explicitly supply per-trial adaptive statistics'),
    'coherence_is_projection_cosine': ('eigen_protocol', '/features/coherence', 'not Welch/coherence estimate'),
    'no_general_coherence_claim': ('eigen_approval', '/release_limits/4', 'No claim conventional coherence generally '
                                                                          'fails'),
    'spectral_not_validated_by_raw': ('eigen_handoff', '', 'Success of the raw-time eigenvalue variant must not be '
                                                           'presented as validation of the spectral variant.'),
    'learned_head_gain_unresolved': ('eigen_approval', '/release_limits/3',
                                     'No resolved EIG-RAW gain over untrained RAW-HARM-SUM; not equivalence proof'),
    'raw_vs_spectral_bundled': ('eigen_protocol', '/interpretation/1',
                                'No causal attribution of EIG-SPEC versusEIG-RAW to whitening alone'),
    'spectral_vs_whitened_bundled': ('eigen_protocol', '/interpretation/7',
                                     'also changes feature dimensionality and effective ridge regularization'),
    'harmonic_sum_vs_joint_bundled': ('eigen_protocol', '/interpretation/6',
                                      'changes pooling, optimal spatial weights and overlapping subspaces together'),
    'per_harmonic_discards_subspace': ('eigen_protocol', '/interpretation/3',
                                       'Per-harmonic eigenvalues discardrelative harmonic subspace information'),
    'sign_and_normalization': ('eigen_handoff', '', 'ABS versus SIGNED isolates sign removal, whereas ABS versus '
                                                    'XS-RIDGE changes both normalization and sign handling.'),
    'lower_bound_not_rounded': ('eigen_review', '', 'rounding must not manufacture a positive lower endpoint'),
    'zero_energy_edge_fix': ('eigen_freeze', '/pre_execution_correction',
                             'Enforce frozen zero-channel-energy rule even when energy squaring underflows'),
    'synthetic_suite_timeout_not_a_pass': ('eigen_handoff', '', 'it is not counted as a pass'),
    'release_audit_scope': ('eigen_handoff', '', 'This release pass did not reopen raw EEG, regenerate features, '
                                                 'rerun fits'),
}
CONTRAST_LIMITATIONS = {
    'COH-ABS minus XS-RIDGE': ('sign_and_normalization',),
    'COH-SIGNED minus COH-ABS': ('sign_and_normalization',),
    'COH-SIGNED minus XS-RIDGE': ('sign_and_normalization',),
    'EIG-SPEC minus XS-RIDGE-W': ('spectral_vs_whitened_bundled',),
    'EIG-RAW minus CCA-RAW': ('cca_statistics_supplied',),
    'EIG-RAW minus RAW-HARM-SUM': ('learned_head_gain_unresolved',),
    'EIG-SPEC minus SPEC-HARM-SUM': ('lower_bound_not_rounded',),
    'EIG-JOINT minus JOINT-TOP': ('cca_statistics_supplied',),
}
NOT_RUN_SOURCES = {
    'conventional averaged coherence estimator': ('eigen_handoff', '', 'It does not test a conventional averaged/Welch '
                                                                       'coherence estimator.'),
    'neural-network head': ('eigen_handoff', '', 'No text encoder, EEG foundation model, neural-network training'),
    'equivalence margin for the eigenvalue head against the harmonic sum': (
        'eigen_review', '', 'No equivalence margin was declared for this comparison'),
}
# Card 6's not-run item that this study's eigenvalue heads run, and on what (the plan's "a simpler learned head on
# CCA statistics"); card 6's list stays as released.
ANSWERS_NOT_RUN = ({'card': 6, 'study': 'cca_adapter', 'item': 'simpler learned head on the CCA features',
                    'arms': ['EIG-RAW', 'EIG-JOINT'],
                    'inputs': 'squared canonical correlations between the raw window and the harmonic references',
                    'same_inputs_as_card_6': False},)
DECLARED_EDITS = {
    'coherence_eigen': (
        'release_status not selected; state/release-approval.json records the approval',
        'prediction_seal_sha256 not selected; it is checked against the approval and the release audit',
        'existing_normalized_xs_ridge_bet not selected (a thread prediction; thread predictions stay on card 4, D23)',
        'prespecified_eigenvalue_claim: its two prespecified rules kept as flags on EIG-RAW minus CCA-RAW; '
        'point_absolute_gap_within5pp and the repeated paired_difference not selected',
        'canary_real_label_accuracy_descriptive_only and evaluation_random_pairing_descriptive not selected',
        'main_fits, additional_fits and multiplicity not selected from the aggregate; fit counts come from the '
        'protocol, the release audit and the approval under checks',
        'held8 and seen32 named u8 and seen_ba in ids (card 5\'s spelling of the same two tasks, checked through '
        'CCA\'s own value)',
        'ridge heads carry "deterministic fit", the analytic controls "no training"; reused comparators carry the '
        'levels, seeds and names of card 5 or card 8',
    ),
}


# ---------------------------------------------------------------------------- inputs
def load(pins=None):
    return bx.read_pins(pins or PINS, PINS, TEXT_PINS, SERVED)


def inputs_available(pins=None, xspec_pins=None):
    return (all(location(r['path']).exists() for r in (pins or PINS).values())
            and all(location(p).exists() for p in SERVED.values()) and bx.inputs_available(xspec_pins))


# ---------------------------------------------------------------------------- coherence and eigenvalue (card 9)
def eigen_block(docs, digests, xs_docs, xs_digests, xspec):
    ex, protocol, fz, er, audit, approval = (docs[k] for k in (
        'eigen_export', 'eigen_protocol', 'eigen_freeze', 'eigen_execution_review', 'eigen_audit', 'eigen_approval'))
    numerical, review, handoff, runner = (docs[k] for k in ('eigen_numerical_review', 'eigen_review', 'eigen_handoff',
                                                            'eigen_runner'))

    # Release status: the approval, never the aggregate's own frozen field.
    require(approval['status'] == 'APPROVED_AGGREGATE_HANDOFF', 'eigen: the release approval does not approve')
    bound(approval['aggregate_sha256'], digests['eigen_export'], 'eigen approval export')
    bound(approval['protocol_sha256'], digests['eigen_protocol'], 'eigen approval protocol')
    bound(approval['freeze_sha256'], digests['eigen_freeze'], 'eigen approval freeze')
    bound(approval['handoff_sha256'], digests['eigen_handoff'], 'eigen approval handoff')
    bound(approval['numerical_review_sha256'], digests['eigen_numerical_review'], 'eigen approval numerical review')
    bound(approval['interpretation_review_sha256'], digests['eigen_review'], 'eigen approval review')
    bound(approval['release_audit_summary_sha256'], digests['eigen_audit'], 'eigen approval audit')
    bound(approval['prediction_seal_sha256'], ex['prediction_seal_sha256'], 'eigen approval seal')
    bound(audit['aggregate_sha256'], digests['eigen_export'], 'eigen audit export')
    bound(audit['protocol_sha256'], digests['eigen_protocol'], 'eigen audit protocol')
    bound(audit['freeze_sha256'], digests['eigen_freeze'], 'eigen audit freeze')
    bound(audit['execution_review_sha256'], digests['eigen_execution_review'], 'eigen audit execution review')
    bound(audit['prediction_seal_sha256'], ex['prediction_seal_sha256'], 'eigen audit seal')
    bound(fz['protocol_sha256'], digests['eigen_protocol'], 'eigen freeze protocol')
    bound(fz['code_sha256']['run_coherence_eigen.py'], digests['eigen_runner'], 'eigen freeze runner')
    bound(er['freeze_sha256'], digests['eigen_freeze'], 'eigen execution review freeze')
    bound(er['protocol_sha256'], digests['eigen_protocol'], 'eigen execution review protocol')
    bound(er['code_sha256']['run_coherence_eigen.py'], digests['eigen_runner'], 'eigen execution review runner')
    for name in ('eigen_export', 'eigen_protocol', 'eigen_freeze', 'eigen_execution_review'):
        require(digests[name] in numerical, f'eigen: the numerical review does not bind {name}')
    require(er['status'] == 'PASS', 'eigen: the execution review did not pass')
    require('Technical PASS' in numerical and 'No technical release hold remains.' in numerical,
            'eigen: the numerical review did not pass')
    require('**Decision: PASS for an aggregate handoff' in review and '**Interpretation PASS.**' in review,
            'eigen: the interpretation review did not pass')
    require(audit['status'] == 'PASS_FOR_ROOT_RELEASE_DECISION' and audit['technical_holds'] == []
            and audit['private_mutations'] is False and audit['local_review_synthetic_preflight_hash_bindings_verified']
            is True, 'eigen: the release audit did not pass')
    require(ex['aggregate_only'] is True, 'eigen: the aggregate is not aggregate-only')

    # The aggregate, leaf by leaf, against the release audit's own verified copy.
    pairs = list(numeric_leaves(audit['verified_aggregate_arms'], ex['arms']))
    pairs += list(numeric_leaves(audit['all_13_verified_contrasts'], ex['contrasts']))
    pairs += list(numeric_leaves(audit['verified_prespecified_eigenvalue_claim'], ex['prespecified_eigenvalue_claim']))
    worst = max(abs(a - b) for _, a, b in pairs)
    require(worst <= TOL, f'eigen: the aggregate differs from the release audit by {worst!r}')

    # Interval rule: the protocol's draws and seed, the reviewed regeneration, card 8's runner's percentile summary.
    st = protocol['statistics']
    require(st['bootstrap_draws'] == DRAWS and st['bootstrap_seed'] == SEED, 'eigen: bootstrap draws or seed')
    require('np.random.default_rng(20261015).integers(0,70,size=(2000,70))' in runner, 'eigen: the runner bootstrap')
    require('result=legacy.primary_summary(values,indices,contrast)' in runner, 'eigen: the runner summary')
    bound(bx.comparator_hash({'comparator_hashes': protocol['import_hashes']}, '/run_xspec.py', 'eigen'),
          xs_digests['xspec_runner'], 'eigen imported runner')
    require("np.quantile(b,[.025,.975],method='linear')" in xs_docs['xspec_runner']
            and "'above_zero':bool(lo>0)" in xs_docs['xspec_runner']
            and "'below_zero':bool(hi<0)" in xs_docs['xspec_runner'], 'eigen: the imported summary rule')
    stated(docs, 'eigen_numerical_review', '', 'regenerated the **2,000 paired 70-person bootstrap draws, seed 20261015**',
           'eigen bootstrap')
    require(st['multiplicity'].startswith('none;'), 'eigen: multiplicity')
    stated(docs, 'eigen_handoff', '', 'The 2,000 paired draws use seed 20261015', 'eigen bootstrap')

    # Card 5 and card 8: the run's pinned comparators are their studies.
    diag, cards = bx.released_card5(docs)
    require(cards[bx.CARD]['anchor'] == bx.ANCHOR, 'eigen: card 8 moved')
    bound(bx.comparator_hash(protocol, 'cca_diagnostics_20261015/protocol.json', 'eigen'), diag['protocol_sha256'],
          'eigen comparators card 5 protocol')
    bound(bx.comparator_hash(protocol, 'cca_diagnostics_20261015/execution-freeze.json', 'eigen'), diag['freeze_sha256'],
          'eigen comparators card 5 freeze')
    bound(bx.comparator_hash(protocol, 'xspec_20261019/protocol.json', 'eigen'), xspec['protocol_sha256'],
          'eigen comparators card 8 protocol')
    bound(bx.comparator_hash(protocol, 'xspec_20261019/execution-freeze.json', 'eigen'), xspec['freeze_sha256'],
          'eigen comparators card 8 freeze')
    bound(bx.comparator_hash(protocol, 'xspec_20261019/prediction-seal.json', 'eigen'),
          xs_docs['xspec_export']['prediction_seal_sha256'], 'eigen comparators card 8 seal')
    bound(xspec['source_sha256'], xs_digests['xspec_export'], 'eigen card 8 block')

    dataset = dict(diag['design']['dataset'])
    people = ex['person_count']
    require(people == dataset['people'] == 70 and ex['rotations'] == dataset['frequency_rotations'] == 5,
            'eigen: not card 5\'s people and rotations')
    split_fits = dataset['person_folds'] * dataset['frequency_rotations']
    sa = protocol['source_admission']
    require(sa['candidates_per_fit'] == 32 and sa['rows_per_fit'] == 7680, 'eigen: source admission')
    endpoints = {e: dict(v) for e, v in diag['design']['endpoints'].items()}
    require(set(endpoints) == set(ENDPOINTS), 'eigen: endpoints')
    require(diag['design']['harmonics'] == 3 and 'For each of3harmonics' in protocol['features']['EIG-SPEC'],
            'eigen: harmonics')

    # The arms: five ridge heads, three analytic controls, five reused comparators, in the aggregate's order.
    cells, controls = protocol['main_cells'], protocol['analytic_controls']
    require(tuple(cells) == NEW_ARMS and tuple(controls) == CONTROLS
            and tuple(ex['arms']) == NEW_ARMS + CONTROLS + tuple(REUSED), 'eigen: the arm set changed')
    require("arms=(*CELLS,*CONTROL,'SHARED-RIDGE','CCA-RAW','XS-RIDGE','XS-RIDGE-W','XS-RIDGE-Q')" in runner,
            'eigen: the runner scores other arms')
    require(protocol['main_fit_count'] == len(NEW_ARMS) * split_fits == 175, 'eigen: main fit count')
    seeds_of = {c: DETERMINISTIC for c in NEW_ARMS} | {c: NO_TRAINING for c in CONTROLS}
    sources = {'cca_diagnostics': diag, 'xspec': xspec}

    levels, codes, reused, worst_reuse = {}, {}, {}, {5: 0.0, 8: 0.0}
    names = dict(DISPLAY_NAMES)
    for code in ex['arms']:
        for e, src in ENDPOINTS.items():
            lid = f'{code}/{e}'
            if code in REUSED:
                card, study, there_code = REUSED[code]
                there, block = f'{there_code}/{e}', sources[study]
                twin = block['levels'][there]
                lv = bx.level(ex['arms'][code][src], people, twin['seeds'], f'reused_{study}', f'eigen {lid}')
                worst_reuse[card] = max(worst_reuse[card], bx.same_level(lv, twin, f'eigen {lid} (card {card} {there})'))
                codes[lid] = ['#' + pointer('arms', code, src), study + block['export_codes'][there][0]]
                if study == 'cca_diagnostics':
                    codes[lid].append(f'{bx.RELEASED_FILE}#' + pointer('studies', study, 'levels', there))
            else:
                lv = bx.level(ex['arms'][code][src], people, seeds_of[code], 'new', f'eigen {lid}')
                codes[lid] = ['#' + pointer('arms', code, src)]
            levels[lid] = lv
        if code in REUSED:
            # One set of scores, one name: a reused code takes the name of the card it comes from.
            card, study, there_code = REUSED[code]
            require(code not in DISPLAY_NAMES, f'eigen {code}: a second name for one set of scores')
            names[code] = sources[study]['display_names'][there_code]
            reused[code] = {'card': card, 'study': study, 'anchor': cards[card]['anchor'], 'code': there_code}

    # JOINT-TOP, the untrained identity control, carries CCA's levels exactly.
    for e in ENDPOINTS:
        a, b = levels[f'JOINT-TOP/{e}'], levels[f'CCA-RAW/{e}']
        require((a['estimate'], a['interval']) == (b['estimate'], b['interval']), f'eigen: JOINT-TOP/{e} is not CCA')
    stated(docs, 'eigen_protocol', '/analytic_controls/JOINT-TOP', 'equals CCA-RAW squared with exact decisions',
           'eigen identity control')

    # Contrasts: the protocol's thirteen, in its order and with its roles; the handoff's table states the same.
    planned = [(a, b, 'held8', 'primary') for a, b in st['primary_held8']]
    planned += [(a, b, 'held8', 'secondary') for a, b in st['secondary_held8']]
    planned += [(a, b, 'seen32', 'secondary') for a, b in st['secondary_seen32']]
    require(len(planned) == st['formal_paired_contrast_count'] == len(ex['contrasts']) == 13, 'eigen: thirteen contrasts')
    require([(c['a'], c['b'], c['metric']) for c in ex['contrasts']] == [p[:3] for p in planned],
            'eigen: the aggregate contrasts differ from the protocol')
    require(bx.contrast_table(handoff, 'eigen') == planned, 'eigen: the handoff states other contrasts or roles')
    stated(docs, 'eigen_protocol', '/statistics/primary_inference', 'EIG-RAW is sole primary eigenvalue proximity claim',
           'eigen primary rule')
    stated(docs, 'eigen_protocol', '/statistics/eigenvalue_claim',
           'Literalwithin5pp: paired95CI entirely inside(-.05,+.05). Separately noninferiority lower>-.05',
           'eigen 5 pp rule')
    claim = ex['prespecified_eigenvalue_claim']
    require(claim['arm'] == 'EIG-RAW' and claim['comparator'] == 'matched CCA-RAW', 'eigen: the eigenvalue claim arm')

    contrasts = {}
    for i, (c, (a, b, metric, role)) in enumerate(zip(ex['contrasts'], planned)):
        e = next(k for k, v in ENDPOINTS.items() if v == metric)
        cid = f'{a} minus {b}/{e}'
        n_seeds = NO_TRAINING if all(seeds_of.get(x) == NO_TRAINING or x == 'CCA-RAW' for x in (a, b)) else DETERMINISTIC
        out = bx.paired_contrast(c, role, f'{a}/{e}', f'{b}/{e}', levels, people, n_seeds, f'eigen {cid}')
        lo, hi = out['interval']
        require(set(c) == {'a', 'b', 'metric', 'mean', 'ci95', 'above_zero', 'below_zero'}, f'eigen {cid}: fields')
        for flag in ('above_zero', 'below_zero'):
            require(c[flag] is bx.RULES[flag][2](lo, hi), f'eigen {cid}: {flag} does not follow the rule')
            out['flags'][flag] = c[flag]
        if (a, b, metric) == EIGEN_RULE:
            require(claim['paired_difference'] == c, 'eigen: the eigenvalue claim names another difference')
            require(claim['strict_5pp_equivalence'] is (lo > -0.05 and hi < 0.05)
                    and claim['strict_5pp_noninferiority'] is (lo > -0.05), 'eigen: the 5 pp rules')
            out['flags']['strict_5pp_equivalence'] = claim['strict_5pp_equivalence']
            out['flags']['strict_5pp_noninferiority'] = claim['strict_5pp_noninferiority']
        contrasts[cid], codes[cid] = out, ['#' + pointer('contrasts', i)]
    low = contrasts['EIG-SPEC minus SPEC-HARM-SUM/u8']
    require(low['flags'].get('bound_below_two_decimals') == ['lower'] and low['interval'][0] < 0,
            'eigen: the EIG-SPEC pooling lower bound is not the near-zero negative bound')
    stated(docs, 'eigen_handoff', '', 'The near-zero negative lower endpoint in the EIG-SPEC pooling comparison is '
           'displayed with extra precision rather than rounded', 'eigen extra precision')

    # Counts only: fit operations, identity pairs, the zero-energy gate, the release audit's counts.
    fits = {'main': protocol['main_fit_count'], 'independent_refits': protocol['independent_refit_count'],
            'bridges': protocol['bridge_count'], 'canaries': protocol['canary_count'],
            'total': protocol['total_fit_count']}
    require(fits['total'] == sum(v for k, v in fits.items() if k != 'total') == 361, 'eigen: fit operations')
    require((audit['main_fits_verified'], audit['independent_refits_verified'], audit['bridges_verified'],
             audit['canaries_verified'], audit['total_fits']) == tuple(fits.values()), 'eigen: audit fit counts')
    require(approval['total_fit_operations'] == fits['total'] and approval['main_fits'] == fits['main']
            and approval['independent_refits'] == fits['independent_refits'], 'eigen: approval fit counts')
    stated(docs, 'eigen_handoff', '', 'six zero-cross nesting bridges and five source-label-permutation canaries '
           'completed: 361 fit operations', 'eigen fits')
    gate = audit['geometry_gate']
    require(gate['passed'] is True and gate['identity_pairs'] == dataset['windows'] * dataset['targets'] == 448000
            and audit['joint_top_CCA_squared_max_absolute_error'] == 0.0, 'eigen: the CCA identity')
    stated(docs, 'eigen_handoff', '', 'across all 448,000 trial–candidate pairs and identical all/held/seen decisions',
           'eigen identity')
    qc = audit['geometry_qc_summary']
    require(qc['coherence_gated_pairs'] == 0 and qc['coherence_total_pairs'] == 37632000, 'eigen: the zero gate')
    stated(docs, 'eigen_handoff', '', 'There are 0 gated channel-pair/harmonic entries out of 37,632,000.',
           'eigen zero gate')
    require(audit['formal_contrasts_reconstructed'] == 13 and audit['arm_count'] == len(ex['arms']),
            'eigen: the audit reconstructed other contrasts')
    checks = {
        'release_approval': {'approved': True},
        'numerical_review': {'passed': True, 'technical_holds': len(audit['technical_holds'])},
        'interpretation_review': {'passed': True},
        'execution_review': {'passed': True},
        'release_audit': {'passed': True, 'sealed_artifacts': audit['seal_artifacts_verified'],
                          'source_admission_sets': audit['source_admission_sets_verified'],
                          'metric_entries_reconstructed': audit['metric_entries_reconstructed'],
                          'contrasts_reconstructed': audit['formal_contrasts_reconstructed']},
        'fits': fits,
        'cca_identity': {'pairs': gate['identity_pairs'], 'decisions_identical': True},
        'coherence_zero_gate': {'gated_pairs': qc['coherence_gated_pairs'], 'of': qc['coherence_total_pairs']},
        'aggregate_equals_release_audit': {'passed': True, 'numeric_values': len(pairs)},
        'joint_top_equals_cca': {'passed': True},
        'same_scores_as_card_5': {'passed': True, 'card': 5, 'codes': [c for c in REUSED if REUSED[c][0] == 5],
                                  'tolerance': TOL, 'max_absolute_difference': worst_reuse[5]},
        'same_scores_as_card_8': {'passed': True, 'card': 8, 'codes': [c for c in REUSED if REUSED[c][0] == 8],
                                  'tolerance': TOL, 'max_absolute_difference': worst_reuse[8]},
    }

    # Card 6's not-run item these heads run, on other inputs than card 6's.
    adapter_items = [x['item'] for x in docs['released']['studies']['cca_adapter']['not_run']]
    feats = protocol['features']
    require('two squared canonical correlations to centered raw EEG' in feats['EIG-RAW']
            and 'squared canonical correlations between centered raw EEG' in feats['EIG-JOINT'],
            'eigen: the eigenvalue heads are not read on raw CCA statistics')
    for row in ANSWERS_NOT_RUN:
        require(row['item'] in adapter_items and set(row['arms']) <= set(NEW_ARMS), 'eigen: card 6 not-run item')

    design = {
        'dataset': dataset,
        'endpoints': endpoints,
        'harmonics': diag['design']['harmonics'],
        'source_windows_per_fit': sa['rows_per_fit'],
        'seen_frequencies_per_fit': sa['candidates_per_fit'],
        'arms': [{'code': c, 'training': 'ridge fitted on source people', 'fits': split_fits, 'input_count': cells[c]}
                 for c in NEW_ARMS],
        'controls': [{'code': c, 'training': NO_TRAINING} for c in CONTROLS],
        'comparators': [{'code': c, 'training': NO_TRAINING if c == 'CCA-RAW' else 'ridge fitted on source people',
                         'card': REUSED[c][0]} for c in REUSED],
        'main_fits': protocol['main_fit_count'],
    }
    return {
        'source_sha256': digests['eigen_export'],
        'review_sha256': digests['eigen_review'],
        'numerical_review_sha256': digests['eigen_numerical_review'],
        'audit_summary_sha256': digests['eigen_audit'],
        'approval_sha256': digests['eigen_approval'],
        'protocol_sha256': digests['eigen_protocol'],
        'freeze_sha256': digests['eigen_freeze'],
        'execution_review_sha256': digests['eigen_execution_review'],
        'runner_sha256': digests['eigen_runner'],
        'released_sha256': digests['released'],
        'interval_method': {'method': METHOD, 'draws': st['bootstrap_draws'], 'seed': st['bootstrap_seed'],
                            'level': LEVEL, 'conditional_on': 'the fixed training and fold procedure'},
        'design': design,
        'levels': levels,
        'contrasts': contrasts,
        'contrast_limitations': bx.contrast_limitations(CONTRAST_LIMITATIONS, LIMITATION_SOURCES, contrasts, 'eigen'),
        'reused': reused,
        'answers_not_run': [dict(r) for r in ANSWERS_NOT_RUN],
        'undefined': [],
        'not_run': bx.not_run(NOT_RUN_SOURCES, docs, 'eigen'),
        'checks': checks,
        'limitations_keys': bx.limitations(LIMITATION_SOURCES, docs, 'eigen'),
        'display_names': bx.display_names(names, levels, 'eigen'),
        'export_codes': codes,
    }


def build_blocks(pins=None, xspec_pins=None) -> dict:
    """The coherence and eigenvalue study block, keyed coherence_eigen; card 8's block is built to check its reuse."""
    docs, digests = load(pins)
    xs_docs, xs_digests = bx.load(xspec_pins)
    xspec = bx.build_from(xs_docs, xs_digests)[bx.STUDY]
    block = eigen_block(docs, digests, xs_docs, xs_digests, xspec)
    ex = docs['eigen_export']
    held = bx.withheld(ex, {k: ex[k] for k in ('arms', 'contrasts', 'prespecified_eigenvalue_claim')})
    return bx.finish({STUDY: block}, held)


if __name__ == '__main__':
    built = build_blocks()
    print(json.dumps({s: {'levels': len(b['levels']), 'contrasts': len(b['contrasts']),
                          'limitations': len(b['limitations_keys'])} for s, b in built.items()}, indent=2))
