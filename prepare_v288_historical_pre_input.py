#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,time
from datetime import datetime
from pathlib import Path
from backtest import rows
from historical_waku10_fetcher import fetch_race
import fetch_kyoteibiyori_v288_pre_inputs as kyotei


def bycode(rs):
    return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}


def write(path,rs):
    if not rs: raise RuntimeError(f'no rows for {path}')
    fs=[]; seen=set()
    for r in rs:
        for k in r:
            if k not in seen:seen.add(k);fs.append(k)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)


def kyoteibiyori_history(day8,day_iso):
    """Result-blind historical PRE fallback when BoatraceCSV race cards are absent."""
    kyotei.DAY=day8
    s=kyotei.requests.Session()
    s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; v288-historical-pre/1.0)','Accept':'text/html,application/json'})
    cards=[]; waku=[]; failures=[]; recovered=[]; detail_rows=0
    for jo in range(1,25):
        try:
            referer,token,meta=kyotei.get_meta(s,jo)
        except Exception as e:
            failures.append((jo,'meta',str(e))); continue
        for rno in range(1,13):
            code=f'{day8}{jo:02d}{rno:02d}'
            try:
                z=kyotei.detail(s,jo,rno,referer,token,meta)
                if not z: continue
                detail_rows+=1
                players=sorted(z['race_list'],key=lambda x:int(x.get('course') or 99))
                mt=kyotei.meeting(s,jo,rno,referer,meta,players)
                card=kyotei.make_card(jo,rno,z,mt)
                try:
                    wr=kyotei.make_waku(jo,rno,z)
                    src='kyoteibiyori'
                except Exception as e:
                    wr=fetch_race(day_iso,code)
                    if not wr:
                        failures.append((jo,rno,f'waku unavailable: {e}')); continue
                    src='boatcast_direct_validated_fallback'
                    recovered.append(code)
                card['レース日']=day_iso; wr['レース日']=day_iso
                card['_historical_pre_source']='kyoteibiyori'
                wr['_historical_pre_source']=src
                cards.append(card); waku.append(wr)
                time.sleep(.02)
            except Exception as e:
                failures.append((jo,rno,str(e)))
    if detail_rows and len(cards)<120:
        raise RuntimeError(f'insufficient Kyoteibiyori historical PRE rows {len(cards)}/{detail_rows} for {day_iso}')
    return cards,waku,{'detail_rows':detail_rows,'failures':failures,'waku_fallback_recovered':recovered}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);a=ap.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').date(); y=day.strftime('%Y/%m/%d'); day8=day.strftime('%Y%m%d')
    cards=rows(f'data/programs/race_cards/{y}.csv'); waku0=rows(f'data/programs/waku10/{y}.csv')
    source='boatracecsv_archive'; extra={}

    if not cards:
        cards,waku0,extra=kyoteibiyori_history(day8,a.date)
        source='kyoteibiyori_historical_fallback'
    if not cards:
        raise RuntimeError(f'no archived/pre-race cards from approved sources {a.date}')

    wm=bycode(waku0); recovered=[]; missing=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12)
        if code in wm: continue
        z=fetch_race(a.date,code)
        if z: wm[code]=z;recovered.append(code)
        else: missing.append(code)

    # Production semantics are fail-closed per race; preserve all complete card+waku rows.
    cc=[];ww=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12)
        if code not in wm:continue
        c=dict(card);w=dict(wm[code]);c['レース日']=a.date;w['レース日']=a.date
        cc.append(c);ww.append(w)
    out=Path('current_input/v288')/day8
    write(out/'race_cards.csv',cc);write(out/'waku10.csv',ww)
    m={'target_date':a.date,'archived_pre_input':True,'result_or_payout_used':False,'current_exhibition_used':False,
       'race_card_source':source,'race_cards_seen':len(cards),'public_waku_rows':len(waku0),'complete_rows':len(cc),
       'boatcast_fallback_recovered':recovered,'excluded_missing_waku':missing,'historical_fallback_audit':extra}
    (out/'historical_input_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(m,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
