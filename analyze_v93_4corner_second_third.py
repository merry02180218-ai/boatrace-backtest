"""v93: 10-month 4-corner second/third place diagnostic.

Purpose
- Validate the CURRENT opponent ranking separately for actual 2nd and 3rd when boat 4 wins.
- Compare BASE vs v91 CORR20 selections at A/S thresholds.
- Measure coverage of the historical reduced-ticket shapes (2nd top2 x 3rd top3/4/5).

NO-LEAK
- Selection scores come from v91, already frozen before outcomes.
- Opponent ranking is rebuilt only from pre-race card/waku + current exhibition/original + v90 prior-only corrected ST strengths.
- Outcome columns are stripped before ranking is frozen and rejoined only after all rows are ranked.
"""
from __future__ import annotations
import csv
from collections import Counter, defaultdict
from datetime import date
from statistics import mean, median

from backtest import rows, race_features, grade_score, clamp, pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct

SRC='analysis_v91_st_weight_walkforward.csv'
OUT='analysis_v93_4corner_second_third.csv'
SUMMARY='summary_v93_4corner_second_third.md'
START='2025-11-01'; END='2026-08-31'; A=55.0; S=67.0
OUTCOME={'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit','payout100','winner','second','third','actual_trifecta','actual_ticket_rank20','actual_ticket_rank6','actual_combo','kimarite'}

def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def opp_score(x,b,ex,st,os):
    z=x[b]
    motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
    q=clamp((z['wr']-3.0)/5.0); loc=clamp((z['local']-2.5)/5.5); ww=clamp(z['waku_wr']/8.0)
    nst=clamp((.24-z['nst'])/.14)
    direct=.35*ex[b]+.20*st[b]+.25*os[b]['turn']+.20*os[b]['avg']
    total=.16*grade_score(z['grade'])+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct
    return total, {'grade':grade_score(z['grade']),'national':q,'local':loc,'motor':motor,'waku':ww,'nst':nst,'direct':direct}

def pair_rank(ranked,sec,third):
    pairs=[(a,b) for a in ranked for b in ranked if b!=a]
    try:return pairs.index((sec,third))+1
    except ValueError:return 0

def sel(r,name):
    if name=='BASE_A':return ff(r.get('score_BASE_v91'),-999)>=A
    if name=='CORR20_A':return ff(r.get('score_CORR20_v91'),-999)>=A
    if name=='BASE_S':return ff(r.get('score_BASE_v91'),-999)>=S
    if name=='CORR20_S':return ff(r.get('score_CORR20_v91'),-999)>=S
    return False

