/**
 * Copy for the directory sections that moved off the home page on 2026-10-02:
 * the model directory and the external field notes (now on /methods/), and the
 * public-data register (now on /datasets/). The wording is the home page's,
 * unchanged, plus the line that says when each status was checked.
 */
import type { Locale } from './i18n';

interface DirectoryCopy {
  modelsEyebrow: string; modelsH2: string; modelsLede: string;
  parameters: string; officialSource: string;
  statusChecked: (date: string) => string;
  /** A row with no later check: its status is the one the release carried. */
  statusAsReleased: (date: string) => string;
  /** The register's own review date for a dataset row. */
  reviewed: (date: string) => string;
  releasedStatus: (status: string) => string;
  /** After the released licence on a card whose status was overridden: the licence line is the code's, as released. */
  codeAsReleased: string;
  overrideSource: string;
  /** Before a v9 model's weights licence note (2026-10-04). */
  weights: string;
  /** A catalogue-only card with no licence to state. */
  noLicence: string;
  translated: string;
  datasetsEyebrow: string; datasetsH2: string; datasetsLede: string;
  dtSubjects: string; dtChannels: string;
  newsEyebrow: string; newsH2: string; newsLede: string;
}

export const directoryCopy: Record<Locale, DirectoryCopy> = {
  en: {
    modelsEyebrow: 'Catalogue',
    modelsH2: 'Model directory: from compact baselines to foundation models',
    modelsLede: 'Parameter counts depend on the backbone and task configuration.',
    parameters: 'parameters',
    officialSource: 'Official source ↗',
    statusChecked: (date) => `Status checked ${date}`,
    statusAsReleased: (date) => `Status as released ${date}`,
    reviewed: (date) => `Rights reviewed ${date}`,
    releasedStatus: (status) => `Released status: ${status}.`,
    codeAsReleased: ' (code, as released)',
    overrideSource: 'Source ↗',
    weights: 'Weights:',
    noLicence: 'Not evaluated: no licence reviewed',
    translated: '',
    datasetsEyebrow: 'Register',
    datasetsH2: 'Public-data register: documented experiments',
    datasetsLede: 'Source terms are checked separately from numerical results. Unresolved data remain outside this release.',
    dtSubjects: 'Subjects',
    dtChannels: 'Channels',
    newsEyebrow: 'External',
    newsH2: 'Field notes: other people’s work',
    newsLede: 'Curated research updates, linked to original sources.',
  },
  zh: {
    modelsEyebrow: '目录',
    modelsH2: '模型目录：从轻量基线到基础模型',
    modelsLede: '参数量取决于主干网络与任务配置。',
    parameters: '参数',
    officialSource: '官方来源 ↗',
    statusChecked: (date) => `状态核查于 ${date}`,
    statusAsReleased: (date) => `状态以 ${date} 发布时为准`,
    reviewed: (date) => `权利审查于 ${date}`,
    releasedStatus: (status) => `发布时的状态：${status}。`,
    codeAsReleased: '（代码，发布时）',
    overrideSource: '来源 ↗',
    weights: '权重：',
    noLicence: '未评测：未审查许可',
    translated: '下面各条备注与许可说明由本站译自发布时的英文原文；许可与权利审查说明旁附英文原文。',
    datasetsEyebrow: '登记',
    datasetsH2: '公开数据登记：有据可查的实验',
    datasetsLede: '来源条款与数值结果分开审查。尚未厘清的数据不纳入本次发布。',
    dtSubjects: '被试',
    dtChannels: '通道',
    newsEyebrow: '外部',
    newsH2: '领域动态：他人的研究',
    newsLede: '精选研究动态，均链接至原始来源。',
  },
};
