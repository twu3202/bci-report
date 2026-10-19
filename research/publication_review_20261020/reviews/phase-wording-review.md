# Phase jitter and phase ramp: wording re-confirmation

Package R5 of the release frozen at 20261020 (plan §1.1 rows "Phase jitter" and "Phase ramp, six cells", §6 risk 2; owner default R1_R5). Reviewed 2026-10-19 by an independent reviewer in the publishing session.

**Read only.** Nothing in the two research folders, in the promotion worktree or under `site/` changed. Number checks ran from a scratch directory on the files in place. There was no network use, no git action and no contact with the producing sessions.

Paths are relative to the repository root. Folder aliases:

- `JIT/` = `research/decision_route3_phase_jitter_20261015/`
- `RAMP/` = `research/decision_route3_phaseaug_20261016/`
- `LOG` = `.claude/worktrees/blissful-wozniak-86a1ef/promotion/log.md` (the public thread record)

In this file, "the confidence figure" means the number the commenter gave as his confidence in his bet. Following the release rule, the figure itself is not written here. The commenter is not named.

## Verdict

**Confirmed, with seven required corrections, one more that applies only if check counts are printed, and six recommended ones (§4).**

1. **Dropping the confidence-figure fields loses no required caveat.** None of the dropped blocks carries caveat text, apart from the ramp `interpretation` string. That string holds four clauses. Three are already in the card 4 caption or the scope line. The fourth, "conditional bootstrap uncertainty", is not, and it has to move into the derived export and onto the page (correction M3).
2. **The bet is attributed correctly and stated once, on card 4.** The thread ties the bet to the phase-ramp run in three places: the commitment that answered it, the reply that reported it, and the commenter's own follow-up. Two changes are needed: the threshold must print as stated in the thread (M5), and the bet line must name the FiLM head (M4).
3. **Every number in the card 3 and card 4 leads and captions matches the audited sources at the site's formatters** (59 checks, 0 mismatches; §3). Faithfulness problems remain in wording:
   - Card 4's caption says "the primary contrast", but the ramp has six primary contrasts. The plan repeats this as "P1 marked primary" (M1, M6).
   - Card 4 omits a limit the ramp interpretation review requires: held-out and seen scores come from different tasks (M2).
   - The page and the file cannot pass the plan's digit scan for the confidence figure as written (§4.6 F3, §6 risk 2). The scan needs a token rule (M7).

This receipt covers wording and declared edits only. B4's audit still binds the bytes of the derived export.

## 0. Inputs (all hashes re-computed with `shasum -a 256`)

