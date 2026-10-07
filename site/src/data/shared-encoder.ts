/**
 * Route 2 of the decision-research roadmap, one representation and several questions (2026-10-07, owner
 * approved): what the topic page /topics/shared-encoder/ and the route-2 groups on the OpenBMI, BOAS and EESM19
 * dataset pages (and through them the EEGNet and CBraMod method pages) read from
 * shared-representation-update.json.
 *
 * Every figure is a leaf of that file (a `Fig`, printed with data-fig and re-read by check-workbench.mjs).
 * What this module adds is words: the plain names of the questions and set-ups, the wording of each flag the
 * export carries, and the Chinese of the export's English (limitations, BOAS gaps, not-run items), keyed by the
 * exact English so a changed export fails the build instead of printing other words.
 *
 * Rules the pages live under (handoff and review manifest of 2026-10-07): both flags of every contrast are printed,
 * the margin with its 2 pp; a floor-gated entry is labelled and never counted, and its margin flag is not read; no
 * ranking where intervals overlap; every BOAS figure sits beside the three gaps, the attribution and
 * "pseudonymised in the public release"; no per-person value; E2 sleep travels with its disclosure.
 */
import shared from './shared-representation-update.json';
import type { Locale } from './i18n';
import type { Fig, Fmt } from './entities';

export const SR = 'shared-representation-update.json';
export const srFig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: SR });
/** A contrast's estimate, its interval's lower bound and its upper bound, all already in percentage points. */
export const srPp = (raw: number) => srFig(raw, 'ppr2');
export const srLo = (raw: number) => srFig(raw, 'sgr2');

export type SrEntry = {
  id: string; role: string; level: string; question: string; x: string; y: string; included_people: number;
  estimate_pp: number; interval_95_pp: [number, number]; difference: string; margin: string; wording: string;
  single_seed: boolean; gate: string; gate_attached_by?: string; mean_balanced_accuracy: Record<string, number>;
  label?: string; block?: string; representation?: string; computed_by?: string; note?: string;
};
export type SrLogR = {
  id: string; role: string; level: string; question: string; dedicated: string; read_out_of: string; included_people: number;
  log_r: number; interval_95: [number, number]; r: number; auroc: { dedicated: number; read_out: number };
  difference: string; margin: string; wording: string; single_seed: boolean; gate: string; gate_attached_by?: string;
  read_out_auroc_interval_95: [number, number];
};
export type SrOracle = { id: 'S11-oracle'; question: string; included_people: number; mean: number; gate: string; gate_attached_by: string; read_out_from: string };
export type SrGate = { level: string; question: string; arm: string; mean: number; interval_95: [number, number]; chance: number; floor: number; gate: string };
export type SrArm = { level: string; arm: string; question: string; mean: number; interval_95: [number, number]; chance: number; included_people: number; seeds: number };
export type SrLedgerRow = { parameters: number; parameters_by_part?: { encoder: number; heads: number; conditioning: number };
  mean_steps_per_fit: number; encoder_passes_per_window: number; head_macs_per_window: number; step_time_s: number; batch_time_s: number };
export type SrQuestion = { id: string; question: string; answers: string[]; role: string; windows: number; people: number;
  counts: Record<string, number>; shares: Record<string, number> };
export type SrCanary = { training_people: number; demotes_at: number; questions: { id: string; balanced_accuracy: number; label: string }[] };
export type SrRoute = { sentence: string; supported: boolean; counted: string[]; excluded: Record<string, string>;
  conditioned_head_higher: Record<string, [number, number]>; margin_met_on_every_counted_question: boolean;
  fixed_heads_for_less: boolean; fixed_heads_lower_on: string[]; fixed_heads_higher_on: string[] };
export type SrRights = { name: string; task: string; source: string; version: string; license: string; licenseUrl: string;
  attribution: string; privacyReview: string; reviewedAt: string; reviewBasis: string[]; gaps?: string[]; participants?: string;
  notAnEvaluationOf?: string; ownerApprovalDate?: string };
