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
import adaptation from './adaptation-update.json';
import extension from './extension-update.json';
import large from './large-source-update.json';
import reliable from './reliable-decisions-update.json';
import later from './later-sessions-update.json';
import type { Locale } from './i18n';
import { D as SRD, srFig, srPp, srLo, qName, code as srCode, differenceText, marginText, gateText, floorMarginText,
         ppEntry, entry as srEntry, arm as srArm, type SrEntry, type SrLogR } from './shared-encoder';
import { conditionLabel, modelLabel } from './topics';
import { block as qlBlock, contrast as qlContrast, armName as qlArm, differenceText as qlDifference, marginText as qlMargin,
         gateText as qlGate, qlFig, type QlEntry } from './questions-in-language';
import { modelDirectoryStatus } from './directory-status';
import { FM_ADAPTATION_ANCHOR, FM_ANCHOR, fmAdaptation, fmAdaptationMeta, fmDirectory, fmModelById, fmPageNames, fmRowsByProtocol, fmSlugOf,
         fmResearchUse, fmSlugs, type FmModel, type FmRow, type FmSlug } from './foundation-models';
import { fmZh } from './foundation-models-zh';
import { entityCopy } from './entity-copy';
import { TOPIC_PRINTS } from './foundation-topics';

/** English is required; a missing `zh` renders the English text marked lang="en". */
export type L = { en: string; zh?: string };
export const tr = (l: L, locale: Locale) => (locale === 'zh' && l.zh) || l.en;
export const isEnglishOnly = (l: L, locale: Locale) => locale === 'zh' && !l.zh;

/**
 * `sgn1` is a difference of proportions without its unit, for the lower bound of a
 * percentage-point interval ("+2.3 to +6.9 pp"): the unit is printed once, after
 * the upper bound, as intervalPp prints it (since 2026-10-03). `sgn3` is a signed
 * difference of a unitless quantity (AURC, NLL, ECE) to three decimals, always
 * with its sign (since 2026-10-04). `m2` is a parameter count in millions to two
 * decimals ("69.19M"), as the model directory prints it (v9 directory cards, 2026-10-04).
 * `pp2`, `sgn2` and `pct2` (review of 2026-10-05) print a second decimal where one would read as zero: a
 * difference of −0.03 pp is "−0.03 pp", not "−0.0 pp"; an interval bound of +0.02 and one of exactly 0 no longer
 * both print "+0.0" beside opposite verdicts; one window in 2,160 is a coverage of "0.05%", not "0.0%".
 * `ppr2` and `sgr2` (route 2, 2026-10-07) print a value that is already in percentage points (the route-2 export's
 * `estimate_pp`, `interval_95_pp`) with two decimals, so the 2-pp margin's boundary is visible (+1.98 is not +2.0);
 * `ms2` prints a time in seconds as milliseconds to two decimals (the route-2 ledger's step times, indicative).
 */
export type Fmt = 'pct1' | 'pct1raw' | 'pct2raw' | 'pct2' | 'pp1' | 'pp2' | 'sgn1' | 'sgn2' | 'sgn3' | 'auc3' | 'auc2' | 'num3' | 'count' | 's1' | 'm2'
  | 'ppr2' | 'sgr2' | 'ms2' | 'int0' | 'sig3';
/** A published figure: the raw leaf, the served file it is a leaf of, and how it prints. */
export interface Fig { raw: number; fmt: Fmt; src: string }
/** A difference in percentage points, and an interval's lower bound: a second decimal where one would print ±0.0. */
export const ppFmt = (raw: number): Fmt => Math.abs(raw * 100) < 0.05 ? 'pp2' : 'pp1';
export const sgnFmt = (raw: number): Fmt => Math.abs(raw * 100) < 0.05 ? 'sgn2' : 'sgn1';
/**
 * A dimensionless value whose size spans many decades (the later-sessions page's continuous-tracking errors and R²):
 * a whole number with thousands separators from 1,000 up, three significant digits where three decimals would print
 * a non-zero value as 0.000, else three decimals.
 */
export const wideFmt = (raw: number): Fmt => Math.abs(raw) >= 1000 ? 'int0' : raw !== 0 && Math.abs(raw) < 0.01 ? 'sig3' : 'num3';
/** A coverage: a second decimal where a non-zero share would print 0.0%. */
export const covFmt = (raw: number): Fmt => raw > 0 && raw < 0.0005 ? 'pct2' : 'pct1';

const minus = (s: string) => s.replace(/^-/, '−');
/** Kept in step with the formatters in check-workbench.mjs. */
export function formatFig(f: Fig): string {
  switch (f.fmt) {
    case 'pct1': return `${(f.raw * 100).toFixed(1)}%`;
    case 'pct1raw': return `${f.raw.toFixed(1)}%`;
    case 'pct2raw': return `${f.raw.toFixed(2)}%`;
    case 'pp1': return `${f.raw >= 0 ? '+' : '−'}${Math.abs(f.raw * 100).toFixed(1)} pp`;
    case 'pp2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw * 100).toFixed(2)} pp`;
    case 'sgn2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw * 100).toFixed(2)}`;
    case 'pct2': return `${(f.raw * 100).toFixed(2)}%`;
    case 'sgn1': return `${f.raw >= 0 ? '+' : '−'}${Math.abs(f.raw * 100).toFixed(1)}`;
    case 'sgn3': return `${f.raw >= 0 ? '+' : '−'}${Math.abs(f.raw).toFixed(3)}`;
    case 'auc3': return f.raw.toFixed(3);
    case 'auc2': return f.raw.toFixed(2);
    case 'num3': return minus(f.raw.toFixed(3));
    case 'count': return f.raw.toLocaleString('en-US');
    case 's1': return `${f.raw.toFixed(1)} s`;
    case 'm2': return `${(f.raw / 1e6).toFixed(2)}M`;
    case 'ppr2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw).toFixed(2)} pp`;
    case 'sgr2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw).toFixed(2)}`;
    case 'ms2': return `${(f.raw * 1000).toFixed(2)} ms`;
    case 'int0': return minus(Math.round(f.raw).toLocaleString('en-US'));
    case 'sig3': return minus(f.raw.toPrecision(3));
  }
}

/**
 * A short reading printed under a row's figure, in each language: text, and
 * figures as `Fig`s so the counts in it are re-read from the served file like any
 * other. Figures come in the same order in both languages (figure parity).
 */
export type RowNote = Record<Locale, (string | Fig)[]>;

export interface ResultRow {
  /** Locale-free page path, with an anchor where the figure's section has one. */
  path: string;
  /** The method's English name: its identity in structured data and links. */
  method: string;
  /** What the page prints for it, where a descriptive name has a Chinese one. */
  label?: L;
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
  /**
   * A count of records that are not proven unique people (the later-sessions page's Forenzo cohorts): printed in the
   * people column as records, in place of `people`, which is then 0.
   */
  records?: Fig;
  /** What the figure may and may not be read as, printed beside it. */
  note?: RowNote;
}

export interface ResultGroup {
  id: string;
  title: L;
  /** Chance level where the payload records one. */
  chance?: Fig;
  /** The plot's reading key, where the shared one would mislead (Dreem: no chance line, by design). */
  plotLegend?: L;
  path: string;
  rows: ResultRow[];
  /**
   * Methods of this group that were not run, with the export's reason: a dash and
   * a sentence, never a zero (the v9 BrainOmni cells on the one-second ERP protocols).
   */
  notRun?: { method: string; methodSlug?: MethodSlug; reason: string }[];
  /**
   * A v9 group (2026-10-04): the protocol whose page lists every weights licence. The group prints the weights
   * terms of the checkpoints in its rows beside them, and links that list (review of 2026-10-05).
   */
  fmTerms?: string;
  /**
   * A route-1 group (review of 2026-10-05): the protocol whose boundary, with the route's limitations that bear on every
   * figure in the group, is printed under its rows from the export (reliable-decisions-limits.ts), linking the rest.
   */
  rdLimits?: 'arithmetic-rest' | 'beta-8ch' | 'mi-rest';
  /**
   * A route-2 group (2026-10-07): the dataset whose limitations print under its rows (shared-encoder.ts
   * `groupLimits`), with the margin rule; on BOAS also the three stated gaps, the participants' wording, what is not
   * evaluated and the credit, so a BOAS figure never stands without them on any page (dataset or method).
   */
  srNotes?: 'openbmi' | 'boas' | 'eesm19';
  /**
   * A route-3 group (2026-10-08): the dataset whose route-3 limitations print under its rows (ResultGroups.astro); on
   * BOAS also the three stated gaps, the participants' wording, what is not evaluated and the credit (BoasGaps).
   */
  qlNotes?: 'beta' | 'boas';
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
  /**
   * A source whose register entry prints its consent and ethics statements beside its credit (BOAS, 2026-10-07:
   * the ethics committee and reference, written consent, and that its three gaps are stated with every figure).
   */
  rightsNote?: 'boas';
}

const MVP = 'experiments.json', DEP = 'deployment-topics.json', EVI = 'evidence-update.json',
      CLI = 'clinical-update.json', CTX = 'context-update.json', ADA = 'adaptation-update.json',
      EXT = 'extension-update.json', LSU = 'large-source-update.json', RDU = 'reliable-decisions-update.json';
const LTS = 'later-sessions-update.json';
const fig = (raw: number, fmt: Fmt, src: string): Fig => ({ raw, fmt, src });
const pair = (iv: number[] | null | undefined, fmt: Fmt, src: string): [Fig, Fig] | undefined =>
  iv ? [fig(iv[0], fmt, src), fig(iv[1], fmt, src)] : undefined;

/* --- Methods that get a page -------------------------------------------------- */

const coreMethodSlugs = ['eegnet', 'labram', 'cbramod', 'shallowfbcspnet', 'deep4net', 'csp-lda',
                         'cca', 'fbcca', 'etrca'] as const;
// The v9 foundation models (2026-10-04): one page per model family (foundation-models.ts).
export const methodSlugs = [...coreMethodSlugs, ...fmSlugs] as const;
export type MethodSlug = typeof coreMethodSlugs[number] | FmSlug;
export const isFmSlug = (slug: string): slug is FmSlug => (fmSlugs as readonly string[]).includes(slug);
/** Model ids as the payloads write them → the method page they belong to. */
const METHOD_OF: Record<string, MethodSlug> = {
  eegnet: 'eegnet', labram: 'labram', cbramod: 'cbramod', shallowfbcspnet: 'shallowfbcspnet',
  deep4net: 'deep4net', 'csp-lda': 'csp-lda', cca: 'cca', 'author-cca': 'cca', fbcca: 'fbcca',
  'ensemble-trca': 'etrca',
};
/** The method page a payload model id belongs to, if it has one (a v9 checkpoint: its family's page). */
export const methodSlugOf = (id: string): MethodSlug | undefined => METHOD_OF[id] ?? fmSlugOf(id);
export const methodNames: Record<MethodSlug, string> = {
  eegnet: 'EEGNet', labram: 'LaBraM', cbramod: 'CBraMod', shallowfbcspnet: 'ShallowFBCSPNet',
  deep4net: 'Deep4Net', 'csp-lda': 'CSP+LDA', cca: 'CCA', fbcca: 'FBCCA', etrca: 'eTRCA',
  ...fmPageNames,
};

