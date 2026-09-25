#!/usr/bin/env python3
"""Six-month Mar-Aug 2026 closing-odds replay of frozen 4HEAD 49.61 rule.
Head selection is frozen at p>=.36 + ORIG>=-.06. Current v283 opponent/tickets and JPY10k Dutch.
Official archived closing odds are used. Historical missing Waku10 is NOT reconstructed from outcomes;
the companion prep script uses card fallback/neutral-low Waku primitive. September is blocked.
"""
from __future__ import annotations
import os, math, json, glob, csv, bisect
from pathlib import Path
from collections import defaultdict
import numpy as np, pandas as pd
import research_4head_clean_6m_headmodel as cleanhm
import research_4head_player_waku_soft_ablation_v23 as phsrc
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import audit_4head_86r_v283_closing_odds as v283build
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v282_4head_conditional_third as v282
from head4_v291_downstream_inference import load_artifact,score_second,score_conditional_third
import run_4head_v291_third010_live as live

OUT=Path("/tmp/head4_ph5_live_walkforward"); OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parent
DATA_ROOT=Path(os.environ.get("BOATRACECSV_LOCAL_ROOT", str(ROOT)))
BOATS=(1,2,3,5,6); BANK=10000

def rows(path):
 p=DATA_ROOT/path
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):
 s=str(x).strip(); return (s[:-2] if s.endswith(".0") else s).zfill(12)
def ff(x,d=np.nan):
 try:
  v=float(x); return v if math.isfinite(v) else d
 except:return d

def historical_live_wall_ready():
 """Replay the LIVE wall-data availability contract from raw archived original exhibition.

 LIVE wall3 needs both orig_avg_available and orig_straight_available. Do not
 infer readiness from transformed/imputed cur_orig_* columns.
 """
 out={}
 for ds in pd.date_range("2026-06-01","2026-08-31"):
  ymd=str(ds.date()).replace("-","/")
  for r in rows(f"data/previews/original_exhibition/{ymd}.csv"):
   code=rc(r.get("レースコード",""))
   published=[]
   for k in range(1,7):
    lab=str(r.get(f"計測項目{k}","")).strip().replace(" ","")
    if lab: published.append((k,lab))
   if not published:
    out[code]=False; continue
   def all6(k):
    return all(math.isfinite(ff(r.get(f"艇{b}_値{k}"))) for b in range(1,7))
   avg_all6=all(all6(k) for k,_ in published)
   straight_all6=any(("直線" in lab) and all6(k) for k,lab in published)
   out[code]=bool(avg_all6 and straight_all6)
 return out

def causal_st_bias_map():
 """Exact D-1 ST lane-bias snapshots used by current LIVE daily state."""
 hist={b:[] for b in range(1,7)}; allv=[]; out={}
 for ds in pd.date_range("2025-10-01","2026-08-31"):
  d=str(ds.date())
  g=float(np.mean(allv)) if allv else .15
  out[d]={b:(float(np.mean(hist[b]))-g if hist[b] else 0.0) for b in range(1,7)}
  for r in rows(f"data/previews/stt/{d.replace('-','/')}.csv"):
   for b in range(1,7):
    v=ff(r.get(f"艇{b}_スタート展示"))
    if math.isfinite(v) and -.30<v<1.0:
     hist[b].append(v); allv.append(v)
 return out

def add_current_live_causal(z,biasmap):
 """Historical current-exhibition primitives using the exact LIVE D-1 ST bias."""
 q=z.copy(); cache={}; vals=[]
 for _,r in q.iterrows():
  ds=str(r.date); code=str(r.race_code).zfill(12); b=int(r.boat); ymd=ds.replace('-','/')
  if ds not in cache:
   def bc(rel):
    return {rc(x.get("レースコード","")):x for x in rows(rel)}
   cache[ds]=(bc(f"data/previews/tkz/{ymd}.csv"),bc(f"data/previews/stt/{ymd}.csv"),bc(f"data/previews/original_exhibition/{ymd}.csv"))
  tkz,stt,orig=cache[ds]
  ex,st,os=v283build.v278.corrected_direct(code,tkz,stt,orig,biasmap.get(ds,{i:0.0 for i in range(1,7)}))
  zz=os.get(b,{"lap":.5,"turn":.5,"straight":.5,"avg":.5})
  vals.append((ex.get(b,np.nan),st.get(b,np.nan),zz.get("lap",np.nan),zz.get("turn",np.nan),zz.get("straight",np.nan),zz.get("avg",np.nan)))
 for j,k in enumerate(("cur_ex","cur_st","cur_orig_lap","cur_orig_turn","cur_orig_straight","cur_orig_avg")):
  q[k]=[x[j] for x in vals]
 return q

