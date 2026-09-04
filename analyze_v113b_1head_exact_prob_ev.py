"""v113b wrapper: preserve pre-June rows for role training while attaching p109 only where available."""
import analyze_v113_1head_exact_prob_ev as v


def fixed_attach(src):
    hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in v.read_csv(v.HEAD)}
    vr={(r.get('date'),r.get('race_code')):v.ii(r.get('v110_rank20')) for r in v.read_csv(v.V110)}
    out=[]
    for r0 in src:
        r=dict(r0);key=(r.get('date'),r.get('race_code'))
        # Keep the entire historical source for strictly-prior role training.
        # p109 / v110 settlement fields are attached only to Jun-Aug evaluation rows.
        r['p109']=hp.get(key,'')
        r['_v110_rank20']=vr.get(key,0)
        out.append(r)
    return out

v.attach_head_and_v110=fixed_attach
v.main()
