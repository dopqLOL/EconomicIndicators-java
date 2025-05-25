@echo off
echo ===== 経済指標ボラティリティ分析ツール =====
echo Streamlitアプリケーションを起動します...

cd %~dp0
streamlit run app.py

if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました。
    echo Streamlitがインストールされているか確認してください。
    echo インストールするには: pip install streamlit
    pause
) else (
    echo アプリケーションが終了しました。
    pause
) 