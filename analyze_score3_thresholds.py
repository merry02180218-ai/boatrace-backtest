import csv
from collections import defaultdict

SRC='candidates_v4.csv'
THRESH=[60,65,70,75,80]

with open(SRC,encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))
rs=[r for r in rows if r.get('model')=='3攻め']

def pct(a,b):
    return (100*a/b) if b else 0.0

L=['# 3号艇 まくり/まくり差しモデル 検証（2026-08-03〜2026-09-02）','',
   'candidates_v4.csv の事前固定済み3攻め候補だけを使用。頭的中は「3号艇1着かつ決まり手=まくり/まくり差し」。結果は候補固定後に付与済み。','',
   '## スコア閾値別','|閾値|候補数|3頭的中|頭的中率|3号艇2連関与|関与率|','|---|---:|---:|---:|---:|---:|']
for th in THRESH:
    a=[r for r in rs if float(r['score'])>=th]
    h=sum(int(r['head_hit']) for r in a); iv=sum(int(r['involved_hit']) for r in a)
    L.append(f'|{th}以上|{len(a)}|{h}|{pct(h,len(a)):.1f}%|{iv}|{pct(iv,len(a)):.1f}%|')

L+=['','## 日次×スコア70以上','|日次|候補数|頭的中|頭的中率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|']
a70=[r for r in rs if float(r['score'])>=70]
for dc in ['初日','2日目','3日目以降']:
    a=[r for r in a70 if r['day_cat']==dc];h=sum(int(r['head_hit']) for r in a);iv=sum(int(r['involved_hit']) for r in a)
    L.append(f'|{dc}|{len(a)}|{h}|{pct(h,len(a)):.1f}%|{iv}|{pct(iv,len(a)):.1f}%|')

L+=['','## 足質×スコア70以上','|足質|候補数|頭的中|頭的中率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|']
for ft in ['伸び寄り','バランス','出足・回り足寄り']:
    a=[r for r in a70 if r['foot_type']==ft];h=sum(int(r['head_hit']) for r in a);iv=sum(int(r['involved_hit']) for r in a)
    L.append(f'|{ft}|{len(a)}|{h}|{pct(h,len(a)):.1f}%|{iv}|{pct(iv,len(a)):.1f}%|')

hits=[r for r in rs if int(r['head_hit'])==1]
L+=['','## 的中レース一覧','|日付|場|R|score|ランク|選手|決まり手|足質|','|---|---:|---:|---:|---|---|---|---|']
for r in sorted(hits,key=lambda x:(x['date'],x['race_code'])):
    L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{float(r['score']):.2f}|{r['rank']}|{r['target_name']}|{r['kimarite']}|{r['foot_type']}|")

# score bands to see concentration
L+=['','## スコア帯別','|スコア帯|候補|頭的中|頭率|','|---|---:|---:|---:|']
for lo,hi in [(60,65),(65,70),(70,75),(75,80),(80,101)]:
    a=[r for r in rs if lo<=float(r['score'])<hi];h=sum(int(r['head_hit']) for r in a)
    lab=f'{lo}-{hi-0.01:.2f}' if hi<101 else '80以上'
    L.append(f'|{lab}|{len(a)}|{h}|{pct(h,len(a)):.1f}%|')

open('summary_score3.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
