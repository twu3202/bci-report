"""Release the v9 foundation-model evaluation as aggregate-only JSON and per-protocol CSVs.

Eleven further EEG foundation models — sixteen encoder checkpoints — were run as
frozen probes on the eight core protocols with the published LaBraM and CBraMod
frozen-row recipe and only the encoder swapped (same windows, folds, heads and
scoring), and nine of them were adapted on EEGMAT with the 2026-10-01 recipe:
a frozen encoder with a trained head against rank-4 LoRA, five epochs, three
seeds. The new rows sit beside the core matrix in their own files. The released
matrix (experiments.json, the protocol files) keeps its bytes: a page that shows
a new row next to a core row reads both files at build time.

Its own publication boundary, as with every batch. The website input is the
release candidate. Every {value, src} block in it is re-resolved against the
pinned file it names — a group summary, the pretraining-exposure table, or a
released site file whose bytes must be unchanged; every frozen cell and
adaptation row is checked against the pinned aggregate; the six independent
audits are bound by the hashes the candidate, the audit status, the aggregate
and the handoff record, never opened, because they carry private storage paths;
and every figure is checked against the table of the handoff the owner approved.
What this export refuses:
- per-trial, per-person and per-fold values, features, timings, memory and
  environments, by key, and private paths or host names by value;
- a not-run cell turned into a number, an interval that does not hold its mean,
  a chance flag or overlap call the intervals do not support, a paired change
  whose people do not add up to the cohort, and a figure that is not the
  handoff's.

Two outputs, one content. foundation-models-update.json (proportions, as the
topic exports) and foundation-models-<protocol>.csv, one per protocol, whose
first 22 columns are the core results CSVs' columns in the same units (percent),
so a protocol table can stack a new row under a core row without converting.

    python3 pipeline/publication/export_foundation_models_update.py
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261004'
MANIFEST = REVIEW / 'foundation-models-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'foundation-models-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/foundation-models-update.json',
           PROJECT / 'site/public/data/foundation-models-update.json')
CSV_DIR = PROJECT / 'site/public/data'
# Released files the candidate points into: read, never written. Their bytes must be the ones the candidate names.
SITE_FILES = {'site/src/data/mvp.json': PROJECT / 'site/src/data/mvp.json',
              'site/src/data/adaptation-update.json': PROJECT / 'site/src/data/adaptation-update.json'}

RUN_DIR = 'research/fm_eval_v9_20261004/'
EVALUATION = 'foundation-models-v9'
CANDIDATE_ID = 'fm-eval-v9-20261004'
CANDIDATE_STATUS = 'pending user approval'   # the state the candidate was sealed in; the manifest is the approval
CHECKED_ON = '2026-10-04'

PROTOCOLS = ('mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target', 'semantic-target', 'sleep-scalp')
SCORED = tuple(p for p in PROTOCOLS if p != 'idle')
MATRIX = ('reve-base', 'reve-large', 'luna-base', 'luna-large', 'brainomni-base', 'codebrain', 'eegmamba',
          'steegformer-base', 'steegformer-large', 'eeg-fm-masking/mae-r9cm-L2', 'erp-fm-base', 'singlem', 'zuna')
ABLATION = ('eeg-fm-masking/mae-r9cm-L2', 'eeg-fm-masking/jepa-r9cm-L2', 'eeg-fm-masking/mae-rone-L1',
            'eeg-fm-masking/jepa-rone-L1')
# The three sibling checkpoints have no matrix row in the candidate; their names follow the paper-recommended one's.
SIBLING_NAMES = {'eeg-fm-masking/jepa-r9cm-L2': 'eeg-fm-masking JEPA (r=9 cm, L=2)',
                 'eeg-fm-masking/mae-rone-L1': 'eeg-fm-masking MAE (r=one channel, L=1)',
                 'eeg-fm-masking/jepa-rone-L1': 'eeg-fm-masking JEPA (r=one channel, L=1)'}
CHECKPOINTS = MATRIX + ABLATION[1:]
ADAPTED = ('reve-base', 'reve-large', 'luna-base', 'brainomni-base', 'codebrain', 'eegmamba', 'steegformer-base',
           'singlem', 'zuna')
NOT_RUN = {('brainomni-base', 'p300-target'), ('brainomni-base', 'semantic-target')}
EXPOSED = {('steegformer-base', 'beta-8ch'), ('steegformer-base', 'beta-4ch'), ('steegformer-large', 'beta-8ch'),
           ('steegformer-large', 'beta-4ch'), ('singlem', 'semantic-target')}
UNKNOWN_EXPOSURE = 'zuna'                    # every cell of this model
SIZE_PAIRS = (('reve-base', 'reve-large'), ('luna-base', 'luna-large'), ('steegformer-base', 'steegformer-large'))
EXPOSURE_MODEL = {'reve-base': 'reve-base', 'reve-large': 'reve-large', 'luna-base': 'luna', 'luna-large': 'luna',
                  'brainomni-base': 'brainomni', 'codebrain': 'codebrain', 'eegmamba': 'eegmamba',
                  'steegformer-base': 'st-eegformer', 'steegformer-large': 'st-eegformer', 'erp-fm-base': 'erp-fm',
                  'singlem': 'singlem', 'zuna': 'zuna-1.1', **{m: 'eeg-fm-masking' for m in ABLATION}}
EXPOSURE_DATASET = {'mi-rest': 'ds003810', 'idle': 'ds005342', 'beta-8ch': 'beta', 'beta-4ch': 'beta',
                    'arithmetic-rest': 'eegmat', 'p300-target': 'ds006593', 'semantic-target': 'ds005383',
                    'sleep-scalp': 'eesm19'}
EXPOSURE_TABLE_MODELS = ('st-eegformer', 'luna', 'zuna-1.1', 'reve-base', 'reve-large', 'codebrain', 'eegmamba',
                         'erp-fm', 'singlem', 'brainomni', 'eeg-fm-masking', 'labram', 'cbramod')
# The owner's wording decision (2026-10-04): a sourced statement, never a proof of no overlap.
EXPOSURE_STATEMENT = {
    'exposed': "in the authors' published pretraining list",
    'not_exposed': f"not in the authors' published pretraining list (checked {CHECKED_ON})",
    'unknown': 'unknown: the authors do not list their pretraining data closely enough to decide',
}
# The handoff's row labels, table by table.
HANDOFF_LABEL = {'reve-base': 'REVE Base', 'reve-large': 'REVE Large', 'luna-base': 'LUNA Base',
                 'luna-large': 'LUNA Large', 'brainomni-base': 'BrainOmni Base', 'codebrain': 'CodeBrain',
                 'eegmamba': 'EEGMamba', 'steegformer-base': 'ST-EEGFormer Base',
                 'steegformer-large': 'ST-EEGFormer Large', 'eeg-fm-masking/mae-r9cm-L2': 'eeg-fm-masking MAE 9cm/L2',
                 'eeg-fm-masking/jepa-r9cm-L2': 'eeg-fm-masking JEPA 9cm/L2 (ablation)',
                 'eeg-fm-masking/mae-rone-L1': 'eeg-fm-masking MAE one/L1 (ablation)',
                 'eeg-fm-masking/jepa-rone-L1': 'eeg-fm-masking JEPA one/L1 (ablation)', 'erp-fm-base': 'ERP-FM Base',
                 'singlem': 'SingLEM', 'zuna': 'ZUNA 1.1'}
HANDOFF_COLUMNS = ('mi-rest', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target', 'semantic-target', 'sleep-scalp')
SEEDS = (20260922, 20260923, 20260924)
EEGMAT_PEOPLE = 36
IDLE_TRIALS = 60
IDLE_PEOPLE = 4
AUDIT_GROUPS = ('reve', 'erp-fm', 'masking-steeg', 'cbramod-layout', 'positions', 'single-channel')
TOL = 1e-12

# Per-person, per-fold and per-trial values; timings, memory and environments; and what the pages leave out on purpose.
REFUSED_KEYS = PER_PERSON_KEYS | {'p10', 'p50', 'p90', 'q1', 'q3', 'minimum', 'maximum', 'range', 'features_sha256',
                                  'channels_used', 'contract', 'smoke_test', 'reproducibility', 'compute', 'deviations',
                                  'sensitivity_rows', 'sensitivity_no_mean_removal', 'v8_open_items',
                                  'overlaps_outside_core_datasets', 'audit_file', 'checks', 'notes_private', 'venv'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_fold', 'per_trial', 'per_class', 'percentile', 'median',
                         'participant_id', 'subject', 'prediction', 'probabilit', 'feature', 'private', 'elapsed',
                         'second', 'minute', 'timing', 'cuda', 'mib', 'rss', 'platform', 'environment', 'adapter',
                         'local_clone', 'basename', 'sensitivity', 'path')
# Path roots only: naming this operator's machines or volumes here would itself be the leak. The host and
# volume names are read at run time from the pinned inputs that record them (see `private_names`).
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/|\w:~/',
                            re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub-\d+|\bsubj\d+|\.npz\b|\.edf\b|\.private\b|DECISIONS\.md|summary\.json|contract\.json'
                        r'|audit\.json', re.IGNORECASE)

DESIGN = {
    'frozen_probe': ('Each encoder replaces LaBraM or CBraMod in the published frozen-row recipe, and nothing else '
                     'changes: the published 250 Hz microvolt windows and segments (1 s or 2 s; sleep as the mean of '
                     '15 two-second segments), the same participant-disjoint folds, the same heads (ridge, alpha 100, '
                     'on standardised training-fold features, class-balanced except on BETA; idle: a per-person '
                     'logistic head with a calibration-only threshold and a two-in-a-row trigger) and the same '
                     'scoring. Only recorded channels are fed: no interpolation, padding or learned upsampling. Each '
                     'input contract was written, and a label-free smoke test run, before any score; nothing was '
                     'selected on test folds.'),
    'adaptation': ('The 2026-10-01 EEGMAT recipe, unchanged: a frozen encoder with a trained linear head against '
                   'rank-4 LoRA (alpha 8) with the same head; AdamW, learning rate 1e-4, weight decay 0.01, five '
                   'epochs, batch 32, the final epoch scored, seeds 20260922, 20260923 and 20260924, the same five '
                   'participant-disjoint folds. A three-seed value is each person\'s mean over seeds, then the '
                   'equal-person mean. LoRA targets follow each architecture, so the LoRA budgets differ.'),
    'interval': ('Descriptive 95% participant bootstrap of the equal-participant mean (10,000 draws, published '
                 'seeds). It ignores cross-validation dependence and carries no multiplicity correction.'),
    'harness': ('Before any new score the shared harness reproduced the published LaBraM and CBraMod frozen rows and '
                'idle counts exactly, and all 45 published LaBraM EEGMAT adaptation fits.'),
    'reading_rule': ('Rows are grouped by family, never ranked. A row is called above or below another only when '
                     'their marginal 95% intervals do not overlap; the same people under different encoders are not '
                     'tested pairwise here. Balanced or class-matched designs are method comparisons, not detection, '
                     'false-alarm or latency estimates for real use.'),
    'chance': 'An interval that includes the protocol\'s chance level is flagged on its cell; idle has no chance level.',
    'not_run': 'A cell that was not run is null with its reason, never zero.',
}


# ---------------------------------------------------------------------------- helpers
def close(a, b, label, tol=TOL):
    require(isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float))
            and not isinstance(b, bool) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def finite(*values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def at(doc, pointer, label):
    node = doc
    for tok in pointer.split('/')[1:] if pointer else []:
        tok = tok.replace('~1', '/').replace('~0', '~')
        if isinstance(node, list):
            require(tok.isdigit() and int(tok) < len(node), f'{label}: a reference that does not resolve: {pointer}')
            node = node[int(tok)]
        else:
            require(isinstance(node, dict) and tok in node, f'{label}: a reference that does not resolve: {pointer}')
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


def proportion_interval(iv, point, label):
    require(isinstance(iv, list) and len(iv) == 2 and finite(*iv) and 0.0 <= iv[0] <= iv[1] <= 1.0,
            f'{label}: no two-sided interval in [0, 1]')
    require(finite(point) and iv[0] <= point <= iv[1], f'{label}: the interval does not contain its point')
    return [iv[0], iv[1]]


def percent(v):
    """A proportion in percent, as the CSVs carry it: 100 x v, rounded to 12 decimals.

    100 x 0.6325 is 63.24999999999999 in binary, which toFixed(1) prints as 63.2 where the handoff, like any
    decimal rounding of 63.25, prints 63.3. Twelve decimals are far below any printed precision and remove that
    artefact of the unit change; check_handoff confirms every printed figure.
    """
    return round(100 * v, 12)


def overlap(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def relation(new, ref):
    return 'above' if new[0] > ref[1] else 'below' if new[1] < ref[0] else 'overlap'


# ---------------------------------------------------------------------------- the chain of custody
def reresolve(candidate, files):
    """Every traced block of the candidate is its source file's value at that pointer, in the bytes it names."""
    seen = 0

    def source(src, trail):
        require(isinstance(src, dict) and {'file', 'sha256', 'pointer'} <= set(src), f'{trail}: an untraceable figure')
        name = Path(src['file']).name
        require((src['file'] in SITE_FILES or src['file'].startswith(RUN_DIR)) and name in files,
                f'{trail}: a reference into an unpinned file: {src["file"]}')
        digest, doc = files[name]
        require(src['sha256'] == digest, f'{trail}: {src["file"]} is named by another hash')
        return at(doc, src['pointer'], trail)

    def walk(node, trail):
        nonlocal seen
        if isinstance(node, dict):
            if 'src' in node and isinstance(node['src'], dict):
                target = source(node['src'], trail)
                if 'value' in node:
                    expected = target / 100 if node.get('derived') == 'site chanceLevel (percent) / 100' else target
                    require(same(node['value'], expected) if not isinstance(expected, float)
                            else finite(node['value']) and abs(node['value'] - expected) <= TOL,
                            f'{trail}: the value differs from {node["src"]["file"]}')
                elif 'status' in node:
                    require(node['status'] == target, f'{trail}: the exposure status differs from the table')
                    if 'confidence' in node:
                        cell = at(files[Path(node['src']['file']).name][1], node['src']['pointer'].rsplit('/', 1)[0], trail)
                        require(node['confidence'] == cell['confidence'] and node['lean'] == cell.get('lean'),
                                f'{trail}: the exposure confidence differs from the table')
                else:
                    require(same({k: node[k] for k in ('counts', 'protocol_flags')}, target)
                            and node['definition'] == files[Path(node['src']['file']).name][1]['definition'],
                            f'{trail}: the exposure summary differs from the table')
                seen += 1
            if 'ref_src' in node:
                ref = source(node['ref_src'], trail)
                require(isinstance(ref, list) and len(ref) == 2 and finite(*ref), f'{trail}: a reference row without an interval')
                seen += 1
            for k, v in node.items():
                if k not in ('src', 'ref_src'):
                    walk(v, f'{trail}/{k}')
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f'{trail}[{i}]')
    walk(candidate, '$')
    return seen


