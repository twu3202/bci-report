# Register classifier audit (R2)

**Question.** Before wave 2 shows anything the open-register classifier wrote, which of its fields are accurate enough to display?

**Answer.** Most fields hold up. Modality, paradigm, content kind, declared terms, the four `stated.*` fields, `source_claim` and `derived_from` were correct on all 60 sampled in-scope rows. Three fields fall below the 95% bar and need fixing before display:
- `in_scope`, which D11 uses as the Hugging Face population. Five of 60 sampled in-scope rows should not be counted.
- `one_line_en` and `one_line_zh`. They state names-only identity or re-uploads as fact, and the Chinese line drops the qualifiers the English line keeps.

`consent_or_ethics_statement` passes the bar but merges consent, waiver and ethics approval, so it can only be shown as the card's own sentence.

Data, sample, every verdict and the corrected values: `register-classifier-audit.json` (same folder).

## Sample

There are 90 rows, drawn deterministically from the 649 classified rows. They are stratified by `in_scope` × sensitive flag × modality group: 60 in-scope rows (the displayed population) and 30 out-of-scope rows. Each non-empty cell gets at least 2 rows. Within a cell the ids are sorted and every k-th id is taken, centred.

For each row, the full card (`raw/readme/`) and the full file list (`raw/details/`) were re-read before the classifier row, and each field was judged against the classifier's own field spec (ROW_SPEC). No network was used.

| Cell (in scope, sensitive flag, modality) | N | n |
|---|---:|---:|
| out, no flag, eeg | 13 | 3 |
| out, no flag, invasive | 2 | 2 |
| out, no flag, non_neural | 140 | 11 |
| out, no flag, other_neural_or_biosignal | 22 | 3 |
| out, no flag, unclear | 54 | 5 |
| out, flag, eeg | 1 | 1 |
| out, flag, non_neural | 13 | 3 |
| out, flag, other_neural_or_biosignal | 4 | 2 |
| in, no flag, eeg | 228 | 27 |
| in, no flag, invasive | 16 | 4 |
| in, no flag, other_neural_or_biosignal | 60 | 9 |
| in, no flag, unclear | 19 | 4 |
| in, flag, eeg | 65 | 9 |
| in, flag, invasive | 4 | 2 |
| in, flag, other_neural_or_biosignal | 6 | 3 |
| in, flag, unclear | 2 | 2 |

## Per-field accuracy

"In-scope 60" decides display, because those are the rows shown. The Wilson 95% interval is on that column. "Weighted 400" reweights the sample cells to the 400 in-scope rows.

| Field | All 90 | In-scope 60 | Wilson 95% | Out-of-scope 30 | Weighted 400 | Errors by kind | Verdict |
|---|---:|---:|---|---:|---:|---|---|
| `in_scope` | 85/90 | 55/60 (91.7%) | 81.9-96.4 | 30/30 | 94.3% | scope rule 2, unsupported 3 | fix before display |
| `modality` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | display |
| `paradigm` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | display |
| `content_kind` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | display |
| `stated.participants` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `stated.channels` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `stated.sampling_rate_hz` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `stated.device` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `declared_terms` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | display |
| `source_claim` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `derived_from` | 90/90 | 60/60 (100.0%) | 94.0-100.0 | 30/30 | 100.0% | - | "card states" only |
| `consent_or_ethics_statement` | 89/90 | 59/60 (98.3%) | 91.1-99.7 | 30/30 | 98.2% | keyword match 1 | "card states" only |
| `one_line_en` | 86/90 | 56/60 (93.3%) | 84.1-97.4 | 30/30 | 91.9% | overstatement 4 | fix before display |
| `one_line_zh` | 83/90 | 53/60 (88.3%) | 77.8-94.2 | 30/30 | 87.6% | overstatement 7 | fix before display |

The `stated.*` fields were judged as copies of the card. Sampled rows that carried a value, rather than "not stated", all match the card:
participants 27, channels 32, sampling rate 19 and device 18.

