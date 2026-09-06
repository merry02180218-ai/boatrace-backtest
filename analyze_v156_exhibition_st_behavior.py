from __future__ import annotations
import csv, math
from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

from backtest import rows

START=date(2026,5,1)
END=date(2026,9,5)
OUT='analysis_v156_exhibition_st_behavior.csv'
PLAYERS='analysis_v156_player_st_bias.csv'
SUMMARY='summary_v156_exhibition_st_behavior.md'


def ff(x):
    try:return float(x)
    except:return None

def ii(x):
    try:return int(float(x))
    except:return None

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}
def mean(xs):return float(np.mean(xs)) if xs else float('nan')
def med(xs):return float(np.median(xs)) if xs else float('nan')
def pct(n,d):return 100*n/d if d else 0.0

def actual_map(rr):
    out={}
    for c in range(1,7):
        b=ii(rr.get(f'{c}コース_艇番')); st=ff(rr.get(f'{c}コース_スタートタイミング'))
        if b in range(1,7) and st is not None: out[b]=(c,st)
    return out

def ex_course_map(sr):
    out={}
    for b in range(1,7):
        c=ii(sr.get(f'艇{b}_コース')); st=ff(sr.get(f'艇{b}_スタート展示'))
        if c in range(1,7) and st is not None: out[b]=(c,st)
    return out

def bucket(st):
    if st is None:return 'missing'
    if st < 0:return 'F'
    if st <= .05:return '<=.05'
    if st <= .10:return '.06-.10'
    if st <= .15:return '.11-.15'
    if st <= .20:return '.16-.20'
    return '>.20'

