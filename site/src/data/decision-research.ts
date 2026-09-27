/**
 * The decision-model research track, as the roadmap section of
 * /topics/when-not-to-act/.
 *
 * A proposal, not a result. Nothing in this file is measured by this site. The
 * status below is what the page renders, and check-workbench.mjs fails the
 * build if it changes while `results` is empty, or if a figure appears inside
 * the roadmap section. Literature cards are external evidence with their own
 * limits. Their numbers are left out on purpose, so that none of them can be
 * read as ours.
 *
 * Origin: a research handoff of 2026-09-27 proposing a "Jev-style" EEG decision
 * model — an interface pattern from a vision paper (last card). The maintainer
 * chose to put the name in the section heading and the page title, for reach.
 * Wherever it is prominent, `scope` says what it is not: not an integration
 * with Jev, not an EEG-capable Jev model, no result. check-workbench.mjs
 * requires that sentence on the page. Sources were checked against their arXiv
 * and PMLR records on 2026-09-27.
 */
export const decisionRoadmap = {
  status: 'proposal',
  runStatus: 'not_run',
  results: [] as readonly never[],
  reviewedAt: '2026-09-27',
} as const;

export const decisionSources = {
  selective: { cite: 'Geifman & El-Yaniv, 2017 · Selective classification for deep neural networks', url: 'https://arxiv.org/abs/1705.08500' },
  selectivenet: { cite: 'Geifman & El-Yaniv, ICML 2019 · SelectiveNet', url: 'https://proceedings.mlr.press/v97/geifman19a.html' },
  conformal: { cite: 'Chatterjee et al., 2026 · Making conformal predictors robust in healthcare settings', url: 'https://arxiv.org/abs/2602.19483' },
  mteeg: { cite: 'Dai et al., 2026 · MTEEG: unified multi-task EEG analysis with low-rank adaptation', url: 'https://arxiv.org/abs/2604.25131' },
  neurolm: { cite: 'Jiang et al., 2024 · NeuroLM: a universal multi-task foundation model for EEG', url: 'https://arxiv.org/abs/2409.00101' },
  unimind: { cite: 'Lu et al., 2025 · UniMind: LLMs for unified multi-task brain decoding', url: 'https://arxiv.org/abs/2506.18962' },
  elm: { cite: 'Gijsen & Ritter, 2024 · EEG-language pretraining for label-efficient clinical phenotyping', url: 'https://arxiv.org/abs/2409.07480' },
  jev: { cite: 'Yu et al., 2026 · Visual Jev: decisions from shared visual context', url: 'https://arxiv.org/abs/2609.25845' },
} as const;

type SourceId = keyof typeof decisionSources;
type Route = { tag: string; title: string; body: string; boundary: string };
type Finding = [SourceId, string, string];

interface RoadmapCopy {
  eyebrow: string; h2: string; scope: string; lede: string; statusLine: string;
  routes: Route[]; routeStatus: string;
  boundaryH3: string; boundary: string; inputsNote: string;
  litH3: string; litLede: string; shows: string; limit: string;
  literature: Finding[];
  relatedH3: string; related: [string, string][];
}

