"""v55: 4-corner PRE-RACE structure model after v54 direct-gap rejection.

No-leak protocol:
- Candidate source: v46 candidate rows; target/result column discarded.
- FIT 2026-06-01..06-30: compare a small predefined family of structure formulas, choose by 4-makuri Wilson lower bound.
- TUNE 2026-07-01..07-15: choose only score threshold by 4-makuri Wilson lower bound.
- Validation 2026-07-16..08-02 and Test 2026-08-03..09-02 are untouched until formula/threshold are fixed.
- Payout NEVER selects formula/threshold; it is read only for frozen-ticket ROI reporting.
- Historical/entry structure uses race card + waku10 only. Current frame-corrected direct data is a small optional term in one predefined BLEND formula.
- Actual entry/course and result-derived course are never used.
"""
import csv, math
from collections import defaultdict

from backtest import rows, race_features, score4, clamp, pct_motor, norm_st_edge
from analyze_v23_20260902_daypreview import by_code
from backtest_v51_lane_corrected_tickets import ff, ii, normkim, learn_st_frame_bias, corrected_direct
from backtest_v52_scenario_tickets import route_match, ranked_tickets as v52_ranked
from backtest_v53_pair_and_0902_flow import learn_fit_priors

MODEL='4カドまくり'
D0='2026-06-01'; FIT1='2026-06-30'; TUNE1='2026-07-15'; VA1='2026-08-02'; TE1='2026-09-02'
FORMULAS=['CORE','CORE_HIST','START_WALL','ROBUST','MOTOR_EDGE','BLEND_DIRECT']
TOP_FRACS=[.20,.30,.40]
TUNE_FRACS=[.20,.30,.40,.50,.60]
POINTS=[4,6,8,20]
VENUE={1:'桐生',2:'戸田',3:'江戸川',4:'平和島',5:'多摩川',6:'浜名湖',7:'蒲郡',8:'常滑',9:'津',10:'三国',11:'びわこ',12:'住之江',13:'尼崎',14:'鳴門',15:'丸亀',16:'児島',17:'宮島',18:'徳山',19:'下関',20:'若松',21:'芦屋',22:'福岡',23:'唐津',24:'大村'}

def wilson(k,n,z=1.281551565545):
    if not n:return 0.0
    p=k/n;zz=z*z;den=1+zz/n
    return (p+zz/(2*n)-z*math.sqrt((p*(1-p)+zz/(4*n))/n))/den

def period(d):
    if d<=FIT1:return 'fit'
    if d<=TUNE1:return 'tune'
    if d<=VA1:return 'validation'
    return 'test'

def dv(d,k,default=.5):
    v=d.get(k,default);return default if v is None else v

def ov(os,b,k):
    v=os.get(b,{}).get(k,.5);return .5 if v is None else v

def pre_features(x,hpct):
    a,b,c,d=x[1],x[2],x[3],x[4]
    prest=.60*norm_st_edge(c['waku_st'],d['waku_st'])+.40*norm_st_edge(c['nst'],d['nst'])
    attack=clamp(.55*d['past_win']/.25+.45*(6-d['waku_sr'])/5)
    wall=.60*clamp((5.5-c['waku_wr'])/4.5)+.40*norm_st_edge(c['waku_st'],d['waku_st'])
    motor4=.70*pct_motor(d['motor2'])+.30*pct_motor(d['motor3'])
    motor3=.70*pct_motor(c['motor2'])+.30*pct_motor(c['motor3'])
    motor2=.70*pct_motor(b['motor2'])+.30*pct_motor(b['motor3'])
    motor_edge=clamp(.5+.5*(motor4-(.65*motor3+.35*motor2)))
    meet=.5 if d['meet_st'] is None else clamp((.22-d['meet_st'])/.12)
    inside=clamp((7.5-a['waku_wr'])/6.0)
    quality=clamp((d['wr']-3.5)/4.0);local=clamp((d['local']-3)/5)
    start_order=clamp((6-d['waku_sr'])/5)
    return {'precore':score4(x)/100,'pre_st':prest,'pre_attack':attack,'pre_wall':wall,
            'motor4':motor4,'motor_edge':motor_edge,'meet':meet,'inside':inside,
            'quality':quality,'local4':local,'start_order4':start_order,'history_pct':hpct,
            'waku_st_gap_43':c['waku_st']-d['waku_st'],'nst_gap_43':c['nst']-d['nst'],
            'waku_wr3':c['waku_wr'],'waku_sr4':d['waku_sr'],'past_win4':d['past_win']}

