/**
 * Interface copy in English and Chinese.
 *
 * Scope, as decided: the interface and the four topic pages are translated.
 * /data-use/ and 404 stay English-only — a policy text in two parallel versions
 * invites the question of which one binds, and the answer is not worth having to
 * give. Every link from a Chinese page to /data-use/ says it leads to English.
 *
 * What is NOT translated anywhere: dataset names, licence identifiers,
 * attribution strings, DOIs and model names. Those are citation material —
 * "CC BY 4.0" has one spelling, a credit belongs to the person who earned it,
 * and a translated DOI is a broken link.
 *
 * Nor is the release payload. Protocol steps, limitations, model notes and
 * dataset details render in English on the Chinese pages too, marked
 * `lang="en"`. That is a hard constraint as well as a choice: check-workbench.mjs
 * asserts the page-data and downloadable copies of the topic export are
 * byte-identical, and check_site_artifact.py pins its SHA-256 against the
 * review audit. Short interface labels that happen to come from the payload —
 * protocol titles, metric names, statuses — are mapped for display below,
 * keyed by their English value, which leaves the data files untouched.
 */
/*
 * Chinese glossary. One rendering per concept, following Chinese EEG / BCI /
 * cognitive-neuroscience usage rather than a literal gloss of the English.
 * check-workbench.mjs fails the build if a rejected rendering reappears.
 *
 *   participant / subject        被试            not 参与者, 受试者
 *   balanced accuracy            平衡准确率
 *   chance level                 随机水平
 *   frozen encoder               冻结编码器
 *   readout head / head          分类头          not 读出头
 *   constructor-random           随机初始化      not 构造器随机
 *   abstain (reject a decision)  拒识            not 弃权
 *   false activation             误触发          not 误激活
 *   cue-gated                    提示同步        not 提示门控
 *   mental workload              脑力负荷        not 心理负荷
 *   cognitive load               认知负荷        (faithful to the English page)
 *   full range                   极差            not 全距
 *   block (experimental)         组块            not 区块
 *   future blocks                后续组块        not 未来区块
 *   labeled calibration trials   校准试次        not 有标注试次 / N 个标注,
 *                                                which reads as N classes on a
 *                                                12-target task
 *   analytic reference           免训练参考      not 解析参考
 *   pretraining exposure         是否出现在预训练数据中   not 暴露
 *   participant-disjoint         被试不重叠
 *   session                      会话            (跨会话 is established usage)
 *   confounded / entangled       相互混杂
 *   target-only                  仅用目标被试数据
 *   method names                 stay English: spectral ridge, eTRCA, CCA …
 *                                with a gloss at first use where helpful
 */
import { site } from './site';

