**Correlation quality update — 2026-09-06**

In 0.2.0, these changes are opt-in through `correlation-quality` and
`adaptive-quality`. The existing profiles retain our original engine and tuning.
Each quality profile keeps the source engine's alignment and geometry policy.
The measurements below were recorded on the source branch; merged results are
in the [0.2.0 release notes](release-0.2.0.md).

This branch implements the CPU reliability improvements identified in the [quality review](correlation-quality-review.md). The correlation path now verifies target appearance before accepting an observation and freezes learning when evidence is weak. Correlation boxes keep the selected size by default; physical scale search is optional. SDK methods remain the same; select a quality profile to enable this engine.

**Fixed-size correlation follow-up**

The `correlation-quality` profile preserves the initial selection width and height through tracking, fallback measurements, coasting, and recovery, including tiny targets that otherwise receive larger scale limits. Its FFT search evaluates only the current scale. The `adaptive-quality` profile retains its existing scale search and foreground geometry policy.

Use `--target-correlation-scale-adaptation` to enable nearby scale search and confirmed box resizing. The default confirmation count is three consecutive strong correlation observations agreeing within 2.5% of the first proposed size. PSR and appearance must meet the learning thresholds, and confidence must meet both box and template update thresholds. Current-size matches, inconsistent estimates, weak evidence, fallback detections, loss, and denied geometry updates clear pending evidence. Recovery holds the last accepted size while tracking is re-established. Unconfirmed scales do not train appearance or correlation models. Proposal evaluation copies/restores confirmation state, so discarded proposals do not count as frames.

`--target-correlation-scale-confirm-hits N` sets the confirmation count (minimum 2). `--target-no-correlation-scale-adaptation` restores fixed sizing. Internal C++ callers can set `useCorrelationScaleAdaptation` and `correlationScaleConfirmHits`. These settings do not replace adaptive foreground fitting or multi-target ownership restrictions.

Follow-up validation: all seven C++ suites pass, including fixed dimensions for tiny and large targets, exposure changes, textured template/boundary fallbacks, loss/recovery, scale flicker, sustained growth/shrinkage, discarded proposals, and rejected geometry. The correlation, template, and multi-target suites also pass with ASan/UBSan on OpenCV 4.14.

On the same 861-frame `video_8.mp4` run and `541,826,53,68` selection, fixed mode reports exactly 53 × 68 px in every output row. It reports two lost frames (391 and 447), matches 11/12 visible checkpoints, and has 19.878 px mean center error across those 11 matches. Optional confirmed scale adaptation matches 12/12 checkpoints with 23.328 px mean error. These averages cover different matched populations. Constant box size does not establish continuous identity lock; the optional scale mode remains useful when the apparent target size changes. These are focused checks, not a release-accuracy certification or a new paired performance benchmark.

**Behavior changes**

- FFT peak statistics use circular distances. Subpixel interpolation wraps at the response boundary. Identical input no longer produces the reproduced half-pixel displacement, and the wrapped main peak is no longer counted as a competing object.
- Correlation training, inference, and updates share log intensity mapping, zero-mean contrast normalization with a noise floor, and Hann windowing. Mislabelled shifted initialization crops are removed. Training accumulation is averaged so online learning has consistent weight.
- A separate target appearance verifier combines normalized luminance, gradients, immediate-boundary contrast, and distinctive foreground Lab chroma. Color is measured relative to the surrounding region so sky/cloud colors do not dominate the object signature. Grayscale mode skips color scoring. Quarter-turn reference views help with orientation changes.
- Every acceptance path in a correlation-assisted tracker, including motion/template fallbacks and recovery, checks appearance. A strong context correlation alone cannot satisfy the target-presence check. Confidence remains a heuristic quality score, not a calibrated identity probability.
- When scale search is enabled, one filter evaluates physically resized search patches at nearby scales. A strong verified current-scale match skips extra FFTs. Adaptive multi-target scale search can use the existing recovery-size hint and wider scale candidates; visible geometry still passes through ownership arbitration. Discarded proposals do not commit scale or model state.
- Learning requires stronger appearance evidence than localization, the template-learning permission, the PSR learning gate for correlation updates, and the existing ownership permission. Updates use the accepted sample scale. The verifier retains the initial reference permanently and up to three trusted diverse appearances.
- Long-loss recovery tries the preserved correlation model before the contrast-based sky search. Recovery observations must be consistent across confirmation frames. Prediction during confirmation publishes zero confidence and does not learn the candidate.
- The motion fallback can estimate camera translation from four downsampled image tiles. At least three reliable tiles must agree before registration is used. Low texture or inconsistent motion leaves the existing raw-difference fallback in place. Newly exposed frame borders are excluded from the registered difference. This is translation compensation, not full rotation/affine stabilization, and it does not change the motion-state estimator.
- Appearance scores are cached only within one proposal evaluation; the cache is cleared for each new frame or alternative proposal.

**Defaults and tuning**

