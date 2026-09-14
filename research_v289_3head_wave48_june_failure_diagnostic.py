from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave47_holdout_fixed as w47
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); CUT=.365448
OUTJ=Path('research_v289_3head_wave48_june_failure_diagnostic.json'); OUTM=Path('research_v289_3head_wave48_june_failure_diagnostic.md')
def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def gap(d,met,b): return num(d[f'card__艇3_{met}'])-num(d[f'card__艇{b}_{met}'])
def qstats(x):
    if len(x)==0:return {}
    ret=np.array([base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()],float)
    head=x.actual.str.startswith('3-').to_numpy(); ticket=np.array([a in t.split(';') for a,t in zip(x.actual,x.top5)])
    cond=ticket[head]
    return {'races':len(x),'head_hits':int(head.sum()),'head_rate':float(head.mean()),'ticket_hits':int(ticket.sum()),'ticket_rate':float(ticket.mean()),'top5_capture_given_head':float(cond.mean()) if len(cond) else None,'return_yen':float(ret.sum()),'roi_pct':float(ret.sum()/10000/len(x)*100),'profit_yen':float(ret.sum()-10000*len(x))}
def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BASEC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]; X=base.build_static(d); y=d.settle__actual_combo.astype(str); p=np.full(len(d),np.nan); tops=np.array(['']*len(d),object)
    def run(a,b):
        tr=np.flatnonzero(a.to_numpy()); te=np.flatnonzero(b.to_numpy()); pp,tt=w47.w36(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=pp; tops[te]=tt
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']:run(d.month<mo,d.month==mo)
    d['p3']=p; d['top5']=tops; d['actual']=y
    Z=w47.zfeat(d); tr=d.month=='2026-02'; zm=__import__('sklearn').pipeline.make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.08,class_weight='balanced')); zm.fit(Z.loc[tr],y.loc[tr].str.startswith('3-').astype(int)); d['zone']=zm.predict_proba(Z)[:,1]
    march=d[(d.month=='2026-03')&(d.p3>=CUT)]; zcut=float(march.zone.quantile(.40)); sel=d[d.month.isin(['2026-04','2026-05','2026-06'])&(d.p3>=CUT)&(d.zone>=zcut)].copy()
    metrics=['全国平均ST','全国勝率','当地勝率','モーター2連対率','モーター3連対率']
    feats=['p3','zone']
    for met in metrics:
        for b in [1,2,4]:
            k=f'{met}_3m{b}'; sel[k]=gap(sel,met,b); feats.append(k)
    monthly={}; dist={}
    for mo,g in sel.groupby('month'):
        monthly[mo]=qstats(g)
        dist[mo]={k:{'mean':float(pd.to_numeric(g[k],errors='coerce').mean()),'median':float(pd.to_numeric(g[k],errors='coerce').median())} for k in feats}
        dist[mo]['race_no_mean']=float(pd.to_numeric(g.get('race_no',g.get('race_number',pd.Series(index=g.index,dtype=float))),errors='coerce').mean()) if ('race_no' in g or 'race_number' in g) else None
        venue_col=next((c for c in ['venue_code','jcd','stadium','場コード'] if c in g),None); dist[mo]['top_venues']=g[venue_col].value_counts().head(5).to_dict() if venue_col else {}
    aprmay=pd.concat([sel[sel.month=='2026-04'],sel[sel.month=='2026-05']]); jun=sel[sel.month=='2026-06']
    drift={}
    for k in feats:
        a=pd.to_numeric(aprmay[k],errors='coerce'); b=pd.to_numeric(jun[k],errors='coerce'); pooled=np.nanstd(pd.concat([a,b]).to_numpy())
        drift[k]={'aprmay_mean':float(a.mean()),'june_mean':float(b.mean()),'standardized_shift':float((b.mean()-a.mean())/pooled) if pooled and np.isfinite(pooled) else 0.0}
    ranked=sorted(drift.items(),key=lambda kv:abs(kv[1]['standardized_shift']),reverse=True)
    am=qstats(aprmay); ju=qstats(jun)
    head_drop=ju['head_rate']-am['head_rate']; cap_drop=(ju['top5_capture_given_head'] or 0)-(am['top5_capture_given_head'] or 0)
    if head_drop<=-.08 and cap_drop>-0.08: mech='A_HEAD_SELECTION_FAILURE'
    elif cap_drop<=-.08 and head_drop>-0.08: mech='B_OPPONENT_TOP5_FAILURE'
    elif head_drop<=-.08 and cap_drop<=-.08: mech='MIXED_HEAD_AND_OPPONENT_FAILURE'
    else: mech='C_PAYOUT_ECONOMICS_OR_MIXED'
    out={'wave':'48-june-failure-diagnostic','diagnostic_only':True,'wave47_zcut':zcut,'monthly':monthly,'apr_may_combined':am,'june':ju,'head_rate_change_june_vs_aprmay':head_drop,'conditional_top5_change':cap_drop,'failure_mechanism':mech,'pre_race_distributions':dist,'largest_pre_race_shifts':[{'feature':k,**v} for k,v in ranked[:8]],'future_status':'HYPOTHESIS_FOR_FUTURE_PRISTINE_TEST_ONLY','september_outcomes_read':False}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave48 June failure diagnostic','',f"- Apr-May: {am['races']}R / head {am['head_rate']:.3%} / conditional Top5 {am['top5_capture_given_head']:.3%} / ROI {am['roi_pct']:.3f}%",f"- June: {ju['races']}R / head {ju['head_rate']:.3%} / conditional Top5 {ju['top5_capture_given_head']:.3%} / ROI {ju['roi_pct']:.3f}%",f"- June head-rate change: {head_drop:+.3%}",f"- June conditional Top5 change: {cap_drop:+.3%}",f"- mechanism: **{mech}**",'', '## Largest pre-race distribution shifts']+[f"- {k}: standardized shift {v['standardized_shift']:+.3f}" for k,v in ranked[:8]]+['','- Diagnostic only. No Wave47 retuning/adoption from Apr-Jun.','- September outcomes unread.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
