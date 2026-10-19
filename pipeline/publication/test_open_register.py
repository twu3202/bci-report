"""Acceptance tests for the open register builder (packages B8a and B8b).

    python3 -m unittest pipeline/publication/test_open_register.py

The tests read the files the exporter wrote (run export_open_register.py first) and its inputs, and assert the
package's acceptance items: the frozen population as D11 with the classifier audit's re-check, family collapses,
one EEGDash family, 158 MOABB record groups with merges reported, six agreement corpora, the model rows, opaque ids,
no identifier in two rows or twice in one row, no participant-like id, no uploader name in a URL, no ICLR 2027 /
OpenReview / submission reference, no HF card text, counts or dates, the D3 gate on comparison findings (the
verifier's own identification of each family, its "do not state" and same-party notes), plain rows for personal or
identifying information, no classifier fields in the served file, and the CSV shape.

B8b (class Freeze): the served file is frozen; its site rows are the rows export-site-register-rows.mjs re-read at the
freeze, every row's level is the furthest step whose anchor item is on file with the items missing at or below it as
gaps; the rows the package names are present (IESSEEG, eldBETA with its score held, ZuCo 2.0, L-FAME, Shin2022 with
MOABB's catalog counts); the alpha-waves finding is sourced; merged external rows are aliases of their site rows; the
step words are the pages'; the manifest the file names is the one on disk; the model rows cover /methods/; each
step's evidence lists an item once per public source; the CSV's host is the record's repository, never the DOI
resolver. Class SiteHolds: the eldBETA and ZuCo 2.0 holds are in the site rows with their sources, and the served file
declares and attaches exactly the ones site/src/data/open-register.ts words.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import tempfile
import unittest
import urllib.parse
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import export_open_register as X  # noqa: E402
from register_findings import (FindingError, SITE_HOLD_REASONS, comparison_allowed, finding,  # noqa: E402
                               schema as finding_schema, validate)
from register_ids import IdMap  # noqa: E402

EXT = json.loads(X.EXTERNAL_OUT.read_text())
SITE = json.loads(X.SITE_OUTS[0].read_text())
IDS = json.loads(X.IDS_PATH.read_text())
CSV_ROWS = list(csv.DictReader(io.StringIO(X.CSV_OUT.read_text())))
AUDIT = json.loads(X.AUDIT.read_text())
A4 = json.loads(X.INPUTS['a4_index'].read_text())
CLASSIFIED = {r['id']: r for f in sorted((X.OPEN / 'classified').glob('batch-*.json')) for r in json.loads(f.read_text())}
VERIFIED = {json.loads(f.read_text())['id']: json.loads(f.read_text()) for f in (X.OPEN / 'verified').glob('*.json')}

ID_RX = re.compile(r'^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|model-[a-z0-9-]+|site-[a-z0-9.-]+)$')
# The test's own reading of verifier notes that withhold a row from comparisons (kept apart from the exporter's).
DO_NOT_STATE = re.compile(r'\bdo not state\b', re.I)
SAME_PARTY = re.compile(r"same party|same-party|not a third[- ]party|rather than a third-party|own companion"
                        r"|team release|re-exporting its own data", re.I)
SCOPED_SAME_PARTY = {'LidongYang/BrainFLORA'}


def recheck() -> dict:
    """The classifier audit's population re-check, recomputed from the audit and the classifier rows."""
    class Stub:
        audit = AUDIT
    return X.Build.recheck_scope(Stub(), CLASSIFIED)
VENUE = re.compile(r'ICLR\s*2027|openreview|\bsubmission\b|double[- ]blind|under review', re.I)
FORBIDDEN_KEYS = {'downloads', 'likes', 'createdAt', 'lastModified', 'description', 'readme', 'one_line_en',
                  'one_line_zh', 'notes', 'register_wording_en', 'register_wording_zh', 'trendingScore',
                  'consent_or_ethics_statement', 'stated', 'source_claim', 'Gender', 'Age Mean', 'Age Min', 'Age Max',
                  'Handedness', 'Health'}


def strings(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)
    elif isinstance(x, str):
        yield x


def keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from keys(v)


def urls(x):
    for s in strings(x):
        for m in re.finditer(r'https?://[^\s"]+|mailto:[^\s"]+', s):
            yield m.group(0)


