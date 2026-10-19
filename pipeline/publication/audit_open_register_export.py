"""Independent audit of the frozen open register (package B8b of the 20261020 release).

    python3 pipeline/publication/audit_open_register_export.py          # audit and write the audit record
    python3 pipeline/publication/audit_open_register_export.py --check  # audit only; exit 1 on any failure

A separate program from the export: it imports nothing from export_open_register.py or the site-row exporter. It reads
the served bytes (site/src/data and site/public/data), the release manifest and the files the manifest pins, the A5
census, the MOABB catalog, i18n.ts as text and the external rows file, and re-derives from them what the served file
must say: every site row from the census (its level by the plan rule, its gaps, its status, its findings), every merge
of an external row into a site row, the counts, the CSV, and the words the register may never carry. It writes
research/publication_review_20261020/register/open-register-export-audit.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
D = '20261020'
RELEASE = f'open-register-update-{D}'
REVIEW = PROJECT / f'research/publication_review_{D}'
REGISTER = REVIEW / 'register'
SERVED = (PROJECT / f'site/src/data/open-register-{D}.json', PROJECT / f'site/public/data/open-register-{D}.json')
CSV_PATH = PROJECT / f'site/public/data/open-register-{D}.csv'
MANIFEST = REGISTER / 'open-register-release-manifest.json'
EXTERNAL = REGISTER / f'open-register-external-{D}.json'
SITE_ROWS = REGISTER / f'site-register-rows-{D}.json'
A5 = REVIEW / 'notes/site-step-evidence.json'
MOABB_CATALOG = PROJECT / 'research/moabb_expansion_20261019/evidence/moabb-catalog.json'
I18N = PROJECT / 'site/src/data/i18n.ts'
REGISTER_TS = PROJECT / 'site/src/data/open-register.ts'
RELEASES_TS = PROJECT / 'site/src/data/releases.ts'
DATA_QUALITY = PROJECT / 'site/src/data/data-quality-update.json'
OUT = REGISTER / 'open-register-export-audit.json'

ANCHOR = {1: 'host_record', 2: 'files_opened', 3: 'original_terms', 4: 'fixed_protocol_baseline',
          5: 'comparable_on_protocol_page'}
MODEL_ANCHOR = {1: 'official_record', 2: 'weights_terms', 3: 'files_checked', 4: 'scored_here', 5: 'in_matrix'}
STATUS = {'published': 'published', 'score held': 'score_held', 'status only': 'status_only', 'listed': 'listed',
          'planned': 'planned'}
# What the register never carries (the site rules, D4, D6, the HF boundary), assembled so this file does not spell all.
FORBIDDEN_TEXT = [r'/(?:Users|home|Volumes|mnt)/', r'\btrx50\b', r'\bGal4\b', 'BCI_Arena', r'\btwu\b',
                  'IC' + r'LR\s*2027', 'open' + 'review', r'\bsub' + r'mission\b', r'(?<![\d.])55 ?%']
FORBIDDEN_KEYS = {'downloads', 'likes', 'createdAt', 'lastModified', 'description', 'readme', 'one_line_en', 'one_line_zh',
                  'notes', 'trendingScore', 'consent_or_ethics_statement', 'source_claim', 'Gender',
                  'Age Mean', 'Age Min', 'Age Max', 'Handedness'}
# The holds this release opens on two site rows (plan section 2.6): row -> (reason code, hold id on the site).
SITE_HOLDS = {'r-site-eldbeta': ('one_person_score', 'eldbeta-one-participant-score'),
              'r-site-zuco2': ('converted_run_timing', 'zuco2-converted-run-timing')}
# The model and MOABB hold reasons B8a declares (the page words all of them).
BASE_HOLD_REASONS = {'released_ids_duplicated', 'targets_stored_with_outputs', 'deposits_differ', 'onset_timing_unresolved',
                     'release_family_unchecked', 'one_offline_session', 'weights_licence_not_found',
                     'code_licence_not_found', 'no_released_checkpoint', 'code_not_reachable', 'not_human_scalp_eeg',
                     'noncommercial_noderivs_weights', 'acceptance_not_verified', 'data_not_public'}
# A record DOI's repository by registrant prefix, as this audit states it (the CSV's host is never the resolver).
DOI_REPOSITORY = {'10.18112': 'OpenNeuro', '10.5281': 'Zenodo', '10.6084': 'Figshare', '10.25452': 'Figshare',
                  '10.48324': 'DANDI', '10.82901': 'NEMAR', '10.13026': 'PhysioNet', '10.5524': 'GigaDB',
                  '10.1184': 'KiltHub', '10.22002': 'CaltechDATA'}
PARTICIPANT = re.compile(r'(?<![a-z0-9])(?:sub|subj|subject|participant|pt)[-_ ]?\d+(?![a-z0-9])', re.I)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


class Audit:
    def __init__(self):
        self.checks: list[dict] = []
        self.failures: list[str] = []

    def ok(self, name: str, cond: bool, detail: str = '') -> None:
        self.checks.append({'check': name, 'pass': bool(cond)})
        if not cond:
            self.failures.append(f'{name}{": " + detail if detail else ""}')

    # ------------------------------------------------------------------------------------------------ the files
    def run(self) -> dict:
        raw = [p.read_bytes() for p in SERVED]
        self.ok('the two served copies are byte-identical', raw[0] == raw[1])
        R = json.loads(raw[0])
        man_bytes = MANIFEST.read_bytes()
        M = json.loads(man_bytes)
        ext_bytes = EXTERNAL.read_bytes()
        X = json.loads(ext_bytes)
        S = json.loads(SITE_ROWS.read_text())
        census = json.loads(A5.read_text())
        self.ok('the release and the frozen status', R['release_id'] == RELEASE and R['status'] == 'frozen'
                and M['release_id'] == RELEASE)
        prov = R.get('provenance') or {}
        self.ok('the served file names the manifest it was built from', prov.get('manifest_sha256') == sha(man_bytes))
        self.ok('the served file names the site rows and external rows it merges',
                prov.get('site_rows_sha256') == sha(SITE_ROWS.read_bytes()) and prov.get('external_sha256') == sha(ext_bytes))
        drift = [label for label, pin in M['sources'].items()
                 if not (PROJECT / pin['path']).exists() or sha((PROJECT / pin['path']).read_bytes()) != pin['sha256']]
        self.ok('every file the manifest pins has the SHA-256 it gives', not drift, ', '.join(drift))
        self.ok('the site rows were re-read cleanly at the freeze',
                not S['reread']['mismatches'] and not S['reread']['unresolved'] and S['census']['sha256'] == sha(A5.read_bytes()))
        rows = R['entries']
        by_id = {e['id']: e for e in rows}
        self.ok('every row id is unique', len(by_id) == len(rows))
        self.ok('every row id is opaque', all(re.match(r'^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|model-[a-z0-9-]+|'
                                                       r'site-[a-z0-9-]+)$', e['id']) for e in rows))
        self.ok('every row has its correction mail', all(
            e['correction']['mailto'] == f'mailto:contact@bci.report?subject=Register%20row%20{e["id"]}' for e in rows))
        self.site_dataset_rows(R, census, by_id)
        self.named_rows(R, census, by_id)
        self.merges(R, X, by_id)
        self.model_rows(R, S, by_id)
        self.counts(R)
        self.csv_file(R)
        self.site_holds(R, M)
        self.evidence_items(R)
        self.words(R)
        self.ladders(R)
        return {'R': R, 'manifest_sha256': sha(man_bytes), 'export_sha256': sha(raw[0])}

    # ------------------------------------------------------------------------------------------------ site rows
    @staticmethod
    def slug_of(src: dict) -> str:
        site = src.get('site') or {}
        page = site.get('page') or site.get('page_at_freeze')
        if page and page.startswith('/datasets/'):
            return page.split('/')[2]
        return re.sub(r'-\d+\.\d+\.\d+$', '', src['id'].removeprefix('site-').removeprefix('register-'))

    def site_dataset_rows(self, R, census, by_id) -> None:
        sources = [s for s in census['sources'] if s['census_group'] != 'adjacent_moabb']
        want = {f'r-site-{self.slug_of(s)}': s for s in sources}
        have = {e['id'] for e in R['entries'] if e['group'] == 'site'}
        self.ok('one site row per census source, and no other', set(want) == have,
                f'{sorted(set(want) ^ have)}')
        freeze_items = {'shin2022', 'iesseeg', 'eldbeta', 'zuco2'}
        level_rule_deviation = []
        for rid, src in want.items():
            e = by_id.get(rid)
            if not e:
                continue
            slug = rid.removeprefix('r-site-')
            # The census's item states, with the result-or-hold item passing at the freeze for the four rows whose page,
            # section or hold this release adds.
            states = {}
            for step, items in src['steps'].items():
                for it in items:
                    st = it['state']
                    if slug in freeze_items and it['item'] == 'result_or_hold_on_page':
                        st = 'pass'
                    states[(int(step), it['item'])] = st
            served = {}
            for step, block in e['step_evidence'].items():
                for it in block.get('items', []):
                    served.setdefault((int(step), it['item']), set()).add(it['state'])
            self.ok(f'{rid}: its evidence items are the census\'s, item by item',
                    all(served.get(k) == {v} for k, v in states.items()) and set(served) == set(states))
            plan = max([k for k in range(1, 6) if states.get((k, ANCHOR[k])) == 'pass'], default=0)
            self.ok(f'{rid}: its level is the furthest step whose anchor is on file', e['level'] == plan,
                    f'{e["level"]} != {plan}')
            gaps = sorted((k, i) for (k, i), v in states.items() if v == 'gap' and k <= plan)
            self.ok(f'{rid}: its gaps are the items missing at or below its level',
                    sorted((g['step'], g['item']) for g in e['gaps']) == gaps)
            if plan != src.get('level_recommended', plan):
                level_rule_deviation.append(rid)
            self.ok(f'{rid}: its status is the census\'s', e['status'] == STATUS[src['site']['register_status']])
            self.ok(f'{rid}: one correction route, a site group', e['group'] == 'site' and 'site' in e['source_groups'])
        self.level_rule_deviation = level_rule_deviation

    def named_rows(self, R, census, by_id) -> None:
        """The rows the package names: IESSEEG, eldBETA (score held), ZuCo 2.0, L-FAME, Shin2022, alpha-waves."""
        g = lambda i: by_id.get(i) or {}
        ies, eld, zuco, lfame, shin, alpha = (g('r-site-iesseeg'), g('r-site-eldbeta'), g('r-site-zuco2'),
                                              g('r-site-lfame'), g('r-site-shin2022'), g('r-site-alpha-waves'))
        self.ok('IESSEEG: published, linking its clinical-groups section, its card\'s repo as an alias',
                ies.get('status') == 'published' and ies.get('links', {}).get('page') == '/topics/clinical-groups/#iesseeg'
                and any(a['value'] == 'Capur/IESSEEG' for a in ies.get('aliases', [])))
        worded = self.worded_holds()
        self.ok('eldBETA: score held, its case linked, no score in the row',
                eld.get('status') == 'score_held' and eld.get('links', {}).get('case') == '/topics/data-quality/#eldbeta'
                and sorted(f['code'] for f in eld.get('findings', []))
                == sorted(['named_in_corpus'] + (['hold'] if 'one_person_score' in worded else [])))
        sing = [f for f in eld.get('findings', []) if f['code'] == 'named_in_corpus']
        self.ok('eldBETA: named in SingLEM\'s corpus, release resolved',
                sing and sing[0]['params'] == {'models': ['SingLEM'], 'release_resolved': True})
        self.ok('ZuCo 2.0: status only at step 2, its case linked, no figure in the row',
                zuco.get('status') == 'status_only' and zuco.get('level') == 2
                and zuco.get('links', {}).get('case') == '/topics/data-quality/#zuco2'
                and [f['code'] for f in zuco.get('findings', [])] == (['hold'] if 'converted_run_timing' in worded else []))
        self.ok('ZuCo 2.0: what stops it at step 2 is listed (original terms among the step-3 items)',
                'original_terms' in {g['item'] for g in zuco.get('next_step_gaps', []) if g['step'] == 3})
        self.ok('L-FAME: status only at step 2 with its policy note',
                lfame.get('status') == 'status_only' and lfame.get('level') == 2
                and [f['code'] for f in lfame.get('findings', [])] == ['policy_note']
                and lfame['findings'][0]['params'] == {'source': 'lfame'})
        cat = next((e for e in json.loads(MOABB_CATALOG.read_text())['entries'] if e['Dataset'] == 'Shin2022'), None)
        cf = [f for f in shin.get('findings', []) if f['code'] == 'catalog_differs_from_files']
        self.ok('Shin2022: its page and case, and MOABB\'s catalog counts as listed in the catalog',
                shin.get('links', {}).get('page') == '/datasets/shin2022/' and cf and cat
                and cf[0]['params'] == {'case': 'shin2022', 'catalog_trials': int(cat['#Trials']), 'catalog_runs': int(cat['#Runs'])})
        src = next(s for s in census['sources'] if s['id'] == 'site-alpha-waves')
        vc = next(f for f in src['findings'] if f['code'] == 'version_clarification')
        served = [f for f in alpha.get('findings', []) if f['code'] == 'version_clarification']
        want = {k: vc['params'][k] for k in ('current', 'earlier', 'recordings_source', 'recordings_evaluated')}
        n_sources = len({(s['file'], s['field']) for fact in vc['facts'] for s in fact['sources']})
        self.ok('alpha-waves: the version finding as the census states it',
                served and served[0]['params'] == want)
        # Sourced: one public source per distinct census source (research files by record hash, which may coincide).
        site_sources = {f'{s["file"]}#{s["field"]}' for fact in vc['facts'] for s in fact['sources'] if s['file'].startswith('site/')}
        self.ok('alpha-waves: the finding carries its sources',
                served and served[0].get('sources') and site_sources <= set(served[0]['sources'])
                and 0 < len(served[0]['sources']) <= n_sources)
        self.ok('the core rows link the pretraining-exposure block', all(
            re.fullmatch(r'/protocols/(beta-8ch|mi-rest|idle|p300-target|arithmetic-rest|semantic-target|sleep-scalp)/#pretraining-exposure', by_id[f'r-site-{self.slug_of(s)}']['links'].get('exposure') or '')
            for s in census['sources'] if s['census_group'] == 'core'))

    def merges(self, R, X, by_id) -> None:
        ext = {e['id']: e for e in X['entries']}
        bad = []
        for m in X['merges']:
            e = ext[m['row']]
            if m['row'] in by_id and by_id[m['row']].get('kind') == e['kind']:
                bad.append(f'{m["row"]} still rendered')
            target = by_id.get(f'r-site-{m["into"]}' if m['ladder'] == 'dataset' else f'r-model-{m["into"]}')
            if not target:
                bad.append(f'{m["row"]}: no row {m["into"]}')
                continue
            vals = {a['value'].lower() for a in target['aliases']}
            idents = ([e['hf']['repo']] if e.get('hf') else []) + ((e.get('moabb') or {}).get('loaders') or []) \
                + ([e['moabb']['doi']] if (e.get('moabb') or {}).get('doi') else []) \
                + [a['value'] for a in e['aliases'] if a['kind'] in ('official_weights', 'weights_copy')]
            missing = [x for x in idents if x.lower() not in vals and x != target['name']]
            if missing:
                bad.append(f'{m["row"]} → {target["id"]}: {missing} not aliases')
            if m['ladder'] == 'dataset' and e['group'] not in target['source_groups']:
                bad.append(f'{m["row"]}: group {e["group"]} not in {target["id"]}\'s source groups')
        self.ok('every merged external row is folded into its site row: its ids are the row\'s aliases', not bad, '; '.join(bad))
        self.ok('the Hugging Face repos of BETA and IESSEEG are aliases of their site rows',
                any(a['value'] == 'Bingchuan/BETA' and a['kind'] == 'hf_repo' for a in by_id['r-site-beta']['aliases'])
                and any(a['value'] == 'Capur/IESSEEG' and a['kind'] == 'hf_repo' for a in by_id['r-site-iesseeg']['aliases']))
        seen, dup = {}, []
        for e in R['entries']:
            if e['ladder'] != 'dataset':
                continue
            ids = {(a['kind'], a['value'].lower()) for a in e['aliases']
                   if a['kind'] in ('hf_repo', 'doi', 'accession', 'eegdash_mirror', 'moabb_loader')}
            if e.get('hf'):
                ids.add(('hf_repo', e['hf']['repo'].lower()))
            for x in ids:
                if x in seen and seen[x] != e['id']:
                    dup.append(f'{x} in {seen[x]} and {e["id"]}')
                seen[x] = e['id']
        self.ok('no DOI, accession or repo id in two dataset rows', not dup, '; '.join(dup[:5]))

    def model_rows(self, R, S, by_id) -> None:
        models = [e for e in R['entries'] if e['ladder'] == 'model']
        site = {f'r-model-{r["key"]}': r for r in S['models']}
        self.ok('every model row the site builds is served', set(site) <= set(by_id))
        bad = []
        for e in models:
            if not e.get('terms_by_part') or set(e['terms_by_part']) != {'code', 'weights', 'data'}:
                bad.append(f'{e["id"]}: terms by part')
            if not e.get('model_kind') or not e.get('signal'):
                bad.append(f'{e["id"]}: kind or signal')
            items = {(int(k), it['item']): it['state'] for k, b in e['step_evidence'].items() for it in b.get('items', [])}
            plan = max([k for k in range(1, 6) if items.get((k, MODEL_ANCHOR[k])) == 'pass'], default=0)
            if items and e['level'] != plan:
                bad.append(f'{e["id"]}: level {e["level"]}, its anchors reach {plan}')
            if items and sorted((g['step'], g['item']) for g in e['gaps']) != sorted(
                    (k, i) for (k, i), v in items.items() if v == 'gap' and k <= e['level']):
                bad.append(f'{e["id"]}: gaps')
            if e['kind'] == 'site_model' and not (e.get('links', {}).get('page') or '').startswith('/methods/'):
                bad.append(f'{e["id"]}: no method page')
        self.ok('every model row: terms by part, kind and signal, its level by its anchors, its gaps', not bad, '; '.join(bad))
        n = by_id.get('r-model-neurolm-b') or {}
        self.ok('NeuroLM-B at step 4, linking both pilots, exposure unknown',
                n.get('level') == 4 and set(n.get('links', {}).get('cases', [])) == {
                    '/topics/pilot-studies/#neurolm-eegmat', '/topics/clinical-groups/#iesseeg'} and n.get('exposure') == 'unknown')
        self.ok('no model row carries a venue field D4 keeps off', not any(
            re.search('iclr|sub' + 'mission|open' + 'review|venue_status', k, re.I) for k in keys(models)))

    def counts(self, R) -> None:
        rows = R['entries']
        ds = [e for e in rows if e['ladder'] == 'dataset']
        ms = [e for e in rows if e['ladder'] == 'model']
        c = R['counts']['rows']
        self.ok('the counts are the rows', c['total'] == len(rows) and c['dataset'] == len(ds) and c['model'] == len(ms)
                and c['dataset_by_group'] == dict(sorted(Counter(e['group'] for e in ds).items()))
                and c['dataset_by_level'] == {str(k): v for k, v in sorted(Counter(e['level'] for e in ds).items())}
                and c['model_by_level'] == {str(k): v for k, v in sorted(Counter(e['level'] for e in ms).items())}
                and c['by_status'] == dict(sorted(Counter(e['status'] for e in rows).items())))
        m = R['counts']['models']
        self.ok('the model counts: rows outside method pages are those read, less those merged',
                m['external_rows'] - m['merged_into_site_methods'] == sum(1 for e in ms if e['kind'] == 'model'))
        hf = R['counts']['hf']
        self.ok('the Hugging Face counts add up (D11 population with its re-check)',
                hf['classifier_in_scope'] - hf['recheck_out_simulated'] - hf['recheck_out_emg_rule']
                - hf['recheck_out_undetermined'] == hf['in_scope']
                and hf['in_scope'] == hf['single_rows'] + hf['family_members'] + hf['merged_into_site_rows'] + hf.get('merged_into_moabb_rows', 0) + hf['held_for_review']
                and hf['single_rows'] + hf['family_rows'] == c['dataset_by_group']['hf'])

    def csv_file(self, R) -> None:
        text = CSV_PATH.read_text()
        rows = list(csv.DictReader(io.StringIO(text)))
        ds = [e for e in R['entries'] if e['ladder'] == 'dataset']
        self.ok('the CSV: the dataset ladder, one row per entry, in order',
                list(rows[0].keys()) == ['id', 'group', 'name', 'host', 'licence_as_stated', 'gated', 'level', 'gaps',
                                         'status', 'page'] and [r['id'] for r in rows] == [e['id'] for e in ds])
        self.ok('the CSV agrees with the JSON on every row', all(
            r['group'] == e['group'] and r['name'] == e['name'] and int(r['level']) == e['level'] and r['status'] == e['status']
            and r['licence_as_stated'] == (e['terms_as_stated'].get('value') or '') for r, e in zip(rows, ds)))
        self.ok('the CSV carries no findings', not re.search(r'matches_metadata_of|terms_differ|derived_from|a4:', text))
        self.ok('the CSV never names the DOI resolver as a host', not any(r['host'] in ('doi.org', 'dx.doi.org') for r in rows))
        wrong = []
        for r, e in zip(rows, ds):
            url = (e.get('urls') or {}).get('record') or ''
            m = re.match(r'https?://(?:dx\.)?doi\.org/(10\.\d+)/', url)
            if m and m.group(1) in DOI_REPOSITORY and r['host'] != DOI_REPOSITORY[m.group(1)]:
                wrong.append(f'{e["id"]}: {r["host"]}')
            if e['group'] in ('hf', 'eegdash') and r['host'] != 'Hugging Face':
                wrong.append(f'{e["id"]}: {r["host"]}')
        self.ok('the CSV host of a DOI record is its registrant\'s repository', not wrong, ', '.join(wrong[:5]))

    @staticmethod
    def worded_holds() -> set[str]:
        """The site hold reasons open-register.ts words in both languages (its holdReason table, read as text)."""
        t = REGISTER_TS.read_text()
        start = t.index('const holdReason')
        block = t[start:t.index('\n};', start)]
        return {code for code, _ in SITE_HOLDS.values()
                if re.search(rf"\n  {code}: \{{ en: '[^']+',\s*zh: '[^']+' \}}", block)}

    def site_holds(self, R, M) -> None:
        """The two site holds: declared and attached exactly where the page words them, each sourced to its hold."""
        worded = self.worded_holds()
        declared = set(R['finding_codes']['hold']['reason_codes'])
        self.ok('the hold reasons declared: B8a\'s, and the site holds the page words',
                declared == BASE_HOLD_REASONS | worded, f'{sorted(declared ^ (BASE_HOLD_REASONS | worded))}')
        undeclared = [e['id'] for e in R['entries'] for f in e['findings']
                      if f['code'] == 'hold' and f['params']['reason_code'] not in declared]
        self.ok('every hold finding\'s reason is declared', not undeclared, ', '.join(undeclared))
        rel_text, dq = RELEASES_TS.read_text(), json.loads(DATA_QUALITY.read_text())
        for rid, (code, hold_id) in SITE_HOLDS.items():
            e = next((x for x in R['entries'] if x['id'] == rid), {})
            holds = [f for f in e.get('findings', []) if f['code'] == 'hold']
            self.ok(f'{rid}: the hold {hold_id} is open on the site', f"id: '{hold_id}'" in rel_text
                    and any(h['id'] == hold_id for h in dq['holds']))
            want = [{'code': 'hold', 'params': {'reason_code': code},
                     'sources': [f'site/src/data/releases.ts#holds[id={hold_id}]',
                                 f'site/src/data/data-quality-update.json#holds[id={hold_id}]']}] if code in worded else []
            self.ok(f'{rid}: its hold finding ({code}) is served where the page words it, with its sources',
                    holds == want, f'{holds} != {want}')
        sh = M.get('site_holds') or {}
        self.ok('the manifest records the site holds as served',
                set(sh.get('worded_on_site', [])) == worded
                and set(sh.get('withheld_until_worded', [])) == {f'{r}:{c}' for r, (c, _) in SITE_HOLDS.items() if c not in worded})

    def evidence_items(self, R) -> None:
        """Each step's evidence lists an item once per public source."""
        dup = [f'{e["id"]} step {k}' for e in R['entries'] for k, b in e['step_evidence'].items()
               if len({(i['item'], i['state'], i['source']) for i in b.get('items', [])}) != len(b.get('items', []))]
        self.ok('no evidence item repeats its item, state and source within a step', not dup, ', '.join(dup[:5]))

    def words(self, R) -> None:
        text = re.sub(r'https?://[^\s"]+', ' ', json.dumps(R, ensure_ascii=False))
        hits = [p for p in FORBIDDEN_TEXT if re.search(p, text, re.I)]
        self.ok('no private path, D4 reference or "55%" anywhere in the served file', not hits, str(hits))
        self.ok('no card text, counts, dates, demographics or classifier fields',
                not (set(keys(R)) & FORBIDDEN_KEYS) and not any('classified' in e for e in R['entries'])
                and not any(k.startswith('classified') for k in R['vocab']), str(set(keys(R)) & FORBIDDEN_KEYS))
        self.ok('no participant-like id in any string', not any(PARTICIPANT.search(s) for s in strings(R)))
        self.ok('no research path in the served file', not re.search(r'research/|publication_review_', text))

    def ladders(self, R) -> None:
        t = I18N.read_text()
        bad = []
        for name, ladder in (('datasetLadder', 'dataset'), ('modelLadder', 'model')):
            block = t[t.index(f'export const {name}'):]
            block = block[:block.index('];')]
            for m in re.finditer(r"step: (\d), name: \{ en: '([^']*)', zh: '([^']*)' \},\s*needs: \{ en: '([^']*)',\s*zh: '([^']*)' \}",
                                 block):
                d = R['level_definitions'][ladder][m.group(1)]
                if (d['en'], d['zh'], d['needs_en'], d['needs_zh']) != m.group(2, 3, 4, 5):
                    bad.append(f'{ladder} {m.group(1)}')
        self.ok('the step names and needs are the pages\' (i18n.ts), word for word', not bad, ', '.join(bad))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    a = Audit()
    out = a.run()
    R = out['R']
    rec = {
        'status': 'pass' if not a.failures else 'fail',
        'release_id': RELEASE,
        'export_sha256': out['export_sha256'],
        'manifest_sha256': out['manifest_sha256'],
        'csv_sha256': sha(CSV_PATH.read_bytes()),
        'auditor': 'pipeline/publication/audit_open_register_export.py',
        'independence': ('A separate program from the export, importing nothing from it or from the site-row exporter. '
                         'It reads the served bytes, the release manifest and the files it pins, the A5 census, the '
                         'MOABB catalog (the export reads the shortlist), i18n.ts as text and the external rows, and '
                         're-derives every site row\'s level, gaps and status from the census, every merge from the '
                         'external rows, the counts from the rows and the CSV from the JSON.'),
        'rows': {'total': R['counts']['rows']['total'], 'dataset': R['counts']['rows']['dataset'],
                 'model': R['counts']['rows']['model'], 'site_dataset': R['counts']['rows']['dataset_by_group']['site']},
        'level_rule': ('the furthest step whose anchor item is on file, gaps at or below it; rows where this differs from '
                       'the census\'s recommended contiguous step: ' + ', '.join(a.level_rule_deviation)),
        'checks_run': len(a.checks),
        'checks': sorted({c['check'] for c in a.checks if not c['check'].startswith('r-')})
                  + [f'{sum(1 for c in a.checks if c["check"].startswith("r-"))} per-row checks over the site rows'],
        'failures': a.failures,
    }
    if not args.check:
        OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(f'{rec["status"]}: {len(a.checks)} checks, {len(a.failures)} failures')
    for f in a.failures:
        print('  FAIL', f)
    return 0 if not a.failures else 1


if __name__ == '__main__':
    sys.exit(main())
