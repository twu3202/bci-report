# EEG 数据与评测证据

> 面向 bciarena.ai 的事实备忘录。网页核查截止：2026-09-09（Asia/Shanghai）。本文只记录公开资料、可实施协议和获取路径；**没有声称本站已经下载数据、训练模型或复现任何分数**。法律条款是事实摘录与产品风险判断，不是法律意见。

## 先给产品与工程的结论

1. **一期最容易做成可审计小基准的是 BNCI2014-001 + Sleep-EDF Expanded**。前者适合 4 类运动想象和跨 session，后者适合 5 类睡眠分期且下载量约 8.1 GB。两者都无需人工审批。PhysioNetMI 很适合做较大的受试者外泛化，但 LaBraM 与 EEGPT 都明确用完整 PhysioNetMI 做过预训练，因此只能在“已见预训练数据”分层中展示这两个模型，不能与未见该数据的模型混成一个“公平”名次。
2. **TUAB/TUEV 是重要临床基准，但不适合一期托管原始数据**。当前 TUH 页面要求填写机构信息、签署表格、邮件审批、配置 SSH key 后 rsync；协议明确禁止向第三方释放或再分发。站点可以提供来源、协议、脚本和本站结果元数据，不能代用户镜像原始数据。
3. **CHB-MIT 可直接下载，但先作为二期**：198 次发作、仅约 0.6% 阳性窗口（BIOT 的处理口径）使窗口分类很容易被类别不平衡和病人泄漏误导。应同时报事件级灵敏度、误报/小时、检测延迟，以及病人级 bootstrap CI，而不只报 accuracy/AUROC。
4. **OpenNeuro 是仓库，不是单一任务数据集**。每条 benchmark 必须固定 accession + snapshot DOI + BIDS 校验状态 + task/label 映射；“在 OpenNeuro 上”不能作为可比协议。
5. **论文分数不得进入本站实测总榜**。LaBraM/EEGPT/BIOT 的表格即使引用同一数据集，也常在 checkpoint、预训练重叠、通道、采样率、划窗、线性探测/全量微调、随机种子和聚合单位上不同。建议 UI 固定显示 `本站复现`、`官方 benchmark`、`论文报告` 三种 provenance，并默认只对完全相同 protocol hash 的本站复现结果排序。

## 数据集证据与采用建议

