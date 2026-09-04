"""v89: strict prior-only 4-corner venue-strength x wind interaction walk-forward.

Base:
- frozen v83/v74 candidates
- v88 prior-only venue 4-course attack adjustment already frozen for each day

Interaction design (fixed before evaluation):
1) classify venue each day from v88's PRIOR-ONLY shrunk 4-course attack-rate edge:
   strong >= +1.0 percentage point, weak <= -1.0pt, otherwise neutral.
2) learn 4-corner candidate head rate by venue-strength bucket x relative-wind x speed,
   using only completed candidate outcomes from previous days in a trailing 180-day window.
3) shrink each cell toward its venue-bucket baseline (alpha=30 candidates).
4) require cell n>=20 and bucket n>=60; otherwise wind adjustment is neutral.
5) wind interaction adjustment = clip((shrunk_cell_rate-bucket_rate)*20, -1.5,+1.5).
   Thus a 5 percentage-point interaction lift is +1 score point.
6) score_v89 = score_v88 + interaction adjustment.

NO LEAK:
- current-day outcomes are separated from prediction rows.
- all score_v89 values for a date are frozen first.
- only after that are current-day outcomes added for future dates.
"""
from __future__ import annotations
import csv
from collections import Counter, defaultdict, deque
from datetime import date, timedelta

SRC='analysis_v88_venue_dash_walkforward.csv'
OUT='analysis_v89_4corner_venue_wind_walkforward.csv'
SUMMARY='summary_v89_4corner_venue_wind_walkforward.md'
START=date(2025,11,1); END=date(2026,8,31)
PRIOR_END=date(2026,5,31); RECENT_START=date(2026,6,1)
LOOKBACK_DAYS=180
BUCKET_EDGE_PT=1.0
CELL_ALPHA=30.0
MIN_CELL_N=20
MIN_BUCKET_N=60
WIND_SCALE=20.0
MAX_WIND_POINTS=1.5
A_CUT=55.0; S_CUT=67.0
MODEL='4カドまくり'
OUTCOME_FIELDS={'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit','payout100','winner','second','third','actual_trifecta','actual_ticket_rank20','actual_ticket_rank6'}

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except:return d

def pct(n,d):return 100*n/d if d else 0.0

def clip(x,a,b):return max(a,min(b,x))

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def period_of(ds):
    d=date.fromisoformat(ds)
    if START<=d<=PRIOR_END:return 'prior7'
    if RECENT_START<=d<=END:return 'recent3'
    return 'outside'

def venue_bucket(r):
    edge=ff(r.get('venue_dash_diff_pt_v88'),0.0)
    if edge>=BUCKET_EDGE_PT:return 'strong'
    if edge<=-BUCKET_EDGE_PT:return 'weak'
    return 'neutral'

def wind_cell(r):
    w=(r.get('wind_cell') or '').strip()
    return w if w and w!='missing' else 'missing'

def split_source(src):
    preds=[]; outcomes={}
    for idx,r in enumerate(src):
        if r.get('model')!=MODEL:continue
        key=(r.get('date',''),r.get('race_code',''),idx)
        p={k:v for k,v in r.items() if k not in OUTCOME_FIELDS}
        p['_v89_key']=key
        preds.append(p)
        outcomes[key]={k:r.get(k,'') for k in OUTCOME_FIELDS if k in r}
    return preds,outcomes

def add_stat(bucket_stats,cell_stats,b,c,hit,sign=1):
    bucket_stats[b]['n']+=sign;bucket_stats[b]['h']+=sign*hit
    if c!='missing':
        cell_stats[(b,c)]['n']+=sign;cell_stats[(b,c)]['h']+=sign*hit

def interaction_adjust(b,c,bucket_stats,cell_stats):
    bn=bucket_stats[b]['n']; bh=bucket_stats[b]['h']
    cn=cell_stats[(b,c)]['n'] if c!='missing' else 0
    ch=cell_stats[(b,c)]['h'] if c!='missing' else 0
    if c=='missing' or bn<MIN_BUCKET_N or cn<MIN_CELL_N:
        return 0.0,bn,cn,(bh/bn if bn else 0.0),0.0,0.0
    br=bh/bn
    shr=(ch+CELL_ALPHA*br)/(cn+CELL_ALPHA)
    lift=shr-br
    adj=clip(lift*WIND_SCALE,-MAX_WIND_POINTS,MAX_WIND_POINTS)
    return adj,bn,cn,br,shr,lift

