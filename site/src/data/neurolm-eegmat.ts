/**
 * NeuroLM's frozen features on EEGMAT's arithmetic and rest (release neurolm-eegmat-update-20261020, owner decision D1
 * of 2026-10-19): a separate panel on the pilot studies page, #neurolm-eegmat, outside its pilot count, and a pointer
 * with no figure from the Arithmetic & rest protocol page. The pilot-studies short answer, description, dek, card and
 * pilot count keep their words; the page refuses to build if one of them carries a NeuroLM figure.
 *
 * Read from the served file and nothing else (neurolm-eegmat-update.json). Every figure is a `Fig` naming that file, so
 * check-workbench.mjs and checks/neurolm-eegmat.mjs re-read it there: the tokenizer arm's 64.49% is the same number as
 * ST-EEGFormer Base's own EEGMAT score in foundation-models-update.json (both 1393/2160, a coincidence), and a figure
 * re-read by field and file cannot pass from the wrong one. Nothing is computed here.
 *
 * The export's own sentences (the representations' definitions, the limitations, the audit boundary, the rights) print
 * as released on the English page; on the Chinese page through `neurolmZh`, keyed by the exact English, so a sentence
 * that changes without its translation fails the build, and a translation must carry exactly its English's numbers.
 *
 * Wording rules, from the readings and the release manifest: the arm is "tokenizer features"; pretraining exposure is
 * "unknown"; the paired interval is read with the pilot-studies sentence ("the interval spans zero, so neither is shown
 * to be better, and the two are not shown to be equivalent"); GPT minus tokenizer is descriptive, from this one cohort;
 * no per-arm interval (the export has none); licences per part; no weights distributed.
 *
 * Glossary (src/data/i18n.ts, check-workbench.mjs `rejected`): pretraining exposure is 是否出现在预训练数据中, never
 * 暴露; a readout head is 分类头; cognitive workload is 脑力负荷; the page names 百分点 once (its short answer) and writes
 * pp after that.
 */
import X from './neurolm-eegmat-update.json';
import { PILOT_PATH } from './entities';
import type { Fig, Fmt } from './entities';
import type { Locale } from './i18n';

export const NEUROLM_JSON = 'neurolm-eegmat-update.json';
export const NEUROLM_ANCHOR = 'neurolm-eegmat';
/** The protocol page that points to the panel, and nothing else does. */
export const NEUROLM_POINTER_PROTOCOL = 'arithmetic-rest';
export const neurolmRelease: { id: string; date: string } = { id: X.release_id, date: X.generated_at };

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`neurolm-eegmat.ts: ${what}`); };
const fig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: NEUROLM_JSON });

// --- What every sentence below rests on; the build refuses an export that no longer says it. ------------------
need(X.schema_version === 'bci-report-neurolm-eegmat-update-v1' && X.release_id === 'neurolm-eegmat-update-20261020', 'the served file is not the NeuroLM EEGMAT release');
const P = X.placement;
need(P.page === PILOT_PATH && P.anchor === NEUROLM_ANCHOR && P.pointer_from === `/protocols/${NEUROLM_POINTER_PROTOCOL}/` && P.counted_in_pilots === false
  && P.leaderboard === false && P.core_matrix_row === false && P.new_dataset_count === 0 && P.new_model_count === 0,
  'a separate panel on the pilot studies page, outside its pilot count, with no row, count or leaderboard place');
const C = X.cohort;
need(C.dataset === 'EEGMAT' && C.version === '1.0.0' && C.people === 36 && C.windows === C.recordings * C.windows_per_recording && C.recordings === C.people * C.conditions
  && C.windows_per_recording * C.window_seconds === C.retained_seconds && C.window_seconds === 2 && C.channels === C.channel_names.length,
  'the cohort: the first minute of each recording in two-second windows, one recording per condition and person');
need(C.folds === 5 && C.fold_sizes_people.length === C.folds && C.fold_sizes_people.reduce((a: number, b: number) => a + b, 0) === C.people
  && /whole participants held out/.test(C.split), 'five folds of whole participants');
need(C.classes.join() === 'pre-task rest,mental arithmetic' && /file name/.test(C.labels), 'rest against arithmetic, labelled from the file names');
const M = X.model;
need(M.name === 'NeuroLM-B' && M.frozen === true && M.fine_tuning === false && M.text_generation === false && M.language_model_head === false
  && M.weights_distributed === false && /supervised/.test(M.transfer), 'NeuroLM-B frozen, with a supervised linear head, no generation and no weights distributed');