| 数据源（固定版本） | 已确认的关键数字与任务 | 获取与授权（已确认） | 未确认/不可武断处 | 一期判断 |
|---|---|---|---|---|
| **BNCI2014-001 / BCI Competition IV 2a** | 9 人；22 EEG + 3 EOG；4 类；250 Hz；2 session。MOABB 卡片给出每类 144 trials、4 s；BNCI 原站逐人提供 T/E 文件。 | BNCI 页面直接下载；标注 **CC BY-ND 4.0**，需署名。 | BY-ND 对“转换格式、裁剪、派生包是否属于 Adapted Material”的适用边界不宜由工程团队自行断言；商业使用不因该许可本身被排除，但再分发变换后的数据包应先确认。 | **是**：下载入口 + 哈希 + 本地预处理；不在本站镜像变换后的原始包。 |
| **PhysioNet EEG Motor Movement/Imagery v1.0.0** | 109 个目录/志愿者；64 通道；160 Hz；每人 14 runs：2 个 1 min baseline，4 种 2 min 条件各重复 3 次；EDF+；T0/T1/T2 的语义随 run 改变；解压约 3.4 GB。 | Open Access；网页、ZIP、wget、匿名 S3 均可；文件许可 **ODC-By 1.0**。 | PhysioNet 页面写 160 Hz，但当前 MOABB 发行说明另提 subject 88 为 128 Hz，实施时必须按文件头验证。ODC-By 明示可商业使用和再发布数据库，但不自动清除单条内容、隐私/人格等其他权利。 | **是（带污染标签）**：适合受试者外 MI；LaBraM、EEGPT 对此数据均为预训练 seen。 |
| **TUEG v2.0.2** | 官方下载页：2002–2017 年 26,846 个临床 EEG recordings；总入口称整个持续项目已有 60,000+ EEG。 | 填可编辑 PDF、机构邮箱/地址、签名，发至 `help@nedcdata.org`；通常 24–48 h；批准后 SSH key + rsync。 | “unencumbered”“可用于研究和商业化”是官方入口的宽泛表述；实际 v6.0 协议仍限制第三方转交、再识别、恶意用途，并要求结束后删除。因此具体 SaaS/模型发布方式仍应由数据提供方或法务确认。 | **否**：二期；原始数据绝不镜像。 |
| **TUAB v3.0.1** | 官方：TUEG 的 normal/abnormal 标注子集。LaBraM/BIOT 论文处理口径为 23/16 montage、256 Hz、409,455 个 10 s 样本；这些是论文派生样本数，不是官方原始规模声明。 | 与 TUEG 相同的申请和禁再分发协议。 | 官方下载页未给病例/recording 总数；论文之间出现 2,339/2,383 等 subject/recording 口径，不能在卡片里混写成同一个“样本量”。 | **否**：二期，但可先展示明确标注的论文结果页。 |
| **TUEV v2.0.1** | 官方：TUEG 子集，6 类 SPSW/GPED/PLED/EYEM/ARTF/BCKG。LaBraM/BIOT 的派生口径为 23/16 montage、256 Hz、112,491 个 5 s 样本。 | 同 TUH 申请；禁第三方释放/再分发。 | 强烈长尾；weighted F1 会被 BCKG 主导，需同时报 macro-F1、每类 recall、balanced accuracy。论文通道数取决于原始 23 channel 还是 16 bipolar montage。 | **否**：二期。 |
| **Sleep-EDF Expanded v1.0.0** | 197 个整夜 PSG + hypnogram；153 个 SC recordings、44 个 ST recordings；EEG Fpz-Cz/Pz-Oz，100 Hz；人工 R&K 分期 W/R/1/2/3/4/M/?；约 8.1 GB。 | Open Access；ZIP/wget/匿名 S3；**ODC-By 1.0**。 | 常见 “SleepEDF-20/78” 是论文子集俗称，不等于固定的 PhysioNet 版本；必须提交确切文件清单。R&K 的 3/4 合并、W 裁剪、M/? 丢弃方式会显著改分数。 | **是**：固定全量文件 manifest，并按 subject 而非夜晚/epoch 划分。 |
| **CHB-MIT v1.0.0** | 页面概述 22 位儿科受试者、23 cases；chb21 与 chb01 是同一人相隔 1.5 年；664 EDF、129 个含发作文件、共 198 seizures；多为 23 通道、256 Hz；42.6 GB。 | Open Access；ZIP/wget/匿名 S3；**ODC-By 1.0**。 | case 不等于独立 subject，chb01/chb21 必须同 split。论文的 686 recordings、326,993 个 10 s 样本是 BIOT 的处理产物，与当前 PhysioNet 664 EDF 口径不同。 | **二期**：先锁病人映射和事件评分器。 |
| **OpenNeuro 公共 snapshot** | 接受/校验 BIDS 的 MRI/PET/MEG/EEG/iEEG；公开 snapshot 有版本 DOI。 | 浏览、下载公共集不要求账户；browser、OpenNeuro CLI、DataLad、git/git-annex、S3/GraphQL 均可；新发布数据为 CC0。 | 早期数据可能曾用 CC-BY/PDDL，必须读取具体 snapshot 的许可与 `HowToAcknowledge`；CC0 也不免除学术引用和伦理边界。不同 accession 任务完全不同。 | **作为扩展入口**：先选具体 accession，再进入候选队列。 |

### 许可与再分发的可执行边界

