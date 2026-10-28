"""Release the ten-second EEGMAT probes of two frozen encoders, aggregate-only, as one separate pilot-studies panel.

EEG-Captioner's encoder and AXON stay frozen. Each is read by one fixed ridge head in five subject-disjoint folds on the
same 432 ten-second EEGMAT windows from 36 people (six from the first minute of each of 72 recordings, 19 channels at
200 Hz), and each is set against Welch band power on the same windows: matched and fitted in EEG-Captioner's run, and
the same predictions reused without refitting for AXON. Scores are participant-mean balanced accuracies; each paired
difference carries a 20,000-draw paired participant-bootstrap interval. The two encoders are two separate subsections:
no encoder-against-encoder difference is computed. The owner's decision D14 of 2026-10-28 publishes both; neither
research record grants website authority. The panel sits outside the pilot count and every leaderboard, in its own
file: mvp.json, eegpt-core-update.json, adaptation-update.json, neurolm-eegmat-update.json and pilot-studies-update.json
keep their bytes.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- release status from each study's own approval record (EEG-Captioner's release approval, AXON's independent release
  review), never from an aggregate's status field, and only if each record binds the pinned aggregate, handoff and
  audit by SHA-256;
- EEG-Captioner's scores from the independent result-audit outcome, equal to the interpretation review's verified
  numbers and the handoff's table; AXON's from the released aggregate, equal to the corrected audit's producer and
  independent scores; both equal to the consolidated handoff's displayed figures;
- the shared Welch baseline: AXON's frozen protocol names EEG-Captioner's sealed baseline predictions, physical array
  and audit outcome by SHA-256, and both records give the same baseline score;
- the cohort, preprocessing, head, bootstrap and source-QC rule from the frozen protocols, the QC totals from the
  audit outcome's aggregate summary, equal to every other record that states them;
- identities and licences from the two intake records: EEG-Captioner's intake handoff and its approval, AXON's final
  checkpoint intake admission, the model card and access record it binds, and the strict-load packet.
The research records carry private storage paths and host names, so they are pinned and checked, never published.

What this export refuses:
- per-person, per-fold and per-window values, fold assignments, confusion matrices, pooled macro-F1, the source-QC
  breakdown beyond its totals, forward and fit counts, CPU and wall time and memory, by key and, where the sources hold
  them, by value; any figure of another EEGMAT result on the site;
- a release without both approval records, a baseline that is not the shared one, an interval that does not hold its
  estimate or no longer spans zero, a resolved exposure or a licence the pinned records do not state;
- private paths, host, volume and user names (read at run time from the pinned records, never spelled here), a version
  label, an update marker or a month used as a label in the text, Jev, the commenter's figure, any ICLR 2027 or
  submission reference, an arXiv citation for AXON, MIT beside a weight, and a claim these results do not support
  unless it is negated.

    python3 pipeline/publication/export_eegmat_ten_second_update.py
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261028'
MANIFEST = REVIEW / 'eegmat-ten-second-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'eegmat-ten-second-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/eegmat-ten-second-update.json',
           PROJECT / 'site/public/data/eegmat-ten-second-update.json')
RELEASE_ID = 'eegmat-ten-second-update-20261028'
SCHEMA = 'bci-report-eegmat-ten-second-update-v1'
RESEARCH_ROOT = 'research/autonomous_validation_20261026/'
OWNER_DECISIONS = 'research/publication_review_20261028/owner-decisions.json'
GROUPS = ('captioner', 'axon', 'planning', 'published')

CAPTIONER_STATUS = 'PASS_INTERNAL_CONDITIONAL_PROBE_HANDOFF'
AXON_DECISION = 'PASS_CONDITIONAL_AGGREGATE_RELEASE'
AXON_RELEASE_STATUS = 'AUDITED_CONDITIONAL_RELEASE'
INTAKE_STATUS = 'PASS_CANONICAL_ENCODER_ONLY_INTAKE_HANDOFF'
SPANS_ZERO = ('the interval spans zero, so neither is shown to be better, and the two are not shown to be '
              'equivalent')          # the pilot-studies sentence, reused as the plan requires
CAPTIONER_LABEL = 'EEG-Captioner encoder, mean-token 256-d + ridge'
AXON_LABEL = 'AXON, 512-d + ridge'
WELCH_LABEL = 'Welch band power (95-d, 0.5–45 Hz, ten-second windows)'
WELCH_MATCHED = 'matched for this run'
WELCH_REUSED = 'the same predictions reused without refitting; not matched for normalisation or parameter count'
TOL = 1e-12
WORDS = {2: 'two', 5: 'five', 6: 'six', 10: 'ten'}

REFUSED_KEYS = PER_PERSON_KEYS | {
    'minimum', 'maximum', 'range', 'q1', 'q3', 'seconds', 'checks', 'seal', 'source_files', 'splits', 'rows', 'folds_ba',
    'accuracy', 'flagged_channels', 'bad_trials', 'receipt_sha256', 'checked_files', 'actor', 'reviewer'}
REFUSED_KEY_FRAGMENTS = ('per_person', 'per_participant', 'per_subject', 'per_fold', 'per_trial', 'per_window',
                         'per_class', 'per_condition', 'subject', 'prediction', 'probabilit', 'feature', 'confusion',
                         'percentile', 'quantile', 'median', 'elapsed', 'timing', 'wall', 'cpu', 'rss', 'memory',
                         'forward', 'pooled', 'macro', 'device', 'platform', 'environment', 'private', 'path', 'host',
                         'folder', 'worker', 'lock', 'fold_size', 'fold_assign')
# Two audit facts whose names carry a refused fragment: one number and one flag about the feature rows and the hard
# predictions, never the features or predictions themselves. Allowed only at these keys, in the two audit blocks.
AUDIT_FACT_KEYS = {'feature_max_abs_error', 'hard_predictions_reproduced_exactly'}
AUDIT_FACT_PARENT = re.compile(r'^\$\.(?:eeg_captioner\.audit|axon\.audit\.corrected_audit)$')
# What the not-published list must name, whatever else it says (plan section 2.3 and the brief).
NOT_PUBLISHED_PHRASES = ('per-fold balanced accuracy', 'fold assignments', 'participant identifiers', 'predictions',
                         'Confusion matrices', 'pooled macro-F1', 'flagged channel-record instances',
                         'counts by condition and by fold', 'forward counts', 'CPU and wall time',
                         'A difference between the two encoders', 'AXON’s paper reference', 'Checkpoints and weights')
DECISION_ID = re.compile(r'(?<![\w-])D\d{1,2}(?![\w-])')   # an owner-decision id is internal, never reader text
LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root|opt|var)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsubj\d+|\bSubject\d+|\.(?:npz|npy|edf|mat|md|py|h5)\b'
                        r'|(?<![\w-])(?:independent-result-audit-outcome|independent-result-audit-preparation'
                        r'|release-approval|interpretation-review|producer-ledger|binding\.frozen|producer\.frozen'
                        r'|audit\.frozen|rows|lineage|qc|qc-summary|scores|guard-receipt|receipt|access)\.json',
                        re.IGNORECASE)
TRIVIAL = {0.0, 0.5, 1.0, 2.0}
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
COMMENTER = re.compile(r'(?<![\d.,])55(?:\.0+)?\s*(?:%|per ?cent|percent)|\b0\.55\b', re.IGNORECASE)
SUBMISSIONS = re.compile(r'ICLR\s*2027|\bsubmission', re.IGNORECASE)
ARXIV = re.compile(r'arxiv|2609\.08788', re.IGNORECASE)
CLAIMS = re.compile(r'outperform|\bbeats?\b|\bimprov|superior|\bbetter\b|\badvantage|\bharm|instruction[- ]tuned'
                    r'|question[- ]answer|zero-shot|\bunseen\b|never saw|\bcausal|cognitive workload|\bclinical\b'
                    r'|\bmedical\b|\bonline\b|real-time|closed-loop|\bendorse|equivalen|significan|\bclean\b'
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


def signed(v, minus='−'):
    """A fraction as signed percentage points with two decimals, as the site prints them."""
    return f'{100 * v:+.2f}'.replace('-', minus)


def pct(v, places=2):
    return f'{100 * v:.{places}f}'


def tol(v):
    """A tolerance as the handoffs write it: 1e-6, not 1e-06."""
    return re.sub(r'e-0*(\d)', r'e-\1', f'{v:.0e}')


def long_float(v):
    """A measured value rather than a design constant: a float with more than four decimals."""
    return isinstance(v, float) and math.isfinite(v) and v != round(v, 4)


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


def research_name(ref, root):
    """The path a research record uses for its neighbours: relative to the folder that holds them."""
    require(root in ref['path'], f'{Path(ref["path"]).name}: outside {root}')
    return ref['path'].split(root, 1)[1]


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {g: {k: read_pinned(r, k) for k, r in manifest[g].items() if isinstance(r, dict)} for g in GROUPS}
    docs['refs'] = {g: manifest[g] for g in GROUPS}
    return docs


def owner_decision(manifest):
    """D14 as the manifest quotes it, and only while it is the current value at its key."""
    owner = json.loads((PROJECT / OWNER_DECISIONS).read_bytes())
    quoted = manifest['approval']['ownerDecisions']
    require(quoted['path'] == OWNER_DECISIONS, 'the manifest quotes another decision file')
    require(owner['freeze_date'] == manifest['freeze_date'].replace('-', '') == RELEASE_ID.rsplit('-', 1)[1],
            'the freeze date is not the release id’s')
    require(owner['decisions']['D14']['answer'] == quoted['quoted']['D14'], 'owner decision D14 changed')
    stated(quoted['quoted']['D14'], 'the EEG-Captioner and AXON ten-second EEGMAT probes', 'owner decision D14')
    return owner


def private_names(docs):
    """The user, project, host and volume names the private records use, read from them, never spelled in this file."""
    c, a = docs['captioner'], docs['axon']
    text = json.dumps(a['protocol']) + json.dumps(a['intakeAdmission']) + c['handoff'] + c['intakeHandoff'] + a['handoff']
    names = {n for pair in re.findall(r'/home/([^/\s"`]+)/([^/\s"`]+)/', text) for n in pair}
    names |= {n for pair in re.findall(r'/mnt/([^/\s"`]+)/([^/\s"`]+)/', text) for n in pair}
    for doc in (c['handoff'], c['intakeHandoff'], a['handoff']):
        m = re.search(r'(?:private|acquired) on (\w+)', doc)
        require(m is not None, 'a handoff no longer names the host that keeps its files')
        names.add(m.group(1))
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- the approvals
def captioner_bindings(docs):
    """EEG-Captioner's release approval binds the handoff, the interpretation review and the audit outcome."""
    c, refs = docs['captioner'], docs['refs']['captioner']
    ap, ir, out = c['approval'], c['interpretation'], c['outcome']
    require(ap['status'] == CAPTIONER_STATUS, 'EEG-Captioner’s release approval no longer passes the handoff')
    require(ap['handoff_sha256'] == refs['handoff']['sha256'], 'the approval names another handoff')
    require(ap['independent_outcome_sha256'] == refs['outcome']['sha256'], 'the approval names another audit outcome')
    require(ap['interpretation_review_sha256'] == refs['interpretation']['sha256'],
            'the approval names another interpretation review')
    require(ap['main_comparison_leaderboard_allowed'] is False and ap['raw_preprocessing_recomputed'] is False
            and ap['source_QC_recomputed'] is False and ap['publication_authorized'] is False,
            'the approval’s scope changed')
    require(ir['status'] == 'PASS' and ir['findings'] == [] and ir['draft_sha256'] == ap['reviewed_draft_sha256']
            and ir['audit_outcome_sha256'] == refs['outcome']['sha256']
            and ir['frozen_protocol_sha256'] == refs['protocol']['sha256'], 'the interpretation review did not pass')
    ev = ir['evidence_sha256']
    require(ev['review/result_audit/producer-ledger.json'] == refs['ledger']['sha256']
            and ev['Frozen Evaluation Protocol.json'] == refs['protocol']['sha256']
            and ev['config/binding.frozen.json'] == ap['binding_sha256'], 'the review bound other evidence')
    au = out['audit']
    require(out['status'] == 'PASS' and au['status'] == 'PASS' and out['guard']['status'] == 'PASS'
            and au['binding_sha256'] == ap['binding_sha256'] and au['rows'] == ap['windows']
            and au['scores_recomputed'] is True and au['full_features_recomputed'] is True
            and au['independent_heads_recomputed'] is True and au['adapter_recomputed'] is True
            and au['raw_preprocessing_recomputed'] is False and au['source_QC_recomputed'] is False
            and out['guard']['producer_files_preserved'] is True, 'the independent result audit did not pass')
    require(all(v == 0.0 for v in au['feature_max_abs_error'].values()) and set(au['arms']) == {'encoder', 'baseline'},
            'the audit did not reproduce every feature row exactly')
    # The intake: its own approval binds the intake handoff the frozen protocol names.
    ia = c['intakeApproval']
    require(ia['status'] == INTAKE_STATUS and ia['handoff_sha256'] == refs['intakeHandoff']['sha256']
            and ia['real_EEG_evaluated'] is False and ia['publication_authorized'] is False,
            'the intake approval does not pass the pinned intake handoff')
    require(any(e['sha256'] == refs['intakeHandoff']['sha256'] for e in c['protocol']['evidence']),
            'the frozen protocol names another intake handoff')
    return ap


