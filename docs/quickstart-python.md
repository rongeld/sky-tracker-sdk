# Sky Tracker SDK — Python Quickstart

**Prerequisites**

- Python 3.10 or later
- OpenCV for Python: `pip install opencv-python`
- `sky_tracker.pyd` (Windows) or `sky_tracker.so` (Linux) built from the C++ Python binding
- Your evaluation licence key

---

## 1. Set your licence key

```powershell
# PowerShell
$env:SKY_TRACKER_LICENSE_KEY = "<your-token>"
```

```cmd
rem Windows CMD
set SKY_TRACKER_LICENSE_KEY=<your-token>
```

```bash
# Linux / macOS
export SKY_TRACKER_LICENSE_KEY=<your-token>
```

The `Tracker` constructor reads this variable at import time. A missing or invalid key raises `RuntimeError` immediately.

---

## 2. Run the smoke test

The quickest check — runs 30 frames of the sample video and reports confidence:

```powershell
python cpp_tracker\tools\smoke_python_sdk.py `
  --module-dir cpp_tracker\build-python\Release `
  --video sample.mp4 `
  --bbox 469,409,26,38 `
  --frames 30
```

**Expected output:**

```
python_sdk_smoke passed frames=30 active=29 max_confidence=0.891
```

If the module directory is the default (`cpp_tracker/build-python/Release`) and `video_20.mp4` exists in the repo root, all flags are optional:

```powershell
python cpp_tracker\tools\smoke_python_sdk.py
```

---

## 3. Frame-by-frame API

```python
import os
import sys
import cv2

# ── Load the module ──────────────────────────────────────────────────────────
MODULE_DIR = r"cpp_tracker\build-python\Release"
if os.name == "nt":
    os.add_dll_directory(MODULE_DIR)   # Windows: load OpenCV DLLs next to the .pyd
sys.path.insert(0, MODULE_DIR)

import sky_tracker  # noqa: E402  (must come after path setup)

# ── Open video ───────────────────────────────────────────────────────────────
cap = cv2.VideoCapture("sample.mp4")
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
dt  = 1.0 / fps

# ── Lock on to the target ────────────────────────────────────────────────────
ok, first_frame = cap.read()
assert ok, "could not read first frame"

tracker = sky_tracker.Tracker("default")   # profiles: default, correlation, birds, missile, pi4-target
tracker.lock(first_frame, bbox=(469, 409, 26, 38))   # (x, y, width, height)

# ── Process frames ───────────────────────────────────────────────────────────
frame = first_frame
for i in range(120):
    if i > 0:
        ok, frame = cap.read()
        if not ok:
            break

    result = tracker.update(frame, dt)

    print(
        f"frame={result.frame:4d}  state={result.state:12s}  "
        f"cx={result.cx:6.1f}  cy={result.cy:6.1f}  "
        f"conf={result.confidence:.3f}"
    )

    # Optional: get annotated frame with cyan HUD overlay
    # annotated = result.annotate()
    # cv2.imshow("sky_tracker", annotated)
    # cv2.waitKey(1)

cap.release()
```

---

## 4. Native multi-target API

Use `sky_tracker.MultiTracker` when the caller provides several selected
targets. The SDK assigns stable `target_id` values from the initial bbox order.

```python
multi = sky_tracker.MultiTracker("default")
multi.lock(first_frame, [
    (469, 409, 26, 38),
    (520, 390, 24, 34),
])

for i in range(120):
    ok, frame = cap.read()
    if not ok:
        break

    for result in multi.update(frame, dt):
        print(
            f"target={result.target_id} state={result.state} "
            f"bbox={result.bbox()} suppressed={result.suppressed}"
        )
```

If two selected target slots claim the same object in a frame, the weaker
duplicate is returned with `suppressed=True`, `state="lost"`, and
`suppressed_by_id` pointing to the target that kept the claim.

Command-line example:

```powershell
python cpp_tracker\examples\track_multi_video.py `
  --video video_20.mp4 `
  --bbox 469,409,26,38 `
  --bbox 520,390,24,34 `
  --csv cpp_tracker\build-python\video_20_multi_sdk.csv
```

