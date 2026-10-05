/**
 * Route 1's limitations, as they travel with its rows on the dataset and method pages (review of 2026-10-05).
 *
 * The route-1 handoff asks for its required limitations "on any page that shows route-1 results". The topic page
 * carries all of them; a route-1 group on a dataset or method page carries the protocol's own boundary and the three
 * that bear on every figure in the group — calibration on cross-fit inner models, rejecting errors is not
 * out-of-distribution detection, and the difference rule with no multiplicity correction — and links the rest. The
 * English is the export's own text (reliable-decisions-update.json, `boundaries`), read here by its opening words so
 * a changed export fails the build rather than printing other words; the Chinese is keyed by that exact English, as
 * foundation-models-zh.ts is, and check-workbench.mjs holds both.
 */
import reliable from './reliable-decisions-update.json';
import type { Locale } from './i18n';

export type RdProtocol = 'arithmetic-rest' | 'beta-8ch' | 'mi-rest';
const B = reliable.results['reliable-decisions'].boundaries as { all_protocols: string[]; per_protocol: Record<RdProtocol, string> };

/** The three route-wide limitations every group carries, by the export's opening words. */
const SHARED = ['Calibration data are participant-disjoint inner out-of-fold scores', 'Rejecting likely errors on known classes',
                'A contrast is called a difference only when'];

export const rdLimitsZh: Record<string, string> = {
  // The protocols' own boundaries.
  'Balanced by design. Error rates describe a 1:1 mix and are a method comparison, not a deployment rate. Class equals recording, so recording-level differences are part of what any model or selector can use.':
    '设计上类别平衡。错误率描述的是 1:1 的混合，是方法比较，不是部署时的比率。每个类别各自是一段记录，所以记录层面的差异也是任何模型或选择器都能利用的信息。',
  'Uniform target prior by design; cue-paced lab spelling with no idle state, so no false-activation figure of any kind.':
    '设计上各目标的先验均匀；这是实验室里按提示节奏进行的拼写，没有空闲状态，所以给不出任何形式的误触发数字。',
  'Ten people, two per test fold. Bootstrap intervals are crude; no person-level dispersion is published. Balanced, so no deployment rate.':
    '十名被试，每个测试折两人。bootstrap 区间粗略；不发布按人的离散度。类别平衡，所以没有部署比率。',
  // Route-wide.
  'Calibration data are participant-disjoint inner out-of-fold scores (cross-fit). Inner models see about 3/4 of the training people, so they may be less confident than the full model whose scores are tested. This approximation is part of every calibrated figure.':
    '校准数据是与测试被试不重叠的内层折外分数（交叉拟合）。内层模型只见过约 3/4 的训练被试，所以可能比被测试分数的完整模型更不自信。这一近似体现在每一个经过校准的数字里。',
  'Rejecting likely errors on known classes is not detecting unfamiliar input. An uncertainty threshold may not flag an unseen class (https://arxiv.org/abs/2603.13324). Route 1 makes no out-of-distribution claim.':
    '拒绝已知类别上可能判错的试次，不等于识别陌生的输入：不确定性阈值未必能标出没见过的类别（https://arxiv.org/abs/2603.13324）。第一条路线不作任何分布外的声明。',
  'A contrast is called a difference only when its paired 95% participant-bootstrap interval excludes 0 (no multiplicity correction); otherwise "no difference resolved". No ranking where intervals overlap. Descriptive entries are never called differences.':
    '只有配对的 95% 被试 bootstrap 区间不含 0 时，一个对比才称为有差异（不做多重比较校正）；否则写作“不能认定有差异”。区间重叠时不排名，描述性的数值也从不称为差异。',
};

/** ds003810's contrasts are secondary: the topic page reads them only as such, and so does every group that shows them. */
export const rdSecondary = {
  en: 'Its learned-reject contrasts are secondary, not the route’s primary contrasts, and are read only as such.',
  zh: '其中可学习拒识选项的对比是次要对比，不是这条路线的主要对比，只能按次要对比来读。',
};

/** The sentences a route-1 group on a dataset or method page carries, in the page's language, the export's order. */
export function rdLimits(protocol: RdProtocol, locale: Locale): string[] {
  const shared = SHARED.map(start => {
    const hits = B.all_protocols.filter(x => x.startsWith(start));
    if (hits.length !== 1) throw new Error(`reliable-decisions-limits.ts: the export has no single limitation starting "${start}"`);
    return hits[0];
  });
  const en = [B.per_protocol[protocol], ...shared];
  const out = locale === 'en' ? en : en.map(x => {
    const zh = rdLimitsZh[x];
    if (zh === undefined) throw new Error(`reliable-decisions-limits.ts: no Chinese for "${x.slice(0, 80)}"`);
    return zh;
  });
  return protocol === 'mi-rest' ? [out[0], rdSecondary[locale], ...out.slice(1)] : out;
}
