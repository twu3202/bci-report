---
license: cc-by-4.0
language: [en, zh]
tags: [eeg, ssvep, brain-computer-interface, bci, dry-electrode, ads1299, biosignal]
pretty_name: "cap32-ssvep — SSVEP calibration on a 32-channel dry-electrode cap"
size_categories: [n<1K]
task_categories: [time-series-forecasting]
---

# cap32-ssvep — SSVEP calibration on a 32-channel dry-electrode cap

Four SSVEP calibration sessions from one subject on a low-cost 32-channel dry-electrode cap
(TI ADS1299, 250 Hz, WiFi/UDP). Recorded for a drone-control project; published because the
**failure mode is more informative than the accuracy**.

Code and analysis: **[github.com/twu3202/EEG_SSVEP_Drone](https://github.com/twu3202/EEG_SSVEP_Drone)**
Motor-imagery data from the same cap: **[Twu31/cap32-mi-eeg](https://huggingface.co/datasets/Twu31/cap32-mi-eeg)**

> ⚠ **These files hold 10 posterior channels, not 32.** Channel selection was applied at
> record time, so these sessions cannot be re-analysed with a different montage.
> `meta_json.channels_full` lists the 32 the cap was actually wearing.

## Quick start

```python
import numpy as np
d = np.load("data/ssvep_20260725_171821.npz", allow_pickle=True)
X, y = d["X"], d["y"]        # (60, 10, 500) float32 µV;  (60,) int32 target index
d["freqs"]                   # (4,) Hz          d["phases"]  (4,) rad
d["names"]                   # ('forward','back','left','right')
d["ch_names"]                # ('P7','P3','PZ','P4','P8','PO3','PO4','O1','OZ','O2')
d["filled"]                  # (60,) fraction of each trial reconstructed across UDP drops
import json; json.loads(str(d["meta_json"]))   # paradigm, timing, link and stimulus stats
```

Signals are raw µV, unfiltered, not re-referenced. Trials are already epoched.

## Sessions

| file | trials | targets | window | frequencies (Hz) | stimulus fps / jitter | frame loss |
|---|---|---|---|---|---|---|
| `ssvep_20260725_150031` | 120 | 12 | 3.0 s | 8.0 … 15.7, 0.7 steps | 404.2 / 0.11 ms | 0.087 % |
| `ssvep_20260725_160927` | 3 | 1 | 3.0 s | 8.0 | 433.1 / 0.21 ms | 0 % |
| `ssvep_20260725_164720` | 120 | 12 | 2.0 s | 8.0 … 15.7 | 142.8 / 0.72 ms | 0 % |
| `ssvep_20260725_171821` | 60 | 4 | 2.0 s | 8.57, 10, 12, 15 | 125.0 / 0.58 ms | 0 % |

Trial structure: `cue 1.0 s → flicker (window) → rest 0.5 s`, with a measured 0.14 s
display latency already accounted for. Targets are drone commands (forward / back / left /
right / up / down / rotate cw / rotate ccw / takeoff / land / flip / hover).

`ssvep_20260725_164720`'s `link_received` is recorded as 0, which is a metadata bug — the
signal is present. Its stimulus ran at 142.8 fps with 0.72 ms jitter, the worst of the four.

## What the data shows

Decoding is only just above chance:

| session | targets | best decoder | accuracy | chance | 95 % CI |
|---|---|---|---|---|---|
| `150031` | 12 | FBCCA, 2.4 s | 0.150 | 0.083 | [0.10, 0.22] |
| `171821` | 4 | TRCA-CCA, 1.8 s | 0.450 | 0.250 | [0.33, 0.58] |

Statistically above chance, practically unusable. The useful finding is *how* it fails.

### Errors fall to low frequencies — and it is not alpha

Misclassifications piled up at 8 Hz whatever the true target. This subject's IAF is exactly
10.00 Hz, so alpha is the obvious suspect, but it is the second effect, not the cause.

CCA/FBCCA's ρ is a **variance ratio**, so `argmax` over candidates compares *absolute power*.
Under an `S(f) ∝ f^-α` aperiodic background the noise floor goes as `ρ_noise(f) ∝ f^(-α/2)` —
monotonically decreasing, so the lowest candidate wins by default. Measured slope **−0.95 to
−1.11**, matching an independently fitted α = 1.79–2.34 to within 0.06. The 8 Hz floor is
**1.7–1.9× higher** than 15.7 Hz.

Alpha does sit on top: in the one confound-free session the excess over the power law peaks
at exactly 10.0 Hz, matching the measured IAF — but that excess is **+19.7 %** against
**+71 %** from the 1/f floor.

Derivation and measurements: `docs/lowfreq_bias_report.pdf` (中文).

**Practical consequence:** with log-spaced or high-only stimulus frequencies, or with the 1/f
floor divided out before `argmax`, this bias largely disappears. It is a scoring artifact,
not a property of the subject.

## Caveats

1. **10 channels only** — see the warning above.
2. **Dry electrodes over the occiput seat poorly.** SSVEP lives on Oz/O1/O2/POz; this is the
   hardest region for a dry cap, and it bounds everything here.
3. **Timing is critical.** At 12 Hz one cycle is 83 ms, so a 4 ms epoch-boundary error is 14°
   of phase; eTRCA/TDCA collapse to chance when that drifts. Dropped UDP frames are
   reconstructed rather than skipped, and `filled` marks how much of each trial that was.
4. **The cap's sample clock runs +3235 ppm fast** (measured later against an external
   generator). Negligible for band power, but a 0.4 % error rotates a 12 Hz tone by a full
   cycle in ~2 s.
5. **Single subject, single day.** All four sessions are from 2026-07-25.

## License

CC BY 4.0. Please link back to
[github.com/twu3202/EEG_SSVEP_Drone](https://github.com/twu3202/EEG_SSVEP_Drone).

Recordings are from a single consenting adult subject (the author). No clinical or
identifying information is included.
