#!/usr/bin/env python3
"""4号艇86R/78R研究候補へ frozen production S(PRE/POST/ENV_ENTRY) を重ねる監査。

目的:
- 現在の164Rは head-rate研究候補であり、production S候補そのものではない。
- Jul-Aug comp>=7 の失速が、production本来の frozen S scores で事前に識別できるか確認する。
- 閾値は現行 frozen 値を一切動かさない。
- Jul/Aug outcomes は retrospective validation/diagnostic としてのみ使用可。
- September 2026 outcomes/results は絶対に読まない。
"""
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import json
import numpy as np
import pandas as pd

from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_v250_4head_rebuild_baseline as v250
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v221_3head_scenario_pair as v221
import analyze_v264_4head_feature_exhaustive as v264
import freeze_4head_v291_downstream_artifacts as freeze
from head4_v291_downstream_inference import load_artifact, score_post, score_env_entry
import audit_4head_julaug_roi_collapse_attribution as market

OUT=Path('/tmp/head4_production_s_overlay'); OUT.mkdir(parents=True,exist_ok=True)
START='2026-04-01'; END='2026-08-31'
PRE_CUT=.28; POST_CUT=.25; ENV_CUT=.224790
PRE_COLS=[
 'legacy_score4','racer4','hist_st_edge_4v3','wall3_weak','inner12_resistance',
 'motor4_2ren','motor4_hist','turnfoot4_prior','past_win4'
]

def build_v250_features_to_aug():
    """Exact v250 causal PRE/POST feature rows through Aug, without reading result rows."""
    cache={}; hist=defaultdict(list); seen=set(); d=v250.PRELOAD_START_V250
    while d<v250.START:
        ingest_motor(hist,seen,d)
        if d>=v250.START-timedelta(days=12): ingest_prior_day_preview(cache,d)
        d+=timedelta(days=1)
    out=[]
    stop=date(2026,8,31)
    while d<=stop:
        ymd=d.strftime('%Y/%m/%d')
        tkz=v250.by_code(f'data/previews/tkz/{ymd}.csv')
        stt=v250.by_code(f'data/previews/stt/{ymd}.csv')
        orig=v250.by_code(f'data/previews/original_exhibition/{ymd}.csv')
        for r,x,s4,_s5,_dc in process_features(d,cache,hist):
            z={'date':str(d),'race_code':str(r['レースコード']).zfill(12)}
            z.update(v250.pre_features(x,s4)); z.update(v250.post_features(z['race_code'],tkz,stt,orig))
            out.append(z)
        ingest_prior_day_preview(cache,d); ingest_motor(hist,seen,d); d+=timedelta(days=1)
    q=pd.DataFrame(out); q['_date']=pd.to_datetime(q.date)
    if q.empty or q._date.max()>=pd.Timestamp('2026-09-01'): raise RuntimeError('September feature access blocked')
    return q

def frozen_pre_model():
    """Fit exact frozen PRE state only through 2026-06-30 and verify June walk-forward lineage."""
    trall=freeze.build_v250_frame()
    if trall._date.max()>=pd.Timestamp('2026-07-01'): raise RuntimeError('PRE training cutoff breach')
    # lineage parity for June: train strictly before June and compare archived v250 PRE.
    tr=trall[trall._date<pd.Timestamp('2026-06-01')].copy()
    te=trall[(trall._date>=pd.Timestamp('2026-06-01'))&(trall._date<pd.Timestamp('2026-07-01'))].copy()
    mj=v250.make_model(PRE_COLS); mj.fit(tr[PRE_COLS],tr.y4head.astype(int))
    pred=te[['race_code']].copy(); pred['pred']=mj.predict_proba(te[PRE_COLS])[:,1]
    ref=pd.read_csv(v250.OUT,dtype={'race_code':str})
    ref=ref[(ref.month=='2026-06')&(ref.variant=='PRE')][['race_code','p4head']]
    n,err=freeze.max_abs_join(pred,ref,'pred','p4head')
    if err>freeze.TOL_POST: raise RuntimeError(f'PRE June parity failed n={n} max_abs={err}')
    mf=v250.make_model(PRE_COLS); mf.fit(trall[PRE_COLS],trall.y4head.astype(int))
    return mf, {'june_rows':n,'june_max_abs':err,'train_R':len(trall),'max_training_date':str(trall._date.max().date())}