- **ODC-By 1.0（上述三个 PhysioNet 集）**：许可文本明确授予全球、免版税、非独占使用权，包含商业使用、抽取、派生数据库与分发；公开传播数据库/派生数据库时需保留许可与权利声明，公开使用 produced work 时需注明来源。许可同时明确：它只覆盖数据库权利/合同，不必然覆盖每个内容项的版权、隐私或人格权。因此产品文案应写“数据页标为 ODC-By；仍以具体版本页和适用法律为准”，不写“毫无限制”。
- **BNCI CC BY-ND 4.0**：可以链接并提供原始下载校验；不要默认允许把滤波、重采样、重标注后的数据包作为本站下载。
- **TUH/NEDC v6.0（2025-06-03）**：协议逐字要求“不向第三方释放或再分发”，第三方应自行联系 NEDC；还要求不得再识别、不得恶意使用、结束后从系统删除。站点只发布代码、配置、统计结果和申请指引。
- **模型代码许可不等于 checkpoint 或训练数据许可**：LaBraM 仓库标 MIT、BIOT 标 MIT、EEGPT 标 Apache-2.0；BENDR 官方仓库页面未看到独立 LICENSE 声明，应在商业部署前再次核对。即使代码许可宽松，也不能据此推导权重中所用数据可以再分发。

## 模型、checkpoint 与预训练重叠

| 模型 | 一级来源确认 | 可复现入口 | 对 benchmark 的污染/公平性判断 |
|---|---|---|---|
| **BENDR** | 2021-06-23 Frontiers 正式发表。以 TUEG v1.1/v1.2 约 1.5 TB、10,000+ 人预训练；下游含 PhysioNetMI、BCIC、Sleep-EDF 等，论文表 1 采用 leave-one/multiple-subject-out。 | 官方仓库提供源码与 v0.1-alpha 权重链接，但 README 说明依赖 DN3 v0.2-alpha，复现栈较旧。 | 评 TUAB/TUEV 时与同源 TUEG 存在强域重叠；论文声称其下游 MI/睡眠数据在预训练中未见，但 checkpoint 必须固定并登记。 |
| **BIOT** | NeurIPS 2023。3.2M/约 3.3M 量级；逐通道频域 token + linear transformer；论文对 TUAB/TUEV 使用数据集既定 train/test，训练病人再 80/20 划 train/val。 | 官方 MIT 仓库含代码、三个 EEG checkpoints、TUAB/TUEV reference commands 和论文表值。 | `EEG-six-datasets-18-channels.ckpt` 明确继续在 **TUAB、TUEV、CHB-MIT、IIIC 的训练集**上训练；在这些任务上必须标成“同任务监督预训练”，不能归入 data-unseen foundation track。PREST 是 proprietary MGH resting EEG；其数据许可不可由代码仓库推导。 |
| **LaBraM** | ICLR 2024；5.8M/46M/369M 三档；2534.78 h、约 20 数据集；1 s channel patch、VQ neural spectrum tokenizer、masked token 预训练。 | 官方 MIT 仓库有 tokenizer/pretrain/TUAB/TUEV fine-tune 脚本与 checkpoints；论文给出 0.1–75 Hz、50 Hz notch、200 Hz、幅度缩放协议。 | Appendix D 明列完整 EEG Motor Movement/Imagery Dataset（109 人、47.3 h）为预训练数据，因此 PhysioNetMI 必须标 `pretraining-seen`。其预训练另含 TUAR/TUEP/TUSZ/TUSL（均为 TUEG 子集）；论文对 TUAB/TUEV 只称 recordings 不重合，这不等于已经证明患者不重合。 |
| **EEGPT（Wang et al., NeurIPS 2024）** | 论文称 10M 参数，但官方表/代码还含 Tiny/25M 等配置；mask-based dual SSL + spatio-temporal alignment。预训练表列 PhysioMI 109 人、HGD 14、TSU 35、SEED 15、M3CV 106。 | Apache-2.0 官方仓库；Figshare checkpoint；包含 linear probe/full fine-tune 脚本及 TUAB/TUEV 脚本。 | **完整 PhysioNetMI 被用于预训练**，所以在该数据集上不能作为 unseen 泛化；论文在 TUAB/TUEV 对比是 full fine-tune，而其他下游多为 linear probe，不能把各表数值直接横向排序。另有同名的 2024-10-14 arXiv 稿《Unleashing…Autoregressive Pre-training》，站点实体必须用作者/论文 ID 区分。 |

