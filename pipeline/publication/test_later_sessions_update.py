"""The later-sessions release: what must stay out, and what must follow from the four audited releases."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_later_sessions_export as au
import export_later_sessions_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
CPU, FM, RSVP, FORENZO = ex.WBCIC_CPU, ex.WBCIC_FM, ex.RSVP, ex.FORENZO
VEL, DISP = 'historical_decoder_velocity_imitation', 'constructed_raw_target_displacement_proxy'


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


def dataset(manifest, did):
    return next(d for d in manifest['datasets'] if d['id'] == did)


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class LaterSessionsBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, record, key, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        record[key] = {'path': str(path), 'sha256': digest(data)}
        return digest(data)

    # ------------------------------------------------------------------ forgeries, hash chains re-bound
    def forged_cpu(self, release=None, audit=None, decision=None):
        """The WBCIC CPU release (and audit) edited, the decision re-bound to the edit."""
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, CPU)
        rel, aud, dec = (load(record[k]) for k in ('release', 'numericalAudit', 'releaseDecision'))
        if audit:
            audit(aud)
            aud_sha = self.write(record, 'numericalAudit', 'cpu-audit.json', json.dumps(aud).encode())
            rel['provenance']['audit_sha256'] = dec['audit']['sha256'] = aud_sha
        if release:
            release(rel)
        dec['export']['sha256'] = self.write(record, 'release', 'cpu-release.json', json.dumps(rel).encode())
        if decision:
            decision(dec)
        self.write(record, 'releaseDecision', 'cpu-decision.json', json.dumps(dec).encode())
        return manifest

    def forged_fm(self, cohorts=None, audit=None, release=None, decision=None):
        """The CBraMod release edited; `cohorts` edits the release and the root check identically, `audit` the
        independent audit, and every hash that names them is re-bound."""
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, FM)
        rel, root, aud, dec = (load(record[k]) for k in ('release', 'rootCheck', 'numericalAudit', 'releaseDecision'))
        if audit:
            audit(aud['cohorts'])
            aud_sha = self.write(record, 'numericalAudit', 'fm-audit.json', json.dumps(aud).encode())
            rel['provenance']['independent_result_audit_sha256'] = dec['independent_result_audit_sha256'] = aud_sha
            root['auditor_result_sha256'] = aud_sha
        if cohorts or audit:
            if cohorts:
                cohorts(rel['cohorts'])
                cohorts(root['cohorts'])
            root_sha = self.write(record, 'rootCheck', 'fm-root.json', json.dumps(root).encode())
            rel['provenance']['root_aggregate_check_sha256'] = dec['root_check_sha256'] = root_sha
        if release:
            release(rel)
        dec['release_sha256'] = self.write(record, 'release', 'fm-release.json', json.dumps(rel).encode())
        if decision:
            decision(dec)
        self.write(record, 'releaseDecision', 'fm-decision.json', json.dumps(dec).encode())
        return manifest

    def forged_rsvp(self, release=None, rebind=True):
        """The RSVP release edited; the decision and the final check re-bound unless `rebind` is False."""
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, RSVP)
        rel, dec, fin = (load(record[k]) for k in ('release', 'releaseDecision', 'finalCheck'))
        if release:
            release(rel)
        rel_sha = self.write(record, 'release', 'rsvp-release.json', json.dumps(rel).encode())
        if rebind:
            dec['export_sha256'] = rel_sha
            fin['file_pins']['results/rsvp-longitudinal-retention-cpu-v2-website-release.json'] = rel_sha
            dec_sha = self.write(record, 'releaseDecision', 'rsvp-decision.json', json.dumps(dec).encode())
            fin['file_pins']['review/rsvp-longitudinal-retention-root-release-decision-v2.json'] = dec_sha
            self.write(record, 'finalCheck', 'rsvp-final.json', json.dumps(fin).encode())
        return manifest

    def forged_forenzo(self, release=None, review=None, rebind=True):
        """The Forenzo release (and review) edited; the root decision re-bound unless `rebind` is False."""
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, FORENZO)
        rel, rev, dec = (load(record[k]) for k in ('release', 'independentReview', 'releaseDecision'))
        if review:
            review(rev)
            rev_sha = self.write(record, 'independentReview', 'forenzo-review.json', json.dumps(rev).encode())
            rel['release_review']['independent_review_sha256'] = dec['independent_review']['sha256'] = rev_sha
        if release:
            release(rel)
        rel_sha = self.write(record, 'release', 'forenzo-release.json', json.dumps(rel).encode())
        if rebind:
            dec['release_export']['sha256'] = rel_sha
            self.write(record, 'releaseDecision', 'forenzo-decision.json', json.dumps(dec).encode())
        return manifest

    # ------------------------------------------------------------------ the build itself
    def test_the_published_file_is_the_reviewed_build(self):
        data = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(audit, au.audit(), 'the recorded audit is the one the auditor writes for these bytes')

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helpers_themselves_build(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged_cpu())
        build(self.forged_fm())
        build(self.forged_fm(cohorts=lambda c: None, audit=lambda c: None))
        build(self.forged_rsvp())
        build(self.forged_forenzo())

    def test_the_shape(self):
        p = build(MANIFEST)
        self.assertEqual(p['schema_version'], 'bci-report-later-sessions-update-v1')
        self.assertEqual(p['release_id'], 'later-sessions-update-20261008')
        self.assertEqual(p['question'], 'Does a decoder trained on an earlier session still work later?')
        self.assertEqual(list(p['results']), [CPU, FM, RSVP, FORENZO])
        self.assertEqual(list(p['datasets']), ['wbcic-shu', 'longitudinal-rsvp', 'forenzo-continuous-tracking'])
        self.assertEqual([p['status_only'], p['holds']], [[], []])
        self.assertEqual(p['provenance']['source_export_sha256'],
                         {s['id']: s['release']['sha256'] for s in MANIFEST['sources']})

    # ------------------------------------------------------------------ the figures the pages print
    def test_the_wbcic_handoff_figures(self):
        r = build(MANIFEST)['results']
        pct = lambda b: (round(100 * b['mean'], 2), [round(100 * v, 2) for v in b['interval_95']])
        cpu, fm = r[CPU]['cohorts'], r[FM]['cohorts']
        self.assertEqual(pct(cpu['2C']['arms']['relative_spectral_ridge']['balanced_accuracy']), (53.88, [52.72, 55.09]))
        self.assertEqual(pct(cpu['3C']['arms']['relative_spectral_ridge']['balanced_accuracy']), (37.64, [35.42, 39.97]))
        self.assertEqual(round(100 * cpu['2C']['paired']['balanced_accuracy_difference']['mean'], 2), 3.88)
        self.assertEqual(round(100 * cpu['3C']['paired']['balanced_accuracy_difference']['mean'], 2), 4.30)
        self.assertEqual(pct(fm['2C']['frozen_cbramod']['balanced_accuracy']), (67.69, [64.83, 70.48]))
        self.assertEqual(pct(fm['3C']['frozen_cbramod']['balanced_accuracy']), (51.61, [45.18, 58.27]))
        self.assertEqual(pct(fm['2C']['paired']['balanced_accuracy_difference']), (13.81, [11.25, 16.37]))
        self.assertEqual(pct(fm['3C']['paired']['balanced_accuracy_difference']), (13.97, [7.45, 20.82]))
        for c, n, k in (('2C', 51, 2), ('3C', 11, 3)):
            self.assertEqual([cpu[c]['people'], fm[c]['people']], [n, n])
            self.assertEqual(cpu[c]['chance_level'], 1 / k)
            self.assertEqual(cpu[c]['arms']['source_prior']['balanced_accuracy']['interval_95'][0],
                             cpu[c]['arms']['source_prior']['balanced_accuracy']['mean'])
            self.assertEqual(fm[c]['relative_spectral_ridge']['balanced_accuracy']['mean'],
                             cpu[c]['arms']['relative_spectral_ridge']['balanced_accuracy']['mean'])

    def test_the_wbcic_counts(self):
        r = build(MANIFEST)['results'][CPU]
        self.assertEqual(r['trials'], {'source': 13498, 'target': 13495, 'session_files': 124, 'excluded': 0})
        q = r['session_quality']
        self.assertEqual([q['sessions'], q['fixed_count_holds'], q['holds_in_selected_sessions'],
                          q['holds_in_unused_session_2'], q['delivered_trials'], q['nominal_trials']],
                         [186, 6, 3, 3, 40490, 40500])
        self.assertEqual(r['sessions']['train'], 1)
        self.assertEqual(r['sessions']['test'], 3)
        self.assertEqual(r['sessions']['target_session_labels'], 0)

    def test_the_rsvp_handoff_figures(self):
        r = build(MANIFEST)['results'][RSVP]
        f4 = lambda x: round(x, 4)
        want = [(7, 0.8876, [0.8641, 0.9109], 0.3592, 0.1543, 0.0292, 0.0232, 1794),
                (80, 0.8791, [0.8545, 0.9035], 0.3104, 0.1136, 0.0266, 0.0201, 1786),
                (200, 0.8528, [0.8273, 0.8786], 0.2399, 0.1643, 0.0382, 0.0390, 1793)]
        for v, (day, auc, iv, ap, ll, br, ece, tg) in zip(r['visits'], want):
            self.assertEqual((v['nominal_day'], f4(v['auroc']['mean']), [f4(x) for x in v['auroc']['interval_95']],
                              f4(v['average_precision']['mean']), f4(v['log_loss']['mean']), f4(v['brier_score']['mean']),
                              f4(v['ece_10_bins']['mean']), v['target_events']), (day, auc, iv, ap, ll, br, ece, tg))
            self.assertEqual((v['people'], v['events'], v['delivered_events']), (15, 72000, None))
        c = r['contrast']
        self.assertEqual((f4(c['auroc_difference']['mean']), [f4(x) for x in c['auroc_difference']['interval_95']]),
                         (-0.0349, [-0.0650, -0.0064]))
        self.assertEqual((c['people_declined_by_0_05_or_more'], c['people'], c['share_declined_by_0_05_or_more']), (6, 15, 0.4))
        self.assertEqual(r['design'], {**r['design'], 'first_visit_fit_events': 72000, 'first_visit_calibration_events': 24000,
                                       'scored_events': 216000, 'blocks': 195, 'selected_events': 312000,
                                       'events_removed_for_signal': 0})

    def test_the_forenzo_handoff_figures(self):
        r = build(MANIFEST)['results'][FORENZO]
        f4 = lambda x: round(x, 4)
        want = {('Main', VEL): (9, 192.2901, 1.3166, 1.2658, 191.0244, [0.0257, 572.9951]),
                ('Main', DISP): (9, 698.4993, 1.2251, 1.0558, 697.4434, [0.1206, 2091.9458]),
                ('Transfer Learning', VEL): (14, 44.1720, 0.9899, 0.8637, 43.3083, [0.1050, 129.6013]),
                ('Transfer Learning', DISP): (14, 69.8445, 1.1818, 0.9160, 68.9285, [0.1426, 206.4099])}
        for (c, arm), w in want.items():
            a = r['cohorts'][c]['arms'][arm]
            p = a['paired']
            self.assertEqual((a['records'], f4(a['ridge']['primary']['mean']), f4(a['ridge']['primary']['median']),
                              f4(a['source_mean']['primary']['mean']), f4(p['primary_difference']['mean']),
                              [f4(x) for x in p['primary_difference']['interval_95']]), w, (c, arm))
            self.assertEqual(p['records_with_higher_ridge_error'], p['records'])
            self.assertGreater(a['upper_tail']['ridge_mean_over_median'], 40)
            self.assertNotIn('median', a['source_mean']['primary'])
            self.assertNotIn('median', p['primary_difference'])
        self.assertEqual([r['cohorts'][c][k] for c in ('Main', 'Transfer Learning')
                          for k in ('candidate_records', 'admitted_records', 'held_before_scoring')], [14, 9, 5, 14, 14, 0])
        self.assertEqual(sum(h['records'] for h in r['cohorts']['Main']['hold_reasons']), 5)
        cov = r['coverage']
        self.assertEqual([cov['target_rows_per_arm'], cov['response_fits'], cov['source_target_members'], cov['input_rows'],
                          cov['admitted_records']], [1999926, 46, 552, 4000407, 23])
        m = r['cohorts']['Main']['arms'][VEL]
        self.assertEqual([m['target_rows'], m['target_trials'], m['target_runs']], [782814, 540, 108])

    # ------------------------------------------------------------------ chains and gates
    def test_a_changed_input_byte_is_refused(self):
        for sid, key in ((CPU, 'release'), (FM, 'rootCheck'), (RSVP, 'finalCheck'), (FORENZO, 'independentReview'),
                         (CPU, 'handoff')):
            manifest = copy.deepcopy(MANIFEST)
            ref = source(manifest, sid)[key]
            raw = bytearray((ex.PROJECT / ref['path']).read_bytes())
            raw[-2:-1] = b' '
            path = Path(self.tmp.name) / f'{sid}-{key}'
            path.write_bytes(bytes(raw))
            ref['path'] = str(path)
            with self.assertRaisesRegex(ValueError, 'pinned', msg=(sid, key)):
                build(manifest)

    def test_a_release_the_decision_did_not_name_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'the decision names other bytes'):
            build(self.forged_rsvp(release=lambda r: r.update(title='x'), rebind=False))
        with self.assertRaisesRegex(ValueError, 'the decision names other bytes'):
            build(self.forged_forenzo(release=lambda r: r.update(task='x'), rebind=False))

    def test_a_failed_audit_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'independent audit did not pass'):
            build(self.forged_cpu(audit=lambda a: a.update(verdict='fail')))
        with self.assertRaisesRegex(ValueError, 'the review did not pass'):
            build(self.forged_forenzo(review=lambda r: r.update(blocking_findings=['x'])))

    def test_the_cpu_release_must_equal_its_audit(self):
        def edit(r):
            r['cohorts']['2C']['methods']['relative_spectral_ridge']['accuracy_conditional_mean'] = 0.6
        with self.assertRaisesRegex(ValueError, 'release cohorts differ from the audit'):
            build(self.forged_cpu(release=edit))

    def test_the_two_wbcic_releases_must_share_the_spectral_ridge(self):
        def edit(c):
            c['2C']['spectral_ridge_balanced_accuracy'] += 1e-9
            c['2C']['paired_difference'] -= 1e-9
        with self.assertRaisesRegex(ValueError, 'not the CPU release'):
            build(self.forged_fm(cohorts=edit))

    def test_the_release_must_equal_the_independent_audit(self):
        def edit(c):
            c['3C']['cbramod_ci95'] = [0.45, 0.59]
        with self.assertRaisesRegex(ValueError, 'audit interval'):
            build(self.forged_fm(cohorts=edit))

    def test_every_interval_must_contain_its_mean(self):
        def edit(c):
            c['3C']['cbramod_ci95'] = [0.52, 0.58]

        def audited(c):
            c['3C']['paired_bootstrap']['primary']['ci_95_percentile']['cbramod'] = [0.52, 0.58]
        with self.assertRaisesRegex(ValueError, 'does not contain its mean'):
            build(self.forged_fm(cohorts=edit, audit=audited))

    def test_the_readings_are_held_to_the_intervals(self):
        def crossing(c):
            c['3C']['paired_difference_ci95'][0] = -0.01

        def audited(c):
            c['3C']['paired_bootstrap']['primary']['ci_95_percentile']['cbramod_minus_relative_spectral_ridge'][0] = -0.01
        with self.assertRaisesRegex(ValueError, 'no longer excludes zero'):
            build(self.forged_fm(cohorts=crossing, audit=audited))

        def contrast(r):
            r['contrast']['full_cohort']['interval']['q975'] = 0.001
            r['bootstrap']['Day_200_minus_Day_7']['q975'] = 0.001
        with self.assertRaisesRegex(ValueError, 'no longer lies below zero'):
            build(self.forged_rsvp(release=contrast))

        def tie(r):
            r['cohorts']['Main']['arms'][VEL]['paired_ridge_minus_source_mean'][ex.PRIMARY]['minimum'] = -0.001
        with self.assertRaisesRegex(ValueError, 'did not do worse'):
            build(self.forged_forenzo(release=tie))

        def no_tail(r):
            prim = r['cohorts']['Transfer Learning']['arms'][VEL]['methods']['ridge'][ex.PRIMARY]
            prim['median'] = prim['mean'] / 2
        with self.assertRaisesRegex(ValueError, 'no longer far above the median'):
            build(self.forged_forenzo(release=no_tail))

    def test_null_stays_null(self):
        def number(r):
            r['visits']['Day_80']['counts']['delivered'] = 72000
        with self.assertRaisesRegex(ValueError, 'a null became a number'):
            build(self.forged_rsvp(release=number))
        p = build(MANIFEST)['results'][FORENZO]
        for c in p['cohorts'].values():
            for a in c['arms'].values():
                for k in ('pearson_x', 'pearson_y'):
                    self.assertEqual([a['source_mean']['secondary'][k][x] for x in ('mean', 'interval_95', 'records_defined')],
                                     [None, None, 0])

        def zero(r):
            r['cohorts']['Main']['arms'][DISP]['methods']['source_mean_comparator']['pearson_x'] = {
                'n': 0, 'reason': 'no_defined_values', 'summary': None, 'mean': 0.0}
        p = build(self.forged_forenzo(release=zero))['results'][FORENZO]
        self.assertIsNone(p['cohorts']['Main']['arms'][DISP]['source_mean']['secondary']['pearson_x']['mean'])

    def test_counts_are_whole_people_over_the_cohort(self):
        def fraction(r):
            r['contrast']['decline_at_most_minus_0_05_fraction'] = 0.5
        with self.assertRaisesRegex(ValueError, 'the decline share'):
            build(self.forged_rsvp(release=fraction))

        def holds(r):
            r['cohorts']['Main']['arms'][VEL]['score_pass_participants'] = 8
        with self.assertRaisesRegex(ValueError, 'not every admitted record scored'):
            build(self.forged_forenzo(release=holds))

    def test_the_printed_figures_must_be_the_handoffs(self):
        def nudge(r):
            v = r['visits']['Day_7']
            v['metrics']['average_precision']['mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'the handoff does not state'):
            build(self.forged_rsvp(release=nudge))

    # ------------------------------------------------------------------ rights
    def test_the_rights_records(self):
        p = build(MANIFEST)['datasets']
        self.assertEqual({d: x['rights']['license'] for d, x in p.items()},
                         {'wbcic-shu': 'CC BY 4.0', 'longitudinal-rsvp': 'CC0-1.0', 'forenzo-continuous-tracking': 'CC BY 4.0'})
        for d, x in p.items():
            ce = x['consent_and_ethics']
            self.assertTrue(ce['ethics_approval']['stated'] and ce['informed_consent']['stated'], d)
            self.assertIn('not endorsed by the authors', x['rights']['attribution'])
        self.assertIn('20190002', p['wbcic-shu']['consent_and_ethics']['ethics_approval']['quote'])
        self.assertIn('20230058', p['longitudinal-rsvp']['consent_and_ethics']['ethics_approval']['quote'])
        self.assertIn('Carnegie Mellon University', p['forenzo-continuous-tracking']['consent_and_ethics']['ethics_approval']['quote'])
        self.assertIn('Jenn Shanahan', p['forenzo-continuous-tracking']['rights']['attribution'], 'the requested citation')

    def test_a_statement_needs_its_quote_in_the_paper(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'longitudinal-rsvp')['consentEthics']['quotes'][1]['text'] = 'gave broad consent to public sharing'
        with self.assertRaisesRegex(ValueError, 'the consent statement has no quote in the paper'):
            build(manifest)

    def test_the_licence_must_be_the_repositorys(self):
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'forenzo-continuous-tracking')['license'] = 'CC0-1.0'
        with self.assertRaisesRegex(ValueError, 'another licence'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        dataset(manifest, 'wbcic-shu')['consentEthics']['record'] = dataset(manifest, 'longitudinal-rsvp')['consentEthics']['record']
        with self.assertRaisesRegex(ValueError, 'another paper'):
            build(manifest)

    def test_only_an_aggregate_decision_is_exported(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, RSVP)['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(manifest)

    def test_holds_carry_no_figure(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest['holds'] = [{'id': 'x', 'statement': 'no score exists', 'reason': 'it scored 0.61', 'scope': 'x'}]
        with self.assertRaisesRegex(ValueError, 'carries a figure'):
            build(manifest)

    # ------------------------------------------------------------------ what stays out
    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('minimum', 'maximum', 'median', 'p10', 'p90', 'worst_change', 'thresholds', 'predictions',
                    'probabilities', 'features', 'confusion_aggregate', 'per_class_recall', 'recorded_decoder_strata',
                    'resources', 'production_pipeline_wall_seconds', 'maximum_child_peak_rss_bytes', 'record_ids',
                    'private_audit', 'participant_id', 'basename', 'audit_path'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('S12.mat', 'file S3', 'sub-07', 'archive.zip', '/Volumes/disk/x', '/Users/someone/x', 'on Gal4'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_a_median_only_where_the_handoff_requires_it(self):
        ok = {'results': {FORENZO: {'cohorts': {'Main': {'arms': {VEL: {'ridge': {'primary': {'median': 1.3}}}}}}}}}
        ex.scrub_check(ok)
        for where in ({'results': {FORENZO: {'cohorts': {'Main': {'arms': {VEL: {'source_mean': {'primary': {'median': 1.2}}}}}}}}},
                      {'results': {FORENZO: {'cohorts': {'Main': {'arms': {VEL: {'paired': {'median': 0.03}}}}}}}},
                      {'results': {RSVP: {'visits': [{'auroc': {'median': 0.89}}]}}}):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check(where)

    def test_per_person_values_stay_out_by_value(self):
        payload = build(MANIFEST)
        published = set(ex.numbers(payload))
        private = set()
        for s in MANIFEST['sources']:
            private |= {v for _, v in au.private_stats(load(s['release']))}
        allowed = {a['ridge']['primary']['median'] for c in payload['results'][FORENZO]['cohorts'].values()
                   for a in c['arms'].values()}
        self.assertEqual(len(allowed), 4)
        self.assertFalse((private - allowed) & published)

        def leak(r):  # a published mean that happens to be one record's minimum
            prim = r['cohorts']['Transfer Learning']['arms'][DISP]['methods']['source_mean_comparator'][ex.PRIMARY]
            prim['minimum'] = prim['mean']
        with self.assertRaisesRegex(ValueError, 'per-record value'):
            build(self.forged_forenzo(release=leak))

    def test_no_version_label_or_update_marker_in_the_text(self):
        for text in ('the v9 rows', 'frozen encoders (v9)', 'updated 8 October 2026', 'Added 2026-10-08: x',
                     'in this update', 'run on 2026-10-04'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        ex.scrub_check({'results': {'x': {'source': 'doi:10.25452/figshare.plus.22671172.v5, version 5'}}})
        text = json.dumps({k: v for k, v in build(MANIFEST).items() if k not in ('schema_version', 'release_id')})
        self.assertFalse(re.search(r'(?<![./\w-])v\d+\b', text))

    def test_unsupported_claims_appear_only_negated(self):
        for sentence in ('The ridge supports online control.', 'This decodes intended motion.',
                         'Pretraining caused the gain.', 'A zero-shot result.'):
            with self.assertRaises(ValueError, msg=sentence):
                ex.claims_negated({'results': {'x': {'reading': sentence}}})
        ex.claims_negated({'results': {'x': {'reading': 'Not online control; it does not show that pretraining caused it.'}}})
        text = json.dumps(build(MANIFEST)['results'])
        self.assertNotIn('Jev', text)

    def test_prose_numerals_come_from_the_pinned_sources(self):
        with self.assertRaisesRegex(ValueError, 'in no pinned handoff or release'):
            ex.written_from({'reading': 'about 7.3 points higher'}, ('a 4.30 point gain',), 'x')
        ex.written_from({'reading': 'a 4.30 point gain', 'rights': '7.3'}, ('4.30',), 'x')

    def test_no_private_path_or_identifier_reaches_the_files(self):
        text = json.dumps(build(MANIFEST), ensure_ascii=False)
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', 'Gal4', '.mat', '.zip', 'S1.', 'sub-'):
            self.assertNotIn(token, text)
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/'):
                self.assertNotIn(token, body, f'{path.name}: {token}')

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
            p['results'][RSVP]['visits'][1]['auroc']['mean'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'auroc'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            p['results'][FORENZO]['cohorts']['Main']['arms'][VEL]['ridge']['primary']['p90'] = 345.1
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['results'][CPU]['cohorts']['2C']['arms']['source_prior']['macro_f1']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_and_a_wrong_flag(self):
        def zero(p):
            p['results'][RSVP]['visits'][0]['delivered_events'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def flag(p):
            p['results'][FM]['cohorts']['3C']['paired']['interval_excludes_zero'] = False
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'flag'):
            au.audit()

    def test_the_audit_catches_a_per_person_value(self):
        rel = load(source(MANIFEST, RSVP)['release'])
        median = rel['visits']['Day_7']['metrics']['auroc']['median']

        def edit(p):
            p['results'][RSVP]['visits'][0]['auroc']['mean'] = median
        with self.served(edit), self.assertRaises(au.AuditFailure):
            au.audit()


if __name__ == '__main__':
    unittest.main()
