"""Build the step-evidence census (A3) of the 20261028 register round: the four dataset rows this round promotes from
MOABB catalog rows to this site's rows, and the three model rows it scores.

    python3 research/publication_review_20261028/register/build_site_step_evidence.py          # write the census
    python3 research/publication_review_20261028/register/build_site_step_evidence.py --check  # rebuild and compare

It follows research/publication_review_20261020/notes/site-step-evidence.json (A5): every item is pass, gap or
not-applicable with the file and field it rests on, and every value recorded is read here from that field, never typed.
The census only reads; the register's site-row exporter (site/scripts/export-site-register-rows.mjs) re-reads every
value against the live files at the freeze, and export_open_register.py builds the three model rows from it.

Sources: the dataset-checks, NeuroRVQ and ten-second payloads (served), the A2 consent, ethics and terms record of this
round (research/publication_review_20261028/evidence/consent-statements.json), the owner's decisions of this round,
and the intake records the payloads pin (research files, cited by record hash once served).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
D = '20261028'
OUT = PROJECT / f'research/publication_review_{D}/register/site-step-evidence-{D}.json'
A5 = 'research/publication_review_20261020/notes/site-step-evidence.json'

DC = 'site/src/data/dataset-checks-update.json'
NR = 'site/src/data/neurorvq-update.json'
TS = 'site/src/data/eegmat-ten-second-update.json'
A2 = f'research/publication_review_{D}/evidence/consent-statements.json'
OWNER = f'research/publication_review_{D}/owner-decisions.json'
REL = 'site/src/data/releases.ts'
RF = 'research/research_refresh_20261025/models/EEG model refresh evidence.json'
NR_LOAD = 'research/autonomous_validation_20261026/neurorvq/review/strict-load-acceptance.json'
CAP_LISTING = 'research/autonomous_validation_20261026/scans/models/captioner.json'
CAP_INTAKE = 'research/autonomous_validation_20261026/eeg_captioner/EEG-Captioner Encoder Intake Handoff.md'
AX_LISTING = 'research/autonomous_validation_20261026/scans/models/axon.json'
AX_ADMISSION = 'research/autonomous_validation_20261026/axon_load_admission_20261027/Final Checkpoint Intake Result Admission.json'
HF_MODELS = 'research/open_register_20261019/raw/hf-model-listing.json'

ITEM_STEP = {'host_record': 1, 'licence_as_stated': 1, 'files_opened': 2, 'rights_reviewed': 3, 'derivation': 3,
             'original_terms': 3, 'consent_ethics': 3, 'pinned_version': 3, 'fixed_protocol_baseline': 4,
             'chance_stated': 4, 'share_above_chance': 4, 'result_or_hold_on_page': 4, 'comparable_on_protocol_page': 5}
ANCHOR = {1: 'host_record', 2: 'files_opened', 3: 'original_terms', 4: 'fixed_protocol_baseline',
          5: 'comparable_on_protocol_page'}
MODEL_ITEM_STEP = {'official_record': 1, 'code_terms': 2, 'weights_terms': 2, 'data_terms': 2, 'file_listing': 2,
                   'files_checked': 3, 'scored_here': 4, 'in_matrix': 5}
MODEL_ANCHOR = {1: 'official_record', 2: 'weights_terms', 3: 'files_checked', 4: 'scored_here', 5: 'in_matrix'}
PRIVATE = re.compile(r'/(?:Users|home|Volumes|mnt|root|private)/|\btrx50\b|\bGal4\b|BCI_Arena|\btwu\b', re.I)

_json: dict[str, object] = {}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_json(f: str):
    if f not in _json:
        _json[f] = json.loads((PROJECT / f).read_text())
    return _json[f]


def select(root, selector: str):
    """The census's selector grammar (A5): dotted keys, [key=value] filters, [n] indices."""
    cur = root
    for m in re.finditer(r'([^.\[\]]+)|\[([^\]]+)\]', selector):
        if cur is None:
            return None
        if m.group(1) is not None:
            cur = cur.get(m.group(1)) if isinstance(cur, dict) else None
            continue
        inner = m.group(2)
        if inner.isdigit():
            cur = cur[int(inner)] if isinstance(cur, list) and int(inner) < len(cur) else None
            continue
        k, eq, v = inner.partition('=')
        if not eq:
            return None
        cur = next((x for x in cur if isinstance(x, dict) and str(x.get(k)) == v), None) if isinstance(cur, list) else None
    return cur


