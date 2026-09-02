import csv
rows=[]
with open('bets_v8.csv',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r.get('hit')=='1': rows.append(r)
L=['# v8 的中レース一覧','', '|日付|場|R|頭|買い目|score|事前オッズ|EV|投資額|確定払戻/100円|実回収|レース合成オッズ|点数|', '|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    L.append(f"|{r['date']}|{r['venue']}|{r['race']}|{r['head']}|{r['combo']}|{float(r['score']):.2f}|{float(r['odds_pre']):.1f}倍|{float(r['ev_pre']):.3f}|{int(float(r['stake_v8'])):,}円|{int(float(r['payout'])):,}円|{int(float(r['return_v8'])):,}円|{float(r['composite_odds_race']):.2f}倍|{r['tickets_race']}|")
L += ['',f'- 的中数: {len(rows)}',f"- 的中買い目への投資合計: {sum(int(float(r['stake_v8'])) for r in rows):,}円",f"- 的中買い目の回収合計: {sum(int(float(r['return_v8'])) for r in rows):,}円"]
open('hits_v8.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
