"""The beyond-scalp release: what must stay out, and what must follow from the audited sources and their rights records."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_beyond_scalp_export as au
import export_beyond_scalp_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
BAK, NLB, OPT, H2, FUS = ex.BAK, ex.NLB, ex.OPT, ex.H2, ex.FUS


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


def dataset(manifest, did):
    return next(d for d in manifest['datasets'] if d['id'] == did)


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class BeyondScalpBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, record, key, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        record[key] = {**record[key], 'path': str(path), 'sha256': digest(data)}
        return digest(data)

    # ------------------------------------------------------------------ forgeries, hash chains re-bound
    def forged_bak(self, audit=None, stage=None):
        """The Bak result audit edited (the analysis-stage record too, if `stage`), every hash that names it re-bound."""
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, BAK)
        aud = load(record['resultAudit'])
        if audit:
            audit(aud)
        self.write(record, 'resultAudit', 'bak-audit.json', json.dumps(aud).encode())
        if stage:
            st = load(manifest['batch']['analysisStage'])
            stage(st)
            self.write(manifest['batch'], 'analysisStage', 'stage.json', json.dumps(st).encode())
        return manifest

    def forged_nlb(self, audit=None, stage=None):
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, NLB)
        aud = load(record['resultAudit'])
        if audit:
            audit(aud)
        self.write(record, 'resultAudit', 'nlb-audit.json', json.dumps(aud).encode())
        if stage:
            st = load(manifest['batch']['analysisStage'])
            stage(st)
            self.write(manifest['batch'], 'analysisStage', 'stage.json', json.dumps(st).encode())
        return manifest

    def forged_optical(self, audit=None):
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, OPT)
        aud = load(record['resultAudit'])
        if audit:
            audit(aud)
        self.write(record, 'resultAudit', 'opt-audit.json', json.dumps(aud).encode())
        return manifest

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

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helpers_themselves_build(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged_bak())
        build(self.forged_bak(stage=lambda s: None))
        build(self.forged_nlb())
        build(self.forged_optical())

    def test_the_shape(self):
        p = build(MANIFEST)
        self.assertEqual(p['schema_version'], 'bci-report-beyond-scalp-update-v1')
        self.assertEqual(p['release_id'], 'beyond-scalp-update-20261012')
        self.assertEqual(p['question'], 'What can be measured and decoded beyond scalp EEG?')
        self.assertEqual(list(p['results']), [BAK, NLB, OPT])
        self.assertEqual([e['id'] for e in p['status_only']], [H2, FUS])
        self.assertEqual(list(p['datasets']), ['bak-fnirs', 'nlb-mc-rtt', 'ds007420', 'falcon-h2', 'rabut-fus'])
        self.assertEqual([h['id'] for h in p['holds']], ['ds007420-classifier'])
        self.assertEqual(p['provenance']['source_audit_sha256'],
                         {s['id']: s['resultAudit']['sha256'] for s in MANIFEST['sources'] if s['id'] in (BAK, NLB, OPT)})
        for r in p['results'].values():
            self.assertTrue(r['species'] and r['modality'], r['id'])
        for e in p['status_only']:
            self.assertTrue(e['species'] and e['modality'] and e['scores_published'] is False, e['id'])
        self.assertEqual({d: (x['species'], x['modality']) for d, x in p['datasets'].items()},
                         {'bak-fnirs': ('human', 'fNIRS'), 'nlb-mc-rtt': ('macaque (Macaca mulatta)', 'intracortical spiking'),
                          'ds007420': ('human', 'fNIRS'), 'falcon-h2': ('human', 'intracortical spiking'),
                          'rabut-fus': ('human', 'functional ultrasound imaging')})

    # ------------------------------------------------------------------ the figures the page prints
    def test_the_bak_handoff_figures(self):
        r = build(MANIFEST)['results'][BAK]
        lda, prior = r['arms']['shrinkage_lda'], r['arms']['source_prior']
        pct = lambda x, n: round(100 * x, n)
        self.assertEqual(pct(lda['balanced_accuracy']['mean'], 4), 66.8444)
        self.assertEqual([pct(v, 4) for v in lda['balanced_accuracy']['interval_95']], [60.6211, 72.9344])
        self.assertEqual([pct(v, 2) for v in lda['class_recall'].values()], [69.20, 63.60, 67.73])
        self.assertEqual(list(lda['class_recall']), ['right_hand', 'left_hand', 'foot'])
        self.assertEqual(pct(prior['balanced_accuracy']['mean'], 4), 33.3333)
        self.assertNotIn('interval_95', prior['balanced_accuracy'])
        self.assertEqual(prior['class_recall'], {'right_hand': 1.0, 'left_hand': 0.0, 'foot': 0.0})
        self.assertTrue(lda['balanced_accuracy']['interval_excludes_chance'])
        self.assertEqual(r['cohort'], {'people': 30, 'trials': 2250, 'trials_each_person': 75, 'trials_each_class_each_person': 25})
        self.assertEqual([r['design'][k] for k in ('folds', 'training_people', 'training_trials', 'test_trials')], [30, 29, 2175, 75])
        self.assertEqual([r['signal'][k] for k in ('channels', 'features', 'observation_window_s')], [40, 120, 15])
        self.assertEqual(r['signal']['feature_windows_s'], [[0, 5], [5, 10], [10, 15]])
        self.assertEqual(r['primary_metric']['chance_level'], 1 / 3)
        self.assertEqual([r['uncertainty']['draws'], r['uncertainty']['seed']], [2000, 20261011])

    def test_the_nlb_handoff_figures(self):
        r = build(MANIFEST)['results'][NLB]
        f6 = lambda x: round(x, 6)
        want = {'r2_uniform_average': (0.240355, -0.00175), 'r2_x': (0.202474, -0.000104), 'r2_y': (0.278237, -0.003396),
                'rmse_m_per_s': (0.056065, 0.064268), 'mae_m_per_s': (0.038441, 0.032758)}
        for m, (ridge, base) in want.items():
            self.assertEqual((f6(r['arms']['ridge'][m]), f6(r['arms']['training_mean'][m])), (ridge, base), m)
        self.assertEqual(r['comparison']['ridge_better'], {'r2_uniform_average': True, 'r2_x': True, 'r2_y': True,
                                                           'rmse_m_per_s': True, 'mae_m_per_s': False})
        self.assertEqual([r['signal'][k] for k in ('training_rows', 'validation_rows', 'rows_excluded', 'features',
                                                   'neural_support_ms', 'target_lag_ms', 'retained_bins_each_trial')],
                         [12960, 4320, 0, 588, 160, 140, 16])
        self.assertEqual([r['cohort'][k] for k in ('animals', 'sessions', 'training_trials', 'validation_trials',
                                                   'input_neurons')], [1, 1, 810, 270, 98])
        self.assertEqual(r['coverage'], {'validation_rows_scored': 4320, 'scored_share': 1.0})
        self.assertEqual(r['uncertainty']['kind'], 'none reported')
        self.assertIn('not an official Neural Latents Benchmark score', r['label'])
        self.assertTrue(any('every figure is that animal' in x for x in r['limitations']))

    def test_the_optical_coverage_figures(self):
        r = build(MANIFEST)['results'][OPT]
        self.assertEqual(r['cohort'], {'people': 12, 'recordings': 60, 'recordings_excluded': 0, 'channels_each_recording': 200,
                                       'recording_channels': 12000, 'optical_time_points': 242513})
        self.assertEqual(r['counts'], {'optical_values': 48502600, 'finite': 48502600, 'positive': 48502600, 'zero': 0,
                                       'negative': 0, 'nonfinite': 0, 'constant_channels': 0})
        self.assertEqual(r['shares'], {'finite': 1.0, 'positive': 1.0})
        self.assertEqual(r['gates']['event_duration_s'], {'events_table': 1, 'optical_files': 10, 'cited_paper': 5})
        self.assertEqual(r['gates']['auxiliary_clock_hold_recordings'], 17)
        self.assertEqual(r['gates']['classifier'], 'held')
        self.assertNotIn('balanced_accuracy', json.dumps(r))

    def test_the_status_only_entries_carry_no_score(self):
        p = build(MANIFEST)
        h2, fus = p['status_only']
        self.assertEqual(h2['preparation'], {'participants': 1, 'recording_dates': 26, 'files': 47, 'channels': 192,
                                             'held_in_calibration_trials': 671, 'minival_trials': 42,
                                             'minival_trials_also_in_calibration': 42, 'training_candidate_trials': 629,
                                             'held_out_calibration_trials': 15, 'symbols': 31, 'ctc_classes_with_blank': 32})
        self.assertEqual(fus['preparation'], {'participants': 1, 'runs': 9, 'drawing_runs': 7, 'guitar_runs': 1,
                                              'mixed_speech_reading_runs': 1, 'frames': 2880, 'rest_frames': 1800,
                                              'activity_frames': 1080})
        text = json.dumps(p['status_only'])
        for word in ('accuracy', 'error rate', 'CER', 'WER', 'R²', 'auroc'):
            self.assertNotIn(word, text)
        self.assertEqual(fus['rights']['license'], 'CC BY-NC 4.0')

    # ------------------------------------------------------------------ chains and gates
    def test_a_changed_input_byte_is_refused(self):
        refs = [(source, BAK, 'protocol'), (source, BAK, 'freezeReview'), (source, NLB, 'implementation'),
                (source, NLB, 'auditor'), (source, OPT, 'qualityNote'), (source, H2, 'readiness')]
        for get, sid, key in refs:
            manifest = copy.deepcopy(MANIFEST)
            ref = get(manifest, sid)[key]
            raw = bytearray((ex.PROJECT / ref['path']).read_bytes())
            raw[-2:-1] = b' '
            path = Path(self.tmp.name) / f'{sid}-{key}'
            path.write_bytes(bytes(raw))
            ref['path'] = str(path)
            with self.assertRaisesRegex(ValueError, 'pinned', msg=(sid, key)):
                build(manifest)
        for did, key in (('bak-fnirs', 'licenseRecord'), ('rabut-fus', 'licenseRecord')):
            manifest = copy.deepcopy(MANIFEST)
            ref = dataset(manifest, did)[key]
            raw = (ex.PROJECT / ref['path']).read_bytes() + b' '
            path = Path(self.tmp.name) / f'{did}-{key}'
            path.write_bytes(raw)
            ref['path'] = str(path)
            with self.assertRaisesRegex(ValueError, 'pinned', msg=(did, key)):
                build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        path = Path(self.tmp.name) / 'handoff.md'
        path.write_bytes((ex.PROJECT / manifest['batch']['handoff']['path']).read_bytes().replace(b'66.8444', b'66.8445'))
        manifest['batch']['handoff']['path'] = str(path)
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(manifest)

    def test_a_handoff_the_validation_did_not_name_is_refused(self):
        manifest = copy.deepcopy(MANIFEST)
        text = (ex.PROJECT / manifest['batch']['handoff']['path']).read_bytes() + b'\n'
        self.write(manifest['batch'], 'handoff', 'handoff.md', text)
        with self.assertRaisesRegex(ValueError, 'validation names other handoff bytes'):
            build(manifest)

    def test_a_failed_audit_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            build(self.forged_bak(audit=lambda a: a['checks'].update(whole_person_disjoint_folds=False)))
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            build(self.forged_bak(audit=lambda a: a.update(refit_performed=True)))
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            build(self.forged_nlb(audit=lambda a: a.update(official_nlb_score=True)))
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            build(self.forged_nlb(audit=lambda a: a.update(test_file_opened=True)))
        with self.assertRaisesRegex(ValueError, 'not a coverage release'):
            build(self.forged_optical(audit=lambda a: a.update(decision='eligible_for_decoding')))

    def test_an_audit_of_other_bytes_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'names another protocol, code or freeze'):
            build(self.forged_bak(audit=lambda a: a.update(code_sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'another auditor program'):
            build(self.forged_nlb(audit=lambda a: a.update(auditor_sha256='0' * 64)))

    def test_the_readings_are_held_to_the_figures(self):
        def chance(a):
            a['results']['lda']['descriptive_bootstrap_95_percent'][0] = 0.33
        with self.assertRaisesRegex(ValueError, 'no longer lies above chance'):
            build(self.forged_bak(audit=chance))

        def mae(a):
            a['models']['ridge']['mae_m_per_s'] = 0.03
        with self.assertRaisesRegex(ValueError, 'no longer worse on absolute error'):
            build(self.forged_nlb(audit=mae))

        def rmse(a):
            a['models']['ridge']['rmse_m_per_s'] = 0.07
        with self.assertRaisesRegex(ValueError, 'no longer improves squared error'):
            build(self.forged_nlb(audit=rmse))

        def nonfinite(a):
            a['value_counts']['finite'] -= 1
            a['value_counts']['positive'] -= 1
            a['value_counts']['nonfinite'] += 1
        with self.assertRaisesRegex(ValueError, 'no longer holds'):
            build(self.forged_optical(audit=nonfinite))

    def test_counts_must_add_up(self):
        with self.assertRaisesRegex(ValueError, 'channel or value counts'):
            build(self.forged_optical(audit=lambda a: a.update(optical_values=a['optical_values'] + 200)))
        with self.assertRaisesRegex(ValueError, 'partition'):
            build(self.forged_optical(audit=lambda a: a['value_counts'].update(zero=1)))
        with self.assertRaisesRegex(ValueError, 'did not score or reconstruct every row'):
            build(self.forged_nlb(audit=lambda a: a.update(scored_coverage=0.99)))
        with self.assertRaisesRegex(ValueError, 'recall'):
            build(self.forged_bak(audit=lambda a: a['results']['lda']['class_recall'].__setitem__(0, 0.7)))

    def test_the_printed_figures_must_be_the_handoffs(self):
        def nudge(a):
            a['results']['lda']['participant_macro_balanced_accuracy'] += 1e-6

        def stage(s):
            s['completed']['bak2019']['participant_macro_balanced_accuracy'] += 1e-6
        with self.assertRaisesRegex(ValueError, 'does not state'):
            build(self.forged_bak(audit=nudge, stage=stage))
        with self.assertRaisesRegex(ValueError, 'analysis stage records other figures'):
            build(self.forged_bak(stage=stage))

    # ------------------------------------------------------------------ the switch and the holds
    def test_a_source_can_be_held_without_other_changes(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, BAK)['decision'] = 'hold'
        p = build(manifest)
        self.assertNotIn(BAK, p['results'])
        self.assertEqual([h['id'] for h in p['holds']], ['ds007420-classifier', BAK])
        self.assertEqual(p['datasets']['bak-fnirs']['held'], [BAK])
        self.assertEqual(p['datasets']['bak-fnirs']['results'], [])
        self.assertNotIn(0.6684444444444444, set(ex.numbers(p)))
        self.assertEqual(p['datasets']['bak-fnirs']['rights']['license'], 'CC BY 4.0')
        manifest['standbyHolds'] = []
        with self.assertRaisesRegex(ValueError, 'held without a hold entry'):
            build(manifest)

    def test_only_known_decisions_are_exported(self):
        for sid, decision in ((H2, 'aggregate_preview'), (BAK, 'status_only'), (NLB, 'publish')):
            manifest = copy.deepcopy(MANIFEST)
            source(manifest, sid)['decision'] = decision
            with self.assertRaisesRegex(ValueError, 'no extractor', msg=(sid, decision)):
                build(manifest)

    def test_holds_carry_no_figure(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['holds'][0]['reason'] = 'the durations are 1, 5 and 10 seconds'
        with self.assertRaisesRegex(ValueError, 'carries a figure'):
            build(manifest)

    # ------------------------------------------------------------------ rights
    def test_the_rights_records(self):
        p = build(MANIFEST)['datasets']
        self.assertEqual({d: x['rights']['license'] for d, x in p.items()},
                         {'bak-fnirs': 'CC BY 4.0', 'nlb-mc-rtt': 'CC BY 4.0', 'ds007420': 'CC0-1.0',
                          'falcon-h2': 'CC BY 4.0', 'rabut-fus': 'CC BY-NC 4.0'})
        for d, x in p.items():
            ce = x['consent_and_ethics']
            self.assertTrue(ce['ethics_approval']['stated'], d)
            self.assertIn('not endorsed by the authors', x['rights']['attribution'])
        human = {d for d, x in p.items() if x['consent_and_ethics']['subjects'] == 'human'}
        self.assertEqual(human, {'bak-fnirs', 'ds007420', 'falcon-h2', 'rabut-fus'})
        for d in human:
            self.assertTrue(p[d]['consent_and_ethics']['informed_consent']['stated'], d)
        nlb = p['nlb-mc-rtt']['consent_and_ethics']
        self.assertEqual(nlb['subjects'], 'animal')
        self.assertEqual([nlb['informed_consent']['stated'], nlb['informed_consent']['applicable']], [False, False])
        self.assertIn('Institutional Animal Care and Use Committees', nlb['ethics_approval']['quote'])
        self.assertIn('KUIRB-2019-0254-01', p['bak-fnirs']['consent_and_ethics']['ethics_approval']['quote'])
        self.assertIn('Internet Archive', p['bak-fnirs']['consent_and_ethics']['read_from'])
        self.assertIn('Protocol #4502', p['ds007420']['consent_and_ethics']['ethics_approval']['statement'])
        self.assertIn('Neural Latents Benchmark', p['nlb-mc-rtt']['rights']['attribution'])
        self.assertIn('noncommercial', p['rabut-fus']['rights']['privacyReview'])

    def test_a_statement_needs_its_quote_in_the_record(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'ds007420')['consentEthics']['quotes'][1]['text'] = 'consented to public sharing'
        with self.assertRaisesRegex(ValueError, 'the consent statement has no quote in the record'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'nlb-mc-rtt')['consentEthics']['quotes'][0]['text'] = 'approved by the UCSF IACUC'
        with self.assertRaisesRegex(ValueError, 'animal_care statement has no quote'):
            build(manifest)

    def test_the_licence_must_be_the_repositorys(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'rabut-fus')['license'] = 'CC BY 4.0'
        dataset(manifest, 'rabut-fus')['licenseUrl'] = 'https://creativecommons.org/licenses/by/4.0/'
        with self.assertRaisesRegex(ValueError, 'another licence'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'ds007420')['license'] = 'CC BY 4.0'
        dataset(manifest, 'ds007420')['licenseUrl'] = 'https://creativecommons.org/licenses/by/4.0/'
        with self.assertRaisesRegex(ValueError, 'another licence'):
            build(manifest)

    def test_the_consent_record_must_be_the_paper_named(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'bak-fnirs')['consentEthics']['record'] = dataset(manifest, 'ds007420')['consentEthics']['record']
        with self.assertRaisesRegex(ValueError, 'another document'):
            build(manifest)

    def test_an_animal_source_never_claims_consent(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'nlb-mc-rtt')['consentEthics']['consent'] = 'The animal gave consent.'
        with self.assertRaisesRegex(ValueError, 'not marked not applicable'):
            build(manifest)

    # ------------------------------------------------------------------ what stays out
    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('minimum', 'maximum', 'median', 'p10', 'per_person_scores', 'participant_ids', 'confusion_matrix',
                    'predictions', 'coefficients', 'per_channel_counts', 'per_recording', 'per_trial', 'fold_scores_per_fold',
                    'private_root', 'launcher_wall_seconds', 'runtime', 'free_server_gib', 'acquired_bytes',
                    'storage_path', 'host', 'cues', 'dates', 'timestamps', 'ridge_normal_equation_max_abs_residual'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('file sub-Indy_desc-train.nwb', 'participant T5', 'monkey Indy', 'sub-170', 'x.snirf', 'run.mat',
                     '/home/someone/project/x', '/Users/someone/x', 'on TRX50', 'on Gal4', 'participant J'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_withheld_values_stay_out_by_value(self):
        p = build(MANIFEST)
        published = set(ex.numbers(p))
        bak = load(source(MANIFEST, BAK)['resultAudit'])
        for row in bak['results']['lda']['confusion_matrix']:
            self.assertFalse(set(row) & published, row)
        self.assertNotIn(bak['runtime']['launcher_total_seconds'], published)
        stage = load(MANIFEST['batch']['analysisStage'])
        self.assertNotIn(stage['last_live_check']['free_server_gib'], published)

    def test_no_version_label_or_update_marker_in_the_text(self):
        for text in ('the v2 analysis', 'protocol (v1)', 'updated 12 October 2026', 'Added 2026-10-12: x',
                     'in this update', 'a new page', 'run on 2026-10-11'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        ex.scrub_check({'results': {'x': {'source': 'doi:10.6084/m9.figshare.9783755.v2, version 2'}}})
        text = json.dumps({k: v for k, v in build(MANIFEST).items() if k not in ('schema_version', 'release_id')})
        self.assertFalse(re.search(r'(?<![./\w-])v\d+\b', text))
        self.assertNotIn('Jev', text)

    def test_unsupported_claims_appear_only_negated(self):
        for sentence in ('The decoder supports online control.', 'This is motor imagery.', 'An official NLB score.',
                         'The signal has neural origin.', 'A clinical result.', 'It shows cortical localization.'):
            with self.assertRaises(ValueError, msg=sentence):
                ex.claims_negated({'results': {'x': {'reading': sentence}}})
        ex.claims_negated({'results': {'x': {'reading': 'Not online control; not motor imagery; not an official NLB '
                                                         'score; no neural origin claim.'}}})

    def test_prose_numerals_come_from_the_pinned_sources(self):
        with self.assertRaisesRegex(ValueError, 'in no pinned source'):
            ex.written_from({'reading': 'about 71.3 percent'}, ('66.8444%',), 'x')
        ex.written_from({'reading': '66.8444', 'rights': '7.3'}, ('66.8444%',), 'x')

    def test_no_private_path_or_identifier_reaches_the_files(self):
        text = json.dumps(build(MANIFEST), ensure_ascii=False)
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', 'Gal4', 'TRX50', 'BCI_Arena', '.nwb',
                      '.snirf', '.mat', 'sub-', 'Indy', 'T5'):
            self.assertNotIn(token, text)
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', 'TRX50', 'BCI_Arena'):
                self.assertNotIn(token, body, f'{path.name}: {token}')

    # ------------------------------------------------------------------ the independent audit
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

    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            p['results'][NLB]['arms']['ridge']['mae_m_per_s'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'mae_m_per_s'):
            au.audit()

        def count(p):
            p['status_only'][0]['preparation']['training_candidate_trials'] = 671
        with self.served(count), self.assertRaisesRegex(au.AuditFailure, 'training_candidate_trials'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['results'][BAK]['arms']['shrinkage_lda']['balanced_accuracy']['median'] = 0.67
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['results'][OPT]['counts']['constant_channels']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_wrong_flag_or_licence(self):
        def flag(p):
            p['results'][NLB]['comparison']['ridge_better']['mae_m_per_s'] = True
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'flag'):
            au.audit()

        def licence(p):
            p['datasets']['rabut-fus']['rights']['license'] = 'CC BY 4.0'
        with self.served(licence), self.assertRaisesRegex(au.AuditFailure, 'licence'):
            au.audit()

    def test_the_audit_catches_a_withheld_value_or_a_private_path(self):
        bak = load(source(MANIFEST, BAK)['resultAudit'])

        def runtime(p):
            p['results'][BAK]['signal']['runtime_s'] = bak['runtime']['launcher_total_seconds']
        with self.served(runtime), self.assertRaises(au.AuditFailure):
            au.audit()

        def path(p):
            p['results'][NLB]['design']['split'] += ' (read under /home/someone)'
        with self.served(path), self.assertRaisesRegex(au.AuditFailure, 'private path'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
