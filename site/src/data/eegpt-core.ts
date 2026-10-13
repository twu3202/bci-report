/**
 * EEGPT's eight core-matrix cells and its pretraining-attribution rows (release eegpt-core-update-20261013, owner
 * decisions of 2026-10-12 and 2026-10-13), as the pages print them: a frozen row beside the core matrix, placed as
 * the further foundation encoders' rows are; a group per protocol on each core dataset page and on EEGPT's method
 * page; its attribution rows beside the published LaBraM and CBraMod rows; each footnote beside the cells it bears on,
 * once a page; and its sourced pretraining-exposure statement.
 *
 * Read from the served file and nothing else (eegpt-core-update.json). experiments.json, deployment-topics.json and
 * the further-encoder files keep their bytes: a page that shows this row next to a released one reads both files.
 * Percent figures are the export's `percent` blocks (100 × the proportion, rounded to 12 decimals), the units the core
 * rows print in, so a tie prints as the core CSVs print it. Every figure is a `Fig` naming the file it is a leaf of;
 * check-workbench.mjs re-reads each one. Nothing is computed here.
 *
 * The build refuses an export that no longer carries what the pages print beside these figures: evaluated, the pilot
 * comparison outside every leaderboard, the checkpoint's licence unresolved, no weights distributed, Apache-2.0 the
 * repository's code licence alone.
 */
import ej from './eegpt-core-update.json';
import mvp from './mvp.json';
import { exposureDatasets } from './foundation-models';
import type { Fig, Fmt, L } from './entities';
import { eegptText, eegptZh } from './eegpt-core-zh';

export { eegptText, eegptZh };

const X = ej as any;
export const EEGPT_JSON = 'eegpt-core-update.json';
export const eegptRelease: { id: string; date: string } = { id: X.release_id, date: X.generated_at };
/** The method page's slug, and the section of each protocol page that prints the row (its dataset and method groups link it). */
export const EEGPT_SLUG = 'eegpt' as const;
export const EEGPT_ANCHOR = 'eegpt';

const fig = (raw: number, fmt: Fmt): Fig => ({ raw, fmt, src: EEGPT_JSON });
const need = (ok: unknown, what: string) => { if (!ok) throw new Error(`eegpt-core.ts: ${what}`); };

const M = X.model;
need(X.schema_version === 'bci-report-eegpt-core-update-v1' && M?.id === 'eegpt' && M.name === 'EEGPT' && M.method_slug === EEGPT_SLUG,
  'the served file is not the EEGPT core release');
need(M.weights_licence === null && M.weights_distributed === false && M.code_licence === 'Apache-2.0'
  && /source code only/.test(M.code_licence_scope) && /^unresolved/.test(M.weights_licence_status),
  'the checkpoint licence must stay unresolved, no weights distributed, Apache-2.0 the code\'s alone');
need(X.pilot_comparison?.leaderboard === false && X.pilot_comparison.file === 'pilot-studies-update.json',
  'the pilot comparison stays outside every leaderboard');
need(X.directory_status?.suggested_status === 'Evaluated' && X.directory_status.released_status === 'Rights review pending',
  'the export suggests the directory status the override shows');

/* --- The model ------------------------------------------------------------------------------------------- */

export const eegptModel = {
  name: M.name as string,
  params: fig(M.encoder_parameters, 'm2'),
  revision: M.source_revision as string,
  repository: M.repository as string,
  checkpointFile: M.checkpoint.file as string,
  checkpointSha: M.checkpoint.sha256 as string,
  conversionSha: M.checkpoint.tensor_conversion_sha256 as string,
  paper: M.paper as string,
  paperTitle: M.paper_title as string,
  paperVenue: M.paper_venue as string,
  codeLicence: M.code_licence as string,
  codeLicenceScope: M.code_licence_scope as string,
  weightsLicenceStatus: M.weights_licence_status as string,
  weightsNote: M.weights_note as string,
  rightsReview: M.rights_review as string,
  mode: M.mode as string,
  idleMode: M.idle_mode as string,
  input: M.input as string,
  pooling: M.pooling as string,
  corpus: X.pretraining_exposure.model.corpus as string,
};

/* --- The eight cells -------------------------------------------------------------------------------------- */

