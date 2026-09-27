/**
 * Datasets and methods as entities: one page each, built from the reviewed
 * payloads and nothing else.
 *
 * Why: people — and assistants searching on their behalf — ask about a dataset
 * or a model by name ("how does EEGNet do on SSVEP?", "what has been measured on
 * BETA?"). The topic pages answer questions; these pages answer names, by
 * gathering every published figure that involves the entity, wherever it sits.
 *
 * The rule these pages live under: they add no number. Every value is a leaf of
 * a published payload, carried with the file it came from and the format it is
 * printed in (`Fig`), and check-workbench.mjs re-reads that leaf from the file
 * and re-formats it. An average, a difference or a rank computed here would have
 * no leaf to match and would fail the build.
 *
 * Only `results` enter. Status-only sources and holds never do, so a held source
 * cannot get a page by the side door.
 */
import data from './mvp.json';
import deployment from './deployment-topics.json';
import evidence from './evidence-update.json';
import clinical from './clinical-update.json';
import context from './context-update.json';
import type { Locale } from './i18n';
import { conditionLabel, modelLabel } from './topics';

/** English is required; a missing `zh` renders the English text marked lang="en". */
export type L = { en: string; zh?: string };
export const tr = (l: L, locale: Locale) => (locale === 'zh' && l.zh) || l.en;
export const isEnglishOnly = (l: L, locale: Locale) => locale === 'zh' && !l.zh;

export type Fmt = 'pct1' | 'pct1raw' | 'pp1' | 'auc3' | 'auc2' | 'num3' | 'count';
/** A published figure: the raw leaf, the served file it is a leaf of, and how it prints. */
export interface Fig { raw: number; fmt: Fmt; src: string }

const minus = (s: string) => s.replace(/^-/, '−');
/** Kept in step with the formatters in check-workbench.mjs. */
export function formatFig(f: Fig): string {
  switch (f.fmt) {
    case 'pct1': return `${(f.raw * 100).toFixed(1)}%`;
    case 'pct1raw': return `${f.raw.toFixed(1)}%`;
    case 'pp1': return `${f.raw >= 0 ? '+' : '−'}${Math.abs(f.raw * 100).toFixed(1)} pp`;
    case 'auc3': return f.raw.toFixed(3);
    case 'auc2': return f.raw.toFixed(2);
    case 'num3': return minus(f.raw.toFixed(3));
    case 'count': return f.raw.toLocaleString('en-US');
  }
}

export interface ResultRow {
  /** Locale-free page path, with an anchor where the figure's section has one. */
  path: string;
  method: string;
  methodSlug?: MethodSlug;
  /** A reference or comparator, not a decoding model; printed as such. */
  comparator?: boolean;
  condition: L;
  metric: L;
  value: Fig;
  interval?: [Fig, Fig];
  /** For counts: `value` out of `of`. */
  of?: Fig;
  people: number;
}

export interface ResultGroup {
  id: string;
  title: L;
  /** Chance level where the payload records one. */
  chance?: Fig;
  path: string;
  rows: ResultRow[];
}

export interface DatasetEntity {
  slug: string;
  name: string;
  task: L;
  license: string;
  licenseUrl?: string;
  attribution: string;
  sources: string[];
  groups: ResultGroup[];
}

const MVP = 'experiments.json', DEP = 'deployment-topics.json', EVI = 'evidence-update.json',
      CLI = 'clinical-update.json', CTX = 'context-update.json';
const fig = (raw: number, fmt: Fmt, src: string): Fig => ({ raw, fmt, src });
const pair = (iv: number[] | null | undefined, fmt: Fmt, src: string): [Fig, Fig] | undefined =>
  iv ? [fig(iv[0], fmt, src), fig(iv[1], fmt, src)] : undefined;

/* --- Methods that get a page -------------------------------------------------- */

export const methodSlugs = ['eegnet', 'labram', 'cbramod', 'shallowfbcspnet', 'deep4net', 'csp-lda',
                            'cca', 'fbcca', 'etrca'] as const;
