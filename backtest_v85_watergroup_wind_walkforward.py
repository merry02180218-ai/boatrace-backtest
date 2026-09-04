"""v85: 10-month walk-forward validation for water-surface group x model x relative wind x speed.

Input is v83 enriched/frozen rows. Venue grouping is fixed independently of race outcomes
using the conventional water-quality classification (fresh/brackish/sea).  The grouping
is therefore NOT learned from the ten-month result set.

For each date, classification uses only outcomes from earlier dates. All races on the
same date are frozen first, then that day's results are added to history.

Fixed diagnostic rule:
- entry-changed rows are excluded operationally.
- water group = 淡水 / 汽水 / 海水.
- exact cell = water_group x model x relative_wind x wind_bin.
- water-group/model baseline requires >=60 prior valid results.
- exact cell requires >=20 prior valid results.
- cell head rate is shrunk toward the water-group/model baseline with prior strength 30R.
- favorable if smoothed lift >= +3pt, unfavorable if <= -3pt, otherwise neutral.
- final-score diagnostic adjustment = +1.5 / 0 / -1.5 points.
- no current-day result is used for current-day classification.

This is diagnostic only and does not automatically alter production.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v85_watergroup_wind_walkforward.csv'
SUMMARY='summary_v85_watergroup_wind_walkforward.md'
START=date(2025,11,1); END=date(2026,8,31)
A_CUT=55.0; S_CUT=67.0
CELL_MIN_N=20; BASE_MIN_N=60; PRIOR_STRENGTH=30.0; LIFT=0.03; POINTS=1.5
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
PRIMARY={'3まくり','3まくり差し','5頭展開'}

WATER_GROUP={
    '桐生':'淡水','戸田':'淡水','多摩川':'淡水','三国':'淡水','びわこ':'淡水','住之江':'淡水','尼崎':'淡水','芦屋':'淡水','唐津':'淡水',
    '江戸川':'汽水','浜名湖':'汽水','蒲郡':'汽水','津':'汽水','福岡':'汽水',
    '平和島':'海水','常滑':'海水','鳴門':'海水','丸亀':'海水','児島':'海水','宮島':'海水','徳山':'海水','下関':'海水','若松':'海水','大村':'海水',
}


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

def group_of(r):return WATER_GROUP.get(r.get('venue_v83',''),'unknown')

def exact_key(r):return (group_of(r),r.get('model',''),r.get('wind_cell','missing'))

def base_key(r):return (group_of(r),r.get('model',''))


def classify(r,base_hist,cell_hist):
    bk=base_key(r); ck=exact_key(r)
    bn,bh=base_hist[bk]; cn,ch=cell_hist[ck]
    br=(bh/bn) if bn else 0.0
    cr=(ch/cn) if cn else 0.0
    sr=((ch+PRIOR_STRENGTH*br)/(cn+PRIOR_STRENGTH)) if (cn+PRIOR_STRENGTH)>0 else br
    lift=sr-br
    usable=(group_of(r)!='unknown' and r.get('wind_cell') not in ('','missing') and bn>=BASE_MIN_N and cn>=CELL_MIN_N)
    if usable and lift>=LIFT: cls='favorable'
    elif usable and lift<=-LIFT: cls='unfavorable'
    else: cls='neutral'
    adj=POINTS if cls=='favorable' else (-POINTS if cls=='unfavorable' else 0.0)
    return cls,adj,bn,bh,br,cn,ch,cr,sr,lift,usable


def walk_forward(rows):
    byday=defaultdict(list)
    for r in rows:byday[r['date']].append(r)
    base_hist=defaultdict(lambda:[0,0]); cell_hist=defaultdict(lambda:[0,0])
    out=[]
    for ds in sorted(byday):
        frozen=[]
        for src in byday[ds]:
            z=dict(src); z['water_group_v85']=group_of(z)
            cls,adj,bn,bh,br,cn,ch,cr,sr,lf,usable=classify(z,base_hist,cell_hist)
            s=base_score(z); sw=s+adj
            z.update({
                'v85_class':cls,'v85_adjust':adj,'v85_usable':int(usable),
                'v85_base_n':bn,'v85_base_hits':bh,'v85_base_rate':round(100*br,4),
                'v85_cell_n':cn,'v85_cell_hits':ch,'v85_cell_raw_rate':round(100*cr,4),
                'v85_cell_smoothed_rate':round(100*sr,4),'v85_lift_pt':round(100*lf,4),
                'score_v85':round(sw,4),'approved_A_v85':int(sw>=A_CUT),'approved_S_v85':int(sw>=S_CUT),
            })
            frozen.append(z)
        out.extend(frozen)
        # add today's results only after every row on the date is frozen
        for z in frozen:
            if not kept(z) or not valid_result(z) or z.get('wind_cell') in ('','missing') or group_of(z)=='unknown':continue
            h=int(head_hit(z)); bk=base_key(z); ck=exact_key(z)
            base_hist[bk][0]+=1;base_hist[bk][1]+=h
            cell_hist[ck][0]+=1;cell_hist[ck][1]+=h
        if ds.endswith('-01'):
            print('walk-forward',ds,'bases',len(base_hist),'cells',len(cell_hist),flush=True)
    return out


def roi20(rs):
    q=[r for r in rs if valid_payout(r)]
    inv=2000*len(q)
    ret=sum(ii(r.get('payout100')) for r in q if ii(r.get('ticket20_hit'))==1)
    return pct(ret,inv)

def metrics(rs):
    q=[r for r in rs if valid_result(r)]
    n=len(q); h=sum(head_hit(r) for r in q); rh=sum(route_hit(r) for r in q)
    return n,h,pct(h,n),pct(rh,n),roi20(q)

def filt(rs,grade='A',adjusted=False,primary=False,model=None,group=None,month=None,cls=None,snapshot_only=False):
    out=[]
    for r in rs:
        if not kept(r):continue
        if primary and r.get('model') not in PRIMARY:continue
        if model and r.get('model')!=model:continue
        if group and r.get('water_group_v85')!=group:continue
        if month and month_of(r)!=month:continue
        if cls and r.get('v85_class')!=cls:continue
        if snapshot_only and r.get('wind_source_type')!='snapshot':continue
        s=(ff(r.get('score_v85'),0) if adjusted else base_score(r)) or 0
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
    usable=sum(ii(r.get('v85_usable')) for r in wf)
    cls_counts=Counter(r.get('v85_class') for r in wf)
    groups=['淡水','汽水','海水']

    L=['# v85 10か月：水面グループ×モデル×相対風向×風速 walk-forward','',
       f'**期間: {START}〜{END}**。入力はv83（v74凍結候補＋展示進入＋風）。',
       '水面グループは結果から学習せず、水質の外生分類（淡水/汽水/海水）を固定している。各日の判定では前日までの結果だけを使い、同日全レースを凍結後に当日結果を履歴へ追加する。','',
       '## 固定グループ',
       '- 淡水: 桐生・戸田・多摩川・三国・びわこ・住之江・尼崎・芦屋・唐津',
       '- 汽水: 江戸川・浜名湖・蒲郡・津・福岡',
       '- 海水: 平和島・常滑・鳴門・丸亀・児島・宮島・徳山・下関・若松・大村','',
       '## 固定ルール',
       f'- exact cell = 水面グループ×モデル×相対風向×風速。グループ×モデル基準 {BASE_MIN_N}R以上、cell {CELL_MIN_N}R以上。',
       f'- cell頭率をグループ×モデル基準へ prior strength={PRIOR_STRENGTH:.0f}R で縮約し、差が ±{100*LIFT:.0f}pt以上で favorable / unfavorable。',
       f'- score補正は +{POINTS:.1f}/0/-{POINTS:.1f}点。展示進入changedは除外。診断であり自動採用しない。','',
       '## カバレッジ',
       f'- v83入力: {len(src):,}行 / walk-forward cell判定可能: {usable:,}行 ({pct(usable,len(src)):.1f}%)',
       f"- favorable {cls_counts['favorable']:,} / neutral {cls_counts['neutral']:,} / unfavorable {cls_counts['unfavorable']:,}",'',
       '## 月別 主力（3まくり+3まくり差し+5頭）A以上','|月|補正なし|v85補正|候補差|頭率差|ROI差|','|---|---|---|---:|---:|---:|']
    for mo in months:
        a=metrics(filt(wf,'A',False,True,month=mo)); b=metrics(filt(wf,'A',True,True,month=mo))
        L.append(f'|{mo}|{fmt(a)}|{fmt(b)}|{b[0]-a[0]:+d}R|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## 10か月合計 主力比較','|評価|補正なし|v85補正|候補差|頭率差|ROI差|','|---|---|---|---:|---:|---:|']
    for g in ('A','S'):
        a=metrics(filt(wf,g,False,True)); b=metrics(filt(wf,g,True,True))
        L.append(f'|{g}以上|{fmt(a)}|{fmt(b)}|{b[0]-a[0]:+d}R|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## モデル別 A以上','|モデル|補正なし|v85補正|頭率差|ROI差|','|---|---|---|---:|---:|']
    for m in MODELS:
        a=metrics(filt(wf,'A',False,False,model=m)); b=metrics(filt(wf,'A',True,False,model=m))
        L.append(f'|{m}|{fmt(a)}|{fmt(b)}|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## walk-forward風クラス自体の成績（全構造候補・進入changed除外）','|クラス|R|頭率|ルート率|20点ROI|','|---|---:|---:|---:|---:|']
    for c in ('favorable','neutral','unfavorable'):
        q=[r for r in wf if kept(r) and r.get('v85_class')==c]
        m=metrics(q); L.append(f'|{c}|{m[0]}|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    L+=['','## 水面グループ×モデル A以上（補正前の実成績）','|グループ|モデル|R|頭率|ルート率|20点ROI|','|---|---|---:|---:|---:|---:|']
    for grp in groups:
        for m in MODELS:
            z=metrics(filt(wf,'A',False,False,model=m,group=grp))
            if z[0]:L.append(f'|{grp}|{m}|{z[0]}|{z[2]:.1f}%|{z[3]:.1f}%|{z[4]:.1f}%|')

    L+=['','## 水面グループ別：favorable / unfavorable（A以上）','|グループ|favorable|unfavorable|頭率差|','|---|---|---|---:|']
    for grp in groups:
        fm=metrics(filt(wf,'A',False,False,group=grp,cls='favorable'))
        um=metrics(filt(wf,'A',False,False,group=grp,cls='unfavorable'))
        diff=fm[2]-um[2] if fm[0] and um[0] else 0.0
        L.append(f'|{grp}|{fmt(fm)}|{fmt(um)}|{diff:+.1f}pt|')

    L+=['','## snapshot-only 主力','|評価|補正なし|v85補正|','|---|---|---|']
    for g in ('A','S'):
        a=metrics(filt(wf,g,False,True,snapshot_only=True)); b=metrics(filt(wf,g,True,True,snapshot_only=True))
        L.append(f'|{g}以上|{fmt(a)}|{fmt(b)}|')

    # Non-neutral cells with enough realized OOS rows; shown only as diagnostics.
    buckets=defaultdict(list)
    for r in wf:
        if kept(r) and ii(r.get('v85_usable')) and r.get('v85_class')!='neutral':
            buckets[(r.get('water_group_v85'),r.get('model'),r.get('wind_cell'),r.get('v85_class'))].append(r)
    sig=[]
    for k,a in buckets.items():
        z=metrics(a)
        if z[0]>=12:
            avg_lift=sum(ff(r.get('v85_lift_pt'),0) or 0 for r in a)/len(a)
            sig.append((z[0],k,z,avg_lift))
    sig.sort(reverse=True)
    L+=['','## 実運用候補セル（walk-forward非neutral・OOS 12R以上）','|グループ|モデル|風セル|判定|R|事前平均lift|実頭率|ルート率|20点ROI|','|---|---|---|---|---:|---:|---:|---:|---:|']
    for _,(grp,m,cell,c),z,av in sig:
        L.append(f'|{grp}|{m}|{cell}|{c}|{z[0]}|{av:+.1f}pt|{z[2]:.1f}%|{z[3]:.1f}%|{z[4]:.1f}%|')

    L+=['','## 判定方針',
        '- favorable > neutral > unfavorable がOOSで再現し、かつA/S閾値周辺の候補選別も改善するかを重視する。',
        '- 一部セルだけ高配当でも全体改善がなければ正式採用しない。',
        '- 採用する場合も風は事前候補ゲートには使わず、T-10の展示後ソフト補正だけに限定する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L[:35]),flush=True)

if __name__=='__main__':main()
