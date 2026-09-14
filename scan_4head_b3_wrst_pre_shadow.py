#!/usr/bin/env python3
"""Result-blind PRE scanner for frozen HEAD4_B3_WR_ST_SHADOW_V1."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from backtest import race_features
from backtest_v4 import add_features, score4v4
import analyze_4head_waku10_ablation_20260914 as feature_src
import scan_4head_v291_pre_live as state_src
from head4_b3_wrst_shadow_inference import load_artifact, score_pre, DEFAULT_ARTIFACT, POLICY

PRE_CUT = 0.28


def local_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    a = ap.parse_args()
    day = datetime.strptime(a.date, "%Y-%m-%d").date()
    day8 = day.strftime("%Y%m%d")
    inp = Path("current_input/v291") / day8
    cards_path, waku_path = inp / "race_cards.csv", inp / "waku10.csv"
    manifest_path = inp / "input_manifest.json"
    if not cards_path.exists() or not waku_path.exists() or not manifest_path.exists():
        raise RuntimeError(f"missing result-blind current inputs: {inp}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("result_blind") is not True or manifest.get("current_exhibition_used") is not False:
        raise RuntimeError("current PRE input manifest is not result-blind")

    # Reuse the already-audited causal state builder. Its label fit stops at 2026-06-30;
    # later dates only advance prior preview/motor state and do not fit or tune the model.
    _train_unused, cache, hist = state_src.training_and_state(day)
    art = load_artifact(a.artifact)
    cards = local_rows(cards_path)
    waku = {str(r.get("レースコード", "")).zfill(12): r for r in local_rows(waku_path)}
    rec = []
    pre_features = list(art["models"]["PRE"]["features"])
    for r in cards:
        code = str(r.get("レースコード", "")).zfill(12)
        x = add_features(race_features(r, waku.get(code, {})), r, cache, hist)
        s4 = score4v4(x)
        raw = feature_src.raw_features(x, s4)
        p = score_pre(raw, art)
        z = {
            "date": str(day),
            "race_code": code,
            "jcd": int(code[8:10]),
            "rno": int(code[10:12]),
            "venue": str(r.get("レース場コード", "")).zfill(2),
            "PRE": p,
            "pre_eligible": int(p >= PRE_CUT),
        }
        for k in pre_features:
            z[k] = raw.get(k)
        rec.append(z)
    q = pd.DataFrame(rec).sort_values(["PRE", "race_code"], ascending=[False, True]).reset_index(drop=True)
    outdir = Path("shadow_outputs/b3_wrst") / day8
    outdir.mkdir(parents=True, exist_ok=True)
    csvp = outdir / "pre_scan.csv"
    audp = outdir / "pre_scan_audit.json"
    q.to_csv(csvp, index=False)
    eligible = q[q.pre_eligible == 1]
    audit = {
        "policy": POLICY,
        "stage": "PRE_SHADOW_ONLY",
        "target_date": str(day),
        "generated_at_jst": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "result_blind_target_day": True,
        "result_or_payout_used": False,
        "production_modified": False,
        "pre_cut_inclusive": PRE_CUT,
        "training_label_cutoff": art["training_label_cutoff"],
        "jul_aug_labels_used": False,
        "september_labels_used_for_fit_or_selection": False,
        "current_exhibition_used": False,
        "pre_features": pre_features,
        "current_rows": int(len(q)),
        "eligible_rows": int(len(eligible)),
        "eligible_race_codes": eligible.race_code.tolist(),
        "cards_sha256": sha256(cards_path),
        "waku_sha256": sha256(waku_path),
        "input_manifest_sha256": sha256(manifest_path),
        "head_artifact_sha256": sha256(Path(a.artifact)),
    }
    audp.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
