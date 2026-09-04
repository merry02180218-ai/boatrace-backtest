"""v113: 1号艇 exact 3連単 probability calibration + strict pre-close EV selection.

Predictive side stays frozen:
- head layer: v109 p109 / A=.65, S=.72
- role layer: the v110 second/third models, fit month-by-month on strictly prior dates
- no current odds are allowed to change head selection or role model fitting

Improvement over v112:
- do NOT convert v110 rank into an empirical rank bucket probability
- directly compute P(second=s|1 wins) * P(third=t|1 wins, second=s) for all 20 exact 1-s-t pairs
- calibrate the 20 conditional pair probabilities with prior-month-only Platt or Isotonic
- separately Platt-calibrate p109 for the head, then multiply head probability by normalized pair probability
- use only verified pre-close od3 to decide EV purchases

Validation: 2026-07-19..07-31. Holdout: 2026-08-01..08-31.
"""
from __future__ import annotations

import csv, math
from collections import Counter
from datetime import date, datetime

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from backtest import rows
from analyze_v110_1head_role_tickets import (
    read_csv, fit_roles, second_vec, third_vec
)

RAW='analysis_v108_1head_feasibility.csv'
HEAD='analysis_v109_1head_monthly_walkforward.csv'
V110='analysis_v110_1head_role_tickets.csv'
OUT='analysis_v113_1head_exact_prob_ev.csv'
SUMMARY='summary_v113_1head_exact_prob_ev.md'

MONTHS=['2026-06','2026-07','2026-08']
DEV_START='2026-07-19'; DEV_END='2026-07-31'
TEST_START='2026-08-01'; TEST_END='2026-08-31'
A_CUT=.65; S_CUT=.72
EV_GRID=[1.00,1.05,1.10,1.15,1.20,1.25,1.30,1.40,1.50,1.75,2.00]
METHODS=['PLATT','ISOTONIC']
BOATS=list(range(2,7))
PAIRS=[(s,t) for s in BOATS for t in BOATS if t!=s]


def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def clip01(x,lo=1e-6,hi=1-1e-6):return max(lo,min(hi,float(x)))
def logit(p):
    p=clip01(p);return math.log(p/(1-p))

def grade_sel(r,g):return ff(r.get('p109')) >= (S_CUT if g=='S' else A_CUT)

def cutoff_for(ds,cut,acq):
    hh,mm=map(int,cut.split(':')[:2]);y,m,d=map(int,ds.split('-'))
    return datetime(y,m,d,hh,mm,tzinfo=acq.tzinfo)

def preclose_lead(r,ds):
    acq=(r.get('取得日時') or '').strip();cut=(r.get('締切時刻') or '').strip()
    if not acq or not cut:return None
    try:
        a=datetime.fromisoformat(acq);c=cutoff_for(ds,cut,a)
        z=(c-a).total_seconds()/60.0
        return z if z>0 else None
    except Exception:return None

def load_odds_map(dates):
    om={};leads={}
    for ds in sorted(dates):
        for r in rows(f'data/previews/od3/{ds.replace("-","/")}.csv'):
            code=(r.get('レースコード') or '').strip();lead=preclose_lead(r,ds)
            if not code or lead is None:continue
            if code not in om or abs(lead-10.0)<abs(leads[code]-10.0):
                om[code]=r;leads[code]=lead
    return om,leads

def all_odds(orow):
    d={}
    for s,t in PAIRS:
        k=f'1-{s}-{t}';o=ff(orow.get('3連単_'+k),0)
        if o<=1.0:return None
        d[k]=o
    return d

def actual_combo(r):return (r.get('actual_combo') or '').strip()

def attach_head_and_v110(src):
    hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEAD)}
    vr={}
    for r in read_csv(V110):
        vr[(r.get('date'),r.get('race_code'))]=ii(r.get('v110_rank20'))
    out=[]
    for r0 in src:
        if r0.get('month') not in MONTHS:continue
        r=dict(r0);key=(r.get('date'),r.get('race_code'))
        r['p109']=hp.get(key,'');r['_v110_rank20']=vr.get(key,0)
        if ff(r.get('p109'),-1)<0:continue
        out.append(r)
    return out

