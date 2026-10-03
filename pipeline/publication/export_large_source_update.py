"""Release the 2026-10-03 large-source batch as aggregate-only JSON.

Two questions, two pairs of fixed classical CPU baselines, nothing shared between them:

- Dreem sleep staging. How far do an empirical training prior and a spectral
  ridge get at five-stage sleep staging against the publisher's consensus, in
  25 healthy sleepers (DOD-H) and in 55 people with obstructive sleep apnoea
  (DOD-O)? Two separate within-cohort experiments, never compared with each
  other.
- OpenBMI cross-session calibration. How much do 0, 10, 20 or 40 labelled
  trials from a person's second session help a decoder trained on their first,
  for 51 people and two fixed baselines? And for how many people did it not?

Its own publication boundary, as with every batch. The website inputs are the
two release JSONs. The independent audits, the Dreem supplementary audit, the
OpenBMI source aggregate and both release decisions are pinned by hash and
checked against those exact bytes, but never copied: they carry private
storage paths. What this export refuses:
- per-person values: the OpenBMI worst observed change, medians and 10th
  percentiles, by key, by fragment and by value; how many people declined is
  published, which people is not;
- record, file and participant identifiers, predictions, probabilities,
  features, thresholds, confusion matrices and private paths;
- a null turned into a number, an interval that does not hold its mean, a
  count that is not a whole number of people over the right denominator, and
  any page reading the numbers no longer support.

    python3 pipeline/publication/export_large_source_update.py
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path

from export_snapshot import approved, validate_public
from export_evidence_update import PER_PERSON_KEYS, pinned, require, rights, sha

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261003'
MANIFEST = REVIEW / 'large-source-release-manifest.json'
EXPORT_AUDIT = REVIEW / 'large-source-export-audit.json'
OUTPUTS = (PROJECT / 'site/src/data/large-source-update.json',
           PROJECT / 'site/public/data/large-source-update.json')

DREEM, OPENBMI = 'dreem-sleep-baselines', 'openbmi-cross-session-calibration'

# Per-person distributions, a decoder's internals, and the summaries this batch
# leaves out on purpose. Keys are refused by exact name and by fragment.
REFUSED_KEYS = PER_PERSON_KEYS | {'minimum', 'maximum', 'p10', 'p90', 'q1', 'q3', 'range', 'negative_count',
                                  'negative_fraction', 'per_class', 'private_audit', 'private_supplement'}
REFUSED_KEY_FRAGMENTS = ('threshold', 'prediction', 'probabilit', 'feature', 'private', 'range', 'participant_id',
                         'record_id', 'per_person', 'per_participant', 'per_record', 'per_night', 'minimum',
                         'maximum', 'median', 'quantile', 'percentile', 'worst', 'p10', 'confusion', 'brier',
                         'nll', 'ece_', 'epoch_micro', 'combined', 'pooled', 'cross_cohort', 'basename')
# Dreem record names are UUIDs; OpenBMI files are sessNN_subjNN and folders sN.
SOURCE_IDS = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                        r'|\bsess\d+|\bsubj\d+|\bs[1-9]\d?\b|\.h5\b|\.mat\b|\.npz\b', re.IGNORECASE)
# Path roots only: naming this operator's machines or volumes here would itself be the leak.
PRIVATE_TOKENS = re.compile(r'/(?:Volumes|Users|home|mnt|media|private|tmp|srv|root)/', re.IGNORECASE)
TOL = 1e-12

# ---------------------------------------------------------------------------- Dreem
STAGES = ('Wake', 'N1', 'N2', 'N3', 'REM')
COHORTS = {'DOD-H': 25, 'DOD-O': 55}           # people = nights, one night per person
FOLDS = 5
DREEM_ARMS = {
    'training_prior': {
        'label': 'Training prior',
        'description': "the training folds' stage frequencies, the same for every epoch; its prediction is their most "
                       'frequent stage, N2, for every epoch. A floor to beat, not a chance level',
    },
    'spectral_ridge': {
        'label': 'Spectral ridge',
        'description': 'standardised one-hot ridge regression (alpha 1) on 25 log-relative spectral values per epoch: '
                       'five bands from each of five EEG derivations',
    },
}
DREEM_METRICS = {'accuracy': (0.0, 1.0), 'balanced_accuracy': (0.0, 1.0), 'macro_f1': (0.0, 1.0),
                 'cohen_kappa': (-1.0, 1.0)}
STAGE_METRICS = {'recall': 'sensitivity', 'precision': 'precision', 'f1': 'f1'}
UNDEFINED = {  # release reason code -> what it means for one night
    'zero_truth_support': 'stage_absent',
    'zero_predicted_support': 'stage_never_predicted',
    'zero_2tp_fp_fn_denominator': 'stage_absent_and_never_predicted',
}
DREEM_AUDIT_VERDICT = 'pass_exact_sealed80_truth_prediction_metrics_and_bootstrap_recomputation'
DREEM_AUDIT_TRUE = ('all_packets_validated_before_truth', 'sealed_packet_truth_epoch_identity_exact',
                    'same_records_and_truth_support_across_paired_arms',
                    'per_record_metrics_recomputed_from_prediction_and_truth_arrays',
                    'participant_equal_fixed_bootstrap_recomputed', 'paired_fixed_bootstrap_recomputed',
                    'combined_descriptive_fixed_bootstrap_recomputed', 'epoch_micro_point_estimates_recomputed',
                    'truth_read_ledger_exact80_unique', 'all_compared_values_match_with_rtol_2e-14_atol_2e-15')
DREEM_AUDIT_FALSE = ('feature_files_opened', 'raw_eeg_opened', 'fit_tune_select_or_retry_performed',
                     'project_release_performed')
SUPPLEMENT_VERDICT = 'pass_full_truth_ledger_and_complete_candidate_projection'
SUPPLEMENT_TRUE = ('truth_ledger_exact_key_allowlist', 'every_truth_ledger_row_matches_frozen_truth_reference',
                   'every_truth_ledger_row_matches_stratum_and_fold', 'every_truth_ledger_row_matches_epoch_count',
                   'every_truth_ledger_row_matches_ordered_epoch_identity_digest',
                   'cross_arm_record_truth_stratum_and_fold_bindings_equal', 'candidate_exact_key_allowlist',
                   'candidate_participant_equal_projection_exact', 'candidate_epoch_micro_projection_exact',
                   'candidate_epoch_micro_uncertainty_fields_exact', 'candidate_paired_projection_exact',
                   'candidate_combined_descriptive_projection_exact')
SUPPLEMENT_FALSE = ('feature_prediction_and_raw_files_opened', 'bootstrap_rerun', 'fit_or_scoring_change',
                    'release_performed')
# What each cohort's consent and ethics statement rests on: a recorded quote from
# the paper, with its cohort. The export refuses to state either without it.
REQUIRED_QUOTES = {('DOD-H', 'ethics'): 'Committees of Protection of Persons',
                   ('DOD-O', 'consent'): 'informed written consent',
                   ('both', 'public_availability'): 'publicly-available'}

# ---------------------------------------------------------------------------- OpenBMI
BUDGETS = (0, 10, 20, 40)
OPENBMI_ARMS = {  # release key -> published id, label, description
    'trace_logcov': ('log-covariance-lda', 'Log-covariance + shrinkage LDA',
                     "each trial's channel covariance, regularised and divided by its trace, mapped by the matrix "
                     'logarithm; linear discriminant analysis with shrinkage'),
    'relative_psd': ('relative-psd-ridge', 'Relative PSD + standardized ridge',
                     "each channel's band power as a share of its 8–30 Hz power, on a log scale; standardised, then a "
                     'ridge classifier'),
}
OPENBMI_CELL_METRICS = ('balanced_accuracy', 'accuracy', 'macro_f1')
OPENBMI_METRIC_BLOCKS = ('cells', 'within_arm_budget_contrasts', 'between_arm_same_budget_contrasts',
                         'common_probability_subset_count', 'balanced_accuracy_defined_all_cells_participant_count')
OPENBMI_AUDIT_VERDICT = 'pass_independent_expanded_scientific_result_audit'
# Fields of the release that describe one person, refused by value as well as by key.
PER_PERSON_STATS = ('minimum', 'median', 'p10')


# ---------------------------------------------------------------------------- helpers
def close(a, b, label):
    require(isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < TOL,
            f'{label}: {a!r} does not equal {b!r}')


def when(stamp):
    return datetime.fromisoformat(stamp.replace('Z', '+00:00'))


def count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def bounded(mean, interval, label, lo_bound=0.0, hi_bound=1.0):
    """A published mean and its 95% interval: the interval holds the mean and stays in the metric's range."""
    require(isinstance(interval, list) and len(interval) == 2, f'{label}: no two-sided interval')
    lo, hi = interval
    require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (mean, lo, hi)),
            f'{label}: a mean or bound is not a finite number')
    require(lo_bound <= lo and hi <= hi_bound, f'{label}: the interval leaves the metric range')
    require(lo <= mean <= hi, f'{label}: the interval does not contain its mean')
    return [lo, hi]


