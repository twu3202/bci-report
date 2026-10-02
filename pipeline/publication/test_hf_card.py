"""The Hugging Face card's citation.

The card is the mirror's front page, so the citation a reader copies from it has
to be the one the site and CITATION.cff ask for. It is generated from
CITATION.cff; these tests pin that it names the same release, title and site,
and that the BibTeX is the /api/ page's (same key and fields).
"""
import re
import unittest
from pathlib import Path

from build_hf_dataset import citation_section

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


if __name__ == '__main__':
    unittest.main()
