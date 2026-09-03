"""v54: relative 4-corner attack model.

No-leak boundaries
- Candidate source: v46 pre-race rows; target/result is discarded.
- 2026-06-01..06-30 (FIT): choose one predefined relative-attack formula.
- 2026-07-01..07-15 (TUNE): choose only the fixed score threshold.
- 2026-07-16..08-02: validation.
- 2026-08-03..09-02: test.
- Formula/threshold selection NEVER uses payout. Payout is used only after tickets are frozen for ROI reporting.
- Current exhibition/ST/original exhibition uses existing frame-corrected direct data.
- Actual entry/course and STT course/entry columns are never used.
"""
import csv, math
from collections import defaultdict
from datetime import date

from backtest import rows, race_features
from analyze_v23_20260902_daypreview import by_code, venue_map
from backtest_v51_lane_corrected_tickets import ff, ii, normkim, tilt_band, learn_st_frame_bias, corrected_direct
from backtest_v52_scenario_tickets import TILT_BONUS, route_match, preview_comp, ranked_tickets as v52_ranked
from backtest_v53_pair_and_0902_flow import learn_fit_priors

MODEL='4カドまくり'; HEAD=4
D0='2026-06-01'; FIT1='2026-06-30'; TUNE0='2026-07-01'; TUNE1='2026-07-15'
VA0='2026-07-16'; VA1='2026-08-02'; TE0='2026-08-03'; TE1='2026-09-02'
POINTS=[4,6,8,20]
FORMULAS=['ABS','REL3','REL23','BREAK','OPPORTUNITY','HYBRID']
TOP_FRACS=[.20,.30,.40]
TUNE_FRACS=[.20,.30,.40,.50,.60]
VENUE={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}

def clamp(x): return max(0.0,min(1.0,x))

def wilson(k,n,z=1.281551565545):
    if not n:return 0.0
    p=k/n;zz=z*z;den=1+zz/n
    center=p+zz/(2*n)
    adj=z*math.sqrt((p*(1-p)+zz/(4*n))/n)
    return (center-adj)/den

def direct_features(ex,st,os):
    attack4=.30*ex[4]+.34*st[4]+.23*os[4]['straight']+.13*os[4]['avg']
    wall3=.22*ex[3]+.38*st[3]+.23*os[3]['straight']+.17*os[3]['turn']
    resist2=.18*ex[2]+.30*st[2]+.18*os[2]['straight']+.34*os[2]['turn']
    guard1=.15*ex[1]+.22*st[1]+.13*os[1]['straight']+.30*os[1]['turn']+.20*os[1]['avg']
    inner23=.65*wall3+.35*resist2
    inner231=.55*wall3+.30*resist2+.15*guard1
    gap43=clamp(.5+.5*(attack4-wall3))
    gap423=clamp(.5+.5*(attack4-inner23))
    stbreak=clamp(.5+.5*(st[4]-(.70*st[3]+.30*st[2])))
    stretchbreak=clamp(.5+.5*(os[4]['straight']-os[3]['straight']))
    wallweak=1-inner23
    innerweak=1-inner231
    return {'attack4':attack4,'wall3':wall3,'resist2':resist2,'guard1':guard1,
            'gap43':gap43,'gap423':gap423,'stbreak':stbreak,'stretchbreak':stretchbreak,
            'wallweak':wallweak,'innerweak':innerweak,
            'st_gap_43':st[4]-st[3],'straight_gap_43':os[4]['straight']-os[3]['straight']}

def comp(name,f):
    if name=='ABS': return f['attack4']
    if name=='REL3': return .55*f['attack4']+.45*f['gap43']
    if name=='REL23': return .50*f['attack4']+.50*f['gap423']
    if name=='BREAK': return .38*f['attack4']+.32*f['stbreak']+.20*f['stretchbreak']+.10*f['wallweak']
    if name=='OPPORTUNITY': return .48*f['attack4']+.30*f['gap423']+.22*f['innerweak']
    return .40*f['attack4']+.25*f['gap423']+.20*f['stbreak']+.15*f['stretchbreak']

def load_source():
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        out=[]
        for r in csv.DictReader(f):
            if r.get('model')!=MODEL:continue
            d=r.get('date','')
            if D0<=d<=TE1:
                out.append({k:v for k,v in r.items() if k!='target'})
        return out

