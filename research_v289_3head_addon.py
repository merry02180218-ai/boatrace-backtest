#!/usr/bin/env python3
"""v289 add-on research: preserve canonical v288 and rank only final NO_BET races.

Research-only. September outcomes are never loaded; source artifact ends 2026-08-31.
All test-month decisions are produced from prior-month training only.
"""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

SRC = Path("analysis_v243_3head_expand_feature_audit.csv")
OUT_JSON = Path("research_v289_3head_addon.json")
OUT_MD = Path("research_v289_3head_addon.md")
HANDOFF = Path("CHAT_HANDOFF_3HEAD_AUTO_RESEARCH_CURRENT.md")

KEEP=-0.1999999999999999; RESCUE=0.5672342857142857
WAKU34=0.4999999999999999; ST34=-0.6; MEETST=0.861111111111111
A_ST34=0.6; A_WALL=0.24875; B_MOTOR=0.22388571428571424; B_NST=-0.0714285714285712
S_Q=.70; A_Q=.20
FRACTIONS=(.15,.25,.45)
BASELINE_EXPECTED={"races":94,"hits":52,"payout_yen":1622070.0}

def num(df,c): return pd.to_numeric(df[c],errors="coerce")

def v243_target(df):
    base=(df.bet==1)&(df.p3>=.45)&df.raw_top_n.between(7,18)&df.comp_odds.between(3.05,4.0)
    return (base&(num(df,"f__c_b3_minus_b5_st")>=KEEP))|((df.bet==1)&(~base)&(num(df,"f__c_attack3_stretch")<=RESCUE))

def precols(df):
    bad=("pair_","p3","odds","comp","top_n","raw_top","ticket","hit","ret","profit","bet","invalid","result","settle")
    current=("attack3","wall12","_st","_ex","lap","turn","straight","orig","tilt","exh","tenji","display")
    return [c for c in df if c.startswith("f__") and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in current)]

def learned_pre_features(tr,cols):
    y=tr._target.astype(int); rows=[]
    for c in cols:
        x=num(tr,c); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
        if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
            eff=(a.mean()-b.mean())/sd
            if np.isfinite(eff): rows.append((abs(eff),eff,c))
    return sorted(rows,reverse=True)[:12]

def signed_z_score(tr,te,features):
    s=pd.Series(0.0,index=te.index,dtype=float)
    for _,eff,c in features:
        xtr=num(tr,c); med=xtr.median(); sd=xtr.std()
        if np.isfinite(sd) and sd>1e-12:
            x=num(te,c).fillna(med)
            s += np.sign(eff)*((x-med)/sd).clip(-4,4)
    return s

def replay_operational_pre(q):
    months=sorted(q.month.unique()); cols=precols(q); pred=[]; thresholds={}
    for i,m in enumerate(months):
        if i<2: continue
        tr=q[q.month.isin(months[:i])].copy()
        te=q[q.month==m].copy()
        fs=learned_pre_features(tr,cols)
        trscore=signed_z_score(tr,tr,fs); te["_pre_score"]=signed_z_score(tr,te,fs)
        s_thr=float(trscore.quantile(S_Q)); a_thr=float(trscore.quantile(A_Q))
        te["grade"]=np.where(te._pre_score>=s_thr,"S",np.where(te._pre_score>=a_thr,"A","B"))
        pred.append(te)
        thresholds[m]={"train_months":months[:i],"s_threshold":s_thr,"a_threshold":a_thr,"test_rows":int(len(te))}
    return pd.concat(pred,ignore_index=True), thresholds

def add_v288_route(df, outcol="route"):
    final=v243_target(df)
    core=(num(df,"f__c_b3_minus_b4_waku_st")<=WAKU34)&(num(df,"f__c_b3_minus_b4_st")>=ST34)&(num(df,"f__c_b3_meetst")<=MEETST)
    s=final&core
    purch=df.bet==1
    a=purch&(~s)&(num(df,"f__c_b3_minus_b4_st")>=A_ST34)&(num(df,"f__c_wall12_weak")<=A_WALL)
    b=purch&(~s)&(~a)&(num(df,"f__c_b3_minus_b2_motor")>=B_MOTOR)&(num(df,"f__c_b3_inside_nst")<=B_NST)
    df[outcol]=np.where(s,"S",np.where(a,"A",np.where(b,"B","NO_BET")))
    return df

