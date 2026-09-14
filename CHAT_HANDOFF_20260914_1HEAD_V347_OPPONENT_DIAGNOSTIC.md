# 1号艇 v347 opponent miss diagnostic

## 作業開始
- v345 production identityはprofile lock verifierで確定済み: PASS 276 / head 241 / exact3 121 / SHA `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`。
- v346 full reconstruction Run `34828125951` は二重確認として継続中。
- 現identityのexact3 missは155件。そのうち head-hit / exact3-miss は120件で、相手選びが最大の改善対象。
- v347ではproductionを変更せず、120件を以下に分解する。
  - coverage miss: 実際の2・3着のどちらかがcovered_boats外
  - slot/rank miss: 実際の2・3着はcovered内だがsecond/third候補の割当が不一致
  - ticket-layout miss: second/third候補には入っているが3点ticketに実着順が無い
- Feb-Junをpristine診断の主対象とし、Jul/AugはNON-PRISTINE support only。September outcomesはUNREAD。