def pinned_text(ref, label):
    raw = (PROJECT / ref['path']).read_bytes()
    digest = sha(raw)
    require(digest == ref['sha256'], f'{label}: {ref["path"]} is {digest[:12]}, pinned {ref["sha256"][:12]}')
    return raw.decode('utf-8')


def stated(text, phrase, label):
    """The release figure the pages print is the one the pinned handoff states."""
    require(phrase in text, f'{label}: the handoff does not state {phrase!r}')


# ---------------------------------------------------------------------------- Dreem
def dreem_summary(block, planned, bootstrap, label, lo_bound=0.0, hi_bound=1.0):
    """One participant-equal summary. Null stays null; a value needs nights that define it."""
    require(block['planned_record_count'] == planned, f'{label}: planned nights differ from the cohort')
    defined, missing, reasons = block['defined_record_count'], block['missing_record_count'], block['missing_reason_counts']
    require(count(defined) and count(missing) and defined + missing == planned, f'{label}: defined + missing nights '
            'is not the cohort')
    require(set(reasons) <= set(UNDEFINED) and all(count(n) and n > 0 for n in reasons.values())
            and sum(reasons.values()) == missing, f'{label}: undefined nights do not add up to their reasons')
    require(block['bootstrap_total_draws'] == bootstrap['draws'], f'{label}: another number of bootstrap draws')
    point, iv = block['point_estimate'], block['interval']
    if defined == 0:
        require(point is None, f'{label}: no night defines this value, yet it is not null (a null turned into a number)')
        require(iv is None and block['interval_undefined_reason'] == 'no_defined_records',
                f'{label}: an interval without a defined night')
        out = {'mean': None, 'interval_95': None}
    else:
        require(point is not None, f'{label}: defined nights but a null mean')
        if iv is None:
            require(block['interval_undefined_reason'] == 'insufficient_finite_bootstrap_draws'
                    and block['bootstrap_finite_draws'] < bootstrap['minimum_finite_draws'],
                    f'{label}: an interval is missing without its rule')
            bounded(point, [point, point], label, lo_bound, hi_bound)
            out = {'mean': point, 'interval_95': None, 'interval_undefined': 'fewer than 9,500 finite bootstrap draws'}
        else:
            require(block['interval_undefined_reason'] is None
                    and block['bootstrap_finite_draws'] >= bootstrap['minimum_finite_draws'],
                    f'{label}: an interval from too few finite bootstrap draws')
            out = {'mean': point, 'interval_95': bounded(point, iv, label, lo_bound, hi_bound)}
    out['nights_defined'] = defined
    if missing:
        out['nights_undefined'] = {UNDEFINED[r]: n for r, n in sorted(reasons.items())}
    return out


def consent_and_ethics(record):
    """Which statement each cohort has and which is missing, each resting on a recorded quote."""
    ce = record['consentEthics']
    require(ce['source'] in record['reviewBasis'], 'dreem: consent and ethics were read from an unlisted source')
    quotes = [q for h in record.get('decisionHistory', []) for q in h.get('quotes', [])]
    for (cohort, kind), phrase in REQUIRED_QUOTES.items():
        require(any(q['cohort'] == cohort and q['statement'] == kind and phrase in q['text'] and q['source'] == ce['source']
                    for q in quotes), f'dreem: the {kind} statement for {cohort} has no recorded source quote ("{phrase}")')
    out = {}
    for cohort in COHORTS:
        c = ce['cohorts'][cohort]
        entry = {}
        for kind, key in (('ethics', 'ethics_approval'), ('consent', 'informed_consent')):
            quoted = [q['text'] for q in quotes if q['cohort'] == cohort and q['statement'] == kind]
            if c[kind] is None:
                require(not quoted, f'dreem: {cohort} {kind} is quoted but recorded as missing')
                note = c.get(kind + 'Missing')
                require(bool(note), f'dreem: {cohort} has no {kind} statement and the record does not say so')
                entry[key] = {'stated': False, 'note': note}
            else:
                require(len(quoted) == 1, f'dreem: {cohort} {kind} is recorded without exactly one source quote')
                entry[key] = {'stated': True, 'statement': c[kind], 'quote': quoted[0]}
        entry['read_from'] = f'{ce["version"]}, {ce["section"]}, read {ce["readAt"]}'
        out[cohort] = entry
    return out, ce


def dreem_bindings(record, release, release_sha):
    """Every reviewed record names the next one, and the audits name the run the release reports."""
    protocol, protocol_sha = pinned(record['protocol'], 'dreem protocol')
    audit, audit_sha = pinned(record['numericalAudit'], 'dreem audit')
    supplement, supplement_sha = pinned(record['supplementaryAudit'], 'dreem supplementary audit')
    decision, _ = pinned(record['releaseDecision'], 'dreem release decision')
    scope, scope_sha = pinned(record['scopeReview'], 'dreem source scope review')
    deposit, deposit_sha = pinned(record['depositMetadata'], 'dreem deposit metadata')

    require(decision['release_sha256'] == release_sha, 'dreem: the release decision names other release bytes')
    require(decision['independent_numeric_audit_sha256'] == audit_sha
            and decision['supplementary_audit_sha256'] == supplement_sha,
            'dreem: the release decision names other audits')
    require(decision['handoff_sha256'] == record['handoff']['sha256'], 'dreem: the release decision names another handoff')
    require(decision['source_scope_review_sha256'] == scope_sha, 'dreem: the release decision names another scope review')
    require(decision['release_authorized'] is True and decision['raw_or_individual_release'] is False
            and decision['root_privacy_key_and_path_scan_pass'] is True, 'dreem: the release decision does not authorise '
            'an aggregate-only release')
    require(decision['created_at_utc'] == release['created_at_utc'], 'dreem: decision and release are not one act')

    prov = release['provenance']
    require(release['release_authorized'] is True and release['release_status'] == 'audited_aggregate_research_release',
            'dreem: the release is not an authorised audited release')
    require(prov['independent_result_audit_sha256'] == audit_sha and prov['supplementary_audit_sha256'] == supplement_sha,
            'dreem: the release names other audits')
    require(release['protocol_sha256'] == prov['protocol_sha256'] == protocol_sha == audit['bindings']['protocol_sha256'],
            'dreem: protocol identity differs between release, audit and pinned protocol')
    require(prov['numeric_conventions_sha256'] == audit['bindings']['numeric_conventions_sha256'],
            'dreem: numeric conventions differ between release and audit')
    require(prov['source_metadata_sha256'] == deposit_sha == scope['license_evidence']['sha256'],
            'dreem: the licence evidence differs between release, scope review and pinned metadata')

    require(audit['verdict'] == DREEM_AUDIT_VERDICT and audit['blocking_findings'] == [],
            'dreem: the independent audit did not pass')
    checks = audit['independent_checks']
    require(all(checks[k] is True for k in DREEM_AUDIT_TRUE) and all(checks[k] is False for k in DREEM_AUDIT_FALSE),
            'dreem: the independent audit did not pass every check')
    require(supplement['verdict'] == SUPPLEMENT_VERDICT and supplement['blocking_findings'] == [],
            'dreem: the supplementary audit did not pass')
    sc = supplement['checks']
    require(all(sc[k] is True for k in SUPPLEMENT_TRUE) and all(sc[k] is False for k in SUPPLEMENT_FALSE),
            'dreem: the supplementary audit did not pass every check')
    require(supplement['preserved_prior_audit']['project_report_sha256'] == audit_sha,
            'dreem: the supplement supplements another audit')
    for k in ('activation_sha256', 'activation_contract_sha256', 'production_completion_sha256'):
        require(supplement['bindings'][k] == audit['bindings'][k], 'dreem: the two audits checked different runs')
    require(when(audit['reviewed_at_utc']) < when(supplement['reviewed_at_utc']) < when(release['created_at_utc']),
            'dreem: an audit postdates the release it should precede')
    return protocol, audit, supplement, scope, deposit


