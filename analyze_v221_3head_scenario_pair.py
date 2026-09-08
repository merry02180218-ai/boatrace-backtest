#!/usr/bin/env python3
"""v221: scenario-aware opponent ranking for the clean pre-Jul 3-head redesign.

Frozen rules
- 2026-07/08 are excluded from training/tuning/evaluation.
- Eval 2025-12..2026-06; each month trains only on earlier dates.
- Head selectors are the v220 findings re-created here: BASE+PLAYER and BASE+PRIOR12.
- Opponent model uses ability + race development: 3-makuri / 3-makurizashi context,
  inside survival / outside follow position, prior1/prior2 corrected exhibition/original
  exhibition, and prior-only player/frame traits for BOTH second/third candidates.
- Same-day results are not used. All day-D historical traits are frozen before ingesting day D.
- Closing historical odds are settlement-only; they never choose ranking/features/thresholds.
- Top10 and exact 10,000-yen Hamilton Dutch are fixed diagnostics, not adoption tuning.
"""
from __future__ import annotations
from collections import defaultdict,deque
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,brier_score_loss

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v166_3head_pair_direct as v166
import analyze_v205_3head_operational_replay as v205
import analyze_v220_3head_history_player as v220
from backtest import rows
from backtest_v3 import CORR,expo_rows_to_records
from backtest_v4 import clean_name,rank_strength

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v221_3head_scenario_pair.csv'
SUM=ROOT/'summary_v221_3head_scenario_pair.md'
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
def normkim(x):return (x or '').replace(' ','').replace('　','')

def day_fetch(d):
    ymd=d.strftime('%Y/%m/%d')
    return d,{'cards':rows(f'data/programs/race_cards/{ymd}.csv'),'tkz':rows(f'data/previews/tkz/{ymd}.csv'),
              'orig':rows(f'data/previews/original_exhibition/{ymd}.csv'),'res':rows(f'data/results/realtime/{ymd}.csv')}

def previews(cards,tkz,orig):
    tm=bycode(tkz);om=bycode(orig);out=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12);venue=str(card.get('レース場コード','')).zfill(2)
        nr={}
        if code in om:
            for z in expo_rows_to_records([om[code]]):nr[clean_name(z.get('name',''))]=z
        tr=tm.get(code,{});vals=[]
        for b in range(1,7):
            v=v220.ff(tr.get(f'艇{b}_展示タイム'))
            if v is not None:vals.append((b,v+CORR[b]['展示']))
        dr=rank_strength(vals) if vals else {}
        for b in range(1,7):
            name=clean_name(card.get(f'艇{b}_選手名',''))
            if not name:continue
            z=nr.get(name,{})
            out.append((code,venue,b,name,{'display':float(dr.get(b,.5)),'overall':float(z.get('overall',.5)),
                'turn':float(z.get('turn',.5)),'straight':float(z.get('straight',.5))}))
    return out

def blank():return {'n':0,'w':0,'p2':0,'nf':defaultdict(int),'wf':defaultdict(int),'p2f':defaultdict(int),'r':deque(maxlen=30)}

def hvals(dq):
    a=list(dq);p1=a[-1] if a else None;p2=a[-2] if len(a)>1 else None;o={'has1':int(p1 is not None),'has2':int(p2 is not None)}
    for k in ['display','overall','turn','straight']:
        x1=float(p1[k]) if p1 else .5;x2=float(p2[k]) if p2 else .5
        o['p1_'+k]=x1;o['p2_'+k]=x2;o['p12_'+k]=.6*x1+.4*x2 if p2 else x1;o['delta_'+k]=x1-x2 if p1 and p2 else 0.
    return o

def pstat(s,b):
    n=s['n'];nf=s['nf'][b];r=list(s['r'])
    return {'all_win':(s['w']+2/6)/(n+2),'all_p2':(s['p2']+2/3)/(n+2),
            'frame_races':nf,'frame_win':(s['wf'][b]+3*.125)/(nf+3),'frame_p2':(s['p2f'][b]+3*.25)/(nf+3),
            'recent_p2':sum(r)/len(r) if r else 1/3}

