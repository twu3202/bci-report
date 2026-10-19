"""Release the IESSEEG awake case-control pilot, aggregate-only, as a section of the clinical groups page.

Two research studies on the same 100 people (50 cases of infantile epileptic spasms syndrome, 50 controls) and the
same five published participant folds: six CPU arms that separate cases from controls with and without EEG, including
an age-only and a recording-settings-only control, and four arms that read frozen NeuroLM features with the same
probes. Each study has an export that its release review approves byte for byte. The owner's decisions for this
release (D1, D7 option A, D13) publish both on /topics/clinical-groups/, with the age <=2 column as approved; no
dataset page, no new dataset or model in any count, outside every leaderboard.

Its own publication boundary. Every figure is read from a file the release manifest pins by SHA-256:
- each score block verbatim from its research export, and only if the release review binds that export's hash, the
  independent numerical audit the review binds holds the same block value for value and type for type, and the
  block's own confusion counts give its balanced accuracy, accuracy, sensitivity, specificity and F1;
- the cohort and fold structure from the two exports, the protocols and the QC audit's selection record; the age
  band's counts from both exports and both reviews; the input-cohort QC figures from the independent cohort timing QC result audit, each of them also
  stated in the hash-bound CPU handoff;
- every method fact from the pinned protocol of its study; attribution only from the IESSEEG release card (README and
  LICENSE at the pinned revision, the bytes the CPU review binds).
The handoffs are copy sources only: they name private storage, so this export reads them to check wording and to learn
which private names to refuse, and publishes none of their sentences.

What this export refuses:
- participant rows, per-fold metrics, predictions, probabilities, features and thresholds, by key and, for the
  per-fold metrics the scored aggregates hold, by value;
- per-group age means, medians and quartiles and sex counts (the rule of the Parkinson's comparison in
  clinical-update.json), by key and by value against the cohort metadata audit; the age <=2 column publishes only the
  band's size and its case and control counts, which both reviews approve;
- a score that is not the approved export's, an export the review does not bind, a changed owner decision;
- any conference or submission reference, private paths, host and storage names, version labels, update markers,
  months used as labels, "X, not Y" hedges, Jev, and a claim these results do not support unless it is negated.

    python3 pipeline/publication/export_clinical_iesseeg_update.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from export_snapshot import validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261020'
MANIFEST = REVIEW / 'clinical-iesseeg-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'clinical-iesseeg-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/clinical-iesseeg-update.json',
           PROJECT / 'site/public/data/clinical-iesseeg-update.json')
RELEASE_ID = 'clinical-iesseeg-update-20261020'
SCHEMA = 'bci-report-clinical-iesseeg-update-v1'

REPOSITORY = 'Capur/IESSEEG'
REVISION = '1c32ee3a425a324808a9d275b60ce85625af35c8'
HF = f'https://huggingface.co/datasets/{REPOSITORY}'
TREE_URL, README_URL, LICENSE_URL = f'{HF}/tree/{REVISION}', f'{HF}/blob/{REVISION}/README.md', f'{HF}/blob/{REVISION}/LICENSE'
DEED = 'https://creativecommons.org/licenses/by/4.0/'
STATUS = 'audited_aggregate_development_release_eligible'
CPU_ARMS = ('SOURCE_PRIOR', 'AGE', 'ACQUISITION_METADATA', 'EEG', 'EEG_PLUS_AGE', 'AGE_RESIDUAL_EEG')
NEURAL_ARMS = ('TOKENIZER', 'TOKENIZER_AGE_RESIDUAL', 'GPT_HIDDEN', 'GPT_HIDDEN_AGE_RESIDUAL')
BLOCK_KEYS = ('n', 'balanced_accuracy', 'auroc', 'accuracy', 'f1', 'sensitivity', 'specificity', 'confusion_tn_fp_fn_tp')
TOL = 1e-12
TRIVIAL = {0.0, 0.25, 0.5, 0.75, 1.0}

# The titles the release reviews approved, and the section question the plan pins.
TITLE_CONTROLS = 'Age and acquisition controls for an awake EEG case-control pilot'
TITLE_NEUROLM = 'Do frozen EEG representations survive age controls?'
QUESTION = 'Do EEG case-control results survive age and recording-setting controls?'
CAPTION = ('Point estimates out of fold; no interval or test was specified. One awake recording per person, first 60 s. '
           'Age and recording settings differ between groups; regressing out age is a sensitivity analysis.')
BOUNDARY = ('The probes and every score were reproduced independently; the NeuroLM features themselves were not '
            're-extracted by a second implementation.')

ARMS = {
    'SOURCE_PRIOR': ('Training prior', 'reference',
                     'No input: the training fold’s share of cases, which calls every person a case'),
    'AGE': ('Age only', 'confound_control', 'No EEG: log1p of age at the recording, and its square'),
    'ACQUISITION_METADATA': ('Acquisition metadata only', 'diagnostic_control',
                             'No EEG: the original scalp channel count and sampling rate'),
    'EEG': ('EEG spectral features', 'eeg', 'The 102 log band-power features of the 17 channels'),
    'EEG_PLUS_AGE': ('EEG spectral features + age', 'eeg_with_age', 'The 102 spectral features and the two age terms'),
    'AGE_RESIDUAL_EEG': ('EEG after training-fold age residualization', 'sensitivity_analysis',
                         'The 102 spectral features with age regressed out inside each training fold'),
    'TOKENIZER': ('Frozen EEG tokenizer', 'frozen_representation', 'The 768 frozen tokenizer values of each person'),
    'TOKENIZER_AGE_RESIDUAL': ('Tokenizer + training-fold age residualization', 'sensitivity_analysis',
                               'The tokenizer values with age regressed out inside each training fold'),
    'GPT_HIDDEN': ('Frozen GPT hidden states', 'frozen_representation',
                   'The 768 frozen GPT hidden-state values of each person'),
    'GPT_HIDDEN_AGE_RESIDUAL': ('GPT hidden states + training-fold age residualization', 'sensitivity_analysis',
                                'The GPT hidden-state values with age regressed out inside each training fold'),
}

# A clinical cohort's demographics (as export_clinical_update refuses them), per-fold and per-person values.
DEMOGRAPHIC_KEYS = {'age_mean', 'age_means', 'mean_age', 'age_summary', 'mean_years', 'median_years', 'quartiles_years',
                    'gender_counts', 'sex_counts', 'confound_context', 'age', 'gender', 'sex', 'education',
                    'age_at_eeg_years', 'age_at_onset_months', 'lead_time_months', 'treatment_response_label'}
REFUSED_KEYS = PER_PERSON_KEYS | DEMOGRAPHIC_KEYS | {
    'per_fold', 'folds_detail', 'predictions', 'probabilities', 'features', 'threshold', 'participants_rows',
    'participant_id', 'patient_id', 'recording_id', 'elapsed_seconds', 'peak_rss_bytes', 'private_root', 'host'}
REFUSED_KEY_FRAGMENTS = ('per_fold', 'per_person', 'per_participant', 'per_subject', 'participant_id', 'patient_id',
                         'subject', 'age_mean', 'mean_years', 'median', 'quartile', 'percentile', 'sex', 'gender',
                         'path', 'private', 'host', 'elapsed', 'rss', 'memory', 'device')

LOCAL_ROOTS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/|(?:^|[\s(])~/', re.IGNORECASE)
SOURCE_IDS = re.compile(r'\bsub[-_]\d+|\bsub-[A-Z]{2,}|\bsubj\d+|\.(?:npz|npy|edf|mat|tsv)\b', re.IGNORECASE)
SUBMISSION = re.compile(r'ICLR|OpenReview|NeurIPS|submission|conference|datasets-and-benchmarks|double-blind|anonymi[sz]ed '
                        r'review', re.IGNORECASE)
VERSION_LABEL = re.compile(r'(?<![./\w-])v\d+\b')
UPDATE_MARKER = re.compile(r'(?<![\w-])(?:updated?|added|newly)(?![\w.-])|\bsince \d|\brun on \d|\bsnapshot \d|\bgenerated \d',
                           re.IGNORECASE)
MONTH_LABEL = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b')
HEDGE = re.compile(r'[,;]\s+not\s', re.IGNORECASE)
CLAIMS = re.compile(r'\bclinical\b|\bmedical\b|diagnostic (?:accuracy|utility|use)|\bscreening\b|zero-shot|\bcausal'
                    r'|\bcaused\b|significan|superior|outperform|\bbeats?\b|\bbest\b|\bwinner|\branks?\b|\branked\b'
                    r'|\branking\b|state[- ]of[- ]the[- ]art|\bunseen\b|deconfound|age[- ]matched', re.IGNORECASE)
NEGATION = re.compile(r"\b(?:not|no|never|nor|neither|without|cannot|none)\b|n't\b", re.IGNORECASE)
LINKS = re.compile(r'(?:https?://|/)[\w./#%-]+|\b[\w-]+\.json\b')   # links and file names, not prose
# Quoted from the release card: checked for paths, names, labels and submissions, never reworded.
QUOTED = ('$.dataset.requested_citation', '$.dataset.prior_reuse.study_title', '$.dataset.ethics_as_stated.quote',
          '$.cohort.age_matching_as_stated.quote')


# ---------------------------------------------------------------------------- helpers
def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def count(x):
    return isinstance(x, int) and not isinstance(x, bool)


def close(a, b, label, tol=TOL):
    require(number(a) and number(b) and abs(a - b) <= tol, f'{label}: {a!r} does not equal {b!r}')


def identical(a, b):
    """Equal value for value and type for type: 0.8236 is not 0.8235999999999999 and 1 is not 1.0."""
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


def strings(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        yield trail, value


def floats(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from floats(v)
    elif isinstance(value, list):
        for v in value:
            yield from floats(v)
    elif isinstance(value, float):
        yield value


# ---------------------------------------------------------------------------- inputs
def load(manifest):
    """Every pinned input, refused unless it is byte for byte the file the manifest names."""
    docs = {}
    for k, ref in manifest['sources'].items():
        docs[k] = pinned_text(ref, k) if ref['path'].endswith(('.md', 'LICENSE')) else pinned(ref, k)[0]
    for k, ref in manifest['withheldReference'].items():
        docs[k] = pinned(ref, k)[0]
    docs['clinical'] = pinned(manifest['published']['clinical'], 'clinical-update.json')[0]
    return docs


def owner_decisions(manifest):
    """The quoted decisions are still the owner's: D1 publishes IESSEEG, D7 keeps option A, D13 places the section."""
    od = manifest['approval']['ownerDecisions']
    decisions = json.loads((PROJECT / od['path']).read_bytes())['decisions']
    current = {'D1': decisions['D1']['answer'], 'D13': decisions['D13']['answer'],
               'D7': decisions['defaults_stated_to_owner_and_not_objected']['D7']}
    for k, text in od['quoted'].items():
        require(current[k] == text, f'owner decision {k} changed; the release must be reviewed again')
    require('IESSEEG' in current['D1'] and 'option A' in current['D7'] and 'clinical-groups' in current['D13'],
            'the owner decisions do not publish this section as approved')
    return current


