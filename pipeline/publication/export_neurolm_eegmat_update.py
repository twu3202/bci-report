"""Release the NeuroLM EEGMAT frozen-feature pilot, aggregate-only, as a separate panel on the pilot studies page.

NeuroLM-B stays frozen. One fixed ridge head is fitted on each of three representations of the same 2,160 two-second
EEGMAT windows from 36 people (tokenizer features, band power, GPT hidden states), in five participant-held-out folds,
and scored as equal-person means with paired participant-bootstrap differences. The research session approved the
aggregate handoff; the owner's decision D1 of 2026-10-19 publishes it on the site. It sits outside the pilot count and
every leaderboard, in its own file: mvp.json, the arithmetic-rest files, the further-encoder CSVs, eegpt-core-update.json
and pilot-studies-update.json keep their bytes.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- the scores and paired differences from the approved export, only if the research release record and the delivery
  verification bind those bytes, the readings verified the same hash and the same numbers, and the export equals the
  producer aggregate that the interpretation review pins and the independent numerical audit checked;
- the feature dimensions from the frozen protocol; the parameter count from the strict-restore receipt of the smoke
  evidence, as the initial validation review and the handoff state it (the unrendered legacy models.json is never read);
- the licences per part from the preflight record, its LICENSE file the one the protocol and the acquisition receipt
  hash, and the readings' statement of them; the dataset's rights from its released core-matrix record;
- the exposure facts from the pinned NeuroLM source, the preflight and the checkpoint-stage inspection;
- the core protocol facts that put this pilot in its own panel from the core run's pinned dataset and engine protocols
  and runner.
The research records carry private storage paths, so they are pinned and checked, never published.

What this export refuses:
- per-person, per-fold and per-window values, fold assignments, labels, features, heads, predictions, timings and
  memory, by key and by fragment, and the measured compute by value; private paths, host, volume and user names (read
  at run time from the pinned records that carry them, never spelled here);
- a score or interval other than the approved one, an interval that does not hold its estimate, a figure of a core
  EEGMAT row, a resolved exposure or another licence than the pinned records state;
- a version label, an update marker or a month used as a label in the text, Jev, the commenter's figure, any ICLR 2027
  or submission reference, MIT beside the checkpoint, and a claim these results do not support unless it is negated.

    python3 pipeline/publication/export_neurolm_eegmat_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'neurolm-eegmat-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'neurolm-eegmat-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/neurolm-eegmat-update.json',
           PROJECT / 'site/public/data/neurolm-eegmat-update.json')
RELEASE_ID = 'neurolm-eegmat-update-20261020'
SCHEMA = 'bci-report-neurolm-eegmat-update-v1'
RESEARCH_ROOT = 'research/iclr_bci_expansion_20261016/'
SOURCE_KEY = 'neurolm-eegmat'

# The arms in the order of the handoff's table, with the labels the site uses (the export's own names).
ARMS = (('tokenizer_mean', 'tokenizer features'), ('log_bandpower', 'band power'), ('gpt_mean', 'GPT hidden states'))
CONTRASTS = (('tokenizer_mean', 'log_bandpower', 'question', 'tokenizer-minus-band-power',
              'tokenizer features minus band power'),
             ('gpt_mean', 'tokenizer_mean', 'descriptive', 'gpt-minus-tokenizer', 'GPT hidden states minus tokenizer features'),
             ('gpt_mean', 'log_bandpower', 'descriptive', 'gpt-minus-band-power', 'GPT hidden states minus band power'))
METRICS = ('balanced_accuracy', 'macro_f1')
# Every research file the release record must bind, by the key this manifest gives it.
APPROVED = ('export', 'protocol', 'producer', 'numericalAudit', 'numericalAuditReview', 'interpretationReview',
            'executionReview', 'handoff')
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')          # the pilot-studies sentence, reused as the plan requires
TOL = 1e-12

REFUSED_KEYS = PER_PERSON_KEYS | {
    'minimum', 'maximum', 'range', 'q1', 'q3', 'p10', 'p90', 'seconds', 'elapsed_seconds', 'peak_rss_bytes',
    'cpu_threads', 'batch_size', 'address_space_bytes', 'reserve_bytes', 'checks', 'seal', 'source_files', 'splits',
    'labels_file', 'run_directory', 'expected_root', 'input_manifest_path'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_class', 'subject', 'prediction', 'probabilit', 'threshold', 'feature', 'confusion',
                         'percentile', 'quantile', 'median', 'elapsed', 'timing', 'wall', 'rss', 'memory', 'device',
                         'platform', 'environment', 'private', 'path', 'host', 'folder', 'worker', 'lock')
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\bSubject\d+|\.(?:npz|npy|edf|mat|md|py)\b'
                        r'|(?<![\w-])(?:summary|independent-audit|dataset-protocol|engine-protocol|eegmat-probe-protocol'
                        r'|eegmat-input-manifest|eegmat-aggregate-pending-audit|neurolm-preflight'
                        r'|checkpoint-stage-inspection|independent-numerical-attempt\d+)\.json', re.IGNORECASE)
TRIVIAL = {0.0, 0.5, 1.0, 2.0}
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
COMMENTER = re.compile(r'(?<![\d.,])55(?:\.0+)?\s*(?:%|per ?cent|percent)|\b0\.55\b', re.IGNORECASE)
SUBMISSIONS = re.compile(r'ICLR\s*2027|\bsubmission', re.IGNORECASE)
CLAIMS = re.compile(r'outperform|\bbeats?\b|\bimprov|superior|\bbetter\b|\badvantage|\bharm|instruction[- ]tuned'
                    r'|question[- ]answer|zero-shot|\bunseen\b|never saw|\bcausal|cognitive workload|\bclinical\b'
                    r'|\bmedical\b|\bonline\b|real-time|closed-loop|\bendorse|equivalen|significan'
                    r'|state[- ]of[- ]the[- ]art|\bbest\b|\bwinner|\branks?\b|\branked\b|\branking\b|leaderboard',
                    re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none|nothing|outside)\b|n't\b", re.IGNORECASE)
# The released EEGMAT record, copied as it is (it carries a review date and month names of its own).
VERBATIM = re.compile(r'^\$\.rights\.dataset\.(?:name|source|version|license|licenseUrl|attribution|privacyReview'
                      r'|reviewedAt|reviewBasis|rightsScope)\b')
RIGHTS_FIELDS = ('source', 'version', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'reviewedAt',
                 'reviewBasis', 'rightsScope')


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


def signed(v):
    """A fraction as signed percentage points with two decimals and a true minus sign, as the site prints them."""
    return f'{100 * v:+.2f}'.replace('-', '−')


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
    if ref['path'].endswith('.json'):
        return json.loads(raw)
    return raw.decode('utf-8')


def paper_record(rs):
    entries = [p for p in rs['paperRecord']['opportunities'] if p['id'] == 'neurolm']
    require(len(entries) == 1, 'the paper record has no single NeuroLM entry')
    return entries[0]


def research_name(ref):
    """The path the research session's own records use: relative to its folder."""
    require(RESEARCH_ROOT in ref['path'], f'{Path(ref["path"]).name}: outside the research folder')
    return ref['path'].split(RESEARCH_ROOT, 1)[1]


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {}
    for group in ('research', 'planning', 'published', 'core'):
        docs[group] = {k: read_pinned(r, k) for k, r in manifest[group].items() if isinstance(r, dict)}
    docs['owner'] = read_pinned(manifest['approval']['ownerDecisions'], 'owner decisions')
    return docs


