from __future__ import annotations
import csv, io, json, re, urllib.request
import pandas as pd

SRC='analysis_v289_3head_wave21_allrace_feature_settled.csv'
BASE='https://boatracecsv.github.io/data'

def fetch(kind,date):
    u=f'{BASE}/{kind}/{date:%Y/%m/%d}.csv'
    try:
        with urllib.request.urlopen(u,timeout=20) as r:
            return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
    except Exception:
        return []

def main():
    # Read date column only: do not load any September result/payout columns.
    dates=pd.read_csv(SRC,usecols=['date'])
    d=pd.to_datetime(dates['date'],errors='coerce').dropna()
    safe=d[d < pd.Timestamp('2026-09-01')]
    monthly=safe.dt.to_period('M').astype(str).value_counts().sort_index().to_dict()

    jan_days={}
    for day in pd.date_range('2026-01-01','2026-01-31'):
        counts={}
        for k in ['programs/race_cards','programs/recent_national','programs/recent_local']:
            counts[k]=len(fetch(k,day.date()))
        jan_days[str(day.date())]=counts

    schema={}
    samples={}
    for day in [pd.Timestamp('2026-01-15'),pd.Timestamp('2026-02-01')]:
        for kind in ['programs/recent_national','programs/recent_local']:
            rows=fetch(kind,day.date())
            key=f'{kind}@{day.date()}'
            if not rows:
                schema[key]=[]
                samples[key]={}
                continue
            keys=list(rows[0].keys())
            dateish=[k for k in keys if re.search(r'(日|月|年|開始|終了|開催|節)',k)]
            schema[key]=dateish
            row=rows[0]
            interesting=[k for k in dateish if ('前1節' in k or '前2節' in k or '日' in k or '終了' in k)]
            samples[key]={k:row.get(k) for k in interesting[:80]}

    out={
        'policy':{
            'september_outcome_columns_loaded':False,
            'source_date_audit_only':True,
            'production_v288_changed':False
        },
        'source_date_min_pre_sep':str(safe.min().date()) if len(safe) else None,
        'source_date_max_pre_sep':str(safe.max().date()) if len(safe) else None,
        'source_monthly_rows_pre_sep':monthly,
        'january_funsite_complete_days':sum(
            1 for v in jan_days.values()
            if all(v.get(k,0)>0 for k in ['programs/race_cards','programs/recent_national','programs/recent_local'])
        ),
        'january_funsite_day_counts':jan_days,
        'recent_schema_dateish_keys':schema,
        'recent_schema_samples':samples,
    }
    with open('research_3head_source_horizon_audit.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
