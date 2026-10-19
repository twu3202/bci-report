/**
 * What the open register's two pages read from the register file (open-register-<D>.json; owner decisions D3, D5 and
 * D11): /datasets/register/ prints the dataset ladder and /methods/register/ the model ladder, both through
 * components/RegisterTable.astro. The file is read as the site serves it, by the name releases.ts gives the newest
 * register version (`openRegister.json`), and only while it is served (files.ts `registerServed`); without it neither
 * page is built and nothing links to one.
 *
 * Every number a register page prints is a value of that file, printed with data-fig and re-read by the checks. What
 * this module adds is words: an English and a Chinese template for every finding code the file declares, the step
 * names and badges of both ladders (i18n.ts `datasetLadder`, `modelLadder` and `registerCopy`, checked word for word
 * against the file's own `level_definitions` and `rules`), the labels of the file's vocabularies, and each row's
 * cells. A finding code, hold reason, vocabulary word or step name without words here fails the build, and so does a
 * count sentence whose parts no longer add up (`registerCounts`).
 *
 * What a row may say, enforced here:
 * - Rows state facts. A re-upload finding (matches_metadata_of, terms_differ; owner decision D3) prints only what the
 *   file gives: which fields match which source, and what the source's captured terms page gives against what the
 *   upload declares, with the capture's date. derived_from says only that the upload's own card names its source.
 * - Repository ids and user names appear in a row's text, never in a link or an anchor. A Hugging Face address that
 *   carries a namespace (`huggingface.co/<user>/<repo>`, `/datasets/<user>/<repo>`) is linked as a search for the
 *   repository's own name, and a captured terms page hosted on Hugging Face is cited without a link. Row anchors are
 *   the file's opaque ids, and each row's correction route is a mail whose subject names that id and nothing else.
 * - No card text, download count, modification date or demographic field is read from the file, so none is printed.
 * - On the Chinese page, this site's own rights-record sentences print in Chinese (`statedTerms`); the share of
 *   participants above chance prints as "not computed" (owner decision D12); #levels prints the file's own Chinese for
 *   what each step needs (`ladderSteps`). The markup names no Hugging Face user (`catalogRows`).
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import mvp from './mvp.json';
import { registerServed } from './files';
import { openRegister } from './releases';
import { site } from './site';
import { datasetLadder, directoryText, hrefFor, modelLadder, registerCopy, registerCorrectionHref, topicCards, translatedPaths, type Locale } from './i18n';
import { entityCopy } from './entity-copy';
import { datasets as datasetEntities, entityPaths, formatFig, tr, type Fig, type Fmt } from './entities';
import { topicPages } from './topics';
import { BINGO_DATASET, HANDWRITING_DATASET, bingoReleased, handwritingReleased } from './pilot-switch';

const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`open-register.ts: ${what}`); };

/* --- The file ------------------------------------------------------------------------------------------------- */

export type Ladder = 'dataset' | 'model';
interface Alias { value: string; kind: string; licence_tag?: string; relation?: string; relation_to?: string }
interface Gap { step: number; item: string; label_en: string; label_zh: string }
interface Finding { code: string; params: Record<string, unknown> }
interface PartTerms { state: string; value: string | null; by: string }
interface LoaderFields { loader: string; paradigm: string | null; people: number | null; channels: number | null; sampling_rate_hz: number | null }
interface RecordNote { record: string; concept_doi: string; latest_version: boolean; licence_identifier: string }
interface Venue { value: string; kind: string; evidence: string; checked: string; url?: string }
export interface RegisterEntry {
  id: string; ladder: Ladder; group: string; kind: string; name: string; aliases: Alias[]; source_groups: string[];
  urls: Record<string, string>; correction: { mailto: string };
  links: { page?: string; case?: string; cases?: string[]; parent_row?: string; exposure?: string };
  hf?: { repo: string; revision_sha: string | null; gated: false | 'manual' | 'auto'; licence_tags: string[]; size_bytes: number | null; files: number | null };
  moabb?: { loaders: string[]; doi: string | null; data_url: string | null; repository: string | null; licence_as_listed: string[];
            release: string; fields_as_listed: LoaderFields[]; record_note?: RecordNote };
  site?: { page: string | null; status: string };
  family?: { uploader: string; series: string; n: number; search_url: string | null };
  terms_as_stated: { value: string | null; by: string };
  original_terms?: { access_kind: string; capture_id: string };
  access: string; level: number; level_cap?: { step: number; rule: string };
  gaps: Gap[]; status: string; findings: Finding[]; checked: string;
  model_kind?: string; signal?: string[]; terms_by_part?: Record<'code' | 'weights' | 'data', PartTerms>;
  venue?: Venue; exposure?: string;
}
interface Capture { capture_id: string; family_slug: string; family: string; url: string; captured_at: string; sha256: string;
                    capture_kind: string; access_kind: string }
interface Family { id: string; kind: string; n: number; uploader?: string; series?: string; licence_tag_counts: Record<string, number>;
                   no_licence_tag?: number; gated?: { manual: number; auto: number }; size_bytes?: number;
                   by_accession_kind?: Record<string, number>; site_rows_with_mirror?: number }
interface LevelDef { en: string; zh: string; needs_en: string; needs_zh: string; items: string[] }
interface ItemDef { step: number; label_en: string; label_zh: string }
export interface RegisterFile {
  schema_version: string; release_id: string; status: string;
  level_definitions: Record<Ladder, Record<string, LevelDef>>;
  item_definitions: Record<Ladder, Record<string, ItemDef>>;
  rules: { id: string; en: string; zh: string }[];
  sources: { hf: { retrieved_at: string; search_terms: string[]; tag_filters: string[] }; moabb: { release: string; catalog_checked: string };
             access_terms: Capture[] };
  counts: {
    rows: { total: number; dataset: number; model: number; dataset_by_group: Record<string, number>; dataset_by_level: Record<string, number>;
            model_by_level: Record<string, number>; by_status: Record<string, number> };
    hf: { snapshot: { retrieved_at: string; search_terms: number; tag_filters: number; listings: number; eegdash_mirrors: number;
                      other_uploads: number; prefilter_dropped: number; classified: number };
          classifier_in_scope: number; family_members: number; family_rows: number; gated_auto: number; gated_manual: number;
          held_for_review: number; in_scope: number; merged_into_site_rows: number; merged_into_moabb_rows: number; no_licence_tag: number;
          recheck_out_emg_rule: number; recheck_out_simulated: number; recheck_out_undetermined: number; single_rows: number };
    eegdash: { mirrors: number; nemar: number; openneuro: number; other: number; site_rows_with_mirror: number; moabb_rows_with_mirror: number };
    moabb: { release: string; loaders: number; record_groups: number; merged_into_site_rows: number };
    corpus: { families: number; captured: number };
    models: { external_rows: number; merged_into_site_methods: number };
  };
  finding_codes: Record<string, { params: Record<string, string>; optional: string[]; reason_codes?: string[]; fields?: string[]; declared_by?: string[] }>;
  vocab: { access: string[]; status: string[]; by: string[]; terms_state: string[]; signal: string[]; model_kind: string[] };
  families: Family[];
  entries: RegisterEntry[];
}

/** The newest register file as the site serves it, or null while it is not served (and no register page is built). */
export const REGISTER_FILE: string = openRegister.json;
export const register: RegisterFile | null = registerServed
  ? JSON.parse(readFileSync(resolve('public/data', REGISTER_FILE), 'utf8')) as RegisterFile
  : null;
/** Whether the register pages are built: both read the served file, so a link to either is guarded on this. */
export const registerBuilt = register !== null;

/* --- Words ---------------------------------------------------------------------------------------------------- */

type T = Record<Locale, string>;
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
/** An evidence date as the page prints it: "19 October 2026", "2026 年 10 月 19 日". */
export const longDate = (iso: string, locale: Locale) => {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  need(y > 2000 && m >= 1 && m <= 12 && d >= 1 && d <= 31, `${iso} is not a date`);
  return locale === 'zh' ? `${y} 年 ${m} 月 ${d} 日` : `${d} ${MONTHS[m - 1]} ${y}`;
};

/** The dataset ladder's groups, in the page's order; `copy` is the key registerCopy.groups names it by. */
export const datasetGroups = [
  { key: 'hf', copy: 'hf' }, { key: 'eegdash', copy: 'eegdash' }, { key: 'site', copy: 'site' },
  { key: 'moabb', copy: 'moabb' }, { key: 'corpus', copy: 'agreement' },
] as const;
/** The model ladder's groups, by row kind (every model row is in the file's one group, `model`). */
export const modelGroups = [
  { key: 'site_model', name: { en: 'Models with results on this site', zh: '在本站有结果的模型' } },
  { key: 'model', name: { en: 'Other models and papers we track', zh: '我们关注的其他模型与论文' } },
] as const;

