from backtest_v20_week import *
from datetime import date
import csv
from collections import defaultdict, Counter

D=date(2026,9,4)
VENUES={'02':'戸田','06':'浜名湖','07':'蒲郡','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','17':'宮島','18':'徳山','20':'若松','22':'福岡','24':'大村'}

def main():
    cache={};hist=defaultdict(list);seen=set();d=PRELOAD_START
    while d<TRAIN_START:
        ingest_motor(hist,seen,d)
        if d>=TRAIN_START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    # Walk forward only with information from dates strictly before Sep 4.
    while d<D:
        process_features(d,cache,hist)
        ingest_prior_day_preview(cache,d)
        ingest_motor(hist,seen,d)
        d+=timedelta(days=1)

    ymd=D.strftime('%Y/%m/%d')
    raw_cards=rows(f'data/programs/race_cards/{ymd}.csv')
    raw_w10=rows(f'data/programs/waku10/{ymd}.csv')
    cards_by_venue=Counter(str(r.get('レース場コード','')).zfill(2) for r in raw_cards)
    feats=process_features(D,cache,hist)

    allrows=[]; cand=[]
    for r,x,s4,s5,dc in feats:
        code=r['レースコード']; venue=str(r.get('レース場コード','')).zfill(2); race=r.get('レース回','')
        s3=score3v4(x)
        base={'date':str(D),'race_code':code,'venue_code':venue,'venue':VENUES.get(venue,venue),'race':race,
              'boat3':x[3]['name'],'boat4':x[4]['name'],'boat5':x[5]['name'],
              'score3':round(s3,2),'score4':round(s4,2),'score5':round(score45v4(x,s4),2)}
        allrows.append(base)
        for m,rule in RULES.items():
            fr=features(x,s3,s4,dc,m)
            passed=passes(fr,rule)
            if not passed: continue
            head=HEAD[m]; sc=score_for(x,s3,s4,m)
            margins={k:fr.get(k,0)-v for k,v in rule.items()}
            strong=sorted(margins,key=margins.get,reverse=True)
            weak=sorted(margins,key=margins.get)
            rr=dict(base)
            rr.update({'model':m,'head':head,'target_name':x[head]['name'],'target_grade':x[head]['grade'],
                       'base_score':round(sc,2),'reason_strong':' / '.join(f'{k}={fr[k]:.3f}' for k in strong[:2]),
                       'reason_border':' / '.join(f'{k}={fr[k]:.3f}' for k in weak[:2])})
            rr.update({k:round(fr[k],3) for k in rule})
            cand.append(rr)

    # Head-first consolidation for display: one row per race/head. For 3-head, if both routes pass,
    # prefer makuri when its stricter ST+wall thresholds pass; otherwise makuri-sashi.
    grouped=defaultdict(list)
    for r in cand: grouped[(r['race_code'],r['head'])].append(r)
    display=[]
    for key,rs in grouped.items():
        if key[1]==3:
            mak=[z for z in rs if z['model']=='3まくり']
            z=mak[0] if mak else rs[0]
            routes='/'.join(sorted({q['model'] for q in rs}))
            z=dict(z);z['routes']=routes;display.append(z)
        else:
            z=dict(rs[0]);z['routes']=z['model'];display.append(z)

    display.sort(key=lambda z:(0 if z['head'] in (3,5) else 1,-z['base_score'],z['venue_code'],int(str(z['race']).replace('R','') or 0)))

    with open('pred_v67_20260904_fullscan.csv','w',newline='',encoding='utf-8-sig') as f:
        fs=sorted(set().union(*(r.keys() for r in display))) if display else []
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(display)

    L=['# v67 2026-09-04 全場全R 事前走査','',
       '結果・払戻・実進入・当日展示は不使用。9/4 race_cards + waku10 と9/3までの履歴だけで固定条件を全Rに適用。',
       f'公式対象13場、race_cards取得 **{len(raw_cards)}R**、process_features処理 **{len(feats)}R**。','',
       '## 全場走査確認','|場|コード|取得R|','|---|---:|---:|']
    for c,nm in VENUES.items(): L.append(f'|{nm}|{c}|{cards_by_venue.get(c,0)}|')
    L += ['', '## 正式な事前候補（直前展示待ち）',
          '|優先|場|R|頭|モデル|選手|級|基礎score|主な通過理由|境界項目|',
          '|---|---|---:|---:|---|---|---|---:|---|---|']
    for z in display:
        pri='主候補' if z['head'] in (3,5) else '観察'
        L.append(f"|{pri}|{z['venue']}|{z['race']}|{z['head']}|{z['routes']}|{z['target_name']}|{z['target_grade']}|{z['base_score']:.1f}|{z['reason_strong']}|{z['reason_border']}|")
    L += ['',f'候補（race/head重複除外）: **{len(display)}R**',
          f'主候補3頭+5頭: **{sum(z["head"] in (3,5) for z in display)}R** / 4角観察: **{sum(z["head"]==4 for z in display)}R**',
          '', '※これは展示前の事前候補。締切前の展示・オリジナル展示・ST展示タイミング・チルトでA/S/Bへ最終判定する。']
    open('prediction_v67_20260904_fullscan.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__': main()
