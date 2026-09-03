"""v49 one-day strict no-leak validation for 2026-09-01.
Freeze candidate membership/history score first from v46 output while intentionally ignoring its result-derived `target` column.
Only after frozen list is complete, load realtime results and payout CSVs.
ROI rule: target boat 1st fixed, all 20 permutations of other five boats, 100 yen each (2,000 yen/race).
"""
import csv
from collections import defaultdict
from backtest import rows

DAY='2026-09-01'
YMD='2026/09/01'
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
BOAT={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}

def target_hit(rr,m):
    try:w=int(float(rr.get('1着_艇番',0) or 0))
    except:w=0
    kim=(rr.get('決まり手') or '').replace(' ','').replace('　','')
    if m=='3まくり': return int(w==3 and kim=='まくり')
    if m=='3まくり差し': return int(w==3 and kim=='まくり差し')
    if m=='4カドまくり': return int(w==4 and kim=='まくり')
    return int(w==5)

def band(p):
    return '高' if p>=.7 else ('低' if p<=.3 else '中')

def rate(a,key):
    return 100*sum(x[key] for x in a)/len(a) if a else 0

def main():
    # PHASE 1: freeze candidates using PRE-RESULT fields only.
    frozen=[]
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['date']!=DAY: continue
            # CRITICAL: do not copy/read r['target'] here.
            p=float(r['history_pct'])
            frozen.append({
                'date':r['date'],'race_code':r['race_code'],'model':r['model'],
                'history_pct':p,'history_adjust':float(r['history_adjust']),'band':band(p)
            })

    # PHASE 2: only after candidate list is frozen, read outcomes/payouts.
    res={r['レースコード']:r for r in rows(f'data/results/realtime/{YMD}.csv')}
    pay={r['レースコード']:r for r in rows(f'data/results/payouts/{YMD}.csv')}

    out=[]
    for c in frozen:
        rr=res.get(c['race_code'],{}); pr=pay.get(c['race_code'],{}); boat=BOAT[c['model']]
        try:w=int(float(rr.get('1着_艇番',0) or 0))
        except:w=0
        try:payout=int(float(pr.get('3連単_払戻金',0) or 0))
        except:payout=0
        o=dict(c)
        o['winner']=w
        o['kimarite']=(rr.get('決まり手') or '').replace(' ','').replace('　','')
        o['target_hit']=target_hit(rr,c['model'])
        o['head_hit']=int(w==boat)
        o['trifecta_combo']=pr.get('3連単_組番','')
        o['trifecta_payout']=payout
        o['payout_missing']=int(not bool(pr) or not str(pr.get('3連単_払戻金','')).strip())
        o['invest']=2000
        o['return']=payout if o['head_hit'] else 0
        out.append(o)

    L=['# v49 2026-09-01 厳格ノーリーク1日検証','',
       '候補・履歴スコアを先に固定し、v46 CSVの結果由来 `target` 列は読み込まず破棄。固定完了後に初めて着順・払戻CSVをロード。',
       '買い方は狙い艇1着固定－相手5艇総流し20点×100円（1R 2,000円）。','',
       '|モデル|候補R|狙い成立|成立率|対象艇1着|頭率|投資|払戻|ROI|払戻欠損|履歴 高/中/低 成立率|',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for m in MODELS:
        q=[x for x in out if x['model']==m]
        inv=sum(x['invest'] for x in q); ret=sum(x['return'] for x in q)
        bs=[]
        for b in ['高','中','低']:
            z=[x for x in q if x['band']==b]
            bs.append(f"{b}{len(z)}R/{rate(z,'target_hit'):.1f}%")
        L.append(f"|{m}|{len(q)}|{sum(x['target_hit'] for x in q)}|{rate(q,'target_hit'):.1f}%|{sum(x['head_hit'] for x in q)}|{rate(q,'head_hit'):.1f}%|{inv:,}円|{ret:,}円|{100*ret/inv if inv else 0:.1f}%|{sum(x['payout_missing'] for x in q)}|{' / '.join(bs)}|")
    inv=sum(x['invest'] for x in out);ret=sum(x['return'] for x in out)
    L+=['',f'合計: {len(out)}候補 / 投資 {inv:,}円 / 払戻 {ret:,}円 / ROI {100*ret/inv if inv else 0:.1f}%','',
        '## 候補別','|race_code|model|履歴帯|履歴pct|1着|決まり手|狙い成立|3連単|配当|払戻|',
        '|---|---|---|---:|---:|---|---:|---|---:|---:|']
    for x in out:
        L.append(f"|{x['race_code']}|{x['model']}|{x['band']}|{x['history_pct']:.4f}|{x['winner']}|{x['kimarite']}|{x['target_hit']}|{x['trifecta_combo']}|{x['trifecta_payout']:,}円|{x['return']:,}円|")

    with open('validation_v49_20260901_no_leak.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()) if out else ['date']);w.writeheader();w.writerows(out)
    open('summary_v49_20260901_no_leak.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
