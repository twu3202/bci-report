"""Release the data-quality page's three cases, aggregate-only: Shin2022 worked end to end, eldBETA and ZuCo 2.0 as status.

Shin2022 (closed-loop right/left cursor control, 16-channel dry EEG, ten healthy participants) is the worked case: a
participant-held-out diagnostic of the instructed target in the first second of feedback, with a training prior, a
normalized spectral ridge and a retrospective duration control, and the chain that takes the release's recorded runs
to the signal-valid windows the three arms are scored on. eldBETA is a status case with counts only: the owner's
decision for this release (D2) holds its one-participant score under the one-person rule. ZuCo 2.0 is a status case
with no figure: a fixation-timing hold on one converted run. The owner's decision D1 publishes the page.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- Shin2022's three arms verbatim from the research export, and only if the release audit's independent reconstruction
  holds the same values (value and type), the release review passes the aggregate and the consistency review names
  the export's hash;
- the run chain from the label and duplicate audit, the window chain from the export, the protocol and the census
  review, every link adding up and equal to each other pinned record that states it; the catalog's trial length and
  the header's feedback cap from the MOABB shortlist and the label semantics evidence;
- eldBETA's counts from its export, equal to the release audit and the raw QC aggregate; its published cohort size
  from the Figshare record captured in A3; the SingLEM fact from the released foundation-models file;
- ZuCo 2.0's flags from the independent alignment audit, its wording checked against the hash-bound CPU handoff whose
  ZuCo2 paragraph the release review checked, its identity and stated licence from the intake gate;
- consent, ethics and terms only from this release's A3 record, each capture it cites checked by SHA-256.
The research files are copy and value sources only: several carry private storage paths, so they are pinned and
checked, never published, and the private names this export refuses are read from them at run time.

What this export refuses:
- participant rows, per-participant ranges, the duration distribution, per-channel census counts, predictions,
  features and timings, by key and, where the sources hold them, by value;
- eldBETA's one-participant accuracy and its fixed comparator, by key, by value and by text; any figure in the ZuCo 2.0
  case outside its source identity, and the converted run's code and row values;
- BI2013a, MOABB's catalog trial and run counts, any conference or submission reference and the commenter's figure;
- private paths and names, version labels, update markers, months used as labels, strings that have lost their
  spaces, "X, not Y" hedges, Jev, and claims these results do not support.

    python3 pipeline/publication/export_data_quality_update.py
"""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'data-quality-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'data-quality-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/data-quality-update.json',
           PROJECT / 'site/public/data/data-quality-update.json')
RELEASE_ID = 'data-quality-update-20261020'
SCHEMA = 'bci-report-data-quality-update-v1'

DEED = 'https://creativecommons.org/licenses/by/4.0/'
SHIN_DOI = '10.6084/m9.figshare.20383716.v1'
SHIN_PAPER_DOI = '10.3389/fnhum.2022.951591'
ELD_DOI = '10.6084/m9.figshare.18032669.v3'
ELD_PAPER_DOI = '10.1038/s41597-022-01372-9'
ATTRIBUTION_END = 'Derived analysis by BCI Report; not endorsed by the authors.'
QUESTION = 'What do the files show once a public EEG dataset is checked end to end?'
SHIN_QUESTION = 'What survives a participant-held-out check?'
ZUCO_NAME = 'ZuCo 2.0'
ZUCO_HOLD = ("No EEG–text score is computed until the converter's timing rules and a source-checksummed fixture are "
             'available.')
ARM_ORDER = ('training_prior', 'normalized_spectral_ridge', 'retrospective_duration_ridge')
ARM_KEYS = ('arm', 'participant_bootstrap_percentile_95', 'participant_mean_balanced_accuracy',
            'pooled_balanced_accuracy_secondary')
WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
TOL = 1e-9
TRIVIAL = {0.0, 0.5, 0.95, 1.0}   # chance, the interval level and unit design values that a source figure can equal

# Per-participant figures, distributions, internals and timings.
REFUSED_KEYS = PER_PERSON_KEYS | {'seconds', 'total_seconds', 'quantiles', 'feedback_quantiles_seconds', 'checks_detail',
                                  'samples', 'members', 'aliases', 'fold_manifest', 'boundary_examples'}
REFUSED_KEY_FRAGMENTS = ('per_fold', 'per_person', 'per_participant', 'per_subject', 'participant_id', 'subject',
                         'prediction', 'probabilit', 'threshold', 'quantile', 'median', '_min', '_max', 'elapsed',
                         'cpu', 'wall', 'accounting', 'bytes', 'rss', 'memory', 'device', 'private', 'path', 'host',
                         'onset', 'member', 'decision_values')
# Inside the eldBETA case: nothing that is, or bounds, its held score.
HELD_SCORE_KEY_FRAGMENTS = ('accuracy', 'correct', 'comparator', 'top1', 'residual', 'frequenc', 'interval', 'chance',
                            'correlation')

LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\w+|\bsubj\d+|\bS\d{1,3}\b|\bYAC\b|\btask-nr\b|\brun-?\d+\b'
                        r'|\.(?:npz|npy|edf|mat|tsv|gdf|dat)\b', re.IGNORECASE)
OUT_OF_FILE = re.compile(r'BI2013a|Brain Invaders|2669187|1494163|Vaineau|GIPSA|ICLR|OpenReview|NeurIPS|submission'
                         r'|double-blind|iMINDBench|NEAR-Bench|\bTASER\b|CoLaP', re.IGNORECASE)
FIFTY_FIVE = re.compile(r'(?<![\d.])55(?:\.0+)?\s*(?:%|per ?cent)|fifty[- ]five|(?<![\d.])0\.55(?!\d)', re.IGNORECASE)
HELD_TEXT = re.compile(r'\b26\s*/\s*63\b|\b26 of (?:the )?63\b|41\.2\d|41\.3\b|11\.11|\b7\s*/\s*63\b|\b7 of 63\b'
                       r'|\b2,?640\b|\b2,?62[89]\b|4,?287,?888|2\^32|\b106\b|\b1,?585\b')
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
HEDGE = re.compile(r'[,;]\s+not\s', re.IGNORECASE)
CLAIMS = re.compile(r'significan|superior|outperform|\bbeats?\b|better than|worse than|\bbest\b|\bwinner|\branks?\b'
                    r'|\branked\b|\branking\b|state[- ]of[- ]the[- ]art|pure motor imagery|mental act|whole[- ]pool'
                    r'|\bonline\b|real-time|early decoder|\bclinical\b|\bmedical\b|\bcausal|\bcaused\b|artifact-free'
                    r'|artefact-free|\bclean\b|units? (?:are |were |is |was )?verified|verified (?:microvolt|amplitude|unit)'
                    r'|standard_1005|\bC[34]\b|dry[- ](?:vs|versus)[- ]wet|preregist|ag(?:e)?ing effect|older[- ]adult (?:accuracy|score|performance)',
                    re.IGNORECASE)
HEX = re.compile(r'[0-9a-f]{16,}')
# Verbatim quotations and citations: checked for paths, names, identifiers and labels, never reworded.
QUOTED_SUFFIXES = ('.quote', '.citation', '.hardware', '.title_as_recorded')


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool)