def private_names(docs):
    """The home, storage and host names the handoffs use, read from them, never spelled in this file."""
    text = docs['controlsHandoff'] + docs['neurolmHandoff']
    names = {n for pair in re.findall(r'/(?:home|Users|Volumes)/([^/\s`]+)/([^/\s`]+)', text) for n in pair}
    machines = set(re.findall(r'\b(?:on|or) ([A-Z][A-Za-z]{1,8}\d+)\b', text))    # "stay on <host>", "the Mac or <disk>"
    names |= machines | {re.sub(r'\d+$', '', m) for m in machines}
    return {n for n in names if len(n) >= 3}


# ---------------------------------------------------------------------------- the reviews bind the exports
def reviews(docs, manifest):
    src = manifest['sources']
    pairs = (('controls', 'approve_exact_hash_bound_aggregate_development_handoff_and_export'),
             ('neurolm', 'approve_exact_hash_bound_frozen_NeuroLM_aggregate_development_handoff_and_export'))
    for study, decision in pairs:
        rv = docs[f'{study}ReleaseReview']
        require(rv['status'] == 'independent_aggregate_release_review_passed' and rv['decision'] == decision
                and rv['final_export_status'] == STATUS, f'{study}: the release review does not approve the export')
        require(rv['export_sha256'] == src[f'{study}Export']['sha256']
                and rv['handoff_sha256'] == src[f'{study}Handoff']['sha256'],
                f'{study}: the release review binds another export or handoff')
        bound = rv['reviewed_artifact_sha256']
        for key in (f'{study}NumericalAudit', f'{study}Protocol'):
            require(src[key]['sha256'] in bound.values(), f'{study}: the review does not bind the pinned {key}')
        require(rv['numeric_checks']['full_population_n_cases_controls'] == [100, 50, 50],
                f'{study}: the review checked another cohort')
        require(rv['numeric_checks']['same_sealed_predictions_no_subgroup_refits'] is True,
                f'{study}: the age band was refitted')
    cpu, neu = docs['controlsReleaseReview'], docs['neurolmReleaseReview']
    require(cpu['publication_or_website_action_performed'] is False, 'the CPU review acted on the website')
    bound = cpu['reviewed_artifact_sha256']
    require(bound['evidence/dataset-access-20261016/iesseeg-README.md'] == src['releaseCard']['sha256']
            and bound['evidence/dataset-access-20261016/iesseeg-LICENSE'] == src['releaseLicence']['sha256'],
            'the CPU review binds another release card or licence')
    require(bound['validation/IESSEEG Awake Baseline Scored Aggregates.json']
            == manifest['withheldReference']['controlsScoredAggregates']['sha256'], 'another scored aggregate file')
    cr = cpu['claims_review']
    for flag in ('all_six_controls_retained', 'no_single_arm_overall_winner_claim',
                 'residualization_described_as_sensitivity_not_causal_explanation',
                 'acquisition_arm_diagnostic_non_eeg', 'age_subgroup_descriptive_not_age_matched_independent_benchmark',
                 'point_estimates_no_CI_or_significance_claim', 'raw_rows_signals_ages_predictions_checkpoints_absent_from_export'):
        require(cr[flag] is True, f'CPU review: {flag} is not affirmed')
    require(cr['canonical_dataset_increment'] == 0, 'CPU review: a dataset count increment')
    nr = neu['claims_review']
    for flag in ('frozen_features_plus_supervised_logistic_probes_explicit', 'checkpoint_not_updated',
                 'all_four_arms_and_prior_CPU_controls_retained', 'no_reliable_improvement_or_architecture_only_advantage_claim',
                 'preprocessing_difference_explicit', 'no_independent_real_feature_reextraction_claim'):
        require(nr[flag] is True, f'NeuroLM review: {flag} is not affirmed')
    require(nr['canonical_dataset_increment'] == 0 and nr['new_model_identity'] is False,
            'NeuroLM review: a dataset or model count increment')
    nb = neu['numerical_audit_boundary']
    require(nb['real_neural_features_independently_reextracted'] is False, 'the re-extraction boundary changed')
    require(neu['provenance']['checkpoint_instruction_stage_and_participant_exposure_unverified'] is True,
            'the checkpoint stage or exposure is no longer unverified; the section must be reviewed')
    require(neu['provenance']['model_code_checkpoint_and_data_not_redistributed'] is True, 'a redistribution changed')
    return {'age_band': cpu['numeric_checks']['age_le_2_n_cases_controls']}


