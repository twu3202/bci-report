/**
 * The release log: every reviewed batch, what it added, what it held back.
 *
 * What a payload already records is read from the payload on the page: release
 * IDs, dates, manifest hashes, and the SHA-256 of every download, computed from
 * the bytes being served. Only what no payload records is written here — which
 * pages a batch added, and the history of holds, including resolved ones.
 * check-workbench.mjs checks every id and date below against the payloads, and
 * every download on the page against its file in dist/data.
 */

/**
 * Pages changed in each site update, newest first, for sitemap lastmod. A page
 * carries the date of the newest update that changed it; keeping the history
 * stops a later update from rolling an earlier page's date back.
 */
export const siteUpdates = [
  {
    date: '2026-10-04',
    // Route 1 of the decision-research roadmap, reliable decisions: its results section on
    // when-not-to-act (before the roadmap, whose routes now carry their own status), the topic card
    // on the home page and the Questions hub, route-1 groups on the EEGMAT, BETA and ds003810 pages
    // (and their group counts on the dataset index) and through them the EEGNet, LaBraM, CBraMod and
    // CCA pages, the release log, data use and the API page. The v9 foundation-model files (same
    // day) reached the release log, the API page and the home page's file count and Dataset markup.
    paths: ['/', '/topics/', '/topics/when-not-to-act/', '/datasets/', '/datasets/eegmat/', '/datasets/beta/', '/datasets/ds003810/',
            '/methods/eegnet/', '/methods/labram/', '/methods/cbramod/', '/methods/cca/', '/releases/', '/data-use/', '/api/'],
  },
  {
    date: '2026-10-03',
    // The large-source batch: Dreem sleep staging got its own question,
    // sleep-staging, and dataset page; OpenBMI broadened calibration-budget to the
    // next session (new question, short answer and #next-session) and got a
    // dataset page. The home page and the Questions hub gained the sleep card and
    // the two transfer-map entries, the holds register a hold, and the dataset
    // index, data-use, API and release pages the batch. The Wearable SSVEP page
    // prints calibration-budget's question under "Where it appears", so its text
    // changed with it; model-adaptation's next-day section now points to the
    // next-session result. The topic switcher on every other topic page lists the
    // new question too; that is navigation, as the "Research preview" badge was
    // chrome, and is not counted here.
    paths: ['/', '/topics/', '/topics/sleep-staging/', '/topics/calibration-budget/', '/topics/model-adaptation/',
            '/datasets/', '/datasets/dreem-dod/', '/datasets/openbmi/', '/datasets/wearable-ssvep-102/',
            '/releases/', '/data-use/', '/api/'],
  },
  {
    date: '2026-10-02',
    // The YSU extension became the main non-control evidence on when-not-to-act
    // and reached its dataset page; LTRSVP joined screen-to-vr as a second
    // presentation change and got a dataset page; the home cards, the dataset
    // index, the API page and the release log name both. The LaBraM adaptation
    // and the next-day statuses moved from calibration-budget to their own
    // topic, model-adaptation; the EEGMAT and LaBraM pages now send readers there.
    // The home restructure (same day) moved the model directory and field notes
    // to /methods/ and the public-data register to /datasets/, and opened the
    // Questions hub at /topics/. Every other topic page and every dataset and
    // method page gained visible content the same day — a "Cite this page" block
    // and, on topics, the "Measured on" line — so they carry this date too.
    paths: ['/', '/topics/when-not-to-act/', '/topics/screen-to-vr/', '/releases/', '/data-use/', '/api/',
            '/datasets/', '/datasets/ysu-async-ssvep/', '/datasets/ltrsvp/',
            '/topics/model-adaptation/', '/topics/calibration-budget/', '/datasets/eegmat/', '/methods/labram/',
            '/topics/', '/methods/',
            '/topics/dry-vs-wet/', '/topics/fewer-electrodes/', '/topics/on-the-move/', '/topics/does-pretraining-help/',
            '/topics/clinical-groups/'],
    entityPages: true,
  },
  {
    date: '2026-10-01',
    // The adaptation results replaced the roadmap on calibration-budget and reached
    // the EEGMAT and LaBraM pages; ds003810 gained its requested citation; the API
    // page's Python example changed. Every page also lost the "Research preview"
    // badge that day, which is chrome, not content, and is not counted here.
    paths: ['/', '/topics/calibration-budget/', '/releases/', '/data-use/', '/api/',
            '/datasets/eegmat/', '/methods/labram/', '/datasets/ds003810/'],
  },
  {
    date: '2026-09-27',
    // Every topic page gained its question-form title and short answer on this
    // date; the dataset, method and API pages were first published on it.
    paths: ['/', '/topics/when-not-to-act/', '/releases/', '/topics/screen-to-vr/', '/topics/on-the-move/', '/data-use/',
            '/topics/dry-vs-wet/', '/topics/fewer-electrodes/', '/topics/calibration-budget/',
            '/topics/does-pretraining-help/', '/topics/clinical-groups/', '/api/'],
  },
] as const;

