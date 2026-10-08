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
                     'run on 2026-10-04', 'the v9 rows', 'in this update', 'sub-07'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        for text in (ex.JEV_SCOPE, ex.VISUAL_JEV, ex.INDEPENDENCE, 'Figshare 12264401 v3; mirror',
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

    def test_jev_appears_only_with_its_scope(self):
        r = self.payload['results'][R]
        self.assertEqual(r['route']['origin']['cite'], ex.VISUAL_JEV)
        self.assertIn('not an integration with Jev and not a Jev model that reads EEG', r['route']['jev_scope'])
        self.assertIn('not affiliated with the Jev authors', r['route']['independence'])
        for trail, text in ex.strings(self.payload):
            if 'jev' in text.lower():
                self.assertTrue('not an integration with Jev' in text or text.startswith(ex.VISUAL_JEV)
                                or 'not affiliated with the Jev authors' in text, trail)
        self.assertNotIn('Yu et al', json.dumps(self.payload))
        self.assertNotIn('jev-eeg', json.dumps(self.payload).lower())

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


if __name__ == '__main__':
    unittest.main()
