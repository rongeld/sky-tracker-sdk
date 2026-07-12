#!/usr/bin/env python3
"""Print the machine ID used to issue a machine-locked Sky Tracker licence."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print only the machine ID for scripts and command substitution",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import sky_tracker

    machine_id = sky_tracker.get_machine_id()
    if args.raw:
        print(machine_id)
    else:
        print(f"Machine ID: {machine_id}")
        print("Send this machine ID when requesting your Sky Tracker licence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
