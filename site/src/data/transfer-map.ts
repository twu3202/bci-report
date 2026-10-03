/**
 * The transfer-coverage map: which kinds of transfer this site has evidence on,
 * and in what state.
 *
 * Rows are what changes between training and test (a new person, another
 * session or day, another sensor or montage, another context, another dataset).
 * Columns are the site's own state words: Measured, Status only, Held, Not
 * measured. A state says whether evidence exists, not whether transfer works.
 *
 * What a cell may hold: links, short labels, and cohort sizes. Never a score.
 * Every cohort size is a `Fig` — a leaf of the served file it comes from, printed
 * with data-fig and re-read by check-workbench.mjs, which also pins each one to
 * the payload field it must equal. Labels and notes carry no digit of their own
 * (names such as P300 aside); this module refuses to build if one does.
 *
 * A held entry links its own row of the holds register (/releases/#hold-<id>)
 * and prints no figure; it must stand for an open hold in releases.ts, as must a
 * status-only entry that names one, so a closed hold fails the build until the
 * map moves its entry. A paired comparison of two sensor sets scored on the same
 * data is marked `comparison`: it is not a train-on-one, test-on-the-other
 * transfer. `with` names what else changes in the same contrast (movement and
 * session together, a new person and a new sensor together); it is shown in both
 * modes, so the compact map cannot read as a clean single change.
 *
 * Shown compact on the home page (labels and n) and in full on /topics/#transfer
 * (with the row's gloss and a one-line note per entry). Since 2026-10-02.
 */
import data from './mvp.json';
import deployment from './deployment-topics.json';
import evidence from './evidence-update.json';
import clinical from './clinical-update.json';
import context from './context-update.json';
import adaptation from './adaptation-update.json';
import extension from './extension-update.json';
import { holds } from './releases';
import type { Fig, L } from './entities';

export const mapStates = ['measured', 'status', 'held', 'absent'] as const;
export type MapState = typeof mapStates[number];

export interface MapEntry {
  /** `<row>:<entry>`, stable; printed as data-map so check-workbench can pin each n. */
  key: string;
  label: L;
  /** Locale-free. Held entries link their row of the holds register. */
  href?: string;
  /** Cohort sizes, largest first: each a leaf of its served file. */
  n?: Fig[];
  /** Two sensor sets scored on the same data: a paired comparison, not a transfer. */
  comparison?: boolean;
  /** What else changes at the same time, shown as a tag in both modes: the entry cannot isolate its row's change. */
  with?: L;
  /** Held and status-only entries: the open hold in releases.ts they stand for. */
  hold?: string;
  /** One line, on the full map only. */
  note?: L;
}

export interface MapRow {
  id: 'person' | 'session' | 'sensor' | 'context' | 'dataset';
  axis: L;
  gloss: L;
  cells: Record<MapState, MapEntry[]>;
}

const DEP = 'deployment-topics.json', EVI = 'evidence-update.json', CLI = 'clinical-update.json',
      CTX = 'context-update.json', ADA = 'adaptation-update.json', EXT = 'extension-update.json';
const count = (raw: number, src: string): Fig => ({ raw, fmt: 'count', src });

/** The cohort sizes behind a deployment track (one regime, if given), largest first. */
function depPeople(track: string, regime?: string): Fig[] {
  const sizes = [...new Set(deployment.rows.filter(r => r.track === track && (!regime || r.training_regime === regime))
    .map(r => r.participants))].sort((a, b) => b - a);
  if (!sizes.length) throw new Error(`transfer-map.ts: no deployment rows for ${track}${regime ? ` / ${regime}` : ''}`);
  return sizes.map(n => count(n, DEP));
}
const statusOnly = <T extends { id: string }>(list: T[], id: string): T => {
  const hit = list.find(x => x.id === id);
  if (!hit) throw new Error(`transfer-map.ts: no status-only entry ${id}`);
  return hit;
};

const ada = adaptation.results['eegmat-labram-adaptation'];
const crossSession = statusOnly(context.status_only, 'stieger-longitudinal');
const clinicalCohort = clinical.results.ds004584.cohort.people;
const vr = (context.results as Record<string, any>)['vr-pc-p300'];
const ltrsvp = extension.results['ltrsvp-rate-transfer'];