def src(file: str, field: str, value: bool = True) -> dict:
    """One source, its value read from the file (value=False: the field is only required to be there)."""
    out = {'file': file, 'field': field, 'served': file.startswith('site/')}
    if field.startswith('text: '):
        if field[6:] not in (PROJECT / file).read_text():
            raise ValueError(f'{file}: the quoted text {field[6:]!r} is not in the file')
        return out
    if file.endswith('.ts'):
        m = re.match(r'^holds\[id=([^\]]+)\]$', field)
        if not m or f"id: '{m.group(1)}'" not in (PROJECT / file).read_text():
            raise ValueError(f'{file}: no hold {field}')
        return out
    v = select(read_json(file), field)
    if v is None:
        raise ValueError(f'{file}#{field}: not in the file')
    if value:
        out['value'] = v
    return out


def item(name: str, state: str, sources: list[dict], note: str | None = None, **extra) -> dict:
    it = {'item': name, 'state': state}
    it.update(extra)
    it['sources'] = sources
    if note:
        it['note'] = note
    return it


def level_of(steps: dict, anchor: dict) -> tuple[int, int]:
    passed = lambda k: any(i['item'] == anchor[k] and i['state'] == 'pass' for i in steps.get(str(k), []))
    plan = max([k for k in range(1, 6) if passed(k)], default=0)
    contiguous = 0
    for k in range(1, 6):
        if not passed(k):
            break
        contiguous = k
    return plan, contiguous


def gap_list(steps: dict, defs: dict, level: int, which: str) -> list[dict]:
    out = []
    for k in sorted(steps, key=int):
        for it in steps[k]:
            if it['state'] != 'gap':
                continue
            if (which == 'gaps' and int(k) <= level) or (which == 'next' and int(k) == level + 1):
                g = {'step': int(k), 'item': it['item'], 'label_en': defs[it['item']]['label_en'],
                     'label_zh': defs[it['item']]['label_zh']}
                if it.get('note'):
                    g['note'] = it['note']
                if g not in out:
                    out.append(g)
    return out


