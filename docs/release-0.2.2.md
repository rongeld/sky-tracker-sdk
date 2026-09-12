# Sky Tracker 0.2.2

This release fixes Python wheel builds for Linux x86_64 and ARM64. It also
includes the macOS build and tracking portability fixes from
[0.2.1](release-0.2.1.md).

## Fixes

- Linux wheels build against pinned OpenCV 4.12.0. The previous build used the
  manylinux container's OpenCV 3.4.6 package, which the SDK does not support.
- Wheels include the required OpenCV libraries and their license notices.
  The build retains the existing manylinux glibc 2.28 baseline.

## Upgrading

No tracker settings, public APIs or CSV columns changed from 0.2.1.
Update the Node package together with the 0.2.2 CLI runtime; the npm package
invokes an external executable and does not update it automatically.

When upgrading from 0.1.12, see the
[0.2.0 migration guide](release-0.2.0.md) for profile changes and the `legacy`
compatibility option.
