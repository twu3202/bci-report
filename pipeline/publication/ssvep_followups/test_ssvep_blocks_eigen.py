"""Card 9, the coherence and eigenvalue block: what it must carry, and what it must refuse.

Expected values are written out twice: at full precision, copied from the pinned aggregate (SHA-256 9ee6cc3a...) and
asserted equal to the double; and as the handoff's tables and the plan's card 9 lead state them, rendered the way the
site renders them (JavaScript toFixed on the double: pct2 for levels; the handoff's contrasts at three decimals).
"""
import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public                                   # noqa: E402
from ssvep_followups import blocks_cca as bc                                  # noqa: E402
from ssvep_followups import blocks_eigen as be                                 # noqa: E402
from ssvep_followups import blocks_xspec as bx                                 # noqa: E402
from ssvep_followups.test_ssvep_blocks_cca import floats, js_fixed, lrow, pct2, pp2   # noqa: E402

U8, SBA = 'u8', 'seen_ba'
AGGREGATE = '9ee6cc3a9a46c76faeec00b3d7b57a5fb66993389f85d001a443507becc6717d'
AGGREGATE_PATH = 'research/decision_route3_coherence_eigen_20261020/evidence/Completed Aggregate Results.json'
PROJECT = PUBLICATION.parents[1]
LOWER = -2.2321428571386387e-06          # EIG-SPEC minus SPEC-HARM-SUM, held-out lower bound, as a fraction

