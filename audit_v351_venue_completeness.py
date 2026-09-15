#!/usr/bin/env python3
import pandas as pd
import run_v326_1head_ticketaware_exhibition as v326

VENUES={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}

def main():
    y=v326.build_dataset().copy()
    y['jcd']=y.race_code.astype(str).str.zfill(12).str[8:10].astype(int)
    y['venue']=y.jcd.map(VENUES)
    cols=['tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6','source_complete','model_ready']
    for c in cols:y[c]=pd.to_numeric(y[c],errors='coerce').fillna(0).astype(int)
    rows=[]
    for (jcd,venue),g in y.groupby(['jcd','venue'],sort=True):
        r={'jcd':jcd,'venue':venue,'R':len(g),'head_H':int(g.head_hit.sum()),'head_rate':100*g.head_hit.mean()}
        for c in cols:r[c]=int(g[c].sum())
        r['straight_missing_R']=int((g.orig_straight_all6==0).sum())
        r['strict_excluded_R']=int((g.source_complete==0).sum())
        ready=g[g.model_ready==1]
        r['model_ready_head_H']=int(ready.head_hit.sum())
        r['model_ready_head_rate']=100*ready.head_hit.mean() if len(ready) else float('nan')
        rows.append(r)
    out=pd.DataFrame(rows)
    out.to_csv('analysis_v351_venue_completeness.csv',index=False)
    print(out.to_string(index=False))
    print('TOTAL',len(y),'SOURCE_COMPLETE',int(y.source_complete.sum()),'MODEL_READY',int(y.model_ready.sum()))
if __name__=='__main__':main()