const E = X.pretraining_exposure;
need(E.status === 'unknown' && E.checkpoint_stage.status === 'unknown' && E.checkpoint_stage.instruction_tuning_verified === false
  && E.eegmat_instruction_task === 'Workload' && E.instruction_tasks.length === 6 && E.instruction_tasks.includes('Workload')
  && E.published_pretraining_list.includes_eegmat === false, 'exposure unknown: EEGMAT is NeuroLM’s Workload task, one of six instruction tasks, and absent from its published pretraining list');
const A = X.adapter;
need(A.own_adapter === true && A.notch === false && A.official_notch_hz.join() === '50,60' && A.band_pass_hz.length === 2 && A.sampling_hz === C.sampling_hz
  && A.source_sampling_hz === C.source_sampling_hz, 'the pilot’s own adapter, with no notch where NeuroLM’s pipeline has one');
const S = X.separate_from_core;
need(S.core_band_pass === false && S.core_sampling_hz !== A.sampling_hz && S.shared_windows && S.shared_channels && S.shared_fold_rule && S.shared_head,
  'the core matrix filters nothing and resamples elsewhere; windows, channels, folds and head are shared');
const PR = X.probe;
need(PR.head === 'RidgeClassifier' && PR.alpha === 100 && PR.hyperparameter_search === false && PR.sealed_before_scoring === true
  && PR.fits === C.folds * X.arms.length, 'one fixed ridge head per representation and fold, no tuning');
need(X.arms.map((a: { id: string }) => a.id).join() === 'tokenizer_mean,log_bandpower,gpt_mean'
  && X.arms.every((a: { interval_95: unknown }) => a.interval_95 === null), 'three representations, point estimates only');
const ARM = Object.fromEntries(X.arms.map((a: { id: string }) => [a.id, a])) as Record<string, (typeof X.arms)[number]>;
need(ARM.tokenizer_mean.label === 'tokenizer features' && ARM.log_bandpower.label === 'band power' && ARM.gpt_mean.label === 'GPT hidden states',
  'the arms as the export names them');
need(X.chance_level.balanced_accuracy === 0.5 && X.chance_level.macro_f1 === null, 'chance one half for balanced accuracy, none stated for macro-F1');
const I = X.interval;
need(I.kind === 'paired participant bootstrap' && I.level === 0.95 && I.unit === 'participant' && I.fixed_fits === true && I.same_resamples_all_contrasts === true
  && I.arms === 'point estimates only', 'paired participant-bootstrap intervals over fixed fits; none per arm');
const CON = Object.fromEntries(X.paired_contrasts.map((c: { id: string }) => [c.id, c])) as Record<string, (typeof X.paired_contrasts)[number]>;
need(X.paired_contrasts.map((c: { id: string }) => c.id).join() === 'tokenizer-minus-band-power,gpt-minus-tokenizer,gpt-minus-band-power', 'three paired differences');
/** The pilot-studies page's own reading of an interval that spans zero, reused word for word. */
export const SPANS_ZERO = 'the interval spans zero, so neither is shown to be better, and the two are not shown to be equivalent';
const BELOW_ZERO = 'the interval lies below zero; descriptive, from this one cohort';
const spans = (iv: number[]) => iv[0] < 0 && iv[1] > 0;
for (const c of X.paired_contrasts) for (const m of ['balanced_accuracy', 'macro_f1'] as const) {
  const d = c[m];
  need(d.interval_includes_zero === spans(d.interval_95) && d.reading === (d.interval_includes_zero ? SPANS_ZERO : BELOW_ZERO) && d.interval_95[0] <= d.difference && d.difference <= d.interval_95[1],
    `${c.id} ${m}: its reading follows its interval`);
}
const TB = CON['tokenizer-minus-band-power'], GT = CON['gpt-minus-tokenizer'];
need(TB.role === 'question' && TB.a === 'tokenizer_mean' && TB.b === 'log_bandpower' && TB.balanced_accuracy.interval_includes_zero
  && GT.role === 'descriptive' && GT.balanced_accuracy.interval_95[1] < 0 && CON['gpt-minus-band-power'].role === 'descriptive',
  'the panel’s question spans zero; GPT minus tokenizer lies below zero and is descriptive');
// GPT hidden states are not below band power on every metric: their macro-F1 is the higher one (a forbidden reading).
need(ARM.gpt_mean.macro_f1 > ARM.log_bandpower.macro_f1, 'the GPT arm’s macro-F1 is above band power’s, so no sentence says it loses on every metric');
const R = X.rights;
need(R.code.licence === 'MIT' && R.checkpoint.licence === 'CC BY 4.0' && R.checkpoint.weights_distributed === false && R.checkpoint.model_card_terms === false
  && R.dataset.license === 'Open Data Commons Attribution License 1.0' && R.dataset.rightsScope === 'Personal noncommercial research; aggregate results only',
  'the licence of each part, as the export states it');
