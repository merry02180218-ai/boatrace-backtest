#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle,csv
from pathlib import Path
from datetime import date
import pandas as pd
import backtest as bt
import run_1head_player_history_expansion as phbase
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod
import onehead_five_second_topup as topup

MONTHS=("2026-03","2026-04","2026-05","2026-06","2026-07","2026-08")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-current-sixmonth";OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:return float(x)
    except:return float("nan")
def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:raise RuntimeError("September guard disabled")
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"]
    if len(rr["LIVE165"])!=165 or len(rr["H078_M375"])!=236:raise RuntimeError("frozen universe drift")
    live={str(r["race_code"]).zfill(12):r for r in rr["LIVE165"]}
    added=[r for r in rr["H078_M375"] if str(r["race_code"]).zfill(12) not in live]
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    targets={str(r["race_code"]).zfill(12) for r in added}
    snaps=phbase.build_canonical_ph_snapshots(targets,date(2025,10,1),date(2026,8,31),root)
    phcodes={c for c,v in snaps.items() if float(v[prod.PLAYER_HISTORY_EXPANSION_FEATURE])>=prod.PLAYER_HISTORY_EXPANSION_THRESHOLD}
    selected=list(live.values())+[r for r in added if str(r["race_code"]).zfill(12) in phcodes]
    if len(selected)!=prod.PLAYER_HISTORY_EXPANSION_COMBINED_R:raise RuntimeError(f"current selection drift {len(selected)}")
    selected=[r for r in selected if str(r["race_code"])[:4]+"-"+str(r["race_code"])[4:6] in MONTHS]
    if any(str(r["race_code"]).zfill(12)[:8]>="20260901" for r in selected):raise RuntimeError("September entered")
    v365.install_payout_cache(selected);payouts=v365.payouts_for(selected)
    cache={};rec=[]
    for r in sorted(selected,key=lambda z:str(z["race_code"])):
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3]
        base=[f"1-{s}-{t}" for s,t in formal]
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv"))
        card=cache[day].get(code)
        if not card:raise RuntimeError("missing card "+code)
        xf=bt.race_features(card,{})
        local_edge=ff(xf[5]["local"])-ff(xf[4]["local"])
        straight_edge=ff(r.get("straight5"))-ff(r.get("straight4"))
        core_edge=ff(r.get("core5"))-ff(r.get("core4"))
        rg=topup.regime_meta(p2,local_edge,straight_edge,core_edge,prod.FIVE_SECOND_TOPUP_P2_RATIO_MIN)
        extras=topup.extra_tickets(pc,base,prod.FIVE_SECOND_TOPUP_EXTRA_TICKETS) if rg["applied"] else []
        tickets=base+extras;actual=str(r.get("actual_combo",""));pay=int(payouts.get(code,0))
        head=int(actual.startswith("1-"));hit=int(actual in tickets)
        rec.append(dict(race_code=code,month=m,source=("PH_EXPANSION" if code in phcodes and code not in live else "FORMAL"),
                        head_hit=head,hit=hit,base_hit=int(actual in base),fire=int(rg["applied"]),
                        ticket_count=len(tickets),stake=len(tickets)*100,return_yen=pay if hit else 0,
                        actual_combo=actual,tickets=";".join(tickets),base_tickets=";".join(base),extra_tickets=";".join(extras),
                        p2_2=ff(p2.get(2)),p2_3=ff(p2.get(3)),p2_4=ff(p2.get(4)),p2_5=ff(p2.get(5)),p2_6=ff(p2.get(6)),
                        local5m4=local_edge,straight5m4=straight_edge,core5m4=core_edge))
    z=pd.DataFrame(rec)
    def met(g):
        stake=int(g.stake.sum());ret=int(g.return_yen.sum())
        return dict(R=len(g),HEAD=int(g.head_hit.sum()),head_rate=float(g.head_hit.mean()) if len(g) else 0,
                    EXACT3=int(g.hit.sum()),exact3_rate=float(g.hit.mean()) if len(g) else 0,
                    fires=int(g.fire.sum()),tickets=int(g.ticket_count.sum()),stake=stake,return_yen=ret,
                    profit=ret-stake,roi=ret/stake if stake else 0)
    monthly=[{"month":m,**met(g)} for m,g in z.groupby("month",sort=True)]
    result={"period":"2026-03..2026-08","profile":"CURRENT_1HEAD_FORMAL_PLUS_PH_EXPANSION_WALL3_FIVE6_1TO5",
            "overall":met(z),"monthly":monthly,"formal_R":int((z.source=="FORMAL").sum()),
            "ph_expansion_R":int((z.source=="PH_EXPANSION").sum()),"september_outcomes_read":False,
            "phwaku_w3_used":False,"audit_ok":True}
    z.to_csv(OUT/"races.csv",index=False);(OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    sig=[]
    for col in ["source","fire"]:
        for k,g in z.groupby(col,dropna=False):
            sig.append({"signal":col,"value":str(k),**met(g)})
    for col in ["local5m4","straight5m4","core5m4","p2_5"]:
        try:
            b=pd.qcut(z[col],q=min(4,z[col].nunique()),duplicates="drop")
            for k,g in z.groupby(b,observed=True):
                sig.append({"signal":col+"_quartile","value":str(k),**met(g)})
        except Exception:
            pass
    # pre-race strong-signal candidates inside the promoted 1-5 regime
    fz=z[z.fire==1].copy()
    if len(fz):
        for col in ["local5m4","straight5m4","core5m4","p2_5"]:
            vals=sorted(fz[col].dropna().unique())
            cuts=sorted(set([float(fz[col].quantile(q)) for q in (.25,.5,.75)]))
            for cut in cuts:
                for op in ("ge","le"):
                    g=fz[fz[col]>=cut] if op=="ge" else fz[fz[col]<=cut]
                    if len(g)>=5:
                        sig.append({"signal":"fire_"+col+"_"+op,"value":str(cut),**met(g)})
        # pairwise intersections, thresholds derived only from fire-set quartiles
        cols=["local5m4","straight5m4","core5m4","p2_5"]
        for i,a in enumerate(cols):
            for b in cols[i+1:]:
                for qa in (.25,.5,.75):
                    ca=float(fz[a].quantile(qa))
                    for qb in (.25,.5,.75):
                        cb=float(fz[b].quantile(qb))
                        g=fz[(fz[a]>=ca)&(fz[b]>=cb)]
                        if len(g)>=5:
                            sig.append({"signal":"fire_pair_ge","value":f"{a}>={ca:.6g}&{b}>={cb:.6g}",**met(g)})
    # stability audit for leading pre-race strong-signal candidates
    strong_defs=[
        ("FIRE_ONLY", z.fire==1),
        ("CORE_LE_0289167", (z.fire==1)&(z.core5m4<=0.2891666666666667)),
        ("CORE_LE_0228333", (z.fire==1)&(z.core5m4<=0.2283333333333333)),
        ("LOCAL_GE_125_STRAIGHT_GE_02", (z.fire==1)&(z.local5m4>=1.25)&(z.straight5m4>=0.2)),
    ]
    stability=[]
    for name,mask in strong_defs:
        g=z[mask]
        stability.append({"candidate":name,"scope":"ALL",**met(g)})
        for mm,mg in g.groupby("month",sort=True):
            stability.append({"candidate":name,"scope":mm,**met(mg)})
        # leave-one-month-out: checks whether one month alone drives the result
        for mm in MONTHS:
            mg=g[g.month!=mm]
            if len(mg):
                stability.append({"candidate":name,"scope":"EXCL_"+mm,**met(mg)})
    pd.DataFrame(stability).to_csv(OUT/"strong_signal_stability.csv",index=False)
    result["strong_signal_stability"]=stability
    for sec in BOATS:
        g=z[z.actual_combo.str.startswith(f"1-{sec}-",na=False)]
        if len(g):
            sig.append({"signal":"actual_1_second","value":str(sec),**met(g)})
    pd.DataFrame(sig).to_csv(OUT/"signals.csv",index=False)
    result["signals"]=sig
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("CURRENT_1HEAD_SIXMONTH",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