type Primary = {
  dataset: string; domain: string; people: number; windows: { unit: string; qc_passing: number; scored?: number };
  questions: SrQuestion[]; canary: SrCanary; route_sentence: SrRoute; entries: (SrEntry | SrLogR)[]; gates: SrGate[];
  arms: SrArm[]; ledger: Record<'B-lin' | 'B-sh' | 'C1' | 'A', SrLedgerRow> & { timing: string };
  secondary: (SrEntry | SrLogR | SrOracle)[]; rights: SrRights;
};
export type SrE2 = { level: string; seeds: number; fits: number; run_after_other_results: boolean; disclosure: string;
  chronology: Record<string, string>; resume_checkpoints: { written: number; fits_that_wrote_one: number; left_after_the_run: number };
  gates: (SrGate & { included_people: number })[]; head_parameters: Record<string, number>; lora_parameters: number; note: string; entries: SrEntry[] };
export type SrRoute2 = {
  design: { margin: { delta_pp: number; p3_min_error_removed: number; fixed: string }; multiplicity: string; levels: Record<string, string> };
  datasets: {
    openbmi: Primary;
    boas: Primary & { coherence: { what: string; shares: Record<string, number> }; e2_sleep: SrE2 };
    eesm19: { dataset: string; people: number; seeds: number; label: string; windows: { qc_passing: number; stored: number };
              questions: string[]; stage_only_readout: string; canary: SrCanary; secondary: SrEntry[]; rights: SrRights };
  };
  boas_conditions: { owner_approval: { approved_on: string; decision: string }; gaps: string[]; attribution: string; participants: string;
                     not_an_evaluation_of: string; minimum_cell_people: number; smallest_cell_people: number };
  boundaries: { protocol: string[]; secondary: string; added: string[] };
  not_run: { arm: string; status: string }[];
  not_reported: { item: string; status: string }[];
  audits: Record<'primary' | 'secondary', { checks: number; passed: number; values_recomputed: number; mismatches: number }>
    & { e2_sleep: { checks: number; passed: number; entries_recomputed: number; mismatches: number } };
  literature: { topic: string; url: string }[];
};
export const R2 = shared.results['one-representation'] as unknown as SrRoute2;
export const srRelease = { id: shared.release_id, date: shared.generated_at, schema: shared.schema_version };
export const D = R2.datasets;
export const DELTA = R2.design.margin.delta_pp;
export const P3_CUT = R2.design.margin.p3_min_error_removed;
export const isLogR = (e: SrEntry | SrLogR | SrOracle): e is SrLogR => 'log_r' in e;
export const isPp = (e: SrEntry | SrLogR | SrOracle): e is SrEntry => 'estimate_pp' in e;
export const entry = (list: (SrEntry | SrLogR | SrOracle)[], id: string, q: string, level?: string) => {
  const hits = list.filter(e => e.id === id && e.question === q && (!level || ('level' in e && e.level === level)));
  if (hits.length !== 1) throw new Error(`shared-encoder.ts: ${hits.length} entries ${id} ${level ?? ''} ${q}`);
  return hits[0];
};
export const ppEntry = (list: (SrEntry | SrLogR | SrOracle)[], id: string, q: string, level?: string) => {
  const e = entry(list, id, q, level);
  if (!isPp(e)) throw new Error(`shared-encoder.ts: ${id} ${q} is not a pp contrast`);
  return e;
};
export const arm = (d: Primary, level: string, armId: string, q: string) => {
  const hits = d.arms.filter(a => a.level === level && a.arm === armId && a.question === q);
  if (hits.length !== 1) throw new Error(`shared-encoder.ts: ${hits.length} arms ${level} ${armId} ${q}`);
  return hits[0];
};
export const gate = (d: Primary, level: string, q: string) => {
  const hits = d.gates.filter(g => g.level === level && g.question === q);
  if (hits.length !== 1) throw new Error(`shared-encoder.ts: ${hits.length} gates ${level} ${q}`);
  return hits[0];
};

type T = { en: string; zh: string };
const tr = (t: T, locale: Locale) => t[locale];

