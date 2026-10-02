/**
 * Interface copy in English and Chinese.
 *
 * Scope, as decided: the interface, the topic pages, the dataset and method
 * pages, the release log and the data API page are translated.
 * /data-use/ and 404 stay English-only — a policy text in two parallel versions
 * invites the question of which one binds, and the answer is not worth having to
 * give. Every link from a Chinese page to /data-use/ says it leads to English.
 *
 * What is NOT translated anywhere: dataset names, licence identifiers,
 * attribution strings, DOIs and model names. Those are citation material —
 * "CC BY 4.0" has one spelling, a credit belongs to the person who earned it,
 * and a translated DOI is a broken link.
 *
 * Nor is the release payload. Protocol steps, limitations, table details and
 * attributions render in English on the Chinese pages too, marked
 * `lang="en"`. That is a hard constraint as well as a choice: check-workbench.mjs
 * asserts the page-data and downloadable copies of the topic export are
 * byte-identical, and check_site_artifact.py pins its SHA-256 against the
 * review audit. Short interface labels that happen to come from the payload —
 * protocol titles, metric names, statuses — are mapped for display below,
 * keyed by their English value, which leaves the data files untouched. So are
 * the home page's model-directory notes and licence and rights-review notes
 * (directory-zh.json, `directoryText`), which a Chinese reader needs in order
 * to use the directory at all; licence identifiers stay as written.
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
 *   privacy / metadata exposure  隐私暴露 / 元数据暴露   the only two places 暴露
 *                                                stands (rights-review notes);
 *                                                the lint allows nothing else
 *   participant-disjoint         被试不重叠
 *   session                      会话            (跨会话 is established usage)
 *   confounded / entangled       相互混杂
 *   target-only                  仅用目标被试数据
 *   method names                 stay English: spectral ridge, eTRCA, CCA …
 *                                with a gloss at first use where helpful;
 *                                descriptive labels are translated:
 *                                单频带 eTRCA, CCA（按原作者设置）, 均匀随机,
 *                                同频功率 (modelLabel in topics.ts)
 *   channel                      通道            not 导 ("64 导 EEG"); 多导睡眠图
 *                                                is the established word for
 *                                                polysomnography and stays
 *   percentage points            pp              glossed 百分点 at its first use
 *                                                on a page; not 个百分点
 *   training epoch               轮              "训练 5 轮", not "5 个 epoch"
 *   epoch (ERP, a time window)   分段
 *   epoch (sleep, 30 s scoring)  帧 / 数据帧
 *   network block                Transformer 块（block）  the experimental block
 *                                                is 组块; the two meet on one page
 *   institutions                 Chinese institutions by their standard Chinese
 *                                names (清华大学, 天津大学, 燕山大学); others as
 *                                they name themselves
 */
import { site } from './site';
import directoryZh from './directory-zh.json';

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
  '/topics/screen-to-vr/',
  '/topics/fewer-electrodes/',
  '/topics/clinical-groups/',
  '/topics/on-the-move/',
  '/topics/calibration-budget/',
  '/topics/model-adaptation/',
  '/topics/does-pretraining-help/',
  '/topics/when-not-to-act/',
  '/releases/',
  '/api/',
] as const;

/**
 * Dataset, method and protocol pages exist in every locale too. They are
 * generated from the payloads (src/data/entities.ts, src/data/protocols.ts), so
 * they are matched by shape here rather than listed; the sitemap lists them
 * from those modules.
 */
export const isTranslated = (path: string) =>
  (translatedPaths as readonly string[]).includes(path) || /^\/(?:datasets|methods|protocols)\/(?:[a-z0-9-]+\/)?$/.test(path);

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
  /** Before the date of the newest release, on the home page. */
  updated: string;
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
  footerReleases: string;
  downloadData: string;
  /** Appended to any link that leaves a Chinese page for an English-only one. */
  englishMark: string;
  /**
   * The share card (public/og.png) in words: its own text and the core-matrix
   * counts it prints. The card is English; the Chinese alt describes it in Chinese.
   */
  shareAlt: (c: ShareCounts) => string;
  /** Footer links to the project's other public homes (site.ts). All three are English. */
  footerCode: string;
  footerMirror: string;
  footerCite: string;
  footerElsewhere: string;
}

