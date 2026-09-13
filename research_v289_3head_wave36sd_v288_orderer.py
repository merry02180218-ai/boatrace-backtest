from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave36sc_motor_robustness as sc
import research_v289_3head_wave31_nonlinear_gate as base
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v242_3head_target_comp3_min5_max10 as v242
import analyze_v234_3head_waku10_restored_replay as v234

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
LEG=Path('analysis_v108_1head_feasibility.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave36sd_v288_orderer.json')
MONTHS=['2026-04','2026-05','2026-06']

def parse_odds(s):
    try:z=json.loads(str(s))
    except:return None
    out={}
    if isinstance(z,dict):
        for k,v in z.items():
            try:out[str(k)]=float(v)
            except:pass
    return out if len(out)==120 else None

def wave36sc_selected(src):
    d=src.copy();ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
    feb=d.month=='2026-02';mar=d.month=='2026-03';march=sc.predict_block(d,X,y,feb,mar);mc=sc.fit_cal(march);march['cal_p3']=sc.apply_cal(march,mc);cal_cut=float(1/(1+np.exp(-(float(mc.coef_[0][0])*sc.RAW_CUT+float(mc.intercept_[0])))))
    racer_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率'])]
    motor_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['モーター2連対率','モーター3連対率'])]
    rz=[];mz=[]
    for c in racer_cols:
        z,_,_=sc.zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());rz.append(z)
    for c in motor_cols:
        z,_,_=sc.zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());mz.append(z)
    d['racer_adv']=pd.concat(rz,axis=1).mean(axis=1);d['motor_adv']=pd.concat(mz,axis=1).mean(axis=1)
    rcut=float(d.loc[feb,'racer_adv'].quantile(.5));mcut=float(d.loc[feb,'motor_adv'].quantile(.5));oos={'2026-03':march};out=[]
    for mo in MONTHS:
        q=sc.predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos.keys())[-3:];pool=pd.concat([oos[p] for p in prior],ignore_index=True);c=sc.fit_cal(pool);q['cal_p3']=sc.apply_cal(q,c);q['racer_adv']=d.loc[q.index,'racer_adv'];q['motor_adv']=d.loc[q.index,'motor_adv'];q['mod_p3']=q.cal_p3-.08*((q.racer_adv>=rcut)&(q.motor_adv<=mcut)).astype(float);out.append(q[q.mod_p3>=cal_cut].copy());oos[mo]=q
    return pd.concat(out,ignore_index=True)

def metric(g):
    if len(g)==0:return {'races':0}
    a=g.sort_values(['date','race_code']);profit=a['return_yen']-10000;c=np.cumsum(profit.to_numpy(float));pk=np.maximum.accumulate(np.r_[0.,c]);dd=float((pk[1:]-c).max()) if len(c) else 0
    hh=int(a.actual3.sum());hits=int(a.hit.sum());stake=10000*len(a);pay=float(a.return_yen.sum())
    return {'races':len(a),'ticket_hits':hits,'head_hits':hh,'head_rate':hh/len(a),'conversion':hits/hh if hh else 0,'stake_yen':stake,'payout_yen':pay,'profit_yen':pay-stake,'roi_pct':100*pay/stake,'max_drawdown_yen':dd,'skipped_v242':int(a.skipped.sum())}

def main():
    src=pd.read_csv(SRC,dtype=str).fillna('')
    if src.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
    sel=wave36sc_selected(src);sel_codes=set(sel.race_code.astype(str).str.zfill(12))
    raw=pd.read_csv(LEG,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw=raw[raw._date.notna()&(raw._date<pd.Timestamp('2026-07-01'))].copy();raw['race_code_norm']=raw.race_code.astype(str).str.zfill(12);raw_codes=set(raw.race_code_norm)
    hist=v221.build(raw,dc);hist['race_code_norm']=hist.race_code.astype(str).str.zfill(12);hist_codes=set(hist.race_code_norm)
    sm=src.copy();sm['race_code_norm']=sm.race_code.astype(str).str.zfill(12);sidx=sm.set_index('race_code_norm',drop=False)
    rec=[];cause={};missing=[]
    for code in sorted(sel_codes):
        if code not in raw_codes:cause[code]='absent_from_legacy_v108'
        elif code not in hist_codes:cause[code]='absent_after_v221_build'
    for mo in MONTHS:
        first=pd.Timestamp(mo+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=hist[hist._date<first];pair=v222.fit_pair(tr,'V221')
        targets=hist[(hist._date>=first)&(hist._date<nextm)&hist.race_code_norm.isin(sel_codes)]
        for _,r in targets.iterrows():
            code=r.race_code_norm
            if code not in sidx.index:missing.append(code);cause[code]='absent_from_wave21_source';continue
            sr=sidx.loc[code];sr=sr.iloc[-1] if isinstance(sr,pd.DataFrame) else sr
            odds=parse_odds(sr.get('closing_odds__json',''))
            if odds is None:missing.append(code);cause[code]='invalid_closing_odds';continue
            ts=v242.safe_order(r,pair)
            if ts is None:missing.append(code);cause[code]='safe_order_none';continue
            ch=v242.choose_n(ts,odds);actual=str(sr.get('settle__actual_combo',''));head=int(actual.startswith('3-'));hit=0;ret=0.;sk=1
            if ch.get('action')=='bet':
                sk=0;n=int(ch['top_n']);vals=[float(odds[x]) for x in ts[:n]];stakes=np.asarray(v234.v205.round_dutch(vals,10000),int)
                if int(stakes.sum())!=10000:raise RuntimeError('Dutch invariant')
                if actual in ts[:n]:
                    j=ts[:n].index(actual)
                    if stakes[j]>0:hit=1;ret=float(stakes[j])*vals[j]
            rec.append({'month':mo,'date':str(sr.date),'race_code':code,'actual3':head,'hit':hit,'return_yen':ret,'skipped':sk,'top_n':ch.get('top_n'),'raw_n':ch.get('raw_n'),'comp_odds':ch.get('comp_odds')})
    q=pd.DataFrame(rec);expected=len(sel);covered=len(q);covered_codes=set(q.race_code.astype(str)) if len(q) else set();missing_sel=sorted(sel_codes-covered_codes)
    for code in missing_sel:cause.setdefault(code,'not_reached_unknown')
    cc={}
    for code in missing_sel:cc[cause[code]]=cc.get(cause[code],0)+1
    out={'wave':'36S-D-v288-orderer','orderer':'exact V221 ordered-pair ranker + v242 variable TopN 5-10 + exact JPY10000 Dutch','wave36sc_expected_races':expected,'covered_races':covered,'missing_or_invalid_count':len(missing_sel),'missing_or_invalid_examples':missing_sel[:30],'missing_causes':{c:cause[c] for c in missing_sel},'missing_cause_counts':cc,'legacy_v108_rows':len(raw),'legacy_v108_unique_codes':len(raw_codes),'monthly':{mo:metric(q[q.month==mo]) for mo in MONTHS},'apr_jun':metric(q),'v288_overlap':int(q.race_code.astype(str).isin(set(pd.read_csv(BC,dtype=str).race_code.astype(str))).sum()),'september_forbidden':True}
    if out['v288_overlap']:raise RuntimeError('v288 overlap')
    out['decision']='PARITY_READY' if covered==expected and not missing_sel else 'FAIL_CLOSED_PARITY_INCOMPLETE'
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
    if out['decision']!='PARITY_READY':raise RuntimeError(out['decision'])
if __name__=='__main__':main()
