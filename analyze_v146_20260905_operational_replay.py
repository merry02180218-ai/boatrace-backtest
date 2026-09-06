from __future__ import annotations
import csv
from datetime import date
import numpy as np

from backtest import rows, race_features
import predict_v107_20260905_official_fullscan as v107
import predict_v138_20260906_pre_allmodels as v138
import analyze_v141_integrated_pre_scenario as v141
import analyze_v142_balanced_pre_scenario as v142
import analyze_v144_pre_final_scenario as v144
import analyze_v145_one_gate_specialized_non1 as v145

if not hasattr(v142,'fit_mode'):
    v142.fit_mode=v142.fit_model

YMD='2026/09/05'
ISO='2026-09-05'
OUT='analysis_v146_20260905_operational_replay.csv'
SUMMARY='summary_v146_20260905_operational_replay.md'
PRE_NON1='pred_v107_20260905_official_fullscan.csv'
GATE=.40
CLASSES=v141.CLASSES
NON1=[c for c in CLASSES if c!='1逃げ']


def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def pmap(model,x,classes):
    p=model.predict_proba(np.asarray([x],float))[0]
    cs=list(model.named_steps['lr'].classes_)
    return {c:(float(p[cs.index(c)]) if c in cs else 0.0) for c in classes}


def current_feature(card,w10,m141,m142,one,stbias,cache):
    code=card.get('レースコード',''); venue=str(card.get('レース場コード','')).zfill(2)
    x=race_features(card,w10.get(code,{}))
    op=float(one.predict_proba(np.asarray([v138.legacy_row_from_x(x,venue)],float))[0,1])
    sc=v141.structural(x); fv=v141.feature_vec(op,sc,venue)
    a=v144.pmap(m141,fv); b=v144.pmap(m142,fv)
    pre='1逃げ' if a['1逃げ']>=.45 else max(NON1,key=lambda c:b[c])
    src=1 if pre=='1逃げ' else 0
    dv=v144.direct_vec({'date':ISO,'race_code':code},stbias,cache)
    if dv is None:return None
    xf=list(fv)+[a[c] for c in CLASSES]+[b[c] for c in CLASSES]+[1.0 if pre==c else 0.0 for c in CLASSES]+[float(src)]+dv
    return {'xf':xf,'one_pre':op,'pre143':pre,'venue':venue,'race':v141.rno(card.get('レース回')),'code':code}


