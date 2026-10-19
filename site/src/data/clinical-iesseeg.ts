/**
 * IESSEEG on the clinical-groups page (owner decision D13, release clinical-iesseeg-update-20261020): a section with
 * its own question after the Parkinson's comparison, whose heading, short answer, description and card keep their
 * wording. Six arms with and without EEG (a training prior, age only, recording settings only, EEG spectral features,
 * EEG with age, EEG after training-fold age residualization) and four arms that read frozen NeuroLM-B states with the
 * same probe, on the same 100 people and folds. Point estimates out of fold, balanced accuracy and AUROC for every arm
 * and the age ≤2 band's balanced accuracy (owner decision D7, option A); F1 is in the file and stays out of the page.
 *
 * Read from the served file and nothing else (clinical-iesseeg-update.json). Every figure is a `Fig` naming that file,
 * printed with data-fig and re-read by the checks; prose figures are marked by `mark`, which refuses a number the file
 * does not hold. The English of the export's sentences prints as released; their Chinese is keyed by that English
 * (`ZH`), so a changed export without a matching translation fails the build. The facts every sentence rests on are
 * guarded below, and the build stops when the file no longer supports them.
 *
 * Rules carried from the release reviews and the owner decisions: all ten arms shown; both metric columns shown and
 * no arm named ahead of another; the shared caption once; the audit boundary prominent; the NeuroLM footnote beside
 * its table; the clinical page's medical disclaimer reused; consent and HIPAA authorization were waived, as the
 * release card states; attribution from the release card at the pinned revision only.
 */
import ies from './clinical-iesseeg-update.json';
import clinical from './clinical-update.json';
import { formatFig, type Fig, type Fmt } from './entities';
import type { Locale } from './i18n';

export const IES_FILE = 'clinical-iesseeg-update.json';
export const IES_PATH = `/data/${IES_FILE}`;
const X = ies as any;
type Part = string | Fig;

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`clinical-iesseeg.ts: the copy says ${what}`); };
const says = (text: string, ...xs: string[]) => xs.forEach(x => need(typeof text === 'string' && text.includes(x), `"${x}" (the export says otherwise)`));
export const fig = (raw: number, fmt: Fmt = 'count'): Fig => ({ raw, fmt, src: IES_FILE });
const n = (raw: number) => fig(raw, 'count');
const ba = (raw: number) => fig(raw, 'pct2');
const au = (raw: number) => fig(raw, 'auc3');

/**
 * Text with its numbers marked: every number in it must print as one of `figs` (by its printed form), and becomes that
 * Fig. A number glued to a letter or hyphen (L2, log1p, SHA-256) is part of a word and is left alone.
 */
export function mark(text: string, figs: Fig[], where: string): Part[] {
  const byText = new Map<string, Fig>();
  for (const f of figs) {
    const t = formatFig(f), prev = byText.get(t);
    need(!prev || prev.raw === f.raw, `${where}: "${t}" prints two different values`);
    byText.set(t, f);
  }
  const out: Part[] = [];
  let at = 0;
  for (const m of text.matchAll(/(?<![\w.\-])\d(?:\d|,(?=\d{3}))*(?:\.\d+)?%?(?![\w\-])/g)) {
    const f = byText.get(m[0]);
    need(f, `${where}: "${m[0]}" is a figure of ${IES_FILE}`);
    if (m.index! > at) out.push(text.slice(at, m.index));
    out.push(f!);
    at = m.index! + m[0].length;
  }
  if (at < text.length) out.push(text.slice(at));
  return out;
}

// --- The export, and the facts the section rests on. ---------------------------------------------------------------
const C = X.cohort, B = X.age_band, Q = X.input_qc, D = X.display, CM = X.controls.method, NM = X.neurolm.method, M = X.neurolm.model;
need(X.schema_version === 'bci-report-clinical-iesseeg-update-v1' && X.release_id === 'clinical-iesseeg-update-20261020', 'the served file is the IESSEEG release');
need(X.placement.page === '/topics/clinical-groups/' && X.placement.section === 'iesseeg' && X.placement.after === 'ds004584'
  && X.placement.subsections.join() === 'iesseeg-controls,iesseeg-neurolm' && X.placement.leaderboard === false && X.placement.dataset_page === false,
  'a section of the clinical-groups page after the Parkinson\'s comparison, with no leaderboard and no dataset page');
need(X.counts.new_canonical_datasets === 0 && X.counts.new_dataset_pages === 0 && X.counts.new_model_identity === false, 'no count changes');
need(X.medical_disclaimer === true && X.medical_disclaimer_wording.file === 'clinical-update.json' && X.medical_disclaimer_wording.field === 'medical_disclaimer'
  && typeof clinical.medical_disclaimer === 'string', 'the clinical page\'s medical disclaimer applies, in its own wording');
