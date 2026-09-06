from __future__ import annotations
import csv,re
from datetime import date,timedelta
from collections import Counter,defaultdict
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

from backtest import rows,race_features
import predict_v138_20260906_pre_allmodels as v138
import predict_v107_20260905_official_fullscan as v107

START=date(2026,3,1); END=date(2026,8,31)
TRAIN_END=date(2026,5,31); TEST_START=date(2026,6,1)
TODAY='2026/09/06'; KIRYU='01'
CLASSES=['1逃げ','3まくり','3まくり差し','4カド','5頭','その他']
FEATURE_NAMES=['one_pre','m3','m3s','m4','m5','mg3','mg3s','mg4','mg5']+[f'venue_{i:02d}' for i in range(1,25)]
OUT='analysis_v141_integrated_pre_scenario.csv'
SUMMARY='summary_v141_integrated_pre_scenario.md'
TODAY_OUT='pred_v141_20260906_kiryu_scenario.csv'


def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def normkim(x):return (x or '').replace(' ','').replace('　','')
def rno(x):
    m=re.search(r'\d+',str(x or ''));return int(m.group()) if m else 0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def fit_one_pre_before(cutoff):
    src=[r for r in read_csv(v138.SRC) if v138.ii(r.get('valid_result'))==1 and date.fromisoformat(r['date'])<cutoff]
    X=v138.legacy_hist_matrix(src); y=np.asarray([v138.ii(r.get('head_hit')) for r in src],int)
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))])
    m.fit(X,y);return m

def structural(x):
    a,b,c,d,e=x[1],x[2],x[3],x[4],x[5]
    s3=v107.strength(c);se3=v107.st_edge(b,c);ww2=v107.wallweak(b,c);iw1=v107.c01((7.5-a['waku_wr'])/6)
    s4=v107.strength(d);se4=v107.st_edge(c,d);ww3=v107.wallweak(c,d)
    atk4=v107.c01(.40*se4+.35*ww3+.25*s4);res=v107.resistance12(x);s5=v107.strength(e)
    defs={
      'm3':[(s3,.50),(se3,.55),(ww2,.55)],
      'm3s':[(s3,.50),(se3,.45),(iw1,.45),(ww2,.45)],
      'm4':[(s4,.50),(se4,.55),(ww3,.55)],
      'm5':[(atk4,.55),(res,.55),(s5,.50)],
    }
    out={}
    for k,vals in defs.items():
        out[k]=100*sum(v for v,_ in vals)/len(vals)
        out['g'+k[1:]]=min(v-th for v,th in vals)
    return out

def feature_vec(one_p,sc,venue):
    v=[100*one_p,sc['m3'],sc['m3s'],sc['m4'],sc['m5'],100*sc['g3'],100*sc['g3s'],100*sc['g4'],100*sc['g5']]
    venue=str(venue).zfill(2);v += [1.0 if venue==f'{i:02d}' else 0.0 for i in range(1,25)]
    return v

def actual_class(rr):
    win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
    if win==1:return '1逃げ'
    if win==3 and kim=='まくり':return '3まくり'
    if win==3 and kim=='まくり差し':return '3まくり差し'
    if win==4 and kim in ('まくり','まくり差し'):return '4カド'
    if win==5:return '5頭'
    return 'その他'

def build_history():
    # Legacy PRE is fit strictly before each target month; current-race result is read only after feature freeze.
    month_models={}
    d=START
    frozen=[]
    while d<=END:
        ym=(d.year,d.month)
        if ym not in month_models:month_models[ym]=fit_one_pre_before(date(d.year,d.month,1))
        one_model=month_models[ym]
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv');w10={r.get('レースコード',''):r for r in rows(f'data/programs/waku10/{ymd}.csv')}
        day=[]
        for card in cards:
            code=card.get('レースコード','');
            if not code:continue
            try:x=race_features(card,w10.get(code,{}))
            except:continue
            venue=str(card.get('レース場コード','')).zfill(2)
            one_p=float(one_model.predict_proba(np.asarray([v138.legacy_row_from_x(x,venue)],float))[0,1])
            sc=structural(x)
            day.append({'date':d.isoformat(),'race_code':code,'venue':venue,'race':rno(card.get('レース回')),'x':feature_vec(one_p,sc,venue),
                        'one_pre':100*one_p,**sc})
        # NO-LEAK: outcomes loaded only after all pre-race features for the date are frozen.
        res={r.get('レースコード',''):r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in day:
            rr=res.get(z['race_code'])
            if not rr:continue
            z['actual']=actual_class(rr);frozen.append(z)
        d+=timedelta(days=1)
    return frozen

def fit_integrated(rs,through):
    tr=[z for z in rs if date.fromisoformat(z['date'])<=through]
    X=np.asarray([z['x'] for z in tr],float);y=np.asarray([z['actual'] for z in tr])
    m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.35,max_iter=2500,solver='lbfgs'))])
    m.fit(X,y);return m