| Setting | Previous | Updated |
| --- | ---: | ---: |
| Correlation acceptance PSR | 3.0 | 6.0 |
| Correlation learning PSR | 4.0 | 8.0 |
| Maximum second-peak ratio | 1.0 | 0.85 |
| Correlation learning rate | 0.08 | 0.04 |
| Independent appearance acceptance | — | 0.28 |
| Independent appearance learning | — | 0.60 |

The PSR statistics changed, so old thresholds are not directly comparable. These defaults have focused regression coverage, not universal calibration. Camera-motion compensation is enabled by the `correlation-quality` and `adaptive-quality` profiles; the `default` profile retains its existing policy.

New CLI overrides:

```text
--target-correlation-min-appearance 0.28
--target-correlation-update-min-appearance 0.60
--target-camera-motion-compensation
--target-no-camera-motion-compensation
```

The learning appearance threshold must be at least the acceptance threshold. Existing PSR, learning-rate, grayscale, and geometry options still apply. C++ callers using internal `TemplateTrackerConfig` can set `correlationMinAppearance`, `correlationUpdateMinAppearance`, and `useCameraMotionCompensation` directly. SDK callers selecting a quality profile receive these thresholds. Existing profiles keep their original tuning.

**Validation**

- All seven C++ test executables pass.
- The correlation, template, and multi-target suites also pass when compiled directly against OpenCV 4.14 with AddressSanitizer and UndefinedBehaviorSanitizer.
- Four Python evaluation-tool tests pass.
- New coverage includes circular subpixel offsets, competing peaks, blank responses, translation accuracy, measured scale growth, discarded scale proposals, target disappearance on textured background, equal-luminance color distractors, recovery without model contamination, exposure changes, foreground color under background/orientation changes, camera translation, and low-texture/foreground-only registration rejection.
- Existing multi-target crossing, ownership, and adaptive-geometry tests remain enabled and pass.

The full CMake build and video evaluation used the installed OpenCV 5.0 runtime with a build-local `-include opencv2/geometry.hpp` compatibility flag. The installed OpenCV 4 video library could not load its missing protobuf dependency. The three affected core suites were therefore separately built and tested with OpenCV 4 core/imgproc. No system libraries or repository OpenCV requirements were changed to accommodate that local setup.

The footage comparison below describes commit `f09bd72`, before the fixed-size correlation follow-up. It uses all 861 frames of `video_8.mp4`, initialization `541,826,53,68`, and the same 12 existing visible annotations. Matching uses the evaluator's 60 px distance gate. These checkpoints measure sampled quality; they do not prove uninterrupted lock. Before/after runtime measurements alternate serially, without concurrent builds, using the median of three runs per profile/version. The table below records those paired results.

| Profile | Version | Matched / 12 | Mean error px | P95 error px | Mean IoU | Median FPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| default | before | 12 | 12.471 | 25.545 | 0.414 | 267.17 |
| default | after | 12 | 12.471 | 25.545 | 0.414 | 263.80 |
| correlation | before | 12 | 32.808 | 57.244 | 0.312 | 261.05 |
| correlation | after | 12 | 21.209 | 38.047 | 0.413 | 210.00 |
| adaptive | before | 9 | 16.146 | 30.800 | 0.366 | 261.83 |
| adaptive | after | 12 | 16.864 | 34.997 | 0.356 | 171.96 |

Correlation mean center error decreases by 35.4%, while median throughput decreases by 19.6%. Adaptive recovers three additional checkpoints, with a 34.3% throughput cost. Adaptive error/IoU averages cover different matched populations before and after; they do not establish an improvement in box precision. Default tracking output is unchanged. These are local CPU measurements, not Raspberry Pi/Jetson or universal accuracy claims.

The numeric ID-switch counter is insufficient to establish physical identity for a single tracker that always returns ID 1. The dedicated disappearance/distractor regressions complement the sparse footage metrics. The suite's `passed` label without threshold arguments is not a release-accuracy certification; the stricter documented focused gate and additional footage are still required before release.

**Reproduction**

Build and run the normal C++ tests using an intact OpenCV installation:

```bash
cmake -S cpp_tracker -B cpp_tracker/build-quality -DCMAKE_BUILD_TYPE=Release
cmake --build cpp_tracker/build-quality -j
ctest --test-dir cpp_tracker/build-quality --output-on-failure
python3 -m unittest discover -s cpp_tracker/tests -p 'test_*.py'
```

Evaluate a profile with unchanged labels and initialization:

```bash
python3 cpp_tracker/tools/run_labeled_suite.py \
  --exe cpp_tracker/build-quality/sky_tracker \
  --truth cpp_tracker/labels/ground_truth.csv \
  --videos-dir . \
  --output-dir cpp_tracker/build-quality/evaluation/correlation \
  --include-video video_8.mp4 \
  --initial-bbox-override video_8.mp4=541,826,53,68 \
  -- --profile correlation-quality
```

**Remaining work**

Dense held-out footage, target-hardware latency measurements, covariance-driven search, affine camera-motion correction, and learned verification/detection remain separate work. CLAHE, aggressive denoising, sharpening, and learned restoration are not enabled by this change. Full occlusion or indistinguishable target crossings still require explicit uncertainty rather than a promise of perfect visual lock.