| File | SHA-256 | Role |
|---|---|---|
| `JIT/exports/phase-jitter-v1.json` | `7232ce0000738b25a3e7eb95a0b82a2999c22e55e4b6673ff822d80c31535ef3` | jitter export (card 3 source) |
| `JIT/exports/phase-jitter-aggregate.json` | `74eb6de8524588e5b9ac7854973b87bac31a9a977ea96cda6c00f9ca8eb59bdc` | canonical score, pinned by hash only |
| `JIT/protocol.json` | `8dbe7f458d14631bc111b6439bf55ce5deed6d11c1c3e0fb5ad4bbde729e1a71` | frozen protocol |
| `JIT/review/final-interpretation-review.json` | `ca2e5db29b5cc760f67869368248d5b1217e8ead964002fe82331892b51059fa` | interpretation review |
| `JIT/review/final-provenance-review.json` | `ad6350346bdeff29067b06113df853a70e02e82197888a8f0cbbdb92ea65f5c7` | provenance review |
| `JIT/state/release-status.json` | `776efd6aa26b6702c78986733ebaf292309d4e8c0548a3c8073e2298bf5d8a56` | release receipt |
| `JIT/Phase Jitter SSVEP Results Handoff.md` | `998b9e35078a5e716a64bc1ec8ca3af63c6a1d96331cbe704d85334bc91f4088` | handoff |
| `JIT/review/completed-run/canary-gate.json` | `019c026a4d779d76f731ba2946688aeeaa4b617c28718fea7224c606dbdc4128` | randomized-label gate: 40 of 40 fits, 4 cells, pass |
| `RAMP/review/final-trx/score/main.private.json` | `7498eb5cf79d2f807ab6e12584fdaa76c3542a703701c7fc9e0e31a1164bc8d2` | ramp score (card 4 source) |
| `RAMP/review/final-trx/audit/aggregate.json` | `41ff565b37247a8842c947e98769aefc058602d9bd51b2550015c0c963e12fb6` | numerical audit: pass, release_eligible |
| `RAMP/review/final-trx/audit/numerical-summary.json` | `1dc7a8f4210013e9902207045acfe073300c52c3c04ad636454fbfd0d5f57373` | numerical summary |
| `RAMP/protocol.json` | `d28a6e3cdf0928fa7f55c9dc19b335a4eb3e43180cb1f31903c6a0f41c916f6a` | frozen protocol |
| `RAMP/review/release-interpretation-review.json` | `af55b077127724fa9537e07c7f259ea8623c6d6322b654e0dd7d2cdc4efadeaa` | interpretation review |
| `RAMP/review/release-provenance-review.json` | `942ad85d8a4aca6dfd334081aebd02876b80e9e569a8ef1259754d05621e54f3` | provenance review |
| `RAMP/review/release-status.json` | `4044b7668d440cf84faffd25386603d6428ab1ab0f5b7c9cd3e27f22f93ce3ee` | release receipt |
| `RAMP/Phase Ramp Six-Cell Results Handoff.md` | `efae5870ee51a4cdb31b9e29e3f6b360f5b782e7bc04368fe2c8192ffdce44cb` | handoff |
| `RAMP/review/canary-gate.json` | `35c58ffe467dfd7b6d4138793bafa537283e70c1f3cd390f150bb9d272271198` | randomized-label gate: 120 of 120 fits, 10 cells, pass |
| `LOG` | `1d4389d03b0f2366ee34da10848814e50b54b6eb979311561971e9419e0bec39` | public thread record (replies 1–6) |
| `.claude/worktrees/blissful-wozniak-86a1ef/promotion/Phase-scramble augmentation test handoff.md` | `69370088ca1c6c2673af0c0b0e8fbd516407103e729184672f2ffb3f46b003de` | the ramp commission; `RAMP/protocol.json` pins it as `source_handoff` |
| `research/site_release_plan_20261019/Release Layout Plan v2.md` | `e4834e4baf97bd04fee8c6d4629f1a477858afb2eb994edc69510583fd716aac` | plan under review |
| `research/site_release_plan_20261019/handoff-readings.json` | `f231b1aac935f5fbe991a636191e13b2e1c8a5818bca9f57231fb64ca6c90c6a` | readings 2 (jitter), 3 (ramp), 10, 13 |
| `research/publication_review_20261020/owner-decisions.json` | `3661cb4d54f2daa8512e994865cab20a93c6a6d2ba0e9b31b81092b1bd9ff3b7` | D6, R1_R5 |

Every hash of a jitter or ramp file equals the value in the handoff readings and in that study's own receipts.

## 1. Check 1: what the declared edits drop, and where each caveat lives

### 1.1 The dropped fields

