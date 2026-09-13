from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave39v_combined_odds as w39v
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave37_orderer as w37

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave39c_confidence_k.json')
CUT=.365448
RULES=[('p40_k3_f35',.40,3,3.5),('p45_k4_f35',.45,4,3.5),('p50_k5_f35',.50,5,3.5),('p45_k4_f40',.45,4,4.0)]
