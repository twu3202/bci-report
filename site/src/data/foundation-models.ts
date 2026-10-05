/**
 * The v9 foundation-model rows (release foundation-models-update-20261004, owner
 * approved 2026-10-04) as the pages print them: one frozen-probe row per encoder
 * checkpoint beside every core-matrix protocol, the masking-ablation siblings in
 * their own panel, the EEGMAT adaptation arms, each model's weights licence and
 * footnote, and the sourced pretraining-exposure statement of every cell.
 *
 * Read from the served files and nothing else. Matrix figures come from the
 * per-protocol CSVs (public/data/foundation-models-<protocol>.csv), whose percent
 * columns are 100 × the proportion rounded to 12 decimals, so a tie such as 63.25
 * prints 63.3 as the approved handoff does (the JSON proportion through toFixed
 * would print 63.2). Model metadata, exposure sources and the adaptation arms come
 * from foundation-models-update.json. Every figure is a `Fig` naming the file it is
 * a leaf of; check-workbench.mjs re-reads each one. Nothing is computed here but
 * the chance flag, by the core rule (at or below chance; else interval reaching
 * it), which the check holds to the CSV's own flag columns.
 *
 * The new rows never enter mvp.json (experiments.json keeps its bytes); they are
 * stacked under the core rows at build time.
 */
import fmJson from './foundation-models-update.json';
import type { Fig, Fmt, L } from './entities';

const V9 = (fmJson as any).results['foundation-models-v9'];
export const FM_JSON = 'foundation-models-update.json';
export const fmRelease: { id: string; date: string } = { id: (fmJson as any).release_id, date: (fmJson as any).generated_at };
export const fmFileOf = (protocol: string) => `foundation-models-${protocol}.csv`;
/** The section on each protocol page that prints the rows. */
export const FM_ANCHOR = 'foundation-v9';
export const FM_ABLATION_ANCHOR = 'masking-ablation';
export const FM_ADAPTATION_ANCHOR = 'v9-adaptation';

const fig = (raw: number, fmt: Fmt, src: string): Fig => ({ raw, fmt, src });

/* --- The served CSVs ------------------------------------------------------------- */

type Csv = Record<string, string>;
const csvText = import.meta.glob<string>('/public/data/foundation-models-*.csv', { query: '?raw', import: 'default', eager: true });

/** RFC 4180, as the results files are written: quoted cells may carry commas and doubled quotes. */
function parseCsv(text: string): Csv[] {
  const rows: string[][] = [];
  let row: string[] = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (ch === '"') quoted = false; else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ',') { row.push(cell); cell = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += ch;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter(r => r.length > 1);
  return body.map(r => {
    if (r.length !== head.length) throw new Error('foundation-models.ts: a CSV row does not fit its header');
    return Object.fromEntries(head.map((k, i) => [k, r[i]]));
  });
}

/** The eight core protocols, in the matrix order the export keeps. */
export const fmProtocols: { id: string; title: string; dataset: string; type: 'accuracy' | 'tradeoff'; people: number }[] =
  V9.protocols.map((p: any) => ({ id: p.id, title: p.title, dataset: p.dataset, type: p.type, people: p.people }));

const csvOf: Record<string, Csv[]> = Object.fromEntries(fmProtocols.map(p => {
  const text = csvText[`/public/data/${fmFileOf(p.id)}`];
  if (!text) throw new Error(`foundation-models.ts: ${fmFileOf(p.id)} is not served`);
  return [p.id, parseCsv(text)];
}));

/* --- Models and their pages ---------------------------------------------------------- */

