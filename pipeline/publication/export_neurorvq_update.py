"""Release NeuroRVQ's frozen-backbone probes on three tasks, aggregate-only, as one separate panel on the pilot studies page.

The released NeuroRVQ backbone stays frozen. It is restored strictly (263 trained tensors) with parameter-free branch
normalisation and mean-token pooling into 800 values, because the authors' affine inference wrapper fails a strict
restore with eight normalisation tensors missing. One fixed ridge head per fold reads it on three existing tasks, each
beside simple features of the same windows: EEGMAT rest against mental arithmetic (band power), ds003810 motor imagery
against rest (temporal means, and band power as a descriptive arm) and ds006593 P300 target against non-target
(temporal means). Scores are participant means; each task has one paired participant-bootstrap difference. Each study's
release approval passes an internal aggregate handoff; the owner's decisions D14 and D19 of 2026-10-28 publish the three
as one uncounted panel. mvp.json, pilot-studies-update.json, neurolm-eegmat-update.json, eegpt-core-update.json and
foundation-models-update.json keep their bytes.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- the scores, differences and intervals from each study's independent audit receipt, only if the study's release
  approval and interpretation review bind those bytes, the approval's status is the internal aggregate pass, the
  configuration and protocol the reviews name are the pinned ones, and the values round to the figures the study handoff
  and the consolidated handoff print;
- the cohort, split, input-chain and dimension facts from the frozen protocols, the input queues and the core matrix's
  released tracks;
- the restore counts from the strict-load acceptance; the checkpoint, revisions and paper from the loader and exposure
  contract, the Hugging Face and GitHub listings and the download record;
- the licences from the licence files of both repositories at the pinned revisions; the datasets' rights from their
  released core-matrix records;
- the exposure facts from the loader and exposure contract; the protocols not run from the open-items ledger;
- each caveat only where the handoffs, interpretation reviews, protocols, website-queue rows or contract state it, by
  phrase: among them the input scale (NeuroRVQ's pretraining amplitude and reference are not established, every chain
  feeds microvolts as an adaptation, and no score reproduces the published pipeline), which the sources require for all
  three tasks although the plan's units bullet names only motor imagery and P300;
- each audit boundary only as the study audit states it: the EEGMAT audit program, pinned beside its receipt, reads
  both arms' values from the producer's sealed files and re-extracts neither.
The research records carry private storage paths, so they are pinned and checked, never published.

What this export refuses:
- per-person, per-fold and per-window values, fold assignments, labels, extracted values, heads, predictions, the
  above-50% participant counts, bound-file lists, timings, budgets and memory, by key and by fragment, and the measured
  compute by value; private paths, user, host and volume names (read at run time from the pinned records that carry
  them, never spelled here);
- a score or interval other than the audited one, an interval that does not hold its estimate, a figure of a core-matrix
  row or of the NeuroLM panel, a resolved exposure, and another licence than the licence files state;
- a version label, an update marker or a month used as a label in the text, the commenter's figure, any ICLR 2027 or
  submission reference, the third-party conversion and its licence tag, and a claim these results do not support unless
  it is negated.

    python3 pipeline/publication/export_neurorvq_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'neurorvq-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'neurorvq-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/neurorvq-update.json', PROJECT / 'site/public/data/neurorvq-update.json')
RELEASE_ID = 'neurorvq-update-20261028'
SCHEMA = 'bci-report-neurorvq-update-v1'
RESEARCH_ROOT = 'research/autonomous_validation_20261026/'
APPROVED = 'PASS_INTERNAL_AGGREGATE_HANDOFF'
WRAPPER_FAIL = 'FAIL_MISSING_EIGHT_AFFINE_STATE_ENTRIES'
TASKS = ('eegmat', 'mi-rest', 'p300-target')
QUEUE_ROWS = {'eegmat': 7, 'mi-rest': 8, 'p300-target': 9}
METRICS = ('balanced_accuracy', 'macro_f1')

# The editorial table: the arms in the protocols' order, with the labels and roles the site uses and the key each audit
# receipt gives them; the caveats each block carries.
TASK = {
    'eegmat': {
        'protocol': 'arithmetic-rest', 'title': 'Arithmetic and rest', 'exposure_key': 'eegmat',
        'task': 'pre-task rest against mental arithmetic', 'classes': ['pre-task rest', 'mental arithmetic'],
        'arms': (('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
                 ('band-power', 'band power', 'matched comparator', 'spectral')),
        'caveats': ('variant', 'transfer', 'exposure', 'input-scale', 'input-eegmat', 'dimensions', 'eegmat-order',
                    'development-cohort', 'interval', 'separation', 'scope', 'rights'),
    },
    'mi-rest': {
        'protocol': 'mi-rest', 'title': 'Motor imagery and rest', 'exposure_key': 'ds003810',
        'task': 'dominant-hand motor imagery against rest', 'classes': ['motor imagery', 'rest'],
        'arms': (('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
                 ('temporal-means', 'temporal means', 'primary comparator', 'temporal'),
                 ('band-power', 'band power', 'descriptive comparator', 'spectral')),
        'caveats': ('variant', 'transfer', 'exposure', 'input-scale', 'input-cache', 'units', 'dimensions', 'interval',
                    'separation', 'scope', 'rights'),
    },
    'p300-target': {
        'protocol': 'p300-target', 'title': 'P300 target and non-target', 'exposure_key': 'ds006593',
        'task': 'target against non-target epochs', 'classes': ['non-target', 'target'],
        'arms': (('neurorvq', 'NeuroRVQ backbone', 'probe', 'neurorvq'),
                 ('temporal-means', 'temporal means', 'primary comparator', 'temporal')),
        'caveats': ('variant', 'transfer', 'exposure', 'input-scale', 'input-cache', 'units', 'dimensions',
                    'p300-windows', 'interval', 'separation', 'scope', 'rights'),
    },
}
# The core protocols NeuroRVQ was not run on: (protocol, open-items id, a phrase its gate states, the gate as shown).
NOT_RUN = (
    ('semantic-target', 'NeuroRVQ semantic ERP', 'calibration', 'the original calibration evidence is still missing'),
    ('beta-4ch', 'NeuroRVQ BETA4', 'Physical units absent', 'physical units and reference are unresolved'),
    ('beta-8ch', 'NeuroRVQ BETA8', 'PO5/PO6 unsupported',
     'physical units are unresolved, and PO5 and PO6 are missing from the model’s channel list'),
    ('idle', 'NeuroRVQ idle', 'Expected input directory absent',
     'its inputs are missing, and it needs its own calibration, threshold and split protocol'),
    ('sleep-scalp', 'NeuroRVQ sleep', 'Deferred', 'deferred to a separate study'),
)
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')          # the pilot-studies sentence, used once for the panel as the plan requires
BELOW_ZERO = 'the interval lies below zero; descriptive, from this one cohort'
LICENCE = 'CC BY-NC 4.0'
LICENCE_URL = 'https://creativecommons.org/licenses/by-nc/4.0/'
LICENCE_TITLE = 'Attribution-NonCommercial 4.0 International'
TOL = 1e-12
WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 8: 'eight', 10: 'ten'}

REFUSED_KEYS = PER_PERSON_KEYS | {
    'minimum', 'maximum', 'range', 'q1', 'q3', 'seconds', 'peak_rss_bytes', 'cpu_threads', 'batch_size', 'checks',
    'seal', 'seals', 'source_files', 'splits', 'bound_files', 'bound_file_count', 'source_hashes', 'source_cache_hashes',
    'start_unix', 'end_unix', 'terminal_budgets', 'raw_checks', 'labels_file', 'run_directory', 'output_root',
    'input_manifest', 'checkpoint_path'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_class', 'per_seed', 'subject', 'prediction', 'probabilit', 'threshold', 'feature',
                         'confusion', 'percentile', 'quantile', 'median', 'elapsed', 'timing', 'wall', 'rss', 'memory',
                         'device', 'platform', 'environment', 'private', 'path', 'host', 'folder', 'worker', '_lock', 'lock_',
                         'above_chance', 'bound_file', 'cpu_', '_cpu', 'unix', 'budget', 'allowance', 'deadline',
                         'oof', 'fifty', '055')
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\bSubject\d+|\.(?:npz|npy|edf|mat|md|py|vhdr)\b'
                        r'|(?<![\w-])(?:receipt|neural-receipt|release-approval|mi-release-approval'
                        r'|independent-result-audit|interpretation-review|mi-interpretation-review'
                        r'|strict-load-acceptance|frozen-config|mi-frozen-config|metadata_receipts)\.json',
                        re.IGNORECASE)
HASH = re.compile(r'\b[0-9a-f]{40}(?:[0-9a-f]{24})?\b')   # a revision or a SHA-256 may hold any digit pair
CONFIDENCE_TOKEN = re.compile(r'(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five',
                              re.IGNORECASE)
CONFIDENCE_VALUE = 11 / 20             # the commenter's figure as a fraction, a ratio so it is never spelled here
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d'
                           r'|\bgenerated \d', re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
SUBMISSIONS = re.compile(r'ICLR\s*2027|\bsubmission', re.IGNORECASE)
CLAIMS = re.compile(r'outperform|\bbeats?\b|\bimprov|superior|\bbetter\b|\badvantage|\bharm|\bunseen\b|never saw'
                    r'|zero-shot|\bcausal|\bclinical\b|\bmedical\b|\bonline\b|real-time|closed-loop|\bendorse'
                    r'|equivalen|significan|state[- ]of[- ]the[- ]art|\bbest\b|\bwinner|\branks?\b|\branked\b'
                    r'|\branking\b|leaderboard|official reproduction|fully (?:loaded|restored)', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none|nothing|outside)\b|n't\b", re.IGNORECASE)
HEDGE = re.compile(r',\s+not\s|\bnot\s+\w+(?:\s+\w+){0,4},\s+but\b', re.IGNORECASE)
REFUSED_TEXT = re.compile(r'eugenehp|apache|\bMIT\b|commenter|/discussions', re.IGNORECASE)
# The released dataset records, copied as they are (they carry review dates, versions and their own wording).
VERBATIM = re.compile(r'^\$\.rights\.datasets\.[\w-]+\.(?:name|source|version|license|licenseUrl|attribution'
                      r'|privacyReview|reviewedAt|reviewBasis|rightsScope)\b')
RIGHTS_FIELDS = ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt',
                 'reviewBasis', 'rightsScope')
TRIVIAL = {0.0, 0.5, 1.0, 2.0}


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif number(value):
        yield value


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


def stated(text, phrase, label):
    require(flat(phrase) in flat(text), f'{label}: the pinned record does not state {phrase!r}')


def g(x):
    """A number as the text prints it: 44.5 stays 44.5, 4.0 becomes 4."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def word(n):
    require(n in WORDS, f'no word for {n}')
    return WORDS[n]


