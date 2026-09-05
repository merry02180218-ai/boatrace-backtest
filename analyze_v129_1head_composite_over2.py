"""v129: 1-head exact-7 retrospective slice where final composite odds > 2.0.

Uses the exact same Mar-Aug rows/ticket order/odds cache as v128.
Target-race final odds are used ONLY for post-hoc slicing/evaluation, never for prediction.
"""
from statistics import mean, median
import csv
import analyze_v128_allmodels_sixmonth_7ticket_composite as v128

OUT='analysis_v129_1head_composite_over2.csv'
SUMMARY='summary_v129_1head_composite_over2.md'
CUT=2.0

def main():
    fmap=v128.load_odds()
    rows=v128.onehead_rows(fmap)
    rec=[]
    for g in ('A','S'):
        base=[r for r in rows if v128.selected(r,g)]
        known=[r for r in base if r['composite_odds7'] is not None]
        q=[r for r in known if r['composite_odds7']>CUT]
        hits=sum(r['hit7'] for r in q)
        ods=[r['composite_odds7'] for r in q]
        rec.append({
            'grade':g,
            'all_selected_races':len(base),
            'odds_known_races':len(known),
            'composite_over2_races':len(q),
            'share_of_odds_known_pct':100*len(q)/len(known) if known else 0,
            'hits7':hits,
            'trifecta_hit_rate_pct':100*hits/len(q) if q else 0,
            'avg_composite_odds7':mean(ods) if ods else 0,
            'median_composite_odds7':median(ods) if ods else 0,
            'min_composite_odds7':min(ods) if ods else 0,
            'max_composite_odds7':max(ods) if ods else 0,
        })
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    L=['# v129 1号艇 7点合成オッズ > 2.0倍 の3連単的中率','',
       '- 期間: **2026-03-01〜2026-08-31**（v128と同じ6か月）。',
       '- 1号艇: **v109 + v110 λ=.50、7点固定**。',
       '- 条件: 各レースの7点締切時確定合成オッズが **2.0倍超**。',
       '- この確定オッズ条件は **事後分析専用**。予測・買い目順位には使っていない。','',
       '|層|対象全R|odds取得R|2倍超R|odds取得内比率|7点的中|3連単的中率|2倍超Rの平均合成オッズ|中央値|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rec:
        L.append(f"|{x['grade']}|{x['all_selected_races']}|{x['odds_known_races']}|{x['composite_over2_races']}|{x['share_of_odds_known_pct']:.1f}%|{x['hits7']}|{x['trifecta_hit_rate_pct']:.1f}%|{x['avg_composite_odds7']:.2f}倍|{x['median_composite_odds7']:.2f}倍|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