export const decisionCopy: Record<'en' | 'zh', RoadmapCopy> = {
  en: {
    eyebrow: 'Research proposal · not run',
    h2: 'Jev-style decision models for EEG',
    scope: '“Jev-style” names an interface pattern: encode the signal once, then answer several explicit, typed questions about it. This is not an integration with Jev, not a Jev model that reads EEG, and not a model BCI Report has trained. There are no results here yet.',
    lede: 'A decoder has more choices than a class label. It can act, wait for more evidence, or ask for calibration. How well a model makes those choices can be measured, and nothing on this site measures it yet. This section is a plan: it has no results, and it borrows none.',
    statusLine: 'Status: proposal. No experiment in this section has been run.',
    routeStatus: 'Not run',
    routes: [
      { tag: 'First', title: 'Reliable decisions',
        body: 'Compare a fixed threshold, a simple statistical policy and a learned reject option on the same data. Report error at matched coverage, acceptance per class, and probability quality — Brier score, log loss and reliability — with calibration data kept apart from test data. Recalibration is a separate experiment, with its label cost counted.',
        boundary: 'A risk–coverage curve is defined only where something is accepted; at zero coverage there is no error rate, not a zero one.' },
      { tag: 'Then', title: 'One representation, several questions',
        body: 'On the motor-imagery and sleep protocols separately, compare independent task models, a shared encoder with fixed heads, and the same encoder with a question-conditioned head, at matched data and compute.',
        boundary: 'If fixed heads do as well for less, that is the result, and it will be reported as one.' },
      { tag: 'Later', title: 'Questions in language',
        body: 'Compare task identifiers, label templates and natural-language descriptions. Paraphrases and unseen concepts are tested separately and never merged into one zero-shot number.',
        boundary: 'Questions about negation, location or waveform shape need signal-level ground truth. Writing more prompts does not supply it.' },
    ],
    boundaryH3: 'Two limits of the existing data, before anything runs',
    boundary: 'The sleep and P300 protocols on this site use balanced subsets. A probability estimated on them describes that balance, not how often each class occurs in real use, so they can compare methods with each other but cannot give a deployment error rate. The idle protocol is cue-gated and three minutes long, so no model run on it can give a false-activation rate per hour.',
    inputsNote: 'The first input with explicit non-control states is the four-person pilot above. Further input data sets are named here once their source review is complete.',
    litH3: 'What published work shows, and what it does not',
    litLede: 'External evidence, checked against the original records on 27 September 2026. None of it was reproduced here, and its figures are left out so that none can be read as this site’s.',
    shows: 'Shows', limit: 'Does not show',
    literature: [
      ['selective', 'A trained classifier can be given a reject option with a target risk set by the user, trading coverage for error.', 'Evidence from image benchmarks. Its guarantee assumes test data that resemble the calibration data, which EEG across people and sessions often does not.'],
      ['selectivenet', 'Classification and rejection can be trained together, with risk at a chosen coverage as the explicit objective.', 'Not EEG evidence. Its guarantees do not carry over to a new participant or device by default.'],
      ['conformal', 'On EEG seizure classification, patient shift left standard conformal prediction short of its nominal coverage, and personalised calibration raised coverage substantially.', 'One clinical task. It shows that coverage must be measured under the split that will actually be used, not that conformal methods fail.'],
      ['mteeg', 'One pretrained EEG model can be adapted to several tasks at once with task-specific LoRA modules.', 'A separate adapter per task is not the same as several questions sharing one computation over the same window.'],
      ['neurolm', 'EEG tokens fed to a language model, with instruction tuning, support several EEG tasks in one model.', 'Instruction-style EEG models already exist. A multi-task result is not evidence that arbitrary questions generalise.'],
      ['unimind', 'A language-model-based EEG model can select task-aware queries to decode several tasks.', 'Its queries are internal tokens, not criteria a user writes. Cross-task averages from it do not belong in a ranking here.'],
      ['elm', 'EEG aligned with clinical reports enables zero-shot classification and retrieval in the authors’ clinical evaluations.', 'Hospital EEG and clinical phenotypes. Nothing yet about wearable devices, few channels or arbitrary concepts.'],
      ['jev', 'In vision, one encoding of an image can serve many forced-choice questions run as a batch — the “Jev-style” interface that prompted this plan.', 'Its own typed-head control gave no consistent accuracy advantage, and its training gains stayed within the task families it was trained on. Its speed-ups are vision results, not EEG ones.'],
    ],
    relatedH3: 'Where this connects',
    related: [
      ['/topics/calibration-budget/', 'How much calibration?'],
      ['/topics/does-pretraining-help/', 'Does pretraining help?'],
      ['/topics/fewer-electrodes/', 'Fewer electrodes'],
    ],
  },
  zh: {
    eyebrow: '研究提案 · 尚未运行',
    h2: 'Jev-style 的 EEG 决策模型',
    scope: '“Jev-style”指一种接口范式：信号只编码一次，再回答关于它的多个明确的、规定输出类型的问题。这里既没有接入 Jev，也不是能读 EEG 的 Jev 模型，更不是本站训练出的模型。目前还没有任何结果。',
    lede: '解码器能做的选择不止一个类别标签：它可以执行，可以等待更多证据，也可以请求校准。模型在这些选择上做得好不好，是可以测量的，而本站目前还没有测。本节是计划：没有结果，也不借用任何结果。',
    statusLine: '状态：提案。本节中的实验都尚未运行。',
    routeStatus: '尚未运行',
    routes: [
      { tag: '首先', title: '可靠的决策',
        body: '在同一份数据上比较固定阈值、简单统计策略和可学习的拒识机制。报告相同覆盖率下的错误率、各类别的接受率，以及概率质量——Brier 分数、log loss 和可靠性图——校准数据与测试数据分开。重新校准另作一项实验，并计入所需标签的代价。',
        boundary: '风险—覆盖率曲线只在有样本被接受时才有定义；覆盖率为零时没有错误率，而不是错误率为零。' },
      { tag: '随后', title: '一份表征，多个问题',
        body: '在运动想象和睡眠两个协议上分别比较：各任务独立的模型、共享编码器加固定分类头，以及同一编码器加问题条件化分类头，数据量与计算量保持一致。',
        boundary: '如果固定分类头以更低成本做得一样好，那就是结果，也会照样报告。' },
      { tag: '之后', title: '用语言提问',
        body: '比较任务标识、标签模板和自然语言描述。同义改写与未见概念分开测试，绝不合成一个“零样本”数字。',
        boundary: '关于否定、位置或波形形态的问题，需要信号层面的真值标注。多写几条提示词补不上这一点。' },
    ],
    boundaryH3: '开跑之前，现有数据的两条限制',
    boundary: '本站的睡眠和 P300 协议用的是类别平衡的子集。在上面估计出的概率描述的是这种平衡，而不是各类别在实际使用中出现的频率，所以它们可以用来比较方法之间的高下，却给不出部署时的错误率。空闲协议是提示同步的、只有三分钟，所以无论跑什么模型，都给不出每小时的误触发率。',
    inputsNote: '第一个带有明确非控制状态的输入，就是上面的四人试点。其余数据集等来源审查完成后再在这里列出。',
    litH3: '已发表的工作说明了什么、没说明什么',
    litLede: '外部证据，已于 2026 年 9 月 27 日对照原始记录核查。这里没有复现其中任何一项，也不引用它们的数字，以免被当成本站的结果。',
    shows: '说明了', limit: '没有说明',
    literature: [
      ['selective', '可以给已训练好的分类器加上拒识选项，由使用者设定目标风险，用覆盖率换取更低的错误率。', '证据来自图像基准。它的保证假设测试数据与校准数据相似，而跨被试、跨会话的 EEG 往往不满足这一点。'],
      ['selectivenet', '分类与拒识可以联合训练，把给定覆盖率下的风险作为明确的优化目标。', '不是 EEG 上的证据。它的保证默认不能迁移到新被试或新设备上。'],
      ['conformal', '在 EEG 癫痫分类上，被试之间的分布漂移使标准 conformal 预测达不到名义覆盖率，按被试个别校准能明显提高覆盖率。', '只是一项临床任务。它说明覆盖率必须在实际使用的数据划分下测量，而不是说 conformal 方法失效。'],
      ['mteeg', '一个预训练 EEG 模型可以借助任务专属的 LoRA 模块同时适配多个任务。', '每个任务一个适配器，不等于多个问题共享同一窗口上的一次计算。'],
      ['neurolm', '把 EEG token 输入语言模型并做指令微调，可以在一个模型里支持多项 EEG 任务。', '指令式 EEG 模型已经存在。多任务结果不能证明任意问题都能泛化。'],
      ['unimind', '基于语言模型的 EEG 模型可以选择与任务相关的查询，用来解码多项任务。', '这些查询是模型内部的 token，不是使用者写下的判据。它的跨任务平均值也不适合放进这里的排名。'],
      ['elm', '在作者的临床评测中，与临床报告对齐的 EEG 支持零样本分类和检索。', '医院 EEG 与临床表型。对可穿戴设备、少通道或任意概念，目前还说明不了什么。'],
      ['jev', '在视觉领域，一张图像编码一次，就能批量回答多个强制选择的问题——这就是促成本计划的“Jev-style”接口。', '它自己设置的对照——换成输出类型固定的分类头——没有带来一致的准确率提升；训练带来的提升也集中在训练中见过的任务类型上。它的加速是视觉结果，不是 EEG 结果。'],
    ],
    relatedH3: '与现有内容的联系',
    related: [
      ['/topics/calibration-budget/', '需要多少校准？'],
      ['/topics/does-pretraining-help/', '预训练有用吗？'],
      ['/topics/fewer-electrodes/', '更少的电极'],
    ],
  },
};
