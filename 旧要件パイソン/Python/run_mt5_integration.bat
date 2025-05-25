@echo off
REM MT5連携モジュール実行バッチファイル
REM このバッチファイルはMT5連携モジュールをWindows環境で実行します

echo MT5連携モジュールを起動します...

REM カレントディレクトリをスクリプトのあるディレクトリに変更
cd /d "%~dp0"

REM 必要なディレクトリが存在するか確認
if not exist "..\csv\EconomicIndicators" mkdir "..\csv\EconomicIndicators"
if not exist "..\csv\MergedData" mkdir "..\csv\MergedData"

REM Pythonスクリプトを実行
python run_mt5_integration.py %*

REM エラーがあれば表示
if %ERRORLEVEL% neq 0 (
    echo エラーが発生しました。詳細はログファイルを確認してください。
    pause
    exit /b %ERRORLEVEL%
)

echo MT5連携モジュールが正常に起動しました。終了するには Ctrl+C を押してください。
pause 