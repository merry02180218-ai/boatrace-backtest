from __future__ import annotations
import csv,re
import numpy as np
from datetime import date
import predict_v138_20260906_pre_allmodels as v138
import predict_v107_20260905_official_fullscan as v107
from backtest import rows, race_features

HD='20260906'; YMD='2026/09/06'; JCD='01'
OUT='pred_v139_20260906_kiryu_special.csv'
SUMMARY='prediction_v139_20260906_kiryu_special.md'
v107.HD=HD


def rno_from(x):
    m=re.search(r'\d+',str(x or ''))
    return int(m.group()) if m else 0


def rule_scores(r):
    x=r['lanes']; a,b,c,d,e=x[1],x[2],x[3],x[4],x[5]
    s3=v107.strength(c); se3=v107.st_edge(b,c); ww2=v107.wallweak(b,c); iw1=v107.c01((7.5-a['waku_wr'])/6)
    s4=v107.strength(d); se4=v107.st_edge(c,d); ww3=v107.wallweak(c,d)
    atk4=v107.c01(.40*se4+.35*ww3+.25*s4); resist=v107.resistance12(x); s5=v107.strength(e)
    defs={
      '3まくり':(3,{'3選手力':(s3,.50),'3_ST優位':(se3,.55),'2壁弱さ':(ww2,.55)}),
      '3まくり差し':(3,{'3選手力':(s3,.50),'3_ST優位':(se3,.45),'1弱さ':(iw1,.45),'2壁弱さ':(ww2,.45)}),
      '4カドまくり':(4,{'4選手力':(s4,.50),'4_ST優位':(se4,.55),'3壁弱さ':(ww3,.55)}),
      '5頭展開':(5,{'4攻撃力_非motor':(atk4,.55),'1_2抵抗力':(resist,.55),'5選手力':(s5,.50)}),
    }
    out={}
    for model,(head,ru) in defs.items():
        vals={k:v for k,(v,th) in ru.items()}; margins=[v-th for v,th in ru.values()]
        out[model]={'head':head,'score':100*sum(vals.values())/len(vals),'min_margin':min(margins),'pass':all(m>=0 for m in margins)}
    return out


def main():
    # official Kiryu 12R + prior-frame history, all pre-exhibition
    names=v107.racer_names(); races=[]
    for rno in range(1,13): races.append(v107.parse_race(JCD,rno,names))
    lookup=v138.load_waku_history(); v107.attach_waku(races,lookup)
    by_r={r['rno']:r for r in races}

    # legacy 1-head PRE on every Kiryu race (not only daily top5)
    model=v138.fit_legacy(); cards=rows(f'data/programs/race_cards/{YMD}.csv'); w10=rows(f'data/programs/waku10/{YMD}.csv'); wm={r.get('レースコード',''):r for r in w10}
    pre={}
    for rr in cards:
        if str(rr.get('レース場コード','')).zfill(2)!=JCD: continue
        rn=rno_from(rr.get('レース回'))
        if rn<1 or rn>12: continue
        x=race_features(rr,wm.get(rr.get('レースコード',''),{}))
        X=np.asarray([v138.legacy_row_from_x(x,JCD)],float)
        pre[rn]=(float(model.predict_proba(X)[0,1]),x[1]['name'],x[1]['grade'])

    # global Kiryu rank of 1-head PRE for context; production daily top5 is across all venues, so this is only special venue diagnostic
    ranks={rn:i+1 for i,(rn,_) in enumerate(sorted(pre.items(),key=lambda kv:-kv[1][0]))}
    rows_out=[]
    for rn in range(1,13):
        r=by_r[rn]; sc=rule_scores(r); p,nm,g=pre.get(rn,(float('nan'),r['lanes'][1]['name'],r['lanes'][1]['grade']))
        passed=[m for m,z in sc.items() if z['pass']]
        rows_out.append({
          'race':rn,'deadline':r['deadline'],'one_name':nm,'one_grade':g,'one_pre':p*100,'one_kiryu_rank':ranks.get(rn,''),
          'm3_score':sc['3まくり']['score'],'m3_margin':sc['3まくり']['min_margin'],'m3_pass':int(sc['3まくり']['pass']),
          'm3s_score':sc['3まくり差し']['score'],'m3s_margin':sc['3まくり差し']['min_margin'],'m3s_pass':int(sc['3まくり差し']['pass']),
          'm4_score':sc['4カドまくり']['score'],'m4_margin':sc['4カドまくり']['min_margin'],'m4_pass':int(sc['4カドまくり']['pass']),
          'm5_score':sc['5頭展開']['score'],'m5_margin':sc['5頭展開']['min_margin'],'m5_pass':int(sc['5頭展開']['pass']),
          'passed_models':'/'.join(passed) if passed else '-'
        })
    fields=list(rows_out[0].keys())
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows_out)

    L=['# v139 2026-09-06 桐生 特別全12R事前検証','',
       '- 今回だけ桐生を全12R横断。**展示前データのみ**で、結果・払戻・実進入・当日展示・当日オッズは不使用。',
       '- ①頭は現行Legacy PRE確率を全12Rに算出（通常運用の全場top5制約は外して診断表示）。',
       '- ③まくり/③まくり差し/④カド/⑤頭はv107現行構造ゲートを全12Rに適用。','',
       '|R|締切|①選手|①PRE|桐生内順位|通過モデル|③ま|③差|④カド|⑤頭|','|---:|---|---|---:|---:|---|---:|---:|---:|---:|']
    for z in rows_out:
        L.append(f"|{z['race']}R|{z['deadline']}|{z['one_name']}|{z['one_pre']:.1f}%|{z['one_kiryu_rank']}|{z['passed_models']}|{z['m3_score']:.1f}|{z['m3s_score']:.1f}|{z['m4_score']:.1f}|{z['m5_score']:.1f}|")
    L+=['','※非①のスコアは構造指数。ゲート通過は各構成条件の最低余裕が0以上のもの。①PREと非①構造指数は同一尺度ではない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
