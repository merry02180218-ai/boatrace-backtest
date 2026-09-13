#!/usr/bin/env python3
from __future__ import annotations
import json
import tempfile
from pathlib import Path

from build_4head_env_entry_live import PRIMITIVES
from head4_v291_downstream_inference import BOATS, load_artifact as load_down
from head4_v273_a_live_inference import load_artifact as load_a
from run_4head_v291_varn_auto_live import POLICY, prepare
from verify_4head_current_bundle import fixture as source_fixture


def main():
    down = load_down()
    aa = load_a()

    envst = down['ENV_ENTRY']
    envmed = dict(zip(envst['features'], envst['imputer_median']))
    env = {k: envmed[k] for k in PRIMITIVES}

    ast = aa['A_SCORE']
    afeatures = dict(zip(ast['features'], ast['imputer_median']))

    fs2 = down['v283_SECOND']['features']
    med2 = dict(zip(fs2, down['v283_SECOND']['imputer_median']))
    boats = {str(b): dict(med2) for b in range(1, 7)}
    for b in range(1, 7):
        for c in ('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg'):
            boats[str(b)][c] = 0.45 + 0.005*b

    bundle = {
        'race_code': '202609130101','PRE': 0.29,'POST': 0.26,
        'env_primitives': env,'a_features': afeatures,'boats': boats,
    }

    with tempfile.TemporaryDirectory(prefix='verify_head4_auto_') as td:
        src = Path(td) / 'bundle.json';outp = Path(td) / 'prepared.json'
        src.write_text(json.dumps(bundle, ensure_ascii=False), encoding='utf-8')
        out = prepare(str(src), str(outp))
        disk = json.loads(outp.read_text(encoding='utf-8'))

        causal = Path(td) / 'source.json'; prepared2=Path(td)/'prepared_source.json'; derived=Path(td)/'derived_bundle.json'
        causal.write_text(json.dumps(source_fixture(),ensure_ascii=False),encoding='utf-8')
        out2=prepare(None,str(prepared2),str(causal),str(derived))
        disk2=json.loads(prepared2.read_text(encoding='utf-8'))
        db=json.loads(derived.read_text(encoding='utf-8'))

    assert POLICY == 'HEAD4_V291_COMP7_VARN_F4_N16'
    assert out == disk
    assert out['race_code'] == '202609130101'
    assert 0.0 < float(out['ENV_ENTRY']) < 1.0
    assert set(map(int, out['p2'].keys())) == set(BOATS)
    assert len(out['cond']) == 20
    meta = out['_auto_meta']
    assert meta['policy'] == POLICY and meta['result_blind'] is True
    assert meta['jul_aug_labels_used'] is False and meta['september_labels_used'] is False and meta['v96_used'] is False

    # New strict source mode must reach the exact same frozen runner-input contract.
    assert out2==disk2 and out2['race_code']=='202609130101'
    assert len(out2['p2'])==5 and len(out2['cond'])==20
    assert db['_source_meta']['result_blind'] is True and db['_source_meta']['odds_used'] is False
    assert out2['_auto_meta']['policy']==POLICY
    print('HEAD4 v291 VARN AUTO LIVE bundle + strict source mode contract PASS')


if __name__ == '__main__':
    main()
