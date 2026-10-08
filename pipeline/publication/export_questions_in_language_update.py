"""Release route 3 of the decision-research roadmap, questions in language, as aggregate-only JSON.

Can a question be put to an EEG model in language? One small question-conditioned head (FiLM over frozen features)
is asked each question three ways: by a question number (ID), by a label template (TPL) or by a natural-language
description (DESC). Seen questions in their training wording, rewordings of seen questions and questions the EEG
head was never trained on are three separate results, never pooled into one zero-shot number. Primary: SSVEP on BETA
(70 people; a plain spectrum, L0, and frozen CBraMod features, L1) and sleep on BOAS (100 people; frozen CBraMod
features), three seeds each, 35 pre-declared comparisons. Secondary, single-seed or on EESM19 and declared likely
inconclusive: EESM19, OpenBMI motor imagery, REVE-L features, a second text encoder, Chinese wordings, a negation
probe, extrapolation to a contiguous band and Wearable-102. The interface pattern comes from a vision paper (Yu & Yao,
2026); route 3 is not an integration with Jev and not a Jev model that reads EEG.

Its own publication boundary, as with every batch. The website input is the release candidate. Every
{source, value} block in it is re-resolved against the pinned file it names, nested blocks included; the wording
lists are bound by re-serialising them to the hash the aggregate, the stage-0 report and the protocol record. The
consolidated aggregate, the two audited aggregates, the protocol, the stage-0 report, the two canary declarations,
the BOAS scope extension (D11), the handoff, the reference check and the four independent audits are pinned by
SHA-256, opened and checked, never copied. Two files are written: the results, and the wording lists with the
held-out partition and the derangements (the site's own text, CC BY 4.0).

What this export refuses:
- per-person, per-night, per-recording and per-fold values, percentiles and medians (by key and fragment);
- the S10 per-frequency and interior-only breakdowns, computed at stage 3 and never independently audited (by key
  and by value);
- any value of a pre-run check — permutation canaries, fit check, shuffled-EEG scorer check, triviality canaries —
  for any dataset: each is published as pass or fail and as counts (by key and by value);
- a BOAS figure without its n, a BOAS cell of fewer than 20 people, demographics and recording dates;
- a flag its interval and the frozen margin do not give, a rule the flags do not give, a gate that is not its
  block's, an unseen sentence without "unseen by the EEG head, not by the text encoder", a figure the pinned handoff
  does not state, and a disclosure the pages must carry that the file does not;
- private paths and hosts, the private decision log's file name, an update date or a version label in the text, a
  citation of the vision paper other than "Yu & Yao, 2026", and a mention of Jev without its scope sentence.

    python3 pipeline/publication/export_questions_in_language_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261008'
MANIFEST = REVIEW / 'questions-in-language-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'questions-in-language-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/questions-in-language-update.json',
           PROJECT / 'site/public/data/questions-in-language-update.json')
WORDING_OUTPUTS = (PROJECT / 'site/src/data/questions-in-language-wordings.json',
                   PROJECT / 'site/public/data/questions-in-language-wordings.json')
RELEASE_ID = 'questions-in-language-update-20261008'
SCHEMA = 'bci-report-questions-in-language-update-v1'
WORDINGS_SCHEMA = 'bci-report-questions-in-language-wordings-v1'
ROUTE = 'questions-in-language'
RUN_ID = 'decision-route3-v1/20261007'
CANDIDATE_STATUS = 'pending user approval'    # the state the candidate was sealed in; the manifest is the approval
DELTA = 2.0 / 100                             # the 2-pp margin, as a difference of proportions (fixed at the freeze)
P3_RATIO = 1.25                               # P3: the head may leave at most 25% more remaining error than the read-off
LOG_P3 = math.log(P3_RATIO)
BOAS_MIN_PEOPLE = 20
PRIMARY_COUNT = 35
SECONDARY_ENTRY_COUNT = 105
UNSEEN = 'unseen by the EEG head, not by the text encoder'
VISUAL_JEV = 'Yu & Yao, 2026 · Visual Jev: Accurate and Efficient Decisions from Shared Visual Context'
JEV_SCOPE = ('“Jev-style” names an interface pattern: encode the signal once, then answer several explicit, typed '
             'questions about it. This is not an integration with Jev and not a Jev model that reads EEG.')
INDEPENDENCE = ('BCI Report is independent and not affiliated with the Jev authors; no contact with them and no '
                'endorsement by them is claimed.')

# The pinned files the candidate's {source, value} blocks name, and the manifest key that pins each.
PINNED = {
    'aggregate.json': ('aggregate',),
    'aggregate-primary.json': ('aggregatePrimary',),
    'aggregate-secondary.json': ('aggregateSecondary',),
    'protocol.json': ('protocol',),
    'stage0-report.json': ('stage0Report',),
    'audit-primary-conformance.json': ('independentAudits', 'primaryConformance'),
    'audit-primary-numeric.json': ('independentAudits', 'primaryNumeric'),
    'audit-secondary-conformance.json': ('independentAudits', 'secondaryConformance'),
    'audit-secondary-numeric.json': ('independentAudits', 'secondaryNumeric'),
}
TEXT_PINS = {'revision-4-canary.md': ('canaryDeclarations', 'revision4'),
             'revision-5-canary.md': ('canaryDeclarations', 'revision5'),
             'boas-scope-extension-route3.md': ('boasScopeExtension',)}
# Named in nested blocks only. The wording lists are re-serialised from the aggregate's copy and held to the hash it
# records; the private extract of the route sentences stays in the run root, and the S10 breakdowns are not opened:
# both are bound through the consolidated aggregate's hash.
LISTS = 'lists.json'
NOT_OPENED = {'primary-private-extract.json', 's10-breakdowns.json'}
# The one place the candidate's builder changed a copied value: it wrote the run machine's host name out of the
# compute block (which this export does not publish). Declared here, and nothing else may differ.
CANDIDATE_SCRUBS = {'$/compute': ('gpu_etiquette', 'trx50 is shared', 'the run machine is shared')}

# Entry types: which result they belong to (never pooled), and which flag rule applies.
KIND = {'P1': ('seen', 'pp'), 'P2': ('rewording', 'pp'), 'P3': ('unseen', 'log_r'), 'P4_cca': ('unseen', 'pp'),
        'P4_nn': ('unseen', 'pp_difference_only'), 'P4_num': ('unseen', 'pp_difference_only'),
        'P5': ('unseen', 'auroc_difference_only')}
PP, AUC, LOGR = 'difference of proportions', 'difference of AUROC', 'log R'
UNIT = {'pp': PP, 'pp_difference_only': PP, 'auroc_difference_only': AUC, 'log_r': LOGR}
AGAINST = {'difference: reference higher', 'difference: the read-off leaves less error'}
FOR = 'difference: language arm higher'
MET = {'equivalent within the margin', 'non-inferior'}
DIFFERENCE_ONLY = 'not applicable (difference only)'
DISPLAY_EDITS = {'W2a', 'W2b-minilm', 'W2b-zh', 'W2c'}
BLOCKS = ('P-ssvep-L0', 'P-ssvep-L1', 'P-sleep-L1')
ENTRY_PARTS = ('S1', 'S2', 'S3-sleep', 'S3-ssvep', 'S4-sleep-L1', 'S4-ssvep-L0', 'S4-ssvep-L1', 'S5-sleep-L1',
               'S5-ssvep-L0')
BOAS_PARTS = {'S3-sleep', 'S4-sleep-L1', 'S5-sleep-L1', 'S6', 'S13-sleep', 'flip-sleep-L1'}
S12_SENSORS = {'0': 'dry', '1': 'wet'}         # bound to the handoff's S12 table below

# Text edits, declared: each must apply at least once, and nothing else in the carried text is changed.
EDITS = (
    (re.compile(r'DECISIONS\.md (?=[A-Z][\w-]*\d)'), 'decision log ', 'the private decision log, named by entry'),
    (re.compile(r'DECISIONS\.md'), 'the decision log', 'the private decision log, named'),
    (re.compile(r' \(stage2/secondary-parts\)'), '', 'a run-root folder'),
    (re.compile(r' \(research/decision_route3_20261007/revision-[45]-canary\.md\)'), '',
     'the project path of a canary declaration, pinned in the manifest instead'),
)

# Per-person distributions, per-fold values, pre-run check values, compute and the S10 breakdowns. Refused by key
# and by fragment wherever they appear in either file.
REFUSED_KEYS = PER_PERSON_KEYS | {
    'p10', 'p50', 'p90', 'q1', 'q3', 'minimum', 'maximum', 'excluded_people', 'training_balanced_accuracy', 'mc_se',
    'expected_exact', 'by_fit', 'by_configuration', 'replicates_above_chance', 'replicates_below_chance',
    'single_head_excluding_nominal_chance', 'between_replicate_sd_metric', 'metric_mean', 'exact_chance_mean', 'D',
    'beta_by_cohort_and_frequency', 'per_union', 'record', 'record_sha256', 'value', 'age', 'sex', 'bmi',
    'pid', 'splits', 'compute', 'ledger', 'fits_by_block'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_fold', 'fold', 'per_night', 'per_recording',
                         'percentile', 'median', 'quantile', 'spread', 'participant_id', 'record_id', 'subject',
                         'prediction', 'probabilit', 'private', 'elapsed', 'seconds', 'gpu', 'wall', 'timing',
                         's10_breakdown', 'per_frequency', 'by_frequency', 'interior', 'pilot', 'cosine', 'nearest',
                         'discrepanc', 'demograph', 'night')
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|\b[\w.-]+:(?:~|/(?!/))|Gal4|'
                            r'trx50|RUN_ROOT|DECISIONS\.md|\.private\b|\.npz\b|\.npy\b|\bsub-\d+',
                            re.IGNORECASE)
# The date rule of 2026-10-08 (check-workbench's patterns): no update date and no internal version label.
_MONTH = '(?:January|February|March|April|May|June|July|August|September|October|November|December)'
_DAY, _ISO = rf'\d{{1,2}} {_MONTH}', r'20\d\d-\d\d-\d\d'
DATE_RULES = (
    ('an "updated" date', re.compile(rf'\b[Uu]pdated:? (?:on )?(?:20\d\d|{_DAY})|· [Uu]pdated\b|更新于|{_ISO} ?更新')),
    ('an "added" date', re.compile(rf'\b[Aa]dded:? (?:on )?(?:20\d\d|{_DAY})|新增于|{_ISO} ?新增')),
    ('a "since" date', re.compile(rf'\b[Ss]ince (?:{_ISO}|{_DAY})')),
    ('"held since"', re.compile(r'[Hh]eld since|起暂缓')),
    ('a "run on" date', re.compile(rf'\b(?:[Rr]un|[Rr]an|replayed) on (?:{_ISO}|{_DAY})')),
    ('"this update"', re.compile(r'\b[Tt]his update\b|本次更新|这次更新')),
    ('a "generated" date', re.compile(rf'\bgenerated:? (?:on )?(?:20\d\d|{_DAY})|生成于 ?20\d\d')),
    ('a version label', re.compile(r'(?<![\w.\/#-])v\d+(?![\w.]|-\d)|\brelease v\d|第[一二三四五六七八九十]+轮')),
)
IDENTIFIER_TRAILS = ('$.schema_version', '$.release_id', '$.generated_at')
TOL = 1e-12
REFERENCE_COUNTS = {}                         # the last build's re-resolution counts, for the export audit record


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def close(a, b, label, rel=1e-12, abs_tol=1e-15):
    require(number(a) and number(b) and math.isclose(a, b, rel_tol=rel, abs_tol=abs_tol),
            f'{label}: {a!r} does not equal {b!r}')


def ref_of(route, key):
    node = route
    for k in key:
        node = node[k]
    return node


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8'), digest


def interval(lo, hi, point, label, lo_bound=-math.inf, hi_bound=math.inf):
    require(number(lo) and number(hi) and number(point), f'{label}: a bound or point is not a finite number')
    require(lo <= point <= hi, f'{label}: the interval does not contain its point')
    require(lo_bound <= lo and hi <= hi_bound, f'{label}: the interval leaves the metric range')
    return [lo, hi]


def edit(text, used):
    """Apply the declared edits; record which ones applied."""
    for i, (pattern, replacement, _) in enumerate(EDITS):
        text, n = pattern.subn(replacement, text)
        if n:
            used.add(i)
    return text


def edited(value, used):
    if isinstance(value, str):
        return edit(value, used)
    if isinstance(value, list):
        return [edited(v, used) for v in value]
    if isinstance(value, dict):
        return {k: edited(v, used) for k, v in value.items()}
    return value


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
    elif isinstance(value, float):
        yield value


CONSTANT_KEYS = {'chance', 'floor', 'ceiling', 'threshold', 'level', 'delta_pp', 'p3_ratio', 'stored'}


def figure_numbers(value):
    """The figures of a file: every float but chance levels, gate bounds and the frozen constants."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k not in CONSTANT_KEYS:
                yield from figure_numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from figure_numbers(v)
    elif isinstance(value, float):
        yield value