# ---------------------------------------------------------------------------- the score blocks
def score_block(block, audited, cohort, label):
    """One block verbatim, refused unless the independent numerical audit holds the same block and the block's own
    confusion counts give its threshold metrics."""
    require(tuple(block) == BLOCK_KEYS, f'{label}: another set of metric fields')
    require(identical(block, audited), f'{label}: the export and its independent numerical audit differ')
    tn, fp, fn, tp = block['confusion_tn_fp_fn_tp']
    n, cases, controls = cohort
    require(all(count(x) and x >= 0 for x in (tn, fp, fn, tp)), f'{label}: confusion counts are not counts')
    require(block['n'] == n == tn + fp + fn + tp and tp + fn == cases and tn + fp == controls,
            f'{label}: the confusion counts are not this cohort')
    sens, spec = tp / (tp + fn), tn / (tn + fp)
    close(block['sensitivity'], sens, f'{label} sensitivity')
    close(block['specificity'], spec, f'{label} specificity')
    close(block['balanced_accuracy'], (sens + spec) / 2, f'{label} balanced accuracy')
    close(block['accuracy'], (tp + tn) / n, f'{label} accuracy')
    close(block['f1'], 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn), f'{label} F1')
    require(number(block['auroc']) and 0.0 <= block['auroc'] <= 1.0, f'{label}: AUROC out of range')
    return {k: (list(v) if isinstance(v, list) else v) for k, v in block.items()}


def arms(export_arms, audit, ids, band, label):
    require(tuple(export_arms) == ids and tuple(audit) == ids, f'{label}: another arm set or order')
    out = []
    for arm in ids:
        name, role, inputs = ARMS[arm]
        eeg = arm not in ('SOURCE_PRIOR', 'AGE', 'ACQUISITION_METADATA')
        out.append({'id': arm, 'label': name, 'role': role, 'inputs': inputs, 'eeg_input': eeg,
                    'excluded_from_model_comparisons': not eeg,
                    'pooled': score_block(export_arms[arm]['pooled'], audit[arm]['pooled'], (100, 50, 50),
                                          f'{label} {arm} all 100'),
                    'age_le_2': score_block(export_arms[arm]['age_le_2'], audit[arm]['age_le_2'], tuple(band),
                                            f'{label} {arm} age <=2')})
    prior = next(a for a in out if a['id'] == 'SOURCE_PRIOR') if 'SOURCE_PRIOR' in ids else None
    if prior:   # "calls every person a case": no true or false negatives in either block
        for b in ('pooled', 'age_le_2'):
            tn, _, fn, _ = prior[b]['confusion_tn_fp_fn_tp']
            require(tn == 0 and fn == 0, f'{label}: the training prior does not call every person a case')
    return out