def main():
    obs=[]; d=START
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        cards=bycode(rows(f'data/programs/race_cards/{ymd}.csv'))
        stt=bycode(rows(f'data/previews/stt/{ymd}.csv'))
        res=bycode(rows(f'data/results/realtime/{ymd}.csv'))
        for code,sr in stt.items():
            if code not in res or code not in cards:continue
            em=ex_course_map(sr); am=actual_map(res[code]); card=cards[code]
            course_to_boat={c:b for b,(c,st) in em.items()}
            for b,(ec,exst) in em.items():
                if b not in am:continue
                ac,ast=am[b]
                ib=course_to_boat.get(ec-1); ob=course_to_boat.get(ec+1)
                ist=em.get(ib,(None,None))[1] if ib else None
                ost=em.get(ob,(None,None))[1] if ob else None
                obs.append({
                    'date':str(d),'race_code':code,'venue':code[8:10],'boat':b,
                    'racer_id':card.get(f'艇{b}_登録番号',''),'racer_name':card.get(f'艇{b}_選手名',''),
                    'ex_course':ec,'actual_course':ac,'course_same':int(ec==ac),
                    'ex_st':exst,'actual_st':ast,'delta_actual_minus_ex':ast-exst,
                    'inside_ex_st':ist if ist is not None else '',
                    'outside_ex_st':ost if ost is not None else '',
                    'inside_bucket':bucket(ist),'outside_bucket':bucket(ost),'own_bucket':bucket(exst),
                })
        d+=timedelta(days=1)

    # write observation table
    fs=list(obs[0].keys()) if obs else []
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(obs)

    # overall and neighbor regression, only same-course to isolate behavior rather than entry change
    same=[r for r in obs if r['course_same']==1]
    regrows=[]
    for r in same:
        x=[r['ex_st']]
        ok=True
        for k in ('inside_ex_st','outside_ex_st'):
            v=r[k]
            if v=='':ok=False;break
            x.append(float(v))
        if ok:regrows.append((x,r['actual_st']))
    if regrows:
        X=np.asarray([x for x,y in regrows]);y=np.asarray([y for x,y in regrows]);lr=LinearRegression().fit(X,y)
        coef=lr.coef_; r2=lr.score(X,y)
    else:
        coef=[float('nan')]*3;r2=float('nan')

    # bucket neighbor effects, controlling loosely by own exhibition bucket
    neighbor=[]
    for side in ('inside','outside'):
        groups=defaultdict(list)
        for r in same:
            groups[(r['own_bucket'],r[f'{side}_bucket'])].append(r['actual_st'])
        for (ownb,nb),xs in groups.items():
            if len(xs)>=30:neighbor.append((side,ownb,nb,len(xs),mean(xs)))

    # player-specific exhibition -> actual bias; early/late repeatability
    pg=defaultdict(list)
    for r in same:
        key=r['racer_id'] or r['racer_name'];pg[key].append(r)
    prow=[]
    split=date(2026,7,16)
    early_bias={}; late_bias={}
    for key,rs in pg.items():
        if len(rs)<12:continue
        ds=[r['delta_actual_minus_ex'] for r in rs]
        er=[r['delta_actual_minus_ex'] for r in rs if date.fromisoformat(r['date'])<split]
        lr=[r['delta_actual_minus_ex'] for r in rs if date.fromisoformat(r['date'])>=split]
        # shrink player mean toward global mean; 10 pseudo-races
        gm=mean([x['delta_actual_minus_ex'] for x in same]); shr=(sum(ds)+10*gm)/(len(ds)+10)
        faster=sum(1 for x in ds if x<=-.03)
        slower=sum(1 for x in ds if x>=.03)
        name=rs[-1]['racer_name']
        row={'racer_id':key,'racer_name':name,'n':len(rs),'mean_ex_st':mean([x['ex_st'] for x in rs]),
             'mean_actual_st':mean([x['actual_st'] for x in rs]),'mean_delta':mean(ds),'median_delta':med(ds),
             'shrunk_delta':shr,'actual_3c_faster_rate':pct(faster,len(ds)),'actual_3c_slower_rate':pct(slower,len(ds)),
             'early_n':len(er),'early_delta':mean(er) if er else '', 'late_n':len(lr),'late_delta':mean(lr) if lr else ''}
        prow.append(row)
        if len(er)>=6 and len(lr)>=6:early_bias[key]=mean(er);late_bias[key]=mean(lr)
    prow.sort(key=lambda r:r['shrunk_delta'])
    with open(PLAYERS,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(prow[0].keys()) if prow else []);w.writeheader();w.writerows(prow)
    common=list(set(early_bias)&set(late_bias))
    corr=float(np.corrcoef([early_bias[k] for k in common],[late_bias[k] for k in common])[0,1]) if len(common)>=3 else float('nan')

    # exhibition F behavior
    exf=[r for r in same if r['ex_st']<0]
    exnormal=[r for r in same if r['ex_st']>=0]

    L=['# v156 展示ST behavior audit','',
       f'- 対象: {START}〜{END}。展示STを結果STと艇単位でJOIN。',
       '- 実レースSTは results/realtime の実進入コース別スタートタイミングを使用。',
       '- 選手別「展示をわざと遅くする」は意図を断定せず、**展示より本番が一貫して速い癖**として測定。',
       '- 隣艇効果は展示進入が本番進入と同じ艇を中心に確認。結果情報は説明変数には不使用。','',
       '## 全体','',
       f'- 艇レコード: **{len(obs):,}** / 展示進入=本番進入: **{len(same):,}** ({pct(len(same),len(obs)):.1f}%)',
       f'- 平均 展示ST: **{mean([r["ex_st"] for r in same]):.3f}** / 本番ST: **{mean([r["actual_st"] for r in same]):.3f}** / 本番-展示: **{mean([r["delta_actual_minus_ex"] for r in same]):+.3f}**','',
       '## 隣艇STの追加効果（線形回帰）','',
       'actual_ST ~ own_ex_ST + inside_neighbor_ex_ST + outside_neighbor_ex_ST',
       f'- own展示ST係数: **{coef[0]:+.3f}**',f'- 内隣艇展示ST係数: **{coef[1]:+.3f}**',f'- 外隣艇展示ST係数: **{coef[2]:+.3f}**',f'- R²: **{r2:.4f}**',
       '- 隣艇係数が正なら「隣が遅い展示ほど本人の本番STも遅くなる」方向。own展示STを同時に入れた上で見る。','',
       '## 選手固有の展示→本番補正','',
       f'- 12走以上の選手: **{len(prow):,}**',f'- 前半/後半とも6走以上の選手のbias再現相関: **{corr:.3f}** (n={len(common)})',
       '- `shrunk_delta` がマイナスほど「展示より本番で速くなる」傾向。0.03以上の差率も併記。','',
       '### 本番で速くなる傾向 上位10（shrunk）','|選手|n|展示平均|本番平均|本番-展示|本番が0.03以上速い率|','|---|---:|---:|---:|---:|---:|']
    for r in prow[:10]:L.append(f"|{r['racer_name']}|{r['n']}|{r['mean_ex_st']:.3f}|{r['mean_actual_st']:.3f}|{r['shrunk_delta']:+.3f}|{r['actual_3c_faster_rate']:.1f}%|")
    L += ['','### 本番で遅くなる傾向 上位10（shrunk）','|選手|n|展示平均|本番平均|本番-展示|本番が0.03以上遅い率|','|---|---:|---:|---:|---:|---:|']
    for r in list(reversed(prow[-10:])):L.append(f"|{r['racer_name']}|{r['n']}|{r['mean_ex_st']:.3f}|{r['mean_actual_st']:.3f}|{r['shrunk_delta']:+.3f}|{r['actual_3c_slower_rate']:.1f}%|")
    L += ['','## 展示Fの本番修正','',f'- 展示F艇: **{len(exf):,}** / 本番平均ST **{mean([r["actual_st"] for r in exf]):.3f}** / 本番F率 **{pct(sum(r["actual_st"]<0 for r in exf),len(exf)):.1f}%**',f'- 展示正常艇: **{len(exnormal):,}** / 本番平均ST **{mean([r["actual_st"] for r in exnormal]):.3f}** / 本番F率 **{pct(sum(r["actual_st"]<0 for r in exnormal),len(exnormal)):.1f}%**','',
       '## 隣艇bucket（own展示ST帯も固定、n>=30）','|側|本人展示帯|隣艇展示帯|n|本番平均ST|','|---|---|---|---:|---:|']
    for side,ownb,nb,n,m in sorted(neighbor):L.append(f'|{side}|{ownb}|{nb}|{n}|{m:.3f}|')
    L += ['','## 解釈上の注意','- 選手別biasは「わざと」の証明ではない。展示と本番の一貫した差を示すだけ。','- 隣艇効果も因果とは限らないため、次段階で場・コース・選手通常ST・風を加えたwalk-forward予測改善を確認してから実戦採用する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
