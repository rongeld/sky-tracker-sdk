#!/usr/bin/env python3
"""Track one target from a supplied bbox and write CSV telemetry headlessly."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


PROFILES = ("default", "correlation", "adaptive")


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be x,y,w,h")
    try:
        x, y, width, height = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox values must be integers") from exc
    if x < 0 or y < 0:
        raise argparse.ArgumentTypeError("bbox coordinates must be non-negative")
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("bbox width and height must be positive")
    return x, y, width, height


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Input video file")
    parser.add_argument("--bbox", type=parse_bbox, required=True, help="Initial x,y,w,h")
    parser.add_argument("--profile", choices=PROFILES, default="default")
    parser.add_argument("--start-seconds", type=float, default=0.0)
    parser.add_argument(
        "--csv",
        type=Path,
        help="Telemetry CSV path (default: <video>_tracks.csv)",
    )
    parser.add_argument("--output", type=Path, help="Optional annotated MP4 path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.start_seconds < 0:
        print("--start-seconds must be non-negative", file=sys.stderr)
        return 2

    import cv2
    import sky_tracker

    capture = cv2.VideoCapture(str(args.video))
    video_writer = None
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

        tracker = sky_tracker.Tracker(args.profile)
        tracker.lock(frame, args.bbox)

        csv_path = args.csv or args.video.with_name(f"{args.video.stem}_tracks.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            frame_h, frame_w = frame.shape[:2]
            video_writer = cv2.VideoWriter(
                str(args.output),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (frame_w, frame_h),
            )
            if not video_writer.isOpened():
                print(f"cannot create output video: {args.output}", file=sys.stderr)
                return 2

        fields = (
            "frame",
            "target_id",
            "state",
            "center_x",
            "center_y",
            "bbox_x",
            "bbox_y",
            "bbox_w",
            "bbox_h",
            "confidence",
            "speed_px_s",
            "reason",
            "prediction_only",
        )
        dt = 1.0 / fps
        processed = 0
        current_frame = start_frame
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            telemetry = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            telemetry.writeheader()
            while True:
                result = tracker.update(frame, dt)
                telemetry.writerow(
                    {
                        "frame": current_frame,
                        "target_id": result.target_id,
                        "state": result.state,
                        "center_x": f"{result.cx:.3f}",
                        "center_y": f"{result.cy:.3f}",
                        "bbox_x": f"{result.bbox_x:.3f}",
                        "bbox_y": f"{result.bbox_y:.3f}",
                        "bbox_w": f"{result.bbox_w:.3f}",
                        "bbox_h": f"{result.bbox_h:.3f}",
                        "confidence": f"{result.confidence:.6f}",
                        "speed_px_s": f"{result.speed:.3f}",
                        "reason": result.reason,
                        "prediction_only": int(result.prediction_only),
                    }
                )
                if video_writer is not None:
                    video_writer.write(result.annotate())
                processed += 1

                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                current_frame += 1

        output_note = f" video={args.output}" if args.output else ""
        print(f"tracked {processed} frames -> csv={csv_path}{output_note}")
        return 0
    finally:
        capture.release()
        if video_writer is not None:
            video_writer.release()


if __name__ == "__main__":
    raise SystemExit(main())
