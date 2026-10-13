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
import pilot from './pilot-studies-update.json';
import beyond from './beyond-scalp-update.json';
import type { Locale } from './i18n';
import { D as SRD, srFig, srPp, srLo, qName, code as srCode, differenceText, marginText, gateText, floorMarginText,
         ppEntry, entry as srEntry, arm as srArm, type SrEntry, type SrLogR } from './shared-encoder';
import { conditionLabel, modelLabel } from './topics';
import { block as qlBlock, contrast as qlContrast, armName as qlArm, differenceText as qlDifference, marginText as qlMargin,
         gateText as qlGate, qlFig, type QlEntry } from './questions-in-language';
import { EEGPT_PILOT_PATH, modelDirectoryStatus } from './directory-status';
import { FM_ADAPTATION_ANCHOR, FM_ANCHOR, fmAdaptation, fmAdaptationMeta, fmDirectory, fmModelById, fmPageNames, fmRowsByProtocol, fmSlugOf,
         fmResearchUse, fmSlugs, type FmModel, type FmRow, type FmSlug } from './foundation-models';
import { fmZh } from './foundation-models-zh';
import { EEGPT_ANCHOR, EEGPT_JSON, EEGPT_SLUG, eegptAttributionRows, eegptCells, eegptModel, eegptText, footnotesOf } from './eegpt-core';
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
 * `s1` prints a time in seconds; a time before an event (the BINGO trial timeline on the pilot-studies page) takes a
 * true minus sign, as every other signed format does.
 * `gap2` (EEGPT on the core matrix, 2026-10-13) prints the distance between two non-overlapping intervals, a value
 * already in percentage points and never signed, with two decimals: the export's `gap_pp` ("0.10 pp").
 */
