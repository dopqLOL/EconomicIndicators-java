#!/bin/bash
# MT5連携モジュール実行シェルスクリプト
# このシェルスクリプトはMT5連携モジュールをUnix系環境で実行します

echo "MT5連携モジュールを起動します..."

# カレントディレクトリをスクリプトのあるディレクトリに変更
cd "$(dirname "$0")"

# 必要なディレクトリが存在するか確認
mkdir -p "../csv/EconomicIndicators"
mkdir -p "../csv/MergedData"

# Pythonスクリプトを実行
python3 run_mt5_integration.py "$@"

# エラーがあれば表示
if [ $? -ne 0 ]; then
    echo "エラーが発生しました。詳細はログファイルを確認してください。"
    exit $?
fi

echo "MT5連携モジュールが正常に起動しました。終了するには Ctrl+C を押してください。" 