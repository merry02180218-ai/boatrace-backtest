"""v136: refine 1-head PRE selection by adding only inner opponent (2/3/4) pre-race threat features.

Goal
- Keep the strong legacy boat1 PRE core.
- Add a small, interpretable set of PRE-only opponent features for boats 2/3/4 and boat1-vs-inner margins.
- Avoid v135's all-6 high-dimensional expansion.
- Stage2 remains frozen: v109 S>=.72 + course1; tickets remain v110 lambda=.50 top7.

No-leak
- PRE uses race-card/waku10 only. No current exhibition/ST/original/current entry/odds.
- Monthly walk-forward: target month models train only on strictly earlier dates.
- Absolute threshold (if used) is selected on Mar-May only and frozen for Jun-Aug.
- Result/payout are labels/settlement only.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import rows, race_features, grade_score, clamp, pct_motor
from analyze_v109_1head_monthly_walkforward import fit as fit109, xmatrix, ii, ff
from analyze_v110b_1head_role_tickets import prepare_month

SRC='analysis_v108_1head_feasibility.csv'
OUT='analysis_v136_1head_preselection_inner_threats.csv'
SUMMARY='summary_v136_1head_preselection_inner_threats.md'
MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
VAL={'2026-03','2026-04','2026-05'}
HOLD={'2026-06','2026-07','2026-08'}
S_CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]
ABS_THRESHOLDS=[round(x,3) for x in np.arange(.45,.76,.025)]
LEGACY_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength']


def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def pct(a,b):return 100*a/b if b else 0.0

def boat_pre(x,b):
    z=x[b]
    return [
      grade_score(z['grade']), clamp((z['wr']-3)/5), clamp((z['local']-2.5)/5.5),
      .62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3']), clamp(z['waku_wr']/8),
      clamp((.24-z['nst'])/.14), clamp((6-z['waku_sr'])/5), z['past_win'],
      .5 if z['meet_st'] is None else clamp((.22-z['meet_st'])/.12),
    ]

def threat_summary(v):
    # PRE-only quality/attack proxy; intentionally compact and interpretable.
    # [grade,wr,local,motor,waku_wr,nst,waku_sr,past_win,meet_st]
    return (.16*v[0]+.18*v[1]+.07*v[2]+.17*v[3]+.13*v[4]+.11*v[5]+.08*v[6]+.04*v[7]+.06*v[8])

def fetch_day(ds):
    ymd=ds.replace('-','/')
    cards=rows(f'data/programs/race_cards/{ymd}.csv')
    wm={r.get('レースコード',''):r for r in rows(f'data/programs/waku10/{ymd}.csv')}
    out={}
    for c in cards:
        code=c.get('レースコード','')
        if code and code in wm:
            try:out[code]=race_features(c,wm[code])
            except Exception:pass
    return ds,out

def build_pre_map(src):
    dates=sorted({r['date'] for r in src if r.get('date')})
    out={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(fetch_day,d) for d in dates]
        for i,f in enumerate(as_completed(futs),1):
            try:ds,m=f.result();out.update(m)
            except Exception as e:print('pre fetch fail',e,flush=True)
            if i%30==0:print('pre days',i,'/',len(dates),flush=True)
    return out

def venue_vec(r):
    vv=str(r.get('venue','')).zfill(2)
    return [1.0 if vv==v else 0.0 for v in VENUES]

def xlegacy(rs):
    a=[]
    for r in rs:
        a.append([ff(r.get(k),0) for k in LEGACY_FEATURES]+venue_vec(r))
    return np.asarray(a,float)

def xhybrid(rs,pmap):
    a=[]
    for r in rs:
        base=[ff(r.get(k),0) for k in LEGACY_FEATURES]
        x=pmap.get(r.get('race_code'))
        if x:
            one=boat_pre(x,1); inn=[boat_pre(x,b) for b in (2,3,4)]
            # Add only compact inner threats plus selected boat1-minus-opponent margins.
            ts=[threat_summary(v) for v in inn]
            extra=ts+[max(ts),sum(ts)/3.0]
            # margins on the most decision-relevant PRE components: grade, WR, motor, waku WR, nST, meet ST
            for ob in inn:
                extra += [one[j]-ob[j] for j in (0,1,3,4,5,8)]
            # aggregate inner margin against the strongest inner opponent
            one_t=threat_summary(one);extra += [one_t-max(ts),one_t-sum(ts)/3.0]
        else:
            extra=[0.0]*(5+18+2)
        a.append(base+extra+venue_vec(r))
    return np.asarray(a,float)

def fit_lr(X,y):
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.30,max_iter=1800,solver='lbfgs'))])
    m.fit(X,np.asarray(y,int));return m

def metric(rs):
    q=[r for r in rs if ii(r.get('valid_payout'))==1]
    n=len(q);head=sum(ii(r.get('head_hit')) for r in q)
    hit=sum(1 for r in q if 0<ii(r.get('rank_l50'))<=7)
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get('rank_l50'))<=7)
    ret=sum(ii(r.get('payout100')) for r in q if 0<ii(r.get('rank_l50'))<=7)
    return {'n':n,'head':pct(head,n),'hit':pct(hit,n),'cov':pct(cov,len(heads)),'roi':pct(ret,n*700)}

def topn_select(byday,score,n=5):
    pre=[];buy=[]
    for d in sorted(byday):
        w=sorted(byday[d],key=lambda r:(-ff(r.get(score)),r.get('race_code','')))[:n]
        pre+=w;buy += [r for r in w if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1]
    return pre,buy

def abs_select(rs,th):
    pre=[r for r in rs if ff(r.get('hybrid_pre_p'))>=th]
    buy=[r for r in pre if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1]
    return pre,buy

def choose_abs(val):
    days=len({r['date'] for r in val});rows=[]
    for th in ABS_THRESHOLDS:
        pre,buy=abs_select(val,th);m=metric(buy)
        pr=len(pre)/days if days else 0;br=m['n']/days if days else 0
        # Do not target 5/day; require only useful sample size and avoid near-all-race flood.
        ok=m['n']>=180 and 1.0<=pr<=25.0
        rows.append((th,ok,pr,br,m))
    good=[x for x in rows if x[1]]
    if not good:return None,rows
    best=max(good,key=lambda x:(x[4]['roi'],x[4]['hit'],x[4]['head'],x[4]['n']))
    return best[0],rows

def main():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    pmap=build_pre_map(src);prepared={}
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01')
        tr=[r for r in src if date.fromisoformat(r['date'])<first]
        te=[r for r in src if r.get('month')==mo]
        leg=fit_lr(xlegacy(tr),[ii(r.get('head_hit')) for r in tr])
        hyb=fit_lr(xhybrid(tr,pmap),[ii(r.get('head_hit')) for r in tr])
        lp=leg.predict_proba(xlegacy(te))[:,1]
        hp=hyb.predict_proba(xhybrid(te,pmap))[:,1]
        live=fit109(tr);p109=live.predict_proba(xmatrix(te))[:,1]
        for r,a,b,c in zip(te,lp,hp,p109):
            r['legacy_pre_p']=float(a);r['hybrid_pre_p']=float(b);r['p109']=float(c)
        print('v136 role',mo,flush=True);prepared[mo]=prepare_month(src,mo)

    allrows=sum((prepared[m] for m in MONTHS),[])
    allrows=[r for r in allrows if ii(r.get('valid_payout'))==1]
    byday=defaultdict(list)
    for r in allrows:byday[r['date']].append(r)
    val=[r for r in allrows if r.get('month') in VAL]
    hold=[r for r in allrows if r.get('month') in HOLD]
    holdby=defaultdict(list)
    for r in hold:holdby[r['date']].append(r)

    leg_pre,leg_buy=topn_select(holdby,'legacy_pre_p',5)
    hyb5_pre,hyb5_buy=topn_select(holdby,'hybrid_pre_p',5)
    th,sweep=choose_abs(val)
    if th is not None:hab_pre,hab_buy=abs_select(hold,th)
    else:hab_pre,hab_buy=[],[]

    L=['# v136 1号艇 PRE: Legacy + 2/3/4号艇 threat差分','',
       '- Stage2固定: **v109 S(p>=72%) + 1コース維持**。ticketsは **v110 λ=.50 top7**。',
       '- Legacy PREの1号艇9特徴を維持し、2/3/4号艇だけのPRE threatと1号艇との差分を追加。',
       '- 5/6号艇はPRE追加特徴から外し、v135の高次元化を避ける。',
       '- 展示/オリジナル展示/現在進入/オッズはPRE不使用。月次walk-forward。','',
       '## Mar-May hybrid absolute-threshold selection','|閾値|PRE/day|BUY/day|BUY R|①頭率|7点的中率|coverage|ROI|eligible|','|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for t,ok,pr,br,m in sweep:
        L.append(f'|{t:.3f}|{pr:.2f}|{br:.2f}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|{"YES" if ok else "NO"}|')
    L += ['',f'Frozen hybrid absolute threshold = **{th if th is not None else "NONE"}**','',
          '## Jun-Aug holdout comparison','|方式|PRE R|PRE/day|BUY R|BUY/day|①頭率|7点的中率|coverage|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    hdays=len({r['date'] for r in hold})
    comps=[('Legacy top5/day',leg_pre,leg_buy),('Hybrid threat top5/day',hyb5_pre,hyb5_buy)]
    if th is not None:comps.append(('Hybrid threat absolute',hab_pre,hab_buy))
    metrics={}
    for name,pr,bu in comps:
        m=metric(bu);metrics[name]=m
        L.append(f'|{name}|{len(pr)}|{len(pr)/hdays if hdays else 0:.2f}|{m["n"]}|{m["n"]/hdays if hdays else 0:.2f}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|')

    L += ['','## Monthly Hybrid top5 stability','|月|PRE R|BUY R|①頭率|7点的中率|ROI|','|---|---:|---:|---:|---:|---:|']
    for mo in MONTHS:
        mr=[r for r in allrows if r.get('month')==mo];mb=defaultdict(list)
        for r in mr:mb[r['date']].append(r)
        p,b=topn_select(mb,'hybrid_pre_p',5);m=metric(b)
        L.append(f'|{mo}|{len(p)}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["roi"]:.1f}%|')

    lm=metrics['Legacy top5/day'];hm=metrics['Hybrid threat top5/day']
    better=(hm['roi']>lm['roi'] and hm['hit']>=lm['hit'] and hm['head']>=lm['head']-1.0)
    L += ['','## v136判定',
          f'- top5 holdout ROI: Legacy **{lm["roi"]:.1f}%** → Hybrid **{hm["roi"]:.1f}%**.',
          f'- top5 holdout 7点的中率: Legacy **{lm["hit"]:.1f}%** → Hybrid **{hm["hit"]:.1f}%**.',
          f'- top5 holdout ①頭率: Legacy **{lm["head"]:.1f}%** → Hybrid **{hm["head"]:.1f}%**.',
          f'- **V136 INNER-THREAT PRE = {"PROMISING" if better else "KEEP LEGACY"}**',
          '- PROMISINGでもproduction即変更せず、9月prospective shadowで確認する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

    rec=[]
    for r in allrows:
        rec.append({'date':r['date'],'month':r['month'],'race_code':r['race_code'],'venue':r.get('venue'),'race':r.get('race'),
                    'legacy_pre_p':r.get('legacy_pre_p'),'hybrid_pre_p':r.get('hybrid_pre_p'),'hybrid_abs_threshold':th,
                    'p109':r.get('p109'),'entry_course':r.get('entry_course'),'head_hit':r.get('head_hit'),
                    'rank_l50':r.get('rank_l50'),'payout100':r.get('payout100')})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)

if __name__=='__main__':main()