/** The core-matrix counts printed on the share card (src/data/share-card.ts). */
export interface ShareCounts { protocols: number; datasets: number; comparisons: number; methods: number }

export const chrome: Record<Locale, Chrome> = {
  en: {
    updated: 'Updated',
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
    footerReleases: 'Releases & downloads',
    downloadData: 'Download data ↓',
    englishMark: '',
    shareAlt: c => `${site.name}: Every EEG score, with the protocol that produced it. Core benchmark matrix: ` +
      `${c.protocols} protocols, ${c.datasets} datasets, ${c.comparisons} comparisons, ${c.methods} methods.`,
    footerCode: 'Code on GitHub',
    footerMirror: 'Data mirror on Hugging Face',
    footerCite: 'Cite: CITATION.cff',
    footerElsewhere: 'Elsewhere',
  },
  zh: {
    updated: '更新于',
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
    footerReleases: '发布记录与下载',
    downloadData: '下载数据 ↓',
    englishMark: '（英文）',
    shareAlt: c => `${site.name}：每一个 EEG 分数，都附带产生它的协议。核心基准矩阵：` +
      `${c.protocols} 个协议、${c.datasets} 个数据集、${c.comparisons} 项比较、${c.methods} 种方法。`,
    footerCode: 'GitHub 上的代码',
    footerMirror: 'Hugging Face 数据镜像',
    footerCite: '引用文件 CITATION.cff',
    footerElsewhere: '站外',
  },
};

/* --- "Cite this page" (topic, dataset and method pages) ------------------- */

/**
 * The block at the foot of every topic, dataset and method page, and its
 * Markdown copy. English gives an author-date line; Chinese follows GB/T 7714
 * for an online resource ([EB/OL], the date in brackets). Either way it names
 * the release whose files hold the page's figures, and sends the reader on to
 * the upstream dataset's own credit — the measurements are ours, the
 * recordings are not.
 */
export const citeCopy = {
  en: {
    heading: 'Cite this page',
    figuresFrom: (n: number) => (n === 1 ? 'Figures from release' : 'Figures from releases'),
    upstreamPage: 'Cite the upstream datasets as well: their credits are on this page.',
    upstreamDatasets: 'Cite the upstream datasets as well: each dataset’s page gives its credit.',
    bibtex: 'BibTeX for the site and its releases →',
  },
  zh: {
    heading: '引用本页',
    figuresFrom: (_n: number) => '数字来自发布',
    upstreamPage: '也请同时引用上游数据集：署名就在本页。',
    upstreamDatasets: '也请同时引用上游数据集：每个数据集页面都写明了署名。',
    bibtex: '本站及各次发布的 BibTeX →',
  },
} satisfies Record<Locale, unknown>;

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