def safe_live_cols(df):
    bad=("pair_","hit","ret","profit","result","settle","invalid","y3","winner","actual","payout","ticket")
    out=[]
    for c in df.columns:
        lc=c.lower()
        if c in ("p3","raw_top_n","comp_odds"):
            out.append(c)
        elif c.startswith("f__") and not any(x in lc for x in bad):
            out.append(c)
    return out

def current_exhibition_cols(cols):
    tok=("ex","_st","lap","turn","straight","orig","attack3","wall12","outer_follow","tilt","display","tenji","exh")
    return [c for c in cols if c.startswith("f__") and any(t in c.lower() for t in tok)]

def fit_effect(tr,cols,mode="hit",topk=18):
    rows=[]
    if mode=="hit":
        y=num(tr,"trifecta_hit").fillna(0).astype(int)
        for c in cols:
            x=num(tr,c); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
            if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
                eff=(a.mean()-b.mean())/sd
                if np.isfinite(eff): rows.append((abs(eff),eff,c))
    else:
        y=np.log1p(num(tr,"ret").fillna(0)/10000.0)
        for c in cols:
            x=num(tr,c); ok=x.notna()&np.isfinite(x)&np.isfinite(y)
            if int(ok.sum())>=30 and x[ok].std()>1e-12:
                corr=np.corrcoef(x[ok],y[ok])[0,1]
                if np.isfinite(corr): rows.append((abs(corr),corr,c))
    return sorted(rows,reverse=True)[:topk]

def standardize_by_train(trs, tes):
    med=float(trs.median()) if len(trs) else 0.0
    sd=float(trs.std()) if len(trs) else 1.0
    if not np.isfinite(sd) or sd<1e-12: sd=1.0
    return ((tes-med)/sd).clip(-6,6)

def style_score(tr,te,live_cols):
    a="f__c_attack3_stretch"; b="f__c_attack3_turn"
    tr_style=(num(tr,a)<=num(tr,b)).fillna(False)
    te_style=(num(te,a)<=num(te,b)).fillna(False)
    out=pd.Series(0.0,index=te.index,dtype=float)
    for val in (True,False):
        tri=tr[tr_style==val]
        tei=te[te_style==val]
        if len(tei)==0: continue
        fs=fit_effect(tri,live_cols,"hit",10)
        if len(tri)<35 or len(fs)<3:
            fs=fit_effect(tr,live_cols,"hit",10); tri=tr
        out.loc[tei.index]=signed_z_score(tri,tei,fs)
    return out

def method_scores(tr,te,allcols,livecols):
    hitfs=fit_effect(tr,allcols,"hit",18)
    livefs=fit_effect(tr,livecols,"hit",12)
    retfs=fit_effect(tr,allcols,"value",18)
    tr_hit=signed_z_score(tr,tr,hitfs); te_hit=signed_z_score(tr,te,hitfs)
    tr_live=signed_z_score(tr,tr,livefs); te_live=signed_z_score(tr,te,livefs)
    tr_ret=signed_z_score(tr,tr,retfs); te_ret=signed_z_score(tr,te,retfs)
    tr_style=style_score(tr,tr,livecols); te_style=style_score(tr,te,livecols)
    tr_cons=(standardize_by_train(tr_hit,tr_hit)+standardize_by_train(tr_live,tr_live)+standardize_by_train(tr_ret,tr_ret))/3.0
    te_cons=(standardize_by_train(tr_hit,te_hit)+standardize_by_train(tr_live,te_live)+standardize_by_train(tr_ret,te_ret))/3.0
    return {"residual_hit":(tr_hit,te_hit),"exhibition_upgrade":(tr_live,te_live),"return_rank":(tr_ret,te_ret),"attack_style_split":(tr_style,te_style),"orthogonal_consensus":(tr_cons,te_cons)}