export const IES_ANCHORS = { section: X.placement.section as string, controls: X.controls.anchor as string, neurolm: X.neurolm.anchor as string };
need(IES_ANCHORS.controls === 'iesseeg-controls' && IES_ANCHORS.neurolm === 'iesseeg-neurolm', 'the two anchors');
// The cohort.
need(C.cases + C.controls === C.people && C.cases === C.controls && C.classes === 2 && C.chance_level === 0.5, 'balanced cases and controls, two classes');
says(C.composition, 'infantile epileptic spasms syndrome', 'before the treatment the source study evaluated', 'one institution’s retrospective cohort');
says(C.recording, 'one clinician-selected awake segment per person', 'fixed lexicographic rule with no signal-driven choice', `its first ${C.seconds_analysed} s`);
says(C.reference, `common average of the ${C.channels} channels shared by every recording`);
says(C.split, 'the publisher’s five participant-disjoint folds', 'each person is held out once');
need(C.folds === 5 && C.train_people + C.held_out_people === C.people && C.held_out_people * C.folds === C.people
  && C.held_out_cases === C.held_out_controls, 'five folds, each holding out a fifth of the people, cases and controls alike');
// The age band (D7, option A): the band's size and its case and control counts; nothing refitted.
need(B.maximum_age_years === 2 && B.cases + B.controls === B.people && B.same_predictions === true && B.refit === false, 'the age ≤2 band re-scores the same predictions');
// Input check.
const rate = (hz: number) => Q.sampling_hz.find((x: any) => x.hz === hz);
const chans = (k: number) => Q.scalp_channels.find((x: any) => x.channels === k);
need(Q.recordings === C.people && Q.recordings_passed === Q.recordings && Q.recordings_held === 0 && Q.recordings_with_gaps === 0, 'every recording passed, none held, none with gaps');
need(Q.scalp_channels.reduce((s: number, x: any) => s + x.recordings, 0) === Q.recordings && Q.sampling_hz.reduce((s: number, x: any) => s + x.recordings, 0) === Q.recordings
  && chans(19) && chans(17) && rate(200) && rate(2000) && rate(2000).recordings === 2, 'two channel counts and two rates; two recordings at 2,000 Hz');
says(Q.checked_by, 'independent read-only audit of every input file’s hash, timing and calibration');
// The display rule.
need(D.columns.map((c: any) => `${c.block}/${c.metric}`).join() === 'pooled/balanced_accuracy,pooled/auroc,age_le_2/balanced_accuracy'
  && D.primary_metric === 'balanced_accuracy' && D.interval === null && D.f1_headline === false, 'three columns, balanced accuracy primary, no interval, no F1 headline');
says(D.reading_rule, 'Both metric columns are shown for every arm', 'no arm or threshold is chosen from these results');
// The spectral arms' method.
says(CM.spectra, 'Welch spectra at each recording’s native rate', 'log relative power in five bands from 1 to 45 Hz', `log total 1–45 Hz power for each of the ${C.channels} channels`);
need(CM.feature_count === C.channels * CM.features_per_channel && CM.features_per_channel === CM.bands_hz.length + 1 && CM.bands_hz.length === 5
  && CM.bands_hz[0][0] === 1 && CM.bands_hz[4][1] === 45 && CM.welch_overlap === 0.5, 'six features per channel, five bands from 1 to 45 Hz, half-overlapping windows');
says(CM.classifier, 'standardisation fitted on the training fold only', 'L2 logistic regression', 'fixed in advance, with no tuning');
need(CM.logistic_c === 1, 'C = 1');
says(CM.age_terms, 'log1p of age at the recording', 'and its square');
says(CM.age_residualization, 'inside each training fold', 'regressed on an intercept and the two age terms', 'training-fold coefficients are applied to the training and held-out people');
says(CM.acquisition_terms, 'original scalp channel count (17 or 19)', 'native sampling rate (200 or 2,000 Hz)');
// NeuroLM.
need(M.name === 'NeuroLM-B' && M.weights_updated === false && M.text_tokens === 0 && M.generation === false && M.redistributed === false
  && M.checkpoint_stage === 'unknown' && M.pretraining_exposure === 'unknown' && /^[0-9a-f]{64}$/.test(M.checkpoint_sha256)
  && /^[0-9a-f]{40}$/.test(M.source_revision) && M.source_url === `${M.repository}/tree/${M.source_revision}`, 'NeuroLM-B frozen, no text, not redistributed, stage and exposure unknown');
says(M.use, 'a frozen feature extractor read by supervised logistic probes');
need(NM.windows * NM.window_seconds === C.seconds_analysed && NM.tokens_per_window === C.channels * NM.window_seconds / NM.token_seconds && NM.token_seconds === 1
  && NM.sampling_hz === rate(200).hz && NM.resample_factor === 10 && NM.bandpass_hz.length === 2 && NM.notch_hz.length === 2, 'windows, tokens and rates');
says(NM.tokens, 'one token per channel and second');
says(NM.representations, 'tokenizer states after its final normalisation', 'GPT hidden states after the final layer normalisation', 'averaged over the tokens of a window, then over the windows');
says(NM.probe, 'the classifier and the age residualization of the spectral arms, unchanged');
says(X.neurolm.footnote, 'preprocessing differs', 'training stage and its prior exposure to these participants are unknown');
// The audits.
const CA = X.controls.audit, NA = X.neurolm.audit;
need(CA.status === 'pass' && CA.models === CA.learned_refits + CA.prior_checks && CA.max_probability_error === 0 && CA.reconstructed_predictions === C.people * X.controls.arms.length
  && CA.independent_feature_checks === Q.scalp_channels.length * Q.sampling_hz.length, 'the CPU audit passed: every model refit, every prior checked, every probability rebuilt, one recording per group recomputed');
