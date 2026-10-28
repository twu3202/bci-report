"""The ten-second EEGMAT probes release: what must follow from the pinned research records, and what must stay out."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_eegmat_ten_second_export as au
import export_eegmat_ten_second_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
PLAN = ex.PROJECT / 'research/site_release_plan_20261028/Release Layout Plan v3.md'


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


def pp(x):
    """A fraction as the plan prints a difference: signed, two decimals, a true minus."""
    return f'{100 * x:+.2f}'.replace('-', '−')


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class EegmatTenSecondBoundary(unittest.TestCase):
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

    def docs_copy(self):
        return copy.deepcopy(self.docs)

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
        self.assertEqual(audit['copied_exactly'], 10)
        self.assertGreaterEqual(audit['withheld_values_checked_absent'], 30)

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-eegmat-ten-second-update-v1')
        self.assertEqual(p['release_id'], 'eegmat-ten-second-update-20261028')
        self.assertEqual(p['generated_at'], '2026-10-28')
        self.assertEqual(p['status'], 'aggregate_preview')
        for key in ('schema_version', 'release_id', 'generated_at', 'provenance', 'not_published'):
            self.assertIn(key, p)
        pl = p['placement']
        self.assertEqual((pl['page'], pl['anchor'], pl['after_anchor'], pl['pointer_from']),
                         ('/topics/pilot-studies/', 'eegmat-ten-second', 'neurorvq', '/protocols/arithmetic-rest/'))
        self.assertEqual((pl['counted_in_pilots'], pl['leaderboard'], pl['core_matrix_row'], pl['new_dataset_count'],
                          pl['new_model_count'], pl['shared_table']), (False, False, False, 0, 0, False))
        self.assertEqual(pl['subsections'], ['eeg_captioner', 'axon'])
        pv = p['provenance']
        served = json.loads(ex.OUTPUTS[0].read_bytes())['provenance']
        self.assertEqual(served['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(pv['source_export_sha256'], {
            'eeg-captioner': 'db45216a9ba6591ce6c284595e0fb69c9979bc9fe37bd74f1e9358d8a6af7fbd',
            'axon': '2c1fee43cffb6f4a4f9070067ef031f834e9c46c717cd96305f5a05261e75b8e'})
        self.assertEqual(pv['release_approval_sha256'], {
            'eeg-captioner': 'e8fee718675a324ee1566b8c1dd353fd8a1e7b3f812c933175ce3bb25aa59177',
            'axon': '142df9d09ce4211ac677b92914836708e30b488c78f27ff72a16e285cdf1ce6f'})
        self.assertEqual(p['release_record']['research_release_status'],
                         {'eeg_captioner': 'PASS_INTERNAL_CONDITIONAL_PROBE_HANDOFF',
                          'axon': 'PASS_CONDITIONAL_AGGREGATE_RELEASE'})

    def test_the_figures_are_the_approved_ones(self):
        c, a = self.payload['eeg_captioner'], self.payload['axon']
        self.assertEqual([x['balanced_accuracy'] for x in c['arms']], [0.6574074074074076, 0.6759259259259258])
        self.assertEqual([x['balanced_accuracy'] for x in a['arms']], [0.7013888888888888, 0.6759259259259258])
        self.assertEqual([r2(x['balanced_accuracy']) for x in c['arms'] + a['arms']], [65.74, 67.59, 70.14, 67.59])
        cd, ad = c['paired_difference'], a['paired_difference']
        self.assertEqual((cd['difference'], cd['interval_95']),
                         (-0.0185185185185185, [-0.09027777777777773, 0.04861111111111114]))
        self.assertEqual((ad['difference'], ad['interval_95']),
                         (0.02546296296296297, [-0.057870370370370336, 0.10416666666666667]))
        self.assertEqual((r2(cd['difference']), r2(cd['interval_95'][0]), r2(cd['interval_95'][1])), (-1.85, -9.03, 4.86))
        self.assertEqual((r2(ad['difference']), r2(ad['interval_95'][0]), r2(ad['interval_95'][1])), (2.55, -5.79, 10.42))
        for d in (cd, ad):
            self.assertIs(d['interval_includes_zero'], True)
            self.assertEqual(d['reading'], ex.SPANS_ZERO)
        self.assertIs(self.payload['interval']['both_span_zero'], True)

    @unittest.skipUnless(PLAN.exists(), 'the release plan is local-only')
    def test_the_plans_table_is_these_figures(self):
        plan = PLAN.read_text()
        c, a = self.payload['eeg_captioner'], self.payload['axon']
        for block in (c, a):
            enc, base = (x['balanced_accuracy'] for x in block['arms'])
            d = block['paired_difference']
            self.assertIn(f'| {block["title"]} | {100 * enc:.2f}% | {100 * base:.2f}% (', plan)
            self.assertIn(f'{pp(d["difference"])} pp [{pp(d["interval_95"][0])}, {pp(d["interval_95"][1])}]', plan)
        self.assertIn('the same predictions reused without refitting; not matched for normalisation or parameter count',
                      plan)

    def test_the_cohort(self):
        c = self.payload['cohort']
        self.assertEqual((c['people'], c['recordings'], c['conditions'], c['windows'], c['channels'], c['sampling_hz'],
                          c['folds']), (36, 72, 2, 432, 19, 200, 5))
        self.assertEqual((c['retained_seconds'], c['window_seconds'], c['windows_per_recording']), (60, 10, 6))
        self.assertEqual(len(c['channel_names']), 19)
        self.assertNotIn('OZ', c['channel_names'])
        self.assertEqual((c['preprocessing']['band_pass_hz'], c['preprocessing']['notch_hz']), ([0.1, 75], 50))
        i = self.payload['interval']
        self.assertEqual((i['draws'], i['seed'], i['level'], i['unit']), (20000, 20261026, 0.95, 'participant'))
        self.assertNotIn('fold_sizes_people', json.dumps(self.payload))

    def test_the_source_qc_totals_and_rule(self):
        q = self.payload['source_annotation_qc']
        self.assertEqual((q['windows_meeting_rules'], q['windows'], q['recordings_flagged'], q['recordings']),
                         (0, 432, 72, 72))
        self.assertEqual((q['rule']['flagged_channel_ratio_above'], q['rule']['bad_duration_ratio_above']), (0.3, 0.2))
        self.assertEqual(q['beside_every_score'], '0 of 432 windows meet EEG-Captioner’s source annotation-QC rules, '
                                                  'and 72 of 72 recordings are flagged by them.')
        self.assertIn('not evidence that EEGMAT as a whole is unusable', q['scope'])
        self.assertIs(q['recomputed_by_audit'], False)
        n = self.payload['axon']['numerical_input_check']
        self.assertEqual(n['beside_score'], 'AXON’s own numerical input check passed 432 of 432, a different check')
        published = set(ex.numbers(self.payload))
        for figure in (1211, 557, 654, 1296, 864):
            self.assertNotIn(figure, published)

    def test_two_separate_subsections_and_no_encoder_contrast(self):
        p = self.payload
        self.assertIs(p['encoder_contrast']['published'], False)
        c, a = p['eeg_captioner'], p['axon']
        self.assertEqual((c['title'], a['title']), ('EEG-Captioner encoder, mean-token 256-d + ridge', 'AXON, 512-d + ridge'))
        self.assertEqual((c['arms'][1]['note'], a['arms'][1]['note']), (ex.WELCH_MATCHED, ex.WELCH_REUSED))
        self.assertEqual(a['baseline']['same_baseline_as'], 'eeg-captioner')
        cross = a['arms'][0]['balanced_accuracy'] - c['arms'][0]['balanced_accuracy']
        self.assertFalse({cross, -cross} & set(ex.numbers(p)))
        for block in (c, a):
            self.assertEqual([x['id'] for x in block['arms']][1], 'welch-band-power')
            self.assertEqual(block['paired_difference']['b'], 'welch-band-power')

    def test_identities_and_licences_per_part(self):
        ci, ai = self.payload['eeg_captioner']['identity'], self.payload['axon']['identity']
        self.assertEqual((ci['hf_revision'], ci['source_revision'], ci['encoder_sha256'], ci['encoder_bytes']),
                         ('1d56a371d68a108dd56c362cc41205c5b511cc76', '088d9af2dedcb181534f7fdcff7c913a19e10f04',
                          '060a5c0d9ac11543470038adbcbc5d9ba5828c1dc7c7d5097549435fbe28e989', 20852784))
        self.assertEqual((ai['hf_repository'], ai['hf_revision'], ai['source_revision'], ai['checkpoint_sha256'],
                          ai['checkpoint_bytes']),
                         ('https://huggingface.co/MannasAI/axon-eeg', 'fe7f85239e6018f393039a10a103bf7075c93aa6',
                          '8c618f15a702f63d4899e3e8bc2e6f10a5f54151',
                          '89c864a3ed947588ffc740cd4b342a2158661b13898c0dd9a86abebd33ffc882', 474574184))
        cr, ar = self.payload['eeg_captioner']['rights'], self.payload['axon']['rights']
        self.assertEqual((cr['code']['licence'], cr['weights']['licence']), ('MIT', 'Apache-2.0'))
        self.assertEqual((ar['checkpoint']['licence'], ar['module']['licence'], ar['project']['licence']),
                         ('Apache-2.0', 'Apache-2.0', 'BSD-3-Clause'))
        self.assertFalse(ci['weights_distributed'] or ai['weights_distributed'] or ar['checkpoint']['distributed']
                         or cr['weights']['distributed'])
        self.assertNotRegex(json.dumps(self.payload), r'(?i)arxiv|2609\.08788')
        mvp = json.loads((ex.PROJECT / MANIFEST['published']['coreMatrix']['path']).read_bytes())
        t = next(x for x in mvp['tracks'] if x['id'] == 'arithmetic-rest')
        for k in ex.RIGHTS_FIELDS:
            self.assertEqual(self.payload['rights']['dataset'][k], t[k])

    def test_the_audit_boundary_facts(self):
        c, a = self.payload['eeg_captioner']['audit'], self.payload['axon']['audit']
        self.assertEqual((c['raw_preprocessing_recomputed'], c['source_qc_recomputed'], c['feature_max_abs_error']),
                         (False, False, 0.0))
        self.assertEqual((a['first_audit']['status'], a['first_audit']['kept'], a['first_audit']['rtol'],
                          a['first_audit']['atol']), ('failed', True, 1e-6, 1e-7))
        self.assertEqual((a['corrected_audit']['byte_identical'], a['corrected_audit']['tolerance_relaxed'],
                          a['corrected_audit']['feature_max_abs_error'], a['production_unchanged'], a['producer_rerun']),
                         (True, False, 0.0, True, False))
        self.assertIn('first independent audit failed its feature tolerance and is kept', a['text'])

    def test_the_captioner_audit_says_what_was_exact(self):
        """Zero is the feature error; the hard predictions match exactly; the heads' decision scores only to a bound."""
        c = self.payload['eeg_captioner']['audit']
        for key in ('max_abs_error', 'outputs_reproduced_exactly'):
            self.assertNotIn(key, c)
        self.assertIs(c['hard_predictions_reproduced_exactly'], True)
        self.assertEqual(c['head_decision_score_error_below'], 1e-6)
        self.assertIn('all 432 encoder and baseline feature rows exactly', c['text'])
        self.assertIn('reproduced every hard prediction exactly with decision scores within 1e-6', c['text'])
        errors = self.docs['captioner']['outcome']['audit']['head_max_abs_error']
        self.assertTrue(all(0 < v < c['head_decision_score_error_below'] for v in errors.values()))
        blob, published = json.dumps(self.payload), set(ex.numbers(self.payload))
        for v in errors.values():                       # the measured errors stay out, as numbers and as text
            self.assertNotIn(v, published)
            self.assertNotIn(f'{v:.2e}'.replace('e-0', 'e-'), blob)
        for trail, text in ex.strings(self.payload):     # the hard-prediction count stays out of the text
            if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', text):
                self.assertNotIn('864', text, trail)

    def test_audit_fact_keys_are_allowed_only_in_the_audit_blocks(self):
        ex.scrub_check({'eeg_captioner': {'audit': {'feature_max_abs_error': 0.0,
                                                    'hard_predictions_reproduced_exactly': True}}})
        ex.scrub_check({'axon': {'audit': {'corrected_audit': {'feature_max_abs_error': 0.0}}}})
        for bad in ({'axon': {'feature_max_abs_error': 0.0}},
                    {'eeg_captioner': {'feature_max_abs_error': 0.0}},
                    {'eeg_captioner': {'audit': {'feature_max_abs_error': [0.0, 0.0]}}},
                    {'eeg_captioner': {'audit': {'hard_predictions': [0, 1]}}},
                    {'eeg_captioner': {'audit': {'features': 0.0}}}):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check(bad)

    def test_the_not_published_list_names_every_required_item(self):
        """Plan section 2.3 and the brief: each withheld kind is named, not only matched to the manifest."""
        listed = ' '.join(self.payload['not_published'])
        for phrase in ('per-fold balanced accuracy', 'fold assignments', 'participant identifiers', 'features',
                       'fitted heads', 'predictions', 'Confusion matrices', 'pooled macro-F1',
                       'count of flagged channel-record instances', 'counts by condition and by fold', 'forward counts',
                       'head-fit counts', 'CPU and wall time and memory', 'A difference between the two encoders',
                       'AXON’s paper reference', 'Checkpoints and weights'):
            self.assertIn(phrase, listed)
        for figure in ('1,211', '1211', '557', '654'):
            self.assertNotIn(figure, listed)
        m = copy.deepcopy(MANIFEST)
        m['notPublished'] = [x for x in m['notPublished'] if not x.startswith('Confusion matrices')]
        with self.assertRaisesRegex(ValueError, 'not-published list does not name'):
            build(m)

    def test_the_key_caveats_keep_their_words(self):
        lim = {x['id']: x['text'] for x in self.payload['limitations']}
        for lid, phrase in (('recording-order', 'Rest is recorded before arithmetic'),
                            ('recording-order', 'subject-disjoint folds do not remove this'),
                            ('recording-order', 'neither probe isolates cognitive workload'),
                            ('exposure', 'Whether either encoder saw EEGMAT in pretraining is unknown'),
                            ('axon-inputs', 'nominal template electrode positions, not positions digitised for each '
                                            'person'),
                            ('axon-inputs', 'differs from the pretraining preprocessing on AXON’s model card'),
                            ('upstream-recording', 'linked-ear reference'),
                            ('upstream-recording', 'cannot restore frequencies removed before release'),
                            ('scope', 'using context outside each window')):
            self.assertIn(phrase, lim[lid], lid)
        q = self.payload['source_annotation_qc']
        self.assertIn('It does not say that each window has an artifact', q['scope'])
        self.assertIn('not evidence that EEGMAT as a whole is unusable', q['scope'])
        self.assertIn('the summed duration of BAD annotations exceeds 0.2 of the recording', q['rule_text'])
        self.assertNotIn('cover more than', q['rule_text'])
        self.assertIn('on each whole preprocessed recording, before the zero Oz channel was inserted', q['source'])
        self.assertNotIn('before any window was cut', json.dumps(self.payload, ensure_ascii=False))
        ax = {x['id']: x['text'] for x in self.payload['axon']['limitations']}
        self.assertEqual(list(ax), ['pretraining-not-isolated', 'outcomes-known'])
        self.assertIn('cannot isolate what AXON’s pretraining contributes', ax['pretraining-not-isolated'])
        self.assertIn('the EEG-Captioner and Welch outcomes were known before AXON ran', ax['outcomes-known'])
        self.assertIs(self.payload['axon']['baseline']['isolates_pretraining'], False)
        self.assertIn('training sets overlap across folds', self.payload['interval']['scope'])

    def test_the_research_release_claims_no_authority_it_lacks(self):
        rr = self.payload['release_record']['research_release']
        self.assertIn('does not itself authorise publication', rr)
        self.assertIn('Publication on the site rests on the site owner’s decision of 2026-10-28.', rr)
        self.assertNotIn('leaves publication to the site', rr)
        self.assertNotRegex(json.dumps(self.payload), r'(?<![\w-])D\d{1,2}(?![\w-])')
        m = copy.deepcopy(MANIFEST)
        m['releaseRecord']['researchRelease'] = rr.replace('does not itself authorise publication',
                                                           'leaves publication to the site')
        with self.assertRaisesRegex(ValueError, 'does not itself authorise publication'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['releaseRecord']['researchRelease'] = rr.replace('the site owner’s decision of 2026-10-28',
                                                           'the owner’s decision D14')
        with self.assertRaisesRegex(ValueError, 'release record'):
            build(m)

    def test_released_files_are_never_edited(self):
        for ref in MANIFEST['published'].values():
            self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        for f in ('pilotStudies', 'neurolmEegmat'):
            body = (ex.PROJECT / MANIFEST['published'][f]['path']).read_text().lower()
            self.assertNotIn('captioner', body)
            self.assertNotIn('axon', body)

    def test_no_other_eegmat_figure_reaches_the_file(self):
        other = ex.other_eegmat_figures(self.docs)
        self.assertGreaterEqual(len(other), 30)
        self.assertFalse(other & set(ex.numbers(self.payload)))
        self.assertIn(0.6574074074074074, other)        # LaBraM last-block, one float away from EEG-Captioner's mean
        self.assertNotIn(0.6574074074074076, other)

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['axon']['protocol']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_status_comes_from_the_approval_records(self):
        m = copy.deepcopy(MANIFEST)
        ap = self.get(m['captioner']['approval'])
        ap['status'] = 'PENDING_INTERPRETATION_REVIEW'
        self.put(m['captioner']['approval'], ap)
        with self.assertRaisesRegex(ValueError, 'no longer passes the handoff'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        rv = self.get(m['axon']['review'])
        rv['decision'] = 'HOLD'
        self.put(m['axon']['review'], rv)
        with self.assertRaisesRegex(ValueError, 'no longer passes the aggregate release'):
            build(m)
        # An aggregate's own status field never stands in for the review; a disagreeing one stops the build.
        docs = self.docs_copy()
        docs['axon']['aggregate']['status'] = 'PENDING_INDEPENDENT_REVIEW'
        with self.assertRaisesRegex(ValueError, 'not the reviewed release'):
            ex.axon_bindings(docs)

    def test_an_aggregate_the_approvals_do_not_bind_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        o = self.get(m['captioner']['outcome'])
        o['aggregate_scores']['encoder']['mean_subject_BA'] = 0.70
        self.put(m['captioner']['outcome'], o)
        with self.assertRaisesRegex(ValueError, 'approval names another audit outcome'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        g = self.get(m['axon']['aggregate'])
        g['results']['axon']['mean_subject_BA'] = 0.72
        self.put(m['axon']['aggregate'], g)
        with self.assertRaisesRegex(ValueError, 'review approves another aggregate'):
            build(m)

    def test_the_baseline_must_be_the_shared_one(self):
        docs = self.docs_copy()
        docs['axon']['protocol']['inputs']['baseline_predictions']['sha256'] = '1' * 64
        with self.assertRaisesRegex(ValueError, 'reused other baseline predictions'):
            ex.shared_cache(docs)
        docs = self.docs_copy()
        cap = ex.captioner_values(docs)
        docs['axon']['aggregate']['results']['baseline']['mean_subject_BA'] = 0.68
        docs['axon']['aggregate']['results']['mean_difference'] = 0.7013888888888888 - 0.68
        with self.assertRaisesRegex(ValueError, 'baseline score is not the EEG-Captioner run'):
            ex.axon_values(docs, cap)

    def test_an_interval_that_no_longer_spans_zero_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'no longer spans zero'):
            ex.contrast('axon', 'welch-band-power', 'x', {'difference': 0.05, 'interval': [0.01, 0.1]})

    def test_a_resolved_exposure_or_another_licence_is_refused(self):
        docs = self.docs_copy()
        docs['axon']['aggregate']['quality_scope']['pretraining_exposure'] = 'not_exposed'
        cohort = ex.cohort_block(self.docs)
        qc = ex.qc_block(self.docs, cohort)
        welch = ex.welch_block(self.docs, cohort)
        ax = ex.axon_values(self.docs, ex.captioner_values(self.docs))
        with self.assertRaisesRegex(ValueError, 'quality scope changed'):
            ex.axon_block(docs, ax, cohort, qc, welch)
        docs = self.docs_copy()
        docs['axon']['card'] = docs['axon']['card'].replace('license: apache-2.0', 'license: mit')
        with self.assertRaisesRegex(ValueError, 'model card states another licence'):
            ex.axon_block(docs, ax, cohort, qc, welch)
        docs = self.docs_copy()
        docs['captioner']['intakeHandoff'] = docs['captioner']['intakeHandoff'].replace(
            'Portable weight metadata: Apache-2.0.', 'Portable weight metadata: CC BY-NC 4.0.')
        cap = ex.captioner_values(self.docs)
        with self.assertRaisesRegex(ValueError, 'intake licences'):
            ex.captioner_block(docs, cap, cohort, qc, welch)

    def test_a_changed_owner_decision_hold_or_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['approval']['ownerDecisions']['quoted']['D14'] = 'Hold the ten-second probes'
        with self.assertRaisesRegex(ValueError, 'D14 changed'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['approval']['decision'] = 'withhold'
        with self.assertRaisesRegex(ValueError, 'does not approve'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['holds'] = ['source QC']
        with self.assertRaisesRegex(ValueError, 'no hold'):
            build(m)

    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('per_subject', 'subject_ids', 'per_window_scores', 'predictions', 'features', 'folds_ba',
                    'confusion_matrix', 'pooled_macro_f1', 'macroF1', 'forward_counts', 'cpu_seconds',
                    'peak_rss_bytes', 'elapsed_seconds', 'flagged_channels', 'checked_files', 'fold_sizes_people'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'axon': [{key: 1}]})

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 3)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v1 rows'}, 'version label'), ({'scope': 'run in October'}, 'month'),
                         ({'scope': 'Added with new rows.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'AXON beats band power.'}, 'unsupported claim'),
                         ({'scope': 'AXON is better here.'}, 'unsupported claim'),
                         ({'scope': 'the best encoder on EEGMAT'}, 'unsupported claim'),
                         ({'scope': 'a clean cohort'}, 'unsupported claim'),
                         ({'scope': 'a 55% bet'}, 'commenter'), ({'scope': 'held-out 0.55'}, 'commenter'),
                         ({'scope': 'an ICLR 2027 entry'}, 'ICLR 2027'),
                         ({'scope': 'see arXiv:2609.08788'}, 'arXiv'),
                         ({'scope': 'as the owner’s decision D14 says'}, 'decision id'),
                         ({'scope': 'see Subject07 there'}, 'participant identifier'),
                         ({'scope': 'kept in predictions.npz'}, 'source file'),
                         ({'scope': 'kept in independent-result-audit-outcome.json'}, 'source file'),
                         ({'scope': 'a /' + 'mnt/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'Neither is shown to be better; outside every leaderboard.',
                        'question': 'Does AXON separate rest from arithmetic better than band power?'}, private)

    def test_licences_stay_with_their_part(self):
        for text, why in (('The AXON checkpoint is MIT.', 'MIT not tied'),
                          ('EEG-Captioner code is Apache-2.0.', 'Apache-2.0 not tied'),
                          ('The weights are BSD-3-Clause.', 'BSD-3-Clause not tied')):
            p = copy.deepcopy(self.payload)
            p['scope'] = text
            with self.assertRaisesRegex(ValueError, why):
                ex.licences_per_part(p)
        p = copy.deepcopy(self.payload)
        p['axon']['rights']['project']['licence'] = 'Apache-2.0'
        with self.assertRaisesRegex(ValueError, 'licences per part changed'):
            ex.licences_per_part(p)

    def test_withheld_values_are_absent(self):
        approved = {x['balanced_accuracy'] for k in ('eeg_captioner', 'axon') for x in self.payload[k]['arms']}
        design = {v for k in ('cohort', 'probe', 'interval') for v in ex.numbers(self.payload[k])}
        withheld = ex.withheld_values(self.docs, approved | design)
        self.assertGreaterEqual(len(withheld), 30)
        # Known withheld figures (the flagged instance counts, two per-fold scores, two accounting values), named by the
        # first 16 hex digits of the SHA-256 of their repr so that this public file does not print them.
        held = {hashlib.sha256(repr(v).encode()).hexdigest()[:16] for v in withheld}
        for anchor in ('2ecefe59ab6ae4e7', 'f7961248034a58c4', '6e7910214784f1c8', '32923ba7fbda4712',
                       '3e98a555efba3ced', 'd02e6b31c19c20d2'):
            self.assertIn(anchor, held)
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
            p['axon']['arms'][0]['balanced_accuracy'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'axon/arms/0/balanced_accuracy'):
            au.audit()

        def bound(p):
            p['eeg_captioner']['paired_difference']['interval_95'][1] = 0.0487
        with self.served(bound), self.assertRaisesRegex(au.AuditFailure, 'eeg_captioner/paired_difference/interval_95/1'):
            au.audit()

        def qc(p):
            q = p['source_annotation_qc']
            q['windows_meeting_rules'] = 1
            q['beside_every_score'] = q['beside_every_score'].replace('0 of 432', '1 of 432')
        with self.served(qc), self.assertRaisesRegex(au.AuditFailure, 'windows_meeting_rules'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['axon']['pooled_balanced_accuracy'] = 0.7013888888888888
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['axon']['identity']['checkpoint_bytes']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_wrong_flag_and_a_type_change(self):
        def flag(p):
            p['axon']['baseline']['matched'] = True
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'axon/baseline/matched'):
            au.audit()

        def typed(p):
            p['cohort']['people'] = 36.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'cohort/people'):
            au.audit()

        def first(p):
            p['axon']['audit']['first_audit']['kept'] = False
        with self.served(first), self.assertRaisesRegex(au.AuditFailure, 'first_audit/kept'):
            au.audit()

    def test_the_audit_catches_a_changed_label_line_or_licence(self):
        def label(p):
            p['axon']['arms'][1]['note'] = 'matched for this run'
        with self.served(label), self.assertRaisesRegex(au.AuditFailure, 'reviewed labels'):
            au.audit()

        def line(p):
            p['source_annotation_qc']['beside_every_score'] = ('0 of 432 windows, and 72 of 72 recordings, meet '
                                                               'EEG-Captioner’s source annotation-QC rules')
        with self.served(line), self.assertRaisesRegex(au.AuditFailure, 'another QC line'):
            au.audit()

        def licence(p):
            p['axon']['rights']['project']['licence'] = 'Apache-2.0'
        with self.served(licence), self.assertRaisesRegex(au.AuditFailure, 'module and project licences'):
            au.audit()

        def held(p):
            p['not_published'] = p['not_published'][:-1]
        with self.served(held), self.assertRaisesRegex(au.AuditFailure, 'not-published'):
            au.audit()

    def test_the_audit_catches_a_changed_scope_of_exactness_or_a_dropped_limit(self):
        def bound(p):
            p['eeg_captioner']['audit']['head_decision_score_error_below'] = 1e-7
        with self.served(bound), self.assertRaisesRegex(au.AuditFailure, 'head_decision_score_error_below'):
            au.audit()

        def renamed(p):
            a = p['eeg_captioner']['audit']
            a['outputs_reproduced_exactly'] = a.pop('hard_predictions_reproduced_exactly')
        with self.served(renamed), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def isolates(p):
            p['axon']['baseline']['isolates_pretraining'] = True
        with self.served(isolates), self.assertRaisesRegex(au.AuditFailure, 'axon/baseline/isolates_pretraining'):
            au.audit()

        def dropped(p):
            p['axon']['limitations'] = p['axon']['limitations'][:1]
        with self.served(dropped), self.assertRaisesRegex(au.AuditFailure, 'AXON’s own limitations'):
            au.audit()

        def delegated(p):
            r = p['release_record']
            r['research_release'] = r['research_release'].replace('does not itself authorise publication',
                                                                  'leaves publication to the site')
        with self.served(delegated), self.assertRaisesRegex(au.AuditFailure, 'research release'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
