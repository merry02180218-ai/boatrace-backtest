# v161 ST-context confirmation gate

- v160でST contextをv109へ直接追加するとS頭率が低下したため、**CURRENT v109のS判定は固定したまま補助確認/vetoとして使えるか**を検証。
- Julyだけで補助閾値を選び、Augustは untouched holdout。
- CURRENT S=0.72固定。July候補は600R以上かつCURRENT Sの70%以上を残す条件。
- Julyで頭率最大（同率ならcoverage最大）の閾値を選択し、Augustへそのまま適用。

## baseline
|月|R|頭率|
|---|---:|---:|
|2026-07 CURRENT S|1131|77.45%|
|2026-08 CURRENT S|1016|76.77%|

## July tune → August holdout
|policy|閾値|July R|July頭率|July coverage|Aug R|Aug頭率|Aug coverage|Aug Δ頭率|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|FSTATE|0.76|929|78.15%|82.1%|709|79.13%|69.8%|+2.35pt|
|NEIGHBOR|0.76|878|78.47%|77.6%|663|81.00%|65.3%|+4.22pt|
|BOTH_MIN|0.76|865|78.38%|76.5%|653|81.01%|64.3%|+4.24pt|
|BOTH_AVG|0.76|906|78.15%|80.1%|680|80.29%|66.9%|+3.52pt|
|COMBINED|0.76|902|78.27%|79.8%|680|80.15%|66.9%|+3.38pt|

## 判定
- AugustでCURRENTを上回りつつcoverage 70%以上を維持するpolicyなし。ST contextは説明用補助に留める。