need(NA.status === 'pass' && NA.reconstruction_error === 0 && NA.refit_error === 0 && NA.held_out_predictions_reconstructed === C.people * X.neurolm.arms.length
  && NA.independent_refits === C.folds * X.neurolm.arms.length && NA.source_hash_checks === Q.assets && NA.feature_receipts_checked === C.people
  && NA.real_neural_features_independently_recomputed === false, 'the NeuroLM audit passed, and the features were not re-extracted');
says(X.audit_boundary, 'reproduced independently', 'not re-extracted by a second implementation');
// Rights, consent and attribution: the release card at the pinned revision, nothing else.
const DS = X.dataset, RT = X.rights;
need(DS.repository === 'Capur/IESSEEG' && /^[0-9a-f]{40}$/.test(DS.revision) && DS.url.endsWith(`/tree/${DS.revision}`) && DS.release_card_url.endsWith(`/blob/${DS.revision}/README.md`)
  && DS.licence_file_url.endsWith(`/blob/${DS.revision}/LICENSE`) && DS.licence === 'CC-BY-4.0' && RT.license === DS.licence && RT.licenseUrl === DS.licence_deed
  && DS.attribution_source === 'the release card and LICENSE at the pinned revision' && RT.redistributed === false, 'the release card and LICENSE at the pinned revision');
says(RT.attribution, DS.requested_citation, `${DS.prior_reuse.case_segments} case clinician-selected segments`, DS.prior_reuse.study, DS.prior_reuse.study_title);
says(DS.ethics_as_stated.quote, 'institutional review board approval', 'waivers of informed consent and HIPAA research authorization', 'Do not attempt to re-identify participants');
says(RT.privacyReview, 'waivers of informed consent and HIPAA research authorization', 'aggregate scores only');
const protocolNo = (DS.ethics_as_stated.quote.match(/under protocol ([\d-]+),/) ?? [])[1];
need(protocolNo, 'the protocol number, as the card states it');
// Nothing in the printed strings points at a submission.
{
  const printed = JSON.stringify([X.question, X.caption, X.audit_boundary, X.limitations, X.neurolm.footnote, B.note, RT, DS.prior_reuse, CA.what, NA.what]);
  need(!/ICLR|OpenReview|openreview|submission/i.test(printed), 'nothing about a submission');
}

