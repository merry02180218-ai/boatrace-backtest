#!/usr/bin/env python3
"""Result-blind v23 diagnostic plus proposal-merge source attribution.

v23 established two distinct late failure loci under unchanged v21 behavior:
- Kiryu3 reaches _safe_state with non-empty fleet products that are rejected by
  the immutable reverse-motion corridor;
- the other audited samples can exhaust a frame before _expand_predecessor is
  called, which means feasibility is being lost earlier while proposal sources
  are merged around each predecessor.

v24 deliberately changes no tracking behavior.  It wraps v21._merge and records
where candidates came from (global immutable / predecessor-local immutable /
verified appearance bank), how many are inside the unchanged predecessor
reachability radius, how many are removed by the unchanged 8px merge dedup,
and which sources survive into the unchanged merged list.

No threshold, proposal source, score, beam width, geometry rule, motion rule or
race-specific behavior is changed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v21 as v21
import track_exhibition_boats_v23 as v23

MERGES = []
_ORIG_MERGE = v21._merge


def _center(item):
    return np.asarray(item[0], np.float32)


def _min_dist(opts, prev):
    if not opts:
        return None
    p = np.asarray(prev, np.float32)
    return round(min(float(np.linalg.norm(_center(x) - p)) for x in opts), 3)


def _merge_counted(global_opts, local_opts, bank_opts, prev_center, advance, keep):
    # Call the authoritative implementation first; diagnostics below are a
    # side-channel replay only and cannot alter the returned candidate list.
    out = _ORIG_MERGE(global_opts, local_opts, bank_opts,
                      prev_center, advance, keep)

    radius = 24.0 * max(1, int(advance))
    prev = np.asarray(prev_center, np.float32)
    raw = []
    for source_group, seq in (("local", local_opts), ("global", global_opts)):
        for c, s in seq:
            raw.append((_center((c,)), float(s), float(s), source_group))
    for item in bank_opts:
        c, imm, aux, _source = item
        raw.append((np.asarray(c, np.float32), float(imm), float(aux), "bank"))
    raw.sort(key=lambda z: (0.72 * z[1] + 0.28 * z[2]), reverse=True)

    counts = {
        "local": len(local_opts),
        "global": len(global_opts),
        "bank": len(bank_opts),
        "raw": len(raw),
        "radius_reject_local": 0,
        "radius_reject_global": 0,
        "radius_reject_bank": 0,
        "dedup_reject_local": 0,
        "dedup_reject_global": 0,
        "dedup_reject_bank": 0,
        "accepted_local": 0,
        "accepted_global": 0,
        "accepted_bank": 0,
        "capacity_skipped": 0,
    }
    pool = []
    for c, imm, aux, source_group in raw:
        if len(pool) >= max(1, int(keep)):
            counts["capacity_skipped"] += 1
            continue
        if float(np.linalg.norm(c - prev)) > radius:
            counts[f"radius_reject_{source_group}"] += 1
            continue
        if any(np.linalg.norm(c - q) < 8.0 for q in pool):
            counts[f"dedup_reject_{source_group}"] += 1
            continue
        pool.append(c)
        counts[f"accepted_{source_group}"] += 1

    MERGES.append({
        "advance": int(advance),
        "keep": int(keep),
        "radius": round(float(radius), 3),
        "prev_center": [round(float(prev[0]), 3), round(float(prev[1]), 3)],
        "input_counts": {"global": len(global_opts),
                         "local": len(local_opts),
                         "bank": len(bank_opts)},
        "min_distance": {"global": _min_dist(global_opts, prev),
                         "local": _min_dist(local_opts, prev),
                         "bank": _min_dist(bank_opts, prev)},
        "filter_counts": counts,
        "output_count": len(out),
        "diagnostic_replay_output_count": len(pool),
    })
    return out


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v24.json")


def _annotate(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v24-diagnostic"
    obj["method"] = "v24 result-blind proposal-merge source attribution diagnostic"
    obj["v24_diagnostic"] = {
        "merge_calls": MERGES,
        "merge_call_count": len(MERGES),
        "zero_output_merge_calls": sum(1 for x in MERGES if x["output_count"] == 0),
        "behavior_changed_from_v21": False,
        "quality_thresholds_relaxed": False,
        "purpose": "attribute pre-safe candidate loss to proposal source, predecessor reachability, merge dedup, or capacity",
    }
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def main():
    v21._merge = _merge_counted
    code = 0
    try:
        v23.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate(_out_path(sys.argv))
    print(json.dumps({
        "v24_merge_calls": len(MERGES),
        "v24_zero_output_merges": sum(1 for x in MERGES if x["output_count"] == 0),
    }, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
