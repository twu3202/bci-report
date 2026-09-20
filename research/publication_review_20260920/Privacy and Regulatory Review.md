# Privacy and Regulatory Review

**Scope and limit.** This is issue spotting, not legal advice. It assumes free, non-advertising personal research; local processing of public EEG; and an English static site with aggregate model results, no uploads, raw EEG, or diagnosis. Dataset provenance, affiliation, hosting, analytics, or monetization may change the conclusions.

## Legal requirements and likely scope

### China: personal information and outbound publication

Under China’s Personal Information Protection Law (PIPL), information relating to an identified or identifiable person is personal information; **irreversibly anonymized** information is excluded (Arts. 4, 73). Subject codes are only de-identification if a person remains recoverable. Identifiable clinical EEG and labels are likely sensitive medical/health information. Whether EEG is also “biometric” depends on its use and identifiability (Art. 28).

Research is not a standalone PIPL Art. 13 basis. Lawfully public personal information may be processed only within a reasonable scope, subject to objection; major-impact processing requires consent (Arts. 13(1)(6), 27). Sensitive information normally requires purpose, necessity, safeguards, separate consent, and extra notice (Arts. 28–30). Public disclosure generally requires separate consent (Art. 25).

If China-collected personal information goes to an overseas host, Arts. 38–39 may require a transfer mechanism, notice, separate consent, and equivalent protection; sensitive/public/outbound processing also triggers an impact assessment (Arts. 55–56). Send **no raw EEG, labels, identifiers, or per-subject scores** to the current host unless location and a compliant route are established. Aggregates fall outside PIPL only if people cannot be identified and the result cannot be reversed or singled out.

PIPL Art. 72 excludes a natural person’s processing for personal or household affairs. A public benchmark site is outside the safe core of that exception, so it should not be the compliance premise.

### China: research ethics and human genetic resources

The 2023 ethics Measures apply to covered research by Chinese medical institutions, universities, and research institutes (Arts. 2–5). Art. 32 allows exemption only where work causes no bodily harm, involves neither sensitive personal information nor commercial interests, and uses lawfully obtained public or anonymized data. Identifiable or health-linked EEG fails the sensitive-information condition. Duties of an unaffiliated researcher are uncertain; original consent, source rules, dataset terms, or later institutional use may still require review. Obtain a responsible institution’s written determination before claiming exemption.

Clinical EEG is not automatically a “human genetic resource.” The Regulation covers genetic material and information generated from it (Art. 2). Electrical recordings alone do not fit; reassess if linked to genomic material or derived information.

### GDPR

GDPR applies through an EU establishment or when a non-EU controller offers goods/services to people in the EU or monitors them there (Art. 3); EU accessibility alone is insufficient (Recital 23). If triggered, identifiable EEG may be health data; biometric data is protected when used for unique identification (Art. 9(1)). Research is not a blanket exemption: it still needs an Art. 6 basis and Art. 9(2) condition. Art. 9(2)(j) depends on EU/member-state law and Art. 89 safeguards. Anonymous information is outside GDPR; pseudonymized data remains personal (Recital 26).

### Dataset licenses and platform status

The **exact dataset license/version controls**. CC BY-NC-ND 4.0 permits noncommercial sharing of licensed material and internal creation, but not sharing, of adaptations (Secs. 1–4). Free/no-ads supports “NonCommercial”; sponsorship or paid access requires renewed review. Aggregate accuracy values may be independent facts, but this is jurisdiction-sensitive; copying annotations, transformed files, or substantial database content raises risk. Attribute each dataset and link its license.

CC licenses do not generally grant participants’ privacy, publicity, or similar personality rights (CC 4.0 Sec. 2(b)(1)). Hugging Face’s terms say uploaders represent they have rights, preserve accompanying license terms, and put downstream use at the user’s risk. A public repository therefore is evidence of access, not proof that the uploader obtained all copyright, consent, privacy, or ethics permissions.

