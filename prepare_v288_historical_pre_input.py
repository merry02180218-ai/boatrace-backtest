#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,re,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from backtest import rows
from historical_waku10_fetcher import fetch_race
import fetch_kyoteibiyori_v288_pre_inputs as kyotei

OFFICIAL_RACELIST='https://www.boatrace.jp/owpc/pc/race/racelist'
UA='Mozilla/5.0 (compatible; v288-historical-pre/1.1; +https://github.com/)'
JNUM={'１':1,'２':2,'３':3,'４':4,'５':5,'６':6}


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
    s.headers.update({'User-Agent':UA,'Accept':'text/html,application/json'})
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


def _nums(s):
    return re.findall(r'-?\d+(?:\.\d+)?',s or '')


def _st_value(s):
    q=(s or '').strip().upper().replace(' ','')
    if re.fullmatch(r'F\.?\d{2}',q):
        return -int(q[-2:])/100.0
    if re.fullmatch(r'\.\d{2}',q):
        return float('0'+q)
    if re.fullmatch(r'[01]\.\d{2}',q):
        return float(q)
    return None


def official_racelist_card(day8,day_iso,jo,rno):
    """Build one result-blind card from BOAT RACE official /race/racelist only."""
    r=requests.get(OFFICIAL_RACELIST,params={'rno':rno,'jcd':f'{jo:02d}','hd':day8},headers={'User-Agent':UA},timeout=25)
    r.raise_for_status()
    if '/race/racelist' not in r.url.lower():
        raise RuntimeError(f'unexpected official redirect {r.url}')
    soup=BeautifulSoup(r.text,'html.parser')
    table=None
    for t in soup.find_all('table'):
        tx=t.get_text(' ',strip=True)
        if 'ボートレーサー' in tx and 'モーター' in tx and 'ボート' in tx:
            table=t;break
    if table is None:return None
    trs=table.find_all('tr')
    summaries=[]
    for i,tr in enumerate(trs):
        cells=tr.find_all(['th','td'],recursive=False)
        txt=[x.get_text(' ',strip=True) for x in cells]
        if not txt or txt[0] not in JNUM:continue
        if not any(re.search(r'\b\d{4}\s*/\s*[AB][12]\b',x) for x in txt):continue
        summaries.append((i,JNUM[txt[0]],txt))
    if len(summaries)!=6:return None
    card={'レースコード':f'{day8}{jo:02d}{rno:02d}','レース日':day_iso,'レース場コード':f'{jo:02d}','レース回':str(rno),'_historical_pre_source':'boatrace_official_racelist'}
    for k,(idx,b,txt) in enumerate(summaries):
        info_i=next((j for j,x in enumerate(txt) if re.search(r'\b\d{4}\s*/\s*[AB][12]\b',x)),None)
        if info_i is None:raise RuntimeError(f'official player info missing {day8} {jo} {rno} b{b}')
        info=re.sub(r'\s+',' ',txt[info_i]).strip()
        m=re.match(r'(\d{4})\s*/\s*([AB][12])\s+(.+?)\s+([^\s/]+)/([^\s]+)\s+\d+歳/[\d.]+kg',info)
        if not m:raise RuntimeError(f'official player parse failed {info!r}')
        reg,grade,name=m.group(1),m.group(2),m.group(3).strip()
        fst=txt[info_i+1] if len(txt)>info_i+1 else ''
        fs=re.search(r'F\s*(\d+).*?L\s*(\d+).*?([0-9]+\.[0-9]+)',fst)
        nst=float(fs.group(3)) if fs else 0.20
        fcnt=fs.group(1) if fs else '0'; lcnt=fs.group(2) if fs else '0'
        nat=_nums(txt[info_i+2] if len(txt)>info_i+2 else '')
        loc=_nums(txt[info_i+3] if len(txt)>info_i+3 else '')
        mot=_nums(txt[info_i+4] if len(txt)>info_i+4 else '')
        boat=_nums(txt[info_i+5] if len(txt)>info_i+5 else '')
        if len(nat)<3 or len(loc)<3 or len(mot)<3 or len(boat)<3:
            raise RuntimeError(f'official stats parse failed {day8} JCD{jo:02d} R{rno} b{b}: {txt[:8]}')
        pre=f'艇{b}_'
        card.update({
          pre+'登録番号':reg,pre+'選手登番':reg,pre+'選手名':name,pre+'級別':grade,
          pre+'全国平均ST':nst,pre+'全国勝率':nat[0],pre+'全国2連対率':nat[1],pre+'全国3連対率':nat[2],
          pre+'当地勝率':loc[0],pre+'当地2連対率':loc[1],pre+'当地3連対率':loc[2],
          pre+'モーター番号':mot[0],pre+'モーター2連対率':mot[1],pre+'モーター3連対率':mot[2],
          pre+'ボート番号':boat[0],pre+'ボート2連対率':boat[1],pre+'ボート3連対率':boat[2],
          pre+'F本数':fcnt,pre+'L本数':lcnt,pre+'早見':''})

        # The official racelist embeds prior meeting results as links, but we do
        # not request those result endpoints. Use the link dates only to count
        # slots that are strictly before the target day, then take the matching
        # ST cells from the same displayed history grid. Same-day slots are cut.
        end=summaries[k+1][0] if k+1<len(summaries) else len(trs)
        group=trs[idx:end]
        prior_slots=0
        for gr in group:
            for a in gr.find_all('a',href=True):
                h=a.get('href','')
                mm=re.search(r'/race/raceresult\?[^#]*\bhd=(\d{8})',h)
                if mm and mm.group(1)<day8:prior_slots+=1
        best=[]
        for gr in group[1:]:
            vals=[]
            for c in gr.find_all(['th','td'],recursive=False):
                v=_st_value(c.get_text(' ',strip=True))
                if v is not None:vals.append(v)
            if len(vals)>len(best):best=vals
        safe_st=best[:prior_slots] if prior_slots else []
        for j,v in enumerate(safe_st[-14:]):
            d=j//2+1;s=j%2+1
            card[f'{pre}節D{d}走{s}_ST']=v
    return card


