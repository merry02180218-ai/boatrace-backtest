"""Hotfix runner for v51: missing current direct-info values are neutral (0.5), never dropped."""
import backtest_v51_lane_corrected_tickets as v

def rank_scores(vals,lower=True):
    out={b:.5 for b in vals}
    a=[(b,x) for b,x in vals.items() if x is not None]
    if len(a)<2:return out
    a=sorted(a,key=lambda z:z[1],reverse=not lower);n=len(a)
    out.update({b:1-j/(n-1) for j,(b,_) in enumerate(a)})
    return out

v.rank_scores=rank_scores

if __name__=='__main__':
    v.main()
