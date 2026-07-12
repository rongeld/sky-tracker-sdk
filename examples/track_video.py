#!/usr/bin/env python3
"""Interactively select one target and save an annotated tracking video."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROFILES = ("default", "correlation", "adaptive")
ZOOM_HEIGHT = 160
ZOOM_PADDING = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Input video file")
    parser.add_argument("--profile", choices=PROFILES, default="default")
    parser.add_argument(
        "--start-seconds",
        type=float,
        default=0.0,
        help="Start target selection at this timestamp (default: 0)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Annotated MP4 path (default: <video>_tracked.mp4)",
    )
    return parser.parse_args()


def draw_zoom(cv2, annotated, raw, bbox) -> None:
    """Draw a target crop in the bottom-right corner of the output frame."""
    bx, by, bw, bh = bbox
    frame_h, frame_w = raw.shape[:2]
    x1, y1 = max(0, int(bx)), max(0, int(by))
    x2, y2 = min(frame_w, int(bx + bw)), min(frame_h, int(by + bh))
    if x2 <= x1 or y2 <= y1:
        return

    crop = raw[y1:y2, x1:x2]
    zoom_width = max(1, int(ZOOM_HEIGHT * crop.shape[1] / crop.shape[0]))
    zoom_width = min(zoom_width, frame_w - 2 * ZOOM_PADDING)
    if zoom_width <= 0 or frame_h < ZOOM_HEIGHT + 2 * ZOOM_PADDING:
        return

    zoom = cv2.resize(crop, (zoom_width, ZOOM_HEIGHT))
    cv2.rectangle(zoom, (0, 0), (zoom_width - 1, ZOOM_HEIGHT - 1), (0, 255, 255), 2)
    output_x = frame_w - zoom_width - ZOOM_PADDING
    output_y = frame_h - ZOOM_HEIGHT - ZOOM_PADDING
    annotated[output_y : output_y + ZOOM_HEIGHT, output_x : output_x + zoom_width] = zoom


def main() -> int:
    args = parse_args()
    if args.start_seconds < 0:
        print("--start-seconds must be non-negative", file=sys.stderr)
        return 2

    import cv2
    import sky_tracker

    capture = cv2.VideoCapture(str(args.video))
    writer = None
    try:
        if not capture.isOpened():
            print(f"cannot open video: {args.video}", file=sys.stderr)
            return 2

        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = fps if fps and fps > 1.0 else 30.0
        start_frame = int(round(args.start_seconds * fps))
        if start_frame:
            capture.set(cv2.CAP_PROP_POS_FRAMES, float(start_frame))

        ok, frame = capture.read()
        if not ok or frame is None:
            print(f"cannot read video at {args.start_seconds:.3f}s", file=sys.stderr)
            return 2

        roi = cv2.selectROI(
            "Select target - Enter confirms, Esc cancels",
            frame,
            fromCenter=False,
            showCrosshair=True,
        )
        cv2.destroyAllWindows()
        bbox = tuple(int(value) for value in roi)
        if bbox[2] <= 0 or bbox[3] <= 0:
            print("target selection cancelled", file=sys.stderr)
            return 2

        tracker = sky_tracker.Tracker(args.profile)
        tracker.lock(frame, bbox)

        output = args.output or args.video.with_name(f"{args.video.stem}_tracked.mp4")
        output.parent.mkdir(parents=True, exist_ok=True)
        frame_h, frame_w = frame.shape[:2]
        writer = cv2.VideoWriter(
            str(output),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (frame_w, frame_h),
        )
        if not writer.isOpened():
            print(f"cannot create output video: {output}", file=sys.stderr)
            return 2

        dt = 1.0 / fps
        processed = 0
        while True:
            result = tracker.update(frame, dt)
            annotated = result.annotate()
            if not result.lost:
                draw_zoom(cv2, annotated, frame, result.bbox())
            writer.write(annotated)
            processed += 1

            ok, frame = capture.read()
            if not ok or frame is None:
                break

        print(f"tracked {processed} frames -> {output}")
        return 0
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
