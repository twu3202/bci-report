/**
 * The Chinese for the v9 export's own prose (foundation-models-update.json and its
 * per-protocol CSVs): weights licences and licence notes, row footnotes, rights
 * reviews, model notes, not-run reasons and the three pretraining-exposure
 * statements. Keyed by the exact English, as directory-zh.json is for the core
 * directory, so the export itself is never touched and a key that no longer
 * matches its text fails the build (fmText throws on a missing key;
 * check-workbench.mjs refuses a key that matches no text in the export, and a
 * translation that does not carry exactly its English's numbers).
 *
 * The pages print a translated licence, footnote, rights review or reason with
 * the released English beside it (class "note-original", lang="en"), as the
 * public-data register prints its rights notes (decided 2026-10-02): those are
 * the sentences a reader relies on, and the English is the reviewed text.
 *
 * Glossary (src/data/i18n.ts): pretraining exposure is 是否出现在预训练数据中,
 * never 暴露; percentage points are 百分点 without 个; a training epoch is 轮.
 */
import type { Locale } from './i18n';

export const fmZh: Record<string, string> = {
  // Pretraining exposure: the owner's sourced wording (2026-10-04), never a proof.
  "in the authors' published pretraining list": '在作者公开的预训练数据清单中',
  "not in the authors' published pretraining list (checked 2026-10-04)": '不在作者公开的预训练数据清单中（2026-10-04 核查）',
  'unknown: the authors do not list their pretraining data closely enough to decide': '未知：作者公开的预训练数据清单不够详细，无法判断',

  // Weights licences, as each model row states them.
  'REVE Responsible Use License v1.0 (owner-approved 2026-10-04)': 'REVE 负责任使用许可 v1.0（站点所有者于 2026-10-04 批准）',
  'CC BY-ND 4.0 (owner-approved: internal adaptation, aggregate scores only, no adapted weights or LoRA deltas shared)':
    'CC BY-ND 4.0（经站点所有者批准：仅限内部适配，只发布聚合分数，不分享任何适配后的权重或 LoRA 增量）',
  'CC BY-ND 4.0 (owner-approved terms as LUNA Base)': 'CC BY-ND 4.0（经站点所有者批准的条款同 LUNA Base）',
  'MIT': 'MIT',
  'Apache-2.0': 'Apache-2.0',
  'MIT (repo LICENSE; README reserves the paper, diagrams and the name)': 'MIT（仓库的 LICENSE；README 保留论文、示意图与名称的权利）',
  'MIT (as Base)': 'MIT（同 Base）',
  'CC-BY-4.0 (cite arXiv:2609.33487)': 'CC-BY-4.0（须引用 arXiv:2609.33487）',
  'CC BY-NC-SA 4.0 (non-commercial; aggregate scores only)': 'CC BY-NC-SA 4.0（仅限非商业用途；只发布聚合分数）',
  'MIT (checkpoint committed in the MIT repository)': 'MIT（检查点提交在采用 MIT 许可的仓库中）',
  'Apache-2.0; model card: research use only, not for diagnosis or clinical use': 'Apache-2.0；模型卡：仅供研究使用，不可用于诊断或临床',

  // Licence notes.
  'REVE Responsible Use License v1.0: aggregate scientific results only; no re-identification, model inversion, membership inference or non-consensual profiling; cite the REVE paper and name the model version; no adapted weights shared.':
    'REVE 负责任使用许可 v1.0：只发布聚合的科学结果；不做重新识别、模型反演、成员推断或未经同意的画像分析；引用 REVE 论文并写明模型版本；不分享任何适配后的权重。',
  'REVE Responsible Use License v1.0 (as REVE Base).': 'REVE 负责任使用许可 v1.0（同 REVE Base）。',
  'CC BY-ND 4.0 weights: scores from internal probing/adaptation only; no modified weights, LoRA or adapter deltas are shared; no implied endorsement by the LUNA authors; the LUNA name is not used to suggest an official release.':
    'CC BY-ND 4.0 权重：分数只来自内部的探针与适配；不分享任何修改后的权重、LoRA 或适配器增量；不代表 LUNA 作者的认可；也不借 LUNA 之名暗示这是官方发布。',
  'CC BY-ND 4.0 weights (as LUNA Base).': 'CC BY-ND 4.0 权重（同 LUNA Base）。',
  'MIT.': 'MIT。',
  'Apache-2.0.': 'Apache-2.0。',
  'MIT (repository LICENSE; the README reserves the paper, diagrams and the ST-EEGFormer name).': 'MIT（仓库的 LICENSE；README 保留论文、示意图与 ST-EEGFormer 名称的权利）。',
  'MIT (as Base).': 'MIT（同 Base）。',
  'CC-BY-4.0 weights: attribution required (cite arXiv:2609.33487).': 'CC-BY-4.0 权重：须署名（引用 arXiv:2609.33487）。',
  'CC BY-NC-SA 4.0: non-commercial; aggregate scores only; attribution required; no weights redistributed.': 'CC BY-NC-SA 4.0：仅限非商业用途；只发布聚合分数；须署名；不转发任何权重。',
  'Apache-2.0 weights; model card states research use only, not for diagnosis or clinical use.': 'Apache-2.0 权重；模型卡写明仅供研究使用，不可用于诊断或临床。',

  // Row footnotes: one per checkpoint, printed with its row.
  'Input removes the per-segment per-channel mean before the published /100 scaling (declared before scoring); a no-mean-removal sensitivity run scores P300 0.71 percentage points higher and sleep 1.40 lower.':
    '输入在已发布的 /100 缩放之前，先去掉每个片段各通道的均值（评分前已声明）；不去均值的敏感性分析中，P300 的得分高 0.71、睡眠低 1.40（单位：百分点）。',
  'Input removes the per-segment per-channel mean (declared before scoring); the no-mean-removal sensitivity run scores P300 2.06 percentage points lower and sleep 0.93 lower.':
    '输入先去掉每个片段各通道的均值（评分前已声明）；不去均值的敏感性分析中，P300 的得分低 2.06、睡眠低 0.93（单位：百分点）。',
  "Resampled to 256 Hz and truncated to whole 40-sample patches; 1-2 s windows and 4-8 channel montages are outside the authors' tested regime.":
    '重采样到 256 Hz，并截断为完整的 40 采样点片段；1–2 秒的时间窗和 4–8 通道的电极布局，都超出了作者测试过的范围。',
  'As LUNA Base. Frozen probes only.': '同 LUNA Base。只做冻结探针。',
  'p300-target and semantic-target not run: the 2 s tokenizer window cannot be met by 1 s segments without zero padding. Upstream common average reference kept on 4-8 channel montages.':
    'p300-target 与 semantic-target 未运行：分词器需要 2 秒的时间窗，1 秒的片段不补零就无法满足。在 4–8 通道的电极布局上保留了上游的共同平均参考。',
  'Published CBraMod pooling (patch mean, channels kept); LoRA effectively adapts only the V projection (1-token attention window upstream).':
    '沿用已发布的 CBraMod 池化方式（对片段取均值，保留通道）；上游的注意力窗口只有 1 个 token，所以 LoRA 实际上只适配了 V 投影。',
  'Published CBraMod pooling; LoRA on Mamba2 in_proj and out_proj (24 targets).': '沿用已发布的 CBraMod 池化方式；LoRA 作用于 Mamba2 的 in_proj 与 out_proj（共 24 个目标）。',
  'BETA cells are pretraining-exposed (BETA is in the ST-EEGFormer corpus).': 'BETA 的单元格：数据出现在预训练数据中（BETA 在 ST-EEGFormer 的预训练语料里）。',
  "BETA cells are pretraining-exposed. The authors' downstream class (1-based temporal index) was used; Large may have been pretrained with a 0-based index. Frozen probes only.":
    'BETA 的单元格：数据出现在预训练数据中。这里使用作者的下游类（时间索引从 1 开始）；Large 预训练时用的可能是从 0 开始的索引。只做冻结探针。',
  'Paper-recommended masking geometry; channel-retained pooling (C x 512). Three sibling checkpoints appear in the masking ablation panel.':
    '论文推荐的掩码几何；保留通道的池化（C × 512）。另外三个同系列检查点列在掩码消融面板中。',
  "In design: p300-target and semantic-target. The other six protocols are negative controls outside the model's design. ERP windows have no pre-stimulus baseline.":
    '设计范围内：p300-target 与 semantic-target。其余六个协议是模型设计范围之外的阴性对照。ERP 时间窗没有刺激前基线。',
  'semantic-target is pretraining-exposed (TMNRED is in the SingLEM corpus). Each channel is encoded independently; the last 0.25 s of each 2 s segment is not seen by the tokenizer.':
    'semantic-target 的数据出现在预训练数据中（TMNRED 在 SingLEM 的预训练语料里）。每个通道单独编码；每个 2 秒片段的最后 0.25 秒，分词器看不到。',
  'Pretraining exposure unknown for every core dataset (no published source list). Encoder only; no channel upsampling or reconstruction.':
    '每个核心数据集是否出现在预训练数据中都未知（作者没有公开来源清单）。只用编码器；不做通道上采样或重建。',
  'A sibling of the paper-recommended checkpoint in the masking ablation: the same architecture, corpus and recipe, another masking framework or geometry.':
    '论文推荐检查点在掩码消融中的同系列检查点：架构、语料与训练方案相同，掩码框架或几何不同。',

  // Rights reviews.
  'Accepted by the owner on 2026-10-04. Aggregate scientific results only; no re-identification, model inversion, membership inference or non-consensual profiling; the REVE paper is cited and the model version named; no adapted weights are shared.':
    '站点所有者于 2026-10-04 接受。只发布聚合的科学结果；不做重新识别、模型反演、成员推断或未经同意的画像分析；引用了 REVE 论文并写明模型版本；不分享任何适配后的权重。',
  'Owner-approved on 2026-10-04 for internal probing and adaptation with aggregate scores only. No modified weights, LoRA or adapter deltas are shared; no endorsement by the LUNA authors is implied, and the LUNA name is not used to suggest an official release.':
    '站点所有者于 2026-10-04 批准，仅用于内部的探针与适配，只发布聚合分数。不分享任何修改后的权重、LoRA 或适配器增量；不代表 LUNA 作者的认可，也不借 LUNA 之名暗示这是官方发布。',
  'Permissive weights licence; aggregate scores only, no weights redistributed.': '宽松的权重许可；只发布聚合分数，不转发权重。',
  'MIT repository licence; its README reserves the paper, the diagrams and the ST-EEGFormer name, none of which is reproduced. Aggregate scores only.':
    '仓库采用 MIT 许可；其 README 保留论文、示意图与 ST-EEGFormer 名称的权利，本站均未复制。只发布聚合分数。',
  'Attribution licence; the paper is cited beside every row. Aggregate scores only.': '署名许可；每一行旁都引用了论文。只发布聚合分数。',
  'Non-commercial share-alike weights. This site is personal noncommercial research and publishes aggregate scores only, with attribution; no weights are redistributed.':
    '非商业、相同方式共享的权重。本站是个人非商业研究，只发布聚合分数并署名；不转发任何权重。',
  'Checkpoint committed in the MIT repository; aggregate scores only.': '检查点提交在采用 MIT 许可的仓库中；只发布聚合分数。',
  'Apache-2.0 weights. The model card says research use only, not for diagnosis or clinical use; that sentence travels with its rows.':
    'Apache-2.0 权重。模型卡写明仅供研究使用，不可用于诊断或临床；这句话随它的每一行一起出现。',

  // Model notes (shared by all eight cells of a model).
  'REVE input removes the per-segment per-channel mean (declared before scoring; the published LaBraM/CBraMod rows did not); a no-mean-removal sensitivity run is stated in the row footnote.':
    'REVE 的输入去掉了每个片段各通道的均值（评分前已声明；已发布的 LaBraM/CBraMod 行没有这样做）；不去均值的敏感性分析见该行脚注。',
  'REVE input removes the per-segment per-channel mean (declared before scoring); a no-mean-removal sensitivity run is stated in the row footnote.':
    'REVE 的输入去掉了每个片段各通道的均值（评分前已声明）；不去均值的敏感性分析见该行脚注。',
  'LUNA resamples to 256 Hz and keeps whole 40-sample patches: 1 s keeps 240/256 samples, 2 s keeps 480/512.':
    'LUNA 重采样到 256 Hz，只保留完整的 40 采样点片段：1 秒保留 240/256 个采样点，2 秒保留 480/512 个。',
  "ST-EEGFormer Large uses the authors' downstream class (1-based temporal index); a label-free reconstruction check suggests Large was pretrained with a 0-based index, so its temporal sinusoid may be shifted by one position.":
    'ST-EEGFormer Large 使用作者的下游类（时间索引从 1 开始）；一项不用标签的重建检查显示，Large 预训练时用的可能是从 0 开始的索引，所以它的时间正弦编码可能错开一个位置。',
  'SingLEM tokenizer (128-sample tokens, stride 96 at 128 Hz) leaves the last 0.25 s of every 2 s segment unseen.':
    'SingLEM 的分词器（128 Hz 下每个 token 128 个采样点，步长 96）看不到每个 2 秒片段的最后 0.25 秒。',
  'ZUNA pretraining sources are not published: exposure unknown on every core dataset. 0-4 electrode coordinates per protocol are clamped to the edge of the +-0.12 m position grid as upstream does.':
    'ZUNA 没有公开预训练数据来源：每个核心数据集是否出现在预训练数据中都未知。每个协议有 0–4 个电极坐标被截到 ±0.12 m 位置网格的边缘，与上游做法相同。',

  // Cell notes (2026-10-05 review: the protocol pages' "Notes on the v9 rows" print in Chinese, the English beside).
  'BrainOmni common average reference on 4 channels removes a median 0.87 of segment channel variance.':
    'BrainOmni 在 4 个通道上做共同平均参考，去掉的片段通道方差比例中位数为 0.87。',
  'BrainOmni common average reference on 6 channels removes a median 0.45 of segment channel variance.':
    'BrainOmni 在 6 个通道上做共同平均参考，去掉的片段通道方差比例中位数为 0.45。',
  'BrainOmni keeps its upstream common average reference; on 8 channels it removes a median 0.79 of segment channel variance.':
    'BrainOmni 保留上游的共同平均参考；在 8 个通道上，它去掉的片段通道方差比例中位数为 0.79。',
  'Channel-retained pooling gives 15,360-d features (above the harness ~10k soft guideline).':
    '保留通道维度的池化得到 15,360 维特征（高于评测框架约 10k 维的软性上限）。',
  'In ERP-FM design (post-onset 1 s windows without baseline).':
    '在 ERP-FM 的设计范围内（刺激后 1 秒时间窗，不做基线校正）。',
  'In ERP-FM design (post-onset 1 s windows without baseline; pretraining used baselined, filtered epochs).':
    '在 ERP-FM 的设计范围内（刺激后 1 秒时间窗，不做基线校正；预训练用的是做过基线校正和滤波的数据段）。',
  'LUNA min-max position scaling on a 4-channel montage (see beta-8ch).':
    'LUNA 在 4 通道电极布局上对电极位置做最小-最大缩放（见 beta-8ch）。',
  'LUNA min-max position scaling on a 4-channel montage.': 'LUNA 在 4 通道电极布局上对电极位置做最小-最大缩放。',
  'LUNA min-max position scaling on a 6-channel montage.': 'LUNA 在 6 通道电极布局上对电极位置做最小-最大缩放。',
  'LUNA min-max position scaling on an 8-channel montage.': 'LUNA 在 8 通道电极布局上对电极位置做最小-最大缩放。',
  'LUNA min-max scales electrode positions over the channel set; on 4-8 channel montages a small posterior cluster is stretched to the unit cube.':
    'LUNA 在所用的通道集合上对电极位置做最小-最大缩放；在 4–8 通道的电极布局上，一小簇后部电极会被拉伸到单位立方体。',
  'Outside the ERP-FM design: negative control.': '不在 ERP-FM 的设计范围内：阴性对照。',
  'PRETRAINING-EXPOSED: BETA is in the ST-EEGFormer pretraining corpus (all 70 participants assumed).':
    '在预训练数据中：BETA 在 ST-EEGFormer 的预训练语料中（按全部 70 名被试都在其中处理）。',
  'PRETRAINING-EXPOSED: BETA is in the ST-EEGFormer pretraining corpus.': '在预训练数据中：BETA 在 ST-EEGFormer 的预训练语料中。',
  'PRETRAINING-EXPOSED: TMNRED (ds005383) is in the SingLEM pretraining corpus.':
    '在预训练数据中：TMNRED（ds005383）在 SingLEM 的预训练语料中。',
  'Point estimate at chance; reported as is.': '点估计等于随机水平；按原值报告。',
  'Point estimate below chance; reported as is.': '点估计低于随机水平；按原值报告。',
  // Not-run reasons: never a zero, always the reason.
  'BrainTokenizer needs a 512-sample window (2.0 s at 256 Hz); the published segment is 1 s = 256 samples, so upstream unfold() would zero-pad 256 of 512 samples of every window (invented samples). All upstream downstream tasks use >= 2 s windows.':
    'BrainTokenizer 需要 512 个采样点的时间窗（256 Hz 下 2.0 秒）；已发布的片段是 1 秒 = 256 个采样点，所以上游的 unfold() 会给每个时间窗的 512 个采样点补零 256 个（凭空造出的采样点）。上游所有下游任务用的时间窗都不短于 2 秒。',
  'not run by design: LUNA Large is frozen probes only in the v9 stage specification': '按设计未运行：在 v9 阶段的规格中，LUNA Large 只做冻结探针',
  'not run by design: ST-EEGFormer Large is frozen probes only': '按设计未运行：ST-EEGFormer Large 只做冻结探针',
  'not run by design: eeg-fm-masking is a frozen-probe masking ablation': '按设计未运行：eeg-fm-masking 是用冻结探针做的掩码消融',
  'not run by design: ERP-FM is frozen probes only and EEGMAT arithmetic is outside the ERP design': '按设计未运行：ERP-FM 只做冻结探针，而 EEGMAT 的心算任务不在 ERP 设计范围内',
  'catalogue only by user decision (2026-10-04); not evaluated': '按站点所有者的决定（2026-10-04）只列入目录；未评测',
  'catalogue only by user decision (2026-10-04); upstream weights carry no licence': '按站点所有者的决定（2026-10-04）只列入目录；上游权重没有附带许可',

  // The exposure table's caveats, each printed on the page of the model it names.
  "EEGMamba's list comes from the official code (five entries, matching the abstract); the paywalled paper was not read, so confidence is medium.":
    'EEGMamba 的清单来自官方代码（五项，与摘要一致）；需付费阅读的论文全文没有读过，所以把握程度为中等。',
  'SingLEM and LaBraM lists are matched by dataset name and reference; most rows carry no accession number.':
    'SingLEM 与 LaBraM 的清单按数据集名称和参考文献比对；大多数条目没有登录号。',
  "REVE's Table 7 counts 27 MOABB datasets but names 25 (26 with the open-subset card); the unnamed slot cannot be BETA or ds005342 because MOABB added those loaders only in March 2026.":
    'REVE 论文的表 7 统计了 27 个 MOABB 数据集，但只点名了 25 个（加上开放子集的数据卡为 26 个）；未点名的那一个不可能是 BETA 或 ds005342，因为 MOABB 直到 2026 年三月才加入这两个数据集的加载器。',
  "ST-EEGFormer's in-house data is not described in detail; it is the authors' own lab recordings, so it cannot be any of the seven third-party datasets.":
    'ST-EEGFormer 的实验室内部数据没有详细描述；那是作者自己实验室的记录，所以不可能是这七个第三方数据集中的任何一个。',
};

/**
 * One of the export's sentences as a page prints it: the English as released on
 * an English page; on a Chinese page the Chinese, with the English as `original`
 * where the two differ in more than punctuation (a licence name such as "MIT" is
 * one spelling everywhere; "MIT." prints "MIT。" alone).
 */
const LICENCE_NAME = /^(?:MIT|Apache-2\.0)\.?$/;
export function fmText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = fmZh[en];
  if (zh === undefined) throw new Error(`foundation-models-zh.ts: no Chinese for "${en.slice(0, 80)}"`);
  return zh === en || LICENCE_NAME.test(en) ? { text: zh } : { text: zh, original: en };
}
