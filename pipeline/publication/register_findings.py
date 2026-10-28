"""Finding codes for the open register: codes and parameters only, never prose.

A finding is ``{"code": <code>, "params": {...}}``. The page renders it from an EN and a ZH template
kept with the page code (``site/src/data/open-register.ts``); every number inside a finding is a JSON
value here, so the page never retypes one. This module is the one list of codes, the shape of each
code's parameters, and the gates a finding must pass before the exporter may attach it to a row.

Rules the gates enforce (owner decisions D3 and D4, plan sections 2.6 and 2.7):
- ``matches_metadata_of`` and ``terms_differ`` attach only to a Hugging Face row whose independent
  verification verdict is ``confirmed``, whose source family has an A4 capture, *and* whose verifier
  result itself identifies that family as a source of the upload's files. The exporter keeps that
  identification row by row (``VERIFIED_SOURCES`` in export_open_register.py, each family tied to a
  verbatim phrase of the verifier's ``original_source``); a family that only A4's name match found
  yields nothing. An ``uncertain`` or ``refuted`` verdict yields nothing, and a family without a
  capture yields nothing.
- A row is withheld from every comparison when its verifier result says "do not state", or notes that
  the source is the uploader's own (same party), or when the row carries personal or identifying
  information (``WITHHELD_REASONS``).
- ``derived_from`` attaches only when the upload's own card names the source and the named source
  resolves to exactly one register row.
- No code describes personal or identifying information. A row where the classifier or a verifier
  noted such information is a plain row: its findings are listing metadata only (``PLAIN_ROW_CODES``),
  with no ``derived_from``, no comparison and no re-upload cap. ``validate(..., plain=True)`` checks it.
  No code carries card text, download counts or dates.
- Parameter values are identifiers, enumerated tokens, counts and short source labels. Free-text
  sentences are refused (a string parameter is at most ``MAX_PARAM_CHARS`` long and carries no
  sentence punctuation pattern).
"""
from __future__ import annotations

import re

MAX_PARAM_CHARS = 120

# code -> {param name: kind}. Kinds: 'row' (a register row id), 'rows', 'int', 'bool', 'token'
# (lower-case enumerated value), 'label' (a short name as a source states it), 'labels', 'capture'
# (an A4 capture id), 'tokens'.
CODES: dict[str, dict[str, str]] = {
    # Hugging Face listing metadata (step 1)
    'licence_tag_absent': {},
    'licence_tag_absent_members': {'n': 'int', 'of': 'int'},
    'gated': {'mode': 'token'},
    'gated_members': {'n': 'int', 'of': 'int'},
    'family': {'n': 'int', 'uploader': 'label', 'series': 'label'},
    # What the card itself declares
    'derived_from': {'row': 'row'},
    # Verified comparisons (D3): confirmed verdict and an A4 capture only
    'matches_metadata_of': {'row': 'row', 'source': 'token', 'fields': 'tokens', 'capture_id': 'capture'},
    # original: the captured source's access kind (signed_agreement, request_based, registration) or its licence
    # as a canonical id (cc-by-4.0, odc-by-1.0, ...); declared: what the upload declares, as declared_by says:
    # licence_tag = its Hugging Face licence tag(s) joined by '+', or 'none'; dataset_card = the licence its card
    # gives this source (a canonical id), used where the card's per-source licence differs from the repo tag.
    'terms_differ': {'original': 'token', 'declared': 'token', 'declared_by': 'token', 'capture_id': 'capture',
                     'source': 'token'},
    # Catalog and site facts
    # case: the data-quality page's case; catalog_trials and catalog_runs: the counts the MOABB catalog lists for the
    # source, which differ from what its files hold (Shin2022's case must carry them; the page prints them).
    'catalog_differs_from_files': {'case': 'token', 'catalog_trials': 'int', 'catalog_runs': 'int'},
    'version_clarification': {'current': 'label', 'earlier': 'label', 'recordings_source': 'int',
                              'recordings_evaluated': 'int'},
    'named_in_corpus': {'models': 'labels', 'release_resolved': 'bool'},
    'hold': {'reason_code': 'token'},
    'planned': {},
    'policy_note': {'source': 'token'},
    'merged_rows': {'n': 'int'},
}

# Optional parameters per code (everything else listed in CODES is required).
OPTIONAL = {
    'matches_metadata_of': {'row', 'source'},
    'terms_differ': {'source'},
    'version_clarification': set(),
    'catalog_differs_from_files': {'catalog_trials', 'catalog_runs'},
}