LEVELS = {
    'COH-ABS': ((0.643482142857143, 0.6004419642857144, 0.6913482142857142),
                (0.4029017857142857, 0.3624324776785714, 0.4470345982142857)),
    'COH-SIGNED': ((0.6667857142857143, 0.6228549107142857, 0.7149151785714284),
                   (0.42526785714285714, 0.3824218750000001, 0.4717421875)),
    'EIG-SPEC': ((0.7491964285714285, 0.7053459821428573, 0.7943772321428569),
                 (0.5730580357142857, 0.5190976562500002, 0.6281746651785712)),
    'EIG-RAW': ((0.8297321428571428, 0.790888392857143, 0.8682165178571427),
                (0.7000223214285715, 0.6471852678571428, 0.7543141741071429)),
    'EIG-JOINT': ((0.8228571428571427, 0.7821383928571427, 0.8639352678571429),
                  (0.6925223214285713, 0.6379542410714285, 0.7497606026785713)),
    'JOINT-TOP': ((0.809017857142857, 0.7680334821428572, 0.8513415178571431),
                  (0.6545982142857143, 0.599368861607143, 0.7140184151785715)),
    'RAW-HARM-SUM': ((0.8290178571428571, 0.7890178571428572, 0.869296875),
                     (0.6952678571428572, 0.6402187500000002, 0.7507075892857143)),
    'SPEC-HARM-SUM': ((0.7439285714285715, 0.6995535714285714, 0.7906272321428571),
                      (0.5608258928571428, 0.5084118303571428, 0.6156713169642857)),
    'SHARED-RIDGE': ((0.5744642857142855, 0.5320424107142856, 0.6214308035714287),
                     (0.3491964285714285, 0.3083482142857143, 0.3919933035714284)),
    'CCA-RAW': ((0.809017857142857, 0.7680334821428572, 0.8513415178571431),
                (0.6545982142857143, 0.599368861607143, 0.7140184151785715)),
    'XS-RIDGE': ((0.680267857142857, 0.6339263392857143, 0.7305379464285714),
                 (0.4855803571428572, 0.43561662946428575, 0.5398962053571429)),
    'XS-RIDGE-W': ((0.7999107142857145, 0.7620491071428571, 0.8379486607142856),
                   (0.6210491071428572, 0.5727667410714284, 0.6700669642857143)),
    'XS-RIDGE-Q': ((0.6844642857142855, 0.6398080357142858, 0.7325892857142856),
                   (0.4789508928571428, 0.4300401785714286, 0.5335731026785714)),
}
CONTRASTS = (
    ('COH-ABS minus XS-RIDGE/u8', -0.0367857142857143, -0.049196428571428565, -0.024553571428571428),
    ('EIG-SPEC minus XS-RIDGE-W/u8', -0.05071428571428571, -0.06607366071428572, -0.035892857142857136),
    ('EIG-RAW minus CCA-RAW/u8', 0.020714285714285713, 0.010890624999999989, 0.031249999999999993),
    ('COH-SIGNED minus COH-ABS/u8', 0.02330357142857143, 0.016160714285714292, 0.03098437499999999),
    ('COH-SIGNED minus XS-RIDGE/u8', -0.01348214285714286, -0.02607142857142857, -0.0017857142857142941),
    ('EIG-RAW minus RAW-HARM-SUM/u8', 0.0007142857142857188, -0.004466517857142854, 0.006162946428571422),
    ('EIG-SPEC minus SPEC-HARM-SUM/u8', 0.005267857142857146, LOWER, 0.010714285714285721),
    ('EIG-JOINT minus JOINT-TOP/u8', 0.013839285714285712, 0.005622767857142853, 0.02178571428571428),
    ('COH-ABS minus SHARED-RIDGE/seen_ba', 0.053705357142857145, 0.04182924107142856, 0.06623046874999997),
    ('COH-SIGNED minus SHARED-RIDGE/seen_ba', 0.07607142857142858, 0.061426339285714296, 0.09163113839285715),
    ('EIG-SPEC minus SHARED-RIDGE/seen_ba', 0.22386160714285713, 0.19048828125, 0.2591969866071429),
    ('EIG-RAW minus SHARED-RIDGE/seen_ba', 0.35082589285714283, 0.31472433035714287, 0.38932142857142854),
    ('EIG-JOINT minus SHARED-RIDGE/seen_ba', 0.34332589285714293, 0.3061568080357143, 0.38245703125),
)
ROLES = ['primary'] * 3 + ['secondary'] * 10
# The handoff's "All outcomes" table, held eight then seen 32.
HANDOFF_LEVELS = {
    'COH-ABS': (('64.35', '60.04', '69.13'), ('40.29', '36.24', '44.70')),
    'COH-SIGNED': (('66.68', '62.29', '71.49'), ('42.53', '38.24', '47.17')),
    'EIG-SPEC': (('74.92', '70.53', '79.44'), ('57.31', '51.91', '62.82')),
    'EIG-RAW': (('82.97', '79.09', '86.82'), ('70.00', '64.72', '75.43')),
    'EIG-JOINT': (('82.29', '78.21', '86.39'), ('69.25', '63.80', '74.98')),
    'JOINT-TOP': (('80.90', '76.80', '85.13'), ('65.46', '59.94', '71.40')),
    'RAW-HARM-SUM': (('82.90', '78.90', '86.93'), ('69.53', '64.02', '75.07')),
    'SPEC-HARM-SUM': (('74.39', '69.96', '79.06'), ('56.08', '50.84', '61.57')),
    'SHARED-RIDGE': (('57.45', '53.20', '62.14'), ('34.92', '30.83', '39.20')),
    'CCA-RAW': (('80.90', '76.80', '85.13'), ('65.46', '59.94', '71.40')),
    'XS-RIDGE': (('68.03', '63.39', '73.05'), ('48.56', '43.56', '53.99')),
    'XS-RIDGE-W': (('79.99', '76.20', '83.79'), ('62.10', '57.28', '67.01')),
    'XS-RIDGE-Q': (('68.45', '63.98', '73.26'), ('47.90', '43.00', '53.36')),
}
# The handoff's "All thirteen frozen paired contrasts" table, percentage points at three decimals; the near-zero
# lower bound at the extra precision the handoff prints it with.
HANDOFF_CONTRASTS = {
    'COH-ABS minus XS-RIDGE/u8': ('−3.679', '−4.920', '−2.455'),
    'EIG-SPEC minus XS-RIDGE-W/u8': ('−5.071', '−6.607', '−3.589'),
    'EIG-RAW minus CCA-RAW/u8': ('+2.071', '+1.089', '+3.125'),
    'COH-SIGNED minus COH-ABS/u8': ('+2.330', '+1.616', '+3.098'),
    'COH-SIGNED minus XS-RIDGE/u8': ('−1.348', '−2.607', '−0.179'),
    'EIG-RAW minus RAW-HARM-SUM/u8': ('+0.071', '−0.447', '+0.616'),
    'EIG-SPEC minus SPEC-HARM-SUM/u8': ('+0.527', None, '+1.071'),
    'EIG-JOINT minus JOINT-TOP/u8': ('+1.384', '+0.562', '+2.179'),
    'COH-ABS minus SHARED-RIDGE/seen_ba': ('+5.371', '+4.183', '+6.623'),
    'COH-SIGNED minus SHARED-RIDGE/seen_ba': ('+7.607', '+6.143', '+9.163'),
    'EIG-SPEC minus SHARED-RIDGE/seen_ba': ('+22.386', '+19.049', '+25.920'),
    'EIG-RAW minus SHARED-RIDGE/seen_ba': ('+35.083', '+31.472', '+38.932'),
    'EIG-JOINT minus SHARED-RIDGE/seen_ba': ('+34.333', '+30.616', '+38.246'),
}