# ---------------------------------------------------------------------------- cohort, QC, method facts
def cohort_block(cpu, neu, qc, cp, np_, band):
    sel = qc['selection']
    require((cpu['participants'], cpu['cases'], cpu['controls']) == (100, 50, 50)
            == (neu['cohort']['people'], neu['cohort']['case'], neu['cohort']['control'])
            == (sel['people'], sel['case_pre'], sel['control']), 'the two studies and the QC audit name other cohorts')
    require(sel['awake'] == 100 and sel['post'] == 0, 'the cohort is not one awake PRE or CONTROL recording each')
    folds = sel['folds']
    require(len(folds) == 5 == neu['cohort']['participant_folds'] == np_['folds']
            and all((f['outer_train_people'], f['outer_test_people'], f['case'], f['control']) == (80, 20, 10, 10)
                    for f in folds) and np_['train_test'] == [80, 20], 'another fold structure')
    require(cp['window_seconds'] == np_['window_seconds'] == neu['cohort']['seconds_per_person'] == 60,
            'another window')
    require(len(cp['channels']) == len(set(cp['channels'])) == neu['cohort']['common_channels'] == 17
            and cp['channels'] == np_['channels'], 'another channel set')
    stated(cpu['split'], 'Five published participant-disjoint outer folds', 'CPU export split')
    stated(cpu['selection'], 'One deterministic clinician-selected awake recording/person', 'CPU export selection')
    stated(cp['selection'], 'no amplitude rejection, exclusions, signal-driven window choice', 'CPU protocol selection')
    ag = cpu['age_subgroup']
    require([ag['n'], ag['cases'], ag['controls']] == band == [neu['cohort']['age_le_2_people'],
                                                              neu['cohort']['age_le_2_case'],
                                                              neu['cohort']['age_le_2_control']],
            'the age band counts differ between the exports and the reviews')
    require(ag['maximum_age_years'] == 2 and ag['same_sealed_predictions'] is True and ag['refit'] is False
            and 'age <= 2 years, same sealed OOF predictions, no refits' in cp['subgroup'],
            'the age band is not the protocol’s')
    return {
        'people': sel['people'], 'cases': sel['case_pre'], 'controls': sel['control'], 'classes': 2,
        'chance_level': 0.5,
        'composition': ('Cases of infantile epileptic spasms syndrome, each on the recording made before the treatment '
                        'the source study evaluated, and controls on their control recording; one institution’s '
                        'retrospective cohort'),
        'recording': ('one clinician-selected awake segment per person, chosen by a fixed lexicographic rule with no '
                      'signal-driven choice; its first 60 s'),
        'seconds_analysed': cp['window_seconds'], 'channels': len(cp['channels']),
        'reference': 'the common average of the 17 channels shared by every recording',
        'folds': len(folds), 'train_people': folds[0]['outer_train_people'], 'held_out_people': folds[0]['outer_test_people'],
        'held_out_cases': folds[0]['case'], 'held_out_controls': folds[0]['control'],
        'split': 'the publisher’s five participant-disjoint folds; each person is held out once',
        'prediction_unit': 'one out-of-fold prediction per person and arm',
        'labels': 'each participant’s case or control status',
    }, {'maximum_age_years': ag['maximum_age_years'], 'people': ag['n'], 'cases': ag['cases'],
        'controls': ag['controls'], 'same_predictions': ag['same_sealed_predictions'], 'refit': ag['refit']}


def input_qc(qc, handoff):
    """The cohort QC figures from the independent result audit; the hash-bound CPU handoff states each of them."""
    require(qc['audit_status'] == 'passed_independent_readonly_checks'
            and qc['decision'].startswith('accept_completed_bounded_timing_calibration_characterization'),
            'the cohort timing QC audit did not pass')
    ra, d = qc['recomputed_aggregate'], qc['distributions']
    require(ra['records_completed'] == ra['passed'] == 100 and ra['held'] == 0 and ra['records_with_gaps'] == 0
            and qc['timing']['gap_count'] == 0 and qc['privacy']['private_rows_exported'] is False,
            'the cohort QC is not 100 passed recordings with no gaps')
    channels = sorted(((int(k), v) for k, v in d['scalp_channels'].items()), key=lambda x: -x[1])
    rates = []
    for k, v in d['scalp_sampling_hz'].items():
        require(float(k).is_integer(), 'a fractional sampling rate')
        rates.append((int(float(k)), v))
    rates.sort(key=lambda x: -x[1])
    require(sum(v for _, v in channels) == sum(v for _, v in rates) == 100, 'the QC distributions do not cover 100')
    stated(handoff, f'{qc["payload_hashes_verified"]} assets, {qc["payload_bytes_verified"]:,} bytes; '
                    f'{ra["passed"]} EDF recordings, zero measured gaps', 'CPU handoff QC')
    stated(handoff, f'{channels[0][1]} recordings have {channels[0][0]} scalp channels and {channels[1][1]} have '
                    f'{channels[1][0]}', 'CPU handoff channels')
    stated(handoff, f'{rates[0][1]} are {rates[0][0]} Hz and two are {rates[1][0]:,} Hz', 'CPU handoff rates')
    require(rates[1][1] == 2, 'the handoff’s “two” is another count')
    return {
        'assets': qc['payload_hashes_verified'], 'bytes': qc['payload_bytes_verified'],
        'recordings': ra['records_completed'], 'recordings_passed': ra['passed'], 'recordings_held': ra['held'],
        'recordings_with_gaps': ra['records_with_gaps'],
        'scalp_channels': [{'channels': c, 'recordings': v} for c, v in channels],
        'sampling_hz': [{'hz': h, 'recordings': v} for h, v in rates],
        'checked_by': 'an independent read-only audit of every input file’s hash, timing and calibration',
        'note': 'Endpoint and constant-sample counts were kept as descriptions; no recording was excluded on them.',
    }


def controls_method(cp, handoff):
    f, w = cp['features'], cp['features']['welch']
    require(f['per_channel'] == 6 and f['total'] == 102 == 6 * len(cp['channels']) and f['sampling'].startswith('native')
            and w['window'] == 'hann periodic' and w['seconds'] == 4 and w['overlap_fraction'] == 0.5
            and f['bands_hz'] == [[1, 4], [4, 8], [8, 13], [13, 30], [30, 45]] and f['denominator_hz'] == [1, 45],
            'another spectral recipe')
    m = cp['model']
    require(m['C'] == 1.0 and m['penalty'] == 'l2' and m['class_weight'] is None
            and m['scaler'].startswith('StandardScaler') and 'training only' in m['scaler'], 'another classifier')
    require(tuple(cp['arms']) == CPU_ARMS and cp['age_basis'] == 'log1p(age_at_eeg_years), its square'
            and cp['residualization'].startswith('per outer train OLS') and 'train coefficients on train and test'
            in cp['residualization'] and cp['source_prior'].startswith('training prevalence'),
            'another arm definition')
    require(cp['acquisition_metadata'].startswith('original scalp channel count 17/19, native fs 200/2000'),
            'another acquisition control')
    require(cp['confidence_intervals'].startswith('deferred; none'), 'the protocol specified intervals')
    stated(handoff, '4-second periodic Hann windows, 50% overlap and 0.25 Hz bins', 'CPU handoff spectra')
    return {
        'spectra': ('Welch spectra at each recording’s native rate: log relative power in five bands from 1 to 45 Hz and '
                     'log total 1–45 Hz power for each of the 17 channels'),
        'feature_count': f['total'], 'features_per_channel': f['per_channel'],
        'welch_window_seconds': w['seconds'], 'welch_overlap': w['overlap_fraction'],
        'frequency_resolution_hz': 1 / w['seconds'], 'bands_hz': [list(b) for b in f['bands_hz']],
        'classifier': ('standardisation fitted on the training fold only, then L2 logistic regression; fixed in advance, '
                       'with no tuning'),
        'logistic_c': m['C'],
        'age_terms': 'log1p of age at the recording, in years, and its square',
        'age_residualization': ('inside each training fold, each feature is regressed on an intercept and the two age '
                                'terms; the training-fold coefficients are applied to the training and held-out people'),
        'acquisition_terms': 'the original scalp channel count (17 or 19) and native sampling rate (200 or 2,000 Hz)',
    }


