"""v128: unified six-month (2026-03..08) all-model exact-7 retrospective backtest.

Purpose requested by user:
- trifecta hit rate for every model
- average final composite odds for exactly 7 frozen tickets

No same-race leakage:
- prediction/grade/head/ticket order is frozen before target-race result/final odds.
- target-race final odds are used only after ticket freeze for descriptive composite odds.
- 1HEAD role model is fit month-by-month using strictly prior dates; current fixed blend lambda=.50.
- 4C v106 lineage uses month-prior role fits + strictly prior-date historical price tendencies, lambda=.15.
- route-specific 3-makuri / 3-makurizashi and 5HEAD retain v51/base opponent order so the two 3-head routes remain separately reportable.

Caveat: this is a retrospective application of the current fixed rules to Mar-Aug; model/version choices were developed later,
so it is not six months of prospective deployment. It is however same-race no-leak.
"""
from __future__ import annotations
import csv, math
from statistics import mean, median

import analyze_v110b_1head_role_tickets as one
import analyze_v104_role_value_hybrid as v104

START='2026-03-01';END='2026-08-31';MONTHS=[f'2026-{m:02d}' for m in range(3,9)]
A=55.0;S=67.0;ONE_A=.65;ONE_S=.72;N=7
V83='analysis_v83_wind_entry_gate.csv'
ONE_SRC='analysis_v108_1head_feasibility.csv';ONE_P='analysis_v109_1head_monthly_walkforward.csv'
ODDS_FILES=('cache_v104_final_odds.csv','cache_v111_1head_final_odds.csv')
OUT='analysis_v128_allmodels_sixmonth_7ticket_composite.csv'
SUMMARY='summary_v128_allmodels_sixmonth_7ticket_composite.md'
ROUTE_MODELS=('3まくり','3まくり差し','5頭展開')

def ff(x,d=0.0):
    try:return float(x) if x is not None and str(x).strip()!='' else d
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

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

def composite_odds(od,ts):
    if len(ts)!=N:return None
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    den=sum(1/o for o in vals)
    return 1/den if den>0 else None

def route_rows(fmap):
    src=read(V83);out=[]
    for r in src:
        if not (START<=r.get('date','')<=END):continue
        m=r.get('model');
        if m not in ROUTE_MODELS:continue
        if ii(r.get('entry_gate_keep'))!=1 or ii(r.get('valid_result'))!=1:continue
        ts=[x.strip() for x in (r.get('tickets20_display') or '').split(';') if x.strip()][:N]
        if len(ts)!=N:continue
        score=ff(r.get('score'),-999);winner=ii(r.get('winner'));head=ii(r.get('head'));rank=ii(r.get('actual_rank20'))
        hit=int(winner==head and 1<=rank<=N)
        code=(r.get('race_code') or '').strip();co=composite_odds(fmap.get(code,{}),ts)
        out.append({'model':m,'date':r.get('date'),'race_code':code,'score':score,'head':head,'hit7':hit,'composite_odds7':co,'method':'v51 route-specific fixed opponent order'})
    return out

def fourcorner_rows(fmap):
    r4=v104.c4.read();role=v104.role_orders_4(r4);price=v104.prior_price_scores(r4,'4C',4,fmap)
    rr=v104.mkrows(r4,'4C',4,role,price,'score_CORR20_v91');out=[]
    for r in rr:
        if not (START<=r['date']<=END):continue
        order=v104.hybrid(r['role'],r['price'],.15);sel=order[:N];ts=[v104.tstr(4,p) for p in sel]
        hit=int(r['winner']==4 and r['actual'] in sel);co=composite_odds(fmap.get(r['race_code'],{}),ts)
        out.append({'model':'4カドまくり','date':r['date'],'race_code':r['race_code'],'score':r['score'],'head':4,'hit7':hit,'composite_odds7':co,'method':'v106 lineage: monthly-prior role + prior-price lambda .15'})
    return out

