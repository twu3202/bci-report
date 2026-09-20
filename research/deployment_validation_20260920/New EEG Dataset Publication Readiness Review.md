# New EEG Dataset Publication Readiness Review

**Date:** 20 September 2026  
**Scope:** Aggregate benchmark statistics only. No raw EEG, participant-level scores, trial traces, demographics, questionnaires, or downloadable participant-keyed outputs. This is a bounded readiness assessment, not legal certification.

## Decision

All three releases are **candidates for aggregate benchmark publication with attribution**:

| Evaluated release | Aggregate publication | Raw redistribution |
|---|---|---|
| Tsinghua Wearable SSVEP, official author mirror snapshot (2026-09-20) | Candidate | Hold; the mirror is official, but byte identity with Figshare v4 is unproven |
| NEMAR nm000125, v1.0.2, Mobile SSVEP derivative | Candidate | Out of scope; CC BY 4.0 appears to permit redistribution with attribution, but a separate human-subject review is required |
| NEMAR nm000201, v1.0.2, Mobile ERP derivative | Candidate | Out of scope; CC BY 4.0 appears to permit redistribution with attribution, but a separate human-subject review is required |

CC BY 4.0 permits sharing and adaptation with attribution, a license link, and an indication of changes. It does not waive privacy or other third-party rights. Our aggregate-only release is materially narrower than republishing EEG or participant tables.

## Exact records and required citations

**Tsinghua wearable SSVEP.** Cite Fangkun Zhu, Lu Jiang, Guoya Dong, Xiaorong Gao, and Yijun Wang, “An Open Dataset for Wearable SSVEP-Based Brain-Computer Interfaces,” *Sensors* 21(4), 1256 (2021), [doi:10.3390/s21041256](https://doi.org/10.3390/s21041256), and the Figshare dataset, Version 4, [doi:10.6084/m9.figshare.13560281.v4](https://doi.org/10.6084/m9.figshare.13560281.v4). The analysis used the official Tsinghua BCI Lab author mirror snapshot, not a byte-verified Figshare-v4 snapshot. Figshare labels Version 4 [CC BY 4.0](https://figshare.com/articles/dataset/An_Open_Dataset_for_Wearable_SSVEP-Based_Brain-Computer_Interfaces/13560281). The paper reports Tsinghua ethics approval No. 20200020, informed consent from all participants, and that data sharing accords with the consent provided.

**NEMAR Mobile SSVEP.** Cite Lee, Y., Shin, G., Lee, M., and Lee, S. (2026), “Lee2021 – SSVEP paradigm of the Mobile BCI dataset,” Version v1.0.2, NEMAR, [doi:10.82901/nemar.nm000125](https://doi.org/10.82901/nemar.nm000125). The [NEMAR record](https://nemar.org/dataset/nm000125) labels this BIDS derivative CC BY 4.0.

**NEMAR Mobile ERP.** Cite Lee, Y., Shin, G., Lee, M., and Lee, S. (2026), “ERP paradigm of the Mobile BCI dataset,” Version v1.0.2, NEMAR, [doi:10.82901/nemar.nm000201](https://doi.org/10.82901/nemar.nm000201). The [NEMAR record](https://nemar.org/dataset/nm000201) labels this BIDS derivative CC BY 4.0.

For both NEMAR releases, also cite Young-Eun Lee, Gi-Hwan Shin, Minji Lee, and Seong-Whan Lee, “Mobile BCI dataset of scalp- and ear-EEGs with ERP and SSVEP paradigms while standing, walking, and running,” *Scientific Data* 8, 315 (2021), [doi:10.1038/s41597-021-01094-4](https://doi.org/10.1038/s41597-021-01094-4). The paper reports Korea University IRB approval KUIRB-2019-0194-01, written informed consent, and CC BY 4.0 availability of the data. The exact consent forms were not reviewed, so no broader consent claim should be made.

## Release conditions and unknowns

- Publish cohort aggregates only and remove participant IDs from statistical artifacts.
- Cite the exact dataset DOI/version and the associated paper; describe both NEMAR objects as MOABB-generated BIDS derivatives.
- Do not expose NEMAR participant-table fields such as age, sex, handedness, weight, height, or BCI experience. Do not expose Tsinghua questionnaire, impedance, or per-person results.
- Do not claim the Tsinghua author mirror is byte-identical to Figshare v4; upstream hashes were unavailable.
- Reopen the review if raw redistribution, participant-level reporting, or downloadable derived signals are proposed.

## Wearable gain-invariance wording

The current phrase “invariant to a common positive unit conversion” is acceptable only when kept narrow. Recommended publication wording:

> The reported gain-invariance check covers one positive scalar unit conversion applied uniformly to all relevant training and test samples before training-only standardization. It does not establish invariance to different wet-versus-dry hardware gains or to broader sensor-domain shifts.

Avoid “hardware-gain invariant,” “wet/dry gain invariant,” or “immune to hardware domain shift.” The check does not cover different device gains, channel- or frequency-dependent transfer functions, additive offsets, clipping, impedance changes, or changing noise floors.

The machine-readable evidence and decision details are in `new-dataset-publication-readiness.json` in this directory.
