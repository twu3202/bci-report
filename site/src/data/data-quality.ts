/**
 * What /topics/data-quality/ reads from its two exports. data-quality-update.json (owner decisions D1 and D2): Shin2022
 * as the worked case, with its three arms and the coverage chain from the runs in the release to the windows it is
 * scored on, and eldBETA and ZuCo 2.0 as status cases with no score. dataset-checks-update.json (owner decisions D15,
 * D16, D18, D21): Kim beta-range as a second worked case (training-free CCA on all its participants), MIND as a
 * conditional case on record IDs, and Damm and NeBULA as one-person status cases beside eldBETA, with no score. The
 * page's section order is the one the dataset-checks file sets (placement.page_order), and the one-person sentence is
 * printed once, before eldBETA, Damm and NeBULA (placement.one_person_lead_before); data-quality-update.json keeps its
 * bytes, so eldBETA's own repeat of that sentence is dropped from the page, not from the file.
 *
 * Every figure the page prints is a leaf of one of those files (a `Fig`, printed with data-fig and re-read by the
 * checks). What this module adds is words: the step names of the coverage chains, the arms' names in Chinese, and the
 * Chinese of the exports' own English (arm inputs, caveats, chain steps, checks, holds, consent and ethics statements and
 * what is not published), keyed by the exact English so that a changed export fails the build instead of printing other
 * words. A key that matches no string of either export fails the build too, and so does a translation that does not
 * carry exactly its English's digits.
 *
 * Some of the export's sentences print in the page's own words, each for a reason a release review gave (the B5 and
 * P-DQ reviews): Shin2022's deduplication hold states what the sources establish and no more; the duration control's
 * input states its input, and the caveat beside the table says once that it is known only after the trial ends;
 * eldBETA's "other 99 participants" prints the record's participant count as a figure; the SingLEM fact line points
 * to the paper's list, which the linked exposure row does not reproduce; what is not published states the eldBETA
 * hold's reason no more (the holds line does), and names the register file for MOABB's counts only while Shin2022's
 * row there carries them; ZuCo 2.0's finding drops the marker clause so the case paragraph matches the plan's
 * wording, and its consent gap is not tied to a release. The facts under each are asserted below.
 *
 * The rules the page lives under: eldBETA prints counts and no score (D2), and "header calibration applied", never
 * "units verified"; the ZuCo 2.0 case paragraph carries no figure; the duration control is labelled retrospective; the
 * coverage chain is printed once; Shin2022's consent and ethics are the A3 record's; each attribution ends "Derived
 * analysis by BCI Report; not endorsed by the authors."; links to the open register exist only while its file is
 * served and its page built, and the page says MOABB's counts are on Shin2022's row only while that row carries them.
 * No private path, version label or update date reaches the page.
 *
 * The dataset checks add their own rules: Kim beta-range's sealing is process separation, never blinded labels (the
 * export's sentence); MIND's unit is the record ID, never a person, its four contrasts carry record-ID resampling ranges
 * named as such and never called confidence intervals, its secondary panel stands apart with no interval, and its four
 * licence statements sit side by side with ScienceDB's terms-of-use page stated as unread; Damm and NeBULA carry design,
 * counts, file and timing facts, the arms run and their holds, and no score of any kind (every number in their part of
 * the export is a whole count); NeBULA's participant counts print as the export states them, and the Zenodo record its
 * files name is never linked. Hold reasons stay on /releases/#holds: the page names each hold and links it.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import dq from './data-quality-update.json';
import dcJson from './dataset-checks-update.json';
import fm from './foundation-models-update.json';
import { registerPageBuilt, registerServed } from './files';
import { holds, openRegister } from './releases';
import type { Locale } from './i18n';
import type { Fig, Fmt } from './entities';

export const DQ = 'data-quality-update.json';
export const DC = 'dataset-checks-update.json';
export const DQ_PATH = '/topics/data-quality/';
export const DQ_ANCHOR = { shin: 'shin2022', kim: 'kim2025-beta-range', mind: 'mind2026', onePerson: 'one-person', eldbeta: 'eldbeta', damm: 'damm',
                           nebula: 'nebula', zuco: 'zuco2', zucoSource: 'zuco2-source', register: 'register-rows', methods: 'methods-and-limits' } as const;
/**
 * Each case's row in the open register (register-ids.json keeps these ids stable across register versions), keyed by
 * its section here and in page order. Damm's row is named for the dataset; its section is #damm.
 */
export const DQ_REGISTER_ROW = {
  shin2022: 'r-site-shin2022', 'kim2025-beta-range': 'r-site-kim2025-beta-range', mind2026: 'r-site-mind2026', eldbeta: 'r-site-eldbeta',
  damm: 'r-site-damm-finger-imagery', nebula: 'r-site-nebula', zuco2: 'r-site-zuco2',
} as const;
export type DqSection = keyof typeof DQ_REGISTER_ROW;
export const ENDORSEMENT = 'Derived analysis by BCI Report; not endorsed by the authors.';

