#!/usr/bin/env python3
from __future__ import annotations
import sys,csv,io,urllib.request,importlib.util
from pathlib import Path
from collections import Counter,defaultdict,deque
import numpy as np,pandas as pd
from backtest import rows as bt_rows
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_3head_a60_playerhistory_curve_v1 as base
import analyze_3head_player_history_3v2_ablation_v2 as ph
import run_3head_wave20_manual_gate as w20

HIST_START=pd.Timestamp('2025-10-01')
TARGET_MONTHS=['dec','jan','feb','mar','apr','may','jun','jul','aug']
RANGES={
 'oct':('2025-10-01','2025-10-31'),'nov':('2025-11-01','2025-11-30'),'dec':('2025-12-01','2025-12-31'),
 'jan':('2026-01-01','2026-01-31'),'feb':('2026-02-01','2026-02-28'),'mar':('2026-03-01','2026-03-31'),
 'apr':('2026-04-01','2026-04-30'),'may':('2026-05-01','2026-05-31'),'jun':('2026-06-01','2026-06-30'),
 'jul':('2026-07-01','2026-07-31'),'aug':('2026-08-01','2026-08-31')}
MONNUM={'dec':12,'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8}
def n(s): return pd.to_numeric(s,errors='coerce')

# Build causal universe for all months using the exact v14 mechanics generalized beyond Jul/Aug.
raw={}
for k,(a,b) in RANGES.items():
    x,r,audit=w20.build_pre_enhanced(a,b,True); raw[k]=(x,r)
frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
_,enh,_=w20.make_pre_scores.__globals__['choose_features'](pd.concat(list(frames.values()),ignore_index=True,sort=False))
hist=pd.concat(list(frames.values()),ignore_index=True,sort=False)

scores={}
for k in TARGET_MONTHS:
    target=frames[k].sort_values(['date','rc']).copy(); out=[]
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv); today=target[target.date.dt.normalize()==day].copy()
        tr=hist[(hist.date<day)&(hist.date>=day-pd.Timedelta(days=42))].copy()
        if len(tr)<500 or tr.y.nunique()<2 or today.empty: continue
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=1800,random_state=161))
        model.fit(tr[enh],tr.y); ptr=model.predict_proba(tr[enh])[:,1]; pp=model.predict_proba(today[enh])[:,1]
        z=today[['rc','date','venue','race_no','y']].copy()
        z['pre_score']=w20.make_pre_scores.__globals__['pct_ref'](ptr,pp); out.append(z)
    if out: scores[k]=pd.concat(out,ignore_index=True).drop_duplicates('rc')
    print('PRE',k,len(scores.get(k,[])))

w20.prefetch_sources.__globals__['END']='2026-08-31'
days,cache=w20.prefetch_sources();post,post_audit=w20.build_motor_exhibition(days,cache)
print('POST_AUDIT',post_audit)

allrows=[]
for k in TARGET_MONTHS:
    if k not in scores: continue
    q=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one')
    q['race_code']=q.rc.astype('int64').astype(str).str.zfill(12); q['month']=k; allrows.append(q)
d=pd.concat(allrows,ignore_index=True)
d=ph.add_player_history(d)
names=ph.NAMES; full=[]
for k in names:
    rel=f'pl_rel3_2_{k}'; d[rel]=n(d[f'b3_pl_{k}'])-n(d[f'b2_pl_{k}'])
    full += [f'b3_pl_{k}',f'b2_pl_{k}',rel]
rn=n(d.race_no);pre=n(d.pre_score)
pool=(rn>=1)&(rn<=12)&(pre>=.925)&base.pg.mask(d,base.pg.A['conds'])&(n(d.post_motor_inner_rank_edge)>=0.0)
d=d.loc[pool].copy()
pred=[]
for day in sorted(d.date.dt.normalize().unique()):
    te=d[d.date.dt.normalize()==day].copy(); tr=d[(d.date<day)&(d.date>=HIST_START)].copy()
    if len(tr)<5 or tr.y.nunique()<2: continue
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
        LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=1800,random_state=322))
    model.fit(tr[full],tr.y.astype(int)); te['ph_score']=model.predict_proba(te[full])[:,1]; pred.append(te)
p=pd.concat(pred,ignore_index=True)
print('POOL_PRED',len(p),p.month.value_counts().to_dict())

