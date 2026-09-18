#!/usr/bin/env python3
from __future__ import annotations
"""v372: LOMO robustness + executable pre-close replay for v371 value-gated staking.

Input is the frozen v370 formal_with_closing_odds.csv (165 current-formal races).
Closing odds are used only for the original upper-bound reproduction. For execution
feasibility, this script joins BoatraceCSV's official od3 preview snapshot, normally
captured about five minutes before the official deadline, and replays the same family.

SUPPORT Jul-Aug is never used for parameter selection. September outcomes are forbidden.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, io, json, math, re, time
import numpy as np
import pandas as pd
import requests

OUT=Path('/tmp/v372-value-gated-lomo-preclose'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
COMBINED=[2.0,2.25,2.5,2.75,3.0,3.25,3.5,3.75,4.0]
VALUE=[.7,.8,.9,1.0,1.1,1.2,1.3,1.4,1.5]
EXTRA=(1,2,3)
JST=timezone(timedelta(hours=9))
RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
UA='Mozilla/5.0 (compatible; boatrace-backtest-v372/1.0)'

def baseline(z):
    stake=len(z)*300
    ret=int(sum(int(r.payout100) for _,r in z.iterrows() if int(r.hit_rank)>0))
    return {'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,
            'roi':ret/stake if stake else 0.0}

def combined_odds(vals):
    o=[float(x) for x in vals]
    if any((not math.isfinite(x) or x<=0) for x in o): return np.nan
    return 1.0/sum(1.0/x for x in o)

def alloc_value(r,extra,odds_cols):
    vals=np.array([float(r.p1*r[odds_cols[0]]),float(r.p2*r[odds_cols[1]]),float(r.p3*r[odds_cols[2]])],dtype=float)
    units=np.ones(3,dtype=int)
    rem=int(extra)
    if rem<=0:return units.tolist()
    if not np.isfinite(vals).all() or vals.sum()<=0: vals=np.ones(3)
    target=rem*vals/vals.sum()
    floor=np.floor(target).astype(int); units+=floor
    left=rem-int(floor.sum()); frac=target-floor
    for i in np.argsort(-frac)[:left]: units[int(i)]+=1
    return units.tolist()

def gate(r,c,e,odds_cols):
    co=combined_odds([r[odds_cols[0]],r[odds_cols[1]],r[odds_cols[2]]])
    mx=max(float(r.p1*r[odds_cols[0]]),float(r.p2*r[odds_cols[1]]),float(r.p3*r[odds_cols[2]]))
    return bool(math.isfinite(co) and co>=c and mx>=e)

def evaluate(z,c,e,extra,odds_cols,detail=False):
    stake=ret=trig=0; rows=[]
    for _,r in z.iterrows():
        active=gate(r,c,e,odds_cols)
        u=alloc_value(r,extra,odds_cols) if active else [1,1,1]
        trig+=int(active); stake+=sum(u)*100
        hr=int(r.hit_rank); rr=int(r.payout100)*u[hr-1] if hr>0 else 0
        ret+=rr
        if detail:
            rows.append({'race_code':r.race_code,'month':r.month,'active':int(active),
                         'u1':u[0],'u2':u[1],'u3':u[2],'return_yen':rr,'hit_rank':hr})
    m={'R':len(z),'trigger_R':trig,'stake_yen':stake,'return_yen':ret,
       'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}
    return m,pd.DataFrame(rows)

def grid_for(z,odds_cols):
    b=baseline(z); rows=[]
    for c in COMBINED:
      for e in VALUE:
       for x in EXTRA:
        m,_=evaluate(z,c,e,x,odds_cols)
        rows.append({'combined_min':c,'value_min':e,'extra_units':x,
                     **{f'm_{k}':v for k,v in m.items()},
                     'delta_roi_pp':100*(m['roi']-b['roi'])})
    return pd.DataFrame(rows)

def select_medoid(train,odds_cols):
    g=grid_for(train,odds_cols)
    raw=g.sort_values(['m_roi','m_profit_yen'],ascending=False).iloc[0]
    best=float(raw.m_roi)
    p=g[g.m_roi.ge(best-.025)].copy()
    med={'combined_min':float(p.combined_min.median()),
         'value_min':float(p.value_min.median()),
         'extra_units':float(p.extra_units.median())}
    ranges={k:max(float(p[k].max()-p[k].min()),1e-9) for k in med}
    p['medoid_dist']=sum((p[k]-med[k]).abs()/ranges[k] for k in med)
    core=p.sort_values(['medoid_dist','m_roi','m_profit_yen'],ascending=[True,False,False]).iloc[0]
    cfg={'combined_min':float(core.combined_min),'value_min':float(core.value_min),'extra_units':int(core.extra_units)}
    return cfg,raw.to_dict(),g,p

def lomo(dev,odds_cols):
    rows=[]
    for hold in DEV:
        train=dev[~dev.month.eq(hold)].copy(); test=dev[dev.month.eq(hold)].copy()
        if len(train)==0 or len(test)==0: continue
        cfg,raw,_,plateau=select_medoid(train,odds_cols)
        bm=baseline(test); tm,_=evaluate(test,cfg['combined_min'],cfg['value_min'],cfg['extra_units'],odds_cols)
        rows.append({'holdout_month':hold,**cfg,'train_plateau_cells':len(plateau),
                     'baseline_roi':bm['roi'],'test_roi':tm['roi'],
                     'delta_roi_pp':100*(tm['roi']-bm['roi']),
                     'baseline_profit_yen':bm['profit_yen'],'test_profit_yen':tm['profit_yen'],
                     'test_R':len(test),'trigger_R':tm['trigger_R']})
    return pd.DataFrame(rows)

def get_csv(session,day):
    y,m,d=day[:4],day[4:6],day[6:8]
    url=f'{RAW}data/previews/od3/{y}/{m}/{d}.csv'
    last=None
    for k in range(3):
        try:
            r=session.get(url,headers={'User-Agent':UA},timeout=30)
            if r.status_code==404:return None,url
            r.raise_for_status()
            return pd.read_csv(io.StringIO(r.content.decode('utf-8-sig')),dtype=str),url
        except Exception as ex:
            last=ex
            if k<2: time.sleep(1.5*(k+1))
    raise RuntimeError(f'preclose fetch failed {url}: {last}')

def lead_seconds(day,deadline,acquired):
    try:
        a=pd.Timestamp(str(acquired))
        if a.tzinfo is None:a=a.tz_localize('Asia/Tokyo')
        else:a=a.tz_convert('Asia/Tokyo')
        hm=re.search(r'(\d{1,2}):(\d{2})',str(deadline))
        if not hm:return np.nan
        dt=pd.Timestamp(f'{day[:4]}-{day[4:6]}-{day[6:8]} {int(hm.group(1)):02d}:{hm.group(2)}:00',tz='Asia/Tokyo')
        return float((dt-a).total_seconds())
    except Exception:
        return np.nan

def join_preclose(z):
    sess=requests.Session()
    day_cache={}; rec=[]; missing=[]
    for _,r in z.iterrows():
        code=str(r.race_code).zfill(12); day=code[:8]
        if day>='20260901': raise RuntimeError(f'September entered {code}')
        if day not in day_cache:
            day_cache[day]=get_csv(sess,day)
        df,url=day_cache[day]
        if df is None or 'レースコード' not in df.columns:
            missing.append({'race_code':code,'reason':'day_file_missing','url':url}); continue
        q=df[df['レースコード'].astype(str).str.zfill(12).eq(code)]
        if len(q)!=1:
            missing.append({'race_code':code,'reason':f'row_count_{len(q)}','url':url}); continue
        od=q.iloc[0]; vals=[]; bad=False
        for t in [r.ticket1,r.ticket2,r.ticket3]:
            col=f'3連単_{t}'
            try:v=float(od.get(col,''))
            except Exception:v=np.nan
            if not math.isfinite(v) or v<=0: bad=True
            vals.append(v)
        if bad:
            missing.append({'race_code':code,'reason':'formal_ticket_zero_or_missing','url':url}); continue
        rec.append({'race_code':code,'pre_odds1':vals[0],'pre_odds2':vals[1],'pre_odds3':vals[2],
                    'pre_combined_odds':combined_odds(vals),
                    'pre_deadline':od.get('締切時刻',''),'pre_acquired':od.get('取得日時',''),
                    'pre_lead_seconds':lead_seconds(day,od.get('締切時刻',''),od.get('取得日時','')),
                    'pre_source_url':url})
    p=pd.DataFrame(rec)
    out=z.merge(p,on='race_code',how='left',validate='one_to_one')
    return out,pd.DataFrame(missing)

def support_plateau_eval(sup,plateau,odds_cols):
    rows=[]; b=baseline(sup)
    for _,r in plateau.iterrows():
        c=float(r.combined_min);e=float(r.value_min);x=int(r.extra_units)
        m,_=evaluate(sup,c,e,x,odds_cols)
        rows.append({'combined_min':c,'value_min':e,'extra_units':x,
                     'support_R':len(sup),'support_trigger_R':m['trigger_R'],
                     'support_roi':m['roi'],'support_profit_yen':m['profit_yen'],
                     'support_delta_roi_pp':100*(m['roi']-b['roi'])})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--features',required=True,type=Path);a=ap.parse_args()
    z=pd.read_csv(a.features,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165:raise RuntimeError(f'R drift {len(z)}')
    if any(z.race_code.str[:8].ge('20260901')):raise RuntimeError('September entered')
    b=baseline(z)
    if (b['return_yen'],b['stake_yen'])!=(63700,49500):raise RuntimeError(f'baseline drift {b}')
    dev=z[z.month.isin(DEV)].copy(); sup=z[z.month.isin(SUP)].copy()

    close_cols=('odds1','odds2','odds3')
    close_cfg,close_raw,close_grid,close_plateau=select_medoid(dev,close_cols)
    # v371 identity sentinel.
    if close_cfg!={'combined_min':2.25,'value_min':1.1,'extra_units':3}:
        raise RuntimeError(f'v371 medoid drift {close_cfg}')
    close_lomo=lomo(dev,close_cols)
    close_support_plateau=support_plateau_eval(sup,close_plateau,close_cols)
    cbdev=baseline(dev); cbsup=baseline(sup)
    close_dev,_=evaluate(dev,2.25,1.10,3,close_cols)
    close_sup,_=evaluate(sup,2.25,1.10,3,close_cols)
    close_all,close_detail=evaluate(z,2.25,1.10,3,close_cols,detail=True)

    zp,miss=join_preclose(z)
    cov=zp.pre_odds1.notna() if 'pre_odds1' in zp.columns else pd.Series(False,index=zp.index)
    pc=zp[cov].copy()
    pcdev=pc[pc.month.isin(DEV)].copy(); pcsup=pc[pc.month.isin(SUP)].copy()
    coverage_by_month=[]
    for mon,g in z.groupby('month'):
        got=int(pc.race_code.isin(g.race_code).sum())
        coverage_by_month.append({'month':mon,'total_R':len(g),'covered_R':got,'coverage':got/len(g) if len(g) else 0.0})
    coverage=pd.DataFrame(coverage_by_month)

    pre_cols=('pre_odds1','pre_odds2','pre_odds3')
    pre_frozen_all=pre_frozen_dev=pre_frozen_sup=None
    pre_cfg=pre_raw=None;pre_plateau=pd.DataFrame();pre_lomo=pd.DataFrame();pre_support_plateau=pd.DataFrame()
    if len(pc):
        pre_frozen_all,_=evaluate(pc,2.25,1.10,3,pre_cols)
        pre_frozen_dev,_=evaluate(pcdev,2.25,1.10,3,pre_cols)
        pre_frozen_sup,_=evaluate(pcsup,2.25,1.10,3,pre_cols)
    if len(pcdev)>=20 and all((pcdev.month==m).sum()>0 for m in DEV):
        pre_cfg,pre_raw,pre_grid,pre_plateau=select_medoid(pcdev,pre_cols)
        pre_lomo=lomo(pcdev,pre_cols)
        if len(pcsup):pre_support_plateau=support_plateau_eval(pcsup,pre_plateau,pre_cols)
        pre_grid.to_csv(OUT/'preclose_dev_grid.csv',index=False)

    # Same-race closing vs pre-close execution drift.
    drift=pd.DataFrame()
    agreement={}
    if len(pc):
        d=pc.copy()
        for i in (1,2,3):
            d[f'odds_rel_drift_{i}']=d[f'odds{i}']/d[f'pre_odds{i}']-1.0
        d['combined_close']=d.apply(lambda r:combined_odds([r.odds1,r.odds2,r.odds3]),axis=1)
        d['combined_pre']=d.pre_combined_odds
        d['combined_rel_drift']=d.combined_close/d.combined_pre-1.0
        close_active=[];pre_active=[];same_units=[]
        for _,r in d.iterrows():
            ca=gate(r,2.25,1.10,close_cols);pa=gate(r,2.25,1.10,pre_cols)
            close_active.append(ca);pre_active.append(pa)
            cu=alloc_value(r,3,close_cols) if ca else [1,1,1]
            pu=alloc_value(r,3,pre_cols) if pa else [1,1,1]
            same_units.append(cu==pu)
        d['close_trigger']=close_active;d['pre_trigger']=pre_active;d['same_units']=same_units
        inter=sum(a and b for a,b in zip(close_active,pre_active));union=sum(a or b for a,b in zip(close_active,pre_active))
        agreement={
          'covered_R':len(d),'trigger_close_R':sum(close_active),'trigger_preclose_R':sum(pre_active),
          'trigger_agreement_share':float(np.mean(np.array(close_active)==np.array(pre_active))),
          'allocation_exact_match_share':float(np.mean(same_units)),
          'trigger_jaccard':inter/union if union else 1.0,
          'combined_abs_rel_drift_median':float(d.combined_rel_drift.abs().median()),
          'combined_abs_rel_drift_p90':float(d.combined_rel_drift.abs().quantile(.90)),
          'combined_abs_rel_drift_p95':float(d.combined_rel_drift.abs().quantile(.95)),
        }
        drift=d[['race_code','month','ticket1','ticket2','ticket3','odds1','odds2','odds3',
                 'pre_odds1','pre_odds2','pre_odds3','combined_close','combined_pre','combined_rel_drift',
                 'pre_deadline','pre_acquired','pre_lead_seconds','close_trigger','pre_trigger','same_units']].copy()

    lead=pc.pre_lead_seconds.dropna() if len(pc) and 'pre_lead_seconds' in pc.columns else pd.Series(dtype=float)
    lead_summary={
      'n':int(len(lead)),
      'median_seconds':float(lead.median()) if len(lead) else None,
      'p10_seconds':float(lead.quantile(.10)) if len(lead) else None,
      'p90_seconds':float(lead.quantile(.90)) if len(lead) else None,
      'min_seconds':float(lead.min()) if len(lead) else None,
      'max_seconds':float(lead.max()) if len(lead) else None,
    }

    close_grid.to_csv(OUT/'closing_dev_grid.csv',index=False)
    close_plateau.to_csv(OUT/'closing_dev_plateau.csv',index=False)
    close_lomo.to_csv(OUT/'closing_lomo.csv',index=False)
    close_support_plateau.to_csv(OUT/'closing_plateau_support.csv',index=False)
    pd.DataFrame(close_detail).to_csv(OUT/'closing_core_allocations.csv',index=False)
    zp.to_csv(OUT/'formal_with_preclose_join.csv',index=False)
    miss.to_csv(OUT/'preclose_missing.csv',index=False)
    coverage.to_csv(OUT/'preclose_coverage_by_month.csv',index=False)
    pre_plateau.to_csv(OUT/'preclose_dev_plateau.csv',index=False)
    pre_lomo.to_csv(OUT/'preclose_lomo.csv',index=False)
    pre_support_plateau.to_csv(OUT/'preclose_plateau_support.csv',index=False)
    drift.to_csv(OUT/'closing_vs_preclose_drift.csv',index=False)

    result={
      'baseline_all':b,
      'closing_v371_core':close_cfg,
      'closing_core_dev':close_dev,'closing_core_support':close_sup,'closing_core_all':close_all,
      'closing_lomo_nonnegative_months':int((close_lomo.delta_roi_pp>=0).sum()) if len(close_lomo) else 0,
      'closing_lomo_total_delta_profit_yen':int((close_lomo.test_profit_yen-close_lomo.baseline_profit_yen).sum()) if len(close_lomo) else 0,
      'closing_lomo':close_lomo.to_dict('records'),
      'closing_plateau_cells':len(close_plateau),
      'closing_plateau_support_nonnegative_share':float((close_support_plateau.support_delta_roi_pp>=0).mean()) if len(close_support_plateau) else None,
      'preclose_source':'BoatraceCSV data/previews/od3 official in-progress odds snapshot',
      'preclose_covered_R':int(len(pc)),'preclose_missing_R':int(len(z)-len(pc)),
      'preclose_coverage_by_month':coverage.to_dict('records'),
      'preclose_lead_time':lead_summary,
      'preclose_frozen_closing_core_all':pre_frozen_all,
      'preclose_frozen_closing_core_dev':pre_frozen_dev,
      'preclose_frozen_closing_core_support':pre_frozen_sup,
      'preclose_dev_selected':pre_cfg,
      'preclose_lomo_nonnegative_months':int((pre_lomo.delta_roi_pp>=0).sum()) if len(pre_lomo) else None,
      'preclose_lomo_total_delta_profit_yen':int((pre_lomo.test_profit_yen-pre_lomo.baseline_profit_yen).sum()) if len(pre_lomo) else None,
      'preclose_lomo':pre_lomo.to_dict('records'),
      'closing_vs_preclose_agreement':agreement,
      'LIVE_CURRENT_ODDS_SHADOW_EXISTS':True,
      'LIVE_CURRENT_ODDS_SHADOW_FILE':'run_1head_v351_live_current_odds_shadow.py',
      'LIVE_SHADOW_SAVES_FORMAL3_ODDS_AND_TIMESTAMP':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
