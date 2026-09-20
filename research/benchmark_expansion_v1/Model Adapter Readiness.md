# Model Adapter Readiness: BETA 40-class SSVEP

Scope: BETA, 64 channels at 250 Hz; 2 s windows (`500` samples); full montage and posterior subsets of 4/8 channels. The recommendations below reuse only assets already present in the repository. The model-check runtime is `experiments/asset_readiness/.venv-modelcheck/bin/python`. Do not download, retrain, or fall back to randomly initialized foundation weights during an encoder run.

## Reusable assets and exact loads

| Model | Exact checkpoint and SHA-256 | Adapter status | Feature output |
|---|---|---|---|
| LaBraM Base | `experiments/asset_readiness/weights/labram-base-tensors.pt`; `c79337f581bc7e501999d7a2213ed6e25c3a3a40964f507549dc05c45bb3b574` | Ready for any supported named standard-10/20 subset | Existing first-batch pooling: mean all channel/time patch tokens to `[N,200]` |
| EEGPT target encoder | `experiments/asset_readiness/weights/eegpt-target-encoder-tensors.pt`; `9ce130abd9f66cd6141b15918c35760da62ffc86b90f611cdf7b4cf4cb0585df` | Ready for any channel names in its `CHANNEL_DICT` | Mean over 8 time patches and flatten 4 summary tokens: `[N,2048]` |
| CBraMod | `experiments/idle_replay_v1/model_assets/weights/cbramod-pretrained_weights.pth`; `0792cb808c14e6b7a2bb2ce1dff379bc47bc54c49a779825bdfeb33bf8157178` | Shape-ready for `C=64,8,4`, but channel semantics are not named; every channel configuration needs a declared input order | Remove `proj_out` (`Identity`), mean the 2 time patches, retain `C × 200` |
| EEGNet | No pretrained weights. Existing 17-channel init is only `17×500`: `experiments/idle_replay_v1/model_assets/small_model_initializations/EEGNet-untrained.pt`, SHA `23dc95626ab746397245e944c23dfc1438a23f1eff61d98623a47bc1251ea0` | Train from scratch for each BETA channel configuration/fold | Class logits; expose a documented penultimate representation only if the protocol requires it |

The registry is `experiments/idle_replay_v1/model_assets/candidate-registry.json`. All foundation loads must use `torch.load(..., map_location="cpu", weights_only=True)`, strict state-dict checks, `eval()`, and `requires_grad_(False)`. Hash the exact file before loading and record the hash in every run manifest.

## LaBraM Base

Instantiate the existing `labram_base_patch200_200` with `EEG_size=400`, `patch_size=200`, `num_classes=0`, `qkv_bias=False`, `init_values=0.1`, and `use_mean_pooling=False`, as in `experiments/asset_readiness/benchmark_mac.py` / `experiments/idle_replay_v1/models.py`. Resample each `[N,C,500]` microvolt window from 250 to 200 Hz (`resample_poly(up=4, down=5)`), divide by 100, and reshape to `[N,C,2,200]`. The temporal patch length is checkpoint-compatible and gives exactly two patches; do not pad a shorter input or alter the patch size.

Build `input_chans` from the source `standard_1020` list in `experiments/asset_readiness/source/LaBraM/utils.py`: `[0] + [standard_1020.index(name)+1 for name in beta_names]`. Normalize case and reject, with a clear error, any BETA label absent from that list. Preserve the BETA recording order in the signal array while passing these IDs; never use `[0,1,...,C]` unless it is the verified semantic mapping. The model’s learned channel positional table supports selecting subsets, so 64, 8, and 4 channels are structurally valid when names are known.

Call `forward_features(x, input_chans=ids, return_patch_tokens=True)`. Preserve the existing first-batch pooling convention from `experiments/asset_readiness/benchmark_mac.py`: mean all returned channel/time patch tokens over axis 1 to `[N,200]`. This is the existing checkpoint-trained `norm`; do not instantiate a new pooling norm or include `mask_token`/`lm_head.*` (the expected excluded keys are exactly those three). If a later protocol chooses per-channel pooling to `[N,C*200]`, treat that as a new declared representation rather than silently changing the first batch.

