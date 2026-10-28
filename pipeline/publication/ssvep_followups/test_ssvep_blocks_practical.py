"""SS-B, the practical-settings block (card 11) and its CPU component record: what it must carry, and what it must
refuse.

Expected figures are written out from the records that state them (the approved B/D handoff's tables, the B/D
interpretation review, the approved timing handoff and the plan's card 11), rendered the way the site renders them:
JavaScript toFixed on the double value, so an exact decimal tie rounds away from zero.
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
from ssvep_followups import blocks_practical as bpr                           # noqa: E402
from ssvep_followups.test_ssvep_blocks_cca import crow, floats, js_fixed, lrow   # noqa: E402

S = bpr.STUDY
FB, SUM, CCA, LEAD3, EIG6 = 'FBCCA-M3-N7-H5', 'RAW-HARM-SUM-H3', 'CCA-RAW-H3', 'RAW-LEAD3-RIDGE', 'EIG-RAW6-RIDGE'
GRID_CELLS = ['w125-c4', 'w125-c8', 'w250-c4', 'w250-c8', 'w500-c4', 'w500-c8']
GRID_METHODS = [CCA, SUM, LEAD3, EIG6, FB]
HOST = re.compile(r'threadripper|ryzen|\bamd\b|(?<![\d.])7965(?!\d)|epyc|xeon|\bintel\b|linux|ubuntu|ext4|/dev/'
                  r'|\bsda\b|trx|gal4'
                  r'|\bmac\b|arm64|python\s*\d|numpy\s*\d|scipy\s*\d|logical|/mnt|/home|/Users|/Volumes|\btwu\b', re.I)


def p4(raw):
    return ('' if raw == 0 else '+' if raw > 0 else '−') + js_fixed(abs(raw * 100), 4)


def c4(c):
    return p4(c['estimate']), p4(c['interval'][0]), p4(c['interval'][1])


def l4(lv):
    return tuple(js_fixed(x * 100, 4) for x in (lv['estimate'], *lv['interval']))


def ms4(m):
    return tuple(js_fixed(m[k], 4) for k in ('median', 'min', 'max'))


def cid(left, right):
    return f'{left} minus {right}/u8'


@unittest.skipUnless(bpr.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class PracticalBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bpr.build_blocks()
        cls.b = cls.blocks[S]
        cls.cpu = cls.b['cpu_components']
        cls.docs, cls.digests = bpr.load()

    # ------------------------------------------------------------------ shape
    def test_one_block_with_the_fields_of_the_earlier_blocks(self):
        self.assertEqual(tuple(self.blocks), ('practical_settings',))
        for k in bpr.BLOCK_FIELDS + ('design', 'grid', 'contrast_groups', 'contrast_limitations', 'qualifiers',
                                     'reproduces', 'answers_not_run', 'cpu_components'):
            self.assertIn(k, self.b)
        self.assertEqual((self.b['card'], self.b['anchor']), (11, 'practical-settings'))
        self.assertEqual((len(self.b['levels']), len(self.b['contrasts'])), (60, 41))     # 6 cells x 5 x 2 tasks
        self.assertEqual(set(self.b['export_codes']), set(self.b['levels']) | set(self.b['contrasts']))
        for lid, lv in self.b['levels'].items():
            self.assertEqual(set(lv), {'estimate', 'interval', 'unit', 'people', 'seeds', 'origin'}, lid)
            self.assertEqual((lv['unit'], lv['people'], lv['origin']), ('proportion', 70, 'new'))
            self.assertTrue(0 <= lv['interval'][0] <= lv['estimate'] <= lv['interval'][1] <= 1)
            self.assertIn(lid.split('/')[1], self.b['display_names'])
        for c in self.b['contrasts'].values():
            self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'unit', 'people', 'seeds',
                                      'flags'})
            self.assertTrue(c['left'].endswith('/u8') and c['right'].endswith('/u8'))
            self.assertTrue(-1 <= c['interval'][0] <= c['estimate'] <= c['interval'][1] <= 1)
        for codes in self.b['export_codes'].values():
            self.assertTrue(codes and all(re.fullmatch(r'(?:[\w.-]+)?#(?:/[^/]+)+', x) for x in codes), codes)
        site = {v[0]: k for k, v in bpr.COMPONENTS.items()}
        rows = self.docs['timing_aggregate']['component_summaries']
        for gid, codes in self.cpu['export_codes'].items():
            m = re.fullmatch(r'timing_aggregate#component_summaries\[cell=([\w-]+)\]\[batch=(\d+)\]\[component=(\w+)\]',
                             codes[0])
            self.assertIsNotNone(m, codes)
            hit = [r for r in rows if (r['cell'], r['batch'], r['component']) == (m[1], int(m[2]), site[m[3]])]
            self.assertEqual(len(hit), 1, gid)
            self.assertEqual(hit[0]['wall_ms_per_call'], self.cpu['groups'][gid]['wall_ms_per_call'])

    def test_the_build_is_deterministic_and_public(self):
        self.assertEqual(json.dumps(bpr.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))
        validate_public(self.blocks)

    def test_interval_method_and_seeds(self):
        m = self.b['interval_method']
        self.assertEqual((m['method'], m['draws'], m['seed'], m['level']),
                         ('paired person bootstrap, percentile interval', 2000, 20261015, 0.95))
        for lid, lv in self.b['levels'].items():
            self.assertEqual(lv['seeds'], 'deterministic fit' if lid.split('/')[1] in (LEAD3, EIG6) else 'no training')

    # ------------------------------------------------------------------ the 6 x 5 grid
    def test_the_grid_is_in_prospective_order_not_sorted(self):
        g = self.b['grid']
        self.assertEqual((g['order'], g['cells'], g['methods']), ('prospective', GRID_CELLS, GRID_METHODS))
        self.assertEqual([c['id'] for c in self.b['design']['cells']], GRID_CELLS)
        self.assertEqual(g['table']['u8'], [[f'{c}/{m}/u8' for m in GRID_METHODS] for c in GRID_CELLS])
        self.assertEqual(g['roles'], {'u8': 'primary and secondary contrasts', 'seen_ba': 'descriptive'})
        # a score order would differ: at 0.5 s and 8 electrodes the harmonic sum is below CCA
        row = [self.b['levels'][x]['estimate'] for x in g['table']['u8'][1]]
        self.assertNotEqual(row, sorted(row))
        flat = [self.b['levels'][x]['estimate'] for r in g['table']['u8'] for x in r]
        self.assertNotEqual(flat, sorted(flat))

    def test_held_out_grid_matches_the_approved_handoff(self):
        want = [  # handoff, held-eight table, prospective order
            ('23.9911', '24.5357', '24.8036', '25.0804', '30.4018'),
            ('24.3304', '24.0893', '24.1964', '24.4196', '32.4911'),
            ('52.7768', '54.5893', '55.3929', '55.4554', '63.7679'),
            ('54.9911', '56.8036', '57.1250', '57.3750', '69.2500'),
            ('77.2143', '78.9196', '79.5357', '79.7946', '85.7946'),
            ('80.9018', '82.9018', '83.2054', '82.9732', '90.2143'),
        ]
        got = [tuple(js_fixed(self.b['levels'][x]['estimate'] * 100, 4) for x in r) for r in self.b['grid']['table']['u8']]
        self.assertEqual(got, want)
        self.assertEqual(l4(self.b['levels'][f'w500-c8/{FB}/u8']), ('90.2143', '87.6516', '92.6161'))
        self.assertEqual(lrow(self.b['levels'][f'w500-c8/{FB}/u8']), ('90.21', '87.65', '92.62'))

    def test_seen_32_grid_is_descriptive(self):
        want = [
            ('6.6719', '6.8661', '6.8281', '6.9375', '10.5223'),
            ('6.7455', '6.3549', '6.2455', '6.4710', '11.4665'),
            ('26.0246', '28.0536', '27.8996', '28.5580', '40.5603'),
            ('28.5000', '30.1451', '30.1384', '30.7679', '47.7545'),
            ('60.1719', '63.1027', '63.4554', '64.4442', '74.2321'),
            ('65.4598', '69.5268', '69.3304', '70.0022', '80.7634'),
        ]
        got = [tuple(js_fixed(self.b['levels'][x]['estimate'] * 100, 4) for x in r)
               for r in self.b['grid']['table']['seen_ba']]
        self.assertEqual(got, want)
        self.assertEqual(self.b['design']['endpoints']['seen_ba']['role'], 'descriptive')
        self.assertFalse(any('seen_ba' in x for x in self.b['contrasts']))

    # ------------------------------------------------------------------ the 41 contrasts
    def test_all_41_contrasts_keep_their_own_studys_role(self):
        st = self.docs['bd_protocol']['design']['statistics']
        self.assertEqual(sum(c['role'] == 'primary' for c in self.b['contrasts'].values()), 7)
        self.assertEqual([c['role'] for c in self.b['contrasts'].values()], ['primary'] * 7 + ['secondary'] * 34)
        self.assertEqual(len(st['primary_contrasts']) + len(st['secondary_contrasts']), 41)
        self.assertEqual(self.b['design']['primary']['B'], [cid(f'w500-c8/{FB}', f'w500-c8/{SUM}')])
        self.assertEqual(self.b['design']['primary']['D'], [cid(f'{c}/{EIG6}', f'{c}/{SUM}') for c in GRID_CELLS])
        self.assertEqual({k: len(v) for k, v in self.b['contrast_groups'].items()},
                         {'method': 26, 'window': 10, 'electrodes': 5})
        self.assertEqual(sum(len(v) for v in self.b['contrast_groups'].values()), 41)
        # the 2 s / 8 electrode cell reproduces card 10, with other roles
        here = self.b['contrasts'][cid(f'w500-c8/{LEAD3}', f'w500-c8/{SUM}')]
        self.assertEqual((here['role'], c4(here)), ('secondary', ('+0.3036', '−0.1250', '+0.7768')))

    def test_the_lead_figures(self):
        k = self.b['contrasts']
        self.assertEqual(c4(k[cid(f'w500-c8/{FB}', f'w500-c8/{SUM}')]), ('+7.3125', '+5.1516', '+9.4734'))
        self.assertEqual(crow(k[cid(f'w500-c8/{FB}', f'w500-c8/{CCA}')]), ('+9.31', '+6.84', '+11.71'))
        self.assertEqual(c4(k[cid(f'w500-c8/{FB}', f'w500-c8/{CCA}')]), ('+9.3125', '+6.8391', '+11.7143'))
        self.assertEqual(c4(k[cid(f'w500-c8/{EIG6}', f'w500-c8/{FB}')]), ('−7.2411', '−9.3036', '−5.1783'))
        d_pos = [x for x in self.b['design']['primary']['D'] if k[x]['flags']['direction'] == 'above zero']
        self.assertEqual(d_pos, [cid(f'w500-c4/{EIG6}', f'w500-c4/{SUM}')])
        self.assertEqual(c4(k[d_pos[0]]), ('+0.8750', '+0.0804', '+1.6964'))

    def test_window_contrasts(self):
        k, w = self.b['contrasts'], self.b['contrast_groups']['window']
        self.assertEqual(c4(k[cid(f'w125-c4/{FB}', f'w500-c4/{FB}')]), ('−55.3929', '−57.4558', '−53.2768'))
        self.assertEqual(c4(k[cid(f'w125-c8/{FB}', f'w500-c8/{FB}')])[0], '−57.7232')
        self.assertEqual({k[x]['flags']['direction'] for x in w}, {'below zero'})
        self.assertTrue(all(x.startswith('w125-') and ' minus w500-' in x for x in w))
        self.assertEqual({tuple(self.b['contrast_limitations'][x]) for x in w}, {('observation_window_not_latency',)})

    def test_electrode_contrasts_and_the_0_5_s_qualifier(self):
        k, e = self.b['contrasts'], self.b['contrast_groups']['electrodes']
        self.assertEqual(c4(k[cid(f'w250-c4/{FB}', f'w250-c8/{FB}')]), ('−5.4821', '−7.1257', '−3.8391'))
        raw = [x for x in e if FB not in x]
        self.assertEqual(sorted(js_fixed(abs(k[x]['estimate'] * 100), 2) for x in raw), ['1.73', '1.92', '2.21', '2.21'])
        self.assertEqual({k[x]['flags']['direction'] for x in e}, {'below zero'})
        q = self.b['qualifiers']['eight_electrodes_not_always_better']
        self.assertEqual((q['cells'], q['methods_four_above_eight'], q['paired_interval']),
                         (['w125-c4', 'w125-c8'], [SUM, LEAD3, EIG6], None))
        self.assertIn('eight_not_always_better', self.b['limitations_keys'])
        for m in q['methods_four_above_eight']:
            self.assertGreater(self.b['levels'][f'w125-c4/{m}/u8']['estimate'],
                               self.b['levels'][f'w125-c8/{m}/u8']['estimate'])
        self.assertFalse(any(x.startswith('w125-c4/') and ' minus w125-c8/' in x for x in k))

    def test_undefined_and_not_run(self):
        self.assertEqual(self.b['undefined'], [{'contrast': cid(f'w500-c8/{FB}', f'w500-c8/{LEAD3}'),
                                                'reason': 'no paired interval was registered'}])
        self.assertNotIn(self.b['undefined'][0]['contrast'], self.b['contrasts'])
        self.assertEqual(self.b['answers_not_run'][0]['item'], 'filter-bank CCA')
        self.assertIn('online performance or information transfer rate', [r['item'] for r in self.b['not_run']])

    def test_reproduces_card_10_card_9_and_card_5_bit_for_bit(self):
        pool = bp.build_blocks()['harmonic_pooling']
        card5 = self.docs['released']['studies']['cca_diagnostics']['levels']
        for r in self.b['reproduces']:
            if r['card'] == 10:
                there = (pool['contrasts'] if ' minus ' in r['there'] else pool['levels'])[r['there']]
                here = (self.b['contrasts'] if ' minus ' in r['here'] else self.b['levels'])[r['here']]
                self.assertEqual((here['estimate'], here['interval']), (there['estimate'], there['interval']))
                if 'role_there' in r:
                    self.assertEqual((here['role'], there['role']), (r['role_here'], r['role_there']))
                    self.assertNotEqual(r['role_here'], r['role_there'])
            elif r['card'] == 5:
                self.assertEqual(self.b['levels'][r['here']]['estimate'], card5[r['there']]['estimate'])
        self.assertEqual(sorted({r['card'] for r in self.b['reproduces']}), [5, 9, 10])

    # ------------------------------------------------------------------ the recipe
    def test_the_filter_bank_recipe_is_named(self):
        fb = self.b['design']['fbcca']
        self.assertEqual(fb['description']['en'], 'filter-bank CCA (seven Chebyshev sub-bands, five harmonics), our '
                                                  'SciPy realisation of the published recipe')
        self.assertTrue(fb['description']['zh'])
        self.assertEqual((fb['sub_bands'], fb['harmonics'], fb['trained_head']), (7, 5, False))
        self.assertTrue(fb['filter'].startswith('Chebyshev type I'))
        other = fb['other_recipe_on_site']
        self.assertEqual((other['code'], other['sub_bands'], other['filter'], other['release_id']),
                         ('S11', 5, 'Butterworth', 'questions-in-language-update-20261008'))
        self.assertEqual(self.b['display_names'][FB], 'filter-bank CCA (seven sub-bands)')
        self.assertEqual(self.b['design']['electrodes']['four'], ['POZ', 'O1', 'OZ', 'O2'])
        self.assertEqual(self.b['design']['preprocessing']['author_band_hz'], [3, 100])
        self.assertIs(self.b['design']['preprocessing']['crop_before_new_filtering'], True)

    # ------------------------------------------------------------------ D25: CPU components
    def test_cpu_label_and_measurement(self):
        self.assertEqual(self.cpu['label']['en'], 'components; not sensor-to-decision or online latency')
        self.assertTrue(self.cpu['label']['zh'])
        m = self.cpu['measurement']
        self.assertEqual((m['clock'], m['unit'], m['statistic'], m['measured_calls'], m['warmup_calls_excluded'],
                          m['threads'], m['gpu'], m['summed']), ('wall', 'ms', 'median [min, max]', 3, 1, 1, False, False))
        self.assertEqual(len(self.cpu['groups']), 72)
        self.assertEqual(self.cpu['order'], list(self.cpu['groups']))
        self.assertEqual(self.cpu['order'][:2], ['w125-c4/1/crop', 'w125-c4/1/raw_filter'])
        self.assertIn('components_never_summed', self.cpu['limitations_keys'])

    def test_cpu_anchor_figures(self):
        g = self.cpu['groups']
        self.assertEqual(ms4(g['w500-c8/1/fbcca']['wall_ms_per_call']), ('7.4541', '6.9932', '8.0188'))
        self.assertEqual(ms4(g['w500-c8/8/fbcca']['wall_ms_amortised'])[0], '2.8177')
        self.assertEqual(ms4(g['w500-c8/8/fbcca']['wall_ms_per_call'])[0], '22.5413')
        self.assertEqual(ms4(g['w500-c8/1/raw_geometry']['wall_ms_per_call'])[0], '1.3860')
        self.assertEqual(ms4(g['w500-c8/1/raw_filter']['wall_ms_per_call'])[0], '1.2281')
        self.assertEqual(ms4(g['w500-c8/1/top3_readout']['wall_ms_per_call'])[0], '0.0303')
        self.assertEqual(ms4(g['w500-c8/1/eigenvalue_readout']['wall_ms_per_call'])[0], '0.0595')
        for x in g.values():
            for k in ('median', 'min', 'max'):
                self.assertAlmostEqual(x['wall_ms_amortised'][k], x['wall_ms_per_call'][k] / x['batch'], places=12)

    def test_cpu_components_are_never_summed_and_carry_no_host(self):
        text = json.dumps(self.blocks, ensure_ascii=False)
        self.assertIsNone(HOST.search(text))
        self.assertNotIn('cpu_ms', text)
        anchor = [self.cpu['groups'][f'w500-c8/1/{c}']['wall_ms_per_call']['median'] for c, _ in
                  [(v[0], v[1]) for v in bpr.COMPONENTS.values()]]
        carried = list(floats(self.cpu))
        for total in (sum(anchor), sum(anchor[1:4]), anchor[1] + anchor[2] + anchor[4]):
            self.assertFalse(any(abs(x - total) < 1e-9 for x in carried))
        for key in ('total', 'sum', 'end_to_end', 'latency'):
            self.assertNotIn(f'"{key}"', text)

    def test_no_private_text_or_thread_material(self):
        text = json.dumps(self.blocks, ensure_ascii=False)
        token = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])')     # the release's token rule (R5 M7), on every string
        strings = [x for x in re.findall(r'"((?:[^"\\]|\\.)*)"', text) if not re.fullmatch(r'[0-9a-f]{64}', x)]
        self.assertEqual([x for x in strings if token.search(x)], [])
        self.assertNotIn('pending', text.lower())
        self.assertNotIn('thread_bet', text)
        self.assertNotIn('55%', text)
        self.assertFalse(any(abs(x - 0.55) < 1e-12 or abs(x - 55) < 1e-9 for x in floats(self.blocks)))
        self.assertNotIn('release_status', text)
        self.assertNotIn('interpretation"', text)

    def test_declared_edits_and_name_key(self):
        self.assertEqual(set(bpr.DECLARED_EDITS), {'practical_settings', 'cpu_components'})
        self.assertEqual(set(bpr.HANDOFF_CONTEXT), {'practical_settings', 'cpu_components'})
        for name, code in bpr.NAME_KEY:
            self.assertEqual(self.b['display_names'][code.split()[0]], name)


@unittest.skipUnless(bpr.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class PracticalRefusals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = bpr.load()

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)

    def build(self):
        bpr.check_bindings(self.d, self.h)
        return bpr.practical_block(self.d, self.h)

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(bpr.PINS)
        pins['timing_aggregate']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            bpr.build_blocks(pins)

    def test_release_status_comes_from_the_approval(self):
        self.d['bd_aggregate']['release_status'] = 'anything'
        self.build()
        self.d['bd_approval']['scientific_result_release_approved'] = False
        self.refused('not approved')

    def test_the_approval_must_bind_the_aggregate_and_reviews(self):
        self.h['bd_interpretation_review'] = 'e' * 64
        self.refused('binds')

    def test_the_timing_approval_must_bind_its_aggregate(self):
        self.d['timing_approval']['artifacts_sha256']['results/Component Timing Aggregates.json'] = 'c' * 64
        self.refused('timing approval timing_aggregate')

    def test_the_timing_must_be_of_the_b_d_heads(self):
        self.d['timing_protocol']['head_seal_sha256'] = 'd' * 64
        self.refused('another head seal')

    def test_the_grid_must_be_in_prospective_order(self):
        arms = self.d['bd_aggregate']['arms']
        self.d['bd_aggregate']['arms'] = dict(sorted(arms.items(), key=lambda kv: kv[1]['held8']['mean']))
        self.refused('prospective grid order')

    def test_a_role_must_be_the_protocols(self):
        self.d['bd_aggregate']['contrasts'][22]['role'] = 'primary'
        self.refused('differ from the protocol')

    def test_a_source_label_that_disagrees_with_the_interval_is_refused(self):
        self.d['bd_aggregate']['contrasts'][1]['interpretation'] = 'nominal_positive'
        self.refused('the source reads')

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.d['bd_aggregate']['contrasts'][0]['mean'] += 1e-6
        self.refused('not the difference of its levels')

    def test_a_figure_the_approved_handoff_does_not_print_is_refused(self):
        m = self.d['bd_aggregate']['arms']['w250-c8/RAW-LEAD3-RIDGE']['seen32']
        m['mean'] += 1e-5
        m['ci95'] = [m['ci95'][0], m['ci95'][1] + 1e-5]
        self.refused('approved handoff does not print')

    def test_the_card_10_cell_must_be_reproduced(self):
        self.d['ac_summary']['verified_A_aggregate']['arms']['RAW-LEAD3-RIDGE']['held8']['mean'] += 1e-12
        self.refused('card 10')

    def test_a_timing_row_out_of_order_is_refused(self):
        rows = self.d['timing_aggregate']['component_summaries']
        rows[0], rows[1] = rows[1], rows[0]
        self.refused('predefined cell/batch/component order')

    def test_an_amortised_time_that_is_not_the_batch_share_is_refused(self):
        r = next(r for r in self.d['timing_aggregate']['component_summaries'] if r['batch'] == 8)
        r['wall_ms_per_trial']['median'] *= 1.01
        self.refused('batch cost divided by the batch size')

    def test_the_recipe_must_be_chebyshev(self):
        self.d['fbcca_core'] = self.d['fbcca_core'].replace('cheby1(', 'butter(')
        self.refused('Chebyshev')

    def test_the_route_3_recipe_must_be_the_one_the_site_reports(self):
        self.d['route3_protocol']['secondary_contrasts']['S11'] = 'FBCCA: Nh=5; 7 sub-bands'
        self.refused('S11')

    def test_the_qualifier_must_hold_as_the_review_states_it(self):
        lv = self.d['bd_aggregate']['arms']
        for m in GRID_METHODS:
            lv[f'w125-c4/{m}']['held8']['mean'] = 0.0
        with mock.patch.object(bpr, 'handoff_tables', lambda *a: None), \
                mock.patch.object(bpr, 'contrast', lambda c, role, levels, people, label: {
                    'role': role, 'left': f'{c["a"]}/u8', 'right': f'{c["b"]}/u8', 'estimate': c['mean'],
                    'interval': c['ci95'], 'unit': 'difference of proportions', 'people': people, 'seeds': 'x',
                    'flags': {'interval_includes_zero': True,
                              'direction': {'nominal_positive': 'above zero', 'nominal_negative': 'below zero',
                                            'unresolved': 'unresolved'}[c['interpretation']]}}), \
                mock.patch.object(bpr, 'level', lambda m, people, seeds, label: {
                    'estimate': m['mean'], 'interval': m['ci95'], 'unit': 'proportion', 'people': people,
                    'seeds': seeds, 'origin': 'new'}):
            self.refused('0.5 s qualifier')

    def test_the_scrub_refuses_host_labels_sums_and_private_text(self):
        for bad in ({'note': 'AMD Ryzen Threadripper PRO 7965WX'}, {'note': 'Linux 6.8'}, {'note': 'Python 3.10.12'},
                    {'note': 'ext4 on /dev/sda'}, {'note': 'the Mac arm64 runtime'}, {'total': 1.0}, {'sum': 2.0},
                    {'end_to_end_ms': 3.0}, {'latency_ms': 1.0}, {'cpu_ms_per_call': {}}, {'wall_ms_per_trial': {}},
                    {'elapsed_seconds': 1}, {'note': '/mnt/bigdata'}, {'note': 'trx50'}, {'x': 0.55},
                    {'note': 'the fastest cell'}, {'interpretation': 'unresolved'}, {'blocks_per_person': 4},
                    {'code': 'timing_aggregate#/component_summaries/55'}):
            with self.assertRaises(ValueError, msg=repr(bad)):
                bpr.scrub_check(bad)
        bpr.scrub_check({'label': 'components; not sensor-to-decision or online latency',
                         'pass_band_low_edges_hz': [6, 14, 22, 30, 38, 46, 54], 'x': 7.454137})


if __name__ == '__main__':
    unittest.main()