def private_names(docs):
    """The user, project, host and volume names the private records use, read from them, never spelled in this file."""
    rs = docs['research']
    text = json.dumps(rs['protocol']) + json.dumps(rs['smokeEvidence']['root'])
    names = {n for pair in re.findall(r'/home/([^/\s"]+)/([^/\s"]+)/', text) for n in pair}
    names |= {n for pair in re.findall(r'/Volumes/([^/\s"]+)/([^/\s"]+)', text) for n in pair}
    handoff = rs['handoff']
    for pattern in (r'(\w+) was not mounted', r'on both Mac and (\w+)', r'on (\w+) CPU with'):
        m = re.search(pattern, handoff)
        require(m is not None, f'the handoff no longer names its hosts ({pattern})')
        names.add(m.group(1))
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- the bindings
def readings_entry(docs, manifest):
    entry = next((e for e in docs['planning']['readings'] if e['id'] == manifest['planning']['readings']['entry']), None)
    require(entry is not None, 'the readings have no entry for this pilot')
    return entry['result']


def bindings(docs, manifest):
    """The approved export is the file the research release, its delivery check and the readings name."""
    rs, rm = docs['research'], manifest['research']
    owner = docs['owner']
    require(owner['freeze_date'] == manifest['freeze_date'].replace('-', '') == RELEASE_ID.rsplit('-', 1)[1],
            'the freeze date is not the release id’s')
    stated(owner['decisions']['D1']['answer'], 'the NeuroLM EEGMAT pilot panel', 'owner decision D1')
    rel = rs['releaseRecord']
    require(rel['status'] == 'approved_for_aggregate_pilot_handoff' and rel['overall_leaderboard_eligible'] is False
            and rel['private_data_release_authorized'] is False and rel['website_published_by_this_chat'] is False
            and rel['protocol_unchanged_since_scoring'] is True, 'the research release record changed')
    for key in APPROVED:
        name = research_name(rm[key])
        require(rel['approved_files'].get(name) == rm[key]['sha256'],
                f'{key}: not the file the research release approves')
    dv = rs['deliveryVerification']
    require(dv['status'] == 'audited_handoff_ready' and dv['release_hashes_verified'] is True
            and dv['aggregate_fields_match_immutable_producer'] is True, 'the delivery verification did not pass')
    for key in ('releaseRecord', 'export', 'handoff', 'numericalAuditReview'):
        require(dv['files'].get(research_name(rm[key])) == rm[key]['sha256'], f'{key}: not the delivered file')
    # The readings verified the same two hashes.
    r = readings_entry(docs, manifest)
    require(r['status'] == 'release_ready', 'the readings do not find the pilot release-ready')
    asset = next(a for a in r['files_for_public_assets'] if a['path'].endswith('/' + Path(rm['export']['path']).name))
    require(asset['matches'] is True and asset['sha256_actual'] == rm['export']['sha256']
            and asset['sha256_claimed'].startswith(rm['export']['sha256']), 'the readings verified another export')
    auth = next(a for a in r['release_authority'] if a['path'].endswith('/' + Path(rm['releaseRecord']['path']).name))
    require(auth['matches'] is True and auth['sha256_actual'] == rm['releaseRecord']['sha256'],
            'the readings verified another release record')
    # The reviews' own pins.
    stated(rs['interpretationReview'], f'| Pending aggregate JSON | `{rm["pendingAggregate"]["sha256"]}` |', 'interpretation review')
    stated(rs['interpretationReview'], 'no unresolved material interpretation blocker', 'interpretation review')
    stated(rs['numericalAuditReview'], f'`{rm["numericalAudit"]["sha256"]}`', 'numerical audit review')
    stated(rs['numericalAuditReview'], 'no remaining numerical blocker', 'numerical audit review')
    stated(rs['executionReview'], 'no unresolved critical implementation blocker', 'execution review')
    sd = {f['path']: f['sha256'] for f in rs['smokeDelivery']['files']}
    require(sd.get(research_name(rm['smokeEvidence'])) == rm['smokeEvidence']['sha256'],
            'the smoke evidence is not the delivered receipt')
    require(rs['advancementCheck']['files'].get(research_name(rm['stageInspection'])) == rm['stageInspection']['sha256'],
            'the stage inspection is not the recorded receipt')
    stated(rs['maskExecutionAudit'], f'`{rm["stageInspection"]["sha256"]}`', 'mask execution audit')
    receipt = {x['name']: x for x in rs['sourceReceipt']}
    for key, name in (('instructionSource', 'train_instruction.py'), ('downstreamSource', 'downstream_dataset.py')):
        require(receipt[name]['sha256'] == rm[key]['sha256'] and receipt[name]['returncode'] == 0
                and '/0cda9876d8ce6ee07ed0c43eee5e9a6f5c24b177/' in receipt[name]['url'],
                f'{name}: not the pinned upstream source')
    return r