class Population(unittest.TestCase):
    def test_d11_population_and_recheck_reconcile(self):
        hf = EXT['counts']['hf']
        in_scope = sorted(i for i, r in CLASSIFIED.items() if r['in_scope'])
        self.assertEqual(hf['classifier_in_scope'], len(in_scope))
        self.assertEqual(hf['classifier_in_scope'], 400)
        out = hf['recheck_out_simulated'] + hf['recheck_out_emg_rule'] + hf['recheck_out_undetermined']
        self.assertEqual(hf['in_scope'], hf['classifier_in_scope'] - out)
        self.assertEqual(hf['in_scope'],
                         hf['single_rows'] + hf['family_members'] + hf['merged_into_site_rows'] + hf.get('merged_into_moabb_rows', 0) + hf['held_for_review'])
        pr = EXT['population_recheck']
        self.assertEqual(sum(pr['counts'].values()), out)
        self.assertEqual(len(pr['excluded']) + sum(pr['excluded_participant_like'].values()), out)
        self.assertEqual(hf['recheck_signoff'], 'pending')        # the 368 prints only beside its basis
        self.assertEqual(pr['status'], 'pending_signoff')
        full = recheck()
        self.assertEqual(pr['excluded_digest_sha256'],
                         X.sha(json.dumps(sorted([repo, rule] for repo, rule in full.items())).encode()))
        for x in pr['excluded']:
            self.assertFalse(X.participant_like_repo(x['repo']), x['repo'])

    def test_audit_corrections_applied(self):
        excluded = recheck()
        listed = {x['repo'] for x in EXT['population_recheck']['excluded']}
        self.assertEqual(listed, {r for r in excluded if not X.participant_like_repo(r)})
        for w in AUDIT['wrong_rows']:
            if w['field'] == 'in_scope' and w['corrected_value'] is False:
                self.assertIn(w['id'], excluded, w['id'])
        for item in AUDIT['population_screens']['in_scope_synthetic']:
            repo = item.split(' ', 1)[0]
            self.assertEqual(repo in excluded, 'stays' not in item, repo)
        rendered = {e['hf']['repo'] for e in EXT['entries'] if e.get('hf')}
        self.assertFalse(rendered & set(excluded))

    def test_held_rows_appear_nowhere(self):
        for doc in (EXT, SITE):
            text = json.dumps(doc).lower()
            for repo in X.REVIEW_HOLD:
                self.assertFalse(repo.lower() in text, repo)
                name = repo.split('/', 1)[1].lower()
                if name != 'iesseeg':            # IESSEEG is the site row (D13), cited by its own card only
                    self.assertFalse(name in text, repo)

    def test_one_eegdash_family_with_full_map(self):
        rows = [e for e in EXT['entries'] if e['group'] == 'eegdash']
        self.assertEqual(len(rows), 1)
        fam = next(f for f in EXT['families'] if f['kind'] == 'eegdash')
        mapping = json.loads(X.INPUTS['eegdash'].read_text())
        self.assertEqual(fam['n'], len(mapping))
        self.assertEqual({m['mirror'] for m in fam['members']}, set(mapping))
        # ds004584 and ds004902 carry their mirror ids as aliases on their site rows (plan section 2.6)
        site = {e['id']: e for e in SITE['entries']}
        for slug, mirror in (('ds004584', 'EEGDash/ds004584'), ('ds004902', 'EEGDash/ds004902')):
            self.assertIn(mirror, [a['value'] for a in site[f'r-site-{slug}']['aliases']])

    def test_moabb_groups(self):
        rows = [e for e in EXT['entries'] if e['group'] == 'moabb']
        self.assertEqual(len(rows), 158)
        self.assertEqual(EXT['counts']['moabb']['record_groups'], 158)
        self.assertEqual(sum(len(e['moabb']['loaders']) for e in rows), 206)
        merged = [e for e in rows if e.get('merge_into')]
        self.assertEqual(len(merged), EXT['counts']['moabb']['merged_into_site_rows'])
        site_ids = {e['id'] for e in SITE['entries']}
        must = {'Liu2020BETA': 'beta', 'Lee2019_MI': 'openbmi', 'Lee2021Mobile_ERP': 'mobile-bci',
                'Rodrigues2017': 'alpha-waves', 'Yang2025': 'wbcic-shu', 'BNCI2014_001': 'bnci2014-001',
                'BNCI2014_004': 'bnci2014-004', 'BNCI2014_008': 'bnci2014-008', 'BNCI2014_009': 'bnci2014-009',
                'PhysionetMI': 'physionet-eegmmidb', 'Shin2022': 'shin2022', 'Liu2022EldBETA': 'eldbeta',
                'Stieger2021': 'stieger-longitudinal'}
        for e in merged:
            self.assertIn(f'r-site-{e["merge_into"]}', site_ids)
        for loader, slug in must.items():
            e = next(x for x in rows if loader in x['moabb']['loaders'])
            self.assertEqual(e.get('merge_into'), slug, loader)
        bi = next(x for x in rows if 'BI2013a' in x['moabb']['loaders'])
        self.assertEqual(bi['status'], 'planned')
        self.assertNotIn('merge_into', bi)
        self.assertEqual(bi['terms_as_stated']['value'], 'Creative Commons Attribution 1.0 Generic')
        for loader, code in (('Liu2024', 'released_ids_duplicated'), ('Schrag2026Pediatric', 'targets_stored_with_outputs'),
                             ('Hinss2021', 'deposits_differ'), ('Kim2025BetaRange', 'onset_timing_unresolved'),
                             ('Dreyer2023', 'release_family_unchecked'), ('Alawieh2025', 'one_offline_session')):
            e = next(x for x in rows if loader in x['moabb']['loaders'])
            self.assertIn({'code': 'hold', 'params': {'reason_code': code}}, e['findings'], loader)
        for e in rows:
            for f in e['moabb']['fields_as_listed']:
                self.assertEqual(set(f), {'loader', 'paradigm', 'people', 'channels', 'sampling_rate_hz'})
            if any(re.match(r'^BI20\d\d[ab]?$', x) for x in e['moabb']['loaders']):
                self.assertIn({'code': 'named_in_corpus', 'params': {'models': ['LaBraM', 'REVE'],
                                                                     'release_resolved': False}}, e['findings'])
            if not e['moabb']['licence_as_listed'] and e['terms_as_stated']['by'] == 'none':
                self.assertIn('licence_as_stated', [g['item'] for g in e['gaps']])

    def test_six_agreement_corpora(self):
        rows = {e['id']: e for e in EXT['entries'] if e['group'] == 'corpus'}
        self.assertEqual(set(rows), {f'r-corpus-{s}' for s in ('seed', 'deap', 'amigos', 'mahnob-hci', 'dreamer', 'tuh-eeg')})
        caps = {c['capture_id'] for c in EXT['sources']['access_terms']}
        for e in rows.values():
            self.assertIn(e['original_terms']['capture_id'], caps)
            self.assertEqual(e['level'], 1)
        self.assertEqual(rows['r-corpus-dreamer']['access'], 'request_based')

    def test_model_rows(self):
        rows = {e['id']: e for e in EXT['entries'] if e['ladder'] == 'model'}
        want = {'neurolm-b', 'zuna', 'eeg-fm-masking', 'diver-1', 'popt', 'omnimouse', 'biox-bridge', 'poyo-plus',
                'poyo-cap', 'neuroformer', 'brainlm'}
        self.assertEqual(set(rows), {f'r-model-{s}' for s in want})
        n = rows['r-model-neurolm-b']
        self.assertEqual((n['level'], n['exposure']), (4, 'unknown'))
        self.assertEqual(set(n['links']['cases']), {'/topics/pilot-studies/#neurolm-eegmat', '/topics/clinical-groups/#iesseeg'})
        for s in ('zuna', 'eeg-fm-masking', 'diver-1'):
            self.assertNotIn('venue', rows[f'r-model-{s}'])
        for e in rows.values():
            if 'venue' in e:
                self.assertRegex(e['venue']['value'], r'^ICLR 202[456]$')
                self.assertNotIn('openreview', json.dumps(e['venue']).lower())
            self.assertEqual(set(e['terms_by_part']), {'code', 'weights', 'data'})
        self.assertEqual(rows['r-model-zuna'].get('merge_into'), 'zuna')
        copies = {a['value']: a for a in rows['r-model-zuna']['aliases'] if a['kind'] == 'weights_copy'}
        self.assertEqual(copies['modulsx/ZUNA1.1']['relation'], 'same_file')
        self.assertNotIn('braindecode/ZUNA', copies)          # the earlier ZUNA release, not 1.1

    def test_site_model_copies(self):
        rows = {e['id']: e for e in SITE['entries'] if e['ladder'] == 'model'}
        eegpt = rows['r-model-eegpt']
        aliases = {a['value']: a for a in eegpt['aliases']}
        self.assertIn('braindecode/eegpt-pretrained', aliases)
        self.assertEqual(aliases['braindecode/eegpt-pretrained']['licence_tag'], 'bsd-3-clause')
        cb = {a['value']: a for a in rows['r-model-cbramod']['aliases']}
        self.assertEqual(cb['smoking11/CBraMod']['relation'], 'same_file')
        self.assertNotIn('oraculumai/CBraMod-MI-CoreML', cb)


