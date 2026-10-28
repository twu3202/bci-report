"""The NeuroRVQ release: what must follow from the pinned research records, and what must stay out."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_neurorvq_export as au
import export_neurorvq_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
PLAN = ex.PROJECT / 'research/site_release_plan_20261028/Release Layout Plan v3.md'


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


def block(payload, bid):
    return next(b for b in payload['blocks'] if b['id'] == bid)


def arm(payload, bid, aid):
    return next(a for a in block(payload, bid)['arms'] if a['id'] == aid)


class ServedFile(unittest.TestCase):
    """Checks that need only the committed files, so they run in a clone too."""

    def test_the_two_copies_are_one_and_the_audit_names_them(self):
        data = [p.read_bytes() for p in ex.OUTPUTS]
        self.assertEqual(data[0], data[1])
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertEqual(audit['export_sha256'], digest(data[0]))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(json.loads(data[0])['provenance']['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))

    def test_no_private_path_alias_or_withheld_field_in_the_served_file(self):
        body = ex.OUTPUTS[0].read_text()
        payload = json.loads(body)
        self.assertIsNone(ex.LOCAL_ROOTS.search(body))
        for word in ('eugenehp', 'apache', 'bound_files', 'above_chance', 'wall_seconds', 'cpu_seconds', 'peak_rss',
                     'source_cache', 'research/', 'release-approval', 'handoff.md'):
            self.assertNotIn(word, body.lower(), word)
        ex.scrub_check(payload)
        ex.validate_public(payload)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class NeurorvqBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build(MANIFEST)
        cls.docs = ex.load(MANIFEST)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    # ------------------------------------------------------------------ forged inputs, re-pinned
    def get(self, ref):
        data = (ex.PROJECT / ref['path']).read_bytes()
        name = Path(ref['path']).name
        if name.endswith('.json') or name in ('neurorvq_hf.txt', 'neurorvq_repo.txt'):
            return json.loads(data)
        return data.decode()

    def put(self, ref, obj):
        """Write an edited copy under the temporary root, keeping its name, and re-pin it."""
        data = obj.encode() if isinstance(obj, str) else json.dumps(obj).encode()
        rel = ref['path'].split(ex.RESEARCH_ROOT, 1)[1] if ex.RESEARCH_ROOT in ref['path'] else ref['path']
        path = Path(self.tmp.name) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        ref['path'], ref['sha256'] = str(path), digest(data)

    def served(self, edit):
        payload = json.loads(ex.OUTPUTS[0].read_bytes())
        edit(payload)
        data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
        paths = []
        for i in range(2):
            p = Path(self.tmp.name) / f'served-{i}.json'
            p.write_bytes(data)
            paths.append(p)
        return mock.patch.object(au, 'SERVED', tuple(paths))

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
        self.assertEqual(audit['figures_compared'], audit['copied_exactly'] + audit['recomputed'] + audit['nulls_kept'])
        self.assertEqual(audit['copied_exactly'], 23)      # 7 arms x 2 metrics + 3 differences x 3 numbers
        self.assertEqual(audit['nulls_kept'], 9)           # 7 arm intervals, chance macro-F1, the EEGMAT bitwise flag
        self.assertEqual(audit['reviewed_text_sha256'], MANIFEST['reviewedText']['sha256'])
        self.assertEqual(au.text_digest(json.loads(data)), MANIFEST['reviewedText']['sha256'])

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-neurorvq-update-v1')
        self.assertEqual(p['release_id'], 'neurorvq-update-20261028')
        self.assertEqual(p['generated_at'], '2026-10-28')
        self.assertEqual(p['status'], 'aggregate_preview')
        self.assertEqual([b['id'] for b in p['blocks']], ['eegmat', 'mi-rest', 'p300-target'])
        self.assertEqual([[(a['id'], a['label'], a['role']) for a in b['arms']] for b in p['blocks']], [
            [('neurorvq', 'NeuroRVQ backbone', 'probe'), ('band-power', 'band power', 'matched comparator')],
            [('neurorvq', 'NeuroRVQ backbone', 'probe'), ('temporal-means', 'temporal means', 'primary comparator'),
             ('band-power', 'band power', 'descriptive comparator')],
            [('neurorvq', 'NeuroRVQ backbone', 'probe'), ('temporal-means', 'temporal means', 'primary comparator')]])
        pl = p['placement']
        self.assertEqual((pl['page'], pl['anchor'], pl['after']), ('/topics/pilot-studies/', 'neurorvq', 'neurolm-eegmat'))
        self.assertEqual(pl['pointers_from'], ['/protocols/arithmetic-rest/', '/protocols/mi-rest/',
                                               '/protocols/p300-target/'])
        self.assertEqual((pl['pointers_carry_figures'], pl['counted_in_pilots'], pl['leaderboard'], pl['core_matrix_row'],
                          pl['foundation_encoder_table'], pl['method_page'], pl['new_dataset_count'],
                          pl['new_model_count']), (False, False, False, False, False, False, 0, 0))
        pv = p['provenance']
        self.assertEqual(pv['source_export_sha256'], {
            'eegmat': 'bd672fb7035dd8c4347d7a57678c4747e11db21953ae5fe8540171775818e07a',
            'mi-rest': '711faa01804f5a517b66b8f9110c9dbf1ed9d725f09c51cbfe7e6f7ba2e9bce6',
            'p300-target': 'a213f1e80c87941273e2cc5138c1fceb0a73b0731fc17f9232739db0e10db6ed'})
        self.assertEqual(pv['handoff_sha256'], {
            'eegmat': '83db9e1fea94ca9ae31af00314849dc55be8703854a898432626f783c5603bb6',
            'mi-rest': '4013b3e52e472b9fbf0bd0a1d48b94da87bf02453e39fc48833b487f4a6b288c',
            'p300-target': '2fb9710c2bf470614cb06f70cbf65823e522aadcb730355aad64ba9da659e045'})
        self.assertEqual(p['release_record']['research_release_status'],
                         {t: 'PASS_INTERNAL_AGGREGATE_HANDOFF' for t in ex.TASKS})

    def test_the_figures_are_the_audited_ones(self):
        p = self.payload
        want = {('eegmat', 'neurorvq'): (0.6634259259259259, 0.6482198226102802, 66.34, 64.82),
                ('eegmat', 'band-power'): (0.6481481481481483, 0.6050057914535415, 64.81, 60.50),
                ('mi-rest', 'neurorvq'): (0.5508333333333333, 0.5264332778137192, 55.08, 52.64),
                ('mi-rest', 'temporal-means'): (0.7033333333333334, 0.6983863480354476, 70.33, 69.84),
                ('mi-rest', 'band-power'): (0.5883333333333333, 0.5647969284711711, 58.83, 56.48),
                ('p300-target', 'neurorvq'): (0.5039682539682541, 0.47361097417708453, 50.40, 47.36),
                ('p300-target', 'temporal-means'): (0.5396825396825397, 0.5220746452819641, 53.97, 52.21)}
        for (bid, aid), (ba, f1, ba2, f12) in want.items():
            a = arm(p, bid, aid)
            self.assertEqual((a['balanced_accuracy'], a['macro_f1']), (ba, f1), (bid, aid))
            self.assertEqual((r2(a['balanced_accuracy']), r2(a['macro_f1'])), (ba2, f12), (bid, aid))
            self.assertIsNone(a['interval_95'])
        diffs = {'eegmat': (1.53, -3.52, 6.67, True), 'mi-rest': (-15.25, -20.17, -10.25, False),
                 'p300-target': (-3.57, -5.56, -1.51, False)}
        for bid, (d, lo, hi, spans) in diffs.items():
            x = block(p, bid)['paired_difference']
            self.assertEqual((r2(x['difference']), r2(x['interval_95'][0]), r2(x['interval_95'][1])), (d, lo, hi), bid)
            self.assertIs(x['interval_includes_zero'], spans)
            self.assertEqual(x['reading'], ex.SPANS_ZERO if spans else ex.BELOW_ZERO)
        self.assertEqual(block(p, 'mi-rest')['paired_difference']['difference'], -0.1525)
        self.assertEqual(p['chance_level'], {'balanced_accuracy': 0.5, 'macro_f1': None})
        self.assertEqual({k: p['interval'][k] for k in ('level', 'unit', 'resamples', 'seed', 'metric')},
                         {'level': 0.95, 'unit': 'participant', 'resamples': 20000, 'seed': 20261026,
                          'metric': 'balanced accuracy'})

    @unittest.skipUnless(PLAN.exists(), 'the release plan is local-only')
    def test_the_plans_table_rounds_from_these_figures(self):
        plan = PLAN.read_text()
        p = self.payload
        for bid, aids in (('eegmat', ('neurorvq', 'band-power')), ('mi-rest', ('neurorvq', 'temporal-means', 'band-power')),
                          ('p300-target', ('neurorvq', 'temporal-means'))):
            for aid in aids:
                a = arm(p, bid, aid)
                self.assertIn(f'{100 * a["balanced_accuracy"]:.2f}% · {100 * a["macro_f1"]:.2f}%', plan, (bid, aid))
            x = block(p, bid)['paired_difference']
            lo, hi = x['interval_95']
            self.assertIn(f'{ex.pct(x["difference"], 2, True)} pp [{ex.pct(lo, 2, True)}, {ex.pct(hi, 2, True)}]', plan,
                          bid)

    def test_the_cohorts_and_chains(self):
        p = self.payload
        e, m, t = (block(p, b) for b in ex.TASKS)
        self.assertEqual({k: e['cohort'][k] for k in ('people', 'recordings', 'windows', 'channels', 'folds')},
                         {'people': 36, 'recordings': 72, 'windows': 2160, 'channels': 19, 'folds': 5})
        self.assertEqual((m['cohort']['people'], m['cohort']['windows'], m['cohort']['channels']), (10, 1200, 15))
        self.assertEqual((t['cohort']['people'], t['cohort']['windows'], t['cohort']['channels'],
                          t['cohort']['window_seconds']), (21, 2520, 19, 1))
        self.assertEqual(t['cohort']['balance'], {'target': 60, 'non_target': 60, 'unit': 'epochs per person'})
        ec = e['input_chain']
        self.assertEqual((ec['notch_hz'], ec['band_pass_hz'], ec['filter_order'], ec['clip_microvolts'],
                          ec['source_sampling_hz'], ec['sampling_hz'], ec['epoch_demean']),
                         ([50, 60, 100], [0.5, 44.5], 3, 500, 500, 200, False))
        self.assertEqual((m['input_chain']['resample'], m['input_chain']['epoch_demean']), ({'up': 8, 'down': 5}, True))
        self.assertEqual((t['input_chain']['resample'], t['input_chain']['epoch_demean']), ({'up': 2, 'down': 3}, False))
        self.assertEqual([a['dimension'] for b in p['blocks'] for a in b['arms']], [800, 95, 800, 1500, 75, 800, 950])
        self.assertEqual([b['fits'] for b in p['blocks']], [10, 15, 10])
        self.assertEqual([b['core_track']['same_prepared_windows'] for b in p['blocks']], [False, True, True])

    def test_the_model_variant_and_restore(self):
        m = self.payload['model']
        self.assertEqual(m['variant'], 'the released backbone with parameter-free branch normalisation and mean-token '
                                       'pooling')
        self.assertEqual(m['restore'], {'strict': True, 'trained_tensors': 263, 'trained_elements': 5869088,
                                        'checkpoint_tensors': 330, 'checkpoint_elements': 58560632,
                                        'unused_checkpoint_tensors': 67, 'coverage': 1.0})
        self.assertEqual((m['authors_wrapper']['strict_restore'], m['authors_wrapper']['missing_normalisation_tensors']),
                         (False, 8))
        self.assertEqual(m['pooling']['dimension'], 800)
        self.assertEqual(m['checkpoint']['sha256'], 'd14ef4eae2d4594d5f1f709226a3bb5f362afd84b68050d5da0fa0586aea886a')
        self.assertEqual(m['checkpoint']['bytes'], 234352952)
        self.assertEqual(m['checkpoint']['revision'], 'd944b87f44ae0ba2923b2f10d0518f23f6803b76')
        self.assertEqual(m['source_revision'], '926e770d9d16b6aa308404280fa0cc0211a6f9fb')
        self.assertEqual((m['arxiv_id'], m['paper']), ('2510.13068', 'https://arxiv.org/abs/2510.13068'))
        self.assertEqual((m['frozen'], m['fine_tuning'], m['weights_distributed']), (True, False, False))
        body = json.dumps(self.payload)
        self.assertNotRegex(body, r'(?<![\w./-])[vV]\d+\b')       # no version label, the checkpoint file name aside

    def test_only_the_listed_hashes_are_published(self):
        p = copy.deepcopy(self.payload)
        del p['rights']['datasets']        # the released dataset records keep their own source revisions
        hashes = set(re.findall(r'\b[0-9a-f]{40}(?:[0-9a-f]{24})?\b', json.dumps(p)))
        m = MANIFEST
        allowed = {self.payload['model']['checkpoint']['sha256'], self.payload['model']['checkpoint']['revision'],
                   self.payload['model']['source_revision'], self.payload['provenance']['manifest_sha256']}
        for t in ex.TASKS:
            allowed |= {m['research'][t][k]['sha256'] for k in ('audit', 'approval', 'handoff', 'protocol')}
        allowed.add(m['research']['mi-rest']['neuralAudit']['sha256'])
        self.assertLessEqual(hashes, allowed)
        licence = digest((ex.PROJECT / m['model']['codeLicence']['path']).read_bytes())
        self.assertNotIn(licence, json.dumps(self.payload))

    def test_the_licences_per_part(self):
        r = self.payload['rights']
        self.assertEqual((r['code']['licence'], r['weights']['licence']), ('CC BY-NC 4.0', 'CC BY-NC 4.0'))
        self.assertEqual(r['code']['url'], 'https://github.com/KonstantinosBarmpas/NeuroRVQ/blob/'
                                           '926e770d9d16b6aa308404280fa0cc0211a6f9fb/LICENSE')
        self.assertEqual(r['weights']['url'], 'https://huggingface.co/ntinosbarmpas/NeuroRVQ/blob/'
                                              'd944b87f44ae0ba2923b2f10d0518f23f6803b76/LICENSE')
        self.assertIs(r['weights']['same_file_as_code'], True)
        self.assertIs(r['weights']['weights_distributed'], False)
        mvp = json.loads((ex.PROJECT / MANIFEST['published']['coreMatrix']['path']).read_bytes())
        for t in ex.TASKS:
            tr = next(x for x in mvp['tracks'] if x['id'] == ex.TASK[t]['protocol'])
            for k in ex.RIGHTS_FIELDS:
                self.assertEqual(r['datasets'][t][k], tr[k], (t, k))

    def test_the_exposure_is_unknown(self):
        e = self.payload['pretraining_exposure']
        self.assertEqual(e['status'], 'unknown')
        self.assertEqual(e['published_pretraining_list'], {'corpora': 13, 'public': 12, 'proprietary': 1})
        self.assertEqual([(x['task'], x['named_in_list'], x['status']) for x in e['datasets']],
                         [(t, False, 'unknown') for t in ex.TASKS])
        docs = copy.deepcopy(self.docs)
        docs['model']['contract']['core_exposure'][1]['checkpoint_exposure'] = 'not_exposed'
        with self.assertRaisesRegex(ValueError, 'no longer unknown'):
            ex.exposure_block(docs)
        docs = copy.deepcopy(self.docs)
        docs['model']['contract']['pretraining_corpus']['datasets'][0] = 'PhysioNet EEGMAT'
        with self.assertRaisesRegex(ValueError, 'review the exposure'):
            ex.exposure_block(docs)

    def test_the_caveats_and_the_protocols_not_run(self):
        p = self.payload
        ids = [x['id'] for x in p['limitations']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {k for b in p['blocks'] for k in b['caveat_keys']})
        text = {x['id']: x['text'] for x in p['limitations']}
        self.assertIn('eight normalisation tensors', text['variant'])
        self.assertIn('263 trained tensors restore strictly', text['variant'])
        self.assertIn('800 values against 95 band powers on EEGMAT, 1,500 temporal means and 75 band powers',
                      text['dimensions'])
        self.assertIn('There is no random-initialisation arm', text['dimensions'])
        # the input scale: required by the sources for all three tasks, though the plan names only MI and P300 units
        self.assertIn('do not establish the amplitude scale or reference NeuroRVQ was pretrained on', text['input-scale'])
        self.assertIn('Every chain here feeds microvolts as an adaptation', text['input-scale'])
        self.assertIn('the motor-imagery and P300 chains leave all three out', text['input-scale'])
        self.assertIn('No score here reproduces NeuroRVQ’s published pipeline, and none separates the representation '
                      'from an input mismatch', text['input-scale'])
        self.assertIn('EEGMAT is a known development cohort', text['development-cohort'])
        self.assertIn('the EEGMAT block is not an untouched external confirmation', text['development-cohort'])
        self.assertIn('nothing here measures cognitive workload, clinical use, online decoding', text['scope'])
        # the filter runs over the retained first minute of each recording, never the whole recording
        self.assertIn('filters the retained first minute of each recording as one block before cutting it into windows',
                      text['scope'])
        self.assertNotIn('whole recording', json.dumps(p))
        self.assertIn('the P300 cache’s original preparation from the raw files was not re-run', text['units'])
        boundary = block(p, 'eegmat')['audit']['boundary']
        self.assertTrue(boundary.endswith('it read both arms’ values from the producer’s sealed files and did not '
                                          're-extract them.'), boundary)
        self.assertIs(block(p, 'eegmat')['audit']['backbone_values_reextracted'], False)
        self.assertIn('the motor-imagery band power differs from that protocol’s Spectral ridge row, and the P300 '
                      'temporal means from that protocol’s Temporal ridge row', text['input-cache'])
        keys = {b['id']: set(b['caveat_keys']) for b in p['blocks']}
        for bid in ex.TASKS:
            self.assertLessEqual({'input-scale', 'scope', 'exposure', 'variant'}, keys[bid], bid)
        self.assertIn('development-cohort', keys['eegmat'])
        self.assertNotIn('development-cohort', keys['mi-rest'] | keys['p300-target'])
        self.assertEqual(ids, au.LIMITATION_IDS)
        self.assertEqual([x['protocol'] for x in p['protocols_not_run']],
                         ['semantic-target', 'beta-4ch', 'beta-8ch', 'idle', 'sleep-scalp'])
        # each caveat is said once: no caveat sentence repeats in another caveat
        for a in ids:
            for b in ids:
                if a != b:
                    self.assertNotIn(text[a][:60], text[b])

    def test_released_files_are_never_edited(self):
        for ref in MANIFEST['published'].values():
            self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
            if not ref['path'].endswith('mvp.json'):
                self.assertNotIn('neurorvq', (ex.PROJECT / ref['path']).read_text().lower(), ref['path'])

    def test_no_core_or_neurolm_figure_reaches_the_file(self):
        crossed = ex.collision_values(self.docs)
        self.assertGreaterEqual(len(crossed), 40)
        self.assertFalse(crossed & set(ex.numbers(self.payload)))

    def test_measured_compute_and_above_chance_counts_are_absent(self):
        withheld = ex.withheld_values(self.docs)
        self.assertGreaterEqual(len(withheld), 30)
        # Known withheld figures (above-chance counts and fraction, measured seconds), named by the first 16 hex digits
        # of the SHA-256 of their repr so that this public file does not print them.
        held = {hashlib.sha256(repr(v).encode()).hexdigest()[:16] for v in withheld}
        for anchor in ('c6f3ac57944a5314', '670671cd97404156', 'a5eef1f22305b41c', '1f1b57321b1d5199',
                       '78267ce2a01c0971', 'b79e4f534b927dcb', '5ced0a65b54e7840'):
            self.assertIn(anchor, held)
        self.assertFalse(withheld & set(ex.numbers(self.payload)))

    def test_the_commenters_figure_never_appears(self):
        published = set(ex.numbers(self.payload))
        self.assertNotIn(ex.CONFIDENCE_VALUE, published)
        self.assertNotIn(100 * ex.CONFIDENCE_VALUE, published)
        for trail, text in ex.strings(self.payload):
            self.assertIsNone(ex.CONFIDENCE_TOKEN.search(ex.HASH.sub('', text)), trail)

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['model']['contract']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_an_audit_other_than_the_approved_one_is_refused(self):
        for task in ex.TASKS:
            m = copy.deepcopy(MANIFEST)
            a = self.get(m['research'][task]['audit'])
            if task == 'eegmat':
                a['methods']['neurorvq']['mean_participant_balanced_accuracy'] = 0.7
            else:
                a['mean_participant_metrics']['neurorvq']['balanced_accuracy'] = 0.7
            self.put(m['research'][task]['audit'], a)
            with self.assertRaisesRegex(ValueError, 'binds other files|binds another receipt'):
                build(m)

    def test_an_approval_that_did_not_pass_is_refused(self):
        for task in ex.TASKS:
            m = copy.deepcopy(MANIFEST)
            a = self.get(m['research'][task]['approval'])
            a['status'] = 'HOLD'
            self.put(m['research'][task]['approval'], a)
            with self.assertRaisesRegex(ValueError, 'binds other files'):
                build(m)
        m = copy.deepcopy(MANIFEST)
        a = self.get(m['research']['mi-rest']['approval'])
        a['publication_authorized'] = True       # the research session never authorises the site
        self.put(m['research']['mi-rest']['approval'], a)
        with self.assertRaisesRegex(ValueError, 'binds other files'):
            build(m)

    def test_a_review_that_asks_for_changes_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        r = self.get(m['research']['p300-target']['interpretationReview'])
        r['mandatory_text_fixes'] = ['restate the interval']
        self.put(m['research']['p300-target']['interpretationReview'], r)
        with self.assertRaisesRegex(ValueError, 'binds other files|did not pass'):
            build(m)

    def test_a_handoff_that_prints_other_figures_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        docs = ex.load(m)
        raw, est, ci = ex.audited_values(docs, 'mi-rest')
        docs['research']['mi-rest']['handoff'] = docs['research']['mi-rest']['handoff'].replace('55.0833%', '55.1833%')
        with self.assertRaisesRegex(ValueError, 'does not state'):
            ex.printed(docs, 'mi-rest', raw, est, ci)

    def test_a_source_that_no_longer_states_a_caveat_is_refused(self):
        blocks = {b['id']: b for b in self.payload['blocks']}
        edits = (
            (('research', 'p300-target', 'handoff'), 'It does not isolate whether', 'It isolates whether'),
            (('research', 'eegmat', 'handoff'), 'Exact pretraining absolute units/reference are not established',
             'Exact pretraining absolute units/reference are established'),
            (('research', 'eegmat', 'handoff'), 'this is not untouched external confirmation', 'this is external'),
            (('research', 'mi-rest', 'handoff'), 'clinical claim, online BCI', 'online BCI'),
        )
        for (group, task, key), old, new in edits:
            docs = copy.deepcopy(self.docs)
            self.assertIn(old, docs[group][task][key])
            docs[group][task][key] = docs[group][task][key].replace(old, new)
            with self.assertRaisesRegex(ValueError, 'does not state'):
                ex.input_scale_stated(docs, blocks)
                ex.development_and_scope_stated(docs, blocks)
        docs = copy.deepcopy(self.docs)
        docs['model']['contract']['input_contract']['units'] = 'Microvolts, as pretrained.'
        with self.assertRaisesRegex(ValueError, 'contract units'):
            ex.input_scale_stated(docs, blocks)
        docs = copy.deepcopy(self.docs)
        docs['handoff']['queue']['rows'][8]['usable_level'] = 'Task-specific probe.'
        with self.assertRaisesRegex(ValueError, 'queue row 8'):
            ex.input_scale_stated(docs, blocks)
        b = copy.deepcopy(blocks)
        b['eegmat']['input_chain']['clip_microvolts'] = 400
        with self.assertRaisesRegex(ValueError, 'example preprocessing'):
            ex.input_scale_stated(self.docs, b)
        b = copy.deepcopy(blocks)
        b['p300-target']['input_chain']['clip'] = True
        with self.assertRaisesRegex(ValueError, 'filters, clips'):
            ex.input_scale_stated(self.docs, b)
        docs = copy.deepcopy(self.docs)
        mi = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'mi-rest')
        mi['rows'].append({'name': 'Temporal ridge'})
        with self.assertRaisesRegex(ValueError, 'input-cache caveat'):
            ex.development_and_scope_stated(docs, blocks)
        # the scope: the filter runs over the retained first minute of each recording
        docs = copy.deepcopy(self.docs)
        ad = docs['research']['eegmat']['protocol']['adapter']
        ad['filter_record_extent'] = ad['filter_record_extent'].replace('First 30000 native samples only', 'All samples')
        with self.assertRaisesRegex(ValueError, 'retained first minute'):
            ex.development_and_scope_stated(docs, blocks)
        # the units: the P300 cache's original preparation from the raw files was not re-run
        ex.cache_preparation_stated(self.docs)
        for group, task, key, old, new in (
                ('research', 'p300-target', 'handoff', 'MNE preprocessing runtime was not independently reconstructed',
                 'MNE preprocessing runtime was reconstructed'),
                ('handoff', 'consolidated', None, 'Historical raw preparation and reference/calibration limits remain',
                 'Reference/calibration limits remain')):
            docs = copy.deepcopy(self.docs)
            if key is None:
                self.assertIn(old, docs[group][task])
                docs[group][task] = docs[group][task].replace(old, new)
            else:
                self.assertIn(old, docs[group][task][key])
                docs[group][task][key] = docs[group][task][key].replace(old, new)
            with self.assertRaisesRegex(ValueError, 'does not state'):
                ex.cache_preparation_stated(docs)

    def test_the_eegmat_audit_boundary_rests_on_its_program(self):
        """The EEGMAT audit read both arms' values from the producer's sealed files: a program that extracts them, or a
        receipt that no longer says so, is refused."""
        for old, new in (("x=np.load(root/(method+'.npy'),allow_pickle=False)", 'x=extract(method)'),
                         ("('spectral',95)", "('spectral',96)"),
                         ("check(sha(root/f)==h,'sealed artifact '+f)", 'pass')):
            m = copy.deepcopy(MANIFEST)
            prog = self.get(m['research']['eegmat']['auditProgram'])
            self.assertIn(old, prog)
            self.put(m['research']['eegmat']['auditProgram'], prog.replace(old, new))
            with self.assertRaisesRegex(ValueError, 'eegmat audit program'):
                build(m)
        m = copy.deepcopy(MANIFEST)
        prog = self.get(m['research']['eegmat']['auditProgram'])
        self.put(m['research']['eegmat']['auditProgram'], prog + '\nimport torch\n')
        with self.assertRaisesRegex(ValueError, 'extracts values'):
            build(m)

    def test_another_licence_file_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        self.put(m['model']['weightsLicence'], 'Apache License\nVersion 2.0\n')
        with self.assertRaisesRegex(ValueError, 'not the same CC BY-NC 4.0 text'):
            build(m)

    def test_a_hold_or_another_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['approval']['decision'] = 'withhold'
        with self.assertRaisesRegex(ValueError, 'does not approve'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['holds'] = ['semantic-target']
        with self.assertRaisesRegex(ValueError, 'no hold'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['published']['legacy'] = {'path': 'site/src/data/models.json', 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'never read'):
            build(m)

    def test_per_person_internal_and_withheld_fields_are_refused(self):
        for key in ('per_subject', 'subject_ids', 'per_window_scores', 'per_fold', 'predictions', 'features',
                    'bound_files', 'above_chance_count', 'above_chance_fraction', 'wall_seconds', 'CPU_seconds',
                    'peak_RSS_bytes', 'elapsed_seconds', 'terminal_budgets', 'source_cache_hashes', 'start_unix',
                    'OOF_predictions_exact', 'cpu_threads', 'output_root', 'worker_lock', 'device'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'blocks': [{'audit': {key: 1}}]})

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 4)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v1 backbone'}, 'version label'), ({'scope': 'run in October'}, 'month'),
                         ({'scope': 'Updated with new rows.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'NeuroRVQ beats band power.'}, 'unsupported claim'),
                         ({'scope': 'The backbone is better on EEGMAT.'}, 'unsupported claim'),
                         ({'scope': 'a fully loaded NeuroRVQ'}, 'unsupported claim'),
                         ({'scope': 'an official reproduction of NeuroRVQ'}, 'unsupported claim'),
                         ({'scope': 'the best encoder on P300'}, 'unsupported claim'),
                         ({'scope': 'Scores are epoch counts, not speller accuracy.'}, 'hedge'),
                         ({'scope': 'a 55% bet'}, 'commenter'), ({'scope': 'held-out 0.55'}, 'commenter'),
                         ({'scope': 'an ICLR 2027 entry'}, 'ICLR 2027'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'kept in release-approval.json'}, 'source file'),
                         ({'scope': 'the eugenehp card'}, 'third-party alias'),
                         ({'scope': 'an Apache 2.0 tag'}, 'third-party alias'),
                         ({'scope': 'a /' + 'mnt/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'Neither is shown to be better; outside every leaderboard.',
                        'question': 'Does the backbone separate rest from arithmetic better than band power?'}, private)

    def test_licences_stay_with_their_part(self):
        p = copy.deepcopy(self.payload)
        p['scope'] = 'The datasets are CC BY-NC 4.0.'
        with self.assertRaisesRegex(ValueError, 'CC BY-NC not tied'):
            ex.licences_per_part(p)
        p = copy.deepcopy(self.payload)
        p['rights']['weights']['licence'] = 'CC BY 4.0'
        with self.assertRaisesRegex(ValueError, 'licences per part changed'):
            ex.licences_per_part(p)

    def test_no_private_path_or_name_reaches_the_files(self):
        private = ex.private_names(self.docs)
        records = (*ex.OUTPUTS, ex.MANIFEST, ex.EXPORT_AUDIT)
        for path in (*records, Path(ex.__file__), Path(au.__file__), Path(__file__)):
            body = path.read_text()
            if path in records:      # the programs spell path roots in their own patterns
                self.assertIsNone(ex.LOCAL_ROOTS.search(body), path.name)
            for n in private:
                self.assertNotIn(n.lower(), body.lower(), path.name)

    # ------------------------------------------------------------------ the independent audit
    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            p['blocks'][0]['arms'][0]['balanced_accuracy'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'blocks/0/arms/0/balanced_accuracy'):
            au.audit()

        def bound(p):
            p['blocks'][2]['paired_difference']['interval_95'][1] = -0.0151
        with self.served(bound), self.assertRaisesRegex(au.AuditFailure, 'blocks/2/paired_difference/interval_95/1'):
            au.audit()

        def restore(p):
            p['model']['restore']['trained_tensors'] = 271
        with self.served(restore), self.assertRaisesRegex(au.AuditFailure, 'model/restore/trained_tensors'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['blocks'][0]['arms'][0]['above_50'] = 33
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['blocks'][1]['cohort']['people']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_a_wrong_flag_and_a_type_change(self):
        def zero(p):
            p['blocks'][1]['arms'][2]['interval_95'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def flag(p):
            x = p['blocks'][1]['paired_difference']
            x['interval_includes_zero'], x['reading'] = True, ex.SPANS_ZERO
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'interval_includes_zero'):
            au.audit()

        def typed(p):
            p['blocks'][2]['cohort']['people'] = 21.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'cohort/people'):
            au.audit()

    def test_the_audit_catches_a_changed_label_reading_licence_or_rights_record(self):
        def label(p):
            p['blocks'][1]['arms'][1]['label'] = 'temporal ridge'
        with self.served(label), self.assertRaisesRegex(au.AuditFailure, 'reviewed arms'):
            au.audit()

        def reading(p):
            p['blocks'][0]['paired_difference']['reading'] = 'the two are level'
        with self.served(reading), self.assertRaisesRegex(au.AuditFailure, 'another reading'):
            au.audit()

        def licence(p):
            p['rights']['weights']['licence'] = 'CC BY 4.0'
        with self.served(licence), self.assertRaisesRegex(au.AuditFailure, 'licence files'):
            au.audit()

        def rights(p):
            p['rights']['datasets']['mi-rest']['privacyReview'] = 'none'
        with self.served(rights), self.assertRaisesRegex(au.AuditFailure, 'rights record'):
            au.audit()

        def exposure(p):
            p['pretraining_exposure']['status'] = 'not_exposed'
        with self.served(exposure), self.assertRaisesRegex(au.AuditFailure, 'exposure'):
            au.audit()

        def caveats(p):
            p['blocks'][2]['caveat_keys'].remove('p300-windows')
        with self.served(caveats), self.assertRaisesRegex(au.AuditFailure, 'limitations changed'):
            au.audit()

        def input_scale(p):
            p['blocks'][0]['caveat_keys'].remove('input-scale')
        with self.served(input_scale), self.assertRaisesRegex(au.AuditFailure, 'limitations changed'):
            au.audit()

    def test_the_audit_holds_the_text_to_the_reviewed_text_and_its_figures(self):
        def figure(p):
            x = next(x for x in p['limitations'] if x['id'] == 'variant')
            x['text'] = x['text'].replace('263 trained tensors', '271 trained tensors')
        with self.served(figure), self.assertRaisesRegex(au.AuditFailure, 'variant: the text does not quote'):
            au.audit()

        def dimension(p):
            x = next(x for x in p['limitations'] if x['id'] == 'dimensions')
            x['text'] = x['text'].replace('1,500 temporal means', '1,600 temporal means')
        with self.served(dimension), self.assertRaisesRegex(au.AuditFailure, 'dimensions: the text does not quote'):
            au.audit()

        def boundary(p):
            p['blocks'][1]['audit']['boundary'] = p['blocks'][1]['audit']['boundary'].replace('all 15 heads', 'all 5 heads')
        with self.served(boundary), self.assertRaisesRegex(au.AuditFailure, 'audit boundary quotes other counts'):
            au.audit()

        # what was done: the filtering extent, the P300 cache's preparation and the EEGMAT audit's reach
        def extent(p):
            x = next(x for x in p['limitations'] if x['id'] == 'scope')
            x['text'] = x['text'].replace('the retained first minute of each recording as one block',
                                          'each whole recording')
        with self.served(extent), self.assertRaisesRegex(au.AuditFailure, 'another filtering extent'):
            au.audit()

        def preparation(p):
            x = next(x for x in p['limitations'] if x['id'] == 'units')
            x['text'] = x['text'].replace('; the P300 cache’s original preparation from the raw files was not re-run', '')
        with self.served(preparation), self.assertRaisesRegex(au.AuditFailure, 'preparation otherwise'):
            au.audit()

        def reach(p):
            p['blocks'][0]['audit']['boundary'] = p['blocks'][0]['audit']['boundary'].replace(
                'it read both arms’ values from the producer’s sealed files and did not re-extract them',
                'it re-extracted both arms’ values')
        with self.served(reach), self.assertRaisesRegex(au.AuditFailure, 'describes another reach'):
            au.audit()

        edits = (
            lambda p: p['limitations'][3].update(text=p['limitations'][3]['text'].replace('do not establish', 'establish')),
            lambda p: p['blocks'][0]['arms'][0].update(above_50='33 of 36 above chance'),
            lambda p: p['blocks'][1]['input_chain'].update(reference='a verified common average'),
            lambda p: p['protocols_not_run'][0].update(gate='ready to run'),
            lambda p: p.update(question=p['question'].replace('better than', 'as well as')),
            lambda p: p['placement'].update(text='A ranked panel.'),
            lambda p: p['blocks'][2].update(split='random windows'),
            lambda p: p['limitations'].reverse(),
        )
        for edit in edits:
            with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'reviewed text|limitations changed'):
                au.audit()


if __name__ == '__main__':
    unittest.main()