def audited_values(docs, readings):
    """Scores and paired differences: the approved export, equal to the audited producer aggregate and the readings."""
    rs = docs['research']
    src, pending, protocol, audit = rs['export'], rs['pendingAggregate'], rs['protocol'], rs['numericalAudit']
    require(src['status'] == 'independently_audited_aggregate_pilot' and src['independent_numerical_audit'] is True
            and src['overall_leaderboard_eligible'] is False and src['new_dataset_count_increment'] == 0
            and src['foundation_parameters_frozen'] is True and src['text_generation_used'] is False,
            'the approved export is not a frozen, audited aggregate pilot')
    require(src['protocol_sha256'] == docs['_refs']['protocol']['sha256'], 'the export names another protocol')
    require(src['aggregate'] == pending['aggregate'] and src['paired_contrasts'] == pending['paired_contrasts']
            and src['participants'] == pending['participants'] and src['windows'] == pending['windows']
            and src['sealed_predictions_sha256'] == pending['sealed_predictions_sha256'],
            'the approved export differs from the audited producer aggregate')
    for k in ('protocol_sha256', 'checkpoint_sha256', 'code_revision', 'checkpoint_revision', 'implementation_sha256'):
        require(pending['binding'][k] == audit['binding'][k], f'the audit checked another {k}')
    require(pending['binding']['protocol_sha256'] == src['protocol_sha256']
            and pending['binding']['checkpoint_sha256'] == src['checkpoint_sha256'], 'the aggregate binds other files')
    require(audit['status'] == 'passed' and audit['outcome'] == 'independent_sealed_numerical_audit_passed'
            and audit['paired_bootstrap_match'] is True and audit['all_refit_predictions_exact'] is True
            and audit['all_saved_decisions_reconstructed'] is True and audit['linear_refits_completed'] == 15
            and audit['producer_imported'] is False and audit['group_disjointness_verified'] is True
            and audit['exact_OOF_coverage_verified'] is True and audit['scaler_training_rows_only_verified'] is True,
            'the independent numerical audit did not pass')
    diffs = audit['numerical_max_absolute_differences']
    require(all(0.0 <= v <= audit['tolerances']['metric_absolute'] for v in diffs.values()), 'an audit difference')
    require(set(src['aggregate']) == {a for a, _ in ARMS}, 'the export has other arms')
    pairs = {(c['a'], c['b']): c for c in src['paired_contrasts']}
    require(set(pairs) == {(a, b) for a, b, *_ in CONTRASTS} and len(pairs) == len(src['paired_contrasts']),
            'the export has other contrasts')
    require(protocol['metrics']['paired_bootstrap']['contrasts'] == [[c['a'], c['b']] for c in src['paired_contrasts']],
            'the contrasts are not the protocol’s')
    arms = {}
    for a, _ in ARMS:
        x = src['aggregate'][a]
        ba, f1 = x['equal_person_balanced_accuracy'], x['equal_person_macro_f1']
        require(number(ba) and number(f1) and 0 <= ba <= 1 and 0 <= f1 <= 1 and set(x) == {
            'equal_person_balanced_accuracy', 'equal_person_macro_f1'}, f'{a}: not a pair of proportions')
        arms[a] = {'balanced_accuracy': ba, 'macro_f1': f1}
    contrasts = {}
    for a, b, *_ in CONTRASTS:
        c = pairs[(a, b)]
        require(c['metric_order'] == list(METRICS) and len(c['estimate']) == len(c['interval95']) == 2,
                f'{a} - {b}: another metric order')
        out = {}
        for i, m in enumerate(METRICS):
            est, (lo, hi) = c['estimate'][i], c['interval95'][i]
            require(all(number(v) for v in (est, lo, hi)) and -1 <= lo <= est <= hi <= 1,
                    f'{a} - {b} {m}: the interval does not hold its estimate')
            close_to = arms[a][m] - arms[b][m]
            require(abs(close_to - est) <= TOL, f'{a} - {b} {m}: the estimate is not the difference of the arms')
            out[m] = {'difference': est, 'interval_95': [lo, hi]}
        contrasts[(a, b)] = out
    # Every figure is one the readings verified, digit for digit.
    verified = set()
    for n in readings['public_numbers']:
        for field in ('value', 'interval'):
            verified |= {float(t) for t in re.findall(r'[-+]?\d+\.\d+(?:e-?\d+)?', n.get(field, ''))}
    published = [v for x in arms.values() for v in x.values()]
    published += [v for c in contrasts.values() for m in c.values() for v in [m['difference'], *m['interval_95']]]
    missing = [v for v in published if v not in verified]
    require(not missing, f'figures the readings did not verify: {missing[:3]}')
    return src, arms, contrasts


# ---------------------------------------------------------------------------- the blocks
def cohort_block(docs, readings):
    rs = docs['research']
    src, protocol, audit = rs['export'], rs['protocol'], rs['numericalAudit']
    data, adapter, split = protocol['data'], protocol['adapter'], protocol['split']
    cov = audit['coverage']
    people, records, windows = src['participants'], src['condition_records'], src['windows']
    require(people == data['people'] == cov['subjects'] and records == data['edf_records'] == cov['condition_records']
            and windows == data['windows'] == cov['windows'], 'the cohort counts disagree')
    require(records == 2 * people and windows == records * adapter['windows_per_record']
            and adapter['windows_per_record'] * adapter['window_seconds'] == adapter['retained_record_seconds'],
            'the windows do not follow from the recordings')
    require(src['channels'] == len(data['channels']) == len(set(data['channels'])), 'another montage')
    require(src['folds'] == split['fold_count'] == len(cov['fold_participants']) and sum(cov['fold_participants']) == people,
            'the folds do not cover the cohort')
    stated(split['rule'], 'Whole-participant held-out', 'fold rule')
    stated(split['rule'], 'fold=index modulo5', 'fold rule')
    stated(src['split'], 'sorted subject index modulo five', 'fold rule')
    sizes = '/'.join(map(str, cov['fold_participants']))
    require(any(n['value'].startswith(f'{sizes} participants') for n in readings['public_numbers']),
            'the readings verified other fold sizes')
    stated(data['label_rule'], '_1 ->0pre-task-rest; _2 ->1mental-arithmetic', 'labels')
    stated(data['label_rule'], 'Not participant count-quality grouping', 'labels')
    require(src['sampling_rate_hz'] == adapter['output_sfreq_hz'] and src['window_seconds'] == adapter['window_seconds'],
            'the export and the protocol give other windows')
    return {
        'dataset': 'EEGMAT', 'name': 'EEG During Mental Arithmetic Tasks', 'version': '1.0.0',
        'source': 'https://physionet.org/content/eegmat/1.0.0/',
        'people': people, 'recordings': records, 'conditions': records // people,
        'retained_seconds': adapter['retained_record_seconds'], 'window_seconds': adapter['window_seconds'],
        'windows_per_recording': adapter['windows_per_record'], 'windows': windows,
        'channels': src['channels'], 'channel_names': list(data['channels']),
        'source_sampling_hz': adapter['input_sfreq_hz'], 'sampling_hz': adapter['output_sfreq_hz'],
        'folds': src['folds'], 'fold_sizes_people': list(cov['fold_participants']),
        'split': ('whole participants held out: participants sorted and assigned to a fold by index modulo five, so no '
                  'person is in training and test of the same fold'),
        'labels': ('the recording condition in the file name, pre-task rest against serial subtraction; the '
                   'participants’ count-quality groups are left unused'),
        'classes': ['pre-task rest', 'mental arithmetic'],
    }


