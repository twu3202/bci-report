/**
 * Two frozen encoders on ten-second EEGMAT windows (release eegmat-ten-second-update-20261028, owner decision D14 of
 * 2026-10-28): a separate panel on the pilot studies page, #eegmat-ten-second, after NeuroRVQ's and outside the pilot
 * count, with a cohort block and then one subsection per encoder, EEG-Captioner's and AXON's, each beside the same Welch
 * band-power baseline. There is no table of the two encoders together and no encoder-against-encoder difference: AXON
 * ran after the EEG-Captioner and Welch outcomes were known, and the two read different inputs. The Arithmetic & rest
 * protocol page points to the panel with no figure, in the same line as its pointer to the NeuroRVQ panel.
 *
 * Read from the served file and nothing else (eegmat-ten-second-update.json). Every figure is a `Fig` naming that file,
 * printed at two decimals, so check-workbench.mjs and checks/eegmat-ten-second.mjs re-read it by field: EEG-Captioner's
 * 65.74% is the same number as LaBraM last-block's per-seed mean in adaptation-update.json, and at one decimal the
 * Welch baseline's 67.59% would print as core EEGNet's 67.6% on the same protocol. Nothing is computed here.
 *
 * Beside every score: the source annotation-QC totals (0 of 432 windows meet EEG-Captioner's source annotation-QC
 * rules, and 72 of 72 recordings are flagged by them), and beside AXON's also its own numerical input check, a
 * different check. The QC flag's scope prints once, in the cohort block.
 *
 * The export's own sentences print as released on the English page; on the Chinese page through `tenSecondZh`, keyed by
 * the exact English, so a sentence that changes without its translation fails the build, and a translation must carry
 * exactly its English's numbers.
 *
 * EEGMAT's shared facts are stated once on the page, by the NeuroLM panel above, beside its evidence: rest recorded
 * before arithmetic, and the dataset's credit, licence and consent (the same rights record, checked below). Here the
 * `recording-order` limitation points there and keeps what this export adds (time and artifacts move with the label too,
 * the folds do not remove it, neither probe isolates cognitive workload); the EEGMAT credit points to the NeuroLM credits
 * and keeps its licence link. Each licence line names its model, so EEG-Captioner's and AXON's Apache-2.0 terms never
 * read as another model's.
 */
import X from './eegmat-ten-second-update.json';
import { PILOT_PATH } from './entities';
import type { Fig, Fmt } from './entities';
import type { Locale } from './i18n';
import { CONSENT_EN, SPANS_ZERO, neurolmCopy, neurolmFacts, neurolmZh } from './neurolm-eegmat';
import { NEURORVQ_ANCHOR, NEURORVQ_POINTER_PROTOCOLS } from './neurorvq';

export const TEN_SECOND_JSON = 'eegmat-ten-second-update.json';
export const TEN_SECOND_ANCHOR = 'eegmat-ten-second';
export const TEN_SECOND_PANEL_PATH = `${PILOT_PATH}#${TEN_SECOND_ANCHOR}`;
export const tenSecondRelease: { id: string; date: string } = { id: X.release_id, date: X.generated_at };

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`eegmat-ten-second.ts: ${what}`); };
const fig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: TEN_SECOND_JSON });

// --- What every sentence below rests on; the build refuses an export that no longer says it. ------------------
need(X.schema_version === 'bci-report-eegmat-ten-second-update-v1' && X.release_id === 'eegmat-ten-second-update-20261028', 'the served file is not the ten-second EEGMAT release');
const P = X.placement;
need(P.page === PILOT_PATH && P.anchor === TEN_SECOND_ANCHOR && P.after_anchor === NEURORVQ_ANCHOR && P.counted_in_pilots === false && P.leaderboard === false
  && P.core_matrix_row === false && P.new_dataset_count === 0 && P.new_model_count === 0 && P.shared_table === false && P.subsections.join() === 'eeg_captioner,axon',
  'a separate panel after NeuroRVQ’s, outside the pilot count, one subsection per encoder and no shared table');
/** The protocol page that points to the panel, in the same line as its NeuroRVQ pointer. */
export const TEN_SECOND_POINTER_PROTOCOL = P.pointer_from.replace(/^\/protocols\/([a-z0-9-]+)\/$/, '$1');
need(P.pointer_from === `/protocols/${TEN_SECOND_POINTER_PROTOCOL}/` && NEURORVQ_POINTER_PROTOCOLS.includes(TEN_SECOND_POINTER_PROTOCOL),
  'the pointing protocol page also points to the NeuroRVQ panel, so one line links both');
const C = X.cohort;
need(C.dataset === 'EEGMAT' && C.version === '1.0.0' && C.recordings === C.people * C.conditions && C.windows === C.recordings * C.windows_per_recording
  && C.windows_per_recording * C.window_seconds === C.retained_seconds && C.window_seconds === 10 && C.channels === C.channel_names.length && C.folds === 5
  && C.same_windows_both_encoders === true && /^subject-disjoint/.test(C.split), 'the cohort: six ten-second windows from the first minute of each recording, both encoders on the same windows, five subject-disjoint folds');
const PP = C.preprocessing;
need(PP.whole_recording === true && PP.band_pass_hz.length === 2 && PP.sampling_hz === C.sampling_hz && PP.units === 'microvolts', 'whole recordings filtered, resampled to the cohort’s rate');
const Q = X.source_annotation_qc;
need(Q.windows === C.windows && Q.windows_meeting_rules === 0 && Q.recordings === C.recordings && Q.recordings_flagged === C.recordings && Q.level === 'recording'
  && Q.selects_windows === false && Q.changes_inputs === false, 'none of the windows meets the source QC rules and every recording is flagged; the flag selects and changes nothing');
