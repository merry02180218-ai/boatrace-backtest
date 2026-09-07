#!/usr/bin/env python3
"""v174: diagnose 2nd/3rd distributions by actual 3-head winning development type.

This is diagnostic only. It uses actual result / winning method after the race, so it is NOT a predictive feature test.
The purpose is to see whether 3-head races should later be modeled with separate pre-race probabilities
for makuri / makuri-sashi / other developments.
"""
import csv
from collections import Counter,defaultdict
from analyze_v166_3head_pair_direct import read, combo, ii, SRC

OUT='analysis_v174_3head_development_type_diagnostics.csv'
SUMMARY='summary_v174_3head_development_type_diagnostics.md'

METHOD_KEYS=['kimarite','winning_method','win_method','decision','kime','race_kimarite','actual_kimarite']

def norm_method(r):
    raw=''
    used=''
    for k in METHOD_KEYS:
        if str(r.get(k,'')).strip():
            raw=str(r.get(k,'')).strip(); used=k; break
    s=raw.replace(' ','').replace('　','')
    sl=s.lower()
    if 'まくり差し' in s or '捲り差し' in s or 'makurizashi' in sl or 'makuri-sashi' in sl:
        return 'makuri-sashi',raw,used
    if 'まくり' in s or '捲り' in s or ('makuri' in sl and 'sashi' not in sl):
        return 'makuri',raw,used
    if '差し' in s or 'sashi' in sl:
        return 'sashi-other',raw,used
    if raw:
        return 'other-known',raw,used
    return 'unknown','',used

def pct(n,d): return 100*n/d if d else 0.0

def fmt(c):
    return ' '.join(f'{k}:{v}' for k,v in sorted(c.items()))

def main():
    rows=read(SRC)
    heads=[]
    key_counts=Counter(); raw_counts=Counter(); type_counts=Counter()
    stats=defaultdict(lambda:{'n':0,'second':Counter(),'third':Counter(),'second_inner':0,'third_outer':0})
    for r in rows:
        if ii(r.get('valid_result'))!=1: continue
        a=combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=3: continue
        typ,raw,key=norm_method(r)
        if key:key_counts[key]+=1
        if raw:raw_counts[raw]+=1
        type_counts[typ]+=1
        s,t=a[1],a[2]
        q=stats[typ];q['n']+=1;q['second'][s]+=1;q['third'][t]+=1
        q['second_inner']+=int(s in [1,2]);q['third_outer']+=int(t in [4,5,6])
        heads.append((typ,s,t,raw,key))
    out=[]
    for typ,q in sorted(stats.items(),key=lambda kv:(-kv[1]['n'],kv[0])):
        n=q['n']
        top2=q['second'].most_common(1)[0][0] if q['second'] else ''
        top3=q['third'].most_common(1)[0][0] if q['third'] else ''
        out.append({'type':typ,'R':n,'share':pct(n,len(heads)),'top2':top2,'top3':top3,
                    'second_inner12':pct(q['second_inner'],n),'third_outer456':pct(q['third_outer'],n),
                    'second_dist':fmt(q['second']),'third_dist':fmt(q['third'])})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=['type','R','share','top2','top3','second_inner12','third_outer456','second_dist','third_dist']
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v174 ③1着・実展開タイプ別 2着3着診断','',
       '- 実際に③が1着になったレースだけを対象。','- この検証は結果後の決まり手を使う**診断**であり、予測モデルへの直接投入ではない。',
       '- 目的は、まくり／まくり差し等で2着3着分布が十分に違うかを確認し、次に事前の展開確率モデルを作る価値を判定する。','',
       f'- ③頭レース総数: {len(heads)}',f'- 決まり手取得キー: {dict(key_counts)}',
       f'- raw決まり手上位: {raw_counts.most_common(12)}','',
       '|type|R|share|2着最多|3着最多|2着内(1,2)|3着外(4,5,6)|','|---|---:|---:|---:|---:|---:|---:|']
    for r in out:
        L.append(f"|{r['type']}|{r['R']}|{r['share']:.1f}%|{r['top2']}|{r['top3']}|{r['second_inner12']:.1f}%|{r['third_outer456']:.1f}%|")
    L+=['','## 詳細分布']
    for r in out:
        L.append(f"- {r['type']}: 2着 {r['second_dist']} / 3着 {r['third_dist']}")
    L+=['','## 判定','- まくりとまくり差しで2着・3着分布が明確に違えば、次段階は「事前の展開タイプ確率」を作り、v166 pair scoreへsoftに混ぜてOOS比較する。','- unknownが大半なら、現行データに決まり手列がなく、この方向は別データ結合が必要。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__': main()
