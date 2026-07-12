# Python README and Examples Design

## Goal

Update the public SDK entry point and Python examples for Sky Tracker `v0.1.12`.

## Scope

Change only `README.md` and files under `examples/`, apart from this design and
its implementation plan. Do not edit the longer documents under `docs/` or any
package/runtime code.

## README

The README will explain that Sky Tracker follows caller-selected targets rather
than detecting arbitrary objects. It will show installation, licence setup,
single-target and multi-target quick starts, the three canonical profiles
(`default`, `correlation`, and `adaptive`), and links to each Python example.
Claims will remain practical and avoid unverified performance numbers.

## Examples

- `track_video.py`: interactive single-target selection, annotated MP4 output,
  profile selection, start-time support, and clean argument validation.
- `track_multi_video.py`: interactive selection of two or more targets using
  `MultiTracker`, stable target IDs, ownership-aware interaction state, and
  annotated MP4 output.
- `track_from_bbox.py`: non-interactive/headless tracking from an `x,y,w,h`
  argument, with optional annotated video and CSV telemetry.
- `machine_id.py`: print the machine ID required for a machine-locked licence.

Every script will use the installed `sky_tracker` package directly, accept
`--help`, return a non-zero status for invalid input, release OpenCV resources,
and use deterministic video `dt` values derived from source FPS.

## Verification

Compile all Python examples with `py_compile`, run each `--help` path, check the
README links and deprecated profile-name scan, and inspect the final Git diff.
