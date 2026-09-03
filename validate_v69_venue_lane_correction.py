"""v69: validate venue x frame correction for exhibition/original exhibition.

No-leak partition:
- correction fit: 2026-06-01..2026-07-15 only
- shrinkage selection: 2026-07-16..2026-08-02 only
- untouched test: 2026-08-03..2026-09-02

Baseline = existing global CORR from v3.
Variant = venue x metric x frame residual correction, shrunk toward global CORR.
ST exhibition correction is unchanged from v51/v64 (frame bias only) so the test isolates
venue-specific correction of standard/original exhibition.
Results/payouts are loaded only after candidate score/grade/opponent order are frozen.
"""
import csv
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

from backtest import rows, race_features
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import ff, ii, norm_metric, rank_scores, opp_place_score
from backtest_v52_scenario_tickets import TILT_BONUS
from backtest_v51_lane_corrected_tickets import tilt_band

FIT0=date(2026,6,1); FIT1=date(2026,7,15)
VA0=date(2026,7,16); VA1=date(2026,8,2)
TE0=date(2026,8,3); TE1=date(2026,9,2)
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']
HEAD={'3まくり':3,'3まくり差し':3,'4カドまくり':4,'5頭展開':5}
A_CUT=55.0; S_CUT=67.0; HIST_P=2.0
KS=[12.0,24.0,48.0,96.0]


def by_code(path): return {r['レースコード']:r for r in rows(path)}

def history_value(r):
    p1=ff(r.get('prior1'),.5); p2=ff(r.get('prior2'),p1); has2=ii(r.get('has2'))
    if r['model']=='4カドまくり': return .4*p1+.6*p2 if has2 else p1
    if r['model']=='5頭展開': return p2 if has2 else p1
    return p1

def pct_rank_online(x, vals):
    return .5 if not vals else sum(v<=x for v in vals)/len(vals)

def load_source():
    out=[]
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r.get('model') not in MODELS: continue
            if not ('2026-06-01'<=r.get('date','')<='2026-09-02'): continue
            out.append({k:v for k,v in r.items() if k not in ('target','history_pct','history_adjust')})
    return out

def learn_st_frame_bias():
    sums=defaultdict(list); allv=[]; d=FIT0
    while d<=FIT1:
        ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/previews/stt/{ymd}.csv'):
            for b in range(1,7):
                v=ff(r.get(f'艇{b}_スタート展示'))
                if v is not None and -.30<v<1.0:
                    sums[b].append(v); allv.append(v)
        d+=timedelta(days=1)
    g=mean(allv) if allv else .15
    return {b:(mean(sums[b])-g if sums[b] else 0.0) for b in range(1,7)}

def learn_venue_lane_residuals():
    acc=defaultdict(list); d=FIT0
    while d<=FIT1:
        ymd=d.strftime('%Y/%m/%d')
        for r in rows(f'data/previews/tkz/{ymd}.csv'):
            code=r.get('レースコード',''); venue=code[8:10] if len(code)>=10 else ''
            vals={b:ff(r.get(f'艇{b}_展示タイム')) for b in range(1,7)}
            vv=[v for v in vals.values() if v is not None]
            if len(vv)>=4:
                g=mean(vv)
                for b,v in vals.items():
                    if v is not None: acc[(venue,'展示',b)].append(v-g)
        for r in rows(f'data/previews/original_exhibition/{ymd}.csv'):
            code=r.get('レースコード',''); venue=code[8:10] if len(code)>=10 else ''
            for k in range(1,5):
                label=r.get(f'計測項目{k}','')
                if not label: continue
                mk=norm_metric(label)
                if mk not in ('一周','まわり足','回り足','直線'): continue
                vals={b:ff(r.get(f'艇{b}_値{k}')) for b in range(1,7)}
                vv=[v for v in vals.values() if v is not None]
                if len(vv)>=4:
                    g=mean(vv)
                    for b,v in vals.items():
                        if v is not None: acc[(venue,mk,b)].append(v-g)
        d+=timedelta(days=1)
    out={}
    for key,a in acc.items():
        # lower time is better; correction cancels the learned lane residual.
        out[key]={'n':len(a),'raw_corr':-mean(a)}
    return out

