"""v97: 10-month second/third diagnostic for 3-head and 5-head models.

NO-LEAK
- Source is v90, whose candidate scores/ST strengths were frozen before outcomes.
- 3-head duplicates (3m/3ms same date+race+head) are deduped by PRE-RESULT score only.
- Opponent ranks are rebuilt from pre-race card/waku + current exhibition/original + prior-only corrected exhibition ST.
- All ranks are frozen before official 1st/2nd/3rd results are joined.
"""
from __future__ import annotations
import csv
from collections import Counter, defaultdict

from backtest import rows, race_features, grade_score, clamp, pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct

SRC='analysis_v90_exhibition_st_10month.csv'
OUT='analysis_v97_3head5head_second_third.csv'
SUMMARY='summary_v97_3head5head_second_third.md'
START='2025-11-01'; END='2026-08-31'; A=55.0; S=67.0
GROUPS={'3HEAD':{'models':('3まくり','3まくり差し'),'head':3},'5HEAD':{'models':('5頭展開',),'head':5}}
OUTCOME={'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit','payout100','winner','second','third','actual_trifecta','actual_ticket_rank20','actual_ticket_rank6','actual_combo','kimarite'}

def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='':return d
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
    q=clamp((z['wr']-3.0)/5.0);loc=clamp((z['local']-2.5)/5.5);ww=clamp(z['waku_wr']/8.0)
    nst=clamp((.24-z['nst'])/.14)
    direct=.35*ex[b]+.20*st[b]+.25*os[b]['turn']+.20*os[b]['avg']
    total=.16*grade_score(z['grade'])+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct
    return total,{'grade':grade_score(z['grade']),'national':q,'local':loc,'motor':motor,'waku':ww,'nst':nst,'direct':direct}

def group_of(r):
    m=r.get('model','')
    if m in GROUPS['3HEAD']['models']:return '3HEAD'
    if m in GROUPS['5HEAD']['models']:return '5HEAD'
    return ''

def dedupe_source(src):
    """Pre-result-only dedupe: 3m/3ms overlap -> larger frozen score."""
    best={}
    for idx,r in enumerate(src):
        ds=r.get('date','');g=group_of(r)
        if not g or not (START<=ds<=END):continue
        key=(ds,r.get('race_code',''),g)
        s=ff(r.get('score'),-999)
        if key not in best or s>best[key][0]:best[key]=(s,idx,r)
    return [v[2] for v in sorted(best.values(),key=lambda z:(z[2].get('date',''),z[2].get('race_code',''),z[2].get('model','')))]

