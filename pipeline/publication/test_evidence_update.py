"""The 2026-09-22 evidence boundary: what must stay out, and what must not drift."""
import copy
import json
import unittest

import export_evidence_update as ev

MANIFEST = json.loads(ev.MANIFEST.read_bytes())



def build(manifest):
    return ev.build(json.dumps(manifest).encode())[0]


@unittest.skipUnless(ev.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class EvidenceBoundary(unittest.TestCase):
    def test_held_and_excluded_sources_never_reach_the_output(self):
        payload = build(MANIFEST)
        held = {s['id'] for s in MANIFEST['sources'] if s['decision'] != 'aggregate_preview'}
        self.assertTrue(held, 'the fixture should exercise at least one hold')
        self.assertFalse(held & set(payload['results']))
        self.assertFalse(any(h in json.dumps(payload) for h in ('Alpha Waves', 'alphawaves', 'L-FAME')))

    def test_approving_a_source_needs_the_complete_record(self):
        manifest = copy.deepcopy(MANIFEST)
        alpha = next(s for s in manifest['sources'] if s['id'] == 'alphawaves')
        alpha['decision'] = 'aggregate_preview'   # no privacyReview, reviewedAt or reviewBasis yet
        with self.assertRaises(ValueError):
            build(manifest)

    def test_a_complete_approval_publishes_aggregates_only(self):
        manifest = copy.deepcopy(MANIFEST)
        alpha = next(s for s in manifest['sources'] if s['id'] == 'alphawaves')
        alpha.update(decision='aggregate_preview', task='Eyes open / closed', version='Zenodo 2605110',
                     privacyReview='test', reviewedAt='2026-09-22', reviewBasis=['https://example.org'])
        payload = build(manifest)
        text = json.dumps(payload['results']['alphawaves'])
        for key in ev.PER_PERSON_KEYS:
            self.assertNotIn(f'"{key}"', text, key)

    def test_a_changed_input_byte_is_refused(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['sources'][0]['summary']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_the_roadmap_cannot_be_promoted_by_a_wording_change(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['roadmap']['status'] = 'running'
        with self.assertRaises(ValueError):
            build(manifest)
        payload = build(MANIFEST)['roadmap']['peft']
        self.assertEqual(payload['status'], 'planned')
        self.assertIs(payload['real_eeg_results_available'], False)
        self.assertNotIn('elapsed', json.dumps(payload), 'smoke-test runtime is not a training cost')

    def test_a_per_person_field_is_refused_wherever_it_appears(self):
        with self.assertRaises(ValueError):
            ev.scrub_check({'results': {'x': {'configurations': [{'min': 0.35}]}}})

    def test_phantom_keeps_negative_r_squared_unclamped(self):
        conditions = build(MANIFEST)['results']['phantom']['conditions']
        r2 = {c['condition']: c['predictive_r_squared']['value'] for c in conditions}
        self.assertGreater(r2['Brain'], 0)
        self.assertLess(r2['Walking'], -700, 'predictive R² must be reported as measured, not floored at 0')

    def test_the_published_file_is_the_reviewed_build(self):
        self.assertEqual(ev.OUTPUTS[0].read_bytes(), ev.serialized_export())
        self.assertEqual(ev.OUTPUTS[1].read_bytes(), ev.serialized_export())


if __name__ == '__main__':
    unittest.main()