/** One method page per model family; a checkpoint's row links to its family's page. */
export const fmSlugs = ['reve', 'luna', 'brainomni', 'codebrain', 'eegmamba', 'st-eegformer', 'eeg-fm-masking', 'erp-fm', 'singlem', 'zuna'] as const;
export type FmSlug = typeof fmSlugs[number];
export const fmPageNames: Record<FmSlug, string> = {
  reve: 'REVE', luna: 'LUNA', brainomni: 'BrainOmni', codebrain: 'CodeBrain', eegmamba: 'EEGMamba',
  'st-eegformer': 'ST-EEGFormer', 'eeg-fm-masking': 'eeg-fm-masking', 'erp-fm': 'ERP-FM', singlem: 'SingLEM', zuna: 'ZUNA',
};
const SLUG_OF: Record<string, FmSlug> = {
  'reve-base': 'reve', 'reve-large': 'reve', 'luna-base': 'luna', 'luna-large': 'luna', 'brainomni-base': 'brainomni',
  codebrain: 'codebrain', eegmamba: 'eegmamba', 'steegformer-base': 'st-eegformer', 'steegformer-large': 'st-eegformer',
  'eeg-fm-masking/mae-r9cm-L2': 'eeg-fm-masking', 'eeg-fm-masking/jepa-r9cm-L2': 'eeg-fm-masking',
  'eeg-fm-masking/mae-rone-L1': 'eeg-fm-masking', 'eeg-fm-masking/jepa-rone-L1': 'eeg-fm-masking',
  'erp-fm-base': 'erp-fm', singlem: 'singlem', zuna: 'zuna',
};
/** The exposure table keys a model by family (one corpus for every size), REVE by size. */
const EXPOSURE_KEY: Record<string, string> = {
  'reve-base': 'reve-base', 'reve-large': 'reve-large', 'luna-base': 'luna', 'luna-large': 'luna', 'brainomni-base': 'brainomni',
  codebrain: 'codebrain', eegmamba: 'eegmamba', 'steegformer-base': 'st-eegformer', 'steegformer-large': 'st-eegformer',
  'eeg-fm-masking/mae-r9cm-L2': 'eeg-fm-masking', 'eeg-fm-masking/jepa-r9cm-L2': 'eeg-fm-masking',
  'eeg-fm-masking/mae-rone-L1': 'eeg-fm-masking', 'eeg-fm-masking/jepa-rone-L1': 'eeg-fm-masking',
  'erp-fm-base': 'erp-fm', singlem: 'singlem', zuna: 'zuna-1.1',
};

export interface FmModel {
  id: string;
  name: string;
  slug: FmSlug;
  panel: 'matrix' | 'masking ablation';
  inputFamily: string;
  mode: string;
  idleMode: string;
  /** Encoder parameters, printed from the JSON. */
  params: Fig;
  revision: string | null;
  checkpointSha: string | null;
  paper: string;
  weightsLicence: string;
  licenceNote: string;
  footnote: string;
  rightsReview: string;
  notes: string[];
  /** "run", or the reason it was not. */
  adaptation: string;
  exposureKey: string;
}

export const fmModels: FmModel[] = V9.models.map((m: any): FmModel => {
  const slug = SLUG_OF[m.id], exposureKey = EXPOSURE_KEY[m.id];
  if (!slug || !exposureKey) throw new Error(`foundation-models.ts: no page for ${m.id}`);
  return {
    id: m.id, name: m.name, slug, panel: m.panel, inputFamily: m.input_family, mode: m.mode, idleMode: m.idle_mode,
    params: fig(m.parameters_encoder, 'm2', FM_JSON), revision: m.revision, checkpointSha: m.checkpoint_sha256, paper: m.paper,
    weightsLicence: m.weights_licence, licenceNote: m.licence_note, footnote: m.row_footnote, rightsReview: m.rights_review,
    notes: m.notes, adaptation: m.adaptation, exposureKey,
  };
});
export const fmModelById = Object.fromEntries(fmModels.map(m => [m.id, m])) as Record<string, FmModel>;
export const fmSlugOf = (id: string): FmSlug | undefined => SLUG_OF[id];
export const fmMatrixModels = fmModels.filter(m => m.panel === 'matrix');
export const fmAblationModels = fmModels.filter(m => m.panel === 'masking ablation');
/** The model whose sibling checkpoints make up the ablation panel, and the ablation's design. */
export const fmAblation: { design: string; paper: string; checkpoints: string[] } = V9.masking_ablation;
/** ZUNA 1.1's model-card sentence, which must travel with its rows. */
export const ZUNA_RESEARCH_USE = 'research use only, not for diagnosis or clinical use';
export const fmResearchUse = (m: FmModel) => m.licenceNote.includes(ZUNA_RESEARCH_USE);