const PR = X.probe;
need(PR.head === 'RidgeClassifier' && PR.alpha === 100 && PR.solver === 'svd' && PR.class_weight === 'balanced' && PR.hyperparameter_search === false
  && PR.encoder_fine_tuning === false && PR.sealed_before_scoring === true && PR.shared_by_both_encoders === true && PR.fits_per_representation === C.folds,
  'one fixed ridge head per representation and fold, shared by both encoders, no tuning');
const I = X.interval;
need(I.kind === 'paired participant bootstrap' && I.level === 0.95 && I.unit === 'participant' && I.same_rule_both_encoders === true && I.prespecified === true && I.both_span_zero === true,
  'the same paired participant bootstrap in both subsections; both intervals span zero');
const CAP = X.eeg_captioner, AX = X.axon;
const spans = (iv: number[]) => iv[0] < 0 && iv[1] > 0;
for (const e of [CAP, AX] as any[]) {
  const d = e.paired_difference, enc = e.arms.find((a: any) => a.role === 'encoder'), base = e.arms.find((a: any) => a.role === 'baseline');
  need(e.arms.length === 2 && enc.id === d.a && base.id === d.b && base.id === 'welch-band-power' && enc.dimension === e.representation.dimension, `${e.id}: its encoder against Welch band power`);
  need(d.interval_includes_zero === true && spans(d.interval_95) && d.reading === SPANS_ZERO && d.interval_95[0] <= d.difference && d.difference <= d.interval_95[1], `${e.id}: the interval spans zero`);
  need(e.pretraining_exposure === 'unknown' && e.identity.frozen === true && e.identity.fine_tuning === false && e.identity.weights_distributed === false, `${e.id}: frozen, exposure unknown, no weights distributed`);
}
const capBase = CAP.arms.find(a => a.role === 'baseline')!, axBase = AX.arms.find(a => a.role === 'baseline')!;
need(capBase.balanced_accuracy === axBase.balanced_accuracy && capBase.label === axBase.label && CAP.baseline.matched === true && CAP.baseline.fitted_in_this_run === true
  && AX.baseline.matched === false && AX.baseline.fitted_in_this_run === false && AX.baseline.same_baseline_as === CAP.id && AX.baseline.isolates_pretraining === false,
  'one Welch baseline: matched and fitted for EEG-Captioner, its predictions reused for AXON');
need(CAP.encoder_only === true && CAP.caption_result === false && CAP.language_model_loaded === false && CAP.input.zero_oz_channel === true && CAP.input.amplitude_divisor === 100,
  'EEG-Captioner’s encoder only, no caption result; a zero Oz channel and division by 100');
need(AX.native_head_used === false && AX.input.zero_oz_channel === false && AX.input.divided_by_100 === false && AX.input.template_positions === true && AX.input.digitised_positions === false,
  'AXON’s own standardisation, template positions, its native head unused');
const NIC = AX.numerical_input_check;
need(NIC.windows_passed === NIC.windows && NIC.windows === C.windows && NIC.separate_from_source_qc === true, 'AXON’s own numerical input check, every window, a separate check');
need(CAP.audit.status === 'passed' && CAP.audit.rows_reproduced === C.windows && CAP.audit.raw_preprocessing_recomputed === false && CAP.audit.source_qc_recomputed === false,
  'EEG-Captioner’s audit starts at the sealed arrays');
need(AX.audit.first_audit.status === 'failed' && AX.audit.first_audit.kept === true && AX.audit.corrected_audit.status === 'passed' && AX.audit.corrected_audit.byte_identical === true
  && AX.audit.corrected_audit.tolerance_relaxed === false && AX.audit.production_unchanged === true && AX.audit.corrected_audit.rows_reproduced === C.windows,
  'AXON’s first audit failed and is kept; the corrected audit matched byte for byte; production unchanged');
need(X.encoder_contrast.published === false && X.encoder_contrast.same_inputs === false && X.encoder_contrast.axon_ran_after_outcomes_known === true, 'no encoder contrast');
const S = X.separate_from_two_second_results;
need(S.ranked_against_two_second_results === false && S.window_seconds === C.window_seconds && S.core_band_pass === false
  && S.not_ranked_against.map((x: { id: string }) => x.id).join() === 'core-matrix,frozen-rows,labram-last-block,neurolm-panel,neurorvq-panel', 'not ranked against the two-second results');
need(CAP.rights.code.licence === 'MIT' && CAP.rights.weights.licence === 'Apache-2.0' && CAP.rights.weights.distributed === false && AX.rights.checkpoint.licence === 'Apache-2.0'
  && AX.rights.checkpoint.distributed === false && AX.rights.module.licence === 'Apache-2.0' && AX.rights.project.licence === 'BSD-3-Clause'
  && X.rights.dataset.license === 'Open Data Commons Attribution License 1.0' && X.rights.dataset.rightsScope === 'Personal noncommercial research; aggregate results only',
  'the licence of each part, as the export states it');
need((X.rights.dataset.privacyReview as string).startsWith(`${CONSENT_EN} `), 'EEGMAT’s ethics and consent statement');
// The EEGMAT rights record is the NeuroLM panel's, word for word, so its credit, licence and consent print once, there.
const NL_EEGMAT = (neurolmFacts.rights as any).dataset;
need(['name', 'source', 'license', 'licenseUrl', 'attribution', 'privacyReview', 'rightsScope'].every(k => NL_EEGMAT[k] === (X.rights.dataset as any)[k]),
  'EEGMAT’s rights record here is the NeuroLM panel’s, word for word');