export const locales = ['en', 'zh'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';

/** Written in each language's own name, which is what a switcher should show. */
export const localeNames: Record<Locale, string> = { en: 'English', zh: '中文' };

/** BCP 47 tags for `lang` and `hreflang`. */
export const htmlLang: Record<Locale, string> = { en: 'en', zh: 'zh-Hans' };
export const ogLocale: Record<Locale, string> = { en: 'en_US', zh: 'zh_CN' };

/** Pages that exist in every locale. Anything else is English-only. */
export const translatedPaths = [
  '/',
  '/topics/dry-vs-wet/',
  '/topics/fewer-electrodes/',
  '/topics/on-the-move/',
  '/topics/calibration-budget/',
  '/topics/does-pretraining-help/',
] as const;

const isTranslated = (path: string) => (translatedPaths as readonly string[]).includes(path);

/** Prefix a path for a locale. English stays at the root. */
export function localizePath(path: string, locale: Locale): string {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return locale === defaultLocale ? clean : `/${locale}${clean}`;
}

/**
 * Where a link to `path` should point from a page in `locale`. An English-only
 * page keeps its English address; prefixing it would link to a 404.
 */
export function hrefFor(path: string, locale: Locale): string {
  const [base, hash] = path.split('#');
  const target = isTranslated(base) ? localizePath(base, locale) : base;
  return hash === undefined ? target : `${target}#${hash}`;
}

/** `getStaticPaths` for a page that exists in every locale. */
export const localeParams = () =>
  locales.map((code) => ({ params: { lang: code === defaultLocale ? undefined : code } }));

export const localeOf = (lang: string | undefined): Locale =>
  (locales as readonly string[]).includes(lang ?? '') ? (lang as Locale) : defaultLocale;

/** hreflang alternates for a translated page, x-default pointing at English. */
export function alternates(path: string, origin: string) {
  if (!isTranslated(path)) return [];
  const abs = (p: string) => new URL(p, origin).href;
  return [
    ...locales.map((code) => ({ hreflang: htmlLang[code], href: abs(localizePath(path, code)) })),
    { hreflang: 'x-default', href: abs(localizePath(path, defaultLocale)) },
  ];
}

/* --- Shared chrome -------------------------------------------------------- */

interface Chrome {
  stage: string;
  skipToResults: string;
  skipToEvidence: string;
  mainNav: string;
  nav: { results: string; explore: string; protocols: string; models: string;
         datasets: string; updates: string; dataUse: string };
  languageLabel: string;
  /** Title on the switcher link when the current page has no translation. */
  onlyInEnglish: string;
  footerTagline: string;
  footerReport: string;
  footerDataUse: string;
  footerBack: string;
  footerTop: string;
  downloadData: string;
  /** Appended to any link that leaves a Chinese page for an English-only one. */
  englishMark: string;
}

export const chrome: Record<Locale, Chrome> = {
  en: {
    stage: 'Research preview',
    skipToResults: 'Skip to results',
    skipToEvidence: 'Skip to evidence',
    mainNav: 'Main navigation',
    nav: { results: 'Results', explore: 'Explore', protocols: 'Protocols', models: 'Models',
           datasets: 'Datasets', updates: 'Updates', dataUse: 'Data use' },
    languageLabel: 'Language',
    onlyInEnglish: 'This page is available in English only',
    footerTagline: 'Aggregate results. Credited sources. Research use.',
    footerReport: 'Report an issue',
    footerDataUse: 'Data use & privacy',
    footerBack: 'Back to results ↑',
    footerTop: 'Back to top ↑',
    downloadData: 'Download data ↓',
    englishMark: '',
  },
  zh: {
    stage: '研究预览',
    skipToResults: '跳至结果',
    skipToEvidence: '跳至证据',
    mainNav: '主导航',
    nav: { results: '结果', explore: '专题', protocols: '协议', models: '模型',
           datasets: '数据集', updates: '动态', dataUse: '数据使用' },
    languageLabel: '语言',
    onlyInEnglish: '本页仅提供英文版',
    footerTagline: '聚合结果，标注来源，研究用途。',
    footerReport: '报告问题',
    footerDataUse: '数据使用与隐私',
    footerBack: '返回结果 ↑',
    footerTop: '返回顶部 ↑',
    downloadData: '下载数据 ↓',
    englishMark: '（英文）',
  },
};

/* --- Display labels for short payload strings ----------------------------- */

type LabelMap = Record<string, string>;
const zhLabel = (map: LabelMap) => (value: string, locale: Locale) =>
  locale === 'zh' ? map[value] ?? value : value;

/** Protocol titles, keyed by the English title the payload carries. */
export const trackTitle = zhLabel({
  'Motor imagery & rest': '运动想象与静息',
  'Idle & command': '空闲与指令',
  'SSVEP · 8 channels': 'SSVEP · 8 通道',
  'SSVEP · 4 channels': 'SSVEP · 4 通道',
  'Arithmetic & rest': '心算与静息',
  'P300 target ERP': 'P300 目标 ERP',
  'Semantic target ERP': '语义目标 ERP',
  'Sleep staging': '睡眠分期',
});

export const metricLabel = zhLabel({
  'Balanced accuracy': '平衡准确率',
  'Command detection ≤3s': '指令检出率 ≤3 秒',
  'Idle false activation': '空闲误触发率',
  'Macro F1': '宏平均 F1',
});

export const modelStatus = zhLabel({
  'Evaluated': '已评测',
  'Adapter needed': '需要适配器',
  'Access gated': '访问受限',
  'Access unverified': '访问未核实',
  'Research candidate': '研究候选',
  'Rights review pending': '权利审查中',
});

export const datasetStatus = zhLabel({
  'Aggregate results': '已发布聚合结果',
  'Not in this release': '未纳入本次发布',
});

export const datasetTask = zhLabel({
  '40-target SSVEP': '40 目标 SSVEP',
  'Arithmetic / rest': '心算 / 静息',
  'Cue-gated idle / command': '提示同步的空闲 / 指令',
  'Five-stage sleep': '五期睡眠分期',
  'Motor imagery / rest': '运动想象 / 静息',
  'P300 target ERP': 'P300 目标 ERP',
  'Research source': '研究来源',
  'Semantic target ERP': '语义目标 ERP',
});

export const familyLabel = (family: string, locale: Locale) => ({
  en: { foundation: 'Foundation model', small: 'Compact model', classical: 'Classical method' },
  zh: { foundation: '基础模型', small: '轻量模型', classical: '经典方法' },
}[locale] as Record<string, string>)[family] ?? family;

/* --- Homepage ------------------------------------------------------------- */

interface HomeCounts { methods: number; protocols: number; datasets: number;
                       comparisons: number; topicRows: number }

export const home = {
  en: {
    title: 'Public EEG Model Evaluation',
    /** One source: the English description is the site's own. */
    description: site.description,
    ogAlt: (c: HomeCounts) => `core benchmark matrix: ${c.protocols} protocols, ${c.datasets} datasets, ${c.comparisons} comparisons, ${c.methods} methods.`,
    eyebrow: (date: string) => `Open EEG evaluation · Snapshot ${date}`,
    h1: 'Every EEG score, with the protocol that produced it.',
    lede: (c: HomeCounts) =>
      `The core matrix covers ${c.methods} decoding methods under ${c.protocols} fixed protocols on ${c.datasets} public datasets. ` +
      `Five deployment topics add evidence on sensors, electrode layout, movement, calibration and pretraining.`,
    statsLabel: 'Core matrix coverage',
    stats: { protocols: 'Protocols', datasets: 'Datasets', comparisons: 'Comparisons', methods: 'Methods' },
    topicsEyebrow: 'Deployment questions',
    topicsH2: 'Five ways to read the new evidence',
    // No summed count: the topics now draw on two exports that measure different
    // things (proportions, correlation, R²), and one total would add them up.
    topicsLede: (_n: number) =>
      'Aggregate measurements, organized by the decision they can inform. They are repeated ' +
      'conditions within protocols, not independent experiments, and not an overall ranking.',
    readEvidence: 'Read the evidence →',
    topicsDownloadNote: 'Full-precision proportions, paired contrasts, descriptive intervals, citations and five three-seed sensitivity groups.',
    topicsDownload: 'Download reviewed topic data · JSON ↓',
    evidenceDownload: 'Evidence update, 22 September · JSON ↓',
    matrixEyebrow: 'Core benchmark matrix',
    matrixH2: (c: HomeCounts) => `${c.methods} methods × ${c.protocols} protocols`,
    matrixLede: 'The original eight-protocol snapshot, separate from the deployment topics above. Blank cells are protocols a method has not been run on — not failures.',
    matrixRegion: 'Coverage matrix of methods against protocols, scrolls horizontally',
    matrixCaption: 'Balanced accuracy of each method on each protocol. Chance level differs by protocol and is given in each column heading.',
    corner: 'Method',
    colDetection: 'detection',
    colChance: (c: number) => `chance ${c}%`,
    covered: (k: number, n: number) => `${k} of ${n}`,
    notEvaluated: (m: string, t: string) => `${m} has not been evaluated on ${t}`,
    atChance: '≤ chance',
    keyLead: 'Best on that protocol',
    keyBar: "Bar = position between that protocol's chance level and 100%",
    keyGap: 'Not evaluated',
    matrixDownload: 'Core matrix · JSON ↓',
    matrixCaveat:
      'Bars are comparable <strong>down</strong> a column and not <strong>across</strong> one: chance level is 50% for the two-class tasks, ' +
      '20% for sleep staging and 2.5% for 40-class SSVEP, and every protocol uses a different cohort and electrode layout. There is no overall score. ' +
      'The idle column reports command detection only — read it with the false-activation rate in its protocol.',
    protocolsEyebrow: 'One protocol at a time',
    protocolsH2: 'The evidence behind each score',
    protocolsLede: 'Cohort, electrode layout, training budget, source terms and known limitations, alongside the numbers they belong to.',
    tabsLabel: 'Evaluation protocol',
    tabParticipants: (n: number) => `${n} participants`,
    panelResults: (title: string) => `${title} results`,
    subjects: 'subjects',
    viewProtocol: 'View protocol ↗',
    measuredHere: 'Measured here',
    atAGlance: 'Results at a glance',
    familyControl: 'Model family',
    allFamilies: 'All families',
    sortControl: 'Sort',
    sortName: 'Model name',
    sortPrimary: 'Primary metric ↓',
    sortSecondary: 'Secondary metric ↓',
    csv: 'CSV ↓',
    tableRegion: 'Results table, scrolls horizontally',
    colModel: 'Model / configuration',
    colCompute: 'Compute time',
    scrollHint: 'Scroll the table sideways for the remaining columns.',
    tableCaption: 'Fixed budgets and adapters; no universal ranking. Scoring time includes fitting and prediction, and may include accelerator waiting. It excludes data preparation.',
    visualEyebrow: 'Visual comparison',
    chartTitle: 'Accuracy by configuration',
    chartNote: 'Read each comparison with its protocol and limitations.',
    rights: 'Aggregate research results',
    originalDataset: 'Original dataset ↗',
    usePrivacy: 'Use & privacy →',
    reportResult: 'Report an issue with this result →',
    readWithCare: 'Read with care',
    methodsLink: 'Methods →',
    atOrBelow: (c: number) => `At or below the ${c}% chance level`,
    intervalReaches: (c: number) => `Interval reaches the ${c}% chance level`,
    singleSeed: (word: string, n: number, lo: string, hi: string, mean: string) =>
      `Single seed — the ${word} of ${n} run (${lo}–${hi}%, mean ${mean}%)`,
    seedWord: { highest: 'highest', lowest: 'lowest', middle: 'middle' } as Record<string, string>,
    modelsEyebrow: 'Model directory',
    modelsH2: 'From compact baselines to foundation models',
    modelsLede: 'Availability and measured performance are separate. Parameter counts depend on the backbone and task configuration.',
    parameters: 'parameters',
    officialSource: 'Official source ↗',
    datasetsEyebrow: 'Public data',
    datasetsH2: 'Public data, documented experiments',
    datasetsLede: 'Source terms are checked separately from numerical results. Unresolved data remain outside this release.',
    dtSubjects: 'Subjects',
    dtChannels: 'Channels',
    newsEyebrow: 'Field notes',
    newsH2: 'Notes from the field',
    newsLede: 'Curated research updates, linked to original sources.',
    methodsEyebrow: 'Evidence before ranking',
    methodsH2: 'A score is only useful with its conditions.',
    downloadAll: 'Download all results · JSON ↓',
    principles: [
      ['A successful forward pass is not a benchmark', 'Downloads, loading checks and scored evaluations have distinct status labels. Models awaiting an adapter have no result.'],
      ['Show the failure modes', 'Report missed commands, false activations and abstention. Zero errors in a short session do not establish all-day reliability.'],
      ['Compare the same task', 'Splits, channels, preprocessing and training modes travel with each protocol. Frozen encoders and scratch baselines are labeled separately.'],
      ['Start with fixed, audited local runs', 'Experiments run offline on a Mac or local GPU workstation. Timings are configuration-specific. This website performs no EEG inference or diagnosis.'],
    ] as [string, string][],
    dialogEyebrow: 'Experiment details',
    colon: ': ',
    closeDialog: 'Close details',
    payloadNote: '',
  },
  zh: {
    title: '公开 EEG 模型评测',
    description:
      '公开 EEG 解码结果，每一项都附带产生它的协议：运动想象、4 与 8 电极 SSVEP、' +
      'P300 与语义 ERP、认知负荷、睡眠分期，以及空闲误触发。',
    ogAlt: (c: HomeCounts) => `核心基准矩阵：${c.protocols} 个协议、${c.datasets} 个数据集、${c.comparisons} 项比较、${c.methods} 种方法。`,
    eyebrow: (date: string) => `公开 EEG 评测 · 快照 ${date}`,
    h1: '每一个 EEG 分数，都附带产生它的协议。',
    lede: (c: HomeCounts) =>
      `核心矩阵覆盖 ${c.methods} 种解码方法、${c.protocols} 个固定协议、${c.datasets} 个公开数据集。` +
      `五个部署专题补充了关于传感器、电极布局、运动、校准与预训练的证据。`,
    statsLabel: '核心矩阵覆盖范围',
    stats: { protocols: '协议', datasets: '数据集', comparisons: '比较', methods: '方法' },
    topicsEyebrow: '部署问题',
    topicsH2: '解读新证据的五个角度',
    topicsLede: (_n: number) =>
      '聚合测量结果，按它们能支持的决策来组织。它们是同一协议内的重复条件，不是独立实验，也不是总排名。',
    readEvidence: '查看证据 →',
    topicsDownloadNote: '全精度比例、配对对比、描述性区间、引用，以及五组各含三个随机种子的敏感性分析。',
    topicsDownload: '下载已审核的专题数据 · JSON ↓',
    evidenceDownload: '9 月 22 日证据更新 · JSON ↓',
    matrixEyebrow: '核心基准矩阵',
    matrixH2: (c: HomeCounts) => `${c.methods} 种方法 × ${c.protocols} 个协议`,
    matrixLede: '最初的八协议快照，与上方的部署专题相互独立。空白单元格表示该方法尚未在该协议上运行——不是失败。',
    matrixRegion: '方法与协议的覆盖矩阵，可横向滚动',
    matrixCaption: '各方法在各协议上的平衡准确率。随机水平因协议而异，标注在每列表头中。',
    corner: '方法',
    colDetection: '检出率',
    colChance: (c: number) => `随机水平 ${c}%`,
    covered: (k: number, n: number) => `${k} / ${n}`,
    notEvaluated: (m: string, t: string) => `${m} 尚未在「${t}」上评测`,
    atChance: '≤ 随机',
    keyLead: '该协议最佳',
    keyBar: '条长 = 在该协议随机水平与 100% 之间的位置',
    keyGap: '未评测',
    matrixDownload: '核心矩阵 · JSON ↓',
    matrixCaveat:
      '条形只能<strong>纵向</strong>比较，不能<strong>横向</strong>比较：二分类任务的随机水平是 50%，' +
      '睡眠分期是 20%，40 分类 SSVEP 是 2.5%，而且每个协议的队列和电极布局都不同。不存在总分。' +
      '空闲一列只报告指令检出率——请结合该协议中的误触发率一起读。',
    protocolsEyebrow: '逐个协议',
    protocolsH2: '每个分数背后的证据',
    protocolsLede: '队列、电极布局、训练预算、来源条款与已知局限，和它们所属的数字放在一起。',
    tabsLabel: '评测协议',
    tabParticipants: (n: number) => `${n} 名被试`,
    panelResults: (title: string) => `${title} 结果`,
    subjects: '名被试',
    viewProtocol: '查看协议 ↗',
    measuredHere: '本协议实测',
    atAGlance: '结果一览',
    familyControl: '模型类别',
    allFamilies: '全部类别',
    sortControl: '排序',
    sortName: '模型名称',
    sortPrimary: '主指标 ↓',
    sortSecondary: '次指标 ↓',
    csv: 'CSV ↓',
    tableRegion: '结果表，可横向滚动',
    colModel: '模型 / 配置',
    colCompute: '计算耗时',
    scrollHint: '横向滚动表格查看其余列。',
    tableCaption: '固定预算与适配器；不存在通用排名。评分耗时包括拟合与预测，可能含加速器等待时间，不含数据准备。',
    visualEyebrow: '可视化比较',
    chartTitle: '各配置的准确率',
    chartNote: '请结合协议与局限阅读每一项比较。',
    rights: '聚合研究结果',
    originalDataset: '原始数据集 ↗',
    usePrivacy: '使用与隐私（英文）→',
    reportResult: '报告此结果的问题（英文）→',
    readWithCare: '谨慎解读',
    methodsLink: '方法 →',
    atOrBelow: (c: number) => `不高于 ${c}% 随机水平`,
    intervalReaches: (c: number) => `区间触及 ${c}% 随机水平`,
    singleSeed: (word: string, n: number, lo: string, hi: string, mean: string) =>
      `仅单个随机种子——为 ${n} 次运行中${word}（${lo}–${hi}%，均值 ${mean}%）`,
    seedWord: { highest: '最高的一次', lowest: '最低的一次', middle: '居中的一次' } as Record<string, string>,
    modelsEyebrow: '模型目录',
    modelsH2: '从轻量基线到基础模型',
    modelsLede: '可获得性与实测表现是两回事。参数量取决于主干网络与任务配置。',
    parameters: '参数',
    officialSource: '官方来源 ↗',
    datasetsEyebrow: '公开数据',
    datasetsH2: '公开数据，有据可查的实验',
    datasetsLede: '来源条款与数值结果分开审查。尚未厘清的数据不纳入本次发布。',
    dtSubjects: '被试',
    dtChannels: '通道',
    newsEyebrow: '领域动态',
    newsH2: '研究前沿动态',
    newsLede: '精选研究动态，均链接至原始来源。',
    methodsEyebrow: '先有证据，再谈排名',
    methodsH2: '分数只有连同条件才有用。',
    downloadAll: '下载全部结果 · JSON ↓',
    principles: [
      ['能跑通前向传播不等于基准测试', '下载、加载检查与完成评分的评测有各自的状态标签。仍待适配器的模型没有结果。'],
      ['把失败模式摆出来', '报告漏检、误触发与拒识。短时间内零错误不能证明全天可靠。'],
      ['比较同一个任务', '数据划分、通道、预处理与训练模式都随协议一起给出。冻结编码器与从头训练的基线分开标注。'],
      ['从固定、经审计的本地运行做起', '实验在 Mac 或本地 GPU 工作站上离线运行。耗时只对该配置有效。本网站不做任何 EEG 推理或诊断。'],
    ] as [string, string][],
    dialogEyebrow: '实验详情',
    colon: '：',
    closeDialog: '关闭详情',
    /** Shown once above the payload-driven sections, which stay in English. */
    payloadNote: '协议步骤、局限说明、模型备注与数据集署名来自发布数据本身，保持英文原文——它们随数据一起被审核，翻译会让网页与可下载文件不再一致。',
  },
} as const;

/* --- Topic pages: shared layout ------------------------------------------- */

export const topicChrome = {
  en: {
    home: 'Home',
    explore: 'Explore',
    breadcrumb: 'Breadcrumb',
    reviewedJson: 'Reviewed aggregate JSON ↓',
    methodsLimits: 'Methods & limits ↓',
    keepExploring: 'Keep exploring',
    exploreNav: 'Explore benchmark questions',
    dataSource: 'Data source:',
    reviewedAggregate: 'reviewed aggregate JSON',
    schema: 'schema',
    generated: 'generated',
    datasetRecord: 'Dataset record ↗',
    sensorsPaper: 'Sensors paper ↗',
    sourceStudy: 'Source study ↗',
    methodsEyebrow: 'Methods & limits',
    interval95: '95% interval',
    to: 'to',
    period: '.',
  },
  zh: {
    home: '首页',
    explore: '专题',
    breadcrumb: '面包屑导航',
    reviewedJson: '已审核的聚合 JSON ↓',
    methodsLimits: '方法与局限 ↓',
    keepExploring: '继续探索',
    exploreNav: '浏览基准问题',
    dataSource: '数据来源：',
    reviewedAggregate: '已审核的聚合 JSON',
    schema: 'schema',
    generated: '生成于',
    datasetRecord: '数据集记录 ↗',
    sensorsPaper: 'Sensors 论文 ↗',
    sourceStudy: '原始研究 ↗',
    methodsEyebrow: '方法与局限',
    interval95: '95% 区间',
    to: '至',
    period: '。',
  },
} as const;

/** Topic cards on the homepage and in the "keep exploring" strip. */
export const topicCards: Record<Locale, Record<string, { kicker: string; title: string; summary: string; detail: string }>> = {
  en: {
    'dry-vs-wet': { kicker: 'Sensor transfer', title: 'Dry vs. wet electrodes',
      summary: 'What changes when a decoder crosses between two native eight-channel recordings from the same 102 people?',
      detail: '2 s SSVEP · 12 targets · balanced accuracy' },
    'fewer-electrodes': { kicker: 'Montage', title: 'Fewer electrodes',
      summary: 'In-ear against scalp for sleep, and four posterior electrodes against sixteen for eyes open or closed — and what neither says about any headset.',
      detail: 'Two paired comparisons · 10 and 19 people' },
    'on-the-move': { kicker: 'Motion robustness', title: 'On the move',
      summary: 'Standing, walking and running results, with scalp and ear recordings and incompatible time windows kept apart.',
      detail: 'SSVEP balanced accuracy · ERP ROC AUC' },
    'calibration-budget': { kicker: 'Adaptation budget', title: 'How much calibration?',
      summary: 'Twelve, 24 or 48 labeled target trials help some methods more than others—and trial count is not elapsed time.',
      detail: 'Common future blocks · target-only fitting' },
    'does-pretraining-help': { kicker: 'Representation controls', title: 'Does pretraining help?',
      summary: 'Matched pretrained and constructor-random encoders under fixed and train-selected readout settings.',
      detail: 'Two tasks · two encoders · three random initializations' },
  },
  zh: {
    'dry-vs-wet': { kicker: '传感器迁移', title: '干电极与湿电极',
      summary: '同一批 102 名被试、两种原生八通道记录之间，解码器迁移过去会发生什么？',
      detail: '2 秒 SSVEP · 12 个目标 · 平衡准确率' },
    'fewer-electrodes': { kicker: '电极布局', title: '更少的电极',
      summary: '睡眠分期里耳道内对头皮，睁闭眼任务里后部 4 个对全部 16 个电极——以及两者都不能说明哪款设备更好。',
      detail: '两项配对比较 · 10 名与 19 名被试' },
    'on-the-move': { kicker: '运动鲁棒性', title: '移动中的解码',
      summary: '站立、行走与跑动时的结果，头皮与耳部记录、互不兼容的时间窗分开呈现。',
      detail: 'SSVEP 平衡准确率 · ERP ROC AUC' },
    'calibration-budget': { kicker: '适配预算', title: '需要多少校准？',
      summary: '12、24 或 48 个目标被试校准试次，对某些方法帮助更大——而且试次数不等于耗时。',
      detail: '共同的后续组块 · 仅用目标被试数据拟合' },
    'does-pretraining-help': { kicker: '表征对照', title: '预训练有用吗？',
      summary: '在固定与训练集内选定两种分类头设置下，对比匹配的预训练编码器与随机初始化编码器。',
      detail: '两个任务 · 两种编码器 · 三次随机初始化' },
  },
};
