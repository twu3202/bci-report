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

/** Pages changed in the current site update, for sitemap lastmod. */
export const pagesUpdated = {
  date: '2026-09-27',
  // Every topic page gained its question-form title and short answer on this
  // date; the dataset, method and API pages were first published on it.
  paths: ['/', '/topics/when-not-to-act/', '/releases/', '/topics/screen-to-vr/', '/topics/on-the-move/', '/data-use/',
          '/topics/dry-vs-wet/', '/topics/fewer-electrodes/', '/topics/calibration-budget/',
          '/topics/does-pretraining-help/', '/topics/clinical-groups/', '/api/'],
} as const;

type Text = { en: string; zh: string };

export interface Release {
  id: string;
  date: string;
  /** The payload whose release_id / releaseId this entry must match. */
  payload: 'mvp' | 'deployment' | 'evidence' | 'clinical' | 'context';
  files: string[];
  pages: string[];
  summary: Text;
  notes: Text[];
}

const protocolFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].flatMap(id => [`${id}-results.csv`, `${id}-protocol.json`]);

export const releases: Release[] = [
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
    pages: ['/topics/fewer-electrodes/', '/topics/on-the-move/', '/topics/calibration-budget/'],
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

export interface Hold {
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
    item: { en: 'YSU asynchronous SSVEP · consent statement', zh: 'YSU 异步 SSVEP · 同意书声明' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-27', closed: '2026-09-27',
    outcome: { en: 'Scored and audited, then held until the data paper’s consent and ethics statement was read; released the same day.',
               zh: '已评分并通过审计，暂缓到读到数据论文中的同意书与伦理声明为止；当天发布。' },
    href: '/topics/when-not-to-act/#non-control',
  },
  {
    item: { en: 'Stieger longitudinal BCI · one-person pilot', zh: 'Stieger 纵向 BCI · 单人试点' },
    state: { en: 'Status only', zh: '只发状态' },
    opened: '2026-09-27', closed: null,
    outcome: { en: 'The pipeline works on one person’s eleven sessions. With one person every score is that person’s, so none is published.',
               zh: '流程在一名被试的 11 次会话上跑通了。只有一个人时，任何分数都是这个人的分数，所以不发布。' },
  },
  {
    item: { en: 'OpenNeuro ds004902 · paired sleep comparison', zh: 'OpenNeuro ds004902 · 配对睡眠比较' },
    state: { en: 'No score', zh: '没有分数' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'Five source payloads are shorter than their own headers declare. No score of any kind.',
               zh: '5 个源文件比自己的文件头声明的还短。没有任何分数。' },
  },
  {
    item: { en: 'Foundation models on the clinical set', zh: '临床数据上的基础模型' },
    state: { en: 'Held', zh: '暂缓' },
    opened: '2026-09-23', closed: null,
    outcome: { en: 'The source states no physical amplitude unit. Not run on an assumed one.',
               zh: '数据源没有说明物理幅值单位。不按假设的单位去跑。' },
    href: '/topics/clinical-groups/',
  },
  {
    item: { en: 'L-FAME', zh: 'L-FAME' },
    state: { en: 'Described, not scored', zh: '只有描述，没有评分' },
    opened: '2026-09-22', closed: null,
    outcome: { en: 'Not included on 22 September (intake only). Since 23 September: described, not scored; its per-condition numbers withheld.',
               zh: '9 月 22 日未纳入（只完成了数据接收）。9 月 23 日起：只有描述、没有评分，按条件汇总的数值不发布。' },
  },
  {
    item: { en: 'Alpha Waves · primary consent source', zh: 'Alpha Waves · 一手同意书来源' },
    state: { en: 'Released', zh: '已发布' },
    opened: '2026-09-22', closed: '2026-09-22',
    outcome: { en: 'Released the same day, after the primary report’s consent statement was read.',
               zh: '当天读到原始报告中的同意书声明后发布。' },
    href: '/topics/fewer-electrodes/#posterior-subset',
  },
];
