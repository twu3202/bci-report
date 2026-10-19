# Site step evidence for the open register (package A5)

Machine-readable census: `site-step-evidence.json` in this folder (47 sources the site lists, plus BI2013a as an adjacent MOABB row). Every item on the five-step ladder is pass, gap or not-applicable, with the file and field it rests on; the builder resolved each selector against the file hashed in `inputs[]`.

**Rule used.** A row's step is the furthest step whose anchor item passes (plan §2.6): 1 host record · 2 files opened · 3 original terms · 4 fixed-protocol baseline run here · 5 a core-matrix protocol page. Gaps are the items missing at or below that step. "Next" lists what is missing at the step above. Where a row has a published result or hold that ships with this release, the JSON gives its state at freeze; the table below shows the state on file now.

| Source | Register status at freeze | Step now | Gaps at or below the step (by step) | Next step needs |
|---|---|---|---|---|
| **The seven core-matrix datasets (fromMvp in entities.ts)** | | | | |
| ds003810 | published | 5 | 4: share above chance | — |
| EEGMAT | published | 5 | 4: share above chance | — |
| BETA | published | 5 | 4: share above chance | — |
| ds006593 | published | 5 | 4: share above chance | — |
| TMNRED / ds005383 | published | 5 | 4: share above chance | — |
| EESM19 scalp subset | published | 5 | 4: share above chance | — |
| ds005342 | published | 5 | — | — |
| **The other 23 dataset pages (entities.ts datasets)** | | | | |
| Wearable SSVEP BCI dataset (dry and wet electrodes) | published | 4 | 3: pinned version; 4: chance level, share above chance | protocol page |
| Mobile BCI dataset (SSVEP and ERP paradigms) | published | 4 | 4: chance level, share above chance | protocol page |
| EESM23 · Ear-EEG Sleep Monitoring 2023 | published | 4 | 4: share above chance | protocol page |
| EEG Alpha Waves dataset | published | 4 | 3: ethics approval; 4: share above chance | protocol page |
| Phantom EEG with motion, muscle and eye artifacts | published | 4 | — | protocol page |
| OpenNeuro ds004584 · Parkinson's disease, rest eyes open | published | 4 | 4: share above chance | protocol page |
| Cattan PC/VR P300 dataset | published | 4 | 4: share above chance | protocol page |
| Multimodal gait dataset · treadmill walking | published | 4 | 4: share above chance | protocol page |
| YSU asynchronous SSVEP-BCI dataset | published | 4 | 4: chance level, share above chance | protocol page |
| LTRSVP · EEG Signals from an RSVP Task | published | 4 | 4: share above chance | protocol page |
| Dreem Open Datasets (DOD-H and DOD-O) | published | 4 | 3: consent statement (DOD-H); ethics approval (DOD-O); 4: chance level, share above chance | protocol page |
| OpenBMI motor imagery (Lee et al. 2019) | published | 4 | 4: share above chance | protocol page |
| BOAS · Bitbrain Open Access Sleep dataset | published | 4 | 4: share above chance | protocol page |
| WBCIC-SHU motor imagery dataset | published | 4 | 4: share above chance | protocol page |
| Longitudinal ERP dataset (RSVP) | published | 4 | 4: chance level, share above chance | protocol page |
| Forenzo & He continuous-tracking EEG-BCI dataset | published | 4 | — | protocol page |
| Orthosis error-detection dataset (Kueper et al. 2024) | published | 4 | 4: share above chance | protocol page |
| BINGO cross-linguistic inner-speech dataset | published | 4 | 3: ethics approval; consent statement for this dataset, pinned version; 4: share above chance | protocol page |
| EEG-fNIRS-based Handwriting Trajectory Dataset | published | 4 | 3: derivation, original terms, consent statement and ethics approval; 4: share above chance | protocol page |
| REFED emotion dataset (EEG-fNIRS) | published | 4 | — | protocol page |
| Bak et al. fNIRS finger- and foot-tapping dataset | published | 4 | 4: share above chance | protocol page |
| MC_RTT (Neural Latents Benchmark) | published | 4 | — | protocol page |
| OpenNeuro ds007420 · multi-distance fNIRS | published | 3 | — | fixed-protocol baseline |
| **Shin2022, a new dataset page in this release** | | | | |
| Shin2022 · closed-loop motor imagery EEG (Figshare 20383716) | published | 4 | 4: chance level, share above chance, result or hold on a page | protocol page |
| **The status-only sources the plan names: ds004902, stieger-longitudinal, falcon-h2, rabut-fus** | | | | |
| OpenNeuro ds004902 · paired sleep-condition recordings | status only | 3 | 3: consent statement and ethics approval | fixed-protocol baseline; chance level; share above chance |
| Stieger longitudinal BCI · one-person pilot | status only | 4 | 4: chance level | protocol page |
| FALCON H2 · human intracortical handwriting | status only | 3 | — | fixed-protocol baseline; chance level |
| Rabut et al. · human functional ultrasound through a cranial window | status only | 3 | — | fixed-protocol baseline; chance level |
| **IESSEEG (a clinical-groups section, no dataset page)** | | | | |
| IESSEEG · infantile epileptic spasms syndrome EEG (Capur/IESSEEG) | published | 4 | 4: chance level, share above chance, result or hold on a page | protocol page |
| **eldBETA (score held, D2)** | | | | |
| eldBETA · eldercare-oriented SSVEP benchmark database | score held | 4 | 4: chance level, result or hold on a page | protocol page |
| **ZuCo2 (hold: converted-run timing)** | | | | |
| ZuCo 2.0 via NEMAR nm000279 | status only | 2 | — | rights review; original OSF terms; per-excerpt text terms; consent statement and ethics approval |
| **L-FAME (status only since 2026-09-23; left out of the register on 2026-09-22)** | | | | |
| L-FAME | status only | 2 | — | derivation; original terms; consent statement and ethics approval |
| **Listed by the site outside the plan's group-3 list: the six "Not in this release" rows of the /datasets/ register (mvp.json)** | | | | |
| BNCI2014-001 | listed | 3 | 3: consent statement and ethics approval, pinned version | fixed-protocol baseline; chance level; share above chance |
| BNCI2014-004 | listed | 3 (rec. 1) | 2: files opened; 3: consent statement and ethics approval, pinned version | fixed-protocol baseline; chance level; share above chance |
| BNCI2014-008 | listed | 3 | 3: pinned version | fixed-protocol baseline; chance level; share above chance |
| BNCI2014-009 | listed | 3 | 3: consent statement and ethics approval, pinned version | fixed-protocol baseline; chance level; share above chance |
| physionet-eegmmidb-1.0.0 | listed | 3 (rec. 1) | 2: files opened; 3: consent statement and ethics approval | fixed-protocol baseline; chance level; share above chance |
| stew-monster-processed | listed | 2 | — | derivation; original terms |
| **Listed by the site outside the plan's group-3 list: BNCI2015-001 (hold) and the meditation dataset (pilot-studies status entry)** | | | | |
| BNCI2015-001 · next-day adaptation | score held | 4 | 3: rights review, ethics approval, pinned version; 4: chance level, share above chance | protocol page |
| Synchronized multimodal meditation and rest dataset (Zenodo) | status only | 2 | 1: licence as stated | rights review; derivation; original terms; consent statement and ethics approval; pinned version |
| **Adjacent, for B8a: BI2013a, a MOABB catalog row the plan marks planned** | | | | |
| Brain Invaders 2013a (MOABB BI2013a) | planned | 3 (rec. 1) | 2: files opened | fixed-protocol baseline; chance level; share above chance; result or hold on a page |

