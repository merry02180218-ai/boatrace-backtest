import csv, io, re, requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter

HD='20260905'
ALL_VENUES={
 '01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
 '07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
 '13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
 '19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}
BASECSV='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
UA={'User-Agent':'Mozilla/5.0 (compatible; boatrace-research/1.0)'}


def ff(x,d=0.0):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def c01(x): return max(0.0,min(1.0,x))
def norm_st_edge(inside,outside): return c01((inside-outside+0.01)/0.06)
def strength(z): return .6*c01((z['wr']-3.5)/4)+.4*c01((z['local']-3)/5)
def st_edge(left,right): return .60*norm_st_edge(left['waku_st'],right['waku_st'])+.40*norm_st_edge(left['nst'],right['nst'])
def wallweak(left,right): return .60*c01((5.5-left['waku_wr'])/4.5)+.40*norm_st_edge(left['waku_st'],right['waku_st'])
def resistance12(x):
    a,b=x[1],x[2]
    r1=.55*c01(a['waku_wr']/8)+.25*c01((a['wr']-3)/5)+.20*c01((.22-a['waku_st'])/.12)
    r2=.45*c01(b['waku_wr']/7)+.30*c01((b['wr']-3)/5)+.25*c01((.22-b['waku_st'])/.12)
    return c01(.60*r1+.40*r2)


def get_text(url,timeout=20):
    r=requests.get(url,headers=UA,timeout=timeout);r.raise_for_status();return r.text

def csv_rows(url):
    try:
        r=requests.get(url,headers=UA,timeout=15)
        if r.status_code!=200:return []
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception:return []


def racer_names():
    url='https://raw.githubusercontent.com/ryuriki/boatrace-v2/main/config/racers_name.yaml'
    txt=get_text(url)
    out={}
    for ln in txt.splitlines():
        m=re.match(r"'?(\d{4})'?:\s*(.+?)\s*$",ln)
        if m:out[int(m.group(1))]=m.group(2).strip()
    return out


def parse_race(jcd,rno,names):
    url=f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={HD}'
    soup=BeautifulSoup(get_text(url),'html.parser')
    tables=soup.find_all('div',class_='table1')
    if len(tables)<2: raise ValueError('racelist table missing')
    tds=tables[0].find('tbody').find_all('td')
    deadline=tds[rno].get_text(strip=True) if len(tds)>rno else ''
    bodies=tables[1].find_all('tbody')
    if len(bodies)<6: raise ValueError(f'lane bodies={len(bodies)}')
    lanes={}
    for lane in range(1,7):
        cells=bodies[lane-1].find_all('td')
        if len(cells)<8: raise ValueError(f'cells lane{lane}={len(cells)}')
        info=cells[2].find_all('div',class_='is-fs11')
        racer_text=info[0].get_text(strip=True)
        rid=ii(racer_text.split('/')[0].strip())
        grade=racer_text.split('/')[1].strip() if '/' in racer_text else ''
        c3=[z.strip() for z in cells[3].get_text('\n',strip=True).split('\n') if z.strip()]
        zn=[z.strip() for z in cells[4].get_text('\n',strip=True).split('\n') if z.strip()]
        jl=[z.strip() for z in cells[5].get_text('\n',strip=True).split('\n') if z.strip()]
        mo=[z.strip() for z in cells[6].get_text('\n',strip=True).split('\n') if z.strip()]
        lanes[lane]={'rid':rid,'name':names.get(rid,str(rid)),'grade':grade,
                     'nst':ff(c3[2] if len(c3)>2 else .20,.20),
                     'wr':ff(zn[0] if zn else 0), 'local':ff(jl[0] if jl else 0),
                     'motor_no':ii(mo[0] if mo else 0),'motor2':ff(mo[1] if len(mo)>1 else 0),'motor3':ff(mo[2] if len(mo)>2 else 0)}
    return {'jcd':jcd,'venue':ALL_VENUES[jcd],'rno':rno,'deadline':deadline,'lanes':lanes,'url':url}


def discover_active(names):
    active=[]; probe_errors={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(parse_race,j,1,names):j for j in ALL_VENUES}
        for f in as_completed(fs):
            j=fs[f]
            try:
                f.result(); active.append(j)
            except Exception as e:
                probe_errors[j]=str(e)
    return sorted(active),probe_errors


def fetch_hist_day(d):
    y=d.strftime('%Y/%m/%d')
    cards=csv_rows(BASECSV+f'data/programs/race_cards/{y}.csv')
    w10=csv_rows(BASECSV+f'data/programs/waku10/{y}.csv')
    wm={r.get('レースコード'):r for r in w10}
    out=[]
    for card in cards:
        w=wm.get(card.get('レースコード'),{})
        for b in range(1,7):
            rid=ii(card.get(f'艇{b}_登録番号'))
            if not rid:continue
            out.append((rid,b,{
                'waku_wr':ff(w.get(f'艇{b}_枠番別勝率'),ff(card.get(f'艇{b}_全国勝率'),5.0)),
                'waku_st':ff(w.get(f'艇{b}_枠番別平均ST'),ff(card.get(f'艇{b}_全国平均ST'),.18)),
                'date':d.isoformat()}))
    return d,out


def load_waku_history(days=45):
    ds=[];d=date(2026,9,4)
    for _ in range(days):ds.append(d);d-=timedelta(days=1)
    got=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        fut=[ex.submit(fetch_hist_day,d) for d in ds]
        for f in as_completed(fut):
            try:got.append(f.result())
            except:pass
    got.sort(key=lambda z:z[0])
    lookup={}
    for _,items in got:
        for rid,b,z in items:lookup[(rid,b)]=z
    return lookup


def attach_waku(races,lookup):
    found=total=0
    for r in races:
        for b,z in r['lanes'].items():
            total+=1; h=lookup.get((z['rid'],b))
            if h:found+=1; z.update(h);z['waku_source']='prior_same_frame'
            else:
                z['waku_wr']=z['wr'];z['waku_st']=z['nst'];z['waku_source']='national_fallback'
    return found,total


def eval_race(r):
    x=r['lanes']; out=[]
    a,b,c,d,e=x[1],x[2],x[3],x[4],x[5]
    s3=strength(c); se3=st_edge(b,c); ww2=wallweak(b,c); iw1=c01((7.5-a['waku_wr'])/6)
    rules3m={'3選手力':(s3,.50),'3_ST優位':(se3,.55),'2壁弱さ':(ww2,.55)}
    rules3s={'3選手力':(s3,.50),'3_ST優位':(se3,.45),'1弱さ':(iw1,.45),'2壁弱さ':(ww2,.45)}
    s4=strength(d); se4=st_edge(c,d); ww3=wallweak(c,d)
    rules4={'4選手力':(s4,.50),'4_ST優位':(se4,.55),'3壁弱さ':(ww3,.55)}
    atk4=c01(.40*se4+.35*ww3+.25*s4); resist=resistance12(x); s5=strength(e)
    rules5={'4攻撃力_非motor':(atk4,.55),'1_2抵抗力':(resist,.55),'5選手力':(s5,.50)}
    for m,head,ru in [('3まくり',3,rules3m),('3まくり差し',3,rules3s),('4カドまくり',4,rules4),('5頭展開',5,rules5)]:
        if all(v>=th for v,th in ru.values()):
            vals={k:v for k,(v,_) in ru.items()}; margins={k:v-th for k,(v,th) in ru.items()}
            idx=100*sum(vals.values())/len(vals)
            out.append({'venue':r['venue'],'jcd':r['jcd'],'race':r['rno'],'deadline':r['deadline'],'model':m,'head':head,
                        'name':x[head]['name'],'grade':x[head]['grade'],'struct_index':round(idx,1),
                        'features':vals,'min_margin':round(min(margins.values()),3),
                        'waku_sources':'/'.join(x[q]['waku_source'] for q in range(1,6))})
    return out


def main():
    names=racer_names()
    active,probe_errors=discover_active(names)
    lookup=load_waku_history()
    races=[];errs=[]
    jobs=[(j,r) for j in active for r in range(1,13)]
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(parse_race,j,r,names):(j,r) for j,r in jobs}
        for f in as_completed(fs):
            j,r=fs[f]
            try:races.append(f.result())
            except Exception as e:errs.append((j,r,str(e)))
    races.sort(key=lambda z:(z['jcd'],z['rno']))
    found,total=attach_waku(races,lookup)
    raw=[]
    for r in races:raw.extend(eval_race(r))
    # consolidate duplicate 3 routes by race/head; preserve both route names
    g=defaultdict(list)
    for z in raw:g[(z['jcd'],z['race'],z['head'])].append(z)
    cand=[]
    for _,rs in g.items():
        z=max(rs,key=lambda q:q['struct_index']).copy()
        z['routes']='/'.join(sorted(q['model'] for q in rs))
        cand.append(z)
    cand.sort(key=lambda z:(0 if z['head'] in (3,5) else 1,-z['struct_index'],z['jcd'],z['race']))
    counts=Counter(r['jcd'] for r in races)
    expected=len(active)*12
    complete=(len(races)==expected and all(counts[j]==12 for j in active) and not errs)
    with open('pred_v107_20260905_official_fullscan.csv','w',newline='',encoding='utf-8-sig') as f:
        fields=['venue','jcd','race','deadline','head','routes','name','grade','struct_index','min_margin','waku_sources','shadow']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for z in cand:
            row={k:z.get(k,'') for k in fields}
            row['shadow']='v100' if z['head']==3 else ('v106' if z['head']==4 else '')
            w.writerow(row)
    L=['# v107 2026-09-05 公式サイト全場全R 事前走査','',
       'BOAT RACE公式 racelist を直接取得。結果・払戻・実進入・当日展示・当日オッズは使用していない。候補ゲートは現行v20固定条件。',
       f'自動検出開催場: **{len(active)}場** / 取得: **{len(races)}/{expected}R** / 開催場内エラー **{len(errs)}R** / 全開催完全走査: **{"YES" if complete else "NO"}**',
       '開催場: '+', '.join(ALL_VENUES[j] for j in active),
       f'枠別ST/勝率の9/4以前同枠履歴補完: **{found}/{total} ({found/total*100 if total else 0:.1f}%)**。欠損のみ全国値fallback。','',
       '## 全場取得確認','|場|取得R|','|---|---:|']
    for j in active:L.append(f'|{ALL_VENUES[j]}|{counts[j]}|')
    if errs:
        L+=['','## 開催場内取得エラー']+[f'- {ALL_VENUES.get(j,j)} {r}R: {e}' for j,r,e in errs]
    L+=['','## 事前候補（展示前）','|優先|場|R|締切|頭|モデル|選手|級|構造指数|最低余裕|shadow|理由|','|---|---|---:|---|---:|---|---|---|---:|---:|---|---|']
    for z in cand:
        pri='主候補' if z['head'] in (3,5) else '観察'
        shadow='v100' if z['head']==3 else ('v106' if z['head']==4 else '-')
        fr=' / '.join(f'{k}={v:.3f}' for k,v in z['features'].items())
        L.append(f"|{pri}|{z['venue']}|{z['race']}R|{z['deadline']}|{z['head']}|{z['routes']}|{z['name']}|{z['grade']}|{z['struct_index']:.1f}|{z['min_margin']:+.3f}|{shadow}|{fr}|")
    L+=['',f'候補: **{len(cand)}R** / 主候補3頭+5頭: **{sum(z["head"] in (3,5) for z in cand)}R** / 4角観察: **{sum(z["head"]==4 for z in cand)}R**',
        '', '※これは展示前の構造候補。S/A/Bは締切前の進入・展示ST・展示タイム・オリジナル展示・風を入れて初めて判定する。',
        '※3頭候補は結果前にv100 shadow相手順位を保存。4カド候補は適格化後、CURRENT7/ROLE7/V106_7を結果前に保存する。']
    open('prediction_v107_20260905_official_fullscan.md','w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
