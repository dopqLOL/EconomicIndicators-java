#!/bin/bash

echo "===== 経済指標ボラティリティ分析ツール ====="
echo "Streamlitアプリケーションを起動します..."

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Streamlitアプリケーションを実行
streamlit run app.py

if [ $? -ne 0 ]; then
    echo "エラーが発生しました。"
    echo "Streamlitがインストールされているか確認してください。"
    echo "インストールするには: pip install streamlit"
    read -p "Enterキーを押して終了..."
else
    echo "アプリケーションが終了しました。"
    read -p "Enterキーを押して終了..."
fi 