export type MethodSlug = typeof methodSlugs[number];
/** Model ids as the payloads write them → the method page they belong to. */
const METHOD_OF: Record<string, MethodSlug> = {
  eegnet: 'eegnet', labram: 'labram', cbramod: 'cbramod', shallowfbcspnet: 'shallowfbcspnet',
  deep4net: 'deep4net', 'csp-lda': 'csp-lda', cca: 'cca', 'author-cca': 'cca', fbcca: 'fbcca',
  'ensemble-trca': 'etrca',
};
export const methodNames: Record<MethodSlug, string> = {
  eegnet: 'EEGNet', labram: 'LaBraM', cbramod: 'CBraMod', shallowfbcspnet: 'ShallowFBCSPNet',
  deep4net: 'Deep4Net', 'csp-lda': 'CSP+LDA', cca: 'CCA', fbcca: 'FBCCA', etrca: 'eTRCA',
};

/* --- Labels ------------------------------------------------------------------- */

const BA: L = { en: 'Balanced accuracy', zh: '平衡准确率' };
const AUROC: L = { en: 'AUROC' };
const ROC_AUC: L = { en: 'ROC AUC' };
const DIFF: L = { en: 'Paired difference', zh: '配对差值' };
const sensor = { wet: { en: 'wet', zh: '湿电极' }, dry: { en: 'dry', zh: '干电极' } } as Record<string, { en: string; zh: string }>;
const cap = (s: string) => s[0].toUpperCase() + s.slice(1);

/* --- Core matrix (mvp.json) ------------------------------------------------------ */

const MVP_SLUG: Record<string, string> = {
  ds003810: 'ds003810', EEGMAT: 'eegmat', 'EESM19 scalp subset': 'eesm19', BETA: 'beta',
  'TMNRED / ds005383': 'tmnred', ds006593: 'ds006593', ds005342: 'ds005342',
};
const trackTitles: Record<string, L> = {
  'mi-rest': { en: 'Core matrix · motor imagery & rest', zh: '核心矩阵 · 运动想象与静息' },
  idle: { en: 'Core matrix · idle & command', zh: '核心矩阵 · 空闲与指令' },
  'beta-8ch': { en: 'Core matrix · SSVEP, 8 channels', zh: '核心矩阵 · SSVEP，8 通道' },
  'beta-4ch': { en: 'Core matrix · SSVEP, 4 channels', zh: '核心矩阵 · SSVEP，4 通道' },
  'arithmetic-rest': { en: 'Core matrix · arithmetic & rest', zh: '核心矩阵 · 心算与静息' },
  'p300-target': { en: 'Core matrix · P300 target ERP', zh: '核心矩阵 · P300 目标 ERP' },
  'semantic-target': { en: 'Core matrix · semantic target ERP', zh: '核心矩阵 · 语义目标 ERP' },
  'sleep-scalp': { en: 'Core matrix · sleep staging', zh: '核心矩阵 · 睡眠分期' },
};

function mvpGroups(datasetName: string): ResultGroup[] {
  return data.tracks.filter(t => t.dataset === datasetName).map(t => {
    const rows: ResultRow[] = [];
    for (const r of t.rows) {
      const base = { path: '/#overview', method: r.name, methodSlug: METHOD_OF[r.id],
                     condition: { en: t.subtitle }, people: r.subjects ?? t.subjects };
      if (t.type === 'tradeoff') {
        rows.push({ ...base, metric: { en: 'Command detection ≤3 s', zh: '指令检出率 ≤3 秒' }, value: fig(r.y, 'pct1raw', MVP) });
        rows.push({ ...base, metric: { en: 'Idle false activation', zh: '空闲误触发率' }, value: fig(r.x, 'pct1raw', MVP) });
      } else {
        rows.push({ ...base, metric: BA, value: fig(r.y, 'pct1raw', MVP), interval: pair(r.interval, 'pct1raw', MVP) });
      }
    }
    return { id: t.id, title: trackTitles[t.id] ?? { en: t.title }, path: '/#overview', rows,
             chance: t.chanceLevel != null ? fig(t.chanceLevel, 'pct1raw', MVP) : undefined };
  });
}