export type Part = string | Fig;
export const dqFig = (raw: number, fmt: Fmt = 'count'): Fig => ({ raw, fmt, src: DQ });
export const dcFig = (raw: number, fmt: Fmt = 'count'): Fig => ({ raw, fmt, src: DC });
/** A small count as a word, for the page's prose (five fingers, eight variants); outside one to ten the build stops. */
const WORDS: Record<Locale, string[]> = {
  en: ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'],
  zh: ['零', '一', '两', '三', '四', '五', '六', '七', '八', '九', '十'],
};
export const word = (n: number, locale: Locale) => {
  if (!Number.isInteger(n) || n < 1 || n > 10) throw new Error(`data-quality.ts: ${n} has no word`);
  return WORDS[locale][n];
};
export const Word = (n: number) => word(n, 'en').replace(/^./, c => c.toUpperCase());
const countText = (n: number) => n.toLocaleString('en-US');

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`data-quality.ts: ${what}`); };
// The dataset-checks export, read as data: its four cases are keyed by section id, two with a hyphen.
const dc: any = dcJson;
const near = (a: number, b: number) => Math.abs(a - b) < 1e-12;
/** The export mixes straight and curly apostrophes; the page prints the curly one (B5 review). */
export const curly = (s: string) => s.replace(/(\w)'(?=\w)/g, '$1’');

/* --- The cases, typed as the page reads them ---------------------------------------------------------------- */

type Interval = [number, number];
export interface ShinArm {
  arm: 'training_prior' | 'normalized_spectral_ridge' | 'retrospective_duration_ridge';
  role: 'reference' | 'eeg' | 'retrospective_control';
  name: string; input: string; mean: number; interval: Interval; pooled: number;
}
export interface ChainStep {
  id: string; count: number; text: string; role?: 'excluded' | 'held';
  by_target?: Record<'1' | '2', number>; windows_per_run_by_target?: Record<'1' | '2', number>;
  closed_windows?: number; participants?: number; flat_on_all_channels?: number; flat_on_some_channels?: number;
  non_finite_input_windows?: number; percent_of_closed_windows?: number; percent_of_duration_eligible?: number;
  participants_with_both_targets?: number; pair_conditions?: string[]; within_one_participant?: boolean;
}

const S = dq.shin2022, E = dq.eldbeta, Z = dq.zuco2;
export const shin = S, eld = E, zuco = Z, dqRelease = dq.release_id, dqSchema = dq.schema_version, dqNotPublished = dq.not_published;
export const shinArms: ShinArm[] = S.arms.map(a => ({
  arm: a.arm as ShinArm['arm'], role: a.role as ShinArm['role'], name: a.name, input: a.input,
  mean: a.participant_mean_balanced_accuracy, interval: a.participant_bootstrap_percentile_95 as Interval,
  pooled: a.pooled_balanced_accuracy_secondary,
}));
export const shinChain = S.coverage_chain as unknown as ChainStep[];
const arm = (id: ShinArm['arm']) => { const a = shinArms.find(x => x.arm === id); need(a, `no Shin2022 arm ${id}`); return a!; };
export const prior = arm('training_prior'), spectral = arm('normalized_spectral_ridge'), duration = arm('retrospective_duration_ridge');
export const step = (id: string) => { const c = shinChain.find(x => x.id === id); need(c, `no coverage step ${id}`); return c!; };

/* --- The facts every sentence of the page rests on; the build stops without them ----------------------------- */

need(dq.release_id === 'data-quality-update-20261020' && dq.schema_version === 'bci-report-data-quality-update-v1', 'this release and schema');
need(dc.release_id === 'dataset-checks-update-20261028' && dc.schema_version === 'bci-report-dataset-checks-update-v1', 'the dataset checks’ release and schema');
// One page for both files, outside every leaderboard and the core matrix. Its sections are both files' cases, each once,
// in the order the dataset-checks file sets; the earlier file's three keep their relative order.
export const dqSections = dc.placement.page_order as DqSection[];
need([dq, dc].every(f => f.placement.page === DQ_PATH && f.placement.leaderboard === false && f.placement.core_matrix === false),
  'one page, outside every leaderboard and the core matrix');
need(JSON.stringify([...dq.placement.sections, ...dc.placement.sections].sort()) === JSON.stringify([...dqSections].sort())
  && new Set(dqSections).size === dqSections.length, 'the page’s sections are both files’ cases, each once');
need(dqSections.filter(s => (dq.placement.sections as string[]).includes(s)).join() === dq.placement.sections.join(), 'the earlier cases keep their order');
need(JSON.stringify(Object.keys(DQ_REGISTER_ROW)) === JSON.stringify(dqSections), 'a register row for every section, in page order');
need([DQ_ANCHOR.shin, DQ_ANCHOR.kim, DQ_ANCHOR.mind, DQ_ANCHOR.eldbeta, DQ_ANCHOR.damm, DQ_ANCHOR.nebula, DQ_ANCHOR.zuco].join() === dqSections.join(),
  'the anchors are the sections, in page order');
/** Every case of both files with its kind: worked, conditional, or status (a held score, or no score). */
export const dqCases: { id: DqSection; status: string; kind: 'worked' | 'conditional' | 'status' }[] = [...dq.cases, ...dc.cases].map(c => ({
  id: c.id as DqSection, status: c.status,
  kind: c.status === 'released' ? 'worked' : c.status === 'released_conditional' ? 'conditional' : 'status',
})).sort((a, b) => dqSections.indexOf(a.id) - dqSections.indexOf(b.id));
need(dqCases.map(c => `${c.id}:${c.status}`).join() === 'shin2022:released,kim2025-beta-range:released,mind2026:released_conditional,'
  + 'eldbeta:score_held,damm:score_held,nebula:score_held,zuco2:no_score', 'two worked cases, one conditional case and four status cases, in page order');
need(dc.cases.every(c => (dc as any)[c.id]?.section === c.id && (dc as any)[c.id]?.status === c.status && (dc as any)[c.id]?.kind === c.kind),
  'each dataset check’s own record matches its case');
// The one-person sentence: once, before the cases it covers, which are the three held scores.
export const onePerson = dc.one_person;
need(onePerson.cases.join() === dqCases.filter(c => c.status === 'score_held').map(c => c.id).join()
  && dc.placement.one_person_lead_before === onePerson.cases[0] && dqSections.indexOf(onePerson.cases[0] as DqSection) === dqSections.indexOf(DQ_ANCHOR.mind) + 1,
  'the one-person sentence covers the three held scores and leads them, after MIND');
need(onePerson.sentence.startsWith('With one person every score is that person’s') && onePerson.sentence.includes(`these ${word(onePerson.cases.length, 'en')} cases`),
  'the one-person sentence names its cases’ number');
// Shin2022: the question, the task and the design.
need(S.question === 'What survives a participant-held-out check?', 'the Shin2022 question');
need(S.scope.participants === 10 && S.scope.recording_days_each === 1 && S.scope.human_recordings_only && !S.scope.foundation_models
  && S.scope.sensor === 'dry', 'ten participants, one recording day each, human recordings, dry electrodes');
need(S.method.evaluation === 'leave-one-participant-out' && S.method.folds === S.scope.participants
  && S.method.training_participants_each_fold === S.scope.participants - 1, 'every participant held out once, fitted on the others');
need(S.method.window_samples === S.method.window_seconds * S.scope.sampling_hz && S.method.window_seconds === 1, 'the first second, every sample');
need(S.method.tuning === false && S.method.hypothesis_tests === false && S.method.label_from_outcome === false
  && S.labels.outcome_used === false, 'no tuning, no test, no label from the outcome');
need(S.labels.state === 'TargetCode' && /right/.test(S.labels.classes['1']) && /left/.test(S.labels.classes['2']), 'right and left are the instructed targets');
need(S.interval.unit === 'participant' && S.interval.descriptive && S.interval.one_index_matrix_for_all_arms
  && S.interval.kind === 'participant bootstrap percentile interval' && S.interval.level === 0.95, 'one participant-bootstrap index for all arms');
// The arms: roles, the retrospective control, the intervals around their means, and the prior on one half.
need(shinArms.map(a => `${a.arm}:${a.role}`).join() === 'training_prior:reference,normalized_spectral_ridge:eeg,retrospective_duration_ridge:retrospective_control',
  'three arms in the export’s order, the duration control retrospective');
for (const a of shinArms) need(a.interval[0] <= a.mean && a.mean <= a.interval[1], `${a.arm}: the interval holds the mean`);
need(prior.mean === 0.5 && prior.pooled === 0.5 && prior.interval[0] === 0.5 && prior.interval[1] === 0.5, 'the prior is one half, every resample');
need(/known only after the trial ends/.test(duration.input) && /Retrospective/.test(duration.name), 'the duration control reads what is known only after the trial ends');
// "Sits close to it": the two arms' intervals overlap and their means are within one point.
need(Math.abs(spectral.mean - duration.mean) < 0.01 && spectral.interval[0] < duration.interval[1] && duration.interval[0] < spectral.interval[1],
  'the spectral arm sits close to the duration control');
need(S.caveat.includes('the spectral arm sits close to it, and no test between arms was run') && S.caveat.includes('Ten participants, one recording day each'),
  'the caveat as the page prints it');
// The coverage chain: each link adds up, from the runs in the release to the signal-valid windows.
need(shinChain.map(c => c.id).join() === 'recorded_runs,byte_identical_pairs,distinct_runs,incomplete_run_held,complete_runs,closed_windows,'
  + 'shorter_than_one_second,duration_eligible,signal_invalid,signal_valid', 'the ten links of the coverage chain, in order');
{
  const [runs, pairs, distinct, held, complete, closed, short, eligible, invalid, valid] = shinChain;
  need(distinct.count === runs.count - pairs.count && pairs.within_one_participant && pairs.pair_conditions?.join() === 'BW30,NT0', 'runs less byte-identical pairs');
  need(complete.count === distinct.count - held.count && held.count === 1 && held.role === 'held', 'one incomplete run held whole');
  need(complete.participants === S.scope.participants, 'the complete runs cover every participant');
  const perRun = complete.windows_per_run_by_target!;
  need(closed.count === complete.count * (perRun['1'] + perRun['2']) && perRun['1'] === perRun['2'], 'closed windows: twelve per target per complete run');
  need(distinct.closed_windows! > closed.count, 'the distinct runs hold the closed windows and the incomplete run’s');
  need(eligible.count === closed.count - short.count && short.role === 'excluded', 'windows of at least one second');
  need(valid.count === eligible.count - invalid.count && invalid.role === 'excluded', 'signal-valid windows');
  for (const c of [closed, short, eligible, invalid, valid]) need(c.by_target!['1'] + c.by_target!['2'] === c.count, `${c.id}: right and left add up`);
  need(invalid.flat_on_all_channels! + invalid.flat_on_some_channels! === invalid.count && invalid.non_finite_input_windows === 0, 'flat on all or some channels');
  need(Math.round(1000 * valid.count / closed.count) / 10 === valid.percent_of_closed_windows, 'the share of closed windows');
  need(Math.abs(100 * valid.count / eligible.count - valid.percent_of_duration_eligible!) < 1e-9, 'the share of windows lasting a second');
  need(valid.participants_with_both_targets === S.scope.participants, 'every participant keeps both targets');
  need(S.catalog.catalog_trial_seconds === S.catalog.header_feedback_cap_seconds && S.catalog.headers_read === runs.count
    && S.catalog.reading.includes('MaxFeedbackDuration'), 'the catalog’s trial length is the feedback cap of every header read');
}
// How it was checked: the strict attempt stopped with no model; the census read no score; the rule was frozen first.
{
  const H = Object.fromEntries(S.how_checked.map(h => [h.id, h])) as Record<string, any>;
  need(S.how_checked.map(h => `${h.id}:${h.state}`).join() === 'strict-protocol-stopped:held,score-free-census:pass,second-protocol-frozen:pass,'
    + 'predictions-sealed:pass,independent-audit:pass,release-review:pass', 'six checks, the first held');
  need(H['strict-protocol-stopped'].models_fitted === 0 && H['score-free-census'].models_trained === 0 && H['score-free-census'].scores_computed === false
    && H['second-protocol-frozen'].scores_inspected_during_design === false && H['independent-audit'].metrics_reproduced === true, 'the order of the checks');
}
need(S.holds.length === 7, 'seven Shin2022 holds');
// Shin2022's terms, consent and ethics: the A3 record's.
const SC = S.consent_and_ethics;
need(S.rights.license === 'CC BY 4.0' && S.rights.terms.data_licence.pinned_version_is_latest && S.rights.attribution.endsWith(ENDORSEMENT),
  'Shin2022: CC BY 4.0, the pinned version the latest, the attribution ending with the site’s sentence');
need(SC.ethics_approval.stated && SC.ethics_approval.approval_number === null && SC.ethics_approval.statement.endsWith('the paper gives no approval number.')
  && SC.gaps.length === 1 && SC.gaps[0].field === 'ethics.approval_number', 'Shin2022: board named, no approval number, the one gap');
need(SC.informed_consent.stated && SC.informed_consent.kind === 'written informed consent', 'Shin2022: written informed consent');
// eldBETA (D2): counts only, the score held; header calibration applied; the derived epochs unused.
const EC = E.counts;
need(E.status === 'score_held' && E.flags.score_published === false && E.flags.header_calibration_applied === true
  && E.flags.derived_matlab_epochs_used === false && E.flags.recordings_repaired === false, 'eldBETA: counts only, the score held');
need(EC.participants_run === 1 && EC.trials === EC.blocks * EC.targets && EC.trials_passing_checks === EC.trials && EC.trials_dropped === 0
  && EC.non_finite_values_in_analysed_windows === 0 && EC.non_finite_values_outside_analysed_windows > 0, 'eldBETA: every trial passes, none dropped');
need(E.holds[3] === `The other ${EC.published_participants - EC.participants_run} published participants are neither acquired nor evaluated.`,
  'eldBETA: the other published participants');
need(/header calibration applied/.test(E.holds[1]) && /MATLAB epochs were not used/.test(E.holds[0]), 'eldBETA: the holds line');
need(E.rights.attribution.endsWith(ENDORSEMENT) && E.rights.license === 'CC BY 4.0', 'eldBETA: CC BY 4.0, the attribution ending with the site’s sentence');
need(E.consent_and_ethics.ethics_approval.approval_number === '20210032' && E.consent_and_ethics.informed_consent.stated, 'eldBETA: approval number and written consent');
{
  // No score of any kind in the eldBETA case: no key names an accuracy, and no value is one.
  const keys: string[] = [];
  const walk = (v: unknown) => { if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) { keys.push(k); walk(x); } };
  walk(E);
  need(!keys.some(k => /accuracy|^score$|residual|comparator/.test(k)), 'eldBETA carries no score');
}
// The SingLEM fact line: the released exposure row on BETA reads "not in the list", and its evidence names eldBETA,
// a separate database, as in Table I of the paper the row links.
export const singlemSource: string = (() => {
  const cell = (fm as any).results['foundation-models-v9'].pretraining_exposure.cells.find((c: any) => c.model === E.related.model && c.dataset === E.related.dataset);
  need(cell && cell.status === 'not_exposed' && /^Not in Table I\. Only eldBETA/.test(cell.evidence) && /different database from BETA/.test(cell.evidence)
    && E.related.file === 'foundation-models-update.json' && E.related.model === 'singlem', 'SingLEM’s exposure row on BETA: absent, eldBETA in Table I');
  need(cell.urls?.[0] === 'https://arxiv.org/abs/2509.17920v3', 'the paper SingLEM’s exposure row links');
  return cell.urls[0];
})();
// ZuCo 2.0: fixation times outside the recording; no score; nothing corrected or removed; no consent read.
need(Z.status === 'no_score' && Z.flags.fixation_times_outside_recording && Z.flags.score_computed === false && Z.flags.timing_corrected === false
  && Z.flags.rows_removed === false && Z.flags.data_redistributed === false && Z.consent_and_ethics.read === false, 'ZuCo 2.0: status only');
need(Z.finding.startsWith('In one converted run on NEMAR, some fixation times fall outside the recording')
  && curly(Z.hold) === 'No EEG–text score is computed until the converter’s timing rules and a source-checksummed fixture are available.',
  'ZuCo 2.0: the case paragraph as the plan words it');
need(Z.clears_when.length === 3 && Z.source.repository === 'NEMAR' && Z.source.name === 'ZuCo 2.0', 'ZuCo 2.0: three conditions, its NEMAR record');
// The holds register: both holds open, each linked to its section here.
export const eldHold = holds.find(h => h.id === 'eldbeta-one-participant-score');
export const zucoHold = holds.find(h => h.id === 'zuco2-converted-run-timing');
need(eldHold && !eldHold.closed && eldHold.href === `${DQ_PATH}#${DQ_ANCHOR.eldbeta}`, 'the eldBETA hold, open, linked here');
need(zucoHold && !zucoHold.closed && zucoHold.href === `${DQ_PATH}#${DQ_ANCHOR.zuco}`, 'the ZuCo 2.0 hold, open, linked here');
need(dq.holds.map(h => h.id).join() === 'eldbeta-one-participant-score,zuco2-converted-run-timing', 'the export’s two holds');

/* --- The dataset checks (dataset-checks-update.json): the facts each section's sentences rest on --------------- */

export const kim = dc['kim2025-beta-range'], mind = dc.mind2026, damm = dc.damm, nebula = dc.nebula;
export const dcRelease: string = dc.release_id, dcSchema: string = dc.schema_version, dcNotPublished: string[] = dc.not_published;
const pass = (checks: { id: string; state: string }[], ids: string) => checks.map(h => `${h.id}:${h.state}`).join() === ids.split(',').map(x => `${x}:pass`).join();