# ------------------------------------------------------------------------------------------- dataset rows
def dataset_sources(defs: dict) -> list[dict]:
    dc = read_json(DC)
    kim, mind, damm, neb = dc['kim2025-beta-range'], dc['mind2026'], dc['damm'], dc['nebula']
    fig_id = lambda url: re.search(r'figshare\.(\d+)', url).group(1)
    owner = 'decisions.{}.answer'
    rows = []

    # Kim beta-range (owner decisions D14, D21): a worked case and a dataset page; amplitude-dependent models held.
    k = 'kim2025-beta-range'
    rows.append({
        'id': f'site-{k}',
        'name': kim['name'],
        'census_group': 'dataset_checks',
        'site': {'page': None, 'status': 'published at freeze', 'register_status': 'published',
                 'page_at_freeze': dc['placement']['dataset_pages'][k], 'case': f'{dc["placement"]["page"]}#{kim["section"]}'},
        'identity': {'record': kim['rights']['source'], 'moabb_loader': 'Kim2025BetaRange',
                     'moabb_row_merged': 'r-moabb-0071'},
        'hold': {'id': kim['hold']['id'], 'reason_code': 'amplitude_units_unresolved',
                 'replaces_catalog_hold': 'onset_timing_unresolved'},
        'steps': {
            '1': [item('host_record', 'pass', [src(A2, f'sources.{k}.licence.data.read_from'),
                                               src(A2, f'sources.{k}.licence.data.capture_sha256'),
                                               src(DC, f'{k}.rights.source')]),
                  item('licence_as_stated', 'pass', [src(DC, f'{k}.rights.license'),
                                                     src(A2, f'sources.{k}.licence.data.value')])],
            '2': [item('files_opened', 'pass', [src(DC, f'{k}.intake.task_files'), src(DC, f'{k}.intake.md5_matched')],
                       'All task files passed their MD5 checks before any score; the rest and questionnaire files were '
                       'not acquired.')],
            '3': [item('rights_reviewed', 'pass', [src(OWNER, owner.format('D14')), src(DC, f'{k}.rights.reviewedAt')]),
                  item('derivation', 'pass', [src(DC, f'{k}.rights.version'), src(DC, f'{k}.intake.rest_and_questionnaire_acquired')],
                       'The authors\' Figshare deposit at its latest version, the task files only.'),
                  item('original_terms', 'pass', [src(A2, f'sources.{k}.licence.data.value'),
                                                  src(A2, f'sources.{k}.licence.data.stated_by'),
                                                  src(A2, f'sources.{k}.licence.data.paper_cited_version.licence')],
                       'The record\'s licence field at the version used and at the version the paper cites.'),
                  item('consent_ethics', 'pass', [src(A2, f'sources.{k}.consent_quote'), src(A2, f'sources.{k}.ethics_quote'),
                                                  src(A2, f'sources.{k}.capture_sha256')],
                       'Signed consent, including open sharing, and the GIST IRB approval, quoted from the data descriptor.',
                       parts={'consent': 'pass', 'ethics': 'pass'}),
                  item('pinned_version', 'pass', [src(DC, f'{k}.rights.terms.data_licence.pinned_version'),
                                                  src(DC, f'{k}.rights.terms.data_licence.pinned_version_is_latest')])],
            '4': [item('fixed_protocol_baseline', 'pass', [src(DC, f'provenance.source_export_sha256.{k}'),
                                                           src(DC, f'{k}.method.training_free')],
                       'Training-free CCA on every trial of every participant, independently audited.'),
                  item('chance_stated', 'pass', [src(DC, f'{k}.result.chance'), src(DC, f'{k}.result.chance_basis')]),
                  item('share_above_chance', 'gap', [],
                       'Not computed: no export carries a count of participants above chance (owner default D12).'),
                  item('result_or_hold_on_page', 'pass', [src(DC, f'placement.dataset_pages.{k}'), src(DC, 'placement.sections'),
                                                          src(REL, f'holds[id={kim["hold"]["id"]}]')])],
            '5': [item('comparable_on_protocol_page', 'gap', [], 'Outside the core matrix and every leaderboard.')],
        },
    })

    # MIND (owner decision D15): a conditional case on record IDs; four licence statements disagree.
    k = 'mind2026'
    rows.append({
        'id': f'site-{k}',
        'name': f'MIND · multimodal fNIRS-EEG unilateral limb motor imagery (ScienceDB {mind["rights"]["source"].rsplit(".", 1)[1]})',
        'census_group': 'dataset_checks',
        'site': {'page': None, 'status': 'published at freeze', 'register_status': 'published',
                 'case': f'{dc["placement"]["page"]}#{mind["section"]}'},
        'identity': {'record': mind['rights']['source'], 'moabb_loader': 'MIND2026', 'moabb_row_merged': 'r-moabb-0095'},
        'steps': {
            '1': [item('host_record', 'pass', [src(A2, f'sources.{k}.licence.sciencedb_record.read_from'),
                                               src(A2, f'sources.{k}.licence.sciencedb_record.capture_sha256'),
                                               src(DC, f'{k}.rights.source')]),
                  item('licence_as_stated', 'pass', [src(DC, f'{k}.rights.licenses_stated'),
                                                     src(A2, f'sources.{k}.licence.sciencedb_record.value')],
                       'Both licences side by side, as this site\'s rights record states them (owner decision D15).')],
            '2': [item('files_opened', 'pass', [src(DC, f'{k}.coverage[id=runs_in_release].count'),
                                                src(DC, f'{k}.coverage[id=runs_evaluated].count')])],
            '3': [item('rights_reviewed', 'pass', [src(OWNER, owner.format('D15')), src(DC, f'{k}.rights.reviewedAt')]),
                  item('derivation', 'pass', [src(DC, f'{k}.rights.source'), src(DC, f'{k}.processing.auxiliary_channels_used')],
                       'The authors\' ScienceDB deposit, its EEG only.'),
                  item('original_terms', 'gap', [src(DC, f'{k}.rights.terms.statements', value=False),
                                                 src(DC, f'{k}.rights.terms.terms_of_use_page_read')],
                       'Four statements disagree: the paper and the archive\'s dataset description state CC BY 4.0, the '
                       'MOABB adapter and the ScienceDB record\'s metadata CC BY-NC 4.0; the ScienceDB terms-of-use page '
                       'was not read.'),
                  item('consent_ethics', 'pass', [src(A2, f'sources.{k}.consent_quote'), src(A2, f'sources.{k}.ethics_quote'),
                                                  src(A2, f'sources.{k}.ethics_consent_source.capture_sha256')],
                       'Written consent and an ethics approval stated in the paper; the committee is not named and no '
                       'approval number is given.', parts={'consent': 'pass', 'ethics': 'pass'}),
                  item('pinned_version', 'gap', [src(DC, f'{k}.rights.version'),
                                                 src(DC, f'{k}.rights.terms.publisher_checksum_verified')],
                       'The record version is named, and the files used are matched by local hashes only, with no '
                       'publisher checksum.')],
            '4': [item('fixed_protocol_baseline', 'pass', [src(DC, f'provenance.source_export_sha256.{k}'),
                                                           src(DC, f'{k}.primary.pairs', value=False)],
                       'CSP + LDA with two controls on stored codes, independently audited.'),
                  item('chance_stated', 'gap', [src(DC, f'{k}.processing.controls', value=False)],
                       'No chance-level field; the majority and ordinal-lookup controls are published beside the model.'),
                  item('share_above_chance', 'gap', [],
                       'Not computed: no export carries a count of record IDs above chance (owner default D12).'),
                  item('result_or_hold_on_page', 'pass', [src(DC, 'placement.sections')])],
            '5': [item('comparable_on_protocol_page', 'gap', [], 'Outside the core matrix and every leaderboard.')],
        },
    })

    # Damm finger motor imagery (owner decision D16): one participant, the score held; consent and the LICENSE file gaps.
    k, case = 'damm-finger-imagery', 'damm'
    rows.append({
        'id': f'site-{k}',
        'name': f'Damm finger motor imagery · random and sequential order (OpenNeuro '
                f'{re.search(r"openneuro[.](ds[0-9]+)", damm["rights"]["source"]).group(1)})',
        'census_group': 'dataset_checks',
        'site': {'page': None, 'status': 'score held at freeze', 'register_status': 'score held',
                 'case': f'{dc["placement"]["page"]}#{damm["section"]}'},
        'identity': {'record': damm['rights']['source'], 'moabb_loader': 'Damm2026', 'moabb_row_merged': 'r-moabb-0048'},
        'hold': {'id': damm['held']['id'], 'reason_code': 'one_person_score'},
        'steps': {
            '1': [item('host_record', 'pass', [src(A2, f'sources.{case}.licence.data.read_from'),
                                               src(A2, f'sources.{case}.licence.data.capture_sha256'),
                                               src(DC, f'{case}.rights.source')]),
                  item('licence_as_stated', 'pass', [src(DC, f'{case}.rights.license'), src(A2, f'sources.{case}.licence.data.value')])],
            '2': [item('files_opened', 'pass', [src(DC, f'{case}.files.edf_channels'), src(DC, f'{case}.files.state_blocks_per_run')],
                       'One participant\'s two random-order runs read end to end.')],
            '3': [item('rights_reviewed', 'gap', [src(A2, f'sources.{case}.licence.license_file.present'),
                                                  src(DC, f'{case}.rights.terms.license_file_present')],
                       'The rights review stays open: the README cites a LICENSE file that the tree at the pinned commit '
                       'does not hold.'),
                  item('derivation', 'pass', [src(DC, f'{case}.rights.version')],
                       'The authors\' OpenNeuro deposit, read at a pinned commit of its mirror.'),
                  item('original_terms', 'pass', [src(A2, f'sources.{case}.licence.data.value'),
                                                  src(A2, f'sources.{case}.licence.data.stated_by')],
                       'CC0 in dataset_description.json at the pinned commit, the only licence statement.'),
                  item('consent_ethics', 'gap', [src(A2, f'sources.{case}.ethics_quote'), src(A2, f'sources.{case}.consent.stated')],
                       'The ethics approval is stated; no consent statement was found in the dataset files or metadata, '
                       'and no paper is named.', parts={'consent': 'gap', 'ethics': 'pass'}),
                  item('pinned_version', 'pass', [src(DC, f'{case}.rights.pinned_commit'), src(DC, f'{case}.rights.pinned_snapshot')])],
            '4': [item('fixed_protocol_baseline', 'pass', [src(DC, f'provenance.protocol_sha256.{case}'),
                                                           src(DC, f'{case}.flags.independent_audit_passed')],
                       'A fixed pipeline with variants and controls set before scoring, independently audited; the score '
                       'is held (owner decision D16).'),
                  item('chance_stated', 'gap', [], 'No chance-level field; the scores are held.'),
                  item('share_above_chance', 'not-applicable', [], 'One participant: a share would be that person\'s held result.'),
                  item('result_or_hold_on_page', 'pass', [src(DC, f'holds[id={damm["held"]["id"]}].state'),
                                                          src(REL, f'holds[id={damm["held"]["id"]}]')])],
            '5': [item('comparable_on_protocol_page', 'gap', [], 'Outside the core matrix and every leaderboard.')],
        },
    })

    # NeBULA (owner decision D16): one participant, the scores held. Its Figshare record is the only registered one; the
    # Zenodo DOI its files name is no registered record and is no alias of this row.
    k = 'nebula'
    rows.append({
        'id': f'site-{k}',
        'name': f'NeBULA · EEG-EMG standardized reaching task (Figshare {fig_id(neb["rights"]["source"])})',
        'census_group': 'dataset_checks',
        'site': {'page': None, 'status': 'score held at freeze', 'register_status': 'score held',
                 'case': f'{dc["placement"]["page"]}#{neb["section"]}'},
        'identity': {'record': neb['rights']['source'], 'moabb_loader': 'NeBULA2025', 'moabb_row_merged': 'r-moabb-0106',
                     'not_an_alias': {'value': '10.5281/zenodo.13627307',
                                      'why': 'named by the files\' own dataset description; no registered public record'}},
        'hold': {'id': neb['held']['id'], 'reason_code': 'one_person_score'},
        'steps': {
            '1': [item('host_record', 'pass', [src(A2, f'sources.{k}.licence.data.read_from'),
                                               src(A2, f'sources.{k}.licence.data.capture_sha256'),
                                               src(DC, f'{k}.rights.source')]),
                  item('licence_as_stated', 'pass', [src(DC, f'{k}.rights.license'), src(A2, f'sources.{k}.licence.data.value')])],
            '2': [item('files_opened', 'pass', [src(DC, f'{k}.design.participant_counts'),
                                                src(DC, f'{k}.file_facts.markers_match_eeg_files'),
                                                src(DC, f'{k}.file_facts.emg_channel_rows'),
                                                src(DC, f'{k}.file_facts.emg_channels_in_metadata')],
                       'One participant\'s EEG and EMG files read end to end: the EMG layout, and the stored markers '
                       'against the EEG marker files; participants as the record states them and as its files hold them.')],
            '3': [item('rights_reviewed', 'pass', [src(OWNER, owner.format('D16')), src(DC, f'{k}.rights.reviewedAt')]),
                  item('derivation', 'pass', [src(DC, f'{k}.rights.version'),
                                              src(A2, f'sources.{k}.licence.zenodo_13627307.resolves')],
                       'The authors\' Figshare record, its only version; the Zenodo DOI the files\' own description names '
                       'resolves to no registered record.'),
                  item('original_terms', 'pass', [src(A2, f'sources.{k}.licence.data.value'),
                                                  src(A2, f'sources.{k}.licence.data.stated_by')]),
                  item('consent_ethics', 'pass', [src(A2, f'sources.{k}.consent_quote'), src(A2, f'sources.{k}.ethics_quote'),
                                                  src(A2, f'sources.{k}.capture_sha256')],
                       'Consent to take part and to share the data openly, and the CER Liguria approval, quoted from the '
                       'data descriptor.', parts={'consent': 'pass', 'ethics': 'pass'}),
                  item('pinned_version', 'pass', [src(DC, f'{k}.rights.terms.data_licence.pinned_version'),
                                                  src(DC, f'{k}.rights.terms.data_licence.versions_listed')])],
            '4': [item('fixed_protocol_baseline', 'pass', [src(DC, f'provenance.protocol_sha256.{k}_eeg'),
                                                           src(DC, f'{k}.arms.independently_audited')],
                       'EEG, EMG and EEG plus EMG arms with controls, independently audited; the scores are held (owner '
                       'decision D16).'),
                  item('chance_stated', 'gap', [], 'No chance-level field; the scores are held.'),
                  item('share_above_chance', 'not-applicable', [], 'One participant: a share would be that person\'s held result.'),
                  item('result_or_hold_on_page', 'pass', [src(DC, f'holds[id={neb["held"]["id"]}].state'),
                                                          src(REL, f'holds[id={neb["held"]["id"]}]')])],
            '5': [item('comparable_on_protocol_page', 'gap', [], 'Outside the core matrix and every leaderboard.')],
        },
    })

    for r in rows:
        for k, its in r['steps'].items():
            for it in its:
                if ITEM_STEP[it['item']] != int(k):
                    raise ValueError(f'{r["id"]}: {it["item"]} is not a step-{k} item')
        plan, contiguous = level_of(r['steps'], ANCHOR)
        r['level'] = plan
        r['level_name'] = {'en': {4: 'Run'}[plan], 'zh': {4: '已运行'}[plan]}
        r['level_contiguous'] = contiguous
        # The census's recommendation, as A5 defines it: the plan rule, unless the files were never opened.
        r['level_recommended'] = plan
        r['gaps'] = gap_list(r['steps'], defs, plan, 'gaps')
        r['next_step_gaps'] = gap_list(r['steps'], defs, plan, 'next')
    return rows


