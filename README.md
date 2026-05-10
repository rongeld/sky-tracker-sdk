# Sky Tracker SDK

C++ tracking core for fast-moving small objects — installable as a Python package, no GPU required.

## Install

```bash
pip install sky-tracker-sdk
```

```bash
npm install @sky-tracker/node
```

## Quick start

```python
import cv2, sky_tracker

cap = cv2.VideoCapture("video.mp4")
ok, first_frame = cap.read()

tracker = sky_tracker.Tracker("default")
tracker.lock(first_frame, bbox=(469, 409, 26, 38))

while cap.isOpened():
    ok, frame = cap.read()
    if not ok:
        break
    result = tracker.update(frame)
    print(result.cx, result.cy, result.confidence)
```

## Licence

A valid licence key is required at runtime.

Set the key before running:

```powershell
$env:SKY_TRACKER_LICENSE_KEY = "<your-token>"
```

Or drop `sky_tracker.lic` next to your script — the runtime finds it automatically.

## Documentation

- [Python quickstart](docs/quickstart-python.md)
- [Node.js quickstart](docs/quickstart-node.md)

## Platforms

| Platform | Status |
| --- | --- |
| Windows x64 | Verified |
| Linux x86_64 | Planned |
| Raspberry Pi 4 (ARM64) | Benchmark required |
| macOS | Planned |
