from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct, ff, norm_metric

V320=Path('analysis_v320_1head_exact3_ticket_policy_best_race.csv')
OUT=Path('/tmp/v326'); OUT.mkdir(parents=True,exist_ok=True)
PRELOAD=date(2025,10,1)

MODEL_FEATURES=[
    'one_ex','one_st','one_turn','one_straight','one_orig_avg',
    'sec_ex_mean_margin','sec_st_mean_margin','sec_turn_mean_margin','sec_straight_mean_margin',
    'third_turn_mean_margin','third_straight_mean_margin','third_orig_mean_margin',
    'covered_turn_weak_margin','covered_straight_weak_margin',
    'covered_balance_min','uncovered_turn_dominance','uncovered_straight_dominance',
]
RULE_FEATURES=[
    'sec_ex_mean_margin','sec_st_mean_margin','sec_turn_mean_margin','sec_straight_mean_margin',
    'third_turn_mean_margin','third_straight_mean_margin','third_orig_mean_margin',
    'covered_turn_weak_margin','covered_straight_weak_margin','covered_balance_min',
]
RULE_READY={
    'sec_ex_mean_margin':'tkz_all6',
    'sec_st_mean_margin':'stt_all6',
    'sec_turn_mean_margin':'orig_turn_all6',
    'sec_straight_mean_margin':'orig_straight_all6',
    'third_turn_mean_margin':'orig_turn_all6',
    'third_straight_mean_margin':'orig_straight_all6',
    'third_orig_mean_margin':'orig_avg_all6',
    'covered_turn_weak_margin':'orig_turn_all6',
    'covered_straight_weak_margin':'orig_straight_all6',
    'covered_balance_min':'orig_turn_straight_all6',
}

def pct(n,d): return 100*n/d if d else float('nan')
def bycode(rs): return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def metrics(x):
    n=len(x);h=int(x.hit.sum()) if n else 0;hh=int(x.head_hit.sum()) if n else 0
    return {'R':n,'H':h,'exact3_rate':pct(h,n),'head_H':hh,'head_rate':pct(hh,n)}

def st_bias(sums,allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}
def update_st(strows,sums,allv):
    for r in strows:
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:
                sums[b].append(v);allv.append(v)

def all6_numeric(row,prefix):
    return bool(row) and all(ff(row.get(f'艇{b}_{prefix}')) is not None for b in range(1,7))

def orig_metric_all6(row,target):
    if not row:return False
    for k in range(1,5):
        if norm_metric(row.get(f'計測項目{k}',''))!=target:continue
        if all(ff(row.get(f'艇{b}_値{k}')) is not None for b in range(1,7)):
            return True
    return False

def orig_avg_all6(row):
    if not row:return False
    used=0
    for k in range(1,5):
        label=norm_metric(row.get(f'計測項目{k}',''))
        if not label:continue
        vals=[ff(row.get(f'艇{b}_値{k}')) for b in range(1,7)]
        if not any(v is not None for v in vals):continue
        used+=1
        if not all(v is not None for v in vals):return False
    return used>0

def raw_completeness(tkz_row,stt_row,orig_row):
    tkz_all6=all6_numeric(tkz_row,'展示タイム')
    stt_all6=all6_numeric(stt_row,'スタート展示')
    orig_turn_all6=orig_metric_all6(orig_row,'回り足') or orig_metric_all6(orig_row,'まわり足')
    orig_straight_all6=orig_metric_all6(orig_row,'直線')
    orig_avg_ok=orig_avg_all6(orig_row)
    return {
        'tkz_all6':int(tkz_all6),'stt_all6':int(stt_all6),
        'orig_turn_all6':int(orig_turn_all6),'orig_straight_all6':int(orig_straight_all6),
        'orig_avg_all6':int(orig_avg_ok),
        'orig_turn_straight_all6':int(orig_turn_all6 and orig_straight_all6),
    }

def parse_tickets(s):
    ts=[]
    for t in str(s).split(';'):
        p=t.strip().split('-')
        if len(p)==3 and all(z.isdigit() for z in p):ts.append(tuple(map(int,p)))
    if len(ts)!=3: raise AssertionError(f'expected exactly 3 tickets: {s}')
    if any(t[0]!=1 for t in ts): raise AssertionError(f'non-1 head ticket: {s}')
    return ts

