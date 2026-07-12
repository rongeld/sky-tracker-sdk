#!/usr/bin/env python3
"""Interactively select multiple targets and save an annotated tracking video."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROFILES = ("default", "correlation", "adaptive")
COLORS = (
    (0, 255, 255),
    (255, 180, 0),
    (0, 220, 100),
    (255, 80, 200),
    (100, 180, 255),
)


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
        help="Annotated MP4 path (default: <video>_multi_tracked.mp4)",
    )
    return parser.parse_args()


def select_targets(cv2, frame) -> list[tuple[int, int, int, int]]:
    bboxes: list[tuple[int, int, int, int]] = []
    print("Select each target in stable ID order. Press Esc when all targets are selected.")
    while True:
        title = f"Select target {len(bboxes) + 1} - Enter confirms, Esc finishes"
        roi = cv2.selectROI(title, frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(title)
        bbox = tuple(int(value) for value in roi)
        if bbox[2] <= 0 or bbox[3] <= 0:
            break
        bboxes.append(bbox)
        print(f"target {len(bboxes)}: {bbox}")
    return bboxes


def draw_result(cv2, frame, result) -> None:
    if result.lost and not result.prediction_only:
        return

    x, y, width, height = (int(value) for value in result.bbox())
    color = COLORS[(result.target_id - 1) % len(COLORS)]
    flags: list[str] = []
    if result.interacting:
        flags.append("interacting")
        color = (0, 200, 255)
    if result.suppressed:
        flags.append(f"suppressed-by-{result.suppressed_by_id}")
        color = (0, 128, 255)
    if result.prediction_only:
        flags.append("predicted")
        color = (255, 80, 200)

    cv2.rectangle(frame, (x, y), (x + width, y + height), color, 2)
    suffix = f" {' '.join(flags)}" if flags else ""
    label = f"T{result.target_id} {result.state}{suffix}"
    cv2.putText(
        frame,
        label,
        (x, max(18, y - 7)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        1,
        cv2.LINE_AA,
    )


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

        bboxes = select_targets(cv2, frame)
        if len(bboxes) < 2:
            print("multi-target tracking requires at least two selected targets", file=sys.stderr)
            return 2

        tracker = sky_tracker.MultiTracker(args.profile)
        tracker.lock(frame, bboxes)

        output = args.output or args.video.with_name(f"{args.video.stem}_multi_tracked.mp4")
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
            results = tracker.update(frame, dt)
            annotated = frame.copy()
            for result in results:
                draw_result(cv2, annotated, result)
            writer.write(annotated)
            processed += 1

            ok, frame = capture.read()
            if not ok or frame is None:
                break

        print(f"tracked {len(bboxes)} targets across {processed} frames -> {output}")
        return 0
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
