/**
 * What each served download holds, for the Data API page and llms.txt. The file
 * list itself comes from releases.ts (every release names its files) and is
 * checked against dist/data by check-workbench.mjs, so a file can't be served
 * without a description here, or described without being served.
 */
import data from './mvp.json';
import { releases } from './releases';
import type { Locale } from './i18n';

type Text = Record<Locale, string>;
const track = (id: string) => data.tracks.find(t => t.id === id)!;
const zhTrack: Record<string, string> = {
  'mi-rest': '运动想象与静息', idle: '空闲与指令', 'beta-8ch': 'SSVEP · 8 通道', 'beta-4ch': 'SSVEP · 4 通道',
  'arithmetic-rest': '心算与静息', 'p300-target': 'P300 目标 ERP', 'semantic-target': '语义目标 ERP', 'sleep-scalp': '睡眠分期',
};

const named: Record<string, Text> = {
  'experiments.json': {
    en: 'The core matrix: every protocol with each method’s score, interval, cohort, electrode count, training mode and limitations, plus the model and dataset directories.',
    zh: '核心矩阵：每个协议下各方法的分数、区间、队列、电极数、训练方式与局限，以及模型目录和数据集目录。',
  },
  'deployment-topics.json': {
    en: 'Deployment topics: dry vs. wet sensor transfer, calibration budget, movement (SSVEP and ERP) and pretraining controls — measurements, paired contrasts, seed sensitivity and dataset citations.',
    zh: '部署专题：干湿电极迁移、校准预算、运动中的 SSVEP 与 ERP、预训练对照——测量值、配对差值、随机种子敏感性与数据集引用。',
  },
  'evidence-update.json': {
    en: 'In-ear vs. scalp sleep staging (EESM23), four vs. sixteen electrodes (Alpha Waves), and the physical head phantom, each with its rights record.',
    zh: '耳道内与头皮睡眠分期（EESM23）、4 个与 16 个电极（Alpha Waves），以及物理头模，各附权利记录。',
  },
  'clinical-update.json': {
    en: "Parkinson's disease vs. controls from resting-state EEG (ds004584) beside an age-and-sex-only comparator, the claim boundary, and status-only sources.",
    zh: '静息态 EEG 上的帕金森病与对照（ds004584），旁边并排放着只用年龄和性别的对照基线，附声明边界与仅列状态的来源。',
  },
  'adaptation-update.json': {
    en: 'LaBraM on EEGMAT, new people, same task, zero labels from the test person, adapted three ways (head only, last block, rank-4 LoRA) over three seeds: scores, paired changes with people helped or harmed, trainable parameters and training time; the next-day experiment as status only.',
    zh: 'EEGMAT 上的 LaBraM，新被试、同一任务、不使用测试被试的任何标签，三种适配方式（只训分类头、最后一个 Transformer 块、秩为 4 的 LoRA），3 个随机种子：分数、配对变化与提升/变差人数、可训练参数与训练时间；次日实验只列状态。',
  },
  'extension-update.json': {
    en: 'Twenty further people of the asynchronous SSVEP release under a pilot-fixed and a personal rejection threshold (detection, coverage, correct-and-accepted, false acceptance per state, people helped and harmed), and LTRSVP image-rate and recording transfer (two primary arms, paired difference, 3×3 matrix), with rights records.',
    zh: '异步 SSVEP 数据集中另外 20 名被试在试点固定阈值与逐人阈值下的结果（检测、覆盖率、被接受且正确、各状态误接受、提升与变差人数），以及 LTRSVP 的图像速率与记录迁移（两个主分析组、配对差值、3×3 矩阵），附权利记录。',
  },
  'reliable-decisions-update.json': {
    en: 'Route 1, reliable decisions, on EEGMAT and BETA: each method’s coverage and error under a fixed confidence threshold (with how many people had nothing accepted), a coverage target and a certified selective risk (with folds certified and folds over target); the learned reject option against calibrated confidence (AURC, error at 80% coverage); errors at a matched coverage; NLL, ECE and Brier score; and person-specific recalibration with its label cost — with paired person-bootstrap intervals and verdicts. A crude ds003810 panel, secondary seeds, sensitivity arms and the audit record.',
    zh: '第一条路线“可靠的决策”，EEGMAT 与 BETA：每种方法在固定置信度阈值下的覆盖率与错误率（附什么都没被接受的被试人数）、在覆盖率目标与经认证的选择性风险下的覆盖率与错误率（附认证的折数与超过目标的折数）；可学习的拒识选项与校准后置信度的比较（AURC、80% 覆盖率下的错误率）；相同覆盖率下的错误率；NLL、ECE 与 Brier 分数；以及按人重新校准及其标签代价——均附配对的被试 bootstrap 区间与判定。另有标为粗略的 ds003810 面板、其余随机种子、敏感性分析与审计记录。',
  },
  'later-sessions-update.json': {
    en: 'Does a decoder trained on an earlier session still work later? WBCIC-SHU session 1 to session 3 in two separate cohorts (a source-majority prior and a relative spectral ridge, and frozen CBraMod with a session-1 ridge readout: balanced accuracy with its participant-bootstrap interval, accuracy, macro F1 and the paired differences); the longitudinal RSVP source’s first-visit ERP baseline at the nominal Day 7, 80 and 200 visits (AUROC with its interval, average precision, log loss, Brier score and ECE, event counts, the paired Day 200 minus Day 7 contrast and how many people declined); and Forenzo’s continuous cursor tracking, a negative result (per cohort and response arm, the ridge’s mean and median error against the source-mean comparator, paired differences, how many records the ridge did worse on, secondary metrics with nulls kept null, coverage and holds); with each source’s rights, consent and ethics record and its limitations.',
    zh: '在较早会话上训练的解码器，到后来还管用吗？WBCIC-SHU 两个独立队列从第 1 次会话到第 3 次会话的结果（源会话多数类先验与相对频谱功率 + 岭回归，以及分类头用第 1 次会话拟合的冻结 CBraMod：平衡准确率及其被试 bootstrap 区间、准确率、宏平均 F1 与配对差值）；纵向 RSVP 数据集在第一次访次训练的 ERP 基线，在标称第 7、80、200 天访次上的结果（AUROC 及其区间、平均精确率、对数损失、Brier 分数与 ECE、事件计数、第 200 天减第 7 天的配对对比，以及下降的被试人数）；以及 Forenzo 连续光标追踪这一阴性结果（每个队列、每种响应变量下 spectral ridge 误差的均值与中位数，与源会话均值对照比较，配对差值，ridge 表现更差的记录数，空值保持为空的次要指标，覆盖情况与暂缓的记录）；附每个数据源的权利、知情同意与伦理记录及其局限。',
  },
  'questions-in-language-update.json': {
    en: 'Route 3, questions in language, on BETA SSVEP and BOAS sleep: one question-conditioned head asked each question by a question number, a label template or a description — the 35 pre-declared entries with n, seeds, interval, both flags, the route-sentence rule and the route sentence, kept apart as seen questions, rewordings and questions the EEG head was never trained on; per-arm levels with chance-corrected values, generalisation costs, read-offs and flip rates; the pre-run checks as pass or fail and counts, with the two failed canary revisions and the owner’s override disclosed; the secondary results (EESM19, OpenBMI, REVE-L, a second text encoder, Chinese wordings, negation, extrapolation, Wearable-102), labelled single-seed and likely inconclusive where declared; BOAS’s three stated gaps and attribution, rights records, references and the audit record.',
    zh: '第三条路线“用语言提问”，BETA 上的 SSVEP 与 BOAS 上的睡眠：一个以问题为条件的分类头，每个问题分别用题号、标签模板或描述提出——35 个预先声明的条目，附被试人数、随机种子数、区间、两个标记、路线结论规则与路线结论，并按已见过的问题、改写后的问题、EEG 分类头从未训练过的问题分开列出；各组的水平及其校正随机水平后的数值、泛化代价、读出结果与答案翻转率；运行前检查只以通过或失败及计数给出，并披露金丝雀检查的两次失败修订与所有者的推翻决定；次要结果（EESM19、OpenBMI、REVE-L、另一个文本编码器、中文问法、否定、外推、Wearable-102），按声明标注单种子与多半无法下结论；BOAS 的三个已说明缺口与署名、权利记录、参考文献与审计记录。',
  },
  'questions-in-language-wordings.json': {
    en: 'The wordings route 3 asked its questions with, published with its results: 787 texts in English and Chinese for sleep, SSVEP and motor imagery (training and held-out sentence frames, label names and synonyms, training and held-out descriptions, descriptions and names of the unseen questions, negation frames), written before any score by two agents from a fixed brief; the leakage rules they passed; the held-out frequency partition of the five rotations and the extrapolation band; the declared derangements of the shuffled control; the numeric frequency code; and the pinned text encoders. Text only, CC BY 4.0.',
    zh: '第三条路线提问所用的全部问法，随结果一并发布：睡眠、SSVEP 与运动想象的 787 条英文与中文文本（训练与留出的句式、标签名称与同义词、训练与留出的描述、未见过问题的描述与名称、否定句式），由两个代理在任何评分之前按固定说明写成；它们通过的防泄漏规则；五种轮换中留出频率的划分与外推频段；打乱对照预先声明的错位排列；频率的数值编码；以及固定版本的文本编码器。仅文本，CC BY 4.0。',
  },
  'shared-representation-update.json': {
    en: 'Route 2, one representation and several questions, on OpenBMI motor imagery and BOAS sleep: independent models, fixed linear heads on a shared encoder, a shared hidden layer and the question-conditioned head, at matched data and compute, with EEGNet from scratch, frozen CBraMod features and CBraMod adapted by LoRA — every paired contrast with its interval, its difference and margin flags and its gate; per-arm balanced accuracy, AUROC and log loss; the route sentence per domain and the cost ledger; the derivable-question test (log R); a crude EESM19 replication; BOAS’s three stated gaps and attribution, rights records and the audit record.',
    zh: '第二条路线“一份表征，多个问题”，OpenBMI 运动想象与 BOAS 睡眠：在数据量与计算量匹配的条件下，比较每个问题一个独立模型、共享编码器上的固定线性头、共享隐藏层与以问题为条件的头，编码器分别是从头训练的 EEGNet、冻结的 CBraMod 特征和用 LoRA 适配的 CBraMod——每个配对对比都附区间、差异与界值两个标记以及门槛判定；各组的平衡准确率、AUROC 与对数损失；每个领域的路线结论与成本账；可推导问题的检验（log R）；标为粗略的 EESM19 重复；BOAS 的三个已说明缺口与署名、权利记录与审计记录。',
  },
  'foundation-models-update.json': {
    en: 'Further foundation encoders beside the core matrix: sixteen encoder checkpoints of eleven further models as frozen probes on the eight core protocols (balanced accuracy with its participant-bootstrap interval, macro F1, chance flag and pretraining exposure per cell; idle false activations and detections as counts; two cells not run, with the reason), the masking ablation, nine models adapted on EEGMAT (head on a frozen encoder against rank-4 LoRA: three-seed means, per-seed means, paired changes with people helped and harmed, trainable parameters), comparisons decided by interval overlap, the pretraining-exposure table with sources, weights licences, row footnotes and the audit record.',
    zh: '核心矩阵之外的更多基础模型编码器：另外 11 个模型的 16 个编码器检查点，作为冻结探针在 8 个核心协议上的结果（每个单元格的平衡准确率及其被试 bootstrap 区间、宏平均 F1、随机水平标记，以及该数据集是否在预训练数据清单中；空闲协议的误触发与检出以计数给出；两个未运行的单元格注明原因），掩码消融，9 个模型在 EEGMAT 上的适配（冻结编码器只训分类头对比秩为 4 的 LoRA：三个随机种子的均值、各种子均值、配对变化与提升/变差人数、可训练参数），按区间是否重叠判定的比较，附来源的预训练数据核查表，权重许可、行脚注与审计记录。',
  },
  'large-source-update.json': {
    en: 'Dreem sleep staging in two separate cohorts, DOD-H (healthy) and DOD-O (obstructive sleep apnoea): a training prior and a spectral ridge with accuracy, balanced accuracy, macro F1 and Cohen’s kappa, the paired balanced-accuracy gain and the ridge’s per-stage recall, precision and F1 (nulls kept null); and OpenBMI cross-session motor-imagery calibration, 51 people at 0, 10, 20 and 40 labelled session-2 trials, with paired changes and how many people declined. Rights records and one figure-free hold.',
    zh: '两个独立队列上的 Dreem 睡眠分期——DOD-H（健康被试）与 DOD-O（阻塞性睡眠呼吸暂停）：训练集先验与 spectral ridge 的准确率、平衡准确率、宏平均 F1 与 Cohen kappa 系数，配对的平衡准确率提升，以及 spectral ridge 的逐期召回率、精确率与 F1（空值保持为空）；以及 OpenBMI 跨会话运动想象校准，51 名被试，第二次会话 0、10、20、40 个校准试次，附配对变化与下降人数。附权利记录与一项不含数字的暂缓。',
  },
  'context-update.json': {
    en: 'Screen-to-VR P300 transfer, treadmill walking speed beside a movement-nuisance comparator, and the asynchronous SSVEP non-control pilot, with audits.',
    zh: '从屏幕到 VR 的 P300 迁移、跑步机步速（旁边并排放着运动干扰对照），以及异步 SSVEP 非控制试点，附审计。',
  },
};