def main():
    # 1) Build/freeze PRE candidate set without reading Sep5 results.
    cards=rows(f'data/programs/race_cards/{YMD}.csv')
    w10={r.get('レースコード',''):r for r in rows(f'data/programs/waku10/{YMD}.csv')}
    one=v138.fit_legacy()
    one_scores=[]
    card_by_key={}
    for card in cards:
        code=card.get('レースコード','')
        if not code:continue
        try:x=race_features(card,w10.get(code,{}))
        except:continue
        venue=str(card.get('レース場コード','')).zfill(2); rn=v141.rno(card.get('レース回'))
        card_by_key[(venue,rn)]=card
        p=float(one.predict_proba(np.asarray([v138.legacy_row_from_x(x,venue)],float))[0,1])
        one_scores.append((p,venue,rn,code,x[1]['name']))
    top5=sorted(one_scores,reverse=True)[:5]
    pre={}
    for p,venue,rn,code,name in top5:
        pre[(venue,rn)]={'pre_source':'1頭Legacy top5','pre_model':'1頭','pre_score':100*p,'pre_name':name}
    for r in read_csv(PRE_NON1):
        key=(str(r.get('jcd','')).zfill(2),int(float(r.get('race',0))))
        z=pre.setdefault(key,{'pre_source':'','pre_model':'','pre_score':'','pre_name':''})
        add=r.get('routes','')
        z['pre_source']=(z['pre_source']+' + ' if z['pre_source'] else '')+'v107構造候補'
        z['pre_model']=(z['pre_model']+' / ' if z['pre_model'] else '')+add
        z['pre_score']=r.get('struct_index','') if not z['pre_score'] else z['pre_score']
        z['pre_name']=r.get('name','') if not z['pre_name'] else z['pre_name']

    # 2) Train only on <= Aug31 history, then add Sep5 direct/exhibition and freeze v145 FINAL.
    rs=v141.build_history()
    hist=v144.build_final_rows(rs,.45,v141.TRAIN_END)
    gate=v145.fit_gate(hist,v141.END); non1=v145.fit_non1(hist,v141.END)
    m141=v141.fit_integrated(rs,v141.END); m142=v142.fit_model(rs,v141.END,'capped2')
    stbias=v144.v51.learn_st_frame_bias(); cache={}
    frozen=[]
    for key,meta in sorted(pre.items(),key=lambda kv:kv[0]):
        card=card_by_key.get(key)
        if not card:continue
        f=current_feature(card,w10,m141,m142,one,stbias,cache)
        if f is None:
            frozen.append({**meta,'jcd':key[0],'race':key[1],'race_code':card.get('レースコード',''),'final':'NO_DIRECT','confidence':'','gate_p1':'','branch':'missing-direct'})
            continue
        pg=float(gate.predict_proba(np.asarray([f['xf']],float))[0,1])
        if pg>=GATE:
            pred='1逃げ'; conf=pg; branch='1-gate'
        else:
            pn=pmap(non1,f['xf'],NON1); pred=max(NON1,key=lambda c:pn[c]); conf=(1-pg)*pn[pred]; branch='non1-specialized'
        frozen.append({**meta,'jcd':key[0],'race':key[1],'race_code':f['code'],'one_pre':100*f['one_pre'],'pre143':f['pre143'],'final':pred,'confidence':100*conf,'gate_p1':100*pg,'branch':branch})

    # 3) Only after FINAL is frozen, load Sep5 results for settlement.
    res={r.get('レースコード',''):r for r in rows(f'data/results/realtime/{YMD}.csv')}
    def h(c):return {'1逃げ':1,'3まくり':3,'3まくり差し':3,'4カド':4,'5頭':5}.get(c,0)
    for z in frozen:
        rr=res.get(z.get('race_code',''))
        actual=v141.actual_class(rr) if rr else ''
        z['actual']=actual
        z['scenario_hit']=int(z.get('final')==actual) if actual and z.get('final')!='NO_DIRECT' else ''
        z['head_hit']=int(h(z.get('final'))!=0 and h(z.get('final'))==h(actual)) if actual and z.get('final')!='NO_DIRECT' else ''

    fields=['jcd','race','race_code','pre_source','pre_model','pre_score','pre_name','one_pre','pre143','final','confidence','gate_p1','branch','actual','scenario_hit','head_hit']
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:z.get(k,'') for k in fields} for z in frozen])

    valid=[z for z in frozen if z.get('actual') and z.get('final')!='NO_DIRECT']
    sh=sum(int(z['scenario_hit']) for z in valid); hh=sum(int(z['head_hit']) for z in valid)
    L=['# v146 2026-09-05 実運用型リプレイ','',
       '- PRE候補を先に固定: ①Legacy PRE top5 + 当日保存済みv107非①構造候補。','- その候補だけに9/5展示タイム・展示ST・オリジナル展示を追加してv145 FINALを凍結。','- 結果CSVはFINAL凍結後にのみ読み、的中確認に使用。','- 学習は8/31以前だけ。9/5結果・払戻・締切後オッズは予測特徴に不使用。','',
       f'- PRE候補 union: **{len(pre)}R** / 直前判定可能: **{len(valid)}R**',
       f'- 展開Top1: **{sh}/{len(valid)} ({100*sh/len(valid) if valid else 0:.1f}%)**',
       f'- 頭一致: **{hh}/{len(valid)} ({100*hh/len(valid) if valid else 0:.1f}%)**','',
       '## レース別','|場コード|R|PRE|FINAL|確信度|gate①|実結果展開|展開○×|頭○×|','|---:|---:|---|---|---:|---:|---|---:|---:|']
    for z in sorted(frozen,key=lambda z:(z['jcd'],z['race'])):
        conf=f"{float(z['confidence']):.1f}%" if z.get('confidence') not in ('',None) else '-'
        gp=f"{float(z['gate_p1']):.1f}%" if z.get('gate_p1') not in ('',None) else '-'
        L.append(f"|{z['jcd']}|{z['race']}R|{z['pre_model']}|{z['final']}|{conf}|{gp}|{z.get('actual','')}|{z.get('scenario_hit','')}|{z.get('head_hit','')}|")
    L += ['','## 注意','- これはv145の「PRE→直前→結果」の運用再現。まだ各分岐の既存買い目ロジックは接続していないので、ROI検証ではない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
