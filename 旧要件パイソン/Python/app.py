#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
経済指標ボラティリティ分析アプリケーション

このモジュールは、経済指標ボラティリティ分析結果を表示するためのStreamlitベースの
Webアプリケーションを提供します。経済指標データと時間帯ボラティリティの統計情報を
視覚的に表示し、当日の指標が過去にどの程度の値動きに関連していたかを把握できるように
支援します。

主な機能:
- 当日指標一覧表示
- 統計情報表示（3分類平均値、中央値）
- 直近2回の時間帯ボラティリティ表示
- 地合い判断結果表示
"""

import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# 自作モジュールのインポート
try:
    from data_processor import DataProcessor
except ImportError:
    # 現在のディレクトリをPythonパスに追加
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_processor import DataProcessor

# 定数定義
DEFAULT_ZIGZAG_DIR = "../csv/Zigzag-data"
DEFAULT_INDICATORS_DIR = "../csv/EconomicIndicators"
DEFAULT_STATISTICS_DIR = "../csv/Statistics"
DEFAULT_TIME_WINDOW_START = 7  # 日本時間 午前7時
DEFAULT_TIME_WINDOW_END = 9    # 日本時間 午前9時

# ページ設定
st.set_page_config(
    page_title="経済指標ボラティリティ分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DataProcessor から固定時間帯定義を直接参照できるようにする
# (app.py 内で DataProcessor インスタンスを作成しない場合に備えて)
FIXED_TIME_WINDOWS_JST_FOR_APP = [
    (0, 3), (3, 6), (7, 9), (9, 12), (12, 15), (15, 21), (21, 24)
]

def load_latest_statistics(stats_dir: str = DEFAULT_STATISTICS_DIR) -> pd.DataFrame:
    """
    最新の統計データを読み込む (固定時間帯対応版)
    
    Args:
        stats_dir: 統計データディレクトリ
        
    Returns:
        DataFrame: 統計データ (カラム: Currency, EventName, TimeWindow_Slot, Volatility_Mean, ...)
    """
    try:
        # 統計ファイルを検索 (新しい命名規則に対応)
        stats_files = list(Path(stats_dir).glob("indicator_statistics_for_fixed_windows_*.csv"))
        
        if not stats_files:
            st.error(f"統計データファイルが見つかりません (固定時間帯形式): {stats_dir}")
            return pd.DataFrame()
        
        # 最新のファイルを取得
        latest_file = max(stats_files, key=lambda x: x.stat().st_mtime)
        st.info(f"最新の統計データを読み込みます (固定時間帯形式): {latest_file.name}")
        
        # データ読み込み
        df = pd.read_csv(latest_file)
        return df
        
    except Exception as e:
        st.error(f"統計データの読み込みエラー: {e}")
        return pd.DataFrame()

def load_today_indicators(indicators_dir: str = DEFAULT_INDICATORS_DIR) -> pd.DataFrame:
    """
    当日の経済指標データを読み込む
    
    Args:
        indicators_dir: 経済指標データディレクトリ
        
    Returns:
        DataFrame: 当日の経済指標データ
    """
    try:
        # 最新の経済指標ファイルを検索
        today = datetime.now().strftime("%Y%m%d")
        indicator_files = list(Path(indicators_dir).glob(f"EconomicIndicators_*{today}*.csv"))
        
        # 当日のファイルがない場合は最新のファイルを使用
        if not indicator_files:
            indicator_files = list(Path(indicators_dir).glob("EconomicIndicators_*.csv"))
            
        if not indicator_files:
            st.error(f"経済指標データファイルが見つかりません: {indicators_dir}")
            return pd.DataFrame()
        
        # 最新のファイルを取得
        latest_file = max(indicator_files, key=lambda x: x.stat().st_mtime)
        st.info(f"経済指標データを読み込みます: {latest_file.name}")
        
        # データ読み込み
        df = pd.read_csv(latest_file)
        
        # 日時列を処理
        if 'DateTime (UTC)' in df.columns:
            df['DateTime_UTC'] = pd.to_datetime(df['DateTime (UTC)'], format='%Y.%m.%d %H:%M:%S')
            # JSTに変換（UTC+9）
            df['DateTime_JST'] = df['DateTime_UTC'] + pd.Timedelta(hours=9)
        
        # 当日のデータのみを抽出
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        
        today_df = df[(df['DateTime_JST'] >= today_start) & (df['DateTime_JST'] < tomorrow_start)]
        
        if len(today_df) == 0:
            st.warning("当日の経済指標データがありません。最新の日付のデータを表示します。")
            # 最新の日付のデータを取得
            if len(df) > 0:
                latest_date = df['DateTime_JST'].dt.date.max()
                today_df = df[df['DateTime_JST'].dt.date == latest_date]
        
        return today_df
        
    except Exception as e:
        st.error(f"経済指標データの読み込みエラー: {e}")
        return pd.DataFrame()

def merge_indicators_with_statistics(today_df: pd.DataFrame, filtered_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    当日の経済指標データと、選択された時間帯スロットの統計データを結合する
    
    Args:
        today_df: 当日の経済指標データ
        filtered_stats_df: 特定の時間帯スロットでフィルタリング済みの統計データ
        
    Returns:
        DataFrame: 結合されたデータ
    """
    if len(today_df) == 0 or len(filtered_stats_df) == 0:
        # filtered_stats_df が空の場合は、統計情報なしの today_df を返すイメージでも良いが、
        # 呼び出し側でハンドリングしているのでここでは空を返す。
        return pd.DataFrame()
    
    try:
        # 結合キーの準備 (Currency, EventName)
        # filtered_stats_df には TimeWindow_Slot も含まれるが、マージキーにはしない
        # (既に特定スロットでフィルタリングされているため、CurrencyとEventNameでほぼ一意になるはず)
        merged_df = pd.merge(today_df, 
                             filtered_stats_df[['Currency', 'EventName', 'Volatility_Mean', 'Volatility_Median', 'Volatility_Std', 'Volatility_Min', 'Volatility_Max', 'Sample_Count']], 
                             on=['Currency', 'EventName'], 
                             how='left')
        
        return merged_df
        
    except Exception as e:
        st.error(f"データ結合エラー (merge_indicators_with_statistics): {e}")
        return pd.DataFrame()

