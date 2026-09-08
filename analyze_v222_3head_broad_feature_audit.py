#!/usr/bin/env python3
"""v222: broad pre-Jul feature audit for redesigned 3-head chain.

Goal: search useful PRE-DEADLINE feature families without using Jul/Aug as evidence.
Evaluation: 2025-12..2026-06, strict monthly prior-only.
Historical closing odds are settlement-only. Fixed Top10 + exact 10k Hamilton Dutch.
No feature family is auto-adopted from this script.
"""
from __future__ import annotations
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
from backtest import rows,race_features,grade_score,clamp,pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v222_3head_broad_feature_audit.csv'
SUM=ROOT/'summary_v222_3head_broad_feature_audit.md'
EVAL_MONTHS=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
PRELOAD=date(2025,10,1);END=date(2026,6,30);CONTAM=pd.Timestamp('2026-07-01')
BANK=10000;OPP=[1,2,4,5,6]

def ff(x,d=0.):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def safe_auc(y,p):
    try:return float(roc_auc_score(y,p)) if len(set(map(int,y)))>1 else float('nan')
    except:return float('nan')
def safe_ll(y,p):
    try:return float(log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1]))
    except:return float('nan')

def day_fetch(d):
    y=d.strftime('%Y/%m/%d')
    return d,{
      'cards':rows(f'data/programs/race_cards/{y}.csv'),
      'waku':rows(f'data/programs/waku10/{y}.csv'),
      'tkz':rows(f'data/previews/tkz/{y}.csv'),
      'stt':rows(f'data/previews/stt/{y}.csv'),
      'orig':rows(f'data/previews/original_exhibition/{y}.csv'),
    }

def st_bias(sums,allv):
    g=float(np.mean(allv)) if allv else .15
    return {b:(float(np.mean(sums[b]))-g if sums[b] else 0.) for b in range(1,7)}
def update_st(stt,sums,allv):
    for r in stt:
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'),None)
            if v is not None and -.30<v<1.0:sums[b].append(v);allv.append(v)

