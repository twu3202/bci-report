# CCA adapter: handoff binding review

Package R1 of the release frozen at 20261020 (plan §1.1 row "CCA adapter", §6 risk 5). Reviewed 2026-10-19 by an independent reviewer in the publishing session.

**Read only.** Nothing in `research/decision_route3_cca_adapter_20261015/`, in any other research folder or under `site/` changed. Reconstructions ran in a scratch directory on byte copies of the export and the two reviews. The private run host was not contacted, and there was no network use, no git action and no contact with the producing session.

All paths below are relative to the repository root. The adapter folder is called `ADAPTER/`.

## Verdict

**Safe, with five required copy fixes (§3).** The site can write its adapter copy from three sources:

- the export `ADAPTER/exports/CCA Adapter Aggregate Results.json` (`6f68114e…`);
- the two release reviews: numerical `e880280e…` and interpretation `4e1a3817…`;
- the frozen protocol `22826d2c…`, for method facts the export does not carry.

The handoff hash mismatch is cosmetic:

- The bound text `61d424e9…` and the current file `f4040010…` differ by **one inserted space** in a table header. No word, figure or claim differs.
- The bound text is itself exactly the reviewed draft `e77de0be…` plus the two finalization edits that the interpretation review permits.

Request R1 (re-binding by the producing session) is therefore not needed for content. Under owner default R1_R5, nobody asks that session to change its state files.

## 1. What changed between the bound text and the current handoff

### 1.1 The four versions

The producing Codex thread is `01a08512…`, a long-running main thread. Its local session log records how the handoff was written. All times are 2026-10-15 UTC.

| Version | SHA-256 | When | Made by (log record) | Bound or approved by |
|---|---|---|---|---|
| Draft | `4c605ae2…` | 05:40:45 | Python script that writes the text and fills every table from the export (record 53934) | none |
| Reviewed draft | `e77de0be…` | 05:42:17 | Two wording replacements (record 53965), described below | `review/release-interpretation-review.json` → `handoff_review.reviewed_draft_sha256`, reviewed at 05:43:36 |
| Bound | `61d424e9…` | 05:44:51 | Finalization script (record 54011) | `state/release-status.json`, `state/workflow-current.json`, `state/latest-monitor-check.json`, `state/latest-trx-snapshot.json`, `state/monitor-checks.jsonl`; byte copy placed in the private run host's review folder (logged hash `61d424e9…`, record 54025) |
| On disk | `f4040010…` | file mtime 06:07:11 | not logged (§1.3) | nothing |

Record 53965 made these two wording replacements:

- "preregistered" became "prespecified".
- The RAW-versus-CROP sentence now says the two recipes "differ in the analytic baseline term … learned parameters are fitted separately".

### 1.2 The diffs

**`e77de0be…` → `61d424e9…`.** These are exactly the "finalization changes permitted" by the interpretation review: "Replace pending top status and append approved release evidence/hashes without changing reviewed scientific claims or values".

- Line 3: the status changes from "independent release review pending…" to "independently audited; eligible for aggregate handoff…".
- Line 93: "Final release audit references will be recorded below…" is replaced by three paragraphs:
  - the numerical review path and SHA-256, with its rehash counts;
  - the interpretation review path and SHA-256;
  - the immutable-aggregate note, reworded to "the separate release-status receipt records subsequent approval and binds the final handoff hash".
- No figure, caveat or claim changes.

**`61d424e9…` → `f4040010…`.** There is one change: a single `0x20` byte inserted at offset 1342.

- File size goes from 12,062 to 12,063 bytes.
- The change is on line 15, the header of the results table: `| Arm | Held-frequency…` became `| Arm |  Held-frequency…`.
- Markdown renders both the same.

### 1.3 Who made the 06:07:11 edit

It is not recorded.

- The producing thread was idle from 05:51:49 to 06:10:44.
- No Codex session file changed since 2026-10-15 has any record, of any type, between 06:00 and 06:09.
- No Claude Code session for this repository has a record between 05:00 and 06:59 on that day.

The most likely cause is a manual or editor save. The author does not matter, because the content is unchanged.

### 1.4 How this was established

1. The three logged scripts (records 53934, 53965 and 54011) were replayed in a scratch directory. They ran against byte copies of:
   - the export `6f68114e…`;
   - `release-numerical-audit.json` `e880280e…`;
   - `release-interpretation-review.json` `4e1a3817…`;
   - `execution-freeze.json` `29bdbe5a…`.