def ticket_groups(base):
    ts=parse_tickets(base['tickets'])
    seconds=sorted({t[1] for t in ts});thirds=sorted({t[2] for t in ts})
    covered=sorted((set(seconds)|set(thirds))-{1});uncovered=sorted(set(range(2,7))-set(covered))
    if not covered:raise AssertionError('empty covered opponents')
    sec_un=sorted(set(range(2,7))-set(seconds));third_un=sorted(set(range(2,7))-set(thirds))
    return seconds,thirds,covered,uncovered,sec_un,third_un

def avg(vals): return float(np.mean(vals)) if vals else float('nan')
def mx(vals): return max(vals) if vals else float('nan')
def mn(vals): return min(vals) if vals else float('nan')
def margin_mean(group,uncovered,metric):
    return avg([metric[b] for b in group])-mx([metric[b] for b in uncovered]) if group and uncovered else float('nan')
def margin_weak(group,uncovered,metric):
    return mn([metric[b] for b in group])-mx([metric[b] for b in uncovered]) if group and uncovered else float('nan')

def partial_feature_row(base,ex,st,os,audit):
    seconds,thirds,covered,uncovered,sec_un,third_un=ticket_groups(base)
    out={k:float('nan') for k in MODEL_FEATURES}
    out.update({
        'second_boats':'-'.join(map(str,seconds)),'third_boats':'-'.join(map(str,thirds)),
        'covered_boats':'-'.join(map(str,covered)),'uncovered_boats':'-'.join(map(str,uncovered)),
    })
    if audit['tkz_all6'] and all(b in ex for b in range(1,7)):
        out['one_ex']=ex[1]
        out['sec_ex_mean_margin']=margin_mean(seconds,sec_un,ex)
    if audit['stt_all6'] and all(b in st for b in range(1,7)):
        out['one_st']=st[1]
        out['sec_st_mean_margin']=margin_mean(seconds,sec_un,st)
    turn={b:os[b]['turn'] for b in range(1,7)}
    straight={b:os[b]['straight'] for b in range(1,7)}
    orig={b:os[b]['avg'] for b in range(1,7)}
    if audit['orig_turn_all6']:
        out['one_turn']=turn[1]
        out['sec_turn_mean_margin']=margin_mean(seconds,sec_un,turn)
        out['third_turn_mean_margin']=margin_mean(thirds,third_un,turn)
        out['covered_turn_weak_margin']=margin_weak(covered,uncovered,turn)
        out['uncovered_turn_dominance']=mx([turn[b] for b in uncovered])-mx([turn[b] for b in covered]) if uncovered else -1.0
    if audit['orig_straight_all6']:
        out['one_straight']=straight[1]
        out['sec_straight_mean_margin']=margin_mean(seconds,sec_un,straight)
        out['third_straight_mean_margin']=margin_mean(thirds,third_un,straight)
        out['covered_straight_weak_margin']=margin_weak(covered,uncovered,straight)
        out['uncovered_straight_dominance']=mx([straight[b] for b in uncovered])-mx([straight[b] for b in covered]) if uncovered else -1.0
    if audit['orig_avg_all6']:
        out['one_orig_avg']=orig[1]
        out['third_orig_mean_margin']=margin_mean(thirds,third_un,orig)
    if audit['orig_turn_straight_all6']:
        out['covered_balance_min']=mn([turn[b] for b in covered]+[straight[b] for b in covered])
    return out