/* --- Pretraining exposure: the owner's sourced statement --------------------------------- */

const E = V9.pretraining_exposure;
export type ExposureStatus = 'exposed' | 'not_exposed' | 'unknown';
export const fmExposure: { checkedOn: string; statements: Record<ExposureStatus, string>; definition: string; caveats: string[] } =
  { checkedOn: E.checked_on, statements: E.statements, definition: E.definition, caveats: E.caveats };
const datasetKeyOf = (protocol: string): string => {
  const d = E.datasets.find((x: any) => x.protocols.includes(protocol));
  if (!d) throw new Error(`foundation-models.ts: no exposure dataset for ${protocol}`);
  return d.key;
};
export interface ExposureCell { status: ExposureStatus; statement: string; urls: string[]; confidence?: string }
/** A model's exposure on a protocol's dataset, as the exposure table states it, with its sources. */
export function exposureOf(key: string, protocol: string): ExposureCell {
  const c = E.cells.find((x: any) => x.model === key && x.dataset === datasetKeyOf(protocol));
  if (!c) throw new Error(`foundation-models.ts: no exposure cell for ${key} on ${protocol}`);
  return { status: c.status, statement: c.statement, urls: c.urls, confidence: c.confidence };
}
/**
 * A model's exposure on each of the seven core datasets, as the table states it, for a
 * method page: the dataset (name, record, the protocols that use it), the statement and
 * its sources. Checkpoints of one family share a table when every cell agrees.
 */
export interface ExposureRow { dataset: string; record: string; protocols: string[]; status: ExposureStatus; statement: string; urls: string[]; confidence?: string }
export function exposureTable(key: string): ExposureRow[] {
  return E.datasets.map((d: any) => {
    const c = E.cells.find((x: any) => x.model === key && x.dataset === d.key);
    if (!c) throw new Error(`foundation-models.ts: no exposure cell for ${key} on ${d.key}`);
    return { dataset: d.name, record: d.url, protocols: d.protocols, status: c.status, statement: c.statement, urls: c.urls, confidence: c.confidence };
  });
}
/** The model's primary sources, as the exposure table records them. */
export const exposureSources = (key: string): string[] => E.models.find((x: any) => x.key === key)?.primary_sources ?? [];
/** LaBraM's and CBraMod's sources: the same statement on all seven core datasets (owner decision 2026-10-04). */
export function coreExposure(key: 'labram' | 'cbramod'): { statement: string; urls: string[]; checkedOn: string } {
  const cells = E.cells.filter((x: any) => x.model === key);
  if (cells.length !== 7 || cells.some((c: any) => c.status !== 'not_exposed' || c.statement !== E.statements.not_exposed))
    throw new Error(`foundation-models.ts: ${key} is no longer absent from its authors' list on all seven datasets`);
  return { statement: E.statements.not_exposed, urls: [...new Set<string>(cells.flatMap((c: any) => c.urls))], checkedOn: E.checked_on };
}

/* --- Rows, as each protocol page prints them --------------------------------------------- */

export interface FmRow {
  model: FmModel;
  protocol: string;
  file: string;
  status: 'complete' | 'not_run';
  reason?: string;
  mode: string;
  channels: Fig;
  people?: Fig;
  primary?: Fig;
  interval?: [Fig, Fig];
  /** Macro F1 on an accuracy protocol; the idle false-activation rate on the idle protocol. */
  secondary?: Fig;
  chance?: Fig;
  chanceFlag: 'at-or-below' | 'interval-reaches' | null;
  exposure: ExposureCell;
  /** The CSV's notes for this cell: the model's notes, then the cell's own. */
  notes: string;
  idle?: { detected: Fig; commandTrials: Fig; falseActivations: Fig; idleTrials: Fig; abstain: Fig; windowBa: Fig; windowAuroc: Fig };
}