class Privacy(unittest.TestCase):
    def test_no_participant_like_id_anywhere(self):
        for name, doc in (('external', EXT), ('site', SITE)):
            for s in strings(doc):
                self.assertIsNone(X.PARTICIPANT_ID.search(s), f'{name}: {s[:80]}')
                if re.fullmatch(r'[\w.-]+/[\w.-]+', s):          # any value that is a repo id
                    self.assertFalse(X.participant_like_repo(s), f'{name}: {s}')
            for e in doc['entries']:
                for repo in [(e.get('hf') or {}).get('repo', '')] + [a['value'] for a in e['aliases']]:
                    self.assertFalse(repo and X.participant_like_repo(repo), (e['id'], repo))
        csv_text = X.CSV_OUT.read_text()
        self.assertIsNone(X.PARTICIPANT_ID.search(csv_text))
        for r in CSV_ROWS:
            if r['group'] == 'hf' and '*' not in r['name']:
                self.assertFalse(X.participant_like_repo(r['name']), r['name'])
        for k in list(IDS['assigned']) + list(IDS['retired']):
            self.assertIsNone(X.PARTICIPANT_ID.search(k), k)
            if k.startswith('hf|hf:'):
                self.assertFalse(X.participant_like_repo(k[len('hf|hf:'):]), k)

    def test_participant_patterns_treat_separators_as_boundaries(self):
        for s in ('inogii/eeg_subject0', 'x-sub01.y', 'a/sub 3', 'study_participant12', 'A01T.mat', 'set_pt7'):
            self.assertIsNotNone(X.PARTICIPANT_ID.search(s), s)
        for s in ('subset1', 'gpt2', 'ckpt_10', 'eeg2meg-tiny', 'BCICIV_2A_tensor', 'ds004584'):
            self.assertIsNone(X.PARTICIPANT_ID.search(s), s)
        self.assertTrue(X.participant_like_repo('someone/emg-gestures-task1-u1'))
        self.assertTrue(X.participant_like_repo('someone/eval_emg-task3-edit-u2_test'))
        self.assertFalse(X.participant_like_repo('Zyphra/ZUNA1.1'))

    def test_participant_series_collapsed_without_members(self):
        fam = [f for f in EXT['families'] if f['kind'] == 'hf_series']
        series = {(f['uploader'], f['series']): f['n'] for f in fam}
        self.assertEqual(series[('perottofederico', 'things-eeg-captions')], 13)   # nested -single series folded in
        self.assertNotIn('alex', ' '.join(f['series'] for f in fam))
        self.assertIn(('tankalapavankalyan', 'ds007808'), series)
        for f in fam:
            self.assertNotIn('members', f)

    def test_series_collapse_rules(self):
        fam = {(f['uploader'], f['series']): f['n'] for f in EXT['families'] if f['kind'] == 'hf_series'}
        self.assertEqual(fam[('atgarcia', 'EMGSoundTrain')], 4)                 # trailing index, no separator
        self.assertEqual(fam[('Kkuntal990', 'test')], 4)                        # test runs
        self.assertEqual(fam[('Kkuntal990', 'bnci')], 4)                        # braindecode hub formats
        singles = [e['hf']['repo'] for e in EXT['entries'] if e.get('hf')]
        for repo in singles:                                                    # u<n> repos never stand alone
            self.assertFalse(X.participant_like_repo(repo), repo)
        for repo in ('jalauer/Singh2018', 'jalauer/Singh2020', 'Zachary1150/EESM17-Processed',
                     'McGregorW/EEGDatasets', 'McGregorW/EEGDatasets_raw'):     # years and distinct sets stay rows
            self.assertIn(repo, singles)
        # Family rows read apart: every family name is distinct and carries its uploader.
        names = [e['name'] for e in SITE['entries'] if e['kind'] == 'hf_family']
        self.assertEqual(len(names), len(set(names)))
        for e in SITE['entries']:
            if e['kind'] == 'hf_family':
                self.assertEqual(e['name'], f'{e["family"]["uploader"]}/{e["family"]["series"]}*')
        csv_names = [r['name'] for r in CSV_ROWS if r['group'] == 'hf']
        self.assertEqual(len(csv_names), len(set(csv_names)))
        # Unit: the stem rules.
        fams, _ = X.series_keys(['u/EMGSoundTrain1', 'u/EMGSoundTrain2', 'u/Singh2018', 'u/Singh2020',
                                 'u/x-raw', 'u/x-windows', 'u/data', 'u/data_raw', 'u/run-u1', 'u/run'])
        self.assertEqual(set(fams), {('u', 'emgsoundtrain'), ('u', 'x'), ('u', 'run')})

    def test_no_uploader_name_in_urls_or_anchors(self):
        uploaders = {e['hf']['repo'].split('/')[0] for e in EXT['entries'] if e.get('hf') and not e.get('merge_into')}
        uploaders |= {f['uploader'] for f in EXT['families'] if f['kind'] == 'hf_series'}
        for doc in (EXT, SITE):
            for e in doc['entries']:
                self.assertRegex(e['id'], ID_RX)
                if e['group'] in ('hf', 'eegdash'):
                    own = (e.get('hf') or {}).get('repo', '').split('/')[0] or (e.get('family') or {}).get('uploader', '')
                    for u in urls(e):
                        low = urllib.parse.unquote(u).lower()
                        self.assertNotIn(own.lower(), low, (e['id'], u))
                        for up in uploaders:
                            self.assertNotIn('/' + up.lower() + '/', low, (e['id'], u))
                        if e.get('hf'):
                            self.assertNotIn(e['hf']['repo'].lower(), low)
                self.assertEqual(e['correction']['mailto'],
                                 f'mailto:contact@bci.report?subject=Register%20row%20{e["id"]}')

    def test_no_card_text_counts_dates_or_demographics(self):
        for doc in (EXT, SITE):
            found = set(keys(doc)) & FORBIDDEN_KEYS
            self.assertFalse(found, found)

    def test_no_venue_or_submission_reference(self):
        for name, doc in (('external', {k: v for k, v in EXT.items() if k != 'provenance_paths'}), ('site', SITE)):
            for s in strings(doc):
                self.assertIsNone(VENUE.search(s), f'{name}: {s[:100]}')
        bare = re.sub(r'https?://[^\s"]+', '', json.dumps(SITE))
        self.assertNotIn('iclr_', bare.lower())
        self.assertNotIn('research/', bare)

    def test_no_private_paths(self):
        for doc in (EXT, SITE):
            text = re.sub(r'https?://[^\s"]+', '', json.dumps(doc))
            self.assertIsNone(re.search(r'/(?:Users|home|Volumes|mnt)/|trx50|Gal4|BCI_Arena', text))


