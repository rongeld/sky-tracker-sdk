# Sky Tracker 0.2.0 release and migration notes

For the release containing the macOS portability fixes, see
[Sky Tracker 0.2.1](release-0.2.1.md). The preparation and validation details below
refer to 0.2.0.

## Behavior changes

The default profile now combines correlation identity tracking with scheduled foreground-box fitting and smoothed geometry. Tiny targets use a 64-pixel correlation window automatically. Grayscale scoring and the existing recovery limits remain in place. Template Lab conversion is deferred until needed to reduce startup cost.

Existing CLI flags, Python constructors and result objects, Node calls, and tracker CSV columns remain available. Tracking positions, boxes, confidence, velocity, and recovery can change when using `default` or omitting the profile. Applications tuned to the previous behavior should explicitly select `legacy`.

| Profile | 0.2.0 behavior |
|---|---|
| `default` | Improved correlation and foreground fitting; automatic 64/128/256 search |
| `adaptive` | Stable foreground geometry with color scoring; automatic 64/128/256 search |
| `correlation` | Previous correlation-only 128/256 automatic search policy |
| `legacy` | Previous default settings from v0.1.12 |

For `default` and `adaptive`, the longest initial box side selects 64 pixels through 16 px, 128 through 80 px, and 256 above 80 px. For `correlation`, targets through 80 px retain 128 pixels, including tiny targets. Selection also applies at reinitialization. Explicit `--target-correlation-search` values still override either policy.

## Retaining the previous default

- CLI: add `--profile legacy` to the existing command.
- Python: use `sky_tracker.Tracker("legacy")`, `sky_tracker.MultiTracker("legacy")`, or `config.profile = "legacy"` with `TrackerConfig`.
- Node: pass `profile: "legacy"` to `trackVideo()` and use the 0.2.0 CLI runtime. The Node package invokes an external runtime; upgrading the npm package alone does not upgrade that executable. Older runtimes do not recognize `legacy`.

The older `pi4-target`, `raspi4-target`, and `pi-target` aliases continue to select the improved `default`. They do not select `legacy`.

The CLI adds a processing-timing summary line. The benchmark tool adds processing columns and a repetition `run` column; custom consumers should use column names. The tracker CSV header is unchanged.

## Baseline validation before branch integration

Windows Release CLI and Python module builds passed. All seven CTest suites and nine Python tool tests passed. Python and Node smoke checks each retained 30/30 active frames on video_20 for `default`, `correlation`, and `legacy`, including result/CSV parsing. Close-pass identity coverage also includes `legacy`.

Video_72 uses all 676 frames at 1920x1080, the initial box `892,670,13,11`, and 68 user labels sampled every ten frames. Matches use a 10-pixel radius. Labels are used for initialization and evaluation only.

| Profile | Matched labels | Comparison |
|---|---:|---|
| `legacy` | 26/68 | All 676 tracker CSV rows reproduce the saved previous default executable |
| `correlation` | 57/68 | All 676 rows reproduce the saved previous correlation output; restores the 53/68 regression from automatic 64 |
| `default` | 68/68 | All 676 rows unchanged from the improved default before these release fixes |
| `adaptive` | 68/68 | All 676 rows unchanged from the previously validated stable adaptive executable |

Compatibility is demonstrated on these runs; it is not a guarantee of identical output across every video, platform, or OpenCV build. Previous five-clip accuracy and desktop timing measurements are in [default tracker performance](default-tracker-performance.md).

Both SDK package versions are 0.2.0. The release workflow checks that Python and Node metadata agree and that a release tag matches them before starting platform builds. Its planning code was exercised locally with matching branch/tag inputs and with mismatched package/tag inputs. The npm package dry run passed and reports @sky-tracker/node@0.2.0; no package was published.

## Before publication

Run the existing **Build wheels and binaries** workflow on the prepared branch with `platform=all`, `build_type=full`, `python_versions=all`, and both binaries and wheels enabled. This manual branch run builds artifacts without publishing. Cross-platform CI has not been run for these local changes.

Validate the Linux ARM64 artifact and sustained camera tracking on the Raspberry Pi 4 at the intended resolution, without preview or output files. Desktop measurements do not establish 30 FPS on that device. Check camera throughput, processing time, deadline overruns, and skipped frames; native Linux runtime library compatibility also requires checking on the target OS.

After those checks pass, the corresponding release tag is `v0.2.0`. Tag publication has not been performed as part of this preparation.

## Branch integration

- Existing `default`, `adaptive`, `correlation`, and `legacy` behavior is preserved
  while adding opt-in `correlation-quality` and `adaptive-quality` profiles.
  Each quality profile retains the source engine's model alignment and geometry
  policy instead of mixing it with the original engine's adaptive anchor.
- The quality engine adds normalized FFT matching, independent appearance checks,
  guarded learning, camera translation compensation, and optional confirmed scale
  changes. `correlation-quality` holds the selected box size by default.
- A native C++ SDK, Android Y-plane binding, Jetson CPU packaging, standalone
  machine-ID utility, and perpetual license support are included.
- Python and Node signatures and CSV columns remain unchanged. All SDK version
  metadata is 0.2.0; the release workflow rejects inconsistent versions.
- Windows builds can produce the C++ library and Python module together, and
  incremental CLI builds relink when the core library changes. Wheels
  exclude the standalone C++ headers, library, and machine-ID tool.

Android, Jetson, and Raspberry Pi runtime validation remains part of release
qualification. Merging this branch does not publish a release or change tags.

## Integration validation (Windows, OpenCV 4.12)

All nine C++ suites and nine Python tool tests pass. The native SDK tests cover
all eleven profiles, Gray8/Bgr8/Rgb8 input, padded rows, immutable caller buffers,
invalid inputs, and single/multiple target results. Close-pass identity tests also
exercise both quality profiles.

On video_72, all 676 CSV rows for `default`, `adaptive`, `correlation`, and `legacy`
match the saved pre-merge outputs exactly. Both quality profiles also reproduce
all 676 rows from their source branch equivalents. Matched checkpoints are
68/68 for default and adaptive, 57/68 for correlation, 26/68 for legacy,
63/68 for correlation-quality, and 61/68 for adaptive-quality. The quality
profiles are alternatives to evaluate, not a universal accuracy upgrade.

The default profile passes the focused five-video accuracy gate on video_8,
video_9, video_12, video_20, and video_24: 57/57 visible checkpoints matched,
no sampled false positives or ID switches, and all per-video thresholds met.
These checks do not establish Raspberry Pi 4 camera throughput or accuracy on
unlabeled frames.

Python and Node smoke tests retain 30/30 active frames on video_20 for all six
tracking profiles. Standalone examples build against the installed C++ package
and run with all six profiles. A Python 3.13 Windows wheel builds with only the
extension and package metadata; it does not contain native SDK headers,
libraries, or helper executables. Platform wheel repair and cross-platform
release builds still run in CI before publication.

An incremental-build check touches the core library and confirms that MSVC
relinks the CLI, covering the library-name collision fixed during integration.
The release planning code accepts matching branch/tag versions and rejects a
mismatched tag. No release tag or package has been published by this merge.