def main():
    src=dedupe_source(read_csv(SRC))
    byday=defaultdict(list);outcomes={}
    for idx,r in enumerate(src):
        g=group_of(r);key=(r.get('date',''),r.get('race_code',''),g,idx)
        p={k:v for k,v in r.items() if k not in OUTCOME};p['_key']=key;p['group_v97']=g;p['head_v97']=GROUPS[g]['head']
        byday[p['date']].append(p);outcomes[key]={k:r.get(k,'') for k in OUTCOME if k in r}

    frozen=[]
    for ds in sorted(byday):
        ymd=ds.replace('-','/')
        tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'));cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv'));w10=bycode(rows(f'data/programs/waku10/{ymd}.csv'))
        for p in byday[ds]:
            z=dict(p);code=z.get('race_code','');head=ii(z.get('head_v97'));card=cards.get(code,{})
            if not card:continue
            x=race_features(card,w10.get(code,{}))
            if not x:continue
            ex,_d,os=corrected_direct(code,tkz,stt,orig,{b:0.0 for b in range(1,7)})
            for b in range(1,7):
                ex.setdefault(b,.5);os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
                for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
            st={b:ff(z.get(f'st_corr_strength_b{b}'),.5) for b in range(1,7)}
            others=[b for b in range(1,7) if b!=head];scored=[]
            for b in others:
                sc,parts=opp_score(x,b,ex,st,os);scored.append((b,sc,parts));z[f'opp_score_b{b}_v97']=round(sc,6)
                for k,v in parts.items():z[f'opp_{k}_b{b}_v97']=round(v,6)
            scored.sort(key=lambda t:t[1],reverse=True);ranked=[b for b,_,_ in scored]
            z['ranked_others_v97']='-'.join(map(str,ranked))
            frozen.append(z)

    result_maps={ds:bycode(rows(f'data/results/realtime/{ds.replace("-","/")}.csv')) for ds in sorted(byday)}
    final=[]
    for z in frozen:
        key=z.pop('_key');z.update(outcomes.get(key,{}));rr=result_maps.get(z.get('date',''),{}).get(z.get('race_code',''),{})
        if rr:
            z['winner']=rr.get('1着_艇番','');z['second']=rr.get('2着_艇番','');z['third']=rr.get('3着_艇番','');z['result_join_v97']='official_realtime'
        else:z['result_join_v97']='missing'
        ranked=[ii(x) for x in z.get('ranked_others_v97','').split('-') if x];sec=ii(z.get('second'));third=ii(z.get('third'))
        z['actual_second_rank_v97']=ranked.index(sec)+1 if sec in ranked else 0;z['actual_third_rank_v97']=ranked.index(third)+1 if third in ranked else 0
        final.append(z)

    if final:
        fs=sorted(set().union(*(r.keys() for r in final)))
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(final)

    L=['# v97 3頭・5頭 2着/3着 10か月診断','',
       '- 3頭は3まくり/3まくり差し重複を、結果前に凍結済みscoreの高い方だけ残して集計。',
       '- 相手順位は現行v51式をprior-only補正展示STで再構築し、順位凍結後に公式結果を結合。',
       f'- official result join: **{sum(r.get("result_join_v97")=="official_realtime" for r in final)}/{len(final)}**','']
    L+=['## 頭的中時の現行相手順位カバー','',
        '|対象|級|頭1着R|2着Top1|Top2|Top3|3着Top1|Top2|Top3|Top4|2Top2×3Top3|×Top4|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in ('3HEAD','5HEAD'):
        head=GROUPS[g]['head']
        for label,cut in (('A',A),('S',S)):
            q=[r for r in final if r.get('group_v97')==g and ii(r.get('entry_gate_keep'))==1 and ff(r.get('score'),-999)>=cut and ii(r.get('winner'))==head]
            sr=[ii(r.get('actual_second_rank_v97')) for r in q];tr=[ii(r.get('actual_third_rank_v97')) for r in q];n=len(q)
            cov=lambda arr,k:pct(sum(1 for x in arr if 1<=x<=k),len(arr))
            p3=pct(sum(1 for r in q if 1<=ii(r.get('actual_second_rank_v97'))<=2 and 1<=ii(r.get('actual_third_rank_v97'))<=3),n)
            p4=pct(sum(1 for r in q if 1<=ii(r.get('actual_second_rank_v97'))<=2 and 1<=ii(r.get('actual_third_rank_v97'))<=4),n)
            L.append(f'|{g}|{label}|{n}|{cov(sr,1):.1f}%|{cov(sr,2):.1f}%|{cov(sr,3):.1f}%|{cov(tr,1):.1f}%|{cov(tr,2):.1f}%|{cov(tr,3):.1f}%|{cov(tr,4):.1f}%|{p3:.1f}%|{p4:.1f}%|')

    L+=['','## 艇番分布（A・頭的中）','']
    for g in ('3HEAD','5HEAD'):
        head=GROUPS[g]['head'];q=[r for r in final if r.get('group_v97')==g and ii(r.get('entry_gate_keep'))==1 and ff(r.get('score'),-999)>=A and ii(r.get('winner'))==head]
        c2=Counter(ii(r.get('second')) for r in q);c3=Counter(ii(r.get('third')) for r in q)
        L += [f'### {g}', '|艇|2着|3着|','|---:|---:|---:|']
        for b in range(1,7):
            if b==head:continue
            L.append(f'|{b}|{c2[b]} ({pct(c2[b],len(q)):.1f}%)|{c3[b]} ({pct(c3[b],len(q)):.1f}%)|')
        L.append('')

    L+=['## 3頭サブモデル参考','', '|モデル|級|頭1着R|2着Top2|3着Top3|','|---|---|---:|---:|---:|']
    for m in ('3まくり','3まくり差し'):
        for label,cut in (('A',A),('S',S)):
            q=[r for r in final if r.get('group_v97')=='3HEAD' and r.get('model')==m and ii(r.get('entry_gate_keep'))==1 and ff(r.get('score'),-999)>=cut and ii(r.get('winner'))==3]
            a=sum(1 for r in q if 1<=ii(r.get('actual_second_rank_v97'))<=2);b=sum(1 for r in q if 1<=ii(r.get('actual_third_rank_v97'))<=3)
            L.append(f'|{m}|{label}|{len(q)}|{pct(a,len(q)):.1f}%|{pct(b,len(q)):.1f}%|')
    L+=['','## 次段階','- v97は診断のみ。結果を見てproduction相手順位は変更しない。',
        '- 次は3HEAD/5HEADごとに、現行相手点を主軸にした保守型2着/3着役割補正を時系列分離で検証する。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
