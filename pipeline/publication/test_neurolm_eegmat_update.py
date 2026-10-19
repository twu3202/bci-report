"""The NeuroLM EEGMAT release: what must follow from the pinned research records, and what must stay out."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_neurolm_eegmat_export as au
import export_neurolm_eegmat_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
PLAN = ex.PROJECT / 'research/site_release_plan_20261019/Release Layout Plan v2.md'


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


def arm(payload, aid):
    return next(a for a in payload['arms'] if a['id'] == aid)


def contrast(payload, cid):
    return next(c for c in payload['paired_contrasts'] if c['id'] == cid)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class NeurolmEegmatBoundary(unittest.TestCase):
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
        return json.loads(data) if ref['path'].endswith('.json') else data.decode()

    def put(self, ref, obj):
        """Write an edited copy under the temporary root, keeping its path below the research folder, and re-pin it."""
        data = obj.encode() if isinstance(obj, str) else json.dumps(obj).encode()
        rel = ref['path'].split(ex.RESEARCH_ROOT, 1)[1] if ex.RESEARCH_ROOT in ref['path'] else Path(ref['path']).name
        path = Path(self.tmp.name) / ex.RESEARCH_ROOT / rel
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
        self.assertEqual(audit['copied_exactly'], 24)
        self.assertEqual(audit['nulls_kept'], 4)

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-neurolm-eegmat-update-v1')
        self.assertEqual(p['release_id'], 'neurolm-eegmat-update-20261020')
        self.assertEqual(p['generated_at'], '2026-10-20')
        self.assertEqual(p['status'], 'aggregate_preview')
        self.assertEqual([(a['id'], a['label']) for a in p['arms']],
                         [('tokenizer_mean', 'tokenizer features'), ('log_bandpower', 'band power'),
                          ('gpt_mean', 'GPT hidden states')])
        self.assertEqual([(c['a'], c['b'], c['role']) for c in p['paired_contrasts']],
                         [('tokenizer_mean', 'log_bandpower', 'question'), ('gpt_mean', 'tokenizer_mean', 'descriptive'),
                          ('gpt_mean', 'log_bandpower', 'descriptive')])
        pl = p['placement']
        self.assertEqual((pl['page'], pl['anchor'], pl['pointer_from']),
                         ('/topics/pilot-studies/', 'neurolm-eegmat', '/protocols/arithmetic-rest/'))
        self.assertEqual((pl['counted_in_pilots'], pl['leaderboard'], pl['core_matrix_row'], pl['new_dataset_count'],
                          pl['new_model_count']), (False, False, False, 0, 0))
        self.assertEqual(set(p['provenance']['source_export_sha256']), {'neurolm-eegmat'})
        self.assertEqual(p['provenance']['source_export_sha256']['neurolm-eegmat'],
                         '62b7ebe4be2e331cb0651486185c7abdaa173d3279031d8ffc66c74b6208a20e')
        self.assertEqual(p['provenance']['research_release_sha256'],
                         '9a9c1b4770797c899b229e176f7deec4dceacd209c80dfcd3f63d2365afc7adf')
        self.assertEqual(p['provenance']['protocol_sha256'],
                         '670b55c1d63856af5b318104d40687772658f7790c9ebefd11f6633f4ed23b61')

    def test_the_figures_are_the_verified_ones(self):
        p = self.payload
        want = {'tokenizer_mean': (0.6449074074074076, 0.6251820691155802, 64.49, 62.52),
                'log_bandpower': (0.6388888888888888, 0.5907640266978917, 63.89, 59.08),
                'gpt_mean': (0.612037037037037, 0.5933772131283214, 61.20, 59.34)}
        for aid, (ba, f1, ba2, f12) in want.items():
            a = arm(p, aid)
            self.assertEqual((a['balanced_accuracy'], a['macro_f1']), (ba, f1), aid)
            self.assertEqual((r2(a['balanced_accuracy']), r2(a['macro_f1'])), (ba2, f12), aid)
            self.assertIsNone(a['interval_95'])
        pp = {'tokenizer-minus-band-power': {'balanced_accuracy': (0.60, -5.32, 6.44, True),
                                             'macro_f1': (3.44, -3.93, 10.67, True)},
              'gpt-minus-tokenizer': {'balanced_accuracy': (-3.29, -5.37, -1.02, False),
                                      'macro_f1': (-3.18, -5.42, -0.75, False)},
              'gpt-minus-band-power': {'balanced_accuracy': (-2.69, -8.34, 3.10, True),
                                       'macro_f1': (0.26, -6.64, 7.36, True)}}
        for cid, metrics in pp.items():
            for m, (d, lo, hi, spans) in metrics.items():
                c = contrast(p, cid)[m]
                self.assertEqual((r2(c['difference']), r2(c['interval_95'][0]), r2(c['interval_95'][1])), (d, lo, hi),
                                 f'{cid} {m}')
                self.assertIs(c['interval_includes_zero'], spans)
        q = contrast(p, 'tokenizer-minus-band-power')['balanced_accuracy']
        self.assertEqual((q['difference'], q['interval_95']), (0.00601851851851852,
                                                               [-0.05324074074074073, 0.0643865740740741]))
        self.assertEqual(p['chance_level'], {'balanced_accuracy': 0.5, 'macro_f1': None})
        self.assertEqual({k: p['interval'][k] for k in ('level', 'unit', 'resamples', 'seed')},
                         {'level': 0.95, 'unit': 'participant', 'resamples': 1000, 'seed': 20261016})

    @unittest.skipUnless(PLAN.exists(), 'the release plan is local-only')
    def test_the_interval_sentence_is_the_plans(self):
        q = contrast(self.payload, 'tokenizer-minus-band-power')['balanced_accuracy']
        sentence = (f'Tokenizer features minus band power is {ex.signed(q["difference"])} points (paired 95% '
                    f'participant-bootstrap interval {ex.signed(q["interval_95"][0])} to {ex.signed(q["interval_95"][1])}): '
                    f'{q["reading"]}.')
        self.assertIn(sentence, PLAN.read_text())
        self.assertEqual(q['reading'], ex.SPANS_ZERO)

    def test_the_cohort(self):
        c = self.payload['cohort']
        self.assertEqual((c['people'], c['recordings'], c['conditions'], c['windows'], c['channels'], c['folds']),
                         (36, 72, 2, 2160, 19, 5))
        self.assertEqual((c['retained_seconds'], c['window_seconds'], c['windows_per_recording']), (60, 2, 30))
        self.assertEqual((c['source_sampling_hz'], c['sampling_hz']), (500, 200))
        self.assertEqual(c['fold_sizes_people'], [8, 7, 7, 7, 7])
        self.assertEqual(len(c['channel_names']), 19)

    def test_dimensions_and_parameters_come_from_pinned_evidence(self):
        p = self.payload
        self.assertEqual([a['dimension'] for a in p['arms']], [768, 95, 768])
        m = p['model']
        self.assertEqual(m['parameters'], 255107712)
        self.assertEqual(m['restored_state_entries'], 240)
        self.assertEqual(m['checkpoint']['bytes'], 2377399148)
        self.assertEqual(m['checkpoint']['sha256'], 'ffe098bc138b89f8817d3710a3604498d8ecd15135080e2ca27735d05c6d29ab')
        self.assertEqual(m['checkpoint']['revision'], 'eddfff5c64a4139442f826d6c67c8369fd00f45a')
        self.assertEqual(m['source_revision'], '0cda9876d8ce6ee07ed0c43eee5e9a6f5c24b177')
        self.assertEqual(m['architecture'], {'layers': 12, 'heads': 12, 'width': 768, 'context_tokens': 1024})
        self.assertEqual((m['frozen'], m['fine_tuning'], m['text_generation'], m['language_model_head']),
                         (True, False, False, False))

    def test_the_legacy_models_json_facts_are_not_reused(self):
        self.assertFalse(any(Path(r['path']).name in ('models.json', 'leaderboard.json') for r in ex.input_refs(MANIFEST)))
        legacy = json.loads((ex.PROJECT / 'site/src/data/models.json').read_text()).get('neurolm-b')
        m = self.payload['model']
        if legacy:
            self.assertNotEqual(m['parameters'], legacy['params_m'] * 10 ** 6)
            self.assertNotEqual(m['checkpoint']['repository'], legacy['weights_url'])
        self.assertTrue(m['checkpoint']['repository'].startswith('https://huggingface.co/'))
        self.assertNotIn('instruction-tuned', json.dumps(self.payload).lower())
        m2 = copy.deepcopy(MANIFEST)
        m2['published']['legacy'] = {'path': 'site/src/data/models.json', 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'never read'):
            build(m2)

    def test_the_licences_per_part(self):
        r = self.payload['rights']
        self.assertEqual(r['code']['licence'], 'MIT')
        self.assertEqual(r['code']['url'], 'https://github.com/935963004/NeuroLM/blob/0cda9876d8ce6ee07ed0c43eee5e9a6f5c24b177/LICENSE')
        self.assertEqual(r['checkpoint']['licence'], 'CC BY 4.0')
        self.assertEqual((r['checkpoint']['model_card_bytes'], r['checkpoint']['model_card_terms'], r['checkpoint']['gated'],
                          r['checkpoint']['weights_distributed']), (30, False, False, False))
        self.assertEqual(r['dataset']['license'], 'Open Data Commons Attribution License 1.0')
        self.assertEqual(r['dataset']['rightsScope'], 'Personal noncommercial research; aggregate results only')
        mvp = json.loads((ex.PROJECT / MANIFEST['published']['coreMatrix']['path']).read_bytes())
        t = next(x for x in mvp['tracks'] if x['id'] == 'arithmetic-rest')
        for k in ex.RIGHTS_FIELDS:
            self.assertEqual(r['dataset'][k], t[k])
        self.assertIs(self.payload['model']['weights_distributed'], False)

    def test_the_exposure_is_unknown(self):
        e = self.payload['pretraining_exposure']
        self.assertEqual(e['status'], 'unknown')
        self.assertEqual(e['checkpoint_stage']['status'], 'unknown')
        self.assertIs(e['checkpoint_stage']['instruction_tuning_verified'], False)
        self.assertEqual((e['checkpoint_stage']['checkpoint_epoch'], e['checkpoint_stage']['iteration'],
                          e['checkpoint_stage']['initialised_from'], e['checkpoint_stage']['learning_rate']),
                         (19, 83660, 'gpt2', 0.0006))
        self.assertIs(e['published_pretraining_list']['includes_eegmat'], False)
        self.assertIn('Workload', e['instruction_tasks'])
        ids = [x['id'] for x in self.payload['limitations']]
        self.assertEqual(len(ids), len(set(ids)))
        exposure = next(x['text'] for x in self.payload['limitations'] if x['id'] == 'exposure')
        self.assertIn('exposure is shown as unknown', exposure)

    def test_the_adapter_and_the_core_protocol(self):
        a = self.payload['adapter']
        self.assertEqual((a['band_pass_hz'], a['filter_order'], a['notch'], a['official_notch_hz'], a['amplitude_divisor']),
                         ([0.1, 75], 4, False, [50, 60], 100))
        c = self.payload['separate_from_core']
        self.assertEqual((c['core_band_pass'], c['core_sampling_hz'], c['core_spectral_ridge']['band_hz']),
                         (False, 250, [0.5, 45]))
        self.assertTrue(c['shared_windows'] and c['shared_channels'] and c['shared_fold_rule'] and c['shared_head'])

    def test_released_files_are_never_edited(self):
        for ref in MANIFEST['published'].values():
            self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        pilot = (ex.PROJECT / MANIFEST['published']['pilotStudies']['path']).read_text()
        self.assertNotIn('neurolm', pilot.lower())

    def test_no_core_eegmat_figure_reaches_the_file(self):
        core = ex.core_values(self.docs)
        self.assertGreaterEqual(len(core), 10)
        self.assertFalse(core & set(ex.numbers(self.payload)))
        # The tokenizer figure sits in its own field once.
        hits = [v for v in ex.numbers(self.payload) if v == 0.6449074074074076]
        self.assertEqual(len(hits), 1)

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['research']['preflight']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_an_export_other_than_the_approved_one_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        e = self.get(m['research']['export'])
        e['aggregate']['tokenizer_mean']['equal_person_balanced_accuracy'] = 0.66
        self.put(m['research']['export'], e)
        with self.assertRaisesRegex(ValueError, 'not the file the research release approves'):
            build(m)

    def test_the_readings_must_have_verified_the_same_export(self):
        m = copy.deepcopy(MANIFEST)
        r = self.get(m['planning']['readings'])
        entry = next(x for x in r if x['id'] == m['planning']['readings']['entry'])
        entry['result']['files_for_public_assets'][0]['sha256_actual'] = '1' * 64
        self.put(m['planning']['readings'], r)
        with self.assertRaisesRegex(ValueError, 'readings verified another export'):
            build(m)

    def test_an_aggregate_the_reviews_did_not_pin_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        pa = self.get(m['research']['pendingAggregate'])
        pa['aggregate']['gpt_mean']['equal_person_macro_f1'] = 0.6
        self.put(m['research']['pendingAggregate'], pa)
        with self.assertRaisesRegex(ValueError, 'interpretation review'):
            build(m)

    def test_a_resolved_exposure_stops_the_build(self):
        m = copy.deepcopy(MANIFEST)
        pre = self.get(m['research']['preflight'])
        pre['hf']['instruction_tuned_checkpoint_verified'] = True
        self.put(m['research']['preflight'], pre)
        with self.assertRaisesRegex(ValueError, 'exposure must be reviewed'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        pre = self.get(m['research']['preflight'])
        pre['exposure']['pretraining_dataset_names'].append('PhysioNet Mental Arithmetic')
        self.put(m['research']['preflight'], pre)
        with self.assertRaisesRegex(ValueError, 'in the published pretraining list'):
            build(m)

    def test_another_stated_licence_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        pre = self.get(m['research']['preflight'])
        pre['hf']['license_metadata'] = 'mit'
        self.put(m['research']['preflight'], pre)
        with self.assertRaisesRegex(ValueError, 'stated licence changed'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        pre = self.get(m['research']['preflight'])
        pre['code']['license'] = 'Apache-2.0'
        self.put(m['research']['preflight'], pre)
        with self.assertRaisesRegex(ValueError, 'not the pinned MIT file'):
            build(m)

    def test_a_parameter_count_from_another_receipt_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        sm = self.get(m['research']['smokeEvidence'])
        sm['files']['smoke-attempt-03.json']['strict_restore']['parameters'] = 254000000
        self.put(m['research']['smokeEvidence'], sm)
        with self.assertRaisesRegex(ValueError, 'not the delivered receipt'):
            build(m)

    def test_a_hold_or_another_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['approval']['decision'] = 'withhold'
        with self.assertRaisesRegex(ValueError, 'does not approve'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['holds'] = ['checkpoint stage']
        with self.assertRaisesRegex(ValueError, 'no hold'):
            build(m)

    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('per_subject', 'subject_ids', 'per_window_scores', 'predictions', 'features', 'peak_rss_bytes',
                    'elapsed_seconds', 'cpu_threads', 'expected_root', 'device', 'checks', 'worker_lock'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'arms': [{key: 1}]})

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 3)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v1 rows'}, 'version label'), ({'scope': 'run in October'}, 'month'),
                         ({'scope': 'Updated with new rows.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'NeuroLM features beat band power.'}, 'unsupported claim'),
                         ({'scope': 'Tokenizer features are better here.'}, 'unsupported claim'),
                         ({'scope': 'An instruction-tuned NeuroLM result.'}, 'unsupported claim'),
                         ({'scope': 'the best encoder on EEGMAT'}, 'unsupported claim'),
                         ({'scope': 'a 55% bet'}, 'commenter'), ({'scope': 'held-out 0.55'}, 'commenter'),
                         ({'scope': 'an ICLR 2027 entry'}, 'ICLR 2027'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'kept in eegmat-probe-protocol.json'}, 'source file'),
                         ({'scope': 'read from Subject00_1.edf'}, 'source file'),
                         ({'scope': 'a /' + 'home/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'Neither is shown to be better; outside every leaderboard.',
                        'question': 'Do tokenizer features separate rest from arithmetic better than band power?'}, private)

    def test_licences_stay_with_their_part(self):
        p = copy.deepcopy(self.payload)
        p['scope'] = 'The checkpoint is MIT.'
        with self.assertRaisesRegex(ValueError, 'MIT not tied to the code'):
            ex.licences_per_part(p)
        p = copy.deepcopy(self.payload)
        p['scope'] = 'The code is CC BY 4.0.'
        with self.assertRaisesRegex(ValueError, 'CC BY 4.0 not tied'):
            ex.licences_per_part(p)
        p = copy.deepcopy(self.payload)
        p['rights']['checkpoint']['licence'] = 'MIT'
        with self.assertRaisesRegex(ValueError, 'licences per part changed'):
            ex.licences_per_part(p)

    def test_measured_compute_is_absent(self):
        withheld = ex.withheld_values(self.docs)
        self.assertGreaterEqual(len(withheld), 8)
        self.assertIn(114.96, withheld)
        self.assertFalse(withheld & set(ex.numbers(self.payload)))

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
            p['arms'][0]['balanced_accuracy'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'arms/0/balanced_accuracy'):
            au.audit()

        def bound(p):
            p['paired_contrasts'][1]['macro_f1']['interval_95'][1] = -0.0075
        with self.served(bound), self.assertRaisesRegex(au.AuditFailure, 'paired_contrasts/1/macro_f1/interval_95/1'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['arms'][0]['median_balanced_accuracy'] = 0.64
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['model']['parameters']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_a_wrong_flag_and_a_type_change(self):
        def zero(p):
            p['arms'][1]['interval_95'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def flag(p):
            c = p['paired_contrasts'][1]['balanced_accuracy']
            c['interval_includes_zero'], c['reading'] = True, ex.SPANS_ZERO
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'interval_includes_zero'):
            au.audit()

        def typed(p):
            p['cohort']['people'] = 36.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'cohort/people'):
            au.audit()

    def test_the_audit_catches_a_changed_label_reading_or_rights_record(self):
        def label(p):
            p['arms'][0]['label'] = 'encoder features'
        with self.served(label), self.assertRaisesRegex(au.AuditFailure, 'reviewed label'):
            au.audit()

        def reading(p):
            p['paired_contrasts'][0]['balanced_accuracy']['reading'] = 'the two are level'
        with self.served(reading), self.assertRaisesRegex(au.AuditFailure, 'another reading'):
            au.audit()

        def rights(p):
            p['rights']['dataset']['privacyReview'] = 'none'
        with self.served(rights), self.assertRaisesRegex(au.AuditFailure, 'rights record'):
            au.audit()

        def exposure(p):
            p['pretraining_exposure']['status'] = 'not_exposed'
        with self.served(exposure), self.assertRaisesRegex(au.AuditFailure, 'exposure'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
