#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
データ処理モジュール

このモジュールは、ZigZagデータと経済指標データを処理し、時間帯ボラティリティを
計算するための機能を提供します。具体的には、指定された時間帯（例：日本時間の午前7時から
午前9時まで）のZigZagデータから高値と安値を特定し、その差（時間帯ボラティリティ）を
算出します。

主な機能:
- ZigZagデータの読み込みと結合
- 経済指標データの読み込みと前処理
- 時間帯ボラティリティの計算
- 経済指標と時間帯ボラティリティの紐付け
- 統計情報の計算（3分類平均値、中央値）
- 地合い判断機能
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path

# ロガーの設定
logger = logging.getLogger(__name__)

# 定数定義
ZIGZAG_FILES = [
    "mt5_zigzag_legs_20230501_20250431.csv",
    "mt5_zigzag_legs_20210501_20230431.csv",
    "mt5_zigzag_legs_20190501_20210431.csv"
]
INDICATOR_FILE = "EconomicIndicators_20190501-20250518.csv"
SPECIAL_VALUE = -9223372036854775808.00000000  # 「データなし」を表す特殊値

# デバッグフラグ（Trueにすると処理対象のZigZagファイルを1つにし、期間も限定する）
DEBUG_MODE = False

class DataProcessor:
    """
    データ処理を行うクラス
    """
    
    # 日本時間の固定時間帯 (開始時, 終了時(含まない))
    FIXED_TIME_WINDOWS_JST = [
        (0, 3), (3, 6), (7, 9), (9, 12), (12, 15), (15, 21), (21, 24)
    ]
    
    def __init__(self, 
                 zigzag_dir: str = "../csv/Zigzag-data",
                 indicators_dir: str = "../csv/EconomicIndicators",
                 output_dir: str = "../csv/Statistics",
                 time_window_start: int = 7,  # 日本時間 午前7時
                 time_window_end: int = 9):   # 日本時間 午前9時
        """
        初期化
        
        Args:
            zigzag_dir: ZigZagデータディレクトリ
            indicators_dir: 経済指標データディレクトリ
            output_dir: 出力ディレクトリ
            time_window_start: 時間帯開始時刻（時）
            time_window_end: 時間帯終了時刻（時）
        """
        self.zigzag_dir = Path(zigzag_dir)
        self.indicators_dir = Path(indicators_dir)
        self.output_dir = Path(output_dir)
        self.time_window_start = time_window_start
        self.time_window_end = time_window_end
        
        # データフレーム
        self.zigzag_df = None
        self.indicators_df = None
        self.volatility_df = None
        self.statistics_df = None
        
        # 出力ディレクトリの確認
        self._ensure_directory(self.output_dir)
        
        logger.info(f"DataProcessor initialized. Output directory: {self.output_dir}")
    
    def _ensure_directory(self, directory_path: Path) -> None:
        """
        ディレクトリが存在することを確認し、必要に応じて作成する
        
        Args:
            directory_path: 確認/作成するディレクトリのパス
        """
        if not directory_path.exists():
            logger.info(f"Creating directory: {directory_path}")
            directory_path.mkdir(parents=True, exist_ok=True)
    
    def load_zigzag_data(self) -> pd.DataFrame:
        """
        ZigZagデータを読み込む
        
        Returns:
            DataFrame: 結合されたZigZagデータ
        """
        logger.info("Loading ZigZag data...")
        df_list = []
        
        files_to_load = ZIGZAG_FILES
        if DEBUG_MODE:
            logger.warning("DEBUG_MODE is True. Loading only the first ZigZag file and a limited date range.")
            files_to_load = ZIGZAG_FILES[:1] # 最初のファイルのみ

        for filename in files_to_load:
            file_path = self.zigzag_dir / filename
            if not file_path.exists():
                logger.warning(f"ZigZag file not found: {file_path}")
                continue
            
            try:
                # タブ区切りCSVファイルを読み込む
                df = pd.read_csv(file_path, sep='\t')
                logger.info(f"Loaded {len(df)} records from {filename}")
                df_list.append(df)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        if not df_list:
            logger.error("No ZigZag data could be loaded")
            return pd.DataFrame()
        
        # 全データを結合
        self.zigzag_df = pd.concat(df_list, ignore_index=True)
        
        # 時間列を変換
        if 'start_time_utc_seconds' in self.zigzag_df.columns:
            self.zigzag_df['start_time_dt'] = pd.to_datetime(self.zigzag_df['start_time_utc_seconds'], unit='s')
            # JSTに変換（UTC+9）
            self.zigzag_df['start_time_jst'] = self.zigzag_df['start_time_dt'] + pd.Timedelta(hours=9)
        
        if 'end_time_utc_seconds' in self.zigzag_df.columns:
            self.zigzag_df['end_time_dt'] = pd.to_datetime(self.zigzag_df['end_time_utc_seconds'], unit='s')
            # JSTに変換（UTC+9）
            self.zigzag_df['end_time_jst'] = self.zigzag_df['end_time_dt'] + pd.Timedelta(hours=9)
        
        if DEBUG_MODE and not self.zigzag_df.empty:
            # デバッグ用に期間を限定 (例: 2023年5月のデータのみ)
            # self.zigzag_df = self.zigzag_df[
            #     (self.zigzag_df['start_time_jst'] >= pd.Timestamp('2023-05-01')) &
            #     (self.zigzag_df['start_time_jst'] < pd.Timestamp('2023-06-01'))
            # ]
            # より短い期間でテストするため、直近の数日に絞る (データが存在すれば)
            if not self.zigzag_df.empty:
                # start_time_jst でソートし、最新の日付から数日分を取得
                self.zigzag_df = self.zigzag_df.sort_values(by='start_time_jst', ascending=False)
                if len(self.zigzag_df) > 1000: # あまりにも多い場合は少し絞る
                     # 適切な日付範囲でフィルタリング (例: 最新日から3日間)
                     latest_date = self.zigzag_df['start_time_jst'].max().normalize()
                     start_filter_date = latest_date - pd.Timedelta(days=365) # 約1年間に変更
                     self.zigzag_df = self.zigzag_df[
                         self.zigzag_df['start_time_jst'] >= start_filter_date
                     ]
                logger.info(f"DEBUG_MODE: Filtered ZigZag data to {len(self.zigzag_df)} records for recent period (approx. 1 year).")

        logger.info(f"Combined ZigZag data: {len(self.zigzag_df)} records")
        return self.zigzag_df
    
    def _calculate_daily_fixed_window_volatility(self) -> pd.DataFrame:
        """
        日次の固定時間帯ボラティリティを計算する
        
        Returns:
            pd.DataFrame: 日付ごとの各固定時間帯ボラティリティ
                          カラム例: Date, Volatility_00_03_JST, Volatility_03_06_JST, ...
        """
        if self.zigzag_df is None or 'start_time_jst' not in self.zigzag_df.columns or 'start_price' not in self.zigzag_df.columns:
            logger.error("ZigZag data is not loaded properly or missing required columns (start_time_jst, start_price).")
            return pd.DataFrame()

        logger.info("Calculating daily fixed window volatility...")
        
        # 'start_time_jst' を datetime 型に変換 (もし未変換の場合)
        if not pd.api.types.is_datetime64_any_dtype(self.zigzag_df['start_time_jst']):
            self.zigzag_df['start_time_jst'] = pd.to_datetime(self.zigzag_df['start_time_jst'])

        # 日付カラムを作成
        self.zigzag_df['date_jst'] = self.zigzag_df['start_time_jst'].dt.date
        
        all_dates = self.zigzag_df['date_jst'].unique()
        if len(all_dates) == 0:
            logger.warning("No unique dates found in ZigZag data after filtering (if any). Cannot calculate daily volatility.")
            return pd.DataFrame()
            
        results = []

        for date_val in all_dates:
            daily_data_row = {'Date': date_val}
            for start_hour, end_hour in self.FIXED_TIME_WINDOWS_JST:
                window_start_dt = datetime.combine(date_val, datetime.min.time()) + timedelta(hours=start_hour)
                window_end_dt = datetime.combine(date_val, datetime.min.time()) + timedelta(hours=end_hour)
                
                mask = (
                    (self.zigzag_df['start_time_jst'] >= window_start_dt) &
                    (self.zigzag_df['start_time_jst'] < window_end_dt) &
                    (self.zigzag_df['date_jst'] == date_val)
                )
                window_data = self.zigzag_df.loc[mask]
                
                col_name = f'Volatility_{start_hour:02}_{end_hour:02}_JST'
                # 'price' カラムは存在しないので、'start_price' を使用する (または 'end_price')
                # ZigZagデータ構造を考慮すると、期間内の全ての start_price と end_price を集めて高値・安値を出すのがより正確だが、
                # ここでは簡単のため、start_price のみを見る。
                if not window_data.empty and 'start_price' in window_data.columns:
                    if len(window_data) >= 1: # 1点でもあれば、その点がその期間の高値かつ安値となる (ボラティリティは0)
                                              # 厳密には2点以上でボラティリティを計算するのが一般的
                        # 期間内の全ての start_price と end_price を考慮するなら以下のようにする
                        # prices_in_window = pd.concat([window_data['start_price'], window_data['end_price']]).dropna()
                        # if len(prices_in_window) >= 1:
                        #    high_price = prices_in_window.max()
                        #    low_price = prices_in_window.min()
                        #    daily_data_row[col_name] = high_price - low_price
                        # else:
                        #    daily_data_row[col_name] = np.nan
                        
                        # 今回は start_price のみで計算
                        high_price = window_data['start_price'].max()
                        low_price = window_data['start_price'].min()
                        daily_data_row[col_name] = high_price - low_price
                        
                        if len(window_data) < 2:
                            logger.debug(f"Only one data point in window {date_val} {start_hour}-{end_hour}. Volatility will be 0 or based on single price.")
                    else: # 通常はここには来ないはず (emptyでない かつ len < 1)
                        daily_data_row[col_name] = np.nan
                else:
                    if window_data.empty:
                        logger.debug(f"No ZigZag data in window {date_val} {start_hour:02d}-{end_hour:02d}.")
                    elif 'start_price' not in window_data.columns:
                        logger.warning(f"'start_price' column not found in window_data for {date_val} {start_hour:02d}-{end_hour:02d}.")
                    daily_data_row[col_name] = np.nan
            results.append(daily_data_row)
            
        daily_volatility_df = pd.DataFrame(results)
        if not daily_volatility_df.empty:
             daily_volatility_df['Date'] = pd.to_datetime(daily_volatility_df['Date'])

        logger.info(f"Calculated daily fixed window volatility for {len(daily_volatility_df)} days.")
        return daily_volatility_df

    def _merge_volatility_with_indicators(self, daily_volatility_df: pd.DataFrame) -> pd.DataFrame:
        """
        日次ボラティリティデータと経済指標データをマージする
        
        Args:
            daily_volatility_df: _calculate_daily_fixed_window_volatility からの出力
            
        Returns:
            pd.DataFrame: 経済指標に日次ボラティリティが付加されたデータ
        """
        if self.indicators_df is None or daily_volatility_df is None or daily_volatility_df.empty:
            logger.error("Indicator data or daily volatility data is not available for merging.")
            return pd.DataFrame()
        
        if 'DateTime_JST' not in self.indicators_df.columns:
            logger.error("Indicators DataFrame a 'DateTime_JST' column for merging.")
            return pd.DataFrame()
            
        logger.info("Merging daily volatility with indicators...")
        
        # 指標データの 'DateTime_JST' から日付部分を抽出してマージキーとする
        # 既に pd.Timestamp 型であることを想定
        try:
            indicators_copy = self.indicators_df.copy()
            indicators_copy['Merge_Date'] = indicators_copy['DateTime_JST'].dt.normalize() 
            daily_volatility_df_copy = daily_volatility_df.copy()
            daily_volatility_df_copy['Merge_Date'] = daily_volatility_df_copy['Date'].dt.normalize()

            # 'Date' カラムが daily_volatility_df_copy に存在することを確認
            if 'Date' not in daily_volatility_df_copy.columns:
                 logger.error("Daily volatility DataFrame must have a 'Date' column for merging.")
                 return pd.DataFrame()


            merged_df = pd.merge(
                indicators_copy,
                daily_volatility_df_copy.drop(columns=['Date']), # daily_volatility_df_copyのDateはMerge_Dateと同じなので削除
                on='Merge_Date',
                how='left'
            )
            merged_df.drop(columns=['Merge_Date'], inplace=True)

        except Exception as e:
            logger.error(f"Error during merging volatility with indicators: {e}")
            return pd.DataFrame()
            
        logger.info(f"Merged volatility data for {len(merged_df)} indicator events.")
        return merged_df

    def load_indicator_data(self) -> pd.DataFrame:
        """
        経済指標データを読み込む
        
        Returns:
            DataFrame: 前処理済みの経済指標データ
        """
        logger.info("Loading economic indicator data...")
        file_path = self.indicators_dir / INDICATOR_FILE
        
        if not file_path.exists():
            logger.error(f"Indicator file not found: {file_path}")
            return pd.DataFrame()
        
        try:
            # エンコーディングの問題に対応するためにいくつかのエンコーディングを試す
            encodings = ['utf-8', 'cp932', 'shift-jis', 'latin1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Successfully loaded indicators with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    logger.warning(f"Failed to load with encoding: {encoding}")
                    continue
            
            if df is None:
                logger.error("Failed to load indicator data with any encoding")
                return pd.DataFrame()
            
            # 特殊値を処理
            for col in df.columns:
                if df[col].dtype == 'float64' or df[col].dtype == 'int64':
                    df[col] = df[col].replace(SPECIAL_VALUE, np.nan)
            
            # 日時列を処理
            if 'DateTime (UTC)' in df.columns:
                df['DateTime_UTC'] = pd.to_datetime(df['DateTime (UTC)'], format='%Y.%m.%d %H:%M:%S')
                # JSTに変換（UTC+9）
                df['DateTime_JST'] = df['DateTime_UTC'] + pd.Timedelta(hours=9)
            
            self.indicators_df = df
            logger.info(f"Loaded {len(df)} indicator records")
            return self.indicators_df
            
        except Exception as e:
            logger.error(f"Error loading indicator data: {e}")
            return pd.DataFrame()
    
    def calculate_statistics(self) -> pd.DataFrame:
        """
        指標ごと、かつ固定時間帯ごとに統計情報を計算する
        
        Returns:
            DataFrame: 指標ごと、時間帯ごとの統計情報
        """
        if self.volatility_df is None or self.volatility_df.empty:
            logger.error("Volatility data (merged with indicators) not available for statistics calculation.")
            return pd.DataFrame()

        logger.info("Calculating indicator statistics for fixed time windows...")
        
        stats_list = []
        # 'Currency', 'EventName' でグループ化
        grouped_by_indicator = self.volatility_df.groupby(['Currency', 'EventName'])
        
        for (currency, event_name), group in grouped_by_indicator:
            for start_hour, end_hour in self.FIXED_TIME_WINDOWS_JST:
                vol_col_name = f'Volatility_{start_hour:02}_{end_hour:02}_JST'
                time_window_slot = f'{start_hour:02}-{end_hour:02}_JST'
                
                if vol_col_name not in group.columns:
                    logger.warning(f"Column {vol_col_name} not found for {currency} - {event_name}. Skipping statistics for this slot.")
                    continue

                valid_data = group.dropna(subset=[vol_col_name])
                
                if len(valid_data) < 2:  # 最低2件のデータが必要
                    # 統計計算には不十分だが、情報は残す場合もあるので一旦ログのみ
                    logger.debug(f"Insufficient data (<2) for {currency} - {event_name} in slot {time_window_slot} for full stats. Count: {len(valid_data)}")
                    # ここで NaN で統計情報を埋めるか、この時間帯スロットのレコード自体をスキップするかは要件による
                    # 今回は平均・中央値などを NaN としてレコードは作成する方針で進めてみる
                    mean_val, median_val, std_val, min_val, max_val, count_val = [np.nan] * 6
                    if len(valid_data) == 1:
                        # データが1件の場合は、その値をmin/max/mean/medianとして記録することも可能
                        single_value = valid_data[vol_col_name].iloc[0]
                        mean_val, median_val, min_val, max_val = single_value, single_value, single_value, single_value
                        count_val = 1
                        std_val = 0 # データ1点の場合、標準偏差は0
                    else: # 0件の場合
                        count_val = 0

                else:
                    volatility_values = valid_data[vol_col_name]
                    mean_val = volatility_values.mean()
                    median_val = volatility_values.median()
                    std_val = volatility_values.std()
                    min_val = volatility_values.min()
                    max_val = volatility_values.max()
                    count_val = len(valid_data)
                
                # 3分類のしきい値や平均は、各時間帯スロットごとに計算する必要がある
                # ただし、この機能が新しいコンテキストでも必要かは要確認。一旦基本的な統計量に絞る。
                # q1 = volatility_values.quantile(0.33) if count_val >= 2 else np.nan
                # q2 = volatility_values.quantile(0.67) if count_val >= 2 else np.nan
                # small_mean, medium_mean, large_mean = np.nan, np.nan, np.nan
                # market_condition = "N/A"
                # deviation_ratio = np.nan
                # recent_1, recent_2 = np.nan, np.nan

                # if count_val >=2:
                #     recent_data = valid_data.sort_values('DateTime_JST', ascending=False).head(2)
                #     recent_values = recent_data[vol_col_name].tolist()
                #     recent_1 = recent_values[0] if len(recent_values) > 0 else np.nan
                #     recent_2 = recent_values[1] if len(recent_values) > 1 else np.nan
                
                stats_list.append({
                    'Currency': currency,
                    'EventName': event_name,
                    'TimeWindow_Slot': time_window_slot,
                    'Volatility_Mean': mean_val,
                    'Volatility_Median': median_val,
                    'Volatility_Std': std_val,
                    'Volatility_Min': min_val,
                    'Volatility_Max': max_val,
                    'Sample_Count': count_val,
                    # 'Small_Class_Mean': small_mean, # 一旦コメントアウト
                    # 'Medium_Class_Mean': medium_mean,
                    # 'Large_Class_Mean': large_mean,
                    # 'Recent_Value_1': recent_1,
                    # 'Recent_Value_2': recent_2,
                    # 'Deviation_Ratio': deviation_ratio,
                    # 'Market_Condition': market_condition
                })
        
        self.statistics_df = pd.DataFrame(stats_list)
        logger.info(f"Calculated statistics for {len(self.statistics_df)} indicator-time_window combinations.")
        return self.statistics_df
    
    def save_results(self) -> Tuple[str, str]:
        """
        結果をCSVファイルに保存する
        (新しいデータ構造に合わせて調整)
        
        Returns:
            Tuple[str, str]: 保存したファイルのパス（ボラティリティデータ、統計データ）
        """
        volatility_path_str = ""
        stats_path_str = ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.volatility_df is not None and not self.volatility_df.empty:
            try:
                volatility_filename = f"indicator_volatility_with_fixed_windows_{timestamp}.csv"
                volatility_path = self.output_dir / volatility_filename
                self.volatility_df.to_csv(volatility_path, index=False)
                logger.info(f"Saved merged volatility data to {volatility_path}")
                volatility_path_str = str(volatility_path)
            except Exception as e:
                logger.error(f"Error saving merged volatility data: {e}")
        else:
            logger.warning("No merged volatility data to save.")

        if self.statistics_df is not None and not self.statistics_df.empty:
            try:
                stats_filename = f"indicator_statistics_for_fixed_windows_{timestamp}.csv"
                stats_path = self.output_dir / stats_filename
                self.statistics_df.to_csv(stats_path, index=False)
                logger.info(f"Saved statistics data to {stats_path}")
                stats_path_str = str(stats_path)
            except Exception as e:
                logger.error(f"Error saving statistics data: {e}")
        else:
            logger.warning("No statistics data to save.")
            
        return (volatility_path_str, stats_path_str)
    
    def process_all(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        全処理を実行する
        
        Returns:
            Tuple[DataFrame, DataFrame]: ボラティリティデータと統計データ
        """
        logger.info("Starting full data processing...")
        
        # ZigZagデータの読み込み
        self.load_zigzag_data()
        if self.zigzag_df is None or self.zigzag_df.empty:
            logger.error("Failed to load ZigZag data or data is empty after filtering.")
            return (pd.DataFrame(), pd.DataFrame())
        
        # 経済指標データの読み込み
        self.load_indicator_data()
        if self.indicators_df is None or self.indicators_df.empty:
            logger.error("Failed to load indicator data or data is empty.")
            return (pd.DataFrame(), pd.DataFrame())
        
        # 日次固定時間帯ボラティリティの計算
        daily_vol_df = self._calculate_daily_fixed_window_volatility()
        if daily_vol_df.empty:
            logger.error("Failed to calculate daily fixed window volatility or no data produced.")
            # 経済指標データがある場合は、ボラティリティ情報なしでそれを返すことも検討できる
            # ここでは一旦空のDataFrameを返す
            return (pd.DataFrame(), pd.DataFrame())

        # ボラティリティデータを指標データにマージ
        self.volatility_df = self._merge_volatility_with_indicators(daily_vol_df)
        if self.volatility_df.empty:
            logger.error("Failed to merge volatility data with indicators or no data produced.")
            # daily_vol_df は計算できている可能性があるので、それを返すことも検討できる
            return (pd.DataFrame(), pd.DataFrame()) # または (daily_vol_df, pd.DataFrame())
        
        # 統計情報の計算 (新しい self.volatility_df を使用)
        self.calculate_statistics() # このメソッドは新しいデータ構造に対応する必要がある
        if self.statistics_df is None or self.statistics_df.empty:
            logger.warning("Failed to calculate statistics or no statistics produced. Returning raw merged volatility.")
            return (self.volatility_df, pd.DataFrame())
        
        # 結果の保存
        self.save_results()
        
        logger.info("Data processing completed successfully")
        return (self.volatility_df, self.statistics_df)


def setup_logging(log_level: str = 'INFO'):
    """
    ロギングの設定を行う
    
    Args:
        log_level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # コンソール出力
            logging.FileHandler(f"data_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")  # ファイル出力
        ]
    )

def main():
    """
    メイン処理
    """
    # ロギングの設定
    setup_logging()
    
    try:
        # データ処理インスタンスの作成
        processor = DataProcessor()
        
        # 全処理の実行
        volatility_df, statistics_df = processor.process_all()
        
        # 結果の表示
        if len(volatility_df) > 0:
            print(f"\nProcessed {len(volatility_df)} indicator records")
            print("\nVolatility Data Sample:")
            print(volatility_df.head())
        
        if len(statistics_df) > 0:
            print("\nStatistics Data Sample:")
            print(statistics_df.head())
            
            # 分類別の統計情報 (Market_Condition は現在未実装のためコメントアウト)
            # print("\nIndicator Count by Market Condition:")
            # print(statistics_df['Market_Condition'].value_counts())
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 