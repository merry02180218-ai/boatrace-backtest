#!/usr/bin/env python3
"""v198: long-history validation for current 3-head production and turn-margin gate.

Purpose: address possible Jul/Aug overfit by extending as far back as canonical v108 data allows.
For every test month, v165 and v166 are trained strictly on earlier dates. A rolling turn gate is chosen only from prior evaluated months.
No current/final odds or post-race info is used in prediction/ranking; payout is settlement-only.
"""
from pathlib import Path
from datetime import date
import pandas as pd, numpy as np
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
ROOT=Path(__file__).resolve().parent
CUT=.30; TOPN=10; LAM=1.0
TURN_CUTS=[-1.2,-1.0,-0.8,-0.6,-0.4,-0.2,0.0]

def ff(x,d=0.):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def combo(x):
    try:return [int(z) for z in str(x).replace(' ','').split('-')]
    except:return []

def met(g):
    if len(g)==0:return [0,0,0,0,0,0,0]
    h=g[g.y3head==1]; s=g[g.valid_payout==1]; cost=s.cost_yen.sum(); ret=s.return_yen.sum()
    return [len(g),100*g.y3head.mean(),100*g.hit.mean(),100*h.hit.mean() if len(h) else 0,cost,ret,100*ret/cost if cost else 0]
def fmt(name,g):
    m=met(g);return f'|{name}|{m[0]}|{m[1]:.2f}%|{m[2]:.2f}%|{m[3]:.2f}%|{m[4]:.0f}|{m[5]:.0f}|{m[6]:.1f}%|'

def choose_cut(hist):
    # conservative: require >=40 settled races, maximize ROI with head/hit tie-break, but never use current test month
    cand=[]
    for c in TURN_CUTS:
        g=hist[pd.to_numeric(hist.turn_margin23,errors='coerce')>=c]
        m=met(g)
        if m[0]>=40: cand.append((m[-1],m[2],m[1],-abs(c+0.8),c))
    return max(cand)[-1] if cand else -1.0

def main():
    src_path,df=v165.load(); dc=v165.pc(df,['date','race_date','ymd']); vc=v165.pc(df,['venue','jcd','stadium','place'])
    y,_=v165.target(df); fs=v165.feats(df)
    d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y; d=d[d._date.notna()&d._y.notna()].copy()
    src=v166.read(str(ROOT/'analysis_v108_1head_feasibility.csv'))
    if Path(src_path).name!='analysis_v108_1head_feasibility.csv': raise SystemExit(f'v165 source mismatch {src_path}')
    minm=d._date.min().to_period('M'); maxm=d._date.max().to_period('M')
    months=[str(x) for x in pd.period_range(minm,maxm,freq='M')]
    rows=[]; skipped=[]
    for mon in months:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1); tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy()
        if len(tr)<1000 or len(te)<100: skipped.append((mon,'insufficient rows')); continue
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        hm=v165.model(nums,cats); hm.fit(tr[nums+cats],tr._y.astype(int)); probs=hm.predict_proba(te[nums+cats])[:,1]
        pair_train=[r for r in src if date.fromisoformat(r['date'])<date.fromisoformat(mon+'-01')]
        try: pm,pair_n=v166.fit(pair_train)
        except Exception as ex: skipped.append((mon,str(ex))); continue
        for ix,p in zip(te.index,probs):
            if p<CUT: continue
            r=dict(src[int(ix)]); c3=ii(r.get('course3'),3)
            if c3!=3: continue
            ords=v166.order(r,pm,LAM); top=ords[:TOPN]; act=(r.get('actual_combo') or '').strip(); hit=int(act in top); valid=ii(r.get('valid_payout'))==1
            rows.append({'month':mon,'date':r.get('date'),'race_code':r.get('race_code'),'p3head':float(p),'turn_margin23':ff(r.get('turn_margin23')),'actual_combo':act,'y3head':int(combo(act)[:1]==[3]),'hit':hit,'valid_payout':int(valid),'return_yen':ff(r.get('payout100')) if hit and valid else 0.,'cost_yen':TOPN*100 if valid else 0,'pair_train_3wins':pair_n})
    o=pd.DataFrame(rows)
    if o.empty: raise SystemExit('no evaluable months')
    # rolling gate: first two evaluable months are observation only, then choose from all previous months
    eval_months=sorted(o.month.unique()); roll=[]
    for i,mon in enumerate(eval_months):
        g=o[o.month==mon].copy(); cut=np.nan
        if i>=2:
            hist=o[o.month.isin(eval_months[:i])]; cut=choose_cut(hist); g=g[pd.to_numeric(g.turn_margin23,errors='coerce')>=cut]
        g['rolling_cut']=cut; roll.append(g)
    ro=pd.concat(roll,ignore_index=True)
    o.to_csv(ROOT/'analysis_v198_3head_long_history_base.csv',index=False); ro.to_csv(ROOT/'analysis_v198_3head_long_history_rolling.csv',index=False)
    L=['# v198 3号艇 long-history validation','',f'- source range: {d._date.min().date()} .. {d._date.max().date()}',f'- evaluable months: {eval_months[0]} .. {eval_months[-1]} ({len(eval_months)} months)', '- production: v165 p3>=.30 -> v166 lambda1 -> Top10', '- rolling turn gate is selected only from earlier evaluated months', '- first two evaluable months are baseline-only warmup', '- Jul/Aug are NOT used to choose earlier cuts', '', '## Monthly BASE','|month|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for mon in eval_months:L.append(fmt(mon,o[o.month==mon]))
    L += ['','## Monthly rolling turn gate','|month|cut|R|3-head|hit|Top10 cov|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for i,mon in enumerate(eval_months):
        g=ro[ro.month==mon]; cut='warmup' if i<2 else f'{g.rolling_cut.iloc[0]:.3f}';m=met(g);L.append(f'|{mon}|{cut}|{m[0]}|{m[1]:.2f}%|{m[2]:.2f}%|{m[3]:.2f}%|{m[6]:.1f}%|')
    # pre-Jul/Aug aggregate, critical overfit check
    pre=o[o.month<'2026-07']; prer=ro[ro.month<'2026-07']; post=o[o.month>='2026-07']; postr=ro[ro.month>='2026-07']
    L += ['','## Critical split: before Jul/Aug','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|',fmt('PRE-Jul BASE',pre),fmt('PRE-Jul ROLLING',prer),fmt('Jul-Aug BASE',post),fmt('Jul-Aug ROLLING',postr)]
    # fixed cuts across pre-Jul only, descriptive stability table
    L += ['','## Fixed turn cuts on PRE-Jul only','|cut|R|3-head|hit|Top10 cov|ROI|','|---:|---:|---:|---:|---:|---:|']
    for c in TURN_CUTS:
        g=pre[pd.to_numeric(pre.turn_margin23,errors='coerce')>=c];m=met(g);L.append(f'|{c:.1f}|{m[0]}|{m[1]:.2f}%|{m[2]:.2f}%|{m[3]:.2f}%|{m[6]:.1f}%|')
    if skipped:
        L+=['','## Skipped months']+[f'- {a}: {b}' for a,b in skipped]
    (ROOT/'summary_v198_3head_long_history_validation.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
