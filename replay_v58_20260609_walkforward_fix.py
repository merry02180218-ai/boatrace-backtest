import replay_v58_20260609_walkforward as m

_orig = m.opp_place_score

def safe_opp_place_score(x,b,ex,st,os):
    ex=dict(ex); st=dict(st); os={k:dict(v) for k,v in os.items()}
    for boat in range(1,7):
        ex.setdefault(boat,.5)
        st.setdefault(boat,.5)
        os.setdefault(boat,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for k in ('lap','turn','straight','avg'):
            os[boat].setdefault(k,.5)
    return _orig(x,b,ex,st,os)

m.opp_place_score=safe_opp_place_score

if __name__=='__main__':
    m.main()
