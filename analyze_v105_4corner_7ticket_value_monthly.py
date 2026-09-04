"""v105: monthly holdout stability test for the v104 4C 7-ticket value hybrid.

Frozen before execution:
- model: 4C only
- base: v96 role-aware pair order (CORR20 lineage)
- value lambda: 0.15
- tickets: exactly 7
- test months: 2026-06, 2026-07, 2026-08
- no lambda/ticket-count tuning in this script

No-leak:
- pair role order is fit month-by-month using only races before target month (v104/v96 logic)
- value tendency for a race uses only earlier-date cached final odds
- target-race final odds are used only after ticket freeze for composite-rate evaluation

Pre-fixed PASS criterion:
1) Jun-Aug aggregate, both A and S: hybrid hit rate >= role hit rate,
   hybrid composite rate <= role composite rate, and hybrid ROI >= role ROI.
2) Among the six month x grade cells, composite rate improves in >=4 cells.
3) Cells where BOTH hit rate and ROI worsen <=1/6.
"""
from __future__ import annotations

import csv
from statistics import mean

import analyze_v104_role_value_hybrid as v104

CACHE='cache_v104_final_odds.csv'
OUT='analysis_v105_4corner_7ticket_value_monthly.csv'
SUMMARY='summary_v105_4corner_7ticket_value_monthly.md'
LAM=0.15
N=7
A=55.0
S=67.0
MONTHS=('2026-06','2026-07','2026-08')


def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception: return d


