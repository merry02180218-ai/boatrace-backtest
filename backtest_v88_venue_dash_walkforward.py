"""v88: strict prior-only walk-forward test of venue dash tendency.

Question: do some venues structurally favor outside/dash attacks enough to improve the
current 4-corner and 5-head models?

NO-LEAK DESIGN
- Base candidates/scores are the already-frozen v83/v74 predictions.
- Venue tendencies are computed ONLY from race results strictly BEFORE each candidate date.
- Current-day results/payouts are not touched until all venue adjustments for that date are frozen.
- The venue adjustment formula is fixed before seeing v88 outcome comparisons; it is not optimized.

FIXED VENUE FEATURES
- 4カドまくり: trailing 180-day venue rate of winner coming from ACTUAL 4 course with
  kimarite in {まくり, まくり差し}, shrunk toward trailing-180d all-venue baseline.
- 5頭展開: trailing 180-day venue rate of winner coming from ACTUAL 5 course, shrunk
  toward trailing-180d all-venue baseline.
- denominator = all valid races at that venue in the trailing window, matching v87's
  descriptive rate definition.

FIXED SOFT SCORE MAPPING
- empirical-Bayes shrink alpha = 300 races
- minimum venue sample = 200 races, otherwise neutral
- adjustment = clip((shrunk_venue_rate - global_rate) * 50, -2, +2) score points
  (a +2 percentage-point venue edge => +1 score point)
- 3-head models remain unchanged.

Evaluation follows the current operational entry gate (entry_gate_keep==1) and compares
baseline score vs venue-adjusted score at A>=55 / S>=67. ROI is secondary because payout
variance is high; head-rate stability is the primary diagnostic.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict, deque
from datetime import date, timedelta

from backtest import rows

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v88_venue_dash_walkforward.csv'
SUMMARY='summary_v88_venue_dash_walkforward.md'
START=date(2025,11,1)
END=date(2026,8,31)
PRIOR_END=date(2026,5,31)
RECENT_START=date(2026,6,1)
LOOKBACK_DAYS=180
ALPHA=300.0
MIN_VENUE_N=200
SCALE=50.0
MAX_POINTS=2.0
A_CUT=55.0
S_CUT=67.0

VENUE={
 1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'
}
TARGET_MODELS={'4カドまくり':'4attack','5頭展開':'5head'}
OUTCOME_FIELDS={
    'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit',
    'payout100','winner','second','third','actual_trifecta','actual_ticket_rank20','actual_ticket_rank6'
}

def ii(x,default=0):
    try:return int(float(x))
    except Exception:return default

def ff(x,default=0.0):
    try:
        if x is None or str(x).strip()=='':return default
        return float(x)
    except Exception:return default

def pct(n,d):return 100*n/d if d else 0.0

def clip(x,a,b):return max(a,min(b,x))

def normkim(s):return (s or '').replace(' ','').replace('　','')

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,rs):
    if not rs:return
    fields=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)

def venue_from_code(code):
    s=str(code or '').strip()
    if len(s)>=10:
        return VENUE.get(ii(s[8:10]),'')
    return ''

def winner_course(rr):
    win=ii(rr.get('1着_艇番'))
    if win not in range(1,7):return 0
    for c in range(1,7):
        if ii(rr.get(f'{c}コース_艇番'))==win:return c
    return 0

def summarize_day(d):
    ymd=d.strftime('%Y/%m/%d')
    rr=rows(f'data/results/realtime/{ymd}.csv')
    g=Counter(); v=defaultdict(Counter)
    for r in rr:
        win=ii(r.get('1着_艇番'))
        if win not in range(1,7):continue
        venue=venue_from_code(r.get('レースコード')) or VENUE.get(ii(r.get('レース場')), '')
        if not venue:continue
        wc=winner_course(r); kim=normkim(r.get('決まり手'))
        e4=int(wc==4 and kim in ('まくり','まくり差し'))
        e5=int(wc==5)
        g['n']+=1;g['4attack']+=e4;g['5head']+=e5
        v[venue]['n']+=1;v[venue]['4attack']+=e4;v[venue]['5head']+=e5
    return {'date':d,'global':g,'venue':v}

def add_counter(dst,src,sign=1):
    for k,val in src.items():dst[k]+=sign*val

def venue_adjust(feature,venue,g,v):
    gn=g['n']; vn=v[venue]['n']
    if gn<=0 or vn<MIN_VENUE_N:return 0.0,0.0,0.0,vn
    gr=g[feature]/gn
    vr=v[venue][feature]/vn
    shr=(v[venue][feature]+ALPHA*gr)/(vn+ALPHA)
    adj=clip((shr-gr)*SCALE,-MAX_POINTS,MAX_POINTS)
    return adj,gr,shr,vn

def split_source(src):
    preds=[]; outcomes={}
    for idx,r in enumerate(src):
        key=(r.get('date',''),r.get('race_code',''),r.get('model',''),r.get('head',''),idx)
        p={k:v for k,v in r.items() if k not in OUTCOME_FIELDS}
        p['_v88_key']=key
        preds.append(p)
        outcomes[key]={k:r.get(k,'') for k in OUTCOME_FIELDS if k in r}
    return preds,outcomes

def period_of(ds):
    d=date.fromisoformat(ds)
    if START<=d<=PRIOR_END:return 'prior7'
    if RECENT_START<=d<=END:return 'recent3'
    return 'outside'

def valid_result(r):return ii(r.get('valid_result'))==1

def valid_payout(r):return ii(r.get('valid_payout'))==1

def kept(r):return ii(r.get('entry_gate_keep'))==1

def score_base(r):return ff(r.get('score'),0.0)

def score_adj(r):return ff(r.get('score_v88'),score_base(r))

def metrics(rs):
    q=[r for r in rs if valid_result(r)]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q);rh=sum(ii(r.get('route_hit')) for r in q)
    p=[r for r in q if valid_payout(r)]
    inv=2000*len(p)
    ret=sum(ii(r.get('payout100')) for r in p if ii(r.get('ticket20_hit'))==1)
    return n,h,pct(h,n),pct(rh,n),pct(ret,inv)

def fmt(m):
    n,h,hr,rr,roi=m
    return f'{n}R / 頭{h} ({hr:.1f}%) / ルート{rr:.1f}% / 20点ROI {roi:.1f}%'

def selected(src,model,grade,use_adj,period=None):
    cut=S_CUT if grade=='S' else A_CUT
    out=[]
    for r in src:
        if not kept(r):continue
        if r.get('model')!=model:continue
        if period and period_of(r.get('date',''))!=period:continue
        sc=score_adj(r) if use_adj else score_base(r)
        if sc>=cut:out.append(r)
    return out

def main():
    raw=read_csv(SRC)
    preds,outcomes=split_source(raw)
    byday=defaultdict(list)
    for p in preds:
        if START.isoformat()<=p.get('date','')<=END.isoformat():byday[p['date']].append(p)

    # Build a strictly-prior trailing window. Earliest history starts 180 days before START.
    q=deque(); g=Counter(); v=defaultdict(Counter)
    hist_start=START-timedelta(days=LOOKBACK_DAYS)
    d=hist_start
    while d<START:
        day=summarize_day(d);q.append(day);add_counter(g,day['global'])
        for venue,c in day['venue'].items():add_counter(v[venue],c)
        d+=timedelta(days=1)

    frozen=[]
    for d in (START+timedelta(days=i) for i in range((END-START).days+1)):
        # drop dates outside [d-180, d-1]
        cutoff=d-timedelta(days=LOOKBACK_DAYS)
        while q and q[0]['date']<cutoff:
            old=q.popleft();add_counter(g,old['global'],-1)
            for venue,c in old['venue'].items():add_counter(v[venue],c,-1)

        ds=d.isoformat()
        # Freeze all candidate adjustments BEFORE loading d's outcomes into the window.
        for p in byday.get(ds,[]):
            z=dict(p)
            model=z.get('model','');feature=TARGET_MODELS.get(model)
            venue=z.get('venue_v83') or venue_from_code(z.get('race_code'))
            adj=0.0;gr=0.0;shr=0.0;vn=0
            if feature:
                adj,gr,shr,vn=venue_adjust(feature,venue,g,v)
            base=score_base(z)
            z['venue_dash_feature_v88']=feature or 'neutral'
            z['venue_dash_window_days_v88']=LOOKBACK_DAYS
            z['venue_dash_venue_n_v88']=vn
            z['venue_dash_global_rate_v88']=round(gr,6)
            z['venue_dash_shrunk_rate_v88']=round(shr,6)
            z['venue_dash_diff_pt_v88']=round((shr-gr)*100,3) if feature else 0.0
            z['venue_dash_adj_v88']=round(adj,3)
            z['score_v88']=round(base+adj,3)
            z['period_v88']=period_of(ds)
            frozen.append(z)

        # ONLY AFTER freezing the day's candidates, add today's realized results for future dates.
        day=summarize_day(d);q.append(day);add_counter(g,day['global'])
        for venue,c in day['venue'].items():add_counter(v[venue],c)
        if d.day==1:print('frozen through',ds,'window races',g['n'],flush=True)

    # Join outcomes after ALL walk-forward scores are frozen.
    final=[]
    for z in frozen:
        key=z.pop('_v88_key')
        z.update(outcomes.get(key,{}))
        final.append(z)
    write_csv(OUT,final)

    L=['# v88 場別ダッシュ指数：prior-only walk-forward検証','',
       f'期間: **{START}〜{END}** / 場指数は各レース日の前日までの過去{LOOKBACK_DAYS}日だけで算出。','',
       '## 固定ルール',
       '- 4カド: 実4コースから「まくり/まくり差し」で1着した率。',
       '- 5頭: 実5コース1着率。',
       f'- 場率を全場率へ alpha={ALPHA:.0f}R で縮約。場サンプル{MIN_VENUE_N}R未満は補正0。',
       f'- 補正 = (縮約場率-全場率)×{SCALE:.0f}、**±{MAX_POINTS:.0f}点でcap**。閾値最適化なし。',
       '- 展示進入changedは現行運用どおり entry_gate_keep=1 のみ評価。',
       '- 当日結果はその日の全候補score_v88を固定した後にしか履歴へ追加しない。','',
       '## Baseline vs 場別ダッシュ補正','|モデル|期間|評価|Baseline|v88|候補差|頭率差|ROI差|','|---|---|---|---|---|---:|---:|---:|']

    for model in ('4カドまくり','5頭展開'):
        for per in ('prior7','recent3',None):
            plabel=per or '10mo'
            for grade in ('A','S'):
                b=metrics(selected(final,model,grade,False,per))
                a=metrics(selected(final,model,grade,True,per))
                L.append(f'|{model}|{plabel}|{grade}+|{fmt(b)}|{fmt(a)}|{a[0]-b[0]:+d}R|{a[2]-b[2]:+.2f}pt|{a[4]-b[4]:+.1f}pt|')

    L+=['','## A閾値を跨いだレース（補正の実作用）','|モデル|区分|R|頭率|ルート率|20点ROI|','|---|---|---:|---:|---:|---:|']
    for model in ('4カドまくり','5頭展開'):
        promoted=[r for r in final if kept(r) and r.get('model')==model and score_base(r)<A_CUT<=score_adj(r)]
        demoted=[r for r in final if kept(r) and r.get('model')==model and score_adj(r)<A_CUT<=score_base(r)]
        for label,rs in [('昇格',promoted),('降格',demoted)]:
            m=metrics(rs);L.append(f'|{model}|{label}|{m[0]}|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    # Predeclared conservative adoption signal: recent A head rate must improve >=0.5pt,
    # prior7 must not deteriorate >0.5pt. ROI is reported but not part of pass/fail.
    L+=['','## 事前固定の採用シグナル','- 条件: **直近3か月A+頭率 +0.5pt以上** かつ **前半7か月A+頭率 -0.5pt未満の悪化なし**。ROIは副指標。']
    for model in ('4カドまくり','5頭展開'):
        bp=metrics(selected(final,model,'A',False,'prior7'));ap=metrics(selected(final,model,'A',True,'prior7'))
        br=metrics(selected(final,model,'A',False,'recent3'));ar=metrics(selected(final,model,'A',True,'recent3'))
        dp=ap[2]-bp[2];dr=ar[2]-br[2]
        ok=(dr>=0.5 and dp>=-0.5)
        L.append(f"- **{model}**: prior7 {dp:+.2f}pt / recent3 {dr:+.2f}pt → **{'PASS' if ok else 'FAIL'}**")
    L+=['','## 注意','- PASSでもこの10か月でルール設計・検証をしているため、productionへ即時固定する前にprospective確認を推奨。','- v87の10か月完成値を直接使わず、各日より前だけのデータから場指数を再計算している。','- 3まくり/3まくり差しは今回補正対象外。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