def neurolm_method(np_, neu, cpu_protocol):
    pre = np_['preprocessing']
    require(pre['sequence'] == ['EDF affine uV', 'common17 CAR at native fs', 'fs2000 only resample_poly1/10',
                                '200Hz Butterworth SOS bandpass', '50Hz notch', '60Hz notch', 'divide100',
                                '15 nonoverlapping4s windows'], 'another preprocessing sequence')
    bp, notch, rs = pre['bandpass'], pre['notch'], pre['resampling']
    require(bp['hz'] == [0.1, 75] and bp['fs'] == 200 and bp['application'] == 'sosfiltfilt' and notch['hz'] == [50, 60]
            and pre['amplitude_divisor'] == 100 and (rs['up'], rs['down']) == (1, 10), 'another filter chain')
    windows, seconds = map(int, re.fullmatch(r'(\d+) nonoverlapping(\d+)s windows', pre['sequence'][-1]).groups())
    shape = np_['patches']['shape']
    require(windows * seconds == np_['window_seconds'] and shape[1] == len(np_['channels']) * seconds
            and shape[2] == bp['fs'] and np_['patches']['padding'] is False, 'another token layout')
    at, rep = np_['attention'], np_['representations']
    require(at['text_tokens'] == 0 and at['generation'] is False and at['hooks'] is False
            and 'key_time <= query_time' in at['GPT'] and at['tokenizer'].startswith('all-true'), 'another attention')
    require(rep['dimensions'] == 768 and 'mean68 then mean15 windows' in rep['TOKENIZER']
            and 'mean68 then mean15 windows' in rep['GPT_HIDDEN'], 'another pooling')
    require(tuple(np_['arms']) == NEURAL_ARMS and np_['head'].startswith('same pinned baseline')
            and np_['age_residual'].startswith('same pinned baseline') and np_['metrics'].endswith('noCIs'),
            'another probe')
    require(np_['model'].startswith('NeuroLM-B; strict full state; no head/model tuning')
            and np_['checkpoint_sha256'] == neu['checkpoint_sha256'] and np_['source_revision'] == neu['model_source_revision'],
            'another checkpoint')
    require(cpu_protocol['model']['C'] == 1.0, 'the shared probe changed')
    return {
        'preprocessing': ('EDF samples in microvolts and the common average of the 17 channels at the native rate; the '
                          'two 2,000 Hz recordings resampled to 200 Hz; a 0.1–75 Hz band-pass, 50 and 60 Hz notch filters, '
                          'and amplitudes divided by 100'),
        'sampling_hz': bp['fs'], 'resample_factor': rs['down'], 'bandpass_hz': list(bp['hz']), 'notch_hz': list(notch['hz']),
        'amplitude_divisor': pre['amplitude_divisor'], 'windows': windows, 'window_seconds': seconds,
        'tokens_per_window': shape[1], 'token_seconds': shape[2] // bp['fs'], 'dimensions': rep['dimensions'],
        'tokens': 'one token per channel and second, with no padding',
        'attention': ('the tokenizer sees every token; in the GPT branch each token sees its own second and earlier '
                      'ones, with the channels of the same second visible to each other'),
        'representations': ('tokenizer states after its final normalisation, and GPT hidden states after the final layer '
                            'normalisation; each averaged over the tokens of a window, then over the windows'),
        'probe': 'the classifier and the age residualization of the spectral arms, unchanged',
    }


def release_card(readme, licence, cpu, neu):
    """Attribution from the release card at the pinned revision only."""
    text = flat(readme)
    require(readme.startswith('---\nlicense: cc-by-4.0\n'), 'the card does not declare cc-by-4.0')
    m = re.search(r'Please cite \*\*(.+?)\*\* when using this release\.', text)
    require(m is not None, 'the card requests no citation')
    title = m.group(1)
    reuse = re.search(r'The (\d+) case clinician-selected EEG segments were previously analyzed by (Rajaraman et al\. '
                      r'\(\d{4}\)), \*(.+?)\*\.', text)
    require(reuse is not None, 'the card declares no prior reuse')
    segments, study, study_title = int(reuse.group(1)), reuse.group(2), reuse.group(3)
    ethics = re.search(r'(The retrospective study received institutional review board approval .+?\.) '
                       r'(Do not attempt to re-identify participants\.)', text)
    require(ethics is not None, 'the card states no ethics approval')
    require('Controls are not fully age matched.' in text, 'the card no longer states the age matching')
    stated(text, f'The dataset and annotations are released under [CC BY 4.0]({DEED})', 'card licence')
    stated(licence, 'The IESSEEG dataset and annotations are licensed under CC BY 4.0.', 'LICENSE')
    for c in (cpu['citation']['publisher_requested_title'], neu['attribution']['citation']):
        require(c == title, 'an export cites another title than the card requests')
    require(cpu['citation']['readme_url'] == neu['attribution']['dataset_readme_url'] == README_URL
            and cpu['citation']['license_url'] == neu['attribution']['dataset_license_url'] == LICENSE_URL
            and cpu['source_url'] == neu['attribution']['dataset_url'] == TREE_URL, 'another pinned URL')
    require(f'{segments} case clinician-selected segments' in cpu['citation']['prior_reuse']
            and study in cpu['citation']['prior_reuse'] and study_title in cpu['citation']['prior_reuse'],
            'the export’s prior-reuse declaration is not the card’s')
    require(cpu['data_license'] == 'CC-BY-4.0' and 'CC-BY-4.0' in neu['attribution']['dataset'], 'another licence')
    require(not SUBMISSION.search(title + study_title + ethics.group(0)), 'the card text names a submission')
    return {'title': title, 'segments': segments, 'study': study, 'study_title': study_title,
            'ethics': f'{ethics.group(1)} {ethics.group(2)}', 'age_matching': 'Controls are not fully age matched.'}


