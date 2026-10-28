"""The Hugging Face card's citation.

The card is the mirror's front page, so the citation a reader copies from it has
to be the one the site and CITATION.cff ask for. It is generated from
CITATION.cff; these tests pin that it names the same release, title and site,
and that the BibTeX is the /api/ page's (same key and fields).
"""
import csv
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from build_hf_dataset import (PUBLISHED, build, card, citation_section, load_tables, release_20261028_section,
                              topic_payload)

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


class CardRouteTwo(unittest.TestCase):
    """The route-2 paragraph: its figures are the served export's, and BOAS travels with its three gaps and credit."""

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        text = ' '.join(card(snapshot, len(rows), topic_payload()).split())
        start = text.index('`shared-representation-update.json`')
        cls.r2 = text[start:text.index('catalogued methods have been scored', start)]
        cls.result = json.loads((PUBLISHED/'shared-representation-update.json').read_text())['results']['one-representation']

    def test_the_figures_are_the_exports(self):
        d = self.result['datasets']
        p1 = {(k, e['question']): e for k in ('openbmi', 'boas') for e in d[k]['entries'] if e['id'] == 'P1'}
        for key in (('openbmi', 'MI-A'), ('boas', 'SL-A')):
            e = p1[key]
            self.assertIn(f"{e['estimate_pp']:+.2f} pp [{e['interval_95_pp'][0]:+.2f}, {e['interval_95_pp'][1]:+.2f}]", self.r2)
        for k in ('openbmi', 'boas', 'eesm19'):
            self.assertIn(f"({d[k]['people']} people", self.r2)

    def test_boas_carries_its_gaps_and_credit(self):
        c = self.result['boas_conditions']
        self.assertEqual(len(c['gaps']), 3)
        for gap in c['gaps']:
            self.assertIn(' '.join(gap.split()), self.r2)
        self.assertIn(' '.join(c['attribution'].split()), self.r2)
        self.assertIn('pseudonymised in the public release', self.r2)
        self.assertNotIn('anonymous', self.r2)

    def test_no_ranking_and_no_language_claim(self):
        self.assertNotRegex(self.r2, r'\b(?:best|winner|outperform\w*|beats)\b')
        self.assertIn('not in language', self.r2)
        self.assertIn('supported on neither domain', self.r2)

    def test_the_lift_is_attributed_only_where_the_flags_show_it(self):
        # Review of 2026-10-07: an equivalence at a 2 pp margin cannot assign a 1.48 pp gain to the hidden layer on
        # motor imagery; B-sh - B-lin (S2) shows it on sleep and is inconclusive on motor imagery.
        self.assertNotIn('whatever lifts', self.r2)
        self.assertIn('On sleep B-sh carries the lift over B-lin; on motor imagery B-sh against B-lin was inconclusive.', self.r2)
        # The floor on next-epoch change and time of night is EEGNet's only.
        self.assertIn('at floor for the fixed heads on EEGNet', self.r2)