## Every wrong value, with the corrected value

| # | Row | Field | Kind | Classifier | Corrected |
|---:|---|---|---|---|---|
| 30 | `AnantaJ/Benchmark-from_Tsinghua_BCI_Lab` | `one_line_en` | overstatement | Tsinghua SSVEP Benchmark files (S1-S35 .mat.7z) re-uploaded without a card. | 35 per-subject .mat.7z files (S1-S35) plus Freq_Phase.mat and 64-channels.loc, laid out like the Tsinghua SSVEP Benchmark; no card. |
| 30 | `AnantaJ/Benchmark-from_Tsinghua_BCI_Lab` | `one_line_zh` | overstatement | 清华SSVEP Benchmark数据转存，无说明 | 35个被试.mat.7z文件，结构同清华SSVEP Benchmark，无说明 |
| 38 | `TKQXX/THINGS-EEG-MEG_CVPR2026` | `one_line_en` | overstatement | Preprocessed THINGS-EEG (10 subjects) and THINGS-MEG (4 subjects) tensors plus stimulus images. | No card; folders named THINGS-EEG (sub-01 to sub-10) and THINGS-MEG (sub-01 to sub-04) hold .pt tensors and stimulus images. |
| 38 | `TKQXX/THINGS-EEG-MEG_CVPR2026` | `one_line_zh` | overstatement | THINGS脑电与脑磁预处理张量及刺激图像 | 无说明；以THINGS-EEG/MEG命名的张量与刺激图像 |
| 46 | `heee565/SpanishBCBL` | `one_line_zh` | overstatement | 35人打字时MEG/EEG(SpanishBCBL副本) | 35名成人打字时的MEG/EEG（Brain2Qwerty），文件列表未核 |
| 51 | `perottofederico/things-eeg-captions-3` | `one_line_en` | overstatement | One THINGS-EEG subject split (66,160 rows) with images, captions and encoder hidden states. | One split named test_sub_08 (66,160 rows) of EEG, images, captions and encoder hidden states; repo named after THINGS-EEG; no card text. |
| 51 | `perottofederico/things-eeg-captions-3` | `one_line_zh` | overstatement | THINGS-EEG单被试分片，含图像描述隐状态 | 以THINGS-EEG命名的单被试分片，含图像、描述与隐状态 |
| 60 | `strawcoder33/bci-mamba-data` | `one_line_zh` | overstatement | T15皮层内语音解码数据及基线RNN，无说明 | 文件结构同Brain-to-Text '25（T15，45个会话）及基线RNN，无说明 |
| 64 | `emgbenchanon/muniverse-dynamic-v2` | `in_scope` | scope rule | True | False |
| 70 | `CharlieTY/EEG_dataset` | `in_scope` | unsupported | True | False |
| 71 | `as0305/BCI-Competition-IVa-dataset-2` | `in_scope` | unsupported | True | False |
| 71 | `as0305/BCI-Competition-IVa-dataset-2` | `one_line_zh` | overstatement | BCI竞赛IVa图像数据第2部分，无说明 | 以BCI竞赛IVa命名的仓库系列第2部分：5040行图像，无说明 |
| 73 | `opsecsystems/EEGWORLD` | `in_scope` | unsupported | True | False |
| 79 | `cagataydev/emotiv-ecot` | `consent_or_ethics_statement` | keyword match | present | absent |
| 80 | `graycatHCO3/eegmmidb_0to8_cross` | `one_line_en` | overstatement | Per-subject PyTorch tensors for 106 EEGMMIDB subjects ('0to8' labels); no card. | 106 per-subject PyTorch files (S001-S109, three numbers missing) in a repo named after EEGMMIDB; no card. |
| 80 | `graycatHCO3/eegmmidb_0to8_cross` | `one_line_zh` | overstatement | EEGMMIDB 106名受试者逐人PyTorch张量 | 以EEGMMIDB命名的106个逐被试PyTorch文件，无说明 |
| 85 | `azithromycin/AnasElkhabbaz_sensor_dataset` | `in_scope` | scope rule | True | False |