export interface EegptCell {
  protocol: string;
  people: Fig;
  channels: Fig;
  footnotes: string[];
  exposure: { status: string; statement: string };
  /** Accuracy protocols: balanced accuracy with its interval, macro F1 and the chance level, in the core rows' units. */
  primary?: Fig;
  interval?: [Fig, Fig];
  macroF1?: Fig;
  chance?: Fig;
  chanceFlag: 'at-or-below' | 'interval-reaches' | null;
  /**
   * The idle protocol: counts, and the window metrics as the further foundation-encoder rows define them; the detection
   * and false-activation rates are the export's percent block (the counts over their trials), as the idle table prints them.
   */
  idle?: { detected: Fig; commandTrials: Fig; falseActivations: Fig; idleTrials: Fig; abstain: Fig; windowBa: Fig; windowAuroc: Fig;
           detection: Fig; falseActivation: Fig };
}

export const eegptProtocols: string[] = X.protocols.map((p: any) => p.id);
export const eegptCells: Record<string, EegptCell> = Object.fromEntries(X.cells.map((c: any): [string, EegptCell] => {
  need(c.model === 'eegpt' && c.status === 'complete', `${c.protocol} is not a complete EEGPT cell`);
  const base = { protocol: c.protocol, people: fig(c.people, 'count'), channels: fig(c.channels, 'count'), footnotes: c.footnotes,
                 exposure: { status: c.exposure.status, statement: c.exposure.statement } };
  if (c.protocol === 'idle') {
    need(c.interval === null, 'the idle cell carries no interval');
    return [c.protocol, { ...base, chanceFlag: null, idle: {
      detected: fig(c.commands_detected, 'count'), commandTrials: fig(c.command_trials, 'count'),
      falseActivations: fig(c.idle_false_activations, 'count'), idleTrials: fig(c.idle_trials, 'count'),
      abstain: fig(c.always_abstain_people, 'count'),
      windowBa: fig(c.percent.window_balanced_accuracy, 'pct1raw'), windowAuroc: fig(c.window_auroc, 'auc3'),
      detection: fig(c.percent.command_detection, 'pct1raw'), falseActivation: fig(c.percent.idle_false_activation, 'pct1raw'),
    } }];
  }
  const p = c.percent;
  // The export's own flags, by the core rule: at or below chance, else an interval reaching it.
  const chanceFlag = c.at_or_below_chance ? 'at-or-below' : c.interval_includes_chance ? 'interval-reaches' : null;
  return [c.protocol, { ...base, chanceFlag,
    primary: fig(p.balanced_accuracy, 'pct1raw'), interval: [fig(p.interval_95[0], 'pct1raw'), fig(p.interval_95[1], 'pct1raw')],
    macroF1: fig(c.macro_f1, 'num3'), chance: fig(p.chance_level, 'pct1raw') }];
}));
need(eegptProtocols.length === 8 && eegptProtocols.every(p => eegptCells[p]), 'one cell per core protocol');

/* --- Footnotes: beside the cells they bear on, each once a page ----------------------------------------- */

export interface EegptFootnote { id: string; protocols: string[]; placement: 'row' | 'cell'; text: string }
export const eegptFootnotes: EegptFootnote[] = X.footnotes.map((f: any) => ({ id: f.id, protocols: f.protocols, placement: f.placement, text: f.text }));
export const eegptFootnoteById = Object.fromEntries(eegptFootnotes.map(f => [f.id, f])) as Record<string, EegptFootnote>;
/** The footnotes that hold for the whole row (every cell): a method page states them once, with the model. */
export const eegptRowFootnotes = eegptFootnotes.filter(f => f.placement === 'row');
for (const f of eegptFootnotes) for (const p of f.protocols)
  need(eegptCells[p]?.footnotes.includes(f.id), `footnote ${f.id} names ${p}, whose cell does not carry it`);
/** A cell's footnotes in print order: its own (cell placement) first, then the row's. */
export const footnotesOf = (protocol: string): EegptFootnote[] => {
  const ids = eegptCells[protocol].footnotes.map(id => eegptFootnoteById[id]);
  return [...ids.filter(f => f.placement === 'cell'), ...ids.filter(f => f.placement === 'row')];
};

/** The footnotes bearing on several cells (a topic table that prints some of them), each once, cell footnotes first. */
export const footnotesOn = (protocols: string[]): EegptFootnote[] => {
  const all = [...new Set(protocols.flatMap(p => footnotesOf(p)))];
  return [...all.filter(f => f.placement === 'cell'), ...all.filter(f => f.placement === 'row')];
};

/* --- The published rows: above, below or overlapping, by the export's relations ---------------------------- */

/**
 * EEGPT against each published row of a protocol, as the export states it: above or below only where the two marginal
 * 95% intervals do not overlap, with the gap between them (`gap2`, percentage points, a leaf of the export); otherwise
 * overlap. The build re-derives every relation and gap from the released rows' intervals (experiments.json) and the
 * cell's percent block, so a relation word cannot outlive the intervals it reads. The idle protocol has none.
 */
