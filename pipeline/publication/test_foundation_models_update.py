"""The v9 foundation-model batch: what must stay out, and what must follow from the pinned release candidate."""
import copy
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import export_foundation_models_update as ex

MANIFEST = json.loads(ex.MANIFEST.read_bytes())
EV = MANIFEST['evaluation']
RESULT = ex.EVALUATION


def build(manifest):
    return ex.build(json.dumps(manifest).encode())


def load(ref):
    return json.loads((ex.PROJECT / ref['path']).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def at_pointer(doc, pointer):
    toks = [t.replace('~1', '/').replace('~0', '~') for t in pointer.split('/')[1:]]
    node = doc
    for t in toks[:-1]:
        node = node[int(t)] if isinstance(node, list) else node[t]
    return node, (int(toks[-1]) if isinstance(node, list) else toks[-1])


def cell(cand, model, protocol):
    rows = [c for r in cand['matrix_rows'] for c in r['cells']] + cand['masking_ablation_panel']['cells']
    return next(c for c in rows if c['model'] == model and c['protocol'] == protocol)


def adapt(cand, model):
    return next(r for r in cand['eegmat_adaptation']['rows'] if r['model'] == model)


def result(payload):
    return payload['results'][RESULT]


@unittest.skipUnless(ex.inputs_available(), 'pinned research inputs are local-only; see inputs_available()')
class FoundationModelsBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.csvs = build(MANIFEST)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def forged(self, candidate=None, both=None, aggregate=None, audit_status=None, harness=None, handoff=None,
               manifest=None, rebind=True):
        """A copy whose inputs were edited, with every hash in the chain re-bound to the edit.

        `both(cand, sync)` edits a traced block of the candidate; `sync(block)` writes the block's edited value back
        into the file it points at, and into every aggregate block that points at the same place, so re-resolution
        and the aggregate cross-checks pass and the logic gates are what is exercised. Every pinned file is then
        written to a scratch folder under its own name, and each new hash replaces the old one wherever the chain
        records it: the candidate, the aggregate, the handoff and the manifest. Without `rebind` only the candidate
        is rewritten, so the manifest still pins the original bytes.
        """
        m = copy.deepcopy(MANIFEST)
        ev = m['evaluation']
        cand, agg = load(ev['releaseCandidate']), load(ev['aggregate'])
        docs = {Path(r['path']).name: load(r) for r in ev['summaries'].values()}
        docs['pretraining-exposure.json'] = load(ev['pretrainingExposure'])
        status, valid = load(ev['auditStatus']), load(ev['harnessValidation'])
        text = (ex.PROJECT / ev['handoff']['path']).read_text()
        if not rebind:
            if candidate:
                candidate(cand)
            pinned_sha = ev['releaseCandidate']['sha256']
            self.write(ev['releaseCandidate'], 'fm-eval-v9-website-release-candidate.json', json.dumps(cand).encode())
            ev['releaseCandidate']['sha256'] = pinned_sha
            return m

        def sync(block):
            name, pointer = Path(block['src']['file']).name, block['src']['pointer']
            parent, key = at_pointer(docs[name], pointer)
            value = block['value'] if 'value' in block else block['status']
            parent[key] = copy.deepcopy(value)

            def walk(node):
                if isinstance(node, dict):
                    src = node.get('src')
                    if isinstance(src, dict) and Path(src.get('file', '')).name == name and src.get('pointer') == pointer:
                        node['value' if 'value' in node else 'status'] = copy.deepcopy(value)
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(agg)
            walk(cand)
        if both:
            both(cand, sync)
        if aggregate:
            aggregate(agg)
        if audit_status:
            audit_status(status)
        if harness:
            harness(valid)
        swaps = []
        for g, ref in ev['summaries'].items():
            name = Path(ref['path']).name
            swaps.append((ref['sha256'], self.write(ref, name, json.dumps(docs[name]).encode())))
        swaps.append((ev['pretrainingExposure']['sha256'],
                      self.write(ev['pretrainingExposure'], 'pretraining-exposure.json',
                                 json.dumps(docs['pretraining-exposure.json']).encode())))
        swaps.append((ev['auditStatus']['sha256'], self.write(ev['auditStatus'], 'audit-status.json', json.dumps(status).encode())))
        swaps.append((ev['harnessValidation']['sha256'],
                      self.write(ev['harnessValidation'], 'harness-validation.json', json.dumps(valid).encode())))

        def swap(s):
            for old_sha, new_sha in swaps:
                s = s.replace(old_sha, new_sha)
            return s
        cand = json.loads(swap(json.dumps(cand)))
        agg = json.loads(swap(json.dumps(agg)))
        text = swap(text)
        old_agg = ev['aggregate']['sha256']
        new_agg = self.write(ev['aggregate'], 'aggregate.json', json.dumps(agg).encode())
        cand = json.loads(json.dumps(cand).replace(old_agg, new_agg))
        text = text.replace(old_agg, new_agg)
        if candidate:          # last, so an edit to the hashes the candidate records is not re-bound away
            candidate(cand)
        old = ev['releaseCandidate']['sha256']
        new = self.write(ev['releaseCandidate'], 'fm-eval-v9-website-release-candidate.json', json.dumps(cand).encode())
        text = text.replace(old, new)
        if handoff:
            text = handoff(text)
        self.write(ev['handoff'], 'handoff.md', text.encode())
        if manifest:
            manifest(m)
        return m

    def write(self, ref, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        ref.update(path=str(path), sha256=digest(data))
        return digest(data)

    # ------------------------------------------------------------------ the build itself
    def test_the_published_files_are_the_reviewed_build(self):
        data, csvs = ex.serialized_export()
        for out in ex.OUTPUTS:
            self.assertEqual(out.read_bytes(), data)
        for name, body in csvs.items():
            self.assertEqual((ex.CSV_DIR / name).read_bytes(), body, name)
        audit = json.loads(ex.EXPORT_AUDIT.read_text())
        self.assertEqual(audit['export_sha256'], digest(data))
        self.assertEqual(audit['csv_sha256'], {n: digest(b) for n, b in csvs.items()})
        self.assertEqual(audit['manifest_sha256'], digest(ex.MANIFEST.read_bytes()))
        self.assertEqual(audit['release_candidate_sha256'], EV['releaseCandidate']['sha256'])

    def test_the_build_is_deterministic(self):
        self.assertEqual(ex.serialized_export(), ex.serialized_export())

    def test_the_forgery_helper_itself_builds(self):
        # Guards the tests below: an unedited forged copy must pass, so their failures are the edit's.
        build(self.forged())
        build(self.forged(both=lambda c, sync: sync(cell(c, 'reve-base', 'mi-rest')['balanced_accuracy'])))

    def test_the_shape(self):
        p = self.payload
        self.assertEqual(p['schema_version'], 'bci-report-foundation-models-update-v1')
        self.assertEqual(p['release_id'], 'foundation-models-update-20261004')
        self.assertEqual(list(p['results']), [RESULT])
        self.assertEqual((p['status_only'], p['holds']), ([], []))
        r = result(p)
        self.assertEqual([x['id'] for x in r['protocols']], list(ex.PROTOCOLS))
        self.assertEqual([m['id'] for m in r['models']], list(ex.CHECKPOINTS))
        self.assertEqual([m['id'] for m in r['models'] if m['panel'] == 'matrix'], list(ex.MATRIX))
        self.assertEqual([m['id'] for m in r['models'] if m['panel'] == 'masking ablation'], list(ex.ABLATION[1:]))
        self.assertEqual(sum(m['masking_ablation'] for m in r['models']), 4)
        self.assertEqual(len(r['frozen_probe']), 16 * 8)
        self.assertEqual(sorted((c['model'], c['protocol']) for c in r['frozen_probe'] if c['status'] != 'complete'),
                         sorted(ex.NOT_RUN))
        self.assertEqual([x['model'] for x in r['eegmat_adaptation']['rows']], list(ex.ADAPTED))
        self.assertEqual(p['provenance']['inputs'], list(ex.PROTOCOLS))
        self.assertEqual(p['provenance']['references_reresolved'], 1499)
        self.assertEqual(p['provenance']['handoff_rows_checked'], 45)
        self.assertEqual(sorted(self.csvs), sorted(f'foundation-models-{x}.csv' for x in ex.PROTOCOLS))

    # ------------------------------------------------------------------ the figures the pages will print
    def test_the_handoff_figures(self):
        r = result(self.payload)
        c = {(x['model'], x['protocol']): x for x in r['frozen_probe']}
        rel = {(x['model'], x['protocol']): x for x in r['comparisons']['vs_published_rows']}
        f1 = lambda v: ex.fixed(ex.percent(v), 1)
        sleep = c[('steegformer-large', 'sleep-scalp')]
        self.assertEqual((f1(sleep['balanced_accuracy']), f1(sleep['interval_95'][0]), f1(sleep['interval_95'][1])),
                         ('79.6', '78.2', '81.0'))
        # Sleep: three new encoders above every published row; no other protocol has a cell above the best
        # published non-foundation row.
        above_all = sorted(k for k, x in rel.items() if all(x[ref]['relation'] == 'above'
                                                            for ref in ('labram', 'cbramod', 'best_non_foundation')))
        self.assertEqual(above_all, [('reve-large', 'sleep-scalp'), ('steegformer-base', 'sleep-scalp'),
                                     ('steegformer-large', 'sleep-scalp')])
        self.assertEqual(sorted({k[1] for k, x in rel.items() if x['best_non_foundation']['relation'] == 'above'}),
                         ['sleep-scalp'])
        # BETA, eight channels: the masking checkpoints and REVE Large above frozen CBraMod, none above CCA.
        self.assertEqual(sorted(k[0] for k, x in rel.items() if k[1] == 'beta-8ch' and x['cbramod']['relation'] == 'above'),
                         sorted([*ex.ABLATION, 'reve-large']))
        self.assertEqual(rel[('reve-large', 'beta-8ch')]['best_non_foundation']['name'], 'Standard CCA')
        # Exposure flags travel with the cells.
        self.assertEqual(sorted(k for k, x in c.items() if x['exposure']['status'] == 'exposed'), sorted(ex.EXPOSED))
        self.assertTrue(all(x['exposure']['status'] == 'unknown' for k, x in c.items() if k[0] == 'zuna'))
        # Adaptation: the largest paired gains where frozen features are weakest; LoRA budgets 32,768 to 428,032.
        a = {x['model']: x for x in r['eegmat_adaptation']['rows']}
        self.assertEqual(ex.fixed(100 * a['singlem']['paired_lora_minus_frozen']['mean_change'], 2), '9.71')
        self.assertEqual(sorted(m for m, x in a.items() if not x['paired_lora_minus_frozen']['excludes_zero']),
                         ['brainomni-base', 'codebrain', 'eegmamba', 'steegformer-base'])
        self.assertEqual(r['eegmat_adaptation']['lora_parameter_range'], [32768, 428032])
        # Idle: counts of 60, always-abstaining people beside them.
        idle = c[('steegformer-large', 'idle')]
        self.assertEqual((idle['idle_false_activations'], idle['commands_detected'], idle['always_abstain_people']), (1, 20, 1))

    def test_a_tie_prints_as_the_handoff_prints_it_from_the_csv(self):
        # 100 x 0.6325 is 63.24999999999999: from the proportion the page would print 63.2, the handoff 63.3.
        self.assertEqual(ex.fixed(100 * 0.6325, 1), '63.2')
        self.assertEqual(ex.fixed(ex.percent(0.6325), 1), '63.3')
        rows = list(csv.DictReader(io.StringIO(self.csvs['foundation-models-mi-rest.csv'].decode())))
        st = next(x for x in rows if x['model_id'] == 'steegformer-base')
        self.assertEqual(ex.fixed(float(st['primary_percent']), 1), '58.1')
        self.assertEqual(ex.fixed(float(st['descriptive_interval_high_percent']), 1), '63.3')

    def test_the_csvs_are_the_json_in_the_core_units(self):
        r = result(self.payload)
        cells = {(x['model'], x['protocol']): x for x in r['frozen_probe']}
        for p in ex.PROTOCOLS:
            text = self.csvs[f'foundation-models-{p}.csv'].decode()
            rows = list(csv.reader(io.StringIO(text)))
            core = list(csv.reader(io.StringIO((ex.CSV_DIR / f'{p}-results.csv').read_text())))
            self.assertEqual(rows[0][:len(core[0])], core[0], p)
            self.assertEqual([x[rows[0].index('model_id')] for x in rows[1:]], list(ex.CHECKPOINTS), p)
            for row in rows[1:]:
                d = dict(zip(rows[0], row))
                c = cells[(d['model_id'], p)]
                self.assertEqual(d['scoring_seconds'], '', 'timings are not published')
                if c['status'] != 'complete':
                    self.assertEqual((d['primary_percent'], d['status'], d['not_run_reason']), ('', 'not run', c['reason']))
                elif p == 'idle':
                    self.assertEqual(float(d['primary_percent']), 100 * c['commands_detected'] / 60)
                    self.assertEqual(float(d['secondary_value']), 100 * c['idle_false_activations'] / 60)
                    self.assertEqual(int(d['always_abstain_participants']), c['always_abstain_people'])
                else:
                    self.assertAlmostEqual(float(d['primary_percent']), 100 * c['balanced_accuracy'], places=9)
                    self.assertAlmostEqual(float(d['descriptive_interval_low_percent']), 100 * c['interval_95'][0], places=9)
                    self.assertEqual(d['interval_includes_chance'], 'true' if c['interval_includes_chance'] else 'false')
                self.assertEqual(d['pretraining_exposure'], ex.EXPOSURE_STATEMENT[c['exposure']['status']])

    def test_exposure_is_a_sourced_statement_never_a_proof(self):
        e = result(self.payload)['pretraining_exposure']
        printed = json.dumps(e['statements']).lower() + ''.join(b.decode().lower() for b in self.csvs.values())
        for phrase in ('proven', 'no overlap', 'guarantee', 'certified', 'not exposed'):
            self.assertNotIn(phrase, printed, phrase)
        self.assertIn('never as proven absence of overlap', e['wording_rule'])
        self.assertIn("not in the authors' published pretraining list (checked 2026-10-04)", printed)
        for key in ('labram', 'cbramod'):
            rows = [x for x in e['cells'] if x['model'] == key]
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(x['status'] == 'not_exposed' and x['urls'] and x['statement'].endswith('(checked 2026-10-04)')
                                for x in rows))
        self.assertEqual(e['counts'], {'exposed': 2, 'not_exposed': 82, 'unknown': 7})

    def test_the_prose_is_the_owners_wording(self):
        # Review of 2026-10-05: the candidate's "EEGMamba not exposed at medium confidence" and "user-approved" are
        # restated as the owner's wording; no prose in the file says "not exposed" or "user-approved".
        text = json.dumps(self.payload, ensure_ascii=False) + ''.join(b.decode() for b in self.csvs.values())
        self.assertNotIn('not exposed', text.lower())
        self.assertNotIn('user-approved', text)
        lim = [x for x in result(self.payload)['required_limitations'] if x.startswith('Pretraining exposure')]
        self.assertEqual(lim, [ex.EXPOSURE_LIMITATION])
        self.assertIn("published pretraining list", lim[0])
        self.assertIn('not how certain it is that the recordings were never seen', result(self.payload)['pretraining_exposure']['wording_rule'])
        reve = next(m for m in result(self.payload)['models'] if m['id'] == 'reve-base')
        self.assertEqual(reve['weights_licence'], 'REVE Responsible Use License v1.0 (owner-approved 2026-10-04)')

    def test_a_changed_exposure_limitation_is_refused(self):
        def reword(c):
            c['required_limitations'] = [x.replace('medium confidence', 'high confidence') for x in c['required_limitations']]
        with self.assertRaisesRegex(ValueError, 'exposure limitation'):
            build(self.forged(candidate=reword))

    # ------------------------------------------------------------------ the REVE sensitivity footnotes (review of 2026-10-05)
    def test_the_reve_footnotes_state_the_direction_of_the_aggregate(self):
        # The candidate's "changes P300 by -0.71 and sleep by +1.40" are primary minus sensitivity: read backwards.
        models = {m['id']: m for m in result(self.payload)['models']}
        self.assertTrue(models['reve-base']['row_footnote'].endswith(
            'a no-mean-removal sensitivity run scores P300 0.71 percentage points higher and sleep 1.40 lower.'))
        self.assertTrue(models['reve-large']['row_footnote'].endswith(
            'the no-mean-removal sensitivity run scores P300 2.06 percentage points lower and sleep 0.93 lower.'))
        for k in ('reve-base', 'reve-large'):
            self.assertEqual([n for n in models[k]['notes'] if 'sensitivity run' in n],
                             [n for n in models[k]['notes'] if n.endswith('is stated in the row footnote.')])
        text = json.dumps(self.payload, ensure_ascii=False) + ''.join(b.decode() for b in self.csvs.values())
        for gone in ('changes P300', 'reported separately'):
            self.assertNotIn(gone, text)
        agg = load(EV['aggregate'])
        cells = {c['id']: c['balanced_accuracy']['value'] for c in agg['frozen_probe_cells'] if 'balanced_accuracy' in c}
        for r in agg['sensitivity_rows']:
            if r['model'] == 'reve-base' and r['protocol'] == 'p300-target':
                self.assertGreater(r['balanced_accuracy']['value'], cells['frozen:reve-base:p300-target'])

    def test_a_footnote_with_the_wrong_direction_is_refused(self):
        agg = load(EV['aggregate'])
        models = copy.deepcopy(result(self.payload)['models'])
        ex.check_sensitivity_footnotes(models, agg)
        for k, a, b in (('reve-base', 'higher', 'lower'), ('reve-large', '0.93', '0.94'),
                        ('reve-large', 'scores P300 2.06 percentage points lower', 'changes P300 by -2.06')):
            forged = copy.deepcopy(models)
            m = next(x for x in forged if x['id'] == k)
            m['row_footnote'] = m['row_footnote'].replace(a, b, 1)
            with self.assertRaises(ValueError):
                ex.check_sensitivity_footnotes(forged, agg)

    def test_a_changed_candidate_footnote_is_refused(self):
        # A candidate that fixes or changes its own sign must be re-read, not reversed a second time.
        def fix(c):
            r = next(x for x in c['matrix_rows'] if x['model'] == 'reve-base')
            r['row_footnote'] = r['row_footnote'].replace('-0.71', '+0.71')
        with self.assertRaisesRegex(ValueError, 'row footnote changed'):
            build(self.forged(candidate=fix))

    def test_a_sensitivity_run_the_aggregate_contradicts_is_refused(self):
        def flip(a):
            r = next(x for x in a['sensitivity_rows'] if x['model'] == 'reve-large' and x['protocol'] == 'sleep-scalp')
            r['primary_minus_sensitivity_pp']['value'] = -r['primary_minus_sensitivity_pp']['value']
        with self.assertRaisesRegex(ValueError, 'sensitivity difference'):
            build(self.forged(aggregate=flip))

    def test_the_manifest_records_every_restatement(self):
        for edit in (lambda m: m.pop('restatements'),
                     lambda m: m['restatements'].pop(),
                     lambda m: m['restatements'][2].update(published=m['restatements'][2]['candidate'])):
            m = copy.deepcopy(MANIFEST)
            edit(m)
            with self.assertRaisesRegex(ValueError, 'restatement'):
                build(m)

    # ------------------------------------------------------------------ derived differences (review of 2026-10-05)
    def test_a_derived_difference_prints_as_the_candidate_states_it(self):
        # BrainOmni's BETA change is exactly (1451 - 2431) / 11200 = -0.0875: -8.8 pp at one decimal, not -8.7.
        c = result(self.payload)['comparisons']
        omni = next(x for x in c['fewer_electrodes_beta'] if x['model'] == 'brainomni-base')
        self.assertEqual(omni['four_minus_eight'], -0.0875)
        self.assertEqual(ex.fixed(100 * omni['four_minus_eight'], 1), '-8.8')
        for v in [x['four_minus_eight'] for x in c['fewer_electrodes_beta']] + [x['large_minus_base'] for x in c['base_vs_large']]:
            self.assertEqual(round(v, 12), v)
        self.assertEqual(ex.derived(-0.08749999999999997, -8.75, 'x'), -0.0875)
        with self.assertRaisesRegex(ValueError, 'prints'):
            ex.derived(-0.0874, -8.75, 'x')

    def test_a_stated_difference_that_prints_otherwise_is_refused(self):
        # Within the comparison's tolerance, but -8.745 rounds to -8.7 where the export prints -8.8.
        def edit(c):
            r = next(x for x in c['topic_findings']['comparison_rows']['fewer_electrodes_beta'] if x['model'] == 'brainomni-base')
            r['four_minus_eight_pp'] = -8.745
        with self.assertRaisesRegex(ValueError, 'brainomni-base eight to four electrodes: prints'):
            build(self.forged(candidate=edit))

    # ------------------------------------------------------------------ the chain of custody
    def test_a_changed_input_byte_is_refused(self):
        for key in ('handoff', 'releaseCandidate', 'aggregate', 'pretrainingExposure', 'auditStatus', 'harnessValidation'):
            m = copy.deepcopy(MANIFEST)
            m['evaluation'][key]['sha256'] = '0' * 64
            with self.assertRaises(ValueError, msg=key):
                build(m)
        m = copy.deepcopy(MANIFEST)
        m['evaluation']['summaries']['zuna']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            build(m)

    def test_an_edited_candidate_the_manifest_did_not_pin_is_refused(self):
        def nudge(c):
            cell(c, 'reve-large', 'sleep-scalp')['balanced_accuracy']['value'] += 0.01
        with self.assertRaisesRegex(ValueError, 'release candidate'):
            build(self.forged(candidate=nudge, rebind=False))

    def test_a_candidate_figure_that_is_not_its_source_is_refused(self):
        def nudge(c):
            cell(c, 'reve-large', 'sleep-scalp')['balanced_accuracy']['value'] += 0.001
        with self.assertRaisesRegex(ValueError, 'differs from'):
            build(self.forged(candidate=nudge))
        def released(c):
            cell(c, 'zuna', 'beta-8ch')['chance_level']['value'] = 0.25
        with self.assertRaisesRegex(ValueError, 'differs from site/src/data/mvp.json'):
            build(self.forged(candidate=released))

    def test_a_figure_the_aggregate_does_not_carry_is_refused(self):
        def drift(a):
            next(x for x in a['frozen_probe_cells'] if x['id'] == 'frozen:codebrain:p300-target')['macro_f1']['value'] += 0.01
        with self.assertRaisesRegex(ValueError, 'differs from the aggregate'):
            build(self.forged(aggregate=drift))

    def test_the_chain_names_the_pinned_files(self):
        with self.assertRaisesRegex(ValueError, 'another aggregate'):
            build(self.forged(candidate=lambda c: c['traceability'].update(aggregate_sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'other inputs'):
            build(self.forged(aggregate=lambda a: a['inputs'][0].update(sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'is named by another hash'):
            build(self.forged(candidate=lambda c: cell(c, 'reve-base', 'beta-4ch')['macro_f1']['src'].update(sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'unpinned file'):
            build(self.forged(candidate=lambda c: cell(c, 'reve-base', 'beta-4ch')['macro_f1']['src'].update(
                file='research/elsewhere/other.json')))
        with self.assertRaisesRegex(ValueError, 'handoff does not record'):
            build(self.forged(handoff=lambda t: t.replace(EV['independentAudits']['groups']['positions'], 'x' * 64)))

    def test_the_audits_must_pass(self):
        def fail(s):
            s['groups'][2]['pass'] = False
        with self.assertRaisesRegex(ValueError, 'did not pass without defect'):
            build(self.forged(audit_status=fail))
        def defect(s):
            s['groups'][4]['defects'] = ['LUNA truncation miscounted']
        with self.assertRaisesRegex(ValueError, 'did not pass without defect'):
            build(self.forged(audit_status=defect))
        def check(s):
            s['groups'][0]['checks'][3]['pass'] = False
        with self.assertRaisesRegex(ValueError, 'failed a check'):
            build(self.forged(audit_status=check))
        with self.assertRaisesRegex(ValueError, 'named by another hash'):
            build(self.forged(candidate=lambda c: c['audit']['groups'][1].update(audit_sha256='0' * 64)))
        def orphan(s):
            s['groups'][5]['models'] = ['singlem']
        with self.assertRaises(ValueError):
            build(self.forged(audit_status=orphan))
        with self.assertRaisesRegex(ValueError, 'harness validation did not pass'):
            build(self.forged(harness=lambda h: h['ii_cbramod_reextracted_on_cuda'].update(all_pass=False)))

    def test_the_approval_is_on_record(self):
        for edit in (lambda m: m['approval'].update(decision='hold'), lambda m: m['approval'].update(date='2026-10-03'),
                     lambda m: m['approval'].update(candidateStatusAtSeal='approved'),
                     lambda m: m['approval'].update(pretrainingExposureWording='LaBraM: not exposed.'),
                     lambda m: m.update(holds=[{'id': 'x'}])):
            m = copy.deepcopy(MANIFEST)
            edit(m)
            with self.assertRaises(ValueError):
                build(m)
        with self.assertRaisesRegex(ValueError, 'state it was sealed in'):
            build(self.forged(candidate=lambda c: c.update(status='approved')))

    # ------------------------------------------------------------------ the logic gates
    def test_a_not_run_cell_has_no_figure(self):
        def score(c, sync):
            # A zero written beside the reason, in the summary too, so only the not-run gate can refuse it.
            x = cell(c, 'brainomni-base', 'p300-target')
            src = dict(cell(c, 'brainomni-base', 'mi-rest')['balanced_accuracy']['src'],
                       pointer='/frozen_probe/p300-target/balanced_accuracy')
            x['balanced_accuracy'] = {'value': 0.0, 'src': src}
            sync(x['balanced_accuracy'])
        with self.assertRaisesRegex(ValueError, 'not run, yet a figure'):
            build(self.forged(both=score))
        c = {(x['model'], x['protocol']): x for x in result(self.payload)['frozen_probe']}
        self.assertIsNone(c[('brainomni-base', 'semantic-target')]['balanced_accuracy'])

    def test_every_interval_holds_its_point(self):
        def wide(c, sync):
            block = cell(c, 'luna-base', 'arithmetic-rest')['interval95']
            block['value'] = [0.9, 0.95]
            sync(block)
        with self.assertRaisesRegex(ValueError, 'does not contain its point'):
            build(self.forged(both=wide))

    def test_the_chance_flag_follows_the_interval(self):
        def flip(c):
            cell(c, 'erp-fm-base', 'p300-target')['interval_includes_chance']['value'] = False
        with self.assertRaisesRegex(ValueError, 'chance flag'):
            build(self.forged(candidate=flip))

    def test_a_paired_change_is_the_difference_of_its_arms(self):
        def drift(c, sync):
            block = adapt(c, 'codebrain')['paired_lora_minus_frozen']['mean_change']
            block['value'] += 0.002
            sync(block)
        with self.assertRaisesRegex(ValueError, 'not the difference of the arms'):
            build(self.forged(both=drift))
        def people(c, sync):
            block = adapt(c, 'eegmamba')['paired_lora_minus_frozen']['helped']
            block['value'] += 1
            sync(block)
        with self.assertRaisesRegex(ValueError, 'is not 36'):
            build(self.forged(both=people))
        def zero(c):
            adapt(c, 'brainomni-base')['paired_lora_minus_frozen']['interval_excludes_zero']['value'] = True
        with self.assertRaisesRegex(ValueError, 'zero flag'):
            build(self.forged(candidate=zero))

    def test_exposure_lands_on_its_own_model_and_dataset(self):
        def hide(c, sync):
            block = cell(c, 'singlem', 'semantic-target')['exposure']
            block['status'] = 'not_exposed'
            sync(block)
        with self.assertRaisesRegex(ValueError, 'expected exposed'):
            build(self.forged(both=hide))
        def elsewhere(c):
            cell(c, 'reve-base', 'mi-rest')['exposure']['src']['pointer'] = '/cells/22/status'
        with self.assertRaisesRegex(ValueError, 'another model or dataset'):
            build(self.forged(candidate=elsewhere))

    def test_every_comparison_follows_the_intervals(self):
        def size(c):
            next(x for x in c['topic_findings']['comparison_rows']['base_vs_large']
                 if x['base'] == 'reve-base' and x['protocol'] == 'mi-rest')['marginal_intervals_overlap'] = False
        with self.assertRaisesRegex(ValueError, 'the candidate says otherwise'):
            build(self.forged(candidate=size))
        def above(c):
            x = next(x for x in c['topic_findings']['comparison_rows']['vs_published_rows']
                     if x['model'] == 'reve-base' and x['protocol'] == 'beta-8ch')
            x['relations']['best_non_foundation']['relation'] = 'above'
        with self.assertRaisesRegex(ValueError, 'the candidate says otherwise'):
            build(self.forged(candidate=above))
        def masking(c):
            c['masking_ablation_panel']['overlap_rows'][6]['non_overlapping_pairs'] = []
        with self.assertRaisesRegex(ValueError, 'the candidate says otherwise'):
            build(self.forged(candidate=masking))

    def test_every_figure_is_the_handoffs(self):
        with self.assertRaisesRegex(ValueError, 'the handoff prints'):
            build(self.forged(handoff=lambda t: t.replace('| 79.6 (78.2–81.0) |', '| 79.7 (78.2–81.0) |')))
        with self.assertRaisesRegex(ValueError, 'idle row'):
            build(self.forged(handoff=lambda t: t.replace('| ST-EEGFormer Large | 1/60 | 20/60 |', '| ST-EEGFormer Large | 1/60 | 21/60 |')))
        with self.assertRaisesRegex(ValueError, 'adaptation row'):
            build(self.forged(handoff=lambda t: t.replace('+9.71 (+6.11 to +13.27)', '+9.17 (+6.11 to +13.27)')))
        with self.assertRaisesRegex(ValueError, 'LoRA budget'):
            build(self.forged(handoff=lambda t: t.replace('32,768 to 428,032', '32,768 to 430,466')))

    def test_the_rights_are_the_reviewed_core_tracks_and_licences(self):
        for key, value in (('attribution', 'Someone else'), ('license', 'CC0-1.0'), ('reviewBasis', []), ('name', 'BETA2')):
            m = copy.deepcopy(MANIFEST)
            m['sources'][2][key] = value
            with self.assertRaises(ValueError, msg=key):
                build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][4]['privacyReview'] = 'Aggregate only.'
        with self.assertRaisesRegex(ValueError, 'privacy review'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['sources'][7]['decision'] = 'hold'
        with self.assertRaises(ValueError):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['models'][1]['weightsLicence'] = 'CC BY 4.0'
        with self.assertRaisesRegex(ValueError, 'not the reviewed one'):
            build(m)
        m = copy.deepcopy(MANIFEST)
        m['models'][-1]['ids'] = []
        with self.assertRaisesRegex(ValueError, 'every checkpoint'):
            build(m)
        def research_use(c):
            next(r for r in c['matrix_rows'] if r['model'] == 'zuna')['licence_note'] = 'Apache-2.0 weights.'
        with self.assertRaisesRegex(ValueError, 'research-use sentence'):
            build(self.forged(candidate=research_use))

    # ------------------------------------------------------------------ what stays out
    def test_per_person_timing_and_private_fields_are_refused(self):
        for key in ('p10', 'median', 'per_person_ba', 'per_fold', 'features_sha256', 'channels_used', 'timing_seconds',
                    'peak_cuda_allocated_mib', 'peak_process_rss_mib', 'extraction_seconds', 'environment', 'venv',
                    'adapter_sha256', 'local_clone', 'sensitivity_no_mean_removal', 'audit_file', 'checks',
                    'v8_open_items', 'overlaps_outside_core_datasets', 'predictions', 'participant_id', 'contract'):
            with self.assertRaises(ValueError, msg=key):
                ex.scrub_check({'results': {'x': {key: 1}}})
        for text in ('/Volumes/disk/x', '/Users/someone/x', 'host:/mnt/bigdata', 'somehost:~/Projects/x', ' ~/Projects',
                     'sub-07', 'subj12', 'runs/x/summary.json', 'contract.json', 'scores.private', 'DECISIONS.md'):
            with self.assertRaises(ValueError, msg=text):
                ex.scrub_check({'results': {'x': {'note': text}}})
        with self.assertRaises(ValueError):
            ex.scrub_check({'note': 'kept on SomeHost'}, names={'somehost'})

    def test_the_private_names_are_read_and_absent(self):
        cand = load(EV['releaseCandidate'])
        handoff = (ex.PROJECT / EV['handoff']['path']).read_text()
        names = ex.private_names(cand, handoff)
        self.assertGreaterEqual(len(names), 2)
        files = [json.dumps(self.payload, ensure_ascii=False), *(b.decode() for b in self.csvs.values()),
                 ex.MANIFEST.read_text(), ex.EXPORT_AUDIT.read_text()]
        for text in files:
            for n in names:
                self.assertNotIn(n.lower(), text.lower())
            for token in ('/Volumes/', '/Users/', '/home/', '/mnt/', '~/', '.private', 'DECISIONS.md'):
                self.assertNotIn(token, text)

    def test_no_compute_and_no_sensitivity_figure(self):
        keys = set()

        def walk(v):
            if isinstance(v, dict):
                keys.update(k.lower() for k in v)
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(self.payload)
        self.assertFalse([k for k in keys if any(f in k for f in ('second', 'mib', 'gpu', 'timing', 'compute', 'sensitivity'))])
        cand = load(EV['releaseCandidate'])
        self.assertNotIn(cand['methods']['compute'], json.dumps(self.payload))


if __name__ == '__main__':
    unittest.main()
