#!/usr/bin/env python3
"""v234: rebuild historical Waku10 from recovered Boatcast raw files and replay frozen v224.

Data-correction audit only. No threshold/feature discovery.
- Restores missing Waku10 using bc_j_waku10 raw files recovered by v233.
- Uses published BoatraceCSV Waku10 verbatim where already available.
- Probes Boatcast directly for any remaining missing day/race; no imputation.
- Validates parser against a published August day before model replay.
- Replays the frozen v224 FULL_DECOMP head selector + frozen v221 pair ranker.
- Jul/Aug remain NON-PRISTINE shadow context and are never treated as independent validation.
"""
from __future__ import annotations

import csv, io, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224

ROOT=Path(__file__).resolve().parent
V233=Path(os.environ.get('V233_DIR','/tmp/v233'))
OUTDIR=ROOT/'data/audit/v234_waku10'
REST=OUTDIR/'restored'
OUT=ROOT/'analysis_v234_3head_waku10_restored_replay.csv'
COV=ROOT/'analysis_v234_waku10_reconstruction_coverage.csv'
SUM=ROOT/'summary_v234_3head_waku10_restored_replay.md'
START=date(2025,12,1); END=date(2026,8,31)
MONTHS=['2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
PUB='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/programs/waku10/'
BOAT='https://race.boatcast.jp/hp_txt/'
BANK=10000

FW={'１':'1','２':'2','３':'3','４':'4','５':'5','６':'6','７':'7','８':'8','９':'9','Ｆ':'F','Ｌ':'L'}
SUMMARY=['選手名','枠番別勝率','枠番別平均ST','枠番別平均スタート順']
RUN=['着順','進入','グレード']
HEAD=['レースコード','レース日','レース場コード','レース回']
for b in range(1,7):
    HEAD += [f'艇{b}_{x}' for x in SUMMARY]
    for k in range(1,11): HEAD += [f'艇{b}_過去{k}走_{x}' for x in RUN]


def get(url,timeout=5):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
    except Exception:return b''

def norm_name(s):
    return ' '.join(str(s or '').replace('\u3000',' ').split())

def flt(s):
    try:return float(str(s).strip())
    except:return None

def integer(s):
    try:return int(float(str(s).strip()))
    except:return None

def fmt(v): return '' if v is None else str(v)
def finish(s):
    z=str(s or '').strip()
    if not z or z=='-':return ''
    return FW.get(z,z) if len(z)==1 else z

def parse_raw(raw:bytes,d:date,jo:int,rr:int):
    try: text=raw.decode('utf-8-sig')
    except Exception:return None
    lines=text.splitlines()
    if len(lines)<2 or not lines[0].startswith('data='):return None
    meta=lines[1].split('\t'); status=meta[0].strip() if meta else ''
    if status=='2':return None
    boats=[]
    for bi,line in enumerate(lines[2:8],1):
        if not line.strip():continue
        c=line.split('\t')
        if len(c)<4:continue
        cells=[norm_name(c[0]),fmt(flt(c[1])),fmt(flt(c[2])),fmt(flt(c[3]))]
        for k in range(10):
            j=4+3*k
            cells += [finish(c[j] if j<len(c) else ''),fmt(integer(c[j+1] if j+1<len(c) else '')),str(c[j+2]).strip() if j+2<len(c) else '']
        boats.append((bi,cells))
    if not boats:return None
    row=[f'{d:%Y%m%d}{jo:02d}{rr:02d}',str(d),f'{jo:02d}',f'{rr:02d}R']
    bm={b:x for b,x in boats}
    for b in range(1,7):row += bm.get(b,['']*34)
    return row

def raw_meta(path:Path):
    m=re.search(r'bc_j_waku10_(\d{8})_(\d{2})_(\d{1,2})\.txt$',path.name)
    if not m:return None
    ds,jo,rr=m.groups(); return date(int(ds[:4]),int(ds[4:6]),int(ds[6:])),int(jo),int(rr)

def write_rows(path:Path,rs):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(HEAD);w.writerows(sorted(rs,key=lambda x:x[0]))

def fetch_all_day(d:date):
    jobs=[]
    with ThreadPoolExecutor(max_workers=32) as ex:
        for jo in range(1,25):
            for rr in range(1,13):
                u=f'{BOAT}{jo:02d}/bc_j_waku10_{d:%Y%m%d}_{jo:02d}_{rr:02d}.txt'
                jobs.append((jo,rr,u,ex.submit(get,u,4)))
        out=[]
        for jo,rr,u,f in jobs:
            b=f.result()
            if b and b.lstrip().startswith(b'data='):out.append((jo,rr,u,b))
    return out

def reconstruct():
    REST.mkdir(parents=True,exist_ok=True)
    rawroot=V233/'recovered_boatcast'
    byday={}
    if rawroot.exists():
        for p in rawroot.rglob('bc_j_waku10_*.txt'):
            q=raw_meta(p)
            if q:byday.setdefault(q[0],[]).append((q[1],q[2],str(p),p.read_bytes()))
    coverage=[]; d=START
    while d<=END:
        rel=f'{d:%Y/%m/%d}.csv'; dest=REST/rel
        pub=get(PUB+rel,5)
        if pub:
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(pub)
            n=max(0,len(pub.decode('utf-8-sig',errors='ignore').splitlines())-1)
            coverage.append({'date':str(d),'source':'published','rows':n,'raw_files':0})
            d+=timedelta(days=1);continue
        raws=byday.get(d,[])
        if not raws:
            raws=fetch_all_day(d)
        rs=[]
        for jo,rr,src,b in raws:
            r=parse_raw(b,d,jo,rr)
            if r:rs.append(r)
        if rs:write_rows(dest,rs)
        coverage.append({'date':str(d),'source':'recovered' if rs else 'missing','rows':len(rs),'raw_files':len(raws)})
        print('reconstruct',d,coverage[-1],flush=True)
        d+=timedelta(days=1)
    pd.DataFrame(coverage).to_csv(COV,index=False)
    return pd.DataFrame(coverage)

def validate_parser():
    # One published day is independently re-fetched from Boatcast and rebuilt.
    d=date(2026,8,1); published=REST/f'{d:%Y/%m/%d}.csv'
    if not published.exists():raise RuntimeError('validation published day missing')
    direct=fetch_all_day(d); rs=[]
    for jo,rr,u,b in direct:
        r=parse_raw(b,d,jo,rr)
        if r:rs.append(r)
    pub=list(csv.DictReader(published.open(encoding='utf-8-sig'))); pm={r['レースコード']:r for r in pub}
    sio=io.StringIO();w=csv.writer(sio,lineterminator='\n');w.writerow(HEAD);w.writerows(sorted(rs,key=lambda x:x[0])); rm={r['レースコード']:r for r in csv.DictReader(io.StringIO(sio.getvalue()))}
    common=sorted(set(pm)&set(rm))
    if len(common)<20:raise RuntimeError(f'parser validation too few common races: {len(common)}')
    mism=0
    for code in common:
        for c in HEAD:
            if str(pm[code].get(c,''))!=str(rm[code].get(c,'')):mism+=1
    if mism:raise RuntimeError(f'parser validation mismatch cells={mism}, common={len(common)}')
    return len(common)

def local_rows(d):
    p=REST/f'{d:%Y/%m/%d}.csv'
    if not p.exists():return []
    return list(csv.DictReader(p.open(encoding='utf-8-sig')))

def build_restored():
    endts=pd.Timestamp('2026-09-01')
    v221.CONTAM=endts; v221.END=END
    v222.CONTAM=endts; v222.END=END
    v223.CONTAM=endts; v224.CONTAM=endts
    orig=v222.day_fetch
    def patched(d):
        dd,z=orig(d); z['waku']=local_rows(d); return dd,z
    v222.day_fetch=patched
    raw=pd.read_csv(v224.SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);basefs=v165.feats(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<endts)].copy()
    d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=v224.add_decomp(d,dc)
    return d,dc,vc,basefs

