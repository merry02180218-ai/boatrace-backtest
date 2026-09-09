#!/usr/bin/env python3
"""v243: feature audit + race-expansion search around the verified v242-derived 90R rule.

IN-SAMPLE exploratory search over Dec2025-Aug2026 (user explicitly allowed Jul/Aug too).
No claim of pristine validation.

Reference rule (verified from v242 settlement output):
  v242 bet == 1
  p3 >= 0.45
  raw_top_n in [7,18]
  comp_odds in [3.05,4.00]

Goal: find simple pre-result feature rules that can (a) remove weak baseline races and
(b) rescue additional v242-buyable races, seeking > baseline race count while improving
both realized hit rate and realized ROI. All settlement stays exact 10,000-yen canonical
inverse-odds Dutch / 100-yen Hamilton rounding from v242/v205.
"""
import itertools
import numpy as np
import pandas as pd
import analyze_v242_3head_target_comp3_min5_max10 as v242

BANK=10000
OUT='analysis_v243_3head_expand_feature_audit.csv'
RULES='analysis_v243_3head_expand_rule_search.csv'
SUM='summary_v243_3head_expand_feature_audit.md'


def ff(x):
    try:
        y=float(x)
        return y if np.isfinite(y) else np.nan
    except Exception:
        return np.nan


def scored_order(r,pair):
    rows=[]
    for s in v242.v234.v222.OPP:
        for t in v242.v234.v222.OPP:
            if s==t: continue
            try:
                vec=np.asarray(v242.v234.v222.pairvec(r,s,t,'V221'),dtype=float)
            except Exception:
                return None,None
            if not np.isfinite(vec).all():
                return None,None
            try:
                p=float(pair.predict_proba(np.asarray([vec],float))[0,1])
            except Exception:
                return None,None
            rows.append((p,f'3-{int(s)}-{int(t)}'))
    rows.sort(key=lambda x:(-x[0],x[1]))
    ts=[x[1] for x in rows]
    sc=np.asarray([x[0] for x in rows],float)
    return ts,sc


def metrics(g):
    n=len(g)
    if n==0:return dict(R=0,hits=0,hit=np.nan,roi=np.nan,ret=0.)
    h=int(g.trifecta_hit.sum()); ret=float(g.ret.sum())
    return dict(R=n,hits=h,hit=h/n,roi=ret/(n*BANK),ret=ret)


def rule_mask(df,feat,op,thr):
    x=pd.to_numeric(df[feat],errors='coerce')
    if op=='>=': return x>=thr
    return x<=thr