def build_env_frame(score_rows):
    """Rebuild pre-result ENV feature rows, then replace PRE/POST by frozen final scores."""
    raw=pd.DataFrame(c4.read())
    raw['race_code']=raw.race_code.astype(str).str.zfill(12)
    raw['_date']=pd.to_datetime(raw.date,errors='coerce')
    if raw['_date'].max()>=pd.Timestamp('2026-09-01'): raise RuntimeError('September source present: fail closed')
    raw=v221.build(raw,'date')
    raw['date']=raw.date.astype(str)
    x=raw.merge(score_rows[['date','race_code','PRE_frozen','POST_frozen']],on=['date','race_code'],how='inner',validate='one_to_one')
    x['PRE']=x.PRE_frozen; x['POST']=x.POST_frozen
    x=v264.add_rel(x)
    return x

def desc(q,label):
    st=10000*len(q); pay=float(q.payout_if_bet.sum())
    return {
      'group':label,'R':len(q),'head4':int(q.head4.sum()),'hits':int(q.raw_hit.sum()),
      'head4_rate':100*q.head4.mean() if len(q) else np.nan,
      'hit_rate':100*q.raw_hit.mean() if len(q) else np.nan,
      'ROI':100*pay/st if st else np.nan,
      'PRE_mean':q.PRE_frozen.mean(),'POST_mean':q.POST_frozen.mean(),'ENV_mean':q.ENV_ENTRY_frozen.mean(),
      'PRE_pass_pct':100*q.pre_pass.mean() if len(q) else np.nan,
      'POST_pass_pct':100*q.post_pass.mean() if len(q) else np.nan,
      'ENV_pass_pct':100*q.env_pass.mean() if len(q) else np.nan,
      'S_all_pass_pct':100*q.s_pass.mean() if len(q) else np.nan,
      'opponent_mass_mean':q.opponent_mass.mean(),'comp_mean':q.composite_odds.mean(),
    }

