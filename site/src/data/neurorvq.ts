/**
 * NeuroRVQ's frozen backbone on three tasks (release neurorvq-update-20261028, owner decisions D14 and D19 of 2026-10-28):
 * a separate panel on the pilot studies page, #neurorvq, after NeuroLM's and outside the pilot count, with blocks for
 * EEGMAT's arithmetic and rest, motor imagery against rest and P300 target against non-target, and pointers with no
 * figure from those three protocol pages. The pilot-studies short answer, description, dek, card and pilot count keep
 * their words; the page refuses to build if one of them carries a NeuroRVQ figure.
 *
 * Read from the served file and nothing else (neurorvq-update.json). Every figure is a `Fig` naming that file, so
 * check-workbench.mjs and checks/neurorvq.mjs re-read it there by field: at one decimal the panel's 66.34% and 64.82%
 * would print as REVE LoRA's 66.3% and BrainOmni LoRA's 64.8%, and the motor-imagery band power's 58.83% as BrainOmni's
 * and CodeBrain's 58.8% on the same protocol, so every level, difference and bound prints at two decimals, never at one
 * and never as a whole percent. Nothing is computed here.
 *
 * The export's own sentences (the arm definitions, the limitations, the audit boundaries, the gates of the protocols
 * not run) print as released on the English page; on the Chinese page through `neurorvqZh`, keyed by the exact
 * English, so a sentence that changes without its translation fails the build, and a translation must carry exactly
 * its English's numbers.
 *
 * Where each limitation prints follows the blocks' `caveat_keys`, never a typed list: one in every block's keys is the
 * panel's (the model's identity, or the panel's limits); one that only some blocks name prints once, beside the first
 * block that names it. `rights` is placed by name, with the model's credit. The leaderboard statement prints once, from
 * `separation`.
 *
 * EEGMAT's shared facts are stated once on the page, by the NeuroLM panel above, beside its evidence: rest recorded
 * before arithmetic, the source's prior ICA cleaning, EEGMAT a known development cohort, and the dataset's credit,
 * licence and consent (the three EEGMAT rights records are the same record, checked below). This panel's EEGMAT block
 * names `eegmat-order` and `development-cohort` in one line that points there and keeps the consequence its own export
 * adds; its EEGMAT credit points to the NeuroLM credits and keeps the licence link.
 *
 * Wording, from the release manifest: the arms are "NeuroRVQ backbone", "band power" and "temporal means"; the variant
 * is the released backbone with parameter-free branch normalisation and mean-token pooling, with no version label; the
 * EEGMAT interval takes the pilot-studies sentence and the other two "descriptive, from this one cohort"; exposure is
 * unknown for all three datasets; code and weights CC BY-NC 4.0; no weights distributed.
 */
import X from './neurorvq-update.json';
import { PILOT_PATH } from './entities';
import type { Fig, Fmt } from './entities';
import type { Locale } from './i18n';
import { CONSENT_EN, NEUROLM_ANCHOR, SPANS_ZERO, neurolmCopy, neurolmFacts, neurolmZh } from './neurolm-eegmat';

export const NEURORVQ_JSON = 'neurorvq-update.json';
export const NEURORVQ_ANCHOR = 'neurorvq';
export const NEURORVQ_PANEL_PATH = `${PILOT_PATH}#${NEURORVQ_ANCHOR}`;
export const neurorvqRelease: { id: string; date: string } = { id: X.release_id, date: X.generated_at };

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`neurorvq.ts: ${what}`); };
const fig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: NEURORVQ_JSON });

// --- What every sentence below rests on; the build refuses an export that no longer says it. ------------------
need(X.schema_version === 'bci-report-neurorvq-update-v1' && X.release_id === 'neurorvq-update-20261028', 'the served file is not the NeuroRVQ release');
const P = X.placement;
need(P.page === PILOT_PATH && P.anchor === NEURORVQ_ANCHOR && P.after === NEUROLM_ANCHOR && P.counted_in_pilots === false && P.leaderboard === false
  && P.core_matrix_row === false && P.foundation_encoder_table === false && P.method_page === false && P.new_dataset_count === 0 && P.new_model_count === 0
  && P.pointers_carry_figures === false, 'a separate panel after NeuroLM’s on the pilot studies page, outside its pilot count, with no row, count, method page or leaderboard place');
/** The protocol pages that point to the panel, with no figure, and nothing else does. */
export const NEURORVQ_POINTER_PROTOCOLS: string[] = P.pointers_from.map((p: string) => {
  const m = p.match(/^\/protocols\/([a-z0-9-]+)\/$/);
  need(m, `the pointer page ${p} is a protocol page`);
  return m![1];
});
const M = X.model;
need(M.name === 'NeuroRVQ' && M.frozen === true && M.fine_tuning === false && M.weights_distributed === false && /^supervised/.test(M.transfer)
  && M.variant === 'the released backbone with parameter-free branch normalisation and mean-token pooling', 'NeuroRVQ frozen, read by a supervised head, the variant that ran, no weights distributed');
need(M.restore.strict === true && M.restore.coverage === 1 && M.restore.unused_checkpoint_tensors === M.restore.checkpoint_tensors - M.restore.trained_tensors
  && M.authors_wrapper.strict_restore === false && M.authors_wrapper.missing_normalisation_tensors === 8, 'a strict restore of the trained tensors; the authors’ wrapper missing eight normalisation tensors');
need(M.branch_normalisation.parameter_free === true && M.pooling.dimension === M.pooling.branches * M.pooling.branch_width && M.pooling.branches === M.branch_normalisation.branches,
  'parameter-free branch normalisation; the pooled values are the branches joined');
const E = X.pretraining_exposure;
need(E.status === 'unknown' && E.datasets.length === 3 && E.datasets.every((d: { status: string; named_in_list: boolean }) => d.status === 'unknown' && d.named_in_list === false)
  && E.published_pretraining_list.corpora === E.published_pretraining_list.public + E.published_pretraining_list.proprietary && E.per_checkpoint_list_published === false,
  'exposure unknown for all three datasets, none named in the published list');
