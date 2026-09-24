#!/usr/bin/env python3
"""INNER12 novel-route research after excluding the existing 4HEAD production model.

Inputs:
- Stage-B factor rows built causally before same-day outcomes are opened.
- Exact 4HEAD PH5 LIVE walk-forward race_detail.csv.

Strict comparison universe:
- June-August 2026 only.
- Existing 4HEAD comparable rows are those present in race_detail.csv.
- Existing production_bet==1 rows are EXCLUDED.
- Rows absent from race_detail are reported as not-comparable and are not used
  for strict non-overlap rule discovery.

Selection policy:
- June = train/search.
- July = validation.
- August = report-only confirmation.
- September outcomes are never read here.
- August never chooses a feature, direction, threshold, category, or interaction.

Preferred-rule policy:
- Generic "boat4 is simply strong" rules are flagged.
- preferred_novel rankings remove generic-4-only rules so this does not just
  rediscover the existing 4HEAD concept.
"""
from __future__ import annotations

import json, math, os
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd

STAGEB = Path(os.environ.get("INNER12_STAGEB_ROWS", "/tmp/inner12_stageb_route_discovery_v1/factor_rows.csv"))
HEAD4 = Path(os.environ.get("HEAD4_RACE_DETAIL", "/tmp/head4_ph5_live_walkforward/race_detail.csv"))
OUT = Path(os.environ.get("INNER12_NOVEL_OUTDIR", "/tmp/inner12_novel_nonoverlap_v1"))
OUT.mkdir(parents=True, exist_ok=True)

TRAIN_MONTH="2026-06"
VAL_MONTH="2026-07"
CONF_MONTH="2026-08"
TARGETS=["route_3_family","route_4_family","route_5_family","route_outer_core","route_outer_wide"]

META_EXCLUDE={
    "winner","kimarite","route_target",
    "actual_st1","actual_st2","actual_st3","actual_st4",
    "dual_abs20","dual_vs3_03","inner_vs_outer03",
    *[f"route_{x}" for x in [
        "1_escape","3_makuri","3_makurisashi","4_makuri","4_makurisashi",
        "5_makuri","5_makurisashi","3_family","4_family","5_family","outer_core","outer_wide"
    ]]
}

def rate(df,label):
    if len(df)==0:return float("nan")
    return float(pd.to_numeric(df[label],errors="coerce").fillna(0).mean())

def summary(df,label):
    return {"R":int(len(df)),"H":int(pd.to_numeric(df[label],errors="coerce").fillna(0).sum()),"rate":rate(df,label)}

def is_generic4_strength(name:str)->bool:
    n=name.lower()
    if not ("b4" in n or "4minus" in n or "3minus4" in n):
        return False
    strength_tokens=("wr","local","motor2","motor3","waku_wr","past_win","全国勝率","当地勝率","連対率")
    st_shape_tokens=("st","display","orig","straight","turn","pexpo","pturn","pstraight","pred")
    return any(t in n for t in strength_tokens) and not any(t in n for t in st_shape_tokens)

def safe_num_features(df):
    bad_prefix=("route_","actual_","dual_")
    skip={"race_code","date","month","venue_name","winner","kimarite"}
    out=[]
    for c in df.columns:
        if c in skip or c in META_EXCLUDE or c.startswith("cat_") or c.startswith(bad_prefix):
            continue
        x=pd.to_numeric(df[c],errors="coerce")
        if x.notna().sum()>=40 and x.nunique(dropna=True)>=3:
            out.append(c)
    return out

def evaluate_numeric(df,label):
    tr=df[df.month.eq(TRAIN_MONTH)]
    va=df[df.month.eq(VAL_MONTH)]
    co=df[df.month.eq(CONF_MONTH)]
    bt,bv,bc=rate(tr,label),rate(va,label),rate(co,label)
    rows=[]
    for feat in safe_num_features(df):
        tv=pd.to_numeric(tr[feat],errors="coerce").dropna()
        if len(tv)<30:continue
        cuts=sorted(set(float(tv.quantile(q)) for q in (.20,.35,.50,.65,.80)))
        for cut in cuts:
            for direction in ("HIGH","LOW"):
                def pick(z):
                    v=pd.to_numeric(z[feat],errors="coerce")
                    return z[v.ge(cut)] if direction=="HIGH" else z[v.le(cut)]
                a,b,c=pick(tr),pick(va),pick(co)
                if len(a)<20 or len(b)<12:continue
                rt,rv,rc=rate(a,label),rate(b,label),rate(c,label)
                rows.append({
                    "label":label,"feature":feat,"direction":direction,"cut":cut,
                    "train_R":len(a),"train_rate":rt,"train_lift":rt/bt if bt else np.nan,
                    "val_R":len(b),"val_rate":rv,"val_lift":rv/bv if bv else np.nan,
                    "confirm_R":len(c),"confirm_rate":rc,"confirm_lift":rc/bc if bc else np.nan,
                    "selection_floor":min(rt,rv),
                    "selection_mean":(rt+rv)/2,
                    "generic4_strength_only":int(is_generic4_strength(feat)),
                })
    return pd.DataFrame(rows)

