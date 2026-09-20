# BCI Arena Dataset Rights Review

**Review date:** 2026-09-20  
**Scope:** personal scientific research; free; no ads or fees; no raw EEG uploads or redistribution; public output limited to cohort-level benchmark aggregates. This is a publication risk screen, not legal advice or a guarantee of compliance.

## Release recommendation

Ship **ds006593**, **ds003810**, and **ds005383** first. Each has a pinned upstream release, clear reuse terms, and dataset-specific evidence of ethics review and written consent. ds005383 has an OpenNeuro CC0 label while its publication describes CC BY 4.0; use the stricter attribution practice and do not reproduce its third-party Chinese stimulus text. Suppress participant tables, pseudonymous IDs, demographics, dates, trial traces, and downloadable derived data for all three.

The existing **ds005342** result can remain only as an aggregate four-person case study. Remove participant-level results and IDs, do not break results down by condition or demographic, state prominently that only 4 of 32 participants were evaluated, and describe the estimate as a small-cohort result. Do not say the participants are anonymous: the upstream table combines exact age, sex, handedness, academic major, and pseudonymous IDs.

**EEGMAT**, **EESM19**, and **BETA** are also candidate-eligible under the stated controls, but are lower priority. EEGMAT requires ODC-By attribution and contains occupation and recording-date metadata. EESM19 uses a processed mirror of a CC0 OpenNeuro sleep dataset that also contains diaries and timing data. BETA is CC BY 4.0, yet its participants were told their data would be used for non-commercial scientific research; its status assumes the site remains research-led and is not directed toward commercial advantage. Ads, sponsorship, fees, paid access, or commercial organizational use require a fresh review.

## Hold or clarify

Withhold **BNCI2014-008**. Its eight-person ALS cohort is described with exact age, sex, functional score, and onset type linked to pseudonymous codes. Ethics approval and informed consent are documented, but consent for public secondary benchmark publication was not located. The small clinical cohort creates unusually high reidentification risk even when the displayed metric is aggregate.

Keep **BNCI2014-009**, **BNCI2014-001**, **BNCI2014-004**, **EEGMMIDB**, and the **STEW processed mirror** unranked pending clarification. BNCI licenses are record-specific: 001/004 are CC BY-ND 4.0, while 008/009 are CC BY-NC-ND 4.0. ND forbids distributing adapted material; NC also confines use to noncommercial purposes. Aggregate facts may avoid distributing an adaptation, but that has not been established for this pipeline. The BNCI descriptions do not supply adequate dataset-specific consent evidence for 001/004/009.

EEGMMIDB has a clear ODC Attribution 1.0 database license and PhysioNet deidentification assurances, but no dataset-specific IRB or consent statement was found. STEW’s paper reports written consent and NTU IRB approval, while the Hugging Face mirror claims CC BY 4.0; the exact IEEE DataPort upstream terms and the mirror’s authority to license processed files were not verified.

## Cross-cutting controls

OpenNeuro requires uploaders to attest to ethics permissions, absence of identifiable PHI, and inapplicability of GDPR protections, and releases datasets under CC0. Treat that as repository evidence, not a substitute for dataset consent. CC0 never establishes that privacy, publicity, confidentiality, or third-party rights have disappeared. Likewise, a free site is not automatically noncommercial.

Publish one dataset-level row per benchmark, cite both dataset and primary paper, state the exact release/revision, and maintain a private provenance ledger. Re-review any change involving participant-level displays, subgroup comparisons, raw or derived downloads, user uploads, advertising, sponsorship, fees, organizational commercialization, or a new mirror/revision.