const PR = X.probe;
need(PR.head === 'RidgeClassifier' && PR.alpha === 100 && PR.solver === 'cholesky' && PR.class_weight === 'balanced' && PR.hyperparameter_search === false
  && PR.fine_tuning === false && PR.sealed_before_scoring === true && /training participants’ windows only/.test(PR.scaler), 'one fixed ridge head per fold, no tuning, predictions sealed');
const I = X.interval;
need(I.kind === 'paired participant bootstrap' && I.level === 0.95 && I.unit === 'participant' && I.fixed_fits === true && I.arms === 'point estimates only' && I.metric === 'balanced accuracy',
  'paired participant-bootstrap intervals on balanced accuracy, over fixed fits; none per arm');
need(X.chance_level.balanced_accuracy === 0.5 && X.chance_level.macro_f1 === null, 'chance one half for balanced accuracy, none stated for macro-F1');
const R = X.rights;
need(R.code.licence === 'CC BY-NC 4.0' && R.weights.licence === 'CC BY-NC 4.0' && R.weights.weights_distributed === false && R.weights.same_file_as_code === true,
  'code and weights CC BY-NC 4.0, the same licence file, no weights distributed');

/** The pilot-studies page's reading of an interval below zero, beside the one for an interval that spans zero. */
const BELOW_ZERO = 'the interval lies below zero; descriptive, from this one cohort';
// The blocks differ in shape (EEGMAT's recordings, P300's balance), so they are read loosely and checked here.
type Block = any;
const BLOCKS = X.blocks as Block[];
need(BLOCKS.map(b => b.id).join() === 'eegmat,mi-rest,p300-target', 'three blocks: EEGMAT, motor imagery, P300');
const folds = BLOCKS[0].cohort.folds;
const spans = (iv: number[]) => iv[0] < 0 && iv[1] > 0;
for (const b of BLOCKS) {
  const d = b.paired_difference, arms = b.arms;
  need(b.protocol_page === `/protocols/${b.protocol}/` && NEURORVQ_POINTER_PROTOCOLS.includes(b.protocol) && b.core_track.core_rows === false && b.core_track.same_people === true,
    `${b.id}: its protocol page points here; no core row`);
  need(b.cohort.folds === folds && /whole participants held out/.test(b.split) && b.fits === folds * arms.length, `${b.id}: five folds of whole participants, one fit per arm and fold`);
  need(arms[0].id === 'neurorvq' && arms[0].label === 'NeuroRVQ backbone' && arms[0].dimension === M.pooling.dimension && arms.every((a: any) => a.interval_95 === null),
    `${b.id}: the backbone first, its pooled values, point estimates only`);
  need(d.a === 'neurorvq' && arms.some((a: any) => a.id === d.b) && d.role === 'primary' && d.metric === 'balanced_accuracy', `${b.id}: one primary paired difference on balanced accuracy`);
  need(d.interval_includes_zero === spans(d.interval_95) && d.reading === (d.interval_includes_zero ? SPANS_ZERO : BELOW_ZERO) && d.interval_95[0] <= d.difference && d.difference <= d.interval_95[1]
    && (d.interval_includes_zero || d.interval_95[1] < 0), `${b.id}: its reading follows its interval`);
  need(b.audit.status === 'pass' && b.audit.heads_refit === b.fits, `${b.id}: the audit refitted every head`);
}
const [BE, BM, BP] = BLOCKS;
need(BE.input_chain.kind === 'own chain' && BM.input_chain.kind === 'core prepared windows' && BP.input_chain.kind === 'core prepared windows'
  && BE.cohort.window_seconds === 2 && BM.cohort.window_seconds === 2 && BP.cohort.window_seconds === 1
  && BE.cohort.windows === BE.cohort.recordings * BE.cohort.windows_per_recording && BE.cohort.windows_per_recording * BE.cohort.window_seconds === BE.cohort.retained_seconds
  && BP.cohort.windows === BP.cohort.people * (BP.cohort.balance.target + BP.cohort.balance.non_target),
  'EEGMAT two-second windows in its own chain; motor imagery two-second and P300 one-second windows from the core matrix’s');
need(BLOCKS.every(b => b.input_chain.sampling_hz === BE.input_chain.sampling_hz), 'one sampling rate for the backbone');
const roleOf = (b: Block, id: string) => b.arms.find((a: any) => a.id === id).role;
need(roleOf(BE, 'band-power') === 'matched comparator' && roleOf(BM, 'temporal-means') === 'primary comparator' && roleOf(BM, 'band-power') === 'descriptive comparator'
  && roleOf(BP, 'temporal-means') === 'primary comparator', 'the comparators’ roles as the protocols declare them');
need(!BE.paired_difference.interval_95.some((v: number) => v === 0) && BE.paired_difference.interval_includes_zero && !BM.paired_difference.interval_includes_zero
  && !BP.paired_difference.interval_includes_zero, 'EEGMAT’s interval spans zero; motor imagery’s and P300’s lie below it');

// --- Where each limitation prints. ----------------------------------------------------------------------------
type Limit = { id: string; text: string };
const LIMITS = X.limitations as Limit[];
const limitIds = LIMITS.map(l => l.id);
const keysOf = (b: Block) => b.caveat_keys as string[];
need(BLOCKS.every(b => keysOf(b).every(k => limitIds.includes(k))) && limitIds.every(id => BLOCKS.some(b => keysOf(b).includes(id))),
  'every caveat key is a limitation, and every limitation is some block’s caveat');
/** The model's identity: three limitations every block names. The rights sit with the model's credit. */
const MODEL_LIMITS = ['variant', 'transfer', 'exposure'];
const CREDIT_LIMITS = ['rights'];
/**
 * EEGMAT's facts the NeuroLM panel above already states beside its evidence (rest recorded before arithmetic, the prior
 * ICA cleaning, a known development cohort): this panel's EEGMAT block names them in one line that points there.
 */