def axon_bindings(docs):
    """AXON's independent release review binds the aggregate and handoff and pins the corrected audit evidence."""
    a, refs = docs['axon'], docs['refs']['axon']
    rv, ag = a['review'], a['aggregate']
    require(rv['decision'] == AXON_DECISION and rv['result_release_approved'] is True
            and rv['release_status'] == AXON_RELEASE_STATUS and rv['main_leaderboard_eligible'] is False
            and rv['new_execution_authorized'] is False and rv['website_edited'] is False,
            'AXON’s independent release review no longer passes the aggregate release')
    files = rv['release_files_sha256']
    require(files.get(Path(refs['aggregate']['path']).name) == refs['aggregate']['sha256'],
            'the review approves another aggregate')
    require(files.get(Path(refs['handoff']['path']).name) == refs['handoff']['sha256'], 'the review approves another handoff')
    ev = rv['evidence_sha256']
    root = RESEARCH_ROOT + 'axon_real_data_admission_20261027/'
    for key in ('correctedAudit', 'featureComparison', 'protocol'):
        require(ev.get(research_name(refs[key], root)) == refs[key]['sha256'], f'{key}: not the evidence the review pins')
    # The aggregate's own status is checked for consistency only; the release status is the review's.
    require(ag['status'] == rv['release_status'] and ag['main_leaderboard_eligible'] is False
            and ag['evidence_sha256'] == refs['correctedAudit']['sha256'], 'the aggregate is not the reviewed release')
    ca = a['correctedAudit']
    t = ca['terminal']
    require(t['status'] == 'PASS_CORRECTED_AUDIT_EXECUTION_COMPLETED' and t['tolerances_modified'] is False
            and t['original_failed_audit_overwritten'] is False and t['automatic_retries'] == 0,
            'the corrected audit did not pass')
    for k in ('axon', 'baseline', 'mean_difference', 'bootstrap'):
        require(ag['results'][k] == ca['aggregate_scores'][k] == ca['aggregate_independent_scores'][k],
                f'{k}: the released aggregate is not the corrected audit’s producer and independent scores')
    fc = a['featureComparison']['aggregate']
    require(fc['status'] == 'PASS' and fc['features_sha256'] == fc['producer_features_sha256']
            and fc['max_abs_error'] == 0.0 and fc['outside_tolerance_count'] == 0,
            'the corrected features are not the production features')
    return rv


def shared_cache(docs):
    """AXON read EEG-Captioner's sealed physical array and reused its sealed Welch predictions."""
    c, a = docs['captioner'], docs['axon']
    checked = c['outcome']['audit']['checked_files']
    inputs = a['protocol']['inputs']
    require(inputs['physical']['sha256'] == checked['physical.npy'], 'AXON read another physical array')
    require(inputs['baseline_predictions']['sha256'] == checked['predictions.npz'],
            'AXON reused other baseline predictions')
    require(inputs['old_audit']['sha256'] == docs['refs']['captioner']['outcome']['sha256'],
            'AXON’s protocol names another EEG-Captioner audit outcome')
    require(inputs['binding']['sha256'] == c['approval']['binding_sha256'], 'AXON’s protocol names another binding')
    stated(a['protocol']['baseline'], 'Reuse old audited predictions.npz baseline_pred.npy member only AFTER all432 new '
                                      'AXON predictions globally sealed', 'AXON protocol')
    stated(a['handoff'], 'The existing 95D baseline predictions are reused for the same rows/folds, only after AXON '
                         'predictions are sealed.', 'AXON handoff')
    return True


def planning_bindings(docs):
    """The website queue names the same handoffs, aggregate and review by SHA-256."""
    q, rc, ra = docs['planning']['queue'], docs['refs']['captioner'], docs['refs']['axon']
    require(q['publication_authorized'] is False, 'the queue changed its authority')
    rows = q['rows']
    probe = [r for r in rows if r.get('source_sha256') == rc['handoff']['sha256']]
    intake = [r for r in rows if r.get('source_sha256') == rc['intakeHandoff']['sha256']]
    axon = [r for r in rows if r.get('review_sha256') == ra['review']['sha256']]
    require(len(probe) == len(intake) == len(axon) == 1, 'the queue does not name each study once')
    require('0/432' in probe[0]['usable_level'] and 'not caption generation' in probe[0]['usable_level'],
            'the queue row changed the probe’s use')
    x = axon[0]
    require(x['aggregate_row_sha256'] == ra['aggregate']['sha256'] and x['release_handoff_sha256'] == ra['handoff']['sha256']
            and x['source_sha256'] == ra['handoff']['sha256'] and x['main_leaderboard_eligible'] is False
            and x['scientific_release_status'] == AXON_RELEASE_STATUS, 'the queue names another AXON release')


