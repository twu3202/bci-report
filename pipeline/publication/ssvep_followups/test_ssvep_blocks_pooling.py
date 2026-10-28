"""SS-B, the pooling blocks (card 10): what they must carry, and what they must refuse.

Expected figures are written out from the records that state them (the A/C release review's contrast tables, the
approved A/C handoff's level tables and the plan's card 10), rendered the way the site renders them: JavaScript toFixed
on the double value, so an exact decimal tie rounds away from zero, as the site's pct2 and pp2 formatters do.
"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public                                  # noqa: E402
from ssvep_followups import blocks_pooling as bp                              # noqa: E402
from ssvep_followups.test_ssvep_blocks_cca import crow, floats, js_fixed, lrow, pct2, pp2  # noqa: E402

A, C = bp.STUDIES
PRIVATE = re.compile(r'/(?:Users|Volumes|home|mnt|root)\b|trx|gal4|bci_arena|\btwu\b|threadripper|hy-trx', re.I)


def p4(raw):
    """A difference at the four decimals the reviews print, signed as the plan writes it."""
    return ('' if raw == 0 else '+' if raw > 0 else '−') + js_fixed(abs(raw * 100), 4)


def c4(c):
    return p4(c['estimate']), p4(c['interval'][0]), p4(c['interval'][1])


def l4(lv):
    return tuple(js_fixed(x * 100, 4) for x in (lv['estimate'], *lv['interval']))


@unittest.skipUnless(bp.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class PoolingBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bp.build_blocks()
        cls.a, cls.c = cls.blocks[A], cls.blocks[C]
        cls.docs, cls.digests = bp.load()

    # ------------------------------------------------------------------ shape
    def test_two_blocks_with_the_fields_of_the_earlier_blocks(self):
        self.assertEqual(tuple(self.blocks), ('harmonic_pooling', 'harmonic_pooling_wearable'))
        for name, b in self.blocks.items():
            for k in bp.BLOCK_FIELDS + ('design', 'contrast_limitations', 'level_only', 'reused'):
                self.assertIn(k, b, f'{name} lacks {k}')
            self.assertEqual((b['card'], b['anchor']), (10, 'harmonic-pooling'))
            self.assertEqual(set(b['export_codes']), set(b['levels']) | set(b['contrasts']), name)
            for lid, lv in b['levels'].items():
                self.assertEqual(set(lv), {'estimate', 'interval', 'unit', 'people', 'seeds', 'origin'}, lid)
                self.assertEqual(lv['unit'], 'proportion')
                self.assertIn(lid.split('/')[0], b['display_names'])
                self.assertEqual(lv['interval'] is None, lid in b['level_only'], lid)
            for cid, c in b['contrasts'].items():
                self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'unit', 'people', 'seeds',
                                          'flags'}, cid)
                self.assertEqual(c['unit'], 'difference of proportions')
                self.assertIn(c['left'], b['levels'])
                self.assertIn(c['right'], b['levels'])
                self.assertIn(c['role'], ('primary', 'secondary'))
            for codes in b['export_codes'].values():
                self.assertTrue(codes and all(re.fullmatch(r'(?:[\w.-]+)?#(?:/[^/]+)+', x) for x in codes), codes)
        self.assertEqual((len(self.a['levels']), len(self.a['contrasts'])), (16, 6))       # 8 arms x 2 tasks
        self.assertEqual((len(self.c['levels']), len(self.c['contrasts'])), (16, 10))      # 8 methods x 2 sensors

    def test_the_build_is_deterministic_and_public(self):
        self.assertEqual(json.dumps(bp.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))
        validate_public(self.blocks)

    def test_each_block_carries_its_own_interval_method(self):
        ma, mc = self.a['interval_method'], self.c['interval_method']
        self.assertEqual((ma['method'], ma['draws'], ma['seed'], ma['level']),
                         ('paired person bootstrap, percentile interval', 2000, 20261015, 0.95))
        self.assertEqual((mc['method'], mc['draws'], mc['seed'], mc['level']),
                         ('paired person bootstrap, percentile interval', 2000, 20261020, 0.95))
        self.assertNotIn('conditional_on', ma)
        self.assertIn('35 source heads', mc['conditional_on'])
        self.assertTrue(all(lv['people'] == 70 for lv in self.a['levels'].values()))
        self.assertTrue(all(lv['people'] == 102 for lv in self.c['levels'].values()))

    def test_units_are_fractions_at_source_precision(self):
        s = self.docs['ac_summary']
        for b in self.blocks.values():
            for lv in b['levels'].values():
                lo, hi = lv['interval'] or (lv['estimate'], lv['estimate'])
                self.assertTrue(0 <= lo <= lv['estimate'] <= hi <= 1)
            for c in b['contrasts'].values():
                self.assertTrue(-1 <= c['interval'][0] <= c['estimate'] <= c['interval'][1] <= 1)
        self.assertEqual(self.a['levels']['RAW-LEAD3-RIDGE/u8']['estimate'],
                         s['verified_A_aggregate']['arms']['RAW-LEAD3-RIDGE']['held8']['mean'])
        self.assertEqual(self.c['contrasts']['EIG-JOINT minus JOINT-ALLSUM/dry']['estimate'], -3.5374753235605476e-18)

    # ------------------------------------------------------------------ module A (BETA)
    def test_a_primaries_and_secondaries_with_their_intervals(self):
        want = {  # the release review's table; plan card 10
            'RAW-LEAD3-RIDGE minus RAW-HARM-SUM': ('primary', ('+0.3036', '−0.1250', '+0.7768'), 'unresolved'),
            'EIG-RAW minus RAW-LEAD3-RIDGE': ('primary', ('−0.2321', '−0.5714', '+0.1071'), 'unresolved'),
            'RAW-HARM-ALLSUM minus RAW-HARM-SUM': ('primary', ('−0.8750', '−1.4196', '−0.3750'), 'below zero'),
            'RAW-HARM-MAX minus RAW-HARM-SUM': ('secondary', ('−7.7232', '−9.1163', '−6.4554'), 'below zero'),
            'JOINT-ALLSUM minus CCA-RAW': ('secondary', ('+1.1161', '+0.2587', '+1.9375'), 'above zero'),
            'EIG-JOINT minus JOINT-ALLSUM': ('secondary', ('+0.2679', '−0.0268', '+0.5536'), 'unresolved'),
        }
        self.assertEqual(list(self.a['contrasts']), [f'{k}/u8' for k in want])
        for key, (role, fig, d) in want.items():
            c = self.a['contrasts'][f'{key}/u8']
            self.assertEqual((c['role'], c4(c), c['flags']['direction']), (role, fig, d), key)
            self.assertEqual(c['flags']['interval_includes_zero'], d == 'unresolved', key)
        # at the site's two decimals
        self.assertEqual(crow(self.a['contrasts']['RAW-LEAD3-RIDGE minus RAW-HARM-SUM/u8']), ('+0.30', '−0.12', '+0.78'))
        self.assertEqual(crow(self.a['contrasts']['EIG-JOINT minus JOINT-ALLSUM/u8']), ('+0.27', '−0.03', '+0.55'))

    def test_a_levels_match_the_approved_handoff(self):
        want = {  # the approved A/C handoff's arm table: held8, seen32
            'RAW-HARM-MAX': (('75.1786', '70.7315', '80.0270'), ('53.6607', '48.2401', '59.8371')),
            'RAW-HARM-ALLSUM': (('82.0268', '77.9464', '86.1163'), ('68.8862', '63.3594', '74.6121')),
            'JOINT-ALLSUM': (('82.0179', '77.9460', '86.1071'), ('68.8571', '63.3344', '74.5586')),
            'RAW-LEAD3-RIDGE': (('83.2054', '79.3379', '87.0714'), ('69.3304', '64.0546', '74.6888')),
            'EIG-RAW': (('82.9732', '79.0888', '86.8217'), ('70.0022', '64.7185', '75.4314')),
            'EIG-JOINT': (('82.2857', '78.2138', '86.3935'), ('69.2522', '63.7954', '74.9761')),
            'RAW-HARM-SUM': (('82.9018', '78.9018', '86.9297'), ('69.5268', '64.0219', '75.0708')),
            'CCA-RAW': (('80.9018', '76.8033', '85.1342'), ('65.4598', '59.9369', '71.4018')),
        }
        self.assertEqual(list(self.a['levels']), [f'{c}/{e}' for c in want for e in ('u8', 'seen_ba')])
        for code, (u8, sba) in want.items():
            self.assertEqual((l4(self.a['levels'][f'{code}/u8']), l4(self.a['levels'][f'{code}/seen_ba'])), (u8, sba))
        self.assertEqual(lrow(self.a['levels']['RAW-HARM-SUM/u8']), ('82.90', '78.90', '86.93'))

    def test_a_reuses_card_9_and_card_5_bit_for_bit_and_says_so(self):
        coh = self.docs['coherence_aggregate']['arms']
        card5 = self.docs['released']['studies']['cca_diagnostics']['levels']
        for code in ('EIG-RAW', 'EIG-JOINT', 'RAW-HARM-SUM', 'CCA-RAW'):
            for e, src in bp.ENDPOINTS.items():
                lv = self.a['levels'][f'{code}/{e}']
                self.assertEqual((lv['estimate'], lv['interval']), (coh[code][src]['mean'], coh[code][src]['ci95']))
        for e in ('u8', 'seen_ba'):
            self.assertEqual(self.a['levels'][f'CCA-RAW/{e}']['estimate'], card5[f'CCA-RAW/{e}']['estimate'])
            self.assertEqual(self.a['levels'][f'CCA-RAW/{e}']['interval'], card5[f'CCA-RAW/{e}']['interval'])
        origins = {lid.split('/')[0]: lv['origin'] for lid, lv in self.a['levels'].items()}
        self.assertEqual(origins, {'RAW-HARM-MAX': 'new', 'RAW-HARM-ALLSUM': 'new', 'JOINT-ALLSUM': 'new',
                                   'RAW-LEAD3-RIDGE': 'new', 'EIG-RAW': 'reused_coherence_eigen',
                                   'EIG-JOINT': 'reused_coherence_eigen', 'RAW-HARM-SUM': 'reused_coherence_eigen',
                                   'CCA-RAW': 'reused_cca_diagnostics'})
        self.assertEqual({k: (v['card'], v['anchor']) for k, v in self.a['reused'].items()},
                         {'EIG-RAW': (9, 'eigenvalue-pooling'), 'EIG-JOINT': (9, 'eigenvalue-pooling'),
                          'RAW-HARM-SUM': (9, 'eigenvalue-pooling'), 'CCA-RAW': (5, 'cca-mechanism')})
        self.assertIn('new-ssvep-frequencies-update.json#/studies/cca_diagnostics/levels/CCA-RAW~1u8',
                      self.a['export_codes']['CCA-RAW/u8'])

    def test_a_design_seeds_and_names(self):
        d = self.a['design']
        self.assertEqual((d['dataset']['people'], d['dataset']['windows'], d['dataset']['person_folds'],
                          d['dataset']['frequency_rotations'], d['dataset']['targets']), (70, 11200, 7, 5, 40))
        self.assertEqual(d['fit_operations'], {'main': 35, 'independent_refits': 35, 'bridges': 3,
                                               'label_permutation_check': 1, 'total': 74})
        self.assertEqual(d['endpoints']['seen_ba']['role'], 'descriptive')
        self.assertEqual(d['endpoints']['u8'], {'candidate_count': 8, 'chance': 0.125, 'role': 'contrasts'})
        for lid, lv in self.a['levels'].items():
            want = 'deterministic fit' if lid.split('/')[0] in bp.LEARNED else 'no training'
            self.assertEqual(lv['seeds'], want, lid)
        self.assertTrue(all(cid.endswith('/u8') for cid in self.a['contrasts']))   # seen-32 is descriptive only
        self.assertEqual(self.a['display_names']['RAW-LEAD3-RIDGE'], 'top-three ridge')
        self.assertEqual(self.a['display_names']['CCA-RAW'], 'CCA (no training)')
        for name, code in bp.NAME_KEY:
            self.assertEqual(self.a['display_names'][code], name)

    # ------------------------------------------------------------------ module C (Wearable-102)
    def test_c_primaries_dry_and_wet_are_unresolved(self):
        dry, wet = (self.c['contrasts'][f'EIG-RAW minus RAW-HARM-SUM/{k}'] for k in ('dry', 'wet'))
        self.assertEqual((dry['role'], c4(dry)), ('primary', ('−0.3595', '−1.0623', '+0.3107')))
        self.assertEqual((wet['role'], c4(wet)), ('primary', ('+0.3595', '−0.2371', '+0.9395')))
        self.assertEqual({dry['flags']['direction'], wet['flags']['direction']}, {'unresolved'})
        self.assertEqual(sum(c['role'] == 'primary' for c in self.c['contrasts'].values()), 2)

    def test_c_secondaries_match_the_release_review(self):
        want = {
            'EIG-RAW minus CCA-RAW/dry': ('+0.3023', '−0.7271', '+1.2745'),
            'RAW-LEAD3-RIDGE minus RAW-HARM-SUM/dry': ('−1.5278', '−2.1895', '−0.8738'),
            'EIG-RAW minus RAW-LEAD3-RIDGE/dry': ('+1.1683', '+0.6699', '+1.6667'),
            'EIG-RAW minus CCA-RAW/wet': ('+1.4788', '+0.5801', '+2.3940'),
            'RAW-LEAD3-RIDGE minus RAW-HARM-SUM/wet': ('−0.5065', '−1.0784', '+0.0408'),
            'EIG-RAW minus RAW-LEAD3-RIDGE/wet': ('+0.8660', '+0.4737', '+1.2665'),
            'EIG-JOINT minus JOINT-ALLSUM/wet': ('−0.0327', '−0.3023', '+0.2369'),
        }
        for cid, fig in want.items():
            self.assertEqual((self.c['contrasts'][cid]['role'], c4(self.c['contrasts'][cid])), ('secondary', fig), cid)

    def test_the_dry_joint_contrast_is_flagged_so_it_prints_0_00_never_minus_0_00(self):
        c = self.c['contrasts']['EIG-JOINT minus JOINT-ALLSUM/dry']
        self.assertIs(c['flags']['levels_equal'], True)
        self.assertEqual(self.c['levels']['EIG-JOINT/dry']['estimate'], self.c['levels']['JOINT-ALLSUM/dry']['estimate'])
        self.assertEqual(pp2(c['estimate']), '−0.00')            # what a naive formatter would print: the flag stops it
        self.assertEqual(sum('levels_equal' in x['flags'] for b in self.blocks.values()
                             for x in b['contrasts'].values()), 1)

    def test_the_cca_row_is_card_7s_level_only(self):
        card7 = self.docs['released']['studies']['wearable_transfer']['levels']
        self.assertEqual(self.c['level_only'], {'CCA-RAW/dry': 'wearable_transfer CCA-RAW/dry',
                                                'CCA-RAW/wet': 'wearable_transfer CCA-RAW/wet'})
        for k in ('dry', 'wet'):
            lv = self.c['levels'][f'CCA-RAW/{k}']
            self.assertEqual(lv['estimate'], card7[f'CCA-RAW/{k}']['estimate'])
            self.assertIsNone(lv['interval'])
            self.assertEqual(lv['origin'], 'reused_wearable_transfer')
        self.assertEqual(pct2(self.c['levels']['CCA-RAW/dry']['estimate']), '65.38')
        self.assertEqual(self.c['reused'], {'CCA-RAW': {'card': 7, 'study': 'wearable_transfer',
                                                        'anchor': 'wearable-transfer', 'code': 'CCA-RAW'}})
        self.assertEqual(self.c['display_names']['CCA-RAW'], 'matched CCA')
        # C's own CCA intervals (seed 20261020) are nowhere in the block: no second interval for card 7's arm.
        own = self.docs['ac_summary']['verified_C_aggregate']['levels']
        carried = set(floats(self.c))
        for k in ('dry', 'wet'):
            self.assertFalse(set(own[k]['CCA-RAW']['ci95']) & carried, k)

    def test_c_levels_match_the_approved_handoff(self):
        want = {  # the approved handoff's target table: dry, wet (CCA's interval is card 7's business)
            'EIG-RAW': ('65.6781', '83.1291'), 'EIG-JOINT': ('66.7892', '83.4477'),
            'RAW-LEAD3-RIDGE': ('64.5098', '82.2631'), 'CCA-RAW': ('65.3758', '81.6503'),
            'RAW-HARM-SUM': ('66.0376', '82.7696'), 'RAW-HARM-MAX': ('60.9967', '77.7451'),
            'RAW-HARM-ALLSUM': ('66.8301', '83.5376'), 'JOINT-ALLSUM': ('66.7892', '83.4804'),
        }
        for code, (dry, wet) in want.items():
            self.assertEqual((js_fixed(self.c['levels'][f'{code}/dry']['estimate'] * 100, 4),
                              js_fixed(self.c['levels'][f'{code}/wet']['estimate'] * 100, 4)), (dry, wet), code)

    def test_c_scope_strip(self):
        d = self.c['design']
        self.assertEqual(d['dataset']['same_windows_as'], 'wearable_transfer')
        self.assertEqual(d['dataset']['tie_rule'], 'first native candidate index')
        self.assertEqual(d['dataset']['candidate_order'], 'native order, unsorted')
        self.assertEqual((d['dataset']['windows'], d['dataset']['windows_per_sensor'], d['dataset']['window_s']),
                         (24480, 12240, [0.14, 2.14]))
        sh = d['source_heads']
        self.assertEqual((sh['heads_per_learned_arm'], sh['learned_arms'], sh['target_fits'],
                          sh['collapsed_to_one_affine_function'], sh['retraining']), (35, 3, 0, True, False))
        self.assertEqual(sh['coefficients'], {'EIG-RAW': {'weights': 6, 'bias': 1}, 'EIG-JOINT': {'weights': 6, 'bias': 1},
                                              'RAW-LEAD3-RIDGE': {'weights': 3, 'bias': 1}})
        self.assertEqual(d['endpoints']['dry']['chance'], 1 / 12)
        self.assertNotIn('frequencies_hz', json.dumps(self.c))

    # ------------------------------------------------------------------ what the blocks never carry
    def test_no_private_text_host_or_thread_material(self):
        text = json.dumps(self.blocks, ensure_ascii=False)
        self.assertIsNone(PRIVATE.search(text))
        self.assertNotIn('pending', text.lower())
        self.assertNotIn('thread_bet', text)
        self.assertNotIn('55%', text)
        self.assertFalse(any(abs(x - 0.55) < 1e-12 or abs(x - 55) < 1e-9 for x in floats(self.blocks)))
        for b in self.blocks.values():
            self.assertNotIn('release_status', json.dumps(b))
            self.assertTrue(all(k in bp.LIMITATION_SOURCES[s] for s in bp.STUDIES if self.blocks[s] is b
                                for k in b['limitations_keys']))

    def test_declared_edits_and_name_key_cover_both_studies(self):
        self.assertEqual(set(bp.DECLARED_EDITS), set(bp.STUDIES))
        self.assertEqual(set(bp.HANDOFF_CONTEXT), set(bp.STUDIES))
        self.assertEqual(bp.HANDOFF_CONTEXT[A]['bound_sha256'], self.docs['ac_approval']['handoff_sha256'])


@unittest.skipUnless(bp.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class PoolingRefusals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = bp.load()

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)

    def build(self):
        bp.check_bindings(self.d, self.h)
        return bp.pooling_block(self.d, self.h), bp.wearable_block(self.d, self.h)

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(bp.PINS)
        pins['ac_summary']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            bp.build_blocks(pins)

    def test_pins_of_another_shape_are_refused(self):
        pins = copy.deepcopy(bp.PINS)
        del pins['released']
        with self.assertRaisesRegex(ValueError, 'pins: expected'):
            bp.build_blocks(pins)

    def test_release_status_comes_from_the_approval_not_the_summary(self):
        self.d['ac_summary']['status'] = 'anything'
        self.d['ac_summary']['verified_A_aggregate']['release_status'] = 'anything'
        self.build()                                         # the summary's own status is never read
        self.d['ac_approval']['status'] = 'HOLD'
        self.refused('release approval')

    def test_an_approval_that_binds_another_summary_is_refused(self):
        self.h['ac_summary'] = 'f' * 64
        self.refused('binds')

    def test_the_approval_must_bind_the_aggregates_the_summary_names(self):
        self.d['ac_summary']['aggregate_sha256']['A'] = 'a' * 64
        self.refused('other aggregates')

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.d['ac_summary']['verified_A_aggregate']['contrasts'][0]['mean'] += 1e-6
        self.refused('not the difference of its levels')

    def test_an_interval_must_hold_its_point(self):
        self.d['ac_summary']['verified_A_aggregate']['arms']['RAW-HARM-MAX']['held8']['ci95'] = [0.76, 0.80]
        self.refused('does not hold its point')

    def test_a_reused_level_must_be_card_9s_bit_for_bit(self):
        self.d['coherence_aggregate']['arms']['EIG-RAW']['held8']['mean'] += 1e-12
        self.refused('card 9')

    def test_a_reused_cca_must_be_card_5s_as_released(self):
        lv = self.d['released']['studies']['cca_diagnostics']['levels']['CCA-RAW/u8']
        lv['interval'] = [lv['interval'][0], lv['interval'][1] + 1e-9]
        self.refused('card 5')

    def test_the_wearable_cca_must_be_card_7s_released_level(self):
        self.d['released']['studies']['wearable_transfer']['levels']['CCA-RAW/wet']['estimate'] += 1e-12
        self.refused('card 7')

    def test_the_wearable_windows_must_be_card_7s(self):
        self.d['wear_freeze']['input_sha256']['epochs250.npy'] = 'b' * 64
        self.refused('epochs250.npy is not card 7')

    def test_the_tie_rule_must_be_the_native_first_index(self):
        self.d['ac_protocol']['modules']['C']['tie_rule'] = 'ascending frequency'
        self.refused('tie rule')

    def test_a_role_must_be_the_protocols(self):
        pa = self.d['ac_protocol']['modules']['A']
        pa['primary_contrasts'], pa['secondary_contrasts'] = pa['secondary_contrasts'], pa['primary_contrasts']
        self.refused('differ from the protocol')
        self.d = copy.deepcopy(self.docs)
        self.d['ac_summary']['verified_C_aggregate']['contrasts']['wet']['EIG-RAW minus RAW-HARM-SUM']['primary'] = False
        self.refused('role')

    def test_a_figure_the_release_review_does_not_print_is_refused(self):
        c = self.d['ac_summary']['verified_C_aggregate']['contrasts']['dry']['EIG-RAW minus CCA-RAW']
        c['ci95'] = [c['ci95'][0] - 1e-4, c['ci95'][1]]
        self.refused('release review does not print')

    def test_a_level_the_approved_handoff_does_not_print_is_refused(self):
        m = self.d['ac_summary']['verified_C_aggregate']['levels']['wet']['RAW-HARM-MAX']
        m['ci95'] = [m['ci95'][0], m['ci95'][1] + 1e-4]
        self.refused('approved handoff does not print')

    def test_an_unlabelled_equal_level_contrast_with_real_size_is_refused(self):
        c = self.d['ac_summary']['verified_C_aggregate']['contrasts']['dry']['EIG-JOINT minus JOINT-ALLSUM']
        c['mean'] = 1e-13
        self.refused('equal levels')

    def test_a_limitation_its_record_does_not_state_is_refused(self):
        self.d['ac_interpretation_review'] = self.d['ac_interpretation_review'].replace(
            'not universal second-component irrelevance', 'universal irrelevance')
        self.refused('does not state')

    def test_a_display_name_is_required_for_every_code(self):
        names = copy.deepcopy(bp.DISPLAY_NAMES)
        del names[A]['JOINT-ALLSUM']
        with mock.patch.object(bp, 'DISPLAY_NAMES', names):
            self.refused('no display name')

    def test_the_scrub_refuses_what_must_not_be_published(self):
        for bad in ({'pid': 1}, {'private_root': 'x'}, {'rows': [0, 159]}, {'per_seed_values': []},
                    {'note': '/mnt/bigdata/x'}, {'note': 'run on trx50'}, {'x': [0, 159, 160, 5599]}, {'x': 0.55},
                    {'note': 'beat 55% held-out'}, {'note': 'release review pending'}, {'note': 'the v2 rule'},
                    {'note': 'the best pooling'}, {'status': 'ok'}, {'release_status': 'x'}, {'thread_bet': {}},
                    {'canary_targets': 7454}, {'feature_rows': 6}, {'frequencies_hz': [9.25]}, {'note': 'Jev asked'},
                    {'code': 'x#/rows/55'}, {'note': 'a .55 share'}):
            with self.assertRaises(ValueError, msg=repr(bad)):
                bp.scrub_check(bad)
        bp.scrub_check({'note': 'harmonic sum (no training)', 'x': 0.8290178571428571, 'r': [0.14, 2.14]})


if __name__ == '__main__':
    unittest.main()