class Findings(unittest.TestCase):
    def test_every_finding_validates(self):
        caps = {c['capture_id'] for c in EXT['sources']['access_terms']}
        for e in EXT['entries']:
            verdict = (VERIFIED.get(e['hf']['repo']) or {}).get('verdict') if e.get('hf') else None
            validate(e['findings'], verdict=verdict, captures=caps)

    def test_d3_gate(self):
        fams_by_repo = {v['id']: set(v['families_matched_by_name']) for v in A4['verifier_results_read']}
        n = 0
        for e in EXT['entries']:
            for f in e['findings']:
                if f['code'] in ('matches_metadata_of', 'terms_differ'):
                    n += 1
                    repo = e['hf']['repo']
                    self.assertEqual(VERIFIED[repo]['verdict'], 'confirmed', repo)
                    self.assertIn(f['params']['source'], fams_by_repo[repo])
                    self.assertTrue(f['params']['capture_id'].startswith(f'a4:{f["params"]["source"]}:'))
        self.assertGreater(n, 0)

    def test_comparison_rests_on_the_verifiers_own_identification(self):
        rows = 0
        for e in EXT['entries']:
            comp = [f for f in e['findings'] if f['code'] in ('matches_metadata_of', 'terms_differ')]
            if not comp:
                continue
            rows += 1
            repo = e['hf']['repo']
            spec = X.VERIFIED_SOURCES[repo]['families']
            for f in comp:
                fields, phrase = spec[f['params']['source']]
                self.assertIn(phrase, VERIFIED[repo]['original_source'], (repo, f['params']['source']))
                if f['code'] == 'matches_metadata_of':
                    self.assertEqual(f['params']['fields'], sorted(fields))
            self.assertEqual({f['params']['source'] for f in comp if f['code'] == 'matches_metadata_of'}, set(spec))
            self.assertEqual(e['level_cap'], {'step': 1, 'rule': 'reuploads_stay_at_step_1'})
            caps = sorted(f['params']['capture_id'] for f in comp if f['code'] == 'matches_metadata_of')
            self.assertEqual([i['source'] for i in e['step_evidence']['3']['items'] if i['item'] == 'original_terms'],
                             caps)
        self.assertEqual(rows, len(X.VERIFIED_SOURCES))
        # Families A4 matched by name that the verifier lists as untraced or as context yield nothing.
        by = {e['hf']['repo']: e for e in EXT['entries'] if e.get('hf')}
        for repo, slug in (('2Levi/EEG_fNIRS_4_BCI', None), ('McGregorW/EEGDatasets', 'bci-competition-iv'),
                           ('USuCgex0122e/demo_dataset_seed20260726', 'things-eeg2')):
            if slug:
                self.assertNotIn(slug, {f['params'].get('source') for f in by[repo]['findings']}, repo)

    def test_do_not_state_and_same_party_rows_get_no_comparison(self):
        hit = {}
        for repo, v in VERIFIED.items():
            text = '\n'.join(str(x) for k in ('claim_checked', 'original_source', 'flag_by_flag', 'identifying_info',
                                               'notes') for x in ((v.get(k) or {}).values() if isinstance(v.get(k), dict)
                                                                  else [v.get(k) or '']))
            if DO_NOT_STATE.search(text):
                hit[repo] = 'do_not_state'
            elif SAME_PARTY.search(text):
                hit[repo] = 'same_party'
        self.assertIn('jonathan-lys/reve-atlas', hit)
        self.assertIn('skywalker-p/EEG_2d', hit)
        self.assertIn('divyanshmaurya1/projectcerebro-eeg', hit)
        by = {e['hf']['repo']: e for e in EXT['entries'] if e.get('hf')}
        for repo, why in hit.items():
            if repo in SCOPED_SAME_PARTY:
                # The note is about the duplicate flag between two of the uploader's own repos.
                self.assertIn('Both repos belong to the same account', VERIFIED[repo]['notes'])
                continue
            self.assertNotIn(repo, X.VERIFIED_SOURCES, repo)
            e = by.get(repo)
            if e:
                self.assertFalse([f for f in e['findings'] if f['code'] in ('matches_metadata_of', 'terms_differ')],
                                 (repo, why))
                self.assertNotEqual((e.get('level_cap') or {}).get('rule'), 'reuploads_stay_at_step_1', repo)

    def test_named_review_rows(self):
        by = {e['hf']['repo']: e for e in EXT['entries'] if e.get('hf')}
        reve, eeg2d = by['jonathan-lys/reve-atlas'], by['skywalker-p/EEG_2d']
        self.assertFalse([f for f in reve['findings'] if f['code'] != 'licence_tag_absent' and f['code'] != 'gated'])
        self.assertNotIn('level_cap', reve)
        self.assertNotIn('pair', json.dumps(eeg2d['findings']))
        self.assertNotIn('level_cap', eeg2d)
        # amongglue/amber: the card labels every source ODC-BY 1.0; terms differ only for Siena and HMC.
        amber = [f for f in by['amongglue/amber']['findings'] if f['code'] == 'terms_differ']
        self.assertEqual({f['params']['source'] for f in amber}, {'physionet-siena-scalp-eeg', 'physionet-hmc-sleep-staging'})
        for f in amber:
            self.assertEqual((f['params']['declared'], f['params']['declared_by'], f['params']['original']),
                             ('odc-by-1.0', 'dataset_card', 'cc-by-4.0'))
        # DREAMER: request-based, never a signed agreement (the verifier's correction).
        for repo in ('monster-monash/DREAMERA', 'monster-monash/DREAMERV'):
            td = [f for f in by[repo]['findings'] if f['code'] == 'terms_differ']
            self.assertEqual([f['params']['original'] for f in td], ['request_based'])

    def test_personal_info_rows_are_plain(self):
        P = 'personal-or-identifying-info-visible'
        n = 0
        for e in EXT['entries']:
            if not e.get('hf'):
                continue
            repo = e['hf']['repo']
            v = VERIFIED.get(repo) or {}
            if P in CLASSIFIED[repo].get('flags', []) or P in v.get('claim_checked', '') or P in (v.get('flag_by_flag') or {}):
                n += 1
                self.assertLessEqual({f['code'] for f in e['findings']}, {'licence_tag_absent', 'gated'}, repo)
                self.assertNotEqual((e.get('level_cap') or {}).get('rule'), 'reuploads_stay_at_step_1', repo)
                validate(e['findings'], verdict=v.get('verdict'), plain=True)
        self.assertGreater(n, 0)
        by = {e['hf']['repo']: e for e in EXT['entries'] if e.get('hf')}
        for repo in ('skywalker-p/EEG_2d', 'as674262040/pub_eeg'):
            self.assertEqual([f['code'] for f in by[repo]['findings']], ['licence_tag_absent'], repo)
        with self.assertRaises(FindingError):
            validate([finding('derived_from', row='r-corpus-deap')], plain=True)
        for repo, v in VERIFIED.items():
            if v['verdict'] != 'confirmed':
                e = next((x for x in EXT['entries'] if x.get('hf', {}).get('repo') == repo), None)
                if e:
                    self.assertFalse([f for f in e['findings'] if f['code'] in ('matches_metadata_of', 'terms_differ')])

    def test_derived_from_only_when_card_names_source(self):
        for e in EXT['entries']:
            for f in e['findings']:
                if f['code'] == 'derived_from':
                    self.assertEqual(CLASSIFIED[e['hf']['repo']]['derived_from']['basis'], 'stated in card')

    def test_finding_gate_unit(self):
        self.assertFalse(comparison_allowed('uncertain', 'a4:seed:0123456789abcdef'))
        self.assertFalse(comparison_allowed('confirmed', None))
        self.assertTrue(comparison_allowed('confirmed', 'a4:seed:0123456789abcdef'))
        with self.assertRaises(FindingError):
            finding('personal_info_visible')
        with self.assertRaises(FindingError):
            finding('hold', reason_code='made_up')
        with self.assertRaises(FindingError):
            finding('family', n=2, uploader='x', series='The card says this is the data and that is all.')
        f = finding('terms_differ', original='signed_agreement', declared='none', declared_by='licence_tag',
                    capture_id='a4:seed:0123456789abcdef', source='seed')
        with self.assertRaises(FindingError):
            validate([f], verdict='uncertain')
        with self.assertRaises(FindingError):
            validate([f], verdict='confirmed', withheld='same_party')
        validate([f], verdict='confirmed')
        with self.assertRaises(FindingError):
            finding('terms_differ', original='mit', declared='mit', declared_by='licence_tag',
                    capture_id='a4:seed:0123456789abcdef')
        with self.assertRaises(FindingError):
            finding('terms_differ', original='mit', declared='bsd', declared_by='guess',
                    capture_id='a4:seed:0123456789abcdef')
        self.assertFalse(comparison_allowed('confirmed', 'a4:seed:0123456789abcdef', 'do_not_state'))


