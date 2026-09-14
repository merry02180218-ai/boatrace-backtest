# 1号艇 v347 opponent miss diagnostic

## 作業開始
- v345 production identityはprofile lock verifierで確定済み: PASS 276 / head 241 / exact3 121 / SHA `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`。
- v346 full reconstruction Run `34828125951` は二重確認として継続中。
- 現identityのexact3 missは155件。そのうち head-hit / exact3-miss は120件で、相手選びが最大の改善対象。
- v347ではproductionを変更せず、120件をcoverage / slot-rank / ticket-layoutに分解する。
- Feb-Junをpristine診断の主対象とし、Jul/AugはNON-PRISTINE support only。September outcomesはUNREAD。

## 実装・結果
- script `run_v347_1head_opponent_miss_diagnostic.py` commit `55df877c2b13704da308423cea4e9d875895c71f`。
- workflow `.github/workflows/v347-1head-opponent-miss-diagnostic.yml` commit `c2fd369e20dfa0c3b3637554d80ca68400d9b0f8`。
- Run `34829503297` SUCCESS / Job `103929247701`。
- Artifact `10341681630` / digest `sha256:8784fc2c74a17c76d5fbffc33ef59d4e241414272a3e08788716fbbb4c9a0afe`。
- production identity再確認: 276R / head241 / exact3 121。
- exact3 miss 155件。うちhead-hit / exact3-miss 120件 = 77.4193548387%。head missは35件。
- 120件の相手外れ内訳:
  - coverage_miss 70件 = 58.3333%
  - slot_rank_miss 34件 = 28.3333%
  - ticket_layout_miss 16件 = 13.3333%
- Feb-Jun pristineのみ:
  - coverage_miss 57
  - slot_rank_miss 26
  - ticket_layout_miss 12
- Jul/Aug NON-PRISTINE supportのみ:
  - coverage_miss 13
  - slot_rank_miss 8
  - ticket_layout_miss 4
- productionは変更していない。
- `SEPTEMBER_OUTCOMES_READ=false`。

## 追加診断（artifact rowsから確認）
- coverage_miss 70件のうち、実2着だけcovered外 17件、実3着だけcovered外 49件、両方covered外 4件。
- Feb-Jun pristineでは実2着だけcovered外 13件、実3着だけcovered外 42件、両方covered外 2件。
- したがって次の優先順位は「3着側coverageの改善」>「2/3着slot-rank改善」>「3点ticket配置改善」。
- covered外で実際に来た艇は5・6号艇が最多傾向で、pristineでは5号艇19件 / 6号艇19件（重複含む）。

## 次工程
- v348ではproductionを変えず、3着側coverage missを中心に、uncovered側5/6号艇を拾うための事前・展示特徴を診断する。
- 改善案の選定はFeb-Jun pristineで行い、Jul/Augはsupport checkのみ。