// The core matrix's new-person protocols are the ones its payload labels so.
if (!data.tracks.some(t => t.short === 'Transfer to a new person'))
  throw new Error('transfer-map.ts: the core matrix no longer labels any protocol "Transfer to a new person"');

const dryWet = depPeople('wearable-sensor-transfer', 'participant_disjoint_source_training');
const mobileErp = depPeople('mobile-erp');

export const mapRows: MapRow[] = [
  {
    id: 'person',
    axis: { en: 'Person', zh: '被试' },
    gloss: { en: 'New people: trained on others, tested on someone the model never saw', zh: '新被试：用其他人训练，在训练中没见过的人身上测试' },
    cells: {
      measured: [
        { key: 'person:core-matrix', label: { en: 'Core matrix · new-person protocols', zh: '核心矩阵 · 新被试协议' }, href: '/#overview',
          note: { en: 'Every protocol whose split is “transfer to a new person”: participant-disjoint folds.', zh: '数据划分为“迁移到新被试”的每个协议：被试不重叠的折。' } },
        { key: 'person:dry-vs-wet', label: { en: 'Dry vs. wet electrodes', zh: '干电极与湿电极' }, href: '/topics/dry-vs-wet/', n: dryWet, with: { en: 'sensor', zh: '传感器' },
          note: { en: 'Source models trained on other people, so the new person and the new sensor arrive together.', zh: '源模型用其他被试训练，所以新被试与新传感器是同时出现的。' } },
        { key: 'person:model-adaptation', label: { en: 'LaBraM adaptation · EEGMAT', zh: 'LaBraM 适配 · EEGMAT' }, href: '/topics/model-adaptation/#adaptation',
          n: [count(ada.cohort.people, ADA)],
          note: { en: 'New people, same task, zero labels from the test person.', zh: '新被试、同一任务、不使用测试被试的任何标签。' } },
        { key: 'person:mobile-ssvep', label: { en: 'Standing to walking and running, SSVEP', zh: '从站立到行走与跑动，SSVEP' }, href: '/topics/on-the-move/',
          n: depPeople('mobile-ssvep-2s', 'standing_other_participants_only'), with: { en: 'movement', zh: '运动' },
          note: { en: 'Trained on other people standing, tested on a new person on the move.', zh: '用其他被试站立时的数据训练，在运动中的新被试身上测试。' } },
        { key: 'person:pretraining', label: { en: 'Pretraining controls', zh: '预训练对照' }, href: '/topics/does-pretraining-help/',
          n: depPeople('pretraining-attribution-fixed'),
          note: { en: 'Frozen encoders with a readout fitted on other people, on a motor-imagery and a mental-workload task.', zh: '冻结编码器，分类头在其他被试上拟合，分别用于运动想象任务和脑力负荷任务。' } },
        { key: 'person:clinical', label: { en: 'Parkinson’s disease vs. controls', zh: '帕金森病与对照' }, href: '/topics/clinical-groups/',
          n: [count(clinicalCohort, CLI)],
          note: { en: 'Every person held out once; one site, and not a diagnosis.', zh: '每名被试各留出一次；单中心，也不是诊断。' } },
      ],
      status: [],
      held: [
        { key: 'person:clinical-foundation-models', hold: 'clinical-foundation-models', href: '/releases/#hold-clinical-foundation-models',
          label: { en: 'Foundation models on the clinical cohort', zh: '临床队列上的基础模型' },
          note: { en: 'Not run: the source states no physical amplitude unit.', zh: '未运行：数据源没有说明物理幅值单位。' } },
      ],
      absent: [],
    },
  },
  {
    id: 'session',
    axis: { en: 'Session / day', zh: '会话 / 天' },
    gloss: { en: 'The same person, another session or another day', zh: '同一被试，换一次会话或换一天' },
    cells: {
      measured: [
        { key: 'session:mobile-erp', label: { en: 'Mobile ERP · first session to the others', zh: '移动 ERP · 第一次会话到其余会话' },
          href: '/topics/on-the-move/#erp-heading', n: mobileErp, with: { en: 'movement', zh: '运动' },
          note: { en: 'Fitted on the person’s first session, standing; the session and the movement change together.', zh: '在该被试第一次会话（站立）上拟合；会话与运动一起变化，相互混杂。' } },
      ],
      status: [
        { key: 'session:cross-session', label: { en: 'Cross-session pilot', zh: '跨会话试点' }, href: '/topics/model-adaptation/#cross-session', hold: 'stieger-longitudinal',
          n: [count(crossSession.feasibility.people, CTX)],
          note: { en: 'One person: every score would be that person’s, so none is published.', zh: '只有一名被试：任何分数都是这个人的分数，所以不发布。' } },
      ],
      held: [
        { key: 'session:next-day', hold: 'bnci2015-001-crossday', href: '/releases/#hold-bnci2015-001-crossday',
          label: { en: 'Next-day adaptation', zh: '次日适配' },
          note: { en: 'Run and independently replayed; held for a licence and ethics review.', zh: '已运行并通过独立复核；因许可与伦理审查暂缓。' } },
      ],
      absent: [],
    },
  },
  {
    id: 'sensor',
    axis: { en: 'Sensor / montage', zh: '传感器 / 电极布局' },
    gloss: { en: 'Another sensor type or another set of electrodes', zh: '换一种传感器或另一组电极' },
    cells: {
      measured: [
        { key: 'sensor:dry-vs-wet', label: { en: 'Dry ⇄ wet electrodes', zh: '干电极 ⇄ 湿电极' }, href: '/topics/dry-vs-wet/', n: dryWet, with: { en: 'person', zh: '被试' },
          note: { en: 'Trained on one sensor type, tested on the other, in both directions.', zh: '在一种电极上训练、在另一种上测试，两个方向都做了。' } },
        { key: 'sensor:in-ear', label: { en: 'In-ear vs. scalp, sleep', zh: '耳道内与头皮，睡眠' }, href: '/topics/fewer-electrodes/#montage-finding',
          n: [count(evidence.results.eesm23.cohort.people, EVI)], comparison: true,
          note: { en: 'Both electrode sets scored on the same epochs: a paired comparison, not training on one and testing on the other.', zh: '两组电极在相同数据帧上评分：是配对比较，不是在一组上训练、在另一组上测试。' } },
        { key: 'sensor:posterior-subset', label: { en: 'Posterior subset vs. all electrodes', zh: '后部子集与全部电极' }, href: '/topics/fewer-electrodes/#posterior-subset',
          n: [count(evidence.results.alphawaves.cohort.people, EVI)], comparison: true,
          note: { en: 'A software subset of one headset, not two devices.', zh: '同一设备上的软件子集，不是两款设备。' } },
      ],
      status: [],
      held: [],
      absent: [
        { key: 'sensor:headsets', label: { en: 'From one headset or amplifier to another', zh: '从一款头戴设备或放大器换到另一款' },
          note: { en: 'Every sensor change here is within one study’s own equipment.', zh: '这里的每一次传感器变化，都发生在同一项研究自己的设备之内。' } },
      ],
    },
  },
  {
    id: 'context',
    axis: { en: 'Context', zh: '场景' },
    gloss: { en: 'Another display, movement, or image rate', zh: '换显示设备、身体运动或图像速率' },
    cells: {
      measured: [
        { key: 'context:screen-to-vr', label: { en: 'Screen ⇄ VR, P300', zh: '屏幕 ⇄ VR，P300' }, href: '/topics/screen-to-vr/',
          n: [count(vr.cohort.people, CTX)],
          note: { en: 'The same people, calibrated on one display and tested on the other.', zh: '同样的被试，在一种显示设备上校准、在另一种上测试。' } },
        { key: 'context:mobile-ssvep', label: { en: 'Standing to walking and running, SSVEP', zh: '从站立到行走与跑动，SSVEP' }, href: '/topics/on-the-move/',
          n: depPeople('mobile-ssvep-2s', 'standing_other_participants_only'), with: { en: 'person', zh: '被试' },
          note: { en: 'Trained on other people standing, tested on a new person on the move.', zh: '用其他被试站立时的数据训练，在运动中的新被试身上测试。' } },
        { key: 'context:mobile-erp', label: { en: 'Standing to walking and running, ERP', zh: '从站立到行走与跑动，ERP' }, href: '/topics/on-the-move/#erp-heading',
          n: mobileErp, with: { en: 'session', zh: '会话' },
          note: { en: 'The same person; movement and session change together.', zh: '同一被试；运动与会话一起变化。' } },
        { key: 'context:image-rate', label: { en: 'Image rate, P300', zh: '图像速率，P300' }, href: '/topics/screen-to-vr/#image-rate',
          n: [count(ltrsvp.cohort.people, EXT)], with: { en: 'recording', zh: '记录' },
          note: { en: 'Trained on one recording at one rate, tested on a different recording: rate and recording change together.', zh: '在一种速率的一段记录上训练、在另一段记录上测试：速率与记录一起变化。' } },
      ],
      status: [],
      held: [],
      absent: [],
    },
  },
  {
    id: 'dataset',
    axis: { en: 'Dataset', zh: '数据集' },
    gloss: { en: 'Trained on one dataset, tested on another', zh: '在一个数据集上训练，在另一个上测试' },
    cells: {
      measured: [],
      status: [],
      held: [],
      absent: [
        { key: 'dataset:cross-dataset', label: { en: 'Training on one dataset, testing on another', zh: '在一个数据集上训练、在另一个上测试' },
          note: { en: 'Not run here. Whether a dataset was in a model’s pretraining data is a different question.', zh: '本站还没有做过。某个数据集是否出现在预训练数据中，是另一个问题。' } },
      ],
    },
  },
];