export const CONSENT_EN = 'Paper reports Bioethics Commission approval (15 August 2018) and written consent from every participant.';
need((R.dataset.privacyReview as string).startsWith(`${CONSENT_EN} `), 'EEGMAT’s ethics and consent statement');
need(/not re-extracted/.test(X.audits.boundary) && X.audits.independent_numerical_audit.status === 'passed' && X.audits.independent_numerical_audit.refits === PR.fits,
  'the audit boundary: heads refitted, features not re-extracted');
const LIMIT_IDS = ['exposure', 'adapter', 'band-power', 'recording-order', 'capacity', 'random-initialisation', 'interval', 'development-cohort', 'ica', 'scope'];
need(X.limitations.map((l: { id: string }) => l.id).join() === LIMIT_IDS.join(), 'the export’s ten limitations');
need(X.not_published.length === 7, 'the not-published list');
// Every number the panel prints near the result must fit the paired chart's axis.
export const PAIRED_DOMAIN: [number, number] = [-0.1, 0.1];
need(X.paired_contrasts.every((c: any) => [c.balanced_accuracy.difference, ...c.balanced_accuracy.interval_95].every((v: number) => v > PAIRED_DOMAIN[0] && v < PAIRED_DOMAIN[1])),
  'every balanced-accuracy difference and bound fits the ±10 pp axis');

// --- Figures --------------------------------------------------------------------------------------------------
const pct2 = (raw: number) => fig(raw, 'pct2'), sgn2 = (raw: number) => fig(raw, 'sgn2'), pp2 = (raw: number) => fig(raw, 'pp2'), n = (raw: number) => fig(raw, 'count');

export interface ArmRow { id: string; label: string; dimension: Fig; ba: Fig; f1: Fig; definition: string; definitionEn: string }
export interface ContrastRow { id: string; label: string; role: string; ba: { d: Fig; lo: Fig; hi: Fig; zero: boolean }; f1: { d: Fig; lo: Fig; hi: Fig; zero: boolean } }

