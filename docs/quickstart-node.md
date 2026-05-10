# Sky Tracker SDK - Node.js Quickstart

**Prerequisites**

- Node.js 18 or later
- `sky_tracker.exe` (Windows) or `sky_tracker` (Linux) built from the C++ runtime
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

The runtime reads this variable on every run. A missing or invalid key exits with code 3 and prints a clear error.

---

## 2. Point to the executable (if needed)

The SDK searches common build paths automatically. If it cannot find the binary, set:

```powershell
$env:SKY_TRACKER_EXE = "C:\path\to\sky_tracker.exe"
```

---

## 3. Run the test script

```powershell
node cpp_tracker\node_sdk\test.js `
  <video.mp4> `
  <x,y,w,h>  `
  <maxFrames> `
  <output.csv> `
  [output.mp4]
```

**Example - 120 frames, CSV only:**

```powershell
node cpp_tracker\node_sdk\test.js `
  sample.mp4 `
  469,409,26,38 `
  120 `
  results.csv
```

**Example - 120 frames with annotated video:**

```powershell
node cpp_tracker\node_sdk\test.js `
  sample.mp4 `
  469,409,26,38 `
  120 `
  results.csv `
  annotated.mp4
```

**Expected output:**

```
Sky Tracker Node SDK test
source=sample.mp4
csv=results.csv
output=annotated.mp4
frames=120
avg_fps=47
rows=120
active_rows=118
last= { frame: 119, id: 1, state: 'confirmed', ... }
```

The annotated MP4 is written at the original video resolution with a cyan target overlay. Encoding lowers measured FPS - omit it for throughput benchmarks.

---

## 4. Use the SDK from your own code

```js
import { SkyTrackerCli, parseTrackCsv } from "./cpp_tracker/node_sdk/index.js";

const tracker = new SkyTrackerCli({
  licenseKey: process.env.SKY_TRACKER_LICENSE_KEY,
});

const run = await tracker.trackVideo({
  source: "sample.mp4",
  bbox: [469, 409, 26, 38],
  maxFrames: 120,
  csv: "results.csv",
  output: "annotated.mp4", // optional
  profile: "default",
});

console.log(run.metrics);
// { frames: 120, elapsedSeconds: 2.54, averageFps: 47.2 }

const rows = await parseTrackCsv(run.csv);
const active = rows.filter((r) => r.state !== "lost");
console.log(`active=${active.length}/${rows.length}`);
```

### CSV telemetry fields

| Field                                  | Type   | Description                         |
| -------------------------------------- | ------ | ----------------------------------- |
| `frame`                                | number | Frame index                         |
| `id`                                   | number | Track ID                            |
| `state`                                | string | `confirmed`, `tentative`, or `lost` |
| `center_x`, `center_y`                 | number | Target centre, pixels               |
| `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h` | number | Bounding box                        |
| `speed_px_s`                           | number | Speed in pixels/second              |
| `hits`, `misses`                       | number | Track hit/miss counters             |
| `target_confidence`                    | number | 0–1 template match confidence       |
| `target_score`                         | number | Raw template score                  |
| `target_reason`                        | string | Internal tracking decision label    |

### trackVideo options

| Option       | Default      | Description                                           |
| ------------ | ------------ | ----------------------------------------------------- |
| `source`     | **required** | Video path, stream URL, or camera ID                  |
| `bbox`       | -            | Initial target `[x, y, w, h]` or `"x,y,w,h"`          |
| `maxFrames`  | unlimited    | Stop after N frames                                   |
| `csv`        | temp file    | Telemetry output path                                 |
| `output`     | -            | Annotated MP4 output path                             |
| `profile`    | `"default"`  | Tracking profile (`default`, `pi4-target`, `missile`) |
| `licenseKey` | env var      | Per-run licence key override                          |

---

## 5. Sending evaluation results back

Share `results.csv` and (optionally) `annotated.mp4` with us. The CSV contains the full frame-by-frame telemetry needed to diagnose tracking accuracy and FPS on your specific target.

---

## Known limits (evaluation build)

- Licence is validated on every run. An expired or tampered key exits immediately with code 3.
- The annotated video output (`--output`) encodes with `mp4v` codec - some players prefer H.264. Open in VLC or ffmpeg if your default player cannot decode it.
- Camera inputs work but live-frame latency is higher than file sources on Windows due to VideoCapture buffering.
- The CLI-backed Node SDK is not suitable for <5 ms per-frame integrations. A future native N-API binding will address that.
