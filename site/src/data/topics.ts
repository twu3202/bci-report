import type { Locale } from './i18n';

export type Interval = [number, number];

export interface DeploymentRow {
  id: string;
  track: string;
  protocol_id: string;
  dataset_id: string;
  model: string;
  metric: string;
  value: number;
  confidence_interval_95?: Interval | null;
  participants: number;
  trials: number;
  channels?: number | null;
  window_seconds?: number | null;
  source_sensor?: string | null;
  target_sensor?: string | null;
  modality?: string | null;
  condition?: string | null;
  speed_m_s?: number | null;
  training_regime: string;
  labeled_target_trials?: number | null;
  calibration_blocks?: number[] | null;
  test_blocks?: number[] | null;
  initialization?: string | null;
  head_selection?: string | null;
}

export interface PairedContrast {
  track: string;
  model: string;
  dataset_id?: string;
  modality?: string;
  comparison: string;
  participants: number;
  difference: number;
  paired_participant_bootstrap_95: Interval;
  unit: string;
  interpretation: string;
}

export interface SeedRun {
  seed: number;
  balanced_accuracy: number;
  macro_f1: number;
}

export interface SeedSensitivity {
  model: string;
  protocol: string;
  participants: number;
  trials: number;
  runs: SeedRun[];
  mean_balanced_accuracy: number;
  sample_standard_deviation: number;
  minimum: number;
  maximum: number;
  full_range: number;
  uncertainty_kind: string;
  comparability_note: string;
}

export interface DatasetCitation {
  id: string;
  identity: Record<string, unknown> & {
    title?: string;
    authors?: string[];
    license?: string;
    paper_citation?: string;
    canonical_dataset_citation?: string;
    dataset_citation?: string;
    source_paper_citation?: string;
    paper_doi?: string;
    dataset_doi?: string;
    canonical_version_doi?: string;
    source_paper_doi?: string;
    version?: string;
    representation?: string;
    local_representation?: string;
  };
  primary_sources: string[];
  publication_conditions: string[];
}

export interface DeploymentData {
  schema_version: string;
  status: string;
  generated_at: string;
  metric_units: string;
  rows: DeploymentRow[];
  paired_contrasts: PairedContrast[];
  seed_sensitivity: SeedSensitivity[];
  dataset_citations: DatasetCitation[];
  interpretation_limits: Record<string, string[]>;
  method_references?: Array<Record<string, unknown>>;
}

/**
 * The groups the questions are listed under, in order: on the home page, on the
 * Questions hub (/topics/) and in each topic page's switcher. Labels are in
 * i18n.ts (topicGroupLabels).
 */
export const topicGroups = ['transfer', 'adapting', 'reliability'] as const;
export type TopicGroup = typeof topicGroups[number];

/**
 * Every topic page, in reading order, with its group. The copy (kicker, title,
 * question, summary, detail) lives in i18n.ts `topicCards`, in both languages;
 * this list used to carry a second, English-only copy that nothing rendered.
 * Groups run contiguously, so the order here is the order within each group.
 */
export const topicPages = [
  { slug: 'dry-vs-wet', group: 'transfer' },
  { slug: 'screen-to-vr', group: 'transfer' },
  { slug: 'fewer-electrodes', group: 'transfer' },
  { slug: 'on-the-move', group: 'transfer' },
  { slug: 'calibration-budget', group: 'adapting' },
  { slug: 'model-adaptation', group: 'adapting' },
  { slug: 'does-pretraining-help', group: 'adapting' },
  { slug: 'when-not-to-act', group: 'reliability' },
  { slug: 'clinical-groups', group: 'reliability' },
] as const satisfies readonly { slug: string; group: TopicGroup }[];

/** The topics in one group, in order, each with its position in the whole list. */
export const topicsIn = (group: TopicGroup) =>
  topicPages.map((t, index) => ({ ...t, index })).filter(t => t.group === group);

{
  const seen = topicPages.map(t => t.group).filter((g, i, all) => i === 0 || all[i - 1] !== g);
  if (seen.join() !== topicGroups.join()) throw new Error('topics.ts: topicPages must run group by group, in topicGroups order');
}