class Structure(unittest.TestCase):
    def test_ids_unique_and_persisted(self):
        for doc in (EXT, SITE):
            ids = [e['id'] for e in doc['entries']]
            self.assertEqual(len(ids), len(set(ids)))
        issued = set(IDS['assigned'].values())
        for e in EXT['entries'] + SITE['entries']:
            self.assertIn(e['id'], issued, e['id'])

    def test_no_identifier_in_two_rendered_rows(self):
        seen = {}
        for e in SITE['entries']:
            if e['ladder'] != 'dataset':
                continue
            ids = {(a['kind'], a['value'].lower()) for a in e['aliases']
                   if a['kind'] in ('hf_repo', 'doi', 'accession', 'eegdash_mirror', 'moabb_loader')}
            if e.get('hf'):
                ids.add(('hf_repo', e['hf']['repo'].lower()))
            for x in ids:
                self.assertNotIn(x, seen, f'{x} in {seen.get(x)} and {e["id"]}')
                seen[x] = e['id']

    def test_no_value_twice_in_a_row(self):
        for doc in (EXT, SITE):
            for e in doc['entries']:
                vals = [a['value'].casefold() for a in e['aliases']]
                self.assertEqual(len(vals), len(set(vals)), (e['id'], vals))
        site = {e['id']: e for e in SITE['entries']}
        zuna = {a['value']: a['kind'] for a in site['r-model-zuna']['aliases']}
        self.assertEqual(zuna['Zyphra/ZUNA1.1'], 'official_weights')
        self.assertEqual({a['value']: a['kind'] for a in site['r-site-alpha-waves']['aliases']}['Rodrigues2017'],
                         'moabb_loader')
        self.assertEqual(X._dedupe([{'value': 'A/b', 'kind': 'name'}, {'value': 'a/B', 'kind': 'hf_repo'}]),
                         [{'value': 'a/B', 'kind': 'hf_repo'}])

    def test_classifier_fields_not_served(self):
        self.assertFalse([e['id'] for e in SITE['entries'] if 'classified' in e])
        self.assertFalse([k for k in SITE['vocab'] if k.startswith('classified')])
        self.assertTrue(all('classified' in e for e in EXT['entries'] if e['kind'] == 'hf_upload'))

    def test_moabb_paper_links_are_papers(self):
        for doc in (EXT, SITE):
            for e in doc['entries']:
                paper = (e.get('urls') or {}).get('paper')
                if paper:
                    self.assertIsNone(X.DATA_DOI.search(paper), (e['id'], paper))
        bi = next(x for x in EXT['entries'] if x.get('moabb') and 'BI2013a' in x['moabb']['loaders'])
        self.assertEqual(bi['urls']['paper'], 'https://arxiv.org/abs/1904.09111')
        self.assertIn('10.5281/zenodo.1494163', bi['moabb']['record_note']['concept_doi'])

    def test_step_evidence_lists_each_source_once(self):
        # Two fields of one research file label as one record: the served item appears once per public source.
        for doc in (EXT, SITE):
            for e in doc['entries']:
                for k, st in e['step_evidence'].items():
                    seen = [(i['item'], i['state'], i['source']) for i in st.get('items', []) or []]
                    self.assertEqual(len(seen), len(set(seen)), (e['id'], k))
        eld = {e['id']: e for e in SITE['entries']}['r-site-eldbeta']
        self.assertEqual([i['item'] for i in eld['step_evidence']['1']['items']].count('host_record'), 1)

    def test_step_evidence_sources_are_single(self):
        for doc in (EXT, SITE):
            for e in doc['entries']:
                for st in e['step_evidence'].values():
                    for it in st.get('items', []) or []:
                        src = it['source']
                        self.assertTrue(src is None or (isinstance(src, str) and ';' not in src and ', ' not in src),
                                        (e['id'], src))
        site = {e['id']: e for e in SITE['entries']}
        scored = [i['source'] for i in site['r-model-neurolm-b']['step_evidence']['4']['items']]
        self.assertEqual(scored, ['site/src/data/neurolm-eegmat-update.json', 'site/src/data/clinical-iesseeg-update.json'])
        self.assertIn('application_required', SITE['vocab']['terms_state'])
        self.assertIn('application_required', Path(X.__file__).read_text().split('"""')[1])

    def test_rules_word_for_word_with_the_pages(self):
        i18n = (X.PROJECT / 'site/src/data/i18n.ts').read_text()
        block = i18n[i18n.index('export const registerCopy'):]
        en = re.search(r"rules: \[(.*?)\],", block[:block.index('zh: {')], re.S).group(1)
        zh = re.search(r"rules: \[(.*?)\],", block[block.index('zh: {'):], re.S).group(1)
        pick = lambda t: [m.group(1) for m in re.finditer(r"'((?:[^'\\]|\\.)*)'", t)]
        self.assertEqual([r['en'] for r in SITE['rules']], pick(en))
        self.assertEqual([r['zh'] for r in SITE['rules']], pick(zh))

    def test_site_file_shape(self):
        self.assertEqual(X.SITE_OUTS[0].read_bytes(), X.SITE_OUTS[1].read_bytes())
        self.assertEqual(SITE['status'], 'frozen')
        self.assertEqual(SITE['release_id'], 'open-register-update-20261020')
        for e in SITE['entries']:
            self.assertNotIn('merge_into', e)
            for k in ('id', 'ladder', 'group', 'kind', 'name', 'aliases', 'source_groups', 'urls', 'terms_as_stated',
                      'access', 'level', 'step_evidence', 'gaps', 'status', 'findings', 'links', 'correction', 'checked'):
                self.assertIn(k, e, (e['id'], k))
            self.assertIn(e['level'], (1, 2, 3, 4, 5))
            self.assertEqual(set(e['step_evidence']), {'1', '2', '3', '4', '5'})
            self.assertIn(e['status'], SITE['vocab']['status'])
        site_rows = {e['id'] for e in SITE['entries'] if e['group'] == 'site'}
        for slug in ('iesseeg', 'eldbeta', 'zuco2', 'lfame', 'shin2022', 'beta'):
            self.assertIn(f'r-site-{slug}', site_rows)
        hf_rows = [e for e in SITE['entries'] if e['group'] == 'hf']
        self.assertEqual(len(hf_rows), EXT['counts']['hf']['single_rows'] + EXT['counts']['hf']['family_rows'])
        for e in hf_rows:
            self.assertEqual(e['level'], 1)

    def test_csv(self):
        self.assertEqual(list(CSV_ROWS[0].keys()), ['id', 'group', 'name', 'host', 'licence_as_stated', 'gated', 'level',
                                                    'gaps', 'status', 'page'])
        ds = [e for e in SITE['entries'] if e['ladder'] == 'dataset']
        self.assertEqual([r['id'] for r in CSV_ROWS], [e['id'] for e in ds])
        text = X.CSV_OUT.read_text()
        for word in ('matches_metadata_of', 'terms_differ', 'derived_from', 'a4:'):
            self.assertNotIn(word, text)
        # The host is the repository holding the record, never the DOI resolver.
        self.assertFalse({r['host'] for r in CSV_ROWS} & {'doi.org', 'dx.doi.org'})
        host = {r['id']: r['host'] for r in CSV_ROWS}
        for rid, want in (('r-site-falcon-h2', 'DANDI'), ('r-site-nlb-mc-rtt', 'DANDI'), ('r-site-zuco2', 'NEMAR'),
                          ('r-site-mobile-bci', 'NEMAR'), ('r-site-gait-eeg', 'PhysioNet'), ('r-site-openbmi', 'GigaDB'),
                          ('r-site-forenzo-continuous-tracking', 'KiltHub'), ('r-site-rabut-fus', 'CaltechDATA'),
                          ('r-site-eldbeta', 'Figshare'), ('r-site-ds003810', 'OpenNeuro'), ('r-site-alpha-waves', 'Zenodo'),
                          ('r-site-iesseeg', 'Hugging Face')):
            self.assertEqual(host[rid], want, rid)
        self.assertEqual(X._host({'group': 'moabb', 'urls': {'record': 'https://doi.org/10.9999/unknown'},
                                  'moabb': {'repository': None}}), '')

    def test_counts_match_entries(self):
        c = SITE['counts']['rows']
        ds = [e for e in SITE['entries'] if e['ladder'] == 'dataset']
        self.assertEqual(c['dataset'], len(ds))
        self.assertEqual(c['dataset_by_group'], dict(sorted(Counter(e['group'] for e in ds).items())))