| Dropped item | Exact content | Caveat text in it? | Where the caveat lives after the drop |
|---|---|---|---|
| jitter `one_period_prediction` (export) | `reference` (the confidence figure as a fraction), `point_meets: false`, `above_reference: false`, `below_reference: true` | none: a misread reference and three flags | nothing to carry |
| jitter `release_governed_by` (export) | `"../state/release-status.json"` | none | release status goes into the manifest pins (B4) |
| jitter aggregate's B prediction-flag block | the same three flags | none | not served; the aggregate is pinned by hash only |
| jitter aggregate `interpretation` | "Fixed-split BETA follow-on; conditional bootstrap uncertainty; secondary intervals unadjusted; no unique phase-memorization diagnosis." | yes | not served. The same content survives in the export's `intervals` (`conditional_on`, `secondary_intervals`) and `caveats` (7 strings), which B2 keeps. |
| ramp `fifty_five_reference` (score) | flags for FS-REF and MATCH-REF: `point_meets: false`, `above_reference: false`, `below_reference: true` | none | nothing to carry |
| ramp `interpretation` (score) | "Fixed-split BETA recipe; conditional bootstrap uncertainty; phase ramp approximates a time shift; no phase-alone or sole-head diagnosis." | yes, four clauses | see §1.2 |

### 1.2 The ramp `interpretation` clauses

| Clause | Plan copy that carries it | Status |
|---|---|---|
| Fixed-split BETA recipe | Scope line for cards 1–6: "7 participant folds × 5 frequency rotations … These follow-ups reuse the cohort route 3 already studied." | carried |
| Conditional bootstrap uncertainty | Nowhere in card 4. The figure rules name only the bootstrap and its seed. The score file keeps `multiplicity` but has no other interval text. | **lost unless moved: M3** |
| The phase ramp approximates a time shift | Card 4 caption: "The ramp acts on already-windowed coefficients and approximates a time shift." | carried |
| No phase-alone or sole-head diagnosis | Card 4 caption: the feature-recipe sentence and the initialisation sentence | carried in copy; B2 should keep it as limitation keys so F3 can test against it |

### 1.3 Text in the frozen sources around the confidence figure

The confidence figure also appears in prose: both protocols, both interpretation reviews, both handoffs, the catalog reading (handoff reading 10) and `LOG`. In every one of these places, the only caveat next to the figure is one that already lives elsewhere:

- **Jitter interpretation review, `interpretation.one_period`.** It says the one-period arm's small excess over 12.5% is "acknowledged without a prespecified confirmatory chance test or equivalence claim". Card 3 keeps this by never calling either arm "at chance". Optional wording is in R4.
- **Jitter protocol, `statistics.fifty_five_percent`.** Its interval-reading rule (an interval crossing the reference is uncertainty) only concerns the dropped reference.
- **Ramp interpretation review, `fifty_five_reference.meaning`.** It says the reference is "not … a cell-selection gate". The general rule still covers this: all six cells and 13 contrasts appear, and no cell is selected by score (ramp review `required_limits` 4).
- **Ramp handoff.** The sentences "Both reference-query arms missed …" and "Neither reached …" carry no caveat beyond the bullets under "Limitations that must travel with the numbers". §4 covers those bullets.

Handoff reading 10 recommends presenting the figure "as a prespecified descriptive reference that both REF arms missed". The thread record overrides that recommendation, as plan §1.1 already says. No B or P package may lift it.

A token-aware scan (§4, M7) finds exactly two hits across both source files: the jitter `one_period_prediction` block and the ramp `fifty_five_reference` key. After the declared edits, neither file contains the figure.

**Result of check 1:** no required caveat is lost, provided M3 is applied.

## 2. Check 2: the bet

### 2.1 The thread record (`LOG`)

- **Reply 4 context.** The commenter proposed a random onset shift per training trial of up to one stimulus period. "his bet: unseen clears 39 (…), and seen drops if phase is coded per target."
- **Reply 4 commitment, as posted.** "we will run the shift as a phase ramp on the cached complex spectra, with the magnitude reference and the numeric code as queries, and report both halves: whether unseen clears 39, and whether seen drops."
- **Reply 5.** It reported the phase-ramp results: FS with the magnitude reference "8.7% → 30.6% … below 39.0%". It mentioned the jitter run only as "fell to about 13% on unseen".
- **Reply 6 context.** The commenter's own follow-up: "he lost the phase-ramp bet (30.6 < 39)".

