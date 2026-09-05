"""v133: conditional replacement sweep for 1-head top7.

Start from v110 top7. Find the lowest final trifecta odds among the seven.
Only if that minimum odds <= threshold, replace that ticket with v110 rank-8.
Evaluate hit rate and composite odds vs unchanged top7.

IMPORTANT: target-race final odds are used for the replacement condition, so this is
post-hoc/descriptive only. It is not a valid live rule until separately tested with
pre-close odds.
"""
from __future__ import annotations
import csv
from statistics import mean, median
import analyze_v110b_1head_role_tickets as one
import analyze_v128_allmodels_sixmonth_7ticket_composite as v128

OUT='analysis_v133_1head_conditional_replace_lowodds.csv'
SUMMARY='summary_v133_1head_conditional_replace_lowodds.md'
THRESHOLDS=[3.0,4.0,5.0,6.0,7.0,8.0,10.0,12.0,15.0,20.0]

def comp(od,ts):
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    den=sum(1/o for o in vals)
    return 1/den if den>0 else None

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
            code=(r.get('race_code') or '').strip();od=fmap.get(code,{})
            top7=order[:7];eighth=order[7]
            vals=[od.get(t) for t in top7]
            can=all(o is not None and o>1 for o in vals) and od.get(eighth) is not None and od.get(eighth)>1
            if not can:continue
            k=min(range(7),key=lambda i:vals[i]);minod=vals[k]
            repl=top7.copy();repl[k]=eighth
            act=(r.get('actual_combo') or '').strip()
            rows.append({'date':r.get('date'),'race_code':code,'p109':p,'min_odds':minod,
                         'baseline_hit':int(act in top7),'baseline_comp':comp(od,top7),
                         'replacement_hit':int(act in repl),'replacement_comp':comp(od,repl)})
    rec=[]
    for g,cut in [('A',v128.ONE_A),('S',v128.ONE_S)]:
        q=[r for r in rows if r['p109']>=cut]
        base_hits=sum(r['baseline_hit'] for r in q)
        base_avg=mean(r['baseline_comp'] for r in q)
        base_med=median(r['baseline_comp'] for r in q)
        rec.append({'grade':g,'threshold':'BASE','races':len(q),'replaced_races':0,'replace_pct':0.0,
                    'hits7':base_hits,'hit_rate_pct':100*base_hits/len(q) if q else 0,
                    'avg_comp':base_avg,'median_comp':base_med})
        for th in THRESHOLDS:
            hits=0;cs=[];nrep=0
            for r in q:
                if r['min_odds']<=th:
                    hits+=r['replacement_hit'];cs.append(r['replacement_comp']);nrep+=1
                else:
                    hits+=r['baseline_hit'];cs.append(r['baseline_comp'])
            rec.append({'grade':g,'threshold':f'{th:.1f}','races':len(q),'replaced_races':nrep,
                        'replace_pct':100*nrep/len(q) if q else 0,
                        'hits7':hits,'hit_rate_pct':100*hits/len(q) if q else 0,
                        'avg_comp':mean(cs) if cs else 0,'median_comp':median(cs) if cs else 0})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    L=['# v133 1号艇 低オッズ時だけ8位へ置換・閾値スイープ','',
       '- 期間: **2026-03-01〜2026-08-31**。',
       '- 1号艇モデル: **v109 + v110 λ=.50、7点固定**。',
       '- ルール: v110上位7点のうち最も低い確定3連単オッズが閾値以下の時だけ、その1点を削除してv110順位8位を追加。',
       '- 比較可能条件: 上位7点+8位の全8点で確定オッズ取得済み。',
       '- **重要: 対象レースの確定オッズで置換判断するため事後分析専用。ライブ採用には直前オッズで別検証が必要。**','',
       '|層|最低オッズ閾値|R|置換R|置換率|7点的中|3連単的中率|平均合成|中央値|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in rec:
        lab='通常7点' if x['threshold']=='BASE' else f"{x['threshold']}倍以下"
        L.append(f"|{x['grade']}|{lab}|{x['races']}|{x['replaced_races']}|{x['replace_pct']:.1f}%|{x['hits7']}|{x['hit_rate_pct']:.1f}%|{x['avg_comp']:.2f}倍|{x['median_comp']:.2f}倍|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
