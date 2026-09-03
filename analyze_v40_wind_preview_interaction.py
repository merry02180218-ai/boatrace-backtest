import csv
from collections import defaultdict
from analyze_v38_relative_wind import enrich, rate, REL_ORDER, SPD
from analyze_v37_environment import collect, MODELS
from backtest_v35_tilt_interaction import interaction_features
from analyze_v23_20260902_daypreview import by_code, original_scores, rank_score
from backtest_v34_tilt_compare import rows, f, tiltval

# v40: 相対風 × 展示ST × 直線 × チルト × スロー/ダッシュ。
# 実進入/艇N_コースは不使用。風は締切直前補正専用。
GROUP={'3まくり':'スロー3攻め','3まくり差し':'スロー3攻め','4カドまくり':'ダッシュ4攻め','4刺され':'ダッシュ4攻め','5頭展開':'ダッシュ5展開'}
BOAT={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'4刺され':4,'5頭展開':5}

def add_preview(data):
    cache={}
    for z in data:
        day=z['date']; code=z['race_code']; key=day
        if key not in cache:
            ymd=day.replace('-','/')
            cache[key]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
        tkz,stt,orig=cache[key]; b=BOAT[z['model']]
        tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
        t=tiltval(tr.get(f'艇{b}_チルト'))
        stvals={k:f(sr.get(f'艇{k}_スタート展示')) for k in range(1,7)}
        st=rank_score(stvals,b,True); straight=original_scores(orr,b)['straight']
        z['tilt']=t; z['st_rank']=st; z['straight_rank']=straight
        z['st_good']=int(st>=.60); z['straight_good']=int(straight>=.60); z['tilt_high']=int(t is not None and t>=.5)
        z['preview2']=int(z['st_good'] and z['straight_good'])
        z['preview3']=int(z['st_good'] and z['straight_good'] and z['tilt_high'])
    return data

def rr(a):
    n=len(a); h=sum(x['target'] for x in a); return n,h,100*h/n if n else 0

def main():
    raw,q3=collect(); data=add_preview(enrich(raw))
    with open('analysis_v40_wind_preview_interaction.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=sorted(set().union(*(x.keys() for x in data))));w.writeheader();w.writerows(data)
    L=['# v40 風×展示ST×直線×チルト×スロー/ダッシュ','',
       '実進入・艇N_コース不使用。3号艇攻め=スロー側、4/5号艇攻め=ダッシュ側という事前戦術分類。風は締切約5分前の直前補正専用。展示ST/直線/チルトも展示後補正。','',f'4刺され counter4 学習Q3={q3:.3f}','']
    for p in ['train','validation','latest_month']:
        L += [f'## {p}','|グループ|相対風|風速|全R|全率|ST+直線良好R|率|さらにチルト+.5R|率|','|---|---|---|---:|---:|---:|---:|---:|---:|']
        for g in ['スロー3攻め','ダッシュ4攻め','ダッシュ5展開']:
            base=[x for x in data if x['period']==p and GROUP.get(x['model'])==g]
            for rw in REL_ORDER:
                for sp in SPD:
                    a=[x for x in base if x['relative_wind']==rw and x['wind_bin']==sp]
                    n,h,r=rr(a)
                    if n<10: continue
                    b=[x for x in a if x['preview2']]; n2,h2,r2=rr(b)
                    c=[x for x in a if x['preview3']]; n3,h3,r3=rr(c)
                    L.append(f'|{g}|{rw}|{sp}|{n}|{r:.1f}%|{n2}|{r2:.1f}%|{n3}|{r3:.1f}%|')
    # training→post same direction, requiring useful sample in both sides for ST+straight
    L += ['','## 学習→後半で再現した複合シグナル','|グループ|風|風速|学習 全→複合|後半 全→複合|判定|','|---|---|---|---|---|---|']
    postnames=('validation','latest_month')
    for g in ['スロー3攻め','ダッシュ4攻め','ダッシュ5展開']:
      for rw in REL_ORDER:
       for sp in SPD:
        tr=[x for x in data if x['period']=='train' and GROUP.get(x['model'])==g and x['relative_wind']==rw and x['wind_bin']==sp]
        po=[x for x in data if x['period'] in postnames and GROUP.get(x['model'])==g and x['relative_wind']==rw and x['wind_bin']==sp]
        n,_,r=rr(tr); n2,_,r2=rr([x for x in tr if x['preview2']]); m,_,q=rr(po); m2,_,q2=rr([x for x in po if x['preview2']])
        if n>=30 and m>=20 and n2>=8 and m2>=5 and (r2-r)*(q2-q)>0:
            L.append(f'|{g}|{rw}|{sp}|{r:.1f}%→{r2:.1f}% ({n2}R)|{q:.1f}%→{q2:.1f}% ({m2}R)|{"加点候補" if r2>r else "減点候補"}|')
    L += ['','## 運用','- 事前候補抽出には風・展示・チルトを使わない。','- 展示後にST/直線/チルト、締切直前に相対風向/風速を追加する。','- 複合条件はサンプルが小さくなりやすいため、ハードゲートにせず格上げ/格下げの補助に限定する。','- 場別v38とスロー/ダッシュv39が同方向で、さらにv40複合シグナルも同方向の場合を最優先の直前補正候補とする。']
    open('summary_v40_wind_preview_interaction.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
