"""The 2026-10-01 adaptation batch: what must stay out, and what must equal its audit."""
import copy
import json
import unittest

import export_adaptation_update as ad

MANIFEST = json.loads(ad.MANIFEST.read_bytes())


def build(manifest, snapshot=None):
    return ad.build(json.dumps(manifest).encode(), snapshot)[0]


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


@unittest.skipUnless(ad.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class AdaptationBoundary(unittest.TestCase):
    def test_the_published_file_is_the_reviewed_build(self):
        for out in ad.OUTPUTS:
            self.assertEqual(out.read_bytes(), ad.serialized_export())

    def test_the_handoff_figures(self):
        r = build(MANIFEST)['results']['eegmat-labram-adaptation']
        ba = {a['id']: round(a['balanced_accuracy']['mean'] * 100, 2) for a in r['arms']}
        self.assertEqual(ba, {'frozen': 56.62, 'last-block': 65.71, 'lora-r4': 64.07})
        c = {x['id']: x for x in r['paired_contrasts']['balanced_accuracy']}
        self.assertEqual((c['lora-r4_minus_frozen']['helped'], c['lora-r4_minus_frozen']['harmed']), (30, 6))
        lo, hi = c['lora-r4_minus_last-block']['bootstrap_95']
        self.assertTrue(lo < 0 < hi, 'LoRA vs. last block: the interval crosses zero')

    def test_every_contrast_covers_the_cohort(self):
        r = build(MANIFEST)['results']['eegmat-labram-adaptation']
        for metric in r['paired_contrasts'].values():
            for c in metric:
                self.assertEqual(c['helped'] + c['harmed'] + c['tied'], 36, c['id'])

    def test_memory_and_per_person_fields_are_refused(self):
        for key in ('min', 'max', 'median', 'q1', 'q3', 'cumulative_process_rss_high_water_bytes',
                    'sampled_max_mps_allocated_bytes', 'person_metrics_sha256'):
            with self.assertRaises(ValueError, msg=key):
                ad.scrub_check({'results': {'x': {key: 1}}})
        text = json.dumps(build(MANIFEST))
        for key in ('rss', 'mps_allocated', '"min"', '"max"', '"median"'):
            self.assertNotIn(key, text)

    def test_the_cross_day_source_has_no_score(self):
        st = build(MANIFEST)['status_only']
        self.assertEqual([s['id'] for s in st], ['bnci2015-001-crossday'])
        self.assertIs(st[0]['scores_published'], False)
        for field in ('balanced_accuracy', 'macro_f1', 'mean_change', 'bootstrap_95', 'arms'):
            self.assertNotIn(f'"{field}"', json.dumps(st[0]))

    def test_the_cross_day_source_cannot_be_promoted_by_a_decision_alone(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, 'bnci2015-001-crossday')['decision'] = 'aggregate_preview'
        with self.assertRaises(ValueError):
            build(manifest)

    def test_a_changed_input_byte_is_refused(self):
        for key in ('summary', 'numericalAudit', 'protocol'):
            manifest = copy.deepcopy(MANIFEST)
            source(manifest, 'eegmat-labram-adaptation')[key]['sha256'] = '0' * 64
            with self.assertRaises(ValueError, msg=key):
                build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, 'eegmat-labram-adaptation')['seeds'][1]['numericalAudit']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_the_matrix_reference_must_share_the_folds_and_carries_no_number(self):
        snapshot = json.loads(ad.SNAPSHOT.read_text())
        ref = build(MANIFEST, snapshot)['results']['eegmat-labram-adaptation']['matrix_reference']
        self.assertIs(ref['same_people_and_folds'], True)
        self.assertIs(ref['paired_with_these_arms'], False)
        self.assertFalse(any(isinstance(v, float) for v in ref.values()), 'the pointer carries no figure')
        other = copy.deepcopy(snapshot)
        next(t for t in other['tracks'] if t['id'] == 'arithmetic-rest')['protocolSha'] = '0' * 64
        with self.assertRaises(ValueError):
            build(MANIFEST, other)

    def test_an_incomplete_rights_record_is_refused(self):
        for missing in ('privacyReview', 'reviewBasis', 'attribution', 'licenseUrl'):
            manifest = copy.deepcopy(MANIFEST)
            del source(manifest, 'eegmat-labram-adaptation')[missing]
            with self.assertRaises(ValueError, msg=missing):
                build(manifest)


if __name__ == '__main__':
    unittest.main()