/** The questions in plain words; the identifiers stay as the export writes them. */
export const questionName: Record<string, T> = {
  'MI-A': { en: 'imagery or rest', zh: '想象还是静息' },
  'MI-B': { en: 'which hand', zh: '哪只手' },
  'MI-C': { en: 'offline or online run', zh: '离线段还是在线段' },
  'MI-D': { en: 'day 1 or day 2', zh: '第一天还是第二天' },
  'SL-A': { en: 'sleep stage, five stages', zh: '五期睡眠分期' },
  'SL-B': { en: 'awake or asleep', zh: '清醒还是睡着' },
  'SL-C': { en: 'REM or NREM', zh: 'REM 还是 NREM' },
  'SL-D': { en: 'N3 or not', zh: '是否 N3' },
  'SL-E': { en: 'next epoch’s stage differs', zh: '下一帧分期是否改变' },
  'SL-F': { en: 'first or second half of the night', zh: '前半夜还是后半夜' },
};
export const qName = (q: string, locale: Locale) => {
  const n = questionName[q];
  if (!n) throw new Error(`shared-encoder.ts: no name for question ${q}`);
  return tr(n, locale);
};

/** The four set-ups, by the export's codes. */
export const setupName: Record<'A' | 'B-lin' | 'B-sh' | 'C1', T> = {
  A: { en: 'Separate models', zh: '分开的模型' },
  'B-lin': { en: 'Fixed heads', zh: '固定分类头' },
  'B-sh': { en: 'Shared hidden layer', zh: '共享隐藏层' },
  C1: { en: 'Question-conditioned head', zh: '问题条件化分类头' },
};

/** A code as printed: A_MI-B is A(MI-B); a read-out is named in words. */
export function code(c: string, locale: Locale): string {
  const zh = locale === 'zh';
  let m = c.match(/^A_([A-Z]{2}-[A-Z])\(step-matched\)$/);
  if (m) return zh ? `A(${m[1]})，步数匹配` : `A(${m[1]}), step-matched`;
  m = c.match(/^A_([A-Z]{2}-[A-Z])$/);
  if (m) return `A(${m[1]})`;
  m = c.match(/^readout\[(.+)\]$/);
  if (m) return zh ? `${code(m[1], locale)} 的分期读出` : `read-out from ${code(m[1], locale)}`;
  if (c === 'primary K') return zh ? '只训主分析问题' : 'primary questions only';
  if (c === 'K-all') return zh ? '全部问题一起训' : 'all questions trained together';
  return c;
}

/**
 * The difference flag in words. The arm named is the one the interval favours, by its code as the contrast column
 * prints it (S10's flag says "primary K higher"; the page says "B-lin(primary) higher"), and the export's flag must
 * agree with it. A log-R entry and the stage read-out (S11) have flags of their own.
 */
