/**
 * What each served download holds, for the Data API page and llms.txt. The file
 * list itself comes from releases.ts (every release names its files) and is
 * checked against dist/data by check-workbench.mjs, so a file can't be served
 * without a description here, or described without being served.
 */
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import data from './mvp.json';
import ssvepCards from './ssvep-followups-update.json';
import { openRegister, releases } from './releases';
import { bingoReleased, handwritingReleased } from './pilot-switch';
import type { Locale } from './i18n';

type Text = Record<Locale, string>;
const track = (id: string) => data.tracks.find(t => t.id === id)!;
const zhTrack: Record<string, string> = {
  'mi-rest': '运动想象与静息', idle: '空闲与指令', 'beta-8ch': 'SSVEP · 8 通道', 'beta-4ch': 'SSVEP · 4 通道',
  'arithmetic-rest': '心算与静息', 'p300-target': 'P300 目标 ERP', 'semantic-target': '语义目标 ERP', 'sleep-scalp': '睡眠分期',
};

// The SSVEP follow-ups' card numbers, as the file places them (2026-10-28).
const ssvepCardNos = ssvepCards.placement.cards.map(c => c.card);
const [ssvepFirst, ssvepLast] = [Math.min(...ssvepCardNos), Math.max(...ssvepCardNos)];

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
  'pilot-studies-update.json': {
    en: `Small pilots outside every leaderboard and model ranking. The Orthosis error-detection dataset as one cohort in three results: a 64-channel classical EEG baseline (balanced accuracy, AUROC and average precision with person-bootstrap intervals, a direction/time confound probe, the training majority and class prior, the matched EEG-minus-confound difference with how many people were above, permutation-control means with observed ranges, and the response-clean subset as counts), the same baseline on 58 channels, and frozen EEGPT against those matched classical features (the paired difference with its interval, the checkpoint’s identity and licence status; no weights). ${bingoReleased ? 'BINGO Greek and English inner speech within and across languages (balanced and top-3 accuracy against their priors, order-only, high-frequency and label-shuffle controls, the cross-minus-within contrast, the protocol and the project’s documented preprocessing). ' : ''}${handwritingReleased ? 'A mask-aware EEG analysis of a handwriting competition dataset, five people (balanced accuracy of relative EEG and three controls that see no EEG, with person-bootstrap intervals except the mask-only control’s, three paired contrasts, label-shuffle means with observed ranges, channel availability over trials and its flag counts, and the earlier analysis of the same people as context). ' : ''}REFED’s stored-clip diagnostic (equal-axis mean absolute error for EEG and three source-only controls in two conditions). Status-only entries, ${[bingoReleased, handwritingReleased].every(Boolean) ? '' : [bingoReleased, handwritingReleased].some(Boolean) ? `one hold (the ${bingoReleased ? 'handwriting analysis' : 'BINGO inner-speech pilot'}, with no figure), ` : 'two holds (the BINGO inner-speech pilot and the handwriting analysis, with no figure), '}and each source’s rights, consent and ethics record, with the handwriting dataset’s stated gap.`,
    zh: `不进入任何排行榜或模型排名的小规模试点。Orthosis 错误检测数据集作为同一个队列给出三项结果：64 通道经典 EEG 基线（平衡准确率、AUROC 与平均精确率及其被试 bootstrap 区间，方向/时间混杂探针，训练集多数类与类别先验，逐人匹配的 EEG 减混杂探针的差值及高于探针的人数，标签置换对照的均值与观察到的范围，以及只给计数的“响应干净”子集）、同一基线在 58 个通道上的配置，以及冻结的 EEGPT 与这组匹配的经典特征的比较（配对差值及其区间、检查点的标识与许可状态；不含权重）。${bingoReleased ? 'BINGO 希腊语与英语内部言语在语言内与跨语言的结果（平衡准确率与 top-3 准确率及其先验，仅顺序、高频与标签打乱对照，跨语言减语言内的对比，实验协议，以及项目说明的预处理）。' : ''}${handwritingReleased ? '一个手写竞赛数据集上的掩码感知 EEG 分析，五名被试（相对频带功率 EEG 与三个不用 EEG 的对照的平衡准确率，除只看缺失掩码的对照外都附被试 bootstrap 区间；三个配对对比；打乱标签的均值与观察到的范围；按试次统计的通道可用情况及其标记计数；以及对同一批被试较早的分析，作为背景）。' : ''}REFED 的存储片段诊断（两种条件下 EEG 与三个不用 EEG、只用训练集信息的对照的等权两轴平均绝对误差）。另有只列状态的条目${[bingoReleased, handwritingReleased].every(Boolean) ? '' : [bingoReleased, handwritingReleased].some(Boolean) ? `、一项暂缓（${bingoReleased ? '手写分析' : 'BINGO 内部言语试点'}，没有数字）` : '、两项暂缓（BINGO 内部言语试点与手写分析，都没有数字）'}，以及每个数据源的权利、知情同意与伦理记录，包括手写数据集已说明的缺口。`,
  },
  'eegpt-core-update.json': {
    en: 'EEGPT beside the core matrix, from the same runs as the published LaBraM rows and, except on idle, the CBraMod rows: its eight core-matrix cells as a frozen row (balanced accuracy with its participant-bootstrap interval, macro F1, chance level and pretraining exposure per cell, each percent figure also in the core rows’ units; idle false activations, detections within 3 s and people who always abstained as counts, with the window balanced accuracy and AUROC), the footnotes beside the cells they bear on, how each cell stands against the published rows (above, below or overlapping by the 95% intervals, with the gap in percentage points), its pretraining-attribution rows and paired contrasts on mi-rest and EEGMAT in the published deployment-topics fields, the model’s terms (checkpoint licence unresolved, no weights distributed, Apache-2.0 the code’s alone), the owner’s release record and what is not published.',
    zh: '核心矩阵旁边的 EEGPT，与已发布的 LaBraM 各行、以及除空闲协议外的 CBraMod 各行出自同一批运行：它在 8 个核心协议上的单元格，作为冻结编码器的一行（每个单元格的平衡准确率及其被试 bootstrap 区间、宏平均 F1、随机水平，以及该数据集是否在预训练数据清单中；每个百分比数字另以核心矩阵各行的单位给出；空闲误触发、3 秒内检出的指令与始终拒识的被试以计数给出，另附窗口平衡准确率与 AUROC），放在所涉单元格旁边的脚注，每个单元格与已发布各行的关系（按 95% 区间判断高于、低于或重叠，差距以百分点给出），它在 mi-rest 与 EEGMAT 上的预训练归因各行与配对对比（字段同已发布的部署专题文件），模型条款（检查点许可尚未厘清、不分发任何权重、Apache-2.0 只涵盖代码），所有者的发布记录，以及不发布的内容。',
  },
  'beyond-scalp-update.json': {
    en: 'Do simple baselines work on signals other than scalp EEG? Human fNIRS on Bak et al.’s finger and foot tapping, a person left out at a time (participant-macro balanced accuracy with its descriptive interval, class recalls, and a training-prior comparator); one macaque’s motor-cortex spiking on MC_RTT (a ridge decoder of finger velocity against the training mean: R², RMSE and MAE, including the metric on which the ridge is worse, with trial, neuron and row counts); a numerical coverage check of ds007420’s fNIRS recordings (counts only, with the gates that hold its classifier); and two sources prepared but not scored, FALCON H2 and Rabut et al.’s functional ultrasound, as counts. Species and modality on every entry; each source’s rights record, with its consent and ethics statement or, for the macaque, its animal-care statement.',
    zh: '在头皮 EEG 之外的信号上，简单基线管用吗？Bak 等人手指与脚部敲击的人类 fNIRS 数据，每次留出一名被试（按被试平均的平衡准确率及其描述性区间、各类别召回率，以及训练集先验对照）；MC_RTT 上一只猕猴运动皮层的神经元放电（手指速度的岭回归解码，与训练集均值比较：R²、RMSE 与 MAE，包括岭回归更差的那个指标，附试次、神经元与数据行的计数）；对 ds007420 fNIRS 记录的数值覆盖核查（只有计数，附暂缓其分类器的各项条件）；以及两个已准备、未评分的数据源——FALCON H2 与 Rabut 等人的功能超声——只给计数。每个条目都注明物种与模态；附每个数据源的权利记录，以及知情同意与伦理声明，猕猴数据则附动物护理声明。',
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
  // The four result files of the open-register release (owner decision D1).
  'new-ssvep-frequencies-update.json': {
    en: 'What lets a decoder answer an SSVEP frequency it never trained on? Seven audited follow-ups to route 3 on its BETA cohort, and the same models run unchanged on Wearable-102: the endpoints with their chance levels; a name key from the site’s names to the export codes; for each study its levels and paired contrasts with their intervals and interval method, roles and flags, its checks as pass or fail with counts, and what was not run; the stimulus phases taken from the BETA authors’ corrigendum; a status card for the cross-spectral round, with no figures; rights records and the audit record.',
    zh: '解码器靠什么回答没训练过的 SSVEP 频率？第三条路线在其 BETA 队列上的七项经审计的后续检验，以及同一批模型原样用于 Wearable-102 的结果：各端点及其随机水平；从本站名称到导出代码的对照表；每项检验的水平与配对对比及其区间与区间方法、角色与标记，以通过或失败及计数给出的检查，以及没有运行的部分；取自 BETA 作者更正说明的刺激相位；互谱一轮的状态卡（没有数字）；权利记录与审计记录。',
  },
  'data-quality-update.json': {
    en: 'Three public EEG datasets checked end to end from their files. Shin2022, the worked case: a participant-held-out diagnostic with three arms (a training prior, a normalised spectral ridge and a retrospective duration control; participant-mean balanced accuracy with its participant-bootstrap interval, and a pooled secondary value), the coverage chain from the runs in the release to the signal-valid windows, where the catalog’s trial length comes from, how the files were checked, its holds, rights and consent and ethics statements. eldBETA: counts for one participant’s recordings, with the score held. ZuCo 2.0: a timing hold on one converted run, with no figure.',
    zh: '三个公开 EEG 数据集，从文件本身从头到尾核了一遍。Shin2022 是完整的案例：整名被试留出的诊断，三个组（训练集先验、归一化的 spectral ridge 与一个回溯的时长对照；按被试平均的平衡准确率及其被试 bootstrap 区间，以及合并计算的次要数值），从发布中的 run 到信号有效时间窗的覆盖链，目录中试次时长的来历，文件是怎么核的，以及它的暂缓项、权利、知情同意与伦理声明。eldBETA：一名被试记录的计数，分数暂缓。ZuCo 2.0：一个转换后记录的时间问题，暂缓，没有数字。',
  },
  'clinical-iesseeg-update.json': {
    en: 'IESSEEG, an infant case-control pilot with age and recording-setting controls: six arms with and without EEG (a training prior, age only, recording settings only, EEG spectral features, EEG with age, and EEG after training-fold age residualization) and four arms that read frozen NeuroLM features with the same probes. Out-of-fold point estimates of balanced accuracy, AUROC and secondary metrics with confusion counts, for everyone and for the people aged 2 or under; the cohort and its input check; the release card’s attribution and ethics statement; the audit boundary, limitations and what is not published; and the clinical-groups page’s medical disclaimer.',
    zh: 'IESSEEG，一项附年龄与采集设置对照的婴儿病例对照试点：六个使用或不使用 EEG 的组（训练集先验、只用年龄、只用采集设置、EEG 频谱特征、EEG 加年龄，以及在训练折内回归掉年龄后的 EEG），以及用同样的分类头读冻结 NeuroLM 特征的四个组。平衡准确率、AUROC 与次要指标的折外点估计及混淆计数，分别针对全部被试与 2 岁及以下的被试；队列及其输入核查；数据集发布卡片中的署名与伦理声明；审计边界、局限与不发布的内容；以及临床分组页面的医学免责声明。',
  },
  'neurolm-eegmat-update.json': {
    en: 'NeuroLM’s frozen features on EEGMAT’s arithmetic and rest, a separate pilot panel: equal-person balanced accuracy and macro-F1 of three representations (tokenizer features, GPT hidden states and band power) under one fixed ridge head, three paired differences with their participant-bootstrap intervals, the adapter and the probe, the checkpoint’s identity and the terms of each part, pretraining exposure (unknown) with its sources, limitations, the audit record and what is not published.',
    zh: 'NeuroLM 冻结特征在 EEGMAT 心算与静息上的结果，作为单独的试点一栏：同一个固定的岭回归分类头下三种表示（分词器特征、GPT 隐藏状态与频带功率）按被试等权的平衡准确率与宏平均 F1，三个配对差值及其被试 bootstrap 区间，适配流程与分类头，检查点的标识与各部分的条款，是否出现在预训练数据中（未知）及其出处，局限、审计记录与不发布的内容。',
  },
  // The four result files of the 2026-10-28 round (owner decisions D14–D29); the round's register files are matched by shape below.
  'ssvep-followups-update.json': {
    en: `More audited follow-ups on SSVEP frequencies a decoder never trained on, cards ${ssvepFirst} to ${ssvepLast} of that question page, on route 3’s BETA cohort and, for some, on Wearable-102’s dry and wet headbands: the endpoints with their chance levels; a name key from the site’s names to the export codes, and the estimates several cards share; for each study its design, levels and paired contrasts with their intervals and interval method, roles and flags, its checks as pass or fail with counts, and what was not run; which intervals are adjusted; CPU timings of each component (warm, single-thread, never summed); rights records, the filter-bank CCA credit and the audit record.`,
    zh: `解码器没训练过的 SSVEP 频率的更多经审计后续检验，即那个问题页的第 ${ssvepFirst} 至 ${ssvepLast} 张卡片，用第三条路线的 BETA 队列，其中部分也用 Wearable-102 的干、湿两种头带：各端点及其随机水平；从本站名称到导出代码的对照表，以及几张卡片共用的估计值；每项检验的设计、水平与配对对比及其区间与区间方法、角色与标记，以通过或失败及计数给出的检查，以及没有运行的部分；哪些区间做了校正；各组件的 CPU 计时（预热后单线程测得，从不相加）；权利记录、滤波器组 CCA 的出处与审计记录。`,
  },
  'neurorvq-update.json': {
    en: 'NeuroRVQ’s frozen backbone on three existing tasks (EEGMAT’s arithmetic and rest, motor imagery against rest, P300 target against non-target), a separate pilot panel: for each task the cohort, split and input chain, the participant-mean balanced accuracy and macro-F1 of the backbone and of simple features of the same windows under one fixed ridge head, and one paired difference with its participant-bootstrap interval; the checkpoint’s identity and how it was restored, pretraining exposure (unknown) with its sources, the protocols not run and why, the terms of the code, the weights and each dataset, limitations, the audit record and what is not published.',
    zh: 'NeuroRVQ 冻结主干在三项现有任务上的结果（EEGMAT 的心算与静息、运动想象对静息、P300 目标对非目标），作为单独的试点一栏：每项任务的队列、数据划分与输入流程，同一个固定的岭回归分类头下主干与同一批时间窗简单特征按被试平均的平衡准确率与宏平均 F1，以及一个配对差值及其被试 bootstrap 区间；检查点的标识与加载方式，是否出现在预训练数据中（未知）及其出处，没有运行的协议及其原因，代码、权重与各数据集的条款，局限、审计记录与不发布的内容。',
  },
  'eegmat-ten-second-update.json': {
    en: 'Two frozen encoders, EEG-Captioner’s and AXON, on ten-second windows of EEGMAT’s arithmetic and rest, a separate pilot panel with a subsection for each: the cohort and its preprocessing, the source annotation-QC totals printed beside every score, each encoder’s participant-mean balanced accuracy against Welch band power on the same windows with a paired participant-bootstrap interval, each encoder’s identity and terms, AXON’s own numerical input check, why no difference between the two encoders is computed, limitations, the audit record and what is not published.',
    zh: '两个冻结编码器（EEG-Captioner 的编码器与 AXON）在 EEGMAT 心算与静息十秒时间窗上的结果，作为单独的试点一栏，每个编码器一小节：队列及其预处理，印在每个分数旁边的来源标注质量控制总数，每个编码器按被试平均的平衡准确率与同一批时间窗上的 Welch 频带功率比较及其配对被试 bootstrap 区间，每个编码器的标识与条款，AXON 自己的数值输入检查，为什么不计算两个编码器之间的差值，局限、审计记录与不发布的内容。',
  },
  'dataset-checks-update.json': {
    en: 'Four public EEG datasets checked end to end from their files. Kim beta-range SSVEP, a worked case: training-free CCA on all its participants, the mean participant accuracy with its participant-bootstrap interval against chance, the intake and how it was checked, caveats, and a hold on amplitude-dependent models. MIND, a conditional case on record IDs: CSP + LDA beside an ordinal lookup and a majority control for two stored-code pairs, record-ID resampling ranges, the label schedules, a separate secondary panel and the coverage chain. Damm and NeBULA, one-person status cases: design, counts, file facts and the arms run, with every score held. For each source its rights record, its licence statements as each source states them, its consent and ethics statements, and the holds.',
    zh: '四个公开 EEG 数据集，从文件本身从头到尾核了一遍。Kim beta 频段 SSVEP 是完整的案例：在全部被试上运行不需要训练的 CCA，按被试平均的准确率及其被试 bootstrap 区间与随机水平的比较，数据接收及其核查方式，注意事项，以及对依赖幅值的模型的暂缓。MIND 是以记录编号为单位的有条件案例：两对存储编码上的 CSP + LDA，与按位置查表的对照和多数类对照并列，记录编号重抽样范围，标签排程，单独的次要面板与覆盖链。Damm 与 NeBULA 是单人状态案例：设计、计数、文件事实与运行过的各组，所有分数暂缓。每个数据源的权利记录、按各来源原话给出的许可声明、知情同意与伦理声明，以及暂缓项。',
  },
};

