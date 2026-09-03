from __future__ import annotations
import csv, io, urllib.request
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
H0=date(2025,11,1)
TARGET=date(2026,7,20)
POINT={'1':10,'2':8,'3':6,'4':4,'5':2,'6':1,'F':0,'L':0,'転':0,'落':0,'妨':0,'失':0,'不':0,'エ':0}
BONUS={'SG':2,'G1':1,'G2':1,'G3':0,'IP':0}

def fetch(path):
    try:
        req=urllib.request.Request(BASE+path,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=25) as r:
            return r.read().decode('utf-8-sig')
    except Exception:
        return ''

def rows(path):
    s=fetch(path)
    return list(csv.DictReader(io.StringIO(s))) if s else []

def norm_grade(x):
    s=(x or '').upper().replace(' ','')
    if 'SG' in s:return 'SG'
    if 'G1' in s or 'Ｇ１' in s:return 'G1'
    if 'G2' in s or 'Ｇ２' in s:return 'G2'
    if 'G3' in s or 'Ｇ３' in s:return 'G3'
    return 'IP'

def f(x):
    try:return float(x)
    except:return None

def build_history():
    hist=defaultdict(list)
    d=H0
    nday=0
    while d<TARGET:
        ymd=d.strftime('%Y/%m/%d')
        cards={r.get('レースコード',''):r for r in rows(f'data/programs/race_cards/{ymd}.csv')}
        results=rows(f'data/results/realtime/{ymd}.csv')
        titles={r.get('レースコード',''):r for r in rows(f'data/programs/title/{ymd}.csv')}
        for rr in results:
            code=rr.get('レースコード',''); card=cards.get(code)
            if not card: continue
            grade=norm_grade(titles.get(code,{}).get('グレード','IP'))
            finish_by_boat={}
            for p in range(1,7):
                b=(rr.get(f'{p}着_艇番') or '').strip()
                if b.isdigit(): finish_by_boat[int(b)]=str(p)
            course_by_boat={}; st_by_boat={}; f_by_boat={}
            for c in range(1,7):
                bs=(rr.get(f'{c}コース_艇番') or '').strip()
                if not bs.isdigit(): continue
                b=int(bs); v=f(rr.get(f'{c}コース_スタートタイミング'))
                fl=bool((rr.get(f'{c}コース_F') or '').strip())
                course_by_boat[b]=c; f_by_boat[b]=fl
                if v is not None: st_by_boat[b]=(-abs(v) if fl else v)
            order_by_boat={}
            vals=list(st_by_boat.items())
            for b,v in vals:
                order_by_boat[b]=1+sum(1 for bb,vv in vals if vv < v-1e-12)
            for b in range(1,7):
                reg=(card.get(f'艇{b}_登録番号') or '').strip()
                if not reg: continue
                fin='F' if f_by_boat.get(b) else finish_by_boat.get(b,'欠')
                ac=course_by_boat.get(b)
                hist[(reg,b)].append({
                    'code':code,'finish':fin,'entry':None if ac in (None,b) else ac,
                    'grade':grade,'st':st_by_boat.get(b),'is_f':f_by_boat.get(b,False),
                    'start_order':order_by_boat.get(b)
                })
        if d.day==1 or d.day==15: print('history',d,'racer-frame keys',len(hist))
        d+=timedelta(days=1); nday+=1
    for k in hist: hist[k].sort(key=lambda z:z['code'])
    print('history days',nday,'keys',len(hist))
    return hist

def wr_calc(recs):
    pts=0; den=0
    for z in recs:
        fin=z['finish']
        if fin=='欠': continue
        den+=1
        pts += POINT.get(fin,0)+BONUS.get(z['grade'],0)
    return pts/den if den else None

def true_runs(w,b):
    out=[]
    for k in range(1,11):
        fin=(w.get(f'艇{b}_過去{k}走_着順') or '').strip()
        ent=(w.get(f'艇{b}_過去{k}走_進入') or '').strip()
        grd=norm_grade(w.get(f'艇{b}_過去{k}走_グレード'))
        if not fin: continue
        out.append({'finish':fin,'entry':int(ent) if ent.isdigit() else None,'grade':grd})
    return out

def mae(a): return mean(abs(x-y) for x,y in a) if a else None