// --- The Chinese for the export's own sentences, keyed by the exact English. ------------------------------------
export const neurolmZh: Record<string, string> = {
  // The question.
  'Do NeuroLM’s frozen EEG features separate rest from mental arithmetic better than band power?':
    'NeuroLM 的冻结 EEG 特征区分静息与心算，比频带功率更好吗？',
  // The arms and their definitions.
  'tokenizer features': '分词器特征',
  'band power': '频带功率',
  'GPT hidden states': 'GPT 隐藏状态',
  'the mean of NeuroLM-B’s 38 tokenizer hidden states per window (two one-second blocks of 19 channels), taken before its vocabulary projection':
    '每个时间窗内 NeuroLM-B 的 38 个分词器隐藏状态（两个一秒片段，每段 19 个通道）的均值，取自词表投影之前',
  '95 absolute log band powers: 19 channels by 5 bands (1–4, 4–8, 8–13, 13–30 and 30–75 Hz), Welch with a one-second Hann window at 200 Hz on the same windows':
    '95 个绝对对数频带功率：19 个通道 × 5 个频带（1–4、4–8、8–13、13–30 与 30–75 Hz），在同样的时间窗上以 200 Hz、一秒 Hann 窗做 Welch 估计',
  'the mean of the 38 final normalised GPT hidden states from the same EEG-only forward pass, which stops before the language-model head':
    '同一次只输入 EEG 的前向计算中 38 个经过末层归一化的 GPT 隐藏状态的均值；这次前向计算止于语言模型头之前',
  // The paired differences and their readings.
  'tokenizer features minus band power': '分词器特征减频带功率',
  'GPT hidden states minus tokenizer features': 'GPT 隐藏状态减分词器特征',
  'GPT hidden states minus band power': 'GPT 隐藏状态减频带功率',
  [SPANS_ZERO]: '区间跨过零，既不能说明哪一方更好，也不能说明两者等效',
  [BELOW_ZERO]: '区间整个低于零；这是描述性结果，只来自这一个队列',
  // The limitations the panel lists (the other four are its caveat paragraph, beside the result).
  'The band-power arm is 95 absolute log band powers (19 channels by 5 bands, 1–75 Hz, Welch at 200 Hz), a different feature set from the core matrix’s Spectral ridge row, which uses log relative spectra from 0.5–45 Hz at 250 Hz.':
    '频带功率一组是 95 个绝对对数频带功率（19 个通道 × 5 个频带，1–75 Hz，200 Hz 下的 Welch 估计），与核心矩阵中 spectral ridge 一行的特征不同：后者用的是 250 Hz 下 0.5–45 Hz 的对数相对频谱。',
  'The 95 band-power and 768 NeuroLM dimensions share one fixed alpha, which does not equalise capacity or effective regularisation.':
    '频带功率的 95 维与 NeuroLM 的 768 维共用同一个固定的 alpha，这并不能让两者的容量或实际的正则化强度相当。',
  'There is no random-initialisation control, so the pilot says nothing about a causal benefit of pretraining.':
    '没有随机初始化的对照，所以这项试点不能说明预训练带来任何因果上的好处。',
  'EEGMAT is a known development cohort, used across this site. Predictions were sealed before scoring for procedural integrity: the labels are in the file names, and each person’s windows train the heads of the other folds.':
    'EEGMAT 是本站各处都在用的已知开发队列。预测在评分前封存，是为了流程上的完整性：标签就写在文件名里，而且每个人的时间窗都参与训练其他各折的分类头。',
  'The source README reports prior ICA cleaning of the published signals.':
    '数据源的 README 说明，已发布的信号事先做过 ICA 清理。',
  'Frozen features with a supervised linear head: no text prompt, generated answer or language-model output entered any score, and nothing here measures instruction tuning, question answering, zero-shot use, cognitive workload, clinical use or online decoding.':
    '冻结特征加有监督的线性分类头：没有任何文本提示、生成的回答或语言模型输出进入任何分数；这里也没有测量指令微调、问答、零样本使用、脑力负荷、临床用途或在线解码。',
  // The audit boundary.
  'The independent audit refitted all 15 heads from the sealed NeuroLM and band-power values and reproduced every score and interval; the NeuroLM features themselves were not re-extracted by a second implementation.':
    '独立审计用封存的 NeuroLM 特征值与频带功率值重新拟合了全部 15 个分类头，复现了每个分数与区间；NeuroLM 特征本身没有由第二套实现重新提取。',
  // Not published.
  'Per-person, per-fold and per-window values of any kind, fold assignments, participant identifiers, condition labels, features, fitted heads, predictions and the sealed prediction files: only equal-person means, paired differences with their intervals and cohort counts are published.':
    '任何逐人、逐折与逐时间窗的数值，折的划分，被试标识，条件标签，特征，拟合好的分类头，预测与封存的预测文件：只发布按被试等权的均值、配对差值及其区间，以及队列计数。',
  'Demographics from the source dataset’s participant file.': '数据源被试信息文件中的人口学信息。',
  'Measured compute: worker times, memory and process counts from the handoff, the receipts and the audits.':
    '实测的计算量：交接文件、运行回执与审计中的运行时间、内存与进程数。',
  // Rights.
  'no weights are distributed; the SHA-256 identifies the checkpoint used and grants nothing':
    '不分发任何权重；SHA-256 只用于标识所用的检查点，不授予任何权利',
  [CONSENT_EN]: '论文报告已获生物伦理委员会批准（2018 年 8 月 15 日），并取得每名被试的书面知情同意。',
};

const numbersOf = (s: string) => [...s.matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0].replace(/,/g, '')).sort().join(' ');
/** The Chinese numbers 2018 年 8 月 15 日 are the English date's; the one sentence whose numbers are reordered by the date. */
const dateZh = (s: string) => s.replace('2018 年 8 月 15 日', '15 August 2018').replace(/August/, '');
for (const [en, zh] of Object.entries(neurolmZh))
  need(numbersOf(en.replace(/August/, '')) === numbersOf(dateZh(zh)), `the Chinese for "${en.slice(0, 60)}" carries exactly its English's numbers`);

/** One of the export's sentences as the page prints it: the English as released; on a Chinese page the Chinese, with the English as `original`. */
export function neurolmText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = neurolmZh[en];
  if (zh === undefined) throw new Error(`neurolm-eegmat.ts: no Chinese for "${en.slice(0, 80)}"`);
  return { text: zh, original: en };
}
const say = (en: string, locale: Locale) => neurolmText(en, locale).text;

/** A label at the head of a cell or row: the export's lower-case term, capitalised in English. */
const head = (s: string, locale: Locale) => locale === 'en' ? s[0].toUpperCase() + s.slice(1) : s;
/** The three representations, in the export's order. */
export const neurolmArms = (locale: Locale): ArmRow[] => X.arms.map((a: any) => ({
  id: a.id, label: head(say(a.label, locale), locale), dimension: n(a.dimension), ba: pct2(a.balanced_accuracy), f1: pct2(a.macro_f1),
  definition: say(a.definition, locale), definitionEn: a.definition,
}));
const part = (d: { difference: number; interval_95: number[]; interval_includes_zero: boolean }) =>
  ({ d: pp2(d.difference), lo: sgn2(d.interval_95[0]), hi: pp2(d.interval_95[1]), zero: d.interval_includes_zero });