export const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
export const pp = (value: number, digits = 1) => `${value >= 0 ? '+' : '−'}${Math.abs(value * 100).toFixed(digits)} pp`;
export const auc = (value: number) => value.toFixed(3);
export const intervalPct = (interval?: Interval | null, digits = 1) =>
  interval ? `${pct(interval[0], digits)}–${pct(interval[1], digits)}` : '—';
export const intervalPp = (interval: Interval, digits = 1, locale: Locale = 'en') =>
  `${interval[0] >= 0 ? '+' : '−'}${Math.abs(interval[0] * 100).toFixed(digits)} ${locale === 'zh' ? '至' : 'to'} ${interval[1] >= 0 ? '+' : '−'}${Math.abs(interval[1] * 100).toFixed(digits)} pp`;
/**
 * Display names for the payload's model ids. Names of published methods stay
 * English in both languages (glossary, i18n.ts); descriptive labels — what a
 * baseline does rather than what it is called — are translated, so the plot
 * and table rows say what the prose beside them says ("单频带 eTRCA").
 * `locale` is required so no caller can quietly print the English on a Chinese page.
 */
const MODEL_LABELS: Record<string, { en: string; zh?: string }> = {
  'random-uniform': { en: 'Uniform random', zh: '均匀随机' },
  'same-frequency-power': { en: 'Same-frequency power', zh: '同频功率' },
  'spectral-ridge-gain-invariant': { en: 'Spectral ridge' },
  'spectral-ridge': { en: 'Spectral ridge' },
  'author-cca': { en: 'Author-style CCA', zh: 'CCA（按原作者设置）' },
  'ensemble-trca': { en: 'Single-band eTRCA', zh: '单频带 eTRCA' },
  'temporal-feature-logistic-regression': { en: 'Temporal-feature L2 logistic regression', zh: '时域特征 L2 逻辑回归' },
  'log-covariance-ridge': { en: 'Log-covariance ridge', zh: '对数协方差岭回归' },
  'labram': { en: 'LaBraM' },
  'cbramod': { en: 'CBraMod' },
  'eegnet': { en: 'EEGNet' },
  'fbcca': { en: 'FBCCA' },
  'cca': { en: 'CCA' },
};
export const modelLabel = (model: string, locale: Locale) => {
  const label = MODEL_LABELS[model];
  return label ? (locale === 'zh' && label.zh) || label.en : model;
};

export const conditionLabel = (condition?: string | null, locale: Locale = 'en') => ({
  en: { standing: 'Standing', slow_walking: 'Slow walk · 0.8 m/s',
        fast_walking: 'Fast walk · 1.6 m/s', slight_running: 'Running · 2.0 m/s' },
  zh: { standing: '站立', slow_walking: '慢走 · 0.8 m/s',
        fast_walking: '快走 · 1.6 m/s', slight_running: '慢跑 · 2.0 m/s' },
}[locale] as Record<string, string>)[condition ?? ''] ?? condition ?? '—';

export const datasetLabel = (dataset: string, locale: Locale = 'en') => ({
  en: { ds003810: 'MI / rest', 'physionet-eegmat-1.0.0': 'Mental workload' },
  zh: { ds003810: '运动想象 / 静息', 'physionet-eegmat-1.0.0': '脑力负荷' },
}[locale] as Record<string, string>)[dataset] ?? dataset;

export const seedProtocolLabel = (protocol: string, locale: Locale = 'en') => ({
  en: { ds005383: 'Semantic ERP', ds006593: 'P300', 'eesm19-scalp-sleep': 'Scalp sleep staging',
        'BETA-posterior4': 'BETA · 4 selected channels', 'BETA-posterior8': 'BETA · 8 selected channels' },
  zh: { ds005383: '语义 ERP', ds006593: 'P300', 'eesm19-scalp-sleep': '头皮睡眠分期',
        'BETA-posterior4': 'BETA · 选定 4 通道', 'BETA-posterior8': 'BETA · 选定 8 通道' },
}[locale] as Record<string, string>)[protocol] ?? protocol;
