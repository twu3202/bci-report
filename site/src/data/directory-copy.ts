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
  releasedStatus: string; overrideSource: string;
  datasetsEyebrow: string; datasetsH2: string; datasetsLede: string;
  dtSubjects: string; dtChannels: string;
  newsEyebrow: string; newsH2: string; newsLede: string;
}

export const directoryCopy: Record<Locale, DirectoryCopy> = {
  en: {
    modelsEyebrow: 'Model directory',
    modelsH2: 'From compact baselines to foundation models',
    modelsLede: 'Availability and measured performance are separate. Parameter counts depend on the backbone and task configuration.',
    parameters: 'parameters',
    officialSource: 'Official source ↗',
    statusChecked: (date) => `Status checked ${date}`,
    releasedStatus: 'Released status',
    overrideSource: 'Source ↗',
    datasetsEyebrow: 'Public data',
    datasetsH2: 'Public data, documented experiments',
    datasetsLede: 'Source terms are checked separately from numerical results. Unresolved data remain outside this release.',
    dtSubjects: 'Subjects',
    dtChannels: 'Channels',
    newsEyebrow: 'Field notes (external)',
    newsH2: 'Notes from the field',
    newsLede: 'Curated research updates, linked to original sources. They report other people’s results, not this site’s.',
  },
  zh: {
    modelsEyebrow: '模型目录',
    modelsH2: '从轻量基线到基础模型',
    modelsLede: '可获得性与实测表现是两回事。参数量取决于主干网络与任务配置。',
    parameters: '参数',
    officialSource: '官方来源 ↗',
    statusChecked: (date) => `状态核查于 ${date}`,
    releasedStatus: '发布时的状态',
    overrideSource: '来源 ↗',
    datasetsEyebrow: '公开数据',
    datasetsH2: '公开数据，有据可查的实验',
    datasetsLede: '来源条款与数值结果分开审查。尚未厘清的数据不纳入本次发布。',
    dtSubjects: '被试',
    dtChannels: '通道',
    newsEyebrow: '领域动态（外部）',
    newsH2: '研究前沿动态',
    newsLede: '精选研究动态，均链接至原始来源。这些是他人的结果，不是本站的。',
  },
};