def bindings(manifest, candidate, aggregate, exposure, audit_status, harness, handoff, files):
    """The candidate, the aggregate and the handoff name the same files, audits and hashes as the manifest."""
    ev = manifest['evaluation']
    require(candidate['release_id'] == CANDIDATE_ID == ev['releaseCandidateId'], 'another release candidate')
    require(candidate['status'] == CANDIDATE_STATUS, 'the candidate is not in the state it was sealed in')
    require(candidate['aggregate_only'] is True, 'the candidate is not aggregate only')
    require(candidate['traceability']['aggregate_sha256'] == ev['aggregate']['sha256'],
            'the candidate names another aggregate')
    # The aggregate records every input by hash: each must be the pinned one, or the released site file as it is.
    recorded = {Path(i['file']).name: i['sha256'] for i in aggregate['inputs']}
    require(len(recorded) == len(aggregate['inputs']), 'the aggregate names two inputs alike')
    expected = {Path(ev[k]['path']).name: ev[k]['sha256'] for k in ('pretrainingExposure', 'auditStatus', 'harnessValidation')}
    expected.update({Path(r['path']).name: r['sha256'] for r in ev['summaries'].values()})
    expected.update({Path(name).name: files[Path(name).name][0] for name in SITE_FILES})
    require(recorded == expected, 'the aggregate was built from other inputs than the ones pinned here')
    # Each hash this chain rests on is recorded in the handoff the owner approved.
    for label, digest in [('release candidate', ev['releaseCandidate']['sha256']), ('aggregate', ev['aggregate']['sha256']),
                          ('pretraining exposure', ev['pretrainingExposure']['sha256']),
                          ('audit status', ev['auditStatus']['sha256']),
                          ('harness validation', ev['harnessValidation']['sha256']),
                          *[(f'{g} summary', r['sha256']) for g, r in ev['summaries'].items()],
                          *[(f'{g} audit', d) for g, d in ev['independentAudits']['groups'].items()]]:
        require(digest in handoff, f'the handoff does not record the {label} hash bound here')
    # Six independent audits, all passed with no defect, named alike by every record.
    bound = ev['independentAudits']['groups']
    require(list(bound) == list(AUDIT_GROUPS), 'other audit groups')
    status = {g['group']: g for g in audit_status['groups']}
    agg = {g['group']: g for g in aggregate['audit_status']}
    cand = {g['group']: g for g in candidate['audit']['groups']}
    require(set(status) == set(agg) == set(cand) == set(AUDIT_GROUPS), 'the records name other audit groups')
    require(candidate['audit']['all_groups_passed'] is True, 'not every audit group passed')
    for g in AUDIT_GROUPS:
        s, a, c = status[g], agg[g], cand[g]
        require(s['pass'] is True and s['defects'] == [] and a['pass'] is True and a['defects'] == []
                and c['pass'] is True and c['defects'] == 0, f'the {g} audit did not pass without defect')
        require(len(s['checks']) == a['n_checks'] and all(x['pass'] for x in s['checks']), f'the {g} audit failed a check')
        require(s['sha256'] == a['audit_sha256'] == c['audit_sha256'] == bound[g], f'the {g} audit is named by another hash')
        require(s['models'] == a['models'], f'the {g} audit covers other models')
    covered = [m for g in AUDIT_GROUPS for m in status[g]['models']]
    require(sorted(covered) == sorted(CHECKPOINTS), 'a checkpoint outside the audited groups')
    # Every summary is the one its group's audit read: the aggregate names it, by model, by the pinned hash.
    for m in aggregate['models']:
        require(m['summary_file']['sha256'] == recorded.get(Path(m['summary_file']['file']).name), f'{m["key"]}: another summary')
    require(harness['i_saved_features_reproduce_published']['all_pass'] is True
            and harness['ii_cbramod_reextracted_on_cuda']['all_pass'] is True
            and harness['iii_labram_adaptation_fold']['all_pass'] is True, 'the harness validation did not pass')
    fits = harness['extra_labram_all_45_fits']
    require(fits['frozen-ce'] == fits['published_frozen'] and fits['lora-r4'] == fits['published_lora_r4'],
            'the harness did not reproduce the published LaBraM adaptation')
    require(exposure['generated_on'] == CHECKED_ON and all(m['checked_on'] == CHECKED_ON for m in exposure['models']),
            'the exposure table was checked on another date')
    return {
        'all_groups_passed': True,
        'groups': [{'group': g, 'models': status[g]['models'], 'checks_passed': len(status[g]['checks']), 'passed': True,
                    'defects': 0, 'sha256': bound[g]} for g in AUDIT_GROUPS],
        'rule': ('Only groups whose independent audit passed are released; a group that failed would appear as not '
                 'passed, with no number.'),
        'note': ('Each auditor wrote its own code and imported nothing from the harness or the group\'s adapters. '
                 'The audits stay in the private run root and are bound by hash.'),
    }


