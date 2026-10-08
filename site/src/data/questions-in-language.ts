/**
 * Route 3 of the decision-research roadmap, questions in language (owner approval of the results, 2026-10-08): what
 * /topics/questions-in-language/ reads from questions-in-language-update.json and, for the count of published
 * wordings, questions-in-language-wordings.json.
 *
 * Every figure is a leaf of one of those two files (a `Fig`, printed with data-fig and re-read by
 * check-workbench.mjs). What this module adds is words: the plain names of the contrasts the export labels, the flags
 * in words, and the Chinese of the export's English (its limitations and what was not run or not reported), keyed by
 * the exact English so a changed export fails the build instead of printing other words.
 *
 * Rules the page lives under (the handoff of 2026-10-08 and the review manifest): seen questions in their training
 * wording, rewordings and questions the EEG head was never trained on are separate rows, never pooled into one
 * zero-shot number; every entry prints both flags, the margin with them; "unseen" always travels with "unseen by the
 * EEG head, not by the text encoder"; single-seed entries carry no training-run variance and are said so; the
 * pre-run checks are pass or fail and counts only; every BOAS figure sits beside the three gaps, the attribution and
 * "pseudonymised in the public release" (BoasGaps.astro); no per-person, per-fold or per-frequency value.
 */
import ql from './questions-in-language-update.json';
import qlw from './questions-in-language-wordings.json';
import type { Locale } from './i18n';
import { jevStyle, typesafeJev } from './decision-research';
import type { Fig, Fmt } from './entities';

export const QL = 'questions-in-language-update.json';
export const QLW = 'questions-in-language-wordings.json';
export const qlFig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: QL });
export const qlwFig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: QLW });

type Iv = [number, number];
export type QlEntry = {
  key: string; id: string; type: string; kind: 'seen' | 'rewording' | 'unseen'; label: string; people: number; seeds: number;
  single_seed: boolean; estimate: number; interval_95: Iv; unit: 'difference of proportions' | 'log R' | 'difference of AUROC';
  difference: string; margin: string; rule: number; gate: { gate: string; label: string };
  resampled_wording_kinds: Record<string, number>; sentence: string; sentence_as_produced?: string; display_edits: string[];
  chance_corrected?: { chance: number; estimate: number; interval_95: Iv }; r?: { estimate: number; interval_95: Iv };
};
export type QlBlock = {
  block: string; dataset: string; domain: 'ssvep' | 'sleep'; level: 'L0' | 'L1'; level_words: string; people: number; seeds: number;
  gates: { headroom: { pass: boolean; label: string }; triviality: { pass: boolean; label: string; threshold: number } }; entries: QlEntry[];
};
export type QlLevel = { estimate: number; interval_95: Iv; people: number; seeds: number; chance?: number;
  chance_corrected?: { estimate: number; interval_95: Iv } };
export type QlRow = { estimate: number; interval_95: Iv; people: number; seeds?: number; difference: string; margin: string; unit: string; label?: string; note?: string };
export type QlPart = {
  part: string; what: string; dataset: string; label?: string; status_label?: string; single_seed?: boolean;
  declared_likely_inconclusive?: boolean; boas: boolean; gates?: QlBlock['gates']; entries?: QlEntry[];
  gate_note?: string; shuf_derangements_note?: string; sentence_note?: string; token_note?: string;
  rows?: Record<string, QlRow | { label: string; status: string; reason: string }>; levels?: Record<string, unknown>;
  per_rotation_tpl_minus_cca_8_way?: Record<string, QlRow>; notes?: Record<string, string>; note?: string;
  cells?: Record<string, Record<string, QlLevel>>; by_sensor?: Record<string, Record<string, QlRow>>;
};

