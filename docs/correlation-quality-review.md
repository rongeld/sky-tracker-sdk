**Correlation tracking quality review — 2026-09-06**

Implementation follow-up: [CPU reliability changes and validation](correlation-quality-update.md). The findings below describe the implementation before that follow-up.

The highest-priority improvement is rejecting false locks and protecting the appearance model. Image preprocessing can help, but the present correlation path can confidently track background after the selected object disappears. Better contrast alone does not resolve that failure.

Scope: source inspection of the current working tree, isolated synthetic checks compiled from current sources, and inspection of existing evaluation records. No tracking implementation was changed and no new real-video benchmark was run. Proposed benefits below require paired evaluation. The analysis assumes a CPU-capable baseline, with an optional GPU path.

**What the current system actually does**

The selected-object SDK uses `TemplateTracker`. Its correlation profile enables `CorrelationAssist`, a custom grayscale MOSSE implementation. It predicts a search center using smoothed velocity, evaluates a fixed-size correlation window, and accepts a passing correlation candidate before evaluating the contrast, template, and motion fallbacks.

There are already useful safeguards: speed gating, immutable initial grayscale/color templates, guarded recovery, and a proposal/commit ownership layer in `MultiTracker` that freezes learning during ambiguous interactions. These should be preserved. They do not provide a universal target-presence check for the correlation path.

Color appearance and contrast are enabled in the correlation profile's inherited configuration, but the correlation candidate itself is computed from grayscale and accepted without evaluating those color cues. Its reported confidence is `clamp(PSR / 10, 0, 1)`, not a calibrated probability of correct identity. The selected-object motion predictor is smoothed velocity; the Kalman filter in `SortTracker` is a separate pipeline.

Code locations:

- `src/profile.cpp`: profile configuration.
- `src/template_tracker.cpp:228`: early correlation acceptance.
- `src/template_tracker.cpp:711`: correlation candidate scoring and speed gate.
- `src/template_tracker.cpp:576`: correlation learning gate.
- `src/template_tracker.cpp:1791`: separate grayscale/color appearance scoring.
- `src/template_tracker.cpp:2272`: motion fallback using unregistered consecutive-frame differences.
- `src/multi_tracker.cpp`: ownership arbitration and guarded commit.

**Confirmed synthetic findings**

The probe used current `correlator.cpp`, `correlation_assist.cpp`, and `template_tracker.cpp`, compiled directly with OpenCV core and imgproc. The local reproducer is `/private/tmp/sky-tracker-quality-review/probe.cpp`; it is a diagnostic artifact, not a committed regression test.

| Check | Observed result | Interpretation |
| --- | --- | --- |
| Train a correlation filter on one patch; process that identical patch | Estimated displacement `(-0.5, -0.5)` instead of `(0, 0)` | Subpixel interpolation clamps neighbors at the array boundary although the response is circular. |
| Measure the same response using existing versus circular peak exclusion | Existing PSR `24.265503`, second-peak ratio `0.962158`; circular exclusion PSR `82.956892`, ratio `0.000165` | Wrapped portions of the main peak are incorrectly treated as sidelobes and competitors. These are diagnostic recalculations, not measured tracking improvements. |
| Replace a green textured object with a red object having exactly identical grayscale pixels | `Confirmed`, reason `correlation`, confidence `1.0` | The fast path cannot use the available chromatic distinction. A real object's color can also change; color should be a reliability-weighted cue rather than an unconditional veto. |
| Remove a 20×16 dark target from a stationary textured background | `Confirmed`, reason `correlation`, confidence `1.0` | A strong correlation response does not establish that the selected object is still present. |

The disappearance example is deliberately synthetic. It establishes a reachable failure, not its frequency on customer footage.

**Implementation weaknesses to address**

1. **Circular response geometry.** In `src/correlation/correlator.cpp`, PSR and second-peak exclusion use ordinary coordinate differences, while subpixel interpolation clamps coordinates. Use wrapped neighbors and circular distances. Zero displacement maps to the array boundary, so this affects ordinary tracking around the predicted center. Recalibrate all dependent thresholds after fixing the statistics.

2. **Ambiguity rejection is effectively disabled.** `correlationMaxSecondPeakRatio` defaults to `1.0` and rejection uses `>`. For a positive global maximum, a tied second peak can pass. Simply lowering this threshold now is unsafe because wrapped main-peak energy currently looks like a second peak. Fix the response geometry first, then measure useful ambiguity thresholds.

3. **Background can dominate the learned filter.** The training patch is a 128×128 or 256×256 context window. There is no target-support mask or spatial reliability model constraining which regions constitute the object. A Hann window suppresses patch boundaries; it does not separate target from nearby background. Add target-presence verification and evaluate spatially regularized or masked filter learning.

4. **Acceptance and learning need independent identity evidence.** PSR is useful response quality, but a wrong object or background can also produce a sharp response. Verify candidates against stable appearance and reliable motion evidence before commit. Protect correlation updates with stricter gates than localization. Preserve the existing multi-target ownership veto. Do not require a literal initial-template match forever: viewpoint and lighting changes require a small bank of carefully admitted reference appearances.

5. **The current scale bank does not measure scale.** `CorrelationAssist::initialize()` uses factors `{0.5, 1, 2, 4}` to vary the desired Gaussian width. All filters see the same-size image patch. `locate()` returns center and response statistics, not object scale; the normal correlation candidate retains the existing bbox size. Use a real scale pyramid or separate translation and scale filters. The adaptive profile's foreground geometry helps some scenes but does not replace robust scale estimation.

6. **Initialization augmentation misaligns target positions and labels.** Eight crops move the object relative to the search center, but all are trained with the same zero-displacement desired response. This is a source-level concern about localization bias and peak broadening; its real-video impact was not measured. Compare centered affine appearance perturbations against correctly shifted response labels, with a no-augmentation control.