def pct(v, places, sign=False, minus='−'):
    text = f'{100 * v:{"+" if sign else ""}.{places}f}'
    return text.replace('-', minus)


def input_refs(manifest):
    refs = []

    def walk(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v:
                refs.append(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(manifest)
    return refs


def read_pinned(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {Path(ref["path"]).name} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    text = raw.decode('utf-8')
    if ref['path'].endswith('.json') or ref['path'].endswith(('neurorvq_hf.txt', 'neurorvq_repo.txt')):
        return json.loads(text)
    return text


def bound_sha(bound, suffix, label):
    """The SHA-256 a private bound-file map gives the one entry whose path ends with this suffix."""
    hits = [v for k, v in bound.items() if k.endswith(suffix)]
    require(len(hits) == 1, f'{label}: no single bound entry ends with {suffix!r}')
    return hits[0]


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {'research': {}}
    for task in (*TASKS, 'backbone'):
        docs['research'][task] = {k: read_pinned(r, f'{task} {k}') for k, r in manifest['research'][task].items()}
    for group in ('model', 'handoff', 'published'):
        docs[group] = {k: read_pinned(r, k) for k, r in manifest[group].items() if isinstance(r, dict)}
    docs['owner'] = read_pinned(manifest['approval']['ownerDecisions'], 'owner decisions')
    docs['_bytes'] = {k: (PROJECT / manifest['model'][k]['path']).read_bytes() for k in ('codeLicence', 'weightsLicence')}
    return docs


def private_names(docs):
    """The user, project, host and volume names the private records use, read from them, never spelled in this file."""
    rs = docs['research']['eegmat']
    text = json.dumps(rs['protocol'])
    names = {n for pair in re.findall(r'/home/([^/\s"]+)/([^/\s"]+)/', text) for n in pair}
    names |= {n for pair in re.findall(r'/mnt/([^/\s"]+)/([^/\s"]+)/', text) for n in pair}
    for pattern in (r'tests passed on (\w+) after', r'system/power change, (\w+) access'):
        m = re.search(pattern, rs['handoff'])
        require(m is not None, f'the handoff no longer names its hosts ({pattern})')
        names.add(m.group(1))
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- the bindings
def bindings(docs, manifest):
    """Each study's approval passes and binds the audit, handoff and review this manifest pins; the owner publishes."""
    owner = docs['owner']
    require(owner['freeze_date'] == manifest['freeze_date'].replace('-', '') == RELEASE_ID.rsplit('-', 1)[1],
            'the freeze date is not the release id’s')
    stated(owner['decisions']['D14']['answer'], 'NeuroRVQ on EEGMAT, MI and P300 (aggregate scores only, CC BY-NC, '
                                                'no weights)', 'owner decision D14')
    stated(owner['decisions']['defaults_stated_to_owner_and_not_objected']['D19 (Q5)'],
           'NeuroRVQ: one uncounted panel on /topics/pilot-studies/ with EEGMAT, MI and P300 blocks, and figure-free '
           'pointers from the three protocol pages; no method page', 'owner decision D19')
    rm, rs = manifest['research'], docs['research']
    status = {}
    # EEGMAT
    e, er = rs['eegmat'], rm['eegmat']
    a = e['approval']
    require(a['status'] == APPROVED and a['handoff_sha256'] == er['handoff']['sha256']
            and a['numerical_audit_sha256'] == er['audit']['sha256']
            and a['interpretation_review_sha256'] == er['interpretationReview']['sha256']
            and a['config_sha256'] == er['config']['sha256'] == e['audit']['config_sha256']
            and a['strict_load_acceptance_sha256'] == rm['backbone']['strictLoad']['sha256'],
            'eegmat: the release approval binds other files')
    require(a['original_full_wrapper_gate'] == WRAPPER_FAIL and a['primary_superiority_established'] is False
            and a['participant_rows_exported'] is False and a['website_modified'] is False,
            'eegmat: the release approval changed')
    ir = e['interpretationReview']
    require(ir['decision'].startswith('PASS') and ir['independent_result_audit_sha256'] == er['audit']['sha256']
            and ir['scientific_changes_required'] is False, 'eegmat: the interpretation review did not pass this audit')
    require(bound_sha(e['config']['bound_files'], '/protocols/protocol.json', 'eegmat config') == er['protocol']['sha256']
            and bound_sha(e['config']['bound_files'], '/inputs/header-summary.json', 'eegmat config')
            == er['headerSummary']['sha256'], 'eegmat: the configuration binds another protocol or header summary')
    status['eegmat'] = a['status']
    # Motor imagery and P300
    for task, suffix in (('mi-rest', 'MI-only Prospective Protocol.json'),
                         ('p300-target', 'P300-only Prospective Protocol.json')):
        d, r = rs[task], rm[task]
        a, ir = d['approval'], d['interpretationReview']
        require(a['status'] == APPROVED and a['handoff_sha256'] == r['handoff']['sha256']
                and a['interpretation_review_sha256'] == r['interpretationReview']['sha256']
                and a['publication_authorized'] is False, f'{task}: the release approval binds other files')
        require(ir['decision'] == 'PASS' and ir['config_sha256'] == r['config']['sha256'] == d['audit']['config_sha256']
                and ir['protocol_sha256'] == r['protocol']['sha256'] and ir['mandatory_text_fixes'] == []
                and ir['publication_authorization'] is False, f'{task}: the interpretation review did not pass')
        bound = d['config']['bound_files']
        require(bound_sha(bound, suffix, task) == r['protocol']['sha256']
                and bound_sha(bound, suffix.replace('Prospective Protocol', 'Frozen Input Queue'), task)
                == r['queue']['sha256'], f'{task}: the configuration binds another protocol or queue')
        status[task] = a['status']
    mi, mir = rs['mi-rest'], rm['mi-rest']
    require(mi['approval']['numerical_receipt_sha256'] == mir['audit']['sha256']
            == mi['interpretationReview']['numerical_receipt_sha256']
            and mi['approval']['neural_supplement_receipt_sha256'] == mir['neuralAudit']['sha256']
            == mi['interpretationReview']['supplemental_neural_receipt_sha256']
            and mi['approval']['handoff'] == mir['handoff']['path'], 'mi-rest: the approval binds another receipt')
    p3, p3r = rs['p300-target'], rm['p300-target']
    require(p3['approval']['numerical_audit_sha256'] == p3r['audit']['sha256']
            == p3['interpretationReview']['independent_audit_receipt_sha256']
            and p3['interpretationReview']['queue_sha256'] == p3r['queue']['sha256'],
            'p300-target: the approval binds another receipt')
    # The website queue names the same three handoffs, rows 7 to 9.
    rows = docs['handoff']['queue']
    require(manifest['handoff']['queue']['rows'] == [QUEUE_ROWS[t] for t in TASKS], 'other queue rows')
    for task in TASKS:
        row = rows['rows'][QUEUE_ROWS[task]] if isinstance(rows, dict) and 'rows' in rows else None
        require(row is not None and row['source_sha256'] == rm[task]['handoff']['sha256']
                and row['canonical_handoff'] == rm[task]['handoff']['path'],
                f'{task}: the website queue names another handoff')
    return status


def task_queue(docs, task):
    entries = [p for p in docs['research'][task]['queue']['protocols'] if p['protocol_id'] == task]
    require(len(entries) == 1, f'{task}: the input queue has no single entry')
    return entries[0]


# ---------------------------------------------------------------------------- the values
def audited_values(docs, task):
    """Participant-mean scores and the paired difference, from the study's independent audit receipt."""
    au = docs['research'][task]['audit']
    keys = [k for *_, k in TASK[task]['arms']]
    if task == 'eegmat':
        require(au['status'] == 'PASS_INDEPENDENT_NUMERICAL_AND_PROVENANCE_AUDIT', 'eegmat: the audit did not pass')
        raw = {k: {'balanced_accuracy': v['mean_participant_balanced_accuracy'],
                   'macro_f1': v['mean_participant_macro_f1']} for k, v in au['methods'].items()}
        est, ci = au['mean_difference'], au['paired_person_bootstrap_percentile95']
    else:
        require(au['decision'] == 'PASS' and au['metrics_and_bootstrap_equality'] == 'exact',
                f'{task}: the audit did not pass')
        raw = {k: dict(v) for k, v in au['mean_participant_metrics'].items()}
        est, ci = au['primary_delta_mean'], au['paired_participant_CI95']
    require(sorted(raw) == sorted(keys), f'{task}: the audit has other arms')
    for k, v in raw.items():
        require(set(v) == set(METRICS) and all(number(x) and 0 <= x <= 1 for x in v.values()),
                f'{task} {k}: not a pair of proportions')
    lo, hi = ci
    require(all(number(x) for x in (est, lo, hi)) and -1 <= lo <= est <= hi <= 1,
            f'{task}: the interval does not hold its estimate')
    a, b = keys[0], keys[1]
    require(abs(raw[a]['balanced_accuracy'] - raw[b]['balanced_accuracy'] - est) <= TOL,
            f'{task}: the paired difference is not the difference of the arms')
    return raw, est, [lo, hi]


def printed(docs, task, raw, est, ci):
    """The audited values round to the figures the study handoff and the consolidated handoff print."""
    h = docs['research'][task]['handoff']
    keys = [k for *_, k in TASK[task]['arms']]
    f1_places = 5 if task == 'eegmat' else 6
    for k in keys:
        stated(h, f'{pct(raw[k]["balanced_accuracy"], 4)}%', f'{task} handoff {k} balanced accuracy')
        stated(h, f'{raw[k]["macro_f1"]:.{f1_places}f}', f'{task} handoff {k} macro-F1')
    if task == 'eegmat':
        stated(h, f'**{pct(est, 2, True)} percentage points**', 'eegmat handoff difference')
        stated(h, f'**[{pct(ci[0], 2, True)}, {pct(ci[1], 2, True)}]pp**', 'eegmat handoff interval')
    else:
        stated(h, f'**{pct(est, 4)} percentage points**', f'{task} handoff difference')
        stated(h, f'[{pct(ci[0], 4)}, {pct(ci[1], 4)}] percentage points', f'{task} handoff interval')
    c = docs['handoff']['consolidated']
    head = {'eegmat': '### C1.', 'mi-rest': '### C2.', 'p300-target': '### C3.'}[task]
    section = c.split(head, 1)[1].split('### ', 1)[0]
    for k in keys:
        stated(section, f'**{pct(raw[k]["balanced_accuracy"], 2)}%**', f'consolidated handoff {task} {k}')
    stated(section, f'**[{pct(ci[0], 2, task == "eegmat", "-")}, {pct(ci[1], 2, task == "eegmat", "-")}] pp**',
           f'consolidated handoff {task} interval')
    stated(section, pct(est, 2, task == 'eegmat', '-'), f'consolidated handoff {task} difference')


# ---------------------------------------------------------------------------- the model
def model_block(docs):
    rs, md = docs['research'], docs['model']
    sl, ct = rs['backbone']['strictLoad'], md['contract']
    require(sl['decision'] == 'PASS_STRICT_BACKBONE_LOAD_AND_SYNTHETIC_ACCEPTANCE'
            and sl['original_full_wrapper_gate'] == WRAPPER_FAIL, 'the strict-load acceptance changed')
    tensors, elements = sl['coverage_denominator_keys'], sl['coverage_denominator_elements']
    unused, total, total_el = sl['discarded_keys'], sl['actual_checkpoint_keys'], sl['actual_checkpoint_elements']
    require(sl['key_coverage'] == 1.0 and sl['element_coverage'] == 1.0 and tensors + unused == total
            and elements < total_el, 'the restore does not cover every backbone tensor')
    consts = sl['source_default_equivalence']['explicit_constants']
    norms = sorted({k.split('.')[0] for k in consts})
    require(norms == [f'fc_norm_{i}' for i in range(1, 5)] and len(consts) == 2 * len(norms)
            and all(v['value'] == (1.0 if k.endswith('.weight') else 0.0) for k, v in consts.items())
            and all(b['bitwise_equal'] for b in sl['source_default_equivalence']['batches']),
            'the missing normalisation entries are not the source defaults')
    widths = {v['shape'][0] for v in consts.values()}
    require(len(widths) == 1, 'the branches differ in width')
    width = widths.pop()
    dims = {b['output_shape'][1] for b in sl['synthetic']['batches']}
    require(dims == {len(norms) * width}, 'the pooled size is not four branches')
    dim = len(norms) * width
    eegmat_h = rs['eegmat']['handoff']
    m = re.search(r'four explicitly parameter-free `LayerNorm\((\d+),eps=([\d.e-]+)\)` layers', eegmat_h)
    require(m is not None and int(m.group(1)) == width, 'the handoff states another branch normalisation')
    eps = float(m.group(2))
    stated(eegmat_h, 'eight branch `fc_norm_1..4` affine entries are absent', 'eegmat handoff')
    stated(eegmat_h, '**The original complete inference wrapper did not pass strict restoration.**', 'eegmat handoff')
    for task in TASKS:
        stated(rs[task]['handoff'], '263', f'{task} handoff restore count')
    # The checkpoint and the revisions: contract, listings, download record, every configuration and the strict load.
    code_rev, weights_rev = ct['code_revision'], ct['weights_revision']
    enc = rs['eegmat']['protocol']['encoder']
    require(enc['contract_sha256'] == docs['_manifest']['model']['contract']['sha256'] and enc['code_revision'] == code_rev
            and enc['weights_revision'] == weights_rev and enc['variant'] == sl['variant']
            and enc['original_full_wrapper_gate'] == WRAPPER_FAIL, 'the EEGMAT protocol pins another contract or model')
    fm = [x for x in ct['artifacts'] if x['rfilename'] == ct['minimum_acquisition']['file']]
    require(len(fm) == 1, 'the contract lists no single foundation-model file')
    fm = fm[0]
    ck_sha, ck_bytes = fm['lfs']['sha256'], fm['size']
    require(ck_bytes == fm['lfs']['size'] == ct['minimum_acquisition']['bytes'] and sl['checkpoint_sha256'] == ck_sha
            and enc['weights_sha256'] == ck_sha,
            'the strict load restored another checkpoint')
    hf, gh, dl = md['weightsListing'], md['codeListing'], md['download']
    sib = {s['rfilename']: s for s in hf['siblings']}
    require(hf['sha'] == weights_rev and hf['private'] is False and hf['gated'] is False
            and sib[fm['rfilename']]['lfs']['sha256'] == ck_sha and sib[fm['rfilename']]['size'] == ck_bytes,
            'the Hugging Face listing names another revision or checkpoint')
    require(dl['sha256'] == ck_sha and dl['expected_bytes'] == ck_bytes and dl['version'] == weights_rev
            and dl['url'] == f'https://huggingface.co/{hf["id"]}/resolve/{weights_rev}/{fm["rfilename"]}',
            'the download record names another checkpoint')
    require(gh['private'] is False and gh['full_name'].lower() == gh['html_url'].split('github.com/', 1)[1].lower(),
            'the GitHub listing changed')
    for task in TASKS:
        cfg = rs[task]['config']
        require(bound_sha(cfg['bound_files'], '.pt', task) == ck_sha and cfg['variant'] == sl['variant'],
                f'{task}: the configuration binds another checkpoint or variant')
        require(bound_sha(cfg['bound_files'], '/review/strict-load-acceptance.json', task)
                == docs['_manifest']['research']['backbone']['strictLoad']['sha256'],
                f'{task}: another strict-load acceptance')
    for task in ('mi-rest', 'p300-target'):
        require(bound_sha(rs[task]['audit']['bound_files'], '.pt', task) == ck_sha,
                f'{task}: the audit bound another checkpoint')
        stated(rs[task]['handoff'], f'Checkpoint SHA-256: `{ck_sha}`' if task == 'p300-target' else ck_sha, task)
        stated(rs[task]['handoff'], weights_rev, task)
        stated(rs[task]['handoff'], code_rev, task)
    paper = re.fullmatch(r'https://arxiv\.org/html/(\d{4}\.\d{5})v\d+#A4', ct['paper'])
    require(paper is not None and f'arxiv:{paper.group(1)}' in hf['tags'], 'the contract names another paper')
    arxiv = paper.group(1)
    arch = ct['architecture']['constructor']
    require(arch['embed_dim'] == width and arch['use_as_encoder'] is True, 'another architecture')
    return {
        'id': 'neurorvq', 'name': 'NeuroRVQ', 'family': 'foundation',
        'arxiv_id': arxiv, 'paper': f'https://arxiv.org/abs/{arxiv}',
        'repository': gh['html_url'], 'source_revision': code_rev,
        'source_url': f'{gh["html_url"]}/tree/{code_rev}',
        'checkpoint': {'file': fm['rfilename'], 'repository': f'https://huggingface.co/{hf["id"]}',
                       'revision': weights_rev, 'sha256': ck_sha, 'bytes': ck_bytes,
                       'url': f'https://huggingface.co/{hf["id"]}/tree/{weights_rev}'},
        'variant': 'the released backbone with parameter-free branch normalisation and mean-token pooling',
        'restore': {'strict': True, 'trained_tensors': tensors, 'trained_elements': elements,
                    'checkpoint_tensors': total, 'checkpoint_elements': total_el, 'unused_checkpoint_tensors': unused,
                    'coverage': sl['key_coverage']},
        'authors_wrapper': {
            'strict_restore': False, 'missing_normalisation_tensors': len(consts),
            'text': (f'The authors’ affine inference wrapper fails a strict restore: {word(len(consts))} normalisation '
                     f'tensors it expects are missing from the checkpoint.')},
        'branch_normalisation': {'parameter_free': True, 'branches': len(norms), 'width': width, 'epsilon': eps,
                                 'source_default_scale': 1.0, 'source_default_shift': 0.0},
        'pooling': {'kind': 'the mean of each branch’s tokens, four branches joined', 'branches': len(norms),
                    'branch_width': width, 'dimension': dim},
        'architecture': {'depth': arch['depth'], 'heads': arch['num_heads'], 'width': arch['embed_dim']},
        'frozen': True, 'fine_tuning': False,
        'transfer': 'supervised: the frozen backbone’s pooled values feed a ridge head fitted on the other folds’ labels',
        'weights_distributed': False,
        'weights_note': 'no weights are distributed; the SHA-256 identifies the checkpoint used and grants nothing',
        'endorsement': 'none implied',
    }


def exposure_block(docs):
    ct = docs['model']['contract']
    pc = ct['pretraining_corpus']
    names = pc['datasets']
    require(pc['count'] == len(names) == pc['public_count'] + pc['proprietary_count'] and pc['proprietary_count'] == 1
            and sum('proprietary' in n.lower() for n in names) == 1, 'the pretraining list changed')
    require(not any(re.search(r'eegmat|mental arithmetic|ds003810|ds006593|peterson|cbci|celik', n, re.I)
                    for n in names), 'a dataset of this panel is in the published pretraining list; review the exposure')
    rows = {x['key']: x for x in ct['core_exposure']}
    out = []
    for task in TASKS:
        x = rows[TASK[task]['exposure_key']]
        require(TASK[task]['protocol'] in x['protocols'] and x['named_corpus_overlap'] == 'not_named_in_paper_Table6'
                and x['identity_overlap'] == 'unknown' and x['checkpoint_exposure'] == 'unknown',
                f'{task}: the exposure is no longer unknown')
        out.append({'task': task, 'named_in_list': False, 'status': 'unknown'})
    stated(pc['checkpoint_binding'], 'not accompanied by inspected per-checkpoint dataset/version/subject manifest',
           'contract')
    stated(docs['research']['eegmat']['handoff'], 'No verified per-checkpoint participant/corpus manifest exists.',
           'eegmat handoff')
    return {
        'status': 'unknown', 'status_vocabulary': ['exposed', 'not_exposed', 'unknown'],
        'checked_on': ct['checked_on'],
        'published_pretraining_list': {'corpora': pc['count'], 'public': pc['public_count'],
                                       'proprietary': pc['proprietary_count']},
        'per_checkpoint_list_published': False,
        'datasets': out,
    }


def probe_block(docs):
    p = docs['research']['eegmat']['protocol']['probe']
    require(p['implementation'] == 'sklearn StandardScaler then RidgeClassifier' and p['alpha'] == 100.0
            and p['solver'] == 'cholesky' and p['class_weight'] == 'balanced' and p['hyperparameter_search'] is False
            and p['early_stopping'] is False and p['scaler_fit'].startswith('training rows only'), 'another probe')
    for task, field in (('mi-rest', 'primary_all_tasks'), ('p300-target', 'primary')):
        stated(docs['research'][task]['protocol']['comparators'][field], 'alpha100', f'{task} probe')
        stated(docs['research'][task]['protocol']['comparators'][field], 'balanced', f'{task} probe')
        stated(docs['research'][task]['protocol']['comparators'][field], 'cholesky', f'{task} probe')
    stated(docs['research']['mi-rest']['protocol']['comparators']['prohibition'], 'No hyperparameter search', 'mi')
    stated(docs['research']['p300-target']['protocol']['comparators']['prohibition'], 'No hypersearch', 'p300')
    return {'scaler': 'StandardScaler fitted on the training participants’ windows only', 'head': 'RidgeClassifier',
            'alpha': int(p['alpha']), 'solver': p['solver'], 'class_weight': p['class_weight'],
            'hyperparameter_search': False, 'fine_tuning': False, 'sealed_before_scoring': True}


def interval_block(docs):
    e = docs['research']['eegmat']
    m = re.search(r'(\d+) ?pairedparticipant resamples withreplacement, PCG64default_rng\((\d+)\), '
                  r'percentilelinear([\d.]+)/([\d.]+)', e['protocol']['metrics']['bootstrap'])
    require(m is not None, 'the EEGMAT protocol states another bootstrap')
    resamples, seed, lo_p, hi_p = int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4))
    require(e['audit']['bootstrap_resamples'] == resamples and e['audit']['seed'] == seed, 'the audit drew otherwise')
    for task in ('mi-rest', 'p300-target'):
        stated(docs['research'][task]['protocol']['outcomes']['uncertainty'], f'{resamples} paired participant',
               f'{task} bootstrap')
        stated(docs['research'][task]['protocol']['outcomes']['uncertainty'], f'seed{seed}', f'{task} bootstrap')
    return {'kind': 'paired participant bootstrap', 'method': 'percentile interval', 'level': (hi_p - lo_p) / 100,
            'unit': 'participant', 'resamples': resamples, 'seed': seed, 'metric': 'balanced accuracy',
            'fixed_fits': True, 'arms': 'point estimates only'}


def chance_block(docs):
    e = docs['research']['eegmat']['protocol']
    require(len(e['input']['label_meaning']) == 2 and e['metrics']['chance'] == 0.5, 'EEGMAT is not binary')
    require(len(task_queue(docs, 'p300-target')['onset_label_evidence']['mapping']) == 2, 'P300 is not binary')
    stated(task_queue(docs, 'mi-rest')['onset_label_evidence'], 'motor imagery and OVTK_GDF_Tongue to rest', 'MI labels')
    return {'balanced_accuracy': e['metrics']['chance'], 'macro_f1': None}


# ---------------------------------------------------------------------------- the blocks
def cohort_and_chain(docs, task):
    rs = docs['research'][task]
    au = rs['audit']
    if task == 'eegmat':
        p, hs = rs['protocol']['input'], rs['headerSummary']
        ad = rs['protocol']['adapter']
        people, records, windows = p['people'], p['records'], p['windows']
        channels, window_s = len(p['channels']), p['window_seconds']
        src_hz, hz = p['native_rate_hz'], p['output_rate_hz']
        require(au['participants'] == people == hs['people'] and au['source_records'] == records == hs['records']
                and au['rows'] == windows == records * p['windows_per_record']
                and p['windows_per_record'] * window_s == p['seconds_per_record'] and hs['channels'] == channels
                and hs['sampling_hz'] == src_hz and hs['physical_units'] == 'uV', 'eegmat: the cohort counts disagree')
        fm = re.fullmatch(r'(\d+)-fold participant-disjoint out-of-fold', rs['protocol']['split']['type'])
        require(fm is not None, 'eegmat: another split')
        folds = int(fm.group(1))
        stated(rs['protocol']['split']['rule'], f'assigned fold i%{folds}', 'eegmat fold rule')
        stated(rs['protocol']['split']['rule'], 'Both recordings/all windows stay with subject', 'eegmat fold rule')
        bp = re.fullmatch(r'scipy\.signal\.butter\(N=(\d+),Wn=\[([\d.]+),([\d.]+)\],btype=bandpass,fs=(\d+)\), '
                          r'filtfilt default padding', ad['bandpass'])
        rsm = re.fullmatch(r'scipy\.signal\.resample\(x,(\d+),axis=-1\), FFT, default window', ad['resample'])
        require(bp is not None and int(bp.group(4)) == src_hz and rsm is not None
                and int(rsm.group(1)) == p['seconds_per_record'] * hz
                and ad['filter_record_extent'].startswith(f'First {p["seconds_per_record"] * src_hz} native samples')
                and ad['clip_uv'] == [-ad['clip_uv'][1], ad['clip_uv'][1]] and ad['demean'] is False
                and ad['rereference'] is False and ad['amplitude_divisor'] == 1 and ad['online_claim'] is False,
                'eegmat: another input chain')
        stated(rs['protocol']['units_reference']['reference'], 'linked-ear', 'eegmat reference')
        cohort = {'people': people, 'recordings': records, 'retained_seconds': p['seconds_per_record'],
                  'window_seconds': window_s, 'windows_per_recording': p['windows_per_record'], 'windows': windows,
                  'channels': channels, 'folds': folds}
        chain = {'kind': 'own chain', 'source_sampling_hz': src_hz, 'sampling_hz': hz,
                 'notch_hz': list(ad['notches_hz']), 'band_pass_hz': [float(bp.group(2)), float(bp.group(3))],
                 'filter_order': int(bp.group(1)), 'forward_backward': True, 'clip_microvolts': ad['clip_uv'][1],
                 'resampling': 'FFT over the retained minute of each recording',
                 'epoch_demean': False, 'rereference': False, 'amplitude_divisor': ad['amplitude_divisor'],
                 'reference': 'linked ears, as the source describes'}
        return cohort, chain
    q, pr = task_queue(docs, task), rs['protocol']
    n, c, samples = q['shape']
    src_hz, window_s = q['source_hz'], q['seconds']
    require(float(src_hz).is_integer() and float(window_s).is_integer() and samples == src_hz * window_s
            and au['rows'] == n and au['folds'] == q['splits']['fold_count'] == 5
            and q['splits']['rule'] == 'subject_disjoint_modulo_sorted_subjects' and len(q['channels']) == c
            and q['units'] == 'microvolts', f'{task}: the cohort counts disagree')
    stated(pr['splits'], 'Five folds, sorted unique exact prepared subject strings index modulo5', f'{task} fold rule')
    stated(pr['splits'], 'group-disjoint', f'{task} fold rule')
    up, down = q['adapter']['resample_poly']
    hz = q['adapter']['target_hz']
    require(src_hz * up / down == hz == 200, f'{task}: the resampling does not reach 200 Hz')
    stated(pr['adapter']['resampling'], f'resample_poly{" per window" if task == "mi-rest" else ""}', task)
    stated(pr['adapter']['resampling'], 'constant-zero', f'{task} padding')
    stated(pr['adapter']['amplitude'], 'Preserve calibrated microvolts; no /100, no new clipping', f'{task} amplitude')
    stated(pr['adapter']['filter_reference'], 'No new notch, bandpass, rereference or baseline correction', task)
    cohort = {'people': au['participants'], 'windows': n, 'window_seconds': int(window_s), 'channels': c, 'folds': 5}
    if task == 'mi-rest':
        stated(q['preprocessing']['amplitude'], 'per-channel epoch mean removed', 'mi demeaning')
        stated(pr['adapter']['amplitude'], 'Source MI mean removal is retained', 'mi demeaning')
        ref = 'left ear lobe, as the source states'
        stated(' '.join(au['caveats']), 'left ear lobe reference', 'mi reference')
        demean = True
    else:
        require('mean' not in json.dumps(q['preprocessing']).lower(), 'p300: the prepared cache is demeaned')
        stated(pr['reference_lineage'], 'Original VHDR physical reference blank/unknown', 'p300 reference')
        ref = 'unknown: the reference fields of the source headers are blank'
        demean = False
        stated(pr['prepared_cohort_limitations'], f'{au["participants"]}participants,60target+60nontarget each',
               'p300 balance')
        stated(rs['handoff'], 'with 60 target and 60 non-target rows per participant', 'p300 balance')
        require(au['participants'] * 120 == n, 'p300: the balance does not add up')
        cohort['balance'] = {'target': 60, 'non_target': 60, 'unit': 'epochs per person'}
    chain = {'kind': 'core prepared windows', 'source_sampling_hz': int(src_hz), 'sampling_hz': hz,
             'resample': {'up': up, 'down': down},
             'resampling': 'polyphase, per window, with zero padding at the edges',
             'epoch_demean': demean, 'further_filter': False, 'clip': False, 'rereference': False,
             'amplitude_divisor': 1, 'units': 'microvolts as the source cache stores them', 'reference': ref}
    return cohort, chain


def core_track_block(docs, task, cohort, chain):
    tr = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == TASK[task]['protocol'])
    require(tr['subjects'] == cohort['people']
            and tr['observations'] == f'{cohort["windows"]:,} epochs · {cohort["folds"]} participant-disjoint folds'
            and tr['exposure'] == f'{cohort["channels"]} channels · {cohort["window_seconds"]}-second windows',
            f'{task}: the core track has another cohort')
    same = False
    if task != 'eegmat':
        q, au = task_queue(docs, task), docs['research'][task]['audit']
        require(q['recorded_input_sha256']['protocol.json'] == q['protocol_sha256_live'] == tr['protocolSha']
                and au['source_cache_hashes'] == q['recorded_input_sha256'],
                f'{task}: the audited cache is not the core track’s prepared windows')
        same = True
        require(chain['source_sampling_hz'] != chain['sampling_hz'], f'{task}: no resampling')
    return {'page': f'/protocols/{TASK[task]["protocol"]}/', 'core_rows': False, 'same_people': True,
            'same_window_count': True, 'same_prepared_windows': same, 'own_resampling': True,
            'comparators_recomputed': True}


