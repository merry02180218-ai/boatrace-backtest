"""v135: rebuild 1-head PRE candidate selection with all-6 pre-exhibition features.

Purpose
- Revisit Stage-1 PRE selection; remove the old mechanical top5/day constraint.
- Keep Stage-2 LIVE unchanged: v109 p>=.72 and boat1 course1.
- Keep tickets unchanged: v110 lambda=.50 top7.
- Compare legacy PRE ranking (boat1-only, top5/day) with a new all-6 PRE model and an absolute probability threshold.

No-leak
- PRE features use race-card/waku10 information only; no current exhibition/ST/original/direct/current entry/odds.
- For each target month, PRE and LIVE models train only on strictly earlier dates.
- Threshold for the new PRE model is chosen only on Mar-May validation and frozen for Jun-Aug holdout.
- Results/payouts are labels/settlement only.
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
OUT='analysis_v135_1head_preselection_rebuild.csv'
SUMMARY='summary_v135_1head_preselection_rebuild.md'
MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
VAL={'2026-03','2026-04','2026-05'}
HOLD={'2026-06','2026-07','2026-08'}
S_CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]
THRESHOLDS=[round(x,2) for x in np.arange(.45,.86,.025)]
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

def fetch_day(ds):
    ymd=ds.replace('-','/')
    cards=rows(f'data/programs/race_cards/{ymd}.csv')
    waku=rows(f'data/programs/waku10/{ymd}.csv')
    wm={r.get('レースコード',''):r for r in waku}
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

def xlegacy(rs):
    a=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in LEGACY_FEATURES]
        vv=str(r.get('venue','')).zfill(2);row += [1.0 if vv==v else 0.0 for v in VENUES]
        a.append(row)
    return np.asarray(a,float)

def xall6(rs,pmap):
    a=[]
    for r in rs:
        x=pmap.get(r.get('race_code'))
        if not x:
            # fallback keeps dimensionality but should be rare
            vals=[0.0]*54
        else:
            vals=[]
            for b in range(1,7):vals += boat_pre(x,b)
        # explicit relative margins boat1 - each opponent on the 9 normalized components
        if x:
            one=boat_pre(x,1)
            for b in range(2,7):
                ob=boat_pre(x,b)
                vals += [one[j]-ob[j] for j in range(9)]
        else: vals += [0.0]*45
        vv=str(r.get('venue','')).zfill(2);vals += [1.0 if vv==v else 0.0 for v in VENUES]
        a.append(vals)
    return np.asarray(a,float)

def fit_lr(X,y):
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))])
    m.fit(X,np.asarray(y,int));return m

def metric(rs):
    q=[r for r in rs if ii(r.get('valid_payout'))==1]
    n=len(q);head=sum(ii(r.get('head_hit')) for r in q)
    hit=sum(1 for r in q if 0<ii(r.get('rank_l50'))<=7)
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get('rank_l50'))<=7)
    ret=sum(ii(r.get('payout100')) for r in q if 0<ii(r.get('rank_l50'))<=7)
    return {'n':n,'head':pct(head,n),'hit':pct(hit,n),'cov':pct(cov,len(heads)),'roi':pct(ret,n*700)}

def legacy_select(byday):
    pre=[];buy=[]
    for d,q in byday.items():
        w=sorted(q,key=lambda r:(-ff(r.get('legacy_pre_p')),r.get('race_code','')))[:5]
        pre+=w;buy += [r for r in w if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1]
    return pre,buy

def threshold_select(rs,th):
    pre=[r for r in rs if ff(r.get('new_pre_p'))>=th]
    buy=[r for r in pre if ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1]
    return pre,buy

def choose_threshold(valrows):
    rows=[]
    for th in THRESHOLDS:
        pre,buy=threshold_select(valrows,th);m=metric(buy)
        days=len({r['date'] for r in valrows});pr=len(pre)/days if days else 0;br=m['n']/days if days else 0
        # prioritize ROI, then hit rate, with practical sample floor and no fixed daily-count target
        ok=m['n']>=180 and pr>=1.0
        rows.append((th,ok,pr,br,m))
    good=[x for x in rows if x[1]] or rows
    best=max(good,key=lambda x:(x[4]['roi'],x[4]['hit'],x[4]['head'],x[4]['n']))
    return best[0],rows

def main():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1]
    pmap=build_pre_map(src)
    prepared={}
    for mo in MONTHS:
        first=date.fromisoformat(mo+'-01')
        tr=[r for r in src if date.fromisoformat(r['date'])<first]
        te=[r for r in src if r.get('month')==mo]
        leg=fit_lr(xlegacy(tr),[ii(r.get('head_hit')) for r in tr])
        new=fit_lr(xall6(tr,pmap),[ii(r.get('head_hit')) for r in tr])
        lp=leg.predict_proba(xlegacy(te))[:,1]
        np0=new.predict_proba(xall6(te,pmap))[:,1]
        live=fit109(tr);p109=live.predict_proba(xmatrix(te))[:,1]
        for r,a,b,c in zip(te,lp,np0,p109):
            r['legacy_pre_p']=float(a);r['new_pre_p']=float(b);r['p109']=float(c)
        print('v135 role',mo,flush=True)
        prepared[mo]=prepare_month(src,mo)

    allrows=sum((prepared[m] for m in MONTHS),[])
    # pmap and PRE scores survive prepare_month copies from src
    allrows=[r for r in allrows if ii(r.get('valid_payout'))==1]
    byday=defaultdict(list)
    for r in allrows:byday[r['date']].append(r)
    legacy_pre,legacy_buy=legacy_select(byday)

    val=[r for r in allrows if r.get('month') in VAL]
    hold=[r for r in allrows if r.get('month') in HOLD]
    th,sweep=choose_threshold(val)
    new_pre,new_buy=threshold_select(allrows,th)
    hold_new_pre,hold_new_buy=threshold_select(hold,th)
    hold_leg_pre=[r for r in legacy_pre if r.get('month') in HOLD]
    hold_leg_buy=[r for r in legacy_buy if r.get('month') in HOLD]

    L=['# v135 1号艇 事前候補選定の再設計','',
       '- Stage2は現行固定: **v109 S(p>=72%) + 1コース維持**。買い目は **v110 λ=.50 top7**。',
       '- Legacy PRE: 1号艇のみ9特徴 + 場、毎日top5。',
       '- New PRE: **6艇全艇**の級別/全国/当地/モーター/枠勝率/全国ST/枠ST順/過去勝利/節間ST + 1号艇との差 + 場。展示前情報だけ。',
       '- New PREは毎日固定本数をやめ、**絶対確率閾値**。閾値はMar-Mayだけで選択しJun-Augへ固定。',
       '- PRE/LIVE学習は対象月より前だけ。現行展示・オリジナル展示・現在進入・オッズはPREに不使用。','',
       '## Mar-May threshold selection','|new PRE閾値|PRE/day|LIVE BUY/day|BUY R|①頭率|7点的中率|coverage|7点ROI|eligible|','|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for t,ok,pr,br,m in sweep:
        L.append(f'|{t:.2f}|{pr:.2f}|{br:.2f}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|{"YES" if ok else "NO"}|')
    L += ['',f'Frozen new PRE threshold = **{th:.2f}**','',
          '## Jun-Aug holdout comparison','|方式|PRE R|PRE/day|LIVE BUY R|BUY/day|①頭率|7点的中率|coverage|7点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    hdays=len({r['date'] for r in hold})
    for name,pr,bu in [('Legacy top5/day',hold_leg_pre,hold_leg_buy),('New all6 absolute',hold_new_pre,hold_new_buy)]:
        m=metric(bu)
        L.append(f'|{name}|{len(pr)}|{len(pr)/hdays if hdays else 0:.2f}|{m["n"]}|{m["n"]/hdays if hdays else 0:.2f}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["cov"]:.1f}%|{m["roi"]:.1f}%|')
    L += ['','## Monthly new PRE stability','|月|PRE R|BUY R|①頭率|7点的中率|7点ROI|','|---|---:|---:|---:|---:|---:|']
    for mo in MONTHS:
        mr=[r for r in allrows if r.get('month')==mo];mp,mb=threshold_select(mr,th);m=metric(mb)
        L.append(f'|{mo}|{len(mp)}|{m["n"]}|{m["head"]:.1f}%|{m["hit"]:.1f}%|{m["roi"]:.1f}%|')
    lm=metric(hold_leg_buy);nm=metric(hold_new_buy)
    better=(nm['roi']>lm['roi'] and nm['hit']>=lm['hit']-1.0 and nm['head']>=lm['head']-1.0)
    L += ['','## v135判定',
          f'- Holdout ROI: Legacy **{lm["roi"]:.1f}%** → New **{nm["roi"]:.1f}%**.',
          f'- Holdout 7点的中率: Legacy **{lm["hit"]:.1f}%** → New **{nm["hit"]:.1f}%**.',
          f'- Holdout ①頭率: Legacy **{lm["head"]:.1f}%** → New **{nm["head"]:.1f}%**.',
          f'- **V135 NEW PRE = {"PROMISING" if better else "KEEP LEGACY / REWORK"}**',
          '- PROMISINGでも即production変更はせず、9月prospectiveで確認する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

    rec=[]
    for r in allrows:
        rec.append({'date':r['date'],'month':r['month'],'race_code':r['race_code'],'venue':r.get('venue'),'race':r.get('race'),
                    'legacy_pre_p':r.get('legacy_pre_p'),'new_pre_p':r.get('new_pre_p'),'new_threshold':th,
                    'new_pre_selected':int(ff(r.get('new_pre_p'))>=th),'p109':r.get('p109'),
                    'live_buy_if_new':int(ff(r.get('new_pre_p'))>=th and ff(r.get('p109'))>=S_CUT and ii(r.get('entry_course'))==1),
                    'entry_course':r.get('entry_course'),'head_hit':r.get('head_hit'),'rank_l50':r.get('rank_l50'),'payout100':r.get('payout100')})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)

if __name__=='__main__':main()