def numerals(text):
    """The numerals of a text, identifiers such as S0b-6, EA-1, P3, S12, L1, a1 or A4 D-2 left out."""
    text = re.sub(r'\b(?:S0b-\d+|EA-\d+|[A-Z]{1,2}-?\d+[a-z]?|[a-z]\d|D-\d+|O-\d+|W\d[a-d]?)\b', ' ', text)
    return {n.replace(',', '') for n in re.findall(r'\d[\d,]*(?:\.\d+)?', text)}


# ---------------------------------------------------------------------------- re-resolution
def resolve(files, source):
    """A JSON pointer into one of the pinned files."""
    name, _, pointer = source.partition('#')
    require(name in files, f'a reference into an unpinned file: {source}')
    node = files[name]
    for tok in pointer.split('/')[1:] if pointer else []:
        tok = tok.replace('~1', '/').replace('~0', '~')
        if isinstance(node, list):
            require(tok.isdigit() and int(tok) < len(node), f'a reference that does not resolve: {source}')
            node = node[int(tok)]
        else:
            require(isinstance(node, dict) and tok in node, f'a reference that does not resolve: {source}')
            node = node[tok]
    return node


def same(value, source):
    """Equal, or for a dict a key subset of the source object, recursively; booleans are not numbers."""
    if isinstance(value, dict):
        return isinstance(source, dict) and all(k in source and same(v, source[k]) for k, v in value.items())
    if isinstance(value, list):
        return isinstance(source, list) and len(value) == len(source) and all(same(a, b) for a, b in zip(value, source))
    if isinstance(value, bool) or isinstance(source, bool):
        return value is source
    return value == source


def traced(node):
    """Whether a value holds a {source, value} block anywhere."""
    if isinstance(node, dict):
        if isinstance(node.get('source'), str) and '#' in node['source']:
            return True
        return any(traced(v) for v in node.values())
    if isinstance(node, list):
        return any(traced(v) for v in node)
    return False


def reresolve(candidate, files):
    """Every {source, value} block equals the pinned file's value at that pointer, nested blocks included. A block
    with a source and no value is an annotated copy: each of its plain fields that the source object has must equal
    it; the fields the aggregate added (dataset, label, status_label, boas) are counted."""
    seen = {'top': 0, 'nested': 0, 'bound_through_the_aggregate': 0, 'annotated_copies': 0, 'annotations': 0,
            'host_name_scrubbed': 0}

    def walk(node, trail, depth):
        if isinstance(node, dict):
            src = node.get('source')
            if isinstance(src, str) and '#' in src:
                name = src.partition('#')[0]
                if name in NOT_OPENED:
                    require(depth > 0, f'{trail}: a top-level reference into a file this export does not open')
                    seen['bound_through_the_aggregate'] += 1
                    return
                target = resolve(files, src)
                if trail in CANDIDATE_SCRUBS:
                    field, before, after = CANDIDATE_SCRUBS[trail]
                    require(target[field].startswith(before), f'{trail}: the declared scrub does not apply')
                    target = {**target, field: after + target[field][len(before):]}
                    seen['host_name_scrubbed'] += 1
                if 'value' in node:
                    require(same(node['value'], target), f'{trail}: the value differs from {src}')
                    seen['nested' if depth else 'top'] += 1
                    for k, v in node.items():
                        walk(v, f'{trail}/{k}', depth + (k == 'value'))
                    return
                seen['annotated_copies'] += 1
                for k, v in node.items():
                    if k == 'source':
                        continue
                    if k in target and not traced(v):
                        require(same(v, target[k]), f'{trail}/{k}: differs from {src}')
                    elif k not in target:
                        seen['annotations'] += 1
                    walk(v, f'{trail}/{k}', depth + 1)
                return
            for k, v in node.items():
                walk(v, f'{trail}/{k}', depth)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f'{trail}[{i}]', depth)
    walk(candidate, '$', 0)
    require(seen['host_name_scrubbed'] == len(CANDIDATE_SCRUBS), 'a declared scrub was not met')
    require(seen['top'] == candidate['references_resolved'], 'the candidate resolved another number of references')
    for finding in candidate['key_findings']:
        for ref in finding['refs']:
            resolve(files, 'aggregate.json#' + ref)
    return seen


def val(block, label):
    require(isinstance(block, dict) and 'source' in block and 'value' in block, f'{label}: not a traced block')
    return block['value']


def inner(block, label):
    """The value of a traced block whose value is itself a traced block (the aggregate citing its own source)."""
    v = val(block, label)
    while isinstance(v, dict) and 'source' in v and 'value' in v:
        v = v['value']
    return v


# ---------------------------------------------------------------------------- bindings
def bindings(route, candidate, files, texts, handoff):
    """The candidate, the aggregate, the audits and the handoff name what they were built from; each is pinned."""
    agg = files['aggregate.json']
    require(candidate['run_id'] == agg['run_id'] == RUN_ID == route['runId'] and candidate['route'] == agg['route']
            == ROUTE == route['id'], 'another run or route')
    require(candidate['status'] == CANDIDATE_STATUS and agg['status'] == CANDIDATE_STATUS,
            'the candidate is not in the state it was sealed in')
    require(candidate['sources_sha256'] == {'aggregate.json': route['aggregate']['sha256']},
            'the candidate names another aggregate')
    protocol_sha = route['protocol']['sha256']
    require(candidate['protocol_sha256'] == agg['protocol_sha256'] == protocol_sha, 'the candidate names another protocol')
    for name, key in {**PINNED, **TEXT_PINS}.items():
        if name == 'aggregate.json':
            continue
        require(agg['inputs_sha256'][name] == ref_of(route, key)['sha256'], f'the aggregate names another {name}')
    # The two audited aggregates carry no run id of their own: the audits that checked them name it (below).
    for name in ('stage0-report.json', 'protocol.json'):
        require(files[name]['run_id'] == RUN_ID, f'{name} names another run')
    require(files['aggregate-secondary.json']['protocol_sha256'] == protocol_sha,
            'the secondary aggregate names another protocol')
    # The four audits: each names the run, the protocol and the aggregate it checked, and the aggregate records it.
    a1, a2 = files['audit-primary-conformance.json'], files['audit-primary-numeric.json']
    a3, a4 = files['audit-secondary-conformance.json'], files['audit-secondary-numeric.json']
    for a in (a1, a2, a3, a4):
        require(a['run_id'] == RUN_ID, 'an audit names another run')
    primary_sha, secondary_sha = route['aggregatePrimary']['sha256'], route['aggregateSecondary']['sha256']
    require(a1['audited_objects_sha256']['protocol.json'] == a3['audited_objects_sha256']['protocol.json']
            == a2['inputs']['protocol.json'] == a4['inputs']['protocol.json'] == protocol_sha,
            'an audit checked another protocol')
    require(a1['audited_objects_sha256']['aggregate-primary.json'] == a2['inputs']['aggregate-primary.json']
            == primary_sha, 'a primary audit checked another aggregate')
    require(a3['audited_objects_sha256']['aggregate-secondary.json'] == a4['inputs']['aggregate-secondary.json']
            == secondary_sha, 'a secondary audit checked another aggregate')
    for name, key in PINNED.items():
        if name.startswith('audit-'):
            stem = name[:-len('.json')]
            require(agg['audit_status'][stem]['sha256'] == ref_of(route, key)['sha256'],
                    f'the aggregate records another {stem}')
            require(candidate['audits'][stem]['sha256'] == ref_of(route, key)['sha256'],
                    f'the candidate records another {stem}')
    # The handoff records every hash it hands over.
    for key in ('releaseCandidate', 'aggregate', 'aggregatePrimary', 'aggregateSecondary', 'protocol', 'stage0Report',
                'boasScopeExtension'):
        require(route[key]['sha256'] in handoff, f'the handoff does not record the {key} hash')
    for key in ('revision4', 'revision5'):
        require(route['canaryDeclarations'][key]['sha256'] in handoff, f'the handoff does not record {key}')
    for key, ref in route['independentAudits'].items():
        require(ref['sha256'] in handoff, f'the handoff does not record the {key} audit')
    # The stage-0 report and the protocol name the two canary declarations.
    s0, protocol = files['stage0-report.json'], files['protocol.json']
    require(s0['revision_4']['declaration_sha256'] == route['canaryDeclarations']['revision4']['sha256']
            and s0['revision_5']['declaration_sha256'] == route['canaryDeclarations']['revision5']['sha256'],
            'the stage-0 report names other canary declarations')
    require(protocol['status'] == 'frozen' and protocol['frozen_at'].startswith('2026-10-07T13:37'),
            'the protocol is not the one frozen on 2026-10-07 at 13:37 UTC')
    require('no further revision' in texts['revision-4-canary.md'], 'revision 4 does not say "no further revision"')
    require('no further revision' in texts['revision-5-canary.md'], 'revision 5 does not name what it overrides')
    # D11: the scope extension the aggregate quotes is the pinned one, and it carries the conditions.
    ext = agg['boas_publication']['scope_file']
    require(ext['sha256'] == route['boasScopeExtension']['sha256'] and ext['text'] == texts['boas-scope-extension-route3.md'],
            'the aggregate quotes another BOAS scope extension')
    for phrase in ('D11 批准扩展', 'at least 20 distinct people', 'pseudonymised in the public release',
                   'three gaps', "Bitbrain's headband"):
        require(phrase in texts['boas-scope-extension-route3.md'], f'the BOAS scope extension does not say {phrase!r}')
    return agg, protocol, s0


def wording_lists(agg, protocol, s0):
    """The wording lists, bound byte for byte: re-serialised, they are the file whose hash three records name."""
    block = agg['wordings']['lists']
    lists = block['value']
    data = (json.dumps(lists, indent=2, ensure_ascii=False) + '\n').encode()
    digest = sha(data)
    require(digest == block['sha256'] == agg['inputs_sha256'][LISTS] == s0['wordings']['lists_file_sha256']
            == protocol['stage0b']['lists_file_sha256'], 'the wording lists are not the hashed lists')
    texts = sum(1 for _ in strings(lists))
    require(texts == agg['wordings']['texts_in_lists'] == 787, f'{texts} wording texts, not 787')
    require(s0['wordings']['pass'] is True and s0['wordings']['count_problems'] == 0
            and s0['wordings']['leakage_rules_1_4_6_and_brief_rules']['pass'] is True,
            'the wording checks did not pass before the first fit')
    return lists, digest


