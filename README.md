# Sky Tracker SDK

Sky Tracker is a CPU-friendly SDK for following small, fast-moving targets in
video. The caller selects each target with an initial bounding box; Sky Tracker
then maintains its position, identity, motion state, and visible box over time.

It is a selected-target tracker, not a general object detector. Use your own
detector, telemetry, or an interactive ROI to provide the initial
`(x, y, width, height)` box.

## Install

Python 3.10 or later:

```bash
pip install sky-tracker-sdk opencv-python
```

The Node.js wrapper is also available:

```bash
npm install @sky-tracker/node
```

## Licence setup

A valid licence is required when a tracker is created. To request a
machine-locked licence, print the machine ID:

```bash
python examples/machine_id.py
```

Set a licence token in the environment:

```powershell
$env:SKY_TRACKER_LICENSE_KEY = "<your-token>"
```

```bash
export SKY_TRACKER_LICENSE_KEY="<your-token>"
```

Alternatively, place `sky_tracker.lic` beside your script or point
`SKY_TRACKER_LICENSE_FILE` at it.

## Single-target quick start

```python
import cv2
import sky_tracker

capture = cv2.VideoCapture("video.mp4")
fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
dt = 1.0 / fps

ok, frame = capture.read()
if not ok:
    raise RuntimeError("could not read video")

tracker = sky_tracker.Tracker("default")
tracker.lock(frame, bbox=(469, 409, 26, 38))

while True:
    result = tracker.update(frame, dt)
    print(result.state, result.center(), result.bbox(), result.confidence)

    ok, frame = capture.read()
    if not ok:
        break

capture.release()
```

`tracker.initialize(frame, bbox)` is an alias for `tracker.lock(frame, bbox)`.
Pass `dt` in seconds when processing a video file; omit it for live input when
wall-clock timing is appropriate.

## Multi-target quick start

Use `MultiTracker` when the caller selects several targets. Initial bbox order
defines stable `target_id` values: the first box is target 1, the second is
target 2, and so on.

```python
multi = sky_tracker.MultiTracker("default")
multi.lock(
    frame,
    [
        (469, 409, 26, 38),
        (520, 390, 24, 34),
    ],
)

for result in multi.update(frame, dt):
    print(
        result.target_id,
        result.state,
        result.bbox(),
        result.interacting,
        result.prediction_only,
    )
```

When selected targets pass close to one another, the multi-tracker protects
identity and bbox ownership. It can freeze model or geometry learning during an
ambiguous interaction and coast briefly from motion instead of assigning both
tracks to the same observation. The result exposes this state through
`interacting`, `suppressed`, `suppressed_by_id`,
`geometry_ownership_constrained`, and `prediction_only`.

## Profiles

| Profile       | Choose it when                                                                   |
| ------------- | -------------------------------------------------------------------------------- |
| `default`     | You want the recommended speed/quality balance and adaptive visible bbox sizing. |
| `correlation` | You prefer a correlation-led identity lock with conservative box geometry.       |
| `adaptive`    | You want correlation-led identity plus gated foreground bbox fitting.            |

Start with `default`. Compare profiles on your own labelled footage before
changing a production configuration.

## Python examples

### Interactive single target

Select one object, optionally starting later in the video, and save an annotated
MP4 with a zoom inset:

```bash
python examples/track_video.py video.mp4 --start-seconds 10 --profile default
```

Source: [`examples/track_video.py`](examples/track_video.py)

### Interactive multiple targets

Select targets in stable ID order. After selecting at least two boxes, press
Esc on the next selection dialog to start tracking:

```bash
python examples/track_multi_video.py video.mp4 --profile default
```

Source: [`examples/track_multi_video.py`](examples/track_multi_video.py)

### Headless bbox and telemetry

Use a known bbox without opening a selection window. CSV telemetry is always
written; annotated video is optional:

```bash
python examples/track_from_bbox.py video.mp4 \
  --bbox 469,409,26,38 \
  --start-seconds 10 \
  --csv tracks.csv \
  --output tracked.mp4
```

Source: [`examples/track_from_bbox.py`](examples/track_from_bbox.py)

### Machine ID

```bash
python examples/machine_id.py
python examples/machine_id.py --raw
```

Source: [`examples/machine_id.py`](examples/machine_id.py)

Every example supports `--help`.

## Common result fields

| Field                                            | Meaning                                                              |
| ------------------------------------------------ | -------------------------------------------------------------------- |
| `state`, `lost`                                  | Current lifecycle state and whether the target is lost.              |
| `cx`, `cy`, `center()`                           | Target centre in pixels.                                             |
| `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`, `bbox()` | Visible target box.                                                  |
| `confidence`                                     | Tracker confidence from 0 to 1.                                      |
| `speed`                                          | Estimated image-plane speed in pixels per second.                    |
| `reason`                                         | Decision label useful for telemetry and debugging.                   |
| `prediction_only`                                | The output is a tentative motion coast, not an accepted observation. |
| `annotate()`                                     | A copy of the current frame with the SDK overlay.                    |

## Platforms

| Platform               | Status   |
| ---------------------- | -------- |
| Windows x64            | Verified |
| Linux x86_64           | Verified |
| Raspberry Pi 4 (ARM64) | Verified |
| macOS                  | Verified |

## Documentation

- [Python quickstart](docs/quickstart-python.md)
- [Node.js quickstart](docs/quickstart-node.md)