def build_current(base,dc):
    idx=defaultdict(list)
    for ix,r in base.iterrows():
        dt=pd.to_datetime(r[dc],errors='coerce')
        if pd.notna(dt) and dt<CONTAM:idx[str(r.get('race_code','')).zfill(12)].append(ix)
    days=[];d=PRELOAD
    while d<=END:days.append(d);d+=timedelta(days=1)
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(day_fetch,d) for d in days]
        for j,f in enumerate(as_completed(futs),1):
            try:dd,z=f.result();fetched[dd]=z
            except Exception as e:print('fetch fail',e,flush=True)
            if j%30==0:print('current days',j,'/',len(days),flush=True)
    sums=defaultdict(list);allv=[];extras={}
    for d in sorted(fetched):
        z=fetched[d];bias=st_bias(sums,allv);cm=bycode(z['cards']);wm=bycode(z['waku']);tm=bycode(z['tkz']);sm=bycode(z['stt']);om=bycode(z['orig'])
        for code,card in cm.items():
            if code not in idx:continue
            try:x=race_features(card,wm.get(code,{}));ex,st,os=corrected_direct(code,tm,sm,om,bias)
            except Exception:continue
            tr=tm.get(code,{});q={}
            for b in range(1,7):
                zz=x[b]
                q[f'c_b{b}_ex']=ex.get(b,.5);q[f'c_b{b}_st']=st.get(b,.5)
                q[f'c_b{b}_lap']=os.get(b,{}).get('lap',.5);q[f'c_b{b}_turn']=os.get(b,{}).get('turn',.5)
                q[f'c_b{b}_straight']=os.get(b,{}).get('straight',.5);q[f'c_b{b}_origavg']=os.get(b,{}).get('avg',.5)
                q[f'c_b{b}_wr']=clamp((zz['wr']-3)/5);q[f'c_b{b}_local']=clamp((zz['local']-2.5)/5.5)
                q[f'c_b{b}_motor']=.62*pct_motor(zz['motor2'])+.38*pct_motor(zz['motor3'])
                q[f'c_b{b}_waku_wr']=clamp(zz['waku_wr']/8);q[f'c_b{b}_nst']=clamp((.24-zz['nst'])/.14)
                q[f'c_b{b}_waku_st']=clamp((.24-zz['waku_st'])/.14);q[f'c_b{b}_waku_sr']=clamp((6-zz['waku_sr'])/5)
                q[f'c_b{b}_pastwin']=zz['past_win'];q[f'c_b{b}_meetst']=.5 if zz['meet_st'] is None else clamp((.22-zz['meet_st'])/.12)
                q[f'c_b{b}_grade']=grade_score(zz['grade']);q[f'c_b{b}_tilt']=ff(tr.get(f'艇{b}_チルト'),0.)
            # race-shape aggregates and relative head edges
            for met in ['ex','st','lap','turn','straight','origavg','motor','wr','waku_wr','nst','waku_st','waku_sr','pastwin','meetst']:
                vals=[q[f'c_b{b}_{met}'] for b in range(1,7)]
                q[f'c_{met}_spread']=max(vals)-min(vals);q[f'c_{met}_sd']=float(np.std(vals))
                for b in [1,2,4,5,6]:q[f'c_b3_minus_b{b}_{met}']=q[f'c_b3_{met}']-q[f'c_b{b}_{met}']
                q[f'c_b3_inside_{met}']=q[f'c_b3_{met}']-max(q[f'c_b1_{met}'],q[f'c_b2_{met}'])
                q[f'c_b3_outside_{met}']=q[f'c_b3_{met}']-max(q[f'c_b4_{met}'],q[f'c_b5_{met}'],q[f'c_b6_{met}'])
            # interpretable attack/wall/follow composites, fixed formulas (not tuned here)
            q['c_wall12_weak']=.30*(1-q['c_b1_waku_wr'])+.30*(1-q['c_b2_waku_wr'])+.20*q['c_b3_minus_b2_st']+.20*q['c_b3_minus_b2_straight']
            q['c_attack3_stretch']=.28*q['c_b3_ex']+.28*q['c_b3_st']+.24*q['c_b3_straight']+.20*q['c_b3_motor']
            q['c_attack3_turn']=.18*q['c_b3_ex']+.20*q['c_b3_st']+.27*q['c_b3_turn']+.20*q['c_b3_lap']+.15*q['c_b3_motor']
            q['c_outer_follow']=max(.35*q[f'c_b{b}_st']+.30*q[f'c_b{b}_straight']+.20*q[f'c_b{b}_motor']+.15*q[f'c_b{b}_wr'] for b in [4,5,6])
            for ix in idx[code]:extras[ix]=q
        # current day ST influences only future dates
        update_st(z['stt'],sums,allv)
    return base.join(pd.DataFrame.from_dict(extras,orient='index'),how='left')

def cols(d,prefix):return [c for c in d.columns if c.startswith(prefix)]
def numeric_ok(d,fs,rate=.70):return [c for c in fs if c in d.columns and pd.to_numeric(d[c],errors='coerce').notna().mean()>=rate]

def head_groups(d,basefs):
    player=cols(d,'b3_pl_');hist=cols(d,'b3_vh_')
    cur=[c for c in cols(d,'c_b3_') if 'minus' not in c]+[c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
    rel=[c for c in d.columns if c.startswith('c_b3_minus_') or c.startswith('c_b3_inside_') or c.startswith('c_b3_outside_')]
    return {
      'PLAYER':list(basefs)+player,
      'PLAYER+CURRENT':list(basefs)+player+cur,
      'PLAYER+CURRENT+REL':list(basefs)+player+cur+rel,
      'PLAYER+HISTORY+CURRENT':list(basefs)+player+hist+cur,
      'PLAYER+HISTORY+CURRENT+REL':list(basefs)+player+hist+cur+rel,
      'PRIOR12':list(basefs)+hist,
      'PRIOR12+CURRENT':list(basefs)+hist+cur,
      'PRIOR12+CURRENT+REL':list(basefs)+hist+cur+rel,
    }

def fit_head(d,fs0,vc,first,nextm):
    fs=numeric_ok(d,fs0);tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<nextm)].copy()
    for c in fs:tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce')
    cats=[vc] if vc and vc not in fs else [];m=v165.model(fs,cats);m.fit(tr[fs+cats],tr._y.astype(int));te['_p']=m.predict_proba(te[fs+cats])[:,1]
    return te,len(fs)