# ---------------------------------------------------------------------------- flags, rules, entries
def flags(kind, lo, hi, label):
    """Both flags follow from the interval and the frozen margin, and from nothing else (protocol decision_rules)."""
    if kind == 'log_r':
        require(not hi < 0, f'{label}: a head that leaves less error than its read-off has no declared wording here')
        difference = 'difference: the read-off leaves less error' if lo > 0 else 'no difference shown'
        if -LOG_P3 < lo and hi < LOG_P3:
            margin = 'equivalent within the margin'
        else:
            margin = 'non-inferior' if hi < LOG_P3 else 'margin not met'
        return difference, margin
    difference = FOR if lo > 0 else 'difference: reference higher' if hi < 0 else 'no difference shown'
    if kind in ('pp_difference_only', 'auroc_difference_only'):
        return difference, DIFFERENCE_ONLY
    if -DELTA < lo and hi < DELTA:
        margin = 'equivalent within the margin'
    else:
        margin = 'non-inferior' if lo > -DELTA else 'margin not met'
    return difference, margin


def rule_of(difference, margin, difference_only, gate_pass=True):
    """The route-sentence rule, first match (protocol route_sentence_rules.first_match_order)."""
    if not gate_pass:
        return 0
    if difference_only:
        return -1
    if difference in AGAINST:
        return 2 if margin in MET else 1
    if difference == FOR:
        return 3
    return {'equivalent within the margin': 4, 'non-inferior': 5}.get(margin, 6)


def entry_of(wrapper, key, label, gates, people_floor):
    """A pre-declared entry: its flags, rule, gate and sentences follow from its numbers and the frozen rules."""
    v = wrapper['value']
    require(v['status'] == 'ok', f'{label}: status {v["status"]}')
    require(v['type'] in KIND, f'{label}: an unknown entry type {v["type"]}')
    kind, rule_kind = KIND[v['type']]
    require(v['id'] == v['type'].split('_')[0], f'{label}: id and type disagree')
    n, seeds = v['people'], v['seeds']
    require(count(n) and n >= people_floor, f'{label}: a cell of {n} people')
    require(seeds in (1, 3), f'{label}: {seeds} seeds')
    iv = interval(v['lo'], v['hi'], v['point'], label)
    difference, margin = flags(rule_kind, *iv, label)
    require((v['difference'], v['margin']) == (difference, margin),
            f'{label}: the flags "{v["difference"]}; {v["margin"]}" do not follow from the interval '
            f'("{difference}; {margin}")')
    gate = wrapper['gate']
    if kind == 'unseen':
        require(gate == {'gate': 'headroom', 'label': 'pass'} and gates['headroom']['pass'] is True,
                f'{label}: an unseen entry gated otherwise than by its block\'s headroom')
    else:
        require(gate == {'gate': 'triviality canary', 'label': gates['triviality']['label']}
                and gates['triviality']['pass'] is True, f'{label}: a seen entry gated otherwise than by its canary')
    rule = rule_of(difference, margin, rule_kind.endswith('difference_only'))
    require(v['rule'] == rule, f'{label}: rule {v["rule"]}, the flags give {rule}')
    sentence, display = v['sentence'], wrapper['sentence_display']
    edits = wrapper['display_edits']
    require(set(edits) <= DISPLAY_EDITS and (display == sentence) is (not edits), f'{label}: display edits')
    require('did no difference shown' not in display, f'{label}: the literal template fill reached the display')
    require((UNSEEN in sentence and UNSEEN in display) is (kind == 'unseen'),
            f'{label}: an unseen sentence must carry "{UNSEEN}", and only an unseen one')
    out = {'key': key, 'id': v['id'], 'type': v['type'], 'kind': kind, 'label': v['label'], 'people': n,
           'seeds': seeds, 'single_seed': seeds == 1, 'estimate': v['point'], 'interval_95': iv,
           'unit': UNIT[rule_kind], 'difference': difference, 'margin': margin, 'rule': rule,
           'gate': {'gate': gate['gate'], 'label': gate['label']},
           'resampled_wording_kinds': v['resampled_wording_kinds'],
           'sentence': display, 'display_edits': edits}
    if edits:                                   # the route sentence as the rule produced it, before its display edit
        out['sentence_as_produced'] = sentence
    if 'R' in wrapper:
        require(rule_kind == 'log_r', f'{label}: R beside a contrast that is not a log ratio')
        r = wrapper['R']
        for k, x in (('point', v['point']), ('lo', v['lo']), ('hi', v['hi'])):
            close(r[k], math.exp(x), f'{label}: R {k} is not exp(log R)')
        out['r'] = {'estimate': r['point'], 'interval_95': interval(r['lo'], r['hi'], r['point'], label + ' R', 0.0)}
    else:
        require(rule_kind != 'log_r', f'{label}: a log ratio without R')
    if 'chance_corrected' in wrapper:
        cc = wrapper['chance_corrected']
        require(cc['basis'] == 'difference / (1 - chance)' and 0 < cc['chance'] < 1, f'{label}: chance-corrected')
        for k, x in (('point', v['point']), ('lo', v['lo']), ('hi', v['hi'])):
            close(cc[k], x / (1 - cc['chance']), f'{label}: chance-corrected {k}')
        out['chance_corrected'] = {'chance': cc['chance'], 'estimate': cc['point'],
                                   'interval_95': [cc['lo'], cc['hi']]}
    else:
        require(rule_kind == 'log_r' or v['type'] == 'P5', f'{label}: no chance-corrected value')
    return out


def figure(v, label, people_floor=1, lo_bound=-math.inf, hi_bound=math.inf):
    """A level or a descriptive contrast: point, interval, n and seeds, nothing else of the bootstrap record."""
    require(count(v['people']) and v['people'] >= people_floor, f'{label}: a cell of {v["people"]} people')
    require(v.get('nonfinite_draws', 0) == 0, f'{label}: non-finite bootstrap draws')
    out = {'estimate': v['point'], 'interval_95': interval(v['lo'], v['hi'], v['point'], label, lo_bound, hi_bound),
           'people': v['people']}
    if 'seeds' in v:
        out['seeds'] = v['seeds']
        require(('single_seed' not in v) or v['single_seed'] is (v['seeds'] == 1), f'{label}: single_seed')
    return out


def flagged_row(v, label, kind='pp', people_floor=1):
    """A secondary row with its flags (S8, S10, S11, S12, S13, per rotation): the flags follow from the interval."""
    out = figure(v, label, people_floor)
    difference, margin = flags(kind, *out['interval_95'], label)
    require((v['difference'], v['margin']) == (difference, margin), f'{label}: the flags do not follow')
    out.update(difference=difference, margin=margin, unit=LOGR if kind == 'log_r' else PP)
    if 'label' in v:
        out['label'] = v['label']
    if v.get('note'):
        out['note'] = v['note']
    return out


# ---------------------------------------------------------------------------- primary
def gates_of(g, label):
    require(set(g) == {'headroom', 'triviality'}, f'{label}: gates')
    require(g['headroom']['label'] == ('pass' if g['headroom']['pass'] else g['headroom']['label']), f'{label}: headroom')
    return {'headroom': {'pass': g['headroom']['pass'], 'label': g['headroom']['label']},
            'triviality': {'pass': g['triviality']['pass'], 'label': g['triviality']['label'],
                           'threshold': g['triviality']['threshold']}}


def primary(candidate, agg):
    blocks_c = candidate['results']['primary']['blocks']
    require([val(b, 'block')['block'] for b in blocks_c] == list(BLOCKS), 'the primary blocks changed')
    blocks, by_ref = [], {}
    for b_i, block in enumerate(blocks_c):
        b = val(block, 'block')
        boas = b['dataset'] == 'BOAS'
        gates = val(b['gates'], f'{b["block"]} gates')
        entries = []
        for e_i, wrapper in enumerate(b['entries']):
            key = f'{b["block"]}/{e_i}'
            e = entry_of(wrapper, key, key, gates, BOAS_MIN_PEOPLE if boas else 1)
            require(e['people'] == b['people'] and e['seeds'] == b['seeds'] == 3, f'{key}: another cohort or seed count')
            entries.append(e)
            by_ref[f'/primary/blocks/{b_i}/entries/{e_i}'] = key
        blocks.append({'block': b['block'], 'dataset': b['dataset'], 'domain': b['domain'], 'level': b['level'],
                       'level_words': b['level_words'], 'people': b['people'], 'seeds': b['seeds'],
                       'gates': gates_of(gates, b['block']), 'entries': entries})
    n = sum(len(b['entries']) for b in blocks)
    require(n == PRIMARY_COUNT == candidate['results']['primary']['entries_count'], f'{n} primary entries, not 35')
    return blocks, by_ref


def family_sentences(candidate, blocks):
    """The route sentences as the rules produced them, in entry order, and the one summary stage 3 wrote."""
    fs = candidate['results']['primary']['family_sentences']['value']
    sentences = fs['value']
    by_id = {}
    for b in blocks:
        for e in b['entries']:
            by_id.setdefault(e['id'], []).append(e)
    out = {}
    for pid in ('P1', 'P2', 'P3', 'P4', 'P5'):
        s = sentences[pid]
        own = by_id[pid]
        produced = [e.get('sentence_as_produced', e['sentence'])
                    for e in sorted(own, key=lambda e: BLOCKS.index(e['key'].split('/')[0]))]
        require(s['sentences'] == produced, f'{pid}: the family sentences are not the entries\'')
        rules = {e['rule'] for e in own}
        require(s['summary_allowed'] is (len(rules) == 1), f'{pid}: a summary is allowed only when one rule')
        require(s['rule'] == (rules.pop() if s['summary_allowed'] else None), f'{pid}: the family rule')
        out[pid] = {'summary_allowed': s['summary_allowed'], 'rule': s['rule'],
                    'entries': [e['key'] for e in own]}
    written = fs['summaries_written']
    require(list(written) == ['P3'] and all(e['rule'] == 1 for e in by_id['P3']), 'only the P3 summary is written')
    out['P3']['summary'] = written['P3']['sentence']
    require(UNSEEN in out['P3']['summary'], 'the P3 summary must carry the unseen phrase')
    for pid, why in fs['summaries_not_written'].items():
        out[pid]['summary_not_written'] = why
    return out, fs['rule']


def descriptive(candidate, agg):
    """Levels, chance-corrected levels and the descriptive contrasts of the three primary blocks."""
    d = inner(candidate['results']['descriptive'], 'descriptive')
    ccl = agg['primary_descriptive']['chance_corrected_levels']
    require(ccl['basis'].startswith('(level - chance) / (1 - chance)'), 'the chance-corrected basis')
    cc_all = ccl['value']
    out = {}
    for block in BLOCKS:
        v = d[block]
        boas = block.startswith('P-sleep')
        floor = BOAS_MIN_PEOPLE if boas else 1
        lvl = {}
        cc = cc_all[block]
        for name, x in v['levels'].items():
            f = figure(x, f'{block} {name}', floor, 0.0, 1.0)
            if name in cc:
                c = cc[name]
                close(c['point'], (x['point'] - c['chance']) / (1 - c['chance']), f'{block} {name}: chance-corrected')
                close(c['lo'], (x['lo'] - c['chance']) / (1 - c['chance']), f'{block} {name}: chance-corrected lo')
                close(c['hi'], (x['hi'] - c['chance']) / (1 - c['chance']), f'{block} {name}: chance-corrected hi')
                f['chance'] = c['chance']
                f['chance_corrected'] = {'estimate': c['point'], 'interval_95': [c['lo'], c['hi']]}
            lvl[name] = f
        require(set(cc) <= set(v['levels']), f'{block}: a chance-corrected level without its level')
        contrasts = {name: figure(x, f'{block} {name}', floor) for name, x in v.items()
                     if isinstance(x, dict) and 'point' in x}
        row = {'levels': lvl, 'contrasts': contrasts}
        if 'generalisation_costs' in v:
            row['generalisation_costs'] = {n: figure(x, f'{block} {n}', floor) for n, x in v['generalisation_costs'].items()}
        if 'chance_3way_mean' in v:
            close(v['chance_3way_mean'], 41 / 120, f'{block}: the mean 3-way chance', rel=1e-7)
            row['chance_3way_mean'] = {'stored': v['chance_3way_mean'], 'exact': '41/120',
                                       'note': ('A display value stored as a float32 mean; the exact mean per-trial '
                                                'chance of the neighbour 3-way is 41/120 (2-way at the two grid edges).')}
        for k in ('S15', 'seen_auroc_per_predicate', 'log_loss'):
            if k in v:
                row[k] = {n: figure(x, f'{block} {k} {n}', floor, 0.0, math.inf if k == 'log_loss' else 1.0)
                          for n, x in v[k].items()}
        known = {'levels', 'generalisation_costs', 'chance_3way_mean', 'S15', 'seen_auroc_per_predicate', 'log_loss'}
        require(all(k in known or k in contrasts for k in v), f'{block}: an unknown descriptive field')
        out[block] = row
    return out