def model_block(docs, readings):
    rs = docs['research']
    src, smoke, stage, pre = rs['export'], rs['smokeEvidence'], rs['stageInspection'], rs['preflight']
    s3 = smoke['files']['smoke-attempt-03.json']
    sr = s3['strict_restore']
    require(s3['status'] == 'passed' and sr['missing_keys'] == 0 and sr['unexpected_keys'] == 0
            and sr['model_state_keys'] == s3['checkpoint_state']['keys'], 'the strict restore did not pass')
    params = sr['parameters']
    require(isinstance(params, int) and s3['checkpoint_state']['tensor_bytes'] == 4 * params,
            'the restored parameters and the float32 state disagree')
    require(s3['checkpoint']['sha256'] == src['checkpoint_sha256'] == stage['checkpoint_sha256']
            and s3['checkpoint']['hash_verified'] is True and s3['hf_revision'] == src['checkpoint_revision']
            and s3['code_revision'] == rs['protocol']['code_revision'], 'the smoke test restored another checkpoint')
    stated(rs['initialValidationReview'], f'{params:,} model parameters', 'initial validation review')
    stated(rs['handoff'], f'The pinned {params:,}-parameter NeuroLM checkpoint was strictly restored', 'handoff')
    pn = next(n for n in readings['public_numbers'] if n['label'].startswith('NeuroLM-B parameters'))
    require(int(pn['value'].replace(',', '')) == params, 'the readings verified another parameter count')
    require(s3['model_args'] == stage['model_args'], 'the smoke test and the stage inspection read other model arguments')
    args = stage['model_args']
    ck = next(f for f in pre['hf']['checkpoint_files'] if f['path'] == 'checkpoints/NeuroLM-B.pt')
    require(ck['sha256_publisher_lfs'] == src['checkpoint_sha256'] == rs['protocol']['checkpoint']['sha256']
            and ck['bytes'] == rs['protocol']['checkpoint']['bytes'] == s3['checkpoint']['bytes'],
            'the preflight lists another checkpoint')
    require(pre['hf']['repo_id'] == 'Weibang/NeuroLM' and pre['hf']['revision'] == src['checkpoint_revision']
            and pre['code']['revision'] == src['sources'][2]['url'].rsplit('/', 1)[1]
            and src['sources'][3]['url'].endswith(f'/Weibang/NeuroLM/tree/{src["checkpoint_revision"]}'),
            'the preflight names another repository or revision')
    paper = paper_record(rs)
    require(paper['year'] == 2025 and paper['venue_status'].startswith('ICLR 2025 conference paper confirmed')
            and 'https://openreview.net/forum?id=Io9yFt7XH7' in paper['sources']
            and paper['weights_url'] == 'https://huggingface.co/Weibang/NeuroLM'
            and paper['code_url'] == pre['code']['repo'], 'the paper record changed')
    blob = json.dumps(readings, ensure_ascii=False)
    stated(blob, 'Jiang et al., ICLR 2025', 'readings citation')
    stated(blob, 'https://arxiv.org/abs/2409.00101', 'readings arXiv link')
    feats = rs['protocol']['features']
    stated(feats['gpt_mean']['forward_boundary'], 'No logits computed/used', 'GPT boundary')
    require(feats['gpt_mean']['call_counts_per_batch']['LM_head'] == 0
            and rs['protocol']['science_gate']['generation_or_LM_class_logits'] is False, 'the language-model head ran')
    return {
        'id': 'neurolm-b', 'name': 'NeuroLM-B', 'family': 'foundation',
        'paper_title': paper['title'], 'paper_venue': 'ICLR 2025', 'citation': 'Jiang et al., ICLR 2025',
        'paper': 'https://openreview.net/forum?id=Io9yFt7XH7', 'paper_arxiv': 'https://arxiv.org/abs/2409.00101',
        'repository': pre['code']['repo'], 'source_revision': pre['code']['revision'],
        'source_url': src['sources'][2]['url'],
        'checkpoint': {'file': ck['path'], 'repository': f'https://huggingface.co/{pre["hf"]["repo_id"]}',
                       'revision': src['checkpoint_revision'], 'sha256': src['checkpoint_sha256'], 'bytes': ck['bytes'],
                       'url': src['sources'][3]['url']},
        'parameters': params,
        'restored_state_entries': sr['model_state_keys'],
        'parameters_basis': 'a strict restore of the checkpoint, every state entry present and none unexpected',
        'architecture': {'layers': args['n_layer'], 'heads': args['n_head'], 'width': args['n_embd'],
                         'context_tokens': args['block_size']},
        'frozen': True, 'fine_tuning': False, 'text_generation': False, 'language_model_head': False,
        'transfer': 'supervised: the frozen NeuroLM outputs feed a linear head trained on the other folds’ labels',
        'weights_distributed': False,
        'weights_note': 'no weights are distributed; the SHA-256 identifies the checkpoint used and grants nothing',
        'endorsement': 'none implied',
    }


def exposure_block(docs):
    rs = docs['research']
    pre, stage, smoke = rs['preflight'], rs['stageInspection'], rs['smokeEvidence']
    names = pre['exposure']['pretraining_dataset_names']
    require(not any(re.search(r'eegmat|mental arithmetic|workload', n, re.I) for n in names),
            'EEGMAT is in the published pretraining list; the exposure must be reviewed')
    tasks = list(pre['instruction_tasks'])
    require(tasks == ['TUAB', 'TUEV', 'SEED', 'HMC', 'Workload', 'TUSL'], 'another instruction task list')
    stated(rs['instructionSource'], f"for name in {tasks!r}", 'instruction tasks in the pinned code')
    stated(rs['instructionSource'], "elif downstream_dataset == 'Workload':", 'Workload in the pinned code')
    stated(rs['downstreamSource'], 'class WorkloadLoader(Dataset):', 'Workload loader in the pinned code')
    stated(rs['executionReview'], 'EEGMAT/Workload is a named NeuroLM downstream task', 'execution review')
    require(pre['hf']['instruction_tuned_checkpoint_verified'] is False
            and smoke['files']['smoke-attempt-03.json']['instruction_tuned_checkpoint_verified'] is False,
            'instruction tuning is no longer unverified; the exposure must be reviewed')
    cfg = stage['selected_config']
    require(stage['status'] == 'inspected' and stage['training_steps_performed'] == 0 and cfg['eval_only'] is False,
            'another stage inspection')
    lr = cfg['learning_rate']
    stated(rs['maskExecutionAudit'], f'epoch {stage["epoch"]}, iteration {stage["iteration"]:,}, `init_from='
                                     f'{cfg["init_from"]}`, learning rate {lr:.4f}', 'mask execution audit')
    stated(rs['maskExecutionAudit'], 'Consistent with pretraining configuration; instruction tuning unverified',
           'mask execution audit')
    stated(rs['handoff'], 'Checkpoint metadata is **consistent with pretraining; instruction tuning remains unverified**',
           'handoff')
    require(pre['exposure']['source'].startswith('https://proceedings.iclr.cc/paper_files/paper/2025/'),
            'the pretraining list comes from another source')
    return {
        'status': 'unknown',
        'status_vocabulary': ['exposed', 'not_exposed', 'unknown'],
        'checked_on': pre['checked_date'],
        'published_pretraining_list': {'datasets': len(names), 'includes_eegmat': False,
                                       'source': pre['exposure']['source']},
        'instruction_tasks': tasks,
        'eegmat_instruction_task': 'Workload',
        'checkpoint_stage': {'status': 'unknown', 'checkpoint_epoch': stage['epoch'], 'iteration': stage['iteration'],
                             'initialised_from': cfg['init_from'], 'learning_rate': lr,
                             'instruction_tuning_verified': False},
    }


