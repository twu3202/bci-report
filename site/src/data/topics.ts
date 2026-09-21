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

export const topicPages = [
  {
    slug: 'dry-vs-wet',
    kicker: 'Sensor transfer',
    title: 'Dry vs. wet electrodes',
    summary: 'What changes when a decoder crosses between two native eight-channel recordings from the same 102 people?',
    detail: '2 s SSVEP · 12 targets · balanced accuracy',
  },
  {
    slug: 'on-the-move',
    kicker: 'Motion robustness',
    title: 'On the move',
    summary: 'Standing, walking and running results, with scalp and ear recordings and incompatible time windows kept apart.',
    detail: 'SSVEP balanced accuracy · ERP ROC AUC',
  },
  {
    slug: 'calibration-budget',
    kicker: 'Adaptation budget',
    title: 'How much calibration?',
    summary: 'Twelve, 24 or 48 labeled target trials help some methods more than others—and trial count is not elapsed time.',
    detail: 'Common future blocks · target-only fitting',
  },
  {
    slug: 'does-pretraining-help',
    kicker: 'Representation controls',
    title: 'Does pretraining help?',
    summary: 'Matched pretrained and constructor-random encoders under fixed and train-selected readout settings.',
    detail: 'Two tasks · two encoders · three random initializations',
  },
] as const;

export const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
export const pp = (value: number, digits = 1) => `${value >= 0 ? '+' : '−'}${Math.abs(value * 100).toFixed(digits)} pp`;
export const auc = (value: number) => value.toFixed(3);
export const intervalPct = (interval?: Interval | null, digits = 1) =>
  interval ? `${pct(interval[0], digits)}–${pct(interval[1], digits)}` : '—';
export const intervalPp = (interval: Interval, digits = 1, locale: Locale = 'en') =>
  `${interval[0] >= 0 ? '+' : '−'}${Math.abs(interval[0] * 100).toFixed(digits)} ${locale === 'zh' ? '至' : 'to'} ${interval[1] >= 0 ? '+' : '−'}${Math.abs(interval[1] * 100).toFixed(digits)} pp`;
export const modelLabel = (model: string) => ({
  'random-uniform': 'Uniform random',
  'same-frequency-power': 'Same-frequency power',
  'spectral-ridge-gain-invariant': 'Spectral ridge',
  'spectral-ridge': 'Spectral ridge',
  'author-cca': 'Author-style CCA',
  'ensemble-trca': 'Single-band eTRCA',
  'temporal-feature-logistic-regression': 'Temporal-feature L2 logistic regression',
  'log-covariance-ridge': 'Log-covariance ridge',
  'labram': 'LaBraM',
  'cbramod': 'CBraMod',
  'eegnet': 'EEGNet',
  'fbcca': 'FBCCA',
  'cca': 'CCA',
}[model] ?? model);

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