The ramp protocol puts the commitment into a test: `source_evidence.interpretation` says it "is tested against the paired 39.002976% historical control". The commission's first primary reading, "Does unseen clear 39?", is FS-REF − L0-FS-REF (P1) and MATCH-REF − L0-FS-REF (P2).

### 2.2 Findings

- **Attribution is correct.** The bet belongs to the thread. Its own resolution names the phase-ramp run and the 30.6 figure, which is FS-REF held-out, 30.56%. The jitter protocol was built from the same comment, and its one-period arm has the role "commenter prescription". But the thread never resolved the bet against the jitter run. Putting the bet on card 3 as well would state it twice, and card 3 has no thread-sanctioned resolution to report.
- **Stated once.** In the plan the bet occurs only in the card 4 lead, the §1.1 rule and `thread_bet` under `studies.phase_ramp`. The short answer, the intro line, cards 1–3 and 5–8, §2.2 and the route 3 and Jev-style links do not carry it. The thread holds a second bet: in reply 6 the commenter bet on the cross-spectral scorer, with its own confidence figure. Card 8's addendum wording carries neither, which is correct, and it must stay that way.
- **Wording "held-out accuracy would clear 39%".** This matches "unseen clears 39": the page uses "held-out" for "unseen", and the threshold is a percentage. The card gives the bet without naming the commenter (D6) and without a second link, since the intro line links the thread once.
- **Problem 1: the head is named ambiguously.** "the magnitude-reference head reached 30.56%" can mean either the FiLM head (30.56%) or the matching head (12.93%). Both use the magnitude reference in this run. In the card 3 caption, "the magnitude-reference head (39.00%)" means a third model, L0-FS-REF on the plain spectrum. Consecutive cards would give one name three values (M4).
- **Problem 2: the threshold format.** At the plan's level format (pct2), `thread_bet.held8_threshold = 0.39` prints "39.00%". That adds precision the thread did not state, and it reads as the L0-FS-REF result 39.00% (M5).
- **Should-fix.** The commitment covered both queries. Giving the numeric-code figure (28.10%) beside 30.56% reports the bet the way the thread framed it, and it does not single out the highest cell (R3).

## 3. Check 3: every number in the card 3 and card 4 copy

Script: `phase_parity.mjs` in the session scratchpad, kept out of the repository. It loads the two source files and formats each value with `formatFig` from `site/src/data/entities.ts`: `pct2` = `(raw*100).toFixed(2)`, `pp2` = sign plus `Math.abs(raw*100).toFixed(2)`. **59 checks, 0 mismatches.**