export type Fmt = 'pct1' | 'pct1raw' | 'pct2raw' | 'pct2' | 'pp1' | 'pp2' | 'sgn1' | 'sgn2' | 'sgn3' | 'auc3' | 'auc2' | 'num3' | 'count' | 's1' | 'm2'
  | 'ppr2' | 'sgr2' | 'ms2' | 'int0' | 'sig3' | 'gap2';
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
    case 's1': return `${minus(f.raw.toFixed(1))} s`;
    case 'm2': return `${(f.raw / 1e6).toFixed(2)}M`;
    case 'ppr2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw).toFixed(2)} pp`;
    case 'sgr2': return `${f.raw === 0 ? '' : f.raw > 0 ? '+' : '−'}${Math.abs(f.raw).toFixed(2)}`;
    case 'ms2': return `${(f.raw * 1000).toFixed(2)} ms`;
    case 'int0': return minus(Math.round(f.raw).toLocaleString('en-US'));
    case 'sig3': return minus(f.raw.toPrecision(3));
    case 'gap2': return `${f.raw.toFixed(2)} pp`;
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
  /**
   * A count of something other than people, printed in the people column in place of `people` (then 0), with what it
   * counts (2026-10-12): one macaque (animal data), BINGO's subject fields as the source defines them, REFED's
   * nominal participant folders.
   */
  counted?: { n: Fig; what: L };
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
   * An EEGPT group (2026-10-13): the protocol whose EEGPT section states its checkpoint's terms. A page prints the
   * terms once, under the first EEGPT group, and links that section (ResultGroups.astro); a method page that states
   * them with the model skips them (`skipNotes: ['eegpt-terms']`).
   */
  eegptTerms?: string;
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
  /**
   * The group's caveats, printed under its rows (2026-10-12: the pilot studies and the results beyond scalp EEG):
   * what the figures above cannot be read as, beside them, once. Figures in a note are leaves like any other.
   */
  notes?: RowNote[];
  /**
   * An id for each note, where the same note bears on several groups of one page (EEGPT's footnotes, 2026-10-13: the
   * row's two on every protocol, the Tsinghua context on both BETA protocols). A page prints a note with an id once,
   * under the first of its groups that carries it (ResultGroups.astro); a method page that states some of them with
   * the model leaves those out of its groups.
   */
  noteIds?: string[];
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
   * the ethics committee and reference, written consent, and that its three gaps are stated with every figure;
   * BINGO, 2026-10-12: no ethics-approval reference, and the project's consent statement for its other dataset; the
   * handwriting dataset, 2026-10-12: a short pointer to its stated gap, which the data-use page states in full).
   */
  rightsNote?: 'boas' | 'bingo' | 'handwriting';
  /**
   * What was measured, for the page's Dataset markup, where it is not EEG (2026-10-12: fNIRS, intracortical spiking).
   */
  technique?: string;
  /** The signal a non-EEG dataset's page title names (2026-10-12): "fNIRS", "intracortical spiking". */
  signal?: L;
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
// The v9 foundation models (2026-10-04): one page per model family (foundation-models.ts). EEGPT (2026-10-13): its
// core-matrix cells and attribution rows from its own release (eegpt-core.ts), on a page like theirs.
export const methodSlugs = [...coreMethodSlugs, ...fmSlugs, EEGPT_SLUG] as const;
export type MethodSlug = typeof coreMethodSlugs[number] | FmSlug | typeof EEGPT_SLUG;
export const isFmSlug = (slug: string): slug is FmSlug => (fmSlugs as readonly string[]).includes(slug);
/** Model ids as the payloads write them → the method page they belong to. */
const METHOD_OF: Record<string, MethodSlug> = {
  eegnet: 'eegnet', labram: 'labram', cbramod: 'cbramod', shallowfbcspnet: 'shallowfbcspnet',
  deep4net: 'deep4net', 'csp-lda': 'csp-lda', cca: 'cca', 'author-cca': 'cca', fbcca: 'fbcca',
  'ensemble-trca': 'etrca', eegpt: EEGPT_SLUG,
};
/** The method page a payload model id belongs to, if it has one (a v9 checkpoint: its family's page). */
export const methodSlugOf = (id: string): MethodSlug | undefined => METHOD_OF[id] ?? fmSlugOf(id);
export const methodNames: Record<MethodSlug, string> = {
  eegnet: 'EEGNet', labram: 'LaBraM', cbramod: 'CBraMod', shallowfbcspnet: 'ShallowFBCSPNet',
  deep4net: 'Deep4Net', 'csp-lda': 'CSP+LDA', cca: 'CCA', fbcca: 'FBCCA', etrca: 'eTRCA',
  ...fmPageNames, [EEGPT_SLUG]: 'EEGPT',
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

/* --- EEGPT (eegpt-core-update.json, 2026-10-13) ---------------------------------------------------------- */

// EEGPT's row of a core protocol: a group of its own beside the core-matrix and further-encoder groups, never merged
// into either, read with the protocol page's EEGPT section. Figures are the export's percent blocks, in the core rows'
// units. Each footnote sits under the group of a cell it bears on, once a page (`noteIds`): the cell's own first, then
// the row's two. The group id ends in `-eegpt`, not in a track id, as the v9 groups' do.
const eegptNote = (en: string): RowNote => ({ en: [en], zh: [eegptText(en, 'zh').text] });
function eegptGroups(datasetName: string): ResultGroup[] {
  return data.tracks.filter(t => t.dataset === datasetName).map(t => {
    const c = eegptCells[t.id];
    if (!c) throw new Error(`entities.ts: no EEGPT cell for ${t.id}`);
    const path = `/protocols/${t.id}/#${EEGPT_ANCHOR}`;
    const mode = fmModeLabel(t.type === 'tradeoff' ? eegptModel.idleMode : eegptModel.mode);
    const base = { path, method: 'EEGPT', methodSlug: EEGPT_SLUG as MethodSlug, condition: mode, people: c.people.raw };
    const flag: RowNote | undefined = c.chanceFlag === 'at-or-below' ? { en: ['At or below chance.'], zh: ['不高于随机水平。'] }
      : c.chanceFlag === 'interval-reaches' ? { en: ['The interval reaches chance.'], zh: ['区间触及随机水平。'] } : undefined;
    const rows: ResultRow[] = c.idle ? [
      { ...base, metric: { en: 'Commands detected ≤3 s', zh: '检出的指令 ≤3 秒' }, value: c.idle.detected, of: c.idle.commandTrials,
        note: { en: [c.idle.abstain, ' of ', c.people, ' people always abstained.'], zh: [c.idle.abstain, ' 名始终拒识（共 ', c.people, ' 名被试）。'] } },
      { ...base, metric: { en: 'Idle false activations', zh: '空闲误触发' }, value: c.idle.falseActivations, of: c.idle.idleTrials },
      // The window metrics its idle footnote speaks of, as the further encoders' rows define them: cohort means, no interval.
      { ...base, metric: { en: 'Window balanced accuracy', zh: '窗口平衡准确率' }, value: c.idle.windowBa },
      { ...base, metric: { en: 'Window AUROC', zh: '窗口 AUROC' }, value: c.idle.windowAuroc },
    ] : [{ ...base, metric: BA, value: c.primary!, interval: c.interval, note: flag }];
    const notes = footnotesOf(t.id);
    const core = trackTitles[t.id];
    return {
      id: `${t.id}-${EEGPT_ANCHOR}`,
      title: { en: core.en.replace('Core matrix · ', 'EEGPT, frozen encoder · '), zh: core.zh!.replace('核心矩阵 · ', 'EEGPT（冻结编码器）· ') },
      path, rows, chance: c.chance, eegptTerms: t.id,
      notes: notes.map(f => eegptNote(f.text)), noteIds: notes.map(f => f.id),
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

// `src`: the file the row is a leaf of. EEGPT's attribution rows (2026-10-13) are written in these fields in its own
// release, and sit beside the published LaBraM and CBraMod rows of the same track and dataset.
function depRow(r: DepRow, src: string = DEP): ResultRow {
  const auc = r.metric === 'participant_mean_roc_auc';
  return {
    path: DEP_TRACK[r.track].path, method: modelLabel(r.model, 'en'), label: lbl(modelLabel(r.model, 'en'), modelLabel(r.model, 'zh')),
    methodSlug: METHOD_OF[r.model],
    comparator: r.model === 'random-uniform' || r.model === 'same-frequency-power',
    condition: depCondition(r), metric: auc ? ROC_AUC : BA,
    value: fig(r.value, auc ? 'auc3' : 'pct1', src),
    interval: pair(r.confidence_interval_95, auc ? 'auc3' : 'pct1', src),
    people: r.participants,
  };
}

function depGroups(slug: string): ResultGroup[] {
  const tracks = [...new Set(deployment.rows.filter(r => DEP_SLUG[r.dataset_id] === slug).map(r => r.track))];
  return tracks.map(track => ({
    id: track, title: DEP_TRACK[track].title, path: DEP_TRACK[track].path.split('#')[0],
    rows: [...deployment.rows.filter(r => r.track === track && DEP_SLUG[r.dataset_id] === slug).map(r => depRow(r)),
           ...eegptAttributionRows.filter(r => r.track === track && DEP_SLUG[r.dataset_id] === slug).map(r => depRow(r as DepRow, EEGPT_JSON))],
  }));
}
for (const r of eegptAttributionRows)
  if (!DEP_TRACK[r.track] || !DEP_SLUG[r.dataset_id] || r.model !== 'eegpt')
    throw new Error(`entities.ts: EEGPT's attribution row ${r.id} has no published group to sit in`);

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

/* --- Pilot studies (pilot-studies-update.json) ----------------------------------------------------------------- */

/**
 * The topic page these groups are read on, and its sections: the page must carry these anchors, and its topic card
 * must exist in i18n.ts (a group's "Read on" link takes the card's title). Every pilot stays outside every
 * leaderboard and model ranking, so no group here is ever read beside a matrix row.
 */
export const PILOT_PATH = '/topics/pilot-studies/';
export const PILOT_ANCHOR = { orthosis: 'orthosis', bingo: 'bingo', refed: 'refed', handwriting: 'handwriting', statusOnly: 'status-only' } as const;
if (EEGPT_PILOT_PATH !== `${PILOT_PATH}#${PILOT_ANCHOR.orthosis}`)
  throw new Error('entities.ts: EEGPT\'s directory link and the Orthosis section of the pilot-studies page disagree');
const PS = 'pilot-studies-update.json';
const ps = pilot.results as Record<string, any>;
const psDataset = (id: string) => (pilot.datasets as Record<string, any>)[id];
/** A pilot source gets a dataset page only while its export publishes it, with its results present. */
const psReleased = (id: string) => psDataset(id)?.publication === 'released' && psDataset(id).results.every((r: string) => ps[r]);
const AP: L = { en: 'Average precision', zh: '平均精确率' };
/** A percentage-point interval: the unit once, after the upper bound ("−4.0–+3.2 pp"). */
const ppInterval = (iv: number[], src: string): [Fig, Fig] => [fig(iv[0], sgnFmt(iv[0]), src), fig(iv[1], ppFmt(iv[1]), src)];
const ORTH_ARM: Record<string, L> = {
  eeg: { en: 'Fixed EEG features + logistic regression · 64 channels', zh: '固定 EEG 特征 + 逻辑回归 · 64 通道' },
  classical58: { en: 'Fixed EEG features + logistic regression · 58 channels', zh: '固定 EEG 特征 + 逻辑回归 · 58 通道' },
  eegpt2048: { en: 'EEGPT · frozen encoder + the same supervised probe · 58 channels', zh: 'EEGPT · 冻结编码器 + 同一有监督分类头 · 58 通道' },
  confound: { en: 'Direction/time confound probe (no EEG)', zh: '方向/时间混杂探针（不用 EEG）' },
  prior: { en: 'Training class prior', zh: '训练集类别先验' },
  permutation: { en: 'Permutation control: training labels shuffled within person and run', zh: '标签置换对照：在每名被试、每个 run 内打乱训练标签' },
};
const ORTH_CONDITION: L = { en: 'A person left out of training · 0–0.5 s after each recorded device event', zh: '留出一名被试 · 每个记录下来的设备事件后 0–0.5 秒' };
/** A permutation control: its mean, with the replicate means' lowest and highest beside it, labelled a range. */
function orthPermutation(pc: any, arm: string, path: string, people: number): ResultRow {
  return { path, method: ORTH_ARM.permutation.en, label: { en: `${ORTH_ARM.permutation.en} · ${ORTH_ARM[arm].en}`, zh: `${ORTH_ARM.permutation.zh} · ${ORTH_ARM[arm].zh}` },
    comparator: true, condition: ORTH_CONDITION, metric: BA, value: fig(pc.balanced_accuracy_mean, 'pct1', PS), people,
    note: { en: ['The mean of ', fig(pc.replicates, 'count', PS), ' replicates, whose means ranged from ', fig(pc.observed_range[0], 'pct1', PS), ' to ', fig(pc.observed_range[1], 'pct1', PS), ': an observed range, not a confidence interval.'],
            zh: [fig(pc.replicates, 'count', PS), ' 次重复的均值；各次均值从 ', fig(pc.observed_range[0], 'pct1', PS), ' 到 ', fig(pc.observed_range[1], 'pct1', PS), '：这是观察到的范围，不是置信区间。'] } };
}
/** One arm's balanced accuracy, AUROC and average precision; the interval is printed only where it is not a point. */
function orthArmRows(a: any, arm: string, path: string, people: number, comparator = false): ResultRow[] {
  const iv = (x: { interval_95: number[] }, f: Fmt) => x.interval_95[0] === x.interval_95[1] ? undefined : pair(x.interval_95, f, PS);
  const base = { path, method: ORTH_ARM[arm].en, label: ORTH_ARM[arm], condition: ORTH_CONDITION, people, ...(comparator ? { comparator } : {}) };
  return [
    { ...base, metric: BA, value: fig(a.balanced_accuracy.mean, 'pct1', PS), interval: iv(a.balanced_accuracy, 'pct1') },
    ...(comparator ? [] : [
      { ...base, metric: AUROC, value: fig(a.auroc.mean, 'auc3', PS), interval: iv(a.auroc, 'auc3') },
      { ...base, metric: AP, value: fig(a.average_precision.mean, 'auc3', PS), interval: iv(a.average_precision, 'auc3') },
    ]),
  ];
}
/** The cohort line every Orthosis group carries: one cohort, three configurations, counted once. */
function orthCohortNote(r: any): RowNote {
  const c = r.cohort;
  return {
    en: ['One cohort — ', fig(c.people, 'count', PS), ' people, ', fig(c.runs, 'count', PS), ' runs, ', fig(c.events, 'count', PS), ' recorded device events, ', fig(c.error_events, 'count', PS),
         ' of them injected errors — published as three configurations and counted once. The labels are recorded device events: the results do not show that a person recognised an error, and movement, muscle or device artifacts may contribute. Errors are a minority of events, so average precision is read against that share. Outside every leaderboard and model ranking.'],
    zh: ['同一个队列——', fig(c.people, 'count', PS), ' 名被试、', fig(c.runs, 'count', PS), ' 个 run、', fig(c.events, 'count', PS), ' 个记录下来的设备事件，其中 ', fig(c.error_events, 'count', PS),
         ' 个是注入的错误——以三种配置发布，只计一次。标签是记录下来的设备事件：这些结果不说明被试识别出了错误，运动、肌电或设备伪迹都可能起作用。错误只占事件的少数，所以平均精确率要对照这个比例来读。不进入任何排行榜或模型排名。'],
  };
}
/** Orthosis, the 64-channel classical baseline: the first configuration of the cohort. */
function orthosis64Group(): ResultGroup {
  const r = ps['orthosis-64ch-classical'], path = `${PILOT_PATH}#${PILOT_ANCHOR.orthosis}`, n = r.cohort.people, d = r.eeg_minus_confound;
  const rs = r.response_clean_subset;
  return {
    id: 'pilot-orthosis-64ch', path, chance: fig(r.chance_level, 'pct1', PS),
    title: { en: 'Pilot studies · orthosis error events, the 64-channel classical baseline', zh: '试点研究 · 矫形器错误事件，64 通道经典基线' },
    rows: [
      ...orthArmRows(r.arms.eeg, 'eeg', path, n),
      ...orthArmRows(r.arms.confound, 'confound', path, n, true),
      ...orthArmRows(r.arms.prior, 'prior', path, n, true),
      { path, method: ORTH_ARM.eeg.en, label: ORTH_ARM.eeg, condition: { en: 'Minus the confound probe, matched person by person', zh: '减混杂探针，逐人匹配' }, metric: DIFF,
        value: fig(d.balanced_accuracy_difference.mean, 'pp1', PS), people: n,
        note: { en: ['No interval was computed for this difference. EEG was above the confound probe for ', fig(d.people_with_eeg_above_confound, 'count', PS), ' of ', fig(d.people, 'count', PS), ' people.'],
                zh: ['这个差值没有计算区间。EEG 高于混杂探针的被试有 ', fig(d.people_with_eeg_above_confound, 'count', PS), ' 人（共 ', fig(d.people, 'count', PS), ' 人）。'] } },
      orthPermutation(r.permutation_control.balanced_accuracy, 'eeg', path, n),
    ],
    notes: [orthCohortNote(r), {
      en: ['A response-clean subset is counts only: ', fig(rs.events, 'count', PS), ' events, ', fig(rs.error_events, 'count', PS), ' errors and ', fig(rs.standard_events, 'count', PS), ' standard events, with ',
           fig(rs.people_with_both_classes, 'count', PS), ' people having both classes, so its scores are not published.'],
      zh: ['“响应干净”子集只给计数：', fig(rs.events, 'count', PS), ' 个事件，其中 ', fig(rs.error_events, 'count', PS), ' 个错误、', fig(rs.standard_events, 'count', PS), ' 个标准事件，两类都有的被试只有 ',
           fig(rs.people_with_both_classes, 'count', PS), ' 人，所以不发布它的分数。'],
    }],
  };
}
/** Orthosis, the matched 58-channel classical configuration of the same cohort. */
function orthosis58Group(): ResultGroup {
  const r = ps['orthosis-58ch-classical'], path = `${PILOT_PATH}#${PILOT_ANCHOR.orthosis}`, n = r.cohort.people;
  return {
    id: 'pilot-orthosis-58ch', path, chance: fig(r.chance_level, 'pct1', PS),
    title: { en: 'Pilot studies · orthosis error events, the matched 58-channel classical configuration (the same cohort)', zh: '试点研究 · 矫形器错误事件，匹配的 58 通道经典配置（同一队列）' },
    rows: [
      ...orthArmRows(r.arms.classical58, 'classical58', path, n),
      ...orthArmRows(r.arms.confound, 'confound', path, n, true),
      orthPermutation(r.permutation_control.balanced_accuracy, 'classical58', path, n),
    ],
    notes: [{
      en: ['The same cohort, labels and caveats as the 64-channel baseline above, counted once. The 58 channels are the ones EEGPT supports, fixed before scoring. A second configuration of the same people, not a replication: the 64-channel scores were seen before it was frozen, and no conclusion about how many channels are needed follows.'],
      zh: ['与上面的 64 通道基线是同一个队列、同样的标签与局限，只计一次。这 58 个通道是 EEGPT 支持的通道，在评分前就已固定。这是同一批被试的第二种配置，不是重复验证：冻结这个配置之前，64 通道的分数已经看过；也不能由此得出需要多少通道的结论。'],
    }],
  };
}
/** Orthosis, frozen EEGPT against the matched classical features: the same people, channels, folds and probe. */
function orthosisEegptGroup(): ResultGroup {
  const r = ps['orthosis-eegpt-vs-58ch'], path = `${PILOT_PATH}#${PILOT_ANCHOR.orthosis}`, n = r.cohort.people, p = r.paired;
  if (p.interval_excludes_zero !== false) throw new Error('entities.ts: the EEGPT note says its paired interval spans zero');
  return {
    id: 'pilot-orthosis-eegpt', path, chance: fig(r.chance_level, 'pct1', PS),
    title: { en: 'Pilot studies · orthosis error events, frozen EEGPT against the matched classical features (58 channels, the same cohort)', zh: '试点研究 · 矫形器错误事件，冻结的 EEGPT 与匹配的经典特征比较（58 通道，同一队列）' },
    rows: [
      ...orthArmRows(r.arms.eegpt2048, 'eegpt2048', path, n),
      ...orthArmRows(r.arms.classical58, 'classical58', path, n).slice(0, 1),
      { path, method: ORTH_ARM.eegpt2048.en, label: ORTH_ARM.eegpt2048, condition: { en: 'Minus the matched classical features, the same people and folds', zh: '减匹配的经典特征，相同被试与折' }, metric: DIFF,
        value: fig(p.balanced_accuracy_difference.mean, ppFmt(p.balanced_accuracy_difference.mean), PS), interval: ppInterval(p.balanced_accuracy_difference.interval_95, PS), people: n,
        note: { en: ['The paired interval spans zero: neither arm is shown to be better, and the two are not shown to be equivalent.'],
                zh: ['配对区间跨过零：既不能说明哪一方更好，也不能说明两者等效。'] } },
      orthPermutation(r.permutation_control.eegpt2048, 'eegpt2048', path, n),
    ],
    notes: [{
      en: ['The same cohort, channels, folds and probe as the 58-channel configuration above, counted once. Supervised transfer: the frozen encoder’s outputs feed a probe trained on the other people’s labels, not zero-shot. Overlap between this dataset and EEGPT’s pretraining data has not been excluded, and the 64-channel classical scores were seen before this comparison was frozen. EEGPT’s checkpoint licence is unresolved and no original or converted weights are distributed; Apache-2.0 covers the repository’s code only. Not evidence about EEG foundation models in general.'],
      zh: ['与上面的 58 通道配置是同一个队列、同样的通道、折与分类头，只计一次。这是有监督迁移：冻结编码器的输出送入用其他被试标签训练的分类头，不是零样本。没有排除这个数据集出现在 EEGPT 预训练数据中的可能；冻结这项比较之前，64 通道经典基线的分数已经看过。EEGPT 检查点的许可尚未厘清，不分发任何原始或转换后的权重；Apache-2.0 只涵盖代码仓库中的代码。这不是关于 EEG 基础模型整体的证据。'],
    }],
  };
}

/**
 * BINGO's rights, exactly as they stand (owner decision 3, 2026-10-12), for its dataset page: the export's English
 * statements, their Chinese here, and the public deliverable they are read from. The data management plan is never
 * cited. Read only while the switch releases BINGO (no dataset page exists otherwise).
 */
export const BINGO_RIGHTS_ZH = {
  ethics: '数据源没有公布任何伦理批准的出处或编号。',
  consent: '项目的公开交付文件 D3.1（3.0 版）写明，每名被试在参加实验之前签署了知情同意书。这句话针对的是该项目在同一个 CERTH 实验室记录的、20 名被试的 NATO 字母表数据集；跨语言数据集自己的文档 D3.1（2.0 版）没有伦理或知情同意声明。',
};
export function bingoRights() {
  const d = psDataset('bingo-imagined-speech'), e = d.consent_and_ethics;
  const readFrom = (e.read_from as string).match(/https:\/\/[^\s),]+/)?.[0];
  if (e.ethics_approval.stated !== false || e.informed_consent.stated !== true || !e.informed_consent.scope.includes('not for the cross-language dataset')
      || readFrom !== 'https://bingo-project.gr/download/402' || d.rights.license !== 'No licence stated' || !/^owner decision/.test(e.basis))
    throw new Error('entities.ts: BINGO\'s rights as the export states them (no ethics reference; consent stated for the project\'s other dataset; no licence)');
  return {
    ethics: { en: e.ethics_approval.note as string, zh: BINGO_RIGHTS_ZH.ethics },
    consent: { en: e.informed_consent.statement as string, zh: BINGO_RIGHTS_ZH.consent },
    readFrom, readFromTitle: d.documentation.find((x: { url: string }) => x.url === readFrom).title as string,
  };
}

/** BINGO: one fixed spectral baseline across people, within and across Greek and English. A negative result. */
function bingoGroup(): ResultGroup {
  const r = ps['bingo-cross-language'], path = `${PILOT_PATH}#${PILOT_ANCHOR.bingo}`, c = r.contrast, ds = r.delivered_signal;
  if (c.interval_excludes_zero !== false || ds.verified_against_file !== false)
    throw new Error('entities.ts: the BINGO notes say the contrast spans zero and the preprocessing was not re-verified');
  const counted = { n: fig(r.cohort.source_fields, 'count', PS), what: { en: ' subject fields as the source defines them, not proven distinct people', zh: ' 个按数据源定义的被试字段，不能证明是不同的人' } };
  const lang: Record<string, string> = { Greek: '希腊语', English: '英语' };
  const label: L = { en: 'Relative band power + ridge classifier', zh: '相对频带功率 + 岭分类器' };
  const rows: ResultRow[] = r.directions.map((d: any) => ({
    path, method: label.en, label, counted, people: 0,
    condition: { en: `Trained on ${d.train_language}, tested on ${d.test_language} · a subject field left out`, zh: `用${lang[d.train_language]}训练、在${lang[d.test_language]}上测试 · 留出一个被试字段` },
    metric: BA, value: fig(d.balanced_accuracy.mean, 'pct1', PS), interval: pair(d.balanced_accuracy.interval_95, 'pct1', PS),
    note: { en: ['Top-3 accuracy ', fig(d.top3_accuracy.mean, 'pct1', PS), ', against its prior of ', fig(r.chance.top3_accuracy, 'pct1', PS), '.'],
            zh: ['top-3 准确率 ', fig(d.top3_accuracy.mean, 'pct1', PS), '，其先验为 ', fig(r.chance.top3_accuracy, 'pct1', PS), '。'] },
  }));
  rows.push({ path, method: label.en, label, counted, people: 0,
    condition: { en: 'Across languages minus within, the mean over both training languages', zh: '跨语言减语言内，两种训练语言的均值' }, metric: DIFF,
    value: fig(c.balanced_accuracy_difference.mean, ppFmt(c.balanced_accuracy_difference.mean), PS), interval: ppInterval(c.balanced_accuracy_difference.interval_95, PS),
    note: { en: ['The interval spans zero: no superiority or equivalence between languages, and no significance test.'],
            zh: ['区间跨过零：不能说明两种语言孰优孰劣，也不能说明二者等效，也没有做显著性检验。'] } });
  return {
    id: 'pilot-bingo', path, chance: fig(r.chance.balanced_accuracy, 'pct1', PS),
    title: { en: 'Pilot studies · inner speech in Greek and English, across people and across languages (a negative result)', zh: '试点研究 · 希腊语与英语的内部言语，跨被试、跨语言（阴性结果）' },
    rows,
    notes: [{
      en: ['Every direction is close to the 15-class prior. A negative result for this one baseline in this setting: it does not show that inner speech cannot be decoded by other methods. The intervals are approximate and descriptive, from overlapping leave-one-field-out fits. Outside every leaderboard and model ranking.'],
      zh: ['每个方向都接近 15 类的先验。这是这一个基线在这种设置下的阴性结果：并不说明其他方法也解码不了内部言语。区间是近似的描述性区间，来自彼此重叠的“每次留出一个被试字段”的拟合。不进入任何排行榜或模型排名。'],
    }, {
      en: ['Delivered signals, as the project describes them (BINGO deliverable D3.1, version 2.0): the same preprocessing for both of its released datasets — band-pass and notch filtering, Artifact Subspace Reconstruction (ASR) and FORCe removal of ocular and muscle artifacts — and then segmentation into trials. The signals analysed here were therefore artifact-cleaned on the continuous recordings before any trial was cut. As the project states it; not re-verified against the delivered file.'],
      zh: ['交付的信号，按项目自己的描述（BINGO 交付文件 D3.1，2.0 版）：项目发布的两个数据集采用相同的预处理——带通与陷波滤波、伪迹子空间重构（ASR）与 FORCe 去除眼动和肌电伪迹——然后才切分为试次。因此，这里分析的信号在切分任何试次之前，已经在连续记录上做过去伪迹处理。以上按项目的表述，没有对照交付的数据文件重新核实。'],
    }],
  };
}

/**
 * The handwriting dataset's rights (owner decision, 2026-10-12): no ethics-approval or informed-consent statement was
 * found, and the aggregates are published with that gap stated. The data-use page and the pilot-studies credits state
 * it in full; the dataset page carries this short pointer, read from the export.
 */
export function handwritingRights() {
  const d = psDataset('eeg-fnirs-handwriting'), e = d.consent_and_ethics;
  if (d.publication !== 'released' || e.ethics_approval.stated !== false || e.informed_consent.stated !== false || !/^owner decision/.test(e.basis)
      || !e.gap.startsWith('No ethics-approval or informed-consent statement was found.') || !e.searched?.some((x: { url?: string }) => x.url === 'https://arxiv.org/abs/2608.03176v2'))
    throw new Error('entities.ts: the handwriting rights as the export states them (no statement found, the challenge paper read, the owner\'s decision)');
  return {
    pointer: {
      en: 'No ethics-approval or informed-consent statement was found, on the dataset card or in a participating team’s challenge paper; the aggregates are published with that gap stated, by the owner’s decision.',
      zh: '在数据集卡片和一支参赛队伍的挑战赛论文中，都没有找到伦理批准或知情同意声明；聚合结果依据所有者的决定发布，并说明这一缺口。',
    },
  };
}

/** The handwriting dataset: mask-aware relative EEG against three controls that see no EEG, five people. */
function handwritingGroup(): ResultGroup {
  const r = ps['handwriting-mask-aware'], path = `${PILOT_PATH}#${PILOT_ANCHOR.handwriting}`, n = r.cohort.people, A = r.arms, K = r.contrasts;
  if (A.mask_only.balanced_accuracy.interval_95 !== null || K.relative_eeg_minus_time_only.interval_excludes_zero !== false
      || !K.relative_eeg_minus_mask_only.interval_excludes_zero || !K.relative_eeg_minus_mask_plus_time.interval_excludes_zero)
    throw new Error('entities.ts: the handwriting notes say the mask-only interval is withheld and only the time contrast crosses zero');
  const p2 = (raw: number) => fig(raw, 'pct2', PS);
  const iv2 = (iv: number[] | null) => (iv && iv[0] !== iv[1] ? [p2(iv[0]), p2(iv[1])] as [Fig, Fig] : undefined);
  const condition: L = { en: 'A person left out of training · four released coded labels', zh: '留出一名被试 · 四个已发布的编码标签' };
  const ARM: Record<string, L> = {
    relative_eeg: { en: 'Mask-aware relative EEG + logistic regression', zh: '掩码感知的相对频带功率 EEG + 逻辑回归' },
    mask_only: { en: 'Missingness mask only (no EEG)', zh: '只看缺失掩码（不用 EEG）' },
    time_only: { en: 'Elapsed time / trial order (no EEG)', zh: '经过时间 / 试次顺序（不用 EEG）' },
    mask_plus_time: { en: 'Mask + time (no EEG)', zh: '掩码 + 时间（不用 EEG）' },
    majority: { en: 'Training majority', zh: '训练集多数类' },
  };
  const rows: ResultRow[] = (['relative_eeg', 'mask_only', 'time_only', 'mask_plus_time', 'majority'] as const).map(k => ({
    path, method: ARM[k].en, label: ARM[k], condition, metric: BA, people: n, ...(k === 'relative_eeg' ? {} : { comparator: true }),
    value: p2(A[k].balanced_accuracy.mean), interval: iv2(A[k].balanced_accuracy.interval_95),
    ...(k === 'mask_only' ? { note: { en: ['Interval not published: with five people, its bounds would show individual people’s scores.'], zh: ['不发布区间：只有五名被试，区间端点能反推出个人的分数。'] } }
      : k === 'majority' ? { note: { en: ['Chance for every person, by construction.'], zh: ['对每名被试都等于随机水平，这是由构造决定的。'] } } : {}),
  }));
  const VS: Record<string, L> = {
    relative_eeg_minus_mask_only: { en: 'Minus the missingness mask only, the same people', zh: '减只看缺失掩码的对照，相同被试' },
    relative_eeg_minus_time_only: { en: 'Minus elapsed time / trial order, the same people', zh: '减经过时间 / 试次顺序的对照，相同被试' },
    relative_eeg_minus_mask_plus_time: { en: 'Minus mask + time, the same people', zh: '减掩码 + 时间的对照，相同被试' },
  };
  for (const k of Object.keys(VS)) {
    const d = K[k].balanced_accuracy_difference;
    rows.push({ path, method: ARM.relative_eeg.en, label: ARM.relative_eeg, condition: VS[k], metric: DIFF, people: n,
      value: fig(d.mean, 'pp2', PS), interval: [fig(d.interval_95[0], 'sgn2', PS), fig(d.interval_95[1], 'pp2', PS)],
      ...(K[k].interval_excludes_zero ? {} : { note: { en: ['The interval crosses zero: not separated from this control.'], zh: ['区间跨过零：与这个对照没有区分开。'] } }) });
  }
  const sh = r.label_shuffle.representations.relative_eeg;
  rows.push({ path, method: ARM.relative_eeg.en, label: { en: `Training-label shuffles · ${ARM.relative_eeg.en}`, zh: `打乱训练标签 · ${ARM.relative_eeg.zh}` }, comparator: true,
    condition, metric: BA, value: p2(sh.balanced_accuracy_mean), people: n,
    note: { en: ['The mean of ', fig(sh.replicates, 'count', PS), ' shuffles, whose means ranged from ', p2(sh.observed_range[0]), ' to ', p2(sh.observed_range[1]), ': an observed range, not a confidence interval.'],
            zh: [fig(sh.replicates, 'count', PS), ' 次打乱的均值；各次均值从 ', p2(sh.observed_range[0]), ' 到 ', p2(sh.observed_range[1]), '：这是观察到的范围，不是置信区间。'] } });
  const av = r.availability, c = r.cohort;
  return {
    id: 'pilot-handwriting', path, chance: p2(r.chance_level),
    title: { en: 'Pilot studies · mask-aware EEG on an imagined-handwriting dataset, a data-quality and methods case study', zh: '试点研究 · 想象书写数据集上的掩码感知 EEG，一项数据质量与方法案例研究' },
    rows,
    notes: [{
      en: [fig(c.people, 'count', PS), ' people and ',
           fig(c.trials, 'count', PS), ' trials from a reused development cohort, whose earlier scores were seen before this design: a quality-informed diagnostic, not independent confirmation. Every trial keeps ', fig(av.available_channels_per_trial.fewest, 'count', PS), ' to ', fig(av.available_channels_per_trial.most, 'count', PS), ' of ',
           fig(av.channels_recorded, 'count', PS), ' recorded channels under a fixed numerical availability rule, which is not certified clean EEG. Four released coded labels, not verified characters or trajectories: not handwriting recognition. The intervals are descriptive, resampling the five people over overlapping folds, not population confidence intervals. The official test data were not used. No fNIRS, fusion, online, physiological-origin, competition-standing or medical claim; outside every leaderboard.'],
      zh: [fig(c.people, 'count', PS), ' 名被试、',
           fig(c.trials, 'count', PS), ' 个试次，来自重复使用的开发队列；较早那次分析在这个队列上的分数，在这个设计之前已经看过：这是参考了质量检查的诊断，不是独立确认。按固定的数值可用性规则，每个试次保留 ', fig(av.available_channels_per_trial.fewest, 'count', PS), ' 至 ', fig(av.available_channels_per_trial.most, 'count', PS), ' 个通道（共记录 ',
           fig(av.channels_recorded, 'count', PS), ' 个），这并不代表经过认证的干净 EEG。四个已发布的编码标签，对应的字符或书写轨迹都没有核实：这不是手写识别。区间是描述性的，在彼此重叠的折上对五名被试重抽样，不是群体置信区间。没有使用官方测试数据。不作任何 fNIRS、融合、在线、生理来源、竞赛名次或医学方面的声明；不进入任何排行榜。'],
    }],
  };
}

/** REFED: a stored-clip computational diagnostic, EEG against three source-only controls in two conditions. */
function refedGroup(): ResultGroup {
  const r = ps['refed-stored-clip'], path = `${PILOT_PATH}#${PILOT_ANCHOR.refed}`;
  const counted = { n: fig(r.cohort.nominal_folders, 'count', PS), what: { en: ' nominal participant folders', zh: ' 个标称被试文件夹' } };
  const MAE: L = { en: 'Equal-axis mean absolute error, raw self-report scale (lower is better)', zh: '两轴等权平均绝对误差，原始自评标度（越低越好）' };
  const ARM: Record<string, L & { comparator?: boolean }> = {
    eeg_ridge: { en: 'EEG Ridge (relative band power)', zh: 'EEG 岭回归（相对频带功率）' },
    // Named for what each control is, as the pilot-studies page names them (2026-10-13); the export's arm names stay.
    source_global_mean: { en: 'Training-set mean', zh: '训练集总体均值' },
    source_video_lookup: { en: 'Same-video training lookup', zh: '训练集按视频编号查表' },
    duration_video_id_ridge: { en: 'Duration / numeric-video-ID ridge', zh: '时长 / 数字视频编号岭回归' },
  };
  const COND: Record<string, L> = {
    shared_videos_held_folder: { en: 'Shared videos, a folder held out (familiar stimuli)', zh: '共享视频，留出一个文件夹（刺激是熟悉的）' },
    held_folder_and_videos: { en: 'Folder and video IDs held out together', zh: '文件夹与视频编号一起留出' },
  };
  const rows: ResultRow[] = r.conditions.flatMap((cd: any) => Object.entries(cd.arms).map(([id, a]: [string, any]) => ({
    path, method: ARM[id].en, label: { en: ARM[id].en, zh: ARM[id].zh }, counted, people: 0,
    ...(a.kind === 'control' ? { comparator: true } : {}),
    condition: COND[cd.id], metric: MAE, value: fig(a.equal_axis_mae, 'num3', PS),
  })));
  if (rows.length !== 8 || rows.some(x => !x.condition)) throw new Error('entities.ts: REFED has two conditions of four arms');
  return {
    id: 'pilot-refed', path,
    title: { en: 'Pilot studies · REFED stored clips, a computational diagnostic', zh: '试点研究 · REFED 存储片段，一项计算诊断' },
    rows,
    notes: [{
      en: [fig(r.cohort.nominal_folders, 'count', PS), ' nominal participant folders with the same ', fig(r.cohort.videos, 'count', PS), ' videos: ', fig(r.cohort.clips, 'count', PS),
           ' clips, not as many independent people, so no interval or significance test is reported. EEG Ridge has a larger error than every source-only control in both conditions. With shared videos, the same-video lookup has the smallest error, because familiar stimuli carry the prediction; held out together, it has no matching video and equals the training-set mean. Targets are the mean of each clip’s stored valence and arousal labels on the published raw scale, not SAM scores. Stored EEG units, the EEG-to-rating clock and the crop end points are unresolved, and the rating means were seen before this design. No physiological, neural or population claim; outside every leaderboard.'],
      zh: [fig(r.cohort.nominal_folders, 'count', PS), ' 个标称被试文件夹，观看同样的 ', fig(r.cohort.videos, 'count', PS), ' 段视频：共 ', fig(r.cohort.clips, 'count', PS),
           ' 个片段，并不是同样多的独立个体，所以不报告区间或显著性检验。两种条件下，EEG 岭回归的误差都比每个不用 EEG、只用训练集信息的对照大。共享视频时，按同一视频查表的误差最小，因为熟悉的刺激本身就能带来预测；两者一起留出时，它找不到对应的视频，结果等于总体均值。目标值是每个片段存储的效价与唤醒度标签在已发布原始标度上的均值，不是 SAM 评分。存储的 EEG 单位、EEG 与评分之间的时钟以及裁剪的端点都没有确定，评分均值在这个设计之前就已看过。不作任何生理、神经或群体层面的声明；不进入任何排行榜。'],
    }],
  };
}

/* --- Beyond scalp EEG (beyond-scalp-update.json) ------------------------------------------------------------- */

/** The topic page these groups are read on, and its sections (the page must carry these anchors). */
export const BEYOND_PATH = '/topics/beyond-scalp-eeg/';
export const BEYOND_ANCHOR = { bak: 'bak-fnirs', nlb: 'mc-rtt', ds007420: 'ds007420', falcon: 'falcon-h2', fus: 'rabut-fus', statusOnly: 'status-only' } as const;
const BS = 'beyond-scalp-update.json';
const bs = beyond.results as Record<string, any>;
/** A source gets a dataset page only while the export carries its results (a held consent record removes them). */
const bsReleased = (id: string) => {
  const d = (beyond.datasets as Record<string, any>)[id];
  return !!d && d.results.length > 0 && d.results.every((r: string) => bs[r]);
};

/** Bak et al.: human fNIRS, three executed movements, a person left out at a time. */
function bakGroup(): ResultGroup {
  const r = bs['bak-fnirs-loso'], a = r.arms, path = `${BEYOND_PATH}#${BEYOND_ANCHOR.bak}`, n = r.cohort.people, rec = a.shrinkage_lda.class_recall;
  if (r.species !== 'human' || r.modality !== 'fNIRS' || !a.shrinkage_lda.balanced_accuracy.interval_excludes_chance)
    throw new Error('entities.ts: the Bak group is human fNIRS with its interval above chance');
  const condition: L = { en: 'A person left out of training · executed tapping, not motor imagery', zh: '留出一名被试 · 实际敲击动作，不是运动想象' };
  return {
    id: 'beyond-bak-fnirs', path, chance: fig(r.primary_metric.chance_level, 'pct1', BS),
    title: { en: 'Beyond scalp EEG · human fNIRS, right-hand, left-hand and foot tapping', zh: '头皮 EEG 之外 · 人类 fNIRS，右手、左手手指敲击与脚部敲击' },
    rows: [
      { path, method: 'Shrinkage LDA', label: { en: 'Standardization + shrinkage LDA', zh: '标准化 + 收缩 LDA' }, condition, metric: BA,
        value: fig(a.shrinkage_lda.balanced_accuracy.mean, 'pct1', BS), interval: pair(a.shrinkage_lda.balanced_accuracy.interval_95, 'pct1', BS), people: n,
        note: { en: ['Each person’s balanced accuracy, averaged with equal weight. Class recall over all held-out trials: right hand ', fig(rec.right_hand, 'pct1', BS), ', left hand ', fig(rec.left_hand, 'pct1', BS), ', foot ', fig(rec.foot, 'pct1', BS),
                     '. The interval resamples the fixed participant scores (', fig(r.uncertainty.draws, 'count', BS), ' draws): not a refit bootstrap and not a clinical confidence interval.'],
                zh: ['每名被试的平衡准确率，按等权平均。所有留出试次上的各类别召回率：右手 ', fig(rec.right_hand, 'pct1', BS), '，左手 ', fig(rec.left_hand, 'pct1', BS), '，脚 ', fig(rec.foot, 'pct1', BS),
                     '。区间是对固定的逐人分数重抽样得到的（', fig(r.uncertainty.draws, 'count', BS), ' 次）：不是重新拟合的 bootstrap，也不是临床意义上的置信区间。'] } },
      { path, method: 'Training prior', label: { en: 'Training prior', zh: '训练集先验' }, comparator: true, condition, metric: BA,
        value: fig(a.source_prior.balanced_accuracy.mean, 'pct1', BS), people: n,
        note: { en: ['Predicts the same class every time: no interval, because every person gets the same score.'], zh: ['每次都预测同一个类别：没有区间，因为每名被试的分数都相同。'] } },
    ],
    notes: [{
      en: ['Offline, from the supplied oxy- and deoxyhemoglobin series over a window after each task onset. Task-correlated systemic or motion effects are not excluded, so this shows neither a brain-only signal nor cortical localisation. This site’s own protocol: it does not reproduce the authors’ within-person scores, and it is not compared with any scalp EEG result.'],
      zh: ['离线分析，基于数据集提供的氧合与脱氧血红蛋白序列，取每次任务开始后的一个时间窗。没有排除与任务相关的全身性生理或运动影响，所以既不能说明信号只来自大脑，也不能说明皮层定位。这是本站自己的协议：不复现作者的被试内分数，也不与任何头皮 EEG 结果比较。'],
    }],
  };
}

/** MC_RTT: one macaque, one session, finger velocity from motor-cortex spiking; the ridge against the training mean. */
function nlbGroup(): ResultGroup {
  const r = bs['nlb-mc-rtt-velocity'], a = r.arms, path = `${BEYOND_PATH}#${BEYOND_ANCHOR.nlb}`, better = r.comparison.ridge_better;
  if (r.cohort.animals !== 1 || better.mae_m_per_s !== false) throw new Error('entities.ts: the MC_RTT group is one animal, with the ridge worse on MAE');
  const counted = { n: fig(r.cohort.animals, 'count', BS), what: { en: ' macaque (animal data)', zh: ' 只猕猴（动物数据）' } };
  const condition: L = { en: 'Held-out trials of the same session · x/y finger velocity', zh: '同一次会话的留出试次 · 手指 x/y 速度' };
  const METRIC: Record<string, L> = {
    r2_uniform_average: { en: 'R², mean of x and y (higher is better)', zh: 'R²，x 与 y 的均值（越高越好）' },
    r2_x: { en: 'R², x (higher is better)', zh: 'R²，x（越高越好）' },
    r2_y: { en: 'R², y (higher is better)', zh: 'R²，y（越高越好）' },
    rmse_m_per_s: { en: 'RMSE in m/s (lower is better)', zh: 'RMSE，m/s（越低越好）' },
    mae_m_per_s: { en: 'MAE in m/s (lower is better)', zh: 'MAE，m/s（越低越好）' },
  };
  const ARM: Record<string, L> = { ridge: { en: 'Ridge on spike-count history', zh: '基于放电计数历史的岭回归' }, training_mean: { en: 'Training mean', zh: '训练集均值' } };
  const rows: ResultRow[] = Object.keys(METRIC).flatMap(k => (['ridge', 'training_mean'] as const).map(arm => ({
    path, method: ARM[arm].en, label: ARM[arm], ...(arm === 'training_mean' ? { comparator: true } : {}), condition, metric: METRIC[k],
    // Near-zero R² of the comparator prints with three significant digits, never as −0.000 (wideFmt).
    value: fig(a[arm][k], wideFmt(a[arm][k]), BS), people: 0, counted,
    ...(arm === 'ridge' && !better[k] ? { note: { en: ['The ridge is worse than the training mean on this metric.'], zh: ['在这个指标上，岭回归比训练集均值差。'] } } : {}),
  })));
  return {
    id: 'beyond-mc-rtt', path,
    title: { en: 'Beyond scalp EEG · one macaque’s motor-cortex spiking, finger velocity within one session', zh: '头皮 EEG 之外 · 一只猕猴运动皮层的神经元放电，同一次会话内的手指速度' },
    rows,
    notes: [{
      en: ['One macaque in one session, with training and validation trials interleaved: with one animal every figure is that animal’s, and no interval is reported, because the validation rows are correlated samples, not independent subjects. Not an official Neural Latents Benchmark score and not co-smoothing; offline, with no real-time or closed-loop claim, and no cross-day, cross-animal or human claim.'],
      zh: ['一只猕猴、一次会话，训练试次与验证试次在会话内交错：只有一只动物，每个数字都是这只动物的；不报告区间，因为验证数据行是相关的样本，不是独立的个体。这不是 Neural Latents Benchmark 的官方分数，也不是 co-smoothing；离线分析，不作实时或闭环控制方面的声明，也不涉及跨天、跨动物或人类。'],
    }],
  };
}

/** ds007420: a label-independent numerical check of the optical values. Counts only; its classifier is held. */
function opticalGroup(): ResultGroup {
  const r = bs['ds007420-optical-coverage'], path = `${BEYOND_PATH}#${BEYOND_ANCHOR.ds007420}`, n = r.cohort.people, k = r.counts, g = r.gates;
  if (g.classifier !== 'held' || g.task_code_lookup_verified !== false) throw new Error('entities.ts: the ds007420 note says its classifier is held');
  const method = 'Numerical coverage check', label: L = { en: 'Numerical coverage check (no model)', zh: '数值覆盖核查（不是模型）' };
  const condition: L = { en: 'Every optical value of every recording', zh: '每段记录的每个光学数值' };
  return {
    id: 'beyond-ds007420', path,
    title: { en: 'Beyond scalp EEG · human fNIRS recordings, numerical coverage (counts, not a score)', zh: '头皮 EEG 之外 · 人类 fNIRS 记录的数值覆盖（计数，不是分数）' },
    rows: [
      { path, method, label, condition, metric: { en: 'Finite and positive values', zh: '有限且为正的数值' }, value: fig(k.positive, 'count', BS), of: fig(k.optical_values, 'count', BS), people: n,
        note: { en: ['Across ', fig(r.cohort.recordings, 'count', BS), ' recordings and ', fig(r.cohort.recording_channels, 'count', BS), ' recording-channels; ', fig(k.nonfinite, 'count', BS), ' non-finite, ', fig(k.zero, 'count', BS), ' zero and ', fig(k.negative, 'count', BS), ' negative values.'],
                zh: ['共 ', fig(r.cohort.recordings, 'count', BS), ' 段记录、', fig(r.cohort.recording_channels, 'count', BS), ' 个记录通道；非有限值 ', fig(k.nonfinite, 'count', BS), ' 个，零值 ', fig(k.zero, 'count', BS), ' 个，负值 ', fig(k.negative, 'count', BS), ' 个。'] } },
      { path, method, label, condition: { en: 'Every channel of every recording', zh: '每段记录的每个通道' }, metric: { en: 'Exactly constant channels', zh: '完全恒定的通道' },
        value: fig(k.constant_channels, 'count', BS), of: fig(r.cohort.recording_channels, 'count', BS), people: n },
    ],
    notes: [{
      en: ['Counts only: they say nothing about signal quality, neural origin or decoding. No classifier score exists: the task codes have no verified lookup to hands or movements, and the event durations disagree — ', fig(g.event_duration_s.events_table, 's1', BS), ' in the events table, ',
           fig(g.event_duration_s.optical_files, 's1', BS), ' in the optical files, ', fig(g.event_duration_s.cited_paper, 's1', BS), ' in the cited paper.'],
      zh: ['只有计数：说明不了信号质量、神经来源或解码。没有任何分类器分数：任务编码没有经过核实的、与左右手或动作对应的对照表，事件时长也互相矛盾——事件表中为 ', fig(g.event_duration_s.events_table, 's1', BS), '，光学数据文件中为 ',
           fig(g.event_duration_s.optical_files, 's1', BS), '，所引论文中为 ', fig(g.event_duration_s.cited_paper, 's1', BS), '。'],
    }],
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
    groups: [...mvpGroups(name), ...fmGroups(name), ...eegptGroups(name), ...depGroups(slug), ...later],
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
  // The pilot-studies batch (pilot-studies-update.json, owner decisions of 2026-10-12): small pilots outside every
  // leaderboard. A source has a page only while its export publishes it, so the BINGO and handwriting switches can hold
  // them without rework.
  ...(psReleased('orthosis-error-detection') ? [fromRights('orthosis-error-detection', psDataset('orthosis-error-detection'),
      [orthosis64Group(), orthosis58Group(), orthosisEegptGroup()],
      { en: 'Injected orthosis device errors against standard device events, EEG only: one cohort in three configurations', zh: '注入的矫形器设备错误与标准设备事件，仅用 EEG：同一队列的三种配置' },
      'Orthosis error-detection dataset (Kueper et al. 2024)')] : []),
  ...(psReleased('bingo-imagined-speech') ? [{ ...fromRights('bingo-imagined-speech', psDataset('bingo-imagined-speech'), [bingoGroup()],
      { en: 'Inner speech of 15 matched nouns in Greek and in English, across people and languages', zh: '希腊语与英语 15 个匹配名词的内部言语，跨被试、跨语言' },
      'BINGO cross-linguistic inner-speech dataset'), rightsNote: 'bingo' as const }] : []),
  ...(psReleased('eeg-fnirs-handwriting') ? [{ ...fromRights('eeg-fnirs-handwriting', psDataset('eeg-fnirs-handwriting'), [handwritingGroup()],
      { en: 'Four released coded labels in an imagined-handwriting competition dataset, EEG only: a data-quality and methods case study', zh: '想象书写竞赛数据集中的四个已发布编码标签，仅用 EEG：一项数据质量与方法案例研究' },
      'EEG-fNIRS-based Handwriting Trajectory Dataset'), rightsNote: 'handwriting' as const }] : []),
  ...(psReleased('refed') ? [fromRights('refed', psDataset('refed'), [refedGroup()],
      { en: 'Self-reported valence and arousal while watching videos: a stored-clip diagnostic', zh: '观看视频时自评的效价与唤醒度：一项存储片段诊断' },
      'REFED emotion dataset (EEG-fNIRS)')] : []),
  // The beyond-scalp batch (beyond-scalp-update.json): human fNIRS, one macaque's intracortical spiking and an fNIRS
  // coverage check, each its own species, signal and metric. FALCON H2 and Rabut et al. are status only: no page.
  ...(bsReleased('bak-fnirs') ? [{ ...fromRights('bak-fnirs', (beyond.datasets as any)['bak-fnirs'], [bakGroup()],
      { en: 'Human fNIRS: right-hand, left-hand and foot tapping, a person left out at a time', zh: '人类 fNIRS：右手、左手手指敲击与脚部敲击，每次留出一名被试' },
      'Bak et al. fNIRS finger- and foot-tapping dataset'), technique: 'Functional near-infrared spectroscopy', signal: { en: 'fNIRS', zh: 'fNIRS ' } }] : []),
  ...(bsReleased('nlb-mc-rtt') ? [{ ...fromRights('nlb-mc-rtt', (beyond.datasets as any)['nlb-mc-rtt'], [nlbGroup()],
      { en: 'One macaque’s motor-cortex spiking during self-paced reaching: finger velocity', zh: '一只猕猴自主伸手时运动皮层的神经元放电：手指速度' },
      'MC_RTT (Neural Latents Benchmark)'), technique: 'Intracortical microelectrode array recording',
    signal: { en: 'intracortical spiking', zh: '皮层内神经元放电' } }] : []),
  ...(bsReleased('ds007420') ? [{ ...fromRights('ds007420', (beyond.datasets as any)['ds007420'], [opticalGroup()],
      { en: 'Human fNIRS recordings: a numerical coverage check, no decoding', zh: '人类 fNIRS 记录：数值覆盖核查，不做解码' },
      'OpenNeuro ds007420 · multi-distance fNIRS'), technique: 'Functional near-infrared spectroscopy', signal: { en: 'fNIRS', zh: 'fNIRS ' } }] : []),
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
 * Models listed in the directory that have no result in the core matrix or beside it, and why (status as
 * shown, directory-status.ts). REVE Base left this list on 2026-10-04 (evaluated in v9);
 * MIRepNet and EEG-DINO joined it as catalogue-only entries. EEGPT left it on 2026-10-13: its core-matrix cells are
 * published beside the matrix (eegpt-core.ts), with a method page that links its pilot comparison. An entry with a
 * result elsewhere on the site would link it (`page`); none has one now.
 */
export const unmeasuredModels: { name: string; family: string; status: string; url?: string; released?: string; checked?: string;
                                 page?: { path: string; label: L } }[] = [
  ...data.models.map(m => ({ m, shown: modelDirectoryStatus(m) })).filter(({ shown }) => !shown.status.startsWith('Evaluated'))
    .map(({ m, shown }) =>
      // An overridden status keeps the released one and its check date beside it.
      ({ name: m.name, family: m.family, status: shown.status, url: m.url ?? undefined,
         released: shown.override?.released, checked: shown.override?.checked, page: shown.override?.page })),
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
    methods: p.core ? p.core.map(id => coreName(p.track, id)) : p.eegpt ? ['EEGPT'] : (p.models ?? []).map(id => fmModelById[id].name),
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