---

## 5. API reference

### `sky_tracker.Tracker(profile)`

| Profile | Use case |
|---------|----------|
| `"default"` | General-purpose |
| `"birds"` | Close-pass, occlusion-heavy targets |
| `"missile"` | Fast-moving, scaling targets |
| `"pi4-target"` | Reduced-resolution on ARM hardware |

You can also pass a `TrackerConfig` object:

```python
cfg = sky_tracker.TrackerConfig()
cfg.profile = "birds"
tracker = sky_tracker.Tracker(cfg)
```

### `tracker.lock(frame, bbox)` / `tracker.initialize(frame, bbox)`

Seeds the tracker on the first frame. `bbox` is `(x, y, width, height)` in pixels.

### `tracker.update(frame, dt=-1.0) → TrackResult`

Process the next frame. Pass `dt` in seconds for deterministic video processing. If omitted, the tracker measures wall-clock time automatically.

### `sky_tracker.MultiTracker(profile)`

Native selected-target multi-tracker. Use `lock(frame, bboxes)` with
`bboxes=[(x, y, width, height), ...]`, then call `update(frame, dt)` once per
frame. It returns a list of `TrackResult` objects.

### `TrackResult` fields

| Field | Type | Description |
|-------|------|-------------|
| `frame` | int | Frame counter since `lock()` |
| `lost` | bool | `True` when the tracker has lost the target |
| `state` | str | `"confirmed"`, `"tentative"`, or `"lost"` |
| `cx`, `cy` | float | Target centre, pixels |
| `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h` | float | Bounding box |
| `confidence` | float | 0–1 template match confidence |
| `speed` | float | Speed in pixels/second |
| `hits`, `misses` | int | Track quality counters |
| `reason` | str | Internal tracking decision label |
| `target_id` | int | Stable selected-target id, same as `id` |
| `suppressed` | bool | True when this target was suppressed due to a duplicate claim |
| `suppressed_by_id` | int | Winning target id for a suppressed duplicate, otherwise 0 |
| `bbox()` | tuple | `(x, y, w, h)` shorthand |
| `center()` | tuple | `(cx, cy)` shorthand |
| `annotate()` | ndarray | Copy of the frame with cyan HUD drawn |

---

## 6. Writing a CSV from Python

```python
import csv

with open("results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["frame", "state", "cx", "cy", "confidence"])
    for i in range(120):
        ok, frame = cap.read()
        if not ok:
            break
        r = tracker.update(frame, dt)
        writer.writerow([r.frame, r.state, r.cx, r.cy, r.confidence])
```

---

## 7. Live camera input

For USB/V4L2 cameras, pass an integer camera id to OpenCV and keep the tracker API unchanged:

```python
import cv2
import sky_tracker

cap = cv2.VideoCapture(0)
ok, frame = cap.read()
assert ok, "could not read camera frame"

bbox = cv2.selectROI("select target", frame, fromCenter=False)
cv2.destroyAllWindows()

tracker = sky_tracker.Tracker("pi4-target")
tracker.lock(frame, bbox)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    result = tracker.update(frame)
    cv2.imshow("sky_tracker", result.annotate())
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

On Raspberry Pi OS 64-bit, install the Linux ARM64 wheel and use the same frame-by-frame API. If the official Pi camera is not available as `/dev/video0`, use Picamera2 to capture BGR frames and pass those frames to `tracker.update(...)`.

---

## 8. Sending evaluation results back

Share your CSV and any annotated frames with us. The `reason` field in each row is especially useful for diagnosing tracking failures.

---

## Known limits (evaluation build)

- The Python module is a `.pyd` / `.so` binary built against a specific OpenCV version. If you see import errors, ensure `opencv-python` matches the version used to build the module.
- On Windows, call `os.add_dll_directory(MODULE_DIR)` before `import sky_tracker` so the loader finds OpenCV DLLs next to the module.
- `annotate()` returns a full-resolution copy of the frame — avoid calling it on every frame in throughput-critical paths.
- The licence key is checked when `Tracker()` is constructed. If the key expires mid-session the current tracker instance keeps running; the next `Tracker()` construction will fail.