def x(r,b,k,d=.5):return ff(r.get(f'c_b{b}_{k}'),d)
def pairvec(r,s,t,kind):
    z=list(v221.pairvec(r,s,t,True))
    if kind=='V221':return z
    # candidate current-state details
    mets=['ex','st','lap','turn','straight','origavg','motor','wr','local','waku_wr','nst','waku_st','waku_sr','pastwin','meetst','grade','tilt']
    for b in [s,t,3]:z += [x(r,b,k,0.) for k in mets]
    for k in mets[:-2]:z += [x(r,s,k)-x(r,t,k),x(r,s,k)-x(r,3,k),x(r,t,k)-x(r,3,k)]
    # attack-development interactions: who survives/follows when 3 is strong in stretch vs turn
    mak=x(r,3,'st')*.30+x(r,3,'straight')*.35+x(r,3,'ex')*.20+x(r,3,'motor')*.15
    ms=x(r,3,'turn')*.35+x(r,3,'lap')*.30+x(r,3,'st')*.20+x(r,3,'motor')*.15
    z += [mak,ms,mak-ms,
          mak*float(s in (1,2)),mak*float(t in (1,2)),mak*float(s in (4,5,6)),mak*float(t in (4,5,6)),
          ms*float(s in (1,2)),ms*float(t in (1,2)),ms*float(s in (4,5,6)),ms*float(t in (4,5,6)),
          x(r,s,'turn')*ms,x(r,t,'turn')*ms,x(r,s,'straight')*mak,x(r,t,'straight')*mak]
    return z

def fit_pair(tr,kind):
    X=[];y=[];n=0
    for _,r in tr.iterrows():
        if ii(r.get('valid_result'))!=1:continue
        a=v166.combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=3 or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
        n+=1
        for s in OPP:
            for t in OPP:
                if s==t:continue
                X.append(pairvec(r,s,t,kind));y.append(int(s==a[1] and t==a[2]))
    if n<100:raise RuntimeError('small pair train')
    m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))]);m.fit(np.asarray(X,float),np.asarray(y,int));return m

def order(r,m,kind):
    a=[]
    for s in OPP:
        for t in OPP:
            if s!=t:a.append((float(m.predict_proba(np.asarray([pairvec(r,s,t,kind)],float))[0,1]),s,t))
    a.sort(key=lambda q:(-q[0],q[1],q[2]));return [f'3-{s}-{t}' for _,s,t in a]

def settle(ts,od,actual):
    vals=[]
    for q in ts[:10]:
        try:v=float(od[q])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=np.asarray(v205.round_dutch(vals,BANK),int)
    if int(stakes.sum())!=BANK:raise RuntimeError('Dutch invariant')
    ret=0.;hit=0
    if actual in ts[:10]:
        j=ts[:10].index(actual)
        if stakes[j]>0:hit=1;ret=float(stakes[j]*vals[j])
    return hit,ret,ret-BANK

def maxdd(a):
    c=np.cumsum(np.asarray(a,float));pk=np.maximum.accumulate(np.r_[0.,c]);return float((pk[1:]-c).max()) if len(c) else 0.
def robust(g):
    if g.empty:return (0.,0.,0.,0.,0.)
    roi=100*g.ret.sum()/(len(g)*BANK);md=maxdd(g.sort_values(['date','race_code']).profit)
    s=g.sort_values('profit',ascending=False);rr=[]
    for k in [1,3,5]:
        q=s.iloc[k:];rr.append(100*q.ret.sum()/(len(q)*BANK) if len(q) else 0.)
    return (roi,md,*rr)

