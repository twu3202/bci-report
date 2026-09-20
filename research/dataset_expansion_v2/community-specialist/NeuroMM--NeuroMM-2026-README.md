---
license: cc-by-nc-4.0
viewer: false
extra_gated_prompt: >-
  This dataset is provided for academic research and NeuroMM-2026 challenge participation only.
  By requesting access, your team confirms that all submitted information is accurate and complete.
  The dataset, annotations, and any derived files must not be redistributed, mirrored, modified, or used for commercial purposes without prior written permission.
  Access will be granted only after manual review by the NeuroMM-2026 organizers.
extra_gated_fields:
  Team Name: text
  Team Leader Name: text
  Team Leader Email: text
  Team Members (comma-separated): text
  Organization / University / Company: text
  Country / Region: country
  I confirm that my team will use this dataset for academic research and NeuroMM-2026 challenge participation only: checkbox
  I agree not to redistribute the dataset, annotations, or derived files without written permission: checkbox
language:
  - en
tags:
  - eeg
  - multimodal
  - seizure-detection
  - benchmark
  - neuromm-2026
---

# NeuroMM-2026 — Train + Val Open Release

This repository contains two parts of the NeuroMM-2026 multimodal seizure detection challenge dataset:

- **Train + Val** (root `annotations/` + `archives/`): **25,426 EEG samples** (20,298 train / 5,128 val) with labels and matching pre-extracted **visual features** from 7 vision backbones.
- **Test-phase candidate set** (`candidate/`): the test-phase inputs only — **no labels**. Predictions are submitted to and scored on the official Codabench leaderboards; ground-truth labels are held privately by the organizers. See `candidate/README.md`.

Challenge website: <https://2026.neuromm.org>

---

## Dataset Access Form

Please **follow this format before submitting the gated form**. Many requests are rejected because the team information does not match the expected format.

### Example Application

| Field | Example |
| :--- | :--- |
| Team Name | GML-MM-Lab |
| Team Leader Name | Alice Chen |
| Team Leader Email | alice.chen@university.edu |
| Team Members (comma-separated) | Alice Chen, Bob Li, Carol Wang |
| Organization / University / Company | Guangdong Laboratory of Artificial Intelligence and Digital Economy (Shenzhen) |
| Country / Region | China |

- Submit **one request per team**, not one request per member.
- The request should be submitted by the **team leader or the main contact person**.
- Make sure the team name and member list are consistent with your challenge registration.

---

## Tasks

- **Task 1** — Binary spike-vs-non-spike classification (EEG only)
- **Task 2** — Binary spike classification (EEG + Video)
- **Task 3** — 5-class seizure subtype classification (positives only, EEG + Video)

## Layout

```
NeuroMM-2026/
├── README.md                       ← this file
├── annotations/
│   └── neuromm2026_train_val.csv   ← 25,426 rows (20,298 train / 5,128 val)
├── splits/
│   └── split.md                    ← patient-level partition documentation
└── archives/
    ├── eeg.tar                              ← 25,426 raw EEG .npy
    ├── video_clip-base.tar                  ← OpenAI CLIP ViT-B/32 features (8, 512)
    ├── video_videomae-base.tar              ← VideoMAE-base features (1, 768)
    ├── video_videomae-large.tar             ← VideoMAE-large features (1, 1024)
    ├── video_dinov2-base.tar                ← DINOv2-base features (8, 768)
    ├── video_dinov2-large.tar               ← DINOv2-large features (8, 1024)
    ├── video_siglip-base.tar                ← SigLIP-base features (8, 768)
    └── video_timesformer-k400.tar           ← TimeSformer (Kinetics-400) (1, 768)
```

After extraction:
```
tar -xf archives/eeg.tar
# -> processed/features/eeg/{sample_id}.npy
tar -xf archives/video_clip-base.tar
# -> processed/features/video/clip-base/{sample_id}.npy
```

## Manifest Columns

| Column | Description |
|---|---|
| `sample_id` | Unique window identifier (matches the `.npy` filename stem) |
| `split` | `train` (20,298) or `val` (5,128); patient-disjoint |
| `label` | Binary label: 1 = spike / seizure positive, 0 = negative |
| `label_type` | Multi-class label: 0 = negative, 1–5 = seizure subtype |
| `subject_id` | Patient identifier; use to enforce patient-disjoint cross-validation |

## EEG Feature Format

Each `.npy` is a NumPy array shape `(29, 2000)` (mixed `float16` / `float32`):
- 29 raw EEG channels at 500 Hz
- 2000 timesteps = 4-second window

The reference baseline derives 23 + 3 ECG/EMG = 26 channels via differential pairs. See the official baseline repository for the loader.

## Loading Example

```python
import numpy as np, pandas as pd
df = pd.read_csv("annotations/neuromm2026_train_val.csv")
print(df["label_type"].value_counts())          # multi-class distribution
sid = df.iloc[0]["sample_id"]
x = np.load(f"processed/features/eeg/{sid}.npy")
print(x.shape, x.dtype)                          # (29, 2000)

# Video feature for the same sample (CLIP-base)
v = np.load(f"processed/features/video/clip-base/{sid}.npy")
print(v.shape, v.dtype)                          # (8, 512)
```

## Important: Patient-Level Splitting

The provided train/val split is **patient-disjoint** (no patient appears in both). If you do additional CV folds, also enforce patient-level splitting via `subject_id` to avoid label leakage.

## Test-Phase Candidate Set (`candidate/`)

The `candidate/` subfolder holds the **test-phase inputs only — no labels**:

```
candidate/
├── README.md               ← candidate-set instructions
├── candidate_ids.txt        ← one opaque id per line
└── archives/
    ├── eeg.tar              ← EEG .npy            (29, 2000)
    └── video_<backbone>.tar ← 7 visual backbones
```

Extract each archive (they expand under a common `candidate/` root) and run
the official baseline's `predict_candidate_test{1,2,3}` tools over **every**
id to produce a Codabench submission. Only the official hidden samples for
each test are scored; you are not told which ids those are, and the
ground-truth labels are never distributed. Use automated machine-learning
methods only. Full details in `candidate/README.md`.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — academic research and NeuroMM-2026 challenge participation only. No redistribution, no commercial use.

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{neuromm2026,
  title  = {NeuroMM-2026: Multimodal Seizure Detection Dataset},
  year   = {2026},
  url    = {https://2026.neuromm.org}
}
```
