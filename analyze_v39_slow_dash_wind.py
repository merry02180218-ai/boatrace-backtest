import csv
from collections import defaultdict
from analyze_v38_relative_wind import enrich, rate, REL_ORDER, SPD
from analyze_v37_environment import collect, MODELS

# v39: 風の影響を「スロー攻撃(3)」「ダッシュ攻撃(4/5)」の構造で検証。
# 実進入は締切後なので一切使用しない。枠なり想定の戦術グループとしてのみ扱う。
# 風は previews/sui の締切約5分前スナップショットで、直前補正専用。
GROUP={'3まくり':'スロー3攻め','3まくり差し':'スロー3攻め',
       '4カドまくり':'ダッシュ4攻め','4刺され':'ダッシュ4攻め','5頭展開':'ダッシュ5展開'}

def agg(data, period, group):
    a=[z for z in data if z['period']==period and GROUP.get(z['model'])==group]
    n,h,b=rate(a)
    rows=[]
    for rw in REL_ORDER:
        for sp in SPD:
            x=[z for z in a if z['relative_wind']==rw and z['wind_bin']==sp]
            nn,hh,r=rate(x)
            if nn>=5: rows.append((rw,sp,nn,hh,r,b,r-b))
    return n,h,b,rows

def stable(data,group):
    post=[z for z in data if z['period'] in ('validation','latest_month') and GROUP.get(z['model'])==group]
    tr=[z for z in data if z['period']=='train' and GROUP.get(z['model'])==group]
    _,_,tb=rate(tr); _,_,pb=rate(post)
    out=[]
    for rw in REL_ORDER:
        for sp in SPD:
            a=[z for z in tr if z['relative_wind']==rw and z['wind_bin']==sp]
            b=[z for z in post if z['relative_wind']==rw and z['wind_bin']==sp]
            if len(a)<15 or len(b)<10: continue
            _,_,r1=rate(a); _,_,r2=rate(b); d1=r1-tb; d2=r2-pb
            if d1*d2<=0: continue
            out.append((min(abs(d1),abs(d2)),rw,sp,len(a),r1,tb,len(b),r2,pb,'↑' if d1>0 else '↓'))
    return sorted(out,reverse=True)

def matchup(data,period):
    # 同じ風セルでスロー3攻めとダッシュ4/5側の成立率差を比較
    rows=[]
    slow=[z for z in data if z['period']==period and GROUP.get(z['model'])=='スロー3攻め']
    dash=[z for z in data if z['period']==period and GROUP.get(z['model']) in ('ダッシュ4攻め','ダッシュ5展開')]
    _,_,sb=rate(slow); _,_,db=rate(dash)
    for rw in REL_ORDER:
        for sp in SPD:
            s=[z for z in slow if z['relative_wind']==rw and z['wind_bin']==sp]
            d=[z for z in dash if z['relative_wind']==rw and z['wind_bin']==sp]
            ns,hs,rs=rate(s); nd,hd,rd=rate(d)
            if ns>=10 and nd>=10: rows.append((rw,sp,ns,rs,rs-sb,nd,rd,rd-db,(rd-db)-(rs-sb)))
    return rows

def main():
    raw,q3=collect(); data=enrich(raw)
    with open('analysis_v39_slow_dash_wind.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in data))));w.writeheader();w.writerows(data)
    L=['# v39 スロー/ダッシュ × 相対風向×風速 検証','',
       '重要: 実進入・艇N_コースは不使用。ここでのスロー/ダッシュは実進入ではなく、3号艇攻め=スロー側、4/5号艇攻め=ダッシュ側という事前の戦術グループ。風は締切約5分前の直前補正専用。','',f'4刺され counter4 学習Q3={q3:.3f}','']
    groups=['スロー3攻め','ダッシュ4攻め','ダッシュ5展開']
    for p in ['train','validation','latest_month']:
        L += [f'## {p}']
        for g in groups:
            n,h,b,rows=agg(data,p,g)
            L += [f'### {g}（全体 {n}R / {b:.1f}%）','|相対風|風速|R|成立|成立率|全体差|','|---|---|---:|---:|---:|---:|']
            for rw,sp,nn,hh,r,bb,diff in rows:L.append(f'|{rw}|{sp}|{nn}|{hh}|{r:.1f}%|{diff:+.1f}pt|')
        L += ['### スロー3 vs ダッシュ4/5 相対比較','|相対風|風速|スローR|スロー率|スロー全体差|ダッシュR|ダッシュ率|ダッシュ全体差|ダッシュ相対優位|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
        for rw,sp,ns,rs,sd,nd,rd,dd,edge in matchup(data,p):
            L.append(f'|{rw}|{sp}|{ns}|{rs:.1f}%|{sd:+.1f}pt|{nd}|{rd:.1f}%|{dd:+.1f}pt|{edge:+.1f}pt|')
    L += ['','## 学習→後半で方向一致した風セル','|グループ|相対風|風速|学習R|学習率|学習全体|後半R|後半率|後半全体|方向|','|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for g in groups:
        for _,rw,sp,n1,r1,b1,n2,r2,b2,ud in stable(data,g):
            L.append(f'|{g}|{rw}|{sp}|{n1}|{r1:.1f}%|{b1:.1f}%|{n2}|{r2:.1f}%|{b2:.1f}%|{ud}|')
    L += ['','## 採用ルール','- 実進入は使わない。3=スロー攻撃側、4/5=ダッシュ攻撃側という事前戦術分類のみ。','- 風は直前補正専用で、事前候補抽出・事前ランクには使わない。','- 学習→後半で同方向かつ十分なR数があるセルだけ補正候補。','- モデル別の最終補正はv39のグループ傾向とv38の場別傾向が同方向の時だけ強める。']
    open('summary_v39_slow_dash_wind.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
