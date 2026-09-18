#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys,tempfile

CASES=[
 ('wall3',True,False,[4.0,8.0,20.0],[100,100,400],'WALL3_RANK3'),
 ('five6',False,True,[4.0,8.0,20.0],[400,200,0],'FIVE6_SOFT2X'),
 ('none_soft',False,False,[4.0,8.0,20.0],[200,100,0],'SOFT'),
 ('none_equal',False,False,[5.0,7.0,9.0],[100,100,100],'NONE'),
]
TICKETS=['1-2-3','1-2-4','1-3-2']
def main():
    out=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for name,wall,five,ods,exp_stakes,exp_signal in CASES:
            fin={'race_code':'202609181107','status':'PASS','tickets':TICKETS,
                 'wall3_ticket_applied':wall,'five6_ticket_applied':five,
                 'deadline_jst':'2026-09-18T13:17:00+09:00',
                 'evaluated_at_jst':'2026-09-18T13:05:00+09:00',
                 'minutes_to_deadline':12.0,
                 'result_or_payout_used':False,'chronology_guard':True}
            odds={'fetched_at_jst':'2026-09-18T13:05:00+09:00','odds':dict(zip(TICKETS,ods))}
            fp=td/f'{name}_final.json';op=td/f'{name}_odds.json';rp=td/f'{name}_result.json'
            fp.write_text(json.dumps(fin));op.write_text(json.dumps(odds))
            subprocess.check_call([sys.executable,'run_1head_v351_live_current_odds_shadow.py',
                                   '--final',str(fp),'--odds-json',str(op),'--out',str(rp)])
            z=json.loads(rp.read_text())
            assert z['stakes_yen']==exp_stakes,(name,z)
            assert z['signal']==exp_signal,(name,z)
            assert z['result_or_payout_used'] is False and z['chronology_guard'] is True
            assert z['research_only'] is True
            assert z['formal_deadline_jst']=='2026-09-18T13:17:00+09:00'
            assert z['formal_minutes_to_deadline']==12.0
            assert set(z['safety_scenarios'])=={'3.5','3.9','4.3'}
            if wall:
                for key in ('3.5','3.9','4.3'):
                    assert z['safety_scenarios'][key]['stakes_yen']==[100,100,400],(name,key,z)
            elif name in ('five6','none_soft'):
                assert z['safety_scenarios']['3.5']['soft_applied'] is True
                assert z['safety_scenarios']['3.9']['soft_applied'] is True
                assert z['safety_scenarios']['4.3']['soft_applied'] is True
            else:
                assert all(z['safety_scenarios'][key]['soft_applied'] is False for key in ('3.5','3.9','4.3'))
            out.append({'case':name,'signal':z['signal'],'stakes_yen':z['stakes_yen'],
                        'total_stake_yen':z['total_stake_yen'],'odds_ratio':z['odds_ratio_max_min'],
                        'safety_scenarios':z['safety_scenarios']})
    result={'cases':out,'SEPTEMBER_OUTCOMES_READ':False,'RESULT_OR_PAYOUT_USED':False,'AUDIT_OK':True}
    Path('/tmp/v384-current-odds-shadow-regression').mkdir(parents=True,exist_ok=True)
    Path('/tmp/v384-current-odds-shadow-regression/result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