def onehead_rows(fmap):
    src=one.read_csv(ONE_SRC);hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in one.read_csv(ONE_P)}
    for r in src:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
    out=[]
    for mo in MONTHS:
        print('1HEAD prepare',mo,flush=True);rows=one.prepare_month(src,mo)
        for r in rows:
            p=ff(r.get('p109'),-1)
            if p<0:continue
            order=[x.strip() for x in (r.get('order_l50') or '').split(';') if x.strip()][:N]
            if len(order)!=N:continue
            act=(r.get('actual_combo') or '').strip();hit=int(act in order)
            code=(r.get('race_code') or '').strip();co=composite_odds(fmap.get(code,{}),order)
            out.append({'model':'1号艇','date':r.get('date'),'race_code':code,'score':100*p,'head':1,'hit7':hit,'composite_odds7':co,'method':'v109 + v110 role lambda .50 monthly-prior'})
    return out

def selected(r,g):
    if r['model']=='1号艇':return r['score'] >= 100*(ONE_S if g=='S' else ONE_A)
    return r['score'] >= (S if g=='S' else A)

def summarize(rows):
    rec=[]
    order=['1号艇','3まくり','3まくり差し','4カドまくり','5頭展開']
    for g in ('A','S'):
        for m in order:
            q=[r for r in rows if r['model']==m and selected(r,g)];hits=sum(r['hit7'] for r in q);ods=[r['composite_odds7'] for r in q if r['composite_odds7'] is not None]
            rec.append({'grade':g,'model':m,'races':len(q),'hits7':hits,'trifecta_hit_rate_pct':pct(hits,len(q)),'odds_races':len(ods),'odds_coverage_pct':pct(len(ods),len(q)),'avg_composite_odds7':mean(ods) if ods else 0.0,'median_composite_odds7':median(ods) if ods else 0.0})
    return rec

def main():
    fmap=load_odds();print('odds races cached',len(fmap),flush=True)
    rows=route_rows(fmap)+fourcorner_rows(fmap)+onehead_rows(fmap);rec=summarize(rows)
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    L=['# v128 全モデル 半年間・7点固定 3連単的中率 / 平均合成オッズ','',
       f'- 期間: **{START}〜{END}（2026年3〜8月の6か月）**',
       '- 点数: **全モデル7点固定**。',
       '- 合成オッズ = **1 / Σ(1/選択7点の締切時確定オッズ)**。各レースで計算後、その倍率を算術平均。',
       '- 確定オッズは買い目凍結後の事後評価だけに使用。同一レースの結果/確定オッズを選択・順位付けには使用しない。',
       '- 1号艇: v109 + v110（λ=.50、各月より前だけでrole学習）。',
       '- 3まくり/3まくり差し: ルート別集計を維持するためv51系固定相手順位。',
       '- 4カド: v106系（各月より前だけのrole + 過去確定オッズ傾向λ=.15）。対象レース自身のオッズは順位に不使用。',
       '- 5頭: v51系固定相手順位。','',
       '## 集計','|層|モデル|R|7点的中|3連単的中率|平均7点合成オッズ|中央値|odds R|oddsカバー|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in rec:
        av=f"{x['avg_composite_odds7']:.2f}倍" if x['odds_races'] else '-';md=f"{x['median_composite_odds7']:.2f}倍" if x['odds_races'] else '-'
        L.append(f"|{x['grade']}|{x['model']}|{x['races']}|{x['hits7']}|{x['trifecta_hit_rate_pct']:.1f}%|{av}|{md}|{x['odds_races']}|{x['odds_coverage_pct']:.1f}%|")
    L += ['','## 注意','- これは**現行固定ルールを過去6か月へ遡及適用したバックテスト**。同一レースのリークは防いでいるが、各version自体は後日開発されたため「6か月の完全prospective実績」ではない。','- 実運用比較では1号艇はSのみが現行BUY。非1号艇はA/S運用なので、A表とS表を両方残す。','- oddsカバーが100%未満なら、平均合成オッズは取得できたレースだけの平均として解釈する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L),flush=True)
if __name__=='__main__':main()