def dreem(record):
    release, release_sha = pinned(record['release'], 'dreem release')
    handoff = pinned_text(record['handoff'], 'dreem handoff')
    protocol, audit, supplement, scope, deposit = dreem_bindings(record, release, release_sha)
    units, _ = pinned(record['unitStatus']['evidence'], 'dreem unit evidence')
    consent, ce = consent_and_ethics(record)

    require(release['foundation_model_comparison'] is False and release['lora_or_peft_evaluation'] is False
            and release['model_family'] == 'classical_cpu_baselines', 'dreem: not the two classical baselines')
    design = release['evaluation_design']
    bootstrap = design['bootstrap']
    cov = audit['coverage']

    # Cohorts, records and jobs, from four places that must agree.
    people = {c: s['records'] for c, s in design['strata'].items()}
    require(people == COHORTS == cov['strata'], 'dreem: the cohort is not DOD-H 25 and DOD-O 55')
    total = sum(COHORTS.values())
    ra = design['source_record_accounting']
    require(total == release['record_count'] == cov['records_per_arm'] == supplement['coverage']['records']
            == ra['evaluated'] == ra['archive_records'] - ra['publisher_declared_no_consensus_exclusion'] == 80
            and ra['archive_records'] == 81 and ra['publisher_declared_no_consensus_exclusion'] == 1,
            'dreem: the 81 archive records are not 80 evaluated plus 1 publisher exclusion')
    inv = protocol['cohort_authority']['inventory']
    require(inv['consensus_total'] == total and inv['archive_total'] == ra['archive_records'],
            'dreem: the protocol inventory differs')
    experiments = {e['stratum']: e for e in protocol['experiment_separation']['experiments']}
    require({c: e['record_count'] for c, e in experiments.items()} == COHORTS
            and all(e['fold_count'] == FOLDS for e in experiments.values())
            and design['folds_per_stratum'] == cov['folds_per_stratum'] == supplement['coverage']['folds_per_stratum'] == FOLDS,
            'dreem: not five folds within each cohort')
    jobs = len(COHORTS) * FOLDS * len(DREEM_ARMS)
    require(release['prediction_job_count'] == cov['prediction_jobs'] == cov['prediction_packets']
            == supplement['coverage']['jobs'] == protocol['experiment_separation']['planned_prediction_jobs'] == jobs,
            'dreem: jobs are not 2 cohorts x 5 folds x 2 arms, each with its audited packet')
    require(cov['arms'] == list(DREEM_ARMS) and set(release['strata']) == set(DREEM_ARMS), 'dreem: other arms')

    ep = design['technical_epoch_accounting']
    require(all(count(ep[k]) for k in ('total', 'unscored', 'zero_or_invalid_channel_scale', 'eligible'))
            and ep['total'] - ep['unscored'] - ep['zero_or_invalid_channel_scale'] == ep['eligible']
            == sum(s['eligible_epochs'] for s in design['strata'].values()),
            'dreem: the epoch accounting does not add up')

    # The fixed method, as the pinned protocol froze it.
    feats = protocol['features']
    require(design['class_order'] == list(STAGES) == protocol['consensus_truth_contract']['classes_in_order'],
            'dreem: another stage order')
    require(design['ordered_derivations'] == protocol['input_contract']['ordered_derivations']
            and len(design['ordered_derivations']) * len(feats['bands_hz']) == feats['feature_count'] == 25,
            'dreem: not 25 values from five derivations and five bands')
    require(design['sampling_rate_hz'] == protocol['input_contract']['sampling_rate_hz'] == 250
            and design['epoch_seconds'] == protocol['input_contract']['epoch_seconds'] == 30, 'dreem: another signal')
    require(protocol['models']['spectral_ridge']['alpha'] == 1.0
            and protocol['models']['spectral_ridge']['class_weights_balancing_or_subsampling'] is False,
            'dreem: the ridge is not the fixed alpha-1 unbalanced fit')
    u = protocol['uncertainty']
    require(bootstrap['draws'] == u['draws'] == 10000 and bootstrap['seed'] == u['seed']
            and bootstrap['minimum_finite_draws'] == u['minimum_finite_draws_for_interval'] == 9500
            and bootstrap['generator'] == 'PCG64' and bootstrap['conditional_on_fixed_cv_predictions'] is True,
            'dreem: another bootstrap')

    # Units: the disagreement the pages state, and the hold that follows from it.
    require(units['status'].startswith('unresolved') and units['actual_group_metadata']['signals/eeg']['unit']
            == record['unitStatus']['storedMetadataUnit'] == 'mV' and 'uV' in units['conflicting_upstream']['evidence']
            and record['unitStatus']['status'] == 'unresolved', 'dreem: the unit disagreement is not as recorded')

    audited = audit['audited_paired_spectral_ridge_minus_training_prior']
    cohorts = {}
    for c, n in COHORTS.items():
        strata = {arm: release['strata'][arm][c] for arm in DREEM_ARMS}
        # Cohort-level stage support: eligible epochs per consensus stage, the same for both arms.
        supports = []
        for arm, s in strata.items():
            em = s['epoch_micro']
            require([p['class'] for p in em['per_class']] == list(range(len(STAGES))), f'dreem/{c}/{arm}: stage order')
            supports.append([p['support'] for p in em['per_class']])
            require(em['epoch_count'] == design['strata'][c]['eligible_epochs'], f'dreem/{c}/{arm}: epoch count')
        require(supports[0] == supports[1] and all(count(k) and k >= 0 for k in supports[0])
                and sum(supports[0]) == design['strata'][c]['eligible_epochs'],
                f'dreem/{c}: stage support does not add up to the eligible epochs')

        arms = {}
        for arm, shape in DREEM_ARMS.items():
            pe = strata[arm]['participant_equal']
            arms[arm] = {'label': shape['label'], 'description': shape['description']}
            for metric, (lo_b, hi_b) in DREEM_METRICS.items():
                arms[arm][metric] = dreem_summary(pe[metric], n, bootstrap, f'dreem/{c}/{arm}/{metric}', lo_b, hi_b)
                require(arms[arm][metric]['nights_defined'] == n, f'dreem/{c}/{arm}/{metric}: not defined for every night')

        # The prior predicts N2 for every epoch: its N2 recall is one, no other stage is ever predicted,
        # its accuracy is each night's N2 share and its kappa is zero. Its balanced accuracy is one over the
        # number of stages each night contains, so at least one fifth: not a chance level.
        prior = strata['training_prior']['participant_equal']
        n2 = STAGES.index('N2')
        require(prior[f'class_{n2}_sensitivity']['point_estimate'] == 1.0
                and all(prior[f'class_{i}_precision']['defined_record_count'] == 0 for i in range(len(STAGES)) if i != n2),
                f'dreem/{c}: the training prior does not predict N2 for every epoch')
        close(prior['accuracy']['point_estimate'], prior[f'class_{n2}_precision']['point_estimate'],
              f'dreem/{c}: prior accuracy and its N2 share')
        require(prior['cohen_kappa']['point_estimate'] == 0.0 and prior['balanced_accuracy']['point_estimate'] >= 0.2 - TOL,
                f'dreem/{c}: the training prior is not the constant-N2 floor')

        ridge = strata['spectral_ridge']['participant_equal']
        per_stage, never = [], []
        for i, stage in enumerate(STAGES):
            entry = {'stage': stage, 'support_epochs': supports[0][i]}
            for name, key in STAGE_METRICS.items():
                entry[name] = dreem_summary(ridge[f'class_{i}_{key}'], n, bootstrap, f'dreem/{c}/ridge/{stage}/{name}')
            if ridge[f'class_{i}_precision']['missing_reason_counts'] == {'zero_predicted_support': n}:
                never.append(stage)
                require(entry['recall']['mean'] == 0.0, f'dreem/{c}: a never-predicted stage with nonzero recall')
            per_stage.append(entry)
        arms['spectral_ridge']['per_stage'] = per_stage
        arms['spectral_ridge']['stages_never_predicted'] = never

        # Paired: ridge minus prior on the same nights. Every metric equals the independent audit's value
        # exactly, and the mean of the differences equals the difference of the means.
        paired = release['paired'][c]
        require(paired['difference'] == 'spectral_ridge_minus_training_prior' and paired['stratum'] == c,
                f'dreem/{c}: another paired comparison')
        require(set(paired['metrics']) == set(audited[c]), f'dreem/{c}: the audit checked other paired metrics')
        for metric, block in paired['metrics'].items():
            require(block['point_estimate'] == audited[c][metric]['point']
                    and block['interval'] == audited[c][metric]['interval_95'],
                    f'dreem/{c}/{metric}: the paired value differs from the independent audit')
        for metric in DREEM_METRICS:
            block = paired['metrics'][metric]
            require(block['defined_record_count'] == n, f'dreem/{c}/{metric}: paired nights are not the cohort')
            close(block['point_estimate'], ridge[metric]['point_estimate'] - prior[metric]['point_estimate'],
                  f'dreem/{c}/{metric}: the paired mean')
        ba = paired['metrics']['balanced_accuracy']
        gain = dreem_summary(ba, n, bootstrap, f'dreem/{c}/paired balanced accuracy', -1.0, 1.0)
        excludes = gain['interval_95'][0] > 0
        require(excludes, f'dreem/{c}: the paired balanced-accuracy interval no longer excludes zero; the page calls it '
                          'a gain and must be reviewed')

        exp = experiments[c]
        cohorts[c] = {
            'population': ce['cohorts'][c]['population'],
            'recorded_at': ce['cohorts'][c]['recordedAt'],
            'people': n, 'nights': n, 'eligible_epochs': design['strata'][c]['eligible_epochs'],
            'folds': FOLDS, 'nights_tested_per_fold': exp['test_records_per_fold'],
            'nights_trained_per_fold': exp['training_records_per_fold'],
            'stage_support_epochs': dict(zip(STAGES, supports[0])),
            'arms': arms,
            'paired_balanced_accuracy': {
                'comparison': 'spectral ridge minus training prior, the same nights',
                'mean': gain['mean'], 'interval_95': gain['interval_95'], 'nights': gain['nights_defined'],
                'interval_excludes_zero': excludes,
            },
            'consent_and_ethics': consent[c],
        }

    # The reading the pages print, held to the numbers.
    for c, entry in cohorts.items():
        r = entry['arms']['spectral_ridge']
        require(r['accuracy']['mean'] > r['balanced_accuracy']['mean'] and 'N1' in r['stages_never_predicted'],
                f'dreem/{c}: the reading (accuracy above balanced accuracy; N1 never predicted) no longer holds')

    attribution = release['attribution']
    require(attribution['dataset_record'] == record['source'] == deposit['links']['self_html'] == scope['source_record'],
            'dreem: another deposit')
    meta = deposit['metadata']
    require(meta['license']['id'] == 'mit-license' and meta['access_right'] == 'open'
            and attribution['observed_deposit_license'] == scope['observed_deposit_license'] == record['license'] == 'MIT'
            and scope['observed_access_right'] == 'open', 'dreem: the deposit does not declare MIT and open access')
    require(meta['doi'] == attribution['dataset_doi'] == scope['source_doi'] and meta['doi'] in record['attribution']
            and meta['doi'] in record['version'], 'dreem: the deposit DOI differs')
    paper_doi = attribution['paper_url'].removeprefix('https://doi.org/')
    require(attribution['paper_url'] == scope['paper'] and paper_doi in record['attribution']
            and attribution['paper_url'] in record['reviewBasis'], 'dreem: the paper differs')
    require(all(a in record['attribution'] for a in attribution['paper_authors'])
            and attribution['paper_authors'] == scope['authors'], 'dreem: the attribution omits an author')
    require(attribution['upstream_revision'] == scope['official_code_revision'] and attribution['upstream_revision']
            in record['attribution'], 'dreem: the repository revision differs')

    # Last: the figures the pages print are the ones the pinned handoff states.
    pct = lambda b: f'{100 * b["mean"]:.2f}% ({100 * b["interval_95"][0]:.2f}–{100 * b["interval_95"][1]:.2f})'
    for c, entry in cohorts.items():
        for arm in DREEM_ARMS:
            a = entry['arms'][arm]
            stated(handoff, f'| {c} ({entry["people"]}) | {a["label"]} | {pct(a["accuracy"])} | '
                            f'{pct(a["balanced_accuracy"])} | {pct(a["macro_f1"])} |', f'dreem/{c}/{arm}')
        g = entry['paired_balanced_accuracy']
        m, lo, hi = (f'{100 * v:.2f}' for v in (g['mean'], *g['interval_95']))
        require(re.search(rf'{re.escape(m)} (?:percentage )?points \({re.escape(lo)}–{re.escape(hi)}\)', handoff),
                f'dreem/{c}: the handoff does not state the paired gain')
    for k in ('total', 'eligible'):
        stated(handoff, f'{ep[k]:,}', f'dreem epochs {k}')

    result = {
        'id': DREEM,
        'title': 'Sleep staging: simple CPU baselines',
        'question': 'how far two fixed classical baselines get at five-stage sleep staging against the publisher\'s '
                    'consensus, in healthy sleepers and in people with obstructive sleep apnoea, as two separate '
                    'experiments',
        'source_release_id': release['release_id'],
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'stages': list(STAGES), 'epoch_seconds': design['epoch_seconds'],
        'metric': 'balanced_accuracy',
        'weighting': 'participant-equal: each night counts once, however long; accuracy, balanced accuracy and macro '
                     'F1 use the same nights',
        'prior_balanced_accuracy_note': 'The training prior always predicts N2. Its balanced accuracy is one over the '
                                        'number of stages a night contains, so it sits slightly above one fifth when a '
                                        'night lacks a stage. It is the floor this baseline sets, not a chance level.',
        'separate_experiments': 'DOD-H and DOD-O have separate models, folds and intervals. They were recorded at '
                                'different centres with different equipment; nothing here compares them.',
        'cohorts': cohorts,
        'record_accounting': {'archive_records': ra['archive_records'],
                              'excluded_before_scoring': ra['publisher_declared_no_consensus_exclusion'],
                              'exclusion_reason': 'the publisher declares the record has no consensus scoring',
                              'evaluated': ra['evaluated']},
        'epoch_accounting': {'total': ep['total'], 'unscored': ep['unscored'],
                             'zero_or_invalid_channel_scale': ep['zero_or_invalid_channel_scale'],
                             'eligible': ep['eligible']},
        'jobs': {'trained': jobs, 'composition': '2 cohorts × 5 folds × 2 arms', 'failed': 0},
        'method': {
            'target': "the publisher's stored consensus hypnogram; individual scorers' votes were not reconstructed",
            'signal': 'five EEG derivations (' + ', '.join(d.replace('_', '-') for d in design['ordered_derivations'])
                      + ') at 250 Hz, 30-second epochs',
            'spectra': 'each epoch and channel divided by its own largest absolute value, then Welch spectra; band power in '
                       'delta, theta, alpha, sigma and beta as a log share of 0.5–30 Hz power: 25 values per epoch',
            'arms': {arm: shape['description'] for arm, shape in DREEM_ARMS.items()},
            'folds': 'five folds within each cohort, assigned by a hash of each record before any outcome was seen; '
                     'every night is tested once per arm by a model fitted on the other four folds of its own cohort',
            'selection': 'none: no tuning, held-out calibration, oversampling, class balancing or outcome-selected '
                         'retry; natural stage prevalence kept',
            'balanced_accuracy': 'per night, the mean recall over the stages that night contains; then the mean over '
                                 'nights',
            'macro_f1': 'per night, the mean F1 over the stages that night contains or the model predicts; then the '
                        'mean over nights',
        },
        'uncertainty': {
            'kind': 'pointwise 95% whole-night bootstrap within each cohort',
            'draws': bootstrap['draws'], 'generator': bootstrap['generator'], 'seed': bootstrap['seed'],
            'finite_draws_required': bootstrap['minimum_finite_draws'],
            'paired': 'the same draws for both arms and every metric',
            'conditional_on': 'the fixed cross-validation predictions: refitting and fold-assignment uncertainty are '
                              'not included, and there is no multiple-comparison adjustment',
        },
        'units': {
            'stored_metadata': record['unitStatus']['storedMetadataUnit'],
            'upstream_converter': record['unitStatus']['upstreamConverterUnit'],
            'status': 'unresolved',
            'consequence': 'the two baselines divide out a positive gain per epoch and channel, so they do not depend '
                           'on the unit; models that need absolute amplitude are held (see holds)',
        },
        'reading': 'In both cohorts the spectral ridge\'s balanced accuracy is well above the training prior\'s, with '
                   'a paired interval that excludes zero. Its ordinary accuracy runs well above its balanced accuracy '
                   'because the stages are imbalanced, and it never predicts N1 in either cohort.',
        'limitations': [
            'Two fixed classical baselines on CPU. No neural network, foundation model or fine-tuning (LoRA/PEFT) was '
            'run, and nothing here ranks such models.',
            'DOD-H and DOD-O are separate experiments with separate models, recorded at different centres with '
            'different equipment. They are not a controlled comparison of health status, and nothing here measures '
            'transfer between them.',
            "The target is the publisher's stored consensus; individual scorers' votes were not reconstructed. No "
            'human-expert equivalence, diagnostic or clinical claim.',
            'Physical units are unresolved: the stored metadata says millivolts while the upstream converter treats '
            'the arrays as microvolts. The gain-normalised relative spectra do not depend on a positive gain, but '
            'nothing establishes calibration, reference, clipping or filter equivalence.',
            'Probabilities are uncalibrated: no calibration, confidence or abstention claim.',
            'Intervals are pointwise, conditional on the fixed cross-validation predictions, and not adjusted for '
            'multiple comparisons.',
            "Balanced accuracy and macro F1 average only the stages present (or predicted) in a night, so the prior's "
            'balanced accuracy can sit slightly above one fifth; it is not a chance level.',
            'Natural stage prevalence; no class balancing or tuning. Not comparable with papers that use other '
            'channels, cohorts, preprocessing or splits.',
        ],
        'independent_audit': {
            'status': 'pass', 'nights': cov['records_per_arm'], 'jobs': cov['prediction_jobs'],
            'checked': 'every prediction packet and truth record; every night\'s metrics and every bootstrap summary '
                       'recomputed and matched within a relative tolerance of 2e-14',
            'supplement': 'pass: the truth ledger and the complete projection into the release',
        },
        'credits': {
            'paper': attribution['paper_url'], 'preprint': 'https://arxiv.org/abs/1911.03221',
            'deposit': attribution['dataset_record'], 'deposit_doi': attribution['dataset_doi'],
            'repository': attribution['official_repository'], 'repository_revision': attribution['upstream_revision'],
        },
        'rights': {**rights(record), 'licenseScope': record['licenseScope']},
    }
    no_chance_label(result)
    return result