def evaluate_categories(df,label):
    tr=df[df.month.eq(TRAIN_MONTH)]
    va=df[df.month.eq(VAL_MONTH)]
    co=df[df.month.eq(CONF_MONTH)]
    bt,bv,bc=rate(tr,label),rate(va,label),rate(co,label)
    rows=[]
    for feat in [c for c in df.columns if c.startswith("cat_")]:
        for cat,n in tr[feat].astype(str).value_counts().items():
            if cat in ("","nan","missing") or n<15:continue
            a=tr[tr[feat].astype(str).eq(cat)]
            b=va[va[feat].astype(str).eq(cat)]
            c=co[co[feat].astype(str).eq(cat)]
            if len(b)<8:continue
            rt,rv,rc=rate(a,label),rate(b,label),rate(c,label)
            rows.append({
                "label":label,"feature":feat,"category":cat,
                "train_R":len(a),"train_rate":rt,"train_lift":rt/bt if bt else np.nan,
                "val_R":len(b),"val_rate":rv,"val_lift":rv/bv if bv else np.nan,
                "confirm_R":len(c),"confirm_rate":rc,"confirm_lift":rc/bc if bc else np.nan,
                "selection_floor":min(rt,rv),"selection_mean":(rt+rv)/2,
                "generic4_strength_only":0,
            })
    return pd.DataFrame(rows)

def cond(df,row):
    v=pd.to_numeric(df[row.feature],errors="coerce")
    return v.ge(row.cut) if row.direction=="HIGH" else v.le(row.cut)

def evaluate_interactions(df,label,num):
    if num.empty:return pd.DataFrame()
    # Candidate pool chosen only by June+July metrics.
    pool=num[(num.train_lift>1.05)&(num.val_lift>1.05)].copy()
    pool=pool.sort_values(["selection_floor","selection_mean","train_R"],ascending=False)
    # distinct features, at most 20
    chosen=[];seen=set()
    for r in pool.itertuples():
        if r.feature in seen:continue
        seen.add(r.feature);chosen.append(r)
        if len(chosen)>=20:break
    tr=df[df.month.eq(TRAIN_MONTH)]
    va=df[df.month.eq(VAL_MONTH)]
    co=df[df.month.eq(CONF_MONTH)]
    bt,bv,bc=rate(tr,label),rate(va,label),rate(co,label)
    out=[]
    for a,b in combinations(chosen,2):
        ta=tr[cond(tr,a)&cond(tr,b)]
        vb=va[cond(va,a)&cond(va,b)]
        cc=co[cond(co,a)&cond(co,b)]
        if len(ta)<12 or len(vb)<8:continue
        rt,rv,rc=rate(ta,label),rate(vb,label),rate(cc,label)
        gen4=int(bool(a.generic4_strength_only) and bool(b.generic4_strength_only))
        out.append({
            "label":label,
            "feature1":a.feature,"dir1":a.direction,"cut1":a.cut,
            "feature2":b.feature,"dir2":b.direction,"cut2":b.cut,
            "train_R":len(ta),"train_rate":rt,"train_lift":rt/bt if bt else np.nan,
            "val_R":len(vb),"val_rate":rv,"val_lift":rv/bv if bv else np.nan,
            "confirm_R":len(cc),"confirm_rate":rc,"confirm_lift":rc/bc if bc else np.nan,
            "selection_floor":min(rt,rv),"selection_mean":(rt+rv)/2,
            "generic4_strength_only":gen4,
        })
    return pd.DataFrame(out)