def adapter_block(docs):
    rs = docs['research']
    ad, pre = rs['protocol']['adapter'], rs['preflight']['input']
    f, rp = ad['filter'], ad['resample']
    require(ad['new_declared_adapter'] is True and ad['historical_preprocessing_identical'] is False,
            'the adapter is not the declared new one')
    require(f['kind'] == 'Butterworth bandpass' and f['zero_phase_offline'] is True and 'sosfiltfilt' in f['implementation'],
            'another filter')
    require(ad['input_sfreq_hz'] * rp['up'] / rp['down'] == ad['output_sfreq_hz'] == pre['sample_rate_hz'],
            'the resampling does not reach NeuroLM’s rate')
    require(ad['notch'].startswith('none') and pre['notch_hz'] == [50, 60], 'the notch facts changed')
    stated(rs['handoff'], 'No additional notch filter is applied.', 'handoff')
    require(pre['amplitude_divisor'] == 100 and 'divide by100 for NeuroLM' in ad['units'], 'another amplitude scale')
    stated(ad['window_demean'], 'per-channel mean subtraction', 'demeaning')
    stated(ad['patch_order'], 'time-major then channel-major;2one-second blocks x19channels=38patches', 'patches')
    return {
        'own_adapter': True,
        'source_sampling_hz': ad['input_sfreq_hz'], 'sampling_hz': ad['output_sfreq_hz'],
        'resample': {'up': rp['up'], 'down': rp['down']},
        'band_pass_hz': [f['low_hz'], f['high_hz']], 'filter_order': f['order'], 'zero_phase': True, 'offline': True,
        'filter': 'Butterworth band-pass, applied forward and backward over the retained minute',
        'notch': False, 'official_notch_hz': list(pre['notch_hz']),
        'demean': 'per channel in each two-second window',
        'units': 'microvolts, divided by 100 for NeuroLM; band power uses the microvolt windows',
        'amplitude_divisor': pre['amplitude_divisor'],
        'window_patches': 38, 'patch_seconds': 1, 'patch_order': 'time-major, then channel',
    }


def arms_block(docs, arms):
    feats = docs['research']['protocol']['features']
    bp = feats['log_bandpower']
    channels = len(docs['research']['protocol']['data']['channels'])
    require(bp['dimension'] == channels * len(bp['bands_hz']) and bp['flatten'] == 'channel-major then band-major',
            'the band-power dimension is not channels by bands')
    require(feats['tokenizer_mean']['dimension'] == feats['gpt_mean']['dimension']
            == docs['research']['stageInspection']['model_args']['n_embd'], 'the NeuroLM dimensions are not its width')
    stated(feats['tokenizer_mean']['definition'], 'Mean over38valid pretrained tokenizer encoder hidden states', 'tokenizer')
    stated(feats['gpt_mean']['definition'], 'Mean over38EEG-only final GPT transformer ln_f hidden states', 'GPT')
    bands = [list(b) for b in bp['bands_hz']]
    require(bands == [[1, 4], [4, 8], [8, 13], [13, 30], [30, 75]] and bp['sampling_rate_hz'] == 200
            and bp['welch']['window'] == 'hann' and bp['welch']['nperseg'] == 200, 'another band-power definition')
    definitions = {
        'tokenizer_mean': ('the mean of NeuroLM-B’s 38 tokenizer hidden states per window (two one-second blocks of 19 '
                           'channels), taken before its vocabulary projection'),
        'log_bandpower': ('95 absolute log band powers: 19 channels by 5 bands (1–4, 4–8, 8–13, 13–30 and 30–75 Hz), '
                          'Welch with a one-second Hann window at 200 Hz on the same windows'),
        'gpt_mean': ('the mean of the 38 final normalised GPT hidden states from the same EEG-only forward pass, which '
                     'stops before the language-model head'),
    }
    out = []
    for a, label in ARMS:
        out.append({'id': a, 'label': label, 'dimension': feats[a]['dimension'], 'definition': definitions[a],
                    'balanced_accuracy': arms[a]['balanced_accuracy'], 'macro_f1': arms[a]['macro_f1'],
                    'interval_95': None})
    return out, bands


def contrasts_block(contrasts):
    out = []
    for a, b, role, cid, label in CONTRASTS:
        entry = {'id': cid, 'a': a, 'b': b, 'label': label, 'role': role}
        for m in METRICS:
            c = contrasts[(a, b)][m]
            lo, hi = c['interval_95']
            spans = lo <= 0 <= hi
            if spans:
                reading = SPANS_ZERO
            else:
                reading = f'the interval lies {"below" if hi < 0 else "above"} zero; descriptive, from this one cohort'
            entry[m] = {'difference': c['difference'], 'interval_95': [lo, hi], 'interval_includes_zero': spans,
                        'reading': reading}
        out.append(entry)
    q = out[0]['balanced_accuracy']
    require(q['interval_includes_zero'] is True, 'the question’s interval no longer spans zero; the reading must be reviewed')
    return out


def probe_block(docs):
    rs = docs['research']
    probe = rs['protocol']['probe']
    m = re.fullmatch(r'RidgeClassifier\(alpha=(\d+),solver=(\w+),class_weight=(\w+),fit_intercept=True,tol=1e-4\)',
                     probe['pipeline'][1])
    require(m is not None and probe['pipeline'][0] == 'StandardScaler fit on training windows only'
            and probe['fits'] == len(ARMS) * rs['protocol']['split']['fold_count'] and probe['all_final_no_hpo'] is True,
            'another probe')
    stated(rs['export']['probe'], 'RidgeClassifier alpha=100, balanced weights, Cholesky solver; 15 fixed fits; no HPO',
           'probe')
    stated(probe['labels'], 'separate score-label file first read by scorer after prediction manifest sealed', 'sealing')
    return {'scaler': 'StandardScaler fitted on training windows only', 'head': 'RidgeClassifier',
            'alpha': int(m.group(1)), 'solver': m.group(2), 'class_weight': m.group(3), 'fits': probe['fits'],
            'hyperparameter_search': False, 'sealed_before_scoring': True}


