from backtest import *


def infer_day_from_slots(r):
    """Infer meeting day from already-recorded prior meeting slots in pre-race race_cards.
    If title 日次 is unavailable, highest populated D + 1 is the current day.
    This uses only pre-race information.
    """
    maxd=0
    for b in range(1,7):
        for d in range(1,8):
            any_slot=False
            for s in range(1,3):
                if (r.get(f'艇{b}_節D{d}走{s}_R番号') or '').strip():
                    any_slot=True
            if any_slot:
                maxd=max(maxd,d)
    return maxd+1 if maxd else 1


def main():
    candidates=[]; all_actual=Counter(); daily=START
    while daily<=END:
        ymd=daily.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        w10={r['レースコード']:r for r in rows(f'data/programs/waku10/{ymd}.csv')}
        titles={r['レースコード']:r for r in rows(f'data/programs/title/{ymd}.csv')}
        frozen=[]
        for r in cards:
            code=r['レースコード']; w=w10.get(code,{})
            x=race_features(r,w); s3=score3(x); s4=score4(x); s45=score45(x,s4)
            dn=daynum(titles.get(code,{}).get('日次','')) or infer_day_from_slots(r)
            daycat='初日' if dn==1 else ('2日目' if dn==2 else '3日目以降')
            for model,boat,sc in [('3攻め',3,s3),('4カド',4,s4),('4→5展開',5,s45)]:
                if sc>=60:
                    frozen.append({'date':str(daily),'race_code':code,'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_no':dn,'day_cat':daycat,'model':model,'target_boat':boat,'score':round(sc,2),'rank':label(sc),'target_name':x[boat]['name'],'target_grade':x[boat]['grade'],'motor2':x[boat]['motor2'],'target_waku_st':x[boat]['waku_st']})
        # Outcome load happens only after all candidates for the date are frozen.
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for rr in res.values():
            win=i(rr.get('1着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            if win==3 and kim in ('まくり','まくり差し'): all_actual['3攻め']+=1
            if win==4 and kim in ('まくり','まくり差し'): all_actual['4カド']+=1
            if win==5: all_actual['4→5展開']+=1
        for c in frozen:
            rr=res.get(c['race_code'],{})
            win=i(rr.get('1着_艇番')); second=i(rr.get('2着_艇番')); kim=(rr.get('決まり手') or '').replace('　','').replace(' ','')
            c['winner']=win; c['second']=second; c['kimarite']=kim
            if c['model']=='3攻め':
                c['head_hit']=int(win==3 and kim in ('まくり','まくり差し'))
                c['involved_hit']=int(win==3 or second==3)
            elif c['model']=='4カド':
                c['head_hit']=int(win==4 and kim in ('まくり','まくり差し'))
                c['involved_hit']=int(win==4 or second==4)
            else:
                c['head_hit']=int(win==5)
                c['involved_hit']=int(win==5 or second==5)
            candidates.append(c)
        daily+=timedelta(days=1)

    fields=list(candidates[0].keys()) if candidates else []
    with open('candidates.csv','w',newline='',encoding='utf-8-sig') as f1:
        w=csv.DictWriter(f1,fieldnames=fields); w.writeheader(); w.writerows(candidates)

    groups=defaultdict(lambda:[0,0,0])
    for c in candidates:
        if c['rank'] not in ('S','A'): continue
        keys=[(c['model'],'ALL'),(c['model'],c['day_cat']),(c['model']+'_'+c['rank'],c['day_cat'])]
        for key in keys:
            groups[key][0]+=1; groups[key][1]+=c['head_hit']; groups[key][2]+=c['involved_hit']

    lines=['# 2026-08-03〜2026-09-02 事前固定バックテスト v2','',
      '候補スコアは結果CSVを読み込む前に固定。titleの日次欠損時は、race_cardsに既に記録済みの節間過去走スロットだけから開催日次を推定。S/Aのみ主要集計。','',
      '|モデル|開催日次|候補数|頭的中|頭的中率|2連関与|関与率|','|---|---:|---:|---:|---:|---:|---:|']
    for (m,d),v in sorted(groups.items()):
        n,h,iv=v
        lines.append(f'|{m}|{d}|{n}|{h}|{h/n*100:.1f}%|{iv}|{iv/n*100:.1f}%|')

    # combined comparison for initial-day question
    lines += ['', '## 初日 vs 2日目 vs 3日目以降（S/A候補）']
    for model in ['3攻め','4カド','4→5展開']:
        vals=[]
        for dc in ['初日','2日目','3日目以降']:
            n,h,iv=groups.get((model,dc),(0,0,0))
            vals.append(f'{dc}: {n}件 / 頭{h} ({h/n*100:.1f}%) / 2連関与{iv} ({iv/n*100:.1f}%)' if n else f'{dc}: 0件')
        lines.append(f'- {model}: ' + ' | '.join(vals))

    lines += ['', '## 実際の発生数（期間全体）']
    for k,v in all_actual.items(): lines.append(f'- {k}: {v}')
    lines += ['', '## 注意',
      '- 「4→5展開」は結果CSVに4号艇が攻めたかの直接ラベルがないため、5号艇1着を頭的中としている。',
      '- モーター足質（伸び/出足）は第1段階では直接ラベルを使わず、モーター2/3連率を事前機力として使用。',
      '- 1号艇の張る/締めるは直接ラベルがないため、1枠Waku10勝率を防御力代理指標としている。']
    open('summary.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')

if __name__=='__main__': main()