def identical(a, b):
    """Equal value for value and type for type: 1 is not 1.0 and 0.5258798351627936 is not its rounding."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def flat(text):
    return re.sub(r'\s+', ' ', text).strip()


def stated(text, phrase, label):
    require(flat(phrase) in flat(text), f'{label}: the pinned record does not state {phrase!r}')


def strip_tags(text):
    return flat(html.unescape(re.sub(r'<[^>]+>', ' ', text)))


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def leaves(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, f'{trail}[{i}]')
    else:
        yield trail, value


def floats(value):
    return [v for _, v in leaves(value) if isinstance(v, float)]


def ints(value):
    return [v for _, v in leaves(value) if count(v)]


def names_and(names):
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def word(n):
    return WORDS.get(n, f'{n:,}')


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {}
    for k, ref in manifest['sources'].items():
        docs[k] = pinned_text(ref, k) if ref['path'].endswith('.md') else pinned(ref, k)[0]
    for k, ref in manifest['withheldReference'].items():
        docs[k] = pinned(ref, k)[0]
    docs['consent'] = pinned(manifest['consent']['statements'], 'consent statements')[0]
    docs['foundationModels'] = pinned(manifest['published']['foundationModels'], 'foundation-models-update.json')[0]
    docs['captures'] = captures(docs['consent'])
    return docs


def captures(a3):
    """The A3 captures this release reads, each refused unless its bytes have the SHA-256 the A3 record gives."""
    out = {}
    for key in ('shin2022', 'eldbeta'):
        s = a3['sources'][key]
        lic = s['licence']['data']
        for f, digest in ((s['capture_file'], s['capture_sha256']), (lic['capture_file'], lic['capture_sha256']),
                          (lic['latest_check']['capture_file'], lic['latest_check']['capture_sha256'])):
            raw = (REVIEW / f).read_bytes()
            require(sha(raw) == digest, f'A3 capture {f}: not the bytes the consent record names')
            out[f] = raw.decode('utf-8')
    return out


def owner_decisions(manifest):
    """The quoted decisions are still the owner's: D1 publishes the page with Shin2022, D2 holds eldBETA's score."""
    od = manifest['approval']['ownerDecisions']
    decisions = json.loads((PROJECT / od['path']).read_bytes())['decisions']
    current = {'D1': decisions['D1']['answer'], 'D2': decisions['D2']['answer']}
    for k, text in od['quoted'].items():
        require(current.get(k) == text, f'owner decision {k} changed; the release must be reviewed again')
    require('Shin2022 with the data-quality page' in current['D1'], 'D1 does not publish the data-quality page')
    require(current['D2'].startswith('Status and counts only') and 'score is held' in current['D2'],
            'D2 no longer holds the eldBETA score; the eldBETA case must be reviewed again')
    return current


def private_names(docs):
    """The home, storage and host names the handoffs use, read from them, never spelled in this file."""
    text = docs['moabbWebsiteHandoff'] + docs['eldbetaHandoff'] + docs['zucoHandoff']
    names = {n for pair in re.findall(r'/(?:home|Users|Volumes|mnt)/([^/\s`]+)/([^/\s`]+)', text) for n in pair}
    machines = set(re.findall(r'\b(?:on|or) ([A-Z][A-Za-z]{1,8}\d+)\b', text))    # "stay on <host>", "the Mac or <disk>"
    names |= machines | {re.sub(r'\d+$', '', m) for m in machines}
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- consent, ethics and terms (A3)
def figshare(docs, a3_source):
    lic = a3_source['licence']['data']
    record = json.loads(docs['captures'][lic['capture_file']])
    versions = json.loads(docs['captures'][lic['latest_check']['capture_file']])
    latest = max(v['version'] for v in versions)
    require(lic['pinned_version_is_latest'] is True and record['version'] == latest,
            f'{record["doi"]}: the pinned version is not the latest the record lists')
    require(record['license']['name'] == lic['value'] == 'CC BY 4.0' and record['license']['url'] == lic['url'] == DEED,
            f'{record["doi"]}: another data licence')
    return record, versions


def consent_block(s, label):
    """The A3 statements as recorded: quote, statement, location, body, approval number and gaps."""
    c, e = s['consent'], s['ethics']
    require(c['stated'] is True and e['stated'] is True, f'{label}: a consent or ethics statement is missing')
    return {
        'ethics_approval': {'stated': True, 'statement': e['statement'], 'quote': s['ethics_quote'], 'body': e['body'],
                            'approval_number': e['approval_number'], 'location': e['location']},
        'informed_consent': {'stated': True, 'kind': c['kind'], 'statement': c['statement'], 'quote': s['consent_quote'],
                             'location': c['location']},
        'read_from': s['read_from'], 'read_section': s['read_section'], 'read_at': s['captured_at'],
        'capture_sha256': s['capture_sha256'],
        'gaps': [{'field': g['field'], 'note': g['note']} for g in s['gaps']],
    }


def terms_block(s, record, versions):
    lic = s['licence']
    return {
        'data_licence': {'value': lic['data']['value'], 'url': lic['data']['url'], 'stated_by': lic['data']['stated_by'],
                         'read_from': lic['data']['read_from'], 'read_at': lic['data']['captured_at'],
                         'capture_sha256': lic['data']['capture_sha256'],
                         'pinned_version': record['version'], 'versions_listed': len(versions),
                         'pinned_version_is_latest': True},
        'paper_licence': {'value': lic['paper']['value'], 'quote': lic['paper']['quote'], 'covers': lic['paper']['covers']},
        'other_terms_stated': [{'item': t['item'], 'quote': t['quote'], 'stated_by': t['stated_by']}
                               for t in s['other_terms_stated']],
    }


# ---------------------------------------------------------------------------- Shin2022
ARMS = {
    'training_prior': ('Participant-weighted training prior', 'reference',
                       'No input: always the larger training class, with each training participant weighted equally.'),
    'normalized_spectral_ridge': ('Normalized spectral ridge', 'eeg', None),
    'retrospective_duration_ridge': ('Retrospective duration control', 'retrospective_control', None),
}


def shin_reviews(docs, manifest):
    """The release review passes the aggregate, the consistency review names the export, the audit reconstructs it."""
    src = manifest['sources']
    ex, au = docs['shinExport'], docs['shinReleaseAudit']
    stated(docs['shinResultReview'], '**PASS for limited public aggregate release as a conditional instructed-target '
                                     'diagnostic, outside pure motor-imagery and foundation-model leaderboards.**',
           'Shin release review')
    stated(docs['shinResultReview'], f'`evidence/Shin Signal-Valid Baseline Release Audit.json` | '
                                     f'`{src["shinReleaseAudit"]["sha256"]}`', 'Shin release review binds the audit')
    stated(docs['shinResultReview'], f'| Frozen v2 protocol | `{src["shinProtocol"]["sha256"]}` |',
           'Shin release review binds the protocol')
    cr = docs['moabbConsistencyReview']
    stated(cr, '**PASS.**', 'consistency review')
    stated(cr, f'(SHA256 `{src["shinExport"]["sha256"]}`)', 'consistency review names the export')
    stated(cr, f'(SHA256 `{src["moabbWebsiteHandoff"]["sha256"]}`)', 'consistency review names the handoff')
    stated(cr, 'Export metrics and coverage exactly match the accepted release-audit JSON', 'consistency review')
    require(ex['status'] == 'independently_audited_aggregate_diagnostic' and ex['dataset_id'] == 'Shin2022'
            and ex['dataset_version_doi'] == SHIN_DOI, 'Shin: another export')
    require(ex['protocol_sha256'] == src['shinProtocol']['sha256']
            and ex['independent_audit_sha256'] == src['shinReleaseAudit']['sha256'], 'Shin: the export names other files')
    require(ex['raw_data_included'] is False and ex['participant_rows_included'] is False
            and ex['predictions_included'] is False and ex['models_are_foundation_models'] is False
            and ex['duration_arm_is_retrospective'] is True, 'Shin: the export flags changed')
    require(au['status'] == 'PASS' and au['chain_verified'] is True and au['fixed_mask_verified'] is True
            and au['training_membership_no_heldout'] is True and au['original_strict_v1_preserved'] is True,
            'Shin: the release audit did not pass')
    require(identical(au['independent_metrics'], ex['metrics']), 'Shin: the audit reconstructed other metrics')
    require(identical(au['coverage'], ex['coverage']), 'Shin: the audit covers other windows')
    require(au['hashes']['protocols/Shin Signal-Valid Conditional Baseline Protocol.json'] == src['shinProtocol']['sha256'],
            'Shin: the audit binds another protocol')


def shin_arms(ex, pr):
    feats = pr['features']
    (a0, a1), (b0, b1) = feats['band_bins_hz_inclusive']
    r0, r1 = feats['reference_bins_hz_inclusive']
    alpha = pr['arms']['spectral_ridge']['alpha']
    require(alpha == pr['arms']['duration_diagnostic']['alpha'] == pr['model']['alpha'] == 1.0, 'Shin: another ridge')
    require(pr['arms']['duration_diagnostic']['early_online_decoder'] is False
            and 'known after trial completion' in pr['arms']['duration_diagnostic']['warning'], 'Shin: the duration arm')
    text = {
        'normalized_spectral_ridge': (f'{feats["main_arm_feature_count"]} log band powers relative to each channel’s '
                                      f'{r0}–{r1} Hz power: alpha ({a0}–{a1} Hz) and beta ({b0}–{b1} Hz) on each of the '
                                      f'{feats["channel_count"]} stored channels; ridge with alpha {alpha}, no tuning.'),
        'retrospective_duration_ridge': ('One value: the log of the full feedback duration, which is known only after '
                                         f'the trial ends; ridge with alpha {alpha}.'),
    }
    out = []
    require(tuple(m['arm'] for m in ex['metrics']) == ARM_ORDER, 'Shin: the export lists other arms')
    for m in ex['metrics']:
        require(tuple(sorted(m)) == tuple(sorted(ARM_KEYS)), f'Shin {m["arm"]}: other fields')
        lo, hi = m['participant_bootstrap_percentile_95']
        point = m['participant_mean_balanced_accuracy']
        require(all(number(v) for v in (lo, hi, point, m['pooled_balanced_accuracy_secondary']))
                and 0 <= lo <= point <= hi <= 1, f'Shin {m["arm"]}: the interval does not hold its point')
        name, role, desc = ARMS[m['arm']]
        arm = {k: m[k] for k in ARM_KEYS}        # the export's fields, verbatim
        arm.update({'name': name, 'role': role, 'input': desc or text[m['arm']]})
        out.append(arm)
    return out


def shin_chain(docs):
    ex, pr, la, cr = docs['shinExport'], docs['shinProtocol'], docs['shinLabelDuplicateAudit'], docs['shinCensusReview']
    ob, dc, cov = la['observed'], la['duration_and_coverage'], ex['coverage']
    # The run chain.
    require(ob['raw_duplicate_groups'] == ob['signal_duplicate_groups'] and ob['group_size_histogram'] == {'2': ob['raw_duplicate_groups']}
            and ob['all_duplicate_groups_within_participant'] is True
            and ob['duplicate_condition_pair_histogram'] == {'BW30+NT0': ob['raw_duplicate_groups']}
            and ob['raw_and_signal_duplicate_partitions_identical'] is True, 'Shin: the duplicate pairs changed')
    views, pairs, distinct = ob['record_views'], ob['raw_duplicate_groups'], ob['unique_raw_views']
    require(views - pairs == distinct == ob['unique_signal_payloads'], 'Shin: the distinct runs do not add up')
    incomplete = ob['records_with_unclosed_feedback_at_eof']
    complete = ob['complete_unique_record_views']
    require(distinct - incomplete == complete and incomplete == 1 and 'Hold this incomplete record'
            in la['partial_run']['whole_record_policy'], 'Shin: the incomplete run is not held whole')
    per_run = ob['complete_unique_record_target_count_histogram']
    require(per_run == [{'target1': 12, 'target2': 12, 'record_views': complete}], 'Shin: the runs hold other windows')
    closed = ob['complete_unique_closed_windows']
    by_closed = ob['complete_unique_target_counts']
    require(closed == complete * 24 == cov['source_closed_windows'] == pr['source_closed_windows']
            and by_closed == {'1': complete * 12, '2': complete * 12}, 'Shin: the closed windows do not add up')
    distinct_closed = ob['unique_closed_feedback_windows']
    require(distinct_closed - closed == la['partial_run']['closed_feedback_windows'], 'Shin: 2412 does not add up')
    # The window chain.
    short, by_short = dc['one_second_uncovered_windows'], dc['one_second_uncovered_target_counts']
    eligible, by_eligible = dc['one_second_active_only_covered_windows'], dc['one_second_covered_target_counts']
    require(closed - short == eligible == cov['duration_eligible_windows'] == pr['original_duration_eligible_windows']
            and all(by_closed[t] - by_short[t] == by_eligible[t] for t in ('1', '2'))
            and by_eligible == cr['target_denominators'] and cr['unique_windows'] == eligible
            and pr['eligibility']['coverage']['short_windows'] == short
            and pr['eligibility']['coverage']['short_by_target'] == by_short, 'Shin: the duration step does not add up')
    invalid, by_invalid = cov['signal_invalid_windows'], cov['signal_invalid_targets']
    valid, by_valid = cov['signal_valid_windows'], cov['valid_targets']
    require(eligible - invalid == valid == pr['eligible_windows'] and by_valid == pr['eligible_class_counts']
            and all(by_eligible[t] - by_invalid[t] == by_valid[t] for t in ('1', '2'))
            and by_invalid == pr['signal_validity']['excluded_by_target'], 'Shin: the signal step does not add up')
    sq = ex['signal_qc']
    all_flat = sq['all16_channels_flat']
    joint = cr['independent_joint_patterns']
    require(sq['duration_eligible'] == eligible and sq['signal_invalid'] == invalid and sq['categories_overlap'] is True
            and cr['independent_categories']['all16_constant']['affected_windows'] == all_flat
            and joint.get('000000') == valid and sum(joint.values()) == eligible
            and sorted(v for k, v in joint.items() if k != '000000') == sorted([invalid - all_flat, all_flat]),
            'Shin: the flat windows do not add up')
    require(sq['nonfinite_input'] == 0 == cr['independent_categories']['nonfinite_input']['affected_windows'],
            'Shin: non-finite inputs')
    pct_closed = cov['coverage_percent']
    pct_eligible = pr['signal_validity']['coverage_of2233_percent']
    require(abs(100 * valid / closed - pct_closed) < TOL and abs(100 * valid / eligible - pct_eligible) < TOL,
            'Shin: the coverage percentages')
    require(cov['participants'] == ob['participants_represented_in_complete_unique_pool'] == pr['participant_count']
            and cov['both_targets_each_participant'] is True, 'Shin: the participants')
    return [
        {'id': 'recorded_runs', 'count': views, 'evidence': 'label_and_duplicate_audit',
         'text': 'Runs in the release’s human recordings; the simulated branch is excluded and adds no participant.'},
        {'id': 'byte_identical_pairs', 'count': pairs, 'pair_conditions': ['BW30', 'NT0'], 'within_one_participant': True,
         'evidence': 'label_and_duplicate_audit',
         'text': 'Pairs of runs that are byte-identical: each pair sits within one participant and joins a BW30 run '
                 'and an NT0 run.'},
        {'id': 'distinct_runs', 'count': distinct, 'closed_windows': distinct_closed, 'evidence': 'label_and_duplicate_audit',
         'text': 'Distinct runs once each byte-identical pair counts once.'},
        {'id': 'incomplete_run_held', 'count': incomplete, 'role': 'held', 'evidence': 'label_and_duplicate_audit',
         'text': 'One run ends inside a feedback window; it is held whole.'},
        {'id': 'complete_runs', 'count': complete, 'participants': cov['participants'],
         'windows_per_run_by_target': {'1': 12, '2': 12}, 'evidence': 'label_and_duplicate_audit',
         'text': 'Complete distinct runs, each with twelve closed feedback windows per target.'},
        {'id': 'closed_windows', 'count': closed, 'by_target': dict(by_closed), 'evidence': 'label_and_duplicate_audit',
         'text': 'Closed feedback windows in the complete runs.'},
        {'id': 'shorter_than_one_second', 'count': short, 'by_target': dict(by_short), 'role': 'excluded',
         'evidence': 'label_and_duplicate_audit',
         'text': 'Feedback ended within the first second, so the window holds less than the one second the arms read.'},
        {'id': 'duration_eligible', 'count': eligible, 'by_target': dict(by_eligible), 'evidence': 'signal_census_review',
         'text': 'Windows with at least one second of feedback.'},
        {'id': 'signal_invalid', 'count': invalid, 'by_target': dict(by_invalid), 'flat_on_all_channels': all_flat,
         'flat_on_some_channels': invalid - all_flat, 'non_finite_input_windows': sq['nonfinite_input'],
         'role': 'excluded', 'evidence': 'export',
         'text': 'Windows whose first second is constant on at least one channel, which leaves that channel no '
                 f'{pr["features"]["reference_bins_hz_inclusive"][0]}–{pr["features"]["reference_bins_hz_inclusive"][1]} '
                 'Hz power; the rule was frozen after a score-free census and before any fit.'},
        {'id': 'signal_valid', 'count': valid, 'by_target': dict(by_valid), 'percent_of_closed_windows': pct_closed,
         'percent_of_duration_eligible': pct_eligible, 'participants_with_both_targets': cov['participants'],
         'evidence': 'export',
         'text': 'Signal-valid windows: the population all three arms are scored on.'},
    ]


def shin_catalog(docs, chain):
    cat = next(e for e in docs['moabbShortlist']['entries'] if e['adapter'] == 'Shin2022')['catalog_metadata']
    sem = docs['shinLabelSemantics']
    m = re.search(r'All (\d+) headers show PreFeedbackDuration=2s, ITIDuration=3s, PostFeedbackDuration=1s and '
                  r'MaxFeedbackDuration=(\d+)s\.', flat(sem))
    require(m is not None, 'Shin: the label semantics evidence does not state the feedback cap')
    stated(sem, 'MaxFeedbackDuration is the hard timeout parameter.', 'Shin feedback cap')
    headers, cap = int(m.group(1)), int(m.group(2))
    require(headers == chain[0]['count'], 'Shin: the headers read are not the recorded runs')
    require(cat['Trial (s)'] == str(cap), 'Shin: the catalog trial length is not the feedback cap')
    return {'catalog': 'MOABB dataset summary', 'catalog_trial_seconds': int(cat['Trial (s)']),
            'header_feedback_cap_seconds': cap, 'headers_read': headers,
            'reading': 'The catalog’s six-second trial length is the feedback cap (MaxFeedbackDuration) that every run’s '
                       'header sets.',
            'register': 'MOABB’s catalog trial and run counts for Shin2022 are findings on its register row.'}


def shin_scope(docs, pr):
    ex = docs['shinExport']
    cat = next(e for e in docs['moabbShortlist']['entries'] if e['adapter'] == 'Shin2022')['catalog_metadata']
    require(cat['#Sess'] == '1' and 'one recorded day per person' in ex['limitations'][0], 'Shin: recording days')
    require(cat['#Chan'] == str(pr['features']['channel_count']) and cat['Freq (Hz)'] == str(pr['fs'])
            and cat['#Subj'] == str(pr['participant_count']), 'Shin: the catalog and the protocol disagree')
    return {'participants': ex['coverage']['participants'], 'recording_days_each': int(cat['#Sess']),
            'participant_health': cat['Health'], 'channels': pr['features']['channel_count'], 'sampling_hz': pr['fs'],
            'sensor': cat['Sensor Type'], 'hardware': cat['Hardware'],
            'paradigm': 'closed-loop right/left cursor control with visual feedback',
            'human_recordings_only': True, 'foundation_models': False, 'leaderboard': False, 'core_matrix': False}


def shin_method(docs, pr):
    ex, f, ci = docs['shinExport'], pr['features'], pr['confidence_interval']
    require(ex['evaluation'] == f'{pr["folds"]["outer_fold_count"]}-fold leave-one-participant-out'
            and pr['folds']['scheme'] == 'leave-one-participant-out', 'Shin: another evaluation')
    require(f['segment_samples'] == pr['minimum_window_samples'] == pr['fs'] * f['segment_seconds'], 'Shin: the window')
    require(pr['model']['hyperparameter_search'] is False and pr['folds']['model_selection_or_inner_cv'] is False,
            'Shin: tuning')
    require(pr['metrics']['hypothesis_tests'] == 'none', 'Shin: a hypothesis test')
    require(pr['labels']['result_code_is_label'] is False and pr['labels']['result_code_is_feature'] is False
            and 'ResultCode' in pr['eligibility']['never_filter_on'], 'Shin: ResultCode')
    gate = next(e for e in docs['moabbShortlist']['entries'] if e['adapter'] == 'Shin2022')['scientific_gate']
    require(f['channel_order'].startswith('Recorded channels1..16, retained as EEG1..EEG16; no anatomy/montage inference')
            and 'no electrode labels in headers' in gate, 'Shin: channel names')
    require(ci['enabled'] is True and ci['unit'] == 'participant' and ci['trial_bootstrap'] is False
            and ci['interval'] == 'percentiles2.5and97.5 using np.quantile(method=linear)'
            and 'reuse same matrix for all arms' in ci['index_matrix'], 'Shin: another bootstrap')
    (a0, a1), (b0, b1) = f['band_bins_hz_inclusive']
    method = {
        'evaluation': 'leave-one-participant-out', 'folds': pr['folds']['outer_fold_count'],
        'training_participants_each_fold': pr['folds']['training_participants_per_fold'],
        'window': 'the first second of feedback, read from its recorded start, never extended or padded',
        'window_samples': f['segment_samples'], 'window_seconds': f['segment_seconds'],
        'features': f['main_arm_feature_count'], 'bands_hz': {'alpha': [a0, a1], 'beta': [b0, b1]},
        'reference_band_hz': list(f['reference_bins_hz_inclusive']), 'ridge_alpha': pr['model']['alpha'],
        'tuning': False,
        'channel_names': 'EEG1–EEG16 in stored order; the headers carry no channel names',
        'primary_statistic': 'the unweighted mean of the held-out participants’ balanced accuracies',
        'secondary_statistic': 'balanced accuracy pooled over all signal-valid windows',
        'hypothesis_tests': False, 'label_from_outcome': False,
    }
    interval = {'kind': 'participant bootstrap percentile interval', 'level': 0.95, 'resamples': ci['resamples'],
                'seed': ci['seed'], 'unit': 'participant', 'one_index_matrix_for_all_arms': True,
                'percentile_method': 'linear interpolation', 'descriptive': True}
    labels = {'state': pr['labels']['state'],
              'classes': {k: v.split(',')[0] for k, v in pr['labels']['class_meaning'].items()},
              'outcome_used': False}
    require(labels['classes'] == {'1': 'instructed right target', '2': 'instructed left target'}, 'Shin: the labels')
    return method, interval, labels


def shin_checked(docs, chain):
    zp, cr, pr, au, rr = (docs['shinZeroPowerReview'], docs['shinCensusReview'], docs['shinProtocol'],
                          docs['shinReleaseAudit'], docs['shinResultReview'])
    stated(zp, '**Diagnostic evidence accepted; the current strict baseline remains HOLD.**', 'Shin strict protocol')
    stated(zp, 'Diagnostic evidence records zero fitted models.', 'Shin strict protocol')
    stated(pr['eligibility']['conditional_population_warning'], 'original all-window strict baseline remains failed and '
                                                                'unchanged', 'Shin strict protocol')
    require(cr['status'] == 'PASS' and cr['models_trained'] == 0 and cr['scores_computed'] is False
            and cr['eligibility_changed'] is False, 'Shin: the census was not score-free')
    eligible = next(s for s in chain if s['id'] == 'duration_eligible')['count']
    require(cr['unique_windows'] == eligible, 'Shin: the census read other windows')
    require(pr['frozen'] is True and pr['authorization']['scores_inspected_during_design'] is False
            and pr['authorization']['independent_protocol_approval'].startswith('PASS'), 'Shin: the protocol freeze')
    ia = pr['independent_audit']
    require(ia['predictions_sealed_before_audit'] is True and ia['metrics_computed_only_after_audit'] is True,
            'Shin: the sealing order')
    err = au['independent_audit_max_decision_error']
    require(number(err) and 0 <= err <= ia['decision_value_tolerance']['atol'], 'Shin: the audit decision difference')
    stated(rr, 'This review approves the aggregate values and coverage below.', 'Shin release review')
    return [
        {'id': 'strict-protocol-stopped', 'state': 'held', 'models_fitted': 0,
         'text': 'The first, strict protocol over all duration-eligible windows met a flat signal interval at its '
                 'zero-power gate and stopped before any model was fitted; that attempt stays failed and held.'},
        {'id': 'score-free-census', 'state': 'pass', 'windows': eligible, 'models_trained': cr['models_trained'],
         'scores_computed': False,
         'text': 'A census read the signal of every duration-eligible window, with no model and no score.'},
        {'id': 'second-protocol-frozen', 'state': 'pass', 'scores_inspected_during_design': False,
         'text': 'A second protocol with the signal-validity rule was frozen after the census and before any fit.'},
        {'id': 'predictions-sealed', 'state': 'pass',
         'text': 'Predictions were sealed before the audit; metrics were computed only after it.'},
        {'id': 'independent-audit', 'state': 'pass', 'metrics_reproduced': True, 'max_decision_difference': err,
         'text': 'An independent audit rebuilt every metric from the sealed predictions.'},
        {'id': 'release-review', 'state': 'pass',
         'text': 'An independent release review passed the aggregate values and the coverage for publication.'},
    ]


def shin_holds(docs):
    pr, la, zp = docs['shinProtocol'], docs['shinLabelDuplicateAudit'], docs['shinZeroPowerReview']
    sh = ' '.join(pr['scientific_holds'])
    stated(sh, 'Proven shared aliases are BW30/NT0; NT0/BW60 provenance remains unresolved.', 'Shin holds')
    stated(sh, 'BW/NT/CV treatment causality held, including BW60/BufferLength5s anomaly and30s NT/CV buffers.', 'Shin holds')
    stated(sh, 'Exact deduplication does not establish trial independence; participant and carryover grouping remain '
               'required.', 'Shin holds')
    stated(sh, 'Absolute hardware calibration, physical visual latency and external pretraining overlap remain unproved.',
           'Shin holds')
    stated(sh, 'Missing full montage bars anatomical/ROI/interpolation claims', 'Shin holds')
    stated(la['partial_run']['whole_record_policy'], '12 closed windows may be salvaged only by a separately frozen '
                                                     'objective partial-run rule', 'Shin holds')
    stated(la['duration_and_coverage']['whole_variable_window_contract'], 'may support a separately frozen '
                                                                           'variable-duration input contract', 'Shin holds')
    stated(zp, 'The cause—hardware, acquisition transport, stored sample hold or another mechanism—is unproved',
           'Shin holds')
    return [
        'The paper pairs NT0 with BW60, while the byte-identical runs pair BW30 with NT0; which recording NT0 stands for '
        'is unresolved.',
        'Comparisons between the BW, CV and NT control-parameter conditions are held: one BW60 header records a '
        '5-second buffer, and the NT and CV headers record 30-second defaults.',
        'The incomplete run is held whole; using its closed windows would need its own frozen rule.',
        'A task over every closed window, whatever its duration, would need its own frozen protocol.',
        'The full scalp montage, the display latency, the absolute hardware calibration and any overlap with '
        'pretraining corpora are unestablished.',
        'The physical cause of the flat intervals is unknown.',
        'Exact deduplication leaves trials dependent within each participant and run sequence; every run of a '
        'participant stays in that participant’s fold.',
    ]


def shin_rights(docs, a3):
    s = a3['sources']['shin2022']
    record, versions = figshare(docs, s)
    require(record['doi'] == SHIN_DOI and s['paper'] == f'https://doi.org/{SHIN_PAPER_DOI}', 'Shin: another record')
    authors = [a['full_name'] for a in record['authors']]
    require(authors == ['Hyonyoung Shin', 'Daniel Suma', 'Bin He'], 'Shin: other creators')
    desc = strip_tags(record['description'])
    m = re.search(r'Shin H, Suma D and He B \((\d{4})\) (.+?)\. Front\. Hum\. Neurosci\. (\d+):(\d+)\. doi:(\S+)', desc)
    require(m is not None and m.group(5) == SHIN_PAPER_DOI, 'Shin: the record does not cite its paper')
    year, paper_title, volume, article = m.group(1), m.group(2), m.group(3), m.group(4)
    stated(desc, 'Please cite the above paper if you use any data included in this dataset.', 'Shin citation request')
    stated(desc, 'All identifying information have been removed.', 'Shin de-identification')
    code = 'https://github.com/mcvain/bci-simulator'
    stated(desc, code, 'Shin linked code')
    title = record['title']
    attribution = (f'{names_and(authors)} · {title}, figshare, doi:{SHIN_DOI}, {record["license"]["name"]}. Paper: '
                   f'{names_and(authors)}, {paper_title}, Frontiers in Human Neuroscience {volume}:{article} ({year}), '
                   f'doi:{SHIN_PAPER_DOI}. Funding: {record["funding"]}. Modifications: canonical deduplication of the '
                   'byte-identical runs, first-second window selection and signal-validity filtering. '
                   f'{ATTRIBUTION_END}')
    e, c = s['ethics'], s['consent']
    require(e['approval_number'] is None, 'Shin: an approval number appeared; the privacy line must be reviewed')
    privacy = (f'{e["statement"]} {c["statement"]} The data record states that all identifying information has been '
               'removed. Published here: each arm’s participant-mean balanced accuracy with its participant-bootstrap '
               'interval and pooled secondary value, and aggregate run and window counts; no per-participant value, '
               'identifier, prediction or signal.')
    terms = terms_block(s, record, versions)
    terms['linked_code'] = {'url': code, 'note': 'The simulator code is a separate work linked from the data record; '
                                                 'the data licence covers the data record.'}
    rights = {
        'name': f'Shin2022 · {title} ({names_and([a.split()[-1] for a in authors])})',
        'task': 'Closed-loop right/left cursor control with visual feedback; the label is the instructed target.',
        'source': f'https://doi.org/{SHIN_DOI}',
        'version': (f'Figshare record 20383716, version {record["version"]}, the only version the record lists'
                    if len(versions) == 1 else f'Figshare record 20383716, version {record["version"]}'),
        'license': record['license']['name'], 'licenseUrl': DEED, 'attribution': attribution,
        'reviewedAt': s['captured_at'][:10],
        'reviewBasis': [s['licence']['data']['read_from'], s['read_from']],
        'privacyReview': privacy,
        'terms': terms,
    }
    return rights, consent_block(s, 'Shin2022')


def shin_case(docs, manifest, a3):
    shin_reviews(docs, manifest)
    ex, pr = docs['shinExport'], docs['shinProtocol']
    arms = shin_arms(ex, pr)
    chain = shin_chain(docs)
    method, interval, labels = shin_method(docs, pr)
    require(interval['resamples'] == docs['shinReleaseAudit']['bootstrap']['resamples']
            and interval['seed'] == docs['shinReleaseAudit']['bootstrap']['seed'], 'Shin: the audit bootstrap differs')
    rights, consent = shin_rights(docs, a3)
    r0, r1 = pr['features']['reference_bins_hz_inclusive']
    caveat = ('The scores cover the signal-valid windows only: feedback lasting at least one second, and a first second '
              f'that is finite with positive {r0}–{r1} Hz power on all {pr["features"]["channel_count"]} channels. The '
              'label is the instructed target in closed-loop cursor recordings, which carry visual, controller and '
              'behaviour confounds. The duration control reads the whole feedback duration, known only after the trial '
              'ends, so it checks a confound; the spectral arm sits close to it, and no test between arms was run. '
              f'{word(ex["coverage"]["participants"]).capitalize()} participants, one recording day each; the intervals '
              'are descriptive.')
    return {
        'id': 'shin2022', 'kind': 'worked_case', 'section': 'shin2022', 'name': 'Shin2022',
        'question': SHIN_QUESTION,
        'task': 'Right-versus-left instructed target in the first second of cursor feedback, for a participant held '
                'out entirely.',
        'scope': shin_scope(docs, pr),
        'labels': labels,
        'method': method,
        'interval': interval,
        'arms': arms,
        'caveat': caveat,
        'coverage_chain': chain,
        'catalog': shin_catalog(docs, chain),
        'how_checked': shin_checked(docs, chain),
        'holds': shin_holds(docs),
        'rights': rights,
        'consent_and_ethics': consent,
    }


# ---------------------------------------------------------------------------- eldBETA (D2: status and counts only)
def eldbeta_case(docs, manifest, a3):
    ex, au, qc = docs['eldbetaExport'], docs['eldbetaReleaseAudit'], docs['eldbetaRawQc']
    src = manifest['sources']
    require(ex['status'] == 'independently_audited_single_participant_diagnostic' and ex['dataset_version_doi'] == ELD_DOI
            and ex['eligible_for_cohort_or_foundation_model_leaderboard'] is False, 'eldBETA: another export')
    require(ex['independent_audit']['audit_sha256'] == src['eldbetaReleaseAudit']['sha256'],
            'eldBETA: the export names another audit')
    require(au['status'] == 'PASS_limited_diagnostic_release' and au['predictions_exact'] is True
            and au['protocol_sha256'] == ex['independent_audit']['protocol_sha256'], 'eldBETA: the audit did not pass')
    require(qc['status'] == 'PASS' and qc['scores_computed'] is False and au['raw_qc_output_sha256'] == qc['report_sha256'],
            'eldBETA: the raw QC is not the one the audit binds')
    stated(docs['eldbetaConsistencyReview'], '**PASS.**', 'eldBETA consistency review')
    stated(docs['eldbetaConsistencyReview'], f'SHA256{src["eldbetaExport"]["sha256"]}', 'eldBETA consistency review')
    stated(docs['eldbetaResultReview'], 'All63 prescribed windows were retained; continuous-recording248320nonfinite '
                                        'values remain a separate unresolved limitation, with zero in selected windows.',
           'eldBETA result review')
    for k in ('blocks', 'targets', 'trials', 'trials_dropped'):
        require(count(ex[k]) and ex[k] == au[k], f'eldBETA {k}: the audit counts otherwise')
    require(ex['participants_evaluated'] == au['participants'] == 1, 'eldBETA: one participant')
    sq = ex['source_qc']
    require(sq['prespecified_windows_valid'] == qc['valid_trials'] == ex['trials'] and qc['trials_dropped'] == 0
            and sq['nonfinite_values_in_prespecified_windows'] == qc['selected_window_nonfinite_values'] == 0
            and sq['nonfinite_scalar_values_in_complete_continuous_recordings'] == qc['continuous_nonfinite_values']
            and qc['blocks'] == ex['blocks'] and sq['no_raw_crop_repair_or_mutation'] is True,
            'eldBETA: the raw QC counts otherwise')
    outside = sq['nonfinite_scalar_values_in_complete_continuous_recordings'] - sq['nonfinite_values_in_prespecified_windows']
    require(ex['preprocessing'].startswith('Original header calibration;'), 'eldBETA: the header calibration')
    stated(docs['eldbetaHandoff'], 'It applies the original affine physical/digital calibration', 'eldBETA calibration')
    stated(docs['eldbetaTimingUnits'], 'Independent GDF-code/calibration audit and MAT-to-raw amplitude correspondence '
                                       'remain unresolved.', 'eldBETA units')
    require('Derived MAT amplitude, resampling and raw-to-MAT equivalence remain unresolved and unused' in ex['limitations'],
            'eldBETA: the derived MATLAB epochs')
    s = a3['sources']['eldbeta']
    record, versions = figshare(docs, s)
    require(record['doi'] == ELD_DOI and s['paper'] == f'https://doi.org/{ELD_PAPER_DOI}', 'eldBETA: another record')
    desc = strip_tags(record['description'])
    m = re.search(r'from (\d+) elder subjects, each of whom performed (\w+) blocks of (\d+)-target', desc)
    require(m is not None and m.group(2) == word(ex['blocks']) and int(m.group(3)) == ex['targets'],
            'eldBETA: the record describes another design')
    published = int(m.group(1))
    authors = [a['full_name'] for a in record['authors']]
    require(authors == ['Bingchuan Liu', 'Yijun Wang', 'Xiaorong Gao', 'Xiaogang Chen'], 'eldBETA: other creators')
    counts = {'participants_run': ex['participants_evaluated'], 'published_participants': published,
              'blocks': ex['blocks'], 'targets': ex['targets'], 'trials': ex['trials'],
              'trials_passing_checks': sq['prespecified_windows_valid'], 'trials_dropped': ex['trials_dropped'],
              'non_finite_values_in_analysed_windows': sq['nonfinite_values_in_prespecified_windows'],
              'non_finite_values_outside_analysed_windows': outside}
    status_text = (f'The raw-recording route runs end to end on one participant’s {word(ex["blocks"])} blocks: all '
                   f'{ex["trials"]} trials pass the reader and the quality checks, none dropped. The continuous recordings '
                   f'hold {outside:,} non-finite values outside the analysed windows, left as recorded. With one person '
                   'every score is that person’s, so the accuracy is held.')
    fm = docs['foundationModels']['results']['foundation-models-v9']['pretraining_exposure']
    cell = next(c for c in fm['cells'] if c['model'] == 'singlem' and c['dataset'] == 'beta')
    model = next(x for x in fm['models'] if x['key'] == 'singlem')
    stated(cell['evidence'], 'Only eldBETA (Liu 2022, ref [91], 100 older adults)', 'SingLEM exposure row')
    stated(cell['evidence'], 'eldBETA is a different database from BETA', 'SingLEM exposure row')
    require(model['name'] == 'SingLEM', 'SingLEM: another model name')
    e, c = s['ethics'], s['consent']
    privacy = (f'{e["statement"]} {c["statement"]} Published here: counts for one participant’s recordings (blocks, '
               'targets, trials, trials dropped and non-finite values) and no score; no identifier, per-trial value or '
               'signal.')
    attribution = (f'{names_and(authors)} · {record["title"]}, figshare, doi:{ELD_DOI}, {record["license"]["name"]}. '
                   f'Data descriptor: Scientific Data, doi:{ELD_PAPER_DOI}. Funding: {record["funding"]}. Modifications: '
                   'decoding of the original recording format with the header calibration, and fixed channel and window '
                   f'selection; no score from these data is published. {ATTRIBUTION_END}')
    rights = {
        'name': f'{record["title"]} (Liu, Wang, Gao and Chen)',
        'task': 'Nine-target SSVEP selection by older adults, recorded in seven blocks per person.',
        'source': f'https://doi.org/{ELD_DOI}',
        'version': (f'Figshare record 18032669, version {record["version"]}, the latest of the {len(versions)} versions '
                    'the record lists'),
        'license': record['license']['name'], 'licenseUrl': DEED, 'attribution': attribution,
        'reviewedAt': s['captured_at'][:10],
        'reviewBasis': [s['licence']['data']['read_from'], s['read_from']],
        'privacyReview': privacy,
        'terms': terms_block(s, record, versions),
    }
    require(rights['task'].startswith(f'{word(ex["targets"]).capitalize()}-target') and 'seven blocks' in rights['task']
            and ex['blocks'] == 7, 'eldBETA: the task line')
    return {
        'id': 'eldbeta', 'kind': 'status_case', 'section': 'eldbeta', 'status': 'score_held', 'name': 'eldBETA',
        'counts': counts,
        'flags': {'header_calibration_applied': True, 'derived_matlab_epochs_used': False, 'recordings_repaired': False,
                  'score_published': False},
        'status_text': status_text,
        'held': {'what': 'the one-participant training-free CCA accuracy',
                 'reason': 'With one person every score is that person’s.',
                 'decision': 'the owner’s decision for this release, keeping the one-person rule'},
        'holds': [
            'The derived MATLAB epochs were not used: their amplitude scale, resampling and exact endpoints are '
            'unestablished.',
            'The raw recordings were read with the header calibration applied; the recorded unit code has no '
            'independent audit.',
            'The non-finite values in the continuous recordings are neither located nor explained.',
            f'The other {published - ex["participants_evaluated"]} published participants are neither acquired nor '
            'evaluated.',
        ],
        'related': {'fact': 'eldBETA is in SingLEM’s published pretraining list, as SingLEM’s exposure row on BETA '
                            'records; eldBETA and BETA are separate databases.',
                    'file': 'foundation-models-update.json', 'model': 'singlem', 'model_name': model['name'],
                    'dataset': 'beta'},
        'rights': rights,
        'consent_and_ethics': consent_block(s, 'eldBETA'),
    }


# ---------------------------------------------------------------------------- ZuCo 2.0 (status only, no figure)
def zuco_case(docs, manifest):
    h, rv, gate, aa = docs['zucoHandoff'], docs['zucoReleaseReview'], docs['zucoIntakeGate'], docs['zucoAlignmentAudit']
    require(rv['status'] == 'independent_aggregate_release_review_passed'
            and rv['handoff_sha256'] == manifest['sources']['zucoHandoff']['sha256'],
            'ZuCo2: the review binds another handoff')
    zc = rv['zuco_handoff_cross_check']
    require(zc['run_specific_alignment_hold_retained'] is True and zc['no_correction_or_row_drop_or_zuco_score_claimed']
            is True and zc['no_extension_to_whole_corpus_or_original_OSF'] is True, 'ZuCo2: the review checks changed')
    stated(h, '**run-specific fixation-alignment hold**', 'ZuCo2 handoff')
    stated(h, 'No correction or row deletion is justified. This finding does not apply to the whole ZuCo2 corpus or '
              'original OSF data. No EEG–text model score is released.', 'ZuCo2 handoff')
    fl = aa['flags']
    require(aa['status'] == 'independent_alignment_gate_failed' and aa['eeg_payload_fetched'] is False
            and (fl['onset_beyond_recording'] > 0 or fl['end_beyond_recording'] > 0) and aa['markers_within_recording'] is True
            and aa['action'] == 'Hold fixation-based alignment; no repair, deletion, model fit or score',
            'ZuCo2: the alignment audit changed')
    ident, terms = gate['identity'], gate['terms']
    require(ident['dataset_id'] == 'nm000279' and ident['archive_version'] == 'v1.0.0'
            and terms['dataset_declared_license'] == 'CC-BY-4.0', 'ZuCo2: another identity or licence')
    stated(terms['limit'], 'No public subject/text redistribution authorized by this gate.', 'ZuCo2 redistribution')
    stated(terms['limit'], 'original OSF terms', 'ZuCo2 terms')
    stated(terms['stimulus_source_description'], 'no per-excerpt attribution/source URLs or separate third-party text '
                                                 'license', 'ZuCo2 terms')
    return {
        'id': 'zuco2', 'kind': 'status_case', 'section': 'zuco2', 'status': 'no_score', 'name': ZUCO_NAME,
        'finding': 'In one converted run on NEMAR, some fixation times fall outside the recording; the run’s stimulus '
                   'markers lie within it.',
        'hold': ZUCO_HOLD,
        'scope': 'The hold covers that one converted run; no timing was corrected and no row removed.',
        'clears_when': [
            'the exact converter revision, configuration and environment, with its rules for casts, time origin and '
            'boundaries',
            'a source-checksummed timing fixture with the original start and end timestamps and the recording’s start '
            'and end clocks',
            'the canonical mapping of triggers, sentences and runs',
        ],
        'flags': {'fixation_times_outside_recording': True, 'stimulus_markers_within_recording': True,
                  'timing_corrected': False, 'rows_removed': False, 'score_computed': False, 'data_redistributed': False},
        'consent_and_ethics': {'read': False, 'gap': 'No consent or ethics statement for this dataset was read in this '
                                                     'release.'},
        'source': {
            'name': ZUCO_NAME, 'repository': 'NEMAR', 'accession': ident['dataset_id'],
            'version': ident['dataset_description_version'], 'doi': ident['version_doi'].removeprefix('https://doi.org/'),
            'url': ident['version_base'], 'licence_as_stated': terms['dataset_declared_license'],
            'licence_stated_by': 'the dataset_description.json of that version',
            'terms_unverified': ['the original terms on OSF', 'terms for the text excerpts the stimuli quote'],
            'citation': terms['acknowledgement'],
        },
    }


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {here}')
            if here.startswith('$.eldbeta'):
                require(not any(f in k.lower() for f in HELD_SCORE_KEY_FRAGMENTS), f'held-score field in export: {here}')
            scrub_check(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')


DATASET_ID = re.compile(r'[A-Z][a-z]+\d{4}[A-Za-z]*')     # a dataset's catalog name, such as Shin2022


def malformed(text):
    """In prose, a word that has lost its space against a number (the export's “Only10participants”)."""
    if not re.search(r'\s', text):
        return None                                 # identifiers and single tokens are not prose
    for token in text.split():
        t = re.sub(r"['’]s$", '', token.strip('.,;:()[]“”"‘’\''))
        if ('/' in t or ':' in t or t.startswith('10.') or HEX.fullmatch(t) or t.startswith('http')
                or DATASET_ID.fullmatch(t)):
            continue
        if re.search(r'[a-z]{3,}\d|\d[a-z]{3,}', t):
            return t
    return None


def prose_check(payload, private):
    for trail, text in strings(payload):
        require(not LOCAL_ROOTS.search(text), f'private path in export: {trail}')
        require(not SOURCE_IDS.search(text), f'source file or participant identifier in export: {trail}')
        require(not OUT_OF_FILE.search(text), f'{trail}: register-only, conference or submission content')
        require(not FIFTY_FIVE.search(text), f'{trail}: the commenter’s figure')
        require(not HELD_TEXT.search(text), f'{trail}: a held or withheld figure in text')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.IGNORECASE),
                    f'private host or storage name in export: {trail}')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        if trail in ('$.schema_version', '$.release_id') or text.startswith('http') or HEX.fullmatch(text):
            continue
        bad = malformed(text)
        require(bad is None, f'{trail}: a string that has lost its spaces ({bad!r})')
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):    # the release record is dated by design (/releases/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail.endswith(QUOTED_SUFFIXES) or trail.startswith('$.provenance'):
            continue
        if not trail.endswith('.attribution'):          # the attribution ends with the site's fixed sentence
            require(not HEDGE.search(text), f'{trail}: an “X, not Y” hedge: {text!r}')
        require(not CLAIMS.search(text), f'{trail}: a claim these results do not support: {text!r}')