### LaBraM 原论文 TUAB 数值：只可作“论文报告”

来源为 ICLR 2024 / arXiv:2405.18765 **Table 1**：

| 方法 | 模型规模 | Balanced accuracy | AUC-PR | AUROC |
|---|---:|---:|---:|---:|
| SPaRCNet | 0.79M | 0.7896 ± 0.0018 | 0.8414 ± 0.0018 | 0.8676 ± 0.0012 |
| BIOT | 3.2M | 0.7959 ± 0.0057 | 0.8792 ± 0.0023 | 0.8815 ± 0.0043 |
| LaBraM-Base | 5.8M | 0.8140 ± 0.0019 | 0.8965 ± 0.0016 | 0.9022 ± 0.0009 |

**“±”的含义已确认**：LaBraM §3.2 写明平均值与标准差来自 5 个随机种子；不是 95% CI。数据集使用官方 train/test，训练 patients 再 80/20 分 train/validation；在 validation 选最佳模型，再在 test 评估。预处理为 0.1–75 Hz、50 Hz notch、200 Hz、按 0.1 mV 尺度归一。LaBraM 还写明 baseline 取 BIOT 论文的最佳结果；BIOT §3.1 同样说明 Table 2/3 为 5 个随机种子的 mean ± SD。故这三行内部有论文级可比依据，但仍只能显示在带原论文、表号、协议的资料页，不能伪装成本站同环境重跑。

## 建议的一期协议（可冻结为 `eeg-benchmark-v1`）

### 结果轨道

1. **Scratch**：随机初始化，完整监督训练。
2. **Frozen linear probe**：冻结 encoder，只训练预先规定的线性头；不得偷偷加入多层适配器。
3. **Full fine-tune**：统一预算微调全部参数。
4. **Pretraining-seen**：预训练曾使用同一 dataset 的任何部分，单独展示，不参与 unseen 排名。
5. **Paper-reported**：只作资料，不排名；字段必须有 paper URL、table/figure、作者口径、`±` 定义。

每个 checkpoint 都要记录 SHA-256、来源 URL、下载日期、代码 commit、参数量、预训练数据清单的 `confirmed / claimed / unknown` 状态。若作者只说“约 20 个数据集”，不能推断某个数据没被使用。

### 一期任务

| ID | 数据与任务 | 外层测试 | 主指标 | 必报补充 |
|---|---|---|---|---|
| `mi-bnci001-cross-session-4c-v1` | BNCI2014-001，四类，固定 22 EEG；明确 trial 时间窗 | 每个受试者 session T 训练、session E 测试；反向结果可另报但不平均掩盖方向 | macro balanced accuracy | Cohen's κ、macro-F1、每人分数；按受试者 bootstrap 95% CI |
| `mi-physionet-subject-4c-v1` | PhysioNetMI，只用 imagery runs，run→类别映射锁定 | 固定 subject-group 5-fold；同一人的所有 runs 只在一个 fold；内层按 subject 做 val | macro balanced accuracy | macro-F1、κ、fold 与 subject 分数；LaBraM、EEGPT 标 `pretraining-seen` |
| `sleep-edfx-subject-5c-v1` | Sleep-EDF Expanded；30 s epoch；R&K 3+4 合为 N3，丢 M/?；W 裁剪规则写死 | subject-group 10-fold；同一人的两晚绝不跨 split；SC/ST 分层 | macro-F1 | balanced accuracy、κ、每类 recall、混淆矩阵；subject bootstrap 95% CI |

