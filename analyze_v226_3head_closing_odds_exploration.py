#!/usr/bin/env python3
"""v226 EXPLORATORY ONLY: intentionally use historical closing odds for buy/skip and TopN selection.
This violates the normal settlement-only odds rule by explicit user exception. Results are discovery evidence only.
Clean model-data window Dec2025-Jun2026; Jul/Aug excluded. v224 head + v221 pair. Exact 10k Hamilton Dutch.
"""
from pathlib import Path
import numpy as np,pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
ROOT=Path(__file__).resolve().parent;SRC=ROOT/'analysis_v108_1head_feasibility.csv';OUT=ROOT/'analysis_v226_3head_closing_odds_exploration.csv';SUM=ROOT/'summary_v226_3head_closing_odds_exploration.md';CONTAM=pd.Timestamp('2026-07-01');BANK=10000
NS=list(range(4,16));COMP_CUTS=[0,2.0,2.25,2.5,2.75,3.0,3.25,3.5,4.0];EV_CUTS=[0,0.90,1.0,1.05,1.10,1.15,1.20]
def uniq(x):return list(dict.fromkeys([c for c in x if c]))
def main():
 raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);base=v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy();d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=v224.add_decomp(d,dc)
 hist=v222.cols(d,'b3_vh_');rel=[c for c in d if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))];cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]+[c for c in d if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))];form=[c for c in d if c.startswith(('f_b3_m1_','f_b3_m12_','f_b3_m35_','f_b3_trend_','f_rel_'))]+[c for c in ['f_b3_layoff','f_b3_grade','f_b3_m1_grade'] if c in d];fs=uniq(list(base)+hist+cur+rel+form)
 odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);race=[]
 for mon in v223.EVAL_MONTHS:
  first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1);pair=v222.fit_pair(d[d._date<first],'V221');bte,_=v223.fit_head(d,list(base),vc,first,nxt);k=max(1,int((bte._p>=.30).sum()));te,_=v223.fit_head(d,fs,vc,first,nxt);sel=te.nlargest(k,'_p')
  # prior-only empirical conditional TopN coverage, used only for probability estimate; odds are not involved here.
  tr=d[d._date<first];cov={}
  for n in NS:
   vals=[]
   for _,r in tr[tr._y==1].iterrows():
    ts=v222.order(r,pair,'V221');act=v222.v166.combo(r.get('actual_combo'));a='-'.join(map(str,act)) if len(act)==3 else '';vals.append(int(a in ts[:n]))
   cov[n]=float(np.mean(vals)) if vals else np.nan
  for _,r in sel.iterrows():
   code=str(r.get('race_code','')).zfill(12);act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual or code not in oi.index:continue
   o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o;ts=v222.order(r,pair,'V221')
   for n in NS:
    tickets=ts[:n];vals=[]
    try: vals=[float(o[t]) for t in tickets]
    except: continue
    if len(vals)!=n or any((not np.isfinite(x) or x<=0) for x in vals):continue
    st=v205.round_dutch(vals,BANK);fund=bool((st>=100).all());comp=1/sum(1/x for x in vals);hit=int(actual in tickets and st[tickets.index(actual)]>0) if actual in tickets else 0;ret=float(st[tickets.index(actual)]*vals[tickets.index(actual)]) if hit else 0.;ph=float(r._p);est=ph*cov[n] if np.isfinite(cov[n]) else np.nan;ev=est*comp if np.isfinite(est) else np.nan
    race.append({'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'n':n,'p3':ph,'prior_cov':cov[n],'est_hit':est,'comp':comp,'ev':ev,'fully_funded':fund,'hit':hit,'ret':ret,'profit':ret-BANK})
 z=pd.DataFrame(race);z.to_csv(OUT,index=False);z=z[z.fully_funded].copy();rows=[]
 def stat(label,g):
  if g.empty:return
  cost=len(g)*BANK;ret=g.ret.sum();rows.append((label,len(g),100*g.hit.mean(),g.comp.mean(),g.ev.mean(),100*ret/cost,(g.profit.cumsum().cummax()-g.profit.cumsum()).max()))
 for n in NS:stat(f'FIXED Top{n}',z[z.n==n])
 z10=z[z.n==10]
 for c in COMP_CUTS:stat(f'Top10 comp>={c}',z10[z10.comp>=c])
 for c in EV_CUTS:stat(f'Top10 EV>={c}',z10[z10.ev>=c])
 # Per-race choose N maximizing estimated EV, then optional EV gates.
 ix=z.groupby('race_code').ev.idxmax();best=z.loc[ix]
 stat('BEST_N maxEV all',best)
 for c in EV_CUTS[1:]:stat(f'BEST_N maxEV EV>={c}',best[best.ev>=c])
 L=['# v226 closing-odds exploration','', '**EXPLORATORY / CONTAMINATED BY DESIGN:** historical closing odds are intentionally used for buy/skip and point-count selection. Do not treat these ROI figures as pristine validation or production evidence.','- Model-data evaluation: Dec2025-Jun2026 only; Jul/Aug excluded.','- v224 head + v221 pair; exact 10,000-yen Hamilton Dutch; zero-stake TopN candidates excluded.','- Estimated hit = monthly prior-only p3 probability × prior-only conditional TopN coverage.','', '|rule|R|hit|avg comp|avg est EV|ROI|maxDD|','|---|---:|---:|---:|---:|---:|---:|']
 rows.sort(key=lambda x:-x[5])
 for a in rows:L.append(f'|{a[0]}|{a[1]}|{a[2]:.2f}%|{a[3]:.3f}|{a[4]:.3f}|{a[5]:.2f}%|{a[6]:.0f}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