def main():
    raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy()
    # v221 adds prior exhibition/player traits; v222 adds granular current-day pre-deadline state.
    d=v221.build(raw,dc);d=build_current(d,dc)
    if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION')
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);groups=head_groups(d,basefs);pred=[]
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
        pm={'V221':fit_pair(tr,'V221'),'V222_CURRENT_PAIR':fit_pair(tr,'V222_CURRENT_PAIR')}
        # legacy BASE p>=.30 volume for fair comparison
        base_te,nf=fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
        for hname,hfs in groups.items():
            te,nfeat=fit_head(d,hfs,vc,first,nextm);sel=te.nlargest(k,'_p')
            yv=te._y.astype(int).to_numpy();pv=te._p.to_numpy()
            for pname,m in pm.items():
                rowsout=[]
                for ix,r in sel.iterrows():
                    if ii(r.get('valid_result'))!=1 or ii(r.get('course3'),3)!=3:continue
                    act=v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
                    code=str(r.get('race_code','')).zfill(12)
                    if not actual or code not in oi.index:continue
                    od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
                    ts=order(r,m,pname);s=settle(ts,od,actual)
                    if s is None:continue
                    rank=ts.index(actual)+1 if actual in ts else 0
                    rowsout.append({'variant':hname,'pair':pname,'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(r._p),'y3':int(r._y),'rank':rank,'hit':s[0],'ret':s[1],'profit':s[2],'nfeat':nfeat})
                g=pd.DataFrame(rowsout)
                if not g.empty:
                    h=g[g.y3==1];cov=100*((h['rank']>0)&(h['rank']<=10)).mean() if len(h) else 0.
                    roi,md,rm1,rm3,rm5=robust(g)
                    pred.append({'variant':hname,'pair':pname,'month':mon,'R':len(g),'head_rate':100*g.y3.mean(),'coverage10':cov,'hit10':100*g.hit.mean(),'roi':roi,'maxdd':md,'roi_rm1':rm1,'roi_rm3':rm3,'roi_rm5':rm5,'auc_all_month':safe_auc(yv,pv),'brier_all_month':float(brier_score_loss(yv,pv)),'logloss_all_month':safe_ll(yv,pv),'nfeat':nfeat})
    z=pd.DataFrame(pred)
    if z.empty:raise SystemExit('no v222 rows')
    if set(z.month)-set(EVAL_MONTHS):raise RuntimeError('CONTAM MONTH')
    z.to_csv(OUT,index=False)
    L=['# v222 broad 3-head feature audit','',
       '- clean evaluation only: 2025-12..2026-06; Jul/Aug excluded',
       '- strict monthly prior-only model refit and historical traits',
       '- current-day features are pre-deadline: card/waku10 + lane-corrected exhibition/ST/original exhibition + tilt',
       '- pair candidates receive granular current state, relative state, player/history state, and makuri/makurizashi interaction features',
       '- historical closing odds are settlement-only; Top10 and exact 10,000-yen Hamilton Dutch fixed',
       '- each head variant is volume matched to that month legacy BASE p>=0.30 count','',
       '## Aggregate across clean months','|head features|pair features|R|3-head|Top10 cov|hit|ROI|maxDD|rm1|rm3|rm5|mean AUC|mean Brier|features|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    agg=[]
    for (h,p),g in z.groupby(['variant','pair']):
        R=int(g.R.sum());hr=np.average(g.head_rate,weights=g.R);cv=np.average(g.coverage10,weights=np.maximum(g.R*g.head_rate/100,1e-9));hit=np.average(g.hit10,weights=g.R)
        # aggregate ROI/profit robustness approximated from monthly total R-weighted realized ROI; DD shown max monthly DD here
        roi=np.average(g.roi,weights=g.R);rm1=np.average(g.roi_rm1,weights=g.R);rm3=np.average(g.roi_rm3,weights=g.R);rm5=np.average(g.roi_rm5,weights=g.R)
        row=(h,p,R,hr,cv,hit,roi,float(g.maxdd.max()),rm1,rm3,rm5,float(g.auc_all_month.mean()),float(g.brier_all_month.mean()),int(g.nfeat.max()));agg.append(row)
    agg.sort(key=lambda q:(-q[6],-q[4],-q[11]))
    for a in agg:L.append(f'|{a[0]}|{a[1]}|{a[2]}|{a[3]:.2f}%|{a[4]:.2f}%|{a[5]:.2f}%|{a[6]:.2f}%|{a[7]:.0f}|{a[8]:.2f}%|{a[9]:.2f}%|{a[10]:.2f}%|{a[11]:.4f}|{a[12]:.5f}|{a[13]}|')
    L += ['','## Interpretation','- This is feature-family discovery, not production adoption.',
          '- Prefer improvements repeated across months and preserved after high-profit removal; reject isolated aggregate ROI spikes.',
          '- If current granular features help pair coverage more than head AUC, keep them in the opponent layer rather than blindly pooling into the head model.',
          '- Any next rule still requires Sep+ immutable prospective LIVE validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
