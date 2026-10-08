"""Independent audit of later-sessions-update.json: every figure in the served file against the source releases.

A separate program from export_later_sessions_update.py. It shares no extraction code with that export: it reads
the served bytes, the review manifest and the four approved source releases it pins (and, for a handful of counts
no release carries, the pinned handoffs and the Forenzo independent review), builds its own table of what every
figure must be, and compares the two sets of figures one for one:

- every number and every null in the served file has an expected value here, and every expected value is in the
  served file: nothing unaudited, nothing missing;
- copied figures are equal to the source release exactly; derived ones (chance levels, target shares, the Forenzo
  mean-to-median ratio, the count of records the ridge did worse on) are recomputed here;
- each interval flag follows from its interval; no minimum, 10th or 90th percentile, and no median other than the
  four Forenzo ridge medians, of any source release appears anywhere in the file;
- each source release is the byte-identical file the handoff index fingerprints, and the two served copies are one.

    python3 pipeline/publication/audit_later_sessions_export.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'research/publication_review_20261008'
MANIFEST = REVIEW / 'later-sessions-release-manifest.json'
AUDIT = REVIEW / 'later-sessions-export-audit.json'
SERVED = (PROJECT / 'site/src/data/later-sessions-update.json', PROJECT / 'site/public/data/later-sessions-update.json')
INDEX = PROJECT / 'research/large_source_expansion_20261002/Large EEG Batch Website Integration Handoff.md'
IDS = ('wbcic-cross-session-cpu', 'wbcic-frozen-cbramod', 'rsvp-later-visits', 'forenzo-continuous-control')


class AuditFailure(Exception):
    pass


def check(ok, message):
    if not ok:
        raise AuditFailure(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pinned(ref):
    raw = (PROJECT / ref['path']).read_bytes()
    check(digest(raw) == ref['sha256'], f'{ref["path"]}: not the pinned bytes')
    return raw


def whole(text):
    return int(text.replace(',', ''))


def handoff_count(text, pattern, label):
    m = re.search(pattern, text)
    check(m is not None, f'{label}: the handoff does not state it')
    return whole(m.group(1))


# ---------------------------------------------------------------------------- what every figure must be
def wbcic_cpu(rel, handoff):
    out, R = {}, ('results', IDS[0])
    for c, b in rel['cohorts'].items():
        P = R + ('cohorts', c)
        k = len(b['methods']['source_prior']['confusion_aggregate'])          # classes, from the matrix's size
        t = rel['trial_accounting'][c]
        out[P + ('people',)] = b['expected_participants']
        out[P + ('chance_level',)] = 1 / k
        out[P + ('source_trials',)] = t['source_delivered_trials']
        out[P + ('target_trials',)] = t['target_delivered_trials']
        for arm in ('source_prior', 'relative_spectral_ridge'):
            m = b['methods'][arm]
            A = P + ('arms', arm)
            out[A + ('balanced_accuracy', 'mean')] = m['primary_balanced_accuracy_mean']
            for i in (0, 1):
                out[A + ('balanced_accuracy', 'interval_95', i)] = m['primary_ci_95_percentile'][i]
            out[A + ('accuracy', 'mean')] = m['accuracy_conditional_mean']
            out[A + ('macro_f1', 'mean')] = m['macro_f1_conditional_mean']
        cd = b['conditional_descriptive']
        out[P + ('paired', 'balanced_accuracy_difference', 'mean')] = cd['observed_means']['ridge_minus_prior']
        for i in (0, 1):
            out[P + ('paired', 'balanced_accuracy_difference', 'interval_95', i)] = cd['ci_95_percentile']['ridge_minus_prior'][i]
        out[P + ('paired', 'people')] = cd['declared_participants']
    m, q = rel['method'], rel['qa_holds_preserved']
    out.update({R + ('sessions', 'train'): m['source_session_ordinal'], R + ('sessions', 'test'): m['test_session_ordinal'],
                R + ('sessions', 'unused'): m['unused_session_ordinal'],
                R + ('sessions', 'target_session_labels'): m['target_calibration_labels'],
                R + ('trials', 'source'): rel['source_trials'], R + ('trials', 'target'): rel['test_trials'],
                R + ('trials', 'session_files'): handoff_count(handoff, r'across (\d+) selected session files', 'session files'),
                R + ('trials', 'excluded'): sum(v for t in rel['trial_accounting'].values() for k, v in t.items()
                                                 if 'excluded' in k),
                R + ('session_quality', 'sessions'): q['strict_contract_holds_preserved'] + q['strict_contract_passes_preserved'],
                R + ('session_quality', 'fixed_count_holds'): q['strict_contract_holds_preserved'],
                R + ('session_quality', 'holds_in_selected_sessions'): q['selected_source_or_target_hold_records'],
                R + ('session_quality', 'holds_in_unused_session_2'): q['unused_session02_hold_records'],
                R + ('session_quality', 'delivered_trials'): handoff_count(handoff, r'([\d,]+) delivered trials versus', 'delivered'),
                R + ('session_quality', 'nominal_trials'): handoff_count(handoff, r'versus ([\d,]+) nominal', 'nominal'),
                R + ('independent_audit', 'people'): rel['participants']})
    return out


def wbcic_cbramod(rel, cpu_rel):
    out, R = {}, ('results', IDS[1])
    for c, x in rel['cohorts'].items():
        P = R + ('cohorts', c)
        out[P + ('people',)] = x['participants']
        out[P + ('chance_level',)] = 1 / len(x['confusion_aggregate'])
        out[P + ('source_trials',)] = x['source_trials']
        out[P + ('target_trials',)] = x['target_trials']
        F = P + ('frozen_cbramod',)
        out[F + ('balanced_accuracy', 'mean')] = x['cbramod_balanced_accuracy']
        for i in (0, 1):
            out[F + ('balanced_accuracy', 'interval_95', i)] = x['cbramod_ci95'][i]
        out[F + ('accuracy', 'mean')] = x['accuracy']
        out[F + ('macro_f1', 'mean')] = x['macro_f1']
        ridge = cpu_rel['cohorts'][c]['methods']['relative_spectral_ridge']['primary_balanced_accuracy_mean']
        check(x['spectral_ridge_balanced_accuracy'] == ridge, f'{c}: the two releases disagree on the spectral ridge')
        out[P + ('relative_spectral_ridge', 'balanced_accuracy', 'mean')] = x['spectral_ridge_balanced_accuracy']
        out[P + ('paired', 'balanced_accuracy_difference', 'mean')] = x['paired_difference']
        for i in (0, 1):
            out[P + ('paired', 'balanced_accuracy_difference', 'interval_95', i)] = x['paired_difference_ci95'][i]
        out[P + ('paired', 'people')] = x['participants']
    p = rel['protocol']
    out.update({R + ('sessions', 'train'): p['source_session_ordinal'], R + ('sessions', 'test'): p['target_session_ordinal'],
                R + ('sessions', 'unused'): p['unused_session_ordinal'],
                R + ('sessions', 'target_session_labels'): rel['target_session_new_label_budget'],
                R + ('independent_audit', 'people'): rel['counts']['participants']})
    return out


def rsvp(rel, handoff):
    out, R = {}, ('results', IDS[2])
    for i, key in enumerate(('Day_7', 'Day_80', 'Day_200')):
        v = rel['visits'][key]
        c, mt = v['counts'], v['metrics']
        V = R + ('visits', i)
        fc = v['full_cohort_primary']
        out.update({V + ('nominal_day',): int(key.split('_')[1]), V + ('people',): v['visit_scored_n'],
                    V + ('events',): c['structural_eligible'], V + ('target_events',): c['target'],
                    V + ('non_target_events',): c['non_target'], V + ('target_share',): c['target'] / c['structural_eligible'],
                    V + ('signal_invalid_events',): c['signal_invalid'], V + ('delivered_events',): c['delivered'],
                    V + ('auroc', 'mean'): fc['mean'], V + ('auroc', 'interval_95', 0): fc['interval']['q025'],
                    V + ('auroc', 'interval_95', 1): fc['interval']['q975'],
                    V + ('average_precision', 'mean'): mt['average_precision']['mean'],
                    V + ('log_loss', 'mean'): mt['log_loss']['mean'], V + ('brier_score', 'mean'): mt['brier_score']['mean'],
                    V + ('ece_10_bins', 'mean'): mt['ece_10_equal_width']['mean']})
    ct = rel['contrast']
    C = R + ('contrast',)
    out.update({C + ('auroc_difference', 'mean'): ct['full_cohort']['mean'],
                C + ('auroc_difference', 'interval_95', 0): ct['full_cohort']['interval']['q025'],
                C + ('auroc_difference', 'interval_95', 1): ct['full_cohort']['interval']['q975'],
                C + ('people',): ct['common_defined_n'],
                C + ('people_declined_by_0_05_or_more',): ct['decline_at_most_minus_0_05_count'],
                C + ('share_declined_by_0_05_or_more',): ct['decline_at_most_minus_0_05_fraction'],
                R + ('cohort', 'people'): rel['dataset']['planned_participants'],
                R + ('independent_audit', 'people'): rel['dataset']['planned_participants']})
    D = R + ('design',)
    out.update({D + ('first_visit_fit_events',): handoff_count(handoff, r'([\d,]+) source-fit events', 'fit events'),
                D + ('first_visit_calibration_events',): handoff_count(handoff, r'([\d,]+) source-calibration events', 'cal'),
                D + ('scored_events',): sum(v['counts']['structural_eligible'] for v in rel['visits'].values()),
                D + ('blocks',): handoff_count(handoff, r'across (\d+) selected blocks', 'blocks'),
                D + ('selected_events',): handoff_count(handoff, r'All ([\d,]+) selected events', 'selected events'),
                D + ('events_removed_for_signal',): 0 if 'zero were removed for signal invalidity' in handoff else None})
    check(out[D + ('scored_events',)] == handoff_count(handoff, r'([\d,]+) held-out scoring events', 'scored'),
          'rsvp: the visits do not add up to the handoff’s scored events')
    return out


FORENZO_METRICS = ('raw_rmse_x', 'raw_rmse_y', 'r2_x', 'r2_y', 'pearson_x', 'pearson_y')


def forenzo(rel, handoff, review):
    out, R = {}, ('results', IDS[3])
    reasons = review['coverage']['original_hold_reasons']
    for c, x in rel['cohorts'].items():
        P = R + ('cohorts', c)
        held = x['candidate_participants'] - x['admitted_participants']
        out.update({P + ('candidate_records',): x['candidate_participants'], P + ('admitted_records',): x['admitted_participants'],
                    P + ('held_before_scoring',): held})
        if held:
            for i, k in enumerate(reasons.values()):
                out[P + ('hold_reasons', i, 'records')] = k
        for arm, a in x['arms'].items():
            A = P + ('arms', arm)
            n = a['score_pass_participants']
            out.update({A + ('records',): n, A + ('target_rows',): a['rows'], A + ('target_trials',): a['trials'],
                        A + ('target_runs',): a['runs']})
            for src, dst in (('ridge', 'ridge'), ('source_mean_comparator', 'source_mean')):
                m = a['methods'][src]
                prim = m['joint_source_sd_normalized_rmse']
                M = A + (dst,)
                out[M + ('primary', 'mean')] = prim['mean']
                out[M + ('primary', 'interval_95', 0)] = prim['bootstrap_mean_ci95'][0]
                out[M + ('primary', 'interval_95', 1)] = prim['bootstrap_mean_ci95'][1]
                if src == 'ridge':
                    out[M + ('primary', 'median')] = prim['median']
                for s in FORENZO_METRICS:
                    S = M + ('secondary', s)
                    if m[s].get('summary', 0) is None:
                        out.update({S + ('mean',): None, S + ('interval_95',): None, S + ('records_defined',): m[s]['n']})
                    else:
                        out.update({S + ('mean',): m[s]['mean'], S + ('interval_95', 0): m[s]['bootstrap_mean_ci95'][0],
                                    S + ('interval_95', 1): m[s]['bootstrap_mean_ci95'][1],
                                    S + ('records_defined',): m[s]['n']})
            pr = a['paired_ridge_minus_source_mean']['joint_source_sd_normalized_rmse']
            check(pr['minimum'] > 0, f'forenzo/{c}/{arm}: the ridge did not do worse on every record')
            out.update({A + ('paired', 'primary_difference', 'mean'): pr['mean'],
                        A + ('paired', 'primary_difference', 'interval_95', 0): pr['bootstrap_mean_ci95'][0],
                        A + ('paired', 'primary_difference', 'interval_95', 1): pr['bootstrap_mean_ci95'][1],
                        A + ('paired', 'records_with_higher_ridge_error'): pr['n'],   # minimum > 0: every record
                        A + ('paired', 'records'): pr['n'],
                        A + ('upper_tail', 'ridge_mean_over_median'):
                            a['methods']['ridge']['joint_source_sd_normalized_rmse']['mean']
                            / a['methods']['ridge']['joint_source_sd_normalized_rmse']['median']})
    admitted = sum(x['admitted_participants'] for x in rel['cohorts'].values())
    out.update({R + ('coverage', 'candidate_records'): sum(x['candidate_participants'] for x in rel['cohorts'].values()),
                R + ('coverage', 'admitted_records'): admitted,
                R + ('coverage', 'target_rows_per_arm'): rel['held_out_rows_per_arm'],
                R + ('coverage', 'response_rows_removed'): rel['response_rows_removed'],
                R + ('coverage', 'response_fits'): handoff_count(handoff, r'All (\d+) response fits', 'fits'),
                R + ('coverage', 'source_target_members'): handoff_count(handoff, r'All (\d+) admitted source/target members', 'members'),
                R + ('coverage', 'input_rows'): handoff_count(handoff, r'produced ([\d,]+) feature rows', 'rows'),
                R + ('independent_audit', 'records'): admitted})
    check(out[R + ('coverage', 'response_fits')] == 2 * admitted, 'forenzo: fits are not two arms per admitted record')
    return out


def leaves(value, trail=()):
    """Every number and every null in the served file, with its path."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, trail + (i,))
    elif value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        yield trail, value