# ---------------------------------------------------------------------------- pre-run checks
def pre_run_checks(candidate, agg, s0, a4, used):
    pr = candidate['pre_run_checks']
    rec = val(pr['canary_outcomes'], 'canary outcomes')
    r3, r4, r5, desc = rec['revision_3'], rec['revision_4'], rec['gate_r5'], rec['descriptive_r5']
    a4c = a4['checks']['canary_disclosure']
    require(a4c['pass'] is True, 'audit A4 did not reproduce the canaries')
    # Revision 3 and 4 failed, revision 5 passed; the cells and their sides are the audit's.
    side = {c['cell']: c['side'] for c in a4c['r3_cells_excluding_chance'] + a4c['r4_cells_excluding_chance']}
    require(r3['pass'] is False and r3['intervals'] == 38 and r3['intervals_excluding_chance'] == 1
            == len(r3['excluding_chance']) == len(a4c['r3_cells_excluding_chance']), 'revision 3')
    require(r4['pass'] is False and r4['intervals'] == 38 and r4['intervals_excluding_chance'] == 3
            == len(r4['excluding_chance']) == len(a4c['r4_cells_excluding_chance']), 'revision 4')
    require(set(r4['excluding_chance']) == {c['cell'] for c in a4c['r4_cells_excluding_chance']}, 'revision 4 cells')
    require(all(c.startswith('sleep/') for c in r3['excluding_chance'] + r4['excluding_chance']),
            'a failed canary cell outside BOAS')
    cells5 = r5['cells_include_zero']
    n5 = sum(len(m) for m in cells5.values())
    require(r5['pass'] is True and r5['intervals'] == n5 == 38 and r5['intervals_excluding_zero'] == 0
            == a4c['r5_intervals_excluding_zero'] and r5['excluding_zero'] == []
            and all(all(x is True for x in m.values()) for m in cells5.values()), 'revision 5')
    require(r5['configurations'] == len(cells5) == 17 and r5['replicates'] == 20 and r5['fits'] == 340
            and r5['level'] == 0.999 and r5['bootstrap_draws'] == 2000, 'revision 5 design')
    tot = desc['single_head_intervals_excluding_chance_total']['exact']
    both = desc['cells_with_single_head_failures_in_both_directions']['exact']
    require(tot == a4c['r5_single_head']['exact'] and both == a4c['r5_cells_both_directions']['exact']
            and desc['single_head_tests'] == 760 == 20 * n5, 'revision 5 descriptive counts')
    require(s0['revision_5']['B_gate_canary'] == {'pass': True, 'intervals': 38, 'intervals_excluding_zero': 0}
            and s0['revision_4']['B_gate_canary']['pass'] is False, 'the stage-0 report records other outcomes')
    disclosure = edit(val(pr['canary_disclosure_text'], 'disclosure'), used)
    for phrase in ('failed at stage 0b', 'It failed too', 'no further revision', 'overrode',
                   'centring diagnostic was not run', 'both failed records are kept'):
        require(phrase in disclosure, f'the canary disclosure does not say {phrase!r}')
    override = val(pr['owner_override'], 'override')
    require('no further revision' in override and 'overrode' in override, 'the override')
    centring = pr['centring_diagnostic']
    require('not run' in centring and s0['centring_diagnostic_revision_4']['run'] is False, 'the centring diagnostic')
    canaries = {
        'what': ('A training-label permutation canary refits the heads on shuffled training labels and checks that '
                 'test scores sit at chance (17 configurations, the first fold, 38 intervals at 99.9%).'),
        'revision_3': {'pass': False, 'status': r3['status'], 'permutation': r3['permutation'],
                       'intervals': r3['intervals'], 'intervals_excluding_chance': r3['intervals_excluding_chance'],
                       'cells_excluding_chance': [{'cell': c, 'side': side[c]} for c in r3['excluding_chance']],
                       'decision': edit(r3['decisions'], used)},
        'revision_4': {'pass': False, 'status': r4['status'], 'permutation': r4['permutation'], 'fits': r4['fits'],
                       'intervals': r4['intervals'], 'intervals_excluding_chance': r4['intervals_excluding_chance'],
                       'cells_excluding_chance': [{'cell': c, 'side': side[c]} for c in r4['excluding_chance']],
                       'centring_diagnostic': r4['centring_diagnostic'], 'decision': edit(r4['decisions'], used)},
        'revision_5': {'pass': True, 'stopping_rule': rec['stopping_rule'], 'permutation': r5['permutation'],
                       'configurations': r5['configurations'], 'replicates': r5['replicates'], 'fits': r5['fits'],
                       'statistic': r5['statistic'], 'interval': r5['interval'], 'level': r5['level'],
                       'bootstrap_draws': r5['bootstrap_draws'], 'intervals': r5['intervals'],
                       'intervals_excluding_zero': r5['intervals_excluding_zero'],
                       'cells_interval_includes_zero': cells5,
                       'single_head_tests': desc['single_head_tests'],
                       'single_head_intervals_excluding_exact_chance': {'above': tot['above'], 'below': tot['below'],
                                                                        'total': tot['above'] + tot['below']},
                       'cells_with_single_head_failures_in_both_directions': both,
                       'single_head_role': desc['role']},
        'boas': 'BOAS cells: pass or fail and direction counts only; no BOAS canary value left the private run root.',
        'audit_reproduction': val(pr['audit_reproduction'], 'audit reproduction'),
    }
    s0b6 = val(pr['decision_s0b6'], 'S0b-6')
    scope = val(s0b6['token_rule_record'], 'token rule')
    stops, e5 = scope['stops_run'], scope['e5_number_pieces_only']
    require(stops['pass'] is True and stops['encoders'] == ['bge', 'minilm'] and stops['rotations'] == [0, 1, 2, 3, 4]
            and e5['pass'] is True and e5['rows'] == 5 and not any(e5['full_rule_pass']), 'decision S0b-6')
    decision_s0b6 = {
        'decision': edit(s0b6['decision'], used), 'what': s0b6['what'],
        'owner_approval': val(s0b6['owner_approval'], 'S0b-6 approval'),
        'token_rule': {'stops_the_run_for': ['bge-small-en-v1.5', 'all-MiniLM-L6-v2'],
                       'rotations_passed': len(stops['rotations']),
                       'multilingual_e5_small': {'rotations': e5['rows'], 'number_pieces_only_rule_passed': e5['rows'],
                                                 'full_rule_passed': sum(e5['full_rule_pass'])}},
        'statement_on_entries': s0b6['statement_on_entries'],
    }
    ea1 = inner(pr['engineering_amendment_ea1'], 'EA-1')
    engineering = {k: edit(ea1[k], used) for k in ('decision', 's8_nn', 's8_three_way', 'failed_fits',
                                                     'resumable_secondary_scoring')}
    require('no question, partition, wording, arm, metric, margin or gate' in engineering['decision'], 'EA-1 scope')
    num = val(pr['numeracy_prediction'], 'numeracy')
    obs = inner(num['observed'], 'numeracy observed')
    rho = obs['spearman_rho']
    out_n = num['outcome']
    require(obs['declared_prediction']['active'] is False and any(rho[f'bge/frame{i}'] < 0.3 for i in range(3)) is False,
            'the numeracy prediction: its premise')
    flag_anyway = {}
    for level, f in out_n['flag_anyway'].items():
        require(f['difference'] == flags('pp_difference_only', f['lo'], f['hi'], level)[0] != FOR,
                f'numeracy {level}: the flag')
        flag_anyway[level] = {'entry': f['entry'], 'difference': f['difference']}
    numeracy = {'declared': inner(num['declared'], 'numeracy declared'), 'spearman_rho': rho, 'pairs': obs['pairs'],
                'activated': False, 'premise': out_n['premise'], 'flag_anyway': flag_anyway,
                'reading': out_n['reading']}
    g = val(pr['gates'], 'gates')
    fit = val(g['fit_check'], 'fit check')
    fit_rows = {}
    for dl, x in fit['by_domain_level'].items():
        require(x['failed_fits'] == [] and x['epochs'] == fit['epochs_final_recipe'][dl]
                and x['fallback_60'] is (dl in fit['fallback_60_used_by']) and x['epochs'] == (60 if x['fallback_60'] else 30),
                f'fit check {dl}')
        fit_rows[dl] = {'training_epochs': x['epochs'], 'fallback_to_60_epochs': x['fallback_60'],
                        'arms_more_than_5_pp_below_b_sh': x['arms_more_than_5pp_below_bsh'], 'failed_fits': 0}
    sh = g['shuffled_eeg_scorer_check']
    ssvep_cells = sh['ssvep_cells']
    boas_n = int(re.search(r'all (\d+) BOAS cells within 3 MC SE', sh['boas_cells']).group(1))
    require(sh['pass'] is True and all(c['within_3_se'] is True for c in ssvep_cells.values())
            and sh['cells'] == sh['cells_within_3_se'] == len(ssvep_cells) + boas_n == 51, 'the shuffled-EEG check')
    triv = {}
    for ds, t in g['triviality'].items():
        require(t['pass'] is True, f'triviality {ds}')
        row = {'pass': True}
        if t.get('value') is not None:
            require(t['value'] < t['threshold'], f'triviality {ds}: the value does not pass its threshold')
            row.update(threshold=t['threshold'], training_people=t['people'],
                       origin={'BETA': 'stage 0: the first fold\'s training people, four inner folds; recomputed by '
                                       'audit A2',
                               'BOAS': 'route 2\'s canary, carried', 'EESM19': 'route 2\'s canary, carried'}[ds])
        else:
            row['label'] = t['label']
        triv[ds] = row
    head = {}
    for block, h in g['headroom'].items():
        x = val(h['id_seen_ba'], f'{block} headroom')
        floor_ = h['chance'] + 0.05
        passes = x['lo'] > floor_ and x['hi'] < 0.95
        require(h['pass'] is passes is True, f'{block}: the headroom gate does not follow from the ID interval')
        head[block] = {'arm': 'ID', 'metric': 'seen balanced accuracy', 'pass': True, 'chance': h['chance'],
                       'floor': floor_, 'ceiling': 0.95,
                       **figure(x, f'{block} headroom', BOAS_MIN_PEOPLE if 'sleep' in block else 1, 0.0, 1.0)}
    ro = g['readoff_floor']
    require(ro['primary'].startswith('pass in all 8 P3 cells') and ro['secondary'].startswith('pass in all 34 P3 cells'),
            'the read-off floor gate')
    gates = {'rule': {k: v for k, v in val(g['rule'], 'gate rule').items()},
             'per_entry_rule': edit(g['per_entry_rule'], used),
             'headroom': head, 'triviality': triv,
             'readoff_floor': {'rule': ro['rule'], 'primary_cells': 8, 'primary_cells_passing': 8,
                               'secondary_cells': 34, 'secondary_cells_passing': 34},
             'fit_check': {'rule': fit['rule'], 'fits': fit['fits'], 'by_domain_and_level': fit_rows,
                           'boas': 'pass or fail only; BOAS training scores never left the private run root'},
             'shuffled_eeg_scorer_check': {'rule': val(sh['rule'], 'shuffled rule'), 'pass': True,
                                           'cells': sh['cells'], 'cells_within_3_se': sh['cells_within_3_se'],
                                           'ssvep_cells': len(ssvep_cells), 'boas_cells': boas_n}}
    why = val(pr['why_they_failed'], 'why')
    return {'disclosure': disclosure, 'why_they_failed': {'en': why['en'], 'zh': why['zh']},
            'owner_override': override, 'owner_decisions': owner_decisions(pr, used),
            'canaries': canaries, 'centring_diagnostic': centring, 'decision_s0b6': decision_s0b6,
            'engineering_amendment_ea1': engineering, 'numeracy_probe': numeracy, 'gates': gates}