/** The three paired differences, in the export's order. */
export const neurolmContrasts = (locale: Locale): ContrastRow[] => X.paired_contrasts.map((c: any) => ({
  id: c.id, label: head(say(c.label, locale), locale), role: c.role, ba: part(c.balanced_accuracy), f1: part(c.macro_f1),
}));
/** The limitations the panel lists as released; the other four are its caveat paragraph, beside the result. */
export const LISTED_LIMITS = ['band-power', 'capacity', 'random-initialisation', 'development-cohort', 'ica', 'scope'];
export const neurolmLimits = (locale: Locale) => LISTED_LIMITS.map(id => {
  const l = X.limitations.find((x: { id: string }) => x.id === id)!;
  return { id, ...neurolmText(l.text, locale) };
});
/**
 * What is not published: the export's first three items. Its fourth (no weights distributed) is the credits' own
 * sentence, said there once; the rest name working files and other releases.
 */
export const neurolmNotPublished = (locale: Locale) => X.not_published.slice(0, 3).map((s: string) => neurolmText(s, locale));
export const neurolmFacts = {
  question: X.question as string, cohort: C, model: M, exposure: E, adapter: A, core: S, probe: PR, interval: I, rights: R,
  audits: X.audits, chance: X.chance_level, schema: X.schema_version as string,
};