"rec." marks the four rows where this census recommends the contiguous step (see point 5).

## What the census shows

1. **Steps now:** step 2: 4, step 3: 9, step 4: 27, step 5: 7 (plan rule, 47 sources). At freeze, Shin2022's page, the IESSEEG section and the eldBETA and ZuCo2 holds change only their step-4 "result or hold on a page" item; no row changes step.
2. **Share above chance** is a gap on all 27 rows at step 4 or 5 where a chance level applies: no export carries a count of participants above chance (D12, "not computed"). It is not-applicable for one-participant sources, regression and coverage outcomes, and the ds005342 trade-off protocol.
3. **No chance-level field** on 10 rows at step 4: Wearable SSVEP BCI dataset (dry and wet electrodes), Mobile BCI dataset (SSVEP and ERP paradigms), YSU asynchronous SSVEP-BCI dataset, Dreem Open Datasets (DOD-H and DOD-O), Longitudinal ERP dataset (RSVP), Shin2022 · closed-loop motor imagery EEG (Figshare 20383716), Stieger longitudinal BCI · one-person pilot, IESSEEG · infantile epileptic spasms syndrome EEG (Capur/IESSEEG), eldBETA · eldercare-oriented SSVEP benchmark database, BNCI2015-001 · next-day adaptation. Several publish a prior or random reference arm (Wearable, Shin2022, IESSEEG, Dreem); the census counts only a stored chance value, as the Dreem export does when it labels its prior a floor.
4. **Consent or ethics gaps** (10 rows): EEG Alpha Waves dataset (ethics approval); Dreem Open Datasets (DOD-H and DOD-O) (consent statement (DOD-H); ethics approval (DOD-O)); BINGO cross-linguistic inner-speech dataset (ethics approval; consent statement for this dataset); EEG-fNIRS-based Handwriting Trajectory Dataset (consent statement and ethics approval); OpenNeuro ds004902 · paired sleep-condition recordings (consent statement and ethics approval); BNCI2014-001 (consent statement and ethics approval); BNCI2014-004 (consent statement and ethics approval); BNCI2014-009 (consent statement and ethics approval); physionet-eegmmidb-1.0.0 (consent statement and ethics approval); BNCI2015-001 · next-day adaptation (ethics approval). Package A3's record (`evidence/consent-statements.json`) was present when this census was built and is used for Shin2022, eldBETA, IESSEEG and BI2013a, which now pass; IESSEEG's card states a review-board protocol number with consent waived and does not name the institution.
5. **Rows whose step depends on the rule** (an earlier anchor is a gap): EEG-fNIRS-based Handwriting Trajectory Dataset (plan rule 4, contiguous 2); BNCI2014-004 (plan rule 3, contiguous 1); physionet-eegmmidb-1.0.0 (plan rule 3, contiguous 1); Brain Invaders 2013a (MOABB BI2013a) (plan rule 3, contiguous 1). Recommendation for B8a/B8b: keep the plan rule for the handwriting dataset (run and published, with its stated rights gaps at step 3, the plan's own badge pattern), and use the contiguous step where no file was ever opened (BNCI2014-004, PhysioNet eegmmidb, BI2013a), which also matches the plan's "BI2013a at step 1".
6. **Alpha-waves version finding** (`findings[code=version_clarification]` on `site-alpha-waves`): the site scores Zenodo record 2605110, the last version under concept 2348891 as captured; the record holds 20 subject files and 19 recordings are scored; an earlier inventory names the source as NEMAR nm000221 / Zenodo 2348892 with 19 subjects; MOABB lists the concept DOI with 19 subjects. Which version record 2348892 is, and whether it holds the same files, is not on file (no capture of it).
7. **L-FAME** stays at step 2, the step its 2026-09-22 review reached: files opened (eight on 2026-09-22, sixty in the 2026-09-23 expansion), licence as stated CC BY-NC 4.0 at a pinned revision, no derivation or original-terms record, no consent or ethics statement, no model result. A `policy_note` finding carries the reversal sentence from the plan.
8. **ZuCo2** is at step 2 with step-3 gaps "rights review", "original OSF terms; per-excerpt text terms" and "consent statement and ethics approval", matching the plan's "Step 2 of 5 · held: converted-run timing". Its wording rule (one converted run, no run code, no row values) is carried in the row.
9. **ds007420** has a dataset page and sits at step 3: its published result is a fixed numerical coverage check, and its decoding baseline is held. The Wearable SSVEP row has a pinned-version gap: the data used is the Tsinghua author mirror as acquired, with no version or DOI, and Figshare version 4 is cited without byte identity.
10. **Sources the site lists beyond the plan's group-3 list** (8 rows, census groups `site_register_withheld` and `status_only_other`): the six "Not in this release" rows of the /datasets/ register (BNCI2014-001, -004, -008, -009, PhysioNet eegmmidb, STEW), BNCI2015-001 (editorial hold) and the meditation dataset named in a pilot-studies status entry. The plan merges the four BNCI2014 rows and eegmmidb into site rows (§2.6 group 4), so B8a needs them; BNCI2015-001, STEW and the meditation dataset need a placement decision. The meditation dataset's Zenodo record id (17735692) is in a research handoff only, and no licence or rights record exists for it.
11. **BI2013a licence wording.** A3 captured the Zenodo record page and its linked deed: the page names Creative Commons Attribution 1.0 Generic for the stored identifier "cc-by". The plan (§1.2) prints "the exact version is not established". The census records A3's finding with its caveat and leaves the wording to B8a and the owner.

## Boundaries

- Read-only over site data, the review records and the research folders; these two notes are the only files written in the repository; no network.
- Values copied are licence strings, versions, hashes and counts already printed by served files; no participant rows, identifiers, demographics, run codes or signal values. Paths are repo-relative.
- Census ids (`site-<slug>`) are not register row ids; B8a assigns opaque ids through `register-ids.json`.
- Sources marked `"served": false` are research or review records. A fact from one reaches the site only through the register JSON that B8 freezes.
