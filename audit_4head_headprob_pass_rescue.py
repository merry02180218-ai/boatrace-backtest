#!/usr/bin/env python3
"""4号艇: 頭確率で現行PASSを救済する回収率監査。4〜8月のみ、9月禁止。"""
from pathlib import Path
import math
import pandas as pd
import numpy as np
import audit_4head_boatracecsv_headprob_leakage as hp
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_v283_closing_odds as oddsmod
import run_4head_v291_third010_live as live

OUT=Path('/tmp/head4_headprob_pass_rescue'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'
HP_CUTS=[round(x,2) for x in np.arange(.20,.451,.01)]
LOWER=[0.0,5.5,6.0,6.25,6.5,6.75]

def headprob_scores():
    z=hp.build(); tr=z[z.month.isin(hp.TRAIN_MONTHS)].copy(); va=z[z.month.isin(hp.VALID_MONTHS)].copy()
    cand=[c for c in z.columns if c.startswith('b')]
    feats=[c for c in cand if tr[c].notna().sum()>=max(50,int(.25*len(tr)))]
    m=hp.model(); m.fit(tr[feats],tr.head4)
    tr['head_prob']=m.predict_proba(tr[feats])[:,1]; va['head_prob']=m.predict_proba(va[feats])[:,1]
    return pd.concat([tr,va])[['race_code','head_prob']].assign(race_code=lambda x:x.race_code.astype(str).str.zfill(12))

def summarize(q, mask, period, hcut, lower):
    b=q[mask]; stake=10000*len(b); payout=float(b.payout_if_bet.sum()); hits=int(b.raw_hit.sum())
    rescue=b[b.current_bet.eq(0)]
    return {'期間':period,'頭確率基準':hcut,'救済合成オッズ下限':lower,'購入R':len(b),'追加救済R':len(rescue),
            '購入中4号艇1着':int(b.head4.sum()),'購入中4号艇1着率':100*b.head4.mean() if len(b) else np.nan,
            '買い目的中':hits,'投資':stake,'払戻':payout,'利益':payout-stake,'回収率':100*payout/stake if stake else np.nan}

def main():
    if END>='2026-09-01': raise RuntimeError('9月結果アクセス禁止')
    scores=headprob_scores(); df,_=src.build(START,END); df['race_code']=df.race_code.astype(str).str.zfill(12)
    df=df.merge(scores,on='race_code',how='left',validate='one_to_one')
    if df.head_prob.isna().any():raise RuntimeError(f'頭確率結合不足 {df.head_prob.isna().sum()}')
    if len(df)!=164 or int(df.head4.sum())!=70:raise RuntimeError('固定164R再現失敗')
    cache={}; rows=[]
    for _,r in df.iterrows():
        tickets=[f'4-{s}-{t}' for s,t in src.pairs(r,None,live.THIRD_GAP)]
        if tickets!=live.production_tickets(r.p2,r.pc):raise RuntimeError(f'買い目意味不一致 {r.race_code}')
        actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''
        hit=bool(actual and actual in tickets)
        oq=cache.setdefault(r.date,oddsmod.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)]
        if len(oo)!=1:raise RuntimeError(f'オッズ不足 {r.race_code}')
        odds=[]
        for t in tickets:
            v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
            if pd.isna(v) or float(v)<=0:raise RuntimeError(f'オッズ異常 {r.race_code} {t}')
            odds.append(float(v))
        comp=live.composite_odds(odds); stakes={x['combo']:x['stake'] for x in live.dutch(tickets,odds)}
        payout=float(stakes.get(actual,0))*float(oo.iloc[0].get(actual,0)) if hit else 0.0
        rows.append({'race_code':r.race_code,'date':r.date,'month':r.month,'head4':r.head4,'head_prob':r.head_prob,
                     'tickets':len(tickets),'raw_hit':int(hit),'composite_odds':comp,'current_bet':int(comp>=7.0),'payout_if_bet':payout})
    rd=pd.DataFrame(rows)
    if int(rd.tickets.sum())!=817 or int(rd.raw_hit.sum())!=35:raise RuntimeError('THIRD0.10再現ガード失敗')
    periods=[('4〜6月 研究期間',rd[rd.month<='2026-06']),('7〜8月 未使用検証期間',rd[rd.month>='2026-07']),('4〜8月 参考',rd)]
    out=[]
    for name,q in periods:
        out.append(summarize(q,q.current_bet.eq(1),name,'現行','7.00'))
        for hc in HP_CUTS:
            for lo in LOWER:
                rescue=q.current_bet.eq(0)&q.head_prob.ge(hc)&(q.composite_odds.ge(lo) if lo>0 else True)
                out.append(summarize(q,q.current_bet.eq(1)|rescue,name,hc,lo))
    sm=pd.DataFrame(out); sm.to_csv(OUT/'headprob_rescue_grid.csv',index=False); rd.to_csv(OUT/'race_detail.csv',index=False)
    # 検証期間を主に見やすく表示。回収率100%以上かつ追加5R以上を抽出（結論の自動採用はしない）。
    hold=sm[(sm.期間=='7〜8月 未使用検証期間')&(sm.頭確率基準!='現行')&(sm.追加救済R>=5)].copy()
    hold=hold.sort_values(['回収率','追加救済R'],ascending=[False,False])
    hold.head(30).to_csv(OUT/'holdout_top30_reference.csv',index=False)
    print('4号艇_頭確率_PASS救済_ROI監査_OK')
    print('固定候補',len(rd),'4号艇1着',int(rd.head4.sum()),'買い目数',int(rd.tickets.sum()),'買い目的中',int(rd.raw_hit.sum()))
    print('\n7〜8月 未使用検証期間 上位参考')
    print(hold.head(20).to_string(index=False))
    print('9月_UNREAD'); print('本番変更なし')
if __name__=='__main__':main()