/**
 * The open register's files (releases.ts `openRegister`). Each register version is a new dated file, and earlier ones
 * stay served and listed, so the names are matched by shape: open-register-<YYYYMMDD>.json and .csv.
 */
const registerFile: Record<'json' | 'csv', Text> = {
  json: {
    en: 'The open register, canonical: every EEG dataset we know of and every EEG model and paper we track, one row each under an opaque id, with its ladder (dataset or model), the furthest step checked, each step’s evidence as pass, gap or not applicable with its source, the gaps, its status, the terms as stated and by whom, aliases (repository ids, accessions, MOABB loaders), findings as codes with their parameters, and links; the step definitions in English and Chinese, the rules, the sources with the frozen query, the counts and the uploader families.',
    zh: '开放登记册的规范文件：我们知道的每个 EEG 数据集、关注的每个 EEG 模型与论文，每项一行、各有一个不透明的编号，附其所属的核验序列（数据集或模型）、核验到的最远一步、每一步的证据（通过、缺口或不适用，及其出处）、缺口、状态、所述条款及其出处、别名（仓库编号、登录号、MOABB 加载器）、以代码加参数表示的发现，以及链接；另有中英文的步骤定义、规则、含冻结查询的来源、计数与上传者系列。',
  },
  csv: {
    en: 'The open register’s dataset ladder, flat, for spreadsheets and the Hugging Face viewer: one row per dataset entry with its id, group, name, host, licence as stated, whether access is gated, the furthest step checked, gaps, status and page. Findings are in the JSON.',
    zh: '开放登记册的数据集部分，扁平表格，供电子表格与 Hugging Face 预览使用：每个数据集条目一行，含编号、分组、名称、托管方、所述许可、访问是否受限、核验到的最远一步、缺口、状态与页面。发现写在 JSON 中。',
  },
};

