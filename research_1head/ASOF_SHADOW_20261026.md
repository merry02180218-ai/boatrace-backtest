# GitHub正式v351 → 2026年9–10月の同一時刻Shadow比較 準備

**作成日：2026-10-26 JST ／ 研究専用。ベット推奨・LIVEデプロイは不可。**

## 研究の前提

GitHub正式v351 frozen 276R：2–8月 HEAD241/276, 3連単131/276, 全点賭金82,800円、実払戻86,390円、ROI104.34%。元v351券面の再生成は275/276Rまで一致。2026-03-12 浜名湖4Rの残り1Rは、3着4/5のpair score差0.008637 percentage pointsという再現性上の僅差（原因の断定・後付け修正禁止）。

2026年9–10月のLIVE本番は**異なる**GitLab PRE>=0.775、POST>=0.800、persistent ST-risk CLEAR と現行BASE3。9/26–10/20の同52Rで16的中/ROI66.99%（事後historical as-of snapshot）という基準と混同しない。

## このブランチの実装

- `v351_asof_shadow_gate_20261026.py`：2026年9月・10月のレースについて、**実際に締切3分前より前に保存された**出走カード・公式展示／展示ST・天候・BOATERSオリジナル展示のファイルと、タイムスタンプ・SHA256を照合。元の `run_v323_1head_frozen_live_adapter.py` の `current_static/build_current_features/head_score/opponent_score` をimportし、元v351由来の HEAD＋v317 P2／条件付きv318 P3 のPREのみをShadowで採点する。
- `test_v351_asof_shadow_gate_20261026.py`：期限後スナップショット・結果混入を疑う書換・パストラバーサル・Origin欠損・TZなし・同じ月の履歴投入等をテスト。
- `.github/workflows/gh351-asof-research-unit.yml`：研究branchだけの単体テストをGitHub Actions上で回す。結果にかかわらず本番GitLab LIVEリリースへは連動しない。

**PREのみの実装であり、展示/オリジナルの数値をスコアへ作用させるv351正式POSTは未実装。** 展示ソースは現時点では締切前観測の監査だけで、P2/P3スコアには入らない。`bet_ready=false`相当、投資対象として利用禁止。

## 入力インターフェース

`--date YYYY-MM-DD`、`--cards CSV`、`--manifest JSON`、`--head-history CSV`、`--opponent-history CSV`、`--output JSON`。準備ファイルはGitHub元コードが本来使う `cache_v321_julaug_nonpristine_head.csv` と `cache_v321_julaug_nonpristine_slim.csv.gz` のほか、追加の実測タイムスタンプつき原始ファイル。

Manifest JSON（例は仮想データ、公式データではない）:
```json
{
  "target_date": "2026-10-26",
  "races": [
    {
      "race_code": "202610260104",
      "deadline_jst": "2026-10-26T12:00:00+09:00",
      "sources": {
        "race_cards": {
          "file": "snapshots/cards_20261026_115000.csv",
          "observed_at_jst": "2026-10-26T11:50:00+09:00",
          "sha256": "SHA256_IN_LOWERCASE_HEX"
        },
        "official_tkz": {"file": "snapshots/tkz.csv", "observed_at_jst": "2026-10-26T11:53:00+09:00", "sha256": "SHA256_IN_LOWERCASE_HEX"},
        "official_stt": {"file": "snapshots/stt.csv", "observed_at_jst": "2026-10-26T11:53:00+09:00", "sha256": "SHA256_IN_LOWERCASE_HEX"},
        "official_sui": {"file": "snapshots/sui.csv", "observed_at_jst": "2026-10-26T11:53:00+09:00", "sha256": "SHA256_IN_LOWERCASE_HEX"},
        "boaters_original_exhibition": {"file": "snapshots/boaters.csv", "observed_at_jst": "2026-10-26T11:53:00+09:00", "sha256": "SHA256_IN_LOWERCASE_HEX"}
      }
    }
  ]
}
```
**仮想時刻や偽のSHAは使用不可**。現実のoriginalブックされた場合は該当RのShadowをBLOCKして、架空の埋め戻しはしない。card pathのSHAは`--cards`と全件一致必須。

## 研究に必要な追加作業

1. 9月と10月の現行LIVE保存ログの`as_of / race_code / deadline / official / BOATERS original`及び当時のraw snapshotをGitLabからread-only抽出。**撮影記録が無い過去月に、今取得した最新版CSVを代入してはいけない**。
2. ギットハブ v321 HEAD/P2/P3の7–8月学習済みCSVを研究ブランチのCI artifactから参照して9/10月で推論。既存GitLab workerのアーティファクトを無制限に使う場合、リーク用監査より後の再学習情報を混ぜない。
3. GitHub正式v351のHEAD v308選別ゲート（PRE/POST）と、GitLab正式52Rゲートの相違を別レポートにする。同じ52Rの買い目3点の優劣は**固定した共通レース集合で**、各モデル単独ROIは**自身の選別集合の全投資で**示す。
4. 原GH v351のv347 core補正+条件付きP3を締切前as-of時点へ接続し、同じスナップショットを両方式へ渡す。ROI・毎月件数・最大DDを算出する前にスナップショット時間とHEADゲート一致・公的払い戻し事後決済の境界を立証。
5. G3=0.992983等の過去1Rに合わせた改定は禁止。9–10月は未使用期間だったわけではなく、データを過去研究で調べているため、最後は未来のShadowで採用可否を決める。

## GitLab接続状態（このブランチ作成時）

2026-10-26の作業でGitLab connected APIが`403 Forbidden - Your account has been blocked`を返し、read-only job取得まで拒否された。**このため、本作業中にGitLab LIVEログのas-of比較、GitLabへコミット、新しいGitLabジョブ起動は一切成功していない。** 代わりにユーザー既存GitHub repoの**隔離研究ブランチ**にコード/テストのみ記録。本番にはマージしない。

