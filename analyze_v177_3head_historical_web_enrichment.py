#!/usr/bin/env python3
"""v177: no-leak historical web enrichment for 3-head development prediction.

Purpose
- Recover racer registration numbers from public historical race-card CSVs.
- Build boat1 defensive style and boat3 attack style from PRIOR completed races only.
- Carry the racer's latest PRIOR exhibition / original-exhibition relative strength.
- Compare v176 base features vs enriched features on Jun-Aug OOS.

NO LEAK
- Current-race exhibition is NOT used.
- Current-race result/kimarite is target only.
- Style/exhibition state is read before the current race then updated after it.
- Every evaluation month is trained only on earlier dates.

The public historical source is the same BoatraceCSV tree already used by this repo.
BOATBoy current new-concept values are useful for prospective/live use, but are not
backfilled into historical races because today's rolling value would leak future data.
"""
from __future__ import annotations
import csv, math
from collections import defaultdict, Counter
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score

from backtest import rows
from analyze_v166_3head_pair_direct import read, ff, ii, combo, SRC
from analyze_v175_3head_prerace_development_softpair import race_feat, method

OUT='analysis_v177_3head_historical_web_enrichment.csv'
SUMMARY='summary_v177_3head_historical_web_enrichment.md'
TEST_MONTHS=['2026-06','2026-07','2026-08']
START=date(2025,10,1); END=date(2026,8,31)

def bycode(rs): return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}
def pick(r,*ks):
    for k in ks:
        v=str(r.get(k,'')).strip()
        if v:return v
    return ''
def racer_id(card,b):
    return pick(card,f'艇{b}_登録番号',f'艇{b}_選手登録番号',f'艇{b}_選手番号',f'艇{b}_登録No',f'艇{b}_登録Ｎｏ')
def result_winner(rr):
    return ii(rr.get('1着_艇番'))
def result_method(rr):
    s=str(rr.get('決まり手','')).replace('　','').replace(' ','')
    if 'まくり差し' in s or '捲り差し' in s:return 'makuri-sashi'
    if 'まくり' in s or '捲り' in s:return 'makuri'
    if '差し' in s:return 'sashi-other'
    return ''
def actual_course(strow,b):
    return ii(strow.get(f'艇{b}_コース'),b)

def rank_strength(vals,lower_better=True):
    z={b:v for b,v in vals.items() if v is not None and math.isfinite(v)}
    if not z:return {}
    order=sorted(z,key=lambda b:z[b],reverse=not lower_better)
    n=max(len(order)-1,1)
    return {b:1.0-i/n for i,b in enumerate(order)}
def fv(x):
    try:
        v=float(x);return v if math.isfinite(v) else None
    except:return None

def exhibition_strengths(tk,orow):
    ex={b:fv(tk.get(f'艇{b}_展示タイム')) for b in range(1,7)}
    exs=rank_strength(ex,True)
    metrics={}
    for j in range(1,5):
        name=str(orow.get(f'計測項目{j}','')).strip()
        if not name:continue
        vv={b:fv(orow.get(f'艇{b}_値{j}')) for b in range(1,7)}
        ss=rank_strength(vv,True)
        nl=name.replace(' ','').replace('　','')
        if '一周' in nl: key='lap'
        elif 'まわり' in nl or '回り' in nl: key='turn'
        elif '直線' in nl: key='straight'
        else: key=f'orig{j}'
        metrics[key]=ss
    out={}
    for b in range(1,7):
        d={'ex':exs.get(b,.5),'lap':.5,'turn':.5,'straight':.5}
        for k in ('lap','turn','straight'):
            if k in metrics:d[k]=metrics[k].get(b,.5)
        d['orig_avg']=(d['lap']+d['turn']+d['straight'])/3
        out[b]=d
    return out

def target(r):
    m=method(r)
    if m=='makuri':return 0
    if m=='makuri-sashi':return 1
    return None