def month_role_probs(src,mo):
    first=date.fromisoformat(mo+'-01')
    train=[r for r in src if date.fromisoformat(r['date'])<first]
    test=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    m2,m3,ntrain=fit_roles(train)
    if not test:return []

    x2=[];x3=[]
    for r in test:
        for b in BOATS:x2.append(second_vec(r,b))
        for s,t in PAIRS:x3.append(third_vec(r,s,t))
    p2=m2.predict_proba(np.asarray(x2,dtype=float))[:,1].reshape(len(test),5)
    p3=m3.predict_proba(np.asarray(x3,dtype=float))[:,1].reshape(len(test),20)

    out=[]
    for i,r in enumerate(test):
        a2=np.maximum(p2[i],1e-12);a2=a2/a2.sum()
        pp={};off=0
        for si,s in enumerate(BOATS):
            rem=[t for t in BOATS if t!=s]
            a3=np.maximum(p3[i,off:off+4],1e-12);off+=4;a3=a3/a3.sum()
            for j,t in enumerate(rem):pp[f'1-{s}-{t}']=float(a2[si]*a3[j])
        z=sum(pp.values()) or 1.0
        pp={k:v/z for k,v in pp.items()}
        q=dict(r);q['_pair_raw']=pp;q['_role_train_headwins']=ntrain
        out.append(q)
    return out

def build_records(src):
    out=[]
    for mo in MONTHS:out.extend(month_role_probs(src,mo))
    return out

class HeadPlatt:
    def __init__(self):self.m=None
    def fit(self,rs,g):
        q=[r for r in rs if grade_sel(r,g)]
        X=np.asarray([[logit(ff(r.get('p109')))] for r in q],dtype=float)
        y=np.asarray([ii(r.get('head_hit')) for r in q],dtype=int)
        self.m=LogisticRegression(C=1000,max_iter=1000,solver='lbfgs').fit(X,y)
        return len(q),int(y.sum()),float(np.mean([ff(r.get('p109')) for r in q])),float(y.mean())
    def predict(self,p):return float(self.m.predict_proba(np.asarray([[logit(p)]],dtype=float))[0,1])

class PairCal:
    def __init__(self,method):self.method=method;self.m=None
    def fit(self,rs,g):
        X=[];y=[];heads=0
        for r in rs:
            if not grade_sel(r,g) or ii(r.get('head_hit'))!=1:continue
            act=actual_combo(r)
            if act not in r['_pair_raw']:continue
            heads+=1
            for k in [f'1-{s}-{t}' for s,t in PAIRS]:
                p=r['_pair_raw'][k];X.append(p);y.append(int(k==act))
        if heads<100:raise RuntimeError(f'not enough pair calibration heads: {heads}')
        if self.method=='PLATT':
            xx=np.asarray([[logit(p)] for p in X],dtype=float)
            self.m=LogisticRegression(C=1000,max_iter=1000,solver='lbfgs').fit(xx,np.asarray(y,dtype=int))
        else:
            self.m=IsotonicRegression(out_of_bounds='clip',y_min=1e-7,y_max=1.0).fit(np.asarray(X),np.asarray(y))
        return heads,len(X)
    def transform(self,raw):
        keys=list(raw.keys());x=[raw[k] for k in keys]
        if self.method=='PLATT':
            q=self.m.predict_proba(np.asarray([[logit(v)] for v in x],dtype=float))[:,1]
        else:q=self.m.predict(np.asarray(x,dtype=float))
        q=np.maximum(np.asarray(q,dtype=float),1e-12);s=float(q.sum())
        if not math.isfinite(s) or s<=0:q=np.asarray(x,dtype=float);s=float(q.sum())
        q=q/s
        return {k:float(v) for k,v in zip(keys,q)}

def prior_records(records,target_mo):
    first=date.fromisoformat(target_mo+'-01')
    return [r for r in records if date.fromisoformat(r['date'])<first]

def fit_calibrators(records,target_mo,g,method):
    tr=prior_records(records,target_mo)
    hp=HeadPlatt();hs=hp.fit(tr,g)
    pc=PairCal(method);ps=pc.fit(tr,g)
    return hp,pc,{'head_rows':hs[0],'head_hits':hs[1],'avg_p109':hs[2],'actual_head':hs[3],'pair_head_rows':ps[0],'pair_examples':ps[1]}