def main():
    cov=v242.v234.reconstruct(); common=v242.v234.validate_parser()
    if (cov.source=='missing').any(): raise RuntimeError('missing Waku10; no imputation')
    d,dc,vc,basefs=v242.v234.build_restored()
    fs=v242.v234.full_features(d,basefs); fs=[x for x in fs if x in d.columns]
    odds=v242.v234.v205.load_odds(); oi=odds.set_index('race_code',drop=False)
    rec=[]
    for mon in v242.v234.MONTHS:
        first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1); tr=d[d._date<first]
        pair=v242.v234.v222.fit_pair(tr,'V221')
        base_te,_=v242.v234.v223.fit_head(d,list(basefs),vc,first,nextm)
        k=max(1,int((base_te._p>=.30).sum()))
        te,_=v242.v234.v223.fit_head(d,fs,vc,first,nextm)
        sel=te.nlargest(k,'_p').copy()
        for _,r in sel.iterrows():
            if v242.v234.v223.ii(r.get('valid_result'))!=1 or v242.v234.v223.ii(r.get('course3'),3)!=3: continue
            act=v242.v234.v222.v166.combo(r.get('actual_combo'))
            actual='-'.join(map(str,act)) if len(act)==3 else ''
            if not actual: continue
            code=str(r.get('race_code','')).zfill(12)
            z={'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(r._p),'y3':int(r._y),
               'pair_rank_invalid':0,'odds_available':0,'bet':0,'raw_top_n':np.nan,'raw_comp_odds':np.nan,
               'top_n':np.nan,'comp_odds':np.nan,'capped_at_10':0,'positive_tickets':np.nan,'trifecta_hit':0,
               'ret':np.nan,'profit':np.nan}
            ts,sc=scored_order(r,pair)
            if ts is None:
                z['pair_rank_invalid']=1; rec.append(z); continue
            z['pair_top_score']=float(sc[0]); z['pair_second_score']=float(sc[1]); z['pair_gap']=float(sc[0]-sc[1])
            z['pair_std']=float(sc.std()); z['pair_top5_mean']=float(sc[:5].mean()); z['pair_top10_mean']=float(sc[:10].mean())
            for f in fs: z['f__'+f]=ff(r.get(f))
            if code in oi.index:
                z['odds_available']=1
                od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
                s=v242.settle(ts,od,actual)
                if s is not None:
                    if s.get('raw_n') is not None:
                        z['raw_top_n']=s['raw_n']; z['raw_comp_odds']=s['raw_comp']
                    if s.get('action')=='bet':
                        z.update({'bet':1,'top_n':s['top_n'],'comp_odds':s['comp_odds'],'capped_at_10':s['capped_at_10'],
                                  'positive_tickets':s['positive_tickets'],'trifecta_hit':s['hit'],'ret':s['ret'],'profit':s['profit']})
            rec.append(z)
    q=pd.DataFrame(rec)
    q.to_csv(OUT,index=False)

    bmask=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    base=q[bmask].copy(); bm=metrics(base)
    pool=q[(q.bet==1)&(~bmask)].copy()

    # Feature audit: only pre-result model features + pair confidence summaries.
    features=['p3','pair_top_score','pair_second_score','pair_gap','pair_std','pair_top5_mean','pair_top10_mean']+[c for c in q.columns if c.startswith('f__')]
    features=[f for f in features if f in q.columns and pd.to_numeric(q[f],errors='coerce').notna().sum()>=30]

    audits=[]
    wins=base[base.trifecta_hit==1]; losses=base[base.trifecta_hit==0]
    for f in features:
        a=pd.to_numeric(wins[f],errors='coerce'); b=pd.to_numeric(losses[f],errors='coerce')
        pooled=pd.to_numeric(base[f],errors='coerce').std()
        eff=(a.mean()-b.mean())/pooled if pooled and np.isfinite(pooled) else np.nan
        audits.append((f,a.mean(),b.mean(),eff))
    audits=sorted(audits,key=lambda x:abs(x[3]) if np.isfinite(x[3]) else -1,reverse=True)

    # Build simple exclusion candidates from baseline and rescue candidates from outside baseline.
    ex=[]; rs=[]
    for f in features:
        xb=pd.to_numeric(base[f],errors='coerce').dropna(); xp=pd.to_numeric(pool[f],errors='coerce').dropna()
        if len(xb)>=20:
            for thr in np.unique(np.quantile(xb,[.1,.2,.3,.4,.5,.6,.7,.8,.9])):
                for op in ('>=','<='):
                    keep=rule_mask(base,f,op,float(thr)).fillna(False)
                    g=base[keep]; m=metrics(g)
                    if m['R']>=max(40,int(.55*bm['R'])):
                        ex.append({'kind':'exclude_keep','feature':f,'op':op,'thr':float(thr),**m,'mask':keep.to_numpy()})
        if len(xp)>=20:
            for thr in np.unique(np.quantile(xp,[.1,.2,.3,.4,.5,.6,.7,.8,.9])):
                for op in ('>=','<='):
                    add=rule_mask(pool,f,op,float(thr)).fillna(False)
                    g=pool[add]; m=metrics(g)
                    if 5<=m['R']<=160:
                        rs.append({'kind':'rescue','feature':f,'op':op,'thr':float(thr),**m,'mask':add.to_numpy()})

    # Structural rescue buckets keep interpretation close to the current rule.
    buckets={
      'low_p3_only':(pool.p3<.45)&pool.raw_top_n.between(7,18)&pool.comp_odds.between(3.05,4.0),
      'low_comp_only':(pool.p3>=.45)&pool.raw_top_n.between(7,18)&(pool.comp_odds<3.05),
      'high_comp_only':(pool.p3>=.45)&pool.raw_top_n.between(7,18)&(pool.comp_odds>4.0),
      'raw_outside_only':(pool.p3>=.45)&(~pool.raw_top_n.between(7,18))&pool.comp_odds.between(3.05,4.0),
    }
    for name,mk in buckets.items():
        if mk.sum()>=5:
            g=pool[mk]; m=metrics(g)
            rs.append({'kind':'rescue_bucket','feature':name,'op':'==','thr':1.0,**m,'mask':mk.to_numpy()})

    # Keep best single rules for combination search to avoid enormous in-sample grid.
    ex=sorted(ex,key=lambda r:(r['roi'] if np.isfinite(r['roi']) else -9,r['hit'] if np.isfinite(r['hit']) else -9,r['R']),reverse=True)[:120]
    rs=sorted(rs,key=lambda r:(r['roi'] if np.isfinite(r['roi']) else -9,r['hit'] if np.isfinite(r['hit']) else -9,r['R']),reverse=True)[:180]

    rows=[]
    # rescue-only policies
    for r in rs:
        g=pd.concat([base,pool[r['mask']]],ignore_index=True); m=metrics(g)
        rows.append({'policy':'base+rescue','exclude_feature':'','exclude_op':'','exclude_thr':np.nan,
                     'rescue_feature':r['feature'],'rescue_op':r['op'],'rescue_thr':r['thr'],'added_R':int(r['R']),**m})
    # exclusion + rescue policies
    for e in ex:
        kept=base[e['mask']]
        for r in rs:
            added=pool[r['mask']]
            g=pd.concat([kept,added],ignore_index=True); m=metrics(g)
            if m['R']<=bm['R']: continue
            rows.append({'policy':'exclude+rescue','exclude_feature':e['feature'],'exclude_op':e['op'],'exclude_thr':e['thr'],
                         'rescue_feature':r['feature'],'rescue_op':r['op'],'rescue_thr':r['thr'],'added_R':int(r['R']),**m})
    rr=pd.DataFrame(rows)
    if len(rr):
        rr['delta_R']=rr.R-bm['R']; rr['delta_hit_pp']=100*(rr.hit-bm['hit']); rr['delta_roi_pp']=100*(rr.roi-bm['roi'])
        rr['improves_all']=(rr.R>bm['R'])&(rr.hit>bm['hit'])&(rr.roi>bm['roi'])
        rr['meets_110_35']=(rr.R>bm['R'])&(rr.hit>=.35)&(rr.roi>=1.10)
        rr=rr.sort_values(['improves_all','R','roi','hit'],ascending=[False,False,False,False])
        rr.drop(columns=[],errors='ignore').to_csv(RULES,index=False)
    else:
        pd.DataFrame().to_csv(RULES,index=False)

    L=['# v243 3-head feature audit + expansion search','',
       '- IN-SAMPLE exploratory search over Dec2025-Aug2026; Jul/Aug explicitly included by user. Not pristine validation.',
       '- Settlement remains exact 10,000-yen canonical inverse-odds Dutch.',
       f'- Waku10 validation: {common} races, 0 mismatches.','',
       '## Verified reference policy',
       '- v242 bet; p3>=0.45; raw TopN 7..18; composite odds 3.05..4.00.',
       f'- R={bm["R"]}, hits={bm["hits"]}, hit={100*bm["hit"]:.2f}%, ROI={100*bm["roi"]:.2f}%.','',
       '## Strongest baseline win/loss feature separations','|feature|win mean|loss mean|std effect (win-loss)|','|---|---:|---:|---:|']
    for f,a,b,effect in audits[:20]:
        L.append(f'|{f}|{a:.5f}|{b:.5f}|{effect:.3f}|')
    if len(rr):
        good=rr[rr.improves_all].copy()
        L += ['', '## Policies improving race count + hit rate + ROI simultaneously',
              '|R|hit|ROI|dR|dHit pp|dROI pp|exclude keep rule|rescue rule|','|---:|---:|---:|---:|---:|---:|---|---|']
        for _,x in good.head(25).iterrows():
            exs='none' if not x.exclude_feature else f'{x.exclude_feature} {x.exclude_op} {x.exclude_thr:.5g}'
            rss=f'{x.rescue_feature} {x.rescue_op} {x.rescue_thr:.5g}'
            L.append(f'|{int(x.R)}|{100*x.hit:.2f}%|{100*x.roi:.2f}%|{int(x.delta_R)}|{x.delta_hit_pp:.2f}|{x.delta_roi_pp:.2f}|{exs}|{rss}|')
        if len(good)==0:L.append('|0|--|--|--|--|--|No simple rule found|--|')
        L += ['', '## Largest-R policies meeting hit>=35% and ROI>=110%',
              '|R|hit|ROI|exclude keep rule|rescue rule|','|---:|---:|---:|---|---|']
        g2=rr[rr.meets_110_35].sort_values(['R','roi','hit'],ascending=[False,False,False]).head(20)
        for _,x in g2.iterrows():
            exs='none' if not x.exclude_feature else f'{x.exclude_feature} {x.exclude_op} {x.exclude_thr:.5g}'
            rss=f'{x.rescue_feature} {x.rescue_op} {x.rescue_thr:.5g}'
            L.append(f'|{int(x.R)}|{100*x.hit:.2f}%|{100*x.roi:.2f}%|{exs}|{rss}|')
    with open(SUM,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__': main()
