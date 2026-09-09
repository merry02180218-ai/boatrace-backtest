#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_v229_3head_jul_aug_shadow as v229
import analyze_v205_3head_operational_replay as v205
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v230_v229_data_audit.csv'
SUM=ROOT/'summary_v230_v229_data_audit.md'
SRC=ROOT/'analysis_v108_1head_feasibility.csv'

def combo3(x):
    s=str(x or '').strip()
    a=s.split('-')
    return s if len(a)==3 and all(z in {'1','2','3','4','5','6'} for z in a) else ''

def market_p3(r):
    vals=[]; h=[]
    for a in range(1,7):
        for b in range(1,7):
            if b==a: continue
            for c in range(1,7):
                if c in (a,b): continue
                k=f'{a}-{b}-{c}'
                try:o=float(r.get(k,np.nan))
                except:o=np.nan
                if np.isfinite(o) and o>0:
                    w=1/o; vals.append(w)
                    if a==3:h.append(w)
    return float(sum(h)/sum(vals)) if vals and sum(vals)>0 else np.nan

def main():
    # Recreate v229 exactly first; do not change its selection logic.
    v229.main()
    z=pd.read_csv(v229.OUT,dtype={'race_code':str})
    src=pd.read_csv(SRC,dtype={'race_code':str},usecols=['race_code','actual_combo']).drop_duplicates('race_code',keep='last')
    z=z.merge(src,on='race_code',how='left')
    z['actual_combo']=z.actual_combo.map(combo3)
    z['head3']=z.actual_combo.str.startswith('3-').fillna(False).astype(int)

    off=v205.load_official(); od3=v205.load_od3()
    om=off.set_index('race_code',drop=False) if not off.empty else pd.DataFrame()
    dm=od3.set_index('race_code',drop=False) if not od3.empty else pd.DataFrame()
    rec=[]
    for _,r in z.iterrows():
        code=str(r.race_code).zfill(12)
        ro=om.loc[code] if (not om.empty and code in om.index) else None
        rd=dm.loc[code] if (not dm.empty and code in dm.index) else None
        if isinstance(ro,pd.DataFrame):ro=ro.iloc[-1]
        if isinstance(rd,pd.DataFrame):rd=rd.iloc[-1]
        # current v205 load_odds uses od3 whenever both exist
        used='od3' if rd is not None else ('official' if ro is not None else 'missing')
        mp3_od3=market_p3(rd) if rd is not None else np.nan
        mp3_off=market_p3(ro) if ro is not None else np.nan
        rec.append({**r.to_dict(),'has_official':int(ro is not None),'has_od3':int(rd is not None),'current_odds_source':used,
                    'market_p3_od3':mp3_od3,'market_p3_official':mp3_off,
                    'p3_minus_market_od3':float(r.p3)-mp3_od3 if np.isfinite(mp3_od3) else np.nan,
                    'p3_minus_market_official':float(r.p3)-mp3_off if np.isfinite(mp3_off) else np.nan})
    a=pd.DataFrame(rec)
    a.to_csv(OUT,index=False)

    L=['# v230 v229 data integrity audit','',
       '**Audit only. Jul/Aug remain NON-PRISTINE.**','',
       '## Core decomposition','|month|R|3-head actual|Top10 hit|pair coverage given 3-head|mean p3|','|---|---:|---:|---:|---:|---:|']
    for mon,g in a.groupby('month'):
        h=g[g.head3==1]; cov=100*h.hit.mean() if len(h) else 0
        L.append(f'|{mon}|{len(g)}|{100*g.head3.mean():.2f}%|{100*g.hit.mean():.2f}%|{cov:.2f}%|{g.p3.mean():.4f}|')
    h=a[a.head3==1]; L.append(f'|Jul+Aug|{len(a)}|{100*a.head3.mean():.2f}%|{100*a.hit.mean():.2f}%|{100*h.hit.mean() if len(h) else 0:.2f}%|{a.p3.mean():.4f}|')

    L += ['','## p3 calibration','|month|p3 bin|R|mean p3|actual 3-head|Top10 hit|','|---|---|---:|---:|---:|---:|']
    bins=[0,.4,.45,.5,.55,.6,.7,1.01]
    a['p3_bin']=pd.cut(a.p3,bins,right=False)
    for (mon,b),g in a.groupby(['month','p3_bin'],observed=True):
        L.append(f'|{mon}|{b}|{len(g)}|{g.p3.mean():.3f}|{100*g.head3.mean():.1f}%|{100*g.hit.mean():.1f}%|')

    L += ['','## Odds source audit','|month|R|od3 available|official available|both|current od3-used|','|---|---:|---:|---:|---:|---:|']
    for mon,g in a.groupby('month'):
        both=((g.has_od3==1)&(g.has_official==1)).sum()
        L.append(f'|{mon}|{len(g)}|{g.has_od3.sum()}|{g.has_official.sum()}|{both}|{(g.current_odds_source=="od3").sum()}|')

    L += ['','## Largest model-vs-market p3 gaps (od3 snapshot)','|date|race_code|model p3|market p3|gap|actual|hit|comp|','|---|---|---:|---:|---:|---|---:|---:|']
    q=a[np.isfinite(a.market_p3_od3)].sort_values('p3_minus_market_od3',ascending=False).head(20)
    for _,r in q.iterrows():
        L.append(f'|{r.date}|{r.race_code}|{r.p3:.3f}|{r.market_p3_od3:.3f}|{r.p3_minus_market_od3:.3f}|{r.actual_combo}|{int(r.hit)}|{r.comp:.3f}|')
    L += ['','## Notes',
          '- current v205/v229 odds merge chooses od3 when od3 and official closing both exist.',
          '- BoatraceCSV documents od3 as a usually ~5-min-before-deadline in-progress odds snapshot, not final closing odds.',
          '- Therefore any closing-odds threshold study must not label od3 values as final closing odds.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))
if __name__=='__main__': main()