# Fixed accepted component semantics.
core=pd.read_csv('core107/accepted_core_fast_v20.csv',dtype={'race_code':str})
core['race_code']=core.race_code.astype(str).str.replace('.0','',regex=False).str.zfill(12)
assert len(core)==107 and core.race_code.nunique()==107
selected=[]
for mon,g in p.groupby('month'):
    a=g[(n(g.pre_score)>=.970)&(n(g.ph_score)>=.50)&(n(g.post_motor_inner_rank_edge)>=.60)].copy()
    fullm=g.copy() # exact accepted v14 FULL semantics: all ranked candidates in pool
    cm=core[pd.to_datetime(core.get('date',core.race_code.str[:8]),errors='coerce').dt.month.eq(MONNUM[mon])].copy()
    # year guard for Jan-Aug versus Dec2025
    dtc=pd.to_datetime(cm.get('date',cm.race_code.str[:8]),errors='coerce')
    year=2025 if mon=='dec' else 2026
    cm=cm[dtc.dt.year.eq(year)].copy()
    union=set(a.race_code)|set(fullm.race_code)|set(cm.race_code)
    # Feature-covered selection rows. CORE-only outside p cannot be routed, keep coverage stats explicit.
    z=g[g.race_code.isin(union)].copy()
    z['selected_models']=z.race_code.map(lambda rc:'+'.join([nm for nm,codes in [('CORE',set(cm.race_code)),('A+',set(a.race_code)),('FULL',set(fullm.race_code))] if rc in codes]))
    selected.append(z)
    print('SELECT',mon,'UNION',len(union),'COVERED',len(z),'CORE',len(cm),'A',len(a),'FULL',len(fullm))
sel=pd.concat(selected,ignore_index=True)

# Settled result order.
BASE='https://boatracecsv.github.io/data'
need=set(sel.race_code); res={}
for day in pd.date_range('2025-12-01','2026-08-31'):
    url=f"{BASE}/results/realtime/{day:%Y/%m/%d}.csv"
    try:
        with urllib.request.urlopen(url,timeout=30) as r: rows=list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
    except Exception: continue
    for rr in rows:
        rc=''.join(c for c in str(rr.get('レースコード','')) if c.isdigit()).zfill(12)
        if rc in need:
            vals=[str(rr.get(f'{k}着_艇番','')).strip() for k in [1,2,3]]
            if all(v in '123456' and len(v)==1 for v in vals): res[rc]=tuple(map(int,vals))
sel['actual_tuple']=sel.race_code.map(res)
assert sel.actual_tuple.notna().all(), f"MISSING_RESULTS {sel.loc[sel.actual_tuple.isna(),'race_code'].tolist()[:20]}"
sel['first']=sel.actual_tuple.map(lambda x:x[0]);sel['second']=sel.actual_tuple.map(lambda x:x[1]);sel['third']=sel.actual_tuple.map(lambda x:x[2])
sel['date2']=pd.to_datetime(sel.race_code.str[:8],format='%Y%m%d')

print('SELECTED_TOTAL',len(sel),'HEADS',int(sel.first.eq(3).sum()),'HEAD_RATE',round(sel.first.eq(3).mean(),4))

# Strict-prior boat2 player history at this exact venue ("local").
# Existing b2_pl_frame_* already represents lane-2 historical win / top2 rate.
def _rc(x):
    z=str(x or '').strip().replace('.0','')
    return z.zfill(12)
def _ii(x):
    try:return int(float(x))
    except:return 0
def _blank_local():
    return {'n':0,'w':0,'p2':0,'recent':deque(maxlen=20)}

target_codes=set(sel.race_code.astype(str))
local_state=defaultdict(_blank_local)
local_snap={}
sample_keys_printed=False
for day in pd.date_range('2025-10-01','2026-08-31'):
    y=day.strftime('%Y/%m/%d')
    cards={_rc(r.get('レースコード')):r for r in bt_rows(f'data/programs/race_cards/{y}.csv')}
    if (not sample_keys_printed) and cards:
        ks=sorted({k for r in cards.values() for k in r.keys() if ('当地' in str(k) or '勝率' in str(k))})
        print('CARD_RATE_KEYS',ks[:80]); sample_keys_printed=True
    for code in [c for c in target_codes if c.startswith(day.strftime('%Y%m%d'))]:
        card=cards.get(code)
        if card is None: continue
        reg=str(card.get('艇2_登録番号','')).strip()
        venue=code[8:10]
        q=local_state.get((reg,venue))
        if q is None:
            vals={'b2_local_n':0,'b2_local_win':1/6,'b2_local_p2':1/3,'b2_local_recent_p2':1/3}
        else:
            nn=q['n']
            vals={
              'b2_local_n':nn,
              'b2_local_win':(q['w']+2/6)/(nn+2),
              'b2_local_p2':(q['p2']+2/3)/(nn+2),
              'b2_local_recent_p2':sum(q['recent'])/len(q['recent']) if q['recent'] else 1/3,
            }
        local_snap[code]=vals
    rm={_rc(r.get('レースコード')):r for r in bt_rows(f'data/results/realtime/{y}.csv')}
    for code,card in cards.items():
        rr=rm.get(code); w=_ii((rr or {}).get('1着_艇番')); sec=_ii((rr or {}).get('2着_艇番'))
        if w not in range(1,7) or sec not in range(1,7) or w==sec: continue
        venue=code[8:10]
        for b in range(1,7):
            reg=str(card.get(f'艇{b}_登録番号','')).strip()
            if not reg: continue
            q=local_state[(reg,venue)]
            q['n']+=1; q['w']+=int(w==b); q['p2']+=int(w==b or sec==b); q['recent'].append(int(w==b or sec==b))

