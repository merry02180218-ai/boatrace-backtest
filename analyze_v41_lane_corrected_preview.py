import csv
from collections import defaultdict
from analyze_v37_environment import collect, MODELS
from analyze_v23_20260902_daypreview import by_code, rank_score
from backtest_v34_tilt_compare import f

# User-provided lane corrections. Applied before ranking; lower corrected time is better.
CORR={
 'ex':{1:.02,2:.01,3:0,4:-.01,5:-.01,6:-.02},
 'lap':{1:.40,2:.30,3:.20,4:.10,5:.05,6:0},
 'turn':{1:.20,2:.10,3:0,4:-.05,5:-.10,6:-.15},
 'straight':{1:0,2:0,3:0,4:-.01,5:-.02,6:-.02},
}
GROUP={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'4刺され':4,'5頭展開':5}

def corrected_rank(vals,boat,kind):
    vv={b:(None if vals.get(b) is None else vals[b]+CORR[kind][b]) for b in range(1,7)}
    return rank_score(vv,boat,True)

def orig_values(r,kind):
    if not r:return {b:None for b in range(1,7)}
    labels=[r.get('計測項目1',''),r.get('計測項目2',''),r.get('計測項目3','')]
    idx=None
    for k,label in enumerate(labels,1):
        lab=(label or '').replace(' ','').replace('　','')
        if kind=='straight' and '直線' in lab:idx=k
        elif kind=='turn' and ('まわり' in lab or '回り' in lab or 'ターン' in lab):idx=k
        elif kind=='lap' and ('一周' in lab or 'ラップ' in lab or ('周' in lab and '周回' not in lab)):idx=k
    return {b:(f(r.get(f'艇{b}_値{idx}')) if idx else None) for b in range(1,7)}

def add(data):
    cache={}
    for z in data:
        day=z['date']; ymd=day.replace('-','/')
        if day not in cache: cache[day]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/original_exhibition/{ymd}.csv'))
        tkz,orig=cache[day]; code=z['race_code']; b=GROUP[z['model']]; tr=tkz.get(code,{}); oo=orig.get(code,{})
        ex={j:f(tr.get(f'艇{j}_展示タイム')) for j in range(1,7)}
        z['ex_raw']=rank_score(ex,b,True); z['ex_corr']=corrected_rank(ex,b,'ex')
        for k in ['lap','turn','straight']:
            vals=orig_values(oo,k); z[k+'_raw']=rank_score(vals,b,True); z[k+'_corr']=corrected_rank(vals,b,k)
    return data

def stat(a,key,cut=.60):
    g=[x for x in a if x[key]>=cut]; n=len(g); h=sum(x['target'] for x in g); return n,100*h/n if n else 0

def main():
    data,q3=collect(); data=add(data)
    with open('analysis_v41_lane_corrected_preview.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=sorted(set().union(*(x.keys() for x in data))));w.writeheader();w.writerows(data)
    L=['# v41 枠番補正 展示/オリジナル展示 検証','',
       'ユーザー提示の枠番補正値を各タイムへ加算してから艇間順位化。実進入・艇N_コース不使用。展示後補正専用。','',
       '補正: 展示 [+.02,+.01,0,-.01,-.01,-.02] / 一周 [+.40,+.30,+.20,+.10,+.05,0] / 回り足 [+.20,+.10,0,-.05,-.10,-.15] / 直線 [0,0,0,-.01,-.02,-.02]','']
    for p in ['train','validation','latest_month']:
      L += [f'## {p}','|モデル|項目|無補正 上位40% R/率|枠補正 上位40% R/率|差|','|---|---|---:|---:|---:|']
      for m in MODELS:
       a=[x for x in data if x['period']==p and x['model']==m]
       for k,jp in [('ex','展示'),('lap','一周'),('turn','回り足'),('straight','直線')]:
        n,r=stat(a,k+'_raw'); n2,r2=stat(a,k+'_corr'); L.append(f'|{m}|{jp}|{n}R / {r:.1f}%|{n2}R / {r2:.1f}%|{r2-r:+.1f}pt|')
    # Model-specific composites suggested by tactical meaning; compare raw/corrected on identical weights.
    W={
      '3まくり':{'ex':.40,'straight':.35,'lap':.10,'turn':.15},
      '3まくり差し':{'ex':.15,'straight':.10,'lap':.35,'turn':.40},
      '4カドまくり':{'ex':.40,'straight':.40,'lap':.05,'turn':.15},
      '4刺され':{'ex':.15,'straight':.10,'lap':.35,'turn':.40},
      '5頭展開':{'ex':.15,'straight':.10,'lap':.35,'turn':.40},
    }
    for x in data:
      w=W[x['model']]; x['comp_raw']=sum(w[k]*x[k+'_raw'] for k in w); x['comp_corr']=sum(w[k]*x[k+'_corr'] for k in w)
    L += ['','## モデル別総合展示 上位40%','|期間|モデル|無補正 R/率|枠補正 R/率|差|','|---|---|---:|---:|---:|']
    for p in ['train','validation','latest_month']:
      for m in MODELS:
       a=[x for x in data if x['period']==p and x['model']==m]; n,r=stat(a,'comp_raw'); n2,r2=stat(a,'comp_corr'); L.append(f'|{p}|{m}|{n}R / {r:.1f}%|{n2}R / {r2:.1f}%|{r2-r:+.1f}pt|')
    L += ['','## 判定方針','- 学習だけ改善して検証/最新で悪化する補正は採用しない。','- 枠補正は生タイムの順位化前に適用する。','- 展示/オリジナル展示は候補抽出ではなく展示後の格上げ・格下げに使う。','- 画像記載の全場平均1着率（展示25.2%、一周40.7%、回り足41.2%、直線13.4%）は参考情報とし、当モデルの重みはバックテスト結果を優先する。']
    open('summary_v41_lane_corrected_preview.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