# Hold reasons: dataset ladder (MOABB catalog and site rows) and model ladder.
HOLD_REASONS = {
    # MOABB gap-matrix candidates (plan section 2.6 group 4)
    'released_ids_duplicated',          # Liu2024
    'targets_stored_with_outputs',      # Schrag2026Pediatric
    'deposits_differ',                  # Hinss2021
    'release_family_unchecked',         # Dreyer2023
    'one_offline_session',              # Alawieh2025
    # Model ladder
    'weights_licence_not_found',
    'code_licence_not_found',
    'no_released_checkpoint',
    'code_not_reachable',
    'not_human_scalp_eeg',
    'noncommercial_noderivs_weights',
    'acceptance_not_verified',
    'data_not_public',
    'no_release_found',                 # 20261028 refresh rows (D26): no official code or weights release found
}
# Holds on this site's own dataset rows (plan sections 2.6 and 3): a hold the releases log keeps open, row by row: the
# row, its reason code, and the hold's id in site/src/data/releases.ts and in the payload that opens it
# (data-quality-update.json for eldBETA and ZuCo 2.0, dataset-checks-update.json for the 20261028 dataset checks). One
# reason may hold several rows, each under its own hold id (one_person_score: eldBETA, Damm, NeBULA). Kim beta-range's
# hold replaces the MOABB catalog row's onset_timing_unresolved, which leaves the vocabulary with that row. Their words
# live with the page (open-register.ts holdReason), so ``schema(site_holds=...)`` declares a code only once the page has
# words for it, and the exporter attaches a site hold only where its code is declared.
SITE_HOLDS: dict[str, tuple[str, str]] = {
    'r-site-zuco2': ('converted_run_timing', 'zuco2-converted-run-timing'),        # one converted run's timing
    'r-site-eldbeta': ('one_person_score', 'eldbeta-one-participant-score'),       # owner decision D2
    'r-site-kim2025-beta-range': ('amplitude_units_unresolved', 'kim-amplitude-dependent-models'),   # D14
    'r-site-damm-finger-imagery': ('one_person_score', 'damm-one-participant-score'),                # D16
    'r-site-nebula': ('one_person_score', 'nebula-one-participant-scores'),                          # D16
}
# The same table by reason code: {reason code: {row id: hold id}}.
SITE_HOLD_REASONS: dict[str, dict[str, str]] = {}
for _row, (_code, _hold) in SITE_HOLDS.items():
    SITE_HOLD_REASONS.setdefault(_code, {})[_row] = _hold
SITE_HOLD_REASONS = dict(sorted((k, dict(sorted(v.items()))) for k, v in SITE_HOLD_REASONS.items()))
del _row, _code, _hold

TOKEN = re.compile(r'^[a-z0-9][a-z0-9_.:+-]*$')
ROW = re.compile(r'^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|model-[a-z0-9-]+|site-[a-z0-9.-]+)$')
CAPTURE = re.compile(r'^a4:[a-z0-9-]+:[0-9a-f]{16}$')
SENTENCE = re.compile(r'[.!?]\s+[A-Z]|\b(?:the|and|was|were|is|are|this|that)\b.*\b(?:the|and|was|were|is|are)\b', re.I)
# Words that would turn a finding into a statement about a person.
PERSONAL = re.compile(r'personal|identif|participant[_ ]id|subject[_ ]id|\bfaces?\b|address|e-?mail|phone|birth',
                      re.I)
# Parameters drawn from this register's own vocabulary (checked against PERSONAL); source slugs and licence ids
# are names of external records and are checked by their own patterns only.
OWN_VOCAB_PARAMS = {'reason_code', 'fields', 'mode', 'case'}

# Fields a verified metadata comparison may name (matches_metadata_of.fields): what the verifier's identification
# rests on. file_names / archive_names / folder_names: names in the file list; byte_counts / file_count: sizes and
# counts in the file list; file_hashes: LFS sha256 equal to the source's published checksum; dataset_name: the repo
# name; label_names / split_names / column_names: label vocabulary, split names or table columns in the metadata;
# example_counts / participant_count / channel_count / sampling_rate: counts in the metadata; card_names_source: the
# card names the source; code_names_source: code the uploader published names the source.
METADATA_FIELDS = {'file_names', 'byte_counts', 'file_count', 'archive_names', 'dataset_name',
                   'participant_count', 'channel_count', 'sampling_rate', 'folder_names', 'card_names_source',
                   'label_names', 'split_names', 'example_counts', 'column_names', 'file_hashes',
                   'code_names_source'}
