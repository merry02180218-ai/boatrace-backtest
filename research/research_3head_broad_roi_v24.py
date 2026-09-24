#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys, csv, io, urllib.request, importlib.util
from collections import Counter
from pathlib import Path
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0,'research'); sys.path.insert(0,'.')

# 1) Rebuild exact accepted Jul/Aug union identities + covered causal feature universe.
src=open('research/run_3head_three_layer_independent_core_v14.py',encoding='utf-8').read()
needle="p=pd.concat(pred,ignore_index=True)"
assert needle in src
src=src.replace(needle,needle+"\n    p.to_csv('v24_feature_universe.csv',index=False)",1)
needle2="yu=yy[yy.race_code.isin(union)]"
assert needle2 in src
src=src.replace(needle2,needle2+"\n        _aud=yu.copy(); _aud['month']=mon; _aud['models']=_aud.race_code.map(lambda rc:'+'.join(membership.get(rc,[]))); detail.extend(_aud[['month','race_code','y','models']].to_dict('records'))",1)
needle3="z=pd.DataFrame(rows);z.to_csv(CSV,index=False)"
assert needle3 in src
src=src.replace(needle3,needle3+"\n    pd.DataFrame(detail).to_csv('v24_union_identity.csv',index=False)",1)
open('/tmp/v24_union_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v24_union_builder.py',run_name='__main__')

ids=pd.read_csv('v24_union_identity.csv',dtype={'race_code':str})
ids.race_code=ids.race_code.str.zfill(12)
assert len(ids)==123 and ids.race_code.nunique()==123, f'UNION_ASSERT {len(ids)} {ids.race_code.nunique()}'

u=pd.read_csv('v24_feature_universe.csv')
u['race_code']=pd.to_numeric(u.rc,errors='coerce').astype('Int64').astype(str).str.zfill(12)
d=ids.merge(u.drop_duplicates('race_code'),on='race_code',how='left',suffixes=('','_u'))
covered=d[d.pre_score.notna()].copy()
print('UNION_TOTAL',len(d),'FEATURE_COVERED',len(covered),'COVERAGE',round(len(covered)/len(d),4))
print('COVERED_MONTH',covered.month.value_counts().to_dict())

# 2) Fetch settled result order for all accepted union races.
BASE='https://boatracecsv.github.io/data'
def fetch_results(day):
    url=f"{BASE}/results/realtime/{day:%Y/%m/%d}.csv"
    with urllib.request.urlopen(url,timeout=30) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))

need=set(ids.race_code)
res={}
for day in pd.date_range('2026-07-01','2026-08-31'):
    try: rows=fetch_results(day)
    except Exception as e:
        print('RESULT_FETCH_FAIL',day.date(),repr(e)); continue
    for rr in rows:
        rc=''.join(c for c in str(rr.get('レースコード','')) if c.isdigit()).zfill(12)
        if rc in need:
            vals=[str(rr.get(f'{k}着_艇番','')).strip() for k in [1,2,3]]
            if all(v in '123456' and len(v)==1 for v in vals):
                res[rc]=tuple(map(int,vals))
covered['actual']=covered.race_code.map(res)
assert covered.actual.notna().all(), f'RESULT_MISSING {covered.loc[covered.actual.isna(),"race_code"].tolist()}'
covered['first']=covered.actual.map(lambda z:z[0]);covered['second']=covered.actual.map(lambda z:z[1]);covered['third']=covered.actual.map(lambda z:z[2])
head=covered[covered.first.eq(3)].copy()
print('HEAD_COVERED',len(head),'JUL',int((head.month=='jul').sum()),'AUG',int((head.month=='aug').sum()))

