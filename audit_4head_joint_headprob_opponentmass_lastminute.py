#!/usr/bin/env python3
"""4号艇: 頭確率 × opponent mass × 直前展示判定の3次元ROI監査。4〜8月のみ、9月禁止。"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
import audit_4head_headprob_pass_rescue as base
import analyze_4head_v283_second_margin_rescue as src
import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as oddsmod
import run_4head_v291_third010_live as live

OUT=Path('/tmp/head4_joint_grid'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'
HEAD_CUTS=[round(x,2) for x in np.arange(.20,.401,.02)]
MASS_CUTS=[round(x,2) for x in np.arange(.20,.701,.05)]
# 現行固定候補の直前展示入口 ORIG=-0.057777... 以上の中で、緩めずに締める方向を監査
LAST_CUTS=[-0.057777777777777706,-0.04,-0.02,0.0,0.02,0.04,0.06,0.08,0.10]
COMP_LOWER=[0.0,5.5,6.0,6.25,6.5,6.75]

def pair_mass(p2,pc,tickets):
    # v283と同じ alpha2=.60 の joint score を20通りで正規化し、採用買い目の累積確率質量を返す。
    vals={}
    for s in src.BOATS:
        for t in src.BOATS:
            if s==t: continue
            vals[(s,t)]=math.exp(live.ALPHA2*math.log(max(float(p2[s]),1e-12))+(1-live.ALPHA2)*math.log(max(float(pc[(s,t)]),1e-12)))
    den=sum(vals.values())
    return sum(vals[x]/den for x in tickets)

def summarize(q,mask,period,hc,mc,lc,lo):
    b=q[mask]; stake=10000*len(b); payout=float(b.payout_if_bet.sum()); rescue=b[b.current_bet.eq(0)]
    return {'期間':period,'頭確率基準':hc,'相手累積確率基準':mc,'直前展示基準':lc,'救済合成オッズ下限':lo,
            '購入R':len(b),'追加救済R':len(rescue),'4号艇1着':int(b.head4.sum()),
            '4号艇1着率':100*b.head4.mean() if len(b) else np.nan,'買い目的中':int(b.raw_hit.sum()),
            '投資':stake,'払戻':payout,'利益':payout-stake,'回収率':100*payout/stake if stake else np.nan}

def main():
    if END>='2026-09-01': raise RuntimeError('9月結果アクセス禁止')
    scores=base.headprob_scores()
    df,_=src.build(START,END); df['race_code']=df.race_code.astype(str).str.zfill(12)
    cx=cand.rebuild(START,END)[['race_code','orig4_adv_inside']].copy(); cx['race_code']=cx.race_code.astype(str).str.zfill(12)
    df=df.merge(scores,on='race_code',how='left',validate='one_to_one').merge(cx,on='race_code',how='left',validate='one_to_one')
    if len(df)!=164 or int(df.head4.sum())!=70 or df[['head_prob','orig4_adv_inside']].isna().any().any(): raise RuntimeError('固定母集団/結合再現失敗')
    cache={}; rows=[]
    for _,r in df.iterrows():
        pairs=src.pairs(r,None,live.THIRD_GAP); tickets=[f'4-{s}-{t}' for s,t in pairs]
        if tickets!=live.production_tickets(r.p2,r.pc): raise RuntimeError(f'買い目意味不一致 {r.race_code}')
        mass=pair_mass(r.p2,r.pc,pairs)
        actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''
        hit=bool(actual and actual in tickets)
        oq=cache.setdefault(r.date,oddsmod.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)]
        if len(oo)!=1: raise RuntimeError(f'オッズ不足 {r.race_code}')
        ovs=[]
        for t in tickets:
            v=pd.to_numeric(oo.iloc[0].get(t),errors='coerce')
            if pd.isna(v) or float(v)<=0: raise RuntimeError(f'オッズ異常 {r.race_code} {t}')
            ovs.append(float(v))
        comp=live.composite_odds(ovs); stakes={x['combo']:x['stake'] for x in live.dutch(tickets,ovs)}
        payout=float(stakes.get(actual,0))*float(oo.iloc[0].get(actual,0)) if hit else 0.0
        rows.append({'race_code':r.race_code,'date':r.date,'month':r.month,'head4':int(r.head4),'head_prob':float(r.head_prob),
                     'opponent_mass':mass,'last_orig':float(r.orig4_adv_inside),'raw_hit':int(hit),'composite_odds':comp,
                     'current_bet':int(comp>=7.0),'payout_if_bet':payout,'tickets':len(tickets)})
    rd=pd.DataFrame(rows)
    if int(rd.tickets.sum())!=817 or int(rd.raw_hit.sum())!=35: raise RuntimeError('THIRD0.10再現失敗')
    rd.to_csv(OUT/'race_detail.csv',index=False)
    periods=[('4〜6月 研究期間',rd[rd.month<='2026-06']),('7〜8月 未使用検証期間',rd[rd.month>='2026-07']),('4〜8月 参考',rd)]
    out=[]
    for name,q in periods:
        out.append(summarize(q,q.current_bet.eq(1),name,'現行','現行','現行',7.0))
        for hc in HEAD_CUTS:
          for mc in MASS_CUTS:
            for lc in LAST_CUTS:
              for lo in COMP_LOWER:
                rescue=q.current_bet.eq(0)&q.head_prob.ge(hc)&q.opponent_mass.ge(mc)&q.last_orig.ge(lc)&(q.composite_odds.ge(lo) if lo>0 else True)
                out.append(summarize(q,q.current_bet.eq(1)|rescue,name,hc,mc,lc,lo))
    sm=pd.DataFrame(out); sm.to_csv(OUT/'joint_grid.csv',index=False)
    # 研究期間と検証期間の同一セルを横持ちし、両方でROI>=100、検証追加>=5を安定候補として抽出。
    keys=['頭確率基準','相手累積確率基準','直前展示基準','救済合成オッズ下限']
    dev=sm[sm.期間=='4〜6月 研究期間'].set_index(keys); val=sm[sm.期間=='7〜8月 未使用検証期間'].set_index(keys)
    j=dev[['購入R','追加救済R','買い目的中','回収率','利益']].add_prefix('研究_').join(val[['購入R','追加救済R','買い目的中','回収率','利益']].add_prefix('検証_'),how='inner').reset_index()
    j=j[(j.検証_追加救済R>=5)&(j.研究_回収率>=100)&(j.検証_回収率>=100)].copy()
    if len(j):
        j['安定スコア']=np.minimum(j.研究_回収率,j.検証_回収率)
        j=j.sort_values(['安定スコア','検証_追加救済R','検証_回収率'],ascending=[False,False,False])
    j.head(100).to_csv(OUT/'robust_top100.csv',index=False)
    print('4号艇_頭確率_相手累積確率_直前展示_3次元ROI監査_OK')
    print('固定候補',len(rd),'4号艇1着',int(rd.head4.sum()),'買い目',int(rd.tickets.sum()),'的中',int(rd.raw_hit.sum()))
    print('安定候補数',len(j))
    if len(j): print(j.head(20).to_string(index=False))
    print('9月_UNREAD'); print('本番変更なし')

if __name__=='__main__': main()