// The recording order the NeuroLM panel states beside its result, which this panel's limitation points to.
const neurolmCaveats = (locale: Locale) => neurolmCopy[locale].caveats().map(p => typeof p === 'string' ? p : '').join('');
export const SHARED_WITH_NEUROLM = 'recording-order';
need(X.limitations.find((l: { id: string }) => l.id === SHARED_WITH_NEUROLM)!.text === 'Rest is recorded before arithmetic, so recording order, time and artifacts move with the label; subject-disjoint folds do not remove this, and neither probe isolates cognitive workload.'
  && neurolmCaveats('en').includes('Rest is recorded before arithmetic, so recording order moves with the label.') && neurolmCaveats('zh').includes('静息在心算之前记录'),
  'the NeuroLM panel states the recording order this panel points to; the pointer keeps the rest of the export’s sentence');
need(X.limitations.map((l: { id: string }) => l.id).join() === 'recording-order,exposure,axon-inputs,upstream-recording,scope'
  && AX.limitations.map((l: { id: string }) => l.id).join() === 'pretraining-not-isolated,outcomes-known', 'the panel’s five limitations and AXON’s two');
need(X.not_published.length === 9 && /^Per-person, per-fold and per-window values/.test(X.not_published[0])
  && X.not_published.includes('Checkpoints and weights: none is distributed; each SHA-256 identifies the file used and grants nothing.'), 'the not-published list');

