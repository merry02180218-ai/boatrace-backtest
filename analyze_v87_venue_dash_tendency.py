"""v87: 10-month venue tendency analysis for outer/dash-side winners.

Purpose
-------
Test whether some venues structurally produce more winners from the outer/dash side.
This is DESCRIPTIVE outcome analysis only; it must not be fed directly into production
scoring without a later prior-only / walk-forward validation.

Two separate definitions are reported:
1) outer BOAT-NUMBER winners: winning boat is 4/5/6.
2) outer ACTUAL-COURSE winners: winner actually started from course 4/5/6 according
   to the result CSV's course assignment fields.

The second is closer to a dash-side concept, but actual course 4-6 does not prove a
literal dash start in every abnormal-entry race, so it is treated as an outer-course
proxy rather than a perfect slow/dash label.

Period: 2025-11-01 .. 2026-08-31, same result source/window as v75.
Robustness split: prior7 = Nov-May, recent3 = Jun-Aug.
A venue is called stably dash-side strong/weak only when its actual-course 4-6 win-rate
lift versus the matching national baseline is >= +2.0pt / <= -2.0pt in BOTH blocks.
This fixed descriptive threshold is not optimized for ROI.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
from backtest import rows, i

START=date(2025,11,1)
SPLIT=date(2026,6,1)
END=date(2026,8,31)
THRESHOLD_PT=2.0
ATTACK={'まくり','まくり差し'}

VENUES={
 '01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
 '07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
 '13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
 '19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村',
}

FIELDS=[
 'n','course_valid',
 'frame4','frame5','frame6','frame_outer',
 'course4','course5','course6','course_outer','course45',
 'outer_attack','course4_attack','course5_attack','course6_attack',
 'frame4_attack','frame5_attack','frame6_attack',
]


def normkim(s):
    return (s or '').replace(' ','').replace('　','')


def pct(a,b):
    return 100.0*a/b if b else 0.0


def venue_code(r):
    v=str(r.get('レース場') or '').strip()
    if v.isdigit():
        return v.zfill(2)
    code=str(r.get('レースコード') or '').strip()
    return code[8:10] if len(code)>=12 else ''


def winner_course(r,winner):
    for c in range(1,7):
        if i(r.get(f'{c}コース_艇番'))==winner:
            return c
    return 0


def segment(d):
    return 'prior7' if d<SPLIT else 'recent3'


def add(c,w,course,kim):
    c['n']+=1
    if w in (4,5,6):
        c[f'frame{w}']+=1
        c['frame_outer']+=1
        if kim in ATTACK:
            c[f'frame{w}_attack']+=1
    if course in range(1,7):
        c['course_valid']+=1
        if course in (4,5,6):
            c[f'course{course}']+=1
            c['course_outer']+=1
            if course in (4,5): c['course45']+=1
            if kim in ATTACK:
                c['outer_attack']+=1
                c[f'course{course}_attack']+=1


def blank():
    return Counter({k:0 for k in FIELDS})


def rate(c,key,course_based=False):
    den=c['course_valid'] if course_based else c['n']
    return pct(c[key],den)


def metric_row(vc, nat, prefix):
    out={}
    out[f'{prefix}_races']=vc['n']
    out[f'{prefix}_course_coverage_pct']=round(pct(vc['course_valid'],vc['n']),3)
    for b in (4,5,6):
        out[f'{prefix}_frame{b}_win_pct']=round(rate(vc,f'frame{b}'),3)
        out[f'{prefix}_course{b}_win_pct']=round(rate(vc,f'course{b}',True),3)
    out[f'{prefix}_frame456_win_pct']=round(rate(vc,'frame_outer'),3)
    out[f'{prefix}_course456_win_pct']=round(rate(vc,'course_outer',True),3)
    out[f'{prefix}_course45_win_pct']=round(rate(vc,'course45',True),3)
    out[f'{prefix}_outer_attack_pct']=round(rate(vc,'outer_attack',True),3)
    out[f'{prefix}_course4_attack_pct']=round(rate(vc,'course4_attack',True),3)
    out[f'{prefix}_course5_attack_pct']=round(rate(vc,'course5_attack',True),3)
    out[f'{prefix}_frame456_lift_pt']=round(rate(vc,'frame_outer')-rate(nat,'frame_outer'),3)
    out[f'{prefix}_course456_lift_pt']=round(rate(vc,'course_outer',True)-rate(nat,'course_outer',True),3)
    out[f'{prefix}_outer_attack_lift_pt']=round(rate(vc,'outer_attack',True)-rate(nat,'outer_attack',True),3)
    out[f'{prefix}_course4_attack_lift_pt']=round(rate(vc,'course4_attack',True)-rate(nat,'course4_attack',True),3)
    return out


def main():
    # counts[period][venue], where period includes all10/prior7/recent3
    counts={p:defaultdict(blank) for p in ('all10','prior7','recent3')}
    national={p:blank() for p in ('all10','prior7','recent3')}
    missing=[]; valid_days=0

    d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        rr=rows(f'data/results/realtime/{ymd}.csv')
        if not rr:
            missing.append(str(d)); d+=timedelta(days=1); continue
        valid_days+=1
        seg=segment(d)
        for r in rr:
            w=i(r.get('1着_艇番'))
            if w not in range(1,7): continue
            v=venue_code(r)
            if v not in VENUES: continue
            kim=normkim(r.get('決まり手'))
            course=winner_course(r,w)
            for p in ('all10',seg):
                add(counts[p][v],w,course,kim)
                add(national[p],w,course,kim)
        d+=timedelta(days=1)

    out=[]
    for v in sorted(VENUES):
        row={'venue_code':v,'venue':VENUES[v]}
        for p in ('all10','prior7','recent3'):
            row.update(metric_row(counts[p][v],national[p],p))
        pl=row['prior7_course456_lift_pt']; rl=row['recent3_course456_lift_pt']
        if counts['prior7'][v]['n']>=300 and counts['recent3'][v]['n']>=150 and pl>=THRESHOLD_PT and rl>=THRESHOLD_PT:
            label='ダッシュ側強め・時系列一致'
        elif counts['prior7'][v]['n']>=300 and counts['recent3'][v]['n']>=150 and pl<=-THRESHOLD_PT and rl<=-THRESHOLD_PT:
            label='ダッシュ側弱め・時系列一致'
        else:
            label='平均圏/時系列不一致'
        row['stable_label']=label
        out.append(row)

    out.sort(key=lambda r:r['all10_course456_win_pct'], reverse=True)
    fs=list(out[0].keys()) if out else []
    with open('analysis_v87_venue_dash_tendency.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs); w.writeheader(); w.writerows(out)

    nat=national['all10']
    L=[
      '# v87 10か月：場別ダッシュ側の来やすさ検証','',
      f'期間: **{START}〜{END}**（v75と同じ結果期間） / 有効日 {valid_days}日 / 結果欠損日 {len(missing)}日','',
      '## 定義','- 外枠艇番 = 4・5・6号艇が1着。',
      '- ダッシュ側代理 = 結果CSVの実進入で4・5・6コースだった艇が1着。艇番と実コースを分離して集計。',
      '- 外攻め = 実4〜6コースの勝者かつ決まり手が「まくり / まくり差し」。',
      '- 注意: 実4〜6コースは「外コース」の客観値だが、異常進入等では必ずしも全艇が文字通りダッシュ発進だったことを保証しない。',
      f'- 安定判定は前半7か月と直近3か月の双方で全国平均比 ±{THRESHOLD_PT:.1f}pt以上/以下。結果を見て閾値最適化していない記述基準。','',
      '## 全国ベースライン','|指標|10か月率|','|---|---:|',
      f"|4〜6号艇1着|{rate(nat,'frame_outer'):.2f}%|",
      f"|実4〜6コース1着|{rate(nat,'course_outer',True):.2f}%|",
      f"|実4〜5コース1着|{rate(nat,'course45',True):.2f}%|",
      f"|実4〜6コースのまくり/まくり差し|{rate(nat,'outer_attack',True):.2f}%|",
      f"|実4コースのまくり/まくり差し|{rate(nat,'course4_attack',True):.2f}%|",
      f"|実5コース1着|{rate(nat,'course5',True):.2f}%|",
      f"|実進入コース取得率|{pct(nat['course_valid'],nat['n']):.2f}%|",'',
      '## 24場ランキング：実4〜6コース1着率','|順位|場|R|4〜6号艇|実4〜6コース|全国差|外攻め|実4C攻め|実5C頭|前半差|直近差|判定|',
      '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for idx,r in enumerate(out,1):
        L.append(f"|{idx}|{r['venue']}|{r['all10_races']:,}|{r['all10_frame456_win_pct']:.2f}%|{r['all10_course456_win_pct']:.2f}%|{r['all10_course456_lift_pt']:+.2f}pt|{r['all10_outer_attack_pct']:.2f}%|{r['all10_course4_attack_pct']:.2f}%|{r['all10_course5_win_pct']:.2f}%|{r['prior7_course456_lift_pt']:+.2f}pt|{r['recent3_course456_lift_pt']:+.2f}pt|{r['stable_label']}|")

    strong=[r for r in out if r['stable_label'].startswith('ダッシュ側強め')]
    weak=[r for r in out if r['stable_label'].startswith('ダッシュ側弱め')]
    L+=['','## 時系列で安定した場']
    if strong:
        L.append('### ダッシュ側強め')
        for r in strong:
            L.append(f"- **{r['venue']}**: 10か月 {r['all10_course456_win_pct']:.2f}%（全国差 {r['all10_course456_lift_pt']:+.2f}pt）、前半 {r['prior7_course456_lift_pt']:+.2f}pt / 直近 {r['recent3_course456_lift_pt']:+.2f}pt")
    else:L.append('- ダッシュ側強めの安定条件なし')
    if weak:
        L.append('### ダッシュ側弱め')
        for r in weak:
            L.append(f"- **{r['venue']}**: 10か月 {r['all10_course456_win_pct']:.2f}%（全国差 {r['all10_course456_lift_pt']:+.2f}pt）、前半 {r['prior7_course456_lift_pt']:+.2f}pt / 直近 {r['recent3_course456_lift_pt']:+.2f}pt")
    else:L.append('- ダッシュ側弱めの安定条件なし')

    by4=sorted(out,key=lambda r:r['all10_course4_attack_pct'],reverse=True)
    by5=sorted(out,key=lambda r:r['all10_course5_win_pct'],reverse=True)
    L+=['','## 4カドモデルに近い指標：実4コース攻め 上位8場','|順位|場|実4Cまくり/まくり差し|全国差|実4〜6頭率|','|---:|---|---:|---:|---:|']
    nat4=rate(nat,'course4_attack',True)
    for idx,r in enumerate(by4[:8],1):
        L.append(f"|{idx}|{r['venue']}|{r['all10_course4_attack_pct']:.2f}%|{r['all10_course4_attack_pct']-nat4:+.2f}pt|{r['all10_course456_win_pct']:.2f}%|")
    L+=['','## 5頭モデル参考：実5コース1着率 上位8場','|順位|場|実5C頭率|実4〜6頭率|','|---:|---|---:|---:|']
    for idx,r in enumerate(by5[:8],1):
        L.append(f"|{idx}|{r['venue']}|{r['all10_course5_win_pct']:.2f}%|{r['all10_course456_win_pct']:.2f}%|")

    L+=['','## 解釈上の注意',
        '- これは結果データを使った場特性の記述分析で、予測候補を作る前の特徴量ではない。',
        '- 強い場差が見つかっても、この10か月値をそのまま本番スコアに入れると結果参照になる。',
        '- 採用候補が見つかった場合は、次に「その日より前だけの場別ダッシュ率」を使うwalk-forwardで4カド/5頭モデルへの増分効果を検証する。']
    if missing:L+=['','結果欠損日: '+', '.join(missing)]
    with open('summary_v87_venue_dash_tendency.md','w',encoding='utf-8') as f:
        f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':
    main()