def owner_decisions(pr, used):
    """The owner's two canary decisions of 2026-10-08 as the protocol records them (the GPU etiquette left out)."""
    od = inner(pr['owner_decisions'], 'owner decisions')
    require(list(od) == ['revision_4', 'revision_5'], 'the owner decisions of 2026-10-08')
    r4, r5 = od['revision_4'], od['revision_5']
    require('两个都批准，按方案二继续跑' in r4['source'] and '批准方案二' in r5['source']
            and "overriding revision 4's \"no further revision\"" in r5['option_2'], 'the owner decisions\' words')
    return {'revision_4': {'decided': r4['source'], 'approved': edit(r4['option_2'], used), 'S0b-6': r4['S0b-6']},
            'revision_5': {'decided': r5['source'], 'approved': edit(r5['option_2'], used)}}


# ---------------------------------------------------------------------------- secondary
def secondary(candidate, expected_inconclusive):
    sec = val(candidate['results']['secondary'], 'secondary')
    parts = sec['parts']
    out, entries_n, p3_cells = {}, 0, 0
    for pid in ENTRY_PARTS:
        p = parts[pid]
        boas = p.get('boas', False) is True
        require(boas is (pid in BOAS_PARTS), f'{pid}: the BOAS flag')
        gates = p['gates']
        entries = []
        for i, wrapper in enumerate(p['entries']):
            e = entry_of(wrapper, f'secondary/{pid}/{i}', f'{pid} entry {i}', gates, BOAS_MIN_PEOPLE if boas else 1)
            entries.append(e)
            p3_cells += e['id'] == 'P3'
        seeds = {e['seeds'] for e in entries}
        require(len(seeds) == 1, f'{pid}: mixed seed counts')
        single = seeds == {1}
        inconclusive = single or p['dataset'] == 'EESM19'
        require(('declared likely inconclusive' in p['status_label']) is inconclusive, f'{pid}: the status label')
        row = {'part': pid, 'what': p['what'], 'dataset': p['dataset'], 'label': p['label'],
               'status_label': p['status_label'], 'single_seed': single, 'declared_likely_inconclusive': inconclusive,
               'boas': boas, 'gates': gates_of(gates, pid), 'entries': entries}
        for k in ('gate_note', 'shuf_derangements_note', 'sentence_note', 'token_note'):
            if k in p:
                row[k] = p[k]
        if pid == 'S5-ssvep-L0':
            token_note = p['token_note']
            require(all(token_note in e.get('sentence_as_produced', e['sentence']) and token_note in e['sentence']
                        for e in entries if e['type'].startswith('P4')),
                    'S5 SSVEP: every unseen-frequency entry carries the S0b-6 token note')
        out[pid] = row
        entries_n += len(entries)
    require(entries_n == SECONDARY_ENTRY_COUNT, f'{entries_n} secondary entries, not {SECONDARY_ENTRY_COUNT}')
    require(p3_cells == 34, f'{p3_cells} secondary P3 cells, not 34')
    # S6, the negation probe (BOAS).
    s6 = parts['S6']['value']
    require(s6['boundary_probe'] is True and s6['never_a_route_sentence'] is True, 'S6 is a boundary probe')
    out['S6'] = {'part': 'S6', 'what': s6['what'], 'dataset': 'BOAS', 'boas': True, 'boundary_probe': True,
                 'never_a_route_sentence': True,
                 'cells': {w: {k: figure(x, f'S6 {w} {k}', BOAS_MIN_PEOPLE, 0.0, 1.0) for k, x in c.items()}
                           for w, c in s6['cells'].items()},
                 'note': ('Each "not X" wording is scored against the truth of the negated question, beside the AUROC '
                          'of 1 - p(X); "non-REM sleep" (an implicit name) is scored against the truth of "not REM".')}
    require(all(set(c) == {'negated_wording_auroc', 'one_minus_p_auroc'} for w, c in s6['cells'].items() if w.startswith('not '))
            and set(s6['cells']['non-REM sleep (implicit)']) == {'auroc', 'one_minus_p_REM_auroc'}, 'S6: the cells')
    # S13 on sleep: held-out frames against the read-off (log R, P3 flags).
    s13 = parts['S13-sleep']['value']
    out['S13-sleep'] = {'part': 'S13-sleep', 'what': s13['what'], 'dataset': 'BOAS', 'boas': True,
                        'rows': {k: flagged_row(x, f'S13 {k}', 'log_r', BOAS_MIN_PEOPLE)
                                 for k, x in s13.items() if k != 'what'}}
    # SSVEP secondary rows: S9 levels, S10 contrasts and per-rotation rows, S11 FBCCA, S13 held-out wordings.
    for pid in ('SSVEP-L0-secondary', 'SSVEP-L1-secondary'):
        v = parts[pid]['value']
        rows, levels, rotations = {}, {}, {}
        for k, x in v.items():
            if k == 'what':
                continue
            if k.startswith('S10 rotation'):
                rotations[x['label']] = flagged_row(x, f'{pid} {k}') | {'seeds': x['seeds']}
            elif 'difference' in x:
                rows[k] = flagged_row(x, f'{pid} {k}') | {'seeds': x['seeds']}
            elif 'point' in x:
                levels[k] = figure(x, f'{pid} {k}', 1, 0.0, 1.0)
            else:
                levels[k] = {m: figure(y, f'{pid} {k} {m}', 1, 0.0, 1.0) for m, y in x.items() if m != 'harmonic_mean'}
                if 'harmonic_mean' in x:     # S9: the harmonic mean of seen-truth and unseen-truth accuracy
                    s_, u_ = x['seen_truth']['point'], x['unseen_truth']['point']
                    close(x['harmonic_mean'], 2 * s_ * u_ / (s_ + u_), f'{pid} {k}: the harmonic mean')
                    levels[k]['harmonic_mean'] = x['harmonic_mean']
        require(list(rotations) == [f'rotation {i}' for i in range(5)], f'{pid}: five rotations')
        out[pid] = {'part': pid, 'what': v['what'], 'dataset': 'BETA', 'boas': False, 'rows': rows, 'levels': levels,
                    'per_rotation_tpl_minus_cca_8_way': rotations}
    # S8: extrapolation to a contiguous band (one seed).
    for pid in ('S8-L0', 'S8-L1'):
        p = parts[pid]
        v = p['value']
        rows = {}
        for k, x in v.items():
            if k in ('what', 'notes', 'levels (descriptive)'):
                continue
            if x.get('status') == 'not defined':
                require('EA-1' in x['reason'] or 'engineering amendment EA-1' in x['reason'], f'{pid} {k}: not defined')
                rows[k] = {'label': x['label'], 'status': 'not defined', 'reason': x['reason']}
            else:
                require(x['seeds'] == 1, f'{pid} {k}: one seed')
                rows[k] = flagged_row(x, f'{pid} {k}') | {'seeds': 1}
        out[pid] = {'part': pid, 'what': v['what'], 'dataset': 'BETA', 'boas': False, 'single_seed': True,
                    'status_label': p['status_label'], 'declared_likely_inconclusive': True, 'rows': rows,
                    'notes': v['notes']}
        require('declared likely inconclusive' in p['status_label'], f'{pid}: the status label')
    # S12: Wearable-102, off-grid frequencies, per sensor.
    s12 = parts['S12']['value']
    out['S12'] = {'part': 'S12', 'what': s12['what'], 'dataset': 'Wearable-102', 'boas': False, 'note': s12['note'],
                  'by_sensor': {S12_SENSORS[s]: {k: flagged_row(x, f'S12 {s} {k}') | {'seeds': x['seeds']}
                                                 for k, x in rows.items()}
                                for s, rows in s12['by_sensor'].items()}}
    # Flip rates between wordings (descriptive).
    flips = {}
    for pid in ('flip-ssvep-L0', 'flip-ssvep-L1', 'flip-sleep-L1'):
        v = parts[pid]['value']
        boas = pid in BOAS_PARTS
        people = v.get('people', 70)
        require(people == (100 if boas else 70), f'{pid}: another cohort')
        rate = lambda x: {'rate': x, 'people': people}
        flips[pid] = {'what': v['what'], 'boas': boas,
                      'TPL': {k: rate(x) for k, x in v['TPL'].items()},
                      'DESC': {k: rate(x) for k, x in v['DESC'].items()},
                      'between_ID_seeds': rate(v['ref_between_ID_seeds'])}
        if boas:
            flips[pid]['people_note'] = v['people_note']
        require(all(0 <= r['rate'] <= 1 for g_ in ('TPL', 'DESC') for r in flips[pid][g_].values()), f'{pid}: a rate')
    return {'multiplicity_note': val(sec['multiplicity_note'], 'secondary multiplicity'),
            'interval_note': val(sec['interval_note'], 'secondary interval'),
            'none_inconclusive': sec['none_inconclusive'],
            'expected_inconclusive': expected_inconclusive,
            'parts': out, 'flip_rates': flips}


# ---------------------------------------------------------------------------- rights, references, BOAS
def released_record(src):
    """The rights record a released site file holds for this source (read, never written)."""
    r = src['released']
    data = json.loads((PROJECT / r['file']).read_bytes())
    if 'track' in r:
        t = next(t for t in data['tracks'] if t['id'] == r['track'])
        return {k: t[k] for k in ('license', 'licenseUrl', 'source', 'attribution', 'reviewedAt')}
    if 'dataset' in r:
        x = data['results'][r['result']]['datasets'][r['dataset']]['rights']
        return {k: x[k] for k in ('license', 'licenseUrl', 'source', 'attribution', 'reviewedAt')}
    if 'result' in r:
        x = data['results'][r['result']]['rights']
        return {k: x[k] for k in ('license', 'licenseUrl', 'source', 'attribution', 'reviewedAt')}
    c = next(c for c in data['dataset_citations'] if c['id'] == r['citation'])
    require(c['decision'] == 'aggregate_publication_only', f'{src["id"]}: the released decision')
    return {'license': c['identity']['license'], 'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
            'source': c['primary_sources'][0], 'attribution': c['identity']['canonical_dataset_citation'],
            'paper': c['identity']['paper_citation'], 'reviewedAt': '2026-09-20',
            'mirror': c['identity']['local_representation']}


def datasets(manifest):
    out = {}
    for s in manifest['sources']:
        rec = released_record(s)
        for k in ('license', 'source', 'attribution', 'reviewedAt') + (('paper',) if 'paper' in s else ()):
            require(s[k] == rec[k], f'{s["id"]}: {k} differs from the released record')
        require(s['licenseUrl'] == rec['licenseUrl'], f'{s["id"]}: the licence URL differs from the released record')
        row = {'name': s['name'], 'role': s['role'], 'license': s['license'], 'licenseUrl': s['licenseUrl'],
               'source': s['source'], 'attribution': s['attribution'], 'rights_reviewed': s['reviewedAt'],
               'rights_record': 'reused unchanged from the released record', 'published_here': s['publishedHere']}
        if 'paper' in s:
            row['paper'] = s['paper']
            require('2026-09-20' in rec['mirror'] and 'author mirror' in rec['mirror'], 'Wearable-102: the mirror')
            row['computed_from'] = rec['mirror']
        out[s['id']] = row
    require(list(out) == ['beta', 'boas', 'eesm19', 'openbmi', 'wearable-ssvep-102'], 'the manifest names other sources')
    return out


