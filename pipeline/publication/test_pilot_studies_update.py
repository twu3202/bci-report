"""The pilot-studies release: what must stay out, and what must follow from the approved exports."""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_pilot_studies_export as au
import export_pilot_studies_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
O64, O58, OFM, BINGO, HAND, REFED = ex.SOURCE_ORDER


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


def dataset(manifest, did):
    return next(d for d in manifest['datasets'] if d['id'] == did)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def r2(x):
    return round(100 * x, 2)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class PilotStudiesBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    # ------------------------------------------------------------------ forgeries, hash chains re-bound
    def get(self, ref):
        return json.loads((ex.PROJECT / ref['path']).read_bytes())

    def put(self, ref, obj=None, data=None):
        """Write an edited copy at the same batch-relative path under the temporary root and re-pin it."""
        data = data if data is not None else json.dumps(obj).encode()
        rel = ref['path'].split('research/', 1)[1]
        path = Path(self.tmp.name) / 'research' / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        ref['path'], ref['sha256'] = str(path), digest(data)
        return ref['sha256']

    def switched(self, **publication):
        manifest = copy.deepcopy(MANIFEST)
        for sid, state in publication.items():
            source(manifest, sid)['publication'] = state
        return manifest

    def served(self, payload=None, manifest=None, edit=None):
        """Patch the auditor onto temporary served copies (and manifest)."""
        payload = payload if payload is not None else json.loads(ex.OUTPUTS[0].read_bytes())
        if edit:
            edit(payload)
        data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
        paths = []
        for i in range(2):
            p = Path(self.tmp.name) / f'served-{i}.json'
            p.write_bytes(data)
            paths.append(p)
        patches = [mock.patch.object(au, 'SERVED', tuple(paths))]
        if manifest is not None:
            m = Path(self.tmp.name) / 'manifest.json'
            m.write_bytes(json.dumps(manifest).encode())
            patches.append(mock.patch.object(au, 'MANIFEST', m))
        stack = __import__('contextlib').ExitStack()
        for p in patches:
            stack.enter_context(p)
        return stack

    def built_manifest_bytes(self, manifest):
        return json.dumps(manifest).encode()

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

    def test_the_shape(self):
        p = build(MANIFEST)
        self.assertEqual(p['schema_version'], 'bci-report-pilot-studies-update-v1')
        self.assertEqual(p['release_id'], 'pilot-studies-update-20261012')
        self.assertEqual(list(p['results']), [O64, O58, OFM, BINGO, HAND, REFED])
        self.assertEqual(list(p['datasets']), ['orthosis-error-detection', 'bingo-imagined-speech',
                                               'eeg-fnirs-handwriting', 'refed'])
        self.assertEqual(p['holds'], [])
        self.assertEqual([s['id'] for s in p['status_only']], ['orthosis-emg-tinymyo-fusion', 'handwriting-fnirs-fusion',
                                                               'refed-physiological-fusion', 'meditation-eeg-phase'])
        self.assertEqual(p['provenance']['source_export_sha256'],
                         {s['id']: s['export']['sha256'] for s in MANIFEST['sources'] if s['publication'] == 'released'})
        self.assertEqual(p['provenance']['held_sources'], [])
        self.assertTrue(all(r['leaderboard'] is False for r in p['results'].values()))
        self.assertIn('heartbeat RR intervals, not respiratory rate', p['status_only'][-1]['reason'])

    def test_every_approved_export_is_the_one_its_approval_names(self):
        for s in MANIFEST['sources']:
            raw = (ex.PROJECT / s['export']['path']).read_bytes()
            self.assertEqual(digest(raw), s['export']['sha256'], s['id'])
            self.assertEqual(au.binding(s), s['export']['sha256'], s['id'])
        self.assertEqual(source(MANIFEST, OFM)['export']['sha256'],
                         '201ac453a0f3985b727aca340dc0f6f69261c0e8425db81b90c39b4b99101591')
        self.assertEqual(source(MANIFEST, O58)['export']['sha256'],
                         '9ee443d5424ea7a40b86d3dfb3bb5d15a5e53e5ad7ad9e80c618abc0c213b4d7')
        self.assertEqual(source(MANIFEST, REFED)['export']['sha256'],
                         'f9ecab0bf86303f1ed5e437e15519540898057d5b5e75296081fc2cba084b613')

    def test_no_candidate_file_and_no_eegpt_folder_is_an_input(self):
        for ref in ex.input_refs(MANIFEST):
            self.assertFalse(ref['path'].endswith('-candidate.json'), ref['path'])
            self.assertNotIn('eegpt/', ref['path'].lower(), ref['path'])
            self.assertFalse(ref['path'].startswith('/'), 'repo-relative paths only')

    # ------------------------------------------------------------------ the figures the pages print
    def test_the_orthosis_figures(self):
        r = build(MANIFEST)['results']
        ba = lambda b: (r2(b['mean']), [r2(v) for v in b['interval_95']])
        self.assertEqual(ba(r[O64]['arms']['eeg']['balanced_accuracy']), (72.97, [67.98, 77.68]))
        self.assertEqual(ba(r[O58]['arms']['classical58']['balanced_accuracy']), (70.97, [64.81, 76.9]))
        self.assertEqual(ba(r[OFM]['arms']['eegpt2048']['balanced_accuracy']), (70.34, [66.16, 73.87]))
        self.assertEqual(r[OFM]['arms']['classical58'], r[O58]['arms']['classical58'])
        d = r[OFM]['paired']['balanced_accuracy_difference']
        self.assertEqual((round(100 * d['mean'], 4), [round(100 * v, 4) for v in d['interval_95']]),
                         (-0.6342, [-3.9572, 3.2334]))
        self.assertFalse(r[OFM]['paired']['interval_excludes_zero'])
        pe = r[OFM]['permutation_control']
        self.assertEqual((r2(pe['eegpt2048']['balanced_accuracy_mean']), [r2(v) for v in pe['eegpt2048']['observed_range']]),
                         (49.76, [47.58, 52.15]))
        self.assertEqual(pe['classical58'], r[O58]['permutation_control']['balanced_accuracy'])
        p64 = r[O64]['permutation_control']['balanced_accuracy']
        self.assertEqual((r2(p64['balanced_accuracy_mean']), [r2(v) for v in p64['observed_range']]), (50.09, [48.0, 52.6]))
        self.assertEqual(r2(r[O64]['eeg_minus_confound']['balanced_accuracy_difference']['mean']), 21.62)
        self.assertIsNone(r[O64]['eeg_minus_confound']['balanced_accuracy_difference']['interval_95'])
        for rid in (O64, O58, OFM):
            c = r[rid]['cohort']
            self.assertEqual([c['people'], c['runs'], c['events'], c['standard_events'], c['error_events']],
                             [8, 83, 2407, 1933, 474], rid)
            self.assertEqual(r[rid]['chance_level'], 0.5)
        self.assertEqual(r[O64]['response_clean_subset'] | {'status': '', 'note': ''},
                         {'status': '', 'note': '', 'events': 451, 'error_events': 446, 'standard_events': 5,
                          'people_with_both_classes': 3})
        self.assertEqual(r[O64]['cohort']['exclusions'] | {'note': ''},
                         {'note': '', 'baseline_runs': 8, 'targets_without_following_movement': 82,
                          'windows_crossing_boundary': 1})
        self.assertEqual([r[O64]['signal']['eeg_channels'], r[O58]['signal']['eeg_channels']], [64, 58])

    def test_the_eegpt_model_block(self):
        m = build(MANIFEST)['results'][OFM]['model']
        self.assertEqual(m['code_licence'], 'Apache-2.0')
        self.assertIsNone(m['weights_licence'])
        self.assertFalse(m['weights_distributed'])
        self.assertIn('unresolved', m['weights_licence_status'])
        self.assertEqual(m['checkpoint']['sha256'], '9d63ebc80bba1ad5e3277df4eecfa05d2745e6243a12ff743c4c0a93930dfac0')
        self.assertEqual(m['encoder_parameters'], 25287168)
        r = build(MANIFEST)['results'][OFM]
        self.assertEqual(r['pretraining_exposure']['status'], 'not established')
        self.assertIn('not zero-shot', r['transfer'])

    def test_the_bingo_figures(self):
        b = build(MANIFEST)['results'][BINGO]
        want = [('Greek → Greek', 6.35, [5.84, 6.9], 19.06, 7.1, 7.1, 6.56, [5.53, 7.49]),
                ('Greek → English', 6.59, [5.49, 7.65], 20.98, 6.24, 6.39, 6.51, [5.41, 7.33]),
                ('English → English', 6.71, [5.84, 7.57], 19.92, 7.41, 6.55, 6.81, [6.12, 7.84]),
                ('English → Greek', 7.06, [6.24, 7.92], 19.61, 6.55, 7.22, 6.75, [5.45, 7.73])]
        for d, w in zip(b['directions'], want):
            c = d['controls']
            sh = c['label_shuffle']['balanced_accuracy']
            self.assertEqual((d['label'], r2(d['balanced_accuracy']['mean']), [r2(v) for v in d['balanced_accuracy']['interval_95']],
                              r2(d['top3_accuracy']['mean']), r2(c['order_only']['balanced_accuracy']['mean']),
                              r2(c['high_frequency_ratio']['balanced_accuracy']['mean']), r2(sh['balanced_accuracy_mean']),
                              [r2(v) for v in sh['observed_range']]), w)
            self.assertEqual(sh['replicates'], 20)
        ct = b['contrast']['balanced_accuracy_difference']
        self.assertEqual((r2(ct['mean']), [r2(v) for v in ct['interval_95']]), (0.29, [-0.63, 1.27]))
        self.assertFalse(b['contrast']['interval_excludes_zero'])
        self.assertEqual(b['chance'] | {'note': ''}, {'balanced_accuracy': 1 / 15, 'top3_accuracy': 0.2, 'note': ''})
        self.assertEqual([b['cohort']['source_fields'], b['cohort']['trials'], b['cohort']['training_rows']], [17, 5100, 2400])
        self.assertEqual(b['protocol']['timeline_seconds'], {'word_shown': -2.5, 'word_removed_countdown': -1.0,
                                                              'fixation_inner_speech_onset': 0.0, 'end': 1.5})
        self.assertEqual([b['protocol']['nouns'], b['protocol']['repetitions_per_noun']], [15, 10])
        self.assertEqual(b['project_reported']['mean_accuracy_percent'], 3.85)
        self.assertIn('not run here', b['project_reported']['kind'])
        self.assertFalse(b['delivered_signal']['verified_against_file'])
        for word in ('Artifact Subspace Reconstruction', 'FORCe', '1 to 145 Hz', '50 Hz'):
            self.assertIn(word, b['delivered_signal']['statement'])
        self.assertIn('/download/397', b['delivered_signal']['source'])

    def test_the_refed_figures(self):
        r = build(MANIFEST)['results'][REFED]
        shared, joint = r['conditions']
        got = {a: (round(shared['arms'][a]['equal_axis_mae'], 6), round(joint['arms'][a]['equal_axis_mae'], 6))
               for a in ex.REFED_ARMS}
        self.assertEqual(got, {'eeg_ridge': (107.18212, 91.984465), 'source_global_mean': (40.287029, 41.032302),
                               'source_video_lookup': (27.32457, 41.032302),
                               'duration_video_id_ridge': (37.909675, 47.097703)})
        self.assertEqual([r['cohort']['nominal_folders'], r['cohort']['videos'], r['cohort']['clips']], [2, 15, 30])
        self.assertEqual([shared['folds'], joint['folds'], shared['lookup_matched_videos'], joint['lookup_matched_videos']],
                         [2, 10, 30, 0])
        self.assertIn('1 to 255', r['target']['scale'])

    def test_the_handwriting_figures(self):
        p = build(MANIFEST)
        h = p['results'][HAND]
        ba = lambda b: (r2(b['mean']), [r2(v) for v in b['interval_95']])
        self.assertEqual(ba(h['arms']['relative_eeg']['balanced_accuracy']), (26.81, [26.3, 27.2]))
        self.assertEqual(ba(h['arms']['time_only']['balanced_accuracy']), (25.44, [24.03, 26.79]))
        self.assertEqual(ba(h['arms']['mask_plus_time']['balanced_accuracy']), (25.01, [23.9, 26.12]))
        self.assertEqual(ba(h['arms']['majority']['balanced_accuracy']), (25.0, [25.0, 25.0]))
        diff = {k: (round(100 * c['balanced_accuracy_difference']['mean'], 2), [round(100 * v, 2) for v in c['balanced_accuracy_difference']['interval_95']])
                for k, c in h['contrasts'].items()}
        self.assertEqual(diff, {'relative_eeg_minus_mask_only': (1.82, [1.3, 2.21]), 'relative_eeg_minus_time_only': (1.37, [-0.12, 3.07]),
                                'relative_eeg_minus_mask_plus_time': (1.8, [0.43, 3.05])})
        self.assertEqual({a: (r2(x['balanced_accuracy_mean']), [r2(v) for v in x['observed_range']])
                          for a, x in h['label_shuffle']['representations'].items()},
                         {'relative_eeg': (25.2, [23.85, 26.69]), 'mask_only': (24.95, [24.88, 25.0]),
                          'time_only': (24.7, [24.3, 25.16]), 'mask_plus_time': (24.71, [24.11, 25.78])})
        self.assertEqual([(x['channels'], x['trials']) for x in h['availability']['trials_by_available_channels']],
                         [(27, 1429), (28, 65), (29, 16), (30, 36), (37, 36), (38, 36)])
        self.assertIn('must not be summed', h['availability']['flags_note'])
        self.assertIn('not certified clean physiological EEG', h['availability']['available_means'])
        flags = {k: c['interval_excludes_zero'] for k, c in h['contrasts'].items()}
        self.assertEqual(flags, {'relative_eeg_minus_mask_only': True, 'relative_eeg_minus_time_only': False,
                                 'relative_eeg_minus_mask_plus_time': True})
        sh = h['label_shuffle']['representations']['relative_eeg']
        self.assertEqual((r2(sh['balanced_accuracy_mean']), [r2(v) for v in sh['observed_range']]), (25.2, [23.85, 26.69]))
        av = h['availability']
        self.assertEqual([av['available_channels_per_trial']['fewest'], av['available_channels_per_trial']['most'],
                          av['channel_trials'], av['flags']['constant'], av['flags']['lower_rail']],
                         [27, 38, 95462, 50811, 50815])
        self.assertEqual([h['cohort'][k] for k in ('people', 'sessions', 'events', 'trials', 'quarantined_events')],
                         [5, 45, 1620, 1618, 2])
        self.assertIn('not a second cohort', h['earlier_analysis']['relation'])
        self.assertIn('cannot be attributed to masking', h['earlier_analysis']['not_attributable'])
        # The handoff's forbidden readings, competition standing among them, as the page states them.
        self.assertTrue(any('competition-standing' in t for t in h['limitations']))
        self.assertTrue(any('competition-standing' in t for t in h['claims_not_supported']))
        self.assertIn('owner’s decision', build(MANIFEST)['datasets']['eeg-fnirs-handwriting']['rights']['privacyReview'])
        self.assertEqual(au.audit()['included'], [O64, O58, OFM, BINGO, HAND, REFED])

    def test_the_mask_only_interval_is_withheld(self):
        # Five people: the mask-only control's bounds would show individual people's scores, so its interval is null and
        # its bounds appear nowhere in the file; the mean is published.
        e = json.loads((ex.PROJECT / source(MANIFEST, HAND)['export']['path']).read_bytes())
        bounds = e['results']['primary_and_contrasts']['arms']['mask_only']['percentile_2_5_97_5']
        p = build(MANIFEST)
        m = p['results'][HAND]['arms']['mask_only']
        self.assertIsNone(m['balanced_accuracy']['interval_95'])
        self.assertEqual(r2(m['balanced_accuracy']['mean']), 24.99)
        self.assertIn('individual people’s scores', m['interval_note'])
        published = set(ex.numbers(p))
        self.assertFalse({b for b in bounds if b != 0.25} & published)
        lo = bounds[0]

        def leak(q):
            q['results'][HAND]['arms']['mask_only']['balanced_accuracy']['interval_95'] = [lo, 0.25]
        with self.served(edit=leak), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def elsewhere(q):
            q['results'][REFED]['independent_audit']['largest_metric_difference'] = lo
        with self.served(edit=elsewhere), self.assertRaises(au.AuditFailure):
            au.audit()

    # ------------------------------------------------------------------ the publication switches
    def test_handwriting_held_by_the_switch(self):
        manifest = self.switched(**{HAND: 'status_only'})
        p = build(manifest)
        self.assertNotIn(HAND, p['results'])
        self.assertEqual([h['id'] for h in p['holds']], ['handwriting-mask-aware-rights'])
        self.assertEqual(p['datasets']['eeg-fnirs-handwriting']['results'], [])
        self.assertIn('until that basis is established', p['datasets']['eeg-fnirs-handwriting']['rights']['privacyReview'])
        released = build(MANIFEST)['results'][HAND]
        self.assertFalse({v for v in ex.numbers(released) if v not in (0.0, 0.25, 0.5, 1.0)} & set(ex.numbers(p)))
        with self.served(payload=p, manifest=manifest):
            self.assertEqual(au.audit()['held_sources'], [HAND])

    def test_bingo_held_by_the_switch(self):
        manifest = self.switched(**{BINGO: 'status_only'})
        p = build(manifest)
        self.assertNotIn(BINGO, p['results'])
        self.assertEqual([h['id'] for h in p['holds']], ['bingo-cross-language-rights'])
        self.assertEqual(p['datasets']['bingo-imagined-speech']['results'], [])
        bingo = build(MANIFEST)['results'][BINGO]
        published = set(ex.numbers(p))
        self.assertFalse({v for v in ex.numbers(bingo) if v not in (0.0, 0.25, 0.5, 1.0)} & published)
        with self.served(payload=p, manifest=manifest):
            self.assertEqual(au.audit()['held_sources'], [BINGO])

    def test_one_pilot_is_released_or_held_whole(self):
        manifest = self.switched(**{OFM: 'status_only'})
        with self.assertRaisesRegex(ValueError, 'released or held together'):
            build(manifest)
        manifest = self.switched(**{REFED: 'maybe'})
        with self.assertRaisesRegex(ValueError, 'released or status_only'):
            build(manifest)

    # ------------------------------------------------------------------ chains and gates
    def test_a_changed_input_byte_is_refused(self):
        for sid, key in ((O64, 'export'), (O58, 'approval'), (OFM, 'finalization'), (OFM, 'codeLicence'),
                         (BINGO, 'handoff'), (HAND, 'earlierExport'), (REFED, 'resultAudit')):
            manifest = copy.deepcopy(MANIFEST)
            ref = source(manifest, sid)[key]
            raw = bytearray((ex.PROJECT / ref['path']).read_bytes())
            raw[-2:-1] = b' '
            sha = ref['sha256']
            self.put(ref, data=bytes(raw))
            ref['sha256'] = sha
            with self.assertRaisesRegex(ValueError, 'pinned', msg=(sid, key)):
                build(manifest)
        for did, key in (('refed', ('consentEthics', 'record')), ('orthosis-error-detection', ('licenseRecord',)),
                         ('eeg-fnirs-handwriting', ('consentEthics', 'challengePaper', 'pdf'))):
            manifest = copy.deepcopy(MANIFEST)
            ref = dataset(manifest, did)
            for k in key:
                ref = ref[k]
            sha = ref['sha256']
            self.put(ref, data=(ex.PROJECT / ref['path']).read_bytes() + b' ')
            ref['sha256'] = sha
            with self.assertRaisesRegex(ValueError, 'pinned', msg=did):
                build(manifest)

    def test_an_export_its_approval_did_not_name_is_refused(self):
        manifest = copy.deepcopy(MANIFEST)
        ref = source(manifest, REFED)['export']
        e = self.get(ref)
        e['title'] = 'x'
        self.put(ref, e)
        with self.assertRaisesRegex(ValueError, 'does not bind these bytes'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        ref = source(manifest, BINGO)['export']
        e = self.get(ref)
        e['model'] = 'x'
        self.put(ref, e)
        with self.assertRaisesRegex(ValueError, 'does not bind these bytes'):
            build(manifest)

    def test_the_eegpt_export_may_differ_from_its_audited_payload_only_in_the_named_fields(self):
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, OFM)
        e = self.get(s['export'])
        e['paired_primary_difference']['mean'] = 0.01
        sha = self.put(s['export'], e)
        f = self.get(s['finalization'])
        f['final_export_sha256'] = sha
        self.put(s['finalization'], f)
        with self.assertRaisesRegex(ValueError, 'beyond the named fields'):
            build(manifest)

    def test_the_readings_are_held_to_the_intervals(self):
        # BINGO: a contrast whose interval no longer spans zero.
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, BINGO)
        e = self.get(s['export'])
        e['contrasts']['transfer_minus_within']['percentile_2_5_97_5'] = [0.001, 0.02]
        sha = self.put(s['export'], e)
        f = self.get(s['finalization'])
        f['approved_export_sha256'] = sha
        self.put(s['finalization'], f)
        with self.assertRaisesRegex(ValueError, 'no longer spans zero'):
            build(manifest)
        # REFED: EEG Ridge no longer worse than every control.
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, REFED)
        e, a, c = self.get(s['export']), self.get(s['resultAudit']), self.get(s['approval'])
        for blk in (e['metrics']['pooled'], a['independently_recomputed_pooled_metrics']):
            p = blk['joint_person_video_holdout']['eeg_ridge']
            p['MAE_by_axis'], p['equal_axis_mean_MAE'] = [30.0, 30.0], 30.0
        c['public_export_sha256'] = a['safe_export']['sha256'] = self.put(s['export'], e)
        c['result_audit_sha256'] = self.put(s['resultAudit'], a)
        self.put(s['approval'], c)
        with self.assertRaisesRegex(ValueError, 'EEG Ridge is no longer worse'):
            build(manifest)

    def test_every_interval_must_contain_its_mean(self):
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, BINGO)
        e = self.get(s['export'])
        e['main']['train_gr_test_gr']['percentile_2_5_97_5'] = [0.07, 0.08]
        sha = self.put(s['export'], e)
        f = self.get(s['finalization'])
        f['approved_export_sha256'] = sha
        self.put(s['finalization'], f)
        with self.assertRaisesRegex(ValueError, 'does not contain its mean'):
            build(manifest)

    def test_a_per_person_value_is_refused_by_value(self):
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, O64)
        e, a, c = self.get(s['export']), self.get(s['resultAudit']), self.get(s['approval'])
        eeg = next(r for r in e['primary_results'] if r['arm'] == 'eeg' and r['metric'] == 'auroc')
        for blk in (e['matched_eeg_minus_confound_balanced_accuracy'], a['eeg_minus_confound_primary_ba']):
            blk['range'] = [eeg['mean'], 0.3]
        c['sha256'][ex.in_batch(s['export'])] = self.put(s['export'], e)
        self.put(s['resultAudit'], a)
        self.put(s['approval'], c)
        with self.assertRaisesRegex(ValueError, 'per-person value reached'):
            build(manifest)

    def test_the_printed_figures_must_be_the_handoffs(self):
        manifest = copy.deepcopy(MANIFEST)
        s = source(manifest, REFED)
        e, a, c = self.get(s['export']), self.get(s['resultAudit']), self.get(s['approval'])
        for blk in (e['metrics']['pooled'], a['independently_recomputed_pooled_metrics']):
            p = blk['shared_stimulus_person_holdout']['duration_video_id_ridge']
            p['MAE_by_axis'] = [p['MAE_by_axis'][0] + 0.002, p['MAE_by_axis'][1]]
            p['equal_axis_mean_MAE'] = sum(p['MAE_by_axis']) / 2
        c['public_export_sha256'] = a['safe_export']['sha256'] = self.put(s['export'], e)
        c['result_audit_sha256'] = self.put(s['resultAudit'], a)
        self.put(s['approval'], c)
        with self.assertRaisesRegex(ValueError, 'the handoff does not state'):
            build(manifest)

    # ------------------------------------------------------------------ rights
    def test_the_rights_records(self):
        d = build(MANIFEST)['datasets']
        self.assertEqual({k: v['rights']['license'] for k, v in d.items()},
                         {'orthosis-error-detection': 'CC BY 4.0', 'bingo-imagined-speech': 'No licence stated',
                          'eeg-fnirs-handwriting': 'CC BY-NC-SA 4.0', 'refed': 'CC BY-NC-SA 4.0'})
        o, b, h, r = (d[k]['consent_and_ethics'] for k in d)
        self.assertTrue(o['ethics_approval']['stated'] and o['informed_consent']['stated'])
        self.assertIn('University of Duisburg-Essen', o['ethics_approval']['statement'])
        self.assertFalse(b['ethics_approval']['stated'])
        self.assertIsNone(b['ethics_approval']['statement'])
        self.assertTrue(b['informed_consent']['stated'])
        self.assertIn('NATO-alphabet', b['informed_consent']['scope'])
        self.assertIn('owner decision', b['basis'])
        self.assertFalse(h['ethics_approval']['stated'] or h['informed_consent']['stated'])
        self.assertTrue(h['gap'].startswith('No ethics-approval or informed-consent statement was found.'))
        self.assertIn('owner decision', h['basis'])
        self.assertEqual([x['source'] for x in h['searched']], ['the dataset card', 'a participating team’s challenge paper', 'the organisers’ paper'])
        self.assertEqual(h['searched'][1]['url'], 'https://arxiv.org/abs/2608.03176v2')
        self.assertIn('forthcoming', h['searched'][2]['status'])
        self.assertIn('IRB-CASIA', r['ethics_approval']['statement'])
        self.assertEqual([d[k]['publication'] for k in d], ['released', 'released', 'released', 'released'])
        for k, v in d.items():
            self.assertIn('not endorsed by the', v['rights']['attribution'], k)
        self.assertIn('Elsa Andrea Kirchner', d['orthosis-error-detection']['rights']['attribution'])
        self.assertIn('Ziyu Jia', d['refed']['rights']['attribution'])

    def test_a_statement_needs_its_quote_in_the_source(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'refed')['consentEthics']['quotes'][1]['text'] = 'consented to public sharing'
        with self.assertRaisesRegex(ValueError, 'the consent statement has no quote'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'bingo-imagined-speech')['consentEthics']['quotes'][0]['text'] = 'signed a consent form for this dataset'
        with self.assertRaisesRegex(ValueError, 'no quote in D3.1'):
            build(manifest)

    def test_the_challenge_paper_is_read_for_what_it_says(self):
        # The handwriting gap rests on the card and a participating team's challenge paper: the paper must be the one
        # named, say what is quoted, carry no ethics, consent or dataset-licence statement, and list the organisers'
        # paper as forthcoming.
        def cp(m):
            return dataset(m, 'eeg-fnirs-handwriting')['consentEthics']['challengePaper']
        manifest = copy.deepcopy(MANIFEST)
        cp(manifest)['quotes'][0]['text'] = 'The organisers obtained ethics approval'
        with self.assertRaisesRegex(ValueError, 'does not say'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        ref = cp(manifest)['html']
        page = (ex.PROJECT / ref['path']).read_text().replace('</body>', '<p>All participants gave informed consent.</p></body>')
        self.put(ref, data=page.encode())
        with self.assertRaisesRegex(ValueError, "mentions 'consent'"):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        ref = cp(manifest)['text']
        self.put(ref, data=(ex.PROJECT / ref['path']).read_bytes() + 'The data are released under a CC BY licence.\n'.encode())
        with self.assertRaisesRegex(ValueError, 'states a licence'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        cp(manifest)['organisersPaper']['title'] = 'A published organisers’ paper'
        with self.assertRaisesRegex(ValueError, 'forthcoming'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        cp(manifest)['arxiv'] = '2608.03176v1'
        with self.assertRaisesRegex(ValueError, 'not a listed basis|another paper'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'eeg-fnirs-handwriting')['consentEthics']['gap'] = 'Consent was not checked.'
        with self.assertRaisesRegex(ValueError, 'the gap'):
            build(manifest)

    def test_the_licence_must_be_the_records(self):
        for did, lic in (('orthosis-error-detection', 'CC0-1.0'), ('refed', 'CC BY 4.0'),
                         ('bingo-imagined-speech', 'CC BY 4.0')):
            manifest = copy.deepcopy(MANIFEST)
            dataset(manifest, did)['license'] = lic
            with self.assertRaises(ValueError, msg=did):
                build(manifest)

    def test_an_absence_is_checked_against_the_page(self):
        manifest = copy.deepcopy(MANIFEST)
        ref = dataset(manifest, 'bingo-imagined-speech')['licenseRecord']
        page = (ex.PROJECT / ref['path']).read_text().replace('</body>', '<p>Licence: CC BY 4.0</p></body>')
        self.put(ref, data=page.encode())
        with self.assertRaisesRegex(ValueError, "mentions 'licen'"):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        ref = dataset(manifest, 'eeg-fnirs-handwriting')['consentEthics']['record']
        page = (ex.PROJECT / ref['path']).read_text().replace('</body>', '<p>Participants gave consent.</p></body>')
        self.put(ref, data=page.encode())
        with self.assertRaisesRegex(ValueError, "mentions 'consent'"):
            build(manifest)

    def test_the_confidential_plan_is_never_cited(self):
        text = json.dumps(build(self.switched(**{HAND: 'released'})), ensure_ascii=False)
        manifest = ex.MANIFEST.read_text(encoding='utf-8')
        for token in ('D1.2', 'Data Management Plan', '/download/374', 'Data Access Committee', 'Confidential'):
            self.assertNotIn(token, text)
            self.assertNotIn(token, manifest)
        self.assertNotIn('internalEvidence', dataset(MANIFEST, 'bingo-imagined-speech'))

    @unittest.skipUnless(shutil.which('pdftotext'), 'pdftotext is not installed')
    def test_the_text_extractions_reproduce_their_pdfs(self):
        b = dataset(MANIFEST, 'bingo-imagined-speech')
        pairs = [(d['pdf'], d['text']) for k, d in b['sourceDocuments'].items() if k != 'deliverablesPage']
        r = dataset(MANIFEST, 'refed')['consentEthics']
        pairs.append((r['document'], r['record']))
        h = dataset(MANIFEST, 'eeg-fnirs-handwriting')['consentEthics']['challengePaper']
        pairs.append((h['pdf'], h['text']))
        for pdf, txt in pairs:
            out = subprocess.run(['pdftotext', '-layout', str(ex.PROJECT / pdf['path']), '-'], capture_output=True,
                                 check=True).stdout
            self.assertEqual(digest(out), txt['sha256'], pdf['path'])

    # ------------------------------------------------------------------ what stays out
    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('min', 'max', 'minimum', 'maximum', 'median', 'range', 'means', 'p10', 'p90', 'confusion',
                    'mean_field_confusion', 'perclass_recall', 'per_class_recall', 'pooled', 'combined_RMSE',
                    'MAE_by_axis', 'predictions', 'probabilities', 'features', 'feature_dimensions', 'threshold',
                    'participant_id', 'record_ids', 'private_audit_path', 'elapsed_seconds', 'peak_rss_bytes'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        with self.assertRaisesRegex(ValueError, 'refused field'):
            ex.scrub_check({'results': {'x': {'arms': {'eeg': {'observed_range': [0.1, 0.2]}}}}})
        ex.scrub_check({'results': {'x': {'permutation_control': {'a': {'observed_range': [0.1, 0.2]}}}}})
        for text in ('S12', 'sub_07', 'sub-07', 'BINGO_GRENG.mat', 'raw.zip', '/home/someone/x', '/Users/someone/x', 'on TRX50',
                     'Gal4', 'BCI_Arena'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_no_version_label_or_update_marker_in_the_text(self):
        for text in ('the v2 analysis', 'handwriting (v1)', 'updated 12 October 2026', 'Added 2026-10-12',
                     'in this update', 'generated 2026-10-12'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        ex.scrub_check({'results': {'x': {'note': 'D3.1, version 2.0; doi:10.5281/zenodo.8345429'}}})
        text = json.dumps({k: v for k, v in build(self.switched(**{HAND: 'released'})).items()
                           if k not in ('schema_version', 'release_id')})
        self.assertFalse(re.search(r'(?<![./\w-])v\d+\b', text))
        self.assertNotIn('Jev', text)
        self.assertNotIn('jev', text.lower())

    def test_unsupported_claims_appear_only_negated(self):
        for sentence in ('The EEG recognises the error.', 'EEGPT is superior.', 'The arms are equivalent.',
                         'A zero-shot result.', 'Ready for online use.', 'This shows a neural origin.'):
            with self.assertRaises(ValueError, msg=sentence):
                ex.claims_negated({'results': {'x': {'reading': sentence}}})
        ex.claims_negated({'results': {'x': {'reading': 'Not zero-shot; neither equivalence nor superiority.'}}})

    def test_the_eegpt_weights_are_never_apache(self):
        for sentence in ('EEGPT is Apache-2.0.', 'The weights are Apache-2.0 code.', 'The checkpoint is under the Apache '
                         'code licence.'):
            with self.assertRaises(ValueError, msg=sentence):
                ex.weights_not_apache({'results': {'x': {'note': sentence}}})
        ex.weights_not_apache({'results': {'x': {'note': 'Apache-2.0 covers the repository code, not the weights.'}}})
        p = build(MANIFEST)
        p['results'][OFM]['model']['weights_licence'] = 'Apache-2.0'
        with self.assertRaisesRegex(ValueError, 'not tied to the code|must stay unresolved'):
            ex.weights_not_apache(p)
        p = build(MANIFEST)
        p['results'][OFM]['model']['weights_distributed'] = True
        with self.assertRaisesRegex(ValueError, 'must stay unresolved'):
            ex.weights_not_apache(p)

    def test_prose_numerals_come_from_the_pinned_sources(self):
        with self.assertRaisesRegex(ValueError, 'in no pinned handoff or source'):
            ex.written_from({'reading': 'about 73.4 percent'}, ('72.97%',), 'x')
        ex.written_from({'reading': '72.97 percent', 'model': '9.9'}, ('72.97',), 'x')

    def test_holds_and_status_items_carry_no_figure(self):
        for what in ('statusOnly',):
            manifest = copy.deepcopy(MANIFEST)
            manifest[what][0]['reason'] = 'the EMG runs at 1000 Hz'
            with self.assertRaisesRegex(ValueError, 'carries a figure'):
                build(manifest)
        with self.assertRaisesRegex(ValueError, 'carries a figure'):
            ex.figure_free([{'id': 'x', 'statement': 'no score', 'reason': 'it scored 0.61', 'scope': 'x'}], 'hold')

    def test_no_private_path_or_identifier_reaches_the_files(self):
        text = json.dumps(build(self.switched(**{HAND: 'released'})), ensure_ascii=False)
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', 'Gal4', 'TRX50', 'twu', '.mat', '.bdf',
                      'sub_', 'sub-', 'scores.json'):
            self.assertNotIn(token, text)
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', 'TRX50'):
                self.assertNotIn(token, body, f'{path.name}: {token}')

    # ------------------------------------------------------------------ the independent audit
    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            p['results'][BINGO]['directions'][2]['balanced_accuracy']['mean'] += 1e-12
        with self.served(edit=edit), self.assertRaisesRegex(au.AuditFailure, 'directions'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['results'][O64]['eeg_minus_confound']['balanced_accuracy_difference']['spread'] = 0.25
        with self.served(edit=extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['results'][REFED]['conditions'][0]['arms']['source_video_lookup']['equal_axis_mae']
        with self.served(edit=missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_and_a_wrong_flag(self):
        def zero(p):
            p['results'][O64]['eeg_minus_confound']['balanced_accuracy_difference']['interval_95'] = 0
        with self.served(edit=zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def flag(p):
            p['results'][OFM]['paired']['interval_excludes_zero'] = True
        with self.served(edit=flag), self.assertRaisesRegex(au.AuditFailure, 'flag'):
            au.audit()

    def test_the_audit_catches_a_per_person_or_held_value(self):
        e = json.loads((ex.PROJECT / source(MANIFEST, O64)['export']['path']).read_bytes())
        low = e['matched_eeg_minus_confound_balanced_accuracy']['range'][0]

        def leak(p):
            p['results'][O64]['eeg_minus_confound']['balanced_accuracy_difference']['mean'] = low
        with self.served(edit=leak), self.assertRaises(au.AuditFailure):
            au.audit()
        held = build(self.switched(**{HAND: 'released'}))['results'][HAND]['arms']['relative_eeg']['balanced_accuracy']['mean']

        def held_leak(p):
            p['results'][REFED]['independent_audit']['largest_metric_difference'] = held
        with self.served(edit=held_leak), self.assertRaises(au.AuditFailure):
            au.audit()


SITE = ex.PROJECT / 'site'
NPM, NODE = shutil.which('npm'), shutil.which('node')
# What the site build and check-workbench read from the site folder; the rest of the repository is linked read-only.
SITE_PARTS = ('src', 'public', 'scripts', 'package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json')


@unittest.skipUnless(ex.inputs_available() and NPM and NODE and (SITE / 'node_modules').is_dir()
                     and os.environ.get('BCI_SKIP_SITE_BUILD') != '1',
                     'needs the pinned inputs, node and the site’s node_modules (BCI_SKIP_SITE_BUILD=1 skips it)')
class HeldSiteBuild(unittest.TestCase):
    """One manifest switch holds a pilot, with no other edit (BINGO, owner decision 3; the handwriting analysis, owner
    decision of 2026-10-12). The payload is built with the pilot held and a scratch copy of the site is built from it, so
    the page's own guards run, then the archive metadata is rewritten and check-workbench runs against that build.
    Nothing outside the scratch copy is written."""

    def held_build(self, sid):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, sid)['publication'] = 'status_only'
        data = (json.dumps(build(manifest), indent=2, ensure_ascii=False) + '\n').encode()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / 'repo'
        repo.mkdir()
        written = ('.zenodo.json', 'CITATION.cff')   # write-zenodo-metadata.mjs rewrites the first; copies, not links
        for entry in ex.PROJECT.iterdir():
            if entry.name not in ('site', '.git', *written):
                (repo / entry.name).symlink_to(entry)
        for name in written:
            shutil.copy2(ex.PROJECT / name, repo / name)
        site = repo / 'site'
        site.mkdir()
        for part in SITE_PARTS:
            (shutil.copytree if (SITE / part).is_dir() else shutil.copy2)(SITE / part, site / part)
        # Packages linked one by one, so the build's caches land in the scratch copy, not in the real node_modules.
        (site / 'node_modules').mkdir()
        for entry in (SITE / 'node_modules').iterdir():
            if entry.name not in ('.astro', '.vite', '.cache'):
                (site / 'node_modules' / entry.name).symlink_to(entry)
        for rel in ('src/data/pilot-studies-update.json', 'public/data/pilot-studies-update.json'):
            (site / rel).write_bytes(data)
        for cmd in ((NPM, 'run', 'build'), (NODE, 'scripts/write-zenodo-metadata.mjs'), (NODE, 'scripts/check-workbench.mjs')):
            r = subprocess.run(cmd, cwd=site, capture_output=True, text=True, timeout=900)
            self.assertEqual(r.returncode, 0, f'{" ".join(cmd[1:])} with {sid} held:\n{(r.stdout + r.stderr)[-4000:]}')
        return repo, site / 'dist'

    def test_the_site_builds_and_checks_with_bingo_held(self):
        repo, dist = self.held_build(BINGO)
        self.assertFalse((dist / 'datasets/bingo-imagined-speech').exists())
        self.assertFalse((dist / 'zh/datasets/bingo-imagined-speech').exists())
        page = (dist / 'topics/pilot-studies/index.html').read_text()
        self.assertIn('id="bingo-cross-language-rights"', page)
        self.assertIn('Four findings from three pilots', page)
        # The NeuroLM-on-EEGMAT panel is its own release: a held pilot neither drops it nor pulls it into the count.
        self.assertIn('id="neurolm-eegmat"', page)
        self.assertIn('data-counted="false"', page)
        self.assertIn('data-fig="neurolm-eegmat-update.json|pct2|0.6449074074074076"', page)
        self.assertNotIn('pilot-studies-update.json|pct1|0.0666', page)
        self.assertIn('<tr id="hold-bingo-cross-language-rights"', (dist / 'releases/index.html').read_text())
        self.assertIn('BINGO, held', (dist / 'data-use/index.html').read_text())
        self.assertNotIn('bingo-project.gr', (repo / '.zenodo.json').read_text())

    def test_the_site_builds_and_checks_with_handwriting_held(self):
        repo, dist = self.held_build(HAND)
        self.assertFalse((dist / 'datasets/eeg-fnirs-handwriting').exists())
        self.assertFalse((dist / 'zh/datasets/eeg-fnirs-handwriting').exists())
        page = (dist / 'topics/pilot-studies/index.html').read_text()
        self.assertIn('id="handwriting-mask-aware-rights"', page)
        self.assertIn('Four findings from three pilots', page)
        # The NeuroLM-on-EEGMAT panel is its own release: a held pilot neither drops it nor pulls it into the count.
        self.assertIn('id="neurolm-eegmat"', page)
        self.assertIn('data-counted="false"', page)
        self.assertIn('data-fig="neurolm-eegmat-update.json|pct2|0.6449074074074076"', page)
        self.assertNotIn('pilot-studies-update.json|pct2|0.2680864', page)
        self.assertIn('<tr id="hold-handwriting-mask-aware-rights"', (dist / 'releases/index.html').read_text())
        self.assertIn('The handwriting dataset, held', (dist / 'data-use/index.html').read_text())
        self.assertNotIn('lasfk', (repo / '.zenodo.json').read_text())


if __name__ == '__main__':
    unittest.main()
