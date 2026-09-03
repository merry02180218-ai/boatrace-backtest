import validate_v69_venue_lane_correction as v

_orig=v.corrected_direct

def corrected_direct_safe(code,tkz,stt,orig,stbias,learned=None,k=None):
    ex,st,os=_orig(code,tkz,stt,orig,stbias,learned,k)
    for b in range(1,7):
        ex.setdefault(b,.5)
        st.setdefault(b,.5)
        os.setdefault(b,{'lap':.5,'turn':.5,'straight':.5,'avg':.5})
        for key in ('lap','turn','straight','avg'):
            os[b].setdefault(key,.5)
    return ex,st,os

v.corrected_direct=corrected_direct_safe

if __name__=='__main__':
    v.main()
