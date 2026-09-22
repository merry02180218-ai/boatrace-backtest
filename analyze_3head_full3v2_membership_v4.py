#!/usr/bin/env python3
"""3HEAD PLAYER_HISTORY shadow audit on current restored Waku10 basis.
Uses the same causal player-history family independently audited in 4HEAD.
September 2026 outcomes are never read. No production changes.
"""
from __future__ import annotations
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v234_3head_waku10_restored_replay as v234
from backtest import rows

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_3head_full3v2_membership_v4.csv'
SUM=ROOT/'summary_3head_full3v2_membership_v4.md'
MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
START=date(2025,10,1); END=date(2026,8,31)
NAMES=['all_win','all_p2','frame_win','frame_p2','recent_p2']

def rc(x): return str(x or '').strip().replace('.0','').zfill(12)
def ii(x):
    try:return int(float(x))
    except:return 0
def blank():return {'n':0,'w':0,'p2':0,'nf':defaultdict(int),'wf':defaultdict(int),'p2f':defaultdict(int),'r':deque(maxlen=30)}
def stat(q,b):
    if q is None:return [1/6,1/3,.125,.25,1/3]
    n=q['n'];return [(q['w']+2/6)/(n+2),(q['p2']+2/3)/(n+2),(q['wf'][b]+3*.125)/(q['nf'][b]+3),(q['p2f'][b]+3*.25)/(q['nf'][b]+3),sum(q['r'])/len(q['r']) if q['r'] else 1/3]

def add_player_history(d):
    idx=defaultdict(list)
    for ix,r in d.iterrows(): idx[rc(r.get('race_code'))].append(ix)
    players=defaultdict(blank); extra={}; day=START
    while day<=END:
        y=day.strftime('%Y/%m/%d'); cards={rc(x.get('レースコード')):x for x in rows(f'data/programs/race_cards/{y}.csv')}
        for code,card in cards.items():
            if code not in idx:continue
            z={}
            for b in range(1,7):
                reg=str(card.get(f'艇{b}_登録番号','')).strip(); vals=stat(players.get(reg),b)
                for k,v in zip(NAMES,vals):z[f'b{b}_pl_{k}']=v
            for ix in idx[code]:extra[ix]=z
        # strict prior-date: update only after all target-day features are frozen
        rm={rc(x.get('レースコード')):x for x in rows(f'data/results/realtime/{y}.csv')}
        for code,card in cards.items():
            rr=rm.get(code);w=ii((rr or {}).get('1着_艇番'));s=ii((rr or {}).get('2着_艇番'))
            if w not in range(1,7) or s not in range(1,7) or w==s:continue
            for b in range(1,7):
                reg=str(card.get(f'艇{b}_登録番号','')).strip()
                if not reg:continue
                q=players[reg];q['n']+=1;q['w']+=int(w==b);q['p2']+=int(w==b or s==b);q['nf'][b]+=1;q['wf'][b]+=int(w==b);q['p2f'][b]+=int(w==b or s==b);q['r'].append(int(w==b or s==b))
        day+=timedelta(days=1)
    return d.join(pd.DataFrame.from_dict(extra,orient='index'),how='left')

def metrics(g):
    y=g.y.astype(int);p=g.p
    return (roc_auc_score(y,p) if y.nunique()>1 else np.nan,brier_score_loss(y,p),log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1]))