// --- Chinese for the export's sentences, keyed by their English. -------------------------------------------------
const ZH: Record<string, string> = {
  'Do EEG case-control results survive age and recording-setting controls?': 'EEG 病例对照结果经得起年龄与采集设置校正吗？',
  'Age and acquisition controls for an awake EEG case-control pilot': '清醒期 EEG 病例对照试点中的年龄与采集设置对照',
  'Do frozen EEG representations survive age controls?': '冻结的 EEG 表示经得起年龄校正吗？',
  'Point estimates out of fold; no interval or test was specified. One awake recording per person, first 60 s. Age and recording settings differ between groups; regressing out age is a sensitivity analysis.':
    '折外点估计；事先没有指定区间或检验。每人一段清醒期记录，取前 60 秒。两组之间年龄与采集设置不同；回归掉年龄是一项敏感性分析。',
  'The probes and every score were reproduced independently; the NeuroLM features themselves were not re-extracted by a second implementation.':
    '分类头与每一个分数都经过独立复现；NeuroLM 特征本身没有用第二套实现重新提取。',
  'NeuroLM’s preprocessing differs from the spectral pipeline: the two 2,000 Hz recordings are resampled to 200 Hz, then a 0.1–75 Hz band-pass, 50 and 60 Hz notches and division by 100. A difference between the two pipelines therefore mixes preprocessing with architecture. The checkpoint’s training stage and its prior exposure to these participants are unknown.':
    'NeuroLM 的预处理与频谱流程不同：两段 2,000 Hz 的记录先重采样到 200 Hz，再做 0.1–75 Hz 带通、50 与 60 Hz 陷波，并除以 100。因此两条流程之间的差异混合了预处理与模型结构。检查点的训练阶段，以及它此前是否接触过这些被试，都是未知的。',
  'The age ≤2 column re-scores the same out-of-fold predictions for the people aged 2 or under, with nothing refitted; it is a descriptive subgroup. Only the band’s size and its case and control counts are published; per-group age means and sex counts stay unpublished.':
    '“≤2 岁”一栏沿用同一批折外预测，只对 2 岁及以下的被试重新计分，没有重新拟合任何模型；这是一个描述性的亚组。只发布这一年龄段的人数及其中病例与对照的人数；各组的年龄均值与性别人数不发布。',
  'A small awake-only case-control development cohort from one institution. Labels are each participant’s case or control status, with no timed spasm events. There is no external or clinical validation, and the publisher’s full benchmark is outside this pilot.':
    '来自单一机构的小规模病例对照开发队列，只含清醒期记录。标签是每名被试的病例或对照身份，没有带时间标注的痉挛事件。没有外部验证或临床验证；发布者的完整基准不在本试点范围之内。',
  'Regressing out age inside each training fold assigns no share of the score to age, does not show that confounding is gone, and can also remove disease-related signal that varies with age.':
    '在每个训练折内回归掉年龄，并不能把分数的任何一部分归给年龄，也不能说明混杂已经消除，还可能同时去掉随年龄变化、与疾病相关的信号。',
  'Recording settings (channel count and sampling rate) are a no-EEG diagnostic control, shown beside the EEG rows and kept out of model comparisons.':
    '采集设置（通道数与采样率）是一个不用 EEG 的检查用对照，与 EEG 各行并排列出，不参与模型之间的比较。',
  'NeuroLM is used as a frozen feature extractor read by supervised logistic probes: its weights are unchanged, and there is no text prompt, text generation or zero-shot diagnosis.':
    'NeuroLM 在这里作为冻结的特征提取器使用，由有监督的逻辑回归分类头读取：权重保持不变，没有文本提示、文本生成，也没有零样本诊断。',
  'The release card states institutional review board approval of the retrospective study, with waivers of informed consent and HIPAA research authorization, and asks that no one attempt to re-identify participants. The publication boundary is the one the Parkinson’s comparison uses: aggregate scores only, with no participant rows, predictions, ages or per-group age and sex composition; the age ≤2 column gives the band’s size and its case and control counts.':
    '发布卡片写明，这项回顾性研究获得了机构审查委员会的批准，并豁免了知情同意与 HIPAA 研究授权，同时要求任何人不得尝试重新识别被试。发布边界与帕金森病比较相同：只发布聚合分数，不发布逐被试数据、预测、年龄，也不发布各组的年龄与性别构成；“≤2 岁”一栏只给出该年龄段的人数及其中病例与对照的人数。',
  'The participant-level crosswalk between that analysis and this release is unresolved; the cohort adds no dataset to any count.':
    '上述先前分析与本次发布在被试层面的对应关系尚未厘清；该队列不计入任何数据集计数。',
  'An independent program refit every learned model, checked every prior, rebuilt every held-out probability with zero difference, and recomputed the features of one recording per channel-count and sampling-rate group with its own EDF reader and FFT.':
    '一个独立程序重新拟合了每一个学习得到的模型，核对了每一个先验，以零差异重建了每一个留出概率，并用自己的 EDF 读取器与 FFT，为每种通道数与采样率组合各重算了一段记录的特征。',
  'An independent program refit every probe and rebuilt every held-out probability with zero difference, checked every input file’s hash, and checked each feature file’s hash, layout and finiteness.':
    '一个独立程序重新拟合了每一个分类头，以零差异重建了每一个留出概率，核对了每个输入文件的哈希，并核对了每个特征文件的哈希、布局与数值有限性。',
  'Endpoint and constant-sample counts were kept as descriptions; no recording was excluded on them.':
    '记录端点与恒定样本的计数只作描述保留；没有任何记录因此被排除。',
  // Arm labels and inputs.
  'Training prior': '训练集先验',
  'No input: the training fold’s share of cases, which calls every person a case': '没有输入：训练折中病例所占的比例，因此把每个人都判为病例',
  'Age only': '只用年龄',
  'No EEG: log1p of age at the recording, and its square': '不用 EEG：记录时年龄的 log1p 及其平方',
  'Acquisition metadata only': '只用采集元数据',
  'No EEG: the original scalp channel count and sampling rate': '不用 EEG：原始头皮通道数与采样率',
  'EEG spectral features': 'EEG 频谱特征',
  'The 102 log band-power features of the 17 channels': '17 个通道的 102 个对数频带功率特征',
  'EEG spectral features + age': 'EEG 频谱特征 + 年龄',
  'The 102 spectral features and the two age terms': '102 个频谱特征加上两个年龄项',
  'EEG after training-fold age residualization': '训练折内回归掉年龄后的 EEG',
  'The 102 spectral features with age regressed out inside each training fold': '在每个训练折内回归掉年龄后的 102 个频谱特征',
  'Frozen EEG tokenizer': '冻结的 EEG 分词器',
  'The 768 frozen tokenizer values of each person': '每名被试的 768 个冻结分词器特征值',
  'Tokenizer + training-fold age residualization': '分词器 + 训练折内回归掉年龄',
  'The tokenizer values with age regressed out inside each training fold': '在每个训练折内回归掉年龄后的分词器特征值',
  'Frozen GPT hidden states': '冻结的 GPT 隐藏状态',
  'The 768 frozen GPT hidden-state values of each person': '每名被试的 768 个冻结 GPT 隐藏状态值',
  'GPT hidden states + training-fold age residualization': 'GPT 隐藏状态 + 训练折内回归掉年龄',
  'The GPT hidden-state values with age regressed out inside each training fold': '在每个训练折内回归掉年龄后的 GPT 隐藏状态值',
  // Column labels.
  'Balanced accuracy, all 100': '平衡准确率，全部 100 人',
  'AUROC, all 100': 'AUROC，全部 100 人',
  'Balanced accuracy, age ≤2 years': '平衡准确率，≤2 岁',
};
/** The export's English on the English page; its Chinese on the Chinese page. English with no Chinese fails the build. */
const tr = (en: string, locale: Locale) => {
  if (locale === 'en') return en;
  need(en in ZH, `a Chinese rendering of "${en}"`);
  return ZH[en];
};

// --- Figures. ------------------------------------------------------------------------------------------------------
const cohortFigs = [n(C.people), n(C.cases), n(C.controls), n(C.seconds_analysed), n(C.channels), n(C.folds), n(C.train_people), n(C.held_out_people)];
const bandFigs = [n(B.maximum_age_years), n(B.people), n(B.cases), n(B.controls)];
const featureFigs = [n(CM.feature_count), n(C.channels), n(NM.dimensions)];
const preFigs = [n(rate(2000).hz), n(NM.sampling_hz), n(NM.bandpass_hz[0]), n(NM.bandpass_hz[1]), n(NM.notch_hz[0]), n(NM.notch_hz[1]), n(NM.amplitude_divisor)];