def format_display_table(merged_df: pd.DataFrame, selected_time_window: str) -> pd.DataFrame:
    """
    表示用にデータを整形する
    
    Args:
        merged_df: 結合されたデータ (当日指標 + 選択時間帯の統計)
        selected_time_window: 選択された時間帯スロット (例: "07-09_JST") - 表示用
        
    Returns:
        DataFrame: 表示用に整形されたデータ
    """
    if len(merged_df) == 0:
        return pd.DataFrame()
    
    try:
        # 表示用のデータフレームを作成
        display_df = merged_df.copy()
        
        # 日時列をフォーマット
        if 'DateTime_JST' in display_df.columns:
            display_df['発表時刻'] = display_df['DateTime_JST'].dt.strftime('%H:%M')
        
        # 表示列を選択 (新しい統計カラムに対応)
        display_cols = [
            '発表時刻', 'Currency', 'EventName', 
            'Volatility_Mean', 'Volatility_Median', 'Sample_Count',
            'Volatility_Std', 'Volatility_Min', 'Volatility_Max' # 必要に応じて追加
        ]
        # 存在しない可能性のある列をフィルタリング
        display_cols = [col for col in display_cols if col in display_df.columns]
        
        # 列名の日本語表示用マッピング (新しい統計カラムに対応)
        col_mapping = {
            'Currency': '通貨',
            'EventName': '指標名',
            'Volatility_Mean': '平均変動',
            'Volatility_Median': '変動中央値',
            'Sample_Count': 'サンプル数',
            'Volatility_Std': '標準偏差',
            'Volatility_Min': '最小変動',
            'Volatility_Max': '最大変動'
        }
        
        # 列名を変更
        display_df = display_df[display_cols].rename(columns=col_mapping)
        
        # 数値列を小数点以下3桁に丸める (新しい統計カラムに対応)
        float_cols = ['平均変動', '変動中央値', '標準偏差', '最小変動', '最大変動']
        for col in float_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(3)
        
        # 時間帯スロット情報を表示に含める場合 (任意)
        # display_df['分析時間帯'] = selected_time_window 
        
        return display_df
        
    except Exception as e:
        st.error(f"表示データ整形エラー (format_display_table): {e}")
        return pd.DataFrame()

def display_data_table(display_df: pd.DataFrame):
    """
    データテーブルを表示する
    
    Args:
        display_df: 表示用データ
    """
    if len(display_df) == 0:
        st.info("表示するデータがありません。")
        return
    
    st.dataframe(display_df, height=600)