// --- The Chinese for the export's own sentences, keyed by the exact English. ------------------------------------
export const tenSecondZh: Record<string, string> = {
  'Do frozen EEG-Captioner or AXON features separate rest from mental arithmetic in ten-second windows better than Welch band power?':
    '冻结的 EEG-Captioner 或 AXON 特征，在十秒时间窗上区分静息与心算，比 Welch 频带功率更好吗？',
  'A separate panel: two frozen encoders on ten-second arithmetic and rest windows': '单独一栏：两个冻结编码器，十秒心算与静息时间窗',
  // The cohort block.
  'Each complete recording was filtered at 0.1–75 Hz with a 50 Hz notch and resampled to 200 Hz, then its first 60 s were cut into six ten-second windows.':
    '每段完整记录先做 0.1–75 Hz 滤波并加 50 Hz 陷波，重采样到 200 Hz，再把前 60 秒切成六个十秒时间窗。',
  'subject-disjoint: participants are sorted and dealt into the five folds in turn, so both recordings and all windows of a person stay in one fold':
    '被试不重叠：被试排序后依次分到五折中，所以一个人的两段记录和全部时间窗都在同一折里',
  '20,000 paired participant draws of the 36 participant differences in each subsection, with a 2.5–97.5 percentile interval. Both intervals span zero.':
    '每个小节对 36 个被试差值做 20,000 次配对的被试抽样，取 2.5–97.5 百分位区间。两个区间都跨过零。',
  'Each interval resamples the participant differences of this fixed cohort and its fixed predictions; training sets overlap across folds, so it describes this cohort, not a population.':
    '每个区间对这个固定队列及其固定预测的被试差值重抽样；各折的训练集相互重叠，所以它描述的是这个队列，而不是总体。',
  'EEG-Captioner’s published annotation-QC rules, run unchanged at the pinned source revision on each whole preprocessed recording, before the zero Oz channel was inserted':
    'EEG-Captioner 公开的标注质量控制规则，在固定的源代码版本下原样运行于每段完整的预处理后记录，在插入全零的 Oz 通道之前',
  'A recording is flagged when more than 0.3 of its channels are flagged or the summed duration of BAD annotations exceeds 0.2 of the recording. A channel is flagged by MNE’s adjacent-sample amplitude criteria (500 µV peak, 1 µV flat, 5% of the record, segments of at least 0.02 s); the 100 µV segment rule applies only inside a recording that passes.':
    '一段记录在以下情况被标记：被标记通道的比例超过 0.3，或 BAD 标注的总时长超过记录时长的 0.2。通道按 MNE 的相邻样本幅值标准标记（500 µV 峰值、1 µV 平坦、记录的 5%、至少 0.02 秒的片段）；100 µV 的片段规则只在通过检查的记录内部使用。',
  'The flag is set per recording at the parent-trial level. It does not say that each window has an artifact, and it is not evidence that EEGMAT as a whole is unusable.':
    '这个标记按记录设置，即在时间窗所属的整段试次这一层。它并不表示每个时间窗都有伪迹，也不是 EEGMAT 整体不可用的证据。',
  // EEG-Captioner.
  'EEG-Captioner encoder, mean-token 256-d + ridge': 'EEG-Captioner 编码器，token 均值 256 维 + 岭回归',
  'Welch band power (95-d, 0.5–45 Hz, ten-second windows)': 'Welch 频带功率（95 维，0.5–45 Hz，十秒时间窗）',
  'matched for this run': '在这次运行中作为匹配的对照拟合',
  'the 19 measured channels in microvolts with a zero Oz channel inserted, as the encoder’s loader permits, divided by 100':
    '19 个实测通道，单位为微伏，按编码器加载程序的允许插入一个全零的 Oz 通道，再除以 100',
  'the mean of the 200 output tokens of EEG-Captioner’s frozen encoder, 256 dimensions': 'EEG-Captioner 冻结编码器 200 个输出 token 的均值，256 维',
  '95 absolute log band powers: 19 channels by 5 bands (0.5–4, 4–8, 8–13, 13–30 and 30–45 Hz), Welch at 200 Hz with 400-sample Hann segments and 200-sample overlap, on the same windows':
    '95 个绝对对数频带功率：19 个通道 × 5 个频带（0.5–4、4–8、8–13、13–30 与 30–45 Hz），在同样的时间窗上以 200 Hz 做 Welch 估计，Hann 分段 400 个样本、重叠 200 个样本',
  'Only EEG-Captioner’s encoder was run; its language model, projector and language adapter were not loaded, and there is no caption result.':
    '只运行了 EEG-Captioner 的编码器；没有加载它的语言模型、投影层与语言适配器，也没有生成描述文本的结果。',
  'EEG-Captioner encoder minus Welch band power': 'EEG-Captioner 编码器减 Welch 频带功率',
  'A separately operated reconstruction, importing none of the producer’s scientific helpers, reproduced all 432 encoder and baseline feature rows exactly from the sealed preprocessed arrays. It refitted every head, reproduced every hard prediction exactly with decision scores within 1e-6 of the producer’s, and matched every score and the bootstrap. The raw preprocessing and the source QC were checked against their pinned source and hashes, not recomputed.':
    '一套单独运行、没有引入生产方任何科学计算辅助代码的重建，从封存的预处理数组精确复现了全部 432 行编码器与基线特征。它重新拟合了每个分类头，精确复现了每个硬预测，决策分数与生产方的差在 1e-6 以内，并与每个分数和 bootstrap 结果一致。原始预处理与来源质量控制是对照其固定的源代码与哈希值核查的，没有重新计算。',
  // AXON.
  'AXON, 512-d + ridge': 'AXON，512 维 + 岭回归',
  'the same predictions reused without refitting; not matched for normalisation or parameter count': '沿用同一批预测，没有重新拟合；在归一化与参数量上都不匹配',
  'the same 19 measured channels in microvolts, reordered to AXON’s channel order and standardised per channel and window inside AXON':
    '同样的 19 个实测通道，单位为微伏，按 AXON 的通道顺序重新排列，并在 AXON 内部按通道与时间窗标准化',
  'the mean over AXON’s channel and patch tokens, 512 dimensions': 'AXON 各通道与片段 token 的均值，512 维',
  'AXON minus Welch band power': 'AXON 减 Welch 频带功率',
  'every sample finite, and every channel’s sample standard deviation in every window above 1e-12 µV: numerical non-degeneracy, a separate matter from signal quality':
    '每个样本都是有限值，且每个时间窗里每个通道的样本标准差都大于 1e-12 µV：这是数值上的非退化，与信号质量是两回事',
  'The Welch comparison cannot isolate what AXON’s pretraining contributes.': '与 Welch 的比较无法单独分离出 AXON 预训练的贡献。',
  'AXON’s interval is descriptive for a second reason too: the EEG-Captioner and Welch outcomes were known before AXON ran.':
    'AXON 的区间是描述性的，还有第二个原因：AXON 运行之前，EEG-Captioner 与 Welch 的结果已经知道。',
  'AXON’s first independent audit failed its feature tolerance and is kept. The corrected audit changed only the auditor’s frozen-parameter state to match production; it reproduced all 432 production rows byte for byte under the unchanged tolerance, refitted the heads and matched every score. Production was unchanged.':
    'AXON 的第一次独立审计没有通过特征容差，这一记录予以保留。修正后的审计只把审计方的冻结参数状态改为与生产一致；在不变的容差下，它逐字节复现了全部 432 行生产特征，重新拟合了分类头，并与每个分数一致。生产结果没有改变。',
  // The two encoders, and the two-second results.
  'No EEG-Captioner against AXON difference is computed: AXON ran after the EEG-Captioner and Welch outcomes were known, and the two encoders read different inputs (a zero Oz channel and division by 100 for EEG-Captioner; reordered channels with its own standardisation for AXON).':
    '不计算 EEG-Captioner 与 AXON 之间的差值：AXON 是在 EEG-Captioner 与 Welch 的结果已知之后运行的，而且两个编码器读取的输入不同（EEG-Captioner 插入全零的 Oz 通道并除以 100；AXON 重新排列通道并用自己的标准化）。',
  'Not ranked against the two-second results on this site: the core Arithmetic & rest matrix, the REVE and EEGPT frozen rows, LaBraM last-block adaptation, the NeuroLM panel and the NeuroRVQ panel. These probes use filtered ten-second windows at 200 Hz, where the core protocol uses unfiltered two-second windows at 250 Hz, and its Spectral ridge row uses log relative spectra from 0.5–45 Hz rather than these absolute band powers.':
    '不与本站两秒时间窗的结果比较排名：核心“心算与静息”矩阵、REVE 与 EEGPT 的冻结行、LaBraM 最后一个 Transformer 块的适配、NeuroLM 一栏与 NeuroRVQ 一栏。这些探针使用 200 Hz 下经过滤波的十秒时间窗，而核心协议使用 250 Hz 下未滤波的两秒时间窗，其 spectral ridge 一行使用的是 0.5–45 Hz 的对数相对频谱，而不是这里的绝对频带功率。',
  // The panel's limitations.
  'Rest is recorded before arithmetic, so recording order, time and artifacts move with the label; subject-disjoint folds do not remove this, and neither probe isolates cognitive workload.':
    '静息在心算之前记录，所以记录顺序、时间与伪迹都随标签一起变化；被试不重叠的分折并不能消除这一点，两个探针也都不能单独分离出脑力负荷。',
  'Whether either encoder saw EEGMAT in pretraining is unknown, so exposure is shown as unknown for both.':
    '两个编码器在预训练中是否见过 EEGMAT 都不清楚，所以两者的“是否出现在预训练数据中”都标为未知。',
  'AXON reads nominal template electrode positions, not positions digitised for each person, and the cache’s 0.1–75 Hz band with a 50 Hz notch differs from the pretraining preprocessing on AXON’s model card (0.5–99.5 Hz, a 50 or 60 Hz notch, standardisation and clipping at 15 standard deviations).':
    'AXON 读取的是名义上的模板电极位置，而不是为每个人数字化测得的位置；缓存数据的 0.1–75 Hz 频带加 50 Hz 陷波，也与 AXON 模型卡上的预训练预处理不同（0.5–99.5 Hz，50 或 60 Hz 陷波，标准化并在 15 个标准差处截幅）。',
  'EEGMAT’s linked-ear reference and its upstream filtering are uncertain from the source files, and further filtering cannot restore frequencies removed before release.':
    '从源文件无法确定 EEGMAT 的双耳连接参考及其上游滤波，进一步滤波也无法恢复发布之前已被去除的频率。',
  'Frozen encoders with a supervised linear head, scored on recording condition: the filters ran over whole recordings, using context outside each window, and nothing here measures clinical use or online decoding.':
    '冻结编码器加有监督的线性分类头，按记录条件评分：滤波器在整段记录上运行，用到了每个时间窗之外的上下文；这里没有任何内容衡量临床用途或在线解码。',
  // Not published, and the rights line.
  'Per-person, per-fold and per-window values of any kind: per-fold balanced accuracy, fold assignments, participant identifiers, features, fitted heads, predictions and the sealed files. Only participant-mean balanced accuracy, paired differences with their intervals, cohort counts and the source-QC totals are published.':
    '任何逐人、逐折与逐时间窗的数值：逐折的平衡准确率、折的划分、被试标识、特征、拟合好的分类头、预测与封存的文件。只发布按被试平均的平衡准确率、配对差值及其区间、队列计数与来源质量控制的总数。',
  'EEGMAT 1.0.0: Open Data Commons Attribution License 1.0 (Zyma et al., 2019; PhysioNet). EEG-Captioner source code: MIT. EEG-Captioner encoder weights: Apache-2.0 per the Hugging Face weight metadata. AXON checkpoint: Apache-2.0 per its Hugging Face licence tag; the AXON module: per-file Apache-2.0 terms within the BSD-3-Clause Braindecode project. No weights distributed.':
    'EEGMAT 1.0.0：Open Data Commons Attribution License 1.0（Zyma 等，2019；PhysioNet）。EEG-Captioner 源代码：MIT。EEG-Captioner 编码器的权重：按 Hugging Face 权重元数据为 Apache-2.0。AXON 检查点：按其 Hugging Face 许可标签为 Apache-2.0；AXON 模块：逐文件的 Apache-2.0 条款，所在的 Braindecode 项目为 BSD-3-Clause。不分发任何权重。',
  'none is distributed; each SHA-256 identifies the file used and grants nothing': '不分发任何权重；每个 SHA-256 只用于标识所用的文件，不授予任何权利',
  [SPANS_ZERO]: neurolmZh[SPANS_ZERO],
  [CONSENT_EN]: neurolmZh[CONSENT_EN],
};
const numbersOf = (s: string) => [...s.matchAll(/\d+(?:[.,]\d+)*/g)].map(m => m[0].replace(/,/g, '')).sort().join(' ');
const dateZh = (s: string) => s.replace('2018 年 8 月 15 日', '15 August 2018').replace(/August/, '');
for (const [en, zh] of Object.entries(tenSecondZh))
  need(numbersOf(en.replace(/August/, '')) === numbersOf(dateZh(zh)), `the Chinese for "${en.slice(0, 60)}" carries exactly its English's numbers`);