建议先用 **CSP+LDA / Riemannian tangent-space + LR**（MI）和一个小型 CNN（sleep）作 sanity baselines，再接四个 foundation encoders。MOABB 官方结果页可以作为 MI pipeline 的回归参照：它明确是 within-session 5-fold，二类用 ROC-AUC、多类用 accuracy，并且表中标准差按 `(subject, session)` 聚合，不是 fold SD。它与上表的 cross-session / subject-group 主榜是不同协议，只能用于验证实现数量级。

### 先行数据接入小实验：EEGMMIDB S001--S009

- **任务映射已确认**：MNE 官方 EEGBCI 数据加载文档明确列出 runs `4, 8, 12` 为三次“左手 vs 右手运动想象”；PhysioNet 原始页定义单侧手任务中 `T1=左拳`、`T2=右拳`、`T0=休息`。因此这 27 个 EDF 可做二分类，纳入 T1/T2、排除 T0。不要把相邻的 `6, 10, 14` 混入；它们是“双拳 vs 双脚”的运动想象。
- **获取和许可已确认**：S001--S009 无需注册即可逐文件、wget 或匿名 S3 下载；文件适用 ODC-By 1.0。局部下载和研究评测符合公开访问条件；若以后公开派生数据库或镜像，必须按许可保留来源、许可和权利声明，且 ODC-By 不替代对单条内容、隐私/人格等权利的判断。
- **实验定位**：9 人 × 3 runs 的 LOSO CSP+LDA 很适合验证下载、EDF 解析、事件映射、预处理、受试者分组和评分器能否贯通；它不能估计完整 109 人上的稳定泛化，也不是 foundation model 排名。9 个外层测试主体的区间会很宽，应公开逐人分数、9 折均值及以 subject 为单位的 95% bootstrap CI。
- **最小防泄漏约束**：每折完整留出 1 人；CSP、标准化、LDA 和任何超参数选择只看其余 8 人。若要选择 CSP components 或频带，应在 8 人内再做 subject-group 内层验证；不能随机拆 epochs。所有 3 runs 都随该受试者一起进同一 split。
- **预训练重叠结论**：CSP+LDA 本身没有预训练污染。LaBraM Appendix D 与 EEGPT 官方论文/预训练目录都明确把完整 PhysioNetMI（109 人）列入预训练，因此在这 9 人上评这两者必须标 `exact-corpus / pretraining-seen`，不能声称零样本受试者外泛化。BENDR 论文把 PhysioNetMI 用作 downstream 且声明下游数据未参与其 TUEG 预训练；BIOT 已公开 checkpoint 清单未列 PhysioNetMI，但仍须绑定确切 checkpoint 和披露状态，不能只凭模型名判定。

### 二期任务

- `tuab-abnormal-v1`、`tuev-event6-v1`：取得 TUH 许可后按官方 train/test，训练病人内分 train/val；不对用户分发数据。除模型结果外发布数据版本、申请状态、预处理 manifest、split 的不可逆 hash。
- `chbmit-event-detection-v1`：chb01/chb21 合并为同一 subject；固定 patient outer split；训练窗重采样只能发生在训练折。主指标采用 event sensitivity + false alarms/hour + onset latency；窗口 AUROC/AUC-PR 只作附表。
- OpenNeuro：每次只纳入一个已审查的 accession/snapshot；先做 dataset card，再进入主任务。

## 防泄漏、统计与展示硬规则