def build(base,dc):
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
            if j%30==0:print('fetch',j,'/',len(days),flush=True)
    gh=defaultdict(lambda:deque(maxlen=2));vh=defaultdict(lambda:deque(maxlen=2));ps=defaultdict(blank);extras={}
    for d in sorted(fetched):
        z=fetched[d];cm=bycode(z['cards']);rm=bycode(z['res']);prs=previews(z['cards'],z['tkz'],z['orig'])
        # freeze before current day preview/results
        for code,card in cm.items():
            if code not in idx:continue
            venue=str(card.get('レース場コード','')).zfill(2);q={}
            for b in range(1,7):
                name=clean_name(card.get(f'艇{b}_選手名',''))
                if not name:continue
                a=hvals(vh[(venue,name)]);g=hvals(gh[name]);st=pstat(ps[name],b)
                for k,v in a.items():q[f'b{b}_vh_{k}']=v
                for k,v in g.items():q[f'b{b}_gh_{k}']=v
                for k,v in st.items():q[f'b{b}_pl_{k}']=v
            for ix in idx[code]:extras[ix]=q
        for code,venue,b,name,p in prs:vh[(venue,name)].append(p);gh[name].append(p)
        for code,card in cm.items():
            rr=rm.get(code,{});w=ii(rr.get('1着_艇番'));sec=ii(rr.get('2着_艇番'))
            for b in range(1,7):
                name=clean_name(card.get(f'艇{b}_選手名',''))
                if not name:continue
                s=ps[name];s['n']+=1;s['w']+=int(w==b);s['p2']+=int(w==b or sec==b);s['nf'][b]+=1;s['wf'][b]+=int(w==b);s['p2f'][b]+=int(w==b or sec==b);s['r'].append(int(w==b or sec==b))
    return base.join(pd.DataFrame.from_dict(extras,orient='index'),how='left')

def head_features(d,basefs,kind):
    if kind=='PLAYER':return list(basefs)+[c for c in d.columns if c.startswith('b3_pl_')]
    if kind=='PRIOR12':return list(basefs)+[c for c in d.columns if c.startswith('b3_vh_')]
    raise ValueError(kind)

def head_fit(d,basefs,vc,first,nextm,kind):
    fs=[]
    for c in head_features(d,basefs,kind):
        if c in d.columns and pd.to_numeric(d[c],errors='coerce').notna().mean()>=.70:fs.append(c)
    tr=d[d._date<first].copy();te=d[(d._date>=first)&(d._date<nextm)].copy()
    for c in fs:tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce')
    cats=[vc] if vc and vc not in fs else [];m=v165.model(fs,cats);m.fit(tr[fs+cats],tr._y.astype(int));te['_p']=m.predict_proba(te[fs+cats])[:,1]
    return te

def xtra(r,b,prefix):return ff(r.get(f'b{b}_{prefix}'),.5)
def scenario(r,s,t):
    mak=ff(r.get('structure_3makuri'),ff(r.get('score_3makuri'),.5));ms=ff(r.get('structure_3makurizashi'),ff(r.get('score_3makurizashi'),.5))
    # position effects are explicit so model can learn survival/follow patterns under each attack shape.
    return [mak,ms,mak-ms,
      float(s in (1,2)),float(t in (1,2)),float(s in (4,5,6)),float(t in (4,5,6)),
      float(s==2),float(t==2),float(s==4),float(t==4),float(s==1),float(t==1),
      mak*float(s in (1,2)),mak*float(t in (1,2)),mak*float(s in (4,5,6)),mak*float(t in (4,5,6)),
      ms*float(s in (1,2)),ms*float(t in (1,2)),ms*float(s in (4,5,6)),ms*float(t in (4,5,6))]