def private_names(candidate, handoff):
    """The host and volume names the private records use, read from those records, never spelled in this file."""
    hosts = {g['audit_file'].split(':', 1)[0] for g in candidate['audit']['groups'] if ':' in g['audit_file']}
    volumes = set(re.findall(r'/Volumes/([^/\s`]+)/', handoff))
    return {n for n in hosts | volumes if len(n) >= 3}


# ---------------------------------------------------------------------------- the exposure limitation
CANDIDATE_EXPOSURE_LIMITATION = ('Pretraining exposure: ST-EEGFormer x BETA and SingLEM x semantic-target are exposed; '
                                 'ZUNA 1.1 is unknown on all core datasets; EEGMamba not exposed at medium confidence.')
EXPOSURE_LIMITATION = ('Pretraining exposure, as the authors\' published pretraining lists show it (checked 2026-10-04): '
                       'BETA is in ST-EEGFormer\'s list and TMNRED (semantic-target) in SingLEM\'s; ZUNA 1.1 publishes '
                       'no list, so it is unknown on all core datasets; EEGMamba\'s list is read from its official code, '
                       'with medium confidence. A dataset absent from a list is not proof that its recordings were '
                       'never seen.')


# ---------------------------------------------------------------------------- per cell
def exposure_of(block, model, protocol, table, label):
    cell = at(table, block['src']['pointer'].rsplit('/', 1)[0], label)
    require(cell['model'] == EXPOSURE_MODEL[model] and cell['dataset'] == EXPOSURE_DATASET[protocol]
            and protocol in cell['protocols'], f'{label}: the exposure points at another model or dataset')
    status = cell['status']
    want = 'unknown' if model == UNKNOWN_EXPOSURE else 'exposed' if (model, protocol) in EXPOSED else 'not_exposed'
    require(status == want, f'{label}: exposure {status}, expected {want}')
    out = {'status': status, 'confidence': cell['confidence'], 'statement': EXPOSURE_STATEMENT[status]}
    if cell.get('lean'):
        out['lean'] = cell['lean']
    return out


def frozen_cell(c, model, protocol, track, agg_cell, table):
    label = f'{model} {protocol}'
    require(c['model'] == model and c['protocol'] == protocol and c['aggregate_id'] == f'frozen:{model}:{protocol}',
            f'{label}: another cell')
    require(agg_cell['status'] == c['status'], f'{label}: the aggregate disagrees')
    exposure = exposure_of(c['exposure'], model, protocol, table, label)
    if (model, protocol) in NOT_RUN:
        require(c['status'] == 'not_run' and 'balanced_accuracy' not in c and c['reason']
                and agg_cell['reason']['value'] == c['reason'] and 'balanced_accuracy' not in agg_cell,
                f'{label}: not run, yet a figure')
        return {'model': model, 'protocol': protocol, 'status': 'not run', 'reason': c['reason'],
                'balanced_accuracy': None, 'exposure': exposure}
    require(c['status'] == 'complete' and agg_cell['audit'] == 'passed', f'{label}: {c["status"]}, not passed')
    channels = track['channels']
    require(agg_cell['n_channels']['value'] == channels, f'{label}: other channels than the protocol\'s')
    if protocol == 'idle':
        k = {key: c[key]['value'] for key in ('idle_false_trigger_trials', 'idle_trials', 'mi_detected_trials',
                                              'mi_trials', 'always_abstain_subjects', 'people')}
        require(k['idle_trials'] == IDLE_TRIALS and k['mi_trials'] == IDLE_TRIALS and k['people'] == IDLE_PEOPLE,
                f'{label}: another idle design')
        require(all(count(v) for v in k.values()) and 0 <= k['idle_false_trigger_trials'] <= IDLE_TRIALS
                and 0 <= k['mi_detected_trials'] <= IDLE_TRIALS and 0 <= k['always_abstain_subjects'] <= IDLE_PEOPLE,
                f'{label}: idle figures that are not counts')
        wba, auc = c['mean_window_balanced_accuracy']['value'], c['mean_window_auroc']['value']
        require(finite(wba, auc) and 0 <= wba <= 1 and 0 <= auc <= 1, f'{label}: window metrics outside [0, 1]')
        for key in ('idle_false_trigger_trials', 'mi_detected_trials', 'always_abstain_subjects'):
            require(agg_cell[key]['value'] == c[key]['value'], f'{label}: {key} differs from the aggregate')
        out = {'model': model, 'protocol': 'idle', 'status': 'complete', 'people': k['people'], 'channels': channels,
               'idle_false_activations': k['idle_false_trigger_trials'], 'idle_trials': k['idle_trials'],
               'commands_detected': k['mi_detected_trials'], 'command_trials': k['mi_trials'],
               'always_abstain_people': k['always_abstain_subjects'],
               'window_balanced_accuracy': wba, 'window_auroc': auc, 'exposure': exposure}
    else:
        ba, iv, f1 = c['balanced_accuracy']['value'], c['interval95']['value'], c['macro_f1']['value']
        people, trials = c['people']['value'], c['trials']['value']
        require(people == track['subjects'], f'{label}: another cohort')
        proportion_interval(iv, ba, label)
        require(finite(f1) and 0 <= f1 <= 1, f'{label}: macro F1 outside [0, 1]')
        for key in ('balanced_accuracy', 'interval95', 'macro_f1', 'people', 'trials'):
            require(same(agg_cell[key]['value'], c[key]['value']), f'{label}: {key} differs from the aggregate')
        chance = track['chanceLevel'] / 100
        close(c['chance_level']['value'], chance, f'{label}: chance')
        includes = iv[0] <= chance <= iv[1]
        require(c['interval_includes_chance']['value'] is includes, f'{label}: the chance flag does not follow the interval')
        require(agg_cell['interval_includes_chance']['value'] is includes, f'{label}: the aggregate\'s chance flag')
        out = {'model': model, 'protocol': protocol, 'status': 'complete', 'balanced_accuracy': ba,
               'interval_95': [iv[0], iv[1]], 'macro_f1': f1, 'people': people, 'trials': trials, 'channels': channels,
               'chance_level': chance, 'interval_includes_chance': includes, 'at_or_below_chance': ba <= chance,
               'exposure': exposure}
    if c.get('design_role'):
        out['design_role'] = c['design_role']
    if c.get('notes'):
        out['notes'] = list(c['notes'])
    return out