def arms_block(docs, task, cohort, raw, model):
    pr = docs['research'][task]['protocol']
    ch, dim, width = cohort['channels'], model['pooling']['dimension'], model['pooling']['branch_width']
    patches = cohort['window_seconds']
    tokens = ch * patches
    if task == 'eegmat':
        require(pr['encoder']['input_shape'] == ['B', ch, patches, width], 'eegmat: another encoder input')
        stated(pr['encoder']['feature'], f'mean each tensor over{tokens} tokens', 'eegmat pooling')
    else:
        require(task_queue(docs, task)['adapter']['task_tokens_C_times_A'] == tokens, f'{task}: another token count')
    per_token = (f'{ch} channels by {word(patches)} one-second patches' if patches > 1
                 else f'one one-second patch per channel')
    defs, dims = {}, {}
    defs['neurorvq'] = (f'the four {width}-value branch outputs of the frozen backbone, each averaged over the window’s '
                        f'{tokens} tokens ({per_token}) and joined into {dim} values')
    dims['neurorvq'] = dim
    if task == 'eegmat':
        c = pr['controls']
        bands = [list(b) for b in c['bands_hz']]
        require(c['welch']['window'] == 'hann' and c['welch']['nperseg'] == c['welch']['fs'] == 200
                and c['primary'].startswith(f'Same exact adapted {cohort["windows"]} windows, {ch * len(bands)}D log '
                                            f'Welch bandpower'), 'eegmat: another band-power arm')
        dims['band-power'] = ch * len(bands)
        defs['band-power'] = (f'{dims["band-power"]} log band powers: {ch} channels by {word(len(bands))} bands '
                              f'({", ".join(f"{g(a)}–{g(b)}" for a, b in bands[:-1])} and '
                              f'{g(bands[-1][0])}–{g(bands[-1][1])} Hz), Welch with one-second Hann windows at 200 Hz '
                              f'on the same adapted windows')
    else:
        comp = pr['comparators']
        text = comp['primary_all_tasks'] if task == 'mi-rest' else comp['primary']
        stated(text, 'nonoverlapping4-sample20ms means' if task == 'mi-rest' else 'Temporal20ms means', task)
        bins = cohort['window_seconds'] * 200 // 4
        dims['temporal-means'] = ch * bins
        stated(text, f'MI{dims["temporal-means"]}dim' if task == 'mi-rest'
               else f'{ch}channels x{bins}bins={dims["temporal-means"]}D', f'{task} temporal dimension')
        defs['temporal-means'] = (f'{dims["temporal-means"]:,} means of non-overlapping four-sample (20 ms) bins after '
                                  f'resampling to 200 Hz: {ch} channels by {bins} bins')
        if task == 'mi-rest':
            sp = comp['secondary_mi_only']
            bands = [[float(a), float(b)] for a, b in re.findall(r'\[(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)\)', sp)]
            require(len(bands) == 5 and 'Welch fs200,nperseg200' in sp, 'mi: another band-power arm')
            dims['band-power'] = ch * len(bands)
            stated(sp, f'{dims["band-power"]}dim', 'mi band-power dimension')
            defs['band-power'] = (f'{dims["band-power"]} log band powers: {ch} channels by {word(len(bands))} bands '
                                  f'({", ".join(f"{g(a)}–{g(b)}" for a, b in bands[:-1])} and '
                                  f'{g(bands[-1][0])}–{g(bands[-1][1])} Hz), Welch with one-second windows at 200 Hz')
    au = docs['research'][task]['audit']
    if task == 'p300-target':
        fv = au['feature_verification']
        require(fv['neurorvq']['dimensions'] == dim and fv['temporal']['dimensions'] == dims['temporal-means'],
                'p300: the audit checked other dimensions')
    if task == 'mi-rest':
        require(docs['research'][task]['neuralAudit']['feature_dimensions'] == dim, 'mi: another pooled size')
    out = []
    for aid, label, role, key in TASK[task]['arms']:
        out.append({'id': aid, 'label': label, 'role': role, 'dimension': dims[aid], 'definition': defs[aid],
                    'balanced_accuracy': raw[key]['balanced_accuracy'], 'macro_f1': raw[key]['macro_f1'],
                    'interval_95': None})
    return out