def pairvec(r,s,t,extra=True):
    x=list(v166.pvec(r,s,t))
    if not extra:return x
    for b in (s,t,3):
        x += [xtra(r,b,'vh_p12_display'),xtra(r,b,'vh_p12_overall'),xtra(r,b,'vh_p12_turn'),xtra(r,b,'vh_p12_straight'),
              xtra(r,b,'vh_delta_display',),xtra(r,b,'vh_delta_turn'),xtra(r,b,'vh_delta_straight'),
              xtra(r,b,'pl_all_win'),xtra(r,b,'pl_all_p2'),xtra(r,b,'pl_frame_win'),xtra(r,b,'pl_frame_p2'),xtra(r,b,'pl_recent_p2')]
    # relative state/ability between second and third candidates and to the attacking 3 boat.
    for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_frame_p2']:
        x += [xtra(r,s,k)-xtra(r,t,k),xtra(r,s,k)-xtra(r,3,k),xtra(r,t,k)-xtra(r,3,k)]
    x += scenario(r,s,t)
    return x

def fit_pair(train,extra):
    X=[];y=[];n=0
    for _,r in train.iterrows():
        if ii(r.get('valid_result'))!=1:continue
        a=v166.combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=3 or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
        n+=1
        for s in OPP:
            for t in OPP:
                if s==t:continue
                X.append(pairvec(r,s,t,extra));y.append(int(s==a[1] and t==a[2]))
    if n<100:raise RuntimeError(f'pair training too small {n}')
    m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))]);m.fit(np.asarray(X,float),np.asarray(y,int));return m,n

def order(r,m,extra):
    z=[]
    for s in OPP:
        for t in OPP:
            if s!=t:z.append((float(m.predict_proba(np.asarray([pairvec(r,s,t,extra)],float))[0,1]),s,t))
    z.sort(key=lambda a:(-a[0],a[1],a[2]));return [f'3-{s}-{t}' for _,s,t in z]

def settle(ts,od,actual):
    vals=[]
    for x in ts[:10]:
        try:v=float(od[x])
        except:return None
        if not np.isfinite(v) or v<=0:return None
        vals.append(v)
    stakes=np.asarray(v205.round_dutch(vals,BANK),int)
    if int(stakes.sum())!=BANK:raise RuntimeError('Dutch')
    ret=0.;hit=0
    if actual in ts[:10]:
        i=ts[:10].index(actual)
        if stakes[i]>0:hit=1;ret=float(stakes[i]*vals[i])
    return hit,ret,ret-BANK

def metric(g,col):
    h=g[g.y3==1];cov=100*((h[col]>0)&(h[col]<=10)).mean() if len(h) else 0.;hit=100*g['hit_'+col].mean() if len(g) else 0.;roi=100*g['ret_'+col].sum()/(len(g)*BANK) if len(g) else 0.
    return cov,hit,roi

