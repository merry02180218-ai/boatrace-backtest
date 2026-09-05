"""v132: 1-head fixed-7 variant.

For each race, start from v110 top 7. Among those seven, remove the ticket with the
lowest final trifecta odds, then add v110 rank-8 ticket. Evaluate trifecta hit rate
and composite odds. This uses target-race final odds to choose the removed ticket,
so it is post-hoc/descriptive only, not a valid live rule.
"""
from __future__ import annotations
import csv
from statistics import mean, median
import analyze_v110b_1head_role_tickets as one
import analyze_v128_allmodels_sixmonth_7ticket_composite as v128

OUT='analysis_v132_1head_replace_lowest_odds_with_8th.csv'
SUMMARY='summary_v132_1head_replace_lowest_odds_with_8th.md'

def comp(od, ts):
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    return 1/sum(1/o for o in vals)

def main():
    fmap=v128.load_odds()
    src=one.read_csv(v128.ONE_SRC)
    hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in one.read_csv(v128.ONE_P)}
    for r in src:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
    rows=[]
    for mo in v128.MONTHS:
        print('prepare',mo,flush=True)
        for r in one.prepare_month(src,mo):
            p=v128.ff(r.get('p109'),-1)
            if p<0:continue
            order=[x.strip() for x in (r.get('order_l50') or '').split(';') if x.strip()]
            if len(order)<8:continue
            code=(r.get('race_code') or '').strip(); od=fmap.get(code,{})
            top7=order[:7]; eighth=order[7]
            base_comp=comp(od,top7)
            vals=[od.get(t) for t in top7]
            can=all(o is not None and o>1 for o in vals) and od.get(eighth) is not None and od.get(eighth)>1
            repl=None; removed=None; repl_comp=None
            if can:
                k=min(range(7),key=lambda i: vals[i])
                removed=top7[k]
                repl=top7.copy(); repl[k]=eighth
                repl_comp=comp(od,repl)
            act=(r.get('actual_combo') or '').strip()
            rows.append({'date':r.get('date'),'race_code':code,'p109':p,'actual_combo':act,
                         'baseline_hit7':int(act in top7),'baseline_comp':base_comp,
                         'removed_ticket':removed or '','added_ticket':eighth,'replacement_hit7':int(repl is not None and act in repl),
                         'replacement_comp':repl_comp})
    rec=[]
    for g,cut in [('A',v128.ONE_A),('S',v128.ONE_S)]:
        q=[r for r in rows if r['p109']>=cut]
        usable=[r for r in q if r['replacement_comp'] is not None]
        # Fair comparison on identical odds-known/replacement-possible subset.
        bh=sum(r['baseline_hit7'] for r in usable); rh=sum(r['replacement_hit7'] for r in usable)
        bc=[r['baseline_comp'] for r in usable if r['baseline_comp'] is not None]; rc=[r['replacement_comp'] for r in usable]
        rec.append({'grade':g,'all_races':len(q),'usable_races':len(usable),'coverage_pct':100*len(usable)/len(q) if q else 0,
                    'baseline_hits':bh,'baseline_hit_rate_pct':100*bh/len(usable) if usable else 0,
                    'baseline_avg_comp':mean(bc) if bc else 0,'baseline_median_comp':median(bc) if bc else 0,
                    'replacement_hits':rh,'replacement_hit_rate_pct':100*rh/len(usable) if usable else 0,
                    'replacement_avg_comp':mean(rc) if rc else 0,'replacement_median_comp':median(rc) if rc else 0})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    L=['# v132 1号艇 Top7の最低オッズ1点を外して8位を追加','',
       '- 期間: **2026-03-01〜2026-08-31**。',
       '- 1号艇モデル: **v109 + v110 λ=.50**。',
       '- 基準: v110上位7点。',
       '- 変更: 上位7点のうち**確定3連単オッズが最も低い1点を削除**し、**v110順位8位の1点を追加**。点数は7点のまま。',
       '- 重要: 削除判断に対象レースの確定オッズを使うため、この比較は**事後分析専用**。ライブ運用にはそのまま使えない。',
       '- 比較は、元7点と8位の全8点の確定オッズが取得できた同一レース集合で実施。','',
       '|層|全R|比較可能R|カバー|通常7点 的中率|通常 平均合成|置換7点 的中率|置換 平均合成|',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in rec:
        L.append(f"|{x['grade']}|{x['all_races']}|{x['usable_races']}|{x['coverage_pct']:.1f}%|{x['baseline_hit_rate_pct']:.1f}%|{x['baseline_avg_comp']:.2f}倍|{x['replacement_hit_rate_pct']:.1f}%|{x['replacement_avg_comp']:.2f}倍|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