7. **Preprocessing is incomplete.** Both preprocessing paths currently subtract a mean and multiply by a Hann window. They do not perform logarithmic intensity mapping or contrast normalization. Evaluate a shared implementation with bounded log/contrast normalization and a variance floor. The original MOSSE work describes log mapping, zero-mean/unit-norm normalization, and a cosine window. Numeric scaling and regularization must be retuned together. [MOSSE paper](https://www.cs.colostate.edu/~draper/papers/bolme_cvpr10.pdf)

8. **Motion evidence is not compensated for camera movement.** The fallback computes `absdiff(previous ROI, current ROI)`. Camera pan, shake, or exposure changes can therefore become apparent foreground. Estimate background motion from reliable features outside target boxes, fit a robust transform, and use the residual as supporting evidence. Sparse pyramidal optical flow and robust affine estimation are available in OpenCV. Disable this cue when there are insufficient background features, such as featureless sky. [Optical flow](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html), [transform estimation](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)

**How to use color, motion, and enhanced video**

Keep the captured frame as the common source and compute separate internal feature channels. Painting a motion heatmap onto the video before ordinary correlation changes the object's apparent texture whenever its velocity or camera motion changes. Prefer combining candidate scores from independent channels.

| Cue or processing | Proposed use | Reliability boundary |
| --- | --- | --- |
| Normalized luminance | Main inexpensive correlation channel | Normalization cannot restore clipped or absent detail; use a noise floor. |
| Gradients / HOG | Shape support through moderate illumination changes | Pooling can erase extremely small targets; retain full-resolution luminance for them. |
| Lab chroma or a color histogram | Distinguish similarly shaped objects when color is informative | Reduce weight for desaturated targets, monochrome input, exposure changes, and low light. Compare target and surrounding background distributions. |
| Stabilized frame difference / residual optical flow | Support moving-object hypotheses and reject camera-induced motion | A tracked target may be nearly stationary in image coordinates. Missing motion must not automatically reject it. |
| Mild CLAHE | Optional low-contrast luminance channel | Enhancement can amplify noise. Keep training and detection processing consistent and avoid abrupt frame-to-frame parameter changes. |
| Denoising | Bounded, target-size-aware suppression of sensor noise | Strong spatial smoothing can erase a few-pixel object; temporal averaging without motion alignment creates trails. |
| Sharpening / learned restoration | Separate experiment only if real footage demonstrates benefit | Visual sharpness is not evidence of more accurate target identity or location. |

Color and correlation have complementary strengths, as demonstrated by Staple. CSR-DCF provides a useful design reference for spatial support and channel reliability, and DSST for separate scale estimation. These papers motivate experiments; their published speeds or rankings are not performance promises for this SDK. [Staple](https://arxiv.org/abs/1512.01355), [CSR-DCF](https://arxiv.org/abs/1611.08461), [DSST](https://www.cvl.isy.liu.se/research/objrec/visualtracking/scalvistrack/index.html). OpenCV documents CLAHE's contrast limiting and noise considerations. [CLAHE](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html)

**Recommended delivery order**

1. Establish a dense failure set and add the focused regressions above. Fix circular statistics/subpixel interpolation, then calibrate ambiguity and learning gates. Add target-only presence/appearance verification before accepting correlation. Log raw scores and whether each model learned.
2. Add true scale estimation, normalized luminance, and selectively weighted gradient/color cues. Evaluate each change separately before combining it. Retain full-resolution paths for tiny targets.
3. Add camera-motion compensation and prediction uncertainty. Use actual capture timestamps; make motion uncertainty and coasting time-aware. Expand search as uncertainty grows, while tightening identity verification in larger search regions. Generate several viable hypotheses when the best peak is implausible or ambiguous.
4. Strengthen recovery with a stable appearance bank and candidate-consistent confirmation across frames. On a GPU deployment, evaluate a learned appearance verifier and scheduled detector or learned tracker for difficult recovery. Class detection alone does not identify which of two similar objects was originally selected.

All hypotheses, including recovery and learned-model proposals, should pass the existing ownership/commit layer. A trusted frame may update the short-term model; uncertain or ambiguous frames should freeze learning and report prediction/loss explicitly.

**Evidence needed before claiming better lock**

The documented focused gate has only 10–12 labels per clip. Historical correlation results include 54/57 matched visible labels, 14.081 px weighted center error, and 0.413 weighted IoU in the implementation log. These are historical results, not a fresh measurement of this checkout. Sparse success cannot establish uninterrupted lock between labels.

The evaluator increments ID switches when the returned numeric track ID changes. A single selected tracker that always returns the same ID can follow the wrong physical object without increasing that counter. Dense ground truth, target presence, positional error, and explicit distractor identity must be evaluated together.

Measure:

- Wrong-target and background-lock duration, including while confidence is high.
- Visible-target recall and time to first failure.
- Recovery time and correctness after occlusion, disappearance, and re-entry.
- Center error normalized by target size, bbox IoU, and jitter versus lag.
- Confidence calibration and learning events around failures.
- Median/p95/p99 processing latency on the actual deployment hardware.

Stratify held-out clips by tiny targets, low contrast, blur, exposure changes, camera pan/shake, zoom, deformation, cloud/foliage clutter, distractors, dropped frames, and partial/full occlusion. Include controlled corruptions of the same clips, while reserving genuinely different footage for validation. Compare `default`, `correlation`, and `adaptive` with identical initialization and timestamps.

No RGB tracker can guarantee identity through absent visual information, prolonged total occlusion, or indistinguishable crossings. The practical product objective is accurate measured lock when evidence exists, bounded prediction through short gaps, explicit uncertainty, and reliable recovery without silently switching targets.