The JSON gives the reason for each verdict. It also lists 40 reviewer notes that do not change any value, such as defensible alternatives and inferences that should be labelled.

## Recommendation

**Display:** `modality`, `paradigm`, `content_kind`, `declared_terms`. Rows with no readable card get a marker, because these values then come from names and file lists. That is 177 of the 400 in-scope rows: 86 HTTP 404, 25 HTTP 401 gated, and 66 with front matter only or an empty card.

**Show only as "card states":**
- `stated.participants`, `stated.channels`, `stated.sampling_rate_hz`, `stated.device`. Strip parenthetical notes first; 13 SanderGi rows point to a first name.
- `source_claim`. All 364 quotes across the 649 rows are verbatim and none is over 25 words. Remove the OpenReview link and the two review-status notices first.
- `derived_from`, only where the basis is "stated in card" (123 in-scope rows), worded "card names X". The 161 rows with basis "name/file structure" are suspicions. Under B9 they become `matches_metadata_of` and stay off the page unless independently verified with a captured original-terms page (D3).
- `consent_or_ethics_statement`, shown as the card's own sentence and never as "participants consented". Capur/IESSEEG is "present" for an IRB approval with consent **waived**. 24 gated rows read "absent" although no card was read, so they should say "card not readable". Set cagataydev/emotiv-ecot to "absent". Re-read eZWALT/price-of-attention and neukym/kymata-soto.

**Fix before display:**
- `in_scope`, the D11 population filter. Do not print the 400 until three rules run:
  1. Signals that are only simulated go out, or into a group of their own. That is 7 rows.
  2. The EMG rule is applied the same way to every row. Of the 68 EMG-only rows, 61 are in and 7 are out, and one source (AnasElkhabbaz/sensor_dataset) is in for one conversion and out for two others.
  3. A row whose only evidence of brain signals is its repo name is "undetermined" and not counted. Check the 21 in-scope rows with modality "unclear": 3 of the 4 sampled were wrong, and the six as0305/BCI-Competition-IVa-dataset* rows are image tables with a `patient_id` column.
  The stratum-weighted estimate is that about 23 of the 400 change. The printed count must come from the re-check, not from this estimate.
- `one_line_en` / `one_line_zh`: rewrite with one rule. When `derived_from.basis` is not "stated in card", the line says only "named after X" or "file layout matches X" (以X命名 / 结构同X / 疑为X). The Chinese line must carry the same qualifier as the English line. A keyword screen flags 45 EN and 58 ZH in-scope lines (65 rows) for the rewrite. Copy statements backed by identical git blob ids or LFS sha256 against another HF repo are facts and can stay, worded "files identical to <repo>". No line breaks the length limits: 0 of 649 are over 16 words in EN or 30 characters in ZH.

## Systematic findings