# ---------------------------------------------------------------------------- the values
def captioner_values(docs):
    """The scores, difference and interval of the audit outcome, equal to the reviews' and the handoff's numbers."""
    c = docs['captioner']
    s = c['outcome']['aggregate_scores']
    enc, base = s['encoder']['mean_subject_BA'], s['baseline']['mean_subject_BA']
    diff = s['mean_difference']
    lo, hi = s['descriptive_fixed_cohort_bootstrap95']
    require(all(number(v) for v in (enc, base, diff, lo, hi)) and 0 <= enc <= 1 and 0 <= base <= 1,
            'EEG-Captioner’s scores are not proportions')
    require(-1 <= lo <= diff <= hi <= 1, 'EEG-Captioner’s interval does not hold its estimate')
    require(abs((enc - base) - diff) <= TOL, 'EEG-Captioner’s difference is not the difference of its arms')
    nv = c['interpretation']['numeric_verification']
    require(nv['score_table']['encoder']['mean_participant_BA_percent'] == pct(enc, 4)
            and nv['score_table']['baseline']['mean_participant_BA_percent'] == pct(base, 4),
            'the interpretation review verified other scores')
    require(nv['paired_mean_difference_pp'] / 100 == diff and [v / 100 for v in nv['bootstrap95_pp']] == [lo, hi],
            'the interpretation review verified another difference or interval')
    h = c['handoff']
    stated(h, f'| Canonical EEG-Captioner encoder, mean-token 256-dimensional probe | {pct(enc, 4)}% |', 'handoff table')
    stated(h, f'| Matched 95-dimensional Welch bandpower baseline | {pct(base, 4)}% |', 'handoff table')
    stated(h, f'**{100 * diff:.4f} percentage points**'.replace('-', '−'), 'handoff difference')
    stated(h, f'**[{100 * lo:.4f}, {100 * hi:+.4f}] percentage points**'.replace('-', '−'), 'handoff interval')
    return {'encoder': enc, 'baseline': base, 'difference': diff, 'interval': [lo, hi]}


def axon_values(docs, captioner):
    """The released aggregate's scores, equal to the handoff, and its baseline the EEG-Captioner run's."""
    a = docs['axon']
    r = a['aggregate']['results']
    enc, base, diff = r['axon']['mean_subject_BA'], r['baseline']['mean_subject_BA'], r['mean_difference']
    b = r['bootstrap']
    lo, hi = b['percentile95']
    require(all(number(v) for v in (enc, base, diff, lo, hi)) and 0 <= enc <= 1 and 0 <= base <= 1,
            'AXON’s scores are not proportions')
    require(-1 <= lo <= diff <= hi <= 1, 'AXON’s interval does not hold its estimate')
    require(abs((enc - base) - diff) <= TOL, 'AXON’s difference is not the difference of its arms')
    require(base == captioner['baseline'], 'AXON’s baseline score is not the EEG-Captioner run’s')
    cs = docs['captioner']['outcome']['aggregate_scores']['baseline']
    require(r['baseline']['pooled']['confusion_matrix'] == cs['pooled']['confusion_matrix']
            and r['baseline']['folds'] == cs['folds'], 'AXON’s baseline predictions are not the EEG-Captioner run’s')
    h = a['handoff']
    stated(h, f'| AXON frozen 512-dimensional representation + fixed external ridge classifier | **{pct(enc)}%** |',
           'AXON handoff table')
    stated(h, f'| Previously audited 95-dimensional Welch baseline, reused without refitting | **{pct(base)}%** |',
           'AXON handoff table')
    stated(h, f'The paired difference is **{signed(diff, "-")} percentage points**', 'AXON handoff difference')
    stated(h, f'**{signed(lo)} to {signed(hi)} points**', 'AXON handoff interval')
    return {'encoder': enc, 'baseline': base, 'difference': diff, 'interval': [lo, hi]}


def displayed_figures(docs, cap, ax):
    """The consolidated handoff shows the same figures at two decimals."""
    h = docs['planning']['handoff']
    stated(h, f'participant-mean BA **{pct(cap["encoder"])}%** versus **{pct(cap["baseline"])}%**. Difference '
              f'**{signed(cap["difference"], "-").lstrip("+")} pp**, descriptive 95% interval '
              f'**[{signed(cap["interval"][0], "-")}, {signed(cap["interval"][1], "-")}] pp**', 'consolidated handoff C7')
    stated(h, f'participant-mean BA **{pct(ax["encoder"])}% AXON versus {pct(ax["baseline"])}% Welch**; difference '
              f'**{signed(ax["difference"], "-")} pp**, descriptive 95% interval '
              f'**[{signed(ax["interval"][0], "-")}, {signed(ax["interval"][1], "-")}] pp**', 'consolidated handoff C9')
    stated(h, 'Put the zero eligibility count beside any score and exclude this result from the main comparison '
              'leaderboard.', 'consolidated handoff C7')


