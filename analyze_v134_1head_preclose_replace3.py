"""v134: validate the v133 3.0x replacement rule with pre-close odds.

Rule is frozen from v133: for v109+v110 1-head fixed top7, if the minimum PRE-CLOSE
odds among top7 is <=3.0, remove that cheapest ticket and add v110 rank8.
No final odds/result are used to decide the replacement. Final odds are settlement/
descriptive composite only after tickets are frozen.

Historical pre-close od3 snapshots only exist from 2026-07-19 in the current source,
so evaluation is Jul19-Aug31. August is shown separately.
"""
from __future__ import annotations
import csv
from statistics import mean, median
import analyze_v112_1head_preclose_ev as v112
import analyze_v128_allmodels_sixmonth_7ticket_composite as v128

SRC='analysis_v110_1head_role_tickets.csv'
OUT='analysis_v134_1head_preclose_replace3.csv'
SUMMARY='summary_v134_1head_preclose_replace3.md'
START='2026-07-19'; END='2026-08-31'; TH=3.0
A=.65; S=.72

def comp(od,ts):
    vals=[]
    for t in ts:
        o=od.get(t)
        if o is None or o<=1:return None
        vals.append(o)
    return 1/sum(1/o for o in vals)

def final_map(): return v128.load_odds()

def main():
    src=v112.read_csv(SRC)
    rs=[r for r in src if START<=r.get('date','')<=END and v112.ii(r.get('valid_result'))==1]
    dates={r['date'] for r in rs}
    pom,leads=v112.load_odds_map(dates)
    fm=final_map()
    rows=[]
    for r in rs:
        order=v112.order20(r)
        if len(order)<8:continue
        po=pom.get(r.get('race_code',''))
        if not po:continue
        pod=v112.odds20(po,order)
        if pod is None:continue
        top7=order[:7];eighth=order[7]
        vals=[pod[t] for t in top7]
        k=min(range(7),key=lambda i:vals[i]);minpre=vals[k]
        frozen=top7.copy();replaced=int(minpre<=TH)
        removed=''
        if replaced:
            removed=frozen[k];frozen[k]=eighth
        act=(r.get('actual_combo') or '').strip();code=r.get('race_code','')
        fod=fm.get(code,{})
        bfc=comp(fod,top7);rfc=comp(fod,frozen)
        bpc=comp(pod,top7);rpc=comp(pod,frozen)
        rows.append({'date':r['date'],'month':r['date'][:7],'race_code':code,'p109':v112.ff(r.get('p109'),-1),
                     'lead_min':leads.get(code,0),'min_preclose_odds_top7':minpre,'replaced':replaced,
                     'removed_ticket':removed,'added_ticket':eighth if replaced else '',
                     'baseline_hit':int(act in top7),'replacement_hit':int(act in frozen),
                     'baseline_preclose_comp':bpc,'replacement_preclose_comp':rpc,
                     'baseline_final_comp':bfc,'replacement_final_comp':rfc})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

    def met(q):
        n=len(q);rep=sum(x['replaced'] for x in q);bh=sum(x['baseline_hit'] for x in q);rh=sum(x['replacement_hit'] for x in q)
        bpre=[x['baseline_preclose_comp'] for x in q if x['baseline_preclose_comp'] is not None]
        rpre=[x['replacement_preclose_comp'] for x in q if x['replacement_preclose_comp'] is not None]
        bf=[x['baseline_final_comp'] for x in q if x['baseline_final_comp'] is not None]
        rf=[x['replacement_final_comp'] for x in q if x['replacement_final_comp'] is not None]
        ld=[x['lead_min'] for x in q if x['lead_min']>0]
        return {'n':n,'rep':rep,'repp':100*rep/n if n else 0,'bh':bh,'bhr':100*bh/n if n else 0,'rh':rh,'rhr':100*rh/n if n else 0,
                'bpre':mean(bpre) if bpre else 0,'rpre':mean(rpre) if rpre else 0,
                'bf':mean(bf) if bf else 0,'rf':mean(rf) if rf else 0,'fcov':len(bf),
                'lead':mean(ld) if ld else 0,'medlead':median(ld) if ld else 0}
    rec=[]
    for phase,lo,hi in [('ALL',START,END),('JUL19-31','2026-07-19','2026-07-31'),('AUG','2026-08-01','2026-08-31')]:
        z=[x for x in rows if lo<=x['date']<=hi]
        for g,cut in [('A',A),('S',S)]:
            q=[x for x in z if x['p109']>=cut]
            m=met(q);rec.append((phase,g,m))
    L=['# v134 1号艇 3.0倍ルール pre-close検証','',
       f'- 対象: **{START}〜{END}**（現行pre-close履歴は7/19以降）。',
       '- モデル/順位: **v109 + v110 λ=.50**、通常top7はオッズを見る前に固定。',
       '- 固定ルール: top7の**pre-close 3連単オッズ最小値が3.0倍以下**なら、その最安1点を削除しv110順位8位を追加。7点のまま。',
       '- pre-close snapshotはBoatraceCSV od3の取得時刻<締切だけを使用し、T-10に最も近いsnapshotを採用。',
       '- 結果・確定オッズは置換後にだけ参照。確定オッズは平均合成の事後評価用。','',
       '|期間|層|R|置換R|置換率|通常7点的中率|3倍ルール的中率|preclose平均合成 通常→置換|final平均合成 通常→置換|final odds R|平均snapshot前|',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ph,g,m in rec:
        L.append(f"|{ph}|{g}|{m['n']}|{m['rep']}|{m['repp']:.1f}%|{m['bhr']:.1f}%|{m['rhr']:.1f}%|{m['bpre']:.2f}→{m['rpre']:.2f}倍|{m['bf']:.2f}→{m['rf']:.2f}倍|{m['fcov']}|{m['lead']:.2f}分|")
    L += ['','## 注意','- 3.0倍という閾値自体はv133のMar-Aug確定オッズ分析から得たため、この期間は完全な未見holdoutではない。ここでは**確定オッズ依存だった効果が実際に使えるpre-close oddsでも再現するか**を検証する。','- production採用判断はSのAugustとALLの方向が一致するかを重視し、必要なら2026-09以降prospective shadowで最終確認する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)
if __name__=='__main__':main()