const R = ql.results['questions-in-language'] as unknown as {
  route: { jev_style: { en: string; zh: string }; jev_source: { company: string; url: string }; origin: { cite: string; url: string; note: string };
           boundary: string; site_text: string };
  design: { margins: { delta_pp: number; p3_ratio: number }; multiplicity: string; expected_inconclusive: string[];
            text_encoders: Record<'bge' | 'minilm' | 'e5', { repo: string; commit: string; licence: string }> };
  primary: { entries_count: number; blocks: QlBlock[]; family_sentences: Record<string, { summary_allowed: boolean; rule: number | null; entries: string[] }> };
  descriptive: Record<string, { levels: Record<string, QlLevel>; contrasts: Record<string, QlLevel>; generalisation_costs?: Record<string, QlLevel>;
    chance_3way_mean?: { stored: number; exact: string }; S15?: Record<string, QlLevel>; seen_auroc_per_predicate?: Record<string, QlLevel>; log_loss?: Record<string, QlLevel> }>;
  pre_run_checks: {
    canaries: {
      revision_3: { pass: boolean; intervals: number; intervals_excluding_chance: number; cells_excluding_chance: { cell: string; side: string }[] };
      revision_4: { pass: boolean; fits: number; intervals: number; intervals_excluding_chance: number; cells_excluding_chance: { cell: string; side: string }[]; centring_diagnostic: string };
      revision_5: { pass: boolean; configurations: number; replicates: number; fits: number; level: number; bootstrap_draws: number; intervals: number;
        intervals_excluding_zero: number; single_head_tests: number; single_head_intervals_excluding_exact_chance: { above: number; below: number; total: number };
        cells_with_single_head_failures_in_both_directions: number };
    };
    owner_override: string; centring_diagnostic: string;
    decision_s0b6: { token_rule: { stops_the_run_for: string[]; rotations_passed: number; multilingual_e5_small: { rotations: number; number_pieces_only_rule_passed: number; full_rule_passed: number } } };
    engineering_amendment_ea1: Record<string, string>;
    numeracy_probe: { spearman_rho: Record<string, number>; pairs: number; activated: boolean; flag_anyway: Record<'L0' | 'L1', { entry: string; difference: string }> };
    gates: {
      headroom: Record<string, { pass: boolean; chance: number; floor: number; ceiling: number }>;
      triviality: Record<string, { pass: boolean; threshold?: number; training_people?: number; label?: string }>;
      readoff_floor: { primary_cells: number; primary_cells_passing: number; secondary_cells: number; secondary_cells_passing: number };
      fit_check: { fits: number; by_domain_and_level: Record<string, { training_epochs: number; fallback_to_60_epochs: boolean; failed_fits: number }> };
      shuffled_eeg_scorer_check: { pass: boolean; cells: number; cells_within_3_se: number; ssvep_cells: number; boas_cells: number };
    };
  };
  secondary: { expected_inconclusive: string[]; none_inconclusive: string; parts: Record<string, QlPart>;
    flip_rates: Record<string, { boas: boolean; TPL: Record<string, { rate: number; people: number }>; DESC: Record<string, { rate: number; people: number }>; between_ID_seeds: { rate: number; people: number } }> };
  boundaries: { protocol: string[]; added_by_results: string[] };
  limitations: string[];
  not_run: { item: string; status: string }[];
  not_reported: { item: string; status: string }[];
  audits: Record<'primary_conformance' | 'secondary_conformance', { verdict: string; checks: number; failed: number }>
    & Record<'primary_numeric', { verdict: string; comparisons: number; numeric_values: number; mismatches: number; entries_recomputed: number }>
    & Record<'secondary_numeric', { verdict: string; comparisons: number; outside_tolerance: number; unexplained: number; entries_recomputed: number }>;
  references: { id: string; cite: string; url: string; role: string }[];
  required_disclosures: { id: string; where: string }[];
};
export const R3 = R;
export const qlRelease = { id: ql.release_id, date: ql.generated_at, schema: ql.schema_version };
export const qlwRelease = { id: qlw.release_id, schema: qlw.schema_version, texts: qlw.texts, license: qlw.license, licenseUrl: qlw.licenseUrl };
if (qlw.release_id !== ql.release_id) throw new Error('questions-in-language.ts: the wordings file belongs to another release');
export const QL_DATASETS = ql.datasets as unknown as Record<'beta' | 'boas' | 'eesm19' | 'openbmi' | 'wearable-ssvep-102',
  { name: string; role: string; license: string; licenseUrl: string; source: string; attribution: string; published_here: string; paper?: string; computed_from?: string }>;