### Mainland hosting and content classification

If the site is later served through mainland-China infrastructure, plan for a noncommercial ICP filing before launch and display/link the filing number (Noncommercial Internet Information Service Filing Measures, Arts. 5, 7, 13). Art. 11 requires additional approval documents only when separate rules require approval for the listed regulated service. The Internet News Information Service rules define news as reporting/commentary on political, economic, military, diplomatic and other public affairs or emergencies (Arts. 2, 5); they do **not** make every scientific note licensed news.

The 2009 Medical and Health Information Measures broadly cover medical-institution, preventive-health, and preventive-health-channel content (Arts. 2–4). Whether this benchmark qualifies is uncertain. Before mainland hosting, check the final pages; avoid diagnosis, treatment advice, individual interpretation, patient services, and clinical-efficacy claims. A research-only label reduces risk but does not remove licensing duties.

## Project risk-reduction policy

1. Keep raw and subject-level EEG/results local; publish only cohort-level metrics with minimum cell-size and re-identification review.
2. Do not publish subject IDs, rare-condition slices, example traces, timestamps, filenames, electrode artifacts, or metadata that enable singling out.
3. Maintain a dataset register with source, exact license/version, uploader, original study/consent/ethics link, permitted purpose, and proof date; quarantine unclear datasets from public results.
4. Disable unnecessary analytics/cookies. If logs or analytics are used, treat them as a separate website privacy workstream.
5. Present results as reproducible model evaluation, with provenance, limitations, and no clinical or participant-level claims.

## Questions for counsel or the responsible institution

- Does each original consent/ethics approval permit secondary computational benchmarking and public aggregate publication, including overseas hosting?
- Are the proposed aggregation thresholds sufficient for the smallest cohorts and rare diagnoses, considering linkage to public metadata?
- Does any dataset’s actual license/version or database right bar the planned output, and did the uploader have authority to license it?
- Is any source participant, controller, institution, or processing activity in EU territorial scope, and what national research law applies?
- Before mainland hosting, do the final pages fall within internet medical/health information service rules, and what filings or approvals does the chosen host require?

## Primary sources

- [PIPL (CAC; Arts. 3–4, 13, 25, 27–30, 38–39, 55–56, 72–73)](https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm)
- [2023 Human-Subject Research Ethics Measures (NHC; Arts. 2–5, 28, 32–36)](https://www.nhc.gov.cn/qjjys/c100016/202302/6b6e447b3edc4338856c9a652a85f44b.shtml)
- [Human Genetic Resources Regulation, revised 2024 (NHC; Arts. 2–3, 7, 9)](https://www.nhc.gov.cn/qjjys/rlyczygl/202503/c5373f14621e4011b6cbc932184086a2/files/1746832760945_40292.pdf)
- [GDPR official text (EUR-Lex; Recitals 23, 26; Arts. 3, 6, 9, 89)](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
- [CC BY-NC-ND 4.0 Legal Code (Secs. 1–4)](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode)
- [Hugging Face Terms of Service (“Your Content,” “Open Source”)](https://huggingface.co/terms-of-service)
- [Noncommercial Internet Information Service Filing Measures (MIIT; Arts. 5, 7, 11, 13)](https://www.miit.gov.cn/gyhxxhb/jgsj/cyzcyfgs/bmgz/xxtxl/art/2024/art_84a0cfa0ebd049bbbe751dca9a008e56.html)
- [Internet News Information Service Rules (CAC; Arts. 2, 5)](https://www.cac.gov.cn/2017-05/02/c_1120902760.htm)
- [Internet Medical and Health Information Service Measures (Ministry of Justice archive; Arts. 2–5, 12–17)](https://www.moj.gov.cn/pub/sfbgw/flfggz/flfggzbmgz/200907/t20090728_144717.html)

*Reviewed against official texts on 2026-09-20.*