/** One of the export's sentences as the page prints it: the English as released; on a Chinese page the Chinese, with the English as `original`. */
export function tenSecondText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = tenSecondZh[en];
  if (zh === undefined) throw new Error(`eegmat-ten-second.ts: no Chinese for "${en.slice(0, 80)}"`);
  return { text: zh, original: en };
}
const say = (en: string, locale: Locale) => tenSecondText(en, locale).text;

// --- Figures --------------------------------------------------------------------------------------------------
const pct2 = (raw: number) => fig(raw, 'pct2'), sgn2 = (raw: number) => fig(raw, 'sgn2'), pp2 = (raw: number) => fig(raw, 'pp2'), n = (raw: number) => fig(raw, 'count');
type Part = string | Fig;

/** The source annotation-QC totals, beside every score: the export's sentence, its numbers as figures. */
const qcParts = (zh: boolean): Part[] => zh
  ? [n(Q.windows), ' 个时间窗中有 ', n(Q.windows_meeting_rules), ' 个符合 EEG-Captioner 的来源标注质量控制规则，', n(Q.recordings), ' 段记录中有 ', n(Q.recordings_flagged), ' 段被这些规则标记。']
  : [n(Q.windows_meeting_rules), ' of ', n(Q.windows), ' windows meet EEG-Captioner’s source annotation-QC rules, and ', n(Q.recordings_flagged), ' of ', n(Q.recordings), ' recordings are flagged by them.'];