/** One sentence or two under each group's heading, said once there. */
export const groupNotes: Record<string, T> = {
  hf: {
    en: 'Uploads the register’s classifier marked as brain-signal data in the snapshot counted above, each read from its listing and from its metadata at a pinned revision. A series of repositories from one uploader is one row. What the cards state about signal, task and participants is still being reviewed, so signal and task are left blank here.',
    zh: '上文所计快照中被登记册分类器标为脑信号数据的上传，每个都读取了列表信息和固定版本下的元数据。同一上传者的一系列仓库合为一行。数据卡片关于信号、任务与被试的说法仍在核查，所以这里不填信号与任务。',
  },
  eegdash: {
    en: 'EEGDash’s mirrors of OpenNeuro and NEMAR records, as one row. Which mirror holds which record is in the JSON file; this site’s rows and MOABB rows that have a mirror list it among their names.',
    zh: 'EEGDash 对 OpenNeuro 与 NEMAR 记录的镜像，合为一行。哪个镜像对应哪个记录写在 JSON 文件里；有镜像的本站条目与 MOABB 条目，在名称下列出了它。',
  },
  site: {
    en: 'Datasets this site has scored, held or reviewed, furthest step first. A row with results links its page.',
    zh: '本站计算过分数、暂缓发布或审查过的数据集，核验步骤靠后的在前。有结果的条目链接到它的页面。',
  },
  moabb: {
    en: 'One row per source record in MOABB, with paradigm, people, channels and sampling rate as MOABB lists them. Records this site already lists are merged into its rows.',
    zh: 'MOABB 中每个原始记录一行，范式、人数、通道数与采样率照 MOABB 所列。本站已列出的记录并入本站的条目。',
  },
  corpus: {
    en: 'Corpora that require a signed agreement, a request or a registration. Their terms are quoted from a captured copy of the source’s own page.',
    zh: '需要签署协议、提出申请或注册才能获取的语料。其条款引自来源页面本身的存档副本。',
  },
  site_model: {
    en: 'Models and methods with results on this site; each links its page.',
    zh: '在本站有结果的模型与方法；每一行都链接到它的页面。',
  },
  model: {
    en: 'Other models and papers we track, each at the furthest step checked; a row that is held says why.',
    zh: '我们关注的其他模型与论文，各在核验到的最远一步；暂缓的行写明原因。',
  },
};

/** Who states a row's terms (the file's `vocab.by`). */
const byLabel: Record<string, T> = {
  hf_licence_tag: { en: 'Hugging Face licence tag', zh: 'Hugging Face 许可标签' },
  moabb_catalog: { en: 'as MOABB lists it', zh: 'MOABB 目录所列' },
  deposit_record: { en: 'the deposit’s record', zh: '存档记录' },
  a4_capture: { en: 'the source’s terms page', zh: '来源的条款页面' },
  zenodo_record: { en: 'the Zenodo record', zh: 'Zenodo 记录' },
  host_record: { en: 'the host’s record', zh: '托管方记录' },
  repository_licence_file: { en: 'the repository’s licence file', zh: '仓库的许可文件' },
  model_card_metadata: { en: 'the model card’s metadata', zh: '模型卡片元数据' },
  dataset_card: { en: 'the dataset card', zh: '数据卡片' },
  paper: { en: 'the paper', zh: '论文' },
  project_page: { en: 'the project page', zh: '项目页面' },
  site_release: { en: 'this site’s rights record', zh: '本站的权利记录' },
  none: { en: '', zh: '' },
};
/** How a source is reached (the file's `vocab.access`); printed where it is more than plain open access. */
const accessLabel: Record<string, T> = {
  open: { en: 'open', zh: '公开' },
  gated: { en: 'gated', zh: '需申请访问' },
  signed_agreement: { en: 'signed agreement', zh: '需签署协议' },
  request_based: { en: 'on request', zh: '需提出申请' },
  registration: { en: 'registration', zh: '需注册' },
  catalog_only: { en: 'catalog entry', zh: '仅目录条目' },
  unknown: { en: 'unknown', zh: '未知' },
};
/** A model row's terms for one part (the file's `vocab.terms_state`). */
const partState: Record<string, T> = {
  stated: { en: '', zh: '' },
  not_found: { en: 'not found', zh: '未找到' },
  per_source: { en: 'per source', zh: '按各来源' },
  not_applicable: { en: 'not applicable', zh: '不适用' },
  application_required: { en: 'on application', zh: '需申请' },
};
const partName: Record<'code' | 'weights' | 'data', T> = {
  code: { en: 'Code', zh: '代码' }, weights: { en: 'Weights', zh: '权重' }, data: { en: 'Data', zh: '数据' },
};
const modelKindLabel: Record<string, T> = {
  foundation_model: { en: 'Foundation model', zh: '基础模型' },
  spatial_aggregation_model: { en: 'Spatial aggregation model', zh: '空间聚合模型' },
  generative_model: { en: 'Generative model', zh: '生成模型' },
  decoding_model: { en: 'Decoding model', zh: '解码模型' },
  adaptation_method: { en: 'Adaptation method', zh: '适配方法' },
  classical_method: { en: 'Classical method', zh: '经典方法' },
  trained_from_scratch: { en: 'Trained from scratch', zh: '从头训练' },
};
const signalLabel: Record<string, T> = {
  human_scalp_eeg: { en: 'human scalp EEG', zh: '人类头皮 EEG' },
  human_ieeg: { en: 'human iEEG', zh: '人类颅内 EEG' },
  human_fmri: { en: 'human fMRI', zh: '人类 fMRI' },
  human_meg: { en: 'human MEG', zh: '人类 MEG' },
  mouse_calcium_imaging: { en: 'mouse calcium imaging', zh: '小鼠钙成像' },
  mouse_spiking: { en: 'mouse spiking', zh: '小鼠神经元放电' },
  ecg: { en: 'ECG', zh: 'ECG' }, ppg: { en: 'PPG', zh: 'PPG' }, emg: { en: 'EMG', zh: 'EMG' },
};
/** What a matches_metadata_of finding's fields name (register_findings.py METADATA_FIELDS). */
const fieldLabel: Record<string, T> = {
  file_names: { en: 'file names', zh: '文件名' },
  byte_counts: { en: 'byte counts', zh: '字节数' },
  file_count: { en: 'file count', zh: '文件数' },
  archive_names: { en: 'archive names', zh: '压缩包名' },
  dataset_name: { en: 'dataset name', zh: '数据集名称' },
  participant_count: { en: 'participant count', zh: '被试人数' },
  channel_count: { en: 'channel count', zh: '通道数' },
  sampling_rate: { en: 'sampling rate', zh: '采样率' },
  folder_names: { en: 'folder names', zh: '文件夹名' },
  card_names_source: { en: 'the source its card names', zh: '数据卡片写明的来源' },
  label_names: { en: 'label names', zh: '标签名' },
  split_names: { en: 'split names', zh: '数据划分名' },
  example_counts: { en: 'example counts', zh: '样本数' },
  column_names: { en: 'column names', zh: '列名' },
  file_hashes: { en: 'file hashes', zh: '文件哈希' },
  code_names_source: { en: 'the source its uploader’s code names', zh: '上传者代码写明的来源' },
};
/** Hold reasons, for both ladders (register_findings.py HOLD_REASONS): codes, never ids. */
const holdReason: Record<string, T> = {
  released_ids_duplicated: { en: 'Held: released IDs include duplicated or reprocessed recordings; group-level deduplication is pending.',
                             zh: '暂缓：发布的编号中有重复或重新处理过的记录，按组去重尚未完成。' },
  targets_stored_with_outputs: { en: 'Held: intended targets must be separated from the classifier outputs stored with them.',
                                 zh: '暂缓：预期目标需要与一同存储的分类器输出分开。' },
  deposits_differ: { en: 'Held: two deposits differ in people, sessions and licence; the version is not fixed yet.',
                     zh: '暂缓：两份存档在人数、会话与许可上不一致，版本尚未确定。' },
  onset_timing_unresolved: { en: 'Held: onset timing and block structure are unresolved.', zh: '暂缓：刺激起始时间与组块结构尚未弄清。' },
  release_family_unchecked: { en: 'Held: three releases form one family; selection and filter differences are unchecked.',
                              zh: '暂缓：三个发布版本属于同一系列，筛选与滤波上的差异尚未核对。' },
  one_offline_session: { en: 'Held: MOABB loads one offline session, and the clinical group has two participants.',
                         zh: '暂缓：MOABB 只载入一次离线会话，临床组只有两名被试。' },
  weights_licence_not_found: { en: 'Held: no licence found for the weights.', zh: '暂缓：没有找到权重的许可。' },
  code_licence_not_found: { en: 'Held: no licence found for the code.', zh: '暂缓：没有找到代码的许可。' },
  no_released_checkpoint: { en: 'Held: no checkpoint is released.', zh: '暂缓：没有公开的检查点。' },
  code_not_reachable: { en: 'Held: the code repository could not be reached.', zh: '暂缓：代码仓库无法访问。' },
  not_human_scalp_eeg: { en: 'Held: trained on signals other than human scalp EEG.', zh: '暂缓：训练所用的信号不是人类头皮 EEG。' },
  noncommercial_noderivs_weights: { en: 'Held: the weights’ licence is non-commercial with no derivatives.',
                                    zh: '暂缓：权重许可为非商业使用、禁止演绎。' },
  acceptance_not_verified: { en: 'Held: publication is not yet confirmed from an official record.', zh: '暂缓：尚未从官方记录确认已发表。' },
  data_not_public: { en: 'Held: the training data are not public.', zh: '暂缓：训练数据未公开。' },
  converted_run_timing: { en: 'Held: in one converted run, some fixation times fall outside the recording.',
                          zh: '暂缓：在一个转换后记录中，有些注视时间落在记录之外。' },
  one_person_score: { en: 'Held: with one person, every score is that person’s.', zh: '暂缓：只有一个人时，任何分数都是这个人的分数。' },
};
/** policy_note findings, by source. */
const policyNote: Record<string, T> = {
  lfame: { en: 'Listed because the register records what was checked; it has no model result on this site.',
           zh: '列在这里，是因为登记册记录核验过什么；本站没有它的模型结果。' },
};
/** The rule that keeps a row at its step (`level_cap.rule`), linked to the rules under #levels. */
const capLabel: Record<string, T> = {
  reuploads_stay_at_step_1: { en: 'Stays at step 1 under the re-upload rule', zh: '按转传规则停留在第 1 步' },
  gated_stays_at_step_1: { en: 'Stays at step 1 under the access rule', zh: '按访问规则停留在第 1 步' },
};
/** The data-quality page's cases a catalog_differs_from_files finding may name. */
const dataQualityCase: Record<string, string> = { shin2022: '/topics/data-quality/#shin2022', eldbeta: '/topics/data-quality/#eldbeta', zuco2: '/topics/data-quality/#zuco2' };
/** The cases whose finding must carry MOABB's catalog counts. */
const catalogCountsRequired = new Set(['shin2022']);