| Card | Plan figure | Source field | Formatted |
|---|---|---|---|
| 3 | 526,465 parameters, trained from scratch | `model.parameters`, `model.trained_from_scratch` | 526,465; true |
| 3 | 0–125 ms arm 12.51% (11.93–13.13) | `arms[A].metrics.u8` | 12.51 (11.93, 13.13) |
| 3 | one-period arm 13.13% (12.61–13.68) | `arms[B].metrics.u8` | 13.13 (12.61, 13.68) |
| 3 | no delay 24.97% (22.60–27.44) | `arms[C].metrics.u8` | 24.97 (22.60, 27.44) |
| 3 | primary −12.46 (−14.84 to −10.25) | `contrasts.P1` (A − C, u8, "single primary") | −12.46 (−14.84, −10.25) |
| 3 | seen 49.24 → 15.70 and 15.28 | `arms[C/A/B].metrics.seen_ba` | 49.24, 15.70, 15.28 |
| 3 | magnitude head 39.00% | `arms[M].metrics.u8` | 39.00 |
| 3 | "the other five" are descriptive; table of 6 | `contrasts` S1–S5, role "descriptive secondary" | 5; 6 |
| 3 | S2 renders −25.87 | `contrasts.S2` = −0.25875 | −25.87 |
| 4 | 30.56% (27.81–33.22) | `levels["FS-REF/u8"]` | 30.56 (27.81, 33.22) |
| 4 | 8.45 below the plain spectrum, primary (−10.14 to −6.69) | `contrasts.P1` (FS-REF − L0-FS-REF, u8, primary) | −8.45 (−10.14, −6.69) |
| 4 | 21.88 above without the ramp, secondary (18.78 to 25.00) | `contrasts.S5` (FS-REF − L0c-FS-REF, u8, secondary) | +21.88 (+18.78, +25.00) |
| 4 | seen 47.29 → 15.03 | `levels["L0c-FS-REF/seen_ba"]`, `levels["FS-REF/seen_ba"]` | 47.29, 15.03 |
| 4 | matching head "ended at chance on both tasks" | MATCH-REF and MATCH-NUM `u8` intervals contain 0.125; MATCH-REF, MATCH-NUM and MATCH-ID `seen_ba` intervals contain 1/32 | 5 of 5 contain chance |
| 4 | CCA 80.90% | `levels["CCA/u8"]` | 80.90 |
| 4 | the bet is above the result | 0.39 against `levels["FS-REF/u8"]` | 0.3056 < 0.39 |
| 4 | Thirteen contrasts (6 P, 7 S) | `contrasts`, `role` | 13; 6 primary; 7 secondary |
| 3, 4 | bootstrap seed | every interval's `seed` | 20261007 |

The figures used in the corrections were checked the same way:

- L0c-FS-REF held-out 8.67 (7.85, 9.61)
- FS-NUM held-out 28.10 (25.48, 30.58)
- FS-REF m8 42.86 (39.29, 46.25)
- FS-REF cost −12.30 (−13.71, −10.95)
- S7 −67.97 (−72.07, −63.76), `noninferiority_to_CCA: false`
- No contrast has `equivalent_within_2pp: true`.
- Undefined metrics are exactly FS-ID, MATCH-ID, L0c-FS-ID and L0c-MATCH-ID (u8, u3, cost).

**Rounding note.** Each contrast is a paired difference of unrounded values. In 7 of the 19 jitter and ramp contrasts, the printed difference is 0.01 away from the difference of the printed levels:

- jitter S1 and S5;
- ramp P1, P4, P5, S3 and S5.

Two of these are in the card 4 lead: 39.00 − 30.56 = 8.44 while P1 prints 8.45, and 30.56 − 8.67 = 21.89 while S5 prints 21.88. No source value is wrong. R5 below adds one sentence about it.

## 4. Corrections

### 4.1 Required (M)

**M1. Card 4 caption: the ramp has six primary contrasts.** The plan's caption says "The primary contrast compares two feature recipes as well as the ramp". P1 to P6 are all primary (`RAMP/protocol.json` `analysis.contrasts`; the score's `role` fields). The feature-recipe confound applies to the four contrasts against the plain spectrum, P1, P2, S3 and S4. Replace the plan's first and last caption sentences ("The primary contrast compares …" and "Thirteen contrasts, unadjusted.") with the first and fourth sentences of the corrected caption in §5.

**M2. Card 4: held-out and seen are different tasks.** The card prints held-out 30.56% beside seen 15.03%. The ramp interpretation review's `required_limits` 2 makes this limit mandatory, and so does handoff reading 3, required caveat 1. Add the third sentence of the corrected caption in §5. It gives m8 for the same head: 42.86%.

**M3. Cards 3 and 4: name the intervals and state that they are conditional.** This is the clause the ramp `interpretation` drop would otherwise lose (§1.2). The jitter export keeps it in `intervals.conditional_on`, but the card 3 caption does not show it.

- In B2, give both study blocks `interval_method = {method: "hierarchical paired bootstrap", draws: 2000, seed: 20261007, level: 0.95, conditional_on: "fixed person folds and three training seeds; five fixed rotations averaged first"}`.
- On the page, each caption carries the interval sentence in §5.
- If P-SS1 prefers one definition in `#methods-and-limits` for cards 1–4, each caption may instead name the bootstrap and link to it. The words "conditional on the fixed person folds and three seeds" must then appear in that definition.