def add_start_features(long):
 q=long.copy(); cache={}; vals={}; hist={b:[] for b in range(1,7)}; allv=[]
 # Build prior-only lane bias through July, then update chronologically in August.
 for ds in pd.date_range("2025-10-01","2026-08-31"):
  d=str(ds.date()); ymd=d.replace("-","/")
  rr=rows(f"data/previews/stt/{ymd}.csv")
  g=float(np.mean(allv)) if allv else .15
  bias={b:(float(np.mean(hist[b]))-g if hist[b] else 0.0) for b in range(1,7)}
  if "2026-03" <= d[:7] <= "2026-08":
   for r in rr:
    code=rc(r.get("レースコード",""))
    raw={}
    for b in range(1,7):
     v=ff(r.get(f"艇{b}_スタート展示"))
     if math.isfinite(v):raw[b]=v
    if len(raw)==6:
     corr={b:raw[b]-bias[b] for b in raw}
     def strength(a):
      order=sorted(a,key=lambda b:(a[b],b)); rank={b:i+1 for i,b in enumerate(order)}
      st={b:(6-rank[b])/5 for b in a}; return rank,st
     rrk,rs=strength(raw); crk,cs=strength(corr)
     vals[code]={b:{"suf_st_raw":raw[b],"suf_st_raw_rank":rrk[b],"suf_st_raw_strength":rs[b],
                    "suf_st_corr_rank":crk[b],"suf_st_corr_strength":cs[b]} for b in raw}
  for r in rr:
   for b in range(1,7):
    v=ff(r.get(f"艇{b}_スタート展示"))
    if math.isfinite(v) and -.30<v<1: hist[b].append(v); allv.append(v)
 for i,r in q.iterrows():
  z=vals.get(str(r.race_code).zfill(12),{}).get(int(r.boat),{})
  for k in ("suf_st_raw","suf_st_raw_rank","suf_st_raw_strength","suf_st_corr_rank","suf_st_corr_strength"):q.loc[i,k]=z.get(k,np.nan)
 return q

def od3():
 out={}
 # Prefer historical pre-deadline snapshots from BoatraceCSV (about 5 min before close).
 for p in sorted(glob.glob(str(DATA_ROOT/"data/previews/od3/2026/*/*.csv"))):
  try:q=pd.read_csv(p,dtype={"レースコード":str})
  except:continue
  for _,r in q.iterrows():
   code=rc(r.get("レースコード",""))
   if not ("202603010000" <= code <= "202608319999"):continue
   m={}
   for aa in range(1,7):
    for bb in range(1,7):
     if bb==aa:continue
     for cc in range(1,7):
      if cc in (aa,bb):continue
      key=f"{aa}-{bb}-{cc}"; v=ff(r.get(f"3連単_{key}"))
      if math.isfinite(v) and v>0:m[key]=v
   if len(m)==120:out[code]=m
 # Closing odds are fallback only when no pre-deadline snapshot exists.
 for p in sorted(glob.glob(str(ROOT/"data/official_closing_odds3t/2026/*/*.csv"))):
  q=pd.read_csv(p,dtype={"jcd":str})
  for _,r in q.iterrows():
   ds=str(r.get("date","")).replace("-",""); j=str(r.get("jcd","")).zfill(2); rn=int(r.get("rno",0) or 0)
   if not ("20260301" <= ds <= "20260831") or rn<1:continue
   code=f"{ds}{j}{rn:02d}"; m={}
   for aa in range(1,7):
    for bb in range(1,7):
     if bb==aa:continue
     for cc in range(1,7):
      if cc in (aa,bb):continue
      key=f"{aa}-{bb}-{cc}";v=pd.to_numeric(pd.Series([r.get(key)]),errors="coerce").iloc[0]
      if pd.notna(v) and float(v)>0:m[key]=float(v)
   if len(m)==120 and code not in out:out[code]=m
 return out

def truth():
 out={}
 for ds in pd.date_range("2026-03-01","2026-08-31"):
  for r in rows(f"data/results/realtime/{ds:%Y/%m/%d}.csv"):
   code=rc(r.get("レースコード",""))
   try:a=(int(float(r["1着_艇番"])),int(float(r["2着_艇番"])),int(float(r["3着_艇番"])))
   except:continue
   out[code]=a
 if not out:raise RuntimeError("NO_SIX_MONTH_TRUTH")
 return out

