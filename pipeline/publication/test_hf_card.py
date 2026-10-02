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


if __name__ == '__main__':
    unittest.main()
