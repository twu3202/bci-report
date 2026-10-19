"""B2, the phase blocks (cards 3 and 4): every value against its pinned source, to the last bit, and the R5 rules.

The sources are re-read here with their own pointer walk, not through the builder's helpers; the plan's name key and
source pins, and the R5 corrections (phase-wording-review.md, section 6), are read from those files themselves.
"""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public               # noqa: E402
from ssvep_followups import blocks_phase as bp             # noqa: E402

PLAN = 'research/site_release_plan_20261019/Release Layout Plan v2.md'
POST = 'https://huggingface.co/posts/Twu31/109502481720473'
LOCAL_ROOT = re.compile(r'/(?:Volumes|Users|home|mnt)/')
CELLS = ('FS-REF', 'FS-NUM', 'FS-ID', 'MATCH-REF', 'MATCH-NUM', 'MATCH-ID')
COMPARATORS = ('L0c-FS-REF', 'L0c-FS-NUM', 'L0c-FS-ID', 'L0c-MATCH-REF', 'L0c-MATCH-NUM', 'L0c-MATCH-ID',
               'L0-FS-REF', 'L0-FS-NUM', 'CCA')
ARM_CELL = {'A': 'COMMON-125MS', 'B': 'COMMON-ONE-PERIOD', 'C': 'L0c-FS-REFc-0', 'M': 'L0-FS-REF'}
DROPPED = 11 / 20          # the reference value the declared edits drop, never spelled as digits


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw(name):
    return bp.location(bp.PINS[name]['path']).read_bytes()


def source(name):
    data = raw(name)
    return data.decode() if bp.PINS[name].get('text') else json.loads(data)


def walk(doc, ptr):
    """An independent RFC 6901 walk."""
    cur = doc
    for t in ptr.split('/')[1:]:
        t = t.replace('~1', '/').replace('~0', '~')
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


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


