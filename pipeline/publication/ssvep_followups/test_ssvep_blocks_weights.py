"""SS-C, the weighting blocks (cards 12 to 14): what they must carry, and what they must refuse.

Expected figures are written out from the records that state them: the harmonic-gap interpretation review's tables
and the handoff tables the text reviews accepted (fixed decay, rising weights), and plan section 2.1. They are
rendered the way the site renders them: JavaScript toFixed on the double value, so an exact decimal tie rounds away
from zero. The sources are re-read here with their own pointer walk, not through the builder's helpers.
"""
import copy
import hashlib
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

import export_new_ssvep_frequencies_update as released_assembler   # noqa: E402  (its boundary rules, read only)
from export_snapshot import validate_public               # noqa: E402
from ssvep_followups import blocks_cca as bc               # noqa: E402
from ssvep_followups import blocks_weights as bw           # noqa: E402

PROJECT = PUBLICATION.parents[1]
QUEUE = 'research/autonomous_validation_20261026/handoff_20261028/Website Integration Queue.json'
ENDPOINTS = ('u8', 'seen_ba', 'dry', 'wet')
DROPPED = 11 / 20          # the thread's confidence figure, never spelled as digits


def js_fixed(x, digits=2):
    """Number.prototype.toFixed: the exact value of the double, ties away from zero."""
    return str(Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def pct(raw, digits=2):
    return js_fixed(raw * 100, digits)


def signed(value, digits):
    return ('' if value == 0 else '+' if value > 0 else '−') + js_fixed(abs(value), digits)


def pp(raw, digits=2):
    return signed(raw * 100, digits)


def crow(c, digits=4):
    return pp(c['estimate'], digits), pp(c['interval'][0], digits), pp(c['interval'][1], digits)


def walk(doc, ptr):
    """An independent RFC 6901 walk."""
    cur = doc
    for t in ptr.split('/')[1:]:
        t = t.replace('~1', '/').replace('~0', '~')
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


def floats(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from floats(v)
    elif isinstance(value, list):
        for v in value:
            yield from floats(v)
    elif isinstance(value, float):
        yield value


def keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys(v)


def strings(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)
    elif isinstance(value, str):
        yield value


class FormatterEmulation(unittest.TestCase):
    def test_ties_round_away_from_zero_as_javascript_does(self):
        self.assertEqual(pct(0.82875), '82.88')
        self.assertEqual(pp(-0.05718749999999998, 4), '−5.7187')     # the double; the exact count would be −5.71875
        self.assertEqual(pp(0.0, 4), '0.0000')


@unittest.skipUnless(bw.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class WeightBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bw.build_blocks()
        cls.gap, cls.decay, cls.rise = (cls.blocks[k] for k in bw.STUDIES)
        cls.docs, cls.digests = bw.load()

    def export_of(self, study):
        return self.docs[bw.EXPORT_OF[study]]

    # ------------------------------------------------------------------ shape
    def test_three_blocks_with_the_block_fields(self):
        self.assertEqual(tuple(self.blocks), ('harmonic_gap', 'fixed_decay', 'rising_weights'))
        for name, b in self.blocks.items():
            for k in bw.BLOCK_FIELDS:
                self.assertIn(k, b, f'{name} lacks {k}')
            self.assertEqual((b['card'], b['anchor']), bw.CARDS[name])
            self.assertEqual(set(b['export_codes']), set(b['levels']) | set(b['contrasts']) | set(b.get('gap', {})))
            for lid, lv in b['levels'].items():
                self.assertLessEqual({'estimate', 'interval', 'interval_level', 'unit', 'people', 'seeds', 'origin'},
                                     set(lv), lid)
                self.assertLessEqual(set(lv) - {'estimate', 'interval', 'interval_level', 'unit', 'people', 'seeds',
                                                'origin'}, {'same_estimate_as'}, lid)
                self.assertEqual((lv['unit'], lv['seeds'], lv['origin']), ('proportion', 'no training', 'new'))
                self.assertIn(lid.split('/')[0], b['display_names'])
                self.assertIn(lid.split('/')[1], ENDPOINTS)
            for cid, c in b['contrasts'].items():
                self.assertEqual(set(c), {'role', 'left', 'right', 'estimate', 'interval', 'interval_level', 'unit',
                                          'people', 'seeds', 'flags'}, cid)
                self.assertEqual(c['unit'], 'difference of proportions')
                self.assertEqual(cid, f'{c["left"].split("/")[0]} minus {c["right"]}')
                self.assertIn(c['role'], ('primary', 'secondary', 'rounding_check'))
            for codes in b['export_codes'].values():
                self.assertTrue(codes and all(re.fullmatch(r'#(?:/[^/]+)+', x) for x in codes), codes)
        self.assertEqual([len(self.blocks[s]['levels']) for s in bw.STUDIES], [12, 12, 12])
        self.assertEqual([len(self.blocks[s]['contrasts']) for s in bw.STUDIES], [15, 6, 12])

    def test_the_build_is_deterministic(self):
        self.assertEqual(json.dumps(bw.build_blocks(), sort_keys=True), json.dumps(self.blocks, sort_keys=True))

    def test_each_block_carries_its_own_interval_method(self):
        want = {'harmonic_gap': (20261021, 20261022), 'fixed_decay': (2026102201, 2026102202),
                'rising_weights': (2026102501, 2026102502)}
        for name, (beta, wear) in want.items():
            m = self.blocks[name]['interval_method']
            self.assertEqual((m['method'], m['draws'], m['level'], m['seeds']),
                             ('paired person bootstrap, percentile interval', 20000, 0.95,
                              {'BETA': beta, 'Wearable-102': wear}), name)
        fam = self.gap['interval_method']['family']
        self.assertEqual((fam['comparisons'], fam['adjustment']), (9, 'Bonferroni'))
        self.assertAlmostEqual(fam['level'], 1 - 0.05 / 9, places=12)
        self.assertEqual(js_fixed(fam['level'] * 100, 2), '99.44')
        self.assertEqual(self.decay['interval_method']['equivalence'], {'level': 0.9, 'margin': 0.005})

    def test_every_value_is_the_source_double(self):
        for name, b in self.blocks.items():
            ex = self.export_of(name)
            for lid, lv in b['levels'].items():
                here = walk(ex, b['export_codes'][lid][0][1:])
                if lv['interval'] is None:                                    # fixed decay: a bare accuracy
                    self.assertEqual(lv['estimate'], here, lid)
                else:
                    self.assertEqual((lv['estimate'], lv['interval']), (here['estimate'], here['ci95']), lid)
            for cid, c in b['contrasts'].items():
                codes = b['export_codes'][cid]
                if len(codes) == 2:                                           # estimate and interval fields
                    self.assertEqual((c['estimate'], c['interval']),
                                     (walk(ex, codes[0][1:]), walk(ex, codes[1][1:])), cid)
                else:
                    here = walk(ex, codes[0][1:])
                    ci = here['ci_family99_444'] if c['flags'].get('family_member') else here['ci95']
                    self.assertEqual((c['estimate'], c['interval']), (here['estimate'], ci), cid)
        for gid, g in self.gap['gap'].items():
            here = walk(self.export_of('harmonic_gap'), self.gap['export_codes'][gid][0][1:])
            ci = here['ci_family99_444'] if g['flags'].get('family_member') else here['ci95']
            self.assertEqual((g['estimate'], g['interval']), (here['estimate'], ci), gid)

    # ------------------------------------------------------------------ card 12
    def test_the_three_score_bridge(self):
        """Interpretation review, matched score bridge table (percent to four places)."""
        want = {'u8': ('80.9018', '80.9375', '82.9018', '82.8750'),
                'dry': ('65.3758', '65.3758', '66.0376', '66.0784'),
                'wet': ('81.6503', '81.6013', '82.7696', '82.7451')}
        for e, row in want.items():
            self.assertEqual(tuple(pct(self.gap['levels'][f'{c}/{e}']['estimate'], 4)
                                   for c in ('J', 'B', 'S', 'JplusG')), row, e)
        self.assertEqual(tuple(pct(self.gap['levels'][f'{c}/u8']['estimate']) for c in ('J', 'B', 'S')),
                         ('80.90', '80.94', '82.90'))                  # plan card 12 lead

    def test_the_family_contrasts_at_the_review_figures(self):
        want = {('B minus J', 'u8'): ('+0.0357', '−0.0982', '+0.1875'),
                ('S minus B', 'u8'): ('+1.9643', '+1.0625', '+2.9554'),
                ('B minus J', 'dry'): ('0.0000', '−0.1634', '+0.1634'),
                ('S minus B', 'dry'): ('+0.6618', '−0.2451', '+1.5850'),
                ('B minus J', 'wet'): ('−0.0490', '−0.1879', '+0.0817'),
                ('S minus B', 'wet'): ('+1.1683', '+0.3513', '+2.0135')}
        for (key, e), row in want.items():
            c = self.gap['contrasts'][f'{key}/{e}']
            self.assertEqual(crow(c), row, (key, e))
            self.assertEqual((c['role'], c['interval_level'], c['flags']['family_member']),
                             ('primary', self.gap['family']['interval_level'], True))
        gap_want = {'u8': ('+0.061708', '+0.051920', '+0.073158'), 'dry': ('+0.023174', '+0.018583', '+0.028614'),
                    'wet': ('+0.043520', '+0.035529', '+0.052476')}
        for e, row in gap_want.items():
            g = self.gap['gap'][f'G true minus mean distractor/{e}']
            self.assertEqual((signed(g['estimate'], 6), signed(g['interval'][0], 6), signed(g['interval'][1], 6)), row)
            self.assertEqual((g['unit'], g['role']), ('difference of squared correlations', 'primary'))

    def test_the_family_is_the_nine_prespecified_comparisons(self):
        fam = self.gap['family']
        planned = self.docs['gap_protocol']['statistics']['primary_family']
        cohort = {v: k for k, v in bw.GAP_COHORTS.items()}
        metric = {'G_true_minus_mean_distractor': 'G true minus mean distractor',
                  'accuracy_S_shared_minus_S_joint': 'B minus J', 'accuracy_S_free_minus_S_shared': 'S minus B'}
        self.assertEqual(fam['members'], [f'{metric[p["metric"]]}/{cohort[p["cohort"]]}' for p in planned])
        self.assertEqual(fam['resolved'], ['G true minus mean distractor/u8', 'S minus B/u8',
                                           'G true minus mean distractor/dry', 'G true minus mean distractor/wet',
                                           'S minus B/wet'])
        self.assertIs(fam['all_gap_intervals_above_zero'], True)
        for e in ('u8', 'dry', 'wet'):
            self.assertIn('no_b_over_j_resolved', self.gap['contrast_limitations'][f'B minus J/{e}'])
        self.assertEqual(self.gap['contrast_limitations']['S minus B/dry'], ['dry_bridge_unresolved'])
        # The nominal 95% intervals of the family members are not published beside their family intervals.
        m = self.docs['gap_export']['cohorts']['Wearable-dry']['metrics']['accuracy_S_free_minus_S_shared']
        self.assertGreater(m['ci95'][0], 0)                              # nominally positive ...
        self.assertNotIn(m['ci95'][0], list(floats(self.blocks)))         # ... and never shown

    def test_secondary_steps_and_the_alternate_route_are_nominal(self):
        for e in ('u8', 'dry', 'wet'):
            for key in ('S minus J', 'JplusG minus J', 'S minus JplusG'):
                c = self.gap['contrasts'][f'{key}/{e}']
                self.assertEqual((c['role'], c['interval_level']), ('secondary', 0.95))
        self.assertEqual(crow(self.gap['contrasts']['S minus J/u8']), ('+2.0000', '+1.3214', '+2.7411'))
        self.assertEqual(crow(self.gap['contrasts']['JplusG minus J/u8'])[0], '+1.9732')
        self.assertEqual(crow(self.gap['contrasts']['S minus JplusG/u8'])[0], '+0.0268')

    def test_g_and_r_in_squared_correlation_units(self):
        """Interpretation review: R true-minus-mean-distractor -0.0000389, -0.0000681, -0.0001612; G table."""
        for e, r in (('u8', '−0.0000389'), ('dry', '−0.0000681'), ('wet', '−0.0001612')):
            self.assertEqual(signed(self.gap['gap'][f'R true minus mean distractor/{e}']['estimate'], 7), r)
        for e, (t, d) in (('u8', ('+0.121304', '+0.059595')), ('dry', ('+0.062351', '+0.039177')),
                          ('wet', ('+0.088074', '+0.044554'))):
            self.assertEqual((signed(self.gap['gap'][f'G true/{e}']['estimate'], 6),
                              signed(self.gap['gap'][f'G mean distractor/{e}']['estimate'], 6)), (t, d))
        units = {g['unit'] for g in self.gap['gap'].values()}
        self.assertEqual(units, {'squared correlation', 'difference of squared correlations'})
        self.assertNotIn('proportion', units)
        self.assertEqual(len(self.gap['gap']), 18)                        # 6 statistics x 3 cohorts
        self.assertFalse(any('Delta' in k for k in self.gap['gap']))

    def test_the_identity_and_the_coupling_residual(self):
        idt = self.gap['identity']
        self.assertIs(idt['joint_cca_equals_top_eigenvalue_of_sum'], False)
        self.assertIs(idt['residual_reported_beside_gap'], True)
        self.assertIn('not orthogonal over a finite window', idt['reason'])
        self.assertEqual(set(idt['quantities']), {'G', 'R', 'Delta'})
        self.assertIn(idt['limitation_key'], self.gap['limitations_keys'])
        for e in ('u8', 'dry', 'wet'):
            self.assertIn(f'R true minus mean distractor/{e}', self.gap['gap'])

    def test_win_fractions_are_labelled_not_accuracies(self):
        for e, want in (('u8', '85.6926'), ('dry', '74.6762'), ('wet', '83.1016')):
            w = self.gap['win_fractions'][e]
            self.assertEqual(pct(w['estimate'], 4), want)
            self.assertEqual((w['unit'], w['accuracy'], w['label']),
                             ('pairwise win fraction', False, 'pairwise win fraction (not an accuracy)'))
        self.assertIn('win_fractions_not_accuracies', self.gap['limitations_keys'])

    def test_the_allocation_is_descriptive_accounting(self):
        a = self.gap['allocation']
        self.assertEqual(a['label'], 'descriptive accounting')
        self.assertEqual((pp(a['u8']['G']['estimate'], 5), pp(a['u8']['R']['estimate'], 5)), ('+1.96875', '+0.03125'))
        for e in ('u8', 'dry', 'wet'):
            self.assertAlmostEqual(a[e]['G']['estimate'] + a[e]['R']['estimate'],
                                   self.gap['contrasts'][f'S minus J/{e}']['estimate'], places=12)
        self.assertIn('allocation_descriptive', self.gap['limitations_keys'])

    def test_decision_changes_are_shares_of_11200(self):
        t = self.gap['transitions']
        self.assertEqual((t['endpoint'], t['decisions'], t['unit']), ('u8', 11200, 'share of all decisions on the task'))
        edges = self.docs['gap_export']['cohorts']['BETA-held8']['edges']
        src = {'J to B': 'J->shared', 'B to S': 'shared->free', 'J to S': 'J->free', 'J to JplusG': 'J->JplusG',
               'JplusG to S': 'JplusG->free'}
        self.assertEqual(set(t['edges']), set(src))
        for name, edge in t['edges'].items():
            counts = edges[src[name]]
            for share, count in bw.EDGE_SHARES:
                self.assertIsInstance(edge[share], float)
                self.assertEqual(edge[share], counts[count] / 11200, name)
            self.assertAlmostEqual(sum(edge[k] for k in ('wrong_to_right', 'right_to_wrong', 'unchanged_right',
                                                         'wrong_both')), 1.0, places=12)
            self.assertAlmostEqual(edge['wrong_to_right'] - edge['right_to_wrong'],
                                   self.gap['contrasts'][edge['net_equals']]['estimate'], places=12)
        # Interpretation review: J->B rescues 19 and harms 15; B->S 448 and 228; J->S net 224/11,200 = 2%.
        self.assertEqual((t['edges']['J to B']['wrong_to_right'] * 11200, t['edges']['J to B']['right_to_wrong'] * 11200),
                         (19.0, 15.0))
        self.assertEqual(pct(t['edges']['B to S']['wrong_to_right']), '4.00')
        # No raw count anywhere in the transitions, and no Wearable-102 edge.
        self.assertFalse([v for e in t['edges'].values() for v in e.values() if isinstance(v, int)])
        self.assertNotIn('dry', t)
        self.assertFalse({'rescue', 'harm', 'stable_correct', 'stable_wrong', 'prediction_change'} & set(keys(self.blocks)))

    def test_the_reference_check_is_counts_only(self):
        rc = self.gap['reference_check']
        self.assertEqual((rc['BETA']['candidates'], rc['BETA']['at_or_below_threshold'], rc['BETA']['above_threshold']),
                         (40, 8, 32))
        self.assertEqual((rc['Wearable-102']['candidates'], rc['Wearable-102']['at_or_below_threshold']), (12, 0))
        self.assertEqual(rc['threshold'], 1e-10)
        qc = self.docs['gap_reference_qc']['sources']['BETA']
        named = qc['near_orthogonal_frequencies_hz']
        self.assertEqual(len(named), 8)                                    # the source names them ...
        text = json.dumps(self.blocks)
        self.assertNotIn('Hz', text)                                        # ... the blocks never do
        self.assertNotIn(json.dumps(named), text)
        self.assertFalse([k for k in keys(self.blocks) if 'frequenc' in k.lower() and k != 'frequency_rotations'])
        for v in (qc['crossblock_fro_min'], qc['crossblock_fro_max'], qc['max_joint_to_union_residual']):
            self.assertNotIn(v, list(floats(self.blocks)))

    def test_no_per_frequency_value_anywhere(self):
        for name, b in self.blocks.items():
            for k in keys(b):
                self.assertFalse(re.search(r'frequencies|_hz$|per_freq', k), (name, k))
            for s in strings(b):
                self.assertIsNone(re.search(r'\d\s*Hz\b', s), (name, s))
        # BETA's 40 frequencies and Wearable-102's 12 never appear as a list.
        for proto in ('gap_protocol', 'decay_protocol', 'rise_protocol'):
            for ds in self.docs[proto]['datasets'].values():
                self.assertNotIn(json.dumps(ds['frequencies']), json.dumps(self.blocks))

    # ------------------------------------------------------------------ card 13
    def test_fixed_decay_figures(self):
        """Handoff table (accepted by the interpretation review): flat, decay, decay - flat [paired 95%]."""
        want = {'H3/u8': ('82.9018', '79.9107', ('−2.9911', '−3.7679', '−2.2857')),
                'H3/seen_ba': ('69.5268', '63.8080', ('−5.7187', '−6.6362', '−4.8393')),
                'H3/dry': ('66.0376', '64.7549', ('−1.2827', '−2.0507', '−0.5392')),
                'H3/wet': ('82.7696', '81.4134', ('−1.3562', '−1.9118', '−0.7925')),
                'FBCCA/u8': ('85.0089', '90.2143', ('+5.2054', '+4.0804', '+6.3839')),
                'FBCCA/seen_ba': ('73.3638', '80.7634', ('+7.3996', '+6.0669', '+8.7902'))}
        for key, (flat, decay, row) in want.items():
            con, e = key.split('/')
            self.assertEqual((pct(self.decay['levels'][f'{con}-FLAT/{e}']['estimate'], 4),
                              pct(self.decay['levels'][f'{con}-DECAY/{e}']['estimate'], 4)), (flat, decay), key)
            self.assertEqual(crow(self.decay['contrasts'][f'{con}-DECAY minus {con}-FLAT/{e}']), row, key)
        self.assertTrue(all(lv['interval'] is None and lv['interval_level'] is None
                            for lv in self.decay['levels'].values()))
        self.assertEqual([c['role'] for c in self.decay['contrasts'].values()],
                         ['primary', 'secondary', 'secondary', 'secondary', 'secondary', 'secondary'])

    def test_the_seen_decrement_prints_minus_5_72(self):
        """The plan and the handoff print -5.7188 (the exact count, -2562/44800); the double renders -5.7187 at four
        places and -5.72 at the site's two."""
        c = self.decay['contrasts']['H3-DECAY minus H3-FLAT/seen_ba']
        self.assertEqual(c['estimate'], -0.05718749999999998)
        self.assertEqual((pp(c['estimate']), pp(c['estimate'], 4)), ('−5.72', '−5.7187'))
        t = self.docs['decay_export']['cohorts']['BETA-seen32']['transitions']
        self.assertEqual(t['rescue'] - t['harm'], -2562)

    def test_the_equivalence_test(self):
        eq = self.decay['equivalence']
        self.assertEqual((eq['contrast'], eq['interval_level'], eq['margin'], eq['met'], eq['interval_beyond_margin']),
                         ('H3-DECAY minus H3-FLAT/u8', 0.9, 0.005, False, True))
        self.assertEqual(tuple(pp(v, 4) for v in eq['interval']), ('−3.6429', '−2.3839'))
        self.assertEqual(js_fixed(eq['margin'] * 100, 1), '0.5')
        self.assertIs(self.decay['contrasts'][eq['contrast']]['flags']['equivalence_met'], False)
        self.assertEqual(self.decay['contrast_limitations'][eq['contrast']],
                         ['equivalence_not_met', 'equivalence_approximate'])

    def test_one_rule_on_harmonics_and_sub_bands(self):
        d = self.decay['design']
        self.assertEqual((d['rule']['weight'], d['rule']['exponent'], d['rule']['offset']), ('n^-1.25 + 0.25', 1.25, 0.25))
        self.assertEqual((d['constructions']['H3']['terms'], d['constructions']['FBCCA']['terms'],
                          d['constructions']['FBCCA']['harmonics_per_band']), (3, 7, 5))
        self.assertIs(d['harmonic_and_sub_band_weights_are_different_operations'], True)
        self.assertIs(d['each_contrast_changes_weights_within_one_construction'], True)
        self.assertEqual(self.decay['display_names']['FBCCA-DECAY'], 'filter-bank CCA (seven sub-bands)')
        self.assertIn('practical B/D FBCCA-M3-N7-H5 2 s 8 electrodes held8',
                      self.decay['levels']['FBCCA-DECAY/u8']['same_estimate_as'])
        self.assertEqual(pct(self.decay['levels']['FBCCA-DECAY/u8']['estimate'], 4), '90.2143')

    def test_the_ratio_table_is_not_published(self):
        ratio = self.docs['decay_export']['retrospective_gap_ratio']
        published = set(floats(self.blocks))
        shown_elsewhere = {v for v in floats(ratio) if v in published} - {0.0}     # 0.0: a draw fraction, and J to B dry
        # The only ratio-table doubles in a block are the harmonic gap's own G gaps, published from card 12's export.
        g = {self.gap['gap'][f'G true minus mean distractor/{e}']['estimate'] for e in ('u8', 'dry', 'wet')}
        self.assertEqual(shown_elsewhere, g)
        self.assertFalse((set(floats(ratio)) - {0.0}) & set(floats(self.decay)))
        self.assertFalse([k for k in keys(self.blocks) if 'ratio' in k.lower() and 'operations' not in k])

    # ------------------------------------------------------------------ card 14
    def test_rising_weight_figures(self):
        """Handoff tables (accepted by the interpretation review)."""
        want = {'u8': (('82.9018', '83.7589', '83.7143'), ('+0.8571', '+0.2946', '+1.4464'),
                       ('+0.8125', '+0.2232', '+1.4286'), ('−0.0446', '−0.1161', '+0.0179')),
                'seen_ba': (('69.5268', '70.0156', '69.9621'), ('+0.4888', '−0.2165', '+1.2121'),
                            ('+0.4353', '−0.3170', '+1.2098'), ('−0.0536', '−0.1562', '+0.0491')),
                'dry': (('66.0376', '64.8938', '64.8529'), ('−1.1438', '−1.8627', '−0.4575'),
                        ('−1.1846', '−1.9118', '−0.4820'), ('−0.0408', '−0.1225', '+0.0490')),
                'wet': (('82.7696', '82.3366', '82.3039'), ('−0.4330', '−1.0294', '+0.1552'),
                        ('−0.4657', '−1.0868', '+0.1471'), ('−0.0327', '−0.1062', '+0.0327'))}
        for e, (lv, lit, ex_flat, ex_lit) in want.items():
            self.assertEqual(tuple(pct(self.rise['levels'][f'{a}/{e}']['estimate'], 4) for a in bw.RISE_ARMS), lv, e)
            self.assertEqual(crow(self.rise['contrasts'][f'literal_rise minus flat/{e}']), lit, e)
            self.assertEqual(crow(self.rise['contrasts'][f'exact_rise minus flat/{e}']), ex_flat, e)
            self.assertEqual(crow(self.rise['contrasts'][f'exact_rise minus literal_rise/{e}']), ex_lit, e)
        self.assertEqual((pct(self.rise['levels']['flat/u8']['estimate']),
                          pct(self.rise['levels']['literal_rise/u8']['estimate'])), ('82.90', '83.76'))   # plan lead
        self.assertEqual((pct(self.rise['levels']['flat/dry']['estimate']),
                          pct(self.rise['levels']['literal_rise/dry']['estimate'])), ('66.04', '64.89'))

    def test_the_single_prespecified_criterion(self):
        cr = self.rise['criterion']
        self.assertEqual((cr['contrast'], cr['met'], cr['prespecified']), ('literal_rise minus flat/u8', True, True))
        roles = {cid: c['role'] for cid, c in self.rise['contrasts'].items()}
        self.assertEqual([cid for cid, r in roles.items() if r == 'primary'], ['literal_rise minus flat/u8'])
        self.assertEqual({cid for cid, r in roles.items() if r == 'rounding_check'},
                         {f'exact_rise minus {x}/{e}' for x in ('flat', 'literal_rise') for e in ENDPOINTS})
        self.assertIn('passbands_wider_than_nominal', self.rise['limitations_keys'])

    def test_the_weights(self):
        w = self.rise['design']['weights']
        self.assertEqual((w['flat'], w['literal_rise']), ([1.0, 1.0, 1.0], [1.0, 1.5, 1.9]))
        d = [n ** -1.25 + 0.25 for n in (1, 2, 3)]
        for i, v in enumerate(w['exact_rise']):
            self.assertAlmostEqual(v, sum(d[:i + 1]) / d[0], places=12)
        self.assertEqual(w['exact_rise'], self.docs['rise_protocol']['weights']['rounding_sensitivity_exact'])

    # ------------------------------------------------------------------ one set of scores
    def test_one_set_of_scores_under_one_name(self):
        rel = self.docs['released']['studies']
        self.assertEqual(self.gap['levels']['J/u8']['estimate'], rel['cca_diagnostics']['levels']['CCA-RAW/u8']['estimate'])
        for s in ('dry', 'wet'):
            self.assertEqual(self.gap['levels'][f'J/{s}']['estimate'],
                             rel['wearable_transfer']['levels'][f'CCA-RAW/{s}']['estimate'])
        for e in ('u8', 'dry', 'wet'):
            v = self.gap['levels'][f'S/{e}']['estimate']
            self.assertEqual((self.decay['levels'][f'H3-FLAT/{e}']['estimate'],
                              self.rise['levels'][f'flat/{e}']['estimate']), (v, v), e)
        self.assertEqual(self.decay['levels']['H3-FLAT/seen_ba']['estimate'], self.rise['levels']['flat/seen_ba']['estimate'])
        names = {self.gap['display_names']['S'], self.decay['display_names']['H3-FLAT'], self.rise['display_names']['flat']}
        self.assertEqual(names, {'harmonic sum (no training)'})
        self.assertEqual(dict(bw.NAME_KEY)['harmonic sum (no training)'].count('one set of scores'), 1)
        coh = self.docs['coherence_export']['arms']
        self.assertEqual(coh['CCA-RAW']['seen32']['mean'], rel['cca_diagnostics']['levels']['CCA-RAW/seen_ba']['estimate'])
        self.assertEqual(coh['RAW-HARM-SUM']['seen32']['mean'], self.decay['levels']['H3-FLAT/seen_ba']['estimate'])

    def test_the_endpoints(self):
        for name, b in self.blocks.items():
            for e, ep in b['design']['endpoints'].items():
                self.assertEqual((ep['candidate_count'], ep['chance']), (bw.CANDIDATES[e], 1 / bw.CANDIDATES[e]))
                self.assertEqual(ep['decisions'], {'u8': 11200, 'seen_ba': 44800, 'dry': 12240, 'wet': 12240}[e])
            for lv in b['levels'].values():
                self.assertIn(lv['people'], (70, 102))
        self.assertEqual(set(self.gap['design']['endpoints']), {'u8', 'dry', 'wet'})
        self.assertEqual(set(self.decay['design']['endpoints']), set(ENDPOINTS))
        self.assertEqual(set(self.rise['design']['endpoints']), set(ENDPOINTS))

    # ------------------------------------------------------------------ the boundary
    def test_no_private_or_refused_material(self):
        validate_public(self.blocks)
        text = json.dumps(self.blocks, ensure_ascii=False)
        for word in ('/Users', '/home', '/Volumes', '/mnt', 'trx', 'TRX', 'Gal4', 'BCI_Arena', 'twu', 'pending',
                     'private_root', '"pid"', '55%', '55percent', 'huggingface', 'Twu31',
                     'release_review_pending', '"status"', '.npy', '.npz', '.py', '.md', 'research/', 'Hz',
                     'decision_route3', 'ratio_pp', 'gain_B_to_S', 'point_bet', 'commenter', 'Chen', '2015'):
            self.assertNotIn(word, text, word)
        self.assertIsNone(bc.REFUSED_TEXT.search(text))                       # blocks_cca's rule: paths, hosts, the thread
        self.assertFalse([v for v in floats(self.blocks) if abs(v - DROPPED) < 1e-12 or abs(v - 100 * DROPPED) < 1e-9])
        self.assertIsNone(re.search(r'(?<![./\w-])v\d+\b', text))

    def test_the_released_assemblers_boundary_rules_hold(self):
        """The 2026-10-20 assembler's key and text rules, applied to these blocks as its $.studies."""
        released_assembler.scrub_check({'studies': self.blocks})
        for k in keys(self.blocks):
            self.assertFalse(re.search(r'fifty|05{2}|prediction', k, re.IGNORECASE), k)
        for s in strings(self.blocks):
            if re.fullmatch(r'[0-9a-f]{64}', s):
                continue
            for rule in (bc.REFUSED_TEXT, released_assembler.SOURCE_IDS, released_assembler.VERSION_LABEL,
                         released_assembler.MONTH_LABEL, released_assembler.UPDATE_MARKER,
                         released_assembler.CONFIDENCE_TOKEN, released_assembler.LOCAL_ROOTS):
                self.assertIsNone(rule.search(s), (rule.pattern[:30], s))

    def test_no_thread_prediction_on_the_new_cards(self):
        """D23: the new cards state only their prespecified criteria."""
        for k in keys(self.blocks):
            self.assertFalse(re.search(r'bet$|^bet|forecast|point_inside|positive_point|comment|thread', k), k)
        for s in strings(self.blocks):
            self.assertIsNone(re.search(r'\bbet\b|forecast|comment|thread|predicted', s, re.IGNORECASE), s)
        self.assertIn('point_inside_margin', self.docs['decay_export']['cohorts']['BETA-held8'])   # in the source
        self.assertIn('primary_positive_point', self.docs['rise_release_approval'])

    def test_every_limitation_and_not_run_item_resolves_in_its_pinned_record(self):
        for name, b in self.blocks.items():
            self.assertEqual(b['limitations_keys'], list(bw.LIMITATION_SOURCES[name]))
            for key, (doc, ptr, phrase) in bw.LIMITATION_SOURCES[name].items():
                here = self.docs[doc] if ptr == '' else walk(self.docs[doc], ptr)
                self.assertIn(phrase, here, key)
                self.assertTrue(re.fullmatch(r'[a-z0-9_]+', key), key)
            self.assertEqual([x['item'] for x in b['not_run']], list(bw.NOT_RUN_SOURCES[name]))
            for item, (doc, ptr, phrase) in bw.NOT_RUN_SOURCES[name].items():
                here = self.docs[doc] if ptr == '' else walk(self.docs[doc], ptr)
                self.assertIn(phrase, here, item)
            for cid, ks in b['contrast_limitations'].items():
                self.assertIn(cid, b['contrasts'])
                self.assertLessEqual(set(ks), set(b['limitations_keys']))

    def test_release_status_comes_from_the_approvals(self):
        for name, b in self.blocks.items():
            ap = self.docs[bw.APPROVAL_OF[name]]
            self.assertEqual(ap['status'], 'PASS')
            self.assertEqual(b['approval_sha256'], self.digests[bw.APPROVAL_OF[name]])
        # The execution terminals say "release_review_pending"; nothing reads them.
        self.assertFalse([p for p in bw.PINS.values() if 'Execution Terminal' in p['path']])

    def test_pins_are_the_files_on_disk(self):
        for name, ref in bw.PINS.items():
            self.assertEqual(hashlib.sha256(bw.location(ref['path']).read_bytes()).hexdigest(), ref['sha256'], name)
        self.assertTrue(bw.PINS['gap_export']['sha256'].startswith('32d9337e'))
        self.assertTrue(bw.PINS['decay_export']['sha256'].startswith('c33ef508'))
        self.assertTrue(bw.PINS['rise_export']['sha256'].startswith('13eb89ea'))
        for ref in bw.PINS.values():
            self.assertFalse(Path(ref['path']).is_absolute())

    def test_declared_edits_and_handoff_context_are_kept_for_the_manifest(self):
        self.assertEqual(set(bw.DECLARED_EDITS), set(bw.STUDIES))
        self.assertTrue(all(bw.DECLARED_EDITS[s] for s in bw.STUDIES))
        queue = json.loads((PROJECT / QUEUE).read_text())['rows']
        for name, h in bw.HANDOFF_CONTEXT.items():
            self.assertEqual(queue[h['queue_row']]['source_sha256'], h['bound_sha256'], name)
            self.assertNotIn(h['bound_sha256'], json.dumps(self.blocks[name]))
        for line in (x for v in bw.DECLARED_EDITS.values() for x in v):
            self.assertIsNone(re.search(r'/(?:mnt|home|Users)/|trx|5{2}', line), line)
        self.assertTrue(all(isinstance(x, str) and x.endswith('.') for x in bw.NOT_PUBLISHED))

    def test_withheld_values_never_reach_a_block(self):
        held = bw.withheld_values(self.docs)
        self.assertGreater(len(held), 50)
        self.assertFalse(held & set(floats(self.blocks)))


@unittest.skipUnless(bw.inputs_available(), 'the pinned research folders are local-only; see inputs_available()')
class WeightBlocksRefuse(unittest.TestCase):
    """Each check fires on its own: the pinned records are loaded once, edited in memory, and the blocks rebuilt."""

    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = bw.load()

    def setUp(self):
        self.d, self.h = copy.deepcopy(self.docs), dict(self.digests)

    def build(self):
        blocks = {'harmonic_gap': bw.gap_block(self.d, self.h), 'fixed_decay': bw.decay_block(self.d, self.h),
                  'rising_weights': bw.rise_block(self.d, self.h)}
        bw.same_scores(blocks, self.d)
        return blocks

    def refused(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.build()

    def test_the_unedited_records_build(self):
        self.build()

    def test_bytes_that_are_not_the_pinned_file_are_refused(self):
        pins = copy.deepcopy(bw.PINS)
        pins['gap_export']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            bw.build_blocks(pins)

    def test_pins_of_another_shape_are_refused(self):
        pins = copy.deepcopy(bw.PINS)
        del pins['practical_bd_export']
        with self.assertRaisesRegex(ValueError, 'pins: expected'):
            bw.build_blocks(pins)

    def test_an_export_its_approval_did_not_bind_is_refused(self):
        for name in ('gap_export', 'decay_export', 'rise_export'):
            self.h = dict(self.digests)
            self.h[name] = 'f' * 64
            self.refused('binds')

    def test_a_failed_approval_is_refused(self):
        self.d['decay_release_approval']['status'] = 'HOLD'
        self.refused('fixed decay: the release approval')

    def test_the_gap_export_must_equal_the_numerical_review(self):
        m = self.d['gap_export']['cohorts']['Wearable-wet']['metrics']['accuracy_S_free_minus_S_shared']
        m['ci_family99_444'][0] += 1e-9
        self.refused('differs from the review')

    def test_the_rising_export_must_equal_the_audit(self):
        self.d['rise_export']['cohorts']['Wearable-dry']['arm_levels']['flat']['estimate'] += 1e-9
        self.refused('differs from the audit')

    def test_a_contrast_must_be_the_difference_of_its_levels(self):
        self.d['decay_export']['cohorts']['BETA-seen32']['decay_minus_flat'] += 1e-6
        self.refused('not the difference of its levels')

    def test_a_family_flag_must_follow_the_family_interval(self):
        m = self.d['gap_export']['cohorts']['Wearable-dry']['metrics']['accuracy_S_free_minus_S_shared']
        m['primary_positive'] = True
        self.d['gap_numerical_review']['primary']['Wearable-dry']['accuracy_S_free_minus_S_shared'] = {
            k: m[k] for k in ('estimate', 'ci95', 'ci_family99_444')}
        self.refused('primary_positive')

    def test_the_family_must_be_the_protocols(self):
        self.d['gap_protocol']['statistics']['primary_family'].pop()
        self.refused('the family differs from the protocol')

    def test_a_new_metric_is_refused(self):
        self.d['gap_export']['cohorts']['BETA-held8']['metrics']['mean_true_X'] = {'estimate': 0.1, 'ci95': [0.0, 0.2]}
        self.refused('the metric set changed')

    def test_the_edges_must_cover_the_decisions(self):
        self.d['gap_export']['cohorts']['BETA-held8']['edges']['J->free']['stable_wrong'] += 1
        self.refused('do not cover the decisions')

    def test_net_edge_change_must_equal_the_contrast(self):
        e = self.d['gap_export']['cohorts']['BETA-held8']['edges']['shared->free']
        e['rescue'] += 1
        e['stable_wrong'] -= 1
        self.refused('the net change is not')

    def test_the_reference_counts_must_add_up(self):
        self.d['gap_reference_qc']['sources']['BETA']['near_orthogonal_count'] = 9
        self.refused('reference check BETA: counts')

    def test_the_equivalence_flag_must_follow_the_interval(self):
        self.d['decay_export']['cohorts']['BETA-held8']['equivalent_90ci'] = True
        self.refused('the equivalence flag is not the interval')

    def test_the_criterion_flag_must_follow_the_interval(self):
        self.d['rise_export']['cohorts']['BETA-held8']['supports_primary_benefit'] = False
        self.d['rise_audit_receipt']['supports_primary_benefit'] = False
        self.refused('the criterion flags are not the interval')

    def test_the_exact_profile_must_be_the_protocol_formula(self):
        self.d['rise_protocol']['weights']['rounding_sensitivity_exact'][1] = 1.5364
        self.refused('protocol formula')

    def test_the_bootstrap_seeds_are_the_frozen_ones(self):
        self.d['decay_protocol']['statistics']['seeds']['Wearable'] = 2026102201
        self.refused('fixed_decay: bootstrap seeds')

    def test_a_reused_score_must_be_the_same_double(self):
        self.d['released']['studies']['wearable_transfer']['levels']['CCA-RAW/wet']['estimate'] += 1e-15
        self.refused('not the same score')

    def test_the_filter_bank_arm_must_be_card_11s(self):
        self.d['practical_bd_export']['arms']['w500-c8/FBCCA-M3-N7-H5']['held8']['mean'] += 1e-12
        self.refused('FBCCA-M3-N7-H5 2 s 8 electrodes held8: not the same score')

    def test_a_limitation_its_record_does_not_state_is_refused(self):
        self.d['rise_protocol']['limits'][2] = 'Passbands are as nominal.'
        self.refused('does not state')

    def test_a_withheld_value_in_a_block_is_refused(self):
        ratio = self.docs['decay_export']['retrospective_gap_ratio']['cohorts']['BETA-held8']['ratio_pp_per_gap']
        real = bw.decay_block

        def leaky(docs, digests):
            block = real(docs, digests)
            block['design']['scale'] = ratio
            return block
        with mock.patch.object(bw, 'decay_block', leaky):
            with self.assertRaisesRegex(ValueError, 'withheld value'):
                bw.build_blocks()

    def test_the_scrub_refuses_what_must_not_be_published(self):
        for bad in ({'near_orthogonal_frequencies_hz': [8.0]}, {'frequencies': []}, {'note': 'at 10 Hz'},
                    {'x': [8.0, 9.0, 10.0, 11.0]}, {'point_bet': 1}, {'forecast': True}, {'rescue': 19},
                    {'prediction_change': 3}, {'ratio_pp_per_gap': 1.0}, {'retrospective_gap_ratio': {}},
                    {'note': '/mnt/bigdata/x'}, {'note': 'run on trx50'}, {'x': DROPPED}, {'note': 'the 55% bet'},
                    {'note': 'the v4 rule'}, {'note': 'the best weights'}, {'note': 'updated weights'},
                    {'note': 'in October'}, {'note': 'scores.npy'}, {'note': 'the commenter asked'},
                    {'status': 'PASS'}, {'rows': [0, 361, 722]}, {'window_seconds': 2}):
            with self.assertRaises(ValueError, msg=repr(bad)):
                bw.scrub_check(bad)
        bw.scrub_check({'BETA': {'frequency_rotations': 5}, 'note': 'harmonic sum (no training)', 'x': 0.0617,
                        'r': [0, 2], 'w': [1.0, 1.5, 1.9], 'h': 'c20938849706faf5b73326e8bde3f09f510e085b317039f27ad49f3078689904'})


if __name__ == '__main__':
    unittest.main()