export const SHARED_WITH_NEUROLM = ['eegmat-order', 'development-cohort'];
const everyBlock = (id: string) => BLOCKS.every(b => keysOf(b).includes(id));
need([...MODEL_LIMITS, ...CREDIT_LIMITS].every(everyBlock), 'the model’s identity and rights bound every block');
need(SHARED_WITH_NEUROLM.every(id => BLOCKS.filter(b => keysOf(b).includes(id)).map(b => b.id).join() === 'eegmat'), 'the shared EEGMAT statements bound the EEGMAT block alone');
const NEUROLM_DEVELOPMENT = 'EEGMAT is a known development cohort, used across this site.';
need((LIMITS.find(l => l.id === 'development-cohort')!.text).startsWith(`${NEUROLM_DEVELOPMENT.slice(0, -1)},`)
  && Object.keys(neurolmZh).some(k => k.startsWith(`${NEUROLM_DEVELOPMENT} `)), 'the NeuroLM panel makes the same development-cohort statement this panel points to');
const neurolmCaveats = (locale: Locale) => neurolmCopy[locale].caveats().map(p => typeof p === 'string' ? p : '').join('');
need(LIMITS.find(l => l.id === 'eegmat-order')!.text === 'On EEGMAT, rest is recorded before arithmetic, so recording order moves with the label, and the published signals were already cleaned with ICA.'
  && neurolmCaveats('en').includes('Rest is recorded before arithmetic, so recording order moves with the label.') && neurolmCaveats('zh').includes('静息在心算之前记录')
  && Object.keys(neurolmZh).includes('The source README reports prior ICA cleaning of the published signals.'), 'the NeuroLM panel states the recording order and the ICA cleaning this panel points to');
// The three EEGMAT rights records on the page are one record, so its credit, licence and consent print once, in the NeuroLM credits.
const NL_EEGMAT = (neurolmFacts.rights as any).dataset;
need(['name', 'source', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'rightsScope'].every(k => NL_EEGMAT[k] === (X.rights.datasets.eegmat as any)[k]),
  'EEGMAT’s rights record here is the NeuroLM panel’s, word for word');
const placed = (id: string) => [...MODEL_LIMITS, ...CREDIT_LIMITS].includes(id) ? 'placed' : everyBlock(id) ? 'panel' : BLOCKS.find(b => keysOf(b).includes(id))!.id;
/** The limitation ids each place prints, in the export's order. */
export const LIMIT_PLACE: Record<string, string[]> = { model: MODEL_LIMITS, credits: CREDIT_LIMITS, panel: [], ...Object.fromEntries(BLOCKS.map(b => [b.id, [] as string[]])) };
for (const id of limitIds) { const at = placed(id); if (at !== 'placed') LIMIT_PLACE[at].push(id); }
need(LIMIT_PLACE.panel.includes('separation') && /outside every leaderboard/.test(LIMITS.find(l => l.id === 'separation')!.text), 'the leaderboard statement, from the panel’s separation limitation');
need(Object.values(LIMIT_PLACE).flat().sort().join() === [...limitIds].sort().join(), 'every limitation prints in one place');

need(X.not_published.length === 7 && /^Per-person, per-fold and per-window values/.test(X.not_published[0]) && /^How many people each arm scored above/.test(X.not_published[1]),
  'the not-published list');
need(X.protocols_not_run.map((p: { protocol: string }) => p.protocol).join() === 'semantic-target,beta-4ch,beta-8ch,idle,sleep-scalp', 'five protocols not run');
// Every number the chart draws fits its axis, −30 to +10 pp.
export const NEURORVQ_PAIRED_DOMAIN: [number, number] = [-0.3, 0.1];
need(BLOCKS.every(b => [b.paired_difference.difference, ...b.paired_difference.interval_95].every((v: number) => v > NEURORVQ_PAIRED_DOMAIN[0] && v < NEURORVQ_PAIRED_DOMAIN[1])),
  'every paired difference and bound fits the −30 to +10 pp axis');

