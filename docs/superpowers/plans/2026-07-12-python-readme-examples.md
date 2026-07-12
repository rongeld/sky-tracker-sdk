# Python README and Examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a concise `v0.1.12` README and four runnable Python examples for the installed Sky Tracker SDK.

**Architecture:** Keep each example self-contained so customers can copy one file without importing repository helpers. The README is the routing layer: it explains selected-target tracking, introduces the three canonical profiles, and links users to the example matching their workflow.

**Tech Stack:** Python 3.10+, OpenCV Python, `sky-tracker-sdk`, Markdown

## Global Constraints

- Modify only `README.md`, `examples/*.py`, and this implementation-plan file.
- Use only the canonical profiles `default`, `correlation`, and `adaptive`.
- Do not claim unverified FPS or accuracy numbers.
- All video examples derive `dt` from source FPS and release OpenCV resources.
- Every script supports `--help` without requiring a video or valid licence.

---

### Task 1: Establish failing public-example checks

**Files:**
- Test: `README.md`
- Test: `examples/track_video.py`
- Test: `examples/track_multi_video.py`
- Test: `examples/track_from_bbox.py`
- Test: `examples/machine_id.py`

**Interfaces:**
- Consumes: repository files and Python's compiler
- Produces: a RED baseline proving the missing/outdated examples are detected

- [ ] **Step 1: Run the missing-example syntax check**

```powershell
python -m py_compile examples\track_video.py examples\track_multi_video.py examples\track_from_bbox.py examples\machine_id.py
```

Expected: FAIL because three requested example files do not exist.

- [ ] **Step 2: Run the deprecated-profile check**

```powershell
rg -n "pi4-target|birds|missile" README.md examples
```

Expected: matches in `examples/track_video.py`, proving the public example is outdated.

### Task 2: Implement the four Python workflows

**Files:**
- Modify: `examples/track_video.py`
- Create: `examples/track_multi_video.py`
- Create: `examples/track_from_bbox.py`
- Create: `examples/machine_id.py`

**Interfaces:**
- Consumes: installed `cv2` and `sky_tracker` modules
- Produces: CLI entry points with `main() -> int` and `argparse` help

- [ ] **Step 1: Rewrite interactive single-target tracking**

Add `--profile`, `--start-seconds`, and `--output`; validate the selected ROI;
initialize `sky_tracker.Tracker`; draw the SDK annotation and zoom inset; release
capture, writer, and windows in `finally`-equivalent cleanup.

- [ ] **Step 2: Add interactive multi-target tracking**

Collect ROIs until the user cancels after at least two selections; initialize
`sky_tracker.MultiTracker`; draw stable target IDs and interaction/suppression
state; accept the same profile/start/output arguments.

- [ ] **Step 3: Add headless bbox tracking with CSV telemetry**

Parse `--bbox X,Y,W,H`; accept `--csv` and optional `--output`; write frame,
state, center, bbox, confidence, speed, reason, and `prediction_only` fields.

- [ ] **Step 4: Add the machine-ID helper**

Print `sky_tracker.get_machine_id()` and a one-line instruction to provide it
when requesting a machine-locked licence.

- [ ] **Step 5: Verify GREEN for syntax and help**

```powershell
python -m py_compile examples\*.py
python examples\track_video.py --help
python examples\track_multi_video.py --help
python examples\track_from_bbox.py --help
python examples\machine_id.py --help
```

Expected: all commands exit 0.

### Task 3: Rewrite the README as the SDK entry point

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the four example paths and the `v0.1.12` Python API
- Produces: install, licence, quick-start, profiles, multi-target, and examples guidance

- [ ] **Step 1: Replace duplicated and outdated sections**

Explain selected-target tracking, Python installation, licence token/file setup,
single and multi API snippets, and the profile trade-offs.

- [ ] **Step 2: Add an example index with exact commands**

Link all four scripts and show copyable invocations for interactive, multi,
headless, and machine-ID workflows.

- [ ] **Step 3: Run documentation checks**

```powershell
rg -n "pi4-target|birds|missile" README.md examples
rg -n "track_video.py|track_multi_video.py|track_from_bbox.py|machine_id.py" README.md
git diff --check
```

Expected: the deprecated scan has no matches, all four paths are present, and
`git diff --check` exits 0.

### Task 4: Final verification and commit

**Files:**
- Verify: `README.md`
- Verify: `examples/*.py`

**Interfaces:**
- Produces: a clean, reviewable documentation/examples commit

- [ ] **Step 1: Run the complete verification matrix**

Repeat Python compilation, all four `--help` commands, README link/profile scans,
and inspect `git diff --stat` plus `git diff --check`.

- [ ] **Step 2: Stage only approved files**

```powershell
git add README.md examples/*.py docs/superpowers/plans/2026-07-12-python-readme-examples.md
```

- [ ] **Step 3: Commit**

```powershell
git commit -m "docs: refresh Python README and examples"
```
