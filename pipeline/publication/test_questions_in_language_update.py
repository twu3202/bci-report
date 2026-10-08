"""The route-3 release, questions in language: what must stay out, and what must follow from the audited files."""
import copy
import hashlib
import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_questions_in_language_export as au
import export_questions_in_language_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
ROUTE = MANIFEST['route']
R = 'questions-in-language'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def entries(payload):
    return [e for b in payload['results'][R]['primary']['blocks'] for e in b['entries']]


def by_label(payload, block, label):
    b = next(b for b in payload['results'][R]['primary']['blocks'] if b['block'] == block)
    return next(e for e in b['entries'] if e['label'] == label)


def pp(e):
    return round(100 * e['estimate'], 2), [round(100 * x, 2) for x in e['interval_95']]


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class QuestionsInLanguageBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.wordings = build(MANIFEST)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        return {'path': str(path), 'sha256': digest(data)}

    def forged(self, edit):
        """The release candidate edited, and the handoff re-bound to its new hash: only the export's own checks
        stand between the edit and the served file."""
        manifest = copy.deepcopy(MANIFEST)
        route = manifest['route']
        candidate = load(route['releaseCandidate'])
        edit(candidate)
        ref = self.write('candidate.json', json.dumps(candidate, ensure_ascii=False).encode())
        handoff = (ex.PROJECT / route['handoff']['path']).read_text().replace(route['releaseCandidate']['sha256'],
                                                                              ref['sha256'])
        route['releaseCandidate'] = ref
        route['handoff'] = self.write('handoff.md', handoff.encode())
        return manifest

    # ------------------------------------------------------------------ the build itself
    def test_the_published_files_are_the_reviewed_build(self):
        data, wording_data = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        for out in ex.WORDING_OUTPUTS:
            self.assertEqual(out.read_bytes(), wording_data)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['wordings_sha256'], digest(wording_data))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(audit, au.audit(), 'the recorded audit is the one the auditor writes for these bytes')

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helper_itself_builds(self):
        build(self.forged(lambda c: None))     # an unedited forged copy passes, so failures below are the edits'

    def test_the_shape(self):
        p, w = self.payload, self.wordings
        self.assertEqual((p['schema_version'], p['release_id']),
                         ('bci-report-questions-in-language-update-v1', 'questions-in-language-update-20261008'))
        self.assertEqual(w['schema_version'], 'bci-report-questions-in-language-wordings-v1')
        self.assertEqual(w['release_id'], p['release_id'])
        self.assertEqual(list(p['results']), [R])
        self.assertEqual(list(p['datasets']), ['beta', 'boas', 'eesm19', 'openbmi', 'wearable-ssvep-102'])
        self.assertEqual([p['status_only'], p['holds']], [[], []])
        r = p['results'][R]
        self.assertEqual([b['block'] for b in r['primary']['blocks']], ['P-ssvep-L0', 'P-ssvep-L1', 'P-sleep-L1'])
        self.assertEqual(len(entries(p)), 35)
        self.assertEqual(sum(len(x.get('entries', [])) for x in r['secondary']['parts'].values()), 105)
        self.assertEqual(p['provenance']['release_candidate_sha256'], ROUTE['releaseCandidate']['sha256'])
        self.assertEqual(w['provenance']['wording_lists_sha256'],
                         'b903f4f49138aefdba9385e82d5288f58eccc24ab228d9b45ab5bd53bf63912a')

    # ------------------------------------------------------------------ the figures the pages print
    def test_the_seen_and_reworded_figures(self):
        p = self.payload
        e = by_label(p, 'P-ssvep-L0', 'TPL - ID, seen task (32-way), training-wording score')
        self.assertEqual(pp(e), (-5.96, [-6.84, -5.08]))
        self.assertEqual((e['difference'], e['margin'], e['rule'], e['kind']),
                         ('difference: reference higher', 'margin not met', 1, 'seen'))
        e = by_label(p, 'P-sleep-L1', 'TPL - ID, seen task (5-way), training-wording score')
        self.assertEqual(pp(e), (-0.05, [-0.70, 0.61]))
        self.assertEqual((e['difference'], e['margin'], e['rule'], e['people']),
                         ('no difference shown', 'equivalent within the margin', 4, 100))
        e = by_label(p, 'P-sleep-L1', 'DESC(a3) - DESC(train), seen task')
        self.assertEqual((pp(e), e['kind']), ((-20.87, [-29.49, -13.71]), 'rewording'))
        e = by_label(p, 'P-ssvep-L1', 'TPL(a2) - TPL(train), seen task')
        self.assertEqual((e['margin'], e['rule']), ('equivalent within the margin', 2))

    def test_the_unseen_figures(self):
        p = self.payload
        r_ = [e['r'] for e in entries(p) if e['id'] == 'P3']
        self.assertEqual(len(r_), 8)
        self.assertEqual(round(min(x['estimate'] for x in r_), 2), 2.42)
        self.assertEqual(round(max(x['estimate'] for x in r_), 2), 33.80)
        for e in entries(p):
            if e['id'] == 'P3':
                self.assertTrue(math.isclose(e['r']['estimate'], math.exp(e['estimate']), rel_tol=1e-12))
                self.assertEqual((e['difference'], e['margin'], e['unit']),
                                 ('difference: the read-off leaves less error', 'margin not met', 'log R'))
        e = by_label(p, 'P-ssvep-L0', 'TPL - CCA, 8-way unseen')
        self.assertEqual(pp(e), (-52.21, [-55.13, -48.99]))
        e = by_label(p, 'P-ssvep-L1', 'TPL - NUM, neighbour 3-way')
        self.assertEqual((e['difference'], e['margin']), ('difference: language arm higher', 'not applicable (difference only)'))
        self.assertIn('frequency and stimulus phase', e['sentence'])
        e = by_label(p, 'P-sleep-L1', 'TPL - SHUF unseen AUROC, mean of the explicit cells')
        self.assertEqual((round(e['estimate'], 3), e['unit']), (0.629, 'difference of AUROC'))
        lv = p['results'][R]['descriptive']['P-sleep-L1']['levels']
        self.assertEqual(round(lv['TPL unseen asleep implicit AUROC']['estimate'], 3), 0.317)
        self.assertEqual(round(lv['TPL unseen light implicit AUROC']['estimate'], 3), 0.244)

    def test_every_unseen_sentence_says_unseen_by_the_head(self):
        for e in entries(self.payload):
            self.assertIs(ex.UNSEEN in e['sentence'], e['kind'] == 'unseen', e['key'])
            self.assertNotIn('did no difference shown', e['sentence'])

    def test_rewording_and_unseen_are_never_pooled(self):
        r = self.payload['results'][R]
        self.assertEqual(list(r['route_answer']), ['rule', 'seen_training_wording_P1', 'rewording_P2', 'unseen_P3_P4_P5'])
        kinds = {e['id']: e['kind'] for e in entries(self.payload)}
        self.assertEqual(kinds, {'P1': 'seen', 'P2': 'rewording', 'P3': 'unseen', 'P4': 'unseen', 'P5': 'unseen'})

    # ------------------------------------------------------------------ flags, rules and gates
    def test_flags_and_rules_follow_from_the_interval(self):
        self.assertEqual(ex.flags('pp', -0.019, 0.019, 'x'), ('no difference shown', 'equivalent within the margin'))
        self.assertEqual(ex.flags('pp', -0.019, -0.001, 'x'), ('difference: reference higher', 'equivalent within the margin'))
        self.assertEqual(ex.flags('pp', -0.019, 0.03, 'x'), ('no difference shown', 'non-inferior'))
        self.assertEqual(ex.flags('pp', -0.03, 0.01, 'x'), ('no difference shown', 'margin not met'))
        self.assertEqual(ex.flags('log_r', 0.05, 0.11, 'x'),
                         ('difference: the read-off leaves less error', 'equivalent within the margin'))
        self.assertEqual(ex.flags('log_r', 0.05, 0.3, 'x'), ('difference: the read-off leaves less error', 'margin not met'))
        self.assertEqual(ex.flags('auroc_difference_only', 0.6, 0.65, 'x'),
                         ('difference: language arm higher', 'not applicable (difference only)'))
        self.assertEqual(ex.rule_of('no difference shown', 'margin not met', False), 6)
        self.assertEqual(ex.rule_of('difference: reference higher', 'non-inferior', False), 2)
        self.assertEqual(ex.rule_of('no difference shown', 'not applicable (difference only)', True), -1)

    def entry(self, **change):
        b = load(ROUTE['releaseCandidate'])['results']['primary']['blocks'][2]['value']
        wrapper = copy.deepcopy(b['entries'][0])
        wrapper['value'].update(change.pop('value', {}))
        wrapper.update(change)
        return wrapper, b['gates']['value']

    def test_an_entry_whose_flags_or_rule_do_not_follow_is_refused(self):
        wrapper, gates = self.entry()
        ex.entry_of(wrapper, 'k', 'k', gates, 20)
        wrapper, gates = self.entry(value={'margin': 'non-inferior'})
        with self.assertRaisesRegex(ValueError, 'do not follow from the interval'):
            ex.entry_of(wrapper, 'k', 'k', gates, 20)
        wrapper, gates = self.entry(value={'rule': 5})
        with self.assertRaisesRegex(ValueError, 'the flags give 4'):
            ex.entry_of(wrapper, 'k', 'k', gates, 20)
        wrapper, gates = self.entry(value={'lo': 0.001})
        with self.assertRaisesRegex(ValueError, 'does not contain its point'):
            ex.entry_of(wrapper, 'k', 'k', gates, 20)
        wrapper, gates = self.entry(gate={'gate': 'headroom', 'label': 'pass'})
        with self.assertRaisesRegex(ValueError, 'gated otherwise'):
            ex.entry_of(wrapper, 'k', 'k', gates, 20)

    def test_a_boas_cell_under_20_people_is_refused(self):
        wrapper, gates = self.entry(value={'people': 19})
        with self.assertRaisesRegex(ValueError, 'a cell of 19 people'):
            ex.entry_of(wrapper, 'k', 'k', gates, 20)
        with self.assertRaisesRegex(ValueError, 'a BOAS figure without its n'):
            list(ex.boas_people({'parts': {'x': {'boas': True, 'rows': {'a': {'estimate': 0.1}}}}}))
        r = self.payload['results'][R]
        self.assertEqual(min(ex.boas_people(r)), 71)
        self.assertEqual(self.payload['boas_conditions']['smallest_cell_people'], 71)

    def test_an_unseen_sentence_without_its_phrase_is_refused(self):
        b = load(ROUTE['releaseCandidate'])['results']['primary']['blocks'][2]['value']
        wrapper = copy.deepcopy(b['entries'][5])
        wrapper['value']['sentence'] = wrapper['sentence_display'] = wrapper['value']['sentence'].replace(
            ' (unseen by the EEG head, not by the text encoder)', '')
        with self.assertRaisesRegex(ValueError, 'unseen by the EEG head'):
            ex.entry_of(wrapper, 'k', 'k', b['gates']['value'], 20)

    # ------------------------------------------------------------------ chains
    def test_a_changed_input_byte_is_refused(self):
        for key in (('aggregate',), ('aggregatePrimary',), ('protocol',), ('stage0Report',),
                    ('independentAudits', 'secondaryNumeric'), ('boasScopeExtension',), ('referenceCheck',)):
            manifest = copy.deepcopy(MANIFEST)
            ref = manifest['route']
            for k in key[:-1]:
                ref = ref[k]
            raw = bytearray((ex.PROJECT / ref[key[-1]]['path']).read_bytes())
            raw[-2:-1] = b' '
            ref[key[-1]]['path'] = str(Path(self.tmp.name) / ('x-' + '-'.join(key)))
            Path(ref[key[-1]]['path']).write_bytes(bytes(raw))
            with self.assertRaisesRegex(ValueError, 'pinned', msg=key):
                build(manifest)

    def test_a_candidate_value_that_is_not_the_aggregates_is_refused(self):
        def edit(c):
            c['results']['primary']['blocks'][0]['value']['entries'][0]['value']['point'] += 1e-12
        with self.assertRaisesRegex(ValueError, 'the value differs from aggregate'):
            build(self.forged(edit))

    def test_the_candidate_must_be_in_its_sealed_state(self):
        with self.assertRaisesRegex(ValueError, 'sealed'):
            build(self.forged(lambda c: c.update(status='approved')))

    def test_a_headline_numeral_from_nowhere_is_refused(self):
        def edit(c):
            c['key_findings'][0]['en'] = c['key_findings'][0]['en'].replace('-0.05 pp', '-123.45 pp')
        with self.assertRaisesRegex(ValueError, 'numerals in no pinned text or figure'):
            build(self.forged(edit))

    def test_the_approval_must_be_recorded(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['approval']['ownerDecisions'] = manifest['approval']['ownerDecisions'][:-1]
        with self.assertRaisesRegex(ValueError, 'owner decisions'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['approval']['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(manifest)

    def test_a_reference_must_be_the_checked_one(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['references'][0]['cite'] = 'Yu et al., 2026 · Visual Jev'
        with self.assertRaisesRegex(ValueError, 'Yu & Yao'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['references'][2]['cite'] = manifest['references'][2]['cite'].replace('Frequency Recognition', 'Frequency Detection')
        with self.assertRaisesRegex(ValueError, 'not the checked one'):
            build(manifest)

    def test_rights_must_be_the_released_records(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['sources'][0]['license'] = 'CC0-1.0'
        with self.assertRaisesRegex(ValueError, 'differs from the released record'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['sources'][1]['attribution'] += ' Endorsed.'
        with self.assertRaises(ValueError):
            build(manifest)

    # ------------------------------------------------------------------ what stays out
    def test_refused_fields(self):
        for key in ('per_person', 'median', 'p90', 'percentile_95', 'per_fold_values', 'fold', 'per_frequency',
                    'interior_only', 'beta_by_cohort_and_frequency', 'training_balanced_accuracy', 'mc_se',
                    'replicates_above_chance', 'by_configuration', 'D', 'gpu_hours', 'wall_seconds', 'ledger',
                    'nearest_training_wording_cosine', 'discrepancies', 'predictions', 'value'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})

    def test_refused_text(self):
        for text in ('/Users/someone/x', '/mnt/bigdata/run', 'on trx50', 'Gal4 mirror', 'see DECISIONS.md S0b-6',
                     'RUN_ROOT/stage1', 'stage2/primary.private.json', 'anonymous participants', 'Yu et al., 2026',
                     'a Jev model', 'updated 8 October 2026', 'Added 2026-10-08: x', 'since 2026-10-01',
                     'run on 2026-10-04', 'the v9 rows', 'in this update', 'sub-07',
                     # the sealed build's Jev wording, and defensive or wrong-origin text of any kind (owner, 2026-10-08)
                     ex.SEALED_JEV_SCOPE, ex.SEALED_INDEPENDENCE, ex.SEALED_ORIGIN_NOTE,
                     'BCI Report is not affiliated with TypeSafe.', 'We had no contact with the authors.',
                     'TypeSafe does not endorse these results.', 'This is not an integration with Jev.',
                     'The pattern comes from a vision paper (Yu & Yao, 2026).',
                     'The interface is taken directly from Visual Jev.', 'Visual Jev introduced the pattern.',
                     '本站与 TypeSafe 没有关联。', '这个模式来自一篇视觉论文。'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        for text in (ex.JEV_STYLE['en'], ex.JEV_STYLE['zh'], ex.VISUAL_JEV, ex.TYPESAFE_JEV['url'], ex.ORIGIN_NOTE,
                     ex.REFERENCE_ROLE, 'Figshare 12264401 v3; mirror',
                     'OpenNeuro ds005555, version 1.1.3', 'bge-small-en-v1.5', 'revision 5 passed',
                     'the owner overrode that on 2026-10-08', 'added to the release in version 1.1.1 (May 2025)'):
            ex.scrub_check({'results': {'x': {'note': text}}})

    def test_no_s10_breakdown_and_no_check_value_reaches_the_files(self):
        agg, s0 = load(ROUTE['aggregate']), load(ROUTE['stage0Report'])
        withheld = ex.withheld_values(agg, s0)
        self.assertGreater(len(withheld), 4000)
        keys = set(ex.all_keys(self.payload)) | set(ex.all_keys(self.wordings))
        self.assertFalse([k for k in keys if re.search(r'per_frequency|interior|by_cohort_and_frequency|s10_break', k)])
        # Every published figure equal to a withheld value is an audited figure with the same value, never the S10
        # or check value itself: the triviality canaries' scores, a fit-check score and a canary D are absent.
        published = set(ex.figure_numbers(self.payload))
        for v in (0.0403125, 0.3684, 0.3663):
            self.assertNotIn(v, published)
        r = self.payload['results'][R]['pre_run_checks']
        self.assertEqual(set(r['gates']['triviality']['BETA']), {'pass', 'threshold', 'training_people', 'origin'})
        self.assertNotIn('S10 per frequency', json.dumps(self.payload))

    def test_the_check_on_not_published_items(self):
        p = copy.deepcopy(self.payload)
        p['results'][R]['secondary']['parts']['S1']['descriptive'] = {}
        with self.assertRaisesRegex(ValueError, 'carries what the item says it leaves out'):
            ex.check_not_published(p, self.wordings, p['not_published'])
        p = copy.deepcopy(self.payload)
        p['results'][R]['interior_only'] = {}
        with self.assertRaisesRegex(ValueError, 'carries what the item says it leaves out'):
            ex.check_not_published(p, self.wordings, p['not_published'])
        with self.assertRaisesRegex(ValueError, 'no check for the item'):
            ex.check_not_published(self.payload, self.wordings, self.payload['not_published'] + ['Something else.'])

    def test_no_private_path_or_identifier_reaches_the_files(self):
        for doc in (self.payload, self.wordings):
            text = json.dumps(doc, ensure_ascii=False)
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', 'trx50', 'Gal4', 'DECISIONS.md', '.private',
                          'RUN_ROOT', 'research/decision_route3', '.npz'):
                self.assertNotIn(token, text)
            self.assertIsNone(re.search(r'\bsub-\d', text))
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', 'trx50'):
                self.assertNotIn(token, body, f'{path.name}: {token}')

    # ------------------------------------------------------------------ disclosures and scope
    def test_the_required_disclosures(self):
        r = self.payload['results'][R]
        self.assertEqual([d['id'] for d in r['required_disclosures']],
                         ['revision-3-failed', 'revision-4-failed', 'revision-5-passed', 'owner-override',
                          'centring-diagnostic-not-run', 'revision-5-direction-counts', 'decision-s0b6', 'ea-1',
                          'numeracy-not-activated', 'multiplicity', 'secondary-single-seed-likely-inconclusive'])
        c = r['pre_run_checks']['canaries']
        self.assertEqual([c['revision_3']['pass'], c['revision_4']['pass'], c['revision_5']['pass']], [False, False, True])
        self.assertEqual(c['revision_5']['single_head_intervals_excluding_exact_chance'], {'above': 66, 'below': 59, 'total': 125})
        self.assertEqual(c['revision_5']['cells_with_single_head_failures_in_both_directions'], 18)
        self.assertIn('overrode', r['pre_run_checks']['owner_override'])
        self.assertIn('not run', r['pre_run_checks']['centring_diagnostic'])
        self.assertIs(r['pre_run_checks']['numeracy_probe']['activated'], False)
        self.assertTrue(r['design']['multiplicity'].startswith('35 pre-declared comparisons, not corrected for multiplicity'))
        self.assertEqual(r['secondary']['expected_inconclusive'], ['every EESM19 entry', 'every single-seed S entry'])
        self.assertTrue(all(p['declared_likely_inconclusive'] for p in r['secondary']['parts'].values()
                            if p.get('single_seed') is True))

    # ------------------------------------------------------------------ Jev (owner feedback, 2026-10-08)
    def test_no_defensive_or_wrong_origin_text_in_the_served_files(self):
        """Read from the served bytes, with patterns written here (check-workbench's tone rules for the pages), not
        the export's: no scope sentence, no independence line, nothing defensive beside Jev, and no sentence that gives
        Jev or its pattern to the vision paper."""
        defensive = [r'not affiliated|unaffiliated|no affiliation', r'\bno contact\b',
                     r'endorse[^.。]*\b(?:Jev|TypeSafe|Yu|Yao)\b|\b(?:Jev|TypeSafe)\b[^.。]*endorse',
                     r'not an integration|not a Jev model|Jev model that reads EEG|independent and not',
                     r'没有接入 Jev|能读 EEG 的 Jev 模型|与 Jev 的作者|(?:Jev|TypeSafe)[^。]*(?:没有关联|有过联系|认可|背书)'
                     r'|(?:没有关联|有过联系|认可|背书)[^。]*(?:Jev|TypeSafe)']
        paper = r'Visual Jev|vision paper|视觉论文|Yu & Yao'
        origin = (r'\b(?:comes?|came) from\b|\btak(?:es|en|ing)\b[^.]{0,60}\bfrom\b|\bborrow|\boriginat|\bintroduc|'
                  r'\bcoin(?:s|ed)\b|\binvent|\bprompted\b|\bsource of\b|\bpattern the roadmap names\b|'
                  r'interface pattern from|来自|借来|源自|源于|提出了? ?Jev|促成')
        site = (ex.PROJECT / 'site/src/data/decision-research.ts').read_text()
        m = re.search(r"export const jevStyle = \{\s*en: '([^']+)',\s*zh: '([^']+)',", site)
        source = re.search(r"export const typesafeJev = \{ company: '([^']+)', url: '([^']+)' \}", site)
        self.assertTrue(m and source, 'the site\'s definition and source')
        for path in ex.OUTPUTS + ex.WORDING_OUTPUTS:
            doc = json.loads(path.read_bytes())
            for trail, text in ex.strings(doc):
                for pattern in defensive:
                    self.assertIsNone(re.search(pattern, text, re.IGNORECASE), f'{path.name} {trail}: {pattern}')
                flat = text.replace(ex.VISUAL_JEV, 'Visual Jev')
                for sentence in re.split(r'(?<=[.。!?！？])\s*', flat):
                    if re.search(paper, sentence):
                        self.assertIsNone(re.search(origin, sentence), f'{path.name} {trail}: “{sentence}”')
                if 'jev' in text.lower():      # Jev only in the definition, its source, and the Visual Jev lines
                    self.assertTrue(text in (m.group(1), m.group(2), source.group(2)) or text.startswith(ex.VISUAL_JEV)
                                    or text.startswith('The decision-research plan started from Visual Jev'), trail)
        served = json.loads(ex.OUTPUTS[1].read_bytes())
        route = served['results'][R]['route']
        self.assertEqual(list(route), ['site_text', 'boundary', 'origin', 'jev_style', 'jev_source'])
        self.assertEqual(route['jev_style'], {'en': m.group(1), 'zh': m.group(2)}, 'the site\'s one definition')
        self.assertEqual(route['jev_source'], {'company': source.group(1), 'url': source.group(2)})
        self.assertEqual(route['jev_source']['url'], 'https://typesafe.ai/blog/introducing-system-one-models-and-jev')
        self.assertEqual(route['origin'], {'cite': ex.VISUAL_JEV, 'url': 'https://arxiv.org/abs/2609.25845',
                                           'arxiv': '2609.25845', 'note': ex.ORIGIN_NOTE})
        self.assertIn('started from Visual Jev', route['origin']['note'])
        self.assertIn('applies the same encode-once, answer-many idea to images', route['origin']['note'])
        self.assertEqual(served['results'][R]['references'][0]['role'], ex.REFERENCE_ROLE)
        body = ex.OUTPUTS[1].read_text()
        for gone in ('jev_scope', '"independence": "BCI Report', 'not affiliated', 'no endorsement', 'Yu et al',
                     'interface pattern', 'jev-eeg'):
            self.assertNotIn(gone, body)
        self.assertEqual(self.payload['results'], served['results'], 'the build is what is served')

    def test_the_declared_text_edits(self):
        record = MANIFEST['declaredTextEdits']
        self.assertEqual(record['date'], '2026-10-08')
        self.assertIn('Owner feedback, 2026-10-08', record['reason'])
        for phrase in ('TypeSafe AI', 'https://typesafe.ai/blog/introducing-system-one-models-and-jev',
                       'arXiv:2609.25845', 'started from it', 'jevStyle', 'end of /jev-style/'):
            self.assertIn(phrase, record['reason'])
        self.assertEqual(record['sealedExport'], {
            'note': record['sealedExport']['note'],
            'resultsSha256': 'f320bf25de03e6905d0d9a2d640997d5ad7c70b4af585ed488569461e7c610b4',
            'wordingsSha256': '70ad2e4c7089516b065955166e3e6d75c89416b8fa3b8600b79ec1e4fc65f0eb',
            'manifestSha256': '27d9c391c7362d5305b29fe8163a0870e912dc0443f5451b6fc5ead24cdc6eba'})
        # Exactly these six, in this order, and the manifest records exactly what the export applies.
        p = f'/results/{R}'
        self.assertEqual([(e['op'], e['path']) for e in record['edits']],
                         [('replace', f'{p}/route/origin/note'), ('remove', f'{p}/route/jev_scope'),
                          ('remove', f'{p}/route/independence'), ('add', f'{p}/route/jev_style'),
                          ('add', f'{p}/route/jev_source'), ('replace', f'{p}/references/0/role')])
        self.assertEqual(record['edits'], ex.edit_records())
        self.assertEqual([e.get('before') for e in record['edits']],
                         [ex.SEALED_ORIGIN_NOTE, ex.SEALED_JEV_SCOPE, ex.SEALED_INDEPENDENCE, None, None, ex.SEALED_ROLE])
        self.assertEqual(load(ROUTE['releaseCandidate'])['route_origin']['note'], ex.SEALED_ORIGIN_NOTE)
        self.assertEqual(MANIFEST['references'][0]['role'], ex.SEALED_ROLE)
        self.assertTrue(all(ex.text_only(e[k]) for e in record['edits'] for k in ('before', 'after') if k in e))
        # The audit record: six edits, undone to the sealed bytes of both files.
        audit = json.loads(ex.EXPORT_AUDIT.read_text())['declared_text_edits']
        self.assertEqual((audit['edits'], audit['replaced'], audit['removed'], audit['added'],
                          audit['undone_equals_sealed_bytes']), (6, 2, 2, 2, True))

    def test_the_export_refuses_an_undeclared_or_unmatched_text_edit(self):
        manifest = copy.deepcopy(MANIFEST)              # the record differs from what the export applies
        manifest['declaredTextEdits']['edits'][0]['after'] += ' More.'
        with self.assertRaisesRegex(ValueError, 'records other text edits'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['declaredTextEdits']['edits'].pop()
        with self.assertRaisesRegex(ValueError, 'records other text edits'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        del manifest['declaredTextEdits']
        with self.assertRaisesRegex(ValueError, 'does not record the owner'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)              # a reference role that is not the sealed one
        manifest['references'][0]['role'] = 'the vision paper'
        with self.assertRaisesRegex(ValueError, 'does not apply'):
            build(manifest)

        def note(c):                                     # a candidate note that is not the sealed one
            c['route_origin']['note'] = 'a vision paper'
        with self.assertRaisesRegex(ValueError, 'does not apply'):
            build(self.forged(note))
        with mock.patch.object(ex, 'JEV_STYLE', {'en': ex.JEV_STYLE['en'] + ' x', 'zh': ex.JEV_STYLE['zh']}), \
                self.assertRaisesRegex(ValueError, 'not the one the site prints'):
            ex.owner_edits({}, {'declaredTextEdits': {'date': '2026-10-08', 'reason': 'Owner feedback',
                                                      'edits': ex.edit_records()}})

    def test_boas_travels_with_its_conditions(self):
        b = self.payload['boas_conditions']
        self.assertEqual(len(b['gaps']), 3)
        self.assertEqual(len(b['gaps_zh']), 3)
        self.assertEqual(b['participants'], 'pseudonymised in the public release')
        self.assertIn("Bitbrain's headband", b['not_an_evaluation_of'])
        self.assertEqual(b['attribution'], self.payload['datasets']['boas']['attribution'])
        self.assertEqual(b['minimum_cell_people'], 20)

    def test_the_wordings_file(self):
        w = self.wordings
        self.assertEqual((w['license'], w['texts']), ('CC BY 4.0', 787))
        data = (json.dumps(w['lists'], indent=2, ensure_ascii=False) + '\n').encode()
        self.assertEqual(digest(data), 'b903f4f49138aefdba9385e82d5288f58eccc24ab228d9b45ab5bd53bf63912a')
        self.assertEqual(sorted(f for r in w['held_out_partition_hz'].values() for f in r), w['frequency_grid_hz'])
        self.assertEqual(len(w['derangements']['ssvep_s10_by_rotation_and_seed_index']), 15)

    # ------------------------------------------------------------------ the independent audit
    def served(self, edit):
        payload = json.loads(ex.OUTPUTS[0].read_bytes())
        edit(payload)
        data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
        paths = []
        for i in range(2):
            p = Path(self.tmp.name) / f'served-{i}.json'
            p.write_bytes(data)
            paths.append(p)
        return mock.patch.object(au, 'SERVED', tuple(paths))

    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            p['results'][R]['primary']['blocks'][2]['entries'][3]['estimate'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'estimate'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['results'][R]['descriptive']['P-sleep-L1']['levels']['ID seen_ba']['p90'] = 0.81
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['results'][R]['secondary']['parts']['S12']['by_sensor']['wet']['TPL - NUM (12-way)']['people']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_wrong_flag(self):
        def edit(p):
            p['results'][R]['primary']['blocks'][1]['entries'][3]['margin'] = 'margin not met'
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'flags'):
            au.audit()

    def test_the_audit_catches_a_boas_figure_without_its_n(self):
        def edit(p):
            p['results'][R]['secondary']['parts']['S6']['cells']['not N3']['negated_wording_auroc']['people'] = 19
        with self.served(edit), self.assertRaises(au.AuditFailure):
            au.audit()

    def test_the_audit_catches_a_withheld_value(self):
        agg = load(ROUTE['aggregate'])
        value = agg['s10_breakdowns']['value']['levels']['L0']['interior_only']['levels']['TPL u8']['point']

        def edit(p):
            p['results'][R]['descriptive']['P-ssvep-L0']['levels']['TPL u8']['estimate'] = value
        with self.served(edit), self.assertRaises(au.AuditFailure):
            au.audit()

    # ------------------------------------------------------------------ the audit and the declared text edits
    def test_the_audit_accepts_exactly_the_declared_text_edits(self):
        result = au.audit()['declared_text_edits']
        self.assertEqual((result['edits'], result['undone_equals_sealed_bytes']), (6, True))
        with self.served(lambda p: None):                # the served bytes, re-serialised: still the sealed export
            au.audit()

    def test_the_audit_rejects_an_undeclared_text_change(self):
        r = lambda p: p['results'][R]
        changes = {
            'a limitation reworded': lambda p: r(p)['limitations'].__setitem__(0, r(p)['limitations'][0] + ' Also.'),
            'a route sentence reworded': lambda p: r(p)['primary']['blocks'][0]['entries'][0].update(
                sentence=r(p)['primary']['blocks'][0]['entries'][0]['sentence'] + ' Clearly.'),
            'the independence line back': lambda p: r(p)['route'].update(independence=ex.SEALED_INDEPENDENCE),
            'a scope sentence beside the definition': lambda p: r(p)['route']['jev_style'].update(
                note='This is not an integration with Jev.'),
            'a dataset attribution': lambda p: p['datasets']['beta'].update(attribution='BETA.'),
            'a boolean flipped': lambda p: r(p)['pre_run_checks']['numeracy_probe'].update(activated=True),
            'a key renamed': lambda p: r(p)['route'].update(origin={'cite': r(p)['route']['origin']['cite'],
                                                                     'url': r(p)['route']['origin']['url'],
                                                                     'arxiv_id': '2609.25845',
                                                                     'note': r(p)['route']['origin']['note']}),
            'the release candidate\'s hash': lambda p: p['provenance'].update(release_candidate_sha256='0' * 64),
        }
        for what, change in changes.items():
            with self.subTest(what), self.served(change), self.assertRaisesRegex(au.AuditFailure, 'release candidate|'
                                                                                 'undeclared change|declared'):
                au.audit()
        # A declared edit that is not what is served: the sealed text back, or the new text changed.
        for change in (lambda p: r(p)['route']['origin'].update(note=ex.SEALED_ORIGIN_NOTE),
                       lambda p: r(p)['route']['jev_style'].update(en=ex.JEV_STYLE['en'].replace('once', 'twice')),
                       lambda p: r(p)['references'][0].update(role=ex.SEALED_ROLE)):
            with self.served(change), self.assertRaisesRegex(au.AuditFailure, 'not the declared edit'):
                au.audit()
        with self.served(lambda p: r(p)['route'].update(jev_scope=ex.SEALED_JEV_SCOPE)), \
                self.assertRaisesRegex(au.AuditFailure, 'declared removal is still served'):
            au.audit()

    def test_the_audit_refuses_a_declared_edit_that_is_not_text(self):
        """A manifest that declares a figure as a "text edit", or an edit outside the result, is refused even with
        the served file built to match it."""
        for bad in ({'op': 'replace', 'path': f'/results/{R}/primary/entries_count', 'before': 35, 'after': 36},
                    {'op': 'replace', 'path': '/scope', 'before': 'x', 'after': 'y'},
                    {'op': 'add', 'path': f'/results/{R}/route/extra', 'after': {'n': 1}}):
            manifest = copy.deepcopy(MANIFEST)
            manifest['declaredTextEdits']['edits'].append(bad)
            data = json.dumps(manifest, ensure_ascii=False).encode()
            path = Path(self.tmp.name) / 'manifest.json'
            path.write_bytes(data)
            w = json.loads(ex.WORDING_OUTPUTS[0].read_bytes())
            w['provenance']['manifest_sha256'] = digest(data)
            wpath = Path(self.tmp.name) / 'wordings.json'
            wpath.write_bytes((json.dumps(w, indent=2, ensure_ascii=False) + '\n').encode())
            with mock.patch.object(au, 'MANIFEST', path), mock.patch.object(au, 'SERVED_WORDINGS', (wpath, wpath)), \
                    self.served(lambda p: p['provenance'].update(manifest_sha256=digest(data))), \
                    self.assertRaisesRegex(au.AuditFailure, 'not text|outside the result'):
                au.audit()


if __name__ == '__main__':
    unittest.main()