local_df=pd.DataFrame.from_dict(local_snap,orient='index')
local_df.index.name='race_code'; local_df=local_df.reset_index()
sel=sel.merge(local_df,on='race_code',how='left',validate='one_to_one')
print('LOCAL_COVERAGE',int(sel.b2_local_win.notna().sum()),'OF',len(sel),
      'N_MED',float(sel.b2_local_n.median()),'N_GE3',int((sel.b2_local_n>=3).sum()))


def learn_thresholds(tr):
    return {'b2':float(n(tr.b2_pl_frame_p2).quantile(.6)),'b1':float(n(tr.b1_pl_frame_win).quantile(.6)),
            'se':float(n(tr.post_straight_edge2).quantile(.5))}
def route12(df,th,scale):
    b2=n(df.b2_pl_frame_p2); b1=n(df.b1_pl_frame_win); se=n(df.post_straight_edge2)
    sig32=(b2>=th['b2'])&(se<=th['se']); sig31=(b1>=th['b1'])&(se>=th['se'])
    both=sig32&sig31
    if both.any():
        b2z=(b2-th['b2'])/scale['b2']; b1z=(b1-th['b1'])/scale['b1']
        sig32=sig32&(~both|(b2z>=b1z));sig31=sig31&(~both|(b1z>b2z))
    return pd.Series(np.where(sig32,'2',np.where(sig31,'1','NONE')),index=df.index)

def route_conf(df,route_name,th,scale):
    if route_name=='1':
        a=(n(df.b1_pl_frame_win)-th['b1'])/scale['b1']
        e=(n(df.post_straight_edge2)-th['se'])/scale['se']
    elif route_name=='2':
        a=(n(df.b2_pl_frame_p2)-th['b2'])/scale['b2']
        e=(th['se']-n(df.post_straight_edge2))/scale['se']
    else:
        return pd.Series(np.nan,index=df.index)
    return pd.concat([a,e],axis=1).min(axis=1)
def third_rank(train,s):
    poss=[b for b in [1,2,4,5,6] if b!=s]; cnt=Counter(train.loc[train.second.eq(s),'third']);ov=Counter(train.third)
    return sorted(poss,key=lambda b:(cnt[b],ov[b]),reverse=True)
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

# Official odds loader.
spec=importlib.util.spec_from_file_location('oc','tools/fetch_official_closing_odds3t.py');oc=importlib.util.module_from_spec(spec);spec.loader.exec_module(oc)
def archive_row(rc):
    dt=pd.Timestamp(rc[:8]); pth=Path(f'data/official_closing_odds3t/{dt:%Y}/{dt:%m}/{dt:%d}.csv')
    if not pth.exists(): return None
    q=pd.read_csv(pth,dtype={'jcd':str});q['jcd']=q.jcd.astype(str).str.zfill(2)
    z=q[(q.jcd==rc[8:10])&(pd.to_numeric(q.rno,errors='coerce')==int(rc[10:12]))]
    return z.iloc[-1].to_dict() if len(z) else None
od={}
for rc in sel.race_code:
    row=archive_row(rc)
    if row is None:
        vals=oc.parse(oc.fetch(oc.BASE.format(hd=rc[:8],jcd=int(rc[8:10]),rno=int(rc[10:12]))))
        if vals: row=vals
    if row is not None: od[rc]=row
print('ODDS_COVERAGE',len(od),'OF',len(sel))

def alloc_equal(tix,budget=5000):
    units=budget//100;base=units//len(tix);rem=units%len(tix)
    return {x:100*(base+(1 if i<rem else 0)) for i,x in enumerate(tix)}

