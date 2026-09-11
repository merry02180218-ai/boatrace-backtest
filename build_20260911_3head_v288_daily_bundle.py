#!/usr/bin/env python3
"""Build the 2026-09-11 3-head v288 PRE scan + frozen LIVE cache in one process.

Operational optimization only: the canonical augmented historical/current frame is
built once, then reused by the existing PRE scanner and cache builder.  Their
selection/model/threshold semantics are intentionally unchanged.
"""
from __future__ import annotations

import time

import scan_20260911_3head_v288_pre as pre
import build_20260911_3head_v288_live_cache as cache


def main() -> None:
    t0 = time.perf_counter()
    bundle = pre.build_augmented()
    build_seconds = time.perf_counter() - t0

    # Both existing entry points call pre.build_augmented().  Reuse the exact
    # same in-memory result so the expensive historical reconstruction happens
    # only once while preserving all downstream semantics.
    original = pre.build_augmented
    pre.build_augmented = lambda: bundle
    try:
        t1 = time.perf_counter()
        pre.main()
        pre_seconds = time.perf_counter() - t1

        t2 = time.perf_counter()
        cache.main()
        cache_seconds = time.perf_counter() - t2
    finally:
        pre.build_augmented = original

    total_seconds = time.perf_counter() - t0
    print(
        "V288_DAILY_BUNDLE_READY"
        f" build_augmented_seconds={build_seconds:.3f}"
        f" pre_after_build_seconds={pre_seconds:.3f}"
        f" cache_after_build_seconds={cache_seconds:.3f}"
        f" total_seconds={total_seconds:.3f}",
        flush=True,
    )


if __name__ == '__main__':
    main()