def corr_for(learned, venue, metric, boat, k):
    base=CORR[boat].get(metric,0.0)
    z=learned.get((str(venue).zfill(2),metric,boat))
    if not z: return base
    w=z['n']/(z['n']+k)
    return w*z['raw_corr']+(1-w)*base

def corrected_direct(code,tkz,stt,orig,stbias,learned=None,k=None):
    venue=code[8:10]
    tr=tkz.get(code,{}); sr=stt.get(code,{}); orr=orig.get(code,{})
    def c(metric,b):
        return CORR[b].get(metric,0) if learned is None else corr_for(learned,venue,metric,b,k)
    exraw={}
    for b in range(1,7):
        v=ff(tr.get(f'艇{b}_展示タイム'))
        exraw[b]=(v+c('展示',b)) if v is not None else None
    ex=rank_scores(exraw,True)
    straw={}
    for b in range(1,7):
        v=ff(sr.get(f'艇{b}_スタート展示'))
        straw[b]=(v-stbias[b]) if v is not None else None
    st=rank_scores(straw,True)
    os={b:{'lap':.5,'turn':.5,'straight':.5,'avg':.5} for b in range(1,7)}
    per={b:[] for b in range(1,7)}
    if orr:
        for idx in range(1,5):
            label=orr.get(f'計測項目{idx}','')
            if not label: continue
            mk=norm_metric(label)
            vals={}
            for b in range(1,7):
                v=ff(orr.get(f'艇{b}_値{idx}'))
                vals[b]=(v+c(mk,b)) if v is not None else None
            sc=rank_scores(vals,True)
            for b in range(1,7):
                if vals.get(b) is None: continue
                per[b].append(sc[b])
                if mk=='直線': os[b]['straight']=sc[b]
                elif mk=='一周': os[b]['lap']=sc[b]
                elif mk in ('まわり足','回り足'): os[b]['turn']=sc[b]
    for b in range(1,7):
        if per[b]: os[b]['avg']=sum(per[b])/len(per[b])
    return ex,st,os

def direct_comp(m,ex,st,os):
    if m=='3まくり':
        z=os[3]; return .28*ex.get(3,.5)+.28*st.get(3,.5)+.22*z['straight']+.17*z['avg']+.05*.5
    if m=='3まくり差し':
        z=os[3]; return .17*ex.get(3,.5)+.22*st.get(3,.5)+.17*z['lap']+.27*z['turn']+.12*z['avg']+.05*.5
    if m=='4カドまくり':
        z=os[4]; return .28*ex.get(4,.5)+.30*st.get(4,.5)+.22*z['straight']+.15*z['avg']+.05*.5
    z4=os[4]; z5=os[5]
    attack4=.32*ex.get(4,.5)+.38*st.get(4,.5)+.18*z4['straight']+.12*z4['avg']
    take5=.22*ex.get(5,.5)+.17*st.get(5,.5)+.27*z5['lap']+.27*z5['turn']+.07*z5['avg']
    return .43*attack4+.52*take5+.05*.5

