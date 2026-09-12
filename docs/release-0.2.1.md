# Sky Tracker 0.2.1

This release includes the tracking and SDK updates from 0.2.0, plus fixes for
macOS builds and tracking differences between C++ toolchains.

## Fixes

- macOS CLI and Python wheel builds explicitly use OpenCV 4. CMake reports an
  unsupported OpenCV major version during configuration.
- Correlation initialization draws training offsets in a fixed X/Y order.
  This preserves the established Windows initialization and prevents compilers
  from swapping the coordinates when evaluating random-number draws.
- Small target search windows respect their configured limit, including zero.
  Previously, reversed clamp bounds could expand the window on macOS and prevent
  adaptive boxes from following rapid target growth.

## Upgrading

Python, Node and C++ APIs and tracker CSV columns are unchanged from 0.2.0.
Update the Node package together with the 0.2.1 CLI runtime; the npm package
invokes an external executable and does not update it automatically.

When upgrading from 0.1.12, `default` enables correlation-assisted tracking and
stable foreground boxes. Use `legacy` to retain the previous default settings.
The quality profiles remain opt-in. See the
[0.2.0 migration guide](release-0.2.0.md) for the full profile and SDK changes.