const plain = (p: Part[]) => p.map(x => typeof x === 'string' ? x : x.fmt === 'count' ? x.raw.toLocaleString('en-US') : '').join('');
need(plain(qcParts(false)) === Q.beside_every_score, 'the QC line is the export’s sentence');
/** AXON's own numerical input check, beside its score. */
const checkParts = (zh: boolean): Part[] => zh
  ? ['AXON 自己的数值输入检查在 ', n(NIC.windows), ' 个时间窗中通过了 ', n(NIC.windows_passed), ' 个，这是另一项检查']
  : ['AXON’s own numerical input check passed ', n(NIC.windows_passed), ' of ', n(NIC.windows), ', a different check'];
need(plain(checkParts(false)) === NIC.beside_score, 'the input-check line is the export’s sentence');

export interface TenSecondEncoder {
  id: string; title: string; titleEn: string; input: { text: string; original?: string }; representation: { text: string; original?: string };
  scope?: { text: string; original?: string };
  arms: { id: string; role: string; label: string; labelOriginal?: string; note?: string; noteOriginal?: string; dimension: Fig; ba: Fig }[];
  baseline?: { text: string; original?: string };
  findLabel: Part[]; findP: Part[]; diff: { d: Fig; lo: Fig; hi: Fig };
  qc: Part[]; inputCheck?: Part[]; inputRule?: { text: string; original?: string };
  limits: { id: string; text: string; original?: string }[]; audit: { text: string; original?: string };
}
const encoder = (e: any, locale: Locale): TenSecondEncoder => {
  const zh = locale === 'zh', d = e.paired_difference, enc = e.arms.find((a: any) => a.role === 'encoder'), base = e.arms.find((a: any) => a.role === 'baseline');
  const label = say(d.label, locale), axon = e.id === 'axon';
  return {
    id: e.id, title: say(e.title, locale), titleEn: e.title, input: tenSecondText(e.input.text, locale), representation: tenSecondText(e.representation.definition, locale),
    scope: e.scope ? tenSecondText(e.scope, locale) : undefined,
    arms: e.arms.map((a: any) => ({ id: a.id, role: a.role === 'encoder' ? (zh ? '编码器' : 'encoder') : (zh ? '基线' : 'baseline'),
      label: say(a.label, locale), labelOriginal: zh ? a.label : undefined, note: a.note ? say(a.note, locale) : undefined, noteOriginal: zh && a.note ? a.note : undefined,
      dimension: n(a.dimension), ba: pct2(a.balanced_accuracy) })),
    baseline: e.baseline.definition ? tenSecondText(e.baseline.definition, locale) : undefined,
    findLabel: zh ? [label, '，平衡准确率，在同样 ', n(C.people), ' 名被试上配对'] : [d.label, ', balanced accuracy, paired over the same ', n(C.people), ' people'],
    findP: zh
      ? [say(enc.label, locale), '：', pct2(enc.balanced_accuracy), '；', say(base.label, locale), '：', pct2(base.balanced_accuracy), '。配对差值为 ', sgn2(d.difference),
         ' pp（配对的 95% 被试 bootstrap 区间 ', sgn2(d.interval_95[0]), ' 至 ', sgn2(d.interval_95[1]), `）：${neurolmZh[SPANS_ZERO]}。`]
      : [enc.label, ': ', pct2(enc.balanced_accuracy), '; ', base.label, ': ', pct2(base.balanced_accuracy), '. The paired difference is ', sgn2(d.difference),
         ' points (95% participant-bootstrap interval ', sgn2(d.interval_95[0]), ' to ', sgn2(d.interval_95[1]), `): ${SPANS_ZERO}.`],
    diff: { d: pp2(d.difference), lo: sgn2(d.interval_95[0]), hi: pp2(d.interval_95[1]) },
    qc: qcParts(zh), inputCheck: axon ? checkParts(zh) : undefined, inputRule: axon ? tenSecondText(NIC.rule, locale) : undefined,
    limits: axon ? e.limitations.map((l: { id: string; text: string }) => ({ id: l.id, ...tenSecondText(l.text, locale) })) : [],
    audit: tenSecondText(e.audit.text, locale),
  };
};
/** The two subsections, EEG-Captioner's first, as the export orders them. */
export const tenSecondEncoders = (locale: Locale): TenSecondEncoder[] => [encoder(CAP, locale), encoder(AX, locale)];
/**
 * The panel's limitations, in the export's order; AXON's input mismatch sits in AXON's subsection. The recording order,
 * which the NeuroLM panel states beside its result, prints as a line pointing there, with what this export adds.
 */
export const AXON_PANEL_LIMIT = 'axon-inputs';
export interface TenSecondLimit { id: string; text: string; original?: string; shared?: { lead: string; link: string; rest: string } }
export const tenSecondLimits = (locale: Locale, where: 'panel' | 'axon'): TenSecondLimit[] => X.limitations.filter((l: { id: string }) => (l.id === AXON_PANEL_LIMIT) === (where === 'axon'))
  .map((l: { id: string; text: string }) => {
    if (l.id !== SHARED_WITH_NEUROLM) return { id: l.id, ...tenSecondText(l.text, locale) };
    const r = tenSecondCopy[locale].sharedRef;
    return { id: l.id, text: `${r.lead}${r.link}${r.rest}`, shared: r };
  });
/** What is not published: the export's first item. The rest repeat the subsections and credits, or name working files. */
export const tenSecondNotPublished = (locale: Locale) => [tenSecondText(X.not_published[0], locale)];
const WEIGHTS = X.not_published.find((s: string) => s.startsWith('Checkpoints and weights: '))!.replace('Checkpoints and weights: ', '').replace(/\.$/, '');
need(WEIGHTS === 'none is distributed; each SHA-256 identifies the file used and grants nothing', 'no weights distributed, each SHA-256 an identifier only (the credits’ line follows it)');
export const tenSecondFacts = { question: X.question as string, cohort: C, qc: Q, probe: PR, interval: I, captioner: CAP, axon: AX, rights: X.rights, separation: S,
  contrast: X.encoder_contrast, schema: X.schema_version as string, weights: WEIGHTS };

