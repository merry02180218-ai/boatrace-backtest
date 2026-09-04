"""v91: isolated 10-month exhibition-ST weight / raw-vs-corrected score test.

Predeclared variants (chosen before v91 outcomes are evaluated):
3まくり baseline: ex .28 + corrST .28 + straight .22 + avg .17 + venue .05
- CORR32: ex .24 + corrST .32 + straight .22 + avg .17 + venue .05
- CORR35: ex .21 + corrST .35 + straight .22 + avg .17 + venue .05
- RAW32 : ex .24 + rawST  .32 + straight .22 + avg .17 + venue .05
- RAW35 : ex .21 + rawST  .35 + straight .22 + avg .17 + venue .05
Extra ST weight comes only from exhibition-time weight.

4カド baseline: ex .28 + corrST .30 + straight .22 + avg .15 + venue .05
- CORR25: ex .28 + corrST .25 + straight .27 + avg .15 + venue .05
- CORR20: ex .28 + corrST .20 + straight .32 + avg .15 + venue .05
- RAW25 : ex .28 + rawST  .25 + straight .27 + avg .15 + venue .05
- RAW20 : ex .28 + rawST  .20 + straight .32 + avg .15 + venue .05
Removed ST weight goes only to original-exhibition straight.

NO-LEAK / ISOLATION
- Source is v90, whose ST features were frozen day-by-day using prior-only bias.
- All outcome/payout columns are stripped before variant scores are calculated.
- Variant score = already-frozen source score + 100*(variant direct comp - baseline direct comp).
  Thus history adjustment, tilt bonus, candidate gate, head, subtype, and ticket order remain frozen.
- Only after ALL variant scores are frozen are outcomes joined for evaluation.
- This intentionally does NOT rerun 3m vs 3ms subtype choice; it isolates ST weighting.
- Venue-dash and wind qualitative policies are not numerically added here.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date

from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct

SRC='analysis_v90_exhibition_st_10month.csv'
OUT='analysis_v91_st_weight_walkforward.csv'
SUMMARY='summary_v91_st_weight_walkforward.md'
START=date(2025,11,1)
PRIOR_END=date(2026,5,31)
RECENT_START=date(2026,6,1)
END=date(2026,8,31)
A_CUT=55.0
S_CUT=67.0

OUTCOME_FIELDS={
    'valid_result','valid_payout','head_hit','route_hit','ticket20_hit','ticket6_hit',
    'payout100','winner','second','third','actual_trifecta','actual_ticket_rank20',
    'actual_ticket_rank6','actual_combo','kimarite'
}

VARIANTS={
 '3まくり':{
   'BASE':('corr',.28,.28,.22,.17),
   'CORR32':('corr',.24,.32,.22,.17),
   'CORR35':('corr',.21,.35,.22,.17),
   'RAW32':('raw',.24,.32,.22,.17),
   'RAW35':('raw',.21,.35,.22,.17),
 },
 '4カドまくり':{
   'BASE':('corr',.28,.30,.22,.15),
   'CORR25':('corr',.28,.25,.27,.15),
   'CORR20':('corr',.28,.20,.32,.15),
   'RAW25':('raw',.28,.25,.27,.15),
   'RAW20':('raw',.28,.20,.32,.15),
 }
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

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def period(ds):
    d=date.fromisoformat(ds)
    return 'prior7' if d<=PRIOR_END else 'recent3'

def direct_inputs(code,tkz,stt,orig):
    # ex/original corrections do not depend on ST bias. Pass zeros and ignore returned ST.
    ex,_st,os=corrected_direct(code,tkz,stt,orig,{b:0.0 for b in range(1,7)})
    for b in range(1,7):
        ex.setdefault(b,.5)
        os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
    return ex,os

def comp(model,variant,ex,os,st_raw,st_corr):
    mode,wex,wst,wstraight,wavg=VARIANTS[model][variant]
    h=3 if model=='3まくり' else 4
    st=st_corr if mode=='corr' else st_raw
    return wex*ex[h]+wst*st+wstraight*os[h]['straight']+wavg*os[h]['avg']+.05*.5

def metrics(rs,score_field,cut):
    q=[r for r in rs if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and ff(r.get(score_field),-999)>=cut]
    n=len(q);h=sum(ii(r.get('head_hit')) for r in q);route=sum(ii(r.get('route_hit')) for r in q)
    qp=[r for r in q if ii(r.get('valid_payout'))==1]
    inv=2000*len(qp)
    ret=sum(ii(r.get('payout100')) for r in qp if ii(r.get('ticket20_hit'))==1)
    return {'n':n,'h':h,'hr':pct(h,n),'rr':pct(route,n),'roi':pct(ret,inv),'pay_n':len(qp)}

def fmt(m):
    return f"{m['n']}R / 頭{m['h']} ({m['hr']:.1f}%) / ルート{m['rr']:.1f}% / 20点ROI {m['roi']:.1f}%"

def main():
    raw=read_csv(SRC)
    preds=[];outcomes={};byday=defaultdict(list)
    for idx,r in enumerate(raw):
        ds=r.get('date','');m=r.get('model','')
        if m not in VARIANTS or not (START.isoformat()<=ds<=END.isoformat()):continue
        key=(ds,r.get('race_code',''),m,r.get('head',''),idx)
        p={k:v for k,v in r.items() if k not in OUTCOME_FIELDS};p['_key']=key
        preds.append(p);byday[ds].append(p)
        outcomes[key]={k:r.get(k,'') for k in OUTCOME_FIELDS if k in r}

    frozen=[]
    for ds in sorted(byday):
        ymd=ds.replace('-','/')
        tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'))
        stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
        for p in byday[ds]:
            z=dict(p);code=z.get('race_code','');m=z.get('model','');h=3 if m=='3まくり' else 4
            ex,os=direct_inputs(code,tkz,stt,orig)
            sr=ff(z.get(f'st_raw_strength_b{h}'),.5)
            sc=ff(z.get(f'st_corr_strength_b{h}'),.5)
            base_comp=comp(m,'BASE',ex,os,sr,sc)
            source_score=ff(z.get('score'),0.0)
            z['period_v91']=period(ds)
            z['v91_ex']=round(ex[h],5);z['v91_st_raw']=round(sr,5);z['v91_st_corr']=round(sc,5)
            z['v91_straight']=round(os[h]['straight'],5);z['v91_avg']=round(os[h]['avg'],5)
            z['v91_base_comp_recalc']=round(base_comp,6)
            z['score_BASE_v91']=round(source_score,4)
            for vname in VARIANTS[m]:
                if vname=='BASE':continue
                vc=comp(m,vname,ex,os,sr,sc)
                z[f'score_{vname}_v91']=round(source_score+100*(vc-base_comp),4)
                z[f'delta_{vname}_v91']=round(100*(vc-base_comp),4)
            frozen.append(z)
        print('v91 frozen',ds,len(byday[ds]),flush=True)

    # Join outcomes only after all variant scores are frozen.
    final=[]
    for z in frozen:
        key=z.pop('_key');z.update(outcomes.get(key,{}));final.append(z)
    write_csv(OUT,final)

    L=['# v91 展示ST重み / raw-vs補正ST 10か月スコア再選別','',
       f'期間: **{START}〜{END}**。v90で前日までのSTTだけから固定したraw/枠補正ST強度を使用。','',
       '## 事前固定した比較',
       '- 3まくり: ST 28% → 32% / 35%。増分は展示タイムから移す。raw ST版と枠補正ST版を比較。',
       '- 4カド: ST 30% → 25% / 20%。減分はオリジナル展示の直線へ移す。raw ST版と枠補正ST版を比較。',
       '- 3まくり差し・5頭は変更しない。場別ダッシュ適性・風は数値加点せず、この検証には入れない。',
       '- 元の構造候補・頭・3まくり/まくり差しの既存subtype選択・履歴soft score・チルト・相手順位/20点買い目は固定。ST部分だけをisolatedに変更。','',
       '## Baseline vs variants','|モデル|variant|期間|評価|Baseline|Variant|R差|頭率差|ルート差|ROI差|','|---|---|---|---|---|---|---:|---:|---:|---:|']

    pass_rows=[]
    for m in ('3まくり','4カドまくり'):
        mr=[r for r in final if r.get('model')==m]
        for vname in VARIANTS[m]:
            if vname=='BASE':continue
            sf=f'score_{vname}_v91'
            for per in ('prior7','recent3','10mo'):
                q=mr if per=='10mo' else [r for r in mr if r.get('period_v91')==per]
                for label,cut in (('A+',A_CUT),('S+',S_CUT)):
                    b=metrics(q,'score_BASE_v91',cut);a=metrics(q,sf,cut)
                    L.append(f"|{m}|{vname}|{per}|{label}|{fmt(b)}|{fmt(a)}|{a['n']-b['n']:+d}|{a['hr']-b['hr']:+.2f}pt|{a['rr']-b['rr']:+.2f}pt|{a['roi']-b['roi']:+.1f}pt|")

            bp=metrics([r for r in mr if r.get('period_v91')=='prior7'],'score_BASE_v91',A_CUT)
            ap=metrics([r for r in mr if r.get('period_v91')=='prior7'],sf,A_CUT)
            br=metrics([r for r in mr if r.get('period_v91')=='recent3'],'score_BASE_v91',A_CUT)
            ar=metrics([r for r in mr if r.get('period_v91')=='recent3'],sf,A_CUT)
            bs=metrics([r for r in mr if r.get('period_v91')=='recent3'],'score_BASE_v91',S_CUT)
            ass=metrics([r for r in mr if r.get('period_v91')=='recent3'],sf,S_CUT)
            sample_ok=(ap['n']>=.9*bp['n'] if bp['n'] else False) and (ar['n']>=.9*br['n'] if br['n'] else False)
            ok=(ar['hr']-br['hr']>=.5 and ap['hr']-bp['hr']>=-.5 and ap['rr']-bp['rr']>=-.5 and ar['rr']-br['rr']>=-.5 and ass['hr']-bs['hr']>=-.5 and sample_ok)
            pass_rows.append((m,vname,ok,ap['hr']-bp['hr'],ar['hr']-br['hr'],ap['rr']-bp['rr'],ar['rr']-br['rr'],ass['hr']-bs['hr'],sample_ok))

    L+=['','## 事前固定の採用シグナル',
        '- PASS条件: **直近3か月A+頭率 +0.5pt以上**、prior7 A+頭率/ルート率・recent3 A+ルート率・recent3 S+頭率が各 -0.5pt未満の悪化なし、候補数がbaselineの90%以上。ROIは副指標。',
        '- v90結果を見て仮説を作っているため、PASSでもproduction即採用ではなくprospective候補。']
    for m,v,ok,dph,drh,dpr,drr,dsh,sok in pass_rows:
        L.append(f'- **{m} {v}**: prior頭 {dph:+.2f}pt / recent頭 {drh:+.2f}pt / priorルート {dpr:+.2f}pt / recentルート {drr:+.2f}pt / recent S頭 {dsh:+.2f}pt / sample {"OK" if sok else "NG"} → **{"PASS" if ok else "FAIL"}**')

    # Threshold crossing diagnostic on A cut.
    L+=['','## A閾値を跨いだレース','|モデル|variant|区分|R|頭率|ルート率|20点ROI|','|---|---|---|---:|---:|---:|---:|']
    for m in ('3まくり','4カドまくり'):
        mr=[r for r in final if r.get('model')==m and ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1]
        for v in VARIANTS[m]:
            if v=='BASE':continue
            sf=f'score_{v}_v91'
            prom=[r for r in mr if ff(r.get('score_BASE_v91'),-999)<A_CUT<=ff(r.get(sf),-999)]
            dem=[r for r in mr if ff(r.get(sf),-999)<A_CUT<=ff(r.get('score_BASE_v91'),-999)]
            for label,q in (('昇格',prom),('降格',dem)):
                # Metrics here use dummy always-selected score to reuse outcome calc.
                qq=[]
                for r in q:
                    x=dict(r);x['_always']=999;qq.append(x)
                mm=metrics(qq,'_always',A_CUT)
                L.append(f"|{m}|{v}|{label}|{mm['n']}|{mm['hr']:.1f}%|{mm['rr']:.1f}%|{mm['roi']:.1f}%|")

    L+=['','## 注意','- v91はST重みだけのisolated test。3まくりと3まくり差しが同一レースで重複した場合のsubtype選択自体はv74/v83の凍結値を維持する。',
        '- 古いSTTには backfill-from-daily が含まれ、結果非依存ではあるが厳密なT-10保存が保証されない行がある。',
        '- 結果欠損日はv90同様 2026-06-17。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