export interface IesRow { id: string; label: string; inputs: Part[]; eeg: boolean; ba: Fig; auroc: Fig; ba2: Fig }
const row = (a: any, locale: Locale): IesRow => {
  need(a.pooled.n === C.people && a.age_le_2.n === B.people, `${a.id} is scored on all ${C.people} people and the ${B.people} in the band`);
  need(a.excluded_from_model_comparisons === !a.eeg_input, `${a.id}: the arms with no EEG input are kept out of model comparisons`);
  return { id: a.id, label: tr(a.label, locale), inputs: mark(tr(a.inputs, locale), featureFigs, `${a.id} inputs`), eeg: a.eeg_input,
           ba: ba(a.pooled.balanced_accuracy), auroc: au(a.pooled.auroc), ba2: ba(a.age_le_2.balanced_accuracy) };
};
const arms = (block: any) => Object.fromEntries(block.arms.map((a: any) => [a.id, a]));
const CPU = arms(X.controls), NEU = arms(X.neurolm);
need(X.controls.arms.map((a: any) => a.id).join() === 'SOURCE_PRIOR,AGE,ACQUISITION_METADATA,EEG,EEG_PLUS_AGE,AGE_RESIDUAL_EEG', 'six CPU arms, the three with no EEG first');
need(X.neurolm.arms.map((a: any) => a.id).join() === 'TOKENIZER,TOKENIZER_AGE_RESIDUAL,GPT_HIDDEN,GPT_HIDDEN_AGE_RESIDUAL', 'four neural arms');
need(X.controls.arms.slice(0, 3).every((a: any) => !a.eeg_input) && X.controls.arms.slice(3).every((a: any) => a.eeg_input) && X.neurolm.arms.every((a: any) => a.eeg_input),
  'the CPU table splits into three arms without EEG and three with it; every neural arm reads EEG');
need(CPU.SOURCE_PRIOR.role === 'reference' && CPU.SOURCE_PRIOR.pooled.balanced_accuracy === C.chance_level && CPU.SOURCE_PRIOR.pooled.sensitivity === 1,
  'the training prior calls every person a case and sits on chance');
// The reading paragraph's words, held to the arms they name.
says(CPU.AGE.inputs, 'No EEG', 'age at the recording'); says(CPU.ACQUISITION_METADATA.inputs, 'No EEG', 'channel count and sampling rate');
says(CPU.EEG.inputs, 'log band-power features'); says(CPU.EEG_PLUS_AGE.inputs, 'spectral features and the two age terms');
says(CPU.AGE_RESIDUAL_EEG.inputs, 'spectral features with age regressed out inside each training fold');
says(NEU.TOKENIZER.label, 'Frozen EEG tokenizer'); says(NEU.GPT_HIDDEN.label, 'Frozen GPT hidden states');
says(NEU.TOKENIZER_AGE_RESIDUAL.inputs, 'tokenizer values with age regressed out inside each training fold');
says(NEU.GPT_HIDDEN_AGE_RESIDUAL.inputs, 'GPT hidden-state values with age regressed out inside each training fold');
// Every arm but the prior is learned with the one probe: five learned arms refit in each fold, the prior checked in each.
need(CA.learned_refits === (X.controls.arms.length - 1) * C.folds && CA.prior_checks === C.folds, 'every arm but the prior is learned, with the one probe');
// The card names the board's protocol and no institution (consent statements, A3: a recorded gap).
need(!/University|Hospital|Institut|Cent(?:er|re)|College|Clinic/.test(DS.ethics_as_stated.quote), 'the card names no institution for the board');
need(CPU.AGE.role === 'confound_control' && CPU.ACQUISITION_METADATA.role === 'diagnostic_control' && CPU.AGE_RESIDUAL_EEG.role === 'sensitivity_analysis'
  && NEU.TOKENIZER_AGE_RESIDUAL.role === 'sensitivity_analysis' && NEU.GPT_HIDDEN_AGE_RESIDUAL.role === 'sensitivity_analysis', 'the arms\' roles');
// The two metrics do not put the arms in the same order: the reason both columns are shown.
{
  const all = [...X.controls.arms, ...X.neurolm.arms].filter((a: any) => a.eeg_input);
  const order = (k: string) => [...all].sort((a: any, b: any) => b.pooled[k] - a.pooled[k]).map((a: any) => a.id).join();
  need(order('balanced_accuracy') !== order('auroc'), 'the two metrics order the EEG arms differently');
}

// --- Copy. ----------------------------------------------------------------------------------------------------------
/** The dek's added clause (the Parkinson's dek keeps its words before it). */
export const IES_DEK = {
  en: 'and an infant case-control pilot with age and recording-setting controls',
  zh: '另有一项婴儿病例对照试点，附年龄与采集设置对照',
} as const;

