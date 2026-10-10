# Changelog

## v0.2.2 - 2026-09-12

- Fix Python wheel builds for Linux x86_64 and ARM64 against pinned OpenCV 4.12.0.
- Bundle required OpenCV libraries and license notices into manylinux wheels.
- Retain existing manylinux glibc 2.28 baseline.

## v0.2.1 - 2026-08-26

- Fix macOS builds and tracking differences between C++ toolchains.
- macOS CLI and Python wheel builds explicitly use OpenCV 4.
- Correlation initialization draws training offsets in fixed X/Y order for consistency across compilers.
- Fix small target search window clamp bounds on macOS.

## v0.2.0 - 2026-08-25

- Default profile updated to combine correlation identity tracking with scheduled foreground-box fitting and smoothed geometry.
- Automatic correlation search window sizing (64 px for tiny targets, 128 px through 80 px, 256 px above 80 px).
- Added `legacy` profile to retain v0.1.12 default behavior.
- MultiTracker with identity and bounding box ownership protection during close passes.
- Opt-in `correlation-quality` and `adaptive-quality` profiles.
- Native C++ SDK distribution and quickstart documentation.
- Standalone machine-ID utility and perpetual license support.

## v0.1.0 - 2026-05-08

- Initial evaluation release
- Python SDK: `pip install sky-tracker-sdk`
- Node.js SDK: `npm install @sky-tracker/node`
- Offline Ed25519 licence enforcement - no cloud dependency
- `.lic` file support: drop next to script, no env var needed
- Profiles: `default`, `birds`, `missile`, `pi4-target`
- CSV telemetry: `frame`, `state`, `cx`, `cy`, `confidence`, `speed`, `reason`
- Platforms: Windows x64 verified