/* --- Labels ------------------------------------------------------------------- */

const BA: L = { en: 'Balanced accuracy', zh: '平衡准确率' };
const AUROC: L = { en: 'AUROC' };
const ROC_AUC: L = { en: 'ROC AUC' };
// The Chinese names the unit once, beside the first "pp" a reader meets on the page.
const DIFF: L = { en: 'Paired difference', zh: '配对差值（百分点）' };
const sensor = { wet: { en: 'wet', zh: '湿电极' }, dry: { en: 'dry', zh: '干电极' } } as Record<string, { en: string; zh: string }>;
const cap = (s: string) => s[0].toUpperCase() + s.slice(1);
/** A display label: the Chinese only where it differs from the English name. */
const lbl = (en: string, zh?: string): L => (zh && zh !== en ? { en, zh } : { en });
/** The label a row prints, in the page's language. */
export const methodLabel = (r: ResultRow, locale: Locale) => tr(r.label ?? { en: r.method }, locale);
export const methodLabelIsEnglish = (r: ResultRow, locale: Locale) => isEnglishOnly(r.label ?? { en: r.method }, locale);

/* --- Core matrix (mvp.json) ------------------------------------------------------ */

const MVP_SLUG: Record<string, string> = {
  ds003810: 'ds003810', EEGMAT: 'eegmat', 'EESM19 scalp subset': 'eesm19', BETA: 'beta',
  'TMNRED / ds005383': 'tmnred', ds006593: 'ds006593', ds005342: 'ds005342',
};
/** The dataset page of a core-matrix dataset, by the name the payload gives it. */
export const datasetSlugOf = (name: string): string | undefined => MVP_SLUG[name];
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

// Each core-matrix group links to its protocol's own page (/protocols/<id>/),
// where the split, electrodes, window and training mode behind these figures
// are printed. It used to link to the home page's matrix, which always opened
// on the first protocol.
function mvpGroups(datasetName: string): ResultGroup[] {
  return data.tracks.filter(t => t.dataset === datasetName).map(t => {
    const rows: ResultRow[] = [];
    const path = `/protocols/${t.id}/`;
    for (const r of t.rows) {
      const base = { path, method: r.name, methodSlug: METHOD_OF[r.id],
                     condition: { en: t.subtitle }, people: r.subjects ?? t.subjects };
      if (t.type === 'tradeoff') {
        rows.push({ ...base, metric: { en: 'Command detection ≤3 s', zh: '指令检出率 ≤3 秒' }, value: fig(r.y, 'pct1raw', MVP) });
        rows.push({ ...base, metric: { en: 'Idle false activation', zh: '空闲误触发率' }, value: fig(r.x, 'pct1raw', MVP) });
      } else {
        rows.push({ ...base, metric: BA, value: fig(r.y, 'pct1raw', MVP), interval: pair(r.interval, 'pct1raw', MVP) });
      }
    }
    return { id: t.id, title: trackTitles[t.id] ?? { en: t.title }, path, rows,
             chance: t.chanceLevel != null ? fig(t.chanceLevel, 'pct1raw', MVP) : undefined };
  });
}

/* --- v9 foundation models (foundation-models-update.json, 2026-10-04) ------------------- */

// The v9 rows of a core protocol: a group of their own beside the core-matrix group, never
// merged into it, read with the protocol page's v9 section. Figures come from the
// protocol's v9 CSV (percent, as the core results CSVs), so ties print as the approved
// handoff prints them. The group id ends in `-foundation-v9`, not in a track id: the
// protocol checks read `…-<track id>` as the core-matrix group.
const FM_MODE_ZH: Record<string, string> = {
  'Frozen encoder + ridge head': '冻结编码器 + 岭回归分类头',
  'Frozen encoder + linear head': '冻结编码器 + 线性分类头',
};
export const fmModeLabel = (mode: string): L => {
  if (!FM_MODE_ZH[mode]) throw new Error(`entities.ts: no Chinese for the training mode ${mode}`);
  return { en: mode, zh: FM_MODE_ZH[mode] };
};
const fmExposureNote = (r: { exposure: { status: string; statement: string } }): RowNote | undefined => r.exposure.status === 'not_exposed' ? undefined : {
  en: [`Pretraining exposure: ${r.exposure.statement}.`],
  zh: [`是否出现在预训练数据中：${fmZh[r.exposure.statement]}。`],
};
/**
 * ZUNA 1.1's model-card sentence travels with every one of its rows, here as on the protocol and topic pages
 * (review of 2026-10-05), after any other reading of the row.
 */
const withResearchUse = (model: FmModel, note: RowNote | undefined): RowNote | undefined => !fmResearchUse(model) ? note : {
  en: [...(note?.en ?? []), ...(note ? [' '] : []), entityCopy.en.researchUse],
  zh: [...(note?.zh ?? []), entityCopy.zh.researchUse],
};
function fmGroups(datasetName: string): ResultGroup[] {
  return data.tracks.filter(t => t.dataset === datasetName).map(t => {
    const path = `/protocols/${t.id}/#${FM_ANCHOR}`;
    const rows: ResultRow[] = [], notRun: NonNullable<ResultGroup['notRun']> = [];
    for (const r of fmRowsByProtocol[t.id]) {
      const ablation = r.model.panel !== 'matrix', mode = fmModeLabel(r.mode);
      const base = { path, method: r.model.name, methodSlug: r.model.slug as MethodSlug,
                     condition: ablation ? { en: `${mode.en} · masking ablation`, zh: `${mode.zh} · 掩码消融` } : mode };
      if (r.status !== 'complete') { notRun.push({ method: r.model.name, methodSlug: r.model.slug, reason: r.reason! }); continue; }
      const people = r.people!.raw, note = fmExposureNote(r);
      if (t.type === 'tradeoff') {
        const i = r.idle!;
        rows.push({ ...base, people, metric: { en: 'Commands detected ≤3 s', zh: '检出的指令 ≤3 秒' }, value: i.detected, of: i.commandTrials,
          note: withResearchUse(r.model, { en: [i.abstain, ' of ', r.people!, ' people always abstained', ...(note ? ['. ', ...note.en] : ['.'])],
                  zh: [i.abstain, ' 名始终拒识（共 ', r.people!, ' 名被试）', ...(note ? ['；', ...note.zh] : ['。'])] }) });
        rows.push({ ...base, people, metric: { en: 'Idle false activations', zh: '空闲误触发' }, value: i.falseActivations, of: i.idleTrials,
          note: withResearchUse(r.model, undefined) });
      } else {
        rows.push({ ...base, people, metric: BA, value: r.primary!, interval: r.interval, note: withResearchUse(r.model, note) });
      }
    }
    const chance = fmRowsByProtocol[t.id].find(r => r.chance)?.chance;
    const core = trackTitles[t.id];
    return {
      id: `${t.id}-${FM_ANCHOR}`,
      title: { en: core.en.replace('Core matrix · ', 'Further foundation encoders, frozen · '), zh: core.zh!.replace('核心矩阵 · ', '更多基础模型编码器（冻结）· ') },
      path, rows, chance, notRun, fmTerms: t.id,
    };
  });
}

/**
 * The v9 EEGMAT adaptation (2026-10-04): nine encoders, the 1 October recipe unchanged,
 * a trained head on the frozen encoder against rank-4 LoRA, three seeds. One fixed
 * recipe on one task, not a ranking; LoRA budgets differ by model, so each change
 * carries its trainable-parameter counts and the people behind it.
 */
function fmAdaptationGroup(): ResultGroup {
  const path = `/protocols/arithmetic-rest/#${FM_ADAPTATION_ANCHOR}`;
  const people = fmAdaptationMeta.people.raw;
  return {
    id: 'eegmat-v9-adaptation',
    title: { en: 'Model adaptation, further encoders · new people, same task, one fixed recipe (not a ranking)', zh: '模型适配（更多编码器）· 新被试、同一任务、一个固定方案（不是排名）' },
    path, chance: fmAdaptationMeta.chance, fmTerms: 'arithmetic-rest',
    rows: fmAdaptation.flatMap(a => {
      const base = { path, method: a.model.name, methodSlug: a.model.slug as MethodSlug, people };
      const c = a.change;
      // ZUNA 1.1: exposure unknown and research use only, on each of its rows, as its frozen row says.
      const tail = (n: RowNote): RowNote => { const x = fmExposureNote(a); const y = x ? { en: [...n.en, ' ', ...x.en], zh: [...n.zh, ...x.zh] } : n; return withResearchUse(a.model, y)!; };
      return [
        { ...base, condition: { en: 'Frozen encoder + trained head', zh: '冻结编码器 + 训练的分类头' }, metric: BA, value: a.frozen.ba, interval: a.frozen.interval,
          note: tail({ en: [a.frozen.trainable, ' trainable parameters.'], zh: [a.frozen.trainable, ' 个可训练参数。'] }) },
        { ...base, condition: { en: 'LoRA rank 4 + head', zh: '秩为 4 的 LoRA + 分类头' }, metric: BA, value: a.lora.ba, interval: a.lora.interval,
          note: tail({ en: [a.lora.trainable, ' trainable parameters.'], zh: [a.lora.trainable, ' 个可训练参数。'] }) },
        { ...base, condition: { en: 'LoRA minus frozen + head, same people and folds', zh: 'LoRA 减冻结 + 分类头，相同被试与折' }, metric: DIFF,
          value: c.mean, interval: c.interval,
          note: tail({ en: [c.helped, ' people improved, ', c.harmed, ' got worse, ', c.tied, ' unchanged',
                       c.excludesZero ? '. The interval excludes zero.' : '. The interval includes zero: no change is established.'],
                  zh: [c.helped, ' 人提升、', c.harmed, ' 人变差、', c.tied, ' 人不变',
                       c.excludesZero ? '。区间不含零。' : '。区间包含零：不能认定有变化。'] }) },
      ];
    }),
  };
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
    path: DEP_TRACK[r.track].path, method: modelLabel(r.model, 'en'), label: lbl(modelLabel(r.model, 'en'), modelLabel(r.model, 'zh')),
    methodSlug: METHOD_OF[r.model],
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
        method: 'Log-bandpower logistic regression', label: lbl('Log-bandpower logistic regression', '对数频带功率逻辑回归'),
        labels: { in_ear: { en: 'Four in-ear channels', zh: '4 个耳道内通道' }, scalp: { en: 'Six scalp electrodes', zh: '6 个头皮电极' } } as Record<string, L>,
        diff: { en: 'Scalp minus in-ear, same epochs', zh: '头皮减耳道内，相同数据帧' } }
    : { title: { en: 'Fewer electrodes · four posterior vs. all sixteen', zh: '更少的电极 · 后部 4 个与全部 16 个' }, path: '/topics/fewer-electrodes/#posterior-subset',
        method: 'Relative band-power logistic regression', label: lbl('Relative band-power logistic regression', '相对频带功率逻辑回归'),
        labels: { posterior4: { en: 'Four posterior electrodes', zh: '后部 4 个电极' }, all16: { en: 'All sixteen electrodes', zh: '全部 16 个电极' } } as Record<string, L>,
        diff: { en: 'All sixteen minus four posterior', zh: '全部 16 个减后部 4 个' } };
  const people = r.cohort.people;
  return {
    id, title: fewer.title, path: fewer.path.split('#')[0], chance: fig(r.chance_level, 'pct1', EVI),
    rows: [
      ...r.configurations.map((c: any) => ({ path: fewer.path, method: fewer.method, label: fewer.label, condition: fewer.labels[c.id], metric: BA,
        value: fig(c.mean_balanced_accuracy, 'pct1', EVI), interval: pair(c.balanced_accuracy_bootstrap_95, 'pct1', EVI), people })),
      { path: fewer.path, method: fewer.method, label: fewer.label, condition: fewer.diff, metric: DIFF,
        value: fig(r.paired_difference.mean, 'pp1', EVI), interval: pair(r.paired_difference.bootstrap_95, 'pp1', EVI), people },
    ],
  };
}