def main():
    hist=build_history()
    ymd=TARGET.strftime('%Y/%m/%d')
    cards={r.get('レースコード',''):r for r in rows(f'data/programs/race_cards/{ymd}.csv')}
    true=rows(f'data/programs/waku10/{ymd}.csv')
    samples=0; full=0; run_cmp=0; fin_ok=0; ent_ok=0; grade_ok=0
    wr_pairs=[]; st_signed=[]; st_nonf=[]; st_abs=[]; so_pairs=[]
    details=[]
    for w in true:
        code=w.get('レースコード',''); card=cards.get(code)
        if not card: continue
        for b in range(1,7):
            reg=(card.get(f'艇{b}_登録番号') or '').strip()
            if not reg: continue
            tr=true_runs(w,b)
            if not tr: continue
            samples+=1
            recs=hist.get((reg,b),[])[-10:][::-1]
            if len(recs)>=10: full+=1
            n=min(len(tr),len(recs))
            for i in range(n):
                run_cmp+=1
                fin_ok += recs[i]['finish']==tr[i]['finish']
                ent_ok += recs[i]['entry']==tr[i]['entry']
                grade_ok += recs[i]['grade']==tr[i]['grade']
            tw=f(w.get(f'艇{b}_枠番別勝率')); rw=wr_calc(recs)
            if tw is not None and rw is not None: wr_pairs.append((tw,rw))
            tst=f(w.get(f'艇{b}_枠番別平均ST'))
            sts=[z['st'] for z in recs if z['st'] is not None]
            if tst is not None and sts:
                st_signed.append((tst,mean(sts)))
                st_abs.append((tst,mean(abs(x) for x in sts)))
            nf=[z['st'] for z in recs if z['st'] is not None and not z['is_f']]
            if tst is not None and nf: st_nonf.append((tst,mean(nf)))
            tso=f(w.get(f'艇{b}_枠番別平均スタート順'))
            sos=[z['start_order'] for z in recs if z['start_order'] is not None]
            if tso is not None and sos: so_pairs.append((tso,mean(sos)))
            if len(details)<20 and len(recs)>=8:
                details.append((code,b,w.get(f'艇{b}_選手名',''),len(recs),
                                ''.join(x['finish'] for x in tr),''.join(x['finish'] for x in recs),tw,rw,tst,
                                mean(nf) if nf else None,tso,mean(sos) if sos else None))
    def pct(x,n): return 100*x/n if n else 0
    def exact(pairs,digits):
        return pct(sum(round(a,digits)==round(b,digits) for a,b in pairs),len(pairs))
    lines=[]
    lines.append('# v70 擬似waku10再構築 検証')
    lines.append('')
    lines.append(f'- 履歴元: BoatraceCSV race_cards + realtime results + title、{H0}〜{TARGET-timedelta(days=1)}')
    lines.append(f'- 答え合わせ: 本物waku10 {TARGET}')
    lines.append(f'- 艇サンプル: {samples} / 10走フル再構築: {full} ({pct(full,samples):.1f}%)')
    lines.append('')
    lines.append('## 過去10走の一致')
    lines.append(f'- 着順一致: {fin_ok}/{run_cmp} = {pct(fin_ok,run_cmp):.2f}%')
    lines.append(f'- 枠なり外進入一致: {ent_ok}/{run_cmp} = {pct(ent_ok,run_cmp):.2f}%')
    lines.append(f'- グレード一致: {grade_ok}/{run_cmp} = {pct(grade_ok,run_cmp):.2f}%')
    lines.append('')
    lines.append('## 集計値')
    lines.append(f'- 枠番別勝率 MAE: {mae(wr_pairs):.4f} / 表示値一致(小数2桁): {exact(wr_pairs,2):.1f}%')
    lines.append(f'- 平均ST signed全走 MAE: {mae(st_signed):.4f}')
    lines.append(f'- 平均ST F除外 MAE: {mae(st_nonf):.4f} / 表示値一致(小数2桁): {exact(st_nonf,2):.1f}%')
    lines.append(f'- 平均ST abs(F) MAE: {mae(st_abs):.4f}')
    lines.append(f'- 平均スタート順 MAE: {mae(so_pairs):.4f} / 表示値一致(小数1桁): {exact(so_pairs,1):.1f}%')
    lines.append('')
    lines.append('## 判定')
    fin_rate=pct(fin_ok,run_cmp); ent_rate=pct(ent_ok,run_cmp); st_mae=mae(st_nonf) or 9; so_mae=mae(so_pairs) or 9
    adopt = full/max(samples,1)>=.85 and fin_rate>=98.0 and ent_rate>=97.0 and st_mae<=.015 and so_mae<=.35
    lines.append('**長期代替waku10として採用可能**' if adopt else '**まだ本物waku10の完全代替にはしない**')
    lines.append(f'- 機械判定: {"PASS" if adopt else "FAIL"}')
    lines.append('')
    lines.append('## 抜粋')
    lines.append('|race|艇|選手|履歴数|true着順|recon着順|true勝率|recon勝率|trueST|reconST(F除外)|true順|recon順|')
    lines.append('|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|')
    for z in details:
        lines.append(f'|{z[0]}|{z[1]}|{z[2]}|{z[3]}|{z[4]}|{z[5]}|{z[6]}|{z[7]:.2f}|{z[8]}|{z[9]:.3f}|{z[10]}|{z[11]:.2f}|')
    open('summary_v70_waku10_reconstruction.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('\n'.join(lines[:30]))

if __name__=='__main__': main()
