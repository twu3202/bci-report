/**
 * What /topics/data-quality/ reads from data-quality-update.json (owner decisions D1 and D2): Shin2022 as the worked
 * case, with its three arms and the coverage chain from the runs in the release to the windows it is scored on, and
 * eldBETA and ZuCo 2.0 as status cases with no score.
 *
 * Every figure the page prints is a leaf of that file (a `Fig`, printed with data-fig and re-read by the checks). What
 * this module adds is words: the step names of the coverage chain, the arms' names in Chinese, and the Chinese of the
 * export's own English (its arm inputs, caveat, chain steps, checks, holds, consent and ethics statements and what is
 * not published), keyed by the exact English so that a changed export fails the build instead of printing other words.
 * A key that matches no string of the export fails the build too, and so does a translation that does not carry
 * exactly its English's digits.
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
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import dq from './data-quality-update.json';
import fm from './foundation-models-update.json';
import { registerPageBuilt, registerServed } from './files';
import { holds, openRegister } from './releases';
import type { Locale } from './i18n';
import type { Fig, Fmt } from './entities';

export const DQ = 'data-quality-update.json';
export const DQ_PATH = '/topics/data-quality/';
export const DQ_ANCHOR = { shin: 'shin2022', eldbeta: 'eldbeta', zuco: 'zuco2', zucoSource: 'zuco2-source', register: 'register-rows',
                           methods: 'methods-and-limits' } as const;
/** Each case's row in the open register (register-ids.json keeps these ids stable across register versions). */
export const DQ_REGISTER_ROW = { shin2022: 'r-site-shin2022', eldbeta: 'r-site-eldbeta', zuco2: 'r-site-zuco2' } as const;
export const ENDORSEMENT = 'Derived analysis by BCI Report; not endorsed by the authors.';

export type Part = string | Fig;
export const dqFig = (raw: number, fmt: Fmt = 'count'): Fig => ({ raw, fmt, src: DQ });

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`data-quality.ts: ${what}`); };
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
need(dq.placement.page === DQ_PATH && dq.placement.sections.join() === 'shin2022,eldbeta,zuco2'
  && dq.placement.leaderboard === false && dq.placement.core_matrix === false, 'one page, three sections, outside every leaderboard');
need(dq.cases.map(c => `${c.id}:${c.status}`).join() === 'shin2022:released,eldbeta:score_held,zuco2:no_score', 'one worked case and two status cases');
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
};

/* Every key is a string of the export or a reworded sentence, and every translation carries its English's digits. */
{
  const strings = new Set<string>();
  const walk = (v: unknown) => { if (typeof v === 'string') strings.add(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); };
  walk(dq);
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