export const QL_BOAS = ql.boas_conditions;
export const DELTA = R.design.margins.delta_pp;
export const RATIO = R.design.margins.p3_ratio;
export const blocks = R.primary.blocks;
export const block = (id: string) => {
  const b = blocks.find(x => x.block === id);
  if (!b) throw new Error(`questions-in-language.ts: no block ${id}`);
  return b;
};
const allPrimary = blocks.flatMap(b => b.entries);
export const parts = R.secondary.parts;
const allSecondary = Object.values(parts).flatMap(p => p.entries ?? []);
/** One entry by its key in the export ("P-sleep-L1/5", "secondary/S2/5"). */
export const entry = (key: string): QlEntry => {
  const hits = [...allPrimary, ...allSecondary].filter(e => e.key === key);
  if (hits.length !== 1) throw new Error(`questions-in-language.ts: ${hits.length} entries ${key}`);
  return hits[0];
};
export const isPp = (e: { unit: string }) => e.unit === 'difference of proportions';
export const isLogR = (e: { unit: string }) => e.unit === 'log R';
export const level = (blockId: string, key: string): QlLevel => {
  const x = R.descriptive[blockId]?.levels[key];
  if (!x) throw new Error(`questions-in-language.ts: no level ${blockId} ${key}`);
  return x;
};
export const part = (id: string): QlPart => {
  const p = parts[id];
  if (!p) throw new Error(`questions-in-language.ts: no secondary part ${id}`);
  return p;
};

type T = { en: string; zh: string };
const tr = (t: T, locale: Locale) => t[locale];

/** The arms by the export's codes, in words. */
const ARM: Record<string, T> = {
  ID: { en: 'question number', zh: '题号' },
  TPL: { en: 'label template', zh: '标签模板' },
  DESC: { en: 'description', zh: '描述' },
  SHUF: { en: 'shuffled templates', zh: '错配模板' },
  NUM: { en: 'numeric code', zh: '数值编码' },
  CCA: { en: 'CCA, no training', zh: 'CCA（无需训练）' },
  'NN(TPL)': { en: 'average of the two neighbouring seen frequencies', zh: '相邻两个已见频率的平均' },
  'TPL(a1)': { en: 'new sentence frame', zh: '新句式' },
  'TPL(a2)': { en: 'synonym', zh: '同义词' },
  'DESC(a3)': { en: 'new description', zh: '新描述' },
  'TPL(train)': { en: 'training wording', zh: '训练问法' },
  'DESC(train)': { en: 'training descriptions', zh: '训练描述' },
};
export const armName = (a: string, locale: Locale) => {
  const n = ARM[a];
  if (!n) throw new Error(`questions-in-language.ts: no name for the arm ${a}`);
  return tr(n, locale);
};
/** The unseen questions, and the wordings they were asked with. */
const UNION: Record<string, T> = {
  asleep: { en: 'asleep', zh: '睡着' },
  NREM: { en: 'N1, N2 or N3 sleep', zh: 'N1、N2 或 N3 期睡眠' },
  light: { en: 'light sleep', zh: '浅睡' },
  hand_movement: { en: 'imagining a hand movement', zh: '想象手部动作' },
};
export const unionName = (u: string, locale: Locale) => {
  const n = UNION[u];
  if (!n) throw new Error(`questions-in-language.ts: no name for the unseen question ${u}`);
  return tr(n, locale);
};
const WORDING: Record<string, T> = {
  implicit: { en: 'implicit name', zh: '隐式名称' },
  explicit: { en: 'explicit name', zh: '显式名称' },
  'new descriptions': { en: 'new descriptions', zh: '新描述' },
};
export const wordingName = (w: string, locale: Locale) => {
  const n = WORDING[w];
  if (!n) throw new Error(`questions-in-language.ts: no name for the wording ${w}`);
  return tr(n, locale);
};