/** What a protocol's split generalises to, keyed by the payload's `short`. */
export const trackShort = zhLabel({
  'Transfer to a new person': '迁移到新被试',
  'False activation × detection': '误触发 × 检出率',
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

/**
 * A model-directory or data-register note (mvp.json `note`, `license`,
 * `detail`) as the page prints it. Chinese from directory-zh.json where the
 * exact English text has a translation; otherwise the English, with
 * `lang: 'en'` so the element can say so. The payload itself is never touched.
 *
 * `original` is the released English behind a translation. Rights-review and
 * licence notes print it beside the Chinese, marked lang="en" and visually
 * secondary (class "note-original"), because those notes are what a reader
 * relies on and the English is the reviewed text (decided 2026-10-02). Model
 * notes print the Chinese alone.
 */
export function directoryText(text: string, locale: Locale): { text: string; lang?: 'en'; original?: string } {
  if (locale === 'en') return { text };
  const zh = (directoryZh.text as Record<string, string>)[text];
  return zh ? { text: zh, original: text } : { text, lang: 'en' };
}

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
    eyebrow: (date: string) => `Open EEG evaluation · Snapshot ${date}`,
    h1: 'Every EEG score, with the protocol that produced it.',
    lede: (c: HomeCounts) =>
      `The core matrix covers ${c.methods} decoding methods under ${c.protocols} fixed protocols on ${c.datasets} public datasets. ` +
      `Separate topics add evidence on sensors, displays, electrode layout, movement, calibration and model adaptation, when not to act, pretraining and clinical groups.`,
    statsLabel: 'Core matrix coverage',
    stats: { protocols: 'Protocols', datasets: 'Datasets', comparisons: 'Comparisons', methods: 'Methods' },
    topicsEyebrow: 'Questions',
    // Count-free: the number of topics grows, and a heading that states it goes stale.
    topicsH2: 'What the evidence can answer',
    // No summed count: the topics now draw on two exports that measure different
    // things (proportions, correlation, R²), and one total would add them up.
    topicsLede: (_n: number) =>
      'Aggregate measurements, organized by the decision they can inform. They are repeated ' +
      'conditions within protocols, not independent experiments, and not an overall ranking.',
    readEvidence: 'Read the evidence →',
    releasesNote: 'Every reviewed release, each download with its SHA-256, and what each batch held back.',
    releasesLink: 'Releases & downloads →',
    holdsEyebrow: 'Holds',
    holdsH2: 'What is held back, and since when',
    holdsLede: 'Results that are missing on purpose. A hold is not a failed result: it is one that cannot be published honestly yet. The register, including resolved holds, is on the releases page.',
    holdsSince: (d: string) => `Held since ${d}`,
    holdsRegister: 'Full holds register →',
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
    eyebrow: (date: string) => `公开 EEG 评测 · 快照 ${date}`,
    h1: '每一个 EEG 分数，都附带产生它的协议。',
    lede: (c: HomeCounts) =>
      `核心矩阵覆盖 ${c.methods} 种解码方法、${c.protocols} 个固定协议、${c.datasets} 个公开数据集。` +
      `另有若干专题，补充了关于传感器、显示设备、电极布局、运动、校准与模型适配、何时不该执行、预训练与临床分组的证据。`,
    statsLabel: '核心矩阵覆盖范围',
    stats: { protocols: '协议', datasets: '数据集', comparisons: '比较', methods: '方法' },
    topicsEyebrow: '专题',
    topicsH2: '证据能回答的问题',
    topicsLede: (_n: number) =>
      '聚合测量结果，按它们能支持的决策来组织。它们是同一协议内的重复条件，不是独立实验，也不是总排名。',
    readEvidence: '查看证据 →',
    releasesNote: '每一次经过审核的发布、每个下载文件及其 SHA-256，以及每一批暂缓了什么。',
    releasesLink: '发布记录与下载 →',
    holdsEyebrow: '暂缓发布',
    holdsH2: '暂缓发布的内容，以及从何时开始',
    holdsLede: '有意暂不发布的结果。暂缓不代表结果失败，只是目前还不能如实发布。完整登记册（含已解除的暂缓）在发布记录页上。',
    holdsSince: (d: string) => `${d}起暂缓`,
    holdsRegister: '完整暂缓登记册 →',
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
    methodsH2: '离开测量条件，分数就没有意义。',
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
    payloadNote: '协议步骤、局限说明、结果表中的配置说明与数据集署名来自发布数据本身，保持英文原文——它们随数据一起被审核，翻译会让网页与可下载文件不再一致。模型目录与公开数据两节中的备注和许可说明译成了中文，许可名称保持原文；下载文件仍为英文。',
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
    shortAnswer: 'Short answer',
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
    shortAnswer: '简答',
    interval95: '95% 区间',
    to: '至',
    period: '。',
  },
} as const;

/** Topic cards on the homepage and in the "keep exploring" strip. */
/**
 * `question` is the page's h1 and <title>: the question as a reader, or an
 * assistant searching on a reader's behalf, would type it. `title` stays the
 * short label used on cards, in breadcrumbs and in the topic switcher.
 */
