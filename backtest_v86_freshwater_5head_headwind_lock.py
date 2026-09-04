"""v86: fixed-condition time-split robustness check.

Condition was identified in v85 and is LOCKED here without re-optimizing:
    water_group == 淡水
    model == 5頭展開
    wind_cell == 向かい_0-2m
    entry_gate_keep == 1

Purpose:
1) Check whether the weak performance is directionally present in both the first 7 months
   (2025-11-01..2026-05-31) and recent 3 months (2026-06-01..2026-08-31).
2) Compare against other 淡水×5頭 races in the same period/grade.
3) Diagnose the operational effect of hard-excluding this one locked condition.

Important: because v85 inspected the full ten months before this condition was chosen,
the recent three months are NOT a pristine untouched OOS set. They are only a temporal
robustness check. Production adoption should still require prospective confirmation.
"""
from __future__ import annotations

import csv
from datetime import date

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v86_freshwater_5head_headwind_lock.csv'
SUMMARY='summary_v86_freshwater_5head_headwind_lock.md'
START=date(2025,11,1); SPLIT=date(2026,6,1); END=date(2026,8,31)
A_CUT=55.0; S_CUT=67.0
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

def kept(r):return ii(r.get('entry_gate_keep'))==1

def score(r):return ff(r.get('score'),0.0) or 0.0

def water_group(r):return WATER_GROUP.get(r.get('venue_v83',''),'unknown')

def locked_condition(r):
    return (kept(r) and water_group(r)=='淡水' and r.get('model')=='5頭展開' and r.get('wind_cell')=='向かい_0-2m')

def period(r):
    d=date.fromisoformat(r['date'])
    if START<=d<SPLIT:return 'prior7'
    if SPLIT<=d<=END:return 'recent3'
    return 'outside'

def month(r):return r.get('date','')[:7]

def roi20(rs):
    q=[r for r in rs if valid_payout(r)]
    inv=2000*len(q)
    ret=sum(ii(r.get('payout100')) for r in q if ii(r.get('ticket20_hit'))==1)
    return pct(ret,inv)

def metrics(rs):
    q=[r for r in rs if valid_result(r)]
    n=len(q);h=sum(head_hit(r) for r in q);rh=sum(route_hit(r) for r in q)
    return n,h,pct(h,n),pct(rh,n),roi20(q)

def fmt(m):
    n,h,hr,rr,roi=m
    return f'{n}R / 頭{h} ({hr:.1f}%) / ルート{rr:.1f}% / 20点ROI {roi:.1f}%'

def grade_ok(r,g):
    s=score(r)
    return s>= (S_CUT if g=='S' else A_CUT)

def rows_for(src, per=None, grade='A', locked=None, freshwater5=False, primary=False, snapshot=False):
    out=[]
    for r in src:
        if not kept(r):continue
        if per and period(r)!=per:continue
        if not grade_ok(r,grade):continue
        if locked is True and not locked_condition(r):continue
        if locked is False and locked_condition(r):continue
        if freshwater5 and not (water_group(r)=='淡水' and r.get('model')=='5頭展開'):continue
        if primary and r.get('model') not in PRIMARY:continue
        if snapshot and r.get('wind_source_type')!='snapshot':continue
        out.append(r)
    return out

def enrich(src):
    out=[]
    for r in src:
        z=dict(r)
        z['water_group_v86']=water_group(z)
        z['v86_locked_condition']=int(locked_condition(z))
        z['v86_period']=period(z)
        out.append(z)
    return out

