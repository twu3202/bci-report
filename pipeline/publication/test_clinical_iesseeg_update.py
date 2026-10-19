"""The IESSEEG clinical release: what must follow from the pinned exports and records, and what must stay out."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_clinical_iesseeg_export as au
import export_clinical_iesseeg_update as ex
from export_snapshot import validate_public

MANIFEST = json.loads(ex.MANIFEST.read_bytes())


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pct2(x):
    return f'{100 * x:.2f}'


def arm(payload, study, arm_id):
    return next(a for a in payload[study]['arms'] if a['id'] == arm_id)


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class ClinicalIesseegBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build(MANIFEST)
        cls.docs = ex.load(MANIFEST)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    # ------------------------------------------------------------------ forged inputs, re-pinned
    def get(self, ref):
        return json.loads((ex.PROJECT / ref['path']).read_bytes())

    def put(self, ref, obj, text=None):
        """Write an edited copy under the temporary root and re-pin the manifest's reference to it."""
        data = text.encode() if text is not None else json.dumps(obj).encode()
        path = Path(self.tmp.name) / f'{len(list(Path(self.tmp.name).iterdir()))}-{Path(ref["path"]).name}'
        path.write_bytes(data)
        ref['path'], ref['sha256'] = str(path), digest(data)
        return ref['sha256']

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
        self.assertEqual(audit['figures_compared'], audit['copied_exactly'] + audit['recomputed'] + audit['nulls_kept'])

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-clinical-iesseeg-update-v1')
        self.assertEqual(p['release_id'], 'clinical-iesseeg-update-20261020')
        self.assertEqual(p['generated_at'], '2026-10-20')
        self.assertEqual([a['id'] for a in p['controls']['arms']],
                         ['SOURCE_PRIOR', 'AGE', 'ACQUISITION_METADATA', 'EEG', 'EEG_PLUS_AGE', 'AGE_RESIDUAL_EEG'])
        self.assertEqual([a['id'] for a in p['neurolm']['arms']],
                         ['TOKENIZER', 'TOKENIZER_AGE_RESIDUAL', 'GPT_HIDDEN', 'GPT_HIDDEN_AGE_RESIDUAL'])
        self.assertIs(p['medical_disclaimer'], True)
        self.assertEqual(p['counts'], {'new_canonical_datasets': 0, 'new_model_identity': False, 'new_dataset_pages': 0})
        self.assertEqual(p['placement']['page'], '/topics/clinical-groups/')
        self.assertEqual(p['placement']['subsections'], ['iesseeg-controls', 'iesseeg-neurolm'])
        self.assertIs(p['placement']['leaderboard'], False)
        self.assertIs(p['placement']['dataset_page'], False)
        self.assertEqual(p['controls']['title'], 'Age and acquisition controls for an awake EEG case-control pilot')
        self.assertEqual(p['neurolm']['title'], 'Do frozen EEG representations survive age controls?')
        self.assertEqual(p['holds'], [])
        self.assertEqual(set(p['provenance']['source_export_sha256']), {'controls', 'neurolm'})

    def test_every_score_is_the_approved_export_verbatim(self):
        cpu = self.get(MANIFEST['sources']['controlsExport'])['arms']
        neu = self.get(MANIFEST['sources']['neurolmExport'])['scores']
        for study, source in (('controls', cpu), ('neurolm', neu)):
            for a in self.payload[study]['arms']:
                for block in ('pooled', 'age_le_2'):
                    self.assertEqual(json.dumps(a[block]), json.dumps(source[a['id']][block]), (study, a['id'], block))
        # Stored values stay as stored: the site rounds at display.
        self.assertEqual(arm(self.payload, 'controls', 'AGE_RESIDUAL_EEG')['pooled']['balanced_accuracy'],
                         0.6699999999999999)
        self.assertEqual(arm(self.payload, 'controls', 'EEG')['pooled']['auroc'], 0.8236)

    def test_the_figures_the_handoffs_print(self):
        want = {'SOURCE_PRIOR': ('50.00', 0.5, '50.00'), 'AGE': ('68.00', 0.621, '50.00'),
                'ACQUISITION_METADATA': ('61.00', 0.5242, '69.23'), 'EEG': ('81.00', 0.8236, '76.56'),
                'EEG_PLUS_AGE': ('80.00', 0.8432, '73.90'), 'AGE_RESIDUAL_EEG': ('67.00', 0.7028, '69.41'),
                'TOKENIZER': ('77.00', 0.9012, '73.90'), 'TOKENIZER_AGE_RESIDUAL': ('72.00', 0.7976, '71.34'),
                'GPT_HIDDEN': ('84.00', 0.9024, '84.43'), 'GPT_HIDDEN_AGE_RESIDUAL': ('71.00', 0.7936, '75.92')}
        for a in self.payload['controls']['arms'] + self.payload['neurolm']['arms']:
            ba, auroc, young = want[a['id']]
            self.assertEqual((pct2(a['pooled']['balanced_accuracy']), round(a['pooled']['auroc'], 4),
                              pct2(a['age_le_2']['balanced_accuracy'])), (ba, auroc, young), a['id'])
        self.assertEqual(arm(self.payload, 'controls', 'SOURCE_PRIOR')['pooled']['f1'], 0.6666666666666666)
        self.assertIs(self.payload['display']['f1_headline'], False)
        self.assertNotIn('f1', [c['metric'] for c in self.payload['display']['columns']])
        self.assertEqual([(c['block'], c['metric']) for c in self.payload['display']['columns']],
                         [('pooled', 'balanced_accuracy'), ('pooled', 'auroc'), ('age_le_2', 'balanced_accuracy')])
        self.assertIsNone(self.payload['display']['interval'])

    def test_the_controls_are_marked_as_controls(self):
        flags = {a['id']: (a['eeg_input'], a['excluded_from_model_comparisons'])
                 for a in self.payload['controls']['arms'] + self.payload['neurolm']['arms']}
        for a in ('SOURCE_PRIOR', 'AGE', 'ACQUISITION_METADATA'):
            self.assertEqual(flags[a], (False, True), a)
        for a in ('EEG', 'EEG_PLUS_AGE', 'AGE_RESIDUAL_EEG', 'TOKENIZER', 'GPT_HIDDEN'):
            self.assertEqual(flags[a], (True, False), a)
        self.assertEqual(arm(self.payload, 'controls', 'ACQUISITION_METADATA')['role'], 'diagnostic_control')
        self.assertEqual(arm(self.payload, 'controls', 'AGE_RESIDUAL_EEG')['role'], 'sensitivity_analysis')

    def test_the_cohort_and_input_qc(self):
        c, q = self.payload['cohort'], self.payload['input_qc']
        self.assertEqual((c['people'], c['cases'], c['controls'], c['folds'], c['train_people'], c['held_out_people'],
                          c['held_out_cases'], c['held_out_controls'], c['seconds_analysed'], c['channels']),
                         (100, 50, 50, 5, 80, 20, 10, 10, 60, 17))
        self.assertEqual((q['assets'], q['bytes'], q['recordings'], q['recordings_passed'], q['recordings_held'],
                          q['recordings_with_gaps']), (300, 2884494142, 100, 100, 0, 0))
        self.assertEqual(q['scalp_channels'], [{'channels': 19, 'recordings': 59}, {'channels': 17, 'recordings': 41}])
        self.assertEqual(q['sampling_hz'], [{'hz': 200, 'recordings': 98}, {'hz': 2000, 'recordings': 2}])
        self.assertEqual(self.payload['provenance']['cohort_qc_audit_sha256'],
                         '4bc7b3a9f1cd58da968d2555fae5f14011a721de2903880a6dd3ebb324eb30ca')

    def test_the_age_band_is_published_as_approved(self):
        b = self.payload['age_band']
        self.assertEqual((b['maximum_age_years'], b['people'], b['cases'], b['controls']), (2, 68, 42, 26))
        self.assertIs(b['same_predictions'], True)
        self.assertIs(b['refit'], False)
        for a in self.payload['controls']['arms'] + self.payload['neurolm']['arms']:
            tn, fp, fn, tp = a['age_le_2']['confusion_tn_fp_fn_tp']
            self.assertEqual((a['age_le_2']['n'], tp + fn, tn + fp), (68, 42, 26), a['id'])
        self.assertIn('age means and sex counts stay unpublished', b['note'])

    def test_the_neurolm_boundary_and_caveats(self):
        n = self.payload['neurolm']
        self.assertEqual(n['model']['checkpoint_stage'], 'unknown')
        self.assertEqual(n['model']['pretraining_exposure'], 'unknown')
        self.assertIs(n['model']['weights_updated'], False)
        self.assertIs(n['model']['redistributed'], False)
        self.assertEqual(n['model']['text_tokens'], 0)
        self.assertIs(n['audit']['real_neural_features_independently_recomputed'], False)
        self.assertEqual((n['method']['bandpass_hz'], n['method']['notch_hz'], n['method']['amplitude_divisor'],
                          n['method']['windows'], n['method']['tokens_per_window'], n['method']['dimensions']),
                         ([0.1, 75], [50, 60], 100, 15, 68, 768))
        self.assertIn('not re-extracted by a second implementation', self.payload['audit_boundary'])
        self.assertIn('training stage and its prior exposure to these participants are unknown', n['footnote'])
        self.assertNotIn('licence', json.dumps(n['model']))

    def test_attribution_comes_from_the_release_card_only(self):
        d = self.payload['dataset']
        readme = (ex.PROJECT / MANIFEST['sources']['releaseCard']['path']).read_text()
        self.assertIn(f'Please cite **{d["requested_citation"].split(" Towards")[0]}', readme)
        self.assertEqual(d['requested_citation'],
                         'IESSEEG: An Open EEG Dataset Towards Better Understanding of Infantile Epileptic Spasms Syndrome')
        self.assertEqual((d['licence'], d['revision']), ('CC-BY-4.0', '1c32ee3a425a324808a9d275b60ce85625af35c8'))
        self.assertEqual(d['prior_reuse']['case_segments'], 400)
        self.assertEqual(d['prior_reuse']['study'], 'Rajaraman et al. (2024)')
        self.assertIn(d['ethics_as_stated']['quote'], re.sub(r'\s+', ' ', readme))
        body = ex.OUTPUTS[0].read_text()
        for word in ('ICLR', 'OpenReview', 'NeurIPS', 'submission', 'conference', 'datasets-and-benchmarks'):
            self.assertNotIn(word.lower(), body.lower(), word)
        self.assertNotIn('55%', body)

    def test_the_medical_disclaimer_is_reused_and_the_released_file_keeps_its_bytes(self):
        ref = MANIFEST['published']['clinical']
        for path in (ex.PROJECT / ref['path'], ex.PROJECT / 'site/public/data/clinical-update.json'):
            self.assertEqual(digest(path.read_bytes()), ref['sha256'], path.name)
        clinical = self.get(ref)
        self.assertIn('Not a diagnosis', clinical['medical_disclaimer'])
        self.assertEqual(self.payload['medical_disclaimer_wording'], {'file': 'clinical-update.json',
                                                                      'field': 'medical_disclaimer'})

    def test_the_payload_passes_the_public_boundary(self):
        validate_public(self.payload)

    # ------------------------------------------------------------------ refusals
    def test_a_changed_input_byte_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['sources']['cohortQcAudit']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned'):
            build(m)

    def test_an_export_the_review_does_not_bind_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        e = self.get(m['sources']['controlsExport'])
        e['arms']['EEG']['pooled']['balanced_accuracy'] = 0.82
        self.put(m['sources']['controlsExport'], e)
        with self.assertRaisesRegex(ValueError, 'binds another export'):
            build(m)

    def test_a_score_that_is_not_the_numerical_audits_is_refused(self):
        # Even with the review forged to bind the edited export, the independent audit's value decides.
        m = copy.deepcopy(MANIFEST)
        e = self.get(m['sources']['neurolmExport'])
        e['scores']['GPT_HIDDEN']['pooled']['auroc'] = 0.95
        new = self.put(m['sources']['neurolmExport'], e)
        r = self.get(m['sources']['neurolmReleaseReview'])
        r['export_sha256'] = new
        self.put(m['sources']['neurolmReleaseReview'], r)
        with self.assertRaisesRegex(ValueError, 'independent numerical audit differ'):
            build(m)

    def test_confusion_counts_must_give_the_threshold_metrics(self):
        block = copy.deepcopy(self.get(MANIFEST['sources']['controlsExport'])['arms']['EEG']['pooled'])
        ex.score_block(block, copy.deepcopy(block), (100, 50, 50), 'EEG')
        bad = dict(block, sensitivity=0.8)
        with self.assertRaisesRegex(ValueError, 'sensitivity'):
            ex.score_block(bad, copy.deepcopy(bad), (100, 50, 50), 'EEG')
        with self.assertRaisesRegex(ValueError, 'not this cohort'):
            ex.score_block(block, copy.deepcopy(block), (100, 49, 51), 'EEG')

    def test_a_review_that_does_not_approve_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        r = self.get(m['sources']['controlsReleaseReview'])
        r['decision'] = 'withhold'
        self.put(m['sources']['controlsReleaseReview'], r)
        with self.assertRaisesRegex(ValueError, 'does not approve'):
            build(m)

    def test_a_resolved_checkpoint_exposure_stops_the_build(self):
        m = copy.deepcopy(MANIFEST)
        r = self.get(m['sources']['neurolmReleaseReview'])
        r['provenance']['checkpoint_instruction_stage_and_participant_exposure_unverified'] = False
        self.put(m['sources']['neurolmReleaseReview'], r)
        with self.assertRaisesRegex(ValueError, 'no longer unverified'):
            build(m)

    def test_cohort_qc_figures_must_be_stated_in_the_bound_handoff(self):
        m = copy.deepcopy(MANIFEST)
        q = self.get(m['sources']['cohortQcAudit'])
        q['payload_bytes_verified'] += 1
        self.put(m['sources']['cohortQcAudit'], q)
        with self.assertRaisesRegex(ValueError, 'CPU handoff QC'):
            build(m)

    def test_a_changed_owner_decision_stops_the_build(self):
        decisions = json.loads((ex.PROJECT / MANIFEST['approval']['ownerDecisions']['path']).read_bytes())
        d = copy.deepcopy(decisions)
        d['decisions']['defaults_stated_to_owner_and_not_objected']['D7'] = 'IESSEEG age <=2 column dropped (option B)'
        path = Path(self.tmp.name) / 'owner-decisions.json'
        path.write_text(json.dumps(d))
        m = copy.deepcopy(MANIFEST)
        m['approval']['ownerDecisions']['path'] = str(path)
        with self.assertRaisesRegex(ValueError, 'owner decision D7 changed'):
            build(m)
        m['approval']['ownerDecisions']['quoted']['D7'] = 'IESSEEG age <=2 column dropped (option B)'
        with self.assertRaisesRegex(ValueError, 'do not publish this section as approved'):
            build(m)

    def test_a_declared_edit_or_a_hold_is_refused(self):
        m = copy.deepcopy(MANIFEST)
        m['approval']['declaredEdits'] = ['drop the age <=2 fields']
        with self.assertRaisesRegex(ValueError, 'without edits'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['holds'] = [{'id': 'x'}]
        with self.assertRaisesRegex(ValueError, 'no hold'):
            build(m)

    def test_demographic_per_fold_and_per_person_fields_are_refused(self):
        for key in ('age_mean', 'mean_years', 'median_years', 'quartiles_years', 'sex_counts', 'gender', 'age',
                    'per_fold', 'participant_id', 'patient_id', 'features', 'predictions', 'threshold', 'median',
                    'elapsed_seconds', 'private_root'):
            with self.assertRaisesRegex(ValueError, 'refused field'):
                ex.scrub_check({'cohort': [{key: 1}]})

    def test_withheld_values_are_absent(self):
        approved = set(ex.floats([a[b] for a in self.payload['controls']['arms'] + self.payload['neurolm']['arms']
                                  for b in ('pooled', 'age_le_2')]))
        withheld = ex.withheld_values(self.docs, approved)
        self.assertGreaterEqual(len(withheld), 20)
        self.assertFalse(withheld & set(ex.floats(self.payload)))
        self.assertIn(1.596, withheld)     # a per-group mean age, refused by value
        body = ex.OUTPUTS[0].read_text()
        for s in ex.age_summary_strings(self.docs):
            self.assertNotIn(s, body)

    def test_text_rules(self):
        private = ex.private_names(self.docs)
        self.assertGreaterEqual(len(private), 3)
        base = {'schema_version': 'x', 'release_id': 'x'}
        for bad, why in (({'scope': 'the v2 cohort'}, 'version label'), ({'scope': 'run in October'}, 'month'),
                         ({'scope': 'Added with new arms.'}, 'update marker'), ({'scope': 'Jev reads it.'}, 'Jev'),
                         ({'scope': 'Reported in an ICLR paper.'}, 'submission'),
                         ({'scope': 'Under review as a conference submission.'}, 'submission'),
                         ({'scope': 'A descriptive subgroup, not a benchmark.'}, 'hedge'),
                         ({'scope': 'GPT hidden states are the best arm.'}, 'unsupported claim'),
                         ({'scope': 'Useful for clinical screening.'}, 'unsupported claim'),
                         ({'scope': 'see sub-07 there'}, 'participant identifier'),
                         ({'scope': 'a /' + 'home/x/y path'}, 'private path'),
                         ({'scope': f'kept on {sorted(private)[0]} only'}, 'private host')):
            with self.assertRaisesRegex(ValueError, why):
                ex.prose_check({**base, **bad}, private)
        ex.prose_check({**base, 'scope': 'There is no external or clinical validation.'}, private)
        ex.prose_check({**base, 'placement': '/topics/clinical-groups/', 'file': 'clinical-update.json'}, private)

    def test_no_private_path_or_name_reaches_the_files(self):
        private = ex.private_names(self.docs)
        for path in (*ex.OUTPUTS, ex.MANIFEST, ex.EXPORT_AUDIT):
            body = path.read_text()
            self.assertIsNone(ex.LOCAL_ROOTS.search(body), path.name)
            for n in private:
                self.assertIsNone(re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', body, re.I),
                                  f'{n} in {path.name}')

    # ------------------------------------------------------------------ the independent audit
    def test_the_audit_catches_a_changed_figure(self):
        def edit(p):
            arm(p, 'controls', 'EEG')['pooled']['auroc'] += 1e-12
        with self.served(edit), self.assertRaisesRegex(au.AuditFailure, 'controls/arms/3/pooled/auroc'):
            au.audit()

    def test_the_audit_catches_an_unaudited_or_missing_figure(self):
        def extra(p):
            arm(p, 'neurolm', 'GPT_HIDDEN')['pooled']['median_balanced_accuracy'] = 0.84
        with self.served(extra), self.assertRaisesRegex(au.AuditFailure, 'no audit rule'):
            au.audit()

        def missing(p):
            del p['neurolm']['audit']['refit_error']
        with self.served(missing), self.assertRaisesRegex(au.AuditFailure, 'missing'):
            au.audit()

    def test_the_audit_catches_a_null_made_zero_a_type_change_and_a_changed_count(self):
        def zero(p):
            p['display']['interval'] = 0
        with self.served(zero), self.assertRaisesRegex(au.AuditFailure, 'a null became'):
            au.audit()

        def typed(p):
            p['input_qc']['assets'] = 300.0
        with self.served(typed), self.assertRaisesRegex(au.AuditFailure, 'input_qc/assets'):
            au.audit()

        def band(p):
            p['age_band']['cases'] = 41
        with self.served(band), self.assertRaisesRegex(au.AuditFailure, 'age_band/cases'):
            au.audit()

        def flag(p):
            arm(p, 'controls', 'AGE')['excluded_from_model_comparisons'] = False
        with self.served(flag), self.assertRaisesRegex(au.AuditFailure, 'excluded_from_model_comparisons'):
            au.audit()

    def test_the_audit_catches_a_withheld_value_and_a_changed_string(self):
        secret = sorted(au.withheld(au.sources(MANIFEST)))

        def leak(p):
            p['controls']['method']['welch_overlap'] = secret[0]
        with self.served(leak), self.assertRaises(au.AuditFailure):
            au.audit()

        def title(p):
            p['dataset']['requested_citation'] = 'IESSEEG'
        with self.served(title), self.assertRaisesRegex(au.AuditFailure, 'citation'):
            au.audit()

        def stage(p):
            p['neurolm']['model']['pretraining_exposure'] = 'not_exposed'
        with self.served(stage), self.assertRaisesRegex(au.AuditFailure, 'stated as known'):
            au.audit()

    def test_the_audit_catches_two_different_copies(self):
        a, b = Path(self.tmp.name) / 'a.json', Path(self.tmp.name) / 'b.json'
        a.write_bytes(ex.OUTPUTS[0].read_bytes())
        b.write_bytes(ex.OUTPUTS[0].read_bytes() + b' ')
        with mock.patch.object(au, 'SERVED', (a, b)), self.assertRaisesRegex(au.AuditFailure, 'copies differ'):
            au.audit()


if __name__ == '__main__':
    unittest.main()