def wording(docs):
    """The approved titles and the copy the payload restates are in the hash-bound handoffs."""
    ch, nh = docs['controlsHandoff'], docs['neurolmHandoff']
    stated(ch, f'“{TITLE_CONTROLS}”', 'CPU handoff title')
    stated(nh, f'“{TITLE_NEUROLM}”', 'NeuroLM handoff title')
    stated(ch, 'It is a descriptive subgroup, not an independently trained age-matched benchmark.', 'age band')
    stated(ch, 'the all-positive prior already has F1=66.67% on the balanced cohort', 'F1')
    stated(ch, 'Acquisition metadata uses original channel count and sample rate; it is explicitly a **non-EEG '
               'diagnostic control**', 'acquisition control')
    stated(nh, 'This is a **frozen feature extraction plus supervised logistic-probe study**', 'NeuroLM use')
    stated(nh, 'There is no text query, language generation, model fine-tuning or zero-shot diagnosis.', 'NeuroLM use')
    stated(nh, '**Audit boundary:** real neural features were not re-extracted by a second implementation.', 'boundary')
    stated(nh, 'The supervised heads and metrics were independently reproduced.', 'boundary')
    stated(nh, 'The exact checkpoint instruction-training stage and its prior participant exposure remain unverified',
           'NeuroLM exposure')
    stated(nh, 'resample the two 2,000 Hz recordings to 200 Hz, then fixed 0.1–75 Hz filtering,50/60 Hz notch filters '
               'and division by 100', 'NeuroLM preprocessing')


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
        require(not SUBMISSION.search(text), f'{trail}: a conference or submission reference')
        for n in private:
            require(not re.search(rf'(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])', text, re.IGNORECASE),
                    f'private host or storage name in export: {trail}')
        require('jev' not in text.lower(), f'{trail}: Jev is not part of this release')
        if trail in ('$.schema_version', '$.release_id') or text.startswith('http'):
            continue
        require(not VERSION_LABEL.search(text), f'a version label in export text: {trail}')
        require(not MONTH_LABEL.search(text), f'a month as a label in export text: {trail}')
        if not trail.startswith('$.release_record'):    # the release record is dated by design (/releases/)
            require(not UPDATE_MARKER.search(text), f'an update marker in export text: {trail}')
        if trail in QUOTED or trail.startswith('$.provenance'):
            continue
        require(not HEDGE.search(text), f'{trail}: an “X, not Y” hedge: {text!r}')
        for sentence in re.split(r'(?<=[.;])\s+', text):
            bare = LINKS.sub('', sentence)
            if CLAIMS.search(bare):
                require(NEGATION.search(bare), f'{trail}: an unsupported claim without a negation: {sentence!r}')


def withheld_values(docs, approved):
    """Figures the sources hold that this release does not publish: per-fold metrics and per-group age summaries.
    Values that the approved blocks themselves carry, and trivial levels, cannot be told apart by value."""
    out = set()
    for arm in docs['controlsScoredAggregates']['scores'].values():
        for blocks in (arm['per_fold'], arm['age_le_2_years']['per_fold']):
            out |= set(floats(blocks))
    for group in docs['cohortMetadataAudit']['age_summary'].values():
        for key, value in group.items():
            if key != 'available_n':
                out |= {x for x in (value if isinstance(value, list) else [value]) if isinstance(x, float)}
    return out - approved - TRIVIAL


def age_summary_strings(docs):
    """The age summaries as a reader would print them, two and three decimals."""
    out = set()
    for group in docs['cohortMetadataAudit']['age_summary'].values():
        for k in ('mean_years',):
            out |= {f'{group[k]:.3f}', f'{group[k]:.2f}'}
    return out