export const tenSecondCopy = {
  en: {
    eyebrow: 'Human · scalp EEG · mental arithmetic and rest · EEGMAT · EEG-Captioner and AXON, frozen',
    h2: X.title as string,
    label: 'Locally executed experiment · offline · whole participants held out · outside the pilot count above',
    lede: (): Part[] => [X.question, ' Both encoders stay frozen. Each representation is read by one fixed ridge head (alpha ', n(PR.alpha), ') in ', n(C.folds),
      ' subject-disjoint folds on the same ', n(C.windows), ' ten-second windows from ', n(C.people),
      ' people, and each encoder is set against Welch band power on the same windows. Scores are participant-mean balanced accuracies; each paired difference carries a participant-bootstrap interval.'],
    cohortH3: 'The cohort and the shared steps',
    cohort: (): Part[] => [n(C.people), ' people, ', n(C.recordings), ' recordings, ', n(C.windows), ' ten-second windows, ', n(C.channels), ' channels at ', n(C.sampling_hz), ' Hz, ', n(C.folds), ' folds. '],
    probe: (): Part[] => ['The head: a standard scaler fitted on the training folds only, then a ridge classifier with alpha ', n(PR.alpha),
      ', the SVD solver, balanced class weights and no hyperparameter search, ', n(PR.fits_per_representation), ' fits per representation, each prediction sealed before scoring; the same head reads both encoders.'],
    qcH: 'Source annotation QC:',
    colRep: 'Representation', colRole: 'Role', colDim: 'Dimension', colBa: 'Balanced accuracy',
    region: (t: string) => `${t}: balanced accuracy beside the Welch band-power baseline`,
    caption: (): Part[] => ['Participant means over the ', n(C.people), ' people, each scored by heads fitted without them.'],
    inputH: 'Input:', repH: 'Representation:', baseH: 'Baseline:',
    findH3: 'The interval spans zero',
    inputRuleH: 'The check:',
    otherH3: 'What else bounds this panel',
    coreLink: 'The core Arithmetic & rest matrix →',
    notPubH3: 'Not published here',
    dataUse: 'what this release publishes, on the data-use page →',
    creditsH3: 'Credits, licences and consent',
    eegmatH: 'EEGMAT, the recordings', datasetPage: 'Dataset page →',
    eegmatCreditRef: 'Credit, ethics and consent: in the NeuroLM panel’s credits above ↑',
    sharedRef: { lead: 'EEGMAT’s recording order (rest before arithmetic), ', link: 'stated in the NeuroLM panel above ↑',
      rest: ', holds for these windows too: time and artifacts also move with the label, subject-disjoint folds do not remove this, and neither probe isolates cognitive workload.' },
    captionerH: 'EEG-Captioner, the encoder', axonH: 'AXON',
    model: 'Model:', code: 'code:', source: 'Code:', checkpoint: 'checkpoint', at: 'at', encoderFile: 'Encoder:', sha: 'SHA-256', module: 'module',
    capLicence: (): Part[] => [`EEG-Captioner’s code: ${CAP.rights.code.licence}. EEG-Captioner’s encoder weights: ${CAP.rights.weights.licence}, as stated by `, CAP.rights.weights.as_stated_by, '.'],
    axLicence: (): Part[] => [`AXON’s checkpoint: ${AX.rights.checkpoint.licence}, as stated by `, AX.rights.checkpoint.as_stated_by, `. The AXON module: ${AX.rights.module.licence}, `, AX.rights.module.scope,
      `, within a ${AX.rights.project.licence} project (`, AX.rights.project.scope, ').'],
    weights: 'No weights are distributed; each SHA-256 identifies the file used and grants nothing.',
    endorse: 'Derived analysis by BCI Report, aggregates only; not endorsed by EEG-Captioner’s or AXON’s authors or the data’s authors, and no raw data are redistributed.',
    dataSource: 'Data source:', schema: 'schema',
  },
  zh: {
    eyebrow: '人类 · 头皮 EEG · 心算与静息 · EEGMAT · 冻结的 EEG-Captioner 与 AXON',
    h2: tenSecondZh[X.title],
    label: '本站在本地运行的实验 · 离线 · 整名被试留出 · 不计入上面的试点数',
    lede: (): Part[] => [tenSecondZh[X.question], '两个编码器都保持冻结。每种表示都由一个固定的岭回归分类头（alpha ', n(PR.alpha), '）读出，分 ', n(C.folds),
      ' 折、被试不重叠，用的是同一批 ', n(C.windows), ' 个十秒时间窗（', n(C.people),
      ' 名被试）；每个编码器都与同一批时间窗上的 Welch 频带功率比较。分数是按被试平均的平衡准确率；每个配对差值都附有被试 bootstrap 区间。'],
    cohortH3: '队列与共用的步骤',
    cohort: (): Part[] => [n(C.people), ' 名被试，', n(C.recordings), ' 段记录，', n(C.windows), ' 个十秒时间窗，', n(C.channels), ' 个通道，', n(C.sampling_hz), ' Hz，', n(C.folds), ' 折。'],
    probe: (): Part[] => ['分类头：先用只在训练折上拟合的标准化，再接 alpha 为 ', n(PR.alpha),
      '、用 SVD 求解、类别平衡、不搜索超参数的岭回归分类器，每种表示拟合 ', n(PR.fits_per_representation), ' 次，每个预测都在评分前封存；两个编码器用的是同一个分类头。'],
    qcH: '来源标注质量控制：',
    colRep: '表示', colRole: '作用', colDim: '维度', colBa: '平衡准确率',
    region: (t: string) => `${t}：平衡准确率，与 Welch 频带功率基线并列`,
    caption: (): Part[] => [n(C.people), ' 名被试的均值，每名被试都由训练时没有用到其数据的分类头评分。'],
    inputH: '输入：', repH: '表示：', baseH: '基线：',
    findH3: '区间跨过零',
    inputRuleH: '检查内容：',
    otherH3: '这一栏的其他局限',
    coreLink: '核心“心算与静息”矩阵 →',
    notPubH3: '这里不发布的内容',
    dataUse: '这次发布的内容，见数据使用页面（英文）→',
    creditsH3: '署名、许可与知情同意',
    eegmatH: 'EEGMAT：记录数据', datasetPage: '数据集页面 →',
    eegmatCreditRef: '署名、伦理与知情同意：见上面 NeuroLM 一栏的署名 ↑',
    sharedRef: { lead: 'EEGMAT 的记录顺序（静息在心算之前，', link: '见上面 NeuroLM 一栏 ↑',
      rest: '）同样适用于这些时间窗：时间与伪迹也随标签一起变化，被试不重叠的分折并不能消除这一点，两个探针也都不能单独分离出脑力负荷。' },
    captionerH: 'EEG-Captioner：编码器', axonH: 'AXON',
    model: '模型：', code: '代码：', source: '代码：', checkpoint: '检查点：', at: ' 版本 ', encoderFile: '编码器文件的 ', sha: 'SHA-256：', module: '模块：',
    capLicence: (): Part[] => ['EEG-Captioner 的代码：MIT。EEG-Captioner 编码器的权重：Apache-2.0，依据 Hugging Face 仓库在固定版本下可移植的权重元数据。'],
    axLicence: (): Part[] => ['AXON 的检查点：Apache-2.0，依据 Hugging Face 仓库在固定版本下的许可标签。AXON 模块：Braindecode 中 AXON 模块的逐文件条款为 Apache-2.0，所在的 Braindecode 项目根目录许可为 BSD-3-Clause。'],
    weights: `${tenSecondZh[WEIGHTS]}。`,
    endorse: '以上为 BCI Report 的衍生分析，只发布聚合结果；不代表 EEG-Captioner 或 AXON 作者以及数据作者的认可，也不再分发任何原始数据。',
    dataSource: '数据来源：', schema: 'schema',
  },
};
need(CAP.rights.weights.as_stated_by === 'the portable weight metadata of the Hugging Face repository at the pinned revision'
  && AX.rights.checkpoint.as_stated_by === 'the licence tag of the Hugging Face repository at the pinned revision'
  && AX.rights.module.scope === 'the per-file terms of the AXON module in Braindecode' && AX.rights.project.scope === 'the licence at the Braindecode project root',
  'the licence sources as the export words them (their Chinese above follows them)');