// --- The copy, in both languages. Figures are `Fig`s, in the same order in both. ---------------------------------
type Part = string | Fig;
const tb = TB.balanced_accuracy, gt = GT.balanced_accuracy;
const tok = ARM.tokenizer_mean, bp = ARM.log_bandpower, gpt = ARM.gpt_mean;
export const neurolmCopy = {
  en: {
    eyebrow: 'Human · scalp EEG · mental arithmetic and rest · EEGMAT · NeuroLM-B, frozen',
    h2: 'A separate panel: NeuroLM’s frozen features on arithmetic and rest',
    label: 'Locally executed experiment · offline · whole participants held out · not counted among the pilots above, and on no leaderboard',
    lede: (): Part[] => [X.question, ' NeuroLM-B stays frozen. One fixed ridge head (alpha ', n(PR.alpha), ') is fitted on each of three representations of the same ', n(C.windows),
      ' two-second windows from ', n(C.people), ' people, in five participant-held-out folds: ', n(PR.fits), ' fits and no tuning. Scores are means over people, each weighted equally; chance is ',
      pct2(X.chance_level.balanced_accuracy), ' balanced accuracy.'],
    armsCaption: (): Part[] => ['Equal-person means over the ', n(C.people), ' people, each scored by heads fitted without them. Each representation has a point estimate only; the intervals belong to the paired differences below.'],
    colRep: 'Representation', colDim: 'Dimension', colBa: 'Balanced accuracy', colF1: 'Macro-F1',
    armsRegion: 'NeuroLM on EEGMAT, balanced accuracy and macro-F1 of the three representations',
    plotCaption: 'Paired differences in balanced accuracy, in percentage points, over the same people.',
    plotLegend: 'Dot: the mean of the people’s paired differences; line: its 95% participant-bootstrap interval; dashed line: no difference.',
    findLabel: (): Part[] => ['Tokenizer features minus band power, balanced accuracy, paired over the same ', n(C.people), ' people; 95% interval ', sgn2(tb.interval_95[0]), ' to ', sgn2(tb.interval_95[1])],
    findH3: 'The interval spans zero',
    findP: (): Part[] => ['Balanced accuracy: tokenizer features ', pct2(tok.balanced_accuracy), ', matched log band power ', pct2(bp.balanced_accuracy), ', final GPT hidden states ', pct2(gpt.balanced_accuracy),
      '. Macro-F1: ', pct2(tok.macro_f1), ', ', pct2(bp.macro_f1), ' and ', pct2(gpt.macro_f1), '. Tokenizer features minus band power is ', sgn2(tb.difference),
      ' points (paired 95% participant-bootstrap interval ', sgn2(tb.interval_95[0]), ' to ', sgn2(tb.interval_95[1]), `): ${SPANS_ZERO}. GPT hidden states minus tokenizer features is `,
      sgn2(gt.difference), ' points (', sgn2(gt.interval_95[0]), ' to ', sgn2(gt.interval_95[1]), '): descriptive, from this one cohort.'],
    pairedCaption: (): Part[] => ['Paired differences over the same ', n(C.people), ' people, with 95% participant-bootstrap intervals; every contrast uses the same resamples.'],
    colContrast: 'Paired difference', colRole: 'Role',
    role: { question: 'the panel’s question', descriptive: 'descriptive' } as Record<string, string>,
    interval: '95% interval', crossesZero: 'spans zero', belowZero: 'below zero', to: ' to ',
    pairedRegion: 'NeuroLM on EEGMAT, the three paired differences in balanced accuracy and macro-F1',
    caveats: (): Part[] => ['EEGMAT is NeuroLM’s ', E.eegmat_instruction_task, ' task, one of the six instruction tasks in its pinned code, though not one of the ', n(E.published_pretraining_list.datasets),
      ' datasets in its published pretraining list. The training stage of this checkpoint is unresolved, so the backbone may have seen these people: pretraining exposure is unknown. This pilot has its own adapter, which filters ',
      n(A.band_pass_hz[0]), '–', n(A.band_pass_hz[1]), ' Hz and resamples to ', n(A.sampling_hz), ' Hz with no notch filter, where NeuroLM’s own pipeline adds one at ', n(A.official_notch_hz[0]), '/', n(A.official_notch_hz[1]),
      ' Hz; the core Arithmetic & rest matrix filters nothing and resamples to ', n(S.core_sampling_hz), ' Hz, so these scores have their own panel. Rest is recorded before arithmetic, so recording order moves with the label. Intervals come from ',
      n(I.resamples), ' participant resamples of the ', n(PR.fits), ' fixed fits and exclude refit uncertainty.'],
    coreLink: 'The core Arithmetic & rest matrix →',
    limitsH3: 'What else bounds this panel',
    methodsH3: 'How the panel was produced',
    mWindowsH: 'Windows and folds', mProbeH: 'The head', mModelH: 'The model',
    mWindows: (): Part[] => ['The first ', n(C.retained_seconds), ' s of each of the ', n(C.recordings), ' recordings (one at rest and one during serial subtraction per person), cut into ', n(C.windows_per_recording),
      ' two-second windows on ', n(C.channels), ' channels and resampled from ', n(C.source_sampling_hz), ' to ', n(C.sampling_hz), ' Hz. Labels come from the recording condition in the file name. Whole participants are held out: ',
      n(C.fold_sizes_people[0]), '/', n(C.fold_sizes_people[1]), '/', n(C.fold_sizes_people[2]), '/', n(C.fold_sizes_people[3]), '/', n(C.fold_sizes_people[4]), ' people in the five folds.'],
    mProbe: (): Part[] => ['A standard scaler fitted on the training windows only, then a ridge classifier with alpha ', n(PR.alpha), ', balanced class weights and no hyperparameter search: ', n(PR.fits),
      ' fits, each prediction sealed before scoring. The same head reads all three representations.'],
    mModel: (): Part[] => ['NeuroLM-B, ', n(M.parameters), ' parameters in a strict restore of the checkpoint, kept frozen: no fine-tuning, no text generation and no language-model head. Its outputs feed the head trained on the other folds’ labels, a supervised transfer.'],
    armsH: 'The three representations',
    notPubH3: 'Not published here',
    dataUse: 'what this release publishes, on the data-use page →',
    creditsH3: 'Credits, licences and consent',
    rightsLine: X.rights.summary as string,
    eegmatH: 'EEGMAT, the recordings',
    consentH: 'Ethics and consent, as the source states them:',
    scopeH: 'Use:',
    neurolmH: 'NeuroLM, the model',
    paper: 'Paper:', code: 'Code:', at: 'at', ckpt: 'Checkpoint:', sha: 'SHA-256', licence: 'licence',
    ckptLicence: (): Part[] => ['CC BY 4.0, as the licence tag of its Hugging Face repository states; its ', n(R.checkpoint.model_card_bytes), '-byte model card adds no terms.'],
    weights: 'no weights are distributed; the SHA-256 identifies the checkpoint used and grants nothing',
    endorse: 'Derived analysis by BCI Report, aggregates only; not endorsed by NeuroLM’s authors or the data’s authors, and no raw data are redistributed.',
    recordLink: 'Dataset record ↗', datasetPage: 'Dataset page →', creditsLink: 'Credit, licence and consent ↓',
    auditH: 'Independently audited:',
    dataSource: 'Data source:', schema: 'schema',
  },
  zh: {
    eyebrow: '人类 · 头皮 EEG · 心算与静息 · EEGMAT · 冻结的 NeuroLM-B',
    h2: '单独一栏：NeuroLM 冻结特征，心算与静息',
    label: '本站在本地运行的实验 · 离线 · 整名被试留出 · 不计入上面的试点，也不进入任何排行榜',
    lede: (): Part[] => [neurolmZh[X.question], 'NeuroLM-B 保持冻结。在同一批 ', n(C.windows), ' 个两秒时间窗（', n(C.people), ' 名被试）的三种表示上，各拟合一个固定的岭回归分类头（alpha ', n(PR.alpha),
      '），五折、整名被试留出：共 ', n(PR.fits), ' 次拟合，不调参。分数是各被试等权平均的均值；平衡准确率的随机水平为 ', pct2(X.chance_level.balanced_accuracy), '。'],
    armsCaption: (): Part[] => [n(C.people), ' 名被试的等权均值，每名被试都由训练时没有用到其数据的分类头评分。每种表示只有点估计；区间属于下面的配对差值。'],
    colRep: '表示', colDim: '维度', colBa: '平衡准确率', colF1: '宏平均 F1',
    armsRegion: 'EEGMAT 上的 NeuroLM：三种表示的平衡准确率与宏平均 F1',
    plotCaption: '平衡准确率的配对差值，单位 pp，在同一批被试上配对。',
    plotLegend: '点为各被试配对差值的均值，横线为它的 95% 被试 bootstrap 区间，虚线为没有差异。',
    findLabel: (): Part[] => ['分词器特征减频带功率，平衡准确率，在同样 ', n(C.people), ' 名被试上配对；95% 区间 ', sgn2(tb.interval_95[0]), ' 至 ', sgn2(tb.interval_95[1])],
    findH3: '区间跨过零',
    findP: (): Part[] => ['平衡准确率：分词器特征 ', pct2(tok.balanced_accuracy), '，匹配的对数频带功率 ', pct2(bp.balanced_accuracy), '，GPT 末层隐藏状态 ', pct2(gpt.balanced_accuracy),
      '。宏平均 F1：', pct2(tok.macro_f1), '、', pct2(bp.macro_f1), ' 与 ', pct2(gpt.macro_f1), '。分词器特征减频带功率为 ', sgn2(tb.difference),
      ' pp（配对的 95% 被试 bootstrap 区间 ', sgn2(tb.interval_95[0]), ' 至 ', sgn2(tb.interval_95[1]), `）：${neurolmZh[SPANS_ZERO]}。GPT 隐藏状态减分词器特征为 `,
      sgn2(gt.difference), ' pp（', sgn2(gt.interval_95[0]), ' 至 ', sgn2(gt.interval_95[1]), '）：这是描述性结果，只来自这一个队列。'],
    pairedCaption: (): Part[] => ['在同样 ', n(C.people), ' 名被试上的配对差值，附 95% 被试 bootstrap 区间；所有对比都用同一批重抽样。'],
    colContrast: '配对差值', colRole: '作用',
    role: { question: '这一栏要回答的问题', descriptive: '描述性' } as Record<string, string>,
    interval: '95% 区间', crossesZero: '跨过零', belowZero: '整个低于零', to: ' 至 ',
    pairedRegion: 'EEGMAT 上的 NeuroLM：平衡准确率与宏平均 F1 的三个配对差值',
    caveats: (): Part[] => ['EEGMAT 就是 NeuroLM 固定版本代码中六个指令任务之一的 ', E.eegmat_instruction_task, ' 任务，但不在它公开的预训练数据清单（', n(E.published_pretraining_list.datasets),
      ' 个数据集）中。这个检查点处于哪个训练阶段尚未厘清，所以主干网络可能见过这些被试：是否出现在预训练数据中，未知。这项试点有自己的适配流程：',
      n(A.band_pass_hz[0]), '–', n(A.band_pass_hz[1]), ' Hz 滤波，重采样到 ', n(A.sampling_hz), ' Hz，不做陷波滤波，而 NeuroLM 自己的流程会做 ', n(A.official_notch_hz[0]), '/', n(A.official_notch_hz[1]),
      ' Hz 陷波；核心“心算与静息”矩阵不滤波，并重采样到 ', n(S.core_sampling_hz), ' Hz，所以这些分数单独成栏。静息在心算之前记录，所以记录顺序与标签一起变化。区间来自对 ',
      n(PR.fits), ' 个固定拟合结果的 ', n(I.resamples), ' 次被试重抽样，不包含重新拟合带来的不确定性。'],
    coreLink: '核心“心算与静息”矩阵 →',
    limitsH3: '这一栏的其他局限',
    methodsH3: '这一栏是怎样得到的',
    mWindowsH: '时间窗与折', mProbeH: '分类头', mModelH: '模型',
    mWindows: (): Part[] => [n(C.recordings), ' 段记录（每名被试静息与连续减法心算各一段），各取前 ', n(C.retained_seconds), ' 秒，切成 ', n(C.windows_per_recording), ' 个两秒时间窗，',
      n(C.channels), ' 个通道，从 ', n(C.source_sampling_hz), ' Hz 重采样到 ', n(C.sampling_hz), ' Hz。标签来自文件名中的记录条件。整名被试留出：五折分别为 ',
      n(C.fold_sizes_people[0]), '/', n(C.fold_sizes_people[1]), '/', n(C.fold_sizes_people[2]), '/', n(C.fold_sizes_people[3]), '/', n(C.fold_sizes_people[4]), ' 名被试。'],
    mProbe: (): Part[] => ['先用只在训练时间窗上拟合的标准化，再接 alpha 为 ', n(PR.alpha), '、类别平衡、不搜索超参数的岭回归分类器：共 ', n(PR.fits),
      ' 次拟合，每个预测都在评分前封存。三种表示用的是同一个分类头。'],
    mModel: (): Part[] => ['NeuroLM-B，严格恢复检查点后共 ', n(M.parameters), ' 个参数，保持冻结：不微调，不生成文本，不用语言模型头。它的输出送入用其他各折标签训练的分类头，这是有监督迁移。'],
    armsH: '三种表示',
    notPubH3: '这里不发布的内容',
    dataUse: '这次发布的内容，见数据使用页面（英文）→',
    creditsH3: '署名、许可与知情同意',
    rightsLine: `EEGMAT 1.0.0：${R.dataset.license}（Zyma 等，2019；PhysioNet）。NeuroLM 代码：${R.code.licence}。NeuroLM-B 检查点：按其 Hugging Face 元数据为 ${R.checkpoint.licence}；不分发任何权重。`,
    eegmatH: 'EEGMAT：记录数据',
    consentH: '数据源陈述的伦理与知情同意：',
    scopeH: '使用范围：',
    neurolmH: 'NeuroLM：模型',
    paper: '论文：', code: '代码：', at: ' 版本 ', ckpt: '检查点：', sha: 'SHA-256：', licence: '许可',
    ckptLicence: (): Part[] => ['CC BY 4.0，依据其 Hugging Face 仓库的许可标签；它 ', n(R.checkpoint.model_card_bytes), ' 字节的模型卡没有附加任何条款。'],
    weights: neurolmZh['no weights are distributed; the SHA-256 identifies the checkpoint used and grants nothing'],
    endorse: '以上为 BCI Report 的衍生分析，只发布聚合结果；不代表 NeuroLM 作者或数据作者的认可，也不再分发任何原始数据。',
    recordLink: '数据集记录 ↗', datasetPage: '数据集页面 →', creditsLink: '署名、许可与知情同意 ↓',
    auditH: '经过独立审计：',
    dataSource: '数据来源：', schema: 'schema',
  },
};
need(X.rights.summary === 'EEGMAT 1.0.0: Open Data Commons Attribution License 1.0 (Zyma et al., 2019; PhysioNet). NeuroLM code: MIT. NeuroLM-B checkpoint: CC BY 4.0 per its Hugging Face metadata; no weights distributed.',
  'the rights line, as the export words it (its Chinese above follows it)');

