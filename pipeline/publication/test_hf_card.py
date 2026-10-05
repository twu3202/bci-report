"""The Hugging Face card's citation.

The card is the mirror's front page, so the citation a reader copies from it has
to be the one the site and CITATION.cff ask for. It is generated from
CITATION.cff; these tests pin that it names the same release, title and site,
and that the BibTeX is the /api/ page's (same key and fields).
"""
import json
import re
import unittest
from pathlib import Path

from build_hf_dataset import PUBLISHED, card, citation_section, load_tables, topic_payload

PROJECT = Path(__file__).resolve().parents[2]


class CardCitation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cff_text = (PROJECT/'CITATION.cff').read_text()
        cls.section = citation_section()

    def cff(self, key):
        return re.search(rf'^{key}: "?([^"\n]+)"?$', self.cff_text, re.MULTILINE).group(1)

    def test_names_the_release_citation_cff_names(self):
        self.assertIn(f"`{self.cff('version')}` ({self.cff('date-released')})", self.section)
        self.assertIn(f"note         = {{Release {self.cff('version')}}}", self.section)

    def test_bibtex_matches_the_api_page_shape(self):
        bibtex = re.search(r'```bibtex\n(.*?)\n```', self.section, re.DOTALL).group(1)
        self.assertTrue(bibtex.startswith('@misc{bcireport,'))
        self.assertIn(f"title        = {{{self.cff('title')}}}", bibtex)
        self.assertIn('author       = {{BCI Report}}', bibtex)
        self.assertIn(f"year         = {{{self.cff('date-released')[:4]}}}", bibtex)
        self.assertIn(f"howpublished = {{\\url{{{self.cff('url')}}}}}", bibtex)
        self.assertIn(f"doi          = {{{self.cff('doi')}}}", bibtex)
        self.assertEqual(bibtex.count('{'), bibtex.count('}'), 'unbalanced braces')

    def test_sends_readers_to_the_upstream_credit(self):
        self.assertIn('upstream dataset', self.section)
        self.assertIn('/datasets/', self.section)


class CardLtrsvpWording(unittest.TestCase):
    """The LTRSVP paragraph: run b is a later recording only within a rate.

    Across rates the original study presented the rates in ascending,
    non-randomised order, and how the released files map onto it is not
    documented, so the card must not call the cross-rate test recording later.
    """

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        cls.text = ' '.join(card(snapshot, len(rows), topic_payload()).split())
        start = cls.text.index('And LTRSVP')
        cls.ltrsvp = cls.text[start:cls.text.index('image rate**', start)]

    def test_later_only_within_a_rate(self):
        for sentence in re.split(r'(?<=[.;])\s+', self.text):
            if re.search(r'\blater\b[^.;]*\brecording|\bfollowed run a\b', sentence):
                self.assertRegex(sentence, r'[Ww]ithin (?:a|each|one) rate', sentence)

    def test_states_the_known_order(self):
        for phrase in ('from the lowest to the highest', 'not randomised', 'not documented',
                       'elapsed time, fatigue and practice', '**not a causal effect of'):
            self.assertIn(phrase, self.ltrsvp)



class CardFoundationWording(unittest.TestCase):
    """The v9 paragraph: interval facts, never a ranking where intervals overlap (review of 2026-10-05).

    On BETA standard CCA's interval overlaps EEGNet's and an eeg-fm-masking checkpoint's, so the card says no new
    row lies above it, never that it stays highest or is the best row; exposure is what the authors' lists show.
    """

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        text = ' '.join(card(snapshot, len(rows), topic_payload()).split())
        start = text.index('eleven further EEG foundation models')
        cls.v9 = text[start:text.index('Timings came from a shared GPU', start)]

    def test_no_ranking_word(self):
        self.assertNotRegex(self.v9, r'\b(?:best|highest row|stays highest|top|winner|outperform\w*)\b')
        self.assertIn('no new row lies above standard CCA', self.v9)

    def test_exposure_is_the_authors_lists(self):
        self.assertNotIn('was pretrained on', self.v9)
        self.assertIn("BETA is in ST-EEGFormer's published pretraining list", self.v9)


class CardRouteOneFigures(unittest.TestCase):
    """The route-1 paragraph's figures are typed into the card: each must be the served export's (review of 2026-10-05)."""

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        text = ' '.join(card(snapshot, len(rows), topic_payload()).split())
        start = text.index('`reliable-decisions-update.json`')
        cls.r1 = text[start:text.index('Every contrast', start)]
        cls.result = json.loads((PUBLISHED/'reliable-decisions-update.json').read_text())['results']['reliable-decisions']

    def test_cohorts_and_coverages_are_the_exports(self):
        eegmat, beta = self.result['protocols']['arithmetic-rest'], self.result['protocols']['beta-8ch']
        self.assertIn(f'two LaBraM arms on EEGMAT ({eegmat["people"]} people)', self.r1)
        self.assertIn(f'EEGNet on BETA ({beta["people"]} people)', self.r1)
        cov = {m['id']: f'{100 * m["fixed_cutoff"]["coverage"]:.1f}%' for m in beta['methods']}
        stated = re.search(r'accepted (\d+\.\d%) of BETA trials for one method and (\d+\.\d%) for another', self.r1)
        self.assertIsNotNone(stated)
        self.assertEqual([stated[1], stated[2]], [cov['cca'], cov['cbramod']])
        self.assertEqual(max(cov.values(), key=lambda v: float(v[:-1])), stated[1])
        self.assertEqual(min(cov.values(), key=lambda v: float(v[:-1])), stated[2])

    def test_the_claims_follow_from_the_export(self):
        protocols = self.result['protocols'].values()
        # "The learned reject option erred less than the calibrated confidence for no method."
        self.assertIn('erred less than the calibrated confidence for no method', self.r1)
        self.assertFalse([m['id'] for p in protocols for m in p['methods']
                          if m['learned_minus_confidence']['error_at_80']['excludes_zero']
                          and m['learned_minus_confidence']['error_at_80']['mean'] < 0])
        # "The certified risk accepted nothing on EEGMAT", and on BETA some certified folds exceeded their target.
        self.assertIn('The certified risk accepted nothing on EEGMAT', self.r1)
        self.assertTrue(all(m['risk_certification']['accepted'] == 0
                            for m in self.result['protocols']['arithmetic-rest']['methods']))
        self.assertTrue(any(m['risk_certification']['folds_over_target'] > 0
                            for m in self.result['protocols']['beta-8ch']['methods']))


if __name__ == '__main__':
    unittest.main()