def official_racelist_history(day8,day_iso):
    """Recover historical PRE cards from official racelist; never request results/payouts."""
    cards=[]; failures=[]; active=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut={ex.submit(official_racelist_card,day8,day_iso,jo,1):jo for jo in range(1,25)}
        first={}
        for f in as_completed(fut):
            jo=fut[f]
            try:first[jo]=f.result()
            except Exception as e:failures.append((jo,1,str(e)));first[jo]=None
    for jo,z in sorted(first.items()):
        if z is not None:active.append(jo);cards.append(z)
    with ThreadPoolExecutor(max_workers=20) as ex:
        fut={ex.submit(official_racelist_card,day8,day_iso,jo,rno):(jo,rno) for jo in active for rno in range(2,13)}
        for f in as_completed(fut):
            jo,rno=fut[f]
            try:
                z=f.result()
                if z is not None:cards.append(z)
                else:failures.append((jo,rno,'no official racelist card'))
            except Exception as e:failures.append((jo,rno,str(e)))
    cards.sort(key=lambda x:str(x['レースコード']))
    if cards and len(cards)<120:
        raise RuntimeError(f'insufficient official racelist PRE cards {len(cards)} for {day_iso}; failures={failures[:8]}')
    return cards,{'active_venues':[f'{x:02d}' for x in active],'official_racelist_pages':len(cards),'failures':failures,'result_endpoint_requested':False,'payout_endpoint_requested':False}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);a=ap.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').date(); y=day.strftime('%Y/%m/%d'); day8=day.strftime('%Y%m%d')
    cards=rows(f'data/programs/race_cards/{y}.csv'); waku0=rows(f'data/programs/waku10/{y}.csv')
    source='boatracecsv_archive'; extra={}

    if not cards:
        cards,waku0,extra=kyoteibiyori_history(day8,a.date)
        source='kyoteibiyori_historical_fallback'
    if not cards:
        cards,official_extra=official_racelist_history(day8,a.date)
        waku0=[]
        extra={'kyoteibiyori':extra,'official_racelist':official_extra}
        source='boatrace_official_racelist_fallback'
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