// --- The Chinese for the export's own sentences, keyed by the exact English. ------------------------------------
export const neurorvqZh: Record<string, string> = {
  'Does NeuroRVQ’s frozen backbone, read by a fitted ridge head, separate the classes of three existing tasks better than simple features of the same windows?':
    'NeuroRVQ 的冻结主干由拟合好的岭回归分类头读出，在三项现有任务上区分类别，比同一批时间窗的简单特征更好吗？',
  // The blocks.
  'Arithmetic and rest': '心算与静息',
  'Motor imagery and rest': '运动想象与静息',
  'P300 target and non-target': 'P300 目标与非目标',
  // The arms, their roles and definitions.
  'NeuroRVQ backbone': 'NeuroRVQ 主干',
  'band power': '频带功率',
  'temporal means': '时间均值',
  'probe': '被检验的表示',
  'matched comparator': '匹配的对照',
  'primary comparator': '主要对照',
  'descriptive comparator': '描述性对照',
  'the four 200-value branch outputs of the frozen backbone, each averaged over the window’s 38 tokens (19 channels by two one-second patches) and joined into 800 values':
    '冻结主干四个分支各 200 维的输出，每个分支在该时间窗的 38 个 token（19 个通道 × 两个一秒片段）上取均值，再拼接成 800 维',
  'the four 200-value branch outputs of the frozen backbone, each averaged over the window’s 30 tokens (15 channels by two one-second patches) and joined into 800 values':
    '冻结主干四个分支各 200 维的输出，每个分支在该时间窗的 30 个 token（15 个通道 × 两个一秒片段）上取均值，再拼接成 800 维',
  'the four 200-value branch outputs of the frozen backbone, each averaged over the window’s 19 tokens (one one-second patch per channel) and joined into 800 values':
    '冻结主干四个分支各 200 维的输出，每个分支在该时间窗的 19 个 token（每个通道一个一秒片段）上取均值，再拼接成 800 维',
  '95 log band powers: 19 channels by five bands (1–4, 4–8, 8–13, 13–30 and 30–44.5 Hz), Welch with one-second Hann windows at 200 Hz on the same adapted windows':
    '95 个对数频带功率：19 个通道 × 五个频带（1–4、4–8、8–13、13–30 与 30–44.5 Hz），在同一批经过适配的时间窗上以 200 Hz、一秒 Hann 窗做 Welch 估计',
  '1,500 means of non-overlapping four-sample (20 ms) bins after resampling to 200 Hz: 15 channels by 100 bins':
    '重采样到 200 Hz 后，对互不重叠、每段四个样本（20 ms）的区间取均值，共 1,500 个：15 个通道 × 100 个区间',
  '75 log band powers: 15 channels by five bands (1–4, 4–8, 8–13, 13–30 and 30–45 Hz), Welch with one-second windows at 200 Hz':
    '75 个对数频带功率：15 个通道 × 五个频带（1–4、4–8、8–13、13–30 与 30–45 Hz），以 200 Hz、一秒窗做 Welch 估计',
  '950 means of non-overlapping four-sample (20 ms) bins after resampling to 200 Hz: 19 channels by 50 bins':
    '重采样到 200 Hz 后，对互不重叠、每段四个样本（20 ms）的区间取均值，共 950 个：19 个通道 × 50 个区间',
  // The paired differences and their readings.
  'NeuroRVQ backbone minus band power': 'NeuroRVQ 主干减频带功率',
  'NeuroRVQ backbone minus temporal means': 'NeuroRVQ 主干减时间均值',
  [SPANS_ZERO]: neurolmZh[SPANS_ZERO],
  [BELOW_ZERO]: '区间整个低于零；这是描述性结果，只来自这一个队列',
  // The audit boundaries.
  'The independent audit rebuilt every row, fold and label, refitted all 10 heads and reproduced all 4,320 held-out predictions, the scores and the interval; it read both arms’ values from the producer’s sealed files and did not re-extract them.':
    '独立审计重建了每一行、每一折与每个标签，重新拟合了全部 10 个分类头，复现了全部 4,320 个留出预测、各个分数与区间；两组的特征值都读自生产方封存的文件，没有重新提取。',
  'The independent audit recomputed the temporal and band-power values bit for bit, refitted all 15 heads and reproduced all 3,600 held-out predictions, the scores and the interval; a supplementary check re-extracted all 1,200 × 800 NeuroRVQ values exactly, reusing the accepted backbone loader.':
    '独立审计逐位重新计算了时间均值与频带功率的特征值，重新拟合了全部 15 个分类头，复现了全部 3,600 个留出预测、各个分数与区间；一项补充检查沿用已通过验收的主干加载程序，精确地重新提取了全部 1,200 × 800 个 NeuroRVQ 特征值。',
  'A separately written audit re-extracted all 2,520 × 800 NeuroRVQ values and 2,520 × 950 temporal means exactly, reusing the accepted backbone loader, refitted all 10 heads and reproduced all 5,040 held-out predictions, the scores and the interval.':
    '一套单独编写的审计沿用已通过验收的主干加载程序，精确地重新提取了全部 2,520 × 800 个 NeuroRVQ 特征值与 2,520 × 950 个时间均值，重新拟合了全部 10 个分类头，复现了全部 5,040 个留出预测、各个分数与区间。',
  // The limitations.
  'Every score uses the released NeuroRVQ backbone with parameter-free branch normalisation and mean-token pooling: 263 trained tensors restore strictly, the four branch normalisations carry no parameters and take the source’s default scale 1 and shift 0, and each branch’s tokens are averaged and the four 200-value branches joined into 800 values. The authors’ inference wrapper fails a strict restore, because eight normalisation tensors it expects are missing from the checkpoint.':
    '每个分数都使用已发布的 NeuroRVQ 主干，分支归一化不带参数，并对 token 取均值汇聚：263 个训练好的张量严格恢复；四个分支的归一化不带参数，取源代码默认的缩放 1 与平移 0；每个分支的 token 取均值，再把四个 200 维的分支拼接成 800 维。作者的推理封装无法严格恢复，因为它需要的八个归一化张量在检查点中缺失。',
  'Supervised transfer: the backbone stays frozen, and in each fold a standardiser and a ridge head (alpha 100, balanced class weights) are fitted on the other participants’ windows. No score is zero-shot, and nothing was tuned.':
    '有监督迁移：主干保持冻结，每一折都在其他被试的时间窗上拟合一个标准化器和一个岭回归分类头（alpha 100，类别平衡权重）。没有任何分数是零样本的，也没有做任何调参。',
  'Pretraining exposure is unknown. None of the three datasets is named in the paper’s list of 13 pretraining corpora, but the list includes a proprietary collection and no per-checkpoint list of corpora or participants is published, so the backbone may have seen these recordings.':
    '是否出现在预训练数据中，未知。论文列出的 13 个预训练语料中没有这三个数据集，但这份清单包含一个私有数据集，而且没有公布按检查点划分的语料或被试清单，所以主干网络可能见过这些记录。',
  'The checkpoint and the paper do not establish the amplitude scale or reference NeuroRVQ was pretrained on. Every chain here feeds microvolts as an adaptation: the EEGMAT chain follows the notch, band-pass and clip of the example preprocessing in NeuroRVQ’s code, and the motor-imagery and P300 chains leave all three out. No score here reproduces NeuroRVQ’s published pipeline, and none separates the representation from an input mismatch.':
    '检查点与论文都没有说明 NeuroRVQ 预训练时所用的幅值尺度或参考电极。这里每个流程都以微伏作为输入，这是一种适配：EEGMAT 的流程沿用 NeuroRVQ 代码中示例预处理的陷波、带通与截幅，运动想象与 P300 的流程则三者都不做。这里没有任何分数复现 NeuroRVQ 发表的流程，也没有任何分数能把表示本身与输入不匹配的影响分开。',
  'EEGMAT has its own input chain: the first 60 seconds of each recording, notches at 50, 60 and 100 Hz, a third-order 0.5–44.5 Hz band-pass run forward and backward, clipping at ±500 µV and resampling from 500 to 200 Hz, with no demeaning or re-referencing. The band-power arm reads the same adapted windows.':
    'EEGMAT 有自己的输入流程：取每段记录的前 60 秒，在 50、60 与 100 Hz 做陷波，用三阶 0.5–44.5 Hz 带通滤波器前向、反向各运行一次，在 ±500 µV 截幅，从 500 Hz 重采样到 200 Hz，不去均值，也不重新参考。频带功率一组读取的是同一批经过适配的时间窗。',
  'Motor imagery and P300 reuse the core matrix’s prepared windows, people and fold rule, resampled per window from 125 and 300 Hz to 200 Hz with no further filter, clipping or rescaling; motor imagery keeps the core per-channel epoch demeaning. Their temporal and band-power arms were recomputed in this chain, apart from the matrix run: the motor-imagery band power differs from that protocol’s Spectral ridge row, and the P300 temporal means from that protocol’s Temporal ridge row.':
    '运动想象与 P300 沿用核心矩阵准备好的时间窗、被试与分折规则，逐个时间窗从 125 Hz 和 300 Hz 重采样到 200 Hz，不再滤波、截幅或缩放；运动想象保留核心流程中按通道对每个分段去均值的做法。它们的时间均值组与频带功率组是在这个流程里、在矩阵运行之外重新计算的：运动想象的频带功率与该协议的 spectral ridge 一行不同，P300 的时间均值与该协议的 temporal ridge 一行不同。',
  'Motor-imagery and P300 amplitudes are read as microvolts from the source cache: ds003810’s EDF unit fields are blank and its channel files declare microvolts, and ds006593’s headers give a 0.1 µV resolution with blank reference fields; the P300 cache’s original preparation from the raw files was not re-run. Neither reading is an independent instrument calibration.':
    '运动想象与 P300 的幅值按数据源缓存读作微伏：ds003810 的 EDF 单位字段为空，其通道文件声明单位为微伏；ds006593 的文件头给出 0.1 µV 的分辨率，参考字段为空；P300 缓存当初从原始文件准备的过程没有重新运行。两者的读取都不是独立的仪器校准。',
  'The arms differ in size under one fixed alpha: NeuroRVQ’s 800 values against 95 band powers on EEGMAT, 1,500 temporal means and 75 band powers on motor imagery, and 950 temporal means on P300. There is no random-initialisation arm, so the panel says nothing about what pretraining contributes.':
    '在同一个固定的 alpha 下，各组的维度不同：EEGMAT 上是 NeuroRVQ 的 800 维对 95 个频带功率，运动想象上是对 1,500 个时间均值与 75 个频带功率，P300 上是对 950 个时间均值。没有随机初始化的一组，所以这一栏不能说明预训练带来了什么。',
  'The P300 sample is balanced at 60 target and 60 non-target epochs per person, where the source inquiries hold about one target in ten letters, and stimuli come about every 0.3 s, so each one-second window holds later responses. The scores are for single epochs and do not measure speller accuracy.':
    'P300 样本按每人 60 个目标分段与 60 个非目标分段平衡抽取，而数据源的每轮查询中大约十个字母里才有一个目标；刺激约每 0.3 秒出现一次，所以每个一秒时间窗里都含有后续刺激的反应。这些分数针对的是单个分段，并不衡量拼写器的准确率。',
  'On EEGMAT, rest is recorded before arithmetic, so recording order moves with the label, and the published signals were already cleaned with ICA.':
    '在 EEGMAT 上，静息在心算之前记录，所以记录顺序与标签一起变化；而且已发布的信号事先已经用 ICA 清理过。',
  'Each paired difference carries a descriptive 95% interval from 20,000 paired participant resamples, conditional on the fixed folds and fitted heads; each arm has a point estimate only.':
    '每个配对差值都附有一个描述性的 95% 区间，来自 20,000 次配对的被试重抽样，以固定的折与拟合好的分类头为条件；每一组只有点估计。',
  'Each panel on this page has its own input chain and band-power arm, so these scores stay outside every leaderboard and are not ranked against the NeuroLM panel, the ten-second panel or the core matrix.':
    '本页每一栏都有自己的输入流程和频带功率一组，所以这些分数不进入任何排行榜，也不与 NeuroLM 一栏、十秒一栏或核心矩阵比较排名。',
  'Offline results for one frozen variant: the EEGMAT chain filters the retained first minute of each recording as one block before cutting it into windows, and nothing here measures cognitive workload, clinical use, online decoding or other uses of NeuroRVQ.':
    '一个冻结变体的离线结果：EEGMAT 的流程先把每段记录保留下来的第一分钟作为一个整体滤波，再切成时间窗；这里没有任何内容衡量脑力负荷、临床用途、在线解码或 NeuroRVQ 的其他用途。',
  'NeuroRVQ’s code and weights are licensed CC BY-NC 4.0, the licence file of both repositories at the pinned revisions. Only aggregate figures are published here; no weights are distributed, and no endorsement by NeuroRVQ’s authors is implied.':
    'NeuroRVQ 的代码与权重均以 CC BY-NC 4.0 许可，即两个仓库在固定版本下的许可文件。这里只发布聚合数字；不分发任何权重，也不代表 NeuroRVQ 作者的认可。',
  // The protocols not run: each one's gate.
  'the original calibration evidence is still missing': '仍缺少原始校准证据',
  'physical units and reference are unresolved': '物理单位与参考电极尚未厘清',
  'physical units are unresolved, and PO5 and PO6 are missing from the model’s channel list': '物理单位尚未厘清，模型的通道列表中也没有 PO5 与 PO6',
  'its inputs are missing, and it needs its own calibration, threshold and split protocol': '缺少输入，且需要自己的校准、阈值与划分方案',
  'deferred to a separate study': '推迟到单独的研究',
  // Not published.
  'Per-person, per-fold and per-window values of any kind, fold assignments, participant identifiers, labels, extracted values, fitted heads, predictions and the sealed files: only participant-mean scores, one paired difference per task with its interval, and cohort counts are published.':
    '任何逐人、逐折与逐时间窗的数值，折的划分，被试标识，标签，提取出的特征值，拟合好的分类头，预测与封存的文件：只发布按被试平均的分数、每项任务一个配对差值及其区间，以及队列计数。',
  'How many people each arm scored above 50%, which the sources give as descriptive point-estimate counts.':
    '每一组有多少名被试的分数高于 50%；数据源把这些作为描述性的点估计计数给出。',
  // Ethics and consent, as each dataset's rights record states them (its first sentence).
  [CONSENT_EN]: neurolmZh[CONSENT_EN],
  'Study paper reports ethics approval by CEySTE CCT-CONICET Santa Fe, Declaration of Helsinki compliance, and signed consent.':
    '研究论文报告已获 CEySTE CCT-CONICET Santa Fe 的伦理批准，符合《赫尔辛基宣言》，并取得签署的知情同意。',
  'Dataset metadata/README report IRB approval #10-05-2022 and written informed consent.':
    '数据集元数据与 README 报告已获 IRB 批准（编号 #10-05-2022），并取得书面知情同意。',
};