export function describeFile(file: string): Text {
  if (named[file]) return named[file];
  const register = file.match(/^open-register-\d{8}\.(json|csv)$/);
  if (register) return registerFile[register[1] as 'json' | 'csv'];
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

/**
 * Whether a download is in public/data, the directory the site serves (read at build time, as releases.astro reads
 * it for the hashes). Every link to a register page is guarded on the register file being served (plan §4.7), so a
 * build without it links nowhere that does not exist.
 */
export const isServed = (file: string) => existsSync(resolve('public/data', file));
export const registerServed = isServed(openRegister.json);
/**
 * Whether each register page is built: its register file is served (both pages read it, and neither is built
 * without it) and its route exists. A page that links a register page, or lists it, is guarded on its flag.
 */
const routeExists = (path: string) =>
  [`src/pages/[...lang]${path.slice(0, -1)}.astro`, `src/pages/[...lang]${path}index.astro`].some(p => existsSync(resolve(p)));
export const registerPageBuilt = registerServed && routeExists('/datasets/register/');
export const modelRegisterPageBuilt = registerServed && routeExists('/methods/register/');
/** Whether the release archive (owner decision D17, 2026-10-28) is built: the sitemap lists it only then. */
export const releaseArchiveBuilt = routeExists('/releases/archive/');
