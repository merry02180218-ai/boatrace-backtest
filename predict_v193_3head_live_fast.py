#!/usr/bin/env python3
from __future__ import annotations
import json,joblib,time
from datetime import date
from pathlib import Path
import numpy as np,pandas as pd
from backtest import rows
from analyze_v108_1head_feasibility import feature_row,bycode
from analyze_v166_3head_pair_direct import order as pair_order
from predict_v192_3head_live_manual import build_manual_maps

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'live_input_3head.json'
CACHE=ROOT/'cache_v193_3head_live.joblib'
META=ROOT/'cache_v193_3head_live_meta.json'
OUT=ROOT/'prediction_v193_3head_live_fast.json'
SUMMARY=ROOT/'summary_v193_3head_live_fast.md'
CUT=.30

def main():
    t0=time.time()
    j=json.loads(INPUT.read_text(encoding='utf-8')); hd=date.fromisoformat(j['date'])
    c=joblib.load(CACHE); meta=json.loads(META.read_text(encoding='utf-8'))
    if c.get('date')!=hd.isoformat(): raise RuntimeError(f'cache date {c.get("date")} != input {hd}')
    venue=str(j['venue']).zfill(2); rno=int(j['race']); code=f"{hd:%Y%m%d}{venue}{rno:02d}"; y=hd.strftime('%Y/%m/%d')
    cards=bycode(rows(f'data/programs/race_cards/{y}.csv')); waku=bycode(rows(f'data/programs/waku10/{y}.csv'))
    if code not in cards or code not in waku: raise RuntimeError(f'card/waku not available for {code}')
    tk,stt,orig=build_manual_maps(code,j)
    row=feature_row(hd.isoformat(),cards[code],waku[code],tk,stt,orig,c['st_bias'])
    if row is None: raise RuntimeError('entry changed/excluded')
    cols=c['head_nums']+c['head_cats']; x=pd.DataFrame([{k:row.get(k,np.nan) for k in cols}])
    p=float(c['head_model'].predict_proba(x)[0,1])
    top10=pair_order(row,c['pair_model'],1.0)[:10] if p>=CUT else []
    elapsed=time.time()-t0
    res={'date':hd.isoformat(),'venue':venue,'race':rno,'race_code':code,'boat3':cards[code].get('艇3_選手名',''),'p3head':p,'cut':CUT,'decision':'BUY' if p>=CUT else 'SKIP','v166_lambda':1.0,'top10':top10,'elapsed_sec':elapsed,'cache_meta':meta,'manual_input':j}
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    L=[f"# v193 FAST live 3-head {hd} {venue} {rno}R",'',f"- boat3: **{res['boat3']}**",f"- v165 p3head: **{100*p:.2f}%**",f"- decision: **{res['decision']}** (cut 30%)",f"- elapsed: **{elapsed:.2f}s**",'', '## Top10']
    L += [f"{i}. {z}" for i,z in enumerate(top10,1)] if top10 else ['- SKIP: no tickets']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