def enrich_for(records,start,end,g,method,odds_map,leads,cal_cache):
    out=[]
    for r in records:
        ds=r.get('date','')
        if not(start<=ds<=end) or not grade_sel(r,g) or ii(r.get('valid_payout'))!=1:continue
        orow=odds_map.get(r.get('race_code',''));od=all_odds(orow) if orow else None
        if od is None:continue
        mo=ds[:7];key=(mo,g,method)
        if key not in cal_cache:cal_cache[key]=fit_calibrators(records,mo,g,method)
        hp,pc,stats=cal_cache[key]
        ph=hp.predict(ff(r.get('p109')));qp=pc.transform(r['_pair_raw'])
        probs={k:ph*v for k,v in qp.items()}
        z=dict(r);z['_odds']=od;z['_probs']=probs;z['_lead']=leads.get(r.get('race_code',''),0.0);z['_phead_cal']=ph
        out.append(z)
    return out

def metric(rs,thr):
    bet_r=tickets=hits=ret=0;evsum=0.0;hist=Counter();fixed_hits=fixed_ret=0
    for r in rs:
        act=actual_combo(r);od=r['_odds'];pr=r['_probs']
        if 1<=ii(r.get('_v110_rank20'))<=7:
            fixed_hits+=1;fixed_ret+=ii(r.get('payout100'))
        sel=[k for k in pr if pr[k]*od[k]>=thr]
        hist[len(sel)]+=1
        if not sel:continue
        bet_r+=1;tickets+=len(sel);evsum+=sum(pr[k]*od[k] for k in sel)
        if act in sel:hits+=1;ret+=ii(r.get('payout100'))
    return {
      'odds_races':len(rs),'bet_races':bet_r,'bet_race_pct':pct(bet_r,len(rs)),
      'tickets':tickets,'avg_tickets_bet':tickets/bet_r if bet_r else 0,
      'hits':hits,'hit_rate_bet_pct':pct(hits,bet_r),'roi_pct':pct(ret,tickets*100),
      'avg_selected_model_ev':evsum/tickets if tickets else 0,
      'fixed7_hits':fixed_hits,'fixed7_hit_pct':pct(fixed_hits,len(rs)),
      'fixed7_roi_pct':pct(fixed_ret,len(rs)*700),'point_hist':hist,
    }

def hist_text(h):return ', '.join(f'{k}点:{v}R' for k,v in sorted(h.items()) if v)

