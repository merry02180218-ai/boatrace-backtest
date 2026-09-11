#!/usr/bin/env python3
"""Generic result-blind current PRE input fetcher for 4-head v291.

Date is --date / TARGET_DATE / Asia-Tokyo today. Active venues are discovered by
probing JCD01..24. Missing Waku10 history for an individual racer uses the same
frozen fallback semantics as the 2026-09-11 audited scanner instead of dropping
the whole race.
"""
from __future__ import annotations
import argparse, json, os, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import fetch_kyoteibiyori_v291_pre_inputs as tolerant

base = tolerant.base


def resolve_date(arg: str | None) -> str:
    s = arg or os.environ.get('TARGET_DATE','').strip()
    if not s:
        s = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d')
    return datetime.strptime(s, '%Y-%m-%d').strftime('%Y%m%d')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    a = ap.parse_args()
    day = resolve_date(a.date)
    base.DAY = day
    out = Path('current_input/v291') / day
    out.mkdir(parents=True, exist_ok=True)
    base.OUT = out

    s = base.requests.Session()
    s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; v291-pre-live/1.0)','Accept':'text/html,application/json'})
    cards=[]; waku=[]; failures=[]; active=[]
    for jo in range(1,25):
        try:
            referer,token,meta=base.get_meta(s,jo)
        except Exception as e:
            failures.append((jo,'meta',str(e))); continue
        got=0
        for rno in range(1,13):
            try:
                z=base.detail(s,jo,rno,referer,token,meta)
                if not z: continue
                players=sorted(z['race_list'],key=lambda x:int(x.get('course') or 99))
                mt=base.meeting(s,jo,rno,referer,meta,players)
                cards.append(base.make_card(jo,rno,z,mt))
                waku.append(base.make_waku(jo,rno,z))
                got+=1; time.sleep(.03)
            except Exception as e:
                failures.append((jo,rno,str(e)))
        if got:
            active.append(jo)
            print(f'JCD{jo:02d}: {got}/12 PRE rows', flush=True)

    if not cards or len(cards)!=len(waku):
        raise RuntimeError(f'invalid current universe cards={len(cards)} waku={len(waku)}')
    base.write_csv(out/'race_cards.csv', cards)
    base.write_csv(out/'waku10.csv', waku)
    manifest={
        'target_date':datetime.strptime(day,'%Y%m%d').strftime('%Y-%m-%d'),
        'result_blind':True,'current_exhibition_used':False,
        'active_venues':[f'{x:02d}' for x in active],
        'race_rows':len(cards),'waku_rows':len(waku),'failures':failures,
        'note':'Individual missing Waku10 history uses frozen default fallback; race is retained.'
    }
    (out/'input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ACTIVE',','.join(f'{x:02d}' for x in active),'RACES',len(cards),'FAILURES',len(failures),flush=True)

if __name__=='__main__': main()
