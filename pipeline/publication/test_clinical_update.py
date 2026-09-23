"""The 2026-09-23 clinical boundary: what a clinical cohort adds to what must stay out."""
import copy
import json
import unittest

import export_clinical_update as cl

MANIFEST = json.loads(cl.MANIFEST.read_bytes())


def build(manifest):
    return cl.build(json.dumps(manifest).encode())[0]


@unittest.skipUnless(cl.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class ClinicalBoundary(unittest.TestCase):
    def test_a_status_only_source_publishes_no_score(self):
        payload = build(MANIFEST)
        held = {s['id'] for s in MANIFEST['sources'] if s['decision'] == 'status_only'}
        self.assertTrue(held, 'the fixture should exercise at least one status-only source')
        self.assertFalse(held & set(payload['results']))
        # A metric field, not the word: "no accuracy row exists to publish" is the point.
        def keys(value):
            if isinstance(value, dict):
                return set(value) | {k for v in value.values() for k in keys(v)}
            if isinstance(value, list):
                return {k for v in value for k in keys(v)}
            return set()
        metric_fields = {'balanced_accuracy', 'mean_balanced_accuracy', 'macro_f1', 'auroc',
                         'balanced_accuracy_bootstrap_95', 'models'}
        for entry in payload['status_only']:
            self.assertIs(entry['scores_published'], False)
            self.assertFalse(keys(entry) & metric_fields, entry['id'])

    def test_the_demographic_profile_of_a_clinical_group_is_refused(self):
        # It is in the reviewed audit and it is an aggregate. It still does not go out.
        audit = json.loads((cl.PROJECT / MANIFEST['sources'][0]['numericalAudit']['path']).read_bytes())
        self.assertIn('confound_context', audit['aggregate'], 'the fixture should still contain it')
        for leak in ({'results': {'x': {'confound_context': {'PD': {'age_mean': 68.5}}}}},
                     {'results': {'x': [{'age_mean': 70.9}]}},
                     {'results': {'x': {'gender_counts': {'F': 32, 'M': 68}}}}):
            with self.assertRaises(ValueError):
                cl.scrub_check(leak)
        self.assertNotIn('age_mean', json.dumps(build(MANIFEST)))

    def test_the_six_person_band_descriptors_stay_out(self):
        with self.assertRaises(ValueError):
            cl.scrub_check({'x': {'alpha_8_13': {'median': 0.35}}})
        payload = build(MANIFEST)
        lfame = next(e for e in payload['status_only'] if e['id'] == 'lfame')
        self.assertIs(lfame['described']['numbers_published'], False)
        summary = json.loads((cl.PROJECT / 'research/hf_expansion_v5_20260922'
                              / 'lfame-descriptive-summary.json').read_bytes())
        published = json.dumps(payload)
        for task in summary['filename_task_token_recording_descriptors'].values():
            for band in task.values():
                for bound in ('minimum', 'median', 'maximum'):
                    self.assertNotIn(f'{band[bound]:.4f}'[:6], published, bound)

    def test_the_confound_comparator_cannot_be_read_as_an_eeg_model(self):
        models = {m['id']: m for m in build(MANIFEST)['results']['ds004584']['models']}
        self.assertIs(models['demographics_only']['excluded_from_model_comparisons'], True)
        self.assertIs(models['spectral_logistic']['excluded_from_model_comparisons'], False)
        self.assertEqual(models['demographics_only']['inputs'], 'no EEG')
        manifest = copy.deepcopy(MANIFEST)
        clinical = next(s for s in manifest['sources'] if s['id'] == 'ds004584')
        clinical['comparator']['id'] = 'spectral_logistic'   # the EEG model is not a comparator
        with self.assertRaises(ValueError):
            build(manifest)

    def test_a_published_number_must_equal_the_independent_replay(self):
        row = {'model': 'spectral_logistic', 'balanced_accuracy': 0.72, 'macro_f1': 0.71,
               'auroc': 0.76, 'balanced_accuracy_descriptive_95': [0.63, 0.79]}
        audited = {'metrics': {'balanced_accuracy': 0.75, 'macro_f1': 0.71, 'roc_auc': 0.76},
                   'descriptive_stratified_bootstrap_95': {'balanced_accuracy': [0.63, 0.79]}}
        with self.assertRaises(ValueError):
            cl.metric_block(row, audited)

    def test_a_changed_input_byte_is_refused(self):
        manifest = copy.deepcopy(MANIFEST)
        next(s for s in manifest['sources'] if s['id'] == 'ds004584')['results']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_the_claim_boundary_travels_with_the_score(self):
        payload = build(MANIFEST)
        self.assertIn('Not a diagnosis', payload['medical_disclaimer'])
        self.assertIn('Not a diagnosis', payload['results']['ds004584']['claim_boundary'])

    def test_no_per_person_field_reaches_the_output(self):
        text = json.dumps(build(MANIFEST))
        for key in cl.PER_PERSON_KEYS:
            self.assertNotIn(f'"{key}"', text, key)

    def test_the_published_file_is_the_reviewed_build(self):
        for out in cl.OUTPUTS:
            self.assertEqual(out.read_bytes(), cl.serialized_export())


if __name__ == '__main__':
    unittest.main()