def choose_ev_alpha(tr,base_score,frac):
    best=None
    odds=np.log(num(tr,"comp_odds").clip(lower=.05))
    z=standardize_by_train(base_score,base_score)
    for alpha in (0.0,.25,.5,1.0):
        s=z+alpha*odds.fillna(odds.median())
        thr=float(s.quantile(1-frac)); g=tr[s>=thr]; n=len(g)
        if n<10: continue
        roi=float(100*num(g,"ret").fillna(0).sum()/(n*10000))
        conservative=(roi-100.0)*math.sqrt(n/20.0)
        row=(conservative,roi,alpha,thr)
        if best is None or row>best: best=row
    return best[2] if best else 0.0

def metric(df):
    n=int(len(df)); hits=int(num(df,"trifecta_hit").fillna(0).sum()); payout=float(num(df,"ret").fillna(0).sum()); stake=n*10000
    return {"races":n,"hits":hits,"hit_rate_pct":100*hits/n if n else None,"stake_yen":stake,"payout_yen":payout,"profit_yen":payout-stake,"roi_pct":100*payout/stake if stake else None}

def max_drawdown(df):
    if len(df)==0: return 0.0
    z=df.sort_values(["date","race_code"]).copy(); pnl=num(z,"ret").fillna(0)-10000; curve=pnl.cumsum()
    peak=np.maximum.accumulate(np.r_[0.0,curve.values]); dd=peak[1:]-curve.values
    return float(dd.max()) if len(dd) else 0.0

