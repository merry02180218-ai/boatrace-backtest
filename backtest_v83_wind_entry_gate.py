"""v83: 10-month validation of the new live rules.

Base rows are the already-frozen v74 strict replay candidates.  This script enriches
those frozen candidates with PRE-RACE preview-only information:
  1) exhibition/start-display course for the predicted head boat;
  2) wind direction/speed from previews/sui.

No result/payout field is used to create entry status, wind cell, wind class, or
wind score adjustment.  Outcome columns already present in the frozen v74 file are
used only after enrichment for evaluation.

Entry rule requested 2026-09-04:
- if the target boat's exhibition course differs from its boat number, exclude.
- missing course is not treated as a confirmed change; it is kept but reported.

Wind experiment:
- relative wind normalization reuses the v38 stadium-facing definition;
- old period 2025-11-01..2026-05-31 learns model x relative-wind x speed cells;
- minimum old-period sample 40 structural candidates;
- favorable = head-rate lift >= +3 percentage points vs old model baseline;
- unfavorable = <= -3 points; otherwise neutral;
- recent period 2026-06-01..2026-08-31 is untouched by this v83 classification;
- diagnostic soft adjustment is +2 / 0 / -2 score points, matching the scale of
  the existing history soft-score rather than replacing direct exhibition score.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date

from backtest import rows

SRC = 'analysis_v74_ten_month_strict_flow.csv'
OUT = 'analysis_v83_wind_entry_gate.csv'
SUMMARY = 'summary_v83_wind_entry_gate.md'
START = date(2025, 11, 1)
OLD_END = date(2026, 5, 31)
RECENT_START = date(2026, 6, 1)
END = date(2026, 8, 31)
A_CUT = 55.0
S_CUT = 67.0
WIND_MIN_N = 40
WIND_LIFT = 0.03
WIND_POINTS = 2.0

MODELS = ['3まくり', '3まくり差し', '4カドまくり', '5頭展開']
VENUE = {
    1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'
}
STADIUM_FACING = {
    '桐生':90,'戸田':0,'江戸川':200,'平和島':270,'多摩川':180,'浜名湖':90,
    '蒲郡':90,'常滑':270,'津':90,'三国':270,'びわこ':0,'住之江':0,
    '尼崎':0,'鳴門':0,'丸亀':0,'児島':0,'宮島':90,'徳山':0,
    '下関':0,'若松':0,'芦屋':0,'福岡':0,'唐津':0,'大村':0,
}
WIND_DEG = {1:0,2:45,3:90,4:135,5:180,6:225,7:270,8:315}
REL_ORDER = ['追い','右横','向かい','左横']
SPD_ORDER = ['0-2m','3-4m','5m+']


def ff(x, default=None):
    try:
        if x is None or str(x).strip() == '': return default
        return float(x)
    except Exception:
        return default


def ii(x, default=0):
    try: return int(float(x))
    except Exception: return default


def bycode(rs):
    return {r.get('レースコード',''): r for r in rs if r.get('レースコード')}


def read_local(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_local(path, rs):
    if not rs: return
    fields = sorted(set().union(*(r.keys() for r in rs)))
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rs)


def spdbin(x):
    if x is None: return 'missing'
    return '0-2m' if x <= 2 else ('3-4m' if x <= 4 else '5m+')


def relative_wind(venue, wind_code):
    wd = WIND_DEG.get(wind_code)
    face = STADIUM_FACING.get(venue)
    if wd is None or face is None: return 'missing', None
    rel = (wd - face) % 360
    if rel < 45 or rel >= 315: return '追い', rel
    if rel < 135: return '右横', rel
    if rel < 225: return '向かい', rel
    return '左横', rel


def source_type(v):
    s = (v or '').strip()
    if not s: return 'missing'
    if s.startswith('backfill'): return 'backfill'
    return 'snapshot'


def enrich_preview(base):
    """Enrich frozen rows without looking at result/payout columns."""
    byday = defaultdict(list)
    for r in base:
        byday[r['date']].append(r)
    out = []
    for idx, ds in enumerate(sorted(byday)):
        ymd = ds.replace('-', '/')
        stt = bycode(rows(f'data/previews/stt/{ymd}.csv'))
        sui = bycode(rows(f'data/previews/sui/{ymd}.csv'))
        for src in byday[ds]:
            # Copy prediction/frozen record first.  Outcome fields are deliberately
            # not referenced anywhere in this enrichment block.
            z = dict(src)
            code = z['race_code']; head = ii(z.get('head'))
            sr = stt.get(code, {}); wr = sui.get(code, {})

            course = ii(sr.get(f'艇{head}_コース'), 0)
            if course == head:
                entry_status = 'same'
            elif course in range(1, 7):
                entry_status = 'changed'
            else:
                entry_status = 'missing'

            venue_code = ii(code[8:10] if len(code) >= 10 else 0)
            venue = VENUE.get(venue_code, str(venue_code))
            ws = ff(wr.get('風速(m)'))
            wc = ii(wr.get('風向'), 0)
            rw, rdeg = relative_wind(venue, wc)
            wb = spdbin(ws)
            cell = f'{rw}_{wb}' if rw != 'missing' and wb != 'missing' else 'missing'

            z.update({
                'entry_course_preview': course,
                'entry_status': entry_status,
                'entry_gate_keep': int(entry_status != 'changed'),
                'entry_confirmed_same': int(entry_status == 'same'),
                'entry_source_type': source_type(sr.get('取得日時')),
                'venue_v83': venue,
                'venue_code_v83': venue_code,
                'wind_speed': ws if ws is not None else '',
                'wind_bin': wb,
                'wind_code': wc,
                'relative_wind': rw,
                'relative_deg': '' if rdeg is None else rdeg,
                'wind_cell': cell,
                'wind_source_type': source_type(wr.get('取得日時')),
            })
            out.append(z)
        if idx % 30 == 0:
            print('enriched', ds, 'stt', len(stt), 'sui', len(sui), flush=True)
    return out


def valid_result(r): return ii(r.get('valid_result')) == 1

def valid_payout(r): return ii(r.get('valid_payout')) == 1

def head_hit(r): return ii(r.get('head_hit')) == 1

def route_hit(r): return ii(r.get('route_hit')) == 1

def score(r): return ff(r.get('score'), 0.0) or 0.0

def pct(n,d): return 100*n/d if d else 0.0


def roi20(rs):
    q = [r for r in rs if valid_payout(r)]
    inv = 2000 * len(q)
    ret = sum(ii(r.get('payout100')) for r in q if ii(r.get('ticket20_hit')) == 1)
    return pct(ret, inv)


def roi6(rs):
    q = [r for r in rs if valid_payout(r)]
    inv = 600 * len(q)
    ret = sum(ii(r.get('payout100')) for r in q if ii(r.get('ticket6_hit')) == 1)
    return pct(ret, inv)


def metrics(rs):
    q = [r for r in rs if valid_result(r)]
    n = len(q); hh = sum(head_hit(r) for r in q); rh = sum(route_hit(r) for r in q)
    return {
        'n':n, 'head':hh, 'head_rate':pct(hh,n), 'route':rh, 'route_rate':pct(rh,n),
        'roi6':roi6(q), 'roi20':roi20(q)
    }


def select(rs, grade='A', primary=False, gate='all', period=None, model=None):
    q = []
    for r in rs:
        if period == 'old' and r['date'] > OLD_END.isoformat(): continue
        if period == 'recent' and r['date'] < RECENT_START.isoformat(): continue
        if model and r.get('model') != model: continue
        if primary and ii(r.get('head')) not in (3,5): continue
        if gate == 'changed_only' and ii(r.get('entry_gate_keep')) != 1: continue
        if gate == 'confirmed_same' and ii(r.get('entry_confirmed_same')) != 1: continue
        s = score(r)
        if grade == 'A' and s < A_CUT: continue
        if grade == 'S' and s < S_CUT: continue
        q.append(r)
    return q


def learn_wind_classes(rs):
    """Old-period only, structural candidates after confirmed-change exclusion."""
    old = [r for r in rs if r['date'] <= OLD_END.isoformat() and ii(r.get('entry_gate_keep')) == 1 and valid_result(r)]
    model_base = {}
    for m in MODELS:
        a = [r for r in old if r.get('model') == m]
        model_base[m] = (sum(head_hit(r) for r in a) / len(a)) if a else 0.0

    cells = {}
    for m in MODELS:
        for rw in REL_ORDER:
            for wb in SPD_ORDER:
                cell = f'{rw}_{wb}'
                a = [r for r in old if r.get('model') == m and r.get('wind_cell') == cell]
                n = len(a); rate = (sum(head_hit(r) for r in a) / n) if n else 0.0
                diff = rate - model_base[m]
                if n >= WIND_MIN_N and diff >= WIND_LIFT:
                    cls = 'favorable'
                elif n >= WIND_MIN_N and diff <= -WIND_LIFT:
                    cls = 'unfavorable'
                else:
                    cls = 'neutral'
                cells[(m,cell)] = {'class':cls,'n_old':n,'old_rate':rate,'old_base':model_base[m],'old_diff':diff}
    return cells, model_base


def apply_wind_classes(rs, cells):
    for r in rs:
        info = cells.get((r.get('model'), r.get('wind_cell')), {'class':'neutral','n_old':0,'old_rate':0,'old_base':0,'old_diff':0})
        cls = info['class']
        adj = WIND_POINTS if cls == 'favorable' else (-WIND_POINTS if cls == 'unfavorable' else 0.0)
        r['wind_class_old_only'] = cls
        r['wind_old_n'] = info['n_old']
        r['wind_old_head_rate'] = round(100*info['old_rate'], 4)
        r['wind_old_model_base'] = round(100*info['old_base'], 4)
        r['wind_old_lift_pt'] = round(100*info['old_diff'], 4)
        r['wind_adjust_points'] = adj
        r['score_wind_v83'] = round(score(r) + adj, 4)
        r['approved_A_wind_v83'] = int(score(r) + adj >= A_CUT)
        r['approved_S_wind_v83'] = int(score(r) + adj >= S_CUT)
    return rs


def recent_wind_selected(rs, grade='A', primary=True):
    q=[]
    for r in rs:
        if r['date'] < RECENT_START.isoformat(): continue
        if ii(r.get('entry_gate_keep')) != 1: continue
        if primary and ii(r.get('head')) not in (3,5): continue
        if grade == 'A' and ii(r.get('approved_A_wind_v83')) != 1: continue
        if grade == 'S' and ii(r.get('approved_S_wind_v83')) != 1: continue
        q.append(r)
    return q


def fmtstat(m):
    return f"{m['n']}R / 頭{m['head']} ({m['head_rate']:.1f}%) / ルート{m['route_rate']:.1f}% / 20点ROI {m['roi20']:.1f}%"


def main():
    base = read_local(SRC)
    print('base frozen rows', len(base), flush=True)
    enriched = enrich_preview(base)
    cells, model_base = learn_wind_classes(enriched)
    enriched = apply_wind_classes(enriched, cells)
    write_local(OUT, enriched)

    # Source quality / entry status counts, prediction-only columns.
    entry_counts = Counter(r['entry_status'] for r in enriched)
    entry_src = Counter(r['entry_source_type'] for r in enriched)
    wind_src = Counter(r['wind_source_type'] for r in enriched)
    wind_missing = sum(r['wind_cell'] == 'missing' for r in enriched)

    L = ['# v83 10か月：展示進入変更除外 + 風向/風速 検証','',
         f'**期間: {START}〜{END}**。ベースはv74で結果読込前に凍結済みの候補・score・grade・頭・相手順位。',
         'v83ではその凍結行へ historical previews/stt の展示コースと previews/sui の風向・風速を結合し、結合・除外・風クラス決定では結果/払戻列を参照していない。','',
         '## 新ルール','- 対象選手の展示進入コースが艇番から変わったレースは除外。','- コース欠損は「変更確認できず」として changed-only ルールでは残し、別途 confirmed-same の厳格版も比較。','- 風はv38と同じ場向き定義で追い/向かい/右横/左横へ正規化し、0-2m / 3-4m / 5m+ に区分。','',
         '## データカバレッジ',
         f"- v74凍結候補: {len(enriched):,}行",
         f"- 展示進入: same {entry_counts['same']:,} / changed {entry_counts['changed']:,} / missing {entry_counts['missing']:,}",
         f"- ST展示ソース: snapshot {entry_src['snapshot']:,} / backfill {entry_src['backfill']:,} / missing {entry_src['missing']:,}",
         f"- 風ソース: snapshot {wind_src['snapshot']:,} / backfill {wind_src['backfill']:,} / missing {wind_src['missing']:,}; wind cell missing {wind_missing:,}",
         '- backfill-from-daily はレース後に復元された保存行で、展示コース/気象という結果非依存情報ではあるが、厳密なT-10保存時刻は保証しない。snapshot と区別して解釈する。','']

    L += ['## 展示進入変更の除外効果（主候補3+5）','|評価|ベース|changedのみ除外|confirmed sameのみ|','|---|---|---|---|']
    for g in ('A','S'):
        a = metrics(select(enriched,g,True,'all'))
        b = metrics(select(enriched,g,True,'changed_only'))
        c = metrics(select(enriched,g,True,'confirmed_same'))
        L.append(f'|{g}以上|{fmtstat(a)}|{fmtstat(b)}|{fmtstat(c)}|')

    L += ['','## モデル別 A以上：展示進入変更除外前後','|モデル|ベースR|ベース頭率|除外後R|除外後頭率|除外R|除外群頭率|除外後20点ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        a = select(enriched,'A',False,'all',model=m); b = select(enriched,'A',False,'changed_only',model=m)
        removed = [r for r in a if ii(r.get('entry_gate_keep')) == 0]
        ma,mb,mr = metrics(a),metrics(b),metrics(removed)
        L.append(f"|{m}|{ma['n']}|{ma['head_rate']:.1f}%|{mb['n']}|{mb['head_rate']:.1f}%|{mr['n']}|{mr['head_rate']:.1f}%|{mb['roi20']:.1f}%|")

    L += ['','## 風クラスの学習（旧7か月のみ）',
          f'- 旧期間 {START}〜{OLD_END}: 各モデル×相対風×風速セルを、モデル全体頭率より +3pt以上かつ n>={WIND_MIN_N} なら favorable、-3pt以下なら unfavorable。',
          f'- recent {RECENT_START}〜{END} の結果はクラス決定に未使用。直前scoreへの診断補正は favorable +{WIND_POINTS:.0f} / neutral 0 / unfavorable -{WIND_POINTS:.0f} 点。','',
          '|モデル|風セル|旧R|旧頭率|旧モデル基準|差|クラス|recent R|recent 頭率|recent 20点ROI|','|---|---|---:|---:|---:|---:|---|---:|---:|---:|']
    for m in MODELS:
        for rw in REL_ORDER:
            for wb in SPD_ORDER:
                cell=f'{rw}_{wb}'; info=cells[(m,cell)]
                rec=[r for r in enriched if r['date']>=RECENT_START.isoformat() and ii(r.get('entry_gate_keep'))==1 and r.get('model')==m and r.get('wind_cell')==cell and valid_result(r)]
                mm=metrics(rec)
                if info['n_old'] >= 20 or mm['n'] >= 10:
                    L.append(f"|{m}|{cell}|{info['n_old']}|{100*info['old_rate']:.1f}%|{100*info['old_base']:.1f}%|{100*info['old_diff']:+.1f}pt|{info['class']}|{mm['n']}|{mm['head_rate']:.1f}%|{mm['roi20']:.1f}%|")

    L += ['','## recent 3か月：風±2点を最終scoreへ入れた場合（主候補3+5）','|評価|進入変更除外のみ|進入変更除外+風補正|候補差|頭率差|20点ROI差|','|---|---|---|---:|---:|---:|']
    for g in ('A','S'):
        b = metrics(select(enriched,g,True,'changed_only',period='recent'))
        w = metrics(recent_wind_selected(enriched,g,True))
        L.append(f"|{g}以上|{fmtstat(b)}|{fmtstat(w)}|{w['n']-b['n']:+d}R|{w['head_rate']-b['head_rate']:+.1f}pt|{w['roi20']-b['roi20']:+.1f}pt|")

    L += ['','## recent 3か月：風クラス単体の再現性（進入変更除外後・全構造候補）','|クラス|R|頭率|ルート率|20点ROI|','|---|---:|---:|---:|---:|']
    for cls in ('favorable','neutral','unfavorable'):
        a=[r for r in enriched if r['date']>=RECENT_START.isoformat() and ii(r.get('entry_gate_keep'))==1 and r.get('wind_class_old_only')==cls]
        mm=metrics(a);L.append(f"|{cls}|{mm['n']}|{mm['head_rate']:.1f}%|{mm['route_rate']:.1f}%|{mm['roi20']:.1f}%|")

    # Stable sign report old vs recent for interpretable wind cells.
    L += ['','## 旧7か月→recent 3か月で方向が再現した風セル','|モデル|風セル|旧差|recent差|旧R|recent R|方向|','|---|---|---:|---:|---:|---:|---|']
    for m in MODELS:
        recbase=[r for r in enriched if r['date']>=RECENT_START.isoformat() and ii(r.get('entry_gate_keep'))==1 and r.get('model')==m and valid_result(r)]
        rb=(sum(head_hit(r) for r in recbase)/len(recbase)) if recbase else 0
        for rw in REL_ORDER:
            for wb in SPD_ORDER:
                cell=f'{rw}_{wb}'; info=cells[(m,cell)]
                rec=[r for r in recbase if r.get('wind_cell')==cell]
                if info['n_old']<20 or len(rec)<10: continue
                rr=(sum(head_hit(r) for r in rec)/len(rec)) if rec else 0
                d1=info['old_diff'];d2=rr-rb
                if d1*d2>0:
                    L.append(f"|{m}|{cell}|{100*d1:+.1f}pt|{100*d2:+.1f}pt|{info['n_old']}|{len(rec)}|{'有利' if d1>0 else '不利'}|")

    L += ['','## 判定方針','- 展示進入変更除外は、除外群の成績と除外後の頭率/ROIを見て正式採用可否を判断する。','- 風±2点は旧7か月だけでルールを決め、recent 3か月で改善が再現した場合のみ直前判定へのソフト補正候補とする。','- 風は事前候補ゲートには使わず、展示進入確認後・直前A/S判定時の補助に限定する。','- snapshot/backfill差が大きい場合、ライブ運用では必ず当日提示された公式直前風を優先する。']

    with open(SUMMARY,'w',encoding='utf-8') as f:
        f.write('\n'.join(L)+'\n')
    print('DONE', OUT, SUMMARY, flush=True)


if __name__ == '__main__':
    main()