def zuco_has_no_figure(payload):
    """Outside its anchor, name and source identity, the ZuCo 2.0 case carries no number and no digit."""
    z = payload['zuco2']
    for trail, v in leaves(z, '$.zuco2'):
        if trail in ('$.zuco2.id', '$.zuco2.section', '$.zuco2.name') or trail.startswith('$.zuco2.source'):
            continue
        require(not number(v), f'{trail}: a figure in the ZuCo 2.0 case')
        require(not (isinstance(v, str) and re.search(r'\d', v)), f'{trail}: a digit in the ZuCo 2.0 case')


def eldbeta_has_no_score(payload, docs):
    ex = docs['eldbetaExport']
    held = {ex['top1_accuracy'], ex['fixed_first_frequency_comparator']['accuracy'],
            ex['independent_audit']['max_correlation_residual']}
    require(not held & set(floats(payload)), 'the held eldBETA score reached the export')
    require(ex['correct'] not in ints(payload), 'the held eldBETA count of correct trials reached the export')


def withheld_values(docs):
    """Figures the sources hold that this release does not publish: per-participant ranges, the duration
    distribution, the held eldBETA score, MOABB's catalog counts, run-level ZuCo2 values and compute accounting."""
    fl, it = set(), set()
    la, pr, cr = docs['shinLabelDuplicateAudit'], docs['shinProtocol'], docs['shinCensusReview']
    dc, ob = la['duration_and_coverage'], la['observed']
    fl |= set(dc['feedback_quantiles_seconds'].values()) | {dc['feedback_mean_seconds'],
                                                            dc['one_second_active_only_coverage_percent'],
                                                            la['decision']['one_second_planning_contract']['coverage_percent']}
    for k, v in list(dc.items()) + list(pr['eligibility']['coverage'].items()):
        if 'per_participant' in k:
            it.add(v)
    for cat in cr['independent_categories'].values():
        it |= set(cat['participant_denominator_min_max']) | set(cat['unflagged_windows_per_participant_min_max'])
    it |= {ob['samples_including_duplicate_views'], ob['feedback_windows_including_duplicate_views'],
           ob['closed_feedback_windows_including_duplicate_views'], ob['extra_duplicate_closed_windows']}
    au = docs['shinReleaseAudit']
    fl |= {a[k] for a in au['accounting'] for k in ('cpu_seconds', 'wall_seconds')}
    it |= {au['combined_output_bytes'], au['source_bytes']}
    cat = next(e for e in docs['moabbShortlist']['entries'] if e['adapter'] == 'Shin2022')['catalog_metadata']
    it |= {int(cat['#Trials']), int(cat['#Runs'])}
    ex = docs['eldbetaExport']
    fl |= {ex['top1_accuracy'], ex['fixed_first_frequency_comparator']['accuracy'],
           ex['independent_audit']['max_correlation_residual']}
    it.add(ex['correct'])
    fl |= set(floats(docs['zucoFollowup'])) | set(floats(docs['zucoAlignmentAudit']))
    it |= {v for v in ints(docs['zucoAlignmentAudit']) if v > 16}
    for s in strings(docs['zucoFollowup']):
        for x in re.findall(r'-?\d+\.\d+', s[1]):
            fl.add(float(x))
    # Small per-participant counts (a minimum of 8 short windows) cannot be told apart by value from published counts
    # (8 windows flat on all channels); those keys are refused by name, and only the larger ones are checked by value.
    it = {v for v in it if v > 16} | {int(cat['#Trials']), int(cat['#Runs']), ex['correct']}
    return fl - TRIVIAL, it


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    owner_decisions(manifest)
    docs = load(manifest)
    a3 = docs['consent']
    require(a3['package'] == 'A3' and a3['release_freeze'] == RELEASE_ID.rsplit('-', 1)[1], 'another consent record')
    shin = shin_case(docs, manifest, a3)
    eld = eldbeta_case(docs, manifest, a3)
    zuco = zuco_case(docs, manifest)
    rr = manifest['releaseRecord']
    src = manifest['sources']
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['release_date'],
        'status': 'aggregate_preview',
        'title': 'Checked end to end',
        'question': QUESTION,
        'placement': {'page': '/topics/data-quality/', 'group': 'reliability',
                      'sections': ['shin2022', 'eldbeta', 'zuco2'], 'leaderboard': False, 'core_matrix': False},
        'metric_units': ('balanced accuracies and their interval bounds are proportions in [0,1]; the percent fields of '
                         'the coverage chain are percentages; counts of runs, windows, trials, blocks, targets, '
                         'participants, channels and values are whole numbers; null means not stated, never zero'),
        'scope': ('Three public EEG datasets read from their files: Shin2022 as a worked case, with a participant-held-out '
                  'diagnostic and the chain from the release’s recorded runs to the windows it is scored on, and '
                  'eldBETA and ZuCo 2.0 as status cases with no score. Outside every leaderboard and the core matrix.'),
        'cases': [{'id': 'shin2022', 'kind': 'worked_case', 'status': 'released'},
                  {'id': 'eldbeta', 'kind': 'status_case', 'status': 'score_held'},
                  {'id': 'zuco2', 'kind': 'status_case', 'status': 'no_score'}],
        'shin2022': shin,
        'eldbeta': eld,
        'zuco2': zuco,
        'holds': [dict(h) for h in manifest['holds']],
        'not_published': manifest['notPublished'],
        'release_record': {'date': rr['date'], 'decided': manifest['reviewed_at'], 'decision': rr['decision'],
                           'eldbeta': rr['eldbeta'], 'zuco2': rr['zuco2'], 'placement': rr['placement']},
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {'shin2022': src['shinExport']['sha256'], 'eldbeta': src['eldbetaExport']['sha256']},
            'release_audit_sha256': {'shin2022': src['shinReleaseAudit']['sha256'],
                                     'eldbeta': src['eldbetaReleaseAudit']['sha256']},
            'protocol_sha256': {'shin2022': src['shinProtocol']['sha256'],
                                'eldbeta': docs['eldbetaExport']['independent_audit']['protocol_sha256']},
            'evidence_sha256': {'label_and_duplicate_audit': src['shinLabelDuplicateAudit']['sha256'],
                                'signal_census_review': src['shinCensusReview']['sha256'],
                                'eldbeta_raw_qc': src['eldbetaRawQc']['sha256'],
                                'zuco2_alignment_audit': src['zucoAlignmentAudit']['sha256'],
                                'consent_statements': manifest['consent']['statements']['sha256']},
            'released_files_unchanged': ['foundation-models-update.json'],
            'holds': [h['id'] for h in manifest['holds']],
        },
    }
    require([h['case'] for h in payload['holds']] == ['eldbeta', 'zuco2'], 'the holds changed')

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 3, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    zuco_has_no_figure(payload)
    eldbeta_has_no_score(payload, docs)
    validate_public(payload)
    fl, it = withheld_values(docs)
    require(not (fl & set(floats(payload))), f'a withheld value reached the export: {sorted(fl & set(floats(payload)))[:3]}')
    require(not (it & set(ints(payload))), f'a withheld count reached the export: {sorted(it & set(ints(payload)))[:3]}')
    require(not any(number(v) and v in (55, 0.55) for _, v in leaves(payload)), 'the commenter’s figure as a value')
    return payload


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


def inputs_available():
    """Whether the pinned inputs are on this machine. They are not in the public repository: the research folders and
    the review's evidence are local. A clone still checks the served file against the committed export audit's hash;
    only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest)) and (REVIEW / 'evidence/captures').is_dir()


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_data_quality_export
    return audit_data_quality_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