/* --- Deployment topics (deployment-topics.json) ------------------------------------ */

const DEP_SLUG: Record<string, string> = {
  'zhu2021-wearable102-author-snapshot-20260920': 'wearable-ssvep-102',
  'nemar-nm000125-v1.0.2': 'mobile-bci', 'nemar-nm000201-v1.0.2': 'mobile-bci',
  ds003810: 'ds003810', 'physionet-eegmat-1.0.0': 'eegmat',
};
const DEP_TRACK: Record<string, { title: L; path: string }> = {
  'wearable-sensor-transfer': { title: { en: 'Dry vs. wet sensor transfer', zh: '干湿电极传感器迁移' }, path: '/topics/dry-vs-wet/' },
  'wearable-calibration': { title: { en: 'Calibration budget · spectral ridge', zh: '校准预算 · spectral ridge' }, path: '/topics/calibration-budget/' },
  'wearable-etrca-calibration': { title: { en: 'Calibration budget · eTRCA and CCA', zh: '校准预算 · eTRCA 与 CCA' }, path: '/topics/calibration-budget/' },
  'mobile-ssvep-2s': { title: { en: 'Movement · SSVEP, 2-second windows', zh: '运动 · SSVEP，2 秒时间窗' }, path: '/topics/on-the-move/#ssvep2-heading' },
  'mobile-ssvep-5s': { title: { en: 'Movement · SSVEP, 5-second windows', zh: '运动 · SSVEP，5 秒时间窗' }, path: '/topics/on-the-move/#five-heading' },
  'mobile-erp': { title: { en: 'Movement · ERP', zh: '运动 · ERP' }, path: '/topics/on-the-move/#erp-heading' },
  'pretraining-attribution-fixed': { title: { en: 'Pretraining · fixed readout', zh: '预训练 · 固定分类头' }, path: '/topics/does-pretraining-help/' },
  'pretraining-attribution-selected': { title: { en: 'Pretraining · train-selected readout', zh: '预训练 · 训练集内选定分类头' }, path: '/topics/does-pretraining-help/' },
  'fixed-classical-control': { title: { en: 'Pretraining · fixed classical control', zh: '预训练 · 固定经典对照' }, path: '/topics/does-pretraining-help/' },
};
type DepRow = typeof deployment.rows[number];

function depCondition(r: DepRow): L {
  const s = r.source_sensor ?? null, t = r.target_sensor ?? null;
  switch (r.track) {
    case 'wearable-sensor-transfer':
      return s ? { en: `Trained on ${s}, tested on ${t}`, zh: `${sensor[s].zh}训练，${sensor[t!].zh}测试` }
               : { en: `${cap(t!)} recording · no source training`, zh: `${sensor[t!].zh}记录 · 无源域训练` };
    case 'wearable-calibration':
      return r.training_regime === 'source-only'
        ? { en: `Source-only, trained on ${s}, tested on ${t}`, zh: `仅源域，${sensor[s!].zh}训练，${sensor[t!].zh}测试` }
        : { en: `${r.labeled_target_trials} calibration trials · ${t}`, zh: `${r.labeled_target_trials} 个校准试次 · ${sensor[t!].zh}` };
    case 'wearable-etrca-calibration':
      return r.labeled_target_trials
        ? { en: `${r.labeled_target_trials} calibration trials · ${t}`, zh: `${r.labeled_target_trials} 个校准试次 · ${sensor[t!].zh}` }
        : { en: `No calibration · ${t}`, zh: `无校准 · ${sensor[t!].zh}` };
    case 'mobile-ssvep-2s': case 'mobile-ssvep-5s': case 'mobile-erp': {
      const where = { scalp: { en: 'scalp', zh: '头皮' }, ear: { en: 'ear', zh: '耳部' } }[r.modality as 'scalp' | 'ear'];
      return { en: `${conditionLabel(r.condition, 'en')} · ${where.en} · ${r.channels} ch`,
               zh: `${conditionLabel(r.condition, 'zh')} · ${where.zh} · ${r.channels} 通道` };
    }
    case 'pretraining-attribution-fixed': case 'pretraining-attribution-selected': {
      const task = r.dataset_id === 'ds003810' ? { en: 'MI / rest', zh: '运动想象 / 静息' } : { en: 'Mental workload', zh: '脑力负荷' };
      return r.initialization === 'pretrained'
        ? { en: `${task.en} · pretrained`, zh: `${task.zh} · 预训练` }
        : { en: `${task.en} · random initialization (mean)`, zh: `${task.zh} · 随机初始化（均值）` };
    }
    default:
      return r.dataset_id === 'ds003810' ? { en: 'MI / rest', zh: '运动想象 / 静息' } : { en: 'Mental workload', zh: '脑力负荷' };
  }
}