def load_cache():
    out={}
    with open(CACHE,encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            c=(r.get('race_code') or '').strip(); t=(r.get('combo') or '').strip()
            try: o=float(r.get('odds') or 0)
            except Exception: o=0
            if c and t and o>1: out.setdefault(c,{})[t]=o
    return {c:d for c,d in out.items() if len(d)>=100}


def one_metrics(q,lam,fmap):
    hit=0; ret=0; comps=[]; headwins=0; pairhit=0; changed=0
    for r in q:
        base=r['role']
        order=base if lam==0 else v104.hybrid(base,r['price'],lam)
        sel=order[:N]
        if order[:N] != base[:N]: changed += 1
        if r['winner']==4:
            headwins += 1
            if r['actual'] in sel:
                pairhit += 1
                hit += 1
                if r['valid_payout']: ret += r['payout100']
        od=fmap.get(r['race_code'],{})
        if od:
            cr=v104.vo.composite_rate(od,[v104.tstr(4,p) for p in sel])
            if cr is not None: comps.append(cr)
    inv=sum(r['valid_payout'] for r in q)*N*100
    return {
        'races':len(q),'headwins':headwins,'hit':hit,
        'hit_rate':100*hit/len(q) if q else 0.0,
        'pair_cov':100*pairhit/headwins if headwins else 0.0,
        'comp':mean(comps) if comps else 0.0,
        'roi':100*ret/inv if inv else 0.0,
        'odds_races':len(comps),'changed':changed,
    }


def build_rows(r4,fmap):
    role=v104.role_orders_4(r4)
    price=v104.prior_price_scores(r4,'4C',4,fmap)
    return v104.mkrows(r4,'4C',4,role,price,'score_CORR20_v91')


def row_for(period,grade,cut,q,fmap):
    b=one_metrics(q,0.0,fmap); h=one_metrics(q,LAM,fmap)
    return {
        'period':period,'grade':grade,'lambda':LAM,'tickets':N,
        'races':h['races'],'headwins':h['headwins'],'odds_races':h['odds_races'],'changed_races':h['changed'],
        'role_hit_rate_pct':b['hit_rate'],'hybrid_hit_rate_pct':h['hit_rate'],'hit_diff_pt':h['hit_rate']-b['hit_rate'],
        'role_pair_coverage_pct':b['pair_cov'],'hybrid_pair_coverage_pct':h['pair_cov'],'pair_cov_diff_pt':h['pair_cov']-b['pair_cov'],
        'role_comp_rate_pct':b['comp'],'hybrid_comp_rate_pct':h['comp'],'comp_reduction_pt':b['comp']-h['comp'],
        'role_roi_pct':b['roi'],'hybrid_roi_pct':h['roi'],'roi_diff_pt':h['roi']-b['roi'],
    }


def main():
    r4=v104.c4.read(); fmap=load_cache(); rows=build_rows(r4,fmap)
    out=[]
    for grade,cut in (('A',A),('S',S)):
        for m in MONTHS:
            q=[r for r in rows if r['date'][:7]==m and r['score']>=cut]
            out.append(row_for(m,grade,cut,q,fmap))
        q=[r for r in rows if r['date'][:7] in MONTHS and r['score']>=cut]
        out.append(row_for('2026-06..08',grade,cut,q,fmap))

    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    agg=[r for r in out if r['period']=='2026-06..08']
    monthly=[r for r in out if r['period']!='2026-06..08']
    agg_ok=all(r['hit_diff_pt']>=-1e-9 and r['comp_reduction_pt']>=-1e-9 and r['roi_diff_pt']>=-1e-9 for r in agg)
    comp_good=sum(r['comp_reduction_pt']>1e-9 for r in monthly)
    joint_bad=sum(r['hit_diff_pt']<-1e-9 and r['roi_diff_pt']<-1e-9 for r in monthly)
    passed=agg_ok and comp_good>=4 and joint_bad<=1

    L=['# v105 4カド7点専用 価格補正 月別walk-forward','',
       '- v104で選ばれた `value λ=0.15` を固定。','- 点数は7点固定。','- 4C CORR20 + v96役割別順位を土台。',
       '- 6/7/8月で再調整なし。対象レースの確定オッズは順位作成に使わず、合成率評価だけ。','',
       '## 月別結果','|月|級|R|4頭1着|買い目変更R|役割的中率|hybrid的中率|差|役割合成率|hybrid合成率|低下|役割ROI|hybrid ROI|差|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in monthly:
        L.append(f"|{r['period']}|{r['grade']}|{r['races']}|{r['headwins']}|{r['changed_races']}|{r['role_hit_rate_pct']:.1f}%|{r['hybrid_hit_rate_pct']:.1f}%|{r['hit_diff_pt']:+.1f}pt|{r['role_comp_rate_pct']:.1f}%|{r['hybrid_comp_rate_pct']:.1f}%|{r['comp_reduction_pt']:+.1f}pt|{r['role_roi_pct']:.1f}%|{r['hybrid_roi_pct']:.1f}%|{r['roi_diff_pt']:+.1f}pt|")
    L += ['','## Jun-Aug aggregate','|級|R|役割的中率|hybrid的中率|差|役割合成率|hybrid合成率|低下|役割ROI|hybrid ROI|差|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in agg:
        L.append(f"|{r['grade']}|{r['races']}|{r['role_hit_rate_pct']:.1f}%|{r['hybrid_hit_rate_pct']:.1f}%|{r['hit_diff_pt']:+.1f}pt|{r['role_comp_rate_pct']:.1f}%|{r['hybrid_comp_rate_pct']:.1f}%|{r['comp_reduction_pt']:+.1f}pt|{r['role_roi_pct']:.1f}%|{r['hybrid_roi_pct']:.1f}%|{r['roi_diff_pt']:+.1f}pt|")
    L += ['','## 事前固定判定','- Aggregate A/Sとも 的中率非悪化・合成率非増加・ROI非悪化。',
          '- 月別6セルのうち合成率改善が4セル以上。','- 的中率とROIが同時悪化する月別セルは1セル以下。','',
          f'- Aggregate条件: **{"PASS" if agg_ok else "FAIL"}**',
          f'- 合成率改善セル: **{comp_good}/6**',f'- 的中率&ROI同時悪化セル: **{joint_bad}/6**',
          f'- **v105 FINAL: {"PASS" if passed else "FAIL"}**','',
          '- PASSでもproduction自動採用はしない。次は2026-09-05以降のprospective shadow対象。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__': main()
