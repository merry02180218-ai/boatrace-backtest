#!/usr/bin/env python3
"""Regression audit: canonical historical 3-head path vs serialized cached-LIVE path.

This is a software-equivalence audit, not new model selection. Jul/Aug remain NON-PRISTINE.
It checks:
1) current regenerated OLD/in-memory path against frozen v243 artifact;
2) OLD/in-memory fitted head+V221 models against joblib round-tripped models;
3) v242 TopN/odds/Dutch and selected v243 rule;
4) exact v249 rolling PRE S/A/B grades and final S+A performance.
"""
from __future__ import annotations
import io,json,joblib
import numpy as np
import pandas as pd

import smoke_20260910_3head_fast_bridge as fast
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v242_3head_target_comp3_min5_max10 as v242

KEEP=-0.1999999999999999
RESCUE=0.5672342857142857
BANK=10000
GOLD='golden_v243/analysis_v243_3head_expand_feature_audit.csv'
OUT='audit_cached_live_historical_equivalence.csv'
SUM='summary_cached_live_historical_equivalence.md'
JS='audit_cached_live_historical_equivalence.json'


def roundtrip(x):
    b=io.BytesIO();joblib.dump(x,b,compress=0);b.seek(0);return joblib.load(b)

def fit_head_model(d,fs0,vc,first):
    fs=v223.numeric_ok(d,fs0);tr=d[d._date<first].copy()
    for c in fs:tr[c]=pd.to_numeric(tr[c],errors='coerce')
    cats=[vc] if vc and vc not in fs else []
    m=v165.model(fs,cats);m.fit(tr[fs+cats],tr._y.astype(int))
    return m,fs,cats

def predict(m,te,fs,cats):
    x=te.copy()
    for c in fs:x[c]=pd.to_numeric(x[c],errors='coerce')
    return m.predict_proba(x[fs+cats])[:,1]

def order_and_scores(r,pair):
    rows=[]
    for s in v222.OPP:
        for t in v222.OPP:
            if s==t:continue
            try:vec=np.asarray(v222.pairvec(r,s,t,'V221'),float)
            except Exception:return None,None
            if not np.isfinite(vec).all():return None,None
            p=float(pair.predict_proba(np.asarray([vec],float))[0,1])
            rows.append((p,int(s),int(t)))
    rows.sort(key=lambda z:(-z[0],z[1],z[2]))
    return [f'3-{s}-{t}' for _,s,t in rows],np.asarray([p for p,_,_ in rows])

def final_rule(bet,p3,raw_n,comp,minus,attack):
    buy=bool(bet)
    base=bool(buy and p3>=.45 and pd.notna(raw_n) and 7<=raw_n<=18 and pd.notna(comp) and 3.05<=comp<=4.0)
    keep=bool(np.isfinite(minus) and minus>=KEEP)
    rescue=bool(np.isfinite(attack) and attack<=RESCUE)
    return bool(buy and ((base and keep) or ((not base) and rescue))),base,keep,rescue

def ticket_state(ts,od,ch):
    if ch.get('action')!='bet':return ''
    vals=ch['vals']; stakes=np.asarray(v234.v205.round_dutch(vals,BANK),int)
    return '|'.join(f'{q}:{int(s)}' for q,s in zip(ts[:ch['top_n']],stakes) if s>0)