// Kim beta-range: a complete cohort, every trial of every participant, training-free CCA; the interval is the difference
// from the fixed chance level, shifted back up by it.
{
  const K = kim, c = K.cohort, r = K.result, m = K.method, i = K.intake;
  need(K.kind === 'worked_case' && K.dataset_page === `/datasets/${K.id}/` && K.method_link === false && dc.placement.dataset_pages[K.id] === K.dataset_page,
    'Kim beta-range: a worked case with its own page and no method link');
  need(c.complete_cohort && c.blocks === c.participants * c.blocks_each && c.trials === c.participants * c.targets * c.trials_per_target_each
    && c.trials === c.blocks * c.targets && c.recording_days_each === 1, 'Kim beta-range: every block of every participant, on one day each');
  need(m.training_free && m.tuning === false && m.trials_dropped === 0 && m.channels === m.channel_names.length && m.window_samples === m.window_seconds * m.sampling_hz
    && m.band_hz[0] < i.frequency_lowest_hz && i.frequency_highest_hz * m.harmonics < m.band_hz[1], 'Kim beta-range: no training, no tuning, no trial dropped; both harmonics inside the band');
  need(r.chance === 1 / c.targets && r.equals_balanced_accuracy && c.trials_per_target_each > 0 && near(r.difference_from_chance, r.mean_participant_accuracy - r.chance)
    && near(r.accuracy_interval_95[0], r.difference_interval_95[0] + r.chance) && near(r.accuracy_interval_95[1], r.difference_interval_95[1] + r.chance)
    && r.accuracy_interval_95[0] <= r.mean_participant_accuracy && r.mean_participant_accuracy <= r.accuracy_interval_95[1], 'Kim beta-range: chance one in the targets, the interval the difference shifted by chance');
  need(K.interval.unit === 'participant' && K.interval.descriptive && K.interval.test === false && K.interval.level === 0.95 && K.interval.kind === 'participant bootstrap percentile interval',
    'Kim beta-range: a descriptive participant-bootstrap interval, no test');
  need(i.task_files === c.participants && i.md5_checked === i.task_files && i.md5_matched === i.md5_checked && i.rest_and_questionnaire_acquired === false
    && i.distinct_frequencies === c.targets && i.stored_order_ascending === false && i.moabb_list_ascending === true && i.checks_before_any_score,
    'Kim beta-range: every task file checked, the stored order not MOABB’s ascending list');
  // The export's sentences say what these fields say.
  need(K.task.includes(`${c.targets} flickering targets from ${i.frequency_lowest_hz.toFixed(1)} to ${i.frequency_highest_hz.toFixed(1)} Hz`)
    && K.task.includes(`${m.window_seconds}-second window`) && K.task.includes('no training data'), 'Kim beta-range: the task sentence');
  need(i.text.startsWith(`All ${i.md5_matched} task files passed their MD5 checks; the rest and questionnaire files were not acquired.`)
    && i.text.includes(`in the order ${i.stored_target_order.split(' Hz')[0]} Hz`) && i.text.includes('differs from the ascending list in MOABB’s metadata'), 'Kim beta-range: the intake sentence');
  need(pass(K.how_checked, 'scope-review,all-files-checked,sealed-before-scoring,independent-audit,interpretation-review'), 'Kim beta-range: five checks, each passed');
  const H = Object.fromEntries(K.how_checked.map((h: any) => [h.id, h]));
  need(H['sealed-before-scoring'].text.startsWith(`All ${countText(c.trials)} outputs were sealed`) && H['sealed-before-scoring'].text.includes('process separation, not blinded labels'),
    'Kim beta-range: sealing is process separation, not blinded labels');
  const fx = H['independent-audit'];
  need(fx.fixtures_matched === fx.fixtures && fx.fixtures === fx.fixture_design.participants * fx.fixture_design.blocks * fx.fixture_design.targets, 'Kim beta-range: every fixed fixture reproduced');
  need(K.caveats.map((x: any) => x.id).join() === 'as-stored-amplitudes,nominal-onset,one-day,offline,own-pipeline,other-ssvep-datasets,interval,fixtures', 'Kim beta-range: eight caveats');
  const Cv = Object.fromEntries(K.caveats.map((x: any) => [x.id, x.text]));
  const chancePct = String(r.chance * 100);
  need(Cv.interval.includes(`fixed ${chancePct}% chance level, shifted up by ${chancePct} points`) && Cv.fixtures.includes(`reproduced ${fx.fixtures_matched} of ${fx.fixtures} fixed fixtures`)
    && Cv['one-day'] === `Each participant’s ${word(c.blocks_each, 'en')} blocks were recorded on ${word(c.recording_days_each, 'en')} day.`
    && Cv['nominal-onset'].includes(`at ${countText(m.sampling_hz)} Hz`) && /BETA and Wearable-102/.test(Cv['other-ssvep-datasets']), 'Kim beta-range: the caveats say what the fields say');
  need(K.hold.id === 'kim-amplitude-dependent-models' && dc.holds.some((h: any) => h.id === K.hold.id && h.case === K.id), 'Kim beta-range: its hold');
  need(K.rights.license === 'CC BY 4.0' && K.rights.attribution.endsWith(ENDORSEMENT) && K.rights.terms.data_licence.pinned_version_is_latest
    && K.rights.version.startsWith(`Figshare record ${K.rights.source.match(/figshare\.(\d+)/)[1]}, version ${K.rights.terms.data_licence.pinned_version},`)
    && K.rights.terms.paper_cited_version.licence === K.rights.license, 'Kim beta-range: CC BY 4.0 at the pinned, latest version; the paper’s cited version under the same licence');
  const KC = K.consent_and_ethics;
  need(KC.ethics_approval.stated && KC.ethics_approval.quote.includes(KC.ethics_approval.approval_number) && KC.informed_consent.stated && KC.gaps.length === 0,
    'Kim beta-range: ethics approval with its number and signed consent, no gap');
  need(JSON.stringify(K.aliases) === JSON.stringify(['Kim2025BetaRange', `Figshare ${K.rights.source.match(/figshare\.(\d+)/)[1]}`, 'doi:10.1038/s41597-025-06032-2'])
    && K.rights.attribution.includes(K.aliases[2]), 'Kim beta-range: its three names');
}

// MIND: record IDs, never people. The coverage adds up from the runs in the release to the two panels; each contrast is
// its arm less its control; the ranges are descriptive record-ID resampling ranges, never confidence intervals.
export const mindStep = (id: string) => { const s = mind.coverage.find((x: any) => x.id === id); need(s, `no MIND coverage step ${id}`); return s; };
{
  const M = mind, P = M.primary, S2 = M.secondary, R = M.resampling;
  const [all, over, evald, prim, sec] = ['runs_in_release', 'overfull_first_runs', 'runs_evaluated', 'primary_panel', 'secondary_panel'].map(mindStep);
  need(M.coverage.map((x: any) => x.id).join() === 'runs_in_release,overfull_first_runs,runs_evaluated,primary_panel,secondary_panel', 'MIND: five coverage steps, in order');
  need(M.unit === 'record ID' && M.kind === 'conditional_worked_case' && M.dataset_page === false, 'MIND: a conditional case on record IDs, with no dataset page');
  need(all.count === all.record_ids * all.runs_for_each_record_id && evald.count === all.count - over.count && over.role === 'excluded'
    && evald.trials === evald.count * over.class_markers_required && evald.numeric_check_failures === 0, 'MIND: the runs in the release, less the overfull first runs');
  need(prim.count + sec.count === evald.count && prim.record_ids + sec.record_ids === all.record_ids && prim.trials + sec.trials === evald.trials
    && prim.count === prim.record_ids * all.runs_for_each_record_id && sec.count === sec.record_ids * (all.runs_for_each_record_id - 1) && sec.record_ids === over.count,
    'MIND: the primary panel keeps three runs per record ID, the secondary two');
  need(P.record_ids === prim.record_ids && P.runs === prim.count && P.trials === prim.trials && P.folds_for_each_record_id === all.runs_for_each_record_id
    && S2.record_ids === sec.record_ids && S2.runs === sec.count && S2.trials === sec.trials, 'MIND: the panels are the coverage’s');
  need(S2.interval === null && S2.pooled_with_primary === false && JSON.stringify(S2.pairs.map((p: any) => p.pair)) === JSON.stringify(P.pairs.map((p: any) => p.pair)),
    'MIND: the secondary panel apart, no interval, never pooled');
  need(P.pairs.map((p: any) => p.pair).join() === '4/5,6/7' && P.pairs.every((p: any) => p.pair === p.codes.join('/') && p.majority === 0.5 && p.ordinal_lookup < p.majority),
    'MIND: two stored-code pairs; the ordinal lookup below the majority control');
  need(M.contrasts.length === 4 && M.contrasts.every((x: any) => {
    const p = P.pairs.find((q: any) => q.pair === x.pair);
    return p && x.arm === 'csp_lda' && near(x.mean_difference, p[x.arm] - p[x.control]) && x.resampling_range[0] <= x.mean_difference && x.mean_difference <= x.resampling_range[1]
      && x.range_spans_zero === (x.resampling_range[0] < 0 && 0 < x.resampling_range[1]);
  }) && M.contrasts.map((x: any) => `${x.pair}:${x.control}`).join() === '4/5:ordinal_lookup,4/5:majority,6/7:ordinal_lookup,6/7:majority', 'MIND: four contrasts, each the arm less its control');
  need(R.kind === 'record-ID resampling range' && R.confidence_interval === false && R.test === false && R.shared_index_table
    && R.text.includes(`${R.percentiles[0]}th and ${R.percentiles[1]}th percentiles of ${countText(R.draws)} paired record-ID resamples`)
    && R.text.endsWith('They are no confidence intervals and no test.'), 'MIND: descriptive record-ID resampling ranges, named as such');
  const [s45, s67] = M.schedule.pairs;
  need(M.schedule.panel === 'primary' && M.schedule.pairs.every((s: any) => s.schedules === 2 && s.complementary && s.primary_ids_repeating_one_schedule + s.primary_ids_mixing_schedules === P.record_ids)
    && M.schedule.text.includes(`one of only ${word(s45.schedules, 'en')} complementary ${s45.trials_per_schedule}-trial label schedules`) && s67.trials_per_schedule === s45.trials_per_schedule
    && M.schedule.text.includes(`${s45.primary_ids_repeating_one_schedule} record IDs for ${s45.pair} and ${s67.primary_ids_repeating_one_schedule} for ${s67.pair} repeat one schedule across all ${word(P.folds_for_each_record_id, 'en')} runs`)
    && M.schedule.text.includes('explains the ordinal values below 50%') && s45.trials_per_schedule * 2 === over.class_markers_required, 'MIND: the schedule sentence says what the schedule fields say');
  need(M.processing.controls.every((x: any) => x.input === 'no EEG') && M.processing.controls[0].text.includes(`each of the ${s45.trials_per_schedule} positions`)
    && M.processing.fitted_on_training_runs_only && M.processing.search === false && M.processing.auxiliary_channels_used === false
    && M.processing.window_samples === (M.processing.window_after_marker_seconds[1] - M.processing.window_after_marker_seconds[0]) * M.processing.resampled_hz,
    'MIND: two controls with no EEG; one fixed pipeline fitted on the training runs only');
  need(pass(M.how_checked, 'sealed-before-scoring,independent-replay,interpretation-review') && M.how_checked[0].trials === evald.trials && M.how_checked[1].max_decision_difference === 0,
    'MIND: three checks, each passed');
  need(M.caveats.map((x: any) => x.id).join() === 'stored-marker-windows,record-ids,other-explanations,offline-filtering,sealed-epochs,reference,terms,ethics', 'MIND: eight caveats');
  const Cv = Object.fromEntries(M.caveats.map((x: any) => [x.id, x.text]));
  const w = M.processing.window_after_marker_seconds;
  need(Cv['stored-marker-windows'].startsWith(`Windows run from ${w[0]} to ${w[1]} seconds after each stored class marker.`)
    && Cv['record-ids'].includes(`The release describes ${all.record_ids} participants`) && Cv['record-ids'].includes('no claim about people follows'), 'MIND: the caveats say what the fields say');
  const T = M.rights.terms;
  need(T.statements.map((s: any) => `${s.source}:${s.value}`).join() === 'paper:CC BY 4.0,archive dataset description:CC BY 4.0,MOABB adapter:CC BY-NC 4.0,ScienceDB record page:CC BY-NC 4.0'
    && JSON.stringify(M.rights.licenses_stated) === JSON.stringify([...new Set(T.statements.map((s: any) => s.value))])
    && T.terms_of_use_page_read === false && T.aggregate_only && T.redistributed === false && Cv.terms.includes('terms-of-use page was not read'),
    'MIND: four licence statements, two licences, the terms-of-use page unread');
  const MC = M.consent_and_ethics;
  need(MC.ethics_approval.stated && MC.ethics_approval.body === null && MC.ethics_approval.approval_number === null && MC.informed_consent.stated
    && MC.gaps.map((g: any) => g.field).join() === 'ethics_committee_and_number,ethics_consent_source.captured_at', 'MIND: no committee named, no number; written consent');
  need(M.rights.attribution.endsWith(ENDORSEMENT), 'MIND: the attribution ends with the site’s sentence');
}

