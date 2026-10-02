"""The 2026-10-02 extension batch: what must stay out, and what must follow from the audited counts."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import export_extension_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
YSU, LTR = 'ysu-async-ssvep-extension', 'ltrsvp-rate-transfer'


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class ExtensionBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def forged(self, sid, change_summary=None, change_audit=None, rebind=True):
        """A copy of the manifest whose aggregate (and audit) were edited, with hashes that match the edit.

        Without `rebind` the audit still names the original aggregate, which is the realistic forgery.
        """
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, sid)
        summary = json.loads((ex.PROJECT / record['summary']['path']).read_bytes())
        audit = json.loads((ex.PROJECT / record['numericalAudit']['path']).read_bytes())
        if change_summary:
            change_summary(summary)
        raw = json.dumps(summary).encode()
        if rebind:
            audit['public_summary_sha256'] = hashlib.sha256(raw).hexdigest()
        if change_audit:
            change_audit(audit)
        araw = json.dumps(audit).encode()
        for key, data in (('summary', raw), ('numericalAudit', araw)):
            path = Path(self.tmp.name) / f'{sid}-{key}.json'
            path.write_bytes(data)
            record[key] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
        return manifest

    def test_the_published_file_is_the_reviewed_build(self):
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), ex.serialized_export())

    def test_the_forgery_helper_itself_builds(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged(YSU))
        build(self.forged(LTR))

    def test_the_handoff_figures(self):
        r = build(MANIFEST)['results']
        y = {x['id']: x for x in r[YSU]['rules']}
        pct = lambda v: round(v * 100, 2)
        self.assertEqual([pct(y[k]['detection_balanced_accuracy']['mean']) for k in ('global', 'personal')], [75.99, 78.96])
        for k, cov, acc, both in (('global', 77.92, 85.85, 68.12), ('personal', 77.71, 85.11, 67.60)):
            w = y[k]['control_windows']
            self.assertEqual(pct(w['accepted'] / w['tested']), cov, k)
            self.assertEqual(pct(y[k]['accepted_window_accuracy_mean_over_people']), acc, k)
            self.assertEqual(pct(w['accepted_and_correct'] / w['tested']), both, k)
            self.assertEqual(pct(w['frequency_recognised'] / w['tested']), 80.10, k)
        far = {k: [pct(s['accepted'] / s['tested']) for s in y[k]['false_acceptance']] for k in y}
        self.assertEqual(far, {'global': [20.42, 38.75, 22.29], 'personal': [13.33, 32.92, 16.46]})
        d = r[YSU]['paired_difference']
        self.assertEqual((pct(d['mean']), [pct(v) for v in d['bootstrap_95']]), (2.97, [0.52, 5.68]))
        self.assertEqual((d['helped'], d['harmed'], d['tied']), (10, 8, 2))

        lt = r[LTR]
        self.assertEqual([pct(a['balanced_accuracy']['mean']) for a in lt['primary']['arms']], [60.83, 62.99])
        self.assertEqual([round(a['auroc']['mean'], 4) for a in lt['primary']['arms']], [0.6728, 0.6945])
        p = lt['paired_difference']
        self.assertEqual((pct(p['mean']), [pct(v) for v in p['bootstrap_95']]), (-2.15, [-6.77, 2.8]))
        self.assertEqual((p['people_lower'], p['people_higher'], p['people_tied']), (7, 2, 0))
        self.assertIs(p['interval_crosses_zero'], True)
        self.assertEqual((lt['primary']['target_events'], lt['primary']['non_target_events']), (223, 2036))
        self.assertEqual(lt['cohort']['unique_test_events'], 8626)
        self.assertEqual(len(lt['matrix']), 9)
        self.assertIs(lt['not_causal'], True)

    def test_counts_cover_the_cohort(self):
        r = build(MANIFEST)['results']
        d = r[YSU]['paired_difference']
        self.assertEqual(d['helped'] + d['harmed'] + d['tied'], r[YSU]['cohort']['people'])
        p = r[LTR]['paired_difference']
        self.assertEqual(p['people_lower'] + p['people_higher'] + p['people_tied'], r[LTR]['cohort']['people'])

    def test_a_changed_input_byte_is_refused(self):
        for sid in (YSU, LTR):
            for key in ('summary', 'protocol', 'numericalAudit'):
                manifest = copy.deepcopy(MANIFEST)
                source(manifest, sid)[key]['sha256'] = '0' * 64
                with self.assertRaises(ValueError, msg=f'{sid}/{key}'):
                    build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, YSU)['consentRecord']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['sourceHandoffs'][1]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_an_audit_of_other_bytes_is_refused(self):
        def nudge(s):
            s['paired_BA_personal_minus_global']['bootstrap_mean_ci95'][0] = 0.006
        with self.assertRaisesRegex(ValueError, 'different aggregate'):
            build(self.forged(YSU, nudge, rebind=False))

    def test_a_failed_audit_is_refused(self):
        for sid in (YSU, LTR):
            with self.assertRaisesRegex(ValueError, 'did not pass'):
                build(self.forged(sid, change_audit=lambda a: a.update(status='FAIL')))

    def test_a_rate_that_is_not_a_whole_count_is_refused(self):
        def off(s):
            s['arms']['personal']['NS']['NS2']['participant']['mean'] += 1e-4
        with self.assertRaisesRegex(ValueError, 'NS2'):
            build(self.forged(YSU, off))

        def unequal(s):  # windows that no longer split evenly across the twenty people
            s['test_counts']['NS3'] = 470
        with self.assertRaisesRegex(ValueError, 'not equal across people'):
            build(self.forged(YSU, unequal))

    def test_detection_and_the_paired_difference_must_follow_from_the_counts(self):
        def ba(s):
            s['arms']['global']['balanced_accuracy']['mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'detection BA'):
            build(self.forged(YSU, ba))

        def frac(s):
            s['paired_BA_personal_minus_global']['exact_fraction'] = '20/640'
        with self.assertRaisesRegex(ValueError, 'follow from the counts'):
            build(self.forged(YSU, frac))

        def cohort(s):
            s['paired_BA_personal_minus_global']['tied'] = 3
        with self.assertRaisesRegex(ValueError, 'cohort'):
            build(self.forged(YSU, cohort))

    def test_the_trade_off_wording_is_held_to_the_numbers(self):
        def more_correct(s):  # if the personal rule produced more correct commands, the page wording would be wrong
            p = s['arms']['personal']
            p['CS_counts']['accepted_frequency_correct_count'] = 660
            p['CS']['correct_and_accepted_rate']['mean'] = 660 / 960
        with self.assertRaisesRegex(ValueError, 'trade-off'):
            build(self.forged(YSU, more_correct))

    def test_the_rate_interval_must_cross_zero_for_the_wording(self):
        def narrow(s):
            s['primary_paired_BA_5a_to_10b_minus_10a_to_10b']['bootstrap_mean_ci95'] = [-0.05, -0.001]
        with self.assertRaisesRegex(ValueError, 'crosses zero'):
            build(self.forged(LTR, narrow))

    def test_every_training_rate_must_meet_the_same_test_images(self):
        def other_images(s):
            next(c for c in s['matrix'] if (c['source_rate_hz'], c['target_rate_hz']) == (5, 10))['target_n'] = 224
        with self.assertRaisesRegex(ValueError, 'differ between training rates'):
            build(self.forged(LTR, other_images))

    def test_identical_test_events_must_be_asserted_by_the_aggregate_and_the_audit(self):
        # The export checks counts only; that the events are the same is the aggregate's and the audit's claim.
        def no_identity(s):
            s['primary_estimand'] = s['primary_estimand'].replace('event identities', 'events')
        with self.assertRaisesRegex(ValueError, 'identical 10-Hz run-b test events'):
            build(self.forged(LTR, no_identity))

        def no_pairing(a):
            a['verified'] = [v for v in a['verified'] if not v.startswith('same-target paired primary contrast')]
        with self.assertRaisesRegex(ValueError, 'same-target pairing'):
            build(self.forged(LTR, change_audit=no_pairing))

    def test_the_presentation_order_needs_its_recorded_source(self):
        # Ascending, not randomised: stated only while the manifest holds the quotes it rests on.
        for drop in ('lowest to the highest', 'not randomised', 'which one was taken first'):
            manifest = copy.deepcopy(MANIFEST)
            for h in source(manifest, LTR)['decisionHistory']:
                h['quotes'] = [q for q in h.get('quotes', []) if drop not in q['text']]
            with self.assertRaisesRegex(ValueError, 'source', msg=drop):
                build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        del source(manifest, LTR)['decisionHistory']
        with self.assertRaises(ValueError):
            build(manifest)

    def test_the_order_wording(self):
        lt = build(MANIFEST)['results'][LTR]
        order = lt['presentation_order']
        self.assertIn('from the lowest to the highest', order['known'])
        self.assertIn('not randomised', order['known'])
        self.assertIn('how the two released files of each rate map onto', order['not_documented'])
        self.assertIn('elapsed time, fatigue and practice', order['consequence'])
        self.assertIn('https://doi.org/10.1371/journal.pone.0178498', order['sources'])
        text = json.dumps(lt)
        self.assertNotIn('not established', text, 'the order across rates is partly known; say what is')
        self.assertNotIn('order across rates', text)
        self.assertIn('not_causal', lt)

    def test_later_recording_only_within_a_rate(self):
        # Run b is later than run a only within a rate; across rates the mapping is undocumented.
        payload = build(MANIFEST)
        lt = payload['results'][LTR]
        for where, text in [('question', lt['question']), ('generalization', lt['generalization']),
                            ('rights.task', lt['rights']['task']), ('reading', lt['reading']),
                            *[(f'limitations[{i}]', t) for i, t in enumerate(lt['limitations'])]]:
            for sentence in re.split(r'(?<=[.;])\s+', text):
                if re.search(r'\blater\b[^.;]*\brecording|\bfollowed run a\b', sentence):
                    self.assertRegex(sentence, r'[Ww]ithin (?:a|each|one) rate', f'{where}: "{sentence}"')

    def test_the_task_names_same_rate_transfer_too(self):
        # The matrix diagonal is a same-rate transfer (run a to run b at one rate). The task
        # said "at another" rate only until the 2026-10-02 review; the generalization says both.
        lt = build(MANIFEST)['results'][LTR]
        self.assertIn('tested on a different recording at the same or another rate', lt['rights']['task'])
        self.assertIn('at the same or another rate', lt['generalization'])
        self.assertNotRegex(lt['rights']['task'], r'different recording at another\b')
        self.assertEqual(lt['rights']['task'], source(MANIFEST, LTR)['task'], 'the task is the manifest\'s, unchanged')

    def test_the_paired_rate_difference_must_equal_the_cells(self):
        def drift(s):
            s['primary_paired_BA_5a_to_10b_minus_10a_to_10b']['mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'paired mean'):
            build(self.forged(LTR, drift))

    def test_per_person_threshold_and_prediction_fields_are_refused(self):
        for key in ('range', 'min', 'max', 'median', 'q1', 'global_threshold', 'thresholds', 'prediction_rows',
                    'probabilities', 'features', 'per_person_balanced_accuracy', 'private_evidence'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('S05', 'archive S24', 'rsvp_10Hz_00a.edf'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        payload = build(MANIFEST)
        keys = set()
        def walk(v):
            if isinstance(v, dict):
                keys.update(v)
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(payload)
        for fragment in ('range', 'min', 'max', 'median', 'threshold', 'prediction', 'private', 'feature'):
            self.assertFalse([k for k in keys if fragment in k.lower() and k not in ('people_missing',)], fragment)
        text = json.dumps(payload)
        for path in ('/Volumes/', '/Users/', '/home/'):
            self.assertNotIn(path, text)
        protocol = json.loads((ex.PROJECT / source(MANIFEST, YSU)['protocol']['path']).read_bytes())
        self.assertNotIn(protocol['global_threshold'], set(ex.numbers(payload)), 'the fitted threshold value')

    def test_the_consent_record_must_match_the_source(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, YSU)['attribution'] += ' Edited.'
        with self.assertRaisesRegex(ValueError, 'attribution'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, YSU)['consentRecord']['sourceId'] = 'gait-eeg'
        with self.assertRaises(ValueError):
            build(manifest)

    def test_an_incomplete_rights_record_is_refused(self):
        for sid in (YSU, LTR):
            for missing in ('privacyReview', 'reviewBasis', 'attribution', 'licenseUrl'):
                manifest = copy.deepcopy(MANIFEST)
                del source(manifest, sid)[missing]
                with self.assertRaises((ValueError, KeyError), msg=f'{sid}/{missing}'):
                    build(manifest)

    def test_only_an_aggregate_decision_is_exported(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, LTR)['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(manifest)


if __name__ == '__main__':
    unittest.main()