def interval_block(docs):
    rs = docs['research']
    bs, pb = rs['export']['bootstrap'], rs['protocol']['metrics']['paired_bootstrap']
    require(bs == {'unit': 'participant', 'resamples': pb['resamples'], 'seed': pb['seed'], 'fixed_fits': True}
            and pb['unit'] == 'participant' and pb['interval_percentiles'] == [2.5, 97.5]
            and pb['same_resamples_all_contrasts'] is True, 'another bootstrap')
    stated(rs['handoff'], 'condition on these fixed fitted models. They do not include model-refit uncertainty',
           'handoff')
    return {'kind': 'paired participant bootstrap', 'method': 'percentile interval', 'level': 0.95,
            'unit': 'participant', 'resamples': bs['resamples'], 'seed': bs['seed'],
            'same_resamples_all_contrasts': True, 'fixed_fits': True, 'arms': 'point estimates only'}


def chance_block(docs):
    m = re.search(r'Binary balanced-accuracy chance is (\d+)%\. Macro-F1 has no single universal chance value\.',
                  docs['research']['handoff'])
    require(m is not None, 'the handoff no longer states the chance levels')
    return {'balanced_accuracy': int(m.group(1)) / 100, 'macro_f1': None}


def core_block(docs, manifest, cohort, probe, bands):
    """The facts that put this pilot in its own panel, from the core run's pinned protocols and runner."""
    core, cm = docs['core'], manifest['core']
    run = core['manifest']['runs']['arithmetic-rest']
    require(run['datasetProtocol'] == {'path': cm['datasetProtocol']['path'], 'sha256': cm['datasetProtocol']['sha256']}
            and run['engineProtocol'] == {'path': cm['engineProtocol']['path'], 'sha256': cm['engineProtocol']['sha256']}
            and core['manifest']['code']['parallelRunner']['sha256'] == cm['runner']['sha256'],
            'not the core run the EEGPT core release pins')
    track = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    require(track['protocolSha'] == cm['datasetProtocol']['sha256'], 'the core track publishes another protocol')
    dp, ep, runner = core['datasetProtocol'], core['engineProtocol'], core['runner']
    require(dp['dataset_id'] == 'physionet-eegmat-1.0.0' and [c.upper() for c in dp['channels']] == cohort['channel_names']
            and dp['window_seconds'] == cohort['window_seconds'] and dp['fold_count'] == cohort['folds']
            and dp['sfreq'] == cohort['source_sampling_hz'], 'the core protocol has another montage or windows')
    stated(dp['preprocessing'], 'First 60 s of each recording; 30 contiguous nonoverlapping 2 s windows', 'core windows')
    stated(dp['preprocessing'], "subtract each channel's window mean; no rejection, filtering, resampling", 'core windows')
    stated(ep['native_to_canonical'], 'resample_poly to250Hz; no additional filtering', 'core engine')
    require(ep['ridge'] == {'alpha': float(probe['alpha']), 'solver': probe['solver'], 'class_weight': probe['class_weight'],
                            'scaler': 'training-only StandardScaler'}, 'the core head differs')
    stated(runner, "'fold_assignment':'sorted subject index modulo fold_count'", 'core fold rule')
    stated(runner, "'spectral':'Welch at250Hz, nperseg=min500,T, half overlap; log relative PSD0.5-45Hz", 'core spectra')
    stated(runner, 'z=psd[...,(f>=.5)&(f<=45)];z=z/np.maximum(z.sum(-1,keepdims=True),1e-30)', 'core spectra')
    stated(track['limitation'], 'Published signals were already cleaned with ICA', 'ICA')
    require(bands[0][0] == 1 and bands[-1][1] == 75, 'the pilot bands changed')
    return {
        'page': '/protocols/arithmetic-rest/',
        'shared_windows': True, 'shared_channels': True, 'shared_fold_rule': True, 'shared_head': True,
        'core_band_pass': False, 'core_sampling_hz': 250,
        'core_spectral_ridge': {'kind': 'log relative spectrum', 'band_hz': [0.5, 45], 'sampling_hz': 250},
        'pilot_band_power': {'kind': 'absolute log band power', 'band_hz': [bands[0][0], bands[-1][1]],
                             'sampling_hz': cohort['sampling_hz']},
    }


def rights_block(docs, readings):
    rs = docs['research']
    pre, src = rs['preflight'], rs['export']
    track = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    record = {'name': track['dataset']}
    record.update({k: track[k] for k in RIGHTS_FIELDS})
    norm = lambda s: re.sub(r'\bv(?=\d)', '', s)
    require(record['rightsScope'] == 'Personal noncommercial research; aggregate results only'
            and norm(src['sources'][0]['license']) == record['license'] == 'Open Data Commons Attribution License 1.0'
            and src['sources'][0]['url'] == record['source'], 'the EEGMAT record differs from the export’s source')
    # Code: MIT, the LICENSE file the protocol and the acquisition receipt hash.
    lic = next(f for f in pre['minimal_assets']['source_files'] if f['path'] == 'LICENSE')
    acq = next(a for run in rs['smokeEvidence']['files'].values() if isinstance(run, dict) and run.get('status') == 'complete'
               for a in run.get('assets', []) if a['path'] == 'source/LICENSE')
    require(pre['code']['license'] == 'MIT' and lic['sha256_measured'] == rs['protocol']['source_sha256']['LICENSE']
            == acq['sha256'] and acq['status'] == 'verified_download', 'the code licence is not the pinned MIT file')
    # Checkpoint: the Hugging Face metadata tag, a 30-byte card, public and ungated.
    hf = pre['hf']
    require(hf['license_metadata'] == 'cc-by-4.0' and hf['card_bytes'] == 30 and hf['gated'] is False
            and hf['private'] is False, 'the checkpoint’s stated licence changed')
    caveats = ' '.join(readings['required_caveats'])
    stated(caveats, 'NeuroLM code is MIT at 0cda987.', 'readings')
    stated(caveats, 'The NeuroLM-B checkpoint is CC BY 4.0 per its Hugging Face metadata at eddfff5, and its 30-byte card '
                    'adds no terms text. No weights are distributed.', 'readings')
    paper = paper_record(rs)
    require(paper['licenses']['code'] == 'MIT' and paper['licenses']['weights'].startswith('CC BY 4.0 in HF metadata'),
            'the paper record states other licences')
    record['published_here'] = (
        'Reused unchanged from the review of the same recordings for the core matrix. Published here for NeuroLM’s frozen '
        'features: equal-person balanced accuracy and macro-F1 of three representations, three paired differences with '
        'their participant-bootstrap intervals, and cohort counts; no per-person, per-fold or per-window value.')
    code_url = f'{pre["code"]["repo"]}/blob/{pre["code"]["revision"]}/LICENSE'
    stated(json.dumps(readings), code_url, 'readings code licence link')
    return {
        'dataset': record,
        'code': {'licence': 'MIT', 'scope': 'NeuroLM’s source code at the pinned commit', 'url': code_url,
                 'licence_file_sha256': lic['sha256_measured']},
        'checkpoint': {'licence': 'CC BY 4.0', 'licence_url': 'https://creativecommons.org/licenses/by/4.0/',
                       'as_stated_by': 'the licence tag in the Hugging Face repository metadata at the pinned revision',
                       'model_card_bytes': hf['card_bytes'], 'model_card_terms': False, 'gated': False,
                       'checked_on': pre['checked_date'], 'weights_distributed': False},
        'summary': ('EEGMAT 1.0.0: Open Data Commons Attribution License 1.0 (Zyma et al., 2019; PhysioNet). NeuroLM code: '
                    'MIT. NeuroLM-B checkpoint: CC BY 4.0 per its Hugging Face metadata; no weights distributed.'),
    }