def build_direct(stbias,pri):
    src=load_source();vidx=venue_map();cache={};out=[]
    rolepri={m:{'sec':pri[m]['sec'],'third':pri[m]['third']} for m in pri}
    for r in src:
        d=r['date'];ymd=d.replace('-','/');code=r['race_code'];venue=code[8:10]
        if d not in cache:
            cache[d]=(by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),
                      by_code(f'data/previews/original_exhibition/{ymd}.csv'),by_code(f'data/programs/race_cards/{ymd}.csv'),
                      by_code(f'data/programs/waku10/{ymd}.csv'))
        tkz,stt,orig,cards,w10=cache[d];card=cards.get(code,{})
        if not card:continue
        ex,st,os=corrected_direct(code,tkz,stt,orig,stbias);x=race_features(card,w10.get(code,{}));tr=tkz.get(code,{})
        hist=ff(r.get('history_adjust'),0) or 0;tilt=ff(tr.get('艇4_チルト'),0) or 0;tb=TILT_BONUS[MODEL][tilt_band(tilt)]
        oldcomp=preview_comp(MODEL,venue,ex,st,os,vidx);f=direct_features(ex,st,os)
        ranked=v52_ranked(MODEL,x,ex,st,os,rolepri)
        z={'date':d,'race_code':code,'history_adjust':hist,'history_pct':ff(r.get('history_pct'),.5),
           'tilt':tilt,'old_comp':oldcomp,'old_score':100*oldcomp+hist+tb,**f}
        for name in FORMULAS:z[f'score_{name}']=100*comp(name,f)+hist+tb
        for p in POINTS:z[f'tickets_{p}']=';'.join(ranked[:p])
        out.append(z)
    return out

def settle(direct):
    byday=defaultdict(list)
    for z in direct:byday[z['date']].append(z)
    out=[]
    for d,arr in sorted(byday.items()):
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in arr:
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
            combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
            q=dict(z);q.update({'winner':win,'kimarite':kim,'head_hit':int(win==4),'method_hit':int(route_match(MODEL,win,kim)),
                               'actual_combo':combo,'payout':payout})
            for p in POINTS:
                ts=q[f'tickets_{p}'].split(';') if q[f'tickets_{p}'] else []
                q[f'invest_{p}']=len(ts)*100;q[f'hit_{p}']=int(combo in ts);q[f'return_{p}']=payout if combo in ts else 0
            out.append(q)
    return out

def period(d):
    if d<=FIT1:return 'fit'
    if d<=TUNE1:return 'tune'
    if d<=VA1:return 'validation'
    return 'test'

def top_rows(rs,key,frac):
    a=sorted(rs,key=lambda z:z[key],reverse=True);n=max(1,int(math.ceil(len(a)*frac)));return a[:n]

def basic(rs):
    n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs)
    return n,hh,mh,(100*hh/n if n else 0),(100*mh/n if n else 0),wilson(mh,n)

def choose_formula(out):
    fit=[z for z in out if period(z['date'])=='fit'];table=[];best=None
    for name in FORMULAS:
        vals=[]
        for frac in TOP_FRACS:
            rs=top_rows(fit,f'score_{name}',frac);n,hh,mh,hr,mr,wl=basic(rs);vals.append((frac,n,hr,mr,wl))
        avg=sum(v[4] for v in vals)/len(vals)
        avg_m=sum(v[3] for v in vals)/len(vals)
        table.append((name,avg,avg_m,vals))
        key=(avg,avg_m)
        if best is None or key>best[0]:best=(key,name)
    return best[1],table

def choose_threshold(out,name):
    tune=[z for z in out if period(z['date'])=='tune'];best=None;table=[]
    for frac in TUNE_FRACS:
        rs=top_rows(tune,f'score_{name}',frac);n,hh,mh,hr,mr,wl=basic(rs)
        if n<8:continue
        th=min(z[f'score_{name}'] for z in rs)
        table.append((frac,th,n,hr,mr,wl))
        key=(wl,mr,hr,n)
        if best is None or key>best[0]:best=(key,frac,th)
    if best is None:
        rs=top_rows(tune,f'score_{name}',.5);th=min(z[f'score_{name}'] for z in rs);return .5,th,table
    return best[1],best[2],table

def ticket_stat(rs,p):
    n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs);bh=sum(z[f'hit_{p}'] for z in rs)
    inv=sum(z[f'invest_{p}'] for z in rs);ret=sum(z[f'return_{p}'] for z in rs)
    return n,(100*hh/n if n else 0),(100*mh/n if n else 0),(100*bh/n if n else 0),inv,ret,(100*ret/inv if inv else 0)