def fetch_days():
    src={}
    d=START
    while d<=END:
        y=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{y}.csv')
        if cards:
            src[d]={
              'cards':cards,
              'stt':bycode(rows(f'data/previews/stt/{y}.csv')),
              'tkz':bycode(rows(f'data/previews/tkz/{y}.csv')),
              'orig':bycode(rows(f'data/previews/original_exhibition/{y}.csv')),
              'res':bycode(rows(f'data/results/realtime/{y}.csv')),
            }
        d+=timedelta(days=1)
    return src

def reconstruct(base):
    idx={(r.get('date',''),r.get('race_code','')):i for i,r in enumerate(base)}
    feats={i:{} for i in range(len(base))}
    p1=defaultdict(lambda:Counter(starts=0,makurare=0,sasare=0,escape=0))
    p3=defaultdict(lambda:Counter(starts=0,makuri=0,makuri_sashi=0,head=0))
    prev_ex={}
    coverage=Counter()
    data=fetch_days()
    for d in sorted(data):
        z=data[d]; cards=sorted(z['cards'],key=lambda r:r.get('レースコード',''))
        for card in cards:
            code=card.get('レースコード',''); key=(str(d),code)
            strow=z['stt'].get(code,{})
            ids={b:racer_id(card,b) for b in range(1,7)}
            if ids[1]:coverage['id1']+=1
            if ids[3]:coverage['id3']+=1
            if key in idx:
                i=idx[key]; k1=ids[1];k3=ids[3]
                a=p1[k1] if k1 else Counter(); b=p3[k3] if k3 else Counter()
                da=max(a.get('starts',0),1);db=max(b.get('starts',0),1)
                pe=prev_ex.get(k3,{})
                feats[i]={
                  'b1_hist_starts':a.get('starts',0),
                  'b1_makurare_rate':a.get('makurare',0)/da,
                  'b1_sasare_rate':a.get('sasare',0)/da,
                  'b1_escape_rate':a.get('escape',0)/da,
                  'b3_hist_starts':b.get('starts',0),
                  'b3_makuri_rate':b.get('makuri',0)/db,
                  'b3_makuri_sashi_rate':b.get('makuri_sashi',0)/db,
                  'b3_head_rate':b.get('head',0)/db,
                  'style_makuri_edge':b.get('makuri',0)/db-a.get('makurare',0)/da,
                  'style_makurisashi_edge':b.get('makuri_sashi',0)/db-a.get('sasare',0)/da,
                  'b3_prev_ex':pe.get('ex',.5),'b3_prev_lap':pe.get('lap',.5),
                  'b3_prev_turn':pe.get('turn',.5),'b3_prev_straight':pe.get('straight',.5),
                  'b3_prev_orig_avg':pe.get('orig_avg',.5),'b3_has_prev_ex':1.0 if pe else 0.0,
                }
                coverage['matched_src']+=1
                if pe:coverage['matched_prev_ex']+=1
            # update states only after current feature extraction
            rr=z['res'].get(code,{})
            win=result_winner(rr); km=result_method(rr)
            if win in range(1,7):
                c1=actual_course(strow,1); c3=actual_course(strow,3)
                k1=ids[1];k3=ids[3]
                if k1 and c1==1:
                    q=p1[k1];q['starts']+=1
                    if win==1:q['escape']+=1
                    elif km=='makuri':q['makurare']+=1
                    elif km in ('makuri-sashi','sashi-other'):q['sasare']+=1
                if k3 and c3==3:
                    q=p3[k3];q['starts']+=1
                    if win==3:q['head']+=1
                    if win==3 and km=='makuri':q['makuri']+=1
                    if win==3 and km=='makuri-sashi':q['makuri_sashi']+=1
            tk=z['tkz'].get(code,{}); oo=z['orig'].get(code,{})
            if tk or oo:
                ss=exhibition_strengths(tk,oo)
                for b in range(1,7):
                    if ids[b]:prev_ex[ids[b]]=ss[b]
    defaults={
      'b1_hist_starts':0,'b1_makurare_rate':0.,'b1_sasare_rate':0.,'b1_escape_rate':0.,
      'b3_hist_starts':0,'b3_makuri_rate':0.,'b3_makuri_sashi_rate':0.,'b3_head_rate':0.,
      'style_makuri_edge':0.,'style_makurisashi_edge':0.,'b3_prev_ex':.5,'b3_prev_lap':.5,
      'b3_prev_turn':.5,'b3_prev_straight':.5,'b3_prev_orig_avg':.5,'b3_has_prev_ex':0.
    }
    for i in range(len(base)):
        if not feats[i]:feats[i]=dict(defaults)
        else:
            for k,v in defaults.items():feats[i].setdefault(k,v)
    return feats,coverage