# --------------------------------------------------------------------------------------------- model rows
def model_entries() -> list[dict]:
    nr, ts = read_json(NR), read_json(TS)
    defs = {
        'official_record': ('official record', '官方记录'), 'code_terms': ('code licence', '代码许可'),
        'weights_terms': ('weights licence', '权重许可'), 'data_terms': ('data terms', '数据条款'),
        'file_listing': ('file listing', '文件列表'), 'files_checked': ('files checked', '文件核验'),
        'scored_here': ('scored here', '本站评分'), 'in_matrix': ('core matrix', '核心矩阵'),
    }
    rows = []
    rf_nr = 'candidates[id=neurorvq]'
    rows.append({'key': 'neurorvq', 'row': 'r-model-neurorvq', 'name': nr['model']['name'], 'case': '/topics/pilot-studies/#'
                 + nr['placement']['anchor'], 'steps': {
        '1': [item('official_record', 'pass', [src(RF, f'{rf_nr}.paper'), src(NR, 'model.paper'), src(NR, 'model.repository')])],
        '2': [item('code_terms', 'pass', [src(NR, 'rights.code.licence'), src(RF, f'{rf_nr}.access.code_license')]),
              item('weights_terms', 'pass', [src(NR, 'rights.weights.licence'), src(NR, 'rights.weights.same_file_as_code')]),
              item('data_terms', 'gap', [src(NR, 'pretraining_exposure.published_pretraining_list')],
                   'The paper lists its pretraining corpora, one of them proprietary, whose terms are not public.'),
              item('file_listing', 'pass', [src(RF, f'{rf_nr}.access.checkpoint_files', value=False),
                                            src(NR, 'model.checkpoint.revision')])],
        '3': [item('files_checked', 'pass', [src(NR, 'model.checkpoint.sha256'), src(NR, 'model.restore.trained_tensors'),
                                             src(NR_LOAD, 'decision')],
                   'The checkpoint matched its SHA-256 and the backbone restored strictly; the authors\' wrapper does not.')],
        '4': [item('scored_here', 'pass', [src(NR, 'blocks', value=False)])],
        '5': [item('in_matrix', 'gap', [], 'A separate pilot panel, outside the core matrix (owner decision D19).')],
    }})
    cap = ts['eeg_captioner']
    rows.append({'key': 'eeg-captioner', 'row': 'r-model-eeg-captioner', 'name': 'EEG-Captioner',
                 'case': '/topics/pilot-studies/#' + ts['placement']['anchor'], 'steps': {
        '1': [item('official_record', 'pass', [src(TS, 'eeg_captioner.identity.hf_repository'),
                                               src(TS, 'eeg_captioner.identity.hf_revision'),
                                               src(TS, 'eeg_captioner.identity.source_repository'),
                                               src(TS, 'eeg_captioner.identity.source_revision')])],
        '2': [item('code_terms', 'pass', [src(TS, 'eeg_captioner.rights.code.licence')]),
              item('weights_terms', 'pass', [src(TS, 'eeg_captioner.rights.weights.licence'), src(CAP_LISTING, 'cardData.license')]),
              item('data_terms', 'gap', [], 'No terms for the training data are recorded on this row.'),
              item('file_listing', 'pass', [src(CAP_LISTING, 'siblings', value=False), src(CAP_LISTING, 'sha')])],
        '3': [item('files_checked', 'pass', [src(TS, 'eeg_captioner.identity.encoder_sha256'),
                                             src(CAP_INTAKE, 'text: All 98 state entries matched exactly by key, shape, dtype and value')],
                   'The encoder matched its SHA-256 and restored strictly; only the encoder was loaded.')],
        '4': [item('scored_here', 'pass', [src(TS, 'eeg_captioner.arms', value=False)])],
        '5': [item('in_matrix', 'gap', [], 'A separate pilot panel, outside the core matrix.')],
    }})
    ax = ts['axon']
    rows.append({'key': 'axon', 'row': 'r-model-axon', 'name': ax['name'],
                 'case': '/topics/pilot-studies/#' + ts['placement']['anchor'], 'steps': {
        '1': [item('official_record', 'pass', [src(TS, 'axon.identity.hf_repository'), src(TS, 'axon.identity.hf_revision'),
                                               src(HF_MODELS, 'models.MannasAI/axon-eeg.listing.sha'),
                                               src(TS, 'axon.identity.source_revision')])],
        '2': [item('code_terms', 'pass', [src(TS, 'axon.rights.module.licence'), src(TS, 'axon.rights.project.licence')]),
              item('weights_terms', 'pass', [src(TS, 'axon.rights.checkpoint.licence'), src(AX_LISTING, 'cardData.license')]),
              item('data_terms', 'gap', [], 'The model card does not name its full pretraining corpus.'),
              item('file_listing', 'pass', [src(AX_LISTING, 'siblings', value=False), src(AX_LISTING, 'sha')])],
        '3': [item('files_checked', 'pass', [src(TS, 'axon.identity.checkpoint_sha256'), src(TS, 'axon.identity.checkpoint_bytes'),
                                             src(AX_ADMISSION, 'status')],
                   'The checkpoint matched its size and SHA-256; its header was checked before a strict load.')],
        '4': [item('scored_here', 'pass', [src(TS, 'axon.arms', value=False)])],
        '5': [item('in_matrix', 'gap', [], 'A separate pilot panel, outside the core matrix.')],
    }})
    for r in rows:
        for k, its in r['steps'].items():
            for it in its:
                if MODEL_ITEM_STEP[it['item']] != int(k):
                    raise ValueError(f'{r["row"]}: {it["item"]} is not a step-{k} item')
        plan, contiguous = level_of(r['steps'], MODEL_ANCHOR)
        r['level'] = plan
        r['level_contiguous'] = contiguous
        d = {k: {'label_en': v[0], 'label_zh': v[1]} for k, v in defs.items()}
        r['gaps'] = gap_list(r['steps'], d, plan, 'gaps')
        r['next_step_gaps'] = gap_list(r['steps'], d, plan, 'next')
    return rows


