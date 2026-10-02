/**
 * What each served download holds, for the Data API page and llms.txt. The file
 * list itself comes from releases.ts (every release names its files) and is
 * checked against dist/data by check-workbench.mjs, so a file can't be served
 * without a description here, or described without being served.
 */
import data from './mvp.json';
import { releases } from './releases';
import type { Locale } from './i18n';

type Text = Record<Locale, string>;
const track = (id: string) => data.tracks.find(t => t.id === id)!;
const zhTrack: Record<string, string> = {
  'mi-rest': '运动想象与静息', idle: '空闲与指令', 'beta-8ch': 'SSVEP · 8 通道', 'beta-4ch': 'SSVEP · 4 通道',
  'arithmetic-rest': '心算与静息', 'p300-target': 'P300 目标 ERP', 'semantic-target': '语义目标 ERP', 'sleep-scalp': '睡眠分期',
};

const named: Record<string, Text> = {
  'experiments.json': {
    en: 'The core matrix: every protocol with each method’s score, interval, cohort, electrode count, training mode and limitations, plus the model and dataset directories.',
    zh: '核心矩阵：每个协议下各方法的分数、区间、队列、电极数、训练方式与局限，以及模型目录和数据集目录。',
  },
  'deployment-topics.json': {
    en: 'Deployment topics: dry vs. wet sensor transfer, calibration budget, movement (SSVEP and ERP) and pretraining controls — measurements, paired contrasts, seed sensitivity and dataset citations.',
    zh: '部署专题：干湿电极迁移、校准预算、运动中的 SSVEP 与 ERP、预训练对照——测量值、配对差值、随机种子敏感性与数据集引用。',
  },
  'evidence-update.json': {
    en: 'In-ear vs. scalp sleep staging (EESM23), four vs. sixteen electrodes (Alpha Waves), and the physical head phantom, each with its rights record.',
    zh: '耳道内与头皮睡眠分期（EESM23）、4 个与 16 个电极（Alpha Waves），以及物理头模，各附权利记录。',
  },
  'clinical-update.json': {
    en: "Parkinson's disease vs. controls from resting-state EEG (ds004584) beside an age-and-sex-only comparator, the claim boundary, and status-only sources.",
    zh: '静息态 EEG 上的帕金森病与对照（ds004584），旁边并排放着只用年龄和性别的对照基线，附声明边界与仅列状态的来源。',
  },
  'adaptation-update.json': {
    en: 'LaBraM adapted to new people on EEGMAT three ways (head only, last block, rank-4 LoRA) over three seeds: scores, paired changes with people helped or harmed, trainable parameters and training time; the next-day experiment as status only.',
    zh: 'EEGMAT 上把 LaBraM 适配到新被试的三种方式（只训分类头、最后一个 Transformer 块、秩为 4 的 LoRA），3 个随机种子：分数、配对变化与提升/变差人数、可训练参数与训练时间；次日实验只列状态。',
  },
  'extension-update.json': {
    en: 'Twenty further people of the asynchronous SSVEP release under a pilot-fixed and a personal rejection threshold (detection, coverage, correct-and-accepted, false acceptance per state, people helped and harmed), and LTRSVP image-rate and recording transfer (two primary arms, paired difference, 3×3 matrix), with rights records.',
    zh: '异步 SSVEP 数据集中另外 20 名被试在试点固定阈值与逐人阈值下的结果（检测、覆盖率、被接受且正确、各状态误接受、提升与变差人数），以及 LTRSVP 的图像速率与记录迁移（两个主分析组、配对差值、3×3 矩阵），附权利记录。',
  },
  'context-update.json': {
    en: 'Screen-to-VR P300 transfer, treadmill walking speed beside a movement-nuisance comparator, and the asynchronous SSVEP non-control pilot, with audits.',
    zh: '从屏幕到 VR 的 P300 迁移、跑步机步速（旁边并排放着运动干扰对照），以及异步 SSVEP 非控制试点，附审计。',
  },
};

export function describeFile(file: string): Text {
  if (named[file]) return named[file];
  const m = file.match(/^(.+)-(results\.csv|protocol\.json)$/);
  if (!m) throw new Error(`files.ts: no description for ${file}`);
  const t = track(m[1]);
  return m[2] === 'results.csv'
    ? { en: `${t.title}: one row per method — score, interval, secondary metric, cohort and compute time.`, zh: `${zhTrack[m[1]]}：每种方法一行——分数、区间、次指标、队列与计算耗时。` }
    : { en: `${t.title}: the protocol — cohort, channels, windows, split, training budget, rights and limitations.`, zh: `${zhTrack[m[1]]}：协议——队列、通道、时间窗、数据划分、训练预算、权利与局限。` };
}

/** Every served download, newest release first, with the release that ships it. */
export const servedFiles = releases.flatMap(r => r.files.map(file => ({ file, release: r.id, date: r.date })));
