import csv
from collections import defaultdict
from analyze_v37_environment import collect, rate, MODELS, DIR

# v38: 各場の水面向きに対して、絶対風向を追い/向かい/左右横風へ正規化して検証。
# 風データは previews/sui の締切約5分前スナップショットのみ。事前候補抽出には使わない。
# 実進入・コース情報は一切使わない。
# facing_deg は BoatraceCSV の build_sui_params.py と同じ定義を使用。
# 同リポジトリでも一部は概算値と明記されているため、結果は「採用候補抽出」用途に限定する。

STADIUM_FACING = {
    '桐生':90,'戸田':0,'江戸川':200,'平和島':270,'多摩川':180,'浜名湖':90,
    '蒲郡':90,'常滑':270,'津':90,'三国':270,'びわこ':0,'住之江':0,
    '尼崎':0,'鳴門':0,'丸亀':0,'児島':0,'宮島':90,'徳山':0,
    '下関':0,'若松':0,'芦屋':0,'福岡':0,'唐津':0,'大村':0,
}
WIND_DEG={1:0,2:45,3:90,4:135,5:180,6:225,7:270,8:315}
REL_ORDER=['追い','右横','向かい','左横']
SPD=['0-2m','3-4m','5m+']

def relwind(z):
    wd=WIND_DEG.get(z.get('wind_code'))
    face=STADIUM_FACING.get(z.get('venue'))
    if wd is None or face is None:
        return 'missing',None
    rel=(wd-face)%360
    if rel < 45 or rel >= 315:return '追い',rel
    if 45 <= rel < 135:return '右横',rel
    if 135 <= rel < 225:return '向かい',rel
    return '左横',rel

def enrich(data):
    out=[]
    for z0 in data:
        z=dict(z0); rw,deg=relwind(z);z['relative_wind']=rw;z['relative_deg']=deg
        z['wind_cell']=rw+'_'+z.get('wind_bin','missing') if rw!='missing' else 'missing'
        out.append(z)
    return out

def stable_cells(data):
    post=[z for z in data if z['period'] in ('validation','latest_month')]
    out=[]
    for m in MODELS:
        for v in sorted({z['venue'] for z in data}):
            trbase=[z for z in data if z['period']=='train' and z['model']==m and z['venue']==v]
            pobase=[z for z in post if z['model']==m and z['venue']==v]
            if len(trbase)<18 or len(pobase)<10:continue
            _,_,tb=rate(trbase);_,_,pb=rate(pobase)
            for rw in REL_ORDER:
                for sp in SPD:
                    tr=[z for z in trbase if z['relative_wind']==rw and z['wind_bin']==sp]
                    po=[z for z in pobase if z['relative_wind']==rw and z['wind_bin']==sp]
                    if len(tr)<6 or len(po)<4:continue
                    _,_,r1=rate(tr);_,_,r2=rate(po)
                    d1=r1-tb;d2=r2-pb
                    same=(d1>0 and d2>0) or (d1<0 and d2<0)
                    if not same:continue
                    # サンプルが小さいので極端値だけで並べないよう、両期間の最低差を主評価にする
                    strength=min(abs(d1),abs(d2))
                    out.append((strength,m,v,rw,sp,len(tr),r1,tb,len(po),r2,pb,'↑' if d1>0 else '↓'))
    return sorted(out,reverse=True)

def aggregate_cells(data,period):
    rows=[]
    for m in MODELS:
        base=[z for z in data if z['period']==period and z['model']==m]
        _,_,br=rate(base)
        for rw in REL_ORDER:
            for sp in SPD:
                a=[z for z in base if z['relative_wind']==rw and z['wind_bin']==sp]
                n,h,r=rate(a)
                if n>=5:rows.append((m,rw,sp,n,h,r,br,r-br))
    return rows

def main():
    raw,q3=collect();data=enrich(raw)
    with open('analysis_v38_relative_wind.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in data))));w.writeheader();w.writerows(data)
    L=['# v38 場別・相対風向×風速 検証','',
       'v37の絶対方位を、各場の facing_deg 基準で「追い・向かい・右横・左横」に正規化。風は previews/sui の締切約5分前スナップショットなので、事前候補抽出には使わず直前補正専用。実進入・コース不使用。',
       '', '注意: facing_deg は BoatraceCSV build_sui_params.py と同じ値だが、同ソースで一部は概算値と明記されている。よって本v38は直前補正候補の探索であり、場別採用前に方向定義の確認が必要。',
       '',f'4刺され counter4 学習Q3={q3:.3f}','']
    for p in ['train','validation','latest_month']:
        L += [f'## {p} 相対風向×風速','|モデル|相対風向|風速|R|狙い成立|成立率|モデル全体率|差|','|---|---|---|---:|---:|---:|---:|---:|']
        for m,rw,sp,n,h,r,br,diff in aggregate_cells(data,p):
            L.append(f'|{m}|{rw}|{sp}|{n}|{h}|{r:.1f}%|{br:.1f}%|{diff:+.1f}pt|')
    st=stable_cells(data)
    L += ['','## 場別で学習→後半が同方向だった相対風条件','|モデル|場|相対風向|風速|学習R|学習率|場ベース|後半R|後半率|場ベース|方向|','|---|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for x in st[:50]:
        _,m,v,rw,sp,n1,r1,b1,n2,r2,b2,ud=x
        L.append(f'|{m}|{v}|{rw}|{sp}|{n1}|{r1:.1f}%|{b1:.1f}%|{n2}|{r2:.1f}%|{b2:.1f}%|{ud}|')
    L += ['','## 採用判定ルール','- 風は直前補正専用。事前候補抽出には使わない。','- 全国一律補正より、場×相対風向×風速で学習・後半が同方向の条件を優先。','- 場別採用には facing_deg の方向確認と、今後の新規日での前向き検証を必須とする。','- 潮はv38でも未使用。過去に取得可能だった天文潮位予測値を別途用意できた場合のみ検証する。']
    open('summary_v38_relative_wind.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
