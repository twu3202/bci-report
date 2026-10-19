"""B3, the CCA blocks (cards 5 to 7): what they must carry, and what they must refuse.

Expected figures are written out from the reviews that state them (the R1 binding review's tables, the diagnostics
release review, the A2 note and the plan), rendered the way the site renders them: JavaScript toFixed on the double
value, so an exact decimal tie rounds away from zero, as the site's pct2, pp2 and sgn2 formatters do.
"""
import copy
import json
import re
import sys
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from unittest import mock

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public               # noqa: E402
from ssvep_followups import blocks_cca as bc               # noqa: E402

U8, SBA = 'u8', 'seen_ba'
ADAPTER_EXPORT = '6f68114e4d431beb4903f68e3e2d4549da825d8f94d2ff3a776e368a7b3dca2b'


def js_fixed(x, digits=2):
    """Number.prototype.toFixed: the exact value of the double, ties away from zero."""
    return str(Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def pct2(raw):
    return js_fixed(raw * 100)


def pp2(raw):
    return ('' if raw == 0 else '+' if raw > 0 else '−') + js_fixed(abs(raw * 100))


def lrow(lv):
    return pct2(lv['estimate']), pct2(lv['interval'][0]), pct2(lv['interval'][1])


def crow(c):
    return pp2(c['estimate']), pp2(c['interval'][0]), pp2(c['interval'][1])


def floats(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from floats(v)
    elif isinstance(value, list):
        for v in value:
            yield from floats(v)
    elif isinstance(value, float):
        yield value


class FormatterEmulation(unittest.TestCase):
    def test_ties_round_away_from_zero_as_javascript_does(self):
        self.assertEqual(pct2(0.63125), '63.13')                 # R1: Python's format gives 63.12 here
        self.assertEqual(pp2(-0.0012499999999999892), '−0.12')
        self.assertEqual(pp2(0.04374999999999999), '+4.37')
        self.assertEqual(js_fixed(0.200001, 1), '0.2')


@unittest.skipUnless(bc.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class CcaBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bc.build_blocks()
        cls.diag, cls.adapter, cls.wear = (cls.blocks[k] for k in bc.STUDIES)
        cls.docs, cls.digests = bc.load()

    # ------------------------------------------------------------------ shape
    def test_three_blocks_with_the_b1_fields(self):
        self.assertEqual(tuple(self.blocks), bc.STUDIES)
        for name, b in self.blocks.items():
            for k in bc.BLOCK_FIELDS + ('design', 'contrast_limitations'):
                self.assertIn(k, b, f'{name} lacks {k}')
            self.assertEqual(set(b['export_codes']), set(b['levels']) | set(b['contrasts']), name)
            for lid, lv in b['levels'].items():
                self.assertEqual(set(lv), {'estimate', 'interval', 'unit', 'people', 'seeds', 'origin'}, lid)
                self.assertEqual(lv['unit'], 'proportion')
                self.assertIn(lid.split('/')[0], b['display_names'])
            for cid, c in b['contrasts'].items():
                self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'unit', 'people', 'seeds',
                                          'flags'}, cid)
                self.assertEqual(c['unit'], 'difference of proportions')
                self.assertIn(c['left'], b['levels'])
                self.assertIn(c['right'], b['levels'])
            for codes in b['export_codes'].values():
                self.assertTrue(codes and all(re.fullmatch(r'(?:[\w-]+(?:\.json)?)?#(?:/[^/]+)+', x) for x in codes), codes)
        self.assertEqual((len(self.diag['levels']), len(self.diag['contrasts'])), (14, 14))     # 7 x 2 endpoints
        self.assertEqual((len(self.adapter['levels']), len(self.adapter['contrasts'])), (12, 12))
        self.assertEqual([c['role'] for c in self.wear['contrasts'].values()], ['primary', 'primary', 'secondary'])
        self.assertEqual({c['role'] for b in (self.diag, self.adapter) for c in b['contrasts'].values()},
                         {'prespecified'})

    def test_the_build_is_deterministic(self):
        self.assertEqual(json.dumps(bc.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))

    def test_each_block_carries_its_own_interval_method(self):
        for b, people in ((self.diag, 70), (self.adapter, 70), (self.wear, 102)):
            m = b['interval_method']
            self.assertEqual((m['method'], m['draws'], m['seed'], m['level']),
                             ('paired person bootstrap, percentile interval', 2000, 20261015, 0.95))
            self.assertTrue(all(lv['people'] == people for lv in b['levels'].values()))
        self.assertNotIn('conditional_on', self.diag['interval_method'])
        self.assertIn('three fixed training seeds', self.adapter['interval_method']['conditional_on'])
        self.assertIn('105 source models', self.wear['interval_method']['conditional_on'])
        dvw = self.wear['cca_definition']['dry_vs_wet_cca']['interval_method']
        self.assertEqual((dvw['draws'], dvw['seed']), (10000, 20260920))     # the values beside card 7 keep theirs

    def test_units_are_fractions(self):
        for b in self.blocks.values():
            for lv in b['levels'].values():
                self.assertTrue(0 <= lv['interval'][0] <= lv['estimate'] <= lv['interval'][1] <= 1)
            for c in b['contrasts'].values():
                self.assertTrue(-1 <= c['interval'][0] <= c['estimate'] <= c['interval'][1] <= 1)

    def test_the_endpoints_are_route_3s_u8_and_seen_ba(self):
        r3 = self.docs['route3']['results']['questions-in-language']['descriptive']['P-ssvep-L0']['levels']
        for b in (self.diag, self.adapter):
            self.assertEqual(set(b['design']['endpoints']), {U8, SBA})
            self.assertEqual(b['design']['endpoints'][U8], {'candidate_count': 8, 'chance': 0.125})
            self.assertEqual(b['design']['endpoints'][SBA], {'candidate_count': 32, 'chance': 0.03125})
            for e in (U8, SBA):
                self.assertEqual(b['levels'][f'CCA-RAW/{e}']['estimate'], r3[f'CCA {e}']['estimate'])
                self.assertEqual(b['design']['endpoints'][e]['chance'], r3[f'CCA {e}']['chance'])
        self.assertEqual(self.diag['export_codes']['CCA-RAW/u8'], ['#/summary/arms/CCA-RAW/held8_accuracy'])

    # ------------------------------------------------------------------ card 5
    def test_diagnostics_figures_at_the_site_format(self):
        want = {  # release review accepted findings; plan section 2.1 card 5; the handoff reading
            'CCA-RAW': (('80.90', '76.80', '85.13'), ('65.46', '59.94', '71.40')),
            'CCA-HANN-C': (('72.96', '68.36', '77.86'), ('55.48', '50.01', '61.63')),
            'CCA-HANN-U': (('72.96', '68.36', '77.86'), ('55.48', '50.01', '61.63')),
            'SUBSPACE-CROP': (('73.20', '68.62', '78.13'), ('55.67', '50.20', '61.78')),
            'CHANNEL-JOINT': (('55.21', '49.99', '60.90'), ('35.74', '30.77', '41.13')),
            'CHANNEL-HARMONIC': (('55.21', '49.99', '60.90'), ('35.74', '30.77', '41.13')),
            'SHARED-RIDGE': (('57.45', '53.20', '62.14'), ('34.92', '30.83', '39.20')),
        }
        self.assertEqual(list(self.diag['levels']), [f'{c}/{e}' for c in want for e in (U8, SBA)])
        for code, (u8, sba) in want.items():
            self.assertEqual((lrow(self.diag['levels'][f'{code}/u8']), lrow(self.diag['levels'][f'{code}/seen_ba'])),
                             (u8, sba), code)
        want_c = {
            'CCA-HANN-C minus CCA-RAW': (('−7.95', '−9.07', '−6.78'), ('−9.98', '−11.10', '−8.84')),
            'CCA-HANN-U minus CCA-HANN-C': (('0.00', '0.00', '0.00'), ('0.00', '0.00', '0.00')),
            'SUBSPACE-CROP minus CCA-HANN-U': (('+0.24', '−0.12', '+0.64'), ('+0.19', '−0.22', '+0.64')),
            'SUBSPACE-CROP minus CHANNEL-JOINT': (('+17.98', '+14.94', '+21.28'), ('+19.94', '+17.06', '+23.18')),
            'CHANNEL-HARMONIC minus CHANNEL-JOINT': (('0.00', '0.00', '0.00'), ('0.00', '0.00', '0.00')),
            'SHARED-RIDGE minus CHANNEL-HARMONIC': (('+2.23', '+0.13', '+4.37'), ('−0.82', '−2.86', '+1.18')),
            'SHARED-RIDGE minus CCA-RAW': (('−23.46', '−26.64', '−20.45'), ('−30.54', '−34.76', '−26.67')),
        }
        for key, (u8, sba) in want_c.items():
            self.assertEqual((crow(self.diag['contrasts'][f'{key}/u8']), crow(self.diag['contrasts'][f'{key}/seen_ba'])),
                             (u8, sba), key)

    def test_the_crop_minus_hann_lower_bound_prints_minus_0_12(self):
        """The plan's card 5 and its 'exact figures' line say -0.13; the field renders -0.12, as the review says."""
        c = self.diag['contrasts']['SUBSPACE-CROP minus CCA-HANN-U/u8']
        self.assertEqual(c['interval'][0], -0.0012499999999999892)
        self.assertEqual(pp2(c['interval'][0]), '−0.12')
        self.assertTrue(c['flags']['interval_includes_zero'])
        self.assertIn('CI[-0.12,+0.64]', self.docs['diag_review']['accepted_findings'][3])

    def test_diagnostics_flags_design_and_seeds(self):
        bundled = self.diag['contrasts']['SUBSPACE-CROP minus CHANNEL-JOINT/u8']
        self.assertEqual(bundled['flags']['bundles'],
                         ['cross-channel mixing', 'fitting the reference coefficients', 'aggregation'])
        for key in ('CCA-HANN-U minus CCA-HANN-C', 'CHANNEL-HARMONIC minus CHANNEL-JOINT'):
            for e in (U8, SBA):
                self.assertIs(self.diag['contrasts'][f'{key}/{e}']['flags']['identical_results'], True)
        self.assertEqual(sum('identical_results' in c['flags'] for c in self.diag['contrasts'].values()), 4)
        self.assertEqual({r['variant'] for r in self.diag['design']['scorers'] if 'variant' in r},
                         {'centred', 'uncentred', 'joint reference span', 'per-harmonic spans'})
        d = self.diag['design']
        self.assertEqual((d['dataset']['people'], d['dataset']['windows'], d['dataset']['person_folds'],
                          d['dataset']['frequency_rotations'], d['training_free_scorers'], d['ridge_fits']),
                         (70, 11200, 7, 5, 6, 35))
        for lid, lv in self.diag['levels'].items():
            self.assertEqual(lv['seeds'], 'deterministic fit' if lid.startswith('SHARED-RIDGE') else 'no training', lid)
            self.assertEqual(lv['origin'], 'new')

    # ------------------------------------------------------------------ card 6
    def test_adapter_figures_match_the_binding_review_tables(self):
        want = {  # R1 section 2.4
            'ENERGY-FS': (('63.05', '58.97', '67.50'), ('43.34', '39.09', '47.83')),
            'ADAPT-FS': (('80.56', '76.98', '84.13'), ('64.06', '59.56', '68.85')),
            'CROP-RESIDUAL': (('79.24', '75.24', '83.37'), ('63.35', '58.39', '68.72')),
            'RAW-RESIDUAL': (('86.15', '82.84', '89.35'), ('73.19', '68.48', '77.99')),
            'CCA-CROP': (('73.20', '68.62', '78.13'), ('55.67', '50.20', '61.78')),
            'CCA-RAW': (('80.90', '76.80', '85.13'), ('65.46', '59.94', '71.40')),
        }
        for code, (u8, sba) in want.items():
            self.assertEqual((lrow(self.adapter['levels'][f'{code}/u8']), lrow(self.adapter['levels'][f'{code}/seen_ba'])),
                             (u8, sba), code)
        want_c = {
            'ADAPT-FS minus ENERGY-FS': (('+17.51', '+15.46', '+19.70'), ('+20.72', '+18.54', '+23.01')),
            'ADAPT-FS minus CCA-CROP': (('+7.36', '+5.33', '+9.32'), ('+8.38', '+5.91', '+10.82')),
            'CROP-RESIDUAL minus ADAPT-FS': (('−1.32', '−2.46', '−0.23'), ('−0.71', '−1.95', '+0.54')),
            'CROP-RESIDUAL minus CCA-CROP': (('+6.04', '+4.90', '+7.17'), ('+7.67', '+6.26', '+9.13')),
            'RAW-RESIDUAL minus CCA-RAW': (('+5.24', '+3.91', '+6.62'), ('+7.73', '+6.10', '+9.46')),
            'RAW-RESIDUAL minus CROP-RESIDUAL': (('+6.91', '+5.60', '+8.16'), ('+9.84', '+8.60', '+11.04')),
        }
        self.assertEqual(list(self.adapter['contrasts']), [f'{k}/{e}' for k in want_c for e in (U8, SBA)])
        for key, (u8, sba) in want_c.items():
            self.assertEqual((crow(self.adapter['contrasts'][f'{key}/u8']),
                              crow(self.adapter['contrasts'][f'{key}/seen_ba'])), (u8, sba), key)
        trained = ('ENERGY-FS', 'ADAPT-FS', 'CROP-RESIDUAL', 'RAW-RESIDUAL')
        for lid, lv in self.adapter['levels'].items():
            self.assertEqual(lv['seeds'], 3 if lid.split('/')[0] in trained else 'no training', lid)
        self.assertEqual({a['code']: a.get('parameters') for a in self.adapter['design']['arms']},
                         {'ENERGY-FS': 215681, 'ADAPT-FS': 215681, 'CROP-RESIDUAL': 215682, 'RAW-RESIDUAL': 215682,
                          'CCA-CROP': None, 'CCA-RAW': None})

    def test_the_gain_prints_from_its_own_field(self):
        """86.15 - 80.90 and 7.39 - 2.14 both read 5.25; the paired gain is +5.24 (R1 required finding 1)."""
        gain = self.adapter['contrasts']['RAW-RESIDUAL minus CCA-RAW/u8']['estimate']
        raw, cca = (self.adapter['levels'][f'{c}/u8']['estimate'] for c in ('RAW-RESIDUAL', 'CCA-RAW'))
        self.assertEqual(pp2(gain), '+5.24')
        self.assertEqual(f'{float(pct2(raw)) - float(pct2(cca)):.2f}', '5.25')
        t = self.adapter['transitions'][U8]
        self.assertEqual(f'{float(pct2(t["wrong_to_right"])) - float(pct2(t["right_to_wrong"])):.2f}', '5.25')
        self.assertEqual(gain, self.docs['adapter_export']['contrasts'][4]['metrics']['held8_accuracy']['mean'])

    def test_transitions_are_shares_of_all_decisions(self):
        t = self.adapter['transitions']
        self.assertEqual((t['arm'], t['against'], t['unit']), ('RAW-RESIDUAL', 'CCA-RAW',
                                                               'share of all decisions on the task'))
        self.assertEqual((t[U8]['denominator'], t[SBA]['denominator']), ('all held-out decisions', 'all seen decisions'))
        want = {U8: ('7.39', '2.14', '2.59', '78.76', '9.12', '12.12'),
                SBA: ('10.66', '2.93', '7.63', '62.53', '16.25', '21.22')}
        for e, row in want.items():
            self.assertEqual(tuple(pct2(t[e][k]) for k in ('wrong_to_right', 'right_to_wrong', 'wrong_to_different_wrong',
                                                         'unchanged_right', 'unchanged_wrong', 'changed')), row)
            self.assertAlmostEqual(sum(t[e][k] for k in bc.OUTCOMES), 1.0, places=12)
            gain = self.adapter['contrasts'][f'RAW-RESIDUAL minus CCA-RAW/{e}']['estimate']
            self.assertAlmostEqual(t[e]['wrong_to_right'] - t[e]['right_to_wrong'], gain, places=12)
            self.assertAlmostEqual(t[e]['unchanged_right'] + t[e]['right_to_wrong'],
                                   self.adapter['levels'][f'CCA-RAW/{e}']['estimate'], places=12)

    def test_the_protected_margin_is_the_export_value(self):
        p = self.adapter['protection']
        rd = self.docs['adapter_export']['residual_diagnostics']['RAW-RESIDUAL']['held8_accuracy']
        self.assertEqual(p['protected_margin'], rd['protected_margin'])
        self.assertEqual(p['protected_margin'], 0.200001)
        self.assertEqual(js_fixed(p['protected_margin'], 1), '0.2')
        self.assertEqual((p['protected_flips'], p['protected_instances']), (0, {U8: 11403, SBA: 6012}))
        self.assertEqual(p['instances_unit'], 'prediction instances across 3 seeds and 5 rotations')

    def test_adapter_numbers_come_from_its_export_only(self):
        self.assertEqual(self.adapter['source_sha256'], ADAPTER_EXPORT)
        ex = self.docs['adapter_export']
        export_values = set(floats(ex))
        for v in floats({k: self.adapter[k] for k in ('levels', 'contrasts', 'transitions', 'protection')}):
            self.assertIn(v, export_values, f'{v!r} is not a value of the adapter export')
        for lid, lv in self.adapter['levels'].items():
            here = bc.resolve(ex, self.adapter['export_codes'][lid][0][1:])
            self.assertEqual((lv['estimate'], lv['interval']), (here['mean'], here['ci95']), lid)
        for cid, c in self.adapter['contrasts'].items():
            here = bc.resolve(ex, self.adapter['export_codes'][cid][0][1:])
            self.assertEqual((c['estimate'], c['interval']), (here['mean'], here['ci95']), cid)

    def test_the_unplanned_pair_is_undefined_and_has_no_interval(self):
        self.assertFalse(any({c['left'].split('/')[0], c['right'].split('/')[0]} == {'ADAPT-FS', 'CCA-RAW'}
                             for c in self.adapter['contrasts'].values()))
        self.assertEqual(self.adapter['undefined'], [{'contrast': 'ADAPT-FS minus CCA-RAW',
                                                      'reason': 'not_a_planned_contrast'}])

    def test_the_canonical_correlations_are_attributed_to_the_cropped_match(self):
        f = self.adapter['contrasts']['ADAPT-FS minus ENERGY-FS/u8']['flags']
        self.assertEqual(f['bundles'], ['several matching operations'])
        self.assertEqual(f['added_input'], {'canonical_correlations': 6, 'computed_on': bc.CROPPED_MATCH})
        self.assertNotEqual(f['added_input']['computed_on'], self.adapter['display_names']['CCA-RAW'])

    # ------------------------------------------------------------------ one set of scores, one name
    def test_one_name_for_one_set_of_scores(self):
        self.assertEqual(self.diag['display_names']['SUBSPACE-CROP'], self.adapter['display_names']['CCA-CROP'])
        self.assertEqual(self.adapter['display_names']['CCA-CROP'], 'cropped-spectrum match (no training)')
        for here, there in (('CCA-CROP', 'SUBSPACE-CROP'), ('CCA-RAW', 'CCA-RAW')):
            for e in (U8, SBA):
                a, d = self.adapter['levels'][f'{here}/{e}'], self.diag['levels'][f'{there}/{e}']
                self.assertEqual((a['estimate'], a['interval']), (d['estimate'], d['interval']))
                self.assertEqual(a['origin'], 'reused_cca_diagnostics')
                self.assertIn(f'cca_diagnostics#/summary/arms/{there}/{bc.ENDPOINTS[e]}',
                              self.adapter['export_codes'][f'{here}/{e}'])
        names = [n for b in self.blocks.values() for n in b['display_names'].values()]
        self.assertEqual(names.count('cropped-spectrum match (no training)'), 2)

    def test_the_wearable_cropped_check_is_labelled_separately(self):
        self.assertEqual(self.wear['display_names']['CCA-CROP'], 'cropped-spectrum check (Wearable-102)')
        self.assertEqual(self.wear['display_names']['CCA-RAW'], 'matched CCA')
        crop = [m for m in self.wear['design']['methods'] if m['code'] == 'CCA-CROP'][0]
        self.assertEqual(crop['role'], 'diagnostic')
        self.assertEqual((pct2(self.wear['levels']['CCA-CROP/dry']['estimate']),
                          pct2(self.wear['levels']['CCA-CROP/wet']['estimate'])), ('57.78', '73.01'))
        self.assertTrue(all(lv['origin'] == 'new' for lv in self.wear['levels'].values()))
        self.assertFalse(any('cca_diagnostics#' in x for codes in self.wear['export_codes'].values() for x in codes))
        self.assertFalse(any('CCA-CROP' in c['left'] + c['right'] for c in self.wear['contrasts'].values()))

    def test_the_name_key_rows_of_this_package(self):
        self.assertEqual(dict(bc.NAME_KEY), {
            'CCA (no training)': 'CCA-RAW',
            'Hann-tapered CCA': 'CCA-HANN-C/U',
            'cropped-spectrum match (no training)':
                'SUBSPACE-CROP in the diagnostics export, CCA-CROP in the adapter export: one set of scores',
            'channel-energy average': 'CHANNEL-JOINT/HARMONIC',
            'shared ridge scorer': 'SHARED-RIDGE',
            'energy head': 'ENERGY-FS',
            'adapted head': 'ADAPT-FS',
            'CCA with learned correction': 'RAW-RESIDUAL',
            'cropped match with learned correction': 'CROP-RESIDUAL',
            'cropped-spectrum check (Wearable-102)': 'CCA-CROP in the Wearable export'})
        sites = {n for b in self.blocks.values() for n in b['display_names'].values()} - {'matched CCA'}
        self.assertLessEqual(sites, set(dict(bc.NAME_KEY)))

    # ------------------------------------------------------------------ card 7
    def test_wearable_figures(self):
        want = {'RAW-RESIDUAL': (('65.45', '60.82', '70.08'), ('81.04', '77.14', '84.49'), ('73.24', '69.40', '76.88')),
                'CCA-RAW': (('65.38', '60.73', '70.06'), ('81.65', '77.60', '85.14'), ('73.51', '69.71', '77.22')),
                'CCA-CROP': (('57.78', '52.79', '62.89'), ('73.01', '68.46', '77.18'), ('65.40', '60.94', '69.69'))}
        for code, rows in want.items():
            self.assertEqual(tuple(lrow(self.wear['levels'][f'{code}/{s}']) for s in bc.STRATA), rows, code)
        self.assertEqual([crow(c) for c in self.wear['contrasts'].values()],
                         [('+0.07', '−0.71', '+0.91'), ('−0.61', '−1.48', '+0.23'), ('−0.27', '−0.95', '+0.40')])
        self.assertTrue(all(c['flags']['interval_includes_zero'] for c in self.wear['contrasts'].values()))
        d = self.wear['design']
        self.assertEqual((d['dataset']['people'], d['dataset']['targets'], d['dataset']['frequency_range_hz'],
                          d['dataset']['windows_per_sensor'], d['dataset']['window_s'], d['source_models']['models'],
                          d['source_models']['parameters_per_model']),
                         (102, 12, [9.25, 14.75], 12240, [0.14, 2.14], 105, 215682))
        self.assertEqual(js_fixed(d['endpoints']['dry']['chance'] * 100), '8.33')
        self.assertEqual({s: d['endpoints'][s]['role'] for s in bc.STRATA},
                         {'dry': 'primary', 'wet': 'primary', 'all': 'secondary'})

    def test_the_a2_fact(self):
        a2, note = self.wear['cca_definition'], self.docs['wear_cca_definition']
        self.assertEqual((a2['matched_cca']['harmonics'], a2['dry_vs_wet_cca']['harmonics']), (3, 4))
        self.assertEqual((a2['differs_in'], a2['same_windows']), ('harmonic count', True))
        self.assertEqual(a2['fact'], note['card7']['a2_fact_for_plan_template'])
        dvw = a2['dry_vs_wet_cca']
        self.assertEqual(note['card7']['figures_pct2'],
                         [pct2(self.wear['levels'][f'CCA-RAW/{s}']['estimate']) for s in ('dry', 'wet')]
                         + [pct2(dvw[s]['estimate']) for s in ('dry', 'wet')])
        self.assertEqual(note['card7']['figures_pct2'], ['65.38', '81.65', '65.47', '81.56'])
        rows = self.docs['dry_vs_wet']['rows']
        for code, s in zip(a2['export_codes'][1:], ('dry', 'wet')):
            file, ptr = code.split('#')
            self.assertEqual(file, 'deployment-topics.json')
            self.assertEqual(bc.resolve({'rows': rows}, ptr), dvw[s]['estimate'])

    # ------------------------------------------------------------------ the boundary
    def test_no_private_or_refused_material(self):
        validate_public(self.blocks)
        text = json.dumps(self.blocks, ensure_ascii=False)
        for word in ('/Users', '/home', '/Volumes', '/mnt', 'trx', 'TRX', 'Gal4', 'BCI_Arena', 'twu', 'pending',
                     'private_root', '"job"', '"pid"', '2300265', 'indices_sha256', '64c11d0b', 'per_seed', 'privacy',
                     '"rows"', '5599', '11199', '12239', '24479', 'exported_at', 'Dipankar', '55%', 'audit_pending',
                     'release_review_pending', '"status"', 'protected_trials', '61d424e9', 'f4040010', '.py', '.md',
                     'huggingface.co', 'decision_route3', 'research/'):
            self.assertNotIn(word, text, word)
        self.assertNotIn(0.55, list(floats(self.blocks)))
        self.assertIsNone(re.search(r'(?<![./\w-])v\d+\b', text))

    def test_every_limitation_and_not_run_item_resolves_in_its_pinned_record(self):
        for name, b in self.blocks.items():
            self.assertEqual(b['limitations_keys'], list(bc.LIMITATION_SOURCES[name]))
            for key, (doc, ptr, phrase) in bc.LIMITATION_SOURCES[name].items():
                self.assertIn(phrase, bc.resolve(self.docs[doc], ptr), key)
                self.assertTrue(re.fullmatch(r'[a-z0-9_]+', key), key)
            self.assertEqual([x['item'] for x in b['not_run']], list(bc.NOT_RUN_SOURCES[name]))
            for item, (doc, ptr, phrase) in bc.NOT_RUN_SOURCES[name].items():
                self.assertIn(phrase, bc.resolve(self.docs[doc], ptr), item)
            for cid, keys in b['contrast_limitations'].items():
                self.assertIn(cid, b['contrasts'])
                self.assertLessEqual(set(keys), set(b['limitations_keys']))
        self.assertEqual([x['item'] for x in self.adapter['not_run']][:2], ['filter-bank CCA', 'supervised spatial templates'])

    def test_declared_edits_and_handoff_context_are_kept_for_the_manifest(self):
        self.assertEqual(set(bc.DECLARED_EDITS), set(bc.STUDIES))
        self.assertTrue(all(bc.DECLARED_EDITS[s] for s in bc.STUDIES))
        self.assertIn('pid', self.docs['diag_export']['job'])            # in the source ...
        self.assertNotIn('job', self.diag)                               # ... and not in the block
        self.assertEqual(self.docs['adapter_release_status']['handoff_sha256'],
                         bc.HANDOFF_CONTEXT['cca_adapter']['bound_sha256'])
        for name, b in self.blocks.items():
            self.assertNotIn(bc.HANDOFF_CONTEXT[name]['bound_sha256'], json.dumps(b))


@unittest.skipUnless(bc.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class CcaBlocksRefuse(unittest.TestCase):
    """Each check fires on its own: the pinned records are loaded once, edited in memory, and the blocks rebuilt."""

    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = bc.load()

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)

    def build(self):
        diag = bc.diagnostics_block(self.d, self.h)
        adapter = bc.adapter_block(self.d, self.h, diag)
        return diag, adapter, bc.wearable_block(self.d, self.h, adapter)

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def both(self, edit):
        """Edit the adapter export and the numerical review's copy of it alike."""
        edit(self.d['adapter_export'])
        edit(self.d['adapter_numerical_review']['aggregate_findings'])

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(bc.PINS)
        pins['adapter_export']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            bc.build_blocks(pins)

    def test_pins_of_another_shape_are_refused(self):
        pins = copy.deepcopy(bc.PINS)
        del pins['wear_cca_definition']
        with self.assertRaisesRegex(ValueError, 'pins: expected'):
            bc.build_blocks(pins)

    def test_an_export_its_reviews_did_not_bind_is_refused(self):
        self.h['adapter_export'] = 'f' * 64
        self.refused('binds')

    def test_the_transfer_must_bind_the_adapter_release_records(self):
        self.d['wear_freeze']['parent_provenance']['protocol.json'] = 'b' * 64
        self.refused('transfer parent protocol')

    def test_the_export_must_equal_the_numerical_review(self):
        self.d['adapter_export']['arms']['RAW-RESIDUAL']['held8_accuracy']['mean'] += 1e-9
        self.refused('differs from the numerical review')

    def test_the_cropped_match_must_carry_the_same_scores_in_both_exports(self):
        self.both(lambda x: x['arms']['CCA-CROP']['held8_accuracy'].__setitem__(
            'mean', x['arms']['CCA-CROP']['held8_accuracy']['mean'] + 1e-9))
        self.refused('differs from diagnostics SUBSPACE-CROP')

    def test_the_endpoint_rename_must_hold_on_route_3(self):
        lv = self.d['route3']['results']['questions-in-language']['descriptive']['P-ssvep-L0']['levels']
        lv['CCA u8']['estimate'] += 1e-9
        self.refused("not route 3's CCA u8")

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.d['diag_export']['summary']['contrasts']['SHARED-RIDGE minus CCA-RAW']['held8_accuracy']['mean'] += 1e-6
        self.refused('not the difference of its levels')

    def test_an_interval_must_hold_its_point(self):
        self.d['diag_export']['summary']['arms']['CCA-RAW']['held8_accuracy']['ci95'] = [0.81, 0.85]
        self.refused('does not hold its point')

    def test_the_five_outcomes_must_cover_all_decisions(self):
        def edit(x):
            x['residual_diagnostics']['RAW-RESIDUAL']['held8_accuracy']['unchanged_correct'] += 0.01
        self.both(edit)
        self.refused('do not sum to one')

    def test_net_transitions_must_equal_the_paired_gain(self):
        def edit(x):
            t = x['residual_diagnostics']['RAW-RESIDUAL']['held8_accuracy']
            t['wrong_to_correct'] += 0.01
            t['changed_wrong_to_wrong'] -= 0.01
        self.both(edit)
        self.refused('is not the paired gain')

    def test_a_protected_flip_is_refused(self):
        def edit(x):
            x['residual_diagnostics']['RAW-RESIDUAL']['seen32_balanced_accuracy']['protected_flips'] = 1
        self.both(edit)
        self.refused('protected flip')

    def test_the_protected_margin_must_follow_the_protocol_bound(self):
        def edit(x):
            for arm in x['residual_diagnostics'].values():
                for t in arm.values():
                    t['protected_margin'] = 0.3
        self.both(edit)
        self.refused('not 4/20')

    def test_an_unplanned_adapter_contrast_is_refused(self):
        """Even a well-formed interval for the adapted head against CCA alone is refused: it was never planned."""
        arms = self.d['adapter_export']['arms']
        diff = {e: arms['ADAPT-FS'][e]['mean'] - arms['CCA-RAW'][e]['mean'] for e in bc.ENDPOINTS.values()}
        extra = {'left': 'ADAPT-FS', 'right': 'CCA-RAW', 'metrics': {
            e: {'mean': diff[e], 'ci95': [diff[e] - 0.01, diff[e] + 0.01]} for e in bc.ENDPOINTS.values()}}
        self.both(lambda x: x['contrasts'].append(copy.deepcopy(extra)))
        self.d['adapter_protocol']['metrics']['contrasts'].append(['ADAPT-FS', 'CCA-RAW'])
        self.refused('was not planned')

    def test_the_bootstrap_seed_is_the_reviewed_one(self):
        self.d['adapter_numerical_review']['checks']['independent_numerical_recomputation']['bootstrap_seed'] = 1
        self.refused('adapter: bootstrap seed')
        self.d = copy.deepcopy(self.docs)
        self.d['wear_export']['bootstrap']['seed'] = 20261007
        self.refused('wearable: bootstrap')

    def test_the_a2_note_must_carry_the_source_values(self):
        self.d['wear_cca_definition']['numbers'][2]['value'] = 0.655
        self.refused('A2 note figure')

    def test_the_a2_note_must_name_the_same_windows(self):
        self.d['wear_freeze']['input_sha256']['epochs250.npy'] = 'a' * 64
        self.refused('the windows differ')

    def test_the_wearable_cropped_check_cannot_take_the_beta_name(self):
        names = copy.deepcopy(bc.DISPLAY_NAMES)
        names['wearable_transfer']['CCA-CROP'] = bc.CROPPED_MATCH
        with mock.patch.object(bc, 'DISPLAY_NAMES', names):
            self.refused('shares a name')

    def test_a_limitation_its_record_does_not_state_is_refused(self):
        self.d['adapter_review']['required_boundaries'][6] = 'Protection holds.'
        self.refused('does not state')

    def test_the_scrub_refuses_what_must_not_be_published(self):
        for bad in ({'pid': 1}, {'job': {}}, {'rows': [0, 159]}, {'per_seed_values': []}, {'note': '/home/someone/x'},
                    {'note': 'run on trx50'}, {'x': [0, 159, 160, 5599]}, {'x': 0.55}, {'note': 'beat 55% held-out'},
                    {'note': 'release review pending'}, {'note': 'the v2 rule'}, {'note': 'the best decoder'},
                    {'status': 'ok'}, {'protected_trials': 3}, {'feature_rows': 6}, {'note': 'Dipankar asked'}):
            with self.assertRaises(ValueError, msg=repr(bad)):
                bc.scrub_check(bad)
        bc.scrub_check({'note': 'cropped-spectrum match (no training)', 'x': 0.5567410714285715, 'r': [0, 2]})


if __name__ == '__main__':
    unittest.main()