// Damm and NeBULA: one participant each, no score of any kind. Every number in their part of the export is a whole
// count, no key names a score, and the counts add up.
{
  for (const [name, x] of [['Damm', damm], ['NeBULA', nebula]] as const) {
    const keys: string[] = [], nums: number[] = [];
    const walk = (v: unknown) => { if (typeof v === 'number') nums.push(v); else if (v && typeof v === 'object') for (const [k, y] of Object.entries(v)) { keys.push(k); walk(y); } };
    walk(x);
    need(nums.every(Number.isInteger) && !keys.some(k => /accuracy|^score$|residual|comparator|fraction|(?:^|_)share(?:_|$)|difference|interval/.test(k)), `${name} carries no score`);
    need(x.kind === 'status_case' && x.status === 'score_held' && x.flags.score_published === false && x.flags.additional_participant_acquired === false
      && x.design.participants_run === 1 && x.held.rule === 'one-person' && onePerson.cases.includes(x.id) && x.rights.attribution.endsWith(ENDORSEMENT),
      `${name}: one participant, its scores held under the one-person rule`);
  }
  const D = damm.design, F = damm.files;
  need(D.delivered_cues === D.trials_per_held_out_run * D.directions && D.trials_per_held_out_run === D.classes * D.trials_per_class_per_run && D.class_names.length === D.classes
    && D.runs_used === 2 && D.directions === 2, 'Damm: two runs, each held out once, balanced over the fingers');
  need(F.edf_channels === F.scalp_channels + F.excluded_channels.length && F.samples_per_run === F.run_seconds * F.sampling_hz && F.cue_samples_reconstructed && F.sample_column_present === false,
    'Damm: the channels and samples of each run');
  need(F.text.startsWith(`Each random-order run is ${F.run_seconds} seconds of ${F.edf_channels} EDF channels at ${F.sampling_hz} Hz: ${F.scalp_channels} scalp channels, ${word(2, 'en')} reference channels and a marker channel.`)
    && F.text.includes(`holds ${F.state_blocks_per_run} state blocks`) && F.text.includes(`a ${F.white_seconds}-second white screen and a ${F.fixation_seconds}-second fixation cross and lasts ${F.cue_seconds} seconds`),
    'Damm: the file sentence says what the file fields say');
  need(damm.variants.length === 8 && damm.variant_directions_audited === damm.variants.length * D.directions && damm.flags.variants_fixed_before_scoring && damm.flags.all_variants_retained
    && damm.flags.independent_audit_passed && damm.variants.every((v: any) => v.signal_input === (v.channels !== null) || v.role === 'shuffle sanity check')
    && damm.variants.filter((v: any) => / channels/.test(v.name)).every((v: any) => v.name.includes(`${v.channels} `)), 'Damm: eight variants and controls, fixed before scoring, all audited');
  need(damm.holds.length === 4 && damm.holds[3] === `The other ${D.published_participants - D.participants_run} participants in the record are neither acquired nor evaluated.`
    && damm.flags.sequential_runs_evaluated === false && damm.flags.physical_trigger_timing_validated === false, 'Damm: four holds, the last the other participants');
  need(damm.rights.license === 'CC0' && damm.rights.licenseUrl === null && damm.rights.terms.license_file_present === false && damm.consent_and_ethics.ethics_approval.stated
    && damm.consent_and_ethics.ethics_approval.quote.includes(damm.consent_and_ethics.ethics_approval.approval_number) && damm.consent_and_ethics.informed_consent.stated === false
    && damm.consent_and_ethics.gaps.map((g: any) => g.field).join() === 'consent', 'Damm: CC0 with the LICENSE file absent; ethics approval; no consent statement, a gap');
  const N = nebula.design, E2 = nebula.eeg, G = nebula.emg, A = nebula.arms, X = nebula.file_facts, byC = N.trials_by_condition;
  need(N.assistance_conditions.join() === Object.keys(byC).join() && N.trials === N.assistance_conditions.reduce((s: number, k: string) => s + byC[k], 0)
    && N.folds === N.assistance_conditions.length && N.missing_trial_fabricated === false, 'NeBULA: the trials of the three assistance runs, each held out once');
  need(N.participant_counts.text === `The paper and the Figshare record’s description state ${N.participant_counts.paper_and_record_description} participants; the record’s files hold ${N.participant_counts.participant_archives_in_record} participant archives, and MOABB lists ${N.participant_counts.moabb_catalog}.`,
    'NeBULA: the participant counts as the export states them');
  // The task line says what MOABB's catalog lists: read from the MOABB row that the 20261020 register file (served
  // unchanged) still carries, before this round folded it into the site row.
  {
    const moabbRow = (JSON.parse(readFileSync(resolve('public/data', 'open-register-20261020.json'), 'utf8')).entries as any[])
      .find(e => e.moabb?.loaders?.includes('NeBULA2025'))?.moabb?.fields_as_listed?.[0];
    need(moabbRow?.paradigm === 'Imagery' && moabbRow.people === N.participant_counts.moabb_catalog,
      'NeBULA: MOABB’s catalog lists the dataset under (motor) imagery, with the participant count the page prints');
  }
  need(A.eeg.length * N.folds === A.eeg_fits && A.emg_and_fusion.length * N.folds === A.emg_and_fusion_fits && A.pretrained_model === false && A.independently_audited
    && A.eeg.filter((a: any) => !a.signal_input).map((a: any) => a.id).join() === 'order' && A.emg_and_fusion.every((a: any) => a.signal_input), 'NeBULA: the arms run, one with no signal input');
  need(A.eeg[0].name.includes(`all ${E2.channels} channels, ${E2.window_ms[0] / 1000} to ${E2.window_ms[1] / 1000} seconds`) && A.eeg[1].name.includes(`the ${-E2.precue_window_ms[0]} milliseconds`)
    && A.emg_and_fusion[0].name.startsWith(`EMG, ${G.rows} rows`) && A.emg_and_fusion[1].name.startsWith(`The ${E2.channels} EEG features and the ${G.rows} EMG features`), 'NeBULA: the arms’ names say what the fields say');
  need(X.boundary_ties === Object.values(X.boundary_ties_by_condition as Record<string, number>).reduce((s, v) => s + v, 0) && X.backward_overlaps === 0 && X.first_parse_stopped_before_features
    && X.complete_quartets === N.trials && X.stored_markers === 4 * N.trials && X.markers_match_eeg_files && X.emg_eeg_sample_lengths_equal && X.emg_channel_rows === G.rows
    && X.emg_rows_relabelled === false && X.emg_channel_rows !== X.emg_channels_in_metadata, 'NeBULA: the file facts add up');
  need(X.text[0].includes(`hold ${X.boundary_ties} boundary ties`) && X.text[0].includes(`(${N.assistance_conditions.map((k: string) => `${X.boundary_ties_by_condition[k]} ${k}`).join(', ')})`)
    && X.text[1].startsWith(`The EMG files hold ${X.emg_channel_rows} channel rows where their metadata states ${X.emg_channels_in_metadata};`)
    && X.text[2].startsWith(`All ${X.stored_markers} stored markers of the ${N.trials} trials`) && X.text.length === 4, 'NeBULA: the file sentences say what the file fields say');
  need(nebula.flags.order_diagnostic_comparison_published === false && nebula.holds.length === 3, 'NeBULA: no comparison of the order diagnostic; three holds');
  const Z = nebula.rights.terms.zenodo_13627307;
  need(Z.registered_public_record === false && Z.terms === null && Z.text.includes('Zenodo 13627307') && nebula.rights.source.includes('figshare')
    && /^the data descriptor article only/.test(nebula.rights.terms.paper_licence.covers) && nebula.rights.terms.data_licence.versions_listed === 1
    && nebula.consent_and_ethics.ethics_approval.stated && nebula.consent_and_ethics.informed_consent.stated && nebula.consent_and_ethics.gaps.length === 0,
    'NeBULA: its Figshare record, the Zenodo id no registered record; the paper’s licence the article’s only; ethics and consent stated');
}
// The holds: the export's three, each open in the holds register and linked to its section here; the page names each
// and links it, and prints none of their reasons.
export const kimHold = holds.find(h => h.id === kim.hold.id), dammHold = holds.find(h => h.id === damm.held.id), nebulaHold = holds.find(h => h.id === nebula.held.id);
need(dc.holds.map((h: any) => h.id).join() === [kim.hold.id, damm.held.id, nebula.held.id].join(), 'the dataset checks’ three holds');
for (const [h, s] of [[kimHold, kim.section], [dammHold, damm.section], [nebulaHold, nebula.section]] as const)
  need(h && !h.closed && h.href === `${DQ_PATH}#${s}`, `the hold of ${s}, open, linked here`);
/** The reasons the holds register gives, which this page links and never prints. */
export const holdReasons: string[] = dc.holds.map((h: any) => h.reason);

/* --- The open register: each case's row, only while the register file is served and its page is built -------- */

type RegisterEntry = { id: string; ladder: string; findings?: { code: string; params?: Record<string, unknown> }[] };
/**
 * The register as the site serves it (the bytes of the file releases.ts names as the newest), or null while that file
 * is not served. With the file served, a case whose row is missing, or is not a dataset row, stops the build.
 */
const register = registerServed
  ? JSON.parse(readFileSync(resolve('public/data', openRegister.json), 'utf8')) as { status: string; entries: RegisterEntry[] }
  : null;
if (register) for (const id of Object.values(DQ_REGISTER_ROW)) {
  const row = register.entries.find(e => e.id === id);
  need(row && row.ladder === 'dataset', `${openRegister.json} has no dataset row ${id}`);
}
/**
 * Whether Shin2022's register row carries MOABB's catalog counts as its finding (catalog_differs_from_files, case
 * shin2022). The page says the counts are on that row only while this holds; once the register is frozen, the build
 * stops without it.
 */
export const dqCatalogFinding: boolean = !!register?.entries.find(e => e.id === DQ_REGISTER_ROW.shin2022)?.findings
  ?.some(f => f.code === 'catalog_differs_from_files' && f.params?.case === 'shin2022');
if (register?.status === 'frozen')
  need(dqCatalogFinding, `${openRegister.json} is frozen, and ${DQ_REGISTER_ROW.shin2022} carries no catalog_differs_from_files finding for shin2022`);
/** The row id of each case, or null while the register file is not served or its page (/datasets/register/) not built. */
export const dqRegisterRows: Record<keyof typeof DQ_REGISTER_ROW, string> | null = register && registerPageBuilt ? { ...DQ_REGISTER_ROW } : null;

/* --- The page's words for the export's own English ---------------------------------------------------------- */

/** The coverage chain's step names, by id. */
export const chainLabel: Record<string, Record<Locale, string>> = {
  recorded_runs: { en: 'Runs in the release', zh: '发布中的 run' },
  byte_identical_pairs: { en: 'Byte-identical pairs', zh: '逐字节相同的 run 对' },
  distinct_runs: { en: 'Distinct runs', zh: '互不相同的 run' },
  incomplete_run_held: { en: 'Incomplete run', zh: '不完整的 run' },
  complete_runs: { en: 'Complete runs', zh: '完整的 run' },
  closed_windows: { en: 'Closed feedback windows', zh: '已结束的反馈时间窗' },
  shorter_than_one_second: { en: 'Shorter than one second', zh: '不足一秒' },
  duration_eligible: { en: 'At least one second', zh: '至少一秒' },
  signal_invalid: { en: 'A flat channel in the first second', zh: '第一秒有恒定通道' },
  signal_valid: { en: 'Signal-valid', zh: '信号有效' },
};
need(shinChain.every(c => chainLabel[c.id]), 'a name for every step of the chain');