// Every licence sentence that names Apache-2.0 names its own model, EEG-Captioner or AXON, and never EEGPT (whose weights
// the site never calls Apache-2.0); the pointers to the NeuroLM panel carry no figure.
for (const c of Object.values(tenSecondCopy)) {
  const text = [...c.capLicence(), ...c.axLicence()].map(p => typeof p === 'string' ? p : '').join('');
  need(text.split(/(?<=\.)\s+|(?<=。)/).filter(s => /Apache/.test(s)).every(s => /EEG-Captioner|AXON/.test(s) && !/EEGPT/.test(s)), 'each Apache-2.0 line names its model');
  need(!/\d/.test(Object.values(c.sharedRef).join('') + c.eegmatCreditRef), 'the pointers to the NeuroLM panel carry no figure');
}

/**
 * The panel's results as it prints them, unsigned and without units, at two decimals: each arm's balanced accuracy and
 * each paired difference and bound. A text that prints one of them, or names either encoder, carries the panel.
 */
export const tenSecondResultNumbers: Set<string> = new Set([CAP, AX].flatMap((e: any) => [
  ...e.arms.map((a: any) => a.balanced_accuracy), e.paired_difference.difference, ...e.paired_difference.interval_95,
]).map((v: number) => Math.abs(v * 100).toFixed(2)));
export const carriesTenSecond = (text: string): boolean =>
  /EEG-Captioner|\bAXON\b/i.test(text) || [...text.matchAll(/\d+(?:\.\d+)?/g)].some(m => tenSecondResultNumbers.has(m[0]));

/**
 * The line on the Arithmetic & rest protocol page that links both panels, beside its NeuroLM pointer: no figure and no
 * digit, one link to each panel.
 */
export const arithmeticPanelsPointer = {
  en: { lead: 'Frozen-encoder probes with their own preprocessing are on the pilot studies page: ', neurorvq: 'NeuroRVQ on three tasks →', tenSecond: 'EEG-Captioner and AXON on ten-second windows →' },
  zh: { lead: '另有使用自己预处理流程的冻结编码器探针，见试点研究页面：', neurorvq: 'NeuroRVQ，三项任务 →', tenSecond: 'EEG-Captioner 与 AXON，十秒时间窗 →' },
};
need(Object.values(arithmeticPanelsPointer).every(p => Object.values(p).every(s => !/\d/.test(s))), 'the pointer carries no figure');