export type EegptRelation = 'above' | 'overlap' | 'below';
export interface EegptVs { row: string; name: string; family: string; relation: EegptRelation; gap?: Fig }
export interface EegptComparison { protocol: string; rows: EegptVs[]; smallest?: { row: string; gap: Fig } }
export const eegptComparisons: Record<string, EegptComparison> = Object.fromEntries(X.comparisons.protocols.map((p: any): [string, EegptComparison] => {
  const t = mvp.tracks.find(x => x.id === p.protocol);
  const c = eegptCells[p.protocol];
  need(t && c?.interval, `the comparisons name ${p.protocol}, which has no EEGPT interval`);
  const [lo, hi] = [c.interval![0].raw, c.interval![1].raw];
  need(JSON.stringify(p.rows.map((r: any) => r.row)) === JSON.stringify(t!.rows.map(r => r.id)), `${p.protocol}: one comparison per published row, in the matrix order`);
  const rows: EegptVs[] = p.rows.map((r: any) => {
    const iv = (t!.rows.find(x => x.id === r.row) as { interval?: number[] }).interval!;
    const rel: EegptRelation = lo > iv[1] ? 'above' : hi < iv[0] ? 'below' : 'overlap';
    const gap = rel === 'above' ? lo - iv[1] : rel === 'below' ? iv[0] - hi : null;
    need(r.relation === rel && (gap === null ? r.gap_pp === null : Math.abs(r.gap_pp - gap) < 1e-9),
      `${p.protocol} / ${r.row}: the export's relation is not the intervals' (${r.relation}, ${rel})`);
    return { row: r.row, name: r.name, family: r.family, relation: rel, gap: r.gap_pp === null ? undefined : fig(r.gap_pp, 'gap2') };
  });
  return [p.protocol, { protocol: p.protocol, rows,
    smallest: p.smallest_gap ? { row: p.smallest_gap.row, gap: fig(p.smallest_gap.gap_pp, 'gap2') } : undefined }];
}));
need(Object.keys(eegptComparisons).length === 7 && !eegptComparisons.idle, 'a comparison on every protocol with an interval, none on idle');
/** EEGPT's relation to one published row of a protocol. */
export const eegptVs = (protocol: string, row: string): EegptVs => {
  const r = eegptComparisons[protocol]?.rows.find(x => x.row === row);
  need(r, `no comparison of EEGPT with ${row} on ${protocol}`);
  return r!;
};

/* --- Pretraining exposure: the sourced statement, in the further encoders' formula ----------------------- */

const PE = X.pretraining_exposure;
export const eegptExposure: { checkedOn: string; statement: string; context: Record<string, string> } =
  { checkedOn: PE.checked_on, statement: PE.statement, context: PE.context };
/** One row per core dataset, in the exposure table's order and under its names, with this model's statement and sources. */
export const eegptExposureTable = (): { dataset: string; record: string; protocols: string[]; status: 'exposed' | 'not_exposed' | 'unknown';
                                         statement: string; urls: string[]; confidence?: string }[] =>
  exposureDatasets.map(d => {
    const c = PE.cells.find((x: any) => x.dataset === d.key);
    need(c && JSON.stringify(c.protocols) === JSON.stringify(d.protocols), `no exposure cell for ${d.key}`);
    return { dataset: d.name, record: d.record, protocols: d.protocols, status: c.status, statement: c.statement, urls: c.urls, confidence: c.confidence };
  });

/* --- Pretraining attribution: rows in the published deployment-topics fields ------------------------------- */

const PA = X.pretraining_attribution;
need(PA.topic === 'does-pretraining-help', 'the attribution rows belong to does-pretraining-help');
/** The rows, as deployment-topics.json writes LaBraM's and CBraMod's (track, dataset_id, initialization, value…). */
export const eegptAttributionRows: any[] = PA.rows;
export const eegptAttributionContrasts: any[] = PA.paired_contrasts;

/* --- The directory, and the pilot comparison ------------------------------------------------------------- */

export const eegptPilot: { file: string; result: string } = { file: X.pilot_comparison.file, result: X.pilot_comparison.result };

need(eegptZh[X.directory_status.note], 'the directory note has no Chinese');
/** What the directory card says: the export's status and note, in English and in Chinese. */
export const eegptDirectory: { status: string; released: string; note: L } = {
  status: X.directory_status.suggested_status, released: X.directory_status.released_status,
  note: { en: X.directory_status.note, zh: eegptZh[X.directory_status.note] },
};
