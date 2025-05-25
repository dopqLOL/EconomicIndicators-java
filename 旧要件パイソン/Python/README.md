# 経済指標ボラティリティ分析ツール

## 概要

このツールは、外国為替市場における経済指標発表と価格変動（ボラティリティ）の関係を分析・視覚化するStreamlitベースのWebアプリケーションです。MT5から取得したZigZagデータと経済指標データを統合・分析し、指標ごとの時間帯ボラティリティ統計を提供します。

## 主な機能

- 当日指標一覧表示
- 統計情報表示（3分類平均値、中央値）
- 直近2回の時間帯ボラティリティ表示
- 地合い判断結果表示
- ソート・フィルタリング機能
- データエクスポート機能

## 必要条件

- Python 3.8以上
- MT5（データ取得に使用）
- 必要なPythonライブラリ（requirements.txtに記載）

## インストール方法

1. リポジトリをクローンまたはダウンロードします。

```
git clone https://github.com/yourusername/economic-indicators-analyzer.git
cd economic-indicators-analyzer
```

2. 必要なライブラリをインストールします。

```
pip install -r Python/requirements.txt
```

## 使用方法

### データ準備

1. MT5側の設定
   - `mql5/EconomicIndicatorsExporter_Auto.mq5` をMT5のMQL5/Scriptsフォルダにコピーします。
   - MT5でスクリプトを実行し、経済指標データとZigZagデータをエクスポートします。

2. データディレクトリの確認
   - `csv/Zigzag-data/` にZigZagデータファイルが配置されていることを確認します。
   - `csv/EconomicIndicators/` に経済指標データファイルが配置されていることを確認します。

### アプリケーションの実行

#### Windowsの場合

```
Python/run_app.bat
```

または

```
cd Python
streamlit run app.py
```

#### Mac/Linuxの場合

```
./Python/run_app.sh
```

または

```
cd Python
streamlit run app.py
```

## アプリケーションの使用方法

1. ブラウザで自動的に開かれるStreamlitアプリケーションにアクセスします（通常は http://localhost:8501）。

2. サイドバーの「データ処理を実行」ボタンをクリックして、データ処理を実行します。
   - 初回実行時や新しいデータが追加された場合に実行してください。

3. 分析時間帯設定を調整します（デフォルトは日本時間7:00-9:00）。

4. 当日の経済指標一覧が表示されます。
   - ソート順を変更して表示順を調整できます。
   - 各指標の3分類平均値、中央値、直近値、地合い判断結果を確認できます。

5. 統計情報サマリーで通貨別の指標数や地合い判断の分布を確認できます。

6. 必要に応じてCSVダウンロードボタンからデータをエクスポートできます。

## ファイル構成

- `Python/data_processor.py` - データ処理モジュール
- `Python/app.py` - Streamlitアプリケーション
- `Python/requirements.txt` - 依存ライブラリ定義
- `Python/run_app.bat` - Windows用実行スクリプト
- `Python/run_app.sh` - Unix/Linux用実行スクリプト
- `mql5/EconomicIndicatorsExporter_Auto.mq5` - MT5データエクスポートスクリプト

## データファイル

- `csv/Zigzag-data/mt5_zigzag_legs_*.csv` - ZigZagデータファイル
- `csv/EconomicIndicators/EconomicIndicators_*.csv` - 経済指標データファイル
- `csv/Statistics/indicator_statistics_*.csv` - 生成された統計データファイル
- `csv/Statistics/indicator_volatility_*.csv` - 生成されたボラティリティデータファイル

## トラブルシューティング

- **アプリケーションが起動しない場合**
  - Streamlitがインストールされているか確認してください。
  - `pip install streamlit` でインストールできます。

- **データが表示されない場合**
  - 必要なデータファイルが正しい場所に配置されているか確認してください。
  - サイドバーの「データ処理を実行」ボタンをクリックしてデータ処理を実行してください。

- **MT5連携に問題がある場合**
  - MT5が正常に動作しているか確認してください。
  - スクリプトが正しく配置されているか確認してください。
  - 出力ディレクトリの権限を確認してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は `LICENSE` ファイルを参照してください。

## 連絡先

問題や質問がある場合は、Issueを作成するか、以下の連絡先までご連絡ください。

- Email: your.email@example.com
- GitHub: [yourusername](https://github.com/yourusername) 