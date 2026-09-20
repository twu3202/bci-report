"""Negative cases for the publication boundary guard.

The existing boundary tests cover the happy-path rejections with four top-level,
string-valued keys. Every case below passed `validate_public` before 2026-09-20:
the guard recursed into mapping *values* only, and matched paths and participant
identifiers against a short list of literal spellings. These are the shapes a
real leak would arrive in, so they are pinned here rather than left to review.
"""
import unittest

from export_snapshot import validate_public


class ValidatePublicRejects(unittest.TestCase):
    def assertRejected(self, payload, label):
        with self.assertRaises(ValueError, msg=f'{label} was not rejected'):
            validate_public(payload)

    def test_identifiers_and_paths_used_as_mapping_keys(self):
        for label, payload in [
            ('participant id as key', {'perSubject': {'sub-001': {'balanced_accuracy': 0.83}}}),
            ('local path as key', {'/Volumes/Archive/raw/sub-003.npy': 1}),
            ('path as key, nested', {'runs': [{'C:\\Users\\asus\\eeg.edf': 0.5}]}),
        ]:
            self.assertRejected(payload, label)

    def test_path_roots_beyond_the_original_four(self):
        for note in [
            'cached under /private/var/folders/9k/T/ds005342',
            'see /users/someone/project/experiments',          # macOS is case-insensitive
            'copied from D:\\Users\\asus\\eeg.edf',            # any drive letter
            '/mnt/eeg/session3.edf',
            '/media/usb/recording.edf',
            r'\\fileserver\share\eeg',
            'staged in /tmp/bciarena/run17',
        ]:
            self.assertRejected({'note': note}, note)

    def test_participant_id_spellings(self):
        for note in ['sub-7 excluded', 'sub_001 excluded', 'subject-002 excluded',
                     'participant 3 withdrew', 'A01T excluded for artifacts', 'Subj12 dropped']:
            self.assertRejected({'note': note}, note)

    def test_leak_buried_in_a_list_of_dicts(self):
        self.assertRejected({'a': [{'b': [{'c': '/Users/someone/project/x'}]}]}, 'depth 3')

    def test_forbidden_keys_still_rejected(self):
        for key in ('subjectResults', 'y_pred', 'embeddings'):
            self.assertRejected({key: []}, key)

    def test_nonfinite_metric(self):
        self.assertRejected({'y': float('nan')}, 'nan')


class ValidatePublicAccepts(unittest.TestCase):
    """The guard is deliberately broad, so the published vocabulary is pinned too."""

    def test_real_publication_prose_is_not_rejected(self):
        for note in [
            'Rest versus right-hand imagery; 5 participant-disjoint folds.',
            'OpenNeuro ds005342 v1.0.3, doi:10.18112/openneuro.ds005342.v1.0.3',
            '40 visual targets, 8 posterior electrodes, 70 subjects',
            'Braindecode BSD-3-Clause; MNE/scikit-learn BSD where used.',
            'Two seconds from the class annotation onset; 0.5-45 Hz filtering.',
            'P300 target versus nontarget events; 21 subjects; 19 channels',
            'https://physionet.org/content/eegmmidb/1.0.0/',
            'Frozen encoder + ridge head · 15 ch',
        ]:
            validate_public({'note': note})  # must not raise

    def test_published_snapshot_passes(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        snapshot = root / 'site' / 'src' / 'data' / 'mvp.json'
        if not snapshot.exists():
            self.skipTest('no built snapshot present')
        validate_public(json.loads(snapshot.read_text()))


class NewsReviewGate(unittest.TestCase):
    def test_unreviewed_item_raises(self):
        from export_snapshot import _reviewed
        with self.assertRaises(ValueError):
            _reviewed({'title': 'Unreviewed item'})
        with self.assertRaises(ValueError):
            _reviewed({'title': 'Explicitly false', 'reviewed': False})
        self.assertTrue(_reviewed({'title': 'ok', 'reviewed': True}))


if __name__ == '__main__':
    unittest.main()