def difference_block(task, arms, est, ci):
    a, b = arms[0], arms[1]
    lo, hi = ci
    spans = lo <= 0 <= hi
    if task == 'eegmat':
        require(spans, 'eegmat: the interval no longer spans zero; the reading must be reviewed')
        reading = SPANS_ZERO
    else:
        require(hi < 0, f'{task}: the interval no longer lies below zero; the reading must be reviewed')
        reading = BELOW_ZERO
    return {'a': a['id'], 'b': b['id'], 'label': f'{a["label"]} minus {b["label"]}', 'role': 'primary',
            'metric': 'balanced_accuracy', 'difference': est, 'interval_95': [lo, hi], 'interval_includes_zero': spans,
            'reading': reading}


def audit_block(docs, manifest, task, cohort, arms, model):
    rs, rm = docs['research'][task], manifest['research'][task]
    au = rs['audit']
    n_arms, rows, dim = len(arms), cohort['windows'], model['pooling']['dimension']
    if task == 'eegmat':
        heads, outputs = au['refitted_heads'], au['OOF_predictions_exact']
        require(any('full neural re-extraction not repeated' in x for x in au['limitations']),
                'eegmat: the audit now re-extracts the backbone values; the boundary must be reviewed')
        stated(rs['handoff'], 'It did not repeat full raw hashing or neural feature extraction; those are supported by '
                              'the producer’s sealed checks', 'eegmat handoff')
        # Both arms' values come from the producer's sealed files: the receipt names the feature seal and both methods,
        # and its program (pinned beside it, and writing this receipt's limitation) loads each arm's sealed array after
        # checking every sealed artifact's hash, and extracts nothing.
        require(sorted(au['methods']) == sorted(k for *_, k in TASK['eegmat']['arms'])
                and 'features.seal.json' in au['source_hashes'], 'eegmat: the audit read other values')
        limit = 'feature alignment follows sealed independently rederived rows; full neural re-extraction not repeated'
        item = next((x for x in au['limitations'] if limit in x), None)
        require(item is not None, f'eegmat audit receipt: the pinned record does not state {limit!r}')
        prog = rs['auditProgram']
        stated(prog, f"'{item}'", 'eegmat audit program')
        stated(prog, "for f,h in s['files'].items():check(sha(root/f)==h,'sealed artifact '+f)", 'eegmat audit program')
        stated(prog, f"for method,width in [('neurorvq',{dim}),('spectral',{arms[1]['dimension']})]:",
               'eegmat audit program')
        stated(prog, "x=np.load(root/(method+'.npy'),allow_pickle=False)", 'eegmat audit program')
        require('strict_encoder' not in prog and 'import torch' not in prog, 'eegmat: the audit program extracts values')
        boundary = (f'The independent audit rebuilt every row, fold and label, refitted all {heads} heads and reproduced '
                    f'all {outputs:,} held-out predictions, the scores and the interval; it read both arms’ values from '
                    f'the producer’s sealed files and did not re-extract them.')
        block = {'status': 'pass', 'heads_refit': heads, 'held_out_outputs_reproduced': outputs,
                 'comparator_values_bitwise': None, 'backbone_values_reextracted': False}
    elif task == 'mi-rest':
        heads, outputs = au['heads_refit'], au['predictions_reproduced']
        na = rs['neuralAudit']
        require(au['baseline_feature_equality'] == 'bitwise' and au['neural_feature_reextraction'] is False
                and na['decision'] == 'PASS' and na['neural_feature_reextraction'] is True
                and na['rows_verified'] == rows and na['feature_dimensions'] == dim
                and na['elements_verified'] == rows * dim and na['mismatched_elements'] == 0
                and na['max_absolute_error'] == 0.0 and na['original_evidence_sha256']['receipt.json'] == rm['audit']['sha256']
                and na['config_sha256'] == rm['config']['sha256'], 'mi: the supplementary check did not pass')
        boundary = (f'The independent audit recomputed the temporal and band-power values bit for bit, refitted all '
                    f'{heads} heads and reproduced all {outputs:,} held-out predictions, the scores and the interval; a '
                    f'supplementary check re-extracted all {rows:,} × {dim} NeuroRVQ values exactly, reusing the '
                    f'accepted backbone loader.')
        block = {'status': 'pass', 'heads_refit': heads, 'held_out_outputs_reproduced': outputs,
                 'comparator_values_bitwise': True, 'backbone_values_reextracted': True}
    else:
        heads, outputs = au['heads_refit'], au['predictions_reproduced']
        fv = au['feature_verification']
        tdim = arms[1]['dimension']
        require(au['all_feature_equality'] == 'bitwise' and au['neural_feature_reextraction'] is True
                and all(fv[k]['exact_equal'] is True and fv[k]['max_absolute_error'] == 0.0 and fv[k]['rows'] == rows
                        for k in ('neurorvq', 'temporal')), 'p300: the audit did not re-extract every value')
        stated(rs['handoff'], 'A separate agent authored and ran the independent release audit without importing the '
                              'producer or its selfcheck', 'p300 handoff')
        boundary = (f'A separately written audit re-extracted all {rows:,} × {dim} NeuroRVQ values and {rows:,} × '
                    f'{tdim} temporal means exactly, reusing the accepted backbone loader, refitted all {heads} heads '
                    f'and reproduced all {outputs:,} held-out predictions, the scores and the interval.')
        block = {'status': 'pass', 'heads_refit': heads, 'held_out_outputs_reproduced': outputs,
                 'comparator_values_bitwise': True, 'backbone_values_reextracted': True}
    require(heads == n_arms * cohort['folds'] and outputs == rows * n_arms and au['participants'] == cohort['people'],
            f'{task}: the audit refitted another number of heads')
    block['sha256'] = rm['audit']['sha256']
    if task == 'mi-rest':
        block['supplement_sha256'] = rm['neuralAudit']['sha256']
    block['boundary'] = boundary
    return block


