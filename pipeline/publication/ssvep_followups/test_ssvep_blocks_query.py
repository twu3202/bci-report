"""B1, the query and head blocks (cards 1 and 2): every value against its pinned source, to the last bit.

The sources are re-read here with their own pointer walk, not through the builder's helpers; the plan's name key,
source pins and card figures are read from the plan itself.
"""
import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

PUBLICATION = Path(__file__).resolve().parents[1]
if str(PUBLICATION) not in sys.path:
    sys.path.insert(0, str(PUBLICATION))

from export_snapshot import validate_public               # noqa: E402
from ssvep_followups import blocks_query as bq             # noqa: E402

PLAN = 'research/site_release_plan_20261019/Release Layout Plan v2.md'
REF_RUN = ('results', 'questions-in-language-ref')
PARENT_BSH = ('results', 'questions-in-language', 'descriptive', 'P-ssvep-L0', 'levels', 'B-sh seen_ba')
LOCAL_ROOT = re.compile(r'/(?:Volumes|Users|home|mnt)/')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw(name):
    return bq.location(bq.PINS[name]['path']).read_bytes()


def source(name):
    return json.loads(raw(name))


def walk(doc, ptr):
    """An independent RFC 6901 walk."""
    cur = doc
    for t in ptr.split('/')[1:]:
        t = t.replace('~1', '/').replace('~0', '~')
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


def point_and_interval(obj):
    """A source level or contrast as (estimate, [lo, hi]), whichever way its file spells it."""
    if 'interval_95' in obj:
        return obj['estimate'], list(obj['interval_95'])
    return obj['point'], [obj['lo'], obj['hi']]


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


def keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys(v)


def pct2(v):
    return f'{100 * v:.2f}'