def keys(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k, trail
            yield from keys(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for v in value:
            yield from keys(v, trail)


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield value


# The site's formatters (site/src/data/entities.ts formatFig), in Python; `node_format` runs the JavaScript itself.
def pct2(v):
    return f'{100 * v:.2f}%'


def pp2(v):
    return f'{"" if v == 0 else "+" if v > 0 else "−"}{abs(v * 100):.2f} pp'


def node_format(values, fmt):
    node = shutil.which('node')
    if not node:
        return None
    js = {'pct2': 'v => `${(v * 100).toFixed(2)}%`',
          'pp2': 'v => `${v === 0 ? "" : v > 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(2)} pp`',
          'pct0': 'v => `${(v * 100).toFixed(0)}%`'}[fmt]
    out = subprocess.run([node, '-e', f'const f = {js}; console.log(JSON.stringify({json.dumps(values)}.map(f)))'],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@unittest.skipUnless(bp.inputs_available(), 'the pinned research inputs are local-only; see blocks_phase.PINS')
class PhaseBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bp.build_blocks()
        cls.jit, cls.ramp = cls.blocks['phase_jitter'], cls.blocks['phase_ramp']
        cls.src = {name: source(name) for name in bp.PINS}
        cls.plan = bp.location(PLAN).read_text()
        cls.review = cls.src['wording_review']

    # ------------------------------------------------------------------ pins
    def test_every_input_is_its_pinned_bytes(self):
        for name, ref in bp.PINS.items():
            with self.subTest(name=name):
                self.assertEqual(digest(raw(name)), ref['sha256'])

    def test_the_blocks_name_the_plans_source_pins(self):
        m = re.search(r'jitter `([0-9a-f]+)…` \(aggregate `([0-9a-f]+)…` by hash\), '
                      r'ramp `([0-9a-f]+)…` \+ audit `([0-9a-f]+)…`', self.plan)
        self.assertIsNotNone(m)
        jitter, score, ramp, audit = m.groups()
        self.assertTrue(self.jit['source_sha256'].startswith(jitter))
        self.assertTrue(self.jit['canonical_score_sha256'].startswith(score))
        self.assertTrue(self.ramp['source_sha256'].startswith(ramp))
        self.assertTrue(self.ramp['audit_sha256'].startswith(audit))
        for study, block in self.blocks.items():
            with self.subTest(study=study):
                self.assertEqual(block['source_sha256'], digest(raw(bp.SOURCE_OF[study])))
                self.assertEqual(block['review_sha256'], digest(raw(bp.REVIEW_OF[study])))
                self.assertEqual(block['provenance_review_sha256'], digest(raw(bp.PROVENANCE_OF[study])))
                self.assertEqual(block['wording_review_sha256'], digest(raw('wording_review')))

    def test_the_wording_review_checked_these_very_bytes(self):
        """R5 section 0 lists each file's SHA-256; every one it names for these studies is the pinned one."""
        table = dict(re.findall(r'^\| `(?:JIT|RAMP)/([^`]+)` \| `([0-9a-f]{64})` \|', self.review, re.M))
        expected = {
            'exports/phase-jitter-v1.json': 'jitter_export', 'exports/phase-jitter-aggregate.json': 'jitter_score',
            'protocol.json': None, 'review/final-interpretation-review.json': 'jitter_interpretation',
            'review/final-provenance-review.json': 'jitter_provenance', 'state/release-status.json': 'jitter_release',
            'review/completed-run/canary-gate.json': 'jitter_canary', 'review/final-trx/score/main.private.json':
            'ramp_score', 'review/final-trx/audit/aggregate.json': 'ramp_audit',
            'review/release-interpretation-review.json': 'ramp_interpretation',
            'review/release-provenance-review.json': 'ramp_provenance', 'review/release-status.json': 'ramp_release',
            'review/canary-gate.json': 'ramp_canary',
        }
        for file, name in expected.items():
            if name:
                with self.subTest(file=file):
                    self.assertEqual(table[file], bp.PINS[name]['sha256'])
        for name in ('jitter_protocol', 'ramp_protocol'):
            self.assertIn(f'`{bp.PINS[name]["sha256"]}`', self.review)
        self.assertIn('**Confirmed, with seven required corrections', self.review)

    def test_each_review_binds_its_source(self):
        s = self.src
        self.assertEqual(s['jitter_interpretation']['public_export_sha256'], digest(raw('jitter_export')))
        self.assertEqual(s['jitter_provenance']['numerical_score_sha256'], digest(raw('jitter_score')))
        self.assertEqual(s['jitter_export']['provenance']['canonical_score_sha256'], digest(raw('jitter_score')))
        self.assertEqual(s['ramp_interpretation']['inputs']['score']['sha256'], digest(raw('ramp_score')))
        self.assertEqual(s['ramp_audit']['numerical_score_sha256'], digest(raw('ramp_score')))
        self.assertEqual(s['ramp_release']['score_sha256'], digest(raw('ramp_score')))
        self.assertEqual(s['ramp_provenance']['final_receipts_sha256']['audit/aggregate.json'],
                         digest(raw('ramp_audit')))

    # ------------------------------------------------------------------ values, to full precision
    def test_jitter_levels_are_the_exports_and_the_canonical_score(self):
        levels, seen = self.jit['levels'], set()
        for arm in self.src['jitter_export']['arms']:
            for e, m in arm['metrics'].items():
                lid = f'{ARM_CELL[arm["id"]]}/{e}'
                seen.add(lid)
                got = levels[lid]
                with self.subTest(level=lid):
                    self.assertEqual(got['estimate'], m['point'])
                    self.assertEqual(got['interval'], [m['lo'], m['hi']])
                    self.assertEqual((got['people'], got['seeds'], got['unit']), (m['people'], m['seeds'], 'proportion'))
                    canon = self.src['jitter_score']['levels'][f'{arm["id"]}/{e}']
                    self.assertEqual((canon['point'], canon['lo'], canon['hi']), (m['point'], m['lo'], m['hi']))
        self.assertEqual(set(levels), seen)
        self.assertEqual(len(levels), 8)

    def test_jitter_has_one_primary_contrast_and_five_secondary(self):
        src = self.src['jitter_export']['contrasts']
        got = self.jit['contrasts']
        self.assertEqual(list(got), ['P1', 'S1', 'S2', 'S3', 'S4', 'S5'])
        self.assertEqual([c['role'] for c in got.values()], ['primary'] + ['secondary'] * 5)
        for cid, c in src.items():
            with self.subTest(contrast=cid):
                g = got[cid]
                self.assertEqual(g['estimate'], c['point'])
                self.assertEqual(g['interval'], [c['lo'], c['hi']])
                self.assertEqual((g['left'], g['right']),
                                 (f'{ARM_CELL[c["left"]]}/{c["metric"]}', f'{ARM_CELL[c["right"]]}/{c["metric"]}'))
                self.assertEqual(g['flags']['role_as_stated'], c['role'])
                self.assertEqual((g['people'], g['seeds'], g['unit']), (70, 3, 'difference of proportions'))
        self.assertEqual((got['P1']['left'], got['P1']['right']), ('COMMON-125MS/u8', 'L0c-FS-REFc-0/u8'))
        self.assertEqual(got['P1']['flags'], {'role_as_stated': 'single primary', 'positive_primary': False,
                                              'meaningful_primary': False})
        self.assertEqual(src['P1']['role'], 'single primary')

    def test_s2_keeps_its_raw_value(self):
        s2 = self.jit['contrasts']['S2']
        self.assertEqual(s2['estimate'], -0.25875)
        self.assertEqual(s2['estimate'], self.src['jitter_export']['contrasts']['S2']['point'])
        self.assertEqual(pp2(s2['estimate']), '−25.87 pp')          # the handoff's -25.88 is not the site's
        js = node_format([s2['estimate']], 'pp2')
        if js is not None:
            self.assertEqual(js, ['−25.87 pp'])

    def test_ramp_levels_are_the_scores(self):
        score = self.src['ramp_score']['levels']
        got = self.ramp['levels']
        self.assertEqual(list(got), list(score))
        self.assertEqual(len(got), 78)
        for lid, lv in score.items():
            with self.subTest(level=lid):
                self.assertEqual(got[lid]['estimate'], lv['point'])
                self.assertEqual(got[lid]['interval'], [lv['lo'], lv['hi']])
                self.assertEqual(got[lid]['people'], lv['people'])
                self.assertEqual(got[lid]['seeds'], 'no training' if lid.startswith('CCA/') else lv['seeds'])
                self.assertEqual(got[lid]['unit'], 'difference of proportions' if lid.endswith('/cost')
                                 else 'proportion')
        self.assertEqual(score['CCA/u8']['seeds'], 1)       # the source has the 1 that the edit replaces

    def test_ramp_has_six_cells_nine_comparators_and_thirteen_contrasts(self):
        cells = list(dict.fromkeys(lid.split('/')[0] for lid in self.ramp['levels']))
        self.assertEqual(tuple(cells), CELLS + COMPARATORS)
        self.assertEqual([c['cell'] for c in self.ramp['design']['cells']], list(CELLS))
        self.assertEqual(self.ramp['design']['comparators'], list(COMPARATORS))
        src = self.src['ramp_score']['contrasts']
        got = self.ramp['contrasts']
        self.assertEqual(list(got), ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'])
        roles = [c['role'] for c in got.values()]
        self.assertEqual((roles.count('primary'), roles.count('secondary')), (6, 7))
        self.assertTrue(all(got[f'P{i}']['role'] == 'primary' for i in range(1, 7)))
        declared = {c['id']: c for c in self.src['ramp_protocol']['analysis']['contrasts']}
        for cid, c in src.items():
            with self.subTest(contrast=cid):
                g = got[cid]
                self.assertEqual(g['estimate'], c['point'])
                self.assertEqual(g['interval'], [c['lo'], c['hi']])
                self.assertEqual(g['role'], c['role'])
                self.assertEqual(g['role'], declared[cid]['role'])
                self.assertEqual((g['left'], g['right']), (f'{c["left"]}/{c["metric"]}', f'{c["right"]}/{c["metric"]}'))
                self.assertEqual(g['flags'], {k: c[k] for k in ('difference', 'equivalent_within_2pp',
                                                                'noninferiority_to_CCA')})
                self.assertIs(g['flags']['equivalent_within_2pp'], False)
        self.assertEqual([cid for cid, c in got.items() if c['right'] == 'CCA/u8'], ['S7'])
        self.assertIs(got['S7']['flags']['noninferiority_to_CCA'], False)

    def test_the_card_figures_print_from_these_values(self):
        """Every figure of the card 3 and card 4 text as R5 section 5 corrects it, at pct2 and pp2."""
        j, r = self.jit, self.ramp
        jl, jc, rl, rc = j['levels'], j['contrasts'], r['levels'], r['contrasts']
        levels = [
            (jl['COMMON-125MS/u8'], '12.51%', '11.93%', '13.13%'),
            (jl['COMMON-ONE-PERIOD/u8'], '13.13%', '12.61%', '13.68%'),
            (jl['L0c-FS-REFc-0/u8'], '24.97%', '22.60%', '27.44%'),
            (jl['L0c-FS-REFc-0/seen_ba'], '49.24%', None, None),
            (jl['COMMON-125MS/seen_ba'], '15.70%', None, None),
            (jl['COMMON-ONE-PERIOD/seen_ba'], '15.28%', None, None),
            (jl['L0-FS-REF/u8'], '39.00%', None, None),
            (rl['FS-REF/u8'], '30.56%', '27.81%', '33.22%'),
            (rl['L0c-FS-REF/u8'], '8.67%', '7.85%', '9.61%'),
            (rl['L0c-FS-REF/seen_ba'], '47.29%', None, None),
            (rl['FS-REF/seen_ba'], '15.03%', None, None),
            (rl['CCA/u8'], '80.90%', None, None),
            (rl['FS-NUM/u8'], '28.10%', '25.48%', '30.58%'),
            (rl['FS-REF/m8'], '42.86%', '39.29%', '46.25%'),
        ]
        contrasts = [
            (jc['P1'], '−12.46 pp', '−14.84 pp', '−10.25 pp'),
            (rc['P1'], '−8.45 pp', '−10.14 pp', '−6.69 pp'),
            (rc['S5'], '+21.88 pp', '+18.78 pp', '+25.00 pp'),
            (rc['S7'], '−67.97 pp', '−72.07 pp', '−63.76 pp'),
            (rl['FS-REF/cost'], '−12.30 pp', '−13.71 pp', '−10.95 pp'),
        ]
        for rows, fmt in ((levels, pct2), (contrasts, pp2)):
            for row, est, lo, hi in rows:
                with self.subTest(figure=est):
                    self.assertEqual(fmt(row['estimate']), est)
                    if lo is not None:
                        self.assertEqual([fmt(v) for v in row['interval']], [lo, hi])
        js = node_format([row['estimate'] for row, *_ in levels], 'pct2')
        if js is not None:
            self.assertEqual(js, [est for _, est, *_ in levels])
        js = node_format([row['estimate'] for row, *_ in contrasts], 'pp2')
        if js is not None:
            self.assertEqual(js, [est for _, est, *_ in contrasts])
        self.assertEqual(j['design']['model']['parameters'], 526465)
        self.assertIs(j['design']['model']['trained_from_scratch'], True)

    def test_the_matching_head_ended_at_chance_on_both_tasks(self):
        rl = self.ramp['levels']
        for lid, chance in (('MATCH-REF/u8', 1 / 8), ('MATCH-NUM/u8', 1 / 8), ('MATCH-REF/seen_ba', 1 / 32),
                            ('MATCH-NUM/seen_ba', 1 / 32), ('MATCH-ID/seen_ba', 1 / 32)):
            with self.subTest(level=lid):
                lo, hi = rl[lid]['interval']
                self.assertLessEqual(lo, chance)
                self.assertLessEqual(chance, hi)
        lo, hi = rl['FS-ID/seen_ba']['interval']        # close to chance, yet its interval lies above it
        self.assertGreater(lo, 1 / 32)

    def test_reused_levels_are_the_levels_of_their_studies(self):
        ref = walk(self.src['ref_export'], '/results/questions-in-language-ref/descriptive/REF-ssvep-L0/levels')
        ref2 = self.src['ref2_export']['aggregate']['levels']

        def ref_level(lid):
            cell, e = lid.split('/')
            arm = 'CCA' if cell == 'CCA' else cell.split('-')[-1]
            lv = ref[f'{arm} {e}']
            return lv['estimate'], lv['interval_95'], lv['origin']

        for study, block in self.blocks.items():
            for lid, lv in block['levels'].items():
                with self.subTest(study=study, level=lid):
                    if lv['origin'] == 'new':
                        self.assertNotIn(lid, ref2)
                        continue
                    if lv['origin'] == 'reused_ref2':
                        self.assertTrue(lid.startswith('L0c-'))
                        point, iv = ref2[lid]['point'], [ref2[lid]['lo'], ref2[lid]['hi']]
                    else:
                        point, iv, origin = ref_level(lid)
                        self.assertEqual(lv['origin'], {'new': 'reused_ref', 'reused_parent': 'reused_parent'}[origin])
                    self.assertEqual(lv['interval'], iv)
                    self.assertLessEqual(abs(lv['estimate'] - point), 1e-15)
        # The ramp reuses the bits exactly; the jitter export differs from them in the last bit of the point only.
        for lid in COMPARATORS:
            if lid not in ('L0-FS-REF', 'L0-FS-NUM', 'CCA'):
                self.assertEqual(self.ramp['levels'][f'{lid}/seen_ba']['estimate'], ref2[f'{lid}/seen_ba']['point'])
        self.assertEqual({lv['origin'] for lv in self.jit['levels'].values()}, {'new', 'reused_ref2', 'reused_ref'})
        self.assertEqual(self.ramp['levels']['L0-FS-REF/u8']['origin'], 'reused_ref')
        self.assertEqual(self.ramp['levels']['CCA/u8']['origin'], 'reused_parent')

    def test_contrasts_are_differences_of_their_levels(self):
        for study, block in self.blocks.items():
            for cid, c in block['contrasts'].items():
                with self.subTest(study=study, contrast=cid):
                    diff = block['levels'][c['left']]['estimate'] - block['levels'][c['right']]['estimate']
                    self.assertAlmostEqual(diff, c['estimate'], delta=1e-12)

    def test_every_export_code_points_at_its_value(self):
        for study, block in self.blocks.items():
            own = self.src[bp.SOURCE_OF[study]]
            for item, places in block['export_codes'].items():
                got = block['levels'].get(item) or block['contrasts'].get(item)
                for place in places:
                    self.assertTrue(place.startswith('#/'))
                    at = walk(own, place[1:])
                    with self.subTest(study=study, item=item):
                        self.assertEqual((got['estimate'], got['interval']), (at['point'], [at['lo'], at['hi']]))

    def test_units_are_fractions(self):
        for study, block in self.blocks.items():
            for lid, lv in block['levels'].items():
                with self.subTest(study=study, level=lid):
                    lo, hi = lv['interval']
                    if lid.endswith('/cost'):
                        self.assertEqual(lv['unit'], 'difference of proportions')
                        self.assertTrue(-1 <= lo <= lv['estimate'] <= hi <= 1)
                    else:
                        self.assertEqual(lv['unit'], 'proportion')
                        self.assertTrue(0 <= lo <= lv['estimate'] <= hi <= 1)
            for cid, c in block['contrasts'].items():
                with self.subTest(study=study, contrast=cid):
                    self.assertEqual(c['unit'], 'difference of proportions')
                    self.assertTrue(-1 <= c['interval'][0] <= c['estimate'] <= c['interval'][1] <= 1)

    # ------------------------------------------------------------------ undefined endpoints
    def test_id_held_out_is_undefined_with_its_reason(self):
        expected = {f'{c}/{e}' for c in ('FS-ID', 'MATCH-ID', 'L0c-FS-ID', 'L0c-MATCH-ID')
                    for e in ('u8', 'u3', 'cost')}
        got = {u['level'] for u in self.ramp['undefined']}
        self.assertEqual(got, expected)
        self.assertFalse(got & set(self.ramp['levels']))
        self.assertFalse(got & set(self.src['ramp_score']['levels']))
        self.assertEqual({u['reason'] for u in self.ramp['undefined']}, {'cannot_ask_unseen'})
        self.assertEqual(self.ramp['undefined_metrics'], self.src['ramp_score']['undefined_metrics'])
        self.assertIn('no direct held-frequency queries',
                      self.src['ramp_protocol']['inputs']['query_variants']['ID']['scaling'])
        self.assertEqual(self.jit['undefined'], [])     # the jitter study has no question-number arm
        for c in ('FS-ID', 'MATCH-ID'):                 # m8 and nn8 stay defined for ID
            self.assertIn(f'{c}/m8', self.ramp['levels'])
            self.assertIn(f'{c}/nn8', self.ramp['levels'])

    # ------------------------------------------------------------------ declared edits and the R5 rules
    def test_the_dropped_fields_are_in_the_sources_and_not_in_the_blocks(self):
        jx, rs = self.src['jitter_export'], self.src['ramp_score']
        # The sources do carry them, so this test can fail.
        self.assertEqual(jx['one_period_prediction']['reference'], DROPPED)
        self.assertEqual(jx['release_governed_by'], '../state/release-status.json')
        self.assertEqual(set(rs['fifty_five_reference']), {'FS-REF', 'MATCH-REF'})
        self.assertIn('conditional bootstrap uncertainty', rs['interpretation'])
        self.assertIn('pending', rs['status'])
        names = {k for k, _ in keys(self.blocks)}
        for k in ('one_period_prediction', 'release_governed_by', 'fifty_five_reference', 'interpretation',
                  'status_of_score', 'B_prediction_055', 'reference'):
            self.assertNotIn(k, names)

    def test_r5_m7_key_value_and_text_rules(self):
        bad_key = re.compile(r'fifty|05{2}|prediction', re.I)
        self.assertEqual([k for k, _ in keys(self.blocks) if bad_key.search(k)], [])
        self.assertEqual([v for v in numbers(self.blocks) if v == DROPPED or v == 100 * DROPPED], [])
        self.assertEqual([v for v in numbers(self.blocks) if abs(v - DROPPED) < 1e-9 or abs(v - 100 * DROPPED) < 1e-6],
                         [])
        for s in strings(self.blocks):
            if not re.fullmatch(r'[0-9a-f]{64}', s):
                self.assertNotIn('55', s)
        # The scanner refuses each of them, so a later edit cannot slip one in.
        for forged in ({'x': DROPPED}, {'x': 100 * DROPPED}, {'one_period_prediction': {}}, {'fifty': 1},
                       {'note': 'held-out 55% reference'}, {'x': {'thread_bet': {}}},
                       {'checks': {'interpretation': 'x'}}, {'release_governed_by': 'x'}):
            with self.subTest(forged=forged), self.assertRaises(ValueError):
                bp.scan(forged, '$')

    def test_the_bet_is_the_threads_and_lives_in_the_phase_ramp_only(self):
        self.assertEqual(self.ramp['thread_bet'], {'held8_threshold': 0.39, 'source_url': POST})
        self.assertEqual(list(self.ramp['thread_bet']), ['held8_threshold', 'source_url'])
        self.assertNotIn('#', self.ramp['thread_bet']['source_url'])            # no comment anchor
        places = [trail for k, trail in keys(self.blocks) if k == 'thread_bet']
        self.assertEqual(places, ['$.phase_ramp'])
        self.assertNotIn('thread_bet', self.jit)
        self.assertEqual([v for v in numbers(self.blocks) if v == 0.39], [0.39])   # the threshold only
        # Where it comes from: the commitment as the ramp protocol quotes it, and the post the jitter protocol cites.
        self.assertIn('unseen clears 39', self.src['ramp_protocol']['source_evidence']['comment_quote'])
        self.assertEqual(self.src['jitter_protocol']['comment']['url'].split('#')[0], POST)
        self.assertIn(f'`{POST}`', self.review)
        # M5: the threshold prints as the thread states it, 39%, never 39.00%; the FiLM head stayed below it.
        self.assertEqual(f'{100 * self.ramp["thread_bet"]["held8_threshold"]:.0f}%', '39%')
        js = node_format([self.ramp['thread_bet']['held8_threshold']], 'pct0')
        if js is not None:
            self.assertEqual(js, ['39%'])
        self.assertLess(self.ramp['levels']['FS-REF/u8']['estimate'], self.ramp['thread_bet']['held8_threshold'])
        self.assertLess(self.ramp['levels']['FS-NUM/u8']['estimate'], self.ramp['thread_bet']['held8_threshold'])

    def test_the_interval_method_is_m3_in_both_blocks(self):
        m3 = {'method': 'hierarchical paired bootstrap', 'draws': 2000, 'seed': 20261007, 'level': 0.95,
              'conditional_on': 'fixed person folds and three training seeds; five fixed rotations averaged first'}
        for study, block in self.blocks.items():
            with self.subTest(study=study):
                self.assertEqual(block['interval_method'], m3)
        section = self.review.split('**M3.', 1)[1].split('**M4.', 1)[0]
        self.assertIn('method: "hierarchical paired bootstrap", draws: 2000, seed: 20261007, level: 0.95, '
                      'conditional_on: "fixed person folds and three training seeds; five fixed rotations averaged '
                      'first"', section)
        for name, ptr in (('jitter_protocol', '/statistics/bootstrap'), ('ramp_protocol', '/analysis/bootstrap')):
            boot = walk(self.src[name], ptr)
            self.assertEqual((boot['replicates'], boot['seed'], boot['percentiles']), (2000, 20261007, [2.5, 97.5]))
            self.assertIn('Conditional on the fixed source folds and three training seeds', boot['scope'])

    def test_r5_kept_fields_are_verbatim(self):
        jx, rs = self.src['jitter_export'], self.src['ramp_score']
        self.assertEqual(self.jit['caveats'], jx['caveats'])
        self.assertEqual(len(self.jit['caveats']), 7)
        self.assertEqual(self.jit['intervals'], jx['intervals'])
        self.assertEqual(self.ramp['multiplicity'], rs['multiplicity'])
        self.assertEqual(self.ramp['undefined_metrics'], rs['undefined_metrics'])

    def test_limitation_keys_cite_sentences_that_say_them(self):
        for study, block in self.blocks.items():
            self.assertEqual(block['limitations_keys'], list(bp.LIMITATION_SOURCES[study]))
            for key, (doc, ptr, phrase) in bp.LIMITATION_SOURCES[study].items():
                with self.subTest(study=study, key=key):
                    text = walk(self.src[doc], ptr)
                    self.assertIn(phrase, text)
                    self.assertNotIn('55', text)
        # What R5 asks the blocks to carry as keys (M1, M2, M3, M8, R2, R4 and the ramp `interpretation` clauses).
        for key in ('conditional_intervals', 'no_phase_alone_or_sole_head_diagnosis', 'different_tasks_use_m8',
                    'feature_recipe_confound', 'cca_one_seed_axis_s7_only', 'heads_not_initialisation_matched',
                    'ramp_approximates_time_shift', 'delay_uses_training_label', 'phase_is_label_information'):
            self.assertIn(key, self.ramp['limitations_keys'])
        for key in ('conditional_intervals', 'fixed_range_not_uniform_phase', 'randomized_label_check_limit',
                    'queries_and_test_windows_unchanged', 'one_period_range_uses_training_label',
                    'phase_is_label_information', 'magnitude_head_differs_in_recipe'):
            self.assertIn(key, self.jit['limitations_keys'])
        self.assertIn('conditional bootstrap uncertainty', self.src['ramp_score']['interpretation'])

    def test_no_private_paths_names_versions_or_pending_strings(self):
        text = list(strings(self.blocks))
        self.assertFalse([s for s in text if LOCAL_ROOT.search(s) or re.search(r'trx|gal4|bci_arena', s, re.I)])
        self.assertFalse([s for s in text if 'twu' in s.replace(POST, '').lower()])
        self.assertFalse([s for s in text if 'pending' in s.lower()])
        self.assertFalse([s for s in text if re.search(r'(?<![\w.])v\d+\b', s)])
        self.assertFalse([s for s in text if 'Jev' in s])
        self.assertFalse({k for k, _ in keys(self.blocks)} & {'gpu', 'wall_seconds', 'charged_seconds', 'remote_root',
                                                             'paths', 'handoff_local_path'})
        validate_public(self.blocks)

    # ------------------------------------------------------------------ names, design, checks
    def test_display_names_follow_the_plans_name_key(self):
        section = self.plan.split('4. **Name key.**', 1)[1].split('5. **Cards.**', 1)[0]
        key = {}
        for line in section.splitlines():
            m = re.fullmatch(r'\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*', line)
            if m and not set(m.group(1)) <= set('-') and m.group(1) != 'Site name':
                if re.fullmatch(r'[A-Za-z0-9-]+', m.group(2)):
                    key[m.group(2)] = m.group(1).replace('**', '')
        for code, name in bp.DISPLAY_NAMES.items():
            with self.subTest(code=code):
                key_code = bp.NAME_KEY_ALIASES.get(code, code)
                if code in bp.NOT_IN_NAME_KEY:
                    self.assertNotIn(key_code, key)
                else:
                    self.assertEqual(key[key_code], name)
        used = {c for b in self.blocks.values() for c in b['display_names']}
        self.assertEqual(used, set(bp.DISPLAY_NAMES))
        self.assertEqual(set(self.jit['display_names']), {'REF', 'REFc-0', 'L0', 'L0c', 'FS', 'COMMON-125MS',
                                                          'COMMON-ONE-PERIOD'})
        self.assertEqual(set(self.ramp['display_names']), {'ID', 'NUM', 'REF', 'L0', 'L0c', 'FS', 'MATCH', 'CCA',
                                                           'COMMON-ONE-PERIOD'})

    def test_the_designs_are_the_protocols(self):
        jp, rp = self.src['jitter_protocol'], self.src['ramp_protocol']
        arms = {a['arm']: a for a in self.jit['design']['arms']}
        self.assertEqual(list(arms), ['A', 'B', 'C', 'M'])
        for p in jp['arms']:
            self.assertEqual(arms[p['id']]['training_delay_seconds'], p['tau_seconds'])
            self.assertEqual(arms[p['id']]['delay_uses_training_label'], p['uses_training_labels_for_augmentation'])
        self.assertEqual((arms['A']['training_delay_seconds'], arms['B']['training_delay_seconds']),
                         ('0.125*u', 'u/f_assigned_source_label'))
        self.assertIsNone(arms['C']['training_delay_seconds'])
        self.assertEqual(self.jit['design']['model'], self.src['jitter_export']['model'])
        self.assertEqual(self.jit['design']['dataset'], self.src['jitter_export']['dataset'])
        for c, d in zip(rp['cells'], self.ramp['design']['cells']):
            self.assertEqual((d['cell'], d['features'], d['head'], d['query'], d['parameters'], d['control']),
                             (c['id'], c['level'], c['head'], c['arm'], c['parameters']['total'], c['historical_id']))
            self.assertEqual(d['augmentation'], 'COMMON-ONE-PERIOD')
        for block, protocol in ((self.jit, jp), (self.ramp, rp)):
            for k in ('formula', 'draw', 'queries', 'inference'):
                self.assertEqual(block['design']['delay'][k], protocol['augmentation'][k])

    def test_not_run_is_the_protocols_deferred_list(self):
        for study, name in (('phase_jitter', 'jitter_protocol'), ('phase_ramp', 'ramp_protocol')):
            self.assertEqual([n['item'] for n in self.blocks[study]['not_run']], self.src[name]['deferred'])
        later = {n['item']: n['run_in'] for n in self.jit['not_run'] if n['run_in']}
        self.assertEqual(later, {'Same augmentation on FS-NUM': 'phase_ramp', 'MATCH head follow-up': 'phase_ramp',
                                 'CCA-derived features or residuals': 'cca_adapter'})
        self.assertTrue({'ADAPT-FS', 'RAW-RESIDUAL'} <= set(self.src['cca_adapter_export']['arms']))
        self.assertEqual({c['augmentation'] for c in self.ramp['design']['cells']}, {'COMMON-ONE-PERIOD'})
        self.assertEqual([n['run_in'] for n in self.ramp['not_run']], [None] * 6)

    def test_checks_are_the_receipts(self):
        j, r = self.jit['checks'], self.ramp['checks']
        self.assertEqual(j['randomized_label'], {'status': 'pass', 'fits': 40, 'cells': 4, 'cells_passed': 4})
        self.assertEqual(r['randomized_label'], {'status': 'pass', 'fits': 120, 'cells': 10, 'cells_passed': 10})
        self.assertEqual(j['bridge'], {'status': 'pass', 'fits': 3})
        self.assertEqual(r['bridge'], {'status': 'pass', 'fits': 18})
        ja, ra = self.src['jitter_audit'], self.src['ramp_audit']
        for got, audit in ((j['audit'], ja), (r['audit'], ra)):
            for k in ('status', 'release_eligible', 'main_models_reconstructed', 'canary_models_reconstructed',
                      'fixed_independent_refits', 'baseline_bridge_fits', 'total_optimizer_invocations'):
                self.assertEqual(got[k], audit[k])
        self.assertEqual((j['audit']['main_models_reconstructed'], r['audit']['main_models_reconstructed']), (210, 630))
        self.assertEqual((j['audit']['numerical_summary']['contrasts'], r['audit']['numerical_summary']['contrasts']),
                         (6, 13))
        self.assertEqual(r['audit']['status'], 'pass')          # the ramp's status is the audit's, not the score's
        self.assertEqual(j['reviews'], {'scientific': 'approved_for_aggregate_handoff',
                                        'provenance': 'approved_for_aggregate_handoff'})
        self.assertEqual(r['reviews'], {'scientific': 'approved_for_aggregate_release',
                                        'provenance': 'approved_for_aggregate_release'})
        # Pass or fail and counts only: no 99.9% interval of a randomized-label check is carried.
        self.assertNotIn(0.999, list(numbers(self.blocks)))

    def test_block_fields(self):
        self.assertEqual(list(self.blocks), ['phase_jitter', 'phase_ramp'])
        for study, block in self.blocks.items():
            with self.subTest(study=study):
                self.assertEqual(set(block), set(bp.BLOCK_FIELDS) | set(bp.EXTRA_FIELDS[study]))
                self.assertEqual(set(block['export_codes']), set(block['levels']) | set(block['contrasts']))

    def test_the_build_is_deterministic_and_round_trips(self):
        again = bp.build_blocks()
        self.assertEqual(json.dumps(again, ensure_ascii=False), json.dumps(self.blocks, ensure_ascii=False))
        self.assertEqual(json.loads(json.dumps(self.blocks, allow_nan=False)), self.blocks)

    # ------------------------------------------------------------------ refusals
    def test_an_edit_refuses_what_it_does_not_find(self):
        doc = copy.deepcopy(self.src['jitter_export'])
        doc['one_period_prediction']['reference'] = 0.39
        with self.assertRaises(ValueError):
            bp.apply_edits(doc, bp.EDITS['phase_jitter'], 'jitter')
        doc = copy.deepcopy(self.src['jitter_export'])
        doc['one_period_prediction']['point_meets'] = 0          # 0 is not False
        with self.assertRaises(ValueError):
            bp.apply_edits(doc, bp.EDITS['phase_jitter'], 'jitter')
        doc = copy.deepcopy(self.src['ramp_score'])
        doc['interpretation'] = 'Something else.'
        with self.assertRaises(ValueError):
            bp.apply_edits(doc, bp.EDITS['phase_ramp'], 'ramp')
        doc = copy.deepcopy(self.src['ramp_score'])
        doc['levels']['CCA/u8']['seeds'] = 3
        with self.assertRaises(ValueError):
            bp.apply_edits(doc, bp.EDITS['phase_ramp'], 'ramp')
        ops = {s: [(op, ptr) for op, ptr, _, _ in bp.EDITS[s]] for s in bp.STUDIES}
        self.assertEqual(ops['phase_jitter'], [('remove', '/one_period_prediction'), ('remove', '/release_governed_by')])
        self.assertEqual(ops['phase_ramp'][:3], [('remove', '/status'), ('remove', '/fifty_five_reference'),
                                                 ('remove', '/interpretation')])
        self.assertEqual(ops['phase_ramp'][3:], [('replace', f'/levels/CCA~1{e}/seeds')
                                                 for e in ('u8', 'seen_ba', 'm8', 'nn8', 'u3', 'cost')])

    def test_forged_or_moved_inputs_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            def forge(name, edit):
                doc = source(name)
                doc = edit(doc) if bp.PINS[name].get('text') else (edit(doc) or doc)
                data = (doc if isinstance(doc, str) else json.dumps(doc)).encode()
                path = Path(tmp) / f'{name}.{"md" if bp.PINS[name].get("text") else "json"}'
                path.write_bytes(data)
                pins = copy.deepcopy(bp.PINS)
                pins[name] = dict(pins[name], path=str(path), sha256=digest(data))
                return pins

            cases = {
                # A number changed and re-pinned: its review still binds the original bytes.
                'jitter export point': forge('jitter_export', lambda d: d['arms'][0]['metrics']['u8'].__setitem__(
                    'point', 0.2)),
                'ramp score point': forge('ramp_score', lambda d: d['levels']['FS-REF/u8'].__setitem__('point', 0.4)),
                # A canonical score that no longer equals the export.
                'jitter score': forge('jitter_score', lambda d: d['levels']['A/u8'].__setitem__('point', 0.2)),
                # A comparator study whose level moved.
                'ref2 control': forge('ref2_export', lambda d: d['aggregate']['levels']['L0c-FS-REF/u8'].__setitem__(
                    'point', 0.09)),
                # A wording review that no longer confirms.
                'wording review': forge('wording_review', lambda t: t.replace('**Confirmed', '**Held')),
                # A thread quote with another threshold.
                'ramp protocol': forge('ramp_protocol', lambda d: d['source_evidence'].__setitem__(
                    'comment_quote', 'My bet: unseen clears 45.')),
            }
            wrong = copy.deepcopy(bp.PINS)
            wrong['ramp_audit']['sha256'] = '0' * 64
            cases['wrong pin'] = wrong
            for label, pins in cases.items():
                with self.subTest(case=label), self.assertRaises(ValueError):
                    bp.build_blocks(pins)


if __name__ == '__main__':
    unittest.main()