/**
 * The export's sentences printed in the page's own words (B5 review). Keyed by the export's English; the page prints
 * the value instead, in both languages, and the export's sentence never.
 */
export const dqReworded: Record<string, string> = {
  // Exact deduplication does not establish trial independence; the export's wording asserted dependence.
  'Exact deduplication leaves trials dependent within each participant and run sequence; every run of a participant stays in that participant’s fold.':
    'Exact deduplication leaves trial independence unestablished; every run of a participant stays in that participant’s fold.',
  // The arm's input; that it is known only after the trial ends is said once, in the caveat beside the table.
  'One value: the log of the full feedback duration, which is known only after the trial ends; ridge with alpha 1.0.':
    'One value: the log of the full feedback duration; ridge with alpha 1.0.',
  // The linked SingLEM page shows the BETA row as absent from the list and never names eldBETA: point to the list.
  'eldBETA is in SingLEM’s published pretraining list, as SingLEM’s exposure row on BETA records; eldBETA and BETA are separate databases.':
    'eldBETA is in SingLEM’s published pretraining list, Table I of the SingLEM paper; BETA, a separate database, is absent from it, as SingLEM’s exposure row on BETA shows.',
  // The one-person reason is stated by the holds line and the lede; the list names what is held.
  "eldBETA's one-participant accuracy and its fixed first-frequency comparator: held by the owner's decision under the one-person rule.":
    'eldBETA’s one-participant accuracy and its fixed first-frequency comparator.',
  // Not tied to a release, so it stays true until a statement is read.
  'No consent or ethics statement for this dataset was read in this release.': 'No consent or ethics statement for this dataset has been read yet.',
  // MIND's licence statements sit side by side in a table beside this line, which states what the table does not.
  'The paper and the archive’s dataset description state CC BY 4.0; the MOABB adapter and the ScienceDB record page’s metadata state CC BY-NC 4.0. ScienceDB’s terms-of-use page was not read. Aggregate values only; no data are redistributed.':
    'ScienceDB’s terms-of-use page was not read. Aggregate values only; no data are redistributed.',
  // Kim's amplitude hold is stated once, by its caveat beside the hold line; the check says what the review admitted.
  'A separate review admitted the as-stored, scale-invariant CCA arm before any score, and kept amplitude-dependent models held.':
    'A separate review admitted the as-stored, scale-invariant CCA arm before any score.',
  // The register's NeBULA row folds MOABB's record in and prints no task label; what MOABB lists is its catalog's
  // paradigm field (open-register-20261020.json, the MOABB row it folds in), checked below.
  'The source describes executed reaching with an upper-limb exoskeleton; the open register keeps MOABB’s imagery label as MOABB lists it.':
    'The source describes executed reaching with an upper-limb exoskeleton; MOABB’s catalog lists the dataset under motor imagery.',
  // The one-person rule is stated once, before eldBETA, Damm and NeBULA; the list names what is held.
  'Every Damm and NeBULA score: accuracies, balanced accuracies, control values, differences, paired correctness counts and diagnostic fractions, held by the owner’s decision under the one-person rule; and any comparison of NeBULA’s order diagnostic with its EEG or EMG arms.':
    'Every Damm and NeBULA score: accuracies, balanced accuracies, control values, differences, paired correctness counts and diagnostic fractions; and any comparison of NeBULA’s order diagnostic with its EEG or EMG arms.',
};

