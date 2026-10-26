#!/usr/bin/env python3
"""Research-only, fail-closed v351 PRE shadow on contemporaneous input snapshots.

This is NOT the full v351 POST operation and never modifies a live scheduler.
It uses the original GitHub v323 HEAD + v317/v318 PRE opponent models ONLY,
with a historical train snapshot strictly preceding the target and a source
manifest showing when files were obtained (minimum 3 minutes to deadline).
A mere current/day-archive CSV with no timestamp does NOT meet the contract.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,math,subprocess,sys
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

JST=ZoneInfo("Asia/Tokyo")
KIND_REQUIRED=("race_cards","official_tkz","official_stt",
               "official_sui","boaters_original_exhibition")
RESEARCH_ONLY=True

def parse_jst(s):
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("offset-aware JST timestamp required")
    if dt.utcoffset()!=timedelta(hours=9):
        raise ValueError("timestamp must be explicitly +09:00")
    return dt.astimezone(JST)

def sha_file(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()

def check_history(path,target):
    target_day=target.isoformat()
    target_month=target_day[:7]
    months=set()
    seen=0
    latest=""
    opener=gzip.open if str(path).endswith(".gz") else open
    with opener(path,"rt",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            seen+=1
            day=str(r.get("date") or "").strip()
            code=str(r.get("race_code") or "").zfill(12)
            if not day and code.isdigit() and len(code)==12:
                day=f"{code[:4]}-{code[4:6]}-{code[6:8]}"
            if not day:
                raise ValueError("history lacks a verifiable row date")
            day=date.fromisoformat(day).isoformat()
            mon=str(r.get("month") or day[:7])
            if day>=target_day or mon>=target_month:
                raise ValueError("history contains target/future date or same/future month")
            if day[:7]!=mon:
                raise ValueError("history month/date mismatch")
            months.add(mon)
            latest=max(latest,day)
    if seen<1000:
        raise ValueError("history too small for production-profile fold")
    return {"records":seen,"latest_training_date":latest,
            "months":sorted(months),"sha256":sha_file(path)}

def validate_race_manifest(race,target,root,slack_min=3):
    code=str(race.get("race_code") or "")
    if len(code)!=12 or not code.isdigit() or code[:8]!=target.strftime("%Y%m%d"):
        raise ValueError("race code/date invalid")
    deadline=parse_jst(str(race["deadline_jst"]))
    if deadline.date()!=target:
        raise ValueError("deadline date invalid")
    cutoff=deadline-timedelta(minutes=slack_min)
    data=race.get("sources")
    if not isinstance(data,dict):
        raise ValueError("source manifest missing")
    issues=[]
    checked={}
    for k in KIND_REQUIRED:
        item=data.get(k)
        if not isinstance(item,dict):
            issues.append(f"{k}:missing")
            continue
        try:
            observed=parse_jst(str(item["observed_at_jst"]))
            if observed.date()!=target:
                raise ValueError("observed-date differs")
            if observed>cutoff:
                raise ValueError("captured after deadline-3min")
            relative=Path(str(item["file"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("snapshot outside evidence root")
            path=Path(root)/relative
            if not path.is_file():
                raise ValueError("snapshot missing")
            # Reject traversal beyond the evidence-root.
            path.resolve().relative_to(Path(root).resolve())
            expected=str(item["sha256"]).lower()
            got=sha_file(path)
            if expected!=got:
                raise ValueError("snapshot sha256 drift")
            checked[k]={"observed_at_jst":observed.isoformat(),
                        "sha256":got}
        except Exception as e:
            issues.append(f"{k}:{e}")
    return {"race_code":code,"cutoff_jst":cutoff.isoformat(),
            "observed_sources":checked,"issues":issues,
            "ready":not issues}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",required=True)
    ap.add_argument("--cards",required=True,type=Path)
    ap.add_argument("--github-source",required=True,type=Path)
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--head-history",required=True,type=Path)
    ap.add_argument("--opponent-history",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    target=date.fromisoformat(a.date)
    original_manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    if original_manifest.get("target_date")!=a.date:
        raise ValueError("target manifest date mismatch")
    items=original_manifest.get("races")
    if not isinstance(items,list) or not items:
        raise ValueError("empty races")
    if len({r.get("race_code") for r in items})!=len(items):
        raise ValueError("duplicate race manifest")
    hist_head=check_history(a.head_history,target)
    hist_opp=check_history(a.opponent_history,target)
    observed=[validate_race_manifest(r,target,a.manifest.parent) for r in items]
    ready={r["race_code"] for r in observed if r["ready"]}
    # Score the exact immutable card bytes certified by the capture manifest:
    # a later-downloaded card file cannot silently replace the input.
    card_hash=sha_file(a.cards)
    for r in items:
        if r["race_code"] in ready:
            if str(r["sources"]["race_cards"]["sha256"]).lower()!=card_hash:
                raise ValueError("scored cards file differs from certified pre-cutoff snapshot")
    with a.cards.open(encoding="utf-8-sig",newline="") as f:
        cards=list(csv.DictReader(f))
    selected=[r for r in cards
              if str(r.get("レースコード","")).zfill(12) in ready]
    if len(selected)!=len(ready) or len({str(r["レースコード"]).zfill(12) for r in selected})!=len(selected):
        raise ValueError("pre-card rows do not exactly match eligible source manifests")
    # Crucial: original model is imported only after entire as-of preflight.
    # No target date results, payout or closed odds are fetched.
    result={"research_only":True,"not_a_bet_recommendation":True,
        "not_full_original_v351_post":True,"target_date":a.date,
        "manifest_sha256":sha_file(a.manifest),
        "history_head":hist_head,"history_opponent":hist_opp,
        "races":observed,"ready_R":len(ready),
        "blocked_R":len(observed)-len(ready),
        "odds_used":False,"payouts_used":False,"results_used_for_prediction":False}
    if selected:
        source_dir=a.github_source.resolve()
        if not (source_dir/"run_v323_1head_frozen_live_adapter.py").is_file():
            raise ValueError("pinned original GitHub source unavailable")
        rev=subprocess.run(["git","-C",str(source_dir),"rev-parse","HEAD"],
            capture_output=True,text=True,check=True).stdout.strip()
        if rev!="9fdd307c5a2207adb46a68ff406fbf9b292c28d1":
            raise ValueError("GitHub original v351 source SHA mismatch")
        sys.path.insert(0,str(source_dir))
        import run_v323_1head_frozen_live_adapter as gh
        import pandas as pd
        cur=gh.current_static(selected,target)
        cur,_,_=gh.build_current_features(cur)
        head=gh.head_score(cur,.790,history_path=a.head_history)
        scored,tickets=gh.opponent_score(cur,head,history_path=a.opponent_history)
        res=[]
        for _,r in scored.iterrows():
            code=str(r["race_code"]).zfill(12)
            res.append({"race_code":code,
                "p_head":float(r["p_head"]),
                "opp_mass":float(r["opp_mass"]),
                "original_GH_v323_selected_PRE":bool(int(r["selected"])),
                "PRE_tickets":tickets.get(code,[]),
                "POST_status":"NOT_IMPLEMENTED",
                "bet_ready":False})
        result["GH_FROZEN_PRE_2026_AUG_HISTORY"]=res
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("GH351_ASOF_SHADOW_RESEARCH",json.dumps(
        {"date":a.date,"ready":result["ready_R"],"blocked":result["blocked_R"],
         "head_train_through":hist_head["latest_training_date"],
         "opp_train_through":hist_opp["latest_training_date"],
         "note":"GH v323 PRE only; not v351 POST; no LIVE eligibility"},
        ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