def motor_priors():
 hist=defaultdict(lambda:[0,0]); snaps={}
 for ds in pd.date_range("2025-11-01","2026-08-31"):
  d=str(ds.date());ymd=d.replace("-","/"); cards={rc(r.get("レースコード","")):r for r in rows(f"data/programs/race_cards/{ymd}.csv")}
  if d.startswith("2026-08"):
   for code,card in cards.items():
    j=code[8:10]; z={}
    for b in (3,4):
     mno=str(card.get(f"艇{b}_モーター番号","")).strip(); n,w=hist[(j,mno)]; z[b]=(w/n if n else None)
    snaps[code]=z
  rm={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  for code,card in cards.items():
   rr=rm.get(code); 
   if not rr:continue
   try:winner=int(float(rr.get("1着_艇番")))
   except:continue
   j=code[8:10]
   for b in range(1,7):
    mno=str(card.get(f"艇{b}_モーター番号","")).strip()
    if mno:
     hist[(j,mno)][0]+=1;hist[(j,mno)][1]+=int(winner==b)
 return snaps

def ecdf(x,refs,missing=.5):
 if x is None or not math.isfinite(float(x)) or not refs:return missing
 return bisect.bisect_right(refs,float(x))/len(refs)

def monitoring_parent_snapshots():
 """Exact historical replay of the current LIVE PRE monitoring-parent gate.

 Histories are frozen at D-1 before each target date D, matching
 scan_4head_120r_pre_live.py / prepare_4head_120r_daily_state.py semantics.
 Missing parent features fail open exactly as LIVE does.
 """
 WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605
 mh=defaultdict(lambda:[0,0]); ph=defaultdict(lambda:[0,0]); out={}
 for ds in pd.date_range("2025-10-01","2026-08-31"):
  d=str(ds.date()); ymd=d.replace("-","/")
  cards={rc(r.get("レースコード","")):r for r in rows(f"data/programs/race_cards/{ymd}.csv")}
  if d>="2026-06-01":
   for code,card in cards.items():
    j=code[8:10]
    vals={}
    for b in (3,4):
     mno=str(card.get(f"艇{b}_モーター番号","")).strip()
     n,w=mh[(j,mno)]
     vals[b]=(w/n if n else float("nan"))
    mwd=vals[4]-vals[3] if math.isfinite(vals[4]) and math.isfinite(vals[3]) else float("nan")
    m2d=ff(str(card.get("艇4_モーター2連対率","")).replace("%",""))-ff(str(card.get("艇3_モーター2連対率","")).replace("%",""))
    reg4=str(card.get("艇4_登録番号","")).strip(); pn,pw=ph[reg4]
    p4=(pw/pn if pn else float("nan"))
    missing=not (math.isfinite(mwd) and math.isfinite(m2d) and math.isfinite(p4))
    parent=bool(missing or (mwd>=WIN and m2d>=REN2 and p4>=PLAYER))
    out[code]={"monitoring_parent":int(parent),"parent_feature_missing":int(missing),
               "parent_motor_win_diff_4v3":mwd,"parent_motor_2ren_diff_4v3":m2d,
               "parent_player4_all_win_prior":p4}
  rm={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  for code,card in cards.items():
   rr=rm.get(code)
   if not rr:continue
   try:winner=int(float(rr.get("1着_艇番")))
   except:continue
   if winner not in range(1,7):continue
   j=code[8:10]
   for b in range(1,7):
    mno=str(card.get(f"艇{b}_モーター番号","")).strip()
    if mno:
     mh[(j,mno)][0]+=1; mh[(j,mno)][1]+=int(winner==b)
    reg=str(card.get(f"艇{b}_登録番号","")).strip()
    if reg:
     ph[reg][0]+=1; ph[reg][1]+=int(winner==b)
 return out

def main():
 strict=pd.read_csv(os.environ["STRICT_ROWS"],dtype={"race_code":str});strict.race_code=strict.race_code.astype(str).str.zfill(12)
 strict=strict[(strict.month>="2026-06")&(strict.month<="2026-08")&strict.struct_ready.astype(str).str.lower().isin(["true","1"])].copy()
 if not len(strict):raise RuntimeError("NO_SIX_MONTH_STRUCT_READY")
 v_all=pd.read_csv(os.environ["V93_ROWS"],dtype={"race_code":str});v_all.race_code=v_all.race_code.astype(str).str.zfill(12);v=v_all[v_all.race_code.isin(set(strict.race_code))].copy()
 if set(v.race_code)!=set(strict.race_code):raise RuntimeError(f"V93_COVERAGE_{v.race_code.nunique()}/{len(strict)}")
 # Build v283 long table with the exact LIVE D-1 ST lane-bias before scenario/relative transforms.
 st_bias_by_date=causal_st_bias_map()
 _orig_add_current=v283build.v278.add_current
 v283build.v278.add_current=lambda z:add_current_live_causal(z,st_bias_by_date)
 try:
  long=v283build.build_long_all(v)
 finally:
  v283build.v278.add_current=_orig_add_current
 long=add_start_features(long)
 art=load_artifact(); sf=list(art["v283_SECOND"]["features"]);cf=list(art["v283_COND_THIRD"]["features"])
 # PH5 LIVE head probability: rolling-origin fit, never a future-month frozen artifact.
 # Exact PH5 feature family = v93 base features + five causal boat-4 PLAYER_HISTORY features.
 truth0=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str},usecols=["race_code","head4"])
 truth0.race_code=truth0.race_code.astype(str).str.zfill(12)
 hz=v_all.copy(); hz["month"]=hz.race_code.str[:4]+"-"+hz.race_code.str[4:6]
 hz=hz.merge(truth0,on="race_code",how="left",validate="one_to_one")
 oldph=[c for c in hz if "_pl_" in c]
 if oldph: hz=hz.drop(columns=oldph)
 hz=hz.merge(phsrc.build_ph(),on="race_code",how="left",validate="one_to_one")
 forb=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 num=[c for c in hz if c not in {"head4","race_code","month"} and pd.to_numeric(hz[c],errors="coerce").notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forb)]
 base=[c for c in num if "_pl_" not in c and not c.startswith("w10_") and not c.startswith("opp_waku_b")]
 ph5=["b4_pl_all_win","b4_pl_all_p2","b4_pl_frame_win","b4_pl_frame_p2","b4_pl_recent_p2"]
 fs=base+ph5
 if len(fs)!=35: raise RuntimeError(f"PH5_FEATURE_COUNT_{len(fs)}")
 hm={}
 rolls=[("2026-06",["2026-03","2026-04","2026-05"]),("2026-07",["2026-03","2026-04","2026-05","2026-06"]),("2026-08",["2026-03","2026-04","2026-05","2026-06","2026-07"])]
 for test,trm in rolls:
  tr=hz[hz.month.isin(trm)&hz.head4.isin([0,1])]; te=hz[hz.month.eq(test)]
  mdl=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))])
  mdl.fit(tr[fs],tr.head4); pp=mdl.predict_proba(te[fs])[:,1]
  hm.update(dict(zip(te.race_code,pp)))
 print("PH5_WALKFORWARD_HEAD_SCORES",len(hm),"features",len(fs))
 om=od3(); motors=motor_priors(); parent_snap=monitoring_parent_snapshots(); live_wall_ready=historical_live_wall_ready()
 nf=json.loads((ROOT/"artifacts/head4_newfeature_fixed156_production.json").read_text())
 refs=nf["ecdf_sorted_reference"]; weights=nf["weights"]; thr=float(nf["production_threshold"]); missing=float(nf.get("score_transform",{}).get("missing_value_rank",.5))
 pre=strict.set_index("race_code"); decisions=[]
 for code,g in long.groupby("race_code"):
  if code not in hm or code not in om:continue
  sr=[]
  for _,r in g.iterrows():
   x={"boat":int(r.boat)}
   for f in sf:
    if f not in r:raise RuntimeError(f"SECOND_FEATURE_MISSING_{f}")
    x[f]=r[f]
   sr.append(x)
  p2=score_second(sr,art);pc=score_conditional_third(v283build.conditional_rows(g,sf,cf),art)
  tickets=live.production_tickets(p2,pc); ovs=[om[code][t] for t in tickets]; comp=live.composite_odds(ovs)
  pairs=[tuple(map(int,t.split("-")[1:])) for t in tickets]
  mass=0.0; allj={}
  for s in BOATS:
   for t in BOATS:
    if s!=t:allj[(s,t)]=math.exp(.60*math.log(max(p2[s],1e-12))+.40*math.log(max(pc[(s,t)],1e-12)))
  den=sum(allj.values());mass=sum(allj[x]/den for x in pairs)
  hp=float(hm[code]); rr=pre.loc[code]; st=float(rr.st4_adv_inside);orig=float(rr.orig4_adv_inside)
  old164=(st>=-.6000000000000001 and orig>=-.057777777777777706)
  baseformula=(comp>=7 and mass>=.425) or (comp<7 and hp>=.22 and mass>=.375 and comp>=3)
  base120=old164 and (baseformula or (comp>=2.5 and hp+1.5*mass>=.82))
  by={int(r.boat):r for _,r in g.iterrows()};b3=by[3];b4=by.get(4)
  # Boat 4 row is not in opponent long table; derive head current values from opponent scenario h4_* columns.
  h4={k:ff(g.iloc[0].get("h4_"+k)) for k in ("cur_ex","cur_st","cur_orig_straight","cur_orig_avg")}
  transformed_wall_ready=all(math.isfinite(x) for x in h4.values()) and all(math.isfinite(ff(b3.get(k))) for k in ("cur_ex","cur_st","cur_orig_straight","cur_orig_avg"))
  wall_ready=bool(live_wall_ready.get(code,False) and transformed_wall_ready)
  attack4=(.20*h4["cur_ex"]+.40*h4["cur_st"]+.25*h4["cur_orig_straight"]+.15*h4["cur_orig_avg"]) if wall_ready else None
  exgap=(ff(b3.get("cur_ex"))-h4["cur_ex"]) if wall_ready else None
  stgap=(ff(b3.get("cur_st"))-h4["cur_st"]) if wall_ready else None
  straightgap=(ff(b3.get("cur_orig_straight"))-h4["cur_orig_straight"]) if wall_ready else None
  avggap=(ff(b3.get("cur_orig_avg"))-h4["cur_orig_avg"]) if wall_ready else None
  wall=(.20*exgap+.40*stgap+.25*straightgap+.15*avggap) if wall_ready else None
  mp=motors.get(code,{3:None,4:None}); md=(mp.get(4)-mp.get(3)) if mp.get(4) is not None and mp.get(3) is not None else None
  # card motor 2-ren difference
  ds=f"{code[:4]}/{code[4:6]}/{code[6:8]}"; cards={rc(x.get("レースコード","")):x for x in rows(f"data/programs/race_cards/{ds}.csv")};card=cards.get(code,{})
  m2d=ff(card.get("艇4_モーター2連対率"))-ff(card.get("艇3_モーター2連対率"))
  raw={"hp":hp,"mass":mass,"st":st,"orig":orig,"market_conf":-math.log(max(comp,1e-12)),
       "motor_win_rev":(-md if md is not None else None),"motor_2ren_rev":(-m2d if math.isfinite(m2d) else None),
       "attack4":attack4,"stwall_center":(-abs(stgap-.10) if stgap is not None else None),"wall_rev":(-wall if wall is not None else None)}
  score=sum(float(weights[k])*ecdf(raw.get(k),refs.get(k) or [],missing) for k in weights)
  expansion=(not base120) and st>=-.80 and orig>=-.35 and score>=thr
  selected=bool(hp>=.36 and orig>=-.06)
  pm=parent_snap.get(code,{"monitoring_parent":0,"parent_feature_missing":1,
                           "parent_motor_win_diff_4v3":float("nan"),"parent_motor_2ren_diff_4v3":float("nan"),
                           "parent_player4_all_win_prior":float("nan")})
  open_risk=max(0.0,-float(wall)) if wall_ready and wall is not None else 0.0
  shadow_quality=float(hp)+1.50*float(mass)+.10*open_risk
  # Exact Sep-25 rescue semantics: only races missed by the frozen base120 gate are rescue candidates.
  # Do NOT use PH5 standard selected/pass here; that broadened the historical rescue universe.
  shadow=bool(pm["monitoring_parent"] and (not selected) and (not base120) and wall_ready and comp>=2.5 and open_risk>0 and shadow_quality>=.82)
  stakes=live.dutch(tickets,ovs) if selected else [{"combo":t,"odds":o,"stake":0} for t,o in zip(tickets,ovs)]
  rescue_dutch_feasible=True
  if shadow:
   try:
    rescue_plan=live.dutch(tickets,ovs)
   except RuntimeError:
    rescue_dutch_feasible=False
    rescue_plan=[{"combo":t,"odds":o,"stake":0} for t,o in zip(tickets,ovs)]
  else:
   rescue_plan=[{"combo":t,"odds":o,"stake":0} for t,o in zip(tickets,ovs)]
  srank=sorted(BOATS,key=lambda s:(-float(p2[s]),s))
  third_rank={s:sorted((t for t in BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t)) for s in BOATS}
  oppdiag={"p2":{str(s):float(p2[s]) for s in BOATS},"pc":{f"{s}>{t}":float(pc[(s,t)]) for s in BOATS for t in BOATS if t!=s},
           "second_rank":srank,"third_rank":{str(s):third_rank[s] for s in BOATS},
           "second_gap12":float(p2[srank[0]]-p2[srank[1]]),"second_gap23":float(p2[srank[1]]-p2[srank[2]])}
  decisions.append({"date":str(rr.date),"race_code":code,"jcd":code[8:10],"rno":int(code[10:12]),"head_prob":hp,"mass":mass,"comp":comp,
   "orig4_adv_inside":orig,"wall_ready":int(wall_ready),"wall_ex_gap":exgap,"wall_st_gap":stgap,"wall_straight_gap":straightgap,"wall_avg_gap":avggap,"attack4_score":attack4,"wall_score":wall,"open_risk":open_risk,"shadow_quality":shadow_quality,
   "monitoring_parent":int(pm["monitoring_parent"]),"parent_feature_missing":int(pm["parent_feature_missing"]),
   "parent_motor_win_diff_4v3":pm["parent_motor_win_diff_4v3"],"parent_motor_2ren_diff_4v3":pm["parent_motor_2ren_diff_4v3"],
   "parent_player4_all_win_prior":pm["parent_player4_all_win_prior"],
   "old164":int(old164),"baseformula":int(baseformula),"rescue082":int(old164 and comp>=2.5 and hp+1.5*mass>=.82),"base120":int(base120),"newfeature_add":int(expansion),"selected":int(selected),"shadow":int(shadow),"production_bet":int(selected),
   "tickets":"|".join(tickets),"ticket_count":len(tickets),"stake":sum(x["stake"] for x in stakes),"stake_plan":json.dumps(stakes,ensure_ascii=False),
   "rescue_dutch_feasible":int(rescue_dutch_feasible),"rescue_stake":sum(x["stake"] for x in rescue_plan),"rescue_stake_plan":json.dumps(rescue_plan,ensure_ascii=False),"nf_score":score,
   "opponent_diag":json.dumps(oppdiag,ensure_ascii=False)})
 d=pd.DataFrame(decisions)
 if not len(d):raise RuntimeError("NO_SIX_MONTH_DECISIONS")
 # Month-by-month volume funnel. This diagnoses coverage/gate loss without reading outcomes.
 funnel=[]
 for mon in ("2026-06","2026-07","2026-08"):
  key=mon.replace("-","")
  scored={c for c in hm if c.startswith(key)}
  hp36={c for c in scored if hm[c]>=.36}
  hp36od={c for c in hp36 if c in om}
  dm=d[d.date.str[:7].eq(mon)]
  parent=dm.monitoring_parent.eq(1); passed=parent & dm.selected.eq(0) & dm.base120.eq(0); ready=passed & dm.wall_ready.eq(1)
  opened=ready & dm.open_risk.gt(0); compok=opened & dm.comp.ge(2.5); quality=compok & dm.shadow_quality.ge(.82)
  funnel.append({"month":mon,"v93_R":int((v.race_code.str.startswith(key)).sum()),"ph5_scored_R":len(scored),
   "ph5_ge036_R":len(hp36),"ph5_ge036_odds_R":len(hp36od),"odds_decision_R":len(dm),
   "monitoring_parent_R":int(parent.sum()),"ph5_and_base120_pass_R":int(passed.sum()),
   "live_wall_ready_parent_pass_R":int(ready.sum()),"wall_open_parent_pass_R":int(opened.sum()),
   "comp250_parent_pass_R":int(compok.sum()),"quality082_parent_pass_R":int(quality.sum()),
   "rescue_R":int(dm.shadow.sum()),"selected_R":int(dm.selected.sum()),
   "base120_R":int(dm.base120.sum()),"newfeature_add_R":int(dm.newfeature_add.sum())})
 (OUT/"volume_funnel.json").write_text(json.dumps(funnel,ensure_ascii=False,indent=2)+"\n")
 print("VOLUME_FUNNEL",json.dumps(funnel,ensure_ascii=False))
 # Freeze complete. Only now join truth.
 tr=truth(); missing_truth=set(d.race_code)-set(tr)
 # A missing top-3 result means 3連単 was not established. Refund the race stake.
 pays=[];hits=[];head=[]
 for _,r in d.iterrows():
  a=tr.get(r.race_code); head.append(int(a is not None and a[0]==4)); actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
  plan=json.loads(r.stake_plan); hit=0
  pay=float(r.stake) if (r.production_bet and r.race_code in missing_truth) else 0.0
  if r.production_bet and actual:
   for x in plan:
    if x["combo"]==actual and int(x["stake"])>0:hit=1;pay=float(x["stake"])*float(x["odds"])
  hits.append(hit);pays.append(pay)
 d["head4"]=head;d["hit"]=hits;d["payout"]=pays;d["profit"]=d.payout-d.stake
 # Exact current LIVE wall3 rescue settlement, joined only after all shadow decisions are frozen.
 rh=[]; rp=[]; rep=[]; ree=[]
 for _,r in d.iterrows():
  a=tr.get(r.race_code); actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
  plan=json.loads(r.rescue_stake_plan); hh=0; pay=0.0; eqpay=0.0
  ticket_list=str(r.tickets).split("|") if str(r.tickets) else []
  odds_list=[om[r.race_code][t] for t in ticket_list]
  if int(r.shadow)==1 and actual:
   hh=int(actual in ticket_list)
   if int(r.rescue_dutch_feasible)==1:
    for x in plan:
     if x["combo"]==actual and int(x["stake"])>0:
      pay=float(x["stake"])*float(x["odds"])
   n=len(ticket_list); base=(BANK//(100*n))*100; est=[base]*n; rem=(BANK-sum(est))//100
   for i in range(min(rem,n)): est[i]+=100
   for i,t in enumerate(ticket_list):
    if t==actual: eqpay=float(est[i])*float(odds_list[i])
  rh.append(hh); rp.append(pay); rep.append(eqpay); ree.append(BANK if int(r.shadow)==1 else 0)
 d["rescue_hit"]=rh; d["rescue_payout_dutch"]=rp; d["rescue_payout_equal"]=rep; d["rescue_equal_stake"]=ree
 # Outcome is joined only after all decisions are frozen. Classify opponent misses for research.
 miss_rows=[]
 for _,r in d[(d.production_bet==1)&(d.head4==1)].iterrows():
  a=tr.get(r.race_code)
  if not a: continue
  s,t=int(a[1]),int(a[2]); z=json.loads(r.opponent_diag); sr=[int(x) for x in z["second_rank"]]; trk=[int(x) for x in z["third_rank"][str(s)]]
  ticketset=set(str(r.tickets).split("|"))
  if s not in sr[:2]: reason="SECOND_OUTSIDE_TOP2"
  elif t not in trk[:2] and f"4-{s}-{t}" not in ticketset: reason="THIRD_OUTSIDE_SELECTED"
  elif f"4-{s}-{t}" not in ticketset: reason="PAIR_CONSTRUCTION_MISS"
  else: reason="COVERED"
  miss_rows.append({"race_code":r.race_code,"date":r.date,"jcd":r.jcd,"actual_second":s,"actual_third":t,"reason":reason,
                    "second_rank":sr.index(s)+1,"second_gap_to_top2":max(0.0,float(z["p2"][str(sr[1])])-float(z["p2"][str(s)])),
                    "third_rank":trk.index(t)+1,"third_gap_to_top2":max(0.0,float(z["pc"][f"{s}>{trk[1]}"])-float(z["pc"][f"{s}>{t}"]))})
 oppmiss=pd.DataFrame(miss_rows)
 if len(oppmiss):
  oppmiss.to_csv(OUT/"opponent_miss_decomposition.csv",index=False)
  print("OPPONENT_MISS_COUNTS",json.dumps(oppmiss.reason.value_counts().to_dict(),ensure_ascii=False))
  print("OPPONENT_RANK_COUNTS",json.dumps({"second":oppmiss.second_rank.value_counts().sort_index().to_dict(),"third":oppmiss.third_rank.value_counts().sort_index().to_dict()},ensure_ascii=False))
 # Fast counterfactual grid: reuse frozen p2/pc/odds already computed; no model refit/rebuild per threshold.
 grid=[]
 for sg in (0.06,0.07,0.08,0.09,0.10,0.11,0.12,0.13,0.14):
  for tg in (0.14,0.16,0.18,0.20,0.22,0.24):
   stake=pay=hits=pts=0; eval_rows=[]
   for _,r in d[d.production_bet==1].iterrows():
    z=json.loads(r.opponent_diag); sr=[int(x) for x in z["second_rank"]]; tr0=str(r.tickets).split("|"); ts=list(tr0)
    # add SECOND rank3 only when close to rank2; give it top2 THIRDs
    s3=sr[2]; s2=sr[1]
    if float(z["p2"][str(s2)])-float(z["p2"][str(s3)])<=sg:
     for t in [int(x) for x in z["third_rank"][str(s3)]][:2]:
      x=f"4-{s3}-{t}"
      if x not in ts: ts.append(x)
    # for every selected SECOND, add THIRD rank3 when close to rank2
    secs=sorted({int(x.split("-")[1]) for x in ts})
    for s in secs:
     trk=[int(x) for x in z["third_rank"][str(s)]]
     if float(z["pc"][f"{s}>{trk[1]}"])-float(z["pc"][f"{s}>{trk[2]}"])<=tg:
      x=f"4-{s}-{trk[2]}"
      if x not in ts: ts.append(x)
    ovs=[om[r.race_code][x] for x in ts]
    # Counterfactual can exceed production helper's 4..6 ticket invariant.
    # Preserve JPY10k inverse-odds Dutch semantics with JPY100 Hamilton rounding for any feasible ticket count.
    inv=np.asarray([1.0/max(float(o),1e-12) for o in ovs],dtype=float); raw=BANK*inv/inv.sum()
    units=np.floor(raw/100.0).astype(int); remain=BANK//100-int(units.sum())
    frac=raw/100.0-units
    for ii in np.argsort(-frac)[:remain]: units[ii]+=1
    # Every added ticket must receive a positive stake; otherwise this threshold is not feasible at JPY10k.
    if np.any(units<=0):
     plan=[]; st=0
    else:
     plan=[{"combo":t,"odds":float(o),"stake":int(u*100)} for t,o,u in zip(ts,ovs,units)]
     st=sum(x["stake"] for x in plan)
    stake+=st; pts+=len(ts)
    a=tr.get(r.race_code); actual=f"{a[0]}-{a[1]}-{a[2]}" if a else ""
    pp=st if (not a) else 0.0; hh=0
    for x in plan:
     if actual and x["combo"]==actual: pp=float(x["stake"])*float(x["odds"]); hh=1
    pay+=pp; hits+=hh; eval_rows.append({"date":str(r.date),"jcd":str(r.race_code)[:2],"hit":hh,"stake":st,"payout":pp,"base120":int(r.get("base120",0)),"newfeature":int(r.get("newfeature_add",0))})
   R=int((d.production_bet==1).sum()); expected=R*BANK; feasible=(stake==expected); rr=pd.DataFrame(eval_rows)
   monthly=[]; venue=[]; maxdd=0.0; maxls=0
   if len(rr):
    rr["month"]=rr.date.str[:7]; rr["profit"]=rr.payout-rr.stake; eq=rr.profit.cumsum(); maxdd=float((eq.cummax()-eq).max()); cur=0
    for h in rr.hit: cur=0 if h else cur+1; maxls=max(maxls,cur)
    monthly=[{"month":m,"R":len(g),"hits":int(g.hit.sum()),"roi":100*g.payout.sum()/g.stake.sum()} for m,g in rr.groupby("month")]
    venue=[{"jcd":m,"R":len(g),"hits":int(g.hit.sum()),"roi":100*g.payout.sum()/g.stake.sum()} for m,g in rr.groupby("jcd")]
   grid.append({"second_gap":sg,"third_gap":tg,"R":R,"hits":hits,"avg_points":pts/max(1,R),
                "stake":stake,"expected_stake":expected,"all_races_feasible":feasible,
                "payout":pay,"profit":pay-stake,"roi":100*pay/stake if feasible and stake else None,
                "max_drawdown":maxdd,"max_losing_streak":maxls,"monthly":monthly,"venue":venue})
 pd.DataFrame(grid).sort_values(["roi","hits"],ascending=[False,False]).to_csv(OUT/"opponent_gap_grid.csv",index=False)
 valid=[x for x in grid if x["all_races_feasible"] and x["roi"] is not None]
 print("OPPONENT_GAP_GRID_TOP",json.dumps(sorted(valid,key=lambda x:(x["roi"],x["hits"]),reverse=True)[:10],ensure_ascii=False))
 print("OPPONENT_GAP_GRID_INVALID",sum(not x["all_races_feasible"] for x in grid))
 print("OPPONENT_GAP_GRID_TOP_DETAIL",json.dumps(sorted(valid,key=lambda x:(x["roi"],x["hits"]),reverse=True)[:5],ensure_ascii=False))
 b=d[d.production_bet==1].copy().sort_values(["date","race_code"])
 equity=b.profit.cumsum(); peak=equity.cummax().clip(lower=0); dd=peak-equity
 loss=mx=0
 for x in b.hit:
  loss=loss+1 if not x else 0;mx=max(mx,loss)
 venue=b.groupby("jcd").agg(R=("race_code","size"),stake=("stake","sum"),payout=("payout","sum"),profit=("profit","sum"),hits=("hit","sum"),base120=("base120","sum"),newfeature_add=("newfeature_add","sum")).reset_index();venue["roi"]=100*venue.payout/venue.stake
 daily=b.groupby("date").agg(R=("race_code","size"),stake=("stake","sum"),payout=("payout","sum"),profit=("profit","sum")).reset_index();daily["roi"]=100*daily.payout/daily.stake
 out={"strict_R":len(strict),"decision_R":len(d),"production_BET_R":len(b),"shadow_selected_R":int(((d.selected==1)&(d.shadow==1)).sum()),
      "bet_per_day_mean":float(daily.R.mean()),"bet_per_day_median":float(daily.R.median()),"bet_per_day_max":int(daily.R.max()),
      "head4":int(b.head4.sum()),"hits":int(b.hit.sum()),"stake":int(b.stake.sum()),"payout":float(b.payout.sum()),"profit":float(b.profit.sum()),
      "roi":float(100*b.payout.sum()/b.stake.sum()),"max_drawdown":float(dd.max()),"max_losing_streak":int(mx),
      "base120_BET_R":int((b.base120==1).sum()),"newfeature_add_BET_R":int((b.newfeature_add==1).sum()),"trifecta_not_established_R":int(len(missing_truth)),"trifecta_not_established_BET_R":int(b.race_code.isin(missing_truth).sum()),
      "walk_forward":True,"PH5_C":.5,"PH5_cut":.36,"PRODUCTION_CHANGED":False}
 d.to_csv(OUT/"race_detail.csv",index=False);daily.to_csv(OUT/"daily.csv",index=False);venue.to_csv(OUT/"venue.csv",index=False)
 monthly=b.groupby(b.date.str[:7]).agg(R=("race_code","size"),head4=("head4","sum"),hits=("hit","sum"),stake=("stake","sum"),payout=("payout","sum"),profit=("profit","sum")).reset_index().rename(columns={"date":"month"});monthly["head_rate"]=100*monthly.head4/monthly.R;monthly["roi"]=100*monthly.payout/monthly.stake;monthly.to_csv(OUT/"monthly.csv",index=False)
 out_monthly=monthly.to_dict("records")
 # Diagnose why current LIVE base120 is much broader than the frozen 120R research sample.
 diag={k:int(b[k].sum()) for k in ("old164","baseformula","rescue082","base120","newfeature_add")}
 diag["base120_via_baseformula_R"]=int(((b.base120==1)&(b.baseformula==1)).sum())
 diag["base120_via_rescue_only_R"]=int(((b.base120==1)&(b.baseformula==0)&(b.rescue082==1)).sum())
 diag["base120_headprob_lt018_R"]=int(((b.base120==1)&(b.head_prob<.18)).sum())
 diag["base120_headprob_ge018_R"]=int(((b.base120==1)&(b.head_prob>=.18)).sum())
 (OUT/"base120_diagnostic.json").write_text(json.dumps(diag,ensure_ascii=False,indent=2)+"\n")
 print("BASE120_DIAGNOSTIC",json.dumps(diag,ensure_ascii=False))
 rescue=d[d.shadow.eq(1)].copy()
 rmonthly=[]
 for mo,g in rescue.groupby(rescue.date.str[:7]):
  gf=g[g.rescue_dutch_feasible.eq(1)]
  st=int(gf.rescue_stake.sum()); dst=float(gf.rescue_payout_dutch.sum()); est=int(g.rescue_equal_stake.sum()); ep=float(g.rescue_payout_equal.sum())
  rmonthly.append({"month":mo,"R":int(len(g)),"head4":int(g.head4.sum()),"head4_rate":100*float(g.head4.mean()),"exact3":int(g.rescue_hit.sum()),
                   "exact3_rate":100*float(g.rescue_hit.mean()) if len(g) else None,
                   "dutch_feasible_R":int(len(gf)),"dutch_infeasible_R":int(len(g)-len(gf)),
                   "dutch_stake":st,"dutch_payout":dst,"dutch_roi_feasible_only":100*dst/st if st else None,
                   "equal_stake":est,"equal_payout":ep,"equal_roi":100*ep/est if est else None})
 rf=rescue[rescue.rescue_dutch_feasible.eq(1)]
 rst=int(rf.rescue_stake.sum()); rdst=float(rf.rescue_payout_dutch.sum()); rest=int(rescue.rescue_equal_stake.sum()); rep=float(rescue.rescue_payout_equal.sum())
 rescue_out={"profile":"HEAD4_WALL3_OPEN_RESCUE_SHADOW_V1_BETA010_Q082_COMP250",
             "period":"2026-06..2026-08","monitoring_parent_replayed_exactly":True,
             "R":int(len(rescue)),"head4":int(rescue.head4.sum()),"head4_rate":100*float(rescue.head4.mean()) if len(rescue) else None,
             "exact3":int(rescue.rescue_hit.sum()),"exact3_rate":100*float(rescue.rescue_hit.mean()) if len(rescue) else None,
             "dutch_feasible_R":int(len(rf)),"dutch_infeasible_R":int(len(rescue)-len(rf)),
             "dutch_stake":rst,"dutch_payout":rdst,"dutch_roi_feasible_only":100*rdst/rst if rst else None,
             "equal_stake":rest,"equal_payout":rep,"equal_roi":100*rep/rest if rest else None,
             "dutch_note":"exact production Dutch can be infeasible when a ticket would receive < JPY100; infeasible races excluded from Dutch ROI only",
             "monthly":rmonthly,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 rescue.to_csv(OUT/"wall3_live_rescue_3m_detail.csv",index=False)
 (OUT/"wall3_live_rescue_3m_result.json").write_text(json.dumps(rescue_out,ensure_ascii=False,indent=2)+"\n")
 print("WALL3_LIVE_RESCUE_3M",json.dumps(rescue_out,ensure_ascii=False))
 out["wall3_live_rescue_3m"]=rescue_out
 out["monthly"]=out_monthly; out["closing_odds_used"]=True; out["predeadline_od3_preferred"]=True; out["waku10_backfill_used"]=False; (OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False,indent=2));print(monthly.to_string(index=False));print(venue.to_string(index=False));print("HEAD4_PH5_LIVE_WALKFORWARD_OK")
if __name__=="__main__":main()