def main():
    raw=attach_head_and_v110(read_csv(RAW))
    records=build_records(raw)
    need={r.get('date','') for r in records if DEV_START<=r.get('date','')<=TEST_END}
    odds_map,leads=load_odds_map(need)
    cache={};dev={};test={}
    for method in METHODS:
        dev[method]={};test[method]={}
        for g in ('A','S'):
            dev[method][g]=enrich_for(records,DEV_START,DEV_END,g,method,odds_map,leads,cache)
            test[method][g]=enrich_for(records,TEST_START,TEST_END,g,method,odds_map,leads,cache)

    sweep=[]
    for method in METHODS:
        for th in EV_GRID:
            ma=metric(dev[method]['A'],th);ms=metric(dev[method]['S'],th)
            ok=(ma['bet_races']>=100 and ms['bet_races']>=80 and ma['tickets']>=250 and ms['tickets']>=200 and ma['avg_tickets_bet']<=7 and ms['avg_tickets_bet']<=7)
            sweep.append((method,th,ok,min(ma['roi_pct'],ms['roi_pct']),(ma['roi_pct']+ms['roi_pct'])/2,ma,ms))
    good=[x for x in sweep if x[2]]
    selected=max(good,key=lambda x:(x[3],x[4],-x[1])) if good else next(x for x in sweep if x[0]=='PLATT' and abs(x[1]-1.40)<1e-9)
    smethod,sth=selected[0],selected[1]

    out=[]
    for phase,by in [('DEV',dev),('HOLDOUT',test)]:
        for method in METHODS:
            for g in ('A','S'):
                for th in EV_GRID:
                    m=metric(by[method][g],th)
                    out.append({'phase':phase,'method':method,'grade':g,'ev_threshold':th,
                                **{k:v for k,v in m.items() if k!='point_hist'},
                                'point_hist':';'.join(f'{k}:{v}' for k,v in sorted(m['point_hist'].items())),
                                'selected':int(method==smethod and abs(th-sth)<1e-9)})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v113 1号艇 exact probability × strict pre-close EV','',
       '- 頭判定は **v109固定**、2着/3着モデルは **v110と同じ月次prior-only role学習**。',
       '- `P(1-s-t)=校正済みP(1号艇1着) × 校正済み[P(2着=s|1着)×P(3着=t|1着,s)]`。',
       '- pair校正は対象月より前の月だけ。Platt / Isotonicの2方式をJul19-31 validationで比較し、方式とEV閾値を1組だけ固定してAugust holdoutへ送る。',
       '- 現在レースのod3は買い判定だけに使用。取得日時が締切より前のsnapshot以外は不使用。最終/締切時オッズは不使用。','']
    used=[leads.get(r.get('race_code','')) for r in records if r.get('race_code','') in odds_map and DEV_START<=r.get('date','')<=TEST_END]
    used=[x for x in used if x is not None]
    if used:
        ss=sorted(used);L += [f'- pre-close snapshot: **{len(used)}R** / 平均 **{sum(used)/len(used):.2f}分前** / 中央 **{ss[len(ss)//2]:.2f}分前** / 最短 **{min(used):.2f}分前** / 最長 **{max(used):.2f}分前**。','']

    L+=['## prior-month calibration','|対象月|層|方式|head学習R|head実1着率|平均p109|pair headR|pair examples|','|---|---|---|---:|---:|---:|---:|---:|']
    for mo in ('2026-07','2026-08'):
        for g in ('A','S'):
            for method in METHODS:
                c=cache.get((mo,g,method))
                if not c:continue
                st=c[2];L.append(f'|{mo}|{g}|{method}|{st["head_rows"]:,}|{st["actual_head"]*100:.1f}%|{st["avg_p109"]*100:.1f}%|{st["pair_head_rows"]:,}|{st["pair_examples"]:,}|')

    L+=['','## Jul19-31 validation — method × EV threshold','|方式|EV|A betR|A平均点|A ROI|S betR|S平均点|S ROI|admissible|','|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for method,th,ok,worst,avg,ma,ms in sweep:
        L.append(f'|{method}|{th:.2f}|{ma["bet_races"]}|{ma["avg_tickets_bet"]:.2f}|{ma["roi_pct"]:.1f}%|{ms["bet_races"]}|{ms["avg_tickets_bet"]:.2f}|{ms["roi_pct"]:.1f}%|{"YES" if ok else "NO"}|')
    L += ['',f'選択 = **{smethod} / EV≥{sth:.2f}**（ここで固定。August再調整なし）','']

    hold={g:metric(test[smethod][g],sth) for g in ('A','S')}
    L+=['## August strict holdout','|層|odds R|買うR|購入率|平均点|的中率/買うR|v113 ROI|v110固定7点的中率|v110固定7点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in ('A','S'):
        m=hold[g];L.append(f'|{g}|{m["odds_races"]}|{m["bet_races"]}|{m["bet_race_pct"]:.1f}%|{m["avg_tickets_bet"]:.2f}|{m["hit_rate_bet_pct"]:.1f}%|{m["roi_pct"]:.1f}%|{m["fixed7_hit_pct"]:.1f}%|{m["fixed7_roi_pct"]:.1f}%|')
    L+=['','### August dynamic ticket count']
    for g in ('A','S'):L.append(f'- {g}: {hist_text(hold[g]["point_hist"])}')

    passed=(hold['A']['bet_races']>=300 and hold['S']['bet_races']>=180 and hold['A']['avg_tickets_bet']<=7 and hold['S']['avg_tickets_bet']<=7 and hold['A']['roi_pct']>=100 and hold['S']['roi_pct']>=100)
    L+=['','## v113判定',
        f'- A ROI **{hold["A"]["roi_pct"]:.1f}%** / S ROI **{hold["S"]["roi_pct"]:.1f}%**。',
        f'- A平均点 **{hold["A"]["avg_tickets_bet"]:.2f}** / S平均点 **{hold["S"]["avg_tickets_bet"]:.2f}**。',
        f'- **V113 EXACT-PROB EV = {"PASS" if passed else "FAIL"}**',
        '- PASSでも即production採用はしない。pre-close odds履歴が短いため、prospective shadowで再確認してから採否を決める。',
        '- FAILなら、1号艇モデル自体ではなく「個別3連単確率の表現」を次段で見直す。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