def fmt(code):
    v=int(code[8:10]);r=int(code[10:12]);return f'{VENUE.get(v,v)}{r}R'

def write_csv(path,rs):
    if not rs:return
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        fs=sorted(set().union(*(r.keys() for r in rs)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    stbias=learn_st_frame_bias();pri,_=learn_fit_priors();direct=build_direct(stbias,pri)
    # Results are loaded only after every direct score/ticket is frozen.
    out=settle(direct)
    chosen,ftable=choose_formula(out);frac,threshold,ttable=choose_threshold(out,chosen)
    for z in out:
        z['period']=period(z['date']);z['v54_formula']=chosen;z['v54_threshold']=threshold;z['v54_score']=z[f'score_{chosen}'];z['v54_selected']=int(z['v54_score']>=threshold)
    write_csv('analysis_v54_relative_4corner.csv',out)

    L=['# v54 4角まくり相対攻撃モデル','',
       '4号艇の絶対展示だけでなく、3号艇の壁・2号艇の抵抗・1号艇の内抵抗との相対差を評価。',
       '式は6/1-6/30だけで選択、閾値は7/1-7/15だけで選択。払戻は選択基準に不使用。7/16以降は完全固定。','',
       '## FIT: 相対式比較（上位20/30/40%の4まくり成立率を安定性込みで比較）',
       '|式|平均4まくり率|平均Wilson下限|20%|30%|40%|','|---|---:|---:|---|---|---|']
    for name,avg,avgm,vals in ftable:
        cells=[]
        for fr,n,hr,mr,wl in vals:cells.append(f'{n}R / {mr:.1f}%')
        mark=' **選択**' if name==chosen else ''
        L.append(f'|{name}{mark}|{avgm:.1f}%|{100*avg:.1f}%|{cells[0]}|{cells[1]}|{cells[2]}|')
    L+=['',f'選択式: **{chosen}**','',
        '## TUNE: 閾値選択（4まくり成立率、最低8R）','|上位割合|固定score閾値|R|4頭率|4まくり率|Wilson下限|','|---:|---:|---:|---:|---:|---:|']
    for fr,th,n,hr,mr,wl in ttable:
        mark=' **選択**' if abs(fr-frac)<1e-9 else ''
        L.append(f'|{fr*100:.0f}%{mark}|{th:.2f}|{n}|{hr:.1f}%|{mr:.1f}%|{100*wl:.1f}%|')
    L+=['',f'固定ルール: **{chosen} score >= {threshold:.2f}**（TUNE上位{frac*100:.0f}%相当）','',
        '## Validation / Test 比較','|期間|ルール|点数|R|4頭率|4まくり率|3連単的中率|投資|払戻|ROI|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for per in ['validation','test']:
        base=[z for z in out if z['period']==per]
        rules=[('v53 A',lambda z:z['old_score']>=55),('v53 S',lambda z:z['old_score']>=67),('v54',lambda z:z['v54_selected'])]
        for rn,fn in rules:
            rs=[z for z in base if fn(z)]
            for p in [4,6,8]:
                n,hr,mr,br,inv,ret,roi=ticket_stat(rs,p);L.append(f'|{per}|{rn}|{p}|{n}|{hr:.1f}%|{mr:.1f}%|{br:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## 2026-09-02 全4角候補の再判定','|レース|旧score|v54 score|v54選択|4-3 ST差|4-3直線差|3壁|2抵抗|結果|決まり手|4点買い目|','|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|']
    for z in sorted([q for q in out if q['date']=='2026-09-02'],key=lambda x:x['race_code']):
        L.append(f"|{fmt(z['race_code'])}|{z['old_score']:.1f}|{z['v54_score']:.1f}|{'買い' if z['v54_selected'] else '見送り'}|{z['st_gap_43']:+.2f}|{z['straight_gap_43']:+.2f}|{z['wall3']:.2f}|{z['resist2']:.2f}|{z['actual_combo']}|{z['kimarite']}|{z['tickets_4']}|")
    nine=[z for z in out if z['date']=='2026-09-02' and z['v54_selected']]
    for p in [4,6,8]:
        n,hr,mr,br,inv,ret,roi=ticket_stat(nine,p);L+=['',f'9/2 v54 {p}点: {n}R / 4頭率 {hr:.1f}% / 4まくり率 {mr:.1f}% / 的中率 {br:.1f}% / 投資 {inv:,}円 / 払戻 {ret:,}円 / ROI {roi:.1f}%']
    with open('summary_v54_relative_4corner.md','w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