# ---------------------------------------------------------------------------- per section
def models_block(candidate, manifest):
    rows = candidate['matrix_rows']
    require([r['model'] for r in rows] == list(MATRIX), 'the candidate has other matrix rows')
    licences = {m: entry for entry in manifest['models'] for m in entry['ids']}
    require(sorted(licences) == sorted(CHECKPOINTS) and sum(len(e['ids']) for e in manifest['models']) == len(CHECKPOINTS),
            'the manifest does not review every checkpoint exactly once')
    families = {r['model']: r['input_family'] for r in candidate['topic_findings']['comparison_rows']['fewer_electrodes_beta']}
    out = []
    by_id = {r['model']: r for r in rows}
    for mid in CHECKPOINTS:
        if mid in by_id:
            r = by_id[mid]
            require(r['family'] == 'foundation' and r['mode'] == 'Frozen encoder + ridge head', f'{mid}: another family or mode')
            require(count(r['parameters_encoder']) and r['parameters_encoder'] > 0, f'{mid}: parameters')
            base = {k: r[k] for k in ('name', 'parameters_encoder', 'parameters_note', 'checkpoint_sha256', 'revision',
                                      'paper', 'weights_licence', 'licence_note', 'row_footnote')}
        else:
            mae = by_id[ABLATION[0]]
            require('identical architecture for all four checkpoints' in mae['parameters_note'], f'{mid}: another architecture')
            base = {'name': SIBLING_NAMES[mid], 'parameters_encoder': mae['parameters_encoder'],
                    'parameters_note': mae['parameters_note'], 'checkpoint_sha256': None, 'revision': None,
                    'paper': mae['paper'], 'weights_licence': mae['weights_licence'], 'licence_note': mae['licence_note'],
                    'row_footnote': ('A sibling of the paper-recommended checkpoint in the masking ablation: the '
                                     'same architecture, corpus and recipe, another masking framework or geometry.')}
        lic = licences[mid]
        require(base['weights_licence'].startswith(lic['weightsLicence']), f'{mid}: the weights licence is not the reviewed one')
        # The approval is the site owner's, as the Chinese pages and the manifest say it (review of 2026-10-05).
        require(base['weights_licence'].count('user-approved') <= 1, f'{mid}: the weights licence names the approval twice')
        base['weights_licence'] = base['weights_licence'].replace('user-approved', 'owner-approved')
        adaptation = next(a for a in candidate['eegmat_adaptation']['rows'] if a['model'] == mid)
        out.append({
            'id': mid, **base, 'family': 'foundation', 'input_family': families[mid],
            'panel': 'matrix' if mid in MATRIX else 'masking ablation',
            'masking_ablation': mid in ABLATION,
            'mode': 'Frozen encoder + ridge head', 'idle_mode': 'Frozen encoder + linear head',
            'adaptation': 'run' if adaptation['status'] == 'complete' else adaptation['reason'],
            'rights_review': lic['basis'],
        })
        require((adaptation['status'] == 'complete') is (mid in ADAPTED), f'{mid}: adaptation status')
    zuna = next(m for m in out if m['id'] == 'zuna')
    require('research use only, not for diagnosis or clinical use' in zuna['licence_note'],
            'ZUNA 1.1: the model card\'s research-use sentence must travel with its rows')
    return out


def adaptation_block(candidate, aggregate, frozen):
    a = candidate['eegmat_adaptation']
    agg = {r['id']: r for r in aggregate['adaptation_eegmat']}
    rows, not_run = [], []
    for r in a['rows']:
        mid = r['model']
        if r['status'] != 'complete':
            require(mid not in ADAPTED and r['reason'].startswith('not run by design'), f'{mid}: adaptation not run')
            not_run.append({'model': mid, 'reason': r['reason']})
            continue
        label = f'adaptation {mid}'
        g = agg[r['aggregate_id']]
        require(g['audit'] == 'passed' and g['status'] == 'complete', f'{label}: the aggregate row did not pass')
        arms = {}
        for arm in ('frozen-ce', 'lora-r4'):
            x = r['arms'][arm]
            mean, iv = x['balanced_accuracy_3seed']['value'], x['interval95']['value']
            proportion_interval(iv, mean, f'{label} {arm}')
            seeds = [(int(s), v['value']) for s, v in x['per_seed'].items()]
            require([s for s, _ in seeds] == list(SEEDS) and all(finite(v) for _, v in seeds), f'{label} {arm}: seeds')
            require(count(x['trainable_parameters']['value']), f'{label} {arm}: parameters')
            ga = g['arms'][arm]
            require(same(ga['balanced_accuracy_3seed']['value'], mean) and same(ga['interval95']['value'], iv),
                    f'{label} {arm}: differs from the aggregate')
            arms[arm] = {'balanced_accuracy': mean, 'interval_95': [iv[0], iv[1]],
                         'per_seed_means': [{'seed': s, 'mean': v} for s, v in seeds],
                         'trainable_parameters': x['trainable_parameters']['value']}
        p = r['paired_lora_minus_frozen']
        change, iv = p['mean_change']['value'], p['interval95']['value']
        require(finite(change, *iv) and iv[0] <= change <= iv[1], f'{label}: the paired interval does not hold its mean')
        close(change, arms['lora-r4']['balanced_accuracy'] - arms['frozen-ce']['balanced_accuracy'],
              f'{label}: the paired change is not the difference of the arms', 1e-9)
        h, hm, t = (p[k]['value'] for k in ('helped', 'harmed', 'tied'))
        require(all(count(v) for v in (h, hm, t)) and h + hm + t == EEGMAT_PEOPLE, f'{label}: helped + harmed + tied is not 36')
        excludes = iv[0] > 0 or iv[1] < 0
        require(p['interval_excludes_zero']['value'] is excludes, f'{label}: the zero flag does not follow the interval')
        ref = r['frozen_ridge_reference']
        cell = frozen[(mid, 'arithmetic-rest')]
        require(ref['balanced_accuracy']['value'] == cell['balanced_accuracy']
                and ref['interval95']['value'] == cell['interval_95'], f'{label}: the ridge reference is not the frozen cell')
        head, lora = arms['frozen-ce']['trainable_parameters'], arms['lora-r4']['trainable_parameters']
        require(lora > head, f'{label}: LoRA trains no more than the head')
        rows.append({'model': mid, 'exposure': {'status': r['exposure']['status'],
                                                 'statement': EXPOSURE_STATEMENT[r['exposure']['status']]},
                     'lora_targets': r['lora_targets'], 'arms': arms,
                     'lora_parameters': lora - head,
                     'paired_lora_minus_frozen': {'mean_change': change, 'interval_95': [iv[0], iv[1]],
                                                  'excludes_zero': excludes, 'helped': h, 'harmed': hm, 'tied': t},
                     'frozen_ridge_reference': {'balanced_accuracy': cell['balanced_accuracy'],
                                                'interval_95': cell['interval_95'],
                                                'note': 'the closed-form ridge readout of the frozen-probe table on the '
                                                        'same people and folds: another readout than the trained head'}})
        require(r['exposure']['status'] == frozen[(mid, 'arithmetic-rest')]['exposure']['status'], f'{label}: exposure')
    require([r['model'] for r in rows] == list(ADAPTED), 'other adapted models')
    pc = a['published_context']
    require(pc['source_release'] == 'adaptation-update-20261001', 'the LaBraM context is not the 2026-10-01 release')
    context = {'model': 'LaBraM', 'release': pc['source_release'], 'arms': {}}
    for arm, x in pc['arms'].items():
        mean, iv = x['balanced_accuracy_3seed']['value'], x['interval95']['value']
        proportion_interval(iv, mean, f'LaBraM {arm}')
        context['arms'][arm] = {'balanced_accuracy': mean, 'interval_95': [iv[0], iv[1]],
                                'trainable_parameters': x['trainable_parameters']['value']}
    require(list(context['arms']) == ['frozen', 'last-block', 'lora-r4'], 'the LaBraM context has other arms')
    lp = pc['paired_lora_minus_frozen']
    context['paired_lora_minus_frozen'] = {'mean_change': lp['mean_change']['value'], 'interval_95': lp['interval95']['value'],
                                           'helped': lp['helped']['value'], 'harmed': lp['harmed']['value'],
                                           'tied': lp['tied']['value']}
    require(sum(context['paired_lora_minus_frozen'][k] for k in ('helped', 'harmed', 'tied')) == EEGMAT_PEOPLE,
            'LaBraM: helped + harmed + tied is not 36')
    budgets = [r['lora_parameters'] for r in rows]
    return {
        'scope': ('One fixed five-epoch recipe on one task: not a matrix row, not a tuned ranking. Frozen ridge, '
                  'frozen encoder with a trained head and LoRA order the models differently on the same task, and '
                  'LoRA budgets differ across models.'),
        'people': EEGMAT_PEOPLE, 'outer_folds': 5, 'seeds': list(SEEDS), 'chance_level': 0.5,
        'lora_parameter_range': [min(budgets), max(budgets)],
        'published_context': context, 'rows': rows, 'not_run': not_run,
    }