def references(manifest, handoff, prior_art):
    out = []
    lines = prior_art.splitlines()
    for r in manifest['references']:
        url, cite = r['url'], r['cite']
        require('Yu et al' not in cite, f'{r["id"]}: the vision paper is "Yu & Yao, 2026"')
        ident = url.rstrip('/').split('/abs/')[-1].split('doi.org/')[-1]
        require(ident in handoff, f'{r["id"]}: the handoff does not name {ident}')
        where = r['checkedIn']
        if where.endswith('prior-art.md'):
            hits = [ln for ln in lines if re.match(r'^\d+\. ', ln) and ident.split('/')[-1] in ln]
            require(len(hits) == 1, f'{r["id"]}: the reference check does not list it once')
            authors, _, title = cite.partition(' · ')
            require(title in hits[0], f'{r["id"]}: the title is not the checked one')
            for name in re.findall(r"[A-Z][\w'’-]+", authors.split(',')[0] + ' ' + authors):
                if name not in ('Van', 'Durme'):
                    require(name in hits[0], f'{r["id"]}: {name} is not among the checked authors')
            require('checked 2026-10-07' in hits[0], f'{r["id"]}: no check date')
        else:
            page = (PROJECT / where).read_text()
            require(cite in page and url in page, f'{r["id"]}: the site does not cite it so')
        out.append({k: r[k] for k in ('id', 'cite', 'url', 'role')})
    require(out[0]['cite'] == VISUAL_JEV and out[0]['url'] == 'https://arxiv.org/abs/2609.25845',
            'the route origin is the vision paper, cited as the site cites it')
    return out


def boas_conditions(candidate, released, manifest_boas, smallest):
    req = val(candidate['boas_requirements'], 'BOAS requirements')
    cond = released['results']['one-representation']['boas_conditions']
    gaps = req['three_gaps']
    require(gaps['en'] == cond['gaps'] and len(gaps['en']) == len(gaps['zh']) == 3, 'BOAS: the three gaps are not route 2\'s')
    route2_zh = (PROJECT / 'site/src/data/shared-encoder.ts').read_text()      # the site's Chinese of the same gaps
    require(all(f"'{g}'" in route2_zh for g in gaps['zh']), 'BOAS: the Chinese gaps are not the ones the site prints')
    require(req['attribution'] == cond['attribution'] == manifest_boas['attribution'], 'BOAS: the attribution')
    require(cond['participants'] == 'pseudonymised in the public release'
            and any('pseudonymised in the public release' in w for w in req['wording']), 'BOAS: the participants wording')
    require(req['audit_check']['value']['pass'] is True and req['audit_check']['value']['cells_below_20'] == []
            and req['check_by_this_builder']['cells_under_20'] == 0, 'BOAS: the D11 checks')
    require(smallest >= BOAS_MIN_PEOPLE and smallest == req['check_by_this_builder']['min_people'],
            f'BOAS: the smallest cell is {smallest}')
    return {
        'owner_approval': {'approved_on': '2026-10-07', 'decision': 'publishable with stated gaps',
                           'extended_to_route_3': 'D11, approved by the owner on 2026-10-07'},
        'gaps': gaps['en'], 'gaps_zh': gaps['zh'], 'attribution': cond['attribution'],
        'participants': cond['participants'], 'not_an_evaluation_of': cond['not_an_evaluation_of'],
        'minimum_cell_people': BOAS_MIN_PEOPLE, 'smallest_cell_people': smallest,
        'smallest_cell_note': req['check_by_this_builder']['note'],
        'pre_run_checks': 'pass or fail and direction counts only',
    }


def boas_people(value, inside=False, n=None):
    """Every count of people behind a BOAS figure, and every BOAS figure without one. A figure's own sub-figures (its
    chance-corrected value, R) belong to the same cell and carry its n."""
    if isinstance(value, dict):
        here = inside or value.get('boas') is True or value.get('dataset') == 'BOAS'
        own = value.get('people') if count(value.get('people')) else n
        if here and any(k in value for k in ('estimate', 'rate')) and own is None:
            raise ValueError(f'a BOAS figure without its n: {sorted(value)[:6]}')
        if here and count(value.get('people')):
            yield value['people']
        for k, x in value.items():
            if k != 'people':
                yield from boas_people(x, here, own if any(j in value for j in ('estimate', 'rate')) else None)
    elif isinstance(value, list):
        for x in value:
            yield from boas_people(x, inside)


# ---------------------------------------------------------------------------- what stays out
def all_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from all_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_keys(v)


def scrub_check(value, trail='$'):
    """Refused keys and fragments; private paths, hosts and file names; the date rule; Jev only with its scope."""
    if isinstance(value, dict):
        require(not (isinstance(value.get('source'), str) and '.json#' in value['source']),
                f'{trail}: a traced block of the release candidate reached the export')
        for k, v in value.items():
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not PRIVATE_TOKENS.search(value), f'private host, path or file in export: {trail}')
        require('anonymous' not in value.lower() and 'anonymised' not in value.lower(), f'{trail}: say pseudonymised')
        require('Yu et al' not in value, f'{trail}: the vision paper is "Yu & Yao, 2026"')
        if 'jev' in value.lower():
            require('not an integration with Jev' in value or value.startswith(VISUAL_JEV)
                    or 'not affiliated with the Jev authors' in value, f'{trail}: Jev without its scope sentence')
        if trail not in IDENTIFIER_TRAILS:
            # As check-workbench reads the pages: links are not text, and a Figshare record's "v3" is its version.
            text = re.sub(r'Figshare(?: record)?(?: \d+)? v\d+', ' ', re.sub(r'https?://\S+', ' ', value))
            for what, rule in DATE_RULES:
                require(not rule.search(text), f'{trail}: {what} in export text')


def withheld_values(agg, s0):
    """Values this file never publishes, refused by value: the S10 breakdowns and every pre-run check value."""
    out = set()

    def take(node, keys):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in keys and isinstance(v, float):
                    out.add(v)
                else:
                    take(v, keys)
        elif isinstance(node, list):
            for v in node:
                take(v, keys)
    s10 = agg['s10_breakdowns']['value']['levels']
    for level in s10.values():
        take(level['per_frequency'], {'point', 'lo', 'hi'})
        take(level['interior_only'], {'point', 'lo', 'hi'})
    take(s0['fit_check']['by_domain_level'], {'ID', 'TPL', 'DESC', 'SHUF', 'NUM', 'B-sh'})
    for k in ('permutation_canary_revision_3', 'permutation_canary_revision_4_gate', 'permutation_canary_revision_5_gate'):
        take(s0[k], {'point', 'lo', 'hi', 'D', 'metric_mean', 'between_replicate_sd_metric'})
    take(agg['pre_run_checks']['gates']['shuffled_eeg_scorer_check']['ssvep_cells'], {'mean', 'mc_se'})
    for t in agg['pre_run_checks']['gates']['triviality'].values():
        if isinstance(t.get('value'), float):
            out.add(t['value'])
    return out


def check_not_published(payload, wordings, items):
    """Each not_published item is a claim about these files; the files must bear it out (pattern of 2026-10-05)."""
    keys = set(all_keys(payload)) | set(all_keys(wordings))
    tokens = {t for k in keys for t in re.split(r'[_\-/ ()\[\]]+', k.lower()) if t}

    def none_of(pattern):
        return not [k for k in keys if re.search(pattern, k, re.IGNORECASE)]
    rules = {
        'Per-person, per-night, per-recording and per-fold values': lambda: none_of(
            r'per_person|per_participant|per_night|per_recording|fold|prediction|probabilit|feature|weights$|splits'),
        'The S10 per-frequency and interior-only BETA breakdowns': lambda: none_of(r'per_frequency|interior|s10_break|by_cohort_and_frequency'),
        'Values of the pre-run checks': lambda: none_of(r'training_balanced|^D$|mc_se|expected_exact|metric_mean|replicates_(above|below)|by_fit|by_configuration|^value$'),
        'The secondary parts\' descriptive blocks': lambda: none_of(r'cosine|nearest') and not [
            k for pid, part in payload['results'][ROUTE]['secondary']['parts'].items()
            if pid in ENTRY_PARTS or pid.startswith('S8') for k in part if k in ('descriptive', 'levels')],
        'Demographics, recording dates and clock times': lambda: not tokens & {'age', 'sex', 'bmi', 'date', 'dates',
                                                                                 'clock', 'night', 'nights', 'hypnogram',
                                                                                 'trace', 'demographics'},
        'Measured compute': lambda: none_of(r'gpu|hours|wall|seconds|elapsed|ledger|timing|wait'),
        'The text of the audits\' discrepancy lists': lambda: none_of(r'discrepanc|observations|verdict_note'),
        'The handoff, the release candidate, the aggregates': None,
    }
    used = []
    for item in items:
        hits = [k for k in rules if item.startswith(k)]
        require(len(hits) == 1, f'not_published: no check for the item "{item[:70]}"')
        require(rules[hits[0]] is None or rules[hits[0]](),
                f'not_published: the file carries what the item says it leaves out: "{item[:70]}"')
        used.append(hits[0])
    require(sorted(used) == sorted(rules), 'not_published: an item is missing or named twice')


def handoff_figures(result):
    """The figures the pages print, written as the pinned handoff writes them: each must be there."""
    pp = lambda e: f'| {100 * e["estimate"]:+.2f} | [{100 * e["interval_95"][0]:+.2f}, {100 * e["interval_95"][1]:+.2f}] |'
    lr = lambda e: f'| {e["estimate"]:+.3f} | [{e["interval_95"][0]:+.3f}, {e["interval_95"][1]:+.3f}] |'
    pc = lambda f: f'{100 * f["estimate"]:.1f}% ({100 * f["interval_95"][0]:.1f}–{100 * f["interval_95"][1]:.1f})'
    out = []
    entries = [e for b in result['primary']['blocks'] for e in b['entries']]
    entries += [e for p in result['secondary']['parts'].values() for e in p.get('entries', [])]
    for e in entries:
        out.append(lr(e) if e['unit'] in (LOGR, AUC) else pp(e))
        if 'r' in e and not e['key'].startswith('secondary/'):    # the handoff prints R for the primary entries
            out.append(f'{e["r"]["estimate"]:.2f} [{e["r"]["interval_95"][0]:.2f}, {e["r"]["interval_95"][1]:.2f}]')
    d = result['descriptive']
    for block in ('P-ssvep-L0', 'P-ssvep-L1'):
        for name in ('ID seen_ba', 'TPL seen_ba', 'DESC seen_ba', 'SHUF seen_ba', 'NUM seen_ba', 'B-sh seen_ba',
                     'CCA seen_ba', 'TPL u8', 'DESC u8', 'SHUF u8', 'NUM u8', 'CCA u8', 'TPL nn8', 'ID nn8', 'TPL u3',
                     'NUM u3', 'CCA u3'):
            out.append(pc(d[block]['levels'][name]))
        for name, g in d[block]['generalisation_costs'].items():
            out.append(f'{100 * g["estimate"]:+.2f} [{100 * g["interval_95"][0]:+.2f}, {100 * g["interval_95"][1]:+.2f}]')
    for name in ('ID seen_ba', 'TPL seen_ba', 'DESC seen_ba', 'SHUF seen_ba', 'B-sh seen_ba'):
        out.append(pc(d['P-sleep-L1']['levels'][name]))
    for name, x in d['P-sleep-L1']['levels'].items():
        if name.endswith('AUROC'):
            out.append(f'{x["estimate"]:.3f} ({x["interval_95"][0]:.3f}–{x["interval_95"][1]:.3f})')
    s = result['secondary']['parts']
    for w, c in s['S6']['cells'].items():
        for f in c.values():
            out.append(f'{f["estimate"]:.3f} ({f["interval_95"][0]:.3f}–{f["interval_95"][1]:.3f})')
    for sensor, rows in s['S12']['by_sensor'].items():
        for k, x in rows.items():
            out.append(f'| {sensor} | {k} | {100 * x["estimate"]:+.2f} | [{100 * x["interval_95"][0]:+.2f}, '
                       f'{100 * x["interval_95"][1]:+.2f}] |')
    for pid in ('SSVEP-L0-secondary', 'SSVEP-L1-secondary'):
        for x in s[pid]['per_rotation_tpl_minus_cca_8_way'].values():
            out.append(f'{100 * x["estimate"]:+.2f} [{100 * x["interval_95"][0]:+.2f}, {100 * x["interval_95"][1]:+.2f}]')
    for pid in ('S8-L0', 'S8-L1'):
        for x in s[pid]['rows'].values():
            if 'estimate' in x:
                out.append(f'{100 * x["estimate"]:+.2f} | [{100 * x["interval_95"][0]:+.2f}, {100 * x["interval_95"][1]:+.2f}]')
    for pid, f in result['secondary']['flip_rates'].items():   # the handoff's flip table (DESC between training
        for x in (f['TPL']['a1'], f['TPL']['a2'], f['DESC']['a3'], f['TPL']['ref_training'], f['between_ID_seeds']):
            out.append(f'{100 * x["rate"]:.1f}%')                     # wordings is not in it)
    return out