function depRow(r: DepRow): ResultRow {
  const auc = r.metric === 'participant_mean_roc_auc';
  return {
    path: DEP_TRACK[r.track].path, method: modelLabel(r.model), methodSlug: METHOD_OF[r.model],
    comparator: r.model === 'random-uniform' || r.model === 'same-frequency-power',
    condition: depCondition(r), metric: auc ? ROC_AUC : BA,
    value: fig(r.value, auc ? 'auc3' : 'pct1', DEP),
    interval: pair(r.confidence_interval_95, auc ? 'auc3' : 'pct1', DEP),
    people: r.participants,
  };
}

function depGroups(slug: string): ResultGroup[] {
  const tracks = [...new Set(deployment.rows.filter(r => DEP_SLUG[r.dataset_id] === slug).map(r => r.track))];
  return tracks.map(track => ({
    id: track, title: DEP_TRACK[track].title, path: DEP_TRACK[track].path.split('#')[0],
    rows: deployment.rows.filter(r => r.track === track && DEP_SLUG[r.dataset_id] === slug).map(depRow),
  }));
}

/* --- Later batches ------------------------------------------------------------------ */

const ev = evidence.results, cl = clinical.results, cx = context.results as Record<string, any>;

function evidenceGroup(id: 'eesm23' | 'alphawaves'): ResultGroup {
  const r = ev[id] as any;
  const fewer = id === 'eesm23'
    ? { title: { en: 'Fewer electrodes · in-ear vs. scalp sleep staging', zh: '更少的电极 · 耳道内与头皮睡眠分期' }, path: '/topics/fewer-electrodes/#montage-finding',
        method: 'Log-bandpower logistic regression',
        labels: { in_ear: { en: 'Four in-ear channels', zh: '4 个耳道内通道' }, scalp: { en: 'Six scalp electrodes', zh: '6 个头皮电极' } } as Record<string, L>,
        diff: { en: 'Scalp minus in-ear, same epochs', zh: '头皮减耳道内，相同数据帧' } }
    : { title: { en: 'Fewer electrodes · four posterior vs. all sixteen', zh: '更少的电极 · 后部 4 个与全部 16 个' }, path: '/topics/fewer-electrodes/#posterior-subset',
        method: 'Relative band-power logistic regression',
        labels: { posterior4: { en: 'Four posterior electrodes', zh: '后部 4 个电极' }, all16: { en: 'All sixteen electrodes', zh: '全部 16 个电极' } } as Record<string, L>,
        diff: { en: 'All sixteen minus four posterior', zh: '全部 16 个减后部 4 个' } };
  const people = r.cohort.people;
  return {
    id, title: fewer.title, path: fewer.path.split('#')[0], chance: fig(r.chance_level, 'pct1', EVI),
    rows: [
      ...r.configurations.map((c: any) => ({ path: fewer.path, method: fewer.method, condition: fewer.labels[c.id], metric: BA,
        value: fig(c.mean_balanced_accuracy, 'pct1', EVI), interval: pair(c.balanced_accuracy_bootstrap_95, 'pct1', EVI), people })),
      { path: fewer.path, method: fewer.method, condition: fewer.diff, metric: DIFF,
        value: fig(r.paired_difference.mean, 'pp1', EVI), interval: pair(r.paired_difference.bootstrap_95, 'pp1', EVI), people },
    ],
  };
}

