#!/usr/bin/env python3
from datetime import date,timedelta
from collections import defaultdict
import csv
from backtest import rows
from backtest_v51_lane_corrected_tickets import ff,norm_metric

def bycode(rs): return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def all6(row,prefix): return bool(row) and all(ff(row.get(f'艇{b}_{prefix}')) is not None for b in range(1,7))
def orig_all6(row,target):
    if not row:return False
    for k in range(1,5):
        if norm_metric(row.get(f'計測項目{k}',''))!=target:continue
        if all(ff(row.get(f'艇{b}_値{k}')) is not None for b in range(1,7)):return True
    return False
def orig_avg(row):
    if not row:return False
    used=0
    for k in range(1,5):
        lab=norm_metric(row.get(f'計測項目{k}',''))
        if not lab:continue
        vals=[ff(row.get(f'艇{b}_値{k}')) for b in range(1,7)]
        if not any(v is not None for v in vals):continue
        used+=1
        if not all(v is not None for v in vals):return False
    return used>0

def main():
    agg=defaultdict(lambda:defaultdict(int)); out=[]
    d=date(2026,2,1); end=date(2026,3,31)
    while d<=end:
        ymd=d.strftime('%Y/%m/%d')
        tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv')); stt=bycode(rows(f'data/previews/stt/{ymd}.csv')); org=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
        codes=sorted(set(tkz)|set(stt)|set(org))
        for c in codes:
            jcd=c[8:10]; a=agg[(d.strftime('%Y-%m'),jcd)]; a['R']+=1
            tr=tkz.get(c,{}); sr=stt.get(c,{}); oo=org.get(c,{})
            flags={'tkz_all6':all6(tr,'展示タイム'),'stt_all6':all6(sr,'スタート展示'),'turn_all6':orig_all6(oo,'回り足') or orig_all6(oo,'まわり足'),'straight_all6':orig_all6(oo,'直線'),'lap_all6':orig_all6(oo,'一周'),'orig_avg_all6':orig_avg(oo)}
            flags['common_ready']=flags['tkz_all6'] and flags['stt_all6']
            for k,v in flags.items():a[k]+=int(v)
        d+=timedelta(days=1)
    fields=['month','jcd','R','tkz_all6','stt_all6','common_ready','turn_all6','straight_all6','lap_all6','orig_avg_all6']
    for (m,j),a in sorted(agg.items()):
        z={'month':m,'jcd':j,**{k:a[k] for k in fields[2:]}}
        for k in fields[3:]:z[k+'_pct']=round(100*z[k]/z['R'],2) if z['R'] else 0
        out.append(z)
    fs=list(out[0].keys()) if out else fields
    with open('research_v289_3head_exhibition_availability_v5.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    print('rows',len(out))
    for z in out:print(z)
if __name__=='__main__':main()