def key_findings(candidate, by_ref, handoff, payload_numbers):
    """The candidate's generated headlines, each with the entries it cites; every numeral is the handoff's or a
    figure of this file as printed."""
    allowed = numerals(handoff)
    for x in payload_numbers:
        for s in (f'{abs(x) * 100:.2f}', f'{abs(x) * 100:.1f}', f'{abs(x):.3f}', f'{abs(x):.2f}', f'{abs(math.exp(x)):.2f}'):
            allowed.add(s)
    out = []
    for f in candidate['key_findings']:
        cites = []
        for ref in f['refs']:
            if ref in by_ref:
                cites.append(by_ref[ref])
            else:
                m = re.fullmatch(r'/secondary/parts/([\w-]+)(?:/entries/(\d+))?|/pre_run_checks/(\w+).*', ref)
                require(m is not None, f'{f["id"]}: an unknown reference {ref}')
                cites.append(f'secondary/{m.group(1)}' + (f'/{m.group(2)}' if m.group(2) else '') if m.group(1)
                             else 'pre_run_checks')
        for lang in ('en', 'zh'):
            missing = numerals(f[lang]) - allowed
            require(not missing, f'{f["id"]} ({lang}): numerals in no pinned text or figure: {sorted(missing)[:5]}')
        out.append({'id': f['id'], 'en': f['en'], 'zh': f['zh'], 'cites': cites})
    return out


def disclosures(result):
    """What every page that shows route-3 results must carry is in this file, at a stated place."""
    pr = result['pre_run_checks']
    c = pr['canaries']
    items = [
        ('revision-3-failed', c['revision_3']['pass'] is False, 'pre_run_checks.canaries.revision_3'),
        ('revision-4-failed', c['revision_4']['pass'] is False, 'pre_run_checks.canaries.revision_4'),
        ('revision-5-passed', c['revision_5']['pass'] is True, 'pre_run_checks.canaries.revision_5'),
        ('owner-override', 'overrode' in pr['owner_override'], 'pre_run_checks.owner_override'),
        ('centring-diagnostic-not-run', 'not run' in pr['centring_diagnostic'], 'pre_run_checks.centring_diagnostic'),
        ('revision-5-direction-counts', c['revision_5']['single_head_intervals_excluding_exact_chance']['total'] == 125,
         'pre_run_checks.canaries.revision_5.single_head_intervals_excluding_exact_chance'),
        ('decision-s0b6', 'S0b-6' in pr['decision_s0b6']['decision'], 'pre_run_checks.decision_s0b6'),
        ('ea-1', 'EA-1' in pr['engineering_amendment_ea1']['decision'], 'pre_run_checks.engineering_amendment_ea1'),
        ('numeracy-not-activated', pr['numeracy_probe']['activated'] is False, 'pre_run_checks.numeracy_probe'),
        ('multiplicity', result['design']['multiplicity'].startswith('35 pre-declared comparisons, not corrected'),
         'design.multiplicity'),
        ('secondary-single-seed-likely-inconclusive',
         sum(p.get('single_seed') is True for p in result['secondary']['parts'].values()) >= 8
         and result['secondary']['expected_inconclusive'] == ['every EESM19 entry', 'every single-seed S entry'],
         'secondary.expected_inconclusive'),
    ]
    for name, ok, _ in items:
        require(ok, f'a required disclosure is missing: {name}')
    return [{'id': name, 'where': where} for name, _, where in items]


def limitations(handoff, boundaries):
    """The handoff's required limitations, verbatim; every protocol boundary and result boundary is among them."""
    block = handoff.split('## Required limitations', 1)[1].split('Literature anchors:', 1)[0]
    items = [ln[2:].strip() for ln in block.splitlines() if ln.startswith('- ')]
    require(len(items) == 19, f'{len(items)} required limitations, not 19')
    for b in boundaries['protocol'] + boundaries['added_by_results'] + [boundaries['route_boundary']]:
        require(b in items, f'a boundary is not among the required limitations: {b[:60]}')
    return items


# ---------------------------------------------------------------------------- the build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    route = manifest['route']
    require(manifest['release_id'] == RELEASE_ID and route['id'] == ROUTE, 'another release or route')
    approval = manifest['approval']
    require(approval['decision'] == 'aggregate_preview' and approval['date'] == manifest['reviewed_at'] == '2026-10-08',
            'no recorded approval for route 3')
    require(approval['candidateStatusAtSeal'] == CANDIDATE_STATUS, 'the approval names another candidate state')
    decisions = {d['id']: d for d in approval['ownerDecisions']}
    require(list(decisions) == ['D11', 'revision 4 and S0b-6', 'revision 5', 'results']
            and decisions['results']['date'] == '2026-10-08' and decisions['D11']['date'] == '2026-10-07',
            'the approval does not record the owner decisions')
    require(manifest['holds'] == [], 'route 3 has no hold')
    handoff, _ = pinned_text(route['handoff'], 'handoff')
    prior_art, _ = pinned_text(route['referenceCheck'], 'reference check')
    candidate, candidate_sha = pinned(route['releaseCandidate'], 'release candidate')
    require(candidate_sha in handoff, 'the handoff does not record the release candidate')
    files = {name: pinned(ref_of(route, key), name)[0] for name, key in PINNED.items()}
    texts = {name: pinned_text(ref_of(route, key), name)[0] for name, key in TEXT_PINS.items()}
    agg, protocol, s0 = bindings(route, candidate, files, texts, handoff)
    lists, lists_sha = wording_lists(agg, protocol, s0)
    files[LISTS] = lists
    refs = reresolve(candidate, files)
    REFERENCE_COUNTS.clear()
    REFERENCE_COUNTS.update(refs)
    a4 = files['audit-secondary-numeric.json']
    used = set()

    blocks, by_ref = primary(candidate, agg)
    fam, conj = family_sentences(candidate, blocks)
    margins = val(candidate['margins'], 'margins')
    require(margins['accuracy_pp'] == 2.0 and margins['P3_log_R_ratio'] == P3_RATIO, 'the margins are not the frozen ones')
    rules = inner(candidate['route_sentence_rule'], 'route sentence rules')
    boundaries_c = val(candidate['boundaries'], 'boundaries')
    boundaries = {'protocol': val(boundaries_c['protocol'], 'protocol boundaries'),
                  'route_boundary': val(boundaries_c['route_boundary'], 'route boundary'),
                  'added_by_results': boundaries_c['added_by_results'],
                  'multiplicity': val(boundaries_c['multiplicity'], 'multiplicity')}
    design_route = inner(agg['design']['route'], 'route')
    arms = inner(agg['design']['arms'], 'arms')
    encoders = inner(agg['design']['text_encoders_pinned'], 'text encoders')
    head = re.search(r'One head for every arm: [^\n]*?no early stopping\.', handoff)
    freeze = re.search(r'\*\*Freeze\.\*\* ([^\n]*)', handoff)
    require(head is not None and freeze is not None, 'the handoff does not state the head and the freeze')
    metric_note = 'Per-person accuracy is averaged equally over people; it compares set-ups and is not a deployment error rate.'
    require(metric_note in handoff, 'the handoff does not state the metric note')
    result = {
        'id': ROUTE,
        'title': candidate['title'],
        'run_id': RUN_ID,
        'route': {'site_text': design_route['site_text'], 'boundary': design_route['boundary'],
                  'origin': {'cite': VISUAL_JEV, 'url': candidate['route_origin']['url'], 'arxiv': '2609.25845',
                             'note': candidate['route_origin']['note']},
                  'jev_scope': JEV_SCOPE, 'independence': INDEPENDENCE},
        'design': {
            'unseen_definition': inner(agg['design']['unseen_definition'], 'unseen definition'),
            'question_forms': {k: {'vector': a['e_q'] or 'none: one output per seen question',
                                   **({'role': a['role']} if a.get('role') else {}),
                                   'can_ask_unseen': a['unseen']} for k, a in arms.items()},
            'head': head.group(0),
            'text_encoders': {k: {'repo': e['repo'], 'commit': e['commit'], 'licence': e['card_licence']}
                              for k, e in encoders.items()},
            'text_encoders_note': 'Frozen at pinned commits and never redistributed.',
            'margins': {'delta_pp': margins['accuracy_pp'], 'p3_ratio': margins['P3_log_R_ratio'],
                        'p3_definition': margins['P3_definition'], 'fixed': margins['fixed'],
                        'basis': margins['accuracy_basis']},
            'flags': val(candidate['wording_rule'], 'wording rule'),
            'route_sentence_rules': {k: rules[k] for k in ('always', 'margin_tested_entries', 'first_match_order',
                                                            'difference_only_entries', 'conjunctions')},
            'uncertainty': candidate['uncertainty_method'],
            'multiplicity': val(candidate['multiplicity'], 'multiplicity'),
            'expected_inconclusive': margins['expected_inconclusive'],
            'a2_note': margins['a2_note'],
            'metric_note': metric_note,
            'freeze': edit(freeze.group(1), used),
        },
        'key_findings': [],
        'route_answer': val(candidate['results']['primary']['route_answer'], 'route answer'),
        'primary': {'entries_count': PRIMARY_COUNT, 'multiplicity': candidate['results']['primary']['multiplicity_line'],
                    'blocks': blocks, 'family_sentences': fam, 'conjunction_rule': conj,
                    'display_edits': val(candidate['results']['primary']['display_edits'], 'display edits')},
        'descriptive': descriptive(candidate, agg),
        'pre_run_checks': pre_run_checks(candidate, agg, s0, a4, used),
        'secondary': secondary(candidate, margins['expected_inconclusive']),
        'boundaries': boundaries,
        'limitations': limitations(handoff, boundaries),
        'not_run': val(candidate['not_run'], 'not run'),
        'not_reported': val(candidate['not_reported'], 'not reported'),
        'deviations': [{'id': d['id'], 'what': edit(d['what'], used)} for d in val(candidate['deviations'], 'deviations')
                       if d['id'] != 'Gal4 mirror'],
        'audits': audits_block(candidate, files, route),
        'references': references(manifest, handoff, prior_art),
    }
    require(list(result['route_answer']) == ['rule', 'seen_training_wording_P1', 'rewording_P2', 'unseen_P3_P4_P5'],
            'the route answer is three parts, never pooled')
    result['required_disclosures'] = disclosures(result)
    smallest = min(boas_people(result))
    released_boas = json.loads((PROJECT / manifest['sources'][1]['released']['file']).read_bytes())
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'question': 'Can an EEG model be asked its questions in words, including ones it was never trained on?',
        'metric_units': ('Balanced accuracy, AUROC, flip rates and chance levels are proportions in [0,1], and so are '
                         'levels and descriptive contrasts. An entry with unit "difference of proportions" is the '
                         'language arm minus the reference (or the reworded minus the training wording), stored as a '
                         'proportion: multiply by 100 for percentage points, the unit the margin of 2 pp is in. Unit '
                         '"difference of AUROC" is a difference of AUROC. Unit "log R" is the natural log of R, the '
                         'head\'s remaining error (1 - AUROC) over the read-off\'s, and r gives R itself. Log loss is '
                         'mean binary cross-entropy in nats. Counts of people, seeds, fits, intervals and cells are '
                         'whole numbers.'),
        'scope': ('Route 3 of the decision-research roadmap: one question-conditioned head asked each question by a '
                  'question number, a label template or a description. Seen questions in their training wording, '
                  'rewordings and questions the EEG head was never trained on are separate results, never pooled. '
                  'Every figure compares set-ups; none is a deployment error rate. Every BOAS figure travels with the '
                  'three stated gaps and the attribution in boas_conditions. The wording lists, the held-out '
                  'partition and the derangements are in questions-in-language-wordings.json.'),
        'results': {ROUTE: result},
        'datasets': datasets(manifest),
        'boas_conditions': boas_conditions(candidate, released_boas, manifest['sources'][1], smallest),
        'status_only': [],
        'holds': [],
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'release_candidate_sha256': candidate_sha,
                       'wording_lists_sha256': lists_sha, 'wordings_file': 'questions-in-language-wordings.json',
                       'included': [ROUTE], 'inputs': [s['id'] for s in manifest['sources']], 'holds': []},
    }
    result['key_findings'] = key_findings(candidate, by_ref, handoff, list(numbers(payload)))
    payload['results'][ROUTE] = edited(result, used)     # the declared edits, wherever the carried text has them
    wordings = wordings_payload(manifest, sha(manifest_bytes), agg, lists, lists_sha, used)
    require(used == set(range(len(EDITS))), f'a declared text edit did not apply: {sorted(set(range(len(EDITS))) - used)}')
    for p in (payload, wordings):
        scrub_check(p)
        validate_public(p)
    check_not_published(payload, wordings, payload['not_published'])
    # Refused by value too: a withheld figure equal to a published one is a leak.
    # A withheld value that is also an audited figure (two rationals from small counts can coincide, as one S10 bound
    # does with the cohort's chance-corrected TPL u8 level) is published for the audited figure's sake, not leaked.
    published = set(figure_numbers(payload))
    audited = set(numbers(files['aggregate-primary.json']['blocks'])) | set(numbers(
        [files['aggregate-secondary.json'][k] for k in ('parts', 'primary_blocks_descriptive')])) | set(numbers(
        agg['primary_descriptive']['chance_corrected_levels']['value'])) | set(numbers(
        s0['numeracy_probe']['spearman_rho']))   # text-only, published by decision; 0.5628 is also a fit-check score
    leaked = sorted((withheld_values(agg, s0) - audited) & published)
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    for phrase in handoff_figures(result):
        require(phrase in handoff, f'the handoff does not state {phrase!r}')
    return payload, wordings