def main():
    if END>='2026-09-01': raise RuntimeError('September outcome access blocked')
    rd=market.rebuild()
    if (len(rd),int(rd.head4.sum()),int(rd.raw_hit.sum()))!=(164,70,35): raise RuntimeError('164R reproduction failed')
    art=load_artifact()
    if art.get('frozen_training_cutoff')!='2026-06-30' or art.get('jul_aug_labels_used') is not False or art.get('september_labels_used') is not False:
        raise RuntimeError('frozen artifact discipline mismatch')

    pre_model,pre_meta=frozen_pre_model()
    hf=build_v250_features_to_aug()
    codes=set(rd.race_code.astype(str).str.zfill(12))
    hf=hf[hf.race_code.isin(codes)].copy()
    if len(hf)!=164 or hf.race_code.nunique()!=164: raise RuntimeError(f'historical feature coverage {len(hf)}/164')
    hf['PRE_frozen']=pre_model.predict_proba(hf[PRE_COLS])[:,1]
    hf['POST_frozen']=[score_post(r,art) for r in hf.to_dict('records')]

    ef=build_env_frame(hf[['date','race_code','PRE_frozen','POST_frozen']].copy())
    ef=ef[ef.race_code.isin(codes)].copy()
    if len(ef)!=164 or ef.race_code.nunique()!=164: raise RuntimeError(f'ENV historical coverage {len(ef)}/164')
    ef['ENV_ENTRY_frozen']=[score_env_entry(r,art) for r in ef.to_dict('records')]
    sc=hf[['date','race_code','PRE_frozen','POST_frozen']].merge(
      ef[['race_code','ENV_ENTRY_frozen']],on='race_code',validate='one_to_one')
    rd['race_code']=rd.race_code.astype(str).str.zfill(12)
    rd=rd.merge(sc,on=['date','race_code'],validate='one_to_one')
    rd['pre_pass']=rd.PRE_frozen.ge(PRE_CUT)
    rd['post_pass']=rd.POST_frozen.ge(POST_CUT)
    rd['env_pass']=rd.ENV_ENTRY_frozen.ge(ENV_CUT)
    rd['s_pass']=rd.pre_pass & rd.post_pass & rd.env_pass
    rd['period']=np.where(rd.month.le('2026-06'),'Apr-Jun','Jul-Aug')
    rd.to_csv(OUT/'race_detail.csv',index=False)

    rows=[]
    for per,q in [('Apr-Jun',rd[rd.period.eq('Apr-Jun')]),('Jul-Aug',rd[rd.period.eq('Jul-Aug')])]:
        rows += [desc(q,per+' ALL'),desc(q[q.composite_odds.lt(7)],per+' comp<7'),desc(q[q.composite_odds.ge(7)],per+' comp>=7')]
        rows += [desc(q[q.s_pass],per+' S-pass ALL'),desc(q[q.s_pass & q.composite_odds.ge(7)],per+' S-pass comp>=7')]
    for mo in sorted(rd.month.unique()):
        q=rd[rd.month.eq(mo)]
        rows += [desc(q,mo+' ALL'),desc(q[q.composite_odds.ge(7)],mo+' comp>=7'),desc(q[q.s_pass & q.composite_odds.ge(7)],mo+' S-pass comp>=7')]
    sm=pd.DataFrame(rows); sm.to_csv(OUT/'score_overlay_summary.csv',index=False)

    # Fixed production thresholds only: do not tune. Show exact funnel and reasons for rejection.
    funnel=[]
    for per,q in [('Apr-Jun',rd[rd.period.eq('Apr-Jun')]),('Jul',rd[rd.month.eq('2026-07')]),('Aug',rd[rd.month.eq('2026-08')]),('Jul-Aug',rd[rd.period.eq('Jul-Aug')])]:
        hi=q[q.composite_odds.ge(7)]
        funnel.append({
          'period':per,'high_comp_R':len(hi),'high_comp_hits':int(hi.raw_hit.sum()),'high_comp_head4':int(hi.head4.sum()),
          'PRE_pass':int(hi.pre_pass.sum()),'POST_pass':int(hi.post_pass.sum()),'ENV_pass':int(hi.env_pass.sum()),'S_all_pass':int(hi.s_pass.sum()),
          'S_all_head4':int(hi.loc[hi.s_pass,'head4'].sum()),'S_all_hits':int(hi.loc[hi.s_pass,'raw_hit'].sum()),
          'fail_PRE':int((~hi.pre_pass).sum()),'fail_POST':int((hi.pre_pass & ~hi.post_pass).sum()),
          'fail_ENV_after_PRE_POST':int((hi.pre_pass & hi.post_pass & ~hi.env_pass).sum())
        })
    pd.DataFrame(funnel).to_csv(OUT/'high_comp_s_funnel.csv',index=False)

    meta={
      'scope':'164R research candidate overlay; NOT production candidate population',
      'frozen_cuts':{'PRE':PRE_CUT,'POST':POST_CUT,'ENV_ENTRY':ENV_CUT,'COMPOSITE':7.0},
      'pre_meta':pre_meta,'artifact_cutoff':'2026-06-30',
      'threshold_retuning':False,'formal_prospective_roi':'NOT_COMPUTABLE',
      'closing_odds':'retrospective diagnostic only','v96_used':False,'september_2026':'UNREAD','production_changed':False
    }
    (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('HEAD4_RESEARCH_CANDIDATE_PRODUCTION_S_OVERLAY_OK')
    print(sm[sm.group.isin(['Apr-Jun comp>=7','Jul-Aug comp>=7','2026-07 comp>=7','2026-08 comp>=7','Apr-Jun S-pass comp>=7','Jul-Aug S-pass comp>=7'])].to_string(index=False))
    print('\nHIGH COMP S FUNNEL')
    print(pd.DataFrame(funnel).to_string(index=False))
    print('FORMAL_PROSPECTIVE_ROI NOT_COMPUTABLE')
    print('9月_UNREAD')
    print('本番変更なし')

if __name__=='__main__': main()
