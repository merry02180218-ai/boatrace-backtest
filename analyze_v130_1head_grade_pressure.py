"""v130 corrected: 1HEAD grade-pressure subsets, exact 7-ticket hit rate + average final composite odds.

Requested subsets over same six-month window as v128 (2026-03..08):
A) boat1=B1 AND AT LEAST ONE of boats2,3,4 is in {A1,A2}
B) boat1=A2 AND AT LEAST ONE of boats2,3,4 is A1
Also report union A OR B.

Prediction/ticket side is unchanged v109+v110 lambda=.50, exact 7 tickets.
Target-race final odds are post-hoc only and never used in model/ticket selection.
"""
from __future__ import annotations
import csv
from datetime import date, timedelta
from statistics import mean, median

import analyze_v110b_1head_role_tickets as one
from backtest import rows

START=date(2026,3,1); END=date(2026,8,31)
MONTHS=[f'2026-{m:02d}' for m in range(3,9)]
ONE_SRC='analysis_v108_1head_feasibility.csv'
ONE_P='analysis_v109_1head_monthly_walkforward.csv'
ODDS_FILES=('cache_v104_final_odds.csv','cache_v111_1head_final_odds.csv')
N=7; A_CUT=.65; S_CUT=.72
OUT='analysis_v130_1head_grade_pressure.csv'
SUMMARY='summary_v130_1head_grade_pressure.md'

def ff(x,d=0.):
    try:return float(x) if x is not None and str(x).strip()!='' else d
    except Exception:return d

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def load_odds():
    out={}
    for path in ODDS_FILES:
        try:
            with open(path,encoding='utf-8-sig',newline='') as f:
                for r in csv.DictReader(f):
                    c=(r.get('race_code') or r.get('レースコード') or '').strip();t=(r.get('combo') or r.get('組番') or '').strip();o=ff(r.get('odds') or r.get('オッズ'),0)
                    if c and t and o>1:out.setdefault(c,{})[t]=o
        except FileNotFoundError:pass
    return out

def composite(od,ts):
    if len(ts)!=N:return None
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    den=sum(1/o for o in vals)
    return 1/den if den>0 else None

def card_grades():
    out={};d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/programs/race_cards/{ymd}.csv'):
            code=(r.get('レースコード') or '').strip()
            if code:
                out[(str(d),code)]=tuple((r.get(f'艇{b}_級別') or '').strip() for b in range(1,7))
        d += timedelta(days=1)
    return out

def build_rows(fmap,grades):
    src=read(ONE_SRC);hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read(ONE_P)}
    for r in src:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
    out=[]
    for mo in MONTHS:
        print('prepare',mo,flush=True)
        for r in one.prepare_month(src,mo):
            p=ff(r.get('p109'),-1)
            if p<0:continue
            order=[x.strip() for x in (r.get('order_l50') or '').split(';') if x.strip()][:N]
            if len(order)!=N:continue
            ds=r.get('date','');code=(r.get('race_code') or '').strip();g=grades.get((ds,code))
            if not g:continue
            g1,g2,g3,g4,_,_=g
            cond_b1=(g1=='B1' and any(x in ('A1','A2') for x in (g2,g3,g4)))
            cond_a2=(g1=='A2' and any(x=='A1' for x in (g2,g3,g4)))
            if not (cond_b1 or cond_a2):continue
            co=composite(fmap.get(code,{}),order)
            act=(r.get('actual_combo') or '').strip()
            out.append({'date':ds,'race_code':code,'p109':p,'g1':g1,'g2':g2,'g3':g3,'g4':g4,
                        'cond_b1':int(cond_b1),'cond_a2':int(cond_a2),
                        'hit7':int(act in order),'composite_odds7':co})
    return out

def summarize(rows):
    rec=[]
    subsets=[('B1_vs_any_A1A2_2to4',lambda r:r['cond_b1']==1),('A2_vs_any_A1_2to4',lambda r:r['cond_a2']==1),('UNION',lambda r:r['cond_b1']==1 or r['cond_a2']==1)]
    for grade,cut in [('A',A_CUT),('S',S_CUT)]:
        for lab,fn in subsets:
            q=[r for r in rows if r['p109']>=cut and fn(r)];ods=[r['composite_odds7'] for r in q if r['composite_odds7'] is not None]
            hits=sum(r['hit7'] for r in q)
            rec.append({'grade':grade,'subset':lab,'races':len(q),'hits7':hits,'trifecta_hit_rate_pct':100*hits/len(q) if q else 0,
                        'odds_races':len(ods),'odds_coverage_pct':100*len(ods)/len(q) if q else 0,
                        'avg_composite_odds7':mean(ods) if ods else 0,'median_composite_odds7':median(ods) if ods else 0})
    return rec

def main():
    fmap=load_odds();grades=card_grades();print('grade cards',len(grades),'odds races',len(fmap),flush=True)
    rows=build_rows(fmap,grades);rec=summarize(rows)
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    L=['# v130 1号艇級別プレッシャー条件 7点的中率 / 平均合成オッズ（修正版）','',
       '- 期間: **2026-03-01〜2026-08-31**。','- 1号艇モデル: **v109 + v110 λ=.50、7点固定**。',
       '- 条件①: **1号艇B1 かつ 2・3・4号艇のうち少なくとも1艇がA1またはA2**。',
       '- 条件②: **1号艇A2 かつ 2・3・4号艇のうち少なくとも1艇がA1**。',
       '- UNIONは条件①または②。','- 確定合成オッズは事後評価だけに使用。選択・順位付けには不使用。','',
       '|層|条件|R|7点的中|3連単的中率|平均合成オッズ|中央値|odds R|oddsカバー|',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    names={'B1_vs_any_A1A2_2to4':'① B1 + 2-4にA1/A2が1艇以上','A2_vs_any_A1_2to4':'② A2 + 2-4にA1が1艇以上','UNION':'①または②'}
    for x in rec:
        L.append(f"|{x['grade']}|{names[x['subset']]}|{x['races']}|{x['hits7']}|{x['trifecta_hit_rate_pct']:.1f}%|{x['avg_composite_odds7']:.2f}倍|{x['median_composite_odds7']:.2f}倍|{x['odds_races']}|{x['odds_coverage_pct']:.1f}%|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L),flush=True)
if __name__=='__main__':main()
