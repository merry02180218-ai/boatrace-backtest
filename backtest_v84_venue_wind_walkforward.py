"""v84: 10-month walk-forward validation for venue x model x relative wind x speed.

Input is v83 enriched/frozen rows. The v74 prediction fields were frozen before results.
v84 uses each prior day's already-finished outcomes only to update wind-history statistics.
For every new day, venue/model/wind classification and adjusted score are frozen BEFORE
that day's outcomes are added. This prevents same-day/future result leakage.

Rule is fixed ex ante for this diagnostic:
- entry-changed rows are excluded from operational evaluation.
- exact cell = venue x model x relative_wind x wind_bin.
- venue-model baseline must have >= 40 prior valid results.
- exact cell must have >= 15 prior valid results.
- smoothed cell rate = (cell_hits + PRIOR_STRENGTH * venue_model_rate)/(cell_n + PRIOR_STRENGTH).
- favorable if smoothed lift >= +3pt; unfavorable if <= -3pt; else neutral.
- soft score adjustment = +1.5 / 0 / -1.5 points.
- classification uses no current-day results; history updates after all rows for the day are frozen.

This is a diagnostic and does not automatically change production rules.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v84_venue_wind_walkforward.csv'
SUMMARY='summary_v84_venue_wind_walkforward.md'
START=date(2025,11,1); END=date(2026,8,31)
A_CUT=55.0; S_CUT=67.0
CELL_MIN_N=15; BASE_MIN_N=40; PRIOR_STRENGTH=20.0; LIFT=0.03; POINTS=1.5
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
PRIMARY={'3まくり','3まくり差し','5頭展開'}


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
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def valid_result(r):return ii(r.get('valid_result'))==1

def valid_payout(r):return ii(r.get('valid_payout'))==1

def head_hit(r):return ii(r.get('head_hit'))==1

def route_hit(r):return ii(r.get('route_hit'))==1

def base_score(r):return ff(r.get('score'),0.0) or 0.0

def kept(r):return ii(r.get('entry_gate_keep'))==1

def month_of(r):return (r.get('date') or '')[:7]

def exact_key(r):return (r.get('venue_v83',''),r.get('model',''),r.get('wind_cell','missing'))

def base_key(r):return (r.get('venue_v83',''),r.get('model',''))


def classify(r, base_hist, cell_hist):
    bk=base_key(r); ck=exact_key(r)
    bn,bh=base_hist[bk]; cn,ch=cell_hist[ck]
    br=(bh/bn) if bn else 0.0
    cr=(ch/cn) if cn else 0.0
    sr=((ch+PRIOR_STRENGTH*br)/(cn+PRIOR_STRENGTH)) if (cn+PRIOR_STRENGTH)>0 else br
    lift=sr-br
    usable=(r.get('wind_cell') not in ('','missing') and bn>=BASE_MIN_N and cn>=CELL_MIN_N)
    if usable and lift>=LIFT: cls='favorable'
    elif usable and lift<=-LIFT: cls='unfavorable'
    else: cls='neutral'
    adj=POINTS if cls=='favorable' else (-POINTS if cls=='unfavorable' else 0.0)
    return cls,adj,bn,bh,br,cn,ch,cr,sr,lift,usable


def walk_forward(rows):
    byday=defaultdict(list)
    for r in rows:byday[r['date']].append(r)
    base_hist=defaultdict(lambda:[0,0])
    cell_hist=defaultdict(lambda:[0,0])
    out=[]
    for ds in sorted(byday):
        frozen=[]
        for src in byday[ds]:
            z=dict(src)
            cls,adj,bn,bh,br,cn,ch,cr,sr,lf,usable=classify(z,base_hist,cell_hist)
            s=base_score(z); sw=s+adj
            z.update({
                'v84_class':cls,'v84_adjust':adj,'v84_usable':int(usable),
                'v84_base_n':bn,'v84_base_hits':bh,'v84_base_rate':round(100*br,4),
                'v84_cell_n':cn,'v84_cell_hits':ch,'v84_cell_raw_rate':round(100*cr,4),
                'v84_cell_smoothed_rate':round(100*sr,4),'v84_lift_pt':round(100*lf,4),
                'score_v84':round(sw,4),'approved_A_v84':int(sw>=A_CUT),'approved_S_v84':int(sw>=S_CUT),
            })
            frozen.append(z)
        out.extend(frozen)
        # AFTER the whole day is frozen, add today's outcomes to history.
        for z in frozen:
            if not kept(z) or not valid_result(z) or z.get('wind_cell') in ('','missing'):continue
            bk=base_key(z);ck=exact_key(z);h=int(head_hit(z))
            base_hist[bk][0]+=1;base_hist[bk][1]+=h
            cell_hist[ck][0]+=1;cell_hist[ck][1]+=h
        if ds.endswith('-01'):print('walk-forward',ds,'history base keys',len(base_hist),'cells',len(cell_hist),flush=True)
    return out


def roi20(rs):
    q=[r for r in rs if valid_payout(r)]
    inv=2000*len(q)
    ret=sum(ii(r.get('payout100')) for r in q if ii(r.get('ticket20_hit'))==1)
    return pct(ret,inv)

def metrics(rs):
    q=[r for r in rs if valid_result(r)]
    n=len(q);h=sum(head_hit(r) for r in q);rh=sum(route_hit(r) for r in q)
    return n,h,pct(h,n),pct(rh,n),roi20(q)

def filt(rs,grade='A',adjusted=False,primary=False,model=None,venue=None,month=None,cls=None,snapshot_only=False):
    out=[]
    for r in rs:
        if not kept(r):continue
        if primary and r.get('model') not in PRIMARY:continue
        if model and r.get('model')!=model:continue
        if venue and r.get('venue_v83')!=venue:continue
        if month and month_of(r)!=month:continue
        if cls and r.get('v84_class')!=cls:continue
        if snapshot_only and r.get('wind_source_type')!='snapshot':continue
        s=(ff(r.get('score_v84'),0) if adjusted else base_score(r)) or 0
        if grade=='A' and s<A_CUT:continue
        if grade=='S' and s<S_CUT:continue
        out.append(r)
    return out

def fmt(m):
    n,h,hr,rr,roi=m
    return f'{n}R / 頭{h} ({hr:.1f}%) / ルート{rr:.1f}% / 20点ROI {roi:.1f}%'


def main():
    src=read_csv(SRC)
    wf=walk_forward(src)
    write_csv(OUT,wf)
    months=sorted({month_of(r) for r in wf if month_of(r)})
    usable=sum(ii(r.get('v84_usable')) for r in wf)
    cls_counts=Counter(r.get('v84_class') for r in wf)

    L=['# v84 10か月：場×モデル×相対風向×風速 walk-forward','',
       f'**期間: {START}〜{END}**。入力はv83でv74凍結候補へ展示進入・風を結合した行。',
       '各日の判定時点では、その日より前に終了したレースの結果だけで風履歴を作る。同日全レースを先に凍結し、その後に当日結果を履歴へ追加するため、同日・未来結果リークなし。','',
       '## 固定ルール',
       f'- exact cell = 場×モデル×相対風向×風速。場×モデル基準 {BASE_MIN_N}R以上、exact cell {CELL_MIN_N}R以上で判定対象。',
       f'- cell頭率は場×モデル基準を prior strength={PRIOR_STRENGTH:.0f}R として縮約。縮約後差が ±{100*LIFT:.0f}pt以上なら favorable / unfavorable。',
       f'- 直前score補正は favorable +{POINTS:.1f} / unfavorable -{POINTS:.1f} / neutral 0点。展示進入changedは従来通り除外。',
       '- これは診断であり、結果だけを見て自動採用しない。','',
       '## カバレッジ',f'- v83入力: {len(src):,}行 / walk-forward exact-cell判定可能: {usable:,}行 ({pct(usable,len(src)):.1f}%)',
       f"- クラス件数: favorable {cls_counts['favorable']:,} / neutral {cls_counts['neutral']:,} / unfavorable {cls_counts['unfavorable']:,}",'',
       '## 月別 主力（3まくり+3まくり差し+5頭）A以上','|月|補正なし|v84補正|候補差|頭率差|ROI差|','|---|---|---|---:|---:|---:|']
    for mo in months:
        a=metrics(filt(wf,'A',False,True,month=mo));b=metrics(filt(wf,'A',True,True,month=mo))
        L.append(f'|{mo}|{fmt(a)}|{fmt(b)}|{b[0]-a[0]:+d}R|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## 10か月合計 主力比較','|評価|補正なし|v84補正|候補差|頭率差|ROI差|','|---|---|---|---:|---:|---:|']
    for g in ('A','S'):
        a=metrics(filt(wf,g,False,True));b=metrics(filt(wf,g,True,True))
        L.append(f'|{g}以上|{fmt(a)}|{fmt(b)}|{b[0]-a[0]:+d}R|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## モデル別 A以上','|モデル|補正なし|v84補正|頭率差|ROI差|','|---|---|---|---:|---:|']
    for m in MODELS:
        a=metrics(filt(wf,'A',False,False,model=m));b=metrics(filt(wf,'A',True,False,model=m))
        L.append(f'|{m}|{fmt(a)}|{fmt(b)}|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    # OOS class quality: class is frozen before current-day outcomes.
    L+=['','## walk-forward風クラス自体の成績（全構造候補・進入changed除外）','|クラス|R|頭率|ルート率|20点ROI|','|---|---:|---:|---:|---:|']
    for c in ('favorable','neutral','unfavorable'):
        q=[r for r in wf if kept(r) and r.get('v84_class')==c]
        m=metrics(q);L.append(f'|{c}|{m[0]}|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    # Venue diagnostics, only venues with enough usable A rows; compare favorable vs unfavorable.
    venues=sorted({r.get('venue_v83') for r in wf if r.get('venue_v83')})
    venue_rows=[]
    for v in venues:
        fav=filt(wf,'A',False,False,venue=v,cls='favorable')
        unf=filt(wf,'A',False,False,venue=v,cls='unfavorable')
        fm=metrics(fav);um=metrics(unf)
        if fm[0]>=12 or um[0]>=12:
            venue_rows.append((v,fm,um))
    L+=['','## 場別 A以上：walk-forward favorable / unfavorable','|場|favorable|unfavorable|差（頭率）|','|---|---|---|---:|']
    for v,fm,um in venue_rows:
        diff=(fm[2]-um[2]) if fm[0] and um[0] else 0.0
        L.append(f'|{v}|{fmt(fm)}|{fmt(um)}|{diff:+.1f}pt|')

    # Amagasaki focused breakdown by model and class.
    L+=['','## 尼崎 詳細（A以上）','|モデル|クラス|R|頭率|ルート率|20点ROI|','|---|---|---:|---:|---:|---:|']
    for m in MODELS:
        for c in ('favorable','neutral','unfavorable'):
            q=filt(wf,'A',False,False,model=m,venue='尼崎',cls=c)
            z=metrics(q)
            if z[0]:L.append(f'|{m}|{c}|{z[0]}|{z[2]:.1f}%|{z[3]:.1f}%|{z[4]:.1f}%|')

    # Snapshot-only recent reliability diagnostic.
    L+=['','## snapshot-only A以上（厳密な直前保存行のみ）','|評価|補正なし|v84補正|','|---|---|---|']
    for g in ('A','S'):
        a=metrics(filt(wf,g,False,True,snapshot_only=True));b=metrics(filt(wf,g,True,True,snapshot_only=True))
        L.append(f'|{g}以上|{fmt(a)}|{fmt(b)}|')

    # Strong exact cells that had sufficient prior history at least once; summarize realized OOS outcomes when class non-neutral.
    buckets=defaultdict(list)
    for r in wf:
        if kept(r) and ii(r.get('v84_usable')) and r.get('v84_class')!='neutral':
            buckets[(r.get('venue_v83'),r.get('model'),r.get('wind_cell'),r.get('v84_class'))].append(r)
    sig=[]
    for k,a in buckets.items():
        m=metrics(a)
        if m[0]>=8:
            avg_lift=sum(ff(r.get('v84_lift_pt'),0) or 0 for r in a)/len(a)
            sig.append((m[0],abs(avg_lift),k,avg_lift,m))
    sig.sort(reverse=True)
    L+=['','## 実運用候補になる場×モデル×風セル（walk-forwardで8R以上出現）','|場|モデル|風セル|判定|R|事前平均lift|実頭率|ルート率|20点ROI|','|---|---|---|---|---:|---:|---:|---:|---:|']
    for n,_,k,al,m in sig[:60]:
        v,mod,cell,c=k
        L.append(f'|{v}|{mod}|{cell}|{c}|{m[0]}|{al:+.1f}pt|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    L+=['','## 判定','- favorable が neutral / unfavorable よりOOSで一貫して強いか、月別でも改善が偏り過ぎないかを重視する。','- 場別exact-cellはサンプルが小さいため、単月高配当だけで正式採用しない。','- 採用する場合も事前候補ゲートには使わず、展示後のT-10最終判定でのみソフト補正する。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('DONE',len(wf),'usable',usable,'classes',dict(cls_counts),flush=True)

if __name__=='__main__':main()
