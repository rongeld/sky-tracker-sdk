# Sky Tracker SDK — C++ Quickstart

Native C++ integration. The library is the tracker itself; the Python and Node
SDKs are bindings over this same code.

**Prerequisites**

- A C++17 compiler
- CMake 3.16 or later
- OpenCV 4.x with the `core`, `imgproc` and `video` modules
- Your evaluation licence key

---

The SDK version is 0.2.2. Existing profiles retain the tracking policy used by the CLI and Python SDK.

## 1. What you receive

```
include/sky_tracker/sdk.hpp        the entire public API
lib/libsky_tracker.a               the tracker
lib/cmake/sky_tracker/             CMake package config
```

`sdk.hpp` is the only header you include. It carries no OpenCV types, so your
application does not have to match the OpenCV build we compiled against at the
API level — though a static library still links against a specific OpenCV, so
tell us which one you use and we will build to match.

---

## 2. Report your machine ID

Licences are bound to the machine they run on. On the target unit:

```cpp
#include <sky_tracker/sdk.hpp>
#include <cstdio>

int main() {
    std::printf("%s\n", sky_tracker::sdk::machineId().c_str());
}
```

`machineId()` needs no licence, so this works before you have one. Send us the
32-character string and we will issue a licence for that unit.

The ID derives from the OS install identity. It changes if the machine is
reimaged and differs inside a container from the host — if either applies during
evaluation, tell us and we will issue an unbound licence instead.

---

## 3. Install your licence

Any one of these:

```bash
export SKY_TRACKER_LICENSE_KEY=<your-token>
export SKY_TRACKER_LICENSE_FILE=/path/to/sky_tracker.lic
```

…or place `sky_tracker.lic` next to your executable, in the working directory,
or at `~/.sky_tracker/licence`. Validation is fully offline — nothing contacts a
network at runtime.

Call `validateLicense()` at startup to fail fast with a clear message:

```cpp
try {
    const auto info = sky_tracker::sdk::validateLicense();
    std::printf("licensed to %s until %s\n",
                info.customer.c_str(), info.expiresAt.c_str());
} catch (const sky_tracker::sdk::Error& e) {
    std::fprintf(stderr, "licence: %s\n", e.what());
    return 1;
}
```

---

## 4. Build against it

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_app LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

find_package(sky_tracker REQUIRED)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE sky_tracker::sky_tracker)
```

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH=/path/to/sky-tracker
cmake --build build
```

---

## 5. Track a target

```cpp
#include <sky_tracker/sdk.hpp>

namespace st = sky_tracker::sdk;

st::Tracker tracker("default");

// Point at your capture buffer. No copy is taken for Gray8 or Bgr8.
st::FrameView frame;
frame.data   = capture.pixels();
frame.width  = capture.width();
frame.height = capture.height();
frame.stride = capture.rowBytes();   // 0 if rows are tightly packed
frame.format = st::PixelFormat::Bgr8;

// Acquire from an operator selection or your own detector.
tracker.lock(frame, st::Rect{x, y, w, h});

while (capture.grab()) {
    const st::TrackResult r = tracker.update(frame, dtSeconds);

    const float errorX = r.centerX - frame.width  / 2.0f;
    const float errorY = r.centerY - frame.height / 2.0f;
    panTilt.drive(errorX, errorY);
}
```

`update()` is synchronous and returns the measurement for that frame. There is
no internal buffering or worker thread to account for in your control loop.

### Driving a pan-tilt loop

`r.predictionOnly` is the field that matters most. When the target is briefly
occluded the tracker keeps extrapolating its motion model rather than dropping
the position, so you can keep slewing through the gap instead of stalling. The
estimate degrades the longer it persists — `r.misses` counts the consecutive
extrapolated frames, and a sensible controller reduces gain or holds after a
threshold you choose.

`r.state` is the other signal to key off: drive normally while it is
`Confirmed`, and treat `Lost` as a hold rather than a reason to recentre.

---

## 6. Profiles

Pass a profile name to the constructor:

| Profile | Use |
|---|---|
| `default` | Balanced starting point, grayscale-only, constrained-CPU policy |
| `correlation` | Correlation-led tracking of a selected object |
| `adaptive` | Correlation identity plus scheduled foreground box fitting |
| `legacy` | The v0.1.12 default policy |
| `correlation-quality` | Opt-in normalized correlation, appearance verification, fixed box size |
| `adaptive-quality` | Quality engine with adaptive foreground geometry |
| `fast-sky` | Fast targets against open sky |
| `birds` | Small erratic targets |
| `close-pass` | Targets that pass close to the camera and change scale sharply |
| `missile` | Small, fast, near-constant-heading targets |
| `scale-target` | Targets whose apparent size changes substantially |

`availableProfiles()` returns this list at runtime. Which one wins depends on
your camera and target mix — evaluate against your own footage.

---

## 7. Multiple targets

```cpp
st::MultiTracker multi("default");
multi.lock(frame, {st::Rect{...}, st::Rect{...}});

for (const st::TrackResult& r : multi.update(frame, dt)) {
    // r.targetId is stable across frames, including through close passes.
}
```

During an ambiguous close pass the tracker holds identity rather than guessing:
affected targets report `interacting`, and may report `suppressed` with the ID
that claimed the observation instead of jumping onto a neighbouring object.

---

## Scope

Sky Tracker is a **selected-target** tracker. Every target starts from a
bounding box you supply, from an operator selection or your own detector. It
does not perform automatic search and acquisition.

---

## Errors

Everything throws `sky_tracker::sdk::Error` (derived from `std::runtime_error`)
— invalid arguments, `update()` before `lock()`, and licence failures. Neither
tracker is thread-safe; serialise calls or give each thread its own instance.