/** Words the table prints around the file's values. */
export const ui = {
  en: {
    eyebrow: 'Open register',
    status: 'Status: ',
    gapAt: (step: number, item: string) => `gap at step ${step}: ${item}`,
    notComputed: (item: string) => `${item}: not computed`,
    noTag: 'none',
    termsNone: 'None recorded',
    moabbNoLicence: 'Licence not yet read from the host',
    files: (n: number): Part[] => [' · ', { n }, n === 1 ? ' file' : ' files'],
    bytes: (n: number): Part[] => [' · ', { n }, ' bytes'],
    bytesInAll: (n: number): Part[] => [' · ', { n }, ' bytes in all'],
    revision: (sha: string): Part[] => [' · revision ', { c: sha.slice(0, 7) }],
    alias: { name: 'Also', moabb_loader: 'MOABB', doi: 'DOI', hf_repo: 'Hugging Face', eegdash_mirror: 'EEGDash',
             official_weights: 'Official weights', weights_copy: 'Weights copies' } as Record<string, string>,
    loader: (f: LoaderFields): Part[] => [
      ...(f.paradigm ? [{ en: f.paradigm }] : ['—']),
      ...(f.people !== null ? [' · ', { n: f.people }, f.people === 1 ? ' person' : ' people'] : []),
      ...(f.channels !== null ? [' · ', { n: f.channels }, f.channels === 1 ? ' channel' : ' channels'] : []),
      ...(f.sampling_rate_hz !== null ? [' · ', { n: f.sampling_rate_hz }, ' Hz'] : []),
    ] as Part[],
    asMoabb: 'as MOABB lists it',
    sitePage: 'as this site’s page states it',
    quoted: (date: string, archived: boolean) => `quoted from ${archived ? 'an archived copy of the source’s page' : 'the source’s page'}, captured ${date}`,
    sha: 'SHA-256 ',
    access: 'Access: ',
    recordNote: (n: RecordNote) =>
      `${n.record}${n.latest_version ? ', the latest version under concept DOI ' : ', under concept DOI '}${n.concept_doi}; licence identifier on Zenodo: “${n.licence_identifier}”`,
    page: 'On this site →',
    caseLink: 'The case →',
    cases: 'Its results on this site:',
    exposure: 'Named in a pretraining corpus? →',
    parent: 'Part of ',
    correct: registerCopy.en.correct,
    venue: (v: Venue, date: string): Part[] => [v.url ? { a: v.url, t: `${v.value} paper`, ext: true } : `${v.value} paper`, ` · status checked ${date}`],
    exposureField: (v: string) => `Pretraining exposure: ${v}`,
    exposureValue: { unknown: 'unknown' } as Record<string, string>,
    modelLinks: { paper: 'Paper', code: 'Code', weights: 'Weights', data: 'Data' } as Record<string, string>,
    sourceAgain: 'That source',
    filter: { legend: 'Show only', group: 'Group', step: 'Step', terms: 'Terms', all: 'All', stated: 'Terms stated', unstated: 'No terms stated',
              gap: 'Rows with a gap', reset: 'Show every row', empty: 'No row matches these choices.' },
  },
  zh: {
    eyebrow: '开放登记册',
    status: '状态：',
    gapAt: (step: number, item: string) => `第 ${step} 步缺：${item}`,
    notComputed: (item: string) => `${item}：尚未计算`,
    noTag: '无',
    termsNone: '未记录',
    moabbNoLicence: '尚未从托管方读取许可',
    files: (n: number): Part[] => [' · ', { n }, ' 个文件'],
    bytes: (n: number): Part[] => [' · ', { n }, ' 字节'],
    bytesInAll: (n: number): Part[] => [' · 共 ', { n }, ' 字节'],
    revision: (sha: string): Part[] => [' · 版本 ', { c: sha.slice(0, 7) }],
    alias: { name: '又名', moabb_loader: 'MOABB', doi: 'DOI', hf_repo: 'Hugging Face', eegdash_mirror: 'EEGDash',
             official_weights: '官方权重', weights_copy: '权重副本' } as Record<string, string>,
    loader: (f: LoaderFields): Part[] => [
      ...(f.paradigm ? [{ en: f.paradigm }] : ['—']),
      ...(f.people !== null ? [' · ', { n: f.people }, ' 人'] : []),
      ...(f.channels !== null ? [' · ', { n: f.channels }, ' 个通道'] : []),
      ...(f.sampling_rate_hz !== null ? [' · ', { n: f.sampling_rate_hz }, ' Hz'] : []),
    ] as Part[],
    asMoabb: 'MOABB 目录所列',
    sitePage: '本站页面所写',
    quoted: (date: string, archived: boolean) => `引自${archived ? '来源页面的历史存档' : '来源页面'}，存档于 ${date}`,
    sha: 'SHA-256 ',
    access: '获取方式：',
    recordNote: (n: RecordNote) =>
      `${n.record.replace(/^Zenodo record /, 'Zenodo 记录 ')}${n.latest_version ? '，是概念 DOI ' : '，概念 DOI 为 '}${n.concept_doi}${n.latest_version ? ' 下的最新版本' : ''}；Zenodo 上的许可标识为“${n.licence_identifier}”`,
    page: '本站页面 →',
    caseLink: '案例 →',
    cases: '它在本站的结果：',
    exposure: '是否出现在预训练数据中？→',
    parent: '属于 ',
    correct: registerCopy.zh.correct,
    venue: (v: Venue, date: string): Part[] => [v.url ? { a: v.url, t: `${v.value} 论文`, ext: true } : `${v.value} 论文`, ` · 状态于 ${date}核对`],
    exposureField: (v: string) => `是否出现在预训练数据中：${v}`,
    exposureValue: { unknown: '未知' } as Record<string, string>,
    modelLinks: { paper: '论文', code: '代码', weights: '权重', data: '数据' } as Record<string, string>,
    sourceAgain: '该来源',
    filter: { legend: '只显示', group: '分组', step: '步骤', terms: '条款', all: '全部', stated: '有所述条款', unstated: '没有所述条款',
              gap: '有缺口的行', reset: '显示全部行', empty: '没有符合这些条件的行。' },
  },
} satisfies Record<Locale, unknown>;

/* --- Rich text: a cell is built as parts and printed as escaped HTML ---------------------------------------- */

/**
 * A run of text: a string; a figure `{ n }` (a value of the register file, printed with data-fig as Fig.astro prints
 * one); a link `{ a, t }` (`ext` for another site; on a Chinese page a link whose text has no Chinese is marked
 * lang="en"); `{ c }` code; `{ en }` English text, marked lang="en" on a Chinese page.
 */
export type Part = string | { n: number; fmt?: Fmt } | { a: string; t: string; ext?: boolean } | { c: string } | { en: string };
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const hasChinese = (s: string) => /[　-鿿＀-￯]/.test(s);
/** A register figure: a value of the register file, printed in its format. */
export const regFig = (raw: number, fmt: Fmt = 'count'): Fig => {
  need(typeof raw === 'number' && Number.isFinite(raw), `a figure that is not a number (${raw})`);
  return { raw, fmt, src: REGISTER_FILE };
};
const figHtml = (f: Fig) => `<span data-fig="${f.src}|${f.fmt}|${f.raw}" class="num">${esc(formatFig(f))}</span>`;
export function html(parts: Part[], locale: Locale): string {
  const zh = locale === 'zh';
  return parts.map(p => {
    if (typeof p === 'string') return esc(p);
    if ('n' in p) return figHtml(regFig(p.n, p.fmt));
    if ('a' in p) {
      const lang = zh && !hasChinese(p.t) ? ' lang="en"' : '';
      return `<a href="${esc(safeHref(p.a))}"${p.ext ? ' target="_blank" rel="noreferrer"' : ''}${lang}>${esc(p.t)}${p.ext ? ' ↗' : ''}</a>`;
    }
    if ('c' in p) return `<code>${esc(p.c)}</code>`;
    return zh ? `<span lang="en">${esc(p.en)}</span>` : esc(p.en);
  }).join('');
}
const join = (xs: Part[][], sep: Part[]): Part[] => xs.flatMap((x, i) => (i ? [...sep, ...x] : x));
/** Whether a part begins (or ends) with Latin text or a figure, which Chinese sets off with a space. */
function latinEdge(p: Part | undefined, side: 'start' | 'end'): boolean {
  if (p === undefined) return false;
  const edge = (t: string) => { const ch = side === 'start' ? t.trimStart()[0] : t.trimEnd().slice(-1); return !!ch && !hasChinese(ch); };
  if (typeof p === 'string') return edge(p);
  if ('a' in p) return edge(p.t);
  return true;
}
/** "a, b and c" / "a、b和c": in Chinese, 和 takes a space only beside a Latin name or a figure ("LaBraM 和 REVE"). */
const listed = (xs: Part[][], locale: Locale): Part[] => {
  if (xs.length <= 1) return xs[0] ?? [];
  const head = join(xs.slice(0, -1), [locale === 'zh' ? '、' : ', ']), last = xs[xs.length - 1];
  const and = locale === 'zh'
    ? `${latinEdge(head[head.length - 1], 'end') ? ' ' : ''}和${latinEdge(last[0], 'start') ? ' ' : ''}`
    : (xs.length > 2 ? ', and ' : ' and ');
  return [...head, and, ...last];
};