def no_chance_label(result):
    """The prior's balanced accuracy is a floor, not a chance line: nothing may call it one."""
    def walk(v, trail):
        if isinstance(v, dict):
            for k, x in v.items():
                require('chance' not in k.lower(), f'dreem: a chance field at {trail}.{k}')
                walk(x, f'{trail}.{k}')
        elif isinstance(v, list):
            for i, x in enumerate(v):
                walk(x, f'{trail}[{i}]')
        elif isinstance(v, str):
            for sentence in re.split(r'(?<=[.;])\s+', v):
                require('chance' not in sentence.lower() or re.search(r'\bnot\b', sentence),
                        f'dreem: {trail} calls something a chance level')
    walk(result, '$')


# ---------------------------------------------------------------------------- OpenBMI
def declines(x, people, label):
    """How many of the cohort fell at all, and by five points or more: whole people over the whole cohort."""
    n = x['common_defined_count']
    require(n == people, f'{label}: the denominator is {n}, not the {people} people')
    k, k5 = x['negative_count'], x['balanced_accuracy_loss_at_least_0_05_count']
    for c_, f_, what in ((k, x['negative_fraction'], 'any decline'),
                         (k5, x['balanced_accuracy_loss_at_least_0_05_fraction'], 'a decline of 5 points')):
        require(count(c_) and 0 <= c_ <= n, f'{label}: {what} is not a whole count of people')
        close(f_, c_ / n, f'{label}: the share with {what} is not the count over {n}')
    require(k5 <= k, f'{label}: more people lost five points than lost any')
    return k, k5