1. **先划 subject，再切 window**。2024 年 EEG 泄漏实证显示，随机切 EEG segments 会把同一人的特征放进 train/test；其 seizure 案例中 segment split accuracy 79.1%（78.8–79.4%），subject split 降至 65.1%（61.3–69.1%）。chb01/chb21 这种同人不同 case 也要人工合并。
2. 所有数据驱动步骤都在训练折拟合：重参考选择、滤波器参数若可学习、归一化统计、坏导联阈值、重采样策略、窗口平衡、数据增强、特征选择、class weight、温度缩放、阈值与 early stopping。测试集只运行冻结变换。
3. **预训练重叠也是泄漏元数据**：分 `exact recording`、`same subject other recording`、`same corpus subset`、`same institution/domain`、`unknown` 五档。未披露清单默认 `unknown`，不能默认 clean。
4. 每个任务固定主指标，避免挑分数。多类优先 macro-F1 / balanced accuracy；binary 临床不平衡同时报 AUROC 和 AUC-PR；检测任务报事件指标。accuracy 只能在类别平衡或作为补充时使用。
5. 置信区间的独立单位是**受试者**（或临床检测中的患者），不用数十万个重叠 windows 伪造巨大 n。建议对 subject-level metric 做至少 2,000 次 stratified bootstrap 得 95% percentile CI；折间 mean±SD、seed mean±SD 与 CI 分列。
6. 模型比较用相同 outer splits 的 paired subject bootstrap；模型/数据集很多时报告多重比较校正。小样本 BNCI 的 CI 会很宽，这是事实，不应隐藏。
7. 排名键至少包含：dataset version + exact file manifest、task labels、channels/montage、sample rate、filter/reference、epoch window/stride、split manifest、checkpoint hash、training regime、seed set、metric implementation/version。任一不同即为另一个 protocol。

## 可用于网站的 6 条研究动态

以下均可做带来源的“研究动态”，日期指正式发表或 arXiv v1 日期；预印本必须显示“预印本”。

1. **2021-06-23｜BENDR 正式发表**：将 wav2vec 2.0 风格的对比式自监督迁移到 EEG，并用约 1.5 TB TUEG 预训练，再跨 MI、P300、ERN、睡眠任务检验迁移。来源：Frontiers 原文。
2. **2023-05-10｜BIOT v1 预印本公开（后收录 NeurIPS 2023）**：用逐通道 token 和 linear transformer 处理通道不匹配、可变长度和缺失值；论文摘要报告 CHB-MIT balanced accuracy 相对基线提高约 3 个百分点，预训练最多再提高约 4 个百分点。来源：arXiv v1 与 NeurIPS proceedings；不要把相对提升写成绝对准确率。
3. **2024-04-03｜MOABB 大规模可复现 benchmark 预印本**：统一复现 30 条 pipeline、36 个公开数据集（14 MI、15 P300、7 SSVEP），并加入统计 meta-analysis、运行时间和碳排维度。当前官方结果页公开具体同协议表格。来源：arXiv v1 + MOABB 官方结果页。
4. **2024-05-29｜LaBraM 论文版本公开（ICLR 2024）**：约 2,500 小时、约 20 数据集，5.8M–369M 参数；提出 VQ 神经频谱 tokenizer 和 masked EEG modeling。来源：ICLR 论文/arXiv v1。
5. **2026-06-14｜EEGDash v1 预印本**：报告目录覆盖 791 个公共记录集合、39,778 名参与者、86,051+ 小时，并以 MNE/Braindecode/BIDS validator 接入 ML；这说明规模化 EEG benchmark 的瓶颈已经从“有没有数据”转向可加载性、修复、元数据和协议版本化。来源：arXiv v1；其当前仓库 README 数字可能随目录变化，展示时保留论文快照口径。

## 一级来源与精确 URL（核查日期 2026-09-09）