def direct_small(ex,st,os):
    # v54 showed current ST gap alone is unstable; keep only a modest absolute 4 performance term.
    e4=dv(ex,4);s4=dv(st,4)
    return .30*e4+.28*s4+.25*ov(os,4,'straight')+.17*ov(os,4,'avg')

def formula(name,f):
    if name=='CORE':return f['precore']
    if name=='CORE_HIST':return .88*f['precore']+.12*f['history_pct']
    if name=='START_WALL':return .30*f['pre_st']+.25*f['pre_attack']+.20*f['pre_wall']+.15*f['motor4']+.10*f['history_pct']
    if name=='ROBUST':return .25*f['pre_st']+.20*f['pre_attack']+.18*f['pre_wall']+.15*f['motor4']+.10*f['meet']+.07*f['inside']+.05*f['history_pct']
    if name=='MOTOR_EDGE':return .25*f['pre_st']+.20*f['pre_attack']+.18*f['pre_wall']+.15*f['motor4']+.12*f['motor_edge']+.10*f['history_pct']
    return .78*(.25*f['pre_st']+.20*f['pre_attack']+.18*f['pre_wall']+.15*f['motor4']+.10*f['meet']+.07*f['inside']+.05*f['history_pct'])+.22*f['direct_small']

def load_source():
    with open('analysis_v46_history_softscore.csv',encoding='utf-8-sig') as f:
        return [{k:v for k,v in r.items() if k!='target'} for r in csv.DictReader(f)
                if r.get('model')==MODEL and D0<=r.get('date','')<=TE1]

def freeze():
    src=load_source();stbias=learn_st_frame_bias();pri,_=learn_fit_priors();rolepri={m:{'sec':pri[m]['sec'],'third':pri[m]['third']} for m in pri}
    cache={};out=[]
    for r in src:
        d=r['date'];ymd=d.replace('-','/');code=r['race_code']
        if d not in cache:
            cache[d]=(by_code(f'data/programs/race_cards/{ymd}.csv'),by_code(f'data/programs/waku10/{ymd}.csv'),
                      by_code(f'data/previews/tkz/{ymd}.csv'),by_code(f'data/previews/stt/{ymd}.csv'),
                      by_code(f'data/previews/original_exhibition/{ymd}.csv'))
        cards,w10,tkz,stt,orig=cache[d];card=cards.get(code,{})
        if not card:continue
        x=race_features(card,w10.get(code,{}));hp=ff(r.get('history_pct'),.5) or .5;f=pre_features(x,hp)
        ex,st,os=corrected_direct(code,tkz,stt,orig,stbias);f['direct_small']=direct_small(ex,st,os)
        ranked=v52_ranked(MODEL,x,ex,st,os,rolepri)
        z={'date':d,'race_code':code,**f}
        for name in FORMULAS:z[f'score_{name}']=100*formula(name,f)
        for p in POINTS:z[f'tickets_{p}']=';'.join(ranked[:p])
        out.append(z)
    return out

