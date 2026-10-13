/**
 * The Chinese for the EEGPT core export's own prose (eegpt-core-update.json): its footnotes, the model's terms and
 * inputs, the pretraining-exposure statement and the directory note. Keyed by the exact English, as
 * foundation-models-zh.ts is for the further encoders, so the export itself is never touched: a sentence that changes
 * without its translation fails the build (eegptText throws on a missing key), and check-workbench.mjs refuses a key
 * that matches no text in the export, and a translation that does not carry exactly its English's numbers.
 *
 * Glossary (src/data/i18n.ts): pretraining exposure is 是否出现在预训练数据中, never 暴露; a readout head is 分类头;
 * a patch (a transformer input) is 片段, glossed 片段（patch） at first use; a summary token is 汇总 token.
 */
import type { Locale } from './i18n';

export const eegptZh: Record<string, string> = {
  // Footnotes.
  'On the P300 and semantic targets, one-second windows ran as four real 0.25-second patches: the patch grid was set to four after the encoder was built, with no padding. EEGPT’s encoder treats each time patch on its own, so this is numerically the same as building it for 256-sample inputs, as the Orthosis pilot built it for its 128-sample windows.':
    'P300 与语义目标两个协议的一秒时间窗按四个实际的 0.25 秒片段（patch）运行：编码器构建之后才把片段网格设为四个，没有任何填充。EEGPT 的编码器对每个时间片段分别处理，所以这在数值上等同于直接按 256 个采样点的输入构建编码器，就像 Orthosis 试点按它 128 个采样点的时间窗构建编码器那样。',
  'PO5 and PO6 use channel embeddings that EEGPT’s pretraining never trained: they are two of the four names in its 62-name channel dictionary (AF7, AF8, PO5, PO6) that its 58-electrode pretraining montage leaves out. The other six channels here, and all four of the 4-channel subset, use trained embeddings.':
    'PO5 与 PO6 所用的通道嵌入在 EEGPT 的预训练中从未训练过：EEGPT 的通道字典共 62 个名称，其中四个（AF7、AF8、PO5、PO6）不在它 58 电极的预训练电极布局中，这两个通道就在其中。这里其余六个通道，以及 4 通道子集的全部四个通道，用的都是训练过的嵌入。',
  'For context: BETA is not in EEGPT’s published pretraining list, but the Tsinghua 40-target SSVEP benchmark (Wang et al., 2017) is, as TSU. BETA’s authors describe BETA as an extension of that benchmark, from the same group with the same 40-target layout and its own recordings; whether anyone took part in both is not stated.':
    '背景：BETA 不在 EEGPT 作者公开的预训练数据清单中，但清华大学的 40 目标 SSVEP 基准数据集（Wang 等，2017）在清单中，名为 TSU。BETA 的作者把 BETA 描述为该基准的扩展：出自同一团队，采用相同的 40 目标布局，记录是它自己的；两者是否有共同的被试，作者没有说明。',
  'Every core window is shorter than EEGPT’s 4-second pretraining window: 1 or 2 seconds, and sleep as fifteen 2-second segments. The encoder computes each 0.25-second patch the same way at any length; a shorter window gives fewer patches to average.':
    '每个核心时间窗都比 EEGPT 预训练用的 4 秒时间窗短：1 秒或 2 秒，睡眠则是十五段各 2 秒的数据。无论时间窗多长，编码器对每个 0.25 秒片段的计算方式都相同；时间窗越短，可供平均的片段越少。',
  'The readout is the site’s fixed probe on the frozen summary tokens, as for the published LaBraM and CBraMod rows: ridge (alpha 100) on 2,048 pooled values, and on idle a per-person logistic head. It is not the authors’ downstream probe, a learnable spatial filter with a linear head, and the windows are fed without the average reference EEGPT was pretrained with.':
    '读出用的是本站固定的分类头，接在冻结的汇总 token 上，与已发布的 LaBraM、CBraMod 各行相同：在 2,048 个池化值上做岭回归（alpha 100），空闲协议上则是逐人的逻辑回归分类头。它不是作者在下游任务中用的分类头（可学习的空间滤波器加线性分类头）；输入的时间窗也没有做 EEGPT 预训练时用的平均参考。',
  'ds003810 is recorded at 125 Hz; its windows reach the encoder upsampled to 256 Hz, so they carry nothing above 62.5 Hz.':
    'ds003810 的采样率为 125 Hz；它的时间窗上采样到 256 Hz 后送入编码器，所以不含 62.5 Hz 以上的成分。',
  'Same run as the published LaBraM idle row; the published CBraMod idle row comes from another run, so a comparison with it is across runs. The window balanced accuracy and AUROC were computed from this run’s saved probabilities with the definitions of the further foundation-encoder rows; the run itself recorded the counts.':
    '与已发布的 LaBraM 空闲行出自同一次运行；已发布的 CBraMod 空闲行来自另一次运行，所以与它的比较是跨运行的。窗口平衡准确率与 AUROC 按更多基础模型编码器各行的定义，从这次运行保存的概率算出；各项计数是运行本身记录的。',
  // The model and its terms.
  'unresolved: the checkpoint’s own licence and terms could not be read from its hosting record, and the repository’s code licence is not evidence that it covers the weights':
    '尚未厘清：无法从检查点的托管记录中读到它自己的许可与条款，代码仓库的代码许可也不能证明它涵盖权重',
  'the repository’s source code only': '仅限代码仓库中的源代码',
  'no original or converted weights are distributed; the hashes identify the checkpoint used and grant nothing':
    '不分发任何原始或转换后的权重；哈希只用于标识所用的检查点，不授予任何权利',
  'Published by the owner’s decision, aggregate results only, as the pilot comparison is. The checkpoint’s licence could not be read; no publisher prohibition on independently computed aggregate results was found; no original or converted weights are distributed.':
    '依据所有者的决定发布，只发布聚合结果，与那项试点比较相同。检查点的许可无法读到；没有找到发布者禁止发布独立计算的聚合结果的规定；不分发任何原始或转换后的权重。',
  'the published 250 Hz microvolt windows, resampled to 256 Hz and divided by 1,000 (millivolts); only the recorded channels, each as its channel token (T3, T4, T5 and T6 named T7, T8, P7 and P8); no interpolation, padding, zero-filled channels or average reference':
    '已发布的 250 Hz 微伏时间窗，重采样到 256 Hz 并除以 1,000（换算为毫伏）；只用实际记录的通道，每个通道对应它自己的通道 token（T3、T4、T5、T6 分别按 T7、T8、P7、P8 命名）；不做插值、填充、补零通道或平均参考',
  'the four summary tokens averaged over time patches and concatenated: 2,048 values per window':
    '四个汇总 token 在各时间片段上取平均后拼接：每个时间窗 2,048 个值',
  'Five public datasets, as the paper’s Table 1 lists them: PhysioMI (PhysioNet motor imagery and execution), HGD, TSU (the Tsinghua 40-target SSVEP benchmark), SEED and M3CV; 58 electrodes, 256 Hz, millivolts, average reference, 4-second windows.':
    '五个公开数据集，按论文表 1 所列：PhysioMI（PhysioNet 运动想象与运动执行数据）、HGD、TSU（清华大学 40 目标 SSVEP 基准数据集）、SEED 与 M3CV；58 个电极、256 Hz、毫伏、平均参考、4 秒时间窗。',
  // Pretraining exposure: the owner's sourced wording, never a proof.
  "not in the authors' published pretraining list (checked 2026-10-12)": '不在作者公开的预训练数据清单中（2026-10-12 核查）',
  // The directory card's note.
  'Evaluated as a frozen encoder on the eight core protocols, in the same runs as the published LaBraM rows and, except on idle, the CBraMod rows, and in one pilot comparison outside every leaderboard. The checkpoint’s licence remains unresolved, and no original or converted weights are distributed; Apache-2.0 covers the repository’s code only.':
    '作为冻结编码器在八个核心协议上评测，与已发布的 LaBraM 各行、以及除空闲协议外的 CBraMod 各行出自同一批运行；另有一项不进入任何排行榜的试点比较。检查点的许可仍未厘清，不分发任何原始或转换后的权重；Apache-2.0 只涵盖代码仓库中的代码。',
};

/**
 * One of the export's sentences as a page prints it: the English as released on an English page; on a Chinese page the
 * Chinese, with the English as `original` (printed beside it where the page relies on the sentence, as the further
 * encoders' terms are).
 */
export function eegptText(en: string, locale: Locale): { text: string; original?: string } {
  if (locale === 'en') return { text: en };
  const zh = eegptZh[en];
  if (zh === undefined) throw new Error(`eegpt-core-zh.ts: no Chinese for "${en.slice(0, 80)}"`);
  return { text: zh, original: en };
}