# ---------------------------------------------------------------------------- the shared blocks
def cohort_block(docs):
    c, a = docs['captioner'], docs['axon']
    sc, ag, ap = c['protocol']['scope'], a['aggregate'], c['approval']
    folds = ag['outer_subject_folds']
    people, records, windows = sc['subjects'], sc['recordings'], sc['windows']
    require(people == ag['subjects'] == sum(folds) and records == ag['recordings'] == 2 * people
            and windows == ag['windows'] == ap['windows'] == records * sc['windows_per_recording']
            and sc['classes_windows'] == [windows // 2, windows // 2], 'the cohort counts disagree')
    wsec = ag['window_seconds']
    require(wsec * sc['windows_per_recording'] == sc['seconds_per_recording'] == 60
            and wsec == a['protocol']['cohort']['window_seconds'], 'the windows do not tile the retained minute')
    order = c['protocol']['channel_contract']['order']
    measured = [ch for ch in order if ch != 'OZ']
    require(len(order) == 20 and len(measured) == ag['channels'] == 19
            and a['protocol']['cache_channel_order'] == measured, 'another montage')
    require(ag['sample_rate_Hz'] == a['protocol']['cohort']['sfreq'] == 200, 'another sampling rate')
    stated(c['protocol']['splits_heads_metrics']['folds'], 'zero-based rank i -> outer fold i%5', 'fold rule')
    stated(c['protocol']['splits_heads_metrics']['folds'], 'both conditions and all six windows remain together',
           'fold rule')
    require(len(folds) == 5, 'another fold count')
    stated(sc['task'], 'baseline/rest=0 versus mental arithmetic=1', 'labels')
    seq = c['protocol']['preprocessing']['sequence']
    f = re.fullmatch(r'MNE Raw\.filter\(l_freq=([\d.]+),h_freq=([\d.]+)\)', seq[0])
    n = re.fullmatch(r'MNE Raw\.notch_filter\(freqs=([\d.]+)\)', seq[1])
    r = re.fullmatch(r'MNE Raw\.resample\(sfreq=([\d.]+)\) if needed', seq[2])
    require(f and n and r and float(r.group(1)) == ag['sample_rate_Hz'], 'another preprocessing sequence')
    stated(c['protocol']['preprocessing']['boundary'], 'read and preprocess the complete original recording '
                                                       'independently, then retain samples 0:12000 at 200Hz', 'boundary')
    stated(a['protocol']['active_preprocessing'][0], 'whole-record0.1-75Hz/50Hz/notch/resample200Hz then first60seconds',
           'AXON cache')
    track = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    require(track['dataset'] == ag['dataset'] == 'EEGMAT', 'another dataset')
    low, high, notch = float(f.group(1)), float(f.group(2)), float(n.group(1))
    return {
        'dataset': 'EEGMAT', 'name': 'EEG During Mental Arithmetic Tasks', 'version': '1.0.0',
        'source': track['source'],
        'people': people, 'recordings': records, 'conditions': len(a['protocol']['cohort']['conditions']),
        'retained_seconds': sc['seconds_per_recording'], 'window_seconds': wsec,
        'windows_per_recording': sc['windows_per_recording'], 'windows': windows,
        'channels': ag['channels'], 'channel_names': measured, 'sampling_hz': ag['sample_rate_Hz'],
        'folds': len(folds),
        'split': ('subject-disjoint: participants are sorted and dealt into the five folds in turn, so both '
                  'recordings and all windows of a person stay in one fold'),
        'labels': 'the recording condition: pre-task rest against mental arithmetic',
        'classes': ['rest', 'mental arithmetic'],
        'same_windows_both_encoders': True,
        'preprocessing': {
            'whole_recording': True, 'band_pass_hz': [low, int(high) if high.is_integer() else high],
            'notch_hz': int(notch) if notch.is_integer() else notch, 'sampling_hz': ag['sample_rate_Hz'],
            'units': 'microvolts',
            'text': (f'Each complete recording was filtered at {low:g}–{high:g} Hz with a {notch:g} Hz notch and '
                     f'resampled to {ag["sample_rate_Hz"]} Hz, then its first {sc["seconds_per_recording"]} s were cut '
                     f'into {WORDS[sc["windows_per_recording"]]} ten-second windows.'),
        },
        'text': (f'{people} people, {records} recordings, {windows} ten-second windows '
                 f'({WORDS[sc["windows_per_recording"]]} from the first {sc["seconds_per_recording"]} s of each '
                 f'recording), {ag["channels"]} channels at {ag["sample_rate_Hz"]} Hz, {WORDS[len(folds)]} '
                 f'subject-disjoint folds.'),
    }


def qc_block(docs, cohort):
    """The source annotation-QC totals and the rule as the frozen protocol and the handoff state it."""
    c, a = docs['captioner'], docs['axon']
    q = c['outcome']['QC_summary_aggregate']
    cond = q['condition'].values()
    recordings = sum(x['recordings'] for x in cond)
    flagged = sum(x['bad_trials'] for x in cond)
    windows_flagged = sum(x['flagged_windows'] for x in cond)
    eligible = sum(x['source_eligible_windows'] for x in cond)
    require(q['all_zero_eligibility'] is True and recordings == cohort['recordings']
            and windows_flagged == cohort['windows'], 'the QC summary covers another cohort')
    require(eligible == c['approval']['source_QC_eligible_windows'] == a['aggregate']['quality_scope'][
        'Captioner_specific_source_annotation_QC_eligible'] == a['protocol']['claim_limits']['source_QC_eligible_windows'],
        'the records give other eligible counts')
    require(flagged == a['protocol']['claim_limits']['source_QC_recordings_ineligible'] == cohort['recordings']
            and a['aggregate']['quality_scope']['source_annotation_QC_total'] == cohort['windows'],
            'the records give other flagged counts')
    cfg = c['protocol']['source_annotation_QC']['config']
    require(cfg['enabled'] is True and cfg['action'] == 'mark' and cfg['segment_reject']['enabled'] is True,
            'the QC helper did not run in mark mode')
    rule = {
        'flagged_channel_ratio_above': cfg['max_bad_channel_ratio_for_trial'],
        'bad_duration_ratio_above': cfg['max_bad_time_ratio_for_trial'],
        'channel_peak_uv': int(cfg['peak_threshold_uv']), 'channel_flat_uv': int(cfg['flat_threshold_uv']),
        'channel_bad_percent': int(cfg['bad_percent_threshold']), 'minimum_bad_duration_s': cfg['min_bad_duration_sec'],
        'segment_hard_peak_uv': int(cfg['segment_reject']['hard_peak_threshold_uv']),
    }
    h = c['handoff']
    stated(h, f'Source trial rejection uses flagged-channel ratio >{rule["flagged_channel_ratio_above"]} or summed '
              f'BAD-annotation duration ratio >{rule["bad_duration_ratio_above"]}.', 'handoff QC rule')
    stated(h, f'Its {rule["channel_peak_uv"]} µV peak and {rule["channel_flat_uv"]} µV flat parameters are MNE '
              f'adjacent-sample amplitude criteria, with {rule["channel_bad_percent"]}% channel threshold and '
              f'{rule["minimum_bad_duration_s"]}-second minimum duration', 'handoff QC rule')
    stated(h, f'The source\'s {rule["segment_hard_peak_uv"]} µV hard-peak segment rule is relevant only after the '
              f'parent trial is eligible.', 'handoff QC rule')
    stated(h, 'These masks and flags did not modify either arm\'s input or determine inclusion', 'handoff QC use')
    stated(h, 'Every recording was flagged at the parent-trial level; do not imply that all 432 windows individually '
              'exceeded 100 µV.', 'handoff QC scope')
    stated(h, 'It does not establish that EEGMAT is intrinsically unusable', 'handoff QC scope')
    sq = c['protocol']['source_annotation_QC']
    stated(sq['exact_semantics'], f'Trial bad iff mask.mean()>{rule["flagged_channel_ratio_above"]} or '
                                  f'bad_time_ratio>{rule["bad_duration_ratio_above"]}', 'QC semantics')
    stated(sq['exact_semantics'], 'bad_time_ratio sums durations of BAD_ annotations / whole-record duration, exactly as '
                                  'source, with no union correction.', 'QC semantics')
    # Where it ran: on each whole preprocessed recording, before the zero Oz channel; the windows read its flags after.
    stated(h, 'The unchanged, pinned source QC helper was run in `mark` mode before synthetic Oz was added.',
           'handoff QC timing')
    stated(sq['diagnostic_domain'], 'For each complete 19-channel whole-record preprocessed physical-uV recording BEFORE '
                                    'synthetic OZ', 'QC domain')
    stated(sq['diagnostic_domain'], 'use its resulting mask and bad_trial to evaluate exactly the six selected windows',
           'QC domain')
    beside = (f'{eligible} of {cohort["windows"]} windows meet EEG-Captioner’s source annotation-QC rules, and '
              f'{flagged} of {cohort["recordings"]} recordings are flagged by them.')
    return {
        'source': ('EEG-Captioner’s published annotation-QC rules, run unchanged at the pinned source revision on each '
                   'whole preprocessed recording, before the zero Oz channel was inserted'),
        'windows': cohort['windows'], 'windows_meeting_rules': eligible,
        'recordings': cohort['recordings'], 'recordings_flagged': flagged,
        'level': 'recording',
        'rule': rule,
        'rule_text': (f'A recording is flagged when more than {rule["flagged_channel_ratio_above"]} of its channels are '
                      f'flagged or the summed duration of BAD annotations exceeds {rule["bad_duration_ratio_above"]} of '
                      f'the recording. A '
                      f'channel is flagged by MNE’s adjacent-sample amplitude criteria ({rule["channel_peak_uv"]} µV '
                      f'peak, {rule["channel_flat_uv"]} µV flat, {rule["channel_bad_percent"]}% of the record, segments '
                      f'of at least {rule["minimum_bad_duration_s"]} s); the {rule["segment_hard_peak_uv"]} µV segment '
                      f'rule applies only inside a recording that passes.'),
        'selects_windows': False, 'changes_inputs': False, 'recomputed_by_audit': False,
        'beside_every_score': beside,
        'scope': ('The flag is set per recording at the parent-trial level. It does not say that each window has an '
                  'artifact, and it is not evidence that EEGMAT as a whole is unusable.'),
    }


def interval_block(docs, cap, ax):
    c, a = docs['captioner'], docs['axon']
    pa = c['protocol']['prospective_addendum']
    bc, ba, bp = pa['bootstrap'], a['aggregate']['results']['bootstrap'], a['protocol']['uncertainty']
    require(bc == {'enabled': True, 'replicates': ba['replicates'], 'seed': ba['seed'], 'unit': 'subject',
                   'interval': 'percentile95', 'purpose': 'descriptive_fixed_cohort'}
            and pa['admitted_before_outcomes'] is True, 'EEG-Captioner’s bootstrap is not the prospective one')
    require(ba == {'replicates': bp['replicates'], 'seed': bp['seed'], 'unit': 'subject',
                   'purpose': 'descriptive_fixed_cohort', 'percentile95': ax['interval']}, 'AXON’s bootstrap differs')
    stated(pa['procedure'], 'numpy.percentile at [2.5,97.5]', 'bootstrap procedure')
    stated(bp['interval'], 'percentile2.5/97.5 of paired mean participant BA differences', 'AXON bootstrap')
    stated(c['handoff'], f'The prospective uncertainty addendum uses {ba["replicates"]:,} paired resamples of the 36 '
                         f'participant-level differences', 'handoff bootstrap')
    stated(c['handoff'], 'The interval is descriptive for this fixed cohort and prediction set.', 'interval')
    stated(a['handoff'], 'training sets overlap across cross-validation folds', 'interval')
    spans = [cap['interval'][0] <= 0 <= cap['interval'][1], ax['interval'][0] <= 0 <= ax['interval'][1]]
    require(all(spans), 'an interval no longer spans zero; the panel’s reading must be reviewed')
    return {
        'kind': 'paired participant bootstrap', 'method': 'percentile interval', 'level': 0.95, 'unit': 'participant',
        'draws': ba['replicates'], 'seed': ba['seed'], 'same_rule_both_encoders': True, 'prespecified': True,
        'both_span_zero': True,
        'text': (f'{ba["replicates"]:,} paired participant draws of the {a["aggregate"]["subjects"]} '
                 'participant differences in each subsection, with a 2.5–97.5 percentile interval. Both intervals span '
                 'zero.'),
        'scope': ('Each interval resamples the participant differences of this fixed cohort and its fixed predictions; '
                  'training sets overlap across folds, so it describes this cohort, not a population.'),
    }


def probe_block(docs, cohort):
    c, a = docs['captioner'], docs['axon']
    head = c['protocol']['splits_heads_metrics']['head']
    m = re.search(r'RidgeClassifier\(alpha=(\d+),class_weight=(\w+),fit_intercept=(True),solver=(\w+),tol=1e-4\)', head)
    require(m is not None and m.group(0) in a['protocol']['heads']['head'] and int(m.group(1)) == a['aggregate'][
        'head_alpha'], 'the two probes do not share one head')
    stated(head, 'fit StandardScaler(with_mean=True,with_std=True) on other four folds only', 'scaler')
    stated(head, 'No tuning, validation reuse, feature selection, PCA, clipping or transductive normalization', 'head')
    require(a['protocol']['heads']['fits'] == cohort['folds'], 'another fit count')
    stated(c['handoff'], 'There is no hyperparameter search or encoder fine-tuning.', 'handoff')
    stated(a['handoff'], 'There is no hyperparameter search, encoder fine-tuning or transductive scaling.', 'AXON handoff')
    stated(c['handoff'], 'feature extraction, source-only heads with global prediction sealing, and a distinct scoring '
                         'process', 'sealing')
    stated(a['handoff'], 'global prediction sealing and separate scoring', 'AXON sealing')
    return {'scaler': 'StandardScaler fitted on the training folds only', 'head': 'RidgeClassifier',
            'alpha': int(m.group(1)), 'solver': m.group(4), 'class_weight': m.group(2), 'fit_intercept': True,
            'fits_per_representation': cohort['folds'], 'hyperparameter_search': False, 'encoder_fine_tuning': False,
            'sealed_before_scoring': True, 'shared_by_both_encoders': True}


def welch_block(docs, cohort):
    """The Welch comparator, as the frozen protocol defines it."""
    b = docs['captioner']['protocol']['features']['baseline']
    m = re.match(r'(\d+)D =(\d+) measured channels x(\d+) bands', b)
    bands = [[float(x) if '.' in x else int(x), float(y) if '.' in y else int(y)]
             for x, y in re.findall(r'\[([\d.]+),([\d.]+)[)\]]', b.split('Hz in', 1)[1].split('then', 1)[0])]
    require(m and int(m.group(1)) == int(m.group(2)) * int(m.group(3)) and int(m.group(2)) == cohort['channels']
            and len(bands) == int(m.group(3)), 'the Welch dimension is not channels by bands')
    w = re.search(r'SciPy signal\.welch fs(\d+),window=hann,nperseg(\d+),noverlap(\d+),', b)
    require(w is not None and int(w.group(1)) == cohort['sampling_hz'], 'another Welch estimate')
    stated(b, 'then log10(max(power,1e-12))', 'Welch')
    stated(b, 'on the SAME preprocessed physical-uV windows', 'Welch')
    require(bands[0][0] == 0.5 and bands[-1][1] == 45, 'the Welch bands changed')
    edges = ', '.join(f'{lo:g}–{hi:g}' for lo, hi in bands[:-1]) + f' and {bands[-1][0]:g}–{bands[-1][1]:g}'
    return {
        'id': 'welch-band-power', 'dimension': int(m.group(1)), 'channels': cohort['channels'], 'bands': len(bands),
        'band_edges_hz': bands, 'segment_samples': int(w.group(2)), 'overlap_samples': int(w.group(3)),
        'definition': (f'{m.group(1)} absolute log band powers: {cohort["channels"]} channels by {len(bands)} bands '
                       f'({edges} Hz), Welch at {cohort["sampling_hz"]} Hz with {w.group(2)}-sample Hann segments and '
                       f'{w.group(3)}-sample overlap, on the same windows'),
    }


# ---------------------------------------------------------------------------- the two subsections
def contrast(a_id, b_id, label, values):
    lo, hi = values['interval']
    spans = lo <= 0 <= hi
    require(spans, f'{a_id}: the interval no longer spans zero; the reading must be reviewed')
    return {'a': a_id, 'b': b_id, 'label': label, 'difference': values['difference'], 'interval_95': [lo, hi],
            'interval_includes_zero': spans, 'reading': SPANS_ZERO}


def captioner_block(docs, values, cohort, qc, welch):
    c = docs['captioner']
    p, h, ih = c['protocol'], c['handoff'], c['intakeHandoff']
    enc = p['features']['encoder']
    stated(enc, 'mean all 200 output tokens on token axis ->256D', 'encoder pooling')
    stated(enc, 'no gradients or updates', 'frozen encoder')
    stated(h, 'The encoder\'s 200 tokens are mean-pooled to a 256-dimensional representation.', 'handoff pooling')
    seq = p['preprocessing']['sequence'][-1]
    stated(seq, 'insert zero OZ in model order; cast float32; reshape20x10x200; divide100 exactly once', 'encoder input')
    stated(h, 'Only the encoder inserts the permitted zero Oz channel, reshapes to `[batch,20,10,200]` and divides by 100.',
           'handoff input')
    stated(h, 'Qwen, the projector and language LoRA were not used. No caption correctness or language-conditioning '
              'result is produced here.', 'handoff scope')
    # Identity from the intake handoff, equal to the probe's protocol and handoff.
    ident = p['identity']
    m = re.search(r'Hugging Face repository: `([\w-]+/[\w-]+)`; revision `([0-9a-f]{40})`', ih)
    s = re.search(r'Canonical source: `([\w-]+/[\w-]+)`; commit `([0-9a-f]{40})`', ih)
    b = re.search(r'matched the pinned ([\d,]+)-byte artifact and SHA-256 `([0-9a-f]{64})`', ih)
    require(m and s and b, 'the intake handoff no longer states the identity')
    stated(h, f'- Source repository: `{s.group(1)}`, commit `{s.group(2)}` (MIT code).', 'handoff identity')
    stated(h, f'- Weight repository: `{m.group(1)}`, revision `{m.group(2)}` (Apache-2.0 portable weight metadata).',
           'handoff identity')
    stated(h, f'- Encoder artifact: {b.group(1)} bytes; SHA-256 `{b.group(2)}`.', 'handoff identity')
    require(ident['source_revision'] == s.group(2) and ident['encoder_sha256'] == b.group(2), 'another encoder')
    stated(ih, 'Source code: MIT. Portable weight metadata: Apache-2.0. Preserve both source and weight notices.',
           'intake licences')
    stated(json.dumps(p['limitations']), 'Unknown pretraining exposure', 'exposure')
    return {
        'id': 'eeg-captioner', 'name': 'EEG-Captioner encoder', 'title': CAPTIONER_LABEL,
        'representation': {'dimension': 256, 'tokens': 200,
                           'definition': ('the mean of the 200 output tokens of EEG-Captioner’s frozen encoder, '
                                          '256 dimensions')},
        'input': {'measured_channels': cohort['channels'], 'zero_oz_channel': True, 'model_channels': 20,
                  'amplitude_divisor': 100,
                  'text': ('the 19 measured channels in microvolts with a zero Oz channel inserted, as the encoder’s '
                           'loader permits, divided by 100')},
        'encoder_only': True, 'caption_result': False, 'language_model_loaded': False,
        'scope': ('Only EEG-Captioner’s encoder was run; its language model, projector and language adapter were not '
                  'loaded, and there is no caption result.'),
        'pretraining_exposure': 'unknown',
        'arms': [
            {'id': 'eeg-captioner', 'role': 'encoder', 'label': CAPTIONER_LABEL, 'dimension': 256,
             'balanced_accuracy': values['encoder']},
            {'id': welch['id'], 'role': 'baseline', 'label': WELCH_LABEL, 'note': WELCH_MATCHED,
             'dimension': welch['dimension'], 'balanced_accuracy': values['baseline']},
        ],
        'baseline': {'matched': True, 'fitted_in_this_run': True, 'definition': welch['definition']},
        'paired_difference': contrast('eeg-captioner', welch['id'], 'EEG-Captioner encoder minus Welch band power',
                                      values),
        'identity': {
            'hf_repository': f'https://huggingface.co/{m.group(1)}', 'hf_revision': m.group(2),
            'source_repository': f'https://github.com/{s.group(1)}', 'source_revision': s.group(2),
            'encoder_bytes': int(b.group(1).replace(',', '')), 'encoder_sha256': b.group(2),
            'frozen': True, 'fine_tuning': False, 'weights_distributed': False,
        },
        'rights': {
            'code': {'licence': 'MIT', 'scope': 'EEG-Captioner’s source code at the pinned commit'},
            'weights': {'licence': 'Apache-2.0', 'licence_url': 'https://www.apache.org/licenses/LICENSE-2.0',
                        'as_stated_by': 'the portable weight metadata of the Hugging Face repository at the pinned revision',
                        'distributed': False},
        },
    }


def captioner_audit(docs, cohort):
    c = docs['captioner']
    au, h = c['outcome']['audit'], c['handoff']
    stated(h, 'All 432 encoder and baseline feature rows reproduced exactly, with maximum feature error zero.', 'audit')
    stated(h, 'All metrics and the paired bootstrap matched.', 'audit')
    stated(h, 'Audit coverage begins at the sealed physical/prepared arrays. Raw EDF preprocessing and source-QC '
              'computation were source-reviewed and hash-bound, not independently recomputed.', 'audit boundary')
    stated(c['outcome']['authorship'], 'imports no producer scientific helpers', 'audit authorship')
    stated(c['outcome']['authorship'], 'Entire reconstruction code authorship is not claimed independent', 'authorship')
    require(au['rows'] == cohort['windows'], 'the audit covered other rows')
    # Exact for the feature rows and the hard predictions; the refitted heads' decision scores agree to a bound, which
    # is published as its power of ten, never as the measured errors.
    stated(h, f'Ten head refits reproduced all {2 * au["rows"]} hard predictions exactly; maximum decision-score errors '
              'were approximately', 'audit heads')
    head = au['head_max_abs_error']
    require(set(head) == set(au['arms']) and all(number(v) and 0 < v < 1e-3 for v in head.values()),
            'the refitted heads’ decision-score errors are not a small positive pair')
    bound = 10 ** math.ceil(math.log10(max(head.values())))
    require(all(v < bound for v in head.values()), 'the decision-score bound does not hold')
    return {
        'status': 'passed', 'starts_at': 'the sealed preprocessed arrays',
        'rows_reproduced': au['rows'], 'feature_max_abs_error': max(au['feature_max_abs_error'].values()),
        'heads_refitted': True, 'hard_predictions_reproduced_exactly': True, 'head_decision_score_error_below': bound,
        'scores_and_bootstrap_matched': True,
        'raw_preprocessing_recomputed': False, 'source_qc_recomputed': False, 'producer_helpers_imported': False,
        'text': ('A separately operated reconstruction, importing none of the producer’s scientific helpers, reproduced '
                 f'all {au["rows"]} encoder and baseline feature rows exactly from the sealed preprocessed arrays. It '
                 'refitted every head, reproduced every hard prediction exactly with decision scores within '
                 f'{tol(bound)} of the producer’s, and matched every score and the bootstrap. The raw preprocessing and '
                 'the source QC were checked against their pinned source and hashes, not recomputed.'),
    }


AXON_LIMITATIONS = (
    ('pretraining-not-isolated', 'The Welch comparison cannot isolate what AXON’s pretraining contributes.'),
    ('outcomes-known', 'AXON’s interval is descriptive for a second reason too: the EEG-Captioner and Welch outcomes were '
                       'known before AXON ran.'),
)


def axon_block(docs, values, cohort, qc, welch):
    a = docs['axon']
    ag, p, h = a['aggregate'], a['protocol'], a['handoff']
    require(ag['features'] == p['features']['shape'][1] == 512 and p['features']['shape'][0] == cohort['windows'],
            'another AXON representation')
    stated(p['features']['pool'], 'source features=tokens.mean(dim=(1,2))', 'AXON pooling')
    stated(h, 'The source mean-pools channel/patch tokens into 512 features.', 'AXON handoff pooling')
    stated(h, 'The encoder is frozen; its original untrained classification head is preserved and unused for task '
              'accuracy.', 'AXON head')
    stated(p['active_preprocessing'][2], 'No syntheticOz,20channel reshape,/100,additional scaling/filtering/rereference',
           'AXON input')
    stated(p['active_preprocessing'][1], 'unchanged AXON internal per-window torch sample-standard-deviation zscore',
           'AXON standardisation')
    require(p['permutation'] != sorted(p['permutation']) and sorted(p['permutation']) == list(range(cohort['channels'])),
            'the channels are not reordered')
    g = p['geometry_gate']
    require(g['measured_subject_geometry_verified'] is False and g['status'].startswith('PASS_NOMINAL_TEMPLATE'),
            'the geometry gate changed')
    qs = ag['quality_scope']
    require(qs['template_geometry_not_subject_digitization'] is True and qs['pretraining_exposure'] == 'unknown'
            and qs['condition_order_confounded'] is True and qs['pretraining_preprocessing_equivalence'] is False,
            'AXON’s quality scope changed')
    gate = p['numeric_gate']
    passed = qs['AXON_numeric_nondegeneracy_passed']
    require(passed == cohort['windows'] and gate['shape'] == [cohort['windows'], cohort['channels'], 2000]
            and gate['std_ddof'] == 1 and gate['minimum_exclusive_uV'] == 1e-12, 'AXON’s numerical gate changed')
    stated(gate['failure'], 'This is numerical nondegeneracy, not physiological cleanliness.', 'AXON gate')
    stated(h, f'All {passed} pass the separate AXON numerical finite/nondegenerate-input check.', 'AXON handoff gate')
    stated(h, 'This is not a normalization-matched or parameter-count-matched comparison and cannot isolate the '
              'contribution of pretraining.', 'AXON baseline')
    # AXON's own limits, in its subsection: what the Welch comparison cannot isolate, and why its interval is descriptive
    # beyond the fold overlap both intervals share.
    stated(h, 'training sets overlap across cross-validation folds and earlier comparator outcomes were known.',
           'AXON interval')
    stated(p['uncertainty']['interpretation'], 'overlapping training folds/known outcomes preclude confirmatory '
                                               'independent-generalization CI', 'AXON interval')
    stated(p['claim_limits']['known_prior'], 'known prospectively. No AXON outcome existed at freeze.', 'AXON protocol')
    # Identity: the final intake admission, the card and access record it binds, and the strict-load packet.
    ia, pk = a['intakeAdmission'], a['loadPacket']
    ck = ia['checkpoint']
    require(ia['status'] == 'PASS' and ia['checkpoint_ready_for_separately_reviewed_D2'] is True
            and ck['repo'] == ag['checkpoint_repository'] and ck['revision'] == ag['checkpoint_revision']
            and ck['sha256'] == ag['checkpoint_sha256'] == p['model']['checkpoint']['sha256'],
            'the intake admitted another checkpoint')
    bound = ia['bound_evidence_sha256']
    root = 'axon_load_admission_20261027/'
    for key in ('card', 'access'):
        ref = docs['refs']['axon'][key]
        require(bound.get(research_name(ref, root)) == ref['sha256'], f'{key}: not the record the intake bound')
    stated(a['loadHandoff'], f'accepted {ck["bytes"]:,} bytes with SHA256 `{ck["sha256"]}`', 'AXON load handoff')
    stated(a['loadHandoff'], f'pinned source commit `{ag["source_commit"]}`', 'AXON load handoff')
    require(ag['source_commit'] == p['model']['source_commit'], 'another source commit')
    stated(pk, f'Pinned implementation is `braindecode/braindecode@{ag["source_commit"]}`, `braindecode/models/axon.py`',
           'strict-load packet')
    stated(pk, 'AXON has per-file Apache-2.0 terms while the project root license is BSD-3-Clause; preserve both.',
           'strict-load packet')
    stated(pk, f'**{ck["bytes"]:,} bytes**, LFS SHA256 `{ck["sha256"]}`', 'strict-load packet')
    acc = a['access']
    require(acc['id'] == ck['repo'] and acc['sha'] == ck['revision'] and acc['private'] is False
            and acc['gated'] is False and acc['cardData']['license'] == 'apache-2.0', 'the access record changed')
    require(re.search(r'^license: apache-2\.0$', a['card'], re.M) is not None, 'the model card states another licence')
    stated(a['card'], '- **Code:** [`braindecode.models.AXON`]', 'model card')
    return {
        'id': 'axon', 'name': 'AXON', 'title': AXON_LABEL,
        'representation': {'dimension': ag['features'],
                           'definition': 'the mean over AXON’s channel and patch tokens, 512 dimensions'},
        'input': {'measured_channels': cohort['channels'], 'reordered_to_model_order': True, 'zero_oz_channel': False,
                  'divided_by_100': False, 'own_standardisation': True, 'template_positions': True,
                  'digitised_positions': False,
                  'text': ('the same 19 measured channels in microvolts, reordered to AXON’s channel order and '
                           'standardised per channel and window inside AXON')},
        'native_head_used': False,
        'pretraining_exposure': 'unknown',
        'arms': [
            {'id': 'axon', 'role': 'encoder', 'label': AXON_LABEL, 'dimension': ag['features'],
             'balanced_accuracy': values['encoder']},
            {'id': welch['id'], 'role': 'baseline', 'label': WELCH_LABEL, 'note': WELCH_REUSED,
             'dimension': welch['dimension'], 'balanced_accuracy': values['baseline']},
        ],
        'baseline': {'matched': False, 'fitted_in_this_run': False, 'same_baseline_as': 'eeg-captioner',
                     'matched_normalisation': False, 'matched_parameter_count': False, 'isolates_pretraining': False},
        'paired_difference': contrast('axon', welch['id'], 'AXON minus Welch band power', values),
        'limitations': [{'id': lid, 'text': text} for lid, text in AXON_LIMITATIONS],
        'numerical_input_check': {
            'windows_passed': passed, 'windows': cohort['windows'], 'minimum_channel_std_uv': gate['minimum_exclusive_uV'],
            'separate_from_source_qc': True,
            'rule': ('every sample finite, and every channel’s sample standard deviation in every window above '
                     '1e-12 µV: numerical non-degeneracy, a separate matter from signal quality'),
            'beside_score': f'AXON’s own numerical input check passed {passed} of {cohort["windows"]}, a different check',
        },
        'identity': {
            'hf_repository': f'https://huggingface.co/{ck["repo"]}', 'hf_revision': ck['revision'],
            'checkpoint_file': 'model.safetensors', 'checkpoint_bytes': ck['bytes'], 'checkpoint_sha256': ck['sha256'],
            'source_repository': 'https://github.com/braindecode/braindecode', 'source_revision': ag['source_commit'],
            'module': 'braindecode.models.AXON',
            'frozen': True, 'fine_tuning': False, 'weights_distributed': False,
        },
        'rights': {
            'checkpoint': {'licence': 'Apache-2.0', 'licence_url': 'https://www.apache.org/licenses/LICENSE-2.0',
                           'as_stated_by': 'the licence tag of the Hugging Face repository at the pinned revision',
                           'gated': acc['gated'], 'distributed': False},
            'module': {'licence': 'Apache-2.0', 'scope': 'the per-file terms of the AXON module in Braindecode'},
            'project': {'licence': 'BSD-3-Clause', 'scope': 'the licence at the Braindecode project root'},
        },
    }


def axon_audit(docs, cohort):
    a = docs['axon']
    pa, fc, h = a['protocol']['audit'], a['featureComparison']['aggregate'], a['handoff']
    ag = a['aggregate']['audit']
    require(ag['original_feature_reconstruction'] == 'FAIL retained' and ag['producer_rerun'] is False
            and ag['producer_predictions_unchanged'] is True
            and ag['corrected_reconstruction'].startswith('PASS features byte-identical'), 'AXON’s audit record changed')
    require(fc['rtol'] == pa['features_rtol'] and fc['atol'] == pa['features_atol']
            and fc['counts']['forwards'] == cohort['windows'], 'the corrected audit used another tolerance or rows')
    stated(h, 'The first independent audit failed the frozen feature tolerance.', 'AXON audit')
    stated(h, '**The corrected feature file is byte-identical to the original production feature file**', 'AXON audit')
    stated(h, f'The original feature tolerance (rtol {tol(pa["features_rtol"])}, atol {tol(pa["features_atol"])}) was never '
              'relaxed, and no production prediction, split, model weight or hyperparameter changed.', 'AXON audit')
    stated(h, 'It reconstructed all 432 features and refitted five heads', 'AXON audit')
    stated(h, 'The original import failure and failed audit remain preserved.', 'AXON audit')
    stated(a['review']['provenance_and_failure_review'][2], 'The independently approved correction aligned auditor '
                                                            'parameter gradient flags with the frozen producer.', 'review')
    return {
        'starts_at': 'the sealed physical array the EEG-Captioner run prepared',
        'raw_preprocessing_recomputed': False,
        'first_audit': {'status': 'failed', 'kept': True, 'failed_check': 'feature tolerance',
                        'rtol': pa['features_rtol'], 'atol': pa['features_atol']},
        'corrected_audit': {'status': 'passed', 'rows_reproduced': cohort['windows'], 'byte_identical': True,
                            'feature_max_abs_error': fc['max_abs_error'], 'heads_refitted': True,
                            'tolerance_relaxed': False},
        'production_unchanged': True, 'producer_rerun': False,
        'text': ('AXON’s first independent audit failed its feature tolerance and is kept. The corrected audit changed '
                 'only the auditor’s frozen-parameter state to match production; it reproduced all 432 production rows '
                 'byte for byte under the unchanged tolerance, refitted the heads and matched every score. Production '
                 'was unchanged.'),
    }


# ---------------------------------------------------------------------------- separation and caveats
def encoder_contrast_block(docs):
    a = docs['axon']
    known = a['protocol']['claim_limits']['known_prior']
    stated(known, 'known prospectively. No AXON outcome existed at freeze.', 'AXON protocol')
    stated(a['handoff'], 'earlier comparator outcomes were known', 'AXON handoff')
    stated(a['review']['interpretation_review'][2], 'Known earlier comparator outcomes', 'AXON review')
    return {
        'published': False, 'same_inputs': False, 'axon_ran_after_outcomes_known': True,
        'text': ('No EEG-Captioner against AXON difference is computed: AXON ran after the EEG-Captioner and Welch '
                 'outcomes were known, and the two encoders read different inputs (a zero Oz channel and division by '
                 '100 for EEG-Captioner; reordered channels with its own standardisation for AXON).'),
    }


def separation_block(docs, cohort):
    pub = docs['published']
    nl = pub['neurolmEegmat']
    core = nl['separate_from_core']
    require(core['core_band_pass'] is False and nl['cohort']['window_seconds'] == 2 and core['shared_windows'] is True,
            'the published NeuroLM record no longer states the core windows')
    ep = next(p for p in pub['eegptCore']['protocols'] if p['id'] == 'arithmetic-rest')
    require(ep['window_seconds'] == nl['cohort']['window_seconds'], 'the EEGPT core row uses other windows')
    ad = pub['adaptation']['results']['eegmat-labram-adaptation']
    require(ad['cohort']['two_second_windows'] == nl['cohort']['windows'], 'the adaptation pilot uses other windows')
    rows = list(csv.DictReader(io.StringIO(pub['foundationArithmetic'])))
    require(any(r['model'].startswith('REVE') for r in rows), 'the REVE frozen rows are not on the site')
    stated(docs['captioner']['handoff'], 'The earlier two-second NeuroRVQ EEGMAT evaluation has a different '
                                         'window/preprocessing/representation contract', 'handoff')
    sp = core['core_spectral_ridge']
    return {
        'ranked_against_two_second_results': False,
        'window_seconds': cohort['window_seconds'], 'two_second_window_seconds': nl['cohort']['window_seconds'],
        'core_band_pass': core['core_band_pass'], 'core_sampling_hz': core['core_sampling_hz'],
        'not_ranked_against': [
            {'id': 'core-matrix', 'label': 'the core Arithmetic & rest matrix', 'page': core['page']},
            {'id': 'frozen-rows', 'label': 'the REVE and EEGPT frozen rows'},
            {'id': 'labram-last-block', 'label': 'LaBraM last-block adaptation', 'page': '/topics/model-adaptation/'},
            {'id': 'neurolm-panel', 'label': 'the NeuroLM panel', 'page': nl['placement']['page'],
             'anchor': nl['placement']['anchor']},
            {'id': 'neurorvq-panel', 'label': 'the NeuroRVQ panel', 'page': '/topics/pilot-studies/', 'anchor': 'neurorvq'},
        ],
        'text': ('Not ranked against the two-second results on this site: the core Arithmetic & rest matrix, the REVE '
                 'and EEGPT frozen rows, LaBraM last-block adaptation, the NeuroLM panel and the NeuroRVQ panel. These '
                 f'probes use filtered ten-second windows at {cohort["sampling_hz"]} Hz, where the core protocol uses '
                 f'unfiltered two-second windows at {core["core_sampling_hz"]} Hz, and its Spectral ridge row uses log '
                 f'relative spectra from {sp["band_hz"][0]:g}–{sp["band_hz"][1]:g} Hz rather than these absolute band '
                 'powers.'),
    }


LIMITATIONS = (
    ('recording-order',
     'Rest is recorded before arithmetic, so recording order, time and artifacts move with the label; subject-disjoint '
     'folds do not remove this, and neither probe isolates cognitive workload.'),
    ('exposure',
     'Whether either encoder saw EEGMAT in pretraining is unknown, so exposure is shown as unknown for both.'),
    ('axon-inputs',
     'AXON reads nominal template electrode positions, not positions digitised for each person, and the cache’s '
     '0.1–75 Hz band with a 50 Hz notch differs from the pretraining preprocessing on AXON’s model card (0.5–99.5 Hz, a '
     '50 or 60 Hz notch, standardisation and clipping at 15 standard deviations).'),
    ('upstream-recording',
     'EEGMAT’s linked-ear reference and its upstream filtering are uncertain from the source files, and further '
     'filtering cannot restore frequencies removed before release.'),
    ('scope',
     'Frozen encoders with a supervised linear head, scored on recording condition: the filters ran over whole '
     'recordings, using context outside each window, and nothing here measures clinical use or online decoding.'),
)


def limitations_block(docs, cohort):
    """The caveats, each once, every figure in them read back from the record that states it."""
    c, a = docs['captioner'], docs['axon']
    stated(a['handoff'], 'Rest was recorded before arithmetic. Recording order, time, artifacts and other '
                         'condition-linked changes can explain discrimination; subject-disjoint folds do not remove this '
                         'confound.', 'order')
    stated(a['protocol']['claim_limits']['preprocessing_mismatch'], 'AXON card0.5-99.5Hz/50or60Hz/zscore/15sigma clip '
                                                                     'vs retained cache0.1-75Hz/50Hz', 'AXON mismatch')
    stated(a['handoff'], 'The explicit legacy-channel mapping uses verified nominal template coordinates. No '
                         'participant-specific digitized head geometry is claimed', 'AXON geometry')
    stated(c['handoff'], 'EEGMAT\'s linked-ear source statement and inconsistent upstream prefilter documentation remain '
                         'limitations. Additional filtering cannot recover frequencies already removed upstream',
           'upstream')
    stated(c['handoff'], 'Whole-record filtering is acausal and uses context outside each selected window; no online '
                         'inference claim follows.', 'scope')
    return [{'id': lid, 'text': text} for lid, text in LIMITATIONS]


def rights_block(docs):
    track = next(t for t in docs['published']['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    record = {'name': track['dataset']}
    record.update({k: track[k] for k in RIGHTS_FIELDS})
    require(record['rightsScope'] == 'Personal noncommercial research; aggregate results only'
            and record['license'] == 'Open Data Commons Attribution License 1.0', 'the EEGMAT record changed')
    record['published_here'] = (
        'Reused unchanged from the review of the same recordings for the core matrix. Published here for two frozen '
        'encoders on ten-second windows: participant-mean balanced accuracy of each encoder and of Welch band power, '
        'two paired differences with their participant-bootstrap intervals, cohort counts and the source-QC totals; no '
        'per-person, per-fold or per-window value.')
    return {
        'dataset': record,
        'summary': ('EEGMAT 1.0.0: Open Data Commons Attribution License 1.0 (Zyma et al., 2019; PhysioNet). '
                    'EEG-Captioner source code: MIT. EEG-Captioner encoder weights: Apache-2.0 per the Hugging Face '
                    'weight metadata. AXON checkpoint: Apache-2.0 per its Hugging Face licence tag; the AXON module: '
                    'per-file Apache-2.0 terms within the BSD-3-Clause Braindecode project. No weights distributed.'),
    }


# ---------------------------------------------------------------------------- the boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            here = f'{trail}.{k}'
            fact = k in AUDIT_FACT_KEYS and AUDIT_FACT_PARENT.match(trail) and (number(v) or isinstance(v, bool))
            require(k not in REFUSED_KEYS and (fact or not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS)),
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
        require(not ARXIV.search(text), f'{trail}: AXON’s arXiv tag is not cited until checked')
        require(not DECISION_ID.search(text), f'{trail}: an internal decision id in export text')
        if trail in ('$.schema_version', '$.release_id') or VERBATIM.match(trail):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):   # the release record is dated by design (/releases/, /data-use/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail.startswith(('$.provenance', '$.release_record')) or re.search(r'(?:url|source|repository|_status)$', trail):
            continue
        for sentence in re.split(r'(?<=[.;:])\s+', text):
            if sentence.rstrip().endswith('?'):
                continue          # a question asserts nothing
            if CLAIMS.search(sentence):
                require(NEGATION.search(sentence), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def licences_per_part(payload):
    """MIT is EEG-Captioner's code; Apache-2.0 the weights, checkpoint and module; BSD-3-Clause the project root."""
    cr, ar = payload['eeg_captioner']['rights'], payload['axon']['rights']
    require(cr['code']['licence'] == 'MIT' and cr['weights']['licence'] == 'Apache-2.0'
            and cr['weights']['distributed'] is False and ar['checkpoint']['licence'] == 'Apache-2.0'
            and ar['module']['licence'] == 'Apache-2.0' and ar['project']['licence'] == 'BSD-3-Clause'
            and ar['checkpoint']['distributed'] is False, 'the licences per part changed')
    for trail, text in strings(payload):
        if re.match(r'^\$\.(?:eeg_captioner|axon)\.rights\.', trail) or VERBATIM.match(trail):
            continue
        for sentence in re.split(r'(?<=[.;])\s+', text):
            if re.search(r'\bMIT\b', sentence):
                require(re.search(r'\bcode\b', sentence, re.I)
                        and not re.search(r'checkpoint|weights|module|Apache|BSD', sentence, re.I),
                        f'{trail}: MIT not tied to the code alone: {sentence!r}')
            if 'Apache-2.0' in sentence:
                require(re.search(r'weights?|checkpoint|module|metadata|licence tag', sentence)
                        and not re.search(r'\bMIT\b|\bcode\b', sentence), f'{trail}: Apache-2.0 not tied to a weight '
                                                                         f'or module: {sentence!r}')
            if 'BSD' in sentence:
                require(re.search(r'project', sentence) and not re.search(r'\bMIT\b', sentence),
                        f'{trail}: BSD-3-Clause not tied to the project: {sentence!r}')


def other_eegmat_figures(docs):
    """Every measured figure of another EEGMAT result on the site; none may reach this file."""
    pub = docs['published']
    out = set()
    track = next(t for t in pub['coreMatrix']['tracks'] if t['id'] == 'arithmetic-rest')
    for r in track['rows']:
        out |= {r['y'], r['x'], *r['interval']}
    cell = next(c for c in pub['eegptCore']['cells'] if c['protocol'] == 'arithmetic-rest')
    out |= {cell['balanced_accuracy'], cell['macro_f1'], *cell['interval_95']}
    out |= set(numbers(pub['neurolmEegmat']))
    out |= set(numbers(pub['adaptation']['results']['eegmat-labram-adaptation']))
    for r in csv.DictReader(io.StringIO(pub['foundationArithmetic'])):
        for k in ('primary_percent', 'secondary_value', 'descriptive_interval_low_percent',
                  'descriptive_interval_high_percent'):
            if r[k]:
                out.add(float(r[k]))
    out = {v for v in out if long_float(float(v))}
    return out | {v / 100 for v in out} | {v * 100 for v in out}


def withheld_values(docs, approved):
    """Per-fold, pooled, confusion, QC breakdown and accounting values the sources hold; never published.
    A window-pooled value equal to an approved participant mean is that mean, and a count that equals a design count
    of the cohort is that count."""
    c, a = docs['captioner'], docs['axon']
    out = set()
    for src in (c['outcome']['aggregate_scores'], a['aggregate']['results']):
        for arm in (k for k in src if isinstance(src[k], dict) and 'folds' in src[k]):
            x = src[arm]
            out |= set(x['folds'].values())
            out |= {x['pooled']['macroF1'], x['pooled']['accuracy'], x['pooled']['balanced_accuracy']}
            out |= {v for row in x['pooled']['confusion_matrix'] for v in row}
    q = c['outcome']['QC_summary_aggregate']
    for group in ('condition', 'fold'):
        for x in q[group].values():
            out |= {x['flagged_channels']}
            if group == 'fold':
                out |= {x['recordings'], x['bad_trials'], x['flagged_windows']}
    out.add(sum(x['flagged_channels'] for x in q['condition'].values()))
    out |= set(numbers(c['outcome']['audit']['head_max_abs_error']))
    out |= {v for k, v in c['outcome']['guard'].items() if number(v)}
    out |= set(numbers(c['ledger']))
    for text in (c['handoff'], c['intakeHandoff'], a['handoff'], a['loadHandoff']):
        out |= {float(x.replace(',', '')) for x in re.findall(r'(\d[\d,]*\.\d+) seconds', text)}
    out |= {v for k, v in a['aggregate']['audit'].items() if number(v)}
    out |= set(numbers(a['correctedAudit']['terminal']))
    out |= set(numbers(a['correctedAudit']['receipts']['features-receipt.json']['value']['counts']))
    out.add(a['correctedAudit']['receipts']['features-receipt.json']['value']['min_channel_sample_std_uV'])
    return {v for v in out if v not in TRIVIAL and v not in approved}


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['holds'] == [], 'this release has no hold')
    require(not any(re.search(r'(?:^|/)(?:models|leaderboard)\.json$', r['path']) for r in input_refs(manifest)),
            'the legacy models.json and leaderboard.json are never read')
    owner_decision(manifest)
    docs = load(manifest)
    captioner_bindings(docs)
    axon_bindings(docs)
    shared_cache(docs)
    planning_bindings(docs)
    cap = captioner_values(docs)
    ax = axon_values(docs, cap)
    displayed_figures(docs, cap, ax)
    cohort = cohort_block(docs)
    qc = qc_block(docs, cohort)
    interval = interval_block(docs, cap, ax)
    probe = probe_block(docs, cohort)
    welch = welch_block(docs, cohort)
    captioner = captioner_block(docs, cap, cohort, qc, welch)
    captioner['audit'] = captioner_audit(docs, cohort)
    axon = axon_block(docs, ax, cohort, qc, welch)
    axon['audit'] = axon_audit(docs, cohort)
    pub = docs['published']
    for f in ('pilotStudies', 'neurolmEegmat'):
        require(not re.search(r'captioner|axon', json.dumps(pub[f]), re.I), f'{f}: the released file already names them')
    require(not any(re.search(r'captioner|axon', r['name'], re.I) for t in pub['coreMatrix']['tracks'] for r in t['rows']),
            'an encoder of this panel is already a core row')
    rr, rc, ra = manifest['releaseRecord'], manifest['captioner'], manifest['axon']
    # Neither research record authorises publication; the record says so rather than implying a delegation.
    require(docs['captioner']['approval']['publication_authorized'] is False
            and docs['axon']['review']['website_edited'] is False, 'a research record changed its authority')
    stated(rr['researchRelease'], 'passes an internal conditional-probe handoff and does not itself authorise '
                                  'publication', 'the release record')
    stated(rr['researchRelease'], 'Publication on the site rests on the site owner’s decision of '
                                  f'{manifest["approval"]["date"]}.', 'the release record')
    listed = flat(' '.join(manifest['notPublished']))
    missing = [x for x in NOT_PUBLISHED_PHRASES if x not in listed]
    require(not missing, f'the not-published list does not name {missing}')
    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['freeze_date'],
        'status': 'aggregate_preview',
        'title': 'A separate panel: two frozen encoders on ten-second arithmetic and rest windows',
        'question': ('Do frozen EEG-Captioner or AXON features separate rest from mental arithmetic in ten-second '
                     'windows better than Welch band power?'),
        'placement': {
            'page': '/topics/pilot-studies/', 'anchor': 'eegmat-ten-second', 'after_anchor': 'neurorvq',
            'pointer_from': '/protocols/arithmetic-rest/',
            'counted_in_pilots': False, 'leaderboard': False, 'core_matrix_row': False,
            'new_dataset_count': 0, 'new_model_count': 0,
            'subsections': ['eeg_captioner', 'axon'], 'shared_table': False,
            'text': ('A separate panel on the pilot studies page, outside the pilot count and every leaderboard and '
                     'model ranking, with one subsection per encoder; the core Arithmetic & rest matrix keeps its rows.'),
        },
        'metric_units': ('balanced accuracy is a proportion in [0,1] and paired differences are differences of '
                         'proportions: multiply by 100 for percent or percentage points; dimensions and counts of '
                         'people, recordings, windows, channels, folds and draws are whole numbers; QC ratios are '
                         'proportions of channels or of recording duration'),
        'scope': (f'Two frozen encoders, each read by one fixed ridge head (alpha {probe["alpha"]}) in '
                  f'{WORDS[cohort["folds"]]} subject-disjoint folds on the same {cohort["windows"]} ten-second EEGMAT windows '
                  f'from {cohort["people"]} people, and each set against Welch band power on the same windows. Scores '
                  'are participant-mean balanced accuracies; each paired difference carries a participant-bootstrap '
                  'interval.'),
        'cohort': cohort,
        'source_annotation_qc': qc,
        'probe': probe,
        'interval': interval,
        'eeg_captioner': captioner,
        'axon': axon,
        'encoder_contrast': encoder_contrast_block(docs),
        'separate_from_two_second_results': separation_block(docs, cohort),
        'rights': rights_block(docs),
        'limitations': limitations_block(docs, cohort),
        'release_record': {
            'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
            'rights': rr['rights'], 'research_release': rr['researchRelease'],
            'research_release_status': {'eeg_captioner': docs['captioner']['approval']['status'],
                                        'axon': docs['axon']['review']['decision']},
            'binding': rr['binding'],
        },
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {'eeg-captioner': rc['outcome']['sha256'], 'axon': ra['aggregate']['sha256']},
            'release_approval_sha256': {'eeg-captioner': rc['approval']['sha256'], 'axon': ra['review']['sha256']},
            'protocol_sha256': {'eeg-captioner': rc['protocol']['sha256'], 'axon': ra['protocol']['sha256']},
            'released_files_unchanged': ['mvp.json', 'pilot-studies-update.json', 'eegpt-core-update.json',
                                         'adaptation-update.json', 'neurolm-eegmat-update.json'],
        },
    }
    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 3, 'the private names were not read from the pinned records')
    prose_check(payload, private)
    licences_per_part(payload)
    validate_public(payload)
    published = set(numbers(payload))
    approved = {cap['encoder'], cap['baseline'], ax['encoder'], ax['baseline']}
    design = {v for v in numbers(cohort)} | {v for v in numbers(probe)} | {v for v in numbers(interval)}
    leaked = [v for v in withheld_values(docs, approved | design) if v in published]
    require(not leaked, f'a withheld value reached the export: {leaked[:3]}')
    crossed = [v for v in other_eegmat_figures(docs) if v in published]
    require(not crossed, f'a figure of another EEGMAT result reached the export: {crossed[:3]}')
    return payload


def inputs_available():
    """Whether the pinned inputs are on this machine. The research folders are local-only, so a clone checks the
    served file against the committed export audit's hash; only the maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return (PROJECT / OWNER_DECISIONS).exists() and all((PROJECT / r['path']).exists() for r in input_refs(manifest))


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_eegmat_ten_second_export
    return audit_eegmat_ten_second_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