**M4. One name per model.**

- Card 3 caption: "The magnitude-reference head (39.00%)" becomes "The magnitude-reference head on the plain spectrum (39.00%)".
- Card 4: "the head" becomes "the FiLM head" in the result sentence and in the bet line.

**M5. Print the bet threshold as the thread stated it.** `thread_bet.held8_threshold` (0.39) renders as "39%" in EN and ZH, never as pct2 "39.00%". `formatFig` has no whole-percent case. P-SS3 can either add a local `pct0` (`(raw*100).toFixed(0)+'%'`), mirrored in the check module's formatter, or print it with the existing `int0` on `raw*100` plus a literal "%". F4 adds the rule `thread_bet.held8_threshold 0.39 → 39%`. F3 can then confirm the bet occurs once per locale by counting the standalone token "39%" (one per locale, distinct from "39.00%").

**M6. Plan text: the roles on card 4.**

- §1.1 "Phase ramp" row: "with P1 marked primary" becomes "with P1–P6 marked primary and S1–S7 secondary".
- §4.4 P-SS3 acceptance: "P1 primary" becomes "card 3: P1 the single primary; card 4: P1–P6 primary".
- B2 already says "P/S roles". Its test should assert six primaries for the ramp and one for the jitter.

**M7. Define the confidence-figure scan as a token rule.** As written in F3 (the figure's two digits must not occur on the SSVEP page or in its file), the scan fails on legitimate content:

- card 5 prints the channel-energy average as 55.21%;
- the full-precision values in the file contain that digit pair 12 times in the ramp score and 4 times in the jitter export, including FS-REF held-out 0.30556547…, the value the bet line cites.

A literal scan would push someone to change a correct figure. Use these rules, which pass on the plan's §2.1 copy and catch exactly the two dropped blocks in the sources:

- **page text, EN and ZH:** `/(?<![\d.])5{2}(?:\.0+)?(?![\d.])|(?<![\d.])0?\.5{2}(?![\d])|fifty[- ]five|五十五/i` must not match;
- **served JSON, after parsing:** no numeric value equal to `11 / 20` or `100 * 11 / 20`; no key matching `/fifty|05{2}|prediction/i`. Leave `confidence` out of the key pattern, because jitter `intervals.confidence` is the 0.95 interval level;
- **`thread_bet`:** it holds only `held8_threshold` and `source_url` (and optionally `contrasts: ["P1", "P2"]`, the protocol's test of the commitment). No confidence field, no commenter name or handle, and no comment anchor. The anchor in `JIT/protocol.json` came from a user-supplied comment and was never retrieved live. Use the plain post URL `https://huggingface.co/posts/Twu31/109502481720473`, as `LOG` does. The bet appears under `studies.phase_ramp` only.

Apply this in §1.1's rule line, §4.4 P-SS3, §4.6 F3 and §6 risk 2.

**Conditional M8. Randomized-label checks.** Wherever a card or `#methods-and-limits` prints these check counts, the limit goes beside them. Both protocols say it in `canary.interpretation`, and the jitter interpretation review checked that it was kept (`source_label_dependent_B_support_and_canary_limitation_retained`).

- **Card 3:** "All four randomized-label checks passed (40 fits); a training-only shortcut through the label-dependent delay remains possible."
- **Card 4:** "All ten randomized-label checks passed (120 fits); a training-only shortcut through the label-dependent delay remains possible."

If no counts are printed, nothing is added.

### 4.2 Recommended (R)

**R1. Card 3 title.** "Random delay on the phase-carrying query" reads as if the query were delayed. Delaying the query is a forbidden claim in both studies ("That queries … were augmented"). Change it to EN "A random delay with the phase-carrying query" and ZH "带相位查询下的随机延迟", which parallels card 4's "A random phase ramp with magnitude queries" / "幅度查询下的随机相位斜坡".

**R2. Card 3 lead and caption.**

- Say where the delay acts: on the window's spectrum. This matches card 4. Add "Queries and test windows were unchanged." (jitter reading, required caveat 7; jitter export caveat "Nominal evaluation inputs and all reference queries remain unchanged").
- Add the 0–125 ms half of the label caveat (jitter reading, required caveat 2; `JIT/protocol.json` arm A `interpretation`).

The text is in §5.

**R3. Card 4 lead.**

- Print the matched control, 8.67%, beside +21.88. This keeps it visibly apart from card 3's 24.97% control; merging the two studies' controls is a forbidden claim in reading 3.
- Give the numeric-code result in the bet line (§2.2).

**R4. Card 4 caption, two more limits from reading 3 and the ramp review.**

- The S7 sentence: S7 is the only declared CCA contrast, and CCA has one seed axis.
- "keeps magnitudes and the phase between channels".

Optional for card 3: "Both arms sit close to the 12.5% chance level; the one-period arm's interval lies just above it." This wording is allowed: it avoids "at chance" and "chance-equivalent".

**R5. Rounding sentence in `#methods-and-limits`.** EN: "Differences are paired and computed before rounding, so a printed difference can be 0.01 away from the difference of the printed levels." ZH: "差值为配对差，在舍入前计算，因此印出的差值可能与印出水平之差相差 0.01。"

**R6. Small exactness fixes.**

- "Seen accuracy" becomes "Seen balanced accuracy" on both cards. The endpoint strip calls the task "Seen 32-way balanced".
- Use one phrasing for BETA's phase coding on both cards: "BETA assigns each target a stimulus phase, 0.5π apart for neighbouring frequencies". This is checked against the BETA paper in `LOG` reply 4.

## 5. Card 3 and card 4 text with the corrections applied (EN)

Every figure is a data-fig from the fields in §3. The bet threshold uses the M5 format.

**Card 3 title:** "A random delay with the phase-carrying query" (ZH "带相位查询下的随机延迟").

**Card 3 lead:** "During training only, each window's complex spectrum got a random delay common to all channels, drawn either from 0–125 ms or from 0 to one period of the training label's frequency. The head was the complex-spectrum head with the phase-carrying reference query (526,465 parameters, trained from scratch); queries and test windows were unchanged. On held-out frequencies the 0–125 ms arm reached 12.51% (11.93–13.13) and the one-period arm 13.13% (12.61–13.68). The same head without the delay reached 24.97% (22.60–27.44). Primary change, 0–125 ms minus no delay: −12.46 points (−14.84 to −10.25). Seen balanced accuracy fell from 49.24% to 15.70% and 15.28%."

**Card 3 caption, once:**

1. "Only the 0–125 ms minus no-delay contrast is primary; the other five are descriptive."
2. "Intervals are 95%, from 2,000 hierarchical paired bootstrap draws over people and training seeds (seed 20261007), conditional on the fixed person folds and three seeds; no multiplicity correction."
3. "The delay multiplies already-windowed coefficients by one phase ramp, which approximates an onset shift."
4. "The one-period range is drawn from the training label's frequency; the 0–125 ms range ignores the label and equals one period at 8 Hz, so its phase spread differs by target."
5. "BETA assigns each target a stimulus phase, 0.5π apart for neighbouring frequencies, so the delay also removes information tied to the label."
6. "The magnitude-reference head on the plain spectrum (39.00%) differs in features, query and size."

Add the M8 card 3 line if counts print.

**Card 4 lead:** "During training only, each window's complex spectrum got a random delay of up to one stimulus period, applied as one phase ramp across all channels. Queries and test windows were unchanged. With the magnitude reference as the query, the FiLM head reached 30.56% on held-out frequencies (27.81–33.22). That is 8.45 points below the same head and query on the plain spectrum (primary; −10.14 to −6.69) and 21.88 points above the same head and query on the complex spectrum without the ramp, which reached 8.67% (secondary; 18.78 to 25.00). Seen balanced accuracy fell from 47.29% to 15.03%. The matching head ended at chance on both tasks. CCA reached 80.90% on the same held-out task. The bet in the thread was that held-out accuracy would clear 39%; the FiLM head reached 30.56% with the magnitude reference and 28.10% with the numeric code."

**Card 4 caption, once:**

1. "Six contrasts are primary and seven secondary; 95% intervals come from 2,000 hierarchical paired bootstrap draws over people and training seeds (seed 20261007), conditional on the fixed person folds and three seeds, with no multiplicity correction."
2. "CCA has no training and one seed axis; S7 is its only contrast (−67.97 points), outside the 2-point non-inferiority margin."
3. "Held-out scores choose among 8 candidates and seen scores among 32, so the two are different tasks; on the same eight frequencies in the rotations where they were seen, the FiLM head with the magnitude reference reached 42.86% (m8)."
4. "The contrasts against the plain spectrum (P1, P2, S3, S4) compare two feature recipes as well as the ramp: the complex and plain spectra differ in normalisation, size and capacity."
5. "The delay range is drawn from each window's training label."
6. "The FiLM and matching heads start from different initial scores, so head comparisons are not initialisation-matched."
7. "BETA assigns each target a stimulus phase, so phase carries real label information."
8. "The ramp acts on already-windowed coefficients, keeps magnitudes and the phase between channels, and approximates a time shift."

Add the M8 card 4 line if counts print. The `<details>` table keeps four or more columns: contrast · role · estimate · interval. ID held-out, u3 and cost print as an em dash.

**ZH bet line** (figure multiset 39, 30.56, 28.10, the same as the EN line): "讨论串中的赌注是留出频率准确率会超过 39%；FiLM 分类头以幅度参考谱作查询达到 30.56%，以数值编码作查询为 28.10%。" F3 still reviews all ZH copy.

**Changes from the plan's own text, card by card:**

| Card | Change | Fixes |
|---|---|---|
| 3 | title preposition | R1 |
| 3 | the delay acts on the spectrum; "queries and test windows were unchanged" | R2 |
| 3 | "balanced" | R6 |
| 3 | interval sentence | M3 |
| 3 | 0–125 ms clause | R2 |
| 3 | phase phrasing | R6 |
| 3 | "on the plain spectrum" | M4 |
| 4 | "FiLM head" | M4 |
| 4 | "same head and query"; 8.67% | R3 |
| 4 | "balanced" | R6 |
| 4 | bet line: head named, 28.10% | M4, R3 |
| 4 | caption sentence 1 | M1, M3 |
| 4 | caption sentence 2 | R4 |
| 4 | caption sentence 3 | M2 |
| 4 | caption sentence 4 | M1 |
| 4 | caption sentence 8 | R4 |

Everything else is the plan's wording.

## 6. Limits of this review

- **The original receipts.** Both interpretation reviews are bound to their original handoffs and exports, and the jitter review approved the misread prediction flags. This receipt replaces them on the confidence figure and the bet only. Their other checks stand unchanged, and so do their forbidden-claim lists, which F3 applies.
- **The derived export.** B4's audit binds the bytes of `new-ssvep-frequencies-update.json`. B2's test should assert the following:
  - the M7 key and value rules;
  - `thread_bet` only under `phase_ramp`;
  - the M3 `interval_method` in both blocks;
  - the jitter block keeps `caveats` (7 strings) and `intervals`; the ramp block keeps `multiplicity` and `undefined_metrics`;
  - six ramp cells, the nine comparators and 13 contrasts, with roles;
  - S2 raw −0.25875.
- **Out of scope.** The ZH copy beyond the ZH lines given here, cards 1, 2 and 5–8, and the short answer.