def main():
    src=enrich(read_csv(SRC))
    write_csv(OUT,src)
    L=[
      '# v86 固定条件検証：淡水×5頭×向かい風0〜2m','',
      '**固定条件（v85後にロック）**: 淡水 × 5頭展開 × 向かい風0〜2m。展示進入changedは従来通り除外。','',
      '- 前半7か月: 2025-11-01〜2026-05-31',
      '- 直近3か月: 2026-06-01〜2026-08-31',
      '- v85で10か月全体を見た後に条件を選んでいるため、直近3か月は完全な未観測OOSではなく時系列ロバストネス確認。','',
      '## 条件そのもの vs 同じ淡水5頭のその他レース','|期間|評価|固定条件|その他の淡水5頭|頭率差|ROI差|','|---|---|---|---|---:|---:|']
    for per in ('prior7','recent3'):
        for g in ('A','S'):
            c=metrics(rows_for(src,per,g,locked=True))
            b=metrics([r for r in rows_for(src,per,g,freshwater5=True) if not locked_condition(r)])
            dhr=c[2]-b[2] if c[0] and b[0] else 0.0
            droi=c[4]-b[4] if c[0] and b[0] else 0.0
            L.append(f'|{per}|{g}以上|{fmt(c)}|{fmt(b)}|{dhr:+.1f}pt|{droi:+.1f}pt|')

    L+=['','## 月別 固定条件 A以上','|月|R|頭率|ルート率|20点ROI|','|---|---:|---:|---:|---:|']
    months=sorted({month(r) for r in src if period(r)!='outside'})
    for mo in months:
        q=[r for r in src if month(r)==mo and locked_condition(r) and grade_ok(r,'A')]
        m=metrics(q)
        if m[0]:L.append(f'|{mo}|{m[0]}|{m[2]:.1f}%|{m[3]:.1f}%|{m[4]:.1f}%|')

    L+=['','## ハード除外した場合の主力（3まくり+3まくり差し+5頭）','|期間|評価|現行|固定条件を除外|候補差|頭率差|ROI差|','|---|---|---|---|---:|---:|---:|']
    for per in ('prior7','recent3'):
        for g in ('A','S'):
            base=rows_for(src,per,g,primary=True)
            ex=[r for r in base if not locked_condition(r)]
            a=metrics(base);b=metrics(ex)
            L.append(f'|{per}|{g}以上|{fmt(a)}|{fmt(b)}|{b[0]-a[0]:+d}R|{b[2]-a[2]:+.1f}pt|{b[4]-a[4]:+.1f}pt|')

    L+=['','## snapshot-only 直近3か月 A以上','|対象|成績|','|---|---|']
    c=metrics(rows_for(src,'recent3','A',locked=True,snapshot=True))
    other=[r for r in rows_for(src,'recent3','A',freshwater5=True,snapshot=True) if not locked_condition(r)]
    L.append(f'|固定条件|{fmt(c)}|')
    L.append(f'|その他の淡水5頭|{fmt(metrics(other))}|')

    # Fixed pass/fail robustness rule: direction must be negative in BOTH time blocks vs peer group.
    prior_c=metrics(rows_for(src,'prior7','A',locked=True)); prior_o=metrics([r for r in rows_for(src,'prior7','A',freshwater5=True) if not locked_condition(r)])
    recent_c=metrics(rows_for(src,'recent3','A',locked=True)); recent_o=metrics([r for r in rows_for(src,'recent3','A',freshwater5=True) if not locked_condition(r)])
    prior_diff=(prior_c[2]-prior_o[2]) if prior_c[0] and prior_o[0] else 0.0
    recent_diff=(recent_c[2]-recent_o[2]) if recent_c[0] and recent_o[0] else 0.0
    directional=(prior_c[0]>=5 and recent_c[0]>=5 and prior_diff<0 and recent_diff<0)
    L+=['','## 判定',
        f'- 前半7か月 A頭率差: {prior_diff:+.1f}pt（固定条件 - その他淡水5頭）',
        f'- 直近3か月 A頭率差: {recent_diff:+.1f}pt',
        f"- 時系列方向一致: **{'PASS' if directional else 'FAIL'}**（両期間5R以上かつ両方マイナスを事前基準）",
        '- PASSでもv85で条件を発見済みなので即production採用にはせず、今後の実戦データでprospective確認を続ける。',
        '- hard excludeのROIは高配当の有無に左右されるため、頭率方向一致を主判定、ROIは副指標とする。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