const numbersOf = (s: string) => [...s.matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0].replace(/,/g, '')).sort().join(' ');
const dateZh = (s: string) => s.replace('2018 年 8 月 15 日', '15 August 2018').replace(/August/, '');
for (const [en, zh] of Object.entries(neurorvqZh))
  need(numbersOf(en.replace(/August/, '')) === numbersOf(dateZh(zh)), `the Chinese for "${en.slice(0, 60)}" carries exactly its English's numbers`);

/** One of the export's sentences as the page prints it: the English as released; on a Chinese page the Chinese, with the English as `original`. */
export function neurorvqText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = neurorvqZh[en];
  if (zh === undefined) throw new Error(`neurorvq.ts: no Chinese for "${en.slice(0, 80)}"`);
  return { text: zh, original: en };
}
const say = (en: string, locale: Locale) => neurorvqText(en, locale).text;
const head = (s: string, locale: Locale) => locale === 'en' ? s[0].toUpperCase() + s.slice(1) : s;

// --- Figures --------------------------------------------------------------------------------------------------
const pct2 = (raw: number) => fig(raw, 'pct2'), sgn2 = (raw: number) => fig(raw, 'sgn2'), pp2 = (raw: number) => fig(raw, 'pp2'), n = (raw: number) => fig(raw, 'count');
type Part = string | Fig;
const limitText = (id: string) => LIMITS.find(l => l.id === id)!.text;
export interface NeurorvqLimit { id: string; text: string; original?: string; shared?: { lead: string; link: string; rest: string } }
/**
 * The limitations a place prints. The ones the NeuroLM panel already states for EEGMAT print as one line in place of the
 * first of them, its id naming both, pointing there.
 */