export function differenceText(e: SrEntry | SrLogR, locale: Locale): string {
  const zh = locale === 'zh', flag = e.difference;
  if (flag === 'no difference shown') return zh ? '未显示差异' : 'No difference shown';
  if (isLogR(e)) {
    const t: Record<string, T> = {
      'difference: dedicated model leaves less error': { en: 'Dedicated model leaves less error', zh: '专用模型剩余的错误更少' },
      'difference: read-out leaves less error': { en: 'Read-out leaves less error', zh: '读出剩余的错误更少' },
    };
    if (!t[flag] || (flag.includes('dedicated') !== (e.interval_95[1] < 0))) throw new Error(`shared-encoder.ts: ${e.id} log-R flag "${flag}" against its interval`);
    return tr(t[flag], locale);
  }
  const who = e.estimate_pp > 0 ? e.x : e.y;
  if (/^readout\[/.test(e.y)) {
    const t = e.estimate_pp > 0 ? { en: 'Dedicated head higher', zh: '专用分类头更高' } : { en: 'Read-out from the stage probabilities higher', zh: '由分期概率读出的更高' };
    if (flag !== (e.estimate_pp > 0 ? 'difference: dedicated head higher' : 'difference: stage-posterior readout higher')) throw new Error(`shared-encoder.ts: ${e.id} flag "${flag}"`);
    return tr(t, locale);
  }
  const named = flag.match(/^difference: (.+) higher$/)?.[1];
  // The flag may name the arm's base set-up (A for A_SL-A, C1 for C1(2x)).
  const base = who.replace(/^A_.*$/, 'A').replace(/\(.*\)$/, '');
  const agrees = named === who || named === base || (named === 'primary K' && who === e.y && /\(primary\)/.test(who)) || (named === 'K-all' && who === e.x && /\(K-all\)/.test(who));
  if (!agrees) throw new Error(`shared-encoder.ts: ${e.id} ${e.question} flag "${flag}" does not name ${who}, the arm its interval favours`);
  return zh ? `${code(who, locale)} 更高` : `${code(who, locale)} higher`;
}

/** The margin flag in words, the margin printed with it: 2 pp for a difference, 20% of the remaining error for log R. */
export function marginText(flag: string, kind: 'pp' | 'logr', locale: Locale): string {
  const zh = locale === 'zh';
  const m = kind === 'pp' ? { en: `${DELTA} pp`, zh: `${DELTA} pp` } : { en: `${Math.round(P3_CUT * 100)}%`, zh: `${Math.round(P3_CUT * 100)}%` };
  switch (flag) {
    case 'equivalent within delta': return kind === 'pp' ? (zh ? `在 ±${m.zh} 内等效` : `Equivalent within ±${m.en}`) : (zh ? `在 ${m.zh} 界值内等效` : `Equivalent within the ${m.en} margin`);
    case 'non-inferior': return zh ? `非劣（界值 ${m.zh}）` : `Non-inferior at ${m.en}`;
    case 'margin not met': return zh ? `未达到 ${m.zh} 界值` : `${m.en} margin not met`;
    case 'not applicable (descriptive contrast)': return zh ? '描述性对比，不设界值' : 'No margin: a descriptive contrast';
  }
  throw new Error(`shared-encoder.ts: unknown margin flag "${flag}"`);
}
export const inconclusiveText: T = { en: 'inconclusive at this sample size', zh: '在这个样本量下无法下结论' };
export const floorMarginText: T = { en: 'not read: at floor', zh: '处于下限，不读界值' };

/** The gate in words; for a secondary entry, who attached it. */
export function gateText(g: string, locale: Locale): string {
  const zh = locale === 'zh';
  switch (g) {
    case 'pass': return zh ? '通过门槛' : 'Gate passed';
    case 'floor': return zh ? '处于下限：报告，不计入' : 'At floor: reported, not counted';
    case 'not applicable': return zh ? '不适用：描述性' : 'No gate: descriptive';
  }
  throw new Error(`shared-encoder.ts: unknown gate "${g}"`);
}
const attachedBy: Record<string, T> = {
  'independent secondary audit': { en: 'attached by the independent secondary audit', zh: '由独立的次要审计附上' },
  run: { en: 'attached by the run', zh: '由运行本身附上' },
  'level gate': { en: 'the level’s gate', zh: '所在层级的门槛' },
  'E2-sleep scorer, recomputed by its independent audit': { en: 'attached by the E2-sleep scorer, recomputed by its audit', zh: '由 E2 睡眠评分程序附上，并经其审计重算' },
  'none: descriptive': { en: 'descriptive', zh: '描述性' },
};
export function attachedText(by: string | undefined, locale: Locale): string | null {
  if (!by) return null;
  const t = attachedBy[by];
  if (!t) throw new Error(`shared-encoder.ts: unknown gate source "${by}"`);
  return tr(t, locale);
}

/**
 * The export's English, in Chinese: the required limitations (boundaries), the BOAS gaps and wording, and what was
 * not run or not reported. Keyed by the exact English; a key the export does not carry, or a text without its
 * Chinese, fails the build (srText).
 */
export const srZh: Record<string, string> = {
  // boundaries.protocol
  'The questions are label-backed classification targets from one dataset each, asked by identifier. They are not language prompts and say nothing about unseen questions (route 3).':
    '这些问题都是各自数据集里已有标签的分类目标，按标识提问。它们不是语言提示，对没见过的问题也说明不了什么（那是第 3 条路线）。',
  'MI-A also separates a cue display and position in the run from imagery; MI-B is offline trials only; MI-C and MI-D are about the recording context, not brain states.':
    'MI-A 区分的不只是想象，还有提示画面和在一段记录中所处的位置；MI-B 只用离线试次；MI-C 和 MI-D 关于记录情境，不是大脑状态。',
  'SL-B, SL-C and SL-D are deterministic functions of the 5-stage label. Results on them are about head design, not about new information in the signal.':
    'SL-B、SL-C 和 SL-D 都由 5 期分期标签直接决定。它们上面的结果说明的是分类头的设计，而不是信号里有新的信息。',
  'SL-F is time of night, correlated with stage; SL-E concerns the next 30 s, not a prediction horizon in general.':
    'SL-F 是夜里的时间段，与分期相关；SL-E 只关乎接下来的 30 秒，不代表一般意义上的预测时距。',
  'With identifier-only conditioning, FiLM can differ from the same head without it only by per-question thresholds and signs of the shared hidden units. A null result does not show that language conditioning cannot help.':
    '只用问题标识做条件时，FiLM 与不加条件的同一个分类头之间，只能在各问题的阈值和共享隐藏单元的正负号上有所不同。没有差异，并不说明用语言做条件就帮不上忙。',
  "At E1 the shared encoder is a small CNN whose trunk has 1,200-2,096 parameters; P2 there is 'small-CNN trunk sharing', not foundation-model sharing; E2 on motor imagery ran at one seed, as a secondary arm.":
    '在 E1 层级，共享编码器是一个小 CNN，主干只有 1,200–2,096 个参数；所以那里的 P2 是“小 CNN 主干共享”，不是基础模型共享；E2 在运动想象上只跑了一个随机种子，作为次要分析。',
  'SL-E and SL-F are largely predictable from the current stage; their results are shown beside a stage-only readout.':
    'SL-E 和 SL-F 在很大程度上可以由当前分期预测；它们的结果旁边都给出只用分期读出的结果。',
  'Questions answerable from window statistics or at floor or ceiling are reported but do not count for the route sentence.':
    '能从窗口统计量直接回答的问题，以及处于下限或上限的问题，都照样报告，但不计入路线结论。',
  'Costs were measured on a shared GPU and are indicative; parameter counts, encoder passes and multiply-accumulates are exact.':
    '耗时是在共享 GPU 上测的，只供参考；参数量、编码器前向次数和乘加次数是精确值。',
  'Three datasets (EESM19 as a crude replication), one lab each, and one fixed recipe per encoder: this is not a ranking of encoders or of multi-task methods.':
    '三个数据集（EESM19 只是粗略重复），各来自一个实验室，每种编码器一套固定的训练方案：这不是编码器或多任务方法的排名。',
  'BOAS has natural stage prevalence but is one population and one PSG system; balanced accuracy across people is not a deployment error rate.':
    'BOAS 保留了自然的分期比例，但只是一个人群、一套多导睡眠图设备；跨被试的平衡准确率不是部署时的错误率。',
  // boundaries.added
  'Per-person balanced accuracy averages people equally; it compares arms and is not a deployment error rate.':
    '逐人计算的平衡准确率对每名被试同等加权；它用来比较各设置，不是部署时的错误率。',
  "The OpenBMI numbers here use route 2's own 2-s windows, label-free high-pass and person-disjoint folds; they are not comparable with the site's OpenBMI cross-session calibration figures.":
    '这里的 OpenBMI 数字用的是路线 2 自己的 2 秒窗口、不依赖标签的高通滤波和被试不重叠的交叉验证折；不能与本站 OpenBMI 跨会话校准的数字相比。',
  "EESM19 full (S13) uses every stored epoch that passes the published core rules at its natural stage mix; it is a different protocol from the site's balanced sleep-scalp subset.":
    'EESM19 完整版（S13）用了所有通过已发布核心规则的存储数据帧，保持自然的分期比例；它与本站类别平衡的头皮睡眠子集是不同的协议。',
  'On EESM19 (S13) no stage-only readout was computed (S11 is defined on BOAS only), so its SL-E and SL-F entries must carry the sentence that both questions are largely predictable from the current stage.':
    'EESM19（S13）上没有计算只用分期的读出（S11 只在 BOAS 上定义），所以它的 SL-E 和 SL-F 条目都要附上这句话：这两个问题在很大程度上可以由当前分期预测。',
  'E2 sleep ran after every other result was known; its design and run condition were fixed at the freeze, and nothing about it was chosen from results.':
    'E2 睡眠是在其他所有结果都已知之后才运行的；它的设计与运行条件在冻结时就已确定，没有任何一项是根据结果选的。',
  // boas_conditions
  'The consent statement does not say whether participants agreed to public sharing or secondary use.':
    '知情同意声明没有说明被试是否同意公开共享或二次使用。',
  "The ethics and consent statements come from the publisher's dataset description and README. No peer-reviewed paper describes BOAS.":
    '伦理与知情同意的陈述只来自发布者的数据集说明与 README，没有任何同行评审论文描述 BOAS。',
  'The ethics reference was added to the release in version 1.1.1 (May 2025), and the release does not say when it was granted relative to the recordings.':
    '伦理批件编号是在 1.1.1 版（2025 年 5 月）才加入发布的，发布中没有说明它是在记录之前还是之后批准的。',
  "No result here evaluates Bitbrain's headband or its automatic sleep scoring; neither is used.":
    '这里没有任何结果是在评估 Bitbrain 的头带或它的自动睡眠分期；两者都没有使用。',
  // The two statements BOAS's rights record carries (privacyReview), printed on its dataset page.
  'The dataset description states approval by the Comité de Ética de la Investigación de la Comunidad Autónoma de Aragón (C.I. PI24/046).':
    '数据集说明写明，研究经阿拉贡自治区研究伦理委员会（Comité de Ética de la Investigación de la Comunidad Autónoma de Aragón）批准（C.I. PI24/046）。',
  'The README states that participants, adult members of the general population, provided written informed consent.':
    'README 写明，被试是来自普通人群的成年人，都签署了书面知情同意。',
  // not_run
  'Ying 2025 multi-night sleep (S9)': 'Ying 2025 多晚睡眠（S9）',
  'deferred by the owner before the freeze; nothing was run': '冻结之前由所有者推迟；没有运行任何东西',
  'E2 on motor imagery at three seeds': '三个随机种子的 E2 运动想象',
  'not scheduled: E2 ran at one seed as a secondary arm, so the E1 sharing contrast keeps the label small-CNN trunk sharing':
    '没有安排：E2 只跑了一个随机种子，作为次要分析，所以 E1 上的共享对比仍标为“小 CNN 主干共享”',
  // not_reported
  'The ridge reference row on frozen CBraMod features (G-1)': '冻结 CBraMod 特征上的岭回归参考行（G-1）',
  'Declared in the frozen draft, never implemented, and not computed afterwards: it would be new fits, and each choice it leaves open would be made after every result is known. No decision uses it.':
    '冻结的草案里列了它，但从未实现，事后也没有补算：那需要新的拟合，而它留下的每个选择都会在所有结果已知之后才做。没有任何结论用到它。',
  'Arm-level results of the secondary arms (interval, AUROC, log loss, per-seed means)': '次要设置在单个设置层面的结果（区间、AUROC、log loss、各随机种子的均值）',
  'Not produced by the frozen stage 2; each secondary contrast carries the mean balanced accuracy of its two arms.':
    '冻结的阶段 2没有产出这些；每个次要对比都附上了它两个设置的平均平衡准确率。',
  'P3 at E2': 'E2 层级上的 P3',
  'Not declared for the E2-sleep block, so its five wake-or-sleep fits feed no contrast.':
    'E2 睡眠这一组没有预先声明这项对比，所以它的五个“清醒还是睡着”拟合不进入任何对比。',
  'Counts of people whose paired contrast is above or below zero': '配对对比高于或低于零的被试人数',
  'Allowed by the BOAS review, not computed by the frozen stage 2, and not added afterwards.':
    'BOAS 的权利审核允许发布，但冻结的阶段 2没有计算，事后也没有补上。',
};
/** The export's English in the page's language; Chinese pages print it with the English beside it. */
export function srText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = srZh[en];
  if (zh === undefined) throw new Error(`shared-encoder.ts: no Chinese for "${en.slice(0, 90)}"`);
  return { text: zh, original: en };
}