function phantomGroup(): ResultGroup {
  const r = ev.phantom as any;
  const path = '/topics/on-the-move/#phantom-heading';
  const method = 'Fixed multi-output ridge regression', label = lbl(method, '固定的多输出岭回归');
  return {
    id: 'phantom', title: { en: 'Movement · physical head phantom (engineering check)', zh: '运动 · 物理头模（工程对照）' }, path: '/topics/on-the-move/',
    rows: r.conditions.flatMap((c: any) => [
      { path, method, label, condition: { en: c.condition }, metric: { en: 'Signed correlation r', zh: '有符号相关 r' },
        value: fig(c.signed_correlation_r.value, 'num3', EVI), people: 0 },
      { path, method, label, condition: { en: c.condition }, metric: { en: 'Predictive R²', zh: '预测 R²' },
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
      const base = { path, method: m.label, label: lbl(m.label, ({ spectral_logistic: '相对频谱逻辑回归', demographics_only: '只用年龄和性别' } as Record<string, string>)[m.id]), comparator, condition: comparator ? { en: 'Age and sex only · no EEG', zh: '只用年龄与性别 · 不用 EEG' } : { en: 'Resting-state EEG, eyes open', zh: '睁眼静息态 EEG' }, people: r.cohort.people };
      return [
        { ...base, metric: BA, value: fig(m.mean_balanced_accuracy, 'pct1', CLI), interval: pair(m.balanced_accuracy_bootstrap_95, 'pct1', CLI) },
        { ...base, metric: AUROC, value: fig(m.auroc, 'auc2', CLI) },
      ];
    }),
  };
}

const vrLabel = (m: { id: string; label: string }) =>
  lbl(m.label, ({ mean_window_logreg: '窗口均值逻辑回归', spatiotemporal_shrinkage_lda: '时空收缩 LDA' } as Record<string, string>)[m.id]);

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
      { path, method: m.label, label: vrLabel(m), condition: timing[t], metric: BA, value: fig(m.balanced_accuracy.mean, 'pct1', CTX),
        interval: pair(m.balanced_accuracy.bootstrap_95, 'pct1', CTX), people: r.cohort.people },
      { path, method: m.label, label: vrLabel(m), condition: timing[t], metric: AUROC, value: fig(m.auroc.mean, 'auc3', CTX),
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
      path, method: m.label, label: lbl(m.label, ({ spectral_logistic: '相对频谱频带', nuisance_logistic: '运动干扰特征' } as Record<string, string>)[m.id]), comparator: m.id === 'nuisance_logistic',
      condition: m.id === 'nuisance_logistic' ? { en: 'Movement-nuisance features, not brain signal', zh: '运动干扰特征，不是脑信号' } : { en: 'Relative spectral bands, 19 scalp channels', zh: '相对频带功率，19 个头皮通道' },
      metric: BA, value: fig(m.balanced_accuracy, 'pct1', CTX), interval: pair(m.balanced_accuracy_bootstrap_95, 'pct1', CTX),
      people: r.cohort.people_scored,
    })),
  };
}