def settle(frozen):
    byday=defaultdict(list)
    for z in frozen:byday[z['date']].append(z)
    out=[]
    for d,arr in sorted(byday.items()):
        ymd=d.replace('-','/');res={r['レースコード']:r for r in rows(f'data/results/realtime/{ymd}.csv')};pay={r['レースコード']:r for r in rows(f'data/results/payouts/{ymd}.csv')}
        for z in arr:
            rr=res.get(z['race_code'],{});pr=pay.get(z['race_code'],{});win=ii(rr.get('1着_艇番'));kim=normkim(rr.get('決まり手'))
            combo=(pr.get('3連単_組番') or '').strip();payout=ii(pr.get('3連単_払戻金'))
            q=dict(z);q.update({'period':period(d),'winner':win,'kimarite':kim,'head_hit':int(win==4),'method_hit':int(route_match(MODEL,win,kim)),'actual_combo':combo,'payout':payout})
            for p in POINTS:
                ts=q[f'tickets_{p}'].split(';') if q[f'tickets_{p}'] else []
                q[f'invest_{p}']=len(ts)*100;q[f'hit_{p}']=int(combo in ts);q[f'return_{p}']=payout if combo in ts else 0
            out.append(q)
    return out

def top_rows(rs,key,frac):
    a=sorted(rs,key=lambda z:z[key],reverse=True);return a[:max(1,int(math.ceil(len(a)*frac)))]

def basic(rs):
    n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs)
    return n,100*hh/n if n else 0,100*mh/n if n else 0,wilson(mh,n)

def choose_formula(out):
    fit=[z for z in out if z['period']=='fit'];table=[];best=None
    for name in FORMULAS:
        vals=[]
        for fr in TOP_FRACS:
            rs=top_rows(fit,f'score_{name}',fr);n,hr,mr,wl=basic(rs);vals.append((fr,n,hr,mr,wl))
        avgwl=sum(v[4] for v in vals)/3;avgmr=sum(v[3] for v in vals)/3;table.append((name,avgwl,avgmr,vals))
        key=(avgwl,avgmr)
        if best is None or key>best[0]:best=(key,name)
    return best[1],table

def choose_threshold(out,name):
    tune=[z for z in out if z['period']=='tune'];table=[];best=None
    for fr in TUNE_FRACS:
        rs=top_rows(tune,f'score_{name}',fr);n,hr,mr,wl=basic(rs)
        if n<8:continue
        th=min(z[f'score_{name}'] for z in rs);table.append((fr,th,n,hr,mr,wl));key=(wl,mr,hr,n)
        if best is None or key>best[0]:best=(key,fr,th)
    return best[1],best[2],table

def ticket_stat(rs,p):
    n=len(rs);hh=sum(z['head_hit'] for z in rs);mh=sum(z['method_hit'] for z in rs);bh=sum(z[f'hit_{p}'] for z in rs)
    inv=sum(z[f'invest_{p}'] for z in rs);ret=sum(z[f'return_{p}'] for z in rs)
    return n,100*hh/n if n else 0,100*mh/n if n else 0,100*bh/n if n else 0,inv,ret,100*ret/inv if inv else 0

def feature_diag(out):
    feats=['precore','pre_st','pre_attack','pre_wall','motor4','motor_edge','meet','inside','quality','local4','start_order4','history_pct','direct_small','waku_st_gap_43','nst_gap_43','waku_wr3','waku_sr4','past_win4']
    ans=[]
    for ft in feats:
        row=[ft];dirs=[];strength=[]
        for per in ['fit','tune']:
            rs=[z for z in out if z['period']==per];hit=[z[ft] for z in rs if z['method_hit']];miss=[z[ft] for z in rs if not z['method_hit']]
            ah=sum(hit)/len(hit) if hit else 0;am=sum(miss)/len(miss) if miss else 0;diff=ah-am
            row += [ah,am,diff];dirs.append(1 if diff>0 else -1 if diff<0 else 0);strength.append(abs(diff))
        stable=(dirs[0]==dirs[1] and dirs[0]!=0);row += [stable,min(strength) if stable else 0]
        ans.append(row)
    ans.sort(key=lambda r:r[-1],reverse=True);return ans

def fmt(code):
    v=int(code[8:10]);r=int(code[10:12]);return f'{VENUE.get(v,v)}{r}R'