def build() -> dict:
    a5 = json.loads((PROJECT / A5).read_text())
    defs = a5['item_definitions']
    datasets = dataset_sources(defs)
    models = model_entries()
    files = sorted({s['file'] for r in datasets for its in r['steps'].values() for it in its for s in it['sources']}
                   | {s['file'] for r in models for its in r['steps'].values() for it in its for s in it['sources']} | {A5})
    inputs = [{'file': f, 'sha256': sha((PROJECT / f).read_bytes()), 'bytes': (PROJECT / f).stat().st_size,
               'served': f.startswith('site/')} for f in files]
    doc = {
        'schema_version': 'bci-report-site-step-evidence-v1',
        'package': 'A3',
        'release_freeze': D,
        'generated_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        'purpose': ('Step evidence for the four dataset rows the 20261028 round promotes from MOABB catalog rows to this '
                    'site\'s rows (Kim beta-range, MIND, Damm finger imagery, NeBULA) and for the three model rows it '
                    'scores (NeuroRVQ, EEG-Captioner, AXON), for the open register (plan section 3, package A3). '
                    'Read-only census in the shape of the 20261020 census (A5), which it extends: every item is pass, gap '
                    'or not-applicable with the file and field it rests on.'),
        'extends': {'file': A5, 'sha256': sha((PROJECT / A5).read_bytes())},
        'how_to_read': a5['how_to_read'],
        'step_definitions': a5['step_definitions'],
        'item_definitions': defs,
        'census_groups': [{'id': 'dataset_checks', 'description': 'The four dataset checks of dataset-checks-update.json; '
                           'each merges its MOABB record group', 'count': len(datasets)}],
        'consent_record': {'file': A2, 'sha256': sha((PROJECT / A2).read_bytes()),
                           'affects': [r['id'] for r in datasets]},
        'summary': {
            'sources': len(datasets), 'models': len(models),
            'by_level': {str(k): sum(1 for r in datasets if r['level'] == k) for k in sorted({r['level'] for r in datasets})},
            'gaps_by_item': {g: sum(1 for r in datasets for x in r['gaps'] if x['item'] == g)
                             for g in sorted({x['item'] for r in datasets for x in r['gaps']})},
            'model_levels': {r['row']: r['level'] for r in models},
        },
        'sources': datasets,
        'models': models,
        'inputs': inputs,
        'boundaries': [
            'Read-only: no site file or research folder of another session was changed; no network.',
            'No participant-level rows, identifiers, demographics or signal values are carried; values are licence '
            'strings, versions, counts the served files already print, quotes of consent and ethics statements, and hashes.',
            'No private absolute paths: every path is repo-relative. Research files reach a served file by record hash only.',
        ],
    }
    text = json.dumps(doc, ensure_ascii=False)
    if PRIVATE.search(re.sub(r'https?://[^\s"]+', ' ', text)):
        raise ValueError('the census carries a private path or host name')
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    doc = build()
    if args.check:
        # Every value and state as recorded; the inputs' hashes are reported, not compared (served files change between
        # packages, as the site-row exporter's re-read reports them).
        old = json.loads(OUT.read_text())
        drop = ('generated_at', 'inputs')
        same = {k: v for k, v in old.items() if k not in drop} == {k: v for k, v in doc.items() if k not in drop}
        was = {i['file']: i['sha256'] for i in old['inputs']}
        drift = [i['file'] for i in doc['inputs'] if was.get(i['file']) != i['sha256']]
        print(('census unchanged' if same else 'census differs') + (f'; inputs changed since: {drift}' if drift else ''))
        return 0 if same else 1
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    s = doc['summary']
    print(f'{OUT.relative_to(PROJECT)}: {s["sources"]} dataset rows {s["by_level"]}, gaps {s["gaps_by_item"]}; '
          f'models {s["model_levels"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