const limitsAt = (place: string, locale: Locale): NeurorvqLimit[] => LIMIT_PLACE[place].flatMap(id => {
  if (!SHARED_WITH_NEUROLM.includes(id)) return [{ id, ...neurorvqText(limitText(id), locale) }];
  if (id !== LIMIT_PLACE[place].find(x => SHARED_WITH_NEUROLM.includes(x))) return [];
  const r = neurorvqCopy[locale].sharedRef;
  return [{ id: SHARED_WITH_NEUROLM.join(' '), text: `${r.lead}${r.link}${r.rest}`, shared: r }];
});

export interface NeurorvqArm { id: string; label: string; role: string; dimension: Fig; ba: Fig; f1: Fig; definition: string; definitionEn: string }
export interface NeurorvqBlock {
  id: string; protocol: string; title: string; dataset: string; people: Fig; arms: NeurorvqArm[];
  cohort: Part[]; caption: Part[]; findLabel: Part[]; findH3: string; findP: Part[];
  diff: { d: Fig; lo: Fig; hi: Fig; zero: boolean; label: string; comparator: string };
  limits: NeurorvqLimit[]; audit: { text: string; original?: string };
}

const cohortParts = (b: Block, zh: boolean): Part[] => {
  const C = b.cohort as any;
  if (b.id === 'eegmat') return zh
    ? [n(C.people), ' 名被试，', n(C.recordings), ' 段记录，', n(C.windows), ' 个两秒时间窗（每段记录前 ', n(C.retained_seconds), ' 秒中的 ', n(C.windows_per_recording), ' 个），', n(C.channels), ' 个通道，', n(C.folds), ' 折、整名被试留出；使用自己的输入流程，从 ', n(b.input_chain.source_sampling_hz), ' Hz 重采样到 ', n(b.input_chain.sampling_hz), ' Hz。']
    : [n(C.people), ' people, ', n(C.recordings), ' recordings, ', n(C.windows), ' two-second windows (', n(C.windows_per_recording), ' from the first ', n(C.retained_seconds), ' s of each recording), ', n(C.channels), ' channels, ', n(C.folds), ' folds of whole participants; its own input chain, resampled from ', n(b.input_chain.source_sampling_hz), ' to ', n(b.input_chain.sampling_hz), ' Hz.'];
  const unit = b.cohort.window_seconds === 2 ? (zh ? '两秒时间窗' : 'two-second windows') : (zh ? '一秒分段' : 'one-second epochs');
  const balance = C.balance ? (zh ? ['（每人 ', n(C.balance.target), ' 个目标、', n(C.balance.non_target), ' 个非目标）'] : [' (', n(C.balance.target), ' target and ', n(C.balance.non_target), ' non-target per person)']) : [];
  return zh
    ? [n(C.people), ' 名被试，', n(C.windows), ' 个', unit, ...balance, '，', n(C.channels), ' 个通道，', n(C.folds), ' 折、整名被试留出：沿用核心矩阵准备好的时间窗与分折，从 ', n(b.input_chain.source_sampling_hz), ' Hz 重采样到 ', n(b.input_chain.sampling_hz), ' Hz，对照组在这个流程里重新计算。']
    : [n(C.people), ' people, ', n(C.windows), ` ${unit}`, ...balance, ', ', n(C.channels), ' channels, ', n(C.folds), ' folds of whole participants: the core matrix’s prepared windows and folds, resampled from ', n(b.input_chain.source_sampling_hz), ' to ', n(b.input_chain.sampling_hz), ' Hz, with the comparators recomputed in that chain.'];
};