DECLARED_BY = {'licence_tag', 'dataset_card'}

# A plain row carries listing metadata only: no derived_from, no comparison (personal or identifying information).
PLAIN_ROW_CODES = {'licence_tag_absent', 'gated'}
# Why a confirmed verifier result yields no comparison finding on its row.
WITHHELD_REASONS = {'personal_info', 'do_not_state', 'same_party'}
COMPARISON_CODES = {'matches_metadata_of', 'terms_differ'}


class FindingError(ValueError):
    pass


def _check_param(code: str, name: str, kind: str, value) -> None:
    where = f'{code}.{name}'
    if kind == 'int':
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise FindingError(f'{where}: expected a non-negative int, got {value!r}')
    elif kind == 'bool':
        if not isinstance(value, bool):
            raise FindingError(f'{where}: expected a bool')
    elif kind == 'row':
        if not isinstance(value, str) or not ROW.match(value):
            raise FindingError(f'{where}: expected a register row id, got {value!r}')
    elif kind == 'capture':
        if not isinstance(value, str) or not CAPTURE.match(value):
            raise FindingError(f'{where}: expected an A4 capture id, got {value!r}')
    elif kind == 'token':
        if not isinstance(value, str) or not TOKEN.match(value) or len(value) > MAX_PARAM_CHARS:
            raise FindingError(f'{where}: expected an enumerated token, got {value!r}')
    elif kind == 'tokens':
        if not isinstance(value, list) or not value or not all(isinstance(v, str) and TOKEN.match(v) for v in value):
            raise FindingError(f'{where}: expected a non-empty token list')
    elif kind in ('label', 'labels'):
        values = value if kind == 'labels' else [value]
        if kind == 'labels' and (not isinstance(value, list) or not value):
            raise FindingError(f'{where}: expected a non-empty label list')
        for v in values:
            if not isinstance(v, str) or not v.strip() or len(v) > MAX_PARAM_CHARS:
                raise FindingError(f'{where}: expected a short label, got {v!r}')
            if SENTENCE.search(v):
                raise FindingError(f'{where}: a label may not be a sentence: {v!r}')
    else:
        raise FindingError(f'{where}: unknown parameter kind {kind!r}')


def finding(code: str, **params) -> dict:
    """Build and validate one finding."""
    if code not in CODES:
        raise FindingError(f'unknown finding code {code!r}')
    spec = CODES[code]
    optional = OPTIONAL.get(code, set())
    for name in params:
        if name not in spec:
            raise FindingError(f'{code}: unexpected parameter {name!r}')
    for name, kind in spec.items():
        if name not in params:
            if name in optional:
                continue
            raise FindingError(f'{code}: missing parameter {name!r}')
        _check_param(code, name, kind, params[name])
    if code == 'hold' and params['reason_code'] not in HOLD_REASONS and params['reason_code'] not in SITE_HOLD_REASONS:
        raise FindingError(f'hold: unknown reason code {params["reason_code"]!r}')
    if code == 'matches_metadata_of':
        if not set(params['fields']) <= METADATA_FIELDS:
            raise FindingError(f'matches_metadata_of: unknown fields {set(params["fields"]) - METADATA_FIELDS}')
        if 'row' not in params and 'source' not in params:
            raise FindingError('matches_metadata_of: needs a row or a source family')
    if code == 'gated' and params['mode'] not in ('manual', 'auto'):
        raise FindingError(f'gated: mode must be manual or auto, got {params["mode"]!r}')
    if code == 'catalog_differs_from_files' and ('catalog_trials' in params) != ('catalog_runs' in params):
        raise FindingError('catalog_differs_from_files: the catalog trials and runs come together')
    if code == 'terms_differ':
        if params['declared_by'] not in DECLARED_BY:
            raise FindingError(f'terms_differ: declared_by must be one of {sorted(DECLARED_BY)}')
        if params['original'] == params['declared']:
            raise FindingError('terms_differ: original and declared terms are the same')
    # Our own vocabulary (codes, tokens, reason codes) never names personal or identifying information.
    for name, kind in spec.items():
        if name in OWN_VOCAB_PARAMS and name in params:
            for s in (params[name] if isinstance(params[name], list) else [params[name]]):
                if PERSONAL.search(s):
                    raise FindingError(f'{code}: a finding may not describe personal or identifying information ({s!r})')
    if PERSONAL.search(code):
        raise FindingError(f'{code}: a finding may not describe personal or identifying information')
    return {'code': code, 'params': dict(sorted(params.items()))}