def flags(value, trail=()):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == 'interval_excludes_zero':
                yield trail, v
            yield from flags(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flags(v, trail + (i,))


def private_stats(value, trail=()):
    """Every per-person summary the source releases carry, with where it sits."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k in ('minimum', 'maximum', 'p10', 'p90', 'median') and isinstance(v, float):
                yield trail + (k,), v
            yield from private_stats(v, trail + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from private_stats(v, trail + (i,))


DERIVED = ('chance_level', 'target_share', 'ridge_mean_over_median')


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    served = [p.read_bytes() for p in SERVED]
    check(served[0] == served[1], 'the two served copies differ')
    payload = json.loads(served[0])
    check(payload['release_id'] == manifest['release_id'] and payload['provenance']['manifest_sha256'] == digest(manifest_bytes),
          'the served file names another manifest')

    src = {s['id']: s for s in manifest['sources']}
    check(tuple(src) == IDS, 'the manifest names other sources')
    index = INDEX.read_text()
    releases, handoffs = {}, {}
    for sid, s in src.items():
        raw = load_pinned(s['release'])
        name = Path(s['release']['path']).name
        check(f'| `{name}` | `{digest(raw)}` |' in index, f'{sid}: the handoff index fingerprints other bytes')
        check(payload['provenance']['source_export_sha256'][sid] == digest(raw), f'{sid}: the served file names other bytes')
        releases[sid] = json.loads(raw)
        handoffs[sid] = load_pinned(s['handoff']).decode()
    review = json.loads(load_pinned(src[IDS[3]]['independentReview']))

    expected = {}
    expected.update(wbcic_cpu(releases[IDS[0]], handoffs[IDS[0]]))
    expected.update(wbcic_cbramod(releases[IDS[1]], releases[IDS[0]]))
    expected.update(rsvp(releases[IDS[2]], handoffs[IDS[2]]))
    expected.update(forenzo(releases[IDS[3]], handoffs[IDS[3]], review))

    found = dict(leaves(payload))
    unaudited = sorted(map(str, set(found) - set(expected)))
    missing = sorted(map(str, set(expected) - set(found)))
    check(not unaudited, f'figures in the served file with no audit rule: {unaudited[:5]}')
    check(not missing, f'audited figures missing from the served file: {missing[:5]}')
    exact = derived = nulls = 0
    for path, want in expected.items():
        got = found[path]
        if want is None:
            check(got is None, f'{path}: a null became {got!r}')
            nulls += 1
        elif path[-1] in DERIVED:
            check(got is not None and math.isclose(got, want, rel_tol=1e-15, abs_tol=0), f'{path}: {got!r} != {want!r}')
            derived += 1
        else:
            check(type(got) is type(want) and got == want, f'{path}: {got!r} != {want!r}')
            exact += 1

    # Each interval flag follows from its interval.
    n_flags = 0
    for trail, flag in flags(payload):
        node = payload
        for k in trail:
            node = node[k]
        ivs = [v['interval_95'] for v in node.values() if isinstance(v, dict) and 'interval_95' in v]
        check(len(ivs) == 1 and flag == (ivs[0][0] > 0 or ivs[0][1] < 0), f'{trail}: the flag does not follow')
        n_flags += 1

    # No per-person summary of any source release, except the four Forenzo ridge medians, appears in the file.
    published = [v for _, v in leaves(payload) if isinstance(v, float)]
    allowed = {v for p, v in expected.items() if p[-1] == 'median'}
    private = 0
    for sid, rel in releases.items():
        for where, v in private_stats(rel):
            if v in allowed and where[-1] == 'median' and 'ridge' in where and 'joint_source_sd_normalized_rmse' in where:
                continue
            check(v not in published, f'{sid}: the per-person value at {where} reached the served file')
            private += 1
    check(len(allowed) == 4, 'not exactly four Forenzo ridge medians')

    by_result = {sid: sum(1 for p in expected if p[:2] == ('results', sid)) for sid in IDS}
    return {
        'status': 'pass', 'release_id': payload['release_id'],
        'export_sha256': digest(served[0]), 'manifest_sha256': digest(manifest_bytes),
        'auditor': 'pipeline/publication/audit_later_sessions_export.py',
        'independence': 'A separate program from the export. It reads the served bytes, the review manifest and the '
                        'four pinned source releases, plus the pinned handoffs and the Forenzo independent review for '
                        'the few counts no release carries, builds its own table of what every figure must be and '
                        'shares no extraction code with the export.',
        'source_export_sha256': {sid: payload['provenance']['source_export_sha256'][sid] for sid in IDS},
        'included': payload['provenance']['included'], 'status_only': payload['status_only'],
        'holds': payload['provenance']['holds'],
        'figures_compared': len(expected), 'figures_by_result': by_result,
        'copied_exactly': exact, 'recomputed': derived, 'nulls_kept': nulls, 'interval_flags_recomputed': n_flags,
        'per_person_values_checked_absent': private,
        'checks': [
            'each source release is the pinned file and the one the handoff index fingerprints; the served file names '
            'the same four hashes and the manifest it was built from; the two served copies are byte-identical',
            'every number and null in the served file has an expected value derived here from the source releases, '
            'and every expected value is in the file: no unaudited figure and no missing one',
            'copied figures equal the source release exactly, type included; chance levels (one over the classes of '
            'each confusion matrix), RSVP target shares and the Forenzo mean-to-median ratios are recomputed here',
            'the WBCIC spectral ridge is the same number in both WBCIC releases, cohort by cohort',
            'the Forenzo count of records the ridge did worse on follows from a positive paired minimum in every '
            'cohort and arm; the minimum itself is absent from the file',
            'nulls stay null: the RSVP delivered-event counts and the comparator correlations',
            'every interval_excludes_zero flag follows from its interval',
            'no minimum, 10th or 90th percentile and no median of any source release reaches the file, except the '
            'four Forenzo ridge medians the manifest approves',
            'counts no release carries (124 session files, 40,490 and 40,500 trials, the RSVP design counts, 46 fits, '
            '552 members, 4,000,407 rows) are read from the pinned handoffs and the Forenzo independent review',
        ],
        'audit_bindings': {
            'bound': [
                'source release bytes: pinned in the manifest, fingerprinted in the handoff index, named in the served '
                'file',
                'every figure: equal to its source-release leaf or recomputed from source-release leaves',
            ],
            'not_bound': [
                'the release decisions, independent audits and checks behind each release are verified by the export '
                '(their verdicts and hash chains), not re-read here',
                'prose in the served file is checked by the export (numerals against the pinned handoffs and releases, '
                'claims and labels by pattern), not by this audit',
            ],
        },
    }


def write_audit():
    result = audit()
    AUDIT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(write_audit(), indent=2, ensure_ascii=False))
