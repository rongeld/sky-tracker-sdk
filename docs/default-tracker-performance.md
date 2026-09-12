# Default tracker quality and headless performance

The default profile now uses the same correlation identity and scheduled foreground-box fitting as adaptive. It retains grayscale contrast/appearance scoring, the 0.75 template-update confidence threshold, candidate geometry for multi-target ownership, and its existing recovery limits. The default profile uses automatic 64/128/256 search sizing; the explicit `correlation` profile retains 128/256 sizing for compatibility. No profile or search flag is required.

Foreground fitting runs on the existing four-frame schedule. The jitter fix retains its center correction between fits and smooths relative geometry without delaying identity translation. Original full-resolution frames and coordinate geometry are preserved.

The grayscale path now defers the template's Lab conversion. Color templates are still maintained, and sky recovery computes the Lab cache on demand, preserving its existing color recovery score. Updates invalidate that cache. This avoids paying color initialization cost before normal grayscale tracking; it does not remove a recovery cue.

## Accuracy

`video_72.mp4` has 676 frames at 1920x1080 and approximately 30 FPS. Initialization is `892,670,13,11`. The 68 user labels at ten-frame intervals are used only for initialization and scoring, not for correcting tracker output.

| Profile | Labels within 10 px | Mean error over matched labels (px) | P95 error (px) | Mean IoU |
|---|---:|---:|---:|---:|
| Previous default (`4939380`) | 26/68 | 2.155 | 4.747 | 0.298 |
| New default | 68/68 | 2.331 | 4.866 | 0.424 |
| Adaptive | 68/68 | 2.331 | 4.866 | 0.424 |

The previous default's error averages omit its 42 missed labels and therefore cannot be interpreted as better accuracy. Every frame in the new default run is confirmed. Delaying Lab initialization leaves all 676 CSV rows identical to the updated default with eager Lab conversion. These are sparse-label results, not proof of every frame or every video.

Five other labeled clips retain all matches and pass the focused gate (mean <=15 px, P95 <=35 px, miss rate <=0.20, false-positive rate <=0.15, zero ID switches, desktop throughput >=12 FPS; 60 px matching radius).

| Clip | Matches before and after | Previous mean error (px) | New mean error (px) |
|---|---:|---:|---:|
| video_12.mp4 | 10/10 | 3.343 | 2.838 |
| video_20.mp4 | 12/12 | 1.698 | 1.747 |
| video_24.mp4 | 12/12 | 5.450 | 4.345 |
| video_8.mp4 | 12/12 | 12.697 | 14.222 |
| video_9.mp4 | 11/11 | 3.474 | 6.282 |

Accuracy is not uniformly better: video_8 and video_9 have larger errors, and video_20 changes slightly. The focused gate remains a minimum acceptance test.

## Desktop measurement

Windows Release build on an Intel Core i7-8750H (6 cores / 12 logical processors), original 1920x1080 `video_72.mp4`, one selected target, all 676 frames. Display, annotated output, tracker CSV, JSON, OpenCL, and frame dropping are disabled. These are medians of three full runs per variant with rotating execution order; no benchmark processes run concurrently.

| Variant | Application FPS | Process-launch-inclusive FPS | Steady processing mean (ms/frame) | First-frame processing (ms) |
|---|---:|---:|---:|---:|
| Previous default (`4939380`) | 115.33 | 111.68 | Not instrumented | Not instrumented |
| Updated default | 143.30 | 138.75 | 3.445 | 27.339 |
| Adaptive | 139.46 | 133.83 | 3.544 | 238.635 |

The updated default's application FPS ranged from 141.91 to 144.24 in the final batch. Earlier batches varied with desktop load, so this is not a hardware-independent speed claim. The initial Lab cache setup is deferred in default, while adaptive still initializes its color appearance model. The final five-clip run measured 3.75-5.11 ms of steady processing per frame; application rates were 64.48-229.85 FPS, illustrating the additional decoder/queue costs.

## Timing definitions

The application prints two summary lines:

- `avg_fps` measures processed frames per wall-clock second through the application loop, including capture/decoder waits and any requested output. It is not pure algorithm throughput.
- `processing_avg_ms` and `processing_max_ms` measure grayscale conversion and tracker/detector work after queue retrieval and before serialization, drawing, display, or video encoding. The first processed frame is reported separately as `startup_processing_ms` so cold initialization does not distort steady processing cost. `processing_frames` is the sample count; a one-frame run has zero steady samples.
- `processing_budget_ms` is the input frame period, using reported FPS or a 30 FPS fallback. `processing_over_budget` counts steady samples that exceed it.
- `skipped_frames` counts source-index gaps between processed frames. It detects application queue skipping, not camera-driver drops, buffering, or complete camera-to-result latency.

A Pi 4 at 30 FPS has a 33.3 ms frame period. Desktop rates cannot certify that budget on ARM or a particular camera pipeline. A camera-paced 30 FPS log alone also does not show spare capacity. Check processing cost, deadline misses, skipped frames, and sustained camera throughput on the Pi at the actual resolution. Camera input currently defaults to 640x480 unless width/height are specified; the desktop clip remains 1920x1080.

## Reproduce

From the repository root, after a Release build, this runs headlessly without tracker CSV or video output and records three timing repetitions:

```bash
python cpp_tracker/tools/benchmark_videos.py \
  --exe ./cpp_tracker/build-vcpkg/Release/sky_tracker.exe \
  --pattern video_72.mp4 --max-frames 676 --repeat 3 \
  --csv cpp_tracker/build-vcpkg/default_benchmark.csv \
  -- --bbox 892,670,13,11
```

Use the native executable path on the Pi. For the live camera test, supply a target box for that camera view and `--source 0`, the actual `--width`/`--height`, and `--max-frames 900`. Leave display, video output, tracker CSV, and JSON output disabled. The existing camera queue drops stale frames by default; inspect the skipped-frame counter instead of assuming every captured frame was tracked. Interactive selection can be used once for initialization when a screen is available.

The benchmark parser supports current and older summary formats, including short runs without periodic log lines. It reports missing older processing metrics as blank, not zero.

Validation: Release build, all seven CTest suites, and nine Python tests. Multi-target close-pass tests now use the shared production profile factory rather than copies of old profile settings. A recovery regression verifies deferred Lab conversion preserves the strong color score. Short-run/repeat and skipped-frame-counter smoke tests passed.

Local evidence: `cpp_tracker/build-vcpkg/evaluation/pi4_default/`.
