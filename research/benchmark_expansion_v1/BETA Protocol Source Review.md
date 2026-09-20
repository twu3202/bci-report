# BETA SSVEP benchmark protocol: source review

13 September 2026. This review fixes the first BCI Arena BETA comparison; it is not a reproduction of Liu et al.'s within-participant benchmark.

## Source-grounded dataset contract

The verified Figshare/Hugging Face revision contains `S1.mat`-`S70.mat`, `Description.pdf`, and `README.md`. Each subject has four blocks and one trial for each of 40 targets per block: 11,200 trials total. `data.EEG` is `[channel, time, block, condition]`: S1-S15 are `[64,750,4,40]`; S16-S70 are `[64,1000,4,40]`. `suppl_info.srate` is 250 Hz. These facts agree with the [author paper](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2020.00627/full) (sections 2.4-3.2) and local `Description.pdf`.

Acquisition was 64-channel SynAmps2 EEG, Cz-referenced, 1,000 Hz, hardware passband 0.15-200 Hz and 50 Hz notch, outside a shielded room. The released epochs were zero-phase filtered 3-100 Hz, then downsampled to 250 Hz. Every epoch starts 0.5 s before stimulus onset and ends 0.5 s after the nominal 2 s (S1-S15) or 3 s (S16-S70) stimulation interval. The paper reports a mean visual latency of 124.96 +/- 14.81 ms and used a 130 ms shift in its later classification analysis.

Use the common primary window `EEG[:,125:625,:,:]` (Python half-open indexing): exactly 500 samples from stimulus onset through 2.0 s. This is the only exact two-second interval guaranteed to remain inside nominal stimulation for all 70 people. Do not call it latency-corrected. A `[0.13,2.13)` sensitivity analysis is not part of v1: for S1-S15 it enters the post-stimulation/rest interval, where online visual feedback could occur. If added later, 130 ms is 32.5 samples and requires a declared rounding rule.