def protocols_not_run(docs):
    items = {x['id']: x for x in docs['handoff']['openItems']['remaining']}
    stated(docs['handoff']['consolidated'], 'NeuroRVQ semantic ERP: original calibration; BETA4: units/reference; BETA8: '
                                            'units plus unsupported PO5/PO6; idle: missing inputs and causal '
                                            'calibration/split protocol; sleep: deferred, unfrozen separate study.',
           'consolidated handoff')
    channels = docs['model']['contract']['input_contract']['channels']
    require('po5' not in channels and 'po6' not in channels, 'PO5 and PO6 are now in the model’s channel list')
    out = []
    for protocol, iid, phrase, gate in NOT_RUN:
        x = items.get(iid)
        require(x is not None and x['completion_status'] in ('NOT_COMPLETED', 'NOT_EXECUTED_PROSPECTIVE')
                and x['selected_in_current_round'] is False and phrase in x['current_gate'],
                f'{iid}: the open item changed')
        out.append({'protocol': protocol, 'gate': gate})
    return out


def rights_block(docs, model):
    md, b = docs['model'], docs['_bytes']
    code, weights = b['codeLicence'], b['weightsLicence']
    require(code == weights and code.decode('utf-8').splitlines()[0].strip() == LICENCE_TITLE,
            'the two licence files are not the same CC BY-NC 4.0 text')
    ct = md['contract']
    require(ct['code_license'] == 'CC BY-NC4.0' and ct['weights_license'].startswith('CC BY-NC4.0')
            and ct['licence_sha256'] == sha(code), 'the contract states another licence')
    rec = {r['file']: r for r in md['licenceReceipts']}
    gh_raw = model['repository'].replace('https://github.com/', 'https://raw.githubusercontent.com/')
    require(rec['LICENSE']['url'] == f'{gh_raw}/{model["source_revision"]}/LICENSE'
            and rec['hf_LICENSE.txt']['url'] == f'{model["checkpoint"]["repository"]}/raw/{model["checkpoint"]["revision"]}/LICENSE'
            and rec['LICENSE']['sha256'] == rec['hf_LICENSE.txt']['sha256'] == sha(code)
            and rec['LICENSE']['bytes'] == rec['hf_LICENSE.txt']['bytes'] == len(code)
            and rec['LICENSE']['checked'] == rec['hf_LICENSE.txt']['checked'], 'the licence receipts name other files')
    sib = {s['rfilename']: s for s in md['weightsListing']['siblings']}
    require(sib['LICENSE']['size'] == len(code), 'the Hugging Face listing has another licence file')
    stated(docs['research']['eegmat']['protocol']['exposure_and_rights']['code_and_weights'], 'CC BY-NC4.0', 'protocol')
    for task in TASKS:
        stated(docs['research'][task]['handoff'], 'CC BY-NC', f'{task} handoff')
    datasets = {}
    for task in TASKS:
        tr = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == TASK[task]['protocol'])
        require(tr['rightsScope'] == 'Personal noncommercial research; aggregate results only',
                f'{task}: the released record changed')
        record = {'name': tr['dataset']}
        record.update({k: tr[k] for k in RIGHTS_FIELDS})
        datasets[task] = record
    stated(docs['research']['eegmat']['protocol']['exposure_and_rights']['data'], 'EEGMAT1.0.0 ODC Attribution1.0',
           'eegmat rights')
    require(datasets['eegmat']['license'] == 'Open Data Commons Attribution License 1.0'
            and datasets['mi-rest']['license'] == datasets['p300-target']['license'] == 'CC0-1.0',
            'a dataset’s released licence is not the one the summary states')
    return {
        'code': {'licence': LICENCE, 'licence_url': LICENCE_URL, 'scope': 'NeuroRVQ’s source code at the pinned revision',
                 'url': f'{model["repository"]}/blob/{model["source_revision"]}/LICENSE',
                 'licence_title': LICENCE_TITLE, 'checked_on': rec['LICENSE']['checked']},
        'weights': {'licence': LICENCE, 'licence_url': LICENCE_URL,
                    'scope': 'the NeuroRVQ checkpoints in the Hugging Face repository at the pinned revision',
                    'url': f'{model["checkpoint"]["repository"]}/blob/{model["checkpoint"]["revision"]}/LICENSE',
                    'licence_title': LICENCE_TITLE, 'same_file_as_code': True,
                    'checked_on': rec['hf_LICENSE.txt']['checked'], 'weights_distributed': False},
        'datasets': datasets,
        'summary': ('NeuroRVQ code and weights: CC BY-NC 4.0, the licence file of both repositories; aggregate figures '
                    'only and no weights distributed. EEGMAT 1.0.0: Open Data Commons Attribution License 1.0 (Zyma et '
                    'al., 2019; PhysioNet). ds003810 and ds006593: CC0 1.0 (OpenNeuro).'),
    }