def valid_result(r):return ii(r.get('valid_result'))==1

def valid_payout(r):return ii(r.get('valid_payout'))==1

def kept(r):return ii(r.get('entry_gate_keep'))==1

def score0(r):return ff(r.get('score'),0.0)

def score88(r):return ff(r.get('score_v88'),score0(r))

def score89(r):return ff(r.get('score_v89'),score88(r))

def metrics(rs):
    q=[r for r in rs if valid_result(r)]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q);rh=sum(ii(r.get('route_hit')) for r in q)
    p=[r for r in q if valid_payout(r)];inv=2000*len(p)
    ret=sum(ii(r.get('payout100')) for r in p if ii(r.get('ticket20_hit'))==1)
    return n,h,pct(h,n),pct(rh,n),pct(ret,inv)

def fmt(m):
    n,h,hr,rr,roi=m
    return f'{n}R / 頭{h} ({hr:.1f}%) / ルート{rr:.1f}% / 20点ROI {roi:.1f}%'

def selected(src,grade,which,per=None):
    cut=S_CUT if grade=='S' else A_CUT
    fn={'base':score0,'v88':score88,'v89':score89}[which]
    out=[]
    for r in src:
        if not kept(r):continue
        if per and period_of(r.get('date',''))!=per:continue
        if fn(r)>=cut:out.append(r)
    return out