/** The three blocks, in the export's order: each task's cohort, arms, paired difference, own limitations and audit. */
export const neurorvqBlocks = (locale: Locale): NeurorvqBlock[] => BLOCKS.map(b => {
  const zh = locale === 'zh', d = b.paired_difference, comp = b.arms.find((a: any) => a.id === d.b);
  const label = say(d.label, locale);
  return {
    id: b.id, protocol: b.protocol, title: say(b.title, locale), dataset: b.dataset, people: n(b.cohort.people),
    arms: b.arms.map((a: any) => ({ id: a.id, label: head(say(a.label, locale), locale), role: say(a.role, locale), dimension: n(a.dimension),
      ba: pct2(a.balanced_accuracy), f1: pct2(a.macro_f1), definition: say(a.definition, locale), definitionEn: a.definition })),
    cohort: cohortParts(b, zh),
    caption: zh ? [n(b.cohort.people), ' 名被试的均值，每名被试都由训练时没有用到其数据的分类头评分。'] : ['Participant means over the ', n(b.cohort.people), ' people, each scored by heads fitted without them.'],
    findLabel: zh ? [label, '，平衡准确率，在同样 ', n(b.cohort.people), ' 名被试上配对'] : [head(label, locale), ', balanced accuracy, paired over the same ', n(b.cohort.people), ' people'],
    findH3: d.interval_includes_zero ? (zh ? '区间跨过零' : 'The interval spans zero') : (zh ? '区间整个低于零' : 'The interval lies below zero'),
    findP: zh
      ? [label, '：', sgn2(d.difference), ' pp，配对的 95% 被试 bootstrap 区间 ', sgn2(d.interval_95[0]), ' 至 ', sgn2(d.interval_95[1]), `；${say(d.reading, locale)}。`]
      : [head(label, locale), ': ', sgn2(d.difference), ' points, paired 95% participant-bootstrap interval ', sgn2(d.interval_95[0]), ' to ', sgn2(d.interval_95[1]), `; ${d.reading}.`],
    diff: { d: pp2(d.difference), lo: sgn2(d.interval_95[0]), hi: pp2(d.interval_95[1]), zero: d.interval_includes_zero, label, comparator: say(comp.label, locale) },
    limits: limitsAt(b.id, locale), audit: neurorvqText(b.audit.boundary, locale),
  };
});
export const neurorvqModelLimits = (locale: Locale) => limitsAt('model', locale);
export const neurorvqPanelLimits = (locale: Locale) => limitsAt('panel', locale);
export const neurorvqCreditLimits = (locale: Locale) => limitsAt('credits', locale);
/** What is not published: the export's first two items. The rest repeat the limits and credits, or name working files. */
export const neurorvqNotPublished = (locale: Locale) => X.not_published.slice(0, 2).map((s: string) => neurorvqText(s, locale));
/** The protocols not run, each with its gate: the protocol's id (the page prints its title) and the gate's words. */
export const neurorvqNotRun = (locale: Locale) => (X.protocols_not_run as { protocol: string; gate: string }[]).map(p => ({ protocol: p.protocol, gate: neurorvqText(p.gate, locale) }));
/**
 * Each dataset's credit: its attribution, the first sentence of its rights record's ethics and consent statement as
 * released, its use and licence. EEGMAT's is the NeuroLM panel's record (checked above), so its credit points there
 * (`sharedWithNeurolm`) and keeps its licence link.
 */
const consentOf = (s: string) => s.slice(0, s.indexOf('. ') + 1);
export const neurorvqDatasets = (locale: Locale) => BLOCKS.map(b => {
  const r = (R.datasets as Record<string, any>)[b.id];
  return { block: b.id, name: r.name as string, attribution: r.attribution as string, source: r.source as string, license: r.license as string, licenseUrl: r.licenseUrl as string,
    rightsScope: r.rightsScope as string, consent: neurorvqText(consentOf(r.privacyReview), locale), slug: { eegmat: 'eegmat', 'mi-rest': 'ds003810', 'p300-target': 'ds006593' }[b.id as 'eegmat'],
    sharedWithNeurolm: b.id === 'eegmat' };
});
need(BLOCKS.every(b => (R.datasets as Record<string, any>)[b.id]?.name === b.dataset && (R.datasets as Record<string, any>)[b.id].rightsScope === 'Personal noncommercial research; aggregate results only'),
  'each dataset keeps its released rights record');
export const neurorvqFacts = { question: X.question as string, model: M, probe: PR, interval: I, rights: R, exposure: E, schema: X.schema_version as string, folds, blocks: BLOCKS };

// --- The copy, in both languages. Figures are `Fig`s, in the same order in both. ---------------------------------
const people = BLOCKS.map(b => n(b.cohort.people));
need(X.scope.startsWith(`NeuroRVQ’s released backbone stays frozen. On each task one ridge head (alpha ${PR.alpha}) is fitted per fold on the other participants, for the backbone’s ${M.pooling.dimension} pooled values`)
  && X.scope.includes(`${BE.cohort.people} people on EEGMAT, ${BM.cohort.people} on motor imagery against rest and ${BP.cohort.people} on P300 target against non-target, five participant-held-out folds each, nothing tuned`)
  && folds === 5, 'the lede says what the export’s scope says');