function rowOf(protocol: string, c: Csv): FmRow {
  const model = fmModelById[c.model_id];
  if (!model || model.name !== c.model) throw new Error(`foundation-models.ts: ${fmFileOf(protocol)} names ${c.model_id} as ${c.model}`);
  const src = fmFileOf(protocol), num = (k: string) => Number(c[k]);
  const json = V9.frozen_probe.find((x: any) => x.model === model.id && x.protocol === protocol);
  const exposure = exposureOf(model.exposureKey, protocol);
  if (json.exposure.status !== exposure.status || c.pretraining_exposure !== exposure.statement)
    throw new Error(`foundation-models.ts: ${model.id} on ${protocol}: the CSV, the cell and the exposure table disagree`);
  const base = { model, protocol, file: src, mode: c.evaluation_mode, channels: fig(num('channels'), 'count', src), exposure, notes: c.notes };
  if (c.status !== 'complete') {
    if (c.primary_percent !== '' || !c.not_run_reason) throw new Error(`foundation-models.ts: ${model.id} on ${protocol} is not run without its reason`);
    return { ...base, status: 'not_run', reason: c.not_run_reason, chanceFlag: null };
  }
  const tradeoff = protocol === 'idle';
  const y = num('primary_percent');
  const iv: [Fig, Fig] | undefined = c.descriptive_interval_low_percent !== ''
    ? [fig(num('descriptive_interval_low_percent'), 'pct1raw', src), fig(num('descriptive_interval_high_percent'), 'pct1raw', src)] : undefined;
  const chance = c.chance_level_percent !== '' ? num('chance_level_percent') : null;
  const chanceFlag: FmRow['chanceFlag'] = chance === null || tradeoff ? null
    : y <= chance ? 'at-or-below' : iv && iv[0].raw <= chance ? 'interval-reaches' : null;
  return {
    ...base, status: 'complete', people: fig(num('participants'), 'count', src),
    primary: fig(y, 'pct1raw', src), interval: iv,
    secondary: fig(num('secondary_value'), tradeoff ? 'pct1raw' : 'num3', src),
    chance: chance === null ? undefined : fig(chance, 'pct1raw', src),
    chanceFlag,
    idle: tradeoff ? {
      detected: fig(num('commands_detected'), 'count', src), commandTrials: fig(num('command_trials'), 'count', src),
      falseActivations: fig(num('idle_false_activations'), 'count', src), idleTrials: fig(num('idle_trials'), 'count', src),
      abstain: fig(num('always_abstain_participants'), 'count', src),
      windowBa: fig(num('window_balanced_accuracy'), 'pct1', src), windowAuroc: fig(num('window_auroc'), 'auc3', src),
    } : undefined,
  };
}

/** Every v9 row under one protocol, in the export's order: thirteen matrix rows, then the three ablation siblings. */
export function fmRows(protocol: string): FmRow[] {
  const rows = (csvOf[protocol] ?? []).map(c => rowOf(protocol, c));
  if (rows.length !== fmModels.length || rows.some((r, i) => r.model.id !== fmModels[i].id))
    throw new Error(`foundation-models.ts: ${fmFileOf(protocol)} is not one row per checkpoint, in order`);
  return rows;
}
export const fmRowsByProtocol: Record<string, FmRow[]> = Object.fromEntries(fmProtocols.map(p => [p.id, fmRows(p.id)]));
/** Matrix rows with a score under a protocol: what a count printed for it must count. */
export const fmScored = (protocol: string) => fmRowsByProtocol[protocol].filter(r => r.model.panel === 'matrix' && r.status === 'complete');

/* --- EEGMAT adaptation: one fixed recipe on one task --------------------------------------- */

