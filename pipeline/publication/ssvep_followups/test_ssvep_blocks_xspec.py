"""Card 8, the cross-spectral block: what it must carry, and what it must refuse.

Expected values are written out twice: at full precision, copied from the pinned aggregate (SHA-256 272bac55...) and
asserted equal to the double; and as the handoff's tables and the plan's card 8 lead state them, rendered the way the
site renders them (JavaScript toFixed on the double, the site's pct2 and pp2 formatters).
"""
import copy
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
from ssvep_followups import blocks_xspec as bx                                 # noqa: E402
from ssvep_followups.test_ssvep_blocks_cca import crow, floats, lrow, pct2, pp2   # noqa: E402

U8, SBA = 'u8', 'seen_ba'
AGGREGATE = '272bac552fdf509b4cc9bae930782de6a5673194a4989bcbdcbef3b4f1214a0c'
PROJECT = PUBLICATION.parents[1]

# Full precision, from the aggregate: code -> ((u8 estimate, lo, hi), (seen_ba estimate, lo, hi)).
LEVELS = {
    'XS-RIDGE': ((0.680267857142857, 0.6339263392857143, 0.7305379464285714),
                 (0.4855803571428572, 0.43561662946428575, 0.5398962053571429)),
    'XS-RIDGE-W': ((0.7999107142857145, 0.7620491071428571, 0.8379486607142856),
                   (0.6210491071428572, 0.5727667410714284, 0.6700669642857143)),
    'XS-MLP': ((0.7200000000000001, 0.6759114583333333, 0.7664605654761905),
               (0.5008333333333331, 0.4526380208333332, 0.551893601190476)),
    'XS-RIDGE-Q': ((0.6844642857142855, 0.6398080357142858, 0.7325892857142856),
                   (0.4789508928571428, 0.4300401785714286, 0.5335731026785714)),
    'CCA-RAW': ((0.809017857142857, 0.7680334821428572, 0.8513415178571431),
                (0.6545982142857143, 0.599368861607143, 0.7140184151785715)),
    'SUBSPACE-CROP': ((0.7319642857142856, 0.6861562499999999, 0.7813437499999999),
                      (0.5567410714285715, 0.5019815848214285, 0.6177706473214285)),
    'CHANNEL-HARMONIC': ((0.5521428571428572, 0.4999062499999999, 0.6090200892857144),
                         (0.35736607142857135, 0.3076768973214285, 0.41130580357142854)),
    'SHARED-RIDGE': ((0.5744642857142855, 0.5320424107142856, 0.6214308035714287),
                     (0.3491964285714285, 0.3083482142857143, 0.3919933035714284)),
}
# Full precision, from the aggregate, in its order: (id, estimate, lo, hi).
CONTRASTS = (
    ('XS-RIDGE minus SHARED-RIDGE/u8', 0.10580357142857141, 0.09053571428571427, 0.12277008928571427),
    ('XS-MLP minus CCA-RAW/u8', -0.08901785714285713, -0.11196502976190478, -0.06687351190476191),
    ('XS-RIDGE minus CCA-RAW/u8', -0.12875, -0.15553571428571428, -0.10223214285714285),
    ('XS-RIDGE-W minus XS-RIDGE/u8', 0.11964285714285715, 0.09633705357142855, 0.1430379464285714),
    ('XS-MLP minus XS-RIDGE/u8', 0.03973214285714284, 0.028598214285714286, 0.0509828869047619),
    ('XS-RIDGE-Q minus XS-RIDGE/u8', 0.004196428571428573, -0.0009821428571428546, 0.008930803571428576),
    ('XS-RIDGE minus SHARED-RIDGE/seen_ba', 0.13638392857142856, 0.11558035714285714, 0.1605390625),
    ('XS-RIDGE-W minus SHARED-RIDGE/seen_ba', 0.2718526785714286, 0.23999944196428574, 0.3059207589285714),
    ('XS-MLP minus SHARED-RIDGE/seen_ba', 0.15163690476190478, 0.1301854538690476, 0.1759678199404762),
    ('XS-RIDGE-Q minus SHARED-RIDGE/seen_ba', 0.12975446428571433, 0.10870089285714284, 0.15379799107142858),
)
ROLES = ['primary'] * 2 + ['secondary'] * 8
# The handoff's "All arm outcomes" table, held8 then seen32.
HANDOFF_LEVELS = {
    'SHARED-RIDGE': (('57.45', '53.20', '62.14'), ('34.92', '30.83', '39.20')),
    'XS-RIDGE': (('68.03', '63.39', '73.05'), ('48.56', '43.56', '53.99')),
    'XS-RIDGE-W': (('79.99', '76.20', '83.79'), ('62.10', '57.28', '67.01')),
    'XS-MLP': (('72.00', '67.59', '76.65'), ('50.08', '45.26', '55.19')),
    'XS-RIDGE-Q': (('68.45', '63.98', '73.26'), ('47.90', '43.00', '53.36')),
    'CCA-RAW': (('80.90', '76.80', '85.13'), ('65.46', '59.94', '71.40')),
    'SUBSPACE-CROP': (('73.20', '68.62', '78.13'), ('55.67', '50.20', '61.78')),
    'CHANNEL-HARMONIC': (('55.21', '49.99', '60.90'), ('35.74', '30.77', '41.13')),
}
# The handoff's "All ten formal paired contrasts" table, in percentage points.
HANDOFF_CONTRASTS = {
    'XS-RIDGE minus SHARED-RIDGE/u8': ('+10.58', '+9.05', '+12.28'),
    'XS-MLP minus CCA-RAW/u8': ('−8.90', '−11.20', '−6.69'),
    'XS-RIDGE minus CCA-RAW/u8': ('−12.88', '−15.55', '−10.22'),
    'XS-RIDGE-W minus XS-RIDGE/u8': ('+11.96', '+9.63', '+14.30'),
    'XS-MLP minus XS-RIDGE/u8': ('+3.97', '+2.86', '+5.10'),
    'XS-RIDGE-Q minus XS-RIDGE/u8': ('+0.42', '−0.10', '+0.89'),
    'XS-RIDGE minus SHARED-RIDGE/seen_ba': ('+13.64', '+11.56', '+16.05'),
    'XS-RIDGE-W minus SHARED-RIDGE/seen_ba': ('+27.19', '+24.00', '+30.59'),
    'XS-MLP minus SHARED-RIDGE/seen_ba': ('+15.16', '+13.02', '+17.60'),
    'XS-RIDGE-Q minus SHARED-RIDGE/seen_ba': ('+12.98', '+10.87', '+15.38'),
}