def main():
    q=pd.read_csv(SRC,dtype={"race_code":str}); q["date"]=q.date.astype(str); q["month"]=q.date.str[:7]
    if q.date.max()>"2026-08-31": raise RuntimeError("September or later rows are forbidden in v289 tuning")
    q["_target"]=v243_target(q).astype(int)
    replay,thresholds=replay_operational_pre(q); replay=replay[replay.grade.isin(["S","A"])].copy(); add_v288_route(replay)
    baseline=replay[replay.route!="NO_BET"].copy(); bm=metric(baseline)
    if bm["races"]!=94 or bm["hits"]!=52 or abs(bm["payout_yen"]-1622070.0)>.01: raise RuntimeError(f"baseline drift: {bm}")
    candidates=replay[(replay.route=="NO_BET")&(replay.bet==1)].copy()
    raw=q.copy(); add_v288_route(raw,"raw_route"); allcols=safe_live_cols(raw); livecols=current_exhibition_cols(allcols)
    picked_rows={}; audit={}
    for m in sorted(candidates.month.unique()):
        tr=raw[(raw.month<m)&(raw.bet==1)&(raw.raw_route=="NO_BET")].copy(); te=candidates[candidates.month==m].copy()
        scores=method_scores(tr,te,allcols,livecols); audit[m]={"train_rejects":int(len(tr)),"test_operational_rejects":int(len(te))}
        for method,(trscore,tescore) in scores.items():
            for frac in FRACTIONS:
                threshold=float(trscore.quantile(1-frac)); idx=te.index[tescore>=threshold]
                picked_rows.setdefault((method,frac),[]).append(te.loc[idx].copy())
        tr_hit,te_hit=scores["residual_hit"]
        for frac in FRACTIONS:
            alpha=choose_ev_alpha(tr,tr_hit,frac)
            tr_ev=standardize_by_train(tr_hit,tr_hit)+alpha*np.log(num(tr,"comp_odds").clip(lower=.05)).fillna(0)
            te_ev=standardize_by_train(tr_hit,te_hit)+alpha*np.log(num(te,"comp_odds").clip(lower=.05)).fillna(0)
            threshold=float(tr_ev.quantile(1-frac)); idx=te.index[te_ev>=threshold]
            picked_rows.setdefault(("ev_calibrated",frac),[]).append(te.loc[idx].copy())
    aggregate=[]; detail={}
    for (method,frac),parts in picked_rows.items():
        g=pd.concat(parts,ignore_index=True) if parts else candidates.iloc[0:0].copy(); gm=metric(g); gm["max_drawdown_yen"]=max_drawdown(g)
        combined=pd.concat([baseline,g],ignore_index=True); cm=metric(combined); cm["max_drawdown_yen"]=max_drawdown(combined)
        monthly={m:metric(x) for m,x in g.groupby("month")}; monthly_rois=[x["roi_pct"] for x in monthly.values() if x["roi_pct"] is not None]
        aggregate.append({"method":method,"fraction":frac,"addon":gm,"combined":cm,"overlap_with_v288":0,"monthly":monthly,"min_monthly_roi_pct":min(monthly_rois) if monthly_rois else None})
        detail[f"{method}@{frac:.2f}"]={"races":[{"date":r.date,"race_code":str(r.race_code),"hit":int(r.trifecta_hit),"ret":float(r.ret)} for r in g.itertuples(index=False)]}
    aggregate.sort(key=lambda x:((x["addon"]["roi_pct"] or -1),x["addon"]["races"]),reverse=True)
    candidates_ok=[x for x in aggregate if x["addon"]["races"]>=20 and (x["addon"]["roi_pct"] or 0)>=100 and (x["min_monthly_roi_pct"] or 0)>=60]
    decision="SHADOW_CANDIDATE" if candidates_ok else "NO_ADOPTION_WAVE1"; best=aggregate[0] if aggregate else None
    out={"research_version":"v289-addon-wave1","source_max_date":q.date.max(),"rules":{"baseline_fixed":"v288 operational 94R","test_months":"2026-02..2026-08","july_august":"NON-PRISTINE","september_outcomes_used":False,"candidate_universe":"operational PRE S/A + v242 buyable + final v288 NO_BET only","fractions":list(FRACTIONS)},"baseline":{**bm,"max_drawdown_yen":max_drawdown(baseline)},"candidate_pool":metric(candidates),"methods":aggregate,"decision":decision,"best_wave1":best,"thresholds":thresholds,"audit":audit,"detail":detail}
    OUT_JSON.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# v289 3号艇 add-on auto research — wave 1","","- baseline: **v288 operational 94R fixed**","- target: only operational PRE S/A + buyable races where v288 final route is `NO_BET`","- test: 2026-02..2026-08 strict prior-month training","- July/August: **NON-PRISTINE**","- September outcomes used for tuning: **NO**","",f"## Baseline\n- {bm['races']}R / {bm['hits']} hits / ROI {bm['roi_pct']:.3f}% / profit {bm['profit_yen']:+,.0f} yen","","## Wave-1 methods","","| method | target frac | add R | hits | add ROI | add profit | min month ROI | combined R | combined ROI |","|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in aggregate:
        a=x["addon"]; c=x["combined"]; mn=x["min_monthly_roi_pct"]
        lines.append(f"| {x['method']} | {x['fraction']:.0%} | {a['races']} | {a['hits']} | {a['roi_pct']:.2f}% | {a['profit_yen']:+,.0f} | {mn:.2f}% | {c['races']} | {c['roi_pct']:.2f}% |")
    lines += ["",f"## Decision\n**{decision}**","","Wave 1 is research/model-selection evidence only. A method is not production-adopted from this report alone.","Weak methods remain recorded so later research does not repeat dead ends."]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    hand=["# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT","","## Status",f"- research version: `v289-addon-wave1`",f"- decision: **{decision}**","- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.","- July/August are NON-PRISTINE. September outcomes were not loaded or used.","- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.","","## Wave-1 result",f"- candidate pool: {len(candidates)} races",f"- best tested variant: `{best['method']}@{best['fraction']:.2f}`" if best else "- no variant",f"- best add-on: {best['addon']['races']}R / {best['addon']['hits']} hits / ROI {best['addon']['roi_pct']:.2f}% / profit {best['addon']['profit_yen']:+,.0f} yen" if best else "",f"- combined: {best['combined']['races']}R / ROI {best['combined']['roi_pct']:.2f}%" if best else "","","## Methods tested / dead ends retained","- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.","- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.","- `return_rank`: prior-reject realized-return ranking trained only on prior months.","- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.","- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.","- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.","","## Real-operation audit","- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;","- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;","- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;","- overlap with v288 baseline is zero by construction;","- no production workflow/model was changed.","","## Next restart point","- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.","- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.","- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.","","## Generated artifacts","- `research_v289_3head_addon.json`","- `research_v289_3head_addon.md`",""]
    HANDOFF.write_text("\n".join(hand)+"\n",encoding="utf-8")
    print(json.dumps({"baseline":bm,"candidate_pool":len(candidates),"decision":decision,"best":best},ensure_ascii=False,indent=2)); print("V289_ADDON_WAVE1_OK")

if __name__=="__main__": main()