/**
 * A contrast, parsed from the export's label into its two arms (language arm x, reference y) and what is asked. The
 * label is the export's own words; a label this module does not know fails the build.
 */
export type Contrast = { x: string; y: string; asked: T; union?: string; wording?: string };
export function contrast(label: string): Contrast {
  let m = label.match(/^(TPL|DESC) - ID, seen task \((\d+)-way\), training-wording score$/);
  if (m) return { x: m[1], y: 'ID', asked: { en: `seen, ${m[2]}-way`, zh: `已见，${m[2]} 选 1` } };
  m = label.match(/^(TPL\(a[12]\)|DESC\(a3\)) - (TPL|DESC)\(train\), seen task$/);
  if (m) return { x: m[1], y: `${m[2]}(train)`, asked: { en: 'seen, reworded', zh: '已见，改写' } };
  m = label.match(/^TPL - (CCA|NN\(TPL\)|NUM), (8-way unseen|neighbour 3-way)$/);
  if (m) return { x: 'TPL', y: m[1], asked: m[2] === '8-way unseen' ? { en: 'unseen frequency, 8-way', zh: '未见频率，8 选 1' } : { en: 'unseen frequency, neighbour 3-way', zh: '未见频率，相邻 3 选 1' } };
  m = label.match(/^(TPL|DESC) (asleep|NREM|light|hand_movement) \((implicit|explicit|new descriptions)\) vs prior-corrected read-off, log R$/);
  if (m) return { x: m[1], y: 'read-off', union: m[2], wording: m[3], asked: { en: `${UNION[m[2]].en} · ${WORDING[m[3]].en}`, zh: `${UNION[m[2]].zh} · ${WORDING[m[3]].zh}` } };
  m = label.match(/^TPL - SHUF unseen AUROC, mean of the (implicit|explicit) cells$/);
  if (m) return { x: 'TPL', y: 'SHUF', wording: m[1], asked: m[1] === 'implicit'
    ? { en: 'unseen questions, implicit names', zh: '未见问题，隐式名称' } : { en: 'unseen questions, explicit names', zh: '未见问题，显式名称' } };
  throw new Error(`questions-in-language.ts: an entry label this page does not know: "${label}"`);
}

/** The difference flag in words: which arm the interval favours, or that none is shown. */
export function differenceText(e: { difference: string; estimate: number; interval_95: Iv; label?: string; unit: string }, x: string, y: string, locale: Locale): string {
  const zh = locale === 'zh', [lo, hi] = e.interval_95, f = e.difference;
  const shown = lo > 0 || hi < 0;
  if (f === 'no difference shown') { if (shown) throw new Error(`questions-in-language.ts: "${e.label}" says no difference against its interval`); return zh ? '未显示差异' : 'No difference shown'; }
  if (!shown) throw new Error(`questions-in-language.ts: "${e.label}" shows a difference its interval does not`);
  if (f === 'difference: the read-off leaves less error') {
    if (!(lo > 0)) throw new Error(`questions-in-language.ts: "${e.label}" read-off flag against its interval`);
    return zh ? '读出剩余的错误更少' : 'Read-off leaves less error';
  }
  const who = f === 'difference: reference higher' ? y : f === 'difference: language arm higher' ? x : null;
  if (!who || (who === x) !== (lo > 0)) throw new Error(`questions-in-language.ts: "${e.label}" flag "${f}" against its interval`);
  return zh ? `${who} 更高` : `${who} higher`;
}
/** The margin flag in words, the margin printed with it: 2 pp, or the 1.25 ratio of remaining error for log R. */
export function marginText(e: { margin: string; unit: string }, x: string, locale: Locale): string {
  const zh = locale === 'zh', logr = isLogR(e);
  switch (e.margin) {
    case 'equivalent within the margin': return logr ? (zh ? `在 ${RATIO} 的比值界值内等效` : `Equivalent within the ${RATIO} ratio margin`)
      : (zh ? `在 ±${DELTA} pp 内等效` : `Equivalent within ±${DELTA} pp`);
    case 'non-inferior': return logr ? (zh ? `${x} 非劣（比值界值 ${RATIO}）` : `${x} non-inferior at the ${RATIO} ratio`)
      : (zh ? `${x} 非劣（界值 ${DELTA} pp）` : `${x} non-inferior at ${DELTA} pp`);
    case 'margin not met': return logr ? (zh ? `未达到 ${RATIO} 的比值界值` : `${RATIO} ratio margin not met`) : (zh ? `未达到 ${DELTA} pp 界值` : `${DELTA} pp margin not met`);
    case 'not applicable (difference only)': return zh ? '只读差异，不设界值' : 'Difference only: no margin';
  }
  throw new Error(`questions-in-language.ts: unknown margin flag "${e.margin}"`);
}
/** The gate in words. */
export function gateText(g: { gate: string; label: string }, locale: Locale): string {
  const zh = locale === 'zh';
  if (g.gate === 'triviality canary' && g.label === 'passes canary') return zh ? '通过捷径检查' : 'Passes the triviality canary';
  if (g.gate === 'triviality canary' && g.label === 'not run for this task (no declared canary)') return zh ? '本任务未声明捷径检查，未运行' : 'No canary declared for this task: not run';
  if (g.gate === 'headroom' && g.label === 'pass') return zh ? '通过余量门槛' : 'Headroom gate passed';
  throw new Error(`questions-in-language.ts: unknown gate ${g.gate} / ${g.label}`);
}