def main():
    raw=[r for r in read_csv(SRC) if r.get('model')=='4カドまくり' and START<=r.get('date','')<=END]
    preds=[]; outcomes={}; byday=defaultdict(list)
    for idx,r in enumerate(raw):
        key=(r.get('date',''),r.get('race_code',''),idx)
        p={k:v for k,v in r.items() if k not in OUTCOME};p['_key']=key
        preds.append(p);byday[p['date']].append(p)
        outcomes[key]={k:r.get(k,'') for k in OUTCOME if k in r}

    frozen=[]
    for ds in sorted(byday):
        ymd=ds.replace('-','/')
        tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'))
        stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
        cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv'))
        w10=bycode(rows(f'data/programs/waku10/{ymd}.csv'))
        for p in byday[ds]:
            z=dict(p);code=z.get('race_code','')
            card=cards.get(code,{})
            if not card:continue
            x=race_features(card,w10.get(code,{}))
            if not x:continue
            ex,_dummy,os=corrected_direct(code,tkz,stt,orig,{b:0.0 for b in range(1,7)})
            st={b:ff(z.get(f'st_corr_strength_b{b}'),.5) for b in range(1,7)}
            scored=[]
            for b in (1,2,3,5,6):
                sc,parts=opp_score(x,b,ex,st,os); scored.append((b,sc,parts))
                z[f'opp_score_b{b}_v93']=round(sc,6)
                for k,v in parts.items():z[f'opp_{k}_b{b}_v93']=round(v,6)
            scored.sort(key=lambda t:t[1],reverse=True)
            ranked=[b for b,_,_ in scored]
            z['ranked_others_v93']='-'.join(map(str,ranked))
            for i,b in enumerate(ranked,1):z[f'rank_b{b}_v93']=i
            frozen.append(z)

    final=[]
    for z in frozen:
        key=z.pop('_key');z.update(outcomes.get(key,{}))
        sec=ii(z.get('second'));third=ii(z.get('third'))
        ranked=[ii(x) for x in z.get('ranked_others_v93','').split('-') if x]
        z['actual_second_rank_v93']= ranked.index(sec)+1 if sec in ranked else 0
        z['actual_third_rank_v93']= ranked.index(third)+1 if third in ranked else 0
        z['actual_pair_rank20_v93']=pair_rank(ranked,sec,third)
        final.append(z)

    if final:
        fs=sorted(set().union(*(r.keys() for r in final)))
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(final)

    L=['# v93 4カド 2着・3着 10か月検証','',
       '対象は4カドモデル。相手順位は現行v51式（級別/全国/当地/モーター/枠別/ST/直前展示）を、v90のprior-only枠補正展示STで再構築。結果は順位凍結後に結合。','']
    selections=['BASE_A','CORR20_A','BASE_S','CORR20_S']
    L+=['## 4号艇が実際に1着だった時の相手順位カバー','',
        '|選別|4頭1着R|2着Top1|2着Top2|2着Top3|3着Top1|3着Top2|3着Top3|3着Top4|2Top2×3Top3|×Top4|×Top5|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in selections:
        q=[r for r in final if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and sel(r,name) and ii(r.get('winner'))==4]
        n=len(q)
        sr=[ii(r.get('actual_second_rank_v93')) for r in q];tr=[ii(r.get('actual_third_rank_v93')) for r in q]
        def cov(arr,k):return pct(sum(1 for x in arr if 1<=x<=k),len(arr))
        pair=[]
        for k in (3,4,5):pair.append(pct(sum(1 for r in q if 1<=ii(r.get('actual_second_rank_v93'))<=2 and 1<=ii(r.get('actual_third_rank_v93'))<=k),n))
        L.append(f'|{name}|{n}|{cov(sr,1):.1f}%|{cov(sr,2):.1f}%|{cov(sr,3):.1f}%|{cov(tr,1):.1f}%|{cov(tr,2):.1f}%|{cov(tr,3):.1f}%|{cov(tr,4):.1f}%|{pair[0]:.1f}%|{pair[1]:.1f}%|{pair[2]:.1f}%|')

    for name in selections:
        q=[r for r in final if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and sel(r,name) and ii(r.get('winner'))==4]
        L+=['',f'## {name}: 実2着・実3着の艇番分布','',
            '|艇|2着|3着|','|---:|---:|---:|']
        c2=Counter(ii(r.get('second')) for r in q);c3=Counter(ii(r.get('third')) for r in q)
        for b in (1,2,3,5,6):L.append(f'|{b}|{c2[b]} ({pct(c2[b],len(q)):.1f}%)|{c3[b]} ({pct(c3[b],len(q)):.1f}%)|')

    L+=['','## CORR20 S: 現行順位の詳細','',
        '|順位|実2着頻度|実3着頻度|','|---:|---:|---:|']
    qs=[r for r in final if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and sel(r,'CORR20_S') and ii(r.get('winner'))==4]
    s2=Counter(ii(r.get('actual_second_rank_v93')) for r in qs);s3=Counter(ii(r.get('actual_third_rank_v93')) for r in qs)
    for k in range(1,6):L.append(f'|{k}|{s2[k]} ({pct(s2[k],len(qs)):.1f}%)|{s3[k]} ({pct(s3[k],len(qs)):.1f}%)|')

    L+=['','## 解釈ルール',
        '- 2着Top2が十分高い一方、3着が広く散るなら「2着は絞る・3着は広げる」現行思想を支持。',
        '- 2着と3着の順位分布が明確に異なる場合、次段階で2着用/3着用の重みを分離してwalk-forward検証する。',
        '- 本v93は診断のみ。ここで見た結果から即productionの相手重みは変更しない。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