def pp(raw, digits):
    return ('' if raw == 0 else '+' if raw > 0 else '−') + js_fixed(abs(raw * 100), digits)


def pinned_json(path, digest):
    raw = (PROJECT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, path
    return json.loads(raw)


@unittest.skipUnless(be.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class EigenBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = be.build_blocks()
        cls.b = cls.blocks['coherence_eigen']
        cls.xspec = bx.build_blocks()['xspec']
        cls.docs, cls.digests = be.load()
        cls.aggregate = pinned_json(AGGREGATE_PATH, AGGREGATE)
        cls.released = pinned_json(bx.RELEASED_PATH, bx.PINS['released']['sha256'])

    # ------------------------------------------------------------------ shape
    def test_one_block_with_the_released_fields(self):
        self.assertEqual(tuple(self.blocks), be.STUDIES)
        b = self.b
        for k in bx.BLOCK_FIELDS + ('design', 'contrast_limitations', 'reused', 'answers_not_run'):
            self.assertIn(k, b)
        self.assertEqual(set(b['export_codes']), set(b['levels']) | set(b['contrasts']))
        for lid, lv in b['levels'].items():
            self.assertEqual(set(lv), {'estimate', 'interval', 'unit', 'people', 'seeds', 'origin'}, lid)
            self.assertEqual((lv['unit'], lv['people']), ('proportion', 70))
        for cid, c in b['contrasts'].items():
            self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'unit', 'people', 'seeds',
                                      'flags'}, cid)
            self.assertEqual((c['unit'], c['people'], c['seeds']), ('difference of proportions', 70, 'deterministic fit'))
        for codes in b['export_codes'].values():
            self.assertTrue(codes and all(re.fullmatch(r'(?:[\w-]+(?:\.json)?)?#(?:/[^/]+)+', x) for x in codes), codes)
        self.assertEqual((len(b['levels']), len(b['contrasts'])), (26, 13))         # 13 arms x 2 endpoints
        self.assertEqual([c['role'] for c in b['contrasts'].values()], ROLES)
        self.assertEqual(b['source_sha256'], AGGREGATE)

    def test_the_build_is_deterministic(self):
        self.assertEqual(json.dumps(be.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))

    # ------------------------------------------------------------------ every value at full precision
    def test_every_level_is_the_aggregate_double(self):
        self.assertEqual(list(self.b['levels']), [f'{c}/{e}' for c in LEVELS for e in (U8, SBA)])
        for code, rows in LEVELS.items():
            for e, src, (est, lo, hi) in zip((U8, SBA), ('held8', 'seen32'), rows):
                lv = self.b['levels'][f'{code}/{e}']
                self.assertEqual((lv['estimate'], lv['interval']), (est, [lo, hi]), f'{code}/{e}')
                here = self.aggregate['arms'][code][src]
                self.assertEqual((lv['estimate'], lv['interval']), (here['mean'], here['ci95']), f'{code}/{e}')
                self.assertEqual(self.b['export_codes'][f'{code}/{e}'][0], f'#/arms/{code}/{src}')

    def test_every_contrast_is_the_aggregate_double(self):
        self.assertEqual([c[0] for c in CONTRASTS], list(self.b['contrasts']))
        for i, (cid, est, lo, hi) in enumerate(CONTRASTS):
            c = self.b['contrasts'][cid]
            self.assertEqual((c['estimate'], c['interval']), (est, [lo, hi]), cid)
            src = self.aggregate['contrasts'][i]
            self.assertEqual((c['estimate'], c['interval']), (src['mean'], src['ci95']), cid)
            self.assertEqual(self.b['export_codes'][cid], [f'#/contrasts/{i}'])
            self.assertAlmostEqual(c['estimate'], self.b['levels'][c['left']]['estimate']
                                   - self.b['levels'][c['right']]['estimate'], places=12)

    def test_no_value_outside_the_sources(self):
        source = set(floats(self.aggregate)) | set(floats(self.released))
        for v in floats(self.b):
            self.assertTrue(v in source or v == bx.TOL, v)

    # ------------------------------------------------------------------ the near-zero lower bound
    def test_the_spectral_pooling_lower_bound_is_kept_at_full_precision(self):
        c = self.b['contrasts']['EIG-SPEC minus SPEC-HARM-SUM/u8']
        self.assertEqual(c['interval'][0], LOWER)
        self.assertLess(c['interval'][0], 0.0)
        self.assertEqual(pp(c['interval'][0], 5), '−0.00022')
        self.assertEqual(pp2(c['interval'][0]), '−0.00')                # why the site may not print it at two decimals
        self.assertEqual(c['flags']['bound_below_two_decimals'], ['lower'])
        self.assertTrue(c['flags']['interval_includes_zero'])
        self.assertIs(c['flags']['above_zero'], False)
        self.assertEqual(self.b['contrast_limitations']['EIG-SPEC minus SPEC-HARM-SUM/u8'], ['lower_bound_not_rounded'])
        self.assertEqual([k for k, x in self.b['contrasts'].items() if 'bound_below_two_decimals' in x['flags']],
                         ['EIG-SPEC minus SPEC-HARM-SUM/u8'])
        self.assertIn('[-0.0002232, 1.0714286]', self.docs['eigen_numerical_review'])

    # ------------------------------------------------------------------ the handoff's tables and the plan's lead
    def test_the_handoff_tables_at_the_site_format(self):
        for code, (u8, sba) in HANDOFF_LEVELS.items():
            self.assertEqual((lrow(self.b['levels'][f'{code}/u8']), lrow(self.b['levels'][f'{code}/seen_ba'])),
                             (u8, sba), code)
        for cid, (est, lo, hi) in HANDOFF_CONTRASTS.items():
            c = self.b['contrasts'][cid]
            self.assertEqual((pp(c['estimate'], 3), pp(c['interval'][1], 3)), (est, hi), cid)
            if lo is not None:
                self.assertEqual(pp(c['interval'][0], 3), lo, cid)
        self.assertIn('| 0.527 [-0.00022, 1.071] |', self.docs['eigen_handoff'])

    def test_the_card_9_lead(self):
        """Plan section 2.1, card 9."""
        lv, c = self.b['levels'], self.b['contrasts']
        self.assertEqual(lrow(lv['EIG-RAW/u8']), ('82.97', '79.09', '86.82'))
        self.assertEqual(pct2(lv['CCA-RAW/u8']['estimate']), '80.90')
        primary = c['EIG-RAW minus CCA-RAW/u8']
        self.assertEqual(tuple(pp(x, 3) for x in [primary['estimate']] + primary['interval']),
                         ('+2.071', '+1.089', '+3.125'))
        self.assertIs(primary['flags']['strict_5pp_equivalence'], True)
        self.assertIs(primary['flags']['strict_5pp_noninferiority'], True)
        self.assertEqual(lrow(lv['RAW-HARM-SUM/u8']), ('82.90', '78.90', '86.93'))
        learned = c['EIG-RAW minus RAW-HARM-SUM/u8']
        self.assertEqual(tuple(pp(x, 3) for x in [learned['estimate']] + learned['interval']),
                         ('+0.071', '−0.447', '+0.616'))
        self.assertTrue(learned['flags']['interval_includes_zero'])
        self.assertEqual(pct2(lv['COH-ABS/u8']['estimate']), '64.35')
        self.assertEqual(pct2(lv['XS-RIDGE/u8']['estimate']), '68.03')
        coh = c['COH-ABS minus XS-RIDGE/u8']
        self.assertEqual(tuple(pp(x, 3) for x in [coh['estimate']] + coh['interval']), ('−3.679', '−4.920', '−2.455'))
        self.assertEqual(pct2(lv['EIG-SPEC/u8']['estimate']), '74.92')
        self.assertEqual(pct2(lv['XS-RIDGE-W/u8']['estimate']), '79.99')
        spec = c['EIG-SPEC minus XS-RIDGE-W/u8']
        self.assertEqual(tuple(pp(x, 3) for x in [spec['estimate']] + spec['interval']), ('−5.071', '−6.607', '−3.589'))
        pooling = c['EIG-SPEC minus SPEC-HARM-SUM/u8']
        self.assertEqual((pp(pooling['estimate'], 3), pp(pooling['interval'][1], 3)), ('+0.527', '+1.071'))

    # ------------------------------------------------------------------ roles and flags
    def test_roles_follow_the_protocol(self):
        st = self.docs['eigen_protocol']['statistics']
        self.assertEqual([k for k, c in self.b['contrasts'].items() if c['role'] == 'primary'],
                         [f'{a} minus {b}/u8' for a, b in st['primary_held8']])
        self.assertEqual([k for k, c in self.b['contrasts'].items() if c['role'] == 'primary'],
                         ['COH-ABS minus XS-RIDGE/u8', 'EIG-SPEC minus XS-RIDGE-W/u8', 'EIG-RAW minus CCA-RAW/u8'])

    def test_flags_are_the_aggregates_and_the_5pp_rules_sit_on_the_primary_only(self):
        for i, (cid, c) in enumerate(self.b['contrasts'].items()):
            src = self.aggregate['contrasts'][i]
            self.assertIs(c['flags']['above_zero'], src['above_zero'], cid)
            self.assertIs(c['flags']['below_zero'], src['below_zero'], cid)
            lo, hi = c['interval']
            self.assertIs(c['flags']['interval_includes_zero'], lo <= 0 <= hi, cid)
        with5 = [k for k, c in self.b['contrasts'].items() if 'strict_5pp_equivalence' in c['flags']]
        self.assertEqual(with5, ['EIG-RAW minus CCA-RAW/u8'])
        claim = self.aggregate['prespecified_eigenvalue_claim']
        self.assertEqual(claim['paired_difference'], self.aggregate['contrasts'][2])
        self.assertEqual([k for k, c in self.b['contrasts'].items() if c['flags']['interval_includes_zero']],
                         ['EIG-RAW minus RAW-HARM-SUM/u8', 'EIG-SPEC minus SPEC-HARM-SUM/u8'])

    # ------------------------------------------------------------------ reused comparators: cards 5 and 8
    def test_the_card_5_comparators_are_its_released_levels(self):
        diag = self.released['studies']['cca_diagnostics']
        for code in ('SHARED-RIDGE', 'CCA-RAW'):
            self.assertEqual(self.b['reused'][code],
                             {'card': 5, 'study': 'cca_diagnostics', 'anchor': 'cca-mechanism', 'code': code})
            self.assertEqual(self.b['display_names'][code], diag['display_names'][code])
            for e in (U8, SBA):
                lv, twin = self.b['levels'][f'{code}/{e}'], diag['levels'][f'{code}/{e}']
                self.assertLessEqual(abs(lv['estimate'] - twin['estimate']), 1e-12)
                self.assertEqual({k: lv[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')},
                                 {k: twin[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')})
                self.assertEqual(lv['origin'], 'reused_cca_diagnostics')
                self.assertEqual(self.b['export_codes'][f'{code}/{e}'][1:],
                                 ['cca_diagnostics' + diag['export_codes'][f'{code}/{e}'][0],
                                  f'new-ssvep-frequencies-update.json#/studies/cca_diagnostics/levels/{code}~1{e}'])

    def test_the_card_8_comparators_are_card_8s_block(self):
        for code in ('XS-RIDGE', 'XS-RIDGE-W', 'XS-RIDGE-Q'):
            self.assertEqual(self.b['reused'][code],
                             {'card': 8, 'study': 'xspec', 'anchor': 'cross-spectral', 'code': code})
            self.assertEqual(self.b['display_names'][code], self.xspec['display_names'][code])
            for e in (U8, SBA):
                lv, twin = self.b['levels'][f'{code}/{e}'], self.xspec['levels'][f'{code}/{e}']
                self.assertLessEqual(abs(lv['estimate'] - twin['estimate']), 1e-12)
                self.assertEqual({k: lv[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')},
                                 {k: twin[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')})
                self.assertEqual(lv['origin'], 'reused_xspec')
                self.assertEqual(self.b['export_codes'][f'{code}/{e}'][1], 'xspec' + self.xspec['export_codes'][f'{code}/{e}'][0])
        for card, codes in ((5, ['SHARED-RIDGE', 'CCA-RAW']), (8, ['XS-RIDGE', 'XS-RIDGE-W', 'XS-RIDGE-Q'])):
            self.assertEqual(self.b['checks'][f'same_scores_as_card_{card}'],
                             {'passed': True, 'card': card, 'codes': codes, 'tolerance': 1e-12,
                              'max_absolute_difference': 0.0})
        new = {lid.split('/')[0] for lid, lv in self.b['levels'].items() if lv['origin'] == 'new'}
        self.assertEqual(new, set(be.NEW_ARMS) | set(be.CONTROLS))

    def test_joint_top_carries_ccas_levels(self):
        for e in (U8, SBA):
            a, b = self.b['levels'][f'JOINT-TOP/{e}'], self.b['levels'][f'CCA-RAW/{e}']
            self.assertEqual((a['estimate'], a['interval']), (b['estimate'], b['interval']))
            self.assertEqual((a['origin'], b['origin']), ('new', 'reused_cca_diagnostics'))
        self.assertEqual(self.b['checks']['joint_top_equals_cca'], {'passed': True})
        self.assertEqual(self.b['display_names']['JOINT-TOP'], 'joint CCA')
        self.assertEqual(self.b['display_names']['CCA-RAW'], 'CCA (no training)')

    def test_names_and_seeds(self):
        self.assertEqual(self.b['display_names'], {
            'COH-ABS': 'coherence head', 'COH-SIGNED': 'signed coherence head', 'EIG-SPEC': 'spectral eigenvalue head',
            'EIG-RAW': 'eigenvalue head', 'EIG-JOINT': 'joint eigenvalue head', 'JOINT-TOP': 'joint CCA',
            'RAW-HARM-SUM': 'harmonic sum (no training)', 'SPEC-HARM-SUM': 'spectral harmonic sum (no training)',
            'SHARED-RIDGE': 'shared ridge scorer', 'CCA-RAW': 'CCA (no training)', 'XS-RIDGE': 'cross-spectral ridge',
            'XS-RIDGE-W': 'whitened cross-spectral ridge', 'XS-RIDGE-Q': 'cross-spectral ridge with quadrature'})
        seeds = {lid.split('/')[0]: lv['seeds'] for lid, lv in self.b['levels'].items()}
        self.assertEqual({k for k, v in seeds.items() if v == 'no training'},
                         {'JOINT-TOP', 'RAW-HARM-SUM', 'SPEC-HARM-SUM', 'CCA-RAW'})
        self.assertEqual({k for k, v in seeds.items() if v == 'deterministic fit'},
                         set(be.NEW_ARMS) | {'SHARED-RIDGE', 'XS-RIDGE', 'XS-RIDGE-W', 'XS-RIDGE-Q'})

    # ------------------------------------------------------------------ interval method, design, checks
    def test_interval_method_and_design(self):
        self.assertEqual(self.b['interval_method'], {'method': 'paired person bootstrap, percentile interval',
                                                     'draws': 2000, 'seed': 20261015, 'level': 0.95,
                                                     'conditional_on': 'the fixed training and fold procedure'})
        d = self.b['design']
        self.assertEqual(d['dataset'], self.released['studies']['cca_diagnostics']['design']['dataset'])
        self.assertEqual(d['endpoints'], self.xspec['design']['endpoints'])
        self.assertEqual((d['harmonics'], d['source_windows_per_fit'], d['seen_frequencies_per_fit'], d['main_fits']),
                         (3, 7680, 32, 175))
        self.assertEqual([(a['code'], a['fits'], a['input_count']) for a in d['arms']],
                         [('COH-ABS', 35, 108), ('COH-SIGNED', 35, 108), ('EIG-SPEC', 35, 6), ('EIG-RAW', 35, 6),
                          ('EIG-JOINT', 35, 6)])
        self.assertEqual([c['code'] for c in d['controls']], ['JOINT-TOP', 'RAW-HARM-SUM', 'SPEC-HARM-SUM'])
        self.assertEqual([(c['code'], c['card']) for c in d['comparators']],
                         [('SHARED-RIDGE', 5), ('CCA-RAW', 5), ('XS-RIDGE', 8), ('XS-RIDGE-W', 8), ('XS-RIDGE-Q', 8)])

    def test_checks_are_passes_and_counts(self):
        ch = self.b['checks']
        self.assertEqual(ch['fits'], {'main': 175, 'independent_refits': 175, 'bridges': 6, 'canaries': 5,
                                      'total': 361})
        self.assertEqual(ch['cca_identity'], {'pairs': 448000, 'decisions_identical': True})
        self.assertEqual(ch['coherence_zero_gate'], {'gated_pairs': 0, 'of': 37632000})
        self.assertEqual(ch['release_audit'], {'passed': True, 'sealed_artifacts': 1656, 'source_admission_sets': 186,
                                               'metric_entries_reconstructed': 9100, 'contrasts_reconstructed': 13})
        self.assertEqual(ch['numerical_review'], {'passed': True, 'technical_holds': 0})
        self.assertEqual(ch['aggregate_equals_release_audit'], {'passed': True, 'numeric_values': 120})
        for k in ('release_approval', 'interpretation_review', 'execution_review'):
            self.assertTrue(ch[k].get('approved') or ch[k].get('passed'), k)
        for v in floats(ch):                                    # counts only: no error magnitudes or timings
            self.assertIn(v, (bx.TOL, 0.0))

    def test_card_6s_not_run_item_is_answered_on_other_inputs(self):
        adapter_items = [x['item'] for x in self.released['studies']['cca_adapter']['not_run']]
        self.assertEqual(self.b['answers_not_run'], [{
            'card': 6, 'study': 'cca_adapter', 'item': 'simpler learned head on the CCA features',
            'arms': ['EIG-RAW', 'EIG-JOINT'],
            'inputs': 'squared canonical correlations between the raw window and the harmonic references',
            'same_inputs_as_card_6': False}])
        self.assertIn(self.b['answers_not_run'][0]['item'], adapter_items)

    def test_release_status_is_the_approvals(self):
        self.assertEqual(self.docs['eigen_approval']['status'], 'APPROVED_AGGREGATE_HANDOFF')
        self.assertEqual(self.aggregate['release_status'], 'independent_release_review_pending')   # frozen, unread
        self.assertNotIn('release_status', json.dumps(self.b))

    # ------------------------------------------------------------------ not published
    def test_withheld_values_and_the_thread_prediction_are_absent(self):
        held = set(floats(self.aggregate['canary_real_label_accuracy_descriptive_only']))
        held |= {v for arm in self.aggregate['evaluation_random_pairing_descriptive'].values()
                 for v in arm['permutation_mean'].values()}
        self.assertEqual(len(held), 10 + 10)
        self.assertFalse(held & set(floats(self.b)))
        self.assertIn('existing_normalized_xs_ridge_bet', self.aggregate)      # in the source ...
        text = json.dumps(self.b)
        for word in ('existing_normalized', 'below70', 'point_absolute_gap', 'canary_real', 'random_pairing',
                     'permutation', '2026102001', '2026102002', 'paired_difference'):
            self.assertNotIn(word, text, word)                                 # ... and not in the block
        self.assertFalse({0.70, 0.65, 0.759} & set(floats(self.b)))

    def test_no_private_or_refused_material(self):
        validate_public(self.blocks)
        text = json.dumps(self.blocks, ensure_ascii=False)
        for word in ('/Users', '/home', '/Volumes', '/mnt', 'trx', 'TRX', 'Gal4', 'BCI_Arena', 'twu', 'pending',
                     'private_root', 'prediction', 'seal_sha', '4b669f11', '"status"', '55%', 'huggingface',
                     'Twu31', 'commenter', 'historical', '75.9', 'decision_route3', 'research/', '.md', '.py',
                     'handoff', 'a53819bd7f7e'):
            self.assertNotIn(word, text, word)
        self.assertIsNone(bc.REFUSED_TEXT.search(text))                       # blocks_cca's rule: paths, hosts, the thread
        self.assertNotIn(0.55, list(floats(self.blocks)))
        self.assertIsNone(re.search(r'(?<![./\w-])v\d+\b', text))

    def test_every_limitation_and_not_run_item_resolves_in_its_pinned_record(self):
        self.assertEqual(self.b['limitations_keys'], list(be.LIMITATION_SOURCES))
        for key, (doc, ptr, phrase) in be.LIMITATION_SOURCES.items():
            self.assertIn(phrase, bx.resolve(self.docs[doc], ptr), key)
            self.assertTrue(re.fullmatch(r'[a-z0-9_]+', key), key)
        self.assertEqual([x['item'] for x in self.b['not_run']], list(be.NOT_RUN_SOURCES))
        for item, (doc, ptr, phrase) in be.NOT_RUN_SOURCES.items():
            self.assertIn(phrase, bx.resolve(self.docs[doc], ptr), item)
        for cid, keys in self.b['contrast_limitations'].items():
            self.assertIn(cid, self.b['contrasts'])
            self.assertLessEqual(set(keys), set(self.b['limitations_keys']))
        # The three caveats the plan states once on card 9.
        for key in ('cca_statistics_supplied', 'coherence_is_projection_cosine', 'spectral_not_validated_by_raw'):
            self.assertIn(key, self.b['limitations_keys'])
        # The engineering disclosures: the zero-energy edge fix and the timed-out suite, not counted as a pass.
        for key in ('zero_energy_edge_fix', 'synthetic_suite_timeout_not_a_pass'):
            self.assertIn(key, self.b['limitations_keys'])

    def test_declared_edits_and_handoff_context_are_kept_for_the_manifest(self):
        self.assertEqual(set(be.DECLARED_EDITS), set(be.STUDIES))
        self.assertTrue(all(be.DECLARED_EDITS[s] for s in be.STUDIES))
        self.assertEqual(self.docs['eigen_approval']['handoff_sha256'],
                         be.HANDOFF_CONTEXT['coherence_eigen']['bound_sha256'])
        self.assertEqual(be.PINS['released'], bx.PINS['released'])
        self.assertEqual(set(dict(be.NAME_KEY).values()), set(be.NEW_ARMS) | set(be.CONTROLS))


@unittest.skipUnless(be.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class EigenRefuses(unittest.TestCase):
    """Each check fires on its own: the pinned records are loaded once, edited in memory, and the block rebuilt."""

    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = be.load()
        cls.xs_docs, cls.xs_digests = bx.load()
        cls.xspec = bx.build_from(cls.xs_docs, cls.xs_digests)['xspec']

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)
        self.x = copy.deepcopy(self.xspec)

    def build(self):
        return be.eigen_block(self.d, self.h, self.xs_docs, self.xs_digests, self.x)

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def both(self, edit):
        """Edit the aggregate and the release audit's verified copy of it alike."""
        a, s = self.d['eigen_export'], self.d['eigen_audit']
        edit({'arms': a['arms'], 'contrasts': a['contrasts'], 'claim': a['prespecified_eigenvalue_claim']})
        edit({'arms': s['verified_aggregate_arms'], 'contrasts': s['all_13_verified_contrasts'],
              'claim': s['verified_prespecified_eigenvalue_claim']})

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(be.PINS)
        pins['eigen_export']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            be.build_blocks(pins)

    def test_an_aggregate_the_approval_did_not_bind_is_refused(self):
        self.h['eigen_export'] = 'f' * 64
        self.refused('binds')

    def test_release_status_comes_from_the_approval_only(self):
        self.d['eigen_export']['release_status'] = 'released'
        self.assertEqual(json.dumps(self.build(), sort_keys=True),
                         json.dumps(be.eigen_block(self.docs, self.digests, self.xs_docs, self.xs_digests, self.xspec),
                                    sort_keys=True))
        self.d['eigen_approval']['status'] = 'HELD'
        self.refused('does not approve')

    def test_the_aggregate_must_equal_the_release_audit(self):
        self.d['eigen_export']['arms']['EIG-RAW']['held8']['mean'] += 1e-9
        self.refused('differs from the release audit')

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.both(lambda x: x['contrasts'][5].__setitem__('mean', x['contrasts'][5]['mean'] + 1e-6))
        self.refused('not the difference of its levels')

    def test_the_card_8_comparators_must_be_card_8s(self):
        self.x['levels']['XS-RIDGE-W/u8']['estimate'] += 1e-9
        self.refused('differs from the card it reuses')

    def test_the_card_5_comparators_must_be_card_5s(self):
        self.d['released']['studies']['cca_diagnostics']['levels']['CCA-RAW/seen_ba']['interval'][1] += 1e-9
        self.refused('differs from the card it reuses')

    def test_the_run_must_have_pinned_card_8s_seal(self):
        ch = self.d['eigen_protocol']['comparator_hashes']
        key = next(k for k in ch if k.endswith('xspec_20261019/prediction-seal.json'))
        ch[key] = 'c' * 64
        self.refused('card 8 seal')

    def test_joint_top_must_carry_ccas_levels(self):
        def edit(x):
            x['arms']['JOINT-TOP']['held8']['ci95'][1] -= 1e-6
        self.both(edit)
        self.refused('JOINT-TOP/u8 is not CCA')

    def test_the_5pp_rules_must_follow_the_interval(self):
        self.both(lambda x: x['claim'].__setitem__('strict_5pp_equivalence', False))
        self.refused('the 5 pp rules')

    def test_the_near_zero_lower_bound_must_stay_negative(self):
        def edit(x):
            x['contrasts'][6]['ci95'][0] = 0.0
        self.both(edit)
        self.refused('near-zero negative bound')

    def test_a_flag_must_follow_the_rule(self):
        self.both(lambda x: x['contrasts'][5].__setitem__('above_zero', True))
        self.refused('does not follow the rule')

    def test_the_roles_must_be_the_handoffs(self):
        self.d['eigen_handoff'] = self.d['eigen_handoff'].replace('| Primary | held8 | EIG-RAW − CCA-RAW',
                                                                  '| Secondary | held8 | EIG-RAW − CCA-RAW')
        self.refused('the handoff states other contrasts or roles')

    def test_the_fit_counts_must_agree(self):
        self.d['eigen_approval']['total_fit_operations'] = 360
        self.refused('approval fit counts')

    def test_card_6s_item_must_be_on_card_6s_list(self):
        self.d['released']['studies']['cca_adapter']['not_run'] = []
        self.refused('card 6 not-run item')

    def test_a_limitation_its_record_does_not_state_is_refused(self):
        self.d['eigen_approval']['release_limits'][3] = 'The learned head adds accuracy.'
        self.refused('does not state')


if __name__ == '__main__':
    unittest.main()