export function iesseegCopy(locale: Locale) {
  const zh = locale === 'zh';
  const cpu = X.controls.arms.map((a: any) => row(a, locale));
  const neural = X.neurolm.arms.map((a: any) => row(a, locale));
  const v = (a: any) => formatFig(ba(a.pooled.balanced_accuracy));
  const rd = (text: string, figs: Fig[]) => mark(text, figs, 'reading');
  const cpuFigs = X.controls.arms.map((a: any) => ba(a.pooled.balanced_accuracy));
  const neuFigs = X.neurolm.arms.map((a: any) => ba(a.pooled.balanced_accuracy));
  const bandN = (people: number) => zh ? `${people} 人` : `${people} people`;
  return {
    eyebrow: zh ? '婴儿病例对照试点 · 清醒期 EEG' : 'Infant case-control pilot · awake EEG',
    h2: tr(X.question, locale),
    lede: mark(zh
      ? `IESSEEG 是一个公开的 EEG 数据集，来自同一机构的回顾性队列：${C.people} 名被试，其中 ${C.cases} 例婴儿癫痫性痉挛综合征病例（每例都用开始治疗之前的那段记录，这项治疗正是原始研究评估的对象）、${C.controls} 名对照。每名被试取一段临床医生选定的清醒期记录（按固定规则选取，不依据信号挑选），读取其前 ${C.seconds_analysed} 秒、所有记录共有的 ${C.channels} 个通道。每个组都在发布者给出的 ${C.folds} 个被试不重叠的折上做折外评分：每折 ${C.train_people} 人训练、${C.held_out_people} 人留出，每名被试恰好留出一次。`
      : `IESSEEG is a public EEG dataset from one institution’s retrospective cohort: ${C.people} people, ${C.cases} cases of infantile epileptic spasms syndrome, each on the recording made before the treatment the source study evaluated, and ${C.controls} controls. Each person contributes one clinician-selected awake segment, chosen by a fixed rule with no signal-driven choice, read for its first ${C.seconds_analysed} s on the ${C.channels} channels every recording shares. Every arm is scored out of fold on the publisher’s ${C.folds} participant-disjoint folds: ${C.train_people} people train, ${C.held_out_people} are held out, and each person is held out once.`,
      cohortFigs, 'lede'),
    boundary: tr(X.audit_boundary, locale),
    reading: [
      ...rd(zh
        ? `频谱 EEG 的平衡准确率为 ${v(CPU.EEG)}，加入年龄后为 ${v(CPU.EEG_PLUS_AGE)}。只用年龄为 ${v(CPU.AGE)}，只用采集设置为 ${v(CPU.ACQUISITION_METADATA)}，训练集先验为 ${v(CPU.SOURCE_PRIOR)}。在每个训练折内回归掉年龄后，频谱 EEG 为 ${v(CPU.AGE_RESIDUAL_EEG)}。`
        : `Spectral EEG reached ${v(CPU.EEG)} balanced accuracy, and ${v(CPU.EEG_PLUS_AGE)} with age added. Age alone reached ${v(CPU.AGE)}, recording settings alone ${v(CPU.ACQUISITION_METADATA)}, and the training prior ${v(CPU.SOURCE_PRIOR)}. With age regressed out inside each training fold, spectral EEG reached ${v(CPU.AGE_RESIDUAL_EEG)}.`, cpuFigs),
      zh ? '' : ' ',
      ...rd(zh
        ? `在同样的被试、折与分类头上，冻结 GPT 隐藏状态为 ${v(NEU.GPT_HIDDEN)}，冻结分词器为 ${v(NEU.TOKENIZER)}；回归掉年龄后分别为 ${v(NEU.GPT_HIDDEN_AGE_RESIDUAL)} 与 ${v(NEU.TOKENIZER_AGE_RESIDUAL)}。`
        : `On the same people, folds and probe, frozen GPT hidden states reached ${v(NEU.GPT_HIDDEN)} and the frozen tokenizer ${v(NEU.TOKENIZER)}; with age regressed out, ${v(NEU.GPT_HIDDEN_AGE_RESIDUAL)} and ${v(NEU.TOKENIZER_AGE_RESIDUAL)}.`, neuFigs),
    ],
    bothTables: zh ? '两张表：' : 'Both tables.',
    caption: mark(tr(X.caption, locale), [n(C.seconds_analysed)], 'caption'),
    metricsLine: zh
      ? '平衡准确率是主要指标；每个组都同时给出 AUROC，没有根据这些结果挑选任何组或阈值。'
      : 'Balanced accuracy is the primary metric; AUROC is shown beside it for every arm, and no arm or threshold is chosen from these results.',
    bandNote: [
      ...mark(tr(B.note, locale), bandFigs, 'age band'),
      zh ? '' : ' ',
      ...mark(zh ? `本队列中这一年龄段共 ${B.people} 人：${B.cases} 例病例、${B.controls} 名对照。` : `In this cohort the band holds ${B.people} people: ${B.cases} cases and ${B.controls} controls.`, bandFigs, 'age band'),
    ],
    // The tables.
    colArm: zh ? '组' : 'Arm',
    cols: D.columns.map((c: any) => mark(tr(c.label, locale), [n(C.people), n(B.maximum_age_years)], 'column')),
    bandSize: mark(bandN(B.people), bandFigs, 'column'),
    groupNoEeg: zh ? '不用 EEG' : 'Without EEG',
    groupEeg: zh ? '使用 EEG' : 'With EEG',
    cpu, neural,
    controlsH3: tr(X.controls.title, locale),
    controlsP: mark(zh
      ? `频谱组在每段记录的原始采样率下计算 Welch 频谱（${CM.welch_window_seconds} 秒窗，相邻窗重叠一半，频率分辨率 ${CM.frequency_resolution_hz} Hz）：在 ${CM.bands_hz[0][0]}–${CM.bands_hz[4][1]} Hz 内五个频带上的对数相对功率，加上同一范围内的对数总功率，${C.channels} 个通道每个都算，每人共 ${CM.feature_count} 个特征。每个需要学习的组都用同一个事先固定、不做调参的分类头：只用训练折拟合标准化，再做 L2 逻辑回归（C = ${CM.logistic_c}）。年龄项是记录时年龄的 log1p 及其平方；回归掉年龄的那一组在训练折内把每个特征对这两项做回归，再把训练折的系数用于训练与留出的被试。采集设置组读取原始头皮通道数（${chans(19).channels} 个通道的有 ${chans(19).recordings} 段记录，${chans(17).channels} 个通道的有 ${chans(17).recordings} 段）与原始采样率（${rate(200).hz} Hz 的有 ${rate(200).recordings} 段，${rate(2000).hz.toLocaleString('en-US')} Hz 的有 ${rate(2000).recordings} 段）。`
      : `The spectral arms read Welch spectra at each recording’s native rate (${CM.welch_window_seconds} s windows overlapping by half, ${CM.frequency_resolution_hz} Hz resolution): log relative power in five bands from ${CM.bands_hz[0][0]} to ${CM.bands_hz[4][1]} Hz and log total power over the same range, for each of the ${C.channels} channels, ${CM.feature_count} features per person. Every learned arm uses the same probe, fixed in advance with no tuning: standardisation fitted on the training fold, then L2 logistic regression (C = ${CM.logistic_c}). The age terms are log1p of age at the recording and its square; the residualized arm regresses each feature on them inside the training fold and applies those coefficients to the training and held-out people. The recording-settings arm reads the original scalp channel count, ${chans(19).channels} in ${chans(19).recordings} recordings and ${chans(17).channels} in ${chans(17).recordings}, and the native sampling rate, ${rate(200).hz} Hz in ${rate(200).recordings} and ${rate(2000).hz.toLocaleString('en-US')} Hz in ${rate(2000).recordings}.`,
      [n(CM.welch_window_seconds), n(CM.frequency_resolution_hz), n(CM.bands_hz[0][0]), n(CM.bands_hz[4][1]), n(C.channels), n(CM.feature_count), n(CM.logistic_c),
       n(chans(19).channels), n(chans(19).recordings), n(chans(17).channels), n(chans(17).recordings), n(rate(200).hz), n(rate(200).recordings), n(rate(2000).hz), n(rate(2000).recordings)],
      'controls method'),
    controlsCaption: zh ? '六个使用或不使用 EEG 的组，均为折外评分' : 'Six arms with and without EEG, each scored out of fold',
    controlsRegion: zh ? 'IESSEEG 年龄与采集设置对照，可横向滚动' : 'IESSEEG age and acquisition controls, scrolls horizontally',
    neurolmH3: tr(X.neurolm.title, locale),
    neurolmP: mark(zh
      ? `NeuroLM-B 以冻结方式用作特征提取器：权重保持不变，也不涉及任何文本。每段记录的 ${C.seconds_analysed} 秒切成 ${NM.windows} 个 ${NM.window_seconds} 秒窗，每个通道每秒一个 token，每窗 ${NM.tokens_per_window} 个 token。读取模型的两种内部状态：分词器经最后一次归一化后的状态，以及 GPT 分支经最后一层层归一化后的隐藏状态，各 ${NM.dimensions} 维；先在每个窗内对 token 取平均，再对各窗取平均。分类头与训练折内回归掉年龄的做法都与频谱组相同，没有改动。`
      : `NeuroLM-B is read frozen, as a feature extractor: its weights are unchanged, and no text is involved. Each recording’s ${C.seconds_analysed} s are cut into ${NM.windows} windows of ${NM.window_seconds} s, with one token per channel and second, ${NM.tokens_per_window} tokens per window. Two of the model’s internal states are read: the tokenizer’s, after its final normalisation, and the GPT branch’s hidden states, after the final layer normalisation, ${NM.dimensions} values each, averaged over each window’s tokens and then over the windows. The probe and the training-fold age regression are those of the spectral arms, unchanged.`,
      [n(C.seconds_analysed), n(NM.windows), n(NM.window_seconds), n(NM.tokens_per_window), n(NM.dimensions)], 'NeuroLM method'),
    neurolmCode: zh ? 'NeuroLM 源代码，固定版本' : 'NeuroLM source code at revision',
    checkpoint: zh ? '检查点 SHA-256' : 'checkpoint SHA-256',
    model: { sourceUrl: M.source_url as string, revision: (M.source_revision as string).slice(0, 8), sha: M.checkpoint_sha256 as string },
    neurolmCaption: zh ? '用同一个分类头读冻结 NeuroLM-B 状态的四个组，被试与折相同' : 'Four arms reading frozen NeuroLM-B states with the same probe, on the same people and folds',
    neurolmRegion: zh ? 'IESSEEG 上的冻结 NeuroLM 分类头，可横向滚动' : 'Frozen NeuroLM probes on IESSEEG, scrolls horizontally',
    footnoteLabel: zh ? 'NeuroLM：' : 'NeuroLM.',
    footnote: mark(tr(X.neurolm.footnote, locale), preFigs, 'footnote'),
    // Limits, each beside this pilot's evidence.
    limitsH3: zh ? '本试点的局限' : 'Limits of this pilot',
    limits: ((): [string, string][] => {
      const heads = zh ? ['单一的小型开发队列', '回归掉年龄', '采集设置', '冻结的 NeuroLM'] : ['One small development cohort', 'Regressing out age', 'Recording settings', 'NeuroLM, frozen'];
      need(X.limitations.length === 4 && /^A small awake-only/.test(X.limitations[0]) && /^Regressing out age/.test(X.limitations[1])
        && /^Recording settings/.test(X.limitations[2]) && /^NeuroLM is used as a frozen/.test(X.limitations[3]), 'four limitations, in this order');
      return X.limitations.map((l: string, i: number) => [heads[i], tr(l, locale)]);
    })(),
    // The audit and the input check.
    auditH3: zh ? '经过独立复现' : 'Independently reproduced',
    auditCpu: [
      ...mark(zh ? `频谱与对照组：${CA.models} 个模型（${CA.learned_refits} 次重新拟合、${CA.prior_checks} 次先验核对），${CA.reconstructed_predictions} 个留出概率。` : `Spectral and control arms: ${CA.models} models (${CA.learned_refits} refits and ${CA.prior_checks} prior checks) and ${CA.reconstructed_predictions} held-out probabilities.`,
        [n(CA.models), n(CA.learned_refits), n(CA.prior_checks), n(CA.reconstructed_predictions)], 'CPU audit'),
      zh ? '' : ' ', tr(CA.what, locale),
    ],
    auditNeu: [
      ...mark(zh ? `NeuroLM 各组：${NA.independent_refits} 次分类头重新拟合，${NA.held_out_predictions_reconstructed} 个留出概率，${NA.source_hash_checks} 个输入文件与 ${NA.feature_receipts_checked} 个特征文件。` : `NeuroLM arms: ${NA.independent_refits} probe refits, ${NA.held_out_predictions_reconstructed} held-out probabilities, ${NA.source_hash_checks} input files and ${NA.feature_receipts_checked} feature files.`,
        [n(NA.independent_refits), n(NA.held_out_predictions_reconstructed), n(NA.source_hash_checks), n(NA.feature_receipts_checked)], 'NeuroLM audit'),
      zh ? '' : ' ', tr(NA.what, locale),
    ],
    inputCheck: [
      ...mark(zh
        ? `另有一项独立的只读审计核对了每个输入文件的哈希、时序与定标：${Q.assets} 个文件，共 ${Q.bytes.toLocaleString('en-US')} 字节；${Q.recordings} 段记录全部通过，没有暂缓，也没有缺口。`
        : `An independent read-only audit checked every input file’s hash, timing and calibration: ${Q.assets} files, ${Q.bytes.toLocaleString('en-US')} bytes; all ${Q.recordings} recordings passed, with none held and none with gaps.`,
        [n(Q.assets), n(Q.bytes), n(Q.recordings)], 'input check'),
      zh ? '' : ' ', tr(Q.note, locale),
    ],
    // Credits and consent, from the release card at the pinned revision.
    rightsName: RT.name as string,
    attribution: RT.attribution as string,
    consent: tr(RT.privacyReview, locale),
    protocolLine: zh
      ? `卡片给出的批准方案编号为 ${protocolNo}，没有写明是哪个机构的审查委员会。`
      : `The card gives the approval as protocol ${protocolNo} and does not name the institution whose board approved it.`,
    crosswalk: tr(DS.prior_reuse.crosswalk, locale),
    links: {
      dataset: { href: DS.url as string, text: zh ? '固定版本的数据集 ↗' : 'Dataset at the pinned revision ↗' },
      card: { href: DS.release_card_url as string, text: zh ? '发布卡片 ↗' : 'Release card ↗' },
      licenceFile: { href: DS.licence_file_url as string, text: 'LICENSE ↗' },
      licence: { href: RT.licenseUrl as string, text: (RT.license as string).replace(/-/g, ' ') },
      dataUse: { href: '/data-use/#sources-clinical-iesseeg', text: zh ? '数据使用说明（英文）' : 'Data use' },
    },
    schema: X.schema_version as string,
  };
}

/**
 * The page's own guard for what stays unchanged (D13): the Parkinson's short answer, description and card cite only
 * clinical-update.json. Every number they print must be one of `allowed` (the page's formatted clinical-update.json
 * figures), and none of them may name this section's cohort or model.
 */
export function guardParkinsonsOnly(texts: string[], allowed: string[]) {
  const ok = new Set(allowed);
  for (const t of texts) {
    need(!/IESSEEG|NeuroLM|infant|spasm|婴儿|痉挛/i.test(t), `the Parkinson's summary names nothing of the IESSEEG section: "${t.slice(0, 60)}…"`);
    for (const m of t.replace(/\[\[|\]\]/g, '').matchAll(/\d(?:\d|,(?=\d{3}))*(?:\.\d+)?%?(?:–\d(?:\d|,(?=\d{3}))*(?:\.\d+)?%)?/g))
      need(ok.has(m[0]), `the Parkinson's summary cites only clinical-update.json: "${m[0]}"`);
  }
}
