"""
Track a single target in a video file and save an annotated result.

Usage:
    python track_video.py your_video.mp4

Requirements:
    pip install sky-tracker-sdk opencv-python

License:
    Set SKY_TRACKER_LICENSE_KEY in your environment, or drop sky_tracker.lic
    next to this script before running.
"""

import sys
import cv2
import sky_tracker

ZOOM_H   = 160   # height of the zoom inset in the bottom-right corner
ZOOM_PAD = 10    # margin from the edge


def draw_zoom(frame, raw, bx, by, bw, bh):
    """Paste a clean zoom crop of the target bbox into the bottom-right corner."""
    h, w = frame.shape[:2]
    x1, y1 = max(0, int(bx)), max(0, int(by))
    x2, y2 = min(w, int(bx + bw)), min(h, int(by + bh))
    if x2 <= x1 or y2 <= y1:
        return frame
    crop = raw[y1:y2, x1:x2]
    zoom_w = max(1, int(ZOOM_H * (x2 - x1) / (y2 - y1)))
    zoom = cv2.resize(crop, (zoom_w, ZOOM_H))
    cv2.rectangle(zoom, (0, 0), (zoom_w - 1, ZOOM_H - 1), (0, 255, 255), 2)
    ox = w - zoom_w - ZOOM_PAD
    oy = h - ZOOM_H - ZOOM_PAD
    frame[oy:oy + ZOOM_H, ox:ox + zoom_w] = zoom
    return frame


source = sys.argv[1] if len(sys.argv) > 1 else "video.mp4"

cap = cv2.VideoCapture(source)
ok, frame = cap.read()
if not ok:
    raise RuntimeError(f"Cannot open {source}")

fps = cap.get(cv2.CAP_PROP_FPS) or 30
fh, fw = frame.shape[:2]

# Draw a box around the target, then press Enter to lock
bbox = cv2.selectROI("Select target — press Enter to confirm", frame, fromCenter=False)
cv2.destroyAllWindows()

tracker = sky_tracker.Tracker("pi4-target")
tracker.lock(frame, (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])))

out_path = source.rsplit(".", 1)[0] + "_tracked.mp4"
writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (fw, fh))

frame_count = 0
while cap.isOpened():
    ok, frame = cap.read()
    if not ok:
        break
    result = tracker.update(frame)
    out = result.annotate()
    if not result.lost:
        out = draw_zoom(out, frame, result.bbox_x, result.bbox_y, result.bbox_w, result.bbox_h)
    writer.write(out)
    frame_count += 1

cap.release()
writer.release()
print(f"Tracked {frame_count} frames → {out_path}")