def build_dataset():
    x=pd.read_csv(V320,dtype={'race_code':str})
    x['race_code']=x.race_code.astype(str).str.zfill(12)
    x['hit']=pd.to_numeric(x.hit,errors='coerce').fillna(0).astype(int)
    x['head_hit']=pd.to_numeric(x.head_hit,errors='coerce').fillna(0).astype(int)
    if len(x)!=345 or int(x.hit.sum())!=139 or int(x.head_hit.sum())!=290:raise AssertionError('v320 identity mismatch')
    wanted={c for c in x.race_code};selected_days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted})
    selected_day_set=set(selected_days);last=max(selected_days);sums=defaultdict(list);allv=[];features={}
    d=PRELOAD
    while d<=last:
        ymd=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{ymd}.csv');bias=st_bias(sums,allv)
        if d in selected_day_set:
            tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=bycode(strows);orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
            for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
                tr=tkz.get(code,{});sr=stt.get(code,{});orr=orig.get(code,{})
                audit={'has_tkz':int(code in tkz),'has_stt':int(code in stt),'has_orig':int(code in orig),**raw_completeness(tr,sr,orr)}
                strict=int(all(audit[k] for k in ['tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6']))
                audit['source_complete']=strict
                ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
                b=x.loc[x.race_code.eq(code)].iloc[0]
                z=partial_feature_row(b,ex,st,os,audit);z.update(audit);features[code]=z
        update_st(strows,sums,allv);d+=timedelta(days=1)
    blank={'source_complete':0,'has_tkz':0,'has_stt':0,'has_orig':0,'tkz_all6':0,'stt_all6':0,
           'orig_turn_all6':0,'orig_straight_all6':0,'orig_avg_all6':0,'orig_turn_straight_all6':0}
    rowsout=[]
    for _,r in x.iterrows():
        z=r.to_dict();z.update(features.get(r.race_code,blank));rowsout.append(z)
    y=pd.DataFrame(rowsout)
    for c in MODEL_FEATURES:
        if c not in y:y[c]=np.nan
        y[c]=pd.to_numeric(y[c],errors='coerce')
    y['model_ready']=y[MODEL_FEATURES].notna().all(axis=1).astype(int)
    y.to_csv(OUT/'v326_ticketaware_dataset.csv',index=False)
    return y

def feature_ready(df,feat):
    return df[RULE_READY[feat]].fillna(0).eq(1) & df[feat].notna()

