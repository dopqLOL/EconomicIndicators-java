#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
非対称イベント分析モジュール

このモジュールは、経済指標発表前後の非対称な時間枠でのボラティリティ分析を
行うための機能を提供します。発表前の市場予測の影響と発表後の実際の反応を
区別して分析し、複数の時間スケールでのボラティリティを計算します。

主な機能:
- 指標発表前の固定時間枠（デフォルト5分間）での分析
- 指標発表後の複数時間枠（デフォルト5分、15分、30分）での分析
- 発表前後の変動比率の計算
- 時間枠ごとの統計量計算
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

# ロガーの設定
logger = logging.getLogger(__name__)

class AsymmetricAnalyzer:
    """
    指標発表前後の非対称時間枠でボラティリティ分析を行うクラス
    """
    
    def __init__(self, 
                 pre_window: int = 5, 
                 post_windows: List[int] = None):
        """
        初期化
        
        Args:
            pre_window: 発表前の分析時間（分）
            post_windows: 発表後の分析時間枠のリスト（分）。デフォルトは[5, 15, 30]
        """
        self.pre_window = pre_window
        self.post_windows = post_windows if post_windows else [5, 15, 30]
        logger.info(f"AsymmetricAnalyzer initialized with pre_window={pre_window}, "
                   f"post_windows={self.post_windows}")
    
    def analyze_pre_event(self, 
                          indicator_row: pd.Series, 
                          zigzag_df: pd.DataFrame) -> Dict[str, Any]:
        """
        指標発表前の分析を行う
        
        Args:
            indicator_row: 分析対象の経済指標行（Series）
            zigzag_df: ZigZagデータのDataFrame
            
        Returns:
            dict: 発表前分析の結果
        """
        try:
            # 指標発表時刻を取得
            if 'DateTime_UTC' in indicator_row:
                event_time = pd.to_datetime(indicator_row['DateTime_UTC'])
            else:
                # 代替カラム名を確認
                datetime_cols = [col for col in indicator_row.index if 'datetime' in col.lower() or 'time' in col.lower()]
                if datetime_cols:
                    event_time = pd.to_datetime(indicator_row[datetime_cols[0]])
                else:
                    logger.error(f"No datetime column found in indicator row: {indicator_row.index.tolist()}")
                    return {'pre_event_valid': False, 'error': 'No datetime column found'}
            
            # 発表前の時間ウィンドウを設定
            pre_start = event_time - pd.Timedelta(minutes=self.pre_window)
            
            # 該当期間のZigZagデータを抽出
            pre_data = extract_zigzag_window(zigzag_df, pre_start, event_time)
            
            # データが2ポイント以上ない場合は有効な結果が計算できない
            if len(pre_data) < 2:
                logger.warning(f"Insufficient zigzag data points for pre-event analysis at {event_time}")
                return {
                    'pre_event_valid': False,
                    'pre_event_points': len(pre_data),
                    'pre_window_minutes': self.pre_window
                }
            
            # 価格変動を計算
            movement_results = calculate_price_movement(pre_data)
            
            # 変動速度を計算
            speed_results = calculate_movement_speed(pre_data)
            
            # 結果を統合
            results = {
                'pre_event_valid': True,
                'pre_window_minutes': self.pre_window,
                'pre_event_points': len(pre_data),
                'pre_event_legs': len(pre_data) - 1  # ZigZagレッグ数
            }
            results.update(movement_results)
            results.update(speed_results)
            
            # 発表直前1分間の特別分析（可能な場合）
            last_minute_start = event_time - pd.Timedelta(minutes=1)
            last_minute_data = extract_zigzag_window(zigzag_df, last_minute_start, event_time)
            if len(last_minute_data) >= 2:
                last_min_movement = calculate_price_movement(last_minute_data)
                # キー名を変更して追加
                results['pre_event_last_min_movement'] = last_min_movement.get('price_movement', 0)
                results['pre_event_last_min_direction'] = last_min_movement.get('movement_direction', 'neutral')
            
            return results
            
        except Exception as e:
            logger.error(f"Error in pre-event analysis: {e}")
            return {'pre_event_valid': False, 'error': str(e)}
    
    def analyze_post_event(self, 
                           indicator_row: pd.Series, 
                           zigzag_df: pd.DataFrame) -> Dict[str, Any]:
        """
        指標発表後の複数時間枠での分析を行う
        
        Args:
            indicator_row: 分析対象の経済指標行（Series）
            zigzag_df: ZigZagデータのDataFrame
            
        Returns:
            dict: 発表後分析の結果（時間枠ごと）
        """
        try:
            # 指標発表時刻を取得
            if 'DateTime_UTC' in indicator_row:
                event_time = pd.to_datetime(indicator_row['DateTime_UTC'])
            else:
                # 代替カラム名を確認
                datetime_cols = [col for col in indicator_row.index if 'datetime' in col.lower() or 'time' in col.lower()]
                if datetime_cols:
                    event_time = pd.to_datetime(indicator_row[datetime_cols[0]])
                else:
                    logger.error(f"No datetime column found in indicator row: {indicator_row.index.tolist()}")
                    return {'post_event_valid': False, 'error': 'No datetime column found'}
            
            results = {'post_event_valid': True}
            
            # 各時間枠での分析
            for minutes in self.post_windows:
                # 発表後の時間ウィンドウを設定
                post_end = event_time + pd.Timedelta(minutes=minutes)
                
                # 該当期間のZigZagデータを抽出
                post_data = extract_zigzag_window(zigzag_df, event_time, post_end)
                
                # 時間枠ごとの結果用辞書
                window_key = f'post_{minutes}min'
                
                # データが2ポイント以上ない場合は有効な結果が計算できない
                if len(post_data) < 2:
                    results[f'{window_key}_valid'] = False
                    results[f'{window_key}_points'] = len(post_data)
                    continue
                
                # 価格変動を計算
                movement_results = calculate_price_movement(post_data)
                
                # 変動速度を計算
                speed_results = calculate_movement_speed(post_data)
                
                # 結果を統合（キー名に時間枠を追加）
                results[f'{window_key}_valid'] = True
                results[f'{window_key}_points'] = len(post_data)
                results[f'{window_key}_legs'] = len(post_data) - 1  # ZigZagレッグ数
                
                for k, v in movement_results.items():
                    results[f'{window_key}_{k}'] = v
                
                for k, v in speed_results.items():
                    results[f'{window_key}_{k}'] = v
            
            return results
            
        except Exception as e:
            logger.error(f"Error in post-event analysis: {e}")
            return {'post_event_valid': False, 'error': str(e)}
    
    def calculate_ratios(self, 
                         pre_results: Dict[str, Any], 
                         post_results: Dict[str, Any]) -> Dict[str, float]:
        """
        発表前後の比率計算を行う
        
        Args:
            pre_results: 発表前分析結果
            post_results: 発表後分析結果
            
        Returns:
            dict: 各種比率の計算結果
        """
        ratios = {}
        
        # 発表前の結果が有効であることを確認
        if not pre_results.get('pre_event_valid', False):
            return {'ratios_valid': False, 'error': 'Invalid pre-event results'}
        
        # 発表後の結果が有効であることを確認
        if not post_results.get('post_event_valid', False):
            return {'ratios_valid': False, 'error': 'Invalid post-event results'}
        
        # 発表前の価格変動
        pre_movement = pre_results.get('price_movement', 0)
        
        # ゼロ除算を防止
        if pre_movement == 0:
            return {
                'ratios_valid': False, 
                'error': 'Pre-event movement is zero, cannot calculate ratios'
            }
        
        # 各時間枠での比率計算
        for minutes in self.post_windows:
            window_key = f'post_{minutes}min'
            
            # 時間枠の結果が有効であることを確認
            if not post_results.get(f'{window_key}_valid', False):
                continue
            
            # 発表後の価格変動
            post_movement = post_results.get(f'{window_key}_price_movement', 0)
            
            # 比率計算
            ratio = post_movement / pre_movement if pre_movement > 0 else float('inf')
            ratios[f'ratio_{minutes}min'] = ratio
            
            # 対数比率（比率の大きさを正規化）
            if ratio > 0:
                log_ratio = np.log(ratio)
                ratios[f'log_ratio_{minutes}min'] = log_ratio
        
        # 方向一致性の計算（発表前後で価格方向が一致しているか）
        pre_direction = pre_results.get('movement_direction', 'neutral')
        
        for minutes in self.post_windows:
            window_key = f'post_{minutes}min'
            post_direction = post_results.get(f'{window_key}_movement_direction', 'neutral')
            
            # 方向一致性（1: 一致、0: 不一致、0.5: どちらかがneutral）
            if pre_direction == 'neutral' or post_direction == 'neutral':
                direction_consistency = 0.5
            elif pre_direction == post_direction:
                direction_consistency = 1.0
            else:
                direction_consistency = 0.0
            
            ratios[f'direction_consistency_{minutes}min'] = direction_consistency
        
        ratios['ratios_valid'] = True
        return ratios
    
    def analyze_indicator(self, 
                          indicator_row: pd.Series, 
                          zigzag_df: pd.DataFrame) -> Dict[str, Any]:
        """
        指標に対する完全な分析（発表前、発表後、比率計算）を実行
        
        Args:
            indicator_row: 分析対象の経済指標行（Series）
            zigzag_df: ZigZagデータのDataFrame
            
        Returns:
            dict: 統合された分析結果
        """
        # 発表前分析
        pre_results = self.analyze_pre_event(indicator_row, zigzag_df)
        
        # 発表後分析
        post_results = self.analyze_post_event(indicator_row, zigzag_df)
        
        # 結果を統合
        combined_results = {}
        combined_results.update(pre_results)
        combined_results.update(post_results)
        
        # 両方の分析が有効な場合は比率も計算
        if pre_results.get('pre_event_valid', False) and post_results.get('post_event_valid', False):
            ratio_results = self.calculate_ratios(pre_results, post_results)
            combined_results.update(ratio_results)
        
        # 指標情報を追加
        for key, value in indicator_row.items():
            if key not in combined_results:  # 重複を避ける
                combined_results[key] = value
        
        return combined_results