def comparisons_block(candidate, cells, matrix):
    """Every comparison the pages may state, recomputed from the cells and checked against the candidate's."""
    cr = candidate['topic_findings']['comparison_rows']
    tracks = {t['id']: t for t in matrix['tracks']}
    pp = lambda d: round(100 * d, 2)
    # Large against base, on the same people: a descriptive difference of two marginal means, no paired test.
    sizes = []
    want = {(r['base'], r['protocol']): r for r in cr['base_vs_large']}
    for base, large in SIZE_PAIRS:
        for p in SCORED:
            b, l = cells[(base, p)], cells[(large, p)]
            d = l['balanced_accuracy'] - b['balanced_accuracy']
            o = overlap(b['interval_95'], l['interval_95'])
            w = want[(base, p)]
            require(w['large'] == large and abs(w['large_minus_base_pp'] - pp(d)) < 0.006
                    and w['marginal_intervals_overlap'] is o, f'{base} vs {large} {p}: the candidate says otherwise')
            sizes.append({'base': base, 'large': large, 'protocol': p, 'large_minus_base': d,
                          'marginal_intervals_overlap': o})
    # Eight to four BETA electrodes, every checkpoint.
    electrodes = []
    want = {r['model']: r for r in cr['fewer_electrodes_beta']}
    require(sorted(want) == sorted(CHECKPOINTS), 'the fewer-electrodes rows cover other models')
    for m in CHECKPOINTS:
        e8, e4 = cells[(m, 'beta-8ch')], cells[(m, 'beta-4ch')]
        d = e4['balanced_accuracy'] - e8['balanced_accuracy']
        w = want[m]
        require(w['beta8_ba'] == e8['balanced_accuracy'] and w['beta4_ba'] == e4['balanced_accuracy']
                and abs(w['four_minus_eight_pp'] - pp(d)) < 0.006 and w['exposed'] == e8['exposure']['status'],
                f'{m}: the candidate\'s fewer-electrodes row says otherwise')
        electrodes.append({'model': m, 'input_family': w['input_family'], 'four_minus_eight': d,
                           'marginal_intervals_overlap': overlap(e8['interval_95'], e4['interval_95']),
                           'exposure': e8['exposure']['status']})
    # Against the published frozen LaBraM and CBraMod rows and the best published non-foundation row.
    refs = {}
    for p in SCORED:
        rows = tracks[p]['rows']
        best = max((r for r in rows if r['family'] != 'foundation'), key=lambda r: r['y'])
        refs[p] = {k: next(r for r in rows if r['id'] == k) for k in ('labram', 'cbramod')} | {'best_non_foundation': best}
    published = []
    want = {(r['model'], r['protocol']): r for r in cr['vs_published_rows']}
    for (m, p), c in cells.items():
        if p == 'idle' or c['status'] != 'complete':
            continue
        w = want.pop((m, p))
        out = {'model': m, 'protocol': p}
        for k, row in refs[p].items():
            ref_iv = [row['interval'][0] / 100, row['interval'][1] / 100]
            rel = relation(c['interval_95'], ref_iv)
            require(w['relations'][k]['relation'] == rel and w['relations'][k]['ref'] == f'{row["name"]} ({row["mode"]})',
                    f'{m} {p} vs {k}: the candidate says otherwise')
            out[k] = {'row': row['id'], 'name': row['name'], 'relation': rel}
        published.append(out)
    require(not want, 'the candidate compares cells that are not published')
    # The masking ablation: which of the four checkpoints' marginal intervals overlap, protocol by protocol.
    masking = []
    want = {r['protocol']: r for r in candidate['masking_ablation_panel']['overlap_rows']}
    for p in SCORED:
        pairs = [[a, b] for i, a in enumerate(ABLATION) for b in ABLATION[i + 1:]
                 if not overlap(cells[(a, p)]['interval_95'], cells[(b, p)]['interval_95'])]
        w = want[p]
        require(w['all_pairwise_marginal_intervals_overlap'] is (not pairs)
                and sorted(map(sorted, w['non_overlapping_pairs'])) == sorted(map(sorted, pairs)),
                f'masking {p}: the candidate says otherwise')
        masking.append({'protocol': p, 'all_pairwise_marginal_intervals_overlap': not pairs, 'non_overlapping_pairs': pairs})
    return {
        'rule': ('Above or below only when the marginal 95% intervals do not overlap; otherwise overlap. Descriptive: '
                 'the same people under two encoders are not tested pairwise, and 126 frozen cells mean an occasional '
                 'non-overlap is expected by chance.'),
        'published_reference_release': matrix['releaseId'],
        'vs_published_rows': published,
        'base_vs_large': sizes,
        'fewer_electrodes_beta': electrodes,
        'masking_ablation': masking,
    }


def exposure_block(table, candidate):
    keep_method = [m for m in table['method'] if 'research/' not in m]
    require(len(keep_method) == len(table['method']) - 1, 'the exposure method changed shape')
    require([m['key'] for m in table['models']] == list(EXPOSURE_TABLE_MODELS), 'the exposure table covers other models')
    require(len(table['cells']) == len(EXPOSURE_TABLE_MODELS) * len(table['datasets']), 'the exposure table is not complete')
    counts = {'exposed': 0, 'not_exposed': 0, 'unknown': 0}
    cells = []
    for c in table['cells']:
        require(c['status'] in counts and c['urls'] and all(u.startswith('https://') for u in c['urls']),
                f'exposure {c["model"]} {c["dataset"]}: a cell without a status or a source link')
        counts[c['status']] += 1
        cell = {k: c[k] for k in ('model', 'dataset', 'protocols', 'status', 'confidence', 'evidence', 'urls')}
        cell['statement'] = EXPOSURE_STATEMENT[c['status']]
        for k in ('lean', 'basis', 'author_downstream_use'):
            if c.get(k):
                cell[k] = c[k]
        cells.append(cell)
    require(counts == table['summary']['counts'] == candidate['exposure_flags']['counts'], 'the exposure counts disagree')
    for key in ('labram', 'cbramod'):
        rows = [c for c in cells if c['model'] == key]
        require(len(rows) == len(table['datasets']) and all(c['status'] == 'not_exposed' and c['urls'] for c in rows),
                f'{key}: the sourced statement needs every core dataset absent from a cited list')
    return {
        'checked_on': CHECKED_ON,
        'definition': table['definition'],
        'status_vocabulary': table['status_vocabulary'],
        'statements': EXPOSURE_STATEMENT,
        'wording_rule': ('Owner decision, 2026-10-04: a model\'s exposure is stated as what its authors\' published '
                         'pretraining list shows, checked on a date and linked to the source; never as proven absence '
                         'of overlap. Recording-level audits were not done: exposure is decided per dataset. A '
                         'cell\'s confidence rates how closely its source enumerates the corpus, not how certain it is '
                         'that the recordings were never seen.'),
        'method': keep_method,
        'datasets': [{k: d[k] for k in ('key', 'name', 'protocols', 'url')} for d in table['datasets']],
        'models': [{k: m[k] for k in ('key', 'name', 'variants_covered', 'evaluated_in_v9', 'corpus_summary',
                                      'corpus_listing', 'primary_sources', 'notes', 'checked_on') if k in m}
                   for m in table['models']],
        'cells': cells,
        'counts': counts,
        'caveats': table['caveats'],
    }


