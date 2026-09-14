#!/usr/bin/env python3
"""One-click current-day orchestration for HEAD4_B3_WR_ST_SHADOW_V1.

Research-shadow only. It validates causal sources, scores frozen POST, assembles the
immutable input bundle, and invokes the existing shadow runner. It never submits a
wager and never reads result/payout data.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

POLICY = "HEAD4_B3_WR_ST_SHADOW_V1"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--post-json", required=True)
    ap.add_argument("--env-json", required=True)
    ap.add_argument("--boats-json", required=True)
    ap.add_argument("--pre-scan", help="existing result-blind PRE scan CSV; generated if omitted")
    ap.add_argument("--work-dir")
    ap.add_argument("--audit", default="shadow_audit_4head_b3_wrst.jsonl")
    args = ap.parse_args()

    code = str(args.race_code).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise SystemExit("race_code must be 12 digits")
    day8, jcd, rno = code[:8], int(code[8:10]), int(code[10:12])
    day_iso = f"{day8[:4]}-{day8[4:6]}-{day8[6:8]}"
    work = Path(args.work_dir or f"shadow_outputs/b3_wrst/{day8}/current/{code}")
    norm = work / "normalized_sources"
    work.mkdir(parents=True, exist_ok=True)

    pre_scan = Path(args.pre_scan) if args.pre_scan else Path(
        f"shadow_outputs/b3_wrst/{day8}/pre_scan.csv"
    )
    if not args.pre_scan:
        run([sys.executable, "scan_4head_b3_wrst_pre_shadow.py", "--date", day_iso])
    if not pre_scan.exists():
        raise SystemExit(f"PRE scan unavailable: {pre_scan}")

    run([
        sys.executable, "validate_4head_b3_wrst_current_sources.py",
        "--post-json", args.post_json,
        "--env-json", args.env_json,
        "--boats-json", args.boats_json,
        "--race-code", code,
        "--deadline-jst", args.deadline_jst,
        "--out-dir", str(norm),
    ])

    head_scores = work / "head_scores.json"
    run([
        sys.executable, "score_4head_b3_wrst_post_shadow.py",
        "--pre-scan", str(pre_scan),
        "--race-code", code,
        "--post-json", str(norm / "post.json"),
        "--out", str(head_scores),
    ])

    bundle = work / "shadow_input.json"
    run([
        sys.executable, "assemble_4head_b3_wrst_shadow_input.py",
        "--head-scores", str(head_scores),
        "--env-primitives", str(norm / "env_primitives.json"),
        "--boats", str(norm / "boats.json"),
        "--source-manifest", str(norm / "source_manifest.json"),
        "--out", str(bundle),
    ])

    run([
        sys.executable, "run_4head_b3_wrst_shadow.py",
        "--input-json", str(bundle),
        "--date", day8,
        "--jcd", str(jcd),
        "--race", str(rno),
        "--deadline-jst", args.deadline_jst,
        "--audit", args.audit,
    ])

    print(json.dumps({
        "status": "SHADOW_PIPELINE_COMPLETED",
        "policy": POLICY,
        "race_code": code,
        "shadow_only": True,
        "production_action_taken": False,
        "result_or_payout_used": False,
        "work_dir": str(work),
        "bundle": str(bundle),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