def main():
    raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<CONTAM)].copy();d=build(raw,dc)
    if (d._date>=CONTAM).any():raise RuntimeError('CONTAMINATION')
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);out=[]
    for mon in EVAL_MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
        mb,nb=fit_pair(tr,False);mx,nx=fit_pair(tr,True)
        hp={}
        for kind in ['PLAYER','PRIOR12']:
            te=head_fit(d,basefs,vc,first,nextm,kind);k=max(1,int((te['_p']>=.30).sum())) if kind=='PLAYER' else None
            # fixed diagnostic volume: use legacy BASE p>=.30 count, not a newly tuned threshold.
            base_te=head_fit(d,basefs,vc,first,nextm,'PLAYER') if False else None
            hp[kind]=te
        # use v219 monthly legacy selected count from BASE p>=.30 by fitting BASE directly
        fs=[]
        for c in basefs:
            if c in d.columns and pd.to_numeric(d[c],errors='coerce').notna().mean()>=.70:fs.append(c)
        trb=d[d._date<first].copy();teb=d[(d._date>=first)&(d._date<nextm)].copy()
        for c in fs:trb[c]=pd.to_numeric(trb[c],errors='coerce');teb[c]=pd.to_numeric(teb[c],errors='coerce')
        cats=[vc] if vc and vc not in fs else [];hm=v165.model(fs,cats);hm.fit(trb[fs+cats],trb._y.astype(int));teb['_p']=hm.predict_proba(teb[fs+cats])[:,1];vol=int((teb._p>=.30).sum())
        for kind,te in hp.items():
            sel=te.sort_values('_p',ascending=False).head(vol)
            for ix,r in sel.iterrows():
                code=str(r.get('race_code','')).zfill(12)
                if code not in oi.index or ii(r.get('valid_result'))!=1 or ii(r.get('course3'),3)!=3:continue
                a=v166.combo(r.get('actual_combo'));actual='-'.join(map(str,a)) if len(a)==3 else ''
                if not actual:continue
                od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
                ob=order(r,mb,False);ox=order(r,mx,True);sb=settle(ob,od,actual);sx=settle(ox,od,actual)
                if not sb or not sx:continue
                out.append({'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'head_selector':kind,'p3':float(r._p),'y3':int(r._y),
                  'actual':actual,'rank_base':ob.index(actual)+1 if actual in ob else 0,'rank_v221':ox.index(actual)+1 if actual in ox else 0,
                  'hit_rank_base':sb[0],'ret_rank_base':sb[1],'profit_rank_base':sb[2],'hit_rank_v221':sx[0],'ret_rank_v221':sx[1],'profit_rank_v221':sx[2],
                  'pair_train_3wins':nx})
    z=pd.DataFrame(out)
    if z.empty:raise SystemExit('no output')
    if (pd.to_datetime(z.date)>=CONTAM).any():raise RuntimeError('CONTAMINATION OUTPUT')
    z.to_csv(OUT,index=False)
    L=['# v221 scenario-aware 3-head opponent audit','',
       '- clean evaluation: 2025-12..2026-06 only; 2026-07/08 hard excluded',
       '- head selectors: v220 PLAYER and PRIOR12, volume-matched to legacy BASE p>=0.30 per month',
       '- opponent v221 = v166 ability features + both candidates prior1/prior2 exhibition/original exhibition + player/frame traits + 3-makuri/makurizashi scenario interactions',
       '- historical odds settlement-only; fixed Top10; exact 10,000-yen Hamilton Dutch','',
       '|head selector|R|3-head|v166 Top10 cov|v221 Top10 cov|v166 hit|v221 hit|v166 ROI|v221 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for kind,g in z.groupby('head_selector'):
        c0,h0,r0=metric(g,'rank_base');c1,h1,r1=metric(g,'rank_v221');L.append(f'|{kind}|{len(g)}|{100*g.y3.mean():.2f}%|{c0:.2f}%|{c1:.2f}%|{h0:.2f}%|{h1:.2f}%|{r0:.1f}%|{r1:.1f}%|')
    L += ['','## Monthly v221 vs v166 Top10 coverage / ROI','|selector|month|R|3-head|cov v166|cov v221|ROI v166|ROI v221|','|---|---|---:|---:|---:|---:|---:|---:|']
    for (kind,mon),g in z.groupby(['head_selector','month']):
        c0,_,r0=metric(g,'rank_base');c1,_,r1=metric(g,'rank_v221');L.append(f'|{kind}|{mon}|{len(g)}|{100*g.y3.mean():.2f}%|{c0:.2f}%|{c1:.2f}%|{r0:.1f}%|{r1:.1f}%|')
    L += ['','## Decision rule','- Do not adopt from aggregate ROI alone. Prefer v221 only if conditional coverage improves without concentrated monthly collapse.',
          '- Jul/Aug remain descriptive-only after rules are frozen. Sep+ immutable LIVE is prospective validation.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