def freeze_variant(src, stbias, learned=None, k=None):
    byday=defaultdict(list)
    for r in src: byday[r['date']].append(r)
    histvals={m:[] for m in MODELS}; frozen_all=[]
    d=FIT0
    while d<=TE1:
        ds=str(d); ymd=d.strftime('%Y/%m/%d')
        tkz=by_code(f'data/previews/tkz/{ymd}.csv'); stt=by_code(f'data/previews/stt/{ymd}.csv'); orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
        cards=by_code(f'data/programs/race_cards/{ymd}.csv'); w10=by_code(f'data/programs/waku10/{ymd}.csv')
        cand=[]
        for r in byday.get(ds,[]):
            code=r['race_code']; m=r['model']; h=HEAD[m]; card=cards.get(code,{})
            if not card: continue
            try: x=race_features(card,w10.get(code,{}))
            except Exception: continue
            ex,st,os=corrected_direct(code,tkz,stt,orig,stbias,learned,k)
            hv=history_value(r); hp=pct_rank_online(hv,histvals[m]); hadj=HIST_P*(2*hp-1)
            comp=direct_comp(m,ex,st,os); tr=tkz.get(code,{})
            tilt=ff(tr.get(f'艇{h}_チルト'),0) or 0
            tbonus=TILT_BONUS[m][tilt_band(tilt)]
            score=100*comp+hadj+tbonus
            others=[b for b in range(1,7) if b!=h]
            ranked=sorted(others,key=lambda b:opp_place_score(x,b,ex,st,os),reverse=True)
            cand.append({'date':ds,'race_code':code,'model':m,'head':h,'score':score,
                         'grade':'S' if score>=S_CUT else ('A' if score>=A_CUT else 'B'),
                         'approved_A':int(score>=A_CUT),'approved_S':int(score>=S_CUT),
                         'ranked':ranked})
        grp=defaultdict(list)
        for z in cand: grp[(z['race_code'],z['head'])].append(z)
        frozen=[max(a,key=lambda z:z['score']) for a in grp.values()]
        # Only now load outcomes.
        res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')}
        pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in frozen:
            rr=res.get(z['race_code'],{}); pr=pay.get(z['race_code'],{})
            win=ii(rr.get('1着_艇番')); combo=(pr.get('3連単_組番') or '').strip()
            q=dict(z); q['head_hit']=int(win==z['head']); q['actual_combo']=combo
            q['sec_rank']=None; q['third_rank']=None; q['combo20_rank']=None
            try:
                a,b,c=[int(x) for x in combo.split('-')]
                if a==z['head']:
                    q['sec_rank']=z['ranked'].index(b)+1
                    q['third_rank']=z['ranked'].index(c)+1
                    seq=[f"{z['head']}-{x}-{y}" for x in z['ranked'] for y in z['ranked'] if y!=x]
                    q['combo20_rank']=seq.index(combo)+1
            except Exception: pass
            frozen_all.append(q)
        for r in byday.get(ds,[]): histvals[r['model']].append(history_value(r))
        d+=timedelta(days=1)
    return frozen_all

def metrics(rows_,lo,hi,main_only=True):
    rs=[r for r in rows_ if lo<=date.fromisoformat(r['date'])<=hi and (r['head'] in (3,5) if main_only else True)]
    A=[r for r in rs if r['approved_A']]; S=[r for r in rs if r['approved_S']]
    hh=[r for r in A if r['head_hit']]
    sh=[r for r in S if r['head_hit']]
    def rate(num,den): return num/den if den else 0
    top6=sum((r['combo20_rank'] or 99)<=6 for r in hh)
    top8=sum((r['combo20_rank'] or 99)<=8 for r in hh)
    sec2=sum((r['sec_rank'] or 99)<=2 for r in hh)
    return {'A_n':len(A),'A_head':sum(r['head_hit'] for r in A),'A_rate':rate(sum(r['head_hit'] for r in A),len(A)),
            'S_n':len(S),'S_head':sum(r['head_hit'] for r in S),'S_rate':rate(sum(r['head_hit'] for r in S),len(S)),
            'S_lift':rate(sum(r['head_hit'] for r in S),len(S))-rate(sum(r['head_hit'] for r in A),len(A)),
            'headhit_n':len(hh),'top6':rate(top6,len(hh)),'top8':rate(top8,len(hh)),'sec2':rate(sec2,len(hh))}

def quality(m):
    # head-first weighting; opponent rank is secondary.
    return .55*m['S_rate']+.25*m['A_rate']+.12*m['top6']+.08*m['sec2']