def audits_block(docs, manifest):
    rs, rm = docs['research'], manifest['research']
    a = rs['numericalAudit']
    require(a['foundation_checkpoint_loads'] == 0 and a['raw_edf_reads'] == 0, 'the audit re-extracted features')
    stated(rs['handoff'], 'This does not independently regenerate foundation features', 'handoff')
    return {
        'independent_numerical_audit': {
            'status': 'passed', 'artifacts_hash_verified': a['unique_artifacts_hash_verified'],
            'refits': a['linear_refits_completed'], 'refits_exact': True, 'saved_decisions_reconstructed': True,
            'bootstrap_max_abs_difference': a['numerical_max_absolute_differences']['manual_paired_interval'],
            'checkpoint_loads': a['foundation_checkpoint_loads'], 'sha256': rm['numericalAudit']['sha256']},
        'reviews': {'execution': rm['executionReview']['sha256'], 'numerical_audit': rm['numericalAuditReview']['sha256'],
                    'interpretation': rm['interpretationReview']['sha256']},
        'boundary': ('The independent audit refitted all 15 heads from the sealed NeuroLM and band-power values and '
                     'reproduced every score and interval; the NeuroLM features themselves were not re-extracted by a '
                     'second implementation.'),
    }


LIMITATIONS = (
    ('exposure',
     'EEGMAT is NeuroLM’s Workload task, one of the six instruction tasks in its pinned code, and the training stage of '
     'this checkpoint is unresolved: its metadata (epoch {epoch}, iteration {iteration:,}, initialised from GPT-2, '
     'learning rate {lr}) fits a pretraining checkpoint, and instruction tuning is unverified. The backbone may have seen '
     'these people, so exposure is shown as unknown.'),
    ('adapter',
     'This pilot has its own offline adapter: a fourth-order zero-phase Butterworth band-pass at 0.1–75 Hz, resampling '
     'from 500 to 200 Hz, per-window demeaning, microvolts divided by 100 for NeuroLM, and no notch filter, where '
     'NeuroLM’s own pipeline adds a 50/60 Hz notch. The core Arithmetic & rest protocol filters nothing and resamples to '
     '250 Hz, so these scores have their own panel.'),
    ('band-power',
     'The band-power arm is 95 absolute log band powers (19 channels by 5 bands, 1–75 Hz, Welch at 200 Hz), a different '
     'feature set from the core matrix’s Spectral ridge row, which uses log relative spectra from 0.5–45 Hz at 250 Hz.'),
    ('recording-order',
     'Rest is recorded before the task, so recording order moves with the label, and the pilot does not isolate '
     'cognitive workload.'),
    ('capacity',
     'The 95 band-power and 768 NeuroLM dimensions share one fixed alpha, which does not equalise capacity or effective '
     'regularisation.'),
    ('random-initialisation',
     'There is no random-initialisation control, so the pilot says nothing about a causal benefit of pretraining.'),
    ('interval',
     'Intervals come from 1,000 participant resamples of the 15 fixed fitted heads and exclude refit uncertainty. Each '
     'arm has a point estimate only.'),
    ('development-cohort',
     'EEGMAT is a known development cohort, used across this site. Predictions were sealed before scoring for procedural '
     'integrity: the labels are in the file names, and each person’s windows train the heads of the other folds.'),
    ('ica',
     'The source README reports prior ICA cleaning of the published signals.'),
    ('scope',
     'Frozen features with a supervised linear head: no text prompt, generated answer or language-model output entered '
     'any score, and nothing here measures instruction tuning, question answering, zero-shot use, cognitive workload, '
     'clinical use or online decoding.'),
)


def limitations_block(exposure, adapter, cohort, arms, interval, probe):
    """The caveats, each once, with every figure in them checked against the blocks it comes from."""
    st = exposure['checkpoint_stage']
    require(adapter['band_pass_hz'] == [0.1, 75] and adapter['source_sampling_hz'] == 500 and adapter['sampling_hz'] == 200
            and adapter['filter_order'] == 4 and adapter['amplitude_divisor'] == 100
            and adapter['official_notch_hz'] == [50, 60], 'the adapter caveat no longer matches the protocol')
    dims = {a['id']: a['dimension'] for a in arms}
    require(dims == {'tokenizer_mean': 768, 'log_bandpower': 95, 'gpt_mean': 768} and cohort['channels'] == 19,
            'the dimension caveat no longer matches the protocol')
    require(interval['resamples'] == 1000 and probe['fits'] == 15 and len(exposure['instruction_tasks']) == 6,
            'the interval or task caveat no longer matches')
    lr = f'{st["learning_rate"]:.4f}'
    out = []
    for lid, text in LIMITATIONS:
        out.append({'id': lid, 'text': text.format(epoch=st['checkpoint_epoch'], iteration=st['iteration'], lr=lr)})
    return out


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
        require(not COMMENTER.search(text), f'{trail}: the commenter’s figure never appears')
        require(not SUBMISSIONS.search(text), f'{trail}: no ICLR 2027 or submission reference')
        if trail in ('$.schema_version', '$.release_id') or VERBATIM.match(trail):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):   # the release record is dated by design (/releases/, /data-use/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail.startswith(('$.provenance', '$.release_record')) or re.search(r'(?:url|source|paper\w*)$', trail):
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if sentence.rstrip().endswith('?'):
                continue          # a question asserts nothing
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def licences_per_part(payload):
    """MIT is the code's, CC BY 4.0 the checkpoint's metadata tag; neither is stated for the other part."""
    r = payload['rights']
    require(r['code']['licence'] == 'MIT' and r['checkpoint']['licence'] == 'CC BY 4.0'
            and r['checkpoint']['weights_distributed'] is False and payload['model']['weights_distributed'] is False,
            'the licences per part changed')
    for trail, text in strings(payload):
        if trail.startswith(('$.rights.code.', '$.rights.checkpoint.')) or VERBATIM.match(trail):
            continue
        for sentence in re.split(r'(?<=[.;])\s+', text):
            if re.search(r'\bMIT\b', sentence):
                require(re.search(r'\bcode\b', sentence, re.I) and not re.search(r'checkpoint|weights', sentence, re.I),
                        f'{trail}: MIT not tied to the code alone: {sentence!r}')
            if 'CC BY 4.0' in sentence:
                require(re.search(r'checkpoint|metadata|Hugging Face', sentence)
                        and not re.search(r'\bcode\b', sentence, re.I),
                        f'{trail}: CC BY 4.0 not tied to the checkpoint’s metadata: {sentence!r}')