def eval_holdout(rs):
    model=fit_integrated(rs,TRAIN_END)
    te=[z for z in rs if date.fromisoformat(z['date'])>=TEST_START]
    X=np.asarray([z['x'] for z in te],float);pro=model.predict_proba(X);classes=list(model.named_steps['lr'].classes_)
    pred=[classes[int(np.argmax(p))] for p in pro];conf=[float(np.max(p)) for p in pro]
    for z,p,c,q in zip(te,pred,conf,pro):
        z['pred']=p;z['confidence']=c;z['probs']={cl:float(q[classes.index(cl)]) if cl in classes else 0.0 for cl in CLASSES}
    return model,te

def stat(rs):
    n=len(rs);h=sum(z['pred']==z['actual'] for z in rs)
    head=lambda cl: {'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(cl,0)
    hh=sum(head(z['pred'])!=0 and head(z['pred'])==head(z['actual']) for z in rs)
    return n,h,100*h/n if n else 0,hh,100*hh/n if n else 0

def current_kiryu(final_model):
    cards=rows(f'data/programs/race_cards/{TODAY}.csv');w10={r.get('レースコード',''):r for r in rows(f'data/programs/waku10/{TODAY}.csv')}
    # if today's card/waku is present, use the same feature construction as backtest. This is all pre-exhibition.
    arr=[];one=v138.fit_legacy()
    for card in cards:
        if str(card.get('レース場コード','')).zfill(2)!=KIRYU:continue
        rn=rno(card.get('レース回'))
        if not 1<=rn<=12:continue
        x=race_features(card,w10.get(card.get('レースコード',''),{}));op=float(one.predict_proba(np.asarray([v138.legacy_row_from_x(x,KIRYU)],float))[0,1]);sc=structural(x)
        fv=feature_vec(op,sc,KIRYU);pr=final_model.predict_proba(np.asarray([fv],float))[0];classes=list(final_model.named_steps['lr'].classes_)
        probs={c:(float(pr[classes.index(c)]) if c in classes else 0.0) for c in CLASSES};best=max(CLASSES,key=lambda c:probs[c])
        arr.append({'race':rn,'one_pre':100*op,**sc,'best':best,'confidence':100*probs[best],**{f'p_{c}':100*probs[c] for c in CLASSES}})
    arr.sort(key=lambda z:z['race']);return arr

def main():
    rs=build_history();_,te=eval_holdout(rs)
    # refit only through 8/31 for 9/6 prospective prediction
    final_model=fit_integrated(rs,END);today=current_kiryu(final_model)
    fields=['date','race_code','venue','race','actual','pred','confidence','one_pre','m3','m3s','m4','m5','g3','g3s','g4','g5']+[f'p_{c}' for c in CLASSES]
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for z in te:
            row={k:z.get(k,'') for k in fields};row.update({f'p_{c}':100*z['probs'][c] for c in CLASSES});w.writerow(row)
    if today:
        with open(TODAY_OUT,'w',newline='',encoding='utf-8-sig') as f:
            fs=list(today[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(today)

    L=['# v141 全モデル統合 PRE 展開選択モデル','',
       '- 入力: ①Legacy PRE + ③まくり構造 + ③まくり差し構造 + ④カド構造 + ⑤頭構造 + 各構造ゲート最低余裕 + 場。',
       '- 出力: 1逃げ / 3まくり / 3まくり差し / 4カド / 5頭 / その他 の6クラス確率。',
       '- 展示・実進入・当日オッズは不使用。各日の結果はPRE特徴を全て固定した後でのみ読む。①PREも対象月より前だけで月次再学習。',
       '- 学習 2026-03〜05、完全ホールドアウト 2026-06〜08。9/6予測用は8/31までで再学習。','']
    n,h,acc,hh,hacc=stat(te);L += [f'## Jun-Aug holdout: {n}R / 展開Top1 {h}R ({acc:.1f}%) / 頭一致 {hh}R ({hacc:.1f}%)','',
       '### 確信度別','|条件|R|展開Top1|頭一致|','|---|---:|---:|---:|']
    for th in [.30,.35,.40,.45,.50,.55,.60]:
        q=[z for z in te if z['confidence']>=th];nn,hh1,aa,hhh,haa=stat(q);L.append(f'|p>={th:.2f}|{nn}|{aa:.1f}%|{haa:.1f}%|')
    L += ['','### 実クラス別','|実展開|R|Top1的中|','|---|---:|---:|']
    for c in CLASSES:
        q=[z for z in te if z['actual']==c];L.append(f'|{c}|{len(q)}|{100*sum(z["pred"]==c for z in q)/len(q) if q else 0:.1f}%|')
    if today:
        L += ['','## 2026-09-06 桐生12R 展開確率','|R|最有力|確率|1逃げ|3まくり|3まくり差し|4カド|5頭|その他|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
        for z in today:L.append(f"|{z['race']}R|{z['best']}|{z['confidence']:.1f}%|{z['p_1逃げ']:.1f}%|{z['p_3まくり']:.1f}%|{z['p_3まくり差し']:.1f}%|{z['p_4カド']:.1f}%|{z['p_5頭']:.1f}%|{z['p_その他']:.1f}%|")
    L += ['','## 判定','- これはまず「展開統合そのものに予測力があるか」の第1段階検証。ROIはまだ結論にしない。',
          '- 有効なら次段階で、予測クラスごとに既存の1頭=v110 7点、3/4/5頭=現行相手選びを接続し、Jun-Aug固定ホールドアウトで3連単ROIを比較する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
