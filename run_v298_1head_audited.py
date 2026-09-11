#!/usr/bin/env python3
"""Run v298 with an explicit exact-result coverage audit.

This does not change v298 model logic. It replaces only the settlement guard so that
missing/invalid exact-result rows are exported for inspection. All valid settled
races remain in evaluation, including boat-1 losses. Jul/Aug/Sep hygiene remains
controlled by the underlying v298/v294 data path.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
from backtest import rows
from backtest_v51_lane_corrected_tickets import ii

ROOT=Path(__file__).resolve().parent
AUDIT=ROOT/'analysis_v298_1head_threat_listwise_trifecta5_settlement_missing.csv'
MIN_COVERAGE=0.980


def settle_audited(d):
    days=sorted({date.fromisoformat(str(x)) for x in d.date})
    fetched={}
    def one(day):
        rs=rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv")
        return day,{v298.v297.norm_code(r.get('レースコード','')):r for r in rs if v298.v297.norm_code(r.get('レースコード',''))}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,day) for day in days]
        for j,f in enumerate(as_completed(fs),1):
            day,z=f.result();fetched[day]=z
            if j%40==0:print('audited exact-result fetch',j,'/',len(days),flush=True)
    winners=[];combos=[];valid=[];missing=[]
    for _,r in d.iterrows():
        day=date.fromisoformat(str(r.date));code=v298.v297.norm_code(r.race_code)
        rr=fetched.get(day,{}).get(code,{})
        a=ii(rr.get('1着_艇番'),0);b=ii(rr.get('2着_艇番'),0);c=ii(rr.get('3着_艇番'),0)
        ok=(a in range(1,7) and b in range(1,7) and c in range(1,7) and len({a,b,c})==3)
        winners.append(a if ok else 0);combos.append(f'{a}-{b}-{c}' if ok else '');valid.append(int(ok))
        if not ok:
            missing.append({'date':str(r.date),'month':int(r.month),'race_code':str(r.race_code).zfill(12),'venue':r.get('venue',''),'race':r.get('race',''),'raw_1':a,'raw_2':b,'raw_3':c,'result_row_found':int(bool(rr))})
    z=d.copy();z['winner']=winners;z['valid_result']=valid;z['combo_valid']=valid;z['actual_combo']=combos
    z['head_hit']=(z.winner==1).astype(int)
    cov=float(z.combo_valid.mean()) if len(z) else 0.0
    pd.DataFrame(missing).to_csv(AUDIT,index=False,encoding='utf-8-sig')
    print(f'audited settlement rows={len(z)} valid={sum(valid)} missing={len(missing)} coverage={cov:.6f}',flush=True)
    if cov<MIN_COVERAGE:
        raise RuntimeError(f'audited exact-order settlement coverage too low {cov:.4f} < {MIN_COVERAGE:.4f}')
    return z,cov


if __name__=='__main__':
    v298.v297.settle_full_after_freeze=settle_audited
    v298.main()