@unittest.skipUnless(bq.inputs_available(), 'the pinned research inputs are local-only; see blocks_query.PINS')
class QueryBlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = bq.build_blocks()
        cls.src = {name: source(name) for name in bq.PINS}
        cls.plan = bq.location(PLAN).read_text()

    # ------------------------------------------------------------------ pins
    def test_every_input_is_its_pinned_bytes(self):
        for name, ref in bq.PINS.items():
            with self.subTest(name=name):
                self.assertEqual(digest(raw(name)), ref['sha256'])
        self.assertEqual(digest(bq.location(bq.PARENT_SERVED).read_bytes()), bq.PINS['parent']['sha256'])

    def test_the_blocks_name_the_plans_source_pins(self):
        pins = {s: re.search(rf'\b{label} `([0-9a-f]+)…`', self.plan).group(1)
                for s, label in (('ref', 'REF'), ('ref2', 'REF2'), ('softmax', 'softmax'))}
        for study, prefix in pins.items():
            with self.subTest(study=study):
                self.assertGreaterEqual(len(prefix), 6)
                self.assertTrue(self.blocks[study]['source_sha256'].startswith(prefix))
                self.assertEqual(self.blocks[study]['source_sha256'], bq.PINS[bq.EXPORT_OF[study]]['sha256'])
                self.assertEqual(self.blocks[study]['review_sha256'], bq.PINS[bq.REVIEW_OF[study]]['sha256'])
        self.assertEqual(self.blocks['softmax']['parent_sha256'], bq.PINS['parent']['sha256'])

    def test_each_review_binds_its_export(self):
        s = self.src
        self.assertEqual(s['ref_review']['delivered_file_sha256']['Reference Spectrum Query Audited Results.json'],
                         digest(raw('ref_export')))
        self.assertEqual(s['ref2_review']['export_sha256'], digest(raw('ref2_export')))
        self.assertEqual(s['softmax_review']['export_sha256'], digest(raw('softmax_export')))
        self.assertEqual(s['softmax_review']['prior_baseline_audit_sha256'], digest(raw('softmax_baseline')))
        self.assertEqual(s['softmax_review']['accepted_runtime_review_sha256'], digest(raw('softmax_runtime_review')))

    # ------------------------------------------------------------------ values, to full precision
    def test_ref_levels_are_the_exports(self):
        run = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN))
        levels, seen = self.blocks['ref']['levels'], set()
        for block, feature in (('REF-ssvep-L0', 'L0'), ('REF-ssvep-L1', 'L1')):
            for name, lv in run['descriptive'][block]['levels'].items():
                arm, endpoint = name.split(' ')
                lid = f'{arm}/{endpoint}' if arm in ('CCA', 'TEMPLATE') else f'{feature}-FS-{arm}/{endpoint}'
                seen.add(lid)
                got = levels[lid]
                with self.subTest(level=f'{block} {name}'):
                    self.assertEqual(got['estimate'], lv['estimate'])
                    self.assertEqual(got['interval'], lv['interval_95'])
                    self.assertEqual((got['unit'], got['people'], got['origin']),
                                     (lv['unit'], lv['people'], lv['origin']))
                    self.assertEqual(got['seeds'], 'no training' if arm == 'CCA' else lv['seeds'])
        self.assertEqual(set(levels), seen)
        self.assertEqual(len(seen), 60 - 6)     # 60 audited components; CCA's six are the same in both panels

    def test_ref_contrasts_are_the_exports(self):
        run = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN))
        contrasts = self.blocks['ref']['contrasts']
        n = 0
        for part in ('primary', 'secondary'):
            for block in run[part]['blocks']:
                feature = block['level']
                for entry in block['entries']:
                    n += 1
                    got = contrasts[f'{feature}/{entry["id"]}']
                    with self.subTest(contrast=entry['key']):
                        self.assertEqual(got['estimate'], entry['estimate'])
                        self.assertEqual(got['interval'], entry['interval_95'])
                        self.assertEqual(got['role'], entry['role'])
                        self.assertEqual(got['flags'], {k: entry[k] for k in ('difference', 'margin_pass',
                                                                               'margin_rule')})
                        self.assertEqual((got['people'], got['seeds'], got['unit']),
                                         (entry['people'], entry['seeds'], entry['unit']))
        self.assertEqual(n, len(contrasts), 8)

    def test_ref2_levels_and_contrasts_are_the_exports(self):
        agg = self.src['ref2_export']['aggregate']
        block = self.blocks['ref2']
        self.assertEqual(list(block['levels']), list(agg['levels']))
        for lid, lv in agg['levels'].items():
            with self.subTest(level=lid):
                got = block['levels'][lid]
                self.assertEqual(got['estimate'], lv['point'])
                self.assertEqual(got['interval'], [lv['lo'], lv['hi']])
                self.assertEqual(got['people'], lv['people'])
                self.assertEqual(got['seeds'], 'no training' if lid.startswith('CCA/') else lv['seeds'])
        self.assertEqual(list(block['contrasts']), list(agg['contrasts']))
        for cid, c in agg['contrasts'].items():
            with self.subTest(contrast=cid):
                got = block['contrasts'][cid]
                self.assertEqual(got['estimate'], c['point'])
                self.assertEqual(got['interval'], [c['lo'], c['hi']])
                self.assertEqual((got['left'], got['right']),
                                 (f'{c["left"]}/{c["metric"]}', f'{c["right"]}/{c["metric"]}'))
                self.assertEqual(got['role'], c['role'])
                self.assertEqual(got['flags'], {k: c[k] for k in ('difference', 'equivalent_within_2pp',
                                                                  'noninferiority_to_CCA', 'meaningful_head_gain')})
        self.assertEqual((len(block['levels']), len(block['contrasts'])), (90, 12))

    def test_ref2_origins_follow_its_protocol_and_reuse_the_ref_bits(self):
        new = {c['id'] for c in self.src['ref2_protocol']['scope']['cells']}
        for lid, lv in self.blocks['ref2']['levels'].items():
            cell = lid.split('/')[0]
            with self.subTest(level=lid):
                if cell in new:
                    self.assertEqual(lv['origin'], 'new')
                else:
                    self.assertIn(lv['origin'], ('reused_ref', 'reused_parent'))
                    ref = self.blocks['ref']['levels'][lid]
                    self.assertEqual((lv['estimate'], lv['interval']), (ref['estimate'], ref['interval']))

    def test_softmax_levels_and_contrasts_are_the_exports(self):
        agg = self.src['softmax_export']['aggregate']
        block = self.blocks['softmax']
        for arm in ('LINEAR-CE', 'BSH-CE'):
            with self.subTest(arm=arm):
                got = block['levels'][f'L0-{arm}/seen_ba']
                self.assertEqual(got['estimate'], agg['levels'][arm]['point'])
                self.assertEqual(got['interval'], [agg['levels'][arm]['lo'], agg['levels'][arm]['hi']])
                self.assertEqual((got['people'], got['seeds']), (70, 3))
        for part in ('primary', 'secondary'):
            c = agg[part]
            got = block['contrasts'][c['name']]
            with self.subTest(contrast=c['name']):
                self.assertEqual(got['role'], part)
                self.assertEqual(got['estimate'], c['point'])
                self.assertEqual(got['interval'], [c['lo'], c['hi']])
                self.assertEqual(got['flags'], {'equivalent_strict_2pp': c['equivalent_strict_2pp'],
                                                'equivalence_margin': c['equivalence_margin']})
        self.assertEqual(len(block['contrasts']), 2)

    def test_the_one_vs_rest_interval_is_the_live_route_3_files(self):
        parent = self.src['parent']
        for t in PARENT_BSH:
            parent = parent[t]
        got = self.blocks['softmax']['levels']['L0-BSH-BCE/seen_ba']
        self.assertEqual(got['estimate'], parent['estimate'])
        self.assertEqual(got['interval'], parent['interval_95'])
        self.assertEqual(got['origin'], 'reused_parent')
        self.assertEqual(self.blocks['softmax']['export_codes']['L0-BSH-BCE/seen_ba'],
                         ['questions-in-language-update.json#/results/questions-in-language/descriptive/'
                          'P-ssvep-L0/levels/B-sh seen_ba'])
        # The softmax export carries the point alone, equal to the route 3 one up to the last bit of a double.
        historical = self.src['softmax_export']['aggregate']['historical_descriptive']['BSH-BCE']
        self.assertLessEqual(abs(historical - parent['estimate']), 1e-15)
        self.assertEqual(self.src['parent']['release_id'], 'questions-in-language-update-20261008')

    def test_every_export_code_points_at_its_value(self):
        files = {'#': None, 'questions-in-language-update.json#': self.src['parent']}
        for study, block in self.blocks.items():
            own = self.src[bq.EXPORT_OF[study]]
            for item, places in block['export_codes'].items():
                got = block['levels'].get(item) or block['contrasts'].get(item)
                for place in places:
                    prefix, ptr = place.split('#', 1)
                    doc = files[prefix + '#'] or own
                    with self.subTest(study=study, item=item, place=place):
                        est, iv = point_and_interval(walk(doc, ptr))
                        self.assertEqual((got['estimate'], got['interval']), (est, iv))

    def test_the_card_figures_print_from_these_values(self):
        """Cards 1 and 2 of plan section 2.1, at pct2 and pp2, from the exact doubles."""
        ref, ref2, sm = (self.blocks[s] for s in ('ref', 'ref2', 'softmax'))
        cases = [
            (ref['levels']['L0-FS-REF/u8'], '39.00', '36.07', '41.78', 0.39002976190476196),
            (ref['levels']['L0-FS-NUM/u8'], '41.46', None, None, 0.4146428571428571),
            (ref['levels']['CCA/u8'], '80.90', None, None, 0.809017857142857),
            (ref['contrasts']['L0/R1'], '-2.46', '-3.47', '-1.52', -0.02461309523809525),
            (ref['levels']['L0-FS-REF/seen_ba'], '31.48', None, None, 0.3148437499999999),
            (ref['contrasts']['L0/R2'], '-0.57', '-1.06', '-0.05', -0.005721726190476196),
            (ref['contrasts']['L1/R1'], '-2.35', '-3.16', '-1.57', -0.023541666666666666),
            (ref['contrasts']['L1/R2'], '0.44', '-0.01', '0.92', 0.0043824404761904755),
            (ref['levels']['TEMPLATE/u8'], '28.84', None, None, 0.2883928571428571),
            (sm['levels']['L0-LINEAR-CE/seen_ba'], '35.90', '32.30', '39.32', 0.3590029761904762),
            (sm['levels']['L0-BSH-CE/seen_ba'], '31.45', None, None, 0.314546130952381),
            (sm['contrasts']['BSH-CE minus BSH-BCE'], '-0.71', '-1.01', '-0.41', -0.007098214285714291),
            (ref2['levels']['L0c-FS-ID/seen_ba'], '50.08', None, None, 0.5008184523809525),
            (ref2['levels']['L0c-MATCH-ID/seen_ba'], '56.14', None, None, 0.5613616071428572),
            (ref2['contrasts']['phase_FS'], '16.30', '13.36', '19.32', 0.16300595238095236),
            (ref2['levels']['L0c-FS-REFc-0/u8'], '24.97', None, None, 0.24973214285714285),
            (ref2['levels']['L0c-MATCH-REFc-0/u8'], '22.47', None, None, 0.22470238095238093),
            (ref2['contrasts']['harmonics_u8'], '-13.27', '-15.04', '-11.45', -0.13270833333333332),
            (ref2['contrasts']['harmonics_seen'], '-3.12', '-3.65', '-2.57', -0.031212797619047623),
        ]
        for row, est, lo, hi, exact in cases:
            with self.subTest(figure=est):
                self.assertEqual(row['estimate'], exact)
                self.assertEqual(pct2(row['estimate']), est)
                if lo is not None:
                    self.assertEqual([pct2(v) for v in row['interval']], [lo, hi])

    # ------------------------------------------------------------------ declared edits
    def test_epochs_is_renamed_and_nothing_else_in_the_design_changes(self):
        design = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN) + '/design')
        got = self.blocks['ref']['design']
        self.assertEqual(got['training_epochs'], design['epochs'])
        self.assertEqual(list(got), ['training_epochs' if k == 'epochs' else k for k in design])
        self.assertEqual({k: v for k, v in got.items() if k != 'training_epochs'},
                         {k: v for k, v in design.items() if k != 'epochs'})
        self.assertNotIn('epochs', set(keys(self.blocks)))
        with self.assertRaises(ValueError):          # why the rename is declared: the boundary refuses the key
            validate_public({'design': {'epochs': 60}})

    def test_the_jev_line_is_dropped(self):
        limitations = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN) + '/limitations')
        self.assertIn('Jev', limitations[7])
        self.assertEqual(limitations[7], bq.REF_JEV_LINE)
        cited = {ptr for doc, ptr, _ in bq.LIMITATION_SOURCES['ref'].values() if doc == 'ref_export'}
        self.assertNotIn('/' + '/'.join(REF_RUN) + '/limitations/7', cited)
        self.assertEqual(len([p for p in cited if '/limitations/' in p]), len(limitations) - 1)
        self.assertFalse(any('Jev' in s for s in strings(self.blocks)))

    def test_pending_strings_and_paths_are_dropped(self):
        # The sources do carry them, so this test can fail.
        self.assertIn('pending', self.src['ref_export']['status'])
        self.assertIn('pending', self.src['ref2_export']['aggregate']['status'])
        self.assertIn('pending', self.src['softmax_export']['aggregate']['status'])
        for name in ('ref2_export', 'softmax_export'):
            self.assertTrue(LOCAL_ROOT.search(self.src[name]['remote_root']))
        text = list(strings(self.blocks))
        self.assertFalse([s for s in text if 'pending' in s.lower()])
        self.assertFalse([s for s in text if LOCAL_ROOT.search(s) or 'trx50' in s.lower() or 'twu' in s.lower()
                          or 'Gal4' in s or 'BCI_Arena' in s])
        validate_public(self.blocks)

    def test_cca_seeds_become_no_training_and_only_those(self):
        for study in ('ref', 'ref2'):
            for lid, lv in self.blocks[study]['levels'].items():
                with self.subTest(study=study, level=lid):
                    if lid.startswith('CCA/'):
                        self.assertEqual(lv['seeds'], 'no training')
                    elif lid.startswith('TEMPLATE/'):
                        self.assertEqual(lv['seeds'], 1)
                    else:
                        self.assertEqual(lv['seeds'], 3)
        cca = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN) + '/descriptive/REF-ssvep-L0/levels/CCA u8')
        self.assertEqual(cca['seeds'], 1)

    def test_an_edit_refuses_what_it_does_not_find(self):
        doc = copy.deepcopy(self.src['ref_export'])
        doc['results']['questions-in-language-ref']['limitations'][7] = 'Some other line.'
        with self.assertRaises(ValueError):
            bq.apply_edits(doc, bq.EDITS['ref'], 'REF')
        doc = copy.deepcopy(self.src['ref_export'])
        doc['results']['questions-in-language-ref']['design']['training_epochs'] = 60
        with self.assertRaises(ValueError):
            bq.apply_edits(doc, bq.EDITS['ref'], 'REF')
        doc = copy.deepcopy(self.src['ref2_export'])
        doc['remote_root'] = 'decision_route3_ref2_20261014'
        with self.assertRaises(ValueError):
            bq.apply_edits(doc, bq.EDITS['ref2'], 'REF2')
        doc = copy.deepcopy(self.src['softmax_export'])
        doc['aggregate']['status'] = 'complete'
        with self.assertRaises(ValueError):
            bq.apply_edits(doc, bq.EDITS['softmax'], 'softmax')

    def test_the_edits_are_the_declared_ones(self):
        ops = {s: [(op, ptr.rsplit('/', 1)[-1]) for op, ptr, _, _ in bq.EDITS[s]] for s in bq.STUDIES}
        self.assertEqual(ops['ref'][:4], [('remove', 'status'), ('remove', 'independent_handoff_review_required'),
                                          ('remove', '7'), ('rename', 'epochs')])
        self.assertEqual(ops['ref'][4:], [('replace', 'seeds')] * 12)
        self.assertEqual(ops['ref2'], [('remove', 'remote_root'), ('remove', 'recovery_overlay'),
                                       ('remove', 'status')] + [('replace', 'seeds')] * 6)
        self.assertEqual(ops['softmax'], [('remove', 'remote_root'),
                                          ('remove', 'original_full_receipt_remains_private'), ('remove', 'status')])
        for s in bq.STUDIES:
            for op, ptr, _, new in bq.EDITS[s]:
                if op == 'replace':
                    self.assertIn('CCA', ptr)
                    self.assertEqual(new, 'no training')

    # ------------------------------------------------------------------ names
    def test_display_names_follow_the_plans_name_key(self):
        section = self.plan.split('4. **Name key.**', 1)[1].split('5. **Cards.**', 1)[0]
        key = {}
        for line in section.splitlines():
            m = re.fullmatch(r'\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*', line)
            if m and not set(m.group(1)) <= set('-') and m.group(1) != 'Site name':
                code = m.group(2)
                if re.fullmatch(r'[A-Za-z0-9-]+', code):
                    key[code] = m.group(1).replace('**', '')
        self.assertGreaterEqual(len(key), 15)
        for code, name in bq.DISPLAY_NAMES.items():
            with self.subTest(code=code):
                key_code = bq.NAME_KEY_ALIASES.get(code, code)
                if code in bq.NOT_IN_NAME_KEY:
                    self.assertNotIn(key_code, key)
                else:
                    self.assertEqual(key[key_code], name)
        used = {c for b in self.blocks.values() for c in b['display_names']}
        self.assertEqual(used, set(bq.DISPLAY_NAMES))
        for study, block in self.blocks.items():
            for code, name in block['display_names'].items():
                self.assertEqual(name, bq.DISPLAY_NAMES[code])

    def test_card_2_names_the_heads_as_the_plan_words_them(self):
        lead = self.plan.split('- **Card 2.**', 1)[1].split('- **Card 3.**', 1)[0]
        self.assertIn('A plain 32-way softmax', lead)
        self.assertIn('one-vs-rest version', lead)
        self.assertIn('Dropping the second and third harmonics', lead)
        self.assertEqual(bq.DISPLAY_NAMES['LINEAR-CE'], 'plain 32-way softmax')

    # ------------------------------------------------------------------ structure
    def test_block_fields(self):
        self.assertEqual(list(self.blocks), ['ref', 'ref2', 'softmax'])
        for study, block in self.blocks.items():
            with self.subTest(study=study):
                extra = {'ref': {'design'}, 'ref2': set(), 'softmax': {'parent_sha256'}}[study]
                self.assertEqual(set(block), set(bq.BLOCK_FIELDS) | extra)
                self.assertEqual(block['interval_method'], {
                    'method': 'hierarchical paired bootstrap over people and fold-shared seed indices',
                    'seed': 20261007, 'draws': 2000, 'level': 0.95})
                self.assertEqual(set(block['export_codes']), set(block['levels']) | set(block['contrasts']))

    def test_units_are_fractions(self):
        for study, block in self.blocks.items():
            for lid, lv in block['levels'].items():
                with self.subTest(study=study, level=lid):
                    lo, hi = lv['interval']
                    if lid.endswith('/cost'):
                        self.assertEqual(lv['unit'], 'difference of proportions')
                        self.assertTrue(-1 <= lo <= lv['estimate'] <= hi <= 0.0 + 1e-15)
                    else:
                        self.assertEqual(lv['unit'], 'proportion')
                        self.assertTrue(0 <= lo <= lv['estimate'] <= hi <= 1)
            for cid, c in block['contrasts'].items():
                with self.subTest(study=study, contrast=cid):
                    self.assertEqual(c['unit'], 'difference of proportions')
                    self.assertTrue(-1 <= c['interval'][0] <= c['estimate'] <= c['interval'][1] <= 1)
                    self.assertLess(abs(c['estimate']), 1)

    def test_contrasts_are_differences_of_their_levels(self):
        for study, block in self.blocks.items():
            for cid, c in block['contrasts'].items():
                with self.subTest(study=study, contrast=cid):
                    diff = block['levels'][c['left']]['estimate'] - block['levels'][c['right']]['estimate']
                    self.assertAlmostEqual(diff, c['estimate'], delta=1e-12)

    def test_undefined_endpoints_are_absent_and_their_arms_cannot_ask_unseen(self):
        forms = self.src['parent']['results']['questions-in-language']['design']['question_forms']
        self.assertIs(forms['ID']['can_ask_unseen'], False)
        self.assertIs(forms['B-sh']['can_ask_unseen'], False)
        self.assertIn('ID has no direct held-query predictions', self.src['ref2_export']['aggregate']['u3_caveat'])
        expected = {
            'ref': {f'{f}-FS-ID/{e}' for f in ('L0', 'L1') for e in ('u8', 'u3', 'cost')},
            'ref2': {f'{c}/{e}' for c in ('L0-FS-ID', 'L0-MATCH-ID', 'L0c-FS-ID', 'L0c-MATCH-ID')
                     for e in ('u8', 'u3', 'cost')},
            'softmax': {'L0-LINEAR-CE/u8', 'L0-BSH-CE/u8', 'L0-BSH-BCE/u8'},
        }
        for study, block in self.blocks.items():
            with self.subTest(study=study):
                got = {u['level'] for u in block['undefined']}
                self.assertEqual(got, expected[study])
                self.assertFalse(got & set(block['levels']))
                self.assertEqual({u['reason'] for u in block['undefined']}, {'cannot_ask_unseen'})

    def test_not_run_is_the_exports_list_reconciled_with_ref2(self):
        listed = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN) + '/not_run')
        got = self.blocks['ref']['not_run']
        self.assertEqual([n['item'] for n in got], listed)
        later = {n['item']: n['run_in'] for n in got if n['run_in']}
        self.assertEqual(later, {'Matching/bilinear head': 'ref2', 'Fundamental-only reference ablation': 'ref2'})
        self.assertTrue(any('-MATCH-' in lid for lid in self.blocks['ref2']['levels']))
        self.assertIn('L0-FS-REF1/u8', self.blocks['ref2']['levels'])
        self.assertEqual(self.blocks['ref2']['not_run'], [])
        self.assertEqual(self.blocks['softmax']['not_run'], [])

    def test_limitation_keys_cite_sentences_that_say_them(self):
        for study, block in self.blocks.items():
            self.assertEqual(block['limitations_keys'], list(bq.LIMITATION_SOURCES[study]))
            for key, (doc, ptr, phrase) in bq.LIMITATION_SOURCES[study].items():
                with self.subTest(study=study, key=key):
                    text = walk(self.src[doc], ptr)
                    self.assertIn(phrase, text)
                    self.assertNotIn('Jev', text)

    def test_checks_are_the_audits(self):
        ref = walk(self.src['ref_export'], '/' + '/'.join(REF_RUN) + '/audits')
        got = self.blocks['ref']['checks']
        self.assertEqual(got['audit']['status'], ref['status'])
        self.assertEqual(got['audit']['numeric_metrics']['components'], ref['numeric_metrics']['components'])
        self.assertEqual((got['headroom'], got['excluded_people']), ({'L0': True, 'L1': True}, 0))
        ref2 = self.src['ref2_export']
        got = self.blocks['ref2']['checks']
        self.assertEqual(got['counts'], ref2['counts'])
        self.assertEqual(got['completion'], 'audited_complete')
        self.assertEqual(got['audit']['main_models_reconstructed'], 1260)
        sm = self.src['softmax_export']
        got = self.blocks['softmax']['checks']
        self.assertEqual(got['counts'], sm['counts'])
        self.assertEqual(got['audit'], {k: sm['audit'][k] for k in ('status', 'metrics', 'reconstructions',
                                                                    'independent_refits')})
        self.assertNotIn('wall_seconds', set(keys(self.blocks)))

    def test_no_55_and_no_name_in_any_string(self):
        for s in strings(self.blocks):
            if not re.fullmatch(r'[0-9a-f]{64}', s):
                self.assertNotIn('55', s)

    def test_the_build_is_deterministic_and_round_trips(self):
        again = bq.build_blocks()
        self.assertEqual(json.dumps(again), json.dumps(self.blocks))
        self.assertEqual(json.loads(json.dumps(self.blocks, allow_nan=False)), self.blocks)

    # ------------------------------------------------------------------ refusals
    def test_forged_or_moved_inputs_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            def forge(name, edit):
                doc = source(name)
                edit(doc)
                data = json.dumps(doc).encode()
                path = Path(tmp) / f'{name}.json'
                path.write_bytes(data)
                pins = copy.deepcopy(bq.PINS)
                pins[name] = {'path': str(path), 'sha256': digest(data)}
                return pins

            # An export whose number changed: re-pinned, it is still not what its review binds.
            pins = forge('ref_export', lambda d: d['results']['questions-in-language-ref']['descriptive']
                         ['REF-ssvep-L0']['levels']['REF u8'].__setitem__('estimate', 0.4))
            with self.assertRaises(ValueError):
                bq.build_blocks(pins)
            pins = forge('softmax_export', lambda d: d['aggregate']['levels']['LINEAR-CE'].__setitem__('point', 0.4))
            with self.assertRaises(ValueError):
                bq.build_blocks(pins)
            # A route 3 file that is not the one served.
            pins = forge('parent', lambda d: d.__setitem__('generated_at', 'x'))
            with self.assertRaises(ValueError):
                bq.build_blocks(pins)
            # A pin that does not match the bytes.
            pins = copy.deepcopy(bq.PINS)
            pins['ref2_export']['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                bq.build_blocks(pins)


if __name__ == '__main__':
    unittest.main()