def main():
    src=load_source(); stbias=learn_st_frame_bias(); learned=learn_venue_lane_residuals()
    variants={'baseline':freeze_variant(src,stbias)}
    for k in KS: variants[f'venue_k{int(k)}']=freeze_variant(src,stbias,learned,k)
    val={name:metrics(rs,VA0,VA1) for name,rs in variants.items()}
    best=max([n for n in val if n!='baseline'],key=lambda n:quality(val[n]))
    test={name:metrics(rs,TE0,TE1) for name,rs in variants.items()}
    vb=val['baseline']; vv=val[best]; tb=test['baseline']; tt=test[best]
    adopt=(quality(vv)>quality(vb) and quality(tt)>quality(tb) and tt['A_rate']>=tb['A_rate']-.005 and
           (tt['S_rate']>=tb['S_rate']+.01 or tt['top6']>=tb['top6']+.02 or tt['sec2']>=tb['sec2']+.02))

    # write learned correction table for the selected shrinkage regardless of adoption for auditability.
    ksel=float(best.split('k')[1])
    with open('venue_lane_correction_v69.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(['venue','metric','boat','n','baseline_corr','raw_venue_corr','selected_corr','shrink_k'])
        for (venue,metric,b),z in sorted(learned.items()):
            w.writerow([venue,metric,b,z['n'],CORR[b].get(metric,0),round(z['raw_corr'],6),round(corr_for(learned,venue,metric,b,ksel),6),ksel])

    def fmt(m):
        return f"A {m['A_n']}R head {m['A_rate']*100:.1f}% / S {m['S_n']}R head {m['S_rate']*100:.1f}% / head-hit時 top6 {m['top6']*100:.1f}% / 2着相手top2 {m['sec2']*100:.1f}%"
    L=['# v69 場別×枠別 展示補正 検証','',
       f'- 補正学習: **{FIT0}〜{FIT1}**（結果不使用、展示値のレース平均との差だけ）',
       f'- 縮約強度選択: **{VA0}〜{VA1}**',f'- 完全テスト: **{TE0}〜{TE1}**',
       '- 対象: 通常展示・一周・回り足/まわり足・直線。ST展示の枠補正は従来の艇番別学習値のまま固定し、今回の差分から除外。',
       '- 場別×艇番×項目の平均残差を打ち消す補正を推定し、サンプル数に応じて従来CORRへ縮約。',
       '- 3まくり/3まくり差し重複は結果を見る前にscore上位へ統合。結果・払戻はscore/grade/相手順位固定後にのみロード。','',
       '## validation（縮約選択）','|variant|A候補|A頭率|S候補|S頭率|S-A lift|頭的中時 top6|頭的中時 2着top2|quality|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in val.items():
        L.append(f"|{name}|{m['A_n']}|{m['A_rate']*100:.1f}%|{m['S_n']}|{m['S_rate']*100:.1f}%|{m['S_lift']*100:+.1f}pt|{m['top6']*100:.1f}%|{m['sec2']*100:.1f}%|{quality(m):.4f}|")
    L+=['',f'validationで選択: **{best}**','','## untouched test','|variant|A候補|A頭率|S候補|S頭率|S-A lift|頭的中時 top6|頭的中時 2着top2|quality|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in ['baseline',best]:
        m=test[name];L.append(f"|{name}|{m['A_n']}|{m['A_rate']*100:.1f}%|{m['S_n']}|{m['S_rate']*100:.1f}%|{m['S_lift']*100:+.1f}pt|{m['top6']*100:.1f}%|{m['sec2']*100:.1f}%|{quality(m):.4f}|")
    L+=['',f'## 判定: **{"採用" if adopt else "不採用"}**',f'- baseline test: {fmt(tb)}',f'- {best} test: {fmt(tt)}',
        f"- quality: {quality(tb):.4f} → {quality(tt):.4f} ({quality(tt)-quality(tb):+.4f})",
        '- 採用条件: validation/test両方でquality改善、test A頭率の悪化0.5pt以内、かつtestでS頭率+1pt以上または相手top6/2着top2が+2pt以上。']
    open('summary_v69_venue_lane_correction.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
    open('adopt_v69.txt','w',encoding='utf-8').write(('ADOPT' if adopt else 'REJECT')+'\n'+best+'\n')

if __name__=='__main__': main()