def main():
    raw=read_csv(SRC);preds,outcomes=split_source(raw)
    byday=defaultdict(list)
    for p in preds:
        if START.isoformat()<=p.get('date','')<=END.isoformat():byday[p['date']].append(p)

    bucket_stats=defaultdict(Counter);cell_stats=defaultdict(Counter);history=deque();frozen=[]
    for d in (START+timedelta(days=i) for i in range((END-START).days+1)):
        cutoff=d-timedelta(days=LOOKBACK_DAYS)
        while history and history[0][0]<cutoff:
            _,items=history.popleft()
            for b,c,h in items:add_stat(bucket_stats,cell_stats,b,c,h,-1)

        ds=d.isoformat();today_meta=[]
        # freeze all current-day adjustments before reading current-day outcomes
        for p in byday.get(ds,[]):
            z=dict(p);b=venue_bucket(z);c=wind_cell(z)
            adj,bn,cn,br,shr,lift=interaction_adjust(b,c,bucket_stats,cell_stats)
            z['venue_strength_bucket_v89']=b
            z['wind_interaction_cell_v89']=f'{b}|{c}'
            z['wind_bucket_n_v89']=bn;z['wind_cell_n_v89']=cn
            z['wind_bucket_rate_v89']=round(br,6);z['wind_cell_shrunk_rate_v89']=round(shr,6)
            z['wind_interaction_lift_pt_v89']=round(lift*100,3)
            z['wind_interaction_adj_v89']=round(adj,3)
            z['score_v89']=round(score88(z)+adj,3)
            z['period_v89']=period_of(ds)
            frozen.append(z);today_meta.append((z['_v89_key'],b,c))

        # only now add today's outcomes for future dates
        hist_items=[]
        for key,b,c in today_meta:
            o=outcomes.get(key,{})
            if ii(o.get('valid_result'))!=1:continue
            hit=ii(o.get('head_hit'))
            add_stat(bucket_stats,cell_stats,b,c,hit,1);hist_items.append((b,c,hit))
        history.append((d,hist_items))
        if d.day==1:print('frozen through',ds,'hist',sum(x['n'] for x in bucket_stats.values()),flush=True)

    final=[]
    for z in frozen:
        key=z.pop('_v89_key');z.update(outcomes.get(key,{}));final.append(z)
    write_csv(OUT,final)

    L=['# v89 4カド：場強弱×風 prior-only walk-forward','',
       f'期間: **{START}〜{END}**。v88のprior-only場別4コース攻撃率を強/中立/弱へ3分類し、過去{LOOKBACK_DAYS}日の4カド候補だけで相対風向×風速との相互作用を学習。','',
       '## 固定ルール',
       f'- 場強: v88 prior-only攻撃率差 >= +{BUCKET_EDGE_PT:.1f}pt / 場弱 <= -{BUCKET_EDGE_PT:.1f}pt / その他中立。',
       f'- 風セル: 場3群 × relative wind(追い/右横/向かい/左横) × speed(0-2/3-4/5m+)。',
       f'- セルn>={MIN_CELL_N}, 場群n>={MIN_BUCKET_N}のみ使用。alpha={CELL_ALPHA:.0f}で場群平均へ縮約。',
       f'- 風相互作用補正=(縮約セル頭率-場群頭率)×{WIND_SCALE:.0f}、±{MAX_WIND_POINTS:.1f}点cap。',
       '- score_v89 = v88場補正済みscore + 風相互作用補正。展示進入changedは除外。',
       '- 当日結果は全score_v89固定後にのみ未来の履歴へ追加。','',
       '## Baseline / v88場補正 / v89場×風','|期間|評価|Baseline|v88|v89|v89-v88頭率|v89-v88 ROI|','|---|---|---|---|---|---:|---:|']
    for per in ('prior7','recent3',None):
        pl=per or '10mo'
        for g in ('A','S'):
            b=metrics(selected(final,g,'base',per));a=metrics(selected(final,g,'v88',per));w=metrics(selected(final,g,'v89',per))
            L.append(f'|{pl}|{g}+|{fmt(b)}|{fmt(a)}|{fmt(w)}|{w[2]-a[2]:+.2f}pt|{w[4]-a[4]:+.1f}pt|')

    L+=['','## v88→v89 閾値跨ぎ','|評価|区分|R|頭率|ルート率|20点ROI|','|---|---|---:|---:|---:|---:|']
    for g,cut in [('A',A_CUT),('S',S_CUT)]:
        promoted=[r for r in final if kept(r) and score88(r)<cut<=score89(r)]
        demoted=[r for r in final if kept(r) and score89(r)<cut<=score88(r)]
        for lab,rs in [('昇格',promoted),('降格',demoted)]:
            m=metrics(rs);L.append(f'|{g}+|{lab}|{m[0]}|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    L+=['','## 場群×風セル（実際に補正が発動したセル）','|場群|風セル|R|平均補正|頭率|','|---|---|---:|---:|---:|']
    cells=defaultdict(list)
    for r in final:
        if kept(r) and abs(ff(r.get('wind_interaction_adj_v89'),0))>1e-9:
            cells[(r.get('venue_strength_bucket_v89'),wind_cell(r))].append(r)
    for (b,c),rs in sorted(cells.items(),key=lambda kv:(kv[0][0],kv[0][1])):
        m=metrics(rs);avg=sum(ff(r.get('wind_interaction_adj_v89')) for r in rs)/len(rs)
        L.append(f'|{b}|{c}|{m[0]}|{avg:+.2f}|{m[2]:.1f}%|')

    # Conservative incremental signal vs v88.
    p88=metrics(selected(final,'A','v88','prior7'));p89=metrics(selected(final,'A','v89','prior7'))
    r88=metrics(selected(final,'A','v88','recent3'));r89=metrics(selected(final,'A','v89','recent3'))
    s88=metrics(selected(final,'S','v88','recent3'));s89=metrics(selected(final,'S','v89','recent3'))
    dp=p89[2]-p88[2];dr=r89[2]-r88[2];ds=s89[2]-s88[2]
    ok=(dr>=0.5 and dp>=-0.5 and ds>=0.0)
    L+=['','## 事前固定の採用シグナル',
        '- PASS条件: v88比で直近3か月A+頭率 +0.5pt以上、前半7か月A+ -0.5pt未満の悪化なし、直近S+頭率悪化なし。ROIは副指標。',
        f'- prior7 A差 {dp:+.2f}pt / recent3 A差 {dr:+.2f}pt / recent3 S差 {ds:+.2f}pt → **{"PASS" if ok else "FAIL"}**',
        '- PASSでもproduction即採用ではなく、閾値跨ぎ件数とセル安定性を確認してから判断する。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