LIMITATIONS = (
    ('variant',
     'Every score uses the released NeuroRVQ backbone with parameter-free branch normalisation and mean-token pooling: '
     '{tensors} trained tensors restore strictly, the {branches} branch normalisations carry no parameters and take the '
     'source’s default scale 1 and shift 0, and each branch’s tokens are averaged and the {branches} {width}-value '
     'branches joined into {dim} values. The authors’ inference wrapper fails a strict restore, because {missing} '
     'normalisation tensors it expects are missing from the checkpoint.'),
    ('transfer',
     'Supervised transfer: the backbone stays frozen, and in each fold a standardiser and a ridge head (alpha {alpha}, '
     'balanced class weights) are fitted on the other participants’ windows. No score is zero-shot, and nothing was '
     'tuned.'),
    ('exposure',
     'Pretraining exposure is unknown. None of the three datasets is named in the paper’s list of {corpora} pretraining '
     'corpora, but the list includes a proprietary collection and no per-checkpoint list of corpora or participants is '
     'published, so the backbone may have seen these recordings.'),
    ('input-scale',
     'The checkpoint and the paper do not establish the amplitude scale or reference NeuroRVQ was pretrained on. Every '
     'chain here feeds microvolts as an adaptation: the EEGMAT chain follows the notch, band-pass and clip of the '
     'example preprocessing in NeuroRVQ’s code, and the motor-imagery and P300 chains leave all three out. No score here '
     'reproduces NeuroRVQ’s published pipeline, and none separates the representation from an input mismatch.'),
    ('input-eegmat',
     'EEGMAT has its own input chain: the first {retained} seconds of each recording, notches at {notches} Hz, a '
     '{order}-order {lo}–{hi} Hz band-pass run forward and backward, clipping at ±{clip} µV and resampling from {e_src} '
     'to {hz} Hz, with no demeaning or re-referencing. The band-power arm reads the same adapted windows.'),
    ('input-cache',
     'Motor imagery and P300 reuse the core matrix’s prepared windows, people and fold rule, resampled per window from '
     '{mi_src} and {p3_src} Hz to {hz} Hz with no further filter, clipping or rescaling; motor imagery keeps the core '
     'per-channel epoch demeaning. Their temporal and band-power arms were recomputed in this chain, apart from the '
     'matrix run: the motor-imagery band power differs from that protocol’s Spectral ridge row, and the P300 temporal '
     'means from that protocol’s Temporal ridge row.'),
    ('units',
     'Motor-imagery and P300 amplitudes are read as microvolts from the source cache: ds003810’s EDF unit fields are '
     'blank and its channel files declare microvolts, and ds006593’s headers give a {res} µV resolution with blank '
     'reference fields; the P300 cache’s original preparation from the raw files was not re-run. Neither reading is an '
     'independent instrument calibration.'),
    ('dimensions',
     'The arms differ in size under one fixed alpha: NeuroRVQ’s {dim} values against {bp_e} band powers on EEGMAT, '
     '{t_mi:,} temporal means and {bp_mi} band powers on motor imagery, and {t_p3} temporal means on P300. There is no '
     'random-initialisation arm, so the panel says nothing about what pretraining contributes.'),
    ('p300-windows',
     'The P300 sample is balanced at {target} target and {non_target} non-target epochs per person, where the source '
     'inquiries hold about one target in ten letters, and stimuli come about every {gap} s, so each one-second window '
     'holds later responses. The scores are for single epochs and do not measure speller accuracy.'),
    ('eegmat-order',
     'On EEGMAT, rest is recorded before arithmetic, so recording order moves with the label, and the published '
     'signals were already cleaned with ICA.'),
    ('development-cohort',
     'EEGMAT is a known development cohort, used across this site, so the EEGMAT block is not an untouched external '
     'confirmation.'),
    ('interval',
     'Each paired difference carries a descriptive 95% interval from {resamples:,} paired participant resamples, '
     'conditional on the fixed folds and fitted heads; each arm has a point estimate only.'),
    ('separation',
     'Each panel on this page has its own input chain and band-power arm, so these scores stay outside every '
     'leaderboard and are not ranked against the NeuroLM panel, the ten-second panel or the core matrix.'),
    ('scope',
     'Offline results for one frozen variant: the EEGMAT chain filters the retained first minute of each recording as '
     'one block before cutting it into windows, and nothing here measures cognitive workload, clinical use, online '
     'decoding or other uses of NeuroRVQ.'),
    ('rights',
     'NeuroRVQ’s code and weights are licensed CC BY-NC 4.0, the licence file of both repositories at the pinned '
     'revisions. Only aggregate figures are published here; no weights are distributed, and no endorsement by '
     'NeuroRVQ’s authors is implied.'),
)


def review_text(review):
    return ' '.join(t for _, t in strings(review))


def consolidated_section(docs, head):
    return docs['handoff']['consolidated'].split(head, 1)[1].split('### ', 1)[0]


