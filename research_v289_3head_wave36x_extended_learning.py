import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave36x_extended_learning.json')
CUT=.365448
K=5