def write_csv(path,rs):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        fs=sorted(set().union(*(r.keys() for r in rs)));w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    frozen=freeze();out=settle(frozen);chosen,ftable=choose_formula(out);frac,th,ttable=choose_threshold(out,chosen)
    for z in out:
        z['v55_formula']=chosen;z['v55_score']=z[f'score_{chosen}'];z['v55_threshold']=th;z['v55_selected']=int(z['v55_score']>=th)
    write_csv('analysis_v55_4corner_structure.csv',out);diag=feature_diag(out)
    L=['# v55 4角まくり・事前構造モデル','',
       'v54で直前ST差中心の仮説が崩れたため、4コース実績・枠別/通常ST・スタート順・過去1着率・モーター・3号艇の壁実績を主軸に再設計。',
       '式選択は6/1-6/30、閾値選択は7/1-7/15のみ。払戻は式/閾値選択に不使用。','',
       '## FIT 式比較','|式|平均4まくり率|平均Wilson下限|20%|30%|40%|','|---|---:|---:|---|---|---|']
    for name,awl,amr,vals in ftable:
        mark=' **選択**' if name==chosen else '';cells=[f'{n}R/{mr:.1f}%' for fr,n,hr,mr,wl in vals]
        L.append(f'|{name}{mark}|{amr:.1f}%|{100*awl:.1f}%|{cells[0]}|{cells[1]}|{cells[2]}|')
    L+=['',f'選択式: **{chosen}**','','## TUNE 閾値','|上位割合|閾値|R|4頭率|4まくり率|Wilson下限|','|---:|---:|---:|---:|---:|---:|']
    for fr,t,n,hr,mr,wl in ttable:
        mark=' **選択**' if abs(fr-frac)<1e-9 else '';L.append(f'|{fr*100:.0f}%{mark}|{t:.2f}|{n}|{hr:.1f}%|{mr:.1f}%|{100*wl:.1f}%|')
    L+=['',f'固定ルール: **{chosen} >= {th:.2f}**','', '## Validation / Test','|期間|点数|R|4頭率|4まくり率|3連単的中率|投資|払戻|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for per in ['validation','test']:
        rs=[z for z in out if z['period']==per and z['v55_selected']]
        for p in [4,6,8]:
            n,hr,mr,br,inv,ret,roi=ticket_stat(rs,p);L.append(f'|{per}|{p}|{n}|{hr:.1f}%|{mr:.1f}%|{br:.1f}%|{inv:,}円|{ret:,}円|{roi:.1f}%|')
    L+=['','## FIT/TUNEで方向が一致した特徴（上位）','|特徴|FIT hit|FIT nonhit|差|TUNE hit|TUNE nonhit|差|安定|','|---|---:|---:|---:|---:|---:|---:|---|']
    for r in diag[:12]:
        ft,fh,fm,fd,thh,tm,td,stable,strength=r;L.append(f'|{ft}|{fh:.3f}|{fm:.3f}|{fd:+.3f}|{thh:.3f}|{tm:.3f}|{td:+.3f}|{"○" if stable else "×"}|')
    L+=['','## 2026-09-02 再判定','|レース|v55 score|判定|pre_st|attack|wall|motor|motor edge|hist|direct補助|結果|決まり手|','|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for z in sorted([q for q in out if q['date']=='2026-09-02'],key=lambda x:x['race_code']):
        L.append(f"|{fmt(z['race_code'])}|{z['v55_score']:.1f}|{'買い' if z['v55_selected'] else '見送り'}|{z['pre_st']:.2f}|{z['pre_attack']:.2f}|{z['pre_wall']:.2f}|{z['motor4']:.2f}|{z['motor_edge']:.2f}|{z['history_pct']:.2f}|{z['direct_small']:.2f}|{z['actual_combo']}|{z['kimarite']}|")
    nine=[z for z in out if z['date']=='2026-09-02' and z['v55_selected']]
    for p in [4,6,8]:
        n,hr,mr,br,inv,ret,roi=ticket_stat(nine,p);L+=['',f'9/2 v55 {p}点: {n}R / 4頭率 {hr:.1f}% / 4まくり率 {mr:.1f}% / 的中率 {br:.1f}% / ROI {roi:.1f}%']
    with open('summary_v55_4corner_structure.md','w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