def rule_search(disc,val):
    rowsout=[]
    for feat in RULE_FEATURES:
        dd=disc[feature_ready(disc,feat)];vv=val[feature_ready(val,feat)]
        if len(dd)<25 or len(vv)<10:continue
        for t in np.unique(np.quantile(dd[feat],np.arange(.10,.91,.10))):
            for op in ('>=','<='):
                a=dd[dd[feat]>=t] if op=='>=' else dd[dd[feat]<=t]
                b=vv[vv[feat]>=t] if op=='>=' else vv[vv[feat]<=t]
                dm=metrics(a);vm=metrics(b)
                rowsout.append({'kind':'1d','feature':feat,'ready_flag':RULE_READY[feat],'op':op,'threshold':float(t),
                    'disc_ready_R':len(dd),'val_ready_R':len(vv),
                    **{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
    c=pd.DataFrame(rowsout)
    if c.empty:return c,None
    ok=c[(c.val_R>=15)&(c.val_exact3_rate>=50)&(c.disc_R>=25)]
    if ok.empty:ok=c[(c.val_R>=10)&(c.val_exact3_rate>=48)&(c.disc_R>=20)]
    if ok.empty:return c,None
    return c,ok.sort_values(['val_R','val_exact3_rate','disc_exact3_rate'],ascending=[False,False,False]).iloc[0].to_dict()

def logit_search(disc,val):
    tr=disc[disc.model_ready==1].copy();va=val[val.model_ready==1].copy()
    if len(tr)<30 or len(va)<10:return pd.DataFrame(),None,None
    model=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000))])
    model.fit(tr[MODEL_FEATURES],tr.hit)
    pdsc=model.predict_proba(tr[MODEL_FEATURES])[:,1];pv=model.predict_proba(va[MODEL_FEATURES])[:,1]
    rr=[]
    for t in np.unique(np.quantile(pdsc,np.arange(.10,.91,.05))):
        a=tr[pdsc>=t];b=va[pv>=t];dm=metrics(a);vm=metrics(b)
        rr.append({'kind':'logit','threshold':float(t),'disc_ready_R':len(tr),'val_ready_R':len(va),
                   **{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
    c=pd.DataFrame(rr);ok=c[(c.val_R>=15)&(c.val_exact3_rate>=50)&(c.disc_R>=25)]
    if ok.empty:ok=c[(c.val_R>=10)&(c.val_exact3_rate>=48)&(c.disc_R>=20)]
    if ok.empty:return c,None,model
    return c,ok.sort_values(['val_R','val_exact3_rate','disc_exact3_rate'],ascending=[False,False,False]).iloc[0].to_dict(),model

def apply(df,best,model=None):
    if best is None:return df.iloc[0:0]
    if best['kind']=='1d':
        z=df[feature_ready(df,best['feature'])]
        return z[z[best['feature']]>=best['threshold']] if best['op']=='>=' else z[z[best['feature']]<=best['threshold']]
    z=df[df.model_ready==1].copy();z['pass_prob']=model.predict_proba(z[MODEL_FEATURES])[:,1]
    return z[z.pass_prob>=best['threshold']]

def main():
    y=build_dataset();print('RECONCILE',metrics(y));print('STRICT_SOURCE_COMPLETE',int(y.source_complete.sum()),'MODEL_READY',int(y.model_ready.sum()))
    print('RAW_COMPLETENESS','tkz_all6',int(y.tkz_all6.sum()),'stt_all6',int(y.stt_all6.sum()),
          'orig_turn_all6',int(y.orig_turn_all6.sum()),'orig_straight_all6',int(y.orig_straight_all6.sum()),
          'orig_avg_all6',int(y.orig_avg_all6.sum()),'orig_turn_straight_all6',int(y.orig_turn_straight_all6.sum()))
    for feat in RULE_FEATURES:print('RULE_READY',feat,RULE_READY[feat],int(feature_ready(y,feat).sum()))
    for m,g in y.groupby('month'):print('BASE_MONTH',m,metrics(g),'strict',int(g.source_complete.sum()),'model_ready',int(g.model_ready.sum()))
    disc=y[y.month.isin(['2026-02','2026-03','2026-04'])];val=y[y.month.eq('2026-05')];fwd=y[y.month.eq('2026-06')]
    c1,b1=rule_search(disc,val);cl,bl,model=logit_search(disc,val)
    c1.to_csv(OUT/'v326_candidates_1d.csv',index=False);cl.to_csv(OUT/'v326_candidates_logit.csv',index=False)
    choices=[]
    if b1 is not None:choices.append(('1d',b1,None))
    if bl is not None:choices.append(('logit',bl,model))
    chosen=None
    if choices:
        choices.sort(key=lambda z:(z[1].get('val_R',0),z[1].get('val_exact3_rate',0),1 if z[0]=='1d' else 0),reverse=True);chosen=choices[0]
    summary={'candidate':'NONE','forward_supported':False}
    if chosen:
        typ,best,mdl=chosen
        key=f"{best['feature']} {best['op']} {best['threshold']:.6f}" if typ=='1d' else f"logit p>={best['threshold']:.6f}"
        p=apply(fwd,best,mdl);skip=fwd[~fwd.index.isin(p.index)];pm=metrics(p);sm=metrics(skip);bm=metrics(fwd)
        supported=(pm['R']>=10 and (pm['exact3_rate']>=50 or pm['exact3_rate']>=bm['exact3_rate']+5))
        summary={'candidate':key,'kind':typ,'val_R':best.get('val_R'),'val_exact3_rate':best.get('val_exact3_rate'),
                 'disc_R':best.get('disc_R'),'disc_exact3_rate':best.get('disc_exact3_rate'),
                 'jun_pass_R':pm['R'],'jun_pass_H':pm['H'],'jun_pass_exact3_rate':pm['exact3_rate'],'jun_pass_head_rate':pm['head_rate'],
                 'jun_skip_R':sm['R'],'jun_skip_H':sm['H'],'jun_skip_exact3_rate':sm['exact3_rate'],'jun_base_exact3_rate':bm['exact3_rate'],
                 'forward_supported':bool(supported)}
        print('FROZEN_CANDIDATE',key,best);print('JUN_PASS',pm);print('JUN_SKIP',sm);print('FORWARD_SUPPORTED',supported)
    else:print('FROZEN_CANDIDATE NONE')
    pd.DataFrame([summary]).to_csv(OUT/'v326_summary.csv',index=False)
    with open(OUT/'summary_v326_1head_ticketaware_exhibition.md','w',encoding='utf-8') as f:
        f.write('# v326 ticket-aware exhibition postfilter\n\n')
        f.write(f"- frozen baseline: {len(y)}R / {int(y.hit.sum())} exact3 / {int(y.head_hit.sum())} head hits\n")
        f.write(f"- strict all-feature source complete: {int(y.source_complete.sum())}; full model-ready: {int(y.model_ready.sum())}\n")
        f.write(f"- raw all6: tkz={int(y.tkz_all6.sum())}; stt={int(y.stt_all6.sum())}; original turn={int(y.orig_turn_all6.sum())}; original straight={int(y.orig_straight_all6.sum())}; original avg={int(y.orig_avg_all6.sum())}\n")
        for k,v in summary.items():f.write(f'- {k}: {v}\n')
        f.write('\nOne-dimensional rules use only their required actual source family. Logistic remains fully source-complete. No Jul/Aug or September outcome is read by this script. Jul/Aug reference is allowed only if forward_supported=True.\n')

if __name__=='__main__':main()