def openbmi(record):
    release, release_sha = pinned(record['release'], 'openbmi release')
    handoff = pinned_text(record['handoff'], 'openbmi handoff')
    aggregate, aggregate_sha = pinned(record['sourceAggregate'], 'openbmi source aggregate')
    audit, audit_sha = pinned(record['numericalAudit'], 'openbmi audit')
    decision, _ = pinned(record['releaseDecision'], 'openbmi release decision')
    datacite, _ = pinned(record['licenseRecord'], 'openbmi licence record')
    evidence, _ = pinned(record['consentRecord'], 'openbmi consent record')

    # Chain: decision -> release bytes, aggregate, audit, handoff; audit -> aggregate; release -> both.
    require(decision['website_release']['sha256'] == release_sha, 'openbmi: the release decision names other release bytes')
    require(decision['aggregate_sha256'] == aggregate_sha and decision['audit_sha256'] == audit_sha,
            'openbmi: the release decision names another aggregate or audit')
    require(decision['handoff']['sha256'] == record['handoff']['sha256'], 'openbmi: the release decision names another handoff')
    require(decision['release_authorized'] is True and decision['all_408_cells_independently_audited'] is True
            and decision['scope'].startswith('aggregate_only'), 'openbmi: the release decision does not authorise it')
    require(audit['verdict'] == OPENBMI_AUDIT_VERDICT, 'openbmi: the independent audit did not pass')
    require(audit['expanded_aggregate_sha256'] == aggregate_sha, 'openbmi: the audit checked a different aggregate')
    require(audit['models_loaded_or_refitted'] is False and audit['private_paths_or_participant_values_disclosed'] is False
            and audit['statistical_release_thresholds_met'] is True and audit['old40_independent_cells_and_aggregate_parity']
            is True and audit['all_new_eligible_included'] is True and audit['explicit_failed_predictions'] == 0
            and all(audit['thresholds'][k] is True for k in ('eligible_participants_met',
                                                               'balanced_accuracy_defined_participants_met')),
            'openbmi: the independent audit did not pass every check')
    prov = release['provenance']
    require(prov['source_aggregate_sha256'] == aggregate_sha and prov['independent_result_audit_sha256'] == audit_sha,
            'openbmi: the release names another aggregate or audit')
    require(prov['scoring_activation_sha256'] == aggregate['scoring_activation_sha256'] == audit['scoring_activation_sha256']
            and prov['expanded_aggregation_plan_content_sha256'] == aggregate['expanded_aggregation_plan_content_sha256']
            == audit['expanded_plan_content_sha256'], 'openbmi: scoring run or plan differs between release, aggregate '
            'and audit')
    err = audit['numeric_comparison']['maximum_absolute_difference']
    require(prov['maximum_independent_numeric_error'] == err and 0 <= err <= TOL,
            'openbmi: the audit\'s recomputation did not match')
    require(when(audit['audited_at_utc']) <= when(decision['decided_at_utc']) == when(release['created_at_utc']),
            'openbmi: the audit postdates the release')
    # The aggregate is the sealed pre-audit candidate; its stale flags are expected, and the
    # audit and decision above are what release it.
    require(aggregate['release_authorized'] is False and aggregate['result_status'] == 'awaiting_independent_result_audit'
            and aggregate['independent_result_audit_required'] is True,
            'openbmi: the source aggregate is not the sealed pre-audit candidate')
    require(release['publication']['aggregate_release_approved'] is True
            and release['publication']['raw_EEG_or_participant_outputs_included'] is False,
            'openbmi: the release is not an approved aggregate')

    # Every published figure is the audited aggregate's, value for value.
    m = release['metrics']
    require(set(m) == set(OPENBMI_METRIC_BLOCKS), 'openbmi: the release has other metric blocks')
    for k in OPENBMI_METRIC_BLOCKS:
        require(m[k] == aggregate[k], f'openbmi: release {k} differs from the audited aggregate')

    # Cohort and job accounting.
    ds, p, cr = release['dataset'], release['protocol'], release['cohort_relationship']
    people = aggregate['participant_count']
    require(people == audit['participant_count'] == decision['participant_count'] == ds['eligible_participants']
            == m['balanced_accuracy_defined_all_cells_participant_count'] == audit['balanced_accuracy_defined_all_cells_participant_count']
            == m['common_probability_subset_count'] == 51, 'openbmi: the evaluated cohort is not 51 people')
    old, new = aggregate['old_participant_count'], aggregate['new_participant_count']
    require(old == audit['old_participant_count'] == cr['original_participants_reused'] == 40
            and new == audit['new_participant_count'] == cr['new_participants'] == 11 and old + new == people,
            'openbmi: 40 original plus 11 added is not the cohort')
    require(cr['independent_replication'] is False and cr['original_observations_unchanged'] is True
            and aggregate['all_original40_preserved'] is True and aggregate['identity_sets_disjoint'] is True,
            'openbmi: the expanded cohort is not the original 40 unchanged plus disjoint additions')
    require(ds['all_acquisition_identities'] == ds['engineering_excluded'] + ds['scientific_holds'] + people == 54
            and ds['engineering_excluded'] == 1 and ds['scientific_holds'] == 2,
            'openbmi: 54 identities are not 1 exclusion + 2 holds + 51 evaluated')
    require(ds['benchmark_candidate_pool'] == ds['available_candidate_pairs_audited'] == people + ds['scientific_holds']
            and ds['pending_acquisition'] == 0, 'openbmi: the 53 candidates are not all adjudicated')
    budgets = p['target_adaptation_budgets']
    require(budgets == list(BUDGETS), f'openbmi: the budgets are {budgets}, not {list(BUDGETS)}')
    for arm in OPENBMI_ARMS:
        require(list(m['cells'][arm]) == [str(b) for b in BUDGETS]
                and list(m['within_arm_budget_contrasts'][arm]) == [f'{b}_minus_0' for b in BUDGETS[1:]],
                f'openbmi/{arm}: cells or contrasts at other budgets')
    require(list(m['between_arm_same_budget_contrasts']) == [str(b) for b in BUDGETS] and set(m['cells']) == set(OPENBMI_ARMS),
            'openbmi: other arms or budgets')
    test = p['fixed_target_test_trials']
    trials = p['unique_heldout_trials']
    require(trials == people * test == 3060, 'openbmi: held-out trials are not 51 people x 60')
    require(max(BUDGETS) + test <= p['source_fit_trials'] + p['source_probability_calibration_trials'] == 100,
            'openbmi: calibration and test trials of session 2 would overlap')
    jobs = p['trained_prediction_jobs']
    require(jobs == people * len(OPENBMI_ARMS) * len(BUDGETS) == audit['planned_jobs'] == audit['successful_predictions']
            == 408 and p['failed_prediction_jobs'] == 0, 'openbmi: jobs are not 51 x 2 arms x 4 budgets, all completed')
    require(p['new_prediction_jobs'] == new * 8 and p['original_prediction_jobs_preserved'] == old * 8,
            'openbmi: preserved and new jobs do not split by cohort')
    require(p['hyperparameter_search'] is False and p['target_balance_selects_cohort'] is False
            and p['cohort_changed_after_scores'] is False and aggregate['score_driven_retry'] is False
            and aggregate['cohort_fixed_before_truth'] is True, 'openbmi: a selection the method rules out')
    require(p['bootstrap_draws'] == aggregate['bootstrap']['draws'] == 10000 and p['bootstrap_seed']
            == aggregate['bootstrap']['seed'] and aggregate['bootstrap'] == audit['bootstrap']
            and aggregate['bootstrap']['same_draws_all_arms_budgets'] is True, 'openbmi: another bootstrap')

    # Cells.
    arms, ba_mean, secret = [], {}, []
    for arm, (pid, label, desc) in OPENBMI_ARMS.items():
        require(release['model_labels'][arm] == label, f'openbmi/{arm}: another model label')
        by_budget = []
        for b in BUDGETS:
            cell = m['cells'][arm][str(b)]
            require(cell['prediction_failure_count'] == 0, f'openbmi/{arm}/{b}: a failed condition')
            entry = {'target_trials': b}
            for metric in OPENBMI_CELL_METRICS:
                c_ = cell[metric]
                require(c_['defined_count'] == people and c_['missing_count'] == 0,
                        f'openbmi/{arm}/{b}/{metric}: not defined for every person')
                entry[metric] = {'mean': c_['equal_person_mean'],
                                 'interval_95': bounded(c_['equal_person_mean'], c_['bootstrap_percentile_95'],
                                                        f'openbmi/{arm}/{b}/{metric}')}
            # Every person has the same 60 test trials, so mean accuracy is whole trials over 3,060.
            correct = entry['accuracy']['mean'] * trials
            require(abs(correct - round(correct)) < 1e-6, f'openbmi/{arm}/{b}: accuracy is not a whole count of trials')
            entry['people'] = people
            ba_mean[(arm, b)] = entry['balanced_accuracy']['mean']
            by_budget.append(entry)

        gains = []
        for b in BUDGETS[1:]:
            x = m['within_arm_budget_contrasts'][arm][f'{b}_minus_0']['balanced_accuracy']
            label_ = f'openbmi/{arm}/{b} vs 0'
            close(x['mean'], ba_mean[(arm, b)] - ba_mean[(arm, 0)], f'{label_}: the paired mean')
            iv = bounded(x['mean'], x['bootstrap_percentile_95'], label_, -1.0, 1.0)
            k, k5 = declines(x, people, label_)
            gains.append({'target_trials': b, 'comparison': f'{b} minus 0 labelled session-2 trials, the same people '
                                                            'and test trials',
                          'balanced_accuracy_change': {'mean': x['mean'], 'interval_95': iv},
                          'interval_excludes_zero': iv[0] > 0 or iv[1] < 0,
                          'people': people, 'people_with_any_decline': k, 'people_with_decline_of_5_points_or_more': k5})
        arms.append({'id': pid, 'label': label, 'description': desc, 'by_budget': by_budget, 'calibration_gain': gains})

    for contrasts in (*m['within_arm_budget_contrasts'].values(), {str(b): v['metrics'] for b, v in
                                                                   m['between_arm_same_budget_contrasts'].items()}):
        for block in contrasts.values():
            for stats in block.values():
                secret += [stats[k] for k in PER_PERSON_STATS if stats.get(k) is not None]

    between = []
    for b in BUDGETS:
        y = m['between_arm_same_budget_contrasts'][str(b)]
        require(y['direction'] == 'relative_psd_minus_trace_logcov', f'openbmi/{b}: another between-arm direction')
        x = y['metrics']['balanced_accuracy']
        label_ = f'openbmi/{b}: relative PSD minus log-covariance'
        close(x['mean'], ba_mean[('relative_psd', b)] - ba_mean[('trace_logcov', b)], f'{label_}: the paired mean')
        iv = bounded(x['mean'], x['bootstrap_percentile_95'], label_, -1.0, 1.0)
        k, k5 = declines(x, people, label_)
        between.append({'target_trials': b, 'comparison': 'relative PSD minus log-covariance, the same people and test '
                                                          'trials',
                        'balanced_accuracy_difference': {'mean': x['mean'], 'interval_95': iv},
                        'interval_excludes_zero': iv[0] > 0 or iv[1] < 0, 'people': people,
                        'people_lower_with_relative_psd': k, 'people_lower_by_5_points_or_more': k5})

    # The readings the pages print. Log-covariance: 40 trials help on average, interval above zero.
    # Relative PSD: the interval includes zero, so the pages say the gain is not established.
    lc = next(g for g in arms[0]['calibration_gain'] if g['target_trials'] == 40)
    ps = next(g for g in arms[1]['calibration_gain'] if g['target_trials'] == 40)
    lo, hi = lc['balanced_accuracy_change']['interval_95']
    require(lo > 0, 'openbmi: the log-covariance 40-versus-0 interval no longer excludes zero; the page wording must '
                    'be reviewed')
    lo, hi = ps['balanced_accuracy_change']['interval_95']
    require(lo < 0 < hi, 'openbmi: the relative-PSD 40-versus-0 interval no longer includes zero; the page wording '
                         '("not established") must be reviewed')
    require(lc['people_with_any_decline'] > 0 and ps['people_with_any_decline'] > 0,
            'openbmi: the reading that some people declined no longer holds')

    # Rights.
    attrs = datacite.get('data', {}).get('attributes', datacite)
    require(attrs['doi'] == record['source'].removeprefix('https://doi.org/') == release['dataset']['doi']
            and release['dataset']['source_url'] == record['source'], 'openbmi: another dataset DOI')
    require(any(r.get('rightsIdentifier') == 'cc0-1.0' for r in attrs['rightsList'])
            and record['license'] == ds['recorded_license'] == 'CC0-1.0', 'openbmi: the DataCite record is not CC0')
    require(all(c_['givenName'] in record['attribution'] and c_['familyName'] in record['attribution']
                for c_ in attrs['creators']), 'openbmi: the attribution omits a creator')
    require(any(r['relatedIdentifier'] in record['attribution'] and r['relationType'] == 'IsCitedBy'
                for r in attrs['relatedIdentifiers']), 'openbmi: the attribution omits the paper')
    require(evidence['key'] == 'gigadb:100542' and evidence['licence']['confirmed'] is True
            and evidence['consent_ethics']['status'] == 'stated', 'openbmi: the consent record does not state consent')
    for phrase in ('Korea University Institutional Review Board', '1040548-KUIRB-16-159-A-2', 'written informed consent'):
        require(phrase in evidence['consent_ethics']['evidence'] and phrase in record['privacyReview'],
                f'openbmi: the consent record and the review disagree on "{phrase}"')

    # Last: the figures the pages print are the ones the pinned handoff states.
    for a in arms:
        for e in a['by_budget']:
            b_ = e['balanced_accuracy']
            stated(handoff, f'{100 * b_["mean"]:.2f}% ({100 * b_["interval_95"][0]:.2f}–{100 * b_["interval_95"][1]:.2f})',
                   f'openbmi/{a["id"]}/{e["target_trials"]}')
    for g in (lc, ps):
        d = g['balanced_accuracy_change']
        stated(handoff, f'{100 * d["mean"]:+.2f} pp', 'openbmi 40 vs 0 mean')
        stated(handoff, f'{100 * d["interval_95"][0]:+.2f} to {100 * d["interval_95"][1]:+.2f} pp', 'openbmi 40 vs 0 interval')
        for k in (g['people_with_any_decline'], g['people_with_decline_of_5_points_or_more']):
            stated(handoff, f'{k}/{people} ({100 * k / people:.1f}%)', 'openbmi 40 vs 0 declines')
    stated(handoff, f'{people} evaluated participants, {trials:,} unique held-out trials, and {jobs} completed '
                    'prediction jobs', 'openbmi cohort')
    stated(handoff, f'{ds["engineering_excluded"]} engineering exclusion + {ds["scientific_holds"]} whole-pair numerical '
                    f'input-quality holds + {people} evaluated', 'openbmi accounting')

    result = {
        'id': OPENBMI,
        'title': release['title'],
        'question': 'how much do labelled trials from a person\'s second session help a decoder trained on their '
                    'first, and for how many people did they not',
        'cohort_version': release['cohort_version'],
        'model_family': 'classical', 'foundation_model': False, 'fine_tuning': False,
        'classes': 2, 'class_names': ['left hand', 'right hand'], 'chance_level': 0.5,
        'metric': 'balanced_accuracy',
        'generalization': 'the same person, a later session: trained on session 1, tested on session 2. Not '
                          'generalisation to an unseen person',
        'cohort': {
            'acquisition_identities': ds['all_acquisition_identities'],
            'engineering_exclusion': ds['engineering_excluded'],
            'input_quality_holds': ds['scientific_holds'],
            'evaluated': people,
            'benchmark_candidates_adjudicated': ds['benchmark_candidate_pool'],
            'original_people': old, 'added_people': new,
            'independent_replication': False,
            'relationship': 'the original 40 people, with their results unchanged, plus all 11 later-eligible people '
                            'under the same fixed method: an expanded cohort, not an independent replication',
            'test_trials_each_person': test, 'unique_test_trials': trials,
            'jobs': {'trained': jobs, 'failed': 0, 'preserved_from_the_original_cohort': p['original_prediction_jobs_preserved'],
                     'added': p['new_prediction_jobs']},
        },
        'protocol': {
            'data': f'the motor-imagery training runs (EEG_MI_train) of both sessions: {ds["channels"]} channels at '
                    f'{ds["sampling_hz"]:,} Hz, left- versus right-hand imagery',
            'session_1': f'the first {p["source_fit_trials"]} trials fit the classifier; the last '
                         f'{p["source_probability_calibration_trials"]} calibrate its probabilities',
            'session_2_budgets': list(BUDGETS),
            'session_2_calibration': 'the first 0, 10, 20 or 40 trials of session 2, labelled, added for calibration',
            'session_2_test': f'the final {test} trials of session 2, the same in every condition; the four budgets '
                              'add no people and no test trials',
            'preprocessing': 'fixed per-trial 8–30 Hz filtering; dimensionless inputs only',
            'selection': 'no parameter search, score-driven retry, trial dropping, class-balancing search or target-'
                         'balance selection; the cohort was fixed before its test labels were read',
            'interval_kind': f'pointwise 95% whole-participant bootstrap, {aggregate["bootstrap"]["draws"]:,} draws, '
                             'the same draws for every arm and budget; descriptive, no multiple-comparison adjustment',
        },
        'arms': arms,
        'between_arms': between,
        'reading': 'With 40 labelled session-2 trials the log-covariance baseline improves on average, with a paired '
                   'interval above zero, yet some people still declined. The relative-PSD baseline\'s interval '
                   'includes zero: its average gain is not established.',
        'history': 'An earlier 40-person snapshot of this experiment was prepared but never published here. Its people '
                   'and results are all included, unchanged, in the 51 above; it is not a separate result.',
        'limitations': [
            'One dataset, the same people, offline: trained on session 1, tested on session 2. Not unseen-person '
            'generalisation, online closed-loop control, clinical efficacy, consumer headsets or reduced montages.',
            'Two fixed CPU baselines; no foundation model or fine-tuning (LoRA/PEFT).',
            'An expanded cohort (the original 40 plus 11 later-eligible people), not an independent replication.',
            'Each person\'s estimate rests on 60 test trials and is noisy; the four budgets reuse those trials.',
            'Physical amplitude units are unresolved; only the dimensionless baselines are run.',
            'Intervals are pointwise and descriptive, not adjusted for multiple comparisons. Not comparable with '
            'published scores under other protocols.',
        ],
        'independent_audit': {
            'status': 'pass', 'people': audit['participant_count'], 'conditions_recomputed': audit['planned_jobs'],
            'checked': 'every person, arm and budget recomputed, with the original 40-person aggregate, the expanded '
                       'means, paired contrasts and bootstrap intervals; no model refitted or loaded',
        },
        'rights': rights(record),
    }
    return result, secret