def full_features(d,basefs):
    hist=v222.cols(d,'b3_vh_')
    rel=[c for c in d.columns if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]
    cur += [c for c in d.columns if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))]
    best=v223.uniq(list(basefs)+hist+cur+rel)
    m1=[c for c in d.columns if c.startswith('f_b3_m1_')];m12=[c for c in d.columns if c.startswith('f_b3_m12_')];m35=[c for c in d.columns if c.startswith('f_b3_m35_')]
    trend=[c for c in d.columns if c.startswith('f_b3_trend_')];rctx=[c for c in d.columns if c.startswith('f_rel_')]
    return v223.uniq(best+m1+m12+m35+trend+['f_b3_layoff','f_b3_grade','f_b3_m1_grade']+rctx)

def replay(d,vc,basefs,fs):
    odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);out=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
        pair=v222.fit_pair(tr,'V221')
        base_te,_=v223.fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
        te,nfeat=v223.fit_head(d,fs,vc,first,nextm);sel=te.nlargest(k,'_p').copy()
        rec=[]
        for _,r in sel.iterrows():
            if v223.ii(r.get('valid_result'))!=1 or v223.ii(r.get('course3'),3)!=3:continue
            act=v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else '';code=str(r.get('race_code','')).zfill(12)
            if not actual:continue
            ts=v222.order(r,pair,'V221');rank=ts.index(actual)+1 if actual in ts else 0
            z={'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(r._p),'y3':int(r._y),'rank':rank,'top10_hit':int(rank>0 and rank<=10 and int(r._y)==1),'settled':0,'ret':np.nan,'profit':np.nan}
            if code in oi.index:
                od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od;s=v222.settle(ts,od,actual)
                if s is not None:z.update({'settled':1,'ret':s[1],'profit':s[2]})
            rec.append(z)
        g=pd.DataFrame(rec); h=g[g.y3==1]
        settled=g[g.settled==1]
        roi=100*settled.ret.sum()/(len(settled)*BANK) if len(settled) else np.nan
        out.append({'month':mon,'R':len(g),'avg_p3':g.p3.mean(),'head_rate':g.y3.mean(),'gap_pp':100*(g.p3.mean()-g.y3.mean()),'pair_cov10':((h['rank']>0)&(h['rank']<=10)).mean() if len(h) else np.nan,'top10_hit':g.top10_hit.mean(),'settled_R':len(settled),'roi':roi,'nfeat':nfeat,'non_pristine':int(mon in ('2026-07','2026-08'))})
        print('replay',out[-1],flush=True)
    return pd.DataFrame(out)

def main():
    cov=reconstruct(); common=validate_parser(); d,dc,vc,basefs=build_restored(); fs=full_features(d,basefs); z=replay(d,vc,basefs,fs);z.to_csv(OUT,index=False)
    clean=z[z.month<='2026-06']; cleanR=clean.R.sum(); shadow=z[z.month>='2026-07']
    old=None
    try:
        q=pd.read_csv(v224.OUT);q=q[q.variant=='+FULL_DECOMP'];old={'R':int(q.R.sum()),'head':np.average(q.head_rate,weights=q.R),'cov':np.average(q.coverage10,weights=np.maximum(q.R*q.head_rate/100,1e-9)),'hit':np.average(q.hit10,weights=q.R),'roi':np.average(q.roi,weights=q.R)}
    except Exception:pass
    L=['# v234 restored-Waku10 v224 replay','', '- DATA-CORRECTION AUDIT ONLY: frozen v224 FULL_DECOMP + frozen v221 pair model; no feature/threshold tuning.', '- 2025-12..2026-06 is the original research window replayed with reconstructed Waku10.', '- 2026-07/08 remain NON-PRISTINE shadow context and are not independent validation.', '- Waku10 parser is matched to BoatraceCSV schema and independently compared against a published August day.', f'- Parser validation common races: {common}, mismatched cells: 0.', '', '## Waku10 reconstruction','|month|days|published days|recovered days|missing days|rows|','|---|---:|---:|---:|---:|---:|']
    c=cov.copy();c['month']=c.date.str[:7]
    for m,g in c.groupby('month'):
        L.append(f"|{m}|{len(g)}|{int((g.source=='published').sum())}|{int((g.source=='recovered').sum())}|{int((g.source=='missing').sum())}|{int(g.rows.sum())}|")
    L += ['', '## Replayed frozen v224 FULL_DECOMP','|month|status|R|avg p3|actual 3-head|gap pp|pair cov10|Top10 hit|settled R|ROI*|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in z.iterrows():
        st='NON-PRISTINE shadow' if r.non_pristine else 'research replay'
        L.append(f"|{r.month}|{st}|{int(r.R)}|{100*r.avg_p3:.2f}%|{100*r.head_rate:.2f}%|{r.gap_pp:+.2f}|{100*r.pair_cov10:.2f}%|{100*r.top10_hit:.2f}%|{int(r.settled_R)}|{r.roi:.2f}%|")
    L += ['', '## Dec2025-Jun2026 aggregate after Waku10 correction']
    if old:
        L += ['|metric|old v224|restored v234|','|---|---:|---:|',f"|R|{old['R']}|{cleanR}|",f"|3-head|{old['head']:.2f}%|{100*np.average(clean.head_rate,weights=clean.R):.2f}%|",f"|pair cov10|{old['cov']:.2f}%|{100*np.average(clean.pair_cov10,weights=np.maximum(clean.R*clean.head_rate,1e-9)):.2f}%|",f"|Top10 hit|{old['hit']:.2f}%|{100*np.average(clean.top10_hit,weights=clean.R):.2f}%|",f"|ROI*|{old['roi']:.2f}%|{np.average(clean.roi,weights=clean.settled_R):.2f}%|"]
    L += ['', '* ROI uses the repository current historical odds loader for exact 10,000-yen Dutch settlement. This is not a true-closing-odds validation because the previously audited loader can use od3 snapshots where official closing is absent.', '', '## Guardrails','- No missing Waku10 value is filled with an invented value. Missing source days/races remain missing.', '- Jul/Aug are never promoted to pristine evidence.', '- Do not adopt new thresholds from this replay.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