def display_statistics_summary(stats_df: pd.DataFrame, selected_time_window_slot: Optional[str]):
    """
    統計情報のサマリーを表示する (選択された時間帯スロットでフィルタリング)
    
    Args:
        stats_df: 統計データ
        selected_time_window_slot: ユーザーが選択した時間帯スロット (例: "07-09_JST")
    """
    if len(stats_df) == 0:
        return

    st.subheader("指標別ボラティリティ統計サマリー")

    if selected_time_window_slot:
        filtered_stats = stats_df[stats_df['TimeWindow_Slot'] == selected_time_window_slot]
        if filtered_stats.empty:
            st.warning(f"{selected_time_window_slot} に該当する統計データはありません。")
            return
        display_stats = filtered_stats
        st.write(f"時間帯: {selected_time_window_slot} の統計")
    else:
        st.warning("時間帯スロットが選択されていません。最初の時間帯スロットの統計を表示します。")
        # デフォルトで最初のスロットを表示（あるいは全スロットの集計など、要件に応じて変更）
        first_slot = stats_df['TimeWindow_Slot'].unique()[0] if len(stats_df['TimeWindow_Slot'].unique()) > 0 else None
        if first_slot:
            display_stats = stats_df[stats_df['TimeWindow_Slot'] == first_slot]
            st.write(f"時間帯: {first_slot} の統計 (デフォルト)")
        else:
            st.error("表示できる統計データがありません。")
            return

    # 表示するカラムを選択（例）
    summary_cols = ['Currency', 'EventName', 'Volatility_Mean', 'Volatility_Median', 'Sample_Count']
    st.dataframe(display_stats[summary_cols].sort_values(by=['Currency', 'Volatility_Mean'], ascending=[True, False]))

    # --- グラフ表示 (例: 上位10指標の平均ボラティリティ) ---
    st.subheader("平均ボラティリティ TOP 10")
    top_10_volatility = display_stats.nlargest(10, 'Volatility_Mean')

    if not top_10_volatility.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=top_10_volatility, x='Volatility_Mean', y='EventName', ax=ax, palette="viridis")
        ax.set_title(f"平均ボラティリティ TOP 10 ({selected_time_window_slot or 'デフォルト'})")
        ax.set_xlabel("平均ボラティリティ")
        ax.set_ylabel("経済指標")
        st.pyplot(fig)
    else:
        st.info("グラフ表示する十分なデータがありません。")

def run_data_processing():
    """
    データ処理を実行する
    """
    with st.spinner('データ処理を実行中...'):
        try:
            # データ処理インスタンスの作成
            processor = DataProcessor(
                zigzag_dir=DEFAULT_ZIGZAG_DIR,
                indicators_dir=DEFAULT_INDICATORS_DIR,
                output_dir=DEFAULT_STATISTICS_DIR,
                time_window_start=DEFAULT_TIME_WINDOW_START,
                time_window_end=DEFAULT_TIME_WINDOW_END
            )
            
            # 全処理の実行
            volatility_df, statistics_df = processor.process_all()
            
            if len(volatility_df) > 0 and len(statistics_df) > 0:
                st.success(f"データ処理が完了しました。{len(statistics_df)}件の指標統計情報を計算しました。")
                return True
            else:
                st.error("データ処理に失敗しました。")
                return False
                
        except Exception as e:
            st.error(f"データ処理エラー: {e}")
            return False

def main():
    """
    メイン関数
    """
    st.title("経済指標 固定時間帯ボラティリティ分析")

    # --- サイドバー --- 
    st.sidebar.header("設定")

    # データ処理実行ボタン
    if st.sidebar.button("データ処理実行 (data_processor.py)"):
        with st.spinner('データ処理を実行中です...'):
            run_data_processing()
        st.success("データ処理が完了しました。ページを再読み込みして最新情報を表示してください。")
        # 自動リロードや状態管理の高度化も検討可能

    # 固定時間帯リストをselectboxの選択肢用にフォーマット
    time_window_options = [f"{s:02}-{e:02}_JST" for s, e in FIXED_TIME_WINDOWS_JST_FOR_APP]
    selected_time_window = st.sidebar.selectbox(
        "表示する時間帯を選択:", 
        options=time_window_options,
        index=time_window_options.index("07-09_JST") if "07-09_JST" in time_window_options else 0 # デフォルト7-9時
    )
    st.sidebar.markdown("---    ")
    st.sidebar.info(
        "このアプリは、経済指標発表時の価格変動（ボラティリティ）を、\n"
        "指定された固定の時間帯ごとに分析し、過去の統計情報を提供します。"
    )

    # --- メインコンテンツ --- 
    # データのロード
    stats_df = load_latest_statistics()
    today_indicators_df = load_today_indicators()

    if stats_df.empty:
        st.warning("統計データが読み込まれていません。先にデータ処理を実行するか、CSVファイルを確認してください。")
        return
    
    if today_indicators_df.empty:
        st.info("本日の指標データはありません。統計サマリーのみ表示します。")

    st.header("当日指標と関連ボラティリティ統計")
    if not today_indicators_df.empty:
        # 選択された時間帯で統計データをフィルタリング
        filtered_stats_for_merge = stats_df[stats_df['TimeWindow_Slot'] == selected_time_window]
        
        # 当日指標とフィルターされた統計をマージ
        merged_today_df = merge_indicators_with_statistics(today_indicators_df, filtered_stats_for_merge)
        
        if not merged_today_df.empty:
            # 表示用に整形
            display_today_table = format_display_table(merged_today_df, selected_time_window)
            if not display_today_table.empty:
                st.subheader(f"時間帯: {selected_time_window} のボラティリティ情報")
                display_data_table(display_today_table)
            else:
                st.info(f"当日の指標 ({selected_time_window}) に関連する統計情報はありません。")
        else:
            st.info(f"当日の指標と {selected_time_window} の統計情報を紐付けられませんでした。")
    else:
        st.info("当日の経済指標はありません。")

    # 統計サマリー表示 (選択された時間帯スロットを渡す)
    display_statistics_summary(stats_df.copy(), selected_time_window)

if __name__ == '__main__':
    main() 