The MAT documentation does not explicitly name the stored voltage unit. Native values are physiologically consistent with microvolts (four checked subjects: standard deviation 6.58-9.13 native units), the paper plots response amplitudes in microvolts, and [MetaBCI's independent BETA loader](https://metabci.readthedocs.io/en/master/_modules/metabci/brainda/datasets/tsinghua.html) multiplies the MAT array by `1e-6` before MNE ingestion. Lock `source_unit = "uV"`, but retain `unit_evidence = "inferred; author documentation omits explicit unit"`. Keep native microvolts in prepared arrays; convert to volts only at an API boundary that requires SI units. Record every model-specific scale multiplier.

The condition axis is not ascending frequency. Its exact frequency order is `8.6, 8.8, ..., 15.8, 8.0, 8.2, 8.4` Hz. Use each file's `suppl_info.freqs[condition]` as the label mapping and assert equality across all 70 files. Never sort the frequency list without applying the same permutation to EEG. The local phase array repeats `[0,0.5,1,1.5] * pi`, but the 15 June 2022 corrigendum in `Description.pdf` says it should repeat `[1.5,0,0.5,1] * pi`. Treat local phase metadata as known-invalid and exclude it from v1; sine/cosine CCA and power features are phase-invariant.

## Locked comparison

Question: how well does a fixed method identify the prompted visual target of an unseen participant using four or eight posterior channels?

- Four channels: `POZ, O1, OZ, O2`.
- Eight channels: `PO5, PO3, POZ, PO4, PO6, O1, OZ, O2`.

The four-channel set is nested in the eight-channel set. Resolve names case-insensitively from `suppl_info.chan`; assert the exact resulting indices for every file. The paper's online system used nine posterior channels (`PZ, PO3, PO5, PO4, PO6, POZ, O1, OZ, O2`), supporting the region choice, while BCI Arena's sets are deliberately smaller recorded-channel subsets.

Use seven subject folds: `fold = (subject_number - 1) % 7`. For outer fold `k`, test fold `k` and train on the other six folds. This yields 60/10 train/test participants, keeps all four blocks together, and gives every participant one test appearance. There is no validation split because every hyperparameter and training budget is fixed before scoring and no method uses early stopping. Fit scalers, learned heads, and all training statistics on training participants only.

Run both montages for these six methods:

1. Standard CCA with sine/cosine references at each file's 40 frequencies and harmonics 1-3. It is training-free and should be reported as such.
2. Spectral ridge: fixed exact-frequency sine/cosine power features for harmonics 1-3, per selected channel; training-only standardization and a frozen ridge configuration.
3. EEGNet from scratch for exactly 20 epochs with one frozen seed and no test-based changes.
4. Frozen LaBraM Base embeddings plus ridge, `alpha=100`.
5. Frozen EEGPT embeddings plus ridge, `alpha=100`.
6. Frozen CBraMod embeddings plus ridge, `alpha=100`.

Freeze the exact EEGNet architecture, optimizer, batch size, spectral-ridge alpha, seed, embedding pooling, resampling, missing-channel handling, and checkpoint hashes in `protocol.json` before a scored run. Do not add a new filter over the full 3/4 s stored epoch: that would allow later samples to influence the selected window. If an adapter requires filtering, apply it only to the extracted 500 samples, document padding, and reuse the identical result across folds. The release has already undergone zero-phase 3-100 Hz filtering, so this benchmark is on author-preprocessed EEG.

Primary outcome is mean participant balanced accuracy, which equals participant accuracy here because every participant has four trials per class. Also save participant accuracy, macro F1, trial-level predictions, confusion matrices, and a participant bootstrap 95% interval. The uniform reference is 2.5%. Do not present ITR as a primary score: this cross-subject offline setup and fixed two-second signal window do not reproduce the paper's online timing or within-subject calibration.

## Pretraining-overlap status

The local overlap audit contains only PhysioNet MI, BNCI2014-001, and Sleep-EDF rows, so it does not settle BETA.

- [LaBraM's paper](https://proceedings.iclr.cc/paper_files/paper/2024/file/47393e8594c82ce8fd83adc672cf9872-Paper-Conference.pdf) Appendix D does not list BETA among its named pretraining datasets. Its self-collected data and exact released-checkpoint provenance are insufficiently enumerated for record-level proof. Status: `paper_not_disclosed; exact_checkpoint_unknown`.
- [EEGPT's paper](https://proceedings.nips.cc/paper_files/paper/2024/file/4540d267eeec4e5dbd9dae9448f0b739-Paper-Conference.pdf) Appendix C.1 explicitly includes the earlier Tsinghua/Wang SSVEP benchmark: 35 people, six blocks, five-second stimulation, plus M3CV with SSVEP. These are not BETA's 70 people/four blocks/two-or-three-second protocol, but they are unusually close task/domain exposure. Status: `BETA_not_disclosed; near_domain_pretraining_seen`.
- [CBraMod's paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/bbbd6d915cb90be21c1254a82d45cedd-Paper-Conference.pdf) section 3.1 says pretraining used TUEG clinical EEG. BETA is not disclosed. Status: `paper_disclosed_unseen; exact_checkpoint_hash_pending`.

Publish these statuses beside results. They support descriptive frozen-encoder comparison, not a claim that all encoders had equal prior exposure. The compatibility run must also verify checkpoint-specific units: LaBraM expects microvolt-scaled input in its official pipeline, EEGPT describes millivolt standardization, and CBraMod divides by a 100-microvolt scale. A common unrecorded normalization would invalidate the comparison.

## Failure conditions

Abort before scoring on a missing trial, nonfinite sample, inconsistent channel/frequency order, shape outside the two documented groups, unexpected sampling rate, participant overlap, checkpoint mismatch, or an adapter that cannot produce the frozen embedding under its declared input contract. Preserve failures; do not silently substitute a model, channel, phase list, longer window, or sorted class order.
