#!/usr/bin/env python3
"""v252 research: separate PRE candidate gate from POST final gate for rebuilt 4-head model.

Uses v251's already-frozen monthly prior-only pair order + archived-odds settlement bridge.
Grid is descriptive/model-selection only.  Jul/Aug remain NON-PRISTINE.
No production rule is adopted by this script.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_v252_4head_pre_post_gate_search.csv'
SUM=ROOT/'summary_v252_4head_pre_post_gate_search.md'
BANK=10000
PRE_CUTS=(.15,.18,.20,.22,.25,.28,.30,.32,.35,.38,.40)
POST_CUTS=(.15,.18,.20,.22,.25,.28,.30,.32,.35,.38,.40,.45)
NS=tuple(range(2,21))

def main():
    p=pd.read_csv(PRED,dtype={'race_code':str});p['race_code']=p.race_code.str.zfill(12)
    # Pivot PRE/POST probabilities onto one frozen race row.
    w=p.pivot_table(index=['date','month','race_code'],columns='variant',values='p4head',aggfunc='last').reset_index()
    if 'PRE' not in w or 'POST' not in w: raise RuntimeError('PRE/POST predictions missing')
    rs=c4.read();orders=v251.pair_orders(rs);am=v251.actual_map(rs)
    od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()
    rows=[]
    for _,r in w.iterrows():
        code=str(r.race_code).zfill(12);k=(str(r.date),code);order=orders.get(k);a=am.get(k)
        if not order or not a or a[3]!=1 or code not in oi.index: continue
        o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        for n in NS:
            ts=[f'4-{x}-{y}' for x,y in order[:n]]
            s=v251.settle(code,ts,o,a)
            if s is None: continue
            hit,ret,comp=s
            rows.append({'date':r.date,'month':r.month,'race_code':code,'pre':float(r.PRE),'post':float(r.POST),'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,'head4':int(a[0]==4)})
    z=pd.DataFrame(rows)
    if z.empty: raise RuntimeError('no settled rows')
    out=[]
    for pc in PRE_CUTS:
      for qc in POST_CUTS:
       for n in NS:
        q=z[(z.n==n)&(z.pre>=pc)&(z.post>=qc)]
        if q.empty: continue
        cost=len(q)*BANK;ret=q.return_yen.sum()
        # Ex-Jul/Aug descriptive robustness view, not pristine validation.
        q6=q[q.month<='2026-06'];c6=len(q6)*BANK;r6=q6.return_yen.sum()
        out.append({'pre_cut':pc,'post_cut':qc,'n':n,'R':len(q),'head4_rate_pct':100*q.head4.mean(),'trifecta_hits':int(q.hit.sum()),'trifecta_hit_rate_pct':100*q.hit.mean(),'avg_comp_odds':q.comp_odds.mean(),'cost_yen':cost,'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost,'R_feb_jun':len(q6),'roi_feb_jun_pct':100*r6/c6 if c6 else np.nan,'hit_feb_jun_pct':100*q6.hit.mean() if len(q6) else np.nan})
    d=pd.DataFrame(out);d.to_csv(OUT,index=False)
    L=['# v252 4-head PRE candidate + POST final gate search','',
       '- PREとPOSTを分離し、PRE候補通過後にPOST最終gateを掛ける。','- 相手順位・settlementはv251と同じ月別prior-only pair model / 1R10,000円Hamilton Dutch。','- 当該レースの結果はgate/rank作成に使用しない。 archived oddsはticket freeze後のsettlement用。','- 全結果はmodel-selection evidence。特にJul/AugはNON-PRISTINE。','- このgridの最高ROIをそのままproduction採用しない。','',
       '## Best cells, R>=80 (all Feb-Aug)','|PRE|POST|N|R|4-head|3連単 hit|avg comp|profit|ROI|Feb-Jun R|Feb-Jun ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in d[d.R>=80].sort_values(['roi_pct','R'],ascending=[False,False]).head(25).iterrows():
        L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.n)}|{int(r.R)}|{r.head4_rate_pct:.2f}%|{r.trifecta_hit_rate_pct:.2f}%|{r.avg_comp_odds:.3f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.roi_feb_jun_pct:.2f}%|')
    L += ['','## Robustness shortlist','- 条件: R>=80、Feb-Jun R>=50、全期間ROI>=100%、Feb-Jun ROI>=100%。','|PRE|POST|N|R|hit|ROI|Feb-Jun R|Feb-Jun hit|Feb-Jun ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    robust=d[(d.R>=80)&(d.R_feb_jun>=50)&(d.roi_pct>=100)&(d.roi_feb_jun_pct>=100)].sort_values(['roi_feb_jun_pct','roi_pct'],ascending=False).head(25)
    if robust.empty:L.append('|—|—|—|—|—|—|—|—|該当なし|')
    else:
      for _,r in robust.iterrows():L.append(f'|{r.pre_cut:.2f}|{r.post_cut:.2f}|{int(r.n)}|{int(r.R)}|{r.trifecta_hit_rate_pct:.2f}%|{r.roi_pct:.2f}%|{int(r.R_feb_jun)}|{r.hit_feb_jun_pct:.2f}%|{r.roi_feb_jun_pct:.2f}%|')
    L += ['','## Next','- v253ではv252の結果から候補範囲を狭め、月別安定性・点数/合成オッズ条件を監査する。','- 4頭専用の可変TopNは、その後に別versionとしてfreezeする。']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
