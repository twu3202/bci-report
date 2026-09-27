"""The 2026-09-27 context batch: what must stay out, and what must equal its audit."""
import copy
import json
import unittest

import export_context_update as cx

MANIFEST = json.loads(cx.MANIFEST.read_bytes())


def build(manifest):
    return cx.build(json.dumps(manifest).encode())[0]


def hold_ysu(manifest):
    """The pilot as it stood before its consent statement was read."""
    next(s for s in manifest['sources'] if s['id'] == 'ysu-async-ssvep')['decision'] = 'hold'
    return manifest


@unittest.skipUnless(cx.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class ContextBoundary(unittest.TestCase):
    def test_a_held_source_leaves_no_trace(self):
        payload = json.dumps(build(hold_ysu(copy.deepcopy(MANIFEST))))
        for trace in ('ysu', 'YSU', '24906300', '27706710'):
            self.assertNotIn(trace, payload, trace)

    def test_lifting_the_hold_needs_the_complete_record(self):
        for missing in ('privacyReview', 'reviewedAt', 'reviewBasis', 'attribution'):
            manifest = copy.deepcopy(MANIFEST)
            del next(s for s in manifest['sources'] if s['id'] == 'ysu-async-ssvep')[missing]
            with self.assertRaises(ValueError, msg=missing):
                build(manifest)

    def test_the_pilot_publishes_coverage_with_accuracy(self):
        ysu = build(MANIFEST)['results']['ysu-async-ssvep']
        w = ysu['control_windows']
        self.assertEqual((w['frequency_recognised'], w['accepted'], w['accepted_and_correct'], w['tested']),
                         (152, 130, 121, 192), 'the handoff counts')
        self.assertEqual([(f['accepted'], f['tested']) for f in ysu['false_acceptance']],
                         [(9, 48), (20, 48), (11, 96)])
        self.assertNotIn('"range":', json.dumps(ysu), 'per-participant ranges of a four-person pilot')

    def test_quartiles_ranges_and_extremes_are_refused(self):
        for key in ('min', 'max', 'median', 'q1', 'q3', 'range'):
            with self.assertRaises(ValueError, msg=key):
                cx.scrub_check({'results': {'x': {'balanced_accuracy': {key: 0.5}}}})
        text = json.dumps(build(MANIFEST))
        for key in ('"min"', '"max"', '"median"', '"q1"', '"q3"'):
            self.assertNotIn(key, text)

    def test_a_published_mean_must_equal_the_audit(self):
        block = {'mean': 0.66, 'bootstrap_mean_ci95': [0.61, 0.70], 'n_participants': 21}
        with self.assertRaises(ValueError):
            cx.audited_metric(block, {'mean': 0.65, 'bootstrap_mean_ci95': [0.61, 0.70]}, 'test')

    def test_a_changed_input_byte_is_refused(self):
        manifest = copy.deepcopy(MANIFEST)
        next(s for s in manifest['sources'] if s['id'] == 'gait-eeg')['result']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_the_display_transfer_result_says_it_has_no_same_display_reference(self):
        p300 = build(MANIFEST)['results']['vr-pc-p300']
        self.assertIs(p300['same_display_reference'], False)
        self.assertEqual(set(p300['timings']), {'onset_corrected', 'recorded_tag'})

    def test_the_gait_comparator_is_marked_and_kept_out_of_rankings(self):
        g = build(MANIFEST)['results']['gait-eeg']
        self.assertIs(g['not_for_model_rankings'], True)
        self.assertEqual([m['comparator'] for m in g['models']], [False, True])

    def test_the_one_person_pilot_has_no_score(self):
        st = build(MANIFEST)['status_only'][0]
        self.assertIs(st['scores_published'], False)
        for field in ('balanced_accuracy', 'accuracy', 'auroc', 'models', 'timings'):
            self.assertNotIn(f'"{field}"', json.dumps(st))

    def test_the_published_file_is_the_reviewed_build(self):
        for out in cx.OUTPUTS:
            self.assertEqual(out.read_bytes(), cx.serialized_export())


if __name__ == '__main__':
    unittest.main()
