"""Build the open register (wave 1): every EEG dataset and model we know of, and how far we checked it.

    python3 pipeline/publication/export_open_register.py               # the frozen register (B8b, the default)
    python3 pipeline/publication/export_open_register.py --provisional # B8a's provisional site file (placeholders)
    python3 pipeline/publication/export_open_register.py --check       # build and compare with the files on disk

Packages B8a and B8b of the 20261020 release. B8a built the external rows and a provisional site file; B8b freezes
the site rows. At the freeze (the default) this script first runs site/scripts/export-site-register-rows.mjs, which
re-reads entities.ts and the A5 census against the live files and writes
research/publication_review_20261020/register/site-register-rows-20261020.json; the site rows of the served file are
those rows, with the aliases of every external row that merges into them (``merge_into``: MOABB record groups,
Hugging Face repos of site datasets such as Bingchuan/BETA and Capur/IESSEEG, EEGDash mirrors), and the served file's
status is ``frozen``. It also writes the release manifest (open-register-release-manifest.json, beside the external
file), whose SHA-256 the served file carries as ``provenance.manifest_sha256``; the independent audit
(audit_open_register_export.py) writes open-register-export-audit.json. It writes:
- research/publication_review_20261020/register/open-register-external-20261020.json  the external rows
  (Hugging Face uploads, the EEGDash family, MOABB record groups, the agreement corpora, the model rows), with
  rows that are this site's own datasets or methods marked ``merge_into``;
- research/publication_review_20261020/register/register-ids.json  the persisted opaque-id map;
- site/src/data/open-register-20261020.json and a byte-identical site/public/data copy: a PROVISIONAL register
  (``status: "provisional"``) = the external rows plus placeholder site rows built from the A5 census
  (notes/site-step-evidence.json), so page packages can build against the real shape. Package B8b replaces the
  site rows from entities.ts + A5 at the freeze and sets ``status: "frozen"``;
- site/public/data/open-register-20261020.csv  the dataset ladder, flat, with no findings column.

==============================================================================================================
JSON SCHEMA  (schema_version "bci-report-open-register-v1"; the external file uses the same entry shape)
==============================================================================================================
Top level
  provenance            frozen site file only: {manifest, manifest_sha256, site_rows_sha256, external_sha256}
  schema_version        "bci-report-open-register-v1"
  release_id            "open-register-update-20261020"
  status                "provisional" (B8a) | "frozen" (B8b)   [site file]   |  "external" [external file]
  generated_at          ISO time of the build
  level_definitions     {dataset: {"1".."5": {en, zh, needs_en, needs_zh, items[]}}, model: {same shape}}
                        dataset steps: 1 Listed/已列出, 2 Read/已读取, 3 Traced/已追溯, 4 Run/已运行, 5 In the matrix/已进入核心矩阵
                        model steps:   1 Identified/已识别, 2 Terms recorded/已记录条款, 3 Files checked/已检查文件,
                                       4 Scored here/已在本站评分, 5 In the matrix/已进入核心矩阵
  item_definitions      {dataset: {item: {step, label_en, label_zh, anchor}}, model: {...}}
  rules                 [{id, en, zh}]   the register's rules, stated once (word for word as site/src/data/i18n.ts
                        registerCopy.rules)
  sources               {hf: {retrieved_at, search_terms[], tag_filters[], population}, eegdash: {...},
                         moabb: {release, docs_commit, catalog_checked}, access_terms: [{capture_id, family_slug,
                         family, url, captured_at, sha256, capture_kind, access_kind}], site_census: {...},
                         models: {...}, inputs: [{label, sha256 | files+digest_sha256, served}]}
                        (research inputs appear by label and hash only; the external file adds provenance_paths)
  counts                {rows, hf, eegdash, moabb, corpus, models}   every number a JSON value for data-fig.
                        counts.hf.in_scope = classifier_in_scope - recheck_out_simulated - recheck_out_emg_rule -
                        recheck_out_undetermined; recheck_signoff "pending" until the owner or R2 confirms the
                        re-check, so a page prints in_scope only beside that basis
  finding_codes         {code: {params: {name: kind}, optional[]}} (+ hold.reason_codes, matches_metadata_of.fields,
                        terms_differ.declared_by)
  vocab                 closed token lists used in entries (access, status, by, signal, model_kind, terms_state;
                        external file also classified_by, classified_modality, classified_paradigm,
                        classified_content_kind)
  families[]            uploader series and the EEGDash family, with no member repo id that looks like a
                        participant id: {id, kind: "hf_series"|"eegdash", ...}
                          hf_series: {id, kind, uploader, series, n, search_url, licence_tag_counts{tag: n},
                                      no_licence_tag, gated{manual, auto}, size_bytes, member_digest}
                          eegdash:   {id: r-corpus-openneuro-mirrors, kind, n, by_accession_kind{openneuro, nemar,
                                      other}, licence_tag_counts, site_rows_with_mirror, members[{mirror, accession,
                                      accession_kind, licence_tags[], gated, site_row?, moabb_row?}]}
  entries[]             the rows (shape below). In the site file only rendered rows; rows with merge_into are
                        folded into their site row as aliases (one alias per value, the most specific kind kept).
  id_map_sha256         sha256 of register-ids.json as written by this build
  external file only:   merges[{row, into, ladder}]; site_model_aliases{method_slug: [weights_copy aliases]} for B8b;
                        population_recheck{source, status, rules, counts{rule: n}, excluded_digest_sha256,
                          excluded[{repo, rule}], excluded_participant_like{rule: n}} (the classifier audit's
                          re-check; repo ids that look like participant ids are counted, never listed);
                        comparison_review[{row, repo, verdict, withheld[], a4_families_matched_by_name[],
                          families_kept[], families_dropped[], basis{family: {fields[], original_source_phrase}}}]
                          (the D3 gate row by row,
                          for R2 / F3 review);
                        provenance_paths{label: repo-relative path}
  Encoding: compact JSON, one entry per line.

Entry (one register row)
  id                    opaque: r-hf-NNNN | r-moabb-NNNN | r-corpus-<family> | r-model-<slug> | r-site-<slug>
  ladder                "dataset" | "model"
  group                 dataset: "hf" | "eegdash" | "site" | "moabb" | "corpus";  model: "model"
  kind                  hf_upload | hf_family | eegdash_family | site_dataset | moabb_record_group |
                        agreement_corpus | model | site_model
  name                  the row's name (an HF row: its repo id; a family: 'uploader/stem*')
  aliases[]             {value, kind, licence_tag?, relation?, relation_to?}
                        kind: hf_repo | moabb_loader | accession | doi | eegdash_mirror | name | weights_copy |
                        official_weights;  relation (weights_copy): same_file | declares_base_model | named
  source_groups[]       every group that lists this record (after identity resolution)
  urls                  {record?, search?, paper?, code?, weights?, data?}  never a URL with an HF uploader name
                        for an HF upload row; family search URLs carry the series stem only; paper is a paper or
                        preprint, never a data-repository DOI (DATA_DOI)
  hf?                   {repo, revision_sha, gated: false|"manual"|"auto", licence_tags[], size_bytes, files}
  classified?           external file only, HF upload rows: {modality[], paradigm, content_kind, card_readable,
                        by: register_classifier} (the fields the classifier audit found displayable; card_readable
                        false = values from names and file lists). Not served until the owner approves wave-1
                        display of classifier fields.
  family?               {uploader, series, n, search_url}
  moabb?                {loaders[], doi, data_url, repository, licence_as_listed, fields_as_listed[{loader,
                         paradigm, people, channels, sampling_rate_hz}], release: "1.7.2"}
  site?                 dataset rows {page, status, census_id};  model rows {page, status, method_slug}
  terms_as_stated       {value: str|null, by: token}   (by: a vocab.by token, e.g. hf_licence_tag | moabb_catalog |
                        deposit_record | a4_capture | zenodo_record | site_release | model_card_metadata | none)
  original_terms?       agreement corpora: {access_kind, capture_id, redistribution_stated}   (A4 capture only)
  terms_by_part?        model rows: {code|weights|data: {state: stated|not_found|per_source|not_applicable|
                        application_required, value: str|null, by: token}}
  venue?                model rows, only with accepted-paper evidence: {value, evidence: official_proceedings|
                        camera_ready_pdf, url?, checked}
  exposure?             model rows: "unknown" | ...
  signal[]              model rows: tokens (human_scalp_eeg, human_ieeg, ...); model_kind token
  access                open | gated | signed_agreement | request_based | registration | catalog_only | unknown
  level                 int 1..5, the furthest step whose own evidence is on file (rule caps noted in level_cap)
  level_cap?            {step, rule}   e.g. suspected re-uploads and gated uploads stay at step 1
  step_evidence         {"1".."5": {state: pass|gap|partial|not_reached, items?: [{item, state, source}]}}
                        source: one string or null (an input label with a selector, a served site file, an A4
                        capture id, verification_results or record:<sha256 prefix>). An item with several sources
                        appears once per source (a comparison row: one original_terms item per A4 capture).
  gaps[]                [{step, item, label_en, label_zh}]  items missing at or below the level
  next_step_gaps[]      [{step, item, label_en, label_zh}]  what stops the row moving up
  status                listed | planned | published | score_held | status_only   (holds are findings; a site
                        row's hold (register_findings.SITE_HOLD_REASONS: eldBETA, ZuCo 2.0) is declared and attached
                        once site/src/data/open-register.ts words its reason code, and carries the hold's sources)
  findings[]            [{code, params, sources?}]  codes and parameters only (register_findings.py); a site row's
                        finding carries the census sources it rests on (public source strings). A row with personal or
                        identifying information is a plain row: licence_tag_absent and gated only. A comparison
                        (matches_metadata_of, terms_differ) needs a confirmed verifier result that itself identifies
                        the source family (VERIFIED_SOURCES), an A4 capture, and no withheld reason.
  links                 {page?, case?, cases?[], parent_row?, exposure?}
  correction            {mailto}  every row: mailto:contact@bci.report?subject=Register%20row%20<id>
  checked               evidence date (YYYY-MM-DD) of the row's furthest step
  merge_into?           external file only: the site slug (dataset) or site method slug (model) this row folds into
  placeholder?          true on provisional site rows (B8b replaces them)

What this build refuses (tests in test_open_register.py):
- any repo id that matches the participant-id pattern, in any field; any HF uploader name in a URL or an id;
- HF card free text, download counts, likes and HF modification or creation dates;
- any finding about personal or identifying information, and any finding beyond listing metadata on a row with
  such information; any comparison finding without a confirmed verification verdict, an A4 capture and the
  verifier's own identification of the family, or on a row whose verifier result says "do not state" or notes a
  same-party source (D3); derived_from without the card naming the source;
- ICLR 2027 / OpenReview / submission references in any field (D4); demographics from the MOABB catalog;
- a DOI, accession or repo id in two rendered rows, or one value twice in a row's aliases; private paths.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.parse
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register_findings import (FindingError, SITE_HOLD_REASONS, comparison_allowed, finding,  # noqa: E402
                               schema as finding_schema, validate)
from register_ids import IdMap  # noqa: E402

PROJECT = Path(__file__).resolve().parents[2]
D = '20261020'
RELEASE_ID = f'open-register-update-{D}'
SCHEMA = 'bci-report-open-register-v1'
OPEN = PROJECT / 'research/open_register_20261019'
REVIEW = PROJECT / f'research/publication_review_{D}'
REGISTER = REVIEW / 'register'
MOABB_EV = PROJECT / 'research/moabb_expansion_20261019/evidence'
ICLR = PROJECT / 'research/iclr_bci_expansion_20261016'
SITE_DATA = PROJECT / 'site/src/data'

EXTERNAL_OUT = REGISTER / f'open-register-external-{D}.json'
IDS_PATH = REGISTER / 'register-ids.json'
SITE_OUTS = (SITE_DATA / f'open-register-{D}.json', PROJECT / f'site/public/data/open-register-{D}.json')
CSV_OUT = PROJECT / f'site/public/data/open-register-{D}.csv'
AUDIT = REVIEW / 'reviews/register-classifier-audit.json'
# B8b: the site rows as re-read at the freeze, the script that writes them, and the release manifest.
SITE_ROWS = REGISTER / f'site-register-rows-{D}.json'
SITE_ROWS_SCRIPT = PROJECT / 'site/scripts/export-site-register-rows.mjs'
# The page module that words every finding code and hold reason the served file declares (package P-RG).
SITE_REGISTER_MODULE = PROJECT / 'site/src/data/open-register.ts'
MANIFEST_OUT = REGISTER / 'open-register-release-manifest.json'
EXPORT_AUDIT_OUT = REGISTER / 'open-register-export-audit.json'

INPUTS = {
    'listing': OPEN / 'raw/hf-dataset-listing.json',
    'eegdash': OPEN / 'eegdash-openneuro-map.json',
    'prefilter': OPEN / 'prefilter-dropped.json',
    'known_sources': OPEN / 'known-sources.json',
    'model_listing': OPEN / 'raw/hf-model-listing.json',
    'moabb_catalog': MOABB_EV / 'moabb-catalog.json',
    'moabb_shortlist': MOABB_EV / 'moabb-shortlist-verified.json',
    'moabb_coverage': MOABB_EV / 'existing-dataset-coverage.json',
    'a4_index': REVIEW / 'evidence/access-terms/index.json',
    'a5': REVIEW / 'notes/site-step-evidence.json',
    'a3': REVIEW / 'evidence/consent-statements.json',
    'owner': REVIEW / 'owner-decisions.json',
    'hf_model_metadata': REGISTER / f'hf-model-metadata-{D}.json',
    'model_evidence': ICLR / 'Additional ICLR BCI Opportunities.json',
    'fm_update': SITE_DATA / 'foundation-models-update.json',
    'neurolm_update': SITE_DATA / 'neurolm-eegmat-update.json',
    'iesseeg_update': SITE_DATA / 'clinical-iesseeg-update.json',
    'profiles': SITE_DATA / 'entity-profiles.json',
    'mvp': SITE_DATA / 'mvp.json',
}

# Served files name research inputs by label and hash only (their paths and folder names never reach a page).
INPUT_LABELS = {
    'listing': 'hf_listing_snapshot', 'eegdash': 'eegdash_map', 'prefilter': 'prefilter_dropped',
    'known_sources': 'known_sources', 'model_listing': 'hf_model_listing', 'moabb_catalog': 'moabb_catalog_snapshot',
    'moabb_shortlist': 'moabb_shortlist_check', 'moabb_coverage': 'moabb_site_coverage', 'a4_index': 'access_terms_index',
    'a5': 'site_step_census', 'a3': 'consent_record', 'owner': 'owner_decisions', 'hf_model_metadata': 'hf_model_metadata',
    'model_evidence': 'model_evidence_review', 'audit': 'classifier_audit',
    'fm_update': 'site/src/data/foundation-models-update.json', 'neurolm_update': 'site/src/data/neurolm-eegmat-update.json',
    'iesseeg_update': 'site/src/data/clinical-iesseeg-update.json', 'profiles': 'site/src/data/entity-profiles.json',
    'mvp': 'site/src/data/mvp.json',
}
DIR_LABELS = {'research/open_register_20261019/classified': 'classifier_rows',
              'research/open_register_20261019/verified': 'verification_results',
              'research/open_register_20261019/raw/details': 'hf_detail_records',
              'research/publication_review_20261020/evidence/access-terms': 'access_terms_families'}

CONTACT = 'contact@bci.report'
HF_SEARCH = 'https://huggingface.co/datasets?search='
MOABB_RELEASE = '1.7.2'
CHECKED_HF = '2026-10-19'

# --------------------------------------------------------------------------------------------- vocab
DATASET_STEPS = {
    '1': {'en': 'Listed', 'zh': '已列出', 'needs_en': 'Host record read: host, licence as stated and by whom, size, '
          'whether access is gated', 'needs_zh': '已读取托管记录：托管方、所声明的许可及声明者、数据规模、是否需要授权访问', 'items': ['host_record', 'licence_as_stated']},
    '2': {'en': 'Read', 'zh': '已读取', 'needs_en': 'Files opened; a specification sheet from the files, compared '
          'with the card', 'needs_zh': '已打开文件；根据文件整理规格表，并与说明卡对照', 'items': ['files_opened']},
    '3': {'en': 'Traced', 'zh': '已追溯', 'needs_en': 'Derivation, original terms against declared terms, consent or '
          'ethics statement, pinned revision',
          'needs_zh': '来源链、原始条款与声明条款的对照、知情同意或伦理声明、固定版本',
          'items': ['rights_reviewed', 'derivation', 'original_terms', 'consent_ethics', 'pinned_version']},
    '4': {'en': 'Run', 'zh': '已运行', 'needs_en': 'Fixed-protocol baseline here, chance from trial counts, share of '
          'participants above chance, result or hold on a page',
          'needs_zh': '本站按固定协议运行的基线、按试次数计算的随机水平、高于随机水平的被试比例、页面上的结果或暂缓说明',
          'items': ['fixed_protocol_baseline', 'chance_stated', 'share_above_chance', 'result_or_hold_on_page']},
    '5': {'en': 'In the matrix', 'zh': '已进入核心矩阵', 'needs_en': 'Comparable on a protocol page',
          'needs_zh': '可在协议页上比较', 'items': ['comparable_on_protocol_page']},
}
DATASET_ANCHORS = {'1': 'host_record', '2': 'files_opened', '3': 'original_terms', '4': 'fixed_protocol_baseline',
                   '5': 'comparable_on_protocol_page'}
MODEL_STEPS = {
    '1': {'en': 'Identified', 'zh': '已识别', 'needs_en': 'Official record matched: paper, repository or model page',
          'needs_zh': '已匹配官方记录：论文、代码仓库或模型页', 'items': ['official_record']},
    '2': {'en': 'Terms recorded', 'zh': '已记录条款', 'needs_en': 'Licence for each part (code, weights, data); '
          'file listing read', 'needs_zh': '逐项记录许可（代码、权重、数据）；已读取文件列表',
          'items': ['code_terms', 'weights_terms', 'data_terms', 'file_listing']},
    '3': {'en': 'Files checked', 'zh': '已检查文件', 'needs_en': 'Downloaded, hash-checked, restored or smoke-tested',
          'needs_zh': '已下载并校验哈希、恢复加载或冒烟测试', 'items': ['files_checked']},
    '4': {'en': 'Scored here', 'zh': '已在本站评分', 'needs_en': 'A result computed here and published on a page',
          'needs_zh': '本站计算的结果已发布在页面上', 'items': ['scored_here']},
    '5': {'en': 'In the matrix', 'zh': '已进入核心矩阵', 'needs_en': 'Comparable on the core protocol pages',
          'needs_zh': '可在核心协议页上比较', 'items': ['in_matrix']},
}
MODEL_ANCHORS = {'1': 'official_record', '2': 'weights_terms', '3': 'files_checked', '4': 'scored_here',
                 '5': 'in_matrix'}
ITEM_LABELS = {
    # dataset ladder (labels as the A5 census defines them)
    'host_record': ('host record', '托管记录'),
    'licence_as_stated': ('licence as stated', '声明的许可'),
    'files_opened': ('files opened', '文件读取'),
    'rights_reviewed': ('rights review', '权利审查'),
    'derivation': ('derivation', '来源链'),
    'original_terms': ('original terms', '原始条款'),
    'consent_ethics': ('consent or ethics statement', '知情同意或伦理声明'),
    'pinned_version': ('pinned version', '固定版本'),
    'fixed_protocol_baseline': ('fixed-protocol baseline', '固定协议基线'),
    'chance_stated': ('chance level', '随机水平'),
    'share_above_chance': ('share above chance', '高于随机水平的被试比例'),
    'result_or_hold_on_page': ('result or hold on a page', '页面上的结果或暂缓说明'),
    'comparable_on_protocol_page': ('protocol page', '协议页'),
    # model ladder
    'official_record': ('official record', '官方记录'),
    'code_terms': ('code licence', '代码许可'),
    'weights_terms': ('weights licence', '权重许可'),
    'data_terms': ('data terms', '数据条款'),
    'file_listing': ('file listing', '文件列表'),
    'files_checked': ('files checked', '文件核验'),
    'scored_here': ('scored here', '本站评分'),
    'in_matrix': ('core matrix', '核心矩阵'),
}
RULES = [
    {'id': 'gated_stays_at_step_1',
     'en': 'Gated data, or data that needs a signed or requested agreement, stays at step 1 unless we accept its terms.',
     'zh': '需要授权才能获取的数据，或需要签署、申请协议的数据，除非我们接受其条款，否则停留在第 1 步。'},
    {'id': 'reuploads_stay_at_step_1',
     'en': 'Suspected re-uploads stay at step 1 whatever their gating. They are compared by metadata only, and none '
           'of their files is downloaded.',
     'zh': '疑似转传的数据无论是否需要授权都停留在第 1 步。它们只按元数据比对，不下载任何文件。'},
    {'id': 'reupload_findings_confirmed',
     'en': 'A finding about a re-upload is stated only when an independent check confirms it and a captured page of '
           'the original terms backs it.',
     'zh': '关于转传的发现，只有经独立核查确认、并有原始条款页面的存档为据时才会写出。'},
    {'id': 'rows_state_facts', 'en': 'Rows state facts.', 'zh': '每一行只陈述事实。'},
    {'id': 'correction_route', 'en': 'Every row has a correction route.', 'zh': '每一行都有更正途径。'},
]
VOCAB = {
    'access': ['open', 'gated', 'signed_agreement', 'request_based', 'registration', 'catalog_only', 'unknown'],
    'status': ['listed', 'planned', 'published', 'score_held', 'status_only'],
    'by': ['hf_licence_tag', 'moabb_catalog', 'deposit_record', 'a4_capture', 'zenodo_record', 'host_record',
           'repository_licence_file', 'model_card_metadata', 'dataset_card', 'paper', 'project_page', 'site_release',
           'none'],
    'terms_state': ['stated', 'not_found', 'per_source', 'not_applicable', 'application_required'],
    'signal': ['human_scalp_eeg', 'human_ieeg', 'human_fmri', 'mouse_calcium_imaging', 'mouse_spiking',
               'ecg', 'ppg', 'emg', 'human_meg'],
    'classified_by': ['register_classifier'],
    'model_kind': ['foundation_model', 'spatial_aggregation_model', 'generative_model', 'decoding_model',
                   'adaptation_method', 'classical_method', 'trained_from_scratch'],
}
ACCESS_FROM_A4 = {'signed agreement': 'signed_agreement', 'request-based': 'request_based',
                  'registration': 'registration', 'open': 'open'}

# ------------------------------------------------------------------------- privacy and wording guards
# A participant-style id anywhere in a string. Every character that is not a letter or digit is a boundary, so
# '_', '-', '.', '/' and space all separate ('eeg_subject0', 'x-sub01.y' and 'sub 3' match; 'subset1' does not).
PARTICIPANT_ID = re.compile(r'(?<![a-z0-9])(?:sub|subj|subject|participant|pt)[-_ ]?\d+(?![a-z0-9])'
                            r'|(?<![a-z0-9])[a-z]\d{2}[te](?![a-z0-9])', re.I)
# Inside an HF repo name, tokens that may name a person or a user: participant-style ids and u<n> suffixes
# ('-u1', '_u2'). A repo whose name carries one always collapses into its uploader's series and never appears
# by repo id in any field.
PARTICIPANT_TOKEN = re.compile(r'(?:^|(?<=[-_ .]))(?:(?:sub|subj|subject|participant|pt)[-_ ]?\d+|u\d+)(?=$|[-_ .])',
                               re.I)
# Series index tokens: a separate number, v<n>, u<n> or a participant-style token ...
INDEX_TOKEN = re.compile(r'(?:^|(?<=[-_ .]))(?:\d+|v\d+|u\d+|(?:sub|subj|subject|participant|pt)[-_ ]?\d+)(?=$|[-_ .])',
                         re.I)
# ... or one or two digits run onto the end of a name ('EMGSoundTrain3', 'task2'); years and accessions, with
# three or more digits ('Singh2020', 'ds004584'), are not indices.
TRAILING_INDEX = re.compile(r'(?<=[a-z])\d{1,2}$', re.I)
# Test runs ('test-raw-refactored', 'testing-emg-again') of one uploader form one series.
TEST_STEM = re.compile(r'^(test|testing)(?=$|[-_ .])', re.I)
# Braindecode's hub formats of one dataset ('x-raw', 'x-windows', 'x-eegwindows'): a series when an uploader has two.
FORMAT_TOKEN = re.compile(r'(?:^|(?<=[-_ .]))(?:raw|windows|eegwindows)(?=$|[-_ .])', re.I)


REPO_ID = re.compile(r'[\w.-]+/[\w.-]+')


def participant_like_repo(repo: str) -> bool:
    """True when an HF repo id carries a participant-style id or a u<n> token."""
    name = repo.split('/', 1)[-1]
    return bool(PARTICIPANT_ID.search(repo) or PARTICIPANT_TOKEN.search(name))
PRIVATE = re.compile(r'/(?:Users|home|Volumes|mnt|private|tmp)/|\btrx50\b|\bGal4\b|BCI_Arena|\btwu\b', re.I)
VENUE_REFS = re.compile(r'ICLR\s*2027|openreview|\bsubmission\b|double[- ]blind|under review|anonymous review',
                        re.I)

# Uploads held from the register until the owner's review: rows tied to ICLR 2027 submissions (D4) and repo ids
# that name a conference or a review submission (the release copy rule). Never printed with a reason.
REVIEW_HOLD = {
    'anonymous-588/MCD-EEG',                    # a screened lead under D4
    'synapse-ear-eeg/synapse',                  # card names a submission in the D4 ledger
    'roychowdhuryresearch/IESSEEG',             # IESSEEG appears only as the site row, citing its card (D13, D4)
    'AnonymousAuthorSubmission/EMG-FoundBench',  # repo id names a review submission
    'gifoe/CRCICLR',                            # repo id names a conference
}

# ------------------------------------------------------------------- verified comparisons (D3), row by row
# For each confirmed verifier result, the source families that the verifier ITSELF identifies as a source of the
# upload's files, with the metadata that identification rests on (matches_metadata_of.fields) and a phrase that
# must appear verbatim in the verifier's ``original_source`` (checked at build time, so the gate reads the
# verifier's own words). A4's ``families_matched_by_name`` is a name match over the verifier's whole text; a
# family it found that is not listed here yields no finding (labels a verifier lists as context, names it says
# were "not traced", and leads). ``declared`` overrides what the upload declares for a source when its card gives
# a per-source licence that differs from the repo tag (amongglue/amber). Reviewed one by one against the verifier
# results of research/open_register_20261019/verified/ (B8a); R2 or F3 re-reviews before the freeze.
# Rows with a withheld reason (personal_info, do_not_state, same_party; see withheld_reason()) are never listed.
_CARD = ('card_names_source',)
VERIFIED_SOURCES: dict[str, dict] = {
    '2Levi/EEG_fNIRS_4_BCI': {'families': {   # "identified by file name and byte count"; EEG_fNIRS / UL-MJMI not
        'buccino-2016': (('archive_names', 'byte_counts'), 'Buccino, Keles & Omurtag 2016 hybrid EEG-fNIRS BCI'),
        'finemi': (('archive_names', 'byte_counts'), 'FineMI, an EEG+fNIRS dataset of 18 subjects'),
        'physionet-mimic-iv-ecg': (('archive_names', 'byte_counts'),
                                   'MIMIC-IV-ECG: Diagnostic Electrocardiogram Matched Subset v1.0'),
        'tdbrain': (('archive_names',), 'TDBRAIN, Brainclinics Foundation'),
        'hefmi-ich': (('archive_names',), 'HEFMI-ICH, Figshare'),
        'tu-berlin-hbci': (('archive_names',), 'TU Berlin open-access hybrid EEG-NIRS BCI set')}},
    'HeliumHcc/EEG_raw_datasets': {'families': {
        'tuh-eeg': (('archive_names',), 'Temple University Hospital (TUH) EEG Corpus'),
        'bci-competition-iv': (('archive_names',), 'Secondary archives are named after BCI Competition IV 2a'),
        'faced': (('archive_names',), 'BCI Competition IV 2a (https://www.bbci.de/competition/iv/), FACED')}},
    'JLB-JLB/seizure_eeg_dev': {'families': {
        'tuh-eeg': (('label_names', 'split_names', 'example_counts'), 'TUH EEG Seizure Corpus (TUSZ)')}},
    'JLB-JLB/seizure_eeg_greyscale_224x224_6secWindow': {'families': {
        'tuh-eeg': (('code_names_source', 'label_names', 'split_names'),
                    "The link comes from the uploader's public GitHub code")}},
    'JLB-JLB/seizure_eeg_iirFilter_greyscale_224x224_6secWindow_adjusted': {'families': {
        'tuh-eeg': (('label_names', 'split_names', 'example_counts'), 'TUH EEG Seizure Corpus (TUSZ)')}},
    'JLB-JLB/seizure_eeg_train': {'families': {
        'tuh-eeg': (('label_names', 'split_names', 'example_counts'), 'TUH EEG Seizure Corpus (TUSZ)')}},
    # The verifier's same-author note concerns the duplicate flag between two of this uploader's own repos; the
    # sources, THINGS-data and the THINGS images (Hebart et al.), are third-party (SAME_PARTY_NOTE_SCOPE).
    'LidongYang/BrainFLORA': {'families': {
        'things-data': (('participant_count', 'example_counts', 'code_names_source'),
                        'both part of THINGS-data (Hebart et al. 2023'),
        'things-images': (('example_counts', 'code_names_source'),
                          'stimulus images from the THINGS object image database')}},
    'McGregorW/EEGDatasets': {'families': {   # "By archive name"; BCI-IV-2A "not traced to a host"
        'seed': (('archive_names',), 'SEED and SEED-IV, BCMI lab'),
        'tuh-eeg': (('archive_names',), 'TUSZ and TUSL, TUH EEG Corpus'),
        'shhs': (('archive_names',), 'SHHS, Sleep Heart Health Study'),
        'physionet-chbmit': (('archive_names',), 'Open PhysioNet sets by name: CHB-MIT'),
        'physionet-sleep-edfx': (('archive_names',), 'Sleep-EDF (sleep-edfx)'),
        'physionet-eegmat': (('archive_names',), 'EEGMAT'),
        'physionet-eegmmidb': (('archive_names',), 'PhysioNet-MI (eegmmidb)'),
        'physionet-siena-scalp-eeg': (('archive_names',), 'Siena (siena-scalp-eeg)'),
        'physionet-hmc-sleep-staging': (('archive_names',), 'HMC (hmc-sleep-staging)')}},
    'McGregorW/EEGDatasetsH5': {'families': {   # "candidates come from folder names only"
        'seed': (('folder_names',), 'SJTU BCMI SEED family (SEED, SEED-IV, SEED-FRA'),
        'tuh-eeg': (('folder_names',), 'Temple University Hospital EEG Corpus via NEDC'),
        'shhs': (('folder_names',), 'Sleep Heart Health Study via NSRR'),
        'caueeg': (('folder_names',), 'CAUEEG (https://github.com/ipis-mjkim/caueeg-dataset)'),
        'physionet-chbmit': (('folder_names',), 'CHB-MIT (PhysioNet, ODC-By 1.0)'),
        'physionet-siena-scalp-eeg': (('folder_names',), 'Siena Scalp EEG (PhysioNet, CC BY 4.0)')}},
    'USuCgex0122e/demo_dataset_seed20260726': {'families': {   # Things_EEG2 "not traced"
        'tuh-eeg': (('folder_names', 'label_names'), 'TUAB/TUEV/TUSL/TUSZ = Temple University Hospital EEG corpora'),
        'deap': (('folder_names', 'participant_count', 'channel_count'),
                 'DEAP = QMUL DEAP (source format bdf, 32 subjects, 32 ch)'),
        'seed': (('folder_names', 'participant_count'), 'SEED_V/SEED_VIG/SEED_VII = SJTU BCMI SEED family'),
        'modma': (('folder_names', 'participant_count', 'channel_count'),
                  'MODMA = Lanzhou University MODMA 128-channel resting set'),
        'physionet-chbmit': (('folder_names', 'participant_count'), 'CHB_MIT = PhysioNet chbmit (24 subjects'),
        'physionet-siena-scalp-eeg': (('folder_names', 'participant_count'),
                                      'Siena_EEG = PhysioNet siena-scalp-eeg (14 subjects)'),
        'physionet-eegmmidb': (('folder_names',), 'Physionet_MI, SleepEDF, EEGMAT = PhysioNet sets by name'),
        'physionet-sleep-edfx': (('folder_names',), 'Physionet_MI, SleepEDF, EEGMAT = PhysioNet sets by name'),
        'physionet-eegmat': (('folder_names',), 'Physionet_MI, SleepEDF, EEGMAT = PhysioNet sets by name')}},
    'Ugo96/MMI-EEGSR': {'families': {
        'physionet-eegmmidb': (('dataset_name', 'code_names_source'),
                               'PhysioNet EEG Motor Movement/Imagery Dataset v1.0.0 (EEGMMIDB')}},
    # The card labels every source ODC-BY 1.0 (repo tag 'other'): terms differ only where a source's own terms do.
    'amongglue/amber': {'declared': ('odc-by-1.0', 'dataset_card'), 'families': {
        'bnci-horizon-2020': (_CARD, 'BNCI Horizon 2020 via MOABB'),
        'hbn': (_CARD, 'Healthy Brain Network EEG'),
        'physionet-sleep-edfx': (_CARD, 'PhysioNet (sleep-edfx'),
        'physionet-hmc-sleep-staging': (_CARD, 'hmc-sleep-staging 1.1'),
        'physionet-ucddb': (_CARD, 'ucddb'),
        'physionet-siena-scalp-eeg': (_CARD, 'siena-scalp-eeg'),
        'physionet-chbmit': (_CARD, 'chbmit'),
        'physionet-eegmmidb': (_CARD, 'eegmmidb'),
        'physionet-eegmat': (_CARD, 'eegmat'),
        'physionet-ltrsvp': (_CARD, 'ltrsvp'),
        'physionet-erpbci': (_CARD, 'erpbci'),
        'physionet-shhpsgdb': (_CARD, 'shhpsgdb')}},
    'divyanshmaurya1/BCI_Data_new': {'families': {
        'gigadb-cho2017': (('card_names_source', 'file_names'), 'Cho H, Ahn M, Ahn S, Kwon M, Jun SC.')}},
    'graycatHCO3/BCICIV_2A_tensor': {'families': {
        'bci-competition-iv': (('dataset_name', 'file_names'), 'BCI Competition IV, data set 2a'),
        'bnci-horizon-2020': (('dataset_name', 'file_names'), 'BNCI Horizon 2020 data set 001-2014')}},
    'graycatHCO3/bi_bci2000_MELR_tensor': {'families': {
        'physionet-eegmmidb': (('file_names',), 'PhysioNet EEG Motor Movement/Imagery Dataset (EEGMMIDB) v1.0.0')}},
    'graycatHCO3/eegmmidb_0to8_cross': {'families': {
        'physionet-eegmmidb': (('dataset_name', 'file_names'),
                               'PhysioNet: EEG Motor Movement/Imagery Dataset, version 1.0.0')}},
    'graycatHCO3/eegmmidb_tensor': {'families': {
        'physionet-eegmmidb': (('dataset_name', 'file_names'), 'PhysioNet EEG Motor Movement/Imagery Dataset v1.0.0')}},
    'gymprathap/Brain-Computer-Interaction-Eye-State-Classification': {'families': {
        'uci-eeg-eye-state': (('column_names', 'example_counts'), 'UCI Machine Learning Repository, EEG Eye State')}},
    'liverman/EEG_DECODE': {'families': {   # image zips: OSF sha256 equal; EEG: derived arrays
        'things-eeg2': (('file_hashes',), 'THINGS-EEG2: Gifford, Dwivedi, Roig, Cichy (2022)'),
        'things-images': (('file_hashes',), 'The THINGS object images are from Hebart et al. 2019')}},
    'monster-monash/DREAMERA': {'families': {
        'dreamer': (('card_names_source',), 'DREAMER: A Database for Emotion Recognition')}},
    'monster-monash/DREAMERV': {'families': {
        'dreamer': (('card_names_source',), 'DREAMER: A Database for Emotion Recognition')}},
    'musicji83/amigos-eeg-dataset': {'families': {
        'amigos': (('file_names', 'file_count', 'byte_counts'),
                   'AMIGOS: A Dataset for Affect, Personality and Mood Research')}},
    'neuroinfinite/fnirs-finekyber': {'families': {   # 5 of the card's 28 sources checked
        'kamat-2023-astaund': (_CARD, 'Kamat et al. 2023 ASTaUND'),
        'guevara-2024': (_CARD, 'Guevara et al. 2024 (Zenodo record 7966830'),
        'isaev-2024': (_CARD, 'Isaev et al. 2024 (NITRC'),
        'yucel-2014': (_CARD, 'Yucel et al. 2014 (NITRC'),
        'luke-2021b': (_CARD, 'Luke et al. 2021b (Zenodo record 5529797')}},
    # Stimulus image file names follow NSD's shared-1000 naming; the recordings are not NSD data.
    'rishab-iyer1/mindeye_ieeg': {'families': {
        'nsd': (('file_names',), 'Natural Scenes Dataset (NSD), CVN Lab / CMRR')}},
    'smam/chb-mit-seizure-windows-2to1': {'families': {
        'physionet-chbmit': (_CARD, 'CHB-MIT Scalp EEG Database v1.0.0, PhysioNet')}},
    'smam/tuh-eeg': {'families': {
        'tuh-eeg': (('folder_names',), 'Temple University Hospital EEG Corpus family')}},
    'woldier/eeg_denoise_dataset': {'families': {
        'eegdenoisenet': (_CARD, 'EEGdenoiseNet, NCClab'),
        'klados-2016': (_CARD, 'A semi-simulated EEG/EOG dataset for the comparison of EOG artifact rejection')}},
    'xw1216/tuh-eeg-cloud-transfer': {'families': {
        'tuh-eeg': (_CARD, 'Named in the card')}},
}
# Verifier notes that withhold a row from every comparison finding. DO_NOT_STATE: the verifier limits what may be
# stated. SAME_PARTY: the verifier says the source is the uploader's own release or terms. Read in the verifier's
# own fields (claim_checked, original_source, flag_by_flag, identifying_info, notes), never in quoted source terms.
DO_NOT_STATE = re.compile(r'\bdo not state\b', re.I)
SAME_PARTY = re.compile(r"same party|same-party|not a third[- ]party|rather than a third-party (?:re-?upload|copy)"
                        r"|own companion (?:release|upload)|team release|re-exporting its own data", re.I)
# A same-party note scoped to another flag (the row's comparison families are third-party), by row.
SAME_PARTY_NOTE_SCOPE = {'LidongYang/BrainFLORA': 'duplicate_of_another_hf_repo'}
PERSONAL_FLAG = 'personal-or-identifying-info-visible'
VERIFIER_OWN_FIELDS = ('claim_checked', 'original_source', 'flag_by_flag', 'identifying_info', 'notes')


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(name: str):
    return json.loads(INPUTS[name].read_text())


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(PROJECT))


def mailto(rid: str) -> dict:
    return {'mailto': f'mailto:{CONTACT}?subject=' + urllib.parse.quote(f'Register row {rid}')}


def labels(item: str) -> tuple[str, str]:
    return ITEM_LABELS[item]


def gap(step: str | int, item: str, note: str | None = None) -> dict:
    en, zh = labels(item)
    g = {'step': int(step), 'item': item, 'label_en': en, 'label_zh': zh}
    return g


# ---------------------------------------------------------------------------------- licence names
LICENCE_CANON = [
    (re.compile(r'nc[- ]?sa|noncommercial[- ]?sharealike|by-nc-sa', re.I), 'cc-by-nc-sa-4.0'),
    (re.compile(r'nc[- ]?nd|by-nc-nd', re.I), 'cc-by-nc-nd-4.0'),
    (re.compile(r'by-nc|noncommercial|\bnc\b', re.I), 'cc-by-nc-4.0'),
    (re.compile(r'by-nd|noderiv', re.I), 'cc-by-nd-4.0'),
    (re.compile(r'by-sa[- ]?3', re.I), 'cc-by-sa-3.0'),
    (re.compile(r'by-sa|sharealike', re.I), 'cc-by-sa-4.0'),
    (re.compile(r'cc0|zero v1|public domain', re.I), 'cc0-1.0'),
    (re.compile(r'odbl|open database licen', re.I), 'odbl-1.0'),
    (re.compile(r'odc[- ]?by|open data commons attribution', re.I), 'odc-by-1.0'),
    (re.compile(r'cc[- ]?by[- ]?1\.0|attribution 1\.0', re.I), 'cc-by-1.0'),
    (re.compile(r'cc[- ]?by|creative commons attribution|attribution 4\.0|/licenses/by/4\.0', re.I), 'cc-by-4.0'),
    (re.compile(r'\bmit\b', re.I), 'mit'),
    (re.compile(r'apache', re.I), 'apache-2.0'),
    (re.compile(r'\bbsd\b', re.I), 'bsd'),
    (re.compile(r'\bgpl\b|gnu', re.I), 'gpl'),
]


def canon_licence(s: str | None) -> str | None:
    if not s:
        return None
    s = str(s)
    if re.search(r'per entry|other-open|^other$|unknown|see the file', s, re.I):
        return None
    for rx, out in LICENCE_CANON:
        if rx.search(s):
            return out
    return None


# ---------------------------------------------------------------------------------- identity tokens
OWN_DOIS = {'doi:10.5281/zenodo.23123296'}
# DOI prefixes of data repositories (Zenodo, PhysioNet, OpenNeuro, Harvard Dataverse, figshare, GigaDB, Mendeley
# Data, KiltHub, DataverseNL, ScienceDB, Universidad de Valladolid, NEMAR): a record, not a paper.
DATA_DOI = re.compile(r'\b10\.(?:5281|13026|18112|7910|6084|25452|5524|17632|1184|34894|57760|71569|82901)/')


def ident_tokens(s) -> set[str]:
    """Normalised identifiers in a string: DOIs, deposit and archive accessions, repo ids."""
    out: set[str] = set()
    if not s:
        return out
    s = str(s)
    for m in re.finditer(r'(?:doi\.org/|doi:\s*|\b)(10\.\d{4,9}/[^\s"\'<>,;)]+)', s, re.I):
        d = m.group(1).rstrip('.').lower()
        b = re.sub(r'\.v\d+$', '', d)
        out |= {'doi:' + d, 'doi:' + b}
        for rx, kind in ((r'10\.5281/zenodo\.(\d+)', 'zenodo'), (r'10\.(?:6084|25452)/m9\.figshare\.(\d+)', 'figshare'),
                         (r'10\.25452/figshare\.plus\.(\d+)', 'figshare'), (r'10\.18112/openneuro\.(ds\d{6})', 'openneuro'),
                         (r'10\.82901/nemar\.(nm\d{6})', 'nemar'), (r'10\.5524/(\d+)', 'gigadb'),
                         (r'10\.1184/r1/(\d+)', 'kilthub')):
            mm = re.match(rx, b)
            if mm:
                out.add(f'{kind}:{mm.group(1)}')
    pats = ((r'zenodo\.org/records?/(\d+)', 'zenodo'), (r'figshare\.com/articles/(?:dataset/)?(?:[^/\s]*/)?(\d{6,})', 'figshare'),
            (r'\bfigshare\+? (\d{6,})', 'figshare'), (r'\bZenodo (\d{5,})', 'zenodo'), (r'\bGigaDB (\d+)', 'gigadb'),
            (r'\bKiltHub (\d+)', 'kilthub'), (r'kilthub\.cmu\.edu/articles/dataset/(?:[^/\s]*/)?(\d+)', 'kilthub'),
            (r'(?<![a-z0-9])(ds\d{6})(?![0-9])', 'openneuro'), (r'(?<![a-z0-9])(nm\d{6})(?![0-9])', 'nemar'),
            (r'physionet\.org/content/([a-z0-9-]+)', 'physionet'), (r'osf\.io/([a-z0-9]{5})\b', 'osf'),
            (r'\bOSF ([a-z0-9]{5})\b', 'osf'), (r'bnci-horizon-2020\.eu/database/data-sets/(\d{3}-\d{4})', 'bnci'),
            (r'huggingface\.co/datasets/([\w.-]+/[\w.-]+)', 'hf'))
    for rx, kind in pats:
        for m in re.finditer(rx, s, re.I):
            out.add(f'{kind}:{m.group(1).lower()}')
    return out - OWN_DOIS


# =============================================================================================== build
class Build:
    def __init__(self, fresh_ids: bool, freeze: bool = False):
        self.freeze = freeze
        # B8b: the site rows re-read at the freeze (export-site-register-rows.mjs); pinned with the other inputs.
        self.frozen = json.loads(SITE_ROWS.read_text()) if freeze else None
        # The site holds (SITE_HOLD_REASONS) the page has words for: only those are declared and attached.
        self.site_hold_words = site_hold_words() if freeze else set()
        self.site_holds_withheld: list[str] = []
        self.raw = {k: p.read_bytes() for k, p in INPUTS.items()}
        self.inputs = [{'path': rel(p), 'sha256': sha(self.raw[k])} for k, p in INPUTS.items()]
        self.ids = IdMap.fresh(IDS_PATH) if fresh_ids else IdMap.load(IDS_PATH)
        self.entries: list[dict] = []
        self.families: list[dict] = []
        self.audit = None
        self.audit_applied: list[str] = []
        if AUDIT.exists():
            self.audit = json.loads(AUDIT.read_text())
            self.inputs.append({'path': rel(AUDIT), 'sha256': sha(AUDIT.read_bytes())})
        # Directories are pinned as one digest each (sha256 of the sorted name/sha256 list): their file names
        # carry repo ids, some of which look like participant ids, and never appear in an output.
        self.dir_files: dict[str, list] = defaultdict(list)
        self.classified = []
        for f in sorted((OPEN / 'classified').glob('batch-*.json')):
            self.classified += json.loads(f.read_text())
            self.dir_files[rel(OPEN / 'classified')].append((f.name, sha(f.read_bytes())))
        self.verified = {}
        for f in sorted((OPEN / 'verified').glob('*.json')):
            v = json.loads(f.read_text())
            self.verified[v['id']] = v
            self.dir_files[rel(OPEN / 'verified')].append((f.name, sha(f.read_bytes())))
        self.listing = load('listing')
        self.a4 = load('a4_index')
        self.a4_families = {}
        for fam in self.a4['families']:
            path = PROJECT / fam['json_file']
            self.a4_families[fam['slug']] = {**json.loads(path.read_text()), **fam}
            self.dir_files[rel(REVIEW / 'evidence/access-terms')].append((path.name, sha(path.read_bytes())))
        self.a4_by_repo = {v['id']: v for v in self.a4['verifier_results_read']}
        self.a5 = load('a5')
        self.site_rows: dict[str, dict] = {}       # A5 census id -> placeholder row
        self.site_tokens: dict[str, set] = {}      # A5 census id -> identity tokens
        self.merges: list[dict] = []
        self.issues: list[str] = []

    # --------------------------------------------------------------------------- A4 captures
    def capture_id(self, slug: str) -> str | None:
        fam = self.a4_families.get(slug)
        if not fam or not fam.get('capture_sha256'):
            return None
        return f'a4:{slug}:{fam["capture_sha256"][:16]}'

    def cited_captures(self) -> set[str]:
        text = json.dumps(self.entries)
        cited = {self.capture_id(slug) for slug in self.a4_families if f'r-corpus-{slug}' in text and any(
            e['id'] == f'r-corpus-{slug}' for e in self.entries)}
        return cited | {c for c in (self.capture_id(slug) for slug in self.a4_families) if f'"{c}"' in text}

    def access_terms_sources(self) -> list[dict]:
        out = []
        for slug, fam in sorted(self.a4_families.items()):
            out.append({'capture_id': self.capture_id(slug), 'family_slug': slug, 'family': fam['family'],
                        'url': fam['official_url'], 'captured_at': fam['captured_at'],
                        'sha256': fam['capture_sha256'], 'capture_kind': fam.get('capture_kind'),
                        'access_kind': ACCESS_FROM_A4[fam['access_kind']]})
        return out

    # --------------------------------------------------------------------------- audit corrections (R2)
    def recheck_scope(self, rows: dict[str, dict]) -> dict[str, str]:
        """The classifier audit's population re-check (register-classifier-audit.json, recommendation.in_scope).

        Returns {repo: rule} for in-scope rows that leave the Hugging Face group:
        - simulated: signals that are only simulated (the audit's list; rows that also hold real recordings stay);
        - emg_rule: EMG-only rows count only when recorded with or used as a neural interface; a row whose stated
          use is missing ("not stated", "kept for checking") or that the audit corrected leaves;
        - undetermined: modality unclear and no evidence of brain signals beyond names (no electrophysiology file
          format in the file list).
        """
        a = self.audit
        if not a:
            raise ValueError('register-classifier-audit.json is required: the D11 population is printed only after '
                             'its re-check')
        out: dict[str, str] = {}
        screens = a['population_screens']
        for item in screens['in_scope_synthetic']:
            repo = item.split(' ', 1)[0]
            if 'stays' not in item:
                out[repo] = 'simulated'
        corrected_out = {w['id'] for w in a['wrong_rows'] if w['field'] == 'in_scope' and w['corrected_value'] is False}
        unstated = re.compile(r'not stated|kept for checking|no neural-interface|not a neural interface', re.I)
        ephys = re.compile(r'\b(?:FIF|EDF|BDF|GDF|SET|VHDR|CNT|MFF|XDF|NWB)\b')
        for i, r in rows.items():
            if not r['in_scope'] or i in out:
                continue
            if r['modality'] == ['EMG'] and (unstated.search(r['scope_reason']) or i in corrected_out):
                out[i] = 'emg_rule'
            elif r['modality'] == ['unclear'] and not ephys.search(r.get('formats') or ''):
                out[i] = 'undetermined'
            elif i in corrected_out:
                out[i] = 'undetermined'
        self.audit_applied = sorted(f'{rule}:{repo}' for repo, rule in out.items())
        return out

    def card_unreadable(self) -> set[str]:
        return set(self.audit['population_screens']['no_readable_card']['ids'])

    # ======================================================================= site census (A5)
    def site_slug(self, src: dict) -> str:
        site = src.get('site') or {}
        page = site.get('page') or site.get('page_at_freeze')
        if page and page.startswith('/datasets/'):
            return page.strip('/').split('/')[1]
        slug = src['id'].removeprefix('site-').removeprefix('register-')
        slug = re.sub(r'-\d+\.\d+\.\d+$', '', slug)
        return slug

    def build_site_tokens(self) -> None:
        ks = load('known_sources')
        page_links = {p['slug']: p['source_links'] for p in ks['site_dataset_pages']}
        mvp = load('mvp')
        for src in self.a5['sources']:
            if src['census_group'] == 'adjacent_moabb':
                continue
            t: set[str] = set()
            idn = src['identity']
            rec = idn.get('record')
            for r in (rec if isinstance(rec, list) else [rec]):
                t |= ident_tokens(r)
            for a in (idn.get('aliases_source') or {}).get('value') or []:
                t |= ident_tokens(a)
                t.add('name:' + a.lower())
            if idn.get('moabb_loader'):
                t.add('name:' + idn['moabb_loader'].lower())
            if idn.get('hf_repo'):
                t.add('hf:' + idn['hf_repo'].lower())
            for f in src.get('findings', []):
                m = re.search(r'(\d{5,})', str(f.get('params', {}).get('current_concept', '')))
                if m:
                    t.add('zenodo:' + m.group(1))
            slug = self.site_slug(src)
            for link in page_links.get(slug, []):
                if 'CITATION' not in link:
                    t |= ident_tokens(link)
            self.site_tokens[src['id']] = t
        # HF mirrors a served site file names for a site dataset (mvp.json attribution: "mirror <repo>").
        for ds in mvp.get('datasets', []):
            m = re.search(r'mirror ([\w.-]+/[\w.-]+)', ds.get('attribution') or '')
            if not m:
                continue
            for cid, t in self.site_tokens.items():
                if ident_tokens(ds.get('source')) & t:
                    t.add('hf:' + m.group(1).rstrip('.').lower())

    def site_for_tokens(self, tokens: set[str]) -> list[str]:
        return sorted(cid for cid, t in self.site_tokens.items() if t & tokens)

    # ======================================================================= Hugging Face group
    def hf_group(self) -> None:
        rows = {r['id']: r for r in self.classified}
        self.hf_rows_cls = rows
        self.check_verified_sources()
        listing = self.listing['datasets']
        classified_in = sorted(i for i, r in rows.items() if r['in_scope'])
        self.recheck = self.recheck_scope(rows)
        in_scope = [i for i in classified_in if i not in self.recheck]
        self.hf_counts = Counter()
        self.hf_counts['classifier_in_scope'] = len(classified_in)
        for rule in ('simulated', 'emg_rule', 'undetermined'):
            self.hf_counts[f'recheck_out_{rule}'] = sum(1 for v in self.recheck.values() if v == rule)
        self.hf_counts['in_scope'] = len(in_scope)
        details = {}
        for i in in_scope:
            p = OPEN / 'raw/details' / (i.replace('/', '__') + '.json')
            d = json.loads(p.read_text()) if p.exists() else {}
            details[i] = d.get('body') if isinstance(d.get('body'), dict) else None
            if p.exists():
                self.dir_files[rel(OPEN / 'raw/details')].append((p.name, sha(p.read_bytes())))

        def meta(i):
            L = listing[i]['listing']
            b = details.get(i) or {}
            tags = L.get('tags') or b.get('tags') or []
            sib = b.get('siblings') or []
            gated = L.get('gated', b.get('gated', False))
            return {'repo': i, 'revision_sha': L.get('sha') or b.get('sha'),
                    'gated': gated if gated in ('manual', 'auto') else False,
                    'licence_tags': sorted(t[8:] for t in tags if t.startswith('license:')),
                    'size_bytes': sum((s.get('size') or 0) for s in sib) if sib else None,
                    'files': len(sib) if sib else None}

        no_tag = sum(1 for i in in_scope if not meta(i)['licence_tags'])
        gated = Counter(str(meta(i)['gated']) for i in in_scope)
        self.hf_counts['no_licence_tag'] = no_tag
        self.hf_counts['gated_manual'] = gated.get('manual', 0)
        self.hf_counts['gated_auto'] = gated.get('auto', 0)

        held = [i for i in in_scope if i in REVIEW_HOLD]
        self.hf_counts['held_for_review'] = len(held)
        pool = [i for i in in_scope if i not in REVIEW_HOLD]

        # Repos of this site's own datasets merge into the site rows.
        merged = {}
        for i in pool:
            hits = self.site_for_tokens({'hf:' + i.lower()})
            if len(hits) == 1:
                merged[i] = hits[0]
            elif len(hits) > 1:
                raise ValueError(f'{i}: matches two site rows {hits}')
        self.hf_counts['merged_into_site_rows'] = len(merged)

        # Uploader series (series_keys): same uploader, same name stem. Two or more members collapse; a repo whose
        # name carries a participant-style or u<n> token always collapses. A row with verified comparison findings
        # (VERIFIED_SOURCES) keeps its own row unless its name is participant-like.
        keep_single = {i for i in pool if i in VERIFIED_SOURCES and not participant_like_repo(i)}
        families, self.series_label = series_keys([i for i in pool if i not in merged and i not in keep_single])
        in_family = {x for v in families.values() for x in v}
        singles = [i for i in pool if i not in merged and i not in in_family]
        self.hf_counts['single_rows'] = len(singles)
        self.hf_counts['family_rows'] = len(families)
        self.hf_counts['family_members'] = len(in_family)
        assert len(singles) + len(in_family) + len(merged) + len(held) == len(in_scope)

        self.hf_meta = {i: meta(i) for i in in_scope}
        self.hf_rows_cls = rows
        self.hf_singles, self.hf_families, self.hf_merged = singles, families, merged

    # --------------------------------------------------------------------------- verifier gates (D3)
    def personal_info_noted(self, i: str) -> bool:
        """The classifier or a verifier noted personal or identifying information on this upload (any verdict)."""
        if PERSONAL_FLAG in ((self.hf_rows_cls.get(i) or {}).get('flags') or []):
            return True
        v = self.verified.get(i) or {}
        return PERSONAL_FLAG in (v.get('claim_checked') or '') or PERSONAL_FLAG in (v.get('flag_by_flag') or {})

    @staticmethod
    def verifier_own_text(v: dict) -> str:
        parts = []
        for k in VERIFIER_OWN_FIELDS:
            x = v.get(k)
            parts += list(x.values()) if isinstance(x, dict) else [x or '']
        return '\n'.join(str(p) for p in parts)

    def withheld_reasons(self, i: str) -> list[str]:
        """Every reason this upload gets no comparison finding: personal_info, do_not_state, same_party."""
        out = ['personal_info'] if self.personal_info_noted(i) else []
        v = self.verified.get(i)
        if v:
            text = self.verifier_own_text(v)
            if DO_NOT_STATE.search(text):
                out.append('do_not_state')
            if SAME_PARTY.search(text) and i not in SAME_PARTY_NOTE_SCOPE:
                out.append('same_party')
        return out

    def withheld_reason(self, i: str) -> str | None:
        """The first withheld reason (personal_info first: such a row is a plain row), or None."""
        r = self.withheld_reasons(i)
        return r[0] if r else None

    def check_verified_sources(self) -> None:
        """The comparison table agrees with the verifier results and A4 (run once, before any row is built)."""
        for repo, spec in VERIFIED_SOURCES.items():
            v = self.verified.get(repo)
            if not v or v['verdict'] != 'confirmed':
                raise ValueError(f'VERIFIED_SOURCES {repo}: no confirmed verifier result')
            if self.withheld_reason(repo):
                raise ValueError(f'VERIFIED_SOURCES {repo}: withheld ({self.withheld_reason(repo)})')
            a4 = set((self.a4_by_repo.get(repo) or {}).get('families_matched_by_name', []))
            for slug, (fields, quote) in spec['families'].items():
                if quote not in v['original_source']:
                    raise ValueError(f'VERIFIED_SOURCES {repo}/{slug}: {quote!r} is not in the verifier\'s original_source')
                if slug not in a4 or not self.capture_id(slug):
                    raise ValueError(f'VERIFIED_SOURCES {repo}/{slug}: no A4 capture made for this verifier result')
        for repo in SAME_PARTY_NOTE_SCOPE:
            if not SAME_PARTY.search(self.verifier_own_text(self.verified[repo])):
                raise ValueError(f'SAME_PARTY_NOTE_SCOPE {repo}: the verifier result has no same-party note')

    def hf_findings_single(self, i: str, m: dict, rid_of_row) -> tuple[list, dict]:
        """Findings for one upload; returns (findings, extras for step evidence and the comparison review)."""
        out = []
        v = self.verified.get(i)
        verdict = v.get('verdict') if v else None
        withheld = self.withheld_reason(i)
        extra = {'comparisons': [], 'verdict': verdict, 'withheld': withheld, 'plain': withheld == 'personal_info'}
        if not m['licence_tags']:
            out.append(finding('licence_tag_absent'))
        if m['gated']:
            out.append(finding('gated', mode=m['gated']))
        if extra['plain']:
            return out, extra       # personal or identifying information: listing metadata only
        r = self.hf_rows_cls[i]
        # derived_from: only what the card itself names, resolved to exactly one register row per identifier.
        if (r.get('derived_from') or {}).get('basis') == 'stated in card':   # audit S3: declared sources only
            claim = r.get('source_claim') or {}
            toks = ident_tokens(claim.get('link')) | ident_tokens(claim.get('named_source'))
            for row in sorted(set(rid_of_row(toks))):
                out.append(finding('derived_from', row=row))
        # Verified comparisons (D3): confirmed verdict, an A4 capture, and the verifier's own identification of
        # the family (VERIFIED_SOURCES); nothing for a withheld row.
        spec = VERIFIED_SOURCES.get(i) if not withheld else None
        for slug, (fields, _quote) in sorted((spec or {}).get('families', {}).items()):
            cap = self.capture_id(slug)
            if not comparison_allowed(verdict, cap, withheld):
                raise ValueError(f'{i}/{slug}: VERIFIED_SOURCES lists a comparison the D3 gate refuses')
            fam = self.a4_families[slug]
            row = self.row_for_family(slug)
            kw = {'source': slug, 'fields': sorted(fields), 'capture_id': cap}
            if row:
                kw['row'] = row
            out.append(finding('matches_metadata_of', **kw))
            td = self.terms_difference(fam, m, spec.get('declared'))
            if td:
                out.append(finding('terms_differ', original=td[0], declared=td[1], declared_by=td[2],
                                   capture_id=cap, source=slug))
            extra['comparisons'].append(cap)
        return out, extra

    def terms_difference(self, fam: dict, m: dict, declared_override=None) -> tuple[str, str, str] | None:
        """(original, declared, declared_by) when the source's captured terms differ from what the upload declares.

        declared_by is licence_tag (the repo's licence tags) unless the card gives this source its own licence."""
        if declared_override:
            declared, by = declared_override
            decl = [declared]
        else:
            declared, by = ('+'.join(m['licence_tags']) if m['licence_tags'] else 'none'), 'licence_tag'
            decl = [canon_licence(t) for t in m['licence_tags']]
        access = ACCESS_FROM_A4[fam['access_kind']]
        if access != 'open':
            return access, declared, by
        orig = canon_licence(fam.get('licence_stated'))
        if not orig:
            return None
        if decl and all(d == orig for d in decl):
            return None
        return orig, declared, by

    def row_for_family(self, slug: str) -> str | None:
        return self.family_rows.get(slug)

    # ======================================================================= EEGDash family
    def eegdash_family(self, moabb: list[dict]) -> dict:
        m = load('eegdash')
        moabb_by_token = defaultdict(set)
        for e in moabb:
            if e.get('merge_into'):
                continue
            for t in ident_tokens(e['moabb'].get('data_url')) | ident_tokens(e['moabb'].get('doi') and 'doi:' + e['moabb']['doi']):
                if t.startswith(('openneuro:', 'nemar:')):
                    moabb_by_token[t].add(e['id'])
        moabb_rows = {e['id']: e for e in moabb}
        members = []
        site_hits = 0
        kinds = Counter()
        for mirror in sorted(m):
            v = m[mirror]
            acc = v['openneuro_id']
            kind = 'openneuro' if acc else None
            if not acc:
                mm = re.match(r'EEGDash/(nm\d{6})$', mirror)
                if mm:
                    acc, kind = mm.group(1), 'nemar'
                else:
                    kind = 'other'
            kinds[kind] += 1
            rec = {'mirror': mirror, 'accession': acc, 'accession_kind': kind,
                   'licence_tags': sorted(v['licence_tags']), 'gated': bool(v['gated'])}
            if acc:
                hits = self.site_for_tokens({f'{kind}:{acc}'})
                if len(hits) == 1:
                    rec['site_row'] = self.site_row_id(hits[0])
                    self.site_aliases[hits[0]].append({'value': mirror, 'kind': 'eegdash_mirror'})
                    site_hits += 1
                elif len(moabb_by_token.get(f'{kind}:{acc}', ())) == 1:
                    rid = next(iter(moabb_by_token[f'{kind}:{acc}']))
                    rec['moabb_row'] = rid
                    moabb_rows[rid]['aliases'].append({'value': mirror, 'kind': 'eegdash_mirror'})
                    moabb_rows[rid]['source_groups'] = sorted(set(moabb_rows[rid]['source_groups']) | {'eegdash'})
                    self.moabb_mirror_hits = getattr(self, 'moabb_mirror_hits', 0) + 1
            members.append(rec)
        rid = self.ids.slug('corpus', 'openneuro-mirrors')
        fam = {'id': rid, 'kind': 'eegdash', 'n': len(members), 'by_accession_kind': dict(sorted(kinds.items())),
               'site_rows_with_mirror': site_hits, 'members': members}
        self.eegdash_counts = {'mirrors': len(members), **{f'{k}': v for k, v in sorted(kinds.items())},
                               'site_rows_with_mirror': site_hits,
                               'moabb_rows_with_mirror': getattr(self, 'moabb_mirror_hits', 0)}
        no_tag = sum(1 for x in members if not x['licence_tags'])
        entry = self.base_entry(rid, 'dataset', 'eegdash', 'eegdash_family', 'OpenNeuro and NEMAR via EEGDash')
        entry.update({
            'aliases': [{'value': 'EEGDash', 'kind': 'name'}],
            'source_groups': ['eegdash'],
            'urls': {},
            'family': {'uploader': 'EEGDash', 'series': 'OpenNeuro and NEMAR mirrors', 'n': len(members),
                       'search_url': None},
            'terms_as_stated': {'value': None, 'by': 'hf_licence_tag'},
            'access': 'open',
            'level': 1,
            'step_evidence': self.listing_steps('the Hugging Face listing of each mirror, read ' + CHECKED_HF,
                                                rel(INPUTS['eegdash'])),
            'gaps': [], 'next_step_gaps': [gap(2, 'files_opened')],
            'status': 'listed',
            'findings': [finding('family', n=len(members), uploader='EEGDash', series='OpenNeuro and NEMAR mirrors')]
                        + ([finding('licence_tag_absent_members', n=no_tag, of=len(members))] if no_tag else []),
            'checked': CHECKED_HF,
        })
        fam['licence_tag_counts'] = dict(sorted(Counter(t for x in members for t in (x['licence_tags'] or ['none'])).items()))
        self.families.append(fam)
        return entry

    # ======================================================================= helpers for entries
    def base_entry(self, rid, ladder, group, kind, name) -> dict:
        return OrderedDict([('id', rid), ('ladder', ladder), ('group', group), ('kind', kind), ('name', name),
                            ('aliases', []), ('source_groups', [group]), ('urls', {}),
                            ('correction', mailto(rid)), ('links', {})])

    def listing_steps(self, source_note: str, source_file: str, licence_state='pass') -> dict:
        return {'1': {'state': 'pass' if licence_state == 'pass' else 'partial',
                      'items': [{'item': 'host_record', 'state': 'pass', 'source': source_file},
                                {'item': 'licence_as_stated', 'state': licence_state, 'source': source_file}]},
                '2': {'state': 'not_reached'}, '3': {'state': 'not_reached'}, '4': {'state': 'not_reached'},
                '5': {'state': 'not_reached'}}

    def site_row_id(self, census_id: str) -> str:
        src = next(s for s in self.a5['sources'] if s['id'] == census_id)
        return f'r-site-{self.site_slug(src)}'

    # ======================================================================= MOABB
    def moabb_groups(self) -> list[dict]:
        cat = load('moabb_catalog')
        shortlist = {e['adapter']: e for e in load('moabb_shortlist')['entries']}
        a3 = load('a3')['sources']
        groups: OrderedDict[str, list] = OrderedDict()
        for e in cat['entries']:
            k = (e.get('DOI') or '').strip().lower() or 'loader:' + e['Dataset']
            groups.setdefault(k, []).append(e)
        self.moabb_counts = {'release': MOABB_RELEASE, 'loaders': len(cat['entries']), 'record_groups': len(groups)}
        holds = {'Liu2024': 'released_ids_duplicated', 'Schrag2026Pediatric': 'targets_stored_with_outputs',
                 'Hinss2021': 'deposits_differ', 'Kim2025BetaRange': 'onset_timing_unresolved',
                 'Dreyer2023': 'release_family_unchecked', 'Alawieh2025': 'one_offline_session'}
        brain_invaders = re.compile(r'^BI20\d\d[ab]?$')
        out = []
        merged_n = 0
        for key, es in groups.items():
            loaders = [e['Dataset'] for e in es]
            rid = self.ids.numbered('moabb', 'moabb:' + key)
            toks = set()
            for e in es:
                toks |= ident_tokens(e.get('DOI')) | ident_tokens(e.get('Data URL'))
                toks.add('name:' + e['Dataset'].lower())
            hits = self.site_for_tokens(toks)
            lic = sorted({e['License'] for e in es if e.get('License') and e['License'] != 'Unknown'})
            first = es[0]
            name = loaders[0]
            if len(loaders) > 1:
                cp = re.sub(r'[_A-Z]*$', '', __import__('os').path.commonprefix(loaders)).rstrip('_')
                name = cp if len(cp) >= 4 else loaders[0]
            entry = self.base_entry(rid, 'dataset', 'moabb', 'moabb_record_group', name)
            doi = (first.get('DOI') or '').replace('https://doi.org/', '') or None
            entry['aliases'] = [{'value': x, 'kind': 'moabb_loader'} for x in loaders]
            if doi:
                entry['aliases'].append({'value': doi, 'kind': 'doi'})
            # The catalog's DOI column holds a paper DOI for some loaders and a data-repository DOI for others; only a
            # paper DOI is a paper link (a deposit DOI stays the record link and an alias).
            paper_doi = first.get('DOI') if first.get('DOI') and not DATA_DOI.search(first['DOI']) else None
            entry['urls'] = {k: v for k, v in (('record', first.get('Data URL') or first.get('DOI')),
                                               ('paper', paper_doi)) if v}
            entry['moabb'] = {
                'loaders': loaders, 'doi': doi, 'data_url': first.get('Data URL'), 'repository': first.get('Repository'),
                'licence_as_listed': lic or None, 'release': MOABB_RELEASE,
                'fields_as_listed': [{'loader': e['Dataset'], 'paradigm': e.get('Paradigm'),
                                      'people': _int(e.get('#Subj')), 'channels': _int(e.get('#Chan')),
                                      'sampling_rate_hz': _num(e.get('Freq (Hz)'))} for e in es]}
            sl = next((shortlist[x] for x in loaders if x in shortlist), None)
            step1 = [{'item': 'host_record', 'state': 'pass', 'source': rel(INPUTS['moabb_catalog'])
                      + '#entries[Dataset=' + loaders[0] + '].DOI'}]
            if lic:
                step1.append({'item': 'licence_as_stated', 'state': 'pass',
                              'source': rel(INPUTS['moabb_catalog']) + '#entries[Dataset=' + loaders[0] + '].License'})
                terms = {'value': ', '.join(lic), 'by': 'moabb_catalog'}
                gaps = []
            else:
                step1.append({'item': 'licence_as_stated', 'state': 'gap',
                              'source': rel(INPUTS['moabb_catalog'])})
                terms = {'value': None, 'by': 'none'}
                gaps = [gap(1, 'licence_as_stated')]
            if sl:
                step1[0]['source'] = rel(INPUTS['moabb_shortlist']) + f'#entries[adapter={sl["adapter"]}].deposit_url'
                dl = sl.get('deposit_license') or {}
                dl_name = dl.get('name') or dl.get('id')
                if dl_name:
                    step1[1] = {'item': 'licence_as_stated', 'state': 'pass',
                                'source': rel(INPUTS['moabb_shortlist']) + f'#entries[adapter={sl["adapter"]}].deposit_license'}
                    terms = {'value': dl_name, 'by': 'deposit_record'}
                    gaps = []
            entry['terms_as_stated'] = terms
            entry['access'] = 'catalog_only'
            entry['level'] = 1
            entry['step_evidence'] = {'1': {'state': 'pass' if not gaps else 'partial', 'items': step1},
                                      '2': {'state': 'not_reached'}, '3': {'state': 'not_reached'},
                                      '4': {'state': 'not_reached'}, '5': {'state': 'not_reached'}}
            entry['gaps'] = gaps
            entry['next_step_gaps'] = [gap(2, 'files_opened')]
            entry['status'] = 'listed'
            entry['findings'] = []
            entry['checked'] = '2026-10-19'
            hold = next((holds[x] for x in loaders if x in holds), None)
            if hold:
                entry['findings'].append(finding('hold', reason_code=hold))
            if any(brain_invaders.match(x) for x in loaders):
                entry['findings'].append(finding('named_in_corpus', models=['LaBraM', 'REVE'], release_resolved=False))
            if 'BI2013a' in loaders:
                bi = a3['bi2013a']
                entry['status'] = 'planned'
                entry['findings'].append(finding('planned'))
                entry['terms_as_stated'] = {'value': bi['licence']['data']['title_on_record'], 'by': 'zenodo_record'}
                entry['urls']['record'] = 'https://doi.org/10.5281/zenodo.2669187'
                entry['urls']['paper'] = bi['paper']          # the technical report (A3), never the concept DOI
                entry['aliases'].append({'value': '10.5281/zenodo.2669187', 'kind': 'doi'})
                entry['moabb']['record_note'] = {'record': 'Zenodo record 2669187', 'concept_doi': '10.5281/zenodo.1494163',
                                                 'latest_version': bool(bi.get('record_is_latest_version')),
                                                 'licence_identifier': bi['licence']['data']['identifier']}
                self.bi2013a_steps(entry)
            if hits:
                if len(hits) > 1:
                    raise ValueError(f'MOABB {loaders} matches two site rows {hits}')
                entry['merge_into'] = self.site_slug(next(s for s in self.a5['sources'] if s['id'] == hits[0]))
                for x in loaders:
                    self.site_aliases[hits[0]].append({'value': x, 'kind': 'moabb_loader'})
                # The record group's DOI goes with it (B8b): every identifier of a merged row is an alias of its site row.
                for a in entry['aliases']:
                    if a['kind'] == 'doi':
                        self.site_aliases[hits[0]].append({'value': a['value'], 'kind': 'doi'})
                self.site_groups[hits[0]].add('moabb')
                merged_n += 1
            out.append(entry)
        self.moabb_counts['merged_into_site_rows'] = merged_n
        return out

    def bi2013a_steps(self, entry: dict) -> None:
        src = next(s for s in self.a5['sources'] if s['id'] == 'moabb-bi2013a')
        entry['step_evidence'] = self.a5_steps(src)
        # The plan rule, as the dataset register states it (B8b): the furthest step whose own evidence is on file, with
        # files opened listed as a gap at step 2 (the census's contiguous step is 1).
        entry['level'] = src['level'] if self.freeze else src.get('level_recommended', 1)
        entry['gaps'] = [g for g in self.a5_gaps(src) if g['step'] <= entry['level']]
        entry['next_step_gaps'] = [g for g in self.a5_gaps(src, all_steps=True) if g['step'] == entry['level'] + 1]
        entry['checked'] = '2026-10-19'

    # ======================================================================= agreement corpora (A4)
    def corpus_rows(self) -> list[dict]:
        out = []
        names = {'seed': 'SEED family', 'deap': 'DEAP', 'amigos': 'AMIGOS', 'mahnob-hci': 'MAHNOB-HCI',
                 'dreamer': 'DREAMER', 'tuh-eeg': 'TUH EEG Corpus'}
        for slug in ('seed', 'deap', 'amigos', 'mahnob-hci', 'dreamer', 'tuh-eeg'):
            fam = self.a4_families[slug]
            if fam.get('group', '').startswith('agreement corpus') is False:
                raise ValueError(f'{slug} is not an agreement corpus in A4')
            rid = self.ids.slug('corpus', slug)
            cap = self.capture_id(slug)
            e = self.base_entry(rid, 'dataset', 'corpus', 'agreement_corpus', names[slug])
            members = fam.get('members') or []
            e['aliases'] = [{'value': x, 'kind': 'name'} for x in members if x != names[slug]]
            e['urls'] = {'record': fam['official_url']}
            access = ACCESS_FROM_A4[fam['access_kind']]
            e['terms_as_stated'] = {'value': fam['terms_sentence'], 'by': 'a4_capture'}
            e['original_terms'] = {'access_kind': access, 'capture_id': cap,
                                   'redistribution_stated': bool(fam.get('redistribution_stated'))}
            e['access'] = access
            e['level'] = 1
            e['level_cap'] = {'step': 1, 'rule': 'gated_stays_at_step_1'}
            src = fam['json_file'] + '#capture_sha256'
            e['step_evidence'] = {'1': {'state': 'pass', 'items': [
                {'item': 'host_record', 'state': 'pass', 'source': src},
                {'item': 'licence_as_stated', 'state': 'pass', 'source': fam['json_file'] + '#terms_sentence'}]},
                '2': {'state': 'not_reached'}, '3': {'state': 'not_reached'}, '4': {'state': 'not_reached'},
                '5': {'state': 'not_reached'}}
            e['gaps'] = []
            e['next_step_gaps'] = [gap(2, 'files_opened')]
            e['status'] = 'listed'
            e['findings'] = []
            e['checked'] = fam['captured_at'][:10]
            out.append(e)
            self.family_rows[slug] = rid
        return out

    # ======================================================================= site placeholders (A5)
    def a5_steps(self, src: dict) -> dict:
        out = {}
        for step in ('1', '2', '3', '4', '5'):
            items = []
            for it in src['steps'].get(step, []):
                s = it.get('sources') or []
                for one in (s or [None]):   # one evidence item per source
                    source = (one['file'] + '#' + one['field']) if one else None
                    item = {'item': it['item'], 'state': it['state'], 'source': source}
                    if item not in items:
                        items.append(item)
            states = {i['state'] for i in items}
            st = 'pass' if states <= {'pass', 'not-applicable'} and items else ('gap' if states == {'gap'} else 'partial')
            out[step] = {'state': st, 'items': items}
        return out

    def a5_gaps(self, src: dict, all_steps=False) -> list[dict]:
        out = []
        for step in ('1', '2', '3', '4', '5'):
            for it in src['steps'].get(step, []):
                if it['state'] == 'gap':
                    out.append(gap(step, it['item']))
        return out

    def site_placeholders(self) -> None:
        """Placeholder site rows from the A5 census, so pages can build against the real shape (B8b replaces)."""
        self.site_aliases = defaultdict(list)
        self.site_groups = defaultdict(set)
        for src in self.a5['sources']:
            if src['census_group'] == 'adjacent_moabb':
                continue
            cid = src['id']
            slug = self.site_slug(src)
            rid = self.ids.slug('site', slug)
            e = self.base_entry(rid, 'dataset', 'site', 'site_dataset', src['name'])
            idn = src['identity']
            for a in (idn.get('aliases_source') or {}).get('value') or []:
                e['aliases'].append({'value': a, 'kind': 'name'})
            rec = idn.get('record')
            e['urls'] = {'record': rec[0] if isinstance(rec, list) else rec}
            site = src.get('site') or {}
            page = site.get('page') or site.get('page_at_freeze') or site.get('section_at_freeze')
            e['site'] = {'page': page, 'status': site.get('register_status'), 'census_id': cid}
            lic = next((s.get('value') for it in src['steps'].get('1', []) if it['item'] == 'licence_as_stated'
                        for s in (it.get('sources') or []) if isinstance(s.get('value'), str)), None)
            e['terms_as_stated'] = {'value': lic, 'by': 'site_release' if lic else 'none'}
            e['access'] = 'open'
            level = src.get('level_recommended', src['level'])
            at = src.get('at_freeze') or {}
            if 'level' in at and level == src['level']:
                level = at['level']
            e['level'] = level
            e['step_evidence'] = self.a5_steps(src)
            gaps = at.get('gaps') if 'gaps' in at else None
            if gaps is not None:
                e['gaps'] = [gap(g['step'], g['item']) for g in gaps]
            else:
                e['gaps'] = [g for g in self.a5_gaps(src) if g['step'] <= level]
            e['next_step_gaps'] = [g for g in self.a5_gaps(src) if g['step'] == level + 1]
            status = (site.get('register_status') or 'listed').replace(' ', '_')
            e['status'] = status
            fs = []
            for f in src.get('findings', []):
                if f['code'] == 'version_clarification':
                    p = f['params']
                    fs.append(finding('version_clarification', current=p['current'], earlier=p['earlier'],
                                      recordings_source=p['recordings_source'],
                                      recordings_evaluated=p['recordings_evaluated']))
                elif f['code'] == 'policy_note':
                    fs.append(finding('policy_note', source=f['params']['source']))
            for cm in src.get('corpus_mentions', []):
                if re.search(r'held-out evaluation', cm['text'], re.I):
                    continue
                models = sorted({re.sub(r'\s*\(.*\)$', '', x) for x in cm['models']})
                resolved = 'release resolved' in cm['text'] or 'resolved by name' in cm['text']
                fs.append(finding('named_in_corpus', models=models, release_resolved=resolved))
            e['findings'] = fs
            links = {}
            if page:
                links['page'] = page
            if src['census_group'] == 'core':
                links['exposure'] = '/protocols/' + {'beta': 'beta-8ch', 'ds003810': 'mi-rest', 'ds005342': 'idle', 'ds006593': 'p300-target', 'eegmat': 'arithmetic-rest', 'tmnred': 'semantic-target', 'eesm19': 'sleep-scalp'}[slug] + '/#pretraining-exposure'
            e['links'] = links
            e['checked'] = self.a5['generated_at'][:10]
            e['placeholder'] = True
            self.site_rows[cid] = e

    # ======================================================================= models
    def model_rows(self) -> list[dict]:
        ev = {o['id']: o for o in load('model_evidence')['opportunities']}
        meta = load('hf_model_metadata')['repos']
        nl = load('neurolm_update')
        fm = load('fm_update')['results']['foundation-models-v9']
        fm_models = {m['id']: m for m in fm['models']}
        neurolm_model = _find_key(nl, 'model')
        proceedings = _find_text(nl, r'https://proceedings\.iclr\.cc/[^"\s]+')
        out = []

        def hf_alias(repo, kind, relation=None):
            m = meta.get(repo) or {}
            a = {'value': repo, 'kind': kind, 'licence_tag': '+'.join(m.get('licence_tags') or []) or 'none'}
            if relation:
                a['relation'] = relation
            return a

        def part(state, value=None, by='none'):
            return {'state': state, 'value': value, 'by': by}

        def steps(items: dict) -> tuple[dict, int, list, list]:
            se = {}
            for k, defn in MODEL_STEPS.items():
                its = []
                for i in defn['items']:
                    state, src = items.get(i, ('gap', None))
                    # An item with several sources appears once per source; `source` is always one string or null.
                    for one in (src if isinstance(src, list) else [src]):
                        its.append({'item': i, 'state': state, 'source': one})
                states = {x['state'] for x in its}
                se[k] = {'state': 'pass' if states <= {'pass', 'not-applicable'} else
                         ('gap' if states == {'gap'} else 'partial'), 'items': its}
            level = 0
            for k in ('1', '2', '3', '4', '5'):
                if items.get(MODEL_ANCHORS[k], ('gap',))[0] == 'pass':
                    level = int(k)
            gaps = [gap(int(k), x['item']) for k in se for x in se[k]['items'] if x['state'] == 'gap' and int(k) <= level]
            nxt = [gap(int(k), x['item']) for k in se for x in se[k]['items'] if x['state'] == 'gap' and int(k) == level + 1]
            gaps, nxt = _unique(gaps), _unique(nxt)
            for k in se:
                if int(k) > level and se[k]['state'] == 'gap':
                    se[k] = {'state': 'not_reached', 'items': se[k]['items']}
            return se, level, gaps, nxt

        ev_file = rel(INPUTS['model_evidence'])
        meta_file = rel(INPUTS['hf_model_metadata'])
        nl_file = rel(INPUTS['neurolm_update'])
        fm_file = rel(INPUTS['fm_update'])

        def model(slug, name, kind, signal, terms, items, findings_, urls, aliases, venue=None, links=None,
                  exposure=None, merge_into=None, checked='2026-10-16'):
            rid = self.ids.slug('model', slug)
            e = self.base_entry(rid, 'model', 'model', 'model', name)
            e['source_groups'] = ['model']
            e['aliases'] = aliases
            e['urls'] = {k: v for k, v in urls.items() if v}
            e['model_kind'] = kind
            e['signal'] = signal
            e['terms_by_part'] = terms
            e['terms_as_stated'] = {'value': terms['weights']['value'], 'by': terms['weights']['by']}
            if venue:
                e['venue'] = venue
            if exposure:
                e['exposure'] = exposure
            se, level, gaps, nxt = steps(items)
            e['level'] = level
            e['step_evidence'] = se
            e['gaps'] = gaps
            e['next_step_gaps'] = nxt
            e['access'] = 'open' if terms['weights']['state'] == 'stated' else 'unknown'
            e['status'] = 'published' if level >= 4 else 'listed'
            e['findings'] = findings_
            e['links'] = links or {}
            e['checked'] = checked
            if merge_into:
                e['merge_into'] = merge_into
            out.append(e)
            return e

        def venue(value, evidence, url=None):
            v = {'value': value, 'kind': 'conference_paper', 'evidence': evidence, 'checked': '2026-10-16'}
            if url:
                v['url'] = url
            return v

        def proc_url(o):
            return next((s for s in o['sources'] if 'proceedings.iclr.cc' in s), None)

        # NeuroLM-B: scored here on two site sections (pilot and IESSEEG), exposure unknown.
        o = ev['neurolm']
        ck = neurolm_model['checkpoint']
        model('neurolm-b', 'NeuroLM-B', 'foundation_model', ['human_scalp_eeg'],
              {'code': part('stated', 'MIT', 'repository_licence_file'),
               'weights': part('stated', 'CC BY 4.0', 'model_card_metadata'),
               'data': part('per_source', None, 'paper')},
              {'official_record': ('pass', nl_file + '#results.*.model.repository'),
               'code_terms': ('pass', nl_file + '#rights'),
               'weights_terms': ('pass', meta_file + '#repos[Weibang/NeuroLM].licence_tags'),
               'data_terms': ('pass', ev_file + '#opportunities[id=neurolm].licenses.data'),
               'file_listing': ('pass', meta_file + '#repos[Weibang/NeuroLM].weight_files'),
               'files_checked': ('pass', nl_file + '#results.*.model.checkpoint.sha256'),
               'scored_here': ('pass', [nl_file, rel(INPUTS['iesseeg_update'])]),
               'in_matrix': ('gap', None)},
              [], {'paper': proceedings or None, 'code': neurolm_model.get('repository'),
                   'weights': ck.get('repository')},
              [hf_alias('Weibang/NeuroLM', 'official_weights')],
              venue=venue('ICLR 2025', 'official_proceedings', proceedings) if proceedings else None,
              links={'cases': ['/topics/pilot-studies/#neurolm-eegmat', '/topics/clinical-groups/#iesseeg']},
              exposure='unknown')

        # ZUNA 1.1 and eeg-fm-masking: measured here; they fold into the site method rows, with no venue.
        z = fm_models['zuna']
        zuna_copies = self.weight_copies('zuna', meta)
        model('zuna', 'ZUNA 1.1', 'foundation_model', ['human_scalp_eeg'],
              {'code': part('not_found'), 'weights': part('stated', 'Apache-2.0', 'model_card_metadata'),
               'data': part('not_found')},
              {'official_record': ('pass', fm_file + '#results.*.models[id=zuna].paper'),
               'code_terms': ('gap', None), 'weights_terms': ('pass', fm_file + '#results.*.models[id=zuna].weights_licence'),
               'data_terms': ('gap', None), 'file_listing': ('pass', meta_file + '#repos[Zyphra/ZUNA1.1].weight_files'),
               'files_checked': ('pass', fm_file + '#results.*.models[id=zuna].checkpoint_sha256'),
               'scored_here': ('pass', fm_file), 'in_matrix': ('pass' if z.get('panel') == 'matrix' else 'gap', fm_file)},
              [], {'paper': z.get('paper'), 'weights': 'https://huggingface.co/Zyphra/ZUNA1.1'},
              [hf_alias('Zyphra/ZUNA1.1', 'official_weights')] + zuna_copies,
              links={'page': '/methods/zuna/'}, exposure='unknown', merge_into='zuna')
        e = fm_models['eeg-fm-masking/mae-r9cm-L2']
        model('eeg-fm-masking', 'eeg-fm-masking', 'foundation_model', ['human_scalp_eeg'],
              {'code': part('not_found'), 'weights': part('stated', 'CC-BY-4.0', 'model_card_metadata'),
               'data': part('per_source', None, 'paper')},
              {'official_record': ('pass', fm_file + '#results.*.models[id=eeg-fm-masking/mae-r9cm-L2].paper'),
               'code_terms': ('gap', None),
               'weights_terms': ('pass', fm_file + '#results.*.models[id=eeg-fm-masking/mae-r9cm-L2].weights_licence'),
               'data_terms': ('pass', fm_file + '#results.*.pretraining_exposure'),
               'file_listing': ('pass', rel(INPUTS['model_listing'])),
               'files_checked': ('pass', fm_file + '#results.*.models[id=eeg-fm-masking/mae-r9cm-L2].checkpoint_sha256'),
               'scored_here': ('pass', fm_file),
               'in_matrix': ('pass' if e.get('panel') == 'matrix' else 'gap', fm_file)},
              [], {'paper': e.get('paper'), 'weights': 'https://huggingface.co/PierreGtch/eeg-fm-masking_mae_r9cm_L2'},
              [{'value': 'PierreGtch/eeg-fm-masking_mae_r9cm_L2', 'kind': 'official_weights', 'licence_tag': 'cc-by-4.0'}],
              links={'page': '/methods/eeg-fm-masking/'}, merge_into='eeg-fm-masking')

        # Models this site has not run: identified, with terms by part and holds.
        o = ev['diver-1']
        model('diver-1', 'DIVER-1', 'foundation_model', ['human_ieeg', 'human_scalp_eeg'],
              {'code': part('stated', 'MIT', 'repository_licence_file'), 'weights': part('not_found'),
               'data': part('not_found')},
              {'official_record': ('pass', ev_file + '#opportunities[id=diver-1].sources'),
               'code_terms': ('pass', ev_file + '#opportunities[id=diver-1].licenses.code'),
               'weights_terms': ('gap', None), 'data_terms': ('gap', None), 'file_listing': ('gap', None)},
              [finding('hold', reason_code='weights_licence_not_found')],
              {'paper': 'https://arxiv.org/abs/2512.19097', 'code': o['code_url']},
              self.named_hf_repos(['braindecode/DIVER-1-0.1s-tiny', 'braindecode/DIVER-1-1s-small'], meta))
        o = ev['popt']
        model('popt', 'Population Transformer (PopT)', 'spatial_aggregation_model', ['human_ieeg', 'human_scalp_eeg'],
              {'code': part('stated', 'MIT', 'repository_licence_file'), 'weights': part('not_found'),
               'data': part('stated', 'CC BY 4.0', 'project_page')},
              {'official_record': ('pass', ev_file + '#opportunities[id=popt].sources'),
               'code_terms': ('pass', ev_file + '#opportunities[id=popt].licenses.code'),
               'weights_terms': ('gap', None),
               'data_terms': ('pass', ev_file + '#opportunities[id=popt].licenses.data'),
               'file_listing': ('pass', meta_file + '#repos[PopulationTransformer/popt_brainbert_stft].weight_files')},
              [finding('hold', reason_code='weights_licence_not_found')],
              {'code': o['code_url'], 'weights': o['weights_url'], 'data': o['data_url']},
              [hf_alias('PopulationTransformer/popt_brainbert_stft', 'official_weights')]
              + [{**hf_alias('braindecode/popt-pretrained', 'weights_copy', 'declares_base_model'),
                  'relation_to': 'PopulationTransformer/popt_brainbert_stft'}],
              venue=venue('ICLR 2025', 'camera_ready_pdf'))
        o = ev['omnimouse']
        model('omnimouse', 'OmniMouse', 'foundation_model', ['mouse_calcium_imaging'],
              {'code': part('not_found'), 'weights': part('stated', 'Apache-2.0', 'model_card_metadata'),
               'data': part('stated', 'CC BY 4.0', 'dataset_card')},
              {'official_record': ('pass', ev_file + '#opportunities[id=omnimouse].sources'),
               'code_terms': ('gap', None),
               'weights_terms': ('pass', meta_file + '#repos[the-enigma-project/omnimouse-80M].licence_tags'),
               'data_terms': ('pass', ev_file + '#opportunities[id=omnimouse].licenses.data'),
               'file_listing': ('pass', meta_file + '#repos[the-enigma-project/omnimouse-80M].weight_files'),
               'files_checked': ('gap', None)},
              [finding('hold', reason_code='code_licence_not_found'),
               finding('hold', reason_code='not_human_scalp_eeg')],
              {'code': o['code_url'], 'weights': o['weights_url'], 'data': o['data_url']},
              [hf_alias('the-enigma-project/omnimouse-80M', 'official_weights')]
              + self.same_file_copies('the-enigma-project/omnimouse-80M',
                                      ['the-enigma-project/omnimouse', 'TheKonstantinWilleke/omnimouse'], meta),
              venue=venue('ICLR 2026', 'camera_ready_pdf'))
        o = ev['biox-bridge']
        model('biox-bridge', 'BioX-Bridge', 'adaptation_method', ['human_scalp_eeg', 'ecg', 'ppg', 'emg'],
              {'code': part('not_found'), 'weights': part('per_source', None, 'paper'),
               'data': part('per_source', None, 'paper')},
              {'official_record': ('pass', ev_file + '#opportunities[id=biox-bridge].sources'),
               'code_terms': ('gap', None), 'weights_terms': ('gap', None),
               'data_terms': ('pass', ev_file + '#opportunities[id=biox-bridge].licenses.data'),
               'file_listing': ('gap', None)},
              [finding('hold', reason_code='code_licence_not_found'),
               finding('hold', reason_code='no_released_checkpoint')],
              {'paper': proc_url(o), 'code': o['code_url']}, [],
              venue=venue('ICLR 2026', 'official_proceedings', proc_url(o)))
        o = ev['poyo-plus']
        model('poyo-plus', 'POYO+', 'decoding_model', ['mouse_calcium_imaging'],
              {'code': part('not_found'), 'weights': part('not_found'), 'data': part('not_found')},
              {'official_record': ('pass', ev_file + '#opportunities[id=poyo-plus].sources'),
               'code_terms': ('gap', None), 'weights_terms': ('gap', None), 'data_terms': ('gap', None),
               'file_listing': ('gap', None)},
              [finding('hold', reason_code='code_not_reachable'), finding('hold', reason_code='not_human_scalp_eeg')],
              {'paper': proc_url(o), 'data': o['data_url']}, [],
              venue=venue('ICLR 2025', 'official_proceedings', proc_url(o)))
        o = ev['poyo-cap']
        model('poyo-cap', 'POYO-CAP', 'decoding_model', ['mouse_calcium_imaging'],
              {'code': part('stated', 'MIT', 'repository_licence_file'), 'weights': part('not_found'),
               'data': part('not_found')},
              {'official_record': ('pass', ev_file + '#opportunities[id=poyo-cap].sources'),
               'code_terms': ('pass', ev_file + '#opportunities[id=poyo-cap].licenses.code'),
               'weights_terms': ('gap', None), 'data_terms': ('gap', None), 'file_listing': ('gap', None)},
              [finding('hold', reason_code='no_released_checkpoint'), finding('hold', reason_code='not_human_scalp_eeg')],
              {'paper': proc_url(o), 'code': o['code_url'], 'data': o['data_url']}, [],
              venue=venue('ICLR 2026', 'official_proceedings', proc_url(o)))
        o = ev['neuroformer']
        model('neuroformer', 'Neuroformer', 'generative_model', ['mouse_spiking'],
              {'code': part('stated', 'MIT', 'repository_licence_file'), 'weights': part('not_found'),
               'data': part('not_found')},
              {'official_record': ('pass', ev_file + '#opportunities[id=neuroformer].sources'),
               'code_terms': ('pass', ev_file + '#opportunities[id=neuroformer].licenses.code'),
               'weights_terms': ('gap', None), 'data_terms': ('gap', None), 'file_listing': ('gap', None)},
              [finding('hold', reason_code='no_released_checkpoint'), finding('hold', reason_code='not_human_scalp_eeg')],
              {'code': o['code_url']}, [], venue=venue('ICLR 2024', 'camera_ready_pdf'))
        o = ev['brainlm']
        model('brainlm', 'BrainLM', 'foundation_model', ['human_fmri'],
              {'code': part('not_found'), 'weights': part('stated', 'CC BY-NC-ND 4.0', 'model_card_metadata'),
               'data': part('application_required', None, 'paper')},
              {'official_record': ('pass', ev_file + '#opportunities[id=brainlm].sources'),
               'code_terms': ('gap', None),
               'weights_terms': ('pass', meta_file + '#repos[vandijklab/brainlm].licence_tags'),
               'data_terms': ('pass', ev_file + '#opportunities[id=brainlm].licenses.data'),
               'file_listing': ('pass', meta_file + '#repos[vandijklab/brainlm].weight_files'),
               'files_checked': ('gap', None)},
              [finding('hold', reason_code='noncommercial_noderivs_weights'),
               finding('hold', reason_code='not_human_scalp_eeg')],
              {'paper': proc_url(o), 'code': o['code_url'], 'weights': o['weights_url']},
              [hf_alias('vandijklab/brainlm', 'official_weights')],
              venue=venue('ICLR 2024', 'official_proceedings', proc_url(o)))
        return out

    # --------------------------------------------------------------------------- weight copies
    OFFICIAL = {'cbramod': 'weighting666/CBraMod', 'brainomni': 'OpenTSLab/BrainOmni', 'zuna': 'Zyphra/ZUNA1.1',
                'reve': 'brain-bzh/reve-base', 'luna': 'PulpBio/LUNA', 'eegmamba': 'weighting666/EEGMamba',
                'codebrain': 'YjMajy/CodeBrain'}
    # Candidate copies of the weights this site measures, found in the model listing. Each is kept only with a
    # relation read from HF metadata: the same weight file (sha256) as the official repo, a declared base model,
    # or (braindecode and named "-pretrained"/"-official" repos) the repo's own name and file list.
    CANDIDATES = {
        'labram': ['braindecode/labram-pretrained', 'braindecode/Labram-Braindecode', 'eeg-telecom-paris/labram-base-official'],
        'cbramod': ['smoking11/CBraMod', 'braindecode/cbramod-pretrained', 'hanhan05/cbramod-pretrained',
                    'eeg-telecom-paris/cbramod-base-official', 'oraculumai/CBraMod-CoreML-Apple'],
        'eegpt': ['braindecode/eegpt-pretrained', 'eeg-telecom-paris/eegpt-large-official'],
        'brainomni': ['braindecode/brainomni-base-pretrained'],
        'st-eegformer': ['braindecode/STEEGFormer-base', 'braindecode/STEEGFormer-large', 'eugenehp/ST-EEGFormer'],
        'zuna': ['modulsx/ZUNA1.1', 'suryatmodulus/ZUNA1.1', 'oraculumai/ZUNA1.1-CoreML-Apple',
                 'oraculumai/ZUNA1.1-CoreML-Apple-1s', 'oraculumai/ZUNA1.1-CoreML-Apple-30s',
                 'oraculumai/ZUNA1.1-Classifier-CoreML-Apple'],
    }
    NAMED_OK = re.compile(r'^(?:braindecode|eeg-telecom-paris)/', re.I)
    NOT_COPIES = {
        'oraculumai/CBraMod-MI-CoreML': 'adds a fine-tuned motor-imagery head',
        'braindecode/ZUNA': 'same file as the earlier ZUNA release, not ZUNA 1.1',
        'NeuroTechX/zuna': 'weight file matches neither ZUNA release',
        'mhough/zuna-base': 'weight file matches neither ZUNA release',
        'scitty/neurolm-faced': 'fine-tuned on another dataset',
    }

    def weight_copies(self, slug: str, meta: dict) -> list[dict]:
        """Copies of a measured model's weights, each with the relation HF metadata supports.

        same_file: a weight file's LFS sha256 equals one in the official repo or in a copy already accepted;
        declares_base_model: the card metadata names the official repo or an accepted copy as base_model;
        named: an organisation's conversion repo named as the model's pretrained weights, with weight files.
        """
        official = self.OFFICIAL.get(slug)
        hash_owner = {w['sha256']: official for w in (meta.get(official) or {}).get('weight_files', []) if w.get('sha256')}
        known_repos = {official} if official else set()
        accepted: dict[str, str] = {}
        target: dict[str, str] = {}
        changed = True
        while changed:
            changed = False
            for repo in self.CANDIDATES.get(slug, []):
                m = meta.get(repo)
                if repo in accepted or not m or not m.get('http_ok'):
                    continue
                hashes = {w['sha256'] for w in m.get('weight_files', []) if w.get('sha256')}
                shared = sorted(hash_owner[h] for h in hashes if h in hash_owner)
                bases = sorted(set(m.get('base_model') or []) & known_repos)
                if shared:
                    rel_, target[repo] = 'same_file', shared[0]
                elif bases:
                    rel_, target[repo] = 'declares_base_model', bases[0]
                elif self.NAMED_OK.match(repo) and m.get('weight_files'):
                    rel_ = 'named'
                else:
                    continue
                accepted[repo] = rel_
                for h in hashes:
                    hash_owner.setdefault(h, repo)
                known_repos.add(repo)
                changed = True
        out = []
        for r in self.CANDIDATES.get(slug, []):
            if r in accepted:
                a = {'value': r, 'kind': 'weights_copy', 'relation': accepted[r],
                     'licence_tag': '+'.join(meta[r].get('licence_tags') or []) or 'none'}
                if r in target:
                    a['relation_to'] = target[r]
                out.append(a)
        return out

    def same_file_copies(self, official: str, repos: list[str], meta: dict) -> list[dict]:
        off = {w['sha256'] for w in meta[official]['weight_files'] if w.get('sha256')}
        out = []
        for r in repos:
            m = meta.get(r) or {}
            if off & {w['sha256'] for w in m.get('weight_files', []) if w.get('sha256')}:
                out.append({'value': r, 'kind': 'weights_copy', 'relation': 'same_file', 'relation_to': official,
                            'licence_tag': '+'.join(m.get('licence_tags') or []) or 'none'})
        return out

    def named_hf_repos(self, repos: list[str], meta: dict) -> list[dict]:
        return [{'value': r, 'kind': 'weights_copy', 'relation': 'named',
                 'licence_tag': '+'.join((meta.get(r) or {}).get('licence_tags') or []) or 'none'}
                for r in repos if (meta.get(r) or {}).get('http_ok')]

    def site_model_placeholders(self, external_models: list[dict]) -> list[dict]:
        prof = load('profiles')['methods']
        fm = load('fm_update')['results']['foundation-models-v9']
        meta = load('hf_model_metadata')['repos']
        covered = {e.get('merge_into') for e in external_models if e.get('merge_into')}
        core = {'eegnet', 'labram', 'cbramod', 'shallowfbcspnet', 'deep4net', 'csp-lda', 'cca', 'fbcca', 'etrca'}
        fm_panel = {}
        for m in fm['models']:
            slug = m['id'].split('/')[0].rsplit('-base', 1)[0].rsplit('-large', 1)[0]
            slug = {'steegformer': 'st-eegformer', 'erp-fm': 'erp-fm'}.get(slug, slug)
            fm_panel[slug] = fm_panel.get(slug) or m.get('panel') == 'matrix'
        out = []
        for slug, p in prof.items():
            rid = self.ids.slug('model', slug)
            e = self.base_entry(rid, 'model', 'model', 'site_model', p['aliases'][0] if p.get('aliases') else slug)
            e['aliases'] = [{'value': a, 'kind': 'name'} for a in p.get('aliases', [])[1:]] + self.weight_copies(slug, meta)
            e['site'] = {'page': f'/methods/{slug}/', 'status': 'published', 'method_slug': slug}
            in_matrix = slug in core or fm_panel.get(slug, False)
            level = 5 if in_matrix else 4
            e['level'] = level
            e['step_evidence'] = {str(k): {'state': 'pass' if k <= level else 'not_reached'} for k in range(1, 6)}
            e['gaps'] = []
            e['next_step_gaps'] = []
            e['terms_as_stated'] = {'value': None, 'by': 'site_release'}
            e['access'] = 'open'
            e['status'] = 'published'
            e['findings'] = []
            e['links'] = {'page': f'/methods/{slug}/'}
            e['checked'] = self.a5['generated_at'][:10]
            e['placeholder'] = True
            if slug in covered:
                e['covered_by_external_row'] = f'r-model-{slug}'
            out.append(e)
        return out

    # ======================================================================= the freeze (B8b)
    def apply_frozen_site_rows(self) -> None:
        """Replace the A5 placeholders by the site rows re-read at the freeze (export-site-register-rows.mjs).

        The rows keep the placeholders' opaque ids (r-site-<slug>, one per A5 census id); the aliases and source groups
        that merged external rows bring (site_aliases, site_groups) are added in documents(), as before."""
        fz = self.frozen
        if fz.get('freeze') != D or fz.get('schema_version') != 'bci-report-site-register-rows-v1':
            raise ValueError(f'{rel(SITE_ROWS)}: not the site rows of freeze {D}')
        if fz['reread']['mismatches'] or fz['reread']['unresolved']:
            raise ValueError(f'{rel(SITE_ROWS)}: the census did not re-read cleanly at the freeze')
        if fz['census']['sha256'] != sha(INPUTS['a5'].read_bytes()):
            raise ValueError(f'{rel(SITE_ROWS)}: built from another A5 census than the one pinned here')
        rows = {r['census_id']: r for r in fz['datasets']}
        if set(rows) != set(self.site_rows):
            raise ValueError(f'site rows {sorted(set(rows) ^ set(self.site_rows))} are in one of the census and the frozen rows only')
        for cid, r in rows.items():
            rid = self.ids.slug('site', r['slug'])
            if rid != self.site_rows[cid]['id']:
                raise ValueError(f'{cid}: frozen as {rid}, the census row is {self.site_rows[cid]["id"]}')
            e = self.base_entry(rid, 'dataset', 'site', 'site_dataset', r['name'])
            e['aliases'] = [dict(a) for a in r['aliases']]
            e['urls'] = dict(r['urls'])
            e['site'] = dict(r['site'])
            e['terms_as_stated'] = dict(r['terms_as_stated'])
            e['access'] = r['access']
            e['level'] = r['level']
            e['step_evidence'] = json.loads(json.dumps(r['step_evidence']))
            e['gaps'] = [dict(g) for g in r['gaps']]
            e['next_step_gaps'] = [dict(g) for g in r['next_step_gaps']]
            e['status'] = r['status']
            e['findings'] = []
            for f in r['findings']:
                if f['code'] == 'hold' and f['params']['reason_code'] in SITE_HOLD_REASONS:
                    code = f['params']['reason_code']
                    hold_id = SITE_HOLD_REASONS[code]
                    if not f.get('sources') or not all(x.endswith(f'#holds[id={hold_id}]') for x in f['sources']):
                        raise ValueError(f'{rid}: the site hold {code} rests on {f.get("sources")}, not the hold {hold_id}')
                    if code not in self.site_hold_words:
                        self.site_holds_withheld.append(f'{rid}:{code}')
                        continue
                e['findings'].append(self.frozen_finding(f))
            e['links'] = dict(r['links'])
            e['checked'] = r['checked']
            self.site_rows[cid] = e

    @staticmethod
    def frozen_finding(f: dict) -> dict:
        """A site row's finding, rebuilt through register_findings (its census sources kept, publicised later)."""
        out = finding(f['code'], **f['params'])
        if f.get('sources'):
            out['sources'] = list(f['sources'])
        return out

    def frozen_site_models(self, external_models: list[dict]) -> list[dict]:
        """The model rows this site builds from entities.ts at the freeze: one per method page (site_model), and the
        other measured baselines and the directory's cards (model). External rows with merge_into fold in later."""
        meta = load('hf_model_metadata')['repos']
        external_ids = {e['id'] for e in external_models if not e.get('merge_into')}
        out = []
        for r in self.frozen['models']:
            rid = self.ids.slug('model', r['key'])
            if rid in external_ids:
                raise ValueError(f'{rid}: a site model row and an external row share an id')
            e = self.base_entry(rid, 'model', 'model', r['kind'], r['name'])
            aliases = [dict(a) for a in r['aliases']]
            if r['kind'] == 'site_model':
                official = self.OFFICIAL.get(r['key'])
                for a in aliases:
                    if official and a['value'] == official:
                        a['kind'] = 'official_weights'
                aliases += self.weight_copies(r['key'], meta)
            for a in aliases:
                if a['kind'] == 'official_weights' and a['value'] in meta:
                    a['licence_tag'] = '+'.join(meta[a['value']].get('licence_tags') or []) or 'none'
            e['aliases'] = aliases
            e['urls'] = dict(r['urls'])
            e['model_kind'] = r['model_kind']
            e['signal'] = list(r['signal'])
            e['terms_by_part'] = json.loads(json.dumps(r['terms_by_part']))
            w = r['terms_by_part']['weights']
            e['terms_as_stated'] = {'value': w['value'], 'by': w['by']}
            e['access'] = r['access']
            e['level'] = r['level']
            e['step_evidence'] = json.loads(json.dumps(r['step_evidence']))
            e['gaps'] = [dict(g) for g in r['gaps']]
            e['next_step_gaps'] = [dict(g) for g in r['next_step_gaps']]
            e['status'] = r['status']
            e['findings'] = []
            e['links'] = dict(r['links'])
            e['checked'] = r['checked']
            if r['kind'] == 'site_model':
                e['site'] = {'page': r['links']['page'], 'status': 'published', 'method_slug': r['key']}
            out.append(e)
        return out

    def frozen_level_definitions(self) -> dict:
        """The step names and needs as the pages print them (i18n.ts, read at the freeze): the same English names and
        needs as this exporter's, and the pages' Chinese for what each step needs."""
        out = {}
        for ladder, steps in (('dataset', DATASET_STEPS), ('model', MODEL_STEPS)):
            printed = {str(x['step']): x for x in self.frozen['ladders'][ladder]}
            out[ladder] = {}
            for k, d in steps.items():
                x = printed[k]
                if (x['en'], x['zh'], x['needs_en']) != (d['en'], d['zh'], d['needs_en']):
                    raise ValueError(f'{ladder} step {k}: the pages say {x["en"]}/{x["zh"]} ("{x["needs_en"]}"), '
                                     f'this exporter {d["en"]}/{d["zh"]} ("{d["needs_en"]}")')
                out[ladder][k] = {**d, 'needs_zh': x['needs_zh']}
        rules = self.frozen['rules']
        if [r['en'] for r in RULES] != rules['en'] or [r['zh'] for r in RULES] != rules['zh']:
            raise ValueError('the register rules differ from the pages\' rules (i18n.ts registerCopy.rules)')
        return out

    # ======================================================================= assemble
    def run(self):
        self.family_rows: dict[str, str] = {}
        self.comparison_review: list[dict] = []
        self.build_site_tokens()
        self.site_placeholders()
        corpus = self.corpus_rows()
        # Site rows that are the source family of a verified comparison (exact A4 slug to census id).
        for slug, cid in (('physionet-eegmmidb', 'site-register-physionet-eegmmidb-1.0.0'),
                          ('physionet-eegmat', 'site-eegmat'), ('physionet-ltrsvp', 'site-ltrsvp')):
            if cid in self.site_rows:
                self.family_rows[slug] = self.site_rows[cid]['id']
        moabb = self.moabb_groups()
        eegdash = self.eegdash_family(moabb)
        self.hf_group()
        # An upload that is a MOABB record's own data URL is that record: it becomes the MOABB row's alias.
        moabb_by_tok = defaultdict(list)
        for e in moabb:
            if not e.get('merge_into'):
                for t in ident_tokens(e['moabb'].get('data_url')):
                    moabb_by_tok[t].append(e)
        into_moabb = 0
        for i in list(self.hf_singles):
            hit = moabb_by_tok.get('hf:' + i.lower(), [])
            if len(hit) == 1:
                self.hf_singles.remove(i)
                hit[0]['aliases'].append({'value': i, 'kind': 'hf_repo'})
                into_moabb += 1
        self.hf_counts['single_rows'] = len(self.hf_singles)
        self.hf_counts['merged_into_moabb_rows'] = into_moabb
        hf_entries = self.hf_entries(moabb, corpus)
        models = self.model_rows()
        self.entries = hf_entries + [eegdash] + moabb + corpus + models
        self.site_models = self.site_model_placeholders(models)
        if self.freeze:
            self.apply_frozen_site_rows()
            self.site_models = self.frozen_site_models(models)
        self.ids.retire_unseen(('hf', 'moabb'))
        # Repo ids that look like participant ids leave the id map's retired keys (their numbers stay reserved).
        self.ids.redact_retired(lambda full: full.startswith('hf|hf:') and participant_like_repo(full[len('hf|hf:'):]))
        self.check_unique_identifiers()

    def rid_resolver(self, moabb: list[dict], corpus: list[dict]):
        """Map identifier tokens named by a card to exactly one register row id."""
        index = defaultdict(set)
        for cid, toks in self.site_tokens.items():
            for t in toks:
                if not t.startswith('name:'):
                    index[t].add(self.site_rows[cid]['id'])
        for e in moabb:
            if e.get('merge_into'):
                continue
            for t in ident_tokens(e['moabb'].get('doi') and 'doi:' + e['moabb']['doi']) | ident_tokens(e['moabb'].get('data_url')):
                index[t].add(e['id'])
        corpus_names = {'seed': r'\bSEED(?:-IV|-V|-VIG)?\b', 'deap': r'\bDEAP\b', 'amigos': r'\bAMIGOS\b',
                        'mahnob-hci': r'\bMAHNOB', 'dreamer': r'\bDREAMER\b',
                        'tuh-eeg': r'\bTUH\b|\bTUEG\b|\bTUAB\b|\bTUSZ\b|\bTUEV\b|\bTUAR\b|Temple University Hospital'}

        def resolve(tokens: set[str], text: str = '') -> list[str]:
            rows = []
            for t in tokens:
                hit = index.get(t, set())
                if len(hit) == 1:
                    rows.append(next(iter(hit)))
            for slug, rx in corpus_names.items():
                if text and re.search(rx, text):
                    rows.append(f'r-corpus-{slug}')
            return sorted(set(rows))
        return resolve

    def classified_block(self, i: str, unreadable: set[str]) -> dict:
        """The classifier fields the audit found displayable (modality, paradigm, content kind), as tokens, with
        the audit's marker for rows whose card could not be read (values then come from names and file lists)."""
        r = self.hf_rows_cls[i]
        return {'modality': sorted({_token(x) for x in r['modality']}), 'paradigm': _token(r['paradigm']),
                'content_kind': _token(r['content_kind']), 'card_readable': i not in unreadable,
                'by': 'register_classifier'}

    def hf_entries(self, moabb, corpus) -> list[dict]:
        resolve = self.rid_resolver(moabb, corpus)
        unreadable = self.card_unreadable()
        out = []
        for i in sorted(self.hf_singles + list(self.hf_merged)):
            m = self.hf_meta[i]
            rid = self.ids.numbered('hf', 'hf:' + i.lower())
            name = i.split('/', 1)[1]
            e = self.base_entry(rid, 'dataset', 'hf', 'hf_upload', i)
            # A search by the repo name, never a URL with the uploader's name in it.
            e['urls'] = {} if i.split('/')[0].lower() in name.lower() else {'search': HF_SEARCH + urllib.parse.quote(name)}
            e['hf'] = dict(m)
            e['classified'] = self.classified_block(i, unreadable)
            e['terms_as_stated'] = {'value': '+'.join(m['licence_tags']) or None, 'by': 'hf_licence_tag'}
            e['access'] = 'gated' if m['gated'] else 'open'

            def rid_of_row(toks, _i=i):
                claim = self.hf_rows_cls[_i].get('source_claim') or {}
                return resolve(toks, str(claim.get('named_source') or ''))
            findings_, extra = self.hf_findings_single(i, m, rid_of_row)
            findings_ = [f for f in findings_ if not (f['code'] == 'derived_from' and f['params']['row'] == rid)]
            e['level'] = 1
            se = self.listing_steps('', rel(INPUTS['listing']) + f'#datasets[{i}]')
            if extra['comparisons']:
                # One evidence item per source: the verifier result, then each A4 capture of an original-terms page.
                se['3'] = {'state': 'partial', 'items': [
                    {'item': 'derivation', 'state': 'pass', 'source': 'verified result (confirmed)'}]
                    + [{'item': 'original_terms', 'state': 'pass', 'source': cap} for cap in sorted(extra['comparisons'])]}
                e['level_cap'] = {'step': 1, 'rule': 'reuploads_stay_at_step_1'}
            elif m['gated']:
                e['level_cap'] = {'step': 1, 'rule': 'gated_stays_at_step_1'}
            if extra['verdict'] == 'confirmed' or extra['withheld']:
                a4 = sorted((self.a4_by_repo.get(i) or {}).get('families_matched_by_name', []))
                kept = sorted((VERIFIED_SOURCES.get(i) or {}).get('families', {})) if not extra['withheld'] else []
                self.comparison_review.append({
                    'row': rid, 'repo': i, 'verdict': extra['verdict'], 'withheld': self.withheld_reasons(i),
                    'a4_families_matched_by_name': a4, 'families_kept': kept,
                    'families_dropped': sorted(set(a4) - set(kept)),
                    'basis': {s: {'fields': sorted(f), 'original_source_phrase': q}
                              for s, (f, q) in sorted((VERIFIED_SOURCES.get(i) or {}).get('families', {}).items())
                              if s in kept}})
            e['_plain'] = extra['plain']
            e['_withheld'] = extra['withheld']
            e['step_evidence'] = se
            e['gaps'] = []
            e['next_step_gaps'] = [gap(2, 'files_opened')]
            e['status'] = 'listed'
            e['findings'] = findings_
            e['checked'] = CHECKED_HF
            e['_verdict'] = extra['verdict']
            if i in self.hf_merged:
                cid = self.hf_merged[i]
                e['merge_into'] = self.site_slug(next(s for s in self.a5['sources'] if s['id'] == cid))
                self.site_aliases[cid].append({'value': i, 'kind': 'hf_repo'})
                self.site_groups[cid].add('hf')
            out.append(e)
        for (up, key), members in sorted(self.hf_families.items()):
            series = self.series_label[(up, key)]
            rid = self.ids.numbered('hf', f'hf-family:{up.lower()}/{key}')
            ms = [self.hf_meta[x] for x in members]
            tags = Counter(t for x in ms for t in (x['licence_tags'] or ['none']))
            no_tag = sum(1 for x in ms if not x['licence_tags'])
            g = Counter(x['gated'] for x in ms if x['gated'])
            search = None if up.lower() in series.lower() else HF_SEARCH + urllib.parse.quote(series)
            # The row name carries the uploader (row body only, never a URL or an id), so two uploaders' series with
            # one stem read apart: 'uploader/stem*'.
            e = self.base_entry(rid, 'dataset', 'hf', 'hf_family', f'{up}/{series}*')
            e['urls'] = {'search': search} if search else {}
            e['family'] = {'uploader': up, 'series': series, 'n': len(members), 'search_url': search}
            e['terms_as_stated'] = {'value': ', '.join(f'{t} ({n})' for t, n in sorted(tags.items())),
                                    'by': 'hf_licence_tag'}
            e['access'] = 'gated' if g and sum(g.values()) == len(members) else 'open'
            e['level'] = 1
            e['step_evidence'] = self.listing_steps('', rel(INPUTS['listing']) + '#datasets[members of this family]')
            e['gaps'] = []
            e['next_step_gaps'] = [gap(2, 'files_opened')]
            e['status'] = 'listed'
            fs = [finding('family', n=len(members), uploader=up, series=series)]
            if no_tag:
                fs.append(finding('licence_tag_absent_members', n=no_tag, of=len(members)))
            if g:
                fs.append(finding('gated_members', n=sum(g.values()), of=len(members)))
            e['findings'] = fs
            e['checked'] = CHECKED_HF
            digest = sha(json.dumps(sorted((x['repo'], x['revision_sha']) for x in ms)).encode())
            self.families.append({'id': rid, 'kind': 'hf_series', 'uploader': up, 'series': series,
                                  'n': len(members), 'search_url': search,
                                  'licence_tag_counts': dict(sorted(tags.items())), 'no_licence_tag': no_tag,
                                  'gated': {'manual': g.get('manual', 0), 'auto': g.get('auto', 0)},
                                  'size_bytes': sum(x['size_bytes'] or 0 for x in ms),
                                  'member_digest': digest})
            out.append(e)
        return out

    def check_unique_identifiers(self):
        """No DOI, accession or repo id in two rendered rows."""
        seen = {}
        for e in self.rendered_dataset_entries():
            ids_ = set()
            for a in e['aliases']:
                if a['kind'] in ('hf_repo', 'doi', 'accession', 'eegdash_mirror', 'moabb_loader'):
                    ids_.add(a['kind'] + ':' + a['value'].lower())
            if e.get('hf'):
                ids_.add('hf_repo:' + e['hf']['repo'].lower())
            for x in ids_:
                if x in seen and seen[x] != e['id']:
                    raise ValueError(f'{x} appears in two rows: {seen[x]} and {e["id"]}')
                seen[x] = e['id']

    def rendered_dataset_entries(self) -> list[dict]:
        rows = [e for e in self.entries if not e.get('merge_into') and e['ladder'] == 'dataset']
        for cid, e in self.site_rows.items():
            e2 = dict(e)
            e2['aliases'] = e['aliases'] + self.site_aliases.get(cid, [])
            rows.append(e2)
        return rows

    # ======================================================================= documents
    def counts(self, entries: list[dict]) -> dict:
        ds = [e for e in entries if e['ladder'] == 'dataset']
        ms = [e for e in entries if e['ladder'] == 'model']
        listing = self.listing['datasets']
        eegdash_n = sum(1 for k in listing if k.startswith('EEGDash/'))
        prefilter = len(load('prefilter'))
        return {
            'rows': {'total': len(entries), 'dataset': len(ds), 'model': len(ms),
                     'dataset_by_group': dict(sorted(Counter(e['group'] for e in ds).items())),
                     'dataset_by_level': {str(k): v for k, v in sorted(Counter(e['level'] for e in ds).items())},
                     'model_by_level': {str(k): v for k, v in sorted(Counter(e['level'] for e in ms).items())},
                     'by_status': dict(sorted(Counter(e['status'] for e in entries).items()))},
            'hf': {'snapshot': {'retrieved_at': self.listing['retrieved_at'][:19] + 'Z',
                                'search_terms': len(self.listing['terms']), 'tag_filters': len(self.listing['tag_filters']),
                                'listings': len(listing), 'eegdash_mirrors': eegdash_n,
                                'other_uploads': len(listing) - eegdash_n, 'prefilter_dropped': prefilter,
                                'classified': len(self.classified)},
                   **{k: v for k, v in sorted(self.hf_counts.items())},
                   # in_scope = classifier_in_scope minus the three re-check rules; awaiting owner or R2 sign-off,
                   # so a page prints the basis (classifier_in_scope and each recheck_out_*) beside in_scope.
                   'recheck_signoff': 'pending'},
            'eegdash': self.eegdash_counts,
            'moabb': self.moabb_counts,
            'corpus': {'families': 6, 'captured': sum(1 for s in ('seed', 'deap', 'amigos', 'mahnob-hci', 'dreamer',
                                                                    'tuh-eeg') if self.capture_id(s))},
            'models': self.model_counts(entries),
        }

    def model_counts(self, entries: list[dict]) -> dict:
        """The model ladder's rows other than this site's method pages: external_rows = the models and papers whose
        official records were read outside a method page (B8a's model rows, and at the freeze the directory's cards and
        the other measured baselines that /methods/ names), those merged into a method page's row included;
        merged_into_site_methods = the external rows folded into a method page's row; from_site_records = the rows
        among them built from this site's own records (the directory and the baselines; zero in the external file)."""
        merged = sum(1 for e in self.entries if e['ladder'] == 'model' and e.get('merge_into'))
        own = sum(1 for e in entries if e['ladder'] == 'model' and e['kind'] == 'model' and not e.get('merge_into'))
        site_built = {f'r-model-{r["key"]}' for r in (self.frozen or {}).get('models', []) if r['kind'] == 'model'}
        return {'external_rows': own + merged, 'merged_into_site_methods': merged,
                'from_site_records': sum(1 for e in entries if e['id'] in site_built)}

    def header(self, status: str) -> OrderedDict:
        return OrderedDict([
            ('schema_version', SCHEMA), ('release_id', RELEASE_ID), ('status', status),
            ('generated_at', dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
            ('level_definitions', self.frozen_level_definitions() if self.freeze
             else {'dataset': DATASET_STEPS, 'model': MODEL_STEPS}),
            ('item_definitions', {
                'dataset': {i: {'step': int(k), 'label_en': labels(i)[0], 'label_zh': labels(i)[1],
                                'anchor': DATASET_ANCHORS[k] == i} for k, d in DATASET_STEPS.items() for i in d['items']},
                'model': {i: {'step': int(k), 'label_en': labels(i)[0], 'label_zh': labels(i)[1],
                              'anchor': MODEL_ANCHORS[k] == i} for k, d in MODEL_STEPS.items() for i in d['items']}}),
            ('rules', RULES),
            ('sources', {
                'hf': {'retrieved_at': self.listing['retrieved_at'][:19] + 'Z', 'search_terms': self.listing['terms'],
                       'tag_filters': self.listing['tag_filters'],
                       'population': 'uploads the register classifier marked in scope (brain-signal data) from this '
                                     'snapshot, after the keyword prefilter; EEGDash mirrors form one family row'},
                'eegdash': {'map': INPUT_LABELS['eegdash']},
                'moabb': {'release': MOABB_RELEASE, 'docs_commit': load('moabb_catalog')['source_develop_head_observed'],
                          'catalog_checked': '2026-10-19'},
                # Only the captures a served row cites: the six corpus rows and the captures in served findings.
                'access_terms': [x for x in self.access_terms_sources() if x['capture_id'] in self.cited_captures()],
                'site_census': {'record': INPUT_LABELS['a5'], 'generated_at': self.a5['generated_at']},
                'models': {'evidence_checked': '2026-10-16',
                           'hf_metadata_retrieved_at': load('hf_model_metadata')['retrieved_at']},
                'inputs': self.public_inputs(),
            }),
        ])

    def vocab(self, entries: list[dict]) -> dict:
        v = {k: list(x) for k, x in VOCAB.items()}
        if not any(e.get('classified') for e in entries):
            v.pop('classified_by', None)
            return v
        for key in ('modality', 'paradigm', 'content_kind'):
            vals = set()
            for e in entries:
                c = e.get('classified')
                if c:
                    vals |= set(c[key] if isinstance(c[key], list) else [c[key]])
            v['classified_' + key] = sorted(vals)
        return v

    def public_source(self, src):
        """A step-evidence source as a served file may show it: a site file path, an input label, or a record hash."""
        if not src:
            return src
        path, _, sel = src.partition('#')
        if path.startswith('site/') and ' ' not in path:
            return src
        for k, p in INPUTS.items():
            if path == rel(p):
                return INPUT_LABELS[k] + (('#' + sel) if sel and not PARTICIPANT_ID.search(sel) else '')
        if path == rel(AUDIT):
            return 'classifier_audit'
        for d, label in DIR_LABELS.items():
            if path.startswith(d):
                return label
        if path.startswith('verified result') or path.startswith('a4:'):
            return src if path.startswith('a4:') else 'verification_results'
        h = self.a5_hashes.get(path)
        if h is None and (PROJECT / path).is_file():
            h = sha((PROJECT / path).read_bytes())
        return f'record:{h[:16]}' if h else 'record'

    def publicize(self, e: dict) -> dict:
        e = json.loads(json.dumps(e))
        for f in e.get('findings') or []:
            if 'sources' in f:
                f['sources'] = list(OrderedDict.fromkeys(self.public_source(x) for x in f['sources']))
        for st in (e.get('step_evidence') or {}).values():
            items = []
            for it in st.get('items', []) or []:
                src = it.get('source')
                if src is not None and (not isinstance(src, str) or ';' in src or ', a4:' in src):
                    raise ValueError(f'{e["id"]}: step evidence source must be one source, got {src!r}')
                it['source'] = self.public_source(src) if src else None
                # Two fields of one research file label as the same record: the item appears once per public source.
                if not any((x['item'], x['state'], x['source']) == (it['item'], it['state'], it['source']) for x in items):
                    items.append(it)
            if 'items' in st:
                st['items'] = items
        return e

    def public_inputs(self) -> list[dict]:
        out = []
        for k, p in INPUTS.items():
            out.append({'label': INPUT_LABELS[k], 'sha256': sha(self.raw[k]),
                        'served': rel(p).startswith('site/')})
        if self.audit is not None:
            out.append({'label': 'classifier_audit', 'sha256': sha(AUDIT.read_bytes()), 'served': False})
        if self.freeze:
            out.append({'label': 'site_register_rows', 'sha256': sha(SITE_ROWS.read_bytes()), 'served': False})
        for d, v in sorted(self.dir_files.items()):
            out.append({'label': DIR_LABELS[d], 'files': len(v), 'digest_sha256': sha(json.dumps(sorted(v)).encode()),
                        'served': False})
        return sorted(out, key=lambda x: x['label'])

    def documents(self):
        self.a5_hashes = {i['file']: i['sha256'] for i in self.a5['inputs']}
        ext_entries = [self.publicize(_clean(e)) for e in self.entries]
        ext = self.header('external')
        ext['counts'] = self.counts(ext_entries)
        ext['finding_codes'] = finding_schema()
        ext['vocab'] = self.vocab(ext_entries)
        ext['families'] = self.families
        ext['merges'] = sorted(
            [{'row': e['id'], 'into': e['merge_into'], 'ladder': e['ladder']} for e in ext_entries if e.get('merge_into')],
            key=lambda x: x['row'])
        ext['entries'] = ext_entries
        ext['site_model_aliases'] = {m['site']['method_slug']: [a for a in m['aliases'] if a['kind'] == 'weights_copy']
                                     for m in self.site_models if any(a['kind'] == 'weights_copy' for a in m['aliases'])}
        ext['provenance_paths'] = dict(sorted({**{INPUT_LABELS[k]: rel(p) for k, p in INPUTS.items()},
                                                **{v: k + '/' for k, v in DIR_LABELS.items()},
                                                'classifier_audit': rel(AUDIT),
                                                **({'site_register_rows': rel(SITE_ROWS)} if self.freeze else {})}.items()))
        excluded = [{'repo': x.split(':', 1)[1], 'rule': x.split(':', 1)[0]} for x in self.audit_applied]
        masked = [x for x in excluded if participant_like_repo(x['repo'])]
        ext['population_recheck'] = {
            'source': 'classifier_audit', 'status': 'pending_signoff', 'rules': {
                'simulated': 'signals that are only simulated leave the brain-signal group',
                'emg_rule': 'EMG-only uploads count only when recorded with or used as a neural interface',
                'undetermined': 'no evidence of brain signals beyond names; not counted'},
            'counts': dict(sorted(Counter(x['rule'] for x in excluded).items())),
            # Every excluded (repo, rule) pair, hashed: sha256 of the JSON of the sorted [repo, rule] pairs.
            'excluded_digest_sha256': sha(json.dumps(sorted([x['repo'], x['rule']] for x in excluded)).encode()),
            'excluded': [x for x in excluded if x not in masked],
            # Repo ids that look like participant ids are listed by count and rule only.
            'excluded_participant_like': dict(sorted(Counter(x['rule'] for x in masked).items()))}
        # The D3 comparison gate, row by row, for R2 / F3 review before the freeze.
        ext['comparison_review'] = sorted(self.comparison_review, key=lambda x: x['row'])
        # Provisional site file: rendered rows only (merge_into rows folded into their site rows).
        site_entries = []
        for e in ext_entries:
            if e.get('merge_into'):
                continue
            # Classifier fields stay in the research file until the owner approves their wave-1 display (plan
            # sections 1.1, 1.2 and 2.6: wave-1 HF rows show listing and detail metadata only).
            site_entries.append({k: v for k, v in e.items() if k != 'classified'})
        for cid, e in self.site_rows.items():
            e = dict(e)
            e['aliases'] = e['aliases'] + _dedupe(self.site_aliases.get(cid, []))
            e['source_groups'] = sorted({'site'} | self.site_groups.get(cid, set())
                                        | ({'eegdash'} if any(a['kind'] == 'eegdash_mirror' for a in e['aliases']) else set()))
            site_entries.append(self.publicize(_clean(e)))
        for e in self.site_models:
            m = dict(e)
            slug = (m.get('site') or {}).get('method_slug')
            ext_row = next((x for x in ext_entries if slug and x.get('merge_into') == slug), None)
            if ext_row:
                m['aliases'] = _dedupe(m['aliases'] + [a for a in ext_row['aliases'] if a['kind'] != 'name'])
                # At the freeze the site row's own terms, kind and signal stand (read from the site's records at the
                # freeze); the external row adds its weights' copies and its pretraining-exposure value.
                for k in (('exposure',) if self.freeze else ('terms_by_part', 'exposure', 'signal', 'model_kind')):
                    if k in ext_row:
                        m[k] = ext_row[k]
            m.pop('covered_by_external_row', None)
            site_entries.append(self.publicize(_clean(m)))
        order = {'hf': 0, 'eegdash': 1, 'site': 2, 'moabb': 3, 'corpus': 4, 'model': 5}
        site_entries.sort(key=lambda e: (e['ladder'] != 'dataset', order[e['group']], e['id']))
        site = self.header('frozen' if self.freeze else 'provisional')
        if not self.freeze:
            site['note'] = ('Provisional register for page builds. External rows are final for this release; site rows '
                            'are placeholders from the A5 census and are replaced at the freeze.')
        else:
            site['sources']['site_census']['site_rows'] = {'record': 'site_register_rows', 'freeze': D,
                                                           'sha256': sha(SITE_ROWS.read_bytes())}
        site['counts'] = self.counts(site_entries)
        site['finding_codes'] = finding_schema(self.site_hold_words)
        undeclared = [f'{e["id"]}:{f["params"]["reason_code"]}' for e in site_entries for f in e['findings']
                      if f['code'] == 'hold' and f['params']['reason_code'] not in site['finding_codes']['hold']['reason_codes']]
        if undeclared:
            raise ValueError(f'hold findings whose reason the file does not declare: {undeclared}')
        site['vocab'] = self.vocab(site_entries)
        site['families'] = self.families
        site['entries'] = site_entries
        return ext, site

    def csv_text(self, site: dict) -> str:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator='\n')
        w.writerow(['id', 'group', 'name', 'host', 'licence_as_stated', 'gated', 'level', 'gaps', 'status', 'page'])
        for e in site['entries']:
            if e['ladder'] != 'dataset':
                continue
            host = _host(e)
            gated = e['hf']['gated'] if e.get('hf') else ('yes' if e['access'] in ('gated', 'signed_agreement',
                                                                                  'request_based', 'registration')
                                                          else 'no')
            gaps = '; '.join(f'step {g["step"]}: {g["label_en"]}' for g in e['gaps'])
            w.writerow([e['id'], e['group'], e['name'], host, e['terms_as_stated'].get('value') or '',
                        'no' if gated is False else ('yes' if gated is True else gated), e['level'], gaps,
                        e['status'], (e.get('links') or {}).get('page') or (e.get('site') or {}).get('page')
                        or (e.get('links') or {}).get('case') or ''])
        return buf.getvalue()


# ----------------------------------------------------------------------------------------- series
def _series_key(name: str) -> tuple[str, bool]:
    """(stem, indexed) of one repo name. The stem ends before the first index token (a separate number, v<n>,
    u<n> or participant-style token), then loses one or two digits run onto its end; a name led by a test or
    testing token has that token as its stem. indexed: an index rule shortened the name."""
    t = TEST_STEM.match(name)
    if t:
        return t.group(1).lower(), True
    m = INDEX_TOKEN.search(name)
    key = name[:m.start()].rstrip('-_ .') if m else name
    if not key:                       # the name starts with its index (e.g. a date): no series stem
        return name.lower(), False
    key2 = TRAILING_INDEX.sub('', key).rstrip('-_ .')
    if key2 and len(key2) >= 3:
        key = key2
    return key.lower(), key.lower() != name.lower()


def series_keys(repos: list[str]) -> tuple[dict, dict]:
    """Collapse each uploader's series. Returns ({(uploader, stem): [repo, ...]}, {(uploader, stem): label}).

    1. Group by stem (_series_key). 2. Braindecode format variants ('x-raw', 'x-windows', 'x-eegwindows') of one
    stem form a group when the uploader has two or more. 3. A repo whose name extends an indexed stem
    ('stem_test', 'stem-new') joins that stem's group. 4. Groups with two or more members, or with a participant-like
    member, are families. 5. Nested families of one uploader fold into the shorter stem."""
    keyed = {}
    for i in repos:
        up, name = i.split('/', 1)
        keyed[i] = (up, *_series_key(name))
    fmt = defaultdict(list)
    for i, (up, key, indexed) in keyed.items():
        name = i.split('/', 1)[1]
        m = FORMAT_TOKEN.search(name)
        if m and m.start() > 0:
            fmt[(up, name[:m.start()].rstrip('-_ .').lower())].append(i)
    for (up, stem), members in fmt.items():
        if len(members) >= 2 and stem:
            for i in members:
                keyed[i] = (up, stem, True)
    groups = defaultdict(list)
    for i, (up, key, _) in keyed.items():
        groups[(up, key)].append(i)
    indexed_stems = {(up, key) for i, (up, key, indexed) in keyed.items() if indexed}
    for i, (up, key, indexed) in list(keyed.items()):
        if indexed or len(groups[(up, key)]) > 1:
            continue
        name = i.split('/', 1)[1].lower()
        hosts = sorted((k for k in indexed_stems if k[0] == up and k[1] != key
                        and re.match(re.escape(k[1]) + r'[-_ .]', name)), key=lambda k: -len(k[1]))
        if hosts:
            groups[(up, key)].remove(i)
            groups[hosts[0]].append(i)
    groups = {k: v for k, v in groups.items() if v}
    families = {k: sorted(v) for k, v in groups.items() if len(v) >= 2 or any(participant_like_repo(x) for x in v)}
    for (up, key) in sorted(families, key=lambda k: (k[0], len(k[1]))):
        if (up, key) not in families:
            continue
        for (up2, key2) in list(families):
            if up2 == up and key2 != key and re.match(re.escape(key) + r'[-_ .]', key2):
                families[(up, key)] = sorted(families[(up, key)] + families.pop((up2, key2)))
    labels_ = {}
    for (up, key), v in families.items():
        name = sorted(v)[0].split('/', 1)[1]
        labels_[(up, key)] = name[:len(key)] if name.lower().startswith(key) else key
    return families, labels_


# ----------------------------------------------------------------------------------------- helpers
def _token(s: str) -> str:
    t = re.sub(r'[^a-z0-9]+', '_', str(s).lower()).strip('_')
    return t or 'unclear'


def _int(x):
    try:
        return int(str(x).replace(',', ''))
    except (TypeError, ValueError):
        return None


def _num(x):
    try:
        f = float(str(x).replace(',', ''))
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


def _find_key(d, key):
    if isinstance(d, dict):
        if key in d and isinstance(d[key], dict) and 'checkpoint' in d[key]:
            return d[key]
        for v in d.values():
            r = _find_key(v, key)
            if r:
                return r
    elif isinstance(d, list):
        for v in d:
            r = _find_key(v, key)
            if r:
                return r
    return None


def _find_text(d, rx):
    m = re.search(rx, json.dumps(d))
    return m.group(0) if m else None


# Alias kinds from most to least specific: when one value appears twice in a row, the more specific kind stays.
ALIAS_KIND_RANK = {'official_weights': 0, 'weights_copy': 1, 'hf_repo': 2, 'eegdash_mirror': 3, 'moabb_loader': 4,
                   'accession': 5, 'doi': 6, 'name': 9}


def _dedupe(aliases):
    """One alias per case-folded value, in first-seen order, keeping the most specific kind (official_weights over
    weights_copy over hf_repo ... over name)."""
    best: dict[str, dict] = {}
    order: list[str] = []
    for a in aliases:
        k = a['value'].casefold()
        if k not in best:
            best[k] = a
            order.append(k)
        elif ALIAS_KIND_RANK.get(a['kind'], 8) < ALIAS_KIND_RANK.get(best[k]['kind'], 8):
            best[k] = a
    return [best[k] for k in order]


def _unique(items):
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


def _clean(e: dict) -> dict:
    e = {k: v for k, v in e.items() if not k.startswith('_')}
    e['aliases'] = _dedupe(e.get('aliases', []))
    return e


# The repository behind a record DOI, by the DOI's registrant prefix (the resolver doi.org is never a host). A prefix not
# listed here leaves the host blank rather than naming the resolver.
DOI_PREFIX_HOST = {
    '10.18112': 'OpenNeuro', '10.5281': 'Zenodo', '10.6084': 'Figshare', '10.25452': 'Figshare',
    '10.48324': 'DANDI', '10.82901': 'NEMAR', '10.13026': 'PhysioNet', '10.5524': 'GigaDB', '10.1184': 'KiltHub',
    '10.22002': 'CaltechDATA',
}
DOI_RESOLVERS = {'doi.org', 'dx.doi.org'}


def _host(e: dict) -> str:
    """The CSV's host column: the repository that holds the row's record (never the DOI resolver)."""
    if e['group'] in ('hf', 'eegdash'):
        return 'Hugging Face'
    url = (e.get('urls') or {}).get('record') or ''
    u = urllib.parse.urlparse(url)
    h = u.netloc.lower()
    if h in DOI_RESOLVERS:
        prefix = u.path.lstrip('/').split('/', 1)[0]
        if prefix in DOI_PREFIX_HOST:
            return DOI_PREFIX_HOST[prefix]
        for k, v in (('figshare', 'Figshare'), ('zenodo', 'Zenodo'), ('openneuro', 'OpenNeuro'), ('dandi', 'DANDI'),
                     ('nemar', 'NEMAR'), ('physionet', 'PhysioNet')):
            if k in u.path.lower():
                return v
        if e.get('moabb') and e['moabb'].get('repository'):
            return e['moabb']['repository']
        return ''
    for k, v in (('openneuro', 'OpenNeuro'), ('physionet', 'PhysioNet'), ('zenodo', 'Zenodo'), ('figshare', 'Figshare'),
                 ('huggingface', 'Hugging Face'), ('bnci', 'BNCI Horizon 2020'), ('dandi', 'DANDI'),
                 ('gigadb', 'GigaDB'), ('osf', 'OSF'), ('kilthub', 'KiltHub'), ('nemar', 'NEMAR'),
                 ('ieee-dataport', 'IEEE DataPort')):
        if k in h:
            return v
    if e.get('moabb'):
        return e['moabb'].get('repository') or (h or 'as listed by MOABB')
    return h or ''


def dump(doc) -> bytes:
    """Compact JSON (the register is large); one entry per line keeps diffs readable."""
    head = {k: v for k, v in doc.items() if k != 'entries'}
    body = json.dumps(head, ensure_ascii=False, separators=(',', ':'))[:-1]
    rows = ',\n'.join(json.dumps(e, ensure_ascii=False, separators=(',', ':')) for e in doc.get('entries', []))
    return (body + ',"entries":[\n' + rows + '\n]}\n').encode('utf-8')


def guard(doc: dict, label: str, research_paths_ok: tuple[str, ...] = ()) -> None:
    """Refuse private paths, participant-like ids, venue references and forbidden HF fields anywhere."""
    text = re.sub(r'https?://[^\s"]+', '', json.dumps(doc, ensure_ascii=False))   # public URLs such as .../home/seed/
    m = PRIVATE.search(text)
    if m:
        raise ValueError(f'{label}: private path or host name {m.group(0)!r}')
    rest = re.sub(r'https?://[^\s"]+', '', json.dumps({k: v for k, v in doc.items() if k not in research_paths_ok},
                                                       ensure_ascii=False))
    m = re.search(r'research/|iclr_|publication_review_', rest)
    if m:
        raise ValueError(f'{label}: research path {m.group(0)!r} outside provenance_paths')
    for s in _strings(doc):
        if PARTICIPANT_ID.search(s):
            raise ValueError(f'{label}: participant-like id in {s[:80]!r}')
        if REPO_ID.fullmatch(s) and participant_like_repo(s):
            raise ValueError(f'{label}: participant-like repo id {s[:80]!r}')
        if VENUE_REFS.search(s):
            raise ValueError(f'{label}: venue or submission reference in {s[:80]!r}')
    for k in _keys(doc):
        if k in ('downloads', 'likes', 'createdAt', 'lastModified', 'description', 'readme', 'one_line_en',
                 'one_line_zh', 'notes', 'register_wording_en', 'register_wording_zh', 'trendingScore'):
            raise ValueError(f'{label}: forbidden field {k!r}')


def _strings(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


def _keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from _keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from _keys(v)


def site_hold_words() -> set[str]:
    """The site hold reasons (register_findings.SITE_HOLD_REASONS) that the page module words in both languages: the
    keys of open-register.ts's ``holdReason`` table, read as text. The page refuses a declared reason it has no words
    for, so a site hold is declared and attached only once its words are there."""
    text = SITE_REGISTER_MODULE.read_text()
    m = re.search(r'\nconst holdReason: Record<string, T> = \{\n(.*?)\n\};', text, re.S)
    if not m:
        raise ValueError(f'{rel(SITE_REGISTER_MODULE)}: no holdReason table')
    worded = set()
    for key, body in re.findall(r'^  ([a-z][a-z0-9_]*): (\{.*?\}),?$', m.group(1), re.S | re.M):
        if re.search(r"\ben: '[^']+'", body) and re.search(r"\bzh: '[^']+'", body):
            worded.add(key)
    return worded & set(SITE_HOLD_REASONS)


def refresh_site_rows(check: bool) -> None:
    """Run export-site-register-rows.mjs: the site rows re-read against the live site at the freeze."""
    import subprocess
    cmd = ['node', str(SITE_ROWS_SCRIPT)] + (['--check'] if check else [])
    r = subprocess.run(cmd, cwd=PROJECT / 'site', capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise SystemExit(f'export-site-register-rows.mjs failed ({r.returncode})')


def release_manifest(b: 'Build', site: dict, ext_bytes: bytes, ids_bytes: bytes) -> dict:
    """The release manifest: the owner's decisions this file rests on, every input pinned by SHA-256, the freeze's
    re-read, what the file publishes and what it leaves out. Written before the served file, which carries its hash."""
    owner = load('owner')
    fz = b.frozen
    dec = owner['decisions']
    defaults = dec['defaults_stated_to_owner_and_not_objected']
    pins = OrderedDict()

    def pin(label, path: Path, note, data: bytes | None = None):
        pins[label] = {'path': rel(path), 'sha256': sha(data if data is not None else path.read_bytes()), 'note': note}
    pin('site_rows', SITE_ROWS, 'export-site-register-rows.mjs at the freeze: the site rows from entities.ts and the A5 '
        'census, every census value re-read in the live files')
    pin('external_rows', EXTERNAL_OUT, 'B8a\'s external rows (Hugging Face, EEGDash, MOABB, agreement corpora, models), '
        'rebuilt in this run from the inputs below', ext_bytes)
    pin('register_ids', IDS_PATH, 'the persisted opaque-id map; never served', ids_bytes)
    for path, note in ((SITE_ROWS_SCRIPT, 'the site-row exporter'), (Path(__file__).resolve(), 'this exporter'),
                       (Path(__file__).resolve().parent / 'register_findings.py', 'finding codes and the D3 gate'),
                       (Path(__file__).resolve().parent / 'register_ids.py', 'opaque ids'),
                       (SITE_REGISTER_MODULE, 'the page module; its holdReason table decides which site holds are declared')):
        pin(path.name, path, note)
    for k, path in INPUTS.items():
        pin(INPUT_LABELS[k] if '/' not in INPUT_LABELS[k] else k, path, 'served site file' if rel(path).startswith('site/')
            else 'research or review record (served by label and hash only)', b.raw[k])
    if b.audit is not None:
        pin('classifier_audit', AUDIT, 'the classifier audit (R2) whose population re-check the Hugging Face group applies')
    dirs = [{'label': DIR_LABELS[d], 'path': d + '/', 'files': len(v), 'digest_sha256': sha(json.dumps(sorted(v)).encode())}
            for d, v in sorted(b.dir_files.items())]
    site_row_inputs = [{'path': x['path'], 'sha256': x['sha256']} for x in fz['inputs']]
    rr = fz['reread']
    c = site['counts']
    return OrderedDict([
        ('release_id', RELEASE_ID), ('release_date', f'{D[:4]}-{D[4:6]}-{D[6:]}'), ('freeze_date', D),
        ('reviewer', 'publishing session, package B8b'),
        ('scope', 'Register wave 1 (owner decision D1): the dataset ladder and the model ladder in one file, '
                  f'open-register-{D}.json, and the dataset ladder flat in open-register-{D}.csv. B8b freezes this '
                  'site\'s rows from entities.ts and the A5 census re-read at the freeze, and merges the external rows '
                  'B8a built: MOABB record groups, Hugging Face repos and EEGDash mirrors that are this site\'s datasets '
                  'become aliases of its rows.'),
        ('approval', OrderedDict([
            ('D1', dec['D1']['answer']), ('D2', dec['D2']['answer']), ('D3', dec['D3']['answer']),
            ('D3_default_kept', dec['D3']['default_kept']), ('D4', defaults['D4']), ('D5', defaults['D5']),
            ('D11', owner['decisions']['D11_population']), ('D12', defaults['D12']), ('D13', dec['D13']['answer']),
            ('source', rel(INPUTS['owner']))])),
        ('sources', pins), ('source_directories', dirs), ('site_row_inputs', site_row_inputs),
        ('freeze', OrderedDict([
            ('census', fz['census']), ('values_rechecked', rr['values_checked']), ('fields_rechecked', rr['fields_present']),
            ('mismatches', rr['mismatches']), ('inputs_changed_since_census', [x['file'] for x in rr['drift']]),
            ('consent_record', rr['a3']), ('notes', fz['notes'])])),
        ('rules', OrderedDict([
            ('level', 'A row\'s level is the furthest step whose anchor item is on file (plan section 2.6, as both '
                      'register pages state it); items missing at or below the level are its gaps. Three rows traced '
                      'from their host records whose files were never opened (BNCI2014-004, PhysioNet eegmmidb, BI2013a) '
                      'stand at step 3 with files opened as a gap at step 2; the census had recommended their contiguous '
                      'step 1.'),
            ('share_above_chance', 'not computed (D12): a gap on every step-4 row where a chance level applies'),
            ('merges', 'external rows with merge_into are not rendered; their repo ids, MOABB loaders, DOIs and EEGDash '
                       'mirror ids become aliases of the site row, and their source group is added to it'),
            ('terms', 'a site dataset row states its dataset page\'s terms (entities.ts), or the census\'s licence item; a '
                      'model row states code, weights and data separately, each from the record it names'),
        ])),
        ('site_holds', OrderedDict([
            ('codes', dict(sorted(SITE_HOLD_REASONS.items()))),
            ('worded_on_site', sorted(b.site_hold_words)),
            ('attached', sorted(f'{e["id"]}:{f["params"]["reason_code"]}' for e in site['entries'] for f in e['findings']
                                if f['code'] == 'hold' and f['params']['reason_code'] in SITE_HOLD_REASONS)),
            ('withheld_until_worded', sorted(b.site_holds_withheld)),
            ('note', 'The holds this release opens on the eldBETA and ZuCo 2.0 rows are findings with a reason code, each '
                     'sourced to its hold in releases.ts and data-quality-update.json. A code is declared and attached '
                     f'only once {rel(SITE_REGISTER_MODULE)} words it in its holdReason table (the page refuses a '
                     'declared reason it cannot say); until then the row\'s status and its case link state the hold.'),
        ])),
        ('published', OrderedDict([
            ('json', f'open-register-{D}.json: both ladders, {c["rows"]["dataset"]} dataset rows and '
                     f'{c["rows"]["model"]} model rows'),
            ('csv', f'open-register-{D}.csv: the dataset ladder only, one row per entry, no findings'),
            ('counts', c['rows']),
        ])),
        ('population', OrderedDict([
            ('hf_classifier_in_scope', c['hf']['classifier_in_scope']), ('hf_in_scope_after_recheck', c['hf']['in_scope']),
            ('recheck_signoff', c['hf']['recheck_signoff']),
            ('note', 'D11: the Hugging Face group is the uploads the classifier marked in scope in the frozen snapshot. '
                     'The classifier audit\'s re-check (simulated signals, the EMG rule, no evidence beyond names) is '
                     'applied and its sign-off is pending; the page prints the in-scope count beside its basis.')])),
        ('notPublished', [
            'Classifier fields (modality, paradigm, content kind) and its one-line descriptions: research file only until '
            'the owner approves their display.',
            'Hugging Face card text, download counts, likes and modification or creation dates; demographics from the '
            'MOABB catalog.',
            'Comparison findings (matches_metadata_of, terms_differ) in the CSV and on the Hugging Face and Zenodo mirrors '
            '(D3 default).',
            'Verifier and census free text and notes; research paths (served by label and record hash only).',
            'Repo ids that look like participant ids (family rows only, counted, never listed); the uploads held back '
            'under D4 and the release copy rule.',
            'eldBETA\'s one-person score (D2); any ZuCo 2.0 run code or row value.',
        ]),
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fresh-ids', action='store_true', help='re-issue every id (before the first release only)')
    ap.add_argument('--check', action='store_true', help='build and compare with the files on disk; write nothing')
    ap.add_argument('--provisional', action='store_true', help="B8a's provisional site file (A5 placeholders)")
    ap.add_argument('--no-refresh', action='store_true', help='use the site rows file as it is (do not re-run the .mjs)')
    args = ap.parse_args(argv)
    freeze = not args.provisional
    if freeze and not args.no_refresh:
        refresh_site_rows(check=args.check)
    b = Build(fresh_ids=args.fresh_ids, freeze=freeze)
    b.run()
    ext, site = b.documents()
    caps = {x['capture_id'] for x in ext['sources']['access_terms']}
    raw = {x['id']: x for x in b.entries}
    for e in ext['entries']:
        r = raw[e['id']]
        validate(e['findings'], verdict=r.get('_verdict'), captures=caps, withheld=r.get('_withheld'),
                 plain=bool(r.get('_plain')))
    for e in site['entries']:
        if e['group'] == 'site' or e['kind'] == 'site_model':
            validate(e['findings'])
    ids_text = b.ids.dumps()
    ext['id_map_sha256'] = site['id_map_sha256'] = sha(ids_text.encode())
    guard(ext, 'external', research_paths_ok=('provenance_paths',))
    ext_bytes = dump(ext)
    outs = {EXTERNAL_OUT: ext_bytes, IDS_PATH: ids_text.encode()}
    if freeze:
        manifest = release_manifest(b, site, ext_bytes, ids_text.encode())
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=1) + '\n').encode()
        # A research file: it names research paths and quotes the owner's decisions; no private path or participant id.
        mtext = re.sub(r'https?://[^\s"]+', '', json.dumps(manifest, ensure_ascii=False))
        if PRIVATE.search(mtext) or any(PARTICIPANT_ID.search(x) for x in _strings(manifest)):
            raise ValueError('manifest: a private path or a participant-like id')
        outs[MANIFEST_OUT] = manifest_bytes
        prov = OrderedDict([('manifest', 'open-register-release-manifest'), ('manifest_sha256', sha(manifest_bytes)),
                            ('site_rows_sha256', sha(SITE_ROWS.read_bytes())), ('external_sha256', sha(ext_bytes))])
        site = OrderedDict([('schema_version', site['schema_version']), ('release_id', site['release_id']),
                            ('status', site['status']), ('generated_at', site['generated_at']), ('provenance', prov),
                            *[(k, v) for k, v in site.items() if k not in ('schema_version', 'release_id', 'status',
                                                                          'generated_at')]])
    guard(site, 'site')
    from export_snapshot import validate_public
    validate_public(site)
    validate_public(ext)
    csv_text = b.csv_text(site)
    site_bytes = dump(site)
    for p in SITE_OUTS:
        outs[p] = site_bytes
    outs[CSV_OUT] = csv_text.encode()
    if args.check:
        # The served JSON and the manifest carry the build time (and the manifest pins the external file, which does):
        # they are compared without it.
        def stable(p, data):
            if p in SITE_OUTS or p in (EXTERNAL_OUT, MANIFEST_OUT):
                return re.sub(rb'"generated_at":"[^"]*"|"(?:manifest_sha256|external_sha256|sha256)": ?"[0-9a-f]{64}"', b'',
                              data)
            return data
        bad = [str(p) for p, data in outs.items() if not p.exists() or stable(p, p.read_bytes()) != stable(p, data)]
        print('differs:', bad or 'none')
        return 1 if bad else 0
    for p, data in outs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    c = site['counts']
    print(f'{site["status"]}: external rows {len(ext["entries"])}; site file rows {len(site["entries"])} '
          f'(dataset {c["rows"]["dataset"]}, model {c["rows"]["model"]}); hf {b.hf_counts}; moabb {b.moabb_counts}')
    if freeze:
        print(f'site holds worded on the page: {sorted(b.site_hold_words) or "none"}; withheld until '
              f'{rel(SITE_REGISTER_MODULE)} words them: {b.site_holds_withheld or "none"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