function ysuGroup(): ResultGroup {
  const r = cx['ysu-async-ssvep'];
  const path = '/topics/when-not-to-act/#non-control-pilot';
  const w = r.control_windows, method = 'Fixed CCA with rejection', label = lbl(method, '带拒识的固定 CCA'), people = r.people;
  const intended = { en: 'Command intended', zh: '有意发出指令' };
  // The same renderings as the topic page (when-not-to-act.astro, ncCondition).
  const noCommand: Record<string, string> = { 'central image, flicker off': '注视中央图像，闪烁关闭',
    'looking at a white wall, resting': '看着白墙休息', 'central image while the surrounding stimuli flicker': '注视中央，周围目标在闪烁' };
  return {
    id: 'ysu-async-ssvep', title: { en: 'When not to act · four-person development pilot', zh: '何时不该执行 · 四人开发试点' }, path: '/topics/when-not-to-act/',
    rows: [
      { path, method, label, condition: intended, metric: { en: 'Frequency recognised', zh: '频率识别正确' }, value: fig(w.frequency_recognised, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      { path, method, label, condition: intended, metric: { en: 'Accepted (coverage)', zh: '被接受（覆盖率）' }, value: fig(w.accepted, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      { path, method, label, condition: intended, metric: { en: 'Accepted and correct', zh: '被接受且正确' }, value: fig(w.accepted_and_correct, 'count', CTX), of: fig(w.tested, 'count', CTX), people },
      ...r.false_acceptance.map((f: any) => ({ path, method, label, condition: { en: `No command · ${f.condition}`, zh: noCommand[f.condition] && `无意发出指令 · ${noCommand[f.condition]}` },
        metric: { en: 'Accepted by mistake (per window)', zh: '误接受（按窗口）' }, value: fig(f.accepted, 'count', CTX), of: fig(f.tested, 'count', CTX), people })),
    ],
  };
}

/** The same source, twenty further people, two rejection rules fixed before scoring (2026-10-02). */
function ysuExtensionGroup(): ResultGroup {
  const r = extension.results['ysu-async-ssvep-extension'];
  const path = '/topics/when-not-to-act/#non-control';
  const method = 'Fixed CCA with rejection', label = lbl(method, '带拒识的固定 CCA'), people = r.cohort.people;
  const rule: Record<string, L> = {
    global: { en: 'Global threshold, fixed on the pilot', zh: '全局阈值，在试点上固定' },
    personal: { en: `Personal threshold, ${r.rules[1].target_person_labels} own windows`, zh: `逐人阈值，用自己的 ${r.rules[1].target_person_labels} 个窗口` },
  };
  const state: Record<string, L> = {
    NS1: { en: 'central image, flicker off', zh: '注视中央图像，闪烁关闭' },
    NS2: { en: 'white wall, resting', zh: '看着白墙休息' },
    NS3: { en: 'central image, surround flickering', zh: '注视中央，周围在闪烁' },
  };
  const d = r.paired_difference;
  return {
    id: 'ysu-async-ssvep-extension', title: { en: `When not to act · ${people} further people, two rejection rules`, zh: `何时不该执行 · 另外 ${people} 名被试，两种拒识规则` },
    path: '/topics/when-not-to-act/',
    rows: [
      ...r.rules.flatMap(x => {
        const w = x.control_windows, c = rule[x.id];
        const base = { path, method, label, people, condition: c };
        return [
          { ...base, metric: { en: 'Detection balanced accuracy', zh: '检测平衡准确率' },
            value: fig(x.detection_balanced_accuracy.mean, 'pct1', EXT), interval: pair(x.detection_balanced_accuracy.bootstrap_95, 'pct1', EXT) },
          { ...base, metric: { en: 'Command windows accepted (coverage)', zh: '被接受的指令窗口（覆盖率）' }, value: fig(w.accepted, 'count', EXT), of: fig(w.tested, 'count', EXT) },
          { ...base, metric: { en: 'Accepted and correct', zh: '被接受且正确' }, value: fig(w.accepted_and_correct, 'count', EXT), of: fig(w.tested, 'count', EXT) },
          { ...base, metric: { en: 'Correct among accepted, mean over people', zh: '被接受窗口中的正确率，各被试均值' }, value: fig(x.accepted_window_accuracy_mean_over_people, 'pct1', EXT) },
          ...x.false_acceptance.map(f => ({ ...base, condition: { en: `${c.en} · no command · ${state[f.state].en}`, zh: `${c.zh} · 无指令 · ${state[f.state].zh}` },
            metric: { en: 'Accepted by mistake (per window)', zh: '误接受（按窗口）' }, value: fig(f.accepted, 'count', EXT), of: fig(f.tested, 'count', EXT) })),
        ];
      }),
      { path, method, label, people, condition: { en: 'Personal minus global, same people and windows', zh: '逐人减全局，相同被试与窗口' },
        metric: { en: 'Paired difference, detection balanced accuracy', zh: '配对差值，检测平衡准确率' },
        value: fig(d.mean, 'pp1', EXT), interval: pair(d.bootstrap_95, 'pp1', EXT),
        // The people behind the mean, as the topic page prints them: how many, never which.
        note: { en: [fig(d.helped, 'count', EXT), ' people improved, ', fig(d.harmed, 'count', EXT), ' got worse, ', fig(d.tied, 'count', EXT), ' unchanged'],
                zh: [fig(d.helped, 'count', EXT), ' 人提升、', fig(d.harmed, 'count', EXT), ' 人变差、', fig(d.tied, 'count', EXT), ' 人不变'] } },
    ],
  };
}

/**
 * LTRSVP: train on one recording at one image rate, test on a different recording
 * (2026-10-02). Run b is the later recording only within a rate: across rates the
 * study's order was ascending and how the released files map onto it is not
 * documented, so the title does not call the test recording later.
 */
function ltrsvpGroup(): ResultGroup {
  const r = extension.results['ltrsvp-rate-transfer'];
  const path = '/topics/screen-to-vr/#image-rate';
  const method = 'Logistic regression on 100-ms means', label = lbl(method, '100 毫秒均值逻辑回归'), people = r.cohort.people;
  const d = r.paired_difference;
  return {
    id: 'ltrsvp-rate-transfer', title: { en: 'Image rate · trained on one recording at one rate, tested on a different recording', zh: '图像速率 · 在一种速率的一段记录上训练、在另一段记录上测试' },
    path: '/topics/screen-to-vr/', chance: fig(r.chance_level, 'pct1', EXT),
    rows: [
      ...r.matrix.map(m => ({ path, method, label, people,
        condition: { en: `Trained at ${m.train_rate_hz} Hz (run a), tested at ${m.test_rate_hz} Hz (run b)`, zh: `${m.train_rate_hz} Hz a 段训练，${m.test_rate_hz} Hz b 段测试` },
        metric: BA, value: fig(m.balanced_accuracy.mean, 'pct1', EXT), interval: pair(m.balanced_accuracy.bootstrap_95, 'pct1', EXT) })),
      { path, method, label, people, condition: { en: 'Trained at 5 Hz minus trained at 10 Hz, same 10-Hz test images', zh: '5 Hz 训练减 10 Hz 训练，相同的 10 Hz 测试图像' },
        metric: DIFF, value: fig(d.mean, 'pp1', EXT), interval: pair(d.bootstrap_95, 'pp1', EXT),
        // The reading the topic page gives, beside the number it qualifies. Both
        // clauses are flags in the export, which refuses to build if the first stops being true.
        note: {
          en: [fig(d.people_lower, 'count', EXT), ' people lower, ', fig(d.people_higher, 'count', EXT), ' higher',
               ...(d.interval_crosses_zero ? ['. The interval crosses zero: no change is established'] : []),
               ...(r.not_causal ? ['. Rate and recording change together: not a causal effect of image rate.'] : ['.'])],
          zh: [fig(d.people_lower, 'count', EXT), ' 人更低、', fig(d.people_higher, 'count', EXT), ' 人更高',
               ...(d.interval_crosses_zero ? ['。区间跨过零，不能认定有变化'] : []),
               ...(r.not_causal ? ['。速率与记录一起变化：不是图像速率的因果效应。'] : ['。'])],
        } },
    ],
  };
}

// New people, same task, zero labels from the test person. Its page moved from
// calibration-budget to model-adaptation on 2026-10-02.
function adaptationGroup(): ResultGroup {
  const r = adaptation.results['eegmat-labram-adaptation'];
  const path = '/topics/model-adaptation/#adaptation';
  const arm: Record<string, L> = {
    frozen: { en: 'Head only · encoder frozen', zh: '只训分类头 · 编码器冻结' },
    'last-block': { en: 'Last block + head', zh: '最后一个 Transformer 块 + 分类头' },
    'lora-r4': { en: 'LoRA rank 4 + head', zh: '秩为 4 的 LoRA + 分类头' },
  };
  const people = r.cohort.people;
  return {
    id: 'eegmat-labram-adaptation', title: { en: 'Model adaptation · LaBraM on new people, same task, zero labels from the test person', zh: '模型适配 · LaBraM：新被试、同一任务、不使用测试被试的任何标签' },
    path: '/topics/model-adaptation/', chance: fig(r.chance_level, 'pct1', ADA),
    rows: [
      ...r.arms.map(a => ({ path, method: 'LaBraM', methodSlug: 'labram' as MethodSlug, condition: arm[a.id], metric: BA,
        value: fig(a.balanced_accuracy.mean, 'pct1', ADA), interval: pair(a.balanced_accuracy.bootstrap_95, 'pct1', ADA), people })),
      ...r.paired_contrasts.balanced_accuracy.map(c => ({ path, method: 'LaBraM', methodSlug: 'labram' as MethodSlug,
        condition: { en: `${arm[c.arm].en} minus ${arm[c.minus].en.split(' · ')[0].toLowerCase()}`, zh: `${arm[c.arm].zh}减${arm[c.minus].zh.split(' · ')[0]}` },
        metric: DIFF, value: fig(c.mean_change, 'pp1', ADA), interval: pair(c.bootstrap_95, 'pp1', ADA), people })),
    ],
  };
}

/* --- 2026-10-03: Dreem sleep staging, OpenBMI next session ------------------------- */

const ACC: L = { en: 'Accuracy', zh: '准确率' };
const MF1: L = { en: 'Macro F1', zh: '宏平均 F1' };
const KAPPA: L = { en: 'Cohen’s kappa', zh: 'Cohen kappa 系数' };
const STAGE_METRIC: Record<'recall' | 'precision' | 'f1', L> = {
  recall: { en: 'Recall', zh: '召回率' }, precision: { en: 'Precision', zh: '精确率' }, f1: { en: 'F1' },
};
const dreem = large.results['dreem-sleep-baselines'];
type DreemCohort = keyof typeof dreem.cohorts;
type Summary = { mean: number | null; interval_95: number[] | null; nights_defined: number };
export const dreemArmLabel: Record<'training_prior' | 'spectral_ridge', L> = {
  training_prior: { en: 'Training prior', zh: '训练集先验' },
  spectral_ridge: { en: 'Spectral ridge' },
};
export const dreemCohortLabel: Record<DreemCohort, L> = {
  'DOD-H': { en: 'DOD-H · healthy sleepers', zh: 'DOD-H · 健康被试' },
  'DOD-O': { en: 'DOD-O · people with obstructive sleep apnoea', zh: 'DOD-O · 阻塞性睡眠呼吸暂停患者' },
};

/**
 * Dreem: one group per cohort, never one for both. DOD-H and DOD-O are separate
 * experiments — their own models, folds and intervals, recorded at different
 * centres — so the page keeps them apart, and no group pools or compares them.
 * The training prior is a reference, not a decoding model, and has no chance
 * level here: it is the floor the baseline sets. Balanced accuracy comes first,
 * accuracy in the next row, so accuracy is never read alone. A null (precision of
 * a stage never predicted) has no row: it is not a zero, and its recall row says why.
 */
function dreemGroup(id: DreemCohort): ResultGroup {
  const c = dreem.cohorts[id];
  const path = `/topics/sleep-staging/#${id.toLowerCase()}`;
  const people = c.nights;
  const cohort = dreemCohortLabel[id];
  const rows: ResultRow[] = [];
  for (const arm of ['training_prior', 'spectral_ridge'] as const) {
    const a = c.arms[arm] as unknown as Record<string, Summary>;
    const base = { path, method: dreemArmLabel[arm].en, label: dreemArmLabel[arm], comparator: arm === 'training_prior',
                   condition: { en: `${cohort.en}, every night held out once`, zh: `${cohort.zh}，每晚各留出一次` }, people };
    for (const [key, metric, fmt] of [['balanced_accuracy', BA, 'pct1'], ['accuracy', ACC, 'pct1'], ['macro_f1', MF1, 'pct1'],
                                       ['cohen_kappa', KAPPA, 'num3']] as [string, L, Fmt][])
      rows.push({ ...base, metric, value: fig(a[key].mean!, fmt, LSU), interval: pair(a[key].interval_95, fmt, LSU) });
  }
  const d = c.paired_balanced_accuracy;
  rows.push({ path, method: dreemArmLabel.spectral_ridge.en, label: dreemArmLabel.spectral_ridge, people,
    condition: { en: 'Spectral ridge minus training prior, the same nights', zh: 'spectral ridge 减训练集先验，相同的夜晚' },
    metric: { en: 'Paired difference, balanced accuracy', zh: '配对差值（百分点），平衡准确率' },
    value: fig(d.mean, 'pp1', LSU), interval: pair(d.interval_95, 'pp1', LSU),
    note: { en: [fig(d.nights, 'count', LSU), ' nights under both baselines', ...(d.interval_excludes_zero ? ['; the interval excludes zero.'] : ['.'])],
            zh: [fig(d.nights, 'count', LSU), ' 晚，两个基线相同', ...(d.interval_excludes_zero ? ['；区间不含零。'] : ['。'])] } });
  const never = new Set(c.arms.spectral_ridge.stages_never_predicted);
  for (const st of c.arms.spectral_ridge.per_stage) {
    for (const key of ['recall', 'precision', 'f1'] as const) {
      const m = st[key] as unknown as Summary;
      if (m.mean === null) continue;   // not defined on any night: printed nowhere as a number
      // The reading beside the figure: the stage's support (on its recall row), why a stage the
      // ridge never predicts has no precision row, and on how many nights a mean is defined.
      const en: (string | Fig)[] = [], zh: (string | Fig)[] = [];
      if (key === 'recall') {
        en.push(fig(st.support_epochs, 'count', LSU), ` ${st.stage} epochs in the consensus`);
        zh.push(fig(st.support_epochs, 'count', LSU), ` 个 ${st.stage} 数据帧（共识分期）`);
        if (never.has(st.stage)) {
          en.push(`; never predicted on any night, so every one is missed and ${st.stage} precision is not defined (not zero)`);
          zh.push(`；没有一晚预测过 ${st.stage}，所以全部漏掉，${st.stage} 的精确率没有定义（不是零）`);
        }
      }
      if (m.nights_defined < people) {
        en.push(...(en.length ? ['; '] : []), 'defined on ', fig(m.nights_defined, 'count', LSU), ' of ', fig(people, 'count', LSU), ' nights');
        zh.push(...(zh.length ? ['；'] : []), fig(m.nights_defined, 'count', LSU), ' 晚有定义（共 ', fig(people, 'count', LSU), ' 晚）');
      }
      rows.push({ path, method: dreemArmLabel.spectral_ridge.en, label: dreemArmLabel.spectral_ridge,
        condition: { en: `${cohort.en} · stage ${st.stage}`, zh: `${cohort.zh} · ${st.stage} 期` },
        metric: STAGE_METRIC[key], value: fig(m.mean, 'pct1', LSU), interval: pair(m.interval_95, 'pct1', LSU), people,
        note: en.length ? { en: [...en, '.'], zh: [...zh, '。'] } : undefined });
    }
  }
  return {
    id: `dreem-${id.toLowerCase()}`,
    title: { en: `Sleep staging · ${cohort.en} (a separate experiment)`, zh: `睡眠分期 · ${cohort.zh}（独立实验）` },
    path: '/topics/sleep-staging/', rows,
    plotLegend: { en: 'Dot: the mean over nights; line: 95% interval. No dashed line: the training prior is a floor this baseline sets, not a chance level.',
                  zh: '点为各晚均值，横线为 95% 区间。没有虚线：训练集先验是这个基线设定的下限，不是随机水平。' },
  };
}

/** OpenBMI: same person, session 1 to session 2, four calibration budgets (2026-10-03). */
export const openbmiArmLabel: Record<string, L> = {
  'log-covariance-lda': { en: 'Log-covariance + shrinkage LDA', zh: '对数协方差 + 收缩 LDA' },
  'relative-psd-ridge': { en: 'Relative PSD + standardized ridge', zh: '相对 PSD + 标准化岭回归' },
};
function openbmiGroup(): ResultGroup {
  const r = large.results['openbmi-cross-session-calibration'];
  const path = '/topics/calibration-budget/#next-session';
  const people = r.cohort.evaluated;
  const rows: ResultRow[] = [];
  for (const a of r.arms) {
    const base = { path, method: a.label, label: openbmiArmLabel[a.id], people };
    for (const b of a.by_budget)
      rows.push({ ...base, condition: { en: `Session 1 → session 2 · ${b.target_trials} labeled session-2 trials`, zh: `第一次会话 → 第二次会话 · ${b.target_trials} 个第二次会话校准试次` },
        metric: BA, value: fig(b.balanced_accuracy.mean, 'pct1', LSU), interval: pair(b.balanced_accuracy.interval_95, 'pct1', LSU) });
    for (const g of a.calibration_gain)
      rows.push({ ...base, condition: { en: `${g.target_trials} minus 0 labeled session-2 trials, the same people and test trials`, zh: `${g.target_trials} 个减 0 个第二次会话校准试次，相同被试与测试试次` },
        metric: DIFF, value: fig(g.balanced_accuracy_change.mean, 'pp1', LSU), interval: pair(g.balanced_accuracy_change.interval_95, 'pp1', LSU),
        // The people behind the mean, beside it: how many declined, never which.
        note: { en: [fig(g.people_with_any_decline, 'count', LSU), ' of ', fig(g.people, 'count', LSU), ' people declined, ', fig(g.people_with_decline_of_5_points_or_more, 'count', LSU), ' by 5 points or more',
                     ...(g.interval_excludes_zero ? ['.'] : ['. The interval includes zero: the gain is not established.'])],
                zh: [fig(g.people_with_any_decline, 'count', LSU), ' 人下降（共 ', fig(g.people, 'count', LSU), ' 人），其中 ', fig(g.people_with_decline_of_5_points_or_more, 'count', LSU), ' 人下降 5 pp 及以上',
                     ...(g.interval_excludes_zero ? ['。'] : ['。区间包含零：这一提升不能认定。'])] } });
  }
  return {
    id: r.id, title: { en: 'Calibration budget · same person, next session, motor imagery', zh: '校准预算 · 同一被试、下一次会话、运动想象' },
    path: '/topics/calibration-budget/', chance: fig(r.chance_level, 'pct1', LSU), rows,
  };
}

/* --- 2026-10-04: route 1, reliable decisions ------------------------------------------ */

const rd = reliable.results['reliable-decisions'];
/** Route-1 method ids → the method page, and a label where the method is an arm of one. */
export const reliableMethod: Record<string, { slug?: MethodSlug; label: L }> = {
  'spectral-ridge': { label: { en: 'Spectral ridge' } },
  eegnet: { slug: 'eegnet', label: { en: 'EEGNet' } },
  cca: { slug: 'cca', label: { en: 'Standard CCA' } },
  cbramod: { slug: 'cbramod', label: { en: 'CBraMod' } },
  'labram-frozen-ce': { slug: 'labram', label: { en: 'LaBraM · head only, encoder frozen', zh: 'LaBraM · 只训分类头，编码器冻结' } },
  'labram-lora-r4': { slug: 'labram', label: { en: 'LaBraM · LoRA rank 4 + head', zh: 'LaBraM · 秩为 4 的 LoRA + 分类头' } },
};
type RdMethod = { id: string; label: string; fixed_cutoff: { n: number; accepted: number; people_with_nothing_accepted: number };
                  learned_minus_confidence: { error_at_80: { mean: number; interval_95: number[]; excludes_zero: boolean } } };

/**
 * Route 1 on one dataset: for each method, how many trials the fixed threshold
 * (calibrated confidence at least 0.8) accepted, with how many people had nothing
 * accepted beside it, and the learned reject option minus calibrated confidence at
 * 80% coverage, with its verdict. Balanced or uniform protocols, so a method
 * comparison, never a deployment rate. ds003810 is labelled crude.
 */
function reliableGroup(protocol: 'arithmetic-rest' | 'beta-8ch' | 'mi-rest'): ResultGroup {
  const p = (protocol === 'mi-rest' ? rd.robustness.mi_rest : rd.protocols[protocol]) as unknown as
    { people: number; unit: string; methods: RdMethod[] };
  const path = protocol === 'mi-rest' ? '/topics/when-not-to-act/#rd-robustness' : '/topics/when-not-to-act/#reliable-decisions';
  const crude = protocol === 'mi-rest';
  const unit = p.unit === 'windows' ? { en: 'Windows accepted', zh: '被接受的窗口' } : { en: 'Trials accepted', zh: '被接受的试次' };
  const rows: ResultRow[] = [];
  for (const m of p.methods) {
    const who = reliableMethod[m.id];
    const base = { path, method: who.label.en, label: who.label, methodSlug: who.slug, people: p.people };
    const f = m.fixed_cutoff, d = m.learned_minus_confidence.error_at_80;
    rows.push({ ...base, condition: { en: 'Fixed threshold: calibrated confidence at least 0.8', zh: '固定阈值：校准后的置信度不低于 0.8' },
      metric: unit, value: fig(f.accepted, 'count', RDU), of: fig(f.n, 'count', RDU),
      note: { en: [fig(f.people_with_nothing_accepted, 'count', RDU), ' of ', fig(p.people, 'count', RDU), ' people had nothing accepted. A method comparison on a balanced protocol, not a deployment rate.'],
              zh: [`没有任何${p.unit === 'windows' ? '窗口' : '试次'}被接受的被试：`, fig(f.people_with_nothing_accepted, 'count', RDU), ' 名（共 ', fig(p.people, 'count', RDU), ' 名）。这是类别平衡协议上的方法比较，不是部署时的比率。'] } });
    // ds003810's contrasts are secondary (the topic page reads them only as such): the row says so.
    rows.push({ ...base, condition: crude ? { en: 'Learned reject option minus calibrated confidence, same classifier (a secondary contrast)', zh: '可学习的拒识选项减校准后的置信度，同一分类器（次要对比）' }
                                          : { en: 'Learned reject option minus calibrated confidence, same classifier', zh: '可学习的拒识选项减校准后的置信度，同一分类器' },
      metric: { en: 'Error among the 80% most certain, difference', zh: '最有把握的 80% 中的错误率，差值（百分点）' },
      value: fig(d.mean, ppFmt(d.mean), RDU), interval: [fig(d.interval_95[0], ppFmt(d.interval_95[0]), RDU), fig(d.interval_95[1], ppFmt(d.interval_95[1]), RDU)],
      note: d.excludes_zero ? { en: ['Difference resolved: the interval excludes zero.'], zh: ['可以认定有差异：区间不含零。'] }
                            : { en: ['No difference resolved: the interval includes zero.'], zh: ['不能认定有差异：区间包含零。'] } });
  }
  return {
    // One id on every dataset page; method pages prefix the dataset slug. Not `…-<track id>`, which
    // the protocol checks read as a core-matrix group.
    id: 'reliable-decisions',
    title: crude ? { en: 'Reliable decisions · when to decline a decision (crude: ten people)', zh: '可靠的决策 · 什么时候该拒绝作出决定（粗略：10 名被试）' }
                 : { en: 'Reliable decisions · when to decline a decision', zh: '可靠的决策 · 什么时候该拒绝作出决定' },
    path: '/topics/when-not-to-act/', rows, rdLimits: protocol,
  };
}

/* --- 2026-10-07: route 2, one representation and several questions ---------------------- */

const SRBA: L = { en: 'Balanced accuracy', zh: '平衡准确率' };
const SRDIFF: L = { en: 'Paired difference, balanced accuracy', zh: '配对差值（百分点），平衡准确率' };
const SRLOGR: L = { en: 'log R, the dedicated model’s remaining error over the read-out’s', zh: 'log R：专用模型与读出的剩余错误之比' };
const SR_ARM: Record<string, L> = {
  'B-lin': { en: 'fixed heads (B-lin)', zh: '固定分类头（B-lin）' },
  'B-sh': { en: 'shared hidden layer (B-sh)', zh: '共享隐藏层（B-sh）' },
  C1: { en: 'question-conditioned head (C1)', zh: '问题条件化分类头（C1）' },
  A: { en: 'separate model (A)', zh: '分开的模型（A）' },
  'B-lin-fz-sgd': { en: 'fixed heads (B-lin-fz-sgd)', zh: '固定分类头（B-lin-fz-sgd）' },
  'B-sh-fz': { en: 'shared hidden layer (B-sh-fz)', zh: '共享隐藏层（B-sh-fz）' },
  'C1-fz': { en: 'question-conditioned head (C1-fz)', zh: '问题条件化分类头（C1-fz）' },
};
const SR_CONTRAST: Record<string, L> = {
  P1: { en: 'conditioned head minus fixed heads', zh: '问题条件化分类头减固定分类头' },
  P5: { en: 'conditioned head minus the same layer not told the question', zh: '问题条件化分类头减不告知问题的同一隐藏层' },
  // P2 at E1 (and S13-P2, EEGNet from scratch) is small-CNN trunk sharing, not foundation-model sharing (the export's boundary).
  P2: { en: 'fixed heads on one shared small-CNN trunk minus separate models', zh: '一个共享小 CNN 主干上的固定分类头减分开的模型' },
  P4: { en: 'conditioned head minus fixed heads, on frozen CBraMod features', zh: '冻结 CBraMod 特征上，问题条件化分类头减固定分类头' },
  'S13-P1': { en: 'conditioned head minus fixed heads', zh: '问题条件化分类头减固定分类头' },
  'S13-P2': { en: 'fixed heads on one shared small-CNN trunk minus separate models', zh: '一个共享小 CNN 主干上的固定分类头减分开的模型' },
};
const srWho = (level: string) => level === 'E1' ? { method: 'EEGNet', methodSlug: 'eegnet' as MethodSlug } : { method: 'CBraMod', methodSlug: 'cbramod' as MethodSlug };
const srArmKey = (a: string) => a.startsWith('A_') ? 'A' : a;
/** The reading beside a contrast: both flags, the margin with them, the gate; at floor, the margin flag is not read. */
function srReading(e: SrEntry | SrLogR): RowNote {
  const parts = (locale: Locale) => {
    const sep = locale === 'zh' ? '；' : '; ';
    const margin = marginText(e, locale) + (e.gate === 'floor' ? (locale === 'zh' ? `（${floorMarginText.zh}）` : ` (${floorMarginText.en})`) : '');
    const inconclusive = e.wording === 'inconclusive at this sample size' ? (locale === 'zh' ? '：在这个样本量下无法下结论' : ': inconclusive at this sample size') : '';
    // One sentence: in English the second and third readings start in lower case ("2 pp margin not met" stays as it is).
    const low = (t: string) => locale === 'en' ? t.replace(/^[A-Z](?=[a-z])/, c => c.toLowerCase()) : t;
    return [differenceText(e, locale) + sep + low(margin) + inconclusive + sep + low(gateText(e.gate, locale)) + (locale === 'zh' ? '。' : '.')];
  };
  return { en: parts('en'), zh: parts('zh') };
}
function srContrastRow(e: SrEntry, path: string, contrast: L): ResultRow {
  const [lo, hi] = e.interval_95_pp;
  return { path, ...srWho(e.level), condition: { en: `${qName(e.question, 'en')} (${e.question}) · ${contrast.en} (${srCode(e.x, 'en')} − ${srCode(e.y, 'en')})`,
                                                  zh: `${qName(e.question, 'zh')}（${e.question}）· ${contrast.zh}（${srCode(e.x, 'zh')} − ${srCode(e.y, 'zh')}）` },
    metric: SRDIFF, value: srPp(e.estimate_pp), interval: [srLo(lo), srPp(hi)], people: e.included_people, note: srReading(e) };
}
/**
 * Route 2 on one primary dataset (OpenBMI or BOAS): for each primary question, each arm's balanced accuracy at
 * the two primary levels (EEGNet from scratch; heads on frozen CBraMod features), three seeds, and the contrasts
 * with both flags: P1, P5 and P2 at E1, P4 on frozen features; on BOAS also P3, the derivable question. The
 * secondary arms (E2, K-all, …) stay on the topic page.
 */
function sharedGroup(id: 'openbmi' | 'boas'): ResultGroup {
  const d = SRD[id];
  const anchor = id === 'openbmi' ? 'motor-imagery' : 'sleep';
  const path = `/topics/shared-encoder/#${anchor}`;
  const questions = d.questions.filter(q => q.role === 'primary').map(q => q.id);
  const rows: ResultRow[] = [];
  for (const q of questions) {
    for (const [level, arms] of [['E1', ['B-lin', 'B-sh', 'C1', `A_${q}`]], ['L1', ['B-lin-fz-sgd', 'B-sh-fz', 'C1-fz']]] as const) {
      for (const a of arms) {
        // The method is the encoder; the set-up is part of the condition, so the page names its methods EEGNet and CBraMod.
        const x = srArm(d, level, a, q), who = srWho(level), name = SR_ARM[srArmKey(a)];
        rows.push({ path, ...who,
          condition: level === 'E1' ? { en: `${name.en} · ${qName(q, 'en')} (${q}) · trained from scratch, three seeds`, zh: `${name.zh} · ${qName(q, 'zh')}（${q}）· 从头训练，3 个随机种子` }
                                    : { en: `${name.en} · ${qName(q, 'en')} (${q}) · heads on frozen features, three seeds`, zh: `${name.zh} · ${qName(q, 'zh')}（${q}）· 冻结特征上只训分类头，3 个随机种子` },
          metric: SRBA, value: srFig(x.mean, 'pct1'), interval: [srFig(x.interval_95[0], 'pct1'), srFig(x.interval_95[1], 'pct1')], people: x.included_people });
      }
      for (const cid of level === 'E1' ? ['P1', 'P5', 'P2'] : ['P4'])
        rows.push(srContrastRow(ppEntry(d.entries, cid, q, level), path, SR_CONTRAST[cid]));
    }
  }
  if (id === 'boas') {
    const p3 = srEntry(d.entries, 'P3', 'SL-B') as SrLogR;
    rows.push({ path: '/topics/shared-encoder/#sleep-derived', method: 'EEGNet', methodSlug: 'eegnet',
      condition: { en: `${qName('SL-B', 'en')} (SL-B) · its own model, ${srCode(p3.dedicated, 'en')}, against reading it off ${srCode(p3.read_out_of, 'en')}`,
                   zh: `${qName('SL-B', 'zh')}（SL-B）· 它自己的模型 ${srCode(p3.dedicated, 'zh')}，对比从 ${srCode(p3.read_out_of, 'zh')} 读出` },
      metric: SRLOGR, value: srFig(p3.log_r, 'num3'), interval: [srFig(p3.interval_95[0], 'num3'), srFig(p3.interval_95[1], 'num3')],
      people: p3.included_people, note: srReading(p3) });
  }
  return {
    id: 'shared-encoder',
    title: id === 'openbmi' ? { en: 'One model, several questions · motor imagery (route 2)', zh: '一个模型，多个问题 · 运动想象（第二条路线）' }
                            : { en: 'One model, several questions · sleep (route 2)', zh: '一个模型，多个问题 · 睡眠（第二条路线）' },
    // OpenBMI's two questions share one chance level; BOAS's do not (five stages, then two answers), so it has none.
    chance: id === 'openbmi' ? srFig(srArm(d, 'E1', 'B-lin', 'MI-A').chance, 'pct1') : undefined,
    path: '/topics/shared-encoder/', rows, srNotes: id,
  };
}
/**
 * EESM19, the crude replication (S13): 20 people, one seed, EEGNet from scratch, no shared-hidden-layer arm.
 * Arm means come without an interval (one seed); the contrasts carry both flags and their gate.
 */
function sharedEesm19Group(): ResultGroup {
  const d = SRD.eesm19, path = '/topics/shared-encoder/#eesm19', rows: ResultRow[] = [];
  for (const q of d.questions) {
    const p1 = ppEntry(d.secondary, 'S13-P1', q), p2 = ppEntry(d.secondary, 'S13-P2', q);
    const means: [string, number][] = [['B-lin', p1.mean_balanced_accuracy['B-lin']], ['C1', p1.mean_balanced_accuracy.C1], ['A', p2.mean_balanced_accuracy[`A_${q}`]]];
    if (p2.mean_balanced_accuracy['B-lin'] !== p1.mean_balanced_accuracy['B-lin']) throw new Error('entities.ts: EESM19 B-lin differs between its two contrasts');
    for (const [a, v] of means)
      rows.push({ path, method: 'EEGNet', methodSlug: 'eegnet',
        condition: { en: `${SR_ARM[a].en} · ${qName(q, 'en')} (${q}) · trained from scratch, one seed`, zh: `${SR_ARM[a].zh} · ${qName(q, 'zh')}（${q}）· 从头训练，1 个随机种子` },
        metric: SRBA, value: srFig(v, 'pct1'), people: p1.included_people,
        note: { en: ['One seed: a mean with no interval.'], zh: ['1 个随机种子：只有均值，没有区间。'] } });
    rows.push(srContrastRow(p1, path, SR_CONTRAST['S13-P1']), srContrastRow(p2, path, SR_CONTRAST['S13-P2']));
  }
  return { id: 'shared-encoder', title: { en: 'One model, several questions · sleep, the full EESM19 release (crude: 20 people, one seed)',
                                           zh: '一个模型，多个问题 · 睡眠，EESM19 完整版（粗略：20 名被试，1 个随机种子）' },
           path: '/topics/shared-encoder/', rows, srNotes: 'eesm19' };
}

/* --- Later sessions: WBCIC-SHU, longitudinal RSVP, Forenzo (later-sessions-update.json) -------------------- */

/**
 * The topic page these groups are read on, and its sections: the page must carry these anchors, and its topic
 * card must exist in i18n.ts (a group's "Read on" link takes the card's title).
 */
export const LATER_PATH = '/topics/later-sessions/';
const LATER_ANCHOR = { wbcic: 'wbcic-shu', rsvp: 'longitudinal-rsvp', forenzo: 'forenzo' } as const;
const lt = later.results;
/** Labels for the arms these results name, where the Chinese differs (method names stay English). */
export const laterArmLabel: Record<string, L> = {
  source_prior: { en: 'Source-majority prior', zh: '源会话多数类先验' },
  relative_spectral_ridge: { en: 'Relative spectral power + ridge', zh: '相对频谱功率 + 岭回归' },
  frozen_cbramod: { en: 'CBraMod · frozen encoder, session-1 ridge readout', zh: 'CBraMod · 冻结编码器，分类头用第 1 次会话拟合' },
  rsvp: { en: 'Normalized ERP features + logistic/Platt (CPU baseline)', zh: '归一化 ERP 特征 + logistic/Platt（CPU 基线）' },
  ridge: { en: 'Spectral ridge' },
  source_mean: { en: 'Source-mean comparator', zh: '源会话均值对照' },
};

/** WBCIC-SHU, one group per cohort: the two CPU baselines and frozen CBraMod, session 1 to session 3. */
function laterWbcicGroup(c: '2C' | '3C'): ResultGroup {
  const cpu = lt['wbcic-cross-session-cpu'].cohorts[c], fm = lt['wbcic-frozen-cbramod'].cohorts[c];
  const path = `${LATER_PATH}#${LATER_ANCHOR.wbcic}`;
  const n = cpu.people;
  if (fm.people !== n) throw new Error(`entities.ts: WBCIC ${c} cohorts differ between the two results`);
  const name = c === '2C' ? { en: 'two-class motor imagery', zh: '二分类运动想象' } : { en: 'three-class motor imagery', zh: '三分类运动想象' };
  const condition: L = { en: 'Session 1 → session 3 · no session-3 labels', zh: '第 1 次会话 → 第 3 次会话 · 不使用第 3 次会话的标签' };
  const prior = cpu.arms.source_prior, ridge = cpu.arms.relative_spectral_ridge;
  const rows: ResultRow[] = [
    { path, method: laterArmLabel.source_prior.en, label: laterArmLabel.source_prior, comparator: true, condition, metric: BA,
      value: fig(prior.balanced_accuracy.mean, 'pct1', LTS), people: n,
      note: { en: ['One over the number of classes: a floor, not a model.'], zh: ['等于类别数的倒数：是一个下限，不是模型。'] } },
    { path, method: laterArmLabel.relative_spectral_ridge.en, label: laterArmLabel.relative_spectral_ridge, condition, metric: BA,
      value: fig(ridge.balanced_accuracy.mean, 'pct1', LTS), interval: pair(ridge.balanced_accuracy.interval_95, 'pct1', LTS), people: n },
    { path, method: laterArmLabel.relative_spectral_ridge.en, label: laterArmLabel.relative_spectral_ridge,
      condition: { en: 'Minus the source prior, the same people and trials', zh: '减源会话先验，相同被试与试次' }, metric: DIFF,
      value: fig(cpu.paired.balanced_accuracy_difference.mean, 'pp1', LTS),
      interval: pair(cpu.paired.balanced_accuracy_difference.interval_95, 'pp1', LTS), people: n },
    { path, method: 'CBraMod', methodSlug: 'cbramod', label: laterArmLabel.frozen_cbramod, condition, metric: BA,
      value: fig(fm.frozen_cbramod.balanced_accuracy.mean, 'pct1', LTS), interval: pair(fm.frozen_cbramod.balanced_accuracy.interval_95, 'pct1', LTS),
      people: n },
    { path, method: 'CBraMod', methodSlug: 'cbramod', label: laterArmLabel.frozen_cbramod,
      condition: { en: 'Minus the relative spectral ridge, the same people and trials', zh: '减相对频谱功率 + 岭回归，相同被试与试次' }, metric: DIFF,
      value: fig(fm.paired.balanced_accuracy_difference.mean, 'pp1', LTS),
      interval: pair(fm.paired.balanced_accuracy_difference.interval_95, 'pp1', LTS), people: n,
      note: { en: ['A comparison of two fixed pipelines on reused test trials; it does not show that pretraining caused the gain, and whether this checkpoint saw WBCIC-SHU in pretraining is not established.'],
              zh: ['这是两条固定流程在复用的测试试次上的比较，不能说明提升来自预训练；这个检查点的预训练数据中是否出现过 WBCIC-SHU 也没有确定。'] } },
  ];
  return {
    id: `later-wbcic-${c.toLowerCase()}`,
    title: { en: `Later sessions · ${name.en}, session 1 to session 3`, zh: `后续会话 · ${name.zh}，第 1 次会话到第 3 次会话` },
    path, chance: fig(cpu.chance_level, 'pct1', LTS), rows,
  };
}

/** The longitudinal RSVP source: one first-visit baseline at the nominal later visits, and the paired change. */
function laterRsvpGroup(): ResultGroup {
  const r = lt['rsvp-later-visits'];
  const path = `${LATER_PATH}#${LATER_ANCHOR.rsvp}`;
  const base = { path, method: laterArmLabel.rsvp.en, label: laterArmLabel.rsvp, people: r.cohort.people };
  const AP: L = { en: 'Average precision', zh: '平均精确率' };
  const rows: ResultRow[] = [];
  for (const v of r.visits) {
    const condition: L = { en: `Trained at the first visit · nominal ${v.visit}`, zh: `第一次访次训练 · 标称第 ${v.nominal_day} 天` };
    rows.push({ ...base, condition, metric: AUROC, value: fig(v.auroc.mean, 'auc3', LTS), interval: pair(v.auroc.interval_95, 'auc3', LTS),
      note: { en: ['Targets: ', fig(v.target_events, 'count', LTS), ' of ', fig(v.events, 'count', LTS), ' events. AUROC ranks; it is not accuracy.'],
              zh: ['目标事件：', fig(v.target_events, 'count', LTS), ' 个（共 ', fig(v.events, 'count', LTS), ' 个事件）。AUROC 衡量排序，不是准确率。'] } });
    rows.push({ ...base, condition, metric: AP, value: fig(v.average_precision.mean, 'auc3', LTS) });
  }
  const d = r.contrast;
  rows.push({ ...base, condition: { en: 'Day 200 minus Day 7, the same people', zh: '第 200 天减第 7 天，相同被试' },
    metric: { en: 'AUROC difference', zh: 'AUROC 差值' },
    value: fig(d.auroc_difference.mean, 'sgn3', LTS), interval: pair(d.auroc_difference.interval_95, 'sgn3', LTS),
    note: { en: [fig(d.people_declined_by_0_05_or_more, 'count', LTS), ' of ', fig(d.people, 'count', LTS), ' people lost 0.05 AUROC or more. Nominal visit labels: no claim that elapsed time caused it.'],
            zh: [fig(d.people_declined_by_0_05_or_more, 'count', LTS), ' 人下降 0.05 AUROC 及以上（共 ', fig(d.people, 'count', LTS), ' 人）。访次为标称标签：不说明下降由时间流逝造成。'] } });
  return {
    id: 'later-rsvp', title: { en: 'Later sessions · RSVP target detection, first visit to later visits', zh: '后续会话 · RSVP 目标检测，从第一次访次到后续访次' },
    path, rows,
  };
}

/**
 * Forenzo, one group per cohort and response arm: the ridge against the source-mean comparator. A negative result.
 * The two arms are different outcomes on the same rows, so each has its own group, as on the topic page; the paired
 * row carries the cohort's coverage (Main is conditional on its admitted subset).
 */
function laterForenzoGroup(c: 'Main' | 'Transfer Learning', arm: 'historical_decoder_velocity_imitation' | 'constructed_raw_target_displacement_proxy'): ResultGroup {
  const r = lt['forenzo-continuous-control'];
  const cohort = (r.cohorts as Record<string, any>)[c];
  const a = cohort.arms[arm];
  if (!a) throw new Error(`entities.ts: Forenzo ${c} has no ${arm} arm`);
  const path = `${LATER_PATH}#${LATER_ANCHOR.forenzo}`;
  const ERR: L = { en: 'Normalized RMSE (lower is better)', zh: '归一化 RMSE（越低越好）' };
  const PDIFF: L = { en: 'Paired difference in normalized RMSE', zh: '归一化 RMSE 的配对差值' };
  // Each arm with its label, beside every figure: the two arms are different outcomes, never compared.
  const armName: Record<string, L> = {
    historical_decoder_velocity_imitation: { en: 'Historical decoder velocity (historical decoder imitation, not intended motion)', zh: '历史解码器速度（模仿历史解码器，不是意图运动）' },
    constructed_raw_target_displacement_proxy: { en: 'Constructed displacement proxy (constructed proxy)', zh: '构造的位移代理变量（构造的代理变量）' },
  };
  const armShort: Record<string, L> = {
    historical_decoder_velocity_imitation: { en: 'historical decoder velocity', zh: '历史解码器速度' },
    constructed_raw_target_displacement_proxy: { en: 'constructed displacement proxy', zh: '构造的位移代理变量' },
  };
  // Errors span several decades: thousands separators from 1,000 up (wideFmt).
  const w = (x: number) => fig(x, wideFmt(x), LTS);
  const pr = (iv: number[]) => [w(iv[0]), w(iv[1])] as [Fig, Fig];
  const recs = fig(a.records, 'count', LTS);
  const admitted = fig(cohort.admitted_records, 'count', LTS), candidates = fig(cohort.candidate_records, 'count', LTS);
  if (c === 'Main' ? !cohort.conditional_on_admitted_records || cohort.admitted_records >= cohort.candidate_records
                   : cohort.conditional_on_admitted_records || cohort.admitted_records !== cohort.candidate_records)
    throw new Error(`entities.ts: the Forenzo ${c} coverage note no longer fits the export`);
  const condition: L = { en: `${armName[arm].en} · earliest → latest session`, zh: `${armName[arm].zh} · 最早会话 → 最晚会话` };
  const rows: ResultRow[] = [
    { path, method: laterArmLabel.ridge.en, label: laterArmLabel.ridge, condition, metric: ERR,
      value: w(a.ridge.primary.mean), interval: pr(a.ridge.primary.interval_95), people: 0, records: recs,
      note: { en: ['Median ', w(a.ridge.primary.median), ': the mean is far above it, a severe upper tail.'],
              zh: ['中位数 ', w(a.ridge.primary.median), '：均值远高于中位数，上尾极重。'] } },
    { path, method: laterArmLabel.source_mean.en, label: laterArmLabel.source_mean, comparator: true, condition, metric: ERR,
      value: w(a.source_mean.primary.mean), interval: pr(a.source_mean.primary.interval_95), people: 0, records: recs },
    { path, method: laterArmLabel.ridge.en, label: laterArmLabel.ridge,
      condition: { en: `${armName[arm].en} · ridge minus comparator, the same records`, zh: `${armName[arm].zh} · ridge 减对照，相同记录` },
      metric: PDIFF, value: w(a.paired.primary_difference.mean),
      interval: pr(a.paired.primary_difference.interval_95), people: 0, records: recs,
      note: { en: ['The ridge had the larger error on ', fig(a.paired.records_with_higher_ridge_error, 'count', LTS), ' of ', fig(a.paired.records, 'count', LTS), ' admitted records; ',
                   admitted, ' of ', candidates, ' candidate records admitted',
                   c === 'Main' ? ', the rest held on metadata before scoring, so the result is conditional on that subset.'
                                : '. “Transfer Learning” is the publisher’s name for how the data were collected, not a model trained here.'],
              zh: ['ridge 误差更大的纳入记录有 ', fig(a.paired.records_with_higher_ridge_error, 'count', LTS), ' 条（共 ', fig(a.paired.records, 'count', LTS), ' 条）；纳入 ',
                   admitted, ' 条候选记录（共 ', candidates, ' 条）',
                   c === 'Main' ? '，其余在评分前因元数据问题暂缓，结果以纳入的子集为条件。'
                                : '。“Transfer Learning”是发布者对该队列数据采集方式的命名，不是这里训练的模型。'] } },
  ];
  return {
    id: `later-forenzo-${c === 'Main' ? 'main' : 'transfer-learning'}-${arm === 'historical_decoder_velocity_imitation' ? 'velocity' : 'displacement'}`,
    title: { en: `Later sessions · continuous cursor tracking, ${c} cohort, ${armShort[arm].en} (a negative result; offline, no online-control claim)`,
             zh: `后续会话 · 连续光标追踪，${c} 队列，${armShort[arm].zh}（阴性结果；离线，不涉及在线控制）` },
    path, rows,
  };
}

/* --- Questions in language: route 3 (questions-in-language-update.json) ------------------------------------ */

const QLDIFF: L = { en: 'Paired difference, language arm minus reference (pp)', zh: '配对差值，语言问法减参照（pp）' };
const QLLOGR: L = { en: 'log R, the head’s remaining error over the read-off’s', zh: 'log R：分类头与读出的剩余错误之比' };
const QLAUC: L = { en: 'Paired difference in AUROC', zh: 'AUROC 的配对差值' };
const QL_SECTION: Record<string, string> = { P1: 'seen', P2: 'seen', P3: 'unseen-sleep', P4: 'unseen-frequency', P5: 'unseen-sleep' };
/** The reading beside an entry: the difference shown or not, the margin with it, the gate; an unseen entry says unseen by whom. */
function qlReading(e: QlEntry): RowNote {
  const c = qlContrast(e.label);
  const parts = (locale: Locale): (string | Fig)[] => {
    const zh = locale === 'zh', sep = zh ? '；' : '; ';
    const low = (t: string) => zh ? t : t.replace(/^[A-Z](?=[a-z])/, ch => ch.toLowerCase());
    const unseen = e.kind === 'unseen' ? (zh ? 'EEG 分类头没有见过，但文本编码器读过这些词。' : 'Unseen by the EEG head, not by the text encoder. ') : '';
    const r: (string | Fig)[] = e.r ? (zh ? ['R 为 ', qlFig(e.r.estimate, 'auc2'), '；'] : ['R ', qlFig(e.r.estimate, 'auc2'), '; ']) : [];
    const diff = qlDifference(e, c.x, c.y, locale);
    return [unseen, ...r, (e.r ? low(diff) : diff) + sep + low(qlMargin(e, c.x, locale)) + sep + low(qlGate(e.gate, locale)) + (zh ? '。' : '.')];
  };
  return { en: parts('en'), zh: parts('zh') };
}
/**
 * Route 3 on one primary dataset (BETA or BOAS): every primary entry, with both flags, the margin and the gate, under
 * the level it was measured at (a plain spectrum, or frozen CBraMod features). Seen, reworded and unseen entries are
 * separate rows, never pooled; the secondary results, the levels and the pre-run checks stay on the topic page.
 */
function languageGroup(id: 'beta' | 'boas'): ResultGroup {
  const blocks = id === 'beta' ? [qlBlock('P-ssvep-L0'), qlBlock('P-ssvep-L1')] : [qlBlock('P-sleep-L1')];
  const rows: ResultRow[] = blocks.flatMap(b => b.entries.map(e => {
    const c = qlContrast(e.label), who = b.level === 'L1' ? { method: 'CBraMod', methodSlug: 'cbramod' as MethodSlug }
      : { method: 'Plain spectrum', label: { en: 'Plain spectrum (L0)', zh: '普通频谱（L0）' } };
    const pp = e.unit === 'difference of proportions';
    const value = pp ? qlFig(e.estimate, 'pp2') : qlFig(e.estimate, 'sgn3');
    const interval: [Fig, Fig] = pp ? [qlFig(e.interval_95[0], 'sgn2'), qlFig(e.interval_95[1], 'pp2')] : [qlFig(e.interval_95[0], 'sgn3'), qlFig(e.interval_95[1], 'sgn3')];
    const name = (locale: Locale) => c.y === 'read-off' ? (locale === 'zh' ? `${qlArm(c.x, locale)}，对比读出` : `${qlArm(c.x, locale)} against the read-off`)
      : `${qlArm(c.x, locale)} − ${qlArm(c.y, locale)}`;
    const codes = c.y === 'read-off' ? `${c.x} / read-off` : `${c.x} − ${c.y}`;
    const seeds = (locale: Locale) => e.seeds === 3 ? (locale === 'zh' ? '三个随机种子' : 'three seeds') : (locale === 'zh' ? '一个随机种子' : 'one seed');
    // On frozen CBraMod features the neighbour 3-way also involves stimulus phase (the handoff: never a frequency result alone).
    const phase = b.domain === 'ssvep' && b.level === 'L1' && /neighbour 3-way/.test(e.label);
    return { path: `/topics/questions-in-language/#${QL_SECTION[e.id]}`, ...who,
      // a2 rests on three fixed synonyms: its rows hold for these three only (the handoff's wording).
      condition: { en: `${e.id} · ${name('en')} (${codes}) · ${c.asked.en}${phase ? ' (frequency and stimulus phase)' : ''}${c.x === 'TPL(a2)' ? ', for these three synonyms' : ''} · ${seeds('en')}`,
                   zh: `${e.id} · ${name('zh')}（${codes}）· ${c.asked.zh}${phase ? '（频率与刺激相位）' : ''}${c.x === 'TPL(a2)' ? '，只对这三个同义词成立' : ''} · ${seeds('zh')}` },
      metric: pp ? QLDIFF : e.unit === 'log R' ? QLLOGR : QLAUC, value, interval, people: e.people, note: qlReading(e) };
  }));
  return {
    id: 'questions-in-language',
    title: id === 'beta' ? { en: 'Questions in language · SSVEP (route 3)', zh: '用语言提问 · SSVEP（第三条路线）' }
                         : { en: 'Questions in language · sleep (route 3)', zh: '用语言提问 · 睡眠（第三条路线）' },
    path: '/topics/questions-in-language/', rows, qlNotes: id,
  };
}

/* --- The datasets ------------------------------------------------------------------ */

const mvpDs = (name: string) => data.datasets.find(d => d.name === name)!;
const citation = (id: string) => deployment.dataset_citations.find(c => c.id === id)!;
const rights = (r: any) => r.rights as { name: string; task: string; source: string; license: string; licenseUrl?: string; attribution: string };

function fromMvp(name: string, task: L, later: ResultGroup[] = []): DatasetEntity {
  const d = mvpDs(name);
  const slug = MVP_SLUG[name];
  return {
    slug, name: d.name, task, license: d.license, licenseUrl: d.licenseUrl ?? undefined,
    attribution: d.attribution, sources: [d.source].filter(Boolean) as string[],
    groups: [...mvpGroups(name), ...fmGroups(name), ...depGroups(slug), ...later],
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
  fromMvp('ds003810', { en: 'Motor imagery / rest', zh: '运动想象 / 静息' }, [reliableGroup('mi-rest')]),
  fromMvp('EEGMAT', { en: 'Mental arithmetic / rest', zh: '心算 / 静息' }, [adaptationGroup(), fmAdaptationGroup(), reliableGroup('arithmetic-rest')]),
  fromMvp('BETA', { en: '40-target SSVEP', zh: '40 目标 SSVEP' }, [reliableGroup('beta-8ch'), languageGroup('beta')]),
  fromMvp('ds006593', { en: 'P300 target ERP', zh: 'P300 目标 ERP' }),
  fromMvp('TMNRED / ds005383', { en: 'Semantic target ERP', zh: '语义目标 ERP' }),
  fromMvp('EESM19 scalp subset', { en: 'Five-stage sleep', zh: '五期睡眠分期' }, [sharedEesm19Group()]),
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
  fromRights('ysu-async-ssvep', cx['ysu-async-ssvep'], [ysuExtensionGroup(), ysuGroup()], { en: 'Asynchronous SSVEP, control and non-control states', zh: '异步 SSVEP，控制与非控制状态' }),
  fromRights('ltrsvp', extension.results['ltrsvp-rate-transfer'], [ltrsvpGroup()], { en: 'P300 target images in rapid serial visual presentation at three rates', zh: '三种速率下快速序列视觉呈现中的 P300 目标图像' }, 'LTRSVP · EEG Signals from an RSVP Task'),
  fromRights('dreem-dod', dreem, [dreemGroup('DOD-H'), dreemGroup('DOD-O')], { en: 'Five-stage sleep staging, healthy sleepers and people with obstructive sleep apnoea, kept apart', zh: '五期睡眠分期，健康被试与阻塞性睡眠呼吸暂停患者，分开分析' }),
  fromRights('openbmi', large.results['openbmi-cross-session-calibration'], [openbmiGroup(), sharedGroup('openbmi')], { en: 'Motor imagery: left or right hand across two sessions, and imagery or rest', zh: '运动想象：跨两次会话的左右手，以及想象还是静息' }),
  // Since 2026-10-07 (owner approval of its rights review, publishable with stated gaps): route 2's sleep source.
  { ...fromRights('boas', SRD.boas, [sharedGroup('boas'), languageGroup('boas')], { en: 'Overnight sleep, six polysomnography EEG channels, human-consensus stages', zh: '整夜睡眠，6 个多导睡眠图 EEG 通道，人工共识分期' },
                  'BOAS · Bitbrain Open Access Sleep dataset'), rightsNote: 'boas' as const },
  // The large-source batch's later-session results (later-sessions-update.json): three sources new to the site.
  fromRights('wbcic-shu', later.datasets['wbcic-shu'], [laterWbcicGroup('2C'), laterWbcicGroup('3C')],
             { en: 'Motor imagery across three recording sessions: two-class and three-class cohorts, kept apart', zh: '跨三次记录会话的运动想象：二分类与三分类两个队列，分开分析' },
             'WBCIC-SHU motor imagery dataset'),
  fromRights('longitudinal-rsvp', later.datasets['longitudinal-rsvp'], [laterRsvpGroup()],
             { en: 'RSVP face-target ERP, the same people at nominal Day 1, 7, 80 and 200 visits', zh: 'RSVP 人脸目标 ERP，同一批被试在标称第 1、7、80、200 天的访次' },
             'Longitudinal ERP dataset (RSVP)'),
  fromRights('forenzo-continuous-tracking', later.datasets['forenzo-continuous-tracking'], (['Main', 'Transfer Learning'] as const).flatMap(c => ([
               'historical_decoder_velocity_imitation', 'constructed_raw_target_displacement_proxy'] as const).map(a => laterForenzoGroup(c, a))),
             { en: 'Continuous cursor tracking with a noninvasive BCI, across sessions', zh: '无创 BCI 的连续光标追踪，跨会话' },
             'Forenzo & He continuous-tracking EEG-BCI dataset'),
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
  // A group carries only this method's rows, and its not-run entries for this method.
  const groups = datasets.flatMap(d => d.groups
    .map(g => ({ ...g, rows: g.rows.filter(r => r.methodSlug === slug), notRun: g.notRun?.filter(x => x.methodSlug === slug), dataset: d }))
    .filter(g => g.rows.length || g.notRun?.length));
  if (isFmSlug(slug)) {
    // The v9 model directory (foundation-models.ts); REVE's Base card is the released one,
    // shown as evaluated (directory-status.ts), and its Large card a new one.
    const status = fmDirectory.find(e => e.slug === slug)!.status;
    return { slug, name: methodNames[slug], family: 'foundation', status, groups };
  }
  const model = data.models.find(m => (m.id ?? m.name.toLowerCase().replace('+', '-')) === slug
                                   || m.name === methodNames[slug] || (slug === 'cca' && m.name === 'Standard CCA'));
  return { slug, name: methodNames[slug], family: model?.family, status: model && modelDirectoryStatus(model).status,
           url: model?.url ?? undefined, groups };
});

export const methodBySlug = Object.fromEntries(methods.map(m => [m.slug, m])) as Record<MethodSlug, MethodEntity>;

/**
 * Models listed in the directory that have no published result here, and why (status as
 * shown, directory-status.ts). REVE Base left this list on 2026-10-04 (evaluated in v9);
 * MIRepNet and EEG-DINO joined it as catalogue-only entries.
 */
export const unmeasuredModels: { name: string; family: string; status: string; url?: string; released?: string; checked?: string }[] = [
  ...data.models.map(m => ({ m, shown: modelDirectoryStatus(m) })).filter(({ shown }) => !shown.status.startsWith('Evaluated'))
    .map(({ m, shown }) =>
      // An overridden status keeps the released one and its check date beside it.
      ({ name: m.name, family: m.family, status: shown.status, url: m.url ?? undefined,
         released: shown.override?.released, checked: shown.override?.checked })),
  ...fmDirectory.filter(e => !e.models.length).map(e => ({ name: e.name, family: 'foundation', status: e.status })),
];

/**
 * Core-matrix rows a topic prints from experiments.json, beyond the groups that
 * point at it. Those rows' groups point at their protocol page
 * (/protocols/<id>/), so a reverse index of group paths alone missed them: until
 * 2026-10-02 when-not-to-act named the YSU dataset and no method, though its
 * short answer leads with the idle protocol on ds005342. `methods` narrows a
 * protocol to the rows printed, by the name the group rows carry. The
 * model-adaptation row is the one its export names as the matrix reference, so it
 * follows the export. Since 2026-10-04 the v9 rows a topic prints count too
 * (foundation-topics.ts `TOPIC_PRINTS`): their groups point at the protocol page's
 * v9 section (`anchor`), the EEGMAT adaptation at its own.
 */
const matrixReference = adaptation.results['eegmat-labram-adaptation'].matrix_reference;
type ProtocolRead = { track: string; anchor?: string; methods?: string[] };
const coreName = (track: string, id: string) => {
  const r = data.tracks.find(t => t.id === track)?.rows.find(x => x.id === id);
  if (!r) throw new Error(`entities.ts: the core matrix has no ${track} / ${id}`);
  return r.name;
};
const PROTOCOL_ROWS_PRINTED: Record<string, ProtocolRead[]> = {
  // The whole idle table: every method's detection and false activation.
  'when-not-to-act': [{ track: 'idle' }],
  // The frozen readout printed for scale beside the head-only arm.
  'model-adaptation': [{ track: matrixReference.track_id, methods: [matrixReference.model] }],
  ...Object.fromEntries(Object.entries(TOPIC_PRINTS).map(([slug, prints]) => [slug, prints.map(p => ({
    track: p.track, anchor: p.anchor,
    methods: p.core ? p.core.map(id => coreName(p.track, id)) : (p.models ?? []).map(id => fmModelById[id].name),
  }))])),
};

/**
 * The dataset and method pages a topic draws on: every entity whose figures the
 * topic prints. Derived from the served files the topic's cite block names
 * (structured.ts `topicFiles`): an entity row counts when its figure is a leaf
 * of one of those files and either its group points at the topic, or it is a
 * core-matrix or v9 row the topic prints, reached through its protocol page
 * (PROTOCOL_ROWS_PRINTED). A group pointing at the topic from a file the cite
 * block does not name fails the build: the line and the citation must agree.
 * check-workbench.mjs re-derives the line from the built pages, including the
 * figures the page marks with data-fig.
 */
export function topicEntities(slug: string, files: string[]): { datasets: DatasetEntity[]; methods: MethodEntity[] } {
  const path = `/topics/${slug}/`;
  const cited = new Set(files.map(f => f.replace(/^\/data\//, '')));
  const reads = PROTOCOL_ROWS_PRINTED[slug] ?? [];
  for (const r of reads) if (!data.tracks.some(t => t.id === r.track))
    throw new Error(`entities.ts: ${slug} prints ${r.track}, which the core matrix does not have`);
  const pointsHere = (g: ResultGroup) => g.path.split('#')[0] === path;
  const viaProtocol = (g: ResultGroup, row: ResultRow) =>
    reads.some(r => g.path === `/protocols/${r.track}/${r.anchor ? `#${r.anchor}` : ''}` && (!r.methods || r.methods.includes(row.method)));
  const prints = (g: ResultGroup, row: ResultRow) => {
    if (!cited.has(row.value.src)) {
      if (pointsHere(g) || viaProtocol(g, row)) throw new Error(`entities.ts: ${slug} prints ${g.id} from ${row.value.src}, which its cite block does not name`);
      return false;
    }
    return pointsHere(g) || viaProtocol(g, row);
  };
  const uses = (groups: ResultGroup[]) => groups.some(g => g.rows.some(row => prints(g, row)));
  return { datasets: datasets.filter(d => uses(d.groups)), methods: methods.filter(m => uses(m.groups)) };
}

export const entityPaths = [
  '/datasets/', ...datasets.map(d => `/datasets/${d.slug}/`),
  '/methods/', ...methods.map(m => `/methods/${m.slug}/`),
];
