#!/usr/bin/env python3
# 2026-09-11 PRE live bridge: direct current Boatcast inputs, result-blind.
from __future__ import annotations
from collections import defaultdict
from datetime import date
from pathlib import Path
import csv
import numpy as np, pandas as pd

import analyze_v108_1head_feasibility as v108
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v249_3head_pre_rolling_sab_optimize as v249
from backtest import rows

DAY=date(2026,9,11)
FIRST=pd.Timestamp('2026-09-01'); NEXT=pd.Timestamp('2026-10-01')
OUT='scan_20260911_3head_v288_pre.csv'; SUM='scan_20260911_3head_v288_pre.md'
CUR_CARDS=Path('current_input/race_cards.csv'); CUR_WAKU=Path('current_input/waku10.csv')
COV=Path('analysis_v234_waku10_reconstruction_coverage.csv')

def local_csv(p):
    if not p.exists(): return []
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def bycode(rs):
    return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def learn_bias(end=date(2026,9,10),start=date(2026,8,1)):
    sums=defaultdict(list); allv=[]; d=start
    while d<=end:
        for r in rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'):
            for b in range(1,7):
                try:v=float(r.get(f'艇{b}_スタート展示'))
                except Exception:continue
                if -.30<v<1.0:sums[b].append(v);allv.append(v)
        d=(pd.Timestamp(d)+pd.Timedelta(days=1)).date()
    g=float(np.mean(allv)) if allv else .15
    return {b:(float(np.mean(sums[b]))-g if sums[b] else 0.) for b in range(1,7)}
def make_current_base():
    cards=bycode(local_csv(CUR_CARDS)); waku=bycode(local_csv(CUR_WAKU)); bias=learn_bias(); out=[]
    for code,card in cards.items():
        if code not in waku: continue
        z=v108.feature_row('2026-09-11',card,waku[code],{}, {}, {}, bias)
        if z is None: continue
        z.update({'winner':0,'valid_result':0,'actual_combo':'','valid_payout':0,'payout100':0})
        for b in range(1,7):
            for key in (f'艇{b}_選手名',f'艇{b}_選手登番'):
                if key in card: z[key]=card.get(key)
        out.append(z)
    if not out: raise RuntimeError(f'no current PRE rows built cards={len(cards)} waku={len(waku)}')
    return pd.DataFrame(out)
def build_augmented():
    cov=pd.read_csv(COV,dtype={'date':str,'source':str})
    if (cov.source=='missing').any(): raise RuntimeError('frozen historical restored Waku10 has missing days')
    raw=pd.read_csv(v224.SRC,dtype={'race_code':str}); cur=make_current_base(); raw=pd.concat([raw,cur],ignore_index=True,sort=False)
    dc=v165.pc(raw,['date','race_date','ymd']); vc=v165.pc(raw,['venue','jcd','stadium','place']); y,_=v165.target(raw); basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y; raw=raw[raw._date.notna() & (raw._date<NEXT)].copy()
    v221.CONTAM=NEXT; v221.END=DAY; old221=v221.day_fetch
    lc=local_csv(CUR_CARDS); lw=local_csv(CUR_WAKU)
    def safe221(d):
        if d==DAY:return d,{'cards':lc,'tkz':[],'orig':[],'res':[]}
        return old221(d)
    v221.day_fetch=safe221
    v222.CONTAM=NEXT; v222.END=DAY; old222=v222.day_fetch
    def safe222(d):
        if d==DAY:return d,{'cards':lc,'waku':lw,'tkz':[],'stt':[],'orig':[]}
        dd,z=old222(d); z=dict(z)
        if d<=date(2026,8,31):
            rr=v234.local_rows(d)
            if rr:z['waku']=rr
        return dd,z
    v222.day_fetch=safe222
    v223.CONTAM=NEXT; v224.CONTAM=NEXT
    d=v221.build(raw,dc); d=v222.build_current(d,dc); d=v223.build_unused(d,dc); d=v224.add_decomp(d,dc)
    fs=[x for x in v234.full_features(d,basefs) if x in d.columns]
    return d,vc,basefs,fs
def main():
    d,vc,basefs,fs=build_augmented()
    base_te,_=v223.fit_head(d,list(basefs),vc,FIRST,NEXT)
    k=max(1,int((base_te._p>=.30).sum()))
    te,_=v223.fit_head(d,fs,vc,FIRST,NEXT); te=te[te._date==pd.Timestamp(DAY)].copy(); sel=te.nlargest(min(k,len(te)),'_p').copy()
    if sel.empty: raise RuntimeError('no v243 head candidates')
    hist=pd.read_csv('analysis_v243_3head_expand_feature_audit.csv',dtype={'race_code':str}); hist.date=hist.date.astype(str); hist['_target']=v249.target(hist).astype(int); cs=v249.cols(hist)
    cur=pd.DataFrame(index=sel.index)
    for c in cs:
        rawc=c[3:] if c.startswith('f__') else c; cur[c]=pd.to_numeric(sel.get(rawc,np.nan),errors='coerce')
    cur['_score']=v249.fit_score(hist,cur,cs); cur['_pct']=cur['_score'].rank(pct=True,method='first',ascending=True); cur['grade']=np.where(cur._pct>=.70,'S',np.where(cur._pct>=.20,'A','B'))
    rec=[]
    for idx,r in sel.iterrows():
        c=cur.loc[idx]
        if c.grade not in ('S','A'): continue
        code=str(r.race_code).zfill(12); rec.append(dict(race_code=code,jcd=int(code[8:10]),rno=int(code[10:12]),pre_grade=c.grade,pre_score=float(c._score),pre_pct=float(c._pct),p3=float(r._p),b3_minus_b2_motor=float(r.get('c_b3_minus_b2_motor',np.nan)),b3_inside_nst=float(r.get('c_b3_inside_nst',np.nan))))
    q=pd.DataFrame(rec).sort_values(['pre_grade','pre_pct'],ascending=[False,False]) if rec else pd.DataFrame(columns=['race_code']); q.to_csv(OUT,index=False)
    L=['# 2026-09-11 3-head v288 PRE scan','', '- Result-blind: target-day result/payout endpoints are not used.','- PRE-only: target-day exhibition/ST/original-exhibition feeds are intentionally not supplied.','- Current race cards + Waku10 are scraped directly from Boatcast because public BoatraceCSV main was only published through 2026-09-10 at scan time.','- Operational bridge: historical v249 uses month-internal percentile; today ranks within the target-day v243 candidate universe.','',f'- v243 current head universe: {len(sel)}',f'- PRE S+A candidates: {len(q)}','', '|race|grade|pct|p3|b3-b2 motor|b3 inside NST|','|---|---|---:|---:|---:|---:|']
    for _,x in q.iterrows():L.append(f"|JCD{x.jcd:02.0f} {x.rno:.0f}R|{x.pre_grade}|{x.pre_pct:.3f}|{x.p3:.3f}|{x.b3_minus_b2_motor:.3f}|{x.b3_inside_nst:.3f}|")
    open(SUM,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__': main()