## EEGPT

Use `EEGTransformer(img_size=[C,512], patch_size=64, embed_num=4, embed_dim=512, depth=8, num_heads=8, mlp_ratio=4.0, qkv_bias=True, norm_layer=partial(nn.LayerNorm, eps=1e-6))`. A 2 s, 250 Hz window must be resampled to 512 samples (`resample_poly(up=128, down=125)`) and scaled exactly as the established adapter (`/1000`). `512/64=8` is exact; never crop or zero-pad to make an incompatible duration fit.

Construct `chan_ids = model.prepare_chan_ids(beta_names)`. This function uppercases and strips trailing periods, then asserts membership in the model’s 64-entry `CHANNEL_DICT`; convert that assertion into a validation error that records the missing names. The EEGPT code supports a variable `C` because channel IDs are embeddings, but arbitrary first-64 or first-`C` IDs are invalid semantic substitutions. Use the exact BETA names and order, and require a manifest of the resolved IDs for every full/4/8-channel condition.

Call `model(x, chan_ids=chan_ids)`. The source returns `[B,8,4,512]`; average axis 1 over the eight time patches and flatten the four summary tokens to `[N,2048]`, independent of `C`. Strict loading should have no excluded checkpoint keys. The original official checkpoint is a 58-channel, 256 Hz, 4 s model; the adapter resamples BETA to native 256 Hz and uses a 2 s (`512` sample) window. Record the duration/channel-count mismatch as adapter conditions; changing `img_size` only changes shape bookkeeping and does not retrain weights.

## CBraMod

The source implementation has no channel-name lookup. It receives `[N,C,patches,200]`; for BETA 2 s at 250 Hz, resample to 400 samples, divide by 100, and reshape `[N,C,2,200]`. `CBraMod()` strict-loads the pinned checkpoint, then set `proj_out = torch.nn.Identity()`. Its depthwise spatial positional convolution uses a 19-channel kernel, so 64/8/4 inputs are tensor-compatible and produce `[N,C,2,200]`.

That compatibility does not establish learned channel meaning: there are no electrode tokens or montage map. Channel order and any channel-count change are a domain shift for full 64, posterior-8, and posterior-4 alike. Each condition may run as a fixed, explicitly recorded structural adapter, but none is intrinsically more semantically valid than another. Label posterior and full-montage results exploratory unless a separate supervised adapter protocol is declared; do not pad missing channels, inject zeros, or use random weights.

## EEGNet

EEGNet is a supervised baseline, not a reusable pretrained encoder. Instantiate Braindecode 1.5.1 with `n_chans=C`, `n_times=500`, `n_outputs=40` (and the fixed architecture hyperparameters from `models.py`: `F1=8, D=2, kernel_length=64, drop_prob=0.25`). The old 17-channel, two-class state file cannot be loaded for BETA. Seed initialization deterministically, fit only on each training split, save the new state hash and train-only normalization, and report it as `pretrained=false`. Repeat independently for C=64, 8, and 4; do not reuse a 64-channel initialization for a subset whose channel dimension differs.

## Provenance and overlap

LaBraM source is MIT (`experiments/asset_readiness/source/LaBraM/LICENSE`); EEGPT source is Apache-2.0 (`experiments/asset_readiness/source/EEGPT/LICENSE`); CBraMod source is MIT and its pinned Hugging Face card declares Apache-2.0 (`experiments/idle_replay_v1/model_assets/license_snapshots/`); Braindecode/EEGNet is BSD-3-Clause. These are provenance records, not commercial clearance. LaBraM reports pretraining on about 20 EEG datasets and EEGPT reports a mixed 58-channel/256-Hz/4-s corpus; the repository does not certify whether BETA appears in either corpus. CBraMod’s overlap with BETA is also unknown. The benchmark must record overlap as `unknown`, avoid claims of independent generalization, and preserve the source/checkpoint revisions and hashes.
