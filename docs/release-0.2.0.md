# Sky Tracker 0.2.0 release and migration notes

For the release containing the macOS portability fixes, see
[Sky Tracker 0.2.1](release-0.2.1.md). For Linux OpenCV packaging fixes, see
[Sky Tracker 0.2.2](release-0.2.2.md).

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

## Features and additions

- Existing `default`, `adaptive`, `correlation`, and `legacy` behavior is preserved
  while adding opt-in `correlation-quality` and `adaptive-quality` profiles.
- The quality engine adds normalized FFT matching, independent appearance checks,
  guarded learning, camera translation compensation, and optional confirmed scale
  changes. `correlation-quality` holds the selected box size by default.
- A native C++ SDK, Android Y-plane binding, Jetson CPU packaging, standalone
  machine-ID utility, and perpetual license support are included.
- Python and Node signatures and CSV columns remain unchanged.