def audits_block(candidate, files, route):
    a1, a2 = files['audit-primary-conformance.json'], files['audit-primary-numeric.json']
    a3, a4 = files['audit-secondary-conformance.json'], files['audit-secondary-numeric.json']
    for name, a in (('A1', a1), ('A3', a3)):
        require(a['status'] == 'pass' and a['pass'] is True and a['checks_failed'] == 0
                and a['checks_total'] == len(a['checks']) and all(c['pass'] is True for c in a['checks']),
                f'conformance audit {name} did not pass')
    for name, a in (('A2', a2), ('A4', a4)):
        require(a['verdict'] == 'pass' and all(c['pass'] is True for c in a['checks'].values()),
                f'numerical audit {name} did not pass')
    m2 = re.match(r'(\d[\d,]*) comparisons, (\d+) of them numeric, 0 mismatches',
                  a2['checks']['metrics_contrasts_intervals_flags_sentences']['summary'])
    m4 = re.match(r'([\d,]+) comparisons, (\d+) outside tolerance, all explained \(D-1 to D-3\), 0 unexplained',
                  a4['verdict_note'])
    require(m2 is not None and m4 is not None, 'the numerical audits do not state their counts as read')
    groups = a2['checks']['metrics_contrasts_intervals_flags_sentences']['groups']
    require(sum(g['values_compared'] for g in groups.values()) == int(m2.group(2)), 'A2: the numeric count')
    require(len(a2['entries']) == PRIMARY_COUNT and all(e['difference_flag_match'] and e['margin_flag_match']
                                                       and e['rule_match'] and e['sentence_match'] and e['counts_match']
                                                       for e in a2['entries']), 'A2: an entry does not match')
    require(len(a4['entries']) == SECONDARY_ENTRY_COUNT and all(e['difference_flag_match'] and e['margin_flag_match']
                                                                 and e['rule_match'] and e['counts_match']
                                                                 for e in a4['entries']), 'A4: an entry does not match')
    summary = val(candidate['audits']['summary'], 'audit summary')
    whole = lambda s: int(s.replace(',', ''))
    for n in (a1['checks_total'], a3['checks_total'], whole(m2.group(1)), whole(m4.group(1))):
        require(f'{n:,}' in summary, f'the candidate\'s audit summary does not state {n:,}')
    return {
        'primary_conformance': {'sha256': route['independentAudits']['primaryConformance']['sha256'], 'verdict': 'pass',
                                'checks': a1['checks_total'], 'failed': 0},
        'primary_numeric': {'sha256': route['independentAudits']['primaryNumeric']['sha256'], 'verdict': 'pass',
                            'comparisons': whole(m2.group(1)), 'numeric_values': whole(m2.group(2)), 'mismatches': 0,
                            'entries_recomputed': len(a2['entries'])},
        'secondary_conformance': {'sha256': route['independentAudits']['secondaryConformance']['sha256'],
                                  'verdict': 'pass', 'checks': a3['checks_total'], 'failed': 0},
        'secondary_numeric': {'sha256': route['independentAudits']['secondaryNumeric']['sha256'], 'verdict': 'pass',
                              'comparisons': whole(m4.group(1)), 'outside_tolerance': whole(m4.group(2)),
                              'unexplained': 0, 'entries_recomputed': len(a4['entries'])},
        'summary': summary,
        'independence': 'The audits re-implement the definitions without importing the study\'s scoring modules.',
        'not_audited': ('The S10 per-frequency and interior-only breakdowns were self-checked at stage 3 and are not '
                        'covered by an independent audit; they are not published.'),
    }


def wordings_payload(manifest, manifest_sha, agg, lists, lists_sha, used):
    """The second file: the wording lists, the held-out partition and the derangements, as publishable text."""
    pad = agg['partition_and_derangements']
    grid = inner(pad['grid_hz'], 'grid')
    partition = inner(pad['partition'], 'partition')
    s8 = inner(pad['s8_heldout_hz'], 'S8 band')
    require(len(grid) == 40 and grid == sorted(grid) and grid[0] == 8.0 and grid[-1] == 15.8, 'the frequency grid')
    held = [f for r in partition.values() for f in r]
    require(sorted(held) == grid and all(len(r) == 8 for r in partition.values()) and list(partition) == list('01234'),
            'the partition: five rotations of 8, every grid frequency held out once')
    for r, fs in partition.items():
        steps = sorted(round(f * 5) for f in fs)
        require(all(b - a > 1 for a, b in zip(steps, steps[1:])), f'rotation {r}: two adjacent held-out frequencies')
        require(sorted(int(f) for f in fs) == list(range(8, 16)), f'rotation {r}: one per integer band')
    require(len(s8) == 8 and s8 == grid[-8:], 'S8: the contiguous top band')
    der = pad['derangements']
    sleep_d, mi_d, ssvep_d = (inner(der[k], k) for k in ('sleep', 'mi', 'ssvep_s10'))
    for name, d in (('sleep', sleep_d), ('mi', mi_d)):
        for seed, m in d.items():
            require(sorted(m) == sorted(m.values()) and all(k != v for k, v in m.items()), f'{name} {seed}: not a derangement')
    require(len(ssvep_d) == 15, 'SSVEP: 15 derangements (5 rotations x 3 seeds)')
    for key, m in ssvep_d.items():
        rot = key.split('/')[0]
        seen = sorted(f'{f:.1f}' for f in grid if f not in partition[rot])
        require(sorted(m) == seen == sorted(m.values()), f'SSVEP {key}: not a permutation of the seen frequencies')
        require(min(abs(float(k) - float(v)) for k, v in m.items()) > 1.0 - 1e-9, f'SSVEP {key}: within 1.0 Hz')
    num = inner(pad['num_code'], 'NUM code')
    require(num['dims'] == 1 + len(num['bump_centres']) == 23, 'the NUM code has 23 dimensions')
    w = agg['wordings']
    encoders = inner(agg['design']['text_encoders_pinned'], 'text encoders')
    return {
        'schema_version': WORDINGS_SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'license': 'CC BY 4.0',
        'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
        'scope': ('The wordings route 3 asked its questions with, the held-out frequency partition and the declared '
                  'derangements of the shuffled control, published with its results. Text only: no EEG, no score.'),
        'authoring': inner(w['authoring'], 'authoring'),
        'note': w['note'],
        'kinds': inner(w['kinds'], 'kinds'),
        'leakage_rules': inner(w['leakage_rules'], 'leakage rules'),
        'leakage_checks_passed_before_the_first_fit': True,
        'texts': 787,
        'lists': lists,
        'frequency_grid_hz': grid,
        'held_out_partition_hz': {f'rotation {r}': fs for r, fs in partition.items()},
        'partition_constraints': inner(pad['constraints'], 'constraints'),
        'partition_why_not_uniform': inner(pad['why_not_uniform'], 'why not uniform'),
        's8_held_out_band_hz': s8,
        'derangements': {'sleep_by_seed': sleep_d, 'motor_imagery_by_seed': mi_d,
                         'ssvep_s10_by_rotation_and_seed_index': ssvep_d,
                         'rules': shuf_rules(inner(der['rules'], 'derangement rules'), sleep_d)},
        'num_code': num,
        'text_encoders': {k: {'repo': e['repo'], 'commit': e['commit'], 'licence': e['card_licence'],
                              'pooling': e['pooling'], 'parameters': e['params']} for k, e in encoders.items()},
        'text_encoders_note': 'Frozen at pinned commits and never redistributed.',
        'provenance': {'manifest_sha256': manifest_sha, 'wording_lists_sha256': lists_sha},
    }


def shuf_rules(r, sleep_d):
    """How the shuffled control's derangements were chosen (protocol arms.SHUF), its sleep seeds the ones served."""
    require(r['sleep'] == {'rule': r['sleep']['rule'], **sleep_d} and r['timing'] == 'declared now, fixed at the freeze',
            'the SHUF rules are not the protocol\'s')
    return {'what': r['e_q'], 'role': r['role'], 'convention': r['convention'], 'sleep': r['sleep']['rule'],
            'motor_imagery': r['mi'], 'ssvep_s10': r['ssvep_S10'], 'declared': r['timing']}


# ---------------------------------------------------------------------------- outputs
def input_refs(manifest):
    route = manifest['route']
    refs = [route['handoff'], route['releaseCandidate'], route['referenceCheck']]
    refs += [ref_of(route, k) for k in PINNED.values()] + [ref_of(route, k) for k in TEXT_PINS.values()]
    return refs


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialize(payload):
    return (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()


def serialized_export():
    """The two served files' bytes: the results and the wordings."""
    payload, wordings = build(MANIFEST.read_bytes())
    return serialize(payload), serialize(wordings)


def export():
    data, wording_data = serialized_export()
    for out in OUTPUTS:
        out.write_bytes(data)
    for out in WORDING_OUTPUTS:
        out.write_bytes(wording_data)
    # The audit is a separate program: it reads these bytes and the pinned files, and nothing of build().
    import audit_questions_in_language_export
    return audit_questions_in_language_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
