#!/usr/bin/env python3
"""v182: v180 style probability for broad candidate extraction, then v165 probability as final filter.

NO-LEAK:
- v180/style and v165 probabilities are walk-forward pre-result probabilities;
- style cut × v165 cut is selected using Mar-May only;
- Jun-Aug is a completely fixed OOS evaluation;
- v166 ordered-pair lambda is selected by its existing Mar-May rule;
- payout is settlement-only after race/ticket selection is fixed.
"""
import csv
import pandas as pd
from analyze_v165_3head_monthly_walkforward import load,target,feats,model,pc
from analyze_v166_3head_pair_direct import read,ff,ii,combo,choose,score_month,pct,HEADSRC
from analyze_v177_3head_historical_web_enrichment import reconstruct

OUT='analysis_v182_3head_style_then_v165_filter_oos.csv'
SUMMARY='summary_v182_3head_style_then_v165_filter_oos.md'
VAL=['2026-03','2026-04','2026-05']; TEST=['2026-06','2026-07','2026-08']
STYLE=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate','style_makuri_edge','style_makurisashi_edge']
# v180 is deliberately the broad first-stage gate; v165 is the stricter second-stage filter.
STYLE_CUTS=[.20,.225,.25,.275,.30]
BASE_CUTS=[.20,.225,.25,.275,.30,.325,.35,.375,.40]

def build_style_probs():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place']); y,_=target(df); base=feats(df)
    raw=read(str(src)); extra,cov=reconstruct(raw); d=df.copy(); d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce'); d['_y']=y
    for k in STYLE:d[k]=[float(extra.get(i,{}).get(k,0.0)) for i in range(len(d))]
    d=d[d._date.notna()&d._y.notna()].copy(); out={}
    for mon in VAL+TEST:
        m=pd.Timestamp(mon+'-01'); e=m+pd.offsets.MonthBegin(1); tr=d[d._date<m].copy(); te=d[(d._date>=m)&(d._date<e)].copy(); fs=base+STYLE; nums=[]
        for c in fs:
            if pd.to_numeric(d[c],errors='coerce').notna().mean()>=.8:
                tr[c]=pd.to_numeric(tr[c],errors='coerce'); te[c]=pd.to_numeric(te[c],errors='coerce'); nums.append(c)
        cats=[vc] if vc and vc not in nums else []; mo=model(nums,cats); mo.fit(tr[nums+cats],tr._y.astype(int)); p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p):out[int(ix)]=float(pr)
    return raw,out,cov

def selected(rs,sc,bc):
    return [r for r in rs if ff(r.get('p3style'))>=sc and ff(r.get('p3base'))>=bc]

def stat(rs,sc,bc):
    q=selected(rs,sc,bc); h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hit=[r for r in q if 0<ii(r.get('v166_rank20'))<=10]; sett=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in sett if 0<ii(r.get('v166_rank20'))<=10)
    return len(q),pct(len(h),len(q)),pct(len(hit),len(q)),pct(sum(1 for r in h if 0<ii(r.get('v166_rank20'))<=10),len(h)),100*ret/(len(sett)*1000) if sett else 0

def month_stats(rs,sc,bc,months):
    return [stat([r for r in rs if r.get('v166_month')==mo],sc,bc) for mo in months]

def main():
    src,stylep,cov=build_style_probs(); basep={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    lam,_=choose(src); allrows=[]
    for mon in VAL+TEST: allrows+=score_month(src,mon,lam)
    keyidx={(r['date'],r.get('race_code')):i for i,r in enumerate(src)}
    for r in allrows:
        i=keyidx.get((r['date'],r.get('race_code')),-1); r['p3style']=stylep.get(i,''); r['p3base']=basep.get(i,'')
    val=[r for r in allrows if r.get('v166_month') in VAL]
    tune=[]
    for sc in STYLE_CUTS:
        for bc in BASE_CUTS:
            n,hr,hit,cv,roi=stat(val,sc,bc); ms=month_stats(val,sc,bc,VAL)
            min_r=min(x[0] for x in ms); worst_roi=min(x[4] for x in ms); tune.append((sc,bc,n,hr,hit,cv,roi,min_r,worst_roi))
    # Robust pre-OOS selection: useful sample overall and every validation month, adequate 3-head rate.
    eligible=[x for x in tune if x[2]>=150 and x[7]>=30 and x[3]>=30.0]
    if not eligible: eligible=[x for x in tune if x[2]>=100 and x[7]>=20]
    # ROI first, then monthly downside/stability, then hit/head rate.
    best=max(eligible,key=lambda x:(x[6],x[8],x[4],x[3],x[2])); sc,bc=best[0],best[1]
    test=[r for r in allrows if r.get('v166_month') in TEST]
    fs=sorted(set().union(*(r.keys() for r in test)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(test)
    ranked=sorted(tune,key=lambda x:(x[6],x[8],x[4],x[3]),reverse=True)
    L=['# v182 v180候補抽出 → v165最終選別 → v166 top10','', '- v180/styleで広く候補抽出し、その候補をv165確率で最終選別。','- style cut × v165 cutはMar-Mayだけで固定。Jun-Augは完全OOS。',f'- v166 pair lambda = {lam:.2f}',f"- reconstruction matched: {cov['matched_src']}",'','## Mar-May tuning 上位15','|style cut|v165 cut|R|③頭率|top10 hit|coverage|ROI|月最小R|月最悪ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in ranked[:15]:L.append(f'|{x[0]:.3f}|{x[1]:.3f}|{x[2]}|{x[3]:.2f}%|{x[4]:.2f}%|{x[5]:.2f}%|{x[6]:.1f}%|{x[7]}|{x[8]:.1f}%|')
    L += ['',f'固定条件 = **v180/style >= {sc:.3f} AND v165 >= {bc:.3f}**','','## Jun-Aug fixed OOS','|month|R|③頭率|top10 hit|coverage|ROI|','|---|---:|---:|---:|---:|---:|']
    for mo in TEST:
        x=stat([r for r in test if r.get('v166_month')==mo],sc,bc);L.append(f'|{mo}|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    x=stat(test,sc,bc);L.append(f'|ALL|{x[0]}|{x[1]:.2f}%|{x[2]:.2f}%|{x[3]:.2f}%|{x[4]:.1f}%|')
    L += ['','## Current production reference','- v165 p3>=0.30 + v166 top10: Jun-Aug R270, ③頭率38.52%, hit29.26%, coverage75.96%, ROI103.2%.','', '## Decision rule','- ROI最優先。現行103.2%を上回るか、少なくとも同等ROIでhit/③頭率/安定性が改善する場合のみ採用候補。Jun-Augを見て閾値は変更しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))
if __name__=='__main__':main()
