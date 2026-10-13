"""The EEGPT core release: what must follow from the pinned runs and records, and what must stay out."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_eegpt_core_export as au
import export_eegpt_core_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


def cell(payload, protocol):
    return next(c for c in payload['cells'] if c['protocol'] == protocol)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class EegptCoreBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build(MANIFEST)
        cls.docs = ex.load(MANIFEST)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    # ------------------------------------------------------------------ forged inputs, re-pinned
    def get(self, ref):
        return json.loads((ex.PROJECT / ref['path']).read_bytes())

    def put(self, ref, obj):
        """Write an edited copy under the temporary root and re-pin the manifest's reference to it."""
        data = json.dumps(obj).encode()
        path = Path(self.tmp.name) / f'{len(list(Path(self.tmp.name).iterdir()))}-{Path(ref["path"]).name}'
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

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-eegpt-core-update-v1')
        self.assertEqual(p['release_id'], 'eegpt-core-update-20261013')
        self.assertEqual([x['id'] for x in p['protocols']], list(ex.PROTOCOLS))
        self.assertEqual([c['protocol'] for c in p['cells']], list(ex.PROTOCOLS))
        self.assertTrue(all(c['model'] == 'eegpt' and c['status'] == 'complete' for c in p['cells']))
        self.assertEqual(len(p['pretraining_attribution']['rows']), 8)
        self.assertEqual(len(p['pretraining_attribution']['paired_contrasts']), 4)
        self.assertEqual(p['pretraining_exposure']['counts'], {'exposed': 0, 'not_exposed': 7, 'unknown': 0})
        self.assertIs(p['pilot_comparison']['leaderboard'], False)
        self.assertEqual(p['directory_status']['suggested_status'], 'Evaluated')
        self.assertEqual(p['directory_status']['released_status'], 'Rights review pending')

    def test_the_cells_are_the_verified_figures(self):
        want = {'mi-rest': (58.33, 54.92, 61.75, 0.5547), 'arithmetic-rest': (65.69, 60.93, 70.32, 0.6367),
                'p300-target': (54.05, 51.47, 56.59, 0.528), 'semantic-target': (54.58, 53.31, 55.86, 0.540),
                'sleep-scalp': (75.53, 73.90, 77.10, 0.748), 'beta-8ch': (20.27, 18.17, 22.60, 0.1692),
                'beta-4ch': (17.31, 15.54, 19.17, 0.1436)}
        for p, (ba, lo, hi, f1) in want.items():
            c = cell(self.payload, p)
            self.assertEqual((r2(c['balanced_accuracy']), r2(c['interval_95'][0]), r2(c['interval_95'][1])), (ba, lo, hi), p)
            self.assertAlmostEqual(c['macro_f1'], f1, delta=0.0005 if p in ('p300-target', 'semantic-target', 'sleep-scalp') else 0.00005)
            self.assertEqual(c['interval']['draws'], 10000)
            self.assertEqual(c['interval']['seed'], 20260912 if p.startswith('beta') else 20260919)
            self.assertFalse(c['interval_includes_chance'] or c['at_or_below_chance'])
            self.assertEqual(c['percent']['balanced_accuracy'], round(100 * c['balanced_accuracy'], 12))
        idle = cell(self.payload, 'idle')
        self.assertEqual((idle['idle_false_activations'], idle['idle_trials'], idle['commands_detected'],
                          idle['command_trials'], idle['always_abstain_people'], idle['people']), (2, 60, 7, 60, 1, 4))
        self.assertEqual(round(idle['window_balanced_accuracy'], 4), 0.5722)
        self.assertEqual(round(idle['window_auroc'], 4), 0.7804)
        self.assertIsNone(idle['interval'])

    def test_the_attribution_rows_are_the_verified_figures(self):
        a = self.payload['pretraining_attribution']
        want = [('ds003810', 'pretraining-attribution-fixed', 58.33, 54.08, 4.25, 0.75, 7.44),
                ('ds003810', 'pretraining-attribution-selected', 57.00, 53.08, 3.92, 0.72, 7.08),
                ('physionet-eegmat-1.0.0', 'pretraining-attribution-fixed', 65.69, 59.24, 6.45, 2.61, 10.59),
                ('physionet-eegmat-1.0.0', 'pretraining-attribution-selected', 65.97, 58.60, 7.38, 4.40, 10.40)]
        for n, (ds, track, pre, rnd, d, lo, hi) in enumerate(want):
            rows = a['rows'][2 * n:2 * n + 2]
            self.assertEqual([(r['dataset_id'], r['track'], r['initialization'], r['encoder_seed_count']) for r in rows],
                             [(ds, track, 'pretrained', 1), (ds, track, 'constructor-random-mean', 3)])
            self.assertEqual((r2(rows[0]['value']), r2(rows[1]['value'])), (pre, rnd))
            self.assertTrue(all(r['confidence_interval_95'] is None for r in rows))
            c = a['paired_contrasts'][n]
            self.assertEqual((c['dataset_id'], c['track']), (ds, track))
            self.assertEqual((r2(c['difference']), r2(c['paired_participant_bootstrap_95'][0]),
                              r2(c['paired_participant_bootstrap_95'][1])), (d, lo, hi))
        self.assertEqual(a['method']['bootstrap'], {**a['method']['bootstrap'], 'draws': 10000, 'seed': 20260920})
        # the published rows' fields and strings, exactly
        topics = json.loads((ex.PROJECT / MANIFEST['published']['deploymentTopics']['path']).read_bytes())
        published = [r for r in topics['rows'] if r['track'].startswith('pretraining-attribution')]
        for r in a['rows']:
            ref = next(x for x in published if x['track'] == r['track'] and x['dataset_id'] == r['dataset_id'])
            self.assertEqual(set(r), set(ref))
            for k in ('protocol_id', 'metric', 'training_regime', 'head_selection'):
                self.assertEqual(r[k], ref[k])
        self.assertEqual(len({r['id'] for r in a['rows']} | {r['id'] for r in topics['rows']}), len(topics['rows']) + 8)

    def test_the_fixed_head_pretrained_rows_are_the_core_cells(self):
        a = self.payload['pretraining_attribution']['rows']
        self.assertEqual(a[0]['value'], cell(self.payload, 'mi-rest')['balanced_accuracy'])
        self.assertEqual(a[4]['value'], cell(self.payload, 'arithmetic-rest')['balanced_accuracy'])

    def test_the_comparisons_and_their_gaps(self):
        rel = {(x['protocol'], r['row']): (r['relation'], r['gap_pp'])
               for x in self.payload['comparisons']['protocols'] for r in x['rows']}
        self.assertEqual(rel[('sleep-scalp', 'spectral-ridge')], ('above', 0.1))
        for row in ('labram', 'cbramod', 'eegnet'):
            self.assertEqual(rel[('sleep-scalp', row)][0], 'above')
        self.assertEqual(rel[('p300-target', 'labram')], ('above', 0.277777777778))
        self.assertEqual(rel[('semantic-target', 'spectral-ridge')], ('above', 0.777777777778))
        self.assertEqual(rel[('mi-rest', 'labram')], ('overlap', None))
        self.assertEqual(rel[('beta-8ch', 'cbramod')][0], 'below')
        self.assertFalse(any('idle' == p for p, _ in rel))
        self.assertTrue(all((g is None) == (r == 'overlap') for r, g in rel.values()))

    def test_the_footnotes_sit_beside_their_cells_once(self):
        p = self.payload
        by_id = {f['id']: f for f in p['footnotes']}
        self.assertEqual(by_id['one-second-patch-grid']['protocols'], ['p300-target', 'semantic-target'])
        self.assertEqual(by_id['untrained-channel-embeddings']['protocols'], ['beta-8ch'])
        self.assertEqual(by_id['untrained-channel-embeddings']['facts']['unused_in_pretraining'], ['AF7', 'AF8', 'PO5', 'PO6'])
        self.assertEqual(by_id['untrained-channel-embeddings']['facts']['channels_affected'], ['PO5', 'PO6'])
        self.assertEqual(by_id['tsinghua-benchmark-context']['protocols'], ['beta-8ch', 'beta-4ch'])
        self.assertEqual(by_id['source-rate']['protocols'], ['mi-rest'])
        self.assertEqual(by_id['source-rate']['facts']['source_sampling_hz'], 125)
        self.assertEqual(by_id['idle-run']['facts'], {'same_run_rows': ['csp-lda', 'labram', 'eegnet', 'shallowfbcspnet'],
                                                      'other_run_rows': ['cbramod', 'deep4net']})
        for fid in ('shorter-than-pretraining', 'fixed-readout'):
            self.assertEqual(by_id[fid]['placement'], 'row')
            self.assertEqual(by_id[fid]['protocols'], list(ex.PROTOCOLS))
        for c in p['cells']:
            self.assertEqual(len(c['footnotes']), len(set(c['footnotes'])))
        # The exposure stays the further-encoder formula: BETA's context adds no status.
        beta = cell(p, 'beta-8ch')['exposure']
        self.assertEqual(beta, {'status': 'not_exposed', 'confidence': 'high',
                                'statement': "not in the authors' published pretraining list (checked 2026-10-12)"})
        self.assertEqual(set(p['pretraining_exposure']['status_vocabulary']), {'exposed', 'not_exposed', 'unknown'})

    def test_the_model_block(self):
        m = self.payload['model']
        self.assertIsNone(m['weights_licence'])
        self.assertIs(m['weights_distributed'], False)
        self.assertEqual(m['code_licence'], 'Apache-2.0')
        self.assertIn('unresolved', m['weights_licence_status'])
        self.assertEqual(m['encoder_parameters'], 25287168)
        self.assertEqual(m['paper'], 'https://doi.org/10.52202/079017-1239')
        self.assertEqual(m['architecture']['pooled_dimension'], 2048)
        self.assertEqual(m['checkpoint']['sha256'], '9d63ebc80bba1ad5e3277df4eecfa05d2745e6243a12ff743c4c0a93930dfac0')

    def test_the_rights_blocks_are_the_released_records(self):
        mvp = json.loads((ex.PROJECT / MANIFEST['published']['coreMatrix']['path']).read_bytes())
        for e in self.payload['protocols']:
            t = next(x for x in mvp['tracks'] if x['id'] == e['id'])
            for k in ('license', 'attribution', 'privacyReview', 'reviewedAt', 'reviewBasis'):
                self.assertEqual(e['rights'][k], t[k])
        sleep = next(e for e in self.payload['protocols'] if e['id'] == 'sleep-scalp')['rights']
        self.assertIn('GDPR office', sleep['privacyReview'])
        beta = next(e for e in self.payload['protocols'] if e['id'] == 'beta-8ch')['rights']
        self.assertIn('Only cohort aggregates should be shown', beta['privacyReview'])

    def test_released_files_are_never_edited(self):
        for ref in MANIFEST['published'].values():
            self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        mvp = json.loads((ex.PROJECT / MANIFEST['published']['coreMatrix']['path']).read_bytes())
        self.assertFalse(any(r['id'] == 'eegpt' for t in mvp['tracks'] for r in t['rows']))

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['publicRecords']['attributionAudit']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_a_run_other_than_the_published_one_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        s = self.get(m['runs']['mi-rest']['summary'])
        next(r for r in s['results'] if r['model'] == 'eegpt')['subject_mean_balanced_accuracy'] = 0.6
        self.put(m['runs']['mi-rest']['summary'], s)
        with self.assertRaisesRegex(ValueError, 'core track publishes'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        a = self.get(m['runs']['sleep-scalp']['audit'])
        a['status'] = 'fail'
        self.put(m['runs']['sleep-scalp']['audit'], a)
        with self.assertRaisesRegex(ValueError, 'core track publishes'):
            build(m)

    def test_the_idle_window_metrics_need_both_recomputations(self):
        m = copy.deepcopy(MANIFEST)
        iv = self.get(m['review']['idleVerification'])
        iv['eegpt_idle_result']['window_auroc'] = 0.79
        self.put(m['review']['idleVerification'], iv)
        with self.assertRaisesRegex(ValueError, 'independent recomputation differs'):
            build(m)

    def test_an_exposed_cell_or_another_check_date_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        pr = self.get(m['review']['exposureProposal'])
        pr['cells'][0]['status'] = 'exposed'
        self.put(m['review']['exposureProposal'], pr)
        with self.assertRaisesRegex(ValueError, 'not the proposed cell'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        pr = self.get(m['review']['exposureProposal'])
        pr['model']['checked_on'] = '2026-10-04'
        self.put(m['review']['exposureProposal'], pr)
        with self.assertRaisesRegex(ValueError, 'another exposure proposal'):
            build(m)

    def test_a_resolved_checkpoint_licence_stops_the_build(self):
        m = copy.deepcopy(MANIFEST)
        t = self.get(m['rights']['checkpointTerms'])
        t['resolved_checkpoint_license'] = 'CC-BY-4.0'
        self.put(m['rights']['checkpointTerms'], t)
        with self.assertRaisesRegex(ValueError, 'no longer unresolved'):
            build(m)

    def test_an_attribution_contrast_the_verification_did_not_recompute_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        v = self.get(m['review']['coreVerification'])
        next(c for c in v['attribution_contrasts'] if c['model'] == 'eegpt')['delta'] = 0.05
        self.put(m['review']['coreVerification'], v)
        with self.assertRaisesRegex(ValueError, 'recomputed another contrast'):
            build(m)

    def test_a_hold_or_another_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['approval']['decision'] = 'withhold'
        with self.assertRaisesRegex(ValueError, 'does not approve'):
            build(m)

    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('per_subject', 'subject_ids', 'threshold', 'predictions', 'random_seed_bas', 'calibration_grid',
                    'short_duration_group_balanced_accuracy', 'seconds', 'device', 'features_sha256', 'checks'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'cells': [{key: 1}]})

    def test_withheld_values_are_absent(self):
        withheld = ex.withheld_values(self.docs)
        self.assertGreaterEqual(len(withheld), 20)
        self.assertFalse(withheld & set(ex.floats(self.payload)))

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 3)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v9 rows'}, 'version label'), ({'scope': 'run in September'}, 'month'),
                         ({'scope': 'Updated with new rows.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'EEGPT is superior to LaBraM.'}, 'unsupported claim'),
                         ({'scope': 'the best encoder here'}, 'unsupported claim'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'kept in summary.json'}, 'source file'),
                         ({'scope': 'a /' + 'Volumes/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'EEGPT is not shown to be superior; never ranked.'}, private)

    def test_the_eegpt_weights_are_never_apache(self):
        p = copy.deepcopy(self.payload)
        p['scope'] = 'The checkpoint is Apache-2.0 code.'
        with self.assertRaisesRegex(ValueError, 'Apache-2.0 beside the weights'):
            ex.weights_not_apache(p)
        p = copy.deepcopy(self.payload)
        p['model']['weights_licence'] = 'Apache-2.0'
        with self.assertRaisesRegex(ValueError, 'Apache-2.0 not tied to the code'):
            ex.weights_not_apache(p)
        p = copy.deepcopy(self.payload)
        p['model']['weights_distributed'] = True
        with self.assertRaisesRegex(ValueError, 'must stay unresolved'):
            ex.weights_not_apache(p)

    def test_no_private_path_or_name_reaches_the_files(self):
        private = ex.private_names(self.docs)
        for path in (*ex.OUTPUTS, ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            self.assertIsNone(ex.LOCAL_ROOTS.search(body), path.name)
            for n in private:
                self.assertNotIn(n.lower(), body.lower(), path.name)

    # ------------------------------------------------------------------ the independent audit
    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            cell(p, 'sleep-scalp')['interval_95'][0] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'cells/7/interval_95/0'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            cell(p, 'mi-rest')['median_balanced_accuracy'] = 0.58
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['pretraining_attribution']['paired_contrasts'][1]['difference']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_a_wrong_flag_and_a_wrong_gap(self):
        def zero(p):
            cell(p, 'idle')['interval'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def flag(p):
            cell(p, 'beta-4ch')['interval_includes_chance'] = True
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'interval_includes_chance'):
            au.audit()

        def gap(p):
            p['comparisons']['protocols'][-1]['rows'][0]['gap_pp'] = 0.2
        with self.served(gap), self.assertRaisesRegex(au.AuditFailure, 'gap_pp'):
            au.audit()

        def relation(p):
            p['comparisons']['protocols'][0]['rows'][2]['relation'] = 'above'
        with self.served(relation), self.assertRaisesRegex(au.AuditFailure, 'another relation'):
            au.audit()

    def test_the_audit_catches_a_withheld_value_and_a_type_change(self):
        withheld = sorted(ex.withheld_values(self.docs))

        def leak(p):
            p['pretraining_attribution']['rows'][1]['value'] = withheld[-2]
        with self.served(leak), self.assertRaises(au.AuditFailure):
            au.audit()

        def typed(p):
            cell(p, 'idle')['idle_trials'] = 60.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'idle_trials'):
            au.audit()

    def test_the_audit_catches_a_changed_rights_record_or_string(self):
        def rights(p):
            p['protocols'][2]['rights']['privacyReview'] = 'none'
        with self.served(rights), self.assertRaisesRegex(au.AuditFailure, 'rights record'):
            au.audit()

        def row(p):
            p['pretraining_attribution']['rows'][3]['head_selection'] = 'fixed alpha100'
        with self.served(row), self.assertRaisesRegex(au.AuditFailure, 'head_selection'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