# Where a site row's finding comes from (the census's facts, re-read at the freeze): public source strings, as step
# evidence gives them (a served site file with a selector, an input label, or a record hash). Only on site rows.
SOURCE = re.compile(r'^(?:site/[\w./-]+(?:#.+)?|[a-z][a-z0-9_]*(?:#.+)?|record:[0-9a-f]{16})$')
SOURCED_CODES = {'version_clarification', 'policy_note', 'named_in_corpus', 'catalog_differs_from_files', 'hold'}


def check_sources(f: dict) -> None:
    """A finding's optional ``sources``: a non-empty list of distinct public source strings, on a code that takes them."""
    if 'sources' not in f:
        return
    src = f['sources']
    if f.get('code') not in SOURCED_CODES:
        raise FindingError(f'{f.get("code")}: this code carries no sources')
    if not isinstance(src, list) or not src or len(src) != len(set(src)):
        raise FindingError(f'{f.get("code")}: sources must be a non-empty list of distinct strings')
    for s in src:
        if not isinstance(s, str) or not SOURCE.match(s) or ';' in s:
            raise FindingError(f'{f.get("code")}: a source that is not one public source string: {s!r}')


def comparison_allowed(verdict: str | None, capture_id: str | None, withheld: str | None = None) -> bool:
    """D3: a comparison finding needs an independently confirmed verdict, an A4 capture, and no withheld reason."""
    if withheld is not None and withheld not in WITHHELD_REASONS:
        raise FindingError(f'unknown withheld reason {withheld!r}')
    return verdict == 'confirmed' and withheld is None and bool(capture_id) and bool(CAPTURE.match(capture_id))


def validate(findings: list[dict], *, verdict: str | None = None, captures: set[str] | None = None,
             withheld: str | None = None, plain: bool = False) -> None:
    """Re-validate a row's findings as stored, including the D3 gate against the row's verdict, the row's withheld
    reason, and (for a row with personal or identifying information) the plain-row rule."""
    seen = set()
    for f in findings:
        if set(f) - {'sources'} != {'code', 'params'}:
            raise FindingError(f'finding keys must be code and params (and sources): {sorted(f)}')
        check_sources(f)
        rebuilt = finding(f['code'], **f['params'])
        if rebuilt != {k: v for k, v in f.items() if k != 'sources'}:
            raise FindingError(f'finding not in canonical form: {f}')
        if plain and f['code'] not in PLAIN_ROW_CODES:
            raise FindingError(f'{f["code"]}: a plain row carries listing metadata only')
        if f['code'] in COMPARISON_CODES:
            cap = f['params'].get('capture_id')
            if not comparison_allowed(verdict, cap, withheld):
                raise FindingError(f'{f["code"]}: verdict {verdict!r}, capture {cap!r} or withheld reason '
                                   f'{withheld!r} does not allow a comparison')
            if captures is not None and cap not in captures:
                raise FindingError(f'{f["code"]}: capture {cap!r} is not an A4 capture on file')
        key = (f['code'], tuple(sorted((k, str(v)) for k, v in f['params'].items())))
        if key in seen:
            raise FindingError(f'duplicate finding {f}')
        seen.add(key)


def schema(site_holds: frozenset[str] | set[str] = frozenset()) -> dict:
    """The served ``finding_codes`` block: each code's parameters and their kinds (templates live in the page).
    ``site_holds``: the site hold reasons (SITE_HOLD_REASONS) the page has words for, declared beside HOLD_REASONS."""
    if set(site_holds) - set(SITE_HOLD_REASONS):
        raise FindingError(f'unknown site hold reasons {sorted(set(site_holds) - set(SITE_HOLD_REASONS))}')
    out = {}
    for code, spec in CODES.items():
        out[code] = {'params': {k: v for k, v in spec.items()},
                     'optional': sorted(OPTIONAL.get(code, set()))}
    out['hold']['reason_codes'] = sorted(HOLD_REASONS | set(site_holds))
    out['matches_metadata_of']['fields'] = sorted(METADATA_FIELDS)
    out['terms_differ']['declared_by'] = sorted(DECLARED_BY)
    return out