/**
 * The export's English, in Chinese: the required limitations and what was not run or not reported. Keyed by the
 * exact English; a key the export does not carry, or a text without its Chinese, fails the build (qlText). Each
 * Chinese carries exactly its English's numbers (check-workbench.mjs).
 */
export const qlZh: Record<string, string> = {
  // limitations (boundaries.protocol, the route boundary, boundaries.added_by_results, then the handoff's own)
  "'Unseen' means unseen by the EEG head; the text encoder has read these words, and every token of a held-out frequency also occurs in the training texts.":
    '“未见过”指 EEG 分类头没有见过；文本编码器读过这些词，而且每个留出频率的每个分词也都出现在训练文本中。',
  "Held-out sleep questions are combinations of seen stages ('asleep' is the complement of one), reported as compositional beside the read-off.":
    '留出的睡眠问题都是已见分期的组合（“睡着”是其中一期的补集），作为组合式问题报告，与读出结果并列。',
  'Held-out SSVEP questions name a frequency, which CCA answers without training; interpolation tested, extrapolation secondary.':
    '留出的 SSVEP 问题说的是一个频率，而 CCA 不需要训练就能回答；主分析检验内插，外推只是次要分析。',
  'In the neighbour 3-way the unseen frequency competes against trained detectors for its neighbours; at L1 that test also involves stimulus phase.':
    '在相邻 3 选 1 中，未见过的频率要与两侧相邻频率已训练好的检测器竞争；在 L1 上，这项检验还牵涉刺激相位。',
  'Rewording and unseen results are separate rows and never pooled.':
    '改写的结果与未见问题的结果分行列出，从不合并。',
  'Wordings were written by agents from a fixed brief before scoring, not by users and not tuned.':
    '问法由代理在评分之前按固定说明写成，不是用户写的，也没有调优。',
  'Negation is a boundary probe; location and waveform-shape questions are not tested (no signal-level ground truth held).':
    '否定只是一个边界探针；关于位置和波形形态的问题没有检验（手头没有信号层面的真值）。',
  'Frozen features and a small head; one recipe; not a ranking of text or EEG encoders.':
    '冻结特征加一个小分类头；只有一套训练方案；不是文本编码器或 EEG 编码器的排名。',
  '35 pre-declared comparisons, not corrected for multiplicity.':
    '35 项预先声明的比较，未做多重比较校正。',
  'Questions about negation, location or waveform shape need signal-level ground truth. Writing more prompts does not supply it.':
    '关于否定、位置或波形形态的问题，需要信号层面的真值标注。多写提示词并不能提供这种真值。',
  'Negation was not understood: the negated wordings ("not X", "non-REM sleep") scored as if they asked for X (AUROC 0.02-0.13 against the truth of the negated question; boundary probe S6, never a route sentence).':
    '否定没有被理解：否定问法（“不是 X”“非 REM 睡眠”）的得分，就像在问 X 本身（对被否定问题真值的 AUROC 为 0.02–0.13；边界探针 S6，从不写入路线结论）。',
  'Implicit names of the unseen sleep unions ("asleep", "light sleep") ranked windows in reverse (TPL AUROC 0.317 and 0.244, below 0.5); only the explicit names ("N1, N2, N3 or REM sleep") carried the composition.':
    '未见睡眠组合的隐式名称（“睡着”“浅睡”）把窗口的排序弄反了（TPL 的 AUROC 为 0.317 和 0.244，低于 0.5）；只有显式名称（“N1、N2、N3 或 REM 期睡眠”）承载了组合关系。',
  'The neighbour 3-way at L1 involves stimulus phase as well as frequency; at L0 (a phase-free spectrum) it is the clean frequency test.':
    'L1 上的相邻 3 选 1 同时牵涉刺激相位和频率；在 L0（不含相位的频谱）上，它才是干净的频率检验。',
  'Unseen SSVEP questions compete against trained detectors for their neighbours (seen bias, stated).':
    '未见过的 SSVEP 问题要与相邻频率已训练好的检测器竞争（偏向已见问题，已说明）。',
  'The pre-run permutation canary failed twice (revisions 3 and 4) and was revised by the owner, who overrode revision 4\'s "no further revision"; revision 5 passed. Both failed records are kept and disclosed.':
    '运行前的标签置换金丝雀检查失败了两次（修订 3 和修订 4），由所有者修订；所有者推翻了修订 4 写下的“不再修订”；修订 5 通过。两次失败的记录都保留并披露。',
  'For multilingual-e5-small each held-out frequency is a new token (S0b-6); S8 and S12 also involve new tokens.':
    '对 multilingual-e5-small 来说，每个留出频率都是一个新的分词（S0b-6）；S8 和 S12 也涉及新的分词。',
  'Secondary single-seed entries carry no training-run variance; EESM19 has 20 people; every EESM19 and single-seed entry was declared likely inconclusive.':
    '单种子的次要条目不含训练过程的随机波动；EESM19 只有 20 名被试；每个 EESM19 条目和单种子条目都事先声明为多半无法下结论。',
  'BETA numbers use the published 2-s windows and folds; Wearable-102 numbers are computed from the 2026-09-20 Tsinghua author mirror and claim no physical unit.':
    'BETA 的数字使用已发布的 2 秒窗口和交叉验证折；Wearable-102 的数字由清华大学作者镜像（2026-09-20 获取）计算，不声称任何物理单位。',
  "BOAS: the three gaps and the attribution above; participants are pseudonymised in the public release; no result evaluates Bitbrain's headband or its automatic scoring.":
    'BOAS：三处缺口与署名见上文；被试在公开发布中是假名化的；没有任何结果是在评估 Bitbrain 的头带或它的自动分期。',
  // not_run
  'revision-4 per-person centring diagnostic': '修订 4 的按人中心化诊断',
  'not run (revision 5 part A.2; no fit exists)': '没有运行（修订 5 的 A.2 部分；不存在相应的拟合）',
  'Ying scorer agreement; factorial cognitive sets': 'Ying 评分者一致性；析因设计的认知任务集',
  'deferred (D10)': '推迟（D10）',
  'E1 EEGNet trained jointly with the question vector': '与问题向量联合训练的 E1 EEGNet',
  'deferred (D6)': '推迟（D6）',
  'third text encoder; LEAF-style Q-Former heads; route-1 calibration on language heads; user-written wordings':
    '第三个文本编码器；LEAF 式的 Q-Former 分类头；在语言分类头上做路线 1 的校准；用户撰写的问法',
  'deferred (protocol.deferred)': '推迟（protocol.deferred）',
  'S8 TPL - NN(TPL)': 'S8 TPL − NN(TPL)',
  'not defined (EA-1): the held-out band is contiguous, so no held-out frequency has two seen neighbours':
    '没有定义（EA-1）：留出频段是连续的，所以没有哪个留出频率两侧都是已见过的频率',
  'location and waveform-shape questions': '关于位置和波形形态的问题',
  'not tested: no signal-level ground truth held': '没有检验：手头没有信号层面的真值',
  // not_reported
  'per-union paired contrasts beyond the P3 entries and the per-union levels': 'P3 条目与各组合水平之外的逐组合配对对比',
  'not computed (W1)': '没有计算（W1）',
  'counts of people above or below zero on paired contrasts': '配对对比高于或低于零的被试人数',
  'allowed for BOAS but not computed by stage 2; not added': 'BOAS 允许发布，但阶段 2 没有计算；事后也没有补上',
  'per-person distributions, per-fold values, per-window scores': '逐人分布、逐折数值、逐窗口得分',
  'private by design': '按设计不公开',
};
/** The export's English in the page's language; Chinese pages print it with the English beside it. */
export function qlText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = qlZh[en];
  if (zh === undefined) throw new Error(`questions-in-language.ts: no Chinese for "${en.slice(0, 90)}"`);
  return { text: zh, original: en };
}

