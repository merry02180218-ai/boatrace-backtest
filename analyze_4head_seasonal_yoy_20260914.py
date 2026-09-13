#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from backtest import rows
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250

ROOT=Path(__file__).resolve().parent
FEATURES=['inner12_resistance','wall3_weak','racer4','past_win4','hist_st_edge_4v3']
YEARS=[2025,2026]
MONTHS=[5,6,7,8]
SUMMARY=ROOT/'summary_4head_seasonal_yoy_20260914.md'
MONTHLY=ROOT/'analysis_4head_seasonal_yoy_monthly_20260914.csv'
JUMPS=ROOT/'analysis_4head_seasonal_yoy_jumps_20260914.csv'
COVERAGE=ROOT/'analysis_4head_seasonal_yoy_coverage_20260914.csv'
AUDIT=ROOT/'audit_4head_seasonal_yoy_20260914.json'


def smd(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    a=a[np.isfinite(a)]; b=b[np.isfinite(b)]
    if len(a)==0 or len(b)==0: return None
    den=math.sqrt((np.var(a)+np.var(b))/2)
    return float((np.mean(b)-np.mean(a))/den) if den>0 else 0.0


def build_year(year):
    start=date(year,5,1); end=date(year,8,31); preload=start-timedelta(days=120)
    cache={}; hist=defaultdict(list); seen=set(); d=preload
    # Causal warm-up only; no target outcomes are read anywhere in this script.
    while d<start:
        ingest_motor(hist,seen,d)
        if d>=start-timedelta(days=14): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    rec=[]; cov=[]
    while d<=end:
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        generated=[]
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            z={'date':str(d),'year':year,'month':d.month,'race_code':str(r.get('レースコード','')).zfill(12)}
            z.update(v250.pre_features(x,s4)); generated.append(z)
        rec.extend(generated)
        cov.append({'date':str(d),'year':year,'month':d.month,'card_rows':len(cards),'feature_rows':len(generated),'motor_hist_keys':len(hist),'preview_cache_keys':len(cache)})
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    return pd.DataFrame(rec), pd.DataFrame(cov)


def main():
    frames=[]; coverage=[]
    for y in YEARS:
        df,cov=build_year(y); frames.append(df); coverage.append(cov)
    df=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    cv=pd.concat(coverage,ignore_index=True) if coverage else pd.DataFrame()
    cv.to_csv(COVERAGE,index=False)

    monthly=[]
    for (y,m),g in df.groupby(['year','month']):
        for f in FEATURES:
            s=pd.to_numeric(g[f],errors='coerce') if f in g else pd.Series(dtype=float)
            finite=s[np.isfinite(s)]
            monthly.append({
                'year':int(y),'month':int(m),'feature':f,'R':len(g),'finite_n':len(finite),
                'missing_share':float(1-len(finite)/len(g)) if len(g) else None,
                'zero_share':float((finite==0).mean()) if len(finite) else None,
                'mean':float(finite.mean()) if len(finite) else None,
                'median':float(finite.median()) if len(finite) else None,
                'std':float(finite.std(ddof=0)) if len(finite) else None,
                'p10':float(finite.quantile(.10)) if len(finite) else None,
                'p25':float(finite.quantile(.25)) if len(finite) else None,
                'p75':float(finite.quantile(.75)) if len(finite) else None,
                'p90':float(finite.quantile(.90)) if len(finite) else None,
            })
    md=pd.DataFrame(monthly); md.to_csv(MONTHLY,index=False)

    jumps=[]
    for y in YEARS:
        for a,b,label in [(6,7,'Jun->Jul'),(7,8,'Jul->Aug')]:
            ga=df[(df.year==y)&(df.month==a)]; gb=df[(df.year==y)&(df.month==b)]
            for f in FEATURES:
                xa=pd.to_numeric(ga[f],errors='coerce').dropna(); xb=pd.to_numeric(gb[f],errors='coerce').dropna()
                xa=xa[np.isfinite(xa)]; xb=xb[np.isfinite(xb)]
                ks=ks_2samp(xa,xb) if len(xa) and len(xb) else None
                jumps.append({'year':y,'jump':label,'feature':f,'n_from':len(xa),'n_to':len(xb),'mean_from':float(xa.mean()) if len(xa) else None,'mean_to':float(xb.mean()) if len(xb) else None,'smd':smd(xa,xb),'ks':float(ks.statistic) if ks else None,'ks_p':float(ks.pvalue) if ks else None})
    jd=pd.DataFrame(jumps); jd.to_csv(JUMPS,index=False)

    # Coverage summaries by month to distinguish recurring seasonality from source/pipeline loss.
    covm=cv.groupby(['year','month']).agg(days=('date','count'),days_with_cards=('card_rows',lambda x:int((x>0).sum())),days_with_features=('feature_rows',lambda x:int((x>0).sum())),card_rows=('card_rows','sum'),feature_rows=('feature_rows','sum'),motor_hist_keys_end=('motor_hist_keys','max'),preview_cache_keys_end=('preview_cache_keys','max')).reset_index()

    def fmt(v):
        return 'NA' if pd.isna(v) else f'{v:.3f}'

    L=['# HEAD4 seasonal year-over-year feature audit','',
       '- Outcome-blind: target race results/wins are never loaded.',
       '- Production unchanged; July/August 2026 remain NON-PRISTINE.',
       '- Verified public source coverage exposes 2025 and 2026 realtime eras; 2024 is not fabricated.',
       '', '## Source / feature coverage', '', covm.to_markdown(index=False), '',
       '## June -> July feature jumps', '', '|year|feature|SMD|KS|mean Jun|mean Jul|','|---:|---|---:|---:|---:|---:|']
    for _,r in jd[jd.jump=='Jun->Jul'].iterrows():
        L.append(f"|{int(r.year)}|{r.feature}|{fmt(r.smd)}|{fmt(r.ks)}|{fmt(r.mean_from)}|{fmt(r.mean_to)}|")
    L+=['','## July -> August feature jumps','', '|year|feature|SMD|KS|mean Jul|mean Aug|','|---:|---|---:|---:|---:|---:|']
    for _,r in jd[jd.jump=='Jul->Aug'].iterrows():
        L.append(f"|{int(r.year)}|{r.feature}|{fmt(r.smd)}|{fmt(r.ks)}|{fmt(r.mean_from)}|{fmt(r.mean_to)}|")
    L+=['','## Monthly feature summaries','','See `analysis_4head_seasonal_yoy_monthly_20260914.csv` for row counts, missing/zero shares, means, medians, standard deviations, and quantiles.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')

    audit={
      'status':'COMPLETE','years':YEARS,'months':MONTHS,'features':FEATURES,
      'target_outcomes_loaded':False,'outcome_blind':True,'production_modified':False,
      'jul_aug_2026_non_pristine':True,'source_2024_claimed':False,
      'coverage_monthly':covm.to_dict('records'),
      'jun_jul':jd[jd.jump=='Jun->Jul'].to_dict('records'),
      'jul_aug':jd[jd.jump=='Jul->Aug'].to_dict('records')
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(SUMMARY.read_text(encoding='utf-8'))

if __name__=='__main__': main()