def input_scale_stated(docs, b):
    """The input-scale caveat, as every source states it. Plan section 2.2 names only the MI and P300 source calibration;
    the handoffs, reviews, protocols, queue and contract keep NeuroRVQ's pretraining amplitude and reference open for all
    three tasks, and the sources win."""
    rs = docs['research']
    ic = docs['model']['contract']['input_contract']
    stated(ic['units'], 'Unresolved published absolute calibration', 'contract units')
    stated(ic['units'], 'proposed microvolts consistent with clip scale, not verified pretraining guarantee',
           'contract units')
    stated(ic['reference'], 'No verified universal re-reference', 'contract reference')
    stated(ic['filter'], 'Source example notch50/60/100 when below Nyquist,Q=f/2;third-order bandpass0.5 to '
                         'min(45,fs/2)-0.5Hz;filtfilt;clip±500', 'contract example preprocessing')
    ec, ad = b['eegmat']['input_chain'], rs['eegmat']['protocol']['adapter']
    require(ec['notch_hz'] == [50, 60, 100] and ad['notch_Q'] == 'f/2' and ec['filter_order'] == 3
            and ec['forward_backward'] is True
            and ec['band_pass_hz'] == [0.5, min(45, ec['source_sampling_hz'] / 2) - 0.5] and ec['clip_microvolts'] == 500,
            'the EEGMAT chain no longer follows the example preprocessing in NeuroRVQ’s code')
    eh = rs['eegmat']['handoff']
    stated(eh, 'Exact pretraining absolute units/reference are not established by the checkpoint.', 'eegmat handoff')
    stated(eh, 'Microvolt input is an explicit adaptation assumption grounded in the target EDF calibration, not proof '
               'of published-input reproduction.', 'eegmat handoff')
    stated(rs['eegmat']['protocol']['units_reference']['pretraining_units'],
           'This pilot explicitly assumes µV as an adaptation and cannot establish an exact published-input '
           'reproduction.', 'eegmat protocol')
    stated(rs['eegmat']['interpretationReview']['interpretation_consistency'], 'unknown pretraining units/exposure',
           'eegmat interpretation review')
    stated(consolidated_section(docs, '### C1.'),
           'Preserve unknown pretraining exposure, amplitude/reference compatibility', 'consolidated handoff C1')
    for task in ('mi-rest', 'p300-target'):
        c = b[task]['input_chain']
        require(c['further_filter'] is False and c['clip'] is False and c['units'].startswith('microvolts'),
                f'{task}: the chain now filters, clips or reads other units')
        stated(rs[task]['protocol']['claim_scope'], 'NOT official NeuroRVQ preprocessing reproduction',
               f'{task} claim scope')
    stated(rs['mi-rest']['handoff'], 'not an official NeuroRVQ reproduction', 'mi handoff')
    stated(review_text(rs['mi-rest']['interpretationReview']),
           'No claim of full wrapper restoration or official preprocessing reproduction', 'mi interpretation review')
    ph = rs['p300-target']['handoff']
    stated(ph, 'exact pretraining amplitude compatibility remain unknown', 'p300 handoff')
    stated(ph, 'That explicit event-window contract is not asserted to match the author\'s entire pretraining '
               'preprocessing.', 'p300 handoff')
    stated(ph, 'It does not isolate whether the limitation lies in the pretrained representation, pooling, source '
               'preprocessing or the fixed downstream head.', 'p300 handoff')
    stated(review_text(rs['p300-target']['interpretationReview']), 'unknownpretraining units+exposure',
           'p300 interpretation review')
    for task in TASKS:
        stated(docs['handoff']['queue']['rows'][QUEUE_ROWS[task]]['usable_level'],
               'retain negative outcomes, units/exposure and exact-cache limitations', f'queue row {QUEUE_ROWS[task]}')


def development_and_scope_stated(docs, b):
    """The development-cohort caveat (EEGMAT), the scope caveat (all three) and the matrix rows input-cache names."""
    rs = docs['research']
    eh, ep = rs['eegmat']['handoff'], rs['eegmat']['protocol']
    stated(eh, 'EEGMAT has been used previously in the project; this is not untouched external confirmation.',
           'eegmat handoff')
    stated(rs['eegmat']['interpretationReview']['interpretation_consistency'], 'Known development cohort',
           'eegmat interpretation review')
    stated(ep['scope'], 'complete known development cohort, not new blind cohort', 'eegmat protocol')
    stated(eh, 'Processing is record-local before2-second windowing and is not a causal online/deadline test.',
           'eegmat handoff')
    stated(eh, 'The result is not a causal mental-workload, diagnosis or clinical-efficacy claim.', 'eegmat handoff')
    require(ep['adapter']['online_claim'] is False
            and ep['adapter']['filter_record_extent'].endswith('independently per recording, before windowing'),
            'eegmat: the chain is no longer offline and record-local')
    # "filters the retained first minute of each recording as one block": the filter runs over the retained samples
    # only, the first 60 seconds of recordings that last longer.
    ec, cohort = b['eegmat']['input_chain'], b['eegmat']['cohort']
    require(cohort['retained_seconds'] == 60
            and ep['adapter']['filter_record_extent'] == (f'First {cohort["retained_seconds"] * ec["source_sampling_hz"]} '
                                                          f'native samples only, independently per recording, before '
                                                          f'windowing'),
            'eegmat: the filter no longer runs over the retained first minute of each recording')
    stated(eh, 'Actual supplied recordings span62–188 seconds; the analysis uses only the fixed first 60.',
           'eegmat handoff')
    stated(ep['input']['record_extent_note'], 'onlyfirst60sused', 'eegmat protocol')
    stated(rs['mi-rest']['handoff'], 'It does not justify an overall model ranking, clinical claim, online BCI '
                                     'performance claim', 'mi handoff')
    stated(rs['p300-target']['handoff'], 'No overall foundation-model ranking, clinical validation, online BCI claim',
           'p300 handoff')
    stated(consolidated_section(docs, '### C2.'), 'not all NeuroRVQ uses', 'consolidated handoff C2')
    rows = {t['id']: [r['name'] for r in t['rows']] for t in docs['published']['coreMatrix']['tracks']}
    arms = {t: [a['id'] for a in b[t]['arms']] for t in ('mi-rest', 'p300-target')}
    require('Spectral ridge' in rows['mi-rest'] and 'Temporal ridge' not in rows['mi-rest']
            and 'Temporal ridge' in rows['p300-target'] and 'band-power' in arms['mi-rest']
            and arms['p300-target'] == ['neurorvq', 'temporal-means'],
            'the matrix rows or arms the input-cache caveat names changed')


def cache_preparation_stated(docs):
    """The units caveat's clause that the P300 cache's original preparation from the raw files was not re-run."""
    p3 = docs['research']['p300-target']
    stated(p3['handoff'], 'original raw signal bodies were not reacquired and the historical MNE preprocessing runtime '
                          'was not independently reconstructed', 'p300 handoff')
    stated(' '.join(p3['audit']['caveats']), 'historical runtime not independently reconstructed', 'p300 audit receipt')
    stated(consolidated_section(docs, '### C3.'), 'Historical raw preparation and reference/calibration limits remain',
           'consolidated handoff C3')


def limitations_block(docs, model, blocks, probe, exposure, interval):
    """The caveats, each once, with every figure in them read from the blocks and records they describe."""
    b = {x['id']: x for x in blocks}
    arm = lambda t, a: next(x for x in b[t]['arms'] if x['id'] == a)['dimension']
    ec = b['eegmat']['input_chain']
    res = re.search(r'resolution of \*\*([\d.]+) µV\*\*', docs['research']['p300-target']['handoff'])
    gap = re.search(r'Stimuli are approximately ([\d.]+) seconds apart', docs['research']['p300-target']['handoff'])
    require(res is not None and gap is not None, 'the P300 handoff no longer states its resolution or stimulus gap')
    stated(task_queue(docs, 'p300-target')['onset_label_evidence']['readme_support'],
           'each inquiry has one target and nine nontarget letters', 'p300 prevalence')
    stated(docs['research']['mi-rest']['handoff'], 'The original EDF physical-dimension fields are blank', 'mi units')
    stated(docs['research']['mi-rest']['handoff'], 'explicitly declaring Microv', 'mi units')
    stated(docs['research']['p300-target']['handoff'], 'Physical per-channel reference fields are blank', 'p300 units')
    cache_preparation_stated(docs)
    stated(docs['research']['eegmat']['handoff'], 'Rest precedes arithmetic in source collection', 'eegmat order')
    stated(docs['research']['eegmat']['handoff'], 'already ICA-processed according to its documentation', 'eegmat ICA')
    stated(docs['research']['eegmat']['handoff'], 'no random-initialization attribution arm was tested', 'eegmat')
    stated(docs['research']['eegmat']['handoff'], 'not zero-shot classification', 'eegmat transfer')
    stated(docs['research']['eegmat']['handoff'], 'a proprietary training corpus is included', 'eegmat exposure')
    input_scale_stated(docs, b)
    development_and_scope_stated(docs, b)
    values = dict(
        tensors=model['restore']['trained_tensors'], branches=word(model['pooling']['branches']),
        width=model['pooling']['branch_width'], dim=model['pooling']['dimension'],
        missing=word(model['authors_wrapper']['missing_normalisation_tensors']), alpha=probe['alpha'],
        corpora=exposure['published_pretraining_list']['corpora'], retained=b['eegmat']['cohort']['retained_seconds'],
        notches=', '.join(map(g, ec['notch_hz'][:-1])) + f' and {g(ec["notch_hz"][-1])}',
        order={3: 'third'}[ec['filter_order']], lo=g(ec['band_pass_hz'][0]), hi=g(ec['band_pass_hz'][1]),
        clip=ec['clip_microvolts'], e_src=ec['source_sampling_hz'], hz=ec['sampling_hz'],
        mi_src=b['mi-rest']['input_chain']['source_sampling_hz'],
        p3_src=b['p300-target']['input_chain']['source_sampling_hz'], res=res.group(1),
        bp_e=arm('eegmat', 'band-power'), t_mi=arm('mi-rest', 'temporal-means'), bp_mi=arm('mi-rest', 'band-power'),
        t_p3=arm('p300-target', 'temporal-means'), target=b['p300-target']['cohort']['balance']['target'],
        non_target=b['p300-target']['cohort']['balance']['non_target'], gap=gap.group(1),
        resamples=interval['resamples'])
    require(b['mi-rest']['input_chain']['sampling_hz'] == b['p300-target']['input_chain']['sampling_hz'] == values['hz'],
            'the chains reach different rates')
    return [{'id': lid, 'text': text.format(**values)} for lid, text in LIMITATIONS]


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


