#!/usr/bin/env python3
"""Fill BoatraceCSV od3 gaps with official historical closing 3T odds.

Only dates marked missing in archive_boatracecsv_od3_manifest.csv are processed.
Race inventory is taken from BoatraceCSV historical race_cards so we request only races
that actually existed. If a day's race card is unavailable, that date is reported for
manual/further fallback instead of blindly crawling all 288 combinations.

IMPORTANT: official_closing is a different provenance from BoatraceCSV's ~5-min pre-close
snapshot. Files stay under data/official_closing_odds3t and must not be silently mixed.
"""
from __future__ import annotations
import csv, io, itertools, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
import requests

MANIFEST=Path('archive_boatracecsv_od3_manifest.csv')
OUT=Path('data/official_closing_odds3t')
COVER=Path('archive_od3_official_fill_manifest.csv')
CARD_BASE='https://boatracecsv.github.io/data/programs/race_cards/{y}/{m}/{d}.csv'
ODDS='https://www.boatrace.jp/owpc/pc/race/odds3t'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-backtest historical-research/1.0)'}
COMBOS=[f'{a}-{b}-{c}' for a,b,c in itertools.permutations(range(1,7),3)]


def get_text(url, timeout=12, tries=2):
    for k in range(tries):
        try:
            r=requests.get(url,headers=UA,timeout=timeout)
            if r.status_code==200:return r.text
            if r.status_code in (404,410):return None
        except requests.RequestException:
            pass
        if k+1<tries:time.sleep(.4*(k+1))
    return None


def race_inventory(day):
    y,m,d=day.split('-');u=CARD_BASE.format(y=y,m=m,d=d)
    txt=get_text(u,15,2)
    if not txt:return [],'race_cards_missing'
    try: rows=list(csv.DictReader(io.StringIO(txt.lstrip('\ufeff'))))
    except Exception:return [],'race_cards_parse_error'
    races=[]
    for z in rows:
        code=str(z.get('レースコード','')).strip()
        if len(code)>=12 and code[:8]==y+m+d and code[8:10].isdigit() and code[10:12].isdigit():
            races.append((int(code[8:10]),int(code[10:12])))
    races=sorted(set(races))
    return races,('ok' if races else 'race_cards_empty')


def parse_odds(html):
    if not html:return None
    # Current official HTML normally contains the odds table with 120 numeric prices.
    # Use several strict extraction paths; accept only exactly 120 plausible values.
    areas=[]
    m=re.search(r'3連単オッズ(.*?)(?:2連単オッズ|3連複オッズ|オッズ情報|払戻)',html,re.S)
    if m:areas.append(m.group(1))
    areas.append(html)
    pats=[
      r'(?:odds|ratio)[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*<',
      r'<td[^>]*class="[^"]*(?:odds|ratio)[^"]*"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*</td>',
      r'<span[^>]*class="[^"]*(?:odds|ratio)[^"]*"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*</span>'
    ]
    for area in areas:
        for pat in pats:
            vals=re.findall(pat,area,re.I)
            nums=[]
            for x in vals:
                try:
                    v=float(x)
                    if .1<=v<=99999:nums.append(v)
                except:pass
            if len(nums)==120:return dict(zip(COMBOS,nums))
    return None


def fetch_race(day,jcd,rno):
    hd=day.replace('-','')
    url=ODDS+'?'+urlencode({'hd':hd,'jcd':f'{jcd:02d}','rno':rno})
    html=get_text(url,12,2);o=parse_odds(html)
    return day,jcd,rno,url,o,('ok' if o else 'missing_or_parse')


def missing_days():
    with MANIFEST.open(encoding='utf-8-sig') as f:
        return [r['date'] for r in csv.DictReader(f) if r.get('status')=='missing']


def write_day(day,rows):
    if not rows:return
    y,m,d=day.split('-');p=OUT/y/m/f'{d}.csv';p.parent.mkdir(parents=True,exist_ok=True)
    fields=['date','jcd','rno','source_type','snapshot_type','source_url']+COMBOS
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    workers=int(sys.argv[1]) if len(sys.argv)>1 else 32
    days=missing_days(); inventories={}; todo=[]; report={}
    print(f'missing days={len(days)} workers={workers}',flush=True)
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(race_inventory,d):d for d in days}
        for i,f in enumerate(as_completed(fs),1):
            d=fs[f]
            try:races,status=f.result()
            except Exception as e:races,status=[],f'inventory_error:{type(e).__name__}'
            inventories[d]=races;report[d]={'date':d,'inventory_status':status,'expected_races':len(races),'fetched_races':0,'failed_races':0}
            todo.extend((d,j,r) for j,r in races)
            if i%25==0 or i==len(days):print(f'inventory {i}/{len(days)} races={len(todo)}',flush=True)
    print(f'official race requests={len(todo)}',flush=True)
    byday={d:[] for d in days}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs=[ex.submit(fetch_race,*x) for x in todo]
        for i,f in enumerate(as_completed(fs),1):
            try:
                day,jcd,rno,url,o,status=f.result()
                if o:
                    row={'date':day,'jcd':f'{jcd:02d}','rno':rno,'source_type':'official_closing','snapshot_type':'closing_displayed','source_url':url};row.update(o)
                    byday[day].append(row);report[day]['fetched_races']+=1
                else:report[day]['failed_races']+=1
            except Exception:
                pass
            if i%500==0 or i==len(todo):print(f'fetch {i}/{len(todo)}',flush=True)
    total=0
    for d in days:
        rows=sorted(byday[d],key=lambda z:(z['jcd'],int(z['rno'])))
        write_day(d,rows);total+=len(rows)
    with COVER.open('w',newline='',encoding='utf-8') as f:
        fields=['date','inventory_status','expected_races','fetched_races','failed_races'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(report[d] for d in days)
    complete=sum(1 for d in days if report[d]['expected_races'] and report[d]['fetched_races']==report[d]['expected_races'])
    partial=sum(1 for d in days if 0<report[d]['fetched_races']<report[d]['expected_races'])
    noinv=sum(1 for d in days if not report[d]['expected_races'])
    print(f'SUMMARY days={len(days)} complete_days={complete} partial_days={partial} no_inventory={noinv} fetched_races={total}',flush=True)

if __name__=='__main__':main()