FROZEN = json.loads(X.SITE_ROWS.read_text())
MANIFEST = X.MANIFEST_OUT
ANCHOR = {1: 'host_record', 2: 'files_opened', 3: 'original_terms', 4: 'fixed_protocol_baseline',
          5: 'comparable_on_protocol_page'}
MODEL_ANCHOR = {1: 'official_record', 2: 'weights_terms', 3: 'files_checked', 4: 'scored_here', 5: 'in_matrix'}


def items_of(e):
    return {(int(k), it['item']): it['state'] for k, b in e['step_evidence'].items() for it in b.get('items', [])}


class Freeze(unittest.TestCase):
    def test_reread_clean_and_census_pinned(self):
        rr = FROZEN['reread']
        self.assertEqual(rr['mismatches'], [])
        self.assertEqual(rr['unresolved'], [])
        self.assertGreater(rr['values_checked'], 500)
        self.assertTrue(rr['a3']['unchanged'])
        self.assertEqual(FROZEN['census']['sha256'], X.sha(X.INPUTS['a5'].read_bytes()))
        self.assertEqual(FROZEN['freeze'], X.D)

    def test_site_rows_are_the_frozen_rows(self):
        site = {e['id']: e for e in SITE['entries'] if e['group'] == 'site'}
        frozen = {f'r-site-{r["slug"]}': r for r in FROZEN['datasets']}
        self.assertEqual(set(site), set(frozen))
        for rid, r in frozen.items():
            e = site[rid]
            for k in ('name', 'level', 'status', 'links', 'terms_as_stated', 'access', 'checked'):
                self.assertEqual(e[k], r[k], (rid, k))
            self.assertEqual(e['gaps'], r['gaps'], rid)
            self.assertEqual({(int(k), i['item'], i['state']) for k, b in e['step_evidence'].items() for i in b['items']},
                             {(int(k), i['item'], i['state']) for k, b in r['step_evidence'].items() for i in b['items']}, rid)
            # A site hold the page does not word yet stays in the site rows and off the served row.
            worded = X.site_hold_words()
            self.assertEqual([(f['code'], f['params']) for f in e['findings']],
                             [(f['code'], X.finding(f['code'], **f['params'])['params']) for f in r['findings']
                              if f['code'] != 'hold' or f['params']['reason_code'] in worded], rid)
            for a in r['aliases']:
                self.assertIn(a['value'].casefold(), {x['value'].casefold() for x in e['aliases']}, (rid, a))
            self.assertNotIn('placeholder', e)

    def test_every_level_is_the_furthest_step_on_file(self):
        for e in SITE['entries']:
            items = items_of(e)
            if not items:
                continue
            anchors = MODEL_ANCHOR if e['ladder'] == 'model' else ANCHOR
            plan = max([k for k in range(1, 6) if items.get((k, anchors[k])) == 'pass'], default=0)
            if e.get('level_cap'):                      # gated data and suspected re-uploads stay at step 1
                plan = min(plan, e['level_cap']['step'])
            self.assertEqual(e['level'], plan, e['id'])
            self.assertEqual(sorted((g['step'], g['item']) for g in e['gaps']),
                             sorted((k, i) for (k, i), v in items.items() if v == 'gap' and k <= plan), e['id'])
        site = {e['id']: e for e in SITE['entries']}
        # Traced from their host records, files never opened: step 3 with files opened as a gap (plan rule).
        for rid in ('r-site-bnci2014-004', 'r-site-physionet-eegmmidb'):
            self.assertEqual(site[rid]['level'], 3)
            self.assertIn((2, 'files_opened'), {(g['step'], g['item']) for g in site[rid]['gaps']})
        bi = next(e for e in SITE['entries'] if e.get('moabb') and 'BI2013a' in e['moabb']['loaders'])
        self.assertEqual((bi['level'], bi['status']), (3, 'planned'))

    def test_named_rows(self):
        site = {e['id']: e for e in SITE['entries']}
        ies, eld, zuco, lfame, shin = (site[f'r-site-{s}'] for s in ('iesseeg', 'eldbeta', 'zuco2', 'lfame', 'shin2022'))
        self.assertEqual((ies['status'], ies['links']['page']), ('published', '/topics/clinical-groups/#iesseeg'))
        self.assertEqual((eld['status'], eld['links']['case']), ('score_held', '/topics/data-quality/#eldbeta'))
        worded = X.site_hold_words()
        self.assertEqual(sorted(f['code'] for f in eld['findings']),
                         sorted(['named_in_corpus'] + (['hold'] if 'one_person_score' in worded else [])))
        self.assertEqual((zuco['status'], zuco['level']), ('status_only', 2))
        self.assertEqual([f['params'] for f in zuco['findings']],
                         [{'reason_code': 'converted_run_timing'}] if 'converted_run_timing' in worded else [])
        self.assertIn((3, 'original_terms'), {(g['step'], g['item']) for g in zuco['next_step_gaps']})
        self.assertEqual([f['code'] for f in lfame['findings']], ['policy_note'])
        self.assertEqual(lfame['terms_as_stated']['value'], 'CC-BY-NC-4.0')
        cat = next(e for e in json.loads(X.INPUTS['moabb_catalog'].read_text())['entries'] if e['Dataset'] == 'Shin2022')
        cf = next(f for f in shin['findings'] if f['code'] == 'catalog_differs_from_files')
        self.assertEqual(cf['params'], {'case': 'shin2022', 'catalog_trials': int(cat['#Trials']),
                                        'catalog_runs': int(cat['#Runs'])})
        self.assertEqual(shin['links'], {'page': '/datasets/shin2022/', 'case': '/topics/data-quality/#shin2022'})
        # ZuCo 2.0: one converted run, said nowhere with a run code or a row value; the row carries no number but its
        # steps.
        nums = []

        def walk(x, k=None):
            if isinstance(x, dict):
                for kk, v in x.items():
                    walk(v, kk)
            elif isinstance(x, list):
                for v in x:
                    walk(v, k)
            elif isinstance(x, (int, float)) and not isinstance(x, bool) and k not in ('level', 'step'):
                nums.append((k, x))
        walk(zuco)
        self.assertEqual(nums, [])
        self.assertFalse(re.search(r'\brun[-_ ]?\d|sub-\d', json.dumps(zuco), re.I))

    def test_alpha_waves_finding_is_sourced(self):
        a = {e['id']: e for e in SITE['entries']}['r-site-alpha-waves']
        vc = next(f for f in a['findings'] if f['code'] == 'version_clarification')
        self.assertEqual((vc['params']['recordings_source'], vc['params']['recordings_evaluated']), (20, 19))
        self.assertIn('site/src/data/evidence-update.json#results.alphawaves.rights.version', vc['sources'])
        self.assertTrue(all(re.match(r'^(?:site/|record:|[a-z_]+#)', s) for s in vc['sources']))
        validate(a['findings'])
        for e in SITE['entries']:
            for f in e['findings']:
                if 'sources' in f:
                    self.assertIn(e['group'], ('site',), e['id'])

    def test_merged_rows_are_aliases(self):
        site = {e['id']: e for e in SITE['entries']}
        self.assertIn(('Bingchuan/BETA', 'hf_repo'), {(a['value'], a['kind']) for a in site['r-site-beta']['aliases']})
        self.assertIn(('Capur/IESSEEG', 'hf_repo'), {(a['value'], a['kind']) for a in site['r-site-iesseeg']['aliases']})
        ext = {e['id']: e for e in EXT['entries']}
        for m in EXT['merges']:
            e = ext[m['row']]
            target = site[('r-site-' if m['ladder'] == 'dataset' else 'r-model-') + m['into']]
            values = {a['value'].lower() for a in target['aliases']}
            for x in ([e['hf']['repo']] if e.get('hf') else []) + ((e.get('moabb') or {}).get('loaders') or []):
                self.assertIn(x.lower(), values, (m['row'], target['id']))
            if m['ladder'] == 'dataset':
                self.assertIn(e['group'], target['source_groups'])
                self.assertNotIn(m['row'], site)

    def test_step_words_are_the_pages(self):
        i18n = (X.PROJECT / 'site/src/data/i18n.ts').read_text()
        for name, ladder in (('datasetLadder', 'dataset'), ('modelLadder', 'model')):
            block = i18n[i18n.index(f'export const {name}'):]
            block = block[:block.index('];')]
            found = re.findall(r"step: (\d), name: \{ en: '([^']*)', zh: '([^']*)' \},\s*needs: \{ en: '([^']*)',\s*zh: '([^']*)' \}",
                               block)
            self.assertEqual(len(found), 5)
            for k, en, zh, nen, nzh in found:
                d = SITE['level_definitions'][ladder][k]
                self.assertEqual((d['en'], d['zh'], d['needs_en'], d['needs_zh']), (en, zh, nen, nzh), (ladder, k))

    def test_manifest_and_provenance(self):
        prov = SITE['provenance']
        self.assertEqual(prov['manifest_sha256'], X.sha(MANIFEST.read_bytes()))
        self.assertEqual(prov['site_rows_sha256'], X.sha(X.SITE_ROWS.read_bytes()))
        self.assertEqual(prov['external_sha256'], X.sha(X.EXTERNAL_OUT.read_bytes()))
        man = json.loads(MANIFEST.read_text())
        self.assertEqual(man['release_id'], 'open-register-update-20261020')
        for label, pin in man['sources'].items():
            self.assertEqual(X.sha((X.PROJECT / pin['path']).read_bytes()), pin['sha256'], label)
        self.assertEqual(man['freeze']['mismatches'], [])
        audit = json.loads(X.EXPORT_AUDIT_OUT.read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertEqual(audit['export_sha256'], X.sha(X.SITE_OUTS[0].read_bytes()))
        self.assertEqual(audit['manifest_sha256'], prov['manifest_sha256'])

    def test_model_rows_cover_the_methods_page(self):
        models = {e['id']: e for e in SITE['entries'] if e['ladder'] == 'model'}
        site_models = [r for r in FROZEN['models'] if r['kind'] == 'site_model']
        self.assertEqual(len(site_models), 20)
        for r in FROZEN['models']:
            e = models[f'r-model-{r["key"]}']
            self.assertEqual((e['kind'], e['name'], e['level']), (r['kind'], r['name'], r['level']))
            self.assertEqual(set(e['terms_by_part']), {'code', 'weights', 'data'})
            self.assertTrue(e['model_kind'] and e['signal'])
        for name in ('Spectral ridge', 'Temporal ridge', 'BIOT', 'Signal-JEPA', 'BENDR', 'CSBrain', 'Neuro-GPT',
                     'EEG-Conformer', 'EEGSimpleConv', 'MIRepNet', 'EEG-DINO'):
            self.assertTrue(any(e['name'] == name and e['kind'] == 'model' for e in models.values()), name)
        eegpt = models['r-model-eegpt']
        self.assertEqual((eegpt['level'], [(g['step'], g['item']) for g in eegpt['gaps']]), (4, [(2, 'weights_terms')]))
        self.assertEqual(eegpt['terms_by_part']['weights']['state'], 'not_found')
        for slug in ('fbcca', 'etrca'):        # scored on the deployment pages, not in the core matrix
            self.assertEqual(models[f'r-model-{slug}']['level'], 4)
        m = SITE['counts']['models']
        self.assertEqual(m['external_rows'] - m['merged_into_site_methods'],
                         sum(1 for e in models.values() if e['kind'] == 'model'))
        zuna = models['r-model-zuna']
        self.assertEqual((zuna['name'], zuna['exposure']), ('ZUNA', 'unknown'))
        self.assertNotIn('openreview', json.dumps(list(models.values())).lower())

    def test_catalog_counts_come_together(self):
        with self.assertRaises(FindingError):
            finding('catalog_differs_from_files', case='shin2022', catalog_trials=2640)
        with self.assertRaises(FindingError):
            validate([{**finding('hold', reason_code='planned_pilot' if False else 'one_offline_session'),
                       'sources': ['not a source']}])


class SiteHolds(unittest.TestCase):
    """The holds on eldBETA and ZuCo 2.0: always in the site rows, served once the page words their reason codes."""
    WORDS = ("const holdReason: Record<string, T> = {\n"
             "  weights_licence_not_found: { en: 'Held: no licence found for the weights.', zh: '暂缓：没有找到权重的许可。' },\n"
             "  converted_run_timing: { en: 'Held: in one converted run, some fixation times fall outside the recording.',\n"
             "                          zh: '暂缓：在一个转换后记录中，有些注视时间落在记录之外。' },\n"
             "  one_person_score: { en: 'Held: with one person, every score is that person’s.', zh: '' },\n"
             "};\n")

    def test_site_rows_carry_both_holds_with_their_sources(self):
        rows = {r['slug']: r for r in FROZEN['datasets']}
        for slug, code in (('eldbeta', 'one_person_score'), ('zuco2', 'converted_run_timing')):
            holds = [f for f in rows[slug]['findings'] if f['code'] == 'hold']
            hold_id = SITE_HOLD_REASONS[code]
            self.assertEqual(holds, [{'code': 'hold', 'params': {'reason_code': code},
                                      'sources': [f'site/src/data/releases.ts#holds[id={hold_id}]',
                                                  f'site/src/data/data-quality-update.json#holds[id={hold_id}]']}], slug)
            validate(holds)

    def test_words_are_read_from_the_page_module(self):
        with tempfile.TemporaryDirectory() as d:
            ts = Path(d) / 'open-register.ts'
            ts.write_text('const x = 1;\n/** Hold reasons */\n' + self.WORDS + 'const policyNote = {};\n')
            old, X.SITE_REGISTER_MODULE = X.SITE_REGISTER_MODULE, ts
            try:
                # Words in both languages for converted_run_timing; an empty Chinese string is no words.
                self.assertEqual(X.site_hold_words(), {'converted_run_timing'})
            finally:
                X.SITE_REGISTER_MODULE = old

    def test_served_file_declares_exactly_the_worded_holds(self):
        worded = X.site_hold_words()
        declared = set(SITE['finding_codes']['hold']['reason_codes'])
        self.assertEqual(declared & set(SITE_HOLD_REASONS), worded)
        self.assertEqual(set(EXT['finding_codes']['hold']['reason_codes']) & set(SITE_HOLD_REASONS), set())
        for e in SITE['entries']:
            for f in e['findings']:
                if f['code'] == 'hold':
                    self.assertIn(f['params']['reason_code'], declared, e['id'])
        man = json.loads(MANIFEST.read_text())['site_holds']
        self.assertEqual(set(man['worded_on_site']), worded)
        self.assertEqual(set(man['withheld_until_worded']),
                         {f'r-site-{s}:{c}' for s, c in (('eldbeta', 'one_person_score'), ('zuco2', 'converted_run_timing'))
                          if c not in worded})
        with self.assertRaises(FindingError):
            finding_schema({'not_a_site_hold'})

    def test_a_worded_build_attaches_both(self):
        old = X.site_hold_words
        X.site_hold_words = lambda: set(SITE_HOLD_REASONS)
        try:
            b = X.Build(fresh_ids=False, freeze=True)
            b.run()
            _, site = b.documents()
        finally:
            X.site_hold_words = old
        self.assertEqual(b.site_holds_withheld, [])
        self.assertTrue(set(SITE_HOLD_REASONS) <= set(site['finding_codes']['hold']['reason_codes']))
        rows = {e['id']: e for e in site['entries']}
        self.assertEqual([f['params'] for f in rows['r-site-zuco2']['findings']], [{'reason_code': 'converted_run_timing'}])
        self.assertIn({'reason_code': 'one_person_score'}, [f['params'] for f in rows['r-site-eldbeta']['findings']])
        for rid in ('r-site-zuco2', 'r-site-eldbeta'):
            hold = next(f for f in rows[rid]['findings'] if f['code'] == 'hold')
            self.assertTrue(all(s.startswith('site/src/data/') for s in hold['sources']), rid)
            validate(rows[rid]['findings'])


class IdMapUnit(unittest.TestCase):
    def test_stable_and_never_reused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'ids.json'
            m = IdMap.fresh(p)
            a, b = m.numbered('hf', 'hf:a/x'), m.numbered('hf', 'hf:b/y')
            m.save()
            m2 = IdMap.load(p)
            self.assertEqual(m2.numbered('hf', 'hf:b/y'), b)
            m2.retire_unseen(('hf',))
            m2.save()
            m3 = IdMap.load(p)
            c = m3.numbered('hf', 'hf:c/z')
            self.assertNotIn(c, (a, b))
            self.assertEqual(m3.numbered('hf', 'hf:a/x'), a)      # a returning key keeps its number
            self.assertEqual(m3.slug('corpus', 'seed'), 'r-corpus-seed')


if __name__ == '__main__':
    unittest.main()
