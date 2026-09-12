#!/usr/bin/env python3
"""Build production inference artifacts for frozen HEAD4_V291_COMP7 downstream models.

This script is intentionally historical-only.  It may FIT only on rows dated
<= 2026-06-30, and it first reproduces the archived June walk-forward predictions
for the exact frozen research lineages:

* POST: v250 LogisticRegression(C=.35)
* ENV_ENTRY: v264 LogisticRegression(C=.18)
* SECOND: v279/v282 PLAYER_START listwise, L2=10
* conditional THIRD: v282 COND_BASE listwise, L2=.3

If the current repository/raw historical sources no longer reproduce the archived
June predictions within tight tolerances, artifact freezing fails closed.  This
protects v291 from silently changing because an upstream historical source was
revised after the research artifacts were produced.

No July/August/September outcomes are read.  No v96 score/rank/order is used in
any frozen production model.  The output artifact contains only inference state
(imputer/scaler/model coefficients and feature order), never training rows.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from scipy.special import logsumexp

from backtest import rows, i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250
import analyze_v264_4head_feature_exhaustive as v264
import analyze_v270_4head_win_feature_importance as v270
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "artifacts" / "head4_v291_downstream_20260630.json"
REPORT = ROOT / "artifacts" / "head4_v291_downstream_parity_20260630.json"
CUTOFF = date(2026, 6, 30)
JUNE_START = pd.Timestamp("2026-06-01")
JULY_START = pd.Timestamp("2026-07-01")
POST_COLS = [
    "legacy_score4", "racer4", "hist_st_edge_4v3", "wall3_weak",
    "inner12_resistance", "motor4_2ren", "motor4_hist", "turnfoot4_prior",
    "past_win4", "ex_st_rank4", "ex_st_4", "ex_st_edge_4v3",
    "orig_straight4", "orig_lap4", "orig_turn4", "tilt4",
]
TOL_POST = 1e-10
TOL_ENV = 1e-10
TOL_LISTWISE = 2e-8


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def finite_list(a: Iterable[float]):
    out = []
    for x in a:
        v = float(x)
        if not np.isfinite(v):
            raise RuntimeError("non-finite model state")
        out.append(v)
    return out


def build_v250_frame() -> pd.DataFrame:
    """Recreate v250 feature rows through the frozen 2026-06-30 cutoff."""
    start = v250.START
    preload = v250.PRELOAD_START_V250
    cache: Dict = {}
    hist = defaultdict(list)
    seen = set()
    d = preload
    while d < start:
        ingest_motor(hist, seen, d)
        if d >= start - timedelta(days=12):
            ingest_prior_day_preview(cache, d)
        d += timedelta(days=1)

    out = []
    while d <= CUTOFF:
        ymd = d.strftime("%Y/%m/%d")
        tkz = v250.by_code(f"data/previews/tkz/{ymd}.csv")
        stt = v250.by_code(f"data/previews/stt/{ymd}.csv")
        orig = v250.by_code(f"data/previews/original_exhibition/{ymd}.csv")
        frozen = []
        for r, x, s4, _s5, _dc in process_features(d, cache, hist):
            code = str(r["レースコード"]).zfill(12)
            z = {"date": str(d), "race_code": code}
            z.update(v250.pre_features(x, s4))
            z.update(v250.post_features(code, tkz, stt, orig))
            frozen.append(z)
        result = {str(r["レースコード"]).zfill(12): r for r in rows(f"data/results/realtime/{ymd}.csv")}
        for z in frozen:
            z["y4head"] = int(i(result.get(z["race_code"], {}).get("1着_艇番")) == 4)
            out.append(z)
        ingest_prior_day_preview(cache, d)
        ingest_motor(hist, seen, d)
        d += timedelta(days=1)
    q = pd.DataFrame(out)
    q["_date"] = pd.to_datetime(q.date)
    return q


def serialize_sklearn_logistic(model, features):
    prep = model.named_steps["p"] if "p" in model.named_steps else None
    if prep is not None:
        num_pipe = prep.named_transformers_["n"]
        imp = num_pipe.named_steps["i"]
        sc = num_pipe.named_steps["s"]
        lr = model.named_steps["m"]
    else:
        imp = model.named_steps["imp"]
        sc = model.named_steps["sc"]
        lr = model.named_steps["lr"]
    return {
        "kind": "standardized_logistic",
        "features": list(features),
        "imputer_median": finite_list(imp.statistics_),
        "scaler_mean": finite_list(sc.mean_),
        "scaler_scale": finite_list(sc.scale_),
        "coef": finite_list(lr.coef_[0]),
        "intercept": float(lr.intercept_[0]),
    }


def serialize_listwise(model, family: str, l2: float):
    return {
        "kind": "standardized_listwise_linear",
        "family": family,
        "l2": float(l2),
        "features": list(model.features),
        "imputer_median": finite_list(model.imp.statistics_),
        "scaler_mean": finite_list(model.sc.mean_),
        "scaler_scale": finite_list(model.sc.scale_),
        "beta": finite_list(model.beta),
    }


def max_abs_join(a: pd.DataFrame, b: pd.DataFrame, value_a: str, value_b: str) -> tuple[int, float]:
    z = a[["race_code", value_a]].copy()
    z["race_code"] = z.race_code.astype(str).str.zfill(12)
    y = b[["race_code", value_b]].copy()
    y["race_code"] = y.race_code.astype(str).str.zfill(12)
    m = z.merge(y, on="race_code", how="inner")
    if len(m) != len(z) or len(m) != len(y):
        raise RuntimeError(f"parity row mismatch {len(z)} vs {len(y)} joined={len(m)}")
    d = np.abs(pd.to_numeric(m[value_a]) - pd.to_numeric(m[value_b]))
    return len(m), float(d.max() if len(d) else 0.0)


def post_stage(frame: pd.DataFrame):
    tr_june = frame[frame._date < JUNE_START].copy()
    te_june = frame[(frame._date >= JUNE_START) & (frame._date < JULY_START)].copy()
    mj = v250.make_model(POST_COLS)
    mj.fit(tr_june[POST_COLS], tr_june.y4head.astype(int))
    pred = te_june[["race_code"]].copy()
    pred["pred"] = mj.predict_proba(te_june[POST_COLS])[:, 1]
    ref = pd.read_csv(ROOT / "analysis_v250_4head_rebuild_baseline.csv", dtype={"race_code": str})
    ref = ref[(ref.month == "2026-06") & (ref.variant == "POST")][["race_code", "p4head"]]
    n, err = max_abs_join(pred, ref, "pred", "p4head")
    if err > TOL_POST:
        raise RuntimeError(f"POST June parity failed max_abs={err:.12g}")

    final = v250.make_model(POST_COLS)
    final.fit(frame[POST_COLS], frame.y4head.astype(int))
    return serialize_sklearn_logistic(final, POST_COLS), {"rows": n, "max_abs": err, "tol": TOL_POST}


def env_stage():
    d, _groups, _fs = v270.prepare()
    d = d[d._date < JULY_START].copy()
    d["y4"] = pd.to_numeric(d.y4).astype(int)
    env0 = v264.families(d)["ENV_ENTRY"]

    tr_june = d[d._date < JUNE_START].copy()
    te_june = d[(d._date >= JUNE_START) & (d._date < JULY_START)].copy()
    use_june = [c for c in env0 if v264.goodcol(tr_june, c, .55)]
    mj = v264.lr_model()
    mj.fit(tr_june[use_june].apply(v264.num), tr_june.y4)
    pred = te_june[["race_code"]].copy()
    pred["pred"] = mj.predict_proba(te_june[use_june].apply(v264.num))[:, 1]
    ref = pd.read_csv(ROOT / "analysis_v264_4head_feature_exhaustive.csv", dtype={"race_code": str})
    ref = ref[(ref.month == "2026-06") & (ref.variant == "ENV_ENTRY")][["race_code", "p"]]
    n, err = max_abs_join(pred, ref, "pred", "p")
    if err > TOL_ENV:
        raise RuntimeError(f"ENV_ENTRY June parity failed max_abs={err:.12g}")

    use_final = [c for c in env0 if v264.goodcol(d, c, .55)]
    final = v264.lr_model()
    final.fit(d[use_final].apply(v264.num), d.y4)
    state = serialize_sklearn_logistic(final, use_final)
    state["family"] = "ENV_ENTRY"
    state["C"] = 0.18
    return state, {"rows": n, "max_abs": err, "tol": TOL_ENV, "june_features": len(use_june), "final_features": len(use_final)}


def _p2_frame(z: pd.DataFrame, model) -> pd.DataFrame:
    te = z.copy()
    te["s2"] = model.score(te)
    rec = []
    for code, g in te.groupby("race_code"):
        if len(g) != 5:
            continue
        p = v279.probs_within_race(g, "s2")
        r = {"race_code": str(code).zfill(12)}
        for b in v279.BOATS:
            r[f"p2_{b}"] = p[b]
        rec.append(r)
    return pd.DataFrame(rec)


def _cond_frame(pairs: pd.DataFrame, model) -> pd.DataFrame:
    te = pairs.copy()
    te["sc"] = model.score(te)
    rec = []
    for code, g in te.groupby("race_code"):
        r = {"race_code": str(code).zfill(12)}
        for s, gs in g.groupby("second_boat"):
            ss = gs.sc.to_numpy(float)
            pp = np.exp(ss - logsumexp(ss))
            for t, p in zip(gs.third_boat.astype(int), pp):
                r[f"c_{int(s)}_{int(t)}"] = float(p)
        rec.append(r)
    return pd.DataFrame(rec)


def opponent_stage():
    z, base = v282.prep()
    pairs, fams = v282.make_pairs(z, base)

    # June parity: exactly the monthly walk-forward state used by v282.
    tr2 = z[z.month < "2026-06"].copy()
    te2 = z[z.month == "2026-06"].copy()
    use2 = v279.good_features(tr2, base[v282.SECOND_FAMILY])
    m2j = v279.ListwiseSoftmax(v282.SECOND_L2).fit(tr2, use2, "y2")
    p2 = _p2_frame(te2, m2j)

    tr3 = pairs[(pairs.month < "2026-06") & (pairs.train_group == 1)].copy()
    te3 = pairs[pairs.month == "2026-06"].copy()
    use3 = v282.good(tr3, fams["COND_BASE"])
    m3j = v282.ListwiseN(0.3).fit(tr3, use3)
    pc = _cond_frame(te3, m3j)

    ref = pd.read_csv(ROOT / "analysis_v282_4head_conditional_third.csv", dtype={"race_code": str})
    ref = ref[ref.month == "2026-06"].copy()
    p2_ref = []
    c_ref = []
    for _, r in ref.iterrows():
        a = {"race_code": str(r.race_code).zfill(12)}
        for b, v in v282.parse_p2(r.p2).items():
            a[f"p2_{b}"] = v
        p2_ref.append(a)
        a = {"race_code": str(r.race_code).zfill(12)}
        for (s, t), v in v282.parse_cond(r.cond).items():
            a[f"c_{s}_{t}"] = v
        c_ref.append(a)
    p2r = pd.DataFrame(p2_ref)
    pcr = pd.DataFrame(c_ref)

    def wide_err(a: pd.DataFrame, b: pd.DataFrame):
        m = a.merge(b, on="race_code", suffixes=("_a", "_b"), how="inner")
        if len(m) != len(a) or len(m) != len(b):
            raise RuntimeError(f"opponent parity row mismatch {len(a)} vs {len(b)} joined={len(m)}")
        errs = []
        for c in a.columns:
            if c == "race_code":
                continue
            errs.extend(np.abs(pd.to_numeric(m[c + "_a"]) - pd.to_numeric(m[c + "_b"])).tolist())
        return len(m), float(max(errs) if errs else 0.0)

    n2, e2 = wide_err(p2, p2r)
    n3, e3 = wide_err(pc, pcr)
    if e2 > TOL_LISTWISE:
        raise RuntimeError(f"v283 SECOND June parity failed max_abs={e2:.12g}")
    if e3 > TOL_LISTWISE:
        raise RuntimeError(f"v283 conditional THIRD June parity failed max_abs={e3:.12g}")

    # Final <= Jun states.  These are the only listwise states production loads.
    use2f = v279.good_features(z, base[v282.SECOND_FAMILY])
    m2 = v279.ListwiseSoftmax(v282.SECOND_L2).fit(z, use2f, "y2")
    tr3f = pairs[pairs.train_group == 1].copy()
    use3f = v282.good(tr3f, fams["COND_BASE"])
    m3 = v282.ListwiseN(0.3).fit(tr3f, use3f)
    s2 = serialize_listwise(m2, v282.SECOND_FAMILY, v282.SECOND_L2)
    s3 = serialize_listwise(m3, "COND_BASE", 0.3)
    return s2, s3, {
        "second_rows": n2, "second_max_abs": e2,
        "conditional_rows": n3, "conditional_max_abs": e3,
        "tol": TOL_LISTWISE,
        "second_june_features": len(use2), "second_final_features": len(use2f),
        "conditional_june_features": len(use3), "conditional_final_features": len(use3f),
    }


def main():
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "policy": "HEAD4_V291_COMP7",
        "cutoff": str(CUTOFF),
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "v96_production_signal_used": False,
        "status": "STARTED",
    }
    try:
        frame = build_v250_frame()
        post, rpost = post_stage(frame)
        env, renv = env_stage()
        second, third, ropp = opponent_stage()
        report.update({"POST": rpost, "ENV_ENTRY": renv, "v283": ropp, "status": "PASS"})
        artifact = {
            "schema": "head4_v291_downstream_artifact_v1",
            "policy": "HEAD4_V291_COMP7",
            "frozen_training_cutoff": str(CUTOFF),
            "generated_by": "freeze_4head_v291_downstream_artifacts.py",
            "repository_sha": os.environ.get("GITHUB_SHA", "unknown"),
            "production_inference_only": True,
            "jul_aug_labels_used": False,
            "september_labels_used": False,
            "v96_production_signal_used": False,
            "POST": post,
            "ENV_ENTRY": env,
            "v283_SECOND": second,
            "v283_COND_THIRD": third,
            "v283_pair_policy": {"mode": "TOP2XTOP2", "alpha2": 0.60, "top_n": 4},
            "thresholds": {"PRE": 0.28, "POST": 0.25, "ENV_ENTRY": 0.224790, "COMPOSITE": 7.0},
            "parity": report,
        }
        ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact_sha256"] = sha256_file(ARTIFACT)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as e:
        report.update({"status": "BLOCKED", "error": str(e)})
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        raise


if __name__ == "__main__":
    main()