def main():
    if not STAGEB.exists():raise RuntimeError(f"MISSING_STAGEB_{STAGEB}")
    if not HEAD4.exists():raise RuntimeError(f"MISSING_HEAD4_{HEAD4}")
    f=pd.read_csv(STAGEB,dtype={"race_code":str})
    h=pd.read_csv(HEAD4,dtype={"race_code":str})
    f["race_code"]=f.race_code.astype(str).str.zfill(12)
    h["race_code"]=h.race_code.astype(str).str.zfill(12)
    f=f[f.month.isin([TRAIN_MONTH,VAL_MONTH,CONF_MONTH])].copy()
    h=h[h.date.astype(str).str[:7].isin([TRAIN_MONTH,VAL_MONTH,CONF_MONTH])].copy()
    if h.race_code.duplicated().any():raise RuntimeError("DUP_HEAD4_RACECODE")

    hm=h.set_index("race_code")["production_bet"].to_dict()
    f["head4_comparable"]=f.race_code.isin(hm).astype(int)
    f["head4_production_bet"]=f.race_code.map(hm)
    f["head4_production_bet"]=pd.to_numeric(f.head4_production_bet,errors="coerce")

    # Strict non-overlap means exact comparable race + official production nonfire.
    strict=f[(f.head4_comparable==1)&(f.head4_production_bet.eq(0))].copy()
    overlap=f[(f.head4_comparable==1)&(f.head4_production_bet.eq(1))].copy()
    unknown=f[f.head4_comparable.eq(0)].copy()
    if len(strict)<100:raise RuntimeError(f"STRICT_NONOVERLAP_TOO_SMALL_{len(strict)}")

    coverage=[]
    for mon in (TRAIN_MONTH,VAL_MONTH,CONF_MONTH):
        z=f[f.month.eq(mon)];s=strict[strict.month.eq(mon)];o=overlap[overlap.month.eq(mon)];u=unknown[unknown.month.eq(mon)]
        row={"month":mon,"stagea_R":len(z),"strict_nonoverlap_R":len(s),"existing4_fire_R":len(o),"not_comparable_R":len(u)}
        for lab in TARGETS+["route_1_escape"]:
            row[f"{lab}_strict_rate"]=rate(s,lab)
            row[f"{lab}_overlap_rate"]=rate(o,lab)
        coverage.append(row)
    pd.DataFrame(coverage).to_csv(OUT/"monthly_nonoverlap.csv",index=False)

    base={}
    for lab in TARGETS+["route_1_escape"]:
        base[lab]={}
        for mon,name in ((TRAIN_MONTH,"train"),(VAL_MONTH,"validation"),(CONF_MONTH,"confirmation")):
            base[lab][name]=summary(strict[strict.month.eq(mon)],lab)

    allnum=[];allcat=[];allinter=[]
    for lab in TARGETS:
        n=evaluate_numeric(strict,lab)
        c=evaluate_categories(strict,lab)
        i=evaluate_interactions(strict,lab,n)
        if len(n):allnum.append(n)
        if len(c):allcat.append(c)
        if len(i):allinter.append(i)

    num=pd.concat(allnum,ignore_index=True) if allnum else pd.DataFrame()
    cat=pd.concat(allcat,ignore_index=True) if allcat else pd.DataFrame()
    inter=pd.concat(allinter,ignore_index=True) if allinter else pd.DataFrame()

    def sortsel(x):
        if x.empty:return x
        return x.sort_values(["selection_floor","selection_mean","train_R"],ascending=[False,False,False])

    num=sortsel(num);cat=sortsel(cat);inter=sortsel(inter)
    num.to_csv(OUT/"numeric_ranking.csv",index=False)
    cat.to_csv(OUT/"categorical_ranking.csv",index=False)
    inter.to_csv(OUT/"interaction_ranking.csv",index=False)

    pref_num=sortsel(num[num.generic4_strength_only.eq(0)].copy()) if len(num) else num
    pref_int=sortsel(inter[inter.generic4_strength_only.eq(0)].copy()) if len(inter) else inter
    pref_num.to_csv(OUT/"preferred_novel_numeric.csv",index=False)
    pref_int.to_csv(OUT/"preferred_novel_interactions.csv",index=False)

    top={}
    for lab in TARGETS:
        ni=pref_num[pref_num.label.eq(lab)].head(10).to_dict("records") if len(pref_num) else []
        ii=pref_int[pref_int.label.eq(lab)].head(10).to_dict("records") if len(pref_int) else []
        top[lab]={"numeric":ni,"interaction":ii}

    meta={
        "model_id":"INNER12_NOVEL_NONOVERLAP_V1",
        "status":"RESEARCH_ONLY",
        "existing4_policy":"exact audit_4head_ph5_live_walkforward production_bet",
        "existing4_gate":"PH5 head_prob>=.36 AND orig4_adv_inside>=-.06",
        "strict_nonoverlap_definition":"race present in exact 4HEAD race_detail AND production_bet==0",
        "train":TRAIN_MONTH,"validation":VAL_MONTH,"confirmation_report_only":CONF_MONTH,
        "august_used_for_selection":False,
        "september_outcomes_read":False,
        "production_changed":False,
        "stagea_rows":int(len(f)),"strict_nonoverlap_rows":int(len(strict)),
        "existing4_fire_rows":int(len(overlap)),"not_comparable_rows":int(len(unknown)),
        "baselines":base,"top_preferred_novel":top,
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INNER12_NOVEL_NONOVERLAP_V1_OK")
    print("COUNTS",json.dumps({k:meta[k] for k in ("stagea_rows","strict_nonoverlap_rows","existing4_fire_rows","not_comparable_rows")},ensure_ascii=False))
    print("BASELINES",json.dumps(base,ensure_ascii=False))
    for lab in TARGETS:
        print("TOP_NOVEL",lab,json.dumps(top[lab],ensure_ascii=False))
    print("AUGUST_REPORT_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