/**
 * The panel's results as the panel prints them, unsigned and without units: each arm's balanced accuracy and macro-F1
 * (64.49) and each paired difference and bound (0.60, 5.32). Two decimals only, the panel's precision, so a one-decimal
 * pilot figure that happens to round alike is not mistaken for one.
 */
export const neurolmResultNumbers: Set<string> = new Set([
  ...X.arms.flatMap((a: any) => [a.balanced_accuracy, a.macro_f1]),
  ...X.paired_contrasts.flatMap((c: any) => [c.balanced_accuracy, c.macro_f1]).flatMap((d: any) => [d.difference, ...d.interval_95]),
].map((v: number) => Math.abs(v * 100).toFixed(2)));
/** True when a text names NeuroLM or EEGMAT, or prints one of the panel's results. */
export const carriesNeurolm = (text: string): boolean =>
  /NeuroLM|EEGMAT/i.test(text) || [...text.matchAll(/\d+(?:\.\d+)?/g)].some(m => neurolmResultNumbers.has(m[0]));

/** The pointer on the Arithmetic & rest protocol page: no figure, one link to the panel. */
export const neurolmPointer = {
  en: 'A frozen NeuroLM pilot with its own preprocessing is on the pilot studies page →',
  zh: '另有一项冻结 NeuroLM 的试点，使用自己的预处理流程，见试点研究页面 →',
};
need(Object.values(neurolmPointer).every(s => !/\d/.test(s)), 'the pointer carries no figure');
export const NEUROLM_PANEL_PATH = `${PILOT_PATH}#${NEUROLM_ANCHOR}`;