function phantomGroup(): ResultGroup {
  const r = ev.phantom as any;
  const path = '/topics/on-the-move/#phantom-heading';
  return {
    id: 'phantom', title: { en: 'Movement · physical head phantom (engineering check)', zh: '运动 · 物理头模（工程对照）' }, path: '/topics/on-the-move/',
    rows: r.conditions.flatMap((c: any) => [
      { path, method: 'Fixed multi-output ridge regression', condition: { en: c.condition }, metric: { en: 'Signed correlation r', zh: '有符号相关 r' },
        value: fig(c.signed_correlation_r.value, 'num3', EVI), people: 0 },
      { path, method: 'Fixed multi-output ridge regression', condition: { en: c.condition }, metric: { en: 'Predictive R²', zh: '预测 R²' },
        value: fig(c.predictive_r_squared.value, 'num3', EVI), people: 0 },
    ]),
  };
}

function clinicalGroup(): ResultGroup {
  const r = cl.ds004584 as any;
  const path = '/topics/clinical-groups/';
  return {
    id: 'ds004584', title: { en: "Clinical groups · Parkinson's disease vs. controls", zh: '临床分组 · 帕金森病与对照' }, path,
    chance: fig(r.chance_level, 'pct1', CLI),
    rows: r.models.flatMap((m: any) => {
      const comparator = m.id === 'demographics_only';
      const base = { path, method: m.label, comparator, condition: comparator ? { en: 'Age and sex only · no EEG', zh: '只用年龄与性别 · 不用 EEG' } : { en: 'Resting-state EEG, eyes open', zh: '睁眼静息态 EEG' }, people: r.cohort.people };
      return [
        { ...base, metric: BA, value: fig(m.mean_balanced_accuracy, 'pct1', CLI), interval: pair(m.balanced_accuracy_bootstrap_95, 'pct1', CLI) },
        { ...base, metric: AUROC, value: fig(m.auroc, 'auc2', CLI) },
      ];
    }),
  };
}

function vrGroup(): ResultGroup {
  const r = cx['vr-pc-p300'];
  const path = '/topics/screen-to-vr/';
  const timing: Record<string, L> = {
    onset_corrected: { en: 'PC ⇄ VR, onset-corrected timing', zh: '电脑 ⇄ VR，校正刺激出现时刻' },
    recorded_tag: { en: 'PC ⇄ VR, recorded-tag timing (sensitivity)', zh: '电脑 ⇄ VR，按记录标签计时（敏感性分析）' },
  };
  return {
    id: 'vr-pc-p300', title: { en: 'Screen to VR · P300 across displays', zh: '从屏幕到 VR · 跨设备 P300' }, path,
    chance: fig(r.chance_level, 'pct1', CTX),
    rows: Object.entries(r.timings as Record<string, any[]>).flatMap(([t, models]) => models.flatMap(m => [
      { path, method: m.label, condition: timing[t], metric: BA, value: fig(m.balanced_accuracy.mean, 'pct1', CTX),
        interval: pair(m.balanced_accuracy.bootstrap_95, 'pct1', CTX), people: r.cohort.people },
      { path, method: m.label, condition: timing[t], metric: AUROC, value: fig(m.auroc.mean, 'auc3', CTX),
        interval: pair(m.auroc.bootstrap_95, 'auc3', CTX), people: r.cohort.people },
    ])),
  };
}

function gaitGroup(): ResultGroup {
  const r = cx['gait-eeg'];
  const path = '/topics/on-the-move/#treadmill-speed';
  return {
    id: 'gait-eeg', title: { en: 'Movement · treadmill walking speed (a confound case)', zh: '运动 · 跑步机步速（混杂案例）' }, path: '/topics/on-the-move/',
    chance: fig(r.chance_level, 'pct1', CTX),
    rows: r.models.map((m: any) => ({
      path, method: m.label, comparator: m.id === 'nuisance_logistic',
      condition: m.id === 'nuisance_logistic' ? { en: 'Movement-nuisance features, not brain signal', zh: '运动干扰特征，不是脑信号' } : { en: 'Relative spectral bands, 19 scalp channels', zh: '相对频带功率，19 个头皮通道' },
      metric: BA, value: fig(m.balanced_accuracy, 'pct1', CTX), interval: pair(m.balanced_accuracy_bootstrap_95, 'pct1', CTX),
      people: r.cohort.people_scored,
    })),
  };
}