export const topicCards: Record<Locale, Record<string, { kicker: string; title: string; question: string; summary: string; detail: string }>> = {
  en: {
    'dry-vs-wet': { kicker: 'Sensor transfer', title: 'Dry vs. wet electrodes',
      question: 'Do dry EEG electrodes decode as well as wet ones?',
      summary: 'What changes when a decoder crosses between two native eight-channel recordings from the same 102 people?',
      detail: '2 s SSVEP · 12 targets · balanced accuracy' },
    'screen-to-vr': { kicker: 'Context transfer', title: 'Screen to VR',
      question: 'Does a P300 decoder calibrated on a screen still work in VR?',
      summary: 'The same 21 people calibrated on a PC screen and tested in a VR headset, and the reverse — and why the result is not the cost of the change. Plus: a P300 decoder trained at one image rate and tested at another.',
      detail: 'P300 · 21 people in VR · 9 people across image rates' },
    'fewer-electrodes': { kicker: 'Montage', title: 'Fewer electrodes',
      question: 'Can fewer electrodes, or electrodes in the ear, match a full scalp montage?',
      summary: 'In-ear against scalp for sleep, and four posterior electrodes against sixteen for eyes open or closed — and what neither says about any headset.',
      detail: 'Two paired comparisons · 10 and 19 people' },
    'on-the-move': { kicker: 'Motion robustness', title: 'On the move',
      question: 'Does EEG decoding still work while walking or running?',
      summary: 'Standing, walking and running results, with scalp and ear recordings and incompatible time windows kept apart.',
      detail: 'SSVEP balanced accuracy · ERP ROC AUC' },
    'calibration-budget': { kicker: 'Calibration budget', title: 'How much calibration?',
      question: 'How much calibration data does a wearable SSVEP decoder need?',
      summary: 'Twelve, 24 or 48 labeled target trials help some methods more than others—and trial count is not elapsed time.',
      detail: 'Common future blocks · target-only fitting · 102 people' },
    // Split from calibration-budget on 2026-10-02: the LaBraM result adapts on
    // other people and uses no label from the test person, so it is not
    // calibration, and the next-day hold is a different question again.
    'model-adaptation': { kicker: 'Model adaptation', title: 'Which part to update?',
      question: 'New people, next day: which part of a pretrained model should you update?',
      summary: 'LaBraM on new people, same task, zero labels from the test person: head only, last block or LoRA, printed beside the core matrix’s frozen readout. Plus: the next-day experiment, run and held.',
      detail: 'EEGMAT, 36 people · three update rules · next day: held' },
    'when-not-to-act': { kicker: 'Abstention · Jev-style', title: 'When not to act',
      question: 'How often does an EEG decoder fire when nobody is giving a command?',
      summary: 'A decoder that never acts never fires by mistake. Command detection and false activation, read together — and a Jev-style research plan for when to act, wait or recalibrate.',
      detail: 'Idle, 4-person pilot · non-control, 20 people · research plan' },
    'clinical-groups': { kicker: 'Clinical research', title: 'Clinical groups',
      question: 'Can resting-state EEG separate Parkinson\'s disease from controls?',
      summary: 'A 149-person Parkinson\'s and control comparison, with an age-and-sex-only comparator printed beside it — and why neither is a diagnosis.',
      detail: '149 people · one site · balanced accuracy' },
    'does-pretraining-help': { kicker: 'Representation controls', title: 'Does pretraining help?',
      question: 'Does pretraining help EEG foundation models like LaBraM and CBraMod?',
      summary: 'Matched pretrained and constructor-random encoders under fixed and train-selected readout settings.',
      detail: 'Two tasks · two encoders · three random initializations' },
  },
  zh: {
    'dry-vs-wet': { kicker: '传感器迁移', title: '干电极与湿电极',
      question: '干电极的解码效果能和湿电极一样好吗？',
      summary: '同一批 102 名被试、两种原生八通道记录之间，解码器迁移过去会发生什么？',
      detail: '2 秒 SSVEP · 12 个目标 · 平衡准确率' },
    'screen-to-vr': { kicker: '场景迁移', title: '从屏幕到 VR',
      question: '在屏幕上校准的 P300 解码器，换到 VR 里还管用吗？',
      summary: '同样 21 名被试，在电脑屏幕上校准、在 VR 头显里测试，反之亦然——以及为什么这个结果不是换设备的代价。另有：P300 解码器在一种图像呈现速率下训练、在另一种速率下测试。',
      detail: 'P300 · VR 中 21 名被试 · 跨图像速率 9 名被试' },
    'fewer-electrodes': { kicker: '电极布局', title: '更少的电极',
      question: '更少的电极、或耳道内电极，能比得上完整的头皮电极吗？',
      summary: '睡眠分期里耳道内对头皮，睁闭眼任务里后部 4 个对全部 16 个电极——以及两者都不能说明哪款设备更好。',
      detail: '两项配对比较 · 10 名与 19 名被试' },
    'on-the-move': { kicker: '运动鲁棒性', title: '移动中的解码',
      question: '走路或跑步时，EEG 解码还管用吗？',
      summary: '站立、行走与跑动时的结果，头皮与耳部记录、互不兼容的时间窗分开呈现。',
      detail: 'SSVEP 平衡准确率 · ERP ROC AUC' },
    'calibration-budget': { kicker: '校准预算', title: '需要多少校准？',
      question: '可穿戴 SSVEP 解码器需要多少校准数据？',
      summary: '12、24 或 48 个目标被试校准试次，对某些方法帮助更大——而且试次数不等于耗时。',
      detail: '共同的后续组块 · 仅用目标被试数据拟合 · 102 名被试' },
    'model-adaptation': { kicker: '模型适配', title: '该更新哪一部分？',
      question: '新被试、第二天：预训练模型该更新哪一部分？',
      summary: '新被试、同一任务、不使用测试被试的任何标签：LaBraM 只训分类头、最后一个 Transformer 块还是 LoRA，与核心矩阵中冻结编码器的结果并排给出。另有：次日实验，已运行，暂缓发布。',
      detail: 'EEGMAT，36 名被试 · 三种更新方式 · 次日：暂缓' },
    'when-not-to-act': { kicker: '拒识 · Jev-style', title: '何时不该执行',
      question: '没有人下指令时，EEG 解码器误触发有多频繁？',
      summary: '从不执行的解码器，也就从不误触发。把指令检出与误触发放在一起读——并给出一个 Jev-style（一次编码、回答多个问题）研究计划：何时该执行、该等待、该重新校准。',
      detail: '空闲，四人试点 · 非控制状态，20 名被试 · 研究计划' },
    'clinical-groups': { kicker: '临床研究', title: '临床分组',
      question: '静息态 EEG 能把帕金森病患者和对照组区分开吗？',
      summary: '149 名被试的帕金森病与对照比较，旁边并排放着一个只用年龄和性别的对照基线——以及为什么两者都不是诊断。',
      detail: '149 名被试 · 单中心 · 平衡准确率' },
    'does-pretraining-help': { kicker: '表征对照', title: '预训练有用吗？',
      question: '预训练对 LaBraM、CBraMod 这类 EEG 基础模型有帮助吗？',
      summary: '在固定与训练集内选定两种分类头设置下，对比匹配的预训练编码器与随机初始化编码器。',
      detail: '两个任务 · 两种编码器 · 三次随机初始化' },
  },
};

