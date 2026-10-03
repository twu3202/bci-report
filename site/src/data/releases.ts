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
    date: '2026-10-02',
    // The YSU extension became the main non-control evidence on when-not-to-act
    // and reached its dataset page; LTRSVP joined screen-to-vr as a second
    // presentation change and got a dataset page; the home cards, the dataset
    // index, the API page and the release log name both. The LaBraM adaptation
    // and the next-day statuses moved from calibration-budget to their own
    // topic, model-adaptation; the EEGMAT and LaBraM pages now send readers there.
    // The home restructure (same day) moved the model directory and field notes
    // to /methods/ and the public-data register to /datasets/, and opened the
    // Questions hub at /topics/.
    paths: ['/', '/topics/when-not-to-act/', '/topics/screen-to-vr/', '/releases/', '/data-use/', '/api/',
            '/datasets/', '/datasets/ysu-async-ssvep/', '/datasets/ltrsvp/',
            '/topics/model-adaptation/', '/topics/calibration-budget/', '/datasets/eegmat/', '/methods/labram/',
            '/topics/', '/methods/'],
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
  payload: 'mvp' | 'deployment' | 'evidence' | 'clinical' | 'context' | 'adaptation' | 'extension';
  files: string[];
  pages: string[];
  summary: Text;
  notes: Text[];
}

const protocolFiles = ['mi-rest', 'idle', 'beta-8ch', 'beta-4ch', 'arithmetic-rest', 'p300-target',
  'semantic-target', 'sleep-scalp'].flatMap(id => [`${id}-results.csv`, `${id}-protocol.json`]);

export const releases: Release[] = [
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
