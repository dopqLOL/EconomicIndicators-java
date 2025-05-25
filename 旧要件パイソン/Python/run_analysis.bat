@echo off
setlocal enabledelayedexpansion

REM 経済指標ボラティリティ分析実行スクリプト
REM =============================================================

REM 色の設定
set BLUE=\033[94m
set GREEN=\033[92m
set YELLOW=\033[93m
set RED=\033[91m
set RESET=\033[0m

echo %BLUE%=========================================%RESET%
echo %BLUE%  経済指標ボラティリティ分析ツール%RESET%
echo %BLUE%=========================================%RESET%

REM カレントディレクトリの確認
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Pythonのチェック
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Pythonがインストールされていないか、PATHに設定されていません。%RESET%
    echo %RED%Pythonをインストールして、PATHに追加してください。%RESET%
    goto :error
)

REM 必要なライブラリのインストール確認
echo %YELLOW%必要なライブラリの確認中...%RESET%
python -c "import pandas, numpy, matplotlib, scipy" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW%必要なライブラリをインストールしています...%RESET%
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%ライブラリのインストールに失敗しました。%RESET%
        goto :error
    )
)

REM ディレクトリの確認と作成
set CSV_DIR=..\csv
set MERGED_DIR=%CSV_DIR%\MergedData
set STATS_DIR=%CSV_DIR%\Statistics
set ZIGZAG_DIR=%CSV_DIR%\Zigzag-data

if not exist %STATS_DIR% (
    echo %YELLOW%統計ディレクトリを作成しています...%RESET%
    mkdir %STATS_DIR%
)

REM 入力ファイルの確認
set INDICATORS_FILE=%MERGED_DIR%\indicators_with_volatility.csv
set ZIGZAG_PATTERN=%ZIGZAG_DIR%\mt5_zigzag_legs_*.csv

if not exist %INDICATORS_FILE% (
    echo %RED%指標ファイルが見つかりません: %INDICATORS_FILE%%RESET%
    echo %YELLOW%先にMT5統合スクリプトを実行してデータを取得し、%RESET%
    echo %YELLOW%merge_indicators_with_volatility.pyを実行してください。%RESET%
    goto :error
)

dir %ZIGZAG_PATTERN% > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%ZigZagデータファイルが見つかりません。%RESET%
    echo %YELLOW%先にMT5統合スクリプトを実行してZigZagデータを取得してください。%RESET%
    goto :error
)

REM 分析オプションの選択
echo %GREEN%実行する分析を選択してください:%RESET%
echo %YELLOW%1. データ処理（非対称分析）%RESET%
echo %YELLOW%2. 統計処理%RESET%
echo %YELLOW%3. マルチスケール分析%RESET%
echo %YELLOW%4. 統合分析（すべて実行）%RESET%
echo %YELLOW%5. テスト（単体テスト実行）%RESET%
echo %YELLOW%0. 終了%RESET%

set /p ANALYSIS_OPTION="選択 (0-5): "

REM 選択に応じてスクリプトを実行
if "%ANALYSIS_OPTION%"=="1" (
    echo %GREEN%データ処理（非対称分析）を実行しています...%RESET%
    python process_indicators.py --input_indicators %INDICATORS_FILE% --input_zigzag %ZIGZAG_DIR% --output_dir %STATS_DIR%
    if %ERRORLEVEL% NEQ 0 goto :error
    goto :success
) else if "%ANALYSIS_OPTION%"=="2" (
    echo %GREEN%統計処理を実行しています...%RESET%
    python statistical_processor.py --input_file %STATS_DIR%\analyzed_indicators.csv --output_dir %STATS_DIR%
    if %ERRORLEVEL% NEQ 0 goto :error
    goto :success
) else if "%ANALYSIS_OPTION%"=="3" (
    echo %GREEN%マルチスケール分析を実行しています...%RESET%
    python multiscale_analysis.py --input_file %STATS_DIR%\analyzed_indicators.csv --output_dir %STATS_DIR%
    if %ERRORLEVEL% NEQ 0 goto :error
    goto :success
) else if "%ANALYSIS_OPTION%"=="4" (
    echo %GREEN%統合分析（すべて）を実行しています...%RESET%
    python integrated_analysis.py --input_indicators %INDICATORS_FILE% --input_zigzag %ZIGZAG_DIR% --output_dir %STATS_DIR%
    if %ERRORLEVEL% NEQ 0 goto :error
    goto :success
) else if "%ANALYSIS_OPTION%"=="5" (
    echo %GREEN%単体テストを実行しています...%RESET%
    python test_analysis.py
    if %ERRORLEVEL% NEQ 0 goto :error
    goto :success
) else if "%ANALYSIS_OPTION%"=="0" (
    echo %YELLOW%終了します。%RESET%
    goto :end
) else (
    echo %RED%無効な選択です。%RESET%
    goto :error
)

:success
echo %GREEN%処理が正常に完了しました！%RESET%
goto :end

:error
echo %RED%エラーが発生しました。処理を中断します。%RESET%

:end
endlocal
pause 