# ---------------------------------------------------------------------------- build
def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    require(manifest['release_id'] == RELEASE_ID, 'another release id')
    require(manifest['approval']['decision'] == 'aggregate_preview', 'the manifest does not approve an aggregate')
    require(manifest['approval']['declaredEdits'] == [], 'option A publishes the exports without edits')
    require(manifest['holds'] == [], 'this release has no hold')
    owner_decisions(manifest)
    docs = load(manifest)
    cpu, neu = docs['controlsExport'], docs['neurolmExport']
    require(cpu['status'] == STATUS and neu['release_status'] == STATUS, 'an export is not release eligible')
    require(cpu['dataset'] == REPOSITORY and cpu['revision'] == neu['dataset_revision'] == REVISION,
            'another dataset revision')
    require(cpu['primary_metric'] == 'balanced_accuracy' and cpu['score_scale'] == '0_to_1', 'another metric scale')
    require(neu['confidence_intervals'] is None and cpu['uncertainty'].startswith('Point estimates only'),
            'an export carries intervals')
    require(neu['new_canonical_datasets'] == 0 and neu['new_model_identity'] is False and neu['private_data_included'] is False,
            'the NeuroLM export adds a count or private data')
    bound = reviews(docs, manifest)
    wording(docs)
    card = release_card(docs['releaseCard'], docs['releaseLicence'], cpu, neu)
    cohort, band = cohort_block(cpu, neu, docs['cohortQcAudit'], docs['controlsProtocol'], docs['neurolmProtocol'],
                                bound['age_band'])
    qc = input_qc(docs['cohortQcAudit'], docs['controlsHandoff'])
    ca, na = docs['controlsNumericalAudit'], docs['neurolmNumericalAudit']
    require(ca['status'] == 'passed_independent_numerical_audit' and ca['private_rows_exported'] is False
            and ca['producer_imported'] is False, 'the CPU numerical audit did not pass')
    require(na['status'] == 'passed_independent_scoring_audit' and na['private_rows_exported'] is False,
            'the NeuroLM numerical audit did not pass')
    band_counts = (band['people'], band['cases'], band['controls'])
    cpu_arms = arms(cpu['arms'], ca['aggregate'], CPU_ARMS, band_counts, 'controls')
    neural_arms = arms(neu['scores'], na['aggregate'], NEURAL_ARMS, band_counts, 'NeuroLM')

    # The audit blocks: the exports' counts, equal to the numerical audits the reviews bind.
    ea, rv = cpu['audit'], docs['controlsReleaseReview']['verified_numerical_audit_receipt']
    require((ea['models'], ea['learned_refits'], ea['prior_checks'], ea['reconstructed_predictions'],
             ea['independent_feature_checks'], ea['max_feature_error'], ea['max_probability_error'])
            == (ca['models'], ca['learned_refits'], ca['prior_checks'], ca['reconstructed_predictions'],
                ca['feature_spot_checks'], ca['manual_fft_feature_max_absolute_error'], ca['refit_max_probability_error'])
            and ca['reconstruction_max_absolute_error'] == 0.0, 'the CPU audit counts differ from the numerical audit')
    require(ea['protocol_sha256'] == manifest['sources']['controlsProtocol']['sha256'] == rv['protocol_sha256']
            and ea['score_sha256'] == rv['score_sha256'] == ca['score_sha256'] and ea['seal_sha256'] == rv['seal_sha256'],
            'the CPU export names other sealed files than the review')
    nx, nb = neu['audit'], docs['neurolmReleaseReview']['numerical_audit_boundary']
    require((nx['independent_refits'], nx['held_out_predictions_reconstructed'], nx['reconstruction_error'],
             nx['refit_error'], nx['source_hash_checks'], nx['feature_receipts_checked'],
             nx['real_neural_features_independently_recomputed'])
            == (nb['independent_supervised_head_refits'], nb['reconstructed_predictions'],
                nb['reconstruction_max_absolute_error'], nb['refit_max_probability_error'],
                nb['source_asset_hashes_verified_by_numerical_auditor'], nb['feature_receipt_hashes_layout_finiteness_verified'],
                nb['real_neural_features_independently_reextracted'])
            and (na['preserved_prescore_refits'], na['reconstructed_predictions'], na['checks']['source_payload_hash'],
                 na['checks']['feature_hash']) == (nx['independent_refits'], nx['held_out_predictions_reconstructed'],
                                                   nx['source_hash_checks'], nx['feature_receipts_checked'])
            and nx['seal_sha256'] == nb['seal_sha256'] == na['seal_sha256'] and nx['score_sha256'] == nb['score_sha256'],
            'the NeuroLM audit counts differ from the numerical audit')
    require(nx['numerical_status'] == na['status'] and nx['real_neural_features_independently_recomputed'] is False,
            'the NeuroLM audit boundary changed')

    clinical = docs['clinical']
    require(isinstance(clinical['medical_disclaimer'], str) and 'Not a diagnosis' in clinical['medical_disclaimer']
            and any('age means and sex counts' in x for x in clinical['not_published']),
            'the clinical page’s disclaimer or its demographic rule changed')
    neu_review = docs['neurolmReleaseReview']
    model_source = neu['model_source_url']
    require(model_source == neu_review['provenance']['model_source_url']
            and model_source.endswith(f'/tree/{neu["model_source_revision"]}'), 'another NeuroLM source')
    src = manifest['sources']
    rr = manifest['releaseRecord']

    payload = {
        'schema_version': SCHEMA,
        'release_id': manifest['release_id'],
        'generated_at': manifest['release_date'],
        'status': 'aggregate_preview',
        'title': 'IESSEEG: age and recording-setting controls, with frozen NeuroLM probes',
        'question': QUESTION,
        'placement': {'page': '/topics/clinical-groups/', 'section': 'iesseeg',
                      'subsections': ['iesseeg-controls', 'iesseeg-neurolm'], 'after': 'ds004584',
                      'leaderboard': False, 'dataset_page': False},
        'counts': {'new_canonical_datasets': neu['new_canonical_datasets'],
                   'new_model_identity': neu['new_model_identity'], 'new_dataset_pages': 0},
        'medical_disclaimer': True,
        'medical_disclaimer_wording': {'file': 'clinical-update.json', 'field': 'medical_disclaimer'},
        'metric_units': ('balanced accuracy, AUROC, accuracy, F1, sensitivity and specificity are proportions in [0,1]; '
                         'n and the confusion counts (true negatives, false positives, false negatives, true positives) '
                         'are whole numbers of people; null means not computed'),
        'scope': ('Aggregate development evidence on one public case-control EEG dataset: six arms with and without EEG, '
                  'including age-only and recording-settings-only controls, and four arms that read frozen NeuroLM '
                  'features with the same probes, on the same people and folds. A section of an existing page, outside '
                  'every leaderboard, with no dataset page and no change to any count.'),
        'caption': CAPTION,
        'audit_boundary': BOUNDARY,
        'dataset': {
            'name': 'IESSEEG', 'service': 'Hugging Face', 'repository': REPOSITORY, 'revision': REVISION,
            'url': TREE_URL, 'release_card_url': README_URL, 'licence_file_url': LICENSE_URL,
            'licence': cpu['data_license'], 'licence_scope': 'the dataset and annotations', 'licence_deed': DEED,
            'requested_citation': card['title'],
            'prior_reuse': {'declared_by': 'the publisher, on the release card', 'case_segments': card['segments'],
                            'study': card['study'], 'study_title': card['study_title'],
                            'crosswalk': ('The participant-level crosswalk between that analysis and this release is '
                                          'unresolved; the cohort adds no dataset to any count.')},
            'ethics_as_stated': {'quote': card['ethics'], 'source': README_URL},
            'attribution_source': 'the release card and LICENSE at the pinned revision',
        },
        'cohort': {**cohort, 'age_matching_as_stated': {'quote': card['age_matching'], 'source': README_URL}},
        'age_band': {**band,
                     'note': ('The age ≤2 column re-scores the same out-of-fold predictions for the people aged 2 or '
                              'under, with nothing refitted; it is a descriptive subgroup. Only the band’s size and its '
                              'case and control counts are published; per-group age means and sex counts stay '
                              'unpublished.')},
        'input_qc': qc,
        'display': {
            'columns': [{'block': 'pooled', 'metric': 'balanced_accuracy', 'label': 'Balanced accuracy, all 100'},
                        {'block': 'pooled', 'metric': 'auroc', 'label': 'AUROC, all 100'},
                        {'block': 'age_le_2', 'metric': 'balanced_accuracy', 'label': 'Balanced accuracy, age ≤2 years'}],
            'primary_metric': cpu['primary_metric'],
            'interval': None,
            'reading_rule': ('Both metric columns are shown for every arm; the two metrics order the arms differently, '
                             'and no arm or threshold is chosen from these results.'),
            'f1_headline': False,
            'f1_reason': 'The training prior calls every person a case, and on a balanced cohort that alone gives a high F1.',
        },
        'controls': {
            'title': TITLE_CONTROLS, 'anchor': 'iesseeg-controls',
            'method': controls_method(docs['controlsProtocol'], docs['controlsHandoff']),
            'arms': cpu_arms,
            'audit': {'status': 'pass', 'models': ea['models'], 'learned_refits': ea['learned_refits'],
                      'prior_checks': ea['prior_checks'], 'reconstructed_predictions': ea['reconstructed_predictions'],
                      'independent_feature_checks': ea['independent_feature_checks'],
                      'max_feature_error': ea['max_feature_error'], 'max_probability_error': ea['max_probability_error'],
                      'what': ('An independent program refit every learned model, checked every prior, rebuilt every '
                               'held-out probability with zero difference, and recomputed the features of one recording '
                               'per channel-count and sampling-rate group with its own EDF reader and FFT.'),
                      'protocol_sha256': ea['protocol_sha256'], 'score_sha256': ea['score_sha256'],
                      'seal_sha256': ea['seal_sha256']},
        },
        'neurolm': {
            'title': TITLE_NEUROLM, 'anchor': 'iesseeg-neurolm',
            'model': {'name': 'NeuroLM-B', 'repository': model_source.rsplit('/tree/', 1)[0],
                      'source_revision': neu['model_source_revision'], 'source_url': model_source,
                      'checkpoint_sha256': neu['checkpoint_sha256'],
                      'use': 'a frozen feature extractor read by supervised logistic probes',
                      'weights_updated': False, 'text_tokens': docs['neurolmProtocol']['attention']['text_tokens'],
                      'generation': docs['neurolmProtocol']['attention']['generation'],
                      'checkpoint_stage': 'unknown', 'pretraining_exposure': 'unknown', 'redistributed': False},
            'method': neurolm_method(docs['neurolmProtocol'], neu, docs['controlsProtocol']),
            'arms': neural_arms,
            'audit': {'status': 'pass', 'independent_refits': nx['independent_refits'],
                      'held_out_predictions_reconstructed': nx['held_out_predictions_reconstructed'],
                      'reconstruction_error': nx['reconstruction_error'], 'refit_error': nx['refit_error'],
                      'source_hash_checks': nx['source_hash_checks'],
                      'feature_receipts_checked': nx['feature_receipts_checked'],
                      'real_neural_features_independently_recomputed': nx['real_neural_features_independently_recomputed'],
                      'what': ('An independent program refit every probe and rebuilt every held-out probability with zero '
                               'difference, checked every input file’s hash, and checked each feature file’s hash, '
                               'layout and finiteness.'),
                      'seal_sha256': nx['seal_sha256'], 'score_sha256': nx['score_sha256']},
            'footnote': ('NeuroLM’s preprocessing differs from the spectral pipeline: the two 2,000 Hz recordings are '
                         'resampled to 200 Hz, then a 0.1–75 Hz band-pass, 50 and 60 Hz notches and division by 100. A '
                         'difference between the two pipelines therefore mixes preprocessing with architecture. The '
                         'checkpoint’s training stage and its prior exposure to these participants are unknown.'),
        },
        'limitations': [
            ('A small awake-only case-control development cohort from one institution. Labels are each participant’s '
             'case or control status, with no timed spasm events. There is no external or clinical validation, and the '
             'publisher’s full benchmark is outside this pilot.'),
            ('Regressing out age inside each training fold assigns no share of the score to age, does not show that '
             'confounding is gone, and can also remove disease-related signal that varies with age.'),
            ('Recording settings (channel count and sampling rate) are a no-EEG diagnostic control, shown beside the '
             'EEG rows and kept out of model comparisons.'),
            ('NeuroLM is used as a frozen feature extractor read by supervised logistic probes: its weights are '
             'unchanged, and there is no text prompt, text generation or zero-shot diagnosis.'),
        ],
        'rights': {
            'name': 'IESSEEG · awake case-control pilot',
            'task': 'Case/control discrimination from one awake minute of EEG per person',
            'source': TREE_URL,
            'version': f'Hugging Face {REPOSITORY} at revision {REVISION}',
            'license': cpu['data_license'], 'licenseUrl': DEED,
            'attribution': (f'Dataset: {card["title"]}, Hugging Face {REPOSITORY} at revision {REVISION[:8]}, CC BY 4.0 '
                            f'for the dataset and annotations. The release card declares that the {card["segments"]} '
                            f'case clinician-selected segments were previously analysed by {card["study"]}, '
                            f'{card["study_title"]}.'),
            'privacyReview': ('The release card states institutional review board approval of the retrospective study, '
                              'with waivers of informed consent and HIPAA research authorization, and asks that no one '
                              'attempt to re-identify participants. The publication boundary is the one the Parkinson’s '
                              'comparison uses: aggregate scores only, with no participant rows, predictions, ages or '
                              'per-group age and sex composition; the age ≤2 column gives the band’s size and its case '
                              'and control counts.'),
            'reviewedAt': manifest['reviewed_at'],
            'reviewBasis': [README_URL, LICENSE_URL, TREE_URL],
            'redistributed': False,
        },
        'release_record': {'date': rr['date'], 'decided': manifest['approval']['date'], 'decision': rr['decision'],
                           'age_band': rr['ageBand'], 'placement': rr['placement']},
        'holds': [],
        'not_published': manifest['notPublished'],
        'provenance': {
            'manifest_sha256': sha(manifest_bytes),
            'source_export_sha256': {'controls': src['controlsExport']['sha256'], 'neurolm': src['neurolmExport']['sha256']},
            'release_review_sha256': {'controls': src['controlsReleaseReview']['sha256'],
                                      'neurolm': src['neurolmReleaseReview']['sha256']},
            'numerical_audit_sha256': {'controls': src['controlsNumericalAudit']['sha256'],
                                       'neurolm': src['neurolmNumericalAudit']['sha256']},
            'protocol_sha256': {'controls': src['controlsProtocol']['sha256'], 'neurolm': src['neurolmProtocol']['sha256']},
            'cohort_qc_audit_sha256': src['cohortQcAudit']['sha256'],
            'release_card_sha256': {'readme': src['releaseCard']['sha256'], 'licence': src['releaseLicence']['sha256']},
            'released_files_unchanged': ['clinical-update.json'],
        },
    }

    scrub_check(payload)
    private = private_names(docs)
    require(len(private) >= 3, 'the private names were not read from the handoffs')
    prose_check(payload, private)
    validate_public(payload)
    approved = set(floats([a['pooled'] for a in cpu_arms + neural_arms] + [a['age_le_2'] for a in cpu_arms + neural_arms]))
    published = set(floats(payload))
    leaked = withheld_values(docs, approved) & published
    require(not leaked, f'a withheld value reached the export: {sorted(leaked)[:3]}')
    body = json.dumps(payload, ensure_ascii=False)
    for s in age_summary_strings(docs):
        require(not re.search(rf'(?<![\d.]){re.escape(s)}(?!\d)', body), 'a per-group age summary reached the export')
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
    """Whether the pinned research inputs are on this machine. They are not in the public repository: the research
    folder is local. A clone still checks the served file against the committed export audit's hash; only the
    maintainer's checkout re-derives it."""
    manifest = json.loads(MANIFEST.read_bytes())
    return all((PROJECT / r['path']).exists() for r in input_refs(manifest)) and \
        (PROJECT / manifest['approval']['ownerDecisions']['path']).exists()


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    data = serialized_export()
    for out in OUTPUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    # The audit is a separate program: it reads these bytes and the pinned sources, and nothing of build().
    import audit_clinical_iesseeg_export
    return audit_clinical_iesseeg_export.write_audit()


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
