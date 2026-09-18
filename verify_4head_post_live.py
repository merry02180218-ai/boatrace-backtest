#!/usr/bin/env python3
from __future__ import annotations

from build_4head_post_live import (
    PostBuildError,
    build_from_sources,
    parse_start_timing,
    parse_boatcast_original,
    parse_boatcast_st,
)

HTML = '''<html><body><table>
<tr><th>艇番</th><th>展示タイム</th><th>チルト</th></tr>
<tr><td>1</td><td>6.80</td><td>-0.5</td></tr>
<tr><td>2</td><td>6.81</td><td>0.0</td></tr>
<tr><td>3</td><td>6.82</td><td>0.0</td></tr>
<tr><td>4</td><td>6.79</td><td>+0.5</td></tr>
<tr><td>5</td><td>6.83</td><td>0.0</td></tr>
<tr><td>6</td><td>6.84</td><td>0.0</td></tr>
</table></body></html>'''

ST = '''data=\n1\t6\n1\t1\tA\tx\t.14\t\n2\t2\tB\tx\t.13\t\n3\t3\tC\tx\t.16\t\n5\t4\tD\tx\t.12\t\n4\t5\tE\tx\t.15\t\n6\t6\tF\tx\t.18\t\n'''

ORIG = '''data=\n1\t3\n一周\tまわり足\t直線\n1\tA\t37.20\t5.60\t7.40\n2\tB\t37.10\t5.55\t7.35\n3\tC\t37.00\t5.50\t7.30\n4\tD\t36.90\t5.45\t7.25\n5\tE\t37.30\t5.65\t7.45\n6\tF\t37.40\t5.70\t7.50\n'''


def expect_fail(fn):
    try:
        fn()
    except PostBuildError:
        return
    raise AssertionError('expected fail-closed error')


def main():
    assert parse_start_timing('.08', 'F') == -0.08
    assert parse_start_timing('.08', '') == 0.08
    assert parse_start_timing('.08', 'L') is None

    # BOATCAST can physically wrap a player-name field mid-record.
    st_wrapped = '''data=\n1\n1\t1\tA\t.19\t.10\t\t3.0\n2\t2\tB\t.14\t.26\t\t1.5\n3\t3\tC\t.17\t.14\t\t4.0\n4\t4\tD_PART
\t.19\t.15\t\t4.0\n5\t5\tE\t.19\t.19\t\t5.5\n6\t6\tF\t.31\t.22\t\t6.0\n'''
    pst = parse_boatcast_st(st_wrapped)
    assert set(pst) == set(range(1,7))
    assert pst[4] == 0.15

    labels, rows = parse_boatcast_original(ORIG)
    assert labels == ['一周', 'まわり足', '直線']
    assert rows[4] == [36.9, 5.45, 7.25]

    # Original-exhibition rows can also wrap inside the player-name field.
    orig_wrapped = ORIG.replace('1\tA\t37.20\t5.60\t7.40', '1\tA_PART\nIAL\t37.20\t5.60\t7.40')
    wl, wr = parse_boatcast_original(orig_wrapped)
    assert wl == labels
    assert set(wr) == set(range(1,7))
    assert wr[1] == [37.2, 5.6, 7.4]

    z = build_from_sources('20260630', 1, 1, HTML, ST, ORIG)
    assert list(z) == [
        'ex_st_rank4','ex_st_4','ex_st_edge_4v3',
        'orig_straight4','orig_lap4','orig_turn4','tilt4'
    ]
    assert z['ex_st_4'] == 0.12
    assert abs(z['ex_st_edge_4v3'] - 0.04) < 1e-12
    assert z['ex_st_rank4'] == 1.0
    assert z['orig_straight4'] == 1.0
    assert z['orig_lap4'] == 1.0
    assert z['orig_turn4'] == 1.0
    assert z['tilt4'] == 0.5

    # Two-metric venue: absent straight remains frozen historical default 0.5.
    orig2 = ORIG.replace('1\t3\n一周\tまわり足\t直線', '1\t2\n一周\tまわり足')
    orig2 = '\n'.join('\t'.join(line.split('\t')[:4]) if line and line[0].isdigit() and '\t' in line and len(line.split('\t')) >= 5 else line for line in orig2.splitlines()) + '\n'
    q = build_from_sources('20260630', 1, 1, HTML, ST, orig2)
    assert q['orig_straight4'] == 0.5

    # Required lane 3/4 ST missing/L => fail closed.
    expect_fail(lambda: build_from_sources('20260630',1,1,HTML,ST.replace('5\t4\tD\tx\t.12\t','5\t4\tD\tx\t.12\tL'),ORIG))
    # Original exhibition not measured => fail closed.
    expect_fail(lambda: build_from_sources('20260630',1,1,HTML,ST,ORIG.replace('1\t3','0\t3',1)))
    # Tilt absent => fail closed.
    expect_fail(lambda: build_from_sources('20260630',1,1,HTML.replace('チルト','角度'),ST,ORIG))
    # Boat row missing => fail closed.
    expect_fail(lambda: parse_boatcast_original(ORIG.replace('6\tF\t37.40\t5.70\t7.50\n','')))

    print('HEAD4_POST_LIVE_VERIFY_OK')


if __name__ == '__main__':
    main()
