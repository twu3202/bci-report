"""The 2026-10-03 large-source batch: what must stay out, and what must follow from the audited release."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import export_large_source_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
DREEM, OPENBMI = ex.DREEM, ex.OPENBMI


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def source(manifest, sid):
    return next(s for s in manifest['sources'] if s['id'] == sid)


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class LargeSourceBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, record, key, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        record[key] = {'path': str(path), 'sha256': digest(data)}
        return digest(data)

    def forged_dreem(self, release=None, audit=None, supplement=None, decision=None, rebind=True):
        """A copy whose release (and audits) were edited, with every hash in the chain re-bound to the edit.

        The release names both audits; the supplement names the audit; the release decision names
        the release, both audits and the handoff. Without `rebind` only the release is rewritten,
        so the decision still names the original bytes: the realistic forgery.
        """
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, DREEM)
        rel, aud, sup, dec = (load(record[k]) for k in ('release', 'numericalAudit', 'supplementaryAudit',
                                                         'releaseDecision'))
        if not rebind:
            release(rel)
            self.write(record, 'release', 'dreem-release.json', json.dumps(rel).encode())
            return manifest
        if audit:
            audit(aud)
        audit_sha = self.write(record, 'numericalAudit', 'dreem-audit.json', json.dumps(aud).encode())
        sup['preserved_prior_audit']['project_report_sha256'] = audit_sha
        if supplement:
            supplement(sup)
        sup_sha = self.write(record, 'supplementaryAudit', 'dreem-supplement.json', json.dumps(sup).encode())
        rel['provenance'].update(independent_result_audit_sha256=audit_sha, supplementary_audit_sha256=sup_sha)
        if release:
            release(rel)
        rel_sha = self.write(record, 'release', 'dreem-release.json', json.dumps(rel).encode())
        dec.update(release_sha256=rel_sha, independent_numeric_audit_sha256=audit_sha, supplementary_audit_sha256=sup_sha)
        if decision:
            decision(dec)
        self.write(record, 'releaseDecision', 'dreem-decision.json', json.dumps(dec).encode())
        return manifest

    def forged_openbmi(self, metrics=None, release=None, aggregate=None, audit=None, rebind=True):
        """A copy whose release (and aggregate) were edited, the hash chain re-bound.

        `metrics` edits the release's metric blocks and the aggregate's identically, so the
        value-for-value gate passes and the logic gates are what is exercised.
        """
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, OPENBMI)
        rel, agg, aud, dec = (load(record[k]) for k in ('release', 'sourceAggregate', 'numericalAudit',
                                                         'releaseDecision'))
        if metrics:
            metrics(rel['metrics'])
            metrics({k: agg[k] for k in rel['metrics']})
        if not rebind:
            if release:
                release(rel)
            self.write(record, 'release', 'openbmi-release.json', json.dumps(rel).encode())
            return manifest
        if aggregate:
            aggregate(agg)
        agg_sha = self.write(record, 'sourceAggregate', 'openbmi-aggregate.json', json.dumps(agg).encode())
        aud['expanded_aggregate_sha256'] = agg_sha
        if audit:
            audit(aud)
        aud_sha = self.write(record, 'numericalAudit', 'openbmi-audit.json', json.dumps(aud).encode())
        rel['provenance'].update(source_aggregate_sha256=agg_sha, independent_result_audit_sha256=aud_sha)
        if release:
            release(rel)
        rel_sha = self.write(record, 'release', 'openbmi-release.json', json.dumps(rel).encode())
        dec['website_release']['sha256'] = rel_sha
        dec.update(aggregate_sha256=agg_sha, audit_sha256=aud_sha)
        self.write(record, 'releaseDecision', 'openbmi-decision.json', json.dumps(dec).encode())
        return manifest

    # ------------------------------------------------------------------ the build itself
    def test_the_published_file_is_the_reviewed_build(self):
        data = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helpers_themselves_build(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged_dreem())
        build(self.forged_openbmi())

    def test_the_shape(self):
        payload = build(MANIFEST)
        self.assertEqual(payload['schema_version'], 'bci-report-large-source-update-v1')
        self.assertEqual(list(payload['results']), [DREEM, OPENBMI])
        self.assertEqual(payload['status_only'], [])
        self.assertEqual([h['id'] for h in payload['holds']], ['dreem-amplitude-sensitive-models'])
        self.assertEqual(payload['provenance']['included'], [DREEM, OPENBMI])

    # ------------------------------------------------------------------ the figures the pages print
    def test_the_dreem_handoff_figures(self):
        d = build(MANIFEST)['results'][DREEM]
        pct = lambda b: (round(100 * b['mean'], 2), [round(100 * v, 2) for v in b['interval_95']])
        want = {
            ('DOD-H', 'training_prior'): ((47.97, [44.56, 51.40]), (20.20, [20.00, 20.60]), (13.01, [12.28, 13.76])),
            ('DOD-H', 'spectral_ridge'): ((72.27, [67.78, 76.28]), (56.67, [53.06, 60.01]), (53.26, [48.98, 57.34])),
            ('DOD-O', 'training_prior'): ((49.23, [46.26, 52.21]), (20.52, [20.09, 21.15]), (13.33, [12.75, 13.92])),
            ('DOD-O', 'spectral_ridge'): ((72.48, [69.70, 75.03]), (49.28, [47.31, 51.23]), (47.37, [44.94, 49.71])),
        }
        for (c, arm), figures in want.items():
            a = d['cohorts'][c]['arms'][arm]
            self.assertEqual(tuple(pct(a[m]) for m in ('accuracy', 'balanced_accuracy', 'macro_f1')), figures, (c, arm))
        for c, gain in (('DOD-H', (36.47, [32.94, 39.78])), ('DOD-O', (28.76, [26.73, 30.72]))):
            self.assertEqual(pct(d['cohorts'][c]['paired_balanced_accuracy']), gain, c)
            self.assertIs(d['cohorts'][c]['paired_balanced_accuracy']['interval_excludes_zero'], True)
        self.assertEqual([round(d['cohorts'][c]['arms']['spectral_ridge']['cohen_kappa']['mean'], 4)
                          for c in ('DOD-H', 'DOD-O')], [0.5839, 0.5418])

    def test_the_dreem_counts(self):
        d = build(MANIFEST)['results'][DREEM]
        self.assertEqual({c: (v['people'], v['nights'], v['eligible_epochs'], v['folds']) for c, v in d['cohorts'].items()},
                         {'DOD-H': (25, 25, 24662, 5), 'DOD-O': (55, 55, 53161, 5)})
        self.assertEqual(d['epoch_accounting'], {'total': 77901, 'unscored': 3, 'zero_or_invalid_channel_scale': 75,
                                                 'eligible': 77823})
        self.assertEqual((d['record_accounting']['archive_records'], d['record_accounting']['excluded_before_scoring'],
                          d['record_accounting']['evaluated']), (81, 1, 80))
        self.assertEqual(d['jobs']['trained'], 20)
        for c, v in d['cohorts'].items():
            self.assertEqual(sum(v['stage_support_epochs'].values()), v['eligible_epochs'], c)
            self.assertEqual(list(v['stage_support_epochs']), list(ex.STAGES))

    def test_the_openbmi_handoff_figures(self):
        o = build(MANIFEST)['results'][OPENBMI]
        pct = lambda b: (round(100 * b['mean'], 2), [round(100 * v, 2) for v in b['interval_95']])
        arms = {a['id']: a for a in o['arms']}
        lc, ps = arms['log-covariance-lda'], arms['relative-psd-ridge']
        self.assertEqual([pct(e['balanced_accuracy']) for e in lc['by_budget']],
                         [(67.88, [63.58, 72.38]), (69.11, [64.83, 73.52]), (69.24, [65.28, 73.36]), (72.44, [68.87, 76.17])])
        self.assertEqual([pct(e['balanced_accuracy']) for e in ps['by_budget']],
                         [(57.30, [54.35, 60.50]), (57.37, [54.49, 60.51]), (57.93, [55.25, 60.84]), (58.98, [56.03, 62.11])])
        g = {a: next(x for x in arms[a]['calibration_gain'] if x['target_trials'] == 40) for a in arms}
        self.assertEqual(pct(g['log-covariance-lda']['balanced_accuracy_change']), (4.57, [2.34, 6.88]))
        self.assertEqual(pct(g['relative-psd-ridge']['balanced_accuracy_change']), (1.68, [-0.12, 3.54]))
        self.assertEqual([(x['people_with_any_decline'], x['people_with_decline_of_5_points_or_more'], x['people'])
                          for x in g.values()], [(13, 6, 51), (16, 6, 51)])
        self.assertIs(g['log-covariance-lda']['interval_excludes_zero'], True)
        self.assertIs(g['relative-psd-ridge']['interval_excludes_zero'], False)
        self.assertEqual([e['target_trials'] for e in lc['by_budget']], [0, 10, 20, 40])
        self.assertEqual(len(o['between_arms']), 4)

    def test_the_openbmi_counts(self):
        c = build(MANIFEST)['results'][OPENBMI]['cohort']
        self.assertEqual((c['acquisition_identities'], c['engineering_exclusion'], c['input_quality_holds'], c['evaluated']),
                         (54, 1, 2, 51))
        self.assertEqual(c['acquisition_identities'], c['engineering_exclusion'] + c['input_quality_holds'] + c['evaluated'])
        self.assertEqual((c['unique_test_trials'], c['jobs']['trained'], c['original_people'], c['added_people']),
                         (3060, 408, 40, 11))
        self.assertIs(c['independent_replication'], False)

    # ------------------------------------------------------------------ hash chain
    def test_a_changed_input_byte_is_refused(self):
        for sid, keys in ((DREEM, ('handoff', 'release', 'protocol', 'numericalAudit', 'supplementaryAudit',
                                   'releaseDecision', 'scopeReview', 'depositMetadata')),
                          (OPENBMI, ('handoff', 'release', 'sourceAggregate', 'numericalAudit', 'releaseDecision',
                                     'licenseRecord', 'consentRecord'))):
            for key in keys:
                manifest = copy.deepcopy(MANIFEST)
                source(manifest, sid)[key]['sha256'] = '0' * 64
                with self.assertRaises(ValueError, msg=f'{sid}/{key}'):
                    build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, DREEM)['unitStatus']['evidence']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(manifest)

    def test_a_release_the_decision_did_not_name_is_refused(self):
        def nudge(r):
            r['paired']['DOD-H']['metrics']['balanced_accuracy']['interval'][0] = 0.33
        with self.assertRaisesRegex(ValueError, 'release decision names other release bytes'):
            build(self.forged_dreem(release=nudge, rebind=False))

        def nudge_o(m):
            m['cells']['trace_logcov']['0']['balanced_accuracy']['equal_person_mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'release decision names other release bytes'):
            build(self.forged_openbmi(metrics=nudge_o, rebind=False))

    def test_a_failed_audit_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'independent audit did not pass'):
            build(self.forged_dreem(audit=lambda a: a.update(verdict='fail')))
        with self.assertRaisesRegex(ValueError, 'independent audit did not pass'):
            build(self.forged_dreem(audit=lambda a: a.update(blocking_findings=['x'])))
        with self.assertRaisesRegex(ValueError, 'every check'):
            build(self.forged_dreem(audit=lambda a: a['independent_checks'].update(raw_eeg_opened=True)))
        with self.assertRaisesRegex(ValueError, 'supplementary audit did not pass'):
            build(self.forged_dreem(supplement=lambda s: s.update(verdict='fail')))
        with self.assertRaisesRegex(ValueError, 'independent audit did not pass'):
            build(self.forged_openbmi(audit=lambda a: a.update(verdict='fail')))
        with self.assertRaisesRegex(ValueError, 'every check'):
            build(self.forged_openbmi(audit=lambda a: a.update(models_loaded_or_refitted=True)))

    def test_the_audits_must_bind_the_reported_values(self):
        # Dreem: a paired value the independent audit did not compute.
        def drift(r):
            r['paired']['DOD-O']['metrics']['brier']['point_estimate'] -= 0.001
        with self.assertRaisesRegex(ValueError, 'differs from the independent audit'):
            build(self.forged_dreem(release=drift))
        # Dreem: the supplement must supplement this audit, and the two must audit one run.
        with self.assertRaisesRegex(ValueError, 'supplements another audit'):
            build(self.forged_dreem(supplement=lambda s: s['preserved_prior_audit'].update(project_report_sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'different runs'):
            build(self.forged_dreem(supplement=lambda s: s['bindings'].update(activation_sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'protocol identity'):
            build(self.forged_dreem(audit=lambda a: a['bindings'].update(protocol_sha256='0' * 64)))
        # OpenBMI: a release figure that is not the audited aggregate's.
        def other(r):
            r['metrics']['cells']['relative_psd']['40']['macro_f1']['equal_person_mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'differs from the audited aggregate'):
            build(self.forged_openbmi(release=other))
        with self.assertRaisesRegex(ValueError, 'checked a different aggregate'):
            build(self.forged_openbmi(audit=lambda a: a.update(expanded_aggregate_sha256='0' * 64)))

    def test_the_openbmi_aggregate_is_the_sealed_pre_audit_candidate(self):
        # Its stale flags are expected; an aggregate claiming its own release is not the audited candidate.
        with self.assertRaisesRegex(ValueError, 'sealed pre-audit candidate'):
            build(self.forged_openbmi(aggregate=lambda a: a.update(release_authorized=True)))

    # ------------------------------------------------------------------ logic gates
    def test_every_interval_must_contain_its_mean(self):
        def outside(r):
            b = r['strata']['spectral_ridge']['DOD-H']['participant_equal']['accuracy']
            b['interval'] = [b['point_estimate'] + 0.001, b['interval'][1]]
        with self.assertRaisesRegex(ValueError, 'does not contain its mean'):
            build(self.forged_dreem(release=outside))

        def outside_o(m):
            c = m['cells']['trace_logcov']['20']['accuracy']
            c['bootstrap_percentile_95'] = [c['equal_person_mean'] + 0.001, c['bootstrap_percentile_95'][1]]
        with self.assertRaisesRegex(ValueError, 'does not contain its mean'):
            build(self.forged_openbmi(metrics=outside_o))

    def test_null_stays_null(self):
        payload = build(MANIFEST)
        for c in ('DOD-H', 'DOD-O'):
            n1 = next(s for s in payload['results'][DREEM]['cohorts'][c]['arms']['spectral_ridge']['per_stage']
                      if s['stage'] == 'N1')
            self.assertIsNone(n1['precision']['mean'])
            self.assertIsNone(n1['precision']['interval_95'])
            self.assertEqual(n1['precision']['nights_defined'], 0)
        self.assertIn('null', json.dumps(payload['results'][DREEM]))

        def coerced(r):  # an undefined precision turned into zero
            b = r['strata']['spectral_ridge']['DOD-H']['participant_equal']['class_1_precision']
            b['point_estimate'], b['interval'] = 0.0, [0.0, 0.0]
        with self.assertRaisesRegex(ValueError, 'null turned into a number'):
            build(self.forged_dreem(release=coerced))

        def dropped(r):  # a defined value turned into null
            r['strata']['spectral_ridge']['DOD-O']['participant_equal']['class_0_f1']['point_estimate'] = None
        with self.assertRaisesRegex(ValueError, 'null mean'):
            build(self.forged_dreem(release=dropped))

    def test_the_dreem_cohorts_are_25_and_55(self):
        def one_more(r):
            r['evaluation_design']['strata']['DOD-H']['records'] = 26
        with self.assertRaisesRegex(ValueError, 'DOD-H 25 and DOD-O 55'):
            build(self.forged_dreem(release=one_more))

        def accounting(r):
            r['evaluation_design']['source_record_accounting']['publisher_declared_no_consensus_exclusion'] = 2
        with self.assertRaisesRegex(ValueError, '80 evaluated plus 1'):
            build(self.forged_dreem(release=accounting))

        def epochs(r):
            r['evaluation_design']['technical_epoch_accounting']['unscored'] = 4
        with self.assertRaisesRegex(ValueError, 'epoch accounting'):
            build(self.forged_dreem(release=epochs))

        def support(r):
            r['strata']['spectral_ridge']['DOD-O']['epoch_micro']['per_class'][3]['support'] += 1
        with self.assertRaisesRegex(ValueError, 'stage support'):
            build(self.forged_dreem(release=support))

    def test_the_paired_mean_must_be_the_difference_of_the_arms(self):
        def drift(r):
            r['strata']['spectral_ridge']['DOD-O']['participant_equal']['balanced_accuracy']['point_estimate'] += 0.001
        with self.assertRaisesRegex(ValueError, 'paired mean'):
            build(self.forged_dreem(release=drift))

        def drift_o(m):
            m['within_arm_budget_contrasts']['relative_psd']['20_minus_0']['balanced_accuracy']['mean'] += 0.001
        with self.assertRaisesRegex(ValueError, 'paired mean'):
            build(self.forged_openbmi(metrics=drift_o))

    def test_the_dreem_gain_must_exclude_zero_for_the_wording(self):
        def crosses(r):
            b = r['paired']['DOD-H']['metrics']['balanced_accuracy']
            b['interval'] = [-0.01, b['interval'][1]]
        def audited(a):
            a['audited_paired_spectral_ridge_minus_training_prior']['DOD-H']['balanced_accuracy']['interval_95'] = \
                [-0.01, a['audited_paired_spectral_ridge_minus_training_prior']['DOD-H']['balanced_accuracy']['interval_95'][1]]
        with self.assertRaisesRegex(ValueError, 'no longer excludes zero'):
            build(self.forged_dreem(release=crosses, audit=audited))

    def test_the_training_prior_is_the_constant_n2_floor_and_not_a_chance_level(self):
        d = build(MANIFEST)['results'][DREEM]
        text = json.dumps(d)
        self.assertNotIn('chance_level', text)
        for sentence in re.split(r'(?<=[.;])\s+', text):
            if 'chance' in sentence.lower():
                self.assertRegex(sentence, r'\bnot\b')
        with self.assertRaisesRegex(ValueError, 'chance'):
            ex.no_chance_label({'note': 'The prior sits at the chance level.'})
        with self.assertRaisesRegex(ValueError, 'chance'):
            ex.no_chance_label({'arms': {'chance_level': 0.2}})

        def predicts_wake(r):  # a prior that predicts another stage somewhere
            b = r['strata']['training_prior']['DOD-H']['participant_equal']['class_0_precision']
            b.update(defined_record_count=1, missing_record_count=24, missing_reason_counts={'zero_predicted_support': 24})
        with self.assertRaisesRegex(ValueError, 'does not predict N2'):
            build(self.forged_dreem(release=predicts_wake))

    def test_no_cross_cohort_field(self):
        d = build(MANIFEST)['results'][DREEM]
        self.assertEqual(list(d['cohorts']), ['DOD-H', 'DOD-O'])
        keys = set()

        def walk(v):
            if isinstance(v, dict):
                keys.update(k.lower() for k in v)
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(d)
        for fragment in ('combined', 'pooled', 'cross_cohort', 'between_cohorts', 'dod-h_minus', 'difference_between'):
            self.assertFalse([k for k in keys if fragment in k], fragment)
        for key in ('combined_descriptive', 'pooled_mean', 'cross_cohort_difference'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})

    def test_the_openbmi_budgets_are_0_10_20_40(self):
        def other(r):
            r['protocol']['target_adaptation_budgets'] = [0, 10, 20, 30]
        with self.assertRaisesRegex(ValueError, 'budgets'):
            build(self.forged_openbmi(release=other))

    def test_the_openbmi_accounting(self):
        with self.assertRaisesRegex(ValueError, '1 exclusion \\+ 2 holds \\+ 51'):
            build(self.forged_openbmi(release=lambda r: r['dataset'].update(scientific_holds=3)))
        with self.assertRaisesRegex(ValueError, '51 people x 60'):
            build(self.forged_openbmi(release=lambda r: r['protocol'].update(unique_heldout_trials=3000)))
        with self.assertRaisesRegex(ValueError, '51 x 2 arms x 4 budgets'):
            build(self.forged_openbmi(release=lambda r: r['protocol'].update(trained_prediction_jobs=400)))

    def test_decline_counts_are_whole_people_over_the_cohort(self):
        def fraction(m):
            m['within_arm_budget_contrasts']['trace_logcov']['40_minus_0']['balanced_accuracy']['negative_fraction'] = 0.26
        with self.assertRaisesRegex(ValueError, 'not the count over 51'):
            build(self.forged_openbmi(metrics=fraction))

        def not_whole(m):
            x = m['within_arm_budget_contrasts']['relative_psd']['40_minus_0']['balanced_accuracy']
            x['negative_count'], x['negative_fraction'] = 16.5, 16.5 / 51
        with self.assertRaisesRegex(ValueError, 'not a whole count'):
            build(self.forged_openbmi(metrics=not_whole))

        def denominator(m):
            m['between_arm_same_budget_contrasts']['40']['metrics']['balanced_accuracy']['common_defined_count'] = 50
        with self.assertRaisesRegex(ValueError, 'denominator'):
            build(self.forged_openbmi(metrics=denominator))

        def more_large(m):
            x = m['within_arm_budget_contrasts']['trace_logcov']['10_minus_0']['balanced_accuracy']
            x['balanced_accuracy_loss_at_least_0_05_count'], x['balanced_accuracy_loss_at_least_0_05_fraction'] = 22, 22 / 51
        with self.assertRaisesRegex(ValueError, 'more people lost five points'):
            build(self.forged_openbmi(metrics=more_large))

    def test_the_openbmi_wording_is_held_to_the_intervals(self):
        def psd_established(m):
            x = m['within_arm_budget_contrasts']['relative_psd']['40_minus_0']['balanced_accuracy']
            x['bootstrap_percentile_95'] = [0.001, x['bootstrap_percentile_95'][1]]
        with self.assertRaisesRegex(ValueError, 'relative-PSD 40-versus-0 interval no longer includes zero'):
            build(self.forged_openbmi(metrics=psd_established))

        def logcov_not(m):
            x = m['within_arm_budget_contrasts']['trace_logcov']['40_minus_0']['balanced_accuracy']
            x['bootstrap_percentile_95'] = [-0.001, x['bootstrap_percentile_95'][1]]
        with self.assertRaisesRegex(ValueError, 'log-covariance 40-versus-0 interval no longer excludes zero'):
            build(self.forged_openbmi(metrics=logcov_not))

    def test_accuracy_is_a_whole_count_of_test_trials(self):
        def fractional(m):
            c = m['cells']['relative_psd']['10']['accuracy']
            c['equal_person_mean'] += 0.0001
        with self.assertRaisesRegex(ValueError, 'whole count of trials'):
            build(self.forged_openbmi(metrics=fractional))

    def test_the_printed_figures_must_be_the_handoffs(self):
        manifest = copy.deepcopy(MANIFEST)
        record = source(manifest, OPENBMI)
        text = (ex.PROJECT / record['handoff']['path']).read_text(encoding='utf-8').replace('67.88% (63.58', '67.89% (63.58')
        data = text.encode()
        path = Path(self.tmp.name) / 'handoff.md'
        path.write_bytes(data)
        record['handoff'] = {'path': str(path), 'sha256': digest(data)}
        dec = load(record['releaseDecision'])
        dec['handoff']['sha256'] = digest(data)
        self.write(record, 'releaseDecision', 'openbmi-decision.json', json.dumps(dec).encode())
        with self.assertRaisesRegex(ValueError, 'handoff does not state'):
            build(manifest)

    # ------------------------------------------------------------------ rights and consent
    def test_each_cohort_states_what_it_has_and_what_is_missing(self):
        d = build(MANIFEST)['results'][DREEM]['cohorts']
        h, o = d['DOD-H']['consent_and_ethics'], d['DOD-O']['consent_and_ethics']
        self.assertIs(h['ethics_approval']['stated'], True)
        self.assertIn('Committees of Protection of Persons', h['ethics_approval']['quote'])
        self.assertIs(h['informed_consent']['stated'], False)
        self.assertIn('no informed-consent sentence', h['informed_consent']['note'])
        self.assertIs(o['informed_consent']['stated'], True)
        self.assertIn('informed written consent', o['informed_consent']['quote'])
        self.assertIs(o['ethics_approval']['stated'], False)
        self.assertIn('No ethics committee', o['ethics_approval']['note'])
        for entry in (h, o):
            self.assertIn('arXiv:1911.03221v4', entry['read_from'])

    def test_a_statement_needs_its_recorded_quote(self):
        for drop in ('Committees of Protection of Persons', 'informed written consent', 'publicly-available'):
            manifest = copy.deepcopy(MANIFEST)
            for h in source(manifest, DREEM)['decisionHistory']:
                h['quotes'] = [q for q in h.get('quotes', []) if drop not in q['text']]
            with self.assertRaisesRegex(ValueError, 'recorded source quote', msg=drop):
                build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        del source(manifest, DREEM)['consentEthics']['cohorts']['DOD-H']['consentMissing']
        with self.assertRaisesRegex(ValueError, 'does not say so'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)  # recorded as missing, yet quoted
        source(manifest, DREEM)['consentEthics']['cohorts']['DOD-O']['consent'] = None
        source(manifest, DREEM)['consentEthics']['cohorts']['DOD-O']['consentMissing'] = 'none'
        with self.assertRaisesRegex(ValueError, 'quoted but recorded as missing'):
            build(manifest)

    def test_the_rights_records(self):
        payload = build(MANIFEST)
        d, o = payload['results'][DREEM]['rights'], payload['results'][OPENBMI]['rights']
        self.assertEqual((d['license'], o['license']), ('MIT', 'CC0-1.0'))
        self.assertIn('declares', d['licenseScope'])
        self.assertIn('1040548-KUIRB-16-159-A-2', o['privacyReview'])
        for sid in (DREEM, OPENBMI):
            for missing in ('privacyReview', 'reviewBasis', 'attribution', 'licenseUrl'):
                manifest = copy.deepcopy(MANIFEST)
                del source(manifest, sid)[missing]
                with self.assertRaises((ValueError, KeyError), msg=f'{sid}/{missing}'):
                    build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, DREEM)['license'] = 'CC-BY-4.0'
        with self.assertRaisesRegex(ValueError, 'MIT and open access'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, OPENBMI)['license'] = 'GPL-3.0'
        with self.assertRaisesRegex(ValueError, 'not CC0'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, OPENBMI)['attribution'] = source(manifest, OPENBMI)['attribution'].replace('Siamac Fazli and ', '')
        with self.assertRaisesRegex(ValueError, 'omits a creator'):
            build(manifest)

    def test_only_an_aggregate_decision_is_exported(self):
        manifest = copy.deepcopy(MANIFEST)
        source(manifest, OPENBMI)['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(manifest)

    # ------------------------------------------------------------------ what stays out
    def test_holds_carry_no_figure(self):
        payload = build(MANIFEST)
        for h in payload['holds']:
            self.assertFalse(re.search(r'\d', json.dumps(h)), h['id'])
        manifest = copy.deepcopy(MANIFEST)
        manifest['holds'][0]['statement'] = 'An EEGNet run scored 61% and is held.'
        with self.assertRaisesRegex(ValueError, 'carries a figure'):
            build(manifest)
        manifest = copy.deepcopy(MANIFEST)
        manifest['holds'][0]['balanced_accuracy'] = 0.6
        with self.assertRaises(ValueError):
            build(manifest)

    def test_per_person_and_internal_fields_are_refused(self):
        for key in ('minimum', 'maximum', 'median', 'p10', 'worst_observed_change', 'negative_count', 'range',
                    'thresholds', 'predictions', 'probabilities', 'features', 'confusion_matrix', 'per_class',
                    'epoch_micro', 'brier_score', 'nll', 'ece_10_bin', 'per_participant_ba', 'record_ids',
                    'private_audit', 'participant_id', 'basename'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('00000000-1111-2222-3333-444444444444.h5', 'sess01_subj01_EEG_MI.mat', 'folder s12',
                     'host:/mnt/bigdata', '/Volumes/disk/x', '/Users/someone/x', 'record.npz'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})

    def test_per_person_values_stay_out_by_key_and_by_value(self):
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
        for fragment in ('min', 'max', 'median', 'p10', 'worst', 'range', 'threshold', 'prediction', 'private',
                         'feature', 'confusion', 'brier', 'nll', 'ece'):
            self.assertFalse([k for k in keys if fragment in k], fragment)
        release = load(source(MANIFEST, OPENBMI)['release'])['metrics']
        per_person = set()
        for arm in release['within_arm_budget_contrasts'].values():
            for block in arm.values():
                for stats in block.values():
                    per_person |= {stats[k] for k in ('minimum', 'median', 'p10')}
        published = set(ex.numbers(payload['results'][OPENBMI]))
        self.assertFalse(per_person & published)
        self.assertNotIn(-0.1272321428571429, set(ex.numbers(payload)), 'the worst log-covariance change')

        def leak(m):  # a published mean that happens to be one person's worst change
            x = m['within_arm_budget_contrasts']['trace_logcov']['10_minus_0']['balanced_accuracy']
            x['minimum'] = x['mean']
        with self.assertRaisesRegex(ValueError, 'per-person value'):
            build(self.forged_openbmi(metrics=leak))

    def test_no_private_path_or_identifier_reaches_the_files(self):
        payload = build(MANIFEST)
        text = json.dumps(payload, ensure_ascii=False)
        for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '/private/', '.h5', '.mat', 'subj'):
            self.assertNotIn(token, text)
        self.assertFalse(re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text))
        for path in (ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/'):
                self.assertNotIn(token, body, f'{path.name}: {token}')

    def test_the_40_person_snapshot_is_history_only(self):
        payload = build(MANIFEST)
        self.assertEqual(list(payload['results']), [DREEM, OPENBMI])
        o = payload['results'][OPENBMI]
        self.assertIn('never published', o['history'])
        self.assertEqual(o['cohort']['evaluated'], 51)
        self.assertNotIn('40-person', json.dumps(o['arms']) + json.dumps(o['between_arms']))


if __name__ == '__main__':
    unittest.main()