2. The outputs hashed to `4c605ae2…`, `e77de0be…` and `61d424e9…` exactly.
3. Inserting one space at offset 1342 of the rebuilt bound text gives `f4040010…`, byte-identical to the file on disk.
4. No other copy exists in the repository. The folder is untracked and has no git history, and `.claude/worktrees/` holds no copy. The private run host's copy was not read, because this package has no network.

### 1.5 What the release manifest should record

**Pin by hash:**

| File | SHA-256 |
|---|---|
| Export | `6f68114e4d431beb4903f68e3e2d4549da825d8f94d2ff3a776e368a7b3dca2b` |
| Numerical review | `e880280e330f03a280281936e01a52371d4ca3e4c383e4a527a28b106fd12e5c` |
| Interpretation review | `4e1a38171be118d0c4d1b0f145c4b24578b18af349cccfa265c4aec335f9d4ac` |
| Protocol | `22826d2ceae1a46968fffabf56951d84abbbce3f75d8a4962f3ad385228194ca` |
| Execution freeze | `29bdbe5af3601385e8e3ef47d72985132278be269939d63a01f4b9708e8fa3b1` |
| `state/release-status.json` | `9f4929bbda746079ad1bfc8625f9d0c2eaebd099b505f33a2eaf0663821680bd` |

**Record the handoff as context only, never as a copy source:**

- bound `61d424e9…`;
- on-disk `f4040010…`, which differs from the bound text by one whitespace byte (this review).

## 2. The export carries every figure the site prints for this study

### 2.1 Bindings

| File | Expected | On disk | Match |
|---|---|---|---|
| Export | `6f68114e…` (both reviews, release status, numerical audit `checks.artifact_integrity.aggregate_sha256`) | `6f68114e…` | yes |
| Numerical review | `e880280e…` | `e880280e…` | yes |
| Interpretation review | `4e1a3817…` | `4e1a3817…` | yes |
| Protocol | `22826d2c…` (interpretation review evidence; numerical audit frozen pins) | `22826d2c…` | yes |
| Execution freeze | `29bdbe5a…` | `29bdbe5a…` | yes |

### 2.2 Agreement checks

- **Export against the numerical audit.** All 138 numeric leaves of `aggregate_findings` match the export. The largest difference is 1.1e-16, against the frozen tolerance of 1e-12. The export adds only `status`, `seed_aggregation`, `independent_audits` and `privacy`.
- **Internal consistency of the export:**
  - every contrast mean equals the difference of its two arm means;
  - the five transition outcomes sum to 1 for both endpoints;
  - `changed` equals wrong→right plus right→wrong plus wrong→different wrong;
  - wrong→right minus right→wrong equals the accuracy gain;
  - protected flips are 0.