# ---------------------------------------------------------------------------- the handoff the owner approved
def handoff_tables(handoff):
    """The handoff's three tables, by header, as {row label: [cells]}."""
    tables, current = {}, None
    for line in handoff.splitlines():
        if line.startswith('| Encoder |'):
            current = tables.setdefault(line.split('|')[2].strip(), {})
        elif current is not None and line.startswith('|') and not line.startswith('|---'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            current[cells[0]] = cells[1:]
        elif not line.startswith('|'):
            current = None
    return tables


def fixed(x, digits):
    """Number.prototype.toFixed: the exact binary value, a tie rounded away from zero. The pages format this way."""
    return str(Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def check_handoff(handoff, cells, adaptation, matrix):
    """Every figure of the handoff's three tables, as the pages will print it, is the export's."""
    tables = handoff_tables(handoff)
    frozen, idle, adapt = tables['mi-rest'], tables['Idle false triggers'], tables['Frozen ridge (matrix)']
    f1 = lambda v: fixed(100 * v, 1)
    c1 = lambda v: fixed(percent(v), 1)          # a matrix figure, printed from the CSV
    for m in CHECKPOINTS:
        row = frozen[HANDOFF_LABEL[m]]
        for p, printed in zip(HANDOFF_COLUMNS, row):
            c = cells[(m, p)]
            if c['status'] != 'complete':
                want = 'not run'
            else:
                iv = c['interval_95']
                marks = [m_ for m_, on in (('**E**', c['exposure']['status'] == 'exposed'),
                                           ('U', c['exposure']['status'] == 'unknown'),
                                           ('∘', c['interval_includes_chance'])) if on]
                want = ' '.join([f'{c1(c["balanced_accuracy"])} ({c1(iv[0])}–{c1(iv[1])})', *marks])
            require(printed == want, f'the handoff prints {printed!r} for {m} {p}, the export {want!r}')
        c = cells[(m, 'idle')]
        want = [f'{c["idle_false_activations"]}/{c["idle_trials"]}', f'{c["commands_detected"]}/{c["command_trials"]}',
                str(c['always_abstain_people']), f'{f1(c["window_balanced_accuracy"])}%', fixed(c['window_auroc'], 3)]
        require(idle[HANDOFF_LABEL[m]] == want, f'the handoff\'s idle row for {m} differs from the export')
    # The published context rows the handoff prints are the released matrix's.
    tracks = {t['id']: t for t in matrix['tracks']}
    for label, pick in (('Published LaBraM (frozen)', lambda rows: next(r for r in rows if r['id'] == 'labram')),
                        ('Published CBraMod (frozen)', lambda rows: next(r for r in rows if r['id'] == 'cbramod')),
                        ('Published best non-foundation row¹',
                         lambda rows: max((r for r in rows if r['family'] != 'foundation'), key=lambda r: r['y']))):
        for p, printed in zip(HANDOFF_COLUMNS, frozen[label]):
            r = pick(tracks[p]['rows'])
            require(printed == f'{fixed(r["y"], 1)} ({fixed(r["interval"][0], 1)}–{fixed(r["interval"][1], 1)})',
                    f'the handoff\'s {label} {p} is not the released row')
    pc = adaptation['published_context']
    rows = {r['model']: r for r in adaptation['rows']}
    labram_ridge = next(r for r in tracks['arithmetic-rest']['rows'] if r['id'] == 'labram')['y']
    lines = [('Published LaBraM', labram_ridge, pc['arms']['frozen'], pc['arms']['lora-r4'], pc['paired_lora_minus_frozen'])]
    lines += [(HANDOFF_LABEL[m] + (' U' if m == UNKNOWN_EXPOSURE else ''), 100 * r['frozen_ridge_reference']['balanced_accuracy'],
               r['arms']['frozen-ce'], r['arms']['lora-r4'], r['paired_lora_minus_frozen']) for m, r in rows.items()]
    pp2 = lambda v: ('' if v < 0 else '+') + fixed(100 * v, 2)
    for label, ridge, head, lora, paired in lines:
        iv = paired['interval_95']
        want = [fixed(ridge, 1),
                f'{f1(head["balanced_accuracy"])} ({f1(head["interval_95"][0])}–{f1(head["interval_95"][1])})',
                f'{f1(lora["balanced_accuracy"])} ({f1(lora["interval_95"][0])}–{f1(lora["interval_95"][1])})',
                f'{pp2(paired["mean_change"])} ({pp2(iv[0])} to {pp2(iv[1])})',
                f'{paired["helped"]}/{paired["harmed"]}/{paired["tied"]}',
                f'{head["trainable_parameters"]:,} / {lora["trainable_parameters"]:,}']
        require(adapt[label] == want, f'the handoff\'s adaptation row {label} differs from the export')
    lo, hi = adaptation['lora_parameter_range']
    require(f'LoRA budgets from {lo:,} to {hi:,} parameters' in handoff, 'the handoff states another LoRA budget range')
    return len(frozen) + len(idle) + len(adapt)


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, names=(), trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {trail}.{k}')
            scrub_check(v, names, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, names, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source file or participant identifier in export: {trail}')
        require(not PRIVATE_TOKENS.search(value), f'private host or path in export: {trail}')
        require(not any(n.lower() in value.lower() for n in names), f'a private host or volume name in export: {trail}')


CSV_HEADER = (
    # The core results CSVs' columns, in their order and units (export_snapshot.write).
    'dataset', 'dataset_version', 'protocol_id', 'model', 'evaluation_mode', 'channels', 'participants',
    'primary_metric', 'primary_percent', 'secondary_metric', 'secondary_value', 'descriptive_interval_low_percent',
    'descriptive_interval_high_percent', 'always_abstain_participants', 'chance_level_percent', 'scoring_seconds',
    'source', 'license', 'license_url', 'attribution', 'scope', 'model_rights',
    # This batch's own.
    'release_id', 'model_id', 'panel', 'status', 'not_run_reason', 'interval_includes_chance', 'at_or_below_chance',
    'pretraining_exposure', 'pretraining_exposure_checked', 'encoder_parameters', 'model_revision', 'checkpoint_sha256',
    'model_paper', 'licence_note', 'row_footnote', 'notes', 'idle_false_activations', 'idle_trials', 'commands_detected',
    'command_trials', 'window_balanced_accuracy', 'window_auroc',
)


# Columns that describe the protocol, not the method: equal in every row of a core results CSV.
SHARED_COLUMNS = ('dataset', 'dataset_version', 'protocol_id', 'channels', 'primary_metric', 'secondary_metric',
                  'chance_level_percent', 'source', 'license', 'license_url', 'attribution', 'scope')


def core_results(protocol):
    """The released core results CSV of a protocol (read, never written): its header and its first row."""
    rows = list(csv.reader(io.StringIO((CSV_DIR / f'{protocol}-results.csv').read_text())))
    require(all(len(r) == len(rows[0]) for r in rows), f'{protocol}-results.csv is ragged')
    for k in SHARED_COLUMNS:
        require(len({r[rows[0].index(k)] for r in rows[1:]}) == 1, f'{protocol}-results.csv: {k} varies by row')
    return rows[0], dict(zip(rows[0], rows[1]))


def csv_files(result, release_id, matrix):
    core = {}
    for p in PROTOCOLS:
        header, first = core_results(p)
        require(list(CSV_HEADER[:len(header)]) == header, f'{p}: the core columns are not the core results CSV\'s')
        core[p] = first
    tracks = {t['id']: t for t in matrix['tracks']}
    protocols = {p['id']: p for p in result['protocols']}
    models = {m['id']: m for m in result['models']}
    cells = {(c['model'], c['protocol']): c for c in result['frozen_probe']}
    flag = lambda v: '' if v is None else ('true' if v else 'false')
    out = {}
    for p in PROTOCOLS:
        t = tracks[p]
        stream = io.StringIO()
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(CSV_HEADER)
        for mid in CHECKPOINTS:
            m, c = models[mid], cells[(mid, p)]
            done = c['status'] == 'complete'
            if p == 'idle':
                primary = 100 * c['commands_detected'] / c['command_trials']
                secondary = 100 * c['idle_false_activations'] / c['idle_trials']
                low = high = ''
                abstain = c['always_abstain_people']
            elif done:
                primary, secondary = percent(c['balanced_accuracy']), c['macro_f1']
                low, high = percent(c['interval_95'][0]), percent(c['interval_95'][1])
                abstain = ''
            else:
                primary = secondary = low = high = abstain = ''
            row = [
                t['dataset'], t['version'], t['protocolId'], m['name'], m['idle_mode'] if p == 'idle' else m['mode'],
                protocols[p]['channels'], c['people'] if done else '',
                t['yLabel'], primary, t['xLabel'], secondary, low, high, abstain,
                '' if t.get('chanceLevel') is None else t['chanceLevel'], '',
                t['source'], t['license'], t['licenseUrl'], t['attribution'], t['rightsScope'], m['weights_licence'],
                release_id, mid, m['panel'], c['status'], c.get('reason', ''),
                flag(c.get('interval_includes_chance')), flag(c.get('at_or_below_chance')),
                c['exposure']['statement'], CHECKED_ON, m['parameters_encoder'], m['revision'] or '',
                m['checkpoint_sha256'] or '', m['paper'], m['licence_note'], m['row_footnote'],
                ' '.join([*m['notes'], *c.get('notes', [])]),
                *([c['idle_false_activations'], c['idle_trials'], c['commands_detected'], c['command_trials'],
                   c['window_balanced_accuracy'], c['window_auroc']] if p == 'idle' else [''] * 6),
            ]
            require(len(row) == len(CSV_HEADER), f'{p} {mid}: a CSV row that does not fit the header')
            # The protocol's own columns are the core results CSV's, value for value.
            for k in SHARED_COLUMNS:
                require(str(row[CSV_HEADER.index(k)]) == core[p][k], f'{p}: {k} differs from the core results CSV')
            writer.writerow(row)
        out[f'foundation-models-{p}.csv'] = stream.getvalue().encode()
    return out


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    ev = manifest['evaluation']
    approval = manifest['approval']
    require(ev['id'] == EVALUATION and approval['decision'] == 'aggregate_preview'
            and approval['date'] == manifest['reviewed_at'] == CHECKED_ON, 'no recorded approval for the v9 batch')
    require(approval['candidateStatusAtSeal'] == CANDIDATE_STATUS, 'the approval names another candidate state')
    require('never as proven' in approval['pretrainingExposureWording'], 'the exposure wording decision is not on record')
    require([s['id'] for s in manifest['sources']] == list(PROTOCOLS), 'the manifest names other sources')
    require(manifest['holds'] == [], 'the v9 batch has no hold')
    handoff = pinned_text(ev['handoff'], 'handoff')
    candidate, candidate_sha = pinned(ev['releaseCandidate'], 'release candidate')
    aggregate, aggregate_sha = pinned(ev['aggregate'], 'aggregate')
    table, table_sha = pinned(ev['pretrainingExposure'], 'pretraining exposure')
    audit_status, audit_status_sha = pinned(ev['auditStatus'], 'audit status')
    harness, _ = pinned(ev['harnessValidation'], 'harness validation')
    summaries = {g: pinned(r, f'{g} summary') for g, r in ev['summaries'].items()}
    matrix_raw = SITE_FILES['site/src/data/mvp.json'].read_bytes()
    matrix = json.loads(matrix_raw)
    # Keyed by file name: the candidate names files by their place in the run's folder, the manifest by where
    # they are read from. The bytes are bound by hash either way.
    files = {Path(r['path']).name: (r['sha256'], summaries[g][0]) for g, r in ev['summaries'].items()}
    files[Path(ev['pretrainingExposure']['path']).name] = (table_sha, table)
    for name, path in SITE_FILES.items():
        raw = path.read_bytes()
        files[Path(name).name] = (sha(raw), json.loads(raw))
    require(len(files) == len(ev['summaries']) + 1 + len(SITE_FILES), 'two pinned files share a name')
    audits = bindings(manifest, candidate, aggregate, table, audit_status, harness, handoff, files)
    references = reresolve(candidate, files)

    tracks = {t['id']: t for t in matrix['tracks']}
    records = {}
    for record in manifest['sources']:
        require(record['decision'] == 'aggregate_preview' and approved(record), f'{record["id"]}: approval record is incomplete')
        track = tracks[record['coreTrack']]
        require(record['protocol'] == record['coreTrack'] == record['id'], f'{record["id"]}: another protocol than its core track')
        for k in ('source', 'version', 'license', 'licenseUrl', 'attribution', 'reviewBasis'):
            require(record[k] == track[k], f'{record["id"]}: {k} differs from the reviewed core track')
        require(record['privacyReview'].startswith(track['privacyReview']), f'{record["id"]}: the privacy review is not the reviewed one')
        require(record['name'] == track['dataset'], f'{record["id"]}: another dataset')
        records[record['id']] = record
    for p in PROTOCOLS:
        require(len({r['channels'] for r in tracks[p]['rows']}) == 1, f'{p}: the core rows disagree on channels')
        tracks[p] = tracks[p] | {'channels': tracks[p]['rows'][0]['channels']}
    want = [(p['id'], p['people'], p['chance_level_percent']) for p in candidate['protocols']]
    require(want == [(p, tracks[p]['subjects'], tracks[p].get('chanceLevel')) for p in PROTOCOLS],
            'the candidate\'s protocols are not the released ones')

    # Frozen probes: every checkpoint on every protocol, matrix rows and the masking panel alike.
    agg_cells = {c['id']: c for c in aggregate['frozen_probe_cells']}
    raw_cells = {(c['model'], c['protocol']): c for r in candidate['matrix_rows'] for c in r['cells']}
    for c in candidate['masking_ablation_panel']['cells']:
        if c['model'] in raw_cells and (c['model'], c['protocol']) in raw_cells:
            require(same(c, raw_cells[(c['model'], c['protocol'])]), f'{c["model"]} {c["protocol"]}: two different cells')
        raw_cells[(c['model'], c['protocol'])] = c
    require(sorted(raw_cells) == sorted((m, p) for m in CHECKPOINTS for p in PROTOCOLS), 'the candidate has other cells')
    require(len(agg_cells) == len(raw_cells), 'the aggregate has other cells')
    cells = {}
    for m in CHECKPOINTS:
        for p in PROTOCOLS:
            cells[(m, p)] = frozen_cell(raw_cells[(m, p)], m, p, tracks[p], agg_cells[f'frozen:{m}:{p}'], table)
    not_run = [c for c in candidate['not_run'] if c['protocol'] not in PROTOCOLS or (c['model'], c['protocol']) in NOT_RUN]
    require(len(not_run) == len(candidate['not_run']), 'a frozen cell is listed as not run but scored')
    for m, p in NOT_RUN:
        reason = next(c['reason'] for c in candidate['not_run'] if (c['model'], c['protocol']) == (m, p))
        require(cells[(m, p)]['reason'] == reason, f'{m} {p}: two reasons')
    scored = sum(1 for c in cells.values() if c['status'] == 'complete')   # idle included, as the handoff counts
    require(scored == 126 and len(NOT_RUN) == 2, 'not the 126 frozen cells and 2 not-run cells the handoff describes')

    models = models_block(candidate, manifest)
    # A note every cell of a model carries is the model's: printed once, beside its row.
    for m in models:
        own = [cells[(m['id'], p)].get('notes', []) for p in PROTOCOLS]
        common = [n for n in own[0] if all(n in o for o in own)]
        m['notes'] = common
        for p in PROTOCOLS:
            rest = [n for n in cells[(m['id'], p)].pop('notes', []) if n not in common]
            if rest:
                cells[(m['id'], p)]['notes'] = rest
    adaptation = adaptation_block(candidate, aggregate, cells)
    comparisons = comparisons_block(candidate, cells, matrix)
    exposure = exposure_block(table, candidate)
    handoff_rows = check_handoff(handoff, cells, adaptation, matrix)
    directory = [{k: d[k] for k in ('name', 'suggested_status', 'replaces', 'note')}
                 for d in candidate['model_directory_status_suggestions']]
    limitations = list(candidate['required_limitations'])
    require(len(limitations) == 9 and any('not any model\'s ceiling' in x for x in limitations)
            and any('never ranked' in x for x in limitations), 'the required limitations changed')
    # The candidate's exposure limitation says "EEGMamba not exposed at medium confidence": the owner's wording is the
    # authors' published lists, never "not exposed" (decision of 2026-10-04; review of 2026-10-05). It is restated.
    exposure_items = [i for i, x in enumerate(limitations) if x.startswith('Pretraining exposure:')]
    require(len(exposure_items) == 1 and limitations[exposure_items[0]] == CANDIDATE_EXPOSURE_LIMITATION,
            'the exposure limitation changed: re-read it against the owner\'s wording')
    limitations[exposure_items[0]] = EXPOSURE_LIMITATION

    order = {p: i for i, p in enumerate(PROTOCOLS)}
    result = {
        'id': EVALUATION,
        'title': 'Foundation models, v9: eleven further EEG encoders as frozen probes, and nine adapted on EEGMAT',
        'evaluation_id': CANDIDATE_ID,
        'design': DESIGN,
        'protocols': [{'id': p, 'title': tracks[p]['title'], 'dataset': tracks[p]['dataset'], 'type': tracks[p]['type'],
                       'people': tracks[p]['subjects'], 'channels': tracks[p]['channels'],
                       'chance_level': None if tracks[p].get('chanceLevel') is None else tracks[p]['chanceLevel'] / 100,
                       'file': f'foundation-models-{p}.csv',
                       'core_files': [f'{p}-results.csv', f'{p}-protocol.json'],
                       'rights': rights(records[p]) | {'coreTrack': p}} for p in PROTOCOLS],
        'models': models,
        'frozen_probe': [cells[k] for k in sorted(cells, key=lambda k: (CHECKPOINTS.index(k[0]), order[k[1]]))],
        'masking_ablation': {
            'design': ('2 x 2: masking framework (MAE, JEPA) by mask geometry (the paper-recommended r=9 cm, L=2, and '
                       'a one-channel L=1 control); the same architecture, pretraining corpus and recipe. The '
                       'paper-recommended MAE checkpoint is the matrix row; the other three are this panel.'),
            'checkpoints': list(ABLATION),
            'paper': models[CHECKPOINTS.index(ABLATION[0])]['paper'],
        },
        'eegmat_adaptation': adaptation,
        'comparisons': comparisons,
        'pretraining_exposure': exposure,
        'directory_status': directory,
        'not_run': not_run,
        'required_limitations': limitations,
        'audits': audits,
    }
    payload = {
        'schema_version': 'bci-report-foundation-models-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': ('balanced accuracy, its participant-bootstrap interval, macro F1 and window balanced accuracy '
                         'are proportions in [0,1]; window AUROC is in [0,1]; paired and descriptive changes are '
                         'differences of proportions; idle figures, people, trials and parameters are whole numbers; '
                         'null means not run, never zero. The per-protocol CSVs carry balanced accuracy and its '
                         'interval in percent, as the core results CSVs do.'),
        'scope': ('New rows beside the core matrix, never merged into experiments.json: eleven further foundation '
                  'models (sixteen encoder checkpoints) as frozen probes with the published recipe and only the '
                  'encoder swapped, on the same eight protocols, people and folds; and nine of them adapted on '
                  'EEGMAT with one fixed recipe. Grouped by family, never ranked; new people, same task and '
                  'recording setup; no deployment or clinical claim.'),
        'results': {EVALUATION: result},
        'status_only': [],
        'holds': [],
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'release_candidate_sha256': candidate_sha,
                       'aggregate_sha256': aggregate_sha, 'pretraining_exposure_sha256': table_sha,
                       'audit_status_sha256': audit_status_sha, 'references_reresolved': references,
                       'handoff_rows_checked': handoff_rows, 'included': [EVALUATION],
                       'inputs': [s['id'] for s in manifest['sources']], 'holds': []},
    }
    names = private_names(candidate, handoff)
    require(names, 'the private host and volume names could not be read, so the scrub would be blind to them')
    scrub_check(payload, names)
    validate_public(payload)
    csvs = csv_files(result, manifest['release_id'], matrix)
    for name, data in csvs.items():
        text = data.decode()
        require(not PRIVATE_TOKENS.search(text) and not SOURCE_IDS.search(text)
                and not any(n.lower() in text.lower() for n in names), f'{name}: a private path or identifier')
    return payload, csvs


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    ev = manifest['evaluation']
    refs = [ev[k] for k in ('handoff', 'releaseCandidate', 'aggregate', 'pretrainingExposure', 'auditStatus',
                            'harnessValidation')] + list(ev['summaries'].values())
    return all((PROJECT / r['path']).exists() for r in refs)


def serialize(payload):
    return (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()


def serialized_export():
    """The JSON payload and the per-protocol CSVs, as bytes: what the site serves."""
    payload, csvs = build(MANIFEST.read_bytes())
    return serialize(payload), csvs


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload, csvs = build(manifest_bytes)
    data = serialize(payload)
    for out in OUTPUTS:
        out.write_bytes(data)
    for name, body in csvs.items():
        (CSV_DIR / name).write_bytes(body)
    prov = payload['provenance']
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'csv_sha256': {name: sha(body) for name, body in csvs.items()},
        'manifest_sha256': sha(manifest_bytes),
        'release_candidate_sha256': prov['release_candidate_sha256'],
        'included': prov['included'], 'inputs': prov['inputs'], 'status_only': [], 'holds': [],
        'checks': [
            'pinned handoff, release candidate, aggregate, pretraining-exposure table, audit status, harness validation '
            'and the twelve group summaries',
            f'every traced block of the release candidate re-resolves to the file and bytes it names '
            f'({prov["references_reresolved"]} references), released site files included',
            'the aggregate records every pinned input by its pinned hash; the handoff records every hash bound here',
            'all six independent audits passed with no defect, named by the same hash in the candidate, the audit '
            'status, the aggregate and the handoff; every checkpoint belongs to a passing group',
            'the harness reproduced the published LaBraM and CBraMod frozen rows and the 45 LaBraM adaptation fits',
            'every frozen cell and adaptation row equals the aggregate row of the same id; 126 scored cells, 2 not run '
            'with their reason and no figure',
            'every interval holds its point; every chance flag follows the interval and the released chance level; '
            'idle figures are counts of 60 test trials',
            'every paired change is the difference of its arms, helped + harmed + tied = 36, and its zero flag '
            'follows its interval',
            'every size, electrode, masking and published-row comparison recomputed from the intervals and equal to '
            'the candidate\'s',
            'exposure: each cell\'s pointer lands on its own model and dataset; ST-EEGFormer on BETA and SingLEM on '
            'TMNRED exposed, every ZUNA 1.1 cell unknown, the rest not in the published lists, with source links',
            'cohorts, channels, chance levels and dataset rights equal the released core tracks',
            f'the frozen-probe, idle and adaptation tables equal the handoff\'s, row by row ({prov["handoff_rows_checked"]} rows)',
            'per-trial, per-person, per-fold, timing and environment fields refused by key; no private path, host or '
            'volume name, file or participant identifier in the JSON or the CSVs',
        ],
        'audit_bindings': {
            'bound': [
                'release candidate bytes: pinned here, and recorded in the handoff',
                'every candidate figure: equal, at its JSON pointer, to the pinned summary, exposure table or released '
                'site file it names',
                'aggregate, exposure table, audit status, harness validation and summaries: by the hashes the '
                'aggregate and the handoff record',
                'independent audits: by the hashes the candidate, the audit status, the aggregate and the handoff record',
            ],
            'not_bound': [
                'the independent audits are not opened here (they carry private storage paths); their pass is taken '
                'from the audit status and the candidate, whose bytes are pinned',
            ],
        },
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