def make_rec(mon,r,p3,pair,oi,tag,fs):
    code=str(r.get('race_code','')).zfill(12)
    z={'path':tag,'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(p3),'y3':int(r._y)}
    ts,sc=order_and_scores(r,pair)
    z['pair_rank_invalid']=int(ts is None);z['pair_order20']='' if ts is None else '|'.join(ts)
    z.update({'odds_available':0,'bet':0,'raw_top_n':np.nan,'raw_comp_odds':np.nan,'top_n':np.nan,'comp_odds':np.nan,'trifecta_hit':0,'ret':np.nan,'profit':np.nan,'ticket_state':''})
    for f in fs:z['f__'+f]=pd.to_numeric(pd.Series([r.get(f)]),errors='coerce').iloc[0]
    if ts is None:
        z.update({'final':0,'base':0,'keep':0,'rescue':0});return z
    act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
    if code in oi.index:
        z['odds_available']=1;od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
        ch=v242.choose_n(ts,od)
        if ch.get('raw_n') is not None:z['raw_top_n']=ch['raw_n'];z['raw_comp_odds']=ch['raw_comp']
        if ch.get('action')=='bet':
            z['bet']=1;z['top_n']=ch['top_n'];z['comp_odds']=ch['comp_odds'];z['ticket_state']=ticket_state(ts,od,ch)
            vals=ch['vals'];stakes=np.asarray(v234.v205.round_dutch(vals,BANK),int);ret=0.;hit=0
            if actual in ts[:ch['top_n']]:
                j=ts[:ch['top_n']].index(actual)
                if stakes[j]>0:hit=1;ret=float(stakes[j])*float(vals[j])
            z['trifecta_hit']=hit;z['ret']=ret;z['profit']=ret-BANK
    minus=float(r.get('c_b3_minus_b5_st',np.nan));attack=float(r.get('c_attack3_stretch',np.nan))
    final,base,keep,rescue=final_rule(z['bet'],z['p3'],z['raw_top_n'],z['comp_odds'],minus,attack)
    z.update({'final':int(final),'base':int(base),'keep':int(keep),'rescue':int(rescue)})
    return z

def pre_cols(q):
    bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
    cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
    return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]
def pre_score(tr,te,cs):
    y=tr._target.astype(int);fs=[]
    for c in cs:
        x=pd.to_numeric(tr[c],errors='coerce');a=x[y==1].dropna();b=x[y==0].dropna();sd=x.std()
        if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e):fs.append((abs(e),e,c))
    fs=sorted(fs,reverse=True)[:12];s=pd.Series(0.,index=te.index)
    for _,e,c in fs:
        a=pd.to_numeric(tr[c],errors='coerce');x=pd.to_numeric(te[c],errors='coerce');med=a.median();sd=a.std()
        if np.isfinite(sd) and sd>1e-12:s+=np.sign(e)*((x.fillna(med)-med)/sd).clip(-4,4)
    return s
def add_pre_grade(q):
    q=q.copy();q['_target']=q.final.astype(int);ms=sorted(q.month.unique());cs=pre_cols(q);out=[]
    for i,m in enumerate(ms):
        if i<2:continue
        tr=q[q.month.isin(ms[:i])];te=q[q.month==m].copy();te['_score']=pre_score(tr,te,cs);out.append(te)
    p=pd.concat(out,ignore_index=True);p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first',ascending=True)
    p['grade']=np.where(p._pct>=.70,'S',np.where(p._pct>=.20,'A','B'))
    return p

def val_equal(a,b,tol=1e-12):
    if pd.isna(a) and pd.isna(b):return True
    try:return abs(float(a)-float(b))<=tol
    except:return str(a)==str(b)