function ysuGroup(): ResultGroup {
  const r = cx['ysu-async-ssvep'];
  const path = '/topics/when-not-to-act/#non-control';
  const w = r.control_windows, method = 'Fixed CCA with rejection', people = r.people;
  const intended = { en: 'Command intended', zh: '有意发出指令' };
  return {
    id: 'ysu-async-ssvep', title: { en: 'When not to act · control and non-control windows', zh: '何时不该执行 · 控制与非控制窗口' }, path: '/topics/when-not-to-act/',
    rows: [
      { path, method, condition: intended, metric: { en: 'Frequency recognised', zh: '频率识别正确' }, value: fig(w.frequency_recognised, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      { path, method, condition: intended, metric: { en: 'Accepted (coverage)', zh: '被接受（覆盖率）' }, value: fig(w.accepted, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      { path, method, condition: intended, metric: { en: 'Accepted and correct', zh: '被接受且正确' }, value: fig(w.accepted_and_correct, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      ...r.false_acceptance.map((f: any) => ({ path, method, condition: { en: `No command · ${f.condition}` },
        metric: { en: 'Accepted by mistake (per window)', zh: '误接受（按窗口）' }, value: fig(f.accepted, 'count', CTX), of: fig(f.tested, 'count', CTX), people })),
    ],
  };
}

/* --- The datasets ------------------------------------------------------------------ */

const mvpDs = (name: string) => data.datasets.find(d => d.name === name)!;
const citation = (id: string) => deployment.dataset_citations.find(c => c.id === id)!;
const rights = (r: any) => r.rights as { name: string; task: string; source: string; license: string; licenseUrl?: string; attribution: string };

function fromMvp(name: string, task: L): DatasetEntity {
  const d = mvpDs(name);
  const slug = MVP_SLUG[name];
  return {
    slug, name: d.name, task, license: d.license, licenseUrl: d.licenseUrl ?? undefined,
    attribution: d.attribution, sources: [d.source].filter(Boolean) as string[],
    groups: [...mvpGroups(name), ...depGroups(slug)],
  };
}

function fromRights(slug: string, r: any, groups: ResultGroup[], task: L, name?: string): DatasetEntity {
  const x = rights(r);
  return { slug, name: name ?? x.name, task, license: x.license, licenseUrl: x.licenseUrl, attribution: x.attribution,
           sources: [x.source], groups };
}

const wear = citation('zhu2021-wearable102-author-snapshot-20260920');
const mob = [citation('nemar-nm000125-v1.0.2'), citation('nemar-nm000201-v1.0.2')];

export const datasets: DatasetEntity[] = [
  fromMvp('ds003810', { en: 'Motor imagery / rest', zh: '运动想象 / 静息' }),
  fromMvp('EEGMAT', { en: 'Mental arithmetic / rest', zh: '心算 / 静息' }),
  fromMvp('BETA', { en: '40-target SSVEP', zh: '40 目标 SSVEP' }),
  fromMvp('ds006593', { en: 'P300 target ERP', zh: 'P300 目标 ERP' }),
  fromMvp('TMNRED / ds005383', { en: 'Semantic target ERP', zh: '语义目标 ERP' }),
  fromMvp('EESM19 scalp subset', { en: 'Five-stage sleep', zh: '五期睡眠分期' }),
  fromMvp('ds005342', { en: 'Cue-gated idle / command', zh: '提示同步的空闲 / 指令' }),
  {
    slug: 'wearable-ssvep-102', name: 'Wearable SSVEP BCI dataset (dry and wet electrodes)', task: { en: '12-target SSVEP, dry and wet electrodes', zh: '12 目标 SSVEP，干电极与湿电极' },
    license: String(wear.identity.license), attribution: String(wear.identity.canonical_dataset_citation ?? wear.identity.dataset_citation),
    sources: wear.primary_sources.slice(0, 2), groups: depGroups('wearable-ssvep-102'),
  },
  {
    slug: 'mobile-bci', name: 'Mobile BCI dataset (SSVEP and ERP paradigms)', task: { en: 'SSVEP and ERP while standing, walking and running', zh: '站立、行走与跑动中的 SSVEP 与 ERP' },
    license: String(mob[0].identity.license),
    attribution: mob.map(c => String(c.identity.canonical_dataset_citation ?? c.identity.dataset_citation)).join(' · '),
    sources: [mob[0].primary_sources[0], mob[1].primary_sources[0], mob[0].primary_sources[2]], groups: depGroups('mobile-bci'),
  },
  fromRights('eesm23', ev.eesm23, [evidenceGroup('eesm23')], { en: 'Five-stage sleep, in-ear and scalp', zh: '五期睡眠分期，耳道内与头皮' }),
  fromRights('alpha-waves', ev.alphawaves, [evidenceGroup('alphawaves')], { en: 'Eyes open / eyes closed', zh: '睁眼 / 闭眼' }),
  fromRights('phantom', ev.phantom, [phantomGroup()], { en: 'Physical head phantom with motion, muscle and eye artifacts', zh: '带运动、肌电与眼动伪迹的物理头模' }),
  fromRights('ds004584', cl.ds004584, [clinicalGroup()], { en: "Resting-state EEG, Parkinson's disease and controls", zh: '静息态 EEG，帕金森病与对照' }, "OpenNeuro ds004584 · Parkinson's disease, rest eyes open"),
  fromRights('vr-pc-p300', cx['vr-pc-p300'], [vrGroup()], { en: 'P300 on a PC screen and in a VR headset', zh: '电脑屏幕与 VR 头显上的 P300' }, 'Cattan PC/VR P300 dataset'),
  fromRights('gait-eeg', cx['gait-eeg'], [gaitGroup()], { en: 'Treadmill walking at three speeds', zh: '跑步机上三种速度的行走' }, 'Multimodal gait dataset · treadmill walking'),
  fromRights('ysu-async-ssvep', cx['ysu-async-ssvep'], [ysuGroup()], { en: 'Asynchronous SSVEP, control and non-control states', zh: '异步 SSVEP，控制与非控制状态' }),
];

export const datasetBySlug = Object.fromEntries(datasets.map(d => [d.slug, d]));

/* --- The methods -------------------------------------------------------------------- */

export interface MethodEntity {
  slug: MethodSlug;
  name: string;
  family?: string;
  status?: string;
  url?: string;
  /** Every published row for this method, grouped under the dataset it was measured on. */
  groups: (ResultGroup & { dataset: DatasetEntity })[];
}

export const methods: MethodEntity[] = methodSlugs.map(slug => {
  const model = data.models.find(m => (m.id ?? m.name.toLowerCase().replace('+', '-')) === slug
                                   || m.name === methodNames[slug] || (slug === 'cca' && m.name === 'Standard CCA'));
  const groups = datasets.flatMap(d => d.groups
    .map(g => ({ ...g, rows: g.rows.filter(r => r.methodSlug === slug), dataset: d }))
    .filter(g => g.rows.length));
  return { slug, name: methodNames[slug], family: model?.family, status: model?.status, url: model?.url ?? undefined, groups };
});

export const methodBySlug = Object.fromEntries(methods.map(m => [m.slug, m])) as Record<MethodSlug, MethodEntity>;

/** Models listed in the directory that have no published result here, and why. */
export const unmeasuredModels = data.models.filter(m => m.status !== 'Evaluated')
  .map(m => ({ name: m.name, family: m.family, status: m.status, url: m.url ?? undefined }));

export const entityPaths = [
  '/datasets/', ...datasets.map(d => `/datasets/${d.slug}/`),
  '/methods/', ...methods.map(m => `/methods/${m.slug}/`),
];
