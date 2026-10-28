"""The SSVEP follow-ups release, cards 8 to 14: what must follow from the pinned research records, and what stays out."""
import copy
import hashlib
import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_ssvep_followups_export as au
import export_ssvep_followups_update as ex
import test_validate_public as tvp
from ssvep_followups import blocks_cca, blocks_practical

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
PLAN = ex.PROJECT / 'research/site_release_plan_20261028/Release Layout Plan v3.md'
RELEASED_REVIEW = ex.PROJECT / 'research/publication_review_20261020'
RELEASED_SHA = '197028bdc4dadd9713f6d408bb64204147fdfe39a686e7e119e4988aaf863ee0'
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五|五成五',
                              re.IGNORECASE)
HASH = re.compile(r'[0-9a-f]{64}')


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pct(x, nd=2):
    return f'{100 * x:.{nd}f}'


def pp(x, nd=2):
    return f'{100 * x:+.{nd}f}'


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
class SsvepFollowupsRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = ex.build(ex.MANIFEST.read_bytes())
        cls.plan = PLAN.read_text()
        cls.s = cls.payload['studies']

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

    def repin(self, manifest, group, name, edit):
        """An edited copy of one pinned input under the temporary root, re-pinned in a copy of the manifest."""
        ref = manifest[group][name]
        obj = json.loads(ex.location(ref['path']).read_bytes())
        edit(obj)
        data = json.dumps(obj).encode()
        path = Path(self.tmp.name) / Path(ref['path']).name
        path.write_bytes(data)
        ref['path'], ref['sha256'] = str(path), digest(data)

    def level(self, study, lid):
        return self.s[study]['levels'][lid]

    def con(self, study, cid):
        return self.s[study]['contrasts'][cid]

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
        self.assertGreater(audit['figures_compared'], 2500)
        self.assertGreater(audit['export_codes_resolved'], 400)

    def test_the_served_copies_are_byte_identical(self):
        self.assertEqual(ex.OUTPUTS[0].read_bytes(), ex.OUTPUTS[1].read_bytes())

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_released_file_keeps_its_bytes(self):
        """D28: new-ssvep-frequencies-update.json is the 2026-10-20 release as released, in both served copies."""
        released_audit = json.loads((RELEASED_REVIEW / 'new-ssvep-frequencies-export-audit.json').read_text())
        released_manifest = (RELEASED_REVIEW / 'new-ssvep-frequencies-release-manifest.json').read_bytes()
        self.assertEqual(released_audit['export_sha256'], RELEASED_SHA)
        self.assertEqual(released_audit['manifest_sha256'], digest(released_manifest))
        for p in au.RELEASED_SERVED:
            self.assertEqual(digest(p.read_bytes()), released_audit['export_sha256'], p)
        self.assertEqual(MANIFEST['published']['released']['sha256'], RELEASED_SHA)
        self.assertEqual(self.payload['provenance']['released_file']['sha256'], RELEASED_SHA)
        for m in MANIFEST['blocks'].values():
            for r in m['pins'].values():
                if r['path'].endswith('new-ssvep-frequencies-update.json'):
                    self.assertEqual(r['sha256'], RELEASED_SHA)
        released = json.loads(au.RELEASED_SERVED[0].read_bytes())
        self.assertEqual(released['placement']['cards'][7],
                         {'card': 8, 'anchor': 'cross-spectral', 'studies': [], 'status_only': True})

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-ssvep-followups-update-v1')
        self.assertEqual(p['release_id'], 'ssvep-followups-update-20261028')
        self.assertEqual(p['generated_at'], '2026-10-28')
        self.assertEqual(p['status'], 'aggregate_preview')
        self.assertEqual(list(p['studies']), list(ex.STUDIES))
        for k in ('placement', 'endpoints', 'interval_methods', 'interval_adjustment', 'name_key', 'shared_estimates',
                  'engineering_disclosures', 'rights', 'release_record', 'not_published', 'provenance'):
            self.assertIn(k, p)
        self.assertEqual(p['provenance']['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(list(p['provenance']['source_export_sha256']), list(p['studies']) + ['cpu_components'])
        for study, block in p['studies'].items():
            self.assertEqual(p['provenance']['source_export_sha256'][study], block['source_sha256'])
        cards = p['placement']['cards']
        self.assertEqual([(c['card'], c['anchor']) for c in cards],
                         [(8, 'cross-spectral'), (9, 'eigenvalue-pooling'), (10, 'harmonic-pooling'),
                          (11, 'practical-settings'), (12, 'harmonic-gap'), (13, 'fixed-decay'), (14, 'rising-weights')])
        self.assertEqual(cards[0]['supersedes'], {'release_id': 'new-ssvep-frequencies-update-20261020',
                                                  'file': 'new-ssvep-frequencies-update.json', 'entry': 'status_only'})
        self.assertFalse(any('supersedes' in c for c in cards[1:]))
        self.assertFalse(p['placement']['leaderboard'])
        self.assertEqual((p['placement']['new_page_count'], p['placement']['new_dataset_count'],
                          p['placement']['new_model_count']), (0, 0, 0))

    def test_the_endpoints_per_card(self):
        """Plan section 2.1: held-out 8 to 14; seen-32 8 to 11, 13, 14; Wearable-102 10, 12, 13, 14."""
        e = {x['id']: x for x in self.payload['endpoints']}
        self.assertEqual(e['u8']['cards'], [8, 9, 10, 11, 12, 13, 14])
        self.assertEqual(e['seen_ba']['cards'], [8, 9, 10, 11, 13, 14])
        self.assertEqual(e['wearable_12']['cards'], [10, 12, 13, 14])
        self.assertEqual((e['u8']['chance'], e['seen_ba']['chance'], e['wearable_12']['chance']), (1 / 8, 1 / 32, 1 / 12))
        by_card = {c['card']: c['endpoints'] for c in self.payload['placement']['cards']}
        self.assertEqual(by_card[12], ['u8', 'dry', 'wet'])
        self.assertEqual(by_card[11], ['u8', 'seen_ba'])

    def test_the_source_pins_are_the_plans(self):
        section = self.plan.split('**What the exporter reads.**', 1)[1].split('Release status is taken', 1)[0]
        prefixes = dict(re.findall(r'^\| (.+?) \| (?:summary )?`([0-9a-f]{8})…`', section, re.MULTILINE))
        src = self.payload['provenance']['source_export_sha256']
        for row, study in (('xspec aggregate', 'xspec'), ('coherence aggregate', 'coherence_eigen'),
                           ('B/D aggregate', 'practical_settings'), ('harmonic gap', 'harmonic_gap'),
                           ('fixed decay', 'fixed_decay'), ('rising weights', 'rising_weights')):
            self.assertTrue(src[study].startswith(prefixes[row]), study)
        ac = next(v for k, v in prefixes.items() if k.startswith('A/C'))
        self.assertTrue(src['harmonic_pooling'].startswith(ac) and src['harmonic_pooling_wearable'].startswith(ac))
        timing = next(v for k, v in prefixes.items() if k.startswith('timing handoff'))
        self.assertTrue(self.payload['provenance']['handoff_sha256']['cpu_components'].startswith(timing))
        self.assertEqual(src['xspec'], '272bac552fdf509b4cc9bae930782de6a5673194a4989bcbdcbef3b4f1214a0c')

    def test_the_manifest_pins_what_the_block_modules_pin(self):
        for m, module in ex.MODULES.items():
            self.assertEqual(MANIFEST['blocks'][m]['pins'], {k: dict(v) for k, v in module.PINS.items()}, m)
        refs = ex.input_refs(MANIFEST)
        self.assertTrue(all(digest(ex.location(r['path']).read_bytes()) == r['sha256'] for r in refs))
        # Every study's handoff, review and approval are pinned; the handoffs are never copied into the file.
        for study, h in MANIFEST['handoffContext'].items():
            self.assertEqual(h['role'], 'context only, never a copy source')
            self.assertNotIn(Path(h['path']).name, ex.OUTPUTS[0].read_text())

    # ------------------------------------------------------------------ the boundary
    def test_validate_public_passes_and_still_refuses(self):
        tvp.validate_public(self.payload)
        for edit in (lambda p: p['placement'].update(note='/Users/someone/run/x'),
                     lambda p: p['studies']['xspec']['levels']['XS-RIDGE/u8'].update(note='sub-007 excluded'),
                     lambda p: p['studies']['fixed_decay'].update(subjectResults=[])):
            bad = copy.deepcopy(self.payload)
            edit(bad)
            with self.assertRaises(ValueError):
                tvp.validate_public(bad)

    def test_no_55_tied_to_the_thread(self):
        for v in numbers(self.payload):
            self.assertGreater(abs(v - 11 / 20), 1e-12)
            self.assertGreater(abs(v - 55), 1e-9)
        for t in texts(self.payload):
            if not HASH.fullmatch(t):
                self.assertIsNone(CONFIDENCE_TOKEN.search(t), t)
        for k in keys(self.payload):
            self.assertIsNone(re.search(r'fifty|05{2}|prediction|confidence_figure|^thread$|thread_bet|comment', k,
                                        re.I), k)
        # The thread and its bet stay on card 4 of the released file (D23): no URL, no bet, no 39% line here.
        body = ex.OUTPUTS[0].read_text()
        self.assertIsNone(re.search(r'huggingface|/posts/|hugging face|\bbet\b', body, re.I))
        self.assertNotIn(0.39, numbers(self.payload))
        # The review records of this release carry the figure nowhere either, apart from hashes.
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            self.assertIsNone(CONFIDENCE_TOKEN.search(HASH.sub('', path.read_text())), path.name)
        # A legitimate figure with the digit pair is kept at full precision (R5 M7: the token rule is not a scan).
        window = self.con('practical_settings', 'w125-c4/FBCCA-M3-N7-H5 minus w500-c4/FBCCA-M3-N7-H5/u8')
        self.assertEqual(pp(window['estimate'], 4), '-55.3929')

    def test_the_commenter_is_not_named(self):
        for t in texts(self.payload):
            self.assertIsNone(blocks_cca.REFUSED_TEXT.search(t), t)
        # The review records pass the same rule, read through blocks_cca.REFUSED_TEXT (no literal of the name here).
        self.assertIsNone(blocks_cca.REFUSED_TEXT.search(ex.EXPORT_AUDIT.read_text()))
        for trail, value, key in leaves(MANIFEST):
            text = key if key is not None else value
            if not isinstance(text, str):
                continue
            if key is None and trail[-1] == 'path':
                # A pinned research file's own name may carry a host token ("TRX Synthetic Receipt.json"); the
                # manifest is never served and nothing else of the rule may match a path.
                hits = {m.group(0).lower() for m in blocks_cca.REFUSED_TEXT.finditer(text)}
                self.assertLessEqual(hits, {'trx'}, text)
            else:
                self.assertIsNone(blocks_cca.REFUSED_TEXT.search(text), trail)

    def test_no_private_path_name_or_host(self):
        text = ex.OUTPUTS[0].read_text()
        self.assertIsNone(re.search(r'/(?:Users|home|Volumes|mnt|media|private|tmp|srv|root)/', text))
        for name in ('trx50', 'trx', 'gal4', 'bci_arena', 'bigdata', 'twu', 'bciarena_route3'):
            self.assertIsNone(re.search(rf'(?<![a-z0-9]){name}(?![a-z0-9])', text, re.I), name)
        private = ex.private_names(ex.module_docs(MANIFEST))
        self.assertGreaterEqual(len(private), 4)
        for n in private:
            self.assertIsNone(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.I), n)
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            self.assertIsNone(re.search(r'/(?:Users|home|Volumes|mnt)/', path.read_text()), path.name)

    def test_no_host_label_on_the_cpu_components(self):
        """D25: warm single-thread component medians, never summed, no host label."""
        for t in texts(self.payload):
            self.assertIsNone(re.search(r'threadripper|ryzen|(?<![\d.])7965(?!\d)|epyc|xeon|\bamd\b|ubuntu|linux|darwin',
                                        t, re.I), t)
        cpu = self.s['practical_settings']['cpu_components']
        self.assertEqual(cpu['label']['en'], 'components; not sensor-to-decision or online latency')
        m = cpu['measurement']
        self.assertEqual((m['threads'], m['measured_calls'], m['warmup_calls_excluded'], m['summed'], m['gpu']),
                         (1, 3, 1, False, False))
        for k in keys(cpu):
            self.assertNotIn(k, ('total', 'sum', 'end_to_end', 'cpu_ms_per_call', 'cpu_ms_per_trial', 'host'))
        self.assertEqual(len(cpu['groups']), 72)

    def test_nothing_withheld_reaches_the_file(self):
        published = {v for v in numbers(self.payload) if isinstance(v, float)}
        withheld = ex.withheld_values(ex.module_docs(MANIFEST))
        self.assertGreater(len(withheld), 100)
        self.assertFalse(withheld & published)
        for k in ('per_seed_descriptive', 'random_pairing', 'canary_real_label_accuracy_descriptive_only',
                  'retrospective_gap_ratio', 'near_orthogonal_frequencies_hz', 'release_status', 'private_root',
                  'prediction_seal_sha256', 'existing_normalized_xs_ridge_bet', 'point_inside_margin', 'thread_bet',
                  'cpu_ms_per_call', 'elapsed_seconds', 'mean_true_Delta'):
            self.assertNotIn(k, keys(self.payload), k)

    def test_release_status_comes_from_the_approvals(self):
        self.assertFalse(any('pending' in t.lower() for t in texts(self.payload)))
        approvals = self.payload['provenance']['release_approval_sha256']
        for study, src in MANIFEST['sources'].items():
            self.assertEqual(approvals[study], MANIFEST['blocks'][src['block']]['pins'][src['approval']]['sha256'])
            self.assertTrue(Path(MANIFEST['blocks'][src['block']]['pins'][src['approval']]['path']).name.endswith(
                ('release-approval.json', 'Release Approval.json')))

    # ------------------------------------------------------------------ what spans the studies
    def test_the_name_key_is_the_plans(self):
        section = self.plan.split('New site names:', 1)[1].split('- The exporter asserts', 1)[0]
        rows = [[c.strip() for c in line.strip().strip('|').split('|')] for line in section.splitlines()
                if line.strip().startswith('|')][2:]
        split_names = {'coherence head, signed coherence head': ['coherence head', 'signed coherence head'],
                       'cross-spectral ridge, whitened, with quadrature': [
                           'cross-spectral ridge', 'whitened cross-spectral ridge', 'cross-spectral ridge with quadrature']}
        # Source wins over the plan: the released file names CCA-RAW "CCA (no training)".
        conflicts = {('joint CCA', 'CCA-RAW'): 'CCA (no training)'}
        mine = {r['site_name']: {c['code'] for c in r['codes']} for r in self.payload['name_key']}
        self.assertEqual(len(rows), 15)
        for name, cell in rows:
            codes = [c.strip() for c in re.split(r',| = ', cell)]
            codes = ['H3-FLAT' if c == 'H3 flat' else c for c in codes]
            names = split_names.get(name, [name] * len(codes))
            for n, code in zip(names, codes):
                want = conflicts.get((n, code), n)
                self.assertIn(code, mine[want], f'{code} is not under {want!r}')
        placed = [(c['study'], c['code']) for r in self.payload['name_key'] for c in r['codes']]
        given = [(st, c) for st, b in self.s.items() for c in b['display_names']]
        self.assertEqual(sorted(placed), sorted(given))
        self.assertEqual(len(placed), len(set(placed)))

    def test_one_set_of_scores_under_one_name(self):
        released = json.loads(au.RELEASED_SERVED[0].read_bytes())
        for row in self.payload['shared_estimates']:
            values = {self.level(x['study'], x['level'])['estimate'] for x in row['levels']}
            if 'released_level' in row:
                r = row['released_level']
                values.add(released['studies'][r['study']]['levels'][r['level']]['estimate'])
            self.assertEqual(len(values), 1, row)
        # Reused comparators equal card 5's released levels to 1e-12 and carry its card.
        card5 = released['studies']['cca_diagnostics']['levels']
        for study, code in (('xspec', 'CCA-RAW'), ('xspec', 'SHARED-RIDGE'), ('xspec', 'SUBSPACE-CROP'),
                            ('xspec', 'CHANNEL-HARMONIC'), ('coherence_eigen', 'CCA-RAW'),
                            ('coherence_eigen', 'SHARED-RIDGE'), ('harmonic_pooling', 'CCA-RAW')):
            for e in ('u8', 'seen_ba'):
                lv, twin = self.level(study, f'{code}/{e}'), card5[f'{code}/{e}']
                self.assertLessEqual(abs(lv['estimate'] - twin['estimate']), 1e-12)
                self.assertEqual(lv['interval'], twin['interval'])
            self.assertEqual(self.s[study]['reused'][code]['card'], 5)
        card7 = released['studies']['wearable_transfer']['levels']
        for k in ('dry', 'wet'):
            lv = self.level('harmonic_pooling_wearable', f'CCA-RAW/{k}')
            self.assertEqual((lv['estimate'], lv['interval']), (card7[f'CCA-RAW/{k}']['estimate'], None))

    def test_a_shared_level_prints_its_interval_on_its_home_card(self):
        """Every card keeps its source interval; each shared row names the card whose interval the page prints."""
        rows = {(r['site_name'], r['endpoint']): r for r in self.payload['shared_estimates']}
        cca, hs, mc = 'CCA (no training)', 'harmonic sum (no training)', 'matched CCA'
        want = {(cca, 'u8'): (5, True, ['joint CCA']), (cca, 'seen_ba'): (5, False, ['joint CCA']),
                (mc, 'dry'): (7, True, ['joint CCA']), (mc, 'wet'): (7, True, ['joint CCA']),
                (hs, 'u8'): (9, True, None), (hs, 'seen_ba'): (9, True, None),
                (hs, 'dry'): (10, True, None), (hs, 'wet'): (10, True, None),
                ('eigenvalue head', 'u8'): (9, False, None), ('eigenvalue head', 'seen_ba'): (9, False, None),
                ('top-three ridge', 'u8'): (10, False, None), ('top-three ridge', 'seen_ba'): (10, False, None),
                ('filter-bank CCA (seven sub-bands)', 'u8'): (11, False, None),
                ('filter-bank CCA (seven sub-bands)', 'seen_ba'): (11, False, None)}
        self.assertEqual({k: (r['interval_home'], r['intervals_differ_by_card'], r.get('aliases'))
                          for k, r in rows.items()}, want)
        # The home card's interval: card 5's for CCA (reused bit for bit on cards 8 to 11), card 9's for the sum.
        released = json.loads(au.RELEASED_SERVED[0].read_bytes())
        card5 = released['studies']['cca_diagnostics']['levels']['CCA-RAW/u8']['interval']
        for x in rows[(cca, 'u8')]['levels']:
            if x['study'] != 'harmonic_gap':
                self.assertEqual(self.level(x['study'], x['level'])['interval'], card5, x['level'])
        # Card 12 and card 14 keep their own bootstrap's interval for the same scores; card 13's level has none.
        card9 = self.level('coherence_eigen', 'RAW-HARM-SUM/u8')['interval']
        for study, lid in (('harmonic_gap', 'S/u8'), ('rising_weights', 'flat/u8')):
            self.assertIsNotNone(self.level(study, lid)['interval'])
            self.assertNotEqual(self.level(study, lid)['interval'], card9)
        self.assertIsNone(self.level('fixed_decay', 'H3-FLAT/u8')['interval'])
        self.assertNotEqual(self.level('harmonic_gap', 'J/u8')['interval'], card5)
        self.assertIsNone(self.level('harmonic_pooling_wearable', 'CCA-RAW/dry')['interval'])
        # "joint CCA" is an alias, listed in the name key with the primary names it stands for.
        nk = {r['site_name']: r for r in self.payload['name_key']}
        self.assertEqual(nk['joint CCA']['alias_of'], [cca, mc])
        self.assertEqual([r['site_name'] for r in self.payload['name_key'] if 'alias_of' in r], ['joint CCA'])
        self.assertIn('one set of scores, one primary site name; aliases are listed in the name key',
                      ' '.join(MANIFEST['approval']['previewDefaults']))
        with mock.patch.object(ex, 'ALIASES', {}), self.assertRaisesRegex(ValueError, 'another site name'):
            ex.build(ex.MANIFEST.read_bytes())

    def test_the_context_pins_are_bound(self):
        """Receipts an approval binds and the records behind the disclosures: pinned, bound, never copied."""
        ctx = MANIFEST['contextPins']
        self.assertEqual({k: r['sha256'][:8] for k, r in ctx.items()},
                         {'gap_execution_review': '00f114f2', 'gap_binding_receipt': '15d858e8',
                          'gap_synthetic_receipt': '6cc8c84d', 'gap_audit_timing_evidence': '997774e0',
                          'timing_text_approval': '4c758bef', 'timing_launch_receipt': '6ed644f5',
                          'xspec_startup_declaration_review': 'c8a2cf72', 'xspec_scalar_precision_review': '1628962b',
                          'eigen_synthetic_timeout': '77fed0f8'})
        body = ex.OUTPUTS[0].read_text()
        for k, r in ctx.items():
            self.assertEqual(r['role'], 'context only, never a copy source')
            self.assertEqual(digest(ex.location(r['path']).read_bytes()), r['sha256'], k)
            self.assertNotIn(Path(r['path']).name, body)
            self.assertNotIn(r['sha256'], body)
        cpu = MANIFEST['handoffContext']['cpu_components']
        self.assertEqual((cpu['queue_row'], cpu['queue_handoff']['sha256'][:8]), (30, 'db647d6b'))
        self.assertEqual(MANIFEST['componentSource']['cpu_components']['queue_row'], 30)
        self.assertEqual(self.payload['provenance']['handoff_sha256']['cpu_components'], cpu['sha256'])
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual((audit['context_pins_bound'], audit['shared_rows_derived']), (9, 14))

    def test_an_unbound_context_pin_or_queue_row_is_refused(self):
        for edit, message in (
                (lambda m: m['contextPins']['timing_launch_receipt'].update(bound_by='timing_review'),
                 'does not bind its SHA-256'),
                (lambda m: m['contextPins']['eigen_synthetic_timeout'].update(bound_by='eigen_protocol'),
                 'does not name it'),
                (lambda m: m['contextPins']['gap_synthetic_receipt'].update(role='copy source'), 'a copy source'),
                (lambda m: m['handoffContext']['cpu_components'].update(queue_row=33),
                 'another queue row than its source'),
                (lambda m: m['handoffContext']['cpu_components']['queue_handoff'].update(states='a line it lacks'),
                 'does not ask for this study')):
            m = copy.deepcopy(MANIFEST)
            edit(m)
            with self.assertRaisesRegex(ValueError, message):
                build(m)

    def test_each_card_names_its_own_interval(self):
        im = {(r['card'], r['study']): r for r in self.payload['interval_methods']}
        for card, study, draws, seed in ((8, 'xspec', 2000, 20261015), (9, 'coherence_eigen', 2000, 20261015),
                                         (10, 'harmonic_pooling', 2000, 20261015),
                                         (10, 'harmonic_pooling_wearable', 2000, 20261020),
                                         (11, 'practical_settings', 2000, 20261015)):
            self.assertEqual((im[(card, study)]['draws'], im[(card, study)]['seed'], im[(card, study)]['level']),
                             (draws, seed, 0.95), study)
        for card, study, seeds in ((12, 'harmonic_gap', (20261021, 20261022)),
                                   (13, 'fixed_decay', (2026102201, 2026102202)),
                                   (14, 'rising_weights', (2026102501, 2026102502))):
            r = im[(card, study)]
            self.assertEqual((r['draws'], tuple(r['seeds'].values())), (20000, seeds), study)
        self.assertIn('conditional_on', im[(10, 'harmonic_pooling_wearable')])
        adj = self.payload['interval_adjustment']
        self.assertEqual([(a['card'], a['level']) for a in adj['adjusted']], [(12, 1 - 0.05 / 9), (13, 0.9)])
        self.assertEqual(f'{100 * adj["adjusted"][0]["level"]:.2f}', '99.44')
        self.assertEqual(adj['adjusted'][0]['comparisons'], 9)
        self.assertFalse(adj['other_intervals_adjusted'])

    def test_the_engineering_disclosures(self):
        d = self.payload['engineering_disclosures']
        self.assertEqual([(x['card'], x['study']) for x in d],
                         [(8, 'xspec'), (8, 'xspec'), (9, 'coherence_eigen'), (9, 'coherence_eigen')])
        self.assertEqual(sum(x['study'] == 'xspec' for x in d), self.s['xspec']['checks']['pre_score_corrections']['count'])
        self.assertTrue(all(x.get('supervised_accuracy_used') is False for x in d[:2]))
        self.assertIs(d[3]['counted_as_pass'], False)
        self.assertEqual(d[3]['rerun_tests_passed'], 20)
        for x in d:
            self.assertIsNone(re.search(r'seconds|\bsec\b|bigdata|/mnt', x['what'], re.I))

    def test_the_not_published_list(self):
        body = ' '.join(self.payload['not_published'])
        for phrase in ('Per-frequency values of any kind', 'per-seed MLP accuracies', 'canary accuracies',
                       'retrospective gap-to-gain ratio table', 'Run times of whole evaluations',
                       'shares of the 11,200 decisions', 'The commenter’s name.'):
            self.assertIn(phrase, body)

    def test_the_rights_and_credits(self):
        r = self.payload['rights']
        self.assertEqual((r['datasets']['beta']['license'], r['datasets']['wearable_102']['license']),
                         ('CC BY 4.0', 'CC BY 4.0'))
        self.assertEqual(r['datasets']['beta']['cards'], [8, 9, 10, 11, 12, 13, 14])
        # The CPU component medians are timings measured on BETA windows, a clause of their own.
        self.assertEqual(r['datasets']['beta']['published_here'],
                         'Cohort aggregates over the 70 people for cards 8 to 14: levels and paired contrasts with their '
                         'intervals, gap statistics in squared-correlation units, decision-change shares and check '
                         'counts; and CPU component medians measured on BETA windows. No per-person, per-fold, '
                         'per-rotation, per-window or per-frequency value.')
        self.assertEqual(r['datasets']['wearable_102']['cards'], [10, 12, 13, 14])
        fb = r['credits']['fbcca']
        self.assertEqual((fb['short'], fb['reference_url'], fb['method_page'], fb['cards']),
                         ('Chen et al. 2015', 'https://doi.org/10.1088/1741-2560/12/4/046008', '/methods/fbcca/', [11, 13]))
        self.assertIn('Journal of Neural Engineering 12(4):046008, 2015', fb['reference'])
        self.assertFalse(fb['code_distributed'])
        self.assertEqual(fb['used_for'], blocks_practical.RECIPE['en'])

    def test_the_prose_this_file_adds(self):
        for trail, text in ex.strings(self.payload):
            if ex.authored(trail) and not trail.endswith('.<key>'):
                self.assertIsNone(ex.HEDGE.search(text), trail)
                self.assertIsNone(ex.VERSION_LABEL.search(text), trail)
                self.assertIsNone(ex.MONTH_LABEL.search(text), trail)
        for addition in (' The harmonic sum is a fixed rule, not a learned head.', ' It ranks first.',
                         ' See https://huggingface.co/posts/x for the thread.', ' Run on a Threadripper.'):
            bad = copy.deepcopy(self.payload)
            bad['scope'] += addition
            with self.assertRaises(ValueError):
                ex.prose_check(bad, set())

    # ------------------------------------------------------------------ the card leads print from these values
    def test_card_8_and_9_leads(self):
        x = self.s['xspec']
        self.assertEqual((pct(x['levels']['XS-RIDGE/u8']['estimate']), pct(x['levels']['SHARED-RIDGE/u8']['estimate'])),
                         ('68.03', '57.45'))
        c = x['contrasts']['XS-RIDGE minus SHARED-RIDGE/u8']
        self.assertEqual((c['role'], pp(c['estimate']), pct(c['interval'][0]), pct(c['interval'][1])),
                         ('primary', '+10.58', '9.05', '12.28'))
        c = x['contrasts']['XS-MLP minus CCA-RAW/u8']
        self.assertEqual((c['role'], pp(c['estimate']), pp(c['interval'][0]), pp(c['interval'][1])),
                         ('primary', '-8.90', '-11.20', '-6.69'))
        self.assertIs(c['flags']['prespecified_noninferiority_to_CCA'], False)
        self.assertEqual(pct(x['levels']['XS-MLP/u8']['estimate']), '72.00')
        gaps = x['descriptive_gaps']
        self.assertEqual((pp(gaps['XS-RIDGE-W minus CCA-RAW/u8']['estimate']),
                          pp(gaps['XS-RIDGE-W minus CCA-RAW/seen_ba']['estimate'])), ('-0.91', '-3.35'))
        self.assertNotIn('interval', gaps['XS-RIDGE-W minus CCA-RAW/u8'])
        q = x['contrasts']['XS-RIDGE-Q minus XS-RIDGE/u8']
        self.assertEqual((pp(q['estimate']), pp(q['interval'][0]), pp(q['interval'][1])), ('+0.42', '-0.10', '+0.89'))
        self.assertTrue(all(x['levels'][f'{a}/seen_ba']['estimate'] < x['levels']['CCA-RAW/seen_ba']['estimate']
                            for a in ('XS-RIDGE', 'XS-RIDGE-W', 'XS-MLP', 'XS-RIDGE-Q')))
        e = self.s['coherence_eigen']
        self.assertEqual(pct(e['levels']['EIG-RAW/u8']['estimate']), '82.97')
        c = e['contrasts']['EIG-RAW minus CCA-RAW/u8']
        self.assertEqual((pp(c['estimate'], 3), pct(c['interval'][0], 3), pct(c['interval'][1], 3)),
                         ('+2.071', '1.089', '3.125'))
        self.assertTrue(c['flags']['strict_5pp_equivalence'])
        c = e['contrasts']['EIG-RAW minus RAW-HARM-SUM/u8']
        self.assertEqual((pp(c['estimate'], 3), pp(c['interval'][0], 3), pp(c['interval'][1], 3)),
                         ('+0.071', '-0.447', '+0.616'))
        c = e['contrasts']['EIG-SPEC minus SPEC-HARM-SUM/u8']
        self.assertEqual(c['interval'][0], -2.2321428571386387e-06)
        self.assertEqual((pp(c['estimate'], 3), pp(c['interval'][0], 5)), ('+0.527', '-0.00022'))
        self.assertEqual(c['flags']['bound_below_two_decimals'], ['lower'])
        self.assertEqual(e['checks']['fits']['total'], 361)
        self.assertEqual(e['checks']['cca_identity']['pairs'], 448000)

    def test_card_10_and_11_leads(self):
        a = self.s['harmonic_pooling']['contrasts']
        for cid, want in (('RAW-LEAD3-RIDGE minus RAW-HARM-SUM/u8', ('+0.3036', '-0.1250', '+0.7768')),
                          ('EIG-RAW minus RAW-LEAD3-RIDGE/u8', ('-0.2321', '-0.5714', '+0.1071')),
                          ('RAW-HARM-ALLSUM minus RAW-HARM-SUM/u8', ('-0.8750', '-1.4196', '-0.3750')),
                          ('RAW-HARM-MAX minus RAW-HARM-SUM/u8', ('-7.7232', '-9.1163', '-6.4554')),
                          ('JOINT-ALLSUM minus CCA-RAW/u8', ('+1.1161', '+0.2587', '+1.9375')),
                          ('EIG-JOINT minus JOINT-ALLSUM/u8', ('+0.2679', '-0.0268', '+0.5536'))):
            c = a[cid]
            self.assertEqual((pp(c['estimate'], 4), pp(c['interval'][0], 4), pp(c['interval'][1], 4)), want, cid)
        w = self.s['harmonic_pooling_wearable']['contrasts']
        self.assertEqual(pp(w['EIG-RAW minus RAW-HARM-SUM/dry']['estimate'], 4), '-0.3595')
        self.assertEqual(pp(w['EIG-RAW minus RAW-HARM-SUM/wet']['estimate'], 4), '+0.3595')
        dry = w['EIG-JOINT minus JOINT-ALLSUM/dry']
        self.assertTrue(dry['flags']['levels_equal'])        # the page prints 0.00, never -0.00
        b = self.s['practical_settings']
        self.assertEqual(pct(b['levels']['w500-c8/FBCCA-M3-N7-H5/u8']['estimate'], 4), '90.2143')
        for cid, want in (('w500-c8/FBCCA-M3-N7-H5 minus w500-c8/RAW-HARM-SUM-H3/u8', ('+7.3125', '+5.1516', '+9.4734')),
                          ('w500-c8/FBCCA-M3-N7-H5 minus w500-c8/CCA-RAW-H3/u8', ('+9.3125', '+6.8391', '+11.7143')),
                          ('w500-c4/EIG-RAW6-RIDGE minus w500-c4/RAW-HARM-SUM-H3/u8', ('+0.8750', '+0.0804', '+1.6964')),
                          ('w125-c4/FBCCA-M3-N7-H5 minus w500-c4/FBCCA-M3-N7-H5/u8', ('-55.3929', '-57.4558', '-53.2768')),
                          ('w250-c4/FBCCA-M3-N7-H5 minus w250-c8/FBCCA-M3-N7-H5/u8', ('-5.4821', '-7.1257', '-3.8391'))):
            c = b['contrasts'][cid]
            self.assertEqual((pp(c['estimate'], 4), pp(c['interval'][0], 4), pp(c['interval'][1], 4)), want, cid)
        self.assertEqual(pp(b['contrasts']['w125-c8/FBCCA-M3-N7-H5 minus w500-c8/FBCCA-M3-N7-H5/u8']['estimate'], 4),
                         '-57.7232')
        self.assertEqual(b['design']['primary']['B'], ['w500-c8/FBCCA-M3-N7-H5 minus w500-c8/RAW-HARM-SUM-H3/u8'])
        self.assertEqual(len(b['contrasts']), 41)
        self.assertEqual(sum(c['role'] == 'primary' for c in b['contrasts'].values()), 7)
        self.assertEqual(b['grid']['cells'], ['w125-c4', 'w125-c8', 'w250-c4', 'w250-c8', 'w500-c4', 'w500-c8'])
        cpu = b['cpu_components']['groups']
        fb1, fb8 = cpu['w500-c8/1/fbcca'], cpu['w500-c8/8/fbcca']
        self.assertEqual((f'{fb1["wall_ms_per_call"]["median"]:.4f}', f'{fb1["wall_ms_per_call"]["min"]:.4f}',
                          f'{fb1["wall_ms_per_call"]["max"]:.4f}', f'{fb8["wall_ms_amortised"]["median"]:.4f}'),
                         ('7.4541', '6.9932', '8.0188', '2.8177'))
        for comp, want in (('raw_geometry', '1.3860'), ('raw_filter', '1.2281'), ('top3_readout', '0.0303'),
                           ('eigenvalue_readout', '0.0595')):
            self.assertEqual(f'{cpu[f"w500-c8/1/{comp}"]["wall_ms_per_call"]["median"]:.4f}', want, comp)

    def test_card_12_to_14_leads(self):
        g = self.s['harmonic_gap']
        self.assertEqual([pct(g['levels'][f'{k}/u8']['estimate']) for k in ('J', 'B', 'S')], ['80.90', '80.94', '82.90'])
        for cid, want in (('B minus J/u8', ('+0.0357', '-0.0982', '+0.1875')),
                          ('S minus B/u8', ('+1.9643', '+1.0625', '+2.9554')),
                          ('S minus B/dry', ('+0.6618', '-0.2451', '+1.5850')),
                          ('S minus B/wet', ('+1.1683', '+0.3513', '+2.0135'))):
            c = g['contrasts'][cid]
            self.assertEqual((pp(c['estimate'], 4), pp(c['interval'][0], 4), pp(c['interval'][1], 4)), want, cid)
            self.assertEqual(c['interval_level'], 1 - 0.05 / 9)
        gap = g['gap']
        self.assertEqual([f'{gap[f"G true minus mean distractor/{e}"]["estimate"]:.6f}' for e in ('u8', 'dry', 'wet')],
                         ['0.061708', '0.023174', '0.043520'])
        self.assertEqual(g['reference_check']['BETA'], {'candidates': 40, 'at_or_below_threshold': 8,
                                                        'above_threshold': 32, 'reference_full_rank': True})
        self.assertEqual(g['transitions']['decisions'], 11200)
        self.assertEqual(g['win_fractions']['u8']['accuracy'], False)
        d = self.s['fixed_decay']
        c = d['contrasts']['H3-DECAY minus H3-FLAT/u8']
        self.assertEqual((pct(d['levels']['H3-FLAT/u8']['estimate']), pct(d['levels']['H3-DECAY/u8']['estimate']),
                          pp(c['estimate'], 4), pp(c['interval'][0], 4), pp(c['interval'][1], 4)),
                         ('82.90', '79.91', '-2.9911', '-3.7679', '-2.2857'))
        eq = d['equivalence']
        self.assertEqual((pp(eq['interval'][0], 4), pp(eq['interval'][1], 4), eq['met']), ('-3.6429', '-2.3839', False))
        c = d['contrasts']['FBCCA-DECAY minus FBCCA-FLAT/u8']
        self.assertEqual((pct(d['levels']['FBCCA-FLAT/u8']['estimate']), pct(d['levels']['FBCCA-DECAY/u8']['estimate']),
                          pp(c['estimate'], 4)), ('85.01', '90.21', '+5.2054'))
        # Source over plan: seen-32 is -0.05718749999999998, which prints -5.7187 at four decimals (plan: -5.7188).
        seen = d['contrasts']['H3-DECAY minus H3-FLAT/seen_ba']['estimate']
        self.assertEqual((seen, pp(seen), pp(seen, 4)), (-0.05718749999999998, '-5.72', '-5.7187'))
        self.assertEqual(pp(d['contrasts']['FBCCA-DECAY minus FBCCA-FLAT/seen_ba']['estimate'], 4), '+7.3996')
        r = self.s['rising_weights']
        c = r['contrasts']['literal_rise minus flat/u8']
        self.assertEqual((pct(r['levels']['literal_rise/u8']['estimate']), pp(c['estimate'], 4), pp(c['interval'][0], 4),
                          pp(c['interval'][1], 4), c['role']), ('83.76', '+0.8571', '+0.2946', '+1.4464', 'primary'))
        self.assertTrue(r['criterion']['met'])
        dry = r['contrasts']['literal_rise minus flat/dry']
        self.assertEqual((pct(r['levels']['flat/dry']['estimate']), pct(r['levels']['literal_rise/dry']['estimate']),
                          pp(dry['estimate'], 4)), ('66.04', '64.89', '-1.1438'))
        self.assertEqual(pp(r['contrasts']['literal_rise minus flat/wet']['estimate'], 4), '-0.4330')
        self.assertEqual(pp(r['contrasts']['literal_rise minus flat/seen_ba']['estimate'], 4), '+0.4888')

    # ------------------------------------------------------------------ refusals
    def test_a_pin_changed_in_one_place_only_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['blocks']['weights']['pins']['rise_export']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(m)

    def test_a_handoff_its_queue_row_does_not_name_is_refused(self):
        m = copy.deepcopy(MANIFEST)

        def edit(queue):
            queue['rows'][21]['source_sha256'] = '1' * 64
        self.repin(m, 'planning', 'queue', edit)
        with self.assertRaisesRegex(ValueError, 'queue row 21 names another handoff'):
            build(m)

    def test_a_changed_released_file_is_refused(self):
        m = copy.deepcopy(MANIFEST)

        def edit(audit):
            audit['export_sha256'] = '2' * 64
        self.repin(m, 'published', 'releasedAudit', edit)
        with self.assertRaisesRegex(ValueError, 'the released file is not the one the 2026-10-20 export audit names'):
            build(m)

    def test_a_wrong_declared_edit_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['declaredEdits']['xspec']['not_selected'] = m['declaredEdits']['xspec']['not_selected'][1:]
        with self.assertRaises(ValueError):
            build(m)

    def test_the_audit_catches_a_changed_figure(self):
        def nudge(p):
            lv = p['studies']['xspec']['levels']['XS-RIDGE/u8']
            lv['estimate'] = math.nextafter(lv['estimate'], 1.0)
        with self.served(nudge), self.assertRaises(au.AuditFailure):
            au.audit()

    def test_the_audit_catches_a_missing_an_extra_and_an_unruled_value(self):
        edits = (lambda p: p['studies']['harmonic_gap']['contrasts'].pop('S minus B/u8'),
                 lambda p: p['placement'].update(extra=1),
                 lambda p: p['studies']['practical_settings']['checks'].update(note='an unreviewed claim'),
                 lambda p: p['studies']['fixed_decay']['equivalence'].update(met=True),
                 lambda p: p['studies']['harmonic_gap']['transitions']['edges']['J to B'].update(wrong_to_right=19),
                 lambda p: p['studies']['practical_settings']['cpu_components']['groups']['w500-c8/1/fbcca'][
                     'wall_ms_per_call'].update(median=1.0),
                 lambda p: p['studies']['xspec']['undefined'].pop())
        for edit in edits:
            with self.served(edit), self.assertRaises(au.AuditFailure) as caught:
                au.audit()
            # Caught by a figure, string or row rule, before the last check (the fresh build) is reached.
            self.assertNotIn('fresh build', str(caught.exception))

    def test_the_audit_binds_the_editorial_strings_by_a_fresh_build(self):
        """The audit derives no editorial wording; its last check requires the served bytes to equal the export's own
        build from the same manifest, so a changed display name, limitation key, name key row or scope is caught."""
        edits = (lambda p: p['studies']['xspec']['display_names'].update({'XS-RIDGE': 'cross ridge'}),
                 lambda p: p['studies']['xspec']['limitations_keys'].pop(),
                 lambda p: p['name_key'][2].update(site_name='another name'),
                 lambda p: p.update(scope=p['scope'] + ' More.'))
        for edit in edits:
            with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'fresh build'):
                au.audit()

    def test_the_audit_refuses_copies_that_differ(self):
        with self.served(lambda p: None):
            paths = au.SERVED
            paths[1].write_bytes(paths[1].read_bytes() + b' ')
            with self.assertRaises(au.AuditFailure):
                au.audit()


if __name__ == '__main__':
    unittest.main()