EXTRACT = {DREEM: dreem, OPENBMI: openbmi}


# ---------------------------------------------------------------------------- boundary
def scrub_check(value, trail='$'):
    if isinstance(value, dict):
        for k, v in value.items():
            require(k not in REFUSED_KEYS and not any(f in k.lower() for f in REFUSED_KEY_FRAGMENTS),
                    f'refused field in export: {trail}.{k}')
            scrub_check(v, f'{trail}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scrub_check(v, f'{trail}[{i}]')
    elif isinstance(value, str):
        require(not SOURCE_IDS.search(value), f'source record, file or participant identifier in export: {trail}')
        require(not PRIVATE_TOKENS.search(value), f'private host or path in export: {trail}')


def figure_free(holds):
    """A hold says that no score exists and why; it carries none, not even a number in prose."""
    for h in holds:
        require(set(h) == {'id', 'statement', 'reason', 'scope'}, f'hold {h.get("id")}: unexpected fields')
        require(all(isinstance(v, str) and not re.search(r'\d', v) for v in h.values()),
                f'hold {h["id"]}: a hold carries a figure')
    return holds


def numbers(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)
    elif isinstance(value, float):
        yield value


def build(manifest_bytes):
    manifest = json.loads(manifest_bytes)
    results, included, secret = {}, [], {}
    require([s['id'] for s in manifest['sources']] == list(EXTRACT), 'the manifest names other sources')
    for record in manifest['sources']:
        require(record['decision'] == 'aggregate_preview', f'{record["id"]}: no other decision has an extractor')
        require(approved(record), f'{record["id"]}: approval record is incomplete')
        out = EXTRACT[record['id']](record)
        if isinstance(out, tuple):
            out, secret[record['id']] = out
        results[record['id']] = out
        included.append(record['id'])
    payload = {
        'schema_version': 'bci-report-large-source-update-v1',
        'release_id': manifest['release_id'],
        'generated_at': manifest['reviewed_at'],
        'status': 'aggregate_preview',
        'metric_units': 'accuracy, balanced accuracy, macro F1, recall, precision and F1 are proportions in [0,1]; '
                        "Cohen's kappa is in [-1,1]; differences are differences of proportions; counts of people, "
                        'nights, epochs and trials are whole numbers; null means undefined, never zero',
        'scope': ('Two separate questions, each with two fixed classical CPU baselines: sleep staging in two Dreem '
                  'cohorts kept as separate experiments, and cross-session motor-imagery calibration in 51 OpenBMI '
                  'people. No foundation-model or fine-tuning result. Nothing here extends the eight-protocol matrix, '
                  'and the results share no ranking.'),
        'results': results,
        'status_only': [],
        'holds': figure_free(manifest['holds']),
        'not_published': manifest['notPublished'],
        'provenance': {'manifest_sha256': sha(manifest_bytes), 'included': included,
                       'holds': [h['id'] for h in manifest['holds']]},
    }
    scrub_check(payload)
    validate_public(payload)
    # Per-person values refused by value too: every one of them within its own result, and every
    # nonzero one anywhere (a zero change identifies no one, and zeros are published legitimately,
    # such as the training prior's kappa).
    published = set(numbers(payload))
    for rid, values in secret.items():
        own = set(numbers(results[rid]))
        leaked = [v for v in values if v in own or (v != 0.0 and v in published)]
        require(not leaked, f'{rid}: a per-person value reached the export: {leaked[:3]}')
    return payload


def inputs_available():
    manifest = json.loads(MANIFEST.read_bytes())
    refs = []
    for s in manifest['sources']:
        refs += [s[k] for k in ('handoff', 'release', 'protocol', 'numericalAudit', 'supplementaryAudit',
                                'releaseDecision', 'scopeReview', 'depositMetadata', 'sourceAggregate',
                                'licenseRecord', 'consentRecord') if k in s]
        if 'unitStatus' in s:
            refs.append(s['unitStatus']['evidence'])
    return all((PROJECT / r['path']).exists() for r in refs)


def serialized_export():
    return (json.dumps(build(MANIFEST.read_bytes()), indent=2, ensure_ascii=False) + '\n').encode()


def export():
    manifest_bytes = MANIFEST.read_bytes()
    payload = build(manifest_bytes)
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode()
    for out in OUTPUTS:
        out.write_bytes(data)
    audit = {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': sha(data), 'manifest_sha256': sha(manifest_bytes),
        'included': payload['provenance']['included'], 'status_only': [],
        'holds': payload['provenance']['holds'],
        'checks': [
            'pinned handoffs, release JSONs, protocol, audits, supplementary audit, source aggregate, release '
            'decisions, licence and consent evidence and the unit-discrepancy record',
            'each release decision names the exact release bytes, its audits and its handoff',
            'Dreem: both audits passed every check and bind the same scoring run; every paired value in the release '
            'equals the independent audit\'s exactly; the release names both audit hashes and the protocol the audit '
            'names',
            'OpenBMI: the audit passed and names the source aggregate; every metric block in the release equals that '
            'aggregate value for value; its stale pre-audit flags are the expected sealed state',
            'Dreem: DOD-H 25 and DOD-O 55 nights, 80 evaluated of 81 archive records, 20 jobs, 5 folds per cohort; '
            '77,901 - 3 - 75 = 77,823 eligible epochs; stage support sums to each cohort\'s eligible epochs',
            'Dreem: null stays null (no night defines it), every interval holds its mean, the paired mean equals the '
            'difference of the arm means, and the paired balanced-accuracy interval excludes zero',
            'Dreem: the training prior is the constant-N2 floor and is labelled nowhere as a chance level; no '
            'cross-cohort field',
            'Dreem: each cohort\'s consent and ethics statement rests on a recorded quote, and each missing statement '
            'is stated as missing',
            'OpenBMI: 54 = 1 + 2 + 51; 3,060 = 51 x 60 test trials; 408 = 51 x 2 x 4 jobs; budgets exactly 0/10/20/40',
            'OpenBMI: decline counts are whole people over 51; paired means equal the cell differences; accuracy is a '
            'whole count of 3,060 trials; every interval holds its mean',
            'OpenBMI: the log-covariance 40-versus-0 interval excludes zero and the relative-PSD one includes it',
            'the printed figures are the ones the pinned handoffs state',
            'per-person summaries refused by key, fragment and value; holds carry no figure',
            'no private paths or hosts, record, file or participant identifiers',
        ],
        'audit_bindings': {
            DREEM: {
                'bound': [
                    'release bytes: by the release decision (release_sha256), which also names both audits, the '
                    'handoff and the source-scope review',
                    'all six paired metrics per cohort (point and interval): equal, exactly, to the independent '
                    'audit\'s audited values',
                    'protocol and numeric conventions: the same hashes in release and independent audit; protocol '
                    'pinned here',
                    'coverage: 20 jobs, 80 nights, DOD-H 25 / DOD-O 55, 5 folds, both arms, in both audits and the '
                    'release',
                    'the supplement names the independent audit\'s hash and the same activation and completion '
                    'hashes',
                ],
                'not_bound': [
                    'neither audit names the release JSON hash or the private aggregate-candidate hash it projects; '
                    'per-arm levels (accuracy, balanced accuracy, macro F1, kappa, per-stage values) are bound only '
                    'through the release decision, the supplement\'s projection assertion, the audited paired '
                    'differences (ridge minus prior) and the handoff\'s printed figures',
                ],
            },
            OPENBMI: {
                'bound': [
                    'release bytes: by the release decision (website_release.sha256), which also names the aggregate, '
                    'the audit and the handoff',
                    'source aggregate bytes: by the audit (expanded_aggregate_sha256)',
                    'every metric block of the release: equal, value for value, to the audited aggregate',
                    'scoring activation, aggregation plan, bootstrap, cohort and job counts: equal across release, '
                    'aggregate and audit',
                ],
                'not_bound': [
                    'the audit does not name the release JSON hash; the release is tied to it through the release '
                    'decision and through value-for-value equality with the audited aggregate',
                ],
            },
        },
    }
    EXPORT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    return audit


if __name__ == '__main__':
    print(json.dumps(export(), indent=2, ensure_ascii=False))
