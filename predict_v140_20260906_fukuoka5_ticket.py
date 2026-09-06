from datetime import date,timedelta
import predict_v107_20260905_official_fullscan as v107
from backtest import grade_score,clamp,pct_motor

v107.HD='20260906'
JCD='22'; RNO=5
# Screenshot values frozen before deadline
EX={1:6.86,2:6.86,3:6.90,4:6.79,5:6.87,6:6.94}
ST={1:.10,2:.09,3:.16,4:-.03,5:-.03,6:.03}
LAP={1:37.62,2:37.60,3:37.55,4:37.08,5:38.11,6:38.22}
TURN={1:5.65,2:5.53,3:5.69,4:5.58,5:5.50,6:6.28}
STRAIGHT={1:7.63,2:7.60,3:7.57,4:7.57,5:7.60,6:7.66}
CORR={1:{'ex':.02,'lap':.40,'turn':.20,'straight':0},2:{'ex':.01,'lap':.30,'turn':.10,'straight':0},3:{'ex':0,'lap':.20,'turn':0,'straight':0},4:{'ex':-.01,'lap':.10,'turn':-.05,'straight':-.01},5:{'ex':-.01,'lap':.05,'turn':-.10,'straight':-.02},6:{'ex':-.02,'lap':0,'turn':-.15,'straight':-.02}}
STBIAS={1:-.0052,2:.0108,3:.0052,4:-.0025,5:-.0065,6:-.0018}

def rank(vals):
    s=sorted(vals.items(),key=lambda z:z[1]); n=len(s)
    return {b:1-i/(n-1) for i,(b,_) in enumerate(s)}

def main():
    names=v107.racer_names(); race=v107.parse_race(JCD,RNO,names)
    # strictly prior-date same-frame history through Sep5
    lookup={}
    d=date(2026,9,5)
    for _ in range(45):
        _,items=v107.fetch_hist_day(d)
        for rid,b,z in items: lookup[(rid,b)]=z
        d-=timedelta(days=1)
    v107.attach_waku([race],lookup)
    x=race['lanes']
    ex=rank({b:EX[b]+CORR[b]['ex'] for b in EX})
    st=rank({b:ST[b]-STBIAS[b] for b in ST})
    lap=rank({b:LAP[b]+CORR[b]['lap'] for b in LAP})
    turn=rank({b:TURN[b]+CORR[b]['turn'] for b in TURN})
    straight=rank({b:STRAIGHT[b]+CORR[b]['straight'] for b in STRAIGHT})
    avg={b:(lap[b]+turn[b]+straight[b])/3 for b in range(1,7)}
    scores={}
    for b in [1,2,3,4,6]:
        z=x[b]
        motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
        q=clamp((z['wr']-3.0)/5.0); loc=clamp((z['local']-2.5)/5.5); ww=clamp(z['waku_wr']/8.0)
        nst=clamp((.24-z['nst'])/.14)
        direct=.35*ex[b]+.20*st[b]+.25*turn[b]+.20*avg[b]
        total=.16*grade_score(z['grade'])+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct
        scores[b]=(total,direct,z)
    ranked=sorted(scores,key=lambda b:scores[b][0],reverse=True)
    sec=ranked[:2]; third=ranked[:4]
    tickets=[f'5-{a}-{b}' for a in sec for b in third if b!=a]
    print('RANK',ranked)
    for b in ranked:
        t,d,z=scores[b]
        print(b,z['name'],z['grade'],f'total={t:.6f}',f'direct={d:.6f}',f'wr={z["wr"]}',f'local={z["local"]}',f'motor2={z["motor2"]}',f'motor3={z["motor3"]}',f'waku_wr={z["waku_wr"]}',f'nst={z["nst"]}')
    print('TICKETS',tickets)

if __name__=='__main__':main()