1. MOABB API / evaluation 定义：https://moabb.neurotechx.com/docs/api.html
2. MOABB 官方 benchmark 结果与统计口径：https://moabb.neurotechx.com/docs/paper_results.html
3. BNCI 数据集总页（001-2014 与许可证）：https://bnci-horizon-2020.eu/database/data-sets
4. MOABB BNCI2014-001 数据卡：https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2014_001.html
5. PhysioNet EEGMMIDB v1.0.0：https://physionet.org/content/eegmmidb/1.0.0/
6. PhysioNet Sleep-EDF Expanded v1.0.0：https://physionet.org/content/sleep-edfx/1.0.0/
7. PhysioNet CHB-MIT v1.0.0：https://physionet.org/content/chbmit/1.0.0/
8. PhysioNet / Open Data Commons Attribution License 1.0：https://physionet.org/content/sleep-edfx/view-license/1.0.0/
9. TUH/NEDC 当前 corpus 与 access 页：https://isip.piconepress.com/projects/nedc/html/tuh_eeg/
10. TUH EEG 项目入口（含 research/commercialization 表述）：https://isip.piconepress.com/projects/tuh_eeg/index.shtml
11. TUH/NEDC Data Sharing Agreement v6.0, 2025-06-03：https://isip.piconepress.com/projects/nedc/forms/tuh_eeg.pdf
12. OpenNeuro User Guide：https://docs.openneuro.org/user-guide/
13. OpenNeuro FAQ / CC0 规则：https://docs.openneuro.org/faq
14. BENDR 正式论文（2021-06-23）：https://doi.org/10.3389/fnhum.2021.653659
15. BENDR 官方仓库/权重路径：https://github.com/SPOClab-ca/BENDR
16. BIOT arXiv v1（2023-05-10）与 NeurIPS 2023 论文：https://arxiv.org/abs/2305.10351 ；https://proceedings.neurips.cc/paper_files/paper/2023/file/f6b30f3e2dd9cb53bbf2024402d02295-Paper-Conference.pdf
17. BIOT 官方仓库、checkpoints、reference commands：https://github.com/ycq091044/BIOT
18. LaBraM ICLR 2024 论文（Table 1/§3.2/Appendix D）：https://arxiv.org/pdf/2405.18765
19. LaBraM 官方仓库：https://github.com/935963004/LaBraM
20. EEGPT NeurIPS 2024 论文：https://papers.neurips.cc/paper_files/paper/2024/file/4540d267eeec4e5dbd9dae9448f0b739-Paper-Conference.pdf
21. EEGPT 官方仓库及预训练数据说明：https://github.com/BINE022/EEGPT/tree/main/datasets/pretrain
22. EEG 数据泄漏实证（2024-05-03）：https://doi.org/10.3389/fnins.2024.1373515
23. MOABB 大规模研究 arXiv v1（2024-04-03）：https://arxiv.org/abs/2404.15319
24. EEGDash arXiv v1（2026-06-14）：https://arxiv.org/abs/2606.16041
25. MNE EEGBCI loader（run→任务权威实现映射）：https://mne.tools/stable/generated/mne.datasets.eegbci.load_data.html

## 尚需在实现前补证的清单

- 从每个 checkpoint 的发布文件生成 SHA-256，并保存对应 commit/tag；仓库 README 会变化，不能只存“latest”。
- 向 TUH/NEDC 书面确认：基准服务运行、公开聚合结果、允许用户提交模型但不接触数据，分别是否落在协议允许范围；当前公开文本不足以替代这一步。
- 对 LaBraM 所用 TUAR/TUEP/TUSZ/TUSL 与 TUAB/TUEV 做 patient ID 交叉审计；论文只确认 recordings disjoint。
- 核验 PhysioNetMI S088 实际 header sampling frequency，并把异常处理写进 manifest。
- Sleep-EDF 明确 SC/ST 是否混合、具体 subjects/recordings、W 裁剪与 R&K→AASM 映射；不要沿用含糊的 “SleepEDF-20/78”。
- BENDR 仓库/权重的独立软件与 checkpoint 许可未在当前仓库主页确认；商业部署前补证。
- 对所有论文种子数据执行一次来源审计：找不到原文表格、分割和 `±` 定义的行保持 `待核对`，绝不进入排行榜。