/**
 * BOAS's two statements as its rights record gives them (privacyReview), read by their opening words so a changed
 * record fails the build. The register entry on /datasets/boas/ prints them with the three gaps.
 */
export function boasStatements(): { ethics: string; consent: string } {
  // A sentence ends at a full stop after a lower-case letter or a bracket, so "(C.I. PI24/046)" stays whole.
  const sentences = D.boas.rights.privacyReview.split(/(?<=[a-z)]\.)\s+(?=[A-Z])/);
  const one = (start: string) => {
    const hits = sentences.filter(s => s.startsWith(start));
    if (hits.length !== 1) throw new Error(`shared-encoder.ts: BOAS's rights record has no single sentence starting "${start}"`);
    return hits[0];
  };
  const ethics = one('The dataset description states approval by'), consent = one('The README states that participants');
  if (!/PI24\/046/.test(ethics) || !/written informed consent/.test(consent)) throw new Error('shared-encoder.ts: BOAS ethics reference or written consent missing');
  return { ethics, consent };
}

/**
 * What a route-2 group on a dataset or method page carries under its rows, in the page's language: the export's
 * limitations that bear on every figure in it (identifier questions; balanced accuracy is not a deployment rate; the
 * dataset's own boundary), and the multiplicity rule. The topic page carries the rest.
 */