/** Chinese for the export's English and for the reworded sentences, keyed by the exact English. */
export const dqZh: Record<string, string> = {
  // The arms.
  'Participant-weighted training prior': '按被试等权的训练集先验',
  'Normalized spectral ridge': '归一化 spectral ridge',
  'Retrospective duration control': '回溯的时长对照',
  'No input: always the larger training class, with each training participant weighted equally.':
    '不读任何输入：总是预测训练集中较大的那一类，每名训练被试的权重相同。',
  '32 log band powers relative to each channel’s 1–40 Hz power: alpha (8–12 Hz) and beta (13–30 Hz) on each of the 16 stored channels; ridge with alpha 1.0, no tuning.':
    '32 个对数频带功率，各自相对于所在通道 1–40 Hz 的功率：16 个存储通道上各取 alpha（8–12 Hz）与 beta（13–30 Hz）；岭回归，alpha 取 1.0，不调参。',
  'One value: the log of the full feedback duration; ridge with alpha 1.0.': '只读一个值：整段反馈时长的对数；岭回归，alpha 取 1.0。',
  'The scores cover the signal-valid windows only: feedback lasting at least one second, and a first second that is finite with positive 1–40 Hz power on all 16 channels. The label is the instructed target in closed-loop cursor recordings, which carry visual, controller and behaviour confounds. The duration control reads the whole feedback duration, known only after the trial ends, so it checks a confound; the spectral arm sits close to it, and no test between arms was run. Ten participants, one recording day each; the intervals are descriptive.':
    '分数只覆盖信号有效的时间窗：反馈至少持续一秒，且第一秒在全部 16 个通道上都是有限值、1–40 Hz 功率为正。标签是闭环光标记录中指示的目标，这类记录带有视觉、控制器与行为上的混杂。时长对照读的是整段反馈时长，要到试次结束后才知道，所以它检验的是一个混杂因素；spectral ridge 一组与它相差无几，两组之间没有做任何检验。十名被试，每人一个记录日；区间只作描述。',
  // The coverage chain.
  'Runs in the release’s human recordings; the simulated branch is excluded and adds no participant.':
    '发布中人类记录的 run；模拟分支不计入，也不增加被试。',
  'Pairs of runs that are byte-identical: each pair sits within one participant and joins a BW30 run and an NT0 run.':
    '逐字节相同的 run 对：每一对都在同一名被试之内，由一个 BW30 run 和一个 NT0 run 组成。',
  'Distinct runs once each byte-identical pair counts once.': '每对逐字节相同的 run 只计一次后，互不相同的 run。',
  'One run ends inside a feedback window; it is held whole.': '有一个 run 在某个反馈时间窗中途结束；这个 run 整个暂缓。',
  'Complete distinct runs, each with twelve closed feedback windows per target.': '完整且互不相同的 run，每个目标各有十二个已结束的反馈时间窗。',
  'Closed feedback windows in the complete runs.': '完整 run 中已结束的反馈时间窗。',
  'Feedback ended within the first second, so the window holds less than the one second the arms read.':
    '反馈在第一秒之内就结束了，所以时间窗不足各组读取的一秒。',
  'Windows with at least one second of feedback.': '反馈至少持续一秒的时间窗。',
  'Windows whose first second is constant on at least one channel, which leaves that channel no 1–40 Hz power; the rule was frozen after a score-free census and before any fit.':
    '第一秒内至少有一个通道恒定不变的时间窗，该通道因此没有 1–40 Hz 功率；这条规则在不计算分数的普查之后、任何拟合之前冻结。',
  'Signal-valid windows: the population all three arms are scored on.': '信号有效的时间窗：三个组都在这些时间窗上评分。',
  // How it was checked.
  'The first, strict protocol over all duration-eligible windows met a flat signal interval at its zero-power gate and stopped before any model was fitted; that attempt stays failed and held.':
    '第一个、更严格的协议覆盖全部时长合格的时间窗，在零功率关卡处遇到一段平直信号，在拟合任何模型之前就停止了；那次尝试记为失败并暂缓。',
  'A census read the signal of every duration-eligible window, with no model and no score.':
    '一次普查读取了每个时长合格时间窗的信号，不用任何模型，也不计算任何分数。',
  'A second protocol with the signal-validity rule was frozen after the census and before any fit.':
    '带信号有效性规则的第二个协议在普查之后、任何拟合之前冻结。',
  'Predictions were sealed before the audit; metrics were computed only after it.': '预测在审计之前封存；指标在审计之后才计算。',
  'An independent audit rebuilt every metric from the sealed predictions.': '一次独立审计从封存的预测重建了每一项指标。',
  'An independent release review passed the aggregate values and the coverage for publication.': '一次独立的发布审核认可了聚合数值与覆盖情况，准予发布。',
  // Shin2022's holds.
  'The paper pairs NT0 with BW60, while the byte-identical runs pair BW30 with NT0; which recording NT0 stands for is unresolved.':
    '论文把 NT0 与 BW60 配成一对，而逐字节相同的 run 是 BW30 与 NT0 成对；NT0 究竟对应哪一段记录，尚未厘清。',
  'Comparisons between the BW, CV and NT control-parameter conditions are held: one BW60 header records a 5-second buffer, and the NT and CV headers record 30-second defaults.':
    'BW、CV 与 NT 三种控制参数条件之间的比较暂缓：有一个 BW60 的文件头记录了 5 秒的缓冲，NT 与 CV 的文件头记录的是 30 秒的默认值。',
  'The incomplete run is held whole; using its closed windows would need its own frozen rule.':
    '不完整的 run 整个暂缓；要使用其中已结束的时间窗，需要单独冻结一条规则。',
  'A task over every closed window, whatever its duration, would need its own frozen protocol.':
    '如果要在每个已结束的时间窗上做任务、不论其时长，需要单独冻结一个协议。',
  'The full scalp montage, the display latency, the absolute hardware calibration and any overlap with pretraining corpora are unestablished.':
    '完整的头皮电极布局、显示延迟、硬件的绝对定标，以及数据与各预训练语料有无重叠，都尚未确立。',
  'The physical cause of the flat intervals is unknown.': '平直信号段的物理成因不明。',
  'Exact deduplication leaves trial independence unestablished; every run of a participant stays in that participant’s fold.':
    '精确去重之后，试次是否相互独立仍未确立；同一被试的所有 run 都留在该被试所在的折中。',
  // Shin2022's source, terms, ethics and consent.
  'The study was reviewed and approved by the Institutional Review Board of Carnegie Mellon University; the paper gives no approval number.':
    '研究经卡内基梅隆大学机构审查委员会审查并批准；论文没有给出批准编号。',
  'The participants gave written informed consent to take part in the study.': '被试签署了参加本研究的书面知情同意。',
  'Figshare record 20383716, version 1, the only version the record lists': 'Figshare 记录 20383716 的第 1 版，也是该记录列出的唯一版本',
  'Closed-loop right/left cursor control with visual feedback; the label is the instructed target.': '带视觉反馈的闭环左右光标控制；标签是指示的目标。',
  'The simulator code is a separate work linked from the data record; the data licence covers the data record.':
    '模拟器代码是数据记录所链接的另一项作品；数据许可覆盖的是数据记录。',
  'EEG1–EEG16 in stored order; the headers carry no channel names': '按存储顺序为 EEG1–EEG16；文件头中没有通道名称',
  'the first second of feedback, read from its recorded start, never extended or padded': '反馈的第一秒，从记录的起点读起，从不延长或填充',
  // eldBETA.
  'The derived MATLAB epochs were not used: their amplitude scale, resampling and exact endpoints are unestablished.':
    '没有使用派生的 MATLAB 分段：它们的幅值尺度、重采样方式与确切端点都尚未确立。',
  'The raw recordings were read with the header calibration applied; the recorded unit code has no independent audit.':
    '读取原始记录时应用了文件头中的定标；记录下来的单位代码没有经过独立审计。',
  'The non-finite values in the continuous recordings are neither located nor explained.': '连续记录中的非有限值既没有定位，也没有得到解释。',
  'The protocol followed the Declaration of Helsinki and was approved by the institutional review board of Tsinghua University, approval number 20210032.':
    '实验方案遵循《赫尔辛基宣言》，经清华大学机构审查委员会批准，批准编号 20210032。',
  'The participants were familiarised with the protocol and gave full written consent before the experiment.':
    '被试在实验前熟悉了实验方案，并签署了完整的书面同意。',
  'Figshare record 18032669, version 3, the latest of the 3 versions the record lists': 'Figshare 记录 18032669 的第 3 版，是该记录列出的 3 个版本中最新的一版',
  'Nine-target SSVEP selection by older adults, recorded in seven blocks per person.': '老年人在九个目标中做 SSVEP 选择，每人记录七个组块。',
  'eldBETA is in SingLEM’s published pretraining list, Table I of the SingLEM paper; BETA, a separate database, is absent from it, as SingLEM’s exposure row on BETA shows.':
    'eldBETA 在 SingLEM 公开的预训练数据清单中，即 SingLEM 论文的表 I；BETA 是另一个数据库，不在这份清单里，SingLEM 在 BETA 上“是否出现在预训练数据中”的那一行写明了这一点。',
  // ZuCo 2.0.
  'The hold covers that one converted run; no timing was corrected and no row removed.': '暂缓只涉及那一个转换后的记录；没有修正任何时间，也没有删除任何数据行。',
  'the exact converter revision, configuration and environment, with its rules for casts, time origin and boundaries':
    '转换程序的确切版本、配置与运行环境，以及它在类型转换、时间原点与边界上的规则',
  'a source-checksummed timing fixture with the original start and end timestamps and the recording’s start and end clocks':
    '一个带源校验和的时间测试样例，含原始的起止时间戳以及记录本身的起止时钟',
  'the canonical mapping of triggers, sentences and runs': '触发信号、句子与 run 之间的规范对应关系',
  'No consent or ethics statement for this dataset has been read yet.': '尚未读取这个数据集的知情同意或伦理声明。',
  'the original terms on OSF': 'OSF 上的原始条款',
  'terms for the text excerpts the stimuli quote': '刺激所引文本片段的条款',
  // What is not published.
  'Participant rows of any kind: identifiers, run and file names, fold assignments, features, fitted models, decision values and predictions; raw signals from any of the three datasets.':
    '任何形式的逐被试数据：标识符、run 与文件名、折的分配、特征、拟合的模型、决策值与预测；三个数据集中任何一个的原始信号。',
  'Per-participant figures from the Shin2022 evidence: window counts per participant and their ranges, and which participants had flat windows.':
    'Shin2022 证据中的逐被试数字：每名被试的时间窗数及其范围，以及哪些被试有平直的时间窗。',
  'The Shin2022 feedback-duration distribution (quantiles and mean) and the per-channel counts of the signal census.':
    'Shin2022 的反馈时长分布（分位数与均值），以及信号普查中逐通道的计数。',
  'eldBETA’s one-participant accuracy and its fixed first-frequency comparator.': 'eldBETA 那一名被试的准确率及其固定的首频率对照。',
  "ZuCo 2.0's converted-run code, row-level timing values and marker counts; no ZuCo 2.0 data are redistributed.":
    'ZuCo 2.0 转换后记录的编号、逐行的时间数值与标记计数；本站不转发任何 ZuCo 2.0 数据。',
  "MOABB's catalog trial and run counts for Shin2022: register content, in the open register file.":
    'MOABB 目录中 Shin2022 的试次数与 run 数：属于开放登记册的内容，写在开放登记册的文件中。',
  'Compute times, storage sizes, hosts and storage locations.': '计算时间、存储大小、主机与存储位置。',
  'The research exports, audits, reviews, protocols and handoffs themselves: each is pinned by SHA-256 in the release manifest and checked by the export, never published, because several carry private storage paths.':
    '研究导出文件、审计、审核、协议与交接文件本身：每一份都在发布清单中以 SHA-256 固定、由导出程序核对，但不发布，因为其中几份含有私有存储路径。',

  /* dataset-checks-update.json */
  // The one-person sentence, once.
  'With one person every score is that person’s, so these three cases publish counts and file facts and hold every score.':
    '只有一个人时，任何分数都是这个人的分数，所以这三个案例只发布计数与文件事实，所有分数暂缓。',
  // Kim beta-range.
  'What does training-free CCA give on 40 frequencies in the beta range?': '不需要训练的 CCA，在 beta 频段的 40 个频率上能做到多少？',
  'Which of 40 flickering targets from 14.0 to 21.8 Hz a participant attends, from a 2-second window, with no training data.':
    '从一个 2 秒的时间窗判断被试注视的是 14.0 至 21.8 Hz 之间 40 个闪烁目标中的哪一个，不用任何训练数据。',
  'mean participant accuracy; with six trials per target for every participant it equals balanced accuracy in this cohort':
    '按被试平均的准确率；每名被试的每个目标都有六个试次，所以在这个队列中它等于平衡准确率',
  'one in 40 balanced targets': '40 个均衡目标中的一个',
  'All 40 task files passed their MD5 checks; the rest and questionnaire files were not acquired. The files store the targets in the order 14 + j + 0.2·i Hz, which differs from the ascending list in MOABB’s metadata, and the references follow the stored order.':
    '全部 40 个任务文件都通过了 MD5 校验；静息与问卷文件没有获取。文件按 14 + j + 0.2·i Hz 的顺序存储各目标，与 MOABB 元数据中的升序列表不同；参考信号按存储的顺序生成。',
  'A separate review admitted the as-stored, scale-invariant CCA arm before any score.':
    '在计算任何分数之前，一次单独的审核认可了按存储原样、不随尺度变化的 CCA 一组。',
  'Every file passed identity, shape, timing, frequency, phase, finite-value and rank checks before any score.':
    '在计算任何分数之前，每个文件都通过了身份、形状、时间、频率、相位、有限值与秩的检查。',
  'All 9,600 outputs were sealed before a separate process scored them; this is process separation, not blinded labels, because the stored class order is known.':
    '全部 9,600 个输出在另一个进程评分之前就已封存；这是进程上的隔离，不是对标签设盲，因为存储的类别顺序是已知的。',
  'An independent audit verified the counts and the bootstrap, and a separate CCA implementation reproduced every fixed fixture.':
    '一次独立审计核对了各项计数与 bootstrap，另一套独立的 CCA 实现复现了每一个固定的测试样例。',
  'An independent review checked the figures and the wording against the audit aggregate.': '一次独立审核对照审计的聚合结果核对了各项数字与措辞。',
  'The scores use amplitudes as stored. CCA does not depend on a common amplitude scale, but common channel gains, freedom from clipping and the saved reference history are not established, so models whose output depends on amplitude are held.':
    '分数使用按存储原样的幅值。CCA 不依赖共同的幅值尺度，但各通道增益是否一致、有无削波以及保存下来的参考历史都没有确立，所以输出依赖幅值的模型暂缓。',
  'The onset is nominal: it is derived from the stored start of each epoch, 2 seconds before the cue, at 1,024 Hz, and no trigger trace is stored.':
    '起点是标称的：由每个分段存储的起始点推出，即提示前 2 秒，采样率 1,024 Hz；文件中没有存储触发信号的波形。',
  'Each participant’s six blocks were recorded on one day.': '每名被试的六个组块都在同一天记录。',
  'The filter runs forward and backward inside each window, so the pipeline is offline and gives no response-time figure.':
    '滤波在每个时间窗内正向与反向各做一遍，所以这个流程是离线的，不给出响应时间的数字。',
  'The pipeline is BCI Report’s fixed recipe; it does not reproduce the paper’s processing.': '流程是 BCI Report 固定的做法，没有复现论文中的处理方式。',
  'Frequencies, people and channels differ from BETA and Wearable-102, so comparing absolute scores across those datasets does not isolate the frequency range.':
    '频率、被试与通道都与 BETA 和 Wearable-102 不同，所以在这些数据集之间比较绝对分数，并不能单独看出频率范围的作用。',
  'The accuracy interval is the participant-bootstrap interval of the difference from the fixed 2.5% chance level, shifted up by 2.5 points; no algorithm was run as chance and no test was run.':
    '准确率的区间，是与固定的 2.5% 随机水平之差的被试 bootstrap 区间，再整体上移 2.5 个点；没有把任何算法当作随机水平来运行，也没有做任何检验。',
  'The independent audit reproduced 60 of 60 fixed fixtures; it did not rerun every trial.': '独立审计复现了 60 个固定测试样例中的全部 60 个；它没有重跑每一个试次。',
  'Forty-target SSVEP speller selection with stimuli from 14.0 to 21.8 Hz, six blocks per person on one day.':
    '四十个目标的 SSVEP 拼写器选择，刺激频率 14.0 至 21.8 Hz，每人六个组块，在同一天记录。',
  'Figshare record 28806815, version 3, the latest of the 3 versions the record lists': 'Figshare 记录 28806815 的第 3 版，是该记录列出的 3 个版本中最新的一版',
  "The paper's Data availability links version 2; the research used version 3 (the latest), which adds a questionnaire. Both versions carry CC BY 4.0 in the licence field.":
    '论文的“数据可用性”部分链接的是第 2 版；研究用的是第 3 版（最新的一版），这一版增加了一份问卷。两个版本的许可字段都是 CC BY 4.0。',
  'The Institutional Review Board at Gwangju Institute of Science and Technology (GIST) approved this experiment (20211201-HR-64-02-04)':
    '光州科学技术院（GIST）机构审查委员会批准了这项实验（20211201-HR-64-02-04）',
  'all subjects were informed of all experimental procedures and signed consent forms': '所有被试都被告知了全部实验流程，并签署了知情同意书',
  'All research data has been consented to by participants, with explicit agreement for public sharing.': '所有研究数据都已获得被试同意，并明确同意公开共享。',
  'The confidentiality clause of the consent forms excludes questionnaire-related personal data; the research acquired the 40 task files only and excluded the questionnaire and rest files.':
    '知情同意书的保密条款把与问卷相关的个人数据排除在外；研究只获取了 40 个任务文件，没有获取问卷与静息文件。',
  'standard CCA, largest canonical correlation over the stored target frequencies': '标准 CCA，在存储的各目标频率中取最大的典型相关',
  'the stored mean of M1 and M2 subtracted; no unit conversion': '减去存储的 M1 与 M2 的均值；不做单位换算',
  'a nominal 2-second window from the stored onset, with no visual-delay shift': '从存储的起点开始的标称 2 秒时间窗，不做视觉延迟平移',
  'second-order Butterworth band-pass, forward and backward, inside the window only': '二阶 Butterworth 带通滤波，正向与反向各一遍，只在时间窗内进行',
  'sine and cosine at each stored target frequency and its second harmonic': '每个存储目标频率及其二次谐波上的正弦与余弦',
  // MIND.
  'What do stored markers support in a motor-imagery release?': '在一份运动想象数据的发布中，存储的标记能支撑什么？',
  'Stored class codes 4 versus 5 and 6 versus 7, each pair classified on its own, from the EEG of a four-class motor-imagery release; the codes are as stored and are not verified imagery.':
    '存储的类别编码 4 对 5 与 6 对 7，每一对单独分类，数据来自一份四类运动想象发布中的 EEG；编码按存储原样使用，并未核实为想象。',
  'Runs in the release: three per record ID.': '发布中的 run：每个记录编号三个。',
  'First runs holding more class markers than the 40 a run requires, excluded whole before any waveform was read; no trial was salvaged from them.':
    '类别标记多于每个 run 所需 40 个的第一个 run，在读取任何波形之前就整个排除；没有从中挽回任何试次。',
  'Runs that passed the frozen finite and non-degenerate checks, which is every one; the checks do not clear artifacts.':
    '通过了冻结的有限值与非退化检查的 run，也就是全部 run；这些检查并不排除伪迹。',
  'Record IDs with three runs each: the primary panel.': '各有三个 run 的记录编号：主面板。',
  'The two record IDs whose first run was excluded keep two runs each: the secondary panel.': '第一个 run 被排除的两个记录编号，各保留两个 run：次要面板。',
  'two whole runs train the pipeline and the third is held out, for each record ID and pair': '对每个记录编号与每一对编码，用两个完整的 run 训练流程，留出第三个',
  'record-ID mean balanced accuracy: out-of-fold trials pooled within each record ID, then record IDs weighted equally':
    '按记录编号平均的平衡准确率：折外试次先在每个记录编号内合并，再对各记录编号等权平均',
  'Descriptive sensitivity ranges for this fixed set of record IDs: the 2.5th and 97.5th percentiles of 20,000 paired record-ID resamples drawn from one shared index table. They are no confidence intervals and no test.':
    '针对这一组固定记录编号的描述性敏感度范围：从同一张共享下标表抽取的 20,000 次配对记录编号重抽样的第 2.5 与第 97.5 百分位。它们不是置信区间，也不是检验。',
  'Each stored-code pair follows one of only two complementary 20-trial label schedules. In the primary panel, 6 record IDs for 4/5 and 5 for 6/7 repeat one schedule across all three runs; the others mix the two. Under the frozen ordinal lookup and its tie rule, this composition explains the ordinal values below 50%: they describe this lookup and schedule rather than a chance floor. No replacement control was fitted after the scores were seen.':
    '每一对存储编码都只遵循两种互补的 20 试次标签排程之一。在主面板中，4/5 有 6 个记录编号、6/7 有 5 个记录编号在全部三个 run 中重复同一种排程；其余的混用两种。在冻结的按位置查表及其平局规则下，这一构成解释了按位置查表的数值为什么低于 50%：它们描述的是这种查表方式与排程，而不是随机水平的下限。看到分数之后，没有另行拟合替代的对照。',
  'one run trains the pipeline and the other is held out': '用一个 run 训练流程，留出另一个',
  'Reported apart with no interval and never pooled with the primary panel; its schedule composition is not printed because with two record IDs it would show each one’s outcome.':
    '单独报告，不附区间，从不与主面板合并；它的排程构成不印出，因为只有两个记录编号时，它会显示出每一个编号的结果。',
  'FIR band-pass over each whole run, zero phase': '对每个完整 run 做 FIR 带通滤波，零相位',
  'shrinkage LDA on the four CSP log-power features': '在四个 CSP 对数功率特征上做收缩 LDA',
  'ICA, interpolation, rereferencing, amplitude clipping, channel search and trial exclusion': 'ICA、插值、重参考、幅值削波、通道搜索与试次剔除',
  'For each of the 20 positions of a pair within a run, the code the training runs hold most often at that position, ties to the lower code.':
    '对一个 run 中某一对编码的 20 个位置，逐个取训练 run 在该位置上最常出现的编码，平局时取较小的编码。',
  'The code the training runs hold most often, ties to the lower code.': '训练 run 中最常出现的编码，平局时取较小的编码。',
  'All out-of-fold outputs were sealed together before a separate scoring process.': '所有折外输出在单独的评分进程之前一并封存。',
  'An independent replay reproduced every hard output, decision value, metric and resampling output exactly.': '一次独立重放精确复现了每一个硬输出、决策值、指标与重抽样输出。',
  'An independent review approved the figures, the four contrasts, the schedule explanation and the wording.': '一次独立审核认可了各项数字、四个对比、对排程的解释与措辞。',
  'Windows run from 1 to 9 seconds after each stored class marker. Most class markers have no cue marker before them and no cue marker sits exactly 2 seconds before its class marker, so the windows do not certify pure imagery.':
    '时间窗从每个存储的类别标记之后 1 秒到 9 秒。大多数类别标记之前没有提示标记，也没有哪个提示标记恰好位于其类别标记之前 2 秒，所以这些时间窗并不能保证只包含想象。',
  'The unit is the record ID. The release describes 30 participants, and whether record IDs and people match one to one was not reconciled, so no claim about people follows.':
    '单位是记录编号。该发布描述有 30 名被试，记录编号与人是否一一对应没有核对清楚，所以由此得不出关于人的结论。',
  'Pair 4/5 above the majority control does not exclude temporal, visual or movement explanations.': '4/5 这一对高于多数类对照，并不排除时间、视觉或动作方面的解释。',
  'Each run is filtered whole, offline and in both directions, so no response-time figure follows.': '每个 run 都是整体、离线、双向滤波，所以得不出响应时间的数字。',
  'The independent replay starts from the sealed epochs; raw preprocessing and the numerical checks were source-reviewed and bound by hash and were not recomputed.':
    '独立重放从封存的分段开始；原始预处理与数值检查经过源代码审核并以哈希绑定，没有重新计算。',
  'The headers leave the reference field empty while the BIDS sidecars describe a parietal reference; the declared calibration and reference were kept as stored and were not verified physiologically.':
    '文件头中的参考字段为空，而 BIDS 附带文件描述的是顶区参考；声明的定标与参考按存储原样保留，没有从生理上核实。',
  'ScienceDB’s terms-of-use page was not read. Aggregate values only; no data are redistributed.': 'ScienceDB 的使用条款页面没有读取。只发布聚合数值，不转发任何数据。',
  'Ethics and consent are quoted from the paper, which names no committee and gives no approval number.': '伦理与知情同意引自论文，论文没有写出委员会名称，也没有给出批准编号。',
  'The intake receipt records no capture time.': '接收记录中没有记下读取时间。',
  'Four-class directional motor imagery of the right upper limb with EEG and fNIRS; here the EEG of stored codes 4 versus 5 and 6 versus 7.':
    '右上肢四个方向的运动想象，同时记录 EEG 与 fNIRS；这里只用存储编码 4 对 5 与 6 对 7 的 EEG。',
  'ScienceDB record 10.57760/sciencedb.34326, record version 4.0.0': 'ScienceDB 记录 10.57760/sciencedb.34326，记录版本 4.0.0',
  'quoted from the research intake receipt of the paper page': '引自研究接收时对论文页面所做的记录',
  'as the research protocol records the dataset description inside the downloaded archive': '按研究协议对所下载压缩包中数据集说明的记录',
  'the licence field of the MOABB dataset adapter': 'MOABB 数据集适配器的许可字段',
  'the schema.org metadata the record page serves': '记录页面提供的 schema.org 元数据',
  'The study protocol was approved by the Ethics Committee. All procedures followed institutional review board (IRB) guidelines and relevant privacy regulations.':
    '研究方案经伦理委员会批准。所有程序都遵循机构审查委员会（IRB）的指南与相关隐私法规。',
  'After confirming that they understood the instructions, all participants voluntarily signed written informed consent forms.':
    '在确认理解了实验说明之后，所有被试都自愿签署了书面知情同意书。',
  // Damm.
  'log band power from an 8–30 Hz filter on each epoch, with fixed shrinkage LDA fitted on the training run only':
    '每个分段经 8–30 Hz 滤波后取对数频带功率，再用只在训练 run 上拟合的固定收缩 LDA',
  'Each random-order run is 916 seconds of 65 EDF channels at 512 Hz: 62 scalp channels, two reference channels and a marker channel. The event stream of each run holds 227 state blocks, and every cue follows a 3-second white screen and a 3-second fixation cross and lasts 6 seconds. The files carry no sample column, so cue samples are reconstructed from the stored onsets.':
    '每个随机顺序的 run 长 916 秒，含 65 个 EDF 通道，采样率 512 Hz：62 个头皮通道、两个参考通道与一个标记通道。每个 run 的事件流有 227 个状态段，每个提示之前先有 3 秒白屏与 3 秒注视十字，提示本身持续 6 秒。文件中没有采样点列，所以提示所在的采样点由存储的起始时间推算出来。',
  'All 62 scalp channels, 1 to 5 seconds after the cue': '全部 62 个头皮通道，提示后 1 至 5 秒',
  'All 62 scalp channels over the full cue interval, 0 to 6 seconds': '全部 62 个头皮通道，覆盖整个提示区间，0 至 6 秒',
  'All 62 scalp channels in the 2 seconds before the cue': '全部 62 个头皮通道，提示前的 2 秒',
  'A fixed central subset of 15 channels, 1 to 5 seconds after the cue': '固定的 15 个中央区通道子集，提示后 1 至 5 秒',
  'The trial index alone, with no signal input': '只用试次序号，不输入任何信号',
  'The trial index modulo five, with no signal input': '试次序号对五取模，不输入任何信号',
  'The previous delivered cue, with no signal input: privileged context that no live system would have': '上一个实际呈现的提示，不输入任何信号：这是任何在线系统都拿不到的特权信息',
  'The primary features with the training labels shuffled once with a fixed seed': '主要特征，训练标签用固定的随机种子打乱一次',
  'Cue samples are reconstructed from the stored onsets; physical trigger timing is not validated.': '提示所在的采样点由存储的起始时间推算；物理触发时间没有经过验证。',
  'The EEG sidecars and the counterbalancing log disagree on which condition came first, so no order effect is inferred.':
    'EEG 附带文件与平衡顺序记录对哪个条件在前说法不一，所以不推断任何顺序效应。',
  'The sequential-order runs were not evaluated: their two annotation tables are byte-identical copies of one file, and no transfer between the random and sequential orders was tested.':
    '顺序呈现的 run 没有评测：它们的两份标注表是同一个文件的逐字节副本；随机顺序与顺序呈现之间的迁移也没有检验。',
  'Five-finger motor imagery cued in random and in sequential order; here the random-order runs only.': '五个手指的运动想象，按随机顺序与按顺序两种方式提示；这里只用随机顺序的 run。',
  'OpenNeuro ds008446 at its latest snapshot, read at a pinned commit of its mirror': 'OpenNeuro ds008446 的最新快照，在其镜像的一个固定提交上读取',
  'The README cites a LICENSE file that the tree at the pinned commit does not hold; the only licence statement is CC0 in dataset_description.json.':
    'README 提到一个 LICENSE 文件，但固定提交的文件树中并没有它；唯一的许可声明是 dataset_description.json 中的 CC0。',
  'UCL Humanities, Arts and Sciences Research Ethics Committee; Approval Number: 26907/001': 'UCL 人文、艺术与科学研究伦理委员会；批准编号：26907/001',
  'No consent statement in README.md, dataset_description.json, CHANGES or the OpenNeuro dataset metadata at the pinned commit; neither the README nor the metadata names a paper, so no paper was read.':
    '固定提交下的 README.md、dataset_description.json、CHANGES 与 OpenNeuro 数据集元数据中都没有知情同意声明；README 与元数据都没有提到论文，所以没有读取论文。',
  // NeBULA.
  'The paper and the Figshare record’s description state 40 participants; the record’s files hold 39 participant archives, and MOABB lists 39.':
    '论文与 Figshare 记录的说明写的是 40 名被试；记录中的文件有 39 个被试压缩包，MOABB 列出的是 39 名。',
  'The source describes executed reaching with an upper-limb exoskeleton; MOABB’s catalog lists the dataset under motor imagery.':
    '数据源描述的是借助上肢外骨骼实际执行的伸手动作；MOABB 的目录把这个数据集列在运动想象之下。',
  'EEG, all 127 channels, 0 to 2 seconds after the Go cue': 'EEG，全部 127 个通道，Go 提示后 0 至 2 秒',
  'EEG, all 127 channels, the 500 milliseconds before the Go cue': 'EEG，全部 127 个通道，Go 提示前的 500 毫秒',
  'EEG, a fixed set of central channels, 0 to 2 seconds after the Go cue': 'EEG，一组固定的中央区通道，Go 提示后 0 至 2 秒',
  'Order diagnostic: trial position and the previous delivered target, with no signal input; privileged context that no live system would have':
    '顺序诊断：试次位置与上一个实际呈现的目标，不输入任何信号；这是任何在线系统都拿不到的特权信息',
  'The primary EEG features with the training labels shuffled once with a fixed seed': '主要的 EEG 特征，训练标签用固定的随机种子打乱一次',
  'EMG, 11 rows, 0 to 2 seconds after the Go cue': 'EMG，11 行，Go 提示后 0 至 2 秒',
  'The 127 EEG features and the 11 EMG features concatenated in a fixed order': '127 个 EEG 特征与 11 个 EMG 特征按固定顺序拼接',
  'EMG, the 500 milliseconds before the Go cue': 'EMG，Go 提示前的 500 毫秒',
  'The EMG features with the training labels shuffled once': 'EMG 特征，训练标签打乱一次',
  'The concatenated features with the same shuffled training labels': '拼接后的特征，使用同样打乱过的训练标签',
  'The original markers hold 25 boundary ties where one trial’s end and the next trial’s start share a sample (7 free, 9 low, 9 high), with no backward overlap. The first parse stopped on them before any feature, model or score; a reviewed fix that accepts a shared boundary reran within the original budget.':
    '原始标记中有 25 处边界重合，即一个试次的结束与下一个试次的开始落在同一个采样点上（自由 7 处、低辅助 9 处、高辅助 9 处），没有向后的重叠。第一次解析在这些重合处停下，当时还没有计算任何特征、模型或分数；一个经过审核、接受共享边界的修正在原定的预算之内重跑。',
  'The EMG files hold 11 channel rows where their metadata states 16; the rows were not relabelled or mapped to muscles.':
    'EMG 文件中有 11 行通道，而其元数据写的是 16 个；这些行没有重新标注，也没有对应到肌肉。',
  'All 356 stored markers of the 89 trials match the EEG marker files in label, order and sample position.':
    '89 个试次的全部 356 个存储标记，在标签、顺序与采样点位置上都与 EEG 标记文件一致。',
  'The EMG and EEG files of each run have equal sample lengths.': '每个 run 的 EMG 与 EEG 文件采样点数相同。',
  'Go is a cue and the reach marker marks reaching the target; neither certifies physical movement onset.': 'Go 是一个提示，到达标记标的是够到目标的时刻；两者都不能证明身体动作开始的时间。',
  'Stored marker agreement between the EEG and EMG files does not certify clock synchronisation or amplitude calibration.':
    'EEG 与 EMG 文件的存储标记相互一致，并不能证明时钟同步或幅值定标。',
  'The other participants’ files in the record are neither acquired nor evaluated.': '记录中其余被试的文件既没有获取，也没有评测。',
  'Reaching to three targets with an upper-limb exoskeleton under free, low and high assistance, with EEG and EMG.':
    '借助上肢外骨骼在自由、低与高三种辅助水平下伸手够向三个目标，同时记录 EEG 与 EMG。',
  'Figshare record 27301629, version 1, the only version the record lists': 'Figshare 记录 27301629 的第 1 版，也是该记录列出的唯一版本',
  "the data descriptor article only; the data licence is the Figshare record's": '只涵盖数据描述论文本身；数据的许可以 Figshare 记录为准',
  'The files’ own dataset description names Zenodo 13627307, which is no registered public record: the Zenodo API, the record page, DataCite and doi.org each return 404. The paper names Figshare alone.':
    '文件自带的数据集说明提到 Zenodo 13627307，但它不是已登记的公开记录：Zenodo API、记录页面、DataCite 与 doi.org 都返回 404。论文只提到 Figshare。',
  'The study’s experimental procedures were approved by the local ethical committee (CER Liguria:784/2022 - DB id 12044).':
    '研究的实验程序经当地伦理委员会批准（CER Liguria:784/2022 - DB id 12044）。',
  'All participants gave consent to participate and openly share the data collected.': '所有被试都同意参加研究，并同意公开共享所采集的数据。',
  // What is not published.
  'Values per person, per record ID, per fold, per run or per trial: identifiers, file and run names, fold assignments, features, fitted models, decision values and predictions; raw signals from any of the four datasets.':
    '逐人、逐记录编号、逐折、逐 run 或逐试次的数值：标识符、文件与 run 名称、折的分配、特征、拟合的模型、决策值与预测；四个数据集中任何一个的原始信号。',
  'Every Damm and NeBULA score: accuracies, balanced accuracies, control values, differences, paired correctness counts and diagnostic fractions; and any comparison of NeBULA’s order diagnostic with its EEG or EMG arms.':
    'Damm 与 NeBULA 的每一个分数：准确率、平衡准确率、对照数值、差值、配对判对计数与诊断比例；以及 NeBULA 的顺序诊断与其 EEG 或 EMG 各组之间的任何比较。',
  'MIND’s pooled metrics, confusion matrices and macro-F1, the secondary panel’s schedule census and differences, the overfull runs’ marker counts and the model-fit counts.':
    'MIND 合并计算的指标、混淆矩阵与宏平均 F1，次要面板的排程统计与差值，超额 run 的标记计数，以及模型拟合次数。',
  'Kim’s per-participant accuracies, the fixture identities of the independent audit and the stored-value ranges of the schema record.':
    'Kim 的逐被试准确率、独立审计所用测试样例的标识，以及结构记录中存储数值的范围。',
  'Compute times, CPU and memory accounting, storage sizes, hosts and storage locations.': '计算时间、CPU 与内存的用量统计、存储大小、主机与存储位置。',
  'The research aggregates, audits, reviews, protocols and handoffs themselves: each is pinned by SHA-256 in the release manifest and checked by the export, never published, because several carry private storage paths.':
    '研究聚合文件、审计、审核、协议与交接文件本身：每一份都在发布清单中以 SHA-256 固定、由导出程序核对，但不发布，因为其中几份含有私有存储路径。',
};

