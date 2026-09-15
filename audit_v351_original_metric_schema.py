#!/usr/bin/env python3
from collections import Counter, defaultdict
import pandas as pd
import run_v326_1head_ticketaware_exhibition as v326
from backtest import rows
from backtest_v51_lane_corrected_tickets import norm_metric


def main():
    base=pd.read_csv(v326.V320,dtype={'race_code':str})
    base['race_code']=base.race_code.astype(str).str.zfill(12)
    records=[]
    for day,g in base.groupby(base.race_code.str[:8]):
        ymd=f'{day[:4]}/{day[4:6]}/{day[6:8]}'
        orig={str(r.get('レースコード','')).zfill(12):r for r in rows(f'data/previews/original_exhibition/{ymd}.csv') if r.get('レースコード')}
        for code in g.race_code:
            r=orig.get(code,{})
            rec={'race_code':code,'jcd':int(code[8:10]),'has_orig':int(bool(r))}
            normalized=[]
            for k in range(1,5):
                raw=(r.get(f'計測項目{k}','') or '').strip()
                norm=norm_metric(raw) if raw else ''
                vals=[]
                for b in range(1,7):
                    try: vals.append(float(r.get(f'艇{b}_値{k}')))
                    except: vals.append(None)
                all6=int(bool(raw) and all(v is not None for v in vals))
                rec[f'raw{k}']=raw;rec[f'norm{k}']=norm;rec[f'all6_{k}']=all6
                if raw: normalized.append(norm)
            rec['schema']='|'.join(normalized)
            records.append(rec)
    df=pd.DataFrame(records)
    df.to_csv('analysis_v351_original_metric_raw.csv',index=False,encoding='utf-8-sig')
    schema=(df.groupby(['jcd','schema'],dropna=False).size().reset_index(name='R').sort_values(['jcd','R'],ascending=[True,False]))
    schema.to_csv('analysis_v351_original_metric_schema.csv',index=False,encoding='utf-8-sig')
    print('R',len(df),'HAS_ORIG',int(df.has_orig.sum()))
    for jcd,g in df.groupby('jcd'):
        raws=Counter(); norms=Counter(); schemas=Counter(g.schema)
        for k in range(1,5):
            raws.update(x for x in g[f'raw{k}'] if x)
            norms.update(x for x in g[f'norm{k}'] if x)
        print(f'JCD {jcd:02d} R={len(g)} has_orig={int(g.has_orig.sum())}')
        print(' RAW',dict(raws))
        print(' NORM',dict(norms))
        print(' SCHEMA',dict(schemas))

if __name__=='__main__': main()
