"""Regression tests for the additional public release boundary, using audited aggregates."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from export_deployment_topics import (PROJECT, MANIFEST, OUTPUTS, build_export,
                                       load_reviewed_export, serialized_export)


class DeploymentReleaseTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())
        inputs = {key: (PROJECT / value['path']).read_bytes()
                  for key, value in self.manifest['inputs'].items()}
        self.source_bytes = inputs.pop('aggregate')
        self.source = json.loads(self.source_bytes)
        self.inputs = {key: json.loads(value) for key, value in inputs.items()}

    def build(self):
        return build_export(self.source_bytes, self.inputs['audit'], self.inputs['rights'],
                            self.inputs['base_manifest'], self.manifest)

    def reseal_fixture(self):
        # Bypass the first digest guard to exercise independent inner guards.
        self.source_bytes = json.dumps(self.source).encode()
        digest = hashlib.sha256(self.source_bytes).hexdigest()
        self.manifest['inputs']['aggregate']['sha256'] = digest
        self.inputs['audit']['aggregate_sha256'] = digest

    def test_export_has_complete_citations_and_identical_download(self):
        result = load_reviewed_export()
        self.assertEqual([t['measurements'] for t in result['topics']], [16, 32, 16, 18])
        self.assertEqual(result['coverage']['seed_runs'], 15)
        self.assertEqual(len(result['dataset_citations']), 9)
        self.assertTrue(all(p.read_bytes() == serialized_export() for p in OUTPUTS))

    def test_modified_score_fails_reviewed_hash(self):
        self.source['rows'][0]['value'] += 0.01
        self.source_bytes = json.dumps(self.source).encode()
        with self.assertRaisesRegex(ValueError, 'Unreviewed aggregate'):
            self.build()

    def test_failed_independent_audit_fails_closed(self):
        self.inputs['audit']['status'] = 'fail'
        with self.assertRaisesRegex(ValueError, 'Independent audit'):
            self.build()

    def test_revoked_new_and_existing_sources_fail_closed(self):
        self.inputs['rights']['datasets'][0]['decision'] = 'hold'
        with self.assertRaisesRegex(ValueError, 'revoked'):
            self.build()
        self.setUp()
        for record in self.inputs['base_manifest']['datasets']:
            if record['id'] == 'ds003810':
                record['decision'] = 'withhold'
        with self.assertRaisesRegex(ValueError, 'revoked'):
            self.build()

    def test_held_model_cannot_enter_release(self):
        self.source['rows'][0]['model'] = 'eegpt'
        self.reseal_fixture()
        with self.assertRaisesRegex(ValueError, 'Unapproved model'):
            self.build()

    def test_private_identifier_in_method_text_is_rejected(self):
        self.source['method_references'][0]['adaptation'] = 'Result for participant-007'
        self.reseal_fixture()
        with self.assertRaisesRegex(ValueError, 'Participant identifier'):
            self.build()

    def test_individual_prediction_field_is_rejected(self):
        self.source['rows'][0]['y_pred'] = [1, 0]
        self.reseal_fixture()
        with self.assertRaisesRegex(ValueError, 'Unknown row fields'):
            self.build()

    def test_mixed_backend_seed_summary_is_rejected(self):
        self.inputs['audit']['seed_runs'][0]['backend'] = 'cuda'
        with self.assertRaisesRegex(ValueError, 'backend mismatch'):
            self.build()

    def test_seed_aggregate_must_match_recomputed_values(self):
        self.source['seed_sensitivity'][0]['mean_balanced_accuracy'] = 0.99
        self.reseal_fixture()
        with self.assertRaisesRegex(ValueError, 'mean_balanced_accuracy'):
            self.build()


if __name__ == '__main__':
    unittest.main()
