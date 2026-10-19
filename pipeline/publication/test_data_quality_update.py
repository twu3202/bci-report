"""The data-quality release: what must follow from the pinned records, and what must stay out."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_data_quality_export as au
import export_data_quality_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


def step(payload, sid):
    return next(s for s in payload['shin2022']['coverage_chain'] if s['id'] == sid)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class DataQualityBoundary(unittest.TestCase):
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
        self.assertEqual(audit['figures_compared'],
                         audit['copied_exactly'] + audit['recomputed'] + audit['flags'] + audit['nulls_kept'])

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-data-quality-update-v1')
        self.assertEqual(p['release_id'], 'data-quality-update-20261020')
        self.assertEqual(p['generated_at'], '2026-10-20')
        self.assertEqual(p['question'], 'What do the files show once a public EEG dataset is checked end to end?')
        self.assertEqual([c['id'] for c in p['cases']], ['shin2022', 'eldbeta', 'zuco2'])
        self.assertEqual(p['placement']['sections'], ['shin2022', 'eldbeta', 'zuco2'])
        self.assertIs(p['placement']['leaderboard'], False)
        self.assertEqual(p['shin2022']['question'], 'What survives a participant-held-out check?')
        self.assertEqual(set(p['provenance']['source_export_sha256']), {'shin2022', 'eldbeta'})
        self.assertEqual(p['provenance']['source_export_sha256']['shin2022'][:8], '04a8b3a4')
        self.assertEqual(p['provenance']['source_export_sha256']['eldbeta'][:8], '01badee2')
        self.assertEqual(p['provenance']['release_audit_sha256'], {'shin2022': MANIFEST['sources']['shinReleaseAudit']['sha256'],
                                                                   'eldbeta': MANIFEST['sources']['eldbetaReleaseAudit']['sha256']})
        served = json.loads(ex.OUTPUTS[0].read_bytes())
        self.assertEqual(served['provenance']['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(p['not_published'], MANIFEST['notPublished'])

    # ------------------------------------------------------------------ Shin2022
    def test_the_shin_export_is_the_pinned_one(self):
        ref = MANIFEST['sources']['shinExport']
        self.assertTrue(ref['sha256'].startswith('04a8b3a4'))
        self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'])

    def test_the_shin_arms_are_the_export_verbatim(self):
        arms = self.payload['shin2022']['arms']
        export = self.docs['shinExport']['metrics']
        self.assertEqual([a['arm'] for a in arms], ['training_prior', 'normalized_spectral_ridge',
                                                    'retrospective_duration_ridge'])
        for a, m in zip(arms, export):
            self.assertEqual(json.dumps({k: a[k] for k in m}, sort_keys=True), json.dumps(m, sort_keys=True))
        want = [(50.00, 50.00, 50.00, 50.00), (52.59, 51.51, 53.66, 52.55), (52.33, 50.87, 54.02, 52.15)]
        for a, (pt, lo, hi, pooled) in zip(arms, want):
            self.assertEqual((r2(a['participant_mean_balanced_accuracy']), r2(a['participant_bootstrap_percentile_95'][0]),
                              r2(a['participant_bootstrap_percentile_95'][1]), r2(a['pooled_balanced_accuracy_secondary'])),
                             (pt, lo, hi, pooled))
        self.assertEqual([a['role'] for a in arms], ['reference', 'eeg', 'retrospective_control'])
        self.assertIn('known only after the trial ends', arms[2]['input'])
        iv = self.payload['shin2022']['interval']
        self.assertEqual((iv['resamples'], iv['seed'], iv['level']), (10000, 20261019, 0.95))

    def test_the_coverage_chain(self):
        p = self.payload
        want = {'recorded_runs': 110, 'byte_identical_pairs': 9, 'distinct_runs': 101, 'incomplete_run_held': 1,
                'complete_runs': 100, 'closed_windows': 2400, 'shorter_than_one_second': 167, 'duration_eligible': 2233,
                'signal_invalid': 13, 'signal_valid': 2220}
        self.assertEqual({s['id']: s['count'] for s in p['shin2022']['coverage_chain']}, want)
        self.assertEqual([s['id'] for s in p['shin2022']['coverage_chain']], list(want))
        self.assertEqual(step(p, 'distinct_runs')['closed_windows'], 2412)
        self.assertEqual(step(p, 'byte_identical_pairs')['pair_conditions'], ['BW30', 'NT0'])
        self.assertEqual(step(p, 'shorter_than_one_second')['by_target'], {'1': 76, '2': 91})
        self.assertEqual(step(p, 'duration_eligible')['by_target'], {'1': 1124, '2': 1109})
        inv = step(p, 'signal_invalid')
        self.assertEqual((inv['by_target'], inv['flat_on_all_channels'], inv['flat_on_some_channels'],
                          inv['non_finite_input_windows']), ({'1': 7, '2': 6}, 8, 5, 0))
        val = step(p, 'signal_valid')
        self.assertEqual(val['by_target'], {'1': 1117, '2': 1103})
        self.assertEqual(val['percent_of_closed_windows'], 92.5)
        self.assertEqual(round(val['percent_of_duration_eligible'], 2), 99.42)
        self.assertEqual(p['shin2022']['labels']['classes'], {'1': 'instructed right target', '2': 'instructed left target'})

    def test_the_files_against_the_catalog(self):
        c = self.payload['shin2022']['catalog']
        self.assertEqual((c['catalog_trial_seconds'], c['header_feedback_cap_seconds'], c['headers_read']), (6, 6, 110))
        body = ex.OUTPUTS[0].read_text()
        self.assertIsNone(re.search(r'(?<![\d.,])2,?640(?!\d)', body))     # MOABB's trial count, as a figure
        self.assertNotIn(2640, ex.ints(self.payload))
        self.assertNotIn(11, ex.ints(self.payload))

    def test_the_checks_and_holds(self):
        hc = {h['id']: h for h in self.payload['shin2022']['how_checked']}
        self.assertEqual(hc['strict-protocol-stopped']['state'], 'held')
        self.assertEqual(hc['strict-protocol-stopped']['models_fitted'], 0)
        self.assertEqual(hc['score-free-census']['windows'], 2233)
        self.assertIs(hc['score-free-census']['scores_computed'], False)
        self.assertLess(hc['independent-audit']['max_decision_difference'], 1e-13)
        self.assertEqual(len(self.payload['shin2022']['holds']), 7)
        self.assertIn('unknown', self.payload['shin2022']['holds'][5])

    # ------------------------------------------------------------------ eldBETA and ZuCo 2.0
    def test_eldbeta_is_status_and_counts_only(self):
        e = self.payload['eldbeta']
        self.assertEqual(e['status'], 'score_held')
        self.assertEqual(e['counts'], {'participants_run': 1, 'published_participants': 100, 'blocks': 7, 'targets': 9,
                                       'trials': 63, 'trials_passing_checks': 63, 'trials_dropped': 0,
                                       'non_finite_values_in_analysed_windows': 0,
                                       'non_finite_values_outside_analysed_windows': 248320})
        self.assertIs(e['flags']['header_calibration_applied'], True)
        self.assertIs(e['flags']['derived_matlab_epochs_used'], False)
        self.assertIs(e['flags']['score_published'], False)
        self.assertIn('248,320', e['status_text'])
        held = self.docs['eldbetaExport']
        body = ex.OUTPUTS[0].read_text()
        for text in ('26/63', '26 of 63', '41.27', '11.11', '0.4126984126984127', '0.1111111111111111'):
            self.assertNotIn(text, body)
        self.assertNotIn(held['correct'], ex.ints(self.payload))
        self.assertNotIn(held['top1_accuracy'], ex.floats(self.payload))
        self.assertNotIn('verified', json.dumps(e).lower().replace('unverified', ''))
        self.assertEqual(e['related']['model_name'], 'SingLEM')

    def test_zuco2_has_no_figure(self):
        z = self.payload['zuco2']
        self.assertEqual(z['status'], 'no_score')
        self.assertEqual(z['hold'], ex.ZUCO_HOLD)
        for trail, v in ex.leaves(z, '$.zuco2'):
            if trail in ('$.zuco2.id', '$.zuco2.section', '$.zuco2.name') or trail.startswith('$.zuco2.source'):
                continue
            self.assertFalse(ex.number(v), trail)
            self.assertFalse(isinstance(v, str) and re.search(r'\d', v), trail)
        self.assertIs(z['flags']['score_computed'], False)
        self.assertIs(z['flags']['data_redistributed'], False)
        self.assertIs(z['consent_and_ethics']['read'], False)
        body = ex.OUTPUTS[0].read_text()
        for text in ('sub-YAC', 'run-6', '4287888', '4,287,888', '106', '2^32'):
            self.assertNotIn(text, body)

    def test_register_content_and_the_commenters_figure_are_absent(self):
        body = ex.OUTPUTS[0].read_text()
        for text in ('BI2013a', 'Brain Invaders', '2669187', '1494163', 'ICLR', 'OpenReview', 'iMINDBench'):
            self.assertNotIn(text, body)
        self.assertIsNone(re.search(r'(?<![\d.])55(?:\.0+)?\s*%|fifty[- ]five|(?<![\d.])0\.55(?!\d)', body, re.I))
        self.assertFalse({55, 0.55} & (set(ex.ints(self.payload)) | set(ex.floats(self.payload))))

    # ------------------------------------------------------------------ consent, ethics, rights
    def test_consent_and_ethics_are_the_a3_record(self):
        a3 = self.docs['consent']['sources']
        for case in ('shin2022', 'eldbeta'):
            ce, src = self.payload[case]['consent_and_ethics'], a3[case]
            self.assertEqual(ce['ethics_approval']['statement'], src['ethics']['statement'])
            self.assertEqual(ce['ethics_approval']['quote'], src['ethics_quote'])
            self.assertEqual(ce['informed_consent']['quote'], src['consent_quote'])
            self.assertEqual(ce['gaps'], src['gaps'])
        self.assertIsNone(self.payload['shin2022']['consent_and_ethics']['ethics_approval']['approval_number'])
        self.assertEqual(self.payload['eldbeta']['consent_and_ethics']['ethics_approval']['approval_number'], '20210032')
        self.assertEqual(self.payload['shin2022']['consent_and_ethics']['gaps'][0]['field'], 'ethics.approval_number')

    def test_attribution_and_licences(self):
        for case, doi in (('shin2022', ex.SHIN_DOI), ('eldbeta', ex.ELD_DOI)):
            r = self.payload[case]['rights']
            self.assertTrue(r['attribution'].endswith('Derived analysis by BCI Report; not endorsed by the authors.'))
            self.assertIn(doi, r['attribution'])
            self.assertEqual((r['license'], r['licenseUrl']), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'))
        self.assertIn('Hyonyoung Shin, Daniel Suma and Bin He', self.payload['shin2022']['rights']['attribution'])
        self.assertEqual(self.payload['zuco2']['source']['licence_as_stated'], 'CC-BY-4.0')

    def test_released_files_are_never_edited(self):
        for ref in MANIFEST['published'].values():
            self.assertEqual(digest((ex.PROJECT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        fm = MANIFEST['published']['foundationModels']['path']
        self.assertEqual((ex.PROJECT / fm).read_bytes(),
                         (ex.PROJECT / fm.replace('site/src/data', 'site/public/data')).read_bytes())

    def test_no_string_has_lost_its_spaces(self):
        for trail, text in ex.strings(self.payload):
            self.assertIsNone(ex.malformed(text), trail)
        for limitation in self.docs['shinExport']['limitations'] + [self.docs['shinExport']['metric_definition']]:
            self.assertNotIn(limitation, ex.OUTPUTS[0].read_text())

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['sources']['shinExport']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_arms_other_than_the_reviewed_ones_are_refused(self):
        # A changed audit is not the one the release review binds; a changed export is not the one the consistency
        # review names; with both reviews' bindings in place, the audit and the export must still agree.
        m = copy.deepcopy(MANIFEST)
        a = self.get(m['sources']['shinReleaseAudit'])
        a['independent_metrics'][1]['participant_mean_balanced_accuracy'] = 0.53
        self.put(m['sources']['shinReleaseAudit'], a)
        with self.assertRaisesRegex(ValueError, 'release review binds the audit'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        e = self.get(m['sources']['shinExport'])
        e['metrics'][1]['participant_mean_balanced_accuracy'] = 0.53
        self.put(m['sources']['shinExport'], e)
        with self.assertRaisesRegex(ValueError, 'consistency review names the export'):
            build(m)
        docs = copy.deepcopy(self.docs)
        docs['shinReleaseAudit']['independent_metrics'][1]['participant_mean_balanced_accuracy'] = 0.53
        with self.assertRaisesRegex(ValueError, 'reconstructed other metrics'):
            ex.shin_reviews(docs, MANIFEST)

    def test_a_chain_that_does_not_add_up_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        la = self.get(m['sources']['shinLabelDuplicateAudit'])
        la['observed']['unique_raw_views'] = 102
        self.put(m['sources']['shinLabelDuplicateAudit'], la)
        with self.assertRaisesRegex(ValueError, 'distinct runs'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        cr = self.get(m['sources']['shinCensusReview'])
        cr['independent_categories']['all16_constant']['affected_windows'] = 9
        self.put(m['sources']['shinCensusReview'], cr)
        with self.assertRaisesRegex(ValueError, 'flat windows'):
            build(m)

    def test_a_changed_owner_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        od = json.loads((ex.PROJECT / m['approval']['ownerDecisions']['path']).read_bytes())
        od['decisions']['D2']['answer'] = 'Publish the one-participant score'
        path = Path(self.tmp.name) / 'owner-decisions.json'
        path.write_text(json.dumps(od))
        m['approval']['ownerDecisions']['path'] = str(path)
        with self.assertRaisesRegex(ValueError, 'owner decision D2 changed'):
            build(m)

    def test_a_capture_other_than_the_a3_one_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        a3 = self.get(m['consent']['statements'])
        a3['sources']['shin2022']['capture_sha256'] = '0' * 64
        self.put(m['consent']['statements'], a3)
        with self.assertRaisesRegex(ValueError, 'not the bytes the consent record names'):
            build(m)

    def test_the_held_eldbeta_score_is_refused(self):
        p = copy.deepcopy(self.payload)
        p['eldbeta']['counts']['correct'] = 26
        with self.assertRaisesRegex(ValueError, 'held-score field'):
            ex.scrub_check(p)
        p = copy.deepcopy(self.payload)
        p['eldbeta']['status_text'] += ' It picked the target in 26 of 63 trials.'
        with self.assertRaisesRegex(ValueError, 'held or withheld figure'):
            ex.prose_check(p, set())
        p = copy.deepcopy(self.payload)
        p['eldbeta']['flags']['share'] = self.docs['eldbetaExport']['top1_accuracy']
        with self.assertRaisesRegex(ValueError, 'held eldBETA score'):
            ex.eldbeta_has_no_score(p, self.docs)

    def test_a_figure_in_the_zuco_case_is_refused(self):
        for edit in (lambda z: z.__setitem__('finding', 'The run has 106 stimulus markers.'),
                     lambda z: z['flags'].__setitem__('markers', 3)):
            p = copy.deepcopy(self.payload)
            edit(p['zuco2'])
            with self.assertRaisesRegex(ValueError, 'ZuCo 2.0 case'):
                ex.zuco_has_no_figure(p)

    def test_per_participant_and_internal_fields_are_refused(self):
        for key in ('per_participant_closed_windows_min', 'participant_denominator_min_max', 'feedback_quantiles_seconds',
                    'median', 'predictions', 'cpu_seconds', 'combined_output_bytes', 'private_receipt', 'onset'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'shin2022': {key: 1}})

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 3)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v2 diagnostic'}, 'version label'), ({'scope': 'run in October'}, 'month'),
                         ({'scope': 'Updated with the census.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'The spectral arm is significantly above chance.'}, 'claim'),
                         ({'scope': 'Spectral features decode pure motor imagery.'}, 'claim'),
                         ({'scope': 'Units were verified.'}, 'claim'),
                         ({'scope': 'A held-out check, not a benchmark.'}, 'hedge'),
                         ({'scope': 'Only10participants and one recorded day'}, 'lost its spaces'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'the S01 recordings'}, 'participant identifier'),
                         ({'scope': 'BI2013a is planned.'}, 'register-only'),
                         ({'scope': 'the thread bet of 55%'}, 'commenter'),
                         ({'scope': 'MOABB lists 2,640 trials.'}, 'held or withheld'),
                         ({'scope': 'a /' + 'home/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'Shin2022’s windows; 16-channel dry EEG at 250 Hz; EEG1–EEG16.'}, private)

    def test_withheld_values_are_absent(self):
        fl, it = ex.withheld_values(self.docs)
        self.assertGreaterEqual(len(fl), 15)
        self.assertGreaterEqual(len(it), 10)
        self.assertFalse(fl & set(ex.floats(self.payload)))
        self.assertFalse(it & set(ex.ints(self.payload)))

    def test_no_private_path_or_name_reaches_the_files(self):
        private = ex.private_names(self.docs)
        for path in (*ex.OUTPUTS, ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            self.assertIsNone(ex.LOCAL_ROOTS.search(body), path.name)
            for n in private:
                self.assertIsNone(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', body, re.I), path.name)

    def test_the_served_file_passes_the_publication_guard(self):
        ex.validate_public(json.loads(ex.OUTPUTS[0].read_bytes()))

    # ------------------------------------------------------------------ the independent audit
    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            p['shin2022']['arms'][1]['participant_bootstrap_percentile_95'][0] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'normalized_spectral_ridge: not the export'):
            au.audit()

        def pooled(p):
            p['shin2022']['arms'][2]['input'] = 'x'
            p['eldbeta']['counts']['trials_passing_checks'] = 62
        with self.served(pooled), self.assertRaisesRegex(au.AuditFailure, 'counts/trials_passing_checks'):
            au.audit()

        def chain(p):
            step(p, 'signal_invalid')['flat_on_some_channels'] = 4
        with self.served(chain), self.assertRaisesRegex(au.AuditFailure, 'flat_on_some_channels'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['eldbeta']['counts']['median_trials'] = 9
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del step(p, 'duration_eligible')['by_target']['2']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_and_a_type_change(self):
        def zero(p):
            p['shin2022']['consent_and_ethics']['ethics_approval']['approval_number'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def typed(p):
            step(p, 'recorded_runs')['count'] = 110.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'coverage_chain/0/count'):
            au.audit()

    def test_the_audit_catches_a_changed_consent_string_or_attribution(self):
        def consent(p):
            p['eldbeta']['consent_and_ethics']['informed_consent']['statement'] = 'Consent was oral.'
        with self.served(consent), self.assertRaisesRegex(au.AuditFailure, 'A3 record'):
            au.audit()

        def attribution(p):
            p['shin2022']['rights']['attribution'] = p['shin2022']['rights']['attribution'].rsplit(' Derived', 1)[0]
        with self.served(attribution), self.assertRaisesRegex(au.AuditFailure, 'attribution'):
            au.audit()

    def test_the_audit_catches_held_text_and_zuco_digits(self):
        def held(p):
            p['eldbeta']['status_text'] += ' CCA picked 26 of 63.'
        with self.served(held), self.assertRaisesRegex(au.AuditFailure, 'held eldBETA score'):
            au.audit()

        def digit(p):
            p['zuco2']['scope'] = 'The hold covers run 6.'
        with self.served(digit), self.assertRaisesRegex(au.AuditFailure, 'a digit'):
            au.audit()

        def register(p):
            p['shin2022']['catalog']['register'] = 'BI2013a sits in the register.'
        with self.served(register), self.assertRaisesRegex(au.AuditFailure, 'BI2013a'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