const GROUP_LIMITS: Record<'openbmi' | 'boas' | 'eesm19', string[]> = {
  openbmi: ['The questions are label-backed classification targets', 'Per-person balanced accuracy averages people equally',
            "The OpenBMI numbers here use route 2's own"],
  boas: ['The questions are label-backed classification targets', 'Per-person balanced accuracy averages people equally',
         'SL-E and SL-F are largely predictable from the current stage'],
  eesm19: ['The questions are label-backed classification targets', 'EESM19 full (S13) uses every stored epoch',
           'On EESM19 (S13) no stage-only readout was computed'],
};
export function groupLimits(id: 'openbmi' | 'boas' | 'eesm19', locale: Locale): { text: string; original?: string }[] {
  const all = [...R2.boundaries.protocol, ...R2.boundaries.added];
  return GROUP_LIMITS[id].map(start => {
    const hits = all.filter(x => x.startsWith(start));
    if (hits.length !== 1) throw new Error(`shared-encoder.ts: the export has no single limitation starting "${start}"`);
    return srText(hits[0], locale);
  });
}
/** The margin and multiplicity rule every route-2 group states, in words the page writes (no export sentence says it this short). */
export const groupRule: T = {
  en: `A contrast shows a difference when its paired 95% interval excludes zero; it is equivalent when the whole interval lies within ±${DELTA} pp, the margin fixed before any result. No multiplicity correction; no ranking where intervals overlap.`,
  zh: `配对 95% 区间不含零时，才算显示出差异；整个区间落在 ±${DELTA} pp 以内（这个界值在任何结果出来之前就已定下）时，才算等效。不做多重比较校正；区间重叠时不排名。`,
};

/** The BOAS conditions as a group or section prints them: the three gaps, the participants' wording, what is not evaluated, the credit. */
export function boasConditions(locale: Locale) {
  const C = R2.boas_conditions;
  if (C.gaps.length !== 3) throw new Error('shared-encoder.ts: BOAS has three stated gaps');
  return {
    gaps: C.gaps.map(g => srText(g, locale)),
    participants: locale === 'zh' ? '被试在公开发布中是假名化的。' : `Participants are ${C.participants}.`,
    notEvaluated: srText(C.not_an_evaluation_of, locale),
    attribution: C.attribution,
    approvedOn: C.owner_approval.approved_on,
  };
}