const A = V9.eegmat_adaptation;
export interface FmAdaptation {
  model: FmModel;
  frozen: { ba: Fig; interval: [Fig, Fig]; trainable: Fig };
  lora: { ba: Fig; interval: [Fig, Fig]; trainable: Fig };
  change: { mean: Fig; interval: [Fig, Fig]; excludesZero: boolean; helped: Fig; harmed: Fig; tied: Fig };
  loraTargets: string;
  exposure: { status: ExposureStatus; statement: string };
}
const arm = (a: any) => ({ ba: fig(a.balanced_accuracy, 'pct1', FM_JSON),
  interval: [fig(a.interval_95[0], 'pct1', FM_JSON), fig(a.interval_95[1], 'pct1', FM_JSON)] as [Fig, Fig],
  trainable: fig(a.trainable_parameters, 'count', FM_JSON) });
export const fmAdaptation: FmAdaptation[] = A.rows.map((r: any): FmAdaptation => {
  const p = r.paired_lora_minus_frozen;
  return {
    model: fmModelById[r.model], frozen: arm(r.arms['frozen-ce']), lora: arm(r.arms['lora-r4']),
    change: { mean: fig(p.mean_change, 'pp1', FM_JSON), interval: [fig(p.interval_95[0], 'pp1', FM_JSON), fig(p.interval_95[1], 'pp1', FM_JSON)],
              excludesZero: p.excludes_zero, helped: fig(p.helped, 'count', FM_JSON), harmed: fig(p.harmed, 'count', FM_JSON), tied: fig(p.tied, 'count', FM_JSON) },
    loraTargets: r.lora_targets, exposure: r.exposure,
  };
});
export const fmAdaptationMeta: { people: Fig; folds: Fig; seeds: Fig[]; chance: Fig; scope: string; loraRange: [Fig, Fig] } = {
  people: fig(A.people, 'count', FM_JSON), folds: fig(A.outer_folds, 'count', FM_JSON),
  seeds: A.seeds.map((s: number) => fig(s, 'count', FM_JSON)), chance: fig(A.chance_level, 'pct1', FM_JSON), scope: A.scope,
  loraRange: [fig(A.lora_parameter_range[0], 'count', FM_JSON), fig(A.lora_parameter_range[1], 'count', FM_JSON)],
};
/**
 * The published LaBraM arms the v9 adaptation reproduces its recipe from
 * (adaptation-update-20261001), as the v9 export carries them for context: the
 * head-only arm and LoRA rank 4, with the paired change and the people behind it.
 */
export const fmAdaptationContext: { model: string; release: string; frozen: FmAdaptation['frozen']; lora: FmAdaptation['lora'];
  change: Omit<FmAdaptation['change'], 'excludesZero'> & { excludesZero: boolean } } = (() => {
  const c = A.published_context, p = c.paired_lora_minus_frozen;
  return { model: c.model, release: c.release, frozen: arm(c.arms.frozen), lora: arm(c.arms['lora-r4']),
    change: { mean: fig(p.mean_change, 'pp1', FM_JSON), interval: [fig(p.interval_95[0], 'pp1', FM_JSON), fig(p.interval_95[1], 'pp1', FM_JSON)],
              excludesZero: p.interval_95[0] > 0 || p.interval_95[1] < 0,
              helped: fig(p.helped, 'count', FM_JSON), harmed: fig(p.harmed, 'count', FM_JSON), tied: fig(p.tied, 'count', FM_JSON) } };
})();
/** Models not adapted, with the export's reason. */
export const fmNotAdapted = fmModels.filter(m => m.adaptation !== 'run');

/* --- The model directory (/methods/) ---------------------------------------------------- */

export interface FmDirectoryEntry {
  /** As the export's directory suggestions name it. */
  name: string;
  slug?: FmSlug;
  models: FmModel[];
  /** The status the export suggests, as shown. */
  status: string;
  note: L;
  /** The model's paper or official page, as the export records it. */
  source?: string;
  /** A catalogue-only entry: the export's reason it was not evaluated. */
  reason?: string;
}

