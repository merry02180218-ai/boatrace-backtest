#!/usr/bin/env python3
"""v212: reconsider v166 opponent ranking for the new ROI definition.

Selection/gate stays v165 p3head>=.30. For each target month the direct pair model is
trained only on earlier dates. Candidate ticket ranking variants are chosen on July
only, then reported on August with the same frozen rule. Current-race odds are used
ONLY after ranking to settle fixed ¥10,000 inverse-odds Dutch stakes; they never rank tickets.
User-approved unified odds: BoatraceCSV od3 preferred, corrected official closing fallback.
SHADOW only because July/August have already been inspected in project history.
"""
from pathlib import Path
from datetime import date
import math, numpy as np, pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as oddsmod
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v212_3head_pair_dutch10k_search.csv'; SUM=ROOT/'summary_v212_3head_pair_dutch10k_search.md'
MONTHS=['2026-07','2026-08']; LAMS=[0,.25,.5,.75,1.0]; NS=[5,6,7,8,9,10,11,12]; CUT=.30; BANK=10000

def round_dutch(vals):return oddsmod.round_dutch(vals,BANK)
def settle(top,actual,o):
    vals=[]
    for t in top:
      try:v=float(o[t])
      except:return None
      if not np.isfinite(v) or v<=0:return None
      vals.append(v)
    st=round_dutch(vals);ret=0.;hit=0
    if actual in top:
      i=top.index(actual)
      if st[i]>0:ret=float(st[i])*vals[i];hit=1
    return hit,1/sum(1/x for x in vals),ret,int((st==0).sum())

def main():
    src_path,df=v165.load();dc=v165.pc(df,['date','race_date','ymd']);vc=v165.pc(df,['venue','jcd','stadium','place']);y,_=v165.target(df);fs=v165.feats(df)
    d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y;d=d[d._date.notna()&d._y.notna()].copy()
    src=v166.read(str(ROOT/'analysis_v108_1head_feasibility.csv'));od=oddsmod.load_odds();oi=od.set_index('race_code',drop=False)
    rows=[]
    for mon in MONTHS:
      m=pd.Timestamp(mon+'-01');e=m+pd.offsets.MonthBegin(1);tr=d[d._date<m].copy();te=d[(d._date>=m)&(d._date<e)].copy()
      nums=[]
      for c in fs:
        q=pd.to_numeric(d[c],errors='coerce')
        if q.notna().mean()>=.8:tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
      cats=[vc] if vc and vc not in nums else [];hm=v165.model(nums,cats);hm.fit(tr[nums+cats],tr._y.astype(int));pp=hm.predict_proba(te[nums+cats])[:,1]
      pm,pn=v166.fit([r for r in src if date.fromisoformat(r['date'])<date.fromisoformat(mon+'-01')])
      for ix,p in zip(te.index,pp):
        if p<CUT:continue
        r=dict(src[int(ix)]);code=str(r.get('race_code','')).zfill(12)
        if v166.ii(r.get('course3'),3)!=3 or code not in oi.index:continue
        o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o;act=(r.get('actual_combo') or '').strip()
        for lam in LAMS:
          order=v166.order(r,pm,lam)
          for n in NS:
            z=settle(order[:n],act,o)
            if z is None:continue
            hit,comp,ret,zero=z;rows.append({'month':mon,'race_code':code,'p3head':p,'lambda':lam,'N':n,'hit':hit,'comp':comp,'return_yen':ret,'zero_stake':zero,'actual':act,'tickets':';'.join(order[:n]),'pair_train':pn,'odds_source':str(o.get('odds_source','unknown'))})
    z=pd.DataFrame(rows);z.to_csv(OUT,index=False)
    def agg(g):return {'R':len(g),'hit':100*g.hit.mean() if len(g) else 0,'comp':g.comp.mean() if len(g) else 0,'ret':g.return_yen.sum(),'roi':100*g.return_yen.sum()/(BANK*len(g)) if len(g) else 0}
    grid=[]
    for (lam,n),g in z[z.month=='2026-07'].groupby(['lambda','N']):
      a=agg(g);grid.append((a['roi'],a['hit'],a['R'],lam,n,a['comp']))
    # July discovery objective = realized Dutch ROI; tie hit, then fewer tickets.
    best=max(grid,key=lambda x:(x[0],x[1],-x[4]));bl,bn=best[3],best[4]
    L=['# v212 3-head opponent ranking under new Dutch10k ROI — SHADOW','', '- gate: exact monthly-WF v165 p3head>=.30; pair model trains only on earlier dates.','- ranking search: lambda {0,.25,.5,.75,1.0} x N {5..12}.','- July selects one rule by realized ¥10,000 Dutch ROI; same lambda/N frozen for August.','- odds never rank tickets; they are settlement-only after ticket set is frozen.','- unified odds: od3 preferred, corrected official closing fallback.','','## July discovery top rules','|rank|lambda|N|R|hit|avg comp|ROI|','|---:|---:|---:|---:|---:|---:|---:|']
    for k,x in enumerate(sorted(grid,reverse=True)[:12],1):L.append(f'|{k}|{x[3]:.2f}|{x[4]}|{x[2]}|{x[1]:.1f}%|{x[5]:.3f}|**{x[0]:.1f}%**|')
    L += ['',f'July selected: **lambda={bl:.2f}, N={bn}**','', '## Frozen August comparison','|rule|R|hit|avg comp|return|ROI|','|---|---:|---:|---:|---:|---:|']
    rules=[('v166 current lambda1 Top10',1.0,10),('July-selected',bl,bn)]
    # Include same-N lambda1 and Top10 at selected lambda to isolate N/ranking effects.
    rules += [('lambda1 same N',1.0,bn),('selected lambda Top10',bl,10)]
    seen=set()
    for name,lam,n in rules:
      key=(lam,n)
      if key in seen:continue
      seen.add(key);a=agg(z[(z.month=='2026-08')&(z['lambda']==lam)&(z.N==n)])
      L.append(f'|{name} ({lam:.2f},N{n})|{a["R"]}|{a["hit"]:.1f}%|{a["comp"]:.3f}|¥{a["ret"]:,.0f}|**{a["roi"]:.1f}%**|')
    L += ['','## Decision','- This is discovery/shadow, not adoption evidence; August has already been inspected.','- Production v166 lambda=1.00 Top10 remains unchanged until prospective validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