/** The current site update. */
export const pagesUpdated = siteUpdates[0];

type Text = { en: string; zh: string };

export interface Release {
  id: string;
  date: string;
  /** The payload whose release_id / releaseId this entry must match. */
  payload: 'mvp' | 'deployment' | 'evidence' | 'clinical' | 'context' | 'adaptation' | 'extension' | 'largeSource'
    | 'reliableDecisions' | 'foundationModels';
  files: string[];
  pages: string[];
  summary: Text;
  notes: Text[];
}

const protocolFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].flatMap(id => [`${id}-results.csv`, `${id}-protocol.json`]);

/** The v9 batch's per-protocol CSVs: the new rows in the core results CSVs' columns and units. */
export const foundationModelFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].map(id => `foundation-models-${id}.csv`);

export const releases: Release[] = [
  {
    id: 'foundation-models-update-20261004', date: '2026-10-04', payload: 'foundationModels',
    files: ['foundation-models-update.json', ...foundationModelFiles],
    pages: ['/topics/does-pretraining-help/', '/topics/fewer-electrodes/'],
    summary: {
      en: 'The v9 foundation-model evaluation: eleven further EEG foundation models — sixteen encoder checkpoints — run as frozen probes on the eight core protocols with the published LaBraM and CBraMod recipe and only the encoder swapped (the same windows, people, folds, heads and scoring), and nine of them adapted on EEGMAT with the 1 October recipe, a head trained on the frozen encoder against rank-4 LoRA over three seeds. New rows beside the core matrix, in their own files: one JSON, and a CSV per protocol whose first columns are the core results CSVs’. Grouped by family, never ranked: a row is above or below another only where their 95% intervals do not overlap. Every cell says whether its dataset is in the model authors’ published pretraining list, checked on 4 October 2026 with the source, and every model carries its weights licence.',
      zh: '第九轮基础模型评测：另外 11 个 EEG 基础模型（共 16 个编码器检查点）作为冻结探针，在 8 个核心协议上沿用已发布的 LaBraM 与 CBraMod 冻结方案，只替换编码器（时间窗、被试、折、分类头与评分方式都不变）；其中 9 个模型又在 EEGMAT 上按 10 月 1 日的方案做了适配：在冻结编码器上只训分类头，对比秩为 4 的 LoRA，3 个随机种子。这些是放在核心矩阵旁边的新行，有自己的文件：一个 JSON，以及每个协议一个 CSV，其前几列与核心结果 CSV 完全相同。按模型类别分组，从不排名：只有 95% 区间不重叠时，才说一行高于或低于另一行。每个单元格都注明该数据集是否在模型作者公开的预训练数据清单中（2026 年 10 月 4 日核查，附来源），每个模型都注明其权重许可。',
    },
    notes: [
      { en: 'Sleep staging is the only protocol where new frozen cells — ST-EEGFormer Large and Base, and REVE Large — lie entirely above every published row. On the other six scored protocols no new cell lies entirely above the best published non-foundation row; on BETA, standard CCA, which needs no training, stays the highest row. On EEGMAT, frozen readouts and LoRA order the models differently: one fixed recipe on one task, with LoRA budgets that differ by model, not a ranking.',
        zh: '睡眠分期是唯一一个有新的冻结单元格——ST-EEGFormer Large、ST-EEGFormer Base 与 REVE Large——完全高于所有已发布行的协议。在其余 6 个有分数的协议上，没有任何新单元格完全高于已发布的最佳非基础模型行；在 BETA 上，无需训练的标准 CCA 仍是最高的一行。在 EEGMAT 上，冻结读出与 LoRA 给出的模型顺序并不一致：这是一项任务上的一个固定方案，各模型的 LoRA 参数量也各不相同，不是排名。' },
      { en: 'ST-EEGFormer was pretrained on BETA and SingLEM on TMNRED, so those cells are flagged; ZUNA 1.1 does not list its pretraining data, so every ZUNA 1.1 cell is marked unknown. Every other cell, LaBraM’s and CBraMod’s included, is not in the authors’ published pretraining list as checked on 4 October 2026: a sourced statement, not proof that the recordings were never seen. Weights licences travel with the rows: REVE under its Responsible Use License, LUNA under CC BY-ND 4.0, ERP-FM for non-commercial use only, and ZUNA 1.1’s model card limits it to research use, not diagnosis or clinical use.',
        zh: 'ST-EEGFormer 的预训练数据包含 BETA，SingLEM 的包含 TMNRED，这些单元格都已标出；ZUNA 1.1 没有公开其预训练数据清单，所以它的每个单元格都标为未知。其余单元格——包括 LaBraM 与 CBraMod 的——都不在作者公开的预训练数据清单中（2026 年 10 月 4 日核查）：这是有出处的陈述，并不证明这些记录从未被模型见过。权重许可随行标出：REVE 采用其负责任使用许可，LUNA 为 CC BY-ND 4.0，ERP-FM 仅限非商业用途，ZUNA 1.1 的模型卡限定仅供研究使用，不可用于诊断或临床。' },
      { en: 'Not published: per-trial, per-person and per-fold values, features, and timings and memory — measured on a shared GPU, so the CSVs leave the scoring-time column empty — the declared sensitivity runs beyond the row footnotes that state them, and the aggregate, the group summaries and the six independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. Two BrainOmni cells were not run, because its tokenizer needs two-second windows: they are null with that reason, never zero. The released matrix keeps its bytes; the new rows never enter experiments.json.',
        zh: '不发布：逐试次、逐人与逐折的数值、特征，以及计算耗时与显存——它们在共享 GPU 上测得，所以 CSV 的评分耗时列留空；超出行脚注所述内容的预设敏感性分析；以及聚合文件、各组汇总与 6 份独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。BrainOmni 有两个单元格没有运行，因为它的分词器需要两秒的时间窗：这两格为空值并注明原因，而不是零。已发布的矩阵保持原有字节；新行不会进入 experiments.json。' },
    ],
  },
  {
    id: 'reliable-decisions-update-20261004', date: '2026-10-04', payload: 'reliableDecisions',
    files: ['reliable-decisions-update.json'],
    pages: ['/topics/when-not-to-act/'],
    summary: {
      en: 'Route 1 of the decision-research roadmap, reliable decisions: when a decoder should decline to decide, and what its confidence is worth. The saved test scores of models this site already publishes — spectral ridge, EEGNet and two LaBraM arms on EEGMAT (36 people); standard CCA, CBraMod and EEGNet on BETA (70 people) — rescored under a fixed confidence threshold, a coverage target, a certified selective risk and a learned reject option, with probability quality and a person-specific recalibration whose label cost is counted. No classifier was retrained, so every full-coverage accuracy equals the published one. Every protocol is balanced or uniform by design: these are method comparisons, never deployment error rates, and nothing is ranked where intervals overlap.',
      zh: '决策研究路线图的第一条路线——可靠的决策：解码器什么时候应当拒绝作出决定，它的置信度又值多少。本站已发布模型保存下来的测试分数——EEGMAT 上的 spectral ridge、EEGNet 与两种 LaBraM 配置（36 名被试），BETA 上的标准 CCA、CBraMod 与 EEGNet（70 名被试）——在固定置信度阈值、覆盖率目标、经认证的选择性风险和可学习的拒识选项四种策略下重新评分，另测概率质量，以及按人重新校准的效果和它所花费的标签。没有重新训练任何分类器，所以全覆盖时的准确率都与已发布的数值相同。每个协议在设计上都是类别平衡或均匀的：这些是方法之间的比较，从来不是部署时的错误率；区间重叠时不排名。',
    },
    notes: [
      { en: 'The certified selective risk certified no outer fold on EEGMAT, so it accepted nothing there: no error rate, not a zero one. On BETA its realised error exceeded a certified fold’s own target in some folds: a nominal guarantee across people, whose failure rate is measured here, not assumed. The learned reject option had a lower error than the model’s own calibrated confidence for no method.',
        zh: '经认证的选择性风险在 EEGMAT 上没有认证任何一个外层折，所以在那里什么都没有接受：没有错误率，而不是错误率为零。在 BETA 上，有些已认证折的实际错误率超过了该折自己的目标：这是跨被试的名义保证，它失效的频率在这里是测出来的，不是假设的。可学习的拒识选项在任何一种方法上都没有比模型自身校准后的置信度错得更少。' },
      { en: 'ds003810 (ten people) is shown as crude, in a collapsed robustness panel beside secondary seeds, two sensitivity arms (their risk-certification fold counts only) and an exploratory reject head trained jointly with its classifier. Left out: the idle protocol, whose route-1 window proportions are a different unit from the trial-level idle figures on the same page, and every figure of the BNCI2015-001 arm, whose editorial hold stands.',
        zh: 'ds003810（10 名被试）标为粗略，放在折叠的稳健性面板里，旁边是其余随机种子、两个敏感性分析（只给风险认证的折数），以及一个与分类器联合训练的探索性拒识头。没有放进来的：空闲协议——第一条路线在它上面得到的是按窗口的比例，与同一页上按试次统计的空闲数字单位不同；以及 BNCI2015-001 分析的全部数字——该数据源的编辑暂缓仍然有效。' },
      { en: 'Not published: per-trial, per-person and per-fold values, including the release candidate’s person-level percentiles and its median temperature over folds; the accuracies of the matched-holdout, map-sensitivity and jointly trained arms; and the independent audits themselves, pinned by hash in the review manifest because they carry private storage paths. The primary audit’s one failed check is a documentation error, not a computation error, and is stated as such.',
        zh: '不发布：逐试次、逐人和逐折的数值，包括发布候选文件中按人统计的百分位数，以及各折温度的中位数；匹配留出、映射敏感性与联合训练这几组分析的准确率；以及独立审计文件本身——它们含有私有存储路径，只在审核清单中以哈希固定。主审计唯一没有通过的一项是文档错误，不是计算错误，这里如实说明。' },
    ],
  },
  {
    id: 'large-source-update-20261003', date: '2026-10-03', payload: 'largeSource',
    files: ['large-source-update.json'],
    pages: ['/topics/sleep-staging/', '/topics/calibration-budget/'],
    summary: {
      en: 'Two new sources, two separate questions, each with two fixed classical CPU baselines and no shared ranking. Dreem: five-stage sleep staging against the publisher’s consensus in 25 healthy sleepers (DOD-H) and 55 people with obstructive sleep apnoea (DOD-O), kept as separate experiments — a training prior and a spectral ridge, accuracy beside balanced accuracy, macro F1, Cohen’s kappa and the ridge’s stage-by-stage results. And OpenBMI: a motor-imagery decoder trained on a person’s first session and tested on their second after 0, 10, 20 or 40 labelled trials from it, in 51 people, with how many people declined beside every mean change. No foundation-model or fine-tuning result.',
      zh: '两个新来源、两个各自独立的问题，各有两个固定的经典 CPU 基线，彼此不排名。Dreem：以发布者的共识分期为标准的五期睡眠分期，25 名健康被试（DOD-H）与 55 名阻塞性睡眠呼吸暂停患者（DOD-O）作为两项独立实验——训练集先验与 spectral ridge，准确率与平衡准确率并排，另有宏平均 F1、Cohen kappa 系数，以及 spectral ridge 的逐期结果。另有 OpenBMI：运动想象解码器在被试的第一次会话上训练，加入第二次会话的 0、10、20 或 40 个校准试次后在第二次会话上测试，51 名被试，每个平均变化旁都给出有多少人下降。没有基础模型或微调结果。',
    },
    notes: [
      { en: 'The spectral ridge never predicts N1 in either cohort, so its N1 precision is not defined: it is published as null, never as zero. The training prior’s balanced accuracy sits slightly above one fifth because a night’s mean covers only the stages that night contains; it is a floor, not a chance level. Neural-network and foundation models on the Dreem cohorts are held, because the source’s physical units disagree.',
        zh: 'spectral ridge 在两个队列中都从未预测过 N1，所以它的 N1 精确率没有定义：发布为空值，而不是零。训练集先验的平衡准确率略高于五分之一，因为每晚的均值只涵盖该晚出现过的分期；它是一个下限，不是随机水平。Dreem 队列上的神经网络与基础模型暂缓，因为数据源的物理单位说法不一致。' },
      { en: 'OpenBMI is an expanded cohort under the same fixed method — the original 40 people with their results unchanged, plus 11 later-eligible people — not an independent replication; an earlier 40-person snapshot was prepared but never published here and is not a separate result. The relative-PSD change at 40 trials has an interval that includes zero and is not established.',
        zh: 'OpenBMI 是同一固定方法下扩大的队列——原有 40 名被试、结果不变，加上之后符合条件的 11 名被试——不是独立的重复验证；更早的 40 人快照已准备好、但从未在本站发布，它不是一个单独的结果。相对 PSD 基线在 40 个试次时的变化，区间包含零，不能认定。' },
      { en: 'Not published: per-person and per-night values (including the worst observed change, medians and 10th percentiles), Brier scores, log-likelihoods and calibration errors, the combined DOD-H plus DOD-O summary, and the independent audits themselves, which are pinned by hash in the review manifest because they carry private storage paths.',
        zh: '不发布：逐人与逐晚的数值（包括观察到的最差变化、中位数与第 10 百分位数）、Brier 分数、对数似然与校准误差、DOD-H 与 DOD-O 合并后的汇总，以及独立审计文件本身——它们含有私有存储路径，因此只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'extension-update-20261002', date: '2026-10-02', payload: 'extension',
    files: ['extension-update.json'],
    pages: ['/topics/when-not-to-act/', '/topics/screen-to-vr/'],
    summary: {
      en: 'Twenty further people of the asynchronous SSVEP release, scored with a rejection threshold fixed on the four-person pilot and with a personal one: detection, coverage, correct-and-accepted output and false acceptance per non-control state, side by side. And a new source, LTRSVP: a P300 decoder trained on one recording at 5 or 10 images a second and tested on a different, 10-Hz recording, with the full rate-by-rate matrix. Fixed classical baselines; no foundation-model or fine-tuning result.',
      zh: '异步 SSVEP 数据集中另外 20 名被试，分别用在四人试点上固定的拒识阈值和逐人阈值评分：检测、覆盖率、被接受且正确的输出，以及每种非控制状态下的误接受，并排给出。另有一个新来源 LTRSVP：P300 解码器在每秒 5 张或 10 张图像的一段记录上训练，在另一段 10 Hz 记录上测试，附完整的速率对速率矩阵。都是固定的经典基线，没有基础模型或微调结果。',
    },
    notes: [
      { en: 'The personal threshold raised detection balanced accuracy for 10 of 20 people and lowered it for 8, and did not raise the share of commands both accepted and correct. The image-rate difference has an interval that crosses zero, and rate and recording change together, as does time in the session (the original study presented the rates from the lowest to the highest, not randomised), so no rate effect is claimed.',
        zh: '逐人阈值使 20 名被试中 10 人的检测平衡准确率上升、8 人下降，被接受且正确的指令占比并没有提高。图像速率差值的区间跨过零，而且速率与记录一起变化，在实验中的时间位置也随之变化（原始研究按速率从低到高呈现，没有随机化），所以不声称存在速率效应。' },
      { en: 'Not published: per-person values, thresholds, predictions, and the independent audits themselves, which are pinned by hash in the review manifest because they carry private storage paths.',
        zh: '不发布：逐人数值、阈值、预测结果，以及独立审计文件本身——它们含有私有存储路径，因此只在审核清单中以哈希固定。' },
    ],
  },
  {
    id: 'adaptation-update-20261001', date: '2026-10-01', payload: 'adaptation',
    files: ['adaptation-update.json'],
    // Published on calibration-budget; its own topic since 2026-10-02.
    pages: ['/topics/model-adaptation/'],
    summary: {
      en: 'New people, same task, zero labels from the test person: LaBraM adapted on mental arithmetic three ways — head only, last block, rank-4 LoRA — with the same checkpoint, folds, starting heads, batch order and five-epoch recipe, over three seeds. The next-day experiment is listed as status only.',
      zh: '新被试、同一任务、不使用测试被试的任何标签：在心算任务上用三种方式适配 LaBraM——只训分类头、最后一个 Transformer 块、秩为 4 的 LoRA——使用相同的检查点、数据划分、初始分类头、批次顺序和训练 5 轮的配方，跑了 3 个随机种子。次日实验只列状态。',
    },
    notes: [
      { en: "Printed beside the core matrix's frozen LaBraM readout on the same people and folds, because this batch's head-only arm is a short gradient-trained head and not the strongest frozen readout.",
        zh: '与核心矩阵中同一批被试、同一数据划分上的冻结 LaBraM 分类头结果并排给出，因为本批「只训分类头」那一组是短训练的梯度分类头，并不是冻结编码器能达到的最好结果。' },
      { en: 'Not published: memory figures (allocator samples are lower bounds, not per-method peaks) and any figure from the next-day experiment.',
        zh: '不发布：内存数据（分配器采样只是下界，不是各方法的峰值），以及次日实验的任何数字。' },
    ],
  },
  {
    id: 'context-update-20260927', date: '2026-09-27', payload: 'context',
    files: ['context-update.json'],
    pages: ['/topics/screen-to-vr/', '/topics/on-the-move/', '/topics/when-not-to-act/'],
    summary: {
      en: 'P300 calibration carried from a PC screen to a VR headset and back for 21 people; walking-speed scores from dry-electrode EEG printed beside a movement-nuisance comparator; and a four-person pilot of SSVEP windows accepted when no command was intended. Fixed CPU baselines; no foundation-model or fine-tuning result.',
      zh: '21 名被试的 P300 校准在电脑屏幕与 VR 头显之间来回迁移；行走时干电极 EEG 的步速分数，旁边并排放着运动干扰特征的对照基线；以及一个四人试点：无意发出指令时，SSVEP 窗口被误接受的情况。都是固定的 CPU 基线，没有基础模型或微调结果。',
    },
    notes: [
      { en: 'Not published although correct: the direction-specific transfer means, because the independent audit did not recompute them.',
        zh: '虽然正确也不发布：分方向的迁移均值，因为独立审计没有重新计算它们。' },
    ],
  },
  {
    id: 'clinical-update-20260923', date: '2026-09-23', payload: 'clinical',
    files: ['clinical-update.json'],
    pages: ['/topics/clinical-groups/'],
    summary: {
      en: 'A 149-person clinical case/control comparison, printed beside an age-and-sex-only comparator, and three holds that produced no score.',
      zh: '149 名被试的临床病例对照比较，旁边并排放着只用年龄和性别的对照基线；另有三项暂缓，都没有产生分数。',
    },
    notes: [
      { en: 'Not published although aggregate: the per-group age and sex composition of the clinical cohort.',
        zh: '虽然是聚合量也不发布：临床队列各组的年龄与性别构成。' },
    ],
  },
  {
    id: 'evidence-update-20260922', date: '2026-09-22', payload: 'evidence',
    files: ['evidence-update.json'],
    // The adaptation roadmap it carried was on calibration-budget; what is left of
    // it, the engineering check, has been on model-adaptation since 2026-10-02.
    pages: ['/topics/fewer-electrodes/', '/topics/on-the-move/', '/topics/model-adaptation/'],
    summary: {
      en: 'In-ear against scalp sleep staging, four posterior electrodes against sixteen, a physical-phantom motion test, and the status of planned adaptation experiments.',
      zh: '耳道内与头皮的睡眠分期比较、后部 4 个电极对全部 16 个电极、物理头模的运动测试，以及计划中的适配实验的状态。',
    },
    notes: [
      { en: 'Amended the EESM19 consent note (see data use). The core snapshot and the topic export were regenerated with one added citation; no score changed. Their current hashes, below, are the amended files.',
        zh: '修订了 EESM19 的同意书说明（见数据使用页）。核心快照与专题导出因此重新生成，只多了一条引用，没有任何分数变化。下方显示的是修订后文件的哈希。' },
    ],
  },
  {
    id: 'deployment-topics-20260920-v1', date: '2026-09-20', payload: 'deployment',
    files: ['deployment-topics.json'],
    pages: ['/topics/dry-vs-wet/', '/topics/on-the-move/', '/topics/calibration-budget/', '/topics/does-pretraining-help/'],
    summary: {
      en: 'Four deployment questions, each with its own protocol: paired contrasts, descriptive intervals and three-seed sensitivity groups.',
      zh: '四个部署问题，各有自己的协议：配对对比、描述性区间，以及三个随机种子的敏感性分组。',
    },
    notes: [],
  },
  {
    id: 'research-preview-20260920', date: '2026-09-20', payload: 'mvp',
    files: ['experiments.json', ...protocolFiles],
    pages: ['/'],
    summary: {
      en: 'The core matrix: eight fixed protocols on seven public data sets, with one file of results and one protocol descriptor per protocol.',
      zh: '核心矩阵：7 个公开数据集上的 8 个固定协议，每个协议一份结果文件和一份协议说明。',
    },
    notes: [],
  },
];

// Newest first is load-bearing: the home page's "Updated" date, the /api/
// citation, the home Dataset markup and CITATION.cff all take the first entry.
for (let i = 1; i < releases.length; i++)
  if (releases[i].date > releases[i - 1].date)
    throw new Error(`releases.ts: ${releases[i].id} is newer than ${releases[i - 1].id}; keep the list newest first`);

/** The newest release: the one the site, CITATION.cff and the home Dataset markup cite. */
export const latestRelease = releases[0];

/**
 * The releases that ship the given served files ('deployment-topics.json' or
 * '/data/deployment-topics.json'), newest first, each once. A page's "cite this
 * page" block names these, so it can only cite a release whose bytes the page's
 * figures come from.
 */
export function releasesFor(files: string[]): Release[] {
  const names = new Set(files.map(f => f.replace(/^\/data\//, '')));
  const found = releases.filter(r => r.files.some(f => names.has(f)));
  const shipped = new Set(found.flatMap(r => r.files));
  const unknown = [...names].filter(f => !shipped.has(f));
  if (unknown.length) throw new Error(`releases.ts: no release ships ${unknown.join(', ')}`);
  return found;
}

export interface Hold {
  /**
   * Stable slug: the register row on /releases/ is `#hold-<id>`, and a home card
   * without a page of its own links there. The payload's own id where it has one.
   */
  id: string;
  item: Text;
  /** Short state word for the home-page card. */
  state: Text;
  opened: string;
  closed: string | null;
  outcome: Text;
  href?: string;
}

/** Every hold ever recorded, open or resolved. The home page shows the open ones. */
export const holds: Hold[] = [
  {
    id: 'dreem-amplitude-sensitive-models',
    item: { en: 'Dreem sleep cohorts · neural-network and foundation models', zh: 'Dreem 睡眠队列 · 神经网络与基础模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-10-03', closed: null,
    outcome: { en: 'The stored signal metadata says millivolts; the publisher’s own converter treats the same arrays as microvolts. Models that need absolute amplitude are not run on a guessed unit, so no such score exists. The published baselines do not depend on the unit.',
               zh: '存储的信号元数据写的是毫伏，发布者自己的转换程序却把同样的数组当作微伏。需要绝对幅值的模型不在猜测的单位上运行，所以没有这类分数。已发布的基线不依赖这个单位。' },
    href: '/topics/sleep-staging/#held',
  },
  {
    id: 'ysu-async-ssvep-consent',
    item: { en: 'YSU asynchronous SSVEP · consent statement', zh: 'YSU 异步 SSVEP · 同意书声明' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-27', closed: '2026-09-27',
    outcome: { en: 'Scored and audited, then held until the data paper’s consent and ethics statement was read; released the same day.',
               zh: '已评分并通过审计，暂缓到读到数据论文中的同意书与伦理声明为止；当天发布。' },
    href: '/topics/when-not-to-act/#non-control',
  },
  {
    id: 'stieger-longitudinal',
    item: { en: 'Stieger longitudinal BCI · one-person pilot', zh: 'Stieger 纵向 BCI · 单人试点' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: '2026-09-27', closed: null,
    outcome: { en: 'The pipeline works on one person’s eleven sessions. With one person every score is that person’s, so none is published.',
               zh: '流程在一名被试的 11 次会话上跑通了。只有一个人时，任何分数都是这个人的分数，所以不发布。' },
    href: '/topics/model-adaptation/#cross-session',
  },
  {
    id: 'ds004902',
    item: { en: 'OpenNeuro ds004902 · paired sleep comparison', zh: 'OpenNeuro ds004902 · 配对睡眠比较' },
    state: { en: 'No score', zh: '没有分数' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'Five source payloads are shorter than their own headers declare. No score of any kind.',
               zh: '5 个源文件比自己的文件头声明的还短。没有任何分数。' },
  },
  {
    id: 'clinical-foundation-models',
    item: { en: 'Foundation models on the clinical set', zh: '临床数据上的基础模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'The source states no physical amplitude unit. Not run on an assumed one.',
               zh: '数据源没有说明物理幅值单位。不按假设的单位去跑。' },
    href: '/topics/clinical-groups/',
  },
  {
    id: 'lfame',
    item: { en: 'L-FAME', zh: 'L-FAME' },
    state: { en: 'Described, not scored', zh: '只有描述，没有评分' },
    opened: '2026-09-22', closed: null,
    outcome: { en: 'Not included on 22 September (intake only). Since 23 September: described, not scored; its per-condition numbers withheld.',
               zh: '9 月 22 日未纳入（只完成了数据接收）。9 月 23 日起：只有描述、没有评分，按条件汇总的数值不发布。' },
  },
  {
    id: 'alphawaves-consent',
    item: { en: 'Alpha Waves · primary consent source', zh: 'Alpha Waves · 一手同意书来源' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-22', closed: '2026-09-22',
    outcome: { en: 'Released the same day, after the primary report’s consent statement was read.',
               zh: '当天读到原始报告中的同意书声明后发布。' },
    href: '/topics/fewer-electrodes/#posterior-subset',
  },
  {
    id: 'bnci2015-001-crossday',
    item: { en: 'BNCI2015-001 · next-day adaptation', zh: 'BNCI2015-001 · 次日适配' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-09-20', closed: null,
    outcome: { en: 'Run and independently replayed on 22 September. The catalogue licence is CC BY-NC-ND and the description names no ethics approval, so no figure is published until that review is done.',
               zh: '9 月 22 日已运行并通过独立复核。目录标注的许可是 CC BY-NC-ND，数据说明也没有写伦理批准，所以审查完成之前不发布任何数字。' },
    href: '/topics/model-adaptation/#next-day',
  },
];
if (new Set(holds.map(h => h.id)).size !== holds.length) throw new Error('releases.ts: two holds share an id');

export interface Correction {
  date: string;
  /** The served files whose text the correction amends. Their bytes are not rewritten. */
  files: string[];
  what: Text;
  href?: string;
}

/**
 * Corrections to wording in files already released. A release is a record of
 * fixed bytes (their hashes are on the releases page and in the Hugging Face
 * mirror), so a wrong sentence in one is corrected here and on the page that
 * shows it, not by editing the file.
 */
export const corrections: Correction[] = [
  {
    date: '2026-10-01', files: ['deployment-topics.json'],
    what: { en: 'The ensemble-TRCA rows call the original method a three-filter-bank experiment. The original paper and the reference code’s tutorials use five sub-bands; three is only the default of the code’s functions. Our runs used one fixed band either way, and no score changes.',
            zh: '集成 TRCA 各行把原方法称为「三子带滤波器组实验」。原论文与参考代码的教程用的是 5 个子带，3 只是代码函数的默认值。我们的运行无论如何都只用一个固定频带，没有任何分数变化。' },
    href: '/topics/calibration-budget/#methods-and-limits',
  },
  {
    date: '2026-10-01', files: ['experiments.json', 'mi-rest-results.csv', 'mi-rest-protocol.json', 'deployment-topics.json'],
    what: { en: 'The ds003810 credit links only the 2022 Data in Brief description. The OpenNeuro record asks users to cite Peterson, Galván, Hernández and Spies, Heliyon 6(3):e03425 (2020); the dataset page now gives both.',
            zh: 'ds003810 的署名只链接了 2022 年的 Data in Brief 数据描述。OpenNeuro 记录要求引用 Peterson、Galván、Hernández 与 Spies 发表于 Heliyon 6(3):e03425（2020）的论文；数据集页面现在两者都给出。' },
    href: '/datasets/ds003810/#methods-and-limits',
  },
];

/** Citations a source asks for that a released file does not carry; shown on its dataset page. */
export const requestedCitations: Record<string, { text: string; url: string; basis: string }> = {
  ds003810: {
    text: 'Peterson V, Galván C, Hernández H, Spies R. A feasibility study of a complete low-cost consumer-grade brain-computer interface system. Heliyon 6(3):e03425 (2020).',
    url: 'https://doi.org/10.1016/j.heliyon.2020.e03425',
    basis: 'https://openneuro.org/datasets/ds003810',
  },
};