/* --- Links: never a user name, never a page that is not built ------------------------------------------------ */

/** Every Hugging Face namespace the register names: uploaders, repositories, mirrors and weights. */
export const registerNamespaces = new Set<string>();
if (register) for (const e of register.entries) {
  if (e.hf) registerNamespaces.add(e.hf.repo.split('/')[0].toLowerCase());
  if (e.family) registerNamespaces.add(e.family.uploader.toLowerCase());
  for (const a of e.aliases) if (/\//.test(a.value) && ['hf_repo', 'eegdash_mirror', 'official_weights', 'weights_copy'].includes(a.kind))
    registerNamespaces.add(a.value.split('/')[0].toLowerCase());
}
const onHf = (url: string) => /(^|\.)huggingface\.co$/.test(new URL(url).hostname);
/** Whether a Hugging Face search would search for a name the register knows as a user's or an organisation's. */
const searchesNamespace = (u: URL) => {
  const q = (u.searchParams.get('search') ?? '').toLowerCase();
  return !q || [...registerNamespaces].some(ns => q === ns || q.startsWith(`${ns}/`));
};
/** A link the register prints. A Hugging Face link is a search, and never a search for a user name. */
function safeHref(href: string): string {
  if (href.startsWith('mailto:') || href.startsWith('#') || href.startsWith('/')) return href;
  const u = new URL(href);
  need(u.protocol === 'https:' || u.protocol === 'http:', `${href}: not a web address`);
  if (onHf(href)) {
    need(/^\/(?:datasets|models)$/.test(u.pathname) && [...u.searchParams.keys()].join() === 'search', `${href}: a Hugging Face link other than a search`);
    need(!searchesNamespace(u), `${href}: a search for a user name`);
  }
  return href;
}
/**
 * A host address as the register links it: a Hugging Face repository page becomes a search for the repository's own
 * name (its user name stays in the row's text), and none at all where that name is also a namespace (a repository
 * named after its organisation); anything else is kept as the file gives it.
 */
export function hostHref(url: string | undefined | null): string | null {
  if (!url) return null;
  if (!onHf(url)) return safeHref(url);
  const u = new URL(url);
  const m = u.pathname.match(/^\/(datasets\/)?([^/]+)\/([^/]+)/);
  const search = m && m[2] !== 'datasets' && m[2] !== 'models'
    ? new URL(`https://huggingface.co/${m[1] ? 'datasets' : 'models'}?search=${encodeURIComponent(m[3])}`) : u;
  return searchesNamespace(search) ? null : safeHref(search.href);
}

/** Pages this site builds, for checking every internal link a row carries. */
const builtPages = new Set<string>([
  ...entityPaths, ...(translatedPaths as readonly string[]), ...topicPages.map(t => `/topics/${t.slug}/`),
  ...mvp.tracks.map(t => `/protocols/${t.id}/`),
]);
/** Dataset pages a pilot switch removes while that source is held: its row keeps its place, without the page link. */
const heldPages = new Set<string>([...(bingoReleased ? [] : [`/datasets/${BINGO_DATASET}/`]), ...(handwritingReleased ? [] : [`/datasets/${HANDWRITING_DATASET}/`])]);
/** An internal link a row carries, localised; it must be a page this site builds. */
function sitePath(path: string, locale: Locale, what: string): string {
  need(builtPages.has(path.split('#')[0]), `${what}: ${path} is not a page this site builds`);
  return hrefFor(path, locale);
}
/**
 * A core dataset's pretraining-exposure section: the link its row gives, when that is a page this site builds, else
 * the #pretraining-exposure section of the core protocol page the dataset is scored on.
 */
function exposureHref(e: RegisterEntry, locale: Locale): string | null {
  const given = e.links.exposure;
  if (!given) return null;
  if (builtPages.has(given.split('#')[0])) return hrefFor(given, locale);
  const entity = datasetEntities.find(d => `/datasets/${d.slug}/` === e.links.page);
  const track = entity && mvp.tracks.find(t => t.dataset === entity.name);
  need(track, `${e.id}: no core protocol page for its pretraining-exposure link`);
  return hrefFor(`/protocols/${track!.id}/#pretraining-exposure`, locale);
}

/* --- Findings ------------------------------------------------------------------------------------------------- */

const byId = new Map<string, RegisterEntry>();
const captures = new Map<string, Capture>();
const familyOf = new Map<string, Family>();
if (register) {
  for (const e of register.entries) { need(!byId.has(e.id), `${e.id} twice`); byId.set(e.id, e); }
  for (const c of register.sources.access_terms) captures.set(c.capture_id, c);
  for (const f of register.families) familyOf.set(f.id, f);
}

/** `again`: the source was just named by the match sentence before it, in the same list item. */
interface Ctx { locale: Locale; row: RegisterEntry; again?: boolean }
/** A link to another row: on this page when it is on this ladder, else on the other register page. */
function rowLink(id: string, x: Ctx): Part {
  const r = byId.get(id);
  need(r, `${x.row.id}: names a row ${id} the file does not hold`);
  return { a: r!.ladder === x.row.ladder ? `#${id}` : hrefFor(`${r!.ladder === 'dataset' ? '/datasets/register/' : '/methods/register/'}#${id}`, x.locale), t: r!.name };
}
/** The captured terms page a comparison rests on. */
function captureOf(p: Record<string, unknown>, x: Ctx): Capture {
  const c = captures.get(String(p.capture_id));
  need(c, `${x.row.id}: a finding on a capture the file does not list (${p.capture_id})`);
  if (p.source !== undefined) need(c!.family_slug === p.source, `${x.row.id}: ${p.capture_id} is not a capture of ${p.source}`);
  return c!;
}
/** The source a comparison names: its register row where the file gives one, else the captured family's name. */
const sourceName = (p: Record<string, unknown>, x: Ctx): Part =>
  x.again ? ui[x.locale].sourceAgain : p.row ? rowLink(String(p.row), x) : { en: captureOf(p, x).family };
/** "(terms page captured 19 October 2026)", linked unless the captured page is a Hugging Face repository's. */
function captureNote(c: Capture, x: Ctx): Part[] {
  const date = longDate(c.captured_at, x.locale);
  const label = x.locale === 'zh' ? `条款页面于 ${date}存档` : `terms page captured ${date}`;
  const ref: Part = onHf(c.url) ? label : { a: c.url, t: label, ext: true };
  return x.locale === 'zh' ? ['（', ref, '）'] : [' (', ref, ')'];
}
/** A record's label in Chinese: "Zenodo record 2605110" reads "Zenodo 记录 2605110"; any other label stays as given. */
const zhRecord = (label: string): Part => (/^Zenodo record \d+$/.test(label) ? label.replace('Zenodo record ', 'Zenodo 记录 ') : { en: label });
const tokens = (v: unknown): Part[][] => String(v).split('+').map(t => [{ c: t }]);
const int = (p: Record<string, unknown>, k: string) => { const v = p[k]; need(Number.isInteger(v), `a finding's ${k} is not a count`); return v as number; };
/** "1 of 737 members carries", "2 of 2 members are": the noun's number follows `of`, the verb's `n`. */
const members = (p: Record<string, unknown>) => (int(p, 'of') === 1 ? ' member' : ' members');
/** A catalog_differs_from_files finding's case, checked, and MOABB's catalog counts when it carries them (both or neither). */
function catalogCounts(p: Record<string, unknown>, x: Ctx): { trials: number; runs: number } | null {
  need(dataQualityCase[String(p.case)], `${x.row.id}: no data-quality case ${p.case}`);
  const has = ['catalog_trials', 'catalog_runs'].filter(k => k in p).length;
  need(has !== 1, `${x.row.id}: MOABB's catalog trials and runs come together`);
  need(has === 2 || !catalogCountsRequired.has(String(p.case)), `${x.row.id}: the ${p.case} case needs MOABB's catalog trials and runs`);
  return has === 2 ? { trials: int(p, 'catalog_trials'), runs: int(p, 'catalog_runs') } : null;
}

type Template = Record<Locale, (p: Record<string, unknown>, x: Ctx) => Part[]>;
/** Every finding code's words, English and Chinese. A figure prints in the same order in both. */
const templates: Record<string, Template> = {
  licence_tag_absent: {
    en: () => ['No licence tag on its Hugging Face listing.'],
    zh: () => ['Hugging Face 列表上没有许可标签。'],
  },
  licence_tag_absent_members: {
    en: p => [{ n: int(p, 'n') }, ' of ', { n: int(p, 'of') }, members(p), int(p, 'n') === 1 ? ' carries no licence tag.' : ' carry no licence tag.'],
    zh: p => ['其中 ', { n: int(p, 'n') }, ' 个成员没有许可标签（共 ', { n: int(p, 'of') }, ' 个）。'],
  },
  gated: {
    en: p => [p.mode === 'manual' ? 'Gated on Hugging Face: the uploader approves each request.'
      : 'Gated on Hugging Face: access is granted automatically once a user accepts the conditions.'],
    zh: p => [p.mode === 'manual' ? '在 Hugging Face 上需申请访问，由上传者逐一审批。' : '在 Hugging Face 上需申请访问，用户同意条件后自动获准。'],
  },
  gated_members: {
    en: p => [{ n: int(p, 'n') }, ' of ', { n: int(p, 'of') }, members(p), int(p, 'n') === 1 ? ' is gated.' : ' are gated.'],
    zh: p => ['其中 ', { n: int(p, 'n') }, ' 个成员需申请访问（共 ', { n: int(p, 'of') }, ' 个）。'],
  },
  family: {
    en: p => [{ n: int(p, 'n') }, int(p, 'n') === 1 ? ' repository by ' : ' repositories by ', { en: String(p.uploader) },
              ' in the series “', { en: String(p.series) }, '”, listed as one row.'],
    zh: p => [{ en: String(p.uploader) }, ' 名下“', { en: String(p.series) }, '”系列的 ', { n: int(p, 'n') }, ' 个仓库，合为一行。'],
  },
  derived_from: {
    en: (p, x) => ['Its card names ', rowLink(String(p.row), x), ' as its source.'],
    zh: (p, x) => ['其数据卡片写明来源是 ', rowLink(String(p.row), x), '。'],
  },
  matches_metadata_of: {
    en: (p, x) => ['Matches ', sourceName(p, x), ' in ', ...listed((p.fields as string[]).map(f => [fieldLabel[f].en]), 'en'), '.'],
    zh: (p, x) => ['在', ...listed((p.fields as string[]).map(f => [fieldLabel[f].zh]), 'zh'), '上与 ', sourceName(p, x), ' 一致', '。'],
  },
  terms_differ: {
    en: (p, x) => {
      const src = sourceName(p, x);
      const declared: Part[] = p.declared_by === 'dataset_card' ? ['its card gives ', ...listed(tokens(p.declared), 'en'), ' for this source']
        : p.declared === 'none' ? ['this upload has no licence tag'] : ['this upload’s licence tag is ', ...listed(tokens(p.declared), 'en')];
      const original: Part[] = p.original === 'signed_agreement' ? [src, ' is released under a signed agreement']
        : p.original === 'request_based' ? [src, ' is available on request']
        : p.original === 'registration' ? [src, ' requires registration']
        : [src, '’s terms page gives ', { c: String(p.original) }];
      return [...original, '; ', ...declared, ...captureNote(captureOf(p, x), x), '.'];
    },
    zh: (p, x) => {
      const src = sourceName(p, x);
      const declared: Part[] = p.declared_by === 'dataset_card' ? ['其数据卡片对这一来源写的是 ', ...listed(tokens(p.declared), 'zh')]
        : p.declared === 'none' ? ['本上传没有许可标签'] : ['本上传的许可标签是 ', ...listed(tokens(p.declared), 'zh')];
      // A space after an English name, none after 该来源.
      const sp = x.again ? '' : ' ';
      const original: Part[] = p.original === 'signed_agreement' ? [src, `${sp}须签署协议才能获取`]
        : p.original === 'request_based' ? [src, `${sp}须提出申请才能获取`]
        : p.original === 'registration' ? [src, `${sp}须注册才能获取`]
        : [src, `${sp}的条款页面给出的许可是 `, { c: String(p.original) }];
      return [...original, ...captureNote(captureOf(p, x), x), '；', ...declared, '。'];
    },
  },
  // MOABB's catalog counts as the catalog lists them (catalog_trials, catalog_runs), when the finding carries them;
  // Shin2022's must (plan §2.3: the 2,640 trials and 11 runs MOABB lists are findings on its row).
  catalog_differs_from_files: {
    en: (p, x) => { const c = catalogCounts(p, x);
      return [...(c ? ['MOABB’s catalog lists ', { n: c.trials }, ' trials and ', { n: c.runs }, ' runs for it, which differ from what its files hold']
                    : ['MOABB’s catalog figures for it differ from what its files hold']),
              ': see ', { a: sitePath(dataQualityCase[String(p.case)], x.locale, x.row.id), t: 'the case on the data-quality page' }, '.']; },
    zh: (p, x) => { const c = catalogCounts(p, x);
      return [...(c ? ['MOABB 目录为它列出 ', { n: c.trials }, ' 个试次、', { n: c.runs }, ' 个 run，与其文件内容不一致']
                    : ['MOABB 目录中关于它的数字与其文件内容不一致']),
              '：见', { a: sitePath(dataQualityCase[String(p.case)], x.locale, x.row.id), t: '数据质量页面上的案例' }, '。']; },
  },
  version_clarification: {
    en: p => ['The scores here use ', { en: String(p.current) }, ', which holds ', { n: int(p, 'recordings_source') }, ' recordings; ',
              { n: int(p, 'recordings_evaluated') }, ' are scored. An earlier inventory named the source as ', { en: String(p.earlier) }, '.'],
    zh: p => ['本站的分数使用 ', zhRecord(String(p.current)), '，其中有 ', { n: int(p, 'recordings_source') }, ' 份记录，计分的是 ',
              { n: int(p, 'recordings_evaluated') }, ' 份。早先的清单把来源记为 ', zhRecord(String(p.earlier)), '。'],
  },
  named_in_corpus: {
    en: p => { const m = p.models as string[]; const one = m.length === 1;
      return [...listed(m.map(x => [{ en: x }]), 'en'), one ? ' lists it in its pretraining corpus' : ' list it in their pretraining corpus',
              p.release_resolved ? '.' : `; which release of it ${one ? 'it' : 'they'} used is not established.`]; },
    zh: p => { const m = p.models as string[];
      return [...listed(m.map(x => [{ en: x }]), 'zh'), ' 的预训练语料中列有这个数据集', p.release_resolved ? '。' : '；用的是它的哪个版本尚未确定。']; },
  },
  hold: {
    en: p => { need(holdReason[String(p.reason_code)], `no words for the hold ${p.reason_code}`); return [holdReason[String(p.reason_code)].en]; },
    zh: p => { need(holdReason[String(p.reason_code)], `no words for the hold ${p.reason_code}`); return [holdReason[String(p.reason_code)].zh]; },
  },
  planned: {
    en: () => ['Planned for a fixed-protocol run here.'],
    zh: () => ['计划在本站按固定协议运行。'],
  },
  policy_note: {
    en: (p, x) => { need(policyNote[String(p.source)], `${x.row.id}: no words for the policy note ${p.source}`); return [policyNote[String(p.source)].en]; },
    zh: (p, x) => { need(policyNote[String(p.source)], `${x.row.id}: no words for the policy note ${p.source}`); return [policyNote[String(p.source)].zh]; },
  },
  merged_rows: {
    en: p => ['Merges ', { n: int(p, 'n') }, int(p, 'n') === 1 ? ' row from another group.' : ' rows from other groups.'],
    zh: p => ['合并了其他分组的 ', { n: int(p, 'n') }, ' 行。'],
  },
};
/** The finding codes the page has words for (the check module reads this list). */
export const findingCodes = Object.keys(templates);

const COMPARISON = new Set(['matches_metadata_of', 'terms_differ']);
/**
 * A row's findings as list items, in the file's order. The comparison findings on one captured source (its metadata
 * match and its terms) are one item, so the source is named once and its captured page cited once.
 */
function findingItems(e: RegisterEntry, locale: Locale): Part[][] {
  const x: Ctx = { locale, row: e };
  const items: Part[][] = [];
  const slots = new Map<string, { at: number; match?: Finding; terms?: Finding }>();
  for (const f of e.findings) {
    if (!COMPARISON.has(f.code)) { items.push(templates[f.code][locale](f.params, x)); continue; }
    const key = String(f.params.capture_id);
    let slot = slots.get(key);
    if (!slot) { slot = { at: items.length }; slots.set(key, slot); items.push([]); }
    need(!(f.code === 'terms_differ' ? slot.terms : slot.match), `${e.id}: two ${f.code} findings on ${key}`);
    if (f.code === 'terms_differ') slot.terms = f; else slot.match = f;
  }
  for (const slot of slots.values()) {
    const parts: Part[] = [];
    if (slot.match) {
      const m = templates.matches_metadata_of[locale](slot.match.params, x);
      // A match with no terms finding on the same source still cites the captured page it rests on.
      parts.push(...(slot.terms ? m : [...m.slice(0, -1), ...captureNote(captureOf(slot.match.params, x), x), m[m.length - 1]]));
    }
    if (slot.terms) parts.push(...(slot.match ? [locale === 'zh' ? '' : ' '] : []),
                               ...templates.terms_differ[locale](slot.terms.params, { ...x, again: !!slot.match }));
    items[slot.at] = parts;
  }
  return items;
}

/* --- The file, checked against the words here ---------------------------------------------------------------- */

if (register) {
  const R = register;
  need(R.release_id === openRegister.release, `${REGISTER_FILE} names the release ${R.release_id}, not ${openRegister.release}`);
  need(R.schema_version === 'bci-report-open-register-v1', `${REGISTER_FILE}: an unknown schema ${R.schema_version}`);
  // The step names and what each step needs: the file's and i18n.ts's, word for word, in both languages. #levels prints
  // the file's own words (`ladderSteps`). While the file is provisional its Chinese for what a step needs may still
  // differ from i18n.ts (the freeze aligns it); once it is final, a difference stops the build.
  const final = R.status !== 'provisional';
  for (const [ladder, steps] of [['dataset', datasetLadder], ['model', modelLadder]] as const) {
    need(Object.keys(R.level_definitions[ladder]).join() === '1,2,3,4,5', `${ladder}: five steps`);
    for (const s of steps) {
      const def = R.level_definitions[ladder][String(s.step)];
      need(def.en === s.name.en && def.zh === s.name.zh && def.needs_en === s.needs.en,
        `${ladder} step ${s.step}: the file says ${def.en}/${def.zh} (“${def.needs_en}”), i18n.ts ${s.name.en}/${s.name.zh} (“${s.needs.en}”)`);
      need(!final || def.needs_zh === s.needs.zh,
        `${ladder} step ${s.step}: the final file says “${def.needs_zh}” for what the step needs, i18n.ts “${s.needs.zh}”`);
    }
  }
  // The rules the dataset register states once (i18n.ts registerCopy.rules) are the file's, in both languages.
  need(R.rules.map(r => r.en).join('\n') === registerCopy.en.rules.join('\n'), 'the rules printed are not the file’s rules');
  need(R.rules.map(r => r.zh).join('\n') === registerCopy.zh.rules.join('\n'), 'the Chinese rules printed are not the file’s rules');
  // Words for every code, reason, field and vocabulary word the file declares.
  for (const code of Object.keys(R.finding_codes)) need(templates[code], `no words for the finding code ${code}`);
  for (const r of R.finding_codes.hold?.reason_codes ?? []) need(holdReason[r], `no words for the hold reason ${r}`);
  for (const f of R.finding_codes.matches_metadata_of?.fields ?? []) need(fieldLabel[f], `no words for the metadata field ${f}`);
  for (const b of R.vocab.by) need(byLabel[b], `no words for the terms source ${b}`);
  for (const a of R.vocab.access) need(accessLabel[a], `no words for the access kind ${a}`);
  for (const s of R.vocab.status) need(registerCopy.en.status[s] && registerCopy.zh.status[s], `no words for the status ${s}`);
  for (const s of R.vocab.terms_state) need(partState[s], `no words for the terms state ${s}`);
  for (const s of R.vocab.signal) need(signalLabel[s], `no words for the signal ${s}`);
  for (const k of R.vocab.model_kind) need(modelKindLabel[k], `no words for the model kind ${k}`);
  for (const e of R.entries) {
    need(/^r-(?:hf-\d{4}|moabb-\d{4}|corpus-[a-z0-9-]+|model-[a-z0-9-]+|site-[a-z0-9-]+)$/.test(e.id), `${e.id} is not an opaque row id`);
    need(e.correction.mailto === registerCorrectionHref(e.id), `${e.id}: its correction route is not a mail naming its id alone`);
    need(Number.isInteger(e.level) && e.level >= 1 && e.level <= 5, `${e.id}: step ${e.level}`);
    need(registerCopy.en.status[e.status], `${e.id}: the status ${e.status}`);
    for (const f of e.findings) need(templates[f.code], `${e.id}: no words for ${f.code}`);
    if (e.level_cap) need(capLabel[e.level_cap.rule] && e.level <= e.level_cap.step, `${e.id}: the cap ${e.level_cap.rule}`);
    for (const g of e.gaps) need(g.step <= e.level && R.item_definitions[e.ladder][g.item], `${e.id}: a gap at step ${g.step} (${g.item}) past its step ${e.level}`);
    need(byLabel[e.terms_as_stated.by], `${e.id}: terms stated by ${e.terms_as_stated.by}`);
  }
}

/* --- Rows ----------------------------------------------------------------------------------------------------- */

/** A cell: its main lines, then its notes (who states it, the host's facts, aliases), each a line of parts. */
interface Cell { main: Part[][]; notes: Part[][] }
/** A row's cells as escaped HTML, and the values the filter reads. */
export interface RowView {
  id: string; group: string; step: number; terms: boolean; gap: boolean;
  name: string; signal: string; termsCell: string; checked: string; found: string;
}

function aliasLine(e: RegisterEntry, locale: Locale): Part[] {
  const L = ui[locale];
  const kinds = ['name', 'moabb_loader', 'doi', 'hf_repo', 'eegdash_mirror', 'official_weights', 'weights_copy'];
  for (const a of e.aliases) need(kinds.includes(a.kind), `${e.id}: an alias of an unknown kind ${a.kind}`);
  const seen = new Set([e.name, e.hf?.repo]);
  const parts: Part[][] = [];
  for (const k of kinds) {
    const vs = [...new Set(e.aliases.filter(a => a.kind === k && !seen.has(a.value)).map(a => a.value))];
    if (vs.length) parts.push([`${L.alias[k]}${locale === 'zh' ? '：' : ': '}`, ...join(vs.map(v => [{ en: v }]), [locale === 'zh' ? '、' : ', '])]);
  }
  return join(parts, [' · ']);
}

/** Whether a row's terms are stated at all: a licence tag, a licence or captured terms, as its source gives them. */
function termsStated(e: RegisterEntry): boolean {
  if (e.ladder === 'model') return !!e.terms_by_part && Object.values(e.terms_by_part).some(t => t.state === 'stated');
  if (e.findings.some(f => f.code === 'licence_tag_absent')) return false;
  const f = familyOf.get(e.id);
  if (f) return Object.entries(f.licence_tag_counts).some(([k, n]) => k !== 'none' && n > 0);
  const v = e.terms_as_stated.value;
  return !!v && !/^no licen[cs]e/i.test(v);
}

function nameCell(e: RegisterEntry, locale: Locale): Cell {
  const L = ui[locale];
  const notes: Part[][] = [];
  const href = e.ladder === 'model'
    ? (e.links.page ? sitePath(e.links.page, locale, e.id) : null)
    : hostHref(e.urls.record ?? e.urls.search ?? e.family?.search_url ?? null);
  const main: Part[][] = [[href ? { a: href, t: e.name, ext: !href.startsWith('/') } : { en: e.name }]];
  if (e.hf) notes.push(['Hugging Face', ...(e.hf.files !== null ? L.files(e.hf.files) : []), ...(e.hf.size_bytes !== null ? L.bytes(e.hf.size_bytes) : []),
                        ...(e.hf.revision_sha ? L.revision(e.hf.revision_sha) : [])]);
  const fam = familyOf.get(e.id);
  if (fam) notes.push(['Hugging Face', ...(fam.size_bytes !== undefined ? L.bytesInAll(fam.size_bytes) : [])]);
  if (e.ladder === 'model') {
    if (e.venue) notes.push(L.venue(e.venue, longDate(e.venue.checked, locale)));
    // One link per address: a paper whose address is the venue's (linked just above) is not linked again.
    const links = (['paper', 'code', 'weights', 'data'] as const).map(k => [k, hostHref(e.urls[k])] as const).filter(([, h]) => h)
      .filter(([k]) => !(k === 'paper' && e.venue?.url && e.urls.paper === e.venue.url))
      .map(([k, h]) => [{ a: h!, t: L.modelLinks[k], ext: true }] as Part[]);
    if (links.length) notes.push(join(links, [' · ']));
  }
  const aliases = aliasLine(e, locale);
  if (aliases.length) notes.push(aliases);
  return { main, notes };
}

function signalCell(e: RegisterEntry, locale: Locale): Cell {
  const L = ui[locale];
  if (e.ladder === 'model') {
    const kind: Part[] = e.model_kind ? [modelKindLabel[e.model_kind][locale]] : [];
    const sig = (e.signal ?? []).map(s => [signalLabel[s][locale]] as Part[]);
    return { main: [kind.length || sig.length ? [...kind, ...(kind.length && sig.length ? [' · '] : []), ...listed(sig, locale)] : ['—']], notes: [] };
  }
  if (e.moabb) {
    const fs = e.moabb.fields_as_listed;
    return { main: fs.map(f => (fs.length > 1 ? [{ en: f.loader }, locale === 'zh' ? '：' : ': ', ...L.loader(f)] : L.loader(f))), notes: [[L.asMoabb]] };
  }
  const entity = e.links.page ? datasetEntities.find(d => `/datasets/${d.slug}/` === e.links.page) : undefined;
  if (entity) {
    const task = tr(entity.task, locale);
    return { main: [[locale === 'zh' && !hasChinese(task) ? { en: task } : task]], notes: [[L.sitePage]] };
  }
  return { main: [['—']], notes: [] };
}

/** A licence named by its identifier or its full name ("CC BY-NC-ND 4.0", "CC0-1.0", "Open Data Commons Attribution License 1.0"). */
const LICENCE_ID = /^(?:CC[- ]?BY(?:[- ](?:NC|ND|SA))*(?:[- ]\d\.\d)?|CC0(?:[- ]1\.0)?|MIT|GPL-\d\.\d|ODC-BY(?:-\d\.\d)?|Open Data Commons Attribution License \d\.\d|Creative Commons Attribution(?:[- ][A-Za-z]+)* \d\.\d(?: Generic| International)?)$/i;
const licenceIds = (v: string) => v.split(', ').every(t => LICENCE_ID.test(t));
/**
 * This site's own rights-record sentences in Chinese that directory-zh.json cannot hold: its keys are mvp.json's
 * English, and check-workbench.mjs fails any key that matches no mvp.json text, while these come from other release
 * files (BNCI2015-001's from adaptation-update.json). directory-zh.json's translation is used first.
 */
const siteTermsZh: Record<string, string> = {
  'CC BY-NC-ND 4.0 (as displayed by the official catalogue)': 'CC BY-NC-ND 4.0（据官方目录显示）',
};
/**
 * A row's stated terms as its cell prints them. A licence identifier prints as it is. This site's own rights-record
 * sentences print in Chinese on the Chinese page, as the dataset pages print them, with the reviewed English beside
 * them; one without Chinese fails the build. A catalog's own words for its terms ("free for research use") are quoted.
 */
function statedTerms(e: RegisterEntry, v: string, locale: Locale): { main: Part[]; original?: string } {
  if (e.terms_as_stated.by === 'site_release') {
    if (v === entityCopy.en.noLicence) return { main: [entityCopy[locale].noLicence] };
    if (locale === 'en' || licenceIds(v)) return { main: [{ en: v }] };
    const d = directoryText(v, locale);
    const zh = d.original ? d.text : siteTermsZh[v];
    need(zh, `${e.id}: this site's terms “${v}” have no Chinese (directory-zh.json)`);
    return { main: [zh], original: v };
  }
  if (licenceIds(v)) return { main: [{ en: v }] };
  need(e.terms_as_stated.by === 'moabb_catalog', `${e.id}: terms “${v}” stated by ${e.terms_as_stated.by} are neither a licence nor a catalog's words`);
  return { main: ['“', { en: v }, '”'] };
}

function termsCell(e: RegisterEntry, locale: Locale): Cell {
  const L = ui[locale], zh = locale === 'zh';
  if (e.ladder === 'model') {
    if (!e.terms_by_part) return { main: [['—']], notes: [] };
    return { main: (['code', 'weights', 'data'] as const).map(k => {
      const t = e.terms_by_part![k];
      need(t && partState[t.state] && byLabel[t.by], `${e.id}: the ${k} terms`);
      const by = byLabel[t.by][locale];
      const value: Part[] = t.state === 'stated' ? [t.value ? { c: t.value } : '—'] : [partState[t.state][locale]];
      return [`${partName[k][locale]}${zh ? '：' : ': '}`, ...value, ...(by ? [zh ? `（${by}）` : ` (${by})`] : [])];
    }), notes: [] };
  }
  const by = byLabel[e.terms_as_stated.by][locale];
  const fam = familyOf.get(e.id);
  if (fam) {
    const tags = Object.entries(fam.licence_tag_counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    return { main: [join(tags.map(([tag, n]) => [{ c: tag === 'none' ? L.noTag : tag }, ' (', { n }, ')']), [', '])], notes: [[by]] };
  }
  if (e.hf) {
    const tags = e.hf.licence_tags;
    return { main: [tags.length ? join(tags.map(t => [{ c: t }]), [', ']) : [{ c: L.noTag }]], notes: [[by]] };
  }
  if (e.group === 'corpus') {
    const ot = e.original_terms;
    need(ot && e.terms_as_stated.value && e.terms_as_stated.by === 'a4_capture', `${e.id}: a corpus row with no captured terms`);
    const c = captures.get(ot!.capture_id);
    need(c, `${e.id}: its capture ${ot!.capture_id} is not listed`);
    const quoted = L.quoted(longDate(c!.captured_at, locale), c!.capture_kind === 'archived copy');
    return {
      main: [['“', { en: e.terms_as_stated.value! }, '”']],
      notes: [[onHf(c!.url) ? quoted : { a: c!.url, t: quoted, ext: true }, ' · ', L.sha, { c: c!.sha256.slice(0, 16) }],
              [`${L.access}${accessLabel[e.access][locale]}`]],
    };
  }
  const v = e.terms_as_stated.value;
  const stated = v ? statedTerms(e, v, locale) : null;
  const notes: Part[][] = [];
  if (stated?.original) notes.push([{ en: stated.original }]);
  if (v && by) notes.push([by]);
  if (e.moabb?.record_note) notes.push([L.recordNote(e.moabb.record_note)]);
  if (!['open', 'catalog_only', 'unknown'].includes(e.access)) notes.push([`${L.access}${accessLabel[e.access][locale]}`]);
  return { main: [stated ? stated.main : [e.group === 'moabb' ? L.moabbNoLicence : L.termsNone]], notes };
}

/** The step-4 item no export computes yet (owner decision D12). */
export const NOT_COMPUTED = 'share_above_chance';
/** The step badge (by class, `rg-l<step>`), the gaps, the status and any rule that keeps the row at its step. */
function checkedCell(e: RegisterEntry, locale: Locale): { badge: string; lines: Part[][] } {
  const L = ui[locale], C = registerCopy[locale];
  const badge = e.ladder === 'dataset' ? C.datasetBadge(e.level) : C.modelBadge(e.level);
  const defs = register!.item_definitions[e.ladder];
  const lines: Part[][] = e.gaps.map(g => {
    const label = locale === 'zh' ? defs[g.item].label_zh : defs[g.item].label_en;
    // Owner decision D12: no export carries the share of participants above chance yet, so it is a value nobody has
    // computed, said as such.
    if (g.item === NOT_COMPUTED) return [L.notComputed(label)];
    // A gap is registerCopy's badge with a gap, word for word.
    if (e.ladder === 'dataset')
      need(C.datasetBadge(e.level, { step: g.step, item: label }) === `${badge} · ${L.gapAt(g.step, label)}`, `${e.id}: the gap words drifted from registerCopy`);
    return [L.gapAt(g.step, label)];
  });
  // A model row's status line only where it adds to the badge: "Listed" is the dataset ladder's step 1, and a model
  // row's "Published" says no more than its step.
  if (e.ladder === 'dataset' || !['listed', 'published'].includes(e.status)) lines.push([`${L.status}${C.status[e.status]}`]);
  if (e.level_cap) lines.push([{ a: '#levels', t: capLabel[e.level_cap.rule][locale] }]);
  return { badge, lines };
}

function foundCell(e: RegisterEntry, locale: Locale): { items: Part[][]; links: Part[] } {
  const L = ui[locale];
  const items = findingItems(e, locale);
  if (e.exposure) items.push([L.exposureField(L.exposureValue[e.exposure] ?? e.exposure)]);
  if (e.links.cases?.length)
    items.push([L.cases, ...(locale === 'zh' ? [] : [' ']), ...join(e.links.cases.map(c => {
      const slug = c.match(/^\/topics\/([^/]+)\//)?.[1];
      need(slug && topicPages.some(t => t.slug === slug), `${e.id}: ${c} is not a topic page`);
      return [{ a: sitePath(c, locale, e.id), t: topicCards[locale][slug!].title }] as Part[];
    }), [locale === 'zh' ? '、' : ', '])]);
  const links: Part[][] = [];
  if (e.links.page && !heldPages.has(e.links.page) && e.ladder === 'dataset') links.push([{ a: sitePath(e.links.page, locale, e.id), t: L.page }]);
  if (e.links.case) links.push([{ a: sitePath(e.links.case, locale, e.id), t: L.caseLink }]);
  const exposure = exposureHref(e, locale);
  if (exposure) links.push([{ a: exposure, t: L.exposure }]);
  if (e.links.parent_row) links.push([L.parent, rowLink(e.links.parent_row, { locale, row: e })]);
  return { items, links: join(links, [' · ']) };
}

/** A cell as HTML: one main line as it is, several each on its own line; each note in a <small>. */
function cellHtml(c: Cell, locale: Locale): string {
  const main = c.main.length === 1 ? html(c.main[0], locale) : c.main.map(l => `<span class="rg-main">${html(l, locale)}</span>`).join('');
  return main + c.notes.map(l => `<small>${html(l, locale)}</small>`).join('');
}

export function rowView(e: RegisterEntry, locale: Locale): RowView {
  const c = checkedCell(e, locale), f = foundCell(e, locale);
  const fix = `<a class="rg-fix" href="${esc(registerCorrectionHref(e.id))}">${esc(ui[locale].correct)}</a>`;
  return {
    id: e.id, group: e.ladder === 'model' ? e.kind : e.group, step: e.level, terms: termsStated(e), gap: e.gaps.length > 0,
    name: cellHtml(nameCell(e, locale), locale),
    signal: cellHtml(signalCell(e, locale), locale),
    termsCell: cellHtml(termsCell(e, locale), locale),
    checked: `<span class="rg-badge rg-l${e.level}">${esc(c.badge)}</span>${c.lines.map(l => `<small>${html(l, locale)}</small>`).join('')}`,
    found: (f.items.length ? `<ul class="rg-list">${f.items.map(i => `<li>${html(i, locale)}</li>`).join('')}</ul>` : '')
      + `<p class="rg-links">${f.links.length ? `${html(f.links, locale)} · ` : ''}${fix}</p>`,
  };
}

/* --- Groups --------------------------------------------------------------------------------------------------- */

export interface GroupView { key: string; name: string; note: string; count: Fig | null; rows: RowView[] }

/** A ladder's rows in the page's groups and order, each group with its heading. The rows rendered are the file's. */
export function registerGroups(ladder: Ladder, locale: Locale): GroupView[] {
  need(register, 'no register file is served');
  const R = register!;
  const rows = R.entries.filter(e => e.ladder === ladder);
  const out: GroupView[] = [];
  if (ladder === 'dataset') {
    for (const g of datasetGroups) {
      const members = rows.filter(e => e.group === g.key);
      const n = R.counts.rows.dataset_by_group[g.key];
      need(members.length === n, `the ${g.key} group: ${members.length} rows, and the counts say ${n}`);
      // This site's rows, furthest step first; every other group in the file's order.
      if (g.key === 'site') members.sort((a, b) => b.level - a.level || a.id.localeCompare(b.id));
      out.push({ key: g.key, name: registerCopy[locale].groups[g.copy], note: groupNotes[g.key][locale], count: regFig(n), rows: members.map(e => rowView(e, locale)) });
    }
  } else {
    for (const g of modelGroups) {
      const members = rows.filter(e => e.kind === g.key);
      if (!members.length) continue;
      if (g.key === 'site_model') members.sort((a, b) => b.level - a.level || a.id.localeCompare(b.id));
      out.push({ key: g.key, name: g.name[locale], note: groupNotes[g.key][locale], count: null, rows: members.map(e => rowView(e, locale)) });
    }
  }
  const rendered = out.reduce((s, g) => s + g.rows.length, 0);
  need(rendered === rows.length && rendered === (ladder === 'dataset' ? R.counts.rows.dataset : R.counts.rows.model),
    `${ladder}: ${rendered} rows rendered, ${rows.length} in the file`);
  return out;
}

/** The filter's choices for a ladder: its groups and its five steps. */
export function filterChoices(ladder: Ladder, locale: Locale) {
  const steps = ladder === 'dataset' ? datasetLadder : modelLadder;
  return {
    groups: ladder === 'dataset'
      ? datasetGroups.map(g => ({ value: g.key as string, label: registerCopy[locale].groups[g.copy] }))
      : modelGroups.map(g => ({ value: g.key as string, label: g.name[locale] })),
    steps: steps.map(s => ({ value: String(s.step), label: locale === 'zh' ? `第 ${s.step} 步 · ${s.name.zh}` : `Step ${s.step} · ${s.name.en}` })),
  };
}

/* --- The counts strip and the catalog markup ------------------------------------------------------------------ */

/**
 * The register's counts, checked to add up the way the counts strip says they do: the groups and the steps make the
 * rows; the Hugging Face snapshot runs from its listings to the rows in the register; the EEGDash mirrors split by
 * accession; MOABB's records less those merged into this site's rows are its rows; one row per captured corpus.
 */
export function registerCounts() {
  need(register, 'no register file is served');
  const R = register!, C = R.counts, H = C.hf, S = H.snapshot, rows = R.entries.filter(e => e.ladder === 'dataset');
  const sum = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
  need(C.rows.total === C.rows.dataset + C.rows.model && rows.length === C.rows.dataset, 'rows: the dataset and model rows make the total');
  need(sum(C.rows.dataset_by_group) === C.rows.dataset && Object.keys(C.rows.dataset_by_group).sort().join() === datasetGroups.map(g => g.key).sort().join(),
    'rows: the five groups make the dataset rows');
  need(sum(C.rows.dataset_by_level) === C.rows.dataset && [1, 2, 3, 4, 5].every(l => rows.filter(e => e.level === l).length === (C.rows.dataset_by_level[String(l)] ?? 0)),
    'rows: the steps make the dataset rows, each as the rows themselves say');
  need(S.search_terms === R.sources.hf.search_terms.length && S.tag_filters === R.sources.hf.tag_filters.length, 'the snapshot’s query');
  need(S.retrieved_at === R.sources.hf.retrieved_at, 'the snapshot’s time');
  need(S.listings === S.eegdash_mirrors + S.other_uploads && S.other_uploads === S.prefilter_dropped + S.classified, 'the snapshot: listings, mirrors and other uploads');
  need(H.classifier_in_scope - H.recheck_out_emg_rule - H.recheck_out_simulated - H.recheck_out_undetermined === H.in_scope, 'the re-check: in scope after it');
  need(H.in_scope === H.single_rows + H.family_members + H.merged_into_site_rows + H.merged_into_moabb_rows + H.held_for_review, 'the uploads in scope: own rows, families, merged, held');
  need(H.single_rows + H.family_rows === C.rows.dataset_by_group.hf, 'the Hugging Face rows: single rows and family rows');
  const hfRows = rows.filter(e => e.group === 'hf');
  need(hfRows.filter(e => e.kind === 'hf_upload').length === H.single_rows && hfRows.filter(e => e.kind === 'hf_family').length === H.family_rows,
    'the Hugging Face rows by kind');
  const series = R.families.filter(f => f.kind === 'hf_series');
  need(series.reduce((s, f) => s + f.n, 0) === H.family_members && series.length === H.family_rows, 'the uploader series');
  const tagless = hfRows.filter(e => e.findings.some(f => f.code === 'licence_tag_absent')).length + series.reduce((s, f) => s + (f.no_licence_tag ?? 0), 0);
  need(tagless <= H.no_licence_tag && H.no_licence_tag - tagless <= H.merged_into_site_rows + H.merged_into_moabb_rows + H.held_for_review, 'the uploads with no licence tag');
  const gated = hfRows.filter(e => e.hf?.gated).length + series.reduce((s, f) => s + (f.gated?.manual ?? 0) + (f.gated?.auto ?? 0), 0);
  need(gated <= H.gated_manual + H.gated_auto && H.gated_manual + H.gated_auto - gated <= H.merged_into_site_rows + H.held_for_review, 'the gated uploads');
  need(C.eegdash.mirrors === S.eegdash_mirrors && C.eegdash.mirrors === C.eegdash.openneuro + C.eegdash.nemar + C.eegdash.other, 'the EEGDash mirrors by accession');
  const eegdash = R.families.find(f => f.kind === 'eegdash');
  need(eegdash && eegdash.n === C.eegdash.mirrors && eegdash.site_rows_with_mirror === C.eegdash.site_rows_with_mirror, 'the EEGDash family');
  need(C.moabb.release === R.sources.moabb.release && C.moabb.record_groups - C.moabb.merged_into_site_rows === C.rows.dataset_by_group.moabb,
    'MOABB: its records less those merged into this site’s rows');
  need(rows.filter(e => e.group === 'moabb').reduce((s, e) => s + (e.moabb?.loaders.length ?? 0), 0) <= C.moabb.loaders, 'MOABB’s loaders');
  need(C.corpus.families === C.rows.dataset_by_group.corpus && C.corpus.captured === C.corpus.families
    && rows.filter(e => e.group === 'corpus').every(e => e.original_terms && captures.has(e.original_terms.capture_id)), 'one row per captured corpus');
  need(C.rows.model === R.entries.filter(e => e.ladder === 'model').length, 'the model rows');
  const checked = [...new Set(rows.map(e => e.checked))].sort();
  return { C, H, S, checked, moabbRelease: C.moabb.release, catalogChecked: R.sources.moabb.catalog_checked };
}

/**
 * A row's name as the markup gives it, with no Hugging Face user name: repository ids stay in the row's text (plan
 * §2.6). An upload is named by its repository's own name, an uploader's series by the series and its size, and any
 * other name loses the user name of a repository id it carries ("… (Capur/IESSEEG)" → "…").
 */
function markupName(e: RegisterEntry): string {
  if (e.kind === 'hf_family' && e.family) return `${e.family.series} (${e.family.n} ${e.family.n === 1 ? 'repository' : 'repositories'})`;
  if (e.hf) return e.hf.repo.slice(e.hf.repo.indexOf('/') + 1);
  const ns = (x: string) => registerNamespaces.has(x.toLowerCase());
  return e.name.replace(/\s*\(([\w.-]+)\/[\w.-]+\)/g, (m, u: string) => (ns(u) ? '' : m))
    .replace(/(?<![\w.-])([\w.-]+)\/([\w.-]+)/g, (m, u: string, rest: string) => (ns(u) ? rest : m));
}
/** A register page's schema.org DataCatalog rows: each row by name, its address as the page links it, and a description. */
export function catalogRows(ladder: Ladder): { name: string; url?: string; description: string }[] {
  need(register, 'no register file is served');
  const groupName = new Map<string, string>(datasetGroups.map(g => [g.key, registerCopy.en.groups[g.copy]]));
  return register!.entries.filter(e => e.ladder === ladder).map(e => {
    const url = ladder === 'model'
      ? (e.links.page ? new URL(e.links.page, site.origin).href : hostHref(e.urls.paper ?? e.urls.code ?? null))
      : hostHref(e.urls.record ?? e.urls.search ?? e.family?.search_url ?? null);
    const step = register!.level_definitions[ladder][String(e.level)].en;
    const where = ladder === 'dataset' ? `the ${site.name} open register (${groupName.get(e.group)})` : `the ${site.name} model register`;
    const description = `A row of ${where}, checked to step ${e.level} of 5: ${step}.`;
    const name = markupName(e);
    need(![...registerNamespaces].some(u => new RegExp(`(?<![\\w.-])${u.replace(/[.]/g, '\\.')}/`).test(name.toLowerCase())), `${e.id}: a user name in the markup`);
    return url ? { name, url, description } : { name, description };
  });
}

/** A ladder's five steps as #levels prints them: the file's step names and what each step needs, in either language. */
export function ladderSteps(ladder: Ladder, locale: Locale): { step: number; name: string; needs: string }[] {
  need(register, 'no register file is served');
  return [1, 2, 3, 4, 5].map(step => {
    const d = register!.level_definitions[ladder][String(step)];
    need(d.needs_en && d.needs_zh, `${ladder} step ${step}: what it needs, in both languages`);
    return { step, name: locale === 'zh' ? d.zh : d.en, needs: locale === 'zh' ? d.needs_zh : d.needs_en };
  });
}