# 3) Research routing learned on opposite-month HEAD HIT subset, applied to all selected races.
def learn_thresholds(tr):
    return {'b2':float(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').quantile(.6)),
            'b1':float(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').quantile(.6)),
            'se':float(pd.to_numeric(tr.post_straight_edge2,errors='coerce').quantile(.5))}

def route(df,th,outer_cut):
    b2=pd.to_numeric(df.b2_pl_frame_p2,errors='coerce'); b1=pd.to_numeric(df.b1_pl_frame_win,errors='coerce'); se=pd.to_numeric(df.post_straight_edge2,errors='coerce')
    sig32=(b2>=th['b2'])&(se<=th['se']); sig31=(b1>=th['b1'])&(se>=th['se'])
    both=sig32&sig31
    if both.any():
        b2z=(b2-th['b2'])/(b2.std()+1e-9); b1z=(b1-th['b1'])/(b1.std()+1e-9)
        sig32=sig32 & (~both | (b2z>=b1z)); sig31=sig31 & (~both | (b1z>b2z))
    base=~(sig32|sig31); b4=pd.to_numeric(df.b4_pl_recent_p2,errors='coerce')
    so=base & b4.ge(outer_cut)
    return pd.Series(np.where(sig32,'2',np.where(sig31,'1',np.where(so,'OUTER_STRONG','FALLBACK'))),index=df.index)

def long_outer(df):
    rows=[]
    for _,r in df.iterrows():
        for b in [4,5,6]:
            z={'race_code':r.race_code,'boat':b,'y':int(int(r.second)==b)}
            for suf in ['pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']:
                c=f'b{b}_{suf}'; z[suf]=r[c] if c in r.index else np.nan
            for suf in ['win','top2','top3','ewma_rank','ewma_st']:
                c=f'post_motor_b{b}_{suf}'; z['motor_'+suf]=r[c] if c in r.index else np.nan
            rows.append(z)
    return pd.DataFrame(rows)

def third_rank(train,s):
    poss=[b for b in [1,2,4,5,6] if b!=s]
    cnt=Counter(train.loc[train.second.eq(s),'third']); overall=Counter(train.third)
    return sorted(poss,key=lambda b:(cnt[b],overall[b]),reverse=True)

ticket_rows=[]
for testm in ['jul','aug']:
    train=head[head.month.ne(testm)].copy()
    test=covered[covered.month.eq(testm)].copy()
    th=learn_thresholds(train)
    tmp=route(train,th,np.inf)
    base=train[tmp.eq('FALLBACK')]
    outer_cut=float(pd.to_numeric(base.b4_pl_recent_p2,errors='coerce').quantile(.5))
    train['route']=route(train,th,outer_cut); test['route']=route(test,th,outer_cut)

    tr_os=train[train.route.eq('OUTER_STRONG')].copy(); te_os=test[test.route.eq('OUTER_STRONG')].copy()
    outer_orders={}
    if len(tr_os)>=3 and tr_os.second.isin([4,5,6]).any() and len(te_os):
        ltr=long_outer(tr_os); lte=long_outer(te_os)
        feats=[c for c in ltr.columns if c not in ['race_code','boat','y'] and pd.to_numeric(ltr[c],errors='coerce').notna().sum()>=max(4,len(ltr)//3)]
        if ltr.y.nunique()==2 and feats:
            model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=324))
            model.fit(ltr[feats],ltr.y); lte['p']=model.predict_proba(lte[feats])[:,1]
            for rc,g in lte.groupby('race_code'): outer_orders[rc]=g.sort_values('p',ascending=False).boat.astype(int).tolist()
    outer_freq=[b for b,_ in Counter(train.loc[train.second.isin([4,5,6]),'second']).most_common()]
    outer_freq += [b for b in [4,5,6] if b not in outer_freq]
    fallback=[b for b,_ in Counter(train.second).most_common() if b in [1,2,4,5,6]]

    for _,r in test.iterrows():
        if r.route=='2': seconds=[2]
        elif r.route=='1': seconds=[1]
        elif r.route=='OUTER_STRONG': seconds=outer_orders.get(r.race_code,outer_freq)[:2]
        else: seconds=fallback[:3]
        tickets=[]
        for s in seconds:
            thirds=third_rank(train,s)[:4 if r.route!='FALLBACK' else 3]
            for t in thirds:
                if t!=s: tickets.append(f'3-{int(s)}-{int(t)}')
        tickets=list(dict.fromkeys(tickets))
        ticket_rows.append({'month':testm,'race_code':r.race_code,'route':r.route,'first':r.first,'second':r.second,'third':r.third,
                            'actual':f'{r.first}-{r.second}-{r.third}','tickets':'|'.join(tickets),'n':len(tickets)})

t=pd.DataFrame(ticket_rows)
assert len(t)==len(covered)
print('TICKET_RACES',len(t),'AVG_N',round(t.n.mean(),3),'ROUTES',t.route.value_counts().to_dict())

# 4) Official closing odds. Use repository archive where present; targeted official fetch for missing selected races.
spec=importlib.util.spec_from_file_location('oc','tools/fetch_official_closing_odds3t.py'); oc=importlib.util.module_from_spec(spec); spec.loader.exec_module(oc)

def archive_row(rc):
    dt=pd.Timestamp(rc[:8]); p=Path(f'data/official_closing_odds3t/{dt:%Y}/{dt:%m}/{dt:%d}.csv')
    if not p.exists(): return None
    q=pd.read_csv(p,dtype={'jcd':str}); jcd=rc[8:10]; rno=int(rc[10:12])
    q['jcd']=q.jcd.astype(str).str.zfill(2)
    z=q[(q.jcd==jcd)&(pd.to_numeric(q.rno,errors='coerce')==rno)]
    return z.iloc[-1].to_dict() if len(z) else None

od={}
fetched=0
for rc in t.race_code:
    row=archive_row(rc)
    if row is None:
        hd=rc[:8];jcd=int(rc[8:10]);rno=int(rc[10:12]);url=oc.BASE.format(hd=hd,jcd=jcd,rno=rno)
        vals=oc.parse(oc.fetch(url))
        if vals:
            row=vals; fetched+=1
    if row is not None: od[rc]=row
print('ODDS_COVERAGE',len(od),'OF',len(t),'TARGET_FETCHED',fetched)

# 5) ROI. BROAD tickets only. Exact 100-yen unit arithmetic.
# Policies: flat 100/ticket; 5000 equal split; 3-1 route bankroll light (2500 vs 5000); strong-only.
def alloc_equal(tix,budget):
    if not tix:return {}
    units=budget//100; base=units//len(tix); rem=units%len(tix)
    return {x:100*(base+(1 if i<rem else 0)) for i,x in enumerate(tix)}

rows=[]
for _,r in t.iterrows():
    if r.race_code not in od: continue
    tix=r.tickets.split('|') if r.tickets else []
    odds=od[r.race_code]
    policies={
      'FLAT100':{x:100 for x in tix},
      'BUDGET5000':alloc_equal(tix,5000),
      'LIGHT31':alloc_equal(tix,2500 if r.route=='1' else 5000),
      'STRONG5000':alloc_equal(tix,5000) if r.route!='FALLBACK' else {},
      'STRONG_LIGHT31':(alloc_equal(tix,2500 if r.route=='1' else 5000) if r.route!='FALLBACK' else {}),
    }
    for pol,stakes in policies.items():
        inv=sum(stakes.values())
        actual=r.actual
        hit=int(actual in stakes and int(r.first)==3 and actual in odds and pd.notna(odds[actual]))
        ret=float(stakes.get(actual,0))*float(odds.get(actual,0)) if hit else 0.0
        rows.append({'month':r.month,'race_code':r.race_code,'route':r.route,'policy':pol,'invest':inv,'hit':hit,'return':ret,'profit':ret-inv,'actual':actual,'n':len(tix)})

z=pd.DataFrame(rows);z.to_csv('integrated_broad_roi_v24.csv',index=False)
for pol,g in z.groupby('policy'):
    inv=g.invest.sum();ret=g['return'].sum()
    print('ROI',pol,'RACES',len(g),'BET_RACES',int((g.invest>0).sum()),'HIT',int(g.hit.sum()),'INVEST',int(inv),'RETURN',round(ret,1),'ROI',round(100*ret/inv,2) if inv else None,'PROFIT',round(ret-inv,1))
    for m,gm in g.groupby('month'):
        mi=gm.invest.sum();mr=gm['return'].sum()
        print('ROI_MONTH',pol,m,'RACES',len(gm),'BET',int((gm.invest>0).sum()),'HIT',int(gm.hit.sum()),'ROI',round(100*mr/mi,2) if mi else None,'PROFIT',round(mr-mi,1))
    for route,gr in g[g.invest>0].groupby('route'):
        ii=gr.invest.sum();rr=gr['return'].sum()
        print('ROI_ROUTE',pol,route,'R',len(gr),'HIT',int(gr.hit.sum()),'ROI',round(100*rr/ii,2) if ii else None,'PROFIT',round(rr-ii,1))

print('V24_ROI_OK')