export function describeFile(file: string): Text {
  if (named[file]) return named[file];
  // The v9 batch's per-protocol CSVs (releases.ts foundationModelFiles).
  const fm = file.match(/^foundation-models-(.+)\.csv$/);
  if (fm) {
    const t = track(fm[1]);
    if (!t) throw new Error(`files.ts: no protocol for ${file}`);
    return {
      en: `${t.title}: the further foundation-encoder rows — one per encoder checkpoint, in the core results CSV’s columns and units, then status, panel, chance flag, pretraining exposure, licence and footnote. Not run is empty with its reason.`,
      zh: `${zhTrack[fm[1]]}：更多基础模型编码器的各行——每个编码器检查点一行，列与单位同核心结果 CSV，其后为状态、所属面板、随机水平标记、是否在预训练数据清单中、许可与脚注。未运行的单元格留空并注明原因。`,
    };
  }
  const m = file.match(/^(.+)-(results\.csv|protocol\.json)$/);
  if (!m) throw new Error(`files.ts: no description for ${file}`);
  const t = track(m[1]);
  return m[2] === 'results.csv'
    ? { en: `${t.title}: one row per method — score, interval, secondary metric, cohort and compute time.`, zh: `${zhTrack[m[1]]}：每种方法一行——分数、区间、次指标、队列与计算耗时。` }
    : { en: `${t.title}: the protocol — cohort, channels, windows, split, training budget, rights and limitations.`, zh: `${zhTrack[m[1]]}：协议——队列、通道、时间窗、数据划分、训练预算、权利与局限。` };
}

/** Every served download, newest release first, with the release that ships it. */
export const servedFiles = releases.flatMap(r => r.files.map(file => ({ file, release: r.id, date: r.date })));
