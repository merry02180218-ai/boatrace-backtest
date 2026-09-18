#!/usr/bin/env python3
"""Verify BOATCAST od3 parser against captured live structure and current endpoint."""
from run_4head_120r_lastminute_fast import parse_od3,_get_fast,BOATCAST

FIXTURE="""data=
1
桑島　　和宏	45.9	76.0	111.8	84.6	64.4	29.4	48.5	70.5	43.9	25.6	11.5	11.8	104.0	79.0	14.6	16.6	80.1	76.0	27.0	46.6	0	0	0	0	0	
中曽　　瑠華	76.9	91.2	97.1	152.0	120.9	102.2	191.2	228.0	126.1	118.5	219.5	137.8	144.5	296.4	296.4	257.7	312.0	348.7	219.5	395.2	0	0	0	0	0	
宮村　　勇哉	35.4	52.4	53.8	97.1	197.6	79.0	141.1	185.2	100.4	105.8	228.0	160.2	111.8	312.0	237.1	741.0	219.5	219.5	257.7	592.8	0	0	0	0	0	
上條　　嘉嗣	48.5	54.8	39.7	35.2	148.2	107.7	179.6	88.4	89.8	169.3	156.0	126.1	64.4	160.2	116.2	68.9	44.2	116.2	126.1	68.9	0	0	0	0	0	
中村　かなえ	100.4	164.6	118.5	134.7	219.5	296.4	164.6	538.9	219.5	348.7	282.2	423.4	89.8	204.4	237.1	116.2	228.0	592.8	395.2	148.2	0	0	0	0	0	
松尾　　　充	257.7	228.0	174.3	846.8	456.0	423.4	247.0	370.5	456.0	494.0	197.6	741.0	191.2	179.6	269.4	169.3	395.2	658.6	456.0	174.3	0	0	0	0	0	
"""

def assert_map(od):
    assert len(od)==120
    assert od['1-2-3']==45.9
    assert od['1-2-4']==76.0
    assert od['1-2-5']==111.8
    assert od['1-2-6']==84.6
    assert od['4-1-2']==48.5
    assert od['4-1-3']==54.8
    assert od['4-1-5']==39.7
    assert od['4-1-6']==35.2
    assert od['6-5-4']==174.3

def main():
    od=parse_od3(FIXTURE);assert_map(od)
    url=f'{BOATCAST}/txt/24/bc_smt_od3_20260918_24_06.txt'
    body=_get_fast(url,4,2)
    live=parse_od3(body)
    assert len(live)==120 and all(v>0 for v in live.values())
    print('HEAD4_BOATCAST_OD3_PARSER_OK')
    print('fixture_120',len(od),'live_120',len(live))
    print('live_4-1-2',live['4-1-2'])
if __name__=='__main__':main()