/**
 * The vision paper the decision-research plan started from, as the export's references list it. Since the owner's
 * feedback of 2026-10-08 the export carries, by declared text edits, the site's own definition of "Jev-style"
 * (`route.jev_style`, decision-research.ts `jevStyle`) and Jev's source (`route.jev_source`, `typesafeJev`) in place of
 * the sealed build's scope and independence lines; the build fails if the two drift apart.
 */
export const visualJev = R.references.find(r => r.id === 'yu-yao-2026')!;
if (visualJev.cite !== 'Yu & Yao, 2026 · Visual Jev: Accurate and Efficient Decisions from Shared Visual Context' || visualJev.url !== 'https://arxiv.org/abs/2609.25845')
  throw new Error('questions-in-language.ts: the Visual Jev reference is cited as Yu & Yao, 2026');
if (R.route.jev_style.en !== jevStyle.en || R.route.jev_style.zh !== jevStyle.zh
    || R.route.jev_source.company !== typesafeJev.company || R.route.jev_source.url !== typesafeJev.url)
  throw new Error('questions-in-language.ts: the export\'s definition of "Jev-style" or Jev\'s source is not the site\'s');

/**
 * What a route-3 group on a dataset or method page carries under its rows: the export's limitations that bear on every
 * figure in it (what "unseen" means, never pooled, the multiplicity statement), the one its dataset adds, and the two
 * failed canary revisions with the owner's override (the handoff: that disclosure goes wherever route-3 results
 * appear), in the page's language. The topic page carries the rest.
 */
const GROUP_LIMITS: Record<'beta' | 'boas', string[]> = {
  beta: ["'Unseen' means unseen by the EEG head", 'Held-out SSVEP questions name a frequency', 'In the neighbour 3-way the unseen frequency competes',
         'Rewording and unseen results are separate rows', '35 pre-declared comparisons, not corrected for multiplicity',
         'The pre-run permutation canary failed twice'],
  boas: ["'Unseen' means unseen by the EEG head", 'Held-out sleep questions are combinations of seen stages',
         'Rewording and unseen results are separate rows', '35 pre-declared comparisons, not corrected for multiplicity',
         'The pre-run permutation canary failed twice'],
};
export function qlGroupLimits(id: 'beta' | 'boas', locale: Locale): { text: string; original?: string }[] {
  return GROUP_LIMITS[id].map(start => {
    const hits = R.limitations.filter(x => x.startsWith(start));
    if (hits.length !== 1) throw new Error(`questions-in-language.ts: the export has no single limitation starting "${start}"`);
    return qlText(hits[0], locale);
  });
}
