import backtest_v9_hit20 as v9

# Replace the longshot-only EV>=1.15 ticket filter.
# Keep every 4/5-head trifecta candidate when that head score qualifies,
# then rank by probability-per-market-cost (EV) and add while composite odds stay >=5x.
def build_set_probability_coverage(r,s4,s5,dc,od,train4,train5,d):
    p4=v9.cal_prob(train4,s4); p5=v9.cal_prob(train5,s5)
    cand=[]
    for head,sc,p in [(4,s4,p4),(5,s5,p5)]:
        if sc<v9.HEAD_SCORE_MIN: continue
        for combo,o,share in v9.market_conditional(od,head):
            pc=p*share; ev=pc*o
            cand.append({'date':str(d),'race_code':r['レースコード'],'venue':r.get('レース場コード',''),'race':r.get('レース回',''),'day_cat':dc,'head':head,'combo':combo,'score':round(sc,2),'head_prob':p,'combo_prob':pc,'odds_pre':o,'ev_pre':ev})
    cand.sort(key=lambda z:(z['ev_pre'],z['combo_prob']),reverse=True)
    chosen=[]
    for z in cand:
        trial=chosen+[z]
        if v9.composite_odds(trial)>=v9.MIN_COMPOSITE:
            chosen=trial
    return chosen,p4,p5

v9.build_set=build_set_probability_coverage
v9.main()