def main():
    # Current accepted restored-Waku10 feature basis.
    if not v234.REST.exists(): raise RuntimeError('v234 restored Waku10 not materialized')
    d,dc,vc,basefs=v234.build_restored()
    existing=[f'b{b}_pl_{k}' for b in range(1,7) for k in NAMES if f'b{b}_pl_{k}' in d.columns]
    if len(existing)==30:
        print('PLAYER_HISTORY_ALREADY_PRESENT',len(existing))
    else:
        d=add_player_history(d)
    own=[f'b3_pl_{k}' for k in NAMES]
    b2=[f'b2_pl_{k}' for k in NAMES];b4=[f'b4_pl_{k}' for k in NAMES]
    for k in NAMES:
        d[f'pl_rel3_2_{k}']=pd.to_numeric(d[f'b3_pl_{k}'],errors='coerce')-pd.to_numeric(d[f'b2_pl_{k}'],errors='coerce')
        d[f'pl_rel3_4_{k}']=pd.to_numeric(d[f'b3_pl_{k}'],errors='coerce')-pd.to_numeric(d[f'b4_pl_{k}'],errors='coerce')
    rel32=[f'pl_rel3_2_{k}' for k in NAMES];rel34=[f'pl_rel3_4_{k}' for k in NAMES]
    all30=[f'b{b}_pl_{k}' for b in range(1,7) for k in NAMES]
    waku=v234.full_features(d,basefs)
    groups={'SAFE_WAKU_BASE':waku,'FULL_3V2':waku+own+b2+rel32}
    pred=[]
    for mon in MONTHS:
        first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1)
        for name,fs0 in groups.items():
            fs=v223.uniq([x for x in fs0 if x in d.columns])
            te,nf=v223.fit_head(d,fs,vc,first,nxt)
            for _,r in te.iterrows():pred.append({'variant':name,'month':mon,'race_code':rc(r.get('race_code')),'p':float(r._p),'y':int(r._y),'nfeat':nf})
    p=pd.DataFrame(pred); out=[]
    # Volume-match every variant to BASE top-k per month; no new probability cut tuning.
    for mon in MONTHS:
        bm=p[(p.variant=='SAFE_WAKU_BASE')&(p.month==mon)]; k=max(1,int((bm.p>=.30).sum()))
        for name in groups:
            g=p[(p.variant==name)&(p.month==mon)].copy();auc,brier,ll=metrics(g);sel=g.nlargest(k,'p')
            out.append({'variant':name,'month':mon,'R':len(g),'auc':auc,'brier':brier,'logloss':ll,'selected_R':len(sel),'selected_heads':int(sel.y.sum()),'selected_head_rate':float(sel.y.mean()),'volume_match_k':k})
    z=pd.DataFrame(out)
    # Explicit membership delta at fixed monthly BASE volume.
    mem=[]
    for mon in MONTHS:
        bm=p[(p.variant=='SAFE_WAKU_BASE')&(p.month==mon)]; k=max(1,int((bm.p>=.30).sum()))
        sets={name:set(p[(p.variant==name)&(p.month==mon)].nlargest(k,'p').race_code) for name in groups}
        base=sets['SAFE_WAKU_BASE']; full=sets['FULL_3V2']
        mem.append({'month':mon,'k':k,'overlap':len(base&full),'entered':len(full-base),'exited':len(base-full)})
    pd.DataFrame(mem).to_csv(ROOT/'analysis_3head_full3v2_membership_delta_v4.csv',index=False)
    z.to_csv(OUT,index=False)
    L=['# 3HEAD FULL_3V2 fixed membership integration v4','',
       '- Current restored/safe Waku10 basis is fixed; no frozen-v243 identity requirement.',
       '- PLAYER_HISTORY uses strict prior-date results and the same 30-feature definitions independently audited in 4HEAD.',
       '- Fixed comparison only: SAFE_WAKU_BASE vs frozen FULL_3V2. No feature search.',
       '- Selection volume is matched to SAFE_WAKU_BASE p>=.30 count per month. No new cut is tuned.',
       '- Jul/Aug are NON-PRISTINE descriptive shadow. September outcomes are UNREAD. Production unchanged.','',
       '|variant|R|AUC|Brier|LogLoss|selected R|heads|head rate|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in groups:
        q=z[z.variant==name];R=int(q.R.sum());sr=int(q.selected_R.sum());sh=int(q.selected_heads.sum())
        # model-quality rows are equal-sized monthly populations, so R-weighted aggregate.
        L.append(f"|{name}|{R}|{np.average(q.auc,weights=q.R):.4f}|{np.average(q.brier,weights=q.R):.5f}|{np.average(q.logloss,weights=q.R):.5f}|{sr}|{sh}|{100*sh/sr:.2f}%|")
    L+=['','## Monthly selected head rate','|variant|'+'|'.join(MONTHS)+'|','|---|'+'|'.join(['---:']*len(MONTHS))+'|']
    for name in groups:
        q=z[z.variant==name].set_index('month');L.append('|'+name+'|'+'|'.join(f"{100*q.loc[m,'selected_head_rate']:.2f}% ({int(q.loc[m,'selected_R'])}R)" for m in MONTHS)+'|')
    L+=['','FULL3V2_MEMBERSHIP_V4_OK','SEPTEMBER_UNREAD','PRODUCTION_UNCHANGED']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
    meta={'strict_prior_date':True,'same_day_results_used':False,'threshold_tuning':False,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False}
    (ROOT/'analysis_3head_full3v2_membership_v4_meta.json').write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__':main()
