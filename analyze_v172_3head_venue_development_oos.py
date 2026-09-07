#!/usr/bin/env python3
"""v172: venue/development diagnostics conditional on boat 3 winning.

Question: when boat 3 wins, do venues have persistent 2nd/3rd-place patterns?
Design:
- PRE period: all valid races before 2026-06-01, only actual head=3.
- OOS: 2026-06 through 2026-08, only actual head=3.
- Venue tendencies are learned/described from PRE only.
- OOS is evaluation only; no venue filtering or retuning.
- Outcome fields are used only as labels/diagnostics, never as predictive features.
"""
from __future__ import annotations
import csv, math
from collections import Counter
from datetime import date
from analyze_v166_3head_pair_direct import read, combo, ii, SRC

OUT='analysis_v172_3head_venue_development_oos.csv'
SUMMARY='summary_v172_3head_venue_development_oos.md'
TEST_MONTHS={'2026-06','2026-07','2026-08'}
OPP=[1,2,4,5,6]

VENUE_NAMES={
'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
'07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
'13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
'19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}

def vc(r):
    try:return f"{int(float(r.get('venue',''))):02d}"
    except:return str(r.get('venue') or 'NA')

def norm(c):
    n=sum(c.values()); return {k:(c.get(k,0)/n if n else 0.0) for k in OPP}

def tv(p,q): return .5*sum(abs(p[k]-q[k]) for k in OPP)

def top_lane(p): return max(OPP,key=lambda k:(p[k],-k)) if sum(p.values()) else 0

def share(c, lanes):
    n=sum(c.values()); return sum(c.get(k,0) for k in lanes)/n if n else 0.0

def rows3(src):
    out=[]
    for r in src:
        if ii(r.get('valid_result'))!=1: continue
        a=combo(r.get('actual_combo'))
        if len(a)==3 and a[0]==3 and a[1] in OPP and a[2] in OPP and a[1]!=a[2]: out.append(r)
    return out

def main():
    src=rows3(read(SRC))
    pre=[r for r in src if date.fromisoformat(r['date']) < date(2026,6,1)]
    oos=[r for r in src if r.get('month') in TEST_MONTHS]
    rows=[]
    for v in [f'{i:02d}' for i in range(1,25)]:
        a=[r for r in pre if vc(r)==v]; b=[r for r in oos if vc(r)==v]
        p2=Counter();p3=Counter();q2=Counter();q3=Counter();ppair=Counter();qpair=Counter()
        for r in a:
            c=combo(r.get('actual_combo'));p2[c[1]]+=1;p3[c[2]]+=1;ppair[(c[1],c[2])]+=1
        for r in b:
            c=combo(r.get('actual_combo'));q2[c[1]]+=1;q3[c[2]]+=1;qpair[(c[1],c[2])]+=1
        np2,np3,nq2,nq3=norm(p2),norm(p3),norm(q2),norm(q3)
        rows.append({
            'venue':v,'venue_name':VENUE_NAMES.get(v,''),'pre_head3_R':len(a),'oos_head3_R':len(b),
            'pre_2nd_inner12':100*share(p2,[1,2]),'oos_2nd_inner12':100*share(q2,[1,2]),
            'pre_2nd_outer456':100*share(p2,[4,5,6]),'oos_2nd_outer456':100*share(q2,[4,5,6]),
            'pre_3rd_inner12':100*share(p3,[1,2]),'oos_3rd_inner12':100*share(q3,[1,2]),
            'pre_3rd_outer456':100*share(p3,[4,5,6]),'oos_3rd_outer456':100*share(q3,[4,5,6]),
            'pre_top_2nd':top_lane(np2),'oos_top_2nd':top_lane(nq2),'pre_top_3rd':top_lane(np3),'oos_top_3rd':top_lane(nq3),
            'second_tv':100*tv(np2,nq2) if a and b else '', 'third_tv':100*tv(np3,nq3) if a and b else '',
            'pre_2nd_dist':' '.join(f'{k}:{p2[k]}' for k in OPP),'oos_2nd_dist':' '.join(f'{k}:{q2[k]}' for k in OPP),
            'pre_3rd_dist':' '.join(f'{k}:{p3[k]}' for k in OPP),'oos_3rd_dist':' '.join(f'{k}:{q3[k]}' for k in OPP),
            'pre_top_pairs':' '.join(f'{s}-{t}:{n}' for (s,t),n in ppair.most_common(5)),
            'oos_top_pairs':' '.join(f'{s}-{t}:{n}' for (s,t),n in qpair.most_common(5)),
        })
    fields=list(rows[0].keys())
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

    elig=[r for r in rows if r['pre_head3_R']>=20 and r['oos_head3_R']>=3]
    top2_match=sum(1 for r in elig if r['pre_top_2nd']==r['oos_top_2nd'])
    top3_match=sum(1 for r in elig if r['pre_top_3rd']==r['oos_top_3rd'])
    avg2=sum(float(r['second_tv']) for r in elig)/len(elig) if elig else 0
    avg3=sum(float(r['third_tv']) for r in elig)/len(elig) if elig else 0

    L=['# v172 ③1着時の場別・2着3着展開 OOS診断','',
       '- 条件は実際に③が1着になったレースのみ。','- 場別傾向は2026-05-31以前だけで作成し、2026-06〜08でOOS確認。','- Jun-Augから場ルールを作らない。場除外・再調整もしない。','',
       f'- PRE③頭レース: {len(pre)} / OOS③頭レース: {len(oos)}',
       f'- 十分な比較対象（PRE>=20, OOS>=3）: {len(elig)}場',
       f'- 2着最多艇の一致: {top2_match}/{len(elig) if elig else 0}',
       f'- 3着最多艇の一致: {top3_match}/{len(elig) if elig else 0}',
       f'- 平均TV距離 2着: {avg2:.1f}pt / 3着: {avg3:.1f}pt','',
       '## 場別','|場|PRE③頭|OOS③頭|PRE 2着内(1,2)|OOS 2着内|PRE 3着外(4,5,6)|OOS 3着外|2着TV|3着TV|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['pre_head3_R']<10 and r['oos_head3_R']==0: continue
        s2='-' if r['second_tv']=='' else f"{float(r['second_tv']):.1f}"
        s3='-' if r['third_tv']=='' else f"{float(r['third_tv']):.1f}"
        L.append(f"|{r['venue']} {r['venue_name']}|{r['pre_head3_R']}|{r['oos_head3_R']}|{r['pre_2nd_inner12']:.1f}%|{r['oos_2nd_inner12']:.1f}%|{r['pre_3rd_outer456']:.1f}%|{r['oos_3rd_outer456']:.1f}%|{s2}|{s3}|")
    L += ['','## 解釈','- 2着TV/3着TVが低いほど、PREで見えた着順分布がOOSでも近い。','- 2着内(1,2)は「③攻め後に内が残る」展開の粗い代理、3着外(4,5,6)は「外が連動する」展開の粗い代理。','- ここで再現性が確認できれば、次段階でv166 pairモデルに場×展開priorを追加してOOS比較する。','- 再現性が弱ければ、v171の場差はサンプル変動とみなし、場別補正は入れない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__': main()
