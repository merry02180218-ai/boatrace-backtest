#!/usr/bin/env python3
"""v171: diagnose venue differences specifically in 2nd/3rd selection when boat 3 wins.
Frozen v165/v166 outputs only. No retuning, no venue filtering, payout settlement-only.
"""
import csv
from collections import Counter,defaultdict
from analyze_v166_3head_pair_direct import read,ff,ii,combo
SRC='analysis_v166_3head_pair_direct.csv'; OUT='analysis_v171_3head_pair_venue_diagnostics.csv'; SUMMARY='summary_v171_3head_pair_venue_diagnostics.md'
CUT=.30; N=10

def vc(r):
    try:return f"{int(float(r.get('venue',''))):02d}"
    except:return str(r.get('venue') or 'NA')
def tickets(r):return [x for x in str(r.get('v166_20','')).split(';') if x][:N]
def legsets(r):
    ts=tickets(r); sec={int(x.split('-')[1]) for x in ts}; third={int(x.split('-')[2]) for x in ts}; return sec,third

def main():
    a=[r for r in read(SRC) if ff(r.get('p3head'))>=CUT]
    rows=[]
    for v in sorted(set(vc(r) for r in a)):
        q=[r for r in a if vc(r)==v]; h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
        pair=sec=third=bothlegs=0; actual2=Counter();actual3=Counter();miss=Counter()
        for r in h:
            c=combo(r.get('actual_combo')); s,t=c[1],c[2]; actual2[s]+=1;actual3[t]+=1
            ss,tt=legsets(r); sh=s in ss; th=t in tt
            sec+=sh;third+=th;bothlegs+=sh and th
            ph=0<ii(r.get('v166_rank20'))<=N;pair+=ph
            if not ph: miss[f'{s}-{t}']+=1
        settled=[r for r in q if ii(r.get('valid_payout'))==1]; ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get('v166_rank20'))<=N); inv=len(settled)*N*100
        rows.append({'venue':v,'candidate_R':len(q),'head3_R':len(h),'head3_rate':100*len(h)/len(q) if q else 0,'pair_coverage':100*pair/len(h) if h else 0,'second_leg_coverage':100*sec/len(h) if h else 0,'third_leg_coverage':100*third/len(h) if h else 0,'both_legs_present':100*bothlegs/len(h) if h else 0,'roi':100*ret/inv if inv else 0,'actual_2nd_dist':' '.join(f'{k}:{n}' for k,n in sorted(actual2.items())),'actual_3rd_dist':' '.join(f'{k}:{n}' for k,n in sorted(actual3.items())),'top_pair_misses':' '.join(f'{k}:{n}' for k,n in miss.most_common(5))})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    L=['# v171 3号艇 2着3着・場別診断','',f'- Frozen: p3 >= {CUT:.2f}, v166 top {N}.','- ③頭になったレースだけで、2着艇を候補内に含めた率・3着艇を含めた率・ordered pairまで当たった率を場別比較。','- Jun-Aug結果を使った再学習・場除外はしない。','','|venue|候補R|③頭R|③頭率|2着leg|3着leg|両leg|pair coverage|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f"|{r['venue']}|{r['candidate_R']}|{r['head3_R']}|{r['head3_rate']:.1f}%|{r['second_leg_coverage']:.1f}%|{r['third_leg_coverage']:.1f}%|{r['both_legs_present']:.1f}%|{r['pair_coverage']:.1f}%|{r['roi']:.1f}%|")
    L += ['','## 見方','- 2着legが低い場: 2着候補選択側のズレが疑わしい。','- 3着legが低い場: 3着候補選択側のズレが疑わしい。','- 両legは高いのにpair coverageが低い場: 2着/3着の順序付け（ordered pair）が主な問題候補。','- 詳細CSVには実際の2着/3着艇分布と、外したpair上位を保存。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