/**
 * Where a Chinese topic question may break across lines. Headings use
 * `word-break: keep-all` (global.css) so 协议 never splits between two lines,
 * which also makes a run of Chinese with no punctuation one unbreakable word;
 * on a phone that run is wider than the line, and `overflow-wrap` then cut it
 * wherever the space ran out — "有多常误触|发". Each "|" marks a phrase
 * boundary and renders as <wbr>. The marks are checked against `question` at
 * build time, so the heading and the <title> can never say different things.
 * Keep each phrase at eight characters or fewer: that is what fits a 320px
 * screen at the phone size (topics.css).
 */
export const topicQuestionPhrases: Record<string, string> = {
  'dry-vs-wet': '干电极的|解码效果|能和湿电极|一样好吗？',
  'screen-to-vr': '在屏幕上|校准的 P300 解码器，换到 VR 里|还管用吗？',
  'fewer-electrodes': '更少的电极、|或耳道内电极，|能比得上|完整的|头皮电极吗？',
  'on-the-move': '走路或跑步时，EEG 解码|还管用吗？',
  'calibration-budget': '可穿戴 SSVEP 解码器|需要多少|校准数据？',
  'model-adaptation': '新被试、|第二天：|预训练模型|该更新|哪一部分？',
  'when-not-to-act': '没有人下指令时，EEG 解码器|误触发|有多频繁？',
  'clinical-groups': '静息态 EEG 能把|帕金森病患者|和对照组|区分开吗？',
  'does-pretraining-help': '预训练对 LaBraM、CBraMod 这类 EEG 基础模型|有帮助吗？',
};

/** The h1 of a topic page as phrases, to be joined with <wbr>. */
export function questionPhrases(slug: string, locale: Locale): string[] {
  const question = topicCards[locale][slug].question;
  const marked = locale === 'zh' ? topicQuestionPhrases[slug] : undefined;
  if (!marked) return [question];
  if (marked.replace(/\|/g, '') !== question)
    throw new Error(`i18n.ts: topicQuestionPhrases['${slug}'] no longer matches its question`);
  return marked.split('|');
}
