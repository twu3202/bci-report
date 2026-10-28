"""The dataset-checks release: what must follow from the pinned records, and what must stay out."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_dataset_checks_export as au
import export_dataset_checks_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
KIM, MIND, DAMM, NEBULA = ex.KIM, ex.MIND, ex.DAMM, ex.NEBULA


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class DatasetChecksBoundary(unittest.TestCase):
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
        self.assertEqual(p['schema_version'], 'bci-report-dataset-checks-update-v1')
        self.assertEqual(p['release_id'], 'dataset-checks-update-20261028')
        self.assertEqual(p['generated_at'], '2026-10-28')
        self.assertEqual([c['id'] for c in p['cases']], [KIM, MIND, DAMM, NEBULA])
        self.assertEqual([c['status'] for c in p['cases']], ['released', 'released_conditional', 'score_held', 'score_held'])
        self.assertEqual(p['placement']['page'], '/topics/data-quality/')
        self.assertEqual(p['placement']['page_order'], ['shin2022', KIM, MIND, 'eldbeta', DAMM, NEBULA, 'zuco2'])
        self.assertIs(p['placement']['leaderboard'], False)
        self.assertIs(p['placement']['core_matrix'], False)
        pv = p['provenance']
        self.assertEqual(set(pv['source_export_sha256']), {KIM, MIND})
        self.assertEqual(pv['source_export_sha256'][KIM][:8], 'b3043fb0')
        self.assertEqual(pv['source_export_sha256'][MIND][:8], 'ff43f57f')
        self.assertEqual(pv['holds'], ['kim-amplitude-dependent-models', 'damm-one-participant-score',
                                       'nebula-one-participant-scores'])
        served = json.loads(ex.OUTPUTS[0].read_bytes())
        self.assertEqual(served['provenance']['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(p['not_published'], MANIFEST['notPublished'])
        self.assertEqual(p['holds'], MANIFEST['holds'])

    def test_data_quality_keeps_its_bytes(self):
        old = json.loads((ex.PROJECT / 'research/publication_review_20261020/data-quality-export-audit.json').read_bytes())
        for path in ('site/src/data/data-quality-update.json', 'site/public/data/data-quality-update.json'):
            self.assertEqual(digest((ex.PROJECT / path).read_bytes()), old['export_sha256'], path)
        self.assertEqual(MANIFEST['published']['dataQuality']['sha256'], old['export_sha256'])
        self.assertEqual(self.payload['provenance']['released_file_sha256'],
                         {'data-quality-update.json': old['export_sha256']})

    # ------------------------------------------------------------------ Kim beta-range
    def test_kim_figures_are_the_audit_aggregate(self):
        ref = MANIFEST['sources']['kimAggregate']
        self.assertTrue(ref['sha256'].startswith('b3043fb0'))
        self.assertTrue(ref['path'].endswith('kim_betarange/review/independent_audit/Kim_Independent_Audit_Aggregate.json'))
        ag = self.docs['kimAggregate']
        r = self.payload[KIM]['result']
        self.assertEqual(r['mean_participant_accuracy'], ag['mean_accuracy'])
        self.assertEqual(r['difference_from_chance'], ag['mean_difference'])
        self.assertEqual(r['difference_interval_95'], ag['participant_bootstrap_95_percentile'])
        self.assertEqual(r['chance'], 0.025)
        self.assertEqual(r['accuracy_interval_95'], [v + 0.025 for v in ag['participant_bootstrap_95_percentile']])
        self.assertEqual((r2(r['mean_participant_accuracy']), r2(r['accuracy_interval_95'][0]),
                          r2(r['accuracy_interval_95'][1])), (53.40, 45.89, 61.01))
        iv = self.payload[KIM]['interval']
        self.assertEqual((iv['resamples'], iv['seed'], iv['level'], iv['test']), (20000, 20261026, 0.95, False))
        body = ex.OUTPUTS[0].read_text()
        for malformed in ('9, 600', '9, 083, 420, 480', 'All40', '40participants'):
            self.assertNotIn(malformed, body)

    def test_kim_cohort_method_and_intake(self):
        k = self.payload[KIM]
        self.assertEqual(k['question'], 'What does training-free CCA give on 40 frequencies in the beta range?')
        self.assertEqual(k['cohort'], {'participants': 40, 'blocks': 240, 'blocks_each': 6, 'recording_days_each': 1,
                                       'trials': 9600, 'targets': 40, 'trials_per_target_each': 6,
                                       'complete_cohort': True})
        m = k['method']
        self.assertEqual((m['channels'], m['sampling_hz'], m['window_seconds'], m['window_samples'], m['band_hz'],
                          m['harmonics'], m['training_free']), (11, 1024, 2, 2048, [13, 44], 2, True))
        self.assertIn('M1 and M2', m['reference'])
        ik = k['intake']
        self.assertEqual((ik['task_files'], ik['md5_checked'], ik['md5_matched']), (40, 40, 40))
        self.assertEqual((ik['frequency_lowest_hz'], ik['frequency_highest_hz']), (14.0, 21.8))
        self.assertEqual(ik['stored_target_order'], '14 + j + 0.2·i Hz, for row i = 0…4 and column j = 0…7')
        self.assertIs(ik['stored_order_ascending'], False)
        self.assertIs(ik['moabb_list_ascending'], True)
        self.assertEqual(k['hold']['id'], 'kim-amplitude-dependent-models')
        self.assertEqual(k['aliases'], ['Kim2025BetaRange', 'Figshare 28806815', 'doi:10.1038/s41597-025-06032-2'])
        self.assertEqual(k['dataset_page'], '/datasets/kim2025-beta-range/')
        self.assertIs(k['method_link'], False)
        self.assertEqual({c['id'] for c in k['caveats']},
                         {'as-stored-amplitudes', 'nominal-onset', 'one-day', 'offline', 'own-pipeline',
                          'other-ssvep-datasets', 'interval', 'fixtures'})
        hc = {h['id']: h for h in k['how_checked']}
        self.assertEqual((hc['independent-audit']['fixtures'], hc['independent-audit']['fixtures_matched']), (60, 60))

    def test_kim_rights(self):
        r = self.payload[KIM]['rights']
        self.assertEqual((r['license'], r['licenseUrl']), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'))
        self.assertEqual(r['source'], 'https://doi.org/10.6084/m9.figshare.28806815.v3')
        self.assertEqual(r['terms']['data_licence']['pinned_version'], 3)
        self.assertEqual(r['terms']['paper_cited_version']['version'], 2)
        ce = self.payload[KIM]['consent_and_ethics']
        self.assertEqual(ce['ethics_approval']['approval_number'], '20211201-HR-64-02-04')
        self.assertIs(ce['informed_consent']['stated'], True)

    # ------------------------------------------------------------------ MIND
    def test_mind_aggregate_is_read_unchanged_and_its_status_comes_from_the_review(self):
        ref = MANIFEST['sources']['mindAggregate']
        self.assertTrue(ref['sha256'].startswith('ff43f57f'))
        self.assertEqual(self.docs['mindAggregate']['scientific_release_review'], 'PENDING_INTERPRETATION_REVIEW')
        self.assertTrue(self.docs['mindInterpretationReview']['aggregate_sha256'].startswith('ff43f57f'))
        self.assertTrue(MANIFEST['sources']['mindInterpretationReview']['sha256'].startswith('8fd28353'))
        self.assertNotIn('PENDING', ex.OUTPUTS[0].read_text())
        m = copy.deepcopy(MANIFEST)
        r = self.get(m['sources']['mindInterpretationReview'])
        r['decision'] = 'HOLD'
        self.put(m['sources']['mindInterpretationReview'], r)
        with self.assertRaisesRegex(ValueError, 'interpretation review binds other files'):
            build(m)

    def test_mind_primary_panel_and_contrasts(self):
        m = self.payload[MIND]
        self.assertEqual(m['question'], 'What do stored markers support in a motor-imagery release?')
        self.assertEqual(m['unit'], 'record ID')
        pairs = {p['pair']: p for p in m['primary']['pairs']}
        self.assertEqual([r2(pairs['4/5'][a]) for a in ('csp_lda', 'ordinal_lookup', 'majority')], [56.96, 47.62, 50.00])
        self.assertEqual([r2(pairs['6/7'][a]) for a in ('csp_lda', 'ordinal_lookup', 'majority')], [51.85, 45.24, 50.00])
        self.assertEqual((m['primary']['record_ids'], m['primary']['runs'], m['primary']['trials']), (28, 84, 3360))
        want = [('4/5', 'ordinal_lookup', 9.35, -2.68, 20.00, True), ('4/5', 'majority', 6.96, 4.05, 10.00, False),
                ('6/7', 'ordinal_lookup', 6.61, -4.05, 15.95, True), ('6/7', 'majority', 1.85, -0.48, 4.23, True)]
        got = [(c['pair'], c['control'], r2(c['mean_difference']), r2(c['resampling_range'][0]),
                r2(c['resampling_range'][1]), c['range_spans_zero']) for c in m['contrasts']]
        self.assertEqual(got, want)
        ag = self.docs['mindAggregate']['metrics']['primary']
        self.assertEqual(m['contrasts'][0]['mean_difference'], ag['4_5']['mean_paired_ID_differences']['order'])
        rs = m['resampling']
        self.assertEqual((rs['draws'], rs['seed'], rs['percentiles']), (20000, 20261028, [2.5, 97.5]))
        self.assertIs(rs['confidence_interval'], False)
        self.assertIn('no confidence intervals', rs['text'])

    def test_mind_schedule_and_coverage(self):
        m = self.payload[MIND]
        sched = {p['pair']: p for p in m['schedule']['pairs']}
        self.assertEqual((sched['4/5']['primary_ids_repeating_one_schedule'], sched['4/5']['primary_ids_mixing_schedules']),
                         (6, 22))
        self.assertEqual((sched['6/7']['primary_ids_repeating_one_schedule'], sched['6/7']['primary_ids_mixing_schedules']),
                         (5, 23))
        self.assertTrue(all(p['schedules'] == 2 and p['trials_per_schedule'] == 20 and p['complementary']
                            for p in m['schedule']['pairs']))
        self.assertEqual(m['schedule']['panel'], 'primary')
        cov = {c['id']: c for c in m['coverage']}
        self.assertEqual((cov['runs_in_release']['count'], cov['overfull_first_runs']['count'],
                          cov['runs_evaluated']['count'], cov['runs_evaluated']['trials']), (90, 2, 88, 3520))
        self.assertEqual(cov['overfull_first_runs']['role'], 'excluded')
        p = m['processing']
        self.assertEqual((p['channels'], p['sampling_hz'], p['band_hz'], p['resampled_hz'], p['window_after_marker_seconds'],
                          p['window_samples'], p['csp_components']), (64, 1000, [8, 30], 200, [1, 9], 1600, 4))

    def test_mind_secondary_panel_has_no_interval_and_no_census(self):
        s = self.payload[MIND]['secondary']
        self.assertIsNone(s['interval'])
        self.assertIs(s['pooled_with_primary'], False)
        self.assertEqual((s['record_ids'], s['runs'], s['trials']), (2, 4, 160))
        pairs = {p['pair']: p for p in s['pairs']}
        self.assertEqual([r2(pairs['4/5'][a]) for a in ('csp_lda', 'ordinal_lookup', 'majority')], [53.75, 50.0, 50.0])
        self.assertEqual([r2(pairs['6/7'][a]) for a in ('csp_lda', 'ordinal_lookup', 'majority')], [50.0, 50.0, 50.0])
        self.assertEqual(set(s), {'record_ids', 'runs', 'trials', 'design', 'interval', 'pooled_with_primary', 'pairs', 'text'})
        self.assertNotIn('secondary_all_two_same', ex.OUTPUTS[0].read_text())
        for pair in s['pairs']:
            self.assertFalse({'schedules', 'primary_ids_repeating_one_schedule', 'mean_difference'} & set(pair))
        p = copy.deepcopy(self.payload)
        p[MIND]['secondary']['secondary_all_two_same'] = 1
        with self.assertRaisesRegex(ValueError, 'refused field'):
            ex.scrub_check(p)

    def test_mind_terms_and_ethics(self):
        r = self.payload[MIND]['rights']
        st = {t['source']: t for t in r['terms']['statements']}
        self.assertEqual({k: v['value'] for k, v in st.items()},
                         {'paper': 'CC BY 4.0', 'archive dataset description': 'CC BY 4.0', 'MOABB adapter': 'CC BY-NC 4.0',
                          'ScienceDB record page': 'CC BY-NC 4.0'})
        self.assertIs(st['ScienceDB record page']['read_in_this_release'], True)
        self.assertIs(r['terms']['terms_of_use_page_read'], False)
        self.assertIs(r['terms']['redistributed'], False)
        self.assertEqual(r['licenses_stated'], ['CC BY 4.0', 'CC BY-NC 4.0'])
        self.assertNotIn('license', r)
        self.assertNotIn('licenseUrl', r)
        terms = {c['id']: c['text'] for c in self.payload[MIND]['caveats']}['terms']
        self.assertIn('ScienceDB’s terms-of-use page was not read', terms)
        ce = self.payload[MIND]['consent_and_ethics']
        self.assertIsNone(ce['ethics_approval']['body'])
        self.assertIsNone(ce['ethics_approval']['approval_number'])
        self.assertIsNone(ce['read_at'])
        a2 = self.docs['consent']['sources'][MIND]
        self.assertEqual(ce['informed_consent']['quote'], a2['consent_quote'])
        self.assertEqual(ce['ethics_approval']['quote'], a2['ethics_quote'])
        self.assertEqual(ce['capture_sha256'], a2['ethics_consent_source']['capture_sha256'])
        self.assertNotRegex(json.dumps(self.payload[MIND], ensure_ascii=False), r'\bV4\b|2602\.04299v1(?!")')

    # ------------------------------------------------------------------ Damm and NeBULA (one person, scores held)
    def test_damm_and_nebula_hold_no_score(self):
        for case in (DAMM, NEBULA):
            for trail, v in ex.leaves(self.payload[case], f'$.{case}'):
                self.assertNotIsInstance(v, float, trail)
                key = trail.rsplit('.', 1)[-1].lower()
                for frag in ('accuracy', 'correct', 'chance', 'macro', 'balanced', 'percent', 'fraction', 'interval',
                             'difference', 'paired'):
                    self.assertNotIn(frag, key, trail)
                if isinstance(v, str):
                    self.assertNotIn('%', v, trail)
                    self.assertNotIn('percent', v.lower(), trail)
        body = ex.OUTPUTS[0].read_text()
        for text in ('28.00', '25.33', '22.67', '17.33', '26.67', '18.67', '21.33', '14.67', '39.26', '42.84', '64.07',
                     '34.44', '57.53', '63.09', '5.56', '23.83', '24.81', '24.94', '34.69', '27.96', '52.51', '55.19',
                     'both-correct', 'order control reached'):
            self.assertNotIn(text, body)
        held = set(ex.held_values(self.docs))
        self.assertGreaterEqual(len(held), 30)
        self.assertFalse(held & set(ex.floats(self.payload)))
        self.assertIs(self.payload[DAMM]['flags']['score_published'], False)
        self.assertIs(self.payload[NEBULA]['flags']['score_published'], False)
        self.assertIs(self.payload[NEBULA]['flags']['order_diagnostic_comparison_published'], False)
        self.assertNotIn('order_diagnostic_compared', ex.OUTPUTS[0].read_text())

    def test_a_comparison_without_a_number_is_refused(self):
        for case, where, text in ((NEBULA, 'status_text', ' The order diagnostic scored higher than the EEG arm.'),
                                  (DAMM, 'holds', 'The primary variant was above chance in both directions.'),
                                  (NEBULA, 'holds', 'EMG exceeded the EEG arm.'),
                                  (DAMM, 'status_text', ' The precue control did better than the primary variant.'),
                                  (NEBULA, 'status_text', ' Fusion was lower, compared with the order diagnostic.'),
                                  (DAMM, 'status_text', ' The shuffle came out worse.'),
                                  (NEBULA, 'status_text', ' EEG sat below chance.')):
            p = copy.deepcopy(self.payload)
            if where == 'holds':
                p[case]['holds'].append(text)
            else:
                p[case][where] += text
            with self.assertRaisesRegex(ValueError, 'comparison word'):
                ex.held_cases_have_no_score(p, self.docs)
        p = copy.deepcopy(self.payload)
        p['holds'][2]['reason'] = 'One participant; the order diagnostic scored above the EEG arm.'
        with self.assertRaisesRegex(ValueError, 'comparison word'):
            ex.held_cases_have_no_score(p, self.docs)
        p = copy.deepcopy(self.payload)
        p['release_record'][DAMM] += ' The primary variant beat the order controls.'
        with self.assertRaisesRegex(ValueError, 'comparison word'):
            ex.held_cases_have_no_score(p, self.docs)
        ex.held_cases_have_no_score(self.payload, self.docs)

        def compare(p):
            p[NEBULA]['status_text'] += ' The order diagnostic scored higher than the EEG arm.'
        with self.served(compare), self.assertRaisesRegex(au.AuditFailure, 'comparison word'):
            au.audit()

        def chance(p):
            p[DAMM]['holds'].append('The primary variant was above chance in both directions.')
        with self.served(chance), self.assertRaisesRegex(au.AuditFailure, 'comparison word'):
            au.audit()

    def test_damm_facts(self):
        d = self.payload[DAMM]
        self.assertEqual((d['design']['participants_run'], d['design']['delivered_cues'],
                          d['design']['trials_per_held_out_run'], d['design']['classes'], d['design']['directions']),
                         (1, 150, 75, 5, 2))
        self.assertEqual((d['files']['scalp_channels'], d['files']['sampling_hz'], d['files']['state_blocks_per_run']),
                         (62, 512, 227))
        self.assertEqual(len(d['variants']), 8)
        self.assertEqual(d['variant_directions_audited'], 16)
        self.assertEqual(d['held']['id'], 'damm-one-participant-score')
        self.assertTrue(any('sidecars and the counterbalancing log disagree' in h for h in d['holds']))
        self.assertTrue(any('physical trigger timing is not validated' in h for h in d['holds']))
        self.assertTrue(any('sequential-order runs were not evaluated' in h for h in d['holds']))
        r = d['rights']
        self.assertEqual(r['license'], 'CC0')
        self.assertIs(r['terms']['license_file_present'], False)
        ce = d['consent_and_ethics']
        self.assertIs(ce['informed_consent']['stated'], False)
        self.assertEqual(ce['ethics_approval']['approval_number'], '26907/001')
        self.assertEqual([g['field'] for g in ce['gaps']], ['consent'])

    def test_nebula_facts(self):
        n = self.payload[NEBULA]
        self.assertEqual((n['design']['trials'], n['design']['trials_by_condition']), (89, {'free': 29, 'low': 30, 'high': 30}))
        self.assertEqual((n['eeg']['channels'], n['eeg']['sampling_hz']), (127, 1000))
        ff = n['file_facts']
        self.assertEqual((ff['boundary_ties'], ff['boundary_ties_by_condition']), (25, {'free': 7, 'low': 9, 'high': 9}))
        self.assertEqual((ff['emg_channel_rows'], ff['emg_channels_in_metadata'], ff['stored_markers']), (11, 16, 356))
        self.assertIs(ff['emg_rows_relabelled'], False)
        self.assertIs(ff['parser_fix_reviewed'], True)
        self.assertIs(ff['emg_eeg_sample_lengths_equal'], True)
        a = n['arms']
        self.assertEqual((a['eeg_fits'], a['emg_and_fusion_fits']), (15, 15))
        self.assertIs(a['pretrained_model'], False)
        self.assertEqual([x['id'] for x in a['emg_and_fusion']], ['emg', 'fusion', 'emg_precue', 'emg_shuffle',
                                                                  'fusion_shuffle'])
        self.assertEqual(n['held']['id'], 'nebula-one-participant-scores')
        self.assertFalse(any('FCz' in h for h in n['holds']))
        self.assertFalse(any(re.search(r'\d', h) for h in n['holds']), 'no participant count in the holds')
        body = json.dumps(n, ensure_ascii=False)
        for per_run in ('327892', '455262', '467828', '327,892'):
            self.assertNotIn(per_run, body)
        z = n['rights']['terms']['zenodo_13627307']
        self.assertIs(z['registered_public_record'], False)
        self.assertIsNone(z['terms'])
        self.assertEqual(n['rights']['license'], 'CC BY 4.0')
        self.assertEqual(n['consent_and_ethics']['ethics_approval']['approval_number'], '784/2022')

    def test_nebula_participant_counts_as_each_source_states_them(self):
        n = self.payload[NEBULA]['design']
        self.assertNotIn('published_participants', n)
        pc = n['participant_counts']
        self.assertEqual((pc['paper_and_record_description'], pc['participant_archives_in_record'], pc['moabb_catalog']),
                         (40, 39, 39))
        self.assertEqual(pc['text'], 'The paper and the Figshare record’s description state 40 participants; the '
                                     'record’s files hold 39 participant archives, and MOABB lists 39.')
        body = json.dumps(self.payload[NEBULA], ensure_ascii=False)
        self.assertEqual(body.count('participant archives'), 1)
        self.assertNotIn('other 39', body)
        intake = json.loads(self.docs['nebulaFileManifest'])
        self.assertEqual(len(ex.participant_archives(intake['files'])), 39)
        # A file list that is not the record's is refused.
        docs = copy.deepcopy(self.docs)
        intake['files'] = intake['files'][:-1]
        docs['nebulaFileManifest'] = json.dumps(intake)
        with self.assertRaisesRegex(ValueError, 'list other files'):
            ex.nebula_participants(docs, self.docs['consent'])
        # The audit takes each count from another record than the export does.
        def count(p):
            p[NEBULA]['design']['participant_counts']['participant_archives_in_record'] = 40
        with self.served(count), self.assertRaisesRegex(au.AuditFailure, 'participant_archives_in_record'):
            au.audit()

    def test_the_one_person_sentence_is_stated_once(self):
        p = self.payload
        self.assertEqual(p['one_person']['cases'], ['eldbeta', DAMM, NEBULA])
        body = json.dumps(p, ensure_ascii=False)
        self.assertEqual(body.count('every score is that person'), 1)
        self.assertEqual(len(re.findall(r'(?i)that person|this person', body)), 1)
        self.assertNotRegex(body, r'(?i)would be (?:that|this|one|the) (?:person|participant)')
        for bad in ('One participant: every score would be that person’s, so the scores are held.',
                    'One participant: every EEG, EMG and EEG plus EMG score would be that person’s.',
                    'With one participant each score is that participant’s own.'):
            q = copy.deepcopy(p)
            q['holds'][1]['reason'] = bad
            with self.assertRaisesRegex(ValueError, 'one-person reasoning'):
                ex.stated_once(q)
        q = copy.deepcopy(p)
        q[DAMM]['status_text'] += ' Every score would be that person’s.'
        with self.assertRaisesRegex(ValueError, 'one-person reasoning'):
            ex.stated_once(q)

        def repeat(p):
            p['holds'][2]['reason'] = 'One participant: every score would be that person’s.'
        with self.served(repeat), self.assertRaisesRegex(au.AuditFailure, 'one-person sentence'):
            au.audit()

    def test_hold_reasons_are_short_lines_for_the_releases_table(self):
        holds = {h['id']: h['reason'] for h in self.payload['holds']}
        self.assertEqual(holds['damm-one-participant-score'], 'One participant; scores held under the site’s one-person rule.')
        self.assertEqual(holds['nebula-one-participant-scores'],
                         'One participant; EEG, EMG and EEG plus EMG scores held under the site’s one-person rule.')
        for reason in holds.values():
            self.assertLessEqual(len(reason), 160)
            self.assertEqual(reason.count('. '), 0)
        self.assertEqual(set(self.payload[KIM]['hold']), {'id', 'what'}, 'Kim’s reason is its caveat, stated once')

    def test_kim_sealing_states_its_limit_once(self):
        hc = {h['id']: h for h in self.payload[KIM]['how_checked']}
        self.assertEqual(hc['sealed-before-scoring']['text'],
                         'All 9,600 outputs were sealed before a separate process scored them; this is process '
                         'separation, not blinded labels, because the stored class order is known.')
        body = json.dumps(self.payload, ensure_ascii=False)
        self.assertEqual(body.count('process separation'), 1)
        self.assertEqual(body.count('blinded'), 1)
        self.assertNotIn('read the labels', body)
        # The owner's wording passes the hedge rule; any other "X, not Y" still does not.
        private = ex.private_names(self.docs)
        base = {'schema_version': 'x', 'release_id': 'x'}
        ex.prose_check({**base, 'scope': hc['sealed-before-scoring']['text']}, private)
        with self.assertRaisesRegex(ValueError, 'hedge'):
            ex.prose_check({**base, 'scope': 'Sealed before scoring, not blinded.'}, private)
        q = copy.deepcopy(self.payload)
        q[KIM]['caveats'].append({'id': 'sealing', 'text': hc['sealed-before-scoring']['text']})
        with self.assertRaisesRegex(ValueError, 'sealing sentence is not stated once'):
            ex.stated_once(q)

    def test_each_statement_is_in_one_field(self):
        k, n, m = self.payload[KIM], self.payload[NEBULA], self.payload[MIND]
        self.assertNotIn('finite-value', k['intake']['text'])
        self.assertIn('finite-value', {h['id']: h for h in k['how_checked']}['all-files-checked']['text'])
        self.assertEqual([t for t, s in ex.strings(n, '$') if 'FCz' in s], ['$.eeg.reference'])
        self.assertEqual([t for t, s in ex.strings(m, '$') if 'never pooled' in s], ['$.secondary.text'])
        cov = {c['id']: c for c in m['coverage']}
        self.assertNotIn('pooled', cov['secondary_panel']['text'])
        ex.stated_once(self.payload)
        for case, edit in ((NEBULA, lambda p: p[NEBULA]['holds'].append('The reference is FCz as the paper states.')),
                           (MIND, lambda p: p[MIND]['coverage'][4].update(text='Reported apart, never pooled.')),
                           (KIM, lambda p: p[KIM]['intake'].update(text='Finite-value checks passed first.'))):
            q = copy.deepcopy(self.payload)
            edit(q)
            with self.assertRaisesRegex(ValueError, 'is stated in'):
                ex.stated_once(q)

    # ------------------------------------------------------------------ consent, ethics, rights
    def test_consent_and_ethics_are_the_a2_record(self):
        a2 = self.docs['consent']['sources']
        for case in (KIM, DAMM, NEBULA):
            ce, src = self.payload[case]['consent_and_ethics'], a2[case]
            self.assertEqual(ce['ethics_approval']['quote'], src['ethics_quote'])
            self.assertEqual(ce['informed_consent']['quote'], None if src['consent_quote'] == 'gap' else src['consent_quote'])
            self.assertEqual(ce['capture_sha256'], src['capture_sha256'])
            self.assertEqual(ce['read_at'], src['captured_at'])

    def test_attribution_and_licences(self):
        for case, doi in ((KIM, ex.KIM_DOI), (NEBULA, ex.NEBULA_DOI), (MIND, ex.MIND_DOI),
                          (DAMM, '10.18112/openneuro.ds008446.v1.0.1')):
            r = self.payload[case]['rights']
            self.assertTrue(r['attribution'].endswith('Derived analysis by BCI Report; not endorsed by the authors.'))
            self.assertIn(doi, r['attribution'])
        self.assertIn('Heegyu Kim, Kyungho Won, Minkyu Ahn and Sung Chan Jun', self.payload[KIM]['rights']['attribution'])
        self.assertIn('Laura Marie Damm, Dai Jiang and Andreas Demosthenous', self.payload[DAMM]['rights']['attribution'])

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['sources']['kimAggregate']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_figures_other_than_the_reviewed_ones_are_refused(self):
        m = copy.deepcopy(MANIFEST)
        a = self.get(m['sources']['kimAggregate'])
        a['mean_accuracy'] = 0.55
        self.put(m['sources']['kimAggregate'], a)
        with self.assertRaisesRegex(ValueError, 'release approval binds other files'):
            build(m)
        docs = copy.deepcopy(self.docs)
        docs['kimAggregate']['mean_accuracy'] += 1e-6
        docs['kimAggregate']['mean_difference'] += 1e-6
        with self.assertRaisesRegex(ValueError, 'Kim review'):
            ex.kim_result(docs)
        docs = copy.deepcopy(self.docs)
        docs['mindAggregate']['metrics']['primary']['4_5']['mean_paired_ID_differences']['order'] += 1e-6
        with self.assertRaisesRegex(ValueError, 'range does not hold it|arithmetic review differs'):
            ex.mind_panels(docs)

    def test_a_changed_owner_decision_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        od = json.loads((ex.PROJECT / m['approval']['ownerDecisions']['path']).read_bytes())
        od['decisions']['D16']['answer'] = 'Reverse the rule for Damm and NeBULA'
        path = Path(self.tmp.name) / 'owner-decisions.json'
        path.write_text(json.dumps(od))
        m['approval']['ownerDecisions']['path'] = str(path)
        with self.assertRaisesRegex(ValueError, 'owner decision D16 changed'):
            build(m)

    def test_a_capture_other_than_the_a2_one_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        a2 = self.get(m['consent']['statements'])
        a2['sources'][NEBULA]['capture_sha256'] = '0' * 64
        self.put(m['consent']['statements'], a2)
        with self.assertRaisesRegex(ValueError, 'not the bytes the consent record names'):
            build(m)

    def test_a_changed_released_data_quality_file_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['published']['dataQuality']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'data-quality-update.json changed'):
            build(m)

    def test_a_held_score_is_refused(self):
        p = copy.deepcopy(self.payload)
        p[DAMM]['design']['primary_accuracy'] = 28
        with self.assertRaisesRegex(ValueError, 'held-score field'):
            ex.scrub_check(p)
        p = copy.deepcopy(self.payload)
        p[NEBULA]['status_text'] += ' The order diagnostic reached 64.07%.'
        with self.assertRaisesRegex(ValueError, 'score-like figure|held score'):
            ex.held_cases_have_no_score(p, self.docs)
        p = copy.deepcopy(self.payload)
        p[DAMM]['design']['share'] = self.docs['dammAudit']['scores']['1->2:primary_all62']['accuracy']
        with self.assertRaisesRegex(ValueError, 'a fraction in a one-person case'):
            ex.held_cases_have_no_score(p, self.docs)

    def test_per_record_and_internal_fields_are_refused(self):
        for key in ('per_record_balanced_accuracy', 'participant_ids', 'confusion', 'macro_F1', 'cpu_seconds',
                    'peak_rss_bytes', 'predictions', 'fit_calls', 'pooled_metrics', 'ordinal_census', 'private_root'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({MIND: {key: 1}})

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 4)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the MIND V4 baseline'}, 'version label'), ({'scope': 'the v1 pilot'}, 'version label'),
                         ({'scope': 'run in October'}, 'month'), ({'scope': 'Added with the census.'}, 'update marker'),
                         ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'CSP is significantly above the controls.'}, 'claim'),
                         ({'scope': 'The windows hold pure motor imagery.'}, 'claim'),
                         ({'scope': 'Units were verified.'}, 'claim'),
                         ({'scope': 'A record-ID range, not a confidence interval.'}, 'hedge'),
                         ({'scope': 'Only40participants and one recorded day'}, 'lost its spaces'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'the task-free run'}, 'participant identifier'),
                         ({'scope': 'BI2013a is planned.'}, 'register-only'),
                         ({'scope': 'the thread bet of 55%'}, 'commenter'),
                         ({'scope': 'a /' + 'mnt/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'Kim2025BetaRange; 40 targets from 14.0 to 21.8 Hz; no confidence interval.'},
                       private)

    def test_withheld_values_are_absent(self):
        fl, it = ex.withheld_values(self.docs)
        self.assertGreaterEqual(len(fl), 40)
        self.assertGreaterEqual(len(it), 8)
        self.assertFalse(fl & set(ex.floats(self.payload)))
        self.assertFalse(it & set(ex.ints(self.payload)))
        body = ex.OUTPUTS[0].read_text()
        # Known withheld renderings (accounting seconds, a count pair, a pooled score), named by the first 16 hex digits
        # of the SHA-256 of the text so that this public file does not print them; every number-like token and
        # "N and M" pair in the served file is hashed the same way.
        tokens = set(re.findall(r'\d[\d,]*(?:\.\d+)?', body)) | set(re.findall(r'\d+ and \d+', body))
        shown = {hashlib.sha256(t.encode()).hexdigest()[:16] for t in tokens}
        for anchor in ('9309529d80c1429f', '4868c1dbe8022d1d', '25b2fc9e190b5baa', 'f9b92c308e6a99f2', 'e71419a267c9ce2a'):
            self.assertNotIn(anchor, shown)
        self.assertIsNone(re.search(r'\b(?:704|176|352)\b', body))     # the model-fit counts, as figures

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
        def kim(p):
            p[KIM]['result']['accuracy_interval_95'][0] += 1e-12
        with self.served(kim), self.assertRaisesRegex(au.AuditFailure, 'accuracy_interval_95/0'):
            au.audit()

        def mind(p):
            p[MIND]['contrasts'][1]['resampling_range'][1] = 0.11
        with self.served(mind), self.assertRaisesRegex(au.AuditFailure, 'contrasts/1/resampling_range/1'):
            au.audit()

        def nebula(p):
            p[NEBULA]['file_facts']['boundary_ties'] = 24
        with self.served(nebula), self.assertRaisesRegex(au.AuditFailure, 'file_facts/boundary_ties'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p[MIND]['secondary']['pairs'][0]['median'] = 0.5
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p[DAMM]['files']['state_blocks_per_run']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_and_a_type_change(self):
        def zero(p):
            p[MIND]['secondary']['interval'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def typed(p):
            p[KIM]['cohort']['trials'] = 9600.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'cohort/trials'):
            au.audit()

    def test_the_audit_catches_a_changed_consent_string_or_attribution(self):
        def consent(p):
            p[NEBULA]['consent_and_ethics']['informed_consent']['quote'] = 'Consent was oral.'
        with self.served(consent), self.assertRaisesRegex(au.AuditFailure, 'A2 record'):
            au.audit()

        def attribution(p):
            p[KIM]['rights']['attribution'] = p[KIM]['rights']['attribution'].rsplit(' Derived', 1)[0]
        with self.served(attribution), self.assertRaisesRegex(au.AuditFailure, 'attribution'):
            au.audit()

    def test_the_audit_catches_held_scores_and_the_secondary_census(self):
        def held(p):
            p[NEBULA]['status_text'] += ' EMG reached 57.53.'
        with self.served(held), self.assertRaisesRegex(au.AuditFailure, 'score-like figure|held score'):
            au.audit()

        def fraction(p):
            p[DAMM]['flags']['share'] = 0.28
        with self.served(fraction), self.assertRaisesRegex(au.AuditFailure, 'no audit rule|fraction'):
            au.audit()

        def decimal(p):
            p[DAMM]['status_text'] += ' The primary run reached 0.28.'
        with self.served(decimal), self.assertRaisesRegex(au.AuditFailure, 'score-like figure'):
            au.audit()

        def census(p):
            p[MIND]['secondary']['schedule'] = 'one record ID repeats one schedule'
        with self.served(census), self.assertRaisesRegex(au.AuditFailure, 'secondary panel carries other fields'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
