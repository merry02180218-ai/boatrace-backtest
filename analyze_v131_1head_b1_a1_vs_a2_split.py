"""v131: split v130 B1 inner-opponent condition into A1-present vs A2-only.

Same 2026-03..08 window, v109+v110 lambda=.50, fixed top7 tickets.
Final odds are post-hoc only.
"""
from __future__ import annotations
import csv
from statistics import mean, median
import analyze_v130_1head_grade_pressure as v130

OUT='analysis_v131_1head_b1_a1_vs_a2_split.csv'
SUMMARY='summary_v131_1head_b1_a1_vs_a2_split.md'


def summarize(rows):
    rec=[]
    subsets=[
      ('A1_PRESENT',lambda r: r['g1']=='B1' and any(g=='A1' for g in (r['g2'],r['g3'],r['g4']))),
      ('A2_ONLY',lambda r: r['g1']=='B1' and not any(g=='A1' for g in (r['g2'],r['g3'],r['g4'])) and any(g=='A2' for g in (r['g2'],r['g3'],r['g4']))),
      ('B1_ANY_A1A2',lambda r: r['g1']=='B1' and any(g in ('A1','A2') for g in (r['g2'],r['g3'],r['g4']))),
    ]
    for grade,cut in [('A',v130.A_CUT),('S',v130.S_CUT)]:
        for lab,fn in subsets:
            q=[r for r in rows if r['p109']>=cut and fn(r)]
            ods=[r['composite_odds7'] for r in q if r['composite_odds7'] is not None]
            hits=sum(r['hit7'] for r in q)
            rec.append({'grade':grade,'subset':lab,'races':len(q),'hits7':hits,
                        'trifecta_hit_rate_pct':100*hits/len(q) if q else 0,
                        'odds_races':len(ods),'odds_coverage_pct':100*len(ods)/len(q) if q else 0,
                        'avg_composite_odds7':mean(ods) if ods else 0,
                        'median_composite_odds7':median(ods) if ods else 0})
    return rec


def main():
    fmap=v130.load_odds(); grades=v130.card_grades(); rows=v130.build_rows(fmap,grades)
    rec=summarize(rows)
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    names={'A1_PRESENT':'B1 + 2-4にA1が1艇以上','A2_ONLY':'B1 + 2-4にA1なし/A2が1艇以上','B1_ANY_A1A2':'B1 + 2-4にA1/A2が1艇以上'}
    L=['# v131 B1内枠上位級のA1/A2分解','',
       '- 期間: **2026-03-01〜2026-08-31**。',
       '- 1号艇モデル: **v109 + v110 λ=.50、7点固定**。',
       '- A1あり: 1号艇B1かつ2〜4号艇にA1が1艇以上。',
       '- A2のみ: 1号艇B1かつ2〜4号艇にA1はいないがA2が1艇以上。',
       '- 確定合成オッズは事後評価のみ。','',
       '|層|条件|R|7点的中|3連単的中率|平均合成オッズ|中央値|odds R|oddsカバー|',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in rec:
        L.append(f"|{x['grade']}|{names[x['subset']]}|{x['races']}|{x['hits7']}|{x['trifecta_hit_rate_pct']:.1f}%|{x['avg_composite_odds7']:.2f}倍|{x['median_composite_odds7']:.2f}倍|{x['odds_races']}|{x['odds_coverage_pct']:.1f}%|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__': main()