export const neurorvqCopy = {
  en: {
    eyebrow: 'Human · scalp EEG · arithmetic and rest, motor imagery, P300 · NeuroRVQ, frozen',
    h2: 'A separate panel: NeuroRVQ’s frozen backbone on three tasks',
    label: 'Locally executed experiment · offline · whole participants held out · outside the pilot count above',
    lede: (): Part[] => [X.question, ' The backbone stays frozen. On each task one ridge head (alpha ', n(PR.alpha), ') is fitted per fold on the other participants, for the backbone’s ',
      n(M.pooling.dimension), ' values and for simple features of the same windows: ', people[0], ' people on EEGMAT, ', people[1], ' on motor imagery against rest and ', people[2],
      ' on P300 target against non-target, in ', n(folds), ' participant-held-out folds, nothing tuned. Scores are participant means; chance is ', pct2(X.chance_level.balanced_accuracy),
      ' balanced accuracy. Each task has one paired difference with a participant-bootstrap interval.'],
    plotCaption: 'Paired differences in balanced accuracy, the NeuroRVQ backbone minus each task’s primary comparator, in percentage points.',
    plotLegend: 'Dot: the mean of the people’s paired differences; line: its 95% participant-bootstrap interval; dashed line: no difference. Each task has its own people, windows and comparator.',
    axis: 'Paired difference', minus: 'minus', interval: '95% interval', to: ' to ',
    colRep: 'Representation', colRole: 'Role', colDim: 'Dimension', colBa: 'Balanced accuracy', colF1: 'Macro-F1',
    region: (t: string) => `NeuroRVQ, ${t}: balanced accuracy and macro-F1 of each representation`,
    protocolLink: 'This task’s core matrix →',
    sharedRef: { lead: 'EEGMAT’s recording order (rest before arithmetic), the source’s prior ICA cleaning and EEGMAT’s use as a development cohort are ',
      link: 'stated in the NeuroLM panel above ↑', rest: ' and bound this block too: it is not an untouched external confirmation.' },
    eegmatCreditRef: 'Credit, ethics and consent: in the NeuroLM panel’s credits above ↑',
    modelH3: 'The model and its head',
    head: (): Part[] => ['The head: a standard scaler fitted on the training participants’ windows only, then a ridge classifier with alpha ', n(PR.alpha),
      ', the Cholesky solver, balanced class weights and no hyperparameter search; ', n(BE.fits), ', ', n(BM.fits), ' and ', n(BP.fits), ' fits on the three tasks, each prediction sealed before scoring.'],
    limitsH3: 'What else bounds this panel',
    notRun: 'Protocols not run, with what each still needs: ',
    notPubH3: 'Not published here',
    dataUse: 'what this release publishes, on the data-use page →',
    creditsH3: 'Credits, licences and consent',
    modelCreditH: 'NeuroRVQ',
    paper: 'Paper:', code: 'code:', at: 'at', ckpt: 'Checkpoint:', sha: 'SHA-256', weightsLicence: 'licence file of its Hugging Face repository',
    consentH: 'Ethics and consent, as the source states them:', scopeH: 'Use:',
    recordLink: 'Dataset record ↗', datasetPage: 'Dataset page →',
    dataSource: 'Data source:', schema: 'schema',
  },
  zh: {
    eyebrow: '人类 · 头皮 EEG · 心算与静息、运动想象、P300 · 冻结的 NeuroRVQ',
    h2: '单独一栏：NeuroRVQ 冻结主干，三项任务',
    label: '本站在本地运行的实验 · 离线 · 整名被试留出 · 不计入上面的试点数',
    lede: (): Part[] => [neurorvqZh[X.question], '主干保持冻结。每项任务在每一折都用其他被试拟合一个岭回归分类头（alpha ', n(PR.alpha), '），分别读取主干的 ',
      n(M.pooling.dimension), ' 个值和同一批时间窗的简单特征：EEGMAT ', people[0], ' 名被试，运动想象对静息 ', people[1], ' 名，P300 目标对非目标 ', people[2],
      ' 名，都是 ', n(folds), ' 折、整名被试留出，不调参。分数是被试均值；平衡准确率的随机水平为 ', pct2(X.chance_level.balanced_accuracy),
      '。每项任务有一个配对差值及其被试 bootstrap 区间。'],
    plotCaption: '平衡准确率的配对差值：NeuroRVQ 主干减去每项任务的主要对照，单位 pp。',
    plotLegend: '点为各被试配对差值的均值，横线为它的 95% 被试 bootstrap 区间，虚线为没有差异。每项任务有各自的被试、时间窗与对照。',
    axis: '配对差值', minus: '减', interval: '95% 区间', to: ' 至 ',
    colRep: '表示', colRole: '作用', colDim: '维度', colBa: '平衡准确率', colF1: '宏平均 F1',
    region: (t: string) => `NeuroRVQ，${t}：各表示的平衡准确率与宏平均 F1`,
    protocolLink: '这项任务的核心矩阵 →',
    sharedRef: { lead: 'EEGMAT 的记录顺序（静息在心算之前）、数据源事先做过的 ICA 清理，以及 EEGMAT 在本站作为开发队列的用途，',
      link: '见上面 NeuroLM 一栏 ↑', rest: '，同样限定这一块：它不是未经使用的外部确认。' },
    eegmatCreditRef: '署名、伦理与知情同意：见上面 NeuroLM 一栏的署名 ↑',
    modelH3: '模型与分类头',
    head: (): Part[] => ['分类头：先用只在训练被试时间窗上拟合的标准化，再接 alpha 为 ', n(PR.alpha),
      '、用 Cholesky 求解、类别平衡、不搜索超参数的岭回归分类器；三项任务分别拟合 ', n(BE.fits), '、', n(BM.fits), ' 与 ', n(BP.fits), ' 次，每个预测都在评分前封存。'],
    limitsH3: '这一栏的其他局限',
    notRun: '没有运行的协议，以及各自还缺什么：',
    notPubH3: '这里不发布的内容',
    dataUse: '这次发布的内容，见数据使用页面（英文）→',
    creditsH3: '署名、许可与知情同意',
    modelCreditH: 'NeuroRVQ',
    paper: '论文：', code: '代码：', at: ' 版本 ', ckpt: '检查点：', sha: 'SHA-256：', weightsLicence: '其 Hugging Face 仓库的许可文件',
    consentH: '数据源陈述的伦理与知情同意：', scopeH: '使用范围：',
    recordLink: '数据集记录 ↗', datasetPage: '数据集页面 →',
    dataSource: '数据来源：', schema: 'schema',
  },
};
need(Object.values(neurorvqCopy).every(c => !/\d/.test(Object.values(c.sharedRef).join('') + c.eegmatCreditRef)), 'the pointers to the NeuroLM panel’s EEGMAT statements and credits carry no figure');

/**
 * The panel's results as the panel prints them, unsigned and without units, at two decimals: each arm's balanced
 * accuracy and macro-F1 and each paired difference and bound. A text that prints one of them, or names NeuroRVQ,
 * carries the panel.
 */
export const neurorvqResultNumbers: Set<string> = new Set(BLOCKS.flatMap(b => [
  ...b.arms.flatMap((a: any) => [a.balanced_accuracy, a.macro_f1]), b.paired_difference.difference, ...b.paired_difference.interval_95,
]).map((v: number) => Math.abs(v * 100).toFixed(2)));
export const carriesNeurorvq = (text: string): boolean =>
  /NeuroRVQ/i.test(text) || [...text.matchAll(/\d+(?:\.\d+)?/g)].some(m => neurorvqResultNumbers.has(m[0]));

/** The pointer on the motor-imagery and P300 protocol pages: no figure, one link to the panel. */
export const neurorvqPointer = {
  en: 'A frozen NeuroRVQ probe with its own input chain is on the pilot studies page →',
  zh: '另有一项冻结 NeuroRVQ 的探针，使用自己的输入流程，见试点研究页面 →',
};
need(Object.values(neurorvqPointer).every(s => !/\d/.test(s)), 'the pointer carries no figure');