def pinned_json(path, digest):
    """A source re-read here, independently of the module, and refused unless it is the pinned file."""
    raw = (PROJECT / path).read_bytes()
    import hashlib
    assert hashlib.sha256(raw).hexdigest() == digest, path
    return json.loads(raw)


@unittest.skipUnless(bx.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class XspecBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bx.build_blocks()
        cls.b = cls.blocks['xspec']
        cls.docs, cls.digests = bx.load()
        cls.aggregate = pinned_json('research/publication_review_20261028/inputs/xspec-aggregate.json', AGGREGATE)
        cls.released = pinned_json(bx.RELEASED_PATH, bx.PINS['released']['sha256'])

    # ------------------------------------------------------------------ shape
    def test_one_block_with_the_released_fields(self):
        self.assertEqual(tuple(self.blocks), bx.STUDIES)
        b = self.b
        for k in bx.BLOCK_FIELDS + ('design', 'contrast_limitations', 'reused', 'descriptive_gaps'):
            self.assertIn(k, b)
        self.assertEqual(set(b['export_codes']), set(b['levels']) | set(b['contrasts']))
        for lid, lv in b['levels'].items():
            self.assertEqual(set(lv), {'estimate', 'interval', 'unit', 'people', 'seeds', 'origin'}, lid)
            self.assertEqual((lv['unit'], lv['people']), ('proportion', 70))
        for cid, c in b['contrasts'].items():
            self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'unit', 'people', 'seeds',
                                      'flags'}, cid)
            self.assertEqual((c['unit'], c['people']), ('difference of proportions', 70))
            self.assertIn(c['left'], b['levels'])
            self.assertIn(c['right'], b['levels'])
        for codes in b['export_codes'].values():
            self.assertTrue(codes and all(re.fullmatch(r'(?:[\w-]+(?:\.json)?)?#(?:/[^/]+)+', x) for x in codes), codes)
        self.assertEqual((len(b['levels']), len(b['contrasts'])), (16, 10))        # 8 arms x 2 endpoints; 10 contrasts
        self.assertEqual([c['role'] for c in b['contrasts'].values()], ROLES)
        self.assertEqual(b['source_sha256'], AGGREGATE)

    def test_the_build_is_deterministic(self):
        self.assertEqual(json.dumps(bx.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))

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

    def test_no_value_outside_the_aggregate_and_the_released_file(self):
        """Every float is a source double, except the descriptive gap (a difference of two of them) and the tolerance."""
        source = set(floats(self.aggregate)) | set(floats(self.released))
        gaps = {g['estimate'] for g in self.b['descriptive_gaps'].values()}
        for v in floats(self.b):
            self.assertTrue(v in source or v in gaps or v == bx.TOL, v)

    # ------------------------------------------------------------------ the handoff's tables and the plan's lead
    def test_the_handoff_tables_at_the_site_format(self):
        for code, (u8, sba) in HANDOFF_LEVELS.items():
            self.assertEqual((lrow(self.b['levels'][f'{code}/u8']), lrow(self.b['levels'][f'{code}/seen_ba'])),
                             (u8, sba), code)
        for cid, row in HANDOFF_CONTRASTS.items():
            self.assertEqual(crow(self.b['contrasts'][cid]), row, cid)

    def test_the_card_8_lead(self):
        """Plan section 2.1, card 8."""
        lv, c = self.b['levels'], self.b['contrasts']
        self.assertEqual(lrow(lv['XS-RIDGE/u8']), ('68.03', '63.39', '73.05'))
        self.assertEqual(pct2(lv['SHARED-RIDGE/u8']['estimate']), '57.45')
        self.assertEqual(crow(c['XS-RIDGE minus SHARED-RIDGE/u8']), ('+10.58', '+9.05', '+12.28'))
        self.assertEqual(lrow(lv['XS-MLP/u8']), ('72.00', '67.59', '76.65'))
        self.assertEqual(crow(c['XS-MLP minus CCA-RAW/u8']), ('−8.90', '−11.20', '−6.69'))
        self.assertIs(c['XS-MLP minus CCA-RAW/u8']['flags']['prespecified_noninferiority_to_CCA'], False)
        self.assertEqual(lrow(lv['XS-RIDGE-W/u8']), ('79.99', '76.20', '83.79'))
        self.assertEqual(pct2(lv['CCA-RAW/u8']['estimate']), '80.90')
        gaps = self.b['descriptive_gaps']
        self.assertEqual((pp2(gaps['XS-RIDGE-W minus CCA-RAW/u8']['estimate']),
                          pp2(gaps['XS-RIDGE-W minus CCA-RAW/seen_ba']['estimate'])), ('−0.91', '−3.35'))
        new = [k for k in bx.NEW_ARMS]
        self.assertTrue(all(lv[f'{k}/seen_ba']['estimate'] < lv['CCA-RAW/seen_ba']['estimate'] for k in new))
        q = c['XS-RIDGE-Q minus XS-RIDGE/u8']
        self.assertEqual(crow(q), ('+0.42', '−0.10', '+0.89'))
        self.assertTrue(q['flags']['interval_includes_zero'] and q['flags']['strict_equivalence_2pp'])

    # ------------------------------------------------------------------ roles, flags, the unplanned pair
    def test_roles_follow_the_protocol_and_the_handoff(self):
        st = self.docs['xspec_protocol']['statistics']
        primary = [f'{a} minus {b}/u8' for a, b in st['primary_held8']]
        self.assertEqual([k for k, c in self.b['contrasts'].items() if c['role'] == 'primary'], primary)
        self.assertEqual(primary, ['XS-RIDGE minus SHARED-RIDGE/u8', 'XS-MLP minus CCA-RAW/u8'])

    def test_flags_are_the_aggregates_and_follow_the_rules(self):
        for i, (cid, c) in enumerate(self.b['contrasts'].items()):
            src = self.aggregate['contrasts'][i]
            for k in ('above_zero', 'below_zero', 'strict_equivalence_2pp', 'prespecified_noninferiority_to_CCA'):
                self.assertIs(c['flags'][k], src[k], f'{cid} {k}')
            lo, hi = c['interval']
            self.assertIs(c['flags']['interval_includes_zero'], lo <= 0 <= hi)
            self.assertNotIn('bound_below_two_decimals', c['flags'])
        self.assertEqual([k for k, c in self.b['contrasts'].items() if c['flags']['strict_equivalence_2pp']],
                         ['XS-RIDGE-Q minus XS-RIDGE/u8'])
        self.assertEqual([k for k, c in self.b['contrasts'].items()
                          if c['flags']['prespecified_noninferiority_to_CCA'] is not None], ['XS-MLP minus CCA-RAW/u8'])

    def test_the_whitened_readout_against_cca_is_descriptive_only(self):
        self.assertFalse(any({c['left'].split('/')[0], c['right'].split('/')[0]} == {'XS-RIDGE-W', 'CCA-RAW'}
                             for c in self.b['contrasts'].values()))
        self.assertEqual(self.b['undefined'], [{'contrast': 'XS-RIDGE-W minus CCA-RAW', 'reason': 'not_a_planned_contrast'}])
        for e in (U8, SBA):
            g = self.b['descriptive_gaps'][f'XS-RIDGE-W minus CCA-RAW/{e}']
            self.assertNotIn('interval', g)
            self.assertEqual(g['estimate'], self.b['levels'][f'XS-RIDGE-W/{e}']['estimate']
                             - self.b['levels'][f'CCA-RAW/{e}']['estimate'])
        self.assertEqual(self.b['descriptive_gaps']['XS-RIDGE-W minus CCA-RAW/u8']['estimate'], -0.009107142857142536)
        self.assertEqual(self.b['descriptive_gaps']['XS-RIDGE-W minus CCA-RAW/seen_ba']['estimate'], -0.03354910714285708)

    # ------------------------------------------------------------------ reused comparators: card 5
    def test_the_reused_comparators_are_card_5s_released_levels(self):
        diag = self.released['studies']['cca_diagnostics']
        self.assertEqual(set(self.b['reused']), {'CCA-RAW', 'SUBSPACE-CROP', 'CHANNEL-HARMONIC', 'SHARED-RIDGE'})
        for code, r in self.b['reused'].items():
            self.assertEqual(r, {'card': 5, 'study': 'cca_diagnostics', 'anchor': 'cca-mechanism', 'code': code})
            self.assertEqual(self.b['display_names'][code], diag['display_names'][code])
            for e in (U8, SBA):
                lv, twin = self.b['levels'][f'{code}/{e}'], diag['levels'][f'{code}/{e}']
                self.assertLessEqual(abs(lv['estimate'] - twin['estimate']), 1e-12)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(lv['interval'], twin['interval'])), 1e-12)
                self.assertEqual({k: lv[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')},
                                 {k: twin[k] for k in ('estimate', 'interval', 'unit', 'people', 'seeds')})
                self.assertEqual(lv['origin'], 'reused_cca_diagnostics')
                codes = self.b['export_codes'][f'{code}/{e}']
                self.assertEqual(codes[1], 'cca_diagnostics' + diag['export_codes'][f'{code}/{e}'][0])
                self.assertEqual(codes[2], f'new-ssvep-frequencies-update.json#/studies/cca_diagnostics/levels/{code}~1{e}')
        for k in bx.NEW_ARMS:
            self.assertEqual({self.b['levels'][f'{k}/{e}']['origin'] for e in (U8, SBA)}, {'new'})
        self.assertEqual(self.b['checks']['same_scores_as_card_5'],
                         {'passed': True, 'card': 5, 'codes': ['CCA-RAW', 'SUBSPACE-CROP', 'CHANNEL-HARMONIC',
                                                               'SHARED-RIDGE'],
                          'tolerance': 1e-12, 'max_absolute_difference': 0.0})

    def test_names_and_seeds(self):
        self.assertEqual(self.b['display_names'], {
            'XS-RIDGE': 'cross-spectral ridge', 'XS-RIDGE-W': 'whitened cross-spectral ridge',
            'XS-MLP': 'cross-spectral MLP', 'XS-RIDGE-Q': 'cross-spectral ridge with quadrature',
            'CCA-RAW': 'CCA (no training)', 'SUBSPACE-CROP': 'cropped-spectrum match (no training)',
            'CHANNEL-HARMONIC': 'channel-energy average', 'SHARED-RIDGE': 'shared ridge scorer'})
        seeds = {lid.split('/')[0]: lv['seeds'] for lid, lv in self.b['levels'].items()}
        self.assertEqual(seeds, {'XS-RIDGE': 'deterministic fit', 'XS-RIDGE-W': 'deterministic fit', 'XS-MLP': 3,
                                 'XS-RIDGE-Q': 'deterministic fit', 'CCA-RAW': 'no training',
                                 'SUBSPACE-CROP': 'no training', 'CHANNEL-HARMONIC': 'no training',
                                 'SHARED-RIDGE': 'deterministic fit'})
        self.assertEqual([c['seeds'] for c in self.b['contrasts'].values()],
                         ['deterministic fit', 3, 'deterministic fit', 'deterministic fit', 3, 'deterministic fit',
                          'deterministic fit', 'deterministic fit', 3, 'deterministic fit'])

    # ------------------------------------------------------------------ interval method, design, checks
    def test_interval_method_and_design(self):
        self.assertEqual(self.b['interval_method'], {'method': 'paired person bootstrap, percentile interval',
                                                     'draws': 2000, 'seed': 20261015, 'level': 0.95})
        d = self.b['design']
        self.assertEqual(d['dataset'], self.released['studies']['cca_diagnostics']['design']['dataset'])
        self.assertEqual(d['endpoints'], {U8: {'candidate_count': 8, 'chance': 0.125},
                                          SBA: {'candidate_count': 32, 'chance': 0.03125}})
        self.assertEqual((d['harmonics'], d['source_windows_per_fit'], d['seen_frequencies_per_fit'], d['main_fits']),
                         (3, 7680, 32, 210))
        self.assertEqual([(a['code'], a['fits'], a['input_count']) for a in d['arms']],
                         [('XS-RIDGE', 35, 108), ('XS-RIDGE-W', 35, 108), ('XS-MLP', 105, 108), ('XS-RIDGE-Q', 35, 192)])
        mlp = d['arms'][2]
        self.assertEqual((mlp['training_seeds'], mlp['hidden_units'], mlp['training_epochs']), (3, 64, 60))
        self.assertEqual([(c['code'], c['card']) for c in d['comparators']],
                         [('CCA-RAW', 5), ('SUBSPACE-CROP', 5), ('CHANNEL-HARMONIC', 5), ('SHARED-RIDGE', 5)])
        self.assertEqual(d['comparators'][2]['variant'], 'per-harmonic spans')

    def test_checks_are_passes_and_counts(self):
        ch = self.b['checks']
        self.assertEqual(ch['fits'], {'main': 210, 'additional': 118, 'total': 328, 'bridges': 6, 'canaries': 4,
                                      'independent_ridge_refits': 105, 'independent_mlp_refits': 3,
                                      'mlp_forward_reconstructions': 105})
        self.assertEqual(ch['cca_identity'], {'pairs': 448000})
        self.assertEqual(ch['release_audit'], {'passed': True, 'sealed_artifacts': 2424, 'source_admission_sets': 223,
                                               'metric_entries_recomputed': 7000, 'retained_payloads_rehashed': 706,
                                               'archived_originals_rehashed': 720})
        self.assertEqual(ch['pre_score_corrections'], {'count': 2})
        for k in ('release_approval', 'release_review', 'execution_review'):
            self.assertTrue(ch[k].get('approved') or ch[k].get('passed'), k)
        # Counts only: no error magnitudes, timings or seeds of the audit in the block.
        for v in floats(ch):
            self.assertIn(v, (bx.TOL, 0.0))

    def test_release_status_is_the_approvals(self):
        self.assertEqual(self.docs['xspec_approval']['status'], 'APPROVED_AGGREGATE_HANDOFF')
        self.assertEqual(self.aggregate['release_status'], 'independent_release_review_pending')   # frozen, unread
        self.assertNotIn('release_status', json.dumps(self.b))

    # ------------------------------------------------------------------ not published
    def test_withheld_values_are_absent(self):
        """Per-seed MLP means, canary and random-pairing accuracies: none of them, as a key or as a value."""
        held = set(floats(self.aggregate['per_seed_descriptive']['XS-MLP']))
        held |= set(floats(self.aggregate['canary_real_label_accuracy_descriptive_only']))
        held |= {v for arm in self.aggregate['random_pairing'].values() for v in arm['permutation_mean'].values()}
        self.assertEqual(len(held), 6 + 8 + 16 - 1)          # two canaries share one value
        self.assertFalse(held & set(floats(self.b)))
        text = json.dumps(self.b)
        for word in ('per_seed', 'canary_real', 'random_pairing', 'permutation', '20261019', '20261021', '2026101902',
                     'MLP_aggregation', 'logit ensemble'):
            self.assertNotIn(word, text, word)

    def test_no_private_thread_or_refused_material(self):
        validate_public(self.blocks)
        text = json.dumps(self.blocks, ensure_ascii=False)
        for word in ('/Users', '/home', '/Volumes', '/mnt', 'trx', 'TRX', 'Gal4', 'BCI_Arena', 'twu', 'pending',
                     'private_root', 'prediction', 'seal_sha', '74055f7d', 'release_status', '"status"', '55%',
                     'huggingface', 'commenter', 'historical', '39%', '39.00', '32–36', 'decision_route3', 'research/',
                     '.md', '.py', 'handoff', '884565105c98'):
            self.assertNotIn(word, text, word)
        self.assertIsNone(bc.REFUSED_TEXT.search(text))                       # blocks_cca's rule: paths, hosts, the thread
        self.assertNotIn(0.55, list(floats(self.blocks)))
        self.assertNotIn(0.39, list(floats(self.blocks)))
        self.assertIsNone(re.search(r'(?<![./\w-])v\d+\b', text))

    def test_every_limitation_and_not_run_item_resolves_in_its_pinned_record(self):
        self.assertEqual(self.b['limitations_keys'], list(bx.LIMITATION_SOURCES))
        for key, (doc, ptr, phrase) in bx.LIMITATION_SOURCES.items():
            self.assertIn(phrase, bx.resolve(self.docs[doc], ptr), key)
            self.assertTrue(re.fullmatch(r'[a-z0-9_]+', key), key)
        self.assertEqual([x['item'] for x in self.b['not_run']], list(bx.NOT_RUN_SOURCES))
        for item, (doc, ptr, phrase) in bx.NOT_RUN_SOURCES.items():
            self.assertIn(phrase, bx.resolve(self.docs[doc], ptr), item)
        for cid, keys in self.b['contrast_limitations'].items():
            self.assertIn(cid, self.b['contrasts'])
            self.assertLessEqual(set(keys), set(self.b['limitations_keys']))
        self.assertEqual(self.b['contrast_limitations']['XS-MLP minus XS-RIDGE/u8'], ['mlp_ridge_bundled_changes'])
        self.assertEqual(self.b['contrast_limitations']['XS-RIDGE-W minus XS-RIDGE/u8'], ['whitening_composite_recipe'])
        self.assertIn('not_a_fixed_quadratic_form', self.b['limitations_keys'])
        self.assertIn('unadjusted_intervals', self.b['limitations_keys'])

    def test_declared_edits_and_handoff_context_are_kept_for_the_manifest(self):
        self.assertEqual(set(bx.DECLARED_EDITS), set(bx.STUDIES))
        self.assertTrue(all(bx.DECLARED_EDITS[s] for s in bx.STUDIES))
        self.assertEqual(self.docs['xspec_approval']['handoff_sha256'], bx.HANDOFF_CONTEXT['xspec']['bound_sha256'])
        self.assertEqual(bx.PINS['xspec_export']['sha256'], AGGREGATE)
        self.assertEqual(dict(bx.NAME_KEY), {'cross-spectral ridge': 'XS-RIDGE',
                                             'whitened cross-spectral ridge': 'XS-RIDGE-W',
                                             'cross-spectral ridge with quadrature': 'XS-RIDGE-Q',
                                             'cross-spectral MLP': 'XS-MLP'})


@unittest.skipUnless(bx.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class XspecRefuses(unittest.TestCase):
    """Each check fires on its own: the pinned records are loaded once, edited in memory, and the block rebuilt."""

    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = bx.load()

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)

    def build(self):
        return bx.build_from(self.d, self.h)

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(bx.PINS)
        pins['xspec_export']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            bx.build_blocks(pins)

    def test_pins_of_another_shape_are_refused(self):
        pins = copy.deepcopy(bx.PINS)
        del pins['released']
        with self.assertRaisesRegex(ValueError, 'pins: expected'):
            bx.build_blocks(pins)

    def test_an_aggregate_the_approval_did_not_bind_is_refused(self):
        self.h['xspec_export'] = 'f' * 64
        self.refused('binds')

    def test_release_status_comes_from_the_approval_only(self):
        self.d['xspec_export']['release_status'] = 'released'          # the aggregate's own field is never read
        self.assertEqual(json.dumps(self.build(), sort_keys=True),
                         json.dumps(bx.build_from(self.docs, self.digests), sort_keys=True))
        self.d['xspec_approval']['status'] = 'HELD'
        self.refused('does not approve')

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.d['xspec_export']['contrasts'][0]['mean'] += 1e-6
        self.refused('not the difference of its levels')

    def test_an_interval_must_hold_its_point(self):
        self.d['xspec_export']['arms']['XS-RIDGE']['held8']['ci95'] = [0.69, 0.73]
        self.refused('does not hold its point')

    def test_a_flag_must_follow_the_protocol_rule(self):
        self.d['xspec_export']['contrasts'][5]['strict_equivalence_2pp'] = False
        self.refused('does not follow the protocol rule')
        self.d = copy.deepcopy(self.docs)
        self.d['xspec_export']['contrasts'][1]['prespecified_noninferiority_to_CCA'] = True
        self.refused('non-inferiority')

    def test_the_reused_comparators_must_be_card_5s(self):
        self.d['released']['studies']['cca_diagnostics']['levels']['SUBSPACE-CROP/u8']['estimate'] += 1e-9
        self.refused('differs from the card it reuses')

    def test_a_difference_within_1e_12_is_accepted(self):
        lv = self.d['released']['studies']['cca_diagnostics']['levels']['SHARED-RIDGE/u8']
        lv['interval'] = [lv['interval'][0] + 1e-13, lv['interval'][1]]
        worst = self.build()['xspec']['checks']['same_scores_as_card_5']['max_absolute_difference']
        self.assertTrue(0.0 < worst <= 1e-12, worst)
        lv['interval'] = [lv['interval'][0] + 1e-11, lv['interval'][1]]
        self.refused('differs from the card it reuses')

    def test_the_comparators_must_be_card_5s_study(self):
        ch = self.d['xspec_protocol']['comparator_hashes']
        key = next(k for k in ch if k.endswith('cca_diagnostics_20261015/protocol.json'))
        ch[key] = 'b' * 64
        self.refused('xspec comparators protocol')

    def test_card_5s_names_are_kept(self):
        self.d['released']['studies']['cca_diagnostics']['display_names']['CCA-RAW'] = 'raw CCA'
        self.refused('two names for one set of scores')

    def test_the_roles_must_be_the_handoffs(self):
        self.d['xspec_handoff'] = self.d['xspec_handoff'].replace('| Primary | held8 | XS-MLP', '| Secondary | held8 | XS-MLP')
        self.refused('the handoff states other contrasts or roles')

    def test_an_unplanned_contrast_is_refused(self):
        arms = self.d['xspec_export']['arms']
        diff = arms['XS-RIDGE-W']['held8']['mean'] - arms['CCA-RAW']['held8']['mean']
        self.d['xspec_export']['contrasts'].append({'a': 'XS-RIDGE-W', 'b': 'CCA-RAW', 'metric': 'held8', 'mean': diff,
                                                    'ci95': [diff - 0.01, diff + 0.01], 'above_zero': False,
                                                    'below_zero': False, 'strict_equivalence_2pp': True,
                                                    'prespecified_noninferiority_to_CCA': None})
        self.refused('ten contrasts')

    def test_the_descriptive_gap_must_be_the_handoffs(self):
        self.d['xspec_handoff'] = self.d['xspec_handoff'].replace('| XS-RIDGE-W | -0.91 |', '| XS-RIDGE-W | -0.92 |')
        self.refused("not the handoff's")

    def test_the_fit_counts_must_agree(self):
        self.d['xspec_audit']['additional_fits'] = 117
        self.refused('additional fits')

    def test_a_limitation_its_record_does_not_state_is_refused(self):
        self.d['xspec_caveats']['notes'][2] = 'The MLP is better.'
        self.refused('does not state')

    def test_a_withheld_value_is_refused(self):
        b = bx.xspec_block(self.d, self.h)
        seed_mean = self.d['xspec_export']['per_seed_descriptive']['XS-MLP']['20261020']['held8']
        b['design']['note_value'] = seed_mean
        held = bx.withheld(self.d['xspec_export'], {k: self.d['xspec_export'][k] for k in ('arms', 'contrasts')})
        with self.assertRaisesRegex(ValueError, 'withheld value'):
            bx.finish({'xspec': b}, held)

    def test_the_scrub_refuses_what_must_not_be_published(self):
        for bad in ({'per_seed_descriptive': {}}, {'random_pairing': {}}, {'canary_real_label_accuracy': 0.1},
                    {'existing_normalized_xs_ridge_bet': {}}, {'x': 0.39}, {'note': 'above the historical 39% point'},
                    {'note': 'the 32–36% band'}, {'note': 'the commenter predicted'}, {'note': 'run on trx50'},
                    {'note': '/mnt/bigdata/x'}, {'x': 0.55}, {'x': 55}, {'note': 'release review pending'},
                    {'note': 'the v2 rule'}, {'note': 'the best readout'}, {'epochs': 60}, {'x': [0, 159, 160]},
                    {'prediction_seal_sha256': 'a'}, {'percentile_rule': 'x'}):
            with self.assertRaises(ValueError, msg=repr(bad)):
                bx.scrub_check(bad)
        bx.scrub_check({'note': 'whitened cross-spectral ridge', 'x': 0.7999107142857145, 'r': [0, 2], 'n': 448000})


if __name__ == '__main__':
    unittest.main()