EXTRA=['b1_hist_starts','b1_makurare_rate','b1_sasare_rate','b1_escape_rate','b3_hist_starts','b3_makuri_rate','b3_makuri_sashi_rate','b3_head_rate','style_makuri_edge','style_makurisashi_edge','b3_prev_ex','b3_prev_lap','b3_prev_turn','b3_prev_straight','b3_prev_orig_avg','b3_has_prev_ex']
def vec(r,e,enriched):
    x=list(race_feat(r))
    if enriched:x.extend(float(e[k]) for k in EXTRA)
    return x

def eval_month(base,extra,mo,enriched):
    first=date.fromisoformat(mo+'-01');X=[];y=[];te=[];yt=[]
    for i,r in enumerate(base):
        if ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));t=target(r)
        if len(a)!=3 or a[0]!=3 or t is None:continue
        if date.fromisoformat(r['date'])<first:X.append(vec(r,extra[i],enriched));y.append(t)
        elif r.get('month')==mo:te.append(vec(r,extra[i],enriched));yt.append(t)
    if len(X)<300 or len(te)<5:return None
    m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.25,max_iter=1800,solver='lbfgs'))])
    m.fit(np.asarray(X,float),np.asarray(y,int));p=m.predict_proba(np.asarray(te,float))[:,1];yy=np.asarray(yt,int)
    return {'month':mo,'variant':'enriched' if enriched else 'base','n':len(yy),'auc':roc_auc_score(yy,p),'logloss':log_loss(yy,p,labels=[0,1]),'accuracy':accuracy_score(yy,(p>=.5).astype(int)),'train_n':len(y)}

def main():
    base=read(SRC); extra,cov=reconstruct(base);out=[]
    for mo in TEST_MONTHS:
        for en in (False,True):
            q=eval_month(base,extra,mo,en)
            if q:out.append(q)
    fs=['month','variant','n','auc','logloss','accuracy','train_n']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v177 ③頭・historical web enrichment OOS','',
       '- 公開historical race-cardから選手登録番号を復元。','- ①1コース防御率・③3コース攻撃率は、そのレースより前の完了レースだけでrolling生成。','- ③前走展示/オリ展は直前の過去走だけを使用し、レース内相対rankに変換。','- 現在レースの展示は使用しない。実決まり手はtargetのみ。','- BOATBoyの現在値を過去へ貼ることはしない（future leakage防止）。','',
       '## reconstruction coverage',f"- SRC matched: {cov['matched_src']}",f"- matched rows with prior exhibition: {cov['matched_prev_ex']}",f"- historical card rows with boat1 id: {cov['id1']}",f"- historical card rows with boat3 id: {cov['id3']}",'',
       '## Jun-Aug OOS base vs enriched','|month|variant|N|AUC|logloss|accuracy|train N|','|---|---|---:|---:|---:|---:|---:|']
    for r in out:L.append(f"|{r['month']}|{r['variant']}|{r['n']}|{r['auc']:.3f}|{r['logloss']:.3f}|{100*r['accuracy']:.1f}%|{r['train_n']}|")
    L+=['','## 判定','- enrichedが3か月でAUC/loglossを安定改善するなら、事前展開確率の正式候補。','- 一部月だけ改善なら採用せず、特徴別ablationを次に行う。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