- **S1. in_scope rules are applied unevenly.** Simulated signals: in scope for 7 rows (synthetic EEG tables, synthetic EEG pretraining data, simulated HD-sEMG) but out of scope for webxos/BCI-FPS, webxos/BCI-grid-movement-v1, THULab/bci_grid_movement_v1, Axym-Labs/axobench* and mackelab/STG_energy. EMG: the spec admits EMG "only when recorded with or used as a neural interface"; of the 68 rows whose only signal modality is EMG, 61 are in and 7 out, and one source (AnasElkhabbaz/sensor_dataset) is in for one conversion and out for two others. No-evidence rows: repo names alone put CharlieTY/EEG_dataset, opsecsystems/EEGWORLD and the as0305 image tables in scope.
- **S2. One-liners turn suspicions into facts, and ZH drops qualifiers.** Every one-liner error in the sample is the same kind: identity with a known dataset, or a re-upload, stated without a qualifier when the card does not state it. The project's own verifier standard (verified/graycatHCO3__BCICIV_2B.json) is "named after", not "mirror". The ZH line is shorter and loses qualifiers the EN line keeps (EN 4 errors, ZH 7).
- **S3. derived_from mixes declared sources and suspicions.** In the 400 in-scope rows the basis is "stated in card" 123, "name/file structure" 161 (confidence high 69, medium 46, low 46) and "none" 116. B9 requires matches_metadata_of for suspicion and derived_from only for declared sources, so the export must split the field by basis.
- **S4. consent_or_ethics_statement conflates consent, waiver and ethics approval.** Of the 22 in-scope "present" rows, 18 carry a clear consent or ethics sentence, Capur/IESSEEG carries an IRB approval with consent waived, and 3 are weak (cagataydev/emotiv-ecot recording veto, eZWALT/price-of-attention pointer to another file, neukym/kymata-soto mention of consent-form wording). No in-scope "absent" row has a missed consent or ethics sentence (keyword re-scan of all 378 non-present in-scope rows: 2 hits, both rules for future users, correctly "absent"). 24 gated rows are "absent" without the card having been read.
- **S5. Many in-scope rows have no card to read.** 177 of the 400 in-scope rows have no readable card body: 86 return HTTP 404, 25 return HTTP 401 (gated) and 66 hold only front matter or are empty. For these rows every stated.* field is "not stated" by construction and modality, paradigm and content_kind come from names and file lists.
- **S6. Cards were not pinned to a revision.** raw/readme/ was fetched from raw/main while raw/details/ records the revision sha. The audit judged the classifier against the same snapshot it read; B9 requires re-reading cards at each row's pinned revision_sha before wave 2.

## Display hazards found during the audit

- `brain-bzh/reve-dataset` (source_claim.link): openreview.net URL. Site rule: nothing referring to OpenReview.
- `synapse-ear-eeg/synapse` (source_claim): named_source and quote describe a release for an anonymous submission under double-blind review. Site rule against referring to a conference submission; check against D4 (rows tied to ICLR 2027 submissions wait until after the 16 December 2026 decisions).
- `velvet-pine-22/PULSE` (source_claim): named_source says "NeurIPS 2026 Evaluations & Datasets submission (anonymous)" and the quote is the anonymous-review notice.
- `gifoe/CRCICLR` (id): The repo id contains "ICLR" and the card names only a "CRCICLR HSC-TTA project". Check against D4 before listing.
- `ut-vision/EgoBrain-Mini` (source_claim, derived_from): Cites ICLR 2026 (a published paper). Allowed, but a plain "ICLR" scan in F3 will flag it; the scan should target "ICLR 2027".
- `SanderGi/lerobot-eeg-test-alex-* (13 rows)` (stated.participants): Value carries "(repo name contains the first name 'alex')". Strip the parenthetical before display.
- `Capur/IESSEEG` (consent_or_ethics_statement): "present" stands for IRB approval with consent and HIPAA authorisation waived. Never render it as participants consenting.

## Limits

- The sample is 60 in-scope rows. With 0 errors in 60, the Wilson lower bound is 94.0%, so "100%" fields are at least about 94% at 95% confidence.
- The out-of-scope calls were 30/30. Separately, all 17 out-of-scope rows that list a brain modality hold no signal data, which matches the spec.
- Judgments are against the same snapshot the classifier read. The cards came from `raw/main` and were not pinned to the revision sha, so B9 must re-read them at each row's `revision_sha`.
- No data file was opened. File contents are inferred from names, sizes, schemas and blob ids. Two copy relations were confirmed by blob ids in this audit: wang124/L-Mind, with all 12,012 blobs equal to Lance1573/L-Mind, and dhioewhd/things-eeg, with all 33,519 equal to Haitao999/things-eeg.