/* Every key is a string of either export or a reworded sentence, and every translation carries its English's digits. */
{
  const strings = new Set<string>();
  const walk = (v: unknown) => { if (typeof v === 'string') strings.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); };
  walk(dq); walk(dc);
  for (const [from, to] of Object.entries(dqReworded)) need(strings.has(from) && !strings.has(to), `a reworded sentence: "${from.slice(0, 60)}"`);
  const reworded = new Set(Object.values(dqReworded));
  const digits = (s: string) => [...s.matchAll(/\d+(?:\.\d+)?/g)].map(m => m[0]).sort().join(' ');
  for (const [en, zh] of Object.entries(dqZh)) {
    need(strings.has(en) || reworded.has(en), `the Chinese map has unknown English: "${en.slice(0, 80)}"`);
    need(digits(en) === digits(zh), `the Chinese for "${en.slice(0, 60)}" carries other digits`);
  }
}

/**
 * One of the export's sentences as the page prints it: the English (curly apostrophes, or the page's rewording) on an
 * English page; on a Chinese page the Chinese, with that English as `original` for the places that print it beside.
 */
export function dqText(en: string, locale: Locale): { text: string; original?: string } {
  const shown = curly(dqReworded[en] ?? en);
  if (locale === 'en') return { text: shown };
  const zh = dqZh[dqReworded[en] ?? en];
  if (zh === undefined) throw new Error(`data-quality.ts: no Chinese for "${en.slice(0, 90)}"`);
  return { text: zh, original: shown };
}
export const dqSay = (en: string, locale: Locale) => dqText(en, locale).text;