class CardBeyondScalpAndPilots(unittest.TestCase):
    """The two paragraphs of the 2026-10-12 site version (owner decisions): what each file holds, its credit and
    licence and its required caveats, read from the served export; no update date, version label or Jev; EEGPT's
    weights never called Apache-2.0; and the BINGO data management plan, internal evidence only, never cited."""

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        cls.card = card(snapshot, len(rows), topic_payload())
        text = ' '.join(cls.card.split())
        start = text.index('`beyond-scalp-update.json`')
        cls.beyond = text[start:text.index('`pilot-studies-update.json`', start)]
        start = text.index('`pilot-studies-update.json`:')
        cls.pilot = text[start:text.index('`eegpt-core-update.json`:', start)]
        cls.bs = json.loads((PUBLISHED/'beyond-scalp-update.json').read_text())
        cls.ps = json.loads((PUBLISHED/'pilot-studies-update.json').read_text())

    def test_credit_and_licence_from_the_served_file(self):
        for d in self.bs['datasets'].values():
            self.assertIn(d['rights']['license'], self.beyond)
            self.assertIn(' '.join(d['rights']['attribution'].split(' Derived analysis by BCI Report')[0].split()), self.beyond)
        for d in self.ps['datasets'].values():
            if d['publication'] == 'released':
                self.assertIn(' '.join(d['rights']['attribution'].split(' Derived analysis by BCI Report')[0].split()), self.pilot)
        self.assertIn('Neural Latents Benchmark', self.beyond)

    def test_required_caveats(self):
        for phrase in ('executed movement, not motor imagery', 'With one animal every figure is that animal', 'not an official Neural Latents',
                       'no classifier score', 'prepared, not scored', 'animal care and use committees'):
            self.assertIn(phrase, self.beyond)
        for phrase in ('outside every leaderboard', 'one cohort, counted once', 'neither arm is shown to be better, and the two are not shown to be equivalent',
                       'not subjective error recognition', 'not zero-shot', 'not excluded', 'no original or converted weights are distributed',
                       'core-matrix cells are in `eegpt-core-update.json`, below'):
            self.assertIn(phrase, self.pilot)
        c = self.ps['results']['orthosis-64ch-classical']['cohort']
        self.assertIn(f"({c['people']} people, {c['runs']} runs, {c['events']:,} recorded device events", self.pilot)

    def test_eegpt_weights_are_never_apache(self):
        self.assertIn('covers the repository’s source code only', self.pilot)
        self.assertNotRegex(self.pilot, r'(?i)(?:weights|checkpoint)[^.;]{0,40}Apache|Apache[^.;]{0,40}(?:weights|checkpoint)')

    def test_handwriting_as_the_owner_decided(self):
        if self.ps['datasets']['eeg-fnirs-handwriting']['publication'] != 'released':
            self.assertIn('handwriting dataset is held for its rights review, with no figure', self.pilot)
            return
        # Two controls carry the missingness mask, one of them with time as well; relative EEG is above both.
        for phrase in ('(5 people, four released coded labels)', 'above the missingness-mask and mask-plus-time controls',
                       'not separated from elapsed time and trial order', 'not handwriting recognition',
                       'No ethics-approval or informed-consent statement was found, on the dataset card or in a participating team\'s challenge paper',
                       'published with that gap stated, by the owner\'s decision'):
            self.assertIn(phrase, self.pilot)
        small = ' '.join(self.card.split())
        self.assertIn('its mask-only control\'s interval is not published, because its bounds would show individual people\'s scores', small)
        # The full statement belongs to the site's credits and data-use page; the card points to the gap once.
        self.assertEqual(self.pilot.count('No ethics-approval or informed-consent statement was found'), 1)
        self.assertNotIn('rechecked', self.pilot)
        self.assertNotIn('controls that see only which channels are missing', self.pilot)

    def test_bingo_as_the_owner_decided(self):
        if self.ps['datasets']['bingo-imagined-speech']['publication'] != 'released':
            self.assertIn('held for its rights, with no figure', self.pilot)
            return
        for phrase in ('The source states no licence', 'D3.1 (version 3.0)', 'NATO-alphabet recordings in the same laboratory',
                       'no ethics-approval reference is published', 'ASR, FORCe', 'not re-verified against the file'):
            self.assertIn(phrase, self.pilot)

    def test_no_dmp_no_date_no_version_label_no_jev(self):
        for section in (self.beyond, self.pilot):
            self.assertNotRegex(section, r'(?i)D1\.2|data management plan|download/374|confidential')
            self.assertNotRegex(section, r'\b20\d\d-\d\d-\d\d\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
            # A file name is not prose: `beyond-scalp-update.json` names the file.
            self.assertNotRegex(re.sub(r'`[^`]+`', '', section), r'(?<![./\w-])v\d+\b|\b(?:updated?|added|new)\b')
            self.assertNotIn('Jev', section)
        self.assertNotRegex(self.card, r'(?i)D1\.2|data management plan|download/374')


class CardEegptCore(unittest.TestCase):
    """The EEGPT paragraph (owner decisions of 2026-10-12 and 2026-10-13): what the file holds, read from the served
    export; the reading rule, never a ranking; the footnotes that travel with the cells; the sourced exposure statement,
    never a proof; the weights never called Apache-2.0 and none distributed; the pilot outside every leaderboard; no
    update date, version label or Jev; and the file ships beside the others."""

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        cls.card = card(snapshot, len(rows), topic_payload())
        text = ' '.join(cls.card.split())
        start = text.index('`eegpt-core-update.json`:')
        # The EEGPT paragraph alone: the 2026-10-20 and 2026-10-28 paragraphs follow it, and the second of those states
        # EEG-Captioner's and AXON's Apache-2.0 weight terms, which the rule below exists to keep away from EEGPT.
        cls.eegpt = text[start:text.index('`new-ssvep-frequencies-update.json`:', start)]
        cls.ec = json.loads((PUBLISHED/'eegpt-core-update.json').read_text())

    def test_what_the_file_holds(self):
        cells = {c['protocol']: c for c in self.ec['cells']}
        for phrase in ('EEGPT beside the core matrix', 'same runs as the published LaBraM rows and, except on idle, the CBraMod rows, with only the encoder swapped',
                       'published as computed, without a re-run', f"Its {len(cells)} core-matrix cells", f"({cells['idle']['people']} people)",
                       'pretraining-attribution rows on mi-rest and EEGMAT', 'mean of three random initialisations'):
            self.assertIn(phrase, self.eegpt)

    def test_reading_rule_and_caveats(self):
        for phrase in ('Kept apart from `results`, and not a ranking', 'only where their 95% intervals do not overlap',
                       'several of those gaps are narrow', 'four 0.25-second patches with no padding', 'never trained in pretraining',
                       'shorter than EEGPT\'s 4-second pretraining window', 'not the authors\' learnable spatial filter',
                       'not proof that a recording was never seen', 'Tsinghua benchmark', 'stays outside every leaderboard'):
            self.assertIn(phrase, self.eegpt)
        self.assertNotRegex(self.eegpt, r'(?i)\b(?:best|winner|state of the art|outperform\w*|beats?)\b')

    def test_weights_are_never_apache_and_none_distributed(self):
        self.assertIn('covers the repository’s source code only', self.eegpt)

    def test_scored_count_includes_methods_scored_outside_results(self):
        # EEGPT and REVE Base have rows, in their own exports: the next sentence must not say they were not run.
        text = ' '.join(self.card.split())
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        core = len({r['name'] for t in snapshot['tracks'] for r in t['rows']})
        self.assertIn(f"{core + 2} of {len(snapshot['models'])} catalogued methods have been scored ({core} in `results.csv`; "
                      'EEGPT in `eegpt-core-update.json` and REVE Base in `foundation-models-update.json`)', text)
        self.assertIn('A catalogued method with no row in any file has not been run', text)
        self.assertIn('no original or converted weights are distributed', self.eegpt)
        self.assertIn('no author endorsement is implied', self.eegpt)
        self.assertNotRegex(self.eegpt, r'(?i)(?:weights|checkpoint)[^.;]{0,40}Apache|Apache[^.;]{0,40}(?:weights|checkpoint)')

    def test_no_date_no_version_label_no_jev(self):
        self.assertNotRegex(self.eegpt, r'\b20\d\d-\d\d-\d\d\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
        self.assertNotRegex(re.sub(r'`[^`]+`', '', self.eegpt), r'(?<![./\w-])v\d+\b|\b(?:updated?|added|new)\b')
        self.assertNotIn('Jev', self.eegpt)

    def test_the_exposure_bullet_names_eegpt(self):
        text = ' '.join(self.card.split())
        self.assertIn('nor for EEGPT (checked 12 October 2026; in `eegpt-core-update.json`)', text)


def _pp(x):
    return f'{100 * x:+.2f}'


def _ppi(i):
    return f'[{100 * i[0]:+.2f}, {100 * i[1]:+.2f}]'


def _pct(x):
    return f'{100 * x:.2f}%'


def _pcti(i):
    return f'[{100 * i[0]:.2f}, {100 * i[1]:.2f}]'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CardRelease20261028(unittest.TestCase):
    """The 2026-10-28 release on the card (owner decisions D14-D29): one paragraph per batch of the day, in the release
    log's order; every figure, count, licence and credit is the served file's; the files ship as files and add no row to
    the merged CSVs; both dated register CSVs ship; the thread commenter is never named and the figure never appears
    (read through blocks_cca.REFUSED_TEXT and the NeuroRVQ export's token, no literal here); thread predictions stay on
    card 4 of the site (D23); nothing tied to ICLR 2027 (D4); no update date, version label or Jev."""

    FILES = ('ssvep-followups-update.json', 'neurorvq-update.json', 'eegmat-ten-second-update.json',
             'dataset-checks-update.json', 'open-register-20261028.csv')

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        cls.card = card(snapshot, len(rows), topic_payload())
        cls.section = release_20261028_section()
        cls.paragraphs = dict(zip(cls.FILES, cls.section.split('\n\n')))
        cls.flat = {k: ' '.join(v.split()) for k, v in cls.paragraphs.items()}
        cls.data = {n: json.loads((PUBLISHED/n).read_text()) for n in cls.FILES if n.endswith('.json')}

    def test_one_paragraph_per_batch_in_the_card(self):
        self.assertEqual(len(self.section.split('\n\n')), len(self.FILES))
        for name, text in self.paragraphs.items():
            self.assertTrue(text.startswith(f'`{name}`: **'), name)
        self.assertEqual(self.card.count(self.section), 1)
        flat = ' '.join(self.card.split())
        self.assertLess(flat.index('`open-register-20261020.csv`:'), flat.index('`ssvep-followups-update.json`:'))
        self.assertLess(flat.index('`open-register-20261028.csv`:'), flat.index('catalogued methods have been scored'))
        for name, d in self.data.items():
            self.assertTrue(d['release_id'].endswith('-20261028'), name)

    def test_the_files_ship_as_files_and_no_row_joins_the_merged_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = build(out)
            for name in self.FILES + ('open-register-20261020.csv', 'new-ssvep-frequencies-update.json'):
                self.assertEqual((out/name).read_bytes(), (PUBLISHED/name).read_bytes(), name)
            # The register's JSON, with its findings about other uploads, stays on bci.report (owner decision D3).
            self.assertFalse(list(out.glob('open-register-*.json')))
            _, rows = load_tables()
            self.assertEqual(result['rows'], len(rows))
            with (out/'results.csv').open() as fh:
                self.assertEqual(sum(1 for _ in csv.reader(fh)) - 1, len(rows))
            topics = topic_payload()
            with (out/'topics.csv').open() as fh:
                self.assertEqual(sum(1 for _ in csv.reader(fh)) - 1, len(topics['rows']))
            header = (out/'foundation-models.csv').read_text().splitlines()[0]
            self.assertEqual(header, (PUBLISHED/'foundation-models-sleep-scalp.csv').read_text().splitlines()[0])
            self.assertIn(self.section, (out/'README.md').read_text())
            configs = (out/'README.md').read_text().split('---')[1]
            self.assertEqual(configs.count('config_name:'), 5)

    def test_each_file_is_the_audited_one(self):
        review = PROJECT/'research/publication_review_20261028'
        for name in self.FILES[:4]:
            stem = name.removesuffix('-update.json')
            audit = json.loads((review/f'{stem}-export-audit.json').read_text())
            self.assertEqual(audit['status'], 'pass', name)
            self.assertEqual(_sha(PUBLISHED/name), audit['export_sha256'], name)
            self.assertEqual(_sha(review/f'{stem}-release-manifest.json'), audit['manifest_sha256'], name)
        reg = json.loads((review/'register/open-register-export-audit.json').read_text())
        self.assertEqual(_sha(PUBLISHED/'open-register-20261028.csv'), reg['csv_sha256'])
        self.assertEqual(_sha(PUBLISHED/'open-register-20261020.csv'), reg['previous_version']['csv_sha256'])
        self.assertEqual(_sha(PUBLISHED/'open-register-20261020.json'), reg['previous_version']['json_sha256'])
        # D28: the released SSVEP file keeps its bytes, and card 8's results replace its status entry.
        ssvep = json.loads((review/'ssvep-followups-export-audit.json').read_text())
        self.assertEqual(_sha(PUBLISHED/'new-ssvep-frequencies-update.json'), ssvep['released_file_sha256'])
        self.assertIn('kept byte for byte; card 8\'s results here replace the status entry it carries',
                      self.flat['ssvep-followups-update.json'])

    def test_figures_are_the_files(self):
        f = self.flat['ssvep-followups-update.json']
        ps = self.data['ssvep-followups-update.json']['studies']['practical_settings']
        level = ps['levels']['w500-c8/FBCCA-M3-N7-H5/u8']
        diff = ps['contrasts']['w500-c8/FBCCA-M3-N7-H5 minus w500-c8/CCA-RAW-H3/u8']
        self.assertIn(f"reached {_pct(level['estimate'])} {_pcti(level['interval'])} on the held-out 8-way task "
                      'with 2-second windows and eight electrodes, '
                      f"{_pp(diff['estimate'])} pp {_ppi(diff['interval'])} over CCA on the same windows", f)
        self.assertIn('(five Butterworth sub-bands)', f)
        self.assertIn('Bonferroni-adjusted 99.44% intervals over nine comparisons', f)
        self.assertIn('no other interval is adjusted', f)
        n = self.flat['neurorvq-update.json']
        for b in self.data['neurorvq-update.json']['blocks']:
            d = b['paired_difference']
            self.assertIn(f"({b['dataset']}, {b['cohort']['people']} people): {d['label']}, {_pp(d['difference'])} pp "
                          f"{_ppi(d['interval_95'])}; {d['reading']}.", n)
        t = self.flat['eegmat-ten-second-update.json']
        ts = self.data['eegmat-ten-second-update.json']
        diffs = [ts[k]['paired_difference'] for k in ('eeg_captioner', 'axon')]
        self.assertIn(', and '.join(f"{d['label']}, {_pp(d['difference'])} pp {_ppi(d['interval_95'])}" for d in diffs)
                      + f": for each, {diffs[0]['reading']}. {ts['source_annotation_qc']['beside_every_score']}", t)
        c = self.flat['dataset-checks-update.json']
        kim = self.data['dataset-checks-update.json']['kim2025-beta-range']['result']
        self.assertIn(f"mean participant accuracy of {_pct(kim['mean_participant_accuracy'])} "
                      f"{_pcti(kim['accuracy_interval_95'])} against a chance level of 2.5%", c)
        r = self.flat['open-register-20261028.csv']
        with (PUBLISHED/'open-register-20261028.csv').open() as fh:
            self.assertIn(f"**the open register's dataset ladder**, {sum(1 for _ in csv.DictReader(fh))} rows", r)

    def test_scores_held_and_licences_as_the_files_state(self):
        c = self.flat['dataset-checks-update.json']
        held = c[c.index('Damm finger motor imagery and NeBULA are status cases'):c.index('Licences:')]
        self.assertNotRegex(held, r'\d+(?:\.\d+)?\s*%|\bpp\b')
        self.assertIn('hold every score', held)
        # D15: MIND's two licence statements side by side, and the ScienceDB terms page stated as not read.
        self.assertIn('state CC BY 4.0; the MOABB adapter and the ScienceDB record page’s metadata state CC BY-NC 4.0', c)
        self.assertIn('terms-of-use page was not read', c)
        self.assertIn('The unit is the record ID', c)
        # Damm's rights gap stays beside its licence.
        self.assertIn('MIND as above. For Damm, the README cites a LICENSE file that the tree at the pinned commit does not '
                      'hold; the only licence statement is CC0 in dataset_description.json.', c)
        n = self.flat['neurorvq-update.json']
        # Exposure is a property of the datasets, each named or not in NeuroRVQ's published pretraining list.
        self.assertIn('Pretraining exposure is unknown for all three datasets: none is named', n)
        self.assertIn('CC BY-NC 4.0', n)
        self.assertIn('no weights distributed', n)
        self.assertNotIn('Apache', n)
        t = self.flat['eegmat-ten-second-update.json']
        for sentence in re.split(r'(?<=[.;])\s+', t):
            if 'Apache' in sentence:
                self.assertRegex(sentence, r'EEG-Captioner|AXON', sentence)
        self.assertIn('No weights distributed', t)
        # EEGPT's weights are never called Apache-2.0 anywhere on the card.
        for sentence in re.split(r'(?<=[.;])\s+', ' '.join(self.card.split())):
            if 'EEGPT' in sentence and 'Apache' in sentence:
                self.assertIn('source code only', sentence)

    def test_thread_rules(self):
        from ssvep_followups import blocks_cca
        from export_neurorvq_update import CONFIDENCE_TOKEN, HASH
        text = re.sub(r'https?://\S+', ' ', self.section)
        self.assertEqual({m.group(0).lower() for m in blocks_cca.REFUSED_TEXT.finditer(text)}, set())
        self.assertIsNone(CONFIDENCE_TOKEN.search(HASH.sub('', text)))
        hits = {m.group(0).lower() for m in blocks_cca.REFUSED_TEXT.finditer(re.sub(r'https?://\S+', ' ', self.card))}
        self.assertEqual(hits, set())
        # D23: thread predictions stay on card 4 of the site; the card names no thread, comment or prediction (card
        # 11's CPU components ran on one processor thread, the only thread it mentions).
        self.assertNotRegex(self.section.replace('on one thread', ''), r'(?i)\bbet\b|thread|comment|discussion')
        # A head's predictions may be named elsewhere (the ten-second Welch row reuses them); the SSVEP cards name none.
        self.assertNotRegex(self.paragraphs['ssvep-followups-update.json'], r'(?i)predict')

    def test_no_date_version_label_update_marker_jev_or_iclr(self):
        prose = re.sub(r'https?://\S+', ' ', re.sub(r'`[^`]+`', '', self.section))
        self.assertNotRegex(prose, r'\b20\d\d-\d\d-\d\d\b|\b(?:January|February|March|April|May|June|July|August|'
                                   r'September|October|November|December)\b')
        self.assertNotRegex(prose, r'(?<![./\w-])v\d+\b|\b(?:updated?|added|new|newly)\b')
        self.assertNotIn('Jev', prose)
        self.assertNotRegex(self.section, r'(?i)ICLR|submission|openreview')
        self.assertNotRegex(self.section, r'(?i)\b(?:best|winner|state of the art|outperform\w*|beats?|superior)\b')
        for path in ('/Users', '/home', '/Volumes', '/mnt', '/root', '/private'):
            self.assertNotIn(path, self.card)


class CardJevStyle(unittest.TestCase):
    """The "Jev-style evaluation" section (owner plan of 2026-10-07, tone of 2026-10-08): the site's one definition of
    "Jev-style" with TypeSafe's launch post linked, and nothing about what it is not; the plan started from the vision
    paper, cited as Yu & Yao, 2026, and never said to be where Jev comes from; links to the evidence page and the three
    routes, the tags "jev-style" and "decision-models" and never a jev-eeg name, one line to the Explorer Space, and no
    date."""

    @classmethod
    def setUpClass(cls):
        snapshot = json.loads((PUBLISHED/'experiments.json').read_text())
        _, rows = load_tables()
        cls.card = card(snapshot, len(rows), topic_payload())
        cls.text = ' '.join(cls.card.split())
        start = cls.text.index('## Jev-style evaluation')
        cls.section = cls.text[start:cls.text.index('## What this does not contain', start)]
        site = (PROJECT/'site/src/data/decision-research.ts').read_text()
        cls.site_definition = re.search(r"export const jevStyle = \{\n  en: '([^']+)'", site).group(1)

    def test_the_sites_definition_beside_the_name(self):
        self.assertIn('[TypeSafe’s Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)', self.section)
        plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', self.section)
        self.assertIn(self.site_definition, plain)
        self.assertEqual(plain.count('“Jev-style” here means'), 1)

    def test_nothing_defensive_and_no_wrong_origin(self):
        for phrase in ('affiliated', 'endorse', 'no contact', 'not an integration with Jev', 'not a Jev model',
                       'comes from a vision paper', 'pattern comes from', 'takes its interface from'):
            self.assertNotIn(phrase, self.section)
        self.assertIn('The research plan started from a vision paper that applies the same idea to images', self.section)

    def test_cites_yu_and_yao(self):
        self.assertIn('Yu & Yao, 2026 · Visual Jev: Accurate and Efficient Decisions from Shared Visual Context', self.section)
        self.assertIn('https://arxiv.org/abs/2609.25845', self.section)
        self.assertNotIn('Yu et al', self.card)

    def test_links_the_evidence_page_and_the_three_routes(self):
        for url in ('https://bci.report/jev-style/', 'https://bci.report/topics/when-not-to-act/#reliable-decisions',
                    'https://bci.report/topics/shared-encoder/', 'https://bci.report/topics/questions-in-language/'):
            self.assertIn(f'({url})', self.section)
        self.assertIn('mostly a negative result', self.section)

    def test_tags_and_no_jev_eeg_name(self):
        head = self.card.split('---')[1]
        self.assertIn('  - jev-style\n', head)
        self.assertIn('  - decision-models\n', head)
        self.assertNotRegex(self.card, r'(?i)jev-eeg')

    def test_explorer_space_line(self):
        self.assertEqual(self.card.count('https://huggingface.co/spaces/Twu31/bci-report-explorer'), 1)

    def test_no_date_or_version_label_in_the_section(self):
        self.assertNotRegex(self.section, r'20\d\d-\d\d-\d\d|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\bv\d+\b')
        # Yu & Yao, 2026 is the citation year; the arXiv id is a link target.
        self.assertNotRegex(self.section.replace('Yu & Yao, 2026', '').replace('2609.25845', ''), r'\d')


if __name__ == '__main__':
    unittest.main()
