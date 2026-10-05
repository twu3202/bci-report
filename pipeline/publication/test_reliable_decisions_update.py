"""Route 1, reliable decisions: what must stay out, and what must follow from the pinned release candidate."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import export_reliable_decisions_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
ROUTE = ex.ROUTE


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def set_at(aggregates, source, value):
    """Write `value` at a candidate block's source pointer (a dict value updates the keys it names)."""
    name, _, pointer = source.partition('#')
    toks = [t.replace('~1', '/').replace('~0', '~') for t in pointer.split('/')[1:]]
    node = aggregates[name]
    for t in toks[:-1]:
        node = node[t]
    if isinstance(value, dict) and isinstance(node[toks[-1]], dict):
        node[toks[-1]].update(copy.deepcopy(value))
    else:
        node[toks[-1]] = copy.deepcopy(value)


def method(cand, protocol, mid):
    return cand['primary'][protocol]['methods'][mid]


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class ReliableDecisionsBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, ref, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        ref.update(path=str(path), sha256=digest(data))
        return digest(data)

    def forged(self, candidate=None, both=None, stage0=None, stage0s=None, manifest=None, rebind=True):
        """A copy whose candidate (and aggregates) were edited, with every hash in the chain re-bound to the edit.

        `both(cand, sync)` edits a traced block of the candidate; `sync(block)` writes the block's edited value
        back into the aggregate it points at, so re-resolution passes and the logic gates are what is exercised.
        The candidate names the aggregates and stage-0 audits by hash; the handoff names the candidate. Without
        `rebind` only the candidate is rewritten, so the manifest still pins the original bytes.
        """
        m = copy.deepcopy(MANIFEST)
        route = m['route']
        cand = load(route['releaseCandidate'])
        aggs = {'aggregate-primary.json': load(route['aggregatePrimary']),
                'aggregate-secondary.json': load(route['aggregateSecondary'])}
        s0, s0s = load(route['stage0Audit']), load(route['stage0SecondaryAudit'])
        handoff = (ex.PROJECT / route['handoff']['path']).read_text()
        if not rebind:
            if candidate:
                candidate(cand)
            pinned_sha = route['releaseCandidate']['sha256']
            self.write(route['releaseCandidate'], 'candidate.json', json.dumps(cand).encode())
            route['releaseCandidate']['sha256'] = pinned_sha     # the manifest still pins the original bytes
            return m
        if both:
            both(cand, lambda block: set_at(aggs, block['source'], block['value']))
        if stage0:
            stage0(s0)
        if stage0s:
            stage0s(s0s)
        for name, key in (('aggregate-primary.json', 'aggregatePrimary'), ('aggregate-secondary.json', 'aggregateSecondary')):
            cand['sources'][name]['sha256'] = self.write(route[key], name, json.dumps(aggs[name]).encode())
        cand['audits']['stage0']['sha256'] = self.write(route['stage0Audit'], 's0.json', json.dumps(s0).encode())
        cand['audits']['stage0_secondary']['sha256'] = self.write(route['stage0SecondaryAudit'], 's0s.json',
                                                                  json.dumps(s0s).encode())
        if candidate:          # last, so an edit to the hashes the candidate records is not re-bound away
            candidate(cand)
        old = route['releaseCandidate']['sha256']
        new = self.write(route['releaseCandidate'], 'candidate.json', json.dumps(cand).encode())
        self.write(route['handoff'], 'handoff.md', handoff.replace(old, new).encode())
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
        build(self.forged(both=lambda c, sync: sync(method(c, 'beta-8ch', 'cca')['operating_points']['F-cal@0.8'])))

    def test_the_shape(self):
        p = build(MANIFEST)
        self.assertEqual(p['schema_version'], 'bci-report-reliable-decisions-update-v1')
        self.assertEqual(p['release_id'], 'reliable-decisions-update-20261004')
        self.assertEqual(list(p['results']), [ROUTE])
        self.assertEqual((p['status_only'], p['holds']), ([], []))
        r = p['results'][ROUTE]
        self.assertEqual(list(r['protocols']), ['arithmetic-rest', 'beta-8ch'])
        self.assertEqual([m['id'] for m in r['protocols']['arithmetic-rest']['methods']],
                         ['spectral-ridge', 'eegnet', 'labram-frozen-ce', 'labram-lora-r4'])
        self.assertEqual([m['id'] for m in r['protocols']['beta-8ch']['methods']], ['cca', 'cbramod', 'eegnet'])
        self.assertEqual(list(r['robustness']), ['mi_rest', 'seeds', 'matched_model_holdout', 'map_sensitivity', 'l_joint'])
        self.assertEqual(p['provenance']['inputs'], ['eegmat', 'beta', 'ds003810'])
        self.assertEqual(p['provenance']['references_reresolved'], 1120)

    # ------------------------------------------------------------------ the figures the page prints
    def test_the_handoff_figures(self):
        r = build(MANIFEST)['results'][ROUTE]
        pct = lambda v: f'{100 * v:.1f}%'
        beta = {m['id']: m for m in r['protocols']['beta-8ch']['methods']}
        mat = {m['id']: m for m in r['protocols']['arithmetic-rest']['methods']}
        self.assertEqual([(pct(m['fixed_cutoff']['coverage']), m['fixed_cutoff']['people_with_nothing_accepted'])
                          for m in beta.values()], [('28.4%', 0), ('1.5%', 38), ('16.6%', 10)])
        self.assertEqual([(m['fixed_cutoff']['accepted'], m['fixed_cutoff']['people_with_nothing_accepted'])
                          for m in mat.values()], [(3, 33), (126, 19), (1, 35), (44, 24)])
        self.assertEqual([m['fixed_cutoff']['unstable'] for m in mat.values()], [True, False, True, False])
        self.assertEqual([pct(m['balanced_accuracy']) for m in [*mat.values(), *beta.values()]],
                         ['56.8%', '67.6%', '56.9%', '64.4%', '63.1%', '33.7%', '55.8%'])
        # Q2: L lower for no method at 80%; resolved where the handoff says, and nowhere else.
        c2 = {(p, m['id']): m['learned_minus_confidence']['error_at_80'] for p in r['protocols']
              for m in r['protocols'][p]['methods']}
        self.assertEqual(sorted(k for k, d in c2.items() if d['excludes_zero']),
                         [('arithmetic-rest', 'eegnet'), ('arithmetic-rest', 'labram-lora-r4'), ('beta-8ch', 'eegnet')])
        self.assertTrue(all(d['interval_95'][0] > 0 for d in c2.values() if d['excludes_zero']))
        c1 = {(p, m['id']): m['learned_minus_confidence']['aurc'] for p in r['protocols'] for m in r['protocols'][p]['methods']}
        self.assertEqual(sorted(k for k, d in c1.items() if d['excludes_zero']),
                         [('arithmetic-rest', 'labram-frozen-ce'), ('beta-8ch', 'cbramod')])
        # Q3: certified nothing on EEGMAT; BETA 7, 4 and 7 of 7, with 4, 2 and 2 folds over their target.
        self.assertTrue(all(m['risk_certification']['certified_folds'] == 0 and m['risk_certification']['selective_error'] is None
                            for m in mat.values()))
        self.assertEqual([(m['risk_certification']['certified_folds'], m['risk_certification']['folds_over_target'])
                          for m in beta.values()], [(7, 4), (4, 2), (7, 2)])
        self.assertFalse(any(m['risk_certification']['error_minus_target']['excludes_zero'] for m in beta.values()))
        # Q5: BETA, 40 labels, NLL and AURC lower for every method.
        for m in beta.values():
            (x,) = m['recalibration']
            self.assertEqual(x['labels_per_new_person'], 40)
            self.assertTrue(x['nll_change']['excludes_zero'] and x['nll_change']['mean'] < 0)
            self.assertTrue(x['aurc_change']['excludes_zero'] and x['aurc_change']['mean'] < 0)
        self.assertEqual([[x['labels_per_new_person'] for x in m['recalibration']] for m in mat.values()], [[10, 20]] * 4)
        # Q4: LoRA lower NLL, ECE not resolved.
        c4 = r['protocols']['arithmetic-rest']['lora_minus_head_only']
        self.assertTrue(c4['nll_calibrated']['excludes_zero'] and c4['nll_calibrated']['mean'] < 0)
        self.assertFalse(c4['ece_calibrated']['excludes_zero'])
        # Matched coverage on BETA: 165 trials; EEGMAT: one trial, no verdict.
        self.assertEqual(r['protocols']['beta-8ch']['common_coverage']['accepted'], 165)
        self.assertEqual([pct(e['mean']) for e in r['protocols']['beta-8ch']['common_coverage']['errors']], ['0.6%', '22.4%', '8.5%'])
        self.assertTrue(r['protocols']['arithmetic-rest']['common_coverage']['unstable'])
        self.assertNotIn('errors', r['protocols']['arithmetic-rest']['common_coverage'])

    # ------------------------------------------------------------------ the chain of custody
    def test_a_changed_input_byte_is_refused(self):
        for key in ('handoff', 'releaseCandidate', 'aggregatePrimary', 'aggregateSecondary', 'protocol',
                    'supersededProtocol', 'stage0Audit', 'stage0SecondaryAudit'):
            m = copy.deepcopy(MANIFEST)
            m['route'][key]['sha256'] = '0' * 64
            with self.assertRaises(ValueError, msg=key):
                build(m)

    def test_an_edited_candidate_the_manifest_did_not_pin_is_refused(self):
        def nudge(c):
            method(c, 'beta-8ch', 'cca')['operating_points']['F-cal@0.8']['value']['accepted'] = 3177
        with self.assertRaisesRegex(ValueError, 'release candidate'):
            build(self.forged(candidate=nudge, rebind=False))

    def test_a_candidate_figure_that_is_not_its_aggregates_is_refused(self):
        def nudge(c):
            method(c, 'beta-8ch', 'cbramod')['ranking']['S (calibrated MSP)']['value']['aurc'] += 0.001
        with self.assertRaisesRegex(ValueError, 'differs from aggregate-primary'):
            build(self.forged(candidate=nudge))

    def test_the_candidate_must_name_the_pinned_files(self):
        with self.assertRaisesRegex(ValueError, 'another aggregate-primary'):
            build(self.forged(candidate=lambda c: c['sources']['aggregate-primary.json'].update(sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'another protocol'):
            build(self.forged(candidate=lambda c: c['protocol'].update(sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'frozen thresholds'):
            build(self.forged(candidate=lambda c: c['frozen_thresholds_sha256'].update(primary='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'another run'):
            build(self.forged(candidate=lambda c: c.update(run_id='decision-route1-v1/20261005')))

    def test_the_audits_must_pass(self):
        with self.assertRaisesRegex(ValueError, 'stage-0 audit did not pass'):
            build(self.forged(stage0=lambda a: a.update(status='fail')))
        with self.assertRaisesRegex(ValueError, 'stage-0 audit did not pass'):
            build(self.forged(stage0=lambda a: a['hard_checks'].update({'input hashes match protocol': False})))
        with self.assertRaisesRegex(ValueError, 'stage-0 secondary audit did not pass'):
            build(self.forged(stage0s=lambda a: a.update(status='fail')))
        def other_failure(c):
            c['audits']['primary']['checks'][4]['pass'] = False
        with self.assertRaisesRegex(ValueError, 'other than its documentation check'):
            build(self.forged(candidate=other_failure))
        with self.assertRaisesRegex(ValueError, 'secondary audit did not pass'):
            build(self.forged(candidate=lambda c: c['audits']['secondary']['checks'][0].update({'pass': False})))
        with self.assertRaisesRegex(ValueError, 'other independent audits'):
            build(self.forged(candidate=lambda c: c['audits']['primary'].update(sha256='0' * 64)))

    def test_the_approval_is_on_record(self):
        for edit in (lambda m: m['approval'].update(decision='hold'), lambda m: m['approval'].update(date='2026-10-03'),
                     lambda m: m['approval'].update(candidateStatusAtSeal='approved')):
            m = copy.deepcopy(MANIFEST)
            edit(m)
            with self.assertRaises(ValueError):
                build(m)
        with self.assertRaisesRegex(ValueError, 'state it was sealed in'):
            build(self.forged(candidate=lambda c: c.update(status='approved')))

    # ------------------------------------------------------------------ the logic gates
    def test_the_accuracy_must_be_the_sites(self):
        def other(c, sync):
            block = method(c, 'beta-8ch', 'eegnet')['full_coverage_balanced_accuracy']
            block['value']['balanced_accuracy'] += 0.01
            block['value']['published_balanced_accuracy'] += 0.01
            sync(block)
        with self.assertRaisesRegex(ValueError, 'the site value'):
            build(self.forged(both=other))
        def flag(c, sync):
            block = method(c, 'arithmetic-rest', 'labram-lora-r4')['full_coverage_balanced_accuracy']
            block['value']['balanced_accuracy_equals_published'] = False
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not the published one'):
            build(self.forged(both=flag))

    def test_nothing_accepted_has_no_error_rate(self):
        def zero(c, sync):
            block = method(c, 'arithmetic-rest', 'eegnet')['operating_points']['S-risk@relative']
            block['value']['selective_error'] = 0.0
            sync(block)
        with self.assertRaisesRegex(ValueError, 'a null turned into a number'):
            build(self.forged(both=zero))

    def test_coverage_is_accepted_over_n_and_unstable_below_ten(self):
        def cover(c, sync):
            block = method(c, 'beta-8ch', 'cca')['operating_points']['F-cal@0.8']
            block['value']['coverage'] += 0.001
            sync(block)
        with self.assertRaisesRegex(ValueError, 'coverage is not accepted / n'):
            build(self.forged(both=cover))
        def stable(c, sync):
            block = method(c, 'arithmetic-rest', 'spectral-ridge')['operating_points']['F-cal@0.8']
            block['value']['unstable'] = False
            sync(block)
        with self.assertRaisesRegex(ValueError, 'unstable flag'):
            build(self.forged(both=stable))
        def people(c, sync):
            block = method(c, 'beta-8ch', 'cbramod')['operating_points']['F-cal@0.8']
            block['value']['zero_coverage_people'] = 71
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not a count of 70'):
            build(self.forged(both=people))

    def test_every_interval_holds_its_point(self):
        def wide(c, sync):
            block = method(c, 'beta-8ch', 'eegnet')['intervals']
            block['value']['nll_cal']['ci95'] = [2.0, 2.2]
            sync(block)
        with self.assertRaisesRegex(ValueError, 'does not contain its point'):
            build(self.forged(both=wide))

    def test_the_verdict_follows_the_interval(self):
        def call(c, sync):
            block = c['primary']['beta-8ch']['contrasts']['C2:cca:err@0.8(L)-err@0.8(S)']
            block['value']['excludes_zero'] = True
            sync(block)
        with self.assertRaisesRegex(ValueError, 'excludes_zero does not follow'):
            build(self.forged(both=call))
        def word(c):
            c['primary']['beta-8ch']['contrasts']['C2:cca:err@0.8(L)-err@0.8(S)']['verdict'] = RESOLVED
        with self.assertRaisesRegex(ValueError, 'does not follow from the interval'):
            build(self.forged(candidate=word))

    def test_a_contrast_is_the_difference_of_its_levels(self):
        def drift(c, sync):
            block = c['primary']['beta-8ch']['contrasts']['C1:cbramod:AURC(L)-AURC(S)']
            block['value']['point'] -= 0.002
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not the difference of its levels'):
            build(self.forged(both=drift))
        def c6(c, sync):
            block = c['primary']['beta-8ch']['contrasts']['C6:cca:S-risk(rel) error - r*']
            block['value']['point'] += 0.003
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not the difference of its levels'):
            build(self.forged(both=c6))

    def test_certified_folds_add_up(self):
        def certify(c, sync):
            block = method(c, 'beta-8ch', 'cbramod')['operating_points']['S-risk@relative']
            block['value']['folds_violating'] = 5
            sync(block)
        with self.assertRaisesRegex(ValueError, 'folds over r'):
            build(self.forged(both=certify))
        def flags(c, sync):
            block = method(c, 'beta-8ch', 'cbramod')['flags']
            block['value']['certified_folds_by_risk_threshold']['S-risk@relative'] = 5
            sync(block)
        with self.assertRaisesRegex(ValueError, 'certified folds disagree'):
            build(self.forged(both=flags))

    def test_labels_per_new_person_are_the_protocols(self):
        def labels(c, sync):
            block = method(c, 'beta-8ch', 'cca')['recalibration']['prefix']['arms']
            block['value']['labels_per_new_person']['R1'] = [48]
            sync(block)
        with self.assertRaisesRegex(ValueError, 'another label cost'):
            build(self.forged(both=labels))

    def test_ds003810_stays_crude(self):
        def promote(c, sync):
            block = c['primary']['mi-rest']['design']
            block['value']['primary_contrasts'] = True
            sync(block)
        with self.assertRaisesRegex(ValueError, 'without primary contrasts'):
            build(self.forged(both=promote))
        r = build(MANIFEST)['results'][ROUTE]['robustness']['mi_rest']
        self.assertEqual(r['role'], 'secondary, crude')
        self.assertNotIn('probability_quality', json.dumps(r))

    def test_the_rights_are_the_reviewed_core_tracks(self):
        for key, value in (('attribution', 'Someone else'), ('license', 'CC0-1.0'), ('reviewBasis', [])):
            m = copy.deepcopy(MANIFEST)
            m['sources'][1][key] = value
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
    def test_per_person_and_per_fold_fields_are_refused_by_key(self):
        for key in ('p10', 'p50', 'p90', 'median_T_over_folds', 'person_spread_10_50_90', 'per_class_acceptance',
                    'reliability_bins_calibrated', 'rc_curve_20', 'per_fold', 'per_person_metrics', 'percentile_90',
                    'idle', 'bnci', 'bnci2015_001_budgets', 'idle_windows', 'compute_time', 'environment',
                    'elapsed_seconds', 'predictions', 'probabilities', 'participant_id', 'private_audit'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('/Volumes/disk/x', '/Users/someone/x', 'host:/mnt/bigdata', 'sub-07', 'subj12',
                     'test-probabilities.npz', 'scores.private', 'DECISIONS.md entry 46'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_per_person_values_stay_out_by_value(self):
        payload = build(MANIFEST)
        cand = load(MANIFEST['route']['releaseCandidate'])
        withheld = set(ex.withheld_values(cand))
        published = set(ex.numbers(payload))
        pooled = {x['coverage'] for x in ex.pooled_operating_points(payload['results'][ROUTE])}
        self.assertFalse((withheld & published) - pooled - ex.DESIGN_CONSTANTS)
        # The BETA CCA median per-person coverage under the coverage target, and its median temperature.
        self.assertNotIn(0.85625, published)
        self.assertNotIn(0.04185910773492259, published)

        def leak(c, sync):  # a published level that happens to be one person's percentile
            m = method(c, 'beta-8ch', 'cca')
            spread = m['person_spread_10_50_90']
            spread['value']['nll_cal']['p50'] = m['probability_quality_calibrated']['value']['nll']
            sync(spread)
        with self.assertRaisesRegex(ValueError, 'per-person or per-fold value'):
            build(self.forged(both=leak))

    def test_idle_and_bnci_carry_no_figure(self):
        payload = build(MANIFEST)
        keys = set()

        def walk(v):
            if isinstance(v, dict):
                keys.update(k.lower() for k in v)
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(payload)
        self.assertFalse([k for k in keys if 'idle' in k or 'bnci' in k or 'p10' in k or 'median' in k])
        self.assertNotIn('ds005342', json.dumps(payload['results']))
        self.assertNotIn('BNCI', json.dumps(payload['results']))

    def test_the_class_conditional_rows_are_said_to_be_left_out(self):
        # The candidate's first boundary says class-conditional rows are given; this file refuses them, so it says so.
        p = build(MANIFEST)
        bounds = p['results'][ROUTE]['boundaries']['all_protocols']
        self.assertFalse([b for b in bounds if 'rows are given' in b])
        self.assertTrue(bounds[0].endswith('are not carried into this file.'))
        self.assertTrue(any('class-conditional rows' in x and 'acceptance per class' in x for x in p['not_published']))
        self.assertFalse([x for x in p['not_published'] if 'per-class acceptance spreads' in x])
        # A candidate whose boundary no longer says what the export replaces is refused, not carried.
        def reword(c):
            c['boundaries']['all_protocols'][0] = c['boundaries']['all_protocols'][0].replace('re-weight', 'reweight')
        with self.assertRaisesRegex(ValueError, 'class-conditional'):
            build(self.forged(candidate=reword))

    def test_the_bnci_hold_carries_its_register_date(self):
        # The holds register opened it on 2026-09-20; the 2026-10-01 release restated it.
        item = [x for x in build(MANIFEST)['not_published'] if 'BNCI2015-001' in x]
        self.assertEqual(len(item), 1)
        self.assertIn('opened on 2026-09-20', item[0])

    # ------------------------------------------------------------------ not_published is a claim about the file (2026-10-05)
    def test_no_not_published_item_withholds_what_the_file_carries(self):
        p = build(MANIFEST)
        result = p['results'][ex.ROUTE]
        ex.check_not_published(result, p['not_published'])
        # The ds003810 item names what is withheld; the file carries the rest, as the privacy review lists it.
        item = [x for x in p['not_published'] if x.startswith('On ds003810')]
        self.assertEqual(len(item), 1)
        self.assertFalse([x for x in p['not_published'] if 'every ds003810 figure other than' in x])
        mi = result['robustness']['mi_rest']
        self.assertTrue(all(tuple(m) == ex.DS003810_FIELDS for m in mi['methods']))
        self.assertTrue(mi['rights']['privacyReview'].endswith(ex.DS003810_PUBLISHED))
        for words in ('selective error', 'unstable', 'certified-risk fold counts', 'balanced accuracy'):
            self.assertIn(words, mi['rights']['privacyReview'])
        # A field an item says is left out, put back into the file, is refused.
        for edit in (lambda r: r['robustness']['mi_rest']['methods'][1].update(probability_quality={}),
                     lambda r: r['robustness']['mi_rest']['methods'][0].update(ranking_S={}),
                     lambda r: r['robustness']['matched_model_holdout']['rows'][0].update(balanced_accuracy=0.6),
                     lambda r: r['robustness']['l_joint']['rows'][0].update(balanced_accuracy=0.6),
                     lambda r: r['robustness']['seeds']['rows'].append({'protocol': 'mi-rest'}),
                     lambda r: r['protocols']['beta-8ch']['methods'][0]['ranking_S']['error_at_test_coverage'][0]
                     .update(interval_95=[0.1, 0.2]),
                     lambda r: r['protocols']['arithmetic-rest'].update(median_temperature=1.0)):
            forged = copy.deepcopy(result)
            edit(forged)
            with self.assertRaisesRegex(ValueError, 'not_published: the file carries'):
                ex.check_not_published(forged, p['not_published'])

    def test_a_not_published_item_without_a_check_is_refused(self):
        p = build(MANIFEST)
        result = p['results'][ex.ROUTE]
        old = ('Secondary seeds and ensembles on ds003810, and every ds003810 figure other than the fixed-threshold '
               'coverage and the learned-reject contrasts.')
        items = [old if x.startswith('On ds003810') else x for x in p['not_published']]
        with self.assertRaisesRegex(ValueError, 'no check for the item'):
            ex.check_not_published(result, items)
        with self.assertRaisesRegex(ValueError, 'missing or named twice'):
            ex.check_not_published(result, p['not_published'][:-1])
        m = copy.deepcopy(MANIFEST)
        m['notPublished'] = items
        with self.assertRaisesRegex(ValueError, 'no check for the item'):
            build(m)

    def test_the_ds003810_privacy_review_says_what_is_published(self):
        m = copy.deepcopy(MANIFEST)
        rec = next(s for s in m['sources'] if s['id'] == 'ds003810')
        rec['privacyReview'] = rec['privacyReview'].replace('; and the certified-risk fold counts', '')
        with self.assertRaisesRegex(ValueError, 'does not say what the panel publishes'):
            build(m)

    def test_no_private_path_or_identifier_reaches_the_files(self):
        text = json.dumps(build(MANIFEST), ensure_ascii=False)
        # Path roots only: naming this operator's machines or volumes here would itself be the leak.
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', '.npz', 'private.', 'DECISIONS.md'):
            self.assertNotIn(token, text)
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/'):
                self.assertNotIn(token, body, f'{path.name}: {token}')


RESOLVED = ex.RESOLVED

if __name__ == '__main__':
    unittest.main()