- **Across exports.** CCA-RAW, and CCA-CROP (here) against SUBSPACE-CROP (diagnostics export `fae60f74…`), are **bit-identical** for both endpoints, means and intervals. So 80.90 (76.80–85.13) and 73.20 (68.62–78.13) are one set of scores in both files. Card 5 still reads them from the diagnostics export and card 6 from this one, as F4 requires.
- **Rendering.** All values below were rendered with the site's own formatter rules (`(raw*100).toFixed(2)` in node), not with Python.
- **The current handoff.** Every decimal figure in it equals a rendered export value, with five exceptions, none of them site figures: 0.200001 (the raw margin), 12.5 and 3.125 (chance), 15.4 (run minutes, not site material) and 41.46 (the site's existing NUM u8 field).

### 2.3 Figures the plan's adapter copy prints (short answer and card 6)

| Plan statement | Export field | Raw | Prints | Match |
|---|---|---|---|---|
| 86.15% held-out | `arms.RAW-RESIDUAL.held8_accuracy.mean` | 0.8614583333333333 | 86.15% | yes |
| (82.84–89.35) | `…held8_accuracy.ci95` | 0.8284122…, 0.8935438… | 82.84–89.35 | yes |
| 80.90% for CCA alone | `arms.CCA-RAW.held8_accuracy.mean` | 0.809017857142857 | 80.90% | yes |
| +5.24 points | `contrasts[4]` (RAW-RESIDUAL − CCA-RAW) `.metrics.held8_accuracy.mean` | 0.05244047619047618 | +5.24 | yes |
| 3.91 to 6.62 | `contrasts[4].metrics.held8_accuracy.ci95` | 0.0390773…, 0.0661614… | 3.91 to 6.62 | yes |
| 73.19% seen | `arms.RAW-RESIDUAL.seen32_balanced_accuracy.mean` | 0.7318675595238096 | 73.19% | yes |
| 65.46% seen | `arms.CCA-RAW.seen32_balanced_accuracy.mean` | 0.6545982142857143 | 65.46% | yes |
| +7.73, 6.10 to 9.46 | `contrasts[4].metrics.seen32_balanced_accuracy` | 0.0772693…; 0.0610319…, 0.0945762… | +7.73; 6.10 to 9.46 | yes |
| within 0.2 | `residual_diagnostics.RAW-RESIDUAL.held8_accuracy.protected_margin` | 0.200001 | 0.2 | yes |
| 7.39% wrong to right | `residual_diagnostics.RAW-RESIDUAL.held8_accuracy.wrong_to_correct` | 0.07386904761904763 | 7.39% | yes |
| 2.14% right to wrong | `…held8_accuracy.correct_to_wrong` | 0.02142857142857143 | 2.14% | yes |
| 17.51 points (15.46 to 19.70) | `contrasts[0]` (ADAPT-FS − ENERGY-FS) `.metrics.held8_accuracy` | 0.1750595…; 0.1545818…, 0.1969962… | +17.51; 15.46 to 19.70 | yes |
| Six contrasts | `len(contrasts)` | 6 | Six | yes |
| 70 people; person bootstrap | `n_people`, `unit`, `resamples` | 70, "person", 2000 | 70; person; 2,000 | yes |
| Adapted head against CCA alone has no interval | no `contrasts[]` entry pairs ADAPT-FS with CCA-RAW | (absent) | "not a planned contrast and has no interval" | yes |

### 2.4 Full tables, if B3 or P-SS4 renders the six arms and six contrasts

| Arm (export code) | Held-out 8-way, % (interval) | Seen 32-way balanced, % (interval) |
|---|---|---|
| ENERGY-FS | 63.05% (58.97–67.50) | 43.34% (39.09–47.83) |
| ADAPT-FS | 80.56% (76.98–84.13) | 64.06% (59.56–68.85) |
| CROP-RESIDUAL | 79.24% (75.24–83.37) | 63.35% (58.39–68.72) |
| RAW-RESIDUAL | 86.15% (82.84–89.35) | 73.19% (68.48–77.99) |
| CCA-CROP | 73.20% (68.62–78.13) | 55.67% (50.20–61.78) |
| CCA-RAW | 80.90% (76.80–85.13) | 65.46% (59.94–71.40) |

| Contrast (`contrasts[i]`) | Held-out 8-way, pp (interval) | Seen 32-way, pp (interval) |
|---|---|---|
| [0] ADAPT-FS − ENERGY-FS | +17.51 (+15.46 to +19.70) | +20.72 (+18.54 to +23.01) |
| [1] ADAPT-FS − CCA-CROP | +7.36 (+5.33 to +9.32) | +8.38 (+5.91 to +10.82) |
| [2] CROP-RESIDUAL − ADAPT-FS | −1.32 (−2.46 to −0.23) | −0.71 (−1.95 to +0.54) |
| [3] CROP-RESIDUAL − CCA-CROP | +6.04 (+4.90 to +7.17) | +7.67 (+6.26 to +9.13) |
| [4] RAW-RESIDUAL − CCA-RAW | +5.24 (+3.91 to +6.62) | +7.73 (+6.10 to +9.46) |
| [5] RAW-RESIDUAL − CROP-RESIDUAL | +6.91 (+5.60 to +8.16) | +9.84 (+8.60 to +11.04) |

| RAW-RESIDUAL against CCA-RAW (`residual_diagnostics.RAW-RESIDUAL`) | Held-out 8-way | Seen 32-way |
|---|---|---|
| wrong → right (`wrong_to_correct`) | 7.39% | 10.66% |
| right → wrong (`correct_to_wrong`) | 2.14% | 2.93% |
| wrong → different wrong (`changed_wrong_to_wrong`) | 2.59% | 7.63% |
| unchanged right (`unchanged_correct`) | 78.76% | 62.53% |
| unchanged wrong (`unchanged_incorrect`) | 9.12% | 16.25% |
| changed (`changed`) | 12.12% | 21.22% |
| protected flips / protected prediction instances | 0 / 11,403 | 0 / 6,012 |

### 2.5 Figures and facts the site needs that the export does not carry

Take these from the pinned sources named here, never from the handoff.

| Fact | Source |
|---|---|
| Chance 12.5% (8-way) and 3.125% (32-way) | Design (1/8, 1/32); `protocol.json` `metrics.primary` with `split.rotations` (8 held) and `split.source_queries_per_fit` (32) |
| 7 person folds × 5 frequency rotations, 8 held and 32 seen, 3 training seeds | `protocol.json` `split.folds`, `split.rotations`, `split.source_queries_per_fit`, `split.seeds` (the export only implies 3 seeds through its three `per_seed_descriptive` entries) |
| Bootstrap seed 20261015 | Numerical review `checks.independent_numerical_recomputation.bootstrap_seed`; `protocol.json` `metrics.bootstrap` |
| Intervals are descriptive and unadjusted for the six contrasts | Numerical review `…uncertainty`; interpretation review `required_boundaries`; `protocol.json` `metrics.multiplicity` |
| Why 0.2 holds for every pair of candidates | `protocol.json` `model.protection`: the pairwise bounded residual difference is at most 4 logit units, which is 0.2 in correlation units |
| Transitions use all held-out decisions as the denominator | `protocol.json` `metrics.residual_diagnostics` ("denominator all task trials"); interpretation review keys `all_instance_*` |
| Parameter counts (215,681; 215,682 for residual arms), if ever printed | `protocol.json` `model.adapter` |
| 11,200 windows (cohort scope line, shared with cards 1–5) | The cohort block of the SSVEP export; consistent with `protocol.json` `audit.feature_rows` (last index 11199) |
| Release status | `state/release-status.json` (`audited_complete_aggregate_handoff_ready`). Never the export's own `"status": "release_review_pending"` |

Card 7's "105 unchanged BETA models" agrees with `protocol.json` `split.fits_per_arm` = 105. The Wearable-102 figures themselves belong to the external export and were not checked here.

## 3. Findings for the copy and export packages (B3, B4, P-SS4, F3, F4)

### Required

1. **Rounded levels do not subtract to the printed gain.** Each figure is correct from its own field, but a reader who subtracts gets a different number.

   | Shown subtraction | Result | Printed contrast | Exact value |
   |---|---|---|---|
   | 86.15 − 80.90 | 5.25 | +5.24 | 5.2440 |
   | 7.39 − 2.14 | 5.25 | +5.24 | 5.2440 |
   | 64.06 − 55.67 (detail table, ADAPT-FS − CCA-CROP, seen) | 8.39 | +8.38 | 8.3839 |
   | 63.35 − 55.67 (detail table, CROP-RESIDUAL − CCA-CROP, seen) | 7.68 | +7.67 | 7.6719 |

   - Print each figure from its own field.
   - Write no sentence that presents the gain as the difference of the printed levels, or as "fixes minus breaks".
   - F4 must not recompute these as level differences.
   - The plan's card 6 lead prints both transitions with no "net" sentence, which is acceptable.

2. **Card 6, "Giving a learned head CCA's canonical correlations…".**
   - The six canonical correlations are computed on the **cropped complex spectrum**: `protocol.json` `features.z`, and the handoff's architecture paragraph, "computed from the frozen cropped complex representation".
   - The interpretation review calls them "joint canonical-spectrum features".
   - On this page's name key, "CCA" means CCA-RAW, so the sentence as planned attributes them to the wrong scorer.
   - Suggested wording: "Giving the head six canonical correlations from the cropped-spectrum match added 17.51 points over the energy head (15.46 to 19.70); that gain bundles several matching operations."
   - ZH: "给分类头加入裁剪谱匹配的六个典型相关系数，比能量头高 17.51 个百分点（15.46 至 19.70）；这一增益捆绑了多项匹配运算。"

3. **Short answer, "The highest held-out score on BETA came from…".**
   - The interpretation review bars any universal model ranking, and the readings bar any state-of-the-art claim.
   - Filter-bank CCA and supervised spatial templates were not compared.
   - §4.7 bars ranking words.
   - Suggested EN: "On BETA's held-out frequencies, temporal CCA with a small learned correction reached 86.15% against 80.90% for CCA alone, choosing among 8 frequencies (+5.24 points, 3.91 to 6.62; 70 people)."
   - Suggested ZH: "在 BETA 的留出频率上，时域 CCA 加一个小的学习修正在 8 选 1 中达到 86.15%，CCA 单独为 80.90%（+5.24 个百分点，3.91 至 6.62；70 人）。"
   - The Wearable-102 sentence and the last sentence are outside this review.

4. **Export fields that do not cross into the derived SSVEP export.**
   - `status` ("release_review_pending"; superseded by `state/release-status.json`).
   - `indices_sha256` (a hash of private bootstrap indices).
   - `privacy`.
   - `protected_trials`, unless it is labelled "prediction instances across 3 seeds and 5 rotations". These counts are not trials or people.

5. **`interval_method.seed` = 20261015 is read from the numerical review** (or the protocol), because the export does not carry it. `method` = "person bootstrap" and the 2,000 resamples come from the export's `unit` and `resamples`.

### Should

1. **"…only candidates whose CCA scores lie within 0.2 of each other."**
   - Prefer "CCA correlations". The page uses "score" for accuracy elsewhere.
   - The statement is supported for every pair of candidates by `protocol.json` `model.protection`.
   - Never pair it with "cannot hurt" or "never worse": 2.14% of held-out decisions went from right to wrong.

2. **Card 6 caption, "The candidate frequencies still supply CCA's sine and cosine references."** The reviewed boundary is "CCA-derived features and supplied candidate frequencies are explicit analytic inputs". At inference the candidate frequency also supplies the numeric frequency code (`protocol.json` `features.q`). Add "and the numeric frequency code".

3. **One exact rounding tie.** `per_seed_descriptive.ENERGY-FS[1].held8_accuracy` = 0.63125 prints 63.13 with the site's JS formatter and 63.12 with Python. The plan prints no per-seed value, so nothing renders it now. If a per-seed row is ever added, B4's audit must compare against the JS rendering.

4. **The RAW-RESIDUAL per-seed values** (86.18, 86.23, 86.03) may appear only as "three fixed seeds, averaged". Never as a best seed or an ensemble.

5. **F3's "55" scan needs a scoped pattern.** This export's CCA-CROP seen 32-way figure renders as 55.67%, and card 5's channel-energy average as 55.21%. Both are legitimate. The scan should match a bare 55 used as a percentage or threshold (for example `55%`, `0.55`, `55 percent`, `五成五`), not every string that contains "55".

## 4. Statements that must come only from the export

Every item below is printed from the field named, in `6f68114e…`, at the site's format. None comes from the handoff text, the HF thread or the readings' prose.

1. RAW-RESIDUAL held-out 8-way accuracy and its interval: 86.15% (82.84–89.35).
2. CCA alone (CCA-RAW), held-out 8-way: 80.90%. Its interval, if card 6 shows it, is 76.80–85.13, bit-identical to the diagnostics export that card 5 reads.
3. The held-out paired gain and interval: +5.24 (3.91 to 6.62), from `contrasts[4]`, never from the difference of two printed levels.
4. Seen 32-way balanced accuracy for both arms and the paired gain: 73.19%, 65.46%, +7.73 (6.10 to 9.46).
5. The bound printed as "0.2", from `protected_margin` 0.200001.
6. The transition shares of all held-out decisions: 7.39% wrong to right and 2.14% right to wrong, plus the other three outcomes and "changed" if a table shows them. Protected flips: 0.
7. ADAPT-FS minus ENERGY-FS: +17.51 (15.46 to 19.70).
8. The number of contrasts (six) and the fact that ADAPT-FS against CCA-RAW has no interval, read from what `contrasts[]` contains and lacks. No interval for that pair is ever computed or printed.
9. The people count (70), the bootstrap unit (person) and the resample count (2,000).
10. Any row of the six-arm or six-contrast detail tables in §2.4, including CCA-CROP 73.20% (68.62–78.13) under its site name "cropped-spectrum match (no training)".
11. The headline figure is 86.15. The HF reply's 86.2 never appears on the site. The F5 promotion note may say that 86.2 is 86.15 rounded twice.

**Never taken from the handoff:**

- private paths, host names, launch and completion times, and run minutes;
- the "Suggested public wording" paragraph, which is in "X, not Y" form;
- the 41.46% to 86.15% progression, which the reviews forbid as a single-factor gain.

## 5. Not done here

- **The private run host's copy of the bound handoff was not read.** This package has no network. The local replay already reproduces its logged hash.
- **The author of the one-byte edit at 06:07:11 was not identified** (§1.3).
- **The producing session's folder and state files were left unchanged**, and that session was not asked to re-bind (owner default R1_R5).
- **The Wearable-102, diagnostics and other follow-up figures were not checked**, except the two CCA values shared with the diagnostics export.
