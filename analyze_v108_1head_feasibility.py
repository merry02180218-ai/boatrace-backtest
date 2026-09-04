"""v108: 1号艇頭モデルを運用レベルにできるかの厳格な10か月feasibility test.

Design / no-leak
- Feature period: 2025-11-01..2026-08-31. 2025-10 is used only as prior ST-bias preload.
- Every race's race-card/waku10/current exhibition/ST/original exhibition features and
  the 1-course entry gate are frozen before ANY result/payout file is loaded.
- Daily exhibition-ST frame bias is computed strictly from earlier dates only.
- Development split: Nov-Feb train, Mar-May validation, Jun-Aug untouched holdout.
- BASE vs BASE+VENUE variant is chosen only by validation Brier score.
- A/S operating probability cuts are fixed in advance at 0.65 / 0.72, not tuned on holdout.
- After choosing the variant, it is refit through May and evaluated once on Jun-Aug.
- Current/final odds are never read. Payouts are settlement-only for equal-stake ROI.

This is a feasibility diagnostic, NOT production adoption.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from statistics import mean

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backtest import rows, race_features, grade_score, clamp, pct_motor
from backtest_v51_lane_corrected_tickets import corrected_direct, opp_place_score, ff, ii, normkim

PRELOAD=date(2025,10,1)
START=date(2025,11,1)
TRAIN_END=date(2026,2,28)
VAL_START=date(2026,3,1)
VAL_END=date(2026,5,31)
TEST_START=date(2026,6,1)
END=date(2026,8,31)
A_CUT=.65
S_CUT=.72
OUT='analysis_v108_1head_feasibility.csv'
SUMMARY='summary_v108_1head_feasibility.md'

NUM_FEATURES=[
 'one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength',
 'one_waku_sr_strength','one_past_win','one_meet_st_strength',
 'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score',
 'threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max',
 'margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23',
 'ex_margin23','turn_margin23','straight_margin23'
]


def bycode(rs):
    return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def pct(n,d): return 100*n/d if d else 0.0

def safe_auc(y,p):
    try:return roc_auc_score(y,p) if len(set(y))>1 else float('nan')
    except Exception:return float('nan')
def fmt(x,n=3):
    try:return f'{float(x):.{n}f}'
    except Exception:return '-'

def st_bias(sums,allv):
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}
def update_st(strows,sums,allv):
    for r in strows:
        for b in range(1,7):
            v=ff(r.get(f'艇{b}_スタート展示'))
            if v is not None and -.30<v<1.0:
                sums[b].append(v);allv.append(v)

def source_type(v):
    s=(v or '').strip()
    if not s:return 'missing'
    return 'backfill' if s.startswith('backfill') else 'snapshot'

def period(ds):
    d=date.fromisoformat(ds)
    if d<=TRAIN_END:return 'train4'
    if d<=VAL_END:return 'val3'
    return 'holdout3'

def month(ds):return ds[:7]

def combos20(head,ranked):
    out=[]
    for ia,a in enumerate(ranked,1):
        for ib,b in enumerate(ranked,1):
            if a==b:continue
            out.append((ia+.7*ib,ia,ib,f'{head}-{a}-{b}'))
    out.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    return [z[3] for z in out]

def build_pipe(with_venue=False):
    trs=[('num',StandardScaler(),NUM_FEATURES)]
    if with_venue:
        trs.append(('venue',OneHotEncoder(handle_unknown='ignore'),['venue']))
    pre=ColumnTransformer(trs,remainder='drop')
    return Pipeline([('pre',pre),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])

def Xrows(rs):
    # sklearn ColumnTransformer accepts list-of-dicts via DataFrame most reliably.
    import pandas as pd
    return pd.DataFrame([{k:r.get(k,0) for k in NUM_FEATURES+['venue']} for r in rs])

def fetch_feature_day(d):
    ymd=d.strftime('%Y/%m/%d')
    return d,{
      'cards':rows(f'data/programs/race_cards/{ymd}.csv'),
      'waku':rows(f'data/programs/waku10/{ymd}.csv'),
      'tkz':rows(f'data/previews/tkz/{ymd}.csv'),
      'stt':rows(f'data/previews/stt/{ymd}.csv'),
      'orig':rows(f'data/previews/original_exhibition/{ymd}.csv'),
    }

def fetch_result_day(d):
    ymd=d.strftime('%Y/%m/%d')
    return d,bycode(rows(f'data/results/realtime/{ymd}.csv')),bycode(rows(f'data/results/payouts/{ymd}.csv'))

def feature_row(ds,card,w,tkz,stt,orig,bias):
    code=card.get('レースコード','')
    if not code:return None
    x=race_features(card,w)
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(1,7):
        ex.setdefault(b,.5);st.setdefault(b,.5)
        os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):os[b].setdefault(k,.5)
    sr=stt.get(code,{})
    course=ii(sr.get('艇1_コース'),0)
    entry_status='same' if course==1 else ('changed' if course in range(2,7) else 'missing')
    if entry_status=='changed':return None

    scores={b:opp_place_score(x,b,ex,st,os) for b in range(1,7)}
    ranked=sorted(range(2,7),key=lambda b:scores[b],reverse=True)
    tickets=combos20(1,ranked)
    z=x[1]
    motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
    nst=clamp((.24-z['nst'])/.14)
    wsr=clamp((6-z['waku_sr'])/5)
    meet=.5 if z['meet_st'] is None else clamp((.22-z['meet_st'])/.12)
    direct=.35*ex[1]+.20*st[1]+.25*os[1]['turn']+.20*os[1]['avg']
    t23=max(scores[2],scores[3]);tall=max(scores[b] for b in range(2,7))
    out={
      'date':ds,'period':period(ds),'month':month(ds),'race_code':code,
      'venue':str(card.get('レース場コード','')).zfill(2),'race':card.get('レース回',''),
      'head':1,'entry_course':course,'entry_status':entry_status,'entry_source':source_type(sr.get('取得日時')),
      'one_grade':grade_score(z['grade']),'one_wr':clamp((z['wr']-3)/5),'one_local':clamp((z['local']-2.5)/5.5),
      'one_motor':motor,'one_waku_wr':clamp(z['waku_wr']/8),'one_nst_strength':nst,
      'one_waku_sr_strength':wsr,'one_past_win':z['past_win'],'one_meet_st_strength':meet,
      'one_ex':ex[1],'one_st':st[1],'one_lap':os[1]['lap'],'one_turn':os[1]['turn'],
      'one_straight':os[1]['straight'],'one_orig_avg':os[1]['avg'],'one_direct':direct,'one_score':scores[1],
      'threat2':scores[2],'threat3':scores[3],'threat4':scores[4],'threat5':scores[5],'threat6':scores[6],
      'threat23_max':t23,'threat_all_max':tall,
      'margin2':scores[1]-scores[2],'margin3':scores[1]-scores[3],
      'margin23':scores[1]-t23,'margin_all':scores[1]-tall,
      'st_margin2':st[1]-st[2],'st_margin3':st[1]-st[3],'st_margin23':st[1]-max(st[2],st[3]),
      'ex_margin23':ex[1]-max(ex[2],ex[3]),
      'turn_margin23':os[1]['turn']-max(os[2]['turn'],os[3]['turn']),
      'straight_margin23':os[1]['straight']-max(os[2]['straight'],os[3]['straight']),
      'ranked_others':'-'.join(map(str,ranked)),'tickets20_display':';'.join(tickets),
      'has_tkz':int(code in tkz),'has_stt':int(code in stt),'has_orig':int(code in orig),
    }
    return out

def freeze_all_features():
    days=[];d=PRELOAD
    while d<=END:days.append(d);d+=timedelta(days=1)
    fetched={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(fetch_feature_day,d) for d in days]
        for i,f in enumerate(as_completed(futs),1):
            try:
                dd,z=f.result();fetched[dd]=z
            except Exception as e:print('feature fetch fail',e,flush=True)
            if i%30==0:print('feature days fetched',i,'/',len(days),flush=True)

    sums=defaultdict(list);allv=[];frozen=[];cover=defaultdict(int)
    for d in sorted(fetched):
        z=fetched[d];bias=st_bias(sums,allv)
        if d>=START:
            wm=bycode(z['waku']);tm=bycode(z['tkz']);sm=bycode(z['stt']);om=bycode(z['orig'])
            cover['card_races']+=len(z['cards']);cover['waku_races']+=len(wm)
            for card in z['cards']:
                code=card.get('レースコード','')
                if not code or code not in wm:
                    cover['missing_waku']+=1;continue
                try:r=feature_row(str(d),card,wm[code],tm,sm,om,bias)
                except Exception:
                    cover['feature_error']+=1;continue
                if r is None:
                    cover['entry_changed']+=1;continue
                frozen.append(r)
                cover['frozen']+=1;cover['tkz']+=r['has_tkz'];cover['stt']+=r['has_stt'];cover['orig']+=r['has_orig']
        # only after current date is frozen, update bias for future dates
        update_st(z['stt'],sums,allv)
    return frozen,cover

def settle_after_freeze(frozen):
    days=sorted({date.fromisoformat(r['date']) for r in frozen})
    results={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs=[ex.submit(fetch_result_day,d) for d in days]
        for i,f in enumerate(as_completed(futs),1):
            try:
                d,res,pay=f.result();results[d]=(res,pay)
            except Exception as e:print('result fetch fail',e,flush=True)
            if i%30==0:print('result days fetched',i,'/',len(days),flush=True)
    out=[]
    for r in frozen:
        d=date.fromisoformat(r['date']);res,pay=results.get(d,({},{}));code=r['race_code']
        rr=res.get(code,{});pr=pay.get(code,{})
        win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
        combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
        tickets=r['tickets20_display'].split(';') if r['tickets20_display'] else []
        q=dict(r);q.update({
          'valid_result':int(win in range(1,7)),'winner':win,'kimarite':kim,
          'head_hit':int(win==1),'escape_hit':int(win==1 and kim=='逃げ'),
          'valid_payout':int(bool(combo) and payout>0),'actual_combo':combo,'payout100':payout,
          'actual_ticket_rank20':tickets.index(combo)+1 if combo in tickets else 0,
        })
        out.append(q)
    return out

def fit_variant(train,with_venue):
    p=build_pipe(with_venue);p.fit(Xrows(train),[r['head_hit'] for r in train]);return p

def predict(model,rs):
    return model.predict_proba(Xrows(rs))[:,1] if rs else np.array([])
def eval_prob(rs,probs):
    y=[r['head_hit'] for r in rs]
    return safe_auc(y,probs),brier_score_loss(y,probs) if y else float('nan')
def select_prob(rs,cut):return [r for r in rs if float(r.get('p1',0))>=cut]

def candidate_metrics(rs):
    q=[r for r in rs if r['valid_result']]
    n=len(q);hh=sum(r['head_hit'] for r in q);esc=sum(r['escape_hit'] for r in q)
    return n,hh,pct(hh,n),esc,pct(esc,n)
def point_metric(rs,npt):
    q=[r for r in rs if r['valid_payout']]
    hit=[r for r in q if 0<int(r['actual_ticket_rank20'])<=npt]
    inv=len(q)*npt*100;ret=sum(r['payout100'] for r in hit)
    heads=[r for r in q if r['head_hit']]
    cov=sum(1 for r in heads if 0<int(r['actual_ticket_rank20'])<=npt)
    return len(q),len(hit),pct(len(hit),len(q)),pct(cov,len(heads)),pct(ret,inv)
def allbase(rs):
    q=[r for r in rs if r['valid_result']];n=len(q);w=sum(r['head_hit'] for r in q)
    return n,pct(w,n)

def write_csv(path,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def feature_importance(pipe):
    try:
        pre=pipe.named_steps['pre'];names=list(pre.get_feature_names_out());coef=pipe.named_steps['lr'].coef_[0]
        z=sorted(zip(names,coef),key=lambda x:abs(x[1]),reverse=True)
        return z[:15]
    except Exception:return []

def main():
    frozen,cover=freeze_all_features()
    print('ALL FEATURES FROZEN:',len(frozen),'-- only now results/payouts are fetched',flush=True)
    settled=settle_after_freeze(frozen)
    settled=[r for r in settled if r['valid_result']]
    tr=[r for r in settled if r['period']=='train4'];va=[r for r in settled if r['period']=='val3'];te=[r for r in settled if r['period']=='holdout3']

    # Train-only model fit; validation chooses only whether venue one-hot improves calibration.
    mbase=fit_variant(tr,False);mvenue=fit_variant(tr,True)
    pb=predict(mbase,va);pv=predict(mvenue,va)
    aucb,bb=eval_prob(va,pb);aucv,bv=eval_prob(va,pv)
    chosen_venue=bool(bv+1e-6<bb)
    chosen='BASE+VENUE' if chosen_venue else 'BASE'

    # Refit chosen architecture through May; June-Aug is untouched until now.
    refit=fit_variant(tr+va,chosen_venue)
    ptest=predict(refit,te)
    for r,p in zip(te,ptest):r['p1']=round(float(p),8)
    # Also save validation probabilities from the train-only chosen model for audit.
    pval=pv if chosen_venue else pb
    for r,p in zip(va,pval):r['p1']=round(float(p),8)
    for r,p in zip(tr,predict(refit,tr)):r['p1_refit_audit']=round(float(p),8)

    a=select_prob(te,A_CUT);s=select_prob(te,S_CUT)
    base_n,base_r=allbase(te);an,ah,ar,ae,aer=candidate_metrics(a);sn,sh,sr,se,ser=candidate_metrics(s)
    feasible=(an>=300 and ar>=65.0 and sn>=100 and sr>=72.0)

    write_csv(OUT,tr+va+te)

    L=['# v108 1号艇頭モデル feasibility','',
       f'期間: **{START}〜{END}**。train4=11-2月 / validation3=3-5月 / untouched holdout3=6-8月。',
       '全レースの事前特徴（race card / waku10 / 展示 / 枠補正展示ST / オリジナル展示 / 展示進入）を先に完全freezeし、その後に結果・払戻をロード。確定/締切オッズは一切使用していない。',
       f'1号艇展示進入changedは除外。missingは保持して別記。A確率cut=**{A_CUT:.0%}**、S=**{S_CUT:.0%}**はholdoutを見る前に固定。','',
       '## データcoverage',
       f'- frozen: **{cover["frozen"]:,}R** / entry changed除外 **{cover["entry_changed"]:,}R** / feature error **{cover["feature_error"]:,}R**',
       f'- preview coverage: tkz **{pct(cover["tkz"],cover["frozen"]):.1f}%** / stt **{pct(cover["stt"],cover["frozen"]):.1f}%** / original **{pct(cover["orig"],cover["frozen"]):.1f}%**','',
       '## validationでのモデル構造選択',
       '|構造|AUC|Brier|','|---|---:|---:|',
       f'|BASE|{fmt(aucb)}|{fmt(bb,4)}|',f'|BASE+VENUE|{fmt(aucv)}|{fmt(bv,4)}|',
       f'選択: **{chosen}**（validation Brierが低い方だけを選択）。その構造を5月末まででrefitし、6-8月を1回だけ評価。','',
       '## untouched Jun-Aug head performance',
       '|層|R|1着|頭率|逃げ|逃げ率|raw比|','|---|---:|---:|---:|---:|---:|---:|',
       f'|全1号艇|{base_n:,}|-|{base_r:.1f}%|-|-|基準|',
       f'|A p>=65%|{an:,}|{ah}|{ar:.1f}%|{ae}|{aer:.1f}%|{ar-base_r:+.1f}pt|',
       f'|S p>=72%|{sn:,}|{sh}|{sr:.1f}%|{se}|{ser:.1f}%|{sr-base_r:+.1f}pt|','',
       '## 月別 stability','|月|全1頭率|A R|A頭率|A lift|S R|S頭率|S lift|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for mo in ['2026-06','2026-07','2026-08']:
        qm=[r for r in te if r['month']==mo];bn,br=allbase(qm);aa=select_prob(qm,A_CUT);ss=select_prob(qm,S_CUT)
        anm,_,arm,_,_=candidate_metrics(aa);snm,_,srm,_,_=candidate_metrics(ss)
        L.append(f'|{mo}|{br:.1f}%|{anm}|{arm:.1f}%|{arm-br:+.1f}pt|{snm}|{srm:.1f}%|{srm-br:+.1f}pt|')

    L+=['','## 相手選び：現行v51相手scoreで1頭固定20通り','',
        '2〜6号艇を現行v51 opponent scoreで事前順位化し、現行20点display orderを固定。以下はJun-Aug holdout。',
        '|層|点数|3連単的中率|頭的中時coverage|均等買いROI|','|---|---:|---:|---:|---:|']
    for label,q in [('A',a),('S',s)]:
        for npt in [1,2,3,4,5,6,7,8,10,12,15,20]:
            _,_,hr,covr,roi=point_metric(q,npt)
            L.append(f'|{label}|{npt}|{hr:.1f}%|{covr:.1f}%|{roi:.1f}%|')

    L+=['','## 係数上位（refit後・符号付き）','|feature|coef|','|---|---:|']
    for name,c in feature_importance(refit):L.append(f'|{name}|{c:+.3f}|')
    L+=['','## v108 feasibility判定',
        f'- A: 300R以上かつ頭率65%以上 → **{"PASS" if an>=300 and ar>=65 else "FAIL"}**',
        f'- S: 100R以上かつ頭率72%以上 → **{"PASS" if sn>=100 and sr>=72 else "FAIL"}**',
        f'- **V108 FEASIBILITY = {"PASS" if feasible else "FAIL"}**',
        '- PASSでもproduction採用ではない。次段階で月次walk-forward、相手2/3着役割分離、点数・価格評価を固定して再検証する。',
        '- 最終/締切オッズはこのv108の選択・学習・判定に一切使っていない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
