"""Checks the actual release boundary; no waveforms or training are required."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from export_snapshot import approved, build, matching_audit, read, validate_public, write

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT/'research/publication_review_20260920'
BATCH = Path('<evidence-root>/benchmarks/parallel-v1/20260919/batch-state.json')
BETA = Path('<evidence-root>/benchmarks/beta-ssvep-v1/run-20260913-mps-v2')


class ReleaseBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(REVIEW/'release-manifest.json')
        cls.legacy = read(REVIEW/'previous-mvp.private.json')
        cls.batch = read(BATCH)
        cls.snapshot = build(cls.manifest, cls.legacy, cls.batch, BETA)

    def test_sensitive_fields_and_prose_are_rejected(self):
        for value in ({'subjectResults': []}, {'text': 'Participant sub-001'},
                      {'text': '<evidence-root>/private.npy'}, {'y': float('nan')}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_public(value)

    def test_review_requires_explicit_complete_record(self):
        record = next(r for r in self.manifest['datasets'] if r['decision']=='aggregate_preview')
        self.assertTrue(approved(record))
        for field in ('decision','source','version','license','licenseUrl','attribution',
                      'privacyReview','reviewedAt','reviewBasis'):
            changed = dict(record); changed.pop(field)
            self.assertFalse(approved(changed), field)
        self.assertFalse(approved({}))

    def test_real_snapshot_excludes_withheld_inputs_and_individual_rows(self):
        self.assertEqual(self.snapshot['coverage']['displayedProtocols'], 8)
        self.assertEqual(self.snapshot['coverage']['displayedComparisons'], 39)
        self.assertEqual(len({t['dataset'] for t in self.snapshot['tracks']}), 7)
        for track in self.snapshot['tracks']:
            self.assertNotIn('BNCI', track['dataset'])
            self.assertNotIn('eegpt', [r['id'] for r in track['rows']])
            self.assertAlmostEqual(track['elapsed'], sum(r['seconds'] for r in track['rows']))
        validate_public(self.snapshot)
        self.assertIn('subjectResults', json.dumps(self.legacy))
        self.assertNotIn('subjectResults', json.dumps(self.snapshot))
        self.assertNotIn('sub-001', json.dumps(self.snapshot))

    def test_independent_metric_mismatch_blocks_export(self):
        entry = next(e for e in self.batch['datasets'] if e['dataset']=='ds003810')
        run = Path(entry['runs'][0]['path'])
        results = read(run/'summary.json')['results']; audit = read(run/'independent-audit.json')
        matching_audit(results, audit)
        corrupt = copy.deepcopy(results)
        corrupt[0]['subject_mean_balanced_accuracy'] += .01
        with self.assertRaises(ValueError): matching_audit(corrupt, audit)

    def test_revoking_source_removes_every_related_protocol(self):
        manifest = copy.deepcopy(self.manifest)
        next(r for r in manifest['datasets'] if r['id']=='BETA')['decision'] = 'withhold'
        snapshot = build(manifest, self.legacy, self.batch, BETA)
        self.assertFalse(any(t['dataset']=='BETA' for t in snapshot['tracks']))
        self.assertEqual(snapshot['coverage']['displayedProtocols'], 6)

    def test_downloads_share_the_same_aggregate_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory); write(self.snapshot, dest)
            expected = {'experiments.json'} | {t['id']+suffix for t in self.snapshot['tracks']
                                                for suffix in ('-results.csv','-protocol.json')}
            self.assertEqual({p.name for p in (dest/'data').iterdir()}, expected)
            for path in dest.rglob('*'):
                if not path.is_file(): continue
                content = path.read_text()
                self.assertNotIn('subjectResults', content)
                self.assertNotIn('sub-001', content)
                self.assertNotIn('/Volumes/', content)
                if path.suffix=='.json': validate_public(json.loads(content))


if __name__=='__main__': unittest.main()