def core_values(docs):
    """Every figure of the core EEGMAT rows: none may reach this file (no matched comparison with them)."""
    track = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    out = set()
    for r in track['rows']:
        for v in (r['y'], r['x'], *r['interval']):
            out |= {v, v / 100}
    cell = next(c for c in docs['published']['eegptCore']['cells'] if c['protocol'] == 'arithmetic-rest')
    out |= {cell['balanced_accuracy'], cell['macro_f1'], *cell['interval_95']}
    return out - TRIVIAL


def withheld_values(docs):
    """Measured compute the sources hold: worker times, memory and run lengths, never published."""
    rs = docs['research']
    out = {float(x) for x in re.findall(r'(\d+\.\d+) seconds', rs['handoff'])}
    out |= {float(x) for x in re.findall(r'about (\d+\.\d+) GiB', rs['handoff'])}
    for run in rs['smokeEvidence']['files'].values():
        if isinstance(run, dict):
            out |= {run[k] for k in ('elapsed_seconds', 'peak_rss_bytes') if number(run.get(k))}
    out |= {rs['numericalAudit']['peak_rss_bytes'], rs['stageInspection']['elapsed_seconds']}
    out |= {v for k, v in rs['protocol']['limits'].items() if number(v) and v >= 10 ** 6}
    out |= {v for k, v in rs['numericalAudit']['limits'].items() if number(v) and v >= 10 ** 6}
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
    docs['_refs'] = manifest['research']
    readings = bindings(docs, manifest)
    src, arm_values, contrast_values = audited_values(docs, readings)
    cohort = cohort_block(docs, readings)
    model = model_block(docs, readings)
    exposure = exposure_block(docs)
    adapter = adapter_block(docs)
    arms, bands = arms_block(docs, arm_values)
    dims = next(n for n in readings['public_numbers'] if n['label'].startswith('Feature dimensions'))['value']
    require(dims.startswith(f'tokenizer {arms[0]["dimension"]}; GPT {arms[2]["dimension"]}; log-bandpower '
                            f'{arms[1]["dimension"]} ({cohort["channels"]} channels x {len(bands)} bands)'),
            'the readings verified other dimensions')
    probe = probe_block(docs)
    interval = interval_block(docs)
    contrasts = contrasts_block(contrast_values)
    core = core_block(docs, manifest, cohort, probe, bands)
    rights = rights_block(docs, readings)
    audits = audits_block(docs, manifest)
    limitations = limitations_block(exposure, adapter, cohort, arms, interval, probe)
    pilot = docs['published']['pilotStudies']
    require('neurolm' not in json.dumps(pilot).lower(), 'the released pilot file already names NeuroLM')
    require(not any('neurolm' in r['name'].lower() for t in docs['published']['coreMatrix']['tracks'] for r in t['rows']),
            'NeuroLM is already a core row')
    rr, rm = manifest['releaseRecord'], manifest['research']
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['freeze_date'],
        'status': 'aggregate_preview',
        'title': 'NeuroLM’s frozen features on arithmetic and rest',
        'question': 'Do NeuroLM’s frozen EEG features separate rest from mental arithmetic better than band power?',
        'display_track': src['display_track'],
        'placement': {
            'page': '/topics/pilot-studies/', 'anchor': 'neurolm-eegmat', 'pointer_from': '/protocols/arithmetic-rest/',
            'counted_in_pilots': False, 'leaderboard': False, 'core_matrix_row': False,
            'new_dataset_count': src['new_dataset_count_increment'], 'new_model_count': 0,
            'text': ('A separate panel on the pilot studies page, outside the pilot count and every leaderboard and '
                     'model ranking; the core Arithmetic & rest matrix keeps its rows.'),
        },
        'metric_units': ('balanced accuracy, macro-F1 and chance levels are proportions in [0,1], and paired differences '
                         'are differences of proportions: multiply by 100 for percent or percentage points; dimensions '
                         'and counts of people, recordings, windows, channels, folds, fits and resamples are whole numbers; '
                         'null means not computed, never zero'),
        'scope': ('NeuroLM-B stays frozen. One fixed ridge head (alpha 100) is fitted on each of three representations of '
                  'the same 2,160 two-second windows from 36 people, in five participant-held-out folds: 15 fits and no '
                  'tuning. Scores are equal-person means; the paired differences carry participant-bootstrap intervals.'),
        'cohort': cohort,
        'model': model,
        'pretraining_exposure': exposure,
        'adapter': adapter,
        'probe': probe,
        'arms': arms,
        'chance_level': chance_block(docs),
        'paired_contrasts': contrasts,
        'interval': interval,
        'separate_from_core': core,
        'rights': rights,
        'limitations': limitations,
        'audits': audits,
        'release_record': {
            'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
            'rights': rr['rights'], 'research_release': rr['researchRelease'],
            'research_release_status': docs['research']['releaseRecord']['status'], 'binding': rr['binding'],
        },
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {SOURCE_KEY: rm['export']['sha256']},
            'research_release_sha256': rm['releaseRecord']['sha256'],
            'protocol_sha256': rm['protocol']['sha256'],
            'numerical_audit_sha256': rm['numericalAudit']['sha256'],
            'released_files_unchanged': ['mvp.json', 'pilot-studies-update.json', 'eegpt-core-update.json'],
        },
    }
    # The scope sentence's figures are the cohort's and the probe's.
    require(cohort['windows'] == 2160 and cohort['people'] == 36 and cohort['folds'] == 5 and probe['alpha'] == 100,
            'the scope sentence no longer matches the cohort')
    require(model['parameters'] != 254 * 10 ** 6 and model['checkpoint']['repository'].startswith('https://huggingface.co/'),
            'a legacy NeuroLM fact reached the export')

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 3, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    licences_per_part(payload)
    validate_public(payload)
    published = set(numbers(payload))
    leaked = [v for v in withheld_values(docs) if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    crossed = [v for v in core_values(docs) if v in published]
    require(not crossed, f'a core EEGMAT figure reached the export: {crossed[:3]}')
    return payload


def inputs_available():
    """Whether the pinned inputs are on this machine. The research folders and the core run's evidence copies are
    local-only, so a clone checks the served file against the committed export audit's hash; only the maintainer's
    checkout re-derives it."""
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
    import audit_neurolm_eegmat_export
    return audit_neurolm_eegmat_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
