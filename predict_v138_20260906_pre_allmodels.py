from __future__ import annotations
import csv
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import predict_v107_20260905_official_fullscan as v107
from backtest import rows, race_features, grade_score, clamp, pct_motor
from analyze_v109_1head_monthly_walkforward import ff, ii

HD='20260906'
YMD='2026/09/06'
TRAIN_END=date(2026,8,31)
SRC='analysis_v108_1head_feasibility.csv'
OUT='pred_v138_20260906_pre_allmodels.csv'
SUMMARY='prediction_v138_20260906_pre_allmodels.md'
VENUES=[f'{i:02d}' for i in range(1,25)]
LEGACY_FEATURES=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength']

v107.HD=HD


def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def legacy_row_from_x(x, venue):
    z=x[1]
    vals=[
      grade_score(z['grade']), clamp((z['wr']-3)/5), clamp((z['local']-2.5)/5.5),
      .62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3']), clamp(z['waku_wr']/8),
      clamp((.24-z['nst'])/.14), clamp((6-z['waku_sr'])/5), z['past_win'],
      .5 if z['meet_st'] is None else clamp((.22-z['meet_st'])/.12),
    ]
    venue=str(venue).zfill(2)
    vals += [1.0 if venue==v else 0.0 for v in VENUES]
    return vals

def legacy_hist_matrix(rs):
    a=[]
    for r in rs:
        row=[ff(r.get(k),0) for k in LEGACY_FEATURES]
        vv=str(r.get('venue','')).zfill(2)
        row += [1.0 if vv==v else 0.0 for v in VENUES]
        a.append(row)
    return np.asarray(a,float)

def fit_legacy():
    src=[r for r in read_csv(SRC) if ii(r.get('valid_result'))==1 and date.fromisoformat(r['date'])<=TRAIN_END]
    X=legacy_hist_matrix(src); y=np.asarray([ii(r.get('head_hit')) for r in src],int)
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))])
    m.fit(X,y); return m

def current_cards():
    cards=rows(f'data/programs/race_cards/{YMD}.csv')
    w10=rows(f'data/programs/waku10/{YMD}.csv')
    wm={r.get('レースコード',''):r for r in w10}
    out=[]
    for r in cards:
        code=r.get('レースコード',''); w=wm.get(code,{})
        if not code: continue
        try:x=race_features(r,w)
        except Exception: continue
        out.append((r,x))
    return out

def load_waku_history(days=45):
    ds=[]; d=date(2026,9,5)
    for _ in range(days): ds.append(d); d-=timedelta(days=1)
    got=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fut=[ex.submit(v107.fetch_hist_day,d) for d in ds]
        for f in as_completed(fut):
            try: got.append(f.result())
            except Exception: pass
    got.sort(key=lambda z:z[0]); lookup={}
    for _,items in got:
        for rid,b,z in items: lookup[(rid,b)]=z
    return lookup

def non1_scan():
    names=v107.racer_names(); active,probe=v107.discover_active(names)
    lookup=load_waku_history(); races=[]; errs=[]
    jobs=[(j,r) for j in active for r in range(1,13)]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(v107.parse_race,j,r,names):(j,r) for j,r in jobs}
        for f in as_completed(fs):
            j,r=fs[f]
            try:races.append(f.result())
            except Exception as e:errs.append((j,r,str(e)))
    races.sort(key=lambda z:(z['jcd'],z['rno']))
    found,total=v107.attach_waku(races,lookup)
    raw=[]
    for r in races: raw.extend(v107.eval_race(r))
    g=defaultdict(list)
    for z in raw:g[(z['jcd'],z['race'],z['head'])].append(z)
    cand=[]
    for _,rs in g.items():
        z=max(rs,key=lambda q:q['struct_index']).copy(); z['routes']='/'.join(sorted(q['model'] for q in rs)); cand.append(z)
    return active,races,errs,found,total,cand

def main():
    # 1-head Legacy PRE top5/day; pre-exhibition current card only.
    model=fit_legacy(); cur=current_cards()
    one=[]
    if cur:
        X=np.asarray([legacy_row_from_x(x,r.get('レース場コード','')) for r,x in cur],float)
        ps=model.predict_proba(X)[:,1]
        for (r,x),p in zip(cur,ps):
            one.append({'venue':r.get('レース場名','') or r.get('レース場コード',''),'jcd':str(r.get('レース場コード','')).zfill(2),
                        'race':ii(r.get('レース回')),'deadline':r.get('締切予定時刻',''),'head':1,'routes':'1頭 Legacy PRE',
                        'name':x[1]['name'],'grade':x[1]['grade'],'struct_index':100*float(p),'min_margin':'','shadow':'v109/v110'})
        one=sorted(one,key=lambda z:(-z['struct_index'],z['jcd'],z['race']))[:5]

    active,races,errs,found,total,cand=non1_scan()
    for z in cand: z['shadow']='v100' if z['head']==3 else ('v106' if z['head']==4 else '-')
    allc=one+cand
    allc.sort(key=lambda z:(z.get('deadline','') or '99:99',z['jcd'],z['race'],z['head']))
    fields=['venue','jcd','race','deadline','head','routes','name','grade','struct_index','min_margin','shadow']
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:z.get(k,'') for k in fields} for z in allc])

    counts=Counter(r['jcd'] for r in races); expected=len(active)*12
    L=['# v138 2026-09-06 全モデル事前候補','',
       '- **展示前のみ**。結果・払戻・実進入・当日展示・当日オッズは不使用。',
       '- ①頭: 現行Legacy PRE（1号艇9特徴+場）を2026-08-31までで学習し、日次top5。',
       '- ③まくり/③まくり差し/④カド/⑤頭: v107現行構造ゲートを9/6公式racelistへ適用。',
       f'- 公式開催場: {len(active)}場 / 取得 {len(races)}/{expected}R / エラー {len(errs)}R。',
       f'- 枠別履歴補完: {found}/{total}。','',
       '## 締切順','|場|R|締切|頭|モデル|選手|級|PRE/構造指数|shadow|','|---|---:|---|---:|---|---|---|---:|---|']
    for z in allc:
        L.append(f"|{z['venue']}|{z['race']}R|{z.get('deadline','')}|{z['head']}|{z['routes']}|{z['name']}|{z['grade']}|{float(z['struct_index']):.1f}|{z.get('shadow','-')}|")
    L += ['',f'①頭候補 **{len(one)}R** / 非①候補 **{len(cand)}R** / 合計 **{len(allc)}R**。',
          '','※①頭の指数はLegacy PRE確率×100。非①はv107構造指数で、同じ尺度ではない。最終BUYは展示後の各モデル直前判定で決める。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