def main():
    # Fast reconstruction changes only execution strategy; formulas are the frozen v224 formulas.
    v234.reconstruct=fast.cached_reconstruct
    v224.add_decomp=fast.fast_add_decomp
    v234.v224.add_decomp=fast.fast_add_decomp
    cov=v234.reconstruct()
    if (cov.source=='missing').any():raise RuntimeError('cached v234 has missing days')
    d,dc,vc,basefs=v234.build_restored();fs=[x for x in v234.full_features(d,basefs) if x in d.columns]
    odds=v234.v205.load_odds();oi=odds.set_index('race_code',drop=False)
    old=[];cached=[];cmp=[]
    for mon in v234.MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
        pair_old=v222.fit_pair(tr,'V221');pair_cache=roundtrip(pair_old)
        base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
        te_old,_=v223.fit_head(d,fs,vc,first,nextm)
        hm,hfs,cats=fit_head_model(d,fs,vc,first);hm=roundtrip(hm)
        te_cache=d[(d._date>=first)&(d._date<nextm)].copy();te_cache['_p']=predict(hm,te_cache,hfs,cats)
        # Compare entire monthly head prediction vector before top-k selection.
        po=te_old.set_index('race_code')['_p'];pc=te_cache.set_index('race_code')['_p'];common=po.index.intersection(pc.index)
        max_all=float(np.max(np.abs(po.loc[common].to_numpy()-pc.loc[common].to_numpy()))) if len(common) else np.nan
        so=te_old.nlargest(k,'_p').copy();sc=te_cache.nlargest(k,'_p').copy()
        if set(so.race_code.astype(str))!=set(sc.race_code.astype(str)):raise RuntimeError(f'top-k set mismatch {mon}')
        cm=sc.set_index(sc.race_code.astype(str))
        for _,r in so.iterrows():
            if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3:continue
            act=v222.v166.combo(r.get('actual_combo'))
            if len(act)!=3:continue
            code=str(r.get('race_code','')).zfill(12);rc=cm.loc[code]
            a=make_rec(mon,r,float(r._p),pair_old,oi,'old',fs);b=make_rec(mon,rc,float(rc._p),pair_cache,oi,'cached',fs)
            old.append(a);cached.append(b)
            cmp.append({'month':mon,'race_code':code,'head_month_max_abs_diff':max_all,'p3_abs_diff':abs(a['p3']-b['p3']),
                        'pair_order_match':int(a['pair_order20']==b['pair_order20']),'rawN_match':int(val_equal(a['raw_top_n'],b['raw_top_n'])),
                        'rawComp_match':int(val_equal(a['raw_comp_odds'],b['raw_comp_odds'])),'topN_match':int(val_equal(a['top_n'],b['top_n'])),
                        'comp_match':int(val_equal(a['comp_odds'],b['comp_odds'])),'final_match':int(a['final']==b['final']),
                        'ticket_stakes_match':int(a['ticket_state']==b['ticket_state']),'ret_match':int(val_equal(a['ret'],b['ret']))})
    qo=pd.DataFrame(old);qc=pd.DataFrame(cached);c=pd.DataFrame(cmp)
    # frozen v243 artifact is a second independent golden comparison for OLD regeneration
    gold=pd.read_csv(GOLD,dtype={'race_code':str});gold['race_code']=gold.race_code.astype(str).str.zfill(12);qo['race_code']=qo.race_code.astype(str).str.zfill(12)
    gg=gold.set_index('race_code');oo=qo.set_index('race_code');common=gg.index.intersection(oo.index)
    golden={'golden_rows':len(gold),'regen_rows':len(qo),'race_set_match':set(gg.index)==set(oo.index),'common':len(common),
            'p3_max_abs_diff':float(np.nanmax(np.abs(pd.to_numeric(gg.loc[common,'p3'])-pd.to_numeric(oo.loc[common,'p3']))))}
    for col in ['bet','raw_top_n','raw_comp_odds','top_n','comp_odds','trifecta_hit','ret','profit']:
        mm=0
        for code in common:
            if not val_equal(gg.at[code,col],oo.at[code,col],1e-10):mm+=1
        golden[col+'_mismatch']=mm
    po=add_pre_grade(qo);pc=add_pre_grade(qc)
    mo=po[['race_code','grade','final']].set_index('race_code');mc=pc[['race_code','grade','final']].set_index('race_code');ix=mo.index.intersection(mc.index)
    grade_mismatch=int((mo.loc[ix,'grade']!=mc.loc[ix,'grade']).sum());pre_final_mismatch=int((mo.loc[ix,'final']!=mc.loc[ix,'final']).sum())
    sa_o=po[po.grade.isin(['S','A']) & (po.final==1)].copy();sa_c=pc[pc.grade.isin(['S','A']) & (pc.final==1)].copy()
    def agg(x):
        return {'bets':len(x),'hits':int(x.trifecta_hit.sum()),'stake':len(x)*BANK,'payout':float(x.ret.fillna(0).sum()),'profit':float(x.ret.fillna(0).sum()-len(x)*BANK),'roi':float(100*x.ret.fillna(0).sum()/(len(x)*BANK)) if len(x) else np.nan}
    ao=agg(sa_o);ac=agg(sa_c)
    clean_o=agg(sa_o[sa_o.month<='2026-06']);shadow_o=agg(sa_o[sa_o.month>='2026-07'])
    summary={'rows_compared':len(c),'max_p3_abs_diff':float(c.p3_abs_diff.max()),'max_month_head_abs_diff':float(c.head_month_max_abs_diff.max()),
             'pair_order_mismatch':int((c.pair_order_match==0).sum()),'rawN_mismatch':int((c.rawN_match==0).sum()),
             'rawComp_mismatch':int((c.rawComp_match==0).sum()),'topN_mismatch':int((c.topN_match==0).sum()),'comp_mismatch':int((c.comp_match==0).sum()),
             'final_mismatch':int((c.final_match==0).sum()),'ticket_stakes_mismatch':int((c.ticket_stakes_match==0).sum()),'return_mismatch':int((c.ret_match==0).sum()),
             'pre_grade_mismatch':grade_mismatch,'pre_final_mismatch':pre_final_mismatch,'old_SA_final':ao,'cached_SA_final':ac,
             'old_FebJun':clean_o,'old_JulAug_NON_PRISTINE':shadow_o,'golden_v243':golden}
    c.to_csv(OUT,index=False);open(JS,'w').write(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    passed=(golden['race_set_match'] and golden['p3_max_abs_diff']<=1e-10 and all(v==0 for k,v in golden.items() if k.endswith('_mismatch')) and
            summary['max_p3_abs_diff']<=1e-12 and summary['pair_order_mismatch']==0 and summary['rawN_mismatch']==0 and summary['rawComp_mismatch']==0 and
            summary['topN_mismatch']==0 and summary['comp_mismatch']==0 and summary['final_mismatch']==0 and summary['ticket_stakes_mismatch']==0 and
            summary['return_mismatch']==0 and grade_mismatch==0 and pre_final_mismatch==0 and ao==ac)
    L=['# Cached LIVE historical equivalence audit','',f"- RESULT: {'PASS' if passed else 'FAIL'}",'- Software regression/equivalence audit only; no retuning.','- Jul/Aug remain NON-PRISTINE.','',
       '## OLD vs cached model path',f"- compared rows: {len(c)}",f"- max p3 abs diff: {summary['max_p3_abs_diff']:.3g}",f"- max all-month head prediction abs diff: {summary['max_month_head_abs_diff']:.3g}",
       f"- pair-order mismatches: {summary['pair_order_mismatch']}",f"- rawN mismatches: {summary['rawN_mismatch']}",f"- comp-odds mismatches: {summary['comp_mismatch']}",
       f"- final-decision mismatches: {summary['final_mismatch']}",f"- ticket/stake mismatches: {summary['ticket_stakes_mismatch']}",f"- return mismatches: {summary['return_mismatch']}",
       f"- v249 PRE grade mismatches: {grade_mismatch}",'','## S+A final performance',f"- OLD: {ao}",f"- CACHED: {ac}",f"- Feb-Jun: {clean_o}",f"- Jul-Aug NON-PRISTINE: {shadow_o}",'','## Frozen v243 golden artifact check',f"- {golden}"]
    open(SUM,'w').write('\n'.join(L)+'\n');print('\n'.join(L))
    if not passed:raise SystemExit(2)
if __name__=='__main__':main()
