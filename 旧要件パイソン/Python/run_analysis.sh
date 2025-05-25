#!/bin/bash
# 経済指標ボラティリティ分析実行スクリプト
# =============================================================

# 色の設定
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${BLUE}==========================================${RESET}"
echo -e "${BLUE}  経済指標ボラティリティ分析ツール${RESET}"
echo -e "${BLUE}==========================================${RESET}"

# カレントディレクトリをスクリプトの場所に変更
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Pythonのチェック
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3がインストールされていません。${RESET}"
    echo -e "${RED}Python 3をインストールしてください。${RESET}"
    exit 1
fi

# Pythonコマンドの設定
PYTHON="python3"
if command -v python &> /dev/null && [[ $(python --version 2>&1) == *"Python 3"* ]]; then
    PYTHON="python"
fi

# 必要なライブラリのインストール確認
echo -e "${YELLOW}必要なライブラリの確認中...${RESET}"
$PYTHON -c "import pandas, numpy, matplotlib, scipy" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}必要なライブラリをインストールしています...${RESET}"
    $PYTHON -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}ライブラリのインストールに失敗しました。${RESET}"
        exit 1
    fi
fi

# ディレクトリの確認と作成
CSV_DIR="../csv"
MERGED_DIR="$CSV_DIR/MergedData"
STATS_DIR="$CSV_DIR/Statistics"
ZIGZAG_DIR="$CSV_DIR/Zigzag-data"

if [ ! -d "$STATS_DIR" ]; then
    echo -e "${YELLOW}統計ディレクトリを作成しています...${RESET}"
    mkdir -p "$STATS_DIR"
fi

# 入力ファイルの確認
INDICATORS_FILE="$MERGED_DIR/indicators_with_volatility.csv"
ZIGZAG_PATTERN="$ZIGZAG_DIR/mt5_zigzag_legs_*.csv"

if [ ! -f "$INDICATORS_FILE" ]; then
    echo -e "${RED}指標ファイルが見つかりません: $INDICATORS_FILE${RESET}"
    echo -e "${YELLOW}先にMT5統合スクリプトを実行してデータを取得し、${RESET}"
    echo -e "${YELLOW}merge_indicators_with_volatility.pyを実行してください。${RESET}"
    exit 1
fi

if [ -z "$(ls $ZIGZAG_PATTERN 2>/dev/null)" ]; then
    echo -e "${RED}ZigZagデータファイルが見つかりません。${RESET}"
    echo -e "${YELLOW}先にMT5統合スクリプトを実行してZigZagデータを取得してください。${RESET}"
    exit 1
fi

# 分析オプションの選択
echo -e "${GREEN}実行する分析を選択してください:${RESET}"
echo -e "${YELLOW}1. データ処理（非対称分析）${RESET}"
echo -e "${YELLOW}2. 統計処理${RESET}"
echo -e "${YELLOW}3. マルチスケール分析${RESET}"
echo -e "${YELLOW}4. 統合分析（すべて実行）${RESET}"
echo -e "${YELLOW}5. テスト（単体テスト実行）${RESET}"
echo -e "${YELLOW}0. 終了${RESET}"

read -p "選択 (0-5): " ANALYSIS_OPTION

# 選択に応じてスクリプトを実行
case $ANALYSIS_OPTION in
    1)
        echo -e "${GREEN}データ処理（非対称分析）を実行しています...${RESET}"
        $PYTHON process_indicators.py --input_indicators "$INDICATORS_FILE" --input_zigzag "$ZIGZAG_DIR" --output_dir "$STATS_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}エラーが発生しました。処理を中断します。${RESET}"
            exit 1
        fi
        ;;
    2)
        echo -e "${GREEN}統計処理を実行しています...${RESET}"
        $PYTHON statistical_processor.py --input_file "$STATS_DIR/analyzed_indicators.csv" --output_dir "$STATS_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}エラーが発生しました。処理を中断します。${RESET}"
            exit 1
        fi
        ;;
    3)
        echo -e "${GREEN}マルチスケール分析を実行しています...${RESET}"
        $PYTHON multiscale_analysis.py --input_file "$STATS_DIR/analyzed_indicators.csv" --output_dir "$STATS_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}エラーが発生しました。処理を中断します。${RESET}"
            exit 1
        fi
        ;;
    4)
        echo -e "${GREEN}統合分析（すべて）を実行しています...${RESET}"
        $PYTHON integrated_analysis.py --input_indicators "$INDICATORS_FILE" --input_zigzag "$ZIGZAG_DIR" --output_dir "$STATS_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}エラーが発生しました。処理を中断します。${RESET}"
            exit 1
        fi
        ;;
    5)
        echo -e "${GREEN}単体テストを実行しています...${RESET}"
        $PYTHON test_analysis.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}エラーが発生しました。処理を中断します。${RESET}"
            exit 1
        fi
        ;;
    0)
        echo -e "${YELLOW}終了します。${RESET}"
        exit 0
        ;;
    *)
        echo -e "${RED}無効な選択です。${RESET}"
        exit 1
        ;;
esac

echo -e "${GREEN}処理が正常に完了しました！${RESET}" 