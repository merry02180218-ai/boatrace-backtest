import csv
from collections import defaultdict

DATE='2026-08-27'
SRC='analysis_v64_three_month_strict_flow.csv'
OUT='summary_v65_20260827_twenty_tickets.md'


def combos(head, ranked):
    out=[]
    for ia,a in enumerate(ranked,1):
        for ib,b in enumerate(ranked,1):
            if a==b: continue
            # deterministic display score only; preserves separate 2nd/3rd rank information
            out.append((ia+0.7*ib, ia, ib, f'{head}-{a}-{b}'))
    out.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    return out


def main():
    with open(SRC,encoding='utf-8-sig') as f:
        rows=[r for r in csv.DictReader(f) if r.get('date')==DATE]
    # Actual operating candidates: A/S only. 3-head already route-consolidated in v64.
    cand=[r for r in rows if int(float(r.get('approved_A') or 0))==1]
    cand.sort(key=lambda r:(0 if int(r['head']) in (3,5) else 1,-float(r['score']),r['race_code']))
    L=['# v65 2026-08-27 頭固定20通りリプレイ','',
       'v64で結果確認前に固定済みの事前候補・直前score・頭・相手順位だけを使用して20通りを展開。',
       '3まくり/3まくり差しの重複はv64時点でscore上位へ統合済み。A=55以上、S=67以上。',
       '20通りは買い目を削るための参考順。2着順位をやや重くした表示順だが、全20通りを残す。結果はその後に照合。','',
       '## A/S頭候補一覧','|優先|レース|頭|モデル|評価|score|相手順位|結果|頭的中|決まり手|','|---|---|---:|---|---|---:|---|---|---:|---|']
    for r in cand:
        pri='主候補' if int(r['head']) in (3,5) else '観察'
        L.append(f"|{pri}|{r['race_code']}|{r['head']}|{r['model']}|{r['grade']}|{float(r['score']):.1f}|{r['ranked_others']}|{r.get('actual_combo','')}|{r.get('head_hit','')}|{r.get('kimarite','')}|")
    for r in cand:
        head=int(r['head']); ranked=[int(x) for x in r['ranked_others'].split('-') if x]
        cc=combos(head,ranked)
        L+=['',f"## {r['race_code']} — {r['model']} / {r['grade']} {float(r['score']):.1f} / 頭{head}",
            f"相手艇評価: **{' > '.join(map(str,ranked))}**",'',
            '|表示順|3連単|2着候補順位|3着候補順位|実結果一致|','|---:|---|---:|---:|---|']
        actual=r.get('actual_combo','')
        for j,(_,ir,jr,c) in enumerate(cc,1):
            L.append(f"|{j}|{c}|{ir}|{jr}|{'★' if c==actual else ''}|")
        if actual:
            rank=next((j for j,z in enumerate(cc,1) if z[3]==actual),None)
            L+=['',f"結果: **{actual}** / 頭的中: **{'○' if int(float(r.get('head_hit') or 0)) else '×'}** / 20通り内順位: **{rank if rank else '-'}位**"]
    open(OUT,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