out=[]
PLAYER_FEATS=[
 'b2_pl_frame_win','b2_pl_frame_p2','b2_pl_all_win','b2_pl_all_p2','b2_pl_recent_p2',
 'b2_local_win','b2_local_p2','b2_local_recent_p2','b2_local_n'
]
QS=[0.25,0.50,0.75]

for testmon in TARGET_MONTHS[1:]:
    test_start=pd.Timestamp(RANGES[testmon][0])
    train=sel[(sel.date2<test_start)&sel.first.eq(3)].copy()
    test=sel[sel.month.eq(testmon)].copy()
    if len(train)<8 or test.empty: continue
    th=learn_thresholds(train)
    scale={'b1':float(n(train.b1_pl_frame_win).std())+1e-9,
           'b2':float(n(train.b2_pl_frame_p2).std())+1e-9,
           'se':float(n(train.post_straight_edge2).std())+1e-9}
    train['route']=route12(train,th,scale)
    test['route']=route12(test,th,scale)
    tr2=train[train.route.eq('2')].copy()
    te2=test[test.route.eq('2')].copy()

    # Thresholds come from prior route2 rows only; labels are not used.
    cuts={}
    for c in PLAYER_FEATS:
        if c not in tr2.columns: continue
        zz=n(tr2[c])
        if zz.notna().sum()>=6:
            cuts[c]={q:float(zz.quantile(q)) for q in QS}

    print('R2_MONTH',testmon,'TRAIN_R2',len(tr2),'TEST_R2',len(te2),
          'TRUE32',int(((te2.first==3)&(te2.second==2)).sum()))
    if len(te2):
        pos=te2[(te2.first==3)&(te2.second==2)]
        neg=te2[~((te2.first==3)&(te2.second==2))]
        for c in PLAYER_FEATS:
            if c in te2.columns:
                print('R2_FEATURE_MEAN',testmon,c,'POS',round(float(n(pos[c]).mean()),4) if len(pos) else None,
                      'NEG',round(float(n(neg[c]).mean()),4) if len(neg) else None)

    for _,r in te2.iterrows():
        if r.race_code not in od: continue
        tix=[]
        for t3 in third_rank(train,2)[:4]:
            if t3!=2:tix.append(f'3-2-{int(t3)}')
        stakes=alloc_equal(tix,5000)
        actual=f'{r.first}-{r.second}-{r.third}'
        hit=int(actual in stakes and r.first==3)
        ret=float(stakes.get(actual,0))*float(od[r.race_code].get(actual,0)) if hit else 0.
        true32=int(r.first==3 and r.second==2)
        base_rec={'month':testmon,'race_code':r.race_code,'true32':true32,'exact3_hit':hit,
                  'invest':sum(stakes.values()),'return':ret,'profit':ret-sum(stakes.values())}
        rec=base_rec.copy();rec.update({'rule':'BASE'});out.append(rec)
        for c,qmap in cuts.items():
            v=pd.to_numeric(pd.Series([r.get(c,np.nan)]),errors='coerce').iloc[0]
            if not np.isfinite(v): continue
            for q,cut in qmap.items():
                for direc in ['ge','le']:
                    if (v>=cut if direc=='ge' else v<=cut):
                        rec=base_rec.copy();rec.update({'rule':f'{c}:{direc}:q{q:.2f}'})
                        out.append(rec)

z=pd.DataFrame(out);z.to_csv('route2_player_local_v28.csv',index=False)

def stat(g):
    inv=g.invest.sum();ret=g['return'].sum()
    months=[]
    for m,gm in g.groupby('month'):
        mi=gm.invest.sum();mr=gm['return'].sum()
        months.append((m,len(gm),int(gm.true32.sum()),float(gm.true32.mean()),100*mr/mi if mi else np.nan))
    return len(g),int(g.true32.sum()),float(g.true32.mean()),int(g.exact3_hit.sum()),100*ret/inv if inv else np.nan,ret-inv,months

for rule,g in z.groupby('rule'):
    R,t32,r32,h,roi,profit,months=stat(g)
    if rule!='BASE' and R<20: continue
    print('PLAYER_RULE',rule,'R',R,'TRUE32',t32,'TRUE32_RATE',round(r32,4),
          'EXACT3',h,'ROI',round(roi,2),'PROFIT',round(profit,1),
          'POS_MONTHS',sum(x[4]>=100 for x in months),'OF',len(months))
    print('PLAYER_RULE_MONTHS',rule,[(m,r,t,round(rt,3),round(ri,2)) for m,r,t,rt,ri in months])

print('V28_ROUTE2_PLAYER_LOCAL_OK')
