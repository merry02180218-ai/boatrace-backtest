"""v90: 10-month validation of exhibition start timing (展示ST).

Goals
1) Measure pure predictive relationship between exhibition-ST rank and race winner over all valid races.
2) Measure model-specific relationship for frozen v83 structural candidates.
3) Compare raw within-race ST rank vs the CURRENT prior-only boat-number/frame-bias corrected ST rank.
4) Check time stability (prior7 vs recent3) and where correction changes top-2 classification.

NO-LEAK
- Daily ST frame bias is computed only from STT rows strictly before the current date,
  matching the v74 update order (preload from 2025-10-01, then freeze day, then update state).
- All ST ranks/features for a day are frozen before that day's results are loaded.
- v83 outcome columns are joined/evaluated only after ST features are frozen.
- STT course/entry columns are NOT scoring features here; v83 entry_gate_keep is used only as
  the current operational eligibility filter for model-specific evaluation.

Caveat
- Older STT rows can be backfill-from-daily. They are result-independent, but exact T-10
  preservation is not always guaranteed. Snapshot-only recent-period checks are reported.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
from statistics import mean

from backtest import rows

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v90_exhibition_st_10month.csv'
SUMMARY='summary_v90_exhibition_st_10month.md'
PRELOAD=date(2025,10,1)
START=date(2025,11,1)
PRIOR_END=date(2026,5,31)
RECENT_START=date(2026,6,1)
END=date(2026,8,31)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
VENUE={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}
OUTCOME_FIELDS={'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit','payout100','winner','second','third','actual_trifecta','actual_ticket_rank20','actual_ticket_rank6','actual_combo','kimarite'}


def ff(x,default=None):
    try:
        if x is None or str(x).strip()=='': return default
        return float(x)
    except Exception:return default

def ii(x,default=0):
    try:return int(float(x))
    except Exception:return default

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,rs):
    if not rs:return
    fields=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def source_type(v):
    s=(v or '').strip()
    if not s:return 'missing'
    if s.startswith('backfill'):return 'backfill'
    return 'snapshot'

def period(ds):
    d=date.fromisoformat(ds)
    return 'prior7' if d<=PRIOR_END else 'recent3'

def st_bias(sums,allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def update_st(strows,sums,allv):
    for r in strows:
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:
                sums[b].append(v);allv.append(v)

def rank_maps(sr,bias):
    raw={};corr={}
    for b in range(1,7):
        v=ff(sr.get(f'艇{b}_スタート展示'))
        if v is not None and -.30<v<1.0:
            raw[b]=v;corr[b]=v-bias.get(b,0.0)
        else:
            raw[b]=None;corr[b]=None
    def make(vals):
        a=[(b,v) for b,v in vals.items() if v is not None]
        a.sort(key=lambda z:(z[1],z[0]))
        n=len(a)
        rank={b:j+1 for j,(b,_) in enumerate(a)}
        strength={b:(1-j/(n-1) if n>=2 else .5) for j,(b,_) in enumerate(a)}
        return rank,strength
    rr,rs=make(raw);cr,cs=make(corr)
    return raw,corr,rr,rs,cr,cs

def rank_bucket(rank):
    if not rank:return 'missing'
    if rank==1:return '1位'
    if rank==2:return '2位'
    if rank<=4:return '3-4位'
    return '5-6位'

def auc(pairs):
    q=[(float(s),int(y)) for s,y in pairs if s is not None and y in (0,1)]
    pos=sum(y for _,y in q);neg=len(q)-pos
    if not pos or not neg:return None
    q.sort(key=lambda z:z[0])
    rank_sum=0.0;i=0
    while i<len(q):
        j=i+1
        while j<len(q) and q[j][0]==q[i][0]:j+=1
        avg_rank=(i+1+j)/2.0
        rank_sum+=avg_rank*sum(q[k][1] for k in range(i,j))
        i=j
    return (rank_sum-pos*(pos+1)/2)/(pos*neg)

def fmt_auc(x):return '-' if x is None else f'{x:.3f}'

def model_roles(m):
    if m=='5頭展開':return [('4号艇攻撃',4),('5号艇追走',5),('4+5合成',0)]
    return [('対象艇',HEAD[m])]

def combined5(raw_strength,corr_strength):
    # Normalize the actual v64/v74 ST contribution weights inside 5-head direct score:
    # .43*.38 for boat4 + .52*.17 for boat5.
    w4=.43*.38;w5=.52*.17;den=w4+w5
    r=None;c=None
    if 4 in raw_strength and 5 in raw_strength:r=(w4*raw_strength[4]+w5*raw_strength[5])/den
    if 4 in corr_strength and 5 in corr_strength:c=(w4*corr_strength[4]+w5*corr_strength[5])/den
    return r,c

def main():
    src=read_csv(SRC)
    pred=[];outcomes={}
    byday=defaultdict(list)
    for idx,r in enumerate(src):
        ds=r.get('date','')
        if not (START.isoformat()<=ds<=END.isoformat()):continue
        key=(ds,r.get('race_code',''),r.get('model',''),r.get('head',''),idx)
        p={k:v for k,v in r.items() if k not in OUTCOME_FIELDS};p['_key']=key
        pred.append(p);byday[ds].append(p)
        outcomes[key]={k:r.get(k,'') for k in OUTCOME_FIELDS if k in r}

    sums=defaultdict(list);allv=[]
    model_frozen=[]
    pure_rank=defaultdict(lambda:Counter())
    pure_boat=defaultdict(lambda:Counter())
    pure_auc_raw=[];pure_auc_corr=[]
    missing_result_dates=[]

    d=PRELOAD
    while d<=END:
        ymd=d.strftime('%Y/%m/%d');ds=d.isoformat()
        strows=rows(f'data/previews/stt/{ymd}.csv');stmap=bycode(strows)
        bias=st_bias(sums,allv)

        if d>=START:
            # Freeze model-candidate ST features before loading outcomes.
            for p in byday.get(ds,[]):
                z=dict(p);code=z.get('race_code','');m=z.get('model','');sr=stmap.get(code,{})
                raw,corr,rr,rs,cr,cs=rank_maps(sr,bias)
                z['st_source_v90']=source_type(sr.get('取得日時'))
                z['st_bias1_v90']=round(bias[1],6);z['st_bias2_v90']=round(bias[2],6);z['st_bias3_v90']=round(bias[3],6)
                z['st_bias4_v90']=round(bias[4],6);z['st_bias5_v90']=round(bias[5],6);z['st_bias6_v90']=round(bias[6],6)
                for b in range(1,7):
                    z[f'st_raw_b{b}']= '' if raw[b] is None else raw[b]
                    z[f'st_raw_rank_b{b}']=rr.get(b,0);z[f'st_corr_rank_b{b}']=cr.get(b,0)
                    z[f'st_raw_strength_b{b}']=round(rs.get(b,.5),4);z[f'st_corr_strength_b{b}']=round(cs.get(b,.5),4)
                if m=='5頭展開':
                    r5,c5=combined5(rs,cs);z['st5_combo_raw_v90']='' if r5 is None else round(r5,4);z['st5_combo_corr_v90']='' if c5 is None else round(c5,4)
                z['period_v90']=period(ds)
                model_frozen.append(z)

            # Freeze pure all-race ST ranks, then load results.
            frozen_pure=[]
            for code,sr in stmap.items():
                raw,corr,rr,rs,cr,cs=rank_maps(sr,bias)
                frozen_pure.append((code,rr,rs,cr,cs))
            res=bycode(rows(f'data/results/realtime/{ymd}.csv'))
            if not res:missing_result_dates.append(ds)
            for code,rr,rs,cr,cs in frozen_pure:
                win=ii(res.get(code,{}).get('1着_艇番'))
                if win not in range(1,7):continue
                for b in range(1,7):
                    if b not in rr or b not in cr:continue
                    y=int(b==win)
                    pure_rank[('raw',rr[b])]['n']+=1;pure_rank[('raw',rr[b])]['win']+=y
                    pure_rank[('corr',cr[b])]['n']+=1;pure_rank[('corr',cr[b])]['win']+=y
                    pure_boat[(b,'all')]['n']+=1;pure_boat[(b,'all')]['win']+=y
                    if cr[b]<=2:
                        pure_boat[(b,'top2')]['n']+=1;pure_boat[(b,'top2')]['win']+=y
                    else:
                        pure_boat[(b,'not_top2')]['n']+=1;pure_boat[(b,'not_top2')]['win']+=y
                    pure_auc_raw.append((rs[b],y));pure_auc_corr.append((cs[b],y))

        # Only after the day's ST features/results comparison is frozen, update bias for future days.
        update_st(strows,sums,allv)
        if d.day==1:print('v90 through',ds,'prior ST obs',len(allv),flush=True)
        d+=timedelta(days=1)

    # Join candidate outcomes only after all ST features are frozen.
    final=[]
    for z in model_frozen:
        key=z.pop('_key');z.update(outcomes.get(key,{}));final.append(z)
    write_csv(OUT,final)

    def valid(r):return ii(r.get('valid_result'))==1 and ii(r.get('entry_gate_keep'))==1
    def outcome(r,kind):return ii(r.get('route_hit' if kind=='route' else 'head_hit'))
    def role_strength(r,m,role,use_corr):
        pref='st_corr_strength_b' if use_corr else 'st_raw_strength_b'
        if role=='4+5合成':return ff(r.get('st5_combo_corr_v90' if use_corr else 'st5_combo_raw_v90'))
        b=dict(model_roles(m))[role];return ff(r.get(pref+str(b)))
    def role_rank(r,m,role,use_corr=True):
        if role=='4+5合成':return 0
        b=dict(model_roles(m))[role];return ii(r.get(('st_corr_rank_b' if use_corr else 'st_raw_rank_b')+str(b)))

    L=['# v90 展示ST 10か月検証','',f'期間: **{START}〜{END}**。現行v74と同じ順序で、各日の展示ST枠/艇番バイアスは前日までのSTTだけから計算。','',
       '## 1. 全レース：展示ST順位と1着率','',
       f'- 全艇観測 AUC: raw **{fmt_auc(auc(pure_auc_raw))}** / 枠補正後 **{fmt_auc(auc(pure_auc_corr))}**（0.5=識別なし、1.0=完全）。','',
       '|順位|raw 1着率|補正後 1着率|','|---:|---:|---:|']
    for rk in range(1,7):
        a=pure_rank[('raw',rk)];c=pure_rank[('corr',rk)]
        L.append(f"|{rk}|{pct(a['win'],a['n']):.2f}% ({a['n']:,})|{pct(c['win'],c['n']):.2f}% ({c['n']:,})|")

    L+=['','### 艇番別：補正後展示ST Top2の1着率','|艇|全体|Top2|非Top2|Top2差|','|---:|---:|---:|---:|---:|']
    for b in range(1,7):
        a=pure_boat[(b,'all')];t=pure_boat[(b,'top2')];n=pure_boat[(b,'not_top2')]
        ar=pct(a['win'],a['n']);tr=pct(t['win'],t['n']);nr=pct(n['win'],n['n'])
        L.append(f'|{b}|{ar:.2f}%|{tr:.2f}%|{nr:.2f}%|{tr-nr:+.2f}pt|')

    L+=['','## 2. 現行モデル候補：raw vs 枠補正後STの識別力','',
        '対象はv83/v74で結果を見る前に固定済みの構造候補。展示進入changedは現行ルールどおり除外。','',
        '|モデル|ST役割|R|頭AUC raw|頭AUC 補正|ルートAUC raw|ルートAUC 補正|','|---|---|---:|---:|---:|---:|---:|']
    for m in MODELS:
        q=[r for r in final if valid(r) and r.get('model')==m]
        for role,_b in model_roles(m):
            hp_raw=[(role_strength(r,m,role,False),outcome(r,'head')) for r in q]
            hp_cor=[(role_strength(r,m,role,True),outcome(r,'head')) for r in q]
            rt_raw=[(role_strength(r,m,role,False),outcome(r,'route')) for r in q]
            rt_cor=[(role_strength(r,m,role,True),outcome(r,'route')) for r in q]
            L.append(f'|{m}|{role}|{len(q)}|{fmt_auc(auc(hp_raw))}|{fmt_auc(auc(hp_cor))}|{fmt_auc(auc(rt_raw))}|{fmt_auc(auc(rt_cor))}|')

    L+=['','## 3. モデル別：補正後展示ST順位と成績','']
    for m in MODELS:
        q=[r for r in final if valid(r) and r.get('model')==m]
        for role,_b in model_roles(m):
            if role=='4+5合成':continue
            L += [f'### {m} / {role}','|ST順位帯|R|頭率|ルート率|','|---|---:|---:|---:|']
            for bucket in ('1位','2位','3-4位','5-6位'):
                a=[r for r in q if rank_bucket(role_rank(r,m,role,True))==bucket]
                L.append(f"|{bucket}|{len(a)}|{pct(sum(outcome(r,'head') for r in a),len(a)):.1f}%|{pct(sum(outcome(r,'route') for r in a),len(a)):.1f}%|")
            L.append('')

    L+=['## 4. 時系列安定性：補正後ST Top2 vs 非Top2','|モデル|役割|期間|Top2 R|Top2頭率|非Top2頭率|頭率差|Top2ルート率|非Top2ルート率|ルート差|','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        for role,_b in model_roles(m):
            if role=='4+5合成':continue
            for per in ('prior7','recent3'):
                q=[r for r in final if valid(r) and r.get('model')==m and r.get('period_v90')==per]
                t=[r for r in q if 0<role_rank(r,m,role,True)<=2];n=[r for r in q if role_rank(r,m,role,True)>2]
                th=pct(sum(outcome(r,'head') for r in t),len(t));nh=pct(sum(outcome(r,'head') for r in n),len(n))
                tr=pct(sum(outcome(r,'route') for r in t),len(t));nr=pct(sum(outcome(r,'route') for r in n),len(n))
                L.append(f'|{m}|{role}|{per}|{len(t)}|{th:.1f}%|{nh:.1f}%|{th-nh:+.1f}pt|{tr:.1f}%|{nr:.1f}%|{tr-nr:+.1f}pt|')

    L+=['','## 5. 枠補正でTop2判定が変わったケース','|モデル|役割|区分|R|頭率|ルート率|','|---|---|---|---:|---:|---:|']
    for m in MODELS:
        for role,_b in model_roles(m):
            if role=='4+5合成':continue
            q=[r for r in final if valid(r) and r.get('model')==m]
            promoted=[];demoted=[]
            for r in q:
                rr=role_rank(r,m,role,False);cr=role_rank(r,m,role,True)
                if rr>2 and 0<cr<=2:promoted.append(r)
                if 0<rr<=2 and cr>2:demoted.append(r)
            for lab,a in [('補正でTop2昇格',promoted),('補正でTop2降格',demoted)]:
                L.append(f"|{m}|{role}|{lab}|{len(a)}|{pct(sum(outcome(r,'head') for r in a),len(a)):.1f}%|{pct(sum(outcome(r,'route') for r in a),len(a)):.1f}%|")

    # Snapshot-only recent3 check for strictest source quality.
    L+=['','## 6. snapshot-only 直近3か月','|モデル|役割|Top2 R|Top2頭率|非Top2頭率|頭率差|Top2ルート率|非Top2ルート率|','|---|---|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        for role,_b in model_roles(m):
            if role=='4+5合成':continue
            q=[r for r in final if valid(r) and r.get('model')==m and r.get('period_v90')=='recent3' and r.get('st_source_v90')=='snapshot']
            t=[r for r in q if 0<role_rank(r,m,role,True)<=2];n=[r for r in q if role_rank(r,m,role,True)>2]
            th=pct(sum(outcome(r,'head') for r in t),len(t));nh=pct(sum(outcome(r,'head') for r in n),len(n));tr=pct(sum(outcome(r,'route') for r in t),len(t));nr=pct(sum(outcome(r,'route') for r in n),len(n))
            L.append(f'|{m}|{role}|{len(t)}|{th:.1f}%|{nh:.1f}%|{th-nh:+.1f}pt|{tr:.1f}%|{nr:.1f}%|')

    L+=['','## 判定方針','- まず「展示STが強いほど頭/ルート率が概ね上がるか」を確認。',
        '- raw AUCより枠補正後AUCが高ければ、現行の艇番/枠バイアス補正を支持。',
        '- 3まくり/4カドはルート率も重視。5頭は4号艇攻撃STと5号艇追走STを別々に評価。',
        '- A/Sは既にSTを含むため主検証には使わず、構造候補全体を主母集団とする。',
        '- このv90は診断であり、ST重み変更は別walk-forwardで検証するまでproductionへ反映しない。']
    if missing_result_dates:L+=['', '結果欠損日: '+', '.join(sorted(set(missing_result_dates)))]
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('v90 done model rows',len(final),'pure observations',sum(c['n'] for (typ,_),c in pure_rank.items() if typ=='corr'),flush=True)

if __name__=='__main__':main()