def extract_zigzag_window(zigzag_df: pd.DataFrame, 
                         start_time: pd.Timestamp, 
                         end_time: pd.Timestamp) -> pd.DataFrame:
    """
    指定された時間ウィンドウ内のZigZagデータを抽出する
    
    Args:
        zigzag_df: ZigZagデータのDataFrame
        start_time: 開始時刻
        end_time: 終了時刻
        
    Returns:
        DataFrame: 抽出されたZigZagデータ
    """
    try:
        # 時間列の特定
        time_cols = [col for col in zigzag_df.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if not time_cols:
            logger.error("No time column found in zigzag dataframe")
            return pd.DataFrame()
        
        time_col = time_cols[0]
        
        # 時間列がdatetimeタイプでない場合は変換
        if not pd.api.types.is_datetime64_any_dtype(zigzag_df[time_col]):
            zigzag_df[time_col] = pd.to_datetime(zigzag_df[time_col])
        
        # 時間ウィンドウ内のデータを抽出
        window_data = zigzag_df[(zigzag_df[time_col] >= start_time) & 
                               (zigzag_df[time_col] <= end_time)].copy()
        
        return window_data
    
    except Exception as e:
        logger.error(f"Error extracting zigzag window: {e}")
        return pd.DataFrame()


def calculate_price_movement(zigzag_window: pd.DataFrame) -> Dict[str, Any]:
    """
    ZigZagウィンドウデータから価格変動を計算する
    
    Args:
        zigzag_window: 時間ウィンドウ内のZigZagデータ
        
    Returns:
        dict: 価格変動に関する各種指標
    """
    if len(zigzag_window) < 2:
        return {
            'price_movement': 0,
            'max_price': None,
            'min_price': None,
            'start_price': None,
            'end_price': None,
            'movement_direction': 'neutral'
        }
    
    try:
        # 価格列の特定
        price_cols = [col for col in zigzag_window.columns if 'price' in col.lower()]
        
        if not price_cols:
            logger.error("No price column found in zigzag dataframe")
            return {
                'price_movement': 0,
                'error': 'No price column found'
            }
        
        price_col = price_cols[0]
        
        # 最大値と最小値の取得
        max_price = zigzag_window[price_col].max()
        min_price = zigzag_window[price_col].min()
        
        # 価格変動（高値 - 安値）
        price_movement = max_price - min_price
        
        # 開始価格と終了価格の取得
        time_cols = [col for col in zigzag_window.columns if 'time' in col.lower() or 'date' in col.lower()]
        time_col = time_cols[0] if time_cols else None
        
        if time_col:
            # 時間でソートして最初と最後の価格を取得
            sorted_data = zigzag_window.sort_values(by=time_col)
            start_price = sorted_data[price_col].iloc[0]
            end_price = sorted_data[price_col].iloc[-1]
            
            # 方向性の判定（上昇/下降/中立）
            if end_price > start_price:
                movement_direction = 'up'
            elif end_price < start_price:
                movement_direction = 'down'
            else:
                movement_direction = 'neutral'
        else:
            # 時間列がない場合はソートなしで最初と最後を使用
            start_price = zigzag_window[price_col].iloc[0]
            end_price = zigzag_window[price_col].iloc[-1]
            
            # 方向性の判定
            if end_price > start_price:
                movement_direction = 'up'
            elif end_price < start_price:
                movement_direction = 'down'
            else:
                movement_direction = 'neutral'
        
        return {
            'price_movement': price_movement,
            'max_price': max_price,
            'min_price': min_price,
            'start_price': start_price,
            'end_price': end_price,
            'movement_direction': movement_direction,
            'net_movement': end_price - start_price,
            'movement_efficiency': abs(end_price - start_price) / price_movement if price_movement > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Error calculating price movement: {e}")
        return {'price_movement': 0, 'error': str(e)}


def calculate_movement_speed(zigzag_window: pd.DataFrame) -> Dict[str, float]:
    """
    価格変動の速度を計算する
    
    Args:
        zigzag_window: 時間ウィンドウ内のZigZagデータ
        
    Returns:
        dict: 価格変動速度に関する指標
    """
    if len(zigzag_window) < 2:
        return {'movement_speed': 0}
    
    try:
        # 価格列と時間列の特定
        price_cols = [col for col in zigzag_window.columns if 'price' in col.lower()]
        time_cols = [col for col in zigzag_window.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if not price_cols or not time_cols:
            logger.error("Missing price or time columns in zigzag dataframe")
            return {'movement_speed': 0, 'error': 'Missing required columns'}
        
        price_col = price_cols[0]
        time_col = time_cols[0]
        
        # 時間でソートしてデータ準備
        sorted_data = zigzag_window.sort_values(by=time_col)
        
        # 最初と最後の時刻と価格
        start_time = sorted_data[time_col].iloc[0]
        end_time = sorted_data[time_col].iloc[-1]
        
        # 時間差（分）を計算
        if isinstance(start_time, (pd.Timestamp, datetime)):
            time_diff_minutes = (end_time - start_time).total_seconds() / 60
        else:
            # 時間列が別の形式の場合
            start_time = pd.to_datetime(start_time)
            end_time = pd.to_datetime(end_time)
            time_diff_minutes = (end_time - start_time).total_seconds() / 60
        
        # ゼロ除算を防止
        if time_diff_minutes == 0:
            return {'movement_speed': 0, 'error': 'Zero time difference'}
        
        # 価格変動の取得
        movement_results = calculate_price_movement(sorted_data)
        price_movement = movement_results.get('price_movement', 0)
        
        # 速度計算（単位時間あたりの価格変動）
        movement_speed = price_movement / time_diff_minutes
        
        # ZigZagレッグの頻度（単位時間あたりのレッグ数）
        leg_frequency = (len(sorted_data) - 1) / time_diff_minutes if time_diff_minutes > 0 else 0
        
        return {
            'movement_speed': movement_speed,
            'time_diff_minutes': time_diff_minutes,
            'leg_frequency': leg_frequency
        }
    
    except Exception as e:
        logger.error(f"Error calculating movement speed: {e}")
        return {'movement_speed': 0, 'error': str(e)}


def batch_process_indicators(indicators_df: pd.DataFrame, 
                            zigzag_df: pd.DataFrame, 
                            analyzer: AsymmetricAnalyzer = None) -> pd.DataFrame:
    """
    複数の経済指標に対して一括で分析を実行する
    
    Args:
        indicators_df: 経済指標のDataFrame
        zigzag_df: ZigZagデータのDataFrame
        analyzer: AsymmetricAnalyzerインスタンス。Noneの場合は新規作成
        
    Returns:
        DataFrame: 分析結果
    """
    if analyzer is None:
        analyzer = AsymmetricAnalyzer()
    
    results = []
    total_indicators = len(indicators_df)
    
    logger.info(f"Starting batch processing of {total_indicators} indicators")
    
    for idx, (_, indicator_row) in enumerate(indicators_df.iterrows()):
        if idx % 100 == 0:
            logger.info(f"Processing indicator {idx+1}/{total_indicators}")
        
        # 指標の分析を実行
        analysis_result = analyzer.analyze_indicator(indicator_row, zigzag_df)
        results.append(analysis_result)
    
    logger.info(f"Completed batch processing of {total_indicators} indicators")
    
    # 結果をDataFrameに変換
    results_df = pd.DataFrame(results)
    
    return results_df


if __name__ == "__main__":
    # モジュール単体テスト用コード
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("AsymmetricAnalyzer module loaded successfully")
    print("Run unit tests or import this module to use its functionality") 