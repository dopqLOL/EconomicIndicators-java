#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
マルチスケール分析モジュール

このモジュールは、経済指標発表前後の価格変動を複数の時間スケールで分析するための
機能を提供します。短期・中期・長期の異なる時間枠での反応パターンを比較し、
時間スケール間の関係性を抽出します。

主な機能:
- 複数時間スケールでのボラティリティ比較
- スケール間の相関分析
- 時間スケール間の波及効果の測定
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from scipy import stats

# ロガーの設定
logger = logging.getLogger(__name__)

class MultiscaleAnalyzer:
    """
    異なる時間スケールでの分析を行うクラス
    """
    
    def __init__(self, 
                 time_scales: List[int] = None,
                 reference_scale: int = 15):
        """
        初期化
        
        Args:
            time_scales: 分析する時間スケール（分）のリスト
            reference_scale: 基準となる時間スケール（分）
        """
        self.time_scales = time_scales if time_scales else [5, 15, 30, 60]
        self.reference_scale = reference_scale
        
        # 基準スケールが分析対象に含まれていることを確認
        if self.reference_scale not in self.time_scales:
            self.time_scales.append(self.reference_scale)
            self.time_scales.sort()
        
        logger.info(f"MultiscaleAnalyzer initialized with time_scales={self.time_scales}, "
                   f"reference_scale={self.reference_scale}")
    
    def calculate_scale_ratios(self, 
                              analyzed_df: pd.DataFrame) -> pd.DataFrame:
        """
        異なる時間スケール間の比率を計算する
        
        Args:
            analyzed_df: AsymmetricAnalyzerで分析されたデータフレーム
            
        Returns:
            DataFrame: スケール比率が追加されたデータフレーム
        """
        try:
            # コピーを作成して変更
            result_df = analyzed_df.copy()
            
            # 基準スケール列の名前を取得
            ref_movement_col = f"post_{self.reference_scale}min_price_movement"
            
            # 基準スケール列が存在するか確認
            if ref_movement_col not in result_df.columns:
                logger.error(f"Reference scale column '{ref_movement_col}' not found in dataframe")
                return analyzed_df
            
            # 各スケールと基準スケールの比率を計算
            for scale in self.time_scales:
                if scale == self.reference_scale:
                    continue
                
                scale_col = f"post_{scale}min_price_movement"
                
                # 対象スケール列が存在するか確認
                if scale_col not in result_df.columns:
                    logger.warning(f"Scale column '{scale_col}' not found, skipping")
                    continue
                
                # 比率を計算（ゼロ除算を防止）
                ratio_col = f"scale_ratio_{scale}_to_{self.reference_scale}"
                result_df[ratio_col] = result_df.apply(
                    lambda row: row[scale_col] / row[ref_movement_col] 
                    if pd.notna(row[scale_col]) and pd.notna(row[ref_movement_col]) and row[ref_movement_col] != 0 
                    else np.nan, 
                    axis=1
                )
                
                # 標準化比率（対数変換で正規化）
                norm_ratio_col = f"norm_scale_ratio_{scale}_to_{self.reference_scale}"
                result_df[norm_ratio_col] = result_df[ratio_col].apply(
                    lambda x: np.log(x) if pd.notna(x) and x > 0 else np.nan
                )
            
            logger.info(f"Scale ratios calculated for {len(result_df)} records")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating scale ratios: {e}")
            return analyzed_df
    
    def calculate_scale_correlations(self, 
                                    analyzed_df: pd.DataFrame) -> pd.DataFrame:
        """
        異なる時間スケール間の相関を計算する
        
        Args:
            analyzed_df: AsymmetricAnalyzerで分析されたデータフレーム
            
        Returns:
            DataFrame: 時間スケール間の相関係数
        """
        try:
            # 各スケールの価格変動列を取得
            movement_cols = [f"post_{scale}min_price_movement" for scale in self.time_scales]
            
            # 存在しない列をフィルタリング
            valid_cols = [col for col in movement_cols if col in analyzed_df.columns]
            
            if len(valid_cols) < 2:
                logger.error("Insufficient valid scale columns for correlation analysis")
                return pd.DataFrame()
            
            # 相関行列を計算
            corr_matrix = analyzed_df[valid_cols].corr(method='pearson')
            
            logger.info(f"Scale correlations calculated with shape {corr_matrix.shape}")
            return corr_matrix
            
        except Exception as e:
            logger.error(f"Error calculating scale correlations: {e}")
            return pd.DataFrame()
    
    def analyze_propagation_effects(self, 
                                   analyzed_df: pd.DataFrame) -> pd.DataFrame:
        """
        時間スケール間の波及効果を分析する
        
        Args:
            analyzed_df: AsymmetricAnalyzerで分析されたデータフレーム
            
        Returns:
            DataFrame: 波及効果分析の結果
        """
        try:
            # 隣接するスケール間の関係を分析
            results = []
            
            for i in range(len(self.time_scales) - 1):
                smaller_scale = self.time_scales[i]
                larger_scale = self.time_scales[i + 1]
                
                smaller_col = f"post_{smaller_scale}min_price_movement"
                larger_col = f"post_{larger_scale}min_price_movement"
                
                # 両方の列が存在するか確認
                if smaller_col not in analyzed_df.columns or larger_col not in analyzed_df.columns:
                    logger.warning(f"Columns {smaller_col} or {larger_col} not found, skipping")
                    continue
                
                # 有効なデータのみを抽出
                valid_data = analyzed_df.dropna(subset=[smaller_col, larger_col])
                
                if len(valid_data) < 5:
                    logger.warning(f"Insufficient valid data for scales {smaller_scale} and {larger_scale}")
                    continue
                
                # 両スケールの相関係数
                correlation, p_value = stats.pearsonr(valid_data[smaller_col], valid_data[larger_col])
                
                # 成長率: 大きいスケール / 小さいスケール
                avg_growth_ratio = np.mean(valid_data[larger_col] / valid_data[smaller_col].replace(0, np.nan))
                
                # 回帰分析: 小さいスケールから大きいスケールを予測
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    valid_data[smaller_col], valid_data[larger_col]
                )
                
                # 結果を保存
                results.append({
                    'smaller_scale': smaller_scale,
                    'larger_scale': larger_scale,
                    'count': len(valid_data),
                    'correlation': correlation,
                    'avg_growth_ratio': avg_growth_ratio,
                    'regression_slope': slope,
                    'regression_intercept': intercept,
                    'regression_r_squared': r_value ** 2,
                    'regression_p_value': p_value,
                    'regression_std_err': std_err
                })
            
            if not results:
                logger.warning("No valid propagation effects could be calculated")
                return pd.DataFrame()
            
            # 結果をDataFrameに変換
            results_df = pd.DataFrame(results)
            
            # 小数点以下の桁数を制限
            float_cols = [col for col in results_df.columns if results_df[col].dtype == 'float64']
            for col in float_cols:
                results_df[col] = results_df[col].round(4)
            
            logger.info(f"Propagation effects analyzed for {len(results_df)} scale pairs")
            return results_df
            
        except Exception as e:
            logger.error(f"Error analyzing propagation effects: {e}")
            return pd.DataFrame()
    
    def analyze_scaling_properties(self, 
                                  analyzed_df: pd.DataFrame) -> pd.DataFrame:
        """
        価格変動のスケーリング特性を分析する
        
        Args:
            analyzed_df: AsymmetricAnalyzerで分析されたデータフレーム
            
        Returns:
            DataFrame: 指標ごとのスケーリング特性
        """
        try:
            # イベント識別用の列
            id_columns = ['Currency', 'EventName']
            if not all(col in analyzed_df.columns for col in id_columns):
                # 代替の識別列を探す
                potential_id_cols = [col for col in analyzed_df.columns if 'currency' in col.lower() or 'event' in col.lower()]
                if len(potential_id_cols) >= 2:
                    id_columns = potential_id_cols[:2]
                else:
                    logger.error("Unable to identify event columns for grouping")
                    return pd.DataFrame()
            
            # 分析結果を格納するためのリスト
            results = []
            
            # 指標ごとにグループ化
            grouped = analyzed_df.groupby(id_columns)
            
            for name, group in grouped:
                if len(group) < 5:
                    # サンプル数が少なすぎる場合はスキップ
                    continue
                
                # 各スケールでの平均価格変動を計算
                scale_movements = {}
                for scale in self.time_scales:
                    col = f"post_{scale}min_price_movement"
                    if col in group.columns:
                        movement = group[col].mean()
                        if pd.notna(movement):
                            scale_movements[scale] = movement
                
                if len(scale_movements) < 3:
                    # 有効なスケールが少なすぎる場合はスキップ
                    continue
                
                # 対数変換したデータで回帰分析を実行
                scales = np.array(list(scale_movements.keys()))
                movements = np.array(list(scale_movements.values()))
                
                # 両対数プロットでの直線の傾きを計算（log(movement) = alpha * log(scale) + c）
                log_scales = np.log(scales)
                log_movements = np.log(movements)
                
                slope, intercept, r_value, p_value, std_err = stats.linregress(log_scales, log_movements)
                
                # 結果を保存
                result = {
                    id_columns[0]: name[0] if isinstance(name, tuple) else name,
                    id_columns[1]: name[1] if isinstance(name, tuple) and len(name) > 1 else '',
                    'count': len(group),
                    'scaling_exponent': slope,
                    'scaling_intercept': intercept,
                    'scaling_r_squared': r_value ** 2,
                    'scaling_p_value': p_value,
                }
                
                # 各スケールでの平均値も追加
                for scale, movement in scale_movements.items():
                    result[f'avg_movement_{scale}min'] = movement
                
                results.append(result)
            
            if not results:
                logger.warning("No valid scaling properties could be calculated")
                return pd.DataFrame()
            
            # 結果をDataFrameに変換
            results_df = pd.DataFrame(results)
            
            # 小数点以下の桁数を制限
            float_cols = [col for col in results_df.columns if results_df[col].dtype == 'float64']
            for col in float_cols:
                results_df[col] = results_df[col].round(4)
            
            logger.info(f"Scaling properties analyzed for {len(results_df)} indicators")
            return results_df
            
        except Exception as e:
            logger.error(f"Error analyzing scaling properties: {e}")
            return pd.DataFrame()
    
    def perform_multiscale_analysis(self, 
                                   analyzed_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        マルチスケール分析の一連の処理を実行する
        
        Args:
            analyzed_df: AsymmetricAnalyzerで分析されたデータフレーム
            
        Returns:
            Dict[str, DataFrame]: 分析結果の辞書
        """
        logger.info(f"Starting multiscale analysis for {len(analyzed_df)} records")
        
        results = {}
        
        # 1. スケール比率の計算
        results['scale_ratios'] = self.calculate_scale_ratios(analyzed_df)
        
        # 2. スケール間の相関分析
        results['scale_correlations'] = self.calculate_scale_correlations(analyzed_df)
        
        # 3. 波及効果の分析
        results['propagation_effects'] = self.analyze_propagation_effects(analyzed_df)
        
        # 4. スケーリング特性の分析
        results['scaling_properties'] = self.analyze_scaling_properties(analyzed_df)
        
        logger.info("Multiscale analysis completed")
        return results


def compare_time_windows(df: pd.DataFrame, 
                        windows: List[int], 
                        metric: str = 'price_movement') -> pd.DataFrame:
    """
    複数の時間ウィンドウでの計測値を比較する
    
    Args:
        df: 分析済みデータフレーム
        windows: 比較する時間ウィンドウ（分）のリスト
        metric: 比較する指標（例: 'price_movement', 'movement_speed'）
        
    Returns:
        DataFrame: 比較結果
    """
    try:
        # 比較結果を格納するためのリスト
        results = []
        
        # 各時間ウィンドウの列名を生成
        columns = [f"post_{window}min_{metric}" for window in windows]
        
        # 列が存在するか確認
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in dataframe: {missing_cols}")
            return pd.DataFrame()
        
        # 基本統計量の計算
        for window, col in zip(windows, columns):
            # 欠損値を除外
            valid_data = df[col].dropna()
            
            if len(valid_data) < 2:
                logger.warning(f"Insufficient data for window {window}")
                continue
            
            # 統計量を計算
            result = {
                'window_minutes': window,
                'mean': valid_data.mean(),
                'median': valid_data.median(),
                'std': valid_data.std(),
                'min': valid_data.min(),
                'max': valid_data.max(),
                'count': len(valid_data)
            }
            
            # 四分位数を計算
            for q in [0.25, 0.75, 0.9]:
                result[f'q{int(q*100)}'] = valid_data.quantile(q)
            
            results.append(result)
        
        if not results:
            logger.warning("No valid comparison results could be calculated")
            return pd.DataFrame()
        
        # 結果をDataFrameに変換
        results_df = pd.DataFrame(results)
        
        # 小数点以下の桁数を制限
        float_cols = [col for col in results_df.columns if results_df[col].dtype == 'float64']
        for col in float_cols:
            results_df[col] = results_df[col].round(4)
        
        logger.info(f"Time window comparison completed for {metric} across {len(windows)} windows")
        return results_df
        
    except Exception as e:
        logger.error(f"Error comparing time windows: {e}")
        return pd.DataFrame()


def analyze_growth_patterns(df: pd.DataFrame, 
                           windows: List[int], 
                           metric: str = 'price_movement',
                           group_by: List[str] = None) -> pd.DataFrame:
    """
    時間経過に伴う指標の成長パターンを分析する
    
    Args:
        df: 分析済みデータフレーム
        windows: 比較する時間ウィンドウ（分）のリスト
        metric: 比較する指標
        group_by: グループ化する列のリスト
        
    Returns:
        DataFrame: 成長パターン分析の結果
    """
    try:
        # グループ化列のデフォルト値
        if group_by is None:
            group_by = ['Currency', 'EventName']
            
            # 指定された列が存在しない場合は代替を探す
            if not all(col in df.columns for col in group_by):
                potential_cols = [col for col in df.columns if 'currency' in col.lower() or 'event' in col.lower()]
                if len(potential_cols) >= 2:
                    group_by = potential_cols[:2]
                else:
                    # グループ化できない場合は全体で分析
                    group_by = []
        
        # 比較する列を生成
        columns = [f"post_{window}min_{metric}" for window in windows]
        
        # 列が存在するか確認
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in dataframe: {missing_cols}")
            return pd.DataFrame()
        
        # グループ化せずに全体のパターンを分析
        if not group_by:
            # 各ウィンドウでの平均値を計算
            mean_values = [df[col].mean() for col in columns]
            
            # 成長率を計算（現在のウィンドウ / 前のウィンドウ）
            growth_rates = [1.0]  # 最初の要素は基準なので1.0
            for i in range(1, len(mean_values)):
                if mean_values[i-1] == 0:
                    growth_rates.append(np.nan)
                else:
                    growth_rates.append(mean_values[i] / mean_values[i-1])
            
            # 結果を作成
            result = pd.DataFrame({
                'window_minutes': windows,
                f'mean_{metric}': mean_values,
                'growth_rate': growth_rates
            })
            
            # 増加率の傾向を分析
            slopes = []
            for i in range(len(windows)):
                if i == 0:
                    slopes.append(np.nan)
                else:
                    # 時間の差分
                    time_diff = windows[i] - windows[i-1]
                    # 値の差分
                    value_diff = mean_values[i] - mean_values[i-1]
                    # 傾き
                    slope = value_diff / time_diff if time_diff > 0 else np.nan
                    slopes.append(slope)
            
            result['slope'] = slopes
            return result
            
        # 指標ごとにグループ化して分析
        results = []
        
        for name, group in df.groupby(group_by):
            if len(group) < 3:
                # サンプル数が少なすぎる場合はスキップ
                continue
            
            # 各ウィンドウでの平均値を計算
            mean_values = [group[col].mean() for col in columns]
            
            # 成長率を計算
            growth_rates = [1.0]
            for i in range(1, len(mean_values)):
                if mean_values[i-1] == 0:
                    growth_rates.append(np.nan)
                else:
                    growth_rates.append(mean_values[i] / mean_values[i-1])
            
            # 結果データを作成
            result = {
                group_by[0]: name[0] if isinstance(name, tuple) else name,
                'count': len(group)
            }
            
            # 2つ目のグループ化列がある場合
            if len(group_by) > 1 and isinstance(name, tuple) and len(name) > 1:
                result[group_by[1]] = name[1]
            
            # 各ウィンドウでの値と成長率を追加
            for i, window in enumerate(windows):
                result[f'{metric}_{window}min'] = mean_values[i]
                if i > 0:
                    result[f'growth_{windows[i-1]}to{window}min'] = growth_rates[i]
            
            # 累積成長率（最初のウィンドウを基準とした相対値）
            for i, window in enumerate(windows):
                if i == 0:
                    result[f'cumulative_growth_{window}min'] = 1.0
                else:
                    result[f'cumulative_growth_{window}min'] = mean_values[i] / mean_values[0] if mean_values[0] > 0 else np.nan
            
            results.append(result)
        
        if not results:
            logger.warning("No valid growth patterns could be calculated")
            return pd.DataFrame()
        
        # 結果をDataFrameに変換
        results_df = pd.DataFrame(results)
        
        # 小数点以下の桁数を制限
        float_cols = [col for col in results_df.columns if results_df[col].dtype == 'float64']
        for col in float_cols:
            results_df[col] = results_df[col].round(4)
        
        logger.info(f"Growth pattern analysis completed for {len(results_df)} groups")
        return results_df
        
    except Exception as e:
        logger.error(f"Error analyzing growth patterns: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    # モジュール単体テスト用コード
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("MultiscaleAnalyzer module loaded successfully")
    print("Run unit tests or import this module to use its functionality") 