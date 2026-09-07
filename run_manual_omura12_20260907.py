from datetime import date,timedelta
from predict_v116_20260905_1head_live import read_csv,fit_model,pred,grade,NUM_FEATURES
from analyze_v108_1head_feasibility import feature_row,bycode,st_bias,update_st
from analyze_v162_1head_pair_direct import fit_pair,pair_order
from backtest import rows

HD=date(2026,9,7); Y='2026/09/07'; CODE='202609072412'
SRC='analysis_v108_1head_feasibility.csv'
# screenshot direct inputs; F.xx is negative ST
EX=[6.92,6.96,6.95,6.99,6.96,7.00]
ST=[-.01,-.01,.01,-.11,-.17,.01]
LAP=[36.96,38.27,37.57,38.00,37.83,37.97]
TURN=[6.37,6.37,6.27,6.27,6.57,6.43]
STRAIGHT=[7.33,7.50,7.47,7.43,7.57,7.50]

def main():
    train=[r for r in read_csv(SRC) if int(float(r.get('valid_result') or 0))==1 and r.get('date','')<HD.isoformat()]
    hm=fit_model(train)
    card=next(r for r in rows(f'data/programs/race_cards/{Y}.csv') if r.get('レースコード')==CODE)
    waku=bycode(rows(f'data/programs/waku10/{Y}.csv'))[CODE]
    sums={b:[] for b in range(1,7)}; allv=[]; d=date(2025,10,1)
    while d<HD:
        try:update_st(rows(f"data/previews/stt/{d.strftime('%Y/%m/%d')}.csv"),sums,allv)
        except Exception:pass
        d+=timedelta(days=1)
    bias=st_bias(sums,allv)
    tkz=bycode(rows(f'data/previews/tkz/{Y}.csv')).get(CODE,{})
    stt=bycode(rows(f'data/previews/stt/{Y}.csv')).get(CODE,{})
    orig=bycode(rows(f'data/previews/original_exhibition/{Y}.csv')).get(CODE,{})
    # overwrite all direct-info fields from screenshot
    for b in range(1,7):
        tkz[f'艇{b}_展示タイム']=str(EX[b-1])
        stt[f'艇{b}_コース']=str(b)
        stt[f'艇{b}_スタート展示']=str(ST[b-1])
    orig['計測項目1']='一周'; orig['計測項目2']='まわり足'; orig['計測項目3']='直線'; orig['計測項目4']=''
    for b in range(1,7):
        orig[f'艇{b}_値1']=str(LAP[b-1]); orig[f'艇{b}_値2']=str(TURN[b-1]); orig[f'艇{b}_値3']=str(STRAIGHT[b-1]); orig[f'艇{b}_値4']=''
    r=feature_row(HD.isoformat(),card,waku,{CODE:tkz},{CODE:stt},{CODE:orig},bias)
    if r is None: raise RuntimeError('feature_row returned None')
    p=pred(hm,r)
    pm,ntr=fit_pair(train); order=pair_order(r,pm,1.0)
    lines=[f'p109={p:.8f}',f'grade={grade(p)}',f'pair_train={ntr}',f'top7={";".join(order[:7])}',f'top20={";".join(order)}']
    lines += [f'{k}={r.get(k)}' for k in NUM_FEATURES]
    out='\n'.join(lines)+'\n'
    print(out,end='')
    open('manual_omura12_20260907_result.txt','w',encoding='utf-8').write(out)
if __name__=='__main__':main()