// What the map may not say. Checked when the site builds, so a cell cannot
// carry a hand-typed figure, a held entry cannot name or link its source, and a
// held entry cannot outlive its hold.
{
  const openHolds = new Set(holds.filter(h => !h.closed).map(h => h.id));
  const keys = new Set<string>();
  const digitFree = (s: string) => !/\d/.test(s.replace(/[A-Za-z]+\d+/g, ''));
  for (const row of mapRows) for (const state of mapStates) for (const e of row.cells[state]) {
    if (keys.has(e.key) || !e.key.startsWith(`${row.id}:`)) throw new Error(`transfer-map.ts: bad or repeated key ${e.key}`);
    keys.add(e.key);
    for (const text of [e.label.en, e.label.zh ?? '', e.note?.en ?? '', e.note?.zh ?? '', e.with?.en ?? '', e.with?.zh ?? '', row.axis.en, row.axis.zh ?? '', row.gloss.en, row.gloss.zh ?? ''])
      if (!digitFree(text)) throw new Error(`transfer-map.ts: ${e.key} prints a figure that is not a cohort size: "${text}"`);
    if (state === 'held' && (!e.hold || e.href !== `/releases/#hold-${e.hold}`))
      throw new Error(`transfer-map.ts: ${e.key} must stand for a hold and link its row in the holds register`);
    // An entry standing for a hold follows it: once the hold closes, the build fails until the map moves the entry.
    if (e.hold && !openHolds.has(e.hold)) throw new Error(`transfer-map.ts: ${e.key} stands for ${e.hold}, which is not an open hold`);
    if (e.hold && state !== 'held' && state !== 'status') throw new Error(`transfer-map.ts: ${e.key} names a hold outside the Held and Status-only columns`);
    // Hold cards carry no figures (releases.ts), and a held entry is a hold card in miniature.
    if (state === 'held' && e.n) throw new Error(`transfer-map.ts: ${e.key} is held, so it prints no cohort size`);
    if ((state === 'measured' || state === 'status') && !e.href) throw new Error(`transfer-map.ts: ${e.key} needs a link to its evidence`);
    if (state === 'absent' && (e.href || e.n)) throw new Error(`transfer-map.ts: ${e.key} is not measured, so it has no link or cohort`);
  }
}
