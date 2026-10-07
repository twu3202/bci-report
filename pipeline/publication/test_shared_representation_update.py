"""Route 2, one representation and several questions: what must stay out, and what must follow from the pinned inputs."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import export_shared_representation_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
ROUTE = ex.ROUTE


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def set_at(files, source, value):
    """Write `value` at a candidate block's source pointer (a dict value updates the keys it names)."""
    name, _, pointer = source.partition('#')
    toks = [t.replace('~1', '/').replace('~0', '~') for t in pointer.split('/')[1:]]
    node = files[name]
    for t in toks[:-1]:
        node = node[int(t)] if isinstance(node, list) else node[t]
    last = int(toks[-1]) if isinstance(node, list) else toks[-1]
    if isinstance(value, dict) and isinstance(node[last], dict) and set(value) != {'source', 'value'}:
        node[last].update(copy.deepcopy(value))
    else:
        node[last] = copy.deepcopy(value)


def entry(cand, dataset, entry_id, question, level=None, kind='primary_entries'):
    for e in cand['results'][dataset][kind]:
        v = e['ref']['value']
        if v['id'] == entry_id and v['question'] == question and (level is None or v.get('level') == level):
            return e
    raise KeyError((dataset, entry_id, question, level))


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class SharedRepresentationBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, ref, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        ref.update(path=str(path), sha256=digest(data))
        return digest(data)

    def forged(self, candidate=None, both=None, files=None, aggregate=None, manifest=None, rebind=True):
        """A copy whose candidate (and pinned files) were edited, with every hash in the chain re-bound to the edit.

        `both(cand, sync)` edits a traced block of the candidate; `sync(block)` writes the block's edited value back
        into the file it points at, so re-resolution passes and the logic gates are what is exercised. `files(docs)`
        edits the pinned files themselves. The candidate, the consolidated aggregate, the aggregates, the audits and
        the handoff name each other by hash, so every hash is re-bound; `aggregate(doc)` edits the consolidated
        aggregate after its hashes were re-bound. Without `rebind` only the candidate is rewritten, so the manifest
        still pins the original bytes.
        """
        m = copy.deepcopy(MANIFEST)
        route = m['route']
        cand = load(route['releaseCandidate'])
        docs = {name: load(ex.ref_of(route, key)) for name, key in ex.PINNED.items()}
        handoff = (ex.PROJECT / route['handoff']['path']).read_text()
        if not rebind:
            if candidate:
                candidate(cand)
            pinned_sha = route['releaseCandidate']['sha256']
            self.write(route['releaseCandidate'], 'candidate.json', json.dumps(cand).encode())
            route['releaseCandidate']['sha256'] = pinned_sha     # the manifest still pins the original bytes
            return m
        if both:
            both(cand, lambda block: set_at(docs, block['source'], block['value']))
        if files:
            files(docs)
        swaps = {}

        def put(name):
            ref = ex.ref_of(route, ex.PINNED[name])
            old = ref['sha256']
            swaps[old] = self.write(ref, name, json.dumps(docs[name]).encode())
            cand['sources_sha256'][name] = swaps[old]
            return swaps[old]
        protocol = put('protocol.json')
        for name in ('aggregate.json', 'aggregate-primary.full.json', 'aggregate-secondary.full.json'):
            docs[name]['protocol_sha256'] = protocol
        for name in ('audit-primary.json', 'audit-secondary.json'):
            docs[name]['inputs']['protocol.json'] = protocol
        for name in ex.PINNED:
            if name not in ('protocol.json', 'aggregate.json'):
                docs['aggregate.json']['inputs_sha256'][name] = put(name)
        docs['aggregate.json']['inputs_sha256']['protocol.json'] = protocol
        if aggregate:
            aggregate(docs['aggregate.json'])
        put('aggregate.json')
        if candidate:          # last, so an edit to the hashes the candidate records is not re-bound away
            candidate(cand)
        old = route['releaseCandidate']['sha256']
        swaps[old] = self.write(route['releaseCandidate'], 'candidate.json', json.dumps(cand).encode())
        for a, b in swaps.items():
            handoff = handoff.replace(a, b)
        self.write(route['handoff'], 'handoff.md', handoff.encode())
        if manifest:
            manifest(m)
        return m

    # ------------------------------------------------------------------ the build itself
    def test_the_published_file_is_the_reviewed_build(self):
        data = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(audit['release_candidate_sha256'], MANIFEST['route']['releaseCandidate']['sha256'])

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helper_itself_builds(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged())
        build(self.forged(both=lambda c, sync: sync(entry(c, 'MI', 'P1', 'MI-A')['ref'])))

    def test_the_shape(self):
        p = build(MANIFEST)
        self.assertEqual(p['schema_version'], 'bci-report-shared-representation-update-v1')
        self.assertEqual(p['release_id'], 'shared-representation-update-20261007')
        self.assertEqual(list(p['results']), [ROUTE])
        self.assertEqual((p['status_only'], p['holds']), ([], []))
        r = p['results'][ROUTE]
        self.assertEqual(list(r['datasets']), ['openbmi', 'boas', 'eesm19'])
        self.assertEqual(p['provenance']['inputs'], ['openbmi', 'boas', 'eesm19'])
        self.assertEqual((p['provenance']['references_reresolved'], p['provenance']['references_bound_through_the_aggregate']),
                         (363, 5))
        primary = [e for d in r['datasets'].values() for e in d.get('entries', []) if e['role'] == 'primary']
        self.assertEqual(len(primary), 21)
        self.assertEqual(sorted(e['id'] for e in primary), sorted(['P1'] * 5 + ['P2'] * 5 + ['P3'] + ['P4'] * 5 + ['P5'] * 5))
        self.assertEqual(len(r['datasets']['boas']['e2_sleep']['entries']), 9)
        self.assertEqual(len(r['datasets']['eesm19']['secondary']), 6)

    # ------------------------------------------------------------------ the figures the pages will print
    def test_the_handoff_figures(self):
        r = build(MANIFEST)['results'][ROUTE]
        mi, boas = r['datasets']['openbmi'], r['datasets']['boas']
        pp = lambda e: (round(e['estimate_pp'], 2), [round(x, 2) for x in e['interval_95_pp']])
        p1 = {e['question']: e for e in mi['entries'] if e['id'] == 'P1'}
        self.assertEqual(pp(p1['MI-A']), (1.48, [0.09, 2.89]))
        self.assertEqual((p1['MI-A']['difference'], p1['MI-A']['margin']), ('difference: C1 higher', 'margin not met'))
        self.assertEqual(p1['MI-B']['margin'], 'equivalent within delta')
        self.assertEqual(mi['route_sentence']['sentence'], 'The fixed-heads sentence is not supported')
        self.assertEqual(mi['route_sentence']['fixed_heads_lower_on'], ['parameters', 'head_macs'])
        # Sleep: only SL-A counted; SL-E and SL-F at floor; the whole SL-A interval above +2 pp.
        rs = boas['route_sentence']
        self.assertEqual((rs['counted'], rs['excluded']), (['SL-A'], {'SL-E': 'floor', 'SL-F': 'floor'}))
        self.assertEqual(rs['fixed_heads_lower_on'], ['parameters', 'head_macs', 'step_time'])
        sl = next(e for e in boas['entries'] if e['id'] == 'P1' and e['question'] == 'SL-A')
        self.assertEqual(pp(sl), (6.96, [4.92, 9.09]))
        self.assertGreater(sl['interval_95_pp'][0], ex.DELTA)
        p3 = next(e for e in boas['entries'] if e['id'] == 'P3')
        self.assertEqual((round(p3['log_r'], 3), round(p3['r'], 3)), (-0.380, 0.684))
        self.assertEqual(p3['margin'], 'margin not met')
        # P2 at E1 on MI-B: sharing a small trunk cost accuracy; its sentence carries the label at E1.
        p2 = next(e for e in mi['entries'] if e['id'] == 'P2' and e['question'] == 'MI-B')
        self.assertEqual((p2['difference'], p2['sentences_derived_by_audit']), ('difference: A higher', ['sharing costs accuracy on q']))
        # Floor-gated entries are reported and never counted.
        for e in [*mi['entries'], *boas['entries']]:
            if e['gate'] == 'floor' and e['role'] == 'primary':
                self.assertEqual(e['sentences_derived_by_audit'], [])
        # E2 sleep: every gate passes on the E2 B-lin arm; one seed; the disclosure travels with it.
        e2 = boas['e2_sleep']
        self.assertTrue(all(g['gate'] == 'pass' for g in e2['gates']) and all(e['single_seed'] for e in e2['entries']))
        self.assertTrue(e2['run_after_other_results'] and 'after every other primary and secondary result' in e2['disclosure'])
        self.assertEqual(e2['resume_checkpoints']['left_after_the_run'], 0)
        # S2 at Level 1 is labelled as computed by the audit; every secondary entry carries a gate and who attached it.
        s2 = [e for d in (mi, boas) for e in d['secondary'] if e['id'] == 'S2' and e['level'] == 'L1']
        self.assertEqual(len(s2), 5)
        self.assertTrue(all('independent secondary audit' in e['computed_by'] for e in s2))
        for d in (mi, boas, r['datasets']['eesm19']):
            for e in [*d['secondary'], *d.get('e2_sleep', {}).get('entries', [])]:
                self.assertIn('gate', e)
                self.assertTrue(e.get('gate_attached_by'), e['id'])

    # ------------------------------------------------------------------ the chain of custody
    def test_a_changed_input_byte_is_refused(self):
        keys = ['handoff', 'releaseCandidate', 'aggregate', 'aggregatePrimary', 'aggregateSecondary', 'auditExtract',
                'protocol', 'boasRightsReview', 'boasRightsReviewText']
        for key in keys + [('independentAudits', k) for k in ('primary', 'secondary', 'e2Sleep')]:
            m = copy.deepcopy(MANIFEST)
            ex.ref_of(m['route'], key)['sha256'] = '0' * 64
            with self.assertRaises(ValueError, msg=str(key)):
                build(m)

    def test_an_edited_candidate_the_manifest_did_not_pin_is_refused(self):
        def nudge(c):
            entry(c, 'MI', 'P1', 'MI-A')['ref']['value']['estimate_pp'] += 0.01
        with self.assertRaisesRegex(ValueError, 'release candidate'):
            build(self.forged(candidate=nudge, rebind=False))

    def test_a_candidate_figure_that_is_not_its_source_is_refused(self):
        def nudge(c):
            entry(c, 'BOAS', 'P1', 'SL-A')['ref']['value']['ci95_pp'][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'differs from aggregate-primary'):
            build(self.forged(candidate=nudge))
        def gap(c):
            c['boas_requirements']['gaps_to_state_on_any_page']['value'][0] = 'Consent covered sharing.'
        with self.assertRaisesRegex(ValueError, 'differs from boas-rights-review'):
            build(self.forged(candidate=gap))
        def nested(c, sync):   # the aggregate's own reference into the protocol must still hold
            block = c['multiplicity']
            block['value']['value'] = block['value']['value'].replace('one in 20', 'one in 50')
            sync(block)
        with self.assertRaisesRegex(ValueError, 'differs from protocol.json'):
            build(self.forged(both=nested))

    def test_the_candidate_and_the_aggregate_must_name_the_pinned_files(self):
        with self.assertRaisesRegex(ValueError, 'the candidate names another aggregate-primary'):
            build(self.forged(candidate=lambda c: c['sources_sha256'].update({'aggregate-primary.full.json': '0' * 64})))
        with self.assertRaisesRegex(ValueError, 'the aggregate names another audit-e2-sleep'):
            build(self.forged(aggregate=lambda a: a['inputs_sha256'].update({'audit-e2-sleep.json': '0' * 64})))
        with self.assertRaisesRegex(ValueError, 'another run'):
            build(self.forged(candidate=lambda c: c.update(run_id='decision-route2-v1/20261007')))
        with self.assertRaisesRegex(ValueError, 'audit-secondary.json names another run'):
            build(self.forged(files=lambda d: d['audit-secondary.json'].update(run_id='decision-route2-v1/20261005')))

    def test_the_audits_must_pass(self):
        def fail(name, edit):
            return self.forged(files=lambda d: edit(d[name]))
        def verdict(c, sync):   # the candidate and the audit file both say fail
            block = c['audits']['primary']['verdict']
            block['value'] = 'fail'
            sync(block)
        with self.assertRaisesRegex(ValueError, 'the independent primary audit did not pass'):
            build(self.forged(both=verdict))
        with self.assertRaisesRegex(ValueError, 'failed a check'):
            build(fail('audit-secondary.json', lambda a: a['checks']['provenance'].update({'pass': False})))
        with self.assertRaisesRegex(ValueError, 'found a mismatch'):
            build(fail('audit-primary.json', lambda a: a['checks']['metrics_contrasts_intervals_verdicts_recomputed']
                       ['detail'].update(mismatches_float32=['E1/P1/MI-A'])))
        with self.assertRaisesRegex(ValueError, 'an audit check did not pass'):
            build(fail('audit-e2-sleep.json', lambda a: a['checks'].update(
                {next(k for k in a['checks'] if k.startswith('no_checkpoint_left')): False})))
        with self.assertRaisesRegex(ValueError, 'a resume checkpoint was left'):
            build(fail('audit-e2-sleep.json', lambda a: next(v for v in a['results']['checkpoints'].values()
                                                             if isinstance(v, dict) and 'content_hits' in v)['content_hits'].append('x')))
        with self.assertRaisesRegex(ValueError, 'the run condition was not met'):
            build(fail('audit-e2-sleep.json', lambda a: a['results']['design_fixed_at_freeze'].update(
                projection_primary_gpu_hours=6.5)))

    def test_the_approval_is_on_record(self):
        for edit in (lambda m: m['approval'].update(decision='hold'), lambda m: m['approval'].update(date='2026-10-06'),
                     lambda m: m['approval'].update(candidateStatusAtSeal='approved'),
                     lambda m: m['approval']['ownerDecisions'].pop(1)):
            m = copy.deepcopy(MANIFEST)
            edit(m)
            with self.assertRaises(ValueError):
                build(m)
        with self.assertRaisesRegex(ValueError, 'state it was sealed in'):
            build(self.forged(candidate=lambda c: c.update(status='approved')))

    # ------------------------------------------------------------------ BOAS: the owner's conditions
    def test_boas_needs_the_owner_approved_review(self):
        with self.assertRaisesRegex(ValueError, 'not approved by the owner'):
            build(self.forged(files=lambda d: d['boas-rights-review.json'].update(status='recommendation')))
        def withdrawn(c, sync):
            block = c['boas_requirements']['review']
            block['value']['given'] = False
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not approved by the owner'):
            build(self.forged(both=withdrawn))

    def test_boas_carries_the_three_gaps_and_the_attribution(self):
        m = copy.deepcopy(MANIFEST)
        m['sources'][1]['rightsReview']['gaps'] = m['sources'][1]['rightsReview']['gaps'][:2]
        with self.assertRaisesRegex(ValueError, 'three gaps'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][1]['attribution'] = 'Bitbrain · BOAS.'
        with self.assertRaisesRegex(ValueError, 'attribution'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][1]['rightsReview']['participants'] = 'anonymous'
        with self.assertRaisesRegex(ValueError, 'participants wording'):
            build(m)
        r = build(MANIFEST)['results'][ROUTE]
        self.assertEqual(r['boas_conditions']['gaps'], r['datasets']['boas']['rights']['gaps'])
        self.assertEqual(len(r['boas_conditions']['gaps']), 3)
        self.assertEqual(r['boas_conditions']['attribution'], r['datasets']['boas']['rights']['attribution'])

    def test_the_boas_privacy_review_is_the_draft_with_route_2s_clause(self):
        m = copy.deepcopy(MANIFEST)
        rec = m['sources'][1]
        rec['privacyReview'] = rec['privacyReview'].replace('log R with its interval,', 'counts of people above or below zero,')
        with self.assertRaisesRegex(ValueError, 'a figure route 2 does not produce'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][1]['privacyReview'] = m['sources'][1]['privacyReview'].replace('no peer-reviewed paper', 'a paper')
        with self.assertRaisesRegex(ValueError, 'not the reviewed draft'):
            build(m)

    def test_no_boas_cell_under_20_people(self):
        def small(c, sync):
            e = entry(c, 'BOAS', 'S4-SL-D', 'SL-D', kind='secondary_entries')
            e['ref']['value']['included_people'] = 19
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'a cell of 19 people'):
            build(self.forged(both=small))

    # ------------------------------------------------------------------ the logic gates
    def test_the_flags_follow_the_interval(self):
        def diff(c, sync):
            e = entry(c, 'MI', 'P1', 'MI-B')
            e['ref']['value']['difference_flag'] = 'difference: C1 higher'
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'the difference flag'):
            build(self.forged(both=diff))
        def margin(c, sync):
            e = entry(c, 'BOAS', 'P5', 'SL-A')
            e['ref']['value']['margin_flag'] = 'equivalent within delta'
            e['ref']['value']['wording'] = 'no difference shown; equivalent within delta'
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'the margin flag'):
            build(self.forged(both=margin))
        def word(c, sync):
            e = entry(c, 'MI', 'P2', 'MI-A')
            e['ref']['value']['wording'] = 'no difference shown; margin not met'
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'the wording'):
            build(self.forged(both=word))
        def lower_rule(c, sync):   # S10 is judged on its lower bound: an upper-bound reading is refused
            e = [x for x in c['results']['BOAS']['secondary_entries'] if x['ref']['value']['id'] == 'S10'
                 and x['ref']['value']['x'] == 'C1(K-all)' and x['ref']['value']['question'] == 'SL-A'][0]
            e['ref']['value']['margin_flag'] = 'margin not met'
            e['ref']['value']['wording'] = 'difference: K-all higher; margin not met'
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'the margin flag'):
            build(self.forged(both=lower_rule))

    def test_a_contrast_is_the_difference_of_its_arms(self):
        def drift(c, sync):
            e = entry(c, 'BOAS', 'P2', 'SL-A')
            e['ref']['value']['mean_ba']['B-lin'] += 0.001
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'not the difference of its arms'):
            build(self.forged(both=drift))
        def seeds(c, sync):
            e = entry(c, 'MI', 'P5', 'MI-B')
            e['ref']['value']['per_seed'][0]['point'] += 0.3
            e['ref']['value']['per_seed'][0]['hi'] += 0.3
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'the seeds do not average'):
            build(self.forged(both=seeds))
        def ratio(c, sync):
            e = entry(c, 'BOAS', 'P3', 'SL-B')
            e['ref']['value']['R'] = 0.7
            sync(e['ref'])
        with self.assertRaisesRegex(ValueError, 'ratio of remaining errors'):
            build(self.forged(both=ratio))

    def test_the_gate_follows_the_arm(self):
        def lift(c, sync):
            g = c['results']['BOAS']['gates']['E1/sleep/SL-E']
            g['value']['gate'] = 'pass'
            sync(g)
        with self.assertRaisesRegex(ValueError, 'the gate does not follow'):
            build(self.forged(both=lift))
        def e2(c, sync):
            e = entry(c, 'BOAS', 'S3-P1', 'SL-E', kind='secondary_entries')
            e['ref']['value']['gate'] = 'floor'
            e['gate_label']['value']['gate'] = 'floor'
            sync(e['ref'])
            sync(e['gate_label'])
        with self.assertRaisesRegex(ValueError, "not the E2 B-lin arm"):
            build(self.forged(both=e2))
        def provenance(c, sync):
            e = entry(c, 'MI', 'S7', 'MI-A', kind='secondary_entries')
            e['gate_label']['value']['by'] = 'the write-up'
            sync(e['gate_label'])
        with self.assertRaisesRegex(ValueError, 'unknown gate provenance'):
            build(self.forged(both=provenance))

    def test_the_route_sentence_follows_its_questions_and_the_ledger(self):
        def count_floor(c, sync):
            rs = c['results']['BOAS']['route_sentence']
            rs['value']['counted'] = ['SL-A', 'SL-E']
            sync(rs)
        with self.assertRaisesRegex(ValueError, 'counted questions'):
            build(self.forged(both=count_floor))
        def slower(c, sync):   # C1's step time within 1.2x of B-lin's: no longer a sleep ledger item
            led = c['results']['BOAS']['cost_ledger_E1']
            led['value']['C1']['step_seconds'] = led['value']['B-lin']['step_seconds'] * 1.1
            sync(led)
        with self.assertRaisesRegex(ValueError, 'for less'):
            build(self.forged(both=slower))
        def supported(c, sync):
            rs = c['results']['MI']['route_sentence']
            rs['value']['sentence'] = 'Fixed heads did as well for less'
            sync(rs)
        with self.assertRaisesRegex(ValueError, 'sentence does not follow'):
            build(self.forged(both=supported))
        def sentence(c, sync):
            d = c['results']['BOAS']['per_question_sentences_derived_by_audit']['E1/sleep/P2/SL-E']
            d['value']['stated'] = list(d['value']['sentences_if_counted'])
            sync(d)
        with self.assertRaisesRegex(ValueError, "audit's sentences"):
            build(self.forged(both=sentence))

    def test_the_rights_are_the_released_records(self):
        for i, key, value in ((0, 'attribution', 'Someone else'), (0, 'license', 'CC-BY-4.0'), (2, 'version', '1.0.3'),
                              (2, 'reviewBasis', [])):
            m = copy.deepcopy(MANIFEST)
            m['sources'][i][key] = value
            with self.assertRaises(ValueError, msg=key):
                build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][0]['privacyReview'] = 'Aggregate only.'
        with self.assertRaisesRegex(ValueError, 'privacy review'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][2]['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(m)

    # ------------------------------------------------------------------ what stays out
    def test_per_person_fields_are_refused_by_key(self):
        for key in ('p10', 'p50_pp', 'per_person_value', 'per_person_contrast_percentiles', 'steps_per_fold',
                    'gpu_seconds_per_fit', 'compute_time', 'pilot_sd', 'median_window_channel_sd_uv', 'age', 'sex',
                    'bmi', 'pid', 'splits', 'participant_id', 'predictions', 'probabilities', 'discrepancies',
                    'elapsed_seconds', 'primary_gpu_hours_guard'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('/Volumes/disk/x', '/Users/someone/x', 'host:/mnt/bigdata', 'host:~/Projects', 'sub-07',
                     'boas-epochs250.npy', 'stage0-report.private', 'DECISIONS.md entry', 'pid 89'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_per_person_percentiles_stay_out_by_value(self):
        payload = build(MANIFEST)
        cand = load(MANIFEST['route']['releaseCandidate'])
        withheld = set(ex.withheld_values(cand))
        self.assertEqual(len(withheld), 30)
        self.assertFalse(withheld & set(ex.numbers(payload)))

        def leak(c, sync):   # a published estimate that happens to be one person's percentile
            item = c['computed_not_proposed_for_site'][0]['ref']
            item['value']['E1/MI/P1/MI-A']['p50_pp'] = entry(c, 'MI', 'P1', 'MI-A')['ref']['value']['estimate_pp']
            sync(item)
        with self.assertRaisesRegex(ValueError, 'per-person value reached the export'):
            build(self.forged(both=leak))

    def test_no_not_published_item_withholds_what_the_file_carries(self):
        p = build(MANIFEST)
        result = p['results'][ROUTE]
        ex.check_not_published(result, p['not_published'])
        for edit in (lambda r: r['datasets']['openbmi']['entries'][0].update(per_fold=[1, 2]),
                     lambda r: r['datasets']['openbmi']['entries'][0].update(p50_pp=1.0),
                     lambda r: r['datasets']['boas']['canary'].update(pilot_sd=0.1),
                     lambda r: r['datasets']['boas']['secondary'][0].update(included_people=12),
                     lambda r: r['datasets']['boas'].update(recording_dates=['2023']),
                     lambda r: r['datasets']['boas']['ledger']['B-lin'].update(gpu_hours=1.0),
                     lambda r: r['audits'].update(discrepancies=['D-1']),
                     lambda r: r['boas_conditions'].update(filter='EDF start years 2022 to 2024'),
                     lambda r: r.update(key_findings=['x'])):
            forged = copy.deepcopy(result)
            edit(forged)
            with self.assertRaisesRegex(ValueError, 'not_published: the file carries'):
                ex.check_not_published(forged, p['not_published'])

    def test_a_not_published_item_without_a_check_is_refused(self):
        p = build(MANIFEST)
        result = p['results'][ROUTE]
        items = [x if not x.startswith('Measured compute time') else 'Compute time: GPU-hours.' for x in p['not_published']]
        with self.assertRaisesRegex(ValueError, 'no check for the item'):
            ex.check_not_published(result, items)
        with self.assertRaisesRegex(ValueError, 'missing or named twice'):
            ex.check_not_published(result, p['not_published'][:-1])
        m = copy.deepcopy(MANIFEST)
        m['notPublished'] = items
        with self.assertRaisesRegex(ValueError, 'no check for the item'):
            build(m)

    def test_the_e1_sharing_boundary_states_what_was_run(self):
        r = build(MANIFEST)['results'][ROUTE]
        b = [x for x in r['boundaries']['protocol'] if 'small-CNN trunk sharing' in x]
        self.assertEqual(len(b), 1)
        self.assertNotIn('unless', b[0])
        self.assertTrue(b[0].endswith(ex.E2_MI_OUTCOME))

        def reword(c, sync):
            block = c['boundaries']['protocol']
            block['value'][5] = block['value'][5].replace('unless', 'if')
            sync(block)
        with self.assertRaisesRegex(ValueError, 'the E1 sharing boundary changed'):
            build(self.forged(both=reword))

    def test_no_private_path_or_identifier_reaches_the_files(self):
        text = json.dumps(build(MANIFEST), ensure_ascii=False)
        # Path roots only: naming this operator's machines or volumes here would itself be the leak.
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', '.npy', '.private', 'DECISIONS.md',
                      'run-log', 'splits.json'):
            self.assertNotIn(token, text)
        self.assertIsNone(ex.PRIVATE_TOKENS.search(text))
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '.private'):
                self.assertNotIn(token, body, f'{path.name}: {token}')


if __name__ == '__main__':
    unittest.main()