const suggested = (name: string): string => {
  const s = V9.directory_status.find((x: any) => x.name === name);
  if (!s) throw new Error(`foundation-models.ts: the export suggests no directory status for ${name}`);
  return s.suggested_status;
};
const reason = (model: string): string => V9.not_run.find((x: any) => x.model === model && x.protocol === 'all').reason;
const ids = (...xs: string[]) => xs.map(id => {
  const m = fmModelById[id];
  if (!m) throw new Error(`foundation-models.ts: no checkpoint ${id}`);
  return m;
});

/**
 * One card per entry the export's directory suggestions name, except REVE Base,
 * which keeps its released card with a display-layer override
 * (directory-status.ts), and EEGPT, unchanged. The notes are site-written from the
 * export's facts; the statuses are the export's.
 */
export const fmDirectory: FmDirectoryEntry[] = [
  { name: 'REVE Large', slug: 'reve', models: ids('reve-large'), status: suggested('REVE Large'), source: fmModelById['reve-large'].paper,
    note: { en: 'Frozen probes on all eight core protocols and the EEGMAT adaptation (2026-10-04), with the same corpus and terms as REVE Base.',
            zh: '在全部 8 个核心协议上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04）；预训练语料与条款同 REVE Base。' } },
  { name: 'LUNA (Base, Large)', slug: 'luna', models: ids('luna-base', 'luna-large'), status: suggested('LUNA (Base, Large)'), source: fmModelById['luna-base'].paper,
    note: { en: 'Frozen probes on all eight core protocols (2026-10-04); Base was also adapted on EEGMAT, Large was not, by design. The weights are CC BY-ND 4.0: no modified weights or adapters are shared, and no endorsement by the LUNA authors is implied.',
            zh: '在全部 8 个核心协议上做了冻结探针评测（2026-10-04）；Base 还在 EEGMAT 上做了适配，Large 按设计没有。权重为 CC BY-ND 4.0：不分享任何修改后的权重或适配器，也不代表 LUNA 作者的认可。' } },
  { name: 'BrainOmni Base', slug: 'brainomni', models: ids('brainomni-base'), status: suggested('BrainOmni Base'), source: fmModelById['brainomni-base'].paper,
    note: { en: 'Frozen probes on six of the eight core protocols and the EEGMAT adaptation (2026-10-04). The two one-second ERP protocols were not run: its tokenizer needs two-second windows.',
            zh: '在 8 个核心协议中的 6 个上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04）。两个 1 秒时间窗的 ERP 协议没有运行：它的分词器需要 2 秒的时间窗。' } },
  { name: 'CodeBrain', slug: 'codebrain', models: ids('codebrain'), status: suggested('CodeBrain'), source: fmModelById.codebrain.paper,
    note: { en: 'Frozen probes on all eight core protocols and the EEGMAT adaptation (2026-10-04), pooled as the published CBraMod rows are.',
            zh: '在全部 8 个核心协议上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04），池化方式与已发布的 CBraMod 行相同。' } },
  { name: 'EEGMamba', slug: 'eegmamba', models: ids('eegmamba'), status: suggested('EEGMamba'), source: fmModelById.eegmamba.paper,
    note: { en: 'The Neural Networks (2025) model from the CBraMod group. Frozen probes on all eight core protocols and the EEGMAT adaptation (2026-10-04).',
            zh: 'CBraMod 团队发表在 Neural Networks（2025）上的模型。在全部 8 个核心协议上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04）。' } },
  { name: 'ST-EEGFormer (Base, Large)', slug: 'st-eegformer', models: ids('steegformer-base', 'steegformer-large'), status: suggested('ST-EEGFormer (Base, Large)'), source: fmModelById['steegformer-base'].paper,
    note: { en: 'Frozen probes on all eight core protocols (2026-10-04); Base was also adapted on EEGMAT. BETA is in the authors’ published pretraining list, so both BETA protocols are flagged.',
            zh: '在全部 8 个核心协议上做了冻结探针评测（2026-10-04）；Base 还在 EEGMAT 上做了适配。BETA 在作者公开的预训练数据清单中，所以两个 BETA 协议都已标出。' } },
  { name: 'eeg-fm-masking (4 checkpoints)', slug: 'eeg-fm-masking', models: ids(...fmAblation.checkpoints), status: suggested('eeg-fm-masking (4 checkpoints)'), source: fmAblation.paper,
    note: { en: 'Four checkpoints of one masking study, as frozen probes on all eight core protocols (2026-10-04): the paper-recommended MAE checkpoint as a matrix row, three siblings in a masking ablation. Weights CC-BY-4.0.',
            zh: '同一项掩码研究的 4 个检查点，在全部 8 个核心协议上做了冻结探针评测（2026-10-04）：论文推荐的 MAE 检查点作为矩阵中的一行，另外 3 个同系列检查点放在掩码消融中。权重为 CC-BY-4.0。' } },
  { name: 'ERP-FM Base', slug: 'erp-fm', models: ids('erp-fm-base'), status: suggested('ERP-FM Base'), source: fmModelById['erp-fm-base'].paper,
    note: { en: 'Frozen probes on all eight core protocols (2026-10-04): the two ERP protocols are in its design, the other six are negative controls. Weights for non-commercial use only.',
            zh: '在全部 8 个核心协议上做了冻结探针评测（2026-10-04）：两个 ERP 协议在它的设计范围内，其余 6 个是阴性对照。权重仅限非商业用途。' } },
  { name: 'SingLEM', slug: 'singlem', models: ids('singlem'), status: suggested('SingLEM'), source: fmModelById.singlem.paper,
    note: { en: 'A single-channel encoder. Frozen probes on all eight core protocols and the EEGMAT adaptation (2026-10-04). TMNRED is in the authors’ published pretraining list, so the semantic-target protocol is flagged.',
            zh: '单通道编码器。在全部 8 个核心协议上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04）。TMNRED 在作者公开的预训练数据清单中，所以语义目标协议已标出。' } },
  { name: 'ZUNA 1.1', slug: 'zuna', models: ids('zuna'), status: suggested('ZUNA 1.1'), source: fmModelById.zuna.paper,
    note: { en: 'Frozen probes on all eight core protocols and the EEGMAT adaptation (2026-10-04). Its authors publish no pretraining list, so every cell is marked exposure unknown. The model card says research use only, not for diagnosis or clinical use.',
            zh: '在全部 8 个核心协议上做了冻结探针评测，并在 EEGMAT 上做了适配（2026-10-04）。作者没有公开预训练数据清单，所以每个单元格都标为“是否出现在预训练数据中：未知”。模型卡写明仅供研究使用，不可用于诊断或临床。' } },
  { name: 'MIRepNet', models: [], status: suggested('MIRepNet, EEG-DINO'),
    note: { en: 'Catalogue only, not evaluated: the owner’s decision of 2026-10-04.',
            zh: '按站点所有者 2026-10-04 的决定只列入目录，未评测。' }, reason: reason('MIRepNet') },
  { name: 'EEG-DINO', models: [], status: suggested('MIRepNet, EEG-DINO'),
    note: { en: 'Catalogue only, not evaluated: the owner’s decision of 2026-10-04. The upstream weights carry no licence.',
            zh: '按站点所有者 2026-10-04 的决定只列入目录，未评测。上游权重没有附带许可。' }, reason: reason('EEG-DINO') },
];
for (const m of fmModels.filter(m => m.id !== 'reve-base'))
  if (fmDirectory.filter(e => e.models.includes(m)).length !== 1) throw new Error(`foundation-models.ts: ${m.id} must be in exactly one directory card`);
/** REVE Base: its released card, now evaluated (directory-status.ts carries the override). */
export const reveBaseDirectory: { status: string; note: string; replaces: string } = (() => {
  const s = V9.directory_status.find((x: any) => x.name === 'REVE Base');
  return { status: s.suggested_status, note: s.note, replaces: s.replaces };
})();
/** EEGPT stays as released. */
export const eegptUnchanged: boolean = /^unchanged/.test(suggested('EEGPT'));
