"""The new-SSVEP-frequencies release: what must follow from the pinned research records, and what must stay out."""
import copy
import hashlib
import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_new_ssvep_frequencies_export as au
import export_new_ssvep_frequencies_update as ex
from export_snapshot import validate_public
from ssvep_followups import blocks_cca

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
PLAN = ex.PROJECT / 'research/site_release_plan_20261019/Release Layout Plan v2.md'
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                              re.IGNORECASE)
HASH = re.compile(r'[0-9a-f]{64}')


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pct2(x):
    return f'{100 * x:.2f}'


def pp2(x):
    return f'{100 * x:+.2f}'


def leaves(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield trail + (k,), None, k              # the key itself, as a leaf of its own
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    else:
        yield trail, value, None


def texts(payload):
    return [v for _, v, _ in leaves(payload) if isinstance(v, str)]


def keys(payload):
    return [k for _, _, k in leaves(payload) if k is not None]


def numbers(payload):
    return [v for _, v, _ in leaves(payload) if isinstance(v, (int, float)) and not isinstance(v, bool)]


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class NewSsvepFrequenciesRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = ex.build(ex.MANIFEST.read_bytes())
        cls.plan = PLAN.read_text()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def served(self, edit):
        """Two identical served copies, edited, under the temporary root, for the auditor to read."""
        payload = json.loads(ex.OUTPUTS[0].read_bytes())
        edit(payload)
        data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
        paths = []
        for i in range(2):
            p = Path(self.tmp.name) / f'served-{i}.json'
            p.write_bytes(data)
            paths.append(p)
        return mock.patch.object(au, 'SERVED', tuple(paths))

    def repin(self, manifest, block, name, edit):
        """An edited copy of one pinned input under the temporary root, re-pinned in a copy of the manifest."""
        ref = manifest['blocks'][block]['pins'][name] if block else manifest['planning'][name]
        obj = json.loads(ex.location(ref['path']).read_bytes())
        edit(obj)
        data = json.dumps(obj).encode()
        path = Path(self.tmp.name) / Path(ref['path']).name
        path.write_bytes(data)
        ref['path'], ref['sha256'] = str(path), digest(data)

    # ------------------------------------------------------------------ the build itself
    def test_the_published_file_is_the_reviewed_build(self):
        data = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(audit, au.audit(), 'the recorded audit is the one the auditor writes for these bytes')
        self.assertEqual(audit['figures_compared'],
                         audit['copied_exactly'] + audit['recomputed'] + audit['editorial'] + audit['nulls_kept'])
        self.assertGreater(audit['figures_compared'], 2000)

    def test_the_served_copies_are_byte_identical(self):
        self.assertEqual(ex.OUTPUTS[0].read_bytes(), ex.OUTPUTS[1].read_bytes())

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-new-ssvep-frequencies-update-v1')
        self.assertEqual(p['release_id'], 'new-ssvep-frequencies-update-20261020')
        self.assertEqual(p['generated_at'], '2026-10-20')
        self.assertEqual(p['status'], 'aggregate_preview')
        self.assertEqual(list(p['studies']), ['ref', 'ref2', 'softmax', 'phase_jitter', 'phase_ramp',
                                              'cca_diagnostics', 'cca_adapter', 'wearable_transfer'])
        for k in ('cohort', 'wearable', 'endpoints', 'name_key', 'rights', 'provenance'):
            self.assertIn(k, p)
        self.assertEqual(p['provenance']['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(list(p['provenance']['source_export_sha256']), list(p['studies']))
        for study, block in p['studies'].items():
            self.assertEqual(p['provenance']['source_export_sha256'][study], block['source_sha256'])
        self.assertEqual([c['card'] for c in p['placement']['cards']], list(range(1, 9)))
        self.assertEqual(p['placement']['cards'][7], {'card': 8, 'anchor': 'cross-spectral', 'studies': [],
                                                      'status_only': True})
        self.assertFalse(p['placement']['leaderboard'])

    def test_the_source_pins_are_the_plans(self):
        row = next(line for line in self.plan.splitlines() if line.startswith('| `new-ssvep-frequencies-update-<D>`'))
        pins = dict(re.findall(r'(REF2|REF|softmax|jitter|aggregate|ramp|audit|diagnostics|adapter|external) `([0-9a-f]{6,})…`',
                               row))
        src = self.payload['provenance']['source_export_sha256']
        by_hash = self.payload['provenance']['pinned_by_hash_only']
        for name, study in (('REF', 'ref'), ('REF2', 'ref2'), ('softmax', 'softmax'), ('jitter', 'phase_jitter'),
                            ('ramp', 'phase_ramp'), ('diagnostics', 'cca_diagnostics'), ('adapter', 'cca_adapter'),
                            ('external', 'wearable_transfer')):
            self.assertTrue(src[study].startswith(pins[name]), study)
        self.assertTrue(by_hash['phase_jitter_canonical_score'].startswith(pins['aggregate']))
        self.assertTrue(by_hash['phase_ramp_audit'].startswith(pins['audit']))
        self.assertTrue(src['cca_adapter'].startswith('6f68114e'), 'the adapter figures come from 6f68114e… only')

    def test_the_manifest_pins_what_the_block_modules_pin(self):
        for m, module in ex.MODULES.items():
            self.assertEqual(MANIFEST['blocks'][m]['pins'], {k: dict(v) for k, v in module.PINS.items()}, m)

    # ------------------------------------------------------------------ the boundary
    def test_validate_public_passes_and_still_refuses(self):
        validate_public(self.payload)
        for edit in (lambda p: p['cohort'].update(note='/Users/someone/run/x'),
                     lambda p: p['studies']['ref']['levels']['L0-FS-REF/u8'].update(note='sub-007 excluded'),
                     lambda p: p['studies']['ref'].update(epochs=60)):
            bad = copy.deepcopy(self.payload)
            edit(bad)
            with self.assertRaises(ValueError):
                validate_public(bad)

    def test_the_commenters_figure_appears_nowhere(self):
        for v in numbers(self.payload):
            self.assertGreater(abs(v - 11 / 20), 1e-12)
            self.assertGreater(abs(v - 55), 1e-9)
        for t in texts(self.payload):
            if not HASH.fullmatch(t):
                self.assertIsNone(CONFIDENCE_TOKEN.search(t), t)
        for k in keys(self.payload):
            self.assertIsNone(re.search(r'fifty|05{2}|prediction|confidence_figure', k, re.I), k)
        # The review records of this release carry it nowhere either, apart from hashes.
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = HASH.sub('', path.read_text())
            self.assertIsNone(CONFIDENCE_TOKEN.search(body), path.name)
        # A legitimate figure with the digit pair, at full precision, is kept (R5 M7): the token rule is not a scan.
        self.assertIn('55', repr(self.payload['studies']['cca_diagnostics']['levels']['CHANNEL-JOINT/u8']['estimate']))

    def test_the_bet_is_stated_once_in_the_phase_ramp(self):
        p = self.payload
        holders = [s for s, b in p['studies'].items() if 'thread_bet' in b]
        self.assertEqual(holders, ['phase_ramp'])
        bet = p['studies']['phase_ramp']['thread_bet']
        self.assertEqual(bet, {'held8_threshold': 0.39, 'source_url': 'https://huggingface.co/posts/Twu31/109502481720473'})
        self.assertEqual(numbers(p).count(0.39), 1)
        self.assertNotIn('#', bet['source_url'])
        self.assertEqual(p['thread']['url'], bet['source_url'])
        self.assertFalse(p['thread']['commenter_named'])

    def test_no_private_path_name_or_host(self):
        text = ex.OUTPUTS[0].read_text()
        self.assertIsNone(re.search(r'/(?:Users|home|Volumes|mnt|media|private|tmp|srv|root)/', text))
        for name in ('trx50', 'trx', 'gal4', 'bci_arena', 'bigdata'):
            self.assertIsNone(re.search(rf'(?<![a-z0-9]){name}(?![a-z0-9])', text, re.I), name)
        self.assertNotIn('twu', text.replace(self.payload['thread']['url'], '').lower(),
                         'the only twu is the public thread handle in the post URL')
        private = ex.private_names(ex.load(MANIFEST))
        self.assertGreaterEqual(len(private), 4)
        for n in private:
            self.assertIsNone(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.I), n)

    def test_the_commenter_is_not_named(self):
        for t in texts(self.payload):
            self.assertIsNone(blocks_cca.REFUSED_TEXT.search(t), t)

    def test_nothing_withheld_reaches_the_file(self):
        published = set(numbers(self.payload))
        withheld = ex.withheld_values(ex.load(MANIFEST))
        self.assertGreater(len(withheld), 30)
        self.assertFalse(withheld & published)
        for k in ('per_seed_descriptive', 'protected_trials', 'private_root', 'remote_root', 'pid', 'job', 'epochs',
                  'one_period_prediction', 'release_governed_by', 'fifty_five_reference', 'interpretation'):
            self.assertNotIn(k, keys(self.payload), k)

    # ------------------------------------------------------------------ the declared edits
    def test_the_declared_edits(self):
        s = self.payload['studies']
        self.assertEqual(s['ref']['design']['training_epochs'], 60)
        for study, cca in (('ref', 'CCA'), ('ref2', 'CCA'), ('phase_ramp', 'CCA'), ('cca_diagnostics', 'CCA-RAW'),
                           ('cca_adapter', 'CCA-RAW')):
            self.assertEqual({lv['seeds'] for lid, lv in s[study]['levels'].items() if lid.startswith(cca + '/')},
                             {'no training'}, study)
        self.assertEqual(s['phase_jitter']['contrasts']['S2']['estimate'], -0.25875)
        self.assertFalse(any('pending' in t.lower() for t in texts(s)))
        self.assertFalse(any('Jev' in t for t in texts(self.payload)))

    # ------------------------------------------------------------------ what spans the studies
    def test_the_cohort_of_cards_1_to_6(self):
        c = self.payload['cohort']
        self.assertEqual((c['dataset'], c['people'], c['targets'], c['windows'], c['window_seconds'], c['person_folds'],
                          c['frequency_rotations'], c['seen_frequencies'], c['held_out_frequencies'],
                          c['training_seeds']), ('BETA', 70, 40, 11200, 2, 7, 5, 32, 8, 3))
        self.assertEqual(c['card5'], {'training_free_scorers': 6, 'ridge_fits': 35})
        self.assertEqual(c['cards'], [1, 2, 3, 4, 5, 6])
        self.assertEqual(c['same_cohort_as'], 'questions-in-language-update-20261008')

    def test_the_wearable_scope_of_card_7(self):
        w = self.payload['wearable']
        self.assertEqual((w['dataset'], w['people'], w['targets'], w['frequency_range_hz'], w['windows_per_sensor'],
                          w['windows'], w['window_seconds'], w['sensors'], w['source_models'], w['retraining'],
                          w['matched_cca_harmonics']),
                         ('Wearable-102', 102, 12, [9.25, 14.75], 12240, 24480, 2, ['dry', 'wet'], 105, False, 3))
        self.assertEqual(w['recordings'], 'as stored')
        self.assertIn('cannot rule it out', w['participant_overlap_with_beta'])
        self.assertIn(w['overlap_limitation_key'], self.payload['studies']['wearable_transfer']['limitations_keys'])

    def test_the_endpoint_strip(self):
        e = {x['id']: x for x in self.payload['endpoints']}
        self.assertEqual([x['task'] for x in self.payload['endpoints']],
                         ['Held-out 8-way', 'Seen 32-way balanced', 'Core 40-way', 'Wearable-102 12-way',
                          'ID on held-out'])
        self.assertEqual((e['u8']['chance'], e['seen_ba']['chance'], e['core_40']['chance'], e['wearable_12']['chance']),
                         (1 / 8, 1 / 32, 0.025, 1 / 12))
        self.assertEqual(f'{100 * e["wearable_12"]["chance"]:.2f}', '8.33')
        self.assertTrue(e['core_40']['separate_page'])
        self.assertEqual((e['id_held_out']['chance'], e['id_held_out']['defined']), (None, False))

    def test_the_name_key_is_the_plans(self):
        section = self.plan.split('4. **Name key.**', 1)[1].split('5. **Cards.**', 1)[0]
        rows = [[c.strip().replace('**', '') for c in line.strip().strip('|').split('|')]
                for line in section.splitlines() if line.strip().startswith('|')][2:]
        mine = [(r['site_name'], r['export_codes']) for r in self.payload['name_key'] if r['in_page_key']]
        self.assertEqual(mine, [tuple(r) for r in rows])
        crop = next(r for r in self.payload['name_key'] if r['site_name'] == 'cropped-spectrum match (no training)')
        self.assertEqual({(c['study'], c['code']) for c in crop['codes']},
                         {('cca_diagnostics', 'SUBSPACE-CROP'), ('cca_adapter', 'CCA-CROP')})
        wear = self.payload['studies']['wearable_transfer']['display_names']
        self.assertEqual(wear['CCA-CROP'], 'cropped-spectrum check (Wearable-102)')
        placed = [(c['study'], c['code']) for r in self.payload['name_key'] for c in r['codes']]
        given = [(s, c) for s, b in self.payload['studies'].items() for c in b['display_names']]
        self.assertEqual(sorted(placed), sorted(given))

    def test_each_card_names_its_own_interval(self):
        s = self.payload['studies']
        for study in ('ref', 'ref2', 'softmax', 'phase_jitter', 'phase_ramp'):
            im = s[study]['interval_method']
            self.assertEqual((im['seed'], im['draws'], im['level']), (20261007, 2000, 0.95), study)
            self.assertIn('hierarchical paired bootstrap', im['method'])
        for study in ('cca_diagnostics', 'cca_adapter', 'wearable_transfer'):
            im = s[study]['interval_method']
            self.assertEqual((im['seed'], im['draws'], im['level']), (20261015, 2000, 0.95), study)
            self.assertIn('person bootstrap', im['method'])

    def test_the_short_answer_and_card_figures_print_from_these_values(self):
        s = self.payload['studies']
        ad, w = s['cca_adapter'], s['wearable_transfer']
        gain = ad['contrasts']['RAW-RESIDUAL minus CCA-RAW/u8']
        self.assertEqual((pct2(ad['levels']['RAW-RESIDUAL/u8']['estimate']), pct2(ad['levels']['CCA-RAW/u8']['estimate'])),
                         ('86.15', '80.90'))
        self.assertEqual((pp2(gain['estimate']), pct2(gain['interval'][0]), pct2(gain['interval'][1])),
                         ('+5.24', '3.91', '6.62'))
        dry, wet = w['contrasts']['RAW-RESIDUAL_minus_CCA-RAW/dry'], w['contrasts']['RAW-RESIDUAL_minus_CCA-RAW/wet']
        self.assertEqual((pp2(dry['estimate']), pp2(dry['interval'][0]), pct2(dry['interval'][1])), ('+0.07', '-0.71', '0.91'))
        self.assertEqual((pp2(wet['estimate']), pp2(wet['interval'][0]), pct2(wet['interval'][1])), ('-0.61', '-1.48', '0.23'))
        ref = s['ref']['levels']['L0-FS-REF/u8']
        self.assertEqual((pct2(ref['estimate']), pct2(ref['interval'][0]), pct2(ref['interval'][1])),
                         ('39.00', '36.07', '41.78'))
        self.assertEqual(pct2(s['phase_ramp']['levels']['FS-REF/u8']['estimate']), '30.56')
        self.assertEqual(f'{ad["protection"]["protected_margin"]:.1f}', '0.2')
        self.assertEqual(ad['protection']['protected_margin'], 0.200001)
        self.assertEqual((pct2(ad['transitions']['u8']['wrong_to_right']), pct2(ad['transitions']['u8']['right_to_wrong'])),
                         ('7.39', '2.14'))
        self.assertEqual(ad['transitions']['u8']['denominator'], 'all held-out decisions')
        diag = s['cca_diagnostics']['contrasts']['SUBSPACE-CROP minus CHANNEL-JOINT/u8']
        self.assertEqual(pp2(diag['estimate']), '+17.98')
        self.assertEqual(diag['flags']['bundles'],
                         ['cross-channel mixing', 'fitting the reference coefficients', 'aggregation'])
        a2 = w['cca_definition']
        self.assertEqual((pct2(w['levels']['CCA-RAW/dry']['estimate']), pct2(w['levels']['CCA-RAW/wet']['estimate']),
                          pct2(a2['dry_vs_wet_cca']['dry']['estimate']), pct2(a2['dry_vs_wet_cca']['wet']['estimate'])),
                         ('65.38', '81.65', '65.47', '81.56'))

    def test_one_set_of_scores_under_one_name(self):
        s = self.payload['studies']
        for e in ('u8', 'seen_ba'):
            self.assertEqual(s['cca_adapter']['levels'][f'CCA-CROP/{e}']['interval'],
                             s['cca_diagnostics']['levels'][f'SUBSPACE-CROP/{e}']['interval'])
            self.assertEqual(s['cca_adapter']['levels'][f'CCA-RAW/{e}']['estimate'],
                             s['cca_diagnostics']['levels'][f'CCA-RAW/{e}']['estimate'])
        self.assertEqual(s['ref']['levels']['CCA/u8']['estimate'], s['cca_diagnostics']['levels']['CCA-RAW/u8']['estimate'])

    def test_the_rights_and_credits(self):
        r = self.payload['rights']
        self.assertEqual((r['datasets']['beta']['license'], r['datasets']['wearable_102']['license']),
                         ('CC BY 4.0', 'CC BY 4.0'))
        self.assertNotIn('v3', r['datasets']['beta']['citation'])
        self.assertTrue(r['datasets']['wearable_102']['readme'].endswith('/Readme.pdf'))
        self.assertIn('noncommercial', r['datasets']['wearable_102']['consent_scope'])
        self.assertEqual(r['corrigendum']['revision'], 'd4290c0200db8a104e0f557349dc49f90ba79506')
        self.assertEqual(r['cbramod']['method_page'], '/methods/cbramod/')

    def test_the_prose_this_file_adds(self):
        for trail, text in ex.strings(self.payload):
            if ex.authored(trail) and not trail.endswith('.<key>'):
                self.assertIsNone(ex.HEDGE.search(text), trail)
                self.assertIsNone(ex.VERSION_LABEL.search(text), trail)
                self.assertIsNone(ex.MONTH_LABEL.search(text), trail)
        bad = copy.deepcopy(self.payload)
        bad['scope'] += ' The correction is a learned head, not a new scorer.'
        with self.assertRaises(ValueError):
            ex.prose_check(bad, set())
        bad = copy.deepcopy(self.payload)
        bad['scope'] += ' It ranks first.'
        with self.assertRaises(ValueError):
            ex.prose_check(bad, set())

    # ------------------------------------------------------------------ refusals
    def test_a_pin_changed_in_one_place_only_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['blocks']['query']['pins']['ref_export']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(m)

    def test_an_export_the_readings_did_not_verify_is_refused(self):
        m = copy.deepcopy(MANIFEST)

        def edit(readings):
            entry = next(e for e in readings if e['id'] == 'Phase jitter')
            for a in entry['result']['files_for_public_assets']:
                if a['path'].endswith('phase-jitter-v1.json'):
                    a['sha256_actual'] = '1' * 64
        self.repin(m, None, 'readings', edit)
        with self.assertRaisesRegex(ValueError, 'readings verified another export'):
            build(m)

    def test_a_wrong_declared_edit_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['declaredEdits']['ref']['edits'] = m['declaredEdits']['ref']['edits'][1:]
        with self.assertRaises(ValueError):
            build(m)

    def test_the_audit_catches_a_changed_figure(self):
        def nudge(p):
            lv = p['studies']['cca_adapter']['levels']['RAW-RESIDUAL/u8']
            lv['estimate'] = math.nextafter(lv['estimate'], 1.0)
        with self.served(nudge), self.assertRaises(au.AuditFailure):
            au.audit()

    def test_the_audit_catches_a_missing_an_extra_and_an_unruled_value(self):
        edits = (lambda p: p['studies']['phase_ramp']['contrasts'].pop('S7'),
                 lambda p: p['cohort'].update(extra=1),
                 lambda p: p['studies']['ref']['checks'].update(note='an unreviewed claim'),
                 lambda p: p['studies']['phase_jitter']['caveats'].__setitem__(0, 'reworded'),
                 lambda p: p['studies']['softmax']['undefined'].pop())
        for edit in edits:
            with self.served(edit), self.assertRaises((au.AuditFailure, KeyError)):
                au.audit()

    def test_the_audit_refuses_copies_that_differ(self):
        with self.served(lambda p: None) as _:
            paths = au.SERVED
            paths[1].write_bytes(paths[1].read_bytes() + b' ')
            with self.assertRaises(au.AuditFailure):
                au.audit()


if __name__ == '__main__':
    unittest.main()