def prose_check(payload, private):
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(not SOURCE_IDS.search(text), f'source file or participant identifier in export: {trail}')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}', text, re.IGNORECASE),
                    f'private host or volume name in export: {trail}')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        require(not CONFIDENCE_TOKEN.search(HASH.sub('', text)), f'{trail}: the commenter’s figure never appears')
        require(not SUBMISSIONS.search(text), f'{trail}: no ICLR 2027 or submission reference')
        require(not REFUSED_TEXT.search(text), f'{trail}: a third-party alias, another licence or the thread')
        if trail in ('$.schema_version', '$.release_id') or VERBATIM.match(trail):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):   # the release record is dated by design (/releases/, /data-use/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail.startswith(('$.provenance', '$.release_record')) or re.search(r'(?:url|source|paper\w*|repository)$',
                                                                               trail):
            continue
        require(not HEDGE.search(text), f'{trail}: a hedge (“, not …” or “not … , but”): {text!r}')
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if sentence.rstrip().endswith('?'):
                continue          # a question asserts nothing
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def licences_per_part(payload):
    """CC BY-NC 4.0 is NeuroRVQ's code and weights licence; no other licence is stated for either."""
    r = payload['rights']
    require(r['code']['licence'] == r['weights']['licence'] == LICENCE and r['weights']['weights_distributed'] is False
            and payload['model']['weights_distributed'] is False, 'the licences per part changed')
    for trail, text in strings(payload):
        if trail.startswith(('$.rights.code.', '$.rights.weights.')) or VERBATIM.match(trail):
            continue
        for sentence in re.split(r'(?<=[.;])\s+', text):
            if 'CC BY-NC' in sentence:
                require(re.search(r'\bcode\b|\bweights\b', sentence), f'{trail}: CC BY-NC not tied to NeuroRVQ: '
                                                                      f'{sentence!r}')


def collision_values(docs):
    """Every figure of the core-matrix rows of the three protocols and of the NeuroLM panel: none may reach this file."""
    out = set()
    for t in docs['published']['coreMatrix']['tracks']:
        if t['id'] in {TASK[x]['protocol'] for x in TASKS}:
            for r in t['rows']:
                for v in (r['y'], r['x'], *r['interval']):
                    out |= {v, v / 100}
    nl = docs['published']['neurolmEegmat']
    out |= {a[m] for a in nl['arms'] for m in METRICS}
    out |= {v for c in nl['paired_contrasts'] for m in METRICS for v in (c[m]['difference'], *c[m]['interval_95'])}
    return out - TRIVIAL


def withheld_values(docs):
    """Measured compute and the above-50% counts the sources hold, never published."""
    rs = docs['research']
    out = set()
    for task in TASKS:
        out |= {float(x) for x in re.findall(r'(\d+\.\d+)\s*(?:wall |CPU )?seconds', rs[task]['handoff'])}
    e = rs['eegmat']['audit']
    for m in e['methods'].values():
        out |= {m['above_chance_count'], m['above_chance_fraction']}
    out |= {e['elapsed_seconds'], *e['terminal_budgets'].values()}
    for doc in (rs['mi-rest']['audit'], rs['mi-rest']['neuralAudit'], rs['p300-target']['audit']):
        out |= {v for k, v in doc.items() if number(v) and re.search(r'seconds|RSS|unix', k)}
    cb = rs['backbone']['strictLoad']['cumulative_budget']
    out |= {cb['observed_wall_seconds'], cb['observed_CPU_seconds']}
    return out - TRIVIAL


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['holds'] == [], 'this release has no hold')
    require(not any(re.search(r'(?:^|/)(?:models|leaderboard)\.json$', r['path']) for r in input_refs(manifest)),
            'the legacy models.json and leaderboard.json are never read')
    docs = load(manifest)
    docs['_manifest'] = manifest
    status = bindings(docs, manifest)
    model = model_block(docs)
    exposure = exposure_block(docs)
    probe = probe_block(docs)
    interval = interval_block(docs)
    blocks = []
    for task in TASKS:
        raw, est, ci = audited_values(docs, task)
        printed(docs, task, raw, est, ci)
        cohort, chain = cohort_and_chain(docs, task)
        arms = arms_block(docs, task, cohort, raw, model)
        t = TASK[task]
        blocks.append({
            'id': task, 'protocol': t['protocol'], 'protocol_page': f'/protocols/{t["protocol"]}/', 'title': t['title'],
            'task': t['task'], 'classes': list(t['classes']),
            'dataset': next(x['dataset'] for x in docs['published']['coreMatrix']['tracks'] if x['id'] == t['protocol']),
            'cohort': cohort,
            'split': ('whole participants held out: participants sorted and assigned to a fold by index modulo five, so '
                      'no person is in training and test of the same fold'),
            'input_chain': chain,
            'core_track': core_track_block(docs, task, cohort, chain),
            'arms': arms,
            'paired_difference': difference_block(task, arms, est, ci),
            'fits': len(arms) * cohort['folds'],
            'audit': audit_block(docs, manifest, task, cohort, arms, model),
            'caveat_keys': list(t['caveats']),
        })
    limitations = limitations_block(docs, model, blocks, probe, exposure, interval)
    ids = [x['id'] for x in limitations]
    require(all(k in ids for blk in blocks for k in blk['caveat_keys']) and len(ids) == len(set(ids))
            and set(ids) == {k for blk in blocks for k in blk['caveat_keys']}, 'a caveat without a block or a block '
                                                                              'without its caveat')
    rights = rights_block(docs, model)
    for name, doc in docs['published'].items():
        if name != 'coreMatrix':
            require('neurorvq' not in json.dumps(doc).lower(), f'the released {name} file already names NeuroRVQ')
    require(not any('neurorvq' in r['name'].lower() for t in docs['published']['coreMatrix']['tracks'] for r in t['rows']),
            'NeuroRVQ is already a core row')
    rr, rm = manifest['releaseRecord'], manifest['research']
    people = {b['id']: b['cohort']['people'] for b in blocks}
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['freeze_date'],
        'status': 'aggregate_preview',
        'title': 'NeuroRVQ’s frozen backbone on three tasks',
        'question': ('Does NeuroRVQ’s frozen backbone, read by a fitted ridge head, separate the classes of three '
                     'existing tasks better than simple features of the same windows?'),
        'placement': {
            'page': '/topics/pilot-studies/', 'anchor': 'neurorvq', 'after': 'neurolm-eegmat',
            'pointers_from': [b['protocol_page'] for b in blocks], 'pointers_carry_figures': False,
            'counted_in_pilots': False, 'leaderboard': False, 'core_matrix_row': False,
            'foundation_encoder_table': False, 'method_page': False, 'new_dataset_count': 0, 'new_model_count': 0,
            'text': ('A separate panel on the pilot studies page, outside the pilot count and every leaderboard and '
                     'model ranking; the core matrix and the foundation-encoder table keep their rows, and the three '
                     'protocol pages link to the panel without figures.'),
        },
        'metric_units': ('balanced accuracy, macro-F1 and chance levels are proportions in [0,1], and paired differences '
                         'are differences of proportions: multiply by 100 for percent or percentage points; dimensions '
                         'and counts of people, recordings, windows, channels, folds, fits, tensors, elements, bytes and '
                         'resamples are whole numbers; null means not computed, never zero'),
        'scope': (f'NeuroRVQ’s released backbone stays frozen. On each task one ridge head (alpha {probe["alpha"]}) is '
                  f'fitted per fold on the other participants, for the backbone’s {model["pooling"]["dimension"]} pooled '
                  f'values and for simple features of the same windows: {people["eegmat"]} people on EEGMAT, '
                  f'{people["mi-rest"]} on motor imagery against rest and {people["p300-target"]} on P300 target '
                  f'against non-target, five participant-held-out folds each, nothing tuned. Scores are participant '
                  f'means; each task has one paired difference with a participant-bootstrap interval.'),
        'model': model,
        'pretraining_exposure': exposure,
        'probe': probe,
        'interval': interval,
        'chance_level': chance_block(docs),
        'blocks': blocks,
        'protocols_not_run': protocols_not_run(docs),
        'rights': rights,
        'limitations': limitations,
        'release_record': {
            'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
            'rights': rr['rights'], 'research_release': rr['researchRelease'],
            'research_release_status': status, 'binding': rr['binding'],
        },
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {t: rm[t]['audit']['sha256'] for t in TASKS},
            'release_approval_sha256': {t: rm[t]['approval']['sha256'] for t in TASKS},
            'handoff_sha256': {t: rm[t]['handoff']['sha256'] for t in TASKS},
            'protocol_sha256': {t: rm[t]['protocol']['sha256'] for t in TASKS},
            'released_files_unchanged': [Path(r['path']).name for r in manifest['published'].values()],
        },
    }
    require(people == {'eegmat': 36, 'mi-rest': 10, 'p300-target': 21} and probe['alpha'] == 100
            and all(b['cohort']['folds'] == 5 for b in blocks), 'the scope sentence no longer matches the cohorts')

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 4, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    licences_per_part(payload)
    validate_public(payload)
    published = set(numbers(payload))
    require(CONFIDENCE_VALUE not in published and 100 * CONFIDENCE_VALUE not in published,
            'the commenter’s figure is a value in the export')
    leaked = [v for v in withheld_values(docs) if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    crossed = [v for v in collision_values(docs) if v in published]
    require(not crossed, f'a core-matrix or NeuroLM figure reached the export: {crossed[:3]}')
    return payload


def inputs_available():
    """Whether the pinned inputs are on this machine. The research folders are local-only, so a clone checks the served
    file against the committed export audit's hash; only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_neurorvq_export
    return audit_neurorvq_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