/**
 * What is not published, as the page prints it. The MOABB line says the counts are in the open register file only while
 * Shin2022's row there carries them (dqCatalogFinding); until then it names what is withheld and nothing more.
 */
const MOABB_NOT_PUBLISHED = "MOABB's catalog trial and run counts for Shin2022: register content, in the open register file.";
need(dq.not_published.includes(MOABB_NOT_PUBLISHED), 'the MOABB line of what is not published');
const moabbWithheld: Record<Locale, string> = { en: 'MOABB’s catalog trial and run counts for Shin2022.', zh: 'MOABB 目录中 Shin2022 的试次数与 run 数。' };
export const dqNotPublishedShown = (locale: Locale): string[] =>
  dq.not_published.map(x => x === MOABB_NOT_PUBLISHED && !dqCatalogFinding ? moabbWithheld[locale] : dqSay(x, locale));

/** eldBETA's holds, the last with the record's participant count as a figure (the export writes "the other 99"). */
export function eldHolds(locale: Locale): Part[][] {
  const last: Record<Locale, Part[]> = {
    en: ['The record lists ', dqFig(EC.published_participants), ' participants; the other published participants are neither acquired nor evaluated.'],
    zh: ['该记录列出 ', dqFig(EC.published_participants), ' 名被试；其余已发布的被试既没有获取，也没有评测。'],
  };
  return [...E.holds.slice(0, 3).map(h => [dqSay(h, locale)]), last[locale]];
}

/** ZuCo 2.0's case paragraph: the plan's two sentences, no figure (the export's finding without its marker clause). */
export const zucoCase: Record<Locale, string> = {
  en: 'In one converted run of ZuCo 2.0 on NEMAR, some fixation times fall outside the recording. No EEG–text score is computed until the converter’s timing rules and a source-checksummed fixture are available.',
  zh: '在 NEMAR 上 ZuCo 2.0 的一个转换后记录中，有些注视时间落在记录之外。在转换程序的时间规则与带源校验和的测试样例具备之前，不计算任何 EEG–文本分数。',
};

/** What the dataset checks do not publish, as the page prints it (the one-person reason stays with the lead line). */
export const dcNotPublishedShown = (locale: Locale): string[] => dc.not_published.map((x: string) => dqSay(x, locale));

/** Damm's holds, the last with the record's participant count as a figure (the export writes "the other 19"), as eldBETA's. */
export function dammHolds(locale: Locale): Part[][] {
  const last: Record<Locale, Part[]> = {
    en: ['The record lists ', dcFig(damm.design.published_participants), ' participants; the others are neither acquired nor evaluated.'],
    zh: ['该记录列出 ', dcFig(damm.design.published_participants), ' 名被试；其余被试既没有获取，也没有评测。'],
  };
  return [...damm.holds.slice(0, 3).map((h: string) => [dqSay(h, locale)]), last[locale]];
}

/** The page's names for the dataset checks' variant roles, Damm's fingers and NeBULA's assistance levels. */
export const dammRole: Record<string, Record<Locale, string>> = {
  primary: { en: 'Primary', zh: '主要' },
  'window sensitivity': { en: 'Window sensitivity', zh: '时间窗敏感性' },
  'precue control': { en: 'Precue control', zh: '提示前对照' },
  'channel sensitivity': { en: 'Channel sensitivity', zh: '通道敏感性' },
  'order control': { en: 'Order control', zh: '顺序对照' },
  'shuffle sanity check': { en: 'Shuffled-label check', zh: '打乱标签的核查' },
};
need(damm.variants.every((v: any) => dammRole[v.role]), 'a name for every Damm variant role');
export const fingerZh: Record<string, string> = { thumb: '拇指', index: '食指', middle: '中指', ring: '无名指', little: '小指' };
need(damm.design.class_names.every((f: string) => fingerZh[f]), 'a Chinese name for every finger');
export const assistanceZh: Record<string, string> = { free: '自由', low: '低', high: '高' };
need(nebula.design.assistance_conditions.every((a: string) => assistanceZh[a]), 'a Chinese name for every assistance level');
/** MIND's licence statements: who states each, in the page's words. */
export const mindSourceName: Record<string, Record<Locale, string>> = {
  paper: { en: 'Paper', zh: '论文' },
  'archive dataset description': { en: 'Dataset description in the archive', zh: '压缩包中的数据集说明' },
  'MOABB adapter': { en: 'MOABB adapter', zh: 'MOABB 适配器' },
  'ScienceDB record page': { en: 'ScienceDB record page', zh: 'ScienceDB 记录页面' },
};
need(mind.rights.terms.statements.every((s: any) => mindSourceName[s.source]), 'a name for every source of MIND’s licence statements');
/** MIND's coverage steps, by id. */
export const mindStepLabel: Record<string, Record<Locale, string>> = {
  runs_in_release: { en: 'Runs in the release', zh: '发布中的 run' },
  overfull_first_runs: { en: 'Overfull first runs', zh: '超额的第一个 run' },
  runs_evaluated: { en: 'Runs evaluated', zh: '参与评测的 run' },
  primary_panel: { en: 'Primary panel', zh: '主面板' },
  secondary_panel: { en: 'Secondary panel', zh: '次要面板' },
};
need(mind.coverage.every((s: any) => mindStepLabel[s.id]), 'a name for every MIND coverage step');
